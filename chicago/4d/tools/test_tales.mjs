#!/usr/bin/env node
/**
 * T-3553 — "Tell me a story", for everyone in town, in every year.
 *
 *   - data/tales/<scene>.json is what tools/build_tales.py writes from
 *     docs/RESEARCH/tales-3553 (its --check);
 *   - every teller's roles have stories (a toddler at least a few, everyone else many), every
 *     role in the library has a teller, every own story belongs to someone drawn, and
 *     everyone a story sends you to find is someone drawn in that scene;
 *   - no story speaks past its scene's year, uses a word of the machine (json, null, T-1234),
 *     or, in 1812, tells a blow or a wound graphically; ids are unique;
 *   - the picker: a person's own stories first, at random; then forty soldiers tell forty
 *     different stories before any is heard twice; a person never repeats one until they
 *     have told you all theirs; a dated story waits for its dates; the memory survives a
 *     reload and a storage that throws;
 *   - Interact offers Tell me a story straight after Greet, only where Greet is, and the
 *     card shows the story, greys Find for someone not out in town, and closes.
 *
 *   node tools/test_tales.mjs
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const { pickTale, noteTold, readTeller, createTales } = await import('../renderers/web/js/tales.js');
const { withStory, storyAction, createTaleTeller } = await import('../renderers/web/js/tale-teller.js');
const { createInteractions, actionStyle } = await import('../renderers/web/js/interact.js');

let checks = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); checks += 1; };

// ── the files are what the builder writes ───────────────────────────────────────────
const built = spawnSync('python3', ['tools/build_tales.py', '--check'], { cwd: ROOT, encoding: 'utf8' });
ok(built.status === 0, `build_tales.py --check: ${built.stdout}${built.stderr}`);

const SCENES = ['1812', '1835', '1904'];
const libs = Object.fromEntries(SCENES.map((s) => [s, JSON.parse(fs.readFileSync(`${ROOT}data/tales/${s}.json`, 'utf8'))]));
const MACHINE = /\b(json|null|undefined|NaN|http|www\.|T-\d{3,}|L-[a-z]|sidecar|asset|reconstructed)\b/i;
const GRAPHIC_1812 = /\b(blood\w*|scalp\w*|tomahawk\w*|gore|corpses?|stabb?\w*|throat|severed|guts|bayonet\w*|brains?)\b/i;

for (const scene of SCENES) {
  const lib = libs[scene];
  const all = [...lib.tales, ...Object.values(lib.personal).flat()];
  ok(lib.scene === scene && lib.liberty === 'L-tales-3553', `${scene}: names its scene and liberty`);
  ok(lib.tales.length >= 100, `${scene}: a library of at least 100 stories (${lib.tales.length})`);
  const ids = new Set();
  for (const t of all) {
    ok(!ids.has(t.id), `${scene}: ${t.id} is one story`);
    ids.add(t.id);
    const words = [t.title, ...t.text].join(' ');
    ok(t.title && t.text.length >= 1 && t.text.every((p) => p.length > 20), `${scene}: ${t.id} has a title and a telling`);
    ok(!MACHINE.test(words), `${scene}: ${t.id} speaks no machine words (${words.match(MACHINE)?.[0]})`);
    for (const y of words.match(/\b1[6-9]\d\d\b/g) ?? []) ok(Number(y) <= Number(scene), `${scene}: ${t.id} names ${y}, after its year`);
    if (scene === '1812') ok(!GRAPHIC_1812.test(words), `1812: ${t.id} tells nothing graphically (${words.match(GRAPHIC_1812)?.[0]})`);
    if (t.meet) ok(t.meet.person in lib.tellers && t.meet.name, `${scene}: ${t.id} sends you to ${t.meet.person}, someone drawn in town`);
  }
  for (const pid of Object.keys(lib.personal)) ok(pid in lib.tellers, `${scene}: ${pid}'s own stories belong to someone drawn`);
  // Every teller has stories enough; every role is somebody's.
  const told = new Set();
  for (const [pid, row] of Object.entries(lib.tellers)) {
    const who = readTeller(row);
    const pool = lib.tales.filter((t) => t.roles.some((r) => who.roles.includes(r)) && (!t.sex || t.sex === who.sex));
    pool.forEach((t) => told.add(t.id));
    const need = who.roles.includes('toddler') ? 4 : 5;
    ok(pool.length >= need, `${scene}: ${pid} (${row}) has ${pool.length} stories, wants ${need}`);
  }
  // A role nobody drawn holds yet (1835's camp children) keeps its stories for when they are.
  const waiting = lib.tales.filter((t) => !told.has(t.id));
  ok(waiting.length <= lib.tales.length * 0.05, `${scene}: someone in town tells nearly every story (${waiting.map((t) => t.id)})`);
  if (waiting.length) console.log(`  ${scene}: ${waiting.length} stories wait for a teller: ${waiting.map((t) => t.id).join(', ')}`);
  ok(lib.fallback?.m && lib.fallback?.f, `${scene}: a figure the builder did not know still has stories`);
}

// ── the picker ────────────────────────────────────────────────────────────────────────
const seq = (seed = 1) => () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
{
  const lib = libs['1812'];
  const soldiers = Object.entries(lib.tellers).filter(([, r]) => readTeller(r).roles.includes('soldier') && !lib.personal[r]).map(([p]) => p)
    .filter((p) => !lib.personal[p]);
  ok(soldiers.length >= 40, `1812 has forty soldiers or more (${soldiers.length})`);
  const pool = lib.tales.filter((t) => t.roles.some((r) => readTeller(lib.tellers[soldiers[0]]).roles.includes(r)));
  const heard = {};
  const first = soldiers.slice(0, Math.min(soldiers.length, pool.length)).map((p) => {
    const got = pickTale(lib, p, heard, { random: seq(7) });
    noteTold(heard, p, got.tale.id);
    return got.tale.id;
  });
  ok(new Set(first).size === first.length, `${first.length} soldiers asked once tell ${first.length} different stories (${new Set(first).size})`);
  // One soldier asked again and again: nothing twice until all are told.
  const one = soldiers[0];
  const h2 = {};
  const mine = [];
  for (let i = 0; i < pool.length; i += 1) { const g = pickTale(lib, one, h2, { random: seq(3 + i) }); noteTold(h2, one, g.tale.id); mine.push(g.tale.id); }
  ok(new Set(mine).size === pool.length, `one soldier tells all ${pool.length} of his before any again`);
  const again = pickTale(lib, one, h2, { random: seq(5) });
  ok(again.tale.id === mine[0], 'then the one he told longest ago');
}
{
  // Own stories first, at random, then the library.
  const lib = libs['1835'];
  const pid = Object.keys(lib.personal).find((p) => lib.personal[p].length >= 2) ?? Object.keys(lib.personal)[0];
  const own = lib.personal[pid].map((t) => t.id);
  const heard = {};
  const got = [];
  for (let i = 0; i < own.length + 1; i += 1) { const g = pickTale(lib, pid, heard, { random: seq(11 + i) }); noteTold(heard, pid, g.tale.id); got.push(g); }
  ok(got.slice(0, own.length).every((g) => g.own) && new Set(got.slice(0, own.length).map((g) => g.tale.id)).size === own.length,
    `${pid} tells their own ${own.length} first`);
  ok(!got[own.length].own, 'and then one from the library');
}
{
  // A dated story waits for its dates while another is left.
  const lib = { tales: [{ id: 'a', roles: ['x'], title: 'A', text: ['a a a a a a a a a a a a a a a a a'], from: '1812-08-15' },
    { id: 'b', roles: ['x'], title: 'B', text: ['b b b b b b b b b b b b b b b b b'] }], personal: {}, tellers: { p: 'x/m' } };
  ok(pickTale(lib, 'p', {}, { date: '1812-08-14', random: () => 0 }).tale.id === 'b', 'a story from after the day waits');
  ok(pickTale(lib, 'p', {}, { date: '1812-08-16', random: () => 0 }).tale.id === 'a', 'and is told once its day has come');
  ok(pickTale({ ...lib, tellers: {}, fallback: { m: 'x', f: 'x' } }, 'nobody', {}, { random: () => 0.9 }).tale.id === 'b',
    'a figure with no row tells the town\'s stories');
}
{
  // The memory survives a reload, and a storage that throws costs nothing but memory.
  const store = new Map();
  const storage = { getItem: (k) => store.get(k) ?? null, setItem: (k, v) => store.set(k, v), removeItem: (k) => store.delete(k) };
  const fetchJson = async () => libs['1904'];
  const a = createTales({ scene: '1904', fetchJson, storage, random: seq(2) });
  const pid = 'glessner_john_j';
  const one = await a.tell(pid);
  const b = createTales({ scene: '1904', fetchJson, storage, random: seq(2) });
  const two = await b.tell(pid);
  ok(one.own && two.own && one.tale.id !== two.tale.id, 'Mr. Glessner does not tell the same story after a reload');
  const broken = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); }, removeItem() { throw new Error('denied'); } };
  const c = createTales({ scene: '1904', fetchJson, storage: broken });
  ok((await c.tell(pid))?.tale, 'a storage that throws still tells a story');
}

// ── Interact and the card ────────────────────────────────────────────────────────────
class Node {
  constructor(tag) { this.tagName = tag; this.children = []; this.hidden = false; this.attrs = {}; this.listeners = {}; this._text = ''; this.disabled = false; this.className = ''; this.title = ''; this.innerHTML = ''; }
  append(...n) { this.children.push(...n); }
  replaceChildren(...n) { this.children = n; }
  setAttribute(k, v) { this.attrs[k] = v; }
  addEventListener(k, fn) { (this.listeners[k] ??= []).push(fn); }
  click() { for (const fn of this.listeners.click ?? []) fn({}); }
  set textContent(v) { this._text = String(v); }
  get textContent() { return this._text + this.children.map((c) => c.textContent).join(''); }
  find(cls) { if (this.className.split(' ').includes(cls)) return this; for (const c of this.children) { const f = c.find?.(cls); if (f) return f; } return null; }
}
const doc = { body: new Node('body'), createElement: (t) => new Node(t), listeners: {}, addEventListener(k, fn) { (this.listeners[k] ??= []).push(fn); } };
{
  const greet = { id: 'greet', label: 'Greet', steps: [{ seconds: 1, run() {} }] };
  const goHome = { id: 'go_home', label: 'Go home', steps: [] };
  const person = { id: 'person:x', kind: 'person', states: ['out'], state: 'out' };
  const list = withStory(person, [greet, goHome], () => {});
  ok(list.map((a) => a.id).join() === 'greet,tale,go_home', 'Tell me a story comes straight after Greet');
  ok(!storyAction({ kind: 'door' }, [greet], () => {}) && !storyAction(person, [goHome], () => {}), 'and only where a person offers Greet');
  ok(actionStyle({ id: 'tale' }).icon === 'story', 'with the story icon');

  const interactions = createInteractions();
  let greeted = 0, talking = null, found = null;
  const actor = { personId: 'pa1904_lee_frances_glessner', actions: { setTalk(on) { talking = on; } } };
  interactions.add({ id: 'person:pa1904_lee_frances_glessner', kind: 'person', personId: actor.personId, actor, name: 'Frances Glessner Lee',
    states: ['out'], state: 'out', at: [0, 0], actions: { get out() { return [{ id: 'greet', label: 'Greet', steps: [{ seconds: 1, run(t) { if (t === 0) greeted += 1; } }] }]; } } });
  const teller = createTaleTeller({ interactions, scene: '1904', base: './', doc, fetchJson: async () => libs['1904'], storage: null,
    canFind: (id) => (id === 'pa1904_lee_blewett' ? 'Not out in town now' : true), find: (id) => { found = id; } });
  const thing = interactions.get('person:pa1904_lee_frances_glessner');
  ok(interactions.actionsOf(thing).map((a) => a.id).join() === 'greet,tale', 'the engine offers it on a registered person');
  ok(interactions.act(thing, 'tale').ok, 'and starts it');
  interactions.update(1);
  await new Promise((r) => setTimeout(r, 10));
  ok(greeted === 1, 'the teller greets you first');
  ok(teller.card.open && talking === true, 'the card is open and the teller is talking');
  const tale = teller.card.showing.tale;
  ok(libs['1904'].personal.pa1904_lee_frances_glessner.some((t) => t.id === tale.id), 'she tells one of her own');
  ok(teller.card.el.find('tale-who').textContent === 'Frances Glessner Lee tells you a story', 'the card names her');
  const findKey = teller.card.el.find('tale-find');
  if (tale.meet?.person === 'pa1904_lee_blewett') {
    ok(findKey.disabled && /Not out/.test(findKey.title), 'Find is greyed, and says why, for someone not out in town');
  } else ok(!findKey.hidden || !tale.meet, 'Find is offered for whom the story names');
  teller.card.el.find('tale-again').click();
  await new Promise((r) => setTimeout(r, 10));
  ok(teller.card.showing.tale.id !== tale.id, 'Another story is another story');
  teller.card.el.find('tale-close').click();
  ok(!teller.card.open && talking === false, 'X closes the card and the teller stops talking');
  void found;
}

console.log(`test_tales: ${checks} checks passed`);
