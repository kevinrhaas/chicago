#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { jauntInvestigation as gossipInvestigation, jauntInvestigation, CASES, createInvestigationDraft, investigationNote, saveInvestigation, CASE_LIMITS } from '../renderers/web/js/jaunt-investigation.js';
import { createFieldNotebook, NOTEBOOK_KEY, LIMITS } from '../renderers/web/js/field-notebook.js';
import { notebookHTML } from '../renderers/web/js/field-notebook-view.js';

const root = process.env.C4D_TEST_ROOT || path.resolve(new URL('..', import.meta.url).pathname);
const dir = path.join(root, 'data/sidecars/1835/jaunts');
const names = fs.readdirSync(dir).filter(name => /^gossip-or-notice(?:-.+)?\.json$/.test(name));
const session = jaunt => ({ session: 'one-outing', jaunt, phase: 'outcome',
  outcome: { completion_eligible: true }, visited: jaunt.stops.map(s => ({ id: s.id, committed: true })) });
const clone = value => structuredClone(value);
let model, complete; const bands = new Set();
assert.equal(names.length, 5, 'exercise every current Gossip telling');
for (const name of names) {
  const jaunt = JSON.parse(fs.readFileSync(path.join(dir, name)));
  complete = session(jaunt); model = gossipInvestigation(complete);
  assert(model, name); bands.add(model.band);
  assert.equal(model.readings.length, 2, 'two newspaper items, never three independent witnesses');
  assert.deepEqual(model.claims.map(c => c.id), ['land-sale', 'bank-branch', 'bank-springfield']);
  for (const claim of model.claims) {
    const authored = jaunt.evidence.find(c => c.id === claim.id);
    assert.equal(claim.text, authored.text, 'use current telling evidence, never categorical stop prose');
    assert.equal(claim.reasoning, authored.reasoning || '');
    assert.deepEqual(claim.sources.map(s => s.id), authored.sources);
    assert(claim.sources.every(s => s.title && s.url === ''), 'text-only sources have no invented links');
  }
  assert(model.claims[0].text.includes('Fi[v]e and […]red'));
  assert(!model.claims[0].text.includes('[Six Hund]red'));
  assert.equal(model.claims[2].confidence, 'inferred');
  assert.equal(model.readings[1].locator, model.claims[1].locator);
  assert(model.readings[1].locator.includes('108'), 'shared American item supplies the inference locator');
  for (const modify of [s => { s.phase = 'atStop'; }, s => { s.outcome.fallback = true; },
    s => { s.outcome.completion_eligible = false; }, s => { s.visited = []; },
    s => { s.visited.find(v => v.id === 'the-american').committed = false; },
    s => { s.jaunt.version_of = 'unrelated'; }, s => { s.jaunt.scene = '1904'; },
    s => { s.jaunt.citations = []; }, s => { s.jaunt.evidence.find(c => c.id === 'land-sale').sources.push('unresolved'); },
    s => { s.jaunt.evidence.find(c => c.id === 'bank-springfield').reasoning = ''; },
    s => { s.jaunt.evidence.find(c => c.id === 'bank-springfield').confidence = 'attested'; },
    s => { s.jaunt.stops.find(x => x.id === 'the-democrat').evidence = []; }]) {
    const bad = clone(complete); modify(bad); assert.equal(gossipInvestigation(bad), null);
  }
}
assert.deepEqual([...bands].sort(), ['11-12', '18+', '3-5', '6-8', '9-10']);
const draft = createInvestigationDraft(), fresh = createInvestigationDraft();
draft.claim = '<script>My reading</script>: the bank was proposed.';
draft.uncertainty = 'We do not know the exact sale total.'; draft.selected = ['land-sale', 'bank-branch'];
assert.equal(fresh.claim, ''); assert.equal(fresh.open, false); assert.equal(fresh.reviewed, false);
const prepared = investigationNote(model, draft);
assert(prepared.ok); assert(prepared.entry.text.includes(draft.claim));
assert(prepared.entry.text.includes('The land-sale estimate and its missing figure'));
assert(!prepared.entry.text.includes('The brick building read as Springfield’s'), 'only chosen readings appear as selected');
for (const claim of model.claims) {
  assert(prepared.entry.excerpt.includes(claim.text), 'retain complete context, including unselected inference');
  if (claim.reasoning) assert(prepared.entry.excerpt.includes(claim.reasoning));
}
assert.deepEqual(prepared.entry.sources.map(s => s.id), ['chicago_democrat_1833_1835', 'chicago_american_1835']);
assert(prepared.entry.excerpt.includes(model.readings[1].locator));
assert(prepared.entry.excerpt.includes('liberties'));
for (const [field, reason, value] of [['claim', 'claim', ' '], ['uncertainty', 'uncertainty', ''],
  ['selected', 'evidence', ['gossip']], ['claim', 'long', 'x'.repeat(CASE_LIMITS.claim + 1)]])
  assert.equal(investigationNote(model, { ...draft, [field]: value }).reason, reason);
assert.equal(investigationNote(null, draft).reason, 'unavailable');
const oversized = clone(model); oversized.claims[0].sources[0].title = 'x'.repeat(LIMITS.sourceTitle + 1);
assert.equal(investigationNote(oversized, draft).reason, 'unavailable', 'never silently truncate provenance');
const storage = () => { const data = new Map(); return { getItem: key => data.get(key) ?? null, setItem: (key, value) => data.set(key, value), data }; };
const store = storage(); let id = 0;
const book = createFieldNotebook({ storage: store, id: () => `case-${++id}` });
assert.equal(store.getItem(NOTEBOOK_KEY), null, 'reading, editing and reviewing have no storage side effect');
const saved = saveInvestigation(model, draft, book); assert(saved.ok);
assert.deepEqual(book.read().entries[0].sources, prepared.entry.sources);
assert.equal(book.read().entries[0].excerpt, prepared.entry.excerpt, 'bounded notebook retains exact source context');
assert.equal(saveInvestigation(model, draft, book).duplicate, true);
assert.equal(book.read().entries.length, 1, 'unchanged repeat click does not duplicate');
draft.claim += ' Revised.';
assert(saveInvestigation(model, draft, book).ok); assert.equal(book.read().entries.length, 2);
assert.equal(book.read().entries[0].text, saved.entry.text, 'explicit revised copy keeps earlier answer');
book.remove(draft.savedEntryId); assert(saveInvestigation(model, draft, book).ok, 'can save again after deleting the previous copy');
book.update(draft.savedEntryId, 'Edited separately in Notebook');
const restored = saveInvestigation(model, draft, book);
assert(restored.ok && !restored.duplicate, 'an edited Notebook entry is no longer the saved case version');
assert(restored.entry.text.includes(draft.claim));
const html = notebookHTML(book.read().entries);
assert.equal((html.match(/<h3>Source context<\/h3>/g) || []).length, book.read().entries.length,
  'each saved newspaper case labels its cited excerpt as source context');
assert(!html.includes('From the person’s card'), 'newspaper readings are not identified as a person card');
assert(html.includes('&lt;script&gt;My reading&lt;/script&gt;')); assert(!html.includes('<script>'));
for (const source of prepared.entry.sources) assert(html.includes(source.title.replaceAll('&', '&amp;')));
assert(html.includes('Fi[v]e and […]red')); assert(html.includes('Springfield'));
assert(!html.includes('href="http'), 'no fabricated source links in export');
const earlier = store.getItem(NOTEBOOK_KEY), unsaved = { ...draft, claim: 'Unsaved edit', selected: [...draft.selected] };
const failed = createFieldNotebook({ storage: { getItem: store.getItem, setItem() { throw Error('quota'); } } });
assert.equal(saveInvestigation(model, unsaved, failed).reason, 'storage');
assert.equal(store.getItem(NOTEBOOK_KEY), earlier); assert.equal(unsaved.claim, 'Unsaved edit');
assert.equal(saveInvestigation(model, unsaved, createFieldNotebook({ storage: null })).reason, 'storage');
const corrupt = storage(); corrupt.setItem(NOTEBOOK_KEY, '{"version":99,"entries":[]}');
assert.equal(saveInvestigation(model, unsaved, createFieldNotebook({ storage: corrupt })).reason, 'damaged');
assert.equal(corrupt.getItem(NOTEBOOK_KEY), '{"version":99,"entries":[]}');
const full = createFieldNotebook({ storage: storage(), id: () => `full-${++id}` });
for (let n = 0; n < LIMITS.entries; n++) assert(full.add({ kind: 'note', title: `Earlier ${n}` }).ok);
assert.equal(saveInvestigation(model, unsaved, full).reason, 'full'); assert.equal(full.read().entries.length, LIMITS.entries);

// T-3678: the case table. Every later case is built from its own telling's compiled,
// cited evidence, in every student band; the 18+ tellings are left out of these cases.
const STUDENT_BANDS = ['11-12', '3-5', '6-8', '9-10'];
assert.equal(new Set(CASES.map(c => c.id)).size, CASES.length, 'case ids are unique');
assert.equal(new Set(CASES.map(c => c.jaunt)).size, CASES.length, 'one case per jaunt');
assert(CASES.length >= 4 && new Set(CASES.filter(c => c.id !== 'gossip').map(c => c.year)).size >= 3,
  'at least three later cases, spread over the years');
const unrelated = JSON.parse(fs.readFileSync(path.join(root, 'data/sidecars/1812/jaunts/errands-before-the-march.json')));
assert.equal(jauntInvestigation(session(unrelated)), null, 'a jaunt with no case offers none');
const caseSummary = [];
for (const spec of CASES.filter(c => c.id !== 'gossip')) {
  const caseDir = path.join(root, `data/sidecars/${spec.year}/jaunts`);
  const tellings = fs.readdirSync(caseDir).filter(n => n.endsWith('.json')).map(n => [n, JSON.parse(fs.readFileSync(path.join(caseDir, n)))])
    .filter(([, j]) => (j.version_of || j.id) === spec.jaunt);
  assert(tellings.length >= 4, `${spec.id}: every telling of ${spec.jaunt}`);
  const caseBands = new Set(), questions = new Set();
  for (const [name, jaunt] of tellings) {
    const done = session(jaunt), got = jauntInvestigation(done);
    if (jaunt.audience === 'adults') { assert.equal(got, null, `${name}: 18+ tellings are out of scope`); continue; }
    assert(got, `${spec.id}: ${name} offers its case`);
    assert.equal(got.id, spec.id); assert.equal(got.year, spec.year); caseBands.add(got.band); questions.add(got.question);
    assert(got.question && got.intro && got.place && got.closing && got.readingNote);
    if (spec.year === '1812') assert(!/\b(blows?|shots?|shot|blood|bloody|scalp\w*|stab\w*|knife|killed|killing|tomahawk)\b/i.test(
      [got.question, got.intro, got.closing, ...got.claims.flatMap(c => [c.label, c.review])].join(' ')), `${name}: no graphic words of ours in an 1812 student case`);
    assert(got.readings.length >= 2, 'two or more readings to weigh');
    assert.deepEqual(got.claims.map(c => c.id), spec.readings.flatMap(r => r.claims.map(c => c.id)));
    for (const claim of got.claims) {
      const authored = jaunt.evidence.find(c => c.id === claim.id);
      assert.equal(claim.text, authored.text, 'the telling’s own evidence, verbatim');
      assert.equal(claim.confidence, authored.confidence, 'the grade is kept');
      assert.equal(claim.reasoning, authored.reasoning || ''); assert.equal(claim.locator, authored.locator || '');
      if (claim.confidence !== 'attested') assert(claim.reasoning, 'an inference keeps its reasoning');
      else assert(claim.locator, 'an attested reading keeps its locator');
      assert.deepEqual(claim.sources.map(s => s.id), authored.sources);
      assert(claim.sources.every(s => s.title && s.url === '' && fs.existsSync(path.join(root, 'data/sources', `${s.id}.json`))),
        'every source resolves to a record; no link is invented');
      assert(claim.label && claim.review && claim.grade.startsWith(claim.confidence[0].toUpperCase()));
    }
    // Each safeguard Gossip has refuses this case too, for every claim it names.
    const mods = [s => { s.phase = 'atStop'; }, s => { s.outcome.fallback = true; }, s => { s.outcome.completion_eligible = false; },
      s => { s.visited = []; }, s => { s.jaunt.version_of = 'unrelated'; s.jaunt.id = 'unrelated'; },
      s => { s.jaunt.scene = spec.year === '1904' ? '1835' : '1904'; }, s => { s.jaunt.citations = []; },
      s => { s.jaunt.grade_band = 'K-12'; s.jaunt.audience = 'adults'; }];
    for (const wanted of spec.readings.flatMap(r => r.claims)) {
      const ev = s => s.jaunt.evidence.find(c => c.id === wanted.id);
      mods.push(s => { s.visited.find(v => v.id === wanted.stop).committed = false; },
        s => { s.visited = s.visited.filter(v => v.id !== wanted.stop); },
        s => { s.jaunt.evidence = s.jaunt.evidence.filter(c => c.id !== wanted.id); },
        s => { s.jaunt.stops.find(x => x.id === wanted.stop).evidence = []; },
        s => { ev(s).sources.push('unresolved'); },
        s => { ev(s).sources = ev(s).sources.filter(id => id !== wanted.sources[0]); },
        s => { ev(s).confidence = wanted.confidence === 'attested' ? 'inferred' : 'attested'; },
        s => { ev(s).confidence = 'reconstructed'; },
        s => { if (wanted.confidence === 'attested') ev(s).locator = ''; else ev(s).reasoning = ''; },
        s => { ev(s).text = ''; });
    }
    for (const modify of mods) { const bad = clone(done); modify(bad); assert.equal(jauntInvestigation(bad), null, `${name}: refused`); }
    // Saved on the visitor's action, with every reading's text, locator, reasoning and source.
    const caseDraft = createInvestigationDraft();
    caseDraft.claim = `<b>${spec.id}</b> claim`; caseDraft.uncertainty = 'What the readings leave open.';
    caseDraft.selected = [got.claims.at(-1).id];
    const note = investigationNote(got, caseDraft); assert(note.ok, `${name}: note fits the notebook bounds`);
    for (const claim of got.claims) {
      assert(note.entry.excerpt.includes(claim.text)); assert(note.entry.excerpt.includes(`${claim.label} · ${claim.grade}`));
      if (claim.reasoning) assert(note.entry.excerpt.includes(claim.reasoning));
      if (claim.locator) assert(note.entry.excerpt.includes(claim.locator));
    }
    for (const r of got.readings) assert(note.entry.excerpt.includes(r.title));
    assert(note.entry.excerpt.includes(got.closing)); assert.equal(note.entry.place, got.place); assert.equal(note.entry.year, spec.year);
    assert(note.entry.text.includes(got.question) && note.entry.text.includes(got.claims.at(-1).label));
    assert(!note.entry.text.includes(got.claims[0].label), 'only chosen readings appear as selected');
    assert.deepEqual(note.entry.sources.map(s => s.id), [...new Set(got.claims.flatMap(c => c.sources.map(s => s.id)))]);
    const caseStore = storage(), caseBook = createFieldNotebook({ storage: caseStore, id: () => `${spec.id}-${++id}` });
    assert.equal(caseStore.getItem(NOTEBOOK_KEY), null, 'nothing is stored before Save');
    assert(saveInvestigation(got, caseDraft, caseBook).ok); assert.equal(saveInvestigation(got, caseDraft, caseBook).duplicate, true);
    const caseHtml = notebookHTML(caseBook.read().entries);
    assert(caseHtml.includes(`&lt;b&gt;${spec.id}&lt;/b&gt;`) && !caseHtml.includes(`<b>${spec.id}</b>`), 'student text is escaped');
    assert(!caseHtml.includes('href="http'), 'no invented source links');
  }
  assert.deepEqual([...caseBands].sort(), STUDENT_BANDS, `${spec.id}: every student band`);
  assert.equal(questions.size, STUDENT_BANDS.length, `${spec.id}: a question for each band`);
  caseSummary.push(`${spec.id} ${spec.year}`);
}
console.log(`GOSSIP INVESTIGATION PASS — five bands; eligible visited citations; missing figure and shared-item inference; explicit bounded saves, duplicates/failures, escaped full-context export; later cases ${caseSummary.join(', ')} in four student bands with every refusal`);
