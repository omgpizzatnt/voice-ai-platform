#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$SCRIPT_DIR/models/rvc_assets/hubert" "$SCRIPT_DIR/models/rvc_assets/rmvpe"
mkdir -p "$SCRIPT_DIR/models/gptsovits_assets/s1" "$SCRIPT_DIR/models/gptsovits_assets/s2"

echo "Downloading RVC pre-trained models..."
echo "====================================="
echo ""

if [ ! -f "$SCRIPT_DIR/models/rvc_assets/hubert/hubert_base.pt" ]; then
    wget -O "$SCRIPT_DIR/models/rvc_assets/hubert/hubert_base.pt" \
        https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt
    echo "✓ hubert_base.pt downloaded"
else
    echo "✓ hubert_base.pt already exists"
fi

echo ""
if [ ! -f "$SCRIPT_DIR/models/rvc_assets/rmvpe/rmvpe.pt" ]; then
    wget -O "$SCRIPT_DIR/models/rvc_assets/rmvpe/rmvpe.pt" \
        https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt
    echo "✓ rmvpe.pt downloaded"
else
    echo "✓ rmvpe.pt already exists"
fi

echo ""
if [ ! -f "$SCRIPT_DIR/models/rvc_assets/rmvpe/rmvpe.onnx" ]; then
    wget -O "$SCRIPT_DIR/models/rvc_assets/rmvpe/rmvpe.onnx" \
        https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.onnx
    echo "✓ rmvpe.onnx downloaded"
else
    echo "✓ rmvpe.onnx already exists"
fi

echo ""
echo "====================================="
echo "Downloading GPT-SoVITS pre-trained models..."
echo "====================================="
echo ""
echo "Note: GPT-SoVITS models are large (~2.5GB total)"
echo "This may take several minutes depending on your connection"
echo ""

if [ ! -f "$SCRIPT_DIR/models/gptsovits_assets/s1/s1bert.ckpt" ]; then
    echo "Downloading s1bert.ckpt (~2GB)..."
    wget -O "$SCRIPT_DIR/models/gptsovits_assets/s1/s1bert.ckpt" \
        https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/s1bert.ckpt
    echo "✓ s1bert.ckpt downloaded"
else
    echo "✓ s1bert.ckpt already exists"
fi

echo ""
if [ ! -f "$SCRIPT_DIR/models/gptsovits_assets/s2/s2G.pth" ]; then
    echo "Downloading s2G.pth (~400MB)..."
    wget -O "$SCRIPT_DIR/models/gptsovits_assets/s2/s2G.pth" \
        https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/s2G.pth
    echo "✓ s2G.pth downloaded"
else
    echo "✓ s2G.pth already exists"
fi

echo ""
echo "====================================="
echo "All models downloaded successfully!"
echo ""
echo "You can now build the Docker image:"
echo "  docker build -t voice-ai-platform ."
