#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "Voice AI Platform - Model Downloader"
echo "========================================"
echo ""

mkdir -p "$SCRIPT_DIR/models/rvc_assets/hubert" "$SCRIPT_DIR/models/rvc_assets/rmvpe"
mkdir -p "$SCRIPT_DIR/models/gptsovits_assets/pretrained_models"
mkdir -p "$SCRIPT_DIR/models/gptsovits_assets/G2PWModel"

echo "========================================"
echo "Downloading RVC pre-trained models..."
echo "========================================"
echo ""

if [ ! -f "$SCRIPT_DIR/models/rvc_assets/hubert/hubert_base.pt" ]; then
    echo "Downloading hubert_base.pt..."
    wget --tries=5 --timeout=60 -O "$SCRIPT_DIR/models/rvc_assets/hubert/hubert_base.pt" \
        https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt
    echo "✓ hubert_base.pt downloaded (181MB)"
else
    echo "✓ hubert_base.pt already exists"
fi

echo ""
if [ ! -f "$SCRIPT_DIR/models/rvc_assets/rmvpe/rmvpe.pt" ]; then
    echo "Downloading rmvpe.pt..."
    wget --tries=5 --timeout=60 -O "$SCRIPT_DIR/models/rvc_assets/rmvpe/rmvpe.pt" \
        https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt
    echo "✓ rmvpe.pt downloaded (173MB)"
else
    echo "✓ rmvpe.pt already exists"
fi

echo ""
echo "Note: rmvpe.onnx is optional (for AMD/Intel GPU users)"
read -p "Download rmvpe.onnx? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ ! -f "$SCRIPT_DIR/models/rvc_assets/rmvpe/rmvpe.onnx" ]; then
        echo "Downloading rmvpe.onnx..."
        wget --tries=5 --timeout=60 -O "$SCRIPT_DIR/models/rvc_assets/rmvpe/rmvpe.onnx" \
            https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.onnx
        echo "✓ rmvpe.onnx downloaded (345MB)"
    else
        echo "✓ rmvpe.onnx already exists"
    fi
else
    echo "Skipping rmvpe.onnx (optional for AMD/Intel GPU)"
fi

echo ""
echo "========================================"
echo "Downloading GPT-SoVITS pre-trained models..."
echo "========================================"
echo ""

if [ ! -f "$SCRIPT_DIR/models/gptsovits_assets/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt" ]; then
    echo "Downloading pretrained_models.zip (~4.5GB with all models)..."
    wget --tries=3 --timeout=120 --show-progress -O "$SCRIPT_DIR/models/pretrained_models.zip" \
        https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/pretrained_models.zip
    echo "✓ pretrained_models.zip downloaded"

    echo ""
    echo "Extracting pretrained_models..."
    unzip -q -o "$SCRIPT_DIR/models/pretrained_models.zip" -d "$SCRIPT_DIR/models/gptsovits_assets/"
    rm "$SCRIPT_DIR/models/pretrained_models.zip"

    echo "✓ pretrained_models extracted to models/gptsovits_assets/pretrained_models/"
else
    echo "✓ GPT-SoVITS pretrained models already exist"
fi

echo ""
echo "========================================"
echo "Downloading G2PWModel (for Chinese TTS)..."
echo "========================================"
echo ""

if [ ! -f "$SCRIPT_DIR/models/gptsovits_assets/G2PWModel/g2pW.onnx" ]; then
    echo "Downloading G2PWModel.zip (~562MB)..."
    wget --tries=3 --timeout=60 --show-progress -O "$SCRIPT_DIR/models/G2PWModel.zip" \
        https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/G2PWModel.zip
    echo "✓ G2PWModel.zip downloaded"

    echo "Extracting G2PWModel..."
    unzip -q -o "$SCRIPT_DIR/models/G2PWModel.zip" -d "$SCRIPT_DIR/models/gptsovits_assets/"
    rm "$SCRIPT_DIR/models/G2PWModel.zip"

    echo "✓ G2PWModel extracted to models/gptsovits_assets/G2PWModel/"
else
    echo "✓ G2PWModel already exists"
fi

echo ""
echo "========================================"
echo "All models downloaded successfully!"
echo "========================================"
echo ""
echo "Downloaded models:"
echo ""
echo "  RVC Models (required):"
echo "    - models/rvc_assets/hubert/hubert_base.pt (181MB)"
echo "    - models/rvc_assets/rmvpe/rmvpe.pt (173MB)"
echo ""
echo "  RVC Models (optional):"
echo "    - models/rvc_assets/rmvpe/rmvpe.onnx (345MB, AMD/Intel GPU)"
echo ""
echo "  GPT-SoVITS Models (Step 1 & 2):"
echo "    - models/gptsovits_assets/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt"
echo "    - models/gptsovits_assets/pretrained_models/s1v3.ckpt"
echo "    - models/gptsovits_assets/pretrained_models/s2G488k.pth"
echo "    - models/gptsovits_assets/pretrained_models/s2D488k.pth"
echo "    - models/gptsovits_assets/pretrained_models/s2Gv3.pth"
echo "    - models/gptsovits_assets/pretrained_models/chinese-hubert-base/"
echo "    - models/gptsovits_assets/pretrained_models/chinese-roberta-wwm-ext-large/"
echo "    - models/gptsovits_assets/pretrained_models/... (other variants)"
echo ""
echo "  G2PWModel (Chinese TTS):"
echo "    - models/gptsovits_assets/G2PWModel/g2pW.onnx (562MB)"
echo ""
echo "You can now build the Docker image:"
echo "  docker build -t voice-ai-platform ."
