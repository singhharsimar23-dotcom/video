from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Callable, TypeVar

import requests

from pipeline.audio_generator import generate_audio
from pipeline.caption_generator import generate_captions
from pipeline.script_generator import generate_script
from pipeline.video_assembler import assemble_video
from pipeline.video_generator import generate_videos
from pipeline.youtube_uploader import upload_to_youtube
from pipeline.quality_validator import validate_video

T = TypeVar("T")

class StepFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "step"):
            record.step = "pipeline"
        return True

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(step)s | %(message)s")
LOGGER = logging.getLogger("studio")
LOGGER.addFilter(StepFilter())


def notify_failure(step: str, error: Exception) -> None:
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        return
    try:
        requests.post(f"https://ntfy.sh/{topic}", data=f"Failed at {step}: {error}", timeout=10)
    except Exception:
        LOGGER.warning("Could not send ntfy failure notification", extra={"step": "notify"})


def run_step(name: str, fn: Callable[[], T]) -> T:
    LOGGER.info("Starting", extra={"step": name})
    try:
        result = fn()
        LOGGER.info("Completed", extra={"step": name})
        return result
    except Exception as exc:
        LOGGER.exception("Failed: %s", exc, extra={"step": name})
        notify_failure(name, exc)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default=os.environ.get("VIDEO_TOPIC", ""))
    parser.add_argument("--format", choices=["reels", "longform"], default=os.environ.get("VIDEO_FORMAT", "reels"))
    parser.add_argument("--style", default=os.environ.get("VIDEO_STYLE", "cinematic"))
    parser.add_argument("--voice", choices=["male", "female"], default=os.environ.get("VIDEO_VOICE", "female"))
    args = parser.parse_args()
    try:
        run_step("Scripting", lambda: generate_script(args.topic, args.format, args.style, "script.json"))
        run_step("Generating clips", lambda: generate_videos("script.json", "."))
        run_step("Generating audio", lambda: generate_audio("script.json", args.voice, "."))
        run_step("Adding captions", lambda: generate_captions("script.json", ".", "final_captions.ass"))
        run_step("Assembling", lambda: assemble_video("script.json", ".", "music/ambient.mp3", "final_captions.ass", "final_video.mp4"))
        run_step("Quality validation", lambda: validate_video("script.json", "final_video.mp4", "quality_report.json"))
        run_step("Uploading", lambda: upload_to_youtube("script.json", "final_video.mp4", "data/library.json"))
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
