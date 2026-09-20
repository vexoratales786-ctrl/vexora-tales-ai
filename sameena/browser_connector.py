"""Minimal Browserbase connector for Sameena.

This first adapter provides a real cloud-browser session and safe read-only
navigation. Credentials are read only from environment variables.
"""

from __future__ import annotations

import os
from typing import Any


def browse_url(url: str) -> dict[str, Any]:
    """Open a URL in a Browserbase browser and return basic page information."""
    api_key = os.getenv("BROWSERBASE_API_KEY")
    if not api_key:
        raise RuntimeError("BROWSERBASE_API_KEY is not configured.")

    from browserbase import Browserbase
    from playwright.sync_api import sync_playwright

    target = url.strip()
    if not target.startswith(("http://", "https://")):
        target = "https://" + target

    bb = Browserbase(api_key=api_key)

    with sync_playwright() as playwright:
        session = bb.sessions.create()
        browser = playwright.chromium.connect_over_cdp(session.connect_url)
        try:
            context = browser.contexts[0]
            page = context.pages[0]
            page.goto(target, wait_until="domcontentloaded", timeout=30000)
            title = page.title()
            final_url = page.url
            text = page.locator("body").inner_text(timeout=10000)
            return {
                "session_id": session.id,
                "title": title,
                "url": final_url,
                "text_preview": text[:4000],
            }
        finally:
            browser.close()
