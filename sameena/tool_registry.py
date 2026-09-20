"""Sameena tool registry.

This module keeps tool metadata separate from execution.  It is intentionally
small so new connectors can be added without rewriting the chat UI.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    category: str
    requires_confirmation: bool = False
    handler: Optional[Callable[..., Any]] = None


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def all(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def names(self) -> list[str]:
        return list(self._tools)


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()

    # Existing YouTube capabilities.  Handlers are attached by the runtime
    # adapter so this module does not import the current YouTube implementation.
    registry.register(ToolSpec(
        name="youtube_status",
        description="Check channel status and recent YouTube analytics.",
        category="youtube",
    ))
    registry.register(ToolSpec(
        name="youtube_trends",
        description="Research current topics and competition for the channel.",
        category="youtube",
    ))
    registry.register(ToolSpec(
        name="youtube_generate_video",
        description="Generate a planned YouTube video package.",
        category="youtube",
        requires_confirmation=False,
    ))
    registry.register(ToolSpec(
        name="youtube_upload",
        description="Upload a prepared video to YouTube.",
        category="youtube",
        requires_confirmation=True,
    ))

    # Connectors available to the Sameena product.  The actual authenticated
    # action adapters are added separately; no passwords or tokens belong here.
    registry.register(ToolSpec(
        name="shopify",
        description="Read or perform authorized Shopify store actions.",
        category="shopify",
        requires_confirmation=True,
    ))
    registry.register(ToolSpec(
        name="canva",
        description="Create or modify authorized Canva designs.",
        category="canva",
        requires_confirmation=False,
    ))
    registry.register(ToolSpec(
        name="browser",
        description="Navigate websites and perform browser tasks where permitted.",
        category="browser",
        requires_confirmation=True,
    ))

    return registry
