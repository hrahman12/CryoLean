"""Data provenance and API surface."""
from backend.validation import Report, validate_catalog, validate_configuration


def test_catalog_validates_without_errors(catalog):
    rep = validate_catalog(catalog)
    assert rep.ok, "\n".join(str(i) for i in rep.errors[:20])


def test_catalog_scale_and_configurations(catalog):
    assert {"leica_cm1950", "linkam_thms600", "qd_ppms_dynacool"} <= set(catalog.equipment)
    assert {"qd_dynacool_9T_eto_res", "qd_dynacool_14T_eto_vsm_hc"} <= set(catalog.configurations)
    for need in ("bio_cryosection_frozen_tissue", "bio_cryo_fluorescence_vitrified", "chem_low_temperature_raman",
                 "chem_temperature_dependent_photoluminescence", "mat_electrical_resistance_low_temperature", "mat_magnetoresistance_10T"):
        assert need in catalog.experiments


def test_every_sourced_value_has_url_title_quote(catalog):
    for cfg in catalog.configurations.values():
        for cap in cfg["capabilities"]:
            if cap["evidence_status"] == "manufacturer_specification":
                recs = catalog.evidence_for(cap["evidence_ids"])
                assert any(r.get("source_url", "").startswith("http") and r.get("quote") for r in recs), (cfg["id"], cap["key"])


def test_experiments_distinguish_reported_conditions_from_requirements(catalog):
    for ex in catalog.experiments.values():
        assert ex.get("sources"), ex["id"]
        assert "reported_conditions" in ex, ex["id"]
        for r in ex["requirements"]:
            assert r.get("rationale"), (ex["id"], r["key"])


def test_validator_rejects_unknown_with_number_and_wrong_unit(catalog):
    rep = Report()
    cfg = {"id": "x", "name": "x", "capabilities": [
        {"key": "magnetic_field.max", "value": {"kind": "max", "q": {"value": 9, "unit": "T"}},
         "install": "installed", "evidence_status": "manufacturer_specification", "evidence_ids": ["ev_qd_0001"]},
        {"key": "temperature.range", "value": {"kind": "range", "lo": {"value": 1800, "unit": "mK"}, "hi": {"value": 400000, "unit": "mK"}},
         "install": "installed", "evidence_status": "unknown", "evidence_ids": []},
        {"key": "optical_access", "value": {"kind": "unknown"}, "install": "installed", "evidence_status": "manufacturer_specification", "evidence_ids": ["ev_qd_0001"]},
        {"key": "not.a.key", "value": {"kind": "flag", "b": True}, "install": "installed", "evidence_status": "user_entered", "evidence_ids": []},
    ]}
    validate_configuration(cfg, "t", rep, catalog.vocabulary, catalog.evidence)
    msgs = " ".join(str(i) for i in rep.errors)
    assert "canonical unit" in msgs and "must not carry evidence_status 'unknown'" in msgs
    assert "must carry evidence_status 'unknown'" in msgs and "not in the vocabulary" in msgs


def test_openapi_schema_lists_required_endpoints(client):
    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    for p in ["/industries", "/experiments", "/equipment", "/configurations/{configuration_id}", "/verify", "/compare",
              "/search", "/ai/match", "/ai/explain", "/sessions", "/sessions/{session_id}/select-configuration",
              "/sessions/{session_id}/verify", "/sessions/{session_id}/result", "/evidence", "/coverage",
              "/research/requests", "/research/candidates", "/vocabulary/propose"]:
        assert p in paths, p
    assert "VerificationResult" in spec["components"]["schemas"]


def test_compare_across_configurations(client):
    r = client.post("/compare", json={"experiment_id": "mat_magnetoresistance_10T", "confirmed": True,
                                      "configuration_ids": ["qd_dynacool_9T_eto_res", "qd_dynacool_14T_eto_vsm_hc", "oxford_teslatronpt_14T"]}).json()
    assert [x["configuration_id"] for x in r["results"]] == ["qd_dynacool_9T_eto_res", "qd_dynacool_14T_eto_vsm_hc", "oxford_teslatronpt_14T"]
    assert r["results"][0]["verdict"] == "REJECT"


def test_evidence_endpoint(client):
    r = client.get("/evidence/ev_qd_0001").json()
    assert r["source_url"].startswith("https://qdusa.com") and r["quote"]
