/** One evidence comparison attached to the existing Gossip completion. It reads the
 * current telling's cited claims; it creates no historical facts or persistent draft. */
import { checkBand } from './jaunt-understanding.js';
import { t } from './strings/index.js';
import './strings/investigation.js';

export const CASE_LIMITS = Object.freeze({ claim: 2400, uncertainty: 1200 });
const CLAIMS = Object.freeze([
  { id: 'land-sale', stop: 'the-democrat', source: 'chicago_democrat_1833_1835', confidence: 'attested' },
  { id: 'bank-branch', stop: 'the-american', source: 'chicago_american_1835', confidence: 'attested' },
  { id: 'bank-springfield', stop: 'the-american', source: 'chicago_american_1835', confidence: 'inferred' },
]);
const label = id => t(`investigation.evidence.${id}`);

export function gossipInvestigation(session) {
  const jaunt = session?.jaunt;
  if ((jaunt?.version_of || jaunt?.id) !== 'gossip-or-notice' || String(jaunt.scene) !== '1835'
    || session.phase !== 'outcome' || session.outcome?.fallback || !session.outcome?.completion_eligible) return null;
  const visited = new Set((session.visited ?? []).filter(v => v.committed).map(v => v.id));
  const claims = [];
  for (const wanted of CLAIMS) {
    const stop = jaunt.stops?.find(s => s.id === wanted.stop);
    const claim = jaunt.evidence?.find(c => c.id === wanted.id);
    if (!visited.has(wanted.stop) || !stop?.evidence?.includes(wanted.id) || !claim?.text
      || claim.confidence !== wanted.confidence || !claim.sources?.includes(wanted.source)) return null;
    const sources = claim.sources.map(id => jaunt.citations?.find(c => c.source_id === id));
    if (sources.some(s => !s?.citation) || (claim.confidence === 'inferred' && !claim.reasoning)) return null;
    claims.push({ id: claim.id, text: claim.text, confidence: claim.confidence,
      locator: claim.locator || '', reasoning: claim.reasoning || '',
      sources: sources.map(s => ({ id: s.source_id, title: s.citation, url: '' })) });
  }
  // Springfield is a reading of the SAME American item, not another witness. Its
  // record has no locator; carry the branch item's locator beside both readings.
  if (!claims[0].locator || !claims[1].locator) return null;
  const band = checkBand(jaunt);
  return { title: jaunt.title, year: '1835', band, question: t(`investigation.question.${band}`),
    readings: [
      { title: t('investigation.paper.democrat'), locator: claims[0].locator, claims: [claims[0]] },
      { title: t('investigation.paper.american'), locator: claims[1].locator, claims: claims.slice(1) },
    ], claims,
  };
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
    place: t('investigation.place'),
    text: [model.question, `${t('investigation.claim')}\n${claim}`,
      `${t('investigation.selected')}\n${selected.map(c => label(c.id)).join('\n')}`,
      `${t('investigation.uncertainty')}\n${uncertainty}`].join('\n\n'),
    excerpt: [t('investigation.reading'), ...model.readings.flatMap(reading => [reading.title, reading.locator,
      ...reading.claims.flatMap(c => [`${label(c.id)} · ${t(`investigation.grade.${c.confidence}`)}`,
        c.text, c.reasoning].filter(Boolean))]), t('investigation.review.liberties')].join('\n\n'), sources };
  if (entry.title.length > 200 || entry.text.length > 6000 || entry.excerpt.length > 12000
    || sources.length > 40 || sources.some(s => s.title.length > 500 || s.id.length > 200)) return { ok: false, reason: 'unavailable' };
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
