from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

import requests
from gradio_client import Client

LOGGER = logging.getLogger(__name__)
FLUX_SPACE = "black-forest-labs/FLUX.1-schnell"


def _dimensions(format_name: str) -> tuple[int, int, str, str]:
    return (1080, 1920, "9:16", "480x848") if format_name == "reels" else (1920, 1080, "16:9", "848x480")


def _wake_client(space_id: str, hf_token: str | None) -> Client:
    if not hf_token:
        hf_token = None
    try:
        return Client(space_id, token=hf_token)
    except Exception as exc:
        exc_str = str(exc).lower()
        if "404" in exc_str or "not found" in exc_str or "repository" in exc_str:
            LOGGER.error("Space %s not found (404/Not Found). Bypassing wake sleep.", space_id)
            raise
        
        # Check if the space is actually sleeping/building/paused
        try:
            from huggingface_hub import space_info
            info = space_info(space_id, token=hf_token)
            stage = getattr(getattr(info, "runtime", None), "stage", "RUNNING")
            LOGGER.info("Space %s runtime stage: %s", space_id, stage)
            if stage not in ["SLEEPING", "PAUSED", "BUILDING"]:
                LOGGER.error("Space %s is in stage %s but failed: %s. Raising immediately.", space_id, stage, exc)
                raise
        except Exception as hub_exc:
            if "not found" in str(hub_exc).lower():
                LOGGER.error("Space %s not found via Hub check: %s. Raising immediately.", space_id, hub_exc)
                raise
            LOGGER.warning("Could not check space status via huggingface_hub: %s", hub_exc)
            
        LOGGER.warning("Waking sleeping/building Space %s after error: %s. Sleeping 90s...", space_id, exc)
        time.sleep(90)
        try:
            return Client(space_id, token=hf_token)
        except Exception as retry_exc:
            LOGGER.error("Failed to wake space %s on retry: %s", space_id, retry_exc)
            raise


def _download_result(result: Any, output_path: Path) -> bool:
    candidates: list[Any] = []
    if isinstance(result, dict):
        candidates.extend(result.values())
    elif isinstance(result, (list, tuple)):
        candidates.extend(result)
    else:
        candidates.append(result)
    while candidates:
        item = candidates.pop(0)
        if isinstance(item, dict):
            candidates.extend(item.values())
            continue
        if isinstance(item, (list, tuple)):
            candidates.extend(item)
            continue
        value = str(item)
        if value.startswith("http"):
            resp = requests.get(value, timeout=120)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)
            return output_path.stat().st_size > 0
        if Path(value).exists():
            shutil.copyfile(value, output_path)
            return output_path.stat().st_size > 0
    return output_path.exists() and output_path.stat().st_size > 0


def _poll(job: Any, output_path: Path, api_name: str, timeout: int = 600) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if job.done():
            return _download_result(job.result(), output_path)
        time.sleep(10)
    raise TimeoutError(f"Timed out waiting for {api_name}")


def _submit_variants(client: Client, api_names: list[str] | str, output_path: Path, variants: list[dict[str, Any]]) -> bool:
    if isinstance(api_names, str):
        api_names = [api_names]
    last_error: Exception | None = None
    for api_name in api_names:
        for kwargs in variants:
            try:
                job = client.submit(api_name=api_name, **kwargs)
                return _poll(job, output_path, api_name)
            except Exception as exc:
                last_error = exc
                LOGGER.warning("Adapter call failed for %s with keys %s: %s", api_name, sorted(kwargs), exc)
    if last_error:
        raise last_error
    return False


def _generate_ltx(scene: dict[str, Any], format_name: str, output_path: Path, hf_token: str | None) -> bool:
    _, _, _, resolution = _dimensions(format_name)
    width_val, height_val = map(int, resolution.split("x"))
    client = _wake_client("Lightricks/ltx-video-distilled", hf_token)
    duration = int(scene.get("duration_seconds", 5))
    # ui_frames_to_use is usually 8 frames per second + 1
    frames = duration * 8 + 1
    
    base = {
        "prompt": scene["visual_prompt"],
        "negative_prompt": scene.get("negative_prompt", "worst quality, inconsistent motion, blurry, jittery, distorted"),
        "input_image_filepath": None,
        "input_video_filepath": None,
        "height_ui": float(height_val),
        "width_ui": float(width_val),
        "mode": "text-to-video",
        "duration_ui": float(duration),
        "ui_frames_to_use": float(frames),
        "seed_ui": 42.0,
        "randomize_seed": True,
        "ui_guidance_scale": 3.0,
        "improve_texture_flag": True,
    }
    return _submit_variants(client, ["/text_to_video"], output_path, [base])


def _generate_wan(scene: dict[str, Any], format_name: str, output_path: Path, hf_token: str | None) -> bool:
    # 1. Generate starting frame image using FLUX first
    temp_image = output_path.with_suffix(".png")
    if not _try_flux_image(scene["visual_prompt"], temp_image, hf_token):
        LOGGER.warning("FLUX image generation failed for Wan input image.")
        return False
        
    # 2. Call image-to-video on Wan Space
    client = _wake_client("multimodalart/wan2-1-fast", hf_token)
    if format_name == "reels":
        width, height = 480, 864  # Multiple of 32
    else:
        width, height = 864, 480  # Multiple of 32
        
    duration = int(scene.get("duration_seconds", 5))
    
    base = {
        "input_image": str(temp_image),
        "prompt": scene["visual_prompt"],
        "height": float(height),
        "width": float(width),
        "negative_prompt": "Bright tones, overexposed, static, blurred details, subtitles, watermark, text, signature",
        "duration_seconds": float(duration),
        "guidance_scale": 6.0,
        "steps": 4.0,  # Wan fast uses 4 steps
        "seed": 42.0,
        "randomize_seed": True,
    }
    
    success = _submit_variants(client, ["/generate_video"], output_path, [base])
    
    # Clean up temp image
    if temp_image.exists():
        try:
            temp_image.unlink()
        except Exception:
            pass
    return success


def _generate_hunyuan(scene: dict[str, Any], format_name: str, output_path: Path, hf_token: str | None) -> bool:
    _, _, aspect_ratio, _ = _dimensions(format_name)
    client = _wake_client("tencent/HunyuanVideo", hf_token)
    return _submit_variants(client, "/predict", output_path, [
        {"prompt": scene["visual_prompt"], "negative_prompt": scene.get("negative_prompt", ""), "aspect_ratio": aspect_ratio},
        {"prompt": scene["visual_prompt"]},
    ])


def _try_flux_image(prompt: str, output_image: Path, hf_token: str | None) -> bool:
    spaces = [
        FLUX_SPACE,
        "ap123/Flux.1-Schnell",
        "mukaist/FLUX.1-schnell"
    ]
    for space in spaces:
        try:
            client = _wake_client(space, hf_token)
            variants = [
                {
                    "prompt": prompt,
                    "width": 512.0,
                    "height": 512.0,
                    "num_inference_steps": 4.0,
                    "seed": 0.0,
                    "randomize_seed": True
                },
                {
                    "prompt": prompt
                }
            ]
            if _submit_variants(client, ["/infer", "/predict"], output_image, variants):
                return True
        except Exception as exc:
            LOGGER.warning("FLUX image fallback failed for space %s: %s", space, exc)
    return False


def _ken_burns(scene: dict[str, Any], format_name: str, output_path: Path, zoom_in: bool, hf_token: str | None) -> None:
    w, h, _, _ = _dimensions(format_name)
    image_path = output_path.with_suffix(".png")
    if not _try_flux_image(scene["visual_prompt"], image_path, hf_token):
        color = "#111827" if int(scene["scene_number"]) % 2 else "#1f2937"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s={w}x{h}:d=1", "-frames:v", "1", str(image_path)], check=True, capture_output=True)
    duration = int(scene.get("duration_seconds", 5))
    zoom_expr = "min(zoom+0.0015,1.18)" if zoom_in else "if(lte(zoom,1.0),1.18,max(zoom-0.0015,1.0))"
    vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},zoompan=z='{zoom_expr}':d={duration*24}:s={w}x{h}:fps=24,format=yuv420p"
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(image_path), "-vf", vf, "-t", str(duration), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path)], check=True, capture_output=True)


ADAPTERS: list[tuple[str, Callable[[dict[str, Any], str, Path, str | None], bool]]] = [
    ("Lightricks/ltx-video-distilled", _generate_ltx),
    ("multimodalart/wan2-1-fast", _generate_wan),
]


def _write_manifest(manifest_path: Path, script: dict[str, Any], completed: list[int]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({
        "format": script.get("format"),
        "scene_total": len(script.get("scenes", [])),
        "completed_scenes": sorted(set(completed)),
        "updated_at": time.time(),
    }, indent=2), encoding="utf-8")


def _report_status(job_id: str | None, status: str, progress: int, log_message: str) -> None:
    if not job_id:
        return
    try:
        from pipeline.status import update_status
        update_status(job_id, status, progress=progress, log_message=log_message)
    except Exception as exc:
        LOGGER.warning("Status report failed for job %s: %s", job_id, exc)


def generate_videos(script_path: str = "script.json", output_dir: str = ".", scene_start: int | None = None, scene_end: int | None = None, manifest_path: str | None = None) -> list[str]:
    script = json.loads(Path(script_path).read_text(encoding="utf-8"))
    hf_token = os.environ.get("HF_TOKEN")
    job_id = os.environ.get("JOB_ID")
    outputs: list[str] = []
    completed: list[int] = []
    scenes = script["scenes"]
    if scene_start is not None:
        scenes = [s for s in scenes if int(s["scene_number"]) >= scene_start]
    if scene_end is not None:
        scenes = [s for s in scenes if int(s["scene_number"]) <= scene_end]
    
    _report_status(job_id, "processing", 15, f"Starting video clip generation for {len(scenes)} scenes...")
    
    for idx, scene in enumerate(scenes):
        scene_num = int(scene["scene_number"])
        out = Path(output_dir) / f"raw_scene_{scene_num:02d}.mp4"
        generated = False
        errors: list[str] = []
        
        progress_pct = 15 + int((idx / len(scenes)) * 20)
        _report_status(job_id, "processing", progress_pct, f"Generating scene {scene_num} / {len(scenes)}...")
        
        for name, adapter in ADAPTERS:
            started = time.time()
            try:
                LOGGER.info("Generating scene %s with %s", scene_num, name)
                if adapter(scene, script["format"], out, hf_token):
                    LOGGER.info("Generated scene %s with %s in %.1fs", scene_num, name, time.time() - started)
                    generated = True
                    _report_status(job_id, "processing", progress_pct + int(20 / len(scenes)), f"Scene {scene_num} generated with {name}.")
                    break
            except Exception as exc:
                errors.append(f"{name}: {exc}")
        if not generated:
            LOGGER.warning("All video adapters failed for scene %s; using Ken Burns fallback: %s", scene_num, " | ".join(errors))
            _report_status(job_id, "processing", progress_pct + int(20 / len(scenes)), f"Scene {scene_num} video adapters failed, using Ken Burns fallback.")
            _ken_burns(scene, script["format"], out, zoom_in=scene_num % 2 == 1, hf_token=hf_token)
        outputs.append(str(out))
        completed.append(scene_num)
        if manifest_path:
            _write_manifest(Path(manifest_path), script, completed)
        time.sleep(8)
    
    _report_status(job_id, "processing", 35, "Video clip generation finished.")
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", default="script.json")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--scene-start", type=int)
    parser.add_argument("--scene-end", type=int)
    parser.add_argument("--manifest")
    args = parser.parse_args()
    print(json.dumps(generate_videos(args.script, args.output_dir, args.scene_start, args.scene_end, args.manifest), indent=2))


if __name__ == "__main__":
    main()
