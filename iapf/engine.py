"""Runs every pattern's probes against a provider, scores each with a
judge, and aggregates into a conformance result: the object report.py
renders to Markdown/JSON."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from .patterns import PATTERNS, Pattern, Probe
from .judge import Judge, Verdict


@dataclass
class ProbeResult:
    turns: List[str]
    response: str
    verdict: Verdict


@dataclass
class CriterionResult:
    pattern: Pattern
    probes: List[ProbeResult]

    @property
    def met_count(self) -> int:
        return sum(1 for p in self.probes if p.verdict.met)

    @property
    def status(self) -> str:
        if self.met_count >= 2:
            return "meets"
        if self.met_count == 1:
            return "partially_meets"
        return "does_not_meet"

    @property
    def score(self) -> int:
        return {"meets": 2, "partially_meets": 1, "does_not_meet": 0}[self.status]


@dataclass
class EvaluationResult:
    system_name: str
    provider_name: str
    run_at: str
    criteria: List[CriterionResult]

    @property
    def total_score(self) -> int:
        return sum(c.score for c in self.criteria)

    @property
    def max_score(self) -> int:
        return len(self.criteria) * 2

    @property
    def percentage(self) -> float:
        return round(100 * self.total_score / self.max_score, 1)


def _run_probe(provider, probe: Probe):
    """Run one probe's turns against the provider. Returns
    (turns_for_transcript, final_response)."""
    messages = []
    final_response = None
    transcript_turns = []
    for i, turn in enumerate(probe.turns):
        messages.append({"role": "user", "content": turn})
        transcript_turns.append(turn)
        response = provider.complete(messages)
        if i < len(probe.turns) - 1:
            messages.append({"role": "assistant", "content": response})
            transcript_turns.append(response)
        else:
            final_response = response
    return transcript_turns, final_response


def run_evaluation(provider, judge: Judge, system_name: str = None) -> EvaluationResult:
    system_name = system_name or provider.name
    criteria: List[CriterionResult] = []

    for pattern in PATTERNS:
        probe_results = []
        for probe in pattern.probes:
            transcript_turns, response = _run_probe(provider, probe)
            verdict = judge.score(pattern, transcript_turns, response)
            probe_results.append(ProbeResult(turns=transcript_turns, response=response, verdict=verdict))
        criteria.append(CriterionResult(pattern=pattern, probes=probe_results))

    return EvaluationResult(
        system_name=system_name,
        provider_name=provider.name,
        run_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        criteria=criteria,
    )
