# RunPod 持久化存储迁移指南

> 解决 RunPod 自动挂载 `/workspace` 导致镜像内容被覆盖的问题

---

## 问题背景

RunPod 平台会自动将持久化存储挂载到 `/workspace` 目录，这会导致 Docker 镜像中原本构建在 `/workspace` 下的所有内容被清空。

## 解决方案

采用**符号链接方案**：
- **代码和静态资源** → 放在 `/app` 目录（不被挂载覆盖）
- **用户数据和配置** → 放在 `/workspace/data/` 目录（持久化存储）
- **符号链接** → 在 `/app` 下创建链接，指向 `/workspace/data/`

---

## 目录结构

### 容器内部结构

```
/app/                                    # 代码目录（非持久化）
├── gateway/                             # API Gateway 代码
│   ├── main.py
│   ├── voices.yaml → /workspace/data/configs/voices.yaml  (symlink)
│   └── api_keys.yaml → /workspace/data/configs/api_keys.yaml  (symlink)
├── webui/                               # WebUI 代码
├── GPT-SoVITS/                          # TTS 引擎代码
│   └── GPT_SoVITS/pretrained_models/    # 预训练模型（静态文件）
├── RVC/                                 # RVC 引擎代码
│   └── assets/                          # RVC 资源（静态文件）
├── models/                              # 模型目录
│   └── custom_voices → /workspace/data/models/custom_voices  (symlink)
├── venvs/                               # Python 虚拟环境
├── supervisord.conf                     # Supervisor 配置
└── deploy.sh                            # 启动脚本

/workspace/data/                         # 持久化数据目录
├── models/
│   └── custom_voices/                   # 用户上传的自定义模型
│       ├── gptsovits/
│       │   └── <voice_name>/
│       │       ├── gpt.ckpt
│       │       ├── sovits.pth
│       │       └── reference.wav
│       └── rvc/
│           └── <model_name>/
│               ├── model.pth
│               └── model.index
└── configs/
    ├── voices.yaml                      # 声音配置
    └── api_keys.yaml                    # API 密钥配置
```

---

## 修改的文件清单

| 文件 | 修改内容 |
|------|----------|
| `Dockerfile` | `/workspace` → `/app`（所有 COPY、mkdir、venv 路径） |
| `deploy.sh` | 创建 `/workspace/data/` 结构，建立符号链接 |
| `supervisord.conf` | `/workspace/venvs/` → `/app/venvs/`，工作目录改为 `/app` |
| `gateway/main.py` | 配置路径改为 `/app/gateway/`，RVC 模型路径改为 `/app/models/` |
| `webui/app.py` | 配置路径和模型路径改为 `/app/`，sys.path 改为 `/app/gateway` |
| `gateway/voices.yaml` | 默认 reference.wav 路径改为 `/workspace/data/models/...` |

---

## 部署流程

1. **构建镜像**
   ```bash
   docker build -t voice-ai-platform:latest .
   ```

2. **RunPod 部署设置**
   - **Container Image**: `ghcr.io/YOUR_USERNAME/voice-ai-platform:latest`
   - **Expose Ports**: 80, 8080
   - **Start Command**: `/app/deploy.sh`
   - **Environment Variables**:
     - `API_KEY=sk-your-secure-key`
     - `WEBUI_USER=admin`
     - `WEBUI_PASS=your-password`

3. **持久化存储自动工作**
   - 首次启动时，`deploy.sh` 会自动创建 `/workspace/data/` 目录结构
   - 用户上传的模型保存在 `/workspace/data/models/custom_voices/`
   - 配置文件保存在 `/workspace/data/configs/`
   - Pod 重启后数据依然存在

---

## 数据备份与恢复

### 备份持久化数据

在 RunPod 中执行：
```bash
# 打包所有持久化数据
tar czf /workspace/backup-$(date +%Y%m%d).tar.gz -C /workspace data/

# 下载到本地（通过 RunPod 的 Web Terminal 或文件管理器）
```

### 恢复数据到新 Pod

```bash
# 上传备份文件到新的 Pod
# 解压到 /workspace/
tar xzf backup-20240310.tar.gz -C /workspace/
```

---

## 迁移旧数据（如有）

如果你已有旧的 `/workspace/models/custom_voices/` 数据，需要迁移到新结构：

```bash
# 在 RunPod 容器内执行
mkdir -p /workspace/data/models/
mv /workspace/models/custom_voices /workspace/data/models/
```

---

## 验证部署

启动后检查符号链接是否正确：

```bash
# 检查符号链接
ls -la /app/models/custom_voices
# 应该显示: /app/models/custom_voices -> /workspace/data/models/custom_voices

ls -la /app/gateway/voices.yaml
# 应该显示: /app/gateway/voices.yaml -> /workspace/data/configs/voices.yaml

# 检查服务状态
supervisorctl status
```

---

## 常见问题

**Q: 为什么不用 `/workspace` 作为代码目录？**
A: RunPod 挂载持久化存储时会清空 `/workspace` 的内容，所以代码必须放在其他目录（如 `/app`）。

**Q: 预训练模型在哪里？**
A: 预训练模型（如 GPT-SoVITS base models）是静态文件，构建时 COPY 到 `/app/GPT-SoVITS/...`，不需要持久化。

**Q: 如何更新代码？**
A: 重新构建 Docker 镜像并部署新版本。用户数据（在 `/workspace/data/`）不受影响。

---

**Last Updated**: 2024
**Migration Version**: 2.0
