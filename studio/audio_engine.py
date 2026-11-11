"""Multi-voice dramatic audio mixer, speech-pause aligner, DSP processor, and YouTube LUFS master."""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np

from .config import (
    CHANNELS,
    SAMPLE_RATE,
    YOUTUBE_LOUDNORM_I,
    YOUTUBE_LOUDNORM_LRA,
    YOUTUBE_LOUDNORM_TP,
)
from .director import SceneAcousticProfile, get_profile
from .soundscape import compute_ducking_envelope, generate_ambience, generate_music_bed


def _db_to_linear(db: float) -> float:
    return float(10.0 ** (db / 20.0))


def load_wav_stereo_44k(path: Path) -> np.ndarray:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(path), "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS),
                "-c:a", "pcm_s16le", tmp_path,
            ],
            check=True,
        )
        with wave.open(tmp_path, "rb") as w:
            raw = w.readframes(w.getnframes())
            arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            return arr.reshape(-1, CHANNELS)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def save_wav_16bit(path: Path, stereo: np.ndarray) -> None:
    clipped = np.clip(stereo, -0.99, 0.99)
    pcm = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(CHANNELS)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())


def detect_speech_spans(stereo: np.ndarray, min_silence_s: float = 0.22, threshold: float = 0.012) -> list[tuple[float, float]]:
    mono = np.mean(np.abs(stereo), axis=1)
    hop = int(0.02 * SAMPLE_RATE)
    n_frames = max(1, len(mono) // hop)
    rms = np.sqrt(np.mean(mono[: n_frames * hop].reshape(n_frames, hop) ** 2, axis=1) + 1e-12)

    active = rms > threshold
    min_gap_frames = max(1, int(round(min_silence_s / 0.02)))
    bridged = active.copy()
    gap = 0
    in_speech = False
    last_on = 0
    for i, on in enumerate(active):
        if on:
            if in_speech and 0 < gap < min_gap_frames:
                bridged[last_on : i + 1] = True
            in_speech = True
            last_on = i
            gap = 0
        else:
            if in_speech:
                gap += 1

    spans: list[tuple[float, float]] = []
    start_idx = None
    for i, on in enumerate(bridged):
        if on and start_idx is None:
            start_idx = i
        elif not on and start_idx is not None:
            s_t = max(0.0, start_idx * 0.02 - 0.04)
            e_t = min(len(stereo) / SAMPLE_RATE, i * 0.02 + 0.05)
            if e_t - s_t > 0.15:
                spans.append((s_t, e_t))
            start_idx = None
    if start_idx is not None:
        s_t = max(0.0, start_idx * 0.02 - 0.04)
        e_t = len(stereo) / SAMPLE_RATE
        if e_t - s_t > 0.15:
            spans.append((s_t, e_t))
    return spans or [(0.0, len(stereo) / SAMPLE_RATE)]


def split_sentences(text: str) -> list[str]:
    raw_parts = re.split(r"(?<=[।?!])\s+|(?<=\.\.\.)\s+", text.strip())
    chunks: list[str] = []
    for part in raw_parts:
        p = part.strip()
        if not p:
            continue
        words = p.split()
        if len(words) <= 11:
            chunks.append(p)
        else:
            mid = len(words) // 2
            split_idx = None
            for offset in range(0, min(5, mid)):
                for cand in (mid - offset, mid + offset):
                    if 2 <= cand < len(words) - 1 and words[cand - 1].endswith((",", "—", "...")):
                        split_idx = cand
                        break
                if split_idx:
                    break
            if not split_idx:
                split_idx = mid
            chunks.append(" ".join(words[:split_idx]))
            chunks.append(" ".join(words[split_idx:]))
    return chunks


def apply_scene_dsp(wav_in: Path, wav_out: Path, profile: SceneAcousticProfile, pace_override: float | None = None) -> np.ndarray:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    pace = max(0.88, min(1.08, float(pace_override if pace_override is not None else profile.pace_multiplier)))

    filters = [
        f"highpass=f={profile.highpass_hz}",
        f"lowshelf=f=180:g={profile.low_shelf_db}",
        f"equalizer=f={profile.presence_hz}:t=q:w=1.2:g={profile.presence_db}",
        f"highshelf=f=6500:g={profile.air_db}",
        f"acompressor=threshold={profile.comp_threshold_db}dB:ratio={profile.comp_ratio}:attack=12:release=140:makeup=2",
        f"volume={profile.gain_db}dB",
    ]
    if abs(pace - 1.0) > 0.005:
        filters.append(f"atempo={pace:.4f}")
    if profile.reverb_wet > 0.02:
        d1 = int(profile.reverb_room_ms)
        d2 = int(profile.reverb_room_ms * 1.47)
        w1 = round(profile.reverb_wet * 0.55, 3)
        w2 = round(profile.reverb_wet * 0.35, 3)
        filters.append(f"aecho=0.92:0.88:{d1}|{d2}:{w1}|{w2}")
    filters.append("silenceremove=start_periods=1:start_threshold=-52dB:detection=peak")

    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(wav_in),
            "-af", ",".join(filters),
            "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS), "-c:a", "pcm_s16le",
            str(wav_out),
        ],
        check=True,
    )
    arr = load_wav_stereo_44k(wav_out)
    fade_n = min(len(arr) // 4, int(0.018 * SAMPLE_RATE))
    if fade_n > 0:
        arr[:fade_n] *= np.linspace(0.0, 1.0, fade_n)[:, None]
        arr[-fade_n:] *= np.linspace(1.0, 0.0, fade_n)[:, None]
    return arr


def align_phrases_to_audio(phrases: list[str], audio: np.ndarray, base_offset_s: float) -> list[dict]:
    dur_s = len(audio) / SAMPLE_RATE
    spans = detect_speech_spans(audio, min_silence_s=0.20, threshold=0.012)
    total_speech_s = sum(e - s for s, e in spans) or dur_s
    total_chars = sum(len(p) for p in phrases) or 1

    cum_speech = [0.0]
    for s, e in spans:
        cum_speech.append(cum_speech[-1] + (e - s))

    def speech_t_to_real_t(st: float) -> float:
        st = max(0.0, min(total_speech_s, st))
        for idx, (s, e) in enumerate(spans):
            if st <= cum_speech[idx + 1] or idx == len(spans) - 1:
                return min(e, s + (st - cum_speech[idx]))
        return dur_s

    cues: list[dict] = []
    cur_char = 0
    for phrase in phrases:
        frac_start = cur_char / total_chars
        cur_char += len(phrase)
        frac_end = cur_char / total_chars
        t0 = speech_t_to_real_t(frac_start * total_speech_s)
        t1 = speech_t_to_real_t(frac_end * total_speech_s)
        if t1 - t0 < 0.7:
            t1 = min(dur_s, t0 + 0.7)
        cues.append({
            "text": phrase,
            "start": round(base_offset_s + t0, 3),
            "end": round(base_offset_s + t1, 3),
        })
    for i in range(1, len(cues)):
        if cues[i]["start"] < cues[i - 1]["end"]:
            cues[i]["start"] = cues[i - 1]["end"]
        if cues[i]["end"] <= cues[i]["start"]:
            cues[i]["end"] = round(cues[i]["start"] + 0.6, 3)
    return cues


def two_pass_loudnorm_youtube(in_wav: Path, out_wav: Path, out_mp3: Path) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    measure_filter = (
        f"loudnorm=I={YOUTUBE_LOUDNORM_I}:TP={YOUTUBE_LOUDNORM_TP}:LRA={YOUTUBE_LOUDNORM_LRA}:print_format=json"
    )
    res = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(in_wav), "-af", measure_filter, "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", res.stderr, re.DOTALL)
    if m:
        stats = json.loads(m.group(0))
        norm_filter = (
            f"loudnorm=I={YOUTUBE_LOUDNORM_I}:TP={YOUTUBE_LOUDNORM_TP}:LRA={YOUTUBE_LOUDNORM_LRA}:"
            f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
            f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
            f"offset={stats['target_offset']}:linear=true"
        )
    else:
        norm_filter = f"loudnorm=I={YOUTUBE_LOUDNORM_I}:TP={YOUTUBE_LOUDNORM_TP}:LRA={YOUTUBE_LOUDNORM_LRA}"

    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(in_wav), "-af", norm_filter,
            "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS), "-c:a", "pcm_s16le", str(out_wav),
        ],
        check=True,
    )
    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(out_wav), "-c:a", "libmp3lame", "-b:a", "96k", str(out_mp3),
        ],
        check=True,
    )


def produce_episode_audio(episode_dir: Path, script_data: dict) -> dict:
    scenes_dir = episode_dir / "scenes"
    slug = script_data["slug"]
    lang = script_data["language"]

    intro_pad_s = 1.4
    outro_pad_s = 2.6
    timeline_segments: list[dict] = []
    all_cues: list[dict] = []
    cursor_s = intro_pad_s
    processed_parts: list[tuple[dict, np.ndarray, float, float]] = []

    for seg in script_data["segments"]:
        raw_wav = scenes_dir / f"{seg['id']}_raw.wav"
        if not raw_wav.exists():
            alt_mp3 = scenes_dir / f"{seg['id']}_raw.mp3"
            if alt_mp3.exists():
                raw_wav = alt_mp3
            else:
                raise FileNotFoundError(f"Missing raw voice segment: {raw_wav}")
        dsp_wav = scenes_dir / f"{seg['id']}_dsp.wav"

        profile = get_profile(seg.get("dsp_preset", "midnight_narration"), seg.get("director"))
        voiced = apply_scene_dsp(raw_wav, dsp_wav, profile, seg.get("pace_multiplier"))

        pause_before_s = float(seg.get("pause_before_ms", 400)) / 1000.0
        pause_after_s = float(seg.get("pause_after_ms", 900)) / 1000.0

        voice_start_s = cursor_s + pause_before_s
        voice_dur_s = len(voiced) / SAMPLE_RATE
        voice_end_s = voice_start_s + voice_dur_s
        scene_end_s = voice_end_s + pause_after_s

        phrases = split_sentences(seg["text"])
        seg_cues = align_phrases_to_audio(phrases, voiced, voice_start_s)
        for c in seg_cues:
            c["speaker"] = seg["speaker"]
            c["scene_number"] = seg["scene_number"]
            c["character_name"] = script_data["characters"][seg["speaker"]]["name"]
        all_cues.extend(seg_cues)

        timeline_segments.append({
            "id": seg["id"],
            "scene_number": seg["scene_number"],
            "scene_title": seg["scene_title"],
            "speaker": seg["speaker"],
            "character_name": script_data["characters"][seg["speaker"]]["name"],
            "image": seg["image"],
            "short_image": seg.get("short_image", seg["image"]),
            "shots": seg.get("shots", []),
            "camera_motion": seg.get("camera_motion", "slow_zoom_in"),
            "rain_overlay": bool(seg.get("rain_overlay", False)),
            "scene_start": round(cursor_s, 3),
            "voice_start": round(voice_start_s, 3),
            "voice_end": round(voice_end_s, 3),
            "scene_end": round(scene_end_s, 3),
            "duration": round(scene_end_s - cursor_s, 3),
            "include_in_short": bool(seg.get("include_in_short", False)),
            "short_max_sec": float(seg.get("short_max_sec", 18.0)),
            "soundscape": seg.get("soundscape", {}),
            "cues": seg_cues,
        })
        processed_parts.append((seg, voiced, voice_start_s, scene_end_s))
        cursor_s = scene_end_s

    total_dur_s = cursor_s + outro_pad_s
    total_samples = int(round(total_dur_s * SAMPLE_RATE))

    voice_bus = np.zeros((total_samples, CHANNELS), dtype=np.float32)
    bed_bus = np.zeros((total_samples, CHANNELS), dtype=np.float32)

    for seg, voiced, v_start_s, _ in processed_parts:
        s_idx = int(round(v_start_s * SAMPLE_RATE))
        e_idx = min(total_samples, s_idx + len(voiced))
        voice_bus[s_idx:e_idx] += voiced[: e_idx - s_idx]

    for idx, (seg, _, v_start_s, s_end_s) in enumerate(processed_parts):
        sc_start_s = 0.0 if idx == 0 else timeline_segments[idx]["scene_start"]
        sc_end_s = total_dur_s if idx == len(processed_parts) - 1 else s_end_s
        ov_start = max(0.0, sc_start_s - (0.0 if idx == 0 else 0.8))
        ov_end = min(total_dur_s, sc_end_s + (0.0 if idx == len(processed_parts) - 1 else 0.8))
        sc_dur = ov_end - ov_start

        ss_cfg = seg.get("soundscape", {})
        amb = generate_ambience(ss_cfg.get("ambience", "rain_soft"), sc_dur, seed=100 + idx)
        mus = generate_music_bed(ss_cfg.get("music", "melancholy_piano"), sc_dur)

        amb_gain = _db_to_linear(float(ss_cfg.get("ambience_db", -24)))
        mus_gain = _db_to_linear(float(ss_cfg.get("music_db", -20)))
        combined = amb * amb_gain + mus * mus_gain

        fade_n = min(len(combined) // 4, int(0.8 * SAMPLE_RATE))
        if fade_n > 0:
            combined[:fade_n] *= np.linspace(0.0, 1.0, fade_n)[:, None]
            combined[-fade_n:] *= np.linspace(1.0, 0.0, fade_n)[:, None]

        b_s = int(round(ov_start * SAMPLE_RATE))
        b_e = min(total_samples, b_s + len(combined))
        bed_bus[b_s:b_e] += combined[: b_e - b_s]

    duck = compute_ducking_envelope(voice_bus, min_gain=0.28, max_gain=1.0)
    mix = voice_bus * 0.92 + bed_bus * duck[:, None]

    f_in = int(1.0 * SAMPLE_RATE)
    f_out = int(2.2 * SAMPLE_RATE)
    mix[:f_in] *= np.linspace(0.0, 1.0, f_in)[:, None]
    mix[-f_out:] *= np.linspace(1.0, 0.0, f_out)[:, None]

    raw_mix_wav = scenes_dir / f"{slug}_raw_mix.wav"
    master_wav = scenes_dir / f"{slug}_master.wav"
    master_mp3 = episode_dir / f"{slug}_master.mp3"
    save_wav_16bit(raw_mix_wav, mix)
    two_pass_loudnorm_youtube(raw_mix_wav, master_wav, master_mp3)

    manifest = {
        "title": script_data["title"],
        "slug": slug,
        "language": lang,
        "total_duration_s": round(total_dur_s, 3),
        "master_wav": str(master_wav),
        "master_mp3": str(master_mp3),
        "scenes": timeline_segments,
        "cues": all_cues,
    }
    (episode_dir / "cue_timeline.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest
