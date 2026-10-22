// The real horse adapter must not turn modern license metadata into an1835claim.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { standingHorseCard } from '../renderers/web/js/standing-horse-card.js';
import { cardOpening } from '../renderers/web/js/popup.js';
const read = name => JSON.parse(readFileSync(new URL('../'+name, import.meta.url), 'utf8'));
const row = read('data/transport/parked/standing-horses.json').scenes['1835'][0];
const spec = read('data/transport/parked/horse-sevket-sidecar.json');
const modern = read('data/sources/sevketkabatas_2021_horse_model.json');
assert.equal(spec.source.publication_date, modern.date);
const saved = JSON.stringify({ row, spec });
function check(record) {
  const s = record.sidecar;
  assert.equal(record.id, row.id);
  assert(!Object.hasOwn(s.attributes, 'model_credit'), 'modern credit is not a graded historical attribute');
  for (const attr of Object.values(s.attributes)) {
    assert(!(attr.sources ?? []).includes(modern.id), 'modern source is not a historical animal claim');
  }
  assert(s.citations.some(c => c.source_id === modern.id), 'retain exact modern source citation');
  for (const id of row.source_ids) assert(s.citations.some(c => c.source_id === id));
  const opening = cardOpening(s, { title: row.name });
  assert.equal(opening.composed, false, 'own account prevents It stood here fallback');
  assert(opening.lead.includes('reconstructed, unidentified horse'));
  assert(opening.lead.includes(spec.source.author));
  assert(opening.lead.includes(modern.date.slice(0, 4)));
  assert(opening.lead.includes('CC BY4.0'));
  assert(opening.lead.includes('modern asset credit is not evidence of a particular 1835 horse, breed or owner'));
  assert(s.research_note.includes(spec.source.credit), 'retain exact creator/license credit in research note');
  assert(s.research_note.includes(row.note), 'preserve historical context and existing reconstruction limits');
}
const actual = standingHorseCard(row, spec);check(actual);
check(standingHorseCard({ ...row, animation: { enabled: false } }, spec));
assert.equal(JSON.stringify({ row, spec }), saved, 'card composition does not mutate source data');
const legacy = structuredClone(actual);
legacy.sidecar.attributes.model_credit = { value: spec.source.credit, confidence: 'attested', sources: [modern.id] };
delete legacy.sidecar.change_note;
assert.throws(() => check(legacy), /not a graded historical attribute/);
const missingCitation = structuredClone(actual);
missingCitation.sidecar.citations = missingCitation.sidecar.citations.filter(c => c.source_id !== modern.id);
assert.throws(() => check(missingCitation), /retain exact modern source citation/);
console.log('STANDING HORSE CARD PASS — actual adapter/popup lead retain modern2021credit and citations without historical grading; observed legacy defect and missing-credit citation rejected');
