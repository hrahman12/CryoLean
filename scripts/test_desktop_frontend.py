"""Production three-card integration test with real PyWebView, Lean and Z3."""
from __future__ import annotations
import json,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import webview
from cryolean import db
from cryolean.bridge import CryoLeanAPI

def main():
    report={'checks':[],'passed':False}
    temp=tempfile.TemporaryDirectory(prefix='cryolean-ui-');database=Path(temp.name)/'test.db';db.build_database(db_path=database)
    api=CryoLeanAPI(str(database))
    window=webview.create_window('CryoLean · Integration QA',str(ROOT/'frontend/dist/index.html'),js_api=api,width=1536,height=1060,hidden=True)
    def run():
        def js(code):return window.evaluate_js(code)
        def wait(expression,timeout=60):
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                try:
                    result=js(expression)
                    if result:return result
                except Exception:pass
                time.sleep(.15)
            raise AssertionError('Timed out: '+expression)
        def click(selector):
            wait(f'Boolean(document.querySelector({json.dumps(selector)}))')
            js(f'document.querySelector({json.dumps(selector)}).click()')
        def choose(selector,value):
            js(f"(()=>{{const e=document.querySelector({json.dumps(selector)});e.value={json.dumps(value)};e.dispatchEvent(new Event('change',{{bubbles:true}}));}})()")
        def record(name):report['checks'].append(name);print('PASS',name,flush=True)
        def verdict(text):wait(f"document.querySelector('[data-testid=verdict]')?.textContent.includes({json.dumps(text)})")
        def verify(text):
            click('[data-testid=review-setup]');wait('Boolean(document.querySelector("dialog[open] [data-testid=confirm]"))')
            assert not js('document.querySelector("[data-testid=confirm]").checked')
            assert js('document.querySelector("[data-testid=verify]").disabled')
            click('[data-testid=confirm]');click('[data-testid=verify]');verdict(text)
        try:
            wait("document.querySelector('.backend-state')?.textContent.includes('Live backend connected')")
            wait("document.querySelectorAll('canvas').length===2")
            assert js("document.querySelector('#industry').options.length") == 21
            record('full 20-industry catalog and two real WebGL canvases load')
            choose('#industry','quantum_computing_and_sensing')
            choose('#experiment','quantum_mxc_wiring_heat_budget')
            wait("document.querySelector('#cryostat').value==='bluefors_ld400_hdw'")
            wait("document.querySelector('.sample-preview')?.dataset.mechanism==='quantum_wiring'")
            record('experiment selection changes specimen and selects documented wiring configuration')
            verify("Doesn't meet requirements")
            wait("document.querySelector('[data-testid=verified-fix]')?.textContent.includes('39 count')")
            assert 'Not established' not in js("document.querySelector('[data-testid=suggested-fixes]').textContent")
            record('real Lean failure automatically yields a preverified 39-line fix')
            click('[data-testid=apply-fix]');verdict('Requirements met')
            assert js("document.querySelector('.repair-comparison')?.textContent.includes('Original:')")
            record('Apply Fix performs real Lean recheck and retains original failure')
            old_eid=js("document.querySelector('#experiment').value")
            choose('#cryostat','bluefors_ld250_manual_v2')
            assert js("document.querySelector('#experiment').value")==old_eid
            assert not js("Boolean(document.querySelector('[data-testid=verdict]'))")
            record('changing the machine preserves the experiment and invalidates the old PASS')
            click('[role=tab]:nth-child(2)');wait("Boolean(document.querySelector('#recorded-demo'))")
            verdict("Doesn't meet requirements")
            click('[data-testid=apply-fix]');verdict('Requirements met')
            record('recorded Demo B replays the actual repair inside the same three cards')
            choose('#recorded-demo','0');verdict("Doesn't meet requirements")
            click('[data-testid=review-setup]');verdict('Need more information')
            record('recorded Demo A preserves FAIL and UNKNOWN as distinct outcomes')
            choose('#recorded-demo','2');verdict("Doesn't meet requirements")
            click('[data-testid=review-setup]');verdict('Requirements met')
            record('Demo C distinguishes two probe arms from the required three')
            choose('#recorded-demo','3');click('[data-testid=review-setup]')
            wait("document.querySelector('.campaign-timeline')?.textContent.includes('23 h')")
            record('Demo D shows the genuine Lean-validated 23-hour schedule')
            click('[role=tab]:first-child')
            wait("!document.querySelector('#recorded-demo')")
            assert js("document.querySelector('#cryostat').value")=='bluefors_ld250_manual_v2'
            assert not js("Boolean(document.querySelector('[data-testid=verdict]'))")
            record('return to Live restores its own setup without importing recorded verdicts')
            choose('#industry','manufacturing_and_industrial_processing')
            choose('#cryostat','expansion_b_retsch_cryomill_documented')
            wait("document.querySelector('.lab-viewer')?.dataset.machineFamily==='mill'")
            choose('#cryostat','leica_cm1950_genA_vacuum_motor_objcool')
            wait("document.querySelector('.lab-viewer')?.dataset.machineFamily==='microtome'")
            record('equipment switches update fundamentally different machine assemblies')
            report['passed']=True
        except Exception as exc:
            report['error']=str(exc);print('FAIL',exc,flush=True)
        finally:
            output=ROOT/'frontend/test-results/desktop.json';output.parent.mkdir(exist_ok=True,parents=True);output.write_text(json.dumps(report,indent=2),encoding='utf-8');window.destroy()
    webview.start(run,debug=False)
    temp.cleanup()
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
