#!/usr/bin/env node
// T-2666 (NAV-806): Guide › For teachers, the teacher handout. Mounts the real Guide screen
// (apps/guide-view.js) over a small hand-made DOM, with each destination's committed Jaunt
// catalog (data/sidecars/<year>/jaunts/catalog.json), and holds:
//   - the seven steps are the tour engine's own (js/tour.js STEPS), in order, never copied;
//   - three suggested Jaunts per destination, by the one stated rule — available only,
//     featured first, then the fewest stops, then the title A to Z — on a fixture exactly,
//     and on the real catalogs as an ordering no unpicked Jaunt beats;
//   - a destination with none, and a catalog that cannot be read, each say so;
//   - Print copies the handout to a top-level element the print stylesheet keeps, calls the
//     browser's print, and the copy goes on afterprint;
//   - no id, path, snake_case, "tier" or "ticket" in what a visitor reads.
// The smoke (part 12) opens it in the page and prints it to Letter and A4: one page each.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');

// ---- a small DOM: elements, text, attributes, clicks, clones -----------------------------
function makeDoc() {
  const text = (data) => ({ nodeType: 3, data, parentNode: null, get textContent() { return this.data; },
    cloneNode() { return text(this.data); }, remove() { const p = this.parentNode; if (p) p.childNodes.splice(p.childNodes.indexOf(this), 1); this.parentNode = null; } });
  const el = (tag) => {
    const fns = {};
    const e = {
      nodeType: 1, tagName: tag.toUpperCase(), childNodes: [], parentNode: null, attrs: {}, dataset: {}, className: '', id: '', type: '',
      get children() { return this.childNodes.filter((c) => c.nodeType === 1); },
      get textContent() { return this.childNodes.map((c) => c.textContent).join(''); },
      set textContent(v) { this.childNodes = []; if (v !== '') this.append(String(v)); },
      get ownerDocument() { return doc; },
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      removeAttribute(k) { if (k === 'id') this.id = ''; delete this.attrs[k]; },
      append(...cs) { for (const c of cs) { const n = typeof c === 'string' ? text(c) : c; n.remove?.(); n.parentNode = e; e.childNodes.push(n); } },
      replaceChildren(...cs) { for (const c of e.childNodes) c.parentNode = null; e.childNodes = []; e.append(...cs); },
      remove() { const p = this.parentNode; if (p) p.childNodes.splice(p.childNodes.indexOf(this), 1); this.parentNode = null; },
      addEventListener(t, f) { (fns[t] ??= []).push(f); },
      click() { for (const f of fns.click ?? []) f({ preventDefault() {}, stopPropagation() {} }); },
      cloneNode(deep) {
        const c = el(tag);
        Object.assign(c, { className: e.className, id: e.id, type: e.type });
        c.attrs = { ...e.attrs }; c.dataset = { ...e.dataset };
        if (deep) for (const k of e.childNodes) c.append(k.cloneNode(true));
        return c;
      },
    };
    e.classList = {
      add(c) { const s = new Set(e.className.split(' ').filter(Boolean)); s.add(c); e.className = [...s].join(' '); },
      remove(c) { e.className = e.className.split(' ').filter((x) => x && x !== c).join(' '); },
      contains: (c) => e.className.split(' ').includes(c),
      toggle(c, on) { if (on) this.add(c); else this.remove(c); },
    };
    return e;
  };
  const winFns = {};
  const win = {
    printed: 0,
    print() { this.printed++; },
    addEventListener(t, f) { (winFns[t] ??= []).push(f); },
    removeEventListener(t, f) { winFns[t] = (winFns[t] ?? []).filter((x) => x !== f); },
    dispatch(t) { for (const f of [...(winFns[t] ?? [])]) f({ type: t }); },
    listeners: (t) => (winFns[t] ?? []).length,
  };
  const doc = {
    createElement: el, defaultView: win,
    getElementById(id) { return all(doc.documentElement).find((n) => n.id === id) ?? null; },
  };
  doc.documentElement = el('html');
  doc.body = el('body');
  doc.documentElement.append(doc.body);
  return doc;
}
const all = (root, out = []) => { for (const c of root?.children ?? []) { out.push(c); all(c, out); } return out; };
const byId = (root, id) => all(root).find((e) => e.id === id) ?? null;
const byClass = (root, cls) => all(root).filter((e) => e.className.split(' ').includes(cls));

globalThis.document = makeDoc();
const doc = globalThis.document;
const { STEPS } = await import('../renderers/web/js/tour.js');
const { DESTINATIONS } = await import('../renderers/web/js/apps/jump-view.js');
const { suggestJaunts, handoutModel, SUGGESTED, PRINT_ID, PRINT_CLASS } = await import('../renderers/web/js/apps/teacher-handout.js');
const { mount, unmount } = await import('../renderers/web/js/apps/guide-view.js');
const { t } = await import('../renderers/web/js/strings/index.js');

// ---- the rule, on a fixture ---------------------------------------------------------------
const row = (id, featured, stop_count, extra = {}) => ({ id, title: id, featured, stop_count, availability: 'available', premise: `${id}.`, ...extra });
const fixture = [
  row('Zeta', true, 4), row('Alpha', true, 4), row('Long', true, 29), row('Short', false, 2),
  row('Broken', true, 1, { availability: 'unavailable' }), row('Mid', true, 5),
];
assert.equal(SUGGESTED, 3);
assert.deepEqual(suggestJaunts(fixture).map((r) => r.id), ['Alpha', 'Zeta', 'Mid'],
  'featured first, then the fewest stops, then A to Z; an unavailable Jaunt is never suggested');
assert.deepEqual(suggestJaunts(fixture.filter((r) => !r.featured)).map((r) => r.id), ['Short'], 'fewer than three: all there are');
assert.deepEqual(suggestJaunts(null), [], 'no catalog, no Jaunts');
assert.deepEqual(fixture.map((r) => r.id), ['Zeta', 'Alpha', 'Long', 'Short', 'Broken', 'Mid'], 'the catalog itself is left in its order');

// ---- the rule, on the committed catalogs ------------------------------------------------
const catalogOf = (year) => {
  const p = `data/sidecars/${year}/jaunts/catalog.json`;
  assert(fs.existsSync(path.join(ROOT, p)), `${p} is committed`);
  const c = JSON.parse(read(p));
  assert.equal(String(c.scene), String(year));
  return c.jaunts;
};
const beats = (a, b) => (a.featured === true) !== (b.featured === true) ? a.featured === true
  : a.stop_count !== b.stop_count ? a.stop_count < b.stop_count : a.title.localeCompare(b.title, 'en') < 0;
const picks = {};
for (const d of DESTINATIONS) {
  const rows = catalogOf(d.year);
  const chosen = suggestJaunts(rows);
  picks[d.year] = chosen.map((r) => r.title);
  const open = rows.filter((r) => r.availability !== 'unavailable');
  assert.equal(chosen.length, Math.min(3, open.length), `${d.year}: three, or all there are`);
  for (const c of chosen) assert.notEqual(c.availability, 'unavailable');
  for (let i = 1; i < chosen.length; i++) assert(beats(chosen[i - 1], chosen[i]), `${d.year}: in the rule's order`);
  for (const r of open.filter((x) => !chosen.includes(x))) {
    for (const c of chosen) assert(!beats(r, c), `${d.year}: ${r.title} is not suggested, so it cannot beat ${c.title}`);
  }
}
assert.equal(picks[1835].length, 3, '1835 has three to suggest');
assert.equal(picks[1904].length, 3, '1904 has three to suggest');
assert(!picks[1904].includes('Every building modelled so far'), 'the 29-stop build log is not a first Jaunt for a class');

// ---- the steps are the tour's own ------------------------------------------------------------
for (const scene of ['1835', '1904', '1812']) {
  const m = handoutModel({ steps: STEPS, scene, destinations: DESTINATIONS, catalogs: {} });
  assert.equal(m.steps.length, 7);
  assert.deepEqual(m.steps.map((s) => s.n), ['01', '02', '03', '04', '05', '06', '07']);
  assert.deepEqual(m.steps.map((s) => s.task), STEPS.map((s) => s.task), 'each step\'s task, as the tour has it');
  assert.deepEqual(m.steps.map((s) => s.bubble), STEPS.map((s) => s.bubble({ scene, front: null })), 'each bubble, as the tour says it there');
  assert.deepEqual(m.destinations.map((d) => d.year), [1835, 1904, 1812], 'the Observatory\'s destinations, in its order');
  assert.equal(m.destinations.filter((d) => d.here).map((d) => String(d.year)).join(), scene, 'the destination in hand is marked');
  assert(m.destinations.every((d) => d.state === 'reading'));
}
assert.match(handoutModel({ steps: STEPS, scene: '1904' }).steps[3].bubble, /Glessner House/);
assert.match(handoutModel({ steps: STEPS, scene: '1835' }).steps[3].bubble, /building in front of you/);

// ---- Guide › For teachers, in the screen ----------------------------------------------------
const settle = () => new Promise((r) => setTimeout(r, 0));
const ctxFor = (scene, jauntCatalog) => ({ controls: 'touch', coarse: true, scene,
  actions: { guideFaq: async () => ({ questions: [] }), onControls: () => () => {}, jauntCatalog } });
const screen = doc.createElement('div');
doc.body.append(screen);
const asked = [];
mount(screen, ctxFor({ id: '1904', target_date: '1904-07-01' }, async (year) => { asked.push(year); return catalogOf(year); }));
const block = byId(screen, 'guide-teachers');
assert(block, 'Guide has For teachers');
assert.equal(screen.children.at(-1), block, '…last, under the glossary and the questions');
assert.equal(byClass(block, 'nav-k')[0].textContent, 'For teachers');
assert.match(byId(block, 'guide-handout').textContent, /Reading the Jaunts…/, 'while the catalogs are read, it says so');
await settle(); await settle();
assert.deepEqual(asked, [1835, 1904, 1812], 'every destination\'s catalog, asked once each');
const handout = byId(block, 'guide-handout');
const words = handout.textContent;
const stepEls = byClass(handout, 'handout-step');
assert.equal(stepEls.length, 7, 'seven steps');
STEPS.forEach((s, i) => {
  assert.equal(byClass(stepEls[i], 'handout-task')[0].textContent, s.task);
  assert.equal(byClass(stepEls[i], 'handout-bubble')[0].textContent, s.bubble({ scene: '1904', front: null }));
});
const dests = byClass(handout, 'handout-dest');
assert.deepEqual(dests.map((d) => byClass(d, 'handout-dest-name')[0].textContent), ['1835 · Chicago', '1904 · Prairie Avenue', '1812 · Fort Dearborn']);
assert.equal(dests[1].dataset.here, 'true', 'the destination in hand');
for (const d of dests) {
  const titles = byClass(d, 'handout-jaunt-title').map((e) => e.textContent);
  assert.deepEqual(titles, picks[d.dataset.year], `${d.dataset.year}: the suggested Jaunts, in order`);
  for (const s of byClass(d, 'handout-stops')) assert.match(s.textContent, /^\d+ stops$/);
}
assert.equal(byClass(dests[2], 'handout-empty')[0]?.textContent, 'No Jaunts here yet.', 'a destination with no Jaunts says so');
assert.match(words, /featured Jaunts first, then the shortest/, 'the rule is printed with the picks');
// What a visitor reads: no id, path, snake_case, tier or ticket; the locked terms as written.
const visible = block.textContent;
assert(!/[a-z0-9]+_[a-z0-9]+/i.test(visible), 'no snake_case');
assert(!/\b(tier|ticket|T-\d{3,})\b/i.test(visible), 'no tier or ticket');
assert(!/[\w-]+\/[\w-]+\.(json|js|html)|https?:|\.json\b/.test(visible), 'no file path or link');
assert(!/\b(attested|inferred|reconstructed|confidence View|Confidence View)\b/.test(visible), 'grades and the Confidence view spelled as locked');
for (const term of ['Attested', 'Inferred', 'Reconstructed', 'Confidence view', 'Jaunts']) assert(visible.includes(term), `${term} as written`);
for (const n of all(block)) assert(n.textContent.trim() !== '' || n.childNodes.length === 0 || n.tagName === 'DETAILS', `${n.className}: every string resolved`);
for (const k of ['k', 'title', 'intro', 'print', 'preview', 'handout.title', 'handout.steps', 'handout.jaunts', 'handout.rule', 'handout.none', 'handout.unread', 'handout.reading', 'handout.foot']) {
  assert(t(`teachers.${k}`), `teachers.${k} is in the string table`);
}

// ---- Print: a top-level copy, the browser's print, gone on afterprint ------------------------
const win = doc.defaultView;
const print = byId(block, 'guide-handout-print');
assert.equal(print.tagName, 'BUTTON');
assert.equal(print.textContent, 'Print the handout');
print.click();
await settle();
assert.equal(win.printed, 1, 'window.print, once');
const copy = byId(doc.body, PRINT_ID);
assert(copy && copy.parentNode === doc.body, 'the copy is a child of body, which the print stylesheet keeps');
assert(doc.documentElement.classList.contains(PRINT_CLASS), '<html> is marked while printing');
assert.equal(copy.textContent, byId(block, 'guide-handout').textContent, 'the copy is the handout, word for word');
assert(!all(copy).some((n) => n.id), 'no id is repeated in the copy');
assert.equal(win.listeners('afterprint'), 1);
win.dispatch('afterprint');
assert.equal(byId(doc.body, PRINT_ID), null, 'the copy goes when the dialog closes');
assert(!doc.documentElement.classList.contains(PRINT_CLASS));
assert.equal(win.listeners('afterprint'), 0);
print.click(); await settle();
print.click(); await settle();
assert.equal(all(doc.body).filter((n) => n.id === PRINT_ID).length, 1, 'a second print replaces the copy, never stacks it');
win.dispatch('afterprint');
unmount(screen);

// A catalog that cannot be read says so; the steps still print.
const offline = doc.createElement('div');
mount(offline, ctxFor({ id: '1835' }, async (year) => { if (year === 1904) throw new Error('404'); return catalogOf(year); }));
await settle(); await settle();
const off = byClass(byId(offline, 'guide-handout'), 'handout-dest');
assert.equal(byClass(off[1], 'handout-empty')[0]?.textContent, 'The Jaunts could not be read just now.');
assert.equal(byClass(off[0], 'handout-jaunt-title').length, 3, 'the others still list theirs');
assert.equal(byClass(byId(offline, 'guide-handout'), 'handout-step').length, 7);
assert.equal(off[0].dataset.here, 'true');
unmount(offline);
// No way to read catalogs at all (an older page): every destination says it could not.
const bare = doc.createElement('div');
mount(bare, { controls: 'pointerlock', actions: {} });
await settle(); await settle();
assert.equal(byClass(byId(bare, 'guide-handout'), 'handout-empty').length, 3);
unmount(bare);

// ---- the page: the print stylesheet, the catalog read, the link -----------------------------
const css = read('renderers/web/css/handout.css');
const print_ = css.slice(css.indexOf('@media print'));
assert(css.indexOf('@media print') > 0, 'a print stylesheet');
assert.match(css, /\.handout-print \{ display: none; \}/, 'the copy never shows on screen');
assert.match(print_, /html\.is-printing-handout body > :not\(\.handout-print\) \{ display: none !important; \}/, 'printed, everything else is left out');
assert.match(print_, /@page \{ margin: 12mm; \}/, 'margins that hold at Letter and A4');
assert(!/@page[^}]*size/.test(print_), 'no page size forced: the printer\'s Letter or A4');
assert.match(read('renderers/web/index.html'), /<link rel="stylesheet" href="\.\/css\/handout\.css">/);
const main = read('renderers/web/js/main.js');
assert(/jauntCatalog: \(year\) => \(jauntCatalogs\[year\] \?\?= fetch\(new URL\(`sidecars\/\$\{encodeURIComponent\(year\)\}\/jaunts\/catalog\.json`/.test(main),
  'each destination\'s catalog is read when Guide asks, never at boot');

console.log(`test_teacher_handout: seven tour steps and three Jaunts each for ${Object.entries(picks).map(([y, p]) => `${y} (${p.length})`).join(', ')}, printed as one top-level copy`);
