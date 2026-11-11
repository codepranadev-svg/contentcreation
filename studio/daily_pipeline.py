"""End-to-end daily story video builder CLI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audio_engine import produce_episode_audio
from .script_parser import export_voicestudio_markdown
from .video_renderer import (
    render_full_16x9_video,
    render_shorts_9x16_video,
    render_thumbnails,
)
from .voicestudio_client import VoiceStudioClient


def build_episode(
    episode_dir: Path,
    use_voicestudio: bool = False,
    voicestudio_url: str | None = None,
    res: int = 720,
) -> dict:
    script_path = episode_dir / "script.json"
    if not script_path.exists():
        raise FileNotFoundError(f"Missing {script_path}")

    script_data = json.loads(script_path.read_text(encoding="utf-8"))
    export_voicestudio_markdown(script_data, episode_dir / "script_voicestudio.md")

    if use_voicestudio:
        client = VoiceStudioClient(voicestudio_url) if voicestudio_url else VoiceStudioClient()
        if not client.health_check():
            raise RuntimeError(f"VoiceStudio server not reachable at {client.base_url}")
        client.synthesize_story_segments(episode_dir, script_data)

    print(f"[1/4] Mixing multi-voice scene-tuned audio for {episode_dir}...")
    manifest = produce_episode_audio(episode_dir, script_data)

    print(f"[2/4] Rendering 16:9 Full Story Video ({res}p, {manifest['total_duration_s']:.1f}s)...")
    full_mp4 = render_full_16x9_video(episode_dir, manifest, res=res)

    print(f"[3/4] Rendering 9:16 YouTube Shorts Teaser ({res}p)...")
    short_mp4 = render_shorts_9x16_video(episode_dir, manifest, res=res)

    print("[4/4] Rendering High-CTR Devanagari Thumbnails...")
    t16, t9 = render_thumbnails(episode_dir, manifest)

    scenes_dir = episode_dir / "scenes"
    for pattern in ("*_dsp.wav", "*_raw_mix.wav", "*_master.wav", "*_vis.mp4", "*_short_*", "thumb_*.ass"):
        for tmp_f in scenes_dir.glob(pattern):
            tmp_f.unlink(missing_ok=True)

    return {
        "episode_dir": str(episode_dir),
        "duration_s": manifest["total_duration_s"],
        "full_16x9": str(full_mp4),
        "shorts_9x16": str(short_mp4),
        "master_mp3": manifest["master_mp3"],
        "thumb_16x9": str(t16),
        "thumb_9x16": str(t9),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Hindi YouTube story episode")
    parser.add_argument("--episode-dir", required=True, help="Path like hindi/2026-11-11")
    parser.add_argument("--res", type=int, default=720, choices=[720, 1080], help="Output resolution height (720 or 1080)")
    parser.add_argument("--voicestudio", action="store_true", help="Synthesize missing raw audio via local VoiceStudio")
    parser.add_argument("--voicestudio-url", default=None, help="Local VoiceStudio URL (default http://127.0.0.1:8000)")
    args = parser.parse_args()

    result = build_episode(
        Path(args.episode_dir),
        use_voicestudio=args.voicestudio,
        voicestudio_url=args.voicestudio_url,
        res=args.res,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
