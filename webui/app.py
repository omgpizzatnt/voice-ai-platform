import os
import sys
import uuid
import hashlib
import shutil
import gradio as gr
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, '/workspace/gateway')
from yaml_utils import AtomicYAML

VOICES_CONFIG_PATH = "/workspace/gateway/voices.yaml"
API_KEYS_PATH = "/workspace/gateway/api_keys.yaml"
MODELS_DIR = "/workspace/models"
CUSTOM_VOICES_DIR = f"{MODELS_DIR}/custom_voices"
GPTSOVITS_MODELS_DIR = f"{CUSTOM_VOICES_DIR}/gptsovits"
RVC_MODELS_DIR = f"{CUSTOM_VOICES_DIR}/rvc"

WEBUI_USER = os.getenv("WEBUI_USER", "admin")
WEBUI_PASS = os.getenv("WEBUI_PASS", "admin")


def load_voices_config() -> Dict:
    data = AtomicYAML.load(VOICES_CONFIG_PATH)
    if data is None:
        return {"voices": {}}
    return data


def save_voices_config(config: Dict):
    AtomicYAML.save(VOICES_CONFIG_PATH, config)


def load_api_keys() -> Dict:
    data = AtomicYAML.load(API_KEYS_PATH)
    if data is None:
        return {"api_keys": {}}
    return data


def save_api_keys(config: Dict):
    AtomicYAML.save(API_KEYS_PATH, config)


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
            lines.append(f"  - Version: {vinfo.get('version', 'v2')}")
            has_custom_model = vinfo.get('gpt_weights') or vinfo.get('sovits_weights')
            lines.append(f"  - Custom Model: {'Yes' if has_custom_model else 'No (use default)'}")
            lines.append(f"  - Ref: {vinfo.get('refer_wav_path', 'N/A')}\\n")

    return "\\n".join(lines)


def register_tts_voice(
    voice_id: str,
    name: str,
    version: str,
    gpt_weights: str,
    sovits_weights: str,
    refer_wav_path: str,
    prompt_text: str,
    prompt_lang: str,
    language: str,
    top_k: int,
    top_p: float,
    temperature: float,
    speed: float,
    text_split_method: str,
    batch_size: int,
    sample_steps: int
):
    if not voice_id or not refer_wav_path:
        return "Error: Voice ID and Reference WAV path are required.", refresh_voices_list()

    config = load_voices_config()

    config["voices"][voice_id] = {
        "name": name or voice_id,
        "type": "tts",
        "version": version,
        "gpt_weights": gpt_weights,
        "sovits_weights": sovits_weights,
        "refer_wav_path": refer_wav_path,
        "prompt_text": prompt_text,
        "prompt_lang": prompt_lang,
        "language": language,
        "top_k": top_k,
        "top_p": top_p,
        "temperature": temperature,
        "speed": speed,
        "text_split_method": text_split_method,
        "batch_size": batch_size,
        "sample_steps": sample_steps
    }

    save_voices_config(config)
    return f"Voice '{voice_id}' registered successfully!", refresh_voices_list()


def delete_voice(voice_id: str):
    if not voice_id:
        return "Error: Voice ID required.", refresh_voices_list()

    config = load_voices_config()
    voices = config.get("voices", {})

    if voice_id in voices:
        voice_type = voices[voice_id].get("type", "tts")
        del voices[voice_id]
        save_voices_config(config)

        if voice_type == "rvc_pipeline":
            return f"Pipeline '{voice_id}' deleted.", refresh_pipelines_list()
        else:
            return f"Voice '{voice_id}' deleted.", refresh_voices_list()

    return f"Voice/Pipeline '{voice_id}' not found.", refresh_voices_list()


def fill_tts_paths_from_model(selected_model):
    if not selected_model:
        return "", "", ""
    base_path = f"/workspace/models/custom_voices/gptsovits/{selected_model}"
    gpt_path = f"{base_path}/{selected_model}_gpt.ckpt"
    sovits_path = f"{base_path}/{selected_model}_sovits.pth"
    ref_path = f"{base_path}/reference.wav"
    return gpt_path, sovits_path, ref_path


def create_tts_tab():
    with gr.Tab("TTS Voice Registration"):
        gr.Markdown("### Register GPT-SoVITS TTS Voices")

        with gr.Row():
            with gr.Column(scale=1):
                voice_id = gr.Textbox(label="Voice ID", placeholder="e.g., xiaoming")
                name = gr.Textbox(label="Display Name", placeholder="e.g., 小明")
                version = gr.Dropdown(
                    label="Model Version",
                    choices=["v1", "v2", "v2Pro", "v2ProPlus", "v3", "v4"],
                    value="v2"
                )

                gr.Markdown("#### Select from Uploaded Models")
                tts_model_dropdown = gr.Dropdown(
                    label="Select Model (Auto-fill paths)",
                    choices=get_gptsovits_model_choices(),
                    value=None
                )

                gpt_weights = gr.Textbox(
                    label="GPT Weights Path (Optional)",
                    placeholder="/workspace/models/custom_voices/gptsovits/<voice_id>/xxx.ckpt"
                )
                sovits_weights = gr.Textbox(
                    label="SoVITS Weights Path (Optional)",
                    placeholder="/workspace/models/custom_voices/gptsovits/<voice_id>/xxx.pth"
                )
                refer_wav_path = gr.Textbox(
                    label="Reference WAV Path *",
                    placeholder="/workspace/models/custom_voices/gptsovits/<voice_id>/reference.wav"
                )

            with gr.Column(scale=1):
                prompt_text = gr.Textbox(
                    label="Prompt Text",
                    placeholder="Reference audio transcription",
                    lines=2
                )
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
                speed = gr.Slider(label="Speed", minimum=0.25, maximum=4.0, value=1.0)

        with gr.Accordion("Advanced Settings", open=False):
            with gr.Row():
                with gr.Column(scale=1):
                    top_k = gr.Slider(label="Top K", minimum=1, maximum=100, value=20)
                    top_p = gr.Slider(label="Top P", minimum=0.0, maximum=1.0, value=0.6)
                    temperature = gr.Slider(label="Temperature", minimum=0.0, maximum=1.0, value=0.6)
                with gr.Column(scale=1):
                    text_split_method = gr.Dropdown(
                        label="Text Split Method",
                        choices=["cut0", "cut1", "cut2", "cut3", "cut4", "cut5"],
                        value="cut5"
                    )
                    batch_size = gr.Slider(label="Batch Size", minimum=1, maximum=10, value=1, step=1)
                    sample_steps = gr.Slider(label="Sample Steps (V3/V4)", minimum=4, maximum=128, value=32, step=1)

        with gr.Row():
            register_btn = gr.Button("Register Voice", variant="primary")
            delete_btn = gr.Button("Delete Voice", variant="stop")

        status = gr.Textbox(label="Status", interactive=False)
        voices_list = gr.Markdown(label="Registered Voices")

        tts_model_dropdown.change(
            fill_tts_paths_from_model,
            inputs=[tts_model_dropdown],
            outputs=[gpt_weights, sovits_weights, refer_wav_path]
        )

        register_btn.click(
            register_tts_voice,
            inputs=[voice_id, name, version, gpt_weights, sovits_weights, refer_wav_path,
                   prompt_text, prompt_lang, language, top_k, top_p, temperature, speed,
                   text_split_method, batch_size, sample_steps],
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
            lines.append(f"  - RVC Model: {vinfo.get('rvc_model_name', 'N/A')}")
            lines.append(f"  - Pitch: {vinfo.get('pitch', 0)}, F0: {vinfo.get('f0_method', 'rmvpe')}")
            lines.append(f"  - Index Rate: {vinfo.get('index_rate', 0.75)}\\n")

    return "\\n".join(lines)


def register_rvc_pipeline(
    pipeline_id: str,
    name: str,
    base_tts_voice: str,
    rvc_model_name: str,
    pitch: int,
    f0_method: str,
    index_rate: float,
    filter_radius: int,
    resample_sr: int,
    rms_mix_rate: float,
    protect: float
):
    if not pipeline_id or not base_tts_voice:
        return "Error: Pipeline ID and Base TTS Voice are required.", refresh_pipelines_list()

    if not rvc_model_name:
        return "Error: RVC Model Name is required.", refresh_pipelines_list()

    config = load_voices_config()

    config["voices"][pipeline_id] = {
        "name": name or pipeline_id,
        "type": "rvc_pipeline",
        "base_tts_voice": base_tts_voice,
        "rvc_model_name": rvc_model_name,
        "pitch": pitch,
        "f0_method": f0_method,
        "index_rate": index_rate,
        "filter_radius": filter_radius,
        "resample_sr": resample_sr,
        "rms_mix_rate": rms_mix_rate,
        "protect": protect
    }

    save_voices_config(config)
    return f"Pipeline '{pipeline_id}' registered successfully!", refresh_pipelines_list()


def fill_rvc_model_name(selected_model):
    return selected_model if selected_model else ""


def create_rvc_tab():
    with gr.Tab("RVC Pipeline Config"):
        gr.Markdown("### Configure TTS+RVC Voice Conversion Pipelines")
        gr.Markdown("Models should be in /workspace/models/custom_voices/rvc/<model_name>/")

        with gr.Row():
            with gr.Column(scale=1):
                pipeline_id = gr.Textbox(label="Pipeline ID", placeholder="e.g., anime_girl")
                name = gr.Textbox(label="Display Name", placeholder="e.g., Anime Girl Voice")
                base_tts_voice = gr.Textbox(
                    label="Base TTS Voice ID *",
                    placeholder="Voice ID for generating dry audio"
                )

                gr.Markdown("#### Select from Uploaded Models")
                rvc_model_dropdown = gr.Dropdown(
                    label="Select RVC Model",
                    choices=get_rvc_model_choices(),
                    value=None
                )

                rvc_model_name = gr.Textbox(
                    label="RVC Model Name *",
                    placeholder="Folder name in /workspace/models/custom_voices/rvc/"
                )

            with gr.Column(scale=1):
                pitch = gr.Slider(label="Pitch Shift", minimum=-24, maximum=24, value=6, step=1)
                f0_method = gr.Dropdown(
                    label="F0 Method",
                    choices=["rmvpe", "crepe", "harvest", "pm"],
                    value="rmvpe"
                )
                index_rate = gr.Slider(label="Index Rate", minimum=0.0, maximum=1.0, value=0.75)

        with gr.Accordion("Advanced Settings", open=False):
            with gr.Row():
                with gr.Column(scale=1):
                    filter_radius = gr.Slider(label="Filter Radius", minimum=0, maximum=10, value=3, step=1)
                    rms_mix_rate = gr.Slider(label="RMS Mix Rate", minimum=0.0, maximum=1.0, value=0.25)
                with gr.Column(scale=1):
                    resample_sr = gr.Slider(label="Resample SR (0=disable)", minimum=0, maximum=48000, value=0, step=1000)
                    protect = gr.Slider(label="Protect", minimum=0.0, maximum=0.5, value=0.33)

        with gr.Row():
            register_btn = gr.Button("Register Pipeline", variant="primary")
            delete_btn = gr.Button("Delete Pipeline", variant="stop")

        status = gr.Textbox(label="Status", interactive=False)
        pipelines_list = gr.Markdown(label="Configured Pipelines")

        rvc_model_dropdown.change(
            fill_rvc_model_name,
            inputs=[rvc_model_dropdown],
            outputs=[rvc_model_name]
        )

        register_btn.click(
            register_rvc_pipeline,
            inputs=[pipeline_id, name, base_tts_voice, rvc_model_name, pitch, f0_method, index_rate,
                   filter_radius, resample_sr, rms_mix_rate, protect],
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
        status = "[Active]" if key_info.get("active", True) else "[Revoked]"
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
    
    return f"New API Key Generated (copy it now):\\n\\n`{new_key}`", refresh_api_keys_list()


def revoke_key(key_hash_prefix: str):
    if not key_hash_prefix or len(key_hash_prefix) < 4:
        return "Error: Please provide at least first 4 characters of the key hash.", refresh_api_keys_list()
    
    config = load_api_keys()
    keys = config.get("api_keys", {})
    
    matching = [k for k in keys.keys() if k.startswith(key_hash_prefix)]
    if not matching:
        return f"No key found starting with '{key_hash_prefix}'", refresh_api_keys_list()
    
    if len(matching) > 1:
        return f"Multiple keys match '{key_hash_prefix}'. Please provide more characters.", refresh_api_keys_list()
    
    key_hash = matching[0]
    keys[key_hash]["active"] = False
    save_api_keys(config)
    
    return f"Key {key_hash[:8]}... has been revoked.", refresh_api_keys_list()


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


def list_gptsovits_models() -> List[Tuple[str, str, str]]:
    models = []
    if not os.path.exists(GPTSOVITS_MODELS_DIR):
        return models
    
    for model_name in sorted(os.listdir(GPTSOVITS_MODELS_DIR)):
        model_path = os.path.join(GPTSOVITS_MODELS_DIR, model_name)
        if not os.path.isdir(model_path):
            continue
        
        files = os.listdir(model_path)
        has_gpt = any(f.endswith('.ckpt') for f in files)
        has_sovits = any(f.endswith('.pth') for f in files)
        has_ref = any(f.endswith('.wav') for f in files)
        
        status = []
        if has_gpt:
            status.append("GPT")
        if has_sovits:
            status.append("SoVITS")
        if has_ref:
            status.append("Ref")
        
        models.append((model_name, ", ".join(status) if status else "Empty", model_path))
    
    return models


def list_rvc_models() -> List[Tuple[str, str, str]]:
    models = []
    if not os.path.exists(RVC_MODELS_DIR):
        return models
    
    for model_name in sorted(os.listdir(RVC_MODELS_DIR)):
        model_path = os.path.join(RVC_MODELS_DIR, model_name)
        if not os.path.isdir(model_path):
            continue
        
        files = os.listdir(model_path)
        has_pth = any(f.endswith('.pth') for f in files)
        has_index = any(f.endswith('.index') for f in files)
        
        status = []
        if has_pth:
            status.append("Model")
        if has_index:
            status.append("Index")
        
        models.append((model_name, ", ".join(status) if status else "Empty", model_path))
    
    return models


def refresh_gptsovits_models_list() -> str:
    models = list_gptsovits_models()
    if not models:
        return "No GPT-SoVITS models uploaded yet."
    
    lines = ["### Uploaded GPT-SoVITS Models\\n"]
    for name, status, path in models:
        lines.append(f"**{name}** ({status})")
        lines.append(f"  Path: `{path}`\\n")
    
    return "\\n".join(lines)


def refresh_rvc_models_list() -> str:
    models = list_rvc_models()
    if not models:
        return "No RVC models uploaded yet."
    
    lines = ["### Uploaded RVC Models\\n"]
    for name, status, path in models:
        lines.append(f"**{name}** ({status})")
        lines.append(f"  Path: `{path}`\\n")
    
    return "\\n".join(lines)


def upload_gptsovits_model(
    model_name: str,
    gpt_file,
    sovits_file,
    ref_audio_file
):
    if not model_name:
        return "Error: Model name is required.", refresh_gptsovits_models_list()

    if not model_name.replace("_", "").replace("-", "").isalnum():
        return "Error: Model name should only contain letters, numbers, underscore and hyphen.", refresh_gptsovits_models_list()
    
    model_dir = os.path.join(GPTSOVITS_MODELS_DIR, model_name)
    os.makedirs(model_dir, exist_ok=True)
    
    uploaded = []
    
    if gpt_file is not None:
        if hasattr(gpt_file, 'name'):
            dest_path = os.path.join(model_dir, os.path.basename(gpt_file.name))
            shutil.copy(gpt_file.name, dest_path)
            uploaded.append("GPT weights")
    
    if sovits_file is not None:
        if hasattr(sovits_file, 'name'):
            dest_path = os.path.join(model_dir, os.path.basename(sovits_file.name))
            shutil.copy(sovits_file.name, dest_path)
            uploaded.append("SoVITS weights")
    
    if ref_audio_file is not None:
        if hasattr(ref_audio_file, 'name'):
            dest_path = os.path.join(model_dir, "reference.wav")
            shutil.copy(ref_audio_file.name, dest_path)
            uploaded.append("Reference audio")
    
    if uploaded:
        return f"Successfully uploaded: {', '.join(uploaded)} to '{model_name}'", refresh_gptsovits_models_list()
    else:
        return "No files uploaded. Please select at least one file.", refresh_gptsovits_models_list()


def upload_rvc_model(
    model_name: str,
    pth_file,
    index_file
):
    if not model_name:
        return "Error: Model name is required.", refresh_rvc_models_list()

    if not model_name.replace("_", "").replace("-", "").isalnum():
        return "Error: Model name should only contain letters, numbers, underscore and hyphen.", refresh_rvc_models_list()
    
    model_dir = os.path.join(RVC_MODELS_DIR, model_name)
    os.makedirs(model_dir, exist_ok=True)
    
    uploaded = []
    
    if pth_file is not None:
        if hasattr(pth_file, 'name'):
            dest_path = os.path.join(model_dir, os.path.basename(pth_file.name))
            shutil.copy(pth_file.name, dest_path)
            uploaded.append("Model weights (.pth)")
    
    if index_file is not None:
        if hasattr(index_file, 'name'):
            dest_path = os.path.join(model_dir, os.path.basename(index_file.name))
            shutil.copy(index_file.name, dest_path)
            uploaded.append("Index file (.index)")
    
    if uploaded:
        return f"Successfully uploaded: {', '.join(uploaded)} to '{model_name}'", refresh_rvc_models_list()
    else:
        return "No files uploaded. Please select at least one file.", refresh_rvc_models_list()


def delete_gptsovits_model(model_name: str):
    if not model_name:
        return "Error: Model name is required.", refresh_gptsovits_models_list()
    
    model_dir = os.path.join(GPTSOVITS_MODELS_DIR, model_name)
    if not os.path.exists(model_dir):
        return f"Error: Model '{model_name}' not found.", refresh_gptsovits_models_list()
    
    try:
        shutil.rmtree(model_dir)
        return f"Model '{model_name}' deleted successfully.", refresh_gptsovits_models_list()
    except Exception as e:
        return f"Error deleting model: {str(e)}", refresh_gptsovits_models_list()


def delete_rvc_model(model_name: str):
    if not model_name:
        return "Error: Model name is required.", refresh_rvc_models_list()
    
    model_dir = os.path.join(RVC_MODELS_DIR, model_name)
    if not os.path.exists(model_dir):
        return f"Error: Model '{model_name}' not found.", refresh_rvc_models_list()
    
    try:
        shutil.rmtree(model_dir)
        return f"Model '{model_name}' deleted successfully.", refresh_rvc_models_list()
    except Exception as e:
        return f"Error deleting model: {str(e)}", refresh_rvc_models_list()


def get_gptsovits_model_choices() -> List[str]:
    models = list_gptsovits_models()
    return [name for name, _, _ in models]


def get_rvc_model_choices() -> List[str]:
    models = list_rvc_models()
    return [name for name, _, _ in models]


def create_model_upload_tab():
    with gr.Tab("Model Upload"):
        gr.Markdown("Upload and Manage Models")
        gr.Markdown("Models will be stored in:")
        gr.Markdown("- GPT-SoVITS: /workspace/models/custom_voices/gptsovits/")
        gr.Markdown("- RVC: /workspace/models/custom_voices/rvc/")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("#### Upload GPT-SoVITS Model")

                gptsovits_model_name = gr.Textbox(
                    label="Model Name",
                    placeholder="e.g., xiaoming"
                )
                gptsovits_gpt_file = gr.File(
                    label="GPT Weights (.ckpt)",
                    file_types=[".ckpt"]
                )
                gptsovits_sovits_file = gr.File(
                    label="SoVITS Weights (.pth)",
                    file_types=[".pth"]
                )
                gptsovits_ref_file = gr.File(
                    label="Reference Audio (.wav)",
                    file_types=[".wav"]
                )

                upload_gptsovits_btn = gr.Button("Upload GPT-SoVITS Model", variant="primary")
                gptsovits_upload_status = gr.Textbox(label="Upload Status", interactive=False)

            with gr.Column(scale=1):
                gr.Markdown("#### Upload RVC Model")

                rvc_model_name = gr.Textbox(
                    label="Model Name",
                    placeholder="e.g., anime_girl"
                )
                rvc_pth_file = gr.File(
                    label="Model Weights (.pth)",
                    file_types=[".pth"]
                )
                rvc_index_file = gr.File(
                    label="Index File (.index)",
                    file_types=[".index"]
                )

                upload_rvc_btn = gr.Button("Upload RVC Model", variant="primary")
                rvc_upload_status = gr.Textbox(label="Upload Status", interactive=False)

        gr.Markdown("---")
        gr.Markdown("### Manage Existing Models")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("#### GPT-SoVITS Models")
                gptsovits_models_list = gr.Markdown()

                with gr.Row():
                    delete_gptsovits_name = gr.Textbox(label="Model to Delete", placeholder="Model name")
                    delete_gptsovits_btn = gr.Button("Delete", variant="stop")

                delete_gptsovits_status = gr.Textbox(label="Delete Status", interactive=False)

            with gr.Column(scale=1):
                gr.Markdown("#### RVC Models")
                rvc_models_list = gr.Markdown()

                with gr.Row():
                    delete_rvc_name = gr.Textbox(label="Model to Delete", placeholder="Model name")
                    delete_rvc_btn = gr.Button("Delete", variant="stop")

                delete_rvc_status = gr.Textbox(label="Delete Status", interactive=False)

        upload_gptsovits_btn.click(
            upload_gptsovits_model,
            inputs=[gptsovits_model_name, gptsovits_gpt_file, gptsovits_sovits_file, gptsovits_ref_file],
            outputs=[gptsovits_upload_status, gptsovits_models_list]
        )

        upload_rvc_btn.click(
            upload_rvc_model,
            inputs=[rvc_model_name, rvc_pth_file, rvc_index_file],
            outputs=[rvc_upload_status, rvc_models_list]
        )

        delete_gptsovits_btn.click(
            delete_gptsovits_model,
            inputs=[delete_gptsovits_name],
            outputs=[delete_gptsovits_status, gptsovits_models_list]
        )

        delete_rvc_btn.click(
            delete_rvc_model,
            inputs=[delete_rvc_name],
            outputs=[delete_rvc_status, rvc_models_list]
        )

        gptsovits_models_list.value = refresh_gptsovits_models_list()
        rvc_models_list.value = refresh_rvc_models_list()


def create_app():
    def auth(username, password):
        return username == WEBUI_USER and password == WEBUI_PASS
    
    with gr.Blocks(title="Voice AI Platform - Model Manager", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # Voice AI Platform - Model Manager
        
        Manage TTS voices, RVC pipelines, and API keys for the Voice AI Gateway.
        """)
        
        create_model_upload_tab()
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
    os.makedirs(GPTSOVITS_MODELS_DIR, exist_ok=True)
    os.makedirs(RVC_MODELS_DIR, exist_ok=True)

    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=8080,
        auth=lambda u, p: u == WEBUI_USER and p == WEBUI_PASS,
        auth_message="Voice AI Platform - Admin Login",
        show_error=True
    )
