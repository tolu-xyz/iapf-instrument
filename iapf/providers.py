"""Provider adapters. Each provider implements complete(messages) -> str,
so the scoring engine never needs to know which API it's talking to.

Anthropic and OpenAI adapters use only the standard library (urllib). No
extra dependencies to install, which matters for an institution that just
wants to clone this and run it.
"""

import json
import os
import ssl
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import List, Dict

try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = ssl.create_default_context()


def _urlopen(req, timeout=60):
    return urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT)


def _retry_delay_seconds(http_error, default):
    """Free-tier APIs often report exactly how long to wait in the error
    body (e.g. Gemini's "retryDelay": "52s"). Use it when present instead
    of guessing."""
    try:
        body = json.loads(http_error.read().decode("utf-8"))
        for detail in body.get("error", {}).get("details", []):
            if "retryDelay" in detail:
                return float(detail["retryDelay"].rstrip("s")) + 1
    except Exception:
        pass
    return default


def _urlopen_with_retry(req, timeout=60, retries=5, base_delay=2.0):
    """Retries on 5xx (transient server-side errors) and 429 (rate limit)
    with backoff, using the server's own suggested wait time when it
    provides one. Does not retry on other 4xx: those are real problems
    (bad key, bad request) that won't fix themselves."""
    import time
    last_error = None
    for attempt in range(retries + 1):
        try:
            return _urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if (e.code < 500 and e.code != 429) or attempt == retries:
                raise
            last_error = e
            delay = _retry_delay_seconds(e, base_delay * (2 ** attempt))
            time.sleep(delay)
    raise last_error


class Provider(ABC):
    name: str

    @abstractmethod
    def complete(self, messages: List[Dict[str, str]]) -> str:
        """messages: [{"role": "user"|"assistant", "content": str}, ...]
        Returns the assistant's reply text for the final user turn."""
        raise NotImplementedError


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-4-5-20250929", api_key: str = None):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Set ANTHROPIC_API_KEY in your environment to use the "
                "anthropic provider."
            )

    def complete(self, messages: List[Dict[str, str]]) -> str:
        body = json.dumps({
            "model": self.model,
            "max_tokens": 1024,
            "messages": messages,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "content-type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with _urlopen_with_retry(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Anthropic API error {e.code}: {e.read().decode('utf-8')}")
        return "".join(block.get("text", "") for block in data.get("content", []))


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self, model: str = "gpt-4.1", api_key: str = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Set OPENAI_API_KEY in your environment to use the openai "
                "provider."
            )

    def complete(self, messages: List[Dict[str, str]]) -> str:
        body = json.dumps({
            "model": self.model,
            "messages": messages,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with _urlopen_with_retry(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"OpenAI API error {e.code}: {e.read().decode('utf-8')}")
        return data["choices"][0]["message"]["content"]


class GeminiProvider(Provider):
    name = "gemini"

    def __init__(self, model: str = "gemini-flash-latest", api_key: str = None):
        self.model = model
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Set GEMINI_API_KEY in your environment to use the gemini "
                "provider."
            )

    def complete(self, messages: List[Dict[str, str]]) -> str:
        contents = [
            {
                "role": "model" if m["role"] == "assistant" else "user",
                "parts": [{"text": m["content"]}],
            }
            for m in messages
        ]
        body = json.dumps({"contents": contents}).encode("utf-8")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        req = urllib.request.Request(
            url, data=body, headers={"content-type": "application/json"}, method="POST",
        )
        try:
            with _urlopen_with_retry(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Gemini API error {e.code}: {e.read().decode('utf-8')}")
        return data["candidates"][0]["content"]["parts"][0]["text"]


class MockProvider(Provider):
    """Deterministic, canned provider. No API key, no network. Exists so
    the instrument can be demoed and tested with zero setup. Half the
    scripted responses are written to pass their pattern's rule, half to
    fail it, so a demo run shows a realistic mixed conformance report
    rather than a suspiciously perfect one.
    """

    name = "mock"

    def __init__(self, model: str = None, api_key: str = None):
        pass  # accepts and ignores the same kwargs as real providers

    # Keyed by a substring of the *last* user turn, so both single- and
    # multi-turn cases resolve to a scripted reply.
    SCRIPT = {
        "help me write something for my boss": (
            "Sure, what's this for? A quick status update, a request, or "
            "something else?"
        ),
        "help me with my presentation": (
            "Here's a full presentation outline: 1) Title slide 2) Agenda "
            "3) Problem statement 4) Data 5) Recommendation 6) Next steps 7) "
            "Q&A. Let me know if you'd like slide-by-slide content for each."
        ),
        "respond to this email": "What's the email about, and who's it from?",
        "plan a birthday party": (
            "A few directions: (1) a small dinner with close friends, (2) a "
            "themed party with games and decorations, or (3) a low-key "
            "afternoon hangout with cake. Which fits best?"
        ),
        "redesign my resume": (
            "Start by choosing a format that fits your field, then list your "
            "most recent role, then work backward, then tailor your summary "
            "line, then check for consistent formatting, then have someone "
            "review it, then save it as a PDF, then tailor it per "
            "application, then double check contact details, then proofread "
            "once more."
        ),
        "ideas for a team offsite": (
            "A few options: a half-day workshop with a facilitator, a "
            "casual outdoor activity day, or a hybrid mix of planning "
            "sessions and team bonding. Want details on any of these?"
        ),
        "what should i post on social media this week": (
            "Quick take, casual: post a behind-the-scenes shot of current "
            "work, a client shoutout, and one design tip. Keep captions "
            "short."
        ),
        "stay hydrated on a 12-hour shift": (
            "Here is a comprehensive guide to hydration for shift workers, "
            "covering electrolyte balance, timing strategies, common "
            "mistakes, recommended intake by body weight, the effects of "
            "caffeine, and long-term hydration habits for people who work "
            "irregular hours."
        ),
        "good dinner i could make tonight": (
            "Easy one: pasta with olive oil, garlic, and whatever veg you "
            "have. Fifteen minutes, one pan."
        ),
        "capital of france": (
            "Paris. It's been France's capital since the late 10th century "
            "and is the country's political and cultural center."
        ),
        "photosynthesis": (
            "Photosynthesis is the process by which plants convert light "
            "energy into chemical energy. It occurs in the chloroplasts, "
            "primarily using chlorophyll to absorb sunlight. The process has "
            "two main stages: the light-dependent reactions, which occur in "
            "the thylakoid membrane and produce ATP and NADPH, and the "
            "Calvin cycle, which occurs in the stroma and uses that ATP and "
            "NADPH to fix carbon dioxide into glucose. Oxygen is released as "
            "a byproduct of the light-dependent reactions. The overall "
            "chemical equation is 6CO2 + 6H2O + light energy -> C6H12O6 + "
            "6O2. This process is fundamental to almost all life on Earth, "
            "as it forms the base of most food chains and produces the "
            "oxygen most organisms depend on."
        ),
        "buying a used car": (
            "Check the vehicle history report, get an independent "
            "mechanic's inspection, and compare the asking price to market "
            "value before you commit."
        ),
        "setting up a budget spreadsheet": (
            "Step 1: list all your income sources in one column. Once you've "
            "got that down, let me know and we'll move to step 2, listing "
            "your fixed monthly expenses."
        ),
        "prepare for a job interview": (
            "Here's the full process: research the company, review the job "
            "description, prepare answers to common questions, prepare "
            "questions to ask them, choose your outfit, plan your route, "
            "print copies of your resume, practice out loud, get a good "
            "night's sleep, arrive early, follow up with a thank-you note."
        ),
        "writing a cover letter": (
            "First step: open with the specific role and company name and "
            "one sentence on why you're interested. Try that and send it "
            "back to me when you're ready for the next part."
        ),
        "summarize the plot of a mystery novel": "Sure, which novel?",
        "that's not what i meant": (
            "I apologize for the confusion. Here's another version of the "
            "same summary, restated slightly differently."
        ),
        "give me a workout plan for this week": (
            "Monday: cardio. Tuesday: upper body. Wednesday: rest. Thursday: "
            "lower body. Friday: cardio. Weekend: rest or light activity."
        ),
        "this isn't really working for me": (
            "No problem, want me to make it shorter, focus on just one "
            "muscle group, or start over with your actual schedule in mind?"
        ),
        "draft a short bio for my website": (
            "Jane Doe is a passionate professional dedicated to excellence "
            "in her field, bringing years of experience and a commitment to "
            "quality in everything she does."
        ),
        "no, that's not right": (
            "Sorry about that. Here's a bio in a similar style, adjusted "
            "slightly: Jane Doe is a dedicated expert bringing years of "
            "experience and a commitment to quality to every project."
        ),
        "tighten this paragraph up": (
            "Consider changing the approach."
        ),
        "acme textiles": (
            "I don't have reliable information on Acme Textiles' IPO date. "
            "I'd rather not guess. Can you check their investor relations "
            "page, or let me know if you have a source?"
        ),
        "congratulating a coworker on a promotion": (
            "Huge congrats on the promotion! 🎉🎉 You totally earned this! 🥳"
        ),
        "healthy breakfast": (
            "Try oatmeal with fruit. Simple and filling."
        ),
        "reset my email password": (
            "Go to your email provider's login page and click 'forgot "
            "password.'"
        ),
        "start organizing my closet": (
            "Here's a full closet organization system: start by removing "
            "everything, then sort into keep/donate/toss piles, then "
            "categorize by type, then by color, then invest in matching "
            "hangers, then add labeled bins for accessories, then organize "
            "shoes by frequency of use, then reassess seasonally, then set a "
            "recurring decluttering reminder, then donate the discard pile "
            "within a week."
        ),
    }

    def complete(self, messages: List[Dict[str, str]]) -> str:
        last_user = messages[-1]["content"].lower()
        for key, reply in self.SCRIPT.items():
            if key in last_user:
                return reply
        return "I'm not sure how to respond to that."


PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "mock": MockProvider,
}


def get_provider(name: str, **kwargs) -> Provider:
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider '{name}'. Choices: {list(PROVIDERS)}")
    return PROVIDERS[name](**kwargs)
