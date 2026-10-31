"""Real-data compatibility tests: every verdict comes from the Lean binary on catalog documents."""
from conftest import outcome, verify

MR = "mat_magnetoresistance_10T"


def test_compatible_setup_accept(client):
    r = verify(client, "bio_cryosection_frozen_tissue", "leica_cm1950_genA_vacuum_motor_objcool")
    assert r["verdict"] == "ACCEPT"
    assert r["headline"] == "Requirements met"
    assert r["verified_by_lean"] is True
    assert all(c["outcome"] == "pass" for c in r["checks"] if c["mandatory"])
    # every passing check is traceable to evidence on both sides
    for c in r["checks"]:
        if c["mandatory"]:
            assert c["capability_evidence"] and all(not e.get("missing") for e in c["capability_evidence"])
            assert c["requirement_evidence"]


def test_temperature_incompatibility(client):
    # photoluminescence needs 4-300 K; the THMS600 + LNP96 is documented down to about -195 C (78 K)
    r = verify(client, "chem_temperature_dependent_photoluminescence", "linkam_thms600_lnp96_t96")
    assert r["verdict"] == "REJECT"
    assert outcome(r, "temperature.range") == "fail"
    assert "temperature.range" in r["failed_requirements"]


def test_sample_too_large(client):
    edit = [{"key": "sample.diameter.max", "constraint": {"kind": "at_least", "q": {"value": 30000, "unit": "um"}}}]
    r = verify(client, "chem_low_temperature_raman", "linkam_thms600_lnp96_t96", requirement_edits=edit)
    assert r["verdict"] == "REJECT"
    assert outcome(r, "sample.diameter.max") == "fail"     # documented 22 mm sample area


def test_missing_measurement_module(client):
    r = verify(client, "mat_electrical_resistance_low_temperature", "qd_dynacool_12T_vsm")
    assert r["verdict"] == "REJECT"
    assert outcome(r, "module.electrical_transport") == "fail"
    chk = next(c for c in r["checks"] if c["key"] == "module.electrical_transport")
    assert chk["capability"]["install"] == "optional_not_installed"


def test_insufficient_magnetic_field_9T_vs_14T(client):
    r9 = verify(client, MR, "qd_dynacool_9T_eto_res")
    r14 = verify(client, MR, "qd_dynacool_14T_eto_vsm_hc")
    assert r9["verdict"] == "REJECT" and outcome(r9, "magnetic_field.max") == "fail"
    assert outcome(r14, "magnetic_field.max") == "pass"
    # the overall result still accounts for the other requirements: transport sample size is undocumented
    assert r14["verdict"] == "NEED_MORE_INFORMATION"
    assert set(r14["missing_information"]) == {"sample.width.max", "sample.length.max", "sample.height.max"}
    # manufacturer evidence for the field values
    ev9 = next(c for c in r9["checks"] if c["key"] == "magnetic_field.max")["capability_evidence"]
    assert any("qdusa.com" in e["source_url"] and "9 T" in e["quote"] for e in ev9)


def test_missing_manufacturer_information(client):
    r = verify(client, "chem_low_temperature_raman", "linkam_thms600_heating_only")
    assert r["verdict"] == "NEED_MORE_INFORMATION"
    assert outcome(r, "temperature.range") == "unknown"


def test_different_configurations_of_same_cryostat(client):
    a = verify(client, "bio_cryosection_frozen_tissue", "leica_cm1950_genA_standard")
    b = verify(client, "bio_cryosection_frozen_tissue", "leica_cm1950_genA_vacuum_motor_objcool")
    assert a["equipment_id"] == b["equipment_id"] == "leica_cm1950"
    assert a["verdict"] == "REJECT" and b["verdict"] == "ACCEPT"
    assert outcome(a, "temperature.specimen_head.range") == "fail"


def test_unconfirmed_requirements_never_accept(client):
    r = verify(client, "bio_cryosection_frozen_tissue", "leica_cm1950_genA_vacuum_motor_objcool", confirmed=False)
    assert r["verdict"] == "NEED_MORE_INFORMATION"


def test_user_entered_instrument_value_and_undocumented_modification(client):
    ov = [{"key": k, "documented": True, "value": {"kind": "max", "q": {"value": 5000, "unit": "um"}}}
          for k in ("sample.width.max", "sample.length.max", "sample.height.max")]
    r = verify(client, MR, "qd_dynacool_14T_eto_vsm_hc", instrument_overrides=ov)
    assert r["verdict"] == "ACCEPT"
    assert r["configuration_id"].startswith("qd_dynacool_14T_eto_vsm_hc~mod:")   # never the catalog id
    assert next(c for c in r["checks"] if c["key"] == "sample.width.max")["capability"]["evidence_status"] == "user_entered"
    r2 = verify(client, MR, "qd_dynacool_14T_eto_vsm_hc",
                instrument_overrides=ov + [{"key": "magnetic_field.max", "documented": False, "note": "rewound"}])
    assert r2["verdict"] == "NEED_MORE_INFORMATION" and outcome(r2, "magnetic_field.max") == "unknown"


def test_unit_mismatch_is_unsupported_not_converted(client):
    edit = [{"key": "magnetic_field.max", "constraint": {"kind": "at_least", "q": {"value": 100000, "unit": "G"}}}]
    r = verify(client, MR, "qd_dynacool_14T_eto_vsm_hc", requirement_edits=edit)
    assert outcome(r, "magnetic_field.max") == "unsupported"
    assert r["verdict"] != "ACCEPT"


def test_every_catalog_pair_verdict_is_consistent_with_checks(client, catalog):
    """Over the whole real catalog: ACCEPT iff every mandatory check passes; any fail => REJECT."""
    from backend import lean_runner
    docs = [(catalog.lean_configuration(c), catalog.lean_experiment(e))
            for e in catalog.experiments.values() for c in catalog.configurations.values()]
    for r in lean_runner.run_batch(docs):
        mand = [c["outcome"] for c in r["checks"] if c["mandatory"]]
        if r["verdict"] == "ACCEPT":
            assert mand and all(o == "pass" for o in mand)
        elif "fail" in mand:
            assert r["verdict"] == "REJECT"
        else:
            assert r["verdict"] == "NEED_MORE_INFORMATION"
