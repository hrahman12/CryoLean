"""User sessions: one experiment, user-reviewed requirements, one selected
configuration, and a result that is invalidated whenever any of those change.

Rules enforced here (the Lean rule `confirmed = false ⇒ never ACCEPT` backs them):
* a session starts unconfirmed; the user must confirm after reviewing;
* editing a requirement resets confirmation and invalidates the result;
* switching cryostat keeps the experiment, clears the result;
* the `mandatory` flag of a prepared requirement cannot be changed through the API.
"""
from __future__ import annotations

import copy
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Callable

from .catalog import Catalog, CatalogError
from . import verifier, lean_runner
from .modifications import apply_overrides, describe_overrides


class SessionError(Exception):
    pass


class StaleResult(SessionError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Session:
    def __init__(self, catalog: Catalog, experiment_id: str):
        ex = catalog.get_experiment(experiment_id)
        self.id = uuid.uuid4().hex[:12]
        self.created_at = _now()
        self.experiment_profile_id = experiment_id
        self.industry = ex.get("industry")
        self.experiment = catalog.lean_experiment(ex)
        self.experiment["confirmed"] = False          # user must review first
        self.original_requirements = copy.deepcopy(self.experiment["requirements"])
        self.configuration_id: str | None = None
        self.overrides: list[dict] = []
        self.result: dict | None = None
        self.events: list[dict] = [{"at": self.created_at, "event": "created", "experiment_id": experiment_id}]

    # ---------------------------------------------------------------- state token
    def state_token(self, catalog: Catalog) -> str:
        h = hashlib.sha256()
        h.update(catalog.version.encode())
        h.update(json.dumps(self.experiment, sort_keys=True).encode())
        h.update((self.configuration_id or "").encode())
        h.update(json.dumps(self.overrides, sort_keys=True).encode())
        return h.hexdigest()[:32]

    def _invalidate(self, reason: str) -> None:
        if self.result is not None:
            self.events.append({"at": _now(), "event": "result_invalidated", "reason": reason})
        self.result = None

    # ---------------------------------------------------------------- mutations
    def edit_requirements(self, edits: list[dict]) -> None:
        reqs = self.experiment["requirements"]
        for e in edits:
            key = e.get("key")
            if not key:
                raise SessionError("edit needs a key")
            existing = next((r for r in reqs if r["key"] == key), None)
            if e.get("remove"):
                if existing is None:
                    raise SessionError(f"no requirement '{key}' to remove")
                if existing["mandatory"]:
                    raise SessionError(f"'{key}' is a mandatory requirement of the prepared experiment and cannot be removed; create a custom experiment instead")
                reqs.remove(existing)
                continue
            if "mandatory" in e and existing is not None and bool(e["mandatory"]) != existing["mandatory"]:
                raise SessionError("the mandatory flag of a prepared requirement cannot be changed")
            if existing is None:
                if "constraint" not in e:
                    raise SessionError(f"new requirement '{key}' needs a constraint")
                reqs.append({
                    "key": key, "constraint": e["constraint"], "mandatory": bool(e.get("mandatory", True)),
                    "origin": "user_entered", "rationale": e.get("rationale", "Entered by the user."), "evidence_ids": [],
                })
            else:
                if "constraint" in e:
                    existing["constraint"] = e["constraint"]
                    existing["origin"] = "user_entered"
                    existing["rationale"] = e.get("rationale", f"Edited by the user (was: {existing.get('rationale','')})")
                    existing["evidence_ids"] = []
        self.experiment["confirmed"] = False
        self.events.append({"at": _now(), "event": "requirements_edited", "keys": [e.get("key") for e in edits]})
        self._invalidate("requirements edited")

    def confirm(self) -> None:
        self.experiment["confirmed"] = True
        self.events.append({"at": _now(), "event": "requirements_confirmed"})
        self._invalidate("requirements re-confirmed")

    def select_configuration(self, catalog: Catalog, configuration_id: str) -> None:
        catalog.get_configuration(configuration_id)  # raises if unknown
        previous = self.configuration_id
        self.configuration_id = configuration_id
        cleared = bool(self.overrides) and previous != configuration_id
        if cleared:
            self.overrides = []   # instrument overrides describe one physical instrument
        self.events.append({"at": _now(), "event": "configuration_selected", "from": previous, "to": configuration_id,
                            "instrument_overrides_cleared": cleared})
        self._invalidate("configuration switched")

    def set_overrides(self, catalog: Catalog, overrides: list[dict]) -> None:
        if not self.configuration_id:
            raise SessionError("select a configuration before describing modifications")
        cfg = catalog.lean_configuration(catalog.get_configuration(self.configuration_id))
        apply_overrides(catalog, cfg, overrides)   # validates; raises on bad input
        self.overrides = copy.deepcopy(overrides)
        self.events.append({"at": _now(), "event": "instrument_overrides_set", "keys": [o.get("key") for o in overrides]})
        self._invalidate("instrument overrides changed")

    def verify(self, catalog: Catalog, run: Callable = lean_runner.run_check) -> dict:
        if not self.configuration_id:
            raise SessionError("select a configuration first")
        cfg = catalog.lean_configuration(catalog.get_configuration(self.configuration_id))
        cfg = apply_overrides(catalog, cfg, self.overrides)
        extra = {"session_id": self.id, "state_token": self.state_token(catalog)}
        if self.overrides:
            extra["instrument_overrides"] = describe_overrides(self.overrides)
        res = verifier.verify(catalog, copy.deepcopy(self.experiment), cfg, run=run, extra=extra)
        self.result = res
        self.events.append({"at": _now(), "event": "verified", "verdict": res["verdict"], "configuration_id": self.configuration_id})
        return res

    def current_result(self, catalog: Catalog) -> dict:
        if self.result is None:
            raise StaleResult("no current result: the setup changed or has not been checked yet")
        if self.result.get("state_token") != self.state_token(catalog):
            self._invalidate("state token mismatch")
            raise StaleResult("the stored result no longer matches the current experiment, configuration or catalog version")
        return self.result

    def summary(self, catalog: Catalog) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "experiment_profile_id": self.experiment_profile_id,
            "industry": self.industry,
            "experiment": self.experiment,
            "confirmed": self.experiment["confirmed"],
            "configuration_id": self.configuration_id,
            "instrument_overrides": describe_overrides(self.overrides),
            "has_valid_result": self.result is not None and self.result.get("state_token") == self.state_token(catalog),
            "state_token": self.state_token(catalog),
            "events": self.events,
        }


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create(self, catalog: Catalog, experiment_id: str) -> Session:
        s = Session(catalog, experiment_id)
        self._sessions[s.id] = s
        return s

    def get(self, session_id: str) -> Session:
        try:
            return self._sessions[session_id]
        except KeyError:
            raise SessionError(f"unknown session '{session_id}'")
