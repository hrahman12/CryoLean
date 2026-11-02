import test from 'node:test';
import assert from 'node:assert/strict';
import * as client from '../src/services/cryolean-client.ts';

function bridge(api:Record<string,Function>) { (globalThis as any).window=Object.assign(new EventTarget(),{pywebview:{api}}); }
const result={verdict:'REQUIREMENTS_MET',verification:{concrete_evaluation:{verified_by_lean:true}}};
test('the canonical JS client unwraps once and forwards exact options in contract order',async()=>{
  let args:unknown[]=[];
  bridge({check_compatibility:async(...values:unknown[])=>{args=values;return {ok:true,data:result};}});
  const q={current:{value:'0.125',unit:'uA'}};
  assert.deepEqual(await client.checkCompatibility('experiment','configuration',{parameters:q,confirmed:true}),result);
  assert.deepEqual(args,['experiment','configuration',q,null,true,null,true]);
});
test('ordinary browser checks reject immediately without waiting for pywebviewready',async()=>{
  (globalThis as any).window=new EventTarget();const start=Date.now();
  await assert.rejects(client.checkCompatibility('e','c'),(error:any)=>error.code==='bridge_unavailable'&&error.verdict===null);
  assert.ok(Date.now()-start<1000);
});
test('Lean unavailable errors survive as errors with a null verdict',async()=>{
  bridge({check_compatibility:async()=>({ok:false,error:{code:'lean_unavailable',message:'Checker missing',verdict:null}})});
  await assert.rejects(client.checkCompatibility('e','c'),(error:any)=>error.code==='lean_unavailable'&&error.verdict===null);
});
test('a frontend may not display an unconfirmed backend evaluation as a real verdict',async()=>{
  bridge({check_compatibility:async()=>({ok:true,data:{verdict:'REQUIREMENTS_MET',verification:{concrete_evaluation:{verified_by_lean:false}}}})});
  await assert.rejects(client.checkCompatibility('e','c'),(error:any)=>error.code==='invalid_response');
});
test('unknown remains unknown and never earns a verified badge',async()=>{
  const unknown={...result,verdict:'NEED_MORE_INFORMATION'};
  bridge({check_compatibility:async()=>({ok:true,data:unknown})});
  const actual=await client.checkCompatibility('e','c');assert.equal(actual.verdict,'NEED_MORE_INFORMATION');assert.equal(client.isVerified(actual),false);
});
test('search and comparison enforce explicit requirement confirmation',async()=>{
  let calls=0;bridge({find_compatible_equipment:async()=>{calls++;},compare_equipment:async()=>{calls++;}});
  await assert.rejects(client.findCompatibleEquipment('e',{confirmed:false}));
  await assert.rejects(client.compareEquipment('e',['a','b'],{confirmed:false}));assert.equal(calls,0);
});
test('an ordinary alternative search excludes hypothetical options',async()=>{
  let args:unknown[]=[];bridge({find_compatible_equipment:async(...values:unknown[])=>{args=values;return {ok:true,data:{candidates:[]}};}});
  await client.findCompatibleEquipment('e',{confirmed:true});assert.deepEqual(args,['e',null,null,true,10,false]);
});
