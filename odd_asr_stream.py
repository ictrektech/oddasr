# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_asr_stream.py 
@info: 消息模版
"""

import torch
import numpy as np

import queue
import threading
import time
import copy

import os
from funasr import AutoModel
from log import logger
from odd_asr_result import enque_asr_result, OddAsrStreamResult
import odd_asr_config as config

class AudioFrame:
    def __init__(self, data, sr: int = 16000, channel=1, bit_depth=16, timestamp = 0):
        self.data = data  # 音频数据
        self.timestamp = timestamp  # 时间戳
        self.sr = sr  # 采样率
        self.channel = 1  # 声道数
        self.bit_depth = 16  # 位深度

class OddAsrParamsStream:
    _transcription_thread: threading.Thread = None
    _audio_queue: queue.Queue = None
    _stop_event: threading.Event = None
    _rec_file:str =""
    _result_callback = None

    _is_busy = False  # 初始化时设置为 False
    _websocket = None
    _session_id = None

    def __init__(self, 
                 mode="stream", 
                 hotwords="", 
                 audio_rec_filename="",
                 result_callback=None,
                 return_raw_text=True, 
                 is_final=True, 
                 sentence_timestamp=False, 
                 chunk_size=[0, 10, 5], 
                 encoder_chunk_look_back=4, 
                 decoder_chunk_look_back=1,
                 ):
        self.mode = mode  # mode should be a string like 'file','stream', 'pipeline'
        self.hotwords = hotwords  # hotwords should be a string like 'word1 word2'
        self._rec_file = audio_rec_filename  # audio_rec_filename should be a string like 'audio.wav'
        self._result_callback = result_callback

        self.return_raw_text=return_raw_text #return raw text or not, default is True, if False, return json format result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]]}, 
        self.is_final=is_final  #is_final=True, if False, return partial result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False},
        self.sentence_timestamp=sentence_timestamp  #sentence_timestamp=False, if True, return sentence timestamp, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False, sentence_timestamp: [[0, 2000]]},

        self.chunk_size = [0, 10, 5] #[0, 10, 5] 600ms, [0, 8, 4] 480ms
        self.chunk_size = chunk_size  #chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking
        self.encoder_chunk_look_back = encoder_chunk_look_back #number of chunks to lookback for encoder self-attention
        self.decoder_chunk_look_back = decoder_chunk_look_back #number of encoder chunks to lookback for decoder cross-attention

        self._audio_queue = queue.Queue()
        self._stop_event = threading.Event()

        # check chunk_size is valid, chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking, chunk_size[1] is the chunk size, in ms, chunk_size[2] is the overlap size, in ms
        if len(self.chunk_size) != 3:
            raise ValueError("chunk_size should be a list of 3 elements, chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking, chunk_size[1] is the chunk size, in ms, chunk_size[2] is the overlap size, in ms")
        if self.chunk_size[0] < -1 or self.chunk_size[0] > 60000:
            raise ValueError("chunk_size[0] should be between -1 and 60000, in ms")
        if self.chunk_size[1] < 0 or self.chunk_size[1] > 60000:
            raise ValueError("chunk_size[1] should be between 0 and 60000, in ms")
        if self.chunk_size[2] < 0 or self.chunk_size[2] > 60000:
            raise ValueError("chunk_size[2] should be between 0 and 60000, in ms")
        
    def _default_callback(self, result):

        print(result)

class OddAsrStream:

    def __init__(self, streamParam:OddAsrParamsStream=None):
        # 初始化 OddAsrParamsStream 实例
        if streamParam is None:
            self.streamParam = OddAsrParamsStream()
        else:
            self.streamParam = streamParam

        # auto detect GPU device
        if config.enable_gpu:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = "cpu"

        self.load_stream_model(self.device)

        self.lock = threading.Lock()  # 初始化锁

    def set_busy(self, is_busy):
        with self.lock:  # 使用锁保护共享资源
            self.streamParam._is_busy = is_busy
            if not is_busy:
                logger.info(f"set_busy to False, clear _stop_event, websocket={self.streamParam._websocket}, session_id={self.streamParam._session_id}")
                self.streamParam._stop_event.set()
                self.streamParam._transcription_thread.join()
                self.streamParam._transcription_thread = None
                self.streamParam._audio_queue.empty()
                logger.info(f"set_busy to False, clear _stop_event,done")

    def is_busy(self):
        with self.lock:  # 使用锁保护共享资源
            return self.streamParam._is_busy
        
    def set_websocket(self, websocket):
        with self.lock:  # 使用锁保护共享资源
            self.streamParam._websocket = websocket
    
    def get_websocket(self):
        with self.lock:  # 使用锁保护共享资源
            return self.streamParam._websocket
        
    def set_session_id(self, session_id):
        with self.lock:  # 使用锁保护共享资源
            self.streamParam._session_id = session_id

    def get_session_id(self):
        with self.lock:  # 使用锁保护共享资源
            return self.streamParam._session_id

    def load_stream_model(self, device="cuda:0"):
        # load stream model
        self.stream_model = AutoModel(
            model="paraformer-zh-streaming", model_revision="v2.0.4",
            # vad_model='iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', vad_model_revision="v2.0.4",
            # punc_model='iic/punc_ct-transformer_cn-en-common-vocab471067-large', punc_model_revision="v2.0.4",
            # spk_model="cam++",
            log_level="error",
            hub="ms",  # hub：表示模型仓库，ms为选择modelscope下载，hf为选择huggingface下载。
            device=device,
            disable_update=True,
        )

    def transcribe_stream(self, audio_frame, socket=None, session_id=""):
        '''
        transcribe audio stream, support real-time transcription, 
        and return partial result, like: 
            {
                text: "hello world", 
                timestamp: [[0, 1000], [1000, 2000]], 
                is_final: False, 
                sentence_timestamp: [[0, 2000]]
            },
        and return final result, like:
            {
                text: "hello world",
                timestamp: [[0, 1000], [1000, 2000]],
                is_final: True,
                sentence_timestamp: [[0, 2000]]
            }

        1. start a thread to transcribe audio stream
        2. add input audio_frame to queue
        3. empty queue, yield result and stop transcribe thread if got an EOF
        '''
        try:
            if self.streamParam._audio_queue is None:
                logger.error(f"_audio_queue is None")
                return ""
            if self.streamParam._stop_event is None:
                logger.error(f"_stop_event is None")
                return ""
            if self.stream_model is None:
                self.load_stream_model()

            # Create and start the transcription thread
            if self.streamParam._transcription_thread is None or not self.streamParam._transcription_thread.is_alive():
                self.streamParam._stop_event.clear()  # 确保 _stop_event 未被设置
                logger.info(f"start transcription_thread, websocket={socket}, session_id={session_id}")
                # self.streamParam._transcription_thread = threading.Thread(target=self._transcribe_thread_wrapper, args=(self.streamParam,))
                self.streamParam._transcription_thread = threading.Thread(target=self._transcribe_thread_wrapper)
                self.streamParam._transcription_thread.daemon = True  # 设置为守护线程
                self.streamParam._transcription_thread.start()

            # DONT terminite the thread, just add an empty audio_frame to queue, let the previous frames to be processed
            if audio_frame is None:  # Receive EOF signal
                frame = AudioFrame(data=None)  # Put EOF signal
                self.streamParam._audio_queue.put(frame)
            else:
                copied_audio_frame = copy.deepcopy(audio_frame)
                frame = AudioFrame(data=copied_audio_frame)
                self.streamParam._audio_queue.put(frame)

        except Exception as e:
            logger.error(f"Error in transcribe_stream: {e}")
            self.streamParam._stop_event.set()  # Stop the thread in case of an error
            if self.streamParam._transcription_thread is not None and self.streamParam._transcription_thread.is_alive():
                self.streamParam._transcription_thread.join()  # Wait for the thread to finish
                self.streamParam._transcription_thread = None
            raise RuntimeError(f"Error processing audio stream: {e}")


    def _save_audio_rec(self, filename, audio_data, sample_rate=16000):
        try:
            # # 保存文件
            # if not os.path.exists(os.path.dirname(filename)):
            #     os.makedirs(os.path.dirname(filename))

            # 确保 audio_data 是 NumPy 数组
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)

            # 若 audio_data 是浮点数类型，转换回 16 位有符号整数
            if audio_data.dtype == np.float32:
                audio_data = (audio_data * 32767).astype(np.int16)

            # 直接写入二进制文件
            with open(filename, 'ab') as binfile:
                audio_data.tofile(binfile)
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")

    def _transcribe_thread_wrapper(self):
        # for result in self._transcribe_thread(param):
        #     # 这里可以根据需求处理生成器的输出
        #     logger.info(f"Transcription result: {result}")
        import asyncio
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        chunk_size = [0, 10, 5] #[0, 10, 5] 600ms, [0, 8, 4] 480ms
        encoder_chunk_look_back = 4 #number of chunks to lookback for encoder self-attention
        decoder_chunk_look_back = 1 #number of encoder chunks to lookback for decoder cross-attention
        is_final = False
        cache = {}
        hotwords = ""

        tasks = []  # 用于存储所有异步任务

        if self.streamParam.hotwords is not None and self.streamParam.hotwords != "":
            hotwords = self.streamParam.hotwords.split(" ")

        try:
            while not self.streamParam._stop_event.is_set():
                # 从队列中获取音频帧，设置超时时间为 1 秒
                logger.info(f"queue length: {self.streamParam._audio_queue.qsize()},websocket={self.streamParam._websocket}")
                try:
                    frame: AudioFrame = self.streamParam._audio_queue.get(timeout=1)
                except queue.Empty:  # 超时后继续循环
                    time.sleep(0.1)
                    continue

                if frame.data is None:  # 收到 EOF 信号
                    logger.warn(f"Received EOF signal, stopping transcription thread.")
                    is_final = True
                    break

                # 保存到录音文件
                if self.streamParam._rec_file != "":
                    self._save_audio_rec(self.streamParam._rec_file, frame.data, frame.sr)
                
                speech = frame.data

                chunk_stride = chunk_size[1] * 960 # 600ms
                total_chunk_num = int(len(speech)/chunk_stride)
                logger.info(f"Processing frame, stride: {chunk_stride}, data={len(speech)}, total_chunk_num={total_chunk_num}, speech type={type(speech)}")

                for i in range(total_chunk_num):
                    start = i * chunk_stride
                    end = start + chunk_stride
                    audio_chunk = speech[start:end]

                    logger.info(f"start={start}, end={end}, audio_chunk type: {type(audio_chunk)}, audio_chunk shape: {audio_chunk.shape}")

                    try:
                        text = self.stream_model.generate(input=audio_chunk, 
                                                          input_len=len(audio_chunk),
                                                            cache=cache, 
                                                            is_final=is_final, 
                                                            # return_raw_text=True,
                                                            # sentence_timestamp=True,
                                                            # hotword=hotwords,
                                                            chunk_size=chunk_size, 
                                                            encoder_chunk_look_back=encoder_chunk_look_back, 
                                                            decoder_chunk_look_back=decoder_chunk_look_back
                                                            )

                        logger.info(f"res={text}, websocket={self.streamParam._websocket}")
                        websocket = self.streamParam._websocket
                        if websocket is not None:
                            result = OddAsrStreamResult(websocket, text)
                            enque_asr_result(result)

                    except Exception as e:
                        logger.error(f"Error processing audio chunk: {e}")
                        continue
                time.sleep(0.1)

            logger.info(f"Transcription thread stopped.")

            websocket = self.streamParam._websocket
            if websocket is not None:
                result = OddAsrStreamResult(websocket, "END", is_final=True, is_last=True)
                enque_asr_result(result)

            if tasks:
                loop.run_until_complete(asyncio.gather(*tasks))

        except Exception as e:
            logger.error(f"Error in transcription thread: {e}")
        finally:
            logger.info(f"Transcription thread stopped.")
            loop.close()


