"""
Video Rendering Engine
Renders full HD videos (16:9 Landscape or 9:16 Shorts) using MoviePy, Pillow, and NumPy.
Applies Ken Burns zoom/pan motion, smooth crossfades, burned-in subtitles, and synchronized audio.
"""
import os
import re
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
# Compatibility fix: MoviePy 1.0.3 references Image.ANTIALIAS removed in Pillow 10+
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = getattr(Image, "Resampling", Image).LANCZOS

from moviepy.editor import VideoClip, AudioFileClip, concatenate_videoclips, VideoFileClip
from config import load_config, FONTS_DIR, OUTPUT_DIR
from core.logger import log_info, log_warn, log_success

_font_cache = {}


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    font_candidates = [
        FONTS_DIR / "BeVietnamPro-Bold.ttf",
        FONTS_DIR / "MicrosoftYaHeiBold.ttc",
        FONTS_DIR / "Charm-Bold.ttf",
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf")
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
    _font_cache[key] = font
    return font


def _parse_srt(srt_path: str) -> list[dict]:
    """Parse SRT subtitles into a list of {start: float, end: float, text: str}."""
    if not srt_path or not os.path.exists(srt_path):
        log_warn(f"SRT file not found: {srt_path} — video will render without subtitles.")
        return []

    def _ts_to_sec(s: str) -> float:
        parts = s.strip().split(":")
        sec_ms = parts[2].split(",")
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(sec_ms[0]) + int(sec_ms[1]) / 1000.0

    cues = []
    try:
        content = open(srt_path, "r", encoding="utf-8").read().strip()
        # Handle both Windows CRLF (\r\n) and Unix LF (\n) line endings
        blocks = re.split(r"\r?\n\r?\n", content)
        for b in blocks:
            lines = b.strip().splitlines()
            if len(lines) >= 3 and "-->" in lines[1]:
                times = lines[1].split("-->")
                start = _ts_to_sec(times[0])
                end = _ts_to_sec(times[1])
                text = " ".join(lines[2:]).strip()
                if text:
                    cues.append({"start": start, "end": end, "text": text})
    except Exception as e:
        log_warn(f"Failed parsing SRT file {srt_path}: {e}")
    log_info(f"SRT loaded: {len(cues)} subtitle cues from {os.path.basename(srt_path)}")
    return cues


def _find_cue_at_time(cues: list[dict], current_time: float) -> str:
    for c in cues:
        # Extend cue display by 0.25s for visual persistence across speech pauses
        if c["start"] <= current_time <= (c["end"] + 0.25):
            return c["text"]
    return ""


_vignette_cache = {}


def _get_vignette_overlay(W: int, H: int) -> Image.Image:
    """Precomputed cached vignette gradient overlay for fast frame rendering."""
    key = (W, H)
    if key in _vignette_cache:
        return _vignette_cache[key]
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    grad_height = int(H * 0.28)
    for y in range(grad_height):
        alpha = int(170 * (y / grad_height))
        ov_draw.line([(0, H - grad_height + y), (W, H - grad_height + y)], fill=(0, 0, 0, alpha))
    _vignette_cache[key] = overlay
    return overlay


def _pre_fit_aspect(base_img: Image.Image, W: int, H: int) -> Image.Image:
    """Fit base image to target aspect ratio once per section for maximum speed."""
    bw, bh = base_img.size
    target_aspect = W / H
    img_aspect = bw / bh

    if img_aspect > target_aspect:
        new_w = int(bh * target_aspect)
        offset_x = (bw - new_w) // 2
        crop_box = (offset_x, 0, offset_x + new_w, bh)
    else:
        new_h = int(bw / target_aspect)
        offset_y = (bh - new_h) // 2
        crop_box = (0, offset_y, bw, offset_y + new_h)

    return base_img.crop(crop_box)


def _draw_subtitles_and_overlay(frame_img: Image.Image, subtitle: str, W: int, H: int, is_shorts: bool, section_title: str = "", show_subtitles: bool = True):
    # Only apply vignette if subtitles or header are present
    if (show_subtitles and subtitle) or section_title:
        vignette = _get_vignette_overlay(W, H)
        frame_img = frame_img.convert("RGBA")
        frame_img.paste(vignette, (0, 0), vignette)
        draw = ImageDraw.Draw(frame_img)
    else:
        draw = ImageDraw.Draw(frame_img)

    # 1. Section Header badge
    if section_title:
        head_font = _get_font(26 if is_shorts else 24, bold=True)
        if is_shorts:
            bbox = draw.textbbox((0, 0), section_title.upper(), font=head_font)
            bw = bbox[2] - bbox[0]
            bx = (W - bw) // 2
            draw.rounded_rectangle([bx - 12, 50, bx + bw + 12, 90], radius=8, fill=(15, 23, 42, 190))
            draw.text((bx, 57), section_title.upper(), font=head_font, fill=(251, 191, 36))
        else:
            draw.rounded_rectangle([50, 45, 350, 85], radius=6, fill=(15, 23, 42, 180))
            draw.text((65, 52), f"• {section_title[:32]}", font=head_font, fill=(241, 245, 249))

    # 2. Render Subtitle Text (fast compiled outline stroke in C)
    if show_subtitles and subtitle:
        font_size = 56 if is_shorts else 44
        sub_font = _get_font(font_size, bold=True)
        
        max_w = int(W * 0.85)
        words = subtitle.split()
        lines = []
        cur = []
        for w in words:
            test = " ".join(cur + [w])
            bb = draw.textbbox((0, 0), test, font=sub_font)
            if bb[2] - bb[0] > max_w and cur:
                lines.append(" ".join(cur))
                cur = [w]
            else:
                cur.append(w)
        if cur:
            lines.append(" ".join(cur))

        line_h = font_size + 14
        total_h = len(lines) * line_h
        # Safe margin from YouTube UI (bottom 32% for Shorts, bottom 15% for normal)
        y_pos = int(H * 0.68) if is_shorts else (H - total_h - 85)

        # Professional captions styling: Crisp White with controlled Amber Gold accent
        # Strictly compliant with MASTER_ARCHITECTURE.md Section 20 (no rainbow colors!)
        PRIMARY_COLOR = (255, 255, 255)     # Crisp White (#FFFFFF)
        ACCENT_COLOR = (251, 191, 36)       # Amber Gold (#FBBF24)

        for l_idx, line_str in enumerate(lines):
            l_bbox = draw.textbbox((0, 0), line_str, font=sub_font)
            l_w = l_bbox[2] - l_bbox[0]
            x_pos = (W - l_w) // 2
            cur_y = y_pos + (l_idx * line_h)

            # Accent color on final punchline line, crisp white on all others
            fill_color = ACCENT_COLOR if (l_idx == len(lines) - 1 and len(lines) > 1) else PRIMARY_COLOR
            # High-contrast 4px black outline stroke for maximum readability
            draw.text((x_pos, cur_y), line_str, font=sub_font, fill=fill_color, stroke_width=4, stroke_fill=(0, 0, 0))

    return np.array(frame_img.convert("RGB"))


def _ken_burns_frame(fitted: Image.Image, t: float, duration: float, W: int, H: int, zoom_start: float = 1.0, zoom_end: float = 1.15, pan_dir: tuple = (1, 0)) -> Image.Image:
    """Computes smooth Ken Burns crop and zoom with fast Bilinear interpolation."""
    progress = min(1.0, max(0.0, t / max(duration, 0.1)))
    eased = 0.5 - 0.5 * math.cos(progress * math.pi)

    scale = zoom_start + (zoom_end - zoom_start) * eased
    fw, fh = fitted.size

    scaled_w = int(fw / scale)
    scaled_h = int(fh / scale)

    max_dx = fw - scaled_w
    max_dy = fh - scaled_h

    dx = int((pan_dir[0] + 1) * 0.5 * max_dx * eased)
    dy = int((pan_dir[1] + 1) * 0.5 * max_dy * eased)

    zoomed = fitted.crop((dx, dy, dx + scaled_w, dy + scaled_h))
    return zoomed.resize((W, H), Image.BILINEAR)


def render_video(script: dict, media_map: dict[int, list[str]], audio_path: str, srt_path: str, output_path: str = None) -> str:
    """
    Render video with synced voiceover, subtitles, and Ken Burns animation.
    """
    if not output_path:
        output_path = str(OUTPUT_DIR / "final_video.mp4")

    cfg = load_config()
    video_type = script.get("video_type", cfg.get("video_type", "normal"))
    is_shorts = (video_type == "shorts")

    W = 1080 if is_shorts else 1920
    H = 1920 if is_shorts else 1080
    FPS = int(cfg.get("video_fps", 30))
    preset = cfg.get("render_preset", "ultrafast")
    zoom_start = float(cfg.get("kb_zoom_start", 1.0))
    zoom_end = float(cfg.get("kb_zoom_end", 1.15))
    show_subtitles = (cfg.get("subtitles_enabled", True) is not False)

    audio_clip = AudioFileClip(audio_path)
    total_duration = audio_clip.duration

    # YouTube Shorts strict duration limit: Maximum 60 seconds (clamp to 58.5s for safety)
    if is_shorts and total_duration > 59.0:
        log_warn(f"Audio duration ({total_duration:.1f}s) exceeds YouTube Shorts 60s limit. Trimming to 58.5s.")
        audio_clip = audio_clip.subclip(0, 58.5)
        total_duration = 58.5

    cues = _parse_srt(srt_path) if show_subtitles else []
    sections = script.get("sections", [])
    if not sections:
        raise ValueError("Script contains no sections to render.")

    # Calculate duration per section
    sec_duration = total_duration / len(sections)

    sub_status = "enabled" if show_subtitles else "disabled"
    log_info(f"Rendering {video_type.upper()} video ({sub_status} subtitles): {W}x{H} @ {FPS}fps, Duration: {total_duration:.1f}s across {len(sections)} sections...")

    clips = []
    pan_directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]

    for idx, sec in enumerate(sections):
        sec_id = sec.get("id", idx + 1)
        sec_title = sec.get("title", "")
        sec_start_t = idx * sec_duration
        sec_dur = sec_duration
        paths = media_map.get(sec_id, [])

        img_path = paths[0] if paths else None
        is_video_asset = bool(img_path and img_path.lower().endswith(".mp4") and os.path.exists(img_path))
        if is_video_asset:
            try:
                v_clip = VideoFileClip(img_path)
                v_w, v_h = v_clip.size
                if v_w / v_h > W / H:
                    v_clip = v_clip.resize(height=H)
                else:
                    v_clip = v_clip.resize(width=W)
                v_clip = v_clip.crop(x_center=v_clip.w / 2, y_center=v_clip.h / 2, width=W, height=H)
                if v_clip.duration < sec_dur:
                    from moviepy.editor import vfx
                    v_clip = v_clip.fx(vfx.loop, duration=sec_dur)
                else:
                    v_clip = v_clip.subclip(0, sec_dur)

                def make_vid_frame(get_frame, t, start_t=sec_start_t, title=sec_title, show_sub=show_subtitles):
                    base_f = Image.fromarray(get_frame(t))
                    global_t = start_t + t
                    sub_text = _find_cue_at_time(cues, global_t) if show_sub else ""
                    return _draw_subtitles_and_overlay(base_f, sub_text, W, H, is_shorts, title, show_subtitles=show_sub)

                clip = v_clip.fl(make_vid_frame)
                clips.append(clip)
                continue
            except Exception as vid_err:
                log_warn(f"Failed to load video file {img_path}: {vid_err}. Using image fallback.")

        if img_path and os.path.exists(img_path) and not img_path.lower().endswith(".mp4"):
            raw_img = Image.open(img_path).convert("RGB")
        else:
            raw_img = Image.new("RGB", (W, H), (15, 15, 28))

        # Pre-fit to target aspect ratio once per section
        fitted_base = _pre_fit_aspect(raw_img, W, H)
        pan_dir = pan_directions[idx % len(pan_directions)]

        def make_frame(t, fitted=fitted_base, pan_dir=pan_dir, start_t=sec_start_t, title=sec_title, show_sub=show_subtitles):
            global_t = start_t + t
            sub_text = _find_cue_at_time(cues, global_t) if show_sub else ""
            transformed = _ken_burns_frame(fitted, t, sec_dur, W, H, zoom_start, zoom_end, pan_dir)
            return _draw_subtitles_and_overlay(transformed, sub_text, W, H, is_shorts, title, show_subtitles=show_sub)

        clip = VideoClip(make_frame, duration=sec_dur)
        clips.append(clip)

    # Concatenate clips
    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.set_audio(audio_clip)

    import multiprocessing
    cpu_threads = max(2, min(8, multiprocessing.cpu_count() or 4))
    log_info(f"Encoding final MP4 video to {output_path} (preset={preset}, threads={cpu_threads})...")
    final_video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="5000k" if is_shorts else "8000k",
        preset=preset,
        threads=cpu_threads,
        ffmpeg_params=["-tune", "fastdecode"],
        logger=None
    )

    audio_clip.close()
    final_video.close()
    for c in clips:
        c.close()

    log_success(f"Final video successfully generated: {os.path.basename(output_path)}")
    return output_path
