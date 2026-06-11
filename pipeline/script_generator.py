from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
from pathlib import Path
from typing import Any

import google.generativeai as genai

STYLE_PRESETS = {
    "cinematic": "anamorphic lens, shallow DOF, film grain, moody cinematic, teal-orange color grade",
    "documentary": "handheld, natural light, desaturated realism, 16mm grain, observational",
    "dreamy": "soft bokeh, pastel grade, ethereal haze, slow motion, golden hour",
    "brutalist": "harsh contrast, monochromatic, stark geometry, harsh industrial lighting",
    "neon": "cyberpunk neon-lit, rain-soaked, blue-pink grade, volumetric fog",
    "golden_hour": "warm amber tones, long shadows, soft rim light, cinematic warmth",
}
NEGATIVE_PROMPT = "blurry, watermark, text overlay, low quality, distorted faces, cartoon, anime, oversaturated, noisy"
CAMERA_MOTIONS = {"static", "pan_left", "pan_right", "dolly_in", "dolly_out", "tilt_up", "tilt_down", "orbit"}
PRIMARY_KEYWORDS = {"ai", "video", "creator", "reels", "shorts", "workflow", "automation", "cinematic", "content"}


def _system_prompt(format_name: str, style: str, candidates: int = 1) -> str:
    style_suffix = STYLE_PRESETS.get(style, STYLE_PRESETS["cinematic"])
    if format_name == "reels":
        structure = "4 scenes exactly: hook 3-4s, build 8-10s, twist 8-10s, payoff 4-6s. Target 25-35s, never exceed 45s. loop_anchor true only scenes 1 and 4. Payoff must visually echo hook for replay."
        format_clause = "Every visual prompt includes vertical composition 9:16, portrait-native framing, subject centered for mobile screen. Voiceover max 20 words per scene."
    else:
        structure = "10 scenes exactly: hook 5s, body scenes 2-9 20s each, outro 5s. Total 170-220s. loop_anchor false."
        format_clause = "Every visual prompt is standard widescreen composition."
    envelope = "Return a JSON array of candidate objects" if candidates > 1 else "Return one JSON object"
    return f"""
You are a 2026 algorithmic distribution creative director for Instagram Reels and YouTube Shorts. {envelope} only; no markdown.
Optimize every choice for: watch-through rate, replay rate, DM shares, first-3-second retention, and caption completeness.

FORMAT STRUCTURE: {structure}
CRITICAL RULES:
1. HOOK FIRST: Scene 1 is the most visually arresting moment in the whole video. No intro, context, logo, title card, or establishing shot.
2. LOOP DESIGN: Reels payoff echoes hook by subject, color, motion, or prop so the ending snaps back into the beginning.
3. SHARE-WORTHY ANGLE: Use POV/identity language or a practical insight someone would DM to a friend.
4. CAPTION COMPLETENESS: voiceover is short, punchy, semantic-search-friendly, and understandable muted.
5. NO INTRO CARD. NO OUTRO CARD. NEVER.

VISUAL PROMPT TEMPLATE:
[SHOT TYPE], [CAMERA MOVEMENT], [SUBJECT + ACTION], [ENVIRONMENT], [LIGHTING], [COLOR GRADE], [MOOD], cinematic 4K, ultra-detailed, photorealistic, {style_suffix}. {format_clause}

Each candidate schema:
{{
  "topic": "string",
  "share_angle": "specific DM-shareable POV/identity angle",
  "youtube_title": "50 chars max, keyword-first, non-clickbait",
  "youtube_description": "3 keyword-rich natural sentences; no hashtag dump",
  "youtube_tags": ["10 specific tags"],
  "instagram_caption": "2-3 keyword-rich sentences; 3-5 targeted hashtags at end only",
  "format": "reels|longform",
  "style": "{style}",
  "scenes": [{{
    "scene_number": 1,
    "role": "hook|build|twist|payoff|body|outro",
    "visual_prompt": "string",
    "negative_prompt": "{NEGATIVE_PROMPT}",
    "voiceover": "string",
    "duration_seconds": 4,
    "camera_motion": "static|pan_left|pan_right|dolly_in|dolly_out|tilt_up|tilt_down|orbit",
    "loop_anchor": false
  }}]
}}
"""


def _fallback_script(topic: str, format_name: str, style: str, variant: int = 0) -> dict[str, Any]:
    actual_topic = topic.strip() or random.choice([
        "the moment you realize AI can finish the boring edit before your coffee cools",
        "why your best creative idea always arrives when you stop forcing it",
        "the tiny workflow change that makes a creator feel unstoppable",
    ])
    roles = ["hook", "build", "twist", "payoff"] if format_name == "reels" else ["hook"] + ["body"] * 8 + ["outro"]
    durations = [4, 9, 9, 6] if format_name == "reels" else [5] + [20] * 8 + [5]
    motions = ["dolly_in", "pan_left", "orbit", "dolly_out", "tilt_up"]
    suffix = STYLE_PRESETS.get(style, STYLE_PRESETS["cinematic"])
    scenes = []
    for i, (role, dur) in enumerate(zip(roles, durations), 1):
        loop = format_name == "reels" and i in {1, 4}
        mobile = "vertical composition 9:16, portrait-native framing, subject centered for mobile screen" if format_name == "reels" else "standard widescreen composition"
        motif = "the same glowing phone reflection from scene one returns" if loop and i == len(roles) else actual_topic
        voice = "This is exactly you. Send it to that friend." if role == "payoff" else f"POV: {actual_topic}. Watch what changes."
        scenes.append({
            "scene_number": i,
            "role": role,
            "visual_prompt": f"Extreme close-up, {motions[(i + variant) % len(motions)]}, a creator reacting to {motif} mid-action, cinematic workspace, dramatic practical lighting, rich contrast, urgent curiosity, cinematic 4K, ultra-detailed, photorealistic, {suffix}, {mobile}",
            "negative_prompt": NEGATIVE_PROMPT,
            "voiceover": voice,
            "duration_seconds": dur,
            "camera_motion": motions[(i + variant) % len(motions)],
            "loop_anchor": loop,
        })
    return {
        "topic": actual_topic,
        "share_angle": f"A highly relatable POV for creators who recognize {actual_topic} and would DM it to a friend.",
        "youtube_title": ("AI Creator Workflow #Shorts" if format_name == "reels" else "AI Creator Workflow Explained")[:50],
        "youtube_description": "AI video generation helps creators turn a specific idea into cinematic short-form content. This workflow prioritizes hook speed, replay loops, captions, and useful storytelling. The result is built for retention rather than empty trend chasing.",
        "youtube_tags": ["AI video", "creator workflow", "Instagram Reels", "YouTube Shorts", "text to video", "Gemini", "cinematic AI", "video automation", "short form content", "content strategy"],
        "instagram_caption": "AI video works best when the hook feels personal and the ending loops cleanly. This one is built for muted viewing, saves, and DMs. #AIVideo #CreatorWorkflow #ReelsStrategy",
        "format": format_name,
        "style": style,
        "scenes": scenes,
    }


def _extract_json(text: str) -> Any:
    text = text.strip()
    first_bracket = text.find('[')
    first_brace = text.find('{')
    
    start_idx = -1
    json_str = text
    if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
        start_idx = first_bracket
        end_bracket = text.rfind(']')
        if end_bracket != -1:
            json_str = text[start_idx:end_bracket + 1]
    elif first_brace != -1:
        start_idx = first_brace
        end_brace = text.rfind('}')
        if end_brace != -1:
            json_str = text[start_idx:end_brace + 1]
            
    if start_idx != -1:
        try:
            return json.loads(json_str)
        except Exception:
            pass
            
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    return json.loads(text)


def _validate(script: dict[str, Any], format_name: str, style: str) -> dict[str, Any]:
    expected = 4 if format_name == "reels" else 10
    scenes = script.get("scenes") or []
    if len(scenes) != expected:
        raise ValueError(f"Expected {expected} scenes, got {len(scenes)}")
    script["format"] = format_name
    script["style"] = style
    script["youtube_title"] = str(script.get("youtube_title", "AI Video Workflow"))[:50]
    tags = [str(tag) for tag in list(script.get("youtube_tags") or [])[:10]]
    while len(tags) < 10:
        tags.append(f"{script.get('topic', 'AI video')} {len(tags)+1}")
    script["youtube_tags"] = tags
    for idx, scene in enumerate(scenes, 1):
        scene["scene_number"] = idx
        scene["negative_prompt"] = NEGATIVE_PROMPT
        prompt = str(scene.get("visual_prompt", ""))
        style_suffix = STYLE_PRESETS.get(style, STYLE_PRESETS["cinematic"])
        if style_suffix not in prompt:
            prompt = f"{prompt}, {style_suffix}"
        if format_name == "reels" and "vertical composition 9:16" not in prompt:
            prompt = f"{prompt}, vertical composition 9:16, portrait-native framing, subject centered for mobile screen"
        scene["visual_prompt"] = prompt
        if scene.get("camera_motion") not in CAMERA_MOTIONS:
            scene["camera_motion"] = "dolly_in" if idx == 1 else "static"
        if format_name == "reels":
            scene["loop_anchor"] = idx in {1, 4}
            scene["voiceover"] = " ".join(str(scene.get("voiceover", "")).split()[:20])
            scene["duration_seconds"] = [4, 9, 9, 6][idx - 1]
            scene["role"] = ["hook", "build", "twist", "payoff"][idx - 1]
        else:
            scene["loop_anchor"] = False
            scene["duration_seconds"] = 5 if idx in {1, 10} else 20
            scene["role"] = "hook" if idx == 1 else "outro" if idx == 10 else "body"
    return script


def score_script(script: dict[str, Any]) -> dict[str, Any]:
    scenes = script.get("scenes", [])
    score = 0
    reasons: list[str] = []
    title_first = str(script.get("youtube_title", "")).split(" ", 1)[0].strip("#.,!? ").lower()
    if title_first in PRIMARY_KEYWORDS:
        score += 10; reasons.append("keyword-first title")
    share = str(script.get("share_angle", "")).lower()
    if any(word in share for word in ["pov", "friend", "dm", "relatable", "identity", "you"]):
        score += 20; reasons.append("DM-shareable angle")
    if scenes:
        hook = scenes[0]
        hook_prompt = str(hook.get("visual_prompt", "")).lower()
        if any(word in hook_prompt for word in ["close-up", "mid-action", "reacting", "exploding", "falling", "glowing"]):
            score += 20; reasons.append("immediate visual hook")
        if int(hook.get("duration_seconds", 99)) <= 4:
            score += 10; reasons.append("fast hook duration")
    if script.get("format") == "reels" and len(scenes) >= 4:
        first = str(scenes[0].get("visual_prompt", "")).lower()
        last = str(scenes[-1].get("visual_prompt", "")).lower()
        overlap = set(re.findall(r"[a-z]{5,}", first)) & set(re.findall(r"[a-z]{5,}", last))
        if scenes[0].get("loop_anchor") and scenes[-1].get("loop_anchor") and len(overlap) >= 3:
            score += 20; reasons.append("loop echo detected")
    if all(len(str(scene.get("voiceover", "")).split()) <= 20 for scene in scenes):
        score += 10; reasons.append("caption-friendly voiceover")
    hashtags = re.findall(r"#\w+", str(script.get("instagram_caption", "")))
    if 3 <= len(hashtags) <= 5:
        score += 10; reasons.append("targeted hashtag count")
    return {"score": score, "reasons": reasons}


def _normalize_candidates(raw: Any, format_name: str, style: str) -> list[dict[str, Any]]:
    items = raw if isinstance(raw, list) else raw.get("candidates", [raw]) if isinstance(raw, dict) else []
    candidates = []
    for item in items:
        if isinstance(item, dict):
            try:
                candidate = _validate(item, format_name, style)
                candidate["creative_score"] = score_script(candidate)
                candidates.append(candidate)
            except Exception:
                continue
    return candidates


def generate_script(topic: str, format_name: str, style: str, output_path: str = "script.json", candidates_path: str = "script_candidates.json", candidate_count: int = 5, job_id: str = "") -> dict[str, Any]:
    if format_name not in {"reels", "longform"}:
        raise ValueError("format must be reels or longform")
    if style not in STYLE_PRESETS:
        style = "cinematic"

    job_id = job_id or os.environ.get("JOB_ID")
    if job_id:
        try:
            from pipeline.status import update_status
            update_status(job_id, "processing", progress=5, log_message="Generating script...")
        except Exception as exc:
            print(f"Status report failed: {exc}")

    # Check if a pre-approved script is stored in Supabase for this job
    if job_id:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
        if supabase_url and supabase_key:
            url = f"{supabase_url.rstrip('/')}/rest/v1/videos?id=eq.{job_id}"
            headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}"
            }
            try:
                import requests
                res = requests.get(url, headers=headers, timeout=15)
                if res.ok and res.json():
                    existing = res.json()[0]
                    signals = existing.get("algorithm_signals") or {}
                    if isinstance(signals, dict) and "script" in signals:
                        print(f"Found pre-approved script in Supabase for job_id {job_id}. Downloading...")
                        approved_script = signals["script"]
                        approved_script = _validate(approved_script, format_name, style)
                        Path(output_path).write_text(json.dumps(approved_script, indent=2), encoding="utf-8")
                        Path(candidates_path).write_text(json.dumps([approved_script], indent=2), encoding="utf-8")
                        try:
                            from pipeline.status import update_status
                            update_status(job_id, "processing", progress=15, log_message="Downloaded pre-approved script from Supabase.")
                        except Exception:
                            pass
                        return approved_script
            except Exception as exc:
                print(f"Error checking pre-approved script: {exc}")
    api_key = os.environ.get("GEMINI_API_KEY")
    candidates: list[dict[str, Any]] = []
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash-latest", system_instruction=_system_prompt(format_name, style, candidate_count))
        prompt = f"Topic: {topic or 'Surprise me with a highly DM-shareable creator/technology POV.'}\nStyle: {style}\nGenerate {candidate_count} distinct candidates."
        last_error: Exception | None = None
        for delay in (5, 10, 20):
            try:
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                candidates = _normalize_candidates(_extract_json(response.text), format_name, style)
                if candidates:
                    break
            except Exception as exc:
                last_error = exc
                time.sleep(delay)
        if not candidates and last_error:
            # fall through to local candidates so free-tier outages never hard-stop scripting
            pass
    if not candidates:
        candidates = [_validate(_fallback_script(topic, format_name, style, i), format_name, style) for i in range(candidate_count)]
        for candidate in candidates:
            candidate["creative_score"] = score_script(candidate)
    ranked = sorted(candidates, key=lambda item: item.get("creative_score", {}).get("score", 0), reverse=True)
    Path(candidates_path).write_text(json.dumps(ranked, indent=2), encoding="utf-8")
    selected = ranked[0]
    selected["candidate_count"] = len(ranked)
    selected["selection_reason"] = selected.get("creative_score", {})
    Path(output_path).write_text(json.dumps(selected, indent=2), encoding="utf-8")
    if job_id:
        try:
            from pipeline.status import update_status
            update_status(job_id, "processing", progress=15, log_message="Script generated successfully.")
        except Exception:
            pass
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="")
    parser.add_argument("--format", choices=["reels", "longform"], default="reels")
    parser.add_argument("--style", default="cinematic")
    parser.add_argument("--output", default="script.json")
    parser.add_argument("--candidates-output", default="script_candidates.json")
    parser.add_argument("--candidate-count", type=int, default=5)
    parser.add_argument("--job-id", default="")
    args = parser.parse_args()
    print(json.dumps(generate_script(args.topic, args.format, args.style, args.output, args.candidates_output, args.candidate_count, args.job_id), indent=2))


if __name__ == "__main__":
    main()
