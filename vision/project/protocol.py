"""帧打包 —— 与 docs/03_接口协议.md 严格一致。

帧（7 字节定长）：
   0xAA | 0x55 | sign | color_valid | color_seq | quality | checksum
   checksum = sign ^ color_valid ^ color_seq ^ quality
"""

import struct

HEADER = b"\xAA\x55"
FRAME_LEN = 7

SIGN_NONE = 0
SIGN_LEFT = 1
SIGN_RIGHT = 2

# 单块颜色编码（2 bit）
COLOR_CODE = {"red": 0, "green": 1, "blue": 2, "yellow": 3}
CODE_COLOR = {v: k for k, v in COLOR_CODE.items()}


def checksum(sign: int, color_valid: int, color_seq: int, quality: int) -> int:
    return (sign ^ color_valid ^ color_seq ^ quality) & 0xFF


def pack_frame(sign: int, color_valid: int, color_seq: int, quality: int) -> bytes:
    """打包一帧。参数越界会被夹紧，不会抛异常（赛场上宁可发个错值也不要崩）。"""
    sign = max(0, min(2, int(sign)))
    color_valid = 1 if color_valid else 0
    color_seq = int(color_seq) & 0xFF
    quality = max(0, min(100, int(quality)))
    cs = checksum(sign, color_valid, color_seq, quality)
    return struct.pack("BBBBBBB", 0xAA, 0x55, sign, color_valid, color_seq, quality, cs)


def encode_seq(colors: list[str]) -> int:
    """['red','green','blue','yellow'] -> 0x1B。不足 4 个用 0 补（红）。"""
    seq = 0
    for i in range(4):
        c = colors[i] if i < len(colors) else "red"
        seq |= (COLOR_CODE.get(c, 0) & 0x03) << (6 - 2 * i)
    return seq


def decode_seq(seq: int) -> list[str]:
    return [CODE_COLOR[(seq >> (6 - 2 * i)) & 0x03] for i in range(4)]


def parse_frame(buf: bytes):
    """STM32 侧解析参考实现（PC 端 tools/view_frames.py 也用它）。返回 dict 或 None。"""
    if len(buf) < FRAME_LEN or buf[0] != 0xAA or buf[1] != 0x55:
        return None
    sign, cv, seq, q, cs = buf[2], buf[3], buf[4], buf[5], buf[6]
    return {
        "sign": sign,
        "color_valid": cv,
        "color_seq": seq,
        "colors": decode_seq(seq) if cv else None,
        "quality": q,
        "checksum_ok": cs == checksum(sign, cv, seq, q),
    }


if __name__ == "__main__":
    f = pack_frame(SIGN_LEFT, 1, encode_seq(["red", "green", "blue", "yellow"]), 88)
    print("frame:", f.hex(" "))
    print("parsed:", parse_frame(f))
    assert parse_frame(f)["colors"] == ["red", "green", "blue", "yellow"]
    assert encode_seq(["red", "green", "blue", "yellow"]) == 0x1B
    print("self-test OK")
