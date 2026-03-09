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

mkdir -p /workspace/models/custom_voices/gptsovits
mkdir -p /workspace/models/custom_voices/rvc
mkdir -p /var/log/supervisor

if [ ! -f "/workspace/gateway/api_keys.yaml" ]; then
    echo "Initializing API keys..."
    mkdir -p /workspace/gateway
    
    # Use Python for cross-platform hash generation instead of sha256sum
    KEY_HASH=$(python3 -c "import hashlib; print(hashlib.sha256('$API_KEY'.encode()).hexdigest()[:16])")
    CREATED_AT=$(python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'))")
    
    cat > /workspace/gateway/api_keys.yaml << EOF
api_keys:
  ${KEY_HASH}:
    key_hash: "${KEY_HASH}"
    created_at: "${CREATED_AT}"
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
    version: "v2"
    gpt_weights: ""
    sovits_weights: ""
    refer_wav_path: "/workspace/models/custom_voices/gptsovits/default/reference.wav"
    prompt_text: "参考音频对应的文本内容"
    prompt_lang: "zh"
    language: "auto"
    top_k: 20
    top_p: 0.6
    temperature: 0.6
    speed: 1.0
    text_split_method: "cut5"
    batch_size: 1
    sample_steps: 32
EOF
fi

if [ ! -d "/workspace/models/custom_voices/gptsovits/default" ]; then
    mkdir -p /workspace/models/custom_voices/gptsovits/default
    echo "Please upload reference.wav to /workspace/models/custom_voices/gptsovits/default/"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Starting all services with Supervisor..."
echo ""

exec supervisord -c /workspace/supervisord.conf
