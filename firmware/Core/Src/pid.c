/**
 * pid.c — 增量式 PID 实现
 *
 *   Δu = Kp*(e - e1) + Ki*e*dt + Kd*(e - 2*e1 + e2)/dt
 *   u  = u + Δu, 再对 u 限幅
 *
 * 三重保护：dt 夹紧（循环卡住时 D 项不炸）、积分限幅、输出限幅。
 */
#include "pid.h"

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
    p->out = 0.0f;
}

float PID_Update(PID *p, float error, float dt)
{
    /* dt 夹紧：正常 5 ms；万一某次循环被卡，也不要让 D 项放大 */
    if (dt <= 0.0f)  dt = 0.001f;
    if (dt > 0.05f)  dt = 0.05f;

    float p_term = p->kp * (error - p->e1);
    float d_term = p->kd * (error - 2.0f * p->e1 + p->e2) / dt;
    /* 积分项单独限幅，防止长时间贴着一边时越积越大、松手后回不来 */
    float i_term = p->ki * error * dt;
    i_term = clampf(i_term, -p->i_max, p->i_max);

    float delta = p_term + i_term + d_term;

    p->out += delta;
    p->out  = clampf(p->out, -p->out_max, p->out_max);

    p->e2 = p->e1;
    p->e1 = error;
    return p->out;
}
