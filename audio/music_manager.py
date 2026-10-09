"""
Background Music Manager
Handles BGM selection, volume balancing, looping, and mixing with voiceover.
"""
import os
import random
from pathlib import Path
from moviepy.editor import AudioFileClip, CompositeAudioClip, afx
from config import load_config, SONGS_DIR, OUTPUT_DIR
from core.logger import log_info, log_warn, log_success


def get_available_songs() -> list[str]:
    """Return all MP3/WAV files in songs directory."""
    if not SONGS_DIR.exists():
        return []
    return [str(p) for p in SONGS_DIR.glob("*.mp3")] + [str(p) for p in SONGS_DIR.glob("*.wav")]


def mix_voice_and_bgm(voice_path: str, output_path: str = None) -> str:
    """
    Mix narration audio with ambient background music.
    Returns the path to the mixed audio file.
    """
    cfg = load_config()
    music_enabled = cfg.get("music_enabled", True)
    bgm_volume = float(cfg.get("music_volume", 0.12))

    if not output_path:
        output_path = str(OUTPUT_DIR / "final_audio.mp3")

    voice_clip = AudioFileClip(voice_path)
    target_duration = voice_clip.duration

    if not music_enabled or bgm_volume <= 0:
        log_info("BGM is disabled. Exporting clean voiceover.")
        voice_clip.write_audiofile(output_path, logger=None)
        voice_clip.close()
        return output_path

    songs = get_available_songs()
    if not songs:
        log_warn("No background songs found in resources/songs/. Exporting voiceover only.")
        voice_clip.write_audiofile(output_path, logger=None)
        voice_clip.close()
        return output_path

    chosen_song = random.choice(songs)
    log_info(f"Adding background music: {os.path.basename(chosen_song)} (Vol: {int(bgm_volume*100)}%)...")

    try:
        bgm_clip = AudioFileClip(chosen_song)
        # Loop BGM if shorter than narration
        if bgm_clip.duration < target_duration:
            loops_needed = int(target_duration / bgm_clip.duration) + 1
            bgm_clip = afx.audio_loop(bgm_clip, nloops=loops_needed)

        # Audio ducking: ensure background music is balanced and never overpowers narration
        effective_bgm_vol = min(0.18, max(0.04, bgm_volume * 0.70))
        bgm_clip = bgm_clip.volumex(effective_bgm_vol)
        boosted_voice = voice_clip.volumex(1.15)
        if target_duration > 3.0:
            bgm_clip = bgm_clip.audio_fadein(1.2).audio_fadeout(2.0)

        composite = CompositeAudioClip([bgm_clip, boosted_voice])
        # MoviePy 1.0.3 fix: CompositeAudioClip doesn't inherit fps — set it explicitly
        composite.fps = getattr(voice_clip, "fps", None) or getattr(bgm_clip, "fps", None) or 44100
        composite.write_audiofile(output_path, fps=composite.fps, logger=None)

        bgm_clip.close()
        voice_clip.close()
        composite.close()
        log_success("Voice and background music mixed successfully.")
        return output_path
    except Exception as e:
        log_warn(f"Failed to mix BGM: {e}. Falling back to clean voiceover.")
        voice_clip.write_audiofile(output_path, logger=None)
        voice_clip.close()
        return output_path
