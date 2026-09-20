"""Natural-language planner for Sameena.

The planner chooses a capability; it does not execute external actions.
Execution remains in connector adapters and sensitive actions can require
explicit confirmation.
"""

from dataclasses import dataclass

from .tool_registry import ToolRegistry, build_default_registry


@dataclass(frozen=True)
class Plan:
    tool: str
    intent: str
    requires_confirmation: bool
    reason: str


_RULES = (
    ("chat", ("hi", "hii", "hiii", "hello", "hey", "namaste", "salam")),
    ("youtube_upload", ("upload", "publish", "post it to youtube")),
    ("youtube_generate_video", ("make a video", "create a video", "video banao", "short banao")),
    ("youtube_trends", ("trend", "viral", "topic", "what should i make")),
    ("youtube_status", ("analytics", "views", "channel status", "youtube status")),
    ("shopify", ("shopify", "store", "product", "order")),
    ("canva", ("canva", "thumbnail", "design", "poster")),
    ("browser", ("open website", "browse", "research this site", "website")),
)


def plan_message(message: str, registry: ToolRegistry | None = None) -> Plan:
    registry = registry or build_default_registry()
    text = " ".join(message.lower().strip().split())

    for tool_name, phrases in _RULES:
        if any(phrase in text for phrase in phrases):
            spec = registry.get(tool_name)
            if spec is not None:
                return Plan(
                    tool=spec.name,
                    intent=text,
                    requires_confirmation=spec.requires_confirmation,
                    reason=spec.description,
                )

    return Plan(
        tool="chat",
        intent=text,
        requires_confirmation=False,
        reason="No specialized action matched; keep the conversation in chat.",
    )
