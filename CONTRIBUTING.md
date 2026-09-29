# Contributing

Thanks for looking at this. Here's how to get involved.

## Setup

No dependencies to install for the core tool. Clone the repo and run:

```bash
python3 tests/test_engine.py
```

If that passes, you're set up.

## Ways to contribute

- **Try it and report what happens.** Run `python3 -m iapf.cli evaluate --provider mock` first (no API key needed), then try a real provider if you have a key. Open a bug report for anything that breaks.
- **Review the patterns.** The 8 IAPF patterns, their test prompts, and their scoring rules are in `iapf/patterns.py`. If you work in accessibility, cognitive disability research, or HCI, and something there doesn't match what you've seen in research or practice, please open a pattern feedback issue. This is the single most useful kind of contribution right now.
- **Add a provider.** Each AI provider is a small adapter in `iapf/providers.py` implementing one method, `complete()`. Adding a new one doesn't require touching the scoring engine.
- **Improve the reliability of scoring.** The `LLMJudge` in `iapf/judge.py` is a first-pass implementation. Suggestions for making it more consistent across runs are welcome.

## Before opening a pull request

1. Run `python3 tests/test_engine.py` and make sure it passes.
2. If you changed a pattern's prompt or rule, explain your reasoning in the PR, ideally with a source (a paper, a study, direct practice experience).
3. Keep changes scoped. Small, focused pull requests are easier to review than large ones.

## Code of conduct

Be respectful. This project exists to make AI systems more usable for people with cognitive and neurodevelopmental disabilities. Treat that goal, and the people discussing it, accordingly.
