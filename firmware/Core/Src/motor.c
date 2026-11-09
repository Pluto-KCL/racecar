/**
 * motor.c — TB6612FNG 驱动
 *
 * 接线（与 README 的表一致）：
 *   PWMA=PB6(TIM4_CH1)  AIN1=PB12  AIN2=PB13   → 左电机
 *   PWMB=PB7(TIM4_CH2)  BIN1=PB14  BIN2=PB15   → 右电机
 *   STBY=PB11（高电平使能）
 *
 * 三个容易踩的坑：
 *   1. STBY 忘了拉高 → 电机一动不动，新手第一坑
 *   2. 方向脚同时为高 → 刹车，不是反转
 *   3. 占空比低于 MOTOR_DEADZONE 时电机不转但会"嗡嗡"发热 → 必须做死区补偿
 */
#include "motor.h"
#include "config.h"

extern TIM_HandleTypeDef htim4;

static int16_t apply_deadzone(int16_t v)
{
    if (v > 0 && v < MOTOR_DEADZONE)  return MOTOR_DEADZONE;
    if (v < 0 && v > -MOTOR_DEADZONE) return -MOTOR_DEADZONE;
    return v;
}

static int16_t clamp_speed(int16_t v)
{
    if (v >  SPEED_MAX) return  SPEED_MAX;
    if (v < -SPEED_MAX) return -SPEED_MAX;
    return v;
}

static void set_one(uint32_t ch, GPIO_TypeDef *p1, uint16_t n1,
                    GPIO_TypeDef *p2, uint16_t n2, int16_t v, uint8_t invert)
{
    if (invert) v = (int16_t)(-v);

    if (v > 0) {                      /* 正转 */
        HAL_GPIO_WritePin(p1, n1, GPIO_PIN_SET);
        HAL_GPIO_WritePin(p2, n2, GPIO_PIN_RESET);
    } else if (v < 0) {               /* 反转 */
        HAL_GPIO_WritePin(p1, n1, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(p2, n2, GPIO_PIN_SET);
        v = (int16_t)(-v);
    } else {                          /* 停 */
        HAL_GPIO_WritePin(p1, n1, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(p2, n2, GPIO_PIN_RESET);
    }

    uint32_t duty = (uint32_t)v;                       /* 0..SPEED_MAX */
    __HAL_TIM_SET_COMPARE(&htim4, ch, duty);
}

void Motor_Init(void)
{
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_11, GPIO_PIN_SET);   /* STBY 使能 */
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_1);
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_2);
    Motor_Stop();
}

void Motor_Set(int16_t left, int16_t right)
{
    left  = apply_deadzone(clamp_speed(left));
    right = apply_deadzone(clamp_speed(right));

    set_one(TIM_CHANNEL_1, GPIOB, GPIO_PIN_12, GPIOB, GPIO_PIN_13, left,  MOTOR_LEFT_INVERT);
    set_one(TIM_CHANNEL_2, GPIOB, GPIO_PIN_14, GPIOB, GPIO_PIN_15, right, MOTOR_RIGHT_INVERT);
}

void Motor_Stop(void)
{
    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_1, 0);
    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_2, 0);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_15, GPIO_PIN_RESET);
}

void Motor_Brake(void)
{
    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_1, 0);
    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_2, 0);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_15, GPIO_PIN_SET);
}
