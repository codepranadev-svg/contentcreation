"""VoiceStudio-compatible story script parser & exporter."""
from __future__ import annotations

import re
from pathlib import Path


def export_voicestudio_markdown(script_data: dict, out_path: Path) -> None:
    lines = [
        f"# {script_data['title']}",
        "",
        f"> Language: `{script_data['language']}` | Genre: {script_data['genre']}",
        "",
    ]
    chars = script_data.get("characters", {})
    for seg in script_data["segments"]:
        char_info = chars.get(seg["speaker"], {"name": seg["speaker"], "voice_id": seg["voice_id"]})
        emo = seg.get("director", {}).get("emotion", "warm")
        intimacy = seg.get("director", {}).get("intimacy", "intimate")
        pause_after = seg.get("pause_after_ms", 900)
        lines.append(f"# Scene {seg['scene_number']}: {seg['scene_title']}")
        lines.append(
            f"[voice:{char_info['name']} ({seg['voice_id']})][emotion:{emo}, {intimacy}]"
        )
        lines.append(seg["text"].strip())
        lines.append(f"[pause {pause_after}ms]")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


_VOICE_RE = re.compile(r"\[voice:([^\]]+)\]", re.IGNORECASE)
_EMOTION_RE = re.compile(r"\[emotion:([^\]]+)\]", re.IGNORECASE)
_PAUSE_RE = re.compile(r"\[pause\s+(\d+)\s*ms\]", re.IGNORECASE)


def parse_voicestudio_markdown(md_path: Path, language: str, slug: str, date_str: str) -> dict:
    raw = md_path.read_text(encoding="utf-8")
    sections = re.split(r"^#\s+Scene\s+\d+:\s*", raw, flags=re.MULTILINE)
    title_match = re.search(r"^#\s+(.+)$", raw, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else slug

    segments = []
    for idx, block in enumerate(sections[1:], start=1):
        lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
        scene_title = lines[0] if lines else f"Scene {idx}"
        body_lines = lines[1:]
        voice_name = "narrator"
        emotion = "warm"
        pause_ms = 900
        spoken = []
        for ln in body_lines:
            vm = _VOICE_RE.search(ln)
            em = _EMOTION_RE.search(ln)
            pm = _PAUSE_RE.search(ln)
            if vm:
                voice_name = vm.group(1).strip()
            if em:
                emotion = em.group(1).strip()
            if pm:
                pause_ms = int(pm.group(1))
            clean = _PAUSE_RE.sub("", _EMOTION_RE.sub("", _VOICE_RE.sub("", ln))).strip()
            if clean:
                spoken.append(clean)
        segments.append({
            "id": f"{language}_{idx:02d}",
            "scene_number": idx,
            "scene_title": scene_title,
            "speaker": "narrator" if "narrator" in voice_name.lower() else "female_lead",
            "voice_id": voice_name,
            "situation": "custom",
            "dsp_preset": "midnight_narration",
            "director": {"emotion": emotion, "pace": "measured", "intimacy": "intimate"},
            "soundscape": {"ambience": "rain_soft", "music": "melancholy_piano", "ambience_db": -24, "music_db": -20},
            "pace_multiplier": 0.97,
            "pause_before_ms": 400,
            "pause_after_ms": pause_ms,
            "image": f"scenes/scene_{idx:02d}.jpg",
            "camera_motion": "slow_zoom_in",
            "include_in_short": idx in (1, 3),
            "text": " ".join(spoken),
        })
    return {
        "title": title,
        "slug": slug,
        "language": language,
        "date": date_str,
        "genre": "Mature Relationship Drama (YouTube-Safe)",
        "characters": {"narrator": {"name": "Narrator", "voice_id": "voice-00"}},
        "segments": segments,
    }
