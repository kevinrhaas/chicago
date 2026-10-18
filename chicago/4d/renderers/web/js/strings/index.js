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
 * T-2668 — Researcher mode's strings. A string only Researcher mode (T-2657) shows — the
 * order book, a source id, a file path, a full "Why this default" essay — lives under a key
 * with a `researcher` segment: the `researcher` namespace, or `researcher` inside an app's
 * own section (`guide.researcher.why-full`). The visitor-UI lint (tools/check_visitor_ui.py)
 * exempts exactly those keys, so a caller shows one only while Researcher mode is on; on a
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
  const value = dot > 0 ? sections.get(key.slice(0, dot))?.[key.slice(dot + 1)] : undefined;
  if (typeof value !== 'string') return fallback;
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
