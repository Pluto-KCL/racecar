/**
 * config.h — 所有可调参数集中在这里
 *
 * 规则：调参只改这个文件，并 commit 记录"改了什么、10 次成功几次"。
 * 现场只允许改标了 TUNABLE 的三项。
 */
#ifndef CONFIG_H
#define CONFIG_H

#include "main.h"

/* ---------------- 电机 / 速度 ---------------- */
#define MOTOR_PWM_MAX        1000    /* 逻辑速度刻度；当前 TIM4 ARR=899，实际 CCR 满量程为 900 */
#define MOTOR_DEADZONE       120     /* 死区补偿：低于这个占空比电机不转，程序自动补上 */
#define MOTOR_REVERSAL_DEADTIME_MS 20 /* 换向先关 PWM，等待后再改变方向脚 */
#define MOTOR_SLEW_STEP       100     /* 每次控制更新允许的最大占空比变化 */
#define SPEED_BASE           420     /* TUNABLE：基础速度，先从 300 开始试 */
#define SPEED_TURN           280     /* 转弯时内侧轮的速度 */
#define SPEED_MAX            700     /* 硬上限，防止手感一抖飞出去 */
#define SPEED_CURVE_MIN      280     /* 大误差时的最低基础速度 */
#define SPEED_CURVE_START    500     /* 超过该误差才开始降速 */
#define SPEED_CURVE_FULL     1750    /* 达到该误差时降到 SPEED_CURVE_MIN */
#define LINE_PERIOD_MS       5
#define STATE_PERIOD_MS      10
#define US_PERIOD_MS         100
#define LOST_SPEED_FACTOR    0.7f

/* 左电机是否装反（实车跑起来直线偏，先查这个） */
#define MOTOR_LEFT_INVERT    0
#define MOTOR_RIGHT_INVERT   0

/* ---------------- PID ---------------- */
/* 增量式 PID。先从 Kp 单独调：Ki=Kd=0，加大到开始小幅摆动，再退一点。 */
#define PID_KP               0.20f
#define PID_KI               0.0f
#define PID_KD               0.0f
#define PID_OUT_MAX          400.0f
#define PID_I_MAX            300.0f
#define PID_D_FILTER_ALPHA   0.25f   /* 微分低通系数，避免 ADC 跳变放大 D 项 */
#define PID_DT_MIN_S         0.001f
#define PID_DT_MAX_S         0.050f
#define PID_ERROR_SCALE      1.0f /* 当前采用原始加权误差，Kp 按误差量级标定 */

/* ---------------- 循迹阵列 ---------------- */
#define LINE_N               8
#define LINE_WEIGHT_STEP     500     /* 每路权重间隔 → 单路 error 约 ±1750 */
#define LINE_THRESHOLD       1800    /* ADC 判黑白的门限（0..4095），用串口看 raw 值定 */
#define LINE_THRESHOLD_HYST  80      /* 黑白判定滞回，抑制阈值附近抖动 */
#define LINE_WHITE_IS_HIGH   1       /* 白底读数大就填 1；黑线读数大就填 0 */
#define LINE_FILTER_SHIFT    2       /* 原始值一阶滤波，2 表示新样本权重 1/4 */
#define LINE_ADC_TIMEOUT_MS  1       /* 单路 ADC 等待上限，避免一条坏路拖住整车 */
#define LINE_FAULT_LIMIT     2       /* 一次采样中 ADC 失败达到此数才判传感器故障 */
#define LINE_LOST_COUNT      3       /* 连续几路都"没线"算丢线 */
#define LINE_LOST_LIMIT      6

/* ---------------- 串口协议 ---------------- */
#define FRAME_HEAD1          0xAA
#define FRAME_HEAD2          0x55
#define FRAME_LEN            7
#define SIGN_NONE_CODE       0
#define SIGN_LEFT_CODE       1
#define SIGN_RIGHT_CODE      2
#define SIGN_PARK_CODE       3
#define COMM_TIMEOUT_MS      200     /* 超过这么久没收到有效帧 → 锁存安全停机 */
#define COMM_INTERBYTE_TIMEOUT_MS 20 /* 半帧超过此时间，重新等待帧头 */
#define VISION_DEGRADED_FRAME_LIMIT 5
#define SIGN_MIN_QUALITY     40      /* TUNABLE：低于此置信度不执行转向 */
#define SIGN_CONFIRM_NEED    3       /* 连续几帧同向才认（与树莓派侧一致） */
#define SIGN_LATCH_MS        3000    /* 执行一次后锁存，避免同一个牌反复触发 */
#define SIGN_TURN_MS         900
#define AVOID_HOLD_MS        1200
#define LINE_LOST_STOP_MS    700
#define PARK_APPROACH_MS     300
#define PARK_TURN_MS         700
#define PARK_REVERSE_MIN_MS  250
#define PARK_MAX_MS          5000
#define PARK_FRAME_ACTIVE_MIN 6

/* ---------------- 颜色顺序 ---------------- */
#define COLOR_CODE_RED       0
#define COLOR_CODE_GREEN     1
#define COLOR_CODE_BLUE      2
#define COLOR_CODE_YELLOW    3

/* ---------------- 超声 ---------------- */
#define US_TRIG_PORT         GPIOB
#define US_TRIG_PIN          GPIO_PIN_8
#define US_ECHO_PORT         GPIOB
#define US_ECHO_PIN          GPIO_PIN_9
#define US_STOP_CM           15      /* 小于这个距离停车 */
#define US_AVOID_CM          35      /* 进入避障判断的距离 */
#define US_TIMEOUT_US        25000   /* 测距超时（约 4 m） */
#define US_ECHO_START_TIMEOUT_US 3000
#define US_FAULT_LIMIT       3       /* 连续无回波达到此次数，进入安全状态 */

/* ---------------- 按键 ---------------- */
#define BTN_PORT             GPIOB
#define BTN_PIN              GPIO_PIN_10
#define BTN_DEBOUNCE_MS      30
#define STOP_RESET_HOLD_MS   2000

/* ---------------- 调试 ---------------- */
#define DEBUG_UART_PRINT     0       /* 另有独立调试口后才可打开，避免污染视觉二进制 UART */
#define DEBUG_PERIOD_MS      100

#endif /* CONFIG_H */
