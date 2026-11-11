# Hindi Storytelling Studio (`contentcreation`)

Automated, YouTube-ready **multi-voice, scene-tuned Hindi story production studio** with situational vocal DSP, procedural rain/midnight music beds, synced Devanagari subtitles, 16:9 full videos, 9:16 YouTube Shorts teasers, high-CTR thumbnails, and optional local integration with [`debpalash/VoiceStudio`](https://github.com/debpalash/voicestudio).

---

## Repository Structure (Hindi-Only Channel Convention)

- **`hindi/YYYY-MM-DD/`** — Date-wise Hindi episode folders (e.g., `hindi/2026-11-11/`).
- **`studio/`** — Python + FFmpeg audio/video production engine (`director.py`, `soundscape.py`, `audio_engine.py`, `subtitle_engine.py`, `video_renderer.py`, `voicestudio_client.py`, `script_parser.py`, `daily_pipeline.py`).
- **`templates/`** — Reusable daily Hindi story blueprint + 7-day rotating non-repetitive YouTube-safe theme playbook.
- **`assets/fonts/`** — Bundled `NotoSansDevanagari.ttf` for clean Devanagari conjunct shaping via HarfBuzz/`libass`.

---

## Current Ready-to-Upload Episode

| Language | Folder | Full Video (16:9) | Shorts Teaser (9:16) | Duration | Loudness |
| --- | --- | --- | --- | --- | --- |
| **Hindi** | `hindi/2026-11-11/` | `baarish-ki-woh-aakhiri-raat_full_16x9.mp4` | `baarish-ki-woh-aakhiri-raat_shorts_9x16.mp4` | ~07:46 | -14.2 LUFS |

---

## Quick Start (Daily Usage)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Render a Hindi date-wise episode (add --res 1080 for 1080p)
python -m studio.daily_pipeline --episode-dir hindi/2026-11-11
```

### Local [`debpalash/VoiceStudio`](https://github.com/debpalash/voicestudio) Integration
Run VoiceStudio locally (`http://127.0.0.1:8000` or `VOICESTUDIO_URL`) and invoke:
```bash
python -m studio.daily_pipeline --episode-dir hindi/2026-11-12 --voicestudio
```
