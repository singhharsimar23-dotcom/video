from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _extract_thumbnail(video_path: str, output_path: str = "thumbnail.jpg") -> str:
    subprocess.run(["ffmpeg", "-y", "-ss", "1", "-i", video_path, "-frames:v", "1", "-q:v", "2", output_path], check=True, capture_output=True)
    return output_path


def _video_duration(video_path: str) -> float:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path], check=True, capture_output=True, text=True)
    return round(float(result.stdout.strip()), 2)


def _credentials() -> Credentials:
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def _append_library(entry: dict[str, Any], library_path: str) -> None:
    path = Path(library_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    data = [item for item in data if item.get("id") != entry["id"]]
    data.append(entry)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _safe_filename(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in value.lower()).strip("-")[:64] or "video"


def _make_instagram_export(script: dict[str, Any], video_path: str, thumbnail: str, video_id: str) -> tuple[str, str]:
    export_dir = Path("exports") / video_id
    export_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(video_path, export_dir / "final_video.mp4")
    if Path(thumbnail).exists():
        shutil.copyfile(thumbnail, export_dir / "thumbnail.jpg")
    (export_dir / "instagram_caption.txt").write_text(script.get("instagram_caption", ""), encoding="utf-8")
    (export_dir / "youtube_description.txt").write_text(script.get("youtube_description", ""), encoding="utf-8")
    (export_dir / "metadata.json").write_text(json.dumps(script, indent=2), encoding="utf-8")
    zip_path = Path(f"{video_id}_instagram_export.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in export_dir.iterdir():
            archive.write(file, arcname=file.name)
    return str(export_dir), str(zip_path)


def _library_entry(script: dict[str, Any], video_path: str, youtube_url: str | None, thumbnail: str, status: str, download_url: str, instagram_zip: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    video_id = f"{now.strftime('%Y%m%d%H%M%S')}-{_safe_filename(script.get('topic', 'video'))}"
    return {
        "id": video_id,
        "title": script.get("youtube_title", "Untitled video"),
        "topic": script.get("topic", ""),
        "shareAngle": script.get("share_angle", ""),
        "date": now.isoformat(),
        "duration": _video_duration(video_path),
        "format": script.get("format", "reels"),
        "style": script.get("style", "cinematic"),
        "badge": "Loop optimized" if script.get("format") == "reels" else "Long-form",
        "thumbnailUrl": os.environ.get("THUMBNAIL_URL", thumbnail),
        "youtubeUrl": youtube_url,
        "downloadUrl": download_url,
        "instagramCaption": script.get("instagram_caption", ""),
        "instagramExportUrl": os.environ.get("INSTAGRAM_EXPORT_URL", instagram_zip),
        "postingStatus": "ready_for_manual_instagram_post",
        "status": status,
        "creativeScore": script.get("creative_score"),
        "algorithmSignals": ["watch-through", "replay loop", "DM-share angle", "first-3-second hook", "caption completeness"],
    }



def _upsert_supabase(entry: dict[str, Any]) -> None:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        print("Supabase credentials not set. Skipping Supabase write.")
        return
    db_entry = {
        "id": entry.get("id"),
        "title": entry.get("title"),
        "topic": entry.get("topic"),
        "share_angle": entry.get("shareAngle"),
        "date": entry.get("date"),
        "duration": entry.get("duration"),
        "format": entry.get("format"),
        "style": entry.get("style"),
        "badge": entry.get("badge"),
        "thumbnail_url": entry.get("thumbnailUrl"),
        "youtube_url": entry.get("youtubeUrl"),
        "download_url": entry.get("downloadUrl"),
        "instagram_caption": entry.get("instagramCaption"),
        "instagram_export_url": entry.get("instagramExportUrl"),
        "posting_status": entry.get("postingStatus"),
        "status": entry.get("status"),
        "creative_score": entry.get("creativeScore"),
        "algorithm_signals": entry.get("algorithmSignals"),
    }
    url = f"{supabase_url.rstrip('/')}/rest/v1/videos"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    try:
        import requests
        print(f"Upserting to Supabase table 'videos' (id={db_entry['id']})...")
        response = requests.post(url, json=db_entry, headers=headers, timeout=15)
        response.raise_for_status()
        print("Successfully upserted entry to Supabase.")
    except Exception as exc:
        print(f"Error upserting to Supabase: {exc}")


def upload_to_youtube(script_path: str = "script.json", video_path: str = "final_video.mp4", library_path: str = "data/library.json") -> dict[str, Any]:
    script = json.loads(Path(script_path).read_text(encoding="utf-8"))
    thumbnail = _extract_thumbnail(video_path)
    provisional_id = os.environ.get("GITHUB_RUN_ID") or f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_safe_filename(script.get('topic', 'video'))}"
    _, instagram_zip = _make_instagram_export(script, video_path, thumbnail, provisional_id)
    download_url = os.environ.get("DOWNLOAD_URL") or f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'owner/repo')}/releases/download/{os.environ.get('RELEASE_TAG', 'latest')}/final_video.mp4"
    youtube_url: str | None = None
    status = "release-only"
    required = ["YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"]
    if all(os.environ.get(name) for name in required):
        try:
            youtube = build("youtube", "v3", credentials=_credentials())
            is_short = script.get("format") == "reels"
            title = script.get("youtube_title", "AI Video")[:50]
            if is_short and "#Shorts" not in title:
                title = f"{title} #Shorts"[:60]
            tags = list(script.get("youtube_tags") or [])
            if is_short and (not tags or tags[0].lower() != "shorts"):
                tags.insert(0, "Shorts")
            body = {
                "snippet": {
                    "title": title,
                    "description": script.get("youtube_description", ""),
                    "tags": tags[:15],
                    "categoryId": "22" if is_short else "28",
                },
                "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False},
            }
            insert = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True))
            response = insert.execute()
            youtube_id = response["id"]
            youtube.thumbnails().set(videoId=youtube_id, media_body=MediaFileUpload(thumbnail)).execute()
            youtube.videos().update(part="status", body={"id": youtube_id, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}).execute()
            youtube_url = f"https://www.youtube.com/watch?v={youtube_id}"
            status = "published"
        except Exception as exc:
            status = f"youtube-failed-release-confirmed: {exc}"
    entry = _library_entry(script, video_path, youtube_url, thumbnail, status, download_url, instagram_zip)
    _append_library(entry, library_path)
    _upsert_supabase(entry)
    Path("publish_result.json").write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return entry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", default="script.json")
    parser.add_argument("--video", default="final_video.mp4")
    parser.add_argument("--library", default="data/library.json")
    args = parser.parse_args()
    print(json.dumps(upload_to_youtube(args.script, args.video, args.library), indent=2))


if __name__ == "__main__":
    main()
