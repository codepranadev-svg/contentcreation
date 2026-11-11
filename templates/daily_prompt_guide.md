# Daily Story Generation Playbook (Hindi & Marathi)

## Folder Convention
- **Hindi (date-wise):** `hindi/YYYY-MM-DD/`
- **Marathi (story-name-wise):** `marathi/<story-slug>/`

## 7-Day Rotating Story Themes (Adult Relationship & Affair Drama — 100% YouTube-Safe)
1. **Ex-Lover Monsoon Reunion** (unexpected late-night knock / airport delay)
2. **Office Late-Night Attraction** (outstation work trip & unspoken tension)
3. **Second Marriage & Past Shadow** (trust vs returning memories)
4. **Long-Distance Loneliness & Neighbor Crush** (emotional neglect vs boundaries)
5. **College Reunion Secret** (after years, seeing the one who never confessed)
6. **Overnight Train / Midnight Café Confession** (raw marriage truths)
7. **Arranged Marriage Awakening** (hidden feelings & honest confrontation)

## Daily CLI Usage
```bash
.venv/bin/python -m studio.daily_pipeline --episode-dir hindi/YYYY-MM-DD
.venv/bin/python -m studio.daily_pipeline --episode-dir marathi/<story-slug>
```
Pass `--res 1080` for Full HD 1080p or `--voicestudio` to synthesize via local `debpalash/VoiceStudio`.
