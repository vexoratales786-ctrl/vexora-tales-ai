"""Vexora Tales / Sameena originality and publishing safety gate.

This gate is intentionally conservative: it does not claim that any AI check can
provide a legal guarantee of zero copyright claims. It blocks obvious reuse,
re-upload, copied-source and branding patterns before a public upload.
"""

import re
from pathlib import Path


BLOCK_PATTERNS = [
    r"\breupload\b",
    r"\bre-upload\b",
    r"\bdownloaded?\s+(?:from|off)\s+youtube\b",
    r"\bcop(?:y|ied|ying)\s+(?:this|the)\s+(?:video|script|content)\b",
    r"\buse\s+the\s+same\s+(?:script|video|footage|clips?)\b",
    r"\bmr\.?\s*beast\b",
    r"\bmovie\s+clip\b",
    r"\btv\s+clip\b",
    r"\bfull\s+episode\b",
    r"\bno\s+copyright\b",
]


def _text(value):
    if isinstance(value, list):
        return " ".join(str(x) for x in value)
    return str(value or "")


def check_originality(metadata, script_path=None):
    """Return a conservative pre-upload result.

    Passing this check means the project did not detect obvious reuse signals;
    it is not a legal determination that a work is copyright-free.
    """
    title = _text(metadata.get("title"))
    description = _text(metadata.get("description"))
    tags = _text(metadata.get("tags"))
    script = ""
    if script_path:
        p = Path(script_path)
        if p.exists():
            script = p.read_text(encoding="utf-8", errors="ignore")

    combined = "\n".join([title, description, tags, script]).lower()
    hits = [pattern for pattern in BLOCK_PATTERNS if re.search(pattern, combined, re.I)]

    # Explicitly reject external video/source URLs in metadata or script.
    urls = re.findall(r"https?://\S+", combined)
    video_urls = [u for u in urls if any(x in u for x in ("youtube.com", "youtu.be", "tiktok.com", "instagram.com"))]
    if video_urls:
        hits.append("external social/video URL")

    if hits:
        return {
            "approved": False,
            "reason": "Potential reused/copyrighted material detected.",
            "signals": hits,
        }

    return {
        "approved": True,
        "reason": "No obvious reuse signals detected. Content should still be original and use licensed/generated assets only.",
        "signals": [],
    }
