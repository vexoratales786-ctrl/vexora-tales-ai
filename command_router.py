"""Natural-language command router for Sameena AI.

This module only parses commands. It does not perform uploads or other
side effects, so the UI can keep approval gates around irreversible actions.
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Command:
    intent: str
    content_type: str | None = None
    duration_seconds: int | None = None
    topic: str | None = None


def parse_command(text: str) -> Command:
    t = text.strip()
    low = t.lower()

    if not t:
        return Command("unknown")

    if re.search(r"\b(yes,?\s*upload|haan,?\s*upload|upload\s+yes)\b", low):
        return Command("approve_upload")

    if any(x in low for x in ("upload kar do", "upload karo", "publish kar do", "publish karo")):
        return Command("request_upload")

    if any(x in low for x in ("status", "report", "channel ka haal", "aaj kya hua")):
        return Command("status")

    if any(x in low for x in ("30 day", "30-day", "30 din")):
        return Command("plan_30")

    if any(x in low for x in ("aaj ka plan", "next 7", "schedule", "kal ka plan")):
        return Command("plan")

    if any(x in low for x in ("video dikhao", "show video", "preview")):
        return Command("preview")

    if any(x in low for x in ("trend", "viral topic", "kya banao", "topic batao")):
        return Command("trend")

    is_long = bool(re.search(r"\b(long|long-form|10 minute|10-minute|15 minute|15-minute)\b", low))
    is_short = bool(re.search(r"\b(short|shorts|reel|30 second|30-second|40 second|40-second|60 second|60-second)\b", low))

    if any(x in low for x in ("banao", "bana do", "make", "create", "generate", "ready karo")):
        duration = None
        m = re.search(r"\b(\d+)\s*(?:sec|second|seconds|s)\b", low)
        if m:
            duration = int(m.group(1))
        else:
            m = re.search(r"\b(\d+)\s*(?:min|minute|minutes|m)\b", low)
            if m:
                duration = int(m.group(1)) * 60

        topic = None
        topic_match = re.search(r"(?:topic|about|par|on)\s*[:\-]?\s*(.+)$", t, re.I)
        if topic_match:
            topic = topic_match.group(1).strip()

        if is_long or (duration is not None and duration >= 300):
            return Command("generate", "long", duration, topic)
        if is_short or duration is not None:
            return Command("generate", "short", duration, topic)

    return Command("unknown")
