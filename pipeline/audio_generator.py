from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import edge_tts

VOICES = {
    "male": "en-US-AndrewMultilingualNeural",
    "female": "en-US-AvaMultilingualNeural",
}


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text)


def _offset_to_ms(offset: int) -> int:
    return int(offset / 10_000)


def _probe_duration(path: Path) -> float:
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0


async def _synthesize_with_timing(text: str, voice: str, output_path: str, timing_path: str) -> None:
    communicate = edge_tts.Communicate(text, voice, rate="+5%")
    boundaries: list[dict[str, int | str]] = []
    audio_bytes = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            start_ms = _offset_to_ms(int(chunk["offset"]))
            duration_ms = _offset_to_ms(int(chunk.get("duration", 0)))
            boundaries.append({"word": str(chunk["text"]), "start_ms": start_ms, "end_ms": max(start_ms + duration_ms, start_ms + 180)})
    Path(output_path).write_bytes(audio_bytes)
    if not boundaries:
        words = _words(text)
        boundaries = [{"word": w, "start_ms": i * 285, "end_ms": (i + 1) * 285} for i, w in enumerate(words)]
    Path(timing_path).write_text(json.dumps(boundaries, indent=2), encoding="utf-8")


def _fit_scene_duration(script: dict[str, Any], scene: dict[str, Any], audio_duration: float) -> None:
    current = float(scene.get("duration_seconds", 5))
    required = round(audio_duration + 0.35, 2)
    if required <= current:
        return
    if script.get("format") == "reels":
        max_by_role = {"hook": 4.5, "build": 10.5, "twist": 10.5, "payoff": 7.0}.get(scene.get("role"), 10.0)
        new_duration = min(required, max_by_role)
        projected = sum(float(s.get("duration_seconds", 5)) for s in script["scenes"]) - current + new_duration
        if projected <= 45:
            scene["duration_seconds"] = new_duration
        else:
            scene["audio_warning"] = f"TTS duration {audio_duration:.2f}s may exceed scene; total cap prevents expansion"
    else:
        scene["duration_seconds"] = max(current, required)


def generate_audio(script_path: str = "script.json", voice_key: str = "female", output_dir: str = ".", timed_script_path: str | None = None) -> list[str]:
    script_file = Path(script_path)
    script = json.loads(script_file.read_text(encoding="utf-8"))
    voice = VOICES.get(voice_key, VOICES["female"])
    outputs: list[str] = []
    job_id = os.environ.get("JOB_ID")

    if job_id:
        try:
            from pipeline.status import update_status
            update_status(job_id, "processing", progress=35, log_message="Generating voiceovers and fitting audio timing...")
        except Exception:
            pass

    async def _inner() -> None:
        scenes = script["scenes"]
        for idx, scene in enumerate(scenes):
            scene_num = int(scene["scene_number"])
            output = Path(output_dir) / f"voice_scene_{scene_num:02d}.mp3"
            timing = Path(output_dir) / f"timing_scene_{scene_num:02d}.json"
            
            if job_id:
                try:
                    from pipeline.status import update_status
                    progress_pct = 35 + int((idx / len(scenes)) * 20)
                    update_status(job_id, "processing", progress=progress_pct, log_message=f"Synthesizing voiceover for scene {scene_num} / {len(scenes)}...")
                except Exception:
                    pass

            await _synthesize_with_timing(scene.get("voiceover", ""), voice, str(output), str(timing))
            audio_duration = _probe_duration(output)
            scene["audio_duration_seconds"] = round(audio_duration, 3)
            _fit_scene_duration(script, scene, audio_duration)
            outputs.append(str(output))

    asyncio.run(_inner())
    destination = Path(timed_script_path or script_path)
    destination.write_text(json.dumps(script, indent=2), encoding="utf-8")

    if job_id:
        try:
            from pipeline.status import update_status
            update_status(job_id, "processing", progress=55, log_message="Voiceovers and audio timing complete.")
        except Exception:
            pass

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", default="script.json")
    parser.add_argument("--voice", choices=["male", "female"], default="female")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--timed-script")
    args = parser.parse_args()
    print(json.dumps(generate_audio(args.script, args.voice, args.output_dir, args.timed_script), indent=2))


if __name__ == "__main__":
    main()
