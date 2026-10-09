"""
Character Manager — Shared Animation Engine
Manages character assets, visual continuity, and procedural rendering of 2D characters
with swappable expressions, eye blinks, talking mouth shapes, walking legs, and arm gestures.
Supports Kids (cute, expressive, colorful) and Elders (dignified, warm, gentle).
"""
import math
from typing import Dict, Any, Tuple
from PIL import Image, ImageDraw


class CharacterManager:
    """Renders consistent, high-resolution layered 2D puppet characters."""

    def __init__(self):
        self._cache: Dict[str, Image.Image] = {}

    def get_character_frame(
        self,
        character_id: str = "host",
        style: str = "kids",
        mouth_open_pct: float = 0.0,
        eye_blink_pct: float = 0.0,
        head_tilt_deg: float = 0.0,
        gesture: str = "none",
        motion: str = "idle_breathe",
        walk_cycle: float = 0.0,
        target_size: Tuple[int, int] = (450, 560)
    ) -> Image.Image:
        """
        Render a clean, high-resolution character sprite with talking mouth,
        expressive features, gestured arms, and walking legs.
        """
        w, h = target_size
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx = w // 2
        cy = int(h * 0.44)

        if style == "kids" or style in ("pip_bunny", "barnaby_bear", "ollie_owl", "sparky"):
            from kids.characters import kids_characters
            char_key = style if style != "kids" else character_id
            kids_characters.render_character(
                character_id=char_key,
                cx=cx,
                cy=cy,
                w=w,
                h=h,
                draw=draw,
                mouth_open=mouth_open_pct,
                blink=eye_blink_pct,
                gesture=gesture,
                motion=motion,
                walk_cycle=walk_cycle
            )
        else:
            self._render_elders_character(
                draw, cx, cy, w, h, mouth_open_pct, eye_blink_pct, gesture, motion, walk_cycle
            )

        # Apply head tilt if needed
        if abs(head_tilt_deg) > 0.5:
            img = img.rotate(head_tilt_deg, resample=Image.BILINEAR, center=(cx, cy + 40))

        return img

    def _render_kids_character(
        self,
        draw: ImageDraw.ImageDraw,
        cx: int,
        cy: int,
        w: int,
        h: int,
        mouth_open: float,
        blink: float,
        gesture: str,
        motion: str,
        walk_cycle: float
    ):
        """Draw cute cheerful young mascot / kid explorer with legs and gestured arms."""
        body_top = cy + 45
        body_bottom = body_top + 150

        # 0. Walking Legs & Sneakers
        leg_offset = 0
        if motion == "walk_in" or walk_cycle != 0.0:
            leg_offset = int(math.sin(walk_cycle * 2 * math.pi) * 18)

        # Left leg & shoe
        draw.rounded_rectangle([cx - 55 + leg_offset, body_bottom - 10, cx - 25 + leg_offset, body_bottom + 65], radius=10, fill=(30, 58, 138))
        draw.ellipse([cx - 65 + leg_offset, body_bottom + 50, cx - 15 + leg_offset, body_bottom + 75], fill=(239, 68, 68), outline=(185, 28, 28), width=2)
        # Right leg & shoe
        draw.rounded_rectangle([cx + 25 - leg_offset, body_bottom - 10, cx + 55 - leg_offset, body_bottom + 65], radius=10, fill=(30, 58, 138))
        draw.ellipse([cx + 15 - leg_offset, body_bottom + 50, cx + 65 - leg_offset, body_bottom + 75], fill=(239, 68, 68), outline=(185, 28, 28), width=2)

        # 1. Torso / Bright Hoodie
        draw.rounded_rectangle([cx - 75, body_top, cx + 75, body_bottom], radius=28, fill=(249, 115, 22), outline=(194, 65, 12), width=3)
        # Yellow star badge
        draw.ellipse([cx - 18, body_top + 30, cx + 18, body_top + 66], fill=(253, 224, 71), outline=(234, 179, 8), width=2)

        # 2. Arms & Gestures
        if gesture in ("wave", "celebrate"):
            # Left arm up waving
            draw.line([(cx - 70, body_top + 20), (cx - 110, body_top - 40)], fill=(249, 115, 22), width=22)
            draw.ellipse([cx - 125, body_top - 55, cx - 95, body_top - 25], fill=(254, 215, 170), outline=(194, 65, 12), width=2)
            # Right arm down
            draw.line([(cx + 70, body_top + 20), (cx + 95, body_top + 80)], fill=(249, 115, 22), width=22)
            draw.ellipse([cx + 85, body_top + 70, cx + 110, body_top + 95], fill=(254, 215, 170))
        elif gesture in ("hold_prop", "point"):
            # Right arm extended forward pointing / holding
            draw.line([(cx + 70, body_top + 20), (cx + 120, body_top + 20)], fill=(249, 115, 22), width=22)
            draw.ellipse([cx + 110, body_top + 5, cx + 135, body_top + 35], fill=(254, 215, 170), outline=(194, 65, 12), width=2)
            # Left arm relaxed
            draw.line([(cx - 70, body_top + 20), (cx - 95, body_top + 80)], fill=(249, 115, 22), width=22)
            draw.ellipse([cx - 110, body_top + 70, cx - 85, body_top + 95], fill=(254, 215, 170))
        else:
            # Idle arms by side
            draw.line([(cx - 70, body_top + 20), (cx - 95, body_top + 80)], fill=(249, 115, 22), width=22)
            draw.ellipse([cx - 110, body_top + 70, cx - 85, body_top + 95], fill=(254, 215, 170))
            draw.line([(cx + 70, body_top + 20), (cx + 95, body_top + 80)], fill=(249, 115, 22), width=22)
            draw.ellipse([cx + 85, body_top + 70, cx + 110, body_top + 95], fill=(254, 215, 170))

        # 3. Head / Face
        head_r = 85
        head_cy = cy - 35
        # Warm skin tone
        draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r], fill=(254, 215, 170), outline=(249, 115, 22), width=3)

        # 4. Fluffy hair / Cap
        draw.chord([cx - head_r - 5, head_cy - head_r - 15, cx + head_r + 5, head_cy], start=180, end=360, fill=(99, 102, 241), outline=(67, 56, 202), width=3)
        # Cap brim
        draw.arc([cx - head_r, head_cy - 40, cx + head_r + 20, head_cy], start=160, end=360, fill=(67, 56, 202), width=6)

        # 5. Big Expressive Eyes
        eye_y = head_cy - 8
        eye_w, eye_h = 24, int(28 * (1.0 - blink * 0.9))
        for eye_x in (cx - 34, cx + 34):
            if blink > 0.7:
                # Closed happy curve
                draw.arc([eye_x - 14, eye_y - 6, eye_x + 14, eye_y + 12], start=180, end=360, fill=(30, 41, 59), width=4)
            else:
                draw.ellipse([eye_x - eye_w // 2, eye_y - eye_h // 2, eye_x + eye_w // 2, eye_y + eye_h // 2], fill=(255, 255, 255), outline=(30, 41, 59), width=2)
                draw.ellipse([eye_x - 7, eye_y - 7, eye_x + 7, eye_y + 7], fill=(59, 130, 246))
                draw.ellipse([eye_x - 4, eye_y - 4, eye_x + 4, eye_y + 4], fill=(15, 23, 42))
                draw.ellipse([eye_x - 2, eye_y - 5, eye_x + 3, eye_y], fill=(255, 255, 255))

        # Rosy cheeks
        draw.ellipse([cx - 62, head_cy + 15, cx - 40, head_cy + 30], fill=(251, 146, 60, 160))
        draw.ellipse([cx + 40, head_cy + 15, cx + 62, head_cy + 30], fill=(251, 146, 60, 160))

        # 6. Talking Animated Mouth
        mouth_y = head_cy + 35
        m_open = int(mouth_open * 22)
        if m_open > 3:
            draw.ellipse([cx - 18, mouth_y - 2, cx + 18, mouth_y + m_open], fill=(185, 28, 28), outline=(127, 29, 29), width=2)
            draw.chord([cx - 12, mouth_y + m_open - 10, cx + 12, mouth_y + m_open], start=0, end=180, fill=(244, 114, 182))
        else:
            draw.arc([cx - 20, mouth_y - 10, cx + 20, mouth_y + 12], start=20, end=160, fill=(185, 28, 28), width=3)

    def _render_elders_character(
        self,
        draw: ImageDraw.ImageDraw,
        cx: int,
        cy: int,
        w: int,
        h: int,
        mouth_open: float,
        blink: float,
        gesture: str,
        motion: str,
        walk_cycle: float
    ):
        """Draw dignified, gentle, wise elder storyteller with sitting armchair option or walking legs."""
        body_top = cy + 45
        body_bottom = body_top + 160

        is_sitting = (motion == "sit")

        # Armchair if sitting
        if is_sitting:
            # Cozy armchair back & cushion
            draw.rounded_rectangle([cx - 110, body_top - 20, cx + 110, body_bottom + 80], radius=35, fill=(67, 20, 7), outline=(41, 12, 4), width=4)
            # Armrests
            draw.rounded_rectangle([cx - 130, body_top + 50, cx - 90, body_bottom + 50], radius=15, fill=(120, 53, 15), outline=(67, 20, 7), width=3)
            draw.rounded_rectangle([cx + 90, body_top + 50, cx + 130, body_bottom + 50], radius=15, fill=(120, 53, 15), outline=(67, 20, 7), width=3)
            # Legs crossed / resting
            draw.rounded_rectangle([cx - 60, body_bottom - 20, cx + 60, body_bottom + 50], radius=15, fill=(51, 65, 85))
            draw.ellipse([cx - 50, body_bottom + 40, cx - 10, body_bottom + 70], fill=(24, 24, 27))
            draw.ellipse([cx + 10, body_bottom + 40, cx + 50, body_bottom + 70], fill=(24, 24, 27))
        else:
            # Walking / Standing slacks
            leg_offset = 0
            if motion == "walk_in" or walk_cycle != 0.0:
                leg_offset = int(math.sin(walk_cycle * 2 * math.pi) * 16)
            # Trousers
            draw.rounded_rectangle([cx - 60 + leg_offset, body_bottom - 10, cx - 20 + leg_offset, body_bottom + 70], radius=10, fill=(51, 65, 85))
            draw.ellipse([cx - 68 + leg_offset, body_bottom + 55, cx - 12 + leg_offset, body_bottom + 80], fill=(24, 24, 27))
            draw.rounded_rectangle([cx + 20 - leg_offset, body_bottom - 10, cx + 60 - leg_offset, body_bottom + 70], radius=10, fill=(51, 65, 85))
            draw.ellipse([cx + 12 - leg_offset, body_bottom + 55, cx + 68 - leg_offset, body_bottom + 80], fill=(24, 24, 27))

        # 1. Warm Knit Cardigan / Sweater
        draw.rounded_rectangle([cx - 85, body_top, cx + 85, body_bottom], radius=25, fill=(120, 53, 15), outline=(69, 26, 3), width=3)
        # Cozy knitted scarf
        draw.rounded_rectangle([cx - 45, body_top - 5, cx + 45, body_top + 60], radius=15, fill=(217, 119, 6), outline=(180, 83, 9), width=2)

        # 2. Arms & Gestures
        if gesture in ("hold_prop", "hold_mug"):
            # Arm holding mug/book close to chest
            draw.line([(cx + 70, body_top + 20), (cx + 50, body_top + 70)], fill=(120, 53, 15), width=24)
            draw.ellipse([cx + 35, body_top + 60, cx + 65, body_top + 85], fill=(253, 230, 200))
            draw.line([(cx - 70, body_top + 20), (cx - 95, body_top + 80)], fill=(120, 53, 15), width=24)
            draw.ellipse([cx - 110, body_top + 70, cx - 85, body_top + 95], fill=(253, 230, 200))
        elif gesture in ("wave", "point"):
            # Gentle dignified hand gesture
            draw.line([(cx + 70, body_top + 20), (cx + 115, body_top + 25)], fill=(120, 53, 15), width=24)
            draw.ellipse([cx + 105, body_top + 10, cx + 130, body_top + 40], fill=(253, 230, 200))
            draw.line([(cx - 70, body_top + 20), (cx - 95, body_top + 80)], fill=(120, 53, 15), width=24)
            draw.ellipse([cx - 110, body_top + 70, cx - 85, body_top + 95], fill=(253, 230, 200))
        else:
            # Relaxed arms
            draw.line([(cx - 70, body_top + 20), (cx - 95, body_top + 80)], fill=(120, 53, 15), width=24)
            draw.ellipse([cx - 110, body_top + 70, cx - 85, body_top + 95], fill=(253, 230, 200))
            draw.line([(cx + 70, body_top + 20), (cx + 95, body_top + 80)], fill=(120, 53, 15), width=24)
            draw.ellipse([cx + 85, body_top + 70, cx + 110, body_top + 95], fill=(253, 230, 200))

        # 3. Head / Face
        head_r = 82
        head_cy = cy - 35
        draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r], fill=(253, 230, 200), outline=(161, 98, 7), width=3)

        # 4. Dignified Silver Hair
        draw.chord([cx - head_r - 6, head_cy - head_r - 15, cx + head_r + 6, head_cy - 10], start=180, end=360, fill=(241, 245, 249), outline=(148, 163, 184), width=3)
        draw.ellipse([cx - head_r - 10, head_cy - 20, cx - head_r + 15, head_cy + 25], fill=(241, 245, 249))
        draw.ellipse([cx + head_r - 15, head_cy - 20, cx + head_r + 10, head_cy + 25], fill=(241, 245, 249))

        # 5. Kind Eyes & Round Gold Glasses
        eye_y = head_cy - 5
        glasses_r = 25
        draw.ellipse([cx - 38 - glasses_r, eye_y - glasses_r, cx - 38 + glasses_r, eye_y + glasses_r], outline=(217, 119, 6), width=3)
        draw.ellipse([cx + 38 - glasses_r, eye_y - glasses_r, cx + 38 + glasses_r, eye_y + glasses_r], outline=(217, 119, 6), width=3)
        draw.line([(cx - 13, eye_y), (cx + 13, eye_y)], fill=(217, 119, 6), width=3)

        if blink > 0.6:
            draw.arc([cx - 46, eye_y - 6, cx - 30, eye_y + 10], start=180, end=360, fill=(67, 56, 202), width=3)
            draw.arc([cx + 30, eye_y - 6, cx + 46, eye_y + 10], start=180, end=360, fill=(67, 56, 202), width=3)
        else:
            draw.ellipse([cx - 42, eye_y - 5, cx - 34, eye_y + 5], fill=(30, 41, 59))
            draw.ellipse([cx + 34, eye_y - 5, cx + 42, eye_y + 5], fill=(30, 41, 59))

        # Gentle laugh lines
        draw.arc([cx - 70, eye_y - 4, cx - 60, eye_y + 12], start=220, end=320, fill=(180, 83, 9), width=2)
        draw.arc([cx + 60, eye_y - 4, cx + 70, eye_y + 12], start=220, end=320, fill=(180, 83, 9), width=2)

        # 6. Warm Moustache / Beard hint
        draw.chord([cx - 28, head_cy + 22, cx + 28, head_cy + 42], start=0, end=180, fill=(241, 245, 249), outline=(203, 213, 225), width=2)

        # 7. Talking Animated Mouth
        mouth_y = head_cy + 38
        m_open = int(mouth_open * 16)
        if m_open > 3:
            draw.ellipse([cx - 14, mouth_y - 2, cx + 14, mouth_y + m_open], fill=(136, 19, 55), outline=(76, 5, 25), width=2)
        else:
            draw.arc([cx - 16, mouth_y - 8, cx + 16, mouth_y + 8], start=20, end=160, fill=(136, 19, 55), width=3)


# Global instance
character_manager = CharacterManager()
