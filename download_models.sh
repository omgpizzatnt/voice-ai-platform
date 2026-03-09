#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_DIR="$SCRIPT_DIR/models/rvc_assets"

mkdir -p "$MODELS_DIR/hubert" "$MODELS_DIR/rmvpe"

echo "Downloading RVC pre-trained models..."
echo "====================================="
echo ""

if [ ! -f "$MODELS_DIR/hubert/hubert_base.pt" ]; then
    wget -O "$MODELS_DIR/hubert/hubert_base.pt" \
        https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt
    echo "✓ hubert_base.pt downloaded"
else
    echo "✓ hubert_base.pt already exists"
fi

echo ""
if [ ! -f "$MODELS_DIR/rmvpe/rmvpe.pt" ]; then
    wget -O "$MODELS_DIR/rmvpe/rmvpe.pt" \
        https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt
    echo "✓ rmvpe.pt downloaded"
else
    echo "✓ rmvpe.pt already exists"
fi

echo ""
if [ ! -f "$MODELS_DIR/rmvpe/rmvpe.onnx" ]; then
    wget -O "$MODELS_DIR/rmvpe/rmvpe.onnx" \
        https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.onnx
    echo "✓ rmvpe.onnx downloaded"
else
    echo "✓ rmvpe.onnx already exists"
fi

echo ""
echo "====================================="
echo "All models downloaded successfully!"
echo ""
echo "You can now build the Docker image:"
echo "  docker build -t voice-ai-platform ."
