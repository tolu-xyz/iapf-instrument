"""Sanity tests using the mock provider. No API key, no network."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from iapf.providers import MockProvider, _retry_delay_seconds
from iapf.judge import HeuristicJudge, LLMJudge
from iapf.engine import run_evaluation
from iapf.patterns import PATTERNS


def test_all_eight_patterns_run():
    result = run_evaluation(MockProvider(), HeuristicJudge(), system_name="test")
    assert len(result.criteria) == 8
    assert {c.pattern.id for c in result.criteria} == set(range(1, 9))


def test_each_pattern_has_three_probes():
    for p in PATTERNS:
        assert len(p.probes) == 3, f"{p.key} does not have 3 probes"


def test_score_is_in_range():
    result = run_evaluation(MockProvider(), HeuristicJudge(), system_name="test")
    assert 0 <= result.total_score <= result.max_score
    assert result.max_score == 16


def test_every_probe_has_evidence():
    result = run_evaluation(MockProvider(), HeuristicJudge(), system_name="test")
    for c in result.criteria:
        for probe in c.probes:
            assert probe.response, "every scored probe must have a captured response"
            assert probe.verdict.reason, "every verdict must have a reason"


class _FakeHTTPBody:
    """Minimal stand-in for an HTTPError's readable body, so retry-delay
    parsing can be tested without hitting a real API."""

    def __init__(self, payload_bytes):
        self._payload = payload_bytes

    def read(self):
        return self._payload


def test_retry_delay_parses_server_suggestion():
    body = (
        b'{"error": {"details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", '
        b'"retryDelay": "5s"}]}}'
    )
    delay = _retry_delay_seconds(_FakeHTTPBody(body), default=99)
    assert delay == 6.0  # 5s from the server, plus the function's 1s safety margin


def test_retry_delay_falls_back_to_default_when_unparseable():
    delay = _retry_delay_seconds(_FakeHTTPBody(b"not json"), default=7)
    assert delay == 7


class _GarbageProvider:
    """A provider whose judge response isn't valid JSON, to check the
    judge fails safe instead of raising."""

    name = "garbage"

    def complete(self, messages):
        return "I cannot comply with that request."


def test_llm_judge_fails_safe_on_unparseable_response():
    pattern = PATTERNS[0]
    verdict = LLMJudge(_GarbageProvider()).score(pattern, ["some prompt"], "some response")
    assert verdict.met is False
    assert "unparseable" in verdict.reason.lower()


if __name__ == "__main__":
    test_all_eight_patterns_run()
    test_each_pattern_has_three_probes()
    test_score_is_in_range()
    test_every_probe_has_evidence()
    test_retry_delay_parses_server_suggestion()
    test_retry_delay_falls_back_to_default_when_unparseable()
    test_llm_judge_fails_safe_on_unparseable_response()
    print("All tests passed.")
