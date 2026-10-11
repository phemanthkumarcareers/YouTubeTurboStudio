"""
Unified Media Manager for YouTube Turbo Studio
Coordinates fetching stock images/videos across Pexels, Pixabay, or Local files.
Guarantees visual assets exist for every script section with intelligent fallbacks.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw
from config import load_config, OUTPUT_DIR
from media.pexels_client import search_photos as pexels_photos, search_videos as pexels_videos, download_file
from media.pixabay_client import search_pixabay_photos, search_pixabay_videos
from core.logger import log_info, log_warn, log_success


def _create_fallback_gradient(dest_path: str, width: int = 1920, height: int = 1080, sec_id: int = 1):
    """Generate high-resolution dark atmospheric gradient image as guaranteed fallback."""
    colors = [
        ((15, 23, 42), (88, 28, 135)),    # Slate to Deep Purple
        ((10, 15, 30), (30, 58, 138)),    # Deep Navy to Blue
        ((20, 20, 30), (13, 148, 136)),   # Dark Charcoal to Teal
        ((24, 24, 27), (180, 83, 9)),     # Dark Gray to Amber
        ((17, 24, 39), (190, 24, 93)),    # Deep Space to Rose
    ]
    c1, c2 = colors[(sec_id - 1) % len(colors)]
    img = Image.new("RGB", (width, height), c1)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        factor = y / height
        r = int(c1[0] * (1 - factor) + c2[0] * factor)
        g = int(c1[1] * (1 - factor) + c2[1] * factor)
        b = int(c1[2] * (1 - factor) + c2[2] * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    img.save(dest_path, "JPEG", quality=90)


def fetch_media_for_script(script: dict, video_type: str = "normal") -> dict[int, list[str]]:
    """
    Downloads media for each section of the script.
    Returns: {section_id: [path1, path2, ...]}
    """
    cfg = load_config()
    source = cfg.get("video_source", "pexels_images")
    pexels_key = cfg.get("pexels_api_key", "").strip()
    pixabay_key = cfg.get("pixabay_api_key", "").strip()

    is_shorts = (video_type == "shorts")
    orientation = "portrait" if is_shorts else "landscape"
    target_count = 2 if is_shorts else 1

    img_dir = OUTPUT_DIR / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    result_map = {}
    sections = script.get("sections", [])

    log_info(f"Fetching media assets for {len(sections)} sections (Mode: {source}, Orientation: {orientation})...")

    # Persistent tracking of used media URLs & generated seeds to prevent reuse
    used_history_file = OUTPUT_DIR / ".used_media_registry.json"
    used_items = set()
    if used_history_file.exists():
        try:
            import json
            with open(used_history_file, "r", encoding="utf-8") as uf:
                used_items = set(json.load(uf))
        except Exception:
            used_items = set()

    for sec in sections:
        sec_id = sec.get("id", 1)
        query = sec.get("visual_query", "cinematic nature space")
        sec_paths = []

        log_info(f"   [Section {sec_id}] Searching '{query}'...")

        # 1. Try Pexels (filtering out already used URLs)
        if "pexels" in source and pexels_key:
            if "video" in source:
                urls = pexels_videos(query, pexels_key, orientation=orientation, count=target_count + 4)
            else:
                urls = pexels_photos(query, pexels_key, orientation=orientation, count=target_count + 4)

            # Filter out already used items
            fresh_urls = [u for u in urls if u not in used_items]
            for i, u in enumerate(fresh_urls[:target_count]):
                ext = ".mp4" if "video" in source else ".jpg"
                dest = str(img_dir / f"sec_{sec_id}_px_{i}{ext}")
                if download_file(u, dest):
                    sec_paths.append(dest)
                    used_items.add(u)

        # 2. Try Pixabay if needed (filtering out already used URLs)
        if not sec_paths and pixabay_key:
            if "video" in source:
                urls = search_pixabay_videos(query, pixabay_key, orientation=orientation, count=target_count + 4)
            else:
                urls = search_pixabay_photos(query, pixabay_key, orientation=orientation, count=target_count + 4)

            fresh_urls = [u for u in urls if u not in used_items]
            for i, u in enumerate(fresh_urls[:target_count]):
                ext = ".mp4" if "video" in source else ".jpg"
                dest = str(img_dir / f"sec_{sec_id}_pb_{i}{ext}")
                if download_file(u, dest):
                    sec_paths.append(dest)
                    used_items.add(u)

        # 3. AI Generative Image Fallback (FLUX / Pollinations with fresh random seed per generation)
        if not sec_paths:
            import time, random
            timestamp_seed = int(time.time() * 1000) % 10000000 + random.randint(100, 99999)
            ai_img_file = str(img_dir / f"sec_{sec_id}_ai_{timestamp_seed}.jpg")
            w, h = (1080, 1920) if is_shorts else (1920, 1080)
            try:
                import urllib.parse, requests
                clean_query = query.replace("\n", " ").strip()
                # Unique artistic style tag per prompt to ensure no visual duplication
                styles = ["cinematic hyperrealistic 8k", "dramatic lighting photorealistic", "epic atmospheric masterpiece", "sharp focus award winning"]
                chosen_style = random.choice(styles)
                prompt_full = f"{clean_query}, {chosen_style}, highly detailed, uncompressed"
                encoded = urllib.parse.quote(prompt_full)
                url = f"https://image.pollinations.ai/prompt/{encoded}?width={w}&height={h}&seed={timestamp_seed}&model=flux&nologo=true"
                resp = requests.get(url, timeout=18)
                if resp.status_code == 200 and resp.content and len(resp.content) > 1000:
                    with open(ai_img_file, "wb") as f:
                        f.write(resp.content)
                    sec_paths.append(ai_img_file)
                    used_items.add(url)
                    log_success(f"   [Section {sec_id}] Synthesized unique AI visual (seed={timestamp_seed}) for '{query}'.")
            except Exception as ai_err:
                log_warn(f"   [Section {sec_id}] AI visual fallback bypassed: {ai_err}")

        # 4. Guaranteed atmospheric gradient background
        if not sec_paths:
            fallback_file = str(img_dir / f"sec_{sec_id}_fallback.jpg")
            w, h = (1080, 1920) if is_shorts else (1920, 1080)
            _create_fallback_gradient(fallback_file, width=w, height=h, sec_id=sec_id)
            sec_paths.append(fallback_file)
            log_warn(f"   [Section {sec_id}] No media found for '{query}'. Used atmospheric backdrop.")
        else:
            log_success(f"   [Section {sec_id}] Acquired {len(sec_paths)} media item(s).")

        result_map[sec_id] = sec_paths

    # Save updated used items registry to disk (capped to latest 1500 items)
    try:
        import json
        with open(used_history_file, "w", encoding="utf-8") as uf:
            json.dump(list(used_items)[-1500:], uf)
    except Exception:
        pass

    return result_map
