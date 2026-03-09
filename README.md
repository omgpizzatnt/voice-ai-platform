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

   **RVC Models** (~700MB):
   - `models/rvc_assets/hubert/hubert_base.pt` (181MB)
   - `models/rvc_assets/rmvpe/rmvpe.pt` (173MB)
   - `models/rvc_assets/rmvpe/rmvpe.onnx` (345MB)

   **GPT-SoVITS Models** (~2.5GB):
   - `models/gptsovits_assets/s1/s1bert.ckpt` (~2GB, Step 1: GPT model)
   - `models/gptsovits_assets/s2/s2G.pth` (~400MB, Step 2: SoVITS model)

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
│   │       └── rmvpe.onnx
│   └── gptsovits_assets/     # GPT-SoVITS pretrained models
│       ├── s1/
│       │   └── s1bert.ckpt   # Step 1: GPT model
│       └── s2/
│           └── s2G.pth       # Step 2: SoVITS model
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
- **Tab 1**: TTS Voice Registration
- **Tab 2**: RVC Pipeline Configuration
- **Tab 3**: API Key Management

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

## License

MIT
