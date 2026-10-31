"""Z3-based configuration search.

Given an experiment's mandatory requirements and every registered configuration
(any manufacturer, any industry), Z3 searches for configurations whose
*documented* capabilities satisfy every mandatory requirement.  It can also
propose "hypothetical" configurations in which optional accessories that the
product family offers but this configuration lacks are added (minimising the
number of added options).

Two tiers:
1. **satisfying** – every mandatory requirement is met by documented values
   (possibly after adding documented optional accessories);
2. **pending information** (only if tier 1 is UNSAT) – no documented conflict,
   but some requirements cannot be established; Z3 minimises how many.  Those
   requirements are reported in ``assumed_unknown`` and are never treated as met.

Guarantees of the encoding (mirroring the Lean rules, but NOT a proof):
* an UNKNOWN value, an unknown install status, a missing capability, an
  inferred estimate or a unit mismatch never satisfies a requirement in tier 1;
* every candidate carries ``verified: False`` until the Lean checker has
  produced a verdict for exactly that configuration document.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field, asdict

import z3

TRUSTED = {"manufacturer_specification", "experimental_observation", "user_entered"}


@dataclass
class ReqStatus:
    key: str
    status: str            # pass | fail | unknown | unsupported | needs_option
    detail: str = ""


@dataclass
class Candidate:
    configuration_id: str
    equipment_id: str
    kind: str                       # "catalog" | "hypothetical" | "pending_information"
    added_options: list[str] = field(default_factory=list)
    assumed_unknown: list[str] = field(default_factory=list)   # requirements Z3 could NOT establish
    requirement_status: list[ReqStatus] = field(default_factory=list)
    smt_status: str = "sat"
    verified: bool = False          # only Lean can set this (via the backend)
    configuration_document: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SearchResult:
    experiment_id: str
    mode: str
    candidates: list[Candidate]
    rejected: list[dict]            # configurations not proposed, with the blocking requirements
    smt_stats: dict
    note: str = ("Z3 candidates are proposals derived from documented values; they are not verified "
                 "until the Lean checker has checked the exact configuration document. Candidates of kind "
                 "'pending_information' have no documented conflict but list requirements the evidence cannot establish.")

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "mode": self.mode,
            "candidates": [c.to_dict() for c in self.candidates],
            "rejected": self.rejected,
            "smt_stats": self.smt_stats,
            "note": self.note,
        }


def _q(x: dict) -> tuple[int, str]:
    return int(x["value"]), str(x["unit"])


def value_formula(constraint: dict, cap_value: dict, name: str) -> tuple[str, z3.BoolRef | None]:
    """Return (status, formula). status 'ok' means `formula` decides it; otherwise a static reason."""
    ck = constraint["kind"]
    vk = cap_value.get("kind")
    if vk == "unknown":
        return "unknown", None
    if ck == "point_within" and vk == "range":
        v, u = _q(constraint["q"]); lo, ul = _q(cap_value["lo"]); hi, uh = _q(cap_value["hi"])
        if not (ul == u and uh == u):
            return "unsupported", None
        L, H, V = z3.Ints(f"{name}_lo {name}_hi {name}_req")
        return "ok", z3.And(L == lo, H == hi, V == v, L <= V, V <= H)
    if ck == "range_within" and vk == "range":
        rlo, u1 = _q(constraint["lo"]); rhi, u2 = _q(constraint["hi"]); lo, ul = _q(cap_value["lo"]); hi, uh = _q(cap_value["hi"])
        if not (u1 == u2 == ul == uh) or rlo > rhi:
            return "unsupported", None
        L, H, RL, RH = z3.Ints(f"{name}_lo {name}_hi {name}_rlo {name}_rhi")
        return "ok", z3.And(L == lo, H == hi, RL == rlo, RH == rhi, L <= RL, RH <= H)
    if ck == "at_least" and vk in ("max", "range"):
        v, u = _q(constraint["q"])
        m, um = _q(cap_value["q"] if vk == "max" else cap_value["hi"])
        if um != u:
            return "unsupported", None
        M, V = z3.Ints(f"{name}_cap {name}_req")
        return "ok", z3.And(M == m, V == v, V <= M)
    if ck == "at_most" and vk in ("min", "range"):
        v, u = _q(constraint["q"])
        m, um = _q(cap_value["q"] if vk == "min" else cap_value["lo"])
        if um != u:
            return "unsupported", None
        M, V = z3.Ints(f"{name}_cap {name}_req")
        return "ok", z3.And(M == m, V == v, M <= V)
    if ck == "present" and vk == "flag":
        return "ok", z3.BoolVal(bool(cap_value["b"]))
    if ck == "count_at_least" and vk == "count":
        N, C = z3.Ints(f"{name}_n {name}_cap")
        return "ok", z3.And(N == int(constraint["n"]), C == int(cap_value["n"]), N <= C)
    return "unsupported", None


class ConfigurationSearch:
    def __init__(self, configurations: list[dict]):
        """`configurations` are catalog configuration dicts (with equipment_id and capabilities)."""
        self.configurations = configurations

    def _encode_pair(self, cfg: dict, req: dict, add_var: z3.BoolRef | None, name: str,
                     assume_var: z3.BoolRef | None = None) -> tuple[ReqStatus, z3.BoolRef]:
        """Encode "configuration `cfg` meets requirement `req`".
        Unknown/unsupported pairs are False, or - only in pending-information mode - an explicit,
        penalised assumption variable reported back as `assumed_unknown` (never as satisfied)."""
        unknown_f = assume_var if assume_var is not None else z3.BoolVal(False)
        cap = next((c for c in cfg.get("capabilities", []) if c["key"] == req["key"]), None)
        if cap is None:
            return ReqStatus(req["key"], "unknown", "no documented capability under this key"), unknown_f
        inst = cap.get("install")
        if inst == "unknown":
            return ReqStatus(req["key"], "unknown", "documentation does not say whether this is fitted"), unknown_f
        if cap.get("evidence_status") not in TRUSTED:
            return ReqStatus(req["key"], "unknown", f"evidence status '{cap.get('evidence_status')}' cannot support a verified pass"), unknown_f
        status, formula = value_formula(req["constraint"], cap["value"], name)
        if status != "ok":
            return ReqStatus(req["key"], status, "value unknown" if status == "unknown" else "unit or shape mismatch"), unknown_f
        s = z3.Solver()
        s.add(formula)
        value_ok = s.check() == z3.sat
        if inst == "optional_not_installed":
            if add_var is None:
                return ReqStatus(req["key"], "fail", "option not installed in this configuration"), z3.BoolVal(False)
            if value_ok:
                return ReqStatus(req["key"], "needs_option", "satisfiable if this option is installed"), z3.And(add_var, formula)
            return ReqStatus(req["key"], "fail", "even the option's documented value does not meet the requirement"), z3.BoolVal(False)
        return ReqStatus(req["key"], "pass" if value_ok else "fail", "documented value compared by Z3"), formula

    def search(self, experiment: dict, allow_hypothetical_options: bool = True, max_candidates: int = 10,
               equipment_filter: list[str] | None = None, allow_pending_information: bool = True) -> SearchResult:
        res = self._search(experiment, allow_hypothetical_options, max_candidates, equipment_filter, pending=False)
        if res.candidates or not allow_pending_information or not res.smt_stats.get("mandatory_requirements"):
            return res
        res2 = self._search(experiment, allow_hypothetical_options, max_candidates, equipment_filter, pending=True)
        res2.smt_stats["tier1_unsat"] = True
        res2.smt_stats["solver_calls"] += res.smt_stats.get("solver_calls", 0)
        return res2

    def _search(self, experiment: dict, allow_hypothetical_options: bool, max_candidates: int,
                equipment_filter: list[str] | None, pending: bool) -> SearchResult:
        reqs = [r for r in experiment.get("requirements", []) if r.get("mandatory")]
        mode = ("hypothetical_options" if allow_hypothetical_options else "strict_catalog") + ("+pending_information" if pending else "")
        cfgs = [c for c in self.configurations if not equipment_filter or c["equipment_id"] in equipment_filter]
        if not reqs:
            return SearchResult(experiment.get("id", "?"), mode, [], [{"reason": "experiment has no mandatory requirements"}],
                                {"configurations": len(cfgs), "mandatory_requirements": 0, "solver_calls": 0})
        if not cfgs:
            return SearchResult(experiment.get("id", "?"), mode, [], [{"reason": "no configurations match the filter"}],
                                {"configurations": 0, "mandatory_requirements": len(reqs), "solver_calls": 0})

        opt = z3.Optimize()
        sel = {c["id"]: z3.Bool(f"sel__{c['id']}") for c in cfgs}
        opt.add(z3.PbEq([(v, 1) for v in sel.values()], 1))          # exactly one configuration
        add_vars: dict[tuple[str, str], z3.BoolRef] = {}
        assume_vars: dict[tuple[str, str], z3.BoolRef] = {}
        statuses: dict[str, list[ReqStatus]] = {}
        for c in cfgs:
            per: list[ReqStatus] = []
            conj = []
            for r in reqs:
                av = None
                cap = next((x for x in c.get("capabilities", []) if x["key"] == r["key"]), None)
                if allow_hypothetical_options and cap is not None and cap.get("install") == "optional_not_installed":
                    av = add_vars.setdefault((c["id"], r["key"]), z3.Bool(f"add__{c['id']}__{r['key']}"))
                asv = z3.Bool(f"assume__{c['id']}__{r['key']}") if pending else None
                st, f = self._encode_pair(c, r, av, f"{c['id']}__{r['key']}".replace(".", "_"), asv)
                if asv is not None and st.status in ("unknown", "unsupported"):
                    assume_vars[(c["id"], r["key"])] = asv
                per.append(st)
                conj.append(f)
            statuses[c["id"]] = per
            opt.add(z3.Implies(sel[c["id"]], z3.And(*conj)))
        for (cid, _), v in list(add_vars.items()) + list(assume_vars.items()):
            opt.add(z3.Implies(v, sel[cid]))     # option/assumption only on the selected configuration
        if assume_vars:   # lexicographic: fewest unknown requirements first, then fewest added options
            opt.minimize(z3.Sum([z3.If(v, 1, 0) for v in assume_vars.values()]))
        if add_vars:
            opt.minimize(z3.Sum([z3.If(v, 1, 0) for v in add_vars.values()]))

        candidates: list[Candidate] = []
        calls = 0
        while len(candidates) < max_candidates:
            calls += 1
            if opt.check() != z3.sat:
                break
            m = opt.model()
            chosen = next(cid for cid, v in sel.items() if z3.is_true(m.eval(v, model_completion=True)))
            added = sorted(k for (cid, k), v in add_vars.items() if cid == chosen and z3.is_true(m.eval(v, model_completion=True)))
            assumed = sorted(k for (cid, k), v in assume_vars.items() if cid == chosen and z3.is_true(m.eval(v, model_completion=True)))
            cfg = next(c for c in cfgs if c["id"] == chosen)
            kind = "pending_information" if assumed else ("hypothetical" if added else "catalog")
            candidates.append(Candidate(
                configuration_id=chosen if not added else f"{chosen}+{'+'.join(added)}",
                equipment_id=cfg["equipment_id"], kind=kind, added_options=added, assumed_unknown=assumed,
                requirement_status=statuses[chosen], smt_status="sat_with_unknowns" if assumed else "sat",
                configuration_document=hypothetical_document(cfg, added) if added else None))
            # block this exact (configuration, added-option set); other option sets of the same configuration stay allowed
            mine = [v for (cid, _), v in add_vars.items() if cid == chosen]
            if mine:
                opt.add(z3.Not(z3.And(sel[chosen], *[(v if z3.is_true(m.eval(v, model_completion=True)) else z3.Not(v)) for v in mine])))
            else:
                opt.add(z3.Not(sel[chosen]))

        rejected = []
        cand_ids = {c.configuration_id.split("+")[0] for c in candidates}
        for c in cfgs:
            if c["id"] in cand_ids:
                continue
            bad = [asdict(s) for s in statuses[c["id"]] if s.status != "pass"]
            rejected.append({"configuration_id": c["id"], "equipment_id": c["equipment_id"], "blocking": bad})
        return SearchResult(experiment.get("id", "?"), mode, candidates, rejected,
                            {"configurations": len(cfgs), "mandatory_requirements": len(reqs), "solver_calls": calls,
                             "z3_version": z3.get_version_string()})


def hypothetical_document(cfg: dict, added: list[str]) -> dict:
    """A configuration document with the named optional accessories marked installed.
    Lean will check *this* document; the id and name say it is hypothetical."""
    doc = copy.deepcopy(cfg)
    doc["id"] = f"{cfg['id']}+{'+'.join(added)}"
    doc["name"] = f"{cfg.get('name', cfg['id'])} (hypothetical: with {', '.join(added)} installed)"
    doc["hypothetical"] = True
    doc["added_options"] = added
    for cap in doc.get("capabilities", []):
        if cap["key"] in added and cap.get("install") == "optional_not_installed":
            cap["install"] = "installed"
    return doc
