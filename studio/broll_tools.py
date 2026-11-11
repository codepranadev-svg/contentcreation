"""Stock B-roll & YouTube hook research helpers (inspired by MoneyPrinterTurbo, OpenMontage & yt-dlp)."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

import requests


def fetch_pexels_videos(
    query: str,
    out_dir: Path,
    count: int = 2,
    orientation: str = "landscape",
    api_key: Optional[str] = None,
) -> list[Path]:
    """Download royalty-free real-human stock MP4 clips from Pexels (MoneyPrinterTurbo pattern)."""
    key = api_key or os.environ.get("PEXELS_API_KEY", "")
    if not key:
        raise RuntimeError("Set PEXELS_API_KEY to fetch Pexels stock B-roll clips.")

    out_dir.mkdir(parents=True, exist_ok=True)
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": key},
        params={"query": query, "per_page": count, "orientation": orientation},
        timeout=30,
    )
    r.raise_for_status()
    saved: list[Path] = []
    for idx, vid in enumerate(r.json().get("videos", [])[:count], start=1):
        files = sorted(
            vid.get("video_files", []),
            key=lambda f: abs((f.get("height") or 720) - 720),
        )
        if not files:
            continue
        dl_url = files[0]["link"]
        dst = out_dir / f"pexels_{idx:02d}.mp4"
        with requests.get(dl_url, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            with dst.open("wb") as fh:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        fh.write(chunk)
        saved.append(dst)
    return saved


def analyze_youtube_hooks(video_url: str, out_dir: Path) -> Path:
    """Download Hindi subtitle/metadata info via yt-dlp locally to study hooks & retention pacing."""
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "yt-dlp",
            "--skip-download",
            "--write-auto-sub",
            "--sub-langs", "hi,en",
            "--write-info-json",
            "-o", str(out_dir / "%(id)s.%(ext)s"),
            video_url,
        ],
        check=True,
    )
    return out_dir
