"""ASS & SRT subtitle generator for Devanagari Hindi/Marathi storytelling."""
from __future__ import annotations

from pathlib import Path

SPEAKER_STYLES = {
    "narrator": ("Narrator", "&H00F2F0EB"),
    "female_lead": ("FemaleLead", "&H00D4D0FF"),
    "male_lead": ("MaleLead", "&H009AE2FF"),
}


def _ass_time(seconds: float) -> str:
    cs = max(0, int(round(float(seconds) * 100)))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def _srt_time(seconds: float) -> str:
    ms_tot = max(0, int(round(float(seconds) * 1000)))
    h, rem = divmod(ms_tot, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ass_escape(text: str) -> str:
    return (
        str(text)
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("\r\n", "\\N")
        .replace("\n", "\\N")
        .replace("\r", "\\N")
    )


def write_srt(cues: list[dict], out_path: Path) -> None:
    lines: list[str] = []
    for idx, cue in enumerate(cues, start=1):
        lines.append(str(idx))
        lines.append(f"{_srt_time(cue['start'])} --> {_srt_time(cue['end'])}")
        lines.append(cue["text"].strip())
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_full_ass(manifest: dict, out_path: Path) -> None:
    title = _ass_escape(manifest["title"])
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitleCard,Noto Sans Devanagari,64,&H00F7E6C4,&H00FFFFFF,&H0010121C,&H99000000,-1,0,0,0,100,100,0,0,1,3,2,5,140,140,80,1
Style: SceneTag,Noto Sans Devanagari,32,&H00C8D4E6,&H00FFFFFF,&H00080A12,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,7,64,64,44,1
Style: Narrator,Noto Sans Devanagari,52,&H00F5F2EB,&H0000E7FF,&H000B0D14,&H99000000,-1,0,0,0,100,100,0,0,1,3,1.5,2,130,130,66,1
Style: FemaleLead,Noto Sans Devanagari,52,&H00E0D2FF,&H0000E7FF,&H000B0D14,&H99000000,-1,0,0,0,100,100,0,0,1,3,1.5,2,130,130,66,1
Style: MaleLead,Noto Sans Devanagari,52,&H009BE0FF,&H0000E7FF,&H000B0D14,&H99000000,-1,0,0,0,100,100,0,0,1,3,1.5,2,130,130,66,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = [
        f"Dialogue: 1,{_ass_time(0.3)},{_ass_time(4.2)},TitleCard,,0,0,0,,{{\\fad(500,600)}}{title}"
    ]

    for sc in manifest["scenes"]:
        st = float(sc["scene_start"])
        ed = min(float(sc["scene_end"]), st + 4.8)
        label = _ass_escape(f"दृश्य {sc['scene_number']} • {sc['scene_title']}")
        if manifest["language"] == "mr":
            label = _ass_escape(f"प्रसंग {sc['scene_number']} • {sc['scene_title']}")
        events.append(
            f"Dialogue: 1,{_ass_time(st + 0.2)},{_ass_time(ed)},SceneTag,,0,0,0,,{{\\fad(350,450)}}{label}"
        )

    for cue in manifest["cues"]:
        style_name = SPEAKER_STYLES.get(cue.get("speaker", "narrator"), ("Narrator", ""))[0]
        char_name = cue.get("character_name", "")
        text = _ass_escape(cue["text"])
        if cue.get("speaker") in ("female_lead", "male_lead") and char_name:
            display = f"{{\\fad(140,120)\\b1\\fs36\\c&H006FD4FF&}}{_ass_escape(char_name)}:\\N{{\\r{style_name}}}{text}"
        else:
            display = f"{{\\fad(140,120)}}{text}"
        events.append(
            f"Dialogue: 0,{_ass_time(cue['start'])},{_ass_time(cue['end'])},{style_name},,0,0,0,,{display}"
        )

    out_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


def write_shorts_ass(
    cues: list[dict],
    title_hook: str,
    cta_text: str,
    total_dur_s: float,
    out_path: Path,
) -> None:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: HookHeader,Noto Sans Devanagari,56,&H009BE0FF,&H00FFFFFF,&H000B0D14,&HBB000000,-1,0,0,0,100,100,0,0,1,4,2,8,70,70,180,1
Style: Narrator,Noto Sans Devanagari,58,&H00FFFFFF,&H0000E7FF,&H00080A12,&H99000000,-1,0,0,0,100,100,0,0,1,4,2,2,80,80,380,1
Style: FemaleLead,Noto Sans Devanagari,58,&H00E4D6FF,&H0000E7FF,&H00080A12,&H99000000,-1,0,0,0,100,100,0,0,1,4,2,2,80,80,380,1
Style: MaleLead,Noto Sans Devanagari,58,&H00A3E4FF,&H0000E7FF,&H00080A12,&H99000000,-1,0,0,0,100,100,0,0,1,4,2,2,80,80,380,1
Style: CtaFooter,Noto Sans Devanagari,46,&H00FFFFFF,&H00FFFFFF,&H00121520,&HCC1A1E2E,-1,0,0,0,100,100,0,0,3,18,0,2,80,80,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = [
        f"Dialogue: 2,0:00:00.00,{_ass_time(total_dur_s)},HookHeader,,0,0,0,,{{\\fad(300,300)}}{_ass_escape(title_hook)}",
        f"Dialogue: 2,{_ass_time(max(0.0, total_dur_s - 6.0))},{_ass_time(total_dur_s)},CtaFooter,,0,0,0,,{{\\fad(300,300)}}{_ass_escape(cta_text)}",
    ]
    for cue in cues:
        style_name = SPEAKER_STYLES.get(cue.get("speaker", "narrator"), ("Narrator", ""))[0]
        char_name = cue.get("character_name", "")
        text = _ass_escape(cue["text"])
        if cue.get("speaker") in ("female_lead", "male_lead") and char_name:
            display = f"{{\\fad(100,100)\\fs42\\c&H006FD4FF&}}{_ass_escape(char_name)}\\N{{\\r{style_name}}}{text}"
        else:
            display = f"{{\\fad(100,100)}}{text}"
        events.append(
            f"Dialogue: 0,{_ass_time(cue['start'])},{_ass_time(cue['end'])},{style_name},,0,0,0,,{display}"
        )
    out_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
