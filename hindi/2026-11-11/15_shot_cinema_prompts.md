# 15-Shot Live-Action Cinema & Lip-Sync Production Guide
**Episode:** `2026-11-11` — *बारिश की वो आख़िरी रात (Baarish Ki Woh Aakhiri Raat)*  
**Channel:** **Rishton Ke Mod** (`रिश्तों के मोड़`) | **Total Runtime:** `466.15s` (`7m 46s`)

Use this guide with any external AI Video / Image-to-Video / Lip-Sync generator (e.g., **Google Veo 3**, **Kling 2.6 Lip-Sync**, **Runway Gen-4**, **Sora 2**, **Seedance**, **Open-Higgsfield-AI**, or **Wan 2.2** on GPU).  
Anchor every shot to its matching photorealistic 35mm keyframe (`scenes/shot_*.jpg`), then save generated continuous-motion clips as `.mp4` and update `shots[*].image` in `script.json` (or run `colab_live_action_generator.ipynb` on Google Colab) and render with:

```bash
python -m studio.daily_pipeline --episode-dir hindi/2026-11-11 --skip-audio --res 1080
```

---

## Scene 1 — `hi_01`: रात के डेढ़ बजे की दस्तक (`00:01.4` – `01:23.7` | `82.25s`)
**Audio Stem:** `scenes/hi_01_raw.mp3` (Narrator — Voice-00)

- **Shot 1A (`00:01.4`–`00:31.0`, `29.6s`) — Anchor:** `scenes/shot_01a.jpg`  
  *Camera & Action:* Slow push-in medium-wide shot inside a dimly lit Mumbai high-rise living room at 1:30 AM. Rain lashes the tall glass window behind Meera (late-20s Indian woman, simple cotton kurti). She slowly exhales, lifts a cooling ceramic cup of chai with both hands, blinks naturally while staring at rain streaks on the glass, and turns slightly toward the silent apartment.
- **Shot 1B (`00:31.0`–`00:55.7`, `24.7s`) — Anchor:** `scenes/shot_01b.jpg`  
  *Camera & Action:* Smooth lateral pan across the warm wooden foyer. Wall clock ticks past 1:30 AM; thunder flashes faintly from the hallway window; sudden sharp triple knock echoes at the main door. Meera steps into frame from the left, freezes mid-step, shifts her weight hesitantly, and reaches trembling fingers toward the brass latch.
- **Shot 1C (`00:55.7`–`01:23.7`, `28.0s`) — Anchor:** `scenes/shot_01c.jpg`  
  *Camera & Action:* Over-the-shoulder reveal as Meera pulls the wooden door open. Standing in the dim corridor is Aarav (late-20s Indian man, drenched navy shirt, wet hair dripping onto his collar), chest rising with heavy breathing, holding an antique silver bangle in his open palm. Eye contact locks between them; subtle micro-expressions of shock and unspoken longing.

---

## Scene 2 — `hi_02`: सन्नाटे और अदरक की चाय का सच (`01:23.7` – `03:03.9` | `100.28s`)
**Audio Stem:** `scenes/hi_02_raw.mp3` (Meera Lip-Sync — Voice-02)

- **Shot 2A (`01:23.7`–`01:57.8`, `34.1s`) — Anchor:** `scenes/shot_02a.jpg`  
  *Camera & Action:* Wide candlelit living-room two-shot during a power outage. Meera walks over carrying a towel and two steaming glasses of ginger chai, sets the tray down on the low wooden table, sits across from Aarav on the sofa, and begins speaking softly with natural lip-sync as she gestures toward the candles. Aarav listens attentively, nodding subtly while drying his wet hair.
- **Shot 2B (`01:57.8`–`02:33.9`, `36.1s`) — Anchor:** `scenes/shot_02b.jpg`  
  *Camera & Action:* Intimate 85mm close-up on Meera bathed in warm candlelight. Realistic blinking, breathing, subtle brow tension, and natural Hindi lip-sync as she confesses the quiet loneliness inside her four-year marriage—looking down at her chai glass, tightening her fingers, then glancing back up toward Aarav.
- **Shot 2C (`02:33.9`–`03:03.9`, `30.1s`) — Anchor:** `scenes/shot_02c.jpg`  
  *Camera & Action:* Reverse close-up reaction on Aarav listening silently in candlelight. Natural breathing, subtle swallow, empathetic eye movement, slight leaning forward as Meera cautions him to keep his voice down and remember boundaries.

---

## Scene 3 — `hi_03`: बालकनी की बारिश और अनकही चाहत (`03:03.9` – `04:34.7` | `90.80s`)
**Audio Stem:** `scenes/hi_03_raw.mp3` (Aarav Lip-Sync — Voice-01)

- **Shot 3A (`03:03.9`–`03:34.8`, `30.9s`) — Anchor:** `scenes/shot_03a.jpg`  
  *Camera & Action:* Wide moody shot on the covered Mumbai high-rise balcony overlooking blurred city lights in heavy monsoon rain. Aarav steps closer to the wet railing beside Meera, turning toward her with intense emotion; wind ruffles hair and wet fabric naturally. Both actors shift weight naturally while speaking and reacting.
- **Shot 3B (`03:34.8`–`04:07.5`, `32.7s`) — Anchor:** `scenes/shot_03b.jpg`  
  *Camera & Action:* Dramatic medium close-up on Aarav with real rain mist and cool blue-amber reflections on skin texture. Full natural Hindi lip-sync as he passionately speaks about the past five years, gesturing with one hand toward the rain-soaked city lights while keeping vulnerable eye contact.
- **Shot 3C (`04:07.5`–`04:34.7`, `27.2s`) — Anchor:** `scenes/shot_03c.jpg`  
  *Camera & Action:* Tight 85mm close-up on Meera standing near the balcony railing as rain droplets cling to her hair. Conflicted breathing, quivering lip, eyes glistening as she looks down momentarily before meeting his gaze.

---

## Scene 4 — `hi_04`: बिस्तर के पास रखा वो छोटा सा नोट (`04:34.7` – `05:32.5` | `97.80s`)
**Audio Stem:** `scenes/hi_04_raw.mp3` (Meera Lip-Sync — Voice-02)

- **Shot 4A (`04:34.7`–`05:06.0`, `31.3s`) — Anchor:** `scenes/shot_04a.jpg`  
  *Camera & Action:* Shallow-depth bedroom insert/medium shot lit by a warm bedside lamp. Meera walks to the nightstand to fetch water, notices a folded yellow sticky note tucked beneath a medicine strip beside her husband's watch, pauses, picks up the paper gently, and feels the weight of her husband's quiet care.
- **Shot 4B (`05:06.0`–`05:41.2`, `35.2s`) — Anchor:** `scenes/shot_04b.jpg`  
  *Camera & Action:* Medium shot of Meera seated on the edge of the bed holding the folded yellow paper while Aarav stands softly out of focus in the bedroom doorway behind her. Meera speaks softly and firmly with accurate lip-sync, gesturing calmly without raising her voice while Aarav listens silently from the threshold.
- **Shot 4C (`05:41.2`–`06:12.5`, `31.3s`) — Anchor:** `scenes/shot_04c.jpg`  
  *Camera & Action:* Close-up on Meera wiping a single tear with the back of her hand, inhaling deeply with calm moral clarity and resolve as she finishes speaking.

---

## Scene 5 — `hi_05`: सुबह की पहली किरण और ईमानदार फ़ैसला (`06:12.5` – `07:43.6` | `91.01s`)
**Audio Stem:** `scenes/hi_05_raw.mp3` (Narrator — Voice-00)

- **Shot 5A (`06:12.5`–`06:42.6`, `30.0s`) — Anchor:** `scenes/shot_05a.jpg`  
  *Camera & Action:* Soft 5:00 AM blue-gold dawn light filtering through the living-room glass. Aarav gives a quiet, respectful nod toward Meera off-frame, gently sets the silver bangle down on the wooden coffee table, offers a bittersweet half-smile, and walks calmly toward the front door.
- **Shot 5B (`06:42.6`–`07:16.2`, `33.7s`) — Anchor:** `scenes/shot_05b.jpg`  
  *Camera & Action:* Warm early-morning sunlight streaming through the open balcony door. Meera stands calmly by the wet railing holding her phone with both hands, typing an honest message to her husband Vikram with steady breathing and peaceful composure.
- **Shot 5C (`07:16.2`–`07:43.6`, `27.3s`) — Anchor:** `scenes/shot_05c.jpg`  
  *Camera & Action:* Golden sunrise rays over the rain-washed Mumbai skyline; a fresh steaming glass of chai rests on the wooden balcony railing as soft dawn breeze moves past, closing the chapter with hope and dignity.
