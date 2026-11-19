/** Optional source-based check at a completed jaunt: three questions in the guide's voice,
 * each with one answer the jaunt's data settles (T-3670), and a reflection in your own words. No generated historical facts,
 * grading, storage or requests. All excerpts and citations belong to stops actually visited.
 * The prompts are editorial learning questions, never quotations attributed to a guide. */
import { t } from './strings/index.js';
import './strings/understanding.js';

export const CHECK_BANDS = Object.freeze(['3-5', '6-8', '9-10', '11-12', '18+']);
export const CHECK_AGES = Object.freeze({ '3-5': '8–10', '6-8': '11–13', '9-10': '14–15', '11-12': '16–17', '18+': '18+' });
export const ANSWER_LIMIT = 2400;

/** URLs in a source record are still data: no script, data or relative URLs become links. */
export function sourceURL(value) {
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) ? url.href : null; }
  catch { return null; }
}

export function checkBand(jaunt) {
  if (jaunt?.audience === 'adults') return '18+';
  return CHECK_BANDS.includes(jaunt?.grade_band) ? jaunt.grade_band : jaunt?.grade_band === 'K-2' ? '3-5' : '18+';
}

/** Three different reading operations, spread through the visited route. A short jaunt may
 * use one claim more than once; an uncited/invented claim is never used to fill a quota. */
export function understandingQuestions(session, { placeOf = null } = {}) {
  const jaunt = session?.jaunt;
  // The page names a stop as its route card does (the jaunt's own places, else the town's
  // label for the destination); a bare session names only the jaunt's own places.
  const nameOf = stop => jaunt?.places?.[stop?.destination?.id] || placeOf?.(stop) || '';
  if (!jaunt || session.phase !== 'outcome' || session.outcome?.fallback || !session.outcome?.completion_eligible) return [];
  const evidence = new Map((jaunt.evidence ?? []).map(claim => [claim.id, claim]));
  const citations = new Map((jaunt.citations ?? []).map(cite => [cite.source_id, cite]));
  const stops = new Map((jaunt.stops ?? []).map(stop => [stop.id, stop]));
  const candidates = [], seen = new Set();
  for (const visit of session.visited ?? []) {
    const stop = stops.get(visit.id);
    if (!stop || !visit.committed) continue;
    for (const id of stop.evidence ?? []) {
      const claim = evidence.get(id);
      if (seen.has(id) || !claim?.text || !['attested', 'inferred'].includes(claim.confidence)) continue;
      const refs = (claim.sources ?? []).map(source => citations.get(source));
      // Do not hide an unresolved reference by presenting the other references alone.
      if (!refs.length || refs.some(ref => !ref?.citation)) continue;
      seen.add(id);
      candidates.push({ stop: stop.id, place: nameOf(stop),
        claim: { id, text: claim.text, confidence: claim.confidence,
          locator: claim.locator ?? '', reasoning: claim.reasoning ?? '' },
        sources: refs.map(ref => ({ id: ref.source_id, citation: ref.citation, url: sourceURL(ref.url) ?? sourceURL(ref.archived_url) })) });
    }
  }
  if (!candidates.length) return [];
  const band = checkBand(jaunt);
  const places = [...new Set(candidates.map(c => c.place).filter(Boolean))];
  // Every place on the route that tells a claim: none of them is a wrong answer for it.
  const told = new Map();
  for (const visit of session.visited ?? []) {
    const stop = stops.get(visit.id), place = stop && nameOf(stop);
    if (!stop || !visit.committed || !place) continue;
    for (const id of stop.evidence ?? []) (told.get(id) ?? told.set(id, new Set()).get(id)).add(place);
  }
  return [0, 1, 2].map(index => {
    const picked = candidates[Math.round(index * (candidates.length - 1) / 2)];
    const id = `${jaunt.id}:reflection:${index}`;
    return { ...picked, id, number: index + 1, band,
      prompt: t(`understanding.prompt.${band}.${index}`),
      ask: askFor(KINDS[index], picked, { places, told: told.get(picked.claim.id) ?? new Set(), citations: jaunt.citations ?? [], band, id }) };
  });
}

/** T-3670, the guide's three questions. Each has one answer the jaunt's own data settles,
 * and every option is a real thing from this jaunt: a stop we visited, a confidence grade,
 * a source it cites. No option is a made-up fact, so a wrong choice is never a lie told
 * to the student, only a place, a grade or a source that does not go with this claim. */
export const KINDS = Object.freeze(['where', 'sure', 'source']);
const GRADES = Object.freeze(['attested', 'inferred', 'reconstructed']);
/** A citation's own words, without the reading note ("Read 5 November 2026."). */
export const shortCitation = citation => String(citation ?? '').replace(/\s*Read \d{1,2} \w+ \d{4}\.?\s*$/, '').trim();
// Stable per question, so a retry or a repaint never reshuffles the options.
function order(items, seed) {
  let h = 2166136261;
  for (const ch of seed) h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0;
  return items.map((item, i) => ({ item, k: Math.imul(h ^ (i + 1) * 2654435761, 2246822519) >>> 0 }))
    .sort((a, b) => a.k - b.k).map(x => x.item);
}
function askFor(kind, q, { places, told, citations, band, id }) {
  const stem = k => t(`understanding.ask.${k}.${band}`);
  if (kind === 'where' && q.place) {
    const others = order(places.filter(p => p !== q.place && !told.has(p)), `${id}:others`).slice(0, 2);
    if (others.length === 2) return { kind, stem: stem(kind), answer: 'a',
      options: order([{ id: 'a', label: q.place }, { id: 'b', label: others[0] }, { id: 'c', label: others[1] }], id) };
  }
  if (kind === 'source') {
    const mine = new Set(q.sources.map(s => s.id));
    const right = shortCitation(q.sources[0]?.citation);
    const others = order([...new Set(citations.filter(c => c?.citation && c.source_id && !mine.has(c.source_id))
      .map(c => shortCitation(c.citation)).filter(c => c && c !== right))], `${id}:others`).slice(0, 2);
    if (right && others.length === 2) return { kind, stem: stem(kind), answer: 'a',
      options: order([{ id: 'a', label: right }, { id: 'b', label: others[0] }, { id: 'c', label: others[1] }], id) };
  }
  // How sure can we be? Always answerable: the claim's own grade.
  return { kind: 'sure', stem: stem('sure'), answer: q.claim.confidence,
    options: GRADES.map(g => ({ id: g, label: t(`understanding.choice.${g}`) })) };
}

/** The tab holds only one finished outing's draft; callers drop it on dismissal/replay. */
export function createUnderstandingDraft() {
  return { answers: ['', '', ''], reviewed: [false, false, false], open: false,
    chosen: [null, null, null], tries: [0, 0, 0], solved: [false, false, false] };
}

/** Ungraded and retry-able: a choice is right or "not yet"; nothing is scored or kept. */
export function answerQuestion(question, draft, index, option) {
  if (!question?.ask || draft.solved[index]) return { right: draft.solved[index], tries: draft.tries[index] };
  if (!question.ask.options.some(o => o.id === option)) return { right: false, tries: draft.tries[index] };
  draft.chosen[index] = option; draft.tries[index] += 1;
  const right = option === question.ask.answer;
  if (right) draft.solved[index] = true;
  return { right, tries: draft.tries[index] };
}
