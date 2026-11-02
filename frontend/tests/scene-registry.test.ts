import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {getSceneDefinition,hasInstalled} from '../src/scene/registry.ts';
import {getComponentForCheck} from '../src/scene/mappings/constraint-to-component.ts';
import {DEMO_SCENARIOS} from '../src/features/demo/demo-scenarios.ts';
import {EXPERIMENT_PRESENTATION,startingConfiguration} from '../src/features/catalog/experiment-presentation.ts';

const catalog=JSON.parse(readFileSync(new URL('../src/data/catalog.json',import.meta.url),'utf8'));
test('every researched experiment and equipment family has an explicit scene',()=>{
  for(const experiment of catalog.experiments)assert.notEqual(getSceneDefinition(experiment.id,'leica_cm1950',experiment.visualization).archetype,'unmapped');
  for(const equipment of catalog.equipment)assert.notEqual(getSceneDefinition('bio_cryosection_frozen_tissue',equipment.id,undefined,equipment.visualization).family,'unmapped');
  assert.equal(getSceneDefinition('bio_cryo_fluorescence_vitrified','linkam_thms600').archetype,'microscopy');
  assert.equal(getSceneDefinition('quantum_mk_vector_field_transport','bluefors_ld').archetype,'nano_transport');
});
test('unmapped data never silently turns into a magnet or a generic sample',()=>{
  assert.equal(getSceneDefinition('new','new').family,'unmapped');assert.equal(getSceneDefinition('new','new').archetype,'unmapped');
});
test('available family options are not rendered as installed modules',()=>{
  const cfg=catalog.configurations.qd_dynacool_9T_eto_res;
  assert.equal(hasInstalled(cfg,'module.vsm'),false);assert.equal(hasInstalled(cfg,'module.electrical_transport'),true);
  assert.equal(hasInstalled(catalog.configurations.bluefors_ld400_hdw,'magnetic_field.max'),false);
  assert.equal(hasInstalled(null,'optical_access'),false);
});
test('inferred and undocumented values are not treated as documented scene options',()=>{
  for(const status of ['unknown','inferred_estimate'])assert.equal(hasInstalled({capabilities:[{key:'module.vsm',install:'installed',evidence_status:status,value:{kind:'flag',b:true}}]} as any,'module.vsm'),false);
});
test('real constraint keys resolve to their physical component',()=>{
  assert.equal(getComponentForCheck({keys:['magnetic_field.max']})?.componentId,'magnet_solenoid');
  assert.equal(getComponentForCheck({keys:['optical_access']})?.componentId,'optical_windows');
  assert.equal(getComponentForCheck({keys:['sample.width.max']})?.componentId,'sample_mount');
  assert.equal(getComponentForCheck({kind:'coupled',model:'mxc_wiring_heat_budget'})?.componentId,'mxc_wiring_bundle');
});
test('demo manifest contains only real catalog inputs and no stored result or proof',()=>{
  for(const demo of DEMO_SCENARIOS){
    assert.ok(catalog.profiles[demo.experimentId]);assert.ok(catalog.configurations[demo.configurationId]);
    assert.ok(!('verdict' in demo));assert.ok(!('expectedOutcome' in demo));assert.ok(!('verification' in demo));
  }
});
test('read-only browser snapshot contains no verification outcomes or checker status',()=>{
  assert.ok(!('results' in catalog));assert.ok(!('leanStatus' in catalog));assert.ok(catalog.provenance.seed_sha256);
});
test('each researched experiment has a unique display title and a real starting configuration',()=>{
  const titles=catalog.experiments.map((e:any)=>EXPERIMENT_PRESENTATION[e.id]?.title??e.plain_name??e.name);
  assert.equal(new Set(titles).size,catalog.experiments.length);
  assert.ok(titles.every(Boolean));
  for(const e of catalog.experiments)assert.ok(catalog.configurations[startingConfiguration(e.id,catalog.equipment,e)]);
  assert.equal(startingConfiguration('unresearched',catalog.equipment),'');
});
test('every researched experiment has a distinct apparatus archetype',()=>{
  const archetypes=catalog.experiments.map((e:any)=>getSceneDefinition(e.id,'',e.visualization).archetype);
  assert.equal(new Set(archetypes).size,catalog.experiments.length);
});
test('the complete catalog has source-guided machine descriptors and multiple scientific mechanisms',()=>{
  assert.equal(catalog.experiments.length,204);assert.equal(Object.keys(catalog.configurations).length,220);
  for(const c of Object.values(catalog.configurations) as any[])assert.ok(c.visualization.family&&c.visualization.archetype===c.id);
  assert.ok(new Set(Object.values(catalog.configurations).map((c:any)=>c.visualization.family)).size>=30);
  assert.ok(new Set(catalog.experiments.map((e:any)=>e.visualization.mechanism)).size>=30);
});
