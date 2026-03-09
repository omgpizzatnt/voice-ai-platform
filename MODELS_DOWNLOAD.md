# RVC 模型文件下载指南

在构建 Docker 镜像之前，需要手动下载 RVC 必需的预训练模型文件。

## 需要的文件

| 文件 | 大小 | 下载地址 | 放置位置 |
|------|------|----------|----------|
| `hubert_base.pt` | 181MB | [HuggingFace](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt) | `models/rvc_assets/hubert/` |
| `rmvpe.pt` | 173MB | [HuggingFace](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt) | `models/rvc_assets/rmvpe/` |
| `rmvpe.onnx` | 345MB | [HuggingFace](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.onnx) | `models/rvc_assets/rmvpe/` |

**总计：约 700MB**

## 目录结构

```
voice-ai-platform/
├── models/
│   ├── custom_voices/        # TTS 音色存放
│   ├── rvc_pipelines/        # RVC 配置
│   └── rvc_assets/           # RVC 预训练模型
│       ├── hubert/
│       │   └── hubert_base.pt
│       └── rmvpe/
│           ├── rmvpe.pt
│           └── rmvpe.onnx
├── RVC/                      # RVC 源码 (submodule)
├── GPT-SoVITS/               # GPT-SoVITS 源码 (submodule)
└── ...
```

## 下载方法

### 方法 1: 直接下载（浏览器）

点击上表中的下载链接，将文件保存到对应目录。

### 方法 2: 使用 wget

```bash
cd voice-ai-platform/models/rvc_assets

# 下载 hubert
wget -O hubert/hubert_base.pt https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt

# 下载 rmvpe
wget -O rmvpe/rmvpe.pt https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt
wget -O rmvpe/rmvpe.onnx https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.onnx
```

### 方法 3: 使用 Git LFS（如果已配置）

```bash
git lfs install
git clone https://huggingface.co/lj1995/VoiceConversionWebUI temp_models
cp temp_models/hubert_base.pt models/rvc_assets/hubert/
cp temp_models/rmvpe.pt temp_models/rmvpe.onnx models/rvc_assets/rmvpe/
rm -rf temp_models
```

### 方法 4: 从已有项目复制

如果你本地已有 RVC 项目，直接复制：

```bash
cp /path/to/your/RVC/assets/hubert/hubert_base.pt voice-ai-platform/models/rvc_assets/hubert/
cp /path/to/your/RVC/assets/rmvpe/rmvpe.pt voice-ai-platform/models/rvc_assets/rmvpe/
cp /path/to/your/RVC/assets/rmvpe/rmvpe.onnx voice-ai-platform/models/rvc_assets/rmvpe/
```

## 验证文件完整性

下载完成后，检查文件大小是否正确：

```bash
ls -lh models/rvc_assets/hubert/
ls -lh models/rvc_assets/rmvpe/
```

预期输出：
```
hubert_base.pt  181M

rmvpe.onnx      345M
rmvpe.pt        173M
```

## 镜像构建

确认所有文件放置正确后，构建镜像：

```bash
docker build -t voice-ai-platform .
```

## 网络问题

如果 HuggingFace 无法访问，可以尝试：

1. **镜像站**：
   - https://hf-mirror.com/lj1995/VoiceConversionWebUI

2. **百度网盘**（国内用户）：
   - 搜索 "RVC 预训练模型"

3. **GitHub Releases**：
   - 某些项目会在 Release 中提供模型文件

## 注意事项

- 这些模型文件**不需要提交到 Git**（已添加到 .gitignore）
- 构建镜像时会被 COPY 进去
- 模型文件较大，首次构建时间会增加约 2-3 分钟（取决于磁盘速度）
