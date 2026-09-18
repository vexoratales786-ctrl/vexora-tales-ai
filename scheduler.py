"""Safe scheduler entry point for Vexora Tales AI.

The scheduler prepares the day's content but never performs a public YouTube
upload. Publishing remains behind the explicit approval gate in app.py.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from agent_core import generate_video
from content_plan import schedule_for_day

TZ = ZoneInfo(os.getenv("TIMEZONE", "Asia/Kolkata"))
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)


def run_today():
    now = datetime.now(TZ)
    plan = schedule_for_day(now.date())

    result = {
        "run_at": now.isoformat(),
        "plan": plan,
        "action": "prepare_content",
        "public_upload": False,
    }

    pending = DATA / "pending.json"
    if pending.exists():
        result["action"] = "pending_video_already_exists"
        result["pending_file"] = str(pending)
        (DATA / "scheduler_last_run.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
        return result

    video = generate_video(
        plan["content_type"],
        target_duration_seconds=plan["target_duration_seconds"],
    )
    result["action"] = "content_prepared"
    result["title"] = video.get("title", "")
    result["content_type"] = video.get("content_type", plan["content_type"])
    result["target_duration_seconds"] = video.get(
        "target_duration_seconds", plan["target_duration_seconds"]
    )

    (DATA / "scheduler_last_run.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    print(json.dumps(run_today(), indent=2))
