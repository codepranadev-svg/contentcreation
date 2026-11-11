"""Configuration and voice/path conventions for the Hindi Storytelling Studio."""
from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
HINDI_DIR = ROOT_DIR / "hindi"

SAMPLE_RATE = 44100
CHANNELS = 2

YOUTUBE_LOUDNORM_I = -14.0
YOUTUBE_LOUDNORM_TP = -1.5
YOUTUBE_LOUDNORM_LRA = 11.0

DEFAULT_VOICES = {
    "hi": {
        "narrator": "voice-00",
        "male_lead": "voice-01",
        "female_lead": "voice-02",
    },
}

VOICESTUDIO_URL = os.environ.get("VOICESTUDIO_URL", "http://127.0.0.1:8000")


def resolve_episode_dir(language: str, slug: str, date_str: str) -> Path:
    """Resolve Hindi episode folder: hindi/<YYYY-MM-DD>/."""
    lang = language.lower().strip()
    if lang in ("hi", "hindi"):
        return HINDI_DIR / date_str
    raise ValueError(f"Unsupported language (Hindi-only channel): {language}")
