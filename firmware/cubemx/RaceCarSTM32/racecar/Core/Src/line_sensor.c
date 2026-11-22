/**
 * line_sensor.c — 8 路 ADC 轮询 + 加权求偏差
 *
 * 为什么用加权而不是"查表"：
 *   加权相当于给你一个连续的误差信号，PID 能平滑工作；
 *   查表（8 种情况对应 8 个转向量）在路沿抖动时会一顿一顿。
 *
 * 引脚：PA0..PA7 = ADC1_IN0..IN7（与 config.h / README 的表一致）
 */
#include "line_sensor.h"

extern ADC_HandleTypeDef hadc1;

static LineState s;
static uint16_t filtered[LINE_N];
static uint8_t filter_ready;

static uint32_t channel_of(uint8_t i)
{
    static const uint32_t ch[LINE_N] = {
        ADC_CHANNEL_0, ADC_CHANNEL_1, ADC_CHANNEL_2, ADC_CHANNEL_3,
        ADC_CHANNEL_4, ADC_CHANNEL_5, ADC_CHANNEL_6, ADC_CHANNEL_7
    };
    return ch[i];
}

void Line_Init(void)
{
    for (uint8_t i = 0; i < LINE_N; i++) {
        s.raw[i]  = 0;
        s.bits[i] = 0;
    }
    s.active = 0;
    s.error  = 0;
    s.lost   = 1;
    s.fault  = 0;
    s.all_black = 0;
    for (uint8_t i = 0; i < LINE_N; i++) {
        filtered[i] = 0;
    }
    filter_ready = 0;
}

static uint8_t adc_read(uint8_t i, uint16_t *value)
{
    ADC_ChannelConfTypeDef cfg = {0};
    cfg.Channel      = channel_of(i);
    cfg.Rank         = ADC_REGULAR_RANK_1;
    cfg.SamplingTime = ADC_SAMPLETIME_55CYCLES_5;

    if (HAL_ADC_ConfigChannel(&hadc1, &cfg) != HAL_OK) {
        return 0;
    }
    HAL_ADC_Start(&hadc1);
    if (HAL_ADC_PollForConversion(&hadc1, LINE_ADC_TIMEOUT_MS) != HAL_OK) {
        HAL_ADC_Stop(&hadc1);
        return 0;
    }
    *value = (uint16_t)HAL_ADC_GetValue(&hadc1);
    HAL_ADC_Stop(&hadc1);
    return 1;
}

void Line_Update(void)
{
    int32_t sum_w = 0;
    uint8_t n = 0;
    uint8_t sample_errors = 0;

    for (uint8_t i = 0; i < LINE_N; i++) {
        uint16_t sample;
        if (adc_read(i, &sample)) {
            s.raw[i] = sample;
            if (!filter_ready) {
                filtered[i] = sample;
            } else {
                int32_t delta = (int32_t)sample - filtered[i];
                filtered[i] = (uint16_t)((int32_t)filtered[i] +
                                         (delta / (1 << LINE_FILTER_SHIFT)));
            }
        } else {
            sample_errors++;
        }

        uint16_t value = filtered[i];

#if LINE_WHITE_IS_HIGH
        uint16_t enter_black = LINE_THRESHOLD > LINE_THRESHOLD_HYST
                                   ? LINE_THRESHOLD - LINE_THRESHOLD_HYST : 0;
        uint16_t leave_black = LINE_THRESHOLD + LINE_THRESHOLD_HYST;
        uint8_t black = s.bits[i]
                            ? (value < leave_black)
                            : (value < enter_black);
#else
        uint16_t enter_black = LINE_THRESHOLD + LINE_THRESHOLD_HYST;
        uint16_t leave_black = LINE_THRESHOLD > LINE_THRESHOLD_HYST
                                   ? LINE_THRESHOLD - LINE_THRESHOLD_HYST : 0;
        uint8_t black = s.bits[i]
                            ? (value > leave_black)
                            : (value > enter_black);
#endif
        s.bits[i] = black;

        if (black) {
            /* 权重：i=0 → -1750, i=3.5 → 0, i=7 → +1750。 */
            int32_t w = ((int32_t)i - 3) * LINE_WEIGHT_STEP - (LINE_WEIGHT_STEP / 2);
            sum_w += w;
            n++;
        }
    }

    s.active = n;
    if (!filter_ready) {
        filter_ready = 1;
    }
    s.fault = (sample_errors >= LINE_FAULT_LIMIT) ? 1 : 0;

    s.all_black = (n == LINE_N && !s.fault) ? 1 : 0;
    if (n == 0 || s.fault) {
        s.lost = 1;                 /* 丢线：error 保持上一次，由 state.c 决定怎么救 */
        return;
    }

    s.lost   = 0;
    s.error  = (int16_t)(sum_w / n);
}

LineState *Line_Get(void)
{
    return &s;
}
