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

RUN python -m venv /app/venvs/gpt-sovits --system-site-packages && \
    /app/venvs/gpt-sovits/bin/pip install --no-cache-dir -r /app/GPT-SoVITS/requirements.txt

RUN python3.9 -m venv /app/venvs/rvc && \
    /app/venvs/rvc/bin/python -m pip install pip==24.0 && \
    /app/venvs/rvc/bin/pip install --no-cache-dir -r /app/RVC/requirements.txt

RUN python -m venv /app/venvs/gateway --system-site-packages && \
    /app/venvs/gateway/bin/pip install --no-cache-dir -r /app/gateway/requirements.txt

RUN python -m venv /app/venvs/webui --system-site-packages && \
    /app/venvs/webui/bin/pip install --no-cache-dir -r /app/webui/requirements.txt

ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:512

EXPOSE 80 8080

CMD ["/app/deploy.sh"]
