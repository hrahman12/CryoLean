"""AI layer (untrusted helper; never a verdict).

* Matching: maps a natural-language description onto the CLOSED set of
  registered experiment profiles.  Offline lexical matcher by default; Claude
  (closed-set ranking) when CRYOLEAN_AI_PROVIDER=claude.  Ids outside the
  catalog are discarded.
* Research assistance: ``draft_candidate`` asks Claude to structure research
  text into a candidate profile; the draft goes through the same validation
  gate and is stored as an UNTRUSTED candidate.  It is never promoted
  automatically.
* Explanations reuse the Lean-generated sentences.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter

from . import config
from .catalog import Catalog

SYNONYMS = {
    "electricity": ["electrical", "resistance", "transport"], "conduct": ["electrical", "resistance"],
    "conductivity": ["electrical", "resistance"], "resistivity": ["resistance"], "current": ["electrical"],
    "cold": ["low", "temperature", "cryogenic"], "cool": ["cooling", "temperature"], "cooling": ["temperature", "cold"],
    "freeze": ["frozen", "cryo"], "freezing": ["frozen", "cryo"], "frozen": ["cryo", "cryosection"],
    "slice": ["cut", "section", "sectioning"], "cut": ["section", "sectioning"], "section": ["sectioning"],
    "tissue": ["biological", "sample"], "microscope": ["examine", "microscopy", "optical"], "look": ["examine", "observe"],
    "watch": ["observe"], "light": ["optical", "spectroscopy", "raman", "photoluminescence"], "laser": ["optical", "raman"],
    "spectrum": ["spectroscopy"], "spectra": ["spectroscopy"], "glow": ["photoluminescence", "optical"],
    "magnet": ["magnetic", "field"], "magnetism": ["magnetic", "magnetization", "magnetometry"], "field": ["magnetic"],
    "tesla": ["magnetic", "field"], "magnetization": ["magnetometry", "magnetic"], "hysteresis": ["magnetometry", "magnetic"],
    "qubit": ["quantum", "superconducting"], "qubits": ["qubit", "quantum"], "quantum": ["qubit"],
    "wiring": ["wiring", "lines", "coax"], "cables": ["wiring", "coax", "lines"], "heat": ["temperature", "thermal", "heat"],
    "melting": ["phase", "transition", "melting"], "crystallization": ["phase", "crystallization"], "crystal": ["crystallization"],
    "change": ["changes", "transition"], "changes": ["transition"], "phase": ["transition"],
    "millikelvin": ["dilution", "quantum"], "vitrified": ["frozen", "cryo"], "chip": ["device", "qubit"],
    "material": ["materials"], "semiconductor": ["device", "transistor", "probe"], "transistor": ["device", "semiconductor"],
    "probe": ["probe", "station"], "wafer": ["semiconductor", "device"],
}
STOP = {"i", "a", "an", "the", "to", "of", "in", "on", "at", "and", "or", "it", "its", "my", "want", "would", "like", "need",
        "how", "what", "when", "is", "are", "be", "do", "does", "with", "for", "as", "this", "that", "while", "through",
        "we", "our", "can", "using", "use", "sample", "some", "test", "measure", "check"}


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
    for r in ex.get("requirements", []):
        parts += [k.replace(".", " ").replace("_", " ") for k in (r.get("keys") or [r.get("key", "")])]
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
            scored.append((num / den if den else 0.0, eid))
        scored.sort(reverse=True)
        out = []
        for score, eid in scored[:top_k]:
            if score <= 0:
                continue
            ex = self.catalog.experiments[eid]
            out.append({"experiment_id": eid, "plain_name": ex.get("plain_name"), "name": ex.get("name"), "industry": ex.get("industry"),
                        "confidence": round(min(1.0, score), 3), "reason": "word overlap with the prepared profile", "provider": self.name})
        return out


class ClaudeMatcher:
    """Closed-set ranking with Claude. The model sees only ids and names and cannot add profiles."""
    name = "claude"

    def __init__(self, catalog: Catalog):
        import anthropic  # optional dependency
        self.catalog = catalog
        self.client = anthropic.Anthropic()

    def _ask(self, prompt: str) -> str:
        resp = self.client.beta.messages.create(
            model=config.claude_model(), max_tokens=4000,
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": prompt}])
        if resp.stop_reason == "refusal":
            return ""
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    def match(self, text: str, top_k: int = 3) -> list[dict]:
        menu = [{"experiment_id": e, "plain_name": x.get("plain_name"), "name": x.get("name"), "industry": x.get("industry")}
                for e, x in self.catalog.experiments.items()]
        raw = self._ask("You match a user's description of a cryogenic experiment to prepared experiment profiles. "
                        "Choose ONLY from the ids in the menu. Never invent ids, requirements or specifications. "
                        'Answer with JSON only: {"matches": [{"experiment_id": str, "confidence": 0-1, "reason": str}]} '
                        f"with at most {top_k} entries, best first; an empty list if nothing fits.\n\n"
                        f"MENU:\n{json.dumps(menu, ensure_ascii=False)}\n\nUSER REQUEST:\n{text}")
        try:
            data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        except ValueError:
            return []
        out = []
        for m in data.get("matches", [])[:top_k]:
            eid = m.get("experiment_id")
            if eid not in self.catalog.experiments:
                continue   # closed set: anything invented is discarded
            ex = self.catalog.experiments[eid]
            out.append({"experiment_id": eid, "plain_name": ex.get("plain_name"), "name": ex.get("name"), "industry": ex.get("industry"),
                        "confidence": float(max(0.0, min(1.0, m.get("confidence", 0)))), "reason": str(m.get("reason", ""))[:300],
                        "provider": self.name})
        return out


def build_matcher(catalog: Catalog):
    if config.ai_provider() == "claude":
        try:
            return ClaudeMatcher(catalog)
        except Exception:  # noqa: BLE001 - fall back to the offline matcher
            return LexicalMatcher(catalog)
    return LexicalMatcher(catalog)


def match(catalog: Catalog, text: str, top_k: int = 3, matcher=None) -> dict:
    m = matcher or build_matcher(catalog)
    matches = m.match(text, top_k)
    best = matches[0]["confidence"] if matches else 0.0
    threshold = 0.12 if m.name == "lexical" else 0.5
    return {"query": text, "provider": m.name, "matches": matches, "needs_confirmation": True,
            "no_good_match": best < threshold,
            "advice": ("Confirm the suggested experiment and review its requirements before checking." if best >= threshold else
                       "No prepared experiment matches well. Start a research request; until a sourced profile is validated "
                       "and approved the answer is NEED_MORE_INFORMATION.")}


def draft_candidate(catalog: Catalog, description: str, research_text: str) -> dict:
    """Ask Claude to STRUCTURE supplied research text into a candidate profile (never trusted).
    Returns {"ok": bool, "draft": dict|None, "error": str|None}."""
    if config.ai_provider() != "claude":
        return {"ok": False, "draft": None,
                "error": "AI drafting needs CRYOLEAN_AI_PROVIDER=claude and API credentials; submit a candidate manually instead."}
    m = ClaudeMatcher(catalog)
    vocab = {k: {"shape": v["shape"], "unit": v.get("unit")} for k, v in catalog.vocabulary.items()}
    raw = m._ask("Structure the following research text into a CryoLean experiment candidate JSON. Use ONLY values that appear "
                 "verbatim in the text and quote them in 'quote' fields; leave anything not stated out and list it in "
                 "'missing_information'. Use only these capability keys and canonical units: "
                 f"{json.dumps(vocab)}\n\nEXPERIMENT: {description}\n\nRESEARCH TEXT:\n{research_text}\n\n"
                 'Answer JSON only: {"document": {...experiment profile...}, "evidence": [...records...]}')
    try:
        data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except ValueError:
        return {"ok": False, "draft": None, "error": "the model did not return JSON"}
    return {"ok": True, "draft": data, "error": None,
            "note": "AI draft — it must pass validation and human review before it can be used for verification."}
