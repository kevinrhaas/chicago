/**
 * Browser-only teacher lessons. Catalogs group the same way as the Jaunts menu. Opening
 * a lesson reads ONE compiled jaunt, whose citations and evidence remain authoritative.
 * No new historical prose or sources are inferred from a title. The curriculum prompts
 * are ours; each displayed claim is explicitly the project's evidence summary.
 */
import { GROUPS, groupOf } from '../menu-icons.js';
import { t } from '../strings/index.js';
import '../strings/lessons.js';

export const LESSON_BANDS = ['3-5', '6-8', '9-10', '11-12', 'K-2'];
export const ILLINOIS_STANDARDS = 'https://www.isbe.net/Documents/IL-Social-Science-Standards.pdf';
export const C3_FRAMEWORK = 'https://www.socialstudies.org/standards/c3';
// Illinois revised standards, p. 10 (retrieved 2026-11-18). Short descriptions are
// paraphrases of the standards, not quotations. The task is a suggested alignment.
export const ALIGNMENTS = Object.freeze({
  'K-2': [['SS.K-2.IS.3', 'Gather relevant information from multiple sources with guidance.'],
    ['SS.K-2.IS.4', 'Distinguish fact and opinion when evaluating a source.']],
  '3-5': [['SS.3-5.IS.4', 'Gather relevant information and assess source credibility.'],
    ['SS.3-5.IS.5', 'Develop claims using evidence from multiple sources.']],
  '6-8': [['SS.6-8.IS.2.MdC', 'Assess source credibility through origin, authority and context.'],
    ['SS.6-8.IS.3.MdC', 'Support claims with evidence and identify its limitations.']],
  '9-10': [['SS.9-12.IS.5', 'Evaluate primary and secondary sources, including perspectives of marginalized groups.'],
    ['SS.9-12.IS.7', 'Construct evidence-based arguments that acknowledge counterclaims, perspectives and biases.']],
  '11-12': [['SS.9-12.IS.5', 'Evaluate primary and secondary sources, including perspectives of marginalized groups.'],
    ['SS.9-12.IS.7', 'Construct evidence-based arguments that acknowledge counterclaims, perspectives and biases.']],
});

export function safeSourceURL(value) {
  try { const u = new URL(value); return ['https:', 'http:'].includes(u.protocol) ? u.href : ''; }
  catch { return ''; }
}
export function lessonGroups(rows = []) {
  const present = new Set(rows.filter(r => r && r.availability === 'available' && r.audience !== 'adults').map(groupOf));
  return [...GROUPS, ...[...present].filter(g => g && !GROUPS.includes(g)).sort()].filter(g => present.has(g));
}
export function lessonJaunts(rows = [], group, band) {
  return rows.filter(r => r && r.availability === 'available' && r.audience !== 'adults'
    && groupOf(r) === group && r.grade_band === band)
    .sort((a, b) => (b.featured === true) - (a.featured === true)
      || (a.stop_count ?? Infinity) - (b.stop_count ?? Infinity)
      || String(a.title).localeCompare(String(b.title)) || a.id.localeCompare(b.id));
}

/** Up to three cited documents, preferring period evidence. A citation only qualifies
 * when a nonempty evidence statement cites it; orphan citations are not lesson material.
 * At most two claims per document keeps a printed guide usable and bounded. */
export function lessonDocuments(jaunt) {
  const claims = (jaunt?.evidence ?? []).filter(e => e && typeof e.text === 'string' && e.text.trim() && Array.isArray(e.sources));
  const seen = new Set();
  const docs = (jaunt?.citations ?? []).filter(c => {
    if (!c?.source_id || !c.citation || seen.has(c.source_id) || !claims.some(e => e.sources.includes(c.source_id))) return false;
    seen.add(c.source_id); return true;
  }).map(c => ({
    id: c.source_id, citation: c.citation, tier: c.tier,
    url: safeSourceURL(c.url), archive: safeSourceURL(c.archived_url),
    claims: claims.filter(e => e.sources.includes(c.source_id)).slice(0, 2).map(e => ({
      text: e.text, locator: typeof e.locator === 'string' ? e.locator : '',
      confidence: ['attested', 'inferred', 'reconstructed', 'conjectural'].includes(e.confidence) ? e.confidence : '',
    })),
  }));
  const rank = d => [1, 2].includes(d.tier) ? d.tier : 3;
  docs.sort((a, b) => rank(a) - rank(b) || Number(!!(b.url || b.archive)) - Number(!!(a.url || a.archive))
    || a.citation.localeCompare(b.citation));
  return docs.slice(0, 3);
}

export function lessonModel({ year, group, band, row, jaunt }) {
  if (!row || row.availability !== 'available' || !jaunt || row.id !== jaunt.id
      || String(jaunt.scene) !== String(year) || groupOf(row) !== group || row.grade_band !== band || row.audience === 'adults') {
    throw new Error('Lesson does not match the selected outing');
  }
  const documents = lessonDocuments(jaunt);
  return {
    year: String(year), group, band, title: jaunt.title, premise: jaunt.premise,
    question: t(`lessons.question.${GROUPS.includes(group) ? group : 'other'}`, { year }),
    documents, hasLinkedPrimary: documents.some(d => [1, 2].includes(d.tier) && (d.url || d.archive)),
    standards: ALIGNMENTS[band] ?? [], contentWarning: row.content_warning || jaunt.content_warning || '',
  };
}

const make = (doc, tag, text, cls) => Object.assign(doc.createElement(tag), text == null ? {} : { textContent: text }, cls ? { className: cls } : {});
function link(doc, label, href) {
  const a = make(doc, 'a', label); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a;
}
function list(doc, tag, texts) {
  const root = doc.createElement(tag); for (const text of texts) root.append(make(doc, 'li', text)); return root;
}

export function renderLesson(doc, model) {
  const n = (tag, text, cls) => make(doc, tag, text, cls);
  const root = n('article', null, 'lesson-guide');
  root.dataset.lesson = `${model.year}:${model.group}:${model.band}`;
  const section = (title, ...nodes) => { const s = n('section'); s.append(n('h4', t(`lessons.${title}`)), ...nodes); root.append(s); };
  root.append(n('h3', `${model.group} · ${model.year}`), n('p', `Grades ${model.band} · ${model.title}`, 'lesson-subtitle'),
    n('p', t('lessons.duration')));
  if (model.contentWarning) root.append(n('p', model.contentWarning, 'lesson-warning'));
  section('question', n('p', model.question, 'lesson-question'));
  section('goal', n('p', t('lessons.goal.text')));
  section('route', n('p', model.premise));
  section('sequence', list(doc, 'ol', ['before', 'during', 'read', 'after'].map(k => t(`lessons.sequence.${k}`))));
  const documents = n('div', null, 'lesson-documents');
  documents.append(n('p', t('lessons.context')));
  if (!model.documents.length) documents.append(n('p', t('lessons.noEvidence')));
  else if (!model.hasLinkedPrimary) documents.append(n('p', t('lessons.noPrimary'), 'lesson-warning'));
  for (const [i, d] of model.documents.entries()) {
    const item = n('section', null, 'lesson-document');
    item.append(n('h5', `${i + 1}. ${d.citation}`), n('p', t(`lessons.${d.tier === 1 ? 'period' : d.tier === 2 ? 'later' : d.tier ? 'secondary' : 'unknown'}`)));
    const links = n('p', null, 'lesson-source-links');
    if (d.url) links.append(link(doc, t('lessons.original'), d.url));
    if (d.archive) { if (d.url) links.append(' · '); links.append(link(doc, t('lessons.archive'), d.archive)); }
    if (!d.url && !d.archive) links.append(t('lessons.noLink'));
    item.append(links, n('p', t('lessons.evidence'), 'lesson-evidence-label'));
    for (const c of d.claims) {
      const claim = n('div', null, 'lesson-claim');
      claim.append(n('p', c.text));
      if (c.locator) claim.append(n('p', t('lessons.locator', { locator: c.locator })));
      if (c.confidence) claim.append(n('p', t('lessons.gradeLine', { grade: c.confidence[0].toUpperCase() + c.confidence.slice(1) })));
      item.append(claim);
    }
    documents.append(item);
  }
  section('documents', documents);
  section('discussion', list(doc, 'ul', [1, 2, 3].map(k => t(`lessons.discussion.${k}`))));
  section('response', n('p', t('lessons.response.text'), 'lesson-response'));
  section('assess', n('p', t('lessons.assess.text')));
  section('adapt', n('p', t(`lessons.adapt.${model.band}`)));
  section('standards', n('p', t('lessons.standardsNote')), link(doc, t('lessons.illinois'), ILLINOIS_STANDARDS),
    list(doc, 'ul', model.standards.map(([code, description]) => `${code}: ${description}`)),
    link(doc, t('lessons.c3'), C3_FRAMEWORK), n('p', t('lessons.c3Note')));
  root.append(n('p', t('lessons.footer'), 'lesson-footer'));
  return root;
}

const printCleanups = new WeakMap();
export function printLesson(lesson, { doc = lesson?.ownerDocument, win = doc?.defaultView } = {}) {
  if (!lesson || !doc?.body || !win?.print) return false;
  printCleanups.get(doc)?.();
  doc.getElementById('lesson-print')?.remove();
  const copy = make(doc, 'div', null, 'lesson-print'); copy.id = 'lesson-print'; copy.append(lesson.cloneNode(true));
  doc.body.append(copy); doc.documentElement.classList.add('is-printing-lesson');
  const done = () => {
    copy.remove(); doc.documentElement.classList.remove('is-printing-lesson');
    win.removeEventListener?.('afterprint', done);
    printCleanups.delete(doc);
  };
  printCleanups.set(doc, done);
  win.addEventListener?.('afterprint', done);
  try { win.print(); } catch { done(); return false; }
  return true;
}

/** Catalogs are supplied by the existing handout request; no extra read at boot. */
export function createLessonGuides(doc, ctx, { catalogs, ready, destinations }) {
  const n = (tag, text, cls) => make(doc, tag, text, cls);
  const root = n('section', null, 'nav-lessons'); root.id = 'guide-lessons';
  root.append(n('h3', t('lessons.title')), n('p', t('lessons.intro'), 'nav-sub'));
  const open = n('button', t('lessons.open'), 'setting-button'); open.type = 'button';
  const content = n('div'); content.hidden = true; content.id = 'guide-lessons-content';
  open.setAttribute('aria-expanded', 'false'); open.setAttribute('aria-controls', content.id);
  const status = n('p'); status.setAttribute('role', 'status');
  root.append(open, status, content);
  let opened = false;
  open.addEventListener('click', async () => {
    if (opened) { content.hidden = !content.hidden; open.setAttribute('aria-expanded', String(!content.hidden)); return; }
    opened = true; open.disabled = true; status.textContent = t('lessons.reading');
    try { await ready; } catch { /* each catalog reports its own error below */ }
    const cssId = 'lesson-guides-style';
    if (!doc.getElementById(cssId)) {
      const css = n('link'); css.id = cssId; css.rel = 'stylesheet'; css.href = new URL('../../css/lessons.css', import.meta.url).href; doc.head?.append(css);
    }
    open.disabled = false; content.hidden = false; open.setAttribute('aria-expanded', 'true'); status.textContent = '';
    const controls = n('div', null, 'lesson-controls'), preview = n('div', null, 'lesson-preview');
    preview.setAttribute('aria-label', t('lessons.preview'));
    const select = (key) => {
      const label = n('label', t(`lessons.${key}`));
      const s = n('select'); s.setAttribute('aria-label', t(`lessons.${key}`)); s.dataset.lessonSelect = key;
      label.append(s); controls.append(label); return s;
    };
    const year = select('year'), group = select('group'), band = select('grade'), jaunt = select('jaunt');
    const option = (s, value, label) => { const o = n('option', label); o.value = value; s.append(o); };
    for (const d of destinations) option(year, String(d.year), String(d.year));
    const here = typeof ctx.scene === 'object' ? ctx.scene.id : ctx.scene;
    if (destinations.some(d => String(d.year) === String(here))) year.value = String(here);
    for (const b of LESSON_BANDS) option(band, b, `Grades ${b}`); band.value = '9-10';
    const prepare = n('button', t('lessons.prepare'), 'setting-button'); prepare.type = 'button';
    const print = n('button', t('lessons.print'), 'setting-button'); print.type = 'button'; print.hidden = true;
    let revision = 0, lesson = null;
    const invalidate = () => { revision++; lesson = null; preview.replaceChildren(); print.hidden = true; };
    const rows = () => catalogs[year.value];
    const refreshJaunts = () => {
      invalidate(); jaunt.replaceChildren();
      const choices = lessonJaunts(rows() ?? [], group.value, band.value);
      for (const r of choices) option(jaunt, r.id, r.title);
      prepare.disabled = !choices.length;
      status.textContent = !Array.isArray(rows()) ? t('lessons.error') : !rows().length ? t('lessons.noCatalog')
        : choices.length ? '' : t('lessons.noBand');
    };
    const refreshGroups = () => {
      group.replaceChildren(); for (const g of lessonGroups(rows() ?? [])) option(group, g, g); refreshJaunts();
    };
    year.addEventListener('change', refreshGroups); group.addEventListener('change', refreshJaunts);
    band.addEventListener('change', refreshJaunts); jaunt.addEventListener('change', () => { invalidate(); prepare.disabled = !jaunt.value; status.textContent = ''; });
    prepare.addEventListener('click', async () => {
      const request = ++revision, selectedYear = year.value, selectedGroup = group.value, selectedBand = band.value;
      const row = (rows() ?? []).find(r => r.id === jaunt.value);
      prepare.disabled = true; print.hidden = true; preview.replaceChildren(); status.textContent = t('lessons.reading');
      try {
        const document = await ctx.actions?.jauntDocument?.(selectedYear, row?.id);
        if (request !== revision) return;
        const model = lessonModel({ year: selectedYear, group: selectedGroup, band: selectedBand, row, jaunt: document });
        lesson = renderLesson(doc, model); preview.append(lesson); print.hidden = false; status.textContent = '';
        lesson.tabIndex = -1; lesson.focus?.({ preventScroll: true });
      } catch {
        if (request === revision) status.textContent = t('lessons.error');
      } finally { if (request === revision) prepare.disabled = false; }
    });
    print.addEventListener('click', () => printLesson(lesson, { doc }));
    const retry = n('button', t('lessons.retry'), 'setting-button'); retry.type = 'button';
    retry.addEventListener('click', async () => {
      invalidate(); retry.disabled = true; prepare.disabled = true; status.textContent = t('lessons.reading');
      const selectedYear = year.value;
      try {
        const result = await ctx.actions?.jauntCatalog?.(selectedYear);
        catalogs[selectedYear] = Array.isArray(result) ? result : null;
      } catch { catalogs[selectedYear] = null; }
      finally { retry.disabled = false; refreshGroups(); }
    });
    content.append(controls, prepare, ' ', print, ' ', retry, preview); refreshGroups();
  });
  return root;
}
