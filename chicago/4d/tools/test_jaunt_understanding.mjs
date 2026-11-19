import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { CHECK_BANDS, checkBand, understandingQuestions, sourceURL, createUnderstandingDraft } from '../renderers/web/js/jaunt-understanding.js';

const root = process.env.C4D_TEST_ROOT || path.resolve(new URL('..', import.meta.url).pathname);
let count = 0;
const bands = new Set();
for (const year of ['1812', '1835', '1904']) {
  const dir = path.join(root, 'data/sidecars', year, 'jaunts');
  const catalog = JSON.parse(fs.readFileSync(path.join(dir, 'catalog.json')));
  for (const row of catalog.jaunts.filter(row => row.availability === 'available')) {
    const jaunt = JSON.parse(fs.readFileSync(path.join(dir, `${row.id}.json`)));
    const session = { jaunt, phase: 'outcome', visited: jaunt.stops.map(stop => ({ id: stop.id, committed: true })), outcome: { completion_eligible: true } };
    const qs = understandingQuestions(session);
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
for (const value of ['javascript:alert(1)', 'data:text/html,test', '/relative', null, '']) assert.equal(sourceURL(value), null);
assert.equal(sourceURL('https://example.org/a'), 'https://example.org/a');
const first = createUnderstandingDraft(), second = createUnderstandingDraft();
first.answers[0] = 'My reading'; assert.equal(second.answers[0], '');
assert.equal(checkBand({ grade_band: '6-8', audience: 'adults' }), '18+');
console.log(`JAUNT UNDERSTANDING PASS — ${count} catalog tellings, five bands, cited visited claims only, interrupted/uncited/reconstructed exclusions`);
