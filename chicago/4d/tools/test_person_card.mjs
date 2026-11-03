#!/usr/bin/env node
// A person's own card (T-3265), read off every 1904 household record without a browser.
//
// The owner, 2026-10-30: a tap on a person on a building's People tab should open "a detailed
// card on that person", telling "their interesting story" and "why some are attested and why
// some are inferred". So, for every person in the 1904 directory:
//   1. the card is theirs: name, grade and household from their own record and row;
//   2. it has something to say about them — a story, or the honest "no more yet" line;
//   3. How we know answers for the grade, and an inferred census servant's answer names the
//      1900 census and the four years between it and the scene;
//   4. every fact the card shows is a field of the record, with that field's grade, and the
//      birthplace and arrival it reads out of a note are words the note itself contains;
//   5. every source it lists is joined to a citation (sidecars/1904/residents_sources.json,
//      which compile_scene.py now joins for the scene's own households), never a bare id;
//   6. a census line's page link points at the leaf the record names;
//   7. Back names the household it returns to.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { personModel, censusLead, householdShort } from '../renderers/web/js/person-card.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const json = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const dir = json('data/sidecars/1904/people.json');
const citations = json('data/sidecars/1904/residents_sources.json').citations;
const failures = [];
const fail = (m) => { if (failures.length < 25) failures.push(m); else if (failures.length === 25) failures.push('…'); };

let cards = 0, inferredCensus = 0, leads = 0, links = 0;
for (const row of dir.people) {
  const hh = json(path.join(dir.residents_root, row.file));
  const person = hh.persons.find((p) => p.id === row.id);
  if (!person) { fail(`${row.id}: no person in ${row.file}`); continue; }
  const m = personModel({ row, person, household: hh, citations, sceneYear: 1904 });
  cards++;
  const who = `${row.name} (${row.id})`;
  if (m.name !== person.name || m.grade !== person.grade || m.household !== hh.name) fail(`${who}: card is not theirs`);
  if (!m.lead && !m.story.length && !m.printedAs && !m.census) fail(`${who}: nothing to say and no listing to show`);
  if (!m.why || m.why.grade !== person.grade || !m.why.text) fail(`${who}: How we know does not answer for ${person.grade}`);
  if (person.grade === 'inferred' && person.census_1900 && !(person.sources ?? []).some((s) => /blue_book/.test(s))) {
    inferredCensus++;
    if (!/1900 census/.test(m.why.text) || !/four years before/.test(m.why.text)) fail(`${who}: inferred census card does not say why`);
  }
  const note = [person.note, person.born?.note].filter(Boolean).join(' ');
  for (const f of m.facts) {
    if (!f.value) fail(`${who}: empty fact ${f.label}`);
    if (['Born in', 'Came to America'].includes(f.label) && !note.includes(f.value)) fail(`${who}: ${f.label} "${f.value}" is not in the note`);
    if (f.label === 'Work' && f.grade !== (person.occupation?.confidence ?? person.grade)) fail(`${who}: Work carries the wrong grade`);
  }
  if (m.lead) {
    leads++;
    if (!m.lead.includes(person.name)) fail(`${who}: the census lead does not name them`);
    if (/undefined|null|NaN/.test(m.lead)) fail(`${who}: lead says ${m.lead}`);
  }
  for (const s of m.sources) if (/not yet joined/.test(s.title)) fail(`${who}: source ${s.id} is not joined`);
  if (m.census?.link) {
    links++;
    const leaf = person.census_1900.locator.match(/leaf (n\d+)/)?.[1];
    if (!m.census.link.endsWith(`/page/${leaf}/mode/1up`)) fail(`${who}: census link ${m.census.link} is not leaf ${leaf}`);
  }
  if (m.back !== householdShort(hh.name) || / at \d/.test(m.back)) fail(`${who}: Back says "${m.back}"`);
  if (m.story.some((p) => /Servants changed places often/.test(p))) fail(`${who}: an evidence sentence stayed in the story`);
}

// The census lead, by hand, on the owner's example.
const billings = censusLead({ name: 'August Billings', work: 'Helper', householdName: 'The Glessner household at 1800 Prairie Avenue',
  line: 'Enumerated on 1 June 1900 in the rear building behind the house, as a helper; born January 1875, in Sweden, came to the United States in 1892, single.' });
const want = 'On 1 June 1900 the census taker found August Billings living in the rear building behind the house at 1800 Prairie Avenue, working as a helper. Born in Sweden in January 1875, August came to the United States in 1892, at about 17. Single at the time.';
if (billings !== want) fail(`census lead for August Billings:\n  got  ${billings}\n  want ${want}`);
// A row alone (the record not read yet) still draws a card that is theirs.
const row = dir.people.find((r) => r.id === 'glessner_john_j');
const early = personModel({ row, sceneYear: 1904 });
if (early.name !== 'John J. Glessner' || early.read || early.back !== 'The Glessner household') fail('the card from a row alone is not John J. Glessner\'s');

if (cards !== dir.people.length || inferredCensus < 150 || leads < 150 || links < 150) {
  fail(`too few read: ${cards} cards of ${dir.people.length}, ${inferredCensus} inferred census, ${leads} leads, ${links} page links`);
}
if (failures.length) {
  console.log(`FAIL person cards (T-3265):\n  ${failures.join('\n  ')}`);
  process.exit(1);
}
console.log(`ok person cards (T-3265): ${cards} people, ${inferredCensus} inferred from the 1900 census, ${leads} census leads, ${links} page links`);
