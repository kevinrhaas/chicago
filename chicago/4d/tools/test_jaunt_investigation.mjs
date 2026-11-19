#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { gossipInvestigation, jauntInvestigation, createInvestigationDraft, investigationNote, saveInvestigation, CASE_LIMITS } from '../renderers/web/js/jaunt-investigation.js';
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
const oversized = clone(model); oversized.claims[0].sources[0].title = 'x'.repeat(501);
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
// T-3693: Who Started the Fire? ends on the same case, four sworn or reported accounts
// from the telling's own claims, each on the stop that cites it.
const fireDir = path.join(root, 'data/sidecars/1871/jaunts');
const fireNames = fs.readdirSync(fireDir).filter(name => /^who-started-the-fire(?:-.+)?\.json$/.test(name));
const FIRE = ['oleary-testimony', 'sullivan-affidavit', 'board-finding', 'peg-leg'];
const fireBands = new Set(); let fireModel;
assert.equal(fireNames.length, 5, 'exercise every Who Started the Fire? telling');
for (const name of fireNames) {
  const jaunt = JSON.parse(fs.readFileSync(path.join(fireDir, name)));
  const done = session(jaunt); fireModel = jauntInvestigation(done);
  assert(fireModel, name); fireBands.add(fireModel.band);
  assert.equal(gossipInvestigation(done), null, 'the Gossip name offers only the Gossip case');
  assert.equal(fireModel.year, '1871');
  assert.deepEqual(fireModel.claims.map(c => c.id), FIRE);
  assert.equal(fireModel.readings.length, 4, 'one reading per account');
  for (const claim of fireModel.claims) {
    const authored = jaunt.evidence.find(c => c.id === claim.id);
    assert.equal(claim.text, authored.text); assert.equal(claim.confidence, 'attested');
    assert.deepEqual(claim.sources.map(s => s.id), authored.sources);
    assert(claim.locator && claim.sources.every(s => s.title && s.url === ''));
  }
  assert(fireModel.question && !fireModel.question.includes('bank'), 'the fire case asks its own question');
  for (const modify of [s => { s.visited = s.visited.filter(v => v.id !== 'the-inquiry'); },
    s => { s.jaunt.scene = '1835'; }, s => { s.jaunt.evidence.find(c => c.id === 'peg-leg').confidence = 'inferred'; },
    s => { s.jaunt.stops.find(x => x.id === 'catherine').evidence = []; },
    s => { s.jaunt.evidence.find(c => c.id === 'sullivan-affidavit').locator = ''; },
    s => { s.jaunt.version_of = 'constructor'; s.jaunt.id = 'constructor'; }]) {
    const bad = clone(done); modify(bad); assert.equal(jauntInvestigation(bad), null);
  }
}
assert.deepEqual([...fireBands].sort(), ['11-12', '18+', '3-5', '6-8', '9-10']);
const fireDraft = { ...createInvestigationDraft(), claim: 'The Board could not say.', uncertainty: 'Nobody saw it start.', selected: ['board-finding'] };
const fireNote = investigationNote(fireModel, fireDraft);
assert(fireNote.ok); assert(fireNote.entry.place.includes('DeKoven'));
assert(fireNote.entry.excerpt.includes('Our reading of the cited source') && !fireNote.entry.excerpt.includes('newspaper transcription'));
assert(!fireNote.entry.excerpt.includes('million-dollar'), 'the fire case carries its own liberties, not Gossip’s');
assert(fireNote.entry.excerpt.includes('Attested: the source records this') && !fireNote.entry.excerpt.includes('the paper reports'), 'testimony is not called a newspaper report');
for (const claim of fireModel.claims) assert(fireNote.entry.excerpt.includes(claim.text));
console.log('GOSSIP INVESTIGATION PASS — Gossip and the Great Fire case; five bands each; eligible visited citations; missing figure and shared-item inference; explicit bounded saves, duplicates/failures, escaped full-context export');
