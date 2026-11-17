/**
 * motor.h — TB6612 双路电机
 *
 * 输入是有符号占空比 -1000..+1000（正=前进）。
 * 死区补偿、限幅、正反转都在内部处理，上层只关心"要多快"。
 */
#ifndef MOTOR_H
#define MOTOR_H

#include <stdint.h>

void Motor_Init(void);
void Motor_Set(int16_t left, int16_t right);
void Motor_Stop(void);      /* 滑行停止（PWM=0，方向脚不变） */
void Motor_Brake(void);     /* 刹车（两方向脚同时拉高，短接电机） */

#endif /* MOTOR_H */
