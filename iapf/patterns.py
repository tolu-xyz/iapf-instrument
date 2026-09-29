"""The eight IAPF interaction patterns, written as testable criteria.

Each pattern has three fixed probes. A probe is either a single prompt,
or a short list of turns (for patterns that only show up across a
conversation, like recovery from a bad response). Prompts are fixed, not
regenerated per run, so results are reproducible across evaluators. This
matters for the planned inter-rater reliability study.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Probe:
    turns: List[str]  # one or more user turns, in order


@dataclass(frozen=True)
class Pattern:
    id: int
    key: str
    name: str
    conventional_principle: str
    rule: str  # the scoring rule given to the judge
    short_description: str  # one line, for brief reports
    probes: List[Probe]
    report_flag: bool = False  # criteria 1 and 6: highest-frequency barriers


PATTERNS: List[Pattern] = [
    Pattern(
        id=1,
        short_description="Asks one focused question instead of guessing",
        key="ask_dont_assume",
        name="Ask, don't assume",
        conventional_principle="Be specific and detailed",
        rule=(
            "Meets: the response asks exactly one focused clarifying "
            "question, and does not also produce a complete deliverable in "
            "the same turn. Does not meet: the response guesses and "
            "produces a full deliverable without asking, OR it demands a "
            "complete detailed brief (multiple questions at once) before "
            "doing anything."
        ),
        report_flag=True,
        probes=[
            Probe(["help me write something for my boss"]),
            Probe(["can you help me with my presentation"]),
            Probe(["I need to respond to this email but I'm not sure what to say"]),
        ],
    ),
    Pattern(
        id=2,
        short_description="Presents 2-3 options instead of picking one path",
        key="offer_directions",
        name="Offer directions, not just outputs",
        conventional_principle="Iterate and refine",
        rule=(
            "Meets: the response presents two or three distinct, concrete "
            "options or directions for the user to choose between. Does not "
            "meet: it picks one approach and only elaborates that, or gives "
            "an undifferentiated single list with no real choice between "
            "distinct directions."
        ),
        probes=[
            Probe(["help me plan a birthday party for a friend"]),
            Probe(["I want to redesign my resume, where do I start"]),
            Probe(["give me ideas for a team offsite"]),
        ],
    ),
    Pattern(
        id=3,
        short_description="Remembers context without the user repeating it",
        key="set_once_reuse",
        name="Set once, reuse",
        conventional_principle="Provide context or a persona",
        rule=(
            "Meets: the second turn's response reflects the context/persona "
            "given in the first turn (tone, role, stated preference) without "
            "the user having to restate it. Does not meet: the second "
            "response ignores the earlier context or reverts to a generic "
            "register that could have been given to anyone."
        ),
        probes=[
            Probe([
                "For context: I'm a freelance graphic designer, and I prefer short, casual replies.",
                "What should I post on social media this week?",
            ]),
            Probe([
                "Quick context: I'm a nurse working night shifts, and I need answers I can skim fast.",
                "What's a good way to stay hydrated on a 12-hour shift?",
            ]),
            Probe([
                "For context: I'm new to cooking and get overwhelmed by long recipes.",
                "What's a good dinner I could make tonight?",
            ]),
        ],
    ),
    Pattern(
        id=4,
        short_description="Answers stay concise unless asked for more",
        key="short_by_default",
        name="Short by default, expand on request",
        conventional_principle="Define the output format",
        rule=(
            "Meets: the response is concise (roughly under 120 words, a provisional "
            "threshold pending validation against study data) and does not "
            "require the user to ask for a shorter version. Does not meet: "
            "the response is long (roughly over 250 words) and unprompted."
        ),
        probes=[
            Probe(["What's the capital of France, and a bit about its history?"]),
            Probe(["Explain how photosynthesis works."]),
            Probe(["What should I know before buying a used car?"]),
        ],
    ),
    Pattern(
        id=5,
        short_description="Gives one step at a time on multi-part tasks",
        key="one_step_at_a_time",
        name="One step at a time when stuck",
        conventional_principle="Step-by-step reasoning; delimiters or tags",
        rule=(
            "Meets: the response breaks the task into numbered steps and "
            "presents only the first step (or a small first chunk), "
            "inviting the user to continue. Does not meet: the response "
            "delivers the entire multi-step process in one uninterrupted "
            "block."
        ),
        probes=[
            Probe(["Walk me through setting up a budget spreadsheet."]),
            Probe(["Help me prepare for a job interview, start to finish."]),
            Probe(["Guide me through writing a cover letter."]),
        ],
    ),
    Pattern(
        id=6,
        short_description="Names a specific fix when something isn't working",
        key="name_the_recovery_move",
        name="Name the recovery move",
        conventional_principle="(not in standard guidance, the most-reported barrier)",
        rule=(
            "Meets: the response to the dissatisfaction signal names a "
            "specific next action, e.g. rephrase, try a simpler version, "
            "start over, show an example, rather than only apologizing and "
            "repeating a near-identical answer. Does not meet: it apologizes "
            "and repeats substantially the same content, with no named "
            "alternative action."
        ),
        report_flag=True,
        probes=[
            Probe(["Can you summarize the plot of a mystery novel for me?", "That's not what I meant."]),
            Probe(["Give me a workout plan for this week.", "This isn't really working for me."]),
            Probe(["Draft a short bio for my website.", "No, that's not right."]),
        ],
    ),
    Pattern(
        id=7,
        short_description="Honors a stated limit without being reminded",
        key="protect_lightly",
        name="Protect what matters, lightly",
        conventional_principle='Use positive instructions ("do X," not "don\'t X")',
        rule=(
            "Meets: the second response honors the constraint stated in the "
            "first turn without the user repeating it. Does not meet: the "
            "constraint is dropped, ignored, or the response asks the user "
            "to re-list it."
        ),
        probes=[
            Probe([
                "One thing: please don't change my writing voice when you edit anything for me.",
                "Can you tighten this paragraph up: 'I think that maybe we should consider possibly changing the approach.'",
            ]),
            Probe([
                "Please don't guess at facts. If you're not sure, say so.",
                "What year did the company I work for, Acme Textiles, IPO?",
            ]),
            Probe([
                "One limit: keep replies free of emoji, I find them distracting.",
                "Give me a fun reply congratulating a coworker on a promotion.",
            ]),
        ],
    ),
    Pattern(
        id=8,
        short_description="Gives short, single-focus answers on low-capacity days",
        key="low_capacity_mode",
        name="Low-capacity mode",
        conventional_principle="(from co-design: \"when I can barely think\")",
        rule=(
            "Meets: the response to the task request is short (roughly one "
            "to three sentences, a provisional threshold pending validation "
            "against study data), addresses one thing at a time, and does "
            "not add unprompted suggestions. Does not meet: the response "
            "reverts to a long, multi-part answer with unprompted extra "
            "suggestions."
        ),
        probes=[
            Probe([
                "I'm having a really hard time focusing today, can you keep things really simple and take it slow?",
                "What's a healthy breakfast I could make?",
            ]),
            Probe([
                "Low energy day, please keep it short and simple.",
                "How do I reset my email password?",
            ]),
            Probe([
                "I can barely think right now, so please go easy on the detail.",
                "What's a good first step to start organizing my closet?",
            ]),
        ],
    ),
]
