"""
Animation Renderer — Shared Animation Engine
Compositor and video renderer for both Kids and Elders channels.
Shared engine implementation supporting Preview mode (15fps) and Final mode (30fps),
dynamic character puppets, props, virtual camera transforms, audio/SFX mixing,
and YouTube-safe subtitles.
"""
import os
import math
import numpy as np
from typing import Optional, Callable, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont

from animation.schema import SceneGraph, Scene
from animation.character_manager import character_manager
from animation.props import props_manager
from animation.backgrounds import background_generator
from animation.motion_engine import motion_engine
from animation.camera import virtual_camera
from animation.audio_sfx import mix_animation_audio
from core.logger import log_info, log_warn


class AnimationRenderer:
    """Core shared renderer for all animated video generation."""

    def __init__(self):
        self._font_cache: Dict[int, ImageFont.FreeTypeFont] = {}

    def get_font(self, size: int) -> ImageFont.ImageFont:
        """Loads a readable font at the given size with fallback to default."""
        if size in self._font_cache:
            return self._font_cache[size]

        font_paths = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    f = ImageFont.truetype(fp, size)
                    self._font_cache[size] = f
                    return f
                except Exception:
                    continue

        f = ImageFont.load_default()
        self._font_cache[size] = f
        return f

    def render_frame(
        self,
        scene: Scene,
        t_scene: float,
        width: int,
        height: int,
        is_shorts: bool = True
    ) -> np.ndarray:
        """
        Renders a single video frame as a NumPy RGB array.
        """
        # 1. Background
        bg_img = background_generator.render_background(
            style=scene.bg_style,
            width=width,
            height=height,
            time_sec=t_scene
        )

        frame = bg_img.convert("RGBA")

        # 2. Compute Character Transforms
        char_transforms = []
        for char in scene.characters:
            tf = motion_engine.compute_character_transform(
                char=char,
                t=t_scene,
                scene_duration=scene.duration,
                width=width,
                height=height
            )
            char_transforms.append((char, tf))

        # 3. Layer Props behind characters (z_index < 10)
        for prop in scene.props:
            if prop.z_index < 10:
                self._composite_prop(frame, prop, t_scene, scene.duration, width, height, char_transforms)

        # 4. Layer Characters
        for char, tf in char_transforms:
            sprite_w = int(450 * tf["scale"] * (width / 1080.0))
            sprite_h = int(560 * tf["scale"] * (width / 1080.0))
            sprite = character_manager.get_character_frame(
                character_id=char.character_id,
                style=char.style,
                mouth_open_pct=tf["mouth_open"],
                eye_blink_pct=tf["blink"],
                head_tilt_deg=tf["head_tilt"],
                gesture=tf["gesture"],
                motion=tf["motion"],
                walk_cycle=tf["walk_cycle"],
                target_size=(max(40, sprite_w), max(50, sprite_h))
            )
            # Paste sprite centered at tf["x"], tf["y"]
            px = tf["x"] - sprite.width // 2
            py = tf["y"] - sprite.height // 2
            frame.alpha_composite(sprite, (px, py))

        # 5. Layer Props in front of characters (z_index >= 10)
        for prop in scene.props:
            if prop.z_index >= 10:
                self._composite_prop(frame, prop, t_scene, scene.duration, width, height, char_transforms)

        # 6. Safe Subtitles / Captions
        if scene.narration:
            self._render_captions(frame, scene.narration, width, height, is_shorts)

        # 7. Apply 2D Virtual Camera
        camera_applied = virtual_camera.apply(
            frame=frame.convert("RGB"),
            camera=scene.camera,
            t=t_scene,
            duration=scene.duration
        )

        return np.array(camera_applied)

    def _composite_prop(
        self,
        frame: Image.Image,
        prop,
        t_scene: float,
        duration: float,
        width: int,
        height: int,
        char_transforms: List
    ):
        """Helper to compute and composite a prop sprite."""
        primary_tf = char_transforms[0][1] if char_transforms else None
        p_tf = motion_engine.compute_prop_transform(
            prop=prop,
            t=t_scene,
            scene_duration=duration,
            width=width,
            height=height,
            char_transform=primary_tf
        )
        base_size = int(240 * p_tf["scale"] * (width / 1080.0))
        prop_sprite = props_manager.get_prop_frame(
            prop_type=prop.prop_type,
            scale=1.0,
            action=p_tf["action"],
            time_sec=t_scene,
            base_size=(max(20, base_size), max(20, base_size))
        )
        if abs(p_tf["rotation_deg"]) > 0.5:
            prop_sprite = prop_sprite.rotate(p_tf["rotation_deg"], resample=Image.BILINEAR)

        px = p_tf["x"] - prop_sprite.width // 2
        py = p_tf["y"] - prop_sprite.height // 2
        frame.alpha_composite(prop_sprite, (px, py))

    def _render_captions(
        self,
        frame: Image.Image,
        text: str,
        width: int,
        height: int,
        is_shorts: bool
    ):
        """Draws readable, high-contrast captions with YouTube UI safe margins."""
        draw = ImageDraw.Draw(frame)
        font_size = int(height * 0.024) if is_shorts else int(height * 0.038)
        font = self.get_font(font_size)

        # Word wrap text within 78% width
        max_line_width = int(width * 0.76)
        words = text.strip().split()
        lines = []
        curr_line = []

        for word in words:
            curr_line.append(word)
            test_line = " ".join(curr_line)
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if (bbox[2] - bbox[0]) > max_line_width:
                curr_line.pop()
                if curr_line:
                    lines.append(" ".join(curr_line))
                curr_line = [word]

        if curr_line:
            lines.append(" ".join(curr_line))

        # Y position: Safe margin (above bottom 22% for Shorts, 16% for 16:9)
        line_height = int(font_size * 1.35)
        total_text_h = len(lines) * line_height
        box_pad_x = 24
        box_pad_y = 14

        base_y = int(height * 0.74) if is_shorts else int(height * 0.82)
        center_x = width // 2

        # Draw lines with dark rounded capsule pill
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            ly = base_y + i * line_height
            lx = center_x - line_w // 2

            # Background pill
            pill_box = [
                lx - box_pad_x,
                ly - box_pad_y,
                lx + line_w + box_pad_x,
                ly + line_height + 4
            ]
            draw.rounded_rectangle(pill_box, radius=16, fill=(15, 23, 42, 215), outline=(254, 240, 138, 140), width=2)
            # Text with subtle drop shadow
            draw.text((lx + 2, ly + 2), line, fill=(0, 0, 0, 180), font=font)
            draw.text((lx, ly), line, fill=(255, 255, 255, 255), font=font)

    def render(
        self,
        scene_graph: SceneGraph,
        output_path: str,
        mode: str = "preview",
        narration_audio_path: Optional[str] = None,
        bgm_path: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """
        Renders complete SceneGraph into an MP4 video file.
        mode: 'preview' (15 fps, fast) or 'final' (30 fps, high fidelity)
        """
        import moviepy.editor as mp

        fps = 15 if mode == "preview" else scene_graph.fps
        width = scene_graph.width
        height = scene_graph.height
        is_shorts = (scene_graph.format == "shorts")

        total_duration = scene_graph.total_duration
        if total_duration <= 0:
            raise ValueError("SceneGraph has 0 duration.")

        log_info(
            f"[RENDERER] Starting Animation Render: '{scene_graph.title}' "
            f"({width}x{height} @ {fps}fps, {total_duration:.1f}s, mode={mode}, scenes={len(scene_graph.scenes)})"
        )

        # 1. Prepare Audio Track
        all_sfx_cues: List[Dict[str, Any]] = []
        elapsed = 0.0
        for scene in scene_graph.scenes:
            for cue in scene.sfx_cues:
                all_sfx_cues.append({
                    "time": elapsed + float(cue.get("time", 0.0)),
                    "type": cue.get("type", "pop"),
                    "volume": float(cue.get("volume", 0.8))
                })
            elapsed += scene.duration

        audio_output_path = os.path.splitext(output_path)[0] + "_audio.wav"
        mix_animation_audio(
            total_duration=total_duration,
            output_path=audio_output_path,
            narration_path=narration_audio_path,
            sfx_cues=all_sfx_cues,
            bgm_path=bgm_path,
            bgm_volume=0.10
        )

        # 2. Render Frames via MoviePy VideoClip make_frame function
        # Flatten scenes into timeline intervals
        intervals = []
        cur_t = 0.0
        for sc in scene_graph.scenes:
            intervals.append((cur_t, cur_t + sc.duration, sc))
            cur_t += sc.duration

        total_frames = int(total_duration * fps)

        def make_frame(t: float) -> np.ndarray:
            # Find matching scene
            active_scene = intervals[-1][2]
            t_in_scene = 0.0
            for start, end, sc in intervals:
                if start <= t <= end:
                    active_scene = sc
                    t_in_scene = t - start
                    break

            frame_np = self.render_frame(
                scene=active_scene,
                t_scene=t_in_scene,
                width=width,
                height=height,
                is_shorts=is_shorts
            )
            return frame_np

        video_clip = mp.VideoClip(make_frame, duration=total_duration)

        # Attach audio
        if os.path.exists(audio_output_path):
            audio_clip = mp.AudioFileClip(audio_output_path)
            video_clip = video_clip.set_audio(audio_clip)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        preset = "ultrafast" if mode == "preview" else "medium"
        bitrate = "3000k" if mode == "preview" else "8000k"

        log_info(f"[RENDERER] Encoding final animated MP4 to '{output_path}'...")
        video_clip.write_videofile(
            output_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            preset=preset,
            bitrate=bitrate,
            threads=4,
            logger=None
        )

        video_clip.close()
        log_info(f"[RENDERER] Successfully exported animation: '{output_path}'")
        return output_path


# Global singleton renderer
animation_renderer = AnimationRenderer()
