"""
Global State Tracker for YouTube Turbo Studio
"""
import copy
import threading

_state_lock = threading.Lock()

_INITIAL_STATE = {
    "running": False,
    "stop_requested": False,
    "current_step": "idle",
    "video_type": "normal",
    "stages": {
        "research": "pending",
        "script": "pending",
        "narration": "pending",
        "media": "pending",
        "video": "pending",
        "thumbnail": "pending"
    },
    "video_path": None,
    "thumb_path": None,
    "audio_path": None,
    "srt_path": None,
    "research_data": None,
    "script_data": None,
    "description": "",
    "tags": [],
    "yt_url": None,
    "error": None,
    "upload_pct": 0,
    "uploading": False
}

state = copy.deepcopy(_INITIAL_STATE)


def get_state() -> dict:
    with _state_lock:
        return copy.deepcopy(state)


def update_state(**kwargs):
    with _state_lock:
        for k, v in kwargs.items():
            if k == "stages" and isinstance(v, dict):
                state["stages"].update(v)
            else:
                state[k] = v


def set_stage(stage_name: str, status: str):
    """status: pending | running | done | error"""
    with _state_lock:
        if stage_name in state["stages"]:
            state["stages"][stage_name] = status


def reset_pipeline_state(video_type: str = "normal"):
    with _state_lock:
        state["running"] = True
        state["stop_requested"] = False
        state["current_step"] = "starting"
        state["video_type"] = video_type
        state["error"] = None
        state["yt_url"] = None
        state["upload_pct"] = 0
        state["uploading"] = False
        for s in state["stages"]:
            state["stages"][s] = "pending"
