#!/usr/bin/env node
// GPL-3.0-or-later. Actual parked adapter and popup composition, without WebGL.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { cardOpening, createPopup } from '../renderers/web/js/popup.js';
import { displayName } from '../renderers/web/js/display-name.js';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=p=>fs.readFileSync(path.join(ROOT,p),'utf8'),json=p=>JSON.parse(read(p));
const need=(v,m)=>{if(!v)throw Error(m)},hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const source=read('renderers/web/js/parked-transport.js');
need(/const spec = record\.models\[row\.model\]/.test(source)&&/card:\s*card\(row,\s*spec\)/.test(source),'Bind the actual placements-spec caller');
const start=source.indexOf('function card('),end=source.indexOf('/** Merge only static meshes',start);
need(start>=0&&end>start,'Actual production adapter range');
const card=vm.runInNewContext('('+source.slice(start,end).trim()+')',{}, {timeout:1000});
const record=json('data/transport/parked/placements.json'),metadata=json('renderers/web/transport/parked-brougham/brougham.json');
const row=record.scenes['1904'].find(r=>r.id==='prairie_parked_studebaker_brougham'),spec=record.models[row.model];
const oldDocument=globalThis.document;
globalThis.document={documentElement:{classList:{add(){},remove(){}}}};
const mount={innerHTML:'',addEventListener(){},setAttribute(){},removeAttribute(){},dispatchEvent(){}};
const popup=createPopup(mount,{}),controls=[];
try {
 function rendered(c){const opening=cardOpening(c.sidecar,displayName(c.sidecar,c.id));need(popup.show(c)===true,'Actual popup must open');return{opening,html:mount.innerHTML,design:popup.sections(c).design}}
 function valid(c,r){const attrs=c.sidecar.attributes,d=attrs.design_reference;return typeof attrs.vehicle_type.value==='string'&&!!attrs.vehicle_type.value&&typeof attrs.vehicle_type.note==='string'&&!!attrs.vehicle_type.note&&attrs.vehicle_type.confidence==='reconstructed'&&attrs.maker.confidence==='reconstructed'&&typeof d?.value==='string'&&!!d.value&&d.confidence==='attested'&&d.sources?.includes('studebaker_1893_illustrated_souvenir')&&r.design.includes(d.value)&&r.design.includes('attested')&&/before (?:1904|the scene date)/.test(d.note)&&/does not (?:establish|document) this/.test(d.note)&&!r.opening.composed&&/reconstructed, empty parked example/.test(r.opening.lead)&&/presence at this stop in 1904 are not attested/.test(r.opening.lead)&&!/(?:undefined|null|\[object Object\])/.test(r.html)}
 const actual=card(row,spec),shown=rendered(actual);need(valid(actual,shown),'Actual installed Brougham type/catalogue/lead must render without false presence');
 need(actual.sidecar.attributes.vehicle_type.value===spec.type&&actual.sidecar.attributes.vehicle_type.note===spec.basis&&JSON.stringify(actual.sidecar.attributes.design_reference)===JSON.stringify(spec.design_reference),'Existing valid type/basis/catalogue claim must remain exact');
 const before=JSON.stringify([row,spec,metadata]);
 const missingLead=structuredClone(actual);delete missingLead.sidecar.change_note;const fallback=rendered(missingLead);need(!valid(missingLead,fallback)&&fallback.opening.composed,'Missing explicit lead must be caught');controls.push({name:'Missing explicit lead',detected:true,actualFallbackLead:fallback.opening.lead});
 const rawClaim=structuredClone(actual);rawClaim.sidecar.attributes.design_reference=structuredClone(metadata.design_reference);const rawClaimShown=rendered(rawClaim);need(!valid(rawClaim,rawClaimShown)&&!rawClaimShown.design.includes(actual.sidecar.attributes.design_reference.value),'Unshaped catalogue object must actually lose its value cell and be caught');controls.push({name:'Unrendered raw catalogue object',detected:true});
 const missingType=structuredClone(actual);delete missingType.sidecar.attributes.vehicle_type.value;need(!valid(missingType,rendered(missingType)),'Missing type must be caught');controls.push({name:'Missing type value',detected:true});
 const falseMaker=structuredClone(actual);falseMaker.sidecar.attributes.maker.confidence='attested';need(!valid(falseMaker,rendered(falseMaker)),'Attested individual maker promotion must be caught');controls.push({name:'Attested individual maker promotion',detected:true});
 const legacy=json('tools/transport/brougham/legacy-card-contract.json'),obsolete=json('tools/transport/brougham/obsolete-c02-placement.json');need(legacy.cases.length===6,'Five live and one historical legacy card contracts');need(!record.scenes['1904'].some(r=>r.id===obsolete.id),'Obsolete C02 card has no current scene placement');
 for(const item of legacy.cases){need(hash(JSON.stringify(item.card))===item.card_json_sha256,'Recorded expected card must match its hash '+item.id);const r=record.scenes[item.scene].find(r=>r.id===item.id)??(item.id===obsolete.id?obsolete:null);need(r,'Current or explicit historical compatibility card '+item.id);const c=card(r,record.models[r.model]),shown=rendered(c);need(hash(JSON.stringify(c))===item.card_json_sha256,'Legacy card bytes changed '+item.id);need(JSON.stringify(shown.opening)===JSON.stringify(item.opening),'Legacy opening changed '+item.id);need(hash(shown.html)===item.popup_html_sha256&&hash(shown.design)===item.design_html_sha256,'Legacy popup HTML changed '+item.id)}
 need(JSON.stringify([row,spec,metadata])===before,'Adapter or popup mutated actual inputs');
 console.log(JSON.stringify({pass:true,scope:'Actual placements-spec card caller and actual popup show/opening/attribute rendering; no browser, geometry or world proof',actualOpening:shown.opening,actualInstalledTypeAndCatalogueWereAlreadyValid:true,rawSidecarIsNotTheRuntimeCardInput:true,parkedCardsMatchDeclaredContracts:legacy.cases.length,negativeControls:controls},null,2));
} finally {globalThis.document=oldDocument}

// Same registered Brougham entry also exercises actual near/mid runtime ownership.
await import('./transport/brougham/test_lod.mjs');
