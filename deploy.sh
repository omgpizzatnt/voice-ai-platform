#!/bin/bash

set -e

echo "Voice AI Platform - RunPod Deployment Script"
echo "=============================================="

if [ -z "$API_KEY" ]; then
    echo "Warning: API_KEY not set, using default"
    export API_KEY="sk-change-me-in-production"
fi

if [ -z "$WEBUI_USER" ]; then
    export WEBUI_USER="admin"
fi

if [ -z "$WEBUI_PASS" ]; then
    export WEBUI_PASS="admin"
fi

mkdir -p /workspace/models/custom_voices
mkdir -p /workspace/models/rvc_pipelines
mkdir -p /workspace/GPT-SoVITS
mkdir -p /workspace/RVC
mkdir -p /var/log/supervisor

if [ ! -f "/workspace/GPT-SoVITS/api.py" ]; then
    echo "Installing GPT-SoVITS..."
    cd /workspace
    
    git clone https://github.com/RVC-Boss/GPT-SoVITS.git GPT-SoVITS-temp
    
    cp -r GPT-SoVITS-temp/* GPT-SoVITS/
    rm -rf GPT-SoVITS-temp
    
    cd GPT-SoVITS
    
    pip install -r requirements.txt -q
    
    echo "GPT-SoVITS installed"
fi

if [ ! -f "/workspace/RVC/api.py" ]; then
    echo "Installing RVC with FastAPI wrapper..."
    cd /workspace
    
    git clone https://github.com/SocAIty/Retrieval-based-Voice-Conversion-FastAPI.git RVC-temp
    
    cp -r RVC-temp/* RVC/
    rm -rf RVC-temp
    
    cd RVC
    
    pip install -r requirements.txt -q
    pip install fastapi uvicorn python-multipart -q
    
    echo "RVC with FastAPI installed"
fi

if [ ! -f "/workspace/gateway/api_keys.yaml" ]; then
    echo "Initializing API keys..."
    mkdir -p /workspace/gateway
    cat > /workspace/gateway/api_keys.yaml << EOF
api_keys:
  $(echo -n "$API_KEY" | sha256sum | cut -c1-16):
    key_hash: "$(echo -n "$API_KEY" | sha256sum | cut -c1-16)"
    created_at: "$(date -Iseconds)"
    last_used: null
    active: true
EOF
fi

if [ ! -f "/workspace/gateway/voices.yaml" ]; then
    echo "Initializing voices config..."
    cat > /workspace/gateway/voices.yaml << 'EOF'
voices:
  default:
    name: "Default Voice"
    type: tts
    model_name: "default"
    refer_wav_path: "/workspace/models/custom_voices/default/reference.wav"
    prompt_text: "参考音频对应的文本内容"
    prompt_lang: "zh"
    text_lang: "auto"
    top_k: 20
    top_p: 0.6
    temperature: 0.6
    speed: 1.0
EOF
fi

if [ ! -d "/workspace/models/custom_voices/default" ]; then
    mkdir -p /workspace/models/custom_voices/default
    echo "Please upload reference.wav to /workspace/models/custom_voices/default/"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Starting all services with Supervisor..."
echo ""

exec supervisord -c /workspace/supervisord.conf
