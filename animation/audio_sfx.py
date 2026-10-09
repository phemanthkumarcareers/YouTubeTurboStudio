"""
Audio & SFX Layer — Shared Animation Engine
Procedural sound effects synthesis (pop, chime, twinkle, bell, tick) and audio mixing
with narration speech and background music ducking.
"""
import os
import wave
import struct
import math
import numpy as np
from typing import List, Dict, Any, Optional
from core.logger import log_info, log_warn


SFX_DIR = os.path.join(os.path.dirname(__file__), "assets", "sfx")
os.makedirs(SFX_DIR, exist_ok=True)


class SFXGenerator:
    """Synthesizes high-quality sound effect WAV files procedurally."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def get_sfx_path(self, sfx_type: str) -> str:
        """Returns the file path for the requested SFX, generating it if needed."""
        filename = f"{sfx_type}.wav"
        target_path = os.path.join(SFX_DIR, filename)

        if not os.path.exists(target_path):
            self.generate_sfx(sfx_type, target_path)

        return target_path

    def generate_sfx(self, sfx_type: str, output_path: str) -> str:
        """Procedurally generate audio effect waveform."""
        sr = self.sample_rate

        if sfx_type in ("pop", "bubble_pop"):
            duration = 0.12
            t = np.linspace(0, duration, int(sr * duration), False)
            # Frequency upward sweep 300 to 750 Hz
            freq = np.linspace(300, 750, len(t))
            audio = np.sin(2 * np.pi * freq * t) * np.exp(-t * 28.0)

        elif sfx_type in ("chime", "cheerful_chime"):
            duration = 0.8
            t = np.linspace(0, duration, int(sr * duration), False)
            # C major triad harmonics (C6, E6, G6)
            audio = (
                0.5 * np.sin(2 * np.pi * 1046.5 * t) +
                0.35 * np.sin(2 * np.pi * 1318.5 * t) +
                0.25 * np.sin(2 * np.pi * 1567.98 * t)
            ) * np.exp(-t * 4.5)

        elif sfx_type in ("twinkle", "magical_twinkle"):
            duration = 0.9
            audio = np.zeros(int(sr * duration))
            # 4 staggered pings
            pitches = [1200, 1500, 1800, 2200]
            for i, p in enumerate(pitches):
                start_sample = int(i * 0.12 * sr)
                ping_len = int(0.35 * sr)
                t_ping = np.linspace(0, 0.35, ping_len, False)
                ping_wave = np.sin(2 * np.pi * p * t_ping) * np.exp(-t_ping * 10.0)
                end_sample = min(len(audio), start_sample + ping_len)
                audio[start_sample:end_sample] += ping_wave[:end_sample - start_sample] * 0.3

        elif sfx_type in ("gentle_bell", "warm_bell", "bell"):
            duration = 1.4
            t = np.linspace(0, duration, int(sr * duration), False)
            # D5 warm acoustic chime
            audio = (
                0.6 * np.sin(2 * np.pi * 587.33 * t) +
                0.3 * np.sin(2 * np.pi * 1174.66 * t) +
                0.15 * np.sin(2 * np.pi * 1762.0 * t)
            ) * np.exp(-t * 2.5)

        elif sfx_type in ("clock_tick", "tick"):
            duration = 0.05
            t = np.linspace(0, duration, int(sr * duration), False)
            audio = np.sin(2 * np.pi * 850.0 * t) * np.exp(-t * 80.0) * 0.4

        elif sfx_type in ("page_turn", "whoosh"):
            duration = 0.18
            t = np.linspace(0, duration, int(sr * duration), False)
            noise = np.random.uniform(-0.3, 0.3, len(t))
            audio = noise * np.sin(np.pi * t / duration)

        else:
            # Gentle default soft beep
            duration = 0.2
            t = np.linspace(0, duration, int(sr * duration), False)
            audio = np.sin(2 * np.pi * 880.0 * t) * np.exp(-t * 12.0) * 0.3

        # Normalize and convert to 16-bit PCM
        max_val = np.max(np.abs(audio))
        if max_val > 0.001:
            audio = audio / max_val * 0.85

        pcm_data = (audio * 32767).astype(np.int16)

        with wave.open(output_path, "w") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sr)
            wf.writeframes(pcm_data.tobytes())

        return output_path


sfx_generator = SFXGenerator()


def mix_animation_audio(
    total_duration: float,
    output_path: str,
    narration_path: Optional[str] = None,
    sfx_cues: Optional[List[Dict[str, Any]]] = None,
    bgm_path: Optional[str] = None,
    bgm_volume: float = 0.12
) -> str:
    """
    Assembles narration, positioned SFX cues, and optional background music
    into a unified audio file.
    """
    from moviepy.editor import AudioFileClip, CompositeAudioClip
    from moviepy.audio.AudioClip import AudioClip

    audio_clips = []

    # 1. Base silent or narration audio
    if narration_path and os.path.exists(narration_path):
        try:
            voice_clip = AudioFileClip(narration_path)
            # Ensure duration fits or pads
            if voice_clip.duration < total_duration:
                # Keep voice clip at start
                audio_clips.append(voice_clip)
            else:
                voice_clip = voice_clip.subclip(0, total_duration)
                audio_clips.append(voice_clip)
        except Exception as e:
            log_warn(f"[AUDIO] Failed to load narration '{narration_path}': {e}")

    # If no audio clip yet, add a quiet silence carrier
    if not audio_clips:
        silence = AudioClip(lambda t: 0.0, duration=total_duration, fps=44100)
        audio_clips.append(silence)

    # 2. SFX Cues
    if sfx_cues:
        for cue in sfx_cues:
            cue_time = float(cue.get("time", 0.0))
            if cue_time >= total_duration:
                continue
            sfx_type = cue.get("type", "pop")
            vol = float(cue.get("volume", 0.8))
            try:
                sfx_file = sfx_generator.get_sfx_path(sfx_type)
                sfx_clip = AudioFileClip(sfx_file).volumex(vol).set_start(cue_time)
                # Trim if overflows
                if cue_time + sfx_clip.duration > total_duration:
                    sfx_clip = sfx_clip.subclip(0, total_duration - cue_time)
                audio_clips.append(sfx_clip)
            except Exception as e:
                log_warn(f"[AUDIO] Failed to add SFX cue '{sfx_type}' at {cue_time}s: {e}")

    # 3. Background Music (optional)
    if bgm_path and os.path.exists(bgm_path):
        try:
            bgm_clip = AudioFileClip(bgm_path)
            # Loop or crop BGM
            if bgm_clip.duration < total_duration:
                # repeat
                loops = int(math.ceil(total_duration / bgm_clip.duration))
                from moviepy.editor import concatenate_audioclips
                bgm_clip = concatenate_audioclips([bgm_clip] * loops)
            bgm_clip = bgm_clip.subclip(0, total_duration).volumex(bgm_volume)
            audio_clips.insert(0, bgm_clip)
        except Exception as e:
            log_warn(f"[AUDIO] Failed to mix BGM: {e}")

    # Composite audio
    composite = CompositeAudioClip(audio_clips)
    composite.fps = 44100
    composite.duration = total_duration

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    composite.write_audiofile(output_path, fps=44100, nbytes=2, logger=None)
    composite.close()
    for c in audio_clips:
        try:
            c.close()
        except Exception:
            pass

    return output_path
