#!/usr/bin/env node
// T-1258: the Chicago daybook — idempotent awards, data-defined ranks, honest recovery.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createJaunts, choicesFor, replaySession } from '../renderers/web/js/jaunts.js';
import { createJournal, countsFor, rankFor, presentKeepsake, DAYBOOK_KEY } from '../renderers/web/js/jaunt-journal.js';

const read = rel => JSON.parse(fs.readFileSync(new URL(`../${rel}`, import.meta.url)));
const book = read('data/jaunts/daybook.json');
const fixture = id => read(`data/jaunts/_fixtures/fixture-${id}.json`);
let tests = 0;
async function test(name, fn) { await fn(); ++tests; console.log(`PASS ${name}`); }
function memory(initial = {}) {
  const data = new Map(Object.entries(initial));
  return { data, getItem: k => data.has(k) ? data.get(k) : null, setItem: (k, v) => data.set(k, String(v)), removeItem: k => data.delete(k) };
}
// Five tiny fixture jaunts per family are made from the walk fixture: same stops, its own
// id and keepsake, so the balanced-progression test plays real outings through the reducer.
const plain = fixture('walk');
const outing = (family, n) => ({ ...structuredClone(plain), id: `fixture-${book.families.find(f => f.name === family).id}-${n}`,
  keepsake: { family, id: `keepsake-${n}`, title: `${family} ${n}`, text: `A fictional ${family.toLowerCase()} memento.` } });
function rig(journal, docs) {
  let active;
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, go(target, hooks) { active = hooks; return true; },
    stop() { const old = active; active = null; old?.onStop({ ...old.token }); } };
  const controller = createJaunts({ load: async id => docs[id], resolve: x => x, place: () => true, enter: () => true, travel,
    render() {}, showMenu() {}, openDetail() {}, closeDetail() {}, onError: e => { throw e; }, storage: null,
    onComplete: state => journal.award(state.jaunt, state.outcome) });
  const arrive = () => active?.onArrive(active.token);
  async function play(id, { revise = false } = {}) {
    await controller.start(id);
    for (let guard = 0; controller.state.phase !== 'outcome' && guard < 40; guard++) {
      const s = controller.state;
      if (s.phase === 'travelling') { arrive(); continue; }
      const choice = choicesFor(s)[0];
      if (choice && !s.visited[s.stopIndex].committed) controller.choose(choice.id);
      controller.next();
      if (revise && s.stopIndex === 0 && controller.state.phase === 'travelling') {
        revise = false; arrive(); controller.prev(); arrive(); controller.revise();
      }
    }
    assert.equal(controller.state.phase, 'outcome', `${id} reached an ending`);
    return controller.state;
  }
  return { controller, play };
}

await test('a keepsake is awarded once across replay, Previous/Revise and duplicate completions', async () => {
  const storage = memory(), journal = createJournal({ book, storage });
  const shopping = fixture('branch'), walk = fixture('walk');
  const { play } = rig(journal, { [shopping.id]: shopping, [walk.id]: walk });
  const done = await play(shopping.id, { revise: true });
  assert(done.events.some(e => e.type === 'revise'), 'the path really revised a choice');
  assert.equal(journal.keepsakes.length, 1); assert.equal(journal.lastAward.added, true);
  await play(shopping.id); await play(shopping.id, { revise: true });
  assert.equal(journal.keepsakes.length, 1, 'replays keep one copy'); assert.equal(journal.lastAward.added, false);
  journal.award(done.jaunt, done.outcome); journal.award(done.jaunt, done.outcome);
  const saved = { content_version: done.jaunt.content_version, jaunt: done.jaunt.id, events: done.events };
  const restored = replaySession(done.jaunt, saved); journal.award(restored.jaunt, restored.outcome);
  assert.equal(journal.keepsakes.length, 1, 'a restored or duplicated completion event adds nothing');
  assert.equal(journal.award(walk, { fallback: true, completion_eligible: false }), null, 'a fallback ending awards nothing');
  assert.equal(journal.award(walk, { completion_eligible: false }), null, 'an ineligible ending awards nothing');
  assert.equal(JSON.parse(storage.getItem(DAYBOOK_KEY)).keepsakes.length, 1);
});

await test('ranks are exactly the data thresholds, and every family must meet them', async () => {
  const journal = createJournal({ book, storage: memory() }), docs = {};
  for (const family of book.families) for (const n of [1, 2, 3]) { const doc = outing(family.name, n); docs[doc.id] = doc; }
  const { play } = rig(journal, docs);
  assert.equal(journal.level().id, book.ranks[0].id);
  const order = [1, 2, 3].flatMap(n => book.families.map(f => `fixture-${f.id}-${n}`));
  const seen = [];
  for (const id of order) { await play(id); seen.push(journal.level().title); }
  assert.deepEqual(seen, [...Array(4).fill('New Arrival'), 'Finding Your Feet', ...Array(4).fill('Finding Your Feet'), 'Knows the Town',
    ...Array(4).fill('Knows the Town'), 'Seasoned Chicagoan']);
  assert.equal(journal.lastAward.rankChanged, true);
  // Three distinct keepsakes in four families and two in the fifth is NOT Seasoned.
  const short = journal.keepsakes.filter(e => e.key !== `fixture-${book.families[4].id}-3:keepsake-3`);
  assert.deepEqual(Object.values(countsFor(book, short)), [3, 3, 3, 3, 2]);
  assert.equal(rankFor(book, short).id, 'knows_the_town');
  // A secondary family counts once for that family as well.
  const both = { ...outing('Provisions', 9), secondary_family: 'Neighbors' }, j = createJournal({ book, storage: null });
  j.award(both); assert.deepEqual(j.counts(), { provisions: 1, livelihood: 0, wayfinding: 0, news: 0, neighbors: 1 });
});

await test('changing daybook.json thresholds re-ranks with no code change', () => {
  const keepsakes = book.families.map((f, i) => ({ key: `k${i}`, jaunt: `j${i}`, id: 'k', family: f.name, title: 't', text: 'x' }));
  assert.equal(rankFor(book, keepsakes).id, 'finding_your_feet');
  const steeper = structuredClone(book); steeper.ranks = steeper.ranks.map(r => ({ ...r, threshold: r.threshold * 2 }));
  assert.equal(rankFor(steeper, keepsakes).id, 'new_arrival');
  const gentler = structuredClone(book); gentler.ranks[2].threshold = 1; gentler.ranks[3].threshold = 2;
  assert.equal(rankFor({ ...gentler, ranks: gentler.ranks.slice(0, 1).concat(gentler.ranks.slice(2)) }, keepsakes).id, 'knows_the_town');
});

await test('corrupt, old and partly unreadable saves recover with an explanation, never silently', () => {
  const damaged = memory({ [DAYBOOK_KEY]: '{not json' }), a = createJournal({ book, storage: damaged });
  assert.equal(a.keepsakes.length, 0); assert.match(a.notice, /damaged/);
  assert.equal(damaged.getItem(`${DAYBOOK_KEY}.damaged`), '{not json', 'the damaged save is set aside, not destroyed');
  const old = memory({ [DAYBOOK_KEY]: JSON.stringify({ schema_version: 0, keepsakes: [] }) });
  assert.match(createJournal({ book, storage: old }).notice, /older version/);
  const good = { key: 'a:b', jaunt: 'a', id: 'b', family: 'Wayfinding', title: 'T', text: 'x' };
  const mixed = memory({ [DAYBOOK_KEY]: JSON.stringify({ schema_version: 1, content_version: 0,
    keepsakes: [good, good, { key: 'c:d', family: 'Gone', jaunt: 'c', id: 'd', title: 'T', text: 'x' }, null] }) });
  const c = createJournal({ book, storage: mixed });
  assert.equal(c.keepsakes.length, 1); assert.match(c.notice, /3 saved keepsakes could not be read/);
  assert.equal(JSON.parse(mixed.getItem(DAYBOOK_KEY)).content_version, book.content_version, 'migrated forward');
});

await test('storage off works in memory, says so, and reset clears', () => {
  const throwing = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); }, removeItem() {} };
  for (const storage of [null, throwing]) {
    const j = createJournal({ book, storage });
    assert.equal(j.persistent, false); assert.match(j.notice, /this visit only/);
    j.award(outing('Neighbors', 1)); assert.equal(j.keepsakes.length, 1);
  }
  const full = { ...memory(), setItem() { throw new Error('quota'); } }, q = createJournal({ book, storage: full });
  q.award(outing('Neighbors', 1)); assert.equal(q.keepsakes.length, 1); assert.equal(q.persistent, false);
  const storage = memory(), j = createJournal({ book, storage });
  j.award(outing('Livelihood', 1)); assert.ok(storage.getItem(DAYBOOK_KEY));
  j.reset(); assert.equal(j.keepsakes.length, 0); assert.equal(storage.getItem(DAYBOOK_KEY), null);
  assert.equal(createJournal({ book, storage }).keepsakes.length, 0);
  assert.equal(createJournal({ book, scene: '1904', storage }).key, `${DAYBOOK_KEY}.1904`, 'years keep separate books');
});

await test('no keepsake carries or renders a source attribution', () => {
  const dirs = ['data/jaunts', 'data/jaunts/_fixtures'];
  const docs = dirs.flatMap(d => fs.readdirSync(new URL(`../${d}`, import.meta.url)).filter(n => n.endsWith('.json') && !['schema.json', 'daybook.json', 'catalog-55.json'].includes(n))
    .map(n => read(`${d}/${n}`)));
  assert(docs.length >= 6);
  const claim = /\b(source|sources|cited|citation|according to|attested|documented)\b|\[(DOC|INF|CONJ)\]/i;
  for (const doc of docs) {
    assert.deepEqual(Object.keys(doc.keepsake).sort(), ['family', 'id', 'text', 'title'], `${doc.id}: keepsake fields`);
    assert(!claim.test(`${doc.keepsake.title} ${doc.keepsake.text}`), `${doc.id}: keepsake reads as evidence`);
    const shown = presentKeepsake(book, { key: 'k', jaunt: doc.id, ...doc.keepsake });
    assert(!Object.keys(shown).some(k => /source|citation|evidence/.test(k)), `${doc.id}: rendered keepsake names a source`);
  }
  assert.match(book.disclaimer, /not evidence/);
  for (const f of book.families) assert(!claim.test(`${f.description} ${f.template.lead}`), `${f.id}: template reads as evidence`);
});

await test('the published daybook is the authored one', () => {
  for (const scene of ['1835', '1904']) assert.deepEqual(read(`data/sidecars/${scene}/jaunts/daybook.json`), book);
});
console.log(`DAYBOOK PASS — ${tests} tests`);
