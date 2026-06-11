from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.script_generator import generate_script


def run_benchmark(topics_path: str = "benchmarks/topics.json", output_path: str = "data/benchmarks.json", format_name: str = "reels", style: str = "cinematic") -> list[dict]:
    topics = json.loads(Path(topics_path).read_text(encoding="utf-8"))
    results = []
    for idx, topic in enumerate(topics, 1):
        script_path = f"benchmark_script_{idx:02d}.json"
        candidates_path = f"benchmark_candidates_{idx:02d}.json"
        script = generate_script(topic, format_name, style, script_path, candidates_path, candidate_count=3)
        results.append({
            "topic": topic,
            "selectedTitle": script.get("youtube_title"),
            "score": script.get("creative_score", {}).get("score", 0),
            "reasons": script.get("creative_score", {}).get("reasons", []),
            "hook": script.get("scenes", [{}])[0].get("voiceover", ""),
            "shareAngle": script.get("share_angle", ""),
        })
    ranked = sorted(results, key=lambda item: item["score"], reverse=True)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(ranked, indent=2), encoding="utf-8")
    return ranked


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topics", default="benchmarks/topics.json")
    parser.add_argument("--output", default="data/benchmarks.json")
    parser.add_argument("--format", choices=["reels", "longform"], default="reels")
    parser.add_argument("--style", default="cinematic")
    args = parser.parse_args()
    print(json.dumps(run_benchmark(args.topics, args.output, args.format, args.style), indent=2))


if __name__ == "__main__":
    main()
