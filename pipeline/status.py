from __future__ import annotations

import argparse
import os
import json
import requests

def update_status(job_id: str, status: str, posting_status: str = "", progress: int | None = None, log_message: str = "") -> None:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        print("Supabase credentials not set. Skipping status update.")
        return

    url = f"{supabase_url.rstrip('/')}/rest/v1/videos?id=eq.{job_id}"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # Fetch existing record to preserve and append data
    existing = {}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.ok and res.json():
            existing = res.json()[0]
    except Exception as exc:
        print(f"Error fetching existing record: {exc}")

    signals = existing.get("algorithm_signals") or {}
    if not isinstance(signals, dict):
        signals = {}

    if progress is not None:
        signals["progress"] = progress
    if log_message:
        logs = signals.get("logs") or []
        logs.append(log_message)
        signals["logs"] = logs

    db_entry = {
        "status": status,
        "algorithm_signals": signals
    }
    if posting_status:
        db_entry["posting_status"] = posting_status

    try:
        response = requests.patch(url, json=db_entry, headers=headers, timeout=15)
        if response.ok:
            print(f"Successfully updated job {job_id} to status={status}, posting_status={posting_status}")
        else:
            print(f"Failed to update Supabase: {response.text}")
    except Exception as exc:
        print(f"Error updating Supabase: {exc}")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--posting-status", default="")
    parser.add_argument("--progress", type=int)
    parser.add_argument("--log", default="")
    args = parser.parse_args()
    
    update_status(args.job_id, args.status, args.posting_status, args.progress, args.log)

if __name__ == "__main__":
    main()
