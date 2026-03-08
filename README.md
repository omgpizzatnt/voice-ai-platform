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

If you want to build the image yourself:

### Option 1: GitHub Actions (Auto-build on push)

1. Push to `main` branch or create a tag in your private repo
2. GitHub Actions automatically builds and pushes to `ghcr.io`
3. See `.github/workflows/docker-build.yml` for details
4. **Note**: GitHub Actions automatically uses `GITHUB_TOKEN` - no extra setup needed

### Option 2: Local Docker Build

```bash
# Build image
docker build -t voice-ai-platform .

# Tag for GitHub Container Registry
docker tag voice-ai-platform ghcr.io/YOUR_USERNAME/voice-ai-platform:latest

# Login and push (optional)
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
docker push ghcr.io/YOUR_USERNAME/voice-ai-platform:latest

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

### Option 3: Build from Source (No Docker)

Requirements:
- Python 3.10+
- CUDA 12.1+
- 16GB+ RAM

```bash
# Install dependencies
pip install -r gateway/requirements.txt
pip install -r webui/requirements.txt

# Clone GPT-SoVITS
cd /workspace
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS && pip install -r requirements.txt

# Clone RVC with FastAPI wrapper
cd /workspace
git clone https://github.com/SocAIty/Retrieval-based-Voice-Conversion-FastAPI.git RVC
cd RVC && pip install -r requirements.txt

# Set env vars
export API_KEY=sk-your-key
export WEBUI_USER=admin
export WEBUI_PASS=password

# Start services (in separate terminals)
# Terminal 1: Gateway
python gateway/main.py

# Terminal 2: WebUI
python webui/app.py

# Terminal 3-6: GPT-SoVITS workers
python GPT-SoVITS/api.py -p 9881 -dr "ref.wav" -dt "text" -dl "zh"
python GPT-SoVITS/api.py -p 9882 -dr "ref.wav" -dt "text" -dl "zh"
python GPT-SoVITS/api.py -p 9883 -dr "ref.wav" -dt "text" -dl "zh"
python GPT-SoVITS/api.py -p 9884 -dr "ref.wav" -dt "text" -dl "zh"

# Terminal 7-8: RVC workers
python RVC/api.py --port 7866 --device cuda
python RVC/api.py --port 7867 --device cuda
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

## File Structure

```
/workspace/
├── gateway/main.py         # FastAPI gateway
├── gateway/voices.yaml     # Voice configurations
├── gateway/api_keys.yaml   # API key registry
├── webui/app.py           # Gradio WebUI
├── GPT-SoVITS/            # GPT-SoVITS source
├── RVC/                   # RVC with FastAPI wrapper
├── models/                # Model storage
│   ├── custom_voices/
│   └── rvc_pipelines/
└── supervisord.conf       # Process management
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
