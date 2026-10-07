"""
Real-time Logger and Event Streamer for YouTube Turbo Studio
Provides structured logging, stage notifications, and SSE streaming.
"""
import sys
import time
import queue
import json
from datetime import datetime

_log_queue = queue.Queue(maxsize=1000)
_history = []
_MAX_HISTORY = 300


class CaptureStdout:
    """Redirects stdout/stderr to log queue and terminal."""
    def __init__(self, original):
        self.original = original

    def write(self, text):
        cleaned = text.strip()
        if cleaned:
            emit_log(cleaned, level="info")
        self.original.write(text)

    def flush(self):
        self.original.flush()


def emit_log(message: str, level: str = "info", stage: str = None):
    now = datetime.now().strftime("%H:%M:%S")
    entry = {
        "time": now,
        "msg": message,
        "level": level,  # 'info', 'success', 'warn', 'error', 'stage'
        "stage": stage
    }
    _history.append(entry)
    if len(_history) > _MAX_HISTORY:
        _history.pop(0)

    try:
        _log_queue.put_nowait(entry)
    except queue.Full:
        pass


def log_info(msg: str):
    emit_log(msg, level="info")


def log_success(msg: str):
    emit_log(f"✓ {msg}", level="success")


def log_warn(msg: str):
    emit_log(f"⚠ {msg}", level="warn")


def log_error(msg: str):
    emit_log(f"✗ {msg}", level="error")


def log_stage(stage: str, status: str):
    emit_log(f"Stage [{stage.upper()}] -> {status.upper()}", level="stage", stage=stage)


def get_log_history():
    return list(_history)


def log_stream():
    """Generator for Flask Server-Sent Events (SSE)."""
    # Send existing history first
    for item in _history[-30:]:
        yield f"data: {json.dumps(item)}\n\n"

    while True:
        try:
            item = _log_queue.get(timeout=20.0)
            yield f"data: {json.dumps(item)}\n\n"
        except queue.Empty:
            # Heartbeat to keep connection alive
            yield ": ping\n\n"
