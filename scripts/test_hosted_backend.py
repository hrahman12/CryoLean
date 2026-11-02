"""Anonymous production smoke tests against real Lean; never cache fake results."""
import argparse,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
import requests

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--url',default='https://frontend-pied-five-58.vercel.app');a=ap.parse_args()
    session=requests.Session();report={'url':a.url,'checked_at':datetime.now(timezone.utc).isoformat(),'checks':[]}
    def call(method,*args,receipt=None):
        r=session.post(a.url+'/api/bridge',json={'method':method,'args':args,'receipt':receipt},timeout=90)
        assert r.status_code==200,(r.status_code,r.text[:300]);e=r.json();assert e.get('ok'),e.get('error');return e
    health=session.get(a.url+'/api/health',timeout=60).json()
    assert health['lean']['lean_available'] and health['lean']['selftest_passed']
    report['catalog']=health['catalog'];report['lean_source_hash']=health['lean_source_hash']
    report['checks'].append('Anonymous health: compiled Linux Lean available, real selftest passed')
    cases=[('chem_phase_transition_pom','linkam_thms600_lnp96_t96','REQUIREMENTS_MET'),('mat_magnetoresistance_10T','qd_dynacool_9T_eto_res','DOES_NOT_MEET_REQUIREMENTS'),('mat_magnetoresistance_10T','qd_dynacool_14T_eto_vsm_hc','NEED_MORE_INFORMATION')]
    for eid,cid,expected in cases:
        result=call('check_compatibility',eid,cid,None,None,True,None,False)['data']
        assert result['verdict']==expected
        assert result['verification']['concrete_evaluation']['verified_by_lean']
        assert result['verdict_card']['axiom_audit']=='current'
        report['checks'].append(f'Live {expected}: {eid} / {cid}')
    original=call('check_compatibility','quantum_mxc_wiring_heat_budget','bluefors_ld400_hdw',None,None,True,None,False)
    r=original['data'];rid=r['result_id'];assert r['verdict']=='DOES_NOT_MEET_REQUIREMENTS'
    found=call('get_verified_repairs',rid,receipt=original['receipts'][rid])
    fixes=found['data']['fixes'];assert fixes and all(f['verified'] and f['lean_verdict']=='REQUIREMENTS_MET' and not f['hypothetical'] for f in fixes)
    fix=next(f for f in fixes if f['kind']=='parameter_adjustment')
    assert fix['changes'][0]['after']=={'value':'39','unit':'count'}
    applied=call('apply_verified_repair',rid,fix['id'],receipt=found['receipts'][rid])['data']
    assert applied['verdict']=='REQUIREMENTS_MET' and applied['lean_input']==fix['lean_input']
    assert applied['verification']['concrete_evaluation']['lean_input_hash']==fix['verification']['concrete_evaluation']['lean_input_hash']
    assert applied['lean_input']['experiment']['requirements']==r['lean_input']['experiment']['requirements']
    report['checks'].append('Real hosted repair: 50 → 39 flux lines; fresh PASS; same verified hash; requirements unchanged')
    report['repair']={'changes':fix['changes'],'input_hash':fix['verification']['concrete_evaluation']['lean_input_hash'],'discarded':found['data']['discarded']}
    check=session.post(a.url+'/api/check',json={'experiment_id':'chem_phase_transition_pom','configuration_id':'linkam_thms600_lnp96_t96','confirmed':True,'suggestions':False},timeout=60).json()
    assert check['ok'] and check['data']['verdict']=='REQUIREMENTS_MET';report['checks'].append('Real /api/check route passed')
    recordings=session.get(a.url+'/recordings.json',timeout=30).json();assert len(recordings['demos'])==4
    report['checks'].append('Four recorded README artifacts publicly available')
    out=Path(__file__).resolve().parents[1]/'frontend/test-results/hosted.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'passed':len(report['checks']),'catalog':report['catalog'],'source_hash':report['lean_source_hash']}))

if __name__=='__main__':main()
