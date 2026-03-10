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

# ============================================
# Setup persistent data directory structure in /workspace
# ============================================
echo "Setting up persistent data directories..."

# Create persistent data directories (these will survive pod restarts)
mkdir -p /workspace/data/models/custom_voices/gptsovits
mkdir -p /workspace/data/models/custom_voices/rvc
mkdir -p /workspace/data/configs
mkdir -p /var/log/supervisor

# ============================================
# Create symbolic links from /app to persistent data
# ============================================
echo "Creating symbolic links..."

# Link models directory
if [ -e "/app/models/custom_voices" ] && [ ! -L "/app/models/custom_voices" ]; then
    rm -rf /app/models/custom_voices
fi
if [ ! -L "/app/models/custom_voices" ]; then
    ln -s /workspace/data/models/custom_voices /app/models/custom_voices
fi

# Link config files
if [ -f "/app/gateway/voices.yaml" ] && [ ! -L "/app/gateway/voices.yaml" ]; then
    rm -f /app/gateway/voices.yaml
fi
if [ ! -L "/app/gateway/voices.yaml" ]; then
    ln -s /workspace/data/configs/voices.yaml /app/gateway/voices.yaml
fi

if [ -f "/app/gateway/api_keys.yaml" ] && [ ! -L "/app/gateway/api_keys.yaml" ]; then
    rm -f /app/gateway/api_keys.yaml
fi
if [ ! -L "/app/gateway/api_keys.yaml" ]; then
    ln -s /workspace/data/configs/api_keys.yaml /app/gateway/api_keys.yaml
fi

echo "Symbolic links created successfully."

# ============================================
# Initialize configuration files if they don't exist
# ============================================

if [ ! -f "/workspace/data/configs/api_keys.yaml" ]; then
    echo "Initializing API keys..."
    
    # Use Python for cross-platform hash generation instead of sha256sum
    KEY_HASH=$(python3 -c "import hashlib; print(hashlib.sha256('$API_KEY'.encode()).hexdigest()[:16])")
    CREATED_AT=$(python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'))")
    
    cat > /workspace/data/configs/api_keys.yaml << EOF
api_keys:
  ${KEY_HASH}:
    key_hash: "${KEY_HASH}"
    created_at: "${CREATED_AT}"
    last_used: null
    active: true
EOF
fi

if [ ! -f "/workspace/data/configs/voices.yaml" ]; then
    echo "Initializing voices config..."
    cat > /workspace/data/configs/voices.yaml << 'EOF'
voices:
  default:
    name: "Default Voice"
    type: tts
    version: "v2"
    gpt_weights: ""
    sovits_weights: ""
    refer_wav_path: "/workspace/data/models/custom_voices/gptsovits/default/reference.wav"
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

if [ ! -d "/workspace/data/models/custom_voices/gptsovits/default" ]; then
    mkdir -p /workspace/data/models/custom_voices/gptsovits/default
    echo "Please upload reference.wav to /workspace/data/models/custom_voices/gptsovits/default/"
fi

echo ""
echo "Setup complete!"
echo "Persistent data location: /workspace/data/"
echo ""
echo "Starting all services with Supervisor..."
echo ""

exec supervisord -c /app/supervisord.conf
