"""Local desktop bridge for the Antigravity frontend (no web server required).

Usage with PyWebView (Windows):

    import webview
    from cryolean.bridge import CryoLeanAPI
    webview.create_window("CryoLean", "frontend/index.html", js_api=CryoLeanAPI())
    webview.start()

JavaScript then calls, e.g.:

    const r = await window.pywebview.api.check_compatibility("mat_magnetoresistance_10T", "qd_dynacool_14T_eto_vsm_hc", null, null, true);
    if (r.ok) show(r.data.verdict, r.data.user_message, r.data.checks, r.data.suggestions);

Every method returns a JSON-compatible envelope:
    {"ok": true,  "data": ...}
    {"ok": false, "error": {"code": "...", "message": "...", "verdict": null}}
No method ever returns a verdict that did not come from the Lean checker.
"""
from __future__ import annotations

import copy
import functools
import json
import traceback
import uuid

from . import ai, coverage, db, lean_runner, modifications, research, serialize, verifier
from .catalog import Catalog, CatalogError
from .edits import EditError
from .modifications import ModificationError
from .research import ResearchError
from .serialize import SerializationError
from .units import UnitError


def _ok(data):
    return {"ok": True, "data": data}


def _err(code: str, message: str):
    return {"ok": False, "error": {"code": code, "message": message, "verdict": None}}


def _api(fn):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return _ok(fn(self, *args, **kwargs))
        except lean_runner.LeanUnavailable as e:
            return _err("lean_unavailable", f"The Lean checker is unavailable; no verdict can be produced. {e}")
        except lean_runner.LeanDecodeError as e:
            return _err("lean_rejected_input", str(e))
        except CatalogError as e:
            return _err("not_found", str(e))
        except (EditError, ModificationError) as e:
            return _err("edit_refused", str(e))
        except ResearchError as e:
            return _err("research_refused", str(e))
        except (UnitError, SerializationError, ValueError, TypeError, KeyError) as e:
            return _err("invalid_input", f"{type(e).__name__}: {e}")
        except StaleResult as e:
            return _err("stale_result", str(e))
        except Exception as e:  # noqa: BLE001 - never crash the frontend
            return _err("internal_error", f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}")
    return wrapper


class StaleResult(RuntimeError):
    pass


def _parse(x):
    """Accept JSON strings from JavaScript as well as Python objects."""
    if isinstance(x, str):
        s = x.strip()
        if s.startswith("{") or s.startswith("["):
            return json.loads(s)
    return x


class CryoLeanAPI:
    """The callable interface for the Antigravity desktop frontend."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db.ensure_database()
        self._catalog = Catalog(db_path)
        self._sessions: dict[str, dict] = {}

    # ------------------------------------------------------------------ industries
    @_api
    def list_industries(self, query: str | None = None):
        """All industries (standard list + registered + any used by an experiment), with research status."""
        inds = sorted(self._catalog.industries.values(), key=lambda i: i["id"])
        if query:
            q = query.lower()
            inds = [i for i in inds if q in i["id"] or q in (i.get("name") or "").lower() or q in (i.get("description") or "").lower()]
        return {"industries": inds, "count": len(inds),
                "note": "Industries are labels; any industry can be registered. 'researched' means at least one validated profile exists."}

    @_api
    def register_industry(self, name: str, description: str = "", industry_id: str | None = None):
        """Register a new (custom) industry. It gets no special verification logic."""
        return self._catalog.register_industry(name, description, industry_id)

    # ------------------------------------------------------------------ experiments
    @_api
    def list_experiments(self, industry: str | None = None):
        exps = [self._catalog.public(e) for e in self._catalog.experiments.values() if not industry or e.get("industry") == industry]
        return {"experiments": [{k: e.get(k) for k in ("id", "plain_name", "name", "industry", "description", "confirmed")} for e in exps],
                "count": len(exps)}

    @_api
    def get_experiment_requirements(self, experiment_id: str):
        """Full prepared profile: requirements, parameters, coupled constraints, sources, missing information."""
        ex = self._catalog.public(self._catalog.get_experiment(experiment_id))
        ex["evidence"] = self._catalog.evidence_for(sorted({i for r in ex["requirements"] for i in r.get("evidence_ids", [])}
                                                          | {i for p in ex.get("params", []) for i in p.get("evidence_ids", [])}))
        ex["coupled_models"] = [self._catalog.coupled_models.get(c["model"]) for c in ex.get("coupled", [])]
        return ex

    @_api
    def match_experiment(self, text: str, top_k: int = 3):
        """AI: map a natural-language description onto prepared profiles (closed set). The user must confirm."""
        return ai.match(self._catalog, text, top_k)

    @_api
    def register_experiment(self, document, evidence=None, submitted_by: str = "user", request_id: str | None = None):
        """Submit a new experiment profile. It is validated and stored as an UNTRUSTED candidate;
        it can be verified only after `approve_candidate` by a named reviewer."""
        return research.submit_candidate(self._catalog, "experiment", _parse(document), _parse(evidence) or [], submitted_by, request_id)

    @_api
    def register_equipment(self, document, evidence=None, submitted_by: str = "user", request_id: str | None = None):
        """Submit new equipment (with configurations). Stored as an UNTRUSTED candidate until approved."""
        return research.submit_candidate(self._catalog, "equipment", _parse(document), _parse(evidence) or [], submitted_by, request_id)

    @_api
    def approve_candidate(self, candidate_id: str, reviewed_by: str):
        """Promote a validated candidate into the trusted catalog (requires a reviewer name)."""
        return research.promote(self._catalog, candidate_id, reviewed_by)

    @_api
    def list_candidates(self):
        return {"candidates": research.list_candidates(self._catalog)}

    # ------------------------------------------------------------------ equipment
    @_api
    def list_equipment(self, manufacturer: str | None = None, family: str | None = None):
        out = []
        for e in self._catalog.equipment.values():
            if manufacturer and manufacturer.lower() not in (e.get("manufacturer") or "").lower():
                continue
            if family and family.lower() not in (e.get("family") or "").lower():
                continue
            out.append({"id": e["id"], "manufacturer": e.get("manufacturer"), "model": e.get("model"), "family": e.get("family"),
                        "description": e.get("description"),
                        "configurations": [{"id": c["id"], "name": c.get("name")} for c in e.get("configurations", [])]})
        return {"equipment": out, "count": len(out)}

    @_api
    def get_equipment_details(self, equipment_or_configuration_id: str):
        """Equipment (all configurations) or one configuration, with evidence per capability, UNKNOWNs and modifications."""
        cat = self._catalog
        if equipment_or_configuration_id in cat.configurations:
            cfgs = [cat.configurations[equipment_or_configuration_id]]
            eq = cat.equipment[cfgs[0]["equipment_id"]]
        else:
            eq = cat.get_equipment(equipment_or_configuration_id)
            cfgs = eq.get("configurations", [])
        out = {k: v for k, v in cat.public(eq).items() if k != "configurations"}
        out["configurations"] = []
        for c in cfgs:
            pc = cat.public(c)
            for cap in pc["capabilities"]:
                cap["evidence"] = cat.evidence_for(cap.get("evidence_ids", []))
                cap["display"] = _display_value(cap["value"])
            pc["unknown_capabilities"] = [cap["key"] for cap in pc["capabilities"] if cap["value"].get("kind") == "unknown"]
            pc["optional_accessories_not_installed"] = [cap["key"] for cap in pc["capabilities"] if cap["install"] == "optional_not_installed"]
            pc["modifications"] = modifications.for_configuration(cat, c["id"])
            out["configurations"].append(pc)
        return out

    @_api
    def register_modification(self, configuration_id: str, status: str, changes, description: str = ""):
        """Record a modification: 'installed_documented', 'proposed' (never used for the real check) or 'undocumented' (makes it UNKNOWN)."""
        return modifications.register(self._catalog, configuration_id, status, _parse(changes), description)

    # ------------------------------------------------------------------ verification
    def _working(self, experiment_id, parameters, requirement_edits, confirmed):
        return serialize.working_experiment(self._catalog, experiment_id, _parse(parameters) or None,
                                            _parse(requirement_edits) or None, confirmed)

    def _store(self, result: dict, experiment: dict, configuration_id: str, extra_mods) -> str:
        rid = "res_" + uuid.uuid4().hex[:12]
        result["result_id"] = rid
        doc = {"result": result, "experiment": experiment, "configuration_id": configuration_id, "extra_modifications": extra_mods}
        con = self._catalog.connect()
        with con:
            con.execute("INSERT INTO results VALUES (?,?,?,?)", (rid, result["fingerprint"], result["checked_at"], db.dumps(doc)))
        con.close()
        return rid

    @_api
    def check_compatibility(self, experiment_id: str, configuration_id: str, parameters=None, requirement_edits=None,
                            confirmed: bool = False, extra_modifications=None, suggestions: bool = True):
        """Lean verdict for one exact configuration, then Z3 suggestions (each re-checked by Lean).
        `confirmed` must be true after the user has reviewed the requirements (otherwise NEED_MORE_INFORMATION)."""
        ex = self._working(experiment_id, parameters, requirement_edits, confirmed)
        mods = _parse(extra_modifications) or []
        res = verifier.check(self._catalog, ex, configuration_id, mods, suggestions=suggestions)
        self._store(res, ex, configuration_id, mods)
        return res

    @_api
    def find_compatible_equipment(self, experiment_id: str, parameters=None, requirement_edits=None, confirmed: bool = False,
                                  max_results: int = 10, include_hypothetical_options: bool = True):
        """Z3 searches ALL registered configurations; every candidate is checked by Lean (check-candidates)."""
        from . import smt
        cat = self._catalog
        ex = self._working(experiment_id, parameters, requirement_edits, confirmed)
        pairs = []
        for cid in cat.configurations:
            cd, ed, _, _ = verifier.build_documents(cat, ex, cid)     # registered modifications applied
            pairs.append((cd, ed))
        models = {cid: f"{c.get('manufacturer', '')} {c.get('model', '')} {c.get('name', '')}" for cid, c in cat.configurations.items()}
        ranked = smt.rank_alternatives(pairs, include_hypothetical_options, ex.get("reported_equipment", []), models)
        # pending-information candidates that document none of the requirements are not useful suggestions
        shown = [r for r in ranked if r["evaluation"]["status"] != "conflict"
                 and (r["evaluation"]["status"] != "pending_information" or r["evaluation"]["documented_passes"] > 0)][:max_results]
        results = []
        for r in shown:
            lr = lean_runner.check_candidates(r["experiment_document"], [r["configuration_document"]])[0]
            ev = r["evaluation"]
            results.append({"configuration_id": r["configuration_document"]["id"], "equipment_id": ev["equipment_id"],
                            "name": r["configuration_document"]["name"], "z3_status": ev["status"], "added_options": ev["added_options"],
                            "hypothetical": bool(ev["added_options"]), "z3_unknown_items": ev["unknown_items"],
                            "named_in_sources": ev["named_in_sources"], "min_relative_margin": ev["min_relative_margin"],
                            "lean_verdict": lr["verdict"], "verified": lr["verdict"] == "REQUIREMENTS_MET", "lean_summary": lr["summary"]})
        rejected = [{"configuration_id": r["configuration_document"]["id"], "failing": r["evaluation"]["failing_items"]}
                    for r in ranked if r["evaluation"]["status"] == "conflict"]
        return {"experiment_id": experiment_id, "candidates": results, "verified_compatible": [c for c in results if c["verified"]],
                "rejected_by_z3": rejected,
                "ranking_criteria": ["status tier", "fewest added options", "named in the experiment's sources", "fewest unknowns",
                                     "most documented passes", "largest smallest relative margin"],
                "note": "Only entries with verified=true passed the Lean checker on the exact document shown."}

    @_api
    def compare_equipment(self, experiment_id: str, configuration_ids, parameters=None, requirement_edits=None, confirmed: bool = False):
        """Same experiment on 2+ configurations (any manufacturers/industries), one Lean verdict each."""
        ids = _parse(configuration_ids)
        ex = self._working(experiment_id, parameters, requirement_edits, confirmed)
        rows = []
        for cid in ids:
            r = verifier.check(self._catalog, copy.deepcopy(ex), cid, suggestions=False)
            self._store(r, ex, cid, [])
            rows.append(r)
        keys = []
        for r in rows:
            for c in r["checks"] + r["coupled_checks"]:
                k = "/".join(c["keys"]) if c["kind"] == "requirement" else c["name"]
                if k not in keys:
                    keys.append(k)
        table = [{"check": k, **{r["equipment"]["configuration_id"]: next(
            (c["outcome"] for c in r["checks"] + r["coupled_checks"]
             if ("/".join(c["keys"]) if c["kind"] == "requirement" else c["name"]) == k), None) for r in rows}} for k in keys]
        return {"experiment_id": experiment_id, "results": rows, "comparison_table": table}

    @_api
    def get_verification_details(self, result_id: str):
        """Stored result; refuses (stale_result) if the catalog or inputs changed since it was computed."""
        return self._details(result_id)

    def _details(self, result_id: str):
        con = self._catalog.connect()
        try:
            row = con.execute("SELECT doc, fingerprint FROM results WHERE id = ?", (result_id,)).fetchone()
        finally:
            con.close()
        if not row:
            raise CatalogError(f"unknown result '{result_id}'")
        doc = json.loads(row["doc"])
        cfg_doc, exp_doc, _, _ = verifier.build_documents(self._catalog, doc["experiment"], doc["configuration_id"], doc["extra_modifications"])
        now_fp = serialize.fingerprint({"catalog_version": self._catalog.version}, cfg_doc, exp_doc)
        if now_fp != row["fingerprint"]:
            raise StaleResult("this result no longer matches the current catalog, configuration or experiment; check again")
        return doc["result"]

    # ------------------------------------------------------------------ sessions (switching equipment)
    @_api
    def start_session(self, experiment_id: str):
        """Keeps one experiment while the user switches machines. Starts UNCONFIRMED."""
        self._catalog.get_experiment(experiment_id)
        sid = "ses_" + uuid.uuid4().hex[:10]
        self._sessions[sid] = {"id": sid, "experiment_id": experiment_id, "parameters": {}, "requirement_edits": [],
                               "confirmed": False, "configuration_id": None, "result_id": None, "events": [{"event": "created"}]}
        return self._sessions[sid]

    def _session(self, sid):
        if sid not in self._sessions:
            raise CatalogError(f"unknown session '{sid}'")
        return self._sessions[sid]

    @_api
    def update_session(self, session_id: str, parameters=None, requirement_edits=None, confirmed: bool | None = None):
        s = self._session(session_id)
        if parameters is not None:
            s["parameters"].update(_parse(parameters))
            s["confirmed"] = False
        if requirement_edits is not None:
            edits = _parse(requirement_edits)
            self._working(s["experiment_id"], s["parameters"], s["requirement_edits"] + edits, False)   # validate the edit rules
            s["requirement_edits"] += edits
            s["confirmed"] = False
        if confirmed is not None:
            s["confirmed"] = confirmed is True          # strict: only an explicit boolean true confirms
        s["result_id"] = None
        s["events"].append({"event": "updated"})
        return s

    @_api
    def select_equipment(self, session_id: str, configuration_id: str):
        """Switch machine: the experiment is kept, the previous result is invalidated."""
        s = self._session(session_id)
        self._catalog.get_configuration(configuration_id)
        s["events"].append({"event": "equipment_switched", "from": s["configuration_id"], "to": configuration_id,
                            "invalidated_result": s["result_id"]})
        s["configuration_id"] = configuration_id
        s["result_id"] = None
        return s

    @_api
    def check_session(self, session_id: str):
        s = self._session(session_id)
        if not s["configuration_id"]:
            raise ValueError("select equipment first")
        ex = self._working(s["experiment_id"], s["parameters"], s["requirement_edits"], s["confirmed"])
        res = verifier.check(self._catalog, ex, s["configuration_id"])
        s["result_id"] = self._store(res, ex, s["configuration_id"], [])
        return res

    @_api
    def get_session_result(self, session_id: str):
        s = self._session(session_id)
        if not s["result_id"]:
            raise StaleResult("no current result: the setup changed or has not been checked yet")
        return self._details(s["result_id"])

    # ------------------------------------------------------------------ research & coverage
    @_api
    def research_new_experiment(self, description: str, industry: str = "unspecified", research_text: str | None = None):
        """For an experiment that is not registered: returns NEED_MORE_INFORMATION, the closest prepared profiles,
        the 12-step research plan, and (optionally, with Claude) an UNTRUSTED draft candidate from supplied research text."""
        cat = self._catalog
        if industry and industry not in cat.industries:
            cat.register_industry(industry.replace("_", " ").title(), industry_id=industry)
        m = ai.match(cat, description)
        req = research.create_request(cat, industry, description, m["matches"])
        draft = ai.draft_candidate(cat, description, research_text) if research_text else None
        if draft and draft.get("ok"):
            d = draft["draft"]
            cand = research.submit_candidate(cat, "experiment", d.get("document", {}), d.get("evidence", []), "ai_draft", req["id"])
            draft["candidate"] = {"id": cand["id"], "validation": cand["validation"]}
        return {"request": req, "verdict": "NEED_MORE_INFORMATION", "closest_profiles": m["matches"], "ai_draft": draft}

    @_api
    def get_research_coverage(self):
        return coverage.build(self._catalog)

    @_api
    def get_lean_status(self):
        ok, out = lean_runner.selftest()
        inv = lean_runner.theorem_inventory()
        return {"lean_available": inv["lean_binary_present"], "version": lean_runner.version(), "selftest_passed": ok,
                "theorem_count": inv["count"], "theorems": inv["theorems"], "unsafe_markers": inv["unproved_or_unsafe_markers"]}

    @_api
    def get_physical_properties(self):
        return {"properties": coverage.property_status(self._catalog),
                "coupled_models": list(self._catalog.coupled_models.values())}

    @_api
    def reload_catalog(self):
        self._catalog.reload()
        return {"catalog_version": self._catalog.version}


def _display_value(v: dict) -> str:
    from . import units
    k = v.get("kind")
    try:
        if k == "range":
            return f"{units.display_catalog(v['lo']['value'], v['lo']['unit'])} to {units.display_catalog(v['hi']['value'], v['hi']['unit'])}"
        if k in ("max", "min"):
            return f"{'up to' if k == 'max' else 'down to'} {units.display_catalog(v['q']['value'], v['q']['unit'])}"
        if k == "flag":
            return "yes" if v["b"] else "no"
        if k == "count":
            return str(v["n"])
        if k == "enum":
            return v["s"]
        if k == "set":
            return ", ".join(v["xs"])
    except Exception:  # noqa: BLE001
        pass
    return "UNKNOWN"
