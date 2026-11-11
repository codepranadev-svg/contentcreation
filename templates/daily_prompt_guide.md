# Rishton Ke Mod (`रिश्तों के मोड़`) — Daily Hindi Story Playbook

## Channel Identity & Folder Convention
- **Channel Name:** **Rishton Ke Mod** (`रिश्तों के मोड़`)
- **Handle:** `@RishtonKeMod`
- **Episode Folders (date-wise):** `hindi/YYYY-MM-DD/`

## Visual Guidelines (Photorealistic Live-Action Characters)
- Always generate **raw 35mm live-action Indian cinema stills** (ARRI Alexa / 50mm lens, real skin pores, authentic Indian home/office lighting, natural film grain — avoid anime/cartoon/digital-painting prompts).
- Reuse Scene 2 (`scene_02.jpg`, showing both leads clearly) as a **reference image** when generating the remaining scenes so the same realistic actors keep consistent faces and outfits throughout the episode.

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
Pass `--res 1080` for Full HD 1080p or `--voicestudio` to synthesize via local `debpalash/VoiceStudio`.
