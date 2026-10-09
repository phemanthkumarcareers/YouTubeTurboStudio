"""
Storyboarder — Shared Animation Engine
Converts scripts, topics, and channel requirements into a declarative SceneGraph.
Provides channel-tailored scene sequencing, character placements, camera directions,
props, and SFX cues for Kids and Elders.
"""
from typing import List, Dict, Any, Optional
from animation.schema import SceneGraph, Scene, CharacterPlacement, PropPlacement, CameraMove
from core.channel_context import ChannelContext


class Storyboarder:
    """Generates structured SceneGraph animations from scripts or prompts."""

    def build_storyboard(
        self,
        script_data: Dict[str, Any],
        channel_context: ChannelContext,
        video_format: str = "shorts",
        fps: int = 30
    ) -> SceneGraph:
        """
        Creates a complete SceneGraph tailored to channel guidelines.
        video_format: "shorts" (1080x1920) or "normal" (1920x1080)
        """
        is_kids = (channel_context.channel_id == "kids" or "kid" in channel_context.channel_id)
        is_shorts = (video_format == "shorts")

        width = 1080 if is_shorts else 1920
        height = 1920 if is_shorts else 1080

        title = script_data.get("title", f"Story for {channel_context.name}")
        scenes_data = script_data.get("scenes", [])

        # Fallback if no structured scenes provided in script_data
        if not scenes_data:
            narration = script_data.get("narration") or script_data.get("full_narration") or "Welcome to today's wonderful story!"
            # Split into 2-3 logical scenes
            sentences = [s.strip() for s in narration.split(".") if s.strip()]
            if len(sentences) >= 2:
                mid = len(sentences) // 2
                scenes_data = [
                    {"scene_id": 1, "title": "Intro", "narration": ". ".join(sentences[:mid]) + ".", "duration": 5.0},
                    {"scene_id": 2, "title": "Conclusion", "narration": ". ".join(sentences[mid:]) + ".", "duration": 6.0}
                ]
            else:
                scenes_data = [
                    {"scene_id": 1, "title": "Story Beat", "narration": narration, "duration": 6.0}
                ]

        scene_list: List[Scene] = []

        # Curated palette & environments
        kids_bgs = ["vibrant_sky", "playful_park", "starry_space", "chalkboard"]
        elders_bgs = ["cozy_study", "sunset_porch", "warm_hearth", "library"]

        kids_props = ["star", "magnifying_glass", "rocket", "book"]
        elders_props = ["tea_mug", "vintage_book", "reading_glasses", "clock"]

        for i, sc in enumerate(scenes_data):
            s_id = sc.get("scene_id", i + 1)
            duration = float(sc.get("duration", 5.0 if is_kids else 6.5))
            narration_text = sc.get("narration", "")

            if is_kids:
                # KIDS SPECIFIC SCENE DESIGN
                bg_style = sc.get("bg_style") or kids_bgs[i % len(kids_bgs)]
                motion = "walk_in" if i == 0 else ("bob_bounce" if i % 2 == 1 else "idle_breathe")
                gesture = "wave" if i == 0 else ("hold_prop" if i == 1 else "point")
                cam_type = "slow_zoom_in" if i % 2 == 0 else "punch_zoom"
                
                # Characters
                char_id = sc.get("character") or "sparky_host"
                char_style = char_id if char_id in ("pip_bunny", "barnaby_bear", "ollie_owl") else "kids"
                char_name = "Pip Bunny" if "bunny" in char_id else ("Barnaby Bear" if "bear" in char_id else ("Ollie Owl" if "owl" in char_id else "Sparky"))
                chars = [
                    CharacterPlacement(
                        character_id=char_id,
                        name=char_name,
                        style=char_style,
                        x_percent=0.50 if is_shorts else 0.40,
                        y_percent=0.62 if is_shorts else 0.58,
                        scale=1.1 if is_shorts else 1.25,
                        motion=motion,
                        gesture=gesture,
                        is_talking=bool(narration_text)
                    )
                ]

                # Props (supports prop_count for counting lessons)
                prop_type = sc.get("prop") or kids_props[i % len(kids_props)]
                prop_count = int(sc.get("prop_count", 1))
                props = []
                prop_action = "held" if (gesture == "hold_prop" and prop_count == 1) else "float"

                if prop_count > 1:
                    # Layout multiple counted items horizontally
                    spacing = 0.16
                    start_x = 0.50 - ((prop_count - 1) * spacing) / 2.0
                    for p_idx in range(prop_count):
                        props.append(
                            PropPlacement(
                                prop_id=f"prop_{s_id}_{p_idx+1}",
                                name=f"{prop_type.capitalize()} {p_idx+1}",
                                prop_type=prop_type,
                                x_percent=max(0.15, min(0.85, start_x + p_idx * spacing)),
                                y_percent=0.48 if is_shorts else 0.45,
                                scale=0.85,
                                action="float"
                            )
                        )
                else:
                    props.append(
                        PropPlacement(
                            prop_id=f"prop_{s_id}",
                            name=prop_type.capitalize(),
                            prop_type=prop_type,
                            x_percent=0.72 if is_shorts else 0.65,
                            y_percent=0.55 if is_shorts else 0.52,
                            scale=1.0 if is_shorts else 1.2,
                            action=prop_action
                        )
                    )

                # SFX Cues
                sfx_cues = [
                    {"time": 0.3, "type": "pop" if i % 2 == 0 else "twinkle", "volume": 0.75},
                    {"time": max(0.5, duration - 1.2), "type": "chime", "volume": 0.8}
                ]

                camera = CameraMove(
                    camera_type=cam_type,
                    zoom_start=1.0,
                    zoom_end=1.12 if cam_type != "static" else 1.0,
                    pan_dx=0.0
                )

            else:
                # ELDERS SPECIFIC SCENE DESIGN
                bg_style = sc.get("bg_style") or elders_bgs[i % len(elders_bgs)]
                # First scene elder walking or sitting comfortably
                motion = "walk_in" if i == 0 else ("sit" if i == 1 else "idle_breathe")
                gesture = "wave" if i == 0 else ("hold_prop" if i == 1 else "point")
                cam_type = "slow_zoom_in" if i % 2 == 0 else "static"

                char_id = sc.get("character") or "arthur_storyteller"
                char_style = sc.get("style", "elders")
                char_name = "Grandma Eleanor" if "eleanor" in char_id else ("Uncle Walter" if "walter" in char_id else "Grandpa Arthur")

                chars = [
                    CharacterPlacement(
                        character_id=char_id,
                        name=char_name,
                        style=char_style,
                        x_percent=0.50 if is_shorts else 0.45,
                        y_percent=0.62 if is_shorts else 0.58,
                        scale=1.1 if is_shorts else 1.25,
                        motion=motion,
                        gesture=gesture,
                        is_talking=bool(narration_text)
                    )
                ]

                # Props
                prop_type = sc.get("prop") or elders_props[i % len(elders_props)]
                prop_action = "held" if gesture == "hold_prop" else "static"
                props = [
                    PropPlacement(
                        prop_id=f"prop_{s_id}",
                        name=prop_type.capitalize(),
                        prop_type=prop_type,
                        x_percent=0.68 if is_shorts else 0.68,
                        y_percent=0.60 if is_shorts else 0.58,
                        scale=0.95 if is_shorts else 1.1,
                        action=prop_action
                    )
                ]

                # SFX Cues
                sfx_cues = [
                    {"time": 0.5, "type": "gentle_bell" if i % 2 == 0 else "clock_tick", "volume": 0.65},
                    {"time": max(0.8, duration - 1.5), "type": "page_turn", "volume": 0.6}
                ]

                camera = CameraMove(
                    camera_type=cam_type,
                    zoom_start=1.0,
                    zoom_end=1.08 if cam_type == "slow_zoom_in" else 1.0,
                    pan_dx=0.0
                )

            scene_list.append(Scene(
                scene_id=s_id,
                title=sc.get("title", f"Beat {s_id}"),
                duration=duration,
                bg_style=bg_style,
                characters=chars,
                props=props,
                camera=camera,
                narration=narration_text,
                sfx_cues=sfx_cues
            ))

        return SceneGraph(
            title=title,
            channel_id=channel_context.channel_id,
            format=video_format,
            width=width,
            height=height,
            fps=fps,
            scenes=scene_list
        )


storyboarder = Storyboarder()
