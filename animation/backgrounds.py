"""
Backgrounds Generator — Shared Animation Engine
Procedural rendering of 1080p high-resolution animated environments
tailored for Kids (cheerful, bright, playful) and Elders (warm, cozy, dignified).
"""
import math
from typing import Tuple, Dict
from PIL import Image, ImageDraw


class BackgroundGenerator:
    """Renders lush 2D layered background environments."""

    def __init__(self):
        self._bg_cache: Dict[str, Image.Image] = {}

    def render_background(
        self,
        style: str = "vibrant_sky",
        width: int = 1080,
        height: int = 1920,
        time_sec: float = 0.0
    ) -> Image.Image:
        """
        Renders a full-resolution background for the given style and timestamp.
        """
        img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Dispatch by style
        if style in ("vibrant_sky", "sunny_day"):
            self._draw_vibrant_sky(draw, width, height, time_sec)
        elif style in ("playful_park", "park"):
            self._draw_playful_park(draw, width, height, time_sec)
        elif style in ("starry_space", "space"):
            self._draw_starry_space(draw, width, height, time_sec)
        elif style in ("chalkboard", "classroom"):
            self._draw_chalkboard(draw, width, height)
        elif style in ("cozy_study", "study"):
            self._draw_cozy_study(draw, width, height, time_sec)
        elif style in ("sunset_porch", "sunset"):
            self._draw_sunset_porch(draw, width, height, time_sec)
        elif style in ("warm_hearth", "fireplace"):
            self._draw_warm_hearth(draw, width, height, time_sec)
        elif style in ("library", "classic_library"):
            self._draw_library(draw, width, height)
        else:
            # Default soft gradient
            self._draw_gradient(draw, width, height, (30, 41, 59), (15, 23, 42))

        return img

    def _draw_gradient(self, draw: ImageDraw.ImageDraw, w: int, h: int, top_rgb: tuple, bot_rgb: tuple):
        """Fast linear vertical gradient."""
        # Draw gradient in slices for performance
        steps = min(h, 240)
        slice_h = h / steps
        for i in range(steps):
            ratio = i / float(steps)
            r = int(top_rgb[0] * (1.0 - ratio) + bot_rgb[0] * ratio)
            g = int(top_rgb[1] * (1.0 - ratio) + bot_rgb[1] * ratio)
            b = int(top_rgb[2] * (1.0 - ratio) + bot_rgb[2] * ratio)
            y1 = int(i * slice_h)
            y2 = int((i + 1) * slice_h) + 1
            draw.rectangle([0, y1, w, y2], fill=(r, g, b, 255))

    def _draw_vibrant_sky(self, draw: ImageDraw.ImageDraw, w: int, h: int, t: float):
        """Kids: Bright daytime sky with rolling green hill and drifting clouds."""
        # Sky gradient
        self._draw_gradient(draw, w, h, (56, 189, 248), (224, 242, 254))

        # Cheerful Sun in top corner
        sun_x, sun_y = int(w * 0.85), int(h * 0.12)
        sun_r = int(min(w, h) * 0.10)
        # Sun rays pulse
        pulse = 1.0 + 0.05 * math.sin(t * 3.0)
        draw.ellipse([sun_x - sun_r * pulse, sun_y - sun_r * pulse, sun_x + sun_r * pulse, sun_y + sun_r * pulse], fill=(254, 240, 138, 120))
        draw.ellipse([sun_x - sun_r * 0.7, sun_y - sun_r * 0.7, sun_x + sun_r * 0.7, sun_y + sun_r * 0.7], fill=(253, 224, 71, 255))

        # Fluffy drifting clouds
        cloud_y1 = int(h * 0.18)
        cloud_x1 = int((w * 0.2 + t * 15) % (w + 200)) - 100
        self._draw_cloud(draw, cloud_x1, cloud_y1, 120, 60)

        cloud_y2 = int(h * 0.28)
        cloud_x2 = int((w * 0.6 + t * 25) % (w + 250)) - 120
        self._draw_cloud(draw, cloud_x2, cloud_y2, 160, 80)

        # Rolling Emerald Green Hills
        hill_top = int(h * 0.70)
        draw.chord([-int(w * 0.3), hill_top - 120, int(w * 0.9), h + 200], start=180, end=360, fill=(74, 222, 128))
        draw.chord([int(w * 0.2), hill_top - 80, int(w * 1.4), h + 200], start=180, end=360, fill=(34, 197, 94))
        # Ground base
        draw.rectangle([0, int(h * 0.78), w, h], fill=(22, 163, 74))

    def _draw_cloud(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
        """Draw a pill-shaped fluffy cartoon cloud."""
        draw.ellipse([x, y, x + int(w * 0.6), y + h], fill=(255, 255, 255, 230))
        draw.ellipse([x + int(w * 0.3), y - int(h * 0.3), x + int(w * 0.8), y + h], fill=(255, 255, 255, 230))
        draw.ellipse([x + int(w * 0.5), y, x + w, y + h], fill=(255, 255, 255, 230))

    def _draw_playful_park(self, draw: ImageDraw.ImageDraw, w: int, h: int, t: float):
        """Kids: Sunny park with stylized cartoon trees."""
        self._draw_vibrant_sky(draw, w, h, t)
        # Stylized cartoon trees
        tree_y = int(h * 0.75)
        # Trunk
        draw.rectangle([int(w * 0.12), tree_y - 120, int(w * 0.16), tree_y], fill=(120, 53, 15))
        # Foliage
        draw.ellipse([int(w * 0.06), tree_y - 240, int(w * 0.22), tree_y - 90], fill=(16, 185, 129))

        # Second tree right
        draw.rectangle([int(w * 0.84), tree_y - 100, int(w * 0.88), tree_y], fill=(120, 53, 15))
        draw.ellipse([int(w * 0.78), tree_y - 210, int(w * 0.94), tree_y - 80], fill=(5, 150, 105))

    def _draw_starry_space(self, draw: ImageDraw.ImageDraw, w: int, h: int, t: float):
        """Kids: Magical deep indigo space with glowing stars."""
        self._draw_gradient(draw, w, h, (15, 23, 42), (59, 7, 100))
        # Twinkling stars
        for i in range(25):
            sx = int((w * (0.05 + 0.9 * ((i * 37) % 100) / 100.0)))
            sy = int((h * (0.05 + 0.7 * ((i * 53) % 100) / 100.0)))
            twinkle = (math.sin(t * 4.0 + i) + 1.0) * 0.5
            sr = int(3 + 3 * twinkle)
            draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(254, 240, 138, int(150 + 105 * twinkle)))

    def _draw_chalkboard(self, draw: ImageDraw.ImageDraw, w: int, h: int):
        """Kids: Warm dark green chalkboard frame."""
        # Wooden border
        draw.rectangle([0, 0, w, h], fill=(146, 64, 14))
        border = int(min(w, h) * 0.04)
        # Blackboard surface
        draw.rectangle([border, border, w - border, h - border], fill=(20, 83, 45))

    def _draw_cozy_study(self, draw: ImageDraw.ImageDraw, w: int, h: int, t: float):
        """Elders: Warm mahogany study, bookshelf, warm ambient light, parquet floor."""
        # Warm room wall
        self._draw_gradient(draw, w, h, (120, 53, 15), (69, 26, 3))

        floor_y = int(h * 0.72)
        # Bookshelf on left / background
        shelf_w = int(w * 0.35)
        draw.rectangle([int(w * 0.05), int(h * 0.15), shelf_w, floor_y], fill=(69, 26, 3), outline=(146, 64, 14), width=4)

        # Shelves with books
        num_shelves = 4
        shelf_step = (floor_y - int(h * 0.15)) // num_shelves
        book_colors = [(185, 28, 28), (30, 64, 175), (20, 83, 45), (180, 83, 9), (107, 33, 168)]
        for s in range(num_shelves):
            sy = int(h * 0.15) + s * shelf_step
            draw.line([(int(w * 0.05), sy + shelf_step), (shelf_w, sy + shelf_step)], fill=(146, 64, 14), width=6)
            # Row of books
            bx = int(w * 0.07)
            while bx < shelf_w - 20:
                bw = 14 + (bx % 12)
                bh = shelf_step - 20 - (bx % 15)
                bcol = book_colors[(bx // 15) % len(book_colors)]
                draw.rectangle([bx, sy + shelf_step - bh, bx + bw, sy + shelf_step - 4], fill=bcol, outline=(24, 24, 27), width=1)
                bx += bw + 3

        # Window with gentle outside twilight / warm glow on right
        win_x1, win_y1 = int(w * 0.55), int(h * 0.18)
        win_x2, win_y2 = int(w * 0.90), int(h * 0.55)
        # Outside amber twilight
        draw.rectangle([win_x1, win_y1, win_x2, win_y2], fill=(251, 146, 60))
        # Window frame
        draw.rectangle([win_x1, win_y1, win_x2, win_y2], outline=(69, 26, 3), width=8)
        draw.line([((win_x1 + win_x2) // 2, win_y1), ((win_x1 + win_x2) // 2, win_y2)], fill=(69, 26, 3), width=6)
        draw.line([(win_x1, (win_y1 + win_y2) // 2), (win_x2, (win_y1 + win_y2) // 2)], fill=(69, 26, 3), width=6)

        # Polished Warm Wooden Floor
        draw.rectangle([0, floor_y, w, h], fill=(69, 26, 3))
        # Planks
        for py in range(floor_y, h, 40):
            draw.line([(0, py), (w, py)], fill=(45, 17, 2), width=2)

        # Soft warm lamp glow aura
        lamp_glow_alpha = int(35 + 10 * math.sin(t * 2.0))
        draw.ellipse([int(w * 0.45), int(h * 0.35), int(w * 0.95), int(h * 0.85)], fill=(254, 240, 138, lamp_glow_alpha))

    def _draw_sunset_porch(self, draw: ImageDraw.ImageDraw, w: int, h: int, t: float):
        """Elders: Serene golden hour sunset on wooden porch."""
        # Majestic gradient from rose-violet to rich warm gold
        self._draw_gradient(draw, w, h, (147, 51, 234), (251, 146, 60))

        # Golden setting sun
        sun_y = int(h * 0.52)
        draw.ellipse([int(w * 0.5) - 100, sun_y - 100, int(w * 0.5) + 100, sun_y + 100], fill=(254, 240, 138))

        # Distant purple hills
        draw.chord([-int(w * 0.2), int(h * 0.54), int(w * 0.7), int(h * 0.75)], start=180, end=360, fill=(107, 33, 168))
        draw.chord([int(w * 0.3), int(h * 0.56), int(w * 1.2), int(h * 0.75)], start=180, end=360, fill=(76, 29, 149))

        # Wooden Porch Railing & Deck
        deck_y = int(h * 0.72)
        draw.rectangle([0, deck_y, w, h], fill=(120, 53, 15))
        # Railing
        draw.line([(0, deck_y - 60), (w, deck_y - 60)], fill=(69, 26, 3), width=12)
        # Balusters
        for bx in range(0, w, 50):
            draw.line([(bx, deck_y - 60), (bx, deck_y)], fill=(69, 26, 3), width=6)

    def _draw_warm_hearth(self, draw: ImageDraw.ImageDraw, w: int, h: int, t: float):
        """Elders: Stone hearth with cozy amber fireplace glow."""
        self._draw_gradient(draw, w, h, (45, 17, 2), (15, 23, 42))
        floor_y = int(h * 0.74)
        # Stone fireplace base
        fp_w = int(w * 0.5)
        fp_x = int(w * 0.25)
        draw.rectangle([fp_x, int(h * 0.35), fp_x + fp_w, floor_y], fill=(71, 85, 105), outline=(51, 65, 85), width=6)
        # Fireplace arch
        draw.ellipse([fp_x + 30, int(h * 0.48), fp_x + fp_w - 30, floor_y + 20], fill=(15, 23, 42))
        # Flame glow
        flicker = 0.9 + 0.2 * math.sin(t * 8.0)
        draw.ellipse([int(w * 0.4), int(floor_y - 80 * flicker), int(w * 0.6), floor_y], fill=(234, 88, 12))
        draw.ellipse([int(w * 0.45), int(floor_y - 50 * flicker), int(w * 0.55), floor_y], fill=(253, 224, 71))
        # Floor
        draw.rectangle([0, floor_y, w, h], fill=(30, 41, 59))

    def _draw_library(self, draw: ImageDraw.ImageDraw, w: int, h: int):
        """Elders: Grand classical library with bookshelves."""
        self._draw_cozy_study(draw, w, h, 0.0)


# Global background generator
background_generator = BackgroundGenerator()
