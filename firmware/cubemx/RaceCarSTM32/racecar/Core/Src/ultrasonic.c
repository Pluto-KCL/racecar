/**
 * ultrasonic.c — HC-SR04 非阻塞测距
 *
 * 使用 Cortex-M3 的 DWT 周期计数器测量 ECHO 脉宽。TRIG、等待回波开始和
 * 等待回波结束被拆成多个状态，单次 US_Task() 只做少量 GPIO 读取。
 * ECHO 输出为 5V 时，接入 PB9 前仍必须使用分压或电平转换。
 */
#include "ultrasonic.h"
#include "config.h"

typedef enum {
    US_IDLE = 0,
    US_TRIG_HIGH,
    US_WAIT_RISE,
    US_WAIT_FALL
} USPhase;

static USPhase phase;
static uint32_t deadline_cycles;
static uint32_t echo_start_cycles;
static uint32_t cycles_per_us;
static uint16_t latest_cm;
static uint8_t latest_valid;
static uint8_t consecutive_failures;

static uint32_t cycle_now(void)
{
    return DWT->CYCCNT;
}

static uint8_t deadline_reached(uint32_t deadline)
{
    return (int32_t)(cycle_now() - deadline) >= 0;
}

static uint32_t us_to_cycles(uint32_t us)
{
    return us * cycles_per_us;
}

static void measurement_failed(void)
{
    phase = US_IDLE;
    HAL_GPIO_WritePin(US_TRIG_PORT, US_TRIG_PIN, GPIO_PIN_RESET);
    latest_cm = 0;
    latest_valid = 0;
    if (consecutive_failures < 255) {
        consecutive_failures++;
    }
}

void US_Init(void)
{
    HAL_GPIO_WritePin(US_TRIG_PORT, US_TRIG_PIN, GPIO_PIN_RESET);
    phase = US_IDLE;
    latest_cm = 0;
    latest_valid = 0;
    consecutive_failures = 0;

    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    cycles_per_us = SystemCoreClock / 1000000UL;
    if (cycles_per_us == 0) {
        cycles_per_us = 72;
    }
}

uint8_t US_StartMeasurement(void)
{
    if (phase != US_IDLE) {
        return 0;
    }

    HAL_GPIO_WritePin(US_TRIG_PORT, US_TRIG_PIN, GPIO_PIN_SET);
    phase = US_TRIG_HIGH;
    deadline_cycles = cycle_now() + us_to_cycles(10);
    return 1;
}

void US_Task(void)
{
    uint32_t now;
    uint32_t pulse_us;

    switch (phase) {
    case US_TRIG_HIGH:
        if (!deadline_reached(deadline_cycles)) {
            return;
        }
        HAL_GPIO_WritePin(US_TRIG_PORT, US_TRIG_PIN, GPIO_PIN_RESET);
        phase = US_WAIT_RISE;
        deadline_cycles = cycle_now() + us_to_cycles(US_ECHO_START_TIMEOUT_US);
        return;

    case US_WAIT_RISE:
        if (HAL_GPIO_ReadPin(US_ECHO_PORT, US_ECHO_PIN) == GPIO_PIN_SET) {
            echo_start_cycles = cycle_now();
            phase = US_WAIT_FALL;
            deadline_cycles = echo_start_cycles + us_to_cycles(US_TIMEOUT_US);
        } else if (deadline_reached(deadline_cycles)) {
            measurement_failed();
        }
        return;

    case US_WAIT_FALL:
        if (HAL_GPIO_ReadPin(US_ECHO_PORT, US_ECHO_PIN) == GPIO_PIN_RESET) {
            now = cycle_now();
            pulse_us = (now - echo_start_cycles) / cycles_per_us;
            latest_cm = (uint16_t)(pulse_us / 58U);
            if (latest_cm > 400U) {
                latest_cm = 400U;
            }
            latest_valid = 1;
            consecutive_failures = 0;
            phase = US_IDLE;
        } else if (deadline_reached(deadline_cycles)) {
            measurement_failed();
        }
        return;

    case US_IDLE:
    default:
        return;
    }
}

uint8_t US_GetLatest(uint16_t *cm)
{
    if (cm != 0) {
        *cm = latest_cm;
    }
    return latest_valid;
}

uint8_t US_HasFault(void)
{
    return (consecutive_failures >= US_FAULT_LIMIT) ? 1 : 0;
}

uint16_t US_ReadCm(void)
{
    return latest_valid ? latest_cm : 0;
}
