/**
 * Guide › For teachers: the teacher handout (T-2666, NAV-806; design doc section 11,
 * "Teacher mode ... shows the same 7 steps as a printable one-page handout").
 *
 * One page a teacher prints for a class: the Field Check's eight steps, read from the tour
 * engine's own STEPS (js/tour.js) and never copied, and three suggested Jaunts for each
 * destination, read from that destination's compiled Jaunt catalog. The suggestion is one
 * stated rule, printed on the page and pinned by tools/test_teacher_handout.mjs:
 *
 *   only Jaunts a visitor can take (not marked unavailable), the featured ones first, then
 *   the fewest stops, then the title A to Z; the first three.
 *
 * A destination with no Jaunts says so; one whose catalog could not be read says that.
 *
 * Printing is the browser's own (window.print) through a print stylesheet, css/handout.css:
 * the handout is copied to a top-level element for the print, everything else on the page
 * is left out of it, and the copy goes when the print dialog closes (afterprint). The page
 * is sized to one sheet at Letter and at A4; the smoke (part 12) prints it to both.
 */
import { t } from '../strings/index.js';
import '../strings/teachers.js';
import { scenePresentation } from '../scene-presentation.js';

export const SUGGESTED = 3;
export const PRINT_ID = 'handout-print';
export const PRINT_CLASS = 'is-printing-handout';

/** The suggested Jaunts from one catalog, by the rule above. */
export function suggestJaunts(rows, n = SUGGESTED) {
  const list = (Array.isArray(rows) ? rows : []).filter((r) => r && r.title && r.availability !== 'unavailable');
  const stops = (r) => (Number.isFinite(r.stop_count) ? r.stop_count : Infinity);
  return list.slice().sort((a, b) => (b.featured === true) - (a.featured === true)
    || stops(a) - stops(b)
    || String(a.title).localeCompare(String(b.title), 'en')).slice(0, n);
}

/** What the handout says, as plain data. `catalogs[year]` is that destination's rows, null
 * when its catalog could not be read, or undefined while it is still being read. */
export function handoutModel({ steps = [], scene, destinations = [], catalogs = {} }) {
  const here = String(scene ?? '');
  return {
    steps: steps.map((s, i) => ({
      n: String(i + 1).padStart(2, '0'),
      task: s.task,
      // The building in front of the student is not known on paper: step 04 names the
      // Glessner House in 1904, and "the building in front of you" elsewhere.
      bubble: typeof s.bubble === 'function' ? s.bubble({ scene: here, front: null }) : String(s.bubble ?? ''),
    })),
    destinations: destinations.map((d) => {
      const rows = catalogs[d.year];
      return {
        year: d.year,
        place: scenePresentation(d.year, d.date).place,
        here: String(d.year) === here,
        state: rows === undefined ? 'reading' : rows === null ? 'unread' : 'read',
        jaunts: suggestJaunts(rows).map((r) => ({ title: r.title, stops: r.stop_count, premise: r.premise ?? '' })),
      };
    }),
  };
}

/** Draw the handout. No ids inside it but its own, so the print copy can carry it whole. */
export function renderHandout(doc, model) {
  const node = (tag, cls, text) => {
    const n = doc.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const root = node('div', 'handout');
  root.id = 'guide-handout';
  const head = node('header', 'handout-head');
  head.append(node('h3', 'handout-title', t('teachers.handout.title')), ' ',
    node('p', 'handout-lede', t('teachers.handout.lede')), ' ',
    node('p', 'handout-start', t('teachers.handout.start')));
  const steps = node('ol', 'handout-steps');
  for (const s of model.steps) {
    const li = node('li', 'handout-step');
    li.append(node('span', 'handout-n', s.n), ' ', node('strong', 'handout-task', s.task), ' ',
      node('span', 'handout-bubble', s.bubble));
    steps.append(li);
  }
  const dests = node('div', 'handout-dests');
  for (const d of model.destinations) {
    const sec = node('section', 'handout-dest');
    sec.dataset.year = String(d.year);
    if (d.here) sec.dataset.here = 'true';
    sec.append(node('h5', 'handout-dest-name', t('teachers.handout.dest', { year: d.year, place: d.place })));
    if (d.jaunts.length) {
      const list = node('ol', 'handout-jaunts');
      for (const j of d.jaunts) {
        const li = node('li', 'handout-jaunt');
        li.append(node('strong', 'handout-jaunt-title', j.title), ' ',
          node('span', 'handout-stops', t('teachers.handout.stops', { n: j.stops })));
        if (j.premise) li.append(' ', node('span', 'handout-premise', j.premise));
        list.append(li);
      }
      sec.append(' ', list);
    } else {
      const key = d.state === 'reading' ? 'reading' : d.state === 'unread' ? 'unread' : 'none';
      sec.append(' ', node('p', 'handout-empty', t(`teachers.handout.${key}`)));
    }
    dests.append(sec);
  }
  root.append(head, ' ', node('h4', 'handout-h', t('teachers.handout.steps')), ' ', steps, ' ',
    node('h4', 'handout-h', t('teachers.handout.jaunts')), ' ',
    node('p', 'handout-rule', t('teachers.handout.rule')), ' ', dests, ' ',
    node('p', 'handout-foot', t('teachers.handout.foot')));
  return root;
}

/** Print the handout: a top-level copy that the print stylesheet keeps and everything else
 * left out, removed again once the print dialog closes. Returns the copy. */
export function printHandout(handout, { doc = handout?.ownerDocument, win = doc?.defaultView } = {}) {
  if (!handout || !doc?.body) return null;
  doc.getElementById?.(PRINT_ID)?.remove();
  const copy = doc.createElement('div');
  copy.id = PRINT_ID;
  copy.className = 'handout-print';
  const inner = handout.cloneNode(true);
  inner.removeAttribute?.('id');
  copy.append(inner);
  doc.body.append(copy);
  doc.documentElement?.classList.add(PRINT_CLASS);
  const done = () => {
    win?.removeEventListener?.('afterprint', done);
    copy.remove();
    if (!doc.getElementById?.(PRINT_ID)) doc.documentElement?.classList.remove(PRINT_CLASS);
  };
  win?.addEventListener?.('afterprint', done);
  try { win?.print?.(); } catch { done(); }
  return copy;
}
