"""
Unified Multi-Provider Audio Generation Service
Supports Edge-TTS, ElevenLabs, OpenAI TTS, and Google TTS.
Features:
- Multi-character dialogue audio generation & synchronized subtitle (SRT) alignment
- Channel-specific voice profiling
- Automatic zero-cost fallback to Edge-TTS when external providers fail
- Connection testing for ElevenLabs and OpenAI TTS
"""
import os
import re
import json
import asyncio
import requests
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import edge_tts
from config import load_config, OUTPUT_DIR
from core.logger import log_info, log_warn, log_success, log_error
from audio.voice_profiles import (
    get_channel_voice_profile,
    get_voice_for_speaker,
    parse_dialogue_line,
    resolve_speaker_role
)


def _format_srt_time(ms: int) -> str:
    """Format milliseconds into standard SRT timestamp 00:00:00,000."""
    ms = max(0, int(ms))
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


# ─────────────────────────────────────────────────────────────────────────────
# 1. PROVIDER CONNECTION TESTERS
# ─────────────────────────────────────────────────────────────────────────────

def test_elevenlabs_connection(api_key: str, voice_id: str = "") -> Tuple[bool, str]:
    """Test connectivity and authentication with ElevenLabs API."""
    key = (api_key or "").strip()
    if not key:
        return False, "ElevenLabs API key cannot be empty."

    url = "https://api.elevenlabs.io/v1/user"
    headers = {"xi-api-key": key}
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            sub = data.get("subscription", {})
            chars_left = sub.get("character_limit", 0) - sub.get("character_count", 0)
            return True, f"ElevenLabs connected! Tier: {sub.get('tier', 'Free')}, Chars available: {chars_left:,}"
        elif resp.status_code == 401:
            return False, "ElevenLabs authentication failed (Invalid API Key)."
        else:
            return False, f"ElevenLabs returned HTTP {resp.status_code}: {resp.text[:120]}"
    except Exception as e:
        return False, f"ElevenLabs Error: {str(e)}"


def test_openai_tts_connection(api_key: str, model: str = "tts-1", voice: str = "alloy") -> Tuple[bool, str]:
    """Test OpenAI TTS API credentials."""
    key = (api_key or "").strip()
    if not key:
        return False, "OpenAI API key cannot be empty."

    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model or "tts-1",
        "input": "Connection test.",
        "voice": voice or "alloy"
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=8)
        if resp.status_code == 200 and len(resp.content) > 100:
            return True, f"OpenAI TTS connected successfully! Model: {model}, Voice: {voice}"
        elif resp.status_code == 401:
            return False, "OpenAI authentication failed (Invalid API Key)."
        elif resp.status_code == 429:
            return False, "OpenAI rate limit or insufficient quota reached."
        else:
            return False, f"OpenAI TTS returned HTTP {resp.status_code}: {resp.text[:120]}"
    except Exception as e:
        return False, f"OpenAI TTS Error: {str(e)}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. LOW-LEVEL SYNTHESIZERS
# ─────────────────────────────────────────────────────────────────────────────

async def _synthesize_edge_tts(text: str, voice: str, rate: str, pitch: str, output_mp3: str) -> List[Dict[str, Any]]:
    """Synthesize audio using Edge-TTS and collect word-level boundary cues."""
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    cues = []
    total_audio_bytes = 0

    with open(output_mp3, "wb") as f_audio:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f_audio.write(chunk["data"])
                total_audio_bytes += len(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                cues.append(chunk)

    return cues


def _synthesize_with_elevenlabs(text: str, voice_id: str, api_key: str, output_mp3: str) -> bool:
    """Synthesize speech via ElevenLabs REST API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code == 200 and len(resp.content) > 200:
        with open(output_mp3, "wb") as f:
            f.write(resp.content)
        return True
    else:
        raise RuntimeError(f"ElevenLabs HTTP {resp.status_code}: {resp.text[:120]}")


def _synthesize_with_openai_tts(text: str, voice: str, api_key: str, model: str, output_mp3: str) -> bool:
    """Synthesize speech via OpenAI TTS REST API."""
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model or "tts-1",
        "input": text,
        "voice": voice or "alloy"
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code == 200 and len(resp.content) > 200:
        with open(output_mp3, "wb") as f:
            f.write(resp.content)
        return True
    else:
        raise RuntimeError(f"OpenAI TTS HTTP {resp.status_code}: {resp.text[:120]}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. DURATION HELPER & SRT GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def get_audio_duration_seconds(file_path: str) -> float:
    """Accurately compute audio file duration in seconds."""
    if not os.path.exists(file_path):
        return 1.0
    try:
        from moviepy.editor import AudioFileClip
        clip = AudioFileClip(file_path)
        dur = float(clip.duration)
        clip.close()
        return max(0.5, dur)
    except Exception:
        # Fallback estimation based on mp3 size (~128kbps = 16000 bytes/sec)
        size = os.path.getsize(file_path)
        return max(0.5, size / 16000.0)


def build_estimated_srt(text: str, start_ms: int, duration_ms: int, start_idx: int = 1) -> Tuple[str, int]:
    """
    Build subtitle blocks for a text segment between start_ms and start_ms + duration_ms.
    Returns (srt_text_block, next_idx).
    """
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if not sentences:
        sentences = [text.strip()]
    
    total_len = sum(len(s) for s in sentences) or 1
    cur_ms = start_ms
    idx = start_idx
    lines = []

    for s in sentences:
        # Allocate time proportional to sentence length
        s_dur = int((len(s) / total_len) * duration_ms)
        s_end = cur_ms + s_dur
        lines.append(f"{idx}\n{_format_srt_time(cur_ms)} --> {_format_srt_time(s_end)}\n{s}\n")
        cur_ms = s_end
        idx += 1

    return "\n".join(lines), idx


# ─────────────────────────────────────────────────────────────────────────────
# 4. SINGLE CLIP SYNTHESIS (WITH AUTOMATIC FALLBACK)
# ─────────────────────────────────────────────────────────────────────────────

def synthesize_clip(
    text: str,
    voice_id: str,
    output_mp3: str,
    provider: str = "edge-tts",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    api_key: Optional[str] = None
) -> Tuple[str, float]:
    """
    Synthesize a single audio segment.
    If external provider fails, automatically falls back to Edge-TTS.
    Returns: (output_mp3_path, duration_seconds)
    """
    clean_text = (text or "").strip()
    if not clean_text:
        clean_text = "..."

    prov = (provider or "edge-tts").lower().strip()
    cfg = load_config()
    synthesized = False

    # 1. Try ElevenLabs
    if prov == "elevenlabs":
        el_key = api_key or cfg.get("elevenlabs_api_key", "")
        if el_key:
            try:
                log_info(f"[Audio] Synthesizing with ElevenLabs (Voice: {voice_id})...")
                _synthesize_with_elevenlabs(clean_text, voice_id, el_key, output_mp3)
                synthesized = True
            except Exception as e:
                log_warn(f"[Audio] ElevenLabs failed: {e}. Falling back to Edge-TTS.")

    # 2. Try OpenAI TTS
    elif prov in ("openai-tts", "openai"):
        oai_key = api_key or cfg.get("openai_api_key", "")
        if oai_key:
            try:
                oai_model = cfg.get("openai_tts_model", "tts-1")
                log_info(f"[Audio] Synthesizing with OpenAI TTS (Model: {oai_model}, Voice: {voice_id})...")
                _synthesize_with_openai_tts(clean_text, voice_id, oai_key, oai_model, output_mp3)
                synthesized = True
            except Exception as e:
                log_warn(f"[Audio] OpenAI TTS failed: {e}. Falling back to Edge-TTS.")

    # 3. Primary or Fallback: Edge-TTS
    if not synthesized:
        edge_voice = voice_id if voice_id and "Neural" in voice_id else "en-US-ChristopherNeural"
        log_info(f"[Audio] Synthesizing with Edge-TTS ({edge_voice}, rate={rate}, pitch={pitch})...")
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_synthesize_edge_tts(clean_text, edge_voice, rate, pitch, output_mp3))
        finally:
            loop.close()

    dur = get_audio_duration_seconds(output_mp3)
    return output_mp3, dur


# ─────────────────────────────────────────────────────────────────────────────
# 5. MULTI-CHARACTER & CHANNEL AUDIO GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_multi_character_speech(
    script_data: dict,
    channel_id: str = "kids",
    provider: Optional[str] = None,
    output_prefix: str = "narration"
) -> Tuple[str, str]:
    """
    Synthesize multi-character dialogue for a script.
    - Resolves speaker per section (or per line) using the channel's voice profile.
    - Generates distinct audio per character.
    - Concatenates audio into master MP3 with natural inter-dialogue pauses.
    - Generates unified synchronized SRT subtitle file.
    Returns: (master_mp3_path, master_srt_path)
    """
    cfg = load_config()
    chosen_provider = provider or cfg.get("tts_provider", "edge-tts")
    profile = get_channel_voice_profile(channel_id)
    sections = script_data.get("sections", [])

    if not sections:
        # Fallback to general narration if no sections
        full_text = script_data.get("narration", "Welcome to YouTube Turbo Studio.")
        return generate_speech(full_text, output_prefix=output_prefix, channel_id=channel_id)

    clip_dir = OUTPUT_DIR / f"audio_clips_{output_prefix}"
    clip_dir.mkdir(parents=True, exist_ok=True)

    clip_paths = []
    srt_blocks = []
    current_time_ms = 0
    sub_index = 1

    log_info(f"[Audio] Generating multi-character audio for channel '{channel_id}' ({len(sections)} sections)...")

    for i, sec in enumerate(sections, 1):
        raw_narration = sec.get("narration", "").strip()
        if not raw_narration:
            continue

        # Detect speaker tag if present in section or in text
        speaker_tag = sec.get("speaker") or sec.get("character")
        if not speaker_tag:
            detected_speaker, clean_text = parse_dialogue_line(raw_narration)
            speaker_tag = detected_speaker
            speech_text = clean_text
        else:
            speech_text = raw_narration

        voice_info = get_voice_for_speaker(channel_id, speaker_tag, provider=chosen_provider)
        clip_file = str(clip_dir / f"clip_{i}_{voice_info['role']}.mp3")

        # Synthesize clip with character voice
        synthesize_clip(
            text=speech_text,
            voice_id=voice_info["voice_id"],
            output_mp3=clip_file,
            provider=chosen_provider,
            rate=voice_info["rate"],
            pitch=voice_info["pitch"]
        )

        clip_paths.append(clip_file)
        duration_sec = get_audio_duration_seconds(clip_file)
        duration_ms = int(duration_sec * 1000)

        # Add subtitle block
        display_text = f"[{speaker_tag.title()}] {speech_text}" if speaker_tag.lower() != "narrator" else speech_text
        srt_chunk, next_sub_index = build_estimated_srt(
            text=display_text,
            start_ms=current_time_ms,
            duration_ms=duration_ms,
            start_idx=sub_index
        )
        srt_blocks.append(srt_chunk)
        sub_index = next_sub_index

        # Add 250ms natural conversational pause
        pause_ms = 250
        current_time_ms += duration_ms + pause_ms

    master_mp3 = str(OUTPUT_DIR / f"{output_prefix}.mp3")
    master_srt = str(OUTPUT_DIR / f"{output_prefix}.srt")

    # Concatenate clips using MoviePy
    if clip_paths:
        try:
            from moviepy.editor import AudioFileClip, concatenate_audioclips
            clips = [AudioFileClip(p) for p in clip_paths]
            composite = concatenate_audioclips(clips)
            composite.fps = 44100
            composite.write_audiofile(master_mp3, fps=44100, logger=None)
            for c in clips:
                c.close()
            composite.close()
            log_success(f"[Audio] Multi-character audio stitched into {os.path.basename(master_mp3)}")
        except Exception as e:
            log_warn(f"[Audio] Audio concatenation error: {e}. Copying first clip as fallback.")
            if os.path.exists(clip_paths[0]):
                import shutil
                shutil.copy(clip_paths[0], master_mp3)

    with open(master_srt, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_blocks) + "\n")

    log_success(f"[Audio] Subtitles generated: {os.path.basename(master_srt)} ({sub_index - 1} cues)")
    return master_mp3, master_srt


# ─────────────────────────────────────────────────────────────────────────────
# 6. GENERAL SPEECH GENERATION (COMPATIBLE WITH LEGACY / SINGLE NARRATOR)
# ─────────────────────────────────────────────────────────────────────────────

def generate_speech(
    full_text: str,
    output_prefix: str = "narration",
    channel_id: Optional[str] = None
) -> Tuple[str, str]:
    """
    Standard voiceover synthesis with channel profile awareness and automatic fallback.
    Returns: (mp3_path, srt_path)
    """
    cfg = load_config()
    channel = channel_id or cfg.get("channel_id", "the-ai-brief-it")
    provider = cfg.get("tts_provider", "edge-tts")
    profile = get_channel_voice_profile(channel)
    narrator_cfg = get_voice_for_speaker(channel, "narrator", provider=provider)

    mp3_path = str(OUTPUT_DIR / f"{output_prefix}.mp3")
    srt_path = str(OUTPUT_DIR / f"{output_prefix}.srt")

    synthesize_clip(
        text=full_text,
        voice_id=narrator_cfg["voice_id"],
        output_mp3=mp3_path,
        provider=provider,
        rate=narrator_cfg["rate"],
        pitch=narrator_cfg["pitch"]
    )

    duration_sec = get_audio_duration_seconds(mp3_path)
    srt_content, _ = build_estimated_srt(full_text, start_ms=0, duration_ms=int(duration_sec * 1000))

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content + "\n")

    return mp3_path, srt_path


def preview_voice_sample(voice_id: str, sample_text: str = "Welcome to YouTube Turbo Studio. Every universe begins with a single thought.", provider: str = "edge-tts") -> str:
    """Generate sample audio clip for UI preview."""
    sample_mp3 = str(OUTPUT_DIR / "voice_sample.mp3")
    synthesize_clip(
        text=sample_text,
        voice_id=voice_id,
        output_mp3=sample_mp3,
        provider=provider
    )
    return sample_mp3
