"""AI experiment matching.

The AI's job is to understand what the user wants and map it onto a *prepared*
experiment profile.  It never writes requirements and never produces a verdict.

Two providers:
* ``lexical`` (default, offline, deterministic): token overlap with a small
  domain-neutral synonym table, scored against each profile's text.
* ``claude`` (optional): asks Claude to rank the *closed* list of profile ids.
  Any id outside the catalog is discarded.  Requires ``ANTHROPIC_API_KEY`` and
  ``CRYOLEAN_AI_PROVIDER=claude``.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter

from . import config
from .catalog import Catalog

SYNONYMS = {
    "electricity": ["electrical", "resistance", "transport", "conduct"],
    "conduct": ["electrical", "resistance"],
    "conductivity": ["electrical", "resistance"],
    "resistivity": ["resistance"],
    "cold": ["low", "temperature", "cryogenic"],
    "cool": ["cooling", "temperature"],
    "cooling": ["temperature"],
    "freeze": ["frozen", "cryo"],
    "freezing": ["frozen", "cryo"],
    "frozen": ["cryo", "cryosection"],
    "slice": ["cut", "section", "sectioning"],
    "cut": ["section", "sectioning"],
    "section": ["sectioning"],
    "tissue": ["biological", "sample"],
    "microscope": ["examine", "microscopy", "optical"],
    "look": ["examine", "observe"],
    "watch": ["observe"],
    "light": ["optical", "spectroscopy", "raman", "photoluminescence"],
    "laser": ["optical", "raman"],
    "spectrum": ["spectroscopy"],
    "spectra": ["spectroscopy"],
    "glow": ["photoluminescence", "optical"],
    "magnet": ["magnetic", "field"],
    "magnetism": ["magnetic", "field"],
    "field": ["magnetic"],
    "tesla": ["magnetic", "field"],
    "qubit": ["quantum", "superconducting"],
    "quantum": ["qubit"],
    "millikelvin": ["dilution", "base", "quantum"],
    "mk": ["millikelvin", "dilution"],
    "change": ["changes", "dependent", "varies"],
    "changes": ["dependent"],
    "heat": ["temperature", "thermal"],
    "warm": ["temperature"],
    "vitrified": ["frozen", "cryo"],
    "chip": ["device", "qubit"],
    "material": ["materials"],
    "sample": [],
}
STOP = {"i", "a", "an", "the", "to", "of", "in", "on", "at", "and", "or", "it", "its", "my", "want", "would", "like",
        "need", "how", "what", "when", "is", "are", "be", "do", "does", "with", "for", "as", "this", "that", "while",
        "through", "when", "its", "we", "our", "can", "using", "use"}


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP and len(t) > 1]


def expand(toks: list[str]) -> Counter:
    c: Counter = Counter()
    for t in toks:
        c[t] += 1.0
        for s in SYNONYMS.get(t, []):
            c[s] += 0.6
        if t.endswith("s") and len(t) > 3:
            c[t[:-1]] += 0.8
    return c


def profile_text(ex: dict) -> str:
    parts = [ex.get("plain_name", ""), ex.get("name", ""), ex.get("description", ""), ex.get("industry", "").replace("_", " ")]
    parts += ex.get("keywords", [])
    parts += [r.get("key", "").replace(".", " ").replace("_", " ") for r in ex.get("requirements", [])]
    return " ".join(parts)


class LexicalMatcher:
    name = "lexical"

    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self.docs = {eid: expand(tokens(profile_text(ex))) for eid, ex in catalog.experiments.items()}
        df: Counter = Counter()
        for c in self.docs.values():
            for t in c:
                df[t] += 1
        n = max(1, len(self.docs))
        self.idf = {t: 1.0 + math.log((n + 1) / (d + 1)) for t, d in df.items()}

    def match(self, text: str, top_k: int = 3) -> list[dict]:
        q = expand(tokens(text))
        if not q:
            return []
        scored = []
        for eid, d in self.docs.items():
            num = sum(q[t] * min(d[t], 2.0) * self.idf.get(t, 1.0) for t in q if t in d)
            den = math.sqrt(sum((q[t] * self.idf.get(t, 1.0)) ** 2 for t in q)) * math.sqrt(sum((min(v, 2.0) * self.idf.get(t, 1.0)) ** 2 for t, v in d.items()))
            score = num / den if den else 0.0
            scored.append((score, eid))
        scored.sort(reverse=True)
        out = []
        for score, eid in scored[:top_k]:
            if score <= 0:
                continue
            ex = self.catalog.experiments[eid]
            out.append({"experiment_id": eid, "plain_name": ex.get("plain_name"), "name": ex.get("name"),
                        "industry": ex.get("industry"), "confidence": round(min(1.0, score), 3),
                        "reason": "lexical overlap with the prepared experiment profile", "provider": self.name})
        return out


class ClaudeMatcher:
    """Closed-set ranking by Claude. The model sees only profile ids and names; it cannot add profiles."""
    name = "claude"

    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        import anthropic  # imported lazily so the default provider needs no SDK
        self.client = anthropic.Anthropic()

    def match(self, text: str, top_k: int = 3) -> list[dict]:
        menu = [{"experiment_id": e, "plain_name": x.get("plain_name"), "name": x.get("name"), "industry": x.get("industry")}
                for e, x in self.catalog.experiments.items()]
        prompt = (
            "You match a user's description of a cryogenic experiment to prepared experiment profiles. "
            "Choose ONLY from the ids in the menu. Never invent ids, requirements, or equipment specifications. "
            "Answer with JSON only: {\"matches\": [{\"experiment_id\": str, \"confidence\": 0-1, \"reason\": str}]} "
            f"with at most {top_k} entries, best first; return an empty list if nothing fits.\n\n"
            f"MENU:\n{json.dumps(menu, ensure_ascii=False)}\n\nUSER REQUEST:\n{text}"
        )
        resp = self.client.beta.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=2000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": prompt}],
        )
        if resp.stop_reason == "refusal":
            return []
        raw = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        try:
            data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        except (ValueError, json.JSONDecodeError):
            return []
        out = []
        for m in data.get("matches", [])[:top_k]:
            eid = m.get("experiment_id")
            if eid not in self.catalog.experiments:
                continue  # closed set: discard anything the model made up
            ex = self.catalog.experiments[eid]
            out.append({"experiment_id": eid, "plain_name": ex.get("plain_name"), "name": ex.get("name"),
                        "industry": ex.get("industry"), "confidence": float(max(0.0, min(1.0, m.get("confidence", 0)))),
                        "reason": str(m.get("reason", ""))[:300], "provider": self.name})
        return out


def build_matcher(catalog: Catalog):
    if config.AI_PROVIDER == "claude":
        try:
            return ClaudeMatcher(catalog)
        except Exception:
            return LexicalMatcher(catalog)
    return LexicalMatcher(catalog)


def match_request(catalog: Catalog, text: str, top_k: int = 3, matcher=None) -> dict:
    matcher = matcher or build_matcher(catalog)
    matches = matcher.match(text, top_k=top_k)
    best = matches[0]["confidence"] if matches else 0.0
    # Lexical cosine scores for a correct top match sit around 0.2-0.3 on this catalog; below 0.12 the
    # best profile shares only generic words with the request.
    threshold = 0.12 if matcher.name == "lexical" else 0.5
    return {
        "query": text,
        "provider": matcher.name,
        "matches": matches,
        "needs_confirmation": True,
        "no_good_match": best < threshold,
        "advice": ("Confirm the suggested experiment and review its requirements before checking."
                   if best >= threshold else
                   "No prepared experiment matches well. You can register a research request for this experiment; "
                   "until a sourced profile exists the answer is NEED_MORE_INFORMATION."),
    }
