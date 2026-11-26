#!/usr/bin/env node
// T-2631 (NAV-402): Jaunt cards — a credited plate of the route's own stops where the
// project holds one (never a stand-in), the keepsake once earned, and the outing in
// progress pinned on top as a Continue card. Reads pictures.js § plateFor and drives
// jaunt-menu.js's real cards over a small hand-made DOM. No browser; the smoke (part 15)
// pauses a Jaunt and taps Continue in a page.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { plateFor } from '../renderers/web/js/pictures.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');

// ---- plates: credited, the stops' own, or none ---------------------------------------------
const doc = {
  image_store: { base_url: 'https://images.example.org/store/' },
  by_structure: {
    linked_only: [{ id: 'l1', title: 'A linked picture', url: 'https://holder.example/1' }],
    glessner_house: [
      { id: 'g1', kind: 'PHOTO', title: 'Glessner House, south front', creator: 'HABS photographer',
        holder: 'Library of Congress — Prints and Photographs', collection: 'HABS', rights: 'public domain', held: { t: 'thumbs/g1.jpg' } },
    ],
  },
};
assert.equal(plateFor(doc, ['nowhere', 'linked_only']), null, 'a picture that is only linked is never shown as a plate');
assert.equal(plateFor(null, ['glessner_house']), null, 'no pictures file, no plate');
const plate = plateFor(doc, ['linked_only', 'glessner_house']);
assert.equal(plate.src, 'https://images.example.org/store/thumbs/g1.jpg');
assert.equal(plate.structure, 'glessner_house', 'the first stop that has a held picture');
assert.equal(plate.credit, 'Library of Congress', 'the holder, as the card shows it');
assert.match(plate.full, /HABS photographer/);
assert.match(plate.full, /PUBLIC DOMAIN/, 'the whole credit and the rights ride along');
assert.match(plate.alt, /^PHOTO: Glessner House/);
// T-3584: a jaunt may name which held picture heads its card; an unknown one falls back to the first.
doc.by_structure.glessner_house.push({ id: 'g2', kind: 'PHOTO', title: 'Glessner House, coach-house end', holder: 'Cornell', rights: 'public domain', held: { t: 'thumbs/g2.jpg' } });
assert.equal(plateFor(doc, ['glessner_house'], 'g2').src, 'https://images.example.org/store/thumbs/g2.jpg', 'the picture the jaunt names');
assert.equal(plateFor(doc, ['glessner_house'], 'gone').src, plate.src, 'a named picture not held: the first held one');
doc.by_structure.glessner_house.pop();

// ---- the cards, over a small DOM -----------------------------------------------------------
function makeDom() {
  const make = (tag) => {
    const fns = {};
    const el = {
      tagName: tag.toUpperCase(), children: [], parent: null, dataset: {}, attrs: {}, hidden: false, disabled: false,
      title: '', type: '', value: '', src: '', alt: '', loading: '', decoding: '', tabIndex: 0, _text: '', _cls: new Set(),
      get className() { return [...this._cls].join(' '); }, set className(v) { this._cls = new Set(String(v).split(/\s+/).filter(Boolean)); },
      classList: null,
      get textContent() { return this._text + this.children.map((c) => c.textContent).join(''); },
      set textContent(v) { this._text = String(v ?? ''); this.children = []; },
      set innerHTML(v) { this._html = v; },
      get content() { const svg = make('svg'); return { firstChild: svg }; },
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      append(...cs) { for (const c of cs) { if (c == null) continue; const n = typeof c === 'string' ? Object.assign(make('#text'), { _text: c }) : c; n.parent = el; el.children.push(n); } },
      prepend(...cs) { const old = el.children; el.children = []; el.append(...cs); el.children.push(...old); },
      replaceChildren(...cs) { el.children = []; el.append(...cs); },
      addEventListener(t, fn) { (fns[t] ??= []).push(fn); },
      click() { for (const fn of fns.click ?? []) fn({ preventDefault() {} }); },
      closest: () => null, focus() {}, scrollIntoView() {}, matches: () => false,
      get isConnected() { return true; },
      querySelectorAll(sel) { return walk(el).filter((c) => matches(c, sel)); },
      querySelector(sel) { return el.querySelectorAll(sel)[0] ?? null; },
    };
    el.classList = { add: (...c) => c.forEach((x) => el._cls.add(x)), remove: (...c) => c.forEach((x) => el._cls.delete(x)),
      contains: (c) => el._cls.has(c), toggle: (c, on = !el._cls.has(c)) => { if (on) el._cls.add(c); else el._cls.delete(c); return on; } };
    return el;
  };
  const walk = (el, out = []) => { for (const c of el.children) { out.push(c); walk(c, out); } return out; };
  const matches = (el, sel) => sel.split(',').some((s) => {
    s = s.trim();
    let m;
    if ((m = /^\.([\w-]+)$/.exec(s))) return el._cls?.has(m[1]);
    if ((m = /^\[data-([\w-]+)\]$/.exec(s))) return el.dataset?.[m[1]] != null;
    if ((m = /^\[data-action="([\w-]+)"\]$/.exec(s))) return el.dataset?.action === m[1];
    if ((m = /^([a-z0-9]+)$/.exec(s))) return el.tagName === m[1].toUpperCase();
    return false;
  });
  return { createElement: make };
}
globalThis.document = makeDom();
const { createJauntMenu } = await import('../renderers/web/js/jaunt-menu.js');
const root = document.createElement('div');
const rows = [
  { id: 'prairie-walk', title: 'Prairie Walk', premise: 'Walk the avenue.', category: 'Orientation', primary_family: 'Ways & Means',
    availability: 'available', stop_count: 3, default_mode: 'walk', allowed_modes: ['walk', 'instantly'],
    destinations: [{ kind: 'structure', id: 'glessner_house' }] },
  { id: 'no-picture', title: 'No Picture', premise: 'Nowhere pictured.', category: 'Orientation', primary_family: 'Ways & Means',
    availability: 'available', stop_count: 2, default_mode: 'walk', allowed_modes: ['walk'], destinations: [{ kind: 'structure', id: 'nowhere' }] },
];
const menu = createJauntMenu({ root, estimate: () => ({ seconds: 600 }), onStart: () => true, onPreview: () => {},
  plateFor: (row) => plateFor(doc, row.destinations.map((d) => d.id)), kept: (row) => row.id === 'prairie-walk' });
menu.show(rows);
const cards = root.querySelectorAll('.jaunt-card');
assert.equal(cards.length, 2);
const byId = Object.fromEntries(cards.map((c) => [c.dataset.jaunt, c]));
const img = byId['prairie-walk'].querySelectorAll('img')[0];
assert(img && img.src === plate.src && img.loading === 'lazy', 'a plate of the route\'s own stop');
assert(byId['prairie-walk'].querySelectorAll('.jaunt-type')[0].classList.contains('has-plate'));
assert.equal(byId['prairie-walk'].querySelectorAll('.jaunt-credit')[0]?.textContent, 'Picture: Library of Congress', 'and its credit, on the card');
assert.equal(byId['prairie-walk'].querySelectorAll('.jaunt-kept')[0]?.textContent, 'Keepsake earned', 'the keepsake, once earned');
assert.equal(byId['no-picture'].querySelectorAll('img').length, 0, 'no held picture: no plate, the family icon stays');
assert.equal(byId['no-picture'].querySelectorAll('.jaunt-credit').length, 0);
assert.equal(byId['no-picture'].querySelectorAll('.jaunt-kept').length, 0, 'no keepsake, no badge');
const text = byId['prairie-walk'].textContent;
assert(/Prairie Walk/.test(text) && /Walk the avenue\./.test(text) && /3 stops/.test(text) && /10 min/.test(text),
  `title, premise, stops and minutes: ${text}`);

// T-3604 (owner, 2026-11-15: "include grade level filters for the jaunts"): a row of grade pills,
// one per band the year's jaunts have; a pill shows only that band, and Clear filters lets it go.
{
  const graded = [
    { ...rows[0], id: 'tour', title: 'The Tour', grade_band: '6-8', menu_group: 'People' },
    { ...rows[0], id: 'tour-young', title: 'The Tour', grade_band: '3-5', menu_group: 'People', version_of: 'tour' },
    { ...rows[1], id: 'style', title: 'A Style Walk', grade_band: '9-10', menu_group: 'Architecture' },
  ];
  const { createReadingChoice } = await import('../renderers/web/js/reading-level.js');
  const mem = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) }; };
  const choice = createReadingChoice({ storage: mem() });
  const groot = document.createElement('div');
  createJauntMenu({ root: groot, estimate: () => ({ seconds: 600 }), onStart: () => true, onPreview: () => {}, choice }).show(graded);
  const row = groot.querySelectorAll('.jaunt-grades')[0];
  assert(row && !row.hidden, 'a grade row when the jaunts have more than one band');
  const pills = row.querySelectorAll('.jaunt-grade-pill');
  // T-3629: Any, then the bands present, youngest first; one card per jaunt. The owner,
  // 2026-11-17: the row is "Your age", each pill the age band its grade band stands for.
  // T-3645: 18+ is a reading age too, always last: each jaunt as first told.
  assert.equal(row.querySelectorAll('.jaunt-grades-label')[0].textContent, 'Your age');
  assert.deepEqual(pills.map((p) => p.textContent), ['Any', '8–10', '11–13', '14–15', '18+'], 'Any, then the age bands present, youngest first, then 18+');
  assert.deepEqual(pills.map((p) => p.getAttribute('aria-label')), ['Any age', 'Ages 8–10', 'Ages 11–13', 'Ages 14–15', 'Ages 18 and over']);
  const shown = () => groot.querySelectorAll('.jaunt-card').map((c) => c.dataset.jaunt);
  assert.deepEqual(shown(), ['tour', 'style'], 'no grade picked: each jaunt once, as first told');
  const tags = (id) => groot.querySelectorAll('.jaunt-card').find((c) => c.dataset.jaunt === id).querySelectorAll('.jaunt-grade').map((t) => t.textContent);
  assert.deepEqual(tags('tour'), ['Grades 6–8', 'Ages 11–13'], 'each card: its age band next to its grade level');
  pills[1].click();
  assert.deepEqual(shown(), ['tour-young', 'style'], 'Ages 8–10: the 3–5 telling, and a jaunt with no 3–5 telling stays');
  assert.equal(pills[1].getAttribute('aria-pressed'), 'true');
  assert.deepEqual(choice.get(), ['8-10'], 'the pill is the reader\'s age: Settings sees it');
  // T-3645 (owner: "i can add multiple levels to see and then you would see all jaunts"): a second age adds its tellings.
  pills[2].click();
  assert.deepEqual(shown(), ['tour', 'tour-young', 'style'], 'Ages 8–10 and 11–13: both tellings of the tour, the walk once');
  assert.equal(pills[1].getAttribute('aria-pressed'), 'true'); assert.equal(pills[2].getAttribute('aria-pressed'), 'true');
  const clear = groot.querySelectorAll('.jaunt-clear')[0];
  assert(clear.hidden, 'a picked age is a choice, not a filter to clear');
  pills[1].click(); pills[2].click();
  assert.deepEqual(shown(), ['tour', 'style'], 'tapping each picked age again lets it go');
  assert.equal(pills[0].getAttribute('aria-pressed'), 'true', 'Any age again');
  choice.set(['14-15'], 'account');
  assert.deepEqual(shown(), ['tour', 'style'], 'an age chosen elsewhere (Settings, the account) redraws the list');
  assert.equal(pills[3].getAttribute('aria-pressed'), 'true');
  pills[0].click();
  assert.deepEqual(choice.get(), [], 'Any clears every age');
  // T-3623 (owner, 2026-11-16: "Do 18+ jaunts for all jaunts"): an 18+ telling is played by the
  // 18+ pill, after the bands, where it has one; the card carries the 18+ tag and no grade tag.
  const aroot = document.createElement('div');
  const grown = { ...rows[0], id: 'tour-adults', title: 'The Tour', grade_band: '6-8', menu_group: 'People', version_of: 'tour', audience: 'adults', content_warning: 'Told in full, for adults.' };
  const achoice = createReadingChoice({ storage: mem() });
  createJauntMenu({ root: aroot, estimate: () => ({ seconds: 600 }), onStart: () => true, onPreview: () => {}, choice: achoice }).show([grown, ...graded]);
  const apills = aroot.querySelectorAll('.jaunt-grades')[0].querySelectorAll('.jaunt-grade-pill');
  assert.deepEqual(apills.map((p) => p.textContent), ['Any', '8–10', '11–13', '14–15', '18+'], 'the 18+ pill comes after the age bands');
  assert.equal(apills[4].title, 'Each jaunt in its 18+ telling, where it has one');
  const ashown = () => aroot.querySelectorAll('.jaunt-card').map((c) => c.dataset.jaunt);
  assert.deepEqual(ashown(), ['tour', 'style'], 'one card per jaunt: the 18+ telling waits for its pill');
  apills[2].click();
  assert.deepEqual(ashown(), ['tour', 'style'], 'an age pill leaves the 18+ telling out');
  apills[2].click(); apills[4].click();
  assert.deepEqual(ashown(), ['tour-adults', 'style'], 'the 18+ pill plays each jaunt\'s 18+ telling where it has one, the rest as first told');
  const gcard = aroot.querySelectorAll('.jaunt-card').find((c) => c.dataset.jaunt === 'tour-adults');
  assert.equal(gcard.querySelectorAll('.jaunt-adults').length, 1, 'its 18+ tag');
  assert.equal(gcard.querySelectorAll('.jaunt-grade').length, 0, 'and no grade or age tag');
  const bchoice = createReadingChoice({ storage: mem() });
  bchoice.set(['18+']);
  createJauntMenu({ root: aroot, estimate: () => ({ seconds: 600 }), onStart: () => true, onPreview: () => {}, choice: bchoice }).show(graded);
  assert.equal(aroot.querySelectorAll('.jaunt-grade-pill').find((p) => p.textContent === '18+').title, 'Each jaunt as first told', 'with the 18+ tellings unlisted, 18+ reads each jaunt as first told');
  assert.deepEqual(ashown(), ['tour', 'style']);
  const one = document.createElement('div');
  createJauntMenu({ root: one, estimate: () => ({ seconds: 600 }), onStart: () => true, onPreview: () => {}, choice: createReadingChoice({ storage: mem() }) }).show([graded[0]]);
  assert(one.querySelectorAll('.jaunt-grades')[0].hidden, 'one band only: no grade row to choose from');
  // T-3645: the one grade T-3629 remembered becomes the first reading age.
  const old = mem(); old.setItem('chicago4d.jaunts.grade', '9-10');
  assert.deepEqual(createReadingChoice({ storage: old }).get(), ['14-15'], 'a remembered grade band is read as its age');
}

// ---- the Continue card in jaunt-preview.js ------------------------------------------------
const preview = read('renderers/web/js/jaunt-preview.js');
// T-3754: m is this route's own count of stops (routeCount), not the file's.
assert(/`Continue · Stop \$\{at \+ 1\} of \$\{routeCount\(session\) \|\| at \+ 1\}`/.test(preview), 'CONTINUE · STOP n OF m');
assert(/next \? `Next: \$\{label\(next\)\}`/.test(preview), 'Next: the next stop by name');
assert(/if \(session\.phase === 'menu'\) prefix\.unshift\(note\)/.test(preview), 'an outing in progress is pinned on top');
assert(/button\('Continue'/.test(preview), 'its key is Continue');
assert(/if \(!jauntRestoreTried\) \{ jauntRestoreTried = true; if \(!jauntRuntime\.state\.jaunt\) await jauntRuntime\.restore\(\); \}/.test(read('renderers/web/js/main.js')),
  'a saved outing is restored when the list first opens, so Continue survives a reload');

console.log('test_nav_jaunt_cards: credited plates of the stops or none, keepsakes, and Continue pinned on top');

// ---- T-2944 (owner, 2026-10-20): titles lead with what is distinctive, and the list keeps
// related outings together — by kind, featured first within it, then by name ---------------
{
  const { jauntOrder, sortTitle, filterJaunts } = await import('../renderers/web/js/jaunt-menu.js');
  const { GROUPS, groupOf } = await import('../renderers/web/js/menu-icons.js');
  const { readFileSync } = await import('node:fs');
  const catalog = (y) => JSON.parse(readFileSync(new URL(`../data/sidecars/${y}/jaunts/catalog.json`, import.meta.url), 'utf8')).jaunts;
  assert.equal(sortTitle('A Letter Home'), 'Letter Home'); assert.equal(sortTitle('An Evening Stroll'), 'Evening Stroll');
  assert.equal(sortTitle('The architects'), 'architects'); assert.equal(sortTitle('Taverns of Chicago'), 'Taverns of Chicago');
  for (const y of ['1835', '1904']) {
    const rows = filterJaunts(catalog(y));
    // T-3590: a version for another grade band takes the place of the jaunt it retells.
    const byId = new Map(rows.map((r) => [r.id, r])), place = (r) => (r.version_of ? byId.get(r.version_of) : r);
    for (const r of rows) {
      assert(!/^(Prairie Avenue|Style walk):/.test(r.title), `${y}: "${r.title}" leads with what it shares, not what it is`);
      assert(r.title.length <= 34, `${y}: "${r.title}" is short enough for two lines on a phone`);
    }
    // T-3584: ranked jaunts lead; the rest are grouped in the pills' order, every row in a group.
    for (const r of rows) assert(GROUPS.includes(r.menu_group), `${y}: ${r.id} has a menu group`);
    const rest = rows.filter((r) => !Number.isInteger(place(r).menu_rank));
    assert.deepEqual(rows.slice(0, rows.length - rest.length).map((r) => place(r).menu_rank), rows.filter((r) => Number.isInteger(place(r).menu_rank)).map((r) => place(r).menu_rank).sort((a, b) => a - b), `${y}: ranked jaunts lead, in rank order`);
    const kinds = rest.map((r) => GROUPS.indexOf(groupOf(r)));
    assert.deepEqual(kinds, [...kinds].sort((a, b) => a - b), `${y}: grouped, in the pills' order`);
    for (let i = 1; i < rows.length; i++) assert(jauntOrder(rows[i - 1], rows[i], (r) => byId.get(r.version_of)) < 0, `${y}: ${rows[i - 1].title} before ${rows[i].title}`);
  }
  // T-3584 (owner, 2026-11-13): the household tour first, then the other Glessner jaunt, the
  // build log last, and the two Glessner cards carry a picture of the house.
  const r1904 = filterJaunts(catalog('1904'));
  // T-3590: the household tour's retellings sit right after it, youngest band first (T-3621:
  // every jaunt now has one per band); the orientation and its retellings follow.
  const tellings = (id) => [id, ...['3-5', '6-8', '9-10', '11-12'].map((g) => `${id}-grades-${g}`), `${id}-adults`].filter((x) => r1904.some((r) => r.id === x));
  const lead = [...tellings('glessner-household-tour'), ...tellings('prairie-avenue-orientation')];
  assert.deepEqual(lead.slice(0, 6), ['glessner-household-tour', 'glessner-household-tour-grades-3-5', 'glessner-household-tour-grades-9-10', 'glessner-household-tour-grades-11-12', 'glessner-household-tour-adults', 'prairie-avenue-orientation']);
  assert.deepEqual(r1904.slice(0, lead.length).map((r) => r.id), lead);
  assert.equal(r1904.at(-1).id, 'prairie-built-so-far');
  for (const r of r1904.slice(0, lead.length)) assert.equal(r.plate?.structure, 'glessner_house', `${r.id} names its card picture`);
  assert.deepEqual(filterJaunts(catalog('1904'), '', 'Architecture').filter((r) => !r.version_of).map((r) => r.id).sort(), ['prairie-architects', 'prairie-style-italianate', 'prairie-style-romanesque', 'prairie-style-second-empire']);
  const t1904 = r1904.filter((r) => !r.version_of).map((r) => r.title);
  const styles = t1904.map((t, i) => (/ style walk$/.test(t) ? i : -1)).filter((i) => i >= 0);
  assert.deepEqual(styles.map((i) => t1904[i]), ['Italianate style walk', 'Romanesque style walk', 'Second Empire style walk']);
  assert.equal(styles[2] - styles[0], 2, 'the three style walks sit together');
  // T-3590: every jaunt names its school grade band; the household tour reads at 6-8 and its retelling at 3-5.
  const { GRADE_BANDS, gradeLabel } = await import('../renderers/web/js/jaunt-menu.js');
  for (const y of ['1812', '1835', '1904']) for (const r of catalog(y)) assert(GRADE_BANDS.includes(r.grade_band), `${y}: ${r.id} has a grade band`);
  const band = Object.fromEntries(r1904.map((r) => [r.id, r.grade_band]));
  assert.equal(band['glessner-household-tour'], '6-8');
  assert.equal(band['glessner-household-tour-grades-3-5'], '3-5');
  assert.equal(r1904[1].version_of, 'glessner-household-tour');
  assert.equal(gradeLabel('3-5'), 'Grades 3–5'); assert.equal(gradeLabel('9-10'), 'Grades 9–10'); assert.equal(gradeLabel(undefined), '');
  // The search finds the band, not a fixed list: the generated build-log jaunt is re-measured on
  // every landing and sits on the 3-5 / 6-8 line (grade 5.9-6.0), so it may join either band.
  const g35 = filterJaunts(catalog('1904'), 'grades 3–5');
  assert(g35.some((r) => r.id === 'glessner-household-tour-grades-3-5'), 'the grade band is searchable');
  assert(g35.every((r) => r.grade_band === '3-5'), 'a grade search returns only that band');
  // T-3604: the grade filter, alone and with a group; the retelling keeps the tour's own name.
  const f35 = filterJaunts(catalog('1904'), '', '', '3-5');
  assert(f35.some((r) => r.id === 'glessner-household-tour-grades-3-5') && f35.every((r) => r.grade_band === '3-5'), 'the grade filter');
  const people68 = filterJaunts(catalog('1904'), '', 'People', '6-8');
  assert(people68.some((r) => r.id === 'glessner-household-tour') && people68.every((r) => r.grade_band === '6-8' && r.menu_group === 'People'), 'grade and group together');
  assert.equal(r1904[1].title, r1904[0].title, 'the grades 3-5 retelling is named as the tour it retells; its grade tag tells them apart');
  // T-3623 (owner, 2026-11-16: "Do 18+ jaunts for all jaunts, fill them in"): every jaunt but the
  // build log has an 18+ telling under the same title and stops, with no warning text in its words.
  for (const y of ['1812', '1835', '1904']) {
    const all = catalog(y), grown = new Map(all.filter((r) => r.audience === 'adults').map((r) => [r.version_of, r]));
    for (const r of all.filter((r) => !r.version_of && r.menu_group !== 'Build log')) {
      const g = grown.get(r.id);
      assert(g, `${y}: ${r.id} has an 18+ telling`);
      assert.equal(g.title, r.title, `${y}: ${g.id} keeps the title`);
      assert.equal(g.stop_count, r.stop_count, `${y}: ${g.id} keeps the stops`);
      assert(g.featured !== true && g.content_warning && !/18\+|no child|for adults/i.test(g.premise), `${y}: ${g.id} is never featured, and its premise reads as story`);
    }
  }
}

// ---- T-3629 (owner, 2026-11-16, the interface sweep): one card per jaunt, the picked grade's
// telling where there is one, else the jaunt itself; nothing else is lost or reordered.
{
  const { filterJaunts, oneTellingEach } = await import('../renderers/web/js/jaunt-menu.js');
  const { readFileSync } = await import('node:fs');
  for (const y of ['1812', '1835', '1904']) {
    const all = filterJaunts(JSON.parse(readFileSync(new URL(`../data/sidecars/${y}/jaunts/catalog.json`, import.meta.url), 'utf8')).jaunts);
    const roots = new Set(all.map((r) => r.version_of || r.id));
    for (const g of ['', '3-5', '6-8', '9-10', '11-12']) {
      const once = oneTellingEach(all, g);
      assert.equal(once.length, roots.size, `${y} grade "${g}": every jaunt exactly once`);
      assert.deepEqual(once, all.filter((r) => once.includes(r)), `${y}: the list keeps its order`);
      for (const r of once) {
        const tellings = all.filter((x) => (x.version_of || x.id) === (r.version_of || r.id));
        if (g && tellings.some((x) => x.grade_band === g)) assert.equal(r.grade_band, g, `${y}: ${r.id} is the ${g} telling`);
        else if (!g) assert(!r.version_of || !tellings.some((x) => !x.version_of), `${y}: with no grade, ${r.id} is the jaunt itself`);
      }
    }
  }
  console.log('test_nav_jaunt_cards: one card per jaunt, told for the picked grade');
}

// ---- T-3711 (owner, 2026-11-20: "for all the jaunts with music or narration allow that to be
// added as a filter so we can filter and include only those jaunts with narration"): the catalog
// says which jaunts are read aloud (data/narration/voices.json) and which have music
// (data/music/jaunts.json, once the score's cues are attached); a Listen row filters on them.
{
  const { filterJaunts, LISTENS } = await import('../renderers/web/js/jaunt-menu.js');
  const { readFileSync, existsSync } = await import('node:fs');
  const listed = (p) => new Set((existsSync(new URL(p, import.meta.url)) ? JSON.parse(readFileSync(new URL(p, import.meta.url), 'utf8')).jaunts : [])
    .map((e) => (typeof e === 'string' ? e : e.id)));
  const voiced = listed('../data/narration/voices.json'), scored = listed('../data/music/jaunts.json');
  assert.deepEqual(LISTENS.map((l) => l.id), ['narrated', 'music']);
  let narrated = 0;
  for (const y of ['1812', '1835', '1871', '1904']) {
    const all = JSON.parse(readFileSync(new URL(`../data/sidecars/${y}/jaunts/catalog.json`, import.meta.url), 'utf8')).jaunts;
    for (const r of all) {
      assert.equal(r.narrated === true, voiced.has(r.id), `${y}: ${r.id} is narrated exactly when voices.json lists it`);
      assert.equal(r.music === true, scored.has(r.id), `${y}: ${r.id} has music exactly when data/music/jaunts.json lists it`);
      assert(r.narrated === undefined || r.narrated === true, 'the flag is written only when true');
    }
    const only = filterJaunts(all, '', '', '', ['narrated']);
    assert.deepEqual(only.map((r) => r.id).sort(), all.filter((r) => voiced.has(r.id)).map((r) => r.id).sort(), `${y}: Narrated lists only the narrated jaunts`);
    narrated += only.length;
  }
  assert(narrated >= 20, `the voiced jaunts are flagged (${narrated})`);
  assert(filterJaunts([{ id: 'a', title: 'A', narrated: true }, { id: 'b', title: 'B', narrated: true, music: true }], '', '', '', ['narrated', 'music']).map((r) => r.id).join() === 'b', 'two picked: only jaunts with both');
  assert.deepEqual(filterJaunts([{ id: 'a', title: 'A', narrated: true }, { id: 'b', title: 'B' }], 'narrated').map((r) => r.id), ['a'], 'a search for "narrated" finds them too');

  // T-3735 (the owner, 2026-11-23): Narrated judges the telling for the reader's ages. With
  // 11-12 picked and only the 6-8 telling voiced, the jaunt is not listed under Narrated (its
  // 6-8 telling is never put in its place); with 6-8 picked it is.
  {
    const { listTellings } = await import('../renderers/web/js/jaunt-menu.js');
    const t = (id, band, extra = {}) => ({ id, title: 'Walk', premise: '', category: 'walk', menu_group: 'Places', grade_band: band, ...extra });
    const tellings = [t('walk', '6-8', { narrated: true }), t('walk-grades-11-12', '11-12', { version_of: 'walk' }), t('walk-grades-3-5', '3-5', { version_of: 'walk', narrated: true })];
    const ids = (bands, listen = ['narrated']) => listTellings(tellings, { bands, listen }).map((r) => r.id);
    assert.deepEqual(ids(['11-12']), [], 'an unvoiced telling is not listed as narrated, nor another age\'s in its place');
    assert.deepEqual(ids(['11-12'], []), ['walk-grades-11-12'], 'without the pick the reader still gets their own telling');
    assert.deepEqual(ids(['6-8']), ['walk']); assert.deepEqual(ids(['3-5']), ['walk-grades-3-5']);
    assert.deepEqual(ids(['3-5', '11-12']).sort(), ['walk-grades-3-5'], 'several ages: each voiced telling of theirs, no other');
    assert.deepEqual(ids([]), ['walk'], 'no age picked: the jaunt itself, as before');
    for (const y of ['1812', '1904']) {
      const all = JSON.parse(readFileSync(new URL(`../data/sidecars/${y}/jaunts/catalog.json`, import.meta.url), 'utf8')).jaunts;
      for (const band of ['3-5', '6-8', '9-10', '11-12'])
        for (const r of listTellings(all, { bands: [band], listen: ['narrated'] }))
          assert(r.narrated === true && voiced.has(r.id), `${y} ${band}: ${r.id} is listed under Narrated only as a voiced telling`);
    }
  }

  // The row, over the hand-made DOM.
  const base = { premise: 'Walk.', category: 'walk', menu_group: 'Places', grade_band: '6-8', availability: 'available', stop_count: 2,
    default_mode: 'walk', allowed_modes: ['walk'], destinations: [{ kind: 'structure', id: 'nowhere' }] };
  const heard = [{ ...base, id: 'voiced', title: 'Voiced', narrated: true }, { ...base, id: 'quiet', title: 'Quiet' }, { ...base, id: 'tune', title: 'Tune', music: true, narrated: true }];
  const lroot = document.createElement('div');
  createJauntMenu({ root: lroot, estimate: () => ({ seconds: 600 }), onStart: () => true, onPreview: () => {} }).show(heard);
  const row = lroot.querySelectorAll('.jaunt-hears')[0];
  assert(row && !row.hidden, 'a Listen row when a jaunt is narrated');
  const lpills = row.querySelectorAll('.jaunt-hears-pill');
  assert.deepEqual(lpills.map((p) => p.dataset.listen), ['narrated', 'music'], 'Narrated, then Music');
  const lshown = () => lroot.querySelectorAll('.jaunt-card').map((c) => c.dataset.jaunt);
  assert.deepEqual(lshown().sort(), ['quiet', 'tune', 'voiced']);
  const tagOf = (id) => lroot.querySelectorAll('.jaunt-card').find((c) => c.dataset.jaunt === id).querySelectorAll('.jaunt-hear').map((t) => t.dataset.hear);
  assert.deepEqual(tagOf('voiced'), ['narrated'], 'a narrated card says so'); assert.deepEqual(tagOf('quiet'), [], 'a quiet one says nothing');
  assert.deepEqual(tagOf('tune'), ['narrated', 'music']);
  lpills[0].click();
  assert.deepEqual(lshown().sort(), ['tune', 'voiced'], 'Narrated: only the narrated jaunts');
  assert.equal(lpills[0].getAttribute('aria-pressed'), 'true');
  const lclear = lroot.querySelectorAll('.jaunt-clear')[0];
  assert(!lclear.hidden, 'a Listen pick is a filter Clear filters lets go');
  lpills[1].click();
  assert.deepEqual(lshown(), ['tune'], 'Narrated and Music: only jaunts with both');
  lclear.click();
  assert.deepEqual(lshown().sort(), ['quiet', 'tune', 'voiced'], 'Clear filters: every jaunt again');
  assert.equal(lpills[0].getAttribute('aria-pressed'), 'false');
  const sroot = document.createElement('div');
  createJauntMenu({ root: sroot, estimate: () => ({ seconds: 600 }), onStart: () => true, onPreview: () => {} }).show([heard[1]]);
  assert(sroot.querySelectorAll('.jaunt-hears')[0].hidden, 'no narrated jaunt this year: no Listen row');
  const nroot = document.createElement('div');
  createJauntMenu({ root: nroot, estimate: () => ({ seconds: 600 }), onStart: () => true, onPreview: () => {} }).show(heard.slice(0, 2));
  assert.deepEqual(nroot.querySelectorAll('.jaunt-hears-pill').map((p) => p.dataset.listen), ['narrated'], 'no jaunt has music yet: no Music pill');
  console.log('test_nav_jaunt_cards: a Listen row filters to narrated jaunts (and music, once a jaunt has it)');
}
