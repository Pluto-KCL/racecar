/**
 * pid.h — 增量式 PID
 *
 * 为什么用增量式：输出是"在当前输出上加多少"，换速度/换电池电压时不用重调参，
 * 比位置式省事，也不会因为积分饱和导致"松手了车还在转"。
 *
 * 记法：e = 本次误差，e1 = 上次，e2 = 上上次
 *    Δu = Kp*(e - e1) + Ki*e*dt + Kd*(e - 2*e1 + e2)/dt
 *    u  = u + Δu
 */
#ifndef PID_H
#define PID_H

typedef struct {
    float kp, ki, kd;
    float out_max;    /* 输出限幅 */
    float i_max;      /* 积分项限幅 */
    float e1, e2;     /* 前两次误差 */
    float out;        /* 当前输出 */
} PID;

void  PID_Init(PID *p, float kp, float ki, float kd, float out_max, float i_max);
void  PID_Reset(PID *p);
float PID_Update(PID *p, float error, float dt);

#endif /* PID_H */
