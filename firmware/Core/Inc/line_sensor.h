/**
 * line_sensor.h — 8 路红外循迹阵列
 *
 * 输出的是"偏差"而不是"左转/右转"：
 *   error < 0  线在车左边  → 该往左打
 *   error > 0  线在车右边  → 该往右打
 *   单路看到线时约 ±1750（8 路等分，中点对齐时 ≈ 0）
 */
#ifndef LINE_SENSOR_H
#define LINE_SENSOR_H

#include <stdint.h>
#include "config.h"

typedef struct {
    uint16_t raw[LINE_N];    /* 原始 ADC 值 0..4095 */
    uint8_t  bits[LINE_N];   /* 1 = 看到黑线 */
    uint8_t  active;         /* 看到黑线的路数 */
    int16_t  error;          /* 加权偏差约 -1750..+1750 */
    uint8_t  lost;           /* 1 = 丢线 */
} LineState;

void      Line_Init(void);
void      Line_Update(void);            /* 采一次，更新内部状态（建议 5~10 ms 调用一次） */
LineState *Line_Get(void);

#endif /* LINE_SENSOR_H */
