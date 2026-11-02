"""Record the four actual README workflows using the real engine in an isolated DB."""
from __future__ import annotations
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cryolean import db, lean_runner
from cryolean.bridge import CryoLeanAPI


def read(envelope):
    if not envelope.get('ok'): raise RuntimeError(envelope.get('error'))
    return envelope['data']


def main():
    with tempfile.TemporaryDirectory(prefix='cryolean-recordings-') as temp:
        dbp=Path(temp)/'catalog.db'; db.build_database(db_path=dbp); a=CryoLeanAPI(str(dbp))
        def check(e,c,**opts): return read(a.check_compatibility(e,c,confirmed=True,suggestions=False,**opts))
        def event(result,note,**extra): return {'result':result,'note':note,**extra}
        a1=check('mat_magnetoresistance_10T','qd_dynacool_9T_eto_res')
        a2=check('mat_magnetoresistance_10T','qd_dynacool_14T_eto_vsm_hc')
        b1=check('quantum_mxc_wiring_heat_budget','bluefors_ld400_hdw')
        fixes=read(a.get_verified_repairs(b1['result_id']))
        fix=next(f for f in fixes['fixes'] if f['kind']=='parameter_adjustment')
        b2=read(a.apply_verified_repair(b1['result_id'],fix['id']))
        candidate=json.loads((ROOT/'research/new_industry/semiconductor_candidate_experiment.json').read_text(encoding='utf-8'))
        evidence=json.loads((ROOT/'research/new_industry/semiconductor_candidate_evidence.json').read_text(encoding='utf-8'))
        submitted=read(a.register_experiment(candidate,evidence,'recorded README workflow'))
        refused=a.check_compatibility(candidate['id'],'lakeshore_crx_vf',confirmed=True,suggestions=False)
        read(a.approve_candidate(submitted['id'],'recording reviewer'))
        c1=check(candidate['id'],'lakeshore_crx_4k')
        c2=check(candidate['id'],'lakeshore_crx_vf')
        exps=['bio_cryo_fluorescence_vitrified','chem_low_temperature_raman','chem_phase_transition_pom','mat_magnetoresistance_10T']
        durations={e:{'value':h,'unit':'h'} for e,h in zip(exps,[6,8,4,2])}
        schedule=read(a.schedule_campaign('lakeshore_crx_vf',exps,{'value':48,'unit':'h'},durations,None,True))
        tight=read(a.schedule_campaign('lakeshore_crx_vf',exps[:3],{'value':20,'unit':'h'},durations,None,True))
        d1=check(exps[-1],'lakeshore_crx_vf'); d2=check(exps[0],'lakeshore_crx_vf')
        demos=[
          {'id':'a','title':'A · 10 T on a 9 T magnet','events':[
            event(a1,'FAIL · The requested 10 T exceeds the documented 9 T maximum.'),
            event(a2,'NEED MORE INFORMATION · The 14 T field is sufficient, but mandatory sample-clearance evidence is missing. This is a diagnostic comparison, not a recommended fix.')]},
          {'id':'b','title':'B · Wiring heat-budget repair','featured':True,'events':[
            event(b1,'FAIL · 14.592 µW exceeds the documented 12 µW cooling budget.',repairs=fixes),
            event(b2,'PASS · Z3 proposed 39 flux lines; Lean accepted the exact candidate and then rechecked it: 11.985 µW ≤ 12 µW.',applied_fix=fix)]},
          {'id':'c','title':'C · A sourced semiconductor experiment','validation':submitted['validation'],'before_approval':refused,
           'events':[event(c1,'A research candidate was source-validated, refused verification before approval, and reviewed into the catalog. Lean now evaluates its separate compatibility: the installed two arms do not meet the three-arm requirement.'),
                     event(c2,'PASS · The documented CRX-VF configuration meets the reviewed semiconductor requirements. Scientific source validation and Lean compatibility are separate checks.')]},
          {'id':'d','title':'D · One cooldown, three experiments','events':[
            event(d1,'FAIL · Lean excludes the incompatible 10 T measurement before scheduling.'),
            event(d2,'The accepted experiments are packed by Z3 into a 23 h campaign, including 5 h cooldown. Lean validates the schedule.',schedule=schedule,tight_schedule=tight)]},
        ]
        ids={e['result']['experiment']['id'] for d in demos for e in d['events']}
        output={'kind':'recorded_real_lean_runs','recorded_at':datetime.now(timezone.utc).isoformat(),
                'lean_source_hash':lean_runner.source_hash(),'demos':demos,
                'profiles':{eid:read(a.get_experiment_requirements(eid)) for eid in ids}}
        destination=ROOT/'frontend/public/recordings.json';destination.parent.mkdir(exist_ok=True,parents=True)
        destination.write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        print('Recorded',len(demos),'README demonstrations;',sum(len(d['events']) for d in demos),'actual Lean events')
        print('Schedule validated:',schedule['schedule_ok'],'makespan:',schedule['z3']['makespan'])

if __name__=='__main__':main()
