// T-2641 — Inspect's Design tab (js/inspect-design.js): the style card from the building's style
// module, the numbered "On this house" hotspots with their grades in place of the attribute table,
// and Compare styles; a building with no module or record degrades honestly to its own sidecar.
//
//   node tools/test_nav_design.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { designModel, renderDesign, hotspots, plateOf, styleFor, labelOf, valueOf } from '../renderers/web/js/inspect-design.js';
import { t } from '../renderers/web/js/strings/index.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const data = path.join(here, '../data');
const read = (p) => JSON.parse(readFileSync(path.join(data, p), 'utf8'));
let n = 0;
const ok = (label, fn) => { fn(); n++; console.log(`  ok ${label}`); };

// ---- a small DOM ------------------------------------------------------------------------------
function fakeDoc() {
  const doc = {
    createElement(tag) {
      const fns = {};
      const el = {
        tagName: tag.toUpperCase(), className: '', dataset: {}, attrs: {}, children: [], _text: '',
        get textContent() { return this._text + this.children.map((c) => c.textContent).join(''); },
        set textContent(v) { this._text = String(v); this.children = []; },
        setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
        append(...cs) { for (const c of cs) { c.parent = el; el.children.push(c); } },
        addEventListener(type, fn) { (fns[type] ??= []).push(fn); },
        click() { for (const fn of fns.click ?? []) fn({ preventDefault() {} }); },
      };
      return el;
    },
  };
  return doc;
}
const all = (el, out = []) => { for (const c of el.children ?? []) { out.push(c); all(c, out); } return out; };
const cls = (el, c) => all(el).filter((e) => String(e.className).split(' ').includes(c));
const dots = [];
const dot = (d, grade) => { const i = d.createElement('i'); i.className = `fact-dot fact-${grade}`; dots.push(grade); return i; };

const sum = read('summaries/glessner_house.json');
const sidecar = read('sidecars/1904/glessner_house.json');
const module = read(`styles/${sum.style}.json`);
const styles = { [module.id]: module };
// The scene's pictures file is compiled at publish (never committed), so the plate is read from
// a stand-in holding exactly the module's picture, public domain, with a held copy.
const pictures = {
  image_store: { base_url: 'https://images.example/prairie/' },
  by_structure: { [module.plate.structure]: [{ id: module.plate.picture, rights: 'public domain', creator: 'Inland Architect Press',
    years: [1888, 1888], held: { f: 'plate.jpg' } }] },
};
const S1904 = { id: '1904' };

ok('labels and values read as words, with their units', () => {
  assert.equal(labelOf('roof_pitch_deg'), 'Roof pitch');
  assert.equal(labelOf('wall_height_m'), 'Wall height');
  assert.equal(labelOf('construction'), 'Built of');
  assert.equal(labelOf('chimneys'), 'Chimneys');
  assert.equal(valueOf('roof_pitch_deg', 35), '35°');
  assert.equal(valueOf('wall_height_m', 2.5), '2.5 m');
  assert.equal(valueOf('roof_type', 'terracotta_tile'), 'terracotta tile');
  assert.equal(valueOf('bay_dining', { outline: [[1, 2]] }), '', 'a structured value prints nothing');
});

ok('Glessner House names the Richardsonian Romanesque module, and the card is the module as written', () => {
  assert.equal(sum.style, 'richardsonian_romanesque');
  const m = designModel({ sum, sidecar, styles, pictures, scene: S1904 });
  assert.equal(m.style.name, 'Richardsonian Romanesque');
  assert.equal(m.style.description.text, module.description.text);
  assert.ok(m.style.description.grade, 'the description carries its grade');
  assert.ok(m.style.cues.length >= 1 && m.style.cues.length <= 4, 'one to four cues, never padded');
  assert.deepEqual(m.style.cues.map((c) => c.text), module.cues.map((c) => c.text));
  assert.ok(m.style.cues.every((c) => c.grade), 'every cue is graded');
  assert.ok(m.style.compare.length >= 1 && m.style.compare.length <= 3 && m.style.compare.every((c) => c.grade && c.name && c.text));
  assert.equal(m.style.plate.src, 'https://images.example/prairie/plate.jpg');
  assert.equal(m.style.plate.credit, 'Inland Architect Press · 1888', 'the credit is the pictures file\'s own creator and year');
  assert.equal(m.style.plate.caption, module.plate.caption);
});

ok('every cue and Compare line rests on sources the module names (the compiler resolves them)', () => {
  for (const c of [module.description, ...module.cues, ...module.compare, module.plate]) {
    assert.ok(c.grade === 'attested' ? c.sources?.length > 0 : (c.note ?? '').trim().length > 0, JSON.stringify(c).slice(0, 80));
    for (const s of c.sources ?? []) assert.ok(readFileSync(path.join(data, 'sources', `${s}.json`), 'utf8').length > 0, s);
  }
});

ok('a plate shows only where the pictures file holds a copy whose rights allow display, in its own scene', () => {
  assert.equal(plateOf(module.plate, pictures, '1835'), null, 'another scene\'s file does not hold it');
  assert.equal(plateOf(module.plate, null, '1904'), null, 'no pictures file, no plate');
  const linkOnly = structuredClone(pictures);
  linkOnly.by_structure[module.plate.structure][0].rights = 'unknown — link only';
  assert.equal(plateOf(module.plate, linkOnly, '1904'), null, 'rights that do not allow display, no plate');
  const unheld = structuredClone(pictures);
  delete unheld.by_structure[module.plate.structure][0].held;
  assert.equal(plateOf(module.plate, unheld, '1904'), null, 'no held copy, no plate');
  assert.equal(designModel({ sum, sidecar, styles, pictures: null, scene: S1904 }).style.plate, null);
});

ok('Glessner\'s hotspots are the record\'s own, numbered, each graded, each sidecar one at the sidecar\'s grade', () => {
  const h = hotspots(sum, sidecar);
  assert.equal(h.source, 'record');
  assert.equal(h.items.length, sum.onThisHouse.length);
  assert.deepEqual(h.items.map((x) => x.n), sum.onThisHouse.map((_, i) => i + 1));
  assert.ok(h.items.every((x) => ['attested', 'inferred', 'reconstructed'].includes(x.grade)));
  for (const a of sum.onThisHouse.filter((x) => x.attribute)) {
    assert.equal(a.grade, sidecar.attributes[a.attribute].confidence, `${a.attribute}: the hotspot keeps the sidecar's grade`);
  }
  assert.ok(h.items.some((x) => x.grade === 'attested') && h.items.some((x) => x.grade === 'reconstructed'),
    'Attested granite walls and a Reconstructed feature, as M8 shows');
  const lib = h.items.filter((x) => x.liberty);
  assert.ok(lib.length >= 1 && lib.every((x) => x.grade === 'reconstructed'), 'only a reconstructed hotspot naming a liberty says so');
  assert.equal(h.tap, true);
  assert.ok(h.items.filter((x) => x.camera).every((x) => Number.isFinite(x.camera.yaw) && Number.isFinite(x.camera.pitch)));
});

ok('the Design tab draws the card, the numbered hotspots (no table) and Compare styles; a tap runs Show me', () => {
  const doc = fakeDoc();
  dots.length = 0;
  const looked = [];
  const m = designModel({ sum, sidecar, styles, pictures, scene: S1904 });
  const root = renderDesign(doc, m, { dot, onLook: (x) => looked.push(x) });
  assert.equal(root.dataset.style, 'richardsonian_romanesque');
  assert.equal(cls(root, 'insp-style-name')[0].textContent, 'Richardsonian Romanesque');
  assert.equal(cls(root, 'insp-cue').length, module.cues.length);
  assert.equal(cls(root, 'insp-compare-item').length, module.compare.length);
  const items = cls(root, 'insp-hot');
  assert.equal(items.length, sum.onThisHouse.length);
  assert.ok(items.every((li) => cls(li, 'fact-dot').length === 1), 'every hotspot has one grade dot');
  assert.deepEqual(items.map((li) => cls(li, 'insp-hot-n')[0].textContent), items.map((_, i) => String(i + 1)));
  assert.equal(all(root).filter((e) => e.tagName === 'TABLE').length, 0, 'no attribute table remains');
  const heads = cls(root, 'insp-h').map((e) => e.textContent);
  assert.deepEqual(heads, [t('inspect-design.cues'), t('inspect-design.hotspots.tap'), t('inspect-design.compare')]);
  assert.match(root.textContent, /Listed in Liberties\./);
  const buttons = all(root).filter((e) => e.tagName === 'BUTTON');
  assert.equal(buttons.length, sum.onThisHouse.filter((x) => x.camera).length, 'a button exactly where the record names a camera');
  buttons[0].click();
  assert.deepEqual(looked[0].camera, sum.onThisHouse[0].camera);
  assert.equal(looked[0].feature, sum.onThisHouse[0].feature);
  const text = root.textContent;
  assert.ok(!/[a-z0-9]+_[a-z0-9]+/i.test(text), 'no snake_case reaches a visitor');
  assert.ok(!/\b(attested|inferred|reconstructed|tier|ticket)\b/i.test(text), 'grades appear only as dots; no tier or ticket');
  // Without Show me, the same hotspots draw and none is a button.
  const still = renderDesign(fakeDoc(), m, { dot });
  assert.equal(all(still).filter((e) => e.tagName === 'BUTTON').length, 0);
  assert.equal(cls(still, 'insp-h')[1].textContent, t('inspect-design.hotspots'));
});

ok('an 1835 building with no record and no module: an honest line, and its own sidecar as graded hotspots', () => {
  const s = read('sidecars/1835/hogan_store.json');
  const m = designModel({ sum: null, sidecar: s, styles, pictures, scene: { id: '1835' } });
  assert.equal(m.style, null);
  assert.equal(m.hot.source, 'sidecar');
  const graded = Object.values(s.attributes).filter((a) => ['attested', 'inferred', 'reconstructed'].includes(a.confidence)).length;
  assert.equal(m.hot.items.length, graded + (s.footprint?.confidence ? 1 : 0));
  assert.equal(m.hot.items[0].text, t('inspect-design.shape'));
  assert.equal(m.hot.items[0].grade, s.footprint.confidence);
  assert.equal(m.hot.tap, false);
  const doc = fakeDoc();
  const root = renderDesign(doc, m, { dot, onLook: () => assert.fail('no camera, no Show me') });
  assert.equal(cls(root, 'insp-style-none')[0].textContent, t('inspect-design.style.none'));
  assert.equal(cls(root, 'insp-style').length, 0, 'no card is composed');
  assert.equal(cls(root, 'insp-compare').length, 0);
  assert.equal(all(root).filter((e) => e.tagName === 'BUTTON').length, 0);
  assert.equal(cls(root, 'insp-h')[0].textContent, t('inspect-design.hotspots'));
  const items = cls(root, 'insp-hot');
  assert.ok(items.length > 1 && items.every((li) => cls(li, 'fact-dot').length === 1));
  assert.match(root.textContent, /Built of/);
  assert.ok(!/[a-z0-9]+_[a-z0-9]+/i.test(root.textContent));
});

ok('a style id with no module, and a building with nothing graded, degrade honestly', () => {
  assert.equal(styleFor({ style: 'no_such_style' }, styles), null);
  assert.equal(styleFor({ style: null }, styles), null);
  const m = designModel({ sum: null, sidecar: { attributes: { roof_type: { value: 'gable' } } }, styles: null });
  assert.equal(m.hot.items.length, 0, 'an ungraded attribute is not listed: every hotspot has a dot');
  const root = renderDesign(fakeDoc(), m, { dot });
  assert.equal(cls(root, 'insp-hot').length, 0);
  assert.match(root.textContent, new RegExp(t('inspect-design.hotspots.none').replace(/[.]/g, '\\.')));
});

console.log(`test_nav_design: OK (${n} checks)`);
