"""Automated live-action motion & lip-sync generator for external Colab / API execution.

Supports:
  - Google Gemini Veo 3.1 (`GEMINI_API_KEY`) via `google-genai`
  - Fal.ai Kling 2.6 Pro + Sync.so LipSync (`FAL_KEY`) via `fal-client`

Cannot run inside offline/CPU-only sandboxes without API keys; designed for Google Colab
or any machine with outbound API access.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

from .daily_pipeline import build_episode


def _extract_shot_prompts(prompts_md: Path) -> dict[str, str]:
    """Extract shot-specific camera & acting descriptions keyed by shot stem (e.g. shot_01a)."""
    if not prompts_md.exists():
        return {}
    text = prompts_md.read_text(encoding="utf-8")
    prompts: dict[str, str] = {}
    pattern = re.compile(
        r"Anchor:\*\*\s*`scenes/(shot_\w+)\.jpg`\s*\n\s*\*Camera & Action:\*\s*(.+)",
        re.MULTILINE,
    )
    for m in pattern.finditer(text):
        prompts[m.group(1)] = (
            "Photorealistic 35mm live-action Indian cinema, continuous natural human movement, "
            "subtle blinking, breathing, realistic fabric and lighting physics. "
            + m.group(2).strip()
        )
    return prompts


def generate_with_veo(episode_dir: Path, clips_dir: Path, model: str = "veo-3.1-fast-generate-preview") -> int:
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY (or GOOGLE_API_KEY) before running with --provider veo")

    client = genai.Client(api_key=api_key)
    script_data = json.loads((episode_dir / "script.json").read_text(encoding="utf-8"))
    shot_prompts = _extract_shot_prompts(episode_dir / "15_shot_cinema_prompts.md")
    clips_dir.mkdir(parents=True, exist_ok=True)
    created = 0

    for seg in script_data["segments"]:
        for sh in seg.get("shots", []):
            src_rel = sh["image"]
            stem = Path(src_rel).stem
            out_mp4 = clips_dir / f"{stem}.mp4"
            if out_mp4.exists() and out_mp4.stat().st_size > 1024:
                continue
            keyframe = episode_dir / "scenes" / f"{stem}.jpg"
            prompt = shot_prompts.get(stem, f"Photorealistic live-action cinematic sequence: {seg['scene_title']}")
            print(f"[Veo] Generating {stem}.mp4 from {keyframe.name}...")
            op = client.models.generate_videos(
                model=model,
                source=types.GenerateVideosSource(
                    prompt=prompt,
                    image=types.Image.from_file(location=str(keyframe)),
                ),
                config=types.GenerateVideosConfig(
                    number_of_videos=1,
                    duration_seconds=8,
                    aspect_ratio="16:9",
                    person_generation="allow_adult",
                    enhance_prompt=True,
                ),
            )
            while not op.done:
                time.sleep(15)
                op = client.operations.get(op)
            gen = op.response.generated_videos[0]
            client.files.download(file=gen.video)
            gen.video.save(str(out_mp4))
            created += 1
    return created


def generate_with_fal(episode_dir: Path, clips_dir: Path) -> int:
    import fal_client
    import requests

    if not os.environ.get("FAL_KEY"):
        raise RuntimeError("Set FAL_KEY before running with --provider fal")

    script_data = json.loads((episode_dir / "script.json").read_text(encoding="utf-8"))
    shot_prompts = _extract_shot_prompts(episode_dir / "15_shot_cinema_prompts.md")
    clips_dir.mkdir(parents=True, exist_ok=True)
    created = 0

    for seg in script_data["segments"]:
        speaker = seg.get("speaker", "narrator")
        raw_audio = episode_dir / "scenes" / f"{seg['id']}_raw.mp3"
        for sh in seg.get("shots", []):
            stem = Path(sh["image"]).stem
            out_mp4 = clips_dir / f"{stem}.mp4"
            if out_mp4.exists() and out_mp4.stat().st_size > 1024:
                continue
            keyframe = episode_dir / "scenes" / f"{stem}.jpg"
            prompt = shot_prompts.get(stem, f"Photorealistic live-action cinema: {seg['scene_title']}")
            print(f"[Fal Kling] Generating motion clip {stem}.mp4...")
            img_url = fal_client.upload_file(str(keyframe))
            res = fal_client.subscribe(
                "fal-ai/kling-video/v2.6/pro/image-to-video",
                arguments={
                    "prompt": prompt,
                    "start_image_url": img_url,
                    "duration": "10",
                    "aspect_ratio": "16:9",
                },
                with_logs=True,
            )
            video_url = res["video"]["url"]
            if speaker != "narrator" and raw_audio.exists():
                print(f"[Fal Sync] Applying Hindi dialogue lip-sync for {stem}.mp4...")
                audio_url = fal_client.upload_file(str(raw_audio))
                sync_res = fal_client.subscribe(
                    "fal-ai/sync-lipsync",
                    arguments={"video_url": video_url, "audio_url": audio_url},
                    with_logs=True,
                )
                video_url = sync_res["video"]["url"]

            with requests.get(video_url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with out_mp4.open("wb") as fh:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            fh.write(chunk)
            created += 1
    return created


def generate_with_sora(episode_dir: Path, clips_dir: Path, model: str = "sora-2") -> int:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY before running with --provider sora")

    base_url = os.environ.get("OPENAI_BASE_URL") or None
    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    script_data = json.loads((episode_dir / "script.json").read_text(encoding="utf-8"))
    shot_prompts = _extract_shot_prompts(episode_dir / "15_shot_cinema_prompts.md")
    clips_dir.mkdir(parents=True, exist_ok=True)
    created = 0

    for seg in script_data["segments"]:
        for sh in seg.get("shots", []):
            stem = Path(sh["image"]).stem
            out_mp4 = clips_dir / f"{stem}.mp4"
            if out_mp4.exists() and out_mp4.stat().st_size > 1024:
                continue
            keyframe = episode_dir / "scenes" / f"{stem}.jpg"
            prompt = shot_prompts.get(stem, f"Photorealistic live-action cinematic sequence: {seg['scene_title']}")
            print(f"[Sora] Generating {stem}.mp4 from {keyframe.name}...")
            with keyframe.open("rb") as ref_fh:
                video = client.videos.create(
                    model=model,
                    prompt=prompt,
                    size="1280x720",
                    seconds=8,
                    input_reference=ref_fh,
                )
            while getattr(video, "status", "") in ("queued", "in_progress"):
                time.sleep(15)
                video = client.videos.retrieve(video.id)
            if getattr(video, "status", "") != "completed":
                raise RuntimeError(f"Sora video generation failed for {stem}: status={getattr(video, 'status', 'unknown')}")
            content = client.videos.download_content(video.id, variant="video")
            content.write_to_file(str(out_mp4))
            created += 1
    return created


def swap_clips_and_render(episode_dir: Path, clips_dir: Path, res: int = 1080) -> dict:
    script_path = episode_dir / "script.json"
    script_data = json.loads(script_path.read_text(encoding="utf-8"))
    swapped = 0

    for seg in script_data["segments"]:
        for sh in seg.get("shots", []):
            stem = Path(sh["image"]).stem
            clip = clips_dir / f"{stem}.mp4"
            if clip.exists() and clip.stat().st_size > 1024:
                dst = episode_dir / "scenes" / f"{stem}.mp4"
                if clip.resolve() != dst.resolve():
                    dst.write_bytes(clip.read_bytes())
                sh["image"] = f"scenes/{stem}.mp4"
                swapped += 1
        for key in ("image", "short_image"):
            if key in seg:
                stem = Path(seg[key]).stem
                if (episode_dir / "scenes" / f"{stem}.mp4").exists():
                    seg[key] = f"scenes/{stem}.mp4"

    script_path.write_text(json.dumps(script_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Swapped {swapped} live-action .mp4 clips into {script_path}")
    return build_episode(episode_dir, res=res, skip_audio=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate & assemble live-action .mp4 clips via Veo, Fal.ai, or Sora")
    parser.add_argument("--episode-dir", required=True)
    parser.add_argument("--clips-dir", default=None)
    parser.add_argument("--provider", choices=["veo", "fal", "sora", "none"], default="none")
    parser.add_argument("--res", type=int, default=1080, choices=[720, 1080])
    args = parser.parse_args()

    ep_dir = Path(args.episode_dir)
    clips_dir = Path(args.clips_dir) if args.clips_dir else (ep_dir / "scenes" / "clips")
    if args.provider == "veo":
        generate_with_veo(ep_dir, clips_dir)
    elif args.provider == "fal":
        generate_with_fal(ep_dir, clips_dir)
    elif args.provider == "sora":
        generate_with_sora(ep_dir, clips_dir)

    result = swap_clips_and_render(ep_dir, clips_dir, res=args.res)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
