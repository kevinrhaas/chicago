import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { CHECK_BANDS, checkBand, understandingQuestions, sourceURL, createUnderstandingDraft, answerQuestion, shortCitation, KINDS } from '../renderers/web/js/jaunt-understanding.js';

const root = process.env.C4D_TEST_ROOT || path.resolve(new URL('..', import.meta.url).pathname);
let count = 0;
const bands = new Set(), kinds = { where: 0, sure: 0, source: 0 };
for (const year of ['1812', '1835', '1904']) {
  const dir = path.join(root, 'data/sidecars', year, 'jaunts');
  const catalog = JSON.parse(fs.readFileSync(path.join(dir, 'catalog.json')));
  // Name stops roughly as the page's destinations do: a viewpoint's short name, a
  // structure's own name (the page's display name may tidy it; distinctness is what counts).
  const anchors = new Map((JSON.parse(fs.readFileSync(path.join(root, 'data/scenes', `${year}.json`))).anchors ?? []).map(a => [a.id, a.short || a.label || a.id]));
  const names = new Map();
  const placeOf = stop => {
    const { kind, id } = stop.destination ?? {};
    if (kind === 'anchor') return anchors.get(id) ?? '';
    if (!names.has(id)) {
      try { names.set(id, JSON.parse(fs.readFileSync(path.join(root, 'data/sidecars', year, `${id}.json`))).name ?? ''); }
      catch { names.set(id, ''); }
    }
    return names.get(id);
  };
  for (const row of catalog.jaunts.filter(row => row.availability === 'available')) {
    const jaunt = JSON.parse(fs.readFileSync(path.join(dir, `${row.id}.json`)));
    const session = { jaunt, phase: 'outcome', visited: jaunt.stops.map(stop => ({ id: stop.id, committed: true })), outcome: { completion_eligible: true } };
    const qs = understandingQuestions(session, { placeOf });
    assert.equal(qs.length, 3, `${row.id}: three cited questions`);
    assert.equal(new Set(qs.map(q => q.id)).size, 3);
    bands.add(qs[0].band);
    for (const q of qs) {
      assert(q.prompt.length > 12);
      assert.equal(q.band, checkBand(jaunt));
      const source = jaunt.evidence.find(claim => claim.id === q.claim.id);
      assert.equal(q.claim.text, source.text, 'claim text is never synthesized');
      assert.deepEqual(q.sources.map(source => source.id), source.sources);
      assert(jaunt.stops.find(stop => stop.id === q.stop).evidence.includes(q.claim.id));
      assert(q.sources.every(source => source.citation));
      // T-3670: one answer the jaunt settles; every option is a real thing from this jaunt.
      const ask = q.ask; kinds[ask.kind]++;
      assert(ask.stem.length > 12 && !ask.stem.startsWith('understanding.'), `${row.id}: ${ask.kind} stem for ${q.band}`);
      assert.equal(new Set(ask.options.map(o => o.label)).size, ask.options.length, 'no repeated option');
      assert.equal(ask.options.filter(o => o.id === ask.answer).length, 1, 'exactly one answer');
      const answer = ask.options.find(o => o.id === ask.answer).label;
      if (ask.kind === 'where') {
        const nm = st => jaunt.places?.[st.destination?.id] || placeOf(st);
        const toldAt = new Set(jaunt.stops.filter(st => st.evidence?.includes(q.claim.id)).map(nm));
        assert.equal(answer, q.place); assert(toldAt.has(answer));
        for (const o of ask.options.filter(o => o.id !== ask.answer)) {
          assert(!toldAt.has(o.label), `${row.id}: a wrong place never also tells the claim`);
          assert(jaunt.stops.some(st => nm(st) === o.label), 'a real stop of this jaunt');
        }
      } else if (ask.kind === 'source') {
        assert.equal(answer, shortCitation(q.sources[0].citation));
        const mine = new Set(q.sources.map(s => shortCitation(s.citation)));
        for (const o of ask.options.filter(o => o.id !== ask.answer)) {
          assert(!mine.has(o.label), 'a wrong source is not one this claim cites');
          assert(jaunt.citations.some(c => shortCitation(c.citation) === o.label), 'a real citation of this jaunt');
        }
      } else {
        assert.equal(ask.answer, q.claim.confidence);
        assert.deepEqual(ask.options.map(o => o.id), ['attested', 'inferred', 'reconstructed']);
      }
      // Stable: a repaint asks the same question with the same order.
      assert.deepEqual(understandingQuestions(session, { placeOf })[q.number - 1].ask, ask);
    }
    if (count === 0) {
      const draft = createUnderstandingDraft(); const q = qs[1];
      const wrong = q.ask.options.find(o => o.id !== q.ask.answer).id;
      assert.deepEqual(answerQuestion(q, draft, 1, wrong), { right: false, tries: 1 });
      assert.deepEqual(answerQuestion(q, draft, 1, 'not-an-option'), { right: false, tries: 1 }, 'a stray value is not a try');
      assert.deepEqual(answerQuestion(q, draft, 1, q.ask.answer), { right: true, tries: 2 }, 'retry allowed');
      assert.deepEqual(answerQuestion(q, draft, 1, wrong), { right: true, tries: 2 }, 'solved stays solved');
      assert.deepEqual(draft.solved, [false, true, false]);
    }
    assert.deepEqual(understandingQuestions({ ...session, phase: 'atStop' }), []);
    assert.deepEqual(understandingQuestions({ ...session, outcome: { fallback: true } }), []);
    assert.deepEqual(understandingQuestions({ ...session, visited: [] }), []);
    assert.deepEqual(understandingQuestions({ ...session, visited: [{ id: jaunt.stops[0].id }] }), [], 'uncommitted stop not tested');
    const only = { ...session, visited: [{ id: qs[0].stop, committed: true }] };
    assert(understandingQuestions(only).every(q => q.stop === qs[0].stop), 'no unvisited route branch');
    const missing = { ...session, jaunt: { ...jaunt, citations: [] } };
    assert.deepEqual(understandingQuestions(missing), [], 'no fabricated citation fallback');
    const invented = { ...session, jaunt: { ...jaunt, evidence: jaunt.evidence.map(c => ({ ...c, confidence: 'reconstructed' })) } };
    assert.deepEqual(understandingQuestions(invented), [], 'invented narrative not treated as fact');
    count++;
  }
}
assert.deepEqual([...bands].sort(), [...CHECK_BANDS].sort());
assert.deepEqual(KINDS, ['where', 'sure', 'source']);
assert(kinds.where > count / 2 && kinds.source > count / 2, `most tellings ask all three kinds: ${JSON.stringify(kinds)}`);
assert.equal(shortCitation("A. Author, 'Title', 2017. Read 5 November 2026."), "A. Author, 'Title', 2017.");
for (const value of ['javascript:alert(1)', 'data:text/html,test', '/relative', null, '']) assert.equal(sourceURL(value), null);
assert.equal(sourceURL('https://example.org/a'), 'https://example.org/a');
const first = createUnderstandingDraft(), second = createUnderstandingDraft();
first.answers[0] = 'My reading'; assert.equal(second.answers[0], '');
assert.equal(checkBand({ grade_band: '6-8', audience: 'adults' }), '18+');
console.log(`JAUNT UNDERSTANDING PASS — ${count} catalog tellings, five bands, guide questions ${JSON.stringify(kinds)} with one settled answer and retry, cited visited claims only, interrupted/uncited/reconstructed exclusions`);
