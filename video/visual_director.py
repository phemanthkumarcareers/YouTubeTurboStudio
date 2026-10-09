"""
Visual Director — InsightSpark TV
Transforms narrative sections into fine-grained timestamped visual beats.
A 50-60s Short will have 12-18 rapid visual cuts (every 2.5 - 3.5s).
Supports video clips, photos with dynamic zooms, and programmatic science diagrams.
"""
import math
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont


def plan_visual_beats(script_data: Dict[str, Any], is_shorts: bool = False) -> List[Dict[str, Any]]:
    """
    Subdivide narrative sections into timestamped visual beats.
    Returns list of visual beat plans:
    [{beat_id, section_id, query, visual_type, duration_weight, pan_direction}]
    """
    sections = script_data.get("sections", [])
    beats = []
    beat_counter = 1

    # In Shorts, cut every ~2.5 - 3.5 seconds; in long form, cut every ~4 - 6 seconds
    sub_cuts_per_section = 2 if is_shorts else 3

    directions = ["zoom_in", "zoom_out", "pan_left", "pan_right", "orbit"]

    for sec in sections:
        sec_id = sec.get("id", 1)
        base_query = sec.get("visual_query", "deep space universe")
        words = sec.get("narration", "").split()
        sec_title = sec.get("title", "")

        for cut_idx in range(sub_cuts_per_section):
            # Derive sub-query variant
            if cut_idx == 0:
                query = base_query
                v_type = "video"  # Video-first priority
            elif cut_idx == 1:
                # Secondary query emphasizing dynamic detail
                query = f"{base_query} cinematic"
                v_type = "photo_zoom"
            else:
                query = f"{base_query} science diagram"
                v_type = "diagram"

            beats.append({
                "beat_id": beat_counter,
                "section_id": sec_id,
                "section_title": sec_title,
                "query": query,
                "visual_type": v_type,
                "direction": directions[beat_counter % len(directions)],
                "word_offset": cut_idx * (len(words) // sub_cuts_per_section)
            })
            beat_counter += 1

    return beats


def generate_science_diagram(
    title: str,
    subtitle: str,
    width: int = 1080,
    height: int = 1920,
    output_path: str = None
) -> Image.Image:
    """
    Generate a high-tech programmatic science diagram / HUD graphic
    when stock media is unavailable or for conceptual abstract topics.
    """
    img = Image.new("RGBA", (width, height), (8, 11, 20, 255))
    draw = ImageDraw.Draw(img)

    cx, cy = width // 2, height // 2

    # Draw cosmic coordinate grid
    grid_color = (30, 41, 59, 120)
    for x in range(0, width, 80):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, 80):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    # Concentric orbital radar rings
    for r in range(120, min(width, height) // 2 - 40, 90):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(56, 189, 248, 70), width=2)

    # Sci-fi reticle lines
    draw.line([(cx - 180, cy), (cx + 180, cy)], fill=(99, 102, 241, 160), width=2)
    draw.line([(cx, cy - 180), (cx, cy + 180)], fill=(99, 102, 241, 160), width=2)

    # Core particle glow
    glow_radius = 45
    draw.ellipse(
        [cx - glow_radius, cy - glow_radius, cx + glow_radius, cy + glow_radius],
        fill=(99, 102, 241, 180),
        outline=(251, 191, 36, 255),
        width=3
    )

    # Draw Title & Subtitle banner
    draw.rectangle([60, height // 2 + 280, width - 60, height // 2 + 380], fill=(15, 23, 42, 220), outline=(56, 189, 248, 180), width=2)

    # Draw text with system font or basic shapes
    try:
        font = ImageFont.truetype("arial.ttf", 36)
        sub_font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    draw.text((80, height // 2 + 295), title[:30].upper(), fill=(255, 255, 255), font=font)
    draw.text((80, height // 2 + 342), subtitle[:45], fill=(251, 191, 36), font=sub_font)

    if output_path:
        img.convert("RGB").save(output_path, "JPEG", quality=95)

    return img
