"""Procedural copyright-free ambient SFX and emotional musical beds for storytelling."""
from __future__ import annotations

import numpy as np
from scipy import signal

from .config import SAMPLE_RATE


def _pink_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    white = rng.standard_normal(n).astype(np.float64)
    b = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
    a = np.array([1.0, -2.494956002, 2.017265875, -0.522189400])
    pink = signal.lfilter(b, a, white)
    peak = np.max(np.abs(pink)) or 1.0
    return (pink / peak).astype(np.float32)


def generate_ambience(kind: str, duration_s: float, seed: int = 42) -> np.ndarray:
    n = max(1, int(round(duration_s * SAMPLE_RATE)))
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, duration_s, n, endpoint=False)

    left_raw = _pink_noise(n, rng)
    right_raw = _pink_noise(n, rng)

    if kind == "rain_heavy":
        sos_lp = signal.butter(3, 3800.0, btype="low", fs=SAMPLE_RATE, output="sos")
        sos_hp = signal.butter(2, 180.0, btype="high", fs=SAMPLE_RATE, output="sos")
        l = signal.sosfilt(sos_hp, signal.sosfilt(sos_lp, left_raw))
        r = signal.sosfilt(sos_hp, signal.sosfilt(sos_lp, right_raw))
        swell = 0.72 + 0.28 * np.sin(2 * np.pi * 0.08 * t + 0.4) * np.sin(2 * np.pi * 0.031 * t)
        thunder_env = np.zeros(n, dtype=np.float64)
        for center in np.arange(5.0, max(5.1, duration_s - 3.0), 18.0):
            idx = int(center * SAMPLE_RATE)
            span = int(3.8 * SAMPLE_RATE)
            if idx + span < n:
                win = np.hanning(span) * np.exp(-np.linspace(0, 2.8, span))
                thunder_env[idx : idx + span] += win * 0.45
        rumble = signal.sosfilt(
            signal.butter(3, 120.0, btype="low", fs=SAMPLE_RATE, output="sos"),
            _pink_noise(n, rng),
        )
        stereo = np.stack([l * swell + rumble * thunder_env, r * swell + rumble * thunder_env], axis=-1)
    elif kind == "rain_soft":
        sos = signal.butter(4, [150.0, 2000.0], btype="band", fs=SAMPLE_RATE, output="sos")
        l = signal.sosfilt(sos, left_raw)
        r = signal.sosfilt(sos, right_raw)
        swell = 0.8 + 0.2 * np.sin(2 * np.pi * 0.06 * t)
        stereo = np.stack([l * swell, r * swell], axis=-1)
    elif kind == "night_wind":
        sos = signal.butter(3, [90.0, 850.0], btype="band", fs=SAMPLE_RATE, output="sos")
        l = signal.sosfilt(sos, left_raw) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * t))
        r = signal.sosfilt(sos, right_raw) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * t + 1.1))
        stereo = np.stack([l, r], axis=-1)
    else:
        sos = signal.butter(3, [120.0, 1200.0], btype="band", fs=SAMPLE_RATE, output="sos")
        l = signal.sosfilt(sos, left_raw) * 0.45
        r = signal.sosfilt(sos, right_raw) * 0.45
        stereo = np.stack([l, r], axis=-1)

    peak = np.max(np.abs(stereo)) or 1.0
    return (stereo / peak * 0.35).astype(np.float32)


def _soft_piano_note(freq: float, dur_s: float, velocity: float = 0.7) -> np.ndarray:
    n = max(1, int(round(dur_s * SAMPLE_RATE)))
    t = np.linspace(0.0, dur_s, n, endpoint=False)
    attack = 1.0 - np.exp(-t / 0.025)
    decay = np.exp(-t / max(0.9, dur_s * 0.55))
    tone = (
        1.00 * np.sin(2 * np.pi * freq * t)
        + 0.32 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t / 0.9)
        + 0.08 * np.sin(2 * np.pi * freq * 3.0 * t) * np.exp(-t / 0.4)
    )
    return (tone * attack * decay * velocity).astype(np.float32)


def generate_music_bed(style: str, duration_s: float) -> np.ndarray:
    n = max(1, int(round(duration_s * SAMPLE_RATE)))
    stereo = np.zeros((n, 2), dtype=np.float64)

    progressions = {
        "melancholy_piano": [
            [220.00, 261.63, 329.63, 392.00],
            [174.61, 220.00, 261.63, 329.63],
            [146.83, 220.00, 261.63, 329.63],
            [164.81, 220.00, 246.94, 329.63],
        ],
        "warm_romance": [
            [261.63, 329.63, 392.00, 493.88],
            [220.00, 261.63, 329.63, 392.00],
            [174.61, 220.00, 261.63, 329.63],
            [196.00, 246.94, 293.66, 329.63],
        ],
        "tense_pulse": [
            [146.83, 220.00, 261.63, 311.13],
            [130.81, 196.00, 233.08, 293.66],
            [116.54, 174.61, 220.00, 261.63],
            [138.59, 196.00, 220.00, 277.18],
        ],
        "hopeful_dawn": [
            [146.83, 220.00, 277.18, 329.63],
            [196.00, 246.94, 293.66, 369.99],
            [246.94, 293.66, 369.99, 440.00],
            [220.00, 277.18, 329.63, 392.00],
        ],
    }

    chords = progressions.get(style, progressions["melancholy_piano"])
    bar_s = 4.0
    step_s = 1.0
    cur_t = 0.0
    bar_idx = 0

    while cur_t < duration_s:
        chord = chords[bar_idx % len(chords)]
        b_start = int(cur_t * SAMPLE_RATE)
        b_len = min(n - b_start, int((bar_s + 0.8) * SAMPLE_RATE))
        if b_len > 100:
            bt = np.linspace(0.0, b_len / SAMPLE_RATE, b_len, endpoint=False)
            pad_env = np.sin(np.pi * bt / (b_len / SAMPLE_RATE)) ** 1.2
            pad = (0.65 * np.sin(2 * np.pi * (chord[0] * 0.5) * bt) + 0.35 * np.sin(2 * np.pi * (chord[1] * 0.5) * bt)) * pad_env * 0.24
            stereo[b_start : b_start + b_len, 0] += pad
            stereo[b_start : b_start + b_len, 1] += pad

        for i, freq in enumerate(chord):
            note_t = cur_t + i * step_s
            if note_t >= duration_s:
                break
            n_start = int(note_t * SAMPLE_RATE)
            note = _soft_piano_note(freq, dur_s=3.4, velocity=0.34 if i == 0 else 0.25)
            copy_len = min(len(note), n - n_start)
            pan = 0.42 + 0.16 * ((i % 2) * 2 - 1)
            stereo[n_start : n_start + copy_len, 0] += note[:copy_len] * (1.0 - pan)
            stereo[n_start : n_start + copy_len, 1] += note[:copy_len] * pan

        if style == "tense_pulse":
            for beat in range(4):
                bt0 = cur_t + beat * 1.0
                if bt0 < duration_s:
                    bs = int(bt0 * SAMPLE_RATE)
                    pulse = _soft_piano_note(55.0, dur_s=0.45, velocity=0.22 if beat % 2 == 0 else 0.13)
                    clen = min(len(pulse), n - bs)
                    stereo[bs : bs + clen, 0] += pulse[:clen]
                    stereo[bs : bs + clen, 1] += pulse[:clen]

        cur_t += bar_s
        bar_idx += 1

    sos_lp = signal.butter(2, 2400.0, btype="low", fs=SAMPLE_RATE, output="sos")
    stereo[:, 0] = signal.sosfilt(sos_lp, stereo[:, 0])
    stereo[:, 1] = signal.sosfilt(sos_lp, stereo[:, 1])

    fade = min(n // 4, int(1.2 * SAMPLE_RATE))
    if fade > 0:
        stereo[:fade, :] *= np.linspace(0.0, 1.0, fade)[:, None]
        stereo[-fade:, :] *= np.linspace(1.0, 0.0, fade)[:, None]

    peak = np.max(np.abs(stereo)) or 1.0
    return (stereo / peak * 0.45).astype(np.float32)


def compute_ducking_envelope(voice_stereo: np.ndarray, min_gain: float = 0.24, max_gain: float = 1.0) -> np.ndarray:
    mono = np.mean(np.abs(voice_stereo), axis=1).astype(np.float64)
    step = 441
    n_frames = max(1, len(mono) // step)
    trimmed = mono[: n_frames * step].reshape(n_frames, step)
    rms = np.sqrt(np.mean(trimmed ** 2, axis=1) + 1e-12)
    speech_active = np.clip((rms - 0.008) / 0.035, 0.0, 1.0)

    env = np.zeros_like(speech_active)
    cur = 0.0
    a_att = 1.0 - np.exp(-0.010 / 0.08)
    a_rel = 1.0 - np.exp(-0.010 / 0.55)
    for i, target in enumerate(speech_active):
        alpha = a_att if target > cur else a_rel
        cur = cur + alpha * (target - cur)
        env[i] = cur

    gain_frames = max_gain - env * (max_gain - min_gain)
    x_old = np.linspace(0, len(mono) - 1, len(gain_frames))
    x_new = np.arange(len(mono))
    return np.interp(x_new, x_old, gain_frames).astype(np.float32)
