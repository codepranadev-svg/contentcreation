"""FFmpeg video & Devanagari thumbnail renderer for 16:9 YouTube and 9:16 Shorts."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import imageio_ffmpeg

from .config import FONTS_DIR, SAMPLE_RATE
from .subtitle_engine import write_full_ass, write_shorts_ass, write_srt


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


def render_scene_clip(
    image_path: Path,
    duration_s: float,
    motion: str,
    out_mp4: Path,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    frames = max(24, int(round(duration_s * fps)))
    z, x, y = _motion_expr(motion, frames)
    threads = str(min(8, os.cpu_count() or 4))
    up_w = int(width * 1.35)
    up_h = int(height * 1.35)
    vf = (
        f"scale={up_w}:{up_h}:force_original_aspect_ratio=increase,"
        f"crop={up_w}:{up_h},"
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={width}x{height}:fps={fps},"
        f"vignette=PI/5,format=yuv420p"
    )
    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-i", str(image_path),
            "-vf", vf,
            "-t", f"{duration_s:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-threads", threads, "-an", str(out_mp4),
        ],
        check=True,
    )


def render_full_16x9_video(episode_dir: Path, manifest: dict, res: int = 720) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    scenes_dir = episode_dir / "scenes"
    slug = manifest["slug"]
    fps = 24
    fade_s = 0.75
    width, height = (1920, 1080) if res >= 1080 else (1280, 720)

    srt_path = episode_dir / "subtitles.srt"
    ass_path = episode_dir / "subtitles.ass"
    write_srt(manifest["cues"], srt_path)
    write_full_ass(manifest, ass_path)

    total_dur_s = float(manifest["total_duration_s"])
    scene_clips: list[tuple[Path, float]] = []
    n_scenes = len(manifest["scenes"])
    for idx, sc in enumerate(manifest["scenes"]):
        start_s = 0.0 if idx == 0 else float(sc["scene_start"])
        end_s = total_dur_s if idx == n_scenes - 1 else float(sc["scene_end"])
        dur = (end_s - start_s) + (fade_s if idx < n_scenes - 1 else 0.0)
        clip_path = scenes_dir / f"{sc['id']}_vis.mp4"
        img_path = episode_dir / sc["image"]
        render_scene_clip(
            img_path, dur, sc.get("camera_motion", "slow_zoom_in"),
            clip_path, width=width, height=height, fps=fps,
        )
        scene_clips.append((clip_path, dur))

    inputs = []
    for clip_path, _ in scene_clips:
        inputs.extend(["-i", str(clip_path)])
    audio_idx = len(scene_clips)
    inputs.extend(["-i", manifest["master_wav"]])

    filter_parts: list[str] = []
    prev_label = "[0:v]"
    offset = scene_clips[0][1] - fade_s
    for idx in range(1, len(scene_clips)):
        out_label = f"[xf{idx}]"
        filter_parts.append(
            f"{prev_label}[{idx}:v]xfade=transition=fade:duration={fade_s:.2f}:offset={offset:.3f}{out_label}"
        )
        prev_label = out_label
        offset += scene_clips[idx][1] - fade_s

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
    lang = manifest["language"]
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
    short_scenes_meta: list[tuple[Path, float]] = []
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
        short_scenes_meta.append((episode_dir / sc["image"], dur))

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

    hook_title = "रात 1:30 बजे की वो दस्तक..." if lang == "hi" else "पावसाळी रात्रीची अधुरी भेट..."
    cta_text = "पूरी कहानी चैनल पर देखें — लिंक बायो में" if lang == "hi" else "संपूर्ण कथा चॅनेलवर पहा"
    short_ass = episode_dir / "subtitles_shorts.ass"
    write_shorts_ass(short_cues, hook_title, cta_text, cursor, short_ass)

    fps = 24
    vert_clips: list[Path] = []
    threads = str(min(8, os.cpu_count() or 4))
    for idx, (img_path, dur) in enumerate(short_scenes_meta):
        vclip = scenes_dir / f"{slug}_short_vis_{idx}.mp4"
        frames = max(24, int(round(dur * fps)))
        vf = (
            f"split=2[bg][fg];"
            f"[bg]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
            f"gblur=sigma=24,eq=brightness=-0.22:saturation=1.1[bgb];"
            f"[fg]scale={w}:-2,zoompan=z='min(1.06,1.0+0.06*(on/{frames}))':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{fg_h}:fps={fps}[fgz];"
            f"[bgb][fgz]overlay=x=0:y={fg_y},drawbox=x=0:y={box_y}:w={w}:h={h-box_y}:color=black@0.48:t=fill,format=yuv420p"
        )
        subprocess.run(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                "-loop", "1", "-i", str(img_path),
                "-vf", vf, "-t", f"{dur:.3f}",
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
    lang = manifest["language"]
    hero_img = episode_dir / manifest["scenes"][2]["image"]
    if not hero_img.exists():
        hero_img = episode_dir / manifest["scenes"][0]["image"]

    if lang == "hi":
        badge = "दिल को छू लेने वाली कहानी"
        headline = "बारिश की वो आख़िरी रात..."
        subline = "जब 5 साल बाद अतीत ने दरवाज़ा खटखटाया!"
    else:
        badge = "मराठी भावनिक कथा"
        headline = "अधुरी भेट — पावसाळी रात्र"
        subline = "जेव्हा नात्याच्या सीमेवर मन डगमगलं..."

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
Style: Badge,Noto Sans Devanagari,42,&H00FFFFFF,&H00FFFFFF,&H00121218,&HEE2438B8,-1,0,0,0,100,100,0,0,3,16,0,8,60,60,240,1
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
