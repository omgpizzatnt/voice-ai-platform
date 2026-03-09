# Voice AI Platform - Model Download Guide

在构建 Docker 镜像之前，需要手动下载预训练模型文件。

## 目录结构

```
models/
├── rvc_assets/                    # RVC 预训练模型
│   ├── hubert/
│   │   └── hubert_base.pt         # 181MB
│   └── rmvpe/
│       ├── rmvpe.pt               # 173MB
│       └── rmvpe.onnx             # 345MB
└── gptsovits_assets/              # GPT-SoVITS 预训练模型
    ├── s1/                        # Step 1: GPT 模型
    │   └── s1bert.ckpt
    └── s2/                        # Step 2: SoVITS 模型
        └── s2G.pth
```

## RVC 模型下载

| 文件 | 大小 | 下载地址 | 放置位置 |
|------|------|----------|----------|
| `hubert_base.pt` | 181MB | [HuggingFace](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt) | `models/rvc_assets/hubert/` |
| `rmvpe.pt` | 173MB | [HuggingFace](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt) | `models/rvc_assets/rmvpe/` |
| `rmvpe.onnx` | 345MB | [HuggingFace](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.onnx) | `models/rvc_assets/rmvpe/` |

**总计：约 700MB**

### 下载方法

```bash
# 使用脚本一键下载
bash download_models.sh
```

或手动下载：

```bash
mkdir -p models/rvc_assets/hubert models/rvc_assets/rmvpe

wget -O models/rvc_assets/hubert/hubert_base.pt \
    https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt

wget -O models/rvc_assets/rmvpe/rmvpe.pt \
    https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt

wget -O models/rvc_assets/rmvpe/rmvpe.onnx \
    https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.onnx
```

## GPT-SoVITS 模型下载

**核心模型 (Step 1 & 2)** - 放在 `models/gptsovits_assets/`:

| 组件 | 文件 | 大小 | 下载地址 |
|------|------|------|----------|
| Step 1 (GPT) | `s1bert.ckpt` | ~2GB | [GPT-SoVITS Models](https://huggingface.co/lj1995/GPT-SoVITS) |
| Step 2 (SoVITS) | `s2G.pth` | ~400MB | [GPT-SoVITS Models](https://huggingface.co/lj1995/GPT-SoVITS) |

**中文 TTS 额外需要**:
- G2PWModel (~100MB): [下载链接](https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/G2PWModel.zip)

### 下载方法

```bash
# 创建目录
mkdir -p models/gptsovits_assets/s1 models/gptsovits_assets/s2

# 下载 Step 1 模型 (GPT)
wget -O models/gptsovits_assets/s1/s1bert.ckpt \
    https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/s1bert.ckpt

# 下载 Step 2 模型 (SoVITS)
wget -O models/gptsovits_assets/s2/s2G.pth \
    https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/s2G.pth

# 中文 TTS: 下载 G2PWModel
wget -O /tmp/G2PWModel.zip \
    https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/G2PWModel.zip
unzip /tmp/G2PWModel.zip -d GPT-SoVITS/GPT_SoVITS/text/
mv GPT-SoVITS/GPT_SoVITS/text/G2PWModel* GPT-SoVITS/GPT_SoVITS/text/G2PWModel
```

**注意**: GPT-SoVITS 模型较大 (~2.5GB)，请确保有足够的磁盘空间和良好的网络连接。

## 快速下载脚本

使用提供的脚本自动下载所有模型：

```bash
bash download_models.sh
```

## 镜像构建

确认所有模型下载完成后，构建镜像：

```bash
docker build -t voice-ai-platform .
```

## 网络问题

如果 HuggingFace 无法访问，可以尝试：

1. **镜像站**: https://hf-mirror.com/
2. **ModelScope** (国内): https://modelscope.cn/
3. **百度网盘**: 搜索 "GPT-SoVITS 预训练模型"

## 模型文件清单

构建前请检查以下文件是否存在：

```bash
# RVC 模型
ls -lh models/rvc_assets/hubert/hubert_base.pt      # 181MB
ls -lh models/rvc_assets/rmvpe/rmvpe.pt             # 173MB
ls -lh models/rvc_assets/rmvpe/rmvpe.onnx           # 345MB

# GPT-SoVITS 模型
ls -lh models/gptsovits_assets/s1/s1bert.ckpt       # ~2GB
ls -lh models/gptsovits_assets/s2/s2G.pth           # ~400MB

# 中文 TTS (可选)
ls -lh GPT-SoVITS/GPT_SoVITS/text/G2PWModel/        # ~100MB
```
