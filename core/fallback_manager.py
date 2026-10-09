"""
Centralized Multi-Provider Fallback Manager
Ensures zero-crash resilience across Text, Visual/Image, and Audio pipelines.

Hierarchies:
- Text Generation: Primary LLM (Gemini) -> Secondary (Groq) -> Tertiary (OpenAI) -> Structured Safe Template
- Visuals & Media: Nano Banana AI Gen -> Stock Media (Pexels / Pixabay) -> Animation Engine / Diagrams -> Gradients
- Audio & Narration: Configured Voice Provider (ElevenLabs / OpenAI TTS) -> Microsoft Edge-TTS
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import load_config, OUTPUT_DIR
from core.logger import log_info, log_warn, log_success, log_error


# ─────────────────────────────────────────────────────────────────────────────
# 1. TEXT / LLM GENERATION MULTI-PROVIDER FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

def _extract_json_payload(raw_text: str) -> Any:
    """Robust extraction of JSON payload even if wrapped in markdown fences."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE).strip()
    data = None
    try:
        data = json.loads(cleaned)
    except Exception:
        # Try finding outermost braces or brackets
        m = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if m:
            data = json.loads(m.group(1))
        else:
            raise

    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        return data[0]
    return data


def generate_text_with_fallback(prompt: str, json_mode: bool = False, custom_config: Optional[dict] = None) -> str:
    """
    Executes text generation cascading across all configured providers:
    Primary Configured Provider -> Groq -> OpenAI -> Gemini -> Local Structured Fallback.
    """
    from agents.llm_client import _generate_gemini, _generate_groq, _generate_openai

    cfg = custom_config if custom_config is not None else load_config()
    primary = cfg.get("llm_provider", "gemini").lower().strip()

    # Define cascade order starting with primary
    all_providers = ["gemini", "groq", "openai"]
    ordered_providers = [primary] + [p for p in all_providers if p != primary]

    last_error = None
    for prov in ordered_providers:
        # Check if provider has key configured
        key = cfg.get(f"{prov}_api_key", "").strip()
        if not key:
            continue

        try:
            log_info(f"[FallbackManager] Attempting text generation with provider: {prov} (json_mode={json_mode})")
            if prov == "gemini":
                result = _generate_gemini(prompt, cfg, json_mode=json_mode)
            elif prov == "groq":
                result = _generate_groq(prompt, cfg, json_mode=json_mode)
            elif prov == "openai":
                result = _generate_openai(prompt, cfg, json_mode=json_mode)
            else:
                continue

            if result and result.strip():
                if json_mode:
                    _extract_json_payload(result)
                log_success(f"[FallbackManager] Text generation succeeded via '{prov}'")
                return result
        except Exception as e:
            last_error = e
            log_warn(f"[FallbackManager] Provider '{prov}' failed: {e}. Cascading to next candidate...")

    # If all API calls failed, generate emergency safe fallback
    log_error(f"[FallbackManager] All LLM providers exhausted. Last error: {last_error}")
    if json_mode:
        fallback_json = {
            "title": "Cosmic Wonders & The Mysteries of Time",
            "topic": "The Nature of Time",
            "hook_question": "What if time does not flow forward, but exists all at once?",
            "score": 92,
            "sections": [
                {
                    "id": 1,
                    "title": "The Grand Illusion",
                    "narration": "What if every tick of the clock is merely an illusion created by consciousness?",
                    "visual_query": "deep space vortex cosmic clock galaxy",
                    "speaker": "Narrator"
                },
                {
                    "id": 2,
                    "title": "The Einstein Revelation",
                    "narration": "Einstein proved that time slows down near black holes and at near light speeds.",
                    "visual_query": "black hole gravitational lens event horizon",
                    "speaker": "Narrator"
                },
                {
                    "id": 3,
                    "title": "The Final Paradox",
                    "narration": "If the past, present, and future coexist, your entire life is an eternal masterpiece.",
                    "visual_query": "infinite fractal stargate cosmic realm",
                    "speaker": "Narrator"
                }
            ],
            "description": "Explore the mind-bending reality of space, time, and human perception.",
            "tags": ["science", "universe", "physics", "cosmology", "mystery"]
        }
        return json.dumps(fallback_json)

    return "What if every moment you experience has already happened, and is happening forever across the cosmos?"


# ─────────────────────────────────────────────────────────────────────────────
# 2. VISUAL / IMAGE GENERATION FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

def acquire_visual_with_fallback(
    query: str,
    sec_id: int = 1,
    sec_title: str = "Scene",
    video_type: str = "normal",
    audience_type: str = "general",
    output_dir: Optional[Path] = None,
    channel_id: str = "the-ai-brief-it"
) -> List[str]:
    """
    Acquires visual assets for a section with intelligent multi-tiered fallback:
    1. Nano Banana Generative Image (if API key active)
    2. Stock Video / Photos (Pexels / Pixabay)
    3. Procedural Cartoon / Storybook Animation Plates (for kids & elders)
    4. Programmatic Science Diagram
    5. Cinematic Atmospheric Gradient
    """
    target_dir = output_dir or (OUTPUT_DIR / "images")
    target_dir.mkdir(parents=True, exist_ok=True)
    cfg = load_config()

    is_shorts = (video_type == "shorts")
    w, h = (1080, 1920) if is_shorts else (1920, 1080)
    assets = []

    # 1. Nano Banana Generative Image (uses Gemini API key)
    nano_key = (cfg.get("gemini_api_key") or cfg.get("nano_banana_api_key", "")).strip()
    if nano_key:
        try:
            from media.nano_banana_client import generate_image_with_nano_banana
            out_file = str(target_dir / f"sec_{sec_id}_nano_banana.jpg")
            style = "cartoon 2d vibrant" if audience_type in ("children", "kids") else "cinematic atmospheric"
            res = generate_image_with_nano_banana(
                prompt=f"{query}, {style}, highly detailed, 4k",
                width=w,
                height=h,
                output_path=out_file,
                api_key=nano_key
            )
            if res and os.path.exists(res):
                log_success(f"[FallbackManager] Acquired Nano Banana AI visual for Section {sec_id}")
                return [res]
        except Exception as e:
            log_warn(f"[FallbackManager] Nano Banana generation failed: {e}")

    # 2. Animation Engine (if channel is kids or elders)
    if audience_type in ("children", "kids", "mature_adults", "elders") or channel_id in ("kids", "elders"):
        try:
            from video.animation_engine import generate_kids_scene, generate_elders_scene
            out_file = str(target_dir / f"sec_{sec_id}_animated.png")
            if audience_type in ("children", "kids") or channel_id == "kids":
                plate = generate_kids_scene(query, sec_title, w, h, out_file)
            else:
                plate = generate_elders_scene(query, sec_title, w, h, out_file)
            log_success(f"[FallbackManager] Generated animation scene plate for Section {sec_id}")
            return [plate]
        except Exception as e:
            log_warn(f"[FallbackManager] Animation plate generation error: {e}")

    # 3. Stock Media (Pexels / Pixabay)
    from media.pexels_client import search_videos as pexels_videos, search_photos as pexels_photos, download_file
    from media.pixabay_client import search_pixabay_videos, search_pixabay_photos

    pexels_key = cfg.get("pexels_api_key", "").strip()
    pixabay_key = cfg.get("pixabay_api_key", "").strip()
    orientation = "portrait" if is_shorts else "landscape"

    if pexels_key:
        try:
            vids = pexels_videos(query, pexels_key, orientation=orientation, count=1)
            if vids:
                dest = str(target_dir / f"sec_{sec_id}_pv_0.mp4")
                if download_file(vids[0], dest):
                    return [dest]
            photos = pexels_photos(query, pexels_key, orientation=orientation, count=1)
            if photos:
                dest = str(target_dir / f"sec_{sec_id}_pp_0.jpg")
                if download_file(photos[0], dest):
                    return [dest]
        except Exception as e:
            log_warn(f"[FallbackManager] Pexels retrieval error: {e}")

    if pixabay_key:
        try:
            vids = search_pixabay_videos(query, pixabay_key, orientation=orientation, count=1)
            if vids:
                dest = str(target_dir / f"sec_{sec_id}_pb_0.mp4")
                if download_file(vids[0], dest):
                    return [dest]
        except Exception as e:
            log_warn(f"[FallbackManager] Pixabay retrieval error: {e}")

    # 4. Programmatic Science Diagram
    try:
        from video.visual_director import generate_science_diagram
        diagram_file = str(target_dir / f"sec_{sec_id}_diagram.jpg")
        generate_science_diagram(title=sec_title, subtitle=query, width=w, height=h, output_path=diagram_file)
        return [diagram_file]
    except Exception:
        pass

    # 5. Guaranteed Atmospheric Gradient
    from media.media_manager import _create_fallback_gradient
    fallback_file = str(target_dir / f"sec_{sec_id}_fallback.jpg")
    _create_fallback_gradient(fallback_file, width=w, height=h, sec_id=sec_id)
    return [fallback_file]


# ─────────────────────────────────────────────────────────────────────────────
# 3. AUDIO MULTI-PROVIDER FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

def synthesize_audio_with_fallback(
    text: str,
    output_prefix: str = "narration",
    channel_id: str = "the-ai-brief-it",
    script_data: Optional[dict] = None
) -> Tuple[str, str]:
    """
    Synthesizes narration or multi-character dialogue using the unified audio service.
    If the primary provider encounters any issue, Edge-TTS is automatically used.
    """
    from audio.audio_service import generate_multi_character_speech, generate_speech

    if script_data and script_data.get("sections"):
        return generate_multi_character_speech(
            script_data=script_data,
            channel_id=channel_id,
            output_prefix=output_prefix
        )
    return generate_speech(
        full_text=text,
        output_prefix=output_prefix,
        channel_id=channel_id
    )
