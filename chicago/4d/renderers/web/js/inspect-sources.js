/**
 * inspect-sources.js — Inspect's Sources tab (T-2644; design doc §08 "Sources", §12 "Move
 * one level down").
 *
 * EVERY FACT THE BUILDING HOLDS, GROUPED BY GRADE. Two kinds of fact stand behind a
 * building, and both are graded and sourced in the data:
 *   - the front page's facts, where the building has an authored summary record
 *     (data/summaries/, compiled into inspect/<scene>.json by tools/compile_summaries.py):
 *     status, built, each key fact, resident, Look-for line, notable fact and story entry;
 *   - the record's own claims, from its sidecar, exactly the set the card's "What did we
 *     include" counts: whether it stood here, where it stood, its outline, and each
 *     attribute.
 * The header counts them, and the Overview's Confidence meter counts the same list
 * (`factCounts`), so the meter and the tab it opens cannot disagree.
 *
 * NOTHING HERE IS COMPOSED BEYOND THE DATA. A fact's label is the record's own (a key
 * fact's label, a person's name) or a plain name for the claim; a value is shown only when
 * it reads as words and passes the visitor lint (fallback-summary.js `clean`). A fact's
 * reasoning (its `note`, the card's "why") is shown in the record's own words when it is
 * clean, and otherwise the row says the reasoning is written for researchers and sits in the
 * full record — never a paraphrase, never a cut-down sentence.
 *
 * HUMAN SOURCE TITLES. A source record carries one `citation` and no separate title, so a
 * title is the citation's own opening words (`sourceTitle`): its first sentence or clause,
 * long enough to say what it is, cut before anything that is not for a visitor (a file
 * name, a handle, an id), and shortened at a word with an ellipsis. It is always a prefix
 * of the citation, so it cannot claim more than the citation does, and the full citation is
 * folded under the fact. No source id, tier number or tier label reaches the page.
 *
 * WHAT KIND OF SOURCE (`sourceTag`), true by definition. §12 asks for "from the time" in place
 * of the tier, and a label must not claim what the data does not: Glessner's 1963-65 HABS
 * photographs are tier 1, first-hand, and are not from the time of a 1904 visit. So "from the
 * time" is said only where the source record carries a date (`source_dates` in the compiled
 * summaries) whose latest year in its leading clause is on or before the scene's year.
 * Every other source says what its rung IS, in the ladder's own terms (docs/PROVENANCE.md
 * § Evidence tiers): first-hand, a witness remembering, gathered from witnesses, a
 * historian's account, a modern reconstruction, a popular map.
 *
 * LIBERTIES, by name (§03: "Every choice we made without a source, listed by name"): each
 * liberty recorded against this building, by its title, with the parts of its entry that
 * are written for a visitor folded under it.
 */
import { citationItems, escapeHtml } from './citations.js';
import { claimValueText } from './claim-value.js';
import { clean, fallbackAddress } from './fallback-summary.js';
import { rangeWords } from './range-words.js';
import { t } from './strings/index.js';
import './strings/inspect-sources.js';
import { gradeTerm } from './strings/terms.js';

export const GRADES = ['attested', 'inferred', 'reconstructed'];

const s = (key, vars) => t(`inspect-sources.${key}`, vars);

/** A value long enough to wrap past two lines sits in the open row, not on its summary. */
const SHORT_VALUE = 90;
/** A source title's length, in characters, before it is shortened at a word. */
const TITLE_MAX = 80;
/** A first sentence shorter than this ("Sanborn Map Company.", an author list) takes the next one too. */
const TITLE_MIN = 36;

// A period after one of these, or after a single capital (an initial), does not end a title.
const ABBREV = new Set(['mr', 'mrs', 'ms', 'dr', 'st', 'ave', 'av', 'blvd', 'jr', 'sr', 'co', 'gen', 'col', 'rev',
  'capt', 'lt', 'mt', 'ft', 'no', 'nos', 'vs', 'inc', 'bros', 'messrs', 'prof', 'hon', 'gov', 'esq', 'ill',
  'vol', 'vols', 'ed', 'eds', 'ca', 'c', 'pp', 'p', 'fig', 'figs', 'ser', 'dept']);

// Liberty fields that are bookkeeping, not an account of the choice.
const LIBERTY_SKIP = /^(recorded|revised|covers|ticket|related|sources|review|applies to)$/i;

/** A claim's key as words: `roof_covering` → "Roof covering", `frame_ft` → "Frame (ft)". */
function keyWords(key) {
  const named = t(`inspect-sources.attr.${String(key).replace(/_/g, '-')}`);
  if (named) return named;
  const w = String(key).replace(/_/g, ' ').replace(/\b(ft|m)\b/g, '($1)').trim();
  const label = w.charAt(0).toUpperCase() + w.slice(1);
  return clean(label) ? label : s('label.detail');
}

/** A value in words, or '' — a structured or uncleanable value is left off. */
function valueWords(v) {
  const text = claimValueText(v);
  return text == null ? '' : clean(String(text));
}

const list = (v) => (Array.isArray(v) ? v.filter(Boolean) : []);

/**
 * Every graded fact behind a building, in reading order: the summary record's facts first
 * (as the front page orders them), then the record's claims.
 * @param {object|null} sidecar  the record's compiled sidecar
 * @param {object|null} summary  its compiled summary record, or null
 * @returns {{label: string, value: string, grade: string, sources: string[], note: string,
 *   absent: boolean, from: 'summary'|'record'}[]}
 */
export function buildingFacts(sidecar, summary) {
  const out = [];
  const add = (from, label, value, claim) => out.push({
    from,
    label: String(label ?? ''),
    value: String(value ?? ''),
    grade: claim?.grade ?? claim?.confidence ?? null,
    sources: list(claim?.sources ?? claim?.position_sources).map(String),
    note: String(claim?.note ?? ''),
    absent: claim?.geometry === 'absent',
  });

  const sum = summary && typeof summary === 'object' ? summary : null;
  if (sum) {
    if (sum.status) add('summary', s('label.today'), [sum.status.text, sum.status.today].filter(Boolean).join(' · '), sum.status);
    if (sum.built) add('summary', s('label.built'), sum.built.phrase ?? sum.built.year ?? '', sum.built);
    for (const k of list(sum.key)) add('summary', k.label, k.value, k);
    for (const r of list(sum.residents)) add('summary', r.name ?? '', r.role ?? '', r);
    for (const l of list(sum.lookFor)) add('summary', s('label.look'), l.text, l);
    for (const n of list(sum.notable)) add('summary', s('label.notable'), n.text, n);
    for (const e of list(sum.story)) add('summary', String(e.date ?? '').slice(0, 4), e.text, e);
  }

  const sc = sidecar && typeof sidecar === 'object' ? sidecar : null;
  if (sc) {
    // The card's own set and rule (popup.js gradedClaims, basisSection): a claim with no
    // grade is counted as the card counts it, reconstructed; one off the scale is kept
    // apart and said to be a fault.
    const range = sc.documented_range;
    if (range && (range.from || range.to)) {
      // T-3037: the span in the ends the record dates; a bound is not a date, so with
      // neither end dated the fact is the scene's year, which is what the record claims.
      const sceneYear = /^\d{4}/.exec(String(sc.target_date ?? sc.scene ?? ''))?.[0] ?? '';
      add('record', s(sc.attributes?.present_status ? 'label.stood' : 'label.stood.whether'),
        rangeWords(range) || (sceneYear ? s('stood.in', { year: sceneYear }) : ''),
        { ...range, confidence: range.confidence || 'reconstructed' });
    }
    const p = sc.placement ?? {};
    add('record', s('label.place'), fallbackAddress(sc),
      { confidence: p.position_confidence || 'reconstructed', sources: p.position_sources, note: p.position_note });
    if (sc.footprint?.confidence) add('record', s('label.outline'), '', sc.footprint);
    for (const [key, attr] of Object.entries(sc.attributes || {})) {
      const a = attr || {};
      add('record', keyWords(key), valueWords(a.value), { ...a, confidence: a.confidence || 'reconstructed' });
    }
  }
  return out;
}

/** {attested, inferred, reconstructed, other, total} over `buildingFacts`. */
export function factCounts(facts) {
  const n = { attested: 0, inferred: 0, reconstructed: 0, other: 0, total: 0 };
  for (const f of facts) {
    if (GRADES.includes(f.grade)) n[f.grade] += 1; else n.other += 1;
    n.total += 1;
  }
  return n;
}

/**
 * The latest year a source's recorded date names, read from its leading clause only (before
 * any ';' or '('), so "1881; accessed 2026-09-02" is 1881 and "1885-1887" is 1887. Null for
 * an undated source or a date with no year. Taking the latest year is the cautious reading:
 * a source that may be later than the scene is never called "from the time".
 * @param {string|null|undefined} date
 */
export function sourceYear(date) {
  const lead = String(date ?? '').split(/[;(]/)[0];
  const years = lead.match(/(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)/g);
  return years ? Math.max(...years.map(Number)) : null;
}

/**
 * The tag on a source: "from the time" where its recorded date is on or before the scene's
 * year, else what kind of source its rung says it is; '' where neither is known.
 * @param {number|string|null} tier
 * @param {string|null} date       the source record's own `date`
 * @param {number|string|null} sceneYear
 */
export function sourceTag(tier, date, sceneYear) {
  const y = sourceYear(date);
  const scene = Number.parseInt(String(sceneYear ?? ''), 10);
  if (y !== null && Number.isFinite(scene) && y <= scene) return s('when.period');
  const n = Number(tier);
  return Number.isInteger(n) && n >= 1 && n <= 6 ? s(`kind.${n}`) : '';
}

/** Split a citation into sentences and clauses, never at an initial or an abbreviation. */
function sentencesOf(text) {
  const out = [];
  let start = 0;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === ';') { out.push(text.slice(start, i)); start = i + 1; continue; }
    if (ch !== '.' || !/\s/.test(text[i + 1] ?? '') || !/[A-Z'"‘“(]/.test(text.slice(i + 1).trimStart()[0] ?? '')) continue;
    const word = (text.slice(start, i).match(/([A-Za-z]+)$/) ?? [])[1] ?? '';
    if (/^[A-Z]$/.test(word) || ABBREV.has(word.toLowerCase())) continue;
    out.push(text.slice(start, i));
    start = i + 1;
  }
  out.push(text.slice(start));
  return out.map((x) => x.trim()).filter(Boolean);
}

const trimTail = (x) => x.replace(/[\s,;:(\[–—-]+$/, '').replace(/\s+\($/, '').trim();

/**
 * A short human title for a source, from its own citation: always a prefix of the citation's
 * opening, never a word that is not in it. '' when nothing in it reads as a title.
 * @param {string} citation
 */
export function sourceTitle(citation) {
  const text = String(citation ?? '').replace(/\s+/g, ' ').trim();
  if (!text) return '';
  const parts = sentencesOf(text);
  let title = parts[0] ?? '';
  for (let i = 1; i < parts.length && title.length < TITLE_MIN; i++) title = `${title}. ${parts[i]}`;
  // Cut before the first word that is not for a visitor: the longest clean prefix.
  if (!clean(title)) {
    const words = title.split(' ');
    let keep = '';
    for (let i = 1; i <= words.length; i++) {
      const next = words.slice(0, i).join(' ');
      if (!clean(next)) break;
      keep = next;
    }
    title = keep;
  }
  title = trimTail(title);
  if (title.length > TITLE_MAX) {
    const cut = title.slice(0, TITLE_MAX);
    title = `${trimTail(cut.slice(0, Math.max(cut.lastIndexOf(' '), 20)))}…`;
  }
  return title.split(' ').filter((w) => /[A-Za-z]{2,}/.test(w)).length >= 2 ? title : '';
}

/** The source behind an id: the record's own joined citation first, then the summaries'
 *  resolved one. Null when neither has it — said as such, never guessed. */
export function resolveSource(id, citationsById, docSources) {
  return citationsById.get(id) ?? (docSources && typeof docSources[id] === 'object' ? docSources[id] : null);
}

function dot(grade) {
  if (!GRADES.includes(grade)) return '';
  const { label, meaning } = gradeTerm(grade);
  return `<i class="fact-dot fact-${grade}" role="img" aria-label="${escapeHtml(label)}" title="${escapeHtml(`${label}: ${meaning}`)}"></i>`;
}

function factRow(f, ctx) {
  const srcs = f.sources.map((id) => {
    const c = resolveSource(id, ctx.citationsById, ctx.docSources);
    return c ? { ...c, id } : null;
  });
  const long = f.value.length > SHORT_VALUE;
  const value = f.value && !long ? `<span class="src-value">${escapeHtml(f.value)}</span>` : '';
  const why = f.note
    ? (clean(f.note)
      ? `<p class="src-why"><span class="src-k">${escapeHtml(s('why'))}</span> ${escapeHtml(f.note)}</p>`
      : `<p class="src-why src-why-later">${escapeHtml(s('why.researchers'))}</p>`)
    : '';
  const titles = srcs.map((c) => {
    const title = c ? sourceTitle(c.citation) : '';
    const when = c ? sourceTag(c.tier, ctx.dateOf(c.id), ctx.sceneYear) : '';
    return `<li><span class="src-title">${escapeHtml(title || s('source.untitled'))}</span>${when
      ? ` <span class="src-when">${escapeHtml(when)}</span>` : ''}</li>`;
  }).join('');
  const found = srcs.filter(Boolean);
  const from = f.sources.length
    ? `<p class="src-k">${escapeHtml(s('sources.k'))}</p><ul class="src-titles">${titles}</ul>`
    : `<p class="src-none">${escapeHtml(s(f.grade === 'attested' ? 'sources.none.attested' : 'sources.none'))}</p>`;
  const cites = found.length
    ? `<details class="src-cites"><summary>${escapeHtml(s(found.length === 1 ? 'cites.one' : 'cites.many'))}</summary>
        <ol class="cites">${citationItems(found, { tier: false, evidence: false })}</ol></details>`
    : '';
  return `<li><details class="src-fact" data-grade="${escapeHtml(f.grade ?? '')}">
    <summary>${dot(f.grade)}<span class="src-label">${escapeHtml(f.label)}</span>${value}</summary>
    <div class="src-body">
      ${long ? `<p class="src-long">${escapeHtml(f.value)}</p>` : ''}
      ${why}${f.absent ? `<p class="src-absent">${escapeHtml(s('absent'))}</p>` : ''}
      ${from}${cites}
    </div>
  </details></li>`;
}

function libertyRow(lib) {
  const raw = String(lib?.title ?? '').trim();
  const title = clean(raw) ? raw.charAt(0).toUpperCase() + raw.slice(1) : s('liberty.untitled');
  const fields = list(lib?.fields)
    .filter((f) => f?.label && !LIBERTY_SKIP.test(String(f.label)))
    .map((f) => ({ label: String(f.label), text: String(f.text ?? '').replace(/\*\*/g, '').trim() }))
    .filter((f) => f.text && clean(f.text) && clean(f.label));
  const body = fields.length
    ? `<dl class="src-lib-body">${fields.map((f) => `<dt>${escapeHtml(f.label)}</dt><dd>${escapeHtml(f.text)}</dd>`).join('')}</dl>`
    : `<p class="src-why src-why-later">${escapeHtml(s('liberties.researchers'))}</p>`;
  return `<li><details class="src-lib"><summary><span class="src-label">${escapeHtml(title)}</span></summary>${body}</details></li>`;
}

function questionRow(u) {
  const q = clean(String(u?.question ?? ''));
  const change = clean(String(u?.consequence ?? ''));
  const cites = list(u?.citations);
  return `<li><details class="src-lib src-open"><summary><span class="src-label">${escapeHtml(q || s('open.lead'))}</span></summary>
    ${change ? `<dl class="src-lib-body"><dt>${escapeHtml(s('open.change'))}</dt><dd>${escapeHtml(change)}</dd></dl>` : ''}
    ${cites.length ? `<ol class="cites">${citationItems(cites, { tier: false, evidence: false })}</ol>` : ''}
  </details></li>`;
}

/**
 * The Sources tab, as HTML.
 * @param {object} o
 * @param {object|null} o.sidecar     the record's sidecar (its `citations` are the joined sources)
 * @param {object|null} o.summary     its compiled summary record, or null
 * @param {object|null} o.docSources  inspect/<scene>.json's `sources`, by id
 * @param {object[]|null} o.liberties this building's liberties; null when the list did not load
 * @param {object[]|null} o.questions this building's open questions; null when not loaded
 * @param {string|null} o.dossier     the research dossier's address, or null when none is written
 * @param {object|null} o.sourceDates inspect/<scene>.json's `source_dates`: each source's own date
 * @param {number|string|null} o.sceneYear the scene's year, which "from the time" is held to
 */
export function sourcesPaneHtml({ sidecar = null, summary = null, docSources = null, liberties = null, questions = null,
  dossier = null, sourceDates = null, sceneYear = null } = {}) {
  const facts = buildingFacts(sidecar, summary);
  const n = factCounts(facts);
  const citationsById = new Map(list(sidecar?.citations).filter((c) => c.source_id).map((c) => [c.source_id, c]));
  const dates = sourceDates && typeof sourceDates === 'object' ? sourceDates : {};
  const dateOf = (id) => docSources?.[id]?.date ?? dates[id] ?? null;
  const ctx = { citationsById, docSources, dateOf, sceneYear };
  const split = GRADES.map((g) => `${n[g]} ${gradeTerm(g).label}`).join(', ');
  const lead = `<p class="src-lead">${escapeHtml(s(n.total === 1 ? 'lead.one' : 'lead', { count: n.total, split }))}</p>`;

  const groups = GRADES.map((g) => {
    const mine = facts.filter((f) => f.grade === g);
    const { label, meaning } = gradeTerm(g);
    return `<section class="src-grade" data-grade="${g}">
      <h3 class="insp-h src-grade-h">${dot(g)}<span>${escapeHtml(label)}</span> <span class="src-count">${mine.length}</span></h3>
      <p class="nav-sub src-gloss">${escapeHtml(meaning)}</p>
      ${mine.length ? `<ul class="src-facts">${mine.map((f) => factRow(f, ctx)).join('')}</ul>`
    : `<p class="nav-sub">${escapeHtml(s('none'))}</p>`}
    </section>`;
  }).join('');
  const odd = facts.filter((f) => !GRADES.includes(f.grade));
  const offScale = odd.length
    ? `<section class="src-grade" data-grade="other"><p class="src-none">${escapeHtml(s('off-scale', { count: odd.length }))}</p>
        <ul class="src-facts">${odd.map((f) => factRow(f, ctx)).join('')}</ul></section>`
    : '';

  const libs = Array.isArray(liberties) ? liberties : null;
  const libTerm = gradeTermOf('Liberties');
  const libSec = `<section class="src-liberties">
    <h3 class="insp-h">${escapeHtml(libTerm.label)}${libs?.length ? ` <span class="src-count">${libs.length}</span>` : ''}</h3>
    <p class="nav-sub src-gloss">${escapeHtml(libTerm.meaning)}</p>
    ${libs === null ? `<p class="nav-sub">${escapeHtml(s('liberties.unread'))}</p>`
    : libs.length ? `<ul class="src-facts">${libs.map(libertyRow).join('')}</ul>`
      : `<p class="nav-sub">${escapeHtml(s('liberties.none'))}</p>`}
  </section>`;

  // An open question is shown only where there is one; silence claims nothing (popup.js
  // openQuestionSection), a reassurance would claim a lot.
  const qs = Array.isArray(questions) ? questions : [];
  const openSec = qs.length
    ? `<section class="src-liberties src-questions"><h3 class="insp-h">${escapeHtml(s('open.k'))}</h3>
        <p class="nav-sub">${escapeHtml(s('open.lead'))}</p><ul class="src-facts">${qs.map(questionRow).join('')}</ul></section>`
    : '';

  const foot = dossier
    ? `<a href="${escapeHtml(dossier)}" target="_blank" rel="noopener">${escapeHtml(s('dossier.link'))} ↗</a>`
    : escapeHtml(s('dossier.none'));
  return `<div class="src-page" data-facts="${n.total}">
    ${lead}${groups}${offScale}${libSec}${openSec}
    <p class="pop-foot src-foot">${foot}</p>
    <button type="button" class="nav-tile insp-full" data-insp-full>${escapeHtml(s('full.record'))}</button>
  </div>`;
}

/** A locked term's label and plain line (terms.js), for Liberties. */
function gradeTermOf(term) {
  const label = t(`terms.${term.toLowerCase()}`) || term;
  return { label, meaning: t(`terms.${term.toLowerCase()}.meaning`) };
}

export const _test = { sentencesOf, keyWords, valueWords };
