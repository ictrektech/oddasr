# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: testStreamAPI.py 
@info: 消息模版
"""

"""Client example using the asyncio API."""

'''
    client --> server: connect
    client --> server: TCmdApppyAsrReq, msg_type = MSG_APPLY_ASR_REQ;
    server --> client: TCmdApplyAsrRes, msg_type = MSG_SUBSCRIBE_INIT_RES;
    client --> server: TCMDTranscribeReq, msg_type = MSG_TRANSCRIBE_REQ;
    server --> client: TCMDTranscribeRes, msg_type = MSG_TRANSCRIBE_RES;

    struct TCmdApppyAsrReq
    {
        std::string msg_type = MSG_APPLY_ASR_REQ;
        std::string msg_id;
        std::string token;
        std::string session_id;	//重连的时候带
    };


    TCMDTranscribeReq

'''

import asyncio
import json
import time
import websockets
import enum

from websockets.asyncio.client import connect
from log import logger

class odd_asr_state(enum.Enum):
    EM_ASR_STATE_IDLE = 0,
    EM_ASR_STATE_APPLYING = 1,
    EM_ASR_STATE_APLLY_OK = 2,
    EM_ASR_STATE_APPLY_FAILED = 3,
    EM_ASR_STATE_RECOGNIZING = 4,

state: odd_asr_state = odd_asr_state.EM_ASR_STATE_IDLE

async def receive_messages(websocket):
    global state
    """
    异步接收服务端消息的函数
    :param websocket: WebSocket 连接对象
    """
    while True:
        try:
            # 接收服务端消息
            message = await websocket.recv()
            match state:
                case odd_asr_state.EM_ASR_STATE_IDLE:
                    continue
                case odd_asr_state.EM_ASR_STATE_APPLYING:
                    res = json.loads(message)
                    logger.debug(f"<<< {res}")
                    if res["msg_type"] == "MSG_APPLY_ASR_RES":
                        if res["error_code"] == 0:
                            state = odd_asr_state.EM_ASR_STATE_APLLY_OK
                            logger.info("client doInit ok")
                            state = odd_asr_state.EM_ASR_STATE_RECOGNIZING
                        else:
                            state = odd_asr_state.EM_ASR_STATE_APPLY_FAILED
                    continue
                case odd_asr_state.EM_ASR_STATE_APLLY_OK:
                    continue
                case odd_asr_state.EM_ASR_STATE_APPLY_FAILED:
                    continue
                case odd_asr_state.EM_ASR_STATE_RECOGNIZING:
                    res = json.loads(message)
                    logger.debug(f"<<< {res}")
                case _:
                    continue

        except websockets.exceptions.ConnectionClosedOK:
            logger.error("Connection closed gracefully")
            break
        except Exception as e:
            logger.error(f"Receive error: {e}")
            break

async def send_messages(websocket):
    global state
    offset = 0
    total_length = 0
    chunk_size = 9600*2

    # 发送PCM数据
    with open("test.pcm", "rb") as f:
        data = f.read()

    total_length = len(data)
    logger.debug(f"total_length={total_length}")

    # 循环发送消息给服务端
    while True:
        await asyncio.sleep(0.1)
        match state:
            case odd_asr_state.EM_ASR_STATE_IDLE:
                req = {"msg_type": "MSG_APPLY_ASR_REQ", "msg_id": "", "token": "", "session_id": ""}
                logger.debug(f">>>client doInit req: {req}")

                await websocket.send(json.dumps(req))
                logger.debug(">>>client doInit req sent")
                state = odd_asr_state.EM_ASR_STATE_APPLYING
                continue
            case odd_asr_state.EM_ASR_STATE_APPLYING:
                continue
            case odd_asr_state.EM_ASR_STATE_APLLY_OK:
                continue
            case odd_asr_state.EM_ASR_STATE_APPLY_FAILED:
                continue
            case odd_asr_state.EM_ASR_STATE_RECOGNIZING:
                chunk = data[offset:offset + chunk_size]
                await websocket.send(chunk)
                logger.debug(f"send chunk {offset}")
                offset += chunk_size

                if offset >= total_length:
                    logger.info("send end")
                    break
                await asyncio.sleep(0.2)
                continue
            case _:
                continue

async def hello():
    async with connect("ws://localhost:8765/v1/asr") as websocket:

        send_task = asyncio.create_task(send_messages(websocket))
        receive_task = asyncio.create_task(receive_messages(websocket))

        # 等待接收任务完成
        await asyncio.gather(send_task, receive_task)
        
if __name__ == "__main__":
    asyncio.run(hello())
