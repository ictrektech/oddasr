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

async def send_messages(websocket, file):
    global state
    offset = 0
    total_length = 0
    chunk_size = 9600*2

    with open(file, "rb") as f:
        data = f.read()

    total_length = len(data)
    logger.debug(f"total_length={total_length}")

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

async def hello(file):
    async with connect("ws://localhost:12341/v1/asr") as websocket:

        send_task = asyncio.create_task(send_messages(websocket, file))
        receive_task = asyncio.create_task(receive_messages(websocket))

        # 等待接收任务完成
        await asyncio.gather(send_task, receive_task)
        
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Your WAV file need to recoginze to text.")
    parser.add_argument("audio_path", type=str, help="file path of your input WAV.")
    args = parser.parse_args()

    file = args.audio_path
    print(f"Current working directory: {os.getcwd()}")
    print(f"Full file path: {os.path.abspath(file)}")

    if not os.path.exists(file):
        print(f"File not found: {file}")
        exit(1) 

    # detect current test file is wav file
    if not file.endswith(".wav") and not file.endswith(".pcm"):
        print(f"File format error: {file}. Please input wav or pcm file.")
        exit(1)

    # check file format, sample rate must be 16000, sample width must be 16bit, channels must be 1
    if file.endswith(".wav"):
        import soundfile as sf
        with sf.SoundFile(file) as f:
            if f.samplerate != 16000:
                print(f"File sample rate error: {file}. Please input 16000 sample rate, while input {f.samplerate}")
                exit(1)
            if f.subtype != 'PCM_16':
                print(f"File sample width error: {file}. Please input 16bit sample width, while input {f.subtype}")
                exit(1)
            if f.channels != 1:
                print(f"File channels error: {file}. Please input 1 channel, while input {f.channels}")
                exit(1)

    asyncio.run(hello(file))
