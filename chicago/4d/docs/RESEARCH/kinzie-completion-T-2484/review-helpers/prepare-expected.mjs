/** External T2484 read-only published pin. Run only after retained native adoption and final 7 fresh photo records. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import cp from 'node:child_process';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const opts=Object.fromEntries(process.argv.slice(2).map((v,i,a)=>v.startsWith('--')?[v.slice(2),a[i+1]]:null).filter(Boolean));
for(const key of ['root','published-root','source-sha','native-run','native-commit','published-source-sha','build-prefix','out'])assert(opts[key],`--${key} required`);
for(const key of ['source-sha','native-commit','published-source-sha'])assert(/^[a-f0-9]{40}$/.test(opts[key]),key);
assert(/^\d+$/.test(opts['native-run']));
const root=path.resolve(opts.root),published=path.resolve(opts['published-root']),out=path.resolve(opts.out);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const bind=p=>{const b=fs.readFileSync(p);return {path:p,bytes:b.length,sha256:sha(b)};};
const pinnedBytes=rel=>cp.execFileSync('git',['show',`${opts['published-source-sha']}:chicago/4d/${rel}`],{cwd:root,maxBuffer:32*1024*1024});
const exact=(rel,dst)=>{const b=pinnedBytes(rel),r=bind(dst);assert.equal(sha(b),r.sha256,`published pin differs ${rel}`);const stored=path.join(path.dirname(out),'immutable-published-source',rel);fs.mkdirSync(path.dirname(stored),{recursive:true});fs.writeFileSync(stored,b);return {source:bind(stored),published:r,pin:{commit:opts['published-source-sha'],path:`chicago/4d/${rel}`}};};
const build=JSON.parse(fs.readFileSync(path.join(published,'build.json')));assert(String(build.version).startsWith(opts['build-prefix']));
const master=read('assets/manifest.json'),web=read('assets/manifest.web.json'),planting=read('data/flora/plantings/kinzie_house_1812_trees.json');
assert.equal(planting.stems.length,6);assert.equal(planting.stems.filter(s=>s.species==='populus_nigra_italica').length,4);assert.equal(planting.stems.filter(s=>s.species==='populus_deltoides').length,2);
const expected={kind:'FINAL_T2484_NATIVE_AND_PUBLISHED_PIN_NOT_EXECUTED_UI',source_sha:opts['source-sha'],native_run:opts['native-run'],native_commit:opts['native-commit'],published_source_sha:opts['published-source-sha'],build_prefix:opts['build-prefix'],build,prepared_from:root,published_root:published,assets:{},sidecars:{},documents:{},targets:['kinzie_house_1812','kinzie_house_1812_green'],planting};
for(const id of expected.targets){
 const rel=`data/sidecars/1812/${id}.json`,sc=read(rel),key=path.basename(sc.asset);assert.equal(sc.id,id);assert.equal(sc.scene,'1812');assert.equal(sc.target_date,'1812-08-14');assert.equal(master.assets[key]?.structure_id,id);assert(web.masters[key]);
 assert(fs.readFileSync(path.join(root,`data/structures/${id}.json`)).equals(pinnedBytes(`data/structures/${id}.json`)),'structure source changed since published pin');
 const pub=JSON.parse(fs.readFileSync(path.join(published,rel)));for(const field of ['id','phase','scene','target_date','grade','placement','footprint','attributes','citations'])assert.deepEqual(pub[field],sc[field],`${id}/${field}`);
 const m=bind(path.join(root,'assets/gltf',key)),w=bind(path.join(root,'assets/web',key)),p=bind(path.join(published,'data/gltf',key));assert.equal(p.sha256,w.sha256,`${id}: exact published WEB copy required; qualify any actual transform separately rather than ignore`);
 expected.assets[id]={asset:key,master:m,web:w,published:p,masterRow:master.assets[key],webRow:web.masters[key]};
 expected.sidecars[id]={document:pub,files:exact(rel,path.join(published,rel))};
}
for(const rel of ['data/pictures/1812.json','data/liberties.json','data/flora/plantings/kinzie_house_1812_trees.json'])expected.documents[rel]=exact(rel,path.join(published,rel));
expected.documents.build={published:bind(path.join(published,'build.json'))};
const pictures=JSON.parse(fs.readFileSync(path.join(published,'data/pictures/1812.json'))),libs=JSON.parse(fs.readFileSync(path.join(published,'data/liberties.json')));
expected.pictures=pictures.by_structure.kinzie_house_1812??[];
expected.liberty=libs.liberties.find(l=>l.id==='L-kinzie-house-completion-2484');assert(expected.liberty);for(const id of expected.targets)assert(expected.liberty.subjects.includes(id));
for(const word of ['whitewash','17','poplar','door'])assert(JSON.stringify(expected.liberty).toLowerCase().includes(word));
const gate=await import(pathToFileURL(path.join(root,'tools/image_gate.mjs')).href);assert.deepEqual(gate.gateFor(expected.targets),[]);expected.final_photo_gate=gate.viewsOf('kinzie_house_1812').map(v=>({view:v.view,camera:bind(v.cameraFile),match:bind(v.matchFile),record:JSON.parse(fs.readFileSync(v.matchFile))}));
assert.equal(expected.final_photo_gate.length,7);assert(expected.final_photo_gate.every(v=>v.record.verdict==='matches'&&!v.record.differences.some(d=>d.status==='open')));
expected.review_ids=fs.readdirSync(path.join(root,'data/sidecars/1812')).filter(f=>f.endsWith('.json')).map(f=>read(`data/sidecars/1812/${f}`)).filter(s=>s.review_required===true).map(s=>{assert.equal(s.scene,'1812');return s.id;}).sort();
fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(expected,null,2)+'\n');console.log(JSON.stringify({status:'PIN_PREPARED_NOT_UI_PASS',out,build,stems:6,assets:2,photo_gate:7}));
