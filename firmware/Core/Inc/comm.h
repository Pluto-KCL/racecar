/**
 * comm.h — 视觉板串口接收（协议见 docs/03_接口协议.md）
 *
 * 中断里只做"喂字节"，解析在状态机里逐字节推进，不阻塞、不动态分配。
 */
#ifndef COMM_H
#define COMM_H

#include <stdint.h>

typedef struct {
    uint8_t  sign;          /* 0=无 1=左 2=右 */
    uint8_t  color_valid;
    uint8_t  color_seq;
    uint8_t  colors[4];     /* 解开后的 4 个颜色码 0=R 1=G 2=B 3=Y */
    uint8_t  quality;
    uint32_t last_ms;       /* 最后一帧到达时刻 */
    uint32_t frames;        /* 累计有效帧数 */
    uint32_t err_frames;    /* 校验错/粘包次数（调试用） */
} VisionData;

void               Comm_Init(void);
void               Comm_Feed(uint8_t byte);   /* 在 UART 接收中断/回调里调用 */
const VisionData  *Comm_Get(void);
uint8_t            Comm_Alive(uint32_t now_ms);   /* 1 = 200ms 内有帧 */

#endif /* COMM_H */
