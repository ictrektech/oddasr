[TOC]

Here’s a draft for the `README.md` file based on your project:

---

# OddASR: A Simple ASR API Server for FunASR

![GitHub](https://img.shields.io/github/license/oddmeta/oddasr)

A simplest ASR API server for FunASR based on Flask, supporting both audio file mode and streaming mode transcriptions.

## Introduction

**[FunASR](https://github.com/modelscope/FunASR)** is a powerful open-source speech recognition (ASR) library developed by ModelScope.
It provides a wide range of pre-trained models and tools for various speech recognition tasks.
This repository aims to simplify the deployment of FunASR for non-realtime audio processing which is my another project ([小落同学](https://x.oddmeta.com)) needed.

## Why OddASR?

- **Simplified Deployment**: Easy-to-use REST API for ASR transcription.
- **Local Reference**: A standalone Python implementation for local ASR transcription.
- **Docker Support**: Dockerfiles for both GPU and CPU deployment.
- **Easy to Use**: Simple API requests for audio file transcription.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/oddmeta/oddasr.git
   cd oddasr
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Run the REST API Server

To start the REST API server:

```bash
python main_server.py
```

The server will start on `http://127.0.0.1:12340`.

### 2. Test file ASR API

Use the `testAPI.py` script to test the API:
```bash
python testAPI.py test_en_steve_jobs_10s.wav txt
```

Example `curl` command:
Send an audio file to the REST API:

```bash
curl -X POST -F "audio=@path/to/audio.wav" http://127.0.0.1:12340/v1/v1/asr
```
Example `curl` command for testing the `test_cn_male_9s.wav` audio file:
```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:12340/v1/asr
```

there are two test audio files in the repo:
- `test_cn_male9s.wav`
- `test_en_steve_jobs_10s.wav`

you can test them by:
```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:12340/v1/asr
curl -X POST -F "audio=@test_en_steve_jobs_10s.wav" http://127.0.0.1:12340/v1/asr
```

### 3. Test stream ASR API
Use the `testStreamAPI.py` script to test the API:

```bash
python testStreamAPI.py 111.pcm
```

### 4. Example output
- text mode
```bash
是开始这个呃实时的一个转写。 
对， 然后是转写的一个效果， 大概大概就是这个样子。 
然后的话那个在这里边你也可以去给他那个加一个人。 
比如说是嗯我随便给他取一个名字， 
就是连云端的还是自己算的连云端的吧。 
```

- spk mode
```bash
发言人 0: 是开始这个呃实时的一个转写。
发言人 0: 对，
发言人 0: 然后是转写的一个效果，
发言人 0: 大概大概就是这个样子。
发言人 0: 然后的话那个在这里边你也可以去给他那个加一个人。
发言人 0: 比如说是嗯我随便给他取一个名字，
发言人 1: 就是连云端的还是自己算的连云端的吧。
发言人 0: 呃本地的本地的本地的对，
发言人 0: 不用连看能调吧。
发言人 2: 这个还有对呀，
发言人 0: 然后这里边可以给他加格。
```

- srt mode
```bash
0 00:00:01,010 --> 00:00:04,865 发言人 0: 是开始这个呃实时的一个转写。 
1 00:00:06,040 --> 00:00:06,280 发言人 0: 对， 
2 00:00:06,640 --> 00:00:08,660 发言人 0: 然后是转写的一个效果， 
3 00:00:08,680 --> 00:00:10,280 发言人 0: 大概大概就是这个样子。 
4 00:00:10,280 --> 00:00:14,500 发言人 0: 然后的话那个在这里边你也可以去给他那个加一个人。 
5 00:00:14,660 --> 00:00:19,665 发言人 0: 比如说是嗯我随便给他取一个名字， 
6 00:00:20,440 --> 00:00:23,200 发言人 1: 就是连云端的还是自己算的连云端的吧。 
7 00:00:23,240 --> 00:00:25,340 发言人 0: 呃本地的本地的本地的对， 
8 00:00:25,340 --> 00:00:27,275 发言人 0: 不用连看能调吧。 
9 00:00:29,120 --> 00:00:31,480 发言人 2: 这个还有对呀， 
10 00:00:32,130 --> 00:00:33,885 发言人 0: 然后这里边可以给他加格。 
```

### 4. Docker Deployment
   - GPU Deployment:
     ```bash
     docker build -t asr-service-gpu:v0.1.0.
     docker run --gpus all -d -p 12340:12340 --name asr-service asr-service-gpu:v0.1.0
     ```
   - CPU Deployment:
     ```bash
     docker build -f Dockerfile_CPU -t asr-service-cpu:v0.1.0.
     docker run -d -p 12340:12340 --name asr-service asr-service-cpu:v0.1.0
     ```

---

## Repository Contents

### Core Files
- **`main_server.py`**: Implements the REST API server for ASR transcription.
- **`main_local.py`**: A standalone Python implementation for local ASR transcription.
- **`odd_asr_app.py`**: Main application file for running the REST API server.
- **`odd_asr_config.py`**: Custom configurations for the project.
- **`odd_asr_exception.py`**: Custom exception classes for the project.
- **`odd_asr_result.py`**: Result classes for the project.
- **`odd_asr.py`**: File ASR class for the project.
- **`odd_asr_stream.py`**: Stream ASR class for the project.
- **`odd_wss_server.py`**: Websocket server class for streaming ASR.
- **`utils_speech.py`**: Utility functions used by the REST API which was origined from FunASR repo.
- **`log.py`**: Logging configuration for the project.
- **`router/asr_api.py`**: Defines the API endpoints for the REST API.

### Testing and Examples
- **`testAPI.py`**: Example client script to test the file mode of ASR API.
- **`testStreamAPI.py`**: Example client script to test the streaming mode of ASR API.

### Audio Files
- **`test_cn_male9s.wav`**: Example audio file for testing.
- **`test_en_steve_jobs_10s.wav`**: Example audio file for testing.

### Deployment Files
- **`Dockerfile`**: Dockerfile for building GPU-accelerated Docker images (NVIDIA GPU deployment).
- **`Dockerfile_CPU`**: Dockerfile for building Docker images for simple CPU-based deployments.

### Additional Files
- **`requirements.txt`**: Python dependencies required for the project.

---

## Features

1. **REST API for ASR**:
   - `main_server.py`Provides a REST API endpoint for audio file transcription.
   - Built using Flask.
   - Example usage: `python main_server.py`.

2. **Docker Support**:
   - Includes Dockerfiles for both GPU and CPU deployment.
   - Simplifies deployment on servers with or without GPU support.

---

## Docker Deployment

### GPU Deployment

Build and run the Docker image for NVIDIA GPU:
```bash
docker build -t oddasr-service-gpu:v0.1.0 .
docker run --gpus all -d -p 12340:12340 --name oddasr-service oddasr-service-gpu:v0.1.0
```

### CPU Deployment

Build and run the Docker image for CPU:
```bash
docker build -f Dockerfile_CPU -t oddasr-service-cpu:v0.1.0 .
docker run -d -p 12340:12340 --name oddasr-service oddasr-service-cpu:v0.1.0
```

---

## TODO
- [ ] Add more models and features.
- [ ] Support realtime ASR.
- [ ] Add more customized options.
   - [ ] --mode: file表示离线文件转写, stream表示实时转写
   - [ ] --output_format: txt表示纯文本, spk表示根据VAD分段后每个段落前面加发言人，srt表示在spk基础上为每个段落加一个段落在音频文件中的时间位置
   - [ ] --hotword 热词文件，每行一个热词，格式(热词 权重)：阿里巴巴 20
- [ ] Simple UI for oddasr to demostrate.
- [ ] Support voiceprint recognition!!! [小落同学](https://x.oddmeta.net) really need this feature!!!
- [ ] Other enhancements
   - [ ] --thread_num 设置并发发送线程数，默认为1
   - [ ] --audio_in 需要进行转写的音频文件，支持服务器本地/远程文件路径，文件列表wav.scp
   - [ ] --ssl 设置是否开启ssl证书校验，默认1开启，设置为0关闭
   - [ ] --use_itn 设置是否使用itn，默认1开启，设置为0关闭

---

## Limitations

- Only supports **non-realtime** ASR transcription.
- Only supports **audio files** as input.

---

## References

- [FunASR](https://github.com/modelscope/FunASR): The ASR framework used in this project.
- [Flask](https://github.com/pallets/flask): The web framework used for the REST API, which is based on Werkzeug and Jinja.
- [funasr-python-api](https://github.com/open-yuhaoz/funasr-python-api): Python api written by funasr server post

---

## License 
This project is NOT licensed under any License.
Copy free, without any string attached! Just happy coding!
