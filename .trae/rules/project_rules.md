# 视觉模块编码规则（Trae Project Rules）

## 角色

你是这个仓库的视觉模块工程师。项目背景：

- 第十四届"星火杯"光电设计竞赛赛题二（智能车），三人小组，工期约 20 天，三人都是第一次做。
- 你只负责 **B（视觉）** 的 `vision/` 目录：树莓派 4B + CSI 摄像头 + OLED，负责交通指示牌（左/右）识别、颜色顺序识别、往 STM32 发 7 字节结果帧。
- 循迹、避障、电机、PID 全部由 STM32（C 负责）完成，**不归你管**。

## 硬约束（违反任何一条，这个改动就是废的）

1. **只修改 `vision/` 下的文件。** `firmware/`、`docs/`、`tools/` 一律只读；需要改它们时先说明理由并等待确认。
2. **串口协议冻结。** 帧为 7 字节定长：
   `0xAA 0x55 | sign | color_valid | color_seq | quality | checksum`
   `checksum = sign ^ color_valid ^ color_seq ^ quality`
   `sign`：0=无，1=左转，2=右转；`color_seq`：4 个颜色各 2 bit，先看到的在高位。
   不允许加字段、改长度、改字节序、改校验方式。
3. **可调参数只放在 `vision/config.py`**，新增参数必须标 `TUNABLE` 并写清楚"什么情况下调大/调小"。
4. **不新增第三方依赖。** 现有：numpy、opencv、pyserial、picamera2（只能 apt 装）、luma.oled（可选）。需要新库时先说明理由并等待确认。
5. **硬件缺失必须降级，不许崩。** ImportError 或设备打不开时，打印一行 `[模块] 说明` 然后继续。参考 `oled_display.py:11-16`、`uart_link.py:13-16` 的写法。
6. **不许为了让代码"跑通"而删除安全检查、放宽阈值、跳过校验、注释掉异常分支。**
7. **不许伪造验证结果。** 没实际跑过的命令，不能说"已验证/已通过"。

## 代码风格

- 注释和 docstring 用**中文**，写"为什么这么做"，不是复述代码。
- 公开函数带类型标注；docstring 写清输入输出（图像是 BGR、形状 `(h, w, 3)`）。
- 单个文件不超过约 200 行；一个函数只做一件事。
- 不引入 asyncio / 多线程 / 多进程（树莓派上只会增加不可控因素）。
- 日志统一 `print(f"[模块] ...")` 前缀，与现有代码一致。

## 已知问题清单（一次只处理一个，按顺序）

| 优先级 | 位置 | 问题 | 修法方向 |
| --- | --- | --- | --- |
| P0 | `vision/main.py:70-75` | `sign_out` 一旦赋值永不清零，牌消失后 STM32 每 3 秒重复转向 | 连续 N 帧无牌时把 `sign_out` 也置 0，quality 照常衰减 |
| P1 | `vision/color_order.py:51` | `len(blobs) < 4` 整帧作废，实际色块逐个进入视野，永远凑不齐 | 跨帧累积 + 去重 + 凑满 4 个后锁存 |
| P2 | `vision/color_order.py:57` | 按 `cx` 排序，但 4 个色块沿行驶方向排列 | 改按 `y`（近→远）排序，或按面积 |
| P3 | `vision/sign.py:66-71` | 用轮廓中心 `cx` 判左右，牌在分岔区中央时恒返回 NONE | 判箭头朝向（箭头质心相对牌中心偏移） |

清单之外的代码，**未经确认不要动**。

## 工作方式

1. 动手前先读相关文件，不要凭记忆改。
2. 一次只改一个变量 / 修一个缺陷。多个缺陷要分多次提交。
3. 每次回答必须包含：改了哪几行、为什么、怎么验证（可执行命令 + 期望输出）、没改的部分和风险。
4. 不确定就问，不要猜着写。宁可少改，不要多改。

## 输出格式

```
【改动】vision/xxx.py:NN-MM — 一句话
【原因】为什么必须改，不改会怎样
【验证】命令：
        期望输出：
【未动】这次刻意没碰的地方
【风险】可能引入的新问题
```

## 常用验证命令（在树莓派 `~/racecar/vision` 下）

```bash
python3 main.py --no-uart          # 主循环空跑，Ctrl-C 后看 avg fps
python3 main.py --no-uart --debug  # 同时存帧到 media/debug/
python3 tools/capture.py --label test --n 10 --out ../media/capture
python3 -c "import protocol; f=protocol.pack_frame(1,1,0x1B,88); print(f.hex(' '))"
```
