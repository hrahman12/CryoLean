"""Evidence database, coverage registry and bridge surface."""
from cryolean.validation import validate_catalog
from conftest import data


def test_catalog_validates(api):
    rep = validate_catalog(api._catalog)
    assert rep.ok, "\n".join(map(str, rep.errors[:20]))


def test_initial_equipment_and_six_experiments_present(api):
    cat = api._catalog
    assert {"leica_cm1950", "linkam_thms600", "qd_ppms_dynacool", "bluefors_ld"} <= set(cat.equipment)
    six = {"bio_cryosection_frozen_tissue", "bio_cryo_fluorescence_vitrified", "chem_low_temperature_raman",
           "chem_phase_transition_pom", "mat_electrical_resistance_low_temperature", "mat_magnetometry_vsm"}
    assert six <= set(cat.experiments)


def test_every_manufacturer_value_has_traceable_source(api):
    cat = api._catalog
    for cfg in cat.configurations.values():
        for cap in cfg["capabilities"]:
            if cap["evidence_status"] == "manufacturer_specification":
                recs = cat.evidence_for(cap["evidence_ids"])
                assert any((r.get("source_url") or "").startswith("http") and r.get("quote") for r in recs), (cfg["id"], cap["key"])


def test_forty_properties_and_honest_status(api):
    props = data(api.get_physical_properties())["properties"]
    assert len(props) == 40 and [p["id"] for p in props] == list(range(1, 41))
    statuses = {p["status"] for p in props}
    assert "implemented_with_data" in statuses and statuses != {"implemented_with_data"}


def test_coverage_does_not_overclaim(api):
    cov = data(api.get_research_coverage())
    researched = {e["industry"] for e in data(api.list_experiments())["experiments"]}
    assert cov["industries"]["researched"] <= cov["industries"]["registered_or_known"]
    assert cov["industries"]["researched"] == len(researched)   # counts industries with real profiles, nothing more
    assert cov["missing_scientific_data"]["unknown_capabilities"]
    assert "does not mean every experiment" in cov["disclaimer"]


def test_required_bridge_methods_exist(api):
    for m in ["list_industries", "register_industry", "list_experiments", "register_experiment", "list_equipment",
              "get_equipment_details", "get_experiment_requirements", "check_compatibility", "find_compatible_equipment",
              "compare_equipment", "research_new_experiment", "get_verification_details", "get_research_coverage"]:
        assert callable(getattr(api, m)), m


def test_compare_equipment(api):
    r = data(api.compare_equipment("mat_magnetoresistance_10T", ["qd_dynacool_9T_eto_res", "qd_dynacool_14T_eto_vsm_hc", "oxford_teslatronpt_14T"], confirmed=True))
    assert [x["equipment"]["catalog_configuration_id"] for x in r["results"]] == ["qd_dynacool_9T_eto_res", "qd_dynacool_14T_eto_vsm_hc", "oxford_teslatronpt_14T"]
    assert r["results"][0]["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"
    assert any(row["check"] == "magnetic_field.max" for row in r["comparison_table"])


def test_equipment_details_show_unknowns_and_options(api):
    d = data(api.get_equipment_details("qd_dynacool_9T_eto_res"))
    cfg = d["configurations"][0]
    assert "module.vsm" in cfg["optional_accessories_not_installed"]
    assert cfg["unknown_capabilities"]


def test_result_has_all_required_sections(api):
    r = data(api.check_compatibility("quantum_mxc_wiring_heat_budget", "bluefors_ld400_hdw", confirmed=True))
    for k in ("equipment", "experiment", "verdict", "checks", "coupled_checks", "missing_information", "references",
              "verification", "suggestions", "user_message", "fingerprint", "lean_input"):
        assert k in r, k
    v = r["verification"]
    assert set(v) == {"generic_theorems", "concrete_evaluation", "source_data_validation", "physical_model_assumptions"}
    assert r["suggestions"]["conflicts"]["status"] == "unsat"
