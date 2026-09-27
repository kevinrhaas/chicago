import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gradeCounts,selectSources,issueGroups,terrainCardId} from '../renderers/web/js/sources.js';
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
