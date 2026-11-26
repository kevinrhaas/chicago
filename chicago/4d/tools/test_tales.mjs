#!/usr/bin/env node
/**
 * T-3553 — "Tell me a story", for everyone in town, in every year.
 *
 *   - (that data/tales/<scene>.json re-derives is the gate's own step for tools/build_tales.py);
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
 *     card shows the story, greys Find for someone not out in town, and closes;
 *   - Ask a question (the owner, 2026-11-16): every question has one or two follow-ups and
 *     speaks no machine words and nothing past its year; everyone drawn is offered five (a
 *     toddler at least three), their own first; the five stay until all are answered, then five
 *     they have not answered; nobody asks you to find themselves; everyone has a persona whose
 *     temperaments are known and whose topics are real, and named people have their own;
 *     the persona leans which questions and stories come; Interact offers Ask a question after
 *     Tell me a story and its card lists, answers, reveals a follow-up and goes back.
 *
 *   node tools/test_tales.mjs
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const { pickTale, noteTold, readTeller, suits, createTales, personaOf, mannerOf, leaning } = await import('../renderers/web/js/tales.js');
const { withStory, storyAction, askAction, createTaleTeller } = await import('../renderers/web/js/tale-teller.js');
const { pickAsks, noteAsked } = await import('../renderers/web/js/asks.js');
const { createInteractions, actionStyle } = await import('../renderers/web/js/interact.js');

let checks = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); checks += 1; };

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
    const pool = lib.tales.filter((t) => t.roles.some((r) => who.roles.includes(r)) && suits(t, who));
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
  const pool = lib.tales.filter((t) => t.roles.some((r) => readTeller(lib.tellers[soldiers[0]]).roles.includes(r)) && suits(t, readTeller(lib.tellers[soldiers[0]])));
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
  const self = { tales: [{ id: 'me', roles: ['x'], title: 'M', text: ['m m m m m m m m m m m m m m m m m'], meet: { person: 'p', name: 'P' } },
    { id: 'b', roles: ['x'], title: 'B', text: ['b b b b b b b b b b b b b b b b b'] }], personal: {}, tellers: { p: 'x/m' } };
  ok([0, 0.6, 0.99].every((r) => pickTale(self, 'p', {}, { random: () => r }).tale.id === 'b'), 'nobody sends you to find themselves');
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
  ok(interactions.actionsOf(thing).map((a) => a.id).join() === 'greet,tale,ask', 'the engine offers it, and Ask a question, on a registered person');
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

  // Ask a question on the same person.
  ok(interactions.act(thing, 'ask').ok, 'Ask a question starts');
  interactions.update(1);
  await new Promise((r) => setTimeout(r, 10));
  const ac = teller.askCard;
  ok(ac.open && talking === true, 'the question card is open and she is talking');
  ok(ac.el.find('tale-who').textContent === 'Ask Frances Glessner Lee', 'it names her');
  ok(/Shrewd/.test(ac.el.find('ask-persona').textContent), `and says who she is (${ac.el.find('ask-persona').textContent})`);
  const qs = ac.el.find('ask-list').children;
  ok(qs.length === 5, 'five questions');
  ok(ac.showing.asks[0].id === libs['1904'].personal_asks.pa1904_lee_frances_glessner[0].id, 'her own first');
  qs[0].children[0].click();
  ok(ac.el.find('ask-you').textContent === ac.showing.ask.q && ac.el.find('ask-manner')?.textContent, 'a tap answers, in her manner');
  const follow = ac.el.find('ask-follow');
  ok(follow, 'with a follow-up to ask');
  follow.click();
  ok(ac.el.find('ask-reveal') && !ac.el.find('ask-more').children.includes(follow), 'which reveals more');
  ac.el.find('ask-back').click();
  ok(ac.el.find('ask-tick'), 'Other questions goes back, the answered one ticked');
  ok(teller.asks.state.by.pa1904_lee_frances_glessner.done[ac.showing.asks[0].id], 'and it is remembered');
  ac.el.find('tale-close').click();
  ok(!ac.open && talking === false, 'X closes it and she stops talking');
}

// ── Ask a question: the questions, the five, the personas ─────────────────────────────
{
  const person = { id: 'person:x', kind: 'person' };
  const greet = { id: 'greet', label: 'Greet', steps: [{ seconds: 1, run() {} }] };
  ok(withStory(person, [greet], () => {}, () => {}).map((a) => a.id).join() === 'greet,tale,ask', 'Ask a question follows Tell me a story');
  ok(!askAction({ kind: 'door' }, [greet], () => {}), 'only for a person');
  ok(actionStyle({ id: 'ask' }).icon === 'chat', 'with the talk icon');
}
for (const scene of SCENES) {
  const lib = libs[scene];
  const asks = [...lib.asks, ...Object.values(lib.personal_asks).flat()];
  ok(lib.asks.length >= 60, `${scene}: at least 60 questions by role (${lib.asks.length})`);
  const ids = new Set();
  for (const a of asks) {
    ok(!ids.has(a.id), `${scene}: ${a.id} is one question`);
    ids.add(a.id);
    ok(a.q && a.a.length && (a.more.length === 1 || a.more.length === 2) && a.more.every((m) => m.q && m.a.length), `${scene}: ${a.id} has an answer and one or two follow-ups`);
    const words = [a.q, ...a.a, ...a.more.flatMap((m) => [m.q, ...m.a])].join(' ');
    ok(!MACHINE.test(words), `${scene}: ${a.id} speaks no machine words (${words.match(MACHINE)?.[0]})`);
    for (const y of words.match(/\b1[6-9]\d\d\b/g) ?? []) ok(Number(y) <= Number(scene), `${scene}: ${a.id} names ${y}, after its year`);
    if (scene === '1812') ok(!GRAPHIC_1812.test(words), `1812: ${a.id} tells nothing graphically (${words.match(GRAPHIC_1812)?.[0]})`);
    if (a.meet) ok(a.meet.person in lib.tellers && a.meet.name, `${scene}: ${a.id} sends you to someone drawn`);
    ok(Array.isArray(a.k), `${scene}: ${a.id} knows its topics`);
  }
  // Never one answer twice in a scene: no two questions share a paragraph.
  const paras = new Set();
  for (const p of asks.flatMap((a) => [...a.a, ...a.more.flatMap((m) => m.a)])) { ok(!paras.has(p) || p.length < 25, `${scene}: an answer is told once (${p.slice(0, 40)})`); paras.add(p); }
  for (const pid of Object.keys(lib.personal_asks)) ok(pid in lib.tellers, `${scene}: ${pid}'s own questions belong to someone drawn`);
  // Everyone: five questions, a persona.
  const topicsOk = new Set(['trade', 'kin', 'home', 'faith', 'war', 'wild', 'work', 'fun', 'talk', 'past', 'dread']);
  let short = 0;
  for (const pid of Object.keys(lib.tellers)) {
    const state = {};
    const got = pickAsks(lib, pid, state, { random: seq(pid.length) });
    const toddler = readTeller(lib.tellers[pid]).roles.includes('toddler');
    if (got.asks.length < 5) short += 1;
    ok(got.asks.length >= (toddler ? 3 : 5), `${scene}: ${pid} is offered five questions (${got.asks.length})`);
    ok(new Set(got.asks.map((a) => a.id)).size === got.asks.length, `${scene}: ${pid}'s five are five`);
    ok(got.asks.every((a) => a.meet?.person !== pid), `${scene}: ${pid} never sends you to find themselves`);
    const p = personaOf(lib, pid);
    ok(p.tempers.length >= 1 && p.tempers.every((t) => lib.tempers[t]) && p.topics.length >= 2 && p.topics.every((t) => topicsOk.has(t)), `${scene}: ${pid} has a temperament and things to talk about`);
    const m = mannerOf(lib, p, `${pid}:x`);
    ok(m && !/[{}]/.test(m), `${scene}: ${pid} comes to an answer in their manner (${m})`);
  }
  ok(short <= 2, `${scene}: at most two little ones have fewer than five (${short})`);
  const named = Object.keys(lib.personal_asks);
  ok(named.filter((pid) => personaOf(lib, pid).who.length > 30).length >= named.length * 0.8, `${scene}: the named people have their own persona`);
  const whos = new Set(Object.keys(lib.tellers).map((pid) => lib.persona[pid]));
  ok(whos.size >= Object.keys(lib.tellers).length * 0.9, `${scene}: personas are nearly all different (${whos.size})`);
}
{
  // The five stay until answered, then five more never answered before.
  const lib = libs['1835'];
  const pid = Object.keys(lib.tellers).find((p) => readTeller(lib.tellers[p]).roles.join() === 'townsman,labourer');
  const state = {};
  const first = pickAsks(lib, pid, state, { random: seq(3) }).asks.map((a) => a.id);
  ok(pickAsks(lib, pid, state, { random: seq(9) }).asks.map((a) => a.id).join() === first.join(), 'the same five while any is unanswered');
  for (const id of first.slice(0, 4)) noteAsked(state, pid, id);
  ok(pickAsks(lib, pid, state, { random: seq(5) }).asks.map((a) => a.id).join() === first.join(), 'still the same five with one left');
  noteAsked(state, pid, first[4]);
  const next = pickAsks(lib, pid, state, { random: seq(7) }).asks.map((a) => a.id);
  ok(next.length === 5 && next.every((id) => !first.includes(id)), 'then five never answered before');
  // A second labourer is offered ones nobody has answered for you first.
  const other = Object.keys(lib.tellers).filter((p) => readTeller(lib.tellers[p]).roles.join() === 'townsman,labourer')[7];
  const theirs = pickAsks(lib, other, state, { random: seq(11) }).asks.map((a) => a.id);
  ok(theirs.filter((id) => first.includes(id)).length === 0, 'a second labourer is not offered what you already had answered');
  // The persona leans: over many people, what they are offered matches their topics more than chance.
  let lean = 0, base = 0;
  for (const p of Object.keys(lib.tellers).slice(0, 400)) {
    const persona = personaOf(lib, p);
    const got = pickAsks(lib, p, {}, { random: seq(p.length + 1) }).asks;
    lean += got.reduce((s, a) => s + leaning(a, persona), 0) / Math.max(1, got.length);
    const who = readTeller(lib.tellers[p]);
    const pool = lib.asks.filter((a) => a.roles.some((r) => who.roles.includes(r)) && suits(a, who));
    base += pool.reduce((s, a) => s + leaning(a, persona), 0) / Math.max(1, pool.length);
  }
  ok(lean > base * 1.1, `a person's temper and history lean what they are asked (${(lean / 400).toFixed(2)} vs ${(base / 400).toFixed(2)})`);
  // And what they tell.
  const soldiers = Object.keys(libs['1812'].tellers).filter((p) => readTeller(libs['1812'].tellers[p]).roles.join() === 'soldier');
  let tl = 0, tb = 0;
  for (const p of soldiers) {
    const persona = personaOf(libs['1812'], p);
    for (let i = 0; i < 6; i++) tl += leaning(pickTale(libs['1812'], p, { n: 0, told: {}, by: {} }, { random: seq(i * 31 + p.length) }).tale, persona);
    const pool = libs['1812'].tales.filter((t) => t.roles.includes('soldier') && suits(t, readTeller(libs['1812'].tellers[p])));
    tb += 6 * pool.reduce((s, t) => s + leaning(t, persona), 0) / pool.length;
  }
  ok(tl > tb * 1.1, `and which stories they tell (${tl} vs ${tb.toFixed(0)})`);
}

// ── Who may tell it (the owner, 2026-11-26) ──────────────────────────────────────────────
// "Louis Ream ... sounds like a young girl and recounts his World's Fair experience from a female
// perspective ... grade each story to age and gender and situation"; and an 1871 woman who shoved
// lumber. A story or question reaches only a teller of its sex, age and origin.
{
  const t = readTeller('maid,cook/f/c/a9/oirish');
  ok(t.roles.join() === 'maid,cook' && t.sex === 'f' && t.child && t.age === 9 && t.origin === 'irish', 'a teller row carries age and origin');
  const plain = readTeller('soldier/m');
  ok(plain.age === null && plain.origin === null && !plain.child, 'and a row without them reads as before');
  ok(!suits({ sex: 'f' }, plain) && suits({ sex: 'm' }, plain) && suits({}, plain), 'a story for one sex is told by that sex only');
  ok(!suits({ age: [40, null] }, readTeller('x/m/a17')) && suits({ age: [40, null] }, readTeller('x/m/a41')) && suits({ age: [40, null] }, plain),
    'a story for an age is told only at that age, and by a teller of no known age');
  ok(!suits({ origin: ['swedish'] }, readTeller('maid/f/oirish')) && suits({ origin: ['swedish'] }, readTeller('maid/f/oswedish')),
    'a story from somewhere is told by people from there');
  const SAYS_F = /\b(my husband|I was (a |only a )?(little |young )?girl|as a girl|I am (a |an )?(widow|old woman))\b/i;
  const SAYS_M = /\b(my wife|I was (a |only a )?(little |young )?(boy|lad)|as a boy|I was a young man)\b/i;
  const words = (x) => [x.title ?? x.q ?? '', ...(x.text ?? x.a ?? []), ...(x.more ?? []).flatMap((m) => [m.q, ...m.a])].join(' ');
  for (const scene of ['1812', '1835', '1871', '1904']) {
    const lib = scene in libs ? libs[scene] : JSON.parse(fs.readFileSync(`${ROOT}data/tales/${scene}.json`, 'utf8'));
    let wrong = [];
    for (const [pid, row] of Object.entries(lib.tellers)) {
      const who = readTeller(row);
      for (const x of [...lib.tales, ...lib.asks]) {
        if (!x.roles.some((r) => who.roles.includes(r)) || !suits(x, who)) continue;
        const w = words(x);
        if ((who.sex === 'm' && SAYS_F.test(w)) || (who.sex === 'f' && SAYS_M.test(w))) wrong.push(`${pid}:${x.id}`);
        if (who.child && /\bmy (husband|wife)\b/i.test(w)) wrong.push(`${pid}:${x.id} (a child)`);
      }
    }
    ok(!wrong.length, `${scene}: nobody tells a story as the other sex, nor a child as a wife (${wrong.slice(0, 6)})`);
  }
  const l04 = libs['1904'];
  const louis = 'pa1904_ream_norman_b_c1900_louis_m_ream';
  ok(louis in l04.tellers && readTeller(l04.tellers[louis]).sex === 'm', 'Louis Ream tells as a young man');
  const his = pickAsks(l04, louis, {}, { random: seq(4) }).asks;
  ok(his.length >= 5 && his.every((a) => !SAYS_F.test(words(a))), 'Louis Ream is never asked to remember the Fair as a girl');
  const fair = l04.asks.find((a) => a.id === 'a04-md-fair');
  ok(fair && suits(fair, readTeller(l04.tellers[louis])) && !SAYS_F.test(words(fair)), 'and the Fair question is his to answer, told plain');
  const l71 = JSON.parse(fs.readFileSync(`${ROOT}data/tales/1871.json`, 'utf8'));
  const lumber = l71.tales.find((x) => x.id === 's71-wm-lumber');
  const women = Object.values(l71.tellers).map(readTeller).filter((w) => w.sex === 'f');
  ok(lumber && women.length > 100 && women.every((w) => !suits(lumber, w)), '1871: no woman shoves lumber on the South Branch');
  const kil = l71.tales.find((x) => x.id === 's71-ir-kilgubbin');
  const notIrish = Object.values(l71.tellers).map(readTeller).filter((w) => !w.roles.includes('irish'));
  ok(kil && notIrish.every((w) => !kil.roles.some((r) => w.roles.includes(r))), '1871: only the Irish tell of Kilgubbin');
  const mourning = l04.tales.find((x) => x.id === 's04-ld-mourning');
  const wives = Object.values(l04.tellers).map(readTeller).filter((w) => w.roles.includes('wife'));
  ok(mourning && wives.length && wives.every((w) => !mourning.roles.some((r) => w.roles.includes(r))), '1904: a wife never tells of her husband dying');
}

console.log(`test_tales: ${checks} checks passed`);
