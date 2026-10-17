/**
 * nav-telemetry.js — the Navigator's telemetry strip (T-2623, NAV-207; DESIGN §06
 * "Machine chrome": "A thin phosphor footer that ticks every 800 ms: FIELD, DRIFT, SIG
 * and a RECALL lamp. It reuses portal.js telemetry and drift events. It is decorative,
 * so mark it aria-hidden.")
 *
 *   FIELD   the field coherence, 0.994-0.999 while the hold is steady
 *   DRIFT   the interval drift, about ±0.4 d
 *   SIG     four signal bars, one dropping while a drift event holds
 *   RECALL  a lamp: the way back to the Observatory is open
 *
 * The numbers and the drift events are the portal's own (machine-drift.js, which
 * portal.js reads too), so the device and the front door are one machine. They are
 * fake instruments and are shown as instruments, never as research: nothing here is a
 * fact about the town, and the whole strip is aria-hidden.
 *
 * WHEN IT TICKS. Every TICK_MS while it can be seen, and not otherwise: never while the
 * tab is hidden, the device is docked (phone) or folded to its rail (desktop), the HUD
 * is hidden or the drawer covers the device; and never under reduced motion, where it
 * stands still at its steady reading (QA-06: "No telemetry ticking"). `sync()` puts the
 * timer in step with all of that; the device calls it when its height changes and from
 * its own once-a-frame update (at most every 250 ms), and the tab's visibility and the
 * reduced-motion setting call it themselves. A tick writes four short text nodes and
 * nothing else, so it costs no frame time worth measuring.
 */
import './machine-drift.js';

const D = globalThis.chicagoMachineDrift;
export const TICK_MS = D.TICK_MS;
export const SIGNAL_BARS = 4;

/** SIG as bars: `n` lit of `of`. */
export function signalBars(n, of = SIGNAL_BARS) {
  const lit = Math.max(0, Math.min(of, Math.round(n)));
  return '▮'.repeat(lit) + '▯'.repeat(of - lit);
}

/** The strip's text for one tick's readings (machine-drift.js `readings`). */
export function stripText({ coherence, drift }, slipping = false) {
  return {
    field: D.format.coherence(coherence),
    drift: D.format.drift(drift).toUpperCase(),
    sig: signalBars(slipping ? SIGNAL_BARS - 2 : SIGNAL_BARS - 1),
  };
}

/** The steady reading: what the strip shows before its first tick, and under reduced motion. */
export const STEADY = Object.freeze({ field: '0.998', drift: '±0.4 D', sig: signalBars(SIGNAL_BARS - 1) });

/** Whether an element can actually be seen: laid out, and not visibility-hidden. */
function seen(el) {
  if (!el?.isConnected) return false;
  if (typeof el.checkVisibility === 'function') return el.checkVisibility({ visibilityProperty: true });
  const view = el.ownerDocument?.defaultView;
  return el.getClientRects().length > 0 && view?.getComputedStyle(el).visibility !== 'hidden';
}

/**
 * Build the strip at the foot of `host` and keep it ticking only while it should.
 * Returns { el, sync, tick, running, ticks, slipping, destroy }.
 */
export function mountTelemetry({
  host,
  open = () => true,
  doc = host?.ownerDocument,
  reducedMotion = doc?.defaultView?.matchMedia?.('(prefers-reduced-motion: reduce)') ?? null,
  random = Math.random,
  now = () => Date.now(),
  setTimer = (fn, ms) => setInterval(fn, ms),
  clearTimer = (id) => clearInterval(id),
  visible = seen,
} = {}) {
  if (!host || !doc) return null;
  const el = doc.createElement('div');
  el.className = 'nav-telemetry';
  el.setAttribute('aria-hidden', 'true');
  const cell = (key, label) => {
    const c = doc.createElement('span');
    c.className = 'nav-tm-cell';
    c.dataset.t = key;
    const k = doc.createElement('span');
    k.className = 'nav-tm-k';
    k.textContent = label;
    const b = doc.createElement('b');
    c.append(k, b);
    el.append(c);
    return b;
  };
  const out = { field: cell('field', 'FIELD'), drift: cell('drift', 'DRIFT'), sig: cell('sig', 'SIG') };
  const recall = doc.createElement('span');
  recall.className = 'nav-tm-cell nav-tm-recall';
  recall.dataset.t = 'recall';
  recall.innerHTML = '<span class="nav-tm-k">RECALL</span><i class="nav-tm-lamp"></i>';
  el.append(recall);
  host.append(el);

  let timer = null;
  let ticks = 0;
  let slippingUntil = 0;
  let nextDrift = now() + D.nextDriftIn(true, random);

  function paint(text, slipping) {
    out.field.textContent = text.field;
    out.drift.textContent = text.drift;
    out.sig.textContent = text.sig;
    el.dataset.state = slipping ? 'drift' : 'steady';
  }
  paint(STEADY, false);

  function tick() {
    const t = now();
    if (t >= nextDrift && t >= slippingUntil) {
      slippingUntil = t + D.DRIFT_MS;
      nextDrift = slippingUntil + D.nextDriftIn(false, random);
    }
    const slipping = t < slippingUntil;
    paint(stripText(D.readings(slipping, random), slipping), slipping);
    ticks += 1;
  }

  const wanted = () => !doc.hidden && !reducedMotion?.matches && open() && visible(el);
  function sync() {
    const want = wanted();
    if (want && timer === null) timer = setTimer(tick, TICK_MS);
    else if (!want && timer !== null) {
      clearTimer(timer);
      timer = null;
      if (reducedMotion?.matches) paint(STEADY, false);
    }
    return want;
  }
  const onVisibility = () => sync();
  doc.addEventListener?.('visibilitychange', onVisibility);
  reducedMotion?.addEventListener?.('change', onVisibility);
  sync();

  return {
    el,
    sync,
    tick,
    get running() { return timer !== null; },
    get ticks() { return ticks; },
    get slipping() { return now() < slippingUntil; },
    destroy() {
      if (timer !== null) clearTimer(timer);
      timer = null;
      doc.removeEventListener?.('visibilitychange', onVisibility);
      reducedMotion?.removeEventListener?.('change', onVisibility);
      el.remove();
    },
  };
}
