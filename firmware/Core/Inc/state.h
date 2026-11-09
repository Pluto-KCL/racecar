/**
 * state.h — 状态机（只做决定，不碰电机）
 *
 * 为什么单独一层：
 *   循迹 PID 管"怎么贴着线走"，状态机管"现在该干什么"。
 *   混在一起写，加一个功能就要动散落在各处的 if —— 20 天里改三次就该崩了。
 *
 * 关键设计：颜色顺序**不进入**这个状态机。
 *   颜色 20 分是"屏幕上显示出来给裁判看"，用树莓派的 OLED 完成，
 *   STM32 完全不需要知道颜色 —— 少一个状态，少一个 bug。
 */
#ifndef STATE_H
#define STATE_H

#include <stdint.h>

typedef enum {
    ST_IDLE = 0,      /* 上电待机，等按键（防一上电就冲出去） */
    ST_RUN,           /* 正常循迹 */
    ST_SIGN_LEFT,     /* 执行左转动作 */
    ST_SIGN_RIGHT,    /* 执行右转动作 */
    ST_AVOID,         /* 避障（11-26 之后才启用） */
    ST_STOP           /* 锁死停车，只能复位 */
} AppState;

typedef struct {
    uint32_t now_ms;
    uint8_t  btn_pressed;
    uint8_t  line_lost;
    uint8_t  comm_alive;
    uint8_t  sign;        /* 0=无 1=左 2=右 */
    uint8_t  quality;
    uint16_t dist_cm;     /* 0=没测到 */
} Sensors;

void        State_Init(void);
AppState    State_Update(AppState cur, const Sensors *s);
const char *State_Name(AppState st);

#endif /* STATE_H */
