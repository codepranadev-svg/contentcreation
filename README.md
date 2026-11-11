# Rishton Ke Mod (`रिश्तों के मोड़`) — Hindi Storytelling Studio

Automated, YouTube-ready **multi-voice, multi-shot Hindi live-action storytelling studio** for the **Rishton Ke Mod** (`रिश्तों के मोड़`) YouTube channel — featuring consistent photorealistic 35mm live-action Indian actors, multi-angle scene cinematography + moving atmospheric rain, situational vocal DSP, procedural rain/midnight music beds, synced Devanagari subtitles, 16:9 full videos, 9:16 YouTube Shorts teasers, high-CTR thumbnails, and optional integration with [`debpalash/VoiceStudio`](https://github.com/debpalash/voicestudio) (`OmniVoice` built-in), [`Open-Higgsfield-AI`](https://github.com/Autom8AI/Open-Higgsfield-AI) / `.mp4` motion clips, Pexels stock B-roll ([`MoneyPrinterTurbo`](https://github.com/harry0703/MoneyPrinterTurbo) pattern), and [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) hook research.

---

## Repository Structure

- **`hindi/YYYY-MM-DD/`** — Date-wise Hindi episode folders (e.g., `hindi/2026-11-11/`).
- **`studio/`** — Python + FFmpeg audio/video production engine (`config.py`, `director.py`, `soundscape.py`, `audio_engine.py`, `subtitle_engine.py`, `video_renderer.py`, `broll_tools.py`, `voicestudio_client.py`, `script_parser.py`, `daily_pipeline.py`).
- **`templates/`** — Reusable daily Hindi story blueprint + 7-day rotating non-repetitive YouTube-safe theme playbook + multi-shot live-action character guidelines.
- **`assets/fonts/`** — Bundled `NotoSansDevanagari.ttf` for clean Devanagari conjunct shaping via HarfBuzz/`libass`.

---

## Current Ready-to-Upload Episode

| Channel | Folder | Full Video (16:9) | Shorts Teaser (9:16) | Visuals | Loudness |
| --- | --- | --- | --- | --- | --- |
| **Rishton Ke Mod** | `hindi/2026-11-11/` | `baarish-ki-woh-aakhiri-raat_full_16x9.mp4` | `baarish-ki-woh-aakhiri-raat_shorts_9x16.mp4` | 15 Live-Action Shots + Moving Rain | -14.2 LUFS |

---

## Quick Start (Daily Usage)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Render a Hindi date-wise episode (add --res 1080 for 1080p)
python -m studio.daily_pipeline --episode-dir hindi/2026-11-11
```

### Multi-Shot & External `.mp4` Live-Action Video Clip Support
Each segment in `script.json` supports a `shots` array mixing photorealistic `.jpg` stills and real `.mp4` motion/lip-sync clips (e.g., via `studio/live_action_api.py` with Google Veo 3.1 or Fal.ai Kling 2.6 + Sync LipSync, `Open-Higgsfield-AI`, `OpenMontage`, or `Pexels` via `studio/broll_tools.py`).

Run the 1-click Google Colab notebook to generate & assemble 1080p moving-actor `.mp4` clips directly into Google Drive:
- **[Open `colab_live_action_generator.ipynb` in Google Colab](https://colab.research.google.com/github/codepranadev-svg/contentcreation/blob/main/studio/colab_live_action_generator.ipynb)**

### Local [`debpalash/VoiceStudio`](https://github.com/debpalash/voicestudio) (`OmniVoice`) Integration
Run VoiceStudio locally (`http://127.0.0.1:8000` or `VOICESTUDIO_URL`) and invoke:
```bash
python -m studio.daily_pipeline --episode-dir hindi/2026-11-12 --voicestudio
```
