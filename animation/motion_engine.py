"""
Motion Engine — Shared Animation Engine
Calculates spatial positions, easing, and expressive animation parameters
(breathing, bouncing, walking, mouth talking, blinking, gestures, and prop interaction)
over continuous scene timelines.
"""
import math
from typing import Tuple, Dict, Any
from animation.schema import CharacterPlacement, PropPlacement


def ease_in_out(t: float) -> float:
    """Standard smooth sinusoidal ease-in-out curve for t in [0.0, 1.0]."""
    t = max(0.0, min(1.0, t))
    return 0.5 * (1.0 - math.cos(math.pi * t))


def ease_out_cubic(t: float) -> float:
    """Fast entry, gentle deceleration curve."""
    t = max(0.0, min(1.0, t))
    return 1.0 - math.pow(1.0 - t, 3)


class MotionEngine:
    """Calculates real-time transform matrices and puppet parameters for each video frame."""

    def compute_character_transform(
        self,
        char: CharacterPlacement,
        t: float,
        scene_duration: float,
        width: int,
        height: int
    ) -> Dict[str, Any]:
        """
        Calculates character's (x_px, y_px, scale, mouth_open, blink, head_tilt, gesture, walk_cycle).
        """
        base_x = char.x_percent * width
        base_y = char.y_percent * height
        scale = char.scale
        motion = char.motion
        gesture = char.gesture

        head_tilt = 0.0
        walk_cycle = 0.0
        y_offset = 0.0
        x_offset = 0.0

        # Motion behavior
        if motion == "walk_in":
            # Walks from left (or right) into target position over first 2.0 seconds
            walk_dur = min(2.5, scene_duration * 0.5)
            if t < walk_dur:
                progress = ease_out_cubic(t / walk_dur)
                start_x = -0.2 * width
                base_x = start_x + (char.x_percent * width - start_x) * progress
                walk_cycle = t * 2.2  # Walk cadence
                y_offset = -abs(math.sin(walk_cycle * 2 * math.pi)) * 12.0
            else:
                # Arrived at destination -> idle breathe
                walk_cycle = 0.0
                y_offset = math.sin((t - walk_dur) * 2.0) * 4.0

        elif motion == "bob_bounce":
            # Cheerful rhythmic bounce (energetic kid mascot)
            bounce = abs(math.sin(t * 4.5))
            y_offset = -bounce * 22.0
            head_tilt = math.sin(t * 3.0) * 4.0

        elif motion == "sit":
            # Dignified calm breathing while sitting
            y_offset = math.sin(t * 1.5) * 2.5
            head_tilt = math.sin(t * 0.8) * 1.5

        elif motion == "nod":
            # Gentle affirmative nod
            nod_cycle = math.sin(t * 3.0)
            head_tilt = nod_cycle * 5.0
            y_offset = max(0.0, nod_cycle) * 6.0

        else:
            # Default: idle_breathe
            y_offset = math.sin(t * 2.0) * 5.0
            head_tilt = math.sin(t * 1.2) * 2.0

        # Mouth talking pulse
        mouth_open = 0.0
        if char.is_talking:
            # Pseudo-phonetic mouth movement oscillation
            m_wave = math.sin(t * 16.0) * 0.5 + math.sin(t * 9.0) * 0.3 + math.sin(t * 23.0) * 0.2
            mouth_open = max(0.0, min(1.0, (m_wave + 0.4)))
            if mouth_open < 0.2:
                mouth_open = 0.0

        # Eye blinking (natural human blink pattern: blink every ~3.5 seconds)
        blink_cycle = (t + hash(char.character_id) % 10) % 3.5
        blink = 0.0
        if blink_cycle < 0.22:
            blink = math.sin((blink_cycle / 0.22) * math.pi)

        return {
            "x": int(base_x + x_offset),
            "y": int(base_y + y_offset),
            "scale": scale,
            "mouth_open": mouth_open,
            "blink": blink,
            "head_tilt": head_tilt,
            "gesture": gesture,
            "motion": motion,
            "walk_cycle": walk_cycle
        }

    def compute_prop_transform(
        self,
        prop: PropPlacement,
        t: float,
        scene_duration: float,
        width: int,
        height: int,
        char_transform: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Calculates prop's (x_px, y_px, scale, rotation_deg).
        """
        base_x = prop.x_percent * width
        base_y = prop.y_percent * height
        scale = prop.scale
        rot = prop.rotation_deg
        action = prop.action

        if action == "held" and char_transform:
            # Track character's hand / chest position
            base_x = char_transform["x"] + int(60 * scale)
            base_y = char_transform["y"] + int(20 * scale)
            rot = char_transform.get("head_tilt", 0.0)

        elif action == "float":
            # Gentle buoyant floating oscillation
            hover = math.sin(t * 3.0) * 14.0
            base_y += hover
            rot += math.sin(t * 2.0) * 5.0

        elif action == "spin":
            rot += (t * 60.0) % 360.0

        return {
            "x": int(base_x),
            "y": int(base_y),
            "scale": scale,
            "rotation_deg": rot,
            "action": action
        }


# Global motion engine
motion_engine = MotionEngine()
