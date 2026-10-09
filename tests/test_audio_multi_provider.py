"""
Tests for Multi-Provider Audio Generation & Voice Profiles
Verifies channel voice isolation, multi-character speaker role resolution,
dialogue parsing, SRT timestamp formatting, and fallback mechanisms.
"""
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from audio.voice_profiles import (
    CHANNEL_VOICE_PROFILES,
    SUPPORTED_AUDIO_PROVIDERS,
    PROVIDER_VOICES,
    get_channel_voice_profile,
    resolve_speaker_role,
    get_voice_for_speaker,
    parse_dialogue_line
)
from audio.audio_service import (
    _format_srt_time,
    build_estimated_srt,
    test_elevenlabs_connection,
    test_openai_tts_connection,
    get_audio_duration_seconds
)


class TestVoiceProfiles(unittest.TestCase):
    def test_channel_voice_profiles_exist(self):
        self.assertIn("kids", CHANNEL_VOICE_PROFILES)
        self.assertIn("elders", CHANNEL_VOICE_PROFILES)
        self.assertIn("the-ai-brief-it", CHANNEL_VOICE_PROFILES)

    def test_kids_profile_has_multi_character_roles(self):
        kids_roles = CHANNEL_VOICE_PROFILES["kids"]["roles"]
        self.assertIn("narrator", kids_roles)
        self.assertIn("character_1", kids_roles)
        self.assertIn("character_2", kids_roles)

    def test_resolve_speaker_role(self):
        self.assertEqual(resolve_speaker_role("Narrator"), "narrator")
        self.assertEqual(resolve_speaker_role("Pip the Bunny"), "character_1")
        self.assertEqual(resolve_speaker_role("Barnaby the Bear"), "character_2")
        self.assertEqual(resolve_speaker_role("Professor Owl"), "character_3")
        self.assertEqual(resolve_speaker_role("Unknown Child"), "character_1")

    def test_parse_dialogue_line(self):
        spk, text = parse_dialogue_line("Bunny: Look at the giant rainbow!")
        self.assertEqual(spk, "Bunny")
        self.assertEqual(text, "Look at the giant rainbow!")

        spk, text = parse_dialogue_line("Once upon a time in the quiet woods.")
        self.assertEqual(spk, "Narrator")
        self.assertEqual(text, "Once upon a time in the quiet woods.")

    def test_get_voice_for_speaker_edge_tts(self):
        voice_info = get_voice_for_speaker("kids", "Bunny", provider="edge-tts")
        self.assertIn("voice_id", voice_info)
        self.assertEqual(voice_info["role"], "character_1")
        self.assertIn("Neural", voice_info["voice_id"])

    def test_get_voice_for_speaker_openai(self):
        voice_info = get_voice_for_speaker("kids", "Narrator", provider="openai-tts")
        self.assertEqual(voice_info["voice_id"], "nova")
        self.assertEqual(voice_info["role"], "narrator")


class TestAudioService(unittest.TestCase):
    def test_format_srt_time(self):
        self.assertEqual(_format_srt_time(0), "00:00:00,000")
        self.assertEqual(_format_srt_time(1500), "00:00:01,500")
        self.assertEqual(_format_srt_time(65432), "00:01:05,432")

    def test_build_estimated_srt(self):
        srt_chunk, next_idx = build_estimated_srt("Hello world. Welcome to the studio.", start_ms=0, duration_ms=4000, start_idx=1)
        self.assertIn("00:00:00,000 -->", srt_chunk)
        self.assertGreaterEqual(next_idx, 2)

    def test_empty_key_validations(self):
        ok_el, msg_el = test_elevenlabs_connection("")
        self.assertFalse(ok_el)
        self.assertIn("empty", msg_el.lower())

        ok_oai, msg_oai = test_openai_tts_connection("")
        self.assertFalse(ok_oai)
        self.assertIn("empty", msg_oai.lower())

    def test_get_audio_duration_missing_file(self):
        dur = get_audio_duration_seconds("non_existent_file.mp3")
        self.assertEqual(dur, 1.0)


if __name__ == "__main__":
    unittest.main()
