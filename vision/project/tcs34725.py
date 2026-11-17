"""TCS34725 颜色传感器（备选/校准方案）。

什么时候用：
  * 摄像头在颜色区识别不稳（反光、光照突变），需要更稳的单点测色
  * 需要对摄像头的结果做一次"金标准"校验

代价：必须让传感器真的"看到"色块——车身侧面伸出去贴近色块，或车停在色块旁边。
这在 25 cm 外、10 cm 方块、车还在动的场景里很难做好，所以它是备选不是主选。

接线：I2C（SDA=GPIO2, SCL=GPIO3），3.3V，地址 0x29。
"""

import time

import config

try:
    from smbus2 import SMBus
except ImportError:
    SMBus = None

# 寄存器
_CMD = 0x80
_REG_ENABLE = 0x00
_REG_ATIME = 0x01
_REG_CONTROL = 0x0F
_REG_ID = 0x12
_REG_CDATAL = 0x14

_PON = 0x01
_AEN = 0x02
_GAIN_MAP = {1: 0x00, 4: 0x01, 16: 0x02, 60: 0x03}


class TCS34725:
    def __init__(self, bus=None, addr=None):
        if SMBus is None:
            raise RuntimeError("没装 smbus2：sudo apt install -y python3-smbus 或 pip install smbus2")
        self.addr = addr or config.TCS_I2C_ADDR
        self.bus = SMBus(bus or config.TCS_I2C_BUS)
        chip_id = self._read8(_REG_ID)
        if chip_id not in (0x44, 0x4D):
            print(f"[tcs] 警告：ID=0x{chip_id:02X}，预期 0x44/0x4D，检查接线")
        self._init()

    # ---- 底层 ----
    def _write8(self, reg, val):
        self.bus.write_byte_data(self.addr, _CMD | reg, val)

    def _read8(self, reg):
        return self.bus.read_byte_data(self.addr, _CMD | reg)

    def _read16(self, reg):
        lo = self.bus.read_byte_data(self.addr, _CMD | reg)
        hi = self.bus.read_byte_data(self.addr, _CMD | (reg + 1))
        return (hi << 8) | lo

    def _init(self):
        self._write8(_REG_ENABLE, _PON)
        time.sleep(0.003)
        self._write8(_REG_ENABLE, _PON | _AEN)
        # ATIME: 256 - ms/2.4
        atime = int(256 - (config.TCS_INTEGRATION_MS / 2.4))
        self._write8(_REG_ATIME, max(0, min(255, atime)))
        self._write8(_REG_CONTROL, _GAIN_MAP.get(config.TCS_GAIN, 0x01))
        time.sleep(config.TCS_INTEGRATION_MS / 1000.0 * 2)

    # ---- 对外 ----
    def read_rgbc(self):
        """返回 (r, g, b, clear)。clear 太小说明没对准/太暗。"""
        c = self._read16(_REG_CDATAL)
        r = self._read16(_REG_CDATAL + 2)
        g = self._read16(_REG_CDATAL + 4)
        b = self._read16(_REG_CDATAL + 6)
        return r, g, b, c

    def read_color(self, min_clear=200):
        """返回颜色名 或 None。用"主导通道 + 比值"判断，比 HSV 阈值更抗光照。"""
        r, g, b, c = self.read_rgbc()
        if c < min_clear:
            return None
        total = max(r + g + b, 1)
        rn, gn, bn = r / total, g / total, b / total

        # 黄 = 红绿都高、蓝低
        if rn > 0.30 and gn > 0.30 and bn < 0.28:
            return "yellow"
        if rn > 0.45 and gn < 0.40:
            return "red"
        if gn > 0.42 and gn > rn and gn > bn:
            return "green"
        if bn > 0.35 and bn > rn:
            return "blue"
        return None


if __name__ == "__main__":
    s = TCS34725()
    for _ in range(10):
        print(s.read_rgbc(), s.read_color())
        time.sleep(0.2)
