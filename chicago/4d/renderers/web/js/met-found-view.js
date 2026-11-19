/**
 * met-found-view.js — the one row People and the Map show for T-3673: a toggle with its
 * count ("Met 3 of 445", "Found 4 of 92 places"), Clear <year> with an inline Clear / Keep
 * confirm, and a status line for what the store says (not saving, a saved copy that could
 * not be read, full). Plain DOM calls only (append, hidden, textContent, setAttribute,
 * addEventListener), so the Navigator's fake pages in tools/ can drive it.
 */
import { t } from './strings/index.js';
import './strings/met-found.js';
import { metFound } from './met-found.js';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
/** '2026-11-19' → '19 November 2026'. */
export function dayWords(day) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(day ?? ''));
  return m && MONTHS[Number(m[2]) - 1] ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}` : '';
}

/**
 * @param {Document} doc
 * @param {object} o
 * @param {string} o.year
 * @param {string} o.cls            a class for the row ('ppl-met' / 'nav-map-found')
 * @param {string} o.toggleCls      the toggle's classes
 * @param {() => string} o.text     the toggle's words now
 * @param {string} o.title
 * @param {() => boolean} o.pressed
 * @param {() => void} o.onToggle
 */
export function metFoundRow(doc, { year, cls, toggleCls, text, title, pressed, onToggle, store = metFound }) {
  const make = (tag, c, words) => { const e = doc.createElement(tag); if (c) e.className = c; if (words != null) e.textContent = words; return e; };
  const button = (c, words) => { const b = make('button', c, words); b.type = 'button'; return b; };
  const row = make('div', `mf-row ${cls}`);
  const toggle = button(toggleCls);
  toggle.title = title;
  const clear = button('mf-clear', t('metfound.clear', { year }));
  clear.title = t('metfound.clear.title', { year });
  const ask = make('div', 'mf-ask');
  ask.setAttribute('role', 'group');
  ask.hidden = true;
  const askText = make('span', 'mf-ask-text');
  const yes = button('mf-yes', t('metfound.clear.yes'));
  const no = button('mf-no', t('metfound.clear.no'));
  ask.append(askText, yes, no);
  const status = make('p', 'mf-status');
  status.setAttribute('role', 'status');
  row.append(toggle, clear, ask, status);
  let said = '';
  let resetting = false;

  function paint() {
    const error = store.error;
    toggle.textContent = text();
    toggle.setAttribute('aria-pressed', String(!!pressed()));
    clear.textContent = error === 'damaged' ? t('metfound.reset') : t('metfound.clear', { year });
    status.textContent = said || (error ? t(`metfound.error.${error}`) : t('metfound.privacy'));
    status.className = `mf-status${error && !said ? ' is-problem' : ''}`;
  }
  toggle.addEventListener('click', () => { said = ''; onToggle(); paint(); });
  clear.addEventListener('click', () => {
    resetting = store.error === 'damaged';
    askText.textContent = resetting ? t('metfound.reset.ask') : t('metfound.clear.ask', { year });
    ask.hidden = false;
    clear.hidden = true;
    no.focus?.();
  });
  const done = () => { ask.hidden = true; clear.hidden = false; clear.focus?.(); };
  no.addEventListener('click', () => { done(); paint(); });
  yes.addEventListener('click', () => {
    const r = resetting ? store.reset() : store.clearYear(year);
    said = r.ok ? t('metfound.clear.done', { year }) : t(`metfound.error.${r.reason ?? 'storage'}`);
    done();
    paint();
  });
  ask.addEventListener('keydown', (e) => { if (e.key === 'Escape') { e.preventDefault?.(); e.stopPropagation?.(); done(); paint(); } });
  paint();
  return { el: row, paint, toggle, clear, ask, yes, no, status, quiet() { said = ''; } };
}
