/**
 * ultrasonic.h — HC-SR04 非阻塞测距
 *
 * US_StartMeasurement() 只启动一次测量，US_Task() 在主循环中快速轮询。
 * 主循环不会因为等待 ECHO 而停住，最新一次有效结果由 US_GetLatest() 读取。
 */
#ifndef ULTRASONIC_H
#define ULTRASONIC_H

#include <stdint.h>

void     US_Init(void);
uint8_t  US_StartMeasurement(void);
void     US_Task(void);
uint8_t  US_GetLatest(uint16_t *cm);
uint8_t  US_HasFault(void);
uint16_t US_ReadCm(void); /* 兼容旧调用，非阻塞返回最新值 */

#endif /* ULTRASONIC_H */
