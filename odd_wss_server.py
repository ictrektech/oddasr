# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_wss_server.py 
@info: 消息模版
"""

"""Server example using the asyncio API."""

import asyncio
from odd_asr_exceptions import mai_err_name, EM_ERR_ASR_ARGS_ERROR
from websockets.asyncio.server import serve
import json
from odd_asr_exceptions import *
from proto import TCMDCommonRes, obj_to_dict, TCMDApplyAsrRes
import numpy as np
import websockets

'''
client --> server: TCmdApppyAsrReq
server --> client: TCmdApppyAsrRsp with session_id
server --> server: add client to clients
client --> server: PCMData
server --> client: ASRResult

            struct TCmdApppyAsrReq
            {
                std::string msg_type = MSG_APPLY_ASR_REQ;
                std::string msg_id;
                std::string token;
                std::string session_id;	//重连的时候带
            };
'''

import uuid
import queue

from odd_asr_stream import OddAsrStream, OddAsrParamsStream
from odd_asr_result import notifyTask
import odd_asr_config as config
from log import logger

odd_asr_stream_set = set()
# odd_asr_stream_dict = dict()
_wss_server = None

def find_free_odd_asr_stream(websocket, session_id):
    '''
    找到一个空闲的odd_asr_stream
    :param websocket:
    :return:
    '''
    for odd_asr_stream in odd_asr_stream_set:
        if not odd_asr_stream.is_busy():
            odd_asr_stream.set_busy(True)
            odd_asr_stream.set_session_id(session_id)
            odd_asr_stream.set_websocket(websocket)

            return odd_asr_stream
        
    return None

def find_odd_asr_stream_by_websocket(websocket):
    '''
    找到websocket对应的odd_asr_stream
    :param websocket:
    :return:
    '''
    for odd_asr_stream in odd_asr_stream_set:
        if odd_asr_stream.get_websocket() == websocket:
            return odd_asr_stream
        
    return None

def find_odd_asr_stream_by_session_id(session_id):
    '''
    找到一个已存在的odd_asr_stream
    :param session_id:
    :return:
    '''
    for odd_asr_stream in odd_asr_stream_set:
        if odd_asr_stream.get_session_id() == session_id:
            return odd_asr_stream
    return None

class OddWssServer:
    def __init__(self):
        self._clients_set = set()
        self._sessionid_set = set()
        self._conn_sessionid = dict()
        self._sessionid_conn = dict()

    async def handle_client(self, *args, **kwargs):
        # 从参数中提取 websocket 和 path
        websocket = args[0]
        logger.debug(f"Client connected: {websocket}, args={args}, len={len(args)}, kwargs={kwargs}")
        
        # # 检查路径是否匹配
        # if path != '/v1/asr':
        #     print(f"Invalid path: {path}")
        #     await websocket.close()
        #     return
        try:
            async for message in websocket:
                if not websocket in self._clients_set:
                    '''
                    新连接上来的client，第一个消息必须是一个json.
                    msg_type: MSG_APPLY_ASR_REQ
                    msg_id: 消息id
                    token: 鉴权token
                    session_id: 正常第一次连接为空，Apply成功后，由服务端生成并返回给客户端。客户端断线重连的时候带上。
                    '''
                    result, res, session_id = self.doInit(websocket, message)

                    logger.info(f"doInit={result}, res={obj_to_dict(res)}, websocket={websocket}, session_id={session_id}")
                    await websocket.send(json.dumps(obj_to_dict(res)))

                    if result:
                        logger.debug(f"add client={websocket} to clients_set")
                    else:
                        logger.error(f"doInit failed, close client={websocket}")
                        await websocket.close()
                        return False

                    # find a odd_asr_stream
                    odd_asr_stream:OddAsrStream = find_odd_asr_stream_by_session_id(session_id=session_id)
                    if odd_asr_stream is None:
                        odd_asr_stream = find_free_odd_asr_stream(websocket, session_id)
                        if odd_asr_stream is None:
                            logger.error(f"no free odd_asr_stream, close client={websocket}")
                            await websocket.close()
                            return
                        else:
                            logger.debug(f"found free odd_asr_stream, session_id={session_id}")
                            self._sessionid_set.add(session_id)
                    else:
                        logger.debug(f"found existing odd_asr_stream, session_id={session_id}, websocket={odd_asr_stream.get_websocket()}:{websocket}")

                    self._clients_set.add(websocket)
                    self._conn_sessionid[websocket] = session_id
                    self._sessionid_conn[session_id] = websocket
                else:
                    '''
                    客户端已经申请过ASR，并且已经连接上了，此时收到的消息是PCMData
                    '''
                    self.onRecv(websocket, message)
                    continue

        finally:
            self.onClose(websocket)

    async def doSend(self, websocket, message):
        '''
        发送消息给客户端
        :param websocket:
        :param message:
        :return:
        '''
        try:
            if not isinstance(message, str):
                message = json.dumps(message)
                logger.debug(f"doSend: {message}")
            else:
                logger.debug(f"doSend: {len(message)}")
            await websocket.send(message)
        except websockets.exceptions.ConnectionClosedOK:
            logger.error(f"Connection closed normally: {websocket}")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connection closed with error: {e}, {websocket}")
        except Exception as e:
            logger.error(f"Unexpected error in doSend: {e}, {websocket}")

    async def doBroadcast(self, message):
        for client in self._clients_set:
            await client.send(message)

    def onRecv(self, websocket, pcm_data):
        logger.debug(f"onRecv: {len(pcm_data)}, websocket={websocket}")

        # Convert bytes to a NumPy array of int16
        pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
        # Convert the array to float32 and normalize it
        speech = pcm_array.astype(np.float32) / 32768.0

        # 找到对应的odd_asr_stream
        session_id = ""
        # session_id = self._conn_sessionid[websocket]
        odd_asr_stream: OddAsrStream = find_odd_asr_stream_by_websocket(websocket=websocket)
        if odd_asr_stream:
            session_id = odd_asr_stream.get_session_id()
            logger.debug(f"find_odd_asr_stream_by_websocket, session_id={session_id}")
            odd_asr_stream.transcribe_stream(speech, socket=websocket, session_id=session_id)
        else:
            logger.error(f"find_odd_asr_stream_by_websocket, not found, websocket={websocket}")

    def onClose(self, websocket):
        logger.warn(f"Client disconnected: {websocket}")
        if websocket in self._clients_set:
            '''
            客户端断开连接，需要从clients中删除。
            然而暂不在sessionid_set中删除，因为可能是客户端断线重连，此时sessionid还存在。
            但是，后面需要做一个计时器，定期检查，若超时未收到客户端的消息，则删除sessionid。
            '''
            session_id = self._conn_sessionid[websocket]

            self._sessionid_set.remove(session_id)
            self._sessionid_conn.pop(session_id)
            self._conn_sessionid.pop(websocket)
            self._clients_set.remove(websocket)
            odd_asr_stream = find_odd_asr_stream_by_session_id(session_id=session_id)

            logger.warn(f"remove session_id={session_id}, client={websocket}, odd_asr_stream={odd_asr_stream}")

            if odd_asr_stream:
                odd_asr_stream.set_websocket(None)
                odd_asr_stream.set_session_id('')
                odd_asr_stream.set_busy(False)

            logger.warn(f"remove session_id={session_id}, client={websocket}")
        else:
            logger.error(f"client={websocket} not in clients_set")

    def doInit(self, websocket, message):
        # 解析json，若第一个消息不是json，则关闭连接
        result = False
        session_id = ""
        try:
            req = json.loads(message)
        except Exception as e:
            logger.error(f"Invalid json format. Received message: {message}. webocket={websocket}")
            msg_id = ''
            msg_type = ''

            res = TCMDCommonRes(msg_id, msg_type)
            res.error_code = EM_ERR_ASR_ARGS_ERROR
            res.error_desc = mai_err_name(EM_ERR_ASR_ARGS_ERROR)

            return result, res, session_id

        # 若第一个消息不是MSG_APPLY_ASR_REQ，则关闭连接
        if req['msg_type'] != 'MSG_APPLY_ASR_REQ':
            logger.error(f"Invalid msg_type. Received message: {message}, req['msg_type']")
            msg_id = req['msg_id'] if 'msg_id' in req else ''
            msg_type = req['msg_type'] if 'msg_type' in req else ''
            res = TCMDCommonRes(msg_id, msg_type)
            res.error_code = EM_ERR_ASR_ARGS_ERROR
            res.error_desc = mai_err_name(EM_ERR_ASR_ARGS_ERROR)

            return result, res, session_id

        # 解析json中的session_id
        res = TCMDApplyAsrRes(req['msg_id'])
        if "session_id" in req and req['session_id']:
            if req['session_id'] in self._sessionid_set:
                '''若session_id已经存在，说明是之前已经申请过ASR，但是中间网络异常，并断线重连了
                '''
                res.session_id = req['session_id']
                self._sessionid_conn[req['session_id']] = websocket
                self._conn_sessionid[websocket] = req['session_id']
                session_id = req['session_id']
                result = True
            else:
                '''
                若session_id不存在，说明是一个非法请求
                '''
                logger.error(f"Received message: {message}, req['session_id']={req['session_id']}")
                res.session_id = ''
                res.error_code = EM_ERR_ASR_SESSION_ID_NOVALID
                res.error_desc = mai_err_name(EM_ERR_ASR_SESSION_ID_NOVALID)
                result = False
        else:
            '''
            若session_id为空，说明是第一次申请ASR，需要生成一个session_id
            '''
            res.session_id = str(uuid.uuid1())
            self._sessionid_set.add(res.session_id)
            self._sessionid_conn[res.session_id] = websocket
            self._conn_sessionid[websocket] = res.session_id
            session_id = res.session_id
            result = True

        return result, res, session_id


    async def send(self, websocket, message):
        await websocket.send(message)

async def notify_task(_wss_server=None):
    global asr_result_queue
    while True:
        try:
            # 使用 asyncio.to_thread 从队列获取消息
            message = await asyncio.to_thread(asr_result_queue.get, timeout=1)
            logger.debug(f"notifyTask: {message.text}")

            if _wss_server:
                if message.webocket in _wss_server._clients_set:
                    # 发送消息给客户端
                    logger.debug(f"notifyTask: send to client={message.webocket}")
                    await _wss_server.doSend(message.webocket, message.text)
        except queue.Empty:
            # 队列为空，继续等待
            continue
        except Exception as e:
            # 处理其他异常
            logger.error(f"notifyTask error: {e}")
            continue


def init_instances_stream(server: OddWssServer):
    '''
    初始化odd_asr_stream实例。
    由于初始化加载模型比较耗时，所以在启动的时候就预加载。
    电脑内存太小，默认这里只初始化2个实例。
    每个odd_asr_stream实例对应一个websocket连接。
    每个websocket连接对应一个odd_asr_stream实例。
    每个odd_asr_stream实例对应一个session_id。
    每个session_id对应一个websocket连接。
    每个websocket连接对应一个session_id。
    每个session_id对应一个odd_asr_stream实例。
    :param server:
    :return:
    '''
    max_instance = config.asr_stream_cfg["max_instance"]
    if max_instance <= 0:
        max_instance = 2

    for i in range(max_instance):
        odd_asr_stream_param: OddAsrParamsStream = OddAsrParamsStream(
            mode="stream",
            hotwords="", 
            audio_rec_filename="",
            # result_callback=server.doSend,
        )
        odd_asr_stream = OddAsrStream(odd_asr_stream_param)
        odd_asr_stream_set.add(odd_asr_stream)

def init_notify_task(server: OddWssServer):
    '''
    初始化notifyTask
    :param server:
    :return:
    '''
    notify_Task = notifyTask()
    notify_Task.start(server)

async def start_wss_server():
    global _wss_server
    _wss_server = OddWssServer()

    init_notify_task(_wss_server)
    init_instances_stream(_wss_server)

    async with serve(_wss_server.handle_client, config.WS_HOST, config.WS_PORT):
        await asyncio.Future()  # run forever    

if __name__ == "__main__":
    asyncio.run(start_wss_server())
