# Rishton Ke Mod (`रिश्तों के मोड़`) — Daily Hindi Story Playbook

## Channel Identity & Folder Convention
- **Channel Name:** **Rishton Ke Mod** (`रिश्तों के मोड़`)
- **Handle:** `@RishtonKeMod`
- **Episode Folders (date-wise):** `hindi/YYYY-MM-DD/`

## Visual Guidelines (Multi-Shot Photorealistic Live-Action Characters)
- Use **3 distinct camera shots per scene** (`shot_0Xa.jpg`, `shot_0Xb.jpg`, `shot_0Xc.jpg` — establishing wide, close-up reaction, reverse angle/insert detail, or `.mp4` live-action clips) so visuals change naturally every 25–35 seconds.
- Always use raw 35mm Indian web-series live-action prompts (ARRI Alexa / 50mm or 85mm prime, real skin texture, authentic Indian home lighting, zero anime/painting keywords), passing the lead anchor frame as reference so actors stay consistent across all 15 shots.
- Set `"rain_overlay": true` on outdoor monsoon shots for moving rain atmosphere.

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
```
Pass `--res 1080` for Full HD 1080p or `--voicestudio` to synthesize via local `debpalash/VoiceStudio` (`OmniVoice`).
