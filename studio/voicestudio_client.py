"""Client adapter for debpalash/VoiceStudio local server (https://github.com/debpalash/voicestudio)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import requests

from .config import VOICESTUDIO_URL


class VoiceStudioClient:
    def __init__(self, base_url: str = VOICESTUDIO_URL, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health_check(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/v1/models", timeout=5.0)
            return r.status_code == 200
        except requests.RequestException:
            return False

    def list_voices(self) -> list[dict]:
        r = requests.get(f"{self.base_url}/v1/audio/voices", timeout=10.0)
        r.raise_for_status()
        return r.json().get("voices", [])

    def synthesize_openai_compat(
        self,
        text: str,
        voice: str,
        out_wav: Path,
        model: str = "tts-1-hd",
        speed: float = 1.0,
        instruct: Optional[str] = None,
    ) -> Path:
        payload: dict = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": "wav",
            "speed": speed,
        }
        if instruct:
            payload["instruct"] = instruct
        r = requests.post(f"{self.base_url}/v1/audio/speech", json=payload, timeout=self.timeout)
        r.raise_for_status()
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        out_wav.write_bytes(r.content)
        return out_wav

    def synthesize_story_segments(self, episode_dir: Path, script_data: dict) -> None:
        scenes_dir = episode_dir / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)
        for seg in script_data["segments"]:
            raw_wav = scenes_dir / f"{seg['id']}_raw.wav"
            if raw_wav.exists() or (scenes_dir / f"{seg['id']}_raw.mp3").exists():
                continue
            d = seg.get("director", {})
            instruct = ", ".join(
                v for v in (d.get("emotion"), d.get("intimacy"), d.get("pace"), d.get("energy")) if v
            )
            voice_ref = seg.get("voicestudio_profile", seg.get("voice_id", "narrator"))
            self.synthesize_openai_compat(
                text=seg["text"],
                voice=voice_ref,
                out_wav=raw_wav,
                speed=float(seg.get("pace_multiplier", 1.0)),
                instruct=instruct or None,
            )
