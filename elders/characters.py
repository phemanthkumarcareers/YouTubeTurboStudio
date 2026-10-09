"""
Adult Character Pack — Elders Channel
Procedural vector rendering of recurring mature characters:
- Arthur (Wise dignified grandfather in warm cardigan and glasses)
- Eleanor (Gentle matriarch with silver curls and lavender shawl)
- Walter (Reflective artisan in tweed cap and vest)
"""
import math
from typing import Dict, Any, Tuple
from PIL import Image, ImageDraw


class EldersCharacterPack:
    """Renders consistent, dignified adult character sprites."""

    def render_character(
        self,
        character_id: str,
        cx: int,
        cy: int,
        w: int,
        h: int,
        draw: ImageDraw.ImageDraw,
        mouth_open: float = 0.0,
        blink: float = 0.0,
        gesture: str = "none",
        motion: str = "idle_breathe",
        walk_cycle: float = 0.0
    ):
        """Draws selected adult character by ID."""
        char_lower = character_id.lower()

        if "eleanor" in char_lower or "grandma" in char_lower:
            self._render_eleanor(draw, cx, cy, w, h, mouth_open, blink, gesture, motion, walk_cycle)
        elif "walter" in char_lower or "artisan" in char_lower:
            self._render_walter(draw, cx, cy, w, h, mouth_open, blink, gesture, motion, walk_cycle)
        else:
            # Default: Arthur
            self._render_arthur(draw, cx, cy, w, h, mouth_open, blink, gesture, motion, walk_cycle)

    def _render_arthur(
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
        """Arthur: Dignified grandfather with glasses and knitted cardigan."""
        from animation.character_manager import character_manager
        character_manager._render_elders_character(
            draw, cx, cy, w, h, mouth_open, blink, gesture, motion, walk_cycle
        )

    def _render_eleanor(
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
        """Eleanor: Gentle matriarch with silver curls, lavender shawl, kind smile."""
        body_top = cy + 45
        body_bottom = body_top + 160
        is_sitting = (motion == "sit")

        # Armchair if sitting
        if is_sitting:
            # Rosewood vintage armchair
            draw.rounded_rectangle([cx - 110, body_top - 20, cx + 110, body_bottom + 80], radius=35, fill=(88, 28, 28), outline=(69, 10, 10), width=4)
            draw.rounded_rectangle([cx - 130, body_top + 50, cx - 90, body_bottom + 50], radius=15, fill=(120, 53, 15), outline=(69, 26, 3), width=3)
            draw.rounded_rectangle([cx + 90, body_top + 50, cx + 130, body_bottom + 50], radius=15, fill=(120, 53, 15), outline=(69, 26, 3), width=3)
            # Long skirt
            draw.rounded_rectangle([cx - 65, body_bottom - 20, cx + 65, body_bottom + 65], radius=15, fill=(107, 33, 168))
        else:
            # Standing skirt
            draw.rounded_rectangle([cx - 65, body_bottom - 10, cx + 65, body_bottom + 75], radius=12, fill=(107, 33, 168))

        # 1. Lavender Knitted Dress / Blouse
        draw.rounded_rectangle([cx - 80, body_top, cx + 80, body_bottom], radius=25, fill=(147, 51, 234), outline=(107, 33, 168), width=3)
        # Cozy Knitted Shawl (warm soft violet/rose drape)
        draw.rounded_rectangle([cx - 55, body_top - 5, cx + 55, body_bottom - 40], radius=18, fill=(192, 132, 252), outline=(147, 51, 234), width=2)
        # Pearl Brooch
        draw.ellipse([cx - 8, body_top + 25, cx + 8, body_top + 41], fill=(255, 255, 255), outline=(226, 232, 240), width=2)

        # 2. Arms & Gestures
        if gesture in ("hold_prop", "hold_tea"):
            draw.line([(cx + 65, body_top + 20), (cx + 45, body_top + 70)], fill=(147, 51, 234), width=22)
            draw.ellipse([cx + 35, body_top + 60, cx + 60, body_top + 85], fill=(253, 230, 200))
            draw.line([(cx - 65, body_top + 20), (cx - 90, body_top + 75)], fill=(147, 51, 234), width=22)
            draw.ellipse([cx - 105, body_top + 65, cx - 80, body_top + 90], fill=(253, 230, 200))
        elif gesture == "wave":
            draw.line([(cx + 65, body_top + 20), (cx + 105, body_top + 20)], fill=(147, 51, 234), width=22)
            draw.ellipse([cx + 95, body_top + 5, cx + 120, body_top + 30], fill=(253, 230, 200))
            draw.line([(cx - 65, body_top + 20), (cx - 90, body_top + 75)], fill=(147, 51, 234), width=22)
            draw.ellipse([cx - 105, body_top + 65, cx - 80, body_top + 90], fill=(253, 230, 200))
        else:
            draw.line([(cx - 65, body_top + 20), (cx - 90, body_top + 75)], fill=(147, 51, 234), width=22)
            draw.ellipse([cx - 105, body_top + 65, cx - 80, body_top + 90], fill=(253, 230, 200))
            draw.line([(cx + 65, body_top + 20), (cx + 90, body_top + 75)], fill=(147, 51, 234), width=22)
            draw.ellipse([cx + 80, body_top + 65, cx + 105, body_top + 90], fill=(253, 230, 200))

        # 3. Head & Face
        head_r = 78
        head_cy = cy - 35
        draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r], fill=(254, 235, 215), outline=(180, 115, 60), width=3)

        # 4. Elegant Silver Curls Hair
        # Soft curls encircling head
        draw.chord([cx - head_r - 8, head_cy - head_r - 18, cx + head_r + 8, head_cy], start=180, end=360, fill=(241, 245, 249), outline=(203, 213, 225), width=3)
        for offset_x in (-70, -45, -20, 0, 20, 45, 70):
            draw.ellipse([cx + offset_x - 18, head_cy - head_r - 10, cx + offset_x + 18, head_cy - head_r + 20], fill=(241, 245, 249), outline=(203, 213, 225), width=2)

        # Pearl earrings
        draw.ellipse([cx - head_r - 6, head_cy + 10, cx - head_r + 4, head_cy + 20], fill=(255, 255, 255))
        draw.ellipse([cx + head_r - 4, head_cy + 10, cx + head_r + 6, head_cy + 20], fill=(255, 255, 255))

        # 5. Kind Eyes & Crinkle Lines
        eye_y = head_cy - 6
        if blink > 0.6:
            draw.arc([cx - 44, eye_y - 6, cx - 24, eye_y + 10], start=180, end=360, fill=(45, 17, 2), width=3)
            draw.arc([cx + 24, eye_y - 6, cx + 44, eye_y + 10], start=180, end=360, fill=(45, 17, 2), width=3)
        else:
            draw.ellipse([cx - 39, eye_y - 7, cx - 29, eye_y + 5], fill=(55, 65, 81))
            draw.ellipse([cx + 29, eye_y - 7, cx + 39, eye_y + 5], fill=(55, 65, 81))
            draw.ellipse([cx - 36, eye_y - 6, cx - 31, eye_y - 1], fill=(255, 255, 255))
            draw.ellipse([cx + 32, eye_y - 6, cx + 37, eye_y - 1], fill=(255, 255, 255))

        # Gentle laugh lines
        draw.arc([cx - 60, eye_y - 4, cx - 50, eye_y + 12], start=220, end=320, fill=(202, 138, 4), width=2)
        draw.arc([cx + 50, eye_y - 4, cx + 60, eye_y + 12], start=220, end=320, fill=(202, 138, 4), width=2)

        # 6. Gentle Smile
        mouth_y = head_cy + 34
        m_open = int(mouth_open * 14)
        if m_open > 3:
            draw.ellipse([cx - 14, mouth_y - 2, cx + 14, mouth_y + m_open], fill=(159, 18, 57))
        else:
            draw.arc([cx - 16, mouth_y - 8, cx + 16, mouth_y + 8], start=20, end=160, fill=(159, 18, 57), width=3)

    def _render_walter(
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
        """Walter: Artisan with wool flat cap, tweed vest, and thoughtful eyes."""
        body_top = cy + 45
        body_bottom = body_top + 160

        # Tweed vest
        draw.rounded_rectangle([cx - 85, body_top, cx + 85, body_bottom], radius=25, fill=(78, 60, 48), outline=(45, 30, 20), width=3)
        # Shirt collar
        draw.polygon([(cx - 25, body_top), (cx, body_top + 25), (cx + 25, body_top)], fill=(241, 245, 249))

        # Legs
        draw.rounded_rectangle([cx - 60, body_bottom - 10, cx - 20, body_bottom + 70], radius=10, fill=(30, 41, 59))
        draw.rounded_rectangle([cx + 20, body_bottom - 10, cx + 60, body_bottom + 70], radius=10, fill=(30, 41, 59))

        # Head & Cap
        head_r = 80
        head_cy = cy - 35
        draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r], fill=(253, 230, 200), outline=(161, 98, 7), width=3)

        # Classic Tweed Flat Cap
        draw.ellipse([cx - head_r - 12, head_cy - head_r - 20, cx + head_r + 12, head_cy - head_r + 30], fill=(87, 83, 78), outline=(41, 37, 36), width=3)
        draw.arc([cx - head_r - 15, head_cy - head_r + 5, cx + head_r + 25, head_cy - head_r + 35], start=160, end=360, fill=(41, 37, 36), width=8)

        # Kind Eyes
        eye_y = head_cy - 4
        if blink > 0.6:
            draw.arc([cx - 44, eye_y - 6, cx - 26, eye_y + 10], start=180, end=360, fill=(30, 41, 59), width=3)
            draw.arc([cx + 26, eye_y - 6, cx + 44, eye_y + 10], start=180, end=360, fill=(30, 41, 59), width=3)
        else:
            draw.ellipse([cx - 40, eye_y - 5, cx - 30, eye_y + 5], fill=(30, 41, 59))
            draw.ellipse([cx + 30, eye_y - 5, cx + 40, eye_y + 5], fill=(30, 41, 59))

        # Silver Moustache
        draw.chord([cx - 32, head_cy + 18, cx + 32, head_cy + 42], start=0, end=180, fill=(226, 232, 240), outline=(203, 213, 225), width=2)

        # Mouth
        mouth_y = head_cy + 38
        m_open = int(mouth_open * 16)
        if m_open > 3:
            draw.ellipse([cx - 14, mouth_y - 2, cx + 14, mouth_y + m_open], fill=(136, 19, 55))
        else:
            draw.arc([cx - 16, mouth_y - 8, cx + 16, mouth_y + 8], start=20, end=160, fill=(136, 19, 55), width=3)


elders_characters = EldersCharacterPack()
