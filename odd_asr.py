import torch
import librosa
import torchaudio
import soundfile

import os
from funasr import AutoModel
from utils_speech import convert_pcm_to_float
from log import logger


class OddAsrParamsStream:
    def __init__(self, 
                 mode="stream", 
                 hotwords="", 
                 return_raw_text=True, 
                 is_final=True, 
                 sentence_timestamp=False, 
                 chunk_size=[0, 10, 5], 
                 encoder_chunk_look_back=4, 
                 decoder_chunk_look_back=1,
                 ):
        self.mode = mode  # mode should be a string like 'file','stream', 'pipeline'
        self.hotwords = hotwords  # hotwords should be a string like 'word1 word2'
        self.return_raw_text=return_raw_text #return raw text or not, default is True, if False, return json format result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]]}, 
        self.is_final=is_final  #is_final=True, if False, return partial result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False},
        self.sentence_timestamp=sentence_timestamp  #sentence_timestamp=False, if True, return sentence timestamp, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False, sentence_timestamp: [[0, 2000]]},

        self.chunk_size = [0, 10, 5] #[0, 10, 5] 600ms, [0, 8, 4] 480ms
        self.chunk_size = chunk_size  #chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking
        self.encoder_chunk_look_back = encoder_chunk_look_back #number of chunks to lookback for encoder self-attention
        self.decoder_chunk_look_back = decoder_chunk_look_back #number of encoder chunks to lookback for decoder cross-attention

        # check chunk_size is valid, chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking, chunk_size[1] is the chunk size, in ms, chunk_size[2] is the overlap size, in ms
        if len(self.chunk_size) != 3:
            raise ValueError("chunk_size should be a list of 3 elements, chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking, chunk_size[1] is the chunk size, in ms, chunk_size[2] is the overlap size, in ms")
        if self.chunk_size[0] < -1 or self.chunk_size[0] > 60000:
            raise ValueError("chunk_size[0] should be between -1 and 60000, in ms")
        if self.chunk_size[1] < 0 or self.chunk_size[1] > 60000:
            raise ValueError("chunk_size[1] should be between 0 and 60000, in ms")
        if self.chunk_size[2] < 0 or self.chunk_size[2] > 60000:
            raise ValueError("chunk_size[2] should be between 0 and 60000, in ms")


class OddAsrParamsFile:
    def __init__(self, mode="file", hotwords="", return_raw_text=True, is_final=True, sentence_timestamp=False):
        self.mode = mode  # mode should be a string like 'file','stream', 'pipeline'
        self.hotwords = hotwords  # hotwords should be a string like 'word1 word2'
        self.return_raw_text=return_raw_text #return raw text or not, default is True, if False, return json format result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]]}, 
        self.is_final=is_final  #is_final=True, if False, return partial result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False},
        self.sentence_timestamp=sentence_timestamp  #sentence_timestamp=False, if True, return sentence timestamp, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False, sentence_timestamp: [[0, 2000]]},


class OddAsr:
    def __init__(self, OddAsrParamsStream:OddAsrParamsStream=None, OddAsrParamsFile:OddAsrParamsFile=None):

        self.OddAsrParamsStream = OddAsrParamsStream
        self.OddAsrParamsFile = OddAsrParamsFile
        # auto detect GPU device
        device = "cuda:0" if torch.cuda.is_available() else "cpu"

        # load file model
        self.model = AutoModel(
            model="iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            vad_model='iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', vad_model_revision="v2.0.4",
            punc_model='iic/punc_ct-transformer_cn-en-common-vocab471067-large', punc_model_revision="v2.0.4",
            spk_model="cam++",
            # spk_model="iic/speech_campplus_sv_zh-cn_3dspeaker_16k",
            log_level="error",
            hub="ms",  # hub：表示模型仓库，ms为选择modelscope下载，hf为选择huggingface下载。
            device=device,
            disable_update=True
        )
        logger.info("Model loaded successfully.")

        # load stream model
        self.stream_model = AutoModel(
            model="paraformer-zh-streaming", model_revision="v2.0.4",
            vad_model='iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', vad_model_revision="v2.0.4",
            punc_model='iic/punc_ct-transformer_cn-en-common-vocab471067-large', punc_model_revision="v2.0.4",
            spk_model="cam++",
            log_level="error",
            hub="ms",  # hub：表示模型仓库，ms为选择modelscope下载，hf为选择huggingface下载。
            device=device,
            disable_update=True,
        )

    def __convert_time_to_srt_format(self, time_in_milliseconds):
        hours = time_in_milliseconds // 3600000
        time_in_milliseconds %= 3600000
        minutes = time_in_milliseconds // 60000
        time_in_milliseconds %= 60000
        seconds = time_in_milliseconds // 1000
        time_in_milliseconds %= 1000

        return f"{hours:02}:{minutes:02}:{seconds:02},{time_in_milliseconds:03}"

    def __text_to_srt(self, idx, speaker_id, msg, start_microseconds, end_microseconds) -> str:
        start_time = self.__convert_time_to_srt_format(start_microseconds)
        end_time = self.__convert_time_to_srt_format(end_microseconds)

        msg = f"发言人 {speaker_id}: {msg}"
        srt = """%d
%s --> %s
%s
            """ % (
            idx,
            start_time,
            end_time,
            msg,
        )
        return srt

    def transcribe_file(self, audio_file, hotwords, output_format="txt"):
        try:
            # check audio file exists
            if not os.path.exists(audio_file):
                logger.error(f"Audio file not found: {audio_file}")
                raise FileNotFoundError(f"Audio file not found: {audio_file}")

            # load audio file
            logger.info(f"Loading audio file: {audio_file}")
            data, sr = librosa.load(audio_file, sr=None, mono=True)
            logger.info(f"Audio loaded successfully. Sample rate: {sr}")
            data = convert_pcm_to_float(data)

            # resample audio to 16kHz if necessary
            if sr != 16000:
                logger.info(f"Resampling audio from {sr} to 16000 Hz")
                data = torch.tensor(data, dtype=torch.float32).unsqueeze(0) # Add batch dimension
                resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
                data = resampler(data).squeeze(0).numpy()  # Resample and convert to numpy array
                logger.info(f"Audio resampled to 16000 Hz. Shape: {data.shape}")

            logger.info(f"Starting speech recognition with expected output_format={output_format}, hotwords: {hotwords}")

            # start speech recognition with hotwords
            result = self.model.generate(
                data, 
                return_raw_text=True, 
                is_final=True, 
                sentence_timestamp=False,
                hotword=hotwords  # Pass the hotwords as a string to the model
            )

            match output_format:
                case "srt":
                    sentences = result[0]["sentence_info"]
                    subtitles = []

                    for idx, sentence in enumerate(sentences):
                        sub = self.__text_to_srt(idx, sentence['spk'], sentence['text'], sentence['start'], sentence['end'])
                        subtitles.append(sub)

                    return "\n".join(subtitles)
                case "spk":
                    sentences = result[0]["sentence_info"]
                    subtitles = []

                    for idx, sentence in enumerate(sentences):
                        sub = f"发言人 {sentence['spk']}: {sentence['text']}"
                        subtitles.append(sub)

                    return "\n".join(subtitles)
                case "txt":
                    return result[0]["text"]
                case _:
                    return result[0]["text"]

        except Exception as e:
            raise RuntimeError(f"Error processing audio file: {e}")


    def transcribe_stream(self, audio_file, hotwords, output_format="txt"):
        try:
            # check audio file exists
            if not os.path.exists(audio_file):
                logger.error(f"Audio file not found: {audio_file}")
                raise FileNotFoundError(f"Audio file not found: {audio_file}")

            # load audio file
            logger.info(f"Loading audio file: {audio_file}")
            data, sr = librosa.load(audio_file, sr=None, mono=True)
            logger.info(f"Audio loaded successfully. Sample rate: {sr}")
            data = convert_pcm_to_float(data)

            # resample audio to 16kHz if necessary
            if sr!= 16000:
                logger.info(f"Resampling audio from {sr} to 16000 Hz")
                data = torch.tensor(data, dtype=torch.float32).unsqueeze(0) # Add batch dimension
                resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
                data = resampler(data).squeeze(0).numpy()  # Resample and convert to numpy array
                logger.info(f"Audio resampled to 16000 Hz. Shape: {data.shape}")

            logger.info(f"Starting speech recognition with hotwords: {hotwords}")

            # start speech recognition with hotwords
            chunk_stride = self.OddAsrParamsStream.chunk_size[1] * 960 # 600ms

            cache = {}
            total_chunk_num = int((len(data) - 1) / chunk_stride + 1)
            result = ""
            for i in range(total_chunk_num):
                speech_chunk = data[i*chunk_stride:(i+1)*chunk_stride]
                is_final = i == total_chunk_num - 1
                res = self.stream_model.generate(
                    input=speech_chunk, 
                    cache=cache, 
                    is_final=is_final, 
                    chunk_size=self.OddAsrParamsStream.chunk_size, 
                    encoder_chunk_look_back=self.OddAsrParamsStream.encoder_chunk_look_back, 
                    decoder_chunk_look_back=self.OddAsrParamsStream.decoder_chunk_look_back)
                
                print(res)

                result += res[0]["text"]

            return result

        except Exception as e:
            raise RuntimeError(f"Error processing audio file: {e}")
