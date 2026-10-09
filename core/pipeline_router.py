"""
Pipeline Router
Routes generation requests to the appropriate engine based on channel configuration:
- 'media_video': Routes to Media Video Engine (The AI Brief It & media stock channels)
- 'animation': Routes to Animation Engine (Kids, Elders & animated channels)
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
        # Animation Engine MVP is scheduled for Phase 3
        log_warn(
            f"[ROUTER] Animation Engine for channel '{channel_context.name}' is scheduled for Phase 3 (Shared Animation Engine MVP). "
            f"Channel configuration, audience profile ({channel_context.audience.get('type')}), and safeguards are active."
        )
        # Update pipeline state safely
        update_state(
            running=False,
            channel_id=channel_context.channel_id,
            error=None
        )
        log_info(f"[ROUTER] Channel '{channel_context.name}' is registered and ready for Phase 3 Animation Engine.")
        return None

    else:
        raise ValueError(f"Unknown engine '{engine}' configured for channel '{channel_context.channel_id}'.")
