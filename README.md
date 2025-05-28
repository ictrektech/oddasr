Here’s a draft for the `README.md` file based on your project:

---

# OddASR: A Simple ASR API Service for FunASR

![GitHub](URL_ADDRESS![GitHub](https://img.shields.io/github/license/oddmeta/OddASR)

A simplest ASR API service for FunASR, supporting audio file transcription.

## Introduction

**[FunASR](URL_ADDRESS**[FunASR](https://github.com/modelscope/FunASR)** is a powerful open-source speech recognition (ASR) library developed by ModelScope.
It provides a wide range of pre-trained models and tools for various speech recognition tasks.
This repository aims to simplify the deployment of FunASR for non-realtime audio processing which is my another project (小落同学) needed.

## Why OddASR?

- **Simplified Deployment**: Easy-to-use REST API for ASR transcription.
- **Local Reference**: A standalone Python implementation for local ASR transcription.
- **Docker Support**: Dockerfiles for both GPU and CPU deployment.
- **Easy to Use**: Simple API requests for audio file transcription.

## Installation
1. Clone the repository:
   ```bash
   git clone URL_ADDRESS   git clone https://github.com/oddmeta/OddASR.git
   cd OddASR
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
## Usage

### 1. Run the REST API Server
   ```bash
   python odd_asr_server.py
   ```

### 2. Test the API
   ```bash
   python testAPI.py
   ```

### 3. Local Transcription Example
   ```bash
   python testLocal.py
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

### 5. Example API Request
   ```bash
   curl -X POST -F "audio=@path/to/audio.wav" URL_ADDRESS
   curl -X POST -F "audio=@path/to/audio.wav" http://127.0.0.1:12340/v1/v1/asr
   ```

---

## Repository Contents

### Core Files:
- **`main_server.py`**: Implements the REST API server for ASR transcription.
- **`main_local.py`**: A standalone Python implementation for local ASR transcription.
- **`odd_asr_app.py`**: Main application file for running the REST API server.
- **`odd_asr_exception.py`**: Custom exception classes for the project.
- **`odd_asr_result.py`**: Result classes for the project.
- **`odd_asr.py`**: Main class for the project.
- **`utils_speech.py`**: Utility functions used by the REST API which was origined from FunASR repo.
- **`log.py`**: Logging configuration for the project.
- **`router/asr_api.py`**: Defines the API endpoints for the REST API.

### Testing and Examples:
- **`testAPI.py`**: Example client script to test the REST API functionality.
- **`testLocal.py`**: Example of using `SoundToTextLocal` for local transcription.

### Audio Files:
- **`test_cn_male9s.wav`**: Example audio file for testing.
- **`test_en_steve_jobs_10s.wav`**: Example audio file for testing.

### Deployment Files:
- **`Dockerfile`**: Dockerfile for building GPU-accelerated Docker images (NVIDIA GPU deployment).
- **`Dockerfile_CPU`**: Dockerfile for building Docker images for simple CPU-based deployments.

### Additional Files:
- **`requirements.txt`**: Python dependencies required for the project.

---

## Features

1. **REST API for ASR**:
   - Provides a REST API endpoint for audio file transcription.
   - Built using Flask.
   - Example usage: `testAPI.py`.

2. **Local Python Reference**:
   - `SoundToTextLocal.py` demonstrates a standalone ASR transcription method without the need for REST APIs.
   - Example usage: `test.py`.

3. **Docker Support**:
   - Includes Dockerfiles for both GPU and CPU deployment.
   - Simplifies deployment on servers with or without GPU support.

---

## Usage

### 1. Install Dependencies

Install the necessary Python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run REST API Server

To start the REST API server:
```bash
python odd_asr_server.py
```

The server will start on `http://127.0.0.1:12340`.

### 3. Test the REST API

Use the `testAPI.py` script to test the API:
```bash
python testAPI.py
```

Example `curl` command:
```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:12340/v1/asr
```

### 4. Local Transcription Example

Run the local transcription example:
```bash
python test.py
```

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

## Example API Request

Send an audio file to the REST API:
```bash
curl -X POST -F "audio=@path/to/audio.wav" http://127.0.0.1:12340/v1/asr
```

there are two test audio files in the repo:
- `test_cn_male9s.wav`
- `test_en_steve_jobs_10s.wav`

you can test them by:
```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:12340/v1/asr
curl -X POST -F "audio=@test_en_steve_jobs_10s.wav" http://127.0.0.1:12340/v1/asr
```


---

## TODO
- [ ] Add more models and features.
- [ ] Support realtime ASR.
- [ ] Add more customized options.
   - [ ] --mode offline表示离线文件转写 
   - [ ] --audio_in 需要进行转写的音频文件，支持文件路径，文件列表wav.scp 
   - [ ] --thread_num 设置并发发送线程数，默认为1 
   - [ ] --ssl 设置是否开启ssl证书校验，默认1开启，设置为0关闭 
   - [ ] --hotword 热词文件，每行一个热词，格式(热词 权重)：阿里巴巴 20 
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
