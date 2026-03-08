FROM runpod/pytorch:1.0.3-cu1281-torch290-ubuntu2404

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    wget \
    libsox-dev \
    ffmpeg \
    build-essential \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /workspace/gateway /workspace/webui \
    /workspace/models/custom_voices \
    /workspace/models/rvc_pipelines \
    /workspace/GPT-SoVITS \
    /workspace/RVC \
    /var/log/supervisor

COPY gateway/requirements.txt /workspace/gateway/
RUN pip install --no-cache-dir -r /workspace/gateway/requirements.txt

COPY webui/requirements.txt /workspace/webui/
RUN pip install --no-cache-dir -r /workspace/webui/requirements.txt

COPY gateway/ /workspace/gateway/
COPY webui/ /workspace/webui/
COPY supervisord.conf /workspace/
COPY deploy.sh /workspace/
RUN chmod +x /workspace/deploy.sh

ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:512

EXPOSE 80 8080
# EXPOSE 9881 9882 9883 9884 7866 7867

CMD ["/workspace/deploy.sh"]
