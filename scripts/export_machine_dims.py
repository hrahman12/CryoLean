#!/usr/bin/env python
"""Documented inside dimensions of every catalog configuration -> site/machine_dims.json (millimetres).

Only capabilities with a numeric documented value are exported (an "unknown" stays out), so the website's 3D view can
draw each machine's sample space to scale from its datasheet and leave undocumented parts undrawn.
"""
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TO_MM = {"mm": Fraction(1), "um": Fraction(1, 1000), "cm": Fraction(10), "m": Fraction(1000), "in": Fraction(254, 10)}
KEYS = {  # capability -> short name used by the page
    "sample.diameter.max": "space_d", "sample.height.max": "space_h", "sample.bore_diameter": "bore_d",
    "sample.width.max": "space_w", "sample.length.max": "space_l", "optical.objective_working_distance.min": "work_dist",
}


def mm(q):
    if not isinstance(q, dict) or q.get("unit") not in TO_MM:
        return None
    try:
        return float(Fraction(str(q["value"])) * TO_MM[q["unit"]])
    except (ValueError, ZeroDivisionError, KeyError):
        return None


def main():
    out = {}
    for f in sorted((ROOT / "data/cryostats").glob("*.json")):
        eq = json.loads(f.read_text(encoding="utf-8"))
        for cfg in eq.get("configurations", []):
            dims = {}
            for cap in cfg.get("capabilities", []):
                name, v = KEYS.get(cap.get("key")), cap.get("value") or {}
                if not name or cap.get("install") == "optionalNotInstalled" or v.get("kind") not in ("max", "min"):
                    continue
                x = mm(v.get("q"))
                if x and x > 0:
                    dims[name] = round(x, 4)
            if dims:
                out[cfg["id"]] = dims
    path = ROOT / "site/machine_dims.json"
    path.write_text(json.dumps(out, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    print(path.relative_to(ROOT), len(out), "configurations with documented inside dimensions")


if __name__ == "__main__":
    main()
