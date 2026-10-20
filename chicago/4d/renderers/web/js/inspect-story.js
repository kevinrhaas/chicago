/**
 * T-2643 — Inspect's Story tab: a timeline from design to today with three marks on it,
 * BUILT, YOU ARE HERE and TODAY (design doc "Field Navigator Mk II" §08 "Story", §12).
 *
 * Every row is a dated fact the data already carries; nothing here composes a date:
 *
 *   - BUILT is the summary record's own `built.year`, with its grade. A building without a
 *     record has no build date anywhere in its sidecar — `documented_range.from` is where
 *     the evidence of its standing begins (often the date of a description, or the scene's
 *     own date), never when it went up — so the row says the records give no date.
 *   - STOOD HERE is the modelled phase (`documented_range`, §12 "Modeled phase dates → Story
 *     timeline"), the years this scene shows the building as it stood, with that claim's grade.
 *   - The record's `story` entries, each with its grade — only those whose `era` is this
 *     scene's (§12: content tagged with another scene's era never renders).
 *   - The town's fire limit, from the 5 August 1835 by-law, on an 1835 building only (the
 *     law's own year must be the scene's), graded no better than inferred: which side of the
 *     line a building stood on is worked out from the street lines the by-law names, so it
 *     is never stronger than where the building itself is placed.
 *   - YOU ARE HERE is the scene's own date, the visit.
 *   - TODAY is the record's status, or the sidecar's `present_status`; with neither, the
 *     row says the records do not say.
 *
 * A row whose earliest possible day falls after the scene date is AFTER YOUR VISIT, and so is
 * Today. A date coarser than the scene's (an entry dated "1904" on a 1 July 1904 scene) may be
 * before the visit, so it is not marked after it.
 */
import { t } from './strings/index.js';
import './strings/inspect-story.js';

const GRADES = ['attested', 'inferred', 'reconstructed'];
const ISO = /^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$/;

function yearOf(date) {
  const m = ISO.exec(String(date ?? ''));
  return m ? m[1] : null;
}

/** The first day a date can mean: '1885' → '1885-01-01', '1885-05' → '1885-05-01'. */
function earliest(date) {
  const m = ISO.exec(String(date ?? ''));
  return m ? `${m[1]}-${m[2] ?? '01'}-${m[3] ?? '01'}` : null;
}

/** The weaker of two grades on the data's ladder; an unknown grade is no grade. */
function weaker(a, b) {
  const i = GRADES.indexOf(a);
  const j = GRADES.indexOf(b);
  if (i < 0 || j < 0) return null;
  return GRADES[Math.max(i, j)];
}

function graded(g) {
  return GRADES.includes(g) ? g : null;
}

/** "1887 – 1946" (non-breaking), or the one year when both ends fall in it. */
function span(range) {
  const f = yearOf(range?.from);
  const to = yearOf(range?.to);
  if (f && to) return f === to ? f : `${f}\u00a0–\u00a0${to}`; // kept on one line
  return f ?? to ?? '';
}

/** The visit, in words: "1 July 1904". */
export function visitWords(date) {
  const m = ISO.exec(String(date ?? ''));
  if (!m || !m[3]) return null;
  try {
    return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])).toLocaleDateString('en-GB',
      { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
  } catch {
    return null;
  }
}

/** The fire-limit side of a building, from the card's loaded limits (popup.js), or null. */
function fireRow(limit, sceneYear, placeGrade) {
  if (!limit || typeof limit.inside !== 'boolean') return null;
  const lawDate = limit.passed;
  if (!sceneYear || yearOf(lawDate) !== sceneYear) return null;
  return {
    kind: 'event', mark: 'fire', date: lawDate,
    text: t(limit.inside ? 'inspect-story.fire.inside' : 'inspect-story.fire.outside'),
    grade: weaker('inferred', placeGrade) ?? null,
  };
}

/**
 * The Story tab's timeline for one building, in order.
 *
 * @param {object} p
 * @param {object|null} p.sum      the compiled summary record (inspect/<scene>.json), or null
 * @param {object|null} p.sidecar  the building's sidecar, or null
 * @param {object|null} p.scene    the scene ({ id, target_date })
 * @param {object|null} [p.fireLimit]  { inside, passed } from the card's loaded fire limit
 * @returns {{ lead: string, rows: object[] }} each row { kind, mark, date, when, text, grade,
 *   after, missing }
 */
export function storyTimeline({ sum = null, sidecar = null, scene = null, fireLimit = null } = {}) {
  const sceneId = String(scene?.id ?? scene?.scene_id ?? '');
  const sceneDate = ISO.exec(String(scene?.target_date ?? ''))?.[3] ? String(scene.target_date) : null;
  const sceneYear = yearOf(sceneDate) ?? yearOf(sceneId);
  // The last day that is still the visit: the scene's date, or (with only a year) that year.
  const visitEnd = sceneDate ?? (sceneYear ? `${sceneYear}-12-31` : null);
  const isAfter = (date) => !!(visitEnd && earliest(date) && earliest(date) > visitEnd);

  const dated = [];
  const built = sum?.built;
  const builtRow = Number.isInteger(built?.year)
    ? { kind: 'built', mark: 'built', date: String(built.year), text: '', grade: graded(built.grade) }
    : { kind: 'built', mark: 'built', date: null, text: t('inspect-story.built.none'), grade: null, missing: true };
  if (builtRow.date) dated.push(builtRow);

  const range = sidecar?.documented_range;
  if (range && (yearOf(range.from) || yearOf(range.to))) {
    dated.push({ kind: 'stood', mark: 'stood', date: range.from && yearOf(range.from) ? range.from : range.to,
      text: t('inspect-story.stood.span', { span: span(range) }), grade: graded(range.confidence) });
  }

  for (const entry of Array.isArray(sum?.story) ? sum.story : []) {
    if (!sceneId || String(entry?.era ?? '') !== sceneId) continue; // another scene's era never renders
    if (!yearOf(entry.date) || !entry.text) continue;
    dated.push({ kind: 'event', mark: 'event', date: String(entry.date), text: String(entry.text), grade: graded(entry.grade) });
  }

  const fire = fireRow(fireLimit, sceneYear, sidecar?.placement?.position_confidence);
  if (fire) dated.push(fire);

  const RANK = { built: 0, stood: 1, event: 2 };
  const order = (a, b) => (earliest(a.date) < earliest(b.date) ? -1 : earliest(a.date) > earliest(b.date) ? 1 : 0)
    || RANK[a.kind] - RANK[b.kind];
  for (const r of dated) { r.after = isAfter(r.date); r.when = yearOf(r.date); }
  const before = dated.filter((r) => !r.after).sort(order);
  const later = dated.filter((r) => r.after).sort(order);

  const rows = [];
  if (builtRow.missing) rows.push({ ...builtRow, when: '', after: false });
  rows.push(...before);
  const words = visitWords(sceneDate);
  rows.push({ kind: 'here', mark: 'here', date: sceneDate ?? sceneYear, when: sceneYear ?? '', text: words ?? sceneYear ?? '', grade: null, after: false });
  rows.push(...later);

  const status = sum?.status;
  const present = sidecar?.attributes?.present_status;
  let today;
  if (status?.text) {
    const said = [status.text, status.today].filter(Boolean);
    today = { text: said.length === 2 && said[0] !== said[1] ? said.join(' · ') : said[0], grade: graded(status.grade) };
  } else if (present?.value) {
    today = { text: String(present.value).replace(/_/g, ' '), grade: graded(present.confidence) };
  } else {
    today = { text: t('inspect-story.today.none'), grade: null, missing: true };
  }
  rows.push({ kind: 'today', mark: 'today', date: null, when: '', after: true, ...today });

  const lead = words ? t('inspect-story.lead', { date: words })
    : sceneYear ? t('inspect-story.lead.year', { year: sceneYear }) : '';
  return { lead, rows };
}

const KICKER = { built: 'inspect-story.built', stood: 'inspect-story.stood', here: 'inspect-story.here', today: 'inspect-story.today' };

/**
 * Draw the timeline. `dot(doc, grade)` is Inspect's own grade dot, so every fact line here
 * carries the same mark as the front page.
 */
export function renderStory(doc, model, dot) {
  const el = (tag, cls, text) => {
    const n = doc.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const block = el('section', 'insp-sec insp-story');
  block.append(el('h3', 'insp-h', t('inspect-story.title')));
  if (model.lead) block.append(el('p', 'nav-sub insp-story-lead', model.lead));
  const ol = el('ol', 'insp-timeline insp-story-line');
  ol.setAttribute('aria-label', t('inspect-story.list.label'));
  for (const r of model.rows) {
    const li = el('li', `insp-when insp-mark-${r.mark}${r.after ? ' is-after' : ''}${r.missing ? ' is-missing' : ''}`);
    li.dataset.mark = r.mark;
    if (r.date) li.dataset.date = r.date;
    if (r.after) li.dataset.after = '';
    if (r.kind === 'here') li.setAttribute('aria-current', 'date');
    li.append(el('span', 'insp-date', r.when ?? ''));
    const body = el('div', 'insp-story-body');
    if (KICKER[r.kind]) {
      body.append(el('span', 'insp-kicker', t(KICKER[r.kind])));
    }
    if (r.text) {
      const what = el('span', 'insp-what', r.text);
      if (r.grade) what.append(dot(doc, r.grade));
      body.append(what);
    } else if (r.grade) {
      body.lastChild?.append(dot(doc, r.grade));
    }
    if (r.after) body.append(el('span', 'insp-after', t('inspect-story.after')));
    li.append(body);
    ol.append(li);
  }
  block.append(ol);
  return block;
}

export const _test = { earliest, weaker, span, yearOf };
