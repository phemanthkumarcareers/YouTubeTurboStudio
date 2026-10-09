"""
Shared Animation Engine for YouTubeTurboStudio
Reusable core for Kids, Elders, and future animated channels.
"""
from animation.schema import SceneGraph, Scene, CharacterPlacement, PropPlacement, CameraMove, validate_scene_graph
from animation.character_manager import CharacterManager, character_manager
from animation.props import PropsManager, props_manager
from animation.backgrounds import BackgroundGenerator, background_generator
from animation.motion_engine import MotionEngine, motion_engine
from animation.camera import VirtualCamera, virtual_camera
from animation.storyboarder import Storyboarder, storyboarder
from animation.renderer import AnimationRenderer, animation_renderer
from animation.qc import AnimationQCChecker, animation_qc
from animation.pipeline import execute_animation_pipeline

__all__ = [
    "SceneGraph",
    "Scene",
    "CharacterPlacement",
    "PropPlacement",
    "CameraMove",
    "validate_scene_graph",
    "CharacterManager",
    "character_manager",
    "PropsManager",
    "props_manager",
    "BackgroundGenerator",
    "background_generator",
    "MotionEngine",
    "motion_engine",
    "VirtualCamera",
    "virtual_camera",
    "Storyboarder",
    "storyboarder",
    "AnimationRenderer",
    "animation_renderer",
    "AnimationQCChecker",
    "animation_qc",
    "execute_animation_pipeline"
]
