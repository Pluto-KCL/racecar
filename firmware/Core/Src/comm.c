/**
 * comm.c — 7 字节帧解析状态机
 *
 *   0xAA | 0x55 | sign | color_valid | color_seq | quality | checksum
 *   checksum = sign ^ color_valid ^ color_seq ^ quality
 *
 * 为什么不"一次收 7 个字节再解析"：
 *   串口会粘包、会丢字节、上电时会收到乱码。逐字节状态机在任何时候断了都能
 *   重新对齐到下一个 0xAA，不会因为丢一个字节就永远错位。
 */
#include "comm.h"
#include "config.h"

typedef enum { S_H1 = 0, S_H2, S_SIGN, S_CV, S_SEQ, S_Q, S_CS } parse_state_t;

static VisionData    d;
static parse_state_t st;
static uint8_t       buf[FRAME_LEN];
static uint8_t       idx;

void Comm_Init(void)
{
    d.sign = 0;
    d.color_valid = 0;
    d.color_seq = 0;
    d.quality = 0;
    d.colors[0] = d.colors[1] = d.colors[2] = d.colors[3] = 0;
    d.last_ms = 0;
    d.frames = 0;
    d.err_frames = 0;
    st = S_H1;
    idx = 0;
}

static void push_frame(void)
{
    uint8_t cs = (uint8_t)(buf[2] ^ buf[3] ^ buf[4] ^ buf[5]);
    if (cs != buf[6]) {
        d.err_frames++;
        return;
    }
    d.sign        = buf[2] & 0x03;
    d.color_valid = buf[3] ? 1 : 0;
    d.color_seq   = buf[4];
    d.quality     = buf[5] > 100 ? 100 : buf[5];
    for (uint8_t i = 0; i < 4; i++) {
        d.colors[i] = (uint8_t)((d.color_seq >> (6 - 2 * i)) & 0x03);
    }
    d.last_ms = HAL_GetTick();
    d.frames++;
}

void Comm_Feed(uint8_t byte)
{
    switch (st) {
    case S_H1:
        if (byte == FRAME_HEAD1) { buf[0] = byte; idx = 1; st = S_H2; }
        break;
    case S_H2:
        if (byte == FRAME_HEAD2) { buf[1] = byte; idx = 2; st = S_SIGN; }
        else if (byte == FRAME_HEAD1) { /* 连续两个 0xAA，重新等 0x55 */ }
        else { st = S_H1; }
        break;
    case S_SIGN:  buf[idx++] = byte; st = S_CV;   break;
    case S_CV:    buf[idx++] = byte; st = S_SEQ;  break;
    case S_SEQ:   buf[idx++] = byte; st = S_Q;    break;
    case S_Q:     buf[idx++] = byte; st = S_CS;   break;
    case S_CS:
        buf[idx++] = byte;
        push_frame();
        st = S_H1;
        idx = 0;
        break;
    default:
        st = S_H1;
        break;
    }
}

const VisionData *Comm_Get(void)
{
    return &d;
}

uint8_t Comm_Alive(uint32_t now_ms)
{
    if (d.frames == 0) {
        return 0;
    }
    return (uint8_t)((now_ms - d.last_ms) < COMM_TIMEOUT_MS);
}
