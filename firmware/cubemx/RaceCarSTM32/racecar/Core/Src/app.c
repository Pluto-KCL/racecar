/**
 * app.c — 初始化 + 主循环
 *
 * 控制节奏：
 *   循迹 5 ms 一圈（200 Hz 采样，PID 够用且不至于把 CPU 塞满）
 *   超声 100 ms 启动一次，测量由非阻塞状态机在主循环中推进
 *   状态机 10 ms 一次
 *   调试打印 100 ms 一行（正式版关掉 DEBUG_UART_PRINT）
 */
#include "app.h"
#include "config.h"
#include "line_sensor.h"
#include "pid.h"
#include "motor.h"
#include "comm.h"
#include "state.h"
#include "ultrasonic.h"
#include <stdio.h>

extern UART_HandleTypeDef huart1;

static PID       g_pid;
static AppState  g_state;
static uint32_t  t_line, t_state, t_us, t_dbg;
static uint16_t  g_dist;
static uint8_t   g_rx;
static int16_t   g_error;
static float     g_steer;
static uint32_t  g_park_start_ms;

static int16_t curve_base_speed(int16_t error)
{
    int32_t magnitude = error < 0 ? -(int32_t)error : error;
    int32_t span = SPEED_CURVE_FULL - SPEED_CURVE_START;
    int32_t range = SPEED_BASE - SPEED_CURVE_MIN;

    if (magnitude <= SPEED_CURVE_START || span <= 0 || range <= 0) {
        return SPEED_BASE;
    }
    if (magnitude >= SPEED_CURVE_FULL) {
        return SPEED_CURVE_MIN;
    }
    return (int16_t)(SPEED_BASE -
                     (range * (magnitude - SPEED_CURVE_START)) / span);
}

/* ---------------- 串口中断：一个字节进来就喂给解析器 ---------------- */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1) {
        Comm_Feed(g_rx);
        HAL_UART_Receive_IT(&huart1, &g_rx, 1);   /* 立刻重新武装 */
    }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1) {
        Comm_ResetParser();
        HAL_UART_Receive_IT(&huart1, &g_rx, 1);
    }
}

void App_Init(void)
{
    Motor_Init();
    Line_Init();
    Comm_Init();
    US_Init();
    State_Init();

    PID_Init(&g_pid, PID_KP, PID_KI, PID_KD, PID_OUT_MAX, PID_I_MAX);

    g_state = ST_IDLE;
    g_dist  = 0;
    g_error = 0;
    g_steer = 0.0f;
    g_park_start_ms = 0;
    t_line = t_state = t_us = t_dbg = HAL_GetTick();

    HAL_UART_Receive_IT(&huart1, &g_rx, 1);

    if (DEBUG_UART_PRINT) {
        const char *hi = "boot: racecar fw v0.1\r\n";
        HAL_UART_Transmit(&huart1, (uint8_t *)hi, 24, 100);
    }
}

static uint8_t button_pressed(void)
{
    static uint32_t t_down;
    if (HAL_GPIO_ReadPin(BTN_PORT, BTN_PIN) == GPIO_PIN_RESET) {
        if (t_down == 0) {
            t_down = HAL_GetTick();
        } else if ((HAL_GetTick() - t_down) > BTN_DEBOUNCE_MS) {
            return 1;
        }
    } else {
        t_down = 0;
    }
    return 0;
}

/* 把"状态 + 偏差"翻译成左右轮速度 —— 整个固件里唯一碰电机的地方 */
static void actuate(AppState st, int16_t error, float u)
{
    int16_t base = SPEED_BASE;
    int16_t l, r;
    (void)error;   /* 偏差已由 PID 吃进 u，这里只保留参数便于以后改 */

    /* 执行层再做一次通信门控，避免状态机刚切换到 RUN 的一个周期继续出力。 */
    if (!Comm_Alive(HAL_GetTick())) {
        Motor_SafeOff();
        return;
    }

    switch (st) {
    case ST_RUN: {
        if (Line_Get()->fault) {
            Motor_SafeOff();
            break;
        }
        /* 丢线：保持上一次转向量并降速，硬拐比停住更容易救回来 */
        base = curve_base_speed(error);
        if (Line_Get()->lost) {
            base = (int16_t)(SPEED_BASE * LOST_SPEED_FACTOR);
        }
        if (US_HasFault() && base > SPEED_CURVE_MIN) {
            base = SPEED_CURVE_MIN;
        }
        if (Comm_VisionDegraded() && base > SPEED_CURVE_MIN) {
            base = SPEED_CURVE_MIN;
        }
        int16_t steer = (int16_t)u;
        l = (int16_t)(base + steer);
        r = (int16_t)(base - steer);
        Motor_Set(l, r);
        break;
    }
    case ST_SIGN_LEFT:
        /* 前进差速转向，避免原地自转后完全丢失循迹线。 */
        Motor_Set((int16_t)(SPEED_TURN / 2), SPEED_TURN);
        break;
    case ST_SIGN_RIGHT:
        Motor_Set(SPEED_TURN, (int16_t)(SPEED_TURN / 2));
        break;
    case ST_AVOID:
        /* 先向右切出去（赛场上正向绕行），11-26 可改 */
        Motor_Set(SPEED_TURN, (int16_t)(SPEED_TURN / 2));
        break;
    case ST_PARK: {
        uint32_t elapsed = HAL_GetTick() - g_park_start_ms;
        if (elapsed < PARK_APPROACH_MS) {
            Motor_Set(SPEED_CURVE_MIN, SPEED_CURVE_MIN);
        } else if (elapsed < PARK_APPROACH_MS + PARK_TURN_MS) {
            /* 右侧车库，先向右切入入口。 */
            Motor_Set(SPEED_TURN, (int16_t)(SPEED_TURN / 2));
        } else {
            Motor_Set(-SPEED_CURVE_MIN, -SPEED_CURVE_MIN);
        }
        break;
    }
    case ST_PARK_HOLD:
        Motor_Stop();
        break;
    case ST_IDLE:
        Motor_Stop();
        break;
    case ST_STOP:
    default:
        Motor_SafeOff();
        break;
    }
}

void App_Loop(void)
{
    uint32_t now = HAL_GetTick();
    uint8_t control_due = 0;
    uint8_t state_due = 0;

    /* 超声波和串口维护都必须是短任务，不能阻塞循迹控制。 */
    US_Task();
    Comm_Task(now);

    /* --- 1) 循迹采样 + PID（5 ms） --- */
    if ((now - t_line) >= LINE_PERIOD_MS) {
        float dt = (now - t_line) / 1000.0f;
        t_line = now;
        control_due = 1;

        Line_Update();
        g_error = Line_Get()->error;
        if (g_state == ST_RUN && !Line_Get()->fault && !Line_Get()->lost &&
            !Line_Get()->all_black) {
            float control_error = (float)g_error / PID_ERROR_SCALE;
            g_steer = PID_Update(&g_pid, control_error, dt);
        } else if (g_state != ST_RUN || Line_Get()->fault) {
            PID_Reset(&g_pid);
            g_steer = 0.0f;
        }

    }

    /* --- 3) 状态机（10 ms），与 ADC 采样任务独立调度 --- */
    if ((now - t_state) >= STATE_PERIOD_MS) {
        t_state = now;
        state_due = 1;
        const VisionData *v = Comm_Get();
        Sensors s;
        s.now_ms      = now;
        s.btn_pressed = button_pressed();
        s.line_lost   = Line_Get()->lost;
        s.line_fault  = Line_Get()->fault;
        s.line_all_black = Line_Get()->all_black;
        s.comm_alive  = Comm_Alive(now);
        s.vision_degraded = Comm_VisionDegraded();
        s.comm_frames = v->frames;
        s.sign        = v->sign;
        s.quality     = v->quality;
        s.dist_cm     = g_dist;
        s.ultrasonic_fault = US_HasFault();
        s.park_frame_detected =
            (Line_Get()->active >= PARK_FRAME_ACTIVE_MIN) ? 1 : 0;
        AppState previous = g_state;
        g_state = State_Update(g_state, &s);
        if (g_state == ST_PARK && previous != ST_PARK) {
            g_park_start_ms = now;
        }
    }

    if (control_due || state_due) {
        actuate(g_state, g_error, g_steer);
    }

    /* --- 2) 超声（100 ms，只在需要时测） --- */
    if ((now - t_us) >= US_PERIOD_MS) {
        t_us = now;
        if (g_state == ST_RUN || g_state == ST_AVOID) {
            (void)US_StartMeasurement();
        } else {
            g_dist = 0;
        }
    }

    {
        uint16_t latest;
        if (US_GetLatest(&latest)) {
            g_dist = latest;
        } else if (US_HasFault()) {
            g_dist = 0;
        }
    }

    /* --- 4) 调试打印 --- */
#if DEBUG_UART_PRINT
    if ((now - t_dbg) >= DEBUG_PERIOD_MS) {
        t_dbg = now;
        const VisionData *v = Comm_Get();
        char buf[128];
        int n = snprintf(buf, sizeof(buf),
                         "%s e=%d lost=%d sign=%d q=%d d=%u st=%lu f=%lu\r\n",
                         State_Name(g_state), Line_Get()->error, Line_Get()->lost,
                         v->sign, v->quality, (unsigned)g_dist,
                         (unsigned long)v->last_ms, (unsigned long)v->frames);
        if (n > 0) {
            HAL_UART_Transmit(&huart1, (uint8_t *)buf, (uint16_t)n, 50);
        }
    }
#endif
}
