"""
Pipeline Router
Routes generation requests to the appropriate engine based on channel configuration:
- 'media_video': Routes to Media Video Engine (InsightSpark TV & media stock channels)
- 'animation': Routes to Animation Engine (Kids Wonder Lab, Wonder Saga TV & animated channels)
Extensible to future channels without hardcoded if/else branching.
"""
from typing import List, Optional, Dict, Any
from core.channel_context import ChannelContext
from core.channel_registry import registry
from core.logger import log_info, log_warn, log_stage
from core.state import set_stage, update_state


def route_and_execute(
    channel_context: Optional[ChannelContext] = None,
    steps: Optional[List[str]] = None,
    topic_override: str = "",
    focus_angle: str = "",
    video_type: str = "normal",
    custom_script: Optional[Dict[str, Any]] = None
):
    """
    Route generation to the engine declared in the channel configuration.
    """
    if channel_context is None:
        channel_context = registry.get_active_channel()

    engine = (channel_context.engine or "media_video").lower().strip()
    log_info(f"[ROUTER] Active Channel: '{channel_context.name}' (ID: {channel_context.channel_id}) -> Engine: '{engine}'")

    if engine == "media_video":
        from core.pipeline import execute_pipeline
        return execute_pipeline(
            steps=steps,
            topic_override=topic_override,
            focus_angle=focus_angle,
            video_type=video_type,
            custom_script=custom_script,
            channel_context=channel_context
        )

    elif engine == "animation":
        from animation.pipeline import execute_animation_pipeline
        log_info(f"[ROUTER] Dispatching '{channel_context.name}' to Shared Animation Engine...")
        return execute_animation_pipeline(
            channel_context=channel_context,
            steps=steps,
            topic_override=topic_override,
            focus_angle=focus_angle,
            video_type=video_type,
            custom_script=custom_script
        )

    else:
        raise ValueError(f"Unknown engine '{engine}' configured for channel '{channel_context.channel_id}'.")
