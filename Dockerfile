# Base image with PyTorch, CUDA 12.4, and cuDNN 9
# FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime
FROM python:3.12-slim

# Set working directory
WORKDIR /app
RUN chmod 1777 /tmp && apt-get update && apt-get install -y \
    curl wget ca-certificates \
    tar \
    &&  update-ca-certificates && rm -rf /var/lib/apt/lists/*
# Install system dependencies (including ffmpeg and other essentials)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# install torch first
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt /app/
# install requirements
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple

# Copy only the necessary application files
COPY . /app/


# expose port
EXPOSE 12340 12341

# set start command
CMD ["python", "main_server.py"]