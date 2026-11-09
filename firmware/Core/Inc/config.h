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
#define MOTOR_PWM_MAX        1000    /* PWM 满量程（ARR+1），与 CubeMX 里 TIM4 的 ARR 一致 */
#define MOTOR_DEADZONE       120     /* 死区补偿：低于这个占空比电机不转，程序自动补上 */
#define SPEED_BASE           420     /* TUNABLE：基础速度，先从 300 开始试 */
#define SPEED_TURN           280     /* 转弯时内侧轮的速度 */
#define SPEED_MAX            700     /* 硬上限，防止手感一抖飞出去 */

/* 左电机是否装反（实车跑起来直线偏，先查这个） */
#define MOTOR_LEFT_INVERT    0
#define MOTOR_RIGHT_INVERT   0

/* ---------------- PID ---------------- */
/* 增量式 PID。先从 Kp 单独调：Ki=Kd=0，加大到开始小幅摆动，再退一点。 */
#define PID_KP               6.0f
#define PID_KI               0.02f
#define PID_KD               1.2f
#define PID_OUT_MAX          400.0f
#define PID_I_MAX            300.0f

/* ---------------- 循迹阵列 ---------------- */
#define LINE_N               8
#define LINE_WEIGHT_STEP     500     /* 每路权重间隔 → 单路 error 约 ±1750 */
#define LINE_THRESHOLD       1800    /* ADC 判黑白的门限（0..4095），用串口看 raw 值定 */
#define LINE_WHITE_IS_HIGH   1       /* 白底读数大就填 1；黑线读数大就填 0 */
#define LINE_LOST_COUNT      3       /* 连续几路都"没线"算丢线 */
#define LINE_LOST_LIMIT      6

/* ---------------- 串口协议 ---------------- */
#define FRAME_HEAD1          0xAA
#define FRAME_HEAD2          0x55
#define FRAME_LEN            7
#define COMM_TIMEOUT_MS      200     /* 超过这么久没收到帧 → 视觉失效 */
#define SIGN_MIN_QUALITY     40      /* TUNABLE：低于此置信度不执行转向 */
#define SIGN_CONFIRM_NEED    3       /* 连续几帧同向才认（与树莓派侧一致） */
#define SIGN_LATCH_MS        3000    /* 执行一次后锁存，避免同一个牌反复触发 */

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

/* ---------------- 按键 ---------------- */
#define BTN_PORT             GPIOB
#define BTN_PIN              GPIO_PIN_10
#define BTN_DEBOUNCE_MS      30

/* ---------------- 调试 ---------------- */
#define DEBUG_UART_PRINT     1       /* 1=每 100ms 打一行状态，正式版可关 */
#define DEBUG_PERIOD_MS      100

#endif /* CONFIG_H */
