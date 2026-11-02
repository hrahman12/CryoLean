"""Actual Lean regression tests for the PASS-only repair boundary."""
import copy
import json
import pytest
from cryolean import http_receipts, lean_runner
from conftest import data, check


def test_wiring_fix_is_verified_exact_and_rechecked_without_changing_requirements(fresh_api):
    original = check(fresh_api,"quantum_mxc_wiring_heat_budget","bluefors_ld400_hdw",suggestions=False)
    assert original["verdict"] == "DOES_NOT_MEET_REQUIREMENTS"
    found = data(fresh_api.get_verified_repairs(original["result_id"]))
    fix = next(f for f in found["fixes"] if f["kind"]=="parameter_adjustment")
    assert fix["changes"] == [{"parameter":"n_flux_lines","before":{"value":50,"unit":"count"},"after":{"value":"39","unit":"count"}}]
    assert all(f["verified"] and f["lean_verdict"]=="REQUIREMENTS_MET" and not f["hypothetical"] for f in found["fixes"])
    assert found["discarded"]["NEED_MORE_INFORMATION"]>0
    assert fix["lean_input"]["experiment"]["requirements"] == original["lean_input"]["experiment"]["requirements"]
    # Independently feed the advertised documents to the real checker.
    direct=lean_runner.check(**fix["lean_input"])
    assert direct["verdict"]=="REQUIREMENTS_MET"
    revised=data(fresh_api.apply_verified_repair(original["result_id"],fix["id"]))
    assert revised["verdict"]=="REQUIREMENTS_MET"
    assert revised["lean_input"]==fix["lean_input"]
    assert revised["verification"]["concrete_evaluation"]["lean_input_hash"]==fix["verification"]["concrete_evaluation"]["lean_input_hash"]
    assert data(fresh_api.get_verification_details(original["result_id"]))["verdict"]=="DOES_NOT_MEET_REQUIREMENTS"
    assert data(fresh_api.get_verification_details(revised["result_id"]))["repair_application"]["requirements_unchanged"]


def test_unknowns_are_diagnostics_never_working_fixes(fresh_api):
    r=check(fresh_api,"mat_magnetoresistance_10T","qd_dynacool_14T_eto_vsm_hc",suggestions=False)
    assert r["verdict"]=="NEED_MORE_INFORMATION"
    found=data(fresh_api.get_verified_repairs(r["result_id"]))
    assert all(f["lean_verdict"]=="REQUIREMENTS_MET" and f["verified"] for f in found["fixes"])
    if not found["fixes"]:
        assert found["message"]=="No verified solution found"
    assert not fresh_api.apply_verified_repair(r["result_id"],"client-invented-repair")["ok"]


def test_fix_cannot_cross_original_results_or_bypass_confirmation(fresh_api):
    r=check(fresh_api,"quantum_mxc_wiring_heat_budget","bluefors_ld400_hdw",suggestions=False)
    fix=data(fresh_api.get_verified_repairs(r["result_id"]))["fixes"][0]
    other=check(fresh_api,"mat_magnetoresistance_10T","qd_dynacool_9T_eto_res",suggestions=False)
    assert not fresh_api.apply_verified_repair(other["result_id"],fix["id"])["ok"]
    unconfirmed=data(fresh_api.check_compatibility("quantum_mxc_wiring_heat_budget","bluefors_ld400_hdw",suggestions=False))
    assert not fresh_api.get_verified_repairs(unconfirmed["result_id"])["ok"]


def test_signed_receipt_survives_cold_start_and_rejects_tampering(fresh_api):
    r=check(fresh_api,"quantum_mxc_wiring_heat_budget","bluefors_ld400_hdw",suggestions=False)
    fix=data(fresh_api.get_verified_repairs(r["result_id"]))["fixes"][0]
    receipt=http_receipts.issue(fresh_api,r["result_id"])
    con=fresh_api._catalog.connect()
    with con: con.execute("DELETE FROM results WHERE id=?",(r["result_id"],))
    con.close()
    http_receipts.restore(fresh_api,r["result_id"],receipt)
    assert data(fresh_api.apply_verified_repair(r["result_id"],fix["id"]))["verdict"]=="REQUIREMENTS_MET"
    with pytest.raises(ValueError): http_receipts.restore(fresh_api,r["result_id"],receipt[:-1]+('1' if receipt[-1]!='1' else '2'))


def test_changed_requirements_or_catalog_invalidate_verified_fixes(fresh_api):
    r=check(fresh_api,"quantum_mxc_wiring_heat_budget","bluefors_ld400_hdw",suggestions=False)
    fix=data(fresh_api.get_verified_repairs(r["result_id"]))["fixes"][0]
    fresh_api._catalog.version+='changed'
    failure=fresh_api.apply_verified_repair(r["result_id"],fix["id"])
    assert not failure["ok"] and failure["error"]["code"]=="stale_result"


def test_web_bridge_uses_the_same_engine_and_no_mutation_endpoints(fresh_api,monkeypatch):
    from fastapi.testclient import TestClient
    from cryolean import server
    monkeypatch.setattr(server,"_api",fresh_api)
    client=TestClient(server.app)
    first=client.post('/api/bridge',json={"method":"check_compatibility","args":["quantum_mxc_wiring_heat_budget","bluefors_ld400_hdw",None,None,True,None,False]}).json()
    assert first["data"]["verdict"]=="DOES_NOT_MEET_REQUIREMENTS"
    rid=first["data"]["result_id"]
    found=client.post('/api/bridge',json={"method":"get_verified_repairs","args":[rid],"receipt":first["receipts"][rid]}).json()
    assert found['ok'],found
    fix=found["data"]["fixes"][0]
    applied=client.post('/api/bridge',json={"method":"apply_verified_repair","args":[rid,fix["id"]],"receipt":found["receipts"][rid]}).json()
    assert applied["data"]["verdict"]=="REQUIREMENTS_MET"
    assert client.post('/api/bridge',json={"method":"register_modification","args":[]}).status_code==422
    assert client.post('/api/bridge',json={"method":"check_compatibility","args":["quantum_mxc_wiring_heat_budget","bluefors_ld400_hdw",None,None,True,[{"status":"installed_documented"}],False]}).status_code==422
