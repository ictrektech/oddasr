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
import re
import copy

import os
from funasr import AutoModel
from log import logger
from odd_asr_result import enque_asr_result, OddAsrStreamResult
import odd_asr_config as config

class AudioFrame:
    def __init__(self, data, sr: int = 16000, channel=1, bit_depth=16, timestamp = 0):
        self.data = data            # 音频数据
        self.timestamp = timestamp  # 时间戳
        self.sr = sr                # 采样率
        self.channel = channel      # 声道数
        self.bit_depth = 16         # 位深度

class OddAsrStats:
    def __init__(self):
        self.index = 0
        self.start_time = 0
        self.end_time = 0
        self.total_audio_recv_len = 0
        self.total_audio_input_len = 0
        self.total_asr_len = 0
        self.total_asr_time = 0


class OddAsrParamsStream:
    _mode: str = "stream"
    _hotwords: str = "oddmeta xiaoluo"
    _rec_file:str =""
    _result_callback = None
    _result_callback: bool = False
    _is_final : bool = False
    _sentence_timestamp: bool = False

    _chunk_size:list = [0, 10, 5]
    _encoder_chunk_look_back: int = 4
    _decoder_chunk_look_back: int = 1

    _transcription_thread: threading.Thread = None
    _audio_queue: queue.Queue = None
    _stop_event: threading.Event = None
    _audio_cache: np.ndarray = np.array([], dtype=np.float32) 
    _text_cache: str = ""

    _is_busy = False
    _websocket = None
    _stats = OddAsrStats()
    task_id = None

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
        self._mode = mode  # mode should be a string like 'file','stream', 'pipeline'
        self._hotwords = hotwords  # hotwords should be a string like 'word1 word2'
        self._rec_file = audio_rec_filename  # audio_rec_filename should be a string like 'audio.wav'
        self._result_callback = result_callback

        self._return_raw_text=return_raw_text #return raw text or not, default is True, if False, return json format result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]]}, 
        self._is_final=is_final  #is_final=True, if False, return partial result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False},
        self._sentence_timestamp=sentence_timestamp  #sentence_timestamp=False, if True, return sentence timestamp, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False, sentence_timestamp: [[0, 2000]]},

        self._chunk_size = [0, 10, 5] #[0, 10, 5] 600ms, [0, 8, 4] 480ms
        self._chunk_size = chunk_size  #chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking

        self._encoder_chunk_look_back = encoder_chunk_look_back #number of chunks to lookback for encoder self-attention
        self._decoder_chunk_look_back = decoder_chunk_look_back #number of encoder chunks to lookback for decoder cross-attention

        self._audio_queue = queue.Queue()
        self._stop_event = threading.Event()

        # check chunk_size is valid, chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking, chunk_size[1] is the chunk size, in ms, chunk_size[2] is the overlap size, in ms
        if len(self._chunk_size) != 3:
            raise ValueError("chunk_size should be a list of 3 elements, chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking, chunk_size[1] is the chunk size, in ms, chunk_size[2] is the overlap size, in ms")
        if self._chunk_size[0] < -1 or self._chunk_size[0] > 60000:
            raise ValueError("chunk_size[0] should be between -1 and 60000, in ms")
        if self._chunk_size[1] < 0 or self._chunk_size[1] > 60000:
            raise ValueError("chunk_size[1] should be between 0 and 60000, in ms")
        if self._chunk_size[2] < 0 or self._chunk_size[2] > 60000:
            raise ValueError("chunk_size[2] should be between 0 and 60000, in ms")
        
    def _default_callback(self, result):

        print(result)

class OddAsrStream:
    punc_model = None
    stream_model = None
    streamParam: OddAsrParamsStream = None
    device: str = "cuda:0"
    lock: threading.Lock = None

    def __init__(self, streamParam:OddAsrParamsStream=None):
        # 初始化 OddAsrParamsStream 实例
        if streamParam is None:
            self.streamParam = OddAsrParamsStream()
        else:
            self.streamParam = streamParam

        self.stream_model = None

        # auto detect GPU device
        if config.odd_asr_cfg["enable_gpu"]:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = "cpu"

        if config.odd_asr_cfg["preload_model"]:
            self._load_stream_model(self.device)

        self.lock = threading.Lock()  # 初始化锁

    def set_busy(self, is_busy):
        with self.lock:  # 使用锁保护共享资源
            self.streamParam._is_busy = is_busy
            if not is_busy:
                logger.info(f"set_busy to False, clear _stop_event, websocket={self.streamParam._websocket}, task_id={self.streamParam.task_id}")
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
        
    def set_session_id(self, task_id):
        with self.lock:  # 使用锁保护共享资源
            self.streamParam.task_id = task_id

    def get_session_id(self):
        with self.lock:  # 使用锁保护共享资源
            return self.streamParam.task_id

    def _load_stream_model(self, device="cuda:0"):
        # load stream model
        if not self.stream_model:
            self.stream_model = AutoModel(
                model="paraformer-zh-streaming", model_revision="v2.0.4",

                # vad_model='iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', vad_model_revision="v2.0.4",
                vad_model="fsmn-vad", vad_model_revision="v2.0.4",

                # punc_model='iic/punc_ct-transformer_cn-en-common-vocab471067-large', punc_model_revision="v2.0.4",
                # punc_model='iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-large', punc_model_revision="v2.0.4",
                # punc_model='iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727', punc_model_revision="v2.0.4",

                # spk_model="cam++",
                log_level="info",
                hub="ms",  # hub：表示模型仓库，ms为选择modelscope下载，hf为选择huggingface下载。
                device=device,
                disable_update=True,
            )

        if not self.punc_model:
            '''
            from modelscope.pipelines import pipeline
            from modelscope.utils.constant import Tasks

            inference_pipeline = pipeline(
                task=Tasks.punctuation,
                model='damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727'
            )

            inputs = "跨境河流是养育沿岸|人民的生命之源长期以来为帮助下游地区防灾减灾中方技术人员|在上游地区极为恶劣的自然条件下克服巨大困难甚至冒着生命危险|向印方提供汛期水文资料处理紧急事件中方重视印方在跨境河流问题上的关切|愿意进一步完善双方联合工作机制|凡是|中方能做的我们|都会去做而且会做得更好我请印度朋友们放心中国在上游的|任何开发利用都会经过科学|规划和论证兼顾上下游的利益"
            vads = inputs.split("|")
            rec_result_all="outputs:"
            param_dict = {"cache": []}
            for vad in vads:
                rec_result = inference_pipeline(text_in=vad, param_dict=param_dict)
                rec_result_all += rec_result['text']

            print(rec_result_all)            
            '''

            self.punc_model = AutoModel(
                # model='iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-large', punc_model_revision="v2.0.4",
                model="iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727", model_revision="v2.0.4",
                hub="ms",  # hub：表示模型仓库，ms为选择modelscope下载，hf为选择huggingface下载。
                device=device,
                disable_update=True,
            )


    def transcribe_stream(self, audio_frame, socket, task_id):
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
                self._load_stream_model()

            # Create and start the transcription thread
            if self.streamParam._transcription_thread is None or not self.streamParam._transcription_thread.is_alive():
                self.streamParam._stop_event.clear()  # 确保 _stop_event 未被设置
                # self.streamParam._transcription_thread = threading.Thread(target=self._transcribe_thread_wrapper, args=(self.streamParam,))
                self.streamParam._transcription_thread = threading.Thread(target=self._transcribe_thread_wrapper)
                self.streamParam._transcription_thread.daemon = True  # 设置为守护线程

                logger.info(f"start transcription_thread, websocket={socket}, task_id={task_id}")

                self.streamParam._transcription_thread.start()
                self.streamParam._stats.start_time = time.time()
            # else:
            #     logger.info(f"transcription_thread is running, websocket={socket}, task_id={task_id}")

            # DONT terminite the thread, just add an empty audio_frame to queue, let the previous frames to be processed
            if audio_frame is None:  # Receive EOF signal
                if self.streamParam._audio_cache.size > 0:
                    # 直接将numpy数组放入队列（无需转换为bytes）
                    cache_array = (self.streamParam._audio_cache * 32768).astype(np.int16)
                    frame = AudioFrame(data=cache_array)
                    self.streamParam._audio_queue.put(frame)
                    self.streamParam._audio_cache = np.array([], dtype=np.float32)  # 清空缓存
                # 放入EOF信号
                frame = AudioFrame(data=None)
                self.streamParam._audio_queue.put(frame)
            else:
                if type(audio_frame) is not bytes:
                    logger.error(f"audio_frame is not bytes, type={type(audio_frame)}")
                    return ""

                # Convert bytes to a NumPy array of int16
                pcm_array = np.frombuffer(audio_frame, dtype=np.int16)
                # Convert the array to float32 and normalize it
                new_audio_array = pcm_array.astype(np.float32) / 32768.0

                # Ensure new_audio_array is 1-dimensional
                if new_audio_array.ndim == 0:
                    new_audio_array = np.array([new_audio_array], dtype=np.float32)
                
                # 计算chunk_stride（基于numpy数组长度，假设采样率16000Hz）
                # chunk_stride = int(self.streamParam._chunk_size[1] * 0.001 * 16000)  # ms转样本数
                chunk_stride = self.streamParam._chunk_size[1] * 960 # 600ms
                
                # 合并缓存和新音频数组
                combined_data = np.concatenate([self.streamParam._audio_cache, new_audio_array])
                data_len = len(combined_data)
                
                # 按chunk_stride分割numpy数组
                if data_len >= chunk_stride:
                    num_chunks = data_len // chunk_stride
                    # 处理完整块
                    for i in range(num_chunks):
                        start = i * chunk_stride
                        end = start + chunk_stride
                        chunk_data = combined_data[start:end]
                        frame = AudioFrame(data=chunk_data)
                        self.streamParam._audio_queue.put(frame)
                    # 保存剩余数据到缓存
                    self.streamParam._audio_cache = combined_data[num_chunks * chunk_stride:]
                else:
                    # 数据不足chunk_stride，存入缓存
                    self.streamParam._audio_cache = combined_data

                self.streamParam._stats.total_audio_recv_len += len(audio_frame)

        except Exception as e:
            logger.error(f"Error in transcribe_stream: {e}")
            self.streamParam._stop_event.set()  # Stop the thread in case of an error
            if self.streamParam._transcription_thread is not None and self.streamParam._transcription_thread.is_alive():
                self.streamParam._transcription_thread.join()  # Wait for the thread to finish
                self.streamParam._transcription_thread = None
            raise RuntimeError(f"Error processing audio stream: {e}")

    def _save_audio_rec(self, filename, audio_data, sample_rate=16000):
        try:
            # 保存文件
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

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

        # chunk_size = [0, 10, 5] #[0, 10, 5] 600ms, [0, 8, 4] 480ms
        # encoder_chunk_look_back = 4 #number of chunks to lookback for encoder self-attention
        # decoder_chunk_look_back = 1 #number of encoder chunks to lookback for decoder cross-attention
        is_final = False
        cache = {}
        punc_cache = []
        hotwords = ""

        tasks = []  # 用于存储所有异步任务

        if self.streamParam._hotwords is not None and self.streamParam._hotwords != "":
            hotwords = self.streamParam._hotwords.split(" ")

        try:
            while not self.streamParam._stop_event.is_set():
                # STEP 1. read from queue, timeout 1 second
                try:
                    frame: AudioFrame = self.streamParam._audio_queue.get(timeout=1)
                    logger.debug(f"queue length: {self.streamParam._audio_queue.qsize()},websocket={self.streamParam._websocket}")
                except queue.Empty:  # sleep 100ms if read timeout
                    time.sleep(0.1)
                    continue

                if frame.data is None:  # EOF received
                    logger.warn(f"Received EOF signal, stopping transcription thread.")
                    is_final = True
                    # break

                # STEP 2. save the pcm to a record file
                if config.odd_asr_cfg["asr_stream_cfg"]["save_audio"]:
                    if self.streamParam._rec_file == "":
                        self.streamParam._rec_file = "tmp/" + self.streamParam.task_id + ".pcm"
                    logger.debug(f"save audio frame to {self.streamParam._rec_file}, sr={frame.sr}, len={len(frame.data)}")
                    self._save_audio_rec(self.streamParam._rec_file, frame.data, frame.sr)

                speech = frame.data
                websocket = self.streamParam._websocket

                # STEP 3. Spit the audio to chunks, each chunk should match the chunk_size initialized in streamParam 
                chunk_stride = self.streamParam._chunk_size[1] * 960 # 600ms
                total_chunk_num = int(len(speech)/chunk_stride)
                logger.info(f"Processing frame, stride: {chunk_stride}, data={len(speech)}, total_chunk_num={total_chunk_num}, is_final={is_final}")

                for i in range(total_chunk_num):
                    start = i * chunk_stride
                    end = start + chunk_stride
                    audio_chunk = speech[start:end]

                    logger.info(f"start={start}, end={end}, audio_chunk type: {type(audio_chunk)}, audio_chunk shape: {audio_chunk.shape}")

                    # STEP 3.1 VAD
                    vad_result = self.stream_model.vad(audio_chunk)
                    if not vad_result.is_speech:
                        logger.debug(f"No speech detected in chunk {i}, skipping...")
                        continue
                    logger.info(f"VAD result: {vad_result}")

                    # STEP 4. Transcribe the audio chunk
                    try:
                        text = self.stream_model.generate(input=audio_chunk, 
                                                            input_len=len(audio_chunk), 
                                                            cache=cache, 
                                                            is_final=is_final, 
                                                            # return_raw_text=True,
                                                            sentence_timestamp=True,
                                                            use_punc=True,
                                                            punc_threshold=0.5,
                                                            hotword=hotwords, 
                                                            chunk_size=self.streamParam._chunk_size, 
                                                            encoder_chunk_look_back=self.streamParam._encoder_chunk_look_back, 
                                                            decoder_chunk_look_back=self.streamParam._decoder_chunk_look_back
                                                            )

                        self.streamParam._stats.total_audio_input_len += len(audio_chunk)
                        self.streamParam._stats.start_time = self.streamParam._stats.total_audio_input_len*1000/256000
                        logger.info(f"res={text}, websocket={websocket}, total input={self.streamParam._stats.total_audio_input_len}, start_time={self.streamParam._stats.start_time}")

                        # skip the empty text
                        if text[0]["text"] == "":
                            continue
                        self.streamParam._text_cache += text[0]["text"]

                        # dont input punc model if current length is less than the configuration value
                        # TODO time is also an important factor
                        if len(self.streamParam._text_cache) < config.odd_asr_cfg["asr_stream_cfg"]["punct_mini_len"]:
                            result = OddAsrStreamResult(self.punc_model, websocket, self.streamParam._text_cache, is_final=False, index=self.streamParam._stats.index, begin_time=self.streamParam._stats.start_time)
                            enque_asr_result(result)
                            continue

                    except Exception as e:
                        logger.error(f"Error in transcribe_stream: {e}")
                        continue

                    # STEP 5. Generate the punctuations
                    try:
                        input_text = self.streamParam._text_cache

                        '''
                        [
                            {
                                'key': 'rand_key_CwYyBZFyUoYmC', 
                                'text': '一二三四五六七八七六五四三二一一三四五三三。打老虎传前明月光 疑是地上霜', 
                                'punc_array': tensor([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3])
                            }
                        ]
                        '''
                        punc_result = self.punc_model.generate(input=input_text, punc_threshold=0.5)
                        logger.info(f"punctuation: \n\tinput={input_text}\n\tpunc_result={punc_result}")
                        punc_result_text = punc_result[0]['text']

                        # find the specified punctuations in the punc_result
                        punct_pattern = re.compile(r'[。？！]')
                        matches = list(punct_pattern.finditer(punc_result_text))

                        if matches:
                            # locate the last punctuation
                            last_match = matches[-1]
                            split_pos = last_match.end()
                            current_text = punc_result_text[:split_pos]
                            remaining_text = punc_result_text[split_pos:]

                            # remove punctuations from the remaining text
                            remaining_text2 = re.sub(r'[。？！，；：“”‘’（）【】{}、,;:"\'()\[\]{}]', '', remaining_text)

                            logger.info(f"split_pos={split_pos}, current_text={current_text}, remaining_text={remaining_text}, remaining_text2={remaining_text2}")

                            # # there could be multiple punctuations in the last chunk
                            # # we need to split the text into multiple chunks
                            # # split the text into multiple chunks
                            # while split_pos < len(punc_result_text):
                            #     current_text = punc_result_text[:split_pos]
                            #     remaining_text = punc_result_text[split_pos:]
                            #     logger.info(f"split_pos={split_pos}, current_text={current_text}, remaining_text={remaining_text}")
                            #     # update the text cache
                            #     self.streamParam._text_cache = remaining_text

                            # update the text cache
                            self.streamParam._text_cache = remaining_text2

                            if websocket is not None:
                                if len(current_text) > 1:
                                    result1 = OddAsrStreamResult(self.punc_model, websocket, current_text, is_final=True, index=self.streamParam._stats.index, begin_time=self.streamParam._stats.start_time)
                                    logger.info(f"result1={result1}")

                                    enque_asr_result(result1)
                                if not remaining_text2 == "":
                                    result2 = OddAsrStreamResult(self.punc_model, websocket, remaining_text2, is_final=False, index=self.streamParam._stats.index, begin_time=self.streamParam._stats.start_time)
                                    logger.info(f"result2={result2}")

                                    enque_asr_result(result2)

                        else:
                            # 没有找到标点符号，添加到缓存并继续
                            # self.streamParam._text_cache = punc_result_text
                            result = OddAsrStreamResult(self.punc_model, websocket, self.streamParam._text_cache, is_final=False, index=self.streamParam._stats.index, begin_time=self.streamParam._stats.start_time)
                            enque_asr_result(result)

                    except Exception as e:
                        logger.error(f"Error in punctuation process: {e}")
                        continue

                # feed the remaining data to the model
                remaining_start = total_chunk_num * chunk_stride
                if remaining_start < len(speech):
                    audio_chunk = speech[remaining_start:]
                    # audio_chunk = speech[total_chunk_num * chunk_stride:remaining_start]
                    # is_final = True
                    logger.info(f"Processing remaining data, start={remaining_start}, end={len(speech)}, audio_chunk shape: {audio_chunk.shape}, is_final={is_final}")
                    try:
                        text = self.stream_model.generate(input=audio_chunk, 
                                                            input_len=len(audio_chunk), 
                                                            cache=cache, 
                                                            is_final=is_final, 
                                                            # return_raw_text=True,
                                                            sentence_timestamp=True,
                                                            use_punc=True,
                                                            punc_threshold=0.5,
                                                            hotword=hotwords, 
                                                            chunk_size=self.streamParam._chunk_size, 
                                                            encoder_chunk_look_back=self.streamParam._encoder_chunk_look_back, 
                                                            decoder_chunk_look_back=self.streamParam._decoder_chunk_look_back
                                                            )

                        self.streamParam._stats.total_audio_input_len += len(audio_chunk)
                        self.streamParam._stats.start_time = self.streamParam._stats.total_audio_input_len*1000/256000
                        logger.info(f"res={text}, websocket={websocket}, total input={self.streamParam._stats.total_audio_input_len}, start_time={self.streamParam._stats.start_time}")
                        if websocket is not None:
                            result = OddAsrStreamResult(self.punc_model, websocket, text, index=self.streamParam._stats.index, begin_time=self.streamParam._stats.start_time, is_final=is_final)

                            enque_asr_result(result)

                    except Exception as e:
                        logger.error(f"Error processing remaining audio chunk: {e}")

                time.sleep(0.1)

            logger.info(f"Transcription thread stopped.")

            if websocket is not None:
                result = OddAsrStreamResult(self.punc_model, websocket, "END", is_final=True, is_last=True)
                enque_asr_result(result)

            if tasks:
                loop.run_until_complete(asyncio.gather(*tasks))

        except Exception as e:
            logger.error(f"Error in transcription thread: {e}")
        finally:
            logger.info(f"Transcription thread stopped.")
            loop.close()