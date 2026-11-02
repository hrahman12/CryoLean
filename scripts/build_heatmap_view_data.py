"""Build display-only filters for the saved Lean verdict heatmap.

The verdict matrix is copied verbatim from the recorded research artifact.  This
script only computes visibility masks and aggregates recorded UNKNOWN reasons;
it cannot create, recolor, or re-evaluate a verdict.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "frontend" / "src" / "data" / "catalog.json"
HEATMAP = ROOT / "frontend" / "public" / "research" / "fig_cross_industry_heatmap.json"
GRID = ROOT / "docs" / "coverage" / "full-grid.csv"
OUTPUT = ROOT / "frontend" / "public" / "research" / "lean-verdict-heatmap.json"
FEATURED = ROOT / "site" / "data.json"


def temperature_mk(q: dict | None) -> float | None:
    if not q or q.get("value") is None:
        return None
    try:
        value = float(q["value"])
    except (TypeError, ValueError):
        return None
    unit = q.get("unit")
    return value if unit == "mK" else value * 1_000 if unit == "K" else (value + 273.15) * 1_000 if unit in {"C", "degC"} else None


def experiment_minimum(profile: dict) -> float | None:
    values: list[float] = []
    for req in profile.get("requirements", []):
        if not req.get("mandatory", True) or req.get("key") not in {"temperature.range", "temperature.base"}:
            continue
        constraint = req.get("constraint", {})
        q = constraint.get("lo") if constraint.get("kind") == "range_within" else constraint.get("q")
        value = temperature_mk(q)
        if value is not None:
            values.append(value)
    return min(values) if values else None


def installed_capability(configuration: dict, key: str) -> dict | None:
    for cap in configuration.get("capabilities", []):
        if cap.get("key") == key and cap.get("install") == "installed" and cap.get("evidence_status") != "unknown":
            value = cap.get("value", {})
            if value.get("kind") != "unknown":
                return value
    return None


def machine_minimum(configuration: dict) -> float | None:
    ranged = installed_capability(configuration, "temperature.range")
    if ranged and ranged.get("kind") == "range":
        return temperature_mk(ranged.get("lo"))
    base = installed_capability(configuration, "temperature.base")
    return temperature_mk(base.get("q")) if base else None


def required_cryogens(profile: dict) -> set[str] | None:
    needed: set[str] = set()
    found = False
    for req in profile.get("requirements", []):
        if req.get("key") != "cryogen.type" or not req.get("mandatory", True):
            continue
        constraint = req.get("constraint", {})
        if constraint.get("kind") == "set_contains":
            found = True
            needed.update(str(v) for v in constraint.get("needed", []))
    return needed if found else None


def machine_cryogens(configuration: dict) -> set[str] | None:
    value = installed_capability(configuration, "cryogen.type")
    if not value:
        return None
    raw = value.get("values", value.get("items", value.get("set")))
    return {str(v) for v in raw} if isinstance(raw, list) else None


def plausible(profile: dict, configuration: dict) -> bool:
    required_temp, available_temp = experiment_minimum(profile), machine_minimum(configuration)
    if required_temp is not None and available_temp is not None and available_temp > required_temp:
        return False
    required_cryo, available_cryo = required_cryogens(profile), machine_cryogens(configuration)
    if required_cryo is not None and available_cryo is not None and not required_cryo.issubset(available_cryo):
        return False
    return True


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    source = json.loads(HEATMAP.read_text(encoding="utf-8"))
    featured = json.loads(FEATURED.read_text(encoding="utf-8"))
    assert len(featured["industries"]) == 20
    assert len(featured["verdicts"]) == 180
    assert featured["counts"] == {"REQUIREMENTS_MET": 113, "DOES_NOT_MEET_REQUIREMENTS": 66, "NEED_MORE_INFORMATION": 1}
    assert featured["catalog"] == {"experiments": 204, "configurations": 220, "pairs": 44880, "met": 3118, "not_met": 30299, "need_info": 11463}
    experiments = source["experiments"]
    configurations = source["configurations"]
    masks = {"all": [], "plausible": [], "same_industry": []}
    for experiment_id in experiments:
        profile = catalog["profiles"][experiment_id]
        industry = source["experiment_industry"][experiment_id]
        for configuration_id in configurations:
            configuration = catalog["configurations"][configuration_id]
            masks["all"].append(True)
            masks["plausible"].append(plausible(profile, configuration))
            masks["same_industry"].append(source["configuration_home_industry"].get(configuration_id) == industry)

    missing = {key: Counter() for key in masks}
    pair_index = {(eid, cid): i for i, (eid, cid) in enumerate((e, c) for e in experiments for c in configurations)}
    with GRID.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["verdict"] != "NEED_MORE_INFORMATION":
                continue
            index = pair_index[(row["experiment_id"], row["configuration_id"])]
            items = json.loads(row["missing_information"])
            for view, mask in masks.items():
                if mask[index]:
                    missing[view].update(items)

    verdicts = source["verdict_index"]
    verdict_names = {value: key for key, value in verdicts.items()}
    flat = [value for row in source["matrix"] for value in row]
    counts = {}
    for view, mask in masks.items():
        counter = Counter(verdict_names[value] for value, visible in zip(flat, mask) if visible)
        counts[view] = dict(counter)

    expected = source["grid_meta"]["counts"]
    assert counts["all"] == expected, (counts["all"], expected)
    assert sum(counts["all"].values()) == 44_880
    payload = {
        "featured": featured,
        "grid_meta": source["grid_meta"],
        "experiments": experiments,
        "configurations": configurations,
        "experiment_industry": source["experiment_industry"],
        "configuration_home_industry": source["configuration_home_industry"],
        "configuration_family": source["configuration_family"],
        "experiment_names": {eid: catalog["profiles"][eid].get("plain_name", catalog["profiles"][eid]["name"]) for eid in experiments},
        "configuration_names": {cid: catalog["configurations"][cid]["name"] for cid in configurations},
        "verdict_index": verdicts,
        "matrix": source["matrix"],
        "masks": {key: [1 if value else 0 for value in mask] for key, mask in masks.items() if key != "all"},
        "counts": counts,
        "top_missing": {key: [{"key": item, "count": count} for item, count in counter.most_common(10)] for key, counter in missing.items()},
        "filter_method": {
            "plausible": "A pair is hidden only when both values are documented and either the machine's minimum temperature is warmer than the experiment's required temperature, or its installed cryogen set cannot supply every required cryogen. Unknown values stay visible.",
            "same_industry": "Configuration home industry is the recorded heatmap grouping: the experiment industry in which that configuration has the most saved REQUIREMENTS_MET outcomes; ties use catalog order."
        }
    }
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
