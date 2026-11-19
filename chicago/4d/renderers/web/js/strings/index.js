/**
 * T-2624 — the Navigator string table (design doc "Field Navigator Mk II", section 03).
 *
 * Every string a visitor reads on the arrival, the HUD and the Navigator comes from here,
 * so the voice rules, the locked terms and the renamed terms are kept in one place and
 * held by one gate (tools/check_strings.mjs). It is a TABLE OF SECTIONS, not a monolith:
 * each app owns one file under js/strings/ that registers its own namespace —
 *
 *   // js/strings/jaunts.js
 *   import { register } from './index.js';
 *   export default register('jaunts', { 'menu.title': 'Jaunts', … });
 *
 * — and imports it beside its code. A later lane (Jaunts, Inspect, Move, Settings, Guide)
 * adds a file; it never edits another app's section, and the gate finds every file in
 * this directory on its own.
 *
 *   t('hud.tab.sources')                    → 'Sources'
 *   t('arrival.stalled', { year: 1950 })    → 'The jump stalled somewhere around 1950.'
 *   applyStrings(root)                      → fills [data-str], [data-str-title],
 *                                             [data-str-label] under root from the table
 *
 * A key that does not resolve returns the caller's fallback, or '' — never the key, which
 * would put an id in front of a visitor.
 */

const sections = new Map();

/**
 * The visitor's language (gap analysis item 15: Spanish). English is the table above and below;
 * another language is a set of locale sections under js/strings/<code>/, keyed exactly as the
 * English ones, loaded only when that language is chosen, so an English visitor never fetches
 * a byte of it. t() reads the locale first and falls back to English key by key, so a string
 * not yet translated still reads, in English, never as its key. A locale file holds data
 * only (no import of this module, which would deadlock under the await below).
 *
 * The choice is `chicago.lang` in localStorage (Settings › Display › Language), or `?lang=es`
 * on the address, which also keeps it; with neither, a browser set to Spanish starts in Spanish.
 * Changing it reloads the page: every panel paints once in the language in force.
 */
export const LANGUAGES = Object.freeze([['en', 'English'], ['es', 'Español']]);
export const LANG_KEY = 'chicago.lang';
const LOCALES = new Set(LANGUAGES.map(([code]) => code));
function readLang() {
  const g = globalThis;
  let code = '';
  try {
    const asked = new URLSearchParams(g.location?.search || '').get('lang');
    if (asked && LOCALES.has(asked)) { code = asked; g.localStorage?.setItem(LANG_KEY, asked); }
    code ||= g.localStorage?.getItem(LANG_KEY) || '';
  } catch { /* private mode, or no window: the browser's own language decides */ }
  if (!LOCALES.has(code)) code = /^es\b/i.test(g.navigator?.language || '') && g.document ? 'es' : 'en';
  return code;
}
export const LANG = readLang();
const locale = new Map();
/** Text the page or a module writes in English, whole, mapped to this language's words; and
 * the same for patterns with {placeholders} (js/i18n-dom.js applies both to the live page). */
export const localeText = new Map();
export const localePatterns = [];
if (LANG !== 'en') {
  try {
    const pack = (await import(`./${LANG}/index.js`)).default;
    for (const [ns, table] of Object.entries(pack.sections || {})) locale.set(ns, table);
    for (const [en, tr] of Object.entries(pack.text || {})) localeText.set(en, tr);
    localePatterns.push(...(pack.patterns || []));
  } catch (e) { console.warn('[strings] the', LANG, 'strings did not load; reading English', e); }
  if (globalThis.document?.documentElement) {
    globalThis.document.documentElement.lang = LANG;
    import('../i18n-dom.js').then((m) => m.start()).catch(() => {});
  }
}
/** Set the language and reload (Settings › Display › Language). */
export function chooseLanguage(code) {
  if (!LOCALES.has(code) || code === LANG) return;
  try { globalThis.localStorage?.setItem(LANG_KEY, code); } catch { /* private mode */ }
  try {
    const url = new URL(globalThis.location.href);
    url.searchParams.delete('lang');
    globalThis.location.replace(url.href);
  } catch { globalThis.location?.reload(); }
}

/**
 * T-2668 — Researcher mode's strings. A string only Researcher mode (T-2657) shows — the
 * order book, a full "Why this default" essay — lives under a key with a `researcher`
 * segment: the `researcher` namespace, or `researcher` inside an app's own section
 * (`guide.researcher.why-full`). The lints read those keys too, and allow them only the words
 * "order book" and sentences past 20 words: no ticket number, record id or file path in any
 * mode (owner, 2026-10-18). A caller shows such a string only while Researcher mode is on; on a
 * static page the marker is a `data-researcher` attribute, hidden by css/skins.css until
 * <html data-researcher-mode> is set.
 */
export const RESEARCHER = 'researcher';
export function isResearcherKey(key) {
  return String(key ?? '').split('.').includes(RESEARCHER);
}

/** Register (or extend) a namespace. Keys are dotted within it; values are strings,
 * with {name} placeholders filled by t(). Returns the frozen section. */
export function register(namespace, table) {
  if (!/^[a-z][a-z0-9-]*$/.test(namespace)) throw new Error(`string namespace ${namespace}`);
  const merged = { ...(sections.get(namespace) || {}), ...table };
  for (const [k, v] of Object.entries(merged)) {
    if (typeof v !== 'string') throw new Error(`string ${namespace}.${k} is not a string`);
  }
  const frozen = Object.freeze(merged);
  sections.set(namespace, frozen);
  return frozen;
}

/** The string at `namespace.key`, with {placeholders} filled from `vars`. */
export function t(key, vars = null, fallback = '') {
  const dot = String(key).indexOf('.');
  const ns = dot > 0 ? key.slice(0, dot) : '';
  const local = ns && locale.get(ns)?.[key.slice(dot + 1)];
  const value = typeof local === 'string' && local ? local : ns ? sections.get(ns)?.[key.slice(dot + 1)] : undefined;
  if (typeof value !== 'string') return typeof fallback === 'string' && fallback ? (localeText.get(fallback) ?? fallback) : fallback;
  return vars ? value.replace(/\{(\w+)\}/g, (m, name) => (vars[name] ?? m)) : value;
}

export function has(key) {
  const dot = String(key).indexOf('.');
  return dot > 0 && typeof sections.get(key.slice(0, dot))?.[key.slice(dot + 1)] === 'string';
}

/** Every registered string, as [`namespace.key`, value] — what the gate reads. */
export function entries() {
  return [...sections].flatMap(([ns, table]) => Object.entries(table).map(([k, v]) => [`${ns}.${k}`, v]));
}

const ATTRS = [['str', null], ['strTitle', 'title'], ['strLabel', 'aria-label']];
/** Fill the static page from the table: an element's [data-str] sets its text, and
 * [data-str-title] / [data-str-label] its title and aria-label. The markup keeps the same
 * words as its first paint (the gate holds them equal), so nothing flashes. */
export function applyStrings(root = globalThis.document) {
  if (!root?.querySelectorAll) return 0;
  let n = 0;
  for (const el of root.querySelectorAll('[data-str], [data-str-title], [data-str-label]')) {
    for (const [key, attr] of ATTRS) {
      const id = el.dataset?.[key];
      if (!id || !has(id)) continue;
      const value = t(id);
      if (attr) { if (el.getAttribute(attr) !== value) el.setAttribute(attr, value); } else if (el.textContent !== value) el.textContent = value;
      n++;
    }
  }
  return n;
}
