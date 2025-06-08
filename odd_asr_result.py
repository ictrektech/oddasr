# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: result.py 
@time: 2025/6/9 15:00
@info: 消息模版
"""

import threading
import queue
import asyncio
from log import logger

# 创建一个线程安全的优先级队列
asr_result_queue = queue.SimpleQueue()

class Result:
    def __init__(self):
        self._result = {}

    def set_code(self, error_code):
        self._result['error_code'] = error_code

    def set_msg(self, error_desc):
        self._result['error_desc'] = error_desc

    def set_data(self, data):
        self._result['data'] = data

    @property
    def result(self):
        return self._result


def from_exc(exc):
    r = Result()
    r.set_code(exc.error_code)
    r.set_msg(exc.error_desc)
    return r.result


def from_data(data):
    r = Result()
    r.set_data(data)
    return r.result


class OddAsrStreamResult:
    def __init__(self, webocket, text, is_final=False, is_last=False):
        self.webocket = webocket
        self.text = text
        self.is_final = is_final
        self.is_last = is_last

def enque_asr_result(message: OddAsrStreamResult):
    global asr_result_queue
    asr_result_queue.put(message)
    
    logger.debug(f"asr result queue size={asr_result_queue.qsize()}")

async def notify_task(_wss_server=None):
    global asr_result_queue
    logger.debug(f"=============================================notifyTask: start===================================")
    while True:
        try:
            if not asr_result_queue.empty():
                # print(f"queue size={asr_result_queue.qsize()}")
                message = asr_result_queue.get()
                # print(f"notifyTask: {message.text}")

                if _wss_server:
                    if message.webocket in _wss_server._clients_set:
                        # 发送消息给客户端
                        # print(f"notifyTask: send to client={message.webocket}")
                        await _wss_server.doSend(message.webocket, message.text)
            else:
                # print(f"notifyTask: queue empty")
                # 队列为空，等待一段时间后再检查
                await asyncio.sleep(0.1)
        except Exception as e:
            # 处理其他异常
            logger.error(f"notifyTask error: {e}")
            continue

class notifyTask():
    @staticmethod
    def start(wss_server=None, loop=None):
        # 获取当前事件循环
        if not loop:
            loop = asyncio.get_running_loop()
        # 创建后台线程
        loop.create_task(notify_task(wss_server))
        # 将后台线程设置为守护线程，以便在主线程结束时自动退出
        logger.info("=> Start ASR result dispatch Task Success")


