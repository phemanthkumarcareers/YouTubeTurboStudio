"""
High-CTR YouTube Thumbnail Generator
Produces eye-catching 1280x720 thumbnails with bold typography, contrast gradient overlays,
accent borders, and channel branding.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import load_config, FONTS_DIR, OUTPUT_DIR
from core.logger import log_info, log_success, log_warn


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    font_candidates = [
        FONTS_DIR / "BeVietnamPro-Bold.ttf",
        FONTS_DIR / "MicrosoftYaHeiBold.ttc",
        FONTS_DIR / "Charm-Bold.ttf",
        Path("C:/Windows/Fonts/impact.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf")
    ]
    for p in font_candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines = []
    current_line = []
    for w in words:
        test_line = " ".join(current_line + [w])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > max_w and current_line:
            lines.append(" ".join(current_line))
            current_line = [w]
        else:
            current_line.append(w)
    if current_line:
        lines.append(" ".join(current_line))
    return lines or [text]


def generate_thumbnail(script: dict, image_path: str = None, output_file: str = None, variant: str = None) -> str:
    """
    Generate ONE high-CTR YouTube thumbnail (1280x720).
    Rotates layouts/styles dynamically per video (minimalist_curiosity, bold_urgency, split_cinematic, dark_spotlight).
    """
    import random
    TW, TH = 1280, 720
    if not output_file:
        output_file = str(OUTPUT_DIR / "thumbnail.jpg")

    cfg = load_config()
    channel_name = cfg.get("channel_name", "InsightSpark TV").upper()
    
    # Use script thumbnail_text if provided by AI, otherwise fallback to title
    raw_text = script.get("thumbnail_text") or script.get("title", "MIND-BENDING REVELATION")
    title = raw_text.upper().strip()

    # Dynamic format rotation per video based on title hash or random
    available_styles = ["curiosity", "urgency", "dramatic", "spotlight"]
    if not variant:
        # Pseudo-random deterministic choice per title so format varies across videos
        style_idx = abs(hash(title + script.get("description", ""))) % len(available_styles)
        variant = available_styles[style_idx]

    # Base Background Image
    if image_path and os.path.exists(image_path):
        try:
            bg = Image.open(image_path).convert("RGB")
            bw, bh = bg.size
            scale = max(TW / bw, TH / bh)
            bg = bg.resize((int(bw * scale), int(bh * scale)), Image.LANCZOS)
            nw, nh = bg.size
            bg = bg.crop(((nw - TW) // 2, (nh - TH) // 2, (nw - TW) // 2 + TW, (nh - TH) // 2 + TH))
            blur_radius = 0.8 if variant == "dramatic" else 1.5
            bg = bg.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        except Exception as e:
            log_warn(f"Thumbnail base image error: {e}. Using dark background.")
            bg = Image.new("RGB", (TW, TH), (15, 15, 26))
    else:
        bg = Image.new("RGB", (TW, TH), (15, 15, 26))

    # Dynamic Gradient / Overlay depending on chosen variant format
    overlay = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)

    if variant == "spotlight":
        # Radial / central spotlight with darkened vignettes
        for x in range(TW):
            dist_from_left = abs(x - (TW * 0.35)) / TW
            alpha = int(min(240, 160 + dist_from_left * 180))
            ov_draw.line([(x, 0), (x, TH)], fill=(5, 5, 15, alpha))
    elif variant == "dramatic":
        # Left-to-right deep dark vignette
        for x in range(TW):
            alpha = int(240 * (1 - (x / TW) * 0.55))
            ov_draw.line([(x, 0), (x, TH)], fill=(3, 7, 18, alpha))
    elif variant == "urgency":
        # Crimson gradient tint overlay
        for x in range(TW):
            alpha = int(220 * (1 - (x / TW) * 0.45))
            ov_draw.line([(x, 0), (x, TH)], fill=(20, 5, 8, alpha))
    else: # curiosity
        for x in range(TW):
            alpha = int(210 * (1 - (x / TW) * 0.45))
            ov_draw.line([(x, 0), (x, TH)], fill=(5, 5, 15, alpha))

    # Bottom shadow bar
    ov_draw.rectangle([0, TH - 90, TW, TH], fill=(0, 0, 0, 200))

    bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(bg)

    # Accent colored glow bar & Badge based on variant
    if variant == "urgency":
        draw.rectangle([50, 80, 60, TH - 120], fill=(239, 68, 68)) # Red accent
        draw.rectangle([70, 80, 500, 86], fill=(245, 158, 11))
        badge_text = "WARNING"
        badge_bg = (220, 38, 38)
        highlight_color = (252, 211, 77)
    elif variant == "dramatic":
        draw.rectangle([50, 80, 60, TH - 120], fill=(168, 85, 247)) # Purple accent
        draw.rectangle([70, 80, 500, 86], fill=(6, 182, 212))
        badge_text = "THE TRUTH"
        badge_bg = (147, 51, 234)
        highlight_color = (192, 132, 252)
    elif variant == "spotlight":
        draw.rectangle([50, 80, 60, TH - 120], fill=(6, 182, 212)) # Cyan accent
        draw.rectangle([70, 80, 500, 86], fill=(251, 191, 36))
        badge_text = "REVEALED"
        badge_bg = (14, 116, 144)
        highlight_color = (56, 189, 248)
    else: # curiosity
        draw.rectangle([50, 80, 60, TH - 120], fill=(99, 102, 241)) # Indigo accent
        draw.rectangle([70, 80, 500, 86], fill=(245, 158, 11))
        badge_text = "MUST WATCH"
        badge_bg = (225, 29, 72)
        highlight_color = (251, 191, 36)

    # Render Title Text (Max 2 lines, large bold font with heavy drop shadow)
    font_main = _get_font(76, bold=True)
    lines = _wrap_text(draw, title, font_main, TW - 240)
    if len(lines) > 2:
        font_main = _get_font(62, bold=True)
        lines = _wrap_text(draw, title, font_main, TW - 240)[:2]

    start_y = 130
    for idx, line in enumerate(lines):
        y = start_y + (idx * 90)
        # 3D Drop shadow
        for dx in range(-5, 6):
            for dy in range(-5, 6):
                draw.text((75 + dx, y + dy), line, font=font_main, fill=(0, 0, 0))

        words = line.split(" ", 1)
        fw = words[0]
        rest = (" " + words[1]) if len(words) > 1 else ""

        draw.text((75, y), fw, font=font_main, fill=highlight_color)
        fw_bbox = draw.textbbox((0, 0), fw, font=font_main)
        fw_w = fw_bbox[2] - fw_bbox[0]
        if rest:
            draw.text((75 + fw_w, y), rest, font=font_main, fill=(255, 255, 255))

    # Channel Name watermark badge
    font_sub = _get_font(30, bold=True)
    draw.text((75, TH - 65), f"▶  {channel_name}", font=font_sub, fill=(203, 213, 225))

    # High CTR Badge on Top Right
    badge_font = _get_font(26, bold=True)
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    bw = bbox[2] - bbox[0]
    bx = TW - bw - 90
    draw.rounded_rectangle([bx - 14, 50, bx + bw + 14, 96], radius=6, fill=badge_bg)
    draw.text((bx, 57), badge_text, font=badge_font, fill=(255, 255, 255))

    bg.save(output_file, "JPEG", quality=95)
    log_success(f"Generated Single High-CTR YouTube Thumbnail ({variant} layout): {os.path.basename(output_file)}")
    return output_file
