import os
import re
import time
import asyncio
import hashlib
import logging
from typing import Optional, Dict, List, Literal
from datetime import datetime
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

import aiohttp
import langid
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from yaml_utils import AtomicYAML

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_API_KEY = os.getenv("API_KEY", "sk-change-me-in-production")
GPT_SOVITS_BASE_URL = "http://localhost"
GPT_SOVITS_PORTS = [9881, 9882, 9883, 9884]
RVC_BASE_URL = "http://localhost"
RVC_PORTS = [7866, 7867]
VOICES_CONFIG_PATH = "/app/gateway/voices.yaml"
API_KEYS_PATH = "/app/gateway/api_keys.yaml"
CONFIG_RELOAD_INTERVAL = 5

langid.set_languages(['en', 'zh', 'ja', 'ko'])

SUPPORTED_LANGUAGES = [
    "auto", "auto_yue", "en", "zh", "ja", "yue", 
    "ko", "all_zh", "all_ja", "all_yue", "all_ko"
]


@dataclass
class APIKeyEntry:
    key_hash: str
    created_at: str
    last_used: Optional[str] = None
    active: bool = True
    _last_persisted: Optional[str] = None


@dataclass
class WorkerState:
    port: int
    worker_type: str
    healthy: bool = True
    last_check: float = field(default_factory=time.time)
    loaded_model: Optional[str] = None
    request_count: int = 0


class VoicesRegistry:
    def __init__(self):
        self.voices: Dict = {}
        self.api_keys: Dict[str, APIKeyEntry] = {}
        self._last_voices_mtime = 0
        self._last_keys_mtime = 0
        self._lock = asyncio.Lock()
        
    async def load_voices(self):
        try:
            if os.path.exists(VOICES_CONFIG_PATH):
                mtime = os.path.getmtime(VOICES_CONFIG_PATH)
                if mtime > self._last_voices_mtime:
                    data = AtomicYAML.load(VOICES_CONFIG_PATH)
                    if data:
                        async with self._lock:
                            self.voices = data.get('voices', {})
                    self._last_voices_mtime = mtime
                    logger.info(f"Loaded {len(self.voices)} voices from config")
        except Exception as e:
            logger.error(f"Failed to load voices: {e}")
    
    async def load_api_keys(self):
        try:
            if os.path.exists(API_KEYS_PATH):
                mtime = os.path.getmtime(API_KEYS_PATH)
                if mtime > self._last_keys_mtime:
                    data = AtomicYAML.load(API_KEYS_PATH)
                    if data:
                        keys_data = data.get('api_keys', {})
                        async with self._lock:
                            self.api_keys = {}
                            for k, v in keys_data.items():
                                entry = APIKeyEntry(
                                    key_hash=v.get('key_hash', k),
                                    created_at=v.get('created_at', ''),
                                    last_used=v.get('last_used'),
                                    active=v.get('active', True),
                                    _last_persisted=v.get('last_used')
                                )
                                self.api_keys[k] = entry
                    self._last_keys_mtime = mtime
                    logger.info(f"Loaded {len(self.api_keys)} API keys")
            else:
                await self._init_default_key()
        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")
    
    async def _init_default_key(self):
        key_hash = hashlib.sha256(DEFAULT_API_KEY.encode()).hexdigest()[:16]
        self.api_keys[key_hash] = APIKeyEntry(
            key_hash=key_hash,
            created_at=datetime.now().isoformat(),
            active=True,
            _last_persisted=datetime.now().isoformat()
        )
        await self._persist_api_keys()

    async def _persist_api_keys(self):
        async with self._lock:
            data = {
                'api_keys': {
                    k: {
                        'key_hash': v.key_hash,
                        'created_at': v.created_at,
                        'last_used': v.last_used,
                        'active': v.active
                    }
                    for k, v in self.api_keys.items()
                }
            }
        AtomicYAML.save(API_KEYS_PATH, data)
    
    async def validate_key(self, auth_header: Optional[str]) -> bool:
        if not auth_header:
            return False

        token = auth_header.replace("Bearer ", "").strip()
        key_hash = hashlib.sha256(token.encode()).hexdigest()[:16]

        entry = self.api_keys.get(key_hash)
        if entry and entry.active:
            now = datetime.now()
            entry.last_used = now.isoformat()

            should_persist = True
            if entry._last_persisted:
                try:
                    last_dt = datetime.fromisoformat(entry._last_persisted)
                    if (now - last_dt).total_seconds() < 60:
                        should_persist = False
                except ValueError:
                    pass

            if should_persist:
                entry._last_persisted = entry.last_used
                await self._persist_api_keys()
            return True
        return False
    
    def get_voice(self, voice_id: str) -> Optional[Dict]:
        return self.voices.get(voice_id)
    
    def list_voices(self) -> List[Dict]:
        return [
            {
                "voice_id": vid,
                "name": v.get("name", vid),
                "type": v.get("type", "tts"),
                "language": v.get("language", "auto")
            }
            for vid, v in self.voices.items()
        ]


registry = VoicesRegistry()


class WorkerPool:
    def __init__(self):
        self.gpt_sovits_workers: List[WorkerState] = [
            WorkerState(port=p, worker_type='gpt_sovits') 
            for p in GPT_SOVITS_PORTS
        ]
        self.rvc_workers: List[WorkerState] = [
            WorkerState(port=p, worker_type='rvc') 
            for p in RVC_PORTS
        ]
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def start(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),
            connector=aiohttp.TCPConnector(limit=100)
        )
    
    async def stop(self):
        if self.session:
            await self.session.close()
    
    async def health_check(self):
        for worker in self.gpt_sovits_workers + self.rvc_workers:
            try:
                base_url = GPT_SOVITS_BASE_URL if worker.worker_type == 'gpt_sovits' else RVC_BASE_URL
                async with self.session.get(
                    f"{base_url}:{worker.port}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    worker.healthy = resp.status == 200
            except:
                worker.healthy = False
            worker.last_check = time.time()
    
    def get_gpt_sovits_worker(self, model_name: Optional[str] = None) -> Optional[WorkerState]:
        healthy = [w for w in self.gpt_sovits_workers if w.healthy]
        if not healthy:
            return None
        
        if model_name:
            for w in healthy:
                if w.loaded_model == model_name:
                    return w
        
        return min(healthy, key=lambda w: w.request_count)
    
    def get_rvc_worker(self) -> Optional[WorkerState]:
        healthy = [w for w in self.rvc_workers if w.healthy]
        if not healthy:
            return None
        return min(healthy, key=lambda w: w.request_count)


worker_pool = WorkerPool()


class TTSRequest(BaseModel):
    model: str = Field(default="tts-1")
    input: str = Field(...)
    voice: str = Field(default="default")
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = Field(default="mp3")
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    extra_body: Optional[Dict] = Field(default=None)


class LanguageDetector:
    @staticmethod
    def detect(text: str) -> str:
        lang_override = re.search(r'\[LANG:(\w+)\]', text)
        if lang_override:
            lang = lang_override.group(1)
            if lang in SUPPORTED_LANGUAGES:
                return lang
        
        clean_text = re.sub(r'[a-zA-Z0-9\s\p{P}]', '', text)
        
        if not clean_text:
            return "auto"
        
        try:
            detected_lang, confidence = langid.classify(clean_text[:1000])
            
            lang_map = {
                'en': 'en',
                'zh': 'zh',
                'ja': 'ja',
                'ko': 'ko'
            }
            
            return lang_map.get(detected_lang, 'auto')
        except:
            return "auto"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API Gateway...")
    await registry.load_voices()
    await registry.load_api_keys()
    await worker_pool.start()
    
    reload_task = asyncio.create_task(config_reload_loop())
    health_task = asyncio.create_task(health_check_loop())
    
    yield
    
    reload_task.cancel()
    health_task.cancel()
    await worker_pool.stop()
    logger.info("API Gateway stopped")


app = FastAPI(
    title="Voice AI Platform API",
    description="OpenAI-compatible TTS API with GPT-SoVITS and RVC support",
    version="1.0.0",
    lifespan=lifespan
)


async def config_reload_loop():
    while True:
        try:
            await asyncio.sleep(CONFIG_RELOAD_INTERVAL)
            await registry.load_voices()
            await registry.load_api_keys()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Config reload error: {e}")


async def health_check_loop():
    while True:
        try:
            await asyncio.sleep(30)
            await worker_pool.health_check()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Health check error: {e}")


async def set_gpt_sovits_model(worker: WorkerState, gpt_weights: str, sovits_weights: str):
    if gpt_weights:
        url = f"{GPT_SOVITS_BASE_URL}:{worker.port}/set_gpt_weights"
        async with worker_pool.session.get(url, params={"weights_path": gpt_weights}) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                logger.warning(f"Failed to set GPT weights on worker {worker.port}: {error_text}")

    if sovits_weights:
        url = f"{GPT_SOVITS_BASE_URL}:{worker.port}/set_sovits_weights"
        async with worker_pool.session.get(url, params={"weights_path": sovits_weights}) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                logger.warning(f"Failed to set SoVITS weights on worker {worker.port}: {error_text}")


async def call_gpt_sovits(
    worker: WorkerState,
    text: str,
    voice_config: Dict,
    text_lang: str
) -> bytes:

    refer_wav_path = voice_config.get("refer_wav_path", "")
    prompt_text = voice_config.get("prompt_text", "")
    prompt_lang = voice_config.get("prompt_lang", "auto")

    if text_lang == "auto":
        text_lang = LanguageDetector.detect(text)

    gpt_weights = voice_config.get("gpt_weights", "")
    sovits_weights = voice_config.get("sovits_weights", "")
    model_id = f"{gpt_weights}:{sovits_weights}" if (gpt_weights or sovits_weights) else "default"

    if worker.loaded_model != model_id:
        if gpt_weights or sovits_weights:
            logger.info(f"Switching worker {worker.port} to model: {model_id}")
            await set_gpt_sovits_model(worker, gpt_weights, sovits_weights)
        worker.loaded_model = model_id

    params = {
        "refer_wav_path": refer_wav_path,
        "prompt_text": prompt_text,
        "prompt_language": prompt_lang,
        "text": text,
        "text_language": text_lang,
        "top_k": voice_config.get("top_k", 20),
        "top_p": voice_config.get("top_p", 0.6),
        "temperature": voice_config.get("temperature", 0.6),
        "speed_factor": voice_config.get("speed", 1.0),
        "text_split_method": voice_config.get("text_split_method", "cut5"),
        "batch_size": voice_config.get("batch_size", 1),
        "sample_steps": voice_config.get("sample_steps", 32),
    }

    # Remove empty parameters
    params = {k: v for k, v in params.items() if v is not None and v != ""}

    url = f"{GPT_SOVITS_BASE_URL}:{worker.port}/tts"

    async with worker_pool.session.get(url, params=params) as resp:
        if resp.status != 200:
            error_text = await resp.text()
            raise HTTPException(status_code=resp.status, detail=f"TTS worker error: {error_text}")

        worker.request_count += 1
        return await resp.read()


async def call_rvc(
    worker: WorkerState,
    audio_data: bytes,
    rvc_config: Dict
) -> bytes:

    model_name = rvc_config.get('rvc_model_name', '')

    model_path = f"/app/models/custom_voices/rvc/{model_name}/model.pth"
    index_path = f"/app/models/custom_voices/rvc/{model_name}/model.index"

    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail=f"RVC model not found: {model_path}")

    if not os.path.exists(index_path):
        index_path = ""

    data = aiohttp.FormData()
    data.add_field('model_name', model_name)
    data.add_field('model_path', model_path)
    if index_path:
        data.add_field('index_path', index_path)
    data.add_field('f0_up_key', str(rvc_config.get('pitch', 0)))
    data.add_field('f0_method', rvc_config.get('f0_method', 'rmvpe'))
    data.add_field('index_rate', str(rvc_config.get('index_rate', 0.75)))
    data.add_field('filter_radius', str(rvc_config.get('filter_radius', 3)))
    data.add_field('resample_sr', str(rvc_config.get('resample_sr', 0)))
    data.add_field('rms_mix_rate', str(rvc_config.get('rms_mix_rate', 0.25)))
    data.add_field('protect', str(rvc_config.get('protect', 0.33)))

    data.add_field(
        'input_file',
        audio_data,
        filename='input.wav',
        content_type='audio/wav'
    )

    url = f"{RVC_BASE_URL}:{worker.port}/convert"

    async with worker_pool.session.post(url, data=data) as resp:
        if resp.status != 200:
            error_text = await resp.text()
            raise HTTPException(status_code=resp.status, detail=f"RVC worker error: {error_text}")

        worker.request_count += 1
        return await resp.read()


@app.post("/v1/audio/speech")
async def create_speech(
    request: TTSRequest,
    authorization: Optional[str] = Header(None)
):
    if not await registry.validate_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    voice_config = registry.get_voice(request.voice)
    if not voice_config:
        available = list(registry.voices.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Voice '{request.voice}' not found. Available: {available}"
        )

    voice_type = voice_config.get("type", "tts")

    text_lang = voice_config.get("language", "auto")
    if request.extra_body and "language" in request.extra_body:
        text_lang = request.extra_body["language"]
    
    try:
        if voice_type == "tts":
            gpt_weights = voice_config.get("gpt_weights", "")
            sovits_weights = voice_config.get("sovits_weights", "")
            model_id = f"{gpt_weights}:{sovits_weights}" if (gpt_weights or sovits_weights) else None

            worker = worker_pool.get_gpt_sovits_worker(model_id)
            if not worker:
                raise HTTPException(status_code=503, detail="No available TTS workers")

            audio_data = await call_gpt_sovits(
                worker, request.input, voice_config, text_lang
            )
            
            content_type = {
                "mp3": "audio/mpeg",
                "wav": "audio/wav",
                "opus": "audio/opus",
                "aac": "audio/aac",
                "flac": "audio/flac",
                "pcm": "audio/pcm"
            }.get(request.response_format, "audio/mpeg")
            
            return StreamingResponse(
                iter([audio_data]),
                media_type=content_type,
                headers={"Content-Disposition": f"attachment; filename=speech.{request.response_format}"}
            )
        
        elif voice_type == "rvc_pipeline":
            base_voice_id = voice_config.get("base_tts_voice", "default")
            base_voice = registry.get_voice(base_voice_id)
            if not base_voice:
                raise HTTPException(
                    status_code=404,
                    detail=f"Base TTS voice '{base_voice_id}' not found"
                )

            base_gpt_weights = base_voice.get("gpt_weights", "")
            base_sovits_weights = base_voice.get("sovits_weights", "")
            base_model_id = f"{base_gpt_weights}:{base_sovits_weights}" if (base_gpt_weights or base_sovits_weights) else None

            tts_worker = worker_pool.get_gpt_sovits_worker(base_model_id)
            if not tts_worker:
                raise HTTPException(status_code=503, detail="No available TTS workers")

            dry_audio = await call_gpt_sovits(
                tts_worker, request.input, base_voice, text_lang
            )

            rvc_worker = worker_pool.get_rvc_worker()
            if not rvc_worker:
                raise HTTPException(status_code=503, detail="No available RVC workers")

            rvc_config = {
                "rvc_model_name": voice_config.get("rvc_model_name", ""),
                "pitch": voice_config.get("pitch", 0),
                "f0_method": voice_config.get("f0_method", "rmvpe"),
                "index_rate": voice_config.get("index_rate", 0.75),
                "filter_radius": voice_config.get("filter_radius", 3),
                "resample_sr": voice_config.get("resample_sr", 0),
                "rms_mix_rate": voice_config.get("rms_mix_rate", 0.25),
                "protect": voice_config.get("protect", 0.33),
            }

            converted_audio = await call_rvc(rvc_worker, dry_audio, rvc_config)
            
            return StreamingResponse(
                iter([converted_audio]),
                media_type="audio/wav",
                headers={"Content-Disposition": "attachment; filename=speech.wav"}
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown voice type: {voice_type}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS processing failed: {str(e)}")


@app.get("/v1/voices")
async def list_voices(authorization: Optional[str] = Header(None)):
    if not await registry.validate_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    
    return {
        "object": "list",
        "data": registry.list_voices()
    }


@app.get("/health")
async def health_check():
    gpt_healthy = sum(1 for w in worker_pool.gpt_sovits_workers if w.healthy)
    rvc_healthy = sum(1 for w in worker_pool.rvc_workers if w.healthy)
    
    return {
        "status": "healthy" if gpt_healthy > 0 else "degraded",
        "version": "1.0.0",
        "workers": {
            "gpt_sovits": {"healthy": gpt_healthy, "total": len(GPT_SOVITS_PORTS)},
            "rvc": {"healthy": rvc_healthy, "total": len(RVC_PORTS)}
        },
        "voices_loaded": len(registry.voices),
        "api_keys_active": sum(1 for k in registry.api_keys.values() if k.active)
    }


@app.get("/")
async def root():
    return {
        "name": "Voice AI Platform API",
        "version": "1.0.0",
        "description": "OpenAI-compatible TTS API with GPT-SoVITS and RVC support",
        "endpoints": {
            "speech": "/v1/audio/speech",
            "voices": "/v1/voices",
            "health": "/health"
        },
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
