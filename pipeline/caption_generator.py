from __future__ import annotations

import argparse
import json
from pathlib import Path


def _ass_time(ms: int) -> str:
    cs = max(0, ms // 10)
    hours, rem = divmod(cs, 360000)
    minutes, rem = divmod(rem, 6000)
    seconds, centis = divmod(rem, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centis:02d}"


def _style(format_name: str) -> tuple[int, int, int, int]:
    if format_name == "reels":
        return 1080, 1920, 72, 200
    return 1920, 1080, 48, 80


def generate_captions(script_path: str = "script.json", timing_dir: str = ".", output_path: str = "final_captions.ass") -> str:
    import os
    job_id = os.environ.get("JOB_ID")
    if job_id:
        try:
            from pipeline.status import update_status
            update_status(job_id, "processing", progress=55, log_message="Generating captions and subtitles...")
        except Exception:
            pass

    script = json.loads(Path(script_path).read_text(encoding="utf-8"))
    play_x, play_y, font_size, margin_v = _style(script.get("format", "reels"))
    events: list[str] = []
    offset_ms = 0
    for scene in script["scenes"]:
        scene_num = int(scene["scene_number"])
        timing_file = Path(timing_dir) / f"timing_scene_{scene_num:02d}.json"
        words = json.loads(timing_file.read_text(encoding="utf-8")) if timing_file.exists() else []
        for idx in range(0, len(words), 3):
            group = words[idx:idx + 3]
            if not group:
                continue
            start = offset_ms + int(group[0].get("start_ms", 0))
            end = offset_ms + int(group[-1].get("end_ms", group[0].get("start_ms", 0) + 600))
            text = " ".join(str(w.get("word", "")).upper() for w in group).replace("{", "").replace("}", "")
            events.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,,0,0,0,,{text}")
        offset_ms += int(float(scene.get("duration_seconds", 5)) * 1000)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_x}
PlayResY: {play_y}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,DejaVu Sans Bold,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,2,2,10,10,{margin_v},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    Path(output_path).write_text(header + "\n".join(events) + "\n", encoding="utf-8")

    if job_id:
        try:
            from pipeline.status import update_status
            update_status(job_id, "processing", progress=65, log_message="Captions and subtitles generated successfully.")
        except Exception:
            pass

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", default="script.json")
    parser.add_argument("--timing-dir", default=".")
    parser.add_argument("--output", default="final_captions.ass")
    args = parser.parse_args()
    print(generate_captions(args.script, args.timing_dir, args.output))


if __name__ == "__main__":
    main()
