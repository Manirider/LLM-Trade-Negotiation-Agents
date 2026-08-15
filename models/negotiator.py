from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from schemas.negotiation import Country, NegotiatorPersona

DEFAULT_POSITIONS_PATH = Path("data/trade_positions.json")


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


def _default_usa_persona() -> NegotiatorPersona:
    return NegotiatorPersona(
        country=Country.USA,
        role="Chief Trade Negotiator for the United States",
        priorities=[
            "Reduce trade deficit with China",
            "Protect intellectual property rights and patents (IP)",
            "Ensure fair market access for US companies",
            "Address forced technology transfer",
            "Strengthen enforcement mechanisms and tariff compliance",
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


def _default_china_persona() -> NegotiatorPersona:
    return NegotiatorPersona(
        country=Country.CHINA,
        role="Chief Trade Negotiator for the People's Republic of China",
        priorities=[
            "Maintain export market access to US",
            "Preserve developmental policy space and industrial sovereignty",
            "Protect domestic technology development and trade interests",
            "Ensure stable supply chains",
            "Oppose unilateral coercive measures and punitive tariffs",
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


def load_trade_positions(
    file_path: str | Path = DEFAULT_POSITIONS_PATH,
) -> dict[Country, NegotiatorPersona]:
    """Dynamically load trade positions and priorities from JSON file."""
    path = Path(file_path)
    if not path.exists():
        return {
            Country.USA: _default_usa_persona(),
            Country.CHINA: _default_china_persona(),
        }

    try:
        with path.open(encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        usa_data = data.get("USA", {})
        china_data = data.get("China", {})

        usa_persona = (
            NegotiatorPersona(country=Country.USA, **usa_data)
            if usa_data
            else _default_usa_persona()
        )
        china_persona = (
            NegotiatorPersona(country=Country.CHINA, **china_data)
            if china_data
            else _default_china_persona()
        )
    except Exception:
        return {
            Country.USA: _default_usa_persona(),
            Country.CHINA: _default_china_persona(),
        }
    else:
        return {
            Country.USA: usa_persona,
            Country.CHINA: china_persona,
        }


def get_usa_persona(file_path: str | Path = DEFAULT_POSITIONS_PATH) -> NegotiatorPersona:
    return load_trade_positions(file_path)[Country.USA]


def get_china_persona(file_path: str | Path = DEFAULT_POSITIONS_PATH) -> NegotiatorPersona:
    return load_trade_positions(file_path)[Country.CHINA]


# Export personas dynamically loaded from trade_positions.json
_INITIAL_POSITIONS = load_trade_positions()
USA_PERSONA: NegotiatorPersona = _INITIAL_POSITIONS[Country.USA]
CHINA_PERSONA: NegotiatorPersona = _INITIAL_POSITIONS[Country.CHINA]
