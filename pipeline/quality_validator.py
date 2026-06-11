from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path
from typing import Any


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def _probe(path: str) -> dict[str, Any]:
    result = _run([
        "ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path
    ])
    return json.loads(result.stdout)


def _sample_blackness(path: str, timestamp: float) -> float:
    result = _run([
        "ffmpeg", "-ss", f"{max(timestamp, 0):.3f}", "-i", path, "-frames:v", "1",
        "-vf", "blackdetect=d=0.04:pic_th=0.92", "-f", "null", "-"
    ])
    output = result.stderr.lower()
    return 1.0 if "black_start" in output else 0.0


def _audio_rms(path: str) -> float:
    result = _run(["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", "-"])
    for line in result.stderr.splitlines():
        if "mean_volume:" in line:
            try:
                return float(line.split("mean_volume:", 1)[1].split(" dB", 1)[0].strip())
            except ValueError:
                pass
    return -math.inf


def validate_video(script_path: str = "script.json", video_path: str = "final_video.mp4", output_path: str = "quality_report.json") -> dict[str, Any]:
    script = json.loads(Path(script_path).read_text(encoding="utf-8"))
    expected_w, expected_h = (1080, 1920) if script.get("format") == "reels" else (1920, 1080)
    probe = _probe(video_path)
    streams = probe.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(probe.get("format", {}).get("duration", 0) or 0)
    failures: list[str] = []
    if not video_stream:
        failures.append("missing video stream")
    else:
        if int(video_stream.get("width", 0)) != expected_w or int(video_stream.get("height", 0)) != expected_h:
            failures.append(f"resolution is {video_stream.get('width')}x{video_stream.get('height')}, expected {expected_w}x{expected_h}")
        if video_stream.get("codec_name") != "h264":
            failures.append(f"video codec is {video_stream.get('codec_name')}, expected h264")
        if video_stream.get("pix_fmt") != "yuv420p":
            failures.append(f"pixel format is {video_stream.get('pix_fmt')}, expected yuv420p")
    if not audio_stream:
        failures.append("missing audio stream")
    elif audio_stream.get("codec_name") != "aac":
        failures.append(f"audio codec is {audio_stream.get('codec_name')}, expected aac")
    if script.get("format") == "reels" and not (20 <= duration <= 45):
        failures.append(f"reels duration {duration:.2f}s is outside safe 20-45s range")
    if script.get("format") == "longform" and not (160 <= duration <= 260):
        failures.append(f"longform duration {duration:.2f}s is outside safe 160-260s range")
    black_samples = {"1s": _sample_blackness(video_path, 1), "midpoint": _sample_blackness(video_path, duration / 2), "final": _sample_blackness(video_path, max(duration - 1, 0))}
    if black_samples["1s"] >= 1:
        failures.append("hook frame near 1s appears black; first-3-second retention risk")
    if sum(black_samples.values()) >= 2:
        failures.append("multiple sampled frames appear black or empty")
    mean_volume = _audio_rms(video_path)
    if mean_volume < -35:
        failures.append(f"audio mean volume {mean_volume:.1f} dB is likely too quiet")
    report = {
        "ok": not failures,
        "failures": failures,
        "duration": duration,
        "expectedResolution": f"{expected_w}x{expected_h}",
        "blackSamples": black_samples,
        "meanVolumeDb": mean_volume,
    }
    Path(output_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if failures:
        raise RuntimeError("Quality validation failed: " + "; ".join(failures))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", default="script.json")
    parser.add_argument("--video", default="final_video.mp4")
    parser.add_argument("--output", default="quality_report.json")
    args = parser.parse_args()
    print(json.dumps(validate_video(args.script, args.video, args.output), indent=2))


if __name__ == "__main__":
    main()
