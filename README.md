# IAPF Evaluation Instrument

A free, open-source tool that checks whether an AI system's prompting
interface can be used by people with cognitive and neurodevelopmental
disabilities: ADHD, autism, depression, and anxiety.

It runs the eight interaction patterns of the **Inclusive AI Prompting
Framework (IAPF)**, developed through a participatory co-design study with
affected users, as scored checks against an AI system's API, and produces a
short conformance report designed to sit alongside the accessibility
documentation (VPAT) institutions already collect from vendors.

**Who this is for:** primarily U.S. public institutions procuring or
deploying AI systems (under the ADA Title II rule and the Section 504 rule),
and the AI teams building the systems they buy. It's also usable by
private companies building AI products, accessibility researchers and
practitioners, and anyone else who wants to check an AI system's cognitive
accessibility. See the [framework document](docs/BRIEF.md) for the full
research background.

**Status:** Version 1, in active development. This is a conformance
instrument: it checks an AI system's behavior against patterns derived from
real research with this population. It is not a substitute for ongoing
usability testing with actual users.

## Requirements

Python 3.9 or later. No other dependencies for the core tool.

## Running the tests

```bash
python3 tests/test_engine.py
```

## Quickstart (no API key needed)

Try the tool with a scripted, fake AI system. No signup, no cost, no key:

```bash
pip install -e .   # or just run from the repo root, no install needed
python3 -m iapf.cli evaluate --provider mock --out reports/demo
cat reports/demo.md
```

## Evaluating a real AI system (requires your own API key)

Once you've tried the quickstart above, here's how to run a genuine
evaluation against a real provider. This step is optional and separate
from the quickstart:

```bash
export ANTHROPIC_API_KEY=sk-...
python3 -m iapf.cli evaluate --provider anthropic --system-name "Claude" --out reports/claude

export OPENAI_API_KEY=sk-...
python3 -m iapf.cli evaluate --provider openai --system-name "GPT-4.1" --out reports/gpt

export GEMINI_API_KEY=...
python3 -m iapf.cli evaluate --provider gemini --system-name "Gemini" --out reports/gemini
```

Each run produces three files: `<out>.md` (a short, table-first summary,
the one to read first), `<out>.evidence.md` (every probe's full transcript
and reasoning, for verifying a specific finding), and `<out>.json` (the
same data, machine-readable).

## How it works

For each of the 8 patterns, the instrument sends 3 fixed test prompts to the
system under review and scores the *actual response behavior*, never a
self-report, against a specific rule.

## The eight patterns

| # | Pattern | What "meets" means |
|---|---|---|
| 1 | Ask, don't assume | Asks one focused question instead of guessing |
| 2 | Offer directions, not just outputs | Presents 2-3 options instead of picking one path |
| 3 | Set once, reuse | Remembers context without the user repeating it |
| 4 | Short by default, expand on request | Answers stay concise unless asked for more |
| 5 | One step at a time when stuck | Gives one step at a time on multi-part tasks |
| 6 | Name the recovery move | Names a specific fix when something isn't working |
| 7 | Protect what matters, lightly | Honors a stated limit without being reminded |
| 8 | Low-capacity mode | Gives short, single-focus answers on low-capacity days |

Full test prompts and scoring rules for each pattern are in
[iapf/patterns.py](iapf/patterns.py); the build rationale is in
[docs/BRIEF.md](docs/BRIEF.md).

## What Version 1 covers

- The eight IAPF interaction patterns, three probes each
- Anthropic and OpenAI APIs, behind a common provider interface
- A `mock` provider for zero-setup demos and tests
- Markdown and JSON report output

**Not in Version 1:** a web interface, a login, a dashboard, other AI
providers, or other disability categories.

**Known limitation:** a run is not resumable. If it fails partway through
(for example, a rate limit on a free-tier API key), re-run it from the
start rather than picking up where it left off. Fixing this is future work,
not a V1 goal.

## Completing the instrument

Confirming that independent evaluators applying the instrument to the same
system reach the same result (an inter-rater reliability study), and
extending the criteria to interaction types the original study did not
cover.

## License

MIT. See [LICENSE](LICENSE).

## Contributing

Reviewing the 8 patterns and their scoring rules against real accessibility
research or practice is the most useful contribution right now. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Citation

If you use this instrument, please cite it:

Adegbite, T. (2026). IAPF Evaluation Instrument (v1.0.1). Zenodo.
https://doi.org/10.5281/zenodo.23047878
