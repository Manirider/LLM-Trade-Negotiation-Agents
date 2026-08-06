from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TradeIssueModel:
    topic: str
    description: str
    usa_priorities: tuple[str, ...]
    china_priorities: tuple[str, ...]
    context: str | None

    def to_prompt_context(self) -> str:
        lines = [
            f"Issue: {self.topic}",
            f"Description: {self.description}",
        ]
        if self.usa_priorities:
            lines.append(f"USA Priorities: {', '.join(self.usa_priorities)}")
        if self.china_priorities:
            lines.append(f"China Priorities: {', '.join(self.china_priorities)}")
        if self.context:
            lines.append(f"Context: {self.context}")
        return "\n".join(lines)

    @classmethod
    def from_request(cls, issue: str, rounds: int) -> TradeIssueModel:
        topic = issue[:100]
        return cls(
            topic=topic,
            description=issue,
            usa_priorities=(
                "Reduce trade deficit",
                "Protect intellectual property",
                "Fair market access",
            ),
            china_priorities=(
                "Maintain export access",
                "Policy sovereignty",
                "Stable supply chains",
            ),
            context=f"Negotiation limited to {rounds} rounds. Seek practical compromise.",
        )
