/**
 * Jump (SCR 08), loaded the first time it opens (T-2618; T-2655, DESIGN §07 "Jump").
 *
 * The three destinations as small era cards — the Observatory's own plates, the
 * destination, its date — with the one you are in marked HERE. Picking another runs the
 * short in-world jump: the transfer ring closes over the town (1.2 s; at once with reduced
 * motion), the Observatory's transfer stamp is written, and the destination's page takes
 * it from there with its own time-stream and landing (T-2610, T-2611, T-2613), the ring's
 * tail on screen as it would be from the Observatory (skin.js, `chicago4d.transfer`).
 * Escape, or Abort, during the ring stays put.
 *
 * RECALL returns to the Observatory, asking first (T-2735), and is the screen's one
 * signal-red key. Time of day is not offered: no scene is lit at another hour yet, and a
 * choice that changes nothing would be a fake one.
 */
import { scenePresentation } from '../scene-presentation.js';

/** The Observatory's destinations, in its order, with the plate each card wears there
 * (portal/plates/SOURCES.md says where each came from). */
export const DESTINATIONS = [
  { year: 1835, date: '1835-07-01', href: '../1835/', plate: 'portal/plates/dearborn-drawbridge-1834.jpg' },
  { year: 1904, date: '1904-07-01', href: '../1904/', plate: 'portal/plates/glessner-house-habs.jpg' },
  { year: 1812, date: '1812-08-14', href: '../1812/', plate: 'portal/plates/fort-dearborn-1812.jpg' },
];
export const RING_MS = 1200;
const TRANSFER_KEY = 'chicago4d.transfer';
const JUMPED_KEY = 'chicago4d.jumped'; // T-2664, js/tour-offer.js

const dateWords = (date) => new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })
  .format(new Date(`${date}T12:00:00Z`));

let pending = null;   // the jump under way: { timer, overlay, onKey }

/** Run the in-world jump to `d`: the ring, the transfer stamp, then the page. */
export function jumpTo(d, {
  doc = globalThis.document,
  reduced = globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false,
  go = (href) => globalThis.location?.assign(href),
  wait = (fn, ms) => setTimeout(fn, ms),
  cancel = (id) => clearTimeout(id),
  storage = (() => { try { return globalThis.sessionStorage; } catch { return null; } })(),
} = {}) {
  if (pending) return false;
  const overlay = doc.createElement('div');
  overlay.className = 'nav-jump-ring';
  overlay.setAttribute('role', 'status');
  overlay.setAttribute('aria-live', 'polite');
  overlay.innerHTML = '<i class="nav-jump-ring-a" aria-hidden="true"></i><i class="nav-jump-ring-b" aria-hidden="true"></i>';
  const label = doc.createElement('p');
  label.className = 'nav-jump-ring-label';
  label.textContent = `Jumping to ${d.year}`;
  const abort = doc.createElement('button');
  abort.type = 'button';
  abort.className = 'nav-jump-abort';
  abort.textContent = 'Abort';
  overlay.append(label, abort);
  doc.body?.append(overlay);
  const stop = () => {
    if (!pending) return;
    cancel(pending.timer);
    doc.removeEventListener?.('keydown', pending.onKey, true);
    pending.overlay.remove?.();
    pending = null;
  };
  const onKey = (e) => { if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation?.(); stop(); } };
  abort.addEventListener('click', stop);
  doc.addEventListener?.('keydown', onKey, true);
  // The transfer stamp is written as the page goes, not when the ring starts: the far page
  // opens on the ring's tail only if the stamp is under 10 s old when it loads (skin.js),
  // and on a busy machine the ring's own timer can fire several seconds late (it waits for
  // the frame in hand), which used to age the stamp out before the far page could read it.
  // An aborted jump writes none, so a later visit is never mistaken for its far end.
  const timer = wait(() => {
    pending = null;
    try { storage?.setItem(TRANSFER_KEY, String(Date.now())); } catch { /* the ring's tail is decoration */ }
    // T-2664: and that this arrival is a Jump, for the far year's one-time Jump hint
    // (js/tour-offer.js reads and clears it); the Observatory writes none.
    try { storage?.setItem(JUMPED_KEY, String(d.year)); } catch { /* the hint is a nicety */ }
    go(d.href);
  }, reduced ? 0 : RING_MS);
  pending = { timer, overlay, onKey };
  return true;
}

export function mount(el, ctx = {}, opts = {}) {
  const doc = el.ownerDocument;
  const here = Number(ctx.scene?.id ?? ctx.scene?.target_date?.slice(0, 4));
  el.replaceChildren();
  const list = doc.createElement('div');
  list.className = 'nav-jump-list';
  for (const d of DESTINATIONS) {
    const p = scenePresentation(d.year, d.date);
    const isHere = d.year === here;
    const card = doc.createElement(isHere ? 'div' : 'a');
    card.className = 'nav-block nav-jump';
    card.dataset.year = String(d.year);
    if (isHere) card.setAttribute('aria-current', 'page');
    else {
      card.href = d.href;
      card.addEventListener('click', (e) => {
        // A plain click jumps in the world; a modified one opens the page as a link does.
        if (e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        e.preventDefault();
        jumpTo(d, opts);
      });
    }
    const plate = doc.createElement('img');
    plate.className = 'nav-jump-plate';
    plate.src = d.plate;
    plate.alt = '';
    plate.loading = 'lazy';
    plate.decoding = 'async';
    const k = doc.createElement('span');
    k.className = 'nav-k nav-k-row';
    k.append(Object.assign(doc.createElement('span'), { textContent: String(d.year) }));
    // The spaces keep the words apart for a screen reader and for anything reading the
    // card's text ("1835 Here", not "1835Here"); flex drops them from the layout.
    if (isHere) k.append(' ', Object.assign(doc.createElement('span'), { className: 'nav-step nav-here', textContent: 'Here' }));
    const name = Object.assign(doc.createElement('strong'), { className: 'nav-place', textContent: p.place });
    const sub = Object.assign(doc.createElement('span'), { className: 'nav-sub',
      textContent: `${p.eyebrow !== p.place ? `${p.eyebrow} · ` : ''}${dateWords(d.date)}` });
    const text = Object.assign(doc.createElement('span'), { className: 'nav-jump-text' });
    text.append(k, ' ', name, ' ', sub);
    card.append(plate, text);
    list.append(card);
  }
  const recall = doc.createElement('a');
  recall.className = 'nav-key nav-recall';
  recall.href = '../';
  recall.innerHTML = '<b>Recall</b><span>Back to the Observatory</span>';
  // T-2735: a plain click asks before going home (the page's recall prompt and reverse
  // ring); a modified one opens the Observatory as a link does.
  recall.addEventListener('click', (e) => {
    if (e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || !ctx.actions?.recall) return;
    e.preventDefault();
    ctx.actions.recall(recall.href);
  });
  el.append(list, recall);
}

export function unmount(el) { el.replaceChildren(); }
