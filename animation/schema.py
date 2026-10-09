"""
Animation Engine — Declarative Scene Representation & Schema
Defines the scene graph, character positions, motion keyframes, virtual camera,
props, and audio/SFX cues for both Kids and Elders channels.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
import copy


@dataclass
class PropPlacement:
    prop_id: str
    name: str = "Prop"
    prop_type: str = "star"  # "star", "magnifying_glass", "rocket", "book", "tea_mug", "vintage_book", "glasses", "clock"
    x_percent: float = 0.50  # Center X (0.0 to 1.0)
    y_percent: float = 0.70  # Center Y (0.0 to 1.0)
    scale: float = 1.0
    rotation_deg: float = 0.0
    action: str = "float"  # "static", "float", "held", "spin", "shimmer"
    z_index: int = 15  # Can be behind or in front of character (default 15 = in front of char at 10)


@dataclass
class CharacterPlacement:
    character_id: str
    name: str = "Host"
    style: str = "kids"  # "kids" or "elders"
    x_percent: float = 0.50  # Center X (0.0 to 1.0)
    y_percent: float = 0.65  # Center Y (0.0 to 1.0)
    scale: float = 1.0
    motion: str = "idle_breathe"  # "idle_breathe", "bob_bounce", "talk_pulse", "walk_in", "wave", "nod", "sit"
    gesture: str = "none"  # "none", "point", "wave", "hold_prop", "celebrate"
    is_talking: bool = True
    z_index: int = 10


@dataclass
class CameraMove:
    camera_type: str = "slow_zoom_in"  # "static", "slow_zoom_in", "slow_zoom_out", "pan_left", "pan_right", "punch_zoom"
    zoom_start: float = 1.0
    zoom_end: float = 1.10
    pan_dx: float = 0.0
    pan_dy: float = 0.0


@dataclass
class Scene:
    scene_id: int
    title: str = "Scene"
    duration: float = 5.0
    bg_style: str = "vibrant_sky"  # Kids: "vibrant_sky", "playful_park", "starry_space", "chalkboard"
                                   # Elders: "cozy_study", "sunset_porch", "warm_hearth", "library"
    bg_color_top: tuple = (14, 165, 233)
    bg_color_bottom: tuple = (240, 249, 255)
    characters: List[CharacterPlacement] = field(default_factory=list)
    props: List[PropPlacement] = field(default_factory=list)
    camera: CameraMove = field(default_factory=CameraMove)
    narration: str = ""
    sfx_cues: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SceneGraph:
    title: str = "Animated Story"
    channel_id: str = "kids"
    format: str = "shorts"  # "shorts" (1080x1920) or "normal" (1920x1080)
    width: int = 1080
    height: int = 1920
    fps: int = 30
    scenes: List[Scene] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(asdict(self))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneGraph":
        d = copy.deepcopy(data)
        scenes = []
        for s in d.get("scenes", []):
            chars = [CharacterPlacement(**c) for c in s.get("characters", [])]
            props = [PropPlacement(**p) for p in s.get("props", [])]
            cam_data = s.get("camera", {})
            camera = CameraMove(**cam_data) if cam_data else CameraMove()
            scenes.append(Scene(
                scene_id=s.get("scene_id", 1),
                title=s.get("title", "Scene"),
                duration=float(s.get("duration", 5.0)),
                bg_style=s.get("bg_style", "vibrant_sky"),
                bg_color_top=tuple(s.get("bg_color_top", (14, 165, 233))),
                bg_color_bottom=tuple(s.get("bg_color_bottom", (240, 249, 255))),
                characters=chars,
                props=props,
                camera=camera,
                narration=s.get("narration", ""),
                sfx_cues=s.get("sfx_cues", [])
            ))
        return cls(
            title=d.get("title", "Animated Story"),
            channel_id=d.get("channel_id", "kids"),
            format=d.get("format", "shorts"),
            width=d.get("width", 1080),
            height=d.get("height", 1920),
            fps=d.get("fps", 30),
            scenes=scenes
        )

    @property
    def total_duration(self) -> float:
        return sum(s.duration for s in self.scenes)


def validate_scene_graph(sg: SceneGraph) -> Tuple[bool, List[str]]:
    """
    Validates a SceneGraph against strict animation quality and timing rules.
    Returns (is_valid, list_of_errors).
    """
    errors: List[str] = []

    if not sg.scenes:
        errors.append("SceneGraph contains no scenes.")
        return False, errors

    if sg.width <= 0 or sg.height <= 0:
        errors.append(f"Invalid dimensions: {sg.width}x{sg.height}")

    if sg.fps not in (15, 24, 30, 60):
        errors.append(f"Unsupported fps: {sg.fps}. Must be 15, 24, 30, or 60.")

    for i, scene in enumerate(sg.scenes):
        if scene.duration <= 0:
            errors.append(f"Scene {i+1} duration must be positive (got {scene.duration}s)")
        
        # Check character bounds
        for char in scene.characters:
            if not (0.0 <= char.x_percent <= 1.0):
                errors.append(f"Scene {i+1} character '{char.name}' x_percent out of bounds: {char.x_percent}")
            if not (0.0 <= char.y_percent <= 1.0):
                errors.append(f"Scene {i+1} character '{char.name}' y_percent out of bounds: {char.y_percent}")
            if char.scale <= 0:
                errors.append(f"Scene {i+1} character '{char.name}' scale must be positive: {char.scale}")

        # Check prop bounds
        for prop in scene.props:
            if not (0.0 <= prop.x_percent <= 1.0):
                errors.append(f"Scene {i+1} prop '{prop.name}' x_percent out of bounds: {prop.x_percent}")
            if not (0.0 <= prop.y_percent <= 1.0):
                errors.append(f"Scene {i+1} prop '{prop.name}' y_percent out of bounds: {prop.y_percent}")
            if prop.scale <= 0:
                errors.append(f"Scene {i+1} prop '{prop.name}' scale must be positive: {prop.scale}")

        # Camera checks
        if scene.camera.zoom_start <= 0 or scene.camera.zoom_end <= 0:
            errors.append(f"Scene {i+1} camera zoom must be positive.")

    return (len(errors) == 0), errors
