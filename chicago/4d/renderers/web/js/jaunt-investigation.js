/** Make your case, attached to an eligible completed jaunt that has a row in the case
 * table. It reads the current telling's cited claims; it creates no historical facts or
 * persistent draft. */
import { checkBand } from './jaunt-understanding.js';
import { t } from './strings/index.js';
import './strings/investigation.js';
import { CASES } from './jaunt-investigation-cases.js';
import { LIMITS } from './field-notebook.js';

export { CASES };
export const CASE_LIMITS = Object.freeze({ claim: 2400, uncertainty: 1200 });

/** The case model for a completed session, or null. Every named claim must still be in
 * this telling, on a stop the visitor reached and committed, with its grade, its named
 * sources resolved to citations, a locator if it is attested and reasoning if it is not.
 * Any miss refuses the whole case rather than showing part of an argument. */
export function jauntInvestigation(session) {
  const jaunt = session?.jaunt;
  if (!jaunt || session.phase !== 'outcome' || session.outcome?.fallback || !session.outcome?.completion_eligible) return null;
  const spec = CASES.find(c => c.jaunt === (jaunt.version_of || jaunt.id));
  if (!spec || String(jaunt.scene) !== spec.year || (jaunt.audience === 'adults' && !spec.adults)) return null;
  const own = key => t(`investigation.${spec.id}.${key}`);
  const word = key => own(key) || t(`investigation.${key}`);
  const band = checkBand(jaunt), question = own(`question.${band}`);
  if (!question) return null;
  const visited = new Set((session.visited ?? []).filter(v => v.committed).map(v => v.id));
  const claims = [], readings = [];
  for (const wantedReading of spec.readings) {
    const title = own(`reading.${wantedReading.id}`);
    if (!title) return null;
    const found = [];
    for (const wanted of wantedReading.claims) {
      const stop = jaunt.stops?.find(s => s.id === wanted.stop);
      const claim = jaunt.evidence?.find(c => c.id === wanted.id);
      if (!visited.has(wanted.stop) || !stop?.evidence?.includes(wanted.id) || !claim?.text
        || claim.confidence !== wanted.confidence || !wanted.sources.every(id => claim.sources?.includes(id))) return null;
      const sources = claim.sources.map(id => jaunt.citations?.find(c => c.source_id === id));
      if (sources.some(s => !s?.citation)) return null;
      if (claim.confidence === 'attested' ? !claim.locator : !claim.reasoning) return null;
      const label = own(`evidence.${claim.id}`), review = own(`review.${claim.id}`), grade = word(`grade.${claim.confidence}`);
      if (!label || !review || !grade) return null;
      found.push({ id: claim.id, text: claim.text, confidence: claim.confidence,
        locator: claim.locator || '', reasoning: claim.reasoning || '', label, grade, review,
        sources: sources.map(s => ({ id: s.source_id, title: s.citation, url: '' })) });
    }
    // A reading may carry one claim's locator for all of it: the Gossip American item's
    // Springfield reading is a reading of the SAME item, not another witness.
    const locator = wantedReading.locator ? found.find(c => c.id === wantedReading.locator)?.locator : '';
    if (wantedReading.locator && !locator) return null;
    readings.push({ title, locator, claims: found }); claims.push(...found);
  }
  const intro = own('intro'), readingNote = word('reading'), place = own('place'), closing = own('review.closing');
  if (!intro || !readingNote || !place || !closing) return null;
  return { id: spec.id, title: jaunt.title, year: spec.year, band, question, intro, readingNote, place, closing, readings, claims };
}

export function createInvestigationDraft() {
  return { open: false, claim: '', uncertainty: '', selected: [], reviewed: false,
    savedSignature: '', savedEntryId: '', status: '' };
}

/** Refuse oversize authored context instead of letting the notebook silently trim it. */
export function investigationNote(model, draft) {
  if (!model) return { ok: false, reason: 'unavailable' };
  const claim = String(draft.claim ?? '').trim(), uncertainty = String(draft.uncertainty ?? '').trim();
  if (!claim) return { ok: false, reason: 'claim' };
  if (!uncertainty) return { ok: false, reason: 'uncertainty' };
  if (claim.length > CASE_LIMITS.claim || uncertainty.length > CASE_LIMITS.uncertainty) return { ok: false, reason: 'long' };
  const selected = model.claims.filter(c => draft.selected?.includes(c.id));
  if (!selected.length) return { ok: false, reason: 'evidence' };
  const sources = [...new Map(model.claims.flatMap(c => c.sources).map(s => [s.id, s])).values()];
  const entry = { kind: 'note', title: `${t('investigation.title')} · ${model.title}`, year: model.year,
    place: model.place,
    text: [model.question, `${t('investigation.claim')}\n${claim}`,
      `${t('investigation.selected')}\n${selected.map(c => c.label).join('\n')}`,
      `${t('investigation.uncertainty')}\n${uncertainty}`].join('\n\n'),
    excerpt: [model.readingNote, ...model.readings.flatMap(reading => [reading.title, reading.locator,
      ...reading.claims.flatMap(c => [`${c.label} · ${c.grade}`, c.locator !== reading.locator && c.locator,
        c.text, c.reasoning])].filter(Boolean)), model.closing].join('\n\n'), sources };
  if (entry.title.length > 200 || entry.text.length > 6000 || entry.excerpt.length > 12000
    || sources.length > 40 || sources.some(s => s.title.length > LIMITS.sourceTitle || s.id.length > 200)) return { ok: false, reason: 'unavailable' };
  return { ok: true, entry, signature: JSON.stringify(entry) };
}

/** Save only on the visitor's action. Unchanged repeated clicks do not add copies;
 * revising a saved case explicitly saves a new copy, leaving the earlier note intact. */
export function saveInvestigation(model, draft, notebook) {
  const prepared = investigationNote(model, draft);
  if (!prepared.ok) return prepared;
  try {
    const state = notebook.read();
    if (state.error) return { ok: false, reason: state.error };
    const saved = state.entries.find(e => e.id === draft.savedEntryId);
    if (draft.savedSignature === prepared.signature && saved
      && Object.keys(prepared.entry).every(key => JSON.stringify(saved[key]) === JSON.stringify(prepared.entry[key])))
      return { ok: true, duplicate: true };
    const result = notebook.add(prepared.entry);
    if (result.ok) { draft.savedSignature = prepared.signature; draft.savedEntryId = result.entry.id; }
    return result;
  } catch { return { ok: false, reason: 'storage' }; }
}
