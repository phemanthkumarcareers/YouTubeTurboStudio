"""
Edge-TTS Audio & SRT Subtitle Generator
Generates high quality natural voiceover with word-level synchronized SRT subtitle cues.
Completely free, no API key required.
"""
import asyncio
import os
import edge_tts
from config import load_config, OUTPUT_DIR
from core.logger import log_info, log_success, log_warn


def _format_srt_time(ms: int) -> str:
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


async def _synthesize_edge_tts(text: str, voice: str, rate: str, pitch: str, output_mp3: str, output_srt: str):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    submaker = edge_tts.SubMaker()
    total_audio_bytes = 0

    with open(output_mp3, "wb") as f_audio:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f_audio.write(chunk["data"])
                total_audio_bytes += len(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)

    srt_content = submaker.get_srt().strip()

    # Fallback if no boundary events received
    if not srt_content:
        # Estimate ~150 words per minute / split sentences
        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if not sentences:
            sentences = [text]
        # Estimate duration roughly from file size (assuming ~128kbps = 16KB/sec)
        est_duration = max(3.0, total_audio_bytes / 16000.0) if total_audio_bytes > 0 else 5.0
        dur_per_s = est_duration / len(sentences)
        srt_lines = []
        for i, s in enumerate(sentences, 1):
            s_start = int((i - 1) * dur_per_s * 1000)
            s_end = int(i * dur_per_s * 1000)
            srt_lines.append(f"{i}\n{_format_srt_time(s_start)} --> {_format_srt_time(s_end)}\n{s}\n")
        srt_content = "\n".join(srt_lines)

    with open(output_srt, "w", encoding="utf-8") as f_srt:
        f_srt.write(srt_content + "\n")

    log_info(f"Subtitles written to {os.path.basename(output_srt)} ({len(srt_content.splitlines())} lines)")


def generate_speech(full_text: str, output_prefix: str = "narration") -> tuple[str, str]:
    """
    Synthesize audio and subtitle files for narration.
    Returns: (mp3_path, srt_path)
    """
    cfg = load_config()
    voice = cfg.get("voice_id", "en-US-JennyNeural")
    rate = cfg.get("voice_rate", "+0%")
    pitch = cfg.get("voice_pitch", "+0Hz")

    mp3_path = str(OUTPUT_DIR / f"{output_prefix}.mp3")
    srt_path = str(OUTPUT_DIR / f"{output_prefix}.srt")

    log_info(f"Synthesizing voiceover with Edge-TTS ({voice}, rate={rate}, pitch={pitch})...")

    # Create a fresh event loop per call — safe in any thread (main or background)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_synthesize_edge_tts(full_text, voice, rate, pitch, mp3_path, srt_path))
    finally:
        loop.close()

    log_success(f"Voiceover synthesized: {os.path.basename(mp3_path)}")
    return mp3_path, srt_path


def preview_voice_sample(voice_id: str, sample_text: str = "Welcome to YouTube Turbo Studio. Every universe begins with a single thought.") -> str:
    """Generate a quick voice sample for audio preview in UI."""
    sample_mp3 = str(OUTPUT_DIR / "voice_sample.mp3")
    sample_srt = str(OUTPUT_DIR / "voice_sample.srt")
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_synthesize_edge_tts(sample_text, voice_id, "+0%", "+0Hz", sample_mp3, sample_srt))
    finally:
        loop.close()
    return sample_mp3
