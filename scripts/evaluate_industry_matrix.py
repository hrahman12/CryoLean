"""Run the real Lean engine on the complete curated industry coverage matrix."""
from __future__ import annotations
import argparse
import csv
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cryolean import db, industry_matrix
from cryolean.catalog import Catalog
from cryolean.validation import validate_catalog


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db")
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    if args.rebuild:
        db.build_database(db_path=args.db)
    catalog = Catalog(args.db)
    validation = validate_catalog(catalog)
    if not validation.ok:
        raise ValueError("Invalid catalog: " + "\n".join(str(i) for i in validation.errors))
    report, full_records = industry_matrix.evaluate(catalog, confirmed=True)
    destination = ROOT / "docs/coverage"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "industry-matrix.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with gzip.open(destination / "industry-matrix-records.jsonl.gz", "wt", encoding="utf-8") as output:
        for record in full_records:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
    with (destination / "industry-matrix.csv").open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=["industry_id", "experiment_id", "configuration_id", "verdict", "summary", "lean_input_hash", "input_sha256"])
        writer.writeheader()
        writer.writerows({key: row[key] for key in writer.fieldnames} for row in report["rows"])
    text = ["# CryoLean industry coverage matrix", "", f"Actual Lean evaluations: **{report['evaluated_pairings']}** of the 180-pair minimum target.",
            f"Recorded {report['evaluated_at']}. Checker source/binary SHA-256: `{report['lean_source_hash']}`.",
            "", "PASS = REQUIREMENTS_MET; FAIL = DOES_NOT_MEET_REQUIREMENTS; UNKNOWN = NEED_MORE_INFORMATION.",
            "These are evaluations of the prepared requirements as authored. Grouping equipment under an industry does not establish suitability.", ""]
    labels = {"REQUIREMENTS_MET": "PASS", "DOES_NOT_MEET_REQUIREMENTS": "FAIL", "NEED_MORE_INFORMATION": "UNKNOWN"}
    for industry in report["industries"]:
        text += [f"## {industry['name']}", ""]
        if industry["shortfalls"]:
            text += [f"Shortfall: {gap}" for gap in industry["shortfalls"]] + [""]
        for index, cid in enumerate(industry["configuration_ids"], 1):
            configuration = catalog.configurations[cid]
            text += [f"{index}. **{configuration['name']}** (`{cid}`)"]
        text += ["", "| Experiment | " + " | ".join(f"Equipment {i+1}" for i in range(len(industry["configuration_ids"]))) + " |",
                 "|---|" + "---|" * len(industry["configuration_ids"])]
        for eid in industry["experiment_ids"]:
            values = [next((labels[row["verdict"]] for row in report["rows"] if row["industry_id"] == industry["id"] and row["experiment_id"] == eid and row["configuration_id"] == cid), "NOT EVALUATED") for cid in industry["configuration_ids"]]
            text += [f"| {catalog.experiments[eid]['name']} (`{eid}`) | " + " | ".join(values) + " |"]
        text += ["", "### Reasons and missing information", ""]
        for row in report["rows"]:
            if row["industry_id"] == industry["id"]:
                text += [f"- `{row['experiment_id']}` × `{row['configuration_id']}`: **{labels[row['verdict']]}**. {row['summary']}"]
        text += [""]
    (destination / "INDUSTRY_COVERAGE_MATRIX.md").write_text("\n".join(text), encoding="utf-8")
    public = ROOT / "frontend/public/coverage"
    public.mkdir(parents=True, exist_ok=True)
    for name in ("industry-matrix.json", "industry-matrix.csv", "INDUSTRY_COVERAGE_MATRIX.md"):
        (public / name).write_bytes((destination / name).read_bytes())
    print(json.dumps({"evaluated_pairings": report["evaluated_pairings"], "counts": report["counts"], "industries": len(report["industries"])}))


if __name__ == "__main__":
    main()
