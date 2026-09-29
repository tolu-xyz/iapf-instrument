# IAPF Evaluation Instrument: Build Brief (V1)

## What this is

A command-line tool that runs the eight Inclusive AI Prompting Framework (IAPF)
interaction patterns as scored checks against an AI system's API, and produces
a conformance report, the accessibility documentation an institution can file
alongside a VPAT.

This is the procurement instrument described in the Inclusive AI Prompting
Framework document. Everything below is scoped to match what that document
already describes it as doing, nothing more and nothing less.

## Who runs it

A technical evaluator: an accessibility staffer, a procurement reviewer with
engineering support, or a researcher. Not the end user with a cognitive
disability. The end user only ever sees the rendered report (or, downstream,
whatever the institution builds on top of a conforming system). This is
"Option A" from the earlier design discussion: the CLI + report is the whole
V1 surface. No web front end, no login, no dashboard.

## Core loop

For each of the 8 patterns:

1. Send that pattern's **3 fixed test prompts** to the AI system under review,
   via its API.
2. Capture the raw response to each.
3. Score each response against that pattern's **rule**, a short, specific
   test for whether the behavior in question happened. Scoring is done by an
   LLM judge given: the rule, the prompt, the response, and (where useful) a
   worked example of a pass and a fail. The judge returns met / not met plus a
   one-line reason. No self-report: the system under test is never asked
   about itself.
4. Aggregate the 3 results for that pattern: **met** (2 or 3 of 3), **partial**
   (1 of 3), **not met** (0 of 3).
5. Store the prompt, response, and judge reasoning as evidence alongside the
   score. Nothing is scored without a visible transcript behind it.

Repeat for all 8 patterns. Sum criterion scores (met=2, partial=1, not
met=0) over 16 for the overall score. Criteria 1 and 6 carry a report flag
(the two highest-frequency barriers from the original study) that does not
change the number, matching the framework document's scoring rules.

## Providers (V1)

Anthropic and OpenAI APIs, behind a single adapter interface, so adding a
provider later doesn't touch the scoring engine. A `mock` provider is
included for demos and tests: deterministic canned responses, no API key
needed.

## Output

One result object, rendered to:
- Markdown (human-readable report)
- JSON (machine-readable, for anything built on top later)

HTML is deferred past V1 unless there's time. Markdown alone is enough to be
genuinely usable and genuinely public.

## What's explicitly NOT in V1

- No web interface, no login, no dashboard (matches the framework document's
  own stated scope)
- No automatic provider discovery: providers are named explicitly
- No fine-tuning or model training of any kind: the judge is a prompted LLM
  call, not a trained classifier
- No claim that this predicts real-world usability with actual disabled
  users. It is a conformance instrument, checking behavior against patterns
  *derived from* a real participatory study, not a substitute for one

## Reliability (Phase 2, not V1, but the interface has to support it)

The instrument's design has to make the later inter-rater reliability study
possible without a rewrite: fixed prompts (not regenerated per run), stored
transcripts, and a scoring rule specific enough that a second, independent
run of the *same* judge process against the *same* transcripts should
reproduce the *same* scores. V1 build should keep this in mind even though
the actual reliability study (independent human evaluators comparing
results) is out of scope for this build.

## Definition of done for V1

- Runs against at least one real provider (Anthropic) end-to-end with a real
  API key
- All 8 patterns implemented with real prompts and real scoring rules (not
  placeholders)
- Produces a Markdown + JSON report matching the framework document's Figure
  5 layout
- Has a demo mode (mock provider) that runs with zero setup, so anyone
  reviewing the repo, an officer, an expert reviewer, a collaborator, can
  see it work immediately
- README documents what it does and who it's for, matching the framework
  document's Section 5 scope statement
