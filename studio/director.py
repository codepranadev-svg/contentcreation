"""Directorial scene & emotion taxonomy inspired by debpalash/VoiceStudio."""
from __future__ import annotations

from dataclasses import dataclass

TAXONOMY = {
    "energy": ["calm", "relaxed", "steady", "energetic", "urgent", "frantic"],
    "emotion": [
        "happy", "sad", "angry", "surprised", "fearful", "neutral",
        "warm", "cold", "hopeful", "resigned", "mysterious", "vulnerable",
        "yearning", "conflicted",
    ],
    "pace": ["slow", "measured", "conversational", "quick", "rushed"],
    "intimacy": ["whispered", "intimate", "conversational", "projected", "announcing"],
}


@dataclass(frozen=True)
class SceneAcousticProfile:
    name: str
    highpass_hz: float
    low_shelf_db: float
    presence_hz: float
    presence_db: float
    air_db: float
    reverb_wet: float
    reverb_room_ms: float
    comp_threshold_db: float
    comp_ratio: float
    gain_db: float
    inter_sentence_pause_ms: int
    pace_multiplier: float


PROFILES: dict[str, SceneAcousticProfile] = {
    "midnight_narration": SceneAcousticProfile(
        name="midnight_narration",
        highpass_hz=75.0,
        low_shelf_db=2.0,
        presence_hz=3200.0,
        presence_db=1.5,
        air_db=0.5,
        reverb_wet=0.05,
        reverb_room_ms=32.0,
        comp_threshold_db=-18.0,
        comp_ratio=2.4,
        gain_db=0.0,
        inter_sentence_pause_ms=420,
        pace_multiplier=0.97,
    ),
    "intimate_whisper": SceneAcousticProfile(
        name="intimate_whisper",
        highpass_hz=90.0,
        low_shelf_db=2.8,
        presence_hz=2600.0,
        presence_db=0.8,
        air_db=-1.2,
        reverb_wet=0.02,
        reverb_room_ms=18.0,
        comp_threshold_db=-21.0,
        comp_ratio=2.8,
        gain_db=-0.4,
        inter_sentence_pause_ms=520,
        pace_multiplier=0.95,
    ),
    "rain_confession": SceneAcousticProfile(
        name="rain_confession",
        highpass_hz=75.0,
        low_shelf_db=1.5,
        presence_hz=2900.0,
        presence_db=2.2,
        air_db=1.0,
        reverb_wet=0.11,
        reverb_room_ms=44.0,
        comp_threshold_db=-17.0,
        comp_ratio=2.2,
        gain_db=0.3,
        inter_sentence_pause_ms=460,
        pace_multiplier=0.98,
    ),
    "heartbreak_sad": SceneAcousticProfile(
        name="heartbreak_sad",
        highpass_hz=85.0,
        low_shelf_db=2.2,
        presence_hz=2400.0,
        presence_db=0.5,
        air_db=-1.5,
        reverb_wet=0.08,
        reverb_room_ms=38.0,
        comp_threshold_db=-20.0,
        comp_ratio=2.2,
        gain_db=-0.6,
        inter_sentence_pause_ms=560,
        pace_multiplier=0.94,
    ),
    "dawn_warmth": SceneAcousticProfile(
        name="dawn_warmth",
        highpass_hz=80.0,
        low_shelf_db=1.2,
        presence_hz=3600.0,
        presence_db=1.8,
        air_db=1.4,
        reverb_wet=0.06,
        reverb_room_ms=28.0,
        comp_threshold_db=-18.0,
        comp_ratio=2.0,
        gain_db=0.2,
        inter_sentence_pause_ms=430,
        pace_multiplier=0.97,
    ),
}


def get_profile(preset_name: str, director_tokens: dict | None = None) -> SceneAcousticProfile:
    base = PROFILES.get(preset_name, PROFILES["midnight_narration"])
    if not director_tokens:
        return base

    pace_mult = base.pace_multiplier
    pause_ms = base.inter_sentence_pause_ms
    reverb_wet = base.reverb_wet

    pace = str(director_tokens.get("pace", "")).lower()
    if pace == "slow":
        pace_mult = min(pace_mult, 0.94)
        pause_ms = max(pause_ms, 520)
    elif pace == "quick":
        pace_mult = max(pace_mult, 1.02)
        pause_ms = min(pause_ms, 340)

    intimacy = str(director_tokens.get("intimacy", "")).lower()
    if intimacy == "whispered":
        reverb_wet = min(reverb_wet, 0.03)
    elif intimacy == "projected":
        reverb_wet = max(reverb_wet, 0.10)

    return SceneAcousticProfile(
        name=base.name,
        highpass_hz=base.highpass_hz,
        low_shelf_db=base.low_shelf_db,
        presence_hz=base.presence_hz,
        presence_db=base.presence_db,
        air_db=base.air_db,
        reverb_wet=reverb_wet,
        reverb_room_ms=base.reverb_room_ms,
        comp_threshold_db=base.comp_threshold_db,
        comp_ratio=base.comp_ratio,
        gain_db=base.gain_db,
        inter_sentence_pause_ms=pause_ms,
        pace_multiplier=pace_mult,
    )
