from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def _dims(format_name: str) -> tuple[int, int, int]:
    return (1080, 1920, 24) if format_name == "reels" else (1920, 1080, 24)


def _run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        LOGGER.error("ffmpeg failed: %s", exc.stderr)
        raise


def _concat_inputs(scene_files: list[Path], durations: list[float], output: Path) -> None:
    if len(scene_files) == 1:
        _run(["ffmpeg", "-y", "-i", str(scene_files[0]), "-c", "copy", str(output)])
        return
    inputs: list[str] = []
    for file in scene_files:
        inputs.extend(["-i", str(file)])
    fade = 0.25
    chains: list[str] = []
    cumulative = 0.0
    last = "[0:v][0:a]"
    video_label = "0:v"
    audio_label = "0:a"
    for i in range(1, len(scene_files)):
        cumulative += durations[i - 1] - fade
        vout = f"v{i}"
        aout = f"a{i}"
        chains.append(f"[{video_label}][{i}:v]xfade=transition=fade:duration={fade}:offset={cumulative:.3f}[{vout}]")
        chains.append(f"[{audio_label}][{i}:a]acrossfade=d={fade}:c1=tri:c2=tri[{aout}]")
        video_label, audio_label = vout, aout
    filter_complex = ";".join(chains)
    _run(["ffmpeg", "-y", *inputs, "-filter_complex", filter_complex, "-map", f"[{video_label}]", "-map", f"[{audio_label}]", "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.1", "-pix_fmt", "yuv420p", "-preset", "slow", "-crf", "18", "-c:a", "aac", "-b:a", "192k", str(output)])


def assemble_video(script_path: str = "script.json", work_dir: str = ".", music_path: str = "music/ambient.mp3", captions_path: str = "final_captions.ass", output_path: str = "final_video.mp4") -> str:
    import os
    job_id = os.environ.get("JOB_ID")
    if job_id:
        try:
            from pipeline.status import update_status
            update_status(job_id, "processing", progress=65, log_message="Assembling video segments and mixing audio...")
        except Exception:
            pass

    script = json.loads(Path(script_path).read_text(encoding="utf-8"))
    work = Path(work_dir)
    w, h, fps = _dims(script.get("format", "reels"))
    durations = [float(scene.get("duration_seconds", 5)) for scene in script["scenes"]]
    voiced: list[Path] = []
    for scene, duration in zip(script["scenes"], durations):
        n = int(scene["scene_number"])
        raw = work / f"raw_scene_{n:02d}.mp4"
        norm = work / f"norm_scene_{n:02d}.mp4"
        voice = work / f"voice_scene_{n:02d}.mp3"
        merged = work / f"scene_with_voice_{n:02d}.mp4"
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},setpts=PTS-STARTPTS"
        _run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(raw), "-vf", vf, "-vcodec", "libx264", "-profile:v", "high", "-level:v", "4.1", "-pix_fmt", "yuv420p", "-preset", "slow", "-crf", "18", "-t", str(duration), "-an", str(norm)])
        _run(["ffmpeg", "-y", "-i", str(norm), "-i", str(voice), "-vcodec", "copy", "-acodec", "aac", "-b:a", "192k", "-af", "apad", "-shortest", "-t", str(duration), str(merged)])
        voiced.append(merged)
    assembled_raw = work / "assembled_raw.mp4"
    _concat_inputs(voiced, durations, assembled_raw)
    captions = Path(captions_path)
    assembled_captions = work / "assembled_with_captions.mp4"
    _run(["ffmpeg", "-y", "-i", str(assembled_raw), "-vf", f"ass={captions}", "-vcodec", "libx264", "-profile:v", "high", "-level:v", "4.1", "-pix_fmt", "yuv420p", "-preset", "slow", "-crf", "18", "-acodec", "copy", str(assembled_captions)])
    if assembled_captions.stat().st_size <= assembled_raw.stat().st_size:
        LOGGER.warning("Caption burn-in verification warning: file size did not increase. This might indicate that libass is missing or the ASS filter did not render, or the video compressed highly.")
    total = sum(durations) - 0.25 * max(0, len(durations) - 1)
    music = Path(music_path)
    mixed = work / "mixed_music.mp4"
    if music.exists():
        filter_complex = f"[1:a]volume=0.08,afade=t=in:d=2,afade=t=out:st={max(total-2,0):.3f}:d=2[music];[0:a][music]amix=inputs=2:duration=first[aout]"
        _run(["ffmpeg", "-y", "-i", str(assembled_captions), "-stream_loop", "-1", "-i", str(music), "-filter_complex", filter_complex, "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", str(mixed)])
    else:
        _run(["ffmpeg", "-y", "-i", str(assembled_captions), "-c", "copy", str(mixed)])
    loud = work / "loudnorm.mp4"
    _run(["ffmpeg", "-y", "-i", str(mixed), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(loud)])
    passlog = str(work / "ffmpeg2pass")
    _run(["ffmpeg", "-y", "-i", str(loud), "-vcodec", "libx264", "-b:v", "8000k", "-pass", "1", "-passlogfile", passlog, "-an", "-f", "null", os.devnull])
    _run(["ffmpeg", "-y", "-i", str(loud), "-vcodec", "libx264", "-b:v", "8000k", "-pass", "2", "-passlogfile", passlog, "-acodec", "aac", "-b:a", "192k", output_path])

    if job_id:
        try:
            from pipeline.status import update_status
            update_status(job_id, "processing", progress=80, log_message="Video assembled and encoded successfully.")
        except Exception:
            pass

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", default="script.json")
    parser.add_argument("--work-dir", default=".")
    parser.add_argument("--music", default="music/ambient.mp3")
    parser.add_argument("--captions", default="final_captions.ass")
    parser.add_argument("--output", default="final_video.mp4")
    args = parser.parse_args()
    print(assemble_video(args.script, args.work_dir, args.music, args.captions, args.output))


if __name__ == "__main__":
    main()
