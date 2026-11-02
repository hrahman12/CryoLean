import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const data=JSON.parse(readFileSync(new URL('../public/research/lean-verdict-heatmap.json',import.meta.url),'utf8'));
const verdictName=Object.fromEntries(Object.entries(data.verdict_index).map(([name,value])=>[value,name]));

test('featured heatmap is the exact 180 verdict set from site data',()=>{
 assert.equal(data.featured.industries.length,20);
 assert.equal(Object.keys(data.featured.verdicts).length,180);
 assert.deepEqual(data.featured.counts,{REQUIREMENTS_MET:113,DOES_NOT_MEET_REQUIREMENTS:66,NEED_MORE_INFORMATION:1});
 const counts:Record<string,number>={};
 for(const record of Object.values(data.featured.verdicts) as any[])counts[record.verdict]=(counts[record.verdict]||0)+1;
 assert.deepEqual(counts,data.featured.counts);
 for(const industry of data.featured.industries){
  assert.equal(industry.experiments.length,3);
  assert.equal(industry.configurations.length,3);
  for(const experiment of industry.experiments)for(const configuration of industry.configurations)assert.ok(data.featured.verdicts[`${experiment.id}|${configuration.id}`]);
 }
});

test('all-pairs heatmap preserves every saved Lean verdict and exact totals',()=>{
 const flat=data.matrix.flat();
 assert.equal(flat.length,204*220);
 const counts:Record<string,number>={};
 for(const value of flat)counts[verdictName[value]]=(counts[verdictName[value]]||0)+1;
 assert.deepEqual(counts,{
  DOES_NOT_MEET_REQUIREMENTS:30299,
  NEED_MORE_INFORMATION:11463,
  REQUIREMENTS_MET:3118,
 });
 assert.equal(Object.values(counts).reduce((a:number,b:any)=>a+b,0),44880);
});

test('filtered heatmap views are visibility-only subsets of the saved matrix',()=>{
 const flat=data.matrix.flat();
 for(const view of ['plausible','same_industry']){
  const mask=data.masks[view];
  assert.equal(mask.length,flat.length);
  assert.ok(mask.every((value:number)=>value===0||value===1));
  const counts:Record<string,number>={};
  flat.forEach((value:number,index:number)=>{if(mask[index])counts[verdictName[value]]=(counts[verdictName[value]]||0)+1});
  assert.deepEqual(counts,data.counts[view]);
  for(const verdict of Object.keys(data.grid_meta.counts))assert.ok((counts[verdict]||0)<=data.grid_meta.counts[verdict]);
 }
});

test('unknown documented basics stay visible in the plausible-pairs mask',()=>{
 assert.match(data.filter_method.plausible,/Unknown values stay visible/);
 assert.equal(data.top_missing.all.length,10);
 assert.ok(data.top_missing.all.every((item:any)=>item.key&&item.count>0));
});
