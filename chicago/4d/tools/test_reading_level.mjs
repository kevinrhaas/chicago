#!/usr/bin/env node
// T-3645 (owner, 2026-11-17: "a person can set a grade level age level in their settings and
// then the cards they read about people etc are targeted at their age level ... there would be
// a tab to read the different levels of all of the cards, the default level is the highest
// level"): the reader's ages, kept on the device and the account; a card's age tabs over a
// small hand-made DOM; a jaunt's other tellings as its table; and the scene table the app
// fetches, as tools/reading_levels.py writes it. No browser: the smoke opens a card in a page.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import {
  LEVELS, LEVEL_IDS, WRITTEN, levelOfGrade, gradeOfLevel, createReadingChoice, readerFields, remoteAges, READER_FIELDS,
  syncReading, tableOf, addTable, clearTables, lookup, wordsAt, tellingTable, readingTabs, levelledIn, forgetAge, openingAge, keyOf,
} from '../renderers/web/js/reading-level.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const mem = () => { const m = new Map(); return { m, getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) }; };

// ---- the ages -----------------------------------------------------------------------------
assert.deepEqual(LEVEL_IDS, ['8-10', '11-13', '14-15', '16-17', '18+'], 'the five ages the Jaunts menu offers (T-3640)');
assert.deepEqual(LEVELS.map((l) => l.grade), ['3-5', '6-8', '9-10', '11-12', null]);
assert.equal(levelOfGrade('9-10'), '14-15'); assert.equal(levelOfGrade('K-2'), '8-10'); assert.equal(gradeOfLevel('11-13'), '6-8');

// ---- the choice: one or several, kept on the device, every view told ------------------------
{
  const store = mem();
  const c = createReadingChoice({ storage: store });
  assert.deepEqual(c.get(), [], 'none chosen at first');
  assert.equal(c.top(), WRITTEN, 'none chosen: the words as written');
  const seen = [];
  c.subscribe((ages, from) => seen.push([ages.join(), from]));
  c.toggle('14-15'); c.toggle('8-10');
  assert.deepEqual(c.get(), ['8-10', '14-15'], 'several ages, kept youngest first');
  assert.equal(c.top(), '14-15', 'the highest chosen');
  assert.deepEqual(JSON.parse(store.getItem('chicago4d.reading.ages')), ['8-10', '14-15'], 'kept on this device');
  assert.deepEqual(createReadingChoice({ storage: store }).get(), ['8-10', '14-15'], 'and read back on the next visit');
  c.toggle('8-10');
  assert.deepEqual(c.get(), ['14-15'], 'a second tap lets an age go');
  assert.equal(c.set(['14-15']), false, 'no change, nobody told');
  c.set(['nine', '16-17', '16-17']);
  assert.deepEqual(c.get(), ['16-17'], 'unknown ages and repeats are dropped');
  assert.deepEqual(seen.map((s) => s[1]), ['reader', 'reader', 'reader', 'reader']);
  const refused = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); } };
  const r = createReadingChoice({ storage: refused });
  r.toggle('11-13');
  assert.deepEqual(r.get(), ['11-13'], 'refused storage: the choice still holds for the visit');
}

// ---- the account: readers/<uid>, its fields the rule allows ----------------------------------
{
  assert.deepEqual(READER_FIELDS, ['ages', 'at']);
  const fields = readerFields(['14-15', '8-10'], new Date('2026-11-17T12:00:00Z'));
  assert.deepEqual(Object.keys(fields), READER_FIELDS, 'only the fields the rule lists');
  assert.deepEqual(remoteAges({ fields }), ['8-10', '14-15']);
  assert.equal(remoteAges({ fields: {} }), null);
  // docs/SIGN-IN.md's rule names exactly these fields, so a new one cannot ship without its rule.
  const rule = read('docs/SIGN-IN.md').match(/match \/readers\/\{uid\}[\s\S]*?hasOnly\(\[([^\]]*)\]\)/);
  assert(rule, 'docs/SIGN-IN.md carries the readers/{uid} rule');
  assert.deepEqual(rule[1].split(',').map((s) => s.trim().replace(/'/g, '')), READER_FIELDS, 'the rule allows exactly the fields written');

  const calls = [];
  const fetchFn = async (url, opts = {}) => {
    calls.push([opts.method ?? 'GET', url, opts.body ? JSON.parse(opts.body) : null, opts.headers?.Authorization]);
    if ((opts.method ?? 'GET') === 'GET') return { ok: true, status: 200, json: async () => ({ fields: readerFields(['11-13']) }) };
    return { ok: true, status: 200 };
  };
  const account = { uid: 'u1', idToken: async () => 'tok' };
  const c = createReadingChoice({ storage: mem() });
  c.set(['8-10']);
  const res = await syncReading({ choice: c, account, projectId: 'p', fetchFn });
  assert.deepEqual(res, { synced: true, from: 'account' });
  assert.deepEqual(c.get(), ['11-13'], 'the account\'s ages win: they were set on another device');
  assert.match(calls[0][1], /\/documents\/readers\/u1$/); assert.equal(calls[0][3], 'Bearer tok');
  c.toggle('16-17');
  await new Promise((r) => setTimeout(r, 0));
  const put = calls.find((x) => x[0] === 'PATCH');
  assert(put, 'a change is written to the account');
  assert.match(put[1], /updateMask\.fieldPaths=ages&updateMask\.fieldPaths=at$/);
  assert.deepEqual(remoteAges(put[2]), ['11-13', '16-17']);

  const none = [];
  const empty = async (url, opts = {}) => { none.push(opts.method ?? 'GET'); return (opts.method ?? 'GET') === 'GET' ? { ok: false, status: 404 } : { ok: true, status: 200 }; };
  const d = createReadingChoice({ storage: mem() }); d.set(['14-15']);
  assert.deepEqual(await syncReading({ choice: d, account, projectId: 'p', fetchFn: empty }), { synced: true, from: 'device' });
  assert.deepEqual(none, ['GET', 'PATCH'], 'an account with none takes this device\'s');
  const warn = console.warn; console.warn = () => {};
  const shut = async () => ({ ok: false, status: 403 });
  const e = createReadingChoice({ storage: mem() }); e.set(['8-10']);
  assert.equal((await syncReading({ choice: e, account, projectId: 'p', fetchFn: shut })).synced, true);
  assert.deepEqual(e.get(), ['8-10'], 'a refused account (the rule not pasted yet) leaves the device\'s choice');
  console.warn = warn;
  assert.equal((await syncReading({ choice: e, account: null, projectId: 'p', fetchFn })).synced, false, 'nobody signed in: device only');
}

// ---- the words at an age ----------------------------------------------------------------------
{
  const entry = { own: '14-15', levels: { '8-10': 'young', '16-17': 'older' } };
  assert.equal(wordsAt(entry, 'own', '14-15'), 'own');
  assert.equal(wordsAt(entry, 'own', '8-10'), 'young');
  assert.equal(wordsAt(entry, 'own', '11-13'), 'own', 'an age not written: the nearest older one written');
  assert.equal(wordsAt(entry, 'own', '18+'), 'older', 'past the oldest written: the nearest younger');
  const t = tableOf([{ text: '  Two  words. ', own: '11-13', levels: { '8-10': 'Two.', '11-13': 'same age: dropped' } }, { text: 'none', levels: {} }]);
  assert.equal(t.size, 1, 'an entry with no other age is not a table row');
  assert.deepEqual(t.get('Two words.'), { own: '11-13', levels: { '8-10': 'Two.' } }, 'keyed with its spaces run together; its own age is not a level');
}

// ---- the tabs, over a small DOM ----------------------------------------------------------------
function makeDoc() {
  const doc = { createElement: (tag) => element(tag), createTextNode: (t) => text(t) };
  function text(t) { return { nodeType: 3, data: String(t), parentNode: null, get textContent() { return this.data; } }; }
  function element(tag) {
    const fns = {};
    const el = {
      nodeType: 1, tagName: tag.toUpperCase(), childNodes: [], parentNode: null, dataset: {}, attrs: {}, ownerDocument: doc,
      className: '', title: '', type: '', hidden: false, isConnected: true,
      get classList() { const self = this; return { add: (c) => { self.className = `${self.className} ${c}`.trim(); }, contains: (c) => self.className.split(/\s+/).includes(c) }; },
      get textContent() { return this.childNodes.map((c) => c.textContent).join(''); },
      set textContent(v) { this.childNodes = []; this.append(String(v)); },
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      append(...cs) { for (const c of cs) { const n = typeof c === 'string' ? text(c) : c; n.parentNode = el; el.childNodes.push(n); } },
      prepend(...cs) { const old = el.childNodes; el.childNodes = []; el.append(...cs); el.childNodes.push(...old); },
      replaceChildren(...cs) { el.childNodes = []; el.append(...cs); },
      after(n) { const p = el.parentNode; const i = p.childNodes.indexOf(el); n.parentNode = p; p.childNodes.splice(i + 1, 0, n); },
      remove() { const p = el.parentNode; if (p) p.childNodes.splice(p.childNodes.indexOf(el), 1); el.parentNode = null; },
      matches(sel) { return sel.split(',').map((s) => s.trim()).some((s) => (s.startsWith('.') ? el.className.split(/\s+/).includes(s.slice(1)) : s.startsWith('[') ? s.slice(1, -1) in el.attrs : el.tagName === s.toUpperCase())); },
      querySelectorAll(sel) { const out = []; const walk = (n) => { for (const c of n.childNodes) if (c.nodeType === 1) { if (c.matches(sel)) out.push(c); walk(c); } }; walk(el); return out; },
      querySelector(sel) { return el.querySelectorAll(sel)[0] ?? null; },
      addEventListener(t, fn) { (fns[t] ??= []).push(fn); },
      click() { for (const fn of fns.click ?? []) fn({ stopPropagation() {} }); },
    };
    return el;
  }
  return doc;
}
{
  clearTables();
  const doc = makeDoc();
  const card = doc.createElement('article');
  const head = doc.createElement('header'); head.append('Mattie Williamson');
  const p1 = doc.createElement('p'); const dot = doc.createElement('span'); dot.className = 'dot';
  p1.append(dot, 'She came to the Glessners as a maid.');
  const p2 = doc.createElement('p'); p2.append('A line nobody rewrote.');
  const key = doc.createElement('button'); key.append('She came to the Glessners as a maid.');
  card.append(head, p1, p2, key);
  const choice = createReadingChoice({ storage: mem() });
  assert.equal(readingTabs(card, { after: head, choice }), WRITTEN, 'no table: no tabs');
  assert.equal(card.querySelectorAll('.reading-tabs').length, 0);

  const drop = addTable([{ text: 'She came to the Glessners as a maid.', own: '14-15', levels: { '8-10': 'She worked for the Glessners as a maid.', '16-17': 'She entered the Glessners\' service as a maid.' } }]);
  // A table landing redraws every card already open (the scene's file arrives after the first card).
  const row = card.querySelectorAll('.reading-tabs')[0];
  assert(row, 'the table landed: the open card has its age tabs');
  assert.equal(card.childNodes.indexOf(row), 1, 'under the card\'s head');
  const tabs = row.querySelectorAll('.reading-tab');
  assert.deepEqual(tabs.map((t) => t.textContent), ['8–10', '14–15', '16–17'], 'one tab for each age the card is written at, youngest first');
  assert.equal(tabs.find((t) => t.getAttribute('aria-selected') === 'true').dataset.readingAge, '14-15', 'none chosen: the card opens in its own words');
  assert.equal(p1.childNodes[0], dot, 'the grade dot beside the words stays');
  tabs[0].click();
  assert.equal(p1.textContent, 'She worked for the Glessners as a maid.', 'a tab swaps the words in place');
  assert.equal(p1.childNodes[0], dot, '…and only the words');
  assert.equal(p2.textContent, 'A line nobody rewrote.', 'a line with no other age is left as it is');
  assert.equal(key.textContent, 'She came to the Glessners as a maid.', 'a key\'s own label is never rewritten');
  assert.equal(tabs[0].getAttribute('aria-selected'), 'true');
  tabs[1].click();
  assert.equal(p1.textContent, 'She came to the Glessners as a maid.', 'its own age gives the words as written back');

  forgetAge(card);
  choice.set(['8-10', '11-13']);
  readingTabs(card, { after: head, choice });
  assert.equal(card.querySelectorAll('.reading-tabs').length, 1, 'redrawn: the same row, not a second');
  assert.equal(card.dataset.readingAge, '14-15', 'chosen 8–10 and 11–13: the highest chosen, 11–13, is not written; the nearest older age is');
  assert(card.querySelectorAll('.reading-tab').find((t) => t.dataset.readingAge === '8-10').className.includes('reading-tab-yours'), 'the reader\'s own ages are marked');
  forgetAge(card);
  choice.set(['8-10']);
  readingTabs(card, { after: head, choice });
  assert.equal(p1.textContent, 'She worked for the Glessners as a maid.', 'chosen 8–10: the card opens at 8–10');
  forgetAge(card);
  choice.set(['18+']);
  readingTabs(card, { after: head, choice });
  assert.equal(card.dataset.readingAge, '16-17', 'chosen 18+, not written: the oldest age the card has');
  assert.equal(openingAge(['8-10', '14-15'], choice), '14-15');

  // A card retold only for younger readers: its own words are every older reader's too ("11+").
  const drop2 = addTable([{ text: 'A line nobody rewrote.', own: '11-13', levels: { '8-10': 'A plain line.' } }]);
  const p3 = doc.createElement('article'); const q = doc.createElement('p'); q.append('A line nobody rewrote.'); p3.append(q);
  choice.set(['16-17']);
  readingTabs(p3, { choice });
  const t3 = p3.querySelectorAll('.reading-tab');
  assert.deepEqual(t3.map((t) => t.textContent), ['8–10', '11+'], 'the oldest tab, its own words, says every older age reads it');
  assert.equal(t3[1].getAttribute('aria-label'), 'Ages 11 and over');
  assert.equal(p3.dataset.readingAge, '11-13', 'chosen 16–17: the card as written');
  assert(t3[1].className.includes('reading-tab-yours'), '…marked as the reader\'s');
  drop2();
  drop();
  assert.equal(card.querySelectorAll('.reading-tabs').length, 0, 'the table gone: the row goes');
  assert.equal(p1.textContent, 'She came to the Glessners as a maid.', '…and the words as written come back');
  assert.equal(lookup('She came to the Glessners as a maid.'), null);
  assert.equal(levelledIn(card).length, 0);
}

// ---- a jaunt's other tellings ------------------------------------------------------------------
{
  const base = { id: 'tour', grade_band: '6-8', opening: { text: 'JAUNT: THE TOUR. Come in.\n\nSecond.' }, premise: 'A walk.',
    stops: [{ text: 'At the door.' }, { text: 'In the court.', narrative: 'A wind.' }], legs: [{ story: 'Out on the avenue.' }], endings: [{ text: 'The end.' }], keepsake: { text: 'A card.' } };
  const young = { id: 'tour-grades-3-5', version_of: 'tour', grade_band: '3-5', opening: { text: 'JAUNT: THE TOUR. Come on in.\n\nTwo.' }, premise: 'A short walk.',
    stops: [{ text: 'Here is the door.' }, { text: 'Here is the yard.', narrative: 'It is windy.' }], legs: [{ story: 'Now we are outside.' }], endings: [{ text: 'All done.' }], keepsake: { text: 'A little card.' } };
  const grown = { ...young, id: 'tour-adults', audience: 'adults', stops: [{ text: 'Blood.' }, { text: 'More.' }] };
  const odd = { ...young, id: 'tour-grades-9-10', grade_band: '9-10', stops: [{ text: 'Only one stop.' }] };
  const t = tellingTable(base, [young, grown, odd, base]);
  assert.deepEqual(t.get('At the door.'), { own: '11-13', levels: { '8-10': 'Here is the door.' } }, 'stop for stop, the walked telling at its own band');
  assert.equal(t.get('A wind.').levels['8-10'], 'It is windy.');
  assert.equal(t.get('Come in.').levels['8-10'], 'Come on in.', 'the opening as the panel shows it, without its JAUNT: heading');
  assert.equal(t.get('Second.').levels['8-10'], 'Two.');
  assert.equal(t.get('Out on the avenue.').levels['8-10'], 'Now we are outside.', 'the road notes');
  assert.equal(t.get('The end.').levels['8-10'], 'All done.');
  assert(![...t.values()].some((e) => Object.values(e.levels).includes('Blood.')), 'an 18+ telling stages other scenes: never read here');
  assert(![...t.values()].some((e) => e.levels['14-15']), 'a telling whose stops do not line up is left out');
}

// ---- the scene table, as tools/reading_levels.py writes it -------------------------------------
{
  const doc = JSON.parse(read('data/reading/1904.json'));
  const stories = JSON.parse(read('data/residents_1904/stories.json')).stories;
  assert(doc.entries.length > 0);
  for (const e of doc.entries) {
    assert(LEVEL_IDS.includes(e.own), `${e.card}: an own age`);
    for (const age of Object.keys(e.levels)) assert(LEVEL_IDS.includes(age) && age !== e.own, `${e.card}: ${age}`);
    const [family, id] = e.card.split(':');
    if (family === 'stories') assert(stories[id].map(keyOf).includes(keyOf(e.text)), `${e.card}: its text is a paragraph of the story as written`);
  }
  const mattie = doc.entries.find((e) => e.card === 'stories:glessner_williamson_martha_l');
  assert(mattie && mattie.levels['8-10'], 'Mattie\'s card reads at 8–10');
  // A building's evidence notes and opening lines are keyed by their own words: each is a
  // line the Details tab or the card shows (tools/reading_notes.mjs, tools/reading_leads.mjs).
  const shown = (tool) => JSON.parse(execFileSync('node', [`tools/${tool}.mjs`, '1904'], { cwd: ROOT, encoding: 'utf8' }));
  const notes = new Set(shown('reading_notes').notes.map(keyOf)), leads = new Set(shown('reading_leads').leads.map(keyOf));
  const byFamily = (f) => doc.entries.filter((e) => e.card.startsWith(`${f}:`));
  assert(byFamily('notes').length > 1000, 'the 1904 evidence notes are retold');
  for (const e of byFamily('notes')) assert(notes.has(keyOf(e.text)), `${e.card.slice(0, 60)}: a note the Details tab shows`);
  assert(byFamily('leads').length > 0, 'the 1904 opening lines are retold');
  for (const e of byFamily('leads')) assert(leads.has(keyOf(e.text)), `${e.card.slice(0, 60)}: a line a card opens on`);
}

// ---- the wiring: Settings, the Jaunts menu, the cards ------------------------------------------
{
  // Settings › Display › Reading age is drawn by settings-app.js (readingAgesGroup) above
  // Appearance, so the page published at every year's door stays under the duplicate floor.
  const { readingAgesGroup } = await import('../renderers/web/js/settings-app.js');
  const make = (tag) => {
    const n = { tag, children: [], dataset: {}, attrs: {}, hidden: false, textContent: '', parentNode: null,
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      append(...c) { for (const x of c) { x.parentNode = this; this.children.push(x); } },
      insertBefore(c, ref) { c.parentNode = this; this.children.splice(this.children.indexOf(ref), 0, c); } };
    return n;
  };
  const body = make('div'); const machine = make('div'); machine.id = 's-machine'; machine.hidden = true; body.append(machine);
  const fakeDoc = { createElement: make, getElementById: (id) => body.children.find((c) => c.id === id)?.children?.find?.((c) => c.id === id) ?? body.children.find((c) => c.id === id) ?? null };
  const seg = readingAgesGroup(fakeDoc);
  const group = body.children[0];
  assert.equal(group.id, 's-reading', 'the Reading age group goes in first, above Appearance');
  assert.equal(group.dataset.setPane, 'display', 'the Reading age group sits on the Display tab');
  assert.equal(group.hidden, true, 'it starts hidden or shown with the Display groups');
  assert.deepEqual(seg.children.map((b) => b.dataset.readingAge), LEVEL_IDS, 'Settings › Display › Reading age has every age');
  assert.equal(readingAgesGroup({ getElementById: (id) => (id === 's-reading-ages' ? seg : null) }), seg, 'drawn once');
  assert(!read('renderers/web/index.html').includes('s-reading-ages'), 'the page itself carries no Reading age markup');
  for (const [file, re] of [
    ['renderers/web/js/apps/inspect-view.js', /readingTabs\(card/], ['renderers/web/js/apps/inspect-view.js', /readingTabs\(pane/],
    ['renderers/web/js/apps/inspect-view.js', /readingTabs\(page/], ['renderers/web/js/apps/people-view.js', /readingTabs\(card/],
    ['renderers/web/js/tale-card.js', /readingTabs\(card/], ['renderers/web/js/ask-card.js', /readingTabs\(card/],
    ['renderers/web/js/jaunt-panel.js', /readingTabs\(body/], ['renderers/web/js/jaunt-preview.js', /tellingTable\(content/],
    ['renderers/web/js/settings-app.js', /wireReadingAges\(readingAgesGroup\(doc\)\)/], ['renderers/web/js/main.js', /syncReading\(\{ account: api\.signIn\.account/],
    ['tools/publish.sh', /data\/reading/], ['renderers/web/js/main.js', /readingTabs\(popupRoot/],
  ]) assert(re.test(read(file)), `${file}: ${re}`);
}

console.log('test_reading_level: ages chosen and kept (device and account), card tabs at each age, a jaunt\'s tellings, the scene table');
