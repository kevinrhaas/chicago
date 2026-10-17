/**
 * T-2735 — the way home. Every route back to the Observatory (the arrival card's
 * "← All destinations", the Jump app's Recall key, the stalled jump's Back to the
 * Observatory) comes through here instead of being a bare link:
 *
 *   ask(href)     a small prompt in the machine's voice, CANCEL and RETURN. Esc, a tap
 *                 outside the card or CANCEL leaves the scene exactly as it was.
 *   depart(href)  the reverse ring: the outbound transfer's rings run backwards (wide and
 *                 faint, closing to the centre), the lamps light Arrive › Lock › Scan and the
 *                 year readout rolls forward to the present, then the page goes. The recall
 *                 stamp is written as it goes, so the Observatory opens on the ring's last
 *                 contraction (skin.js, `chicago4d.recall`), as T-2615 does on the way out.
 *
 * The journey moves to `recall` only as the page leaves (`onReturn`), because `recall` has
 * no way out: a cancelled prompt or an aborted ring must leave the journey where it was.
 * Reduced motion keeps the prompt and skips the ring.
 *
 * Loaded by index.html as its own module ahead of main.js, so the arrival card's link asks
 * even before the town's modules have arrived; main.js imports the same instance.
 */
import { t } from './strings/index.js';
import './strings/recall.js';

export const RECALL_MS = 1100;
export const RECALL_KEY = 'chicago4d.recall';

/** The destination year the page is in, from its path (/4d/1904/) or ?year=. */
export function pageYear(loc = globalThis.location) {
  if (!loc) return null;
  const fromPath = (String(loc.pathname || '').match(/\/(\d{4})\/?(?:index\.html)?$/) || [])[1];
  let fromQuery = null;
  try { fromQuery = new URLSearchParams(loc.search || '').get('year'); } catch { /* no query */ }
  const y = /^\d{4}$/.test(fromQuery || '') ? fromQuery : fromPath;
  return y || null;
}

const plainClick = (e) => !(e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey);

export function createRecall({
  doc = globalThis.document,
  win = doc?.defaultView ?? globalThis,
  year = pageYear(),
  reduced = () => globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false,
  go = (href) => globalThis.location?.assign(href),
  wait = (fn, ms) => setTimeout(fn, ms),
  cancel = (id) => clearTimeout(id),
  storage = (() => { try { return globalThis.sessionStorage; } catch { return null; } })(),
  now = () => Date.now(),
  frame = (fn) => (globalThis.requestAnimationFrame ? globalThis.requestAnimationFrame(fn) : wait(fn, 16)),
  present = new Date().getFullYear(),
} = {}) {
  const hooks = new Set();
  let prompt = null;    // { el, href, back, keys: [no, yes] }
  let ring = null;      // { el, timers }

  // While the prompt or the ring is up it owns the keyboard: Esc is a no (or an abort),
  // Tab stays on the prompt's two keys, and nothing reaches the walk controls, the arrival
  // card or the Navigator underneath. The arrival card's own window-capture handler stops
  // every key while it is open (welcome.js), so this has to sit in front of it: it is
  // registered once, at window capture, when the page's recall is made, which index.html
  // does before main.js runs. Enter and Space still press the focused key.
  win?.addEventListener?.('keydown', (e) => {
    if (!prompt && !ring) return;
    e.stopImmediatePropagation?.();
    if (e.key === 'Escape') { e.preventDefault(); if (prompt) close(); else stopRing(); return; }
    if (prompt && e.key === 'Tab') {
      e.preventDefault();
      const [no, yes] = prompt.keys;
      (doc.activeElement === yes ? no : yes).focus();
    }
  }, true);

  const el = (tag, cls, text) => {
    const n = doc.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const button = (cls, text) => { const b = el('button', cls, text); b.type = 'button'; return b; };

  function close({ restore = true } = {}) {
    if (!prompt) return;
    prompt.el.remove();
    doc.documentElement?.removeAttribute?.('data-recall-open');
    const back = prompt.back;
    prompt = null;
    if (restore) try { back?.focus?.({ preventScroll: true }); } catch { /* focus is a courtesy */ }
  }

  /** Ask first. Returns false when a prompt or a ring is already up. */
  function ask(href = '../') {
    if (prompt || ring) return false;
    const card = el('div', 'recall-card');
    const head = el('p', 'recall-head');
    head.append(el('span', 'recall-eyebrow', t('recall.eyebrow')),
      el('span', 'recall-code', year ? t('recall.code', { year }) : t('recall.code.plain')));
    const title = el('h2', 'recall-title', t('recall.title'));
    title.id = 'recall-title';
    const body = el('p', 'recall-body', year ? t('recall.body', { year }) : t('recall.body.plain'));
    body.id = 'recall-body';
    const no = button('recall-cancel', t('recall.cancel'));
    const yes = button('recall-go', t('recall.confirm'));
    const actions = el('div', 'recall-actions');
    actions.append(no, yes);
    card.append(head, title, body, actions);
    const shade = el('div', 'recall-confirm');
    shade.setAttribute('role', 'alertdialog');
    shade.setAttribute('aria-modal', 'true');
    shade.setAttribute('aria-labelledby', 'recall-title');
    shade.setAttribute('aria-describedby', 'recall-body');
    shade.append(card);
    no.addEventListener('click', () => close());
    yes.addEventListener('click', () => { const to = prompt?.href ?? href; close({ restore: false }); depart(to); });
    // A tap on the shade, outside the card, is a no.
    shade.addEventListener('click', (e) => { if (e.target === shade) close(); });
    prompt = { el: shade, href, back: doc.activeElement, keys: [no, yes] };
    doc.body.append(shade);
    doc.documentElement?.setAttribute?.('data-recall-open', '');
    // The safe answer has the focus; RETURN is the bright key.
    try { no.focus({ preventScroll: true }); } catch { /* focus is a courtesy */ }
    return true;
  }

  function stopRing() {
    if (!ring) return;
    ring.timers.forEach(cancel);
    ring.el.remove();
    ring = null;
  }

  function leave(href) {
    ring = null;
    for (const fn of [...hooks]) { try { fn(href); } catch (error) { console.error('[recall] listener failed', error); } }
    try { storage?.setItem(RECALL_KEY, String(now())); } catch { /* the Observatory's tail is decoration */ }
    go(href);
  }

  /** The reverse ring, then the Observatory. No question asked. */
  function depart(href = '../') {
    if (ring) return false;
    close({ restore: false });
    if (reduced()) { leave(href); return true; }
    const shade = el('div', 'recall-ring');
    shade.setAttribute('role', 'status');
    shade.setAttribute('aria-live', 'polite');
    for (const k of ['a', 'b']) { const i = el('i', `recall-ring-${k}`); i.setAttribute('aria-hidden', 'true'); shade.append(i); }
    const eyebrow = el('p', 'recall-ring-eyebrow', t('recall.eyebrow'));
    const readout = el('div', 'recall-ring-year', year || String(present));
    readout.setAttribute('aria-hidden', 'true');
    const seq = el('div', 'recall-ring-seq');
    seq.setAttribute('aria-hidden', 'true');
    ['arrive', 'lock', 'scan'].forEach((k, n) => {
      if (n) seq.append(el('b', '', '›'));
      const s = el('span', '');
      s.append(el('i', ''), t(`recall.lamp.${k}`));
      seq.append(s);
    });
    const label = el('p', 'recall-ring-label', t('recall.ring.release'));
    const abort = button('recall-ring-abort', t('recall.abort'));
    shade.append(eyebrow, readout, seq, label, abort);
    doc.body.append(shade);
    const timers = [];
    timers.push(wait(() => { label.textContent = t('recall.ring.rewind'); }, 400));
    timers.push(wait(() => { label.textContent = t('recall.ring.home'); }, 800));
    timers.push(wait(() => leave(href), RECALL_MS));
    abort.addEventListener('click', stopRing);
    ring = { el: shade, timers };
    // The readout rolls forward from the destination year to the present.
    const from = Number(year), start = now();
    if (from && from < present) {
      const roll = () => {
        if (!ring || ring.el !== shade) return;
        const k = Math.min(1, (now() - start) / (RECALL_MS - 200));
        readout.textContent = String(Math.round(from + (present - from) * (1 - (1 - k) ** 3)));
        if (k < 1) frame(roll);
      };
      frame(roll);
    }
    return true;
  }

  return {
    ask,
    depart,
    close,
    abort: stopRing,
    /** Called as the page leaves for the Observatory, with the href. */
    onReturn(fn) { hooks.add(fn); return () => hooks.delete(fn); },
    get open() { return prompt ? 'prompt' : ring ? 'ring' : null; },
  };
}

/** The page's one recall. The arrival card's links are caught here, by delegation, from
 * the moment the document is parsed; the Jump app asks through `recall.ask` itself. */
export const recall = globalThis.document ? createRecall() : null;

if (recall) {
  globalThis.document.addEventListener('click', (e) => {
    const a = e.target?.closest?.('.gate-card .skin-tools a, #gate-observatory');
    if (!a || !plainClick(e)) return;
    e.preventDefault();
    // A stalled jump has nothing to lose, so its way home skips the question.
    if (a.id === 'gate-observatory') recall.depart(a.href);
    else recall.ask(a.href);
  });
}
