"""
Virtual Camera — Shared Animation Engine
Provides 2D camera movements: slow zoom in, slow zoom out, panning, and punch zoom.
Applied to composited frames to create cinematic framing for Kids & Elders.
"""
from typing import Tuple
from PIL import Image
from animation.schema import CameraMove


class VirtualCamera:
    """Simulates a 2D camera with zoom and pan over time."""

    def apply(
        self,
        frame: Image.Image,
        camera: CameraMove,
        t: float,
        duration: float,
        focus_center: Tuple[float, float] = (0.5, 0.5)
    ) -> Image.Image:
        """
        Applies camera movement to a PIL Image frame.
        t: current time in seconds
        duration: scene duration in seconds
        focus_center: (cx_percent, cy_percent)
        """
        w, h = frame.size
        progress = max(0.0, min(1.0, t / max(0.001, duration)))

        # Determine zoom factor
        c_type = camera.camera_type
        if c_type == "static":
            zoom = 1.0
            dx, dy = 0.0, 0.0
        elif c_type == "slow_zoom_in":
            zoom = camera.zoom_start + (camera.zoom_end - camera.zoom_start) * progress
            dx = camera.pan_dx * progress
            dy = camera.pan_dy * progress
        elif c_type == "slow_zoom_out":
            zoom = camera.zoom_end - (camera.zoom_end - camera.zoom_start) * progress
            dx = camera.pan_dx * progress
            dy = camera.pan_dy * progress
        elif c_type == "punch_zoom":
            # Quick zoom bump on first 0.8s
            snap = min(1.0, progress * 2.5)
            zoom = camera.zoom_start + (camera.zoom_end - camera.zoom_start) * snap
            dx = camera.pan_dx * snap
            dy = camera.pan_dy * snap
        elif c_type in ("pan_left", "pan_right"):
            zoom = camera.zoom_start
            dx = camera.pan_dx * progress
            dy = camera.pan_dy * progress
        else:
            zoom = 1.0
            dx, dy = 0.0, 0.0

        if abs(zoom - 1.0) < 0.005 and abs(dx) < 1.0 and abs(dy) < 1.0:
            return frame

        # Crop box dimensions
        crop_w = max(10, int(w / zoom))
        crop_h = max(10, int(h / zoom))

        # Center point
        cx = int(w * focus_center[0] + dx)
        cy = int(h * focus_center[1] + dy)

        x1 = max(0, min(w - crop_w, cx - crop_w // 2))
        y1 = max(0, min(h - crop_h, cy - crop_h // 2))
        x2 = x1 + crop_w
        y2 = y1 + crop_h

        cropped = frame.crop((x1, y1, x2, y2))
        return cropped.resize((w, h), resample=Image.BILINEAR)


# Global virtual camera
virtual_camera = VirtualCamera()
