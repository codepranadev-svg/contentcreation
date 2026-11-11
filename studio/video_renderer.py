"""FFmpeg multi-shot video & Devanagari thumbnail renderer for 16:9 YouTube and 9:16 Shorts."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from .config import CHANNEL_NAME_HI, FONTS_DIR, SAMPLE_RATE
from .subtitle_engine import write_full_ass, write_shorts_ass, write_srt

_VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}


def _motion_expr(motion: str, frames: int) -> tuple[str, str, str]:
    f = max(1, frames)
    if motion == "slow_zoom_out":
        z = f"max(1.0,1.07-0.07*(on/{f}))"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif motion == "pan_right":
        z = "1.06"
        x = f"(iw-iw/zoom)*(on/{f})"
        y = "ih/2-(ih/zoom/2)"
    elif motion == "pan_left":
        z = "1.06"
        x = f"(iw-iw/zoom)*(1-on/{f})"
        y = "ih/2-(ih/zoom/2)"
    else:
        z = f"min(1.07,1.0+0.07*(on/{f}))"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    return z, x, y


def render_rain_overlay_loop(out_mp4: Path, width: int, height: int, fps: int = 24) -> Path:
    """Create a 2-second seamless falling-rain luminance overlay video."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    n_frames = fps * 2
    rng = np.random.default_rng(2026)
    n_drops = 145
    xs = rng.uniform(0, width, n_drops)
    ys = rng.uniform(0, height, n_drops)
    speeds = rng.uniform(22.0, 42.0, n_drops)
    lengths = rng.uniform(20.0, 48.0, n_drops)
    alphas = rng.integers(50, 125, n_drops)

    raw_frames: list[bytes] = []
    for f in range(n_frames):
        img = Image.new("RGB", (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        for i in range(n_drops):
            y0 = (ys[i] + f * speeds[i]) % height
            x0 = (xs[i] - f * (speeds[i] * 0.14)) % width
            y1 = y0 + lengths[i]
            x1 = x0 - lengths[i] * 0.14
            a = int(alphas[i])
            draw.line((x0, y0, x1, y1), fill=(a, a, a), width=1)
        raw_frames.append(np.array(img, dtype=np.uint8).tobytes())

    proc = subprocess.Popen(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps),
            "-i", "-", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            "-pix_fmt", "yuv420p", str(out_mp4),
        ],
        stdin=subprocess.PIPE,
    )
    proc.communicate(b"".join(raw_frames))
    if proc.returncode != 0:
        raise RuntimeError("Failed to generate rain overlay loop")
    return out_mp4


def render_scene_clip(
    media_path: Path,
    duration_s: float,
    motion: str,
    out_mp4: Path,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    rain_loop: Optional[Path] = None,
    crf: int = 21,
) -> None:
    """Render either a still photo (Ken Burns) or real video clip (.mp4/.mov) into a scene clip."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    threads = str(min(8, os.cpu_count() or 4))
    is_video = media_path.suffix.lower() in _VIDEO_EXTS

    if is_video:
        inputs = ["-stream_loop", "-1", "-t", f"{duration_s:.3f}", "-i", str(media_path)]
        base_filter = (
            f"[0:v]fps={fps},scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},vignette=PI/5,format=yuv420p[base]"
        )
    else:
        frames = max(24, int(round(duration_s * fps)))
        z, x, y = _motion_expr(motion, frames)
        up_w = int(width * 1.35)
        up_h = int(height * 1.35)
        inputs = ["-loop", "1", "-i", str(media_path)]
        base_filter = (
            f"[0:v]scale={up_w}:{up_h}:force_original_aspect_ratio=increase,"
            f"crop={up_w}:{up_h},"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={width}x{height}:fps={fps},"
            f"vignette=PI/5,format=yuv420p[base]"
        )

    if rain_loop and rain_loop.exists():
        inputs.extend(["-stream_loop", "-1", "-t", f"{duration_s:.3f}", "-i", str(rain_loop)])
        fc = (
            f"{base_filter};"
            f"[1:v]format=yuv420p[rn];"
            f"[base][rn]blend=c0_mode=screen:c0_opacity=0.62:c1_mode=normal:c2_mode=normal[vout]"
        )
    else:
        fc = base_filter.replace("[base]", "[vout]")

    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            *inputs,
            "-filter_complex", fc,
            "-map", "[vout]",
            "-t", f"{duration_s:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf),
            "-threads", threads, "-an", str(out_mp4),
        ],
        check=True,
    )


def _crossfade_clips(clips: list[tuple[Path, float]], fade_s: float, out_mp4: Path, crf: int = 21) -> None:
    if len(clips) == 1:
        clips[0][0].replace(out_mp4)
        return
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    threads = str(min(8, os.cpu_count() or 4))
    inputs: list[str] = []
    for cp, _ in clips:
        inputs.extend(["-i", str(cp)])
    filters: list[str] = []
    prev = "[0:v]"
    offset = clips[0][1] - fade_s
    for idx in range(1, len(clips)):
        nxt = f"[xf{idx}]"
        filters.append(f"{prev}[{idx}:v]xfade=transition=fade:duration={fade_s:.2f}:offset={offset:.3f}{nxt}")
        prev = nxt
        offset += clips[idx][1] - fade_s
    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            *inputs,
            "-filter_complex", ";".join(filters),
            "-map", prev,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-threads", threads, "-an", str(out_mp4),
        ],
        check=True,
    )


def render_full_16x9_video(episode_dir: Path, manifest: dict, res: int = 720) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    scenes_dir = episode_dir / "scenes"
    slug = manifest["slug"]
    fps = 24
    scene_fade_s = 0.75
    shot_fade_s = 0.55
    width, height = (1920, 1080) if res >= 1080 else (1280, 720)

    srt_path = episode_dir / "subtitles.srt"
    ass_path = episode_dir / "subtitles.ass"
    write_srt(manifest["cues"], srt_path)
    write_full_ass(manifest, ass_path)

    needs_rain = any(
        sc.get("rain_overlay") or any(sh.get("rain_overlay") for sh in sc.get("shots", []))
        for sc in manifest["scenes"]
    )
    rain_loop_path: Optional[Path] = None
    if needs_rain:
        rain_loop_path = scenes_dir / f"rain_loop_{width}x{height}.mp4"
        render_rain_overlay_loop(rain_loop_path, width, height, fps=fps)

    total_dur_s = float(manifest["total_duration_s"])
    scene_clips: list[tuple[Path, float]] = []
    n_scenes = len(manifest["scenes"])

    for idx, sc in enumerate(manifest["scenes"]):
        start_s = 0.0 if idx == 0 else float(sc["scene_start"])
        end_s = total_dur_s if idx == n_scenes - 1 else float(sc["scene_end"])
        scene_dur = (end_s - start_s) + (scene_fade_s if idx < n_scenes - 1 else 0.0)
        scene_vis_path = scenes_dir / f"{sc['id']}_vis.mp4"

        shots = sc.get("shots") or [
            {"image": sc["image"], "camera_motion": sc.get("camera_motion", "slow_zoom_in"), "weight": 1.0}
        ]
        if len(shots) == 1:
            sh = shots[0]
            use_rain = rain_loop_path if (sh.get("rain_overlay") or sc.get("rain_overlay")) else None
            render_scene_clip(
                episode_dir / sh["image"], scene_dur,
                sh.get("camera_motion", sc.get("camera_motion", "slow_zoom_in")),
                scene_vis_path, width=width, height=height, fps=fps, rain_loop=use_rain,
            )
        else:
            raw_weights = [max(0.1, float(sh.get("weight", 1.0))) for sh in shots]
            w_sum = sum(raw_weights)
            shot_clips: list[tuple[Path, float]] = []
            for s_idx, sh in enumerate(shots):
                frac = raw_weights[s_idx] / w_sum
                sh_dur = (scene_dur * frac) + (shot_fade_s if s_idx < len(shots) - 1 else 0.0)
                sh_clip = scenes_dir / f"{sc['id']}_shot_{s_idx}.mp4"
                use_rain = rain_loop_path if (sh.get("rain_overlay") or sc.get("rain_overlay")) else None
                render_scene_clip(
                    episode_dir / sh["image"], sh_dur,
                    sh.get("camera_motion", "slow_zoom_in"),
                    sh_clip, width=width, height=height, fps=fps, rain_loop=use_rain, crf=20,
                )
                shot_clips.append((sh_clip, sh_dur))
            _crossfade_clips(shot_clips, shot_fade_s, scene_vis_path, crf=20)

        scene_clips.append((scene_vis_path, scene_dur))

    inputs: list[str] = []
    for clip_path, _ in scene_clips:
        inputs.extend(["-i", str(clip_path)])
    audio_idx = len(scene_clips)
    inputs.extend(["-i", manifest["master_wav"]])

    filter_parts: list[str] = []
    prev_label = "[0:v]"
    offset = scene_clips[0][1] - scene_fade_s
    for idx in range(1, len(scene_clips)):
        out_label = f"[xf{idx}]"
        filter_parts.append(
            f"{prev_label}[{idx}:v]xfade=transition=fade:duration={scene_fade_s:.2f}:offset={offset:.3f}{out_label}"
        )
        prev_label = out_label
        offset += scene_clips[idx][1] - scene_fade_s

    box_y = int(height * 0.78)
    box_h = height - box_y
    wave_w = int(width * 0.40)
    wave_h = max(32, int(height * 0.05))
    wave_offset_y = max(36, int(height * 0.053))

    ass_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")
    fonts_escaped = str(FONTS_DIR).replace("\\", "/").replace(":", "\\:")
    filter_parts.append(
        f"{prev_label}drawbox=x=0:y={box_y}:w={width}:h={box_h}:color=black@0.48:t=fill[bg]"
    )
    filter_parts.append(
        f"[{audio_idx}:a]aformat=channel_layouts=stereo,showwaves=s={wave_w}x{wave_h}:mode=cline:colors=#E8C27A@0.55|#C97B84@0.45:rate={fps}[wave]"
    )
    filter_parts.append(
        f"[bg][wave]overlay=x=(W-w)/2:y=H-{wave_offset_y}:shortest=1[withwave]"
    )
    filter_parts.append(
        f"[withwave]ass='{ass_escaped}':fontsdir='{fonts_escaped}',format=yuv420p[vout]"
    )

    out_mp4 = episode_dir / f"{slug}_full_16x9.mp4"
    threads = str(min(8, os.cpu_count() or 4))
    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            *inputs,
            "-filter_complex", ";".join(filter_parts),
            "-map", "[vout]", "-map", f"{audio_idx}:a",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
            "-c:a", "aac", "-b:a", "128k", "-ar", str(SAMPLE_RATE),
            "-movflags", "+faststart", "-shortest", "-threads", threads,
            str(out_mp4),
        ],
        check=True,
    )
    return out_mp4


def render_shorts_9x16_video(episode_dir: Path, manifest: dict, res: int = 720) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    scenes_dir = episode_dir / "scenes"
    slug = manifest["slug"]
    w, h = (1080, 1920) if res >= 1080 else (720, 1280)
    fg_h = int(w * 2 / 3)
    fg_y = int(h * 0.23)
    box_y = int(h * 0.61)

    selected_scenes = [sc for sc in manifest["scenes"] if sc.get("include_in_short")]
    if not selected_scenes:
        selected_scenes = manifest["scenes"][:3]

    slices: list[tuple[dict, float, float]] = []
    for sc in selected_scenes:
        cues = sc.get("cues", [])
        max_sec = float(sc.get("short_max_sec", 17.0))
        s0 = float(sc["voice_start"])
        s1 = min(float(sc["voice_end"]), s0 + max_sec)
        snapped_end = s1
        for c in cues:
            if float(c["end"]) <= s0 + max_sec + 1.5:
                snapped_end = float(c["end"]) + 0.25
        slices.append((sc, s0, max(s0 + 5.0, snapped_end)))

    slice_wavs: list[Path] = []
    short_cues: list[dict] = []
    short_scenes_meta: list[tuple[Path, float, bool]] = []
    cursor = 0.0

    for idx, (sc, s0, s1) in enumerate(slices):
        dur = s1 - s0
        sw = scenes_dir / f"{slug}_short_slice_{idx}.wav"
        subprocess.run(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                "-ss", f"{s0:.3f}", "-t", f"{dur:.3f}",
                "-i", manifest["master_wav"],
                "-af", f"afade=t=in:st=0:d=0.18,afade=t=out:st={max(0.1, dur-0.22):.3f}:d=0.22",
                "-c:a", "pcm_s16le", str(sw),
            ],
            check=True,
        )
        slice_wavs.append(sw)
        media_rel = sc.get("short_image") or sc["image"]
        short_scenes_meta.append((episode_dir / media_rel, dur, bool(sc.get("rain_overlay", False))))

        for c in sc.get("cues", []):
            cs = float(c["start"])
            ce = float(c["end"])
            if cs >= s0 - 0.1 and ce <= s1 + 0.1:
                short_cues.append({
                    "text": c["text"],
                    "speaker": c.get("speaker", "narrator"),
                    "character_name": c.get("character_name", ""),
                    "start": max(0.0, round(cursor + (cs - s0), 3)),
                    "end": round(cursor + (ce - s0), 3),
                })
        cursor += dur

    concat_txt = scenes_dir / f"{slug}_short_audio.txt"
    concat_txt.write_text("\n".join(f"file '{sw.resolve()}'" for sw in slice_wavs), encoding="utf-8")
    short_wav = scenes_dir / f"{slug}_short_master.wav"
    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-c:a", "pcm_s16le", str(short_wav),
        ],
        check=True,
    )

    hook_title = manifest.get("short_hook") or "रात 1:30 बजे की वो दस्तक..."
    cta_text = f"पूरी कहानी '{CHANNEL_NAME_HI}' चैनल पर देखें"
    short_ass = episode_dir / "subtitles_shorts.ass"
    write_shorts_ass(short_cues, hook_title, cta_text, cursor, short_ass)

    fps = 24
    vert_clips: list[Path] = []
    threads = str(min(8, os.cpu_count() or 4))
    rain_vert: Optional[Path] = None
    if any(r for _, _, r in short_scenes_meta):
        rain_vert = scenes_dir / f"rain_loop_{w}x{h}.mp4"
        render_rain_overlay_loop(rain_vert, w, h, fps=fps)

    for idx, (media_path, dur, use_rain) in enumerate(short_scenes_meta):
        vclip = scenes_dir / f"{slug}_short_vis_{idx}.mp4"
        is_video = media_path.suffix.lower() in _VIDEO_EXTS
        frames = max(24, int(round(dur * fps)))

        if is_video:
            inputs = ["-stream_loop", "-1", "-t", f"{dur:.3f}", "-i", str(media_path)]
            fg_part = f"[fg]fps={fps},scale={w}:{fg_h}:force_original_aspect_ratio=increase,crop={w}:{fg_h}[fgz]"
            bg_part = f"[bg]fps={fps},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},gblur=sigma=24,eq=brightness=-0.22:saturation=1.1[bgb]"
        else:
            inputs = ["-loop", "1", "-i", str(media_path)]
            bg_part = f"[bg]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},gblur=sigma=24,eq=brightness=-0.22:saturation=1.1[bgb]"
            fg_part = (
                f"[fg]scale={w}:-2,zoompan=z='min(1.06,1.0+0.06*(on/{frames}))':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{fg_h}:fps={fps}[fgz]"
            )

        fc = (
            f"[0:v]split=2[bg][fg];{bg_part};{fg_part};"
            f"[bgb][fgz]overlay=x=0:y={fg_y},drawbox=x=0:y={box_y}:w={w}:h={h-box_y}:color=black@0.48:t=fill,format=yuv420p[comp]"
        )
        if use_rain and rain_vert:
            inputs.extend(["-stream_loop", "-1", "-t", f"{dur:.3f}", "-i", str(rain_vert)])
            fc += ";[1:v]format=yuv420p[rn];[comp][rn]blend=c0_mode=screen:c0_opacity=0.60:c1_mode=normal:c2_mode=normal[vout]"
        else:
            fc = fc.replace("[comp]", "[vout]")

        subprocess.run(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                *inputs,
                "-filter_complex", fc,
                "-map", "[vout]",
                "-t", f"{dur:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                "-threads", threads, "-an", str(vclip),
            ],
            check=True,
        )
        vert_clips.append(vclip)

    vlist = scenes_dir / f"{slug}_short_vid.txt"
    vlist.write_text("\n".join(f"file '{c.resolve()}'" for c in vert_clips), encoding="utf-8")
    short_mp4 = episode_dir / f"{slug}_shorts_9x16.mp4"
    ass_escaped = str(short_ass).replace("\\", "/").replace(":", "\\:")
    fonts_escaped = str(FONTS_DIR).replace("\\", "/").replace(":", "\\:")

    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(vlist),
            "-i", str(short_wav),
            "-vf", f"ass='{ass_escaped}':fontsdir='{fonts_escaped}',format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
            "-c:a", "aac", "-b:a", "128k", "-ar", str(SAMPLE_RATE),
            "-movflags", "+faststart", "-shortest", "-threads", threads,
            str(short_mp4),
        ],
        check=True,
    )
    return short_mp4


def render_thumbnails(episode_dir: Path, manifest: dict) -> tuple[Path, Path]:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    hero_img = episode_dir / manifest["scenes"][2]["image"]
    if not hero_img.exists() or hero_img.suffix.lower() in _VIDEO_EXTS:
        hero_img = episode_dir / manifest["scenes"][0]["image"]

    badge = f"{CHANNEL_NAME_HI} • हिंदी कहानी"
    headline = "बारिश की वो आख़िरी रात..."
    subline = "जब 5 साल बाद अतीत ने दरवाज़ा खटखटाया!"

    fonts_escaped = str(FONTS_DIR).replace("\\", "/").replace(":", "\\:")

    thumb_ass_16 = episode_dir / "scenes" / "thumb_16.ass"
    thumb_ass_16.write_text(
        f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Badge,Noto Sans Devanagari,32,&H00FFFFFF,&H00FFFFFF,&H00121218,&HEE2438B8,-1,0,0,0,100,100,0,0,3,12,0,7,48,48,38,1
Style: Headline,Noto Sans Devanagari,74,&H0073E1FF,&H00FFFFFF,&H00080A12,&HCC000000,-1,0,0,0,100,100,0,0,1,5,3,1,48,48,96,1
Style: Subline,Noto Sans Devanagari,44,&H00FFFFFF,&H00FFFFFF,&H00080A12,&HCC000000,-1,0,0,0,100,100,0,0,1,4,2,1,48,48,36,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.00,Badge,,0,0,0,,{badge}
Dialogue: 0,0:00:00.00,0:00:02.00,Headline,,0,0,0,,{headline}
Dialogue: 0,0:00:00.00,0:00:02.00,Subline,,0,0,0,,{subline}
""",
        encoding="utf-8",
    )
    out_16 = episode_dir / "thumbnail_16x9.jpg"
    t16_esc = str(thumb_ass_16).replace("\\", "/").replace(":", "\\:")
    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(hero_img),
            "-vf",
            f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
            f"drawbox=x=0:y=470:w=1280:h=250:color=black@0.58:t=fill,"
            f"vignette=PI/4,ass='{t16_esc}':fontsdir='{fonts_escaped}'",
            "-frames:v", "1", "-q:v", "2", str(out_16),
        ],
        check=True,
    )

    thumb_ass_9 = episode_dir / "scenes" / "thumb_9.ass"
    thumb_ass_9.write_text(
        f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Badge,Noto Sans Devanagari,42,&H00FFFFFF,&H00FFFFFF,&H00121218,&HEE2438B8,-1,0,0,0,100,100,0,0,3,16,0,8,60,60,96,1
Style: Headline,Noto Sans Devanagari,80,&H0073E1FF,&H00FFFFFF,&H00080A12,&HCC000000,-1,0,0,0,100,100,0,0,1,6,3,2,60,60,340,1
Style: Subline,Noto Sans Devanagari,48,&H00FFFFFF,&H00FFFFFF,&H00080A12,&HCC000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.00,Badge,,0,0,0,,{badge}
Dialogue: 0,0:00:00.00,0:00:02.00,Headline,,0,0,0,,{headline}
Dialogue: 0,0:00:00.00,0:00:02.00,Subline,,0,0,0,,{subline}
""",
        encoding="utf-8",
    )
    out_9 = episode_dir / "thumbnail_9x16.jpg"
    t9_esc = str(thumb_ass_9).replace("\\", "/").replace(":", "\\:")
    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(hero_img),
            "-vf",
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"drawbox=x=0:y=1300:w=1080:h=620:color=black@0.58:t=fill,"
            f"vignette=PI/4,ass='{t9_esc}':fontsdir='{fonts_escaped}'",
            "-frames:v", "1", "-q:v", "2", str(out_9),
        ],
        check=True,
    )
    return out_16, out_9
