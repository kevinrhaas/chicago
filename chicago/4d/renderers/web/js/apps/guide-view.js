/**
 * Guide (SCR 09), loaded the first time it opens (T-2661, NAV-803; DESIGN §07 "Guide").
 *
 * The controls sheet, which replaces the control-help popover. It shows the controls the
 * visitor is actually using — touch on a phone (the left thumb walks, the right side
 * looks), keyboard and mouse on a laptop — read from the one switch that knows,
 * js/controls/intent.js (`ctx.controls`, `ctx.coarse`), and follows it when it changes:
 * a laptop with a touch screen that is tapped turns the sheet to touch. The other sheet
 * is one tap away, for a visitor who wants to read it.
 *
 * Under it (T-2662, NAV-804, design doc section 03): the glossary — the seven locked
 * terms, each with its one plain line from the string table (strings/terms.js, held equal
 * to data/guide/glossary.json by the gates) — and the questions "Is this real?" and "What
 * does Reconstructed mean?", read from data/guide/faq.json the first time Guide opens.
 * Tour mode joins with its own ticket (NAV-801).
 *
 * Last (T-2666, NAV-806, design doc section 11): For teachers, the Field Check's seven steps
 * and three suggested Jaunts for each destination as a one-page handout to print
 * (teacher-handout.js). The steps are the tour engine's own; each destination's Jaunts are
 * read from its catalog the first time Guide opens, never at boot.
 */
import { CONTROL_SHEETS, SCHEMES } from '../controls/sheet.js';
import { controlScheme } from '../controls/intent.js';
import { LOCKED_TERMS } from '../strings/terms.js';
import { t } from '../strings/index.js';
import '../strings/teachers.js';
import { STEPS } from '../tour.js';
import { DESTINATIONS } from './jump-view.js';
import { handoutModel, renderHandout, printHandout } from './teacher-handout.js';

const state = { scheme: null, chosen: false, off: null, host: null };

/** The glossary: every locked term, exactly as written, and its one line. */
function glossary(doc) {
  const block = doc.createElement('section');
  block.className = 'nav-block nav-guide-glossary';
  block.id = 'guide-glossary';
  const k = Object.assign(doc.createElement('span'), { className: 'nav-k', textContent: 'Glossary' });
  const title = Object.assign(doc.createElement('strong'), { className: 'nav-place', textContent: 'The words we use' });
  const list = Object.assign(doc.createElement('dl'), { className: 'nav-glossary' });
  for (const [term, meaning] of LOCKED_TERMS) {
    const dt = Object.assign(doc.createElement('dt'), { textContent: term });
    dt.dataset.locked = term;
    list.append(dt, ' ', Object.assign(doc.createElement('dd'), { textContent: meaning }), ' ');
  }
  block.append(k, ' ', title, ' ', list);
  return block;
}

/** The questions, each opening to its answer; filled from the FAQ file. */
function questions(doc, ctx) {
  const block = doc.createElement('section');
  block.className = 'nav-block nav-guide-faq';
  block.id = 'guide-faq';
  const k = Object.assign(doc.createElement('span'), { className: 'nav-k', textContent: 'Questions' });
  const title = Object.assign(doc.createElement('strong'), { className: 'nav-place', textContent: 'Is this real?' });
  const body = Object.assign(doc.createElement('div'), { className: 'nav-faq' });
  body.append(Object.assign(doc.createElement('p'), { className: 'nav-sub', textContent: 'Reading the answers…' }));
  block.append(k, ' ', title, ' ', body);
  Promise.resolve(ctx.actions?.guideFaq?.()).then((faq) => {
    const rows = Array.isArray(faq?.questions) ? faq.questions : [];
    if (!rows.length) throw new Error('no questions');
    body.replaceChildren(...rows.map(({ q, a }) => {
      const item = doc.createElement('details');
      item.className = 'nav-faq-item';
      const summary = Object.assign(doc.createElement('summary'), { textContent: q });
      item.append(summary, Object.assign(doc.createElement('p'), { className: 'nav-sub', textContent: a }));
      return item;
    }));
  }).catch(() => {
    body.replaceChildren(Object.assign(doc.createElement('p'), { className: 'nav-sub',
      textContent: 'The answers could not be read just now. The glossary above still says what each grade means.' }));
  });
  return block;
}

/** For teachers: the handout, shown folded here and printed on one page. */
function teachers(doc, ctx) {
  const node = (tag, cls, text) => Object.assign(doc.createElement(tag), cls ? { className: cls } : {}, text != null ? { textContent: text } : {});
  const block = node('section', 'nav-block nav-guide-teachers');
  block.id = 'guide-teachers';
  const button = node('button', 'setting-button nav-handout-print', t('teachers.print'));
  button.type = 'button';
  button.id = 'guide-handout-print';
  const fold = node('details', 'nav-faq-item nav-handout-fold');
  const summary = node('summary', null, t('teachers.preview'));
  const catalogs = {};
  // The scene the page holds (its sidecar's id, as Jump reads it), or a year given plainly.
  const scene = typeof ctx.scene === 'object' ? (ctx.scene?.id ?? ctx.scene?.target_date?.slice(0, 4)) : ctx.scene;
  const draw = () => renderHandout(doc, handoutModel({ steps: STEPS, scene, destinations: DESTINATIONS, catalogs }));
  let handout = draw();
  fold.append(summary, handout);
  block.append(node('span', 'nav-k', t('teachers.k')), ' ', node('strong', 'nav-place', t('teachers.title')), ' ',
    node('p', 'nav-sub', t('teachers.intro')), ' ', button, ' ', fold);
  const ready = Promise.all(DESTINATIONS.map((d) => Promise.resolve()
    .then(() => ctx.actions?.jauntCatalog?.(d.year))
    .then((rows) => { catalogs[d.year] = Array.isArray(rows) ? rows : null; }, () => { catalogs[d.year] = null; })))
    .then(() => {
      const next = draw();
      fold.replaceChildren(summary, next);
      handout = next;
    });
  button.addEventListener('click', () => { ready.then(() => printHandout(handout, { doc })); });
  return block;
}

function render(el) {
  const doc = el.ownerDocument;
  const node = (tag, cls, text) => {
    const n = doc.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const sheet = CONTROL_SHEETS[state.scheme];
  const block = node('section', 'nav-block nav-guide');
  block.id = 'guide-controls';
  block.dataset.scheme = state.scheme;
  const k = node('span', 'nav-k nav-k-row');
  k.append(node('span', null, 'Guide'), ' ',
    node('span', 'nav-step', state.chosen ? 'Your choice' : 'On this device'));
  const title = node('strong', 'nav-place', 'The controls');
  const seg = node('div', 'seg nav-guide-seg');
  seg.id = 'guide-scheme';
  seg.setAttribute('role', 'radiogroup');
  seg.setAttribute('aria-label', 'Controls for');
  for (const id of SCHEMES) {
    const b = node('button', 'seg-btn', CONTROL_SHEETS[id].title);
    b.type = 'button';
    b.dataset.scheme = id;
    b.setAttribute('role', 'radio');
    b.setAttribute('aria-checked', String(id === state.scheme));
    b.classList.toggle('is-on', id === state.scheme);
    b.addEventListener('click', () => {
      if (state.scheme === id) return;
      state.scheme = id;
      state.chosen = true;
      render(el);
    });
    seg.append(b);
  }
  const intro = node('p', 'nav-sub', sheet.intro);
  const list = node('dl', 'keys nav-guide-keys');
  list.dataset.scheme = state.scheme;
  for (const [keys, does] of sheet.rows) {
    const dt = node('dt');
    keys.forEach((key, i) => {
      if (i) dt.append(' ');
      // Keyboard keys are keys; a touch gesture is words.
      dt.append(state.scheme === 'keyboard' ? node('kbd', null, key) : node('span', null, key));
    });
    list.append(dt, ' ', node('dd', null, does), ' ');
  }
  block.append(k, ' ', title, ' ', seg, ' ', intro, ' ', list);
  el.replaceChildren(block);
}

export function mount(el, ctx = {}) {
  state.scheme = controlScheme(ctx.controls, ctx.coarse);
  state.chosen = false;
  const doc = el.ownerDocument;
  state.host = doc.createElement('div');
  state.host.className = 'nav-guide-controls';
  el.replaceChildren(state.host, glossary(doc), questions(doc, ctx), teachers(doc, ctx));
  render(state.host);
  state.off?.();
  // Follow the live controls until the visitor picks a sheet themselves.
  state.off = ctx.actions?.onControls?.((name) => {
    const next = controlScheme(name, ctx.coarse);
    if (state.chosen || next === state.scheme) return;
    state.scheme = next;
    render(state.host);
  }) ?? null;
}

/** Each time Guide opens: the sheet for the controls in use, unless one was picked. */
export function shown(el, ctx = {}) {
  if (state.chosen) return;
  const next = controlScheme(ctx.controls, ctx.coarse);
  if (next !== state.scheme && state.host) { state.scheme = next; render(state.host); }
}

export function unmount(el) {
  state.off?.();
  state.off = null;
  state.host = null;
  el.replaceChildren();
}
