"""Publish the genuinely evaluated full grid after scripts/build_grid.py."""
import csv,gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from cryolean import grid,lean_runner
from cryolean.catalog import Catalog

def main():
    cat=Catalog();summary=grid.summary(cat)
    assert summary['overall']['pairs']==len(cat.experiments)*len(cat.configurations)
    assert summary['lean_source_hash']==lean_runner.source_hash(),'Rebuild the grid with the current checker first'
    con=cat.connect();rows=con.execute('SELECT experiment_id,configuration_id,verdict,failing,missing,passes FROM grid ORDER BY experiment_id,configuration_id').fetchall();con.close()
    assert {r[0] for r in rows}==set(cat.experiments) and {r[1] for r in rows}==set(cat.configurations)
    output=ROOT/'docs/coverage';output.mkdir(parents=True,exist_ok=True)
    summary.update({'catalog_version':cat.version,'record_kind':'recorded_actual_lean_grid','engine':lean_runner.version(),
                    'platform':sys.platform,'note':'Historical catalog-wide evaluations of the prepared profiles. New visitor inputs are always checked live.'})
    (output/'full-grid-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    with (output/'full-grid.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['industry_id','experiment_id','configuration_id','verdict','failing_requirements','missing_information','mandatory_passes'])
        writer.writerows((cat.experiments[r[0]]['industry'],*r) for r in rows)
    (output/'full-grid.csv.gz').write_bytes(gzip.compress((output/'full-grid.csv').read_bytes(),mtime=0))
    public=ROOT/'frontend/public/coverage';public.mkdir(parents=True,exist_ok=True)
    for name in ['full-grid-summary.json','full-grid.csv','full-grid.csv.gz']:(public/name).write_bytes((output/name).read_bytes())
    print(json.dumps(summary['overall']))

if __name__=='__main__':main()
