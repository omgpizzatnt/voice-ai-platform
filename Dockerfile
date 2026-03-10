FROM runpod/pytorch:1.0.3-cu1281-torch290-ubuntu2404

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    wget \
    libsox-dev \
    ffmpeg \
    build-essential \
    supervisor \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/venvs \
    /app/models/custom_voices \
    /app/models/rvc_pipelines \
    /var/log/supervisor

COPY gateway/ /app/gateway/
COPY webui/ /app/webui/
COPY supervisord.conf /app/
COPY deploy.sh /app/
RUN chmod +x /app/deploy.sh

COPY GPT-SoVITS/ /app/GPT-SoVITS/
COPY RVC/ /app/RVC/

RUN mkdir -p /app/GPT-SoVITS/GPT_SoVITS/pretrained_models \
    /app/GPT-SoVITS/GPT_SoVITS/text/G2PWModel \
    /app/RVC/assets/hubert \
    /app/RVC/assets/rmvpe

COPY models/gptsovits_assets/pretrained_models/ /app/GPT-SoVITS/GPT_SoVITS/pretrained_models/
COPY models/gptsovits_assets/G2PWModel/ /app/GPT-SoVITS/GPT_SoVITS/text/G2PWModel/
COPY models/rvc_assets/ /app/RVC/assets/

# GPT-SoVITS venv with retry logic for network issues
# Pre-install build dependencies to avoid timeouts during pyopenjtalk build
RUN python -m venv /app/venvs/gpt-sovits --system-site-packages

# Configure pip with longer timeout, retry settings, and USTC mirror (China mirror for faster downloads)
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRY_ATTEMPTS=5

# Pre-install build dependencies that pyopenjtalk needs (to avoid timeout during build)
# Using USTC mirror (https://pypi.mirrors.ustc.edu.cn/simple) for faster downloads in China
RUN /app/venvs/gpt-sovits/bin/pip install --no-cache-dir --upgrade pip setuptools wheel -i https://pypi.mirrors.ustc.edu.cn/simple && \
    /app/venvs/gpt-sovits/bin/pip install --no-cache-dir numpy==1.26.4 cython cmake -i https://pypi.mirrors.ustc.edu.cn/simple

# Install GPT-SoVITS requirements with retry logic using USTC mirror
RUN for i in 1 2 3; do \
        /app/venvs/gpt-sovits/bin/pip install --no-cache-dir -r /app/GPT-SoVITS/requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple && break || \
        (echo "Attempt $i failed, retrying in 10 seconds..." && sleep 10); \
    done

# RVC venv - Using USTC mirror for faster downloads in China
RUN python3.9 -m venv /app/venvs/rvc && \
    /app/venvs/rvc/bin/python -m pip install pip==24.0 -i https://pypi.mirrors.ustc.edu.cn/simple && \
    /app/venvs/rvc/bin/pip install --no-cache-dir -r /app/RVC/requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple

# Gateway venv - Using USTC mirror for faster downloads in China
RUN python -m venv /app/venvs/gateway --system-site-packages && \
    /app/venvs/gateway/bin/pip install --no-cache-dir -r /app/gateway/requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple

# WebUI venv - Using USTC mirror for faster downloads in China
RUN python -m venv /app/venvs/webui --system-site-packages && \
    /app/venvs/webui/bin/pip install --no-cache-dir -r /app/webui/requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple

ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:512

EXPOSE 80 8080

CMD ["/app/deploy.sh"]
