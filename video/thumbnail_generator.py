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


def generate_thumbnail(script: dict, image_path: str = None, output_file: str = None) -> str:
    """
    Generate an engaging YouTube thumbnail (1280x720).
    """
    TW, TH = 1280, 720
    if not output_file:
        output_file = str(OUTPUT_DIR / "thumbnail.jpg")

    cfg = load_config()
    channel_name = cfg.get("channel_name", "YouTube Studio").upper()
    title = script.get("title", "MIND-BENDING REVELATION").upper()

    # Base Background Image
    if image_path and os.path.exists(image_path):
        try:
            bg = Image.open(image_path).convert("RGB")
            bw, bh = bg.size
            scale = max(TW / bw, TH / bh)
            bg = bg.resize((int(bw * scale), int(bh * scale)), Image.LANCZOS)
            nw, nh = bg.size
            bg = bg.crop(((nw - TW) // 2, (nh - TH) // 2, (nw - TW) // 2 + TW, (nh - TH) // 2 + TH))
            # Subtle blur & contrast boost for background readability
            bg = bg.filter(ImageFilter.GaussianBlur(radius=1.5))
        except Exception as e:
            log_warn(f"Thumbnail base image error: {e}. Using dark background.")
            bg = Image.new("RGB", (TW, TH), (15, 15, 26))
    else:
        bg = Image.new("RGB", (TW, TH), (15, 15, 26))

    # Dark cinematic gradient overlay
    overlay = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for x in range(TW):
        alpha = int(210 * (1 - (x / TW) * 0.45))
        ov_draw.line([(x, 0), (x, TH)], fill=(5, 5, 15, alpha))
    # Bottom shadow bar
    ov_draw.rectangle([0, TH - 90, TW, TH], fill=(0, 0, 0, 195))

    bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(bg)

    # Accent colored glow bar on the left
    draw.rectangle([50, 80, 60, TH - 120], fill=(99, 102, 241)) # Indigo accent
    draw.rectangle([70, 80, 500, 86], fill=(245, 158, 11)) # Amber secondary

    # Render Title Text (Max 2 lines, large bold font with heavy drop shadow)
    font_main = _get_font(74, bold=True)
    lines = _wrap_text(draw, title, font_main, TW - 240)
    if len(lines) > 2:
        font_main = _get_font(60, bold=True)
        lines = _wrap_text(draw, title, font_main, TW - 240)[:2]

    start_y = 120
    for idx, line in enumerate(lines):
        y = start_y + (idx * 85)
        # Heavy drop shadow
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                draw.text((75 + dx, y + dy), line, font=font_main, fill=(0, 0, 0))
        # Highlight first word with yellow/amber, remainder in pure white
        words = line.split(" ", 1)
        fw = words[0]
        rest = (" " + words[1]) if len(words) > 1 else ""

        draw.text((75, y), fw, font=font_main, fill=(251, 191, 36)) # Amber-400
        fw_bbox = draw.textbbox((0, 0), fw, font=font_main)
        fw_w = fw_bbox[2] - fw_bbox[0]
        if rest:
            draw.text((75 + fw_w, y), rest, font=font_main, fill=(255, 255, 255))

    # Channel Name watermark badge
    font_sub = _get_font(30, bold=True)
    draw.text((75, TH - 65), f"▶  {channel_name}", font=font_sub, fill=(203, 213, 225))

    # "4K HDR" / "EXPLAINED" Badge on Top Right
    badge_font = _get_font(26, bold=True)
    badge_text = "MUST WATCH"
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    bw = bbox[2] - bbox[0]
    bx = TW - bw - 90
    draw.rounded_rectangle([bx - 14, 50, bx + bw + 14, 96], radius=6, fill=(225, 29, 72)) # Crimson
    draw.text((bx, 57), badge_text, font=badge_font, fill=(255, 255, 255))

    bg.save(output_file, "JPEG", quality=95)
    log_success(f"Generated YouTube Thumbnail: {os.path.basename(output_file)}")
    return output_file
