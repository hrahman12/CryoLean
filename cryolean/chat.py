"""Website chat: Claude writes the plain-English answer; Lanyon builds a physics model only when asked.

Claude explains the verdicts Lean already decided and never changes them. Standard library + `anthropic` only, so the
same file runs inside `python -m cryolean serve` and as a standalone Vercel function (api/lanyon.py imports it).
Needs ANTHROPIC_API_KEY (or another credential the Anthropic SDK resolves).
"""
from __future__ import annotations

import os

MODEL = os.environ.get("CRYOLEAN_CHAT_MODEL", "claude-opus-5-5")
MODEL_WORDS = ("model", "simulate", "simulation", "lanyon")

SYSTEM = (
    "You are the CryoLean assistant on a website that checks whether a cryostat can run an experiment. "
    "A Lean 4 checker has already decided every verdict in the FACTS; never change, soften or second-guess them, and "
    "never invent machine specifications that are not in the FACTS. If the FACTS do not settle a question, say what "
    "is missing. Answer in plain English for a non-expert, in under 150 words, without markdown headings."
)


class ChatUnavailable(RuntimeError):
    pass


def wants_model(question: str) -> bool:
    q = question.lower()
    return any(w in q for w in MODEL_WORDS)


def answer(question: str, facts: str) -> str:
    try:
        import anthropic
    except ImportError as e:
        raise ChatUnavailable("the anthropic package is not installed (pip install anthropic)") from e
    try:
        client = anthropic.Anthropic()
        r = client.beta.messages.create(
            model=MODEL, max_tokens=2000, system=SYSTEM,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            messages=[{"role": "user", "content": f"FACTS (from Lean):\n{facts}\n\nQUESTION: {question}"}],
        )
    except anthropic.AuthenticationError as e:
        raise ChatUnavailable("no valid Anthropic API key on this server (set ANTHROPIC_API_KEY)") from e
    except anthropic.RateLimitError as e:
        raise ChatUnavailable("Claude is rate limited right now; try again in a minute") from e
    except anthropic.APIConnectionError as e:
        raise ChatUnavailable("could not reach the Claude API") from e
    except anthropic.APIStatusError as e:
        raise ChatUnavailable(f"Claude API error {e.status_code}") from e
    except TypeError as e:  # no credentials resolved at all
        raise ChatUnavailable("no Anthropic API key on this server (set ANTHROPIC_API_KEY)") from e
    if r.stop_reason == "refusal":
        return "Claude declined to answer that question."
    return "".join(b.text for b in r.content if b.type == "text").strip() or "Claude returned no text."
