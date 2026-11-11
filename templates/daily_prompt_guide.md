# Daily Hindi Story Generation Playbook

## Folder Convention
- **Hindi (date-wise):** `hindi/YYYY-MM-DD/`

## 7-Day Rotating Story Themes (Adult Relationship & Affair Drama — 100% YouTube-Safe)
1. **Ex-Lover Monsoon Reunion** (unexpected late-night knock / airport delay)
2. **Office Late-Night Attraction** (outstation work trip & unspoken tension)
3. **Second Marriage & Past Shadow** (trust vs returning memories)
4. **Long-Distance Loneliness & Neighbor Crush** (emotional neglect vs boundaries)
5. **College Reunion Secret** (after years, seeing the one who never confessed)
6. **Overnight Train / Midnight Café Confession** (raw marriage truths)
7. **Arranged Marriage Awakening** (hidden feelings & honest confrontation)

## Visual Style Tip (Real Live-Action Look)
Prefer **photorealistic 35mm live-action film stills** (or real royalty-free `.mp4` / `.jpg` stock clips) over anime/digital-painting art so stories feel like an authentic Hindi OTT web series.

## Daily CLI Usage
```bash
.venv/bin/python -m studio.daily_pipeline --episode-dir hindi/YYYY-MM-DD
```
Pass `--res 1080` for Full HD 1080p or `--voicestudio` to synthesize via local `debpalash/VoiceStudio`.
