/**
 * ultrasonic.h — HC-SR04
 *
 * 注意：这是阻塞式测距，最长会卡 US_TIMEOUT_US（25 ms）。
 * 所以只在 AVOID 状态下、每 100 ms 调一次，绝不放在循迹主循环里每圈都调。
 * 想要更好的，就改用输入捕获 + 中断（11-26 之后有余力再说）。
 */
#ifndef ULTRASONIC_H
#define ULTRASONIC_H

#include <stdint.h>

void     US_Init(void);
uint16_t US_ReadCm(void);   /* 返回厘米；0 表示超时/没有回波 */

#endif /* ULTRASONIC_H */
