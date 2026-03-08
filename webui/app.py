import os
import uuid
import hashlib
import yaml
import gradio as gr
from datetime import datetime
from typing import Dict, List, Optional

VOICES_CONFIG_PATH = "/workspace/gateway/voices.yaml"
API_KEYS_PATH = "/workspace/gateway/api_keys.yaml"
MODELS_DIR = "/workspace/models"
CUSTOM_VOICES_DIR = f"{MODELS_DIR}/custom_voices"
RVC_PIPELINES_DIR = f"{MODELS_DIR}/rvc_pipelines"

WEBUI_USER = os.getenv("WEBUI_USER", "admin")
WEBUI_PASS = os.getenv("WEBUI_PASS", "admin")


def load_voices_config() -> Dict:
    if os.path.exists(VOICES_CONFIG_PATH):
        with open(VOICES_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {"voices": {}}
    return {"voices": {}}


def save_voices_config(config: Dict):
    os.makedirs(os.path.dirname(VOICES_CONFIG_PATH), exist_ok=True)
    with open(VOICES_CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def load_api_keys() -> Dict:
    if os.path.exists(API_KEYS_PATH):
        with open(API_KEYS_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {"api_keys": {}}
    return {"api_keys": {}}


def save_api_keys(config: Dict):
    os.makedirs(os.path.dirname(API_KEYS_PATH), exist_ok=True)
    with open(API_KEYS_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def generate_api_key() -> str:
    return f"sk-{uuid.uuid4().hex}"


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def refresh_voices_list():
    config = load_voices_config()
    voices = config.get("voices", {})
    
    if not voices:
        return "No voices registered yet."
    
    lines = ["### Registered TTS Voices\\n"]
    for vid, vinfo in voices.items():
        if vinfo.get("type") == "tts":
            lines.append(f"**{vid}**: {vinfo.get('name', 'Unnamed')} ({vinfo.get('language', 'auto')})")
            lines.append(f"  - Model: {vinfo.get('model_name', 'default')}")
            lines.append(f"  - Ref: {vinfo.get('refer_wav_path', 'N/A')}\\n")
    
    return "\\n".join(lines)


def register_tts_voice(
    voice_id: str,
    name: str,
    model_name: str,
    refer_wav_path: str,
    prompt_text: str,
    prompt_lang: str,
    language: str,
    top_k: int,
    top_p: float,
    temperature: float,
    speed: float
):
    if not voice_id or not refer_wav_path:
        return "Error: Voice ID and Reference WAV path are required.", refresh_voices_list()
    
    config = load_voices_config()
    
    config["voices"][voice_id] = {
        "name": name or voice_id,
        "type": "tts",
        "model_name": model_name or "default",
        "refer_wav_path": refer_wav_path,
        "prompt_text": prompt_text,
        "prompt_lang": prompt_lang,
        "text_lang": language,
        "top_k": top_k,
        "top_p": top_p,
        "temperature": temperature,
        "speed": speed
    }
    
    save_voices_config(config)
    return f"✅ Voice '{voice_id}' registered successfully!", refresh_voices_list()


def delete_voice(voice_id: str):
    if not voice_id:
        return "Error: Voice ID required.", refresh_voices_list()
    
    config = load_voices_config()
    if voice_id in config.get("voices", {}):
        del config["voices"][voice_id]
        save_voices_config(config)
        return f"✅ Voice '{voice_id}' deleted.", refresh_voices_list()
    return f"❌ Voice '{voice_id}' not found.", refresh_voices_list()


def create_tts_tab():
    with gr.Tab("TTS Voice Registration"):
        gr.Markdown("### Register GPT-SoVITS TTS Voices")
        
        with gr.Row():
            with gr.Column(scale=1):
                voice_id = gr.Textbox(label="Voice ID", placeholder="e.g., xiaoming")
                name = gr.Textbox(label="Display Name", placeholder="e.g., 小明")
                model_name = gr.Textbox(label="Model Name", placeholder="e.g., xiaoming_v1")
                refer_wav_path = gr.Textbox(
                    label="Reference WAV Path", 
                    placeholder="/workspace/models/custom_voices/.../ref.wav"
                )
                prompt_text = gr.Textbox(
                    label="Prompt Text", 
                    placeholder="Reference audio transcription",
                    lines=2
                )
            
            with gr.Column(scale=1):
                prompt_lang = gr.Dropdown(
                    label="Prompt Language",
                    choices=["auto", "zh", "en", "ja", "yue", "ko"],
                    value="zh"
                )
                language = gr.Dropdown(
                    label="Target Language",
                    choices=["auto", "auto_yue", "en", "zh", "ja", "yue", "ko", "all_zh", "all_ja", "all_yue", "all_ko"],
                    value="auto"
                )
                top_k = gr.Slider(label="Top K", minimum=1, maximum=100, value=20)
                top_p = gr.Slider(label="Top P", minimum=0.0, maximum=1.0, value=0.6)
                temperature = gr.Slider(label="Temperature", minimum=0.0, maximum=1.0, value=0.6)
                speed = gr.Slider(label="Speed", minimum=0.25, maximum=4.0, value=1.0)
        
        with gr.Row():
            register_btn = gr.Button("Register Voice", variant="primary")
            delete_btn = gr.Button("Delete Voice", variant="stop")
        
        status = gr.Textbox(label="Status", interactive=False)
        voices_list = gr.Markdown(label="Registered Voices")
        
        register_btn.click(
            register_tts_voice,
            inputs=[voice_id, name, model_name, refer_wav_path, prompt_text, 
                   prompt_lang, language, top_k, top_p, temperature, speed],
            outputs=[status, voices_list]
        )
        
        delete_btn.click(
            delete_voice,
            inputs=[voice_id],
            outputs=[status, voices_list]
        )
        
        voices_list.value = refresh_voices_list()


def refresh_pipelines_list():
    config = load_voices_config()
    voices = config.get("voices", {})
    
    if not voices:
        return "No pipelines configured yet."
    
    lines = ["### Configured RVC Pipelines\\n"]
    for vid, vinfo in voices.items():
        if vinfo.get("type") == "rvc_pipeline":
            lines.append(f"**{vid}**: {vinfo.get('name', 'Unnamed')}")
            lines.append(f"  - Base TTS: {vinfo.get('base_tts_voice', 'default')}")
            lines.append(f"  - Pitch: {vinfo.get('pitch', 0)}")
            lines.append(f"  - RVC Model: {vinfo.get('rvc_model_path', 'N/A')}\\n")
    
    return "\\n".join(lines)


def register_rvc_pipeline(
    pipeline_id: str,
    name: str,
    base_tts_voice: str,
    rvc_model_path: str,
    pitch: int,
    f0_method: str,
    index_rate: float
):
    if not pipeline_id or not base_tts_voice:
        return "Error: Pipeline ID and Base TTS Voice are required.", refresh_pipelines_list()
    
    config = load_voices_config()
    
    config["voices"][pipeline_id] = {
        "name": name or pipeline_id,
        "type": "rvc_pipeline",
        "base_tts_voice": base_tts_voice,
        "rvc_model_path": rvc_model_path,
        "pitch": pitch,
        "f0_method": f0_method,
        "index_rate": index_rate
    }
    
    save_voices_config(config)
    return f"✅ Pipeline '{pipeline_id}' registered successfully!", refresh_pipelines_list()


def create_rvc_tab():
    with gr.Tab("RVC Pipeline Config"):
        gr.Markdown("### Configure TTS+RVC Voice Conversion Pipelines")
        
        with gr.Row():
            with gr.Column(scale=1):
                pipeline_id = gr.Textbox(label="Pipeline ID", placeholder="e.g., anime_girl")
                name = gr.Textbox(label="Display Name", placeholder="e.g., Anime Girl Voice")
                base_tts_voice = gr.Textbox(
                    label="Base TTS Voice ID",
                    placeholder="Voice ID for generating dry audio"
                )
                rvc_model_path = gr.Textbox(
                    label="RVC Model Path",
                    placeholder="/workspace/models/rvc_pipelines/.../"
                )
            
            with gr.Column(scale=1):
                pitch = gr.Slider(label="Pitch Shift", minimum=-24, maximum=24, value=6, step=1)
                f0_method = gr.Dropdown(
                    label="F0 Method",
                    choices=["rmvpe", "pm", "harvest"],
                    value="rmvpe"
                )
                index_rate = gr.Slider(label="Index Rate", minimum=0.0, maximum=1.0, value=0.75)
        
        with gr.Row():
            register_btn = gr.Button("Register Pipeline", variant="primary")
            delete_btn = gr.Button("Delete Pipeline", variant="stop")
        
        status = gr.Textbox(label="Status", interactive=False)
        pipelines_list = gr.Markdown(label="Configured Pipelines")
        
        register_btn.click(
            register_rvc_pipeline,
            inputs=[pipeline_id, name, base_tts_voice, rvc_model_path, pitch, f0_method, index_rate],
            outputs=[status, pipelines_list]
        )
        
        delete_btn.click(
            delete_voice,
            inputs=[pipeline_id],
            outputs=[status, pipelines_list]
        )
        
        pipelines_list.value = refresh_pipelines_list()


def refresh_api_keys_list():
    config = load_api_keys()
    keys = config.get("api_keys", {})
    
    if not keys:
        return "No API keys generated yet."
    
    lines = ["### Active API Keys\\n"]
    for key_hash, key_info in keys.items():
        status = "🟢" if key_info.get("active", True) else "🔴"
        created = key_info.get("created_at", "Unknown")[:10]
        last_used = key_info.get("last_used", "Never")
        if last_used != "Never":
            last_used = last_used[:10]
        lines.append(f"{status} **{key_hash[:8]}...** | Created: {created} | Last Used: {last_used}")
    
    return "\\n".join(lines)


def generate_new_key():
    new_key = generate_api_key()
    key_hash = hash_api_key(new_key)
    
    config = load_api_keys()
    config["api_keys"][key_hash] = {
        "key_hash": key_hash,
        "created_at": datetime.now().isoformat(),
        "last_used": None,
        "active": True
    }
    save_api_keys(config)
    
    return f"✅ New API Key Generated (copy it now):\\n\\n`{new_key}`", refresh_api_keys_list()


def revoke_key(key_hash_prefix: str):
    if not key_hash_prefix or len(key_hash_prefix) < 4:
        return "Error: Please provide at least first 4 characters of the key hash.", refresh_api_keys_list()
    
    config = load_api_keys()
    keys = config.get("api_keys", {})
    
    matching = [k for k in keys.keys() if k.startswith(key_hash_prefix)]
    if not matching:
        return f"❌ No key found starting with '{key_hash_prefix}'", refresh_api_keys_list()
    
    if len(matching) > 1:
        return f"⚠️ Multiple keys match '{key_hash_prefix}'. Please provide more characters.", refresh_api_keys_list()
    
    key_hash = matching[0]
    keys[key_hash]["active"] = False
    save_api_keys(config)
    
    return f"✅ Key {key_hash[:8]}... has been revoked.", refresh_api_keys_list()


def create_api_keys_tab():
    with gr.Tab("API Key Management"):
        gr.Markdown("### Manage API Keys for Gateway Access")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("#### Generate New Key")
                generate_btn = gr.Button("Generate New API Key", variant="primary")
                new_key_output = gr.Textbox(
                    label="New Key (copy immediately!)",
                    interactive=False,
                    lines=3
                )
            
            with gr.Column(scale=1):
                gr.Markdown("#### Revoke Key")
                key_hash_input = gr.Textbox(
                    label="Key Hash (first 8+ chars)",
                    placeholder="e.g., a1b2c3d4"
                )
                revoke_btn = gr.Button("Revoke Key", variant="stop")
                revoke_status = gr.Textbox(label="Status", interactive=False)
        
        gr.Markdown("---")
        gr.Markdown("### Active API Keys")
        keys_list = gr.Markdown(label="API Keys")
        
        generate_btn.click(
            generate_new_key,
            outputs=[new_key_output, keys_list]
        )
        
        revoke_btn.click(
            revoke_key,
            inputs=[key_hash_input],
            outputs=[revoke_status, keys_list]
        )
        
        keys_list.value = refresh_api_keys_list()


def create_app():
    def auth(username, password):
        return username == WEBUI_USER and password == WEBUI_PASS
    
    with gr.Blocks(title="Voice AI Platform - Model Manager", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # Voice AI Platform - Model Manager
        
        Manage TTS voices, RVC pipelines, and API keys for the Voice AI Gateway.
        """)
        
        create_tts_tab()
        create_rvc_tab()
        create_api_keys_tab()
        
        gr.Markdown("""
        ---
        **API Endpoint**: `POST /v1/audio/speech`  
        **Base URL**: `http://localhost/v1`  
        **Usage**: Generate API key above, then use with any OpenAI-compatible client
        """)
    
    return app


if __name__ == "__main__":
    os.makedirs(CUSTOM_VOICES_DIR, exist_ok=True)
    os.makedirs(RVC_PIPELINES_DIR, exist_ok=True)
    
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=8080,
        auth=lambda u, p: u == WEBUI_USER and p == WEBUI_PASS,
        auth_message="Voice AI Platform - Admin Login",
        show_error=True
    )
