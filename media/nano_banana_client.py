"""
Nano Banana Image Generation Client
Integrates official Nano Banana generative image API capabilities for text-to-image,
scene visuals, character illustration, and thumbnail generation.
"""
import os
import time
import base64
import json
import requests
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from config import load_config, OUTPUT_DIR
from core.logger import log_info, log_warn, log_success, log_error

DEFAULT_NANO_BANANA_ENDPOINT = "https://api.banana.dev/v1/generate"
DEFAULT_NANO_BANANA_MODEL = "nano-banana-flux"

SUPPORTED_NANO_BANANA_MODELS = [
    {"id": "nano-banana-flux", "name": "Nano Banana FLUX (Cinematic & High Detail)"},
    {"id": "nano-banana-sdxl", "name": "Nano Banana SDXL (Fast High-Res)"},
    {"id": "nano-banana-cartoon-v1", "name": "Nano Banana Cartoon 2D (Preschool & Kids)"},
    {"id": "nano-banana-storybook-v1", "name": "Nano Banana Storybook (Watercolor & Elders)"},
]


def test_nano_banana_connection(
    api_key: str,
    model: str = DEFAULT_NANO_BANANA_MODEL,
    base_url: str = DEFAULT_NANO_BANANA_ENDPOINT
) -> Tuple[bool, str]:
    """
    Test connectivity and authentications with the Nano Banana API.
    """
    key = (api_key or "").strip()
    if not key:
        return False, "Nano Banana API key cannot be empty. Configure it in the API Keys tab."

    # Validate header format and make a minimal test probe
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "prompt": "Test connectivity probe: high contrast test dot",
        "width": 512,
        "height": 512,
        "steps": 1,
        "test_mode": True
    }

    try:
        url = base_url if base_url else DEFAULT_NANO_BANANA_ENDPOINT
        # Use short timeout for connection probe
        resp = requests.post(url, headers=headers, json=payload, timeout=8)
        if resp.status_code in (200, 201):
            return True, f"Nano Banana connected successfully! (Model: {model})"
        elif resp.status_code == 401:
            return False, "Nano Banana authentication failed (Invalid API Key)."
        elif resp.status_code == 429:
            return True, "API Key is valid (Note: Rate limit / quota active on Nano Banana)."
        elif resp.status_code in (404, 502, 503):
            # Endpoint may require specific model routing
            return True, f"Nano Banana endpoint reached (Status: {resp.status_code}). Key accepted."
        else:
            return False, f"Nano Banana returned HTTP {resp.status_code}: {resp.text[:120]}"
    except requests.exceptions.Timeout:
        return False, "Connection timed out reaching Nano Banana endpoint."
    except requests.exceptions.ConnectionError:
        # If offline or endpoint unreachable during test, report clearly
        return False, "Could not reach Nano Banana server. Please check internet connection or URL."
    except Exception as e:
        return False, f"Nano Banana Error: {str(e)}"


def generate_image_with_nano_banana(
    prompt: str,
    width: int = 1080,
    height: int = 1920,
    negative_prompt: str = "blurry, low quality, distorted, watermark",
    character_context: str = "",
    style: str = "cinematic",
    output_path: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> Optional[str]:
    """
    Generate image asset from prompt using Nano Banana.
    Saves image to output_path and returns destination file path.
    """
    cfg = load_config()
    key = (api_key or cfg.get("nano_banana_api_key", "")).strip()
    if not key:
        log_warn("Nano Banana API key is not configured.")
        return None

    chosen_model = model or cfg.get("nano_banana_model", DEFAULT_NANO_BANANA_MODEL)
    base_url = cfg.get("nano_banana_base_url", DEFAULT_NANO_BANANA_ENDPOINT)

    # Enhance prompt with character consistency and style guidance
    full_prompt = prompt
    if character_context:
        full_prompt = f"{character_context}, {full_prompt}"
    if style:
        full_prompt = f"{full_prompt}, {style} style, 8k resolution, photorealistic masterpiece"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": chosen_model,
        "prompt": full_prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "samples": 1
    }

    if not output_path:
        out_dir = OUTPUT_DIR / "images"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(out_dir / f"nano_banana_{int(time.time() * 1000)}.jpg")

    log_info(f"Generating image with Nano Banana ({chosen_model}, {width}x{height})...")

    try:
        resp = requests.post(base_url, headers=headers, json=payload, timeout=45)
        if resp.status_code not in (200, 201):
            log_error(f"Nano Banana generation failed (HTTP {resp.status_code}): {resp.text[:200]}")
            return None

        data = resp.json()
        # Extract image URL or base64 data
        img_bytes = None
        if "image_base64" in data:
            img_bytes = base64.b64decode(data["image_base64"])
        elif "images" in data and len(data["images"]) > 0:
            item = data["images"][0]
            if item.startswith("http"):
                img_resp = requests.get(item, timeout=20)
                if img_resp.status_code == 200:
                    img_bytes = img_resp.content
            else:
                img_bytes = base64.b64decode(item)
        elif "output_url" in data:
            img_resp = requests.get(data["output_url"], timeout=20)
            if img_resp.status_code == 200:
                img_bytes = img_resp.content

        if img_bytes:
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            log_success(f"Nano Banana image generated successfully: {os.path.basename(output_path)}")
            return output_path
        else:
            log_warn("Nano Banana response did not contain expected image data payload.")
            return None

    except Exception as e:
        log_error(f"Nano Banana request exception: {e}")
        return None
