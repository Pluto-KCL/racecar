/**
 * state.c — 状态转移
 *
 * 三条安全保护在这里落地（对应 docs/03 §4 与 firmware/README）：
 *   1. 串口 200 ms 无帧 → 进入锁存 STOP，禁止继续使用旧视觉指令行驶
 *   2. 超声 < US_STOP_CM → 直接 ST_STOP
 *   3. 上电 ST_IDLE，必须按键才 RUN
 */
#include "state.h"
#include "config.h"

static uint32_t t_enter;          /* 进入当前状态的时刻 */
static AppState last_st;
static uint32_t t_last_sign;      /* 上次执行转向的时刻 */
static uint32_t t_line_lost;      /* 本次连续丢线开始时刻 */
static uint32_t last_comm_frame;  /* 上次处理过的有效视觉帧 */
static uint8_t  candidate_sign;   /* STM32 侧三帧确认候选 */
static uint8_t  candidate_count;
static uint8_t  sign_armed;       /* 同一块牌清除前只允许触发一次 */
static uint32_t t_stop_button;
static uint8_t  start_armed;

void State_Init(void)
{
    last_st = ST_IDLE;
    t_enter = HAL_GetTick();
    t_last_sign = 0;
    t_line_lost = 0;
    last_comm_frame = 0;
    candidate_sign = 0;
    candidate_count = 0;
    sign_armed = 1;
    t_stop_button = 0;
    start_armed = 1;
}

const char *State_Name(AppState st)
{
    switch (st) {
    case ST_IDLE:       return "IDLE";
    case ST_RUN:        return "RUN";
    case ST_SIGN_LEFT:  return "SIGN_L";
    case ST_SIGN_RIGHT: return "SIGN_R";
    case ST_AVOID:      return "AVOID";
    case ST_PARK:       return "PARK";
    case ST_PARK_HOLD:  return "PARK_HOLD";
    case ST_STOP:       return "STOP";
    default:            return "?";
    }
}

AppState State_Update(AppState cur, const Sensors *s)
{
    /* 只在收到新的有效帧时推进确认计数，避免 10 ms 状态机重复计算同一帧。 */
    if (s->comm_frames != last_comm_frame) {
        last_comm_frame = s->comm_frames;
        if (s->sign == SIGN_LEFT_CODE || s->sign == SIGN_RIGHT_CODE ||
            s->sign == SIGN_PARK_CODE) {
            if (s->quality < SIGN_MIN_QUALITY) {
                candidate_sign = 0;
                candidate_count = 0;
                sign_armed = 1;
            } else if (candidate_sign == s->sign) {
                if (candidate_count < SIGN_CONFIRM_NEED) {
                    candidate_count++;
                }
            } else {
                candidate_sign = s->sign;
                candidate_count = 1;
                sign_armed = 1;
            }
        } else {
            candidate_sign = 0;
            candidate_count = 0;
            sign_armed = 1;
        }
    }

    if (s->line_lost && !s->line_all_black) {
        if (t_line_lost == 0) {
            t_line_lost = s->now_ms;
        }
    } else {
        t_line_lost = 0;
    }

    if (cur != last_st) {          /* 状态切换时重置计时 */
        t_enter = s->now_ms;
        last_st = cur;
    }
    uint32_t in_state = s->now_ms - t_enter;

    switch (cur) {
    case ST_IDLE:
        /* 没有视觉心跳时保持待机，避免一键启动后立刻锁死。 */
        if (!s->btn_pressed) {
            start_armed = 1;
        } else if (start_armed && s->comm_alive) {
            start_armed = 0;
            return ST_RUN;
        }
        return ST_IDLE;

    case ST_RUN:
        /* 视觉链路是运行许可的一部分。超时后不能继续使用旧指令行驶。 */
        if (!s->comm_alive) {
            return ST_STOP;
        }
        if (s->line_fault) {
            return ST_STOP;
        }
        /* 保护 2：太近就停（无论视觉说什么） */
        if (s->dist_cm > 0 && s->dist_cm < US_STOP_CM) {
            return ST_STOP;
        }
        if (s->dist_cm >= US_STOP_CM && s->dist_cm < US_AVOID_CM) {
            return ST_AVOID;
        }
        /* 保护 1 + STM32 侧多帧确认 + 3 s 锁存。 */
        if (sign_armed && candidate_count >= SIGN_CONFIRM_NEED
            && (s->now_ms - t_last_sign) > SIGN_LATCH_MS) {
            t_last_sign = s->now_ms;
            sign_armed = 0;
            if (candidate_sign == SIGN_LEFT_CODE) return ST_SIGN_LEFT;
            if (candidate_sign == SIGN_RIGHT_CODE) return ST_SIGN_RIGHT;
            if (candidate_sign == SIGN_PARK_CODE) return ST_PARK;
        }
        /* 丢线太久：不要继续瞎冲 */
        if (s->line_lost && t_line_lost != 0 &&
            (s->now_ms - t_line_lost) > LINE_LOST_STOP_MS) {
            return ST_STOP;
        }
        return ST_RUN;

    case ST_SIGN_LEFT:
    case ST_SIGN_RIGHT:
        if (!s->comm_alive || s->line_fault) {
            return ST_STOP;
        }
        if (in_state > SIGN_TURN_MS) {
            return ST_RUN;
        }
        return cur;

    case ST_AVOID:
        if (!s->comm_alive || s->line_fault) {
            return ST_STOP;
        }
        if (s->ultrasonic_fault) {
            return ST_RUN;
        }
        if (s->dist_cm > 0 && s->dist_cm < US_STOP_CM) {
            return ST_STOP;
        }
        if (in_state > AVOID_HOLD_MS) {
            return ST_RUN;
        }
        return ST_AVOID;

    case ST_PARK:
        if (!s->comm_alive || s->line_fault) {
            return ST_STOP;
        }
        if (s->park_frame_detected && in_state >= PARK_REVERSE_MIN_MS) {
            return ST_PARK_HOLD;
        }
        if (in_state >= PARK_MAX_MS) {
            return ST_STOP;
        }
        return ST_PARK;

    case ST_PARK_HOLD:
        if (!s->btn_pressed) {
            t_stop_button = 0;
        } else if (t_stop_button == 0) {
            t_stop_button = s->now_ms;
        } else if ((s->now_ms - t_stop_button) >= STOP_RESET_HOLD_MS) {
            t_stop_button = 0;
            candidate_sign = 0;
            candidate_count = 0;
            sign_armed = 1;
            start_armed = s->btn_pressed ? 0 : 1;
            return ST_IDLE;
        }
        return ST_PARK_HOLD;

    case ST_STOP:
        /* 只有长按复位才出来，短暂抖动不会解除故障锁存。 */
        if (!s->btn_pressed) {
            t_stop_button = 0;
        } else if (t_stop_button == 0) {
            t_stop_button = s->now_ms;
        } else if ((s->now_ms - t_stop_button) >= STOP_RESET_HOLD_MS) {
            t_stop_button = 0;
            candidate_sign = 0;
            candidate_count = 0;
            sign_armed = 1;
            t_last_sign = 0;
            t_line_lost = 0;
            start_armed = s->btn_pressed ? 0 : 1;
            return ST_IDLE;
        }
        return ST_STOP;

    default:
        return ST_STOP;
    }
}
