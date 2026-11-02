"""Real frontend scenario inputs through the existing Python/Lean/Z3 contract."""
from conftest import data, check
import json
from pathlib import Path
from copy import deepcopy
from cryolean.validation import Report, validate_configuration, validate_evidence_record

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_readonly_catalog_matches_real_ids(api):
    snapshot = json.loads((ROOT / "frontend/src/data/catalog.json").read_text(encoding="utf-8"))
    assert set(snapshot["profiles"]) == {e["id"] for e in data(api.list_experiments())["experiments"]}
    assert set(snapshot["configurations"]) == {c["id"] for e in data(api.list_equipment())["equipment"] for c in e["configurations"]}


def test_frontend_demo_a_real_pass(api):
    result = check(api, "chem_phase_transition_pom", "linkam_thms600_lnp96_t96", suggestions=True)
    assert result["verdict"] == "REQUIREMENTS_MET"
    assert result["verification"]["concrete_evaluation"]["verified_by_lean"] is True
    assert result["verdict_card"]["axiom_audit"] == "current"


def test_frontend_demo_b_real_failure_and_c_missing_information(api):
    failure = check(api, "mat_magnetoresistance_10T", "qd_dynacool_9T_eto_res", suggestions=True)
    assert failure["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"
    assert "magnetic_field.max" in failure["failed_requirements"]
    assert failure["suggestions"]["engine"] == "z3"
    unknown = check(api, "mat_magnetoresistance_10T", "qd_dynacool_14T_eto_vsm_hc", suggestions=False)
    assert unknown["verdict"] == "NEED_MORE_INFORMATION"
    assert set(unknown["missing_information"]) >= {"sample.width.max", "sample.length.max", "sample.height.max"}


def test_frontend_coupled_demo_and_proposed_input_change(api):
    failed = check(api, "quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw", suggestions=True)
    assert failed["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"
    coupled = next(c for c in failed["coupled_checks"] if c["model"] == "mxc_wiring_heat_budget")
    assert coupled["lhs"]["display"] == "14.592 µW"
    assert coupled["rhs"]["display"] == "12 µW"
    change = next(p for p in failed["suggestions"]["parameter_changes"] if p["parameter"] == "n_flux_lines")
    assert change["suggested"] == "39" and change["verified"] is True
    passed = check(api, "quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw",
                   parameters={"n_flux_lines": {"value": "39", "unit": "count"}}, suggestions=True)
    assert passed["verdict"] == "REQUIREMENTS_MET"


def test_frontend_tissue_and_normal_product_share_the_same_pipeline(api):
    assert check(api, "bio_cryosection_frozen_tissue", "leica_cm1950_genA_vacuum_motor_objcool")["verdict"] == "REQUIREMENTS_MET"
    normal = check(api, "mat_electrical_resistance_low_temperature", "qd_dynacool_9T_eto_res")
    assert normal["verification"]["concrete_evaluation"]["verified_by_lean"] is True
    assert "sample.width.max" in normal["missing_information"]


def test_frontend_alternatives_and_comparison_are_real(api):
    search = data(api.find_compatible_equipment("mat_magnetoresistance_10T", confirmed=True, include_hypothetical_options=False))
    candidate = next(c for c in search["candidates"] if c["configuration_id"] == "qd_dynacool_14T_eto_vsm_hc")
    assert candidate["lean_verdict"] == "NEED_MORE_INFORMATION" and candidate["verified"] is False
    comparison = data(api.compare_equipment("mat_magnetoresistance_10T", ["qd_dynacool_9T_eto_res", "qd_dynacool_14T_eto_vsm_hc"], confirmed=True))
    assert [r["verdict"] for r in comparison["results"]] == ["DOES_NOT_MEET_REQUIREMENTS", "NEED_MORE_INFORMATION"]


def test_unknown_placeholder_is_not_numeric_evidence():
    base = {"id": "test", "source_url": "https://example.org", "document_title": "test",
            "evidence_status": "unknown", "accessed": "2026-10-31"}
    valid = Report()
    validate_evidence_record({**base, "normalized": {"kind": "unknown"}}, "test", valid)
    assert valid.ok
    for normalized in ({"value": 1, "unit": "K"}, {"kind": "unknown", "value": 1}):
        invalid = Report()
        validate_evidence_record({**base, "normalized": normalized}, "test", invalid)
        assert not invalid.ok


def test_unknown_installed_value_cannot_acquire_trusted_status(api):
    cfg = deepcopy(api._catalog.get_configuration("bluefors_ld400_hdw"))
    cap = next(c for c in cfg["capabilities"] if c["key"] == "magnetic_field.max")
    cap.update(value={"kind": "unknown"}, install="installed", evidence_status="manufacturer_specification")
    report = Report()
    validate_configuration(api._catalog, cfg, "test", report)
    assert any("UNKNOWN value" in str(e) for e in report.errors)
