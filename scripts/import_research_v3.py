#!/usr/bin/env python
"""Import the independently verified v3 gap research (research/v3/result.json, from the 'cryolean-data-gap-research'
workflow) into the seed catalog.

Rules (nothing is invented):
* only records the independent verifier accepted (accept = true) are imported; its fixed_value replaces the value;
* a record fills a capability that is missing, UNKNOWN or only an inferred estimate; an existing trusted value is never
  overwritten by a record;
* an existing INSTALLED record backed by trusted evidence is never downgraded to "optional_not_installed"/"not_available";
  an untrusted placeholder ("installed", value UNKNOWN, evidence unknown) may be replaced by a trusted documented absence,
  except where another trusted record of the configuration says the capability exists (PROTECTED);
* sample-size limits of OPTIONAL sample carriers are not imported as absences (a missing carrier does not mean the
  instrument has no sample space);
* keys outside data/capability_vocabulary.json and value shapes the Lean checker does not represent (field envelopes,
  pressure-vs-temperature tables) are kept as evidence for future models but not imported as capabilities;
* corrections to existing values are applied only from the hand-reviewed list CORRECTIONS below (each was accepted by the
  independent verifier and reviewed by the maintainer; declined ones are listed with the reason);
* every imported value gets an evidence record ev_v3_NNNN (records) or ev_v3_cNN (corrections) in
  data/evidence/v3_gap_research.json with the source, location, verbatim quote, access date and the verifier's note.
* 'not_available' marks a documented absence (Lean reads it as "absent"); validation requires trusted evidence for it.

Run:  python scripts/import_research_v3.py      (idempotent: re-running restores the previous values first)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RES = ROOT / "research" / "v3" / "result.json"
EV_OUT = DATA / "evidence" / "v3_gap_research.json"
LOG = ROOT / "research" / "v3" / "import_log.json"
UNTRUSTED = {"unknown", "inferred_estimate"}
# (configuration id prefix, key): never replaced by an absence, because another TRUSTED record of the same configuration
# says the capability exists (ev_ox_0011: "TeslatronPT inserts provide DC and RF wiring to the sample").
PROTECTED = {("oxford_teslatronpt_", "electrical.dc_lines"), ("oxford_teslatronpt_", "electrical.coax_lines")}
LEAN_KINDS = {"range", "max", "min", "flag", "count", "enum", "set", "unknown"}

# Corrections accepted by the independent verifier AND by maintainer review.
# (family, configuration_id, key) -> patch applied to the existing capability (value / install / evidence_status).
CORRECTIONS = {
    ("bluefors", "bluefors_ld450_current", "electrical.coax_lines"):
        {"value": {"kind": "count", "n": 77}},
    ("ccs", "lakeshore_ccs_400h", "temperature.range"):
        {"value": {"kind": "range", "lo": {"value": 5000, "unit": "mK"}, "hi": {"value": 800000, "unit": "mK"}},
         "evidence_status": "manufacturer_specification"},
    ("ccs", "lakeshore_ccs_100", "cooldown_time.max"): {"evidence_status": "manufacturer_specification"},
    ("ccs", "lakeshore_ccs_300s", "cooldown_time.max"): {"evidence_status": "manufacturer_specification"},
    ("ccs", "lakeshore_ccs_400", "cooldown_time.max"): {"evidence_status": "manufacturer_specification"},
    ("ccs", "lakeshore_ccs_400h", "cooldown_time.max"): {"evidence_status": "manufacturer_specification"},
    ("leica", "leica_cm1950_genA_standard", "sample.length.max"):
        {"value": {"kind": "unknown"}, "evidence_status": "unknown",
         "_also": {"sample.height.max": {"value": {"kind": "max", "q": {"value": 50000, "unit": "um"}},
                                         "evidence_status": "manufacturer_specification", "install": "installed"}}},
    ("leica", "leica_cm1950_genA_vacuum_motor_objcool", "sample.length.max"):
        {"value": {"kind": "unknown"}, "evidence_status": "unknown",
         "_also": {"sample.height.max": {"value": {"kind": "max", "q": {"value": 50000, "unit": "um"}},
                                         "evidence_status": "manufacturer_specification", "install": "installed"}}},
    ("linkam", "linkam_thmsel600_lnp96", "electrical.sample_connections"):
        {"value": {"kind": "unknown"}, "evidence_status": "unknown"},
    ("linkam", "linkam_thmsel600_lnp96", "optical.objective_working_distance.min"):
        {"value": {"kind": "unknown"}, "evidence_status": "unknown"},
    ("ppms", "qd_ppms_classic_14T", "magnetic_field.uniformity"):
        {"value": {"kind": "min", "q": {"value": 1000, "unit": "ppm"}}, "evidence_status": "manufacturer_specification"},
    ("ppms", "qd_ppms_classic_16T", "magnetic_field.uniformity"):
        {"value": {"kind": "min", "q": {"value": 1000, "unit": "ppm"}}, "evidence_status": "manufacturer_specification"},
    **{("improvements", c, "temperature.range"):
           {"value": {"kind": "range", "lo": {"value": 1850, "unit": "mK"}, "hi": {"value": 400000, "unit": "mK"}}}
       for c in ("qd_dynacool_9T_eto_res", "qd_dynacool_14T_eto_vsm_hc", "qd_dynacool_12T_vsm")},
    **{("improvements", c, "temperature.base"): {"value": {"kind": "min", "q": {"value": 1850, "unit": "mK"}}}
       for c in ("qd_dynacool_9T_eto_res", "qd_dynacool_14T_eto_vsm_hc", "qd_dynacool_12T_vsm")},
    ("improvements", "oxford_optistatdry_blv", "cooling_power.at_4200mK"):
        {"value": {"kind": "max", "q": {"value": 160000000, "unit": "nW"}}},
    **{("improvements", c, "pressure.base"): {"value": {"kind": "min", "q": {"value": "0.00001", "unit": "Torr"}}}
       for c in ("lakeshore_crx_vf", "lakeshore_crx_4k")},
    **{("improvements", c, "pressure.base"): {"value": {"kind": "min", "q": {"value": "0.0001", "unit": "Torr"}}}
       for c in ("qd_dynacool_9T_eto_res", "qd_dynacool_14T_eto_vsm_hc", "qd_dynacool_12T_vsm")},
}
CONFIG_TEXT = {   # configuration name / basis corrections (verified: THMSEL600 is the ellipsometry stage)
    "linkam_thmsel600_lnp96": {
        "name": "Linkam THMSEL600 (ellipsometry variant of the THMS600) with T96-S controller and LNP96 liquid nitrogen pump",
        "configuration_basis": "catalog combination: THMSEL600 ellipsometry stage (an ellipsometer lid with side windows; the "
                               "electrical variant is the THMS600E) + T96-S + LNP96. Values from the THMSEL600 pages; values "
                               "that earlier came from the THMS600E column of the 2018 brochure were set to UNKNOWN (v3 review)."},
}
EQUIPMENT_TEXT = {"linkam_thms600.json": ("Electrical variant THMSEL600", "Ellipsometry variant THMSEL600 (the electrical variant is the THMS600E)")}
DECLINED = [
    {"correction": "oxford_teslatronpt_* electrical.dc_lines / electrical.coax_lines -> optional_not_installed (UMP probe)",
     "reason": "The evidence shows the optional Universal Measurement Probe carries 38 DC / 4 RF lines; it does not establish "
               "that the base system has no sample wiring (ev_ox_0011: 'TeslatronPT inserts provide DC and RF wiring to the "
               "sample'). Recording absence would create unsourced rejections; the counts stay UNKNOWN."},
    {"correction": "oxford_optistatdry_tlex vacuum.available", "reason": "review only; the verifier and the researcher both keep false."},
    {"correction": "lakeshore_crx_vf magnetic_field.max -> field-temperature envelope",
     "reason": "accepted as a MODEL change (field_temperature_envelope), implemented separately, not as a data patch."},
]


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def save(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalized(value):
    if value.get("kind") in ("max", "min"):
        return value.get("q")
    if value.get("kind") == "range":
        return {"lo": value.get("lo"), "hi": value.get("hi")}
    return value


def restore(files, equipment, old_ids):
    """Undo a previous v3 import (idempotency)."""
    for doc in files.values():
        for cfg in doc["configurations"]:
            if "_v3_previous_text" in cfg:
                for k, v in cfg.pop("_v3_previous_text").items():
                    cfg[k] = v
            for cap in list(cfg["capabilities"]):
                if "_v3_previous" in cap:
                    prev = cap.pop("_v3_previous")
                    cap.clear()
                    cap.update(prev)
                elif set(cap.get("evidence_ids", [])) & old_ids:
                    cfg["capabilities"].remove(cap)
        if "_v3_previous_description" in doc:
            doc["description"] = doc.pop("_v3_previous_description")


def set_cap(cfg, key, new, ev_id):
    cap = next((c for c in cfg["capabilities"] if c["key"] == key), None)
    if cap is None:
        cfg["capabilities"].append({**new, "key": key, "evidence_ids": [ev_id], "_v3_added": True})
        return "added"
    prev = {k: v for k, v in cap.items() if not k.startswith("_v3")}
    cap.update({k: v for k, v in new.items() if k != "key"})
    cap["evidence_ids"] = list(dict.fromkeys(prev.get("evidence_ids", []) + [ev_id]))
    if "_v3_previous" not in cap:
        cap["_v3_previous"] = prev
    return "patched"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    res = load(RES)
    vocab = set(load(DATA / "capability_vocabulary.json")["keys"])
    files = {p.name: load(p) for p in sorted((DATA / "cryostats").glob("*.json"))}
    old_ids = {r["id"] for r in load(EV_OUT)} if EV_OUT.exists() else set()
    restore(files, None, old_ids)
    for doc in files.values():          # drop records added by a previous run (marked _v3_added)
        for cfg in doc["configurations"]:
            cfg["capabilities"] = [c for c in cfg["capabilities"] if not c.get("_v3_added")]
    cfg_index = {cfg["id"]: cfg for doc in files.values() for cfg in doc["configurations"]}
    evidence = []
    log = {"imported": [], "skipped": [], "rejected_by_verifier": [], "corrections_applied": [], "corrections_declined": DECLINED,
           "not_found": [], "proposals": [], "model_data": []}
    n = 0
    for fam in res["results"]:
        recs = fam["research"]["records"]
        verdicts = {v["index"]: v for v in (fam.get("verdicts") or {}).get("results", [])}
        for i, rec in enumerate(recs):
            v = verdicts.get(i)
            if not v or not v.get("accept"):
                log["rejected_by_verifier"].append({"family": fam["family"], "key": rec["key"], "configs": rec["configuration_ids"],
                                                    "note": (v or {}).get("note", "no verdict")[:400]})
                continue
            value = v.get("fixed_value") or rec["value"]
            if rec["key"] not in vocab or value.get("kind") not in LEAN_KINDS:
                log["model_data"].append({"family": fam["family"], "key": rec["key"], "configs": rec["configuration_ids"],
                                          "value": value, "source_url": rec["source_url"], "claim": rec["claim"]})
                continue
            if rec["install"] == "not_available" and value.get("kind") not in ("unknown", "flag"):
                value = {"kind": "unknown"}
            n += 1
            ev_id = f"ev_v3_{n:04d}"
            used = False
            for cid in rec["configuration_ids"]:
                cfg = cfg_index.get(cid)
                if cfg is None:
                    log["skipped"].append({"config": cid, "key": rec["key"], "why": "unknown configuration id"})
                    continue
                cap = next((c for c in cfg["capabilities"] if c["key"] == rec["key"]), None)
                absent_new = rec["install"] in ("optional_not_installed", "not_available")
                if absent_new and rec["key"].startswith("sample."):
                    log["skipped"].append({"config": cid, "key": rec["key"], "why": "optional sample carrier is not evidence that the sample space is absent"})
                    continue
                if absent_new and any(cid.startswith(pre) and rec["key"] == k for pre, k in PROTECTED):
                    log["skipped"].append({"config": cid, "key": rec["key"], "why": "protected: another trusted record says the capability exists"})
                    continue
                if (cap is not None and absent_new and cap.get("install") == "installed"
                        and cap.get("evidence_status") not in UNTRUSTED):
                    log["skipped"].append({"config": cid, "key": rec["key"], "why": "would downgrade a TRUSTED installed record to absent"})
                    continue
                if cap is not None and not (cap.get("evidence_status") in UNTRUSTED or (cap.get("value") or {}).get("kind") == "unknown"
                                            or cap.get("install") == "unknown"):
                    log["skipped"].append({"config": cid, "key": rec["key"], "why": "trusted value already present", "existing": cap.get("value")})
                    continue
                how = set_cap(cfg, rec["key"], {"value": value, "install": rec["install"], "evidence_status": rec["evidence_status"]}, ev_id)
                if how == "patched":
                    cap = next(c for c in cfg["capabilities"] if c["key"] == rec["key"])
                    cap["evidence_ids"] = [ev_id]      # the old record cited only 'not found' evidence; the new value rests on ev_id
                log["imported"].append({"config": cid, "key": rec["key"], "kind": rec["kind"], "install": rec["install"], "evidence": ev_id})
                used = True
            if used:
                evidence.append({"id": ev_id, "claim": rec["claim"], "value_as_printed": rec["value_as_printed"],
                                 "normalized": normalized(value), "source_url": rec["source_url"],
                                 "document_title": rec["document_title"], "location": rec["location"], "quote": rec["quote"],
                                 "applies_to": ", ".join(rec["configuration_ids"]), "evidence_status": rec["evidence_status"],
                                 "accessed": rec["accessed"], "collected_by": f"research agent v3 ({rec.get('found_via', '')})"[:300],
                                 "review_status": f"independently re-fetched and verified by a second agent: {v.get('note', '')}"[:700],
                                 "kind": rec["kind"], "reasoning": rec["reasoning"]})
        for nf in fam["research"].get("not_found", []):
            (log["proposals"] if nf["key"].startswith("proposal:") else log["not_found"]).append({"family": fam["family"], **nf})
    # ------------------------------------------------------------------ reviewed corrections
    c = 0
    for fam in res["results"]:
        cok = {x["index"]: x for x in (fam.get("verdicts") or {}).get("corrections_ok", [])}
        for i, corr in enumerate(fam["research"].get("corrections", [])):
            patch = CORRECTIONS.get((fam["family"], corr["configuration_id"], corr["key"]))
            if patch is None or not cok.get(i, {}).get("accept"):
                continue
            cfg = cfg_index[corr["configuration_id"]]
            c += 1
            ev_id = f"ev_v3_c{c:02d}"
            new = {k: v for k, v in patch.items() if not k.startswith("_")}
            set_cap(cfg, corr["key"], new, ev_id)
            for k2, p2 in (patch.get("_also") or {}).items():
                set_cap(cfg, k2, p2, ev_id)
            status = patch.get("evidence_status") or next(x for x in cfg["capabilities"] if x["key"] == corr["key"]).get("evidence_status")
            evidence.append({"id": ev_id, "claim": f"Correction: {corr['proposed']}"[:800], "value_as_printed": corr.get("quote", "")[:300],
                             "normalized": normalized(new.get("value", {})) if new.get("value") else None,
                             "source_url": corr["source_url"], "document_title": "see source", "location": "see verifier note",
                             "quote": corr["quote"], "applies_to": corr["configuration_id"],
                             "evidence_status": status if status not in UNTRUSTED else "unknown",
                             "accessed": "2026-11-01", "collected_by": "research agent v3 (correction)",
                             "review_status": f"verified by a second agent: {cok[i].get('note', '')}"[:700] + " Reviewed by the maintainer.",
                             "kind": "correction", "previous": corr["current"]})
            log["corrections_applied"].append({"config": corr["configuration_id"], "key": corr["key"], "evidence": ev_id, "patch": patch})
    for cid, text in CONFIG_TEXT.items():
        cfg = cfg_index[cid]
        cfg["_v3_previous_text"] = {k: cfg.get(k) for k in text}
        cfg.update(text)
    for fname, (old, new) in EQUIPMENT_TEXT.items():
        doc = files[fname]
        if old in doc.get("description", ""):
            doc["_v3_previous_description"] = doc["description"]
            doc["description"] = doc["description"].replace(old, new)
    for name, doc in files.items():
        save(DATA / "cryostats" / name, doc)
    save(EV_OUT, evidence)
    save(LOG, log)
    print(f"imported {len(log['imported'])} capability values ({len(evidence) - c} record evidence) and applied {c} corrections; "
          f"skipped {len(log['skipped'])}; verifier rejected {len(log['rejected_by_verifier'])}; model data kept {len(log['model_data'])}; "
          f"not found {len(log['not_found'])}; proposals {len(log['proposals'])}")


if __name__ == "__main__":
    main()
