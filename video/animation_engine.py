"""
Animation Engine — Kids & Elders Dynamic Visual Generator
Produces dedicated cartoon and storybook animation scenes for channels using the 'animation' engine.
Eliminates dependency on stock footage APIs (Pexels / Pixabay) for animated/illustrated channels.
"""
import os
import math
import random
from pathlib import Path
from typing import Dict, List, Any, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import OUTPUT_DIR, FONTS_DIR
from core.logger import log_info, log_success

_ANIM_FONTS_CACHE = {}


def _get_anim_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key in _ANIM_FONTS_CACHE:
        return _ANIM_FONTS_CACHE[key]
    font_candidates = [
        FONTS_DIR / "BeVietnamPro-Bold.ttf",
        Path("C:/Windows/Fonts/comic.ttf"),
        Path("C:/Windows/Fonts/segoeprb.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
    ]
    font = None
    for p in font_candidates:
        if p.exists():
            try:
                font = ImageFont.truetype(str(p), size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()
    _ANIM_FONTS_CACHE[key] = font
    return font


def _draw_cartoon_sun(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int):
    """Draw a smiling cartoon sun with animated rays."""
    # Rays
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        x1 = cx + int((r + 10) * math.cos(rad))
        y1 = cy + int((r + 10) * math.sin(rad))
        x2 = cx + int((r + 35) * math.cos(rad))
        y2 = cy + int((r + 35) * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=(255, 204, 0), width=6)

    # Core
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 215, 0), outline=(245, 158, 11), width=4)
    # Smiling eyes
    eye_r = max(4, r // 7)
    draw.ellipse([cx - r // 3 - eye_r, cy - r // 4 - eye_r, cx - r // 3 + eye_r, cy - r // 4 + eye_r], fill=(30, 41, 59))
    draw.ellipse([cx + r // 3 - eye_r, cy - r // 4 - eye_r, cx + r // 3 + eye_r, cy - r // 4 + eye_r], fill=(30, 41, 59))
    # Smile
    draw.arc([cx - r // 3, cy - r // 6, cx + r // 3, cy + r // 2], start=10, end=170, fill=(234, 88, 12), width=5)


def _draw_cartoon_cloud(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0):
    """Draw a fluffy white cartoon cloud."""
    r = int(35 * scale)
    color = (255, 255, 255, 240)
    border = (203, 213, 225, 255)
    draw.ellipse([x - r, y - r // 2, x + r, y + r // 2], fill=color, outline=border, width=2)
    draw.ellipse([x - int(25 * scale), y - int(20 * scale), x + int(10 * scale), y + int(15 * scale)], fill=color, outline=border, width=2)
    draw.ellipse([x + int(5 * scale), y - int(25 * scale), x + int(45 * scale), y + int(15 * scale)], fill=color, outline=border, width=2)
    draw.ellipse([x + int(30 * scale), y - r // 2, x + int(70 * scale), y + r // 2], fill=color, outline=border, width=2)


def _draw_rainbow(draw: ImageDraw.ImageDraw, W: int, H: int):
    """Draw a vibrant cartoon rainbow arc across the background."""
    cx, cy = W // 2, int(H * 0.95)
    colors = [
        (239, 68, 68),    # Red
        (249, 115, 22),   # Orange
        (234, 179, 8),    # Yellow
        (34, 197, 94),    # Green
        (59, 130, 246),   # Blue
        (168, 85, 247),   # Purple
    ]
    base_r = int(min(W, H) * 0.8)
    arc_w = 14
    for i, col in enumerate(colors):
        r = base_r - (i * arc_w)
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=185, end=355, fill=col, width=arc_w)


def generate_kids_scene(
    title: str,
    narration_snippet: str,
    W: int = 1080,
    H: int = 1920,
    sec_id: int = 1,
    output_path: str = None
) -> str:
    """
    Generate a high-vibrancy, delightful 2D cartoon scene for Kids Wonder Lab.
    """
    img = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(img)

    # 1. Cheerful sky gradient
    sky_palettes = [
        ((125, 211, 252), (186, 230, 253)),  # Sky blue to soft cyan
        ((253, 224, 71), (254, 240, 138)),   # Morning yellow sunburst
        ((196, 181, 253), (233, 213, 255)),  # Dreamy lavender
        ((110, 231, 183), (167, 243, 208)),  # Fresh mint meadow sky
    ]
    top_c, bot_c = sky_palettes[(sec_id - 1) % len(sky_palettes)]
    for y in range(int(H * 0.65)):
        fac = y / (H * 0.65)
        r = int(top_c[0] * (1 - fac) + bot_c[0] * fac)
        g = int(top_c[1] * (1 - fac) + bot_c[1] * fac)
        b = int(top_c[2] * (1 - fac) + bot_c[2] * fac)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # 2. Rainbow or Sun
    if sec_id % 2 == 1:
        _draw_rainbow(draw, W, H)
        _draw_cartoon_sun(draw, int(W * 0.82), int(H * 0.16), int(W * 0.11))
    else:
        _draw_cartoon_sun(draw, int(W * 0.2), int(H * 0.18), int(W * 0.13))
        _draw_cartoon_cloud(draw, int(W * 0.65), int(H * 0.22), scale=1.4)

    # 3. Floating clouds
    _draw_cartoon_cloud(draw, int(W * 0.15), int(H * 0.28), scale=1.1)
    _draw_cartoon_cloud(draw, int(W * 0.78), int(H * 0.35), scale=0.9)

    # 4. Lush rolling green cartoon hills
    hill_color_back = (74, 222, 128)
    hill_color_front = (34, 197, 94)
    # Background hill
    draw.ellipse([-int(W * 0.2), int(H * 0.52), int(W * 0.9), int(H * 0.95)], fill=hill_color_back)
    draw.ellipse([int(W * 0.3), int(H * 0.55), int(W * 1.3), int(H * 0.98)], fill=hill_color_back)
    # Foreground hill
    draw.ellipse([-int(W * 0.1), int(H * 0.62), int(W * 1.1), int(H * 1.05)], fill=hill_color_front)

    # 5. Little flowers & stars on the meadow
    flower_colors = [(244, 63, 94), (234, 179, 8), (168, 85, 247), (255, 255, 255)]
    random.seed(sec_id * 42)
    for _ in range(18):
        fx = random.randint(40, W - 40)
        fy = random.randint(int(H * 0.68), int(H * 0.88))
        fcol = random.choice(flower_colors)
        draw.ellipse([fx - 7, fy - 7, fx + 7, fy + 7], fill=fcol)
        draw.ellipse([fx - 3, fy - 3, fx + 3, fy + 3], fill=(254, 240, 138))

    # 6. Kid-friendly Scene Title Banner
    card_w = int(W * 0.88)
    card_h = 130
    card_x = (W - card_w) // 2
    card_y = int(H * 0.44)
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=26,
        fill=(255, 255, 255, 245),
        outline=(56, 189, 248),
        width=4
    )

    f_title = _get_anim_font(int(card_h * 0.32), bold=True)
    f_badge = _get_anim_font(int(card_h * 0.18), bold=True)
    draw.text((card_x + 28, card_y + 18), "⭐ KIDS WONDER LAB", fill=(14, 165, 233), font=f_badge)
    clean_title = (title[:32] + "...") if len(title) > 32 else title
    draw.text((card_x + 28, card_y + 50), clean_title, fill=(15, 23, 42), font=f_title)

    # 7. Wholesome sticker badge (Child-Safe Educational icon)
    badge_cx = card_x + card_w - 55
    badge_cy = card_y + 60
    draw.ellipse([badge_cx - 36, badge_cy - 36, badge_cx + 36, badge_cy + 36], fill=(245, 158, 11), outline=(255, 255, 255), width=3)
    draw.text((badge_cx - 14, badge_cy - 16), "👶", font=_get_anim_font(28))

    if not output_path:
        out_dir = OUTPUT_DIR / "images"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(out_dir / f"scene_anim_{sec_id}.jpg")

    img.convert("RGB").save(output_path, "JPEG", quality=95)
    return output_path


def generate_elders_scene(
    title: str,
    narration_snippet: str,
    W: int = 1920,
    H: int = 1080,
    sec_id: int = 1,
    output_path: str = None
) -> str:
    """
    Generate a warm, dignified, watercolor storybook plate for Wonder Saga TV.
    """
    img = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(img)

    # 1. Warm Golden Hour / Nostalgic Sunset Gradient
    sunset_palettes = [
        ((30, 27, 75), (120, 53, 15), (251, 191, 36)),    # Deep twilight to golden horizon
        ((67, 20, 7), (154, 52, 18), (254, 215, 170)),     # Mahogany to warm peach
        ((24, 24, 27), (88, 28, 135), (245, 158, 11)),     # Velvet night to amber glow
    ]
    c_top, c_mid, c_bot = sunset_palettes[(sec_id - 1) % len(sunset_palettes)]

    for y in range(H):
        fac = y / H
        if fac < 0.5:
            sub_f = fac * 2.0
            r = int(c_top[0] * (1 - sub_f) + c_mid[0] * sub_f)
            g = int(c_top[1] * (1 - sub_f) + c_mid[1] * sub_f)
            b = int(c_top[2] * (1 - sub_f) + c_mid[2] * sub_f)
        else:
            sub_f = (fac - 0.5) * 2.0
            r = int(c_mid[0] * (1 - sub_f) + c_bot[0] * sub_f)
            g = int(c_mid[1] * (1 - sub_f) + c_bot[1] * sub_f)
            b = int(c_mid[2] * (1 - sub_f) + c_bot[2] * sub_f)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # 2. Golden Sun Glow on the horizon
    sun_x = int(W * 0.5)
    sun_y = int(H * 0.58)
    for r in range(int(W * 0.22), 20, -15):
        alpha = int(45 * (1.0 - (r / (W * 0.22))))
        draw.ellipse([sun_x - r, sun_y - r, sun_x + r, sun_y + r], fill=(251, 191, 36, alpha))

    # 3. Silhouette horizon with hills and ancient oaks
    hill_c = (15, 15, 20)
    draw.ellipse([-int(W * 0.1), int(H * 0.65), int(W * 0.7), int(H * 1.3)], fill=hill_c)
    draw.ellipse([int(W * 0.4), int(H * 0.68), int(W * 1.2), int(H * 1.35)], fill=hill_c)

    # 4. Elegant Storybook Parchment Card
    card_w = int(W * 0.72)
    card_h = 160
    card_x = (W - card_w) // 2
    card_y = int(H * 0.72)
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=18,
        fill=(15, 23, 42, 235),
        outline=(217, 119, 6),
        width=2
    )

    f_sub = _get_anim_font(int(card_h * 0.16), bold=False)
    f_title = _get_anim_font(int(card_h * 0.32), bold=True)
    draw.text((card_x + 36, card_y + 24), "📖 WONDER SAGA TV — MYTHS & WONDERS", fill=(251, 191, 36), font=f_sub)
    clean_title = (title[:48] + "...") if len(title) > 48 else title
    draw.text((card_x + 36, card_y + 62), clean_title, fill=(248, 250, 252), font=f_title)

    # 5. Vintage border accent
    draw.rectangle([20, 20, W - 20, H - 20], outline=(251, 191, 36, 120), width=1)

    if not output_path:
        out_dir = OUTPUT_DIR / "images"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(out_dir / f"scene_anim_{sec_id}.jpg")

    img.convert("RGB").save(output_path, "JPEG", quality=95)
    return output_path


def generate_animated_media_map(
    script: Dict[str, Any],
    channel_id: str = "kids",
    video_type: str = "normal",
    audience_type: str = "children"
) -> Dict[int, List[str]]:
    """
    Generate scene plates for each section of the script without any stock footage API.
    Returns media_map matching renderer expectations: {sec_id: [image_path, ...]}
    """
    is_shorts = (video_type == "shorts")
    w, h = (1080, 1920) if is_shorts else (1920, 1080)
    sections = script.get("sections", [])

    img_dir = OUTPUT_DIR / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    result_map = {}
    is_kids = (channel_id == "kids" or audience_type in ("children", "kids"))

    log_info(f"Animation Engine generating {len(sections)} animated scene plates for channel '{channel_id}'...")

    for sec in sections:
        sec_id = sec.get("id", 1)
        sec_title = sec.get("title", f"Scene {sec_id}")
        narration = sec.get("narration", "")

        out_path = str(img_dir / f"anim_scene_{sec_id}_{'kids' if is_kids else 'elders'}.jpg")
        plate_generated = False

        # Attempt AI generation with Nano Banana if Gemini key configured
        from config import load_config
        cfg = load_config()
        nano_key = (cfg.get("gemini_api_key") or cfg.get("nano_banana_api_key", "")).strip()
        if nano_key:
            try:
                from media.nano_banana_client import generate_image_with_nano_banana
                ai_model = "nano-banana-cartoon-v1" if is_kids else "nano-banana-storybook-v1"
                prompt_desc = f"{sec_title}: {narration}" if narration else sec_title
                res = generate_image_with_nano_banana(
                    prompt=f"{prompt_desc}, {'2D bright cheerful cartoon illustration' if is_kids else 'warm watercolor storybook illustration'}, high quality, 4k",
                    width=w,
                    height=h,
                    output_path=out_path,
                    api_key=nano_key,
                    model=ai_model
                )
                if res and os.path.exists(res):
                    plate_generated = True
                    log_success(f"Animation Engine generated AI plate for Scene {sec_id} via Nano Banana ({ai_model})")
            except Exception as e:
                log_info(f"Nano Banana AI plate generation fallback: {e}")

        if not plate_generated:
            if is_kids:
                generate_kids_scene(title=sec_title, narration_snippet=narration, W=w, H=h, sec_id=sec_id, output_path=out_path)
            else:
                generate_elders_scene(title=sec_title, narration_snippet=narration, W=w, H=h, sec_id=sec_id, output_path=out_path)

        result_map[sec_id] = [out_path]

    log_success(f"Animation Engine generated {len(result_map)} scenes successfully!")
    return result_map
