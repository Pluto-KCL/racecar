/**
 * pid.c — 增量式 PID 实现
 *
 *   Δu = Kp*(e - e1) + Ki*e*dt + Kd*(e - 2*e1 + e2)/dt
 *   u  = u + Δu, 再对 u 限幅
 *
 * 三重保护：dt 夹紧（循环卡住时 D 项不炸）、积分限幅、输出限幅。
 */
#include "pid.h"
#include "config.h"

static float clampf(float v, float lo, float hi)
{
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

void PID_Init(PID *p, float kp, float ki, float kd, float out_max, float i_max)
{
    p->kp = kp;
    p->ki = ki;
    p->kd = kd;
    p->out_max = out_max;
    p->i_max = i_max;
    PID_Reset(p);
}

void PID_Reset(PID *p)
{
    p->e1 = 0.0f;
    p->e2 = 0.0f;
    p->integral = 0.0f;
    p->d_filtered = 0.0f;
    p->out = 0.0f;
}

float PID_Update(PID *p, float error, float dt)
{
    /* dt 夹紧：正常 5 ms；万一某次循环被卡，也不要让 D 项放大 */
    if (dt < PID_DT_MIN_S) dt = PID_DT_MIN_S;
    if (dt > PID_DT_MAX_S) dt = PID_DT_MAX_S;

    float p_term = p->kp * (error - p->e1);
    float d_raw = (error - 2.0f * p->e1 + p->e2) / dt;
    p->d_filtered += PID_D_FILTER_ALPHA * (d_raw - p->d_filtered);
    float d_term = p->kd * p->d_filtered;

    /* 积分单独累计并限幅，避免把单次积分项误当成积分限幅。 */
    float next_integral = clampf(p->integral + p->ki * error * dt,
                                 -p->i_max, p->i_max);
    float i_term = next_integral - p->integral;

    float delta = p_term + i_term + d_term;
    float next_out = clampf(p->out + delta, -p->out_max, p->out_max);

    /* 输出已饱和且误差仍推动同一方向时，不继续积累积分。 */
    if ((next_out >= p->out_max && delta > 0.0f) ||
        (next_out <= -p->out_max && delta < 0.0f)) {
        i_term = 0.0f;
        delta = p_term + d_term;
        next_out = clampf(p->out + delta, -p->out_max, p->out_max);
    } else {
        p->integral = next_integral;
    }

    p->out = next_out;

    p->e2 = p->e1;
    p->e1 = error;
    return p->out;
}
