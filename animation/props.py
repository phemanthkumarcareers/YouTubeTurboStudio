"""
Props Manager — Shared Animation Engine
Procedural and vector rendering of props for both Kids and Elders channels.
Supports dynamic actions: float, held, shimmer, spin.
"""
import math
from typing import Tuple, Dict
from PIL import Image, ImageDraw


class PropsManager:
    """Renders high-resolution scalable 2D props for animation scenes."""

    def __init__(self):
        self._cache: Dict[str, Image.Image] = {}

    def get_prop_frame(
        self,
        prop_type: str = "star",
        scale: float = 1.0,
        action: str = "float",
        time_sec: float = 0.0,
        base_size: Tuple[int, int] = (240, 240)
    ) -> Image.Image:
        """
        Renders prop sprite with procedural animation (hover, shimmer, steam).
        """
        w, h = base_size
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx, cy = w // 2, h // 2

        # Draw base prop by type
        if prop_type in ("star", "gold_star"):
            self._render_star(draw, cx, cy, 60, time_sec)
        elif prop_type in ("magnifying_glass", "lens"):
            self._render_magnifying_glass(draw, cx, cy, time_sec)
        elif prop_type in ("rocket", "toy_rocket"):
            self._render_rocket(draw, cx, cy, time_sec)
        elif prop_type in ("book", "storybook"):
            self._render_kids_book(draw, cx, cy)
        elif prop_type in ("tea_mug", "steaming_tea", "tea_cup"):
            self._render_tea_mug(draw, cx, cy, time_sec)
        elif prop_type in ("vintage_book", "leather_journal"):
            self._render_vintage_book(draw, cx, cy)
        elif prop_type in ("glasses", "reading_glasses"):
            self._render_reading_glasses(draw, cx, cy)
        elif prop_type in ("clock", "pocket_watch"):
            self._render_pocket_watch(draw, cx, cy, time_sec)
        else:
            # Default cheerful orb / prop
            self._render_default_prop(draw, cx, cy, time_sec)

        # Apply procedural action effects
        if action == "shimmer":
            # Add shimmer sparkle
            sparkle_alpha = int(120 + 80 * math.sin(time_sec * 6.0))
            draw.ellipse([cx - 50, cy - 50, cx - 35, cy - 35], fill=(255, 255, 255, sparkle_alpha))
            draw.ellipse([cx + 35, cy + 30, cx + 45, cy + 40], fill=(255, 255, 255, sparkle_alpha))

        # Scaling
        if scale != 1.0 and scale > 0.1:
            target_w = max(10, int(w * scale))
            target_h = max(10, int(h * scale))
            img = img.resize((target_w, target_h), resample=Image.BICUBIC)

        return img

    def _render_star(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, t: float):
        """Cute 5-pointed glowing cartoon star."""
        points = []
        inner_r = r * 0.45
        rot_offset = math.sin(t * 3.0) * 0.1  # subtle breathing wobble
        for i in range(10):
            angle = i * (math.pi / 5) - (math.pi / 2) + rot_offset
            curr_r = r if i % 2 == 0 else inner_r
            px = cx + curr_r * math.cos(angle)
            py = cy + curr_r * math.sin(angle)
            points.append((px, py))

        # Star body
        draw.polygon(points, fill=(253, 224, 71), outline=(217, 119, 6))
        # Cute happy face on star
        draw.ellipse([cx - 15, cy - 5, cx - 7, cy + 5], fill=(30, 41, 59))
        draw.ellipse([cx + 7, cy - 5, cx + 15, cy + 5], fill=(30, 41, 59))
        draw.arc([cx - 10, cy + 2, cx + 10, cy + 16], start=20, end=160, fill=(225, 29, 72), width=3)

    def _render_magnifying_glass(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float):
        """Magnifying glass with wooden handle and glassy shine."""
        # Handle
        draw.line([(cx + 25, cy + 25), (cx + 65, cy + 65)], fill=(120, 53, 15), width=16)
        draw.line([(cx + 25, cy + 25), (cx + 65, cy + 65)], fill=(180, 83, 9), width=10)
        # Rim
        draw.ellipse([cx - 50, cy - 50, cx + 25, cy + 25], outline=(202, 138, 4), width=8)
        # Glass fill
        draw.ellipse([cx - 46, cy - 46, cx + 21, cy + 21], fill=(224, 242, 254, 180))
        # Specular shine curve
        draw.arc([cx - 40, cy - 40, cx + 15, cy + 15], start=190, end=270, fill=(255, 255, 255, 220), width=4)

    def _render_rocket(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float):
        """Toy cartoon rocket with fins and window."""
        # Fins
        draw.polygon([(cx - 45, cy + 40), (cx - 20, cy + 10), (cx - 20, cy + 40)], fill=(220, 38, 38))
        draw.polygon([(cx + 45, cy + 40), (cx + 20, cy + 10), (cx + 20, cy + 40)], fill=(220, 38, 38))
        # Body
        draw.rounded_rectangle([cx - 22, cy - 45, cx + 22, cy + 40], radius=15, fill=(241, 245, 249), outline=(148, 163, 184), width=3)
        # Nose cone
        draw.polygon([(cx - 22, cy - 35), (cx, cy - 65), (cx + 22, cy - 35)], fill=(220, 38, 38))
        # Window
        draw.ellipse([cx - 12, cy - 15, cx + 12, cy + 9], fill=(59, 130, 246), outline=(30, 58, 138), width=3)

    def _render_kids_book(self, draw: ImageDraw.ImageDraw, cx: int, cy: int):
        """Colorful open storybook."""
        # Pages
        draw.polygon([(cx - 50, cy - 25), (cx - 5, cy - 20), (cx - 5, cy + 30), (cx - 50, cy + 25)], fill=(254, 240, 138), outline=(202, 138, 4), width=2)
        draw.polygon([(cx + 5, cy - 20), (cx + 50, cy - 25), (cx + 50, cy + 25), (cx + 5, cy + 30)], fill=(254, 240, 138), outline=(202, 138, 4), width=2)
        # Cover edge
        draw.line([(cx - 52, cy + 27), (cx, cy + 33), (cx + 52, cy + 27)], fill=(234, 88, 12), width=5)

    def _render_tea_mug(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float):
        """Elders cozy ceramic mug with procedural rising steam swirls."""
        # Mug Handle
        draw.arc([cx + 20, cy - 15, cx + 55, cy + 25], start=270, end=90, fill=(180, 83, 9), width=8)
        # Mug Body
        draw.rounded_rectangle([cx - 35, cy - 25, cx + 25, cy + 35], radius=10, fill=(254, 243, 199), outline=(180, 83, 9), width=4)
        # Warm tea rim
        draw.ellipse([cx - 32, cy - 28, cx + 22, cy - 18], fill=(120, 53, 15))

        # Rising Steam (procedural wave animation)
        for i, offset_x in enumerate((-15, 0, 15)):
            steam_phase = (t * 2.5 + i * 0.8) % 3.0
            steam_y = cy - 35 - (steam_phase * 15)
            steam_alpha = max(0, int(180 * (1.0 - (steam_phase / 3.0))))
            wave_x = cx + offset_x + int(math.sin(t * 4.0 + i) * 6)
            draw.arc([wave_x - 8, int(steam_y) - 10, wave_x + 8, int(steam_y) + 10], start=180, end=360, fill=(226, 232, 240, steam_alpha), width=3)

    def _render_vintage_book(self, draw: ImageDraw.ImageDraw, cx: int, cy: int):
        """Leather-bound gold-embossed journal for Elders."""
        # Spine & Cover
        draw.rounded_rectangle([cx - 45, cy - 35, cx + 45, cy + 35], radius=8, fill=(88, 28, 28), outline=(202, 138, 4), width=3)
        # Gold bookmark ribbon
        draw.line([(cx - 10, cy - 35), (cx - 10, cy + 42)], fill=(234, 179, 8), width=4)
        # Gold spine bands
        draw.line([(cx - 30, cy - 25), (cx - 30, cy + 25)], fill=(202, 138, 4), width=2)
        # Gold seal
        draw.ellipse([cx + 5, cy - 10, cx + 25, cy + 10], outline=(202, 138, 4), width=2)

    def _render_reading_glasses(self, draw: ImageDraw.ImageDraw, cx: int, cy: int):
        """Classic tortoiseshell / gold glasses."""
        r = 24
        draw.ellipse([cx - 35 - r, cy - r, cx - 35 + r, cy + r], outline=(180, 83, 9), width=4)
        draw.ellipse([cx + 35 - r, cy - r, cx + 35 + r, cy + r], outline=(180, 83, 9), width=4)
        draw.line([(cx - 11, cy), (cx + 11, cy)], fill=(180, 83, 9), width=4)
        # Side arms
        draw.line([(cx - 59, cy), (cx - 80, cy - 15)], fill=(120, 53, 15), width=3)
        draw.line([(cx + 59, cy), (cx + 80, cy - 15)], fill=(120, 53, 15), width=3)

    def _render_pocket_watch(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float):
        """Brass pocket watch with moving hands."""
        # Top ring
        draw.ellipse([cx - 10, cy - 48, cx + 10, cy - 28], outline=(217, 119, 6), width=4)
        # Outer casing
        draw.ellipse([cx - 40, cy - 30, cx + 40, cy + 50], fill=(254, 240, 138), outline=(217, 119, 6), width=5)
        # Dial
        draw.ellipse([cx - 32, cy - 22, cx + 32, cy + 42], fill=(255, 255, 255), outline=(148, 163, 184), width=2)
        # Hands
        hour_angle = (t * 0.2) % (2 * math.pi)
        min_angle = (t * 2.0) % (2 * math.pi)
        center_y = cy + 10
        draw.line([(cx, center_y), (cx + 14 * math.cos(hour_angle), center_y + 14 * math.sin(hour_angle))], fill=(30, 41, 59), width=3)
        draw.line([(cx, center_y), (cx + 22 * math.cos(min_angle), center_y + 22 * math.sin(min_angle))], fill=(225, 29, 72), width=2)

    def _render_default_prop(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, t: float):
        """Generic cheerful animated floating badge."""
        draw.ellipse([cx - 35, cy - 35, cx + 35, cy + 35], fill=(59, 130, 246), outline=(30, 64, 175), width=4)
        draw.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=(255, 255, 255))


# Global props manager
props_manager = PropsManager()
