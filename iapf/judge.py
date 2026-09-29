"""Scoring. A judge takes a pattern's rule plus a transcript and returns a
verdict, met or not_met, with a one-line reason. The system under test is
never asked to evaluate itself; only the judge sees the rule.

Two judge implementations:

- LLMJudge: sends the rule + transcript to a real model and asks for a
  structured verdict. Used for real evaluation runs.
- HeuristicJudge: fast, deterministic, rule-based approximation used with
  the mock provider, so `iapf evaluate --provider mock` needs no API key at
  all, not even for judging. It is intentionally simple; it exists for
  demos and tests, not for real conformance findings.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Verdict:
    met: bool
    reason: str


class Judge(ABC):
    @abstractmethod
    def score(self, pattern, turns, response: str) -> Verdict:
        raise NotImplementedError


class LLMJudge(Judge):
    def __init__(self, provider):
        self.provider = provider

    def score(self, pattern, turns, response: str) -> Verdict:
        transcript = "\n".join(
            f"{'User' if i % 2 == 0 else 'Assistant'}: {t}"
            for i, t in enumerate(turns)
        )
        prompt = (
            "You are scoring one exchange from an AI system against a "
            "single accessibility criterion. Judge only the RESPONSE "
            "against the RULE. Do not judge tone or quality generally.\n\n"
            f"RULE:\n{pattern.rule}\n\n"
            f"TRANSCRIPT (the prompts sent):\n{transcript}\n\n"
            f"RESPONSE UNDER REVIEW:\n{response}\n\n"
            "Reply with strict JSON only, no other text: "
            '{"met": true or false, "reason": "one sentence, citing what '
            'the response did or didn\'t do"}'
        )
        raw = self.provider.complete([{"role": "user", "content": prompt}])
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            data = json.loads(match.group(0) if match else raw)
            return Verdict(met=bool(data["met"]), reason=str(data["reason"]))
        except Exception:
            return Verdict(met=False, reason=f"Judge response unparseable: {raw[:200]}")


class HeuristicJudge(Judge):
    """Rule-based approximation per pattern, for demo/test use only."""

    def score(self, pattern, turns, response: str) -> Verdict:
        handler = getattr(self, f"_score_{pattern.key}", self._score_default)
        return handler(response)

    def _word_count(self, text: str) -> int:
        return len(text.split())

    def _score_ask_dont_assume(self, response):
        has_question = "?" in response
        is_short = self._word_count(response) < 40
        met = has_question and is_short
        return Verdict(met, f"Contains a question: {has_question}; short (<40 words): {is_short}")

    def _score_offer_directions(self, response):
        markers = len(re.findall(r"\(\d\)|^\d\.|;\s|,\s*or\b", response, re.MULTILINE))
        met = markers >= 2
        return Verdict(met, f"Found {markers} option-like markers (need 2+)")

    def _score_set_once_reuse(self, response):
        # Heuristic: short/casual replies (<40 words) are treated as
        # reflecting a stated "short and casual" persona; long generic
        # replies are treated as having dropped the context.
        met = self._word_count(response) < 40
        return Verdict(met, f"Response length {self._word_count(response)} words (context-appropriate if short)")

    def _score_short_by_default(self, response):
        wc = self._word_count(response)
        met = wc < 120
        return Verdict(met, f"{wc} words (meets if under 120)")

    def _score_one_step_at_a_time(self, response):
        step_count = len(re.findall(r"^\d\.|^step \d", response, re.MULTILINE | re.IGNORECASE))
        met = step_count <= 1 and ("next" in response.lower() or "let me know" in response.lower() or self._word_count(response) < 40)
        return Verdict(met, f"{step_count} enumerated steps in one response; invites continuation: {met}")

    def _score_name_the_recovery_move(self, response):
        recovery_words = ["rephrase", "simpler", "start over", "example", "shorter", "different", "another way", "focus on"]
        met = any(w in response.lower() for w in recovery_words) and "apolog" not in response.lower()[:20]
        return Verdict(met, f"Named a specific alternative action: {met}")

    def _score_protect_lightly(self, response):
        # crude proxy: shorter, non-generic responses are more likely to
        # have honored a stated constraint than long generic ones
        met = self._word_count(response) < 30
        return Verdict(met, f"{self._word_count(response)} words, treated as constraint-respecting if concise")

    def _score_low_capacity_mode(self, response):
        wc = self._word_count(response)
        sentences = len(re.findall(r"[.!?]", response))
        met = wc < 40 and sentences <= 3
        return Verdict(met, f"{wc} words, ~{sentences} sentences (meets if <40 words, <=3 sentences)")

    def _score_default(self, response):
        return Verdict(False, "No heuristic defined for this pattern")
