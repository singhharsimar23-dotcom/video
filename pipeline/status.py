from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_PATH = Path(os.environ.get("JOB_STATUS_PATH", "data/current_job.json"))


def write_status(step: str, status: str = "in_progress", **extra: Any) -> dict[str, Any]:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "step": step,
        "status": status,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "runId": os.environ.get("GITHUB_RUN_ID"),
        "algorithmSignals": [
            "watch-through rate",
            "replay rate",
            "DM shares",
            "first-3-second retention",
            "caption completeness",
        ],
    }
    payload.update({k: v for k, v in extra.items() if v is not None})
    STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
