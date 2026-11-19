#!/usr/bin/env node
/** Lessons must be based on the chosen telling's real cited claims, across all groups.
 * Includes hostile URLs, unavailable/adult variants, source gaps, and print lifecycle. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { lessonGroups, lessonJaunts, lessonDocuments, lessonModel, safeSourceURL, renderLesson, printLesson, LESSON_BANDS } from '../renderers/web/js/apps/lesson-guides.js';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA = process.env.C4D_LESSON_DATA ?? path.join(ROOT, 'data');
const read = p => JSON.parse(fs.readFileSync(path.join(DATA, p)));
let groupCount = 0, tellingCount = 0;
for (const year of ['1812', '1835', '1904']) {
  const rows = read(`sidecars/${year}/jaunts/catalog.json`).jaunts;
  const groups = lessonGroups(rows);
  assert(groups.length > 0);
  assert.deepEqual(new Set(groups), new Set(rows.filter(r => r.availability === 'available' && r.audience !== 'adults').map(r => r.menu_group)));
  groupCount += groups.length;
  for (const group of groups) {
    let seen = 0;
    for (const band of LESSON_BANDS) for (const row of lessonJaunts(rows, group, band)) {
      const jaunt = read(`sidecars/${year}/jaunts/${row.id}.json`);
      const model = lessonModel({ year, group, band, row, jaunt });
      assert.equal(model.title, jaunt.title);
      assert(model.question && !model.question.includes('{year}'));
      assert(model.documents.length > 0 && model.documents.length <= 3, `${row.id}: cited documents`);
      for (const document of model.documents) {
        const source = jaunt.citations.find(c => c.source_id === document.id);
        assert(source);
        assert.equal(document.citation, source.citation);
        assert(document.claims.length > 0 && document.claims.length <= 2);
        for (const claim of document.claims) assert(jaunt.evidence.some(e => e.text === claim.text && e.sources.includes(document.id)), 'claim and citation remain joined');
      }
      if (model.hasLinkedPrimary) assert(model.documents.some(d => [1, 2].includes(d.tier) && (d.url || d.archive)));
      seen++; tellingCount++;
    }
    assert(seen > 0, `${year}/${group}: a lesson is available`);
  }
}
assert.equal(groupCount, 10, 'all currently available year/group combinations; Build log is unavailable');
assert(tellingCount > 150, 'covers the grade variants, not only a few featured jaunts');
assert.equal(safeSourceURL('javascript:alert(1)'), '');
assert.equal(safeSourceURL('data:text/html,bad'), '');
assert.equal(safeSourceURL('/relative'), '');
assert.equal(safeSourceURL('https://example.org/source'), 'https://example.org/source');
assert.deepEqual(lessonGroups([{menu_group:'Places', availability:'unavailable'}, {menu_group:'Work',availability:'available',audience:'adults'}]), []);
assert.deepEqual(lessonJaunts([{id:'x',menu_group:'Places',availability:'available',grade_band:'6-8'}], 'Places', '9-10'), []);
const jaunt = { id: 'fixture', scene:'1835', title:'A <script>title</script>', premise:'A premise.',
  evidence: [{text:'A sourced claim.',confidence:'inferred',locator:'p. 2',sources:['source']}],
  citations: [{source_id:'source',citation:'A source.',tier:3,url:'javascript:alert(1)'}, {source_id:'orphan',citation:'Unused',tier:1,url:'https://example.org'}] };
const row = {id:'fixture',availability:'available',menu_group:'Places',grade_band:'9-10'};
const model = lessonModel({ year:'1835',group:'Places',band:'9-10',row,jaunt });
assert.equal(model.documents.length, 1, 'unused citations never become lesson evidence');
assert.equal(model.hasLinkedPrimary, false, 'a secondary source is not promoted to primary');
assert.deepEqual(lessonDocuments({evidence:[],citations:jaunt.citations}), []);
assert.throws(() => lessonModel({year:'1812',group:'Places',band:'9-10',row,jaunt}), /does not match/);
assert.throws(() => lessonModel({year:'1835',group:'Work',band:'9-10',row,jaunt}), /does not match/);
assert.throws(() => lessonModel({year:'1835',group:'Places',band:'6-8',row,jaunt}), /does not match/);
assert.throws(() => lessonModel({year:'1835',group:'Places',band:'9-10',row:{...row,audience:'adults'},jaunt}), /does not match/);

function fakeDOM() {
  const handlers = new Map();
  const doc = {};
  const element = tag => {
    const e = {tag,ownerDocument:doc,children:[],dataset:{},className:'',id:'',_text:'',parentNode:null,
      set textContent(v) {this._text=String(v); this.children=[];},
      get textContent() {return this._text + this.children.map(c => typeof c==='string'?c:c.textContent).join('');},
      append(...cs) {for (const c of cs) {this.children.push(c);if(typeof c!=='string')c.parentNode=this;}},
      remove() {if(this.parentNode)this.parentNode.children=this.parentNode.children.filter(c=>c!==this);this.parentNode=null;},
      cloneNode(deep) {const c=element(tag);c._text=this._text;c.className=this.className;if(deep)c.append(...this.children.map(x=>typeof x==='string'?x:x.cloneNode(true)));return c;},
    };
    e.classList={add:c=>{e.className+=' '+c;},remove:c=>{e.className=e.className.split(' ').filter(x=>x!==c).join(' ');},contains:c=>e.className.split(' ').includes(c)};
    return e;
  };
  doc.createElement=element;doc.body=element('body');doc.documentElement=element('html');
  const find=(e,id)=>e.id===id?e:e.children.filter(c=>typeof c!=='string').map(c=>find(c,id)).find(Boolean);
  doc.getElementById=id=>find(doc.body,id);
  doc.defaultView={printed:0,print(){this.printed++;},addEventListener:(k,f)=>handlers.set(k,f),removeEventListener:k=>handlers.delete(k)};
  return {doc,handlers};
}
const {doc,handlers}=fakeDOM();
const lesson=renderLesson(doc,model);
assert(lesson.textContent.includes('A <script>title</script>'), 'source text is treated as text');
assert(lesson.textContent.includes('not a quotation'));
assert(lesson.textContent.includes('No linked period source'));
assert(!lesson.textContent.includes('javascript:'));
assert.equal(printLesson(lesson,{doc}),true);
assert.equal(doc.defaultView.printed,1);
assert.equal(doc.getElementById('lesson-print').textContent,lesson.textContent);
assert(doc.documentElement.classList.contains('is-printing-lesson'));
handlers.get('afterprint')();
assert(!doc.getElementById('lesson-print'));
assert(!doc.documentElement.classList.contains('is-printing-lesson'));
doc.defaultView.print=()=>{throw Error('print unavailable');};
assert.equal(printLesson(lesson,{doc}),false);
assert(!doc.getElementById('lesson-print'), 'print failure cleans up');
console.log(`test_lesson_guides: ${groupCount} year/group guides, ${tellingCount} school tellings, cited claims, source gaps, URL safety and print cleanup passed`);
