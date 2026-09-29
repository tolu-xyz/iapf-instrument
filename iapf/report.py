"""Renders an EvaluationResult to three outputs:

- to_markdown_brief(): a short, table-first summary. This is the default
  report anyone reads first, and it applies the same principles the
  instrument checks for (short by default, one clear thing at a time,
  no wall of unprompted detail).
- to_markdown_full(): the full evidence report, every probe's transcript
  and reasoning, matching the framework document's Figure 5 layout. For
  anyone who wants to verify a specific finding.
- to_json(): machine-readable, same data as the full report.
"""

import json
from .engine import EvaluationResult

STATUS_LABEL = {
    "meets": "Meets",
    "partially_meets": "Partially meets",
    "does_not_meet": "Does not meet",
}

STATUS_SYMBOL = {
    "meets": "✅",
    "partially_meets": "⚠️",
    "does_not_meet": "❌",
}


def to_markdown_brief(result: EvaluationResult) -> str:
    lines = []
    lines.append(f"# {result.system_name}: cognitive accessibility summary")
    lines.append("")
    lines.append(f"**Score: {result.total_score} of {result.max_score} ({result.percentage}%)**")
    lines.append("")

    not_met = [c for c in result.criteria if c.status == "does_not_meet"]
    partial = [c for c in result.criteria if c.status == "partially_meets"]
    if not_met:
        names = ", ".join(c.pattern.name for c in not_met)
        lines.append(f"**Biggest gaps:** {names}.")
    elif partial:
        lines.append("**No full misses.** A few patterns are only partially met.")
    else:
        lines.append("**Meets every pattern checked.**")
    lines.append("")

    lines.append("| Pattern | What it checks | Result |")
    lines.append("|---|---|---|")
    for c in result.criteria:
        flag = " ⚑" if c.pattern.report_flag else ""
        lines.append(f"| {c.pattern.name}{flag} | {c.pattern.short_description} | {STATUS_SYMBOL[c.status]} {STATUS_LABEL[c.status]} |")
    lines.append("")
    lines.append("⚑ = one of the two highest-frequency barriers from the original study.")
    lines.append("")

    lines.append("**Next steps:**")
    if not_met:
        lines.append(f"- Read the full evidence for: {', '.join(c.pattern.name for c in not_met)}.")
    lines.append("- Full transcripts and reasoning: the `.evidence.md` file next to this one.")
    lines.append("- Raw data: the `.json` file next to this one.")

    return "\n".join(lines) + "\n"


def to_markdown_full(result: EvaluationResult) -> str:
    lines = []
    lines.append("# Cognitive Accessibility Conformance Report")
    lines.append("_Companion to the VPAT / ACR. Covers the cognitive-interaction dimension not addressed by WCAG-based testing._\n")
    lines.append(f"**Product / interface evaluated:** {result.system_name}")
    lines.append("**Method:** api, 3 test exchanges per criterion, IAPF instrument v0.1.0")
    lines.append(f"**Evaluated on:** {result.run_at}\n")

    lines.append("## Summary\n")
    lines.append(f"**Overall score: {result.total_score} / {result.max_score} ({result.percentage}%)**\n")
    meets = sum(1 for c in result.criteria if c.status == "meets")
    partial = sum(1 for c in result.criteria if c.status == "partially_meets")
    not_met = sum(1 for c in result.criteria if c.status == "does_not_meet")
    lines.append(f"- Meets: {meets}")
    lines.append(f"- Partially meets: {partial}")
    lines.append(f"- Does not meet: {not_met}\n")

    lines.append("## Criteria: Inclusive AI Prompting Framework\n")
    lines.append("| # | Pattern | Rating | Flag |")
    lines.append("|---|---|---|---|")
    for c in result.criteria:
        flag = "⚑" if c.pattern.report_flag else ""
        lines.append(f"| {c.pattern.id} | {c.pattern.name} | {STATUS_LABEL[c.status]} | {flag} |")
    lines.append("")
    lines.append("⚑ = one of the two highest-frequency barriers reported in the original co-design study (does not change the score).\n")

    lines.append("## Evidence\n")
    for c in result.criteria:
        lines.append(f"### {c.pattern.id}. {c.pattern.name}: {STATUS_LABEL[c.status]} ({c.met_count} of 3)\n")
        lines.append(f"_Rule: {c.pattern.rule}_\n")
        for i, probe in enumerate(c.probes, start=1):
            verdict_word = "PASS" if probe.verdict.met else "FAIL"
            lines.append(f"**Probe {i} of 3: {verdict_word}**")
            for j, turn in enumerate(probe.turns):
                speaker = "User" if j % 2 == 0 else "Assistant"
                lines.append(f"> {speaker}: {turn}")
            lines.append(f"> Result: {probe.verdict.reason}\n")

    return "\n".join(lines)


def to_json(result: EvaluationResult) -> str:
    data = {
        "system_name": result.system_name,
        "provider": result.provider_name,
        "run_at": result.run_at,
        "total_score": result.total_score,
        "max_score": result.max_score,
        "percentage": result.percentage,
        "criteria": [
            {
                "id": c.pattern.id,
                "key": c.pattern.key,
                "name": c.pattern.name,
                "status": c.status,
                "score": c.score,
                "met_count": c.met_count,
                "report_flag": c.pattern.report_flag,
                "probes": [
                    {
                        "turns": probe.turns,
                        "response": probe.response,
                        "met": probe.verdict.met,
                        "reason": probe.verdict.reason,
                    }
                    for probe in c.probes
                ],
            }
            for c in result.criteria
        ],
    }
    return json.dumps(data, indent=2)
