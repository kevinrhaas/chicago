#!/usr/bin/env node
// T-3672 — a teacher's route (js/teacher-route.js, js/teacher-route-view.js): one link and one
// file that carry the same bounded object; malformed, over-long, wrong-year and unknown-id
// routes degrade to the town with a message; the teacher's words reach the page as text only;
// a student's answers go to the local field notebook. Read against the real 1812, 1835 and
// 1904 directories and jaunt catalogs.
//
//   node tools/test_teacher_route.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  ROUTE_LIMITS, ROUTE_FORMAT, normalRoute, packRoute, unpackRoute, encodeRoute, decodeRoute, parseRouteLink,
  routeLink, routeFileText, routeFileName, readRouteFile, routeCatalog, jauntStops, routeSession, answerEntry,
  answerTitle, savedAnswer, cleanText, createRouteStore,
} from '../renderers/web/js/teacher-route.js';
import { createFieldNotebook } from '../renderers/web/js/field-notebook.js';
import { t } from '../renderers/web/js/strings/index.js';
import '../renderers/web/js/strings/route.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA = process.env.C4D_TEST_ROOT ? path.join(process.env.C4D_TEST_ROOT, 'data') : path.join(ROOT, 'data');
const read = (p) => JSON.parse(fs.readFileSync(path.join(DATA, p), 'utf8'));
const HREF = 'https://chicago.polecat.live/4d/dev/1904/?debug=1&token=private&nav=map#secret';
const base = {
  year: '1904', title: 'Prairie Avenue in 1904',
  stops: [
    { kind: 'place', id: 'glessner_house', note: 'Look at the walls facing the street.', question: 'Why so few windows on this side?' },
    { kind: 'person', id: 'pa1904_glessner_john_jacob', question: 'What did he do for a living?' },
    { kind: 'spot', id: 'glessner_house' },
  ],
};

// ---- the object: normalized, bounded, refused whole when malformed -------------------- //
const route = normalRoute(base);
assert.deepEqual(route.stops[2], { kind: 'spot', id: 'glessner_house', note: '', question: '' });
assert.equal(route.version, 1);
assert.equal(route.jaunt, null);
assert.equal(normalRoute({ ...base, title: 'x'.repeat(ROUTE_LIMITS.title) }).title.length, ROUTE_LIMITS.title);
assert.equal(normalRoute({ ...base, title: 'x'.repeat(ROUTE_LIMITS.title + 1) }), null, 'an over-long title refuses the route, never cuts it');
assert.equal(normalRoute({ ...base, title: 'é'.repeat(ROUTE_LIMITS.title) })?.title.length, ROUTE_LIMITS.title, 'the bound counts characters');
const long = (field, n) => normalRoute({ ...base, stops: [{ kind: 'place', id: 'a', [field]: 'y'.repeat(n) }] });
assert.ok(long('note', ROUTE_LIMITS.note)); assert.equal(long('note', ROUTE_LIMITS.note + 1), null);
assert.ok(long('question', ROUTE_LIMITS.question)); assert.equal(long('question', ROUTE_LIMITS.question + 1), null);
const many = (n) => normalRoute({ ...base, stops: Array.from({ length: n }, (_, i) => ({ kind: 'place', id: `b${i}` })) });
assert.equal(many(ROUTE_LIMITS.stops).stops.length, 20);
assert.equal(many(ROUTE_LIMITS.stops + 1), null, 'more than twenty stops refuses the route');
for (const bad of [null, [], 'route', { ...base, year: '2026' }, { ...base, year: '../1904' }, { ...base, version: 2 },
  { ...base, stops: 'x' }, { ...base, stops: [] }, { ...base, title: 7 }, { ...base, jaunt: '../x' }, { ...base, jaunt: 3 },
  { ...base, stops: [{ kind: 'house', id: 'a' }] }, { ...base, stops: [{ kind: 'place', id: '../etc' }] },
  { ...base, stops: [{ kind: 'place', id: '<script>' }] }, { ...base, stops: [{ kind: 'place', id: 'a', note: { x: 1 } }] },
  { ...base, stops: [null] }, { ...base, stops: [{ kind: 'place', id: 'x'.repeat(97) }] }]) {
  assert.equal(normalRoute(bad), null, `refused: ${JSON.stringify(bad)?.slice(0, 80)}`);
}
assert.ok(normalRoute({ year: '1835', title: '', jaunt: 'a-decent-coat', stops: [] }), 'a jaunt alone is a route');
assert.equal(cleanText('a\u0000b‮ c\r\n\r\n\r\n\r\nd   e\t', 50), 'ab‮c\n\nd e', 'control characters out, blank lines and spaces closed up');
assert.equal(cleanText('one\ntwo', 50, { lines: false }), 'one two', 'a title is one line');

// ---- the link: one parameter, the page's own path, nothing else carried -------------- //
assert.deepEqual(unpackRoute(packRoute(route)), route, 'the compact form round-trips');
const param = encodeRoute(route);
assert.match(param, /^[A-Za-z0-9_-]+$/, 'base64url, no padding');
assert.deepEqual(decodeRoute(param), route);
const link = routeLink(route, HREF);
const url = new URL(link);
assert.equal(url.pathname, '/4d/dev/1904/');
assert.deepEqual([...url.searchParams.keys()], ['route'], 'only the route: no debug flag, token or other app');
assert.equal(url.hash, '');
assert.deepEqual(parseRouteLink(url.search).route, route);
assert.equal(routeLink(route, 'javascript:alert(1)'), null);
assert.equal(new URL(routeLink(route, 'https://x.test/4d/walk/?year=1904&debug=1')).searchParams.get('year'), '1904', 'a ?year page keeps its year');
const unicode = normalRoute({ ...base, title: 'Chicago — “Prairie” ✓', stops: [{ kind: 'place', id: 'a', note: 'Ça va? 日本 🙂' }] });
assert.deepEqual(parseRouteLink(new URL(routeLink(unicode, HREF)).search).route, unicode, 'UTF-8 round-trips');
// A full route of the longest notes cannot fit one link; the link says so rather than cutting it.
const fullest = normalRoute({ ...base, stops: Array.from({ length: 20 }, (_, i) => ({ kind: 'place', id: `b${i}`, note: 'n'.repeat(280), question: 'q'.repeat(280) })) });
assert.ok(fullest);
assert.equal(routeLink(fullest, HREF), null, 'over the link bound: no link');
assert.ok(routeFileText(fullest), '…but the file still carries it');
// Hostile and broken links: refused whole, and said.
assert.equal(parseRouteLink('?nav=map'), null, 'no route parameter is no route');
for (const search of ['?route=', '?route=%%%', '?route=abc$', `?route=${encodeURIComponent(btoa('not json'))}`,
  `?route=${Buffer.from(JSON.stringify({ v: 1, y: '1904', t: 'x', s: [['z', 'a']] })).toString('base64url')}`,
  `?route=${Buffer.from(JSON.stringify({ v: 1, y: '1904', t: 'x', s: [['b', 'a', 'n', 'q', 'extra']] })).toString('base64url')}`,
  `?route=${Buffer.from([0xff, 0xfe, 0x7b]).toString('base64url')}`,
  `?route=${Buffer.from(JSON.stringify([1, 2])).toString('base64url')}`]) {
  assert.deepEqual(parseRouteLink(search), { error: 'malformed' }, search);
}
assert.deepEqual(parseRouteLink(`?route=${'A'.repeat(ROUTE_LIMITS.url + 1)}`), { error: 'long' });
assert.deepEqual(parseRouteLink(`?route=${param}&pad=${'x'.repeat(ROUTE_LIMITS.url)}`), { error: 'long' }, 'the whole query is bounded');

// ---- the file: the same object, readable, and nothing else accepted ------------------- //
const file = routeFileText(route);
assert.equal(JSON.parse(file).format, ROUTE_FORMAT);
assert.deepEqual(readRouteFile(file), route, 'the file round-trips');
assert.equal(routeFileName(route), '4d-chicago-route-1904-prairie-avenue-in-1904.json');
assert.equal(readRouteFile(JSON.stringify(route)), null, 'a file without its format line is not a route file');
assert.equal(readRouteFile('{'), null);
assert.equal(readRouteFile(' '.repeat(ROUTE_LIMITS.file + 1)), null, 'a file over the bound is not read');
assert.equal(readRouteFile(JSON.stringify({ format: ROUTE_FORMAT, ...route, stops: [{ kind: 'place', id: '<b>' }] })), null);

// ---- against the real scenes: every jaunt and person can be named ---------------------- //
for (const year of ['1812', '1835', '1904']) {
  const people = read(`sidecars/${year}/people.json`).people;
  const jaunts = read(`sidecars/${year}/jaunts/catalog.json`).jaunts;
  // Go to's rows, as main.js hands them in (destinations.targets): here, each jaunt's own stops.
  const targets = [];
  for (const j of jaunts) for (const d of j.destinations ?? []) targets.push({ kind: d.kind, id: d.id, label: `${d.kind} ${d.id}` });
  const catalog = routeCatalog({ year, targets, people, jaunts });
  const offered = jaunts.filter((r) => r.availability === 'available' && r.audience !== 'adults' && !r.version_of);
  assert.equal(catalog.jaunts.length, offered.length, `${year}: every jaunt a class may take, once each`);
  assert(!catalog.jaunts.some((j) => jaunts.find((r) => r.id === j.id).audience === 'adults'), 'never an 18+ telling');
  for (const j of catalog.jaunts) {
    const { stops, dropped } = jauntStops(j, catalog);
    assert.equal(dropped, 0, `${year} ${j.id}: every stop is a building or viewpoint the town holds`);
    assert(stops.length > 0 && stops.length <= 20);
    const r = normalRoute({ year, title: j.title.slice(0, 80), jaunt: j.id, stops: stops.map((s) => ({ ...s, question: 'What do you notice here?' })) });
    const href = routeLink(r, `https://chicago.polecat.live/4d/${year}/`);
    assert(href, `${year} ${j.id}: a jaunt's route with a question at every stop fits one link`);
    const { session } = routeSession(parseRouteLink(new URL(href).search), { year, catalog, href });
    assert.equal(session.state, 'ready');
    assert.equal(session.skipped, 0);
    assert.equal(session.jaunt.id, j.id);
    assert.deepEqual(session.stops.map((s) => s.id), stops.map((s) => s.id), 'stops in order');
  }
  const here = people.filter((p) => p.lived_here?.on_scene_date !== 'no');
  assert(here.length > 0);
  for (const p of here) assert.equal(catalog.get('person', p.id)?.label, p.name, `${year}: ${p.id} can be a stop`);
  assert(catalog.search(here[0].name.split(' ').at(-1)).some((r) => r.kind === 'person'), `${year}: people are found by name`);
}
{
  // Go there for a person who is not placed in town is their house, where the scene has it.
  const people = read('sidecars/1904/people.json').people;
  const glessner = people.find((p) => p.lives_at === 'glessner_house');
  const catalog = routeCatalog({ year: '1904', people, has: (id) => id === 'glessner_house' });
  assert.equal(catalog.get('person', glessner.id).home, 'glessner_house');
  assert.equal(routeCatalog({ year: '1904', people, has: () => false }).get('person', glessner.id).home, null, 'never a house the scene does not hold');
}
assert.deepEqual(jauntStops({ destinations: [{ kind: 'structure', id: 'a' }, { kind: 'structure', id: 'a' }, { kind: 'photo', id: 'p' }, { kind: 'anchor', id: 'v' }] },
  routeCatalog({ targets: [{ kind: 'structure', id: 'a', label: 'A' }, { kind: 'anchor', id: 'v', label: 'V' }] })),
{ stops: [{ kind: 'place', id: 'a', note: '', question: '' }, { kind: 'spot', id: 'v', note: '', question: '' }], dropped: 1 },
'a jaunt\'s stops: repeats closed up, what the town does not hold counted');

// ---- a student's arrival --------------------------------------------------------------- //
const catalog = routeCatalog({ year: '1904', targets: [{ kind: 'structure', id: 'glessner_house', label: 'Glessner House' },
  { kind: 'anchor', id: 'glessner_house', label: 'Glessner corner' }], people: [{ id: 'pa1904_glessner_john_jacob', name: 'John J. Glessner', lives_at: 'glessner_house' }] });
const arrived = routeSession(parseRouteLink(url.search), { year: '1904', catalog, href: HREF });
assert.equal(arrived.session.state, 'ready');
assert.deepEqual(arrived.session.stops.map((s) => [s.n, s.label]), [[1, 'Glessner House'], [2, 'John J. Glessner'], [3, 'Glessner corner']]);
assert.equal(arrived.message.key, 'route.arrived');
assert.equal(new URL(arrived.session.link).search, url.search, 'the panel keeps the same link');
const fewer = routeSession({ route: normalRoute({ ...base, stops: [...base.stops, { kind: 'place', id: 'gone_house' }, { kind: 'person', id: 'nobody' }] }) },
  { year: '1904', catalog, href: HREF });
assert.equal(fewer.session.skipped, 2, 'unknown ids are dropped and counted');
assert.equal(fewer.message.key, 'route.arrivedSkipped');
assert.match(t(fewer.message.key, fewer.message.params), /2 stops are not in this town/);
const none = routeSession({ route: normalRoute({ ...base, stops: [{ kind: 'place', id: 'gone_house' }] }) }, { year: '1904', catalog, href: HREF });
assert.equal(none.session, null, 'nothing known: the town as usual');
assert.equal(none.message.key, 'route.nothing');
const lostJaunt = routeSession({ route: normalRoute({ ...base, jaunt: 'no-such-jaunt' }) }, { year: '1904', catalog, href: HREF });
assert.equal(lostJaunt.session.jauntMissing, true, 'a jaunt this year does not offer is said, the stops kept');
const other = routeSession(parseRouteLink(url.search), { year: '1835', catalog, href: 'https://chicago.polecat.live/4d/dev/1835/?route=x' });
assert.equal(other.session.state, 'wrong-year');
assert.equal(new URL(other.session.link).pathname, '/4d/dev/1904/', 'a route for another year offers that year\'s link');
assert.deepEqual(parseRouteLink(new URL(other.session.link).search).route, route);
assert.equal(other.message.key, 'route.otherYear');
for (const [parsed, key] of [[{ error: 'malformed' }, 'route.invalid'], [{ error: 'long' }, 'route.long']]) {
  const r = routeSession(parsed, { year: '1904', catalog });
  assert.equal(r.session, null); assert.equal(r.message.key, key);
}
assert.deepEqual(routeSession(null, { year: '1904' }), { session: null, message: null });

// ---- answers: in the local notebook, findable by route and stop ---------------------- //
const memory = new Map();
const storage = { getItem: (k) => memory.get(k) ?? null, setItem: (k, v) => memory.set(k, String(v)) };
const notebook = createFieldNotebook({ storage });
const session = arrived.session, stop = session.stops[0];
assert.equal(answerTitle(session, stop), 'Route: Prairie Avenue in 1904 · Stop 1: Glessner House');
assert.equal(answerEntry(session, stop, '   '), null, 'an empty answer is not saved');
const entry = answerEntry(session, stop, 'To keep the street out.');
assert.match(entry.text, /^Teacher’s question: Why so few windows on this side\?\n\nMy answer: To keep the street out\.$/);
assert.equal(notebook.add(entry).ok, true);
assert.deepEqual(savedAnswer(notebook.read().entries, session, stop).answer, 'To keep the street out.');
assert.equal(savedAnswer(notebook.read().entries, session, session.stops[1]), null);
const store = createRouteStore();
const seen = [];
const off = store.subscribe((s) => seen.push(s?.title ?? null));
store.set(session); store.clear(); off(); store.set(session);
assert.deepEqual(seen, ['Prairie Avenue in 1904', null]);

// ---- the screens: a small DOM, and the teacher's words only ever as text -------------- //
function makeDoc() {
  const all = [];
  const text = (data) => ({ nodeType: 3, data: String(data), parentNode: null, get textContent() { return this.data; } });
  const el = (tag) => {
    const fns = {};
    const e = {
      nodeType: 1, tagName: tag.toUpperCase(), childNodes: [], parentNode: null, attrs: {}, dataset: {}, className: '', id: '',
      hidden: false, disabled: false, value: '', type: '', files: null,
      get children() { return this.childNodes.filter((c) => c.nodeType === 1); },
      get textContent() { return this.childNodes.map((c) => c.textContent).join(''); },
      set textContent(v) { this.childNodes = []; if (v !== '' && v != null) this.append(String(v)); },
      set innerHTML(v) { throw new Error(`innerHTML was set: ${v}`); },
      get ownerDocument() { return doc; },
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      append(...cs) { for (const c of cs) { const n = typeof c === 'string' ? text(c) : c; if (n.parentNode) n.parentNode.childNodes.splice(n.parentNode.childNodes.indexOf(n), 1); n.parentNode = e; e.childNodes.push(n); } },
      replaceChildren(...cs) { for (const c of e.childNodes) c.parentNode = null; e.childNodes = []; e.append(...cs); },
      remove() { const p = this.parentNode; if (p) p.childNodes.splice(p.childNodes.indexOf(this), 1); this.parentNode = null; },
      addEventListener(type, f) { (fns[type] ??= []).push(f); },
      fire(type) { return Promise.all((fns[type] ?? []).map((f) => f({ target: e, preventDefault() {} }))); },
      click() { return this.fire('click'); },
      focus() { doc.activeElement = e; }, select() {},
    };
    all.push(e);
    return e;
  };
  const doc = { createElement: el, activeElement: null, defaultView: null };
  doc.body = el('body');
  return doc;
}
const walk = (root, out = []) => { for (const c of root.children ?? []) { out.push(c); walk(c, out); } return out; };
const byClass = (root, c) => walk(root).filter((n) => n.className.split(' ').includes(c));
const byText = (root, tag, words) => walk(root).find((n) => n.tagName === tag && n.textContent === words);
const settle = () => new Promise((r) => setTimeout(r, 0));
const { mountRoutePanel, mountRouteBuilder } = await import('../renderers/web/js/teacher-route-view.js');
{
  const doc = makeDoc();
  const host = doc.createElement('div');
  const hostile = '<img src=x onerror=alert(1)> & "quotes"';
  const panelStore = createRouteStore();
  const went = [], cards = [], started = [];
  const ctx = { navigator: { detent: 'half', docked: 0, dock() { this.docked++; } }, api: { jaunts: { start: (id) => started.push(id) } },
    actions: { routeGo: (s) => { went.push(s.id); return true; }, openPerson: (id) => cards.push(id) } };
  const panel = mountRoutePanel(host, ctx, { notebook, store: panelStore });
  assert.equal(host.hidden, true, 'no route open: nothing shown');
  const hostileRoute = normalRoute({ ...base, title: hostile, jaunt: 'a-decent-coat', stops: [{ kind: 'place', id: 'glessner_house', note: hostile, question: hostile },
    { kind: 'person', id: 'pa1904_glessner_john_jacob' }] });
  const shown = routeSession({ route: hostileRoute }, { year: '1904', catalog: routeCatalog({ ...catalog, year: '1904',
    targets: [{ kind: 'structure', id: 'glessner_house', label: 'Glessner House' }],
    people: [{ id: 'pa1904_glessner_john_jacob', name: 'John J. Glessner' }],
    jaunts: [{ id: 'a-decent-coat', title: 'A Decent Coat', availability: 'available' }] }), href: HREF }).session;
  panelStore.set(shown);
  assert.equal(host.hidden, false);
  const words = byClass(host, 'route-teacher-words');
  assert.deepEqual(words.map((w) => w.textContent), [hostile, hostile], 'the teacher\'s note and question, word for word, as text');
  assert(walk(host).every((n) => !['IMG', 'SCRIPT'].includes(n.tagName)), 'no markup made from the teacher\'s words');
  assert.deepEqual(byClass(host, 'route-teacher-k').map((k) => k.textContent), ['Teacher’s note', 'Teacher’s question'], 'labelled as the teacher\'s words');
  assert(host.textContent.includes('not the town’s sources'), 'and said not to be the town\'s sources');
  assert.equal(byClass(host, 'route-panel-stop').length, 2);
  const go = byClass(host, 'route-go');
  await go[0].click(); await settle();
  assert.deepEqual(went, ['glessner_house']);
  assert.equal(ctx.navigator.docked, 1, 'on a phone the device steps down for the ride');
  await byText(host, 'BUTTON', 'Their card').click();
  assert.deepEqual(cards, ['pa1904_glessner_john_jacob']);
  await byText(host, 'BUTTON', 'Start the jaunt').click();
  assert.deepEqual(started, ['a-decent-coat']);
  const area = walk(host).find((n) => n.tagName === 'TEXTAREA');
  const save = byText(host, 'BUTTON', 'Save answer to notebook');
  await save.click();
  assert(host.textContent.includes('Write an answer first.'));
  area.value = 'Stone, mostly.'; await area.fire('input'); await save.click();
  const mine = notebook.read().entries.filter((e) => e.title.startsWith('Route: <img'));
  assert.equal(mine.length, 1, 'one notebook entry for the answer');
  assert(mine[0].text.endsWith('My answer: Stone, mostly.'));
  area.value = 'Stone and brick.'; await save.click();
  const again = notebook.read().entries.filter((e) => e.title.startsWith('Route: <img'));
  assert.equal(again.length, 1, 'saving again updates the same entry');
  assert(again[0].text.endsWith('My answer: Stone and brick.'));
  panel.refresh(ctx);
  assert.equal(walk(host).find((n) => n.tagName === 'TEXTAREA').value, 'Stone and brick.', 'a reopened panel shows the saved answer');
  await byText(host, 'BUTTON', 'Close the route').click();
  assert.equal(panelStore.get(), null); assert.equal(host.hidden, true);
  // Another year: the message and that year's link, nothing else.
  panelStore.set(other.session);
  const a = walk(host).find((n) => n.tagName === 'A');
  assert.equal(a.href, other.session.link);
  assert.equal(a.textContent, 'Open the route in 1904');
  panel.destroy();
}
{
  // The builder: a jaunt's stops, a person found by name, a note and question, ONE link.
  const doc = makeDoc();
  const container = doc.createElement('div');
  const begun = [];
  const big = routeCatalog({ year: '1904', targets: [{ kind: 'structure', id: 'glessner_house', label: 'Glessner House' },
    { kind: 'anchor', id: 'haunted_battle_ground', label: 'The battle ground' }],
  people: [{ id: 'pa1904_glessner_john_jacob', name: 'John J. Glessner', occupation: 'manufacturer' }],
  jaunts: [{ id: 'walk-one', title: 'A Walk', availability: 'available', destinations: [{ kind: 'anchor', id: 'haunted_battle_ground' }, { kind: 'structure', id: 'glessner_house' }] }] });
  const win = { location: { href: HREF }, navigator: { clipboard: { writeText: async (s) => { win.copied = s; } } } };
  const b = mountRouteBuilder(container, { scene: { id: '1904' }, actions: { routeCatalog: async () => big, beginRoute: async (r) => { begun.push(r); return true; } } }, { win });
  assert(container.textContent.includes('Make a route for your class'));
  await byText(container, 'BUTTON', 'Build a route').click(); await settle();
  const select = walk(container).find((n) => n.tagName === 'SELECT');
  assert.deepEqual(select.children.map((o) => o.textContent), ['Choose a jaunt', 'A Walk']);
  select.value = 'walk-one'; await select.fire('change');
  await byText(container, 'BUTTON', 'Use this jaunt').click();
  assert.deepEqual(b.state.stops.map((s) => s.id), ['haunted_battle_ground', 'glessner_house'], 'the jaunt\'s stops, in its order');
  assert.equal(b.state.title, 'A Walk', 'an empty title takes the jaunt\'s');
  const find = walk(container).find((n) => n.id === 'route-find');
  find.value = 'glessner manu'; await find.fire('input');
  const add = walk(container).find((n) => n.getAttribute('aria-label') === 'Add John J. Glessner');
  assert(add, 'a person found by name and work');
  await add.click();
  assert.equal(b.state.stops.length, 3);
  const stops = byClass(container, 'route-stop');
  const fields = walk(stops[2]).filter((n) => n.tagName === 'TEXTAREA');
  fields[0].value = 'He built this house.'; await fields[0].fire('input');
  fields[1].value = 'What did he make?'; await fields[1].fire('input');
  await walk(stops[2]).find((n) => n.dataset.tool === 'up').click();
  assert.deepEqual(b.state.stops.map((s) => s.id), ['haunted_battle_ground', 'pa1904_glessner_john_jacob', 'glessner_house'], 'Move earlier');
  await byText(container, 'BUTTON', 'Make the share link').click();
  const out = walk(container).find((n) => n.id === 'route-link');
  const made = parseRouteLink(new URL(out.value).search).route;
  assert.deepEqual(made, normalRoute({ year: '1904', title: 'A Walk', jaunt: 'walk-one', stops: [
    { kind: 'spot', id: 'haunted_battle_ground' }, { kind: 'person', id: 'pa1904_glessner_john_jacob', note: 'He built this house.', question: 'What did he make?' },
    { kind: 'place', id: 'glessner_house' }] }), 'one link carries the whole route');
  await byText(container, 'BUTTON', 'Copy link').click();
  assert.equal(win.copied, out.value);
  await byText(container, 'BUTTON', 'Try it here').click();
  assert.deepEqual(begun, [made], 'Try it here opens the same route');
  // A route file opened again, here; one for another year is refused with its year named.
  const fileInput = walk(container).find((n) => n.id === 'route-file');
  fileInput.files = [{ size: 100, text: async () => routeFileText(normalRoute({ year: '1904', title: 'From file', stops: [{ kind: 'place', id: 'glessner_house' }, { kind: 'place', id: 'gone' }] })) }];
  await fileInput.fire('change');
  assert.equal(b.state.title, 'From file');
  assert.deepEqual(b.state.stops.map((s) => s.id), ['glessner_house']);
  assert(container.textContent.includes('1 of its stops are not in this town'), 'skipped stops are said');
  fileInput.files = [{ size: 100, text: async () => routeFileText(normalRoute({ year: '1835', title: 'Old', stops: [{ kind: 'place', id: 'a' }] })) }];
  await fileInput.fire('change');
  assert(container.textContent.includes('That route is for 1835.'));
  fileInput.files = [{ size: ROUTE_LIMITS.file + 1, text: async () => '' }];
  await fileInput.fire('change');
  assert(container.textContent.includes('not a route file'));
  // 1871 has no route: the builder says why instead of opening.
  const c2 = makeDoc().createElement('div');
  mountRouteBuilder(c2, { scene: { id: '1871' }, actions: { routeCatalog: async () => big } }, { win });
  await byText(c2, 'BUTTON', 'Build a route').click();
  assert(c2.textContent.includes('A route is built in the year you are in.'));
}

// ---- every key the screens read is in the string table ------------------------------- //
const view = fs.readFileSync(path.join(ROOT, 'renderers/web/js/teacher-route-view.js'), 'utf8');
const keys = new Set([...view.matchAll(/tr\('([a-zA-Z.]+)'/g)].map((m) => m[1]));
for (const k of ['up', 'down', 'remove', 'link', 'download', 'openFile', 'try']) keys.add(`build.${k}`);
for (const k of ['place', 'spot', 'person']) keys.add(`kind.${k}`);
for (const k of keys) assert(t(`route.${k}`), `route.${k} is in the string table`);
for (const k of ['route.arrived', 'route.arrivedSkipped', 'route.arrivedSkippedOne', 'route.otherYear', 'route.nothing', 'route.invalid', 'route.long', 'route.unread', 'route.atHouse']) assert(t(k), `${k} is in the string table`);
const main = fs.readFileSync(path.join(ROOT, 'renderers/web/js/main.js'), 'utf8');
assert.match(main, /const sharedRoute = sharedMoment \? null : parseRouteLink\(location\.search\)/, 'main.js reads the route link once');
assert.match(main, /if \(!sharedMoment && !sharedRoute && navLink/, 'a route link is not also read as a screen link');
assert.doesNotMatch(view, /innerHTML|insertAdjacentHTML|outerHTML/, 'the screens never write markup');

console.log('TEACHER ROUTE PASS — one link and one file carry the same bounded route; malformed, long, other-year and unknown stops degrade with a message; the teacher\'s words are text; answers go to the local notebook');
