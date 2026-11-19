import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { CHECK_BANDS, checkBand, understandingQuestions, sourceURL, createUnderstandingDraft, answerQuestion, shortCitation, KINDS, heardLine, HEARD_MIN_SHARED } from '../renderers/web/js/jaunt-understanding.js';

const root = process.env.C4D_TEST_ROOT || path.resolve(new URL('..', import.meta.url).pathname);
let count = 0, heardCount = 0; const silent = [];
const bands = new Set(), kinds = { where: 0, who: 0, sure: 0 };
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
    // No question rather than one about a record the walk never said (owner, 19 November).
    if (!qs.length) { silent.push(row.id); continue; }
    assert.equal(qs.length, 3, `${row.id}: three cited questions`);
    assert.equal(new Set(qs.map(q => q.id)).size, 3);
    bands.add(qs[0].band);
    for (const q of qs) {
      assert(q.prompt.length > 12);
      assert.equal(q.band, checkBand(jaunt));
      const source = jaunt.evidence.find(claim => claim.id === q.claim.id);
      assert.equal(q.claim.text, source.text, 'claim text is never synthesized');
      assert.deepEqual(q.sources.map(source => source.id), source.sources);
      const stopOf = jaunt.stops.find(stop => stop.id === q.stop);
      assert(stopOf.evidence.includes(q.claim.id));
      // Owner, 19 November: a question is about something the walk actually said. The
      // quoted line is the stop's own words, and the record shares real words with it.
      const spoken = `${stopOf.text ?? ''} ${stopOf.stage?.caption ?? ''}`;
      assert(q.heard && spoken.includes(q.heard), `${row.id}: the quoted line is said at ${q.stop}`);
      const lower = x => new Set((String(x).toLowerCase().replace(/[’‘]/g, "'").match(/[a-z0-9]+/g) ?? []).map(w => w.length > 4 ? w.replace(/(ings|ing|ed|es|s)$/, '') : w));
      const recordWords = lower(q.claim.text);
      assert([...lower(q.heard)].filter(w => recordWords.has(w)).length >= HEARD_MIN_SHARED, `${row.id}: ${q.claim.id} is what ${q.stop} said`);
      heardCount++;
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
      } else if (ask.kind === 'who') {
        // The one host of the stop that told it, by its own card link; no other teller of it.
        const stop = jaunt.stops.find(st => st.id === q.stop);
        const host = stop.hosts?.length === 1 ? stop.hosts[0].person : null;
        assert(host && answer === stop.links.find(l => l.kind === 'person' && l.id === host).label, `${row.id}: the stop's own host`);
        assert(!q.heard.includes(answer) && !new RegExp(`\\b${answer.split(' ')[0]}\\b`).test(q.heard), `${row.id}: the quoted line does not name who told it`);
        const tellers = new Set(jaunt.stops.filter(st => st.evidence?.includes(q.claim.id) && st.hosts?.length === 1)
          .map(st => st.links?.find(l => l.kind === 'person' && l.id === st.hosts[0].person)?.label));
        for (const o of ask.options.filter(o => o.id !== ask.answer)) {
          assert(!tellers.has(o.label), `${row.id}: a wrong person never also told the claim`);
          assert(jaunt.stops.some(st => st.links?.some(l => l.kind === 'person' && l.label === o.label)), 'a real host of this jaunt');
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
assert.equal(heardCount, count * 3, 'every question quotes a line its stop said');
assert(silent.length <= 4, `few tellings too loosely retold to quiz: ${silent}`);
// The 19 November case: a record behind the scene that the stop never says is not quizzed.
const talk = { text: "From up the street the Field house looks like any other on the row. It is not. Field never liked making speeches." };
assert.equal(heardLine(talk, "The marriage licence acquired in London in 1905 gave Delia as 46 and Field as 70. They married at St. Margaret's, Westminster."), null);
assert.equal(heardLine({ text: 'Good morning. I came to Chicago from Springfield, Ohio, in 1870, a few weeks married. Mr. Richardson designed this house.' },
  'In 1870 John J. Glessner moved from Springfield, Ohio, to Chicago, bringing his wife Frances, whom he had just married.'),
  'I came to Chicago from Springfield, Ohio, in 1870, a few weeks married.');
assert.deepEqual([...bands].sort(), [...CHECK_BANDS].sort());
assert.deepEqual(KINDS, ['where', 'who', 'sure']);
assert(kinds.where + kinds.who >= count, `most tellings ask a place or person question as well as a grade: ${JSON.stringify(kinds)}`);
assert(!Object.keys(kinds).includes('source'), 'no citation-recall question (owner, 19 November)');
assert.equal(shortCitation("A. Author, 'Title', 2017. Read 5 November 2026."), "A. Author, 'Title', 2017.");
for (const value of ['javascript:alert(1)', 'data:text/html,test', '/relative', null, '']) assert.equal(sourceURL(value), null);
assert.equal(sourceURL('https://example.org/a'), 'https://example.org/a');
const first = createUnderstandingDraft(), second = createUnderstandingDraft();
first.answers[0] = 'My reading'; assert.equal(second.answers[0], '');
assert.equal(checkBand({ grade_band: '6-8', audience: 'adults' }), '18+');
console.log(`JAUNT UNDERSTANDING PASS — ${count} catalog tellings quizzed (${silent.length} with no line close enough to a record: ${silent.join(', ')}), five bands, guide questions ${JSON.stringify(kinds)} with one settled answer and retry, cited visited claims only, every one a line the stop said, interrupted/uncited/reconstructed exclusions`);
