/**
 * state.c — 状态转移
 *
 * 三条安全保护在这里落地（对应 docs/03 §4 与 firmware/README）：
 *   1. 串口 200 ms 无帧 → 不再执行 sign 转向（仍继续循迹，因为车停下更危险）
 *   2. 超声 < US_STOP_CM → 直接 ST_STOP
 *   3. 上电 ST_IDLE，必须按键才 RUN
 */
#include "state.h"
#include "config.h"

#define SIGN_TURN_MS      900     /* 转一次持续多久（SIGN_LATCH_MS 在 config.h） */
#define AVOID_HOLD_MS    1200     /* 绕开动作持续多久 */
#define LOST_STOP_MS      700     /* 丢线超过这么久就放弃（避免原地乱转） */

static uint32_t t_enter;          /* 进入当前状态的时刻 */
static AppState last_st;
static uint32_t t_last_sign;      /* 上次执行转向的时刻 */

void State_Init(void)
{
    last_st = ST_IDLE;
    t_enter = HAL_GetTick();
    t_last_sign = 0;
}

const char *State_Name(AppState st)
{
    switch (st) {
    case ST_IDLE:       return "IDLE";
    case ST_RUN:        return "RUN";
    case ST_SIGN_LEFT:  return "SIGN_L";
    case ST_SIGN_RIGHT: return "SIGN_R";
    case ST_AVOID:      return "AVOID";
    case ST_STOP:       return "STOP";
    default:            return "?";
    }
}

AppState State_Update(AppState cur, const Sensors *s)
{
    if (cur != last_st) {          /* 状态切换时重置计时 */
        t_enter = s->now_ms;
        last_st = cur;
    }
    uint32_t in_state = s->now_ms - t_enter;

    switch (cur) {
    case ST_IDLE:
        if (s->btn_pressed) {
            return ST_RUN;
        }
        return ST_IDLE;

    case ST_RUN:
        /* 保护 2：太近就停（无论视觉说什么） */
        if (s->dist_cm > 0 && s->dist_cm < US_STOP_CM) {
            return ST_STOP;
        }
        /* 保护 1 + 多帧确认：视觉活着、置信够、且不是在转向冷却期 */
        if (s->comm_alive
            && s->quality >= SIGN_MIN_QUALITY
            && (s->now_ms - t_last_sign) > SIGN_LATCH_MS) {
            if (s->sign == 1) { t_last_sign = s->now_ms; return ST_SIGN_LEFT; }
            if (s->sign == 2) { t_last_sign = s->now_ms; return ST_SIGN_RIGHT; }
        }
        /* 丢线太久：不要继续瞎冲 */
        if (s->line_lost && in_state > LOST_STOP_MS) {
            return ST_STOP;
        }
        return ST_RUN;

    case ST_SIGN_LEFT:
    case ST_SIGN_RIGHT:
        if (in_state > SIGN_TURN_MS) {
            return ST_RUN;
        }
        return cur;

    case ST_AVOID:
        if (in_state > AVOID_HOLD_MS) {
            return ST_RUN;
        }
        return ST_AVOID;

    case ST_STOP:
        /* 只有长按复位才出来；赛中不要加自动恢复，会突然窜车 */
        return ST_STOP;

    default:
        return ST_STOP;
    }
}
