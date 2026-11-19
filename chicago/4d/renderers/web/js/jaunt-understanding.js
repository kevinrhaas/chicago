/** Optional source-based reflection at a completed jaunt. No generated historical facts,
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
export function understandingQuestions(session) {
  const jaunt = session?.jaunt;
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
      candidates.push({ stop: stop.id, place: jaunt.places?.[stop.destination?.id] ?? '',
        claim: { id, text: claim.text, confidence: claim.confidence,
          locator: claim.locator ?? '', reasoning: claim.reasoning ?? '' },
        sources: refs.map(ref => ({ id: ref.source_id, citation: ref.citation, url: sourceURL(ref.url) ?? sourceURL(ref.archived_url) })) });
    }
  }
  if (!candidates.length) return [];
  const band = checkBand(jaunt);
  return [0, 1, 2].map(index => ({
    ...candidates[Math.round(index * (candidates.length - 1) / 2)],
    id: `${jaunt.id}:reflection:${index}`, number: index + 1, band,
    prompt: t(`understanding.prompt.${band}.${index}`),
  }));
}

/** The tab holds only one finished outing's draft; callers drop it on dismissal/replay. */
export function createUnderstandingDraft() {
  return { answers: ['', '', ''], reviewed: [false, false, false], open: false };
}
