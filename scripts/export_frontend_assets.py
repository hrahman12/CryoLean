"""Package existing computed research artifacts; does not fabricate or rerun data."""
import json
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
public=ROOT/'frontend/public/research';public.mkdir(parents=True,exist_ok=True)
names=['fig1_thermal_margin_3d','fig_mechanical_clearance_3d','fig_lean_z3_performance','fig_cross_industry_heatmap']
figures=[]
for name in names:
    p=ROOT/f'paper/figures/meta/{name}.json'
    if not p.exists():continue
    meta=json.loads(p.read_text(encoding='utf-8'));figures.append(meta)
    shutil.copy2(p,public/f'{name}-methodology.json')
    for source in [ROOT/f'paper/figures/{name}.svg',ROOT/f'paper/figures/{name}.pdf',ROOT/f'paper/data/{name}.json',ROOT/f'paper/interactive/{name}.html']:
        if source.exists():shutil.copy2(source,public/source.name)
(public/'figures.json').write_text(json.dumps(figures,ensure_ascii=False),encoding='utf-8')
print('Packaged',len(figures),'existing scientific figures with data and methodology.')
