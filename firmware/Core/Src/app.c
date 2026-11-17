/**
 * app.c — 初始化 + 主循环
 *
 * 控制节奏：
 *   循迹 5 ms 一圈（200 Hz 采样，PID 够用且不至于把 CPU 塞满）
 *   超声 100 ms 一次（阻塞 1–25 ms，只在 RUN/AVOID 里调）
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

/* ---------------- 串口中断：一个字节进来就喂给解析器 ---------------- */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1) {
        Comm_Feed(g_rx);
        HAL_UART_Receive_IT(&huart1, &g_rx, 1);   /* 立刻重新武装 */
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

    switch (st) {
    case ST_RUN: {
        /* 丢线：保持上一次转向量并降速，硬拐比停住更容易救回来 */
        if (Line_Get()->lost) {
            base = (int16_t)(SPEED_BASE * 0.7f);
        }
        int16_t steer = (int16_t)u;
        l = (int16_t)(base + steer);
        r = (int16_t)(base - steer);
        Motor_Set(l, r);
        break;
    }
    case ST_SIGN_LEFT:
        Motor_Set(-SPEED_TURN, SPEED_TURN);
        break;
    case ST_SIGN_RIGHT:
        Motor_Set(SPEED_TURN, -SPEED_TURN);
        break;
    case ST_AVOID:
        /* 先向右切出去（赛场上正向绕行），11-26 可改 */
        Motor_Set(SPEED_TURN, (int16_t)(SPEED_TURN / 2));
        break;
    case ST_IDLE:
        Motor_Stop();
        break;
    case ST_STOP:
    default:
        Motor_Brake();
        break;
    }
}

void App_Loop(void)
{
    uint32_t now = HAL_GetTick();

    /* --- 1) 循迹采样 + PID（5 ms） --- */
    if ((now - t_line) >= 5) {
        float dt = (now - t_line) / 1000.0f;
        t_line = now;

        Line_Update();
        int16_t error = Line_Get()->error;
        float u = PID_Update(&g_pid, (float)error, dt);

        /* --- 3) 状态机（10 ms） --- */
        if ((now - t_state) >= 10) {
            t_state = now;
            const VisionData *v = Comm_Get();
            Sensors s;
            s.now_ms      = now;
            s.btn_pressed = button_pressed();
            s.line_lost   = Line_Get()->lost;
            s.comm_alive  = Comm_Alive(now);
            s.sign        = v->sign;
            s.quality     = v->quality;
            s.dist_cm     = g_dist;
            g_state = State_Update(g_state, &s);
        }

        actuate(g_state, error, u);
    }

    /* --- 2) 超声（100 ms，只在需要时测） --- */
    if ((now - t_us) >= 100) {
        t_us = now;
        if (g_state == ST_RUN || g_state == ST_AVOID) {
            g_dist = US_ReadCm();
        } else {
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
