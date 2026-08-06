from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from schemas.negotiation import Country, NegotiatorPersona


@dataclass(frozen=True, slots=True)
class NegotiatorModel:
    persona: NegotiatorPersona
    system_prompt: str
    temperature: float
    top_p: float
    max_tokens: int
    memory: tuple[str, ...] = field(default_factory=tuple)

    def with_memory(self, new_memory: str) -> NegotiatorModel:
        return NegotiatorModel(
            persona=self.persona,
            system_prompt=self.system_prompt,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            memory=(*self.memory, new_memory),
        )


USA_PERSONA: Final[NegotiatorPersona] = NegotiatorPersona(
    country=Country.USA,
    role="Chief Trade Negotiator for the United States",
    priorities=[
        "Reduce trade deficit with China",
        "Protect intellectual property rights",
        "Ensure fair market access for US companies",
        "Address forced technology transfer",
        "Strengthen enforcement mechanisms",
    ],
    flexibility=0.3,
    red_lines=[
        "Complete removal of all tariffs without reciprocity",
        "Acceptance of forced technology transfer",
        "Weakening of IP enforcement",
    ],
    strategy=(
        "Apply measured pressure through targeted tariffs while offering "
        "incremental concessions for verifiable structural reforms. "
        "Emphasize reciprocity and verification."
    ),
)

CHINA_PERSONA: Final[NegotiatorPersona] = NegotiatorPersona(
    country=Country.CHINA,
    role="Chief Trade Negotiator for the People's Republic of China",
    priorities=[
        "Maintain export market access to US",
        "Preserve developmental policy space",
        "Protect domestic technology development",
        "Ensure stable supply chains",
        "Oppose unilateral coercive measures",
    ],
    flexibility=0.35,
    red_lines=[
        "Acceptance of unilateral tariff impositions",
        "Constraints on industrial policy sovereignty",
        "Forced market opening without reciprocity",
    ],
    strategy=(
        "Seek mutually beneficial compromises while firmly defending "
        "core interests. Offer targeted market access for equivalent "
        "concessions. Emphasize win-win cooperation and stability."
    ),
)
