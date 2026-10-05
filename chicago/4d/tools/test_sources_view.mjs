import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gradeCounts,selectSources,issueGroups,terrainCardId,sceneRows,edgeUse} from '../renderers/web/js/sources.js';
const e=(claim,confidence,locator=null)=>({entity_type:'structure',entity_id:'a',claim,confidence,locator});
assert.deepEqual(gradeCounts([e('roof','attested'),e('size','inferred'),e('size','inferred','another issue'),e('size','reconstructed')]),[[1,1,0],[1,0,0]]);
const rows=JSON.parse(fs.readFileSync(new URL('../data/sidecars/1835/sources/index.json',import.meta.url))).sources;
const base={all:false,query:'',type:'',tier:'',use:'',sort:'claims'};
assert.equal(selectSources(rows,base).length,rows.filter(r=>r.use==='scene').length);
assert.equal(selectSources(rows,{...base,all:true}).length,rows.length);
for(const key of ['type','tier','use'])for(const v of new Set(rows.map(r=>r[key])))assert.ok(selectSources(rows,{...base,all:true,[key]:v}).every(r=>r[key]===v));
assert.ok(selectSources(rows,{...base,query:'Andreas'}).every(r=>/andreas/i.test(r.citation+' '+r.source_id)));
for(const sort of ['claims','entities']){const found=selectSources(rows,{...base,sort});assert.ok(found.every((r,i)=>!i||found[i-1].counts[sort]>=r.counts[sort]));}
for(const sort of ['date','title']){const found=selectSources(rows,{...base,sort});assert.ok(found.every((r,i)=>!i||(sort==='date'?String(found[i-1].date??'').localeCompare(String(r.date??'')):found[i-1].citation.localeCompare(r.citation))<=0));}
const known=rows.find(r=>r.source_id==='andreas_1884_v1');assert.equal(known.type,'book');assert.equal(known.tier,3);assert.equal(known.date,'1884');
for(const row of rows){const file=JSON.parse(fs.readFileSync(new URL(`../data/sidecars/1835/sources/${row.source_id}.json`,import.meta.url)));const counts=gradeCounts(file.edges);assert.deepEqual(row.counts.grades,counts,row.source_id);assert.equal(counts[0].reduce((a,b)=>a+b,0),row.counts.claims);assert.equal(counts[1].reduce((a,b)=>a+b,0),row.counts.entities);}
assert.equal(issueGroups([e('a','attested','chicago_democrat_1834_12_03 page 3 column 5'),e('b','inferred',null)])[0][0],'1834-12-03');
console.log(`PASS Sources view: ${rows.length} sources, every confidence count independently checked, mixed-tier deduplication, filters, sort, issue grouping`);

assert.equal(terrainCardId({claim:'reaches[main_stem]'},[{id:'reaches.main_stem'}]),'reaches.main_stem');
assert.equal(terrainCardId({claim:'surface_materials[1]'},[{id:'water'},{id:'surface_materials.a'},{id:'surface_materials.b'}]),'surface_materials.b');
assert.equal(terrainCardId({claim:'record'},[{id:'water'}]),undefined);

// T-2079: another scene's Sources default to the sources ITS records cite, over the one catalog.
for(const scene of ['1812','1904']){
  const map=JSON.parse(fs.readFileSync(new URL(`../data/sidecars/${scene}/sources/uses.json`,import.meta.url)));
  const own=sceneRows(rows,map),listed=selectSources(own,base);
  assert.equal(map.scene,scene);assert.equal(own.length,rows.length);assert.ok(listed.length>0,scene);
  assert.deepEqual(own.map(r=>({...r,use:undefined})),rows.map(r=>({...r,use:undefined})),'only use differs');
  for(const r of listed){const file=JSON.parse(fs.readFileSync(new URL(`../data/sidecars/1835/sources/${r.source_id}.json`,import.meta.url)));
    assert.ok(file.edges.some(e=>edgeUse(e,scene)==='scene'),`${scene} lists ${r.source_id} with no edge it draws`);}
  for(const r of own.filter(r=>r.use!=='scene')){const file=JSON.parse(fs.readFileSync(new URL(`../data/sidecars/1835/sources/${r.source_id}.json`,import.meta.url)));
    assert.ok(!file.edges.some(e=>edgeUse(e,scene)==='scene'),`${scene} leaves out ${r.source_id} though an edge is its own`);}
}
const in1904=selectSources(sceneRows(rows,JSON.parse(fs.readFileSync(new URL('../data/sidecars/1904/sources/uses.json',import.meta.url)))),base).map(r=>r.source_id);
assert.ok(in1904.includes('habs_glessner_house_il_1015_drawings')&&!in1904.includes('andreas_1884_v1'),'1904 lists the Glessner drawings and not the 1835 town history');
assert.throws(()=>sceneRows(rows,{scene:'x',uses:{}}),/No use for/);
assert.equal(edgeUse({use:'scene'},'1904'),'other_scene');assert.equal(edgeUse({use:'research',scenes:['1904']},'1904'),'scene');
assert.equal(edgeUse({use:'other_scene',scenes:['1904']}),'other_scene');
console.log(`PASS Sources per scene: 1812 and 1904 list exactly the sources their own records cite (${in1904.length} in 1904)`);
