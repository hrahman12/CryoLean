import test from 'node:test';
import assert from 'node:assert/strict';
import { initialSetup, setupReducer } from '../src/features/verification/setup-state.ts';

function result(experimentId=initialSetup.experimentId,configurationId=initialSetup.configurationId) {
  return {verdict:'REQUIREMENTS_MET',experiment:{id:experimentId},equipment:{configuration_id:configurationId}} as any;
}
function pending() {
  const confirmed=setupReducer(initialSetup,{type:'confirm',value:true});
  return setupReducer(confirmed,{type:'start',revision:confirmed.revision});
}
test('explicit confirmation gates checks',()=>{
  assert.equal(setupReducer(initialSetup,{type:'start',revision:0}).pending,null);
});
test('equipment switches retain experiment and user parameters but invalidate the result',()=>{
  let state=pending();state=setupReducer(state,{type:'success',revision:state.revision,result:result()});
  state={...state,parameters:{current:{value:'0.25',unit:'uA'}}};
  const next=setupReducer(state,{type:'equipment',id:'other'});
  assert.equal(next.experimentId,state.experimentId);assert.deepEqual(next.parameters,state.parameters);
  assert.equal(next.result,null);assert.equal(next.pending,null);assert.equal(next.confirmed,true);
});
test('late responses cannot restore a pass after an equipment change',()=>{
  const original=pending();const changed=setupReducer(original,{type:'equipment',id:'different'});
  assert.deepEqual(setupReducer(changed,{type:'success',revision:original.revision,result:result()}),changed);
});
test('late errors cannot replace the current setup state',()=>{
  const original=pending();const changed=setupReducer(original,{type:'experiment',id:'new'});
  assert.deepEqual(setupReducer(changed,{type:'error',revision:original.revision,message:'Old error'}),changed);
});
test('responses must belong to the selected experiment and configuration',()=>{
  const state=pending();const next=setupReducer(state,{type:'success',revision:state.revision,result:result('wrong')});
  assert.equal(next.result,null);assert.match(next.error!,/does not match/);
});
test('parameter and requirement edits clear confirmation and the result',()=>{
  const state=pending();
  for(const action of [{type:'parameter',name:'n_flux_lines',quantity:{value:'39',unit:'count'}},
    {type:'edit',edit:{key:'magnetic_field.max',constraint:{kind:'at_least',q:{value:'9.5',unit:'T'}}}}] as any[]) {
    const next=setupReducer(state,action);assert.equal(next.confirmed,false);assert.equal(next.result,null);assert.equal(next.pending,null);
  }
});
test('selecting a demo is an ordinary unconfirmed experiment selection',()=>{
  const next=setupReducer(pending(),{type:'experiment',id:'chem_phase_transition_pom',configurationId:'linkam_thms600_lnp96_t96'});
  assert.equal(next.confirmed,false);assert.equal(next.result,null);assert.deepEqual(next.edits,[]);
});
test('a real verification error carries no verdict',()=>{
  const state=pending();const next=setupReducer(state,{type:'error',revision:state.revision,message:'lean_unavailable'});
  assert.equal(next.result,null);assert.equal(next.error,'lean_unavailable');assert.equal(next.pending,null);
});
