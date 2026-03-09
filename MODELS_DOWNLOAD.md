# Voice AI Platform - Model Download Guide

在构建 Docker 镜像之前，需要手动下载预训练模型文件。

## 下载地址 (Download URLs)

| 组件 | 下载地址 | 说明 |
|------|----------|------|
| **RVC Models** | `https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/{filename}` | RVC 官方模型 (rmvpe.onnx 可选) |
| **GPT-SoVITS Pretrained** | `https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/pretrained_models.zip` | 官方打包的 Step 1 & 2 模型 (~4.5GB) |
| **G2PWModel** | `https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/G2PWModel.zip` | 中文 TTS 推理模型 (~562MB) |

## 本地文件结构 (Host Structure)

下载后，所有模型保存在 `models/` 文件夹，**不要放入 git submodules**:

```
models/
├── gptsovits_assets/              # GPT-SoVITS 预训练模型 (zip 解压后重命名)
│   ├── s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt   # Step 1 v1
│   ├── s1v3.ckpt                                        # Step 1 v3
│   ├── s2G488k.pth                                       # Step 2 v1/v2 G
│   ├── s2D488k.pth                                       # Step 2 v1/v2 D
│   ├── s2Gv3.pth                                         # Step 2 v3 G
│   ├── chinese-hubert-base/
│   ├── chinese-roberta-wwm-ext-large/
│   ├── gsv-v2final-pretrained/
│   ├── gsv-v4-pretrained/
│   ├── v2Pro/
│   └── sv/
├── g2pwmodel/                     # G2PW 推理模型
│   ├── g2pW.onnx
│   ├── char_bopomofo_dict.json
│   └── ...
└── rvc_assets/                    # RVC 预训练模型
    ├── hubert/
    │   └── hubert_base.pt         # 必需
    └── rmvpe/
        ├── rmvpe.pt               # 必需
        └── rmvpe.onnx             # 可选 (AMD/Intel GPU)
```

## Docker 容器内位置 (Container Structure)

构建镜像后，模型将被复制到：

```
/workspace/
├── GPT-SoVITS/
│   └── GPT_SoVITS/
│       ├── pretrained_models/     # ← models/gptsovits_assets/
│       │   ├── s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt
│       │   ├── s2G488k.pth
│       │   └── ...
│       └── text/
│           └── G2PWModel/         # ← models/g2pwmodel/
│               ├── g2pW.onnx
│               └── ...
└── RVC/
    └── assets/                    # ← models/rvc_assets/
        ├── hubert/
        │   └── hubert_base.pt
        └── rmvpe/
            ├── rmvpe.pt
            └── rmvpe.onnx
```

## 快速下载

```bash
bash download_models.sh
```

脚本执行流程：
1. 下载 RVC 模型到 `models/rvc_assets/`
2. 下载 `pretrained_models.zip` 并解压，将 `pretrained_models/` 重命名为 `models/gptsovits_assets/`
3. 下载 `G2PWModel.zip` 并解压到 `models/g2pwmodel/`

## 手动下载

### 1. RVC 模型

```bash
mkdir -p models/rvc_assets/hubert models/rvc_assets/rmvpe

wget -O models/rvc_assets/hubert/hubert_base.pt \
    https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt

wget -O models/rvc_assets/rmvpe/rmvpe.pt \
    https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt

# rmvpe.onnx 是可选的，仅用于 AMD/Intel GPU
# wget -O models/rvc_assets/rmvpe/rmvpe.onnx \
#     https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.onnx
```

### 2. GPT-SoVITS 模型 (Step 1 & 2)

```bash
# 下载官方打包的模型
wget -O pretrained_models.zip \
    https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/pretrained_models.zip

# 解压到 models/ 目录 (会创建 pretrained_models/ 子文件夹)
unzip -q -o pretrained_models.zip -d models/
rm pretrained_models.zip

# 重命名为 gptsovits_assets/
mv models/pretrained_models models/gptsovits_assets
```

### 3. G2PWModel (中文 TTS)

```bash
# 下载 G2PWModel
wget -O G2PWModel.zip \
    https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/G2PWModel.zip

# 解压到 models/ 目录 (会创建 G2PWModel/ 子文件夹)
unzip -q -o G2PWModel.zip -d models/
rm G2PWModel.zip

# 重命名为 g2pwmodel/
mv models/G2PWModel models/g2pwmodel

# 验证: models/g2pwmodel/g2pW.onnx
```

## Step 1 & Step 2 模型说明

### Step 1: GPT 模型 (AR - AutoRegressive)
- **v1**: `s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt` (~155MB)
- **v3**: `s1v3.ckpt` (~155MB)
- **位置**: `models/gptsovits_assets/` → 容器内 `GPT_SoVITS/pretrained_models/`
- **作用**: 生成语音的语义 token

### Step 2: SoVITS 模型
- **v1/v2 Generator**: `s2G488k.pth` (~106MB)
- **v1/v2 Discriminator**: `s2D488k.pth` (~94MB)
- **v3 Generator**: `s2Gv3.pth` (~769MB)
- **位置**: `models/gptsovits_assets/` → 容器内 `GPT_SoVITS/pretrained_models/`
- **作用**: 将语义 token 转换为音频波形

### G2PWModel (中文 TTS 推理)
- **文件**: `g2pW.onnx` (~635MB)
- **位置**: `models/g2pwmodel/` → 容器内 `GPT_SoVITS/text/G2PWModel/`
- **作用**: 中文多音字推理 ( Grapheme-to-Phoneme )

## 构建前检查清单

```bash
# RVC 模型 (约 350MB 必需，700MB 含可选)
ls -lh models/rvc_assets/hubert/hubert_base.pt      # 181MB (必需)
ls -lh models/rvc_assets/rmvpe/rmvpe.pt             # 173MB (必需)
ls -lh models/rvc_assets/rmvpe/rmvpe.onnx           # 345MB (可选)

# GPT-SoVITS 模型 (约 4.5GB)
ls -lh models/gptsovits_assets/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt
ls -lh models/gptsovits_assets/s2G488k.pth
ls -lh models/gptsovits_assets/s2D488k.pth
ls -lh models/gptsovits_assets/chinese-hubert-base/
ls -lh models/gptsovits_assets/chinese-roberta-wwm-ext-large/

# G2PWModel (约 562MB)
ls -lh models/g2pwmodel/g2pW.onnx
```

## 网络问题

如果 HuggingFace 无法访问：

1. **镜像站**: `https://hf-mirror.com/`
2. **ModelScope**: `https://www.modelscope.cn/`
3. **手动下载**: 搜索 "GPT-SoVITS 预训练模型" 百度网盘

## 注意事项

1. **不要**将模型下载到 `GPT-SoVITS/` 或 `RVC/` submodules 中，这会导致 git 污染
2. 所有模型统一放在 `models/` 文件夹，Dockerfile 会在构建时 COPY 到正确位置
3. `pretrained_models.zip` 和 `G2PWModel.zip` 都包含嵌套文件夹，解压后需要重命名
4. 如果已运行过 `download_models.sh`，请勿重复下载，脚本会自动检测已存在的文件
