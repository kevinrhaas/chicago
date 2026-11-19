/** One evidence comparison attached to a completed story jaunt that carries a case:
 * Gossip's two newspapers (T-3663) and the Great Fire's sworn accounts (T-3693). It reads
 * the current telling's cited claims; it creates no historical facts or persistent draft. */
import { checkBand } from './jaunt-understanding.js';
import { t } from './strings/index.js';
import './strings/investigation.js';

export const CASE_LIMITS = Object.freeze({ claim: 2400, uncertainty: 1200 });
/** Each case: the jaunt it belongs to, the claims it compares (each on the stop that cites
 * it, from the source and at the grade it must still have), and how they group into
 * readings. `key` prefixes the case's own strings; Gossip's are the table's unprefixed ones. */
const CASES = Object.freeze({
  'gossip-or-notice': { scene: '1835', key: '', claims: [
    { id: 'land-sale', stop: 'the-democrat', source: 'chicago_democrat_1833_1835', confidence: 'attested' },
    { id: 'bank-branch', stop: 'the-american', source: 'chicago_american_1835', confidence: 'attested' },
    { id: 'bank-springfield', stop: 'the-american', source: 'chicago_american_1835', confidence: 'inferred' },
  ],
  // Springfield is a reading of the SAME American item, not another witness. Its
  // record has no locator; carry the branch item's locator beside both readings.
  readings: [{ paper: 'democrat', claims: [0] }, { paper: 'american', claims: [1, 2], locator: 1 }] },
  'who-started-the-fire': { scene: '1871', key: 'fire.', claims: [
    { id: 'oleary-testimony', stop: 'catherine', source: 'greatchicagofire_oleary_legend_2011', confidence: 'attested' },
    { id: 'sullivan-affidavit', stop: 'the-barn', source: 'andreas_1885_v2', confidence: 'attested' },
    { id: 'board-finding', stop: 'the-inquiry', source: 'greatchicagofire_oleary_legend_2011', confidence: 'attested' },
    { id: 'peg-leg', stop: 'other-suspects', source: 'chicago_tribune_1998_03_03_odds_improve', confidence: 'attested' },
  ],
  readings: [{ paper: 'oleary', claims: [0] }, { paper: 'sullivan', claims: [1] },
    { paper: 'board', claims: [2] }, { paper: 'bales', claims: [3] }] },
});
const label = id => t(`investigation.evidence.${id}`);

/** The case a completed telling offers, or null when it has none or anything it rests on
 * is missing: a stop not walked, a claim moved, regraded or unresolved. */
export function jauntInvestigation(session) {
  const jaunt = session?.jaunt, id = jaunt?.version_of || jaunt?.id;
  const spec = typeof id === 'string' && Object.hasOwn(CASES, id) ? CASES[id] : null;
  if (!spec || String(jaunt.scene) !== spec.scene
    || session.phase !== 'outcome' || session.outcome?.fallback || !session.outcome?.completion_eligible) return null;
  const visited = new Set((session.visited ?? []).filter(v => v.committed).map(v => v.id));
  const claims = [];
  for (const wanted of spec.claims) {
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
  const readings = spec.readings.map(r => ({ title: t(`investigation.${spec.key}paper.${r.paper}`),
    locator: claims[r.locator ?? r.claims[0]].locator, claims: r.claims.map(i => claims[i]) }));
  if (readings.some(r => !r.locator)) return null;
  const band = checkBand(jaunt), k = `investigation.${spec.key}`;
  return { title: jaunt.title, year: spec.scene, band, question: t(`${k}question.${band}`),
    intro: t(`${k}intro`), reading: t(`${k}reading`), place: t(`${k}place`), liberties: t(`${k}review.liberties`),
    grades: { attested: t(`${k}grade.attested`), inferred: t(`${k}grade.inferred`) },
    readings, claims };
}

/** T-3663's name for the Gossip case alone; jauntInvestigation offers every case. */
export function gossipInvestigation(session) {
  const jaunt = session?.jaunt;
  return (jaunt?.version_of || jaunt?.id) === 'gossip-or-notice' ? jauntInvestigation(session) : null;
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
    place: model.place ?? t('investigation.place'),
    text: [model.question, `${t('investigation.claim')}\n${claim}`,
      `${t('investigation.selected')}\n${selected.map(c => label(c.id)).join('\n')}`,
      `${t('investigation.uncertainty')}\n${uncertainty}`].join('\n\n'),
    excerpt: [model.reading ?? t('investigation.reading'), ...model.readings.flatMap(reading => [reading.title, reading.locator,
      ...reading.claims.flatMap(c => [`${label(c.id)} · ${model.grades?.[c.confidence] ?? t(`investigation.grade.${c.confidence}`)}`,
        c.text, c.reasoning].filter(Boolean))]), model.liberties ?? t('investigation.review.liberties')].join('\n\n'), sources };
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
