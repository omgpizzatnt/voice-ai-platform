FROM runpod/pytorch:1.0.3-cu1281-torch290-ubuntu2404

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    wget \
    libsox-dev \
    ffmpeg \
    build-essential \
    supervisor \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /workspace/venvs \
    /workspace/models/custom_voices \
    /workspace/models/rvc_pipelines \
    /var/log/supervisor

COPY gateway/ /workspace/gateway/
COPY webui/ /workspace/webui/
COPY supervisord.conf /workspace/
COPY deploy.sh /workspace/
RUN chmod +x /workspace/deploy.sh

COPY GPT-SoVITS/ /workspace/GPT-SoVITS/
COPY RVC/ /workspace/RVC/

RUN mkdir -p /workspace/GPT-SoVITS/GPT_SoVITS/pretrained_models \
    /workspace/GPT-SoVITS/GPT_SoVITS/text/G2PWModel \
    /workspace/RVC/assets/hubert \
    /workspace/RVC/assets/rmvpe

COPY models/gptsovits_assets/pretrained_models/ /workspace/GPT-SoVITS/GPT_SoVITS/pretrained_models/
COPY models/gptsovits_assets/G2PWModel/ /workspace/GPT-SoVITS/GPT_SoVITS/text/G2PWModel/
COPY models/rvc_assets/ /workspace/RVC/assets/

RUN python -m venv /workspace/venvs/gpt-sovits --system-site-packages && \
    /workspace/venvs/gpt-sovits/bin/pip install --no-cache-dir -r /workspace/GPT-SoVITS/requirements.txt

RUN python3.9 -m venv /workspace/venvs/rvc && \
    /workspace/venvs/rvc/bin/python -m pip install pip==24.0 && \
    /workspace/venvs/rvc/bin/pip install --no-cache-dir -r /workspace/RVC/requirements.txt

RUN python -m venv /workspace/venvs/gateway --system-site-packages && \
    /workspace/venvs/gateway/bin/pip install --no-cache-dir -r /workspace/gateway/requirements.txt

RUN python -m venv /workspace/venvs/webui --system-site-packages && \
    /workspace/venvs/webui/bin/pip install --no-cache-dir -r /workspace/webui/requirements.txt

ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:512

EXPOSE 80 8080

CMD ["/workspace/deploy.sh"]
