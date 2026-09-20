"""Sameena runtime: safe dispatch layer between planning and real connectors.

The runtime owns execution policy. Connector credentials are read from the
environment only; secrets must never be sent through chat messages.
"""

from dataclasses import dataclass
import os
from typing import Any, Callable

from .tool_registry import ToolRegistry, build_default_registry


@dataclass
class ActionResult:
    ok: bool
    tool: str
    message: str
    data: dict[str, Any] | None = None


class SameenaRuntime:
    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.registry = registry or build_default_registry()
        self._handlers: dict[str, Callable[..., Any]] = {}

    def register_handler(self, tool: str, handler: Callable[..., Any]) -> None:
        if self.registry.get(tool) is None:
            raise ValueError(f"Unknown Sameena tool: {tool}")
        self._handlers[tool] = handler

    def connection_status(self) -> dict[str, bool]:
        # Presence only; values are never returned.
        return {
            "youtube": bool(os.getenv("YOUTUBE_CLIENT_ID") and os.getenv("YOUTUBE_CLIENT_SECRET")),
            "shopify": bool(os.getenv("SHOPIFY_SHOP_DOMAIN") and os.getenv("SHOPIFY_ACCESS_TOKEN")),
            "meta": bool(os.getenv("META_ACCESS_TOKEN")),
            "browser": bool(os.getenv("BROWSERBASE_API_KEY") or os.getenv("BROWSER_AUTOMATION_API_KEY")),
            "ai": bool(os.getenv("GEMINI_API_KEY")),
        }

    def execute(self, tool: str, *, confirmed: bool = False, **kwargs: Any) -> ActionResult:
        spec = self.registry.get(tool)
        if spec is None:
            return ActionResult(False, tool, "Unknown tool.")

        if spec.requires_confirmation and not confirmed:
            return ActionResult(
                False,
                tool,
                f"Confirmation required before executing: {spec.description}",
            )

        handler = self._handlers.get(tool)
        if handler is None:
            return ActionResult(
                False,
                tool,
                f"{tool} is planned, but its secure runtime adapter is not attached yet.",
            )

        try:
            value = handler(**kwargs)
            return ActionResult(True, tool, "Action completed.", value if isinstance(value, dict) else {"result": value})
        except Exception as exc:
            return ActionResult(False, tool, f"Action failed: {exc}")
