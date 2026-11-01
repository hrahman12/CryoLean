"""Validate expansion A in memory without changing the shared catalog."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from cryolean.validation import Report, validate_configuration, validate_experiment, validate_evidence_record


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


manifest = read(ROOT / "research/expansion/a_manifest.json")
vocab = read(ROOT / "data/capability_vocabulary.json")["keys"]
vocab.update(manifest["vocabulary_proposals"])
evidence = {e["id"]: e for e in read(ROOT / "data/evidence/expansion_a.json")}
catalog = SimpleNamespace(vocabulary=vocab, evidence=evidence, coupled_models={})
report = Report()
for eid, item in evidence.items():
    validate_evidence_record(item, eid, report)
for path in (ROOT / "data/cryostats").glob("expansion_a_*.json"):
    item = read(path)
    for config in item["configurations"]:
        validate_configuration(catalog, config, config["id"], report)
for path in (ROOT / "data/experiments").glob("expansion_a_*.json"):
    item = read(path)
    validate_experiment(catalog, item, item["id"], report)
assert len(manifest["industries"]) == 7
assert sum(len(i["experiment_ids"]) for i in manifest["industries"]) == 21
assert all(len(i["experiment_ids"]) == 3 and len(i["configuration_ids"]) == 3 for i in manifest["industries"])
print(json.dumps(report.as_dict(), indent=2))
sys.exit(0 if report.ok else 1)
