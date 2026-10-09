"""
Kids Recurring Characters — Original Character Packs
Defines and renders original recurring characters for Kids Wonder Lab:
- Sparky (Curious young explorer)
- Pip Bunny (Fluffy white bunny with blue bowtie)
- Barnaby Bear (Warm cuddly teddy bear in green knit vest)
- Ollie Owl (Wise curious owl with golden spectacles)
"""
import math
from typing import Dict, Any, Tuple
from PIL import Image, ImageDraw


class KidsCharacterPack:
    """Renders consistent, high-resolution original characters for Kids."""

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
        """Draws the selected character by ID."""
        char_lower = character_id.lower()

        if "bunny" in char_lower or "pip" in char_lower:
            self._render_pip_bunny(draw, cx, cy, w, h, mouth_open, blink, gesture, motion, walk_cycle)
        elif "bear" in char_lower or "barnaby" in char_lower:
            self._render_barnaby_bear(draw, cx, cy, w, h, mouth_open, blink, gesture, motion, walk_cycle)
        elif "owl" in char_lower or "ollie" in char_lower:
            self._render_ollie_owl(draw, cx, cy, w, h, mouth_open, blink, gesture, motion, walk_cycle)
        else:
            # Default: Sparky
            self._render_sparky(draw, cx, cy, w, h, mouth_open, blink, gesture, motion, walk_cycle)

    def _render_pip_bunny(
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
        """Pip Bunny: fluffy white bunny with pink ear inners and blue bowtie."""
        body_top = cy + 45
        body_bottom = body_top + 140

        leg_offset = int(math.sin(walk_cycle * 2 * math.pi) * 16) if (motion == "walk_in" or walk_cycle != 0.0) else 0

        # Paws / Feet
        draw.ellipse([cx - 60 + leg_offset, body_bottom - 10, cx - 15 + leg_offset, body_bottom + 45], fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        draw.ellipse([cx + 15 - leg_offset, body_bottom - 10, cx + 60 - leg_offset, body_bottom + 45], fill=(255, 255, 255), outline=(226, 232, 240), width=2)

        # Fluffy Body
        draw.ellipse([cx - 70, body_top, cx + 70, body_bottom], fill=(255, 255, 255), outline=(226, 232, 240), width=3)
        # Soft pink tummy patch
        draw.ellipse([cx - 40, body_top + 30, cx + 40, body_bottom - 20], fill=(254, 242, 242))

        # Blue Bowtie
        draw.polygon([(cx - 30, body_top + 10), (cx, body_top + 25), (cx - 30, body_top + 40)], fill=(59, 130, 246))
        draw.polygon([(cx + 30, body_top + 10), (cx, body_top + 25), (cx + 30, body_top + 40)], fill=(59, 130, 246))
        draw.ellipse([cx - 10, body_top + 15, cx + 10, body_top + 35], fill=(29, 78, 216))

        # Fluffy Round Head
        head_r = 75
        head_cy = cy - 30

        # Long Floppy Ears
        # Left Ear
        draw.ellipse([cx - 55, head_cy - 160, cx - 15, head_cy - 10], fill=(255, 255, 255), outline=(226, 232, 240), width=3)
        draw.ellipse([cx - 45, head_cy - 140, cx - 25, head_cy - 30], fill=(251, 207, 232))
        # Right Ear
        draw.ellipse([cx + 15, head_cy - 160, cx + 55, head_cy - 10], fill=(255, 255, 255), outline=(226, 232, 240), width=3)
        draw.ellipse([cx + 25, head_cy - 140, cx + 45, head_cy - 30], fill=(251, 207, 232))

        # Head circle
        draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r], fill=(255, 255, 255), outline=(226, 232, 240), width=3)

        # Big Cute Bunny Eyes
        eye_y = head_cy - 8
        for eye_x in (cx - 30, cx + 30):
            if blink > 0.6:
                draw.arc([eye_x - 12, eye_y - 4, eye_x + 12, eye_y + 10], start=180, end=360, fill=(30, 41, 59), width=3)
            else:
                draw.ellipse([eye_x - 12, eye_y - 14, eye_x + 12, eye_y + 14], fill=(30, 41, 59))
                # Catchlight
                draw.ellipse([eye_x - 6, eye_y - 10, eye_x + 4, eye_y], fill=(255, 255, 255))

        # Rosy Cheeks
        draw.ellipse([cx - 55, head_cy + 10, cx - 35, head_cy + 25], fill=(251, 146, 60, 150))
        draw.ellipse([cx + 35, head_cy + 10, cx + 55, head_cy + 25], fill=(251, 146, 60, 150))

        # Cute Pink Nose
        draw.polygon([(cx - 8, head_cy + 15), (cx + 8, head_cy + 15), (cx, head_cy + 24)], fill=(244, 114, 182))

        # Mouth
        mouth_y = head_cy + 30
        m_open = int(mouth_open * 18)
        if m_open > 3:
            draw.ellipse([cx - 14, mouth_y - 2, cx + 14, mouth_y + m_open], fill=(225, 29, 72))
        else:
            draw.arc([cx - 16, mouth_y - 8, cx, mouth_y + 8], start=20, end=160, fill=(71, 85, 105), width=2)
            draw.arc([cx, mouth_y - 8, cx + 16, mouth_y + 8], start=20, end=160, fill=(71, 85, 105), width=2)

    def _render_barnaby_bear(
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
        """Barnaby Bear: warm cuddly brown bear in green vest."""
        body_top = cy + 45
        body_bottom = body_top + 150

        # Cuddly Brown Fur
        bear_brown = (146, 64, 14)
        bear_light = (217, 119, 6)

        # Vest & Body
        draw.rounded_rectangle([cx - 80, body_top, cx + 80, body_bottom], radius=35, fill=(16, 185, 129), outline=(5, 150, 105), width=3)
        # Gold button
        draw.ellipse([cx - 8, body_top + 45, cx + 8, body_top + 61], fill=(253, 224, 71))

        # Bear Head
        head_r = 82
        head_cy = cy - 35

        # Round Bear Ears
        draw.ellipse([cx - 85, head_cy - 95, cx - 35, head_cy - 45], fill=bear_brown)
        draw.ellipse([cx - 72, head_cy - 82, cx - 48, head_cy - 58], fill=bear_light)
        draw.ellipse([cx + 35, head_cy - 95, cx + 85, head_cy - 45], fill=bear_brown)
        draw.ellipse([cx + 48, head_cy - 82, cx + 72, head_cy - 58], fill=bear_light)

        # Head circle
        draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r], fill=bear_brown, outline=(120, 53, 15), width=3)

        # Light Muzzle
        draw.ellipse([cx - 45, head_cy + 5, cx + 45, head_cy + 55], fill=bear_light)
        # Bear Nose
        draw.ellipse([cx - 15, head_cy + 10, cx + 15, head_cy + 28], fill=(24, 24, 27))

        # Bear Eyes
        eye_y = head_cy - 12
        for eye_x in (cx - 32, cx + 32):
            if blink > 0.6:
                draw.arc([eye_x - 10, eye_y - 4, eye_x + 10, eye_y + 8], start=180, end=360, fill=(24, 24, 27), width=3)
            else:
                draw.ellipse([eye_x - 10, eye_y - 10, eye_x + 10, eye_y + 10], fill=(24, 24, 27))
                draw.ellipse([eye_x - 4, eye_y - 6, eye_x + 4, eye_y + 2], fill=(255, 255, 255))

        # Animated Mouth
        mouth_y = head_cy + 34
        m_open = int(mouth_open * 18)
        if m_open > 3:
            draw.ellipse([cx - 14, mouth_y - 2, cx + 14, mouth_y + m_open], fill=(185, 28, 28))
        else:
            draw.arc([cx - 16, mouth_y - 6, cx + 16, mouth_y + 10], start=20, end=160, fill=(24, 24, 27), width=3)

    def _render_ollie_owl(
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
        """Ollie Owl: wise cute periwinkle feathered owl with spectacles."""
        body_top = cy + 40
        body_bottom = body_top + 145

        # Feathers
        owl_blue = (79, 70, 229)
        owl_chest = (199, 210, 254)

        # Body
        draw.ellipse([cx - 75, body_top, cx + 75, body_bottom], fill=owl_blue, outline=(67, 56, 202), width=3)
        draw.ellipse([cx - 45, body_top + 25, cx + 45, body_bottom - 15], fill=owl_chest)

        # Head
        head_r = 75
        head_cy = cy - 35
        draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r], fill=owl_blue, outline=(67, 56, 202), width=3)

        # Feather Tuft Ears
        draw.polygon([(cx - 65, head_cy - 90), (cx - 40, head_cy - 60), (cx - 20, head_cy - 75)], fill=owl_blue)
        draw.polygon([(cx + 65, head_cy - 90), (cx + 40, head_cy - 60), (cx + 20, head_cy - 75)], fill=owl_blue)

        # Big Round Eyes & Glasses
        eye_y = head_cy - 5
        g_r = 28
        draw.ellipse([cx - 32 - g_r, eye_y - g_r, cx - 32 + g_r, eye_y + g_r], outline=(234, 179, 8), width=3)
        draw.ellipse([cx + 32 - g_r, eye_y - g_r, cx + 32 + g_r, eye_y + g_r], outline=(234, 179, 8), width=3)
        draw.line([(cx - 4, eye_y), (cx + 4, eye_y)], fill=(234, 179, 8), width=3)

        for eye_x in (cx - 32, cx + 32):
            if blink > 0.6:
                draw.arc([eye_x - 14, eye_y - 5, eye_x + 14, eye_y + 9], start=180, end=360, fill=(30, 41, 59), width=3)
            else:
                draw.ellipse([eye_x - 16, eye_y - 16, eye_x + 16, eye_y + 16], fill=(255, 255, 255))
                draw.ellipse([eye_x - 10, eye_y - 10, eye_x + 10, eye_y + 10], fill=(234, 179, 8))
                draw.ellipse([eye_x - 6, eye_y - 6, eye_x + 6, eye_y + 6], fill=(15, 23, 42))

        # Little Orange Beak
        beak_y = head_cy + 22
        m_open = int(mouth_open * 12)
        draw.polygon([(cx - 10, beak_y), (cx + 10, beak_y), (cx, beak_y + 14 + m_open)], fill=(249, 115, 22))

    def _render_sparky(
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
        """Sparky: the boy explorer mascot from Phase 3."""
        from animation.character_manager import character_manager
        character_manager._render_kids_character(
            draw, cx, cy, w, h, mouth_open, blink, gesture, motion, walk_cycle
        )


kids_characters = KidsCharacterPack()
