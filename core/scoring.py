from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScoringResult:
    agreement_reached: bool
    score: float
    summary: str
    final_terms: str = ""


class ScoringEngine:
    POSITIVE_KEYWORDS: tuple[str, ...] = (
        "agreement",
        "agree",
        "accept",
        "reduce",
        "lower",
        "support",
        "cooperate",
        "shared",
        "mutual",
        "compromise",
        "consensus",
        "progress",
        "constructive",
        "willing",
        "flexible",
        "concede",
        "accommodate",
    )

    NEGATIVE_KEYWORDS: tuple[str, ...] = (
        "reject",
        "deny",
        "refuse",
        "oppose",
        "impossible",
        "never",
        "conflict",
        "deadlock",
        "unacceptable",
        "non-negotiable",
        "firm",
        "stand",
        "insist",
        "demand",
        "ultimatum",
    )

    AGREEMENT_THRESHOLD: float = 0.6
    STRONG_AGREEMENT_THRESHOLD: float = 0.8
    PARTIAL_CONVERGENCE_THRESHOLD: float = 0.4

    def __init__(self) -> None:
        self._pos_patterns = [
            re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in self.POSITIVE_KEYWORDS
        ]
        self._neg_patterns = [
            re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in self.NEGATIVE_KEYWORDS
        ]

    def score_round(self, usa_text: str, china_text: str) -> ScoringResult:
        combined = f"{usa_text} {china_text}"
        pos_count = sum(1 for p in self._pos_patterns if p.search(combined))
        neg_count = sum(1 for p in self._neg_patterns if p.search(combined))
        total = pos_count + neg_count

        raw_score = 0.5 if total == 0 else pos_count / total

        score = max(0.0, min(1.0, raw_score))
        agreement = score >= self.AGREEMENT_THRESHOLD
        summary = self._generate_summary(score, agreement)
        final_terms = self._generate_final_terms(usa_text, china_text, score, agreement)
        return ScoringResult(
            agreement_reached=agreement,
            score=score,
            summary=summary,
            final_terms=final_terms,
        )

    def score_final(self, history: list[tuple[str, str]]) -> ScoringResult:
        if not history:
            return ScoringResult(
                agreement_reached=False,
                score=0.0,
                summary="No negotiation history",
                final_terms="No terms negotiated.",
            )

        last_usa, last_china = history[-1]
        return self.score_round(last_usa, last_china)

    def _generate_summary(self, score: float, agreement: bool) -> str:
        if agreement:
            if score >= self.STRONG_AGREEMENT_THRESHOLD:
                return "Strong mutual agreement reached with high cooperation"
            return "Agreement reached with moderate compromise"
        if score >= self.PARTIAL_CONVERGENCE_THRESHOLD:
            return "Partial convergence but significant gaps remain"
        return "Deadlock: fundamental disagreements persist"

    def _generate_final_terms(
        self, usa_text: str, china_text: str, score: float, agreement: bool
    ) -> str:
        if agreement:
            if score >= self.STRONG_AGREEMENT_THRESHOLD:
                return (
                    f"Comprehensive agreement: Mutual concessions accepted on tariffs, "
                    f"intellectual property protection, and market access guarantees. "
                    f"USA terms: '{usa_text[:120]}...' | China terms: '{china_text[:120]}...'"
                )
            return (
                f"Conditional agreement: Phased tariff reduction and reciprocal market access. "
                f"USA proposal: '{usa_text[:100]}...' | China response: '{china_text[:100]}...'"
            )
        return (
            "No formal agreement reached; both parties retain reservations regarding "
            "unilateral tariffs, market access reciprocity, and enforcement terms."
        )
