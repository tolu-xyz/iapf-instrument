import argparse
import os
import sys

from .providers import get_provider
from .judge import LLMJudge, HeuristicJudge
from .engine import run_evaluation
from .report import to_markdown_brief, to_markdown_full, to_json


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="iapf",
        description="Run the Inclusive AI Prompting Framework's eight interaction "
                     "patterns as scored checks against an AI system's API.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ev = sub.add_parser("evaluate", help="Run an evaluation and produce a report.")
    ev.add_argument("--provider", choices=["anthropic", "openai", "gemini", "mock"], default="mock",
                     help="Which AI system to evaluate. 'mock' needs no API key, use it to try the tool.")
    ev.add_argument("--model", default=None, help="Override the provider's default model.")
    ev.add_argument("--system-name", default=None, help="Label for the report (defaults to the provider name).")
    ev.add_argument("--out", default="reports/report",
                     help="Output path prefix. Writes <out>.md (brief summary), "
                          "<out>.evidence.md (full transcripts), and <out>.json (raw data).")
    ev.add_argument("--judge-provider", choices=["anthropic", "openai", "gemini"], default=None,
                     help="Provider to use for scoring. Defaults to the same provider being evaluated. "
                          "Ignored (heuristic judge used instead) when --provider mock.")

    args = parser.parse_args(argv)

    if args.command == "evaluate":
        kwargs = {}
        if args.model:
            kwargs["model"] = args.model
        provider = get_provider(args.provider, **kwargs)

        if args.provider == "mock":
            judge = HeuristicJudge()
        else:
            judge_provider_name = args.judge_provider or args.provider
            judge = LLMJudge(get_provider(judge_provider_name))

        print(f"Running IAPF evaluation against provider={args.provider} ...", file=sys.stderr)
        result = run_evaluation(provider, judge, system_name=args.system_name)

        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        brief_path = f"{args.out}.md"
        evidence_path = f"{args.out}.evidence.md"
        json_path = f"{args.out}.json"
        with open(brief_path, "w") as f:
            f.write(to_markdown_brief(result))
        with open(evidence_path, "w") as f:
            f.write(to_markdown_full(result))
        with open(json_path, "w") as f:
            f.write(to_json(result))

        print(f"Score: {result.total_score}/{result.max_score} ({result.percentage}%)", file=sys.stderr)
        print(f"Wrote {brief_path} (summary), {evidence_path} (full evidence), and {json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
