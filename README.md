# Voice AI Platform

> OpenAI-compatible TTS API with GPT-SoVITS and RVC support

## Quick Start (Using Pre-built Image)

The easiest way to run this project is using the pre-built Docker image from GitHub Container Registry.

### Prerequisites for Private Repository

Since this is a **private repository**, you need to authenticate with GitHub Container Registry:

1. **Create GitHub Personal Access Token**:
   - Go to GitHub Settings -> Developer settings -> Personal access tokens
   - Click "Generate new token (classic)"
   - Select scopes: `read:packages`, `write:packages`, `delete:packages`
   - Generate and copy the token

2. **Docker Login** (for local use):
   ```bash
   echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
   ```

### RunPod Deployment (Recommended)

RunPod supports private images with authentication:

1. **Create Pod** in RunPod:
   - Select **Custom Image**
   - Image URL: `ghcr.io/YOUR_USERNAME/voice-ai-platform:latest`

2. **Set Environment Variables**:
   ```
   API_KEY=sk-your-secure-key
   WEBUI_USER=admin
   WEBUI_PASS=your-password
   ```

3. **Docker Command** (for authentication):
   ```bash
   docker login ghcr.io -u YOUR_GITHUB_USERNAME -p YOUR_GITHUB_TOKEN
   ```
   Or set as Pod Environment Variable:
   ```
   GHCR_USERNAME=YOUR_GITHUB_USERNAME
   GHCR_TOKEN=YOUR_GITHUB_TOKEN
   ```

4. **Expose Ports**: 80, 8080

5. **Start Command**: `/workspace/deploy.sh`

### Local Docker

```bash
# Login to GitHub Container Registry (one-time setup)
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Pull pre-built image
docker pull ghcr.io/YOUR_USERNAME/voice-ai-platform:latest

# Run container
docker run -d \
  --name voice-ai \
  --gpus all \
  -p 80:80 \
  -p 8080:8080 \
  -e API_KEY=sk-your-key \
  -e WEBUI_USER=admin \
  -e WEBUI_PASS=password \
  ghcr.io/YOUR_USERNAME/voice-ai-platform:latest
```

---

## Build Your Own Image

### Prerequisites

Before building, you need to prepare the following:

1. **Clone submodules** (GPT-SoVITS and RVC):
   ```bash
   git submodule update --init --recursive
   ```

2. **Download pre-trained models** (~3.5GB total):
   ```bash
   # Use the provided script to download all models
   bash download_models.sh
   ```

   **RVC Models** (~350MB required, ~700MB with optional):
   - `models/rvc_assets/hubert/hubert_base.pt` (181MB, required)
   - `models/rvc_assets/rmvpe/rmvpe.pt` (173MB, required)
   - `models/rvc_assets/rmvpe/rmvpe.onnx` (345MB, optional for AMD/Intel GPU)

   **GPT-SoVITS Models** (~5GB total):
   - Pretrained models (~4.5GB, from `pretrained_models.zip`):
     - Step 1 v1: `s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt` (~155MB)
     - Step 1 v3: `s1v3.ckpt` (~155MB)
     - Step 2 v1/v2: `s2G488k.pth` (~106MB), `s2D488k.pth` (~94MB)
     - Step 2 v3: `s2Gv3.pth` (~769MB)
     - Encoders: `chinese-hubert-base/`, `chinese-roberta-wwm-ext-large/`
     - Other variants: `gsv-v2final-pretrained/`, `gsv-v4-pretrained/`, `v2Pro/`, `sv/`
   - G2PWModel (~562MB, from `G2PWModel.zip`):
     - `models/gptsovits_assets/G2PWModel/g2pW.onnx` for Chinese TTS inference

   See `MODELS_DOWNLOAD.md` for manual download instructions and alternative mirrors.

### Build

```bash
# Build image
docker build -t voice-ai-platform .

# Run locally
docker run -d \
  --name voice-ai \
  --gpus all \
  -p 80:80 \
  -p 8080:8080 \
  -e API_KEY=sk-your-key \
  -e WEBUI_USER=admin \
  -e WEBUI_PASS=password \
  voice-ai-platform
```

### Project Structure

```
voice-ai-platform/
├── .github/workflows/        # GitHub Actions
├── gateway/                  # API Gateway (FastAPI)
├── webui/                    # Management UI (Gradio)
├── GPT-SoVITS/               # GPT-SoVITS submodule
├── RVC/                      # RVC submodule
├── models/
│   ├── custom_voices/        # TTS voice models
│   ├── rvc_pipelines/        # RVC pipeline configs
│   ├── rvc_assets/           # RVC pretrained models
│   │   ├── hubert/
│   │   │   └── hubert_base.pt
│   │   └── rmvpe/
│   │       ├── rmvpe.pt
│   │       └── rmvpe.onnx    # optional for AMD/Intel GPU
│   └── gptsovits_assets/     # GPT-SoVITS pretrained models
│       ├── pretrained_models/                                 # Main pretrained models (from pretrained_models.zip)
│       │   ├── s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt  # Step 1 v1
│       │   ├── s1v3.ckpt                                        # Step 1 v3
│       │   ├── s2G488k.pth                                      # Step 2 v1/v2 G
│       │   ├── s2D488k.pth                                      # Step 2 v1/v2 D
│       │   ├── s2Gv3.pth                                        # Step 2 v3 G
│       │   ├── chinese-hubert-base/                             # Content encoder
│       │   ├── chinese-roberta-wwm-ext-large/                   # Text encoder
│       │   ├── gsv-v2final-pretrained/                          # v2 final
│       │   ├── gsv-v4-pretrained/                               # v4
│       │   ├── v2Pro/                                           # v2Pro
│       │   └── sv/                                              # Speaker verification
│       └── G2PWModel/                                         # G2PW model for Chinese TTS (from G2PWModel.zip)
│           ├── g2pW.onnx                                      # Main model file (~635MB)
│           ├── config.py                                      # Model configuration
│           ├── char_bopomofo_dict.json                        # Character Bopomofo dictionary
│           ├── bopomofo_to_pinyin_wo_tune_dict.json           # Bopomofo to Pinyin mapping
│           ├── MONOPHONIC_CHARS.txt                           # Monophonic characters list
│           ├── POLYPHONIC_CHARS.txt                           # Polyphonic characters list
│           ├── record.log                                     # Download record
│           └── version                                        # Version info
├── Dockerfile
├── supervisord.conf
└── deploy.sh
```

---

## API Usage

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost/v1",
    api_key="sk-your-key"
)

response = client.audio.speech.create(
    model="tts-1",
    input="Hello world",
    voice="default",
    response_format="mp3"
)

response.stream_to_file("output.mp3")
```

## WebUI

Access `http://localhost:8080` with Basic Auth credentials:
- **Tab 1**: Model Upload - Upload GPT-SoVITS and RVC models
- **Tab 2**: TTS Voice Registration - Configure GPT-SoVITS voices
- **Tab 3**: RVC Pipeline Configuration - Configure TTS+RVC pipelines
- **Tab 4**: API Key Management - Generate and manage API keys

## Model Management

### File Naming Convention

When uploading models through WebUI, files are automatically renamed to standard names:

**GPT-SoVITS Models** (`/workspace/models/custom_voices/gptsovits/<model_name>/`):
- `gpt.ckpt` - GPT weights (renamed from uploaded .ckpt file)
- `sovits.pth` - SoVITS weights (renamed from uploaded .pth file)
- `reference.wav` - Reference audio (renamed from uploaded .wav file)

**RVC Models** (`/workspace/models/custom_voices/rvc/<model_name>/`):
- `model.pth` - Model weights (renamed from uploaded .pth file)
- `model.index` - Feature index (renamed from uploaded .index file, optional)

### voices.yaml Configuration

**GPT-SoVITS Voice:**
```yaml
voices:
  my_voice:
    name: "My Voice"
    type: "tts"
    version: "v2"
    gpt_weights: "/workspace/models/custom_voices/gptsovits/my_voice/gpt.ckpt"
    sovits_weights: "/workspace/models/custom_voices/gptsovits/my_voice/sovits.pth"
    refer_wav_path: "/workspace/models/custom_voices/gptsovits/my_voice/reference.wav"
    prompt_text: "Reference text here"
    prompt_lang: "zh"
    language: "auto"
```

**RVC Pipeline:**
```yaml
voices:
  my_pipeline:
    name: "My Pipeline"
    type: "rvc_pipeline"
    base_tts_voice: "default"
    rvc_model_name: "my_rvc_model"
    # Model paths are auto-generated:
    # model_path: /workspace/models/custom_voices/rvc/my_rvc_model/model.pth
    # index_path: /workspace/models/custom_voices/rvc/my_rvc_model/model.index (if exists)
    pitch: 0
    f0_method: "rmvpe"
    index_rate: 0.75
```

## Architecture

```
RunPod Container
├── API Gateway (Port 80) - OpenAI-compatible API
├── WebUI (Port 8080) - Gradio management interface
├── GPT-SoVITS Workers (Ports 9881-9884) - TTS inference
└── RVC Workers (Ports 7866-7867) - Voice conversion
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `sk-change-me` | Default API key |
| `WEBUI_USER` | `admin` | WebUI username |
| `WEBUI_PASS` | `admin` | WebUI password |

## Available Image Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest build from main branch |
| `v1.0.0` | Specific version release |
| `v1.0` | Minor version (auto-updated) |
| `v1` | Major version (auto-updated) |
| `sha-abc123` | Specific commit |