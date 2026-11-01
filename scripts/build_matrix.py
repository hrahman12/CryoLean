#!/usr/bin/env python
"""Build site/matrix.html: the 180-pair featured matrix (20 industries x 3 experiments x 3 machines).

Every cell is a verdict the Lean 4 checker already returned (site/lattice.json: each of the 60 featured experiments
against all 220 configurations, at the profile's default values). Nothing is recomputed here. The 3 machines per
industry are the ones Lean passes most often for that industry's 3 experiments ("best documented match"); the
previous hand-picked selection is shown for comparison.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
L = json.loads((ROOT / "site/lattice.json").read_text(encoding="utf-8"))
S = json.loads((ROOT / "research/v4/site_selection.json").read_text(encoding="utf-8"))
D = json.loads((ROOT / "site/data.json").read_text(encoding="utf-8"))
lat, cfgs = L["lattice"], L["configurations"]
names = {e["id"]: (e.get("plain_name") or e["name"]) for ind in D["industries"] for e in ind["experiments"]}
ind_names = {ind["id"]: ind["name"] for ind in D["industries"]}

def score(ex, c):
    return (sum(lat[e][c]["verdict"] == "R" for e in ex), -sum(lat[e][c]["verdict"] == "D" for e in ex))

out = {"lean_source_hash": L["lean_source_hash"], "generated": L["generated"], "industries": []}
for ind in D["industries"]:
    iid = ind["id"]; ex = S[iid]["experiment_ids"]
    best = sorted(cfgs, key=lambda c: (tuple(-x for x in score(ex, c)), c))[:3]
    def block(sel):
        return [[lat[e][c]["verdict"] for c in sel] for e in ex]
    out["industries"].append({
        "id": iid, "name": ind_names[iid],
        "experiments": [{"id": e, "name": names.get(e, e), "anywhere": sum(lat[e][c]["verdict"] == "R" for c in cfgs)} for e in ex],
        "best": {"machines": [{"id": c, "m": cfgs[c]["m"], "n": cfgs[c]["n"]} for c in best], "cells": block(best)},
        "old": {"machines": [{"id": c, "m": cfgs[c]["m"], "n": cfgs[c]["n"]} for c in S[iid]["configuration_ids"]], "cells": block(S[iid]["configuration_ids"])},
    })
data = json.dumps(out, ensure_ascii=False).replace("</", "<\\/")
tpl = (ROOT / "site/matrix_template.html").read_text(encoding="utf-8")
(ROOT / "site/matrix.html").write_text(tpl.replace("__MATRIX__", data), encoding="utf-8")
(ROOT / "site/matrix_data.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")   # inlined into the demo tab
cnt = lambda k, v: sum(x == v for i in out["industries"] for row in i[k]["cells"] for x in row)
print("best:", cnt("best", "R"), "met /", cnt("best", "N"), "info /", cnt("best", "D"), "not met")
print("old: ", cnt("old", "R"), "met /", cnt("old", "N"), "info /", cnt("old", "D"), "not met")
