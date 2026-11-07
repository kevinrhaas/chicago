// T-2641 — Inspect's Design tab (js/inspect-design.js): the style card from the building's style
// module, the numbered "On this house" hotspots with their grades, and Compare styles. T-3435: the
// tab is a written style guide for every building (js/style-guide.js) — the same head, lead,
// Look for and five parts on every card, each line graded and filled from the record.
//
//   node tools/test_nav_design.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { designModel, renderDesign, hotspots, plateOf, styleFor, labelOf, valueOf, compareCard } from '../renderers/web/js/inspect-design.js';
import { styleGuide, PART_KEYS, GRADES as SG_GRADES, lowest } from '../renderers/web/js/style-guide.js';
import { clean } from '../renderers/web/js/fallback-summary.js';
import { readdirSync } from 'node:fs';
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
const library = Object.fromEntries(['richardsonian_romanesque', 'second_empire', 'italianate'].map((id) => [id, read(`styles/${id}.json`)]));

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
  assert.deepEqual(heads, [t('inspect-design.look.tap'), t('inspect-design.cues'), t('inspect-design.compare')]);
  assert.match(root.textContent, /Listed in Liberties\./);
  assert.deepEqual(cls(root, 'sg-part').map((e) => e.dataset.part), PART_KEYS, 'the five parts, in order');
  assert.equal(cls(root, 'sg-name')[0].textContent, 'Richardsonian Romanesque', 'the guide is headed by the style');
  assert.deepEqual(cls(root, 'sg-go').map((e) => e.dataset.inspGo), ['details', 'sources'], 'and ends with the ways to Details and Sources');
  const buttons = all(root).filter((e) => e.tagName === 'BUTTON' && e.className === 'insp-hot-row');
  assert.equal(buttons.length, sum.onThisHouse.filter((x) => x.camera).length, 'a button exactly where the record names a camera');
  buttons[0].click();
  assert.deepEqual(looked[0].camera, sum.onThisHouse[0].camera);
  assert.equal(looked[0].feature, sum.onThisHouse[0].feature);
  const text = root.textContent;
  assert.ok(!/[a-z0-9]+_[a-z0-9]+/i.test(text), 'no snake_case reaches a visitor');
  assert.ok(!/\b(attested|inferred|reconstructed|tier|ticket)\b/i.test(text), 'grades appear only as dots; no tier or ticket');
  // Without Show me, the same hotspots draw and none is a button.
  const still = renderDesign(fakeDoc(), m, { dot });
  assert.equal(cls(still, 'insp-hot-row').filter((e) => e.tagName === 'BUTTON').length, 0);
  assert.equal(cls(still, 'insp-h')[0].textContent, t('inspect-design.look'));
});

ok('an 1835 building with no record and no module: a guide written from its own record, the same five parts', () => {
  const s = read('sidecars/1835/hogan_store.json');
  const m = designModel({ sum: null, sidecar: s, styles, pictures, scene: { id: '1835' } });
  assert.equal(m.style, null);
  assert.equal(m.hot.source, 'guide', 'the sidecar\'s attribute list is the Details tab\'s now');
  assert.equal(m.hot.items.length, 0);
  const doc = fakeDoc();
  dots.length = 0;
  const root = renderDesign(doc, m, { dot, onLook: () => assert.fail('no camera, no Show me') });
  assert.equal(cls(root, 'insp-style').length, 0, 'no style card is composed');
  assert.equal(cls(root, 'insp-compare').length, 0);
  assert.equal(cls(root, 'insp-hot-row').filter((e) => e.tagName === 'BUTTON').length, 0);
  assert.deepEqual(cls(root, 'sg-part').map((e) => e.dataset.part), PART_KEYS);
  assert.ok(cls(root, 'sg-name')[0].textContent.length > 3, 'a name: what the building is');
  assert.ok(cls(root, 'sg-sentence').length >= 1, 'a lead');
  assert.ok(cls(root, 'sg-line').every((li) => cls(li, 'fact-dot').length === 1), 'every line keeps its grade dot');
  assert.ok(cls(root, 'sg-line').length >= 3);
  assert.ok(!/[a-z0-9]+_[a-z0-9]+/i.test(root.textContent));
  assert.ok(!/\b(attested|inferred|tier|ticket)\b/i.test(root.textContent));
});

ok('a style id with no module, and a building with nothing graded, degrade honestly', () => {
  assert.equal(styleFor({ style: 'no_such_style' }, styles), null);
  assert.equal(styleFor({ style: null }, styles), null);
  const m = designModel({ sum: null, sidecar: { attributes: { roof_type: { value: 'gable' } } }, styles: null });
  assert.equal(m.hot.items.length, 0, 'an ungraded attribute is not listed: every line has a dot');
  const root = renderDesign(fakeDoc(), m, { dot });
  assert.equal(cls(root, 'insp-hot').length, 0);
  assert.equal(cls(root, 'sg-part').length, 5, 'all five parts still show');
  // An attribute with no grade is counted as Details counts it (and the card): Reconstructed.
  assert.equal(cls(root, 'sg-none').length, 4, 'each empty part says the records do not say');
  assert.equal(cls(root, 'sg-line')[0].textContent, 'Two slopes meeting at a ridge, with gable ends');
  assert.equal(cls(root, 'sg-none')[0].textContent, t('inspect-design.part.none'));
});

// ---- T-3435: the style guide, over every structure in every scene ---------------------------
ok('every structure in every scene gets the same guide: a name, a lead, the five parts, every line graded and clean', () => {
  let count = 0;
  const firstLine = new Map();
  for (const scene of ['1812', '1835', '1904']) {
    const dir = path.join(data, 'sidecars', scene);
    for (const f of readdirSync(dir).filter((x) => x.endsWith('.json'))) {
      const sc = JSON.parse(readFileSync(path.join(dir, f), 'utf8'));
      if (!sc || typeof sc !== 'object' || !sc.attributes || !sc.id) continue;
      let summary = null;
      try { summary = read(`summaries/${sc.id}.json`); } catch { summary = null; }
      const g = styleGuide({ sidecar: sc, sum: summary, mod: summary?.style ? library[summary.style] ?? null : null });
      const where = `${scene}/${sc.id}`;
      assert.ok(clean(g.name.text) && g.name.text.length > 2, `${where}: a name`);
      assert.deepEqual(g.parts.map((p) => p.key), PART_KEYS, `${where}: the five parts, in order`);
      assert.ok(g.lead.length <= 3 && g.look.length <= 4, `${where}: at most three sentences and four highlights`);
      const lines = [...g.lead, ...g.look, ...g.parts.flatMap((p) => p.lines)];
      for (const l of lines) {
        assert.ok(SG_GRADES.includes(l.grade), `${where}: "${l.text}" carries a grade`);
        assert.ok(clean(l.text), `${where}: "${l.text}" is clean`);
        assert.ok(!/\b(undefined|null|NaN)\b|_/.test(l.text), `${where}: "${l.text}" reads as words`);
        assert.ok(l.text.split(/\s+/).length <= 32, `${where}: "${l.text}" is one short line`);
      }
      if (sc.attributes.construction) assert.ok(g.parts[1].lines.length > 0, `${where}: its walls are described`);
      if (g.basis) assert.ok(SG_GRADES.includes(g.basis.grade) && clean(g.basis.text), `${where}: what it was built from`);
      firstLine.set(where, g.lead[0]?.text ?? '');
      count += 1;
    }
  }
  assert.ok(count > 900, `the guide covers the town (${count} structures)`);
  assert.ok([...firstLine.values()].filter(Boolean).length / count > 0.9, 'nine in ten open on a sentence');
});

ok('a sentence is as sure as its least sure part', () => {
  assert.equal(lowest('attested', 'inferred'), 'inferred');
  assert.equal(lowest('attested', null, 'reconstructed', 'inferred'), 'reconstructed');
  assert.equal(lowest(), null);
  const g = styleGuide({ sidecar: { attributes: {
    stories: { value: 2, confidence: 'attested' }, construction: { value: 'brick', confidence: 'attested' },
    function: { value: 'residence', confidence: 'inferred' }, roof_form: { value: 'mansard', confidence: 'reconstructed' },
    roof_covering: { value: { fabric: 'slate_pennsylvania' }, confidence: 'inferred' },
  } } });
  assert.equal(g.name.text, 'Brick house');
  assert.deepEqual(g.lead.map((l) => [l.text, l.grade]), [
    ['A two-storey brick house.', 'inferred'],
    ['Its roof is a mansard roof of Pennsylvania slate.', 'reconstructed'],
  ]);
  assert.ok(g.look.some((h) => h.text === 'Mansard roof'));
});

// ---- T-2642: the style library -------------------------------------------------------------
const images = JSON.parse(readFileSync(path.join(here, '../../prairie_1904_v1/data/images.json'), 'utf8'));
const imageById = new Map((Array.isArray(images.images) ? images.images : Object.values(images.images)).map((r) => [r.id, r]));

ok('the library\'s modules: one to four cues of at most 8 words, every fact graded and sourced, never padded', () => {
  for (const [id, m] of Object.entries(library)) {
    assert.equal(m.id, id);
    assert.ok(m.cues.length >= 1 && m.cues.length <= 4, `${id}: one to four cues`);
    assert.ok(m.cues.every((c) => c.text.split(/\s+/).length <= 8), `${id}: cues of at most 8 words`);
    for (const c of [m.description, ...m.cues, ...m.compare, ...(m.plate ? [m.plate] : [])]) {
      assert.ok(['attested', 'inferred', 'reconstructed'].includes(c.grade), `${id}: ${c.text ?? c.caption}`);
      assert.ok(c.grade === 'attested' ? c.sources?.length > 0 : (c.note ?? '').trim().length > 0, `${id}: ${c.text ?? c.caption}`);
      for (const sid of c.sources ?? []) assert.ok(readFileSync(path.join(data, 'sources', `${sid}.json`), 'utf8').length > 0, sid);
    }
    // No two cues say the same thing.
    assert.equal(new Set(m.cues.map((c) => c.text)).size, m.cues.length, `${id}: no cue twice`);
  }
});

ok('every plate is a held picture of its own structure, credited by a public-domain record of its own', () => {
  for (const [id, m] of Object.entries(library)) {
    if (!m.plate) continue;
    const rec = read(`sources/${m.plate.record}.json`);
    assert.ok(['public_domain', 'no_known_restrictions'].includes(rec.rights_status), `${id}: the plate's record allows display`);
    const img = imageById.get(m.plate.picture);
    assert.ok(img, `${id}: the plate is a picture the library holds`);
    assert.match(String(img.rights), /^(public domain|no known restrictions)/i, `${id}: the library's own rights allow display`);
    assert.ok(img.local?.display, `${id}: the image store holds a copy`);
    assert.ok(readFileSync(path.join(data, 'sidecars', m.plate.scene, `${m.plate.structure}.json`), 'utf8').length > 0, `${id}: its structure stands in its scene`);
  }
});

ok('the buildings a record names a style for link to those modules, and only those', () => {
  const linked = { elbridge_keith_house_1900_prairie: 'second_empire', armour_house_2115_prairie: 'second_empire',
    jones_house_1834_prairie: 'italianate', glessner_house: 'richardsonian_romanesque' };
  for (const [sid, want] of Object.entries(linked)) {
    const rec = read(`summaries/${sid}.json`);
    assert.equal(rec.style, want, sid);
    const styleKey = rec.key.find((k) => k.label === 'Style');
    assert.ok(styleKey && styleKey.grade === 'attested' && styleKey.sources.length > 0, `${sid}: its Style fact is sourced`);
    assert.equal(designModel({ sum: rec, sidecar: null, styles: library, pictures: null, scene: S1904 }).style.name, library[want].name);
  }
});

ok('a Compare line that points at another module opens that style\'s card in place; one that does not, does not', () => {
  const keith = read('summaries/elbridge_keith_house_1900_prairie.json');
  const m = designModel({ sum: keith, sidecar: read('sidecars/1904/elbridge_keith_house_1900_prairie.json'), styles: library, scene: S1904 });
  assert.equal(m.style.name, 'Second Empire');
  const ital = m.style.compare.find((c) => c.style === 'italianate');
  assert.ok(ital.card, 'the Italianate line carries the Italianate card');
  assert.deepEqual(ital.card.cues.map((c) => c.text), library.italianate.cues.map((c) => c.text));
  assert.equal(ital.card.description.text, library.italianate.description.text);
  const doc = fakeDoc();
  dots.length = 0;
  const root = renderDesign(doc, m, { dot });
  assert.equal(cls(root, 'insp-compare-item').length, library.second_empire.compare.length);
  const more = cls(root, 'insp-compare-more');
  assert.equal(more.length, library.second_empire.compare.filter((c) => library[c.style]).length);
  const opened = more.find((d) => d.dataset.style === 'italianate');
  assert.equal(cls(opened, 'insp-compare-open')[0].textContent, t('inspect-design.compare.open', { name: 'Italianate' }));
  assert.equal(cls(opened, 'insp-compare-cue').length, library.italianate.cues.length);
  assert.ok(cls(opened, 'insp-compare-cue').every((li) => cls(li, 'fact-dot').length === 1), 'every opened cue keeps its grade dot');
  assert.equal(cls(root, 'insp-cue').length, library.second_empire.cues.length, 'the opened cards do not count as this card\'s cues');
  assert.ok(more.every((d) => cls(d, 'insp-h').length === 0), 'the opened cards add no section heading');
  // Glessner's Chateauesque line names no module: it stays a line.
  const g = designModel({ sum, sidecar, styles: library, pictures, scene: S1904 });
  assert.equal(g.style.compare.find((c) => c.style === 'chateauesque').card, null);
  assert.ok(g.style.compare.find((c) => c.style === 'second_empire').card);
  // A line pointing at the card's own module opens nothing.
  assert.equal(compareCard({ style: 'second_empire' }, library.second_empire, library), null);
  const text = root.textContent;
  assert.ok(!/[a-z0-9]+_[a-z0-9]+/i.test(text), 'no snake_case reaches a visitor');
  assert.ok(!/\b(attested|inferred|reconstructed|tier|ticket)\b/i.test(text));
});

console.log(`test_nav_design: OK (${n} checks)`);
