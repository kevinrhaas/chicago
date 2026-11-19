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
      // Only a record the stop actually told aloud: the question quotes the line you
      // heard, and the record behind it waits under "Where does this come from?".
      const heard = heardLine(stop, claim.text);
      if (!heard) continue;
      seen.add(id);
      candidates.push({ stop: stop.id, place: nameOf(stop), heard,
        claim: { id, text: claim.text, confidence: claim.confidence,
          locator: claim.locator ?? '', reasoning: claim.reasoning ?? '' },
        sources: refs.map(ref => ({ id: ref.source_id, citation: ref.citation, url: sourceURL(ref.url) ?? sourceURL(ref.archived_url) })) });
    }
  }
  if (!candidates.length) return [];
  const band = checkBand(jaunt);
  const places = [...new Set(candidates.map(c => c.place).filter(Boolean))];
  // Every place on the route, and every host, that tells a claim: none of them is a wrong
  // answer for it.
  const told = new Map(), toldBy = new Map(), add = (map, id, v) => (map.get(id) ?? map.set(id, new Set()).get(id)).add(v);
  for (const visit of session.visited ?? []) {
    const stop = stops.get(visit.id), place = stop && nameOf(stop), who = stop && speakerOf(stop);
    if (!stop || !visit.committed) continue;
    for (const id of stop.evidence ?? []) { if (place) add(told, id, place); if (who) add(toldBy, id, who); }
  }
  for (const c of candidates) c.speaker = speakerOf(stops.get(c.stop));
  const speakers = [...new Set(candidates.map(c => c.speaker).filter(Boolean))];
  return [0, 1, 2].map(index => {
    const picked = candidates[Math.round(index * (candidates.length - 1) / 2)];
    const id = `${jaunt.id}:reflection:${index}`;
    return { ...picked, id, number: index + 1, band,
      prompt: t(`understanding.prompt.${band}.${index}`),
      ask: askFor(PREFER[index], picked, { places, told: told.get(picked.claim.id) ?? new Set(),
        speakers, toldBy: toldBy.get(picked.claim.id) ?? new Set(), band, id }) };
  });
}

/** What a stop says aloud, line by line: its text, then its staged scene's caption. A
 * line may run on into the next sentence of the same passage, so it is always a span of the
 * stop's own words. */
const said = stop => [stop?.text, stop?.stage?.caption].filter(Boolean).flatMap(passage => {
  const text = String(passage), spans = sentenceSpans(text);
  return spans.flatMap(([a, b], i) => [text.slice(a, b), ...(spans[i + 1] ? [text.slice(a, spans[i + 1][1])] : [])])
    .map(x => x.trim());
});
// Mr., Mrs., St., Capt. and an initial ("W. H. Stow") do not end a sentence.
const NOT_AN_END = /(?:^|[\s('"‘“])(?:mr|mrs|ms|dr|st|capt|lt|col|gen|maj|sgt|rev|messrs|jr|sr|co|no|vol|pp?|ft|mt|[a-z])$/i;
function sentenceSpans(text) {
  const spans = []; let start = 0;
  for (const m of text.matchAll(/[.!?]+['’"”)]*(?=\s+|$)/g)) {
    const end = m.index + m[0].length;
    if (m[0][0] === '.' && NOT_AN_END.test(text.slice(start, m.index))) continue;
    if (text.slice(start, end).trim()) spans.push([start, end]);
    start = end;
  }
  if (text.slice(start).trim()) spans.push([start, text.length]);
  return spans;
}
const COMMON = new Set(('the a an and or of to in on at by for from with as is was were be been his her their its it this that these those he she they '
  + 'we our you your i my me who which when where what had has have not but so than then there here into over under about after before one two all '
  + 'any each very more most also only same such some just now still even them him us did does do can could would will shall may might must out up down '
  + 'off much many own other another back long little great good new old first last next way like').split(' '));
const stem = w => w.length > 4 ? w.replace(/(ings|ing|ed|es|s)$/, '') : w;
const contentWords = text => new Set((String(text ?? '').toLowerCase().replace(/[’‘]/g, "'").match(/[a-z0-9]+/g) ?? [])
  .filter(w => !COMMON.has(w) && (w.length > 2 || /\d/.test(w))).map(stem));
// A date or an hour sets a scene; it is not something a record tells. A line that shares
// only those with a record ("It is May 1804, in the morning") is not the record being said.
const WHEN = new Set(('january february march april may june july august september october november december monday tuesday '
  + 'wednesday thursday friday saturday sunday morning afternoon evening night noon midnight sunset sunrise dawn dusk '
  + 'clock today year summer winter spring autumn').split(' ').map(stem));
export const HEARD_MIN_SHARED = 3, HEARD_MIN_COVER = 0.5, HEARD_MIN_BOTH = 0.3;
/** T-3670 (owner, 19 November): a question must be about something the walk actually said.
 * The line of the stop (one sentence, or two running on) that a record's own words cover
 * best; null when no line shares at least three content words with it, two of them more
 * than a date or an hour, and half of the line's words (or the record's, if shorter). A
 * stop's evidence list also holds records behind the scene that are never spoken, and
 * those are never quizzed. */
export function heardLine(stop, recordText) {
  const record = contentWords(recordText);
  let best = null;
  for (const line of said(stop)) {
    const words = contentWords(line);
    const shared = [...words].filter(w => record.has(w));
    const telling = shared.filter(w => !WHEN.has(w) && !/^\d+$/.test(w)).length;
    // Both ways: the line is mostly the record's words, and the record is largely in the line.
    const ofLine = shared.length / Math.max(1, words.size), ofRecord = shared.length / Math.max(1, record.size);
    const score = shared.length * ofLine;
    if (shared.length >= HEARD_MIN_SHARED && telling >= 2 && Math.max(ofLine, ofRecord) >= HEARD_MIN_COVER
      && Math.min(ofLine, ofRecord) >= HEARD_MIN_BOTH
      && (!best || score > best.score)) best = { line, score };
  }
  return best?.line ?? null;
}

/** The one person who hosts a stop, by the name its own card link gives; a stop with no
 * host, or several, has no single teller to ask about. */
function speakerOf(stop) {
  const hosts = (stop?.hosts ?? []).map(h => h?.person).filter(Boolean);
  if (hosts.length !== 1) return '';
  return (stop.links ?? []).find(l => l?.kind === 'person' && l.id === hosts[0])?.label ?? '';
}

/** T-3670, the guide's three questions. Each has one answer the jaunt's own data settles,
 * and every option is a real thing from this jaunt: a stop we visited, a person who told
 * us something, a confidence grade. No option is a made-up fact, so a wrong choice is
 * never a lie told to the student, only a place, a teller or a grade that does not go with
 * this claim. (A "which source" question was tried and dropped on the owner's reading,
 * 19 November: a bibliographic citation is not something a student can recall or weigh,
 * and the record behind a line can differ from the book the telling echoes.) */
export const KINDS = Object.freeze(['where', 'who', 'sure']);
const PREFER = Object.freeze([['where', 'who'], ['sure'], ['who', 'where']]);
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
/** "I'm John Glessner" in the quoted line would answer "who told us" for the student. */
const namesSpeaker = (line, speaker) => {
  const given = String(speaker ?? '').split(/\s+/)[0];
  return !!speaker && (String(line ?? '').includes(speaker) || (given.length > 2 && new RegExp(`\\b${given}\\b`).test(String(line ?? ''))));
};
function askFor(kinds, q, { places, told, speakers, toldBy, band, id }) {
  const stem = k => t(`understanding.ask.${k}.${band}`);
  const three = (kind, right, pool, taken) => {
    const others = order(pool.filter(p => p !== right && !taken.has(p)), `${id}:others`).slice(0, 2);
    return right && others.length === 2 ? { kind, stem: stem(kind), answer: 'a',
      options: order([{ id: 'a', label: right }, { id: 'b', label: others[0] }, { id: 'c', label: others[1] }], id) } : null;
  };
  for (const kind of kinds) {
    const ask = kind === 'where' ? three(kind, q.place, places, told)
      : kind === 'who' && !namesSpeaker(q.heard, q.speaker) ? three(kind, q.speaker, speakers, toldBy) : null;
    if (ask) return ask;
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
