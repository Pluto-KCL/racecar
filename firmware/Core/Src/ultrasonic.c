/**
 * ultrasonic.c — HC-SR04 阻塞式测距
 *
 *   1) TRIG 拉高 10 µs
 *   2) 等 ECHO 变高（最多 2 ms）
 *   3) 量 ECHO 高电平持续多久
 *   4) 距离(cm) = 脉宽(µs) / 58
 *
 * 接线提醒：ECHO 输出 5V，接 STM32 前必须分压（1k + 2k 到 GND）或用电平转换，
 * 否则 PB9 长期过压，早晚锁死。
 */
#include "ultrasonic.h"
#include "config.h"

void US_Init(void)
{
    HAL_GPIO_WritePin(US_TRIG_PORT, US_TRIG_PIN, GPIO_PIN_RESET);
    HAL_GPIO_ReadPin(US_ECHO_PORT, US_ECHO_PIN);
}

uint16_t US_ReadCm(void)
{
    uint32_t t0, t1, us;

    /* 1) 10 µs 触发脉冲 */
    HAL_GPIO_WritePin(US_TRIG_PORT, US_TRIG_PIN, GPIO_PIN_SET);
    for (volatile int i = 0; i < 200; i++) { __NOP(); }   /* 约 10 µs @72MHz */
    HAL_GPIO_WritePin(US_TRIG_PORT, US_TRIG_PIN, GPIO_PIN_RESET);

    /* 2) 等回波拉高 */
    t0 = HAL_GetTick();
    while (HAL_GPIO_ReadPin(US_ECHO_PORT, US_ECHO_PIN) == GPIO_PIN_RESET) {
        if ((HAL_GetTick() - t0) > 3) {      /* 3 ms 内没拉高 → 没回波 */
            return 0;
        }
    }

    /* 3) 量脉宽（用粗计数，1 µs 级精度足够 1 cm 的分辨率） */
    for (us = 0; us < US_TIMEOUT_US; us++) {
        if (HAL_GPIO_ReadPin(US_ECHO_PORT, US_ECHO_PIN) == GPIO_PIN_RESET) {
            break;
        }
        for (volatile int i = 0; i < 6; i++) { __NOP(); }   /* 约 1 µs 的延时 */
    }

    if (us >= US_TIMEOUT_US) {
        return 0;
    }
    t1 = us / 58;
    return (uint16_t)(t1 > 400 ? 400 : t1);
}
