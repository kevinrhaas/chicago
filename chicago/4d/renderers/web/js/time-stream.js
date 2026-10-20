/**
 * T-2611 — the time-stream captions (design doc "Field Navigator Mk II", section 05).
 *
 * As the arrival's ticker rolls down from the present year to the destination, a
 * one-line caption shows for about two seconds as it passes a landmark year:
 * "1966 · A group of architects buys the Glessner House for $35,000 to save it."
 * The deck is data/timestream/<scene>.json, 8 to 12 graded and sourced captions,
 * held by tools/check_timestream.py; this module only decides which to show, when.
 *
 *   - A caption shows only as the ticker passes its year — the frame the ticker first
 *     reads that year or an earlier one. Years crossed while another caption is up are
 *     passed, not queued: a caption never shows after the ticker has left its year.
 *   - One at a time, each for HOLD_MS, and never twice, so a screen reader hears each
 *     at most once (the polite region gets a caption's words once, and is never
 *     cleared, which would be announced too).
 *   - A FAST load shows at most 3, chosen by `importance`; a slow one up to 8. "Slow"
 *     is read off the trip itself: once it has run SLOW_AFTER_MS without landing it is
 *     slow by definition, so a load that lands inside that can never show a fourth.
 *     A forecast that already says the trip will be long widens the choice to the top
 *     8 from the start, so the first captions of a slow trip are not only the top 3.
 *   - Optional, like the loading cards: no deck, a failed fetch or a missing element
 *     shows nothing and never holds the boot. Ready or an essential failure stops it.
 *
 * arrival.js calls `passYear(year)` from its ticker (the `onYear` hook); main.js owns the
 * instance, the fetch and the forecast.
 */

import { gradeTerm } from './strings/terms.js';

export const FAST_LIMIT = 3;
export const SLOW_LIMIT = 8;
export const HOLD_MS = 2000;
export const SLOW_AFTER_MS = 8000;
/** A trip forecast at this many seconds or more is treated as slow from the start. */
export const SLOW_FORECAST_S = 12;
/** How far ahead (in years) a lesser caption may give way to a better one: near
 * neighbours only (1861 for 1860), so a fast trip is not left waiting for a caption
 * the landing would cut short. */
export const MAX_REACH = 4;
/** No caption starts when the forecast lands the trip sooner than this: it would be
 * cut off by the landing before it could be read. */
export const LAST_CALL_S = 0.6;


/** The years of the `limit` most important captions. Importance is unique per deck
 * (the gate holds it), so the pick never depends on file order. */
export function eligibleYears(captions, limit) {
  return new Set([...(captions || [])]
    .sort((a, b) => (b.importance || 0) - (a.importance || 0))
    .slice(0, Math.max(0, limit))
    .map(c => c.year));
}

/** The pure decision, for a pass from `from` (the year shown before) down to `to`:
 * the caption to show, or null. `reach` is how many more years the ticker will pass
 * while a caption shown now is still up (its pace times HOLD_MS): a lesser caption is
 * passed over when a more important one lies inside that reach, since showing the
 * lesser would hold the better one off the screen as the ticker went by it. */
export function pickCaption({ captions, from, to, shown, eligible, busy, count, cap, reach = 0 }) {
  if (busy || count >= cap || !(to < from)) return null;
  const open = c => !shown.has(c.year) && eligible.has(c.year);
  let best = null;
  for (const c of captions || []) {
    if (!(c.year >= to && c.year < from) || !open(c)) continue;
    if (!best || (c.importance || 0) > (best.importance || 0)) best = c;
  }
  if (best && reach > 0 && (captions || []).some(d => open(d) && d.year < to && d.year >= to - reach
    && (d.importance || 0) > (best.importance || 0))) return null;
  return best;
}

export function createTimeStream({
  el = null,
  sayEl = null,
  boot = null,
  forecast = null,
  currentYear = new Date().getFullYear(),
  now = () => performance.now(),
  wait = (fn, ms) => setTimeout(fn, ms),
  cancel = id => clearTimeout(id),
  fetcher = typeof fetch === 'function' ? (...a) => fetch(...a) : null,
  // T-2612: told the whole deck once it arrives (the telemetry log takes its `log` lines).
  onDeck = () => {},
} = {}) {
  const startedAt = now();
  let captions = [];
  let lastYear = Math.trunc(Number(currentYear)) || new Date().getFullYear();
  let stopped = false;
  let shownAt = -Infinity;
  let hideTimer = null;
  const shown = new Set();
  const log = [];
  // The ticker's recent pace, years per millisecond over the last second of passes.
  const trail = [];
  const pace = () => {
    const first = trail[0], last = trail.at(-1);
    return first && last && last.t > first.t ? (first.y - last.y) / (last.t - first.t) : 0;
  };
  const part = key => el?.querySelector?.(`[data-ts="${key}"]`) || null;
  const screen = el?.parentElement || null;

  const elapsed = () => Math.max(0, now() - startedAt);
  const slowForecast = () => {
    try {
      const left = forecast?.remaining?.(now());
      return Number.isFinite(left) && elapsed() / 1000 + left >= SLOW_FORECAST_S;
    } catch { return false; }
  };
  const isSlow = () => elapsed() >= SLOW_AFTER_MS;

  function hide() {
    if (hideTimer != null) cancel(hideTimer);
    hideTimer = null;
    if (el) el.dataset.state = 'off';
    if (screen?.dataset) delete screen.dataset.timestream;
  }

  function show(c) {
    shown.add(c.year);
    shownAt = now();
    log.push({ year: c.year, at: Math.round(elapsed()), ticker: c._ticker });
    if (el) {
      const { label, meaning } = gradeTerm(c.grade);
      const year = part('year'), text = part('text'), grade = part('grade');
      if (year) year.textContent = String(c.year);
      if (text) text.textContent = c.text;
      if (grade) { grade.textContent = label; grade.title = meaning; grade.dataset.grade = c.grade || ''; }
      el.dataset.year = String(c.year);
      el.dataset.state = 'on';
    }
    if (screen?.dataset) screen.dataset.timestream = 'on';
    // Once, never cleared: the region speaks each caption a single time.
    if (sayEl) sayEl.textContent = `${c.year}. ${c.text}`;
    if (hideTimer != null) cancel(hideTimer);
    hideTimer = wait(hide, HOLD_MS);
  }

  function passYear(year) {
    const y = Math.round(Number(year));
    if (!Number.isFinite(y)) return;
    const from = lastYear;
    if (y < lastYear) lastYear = y;
    const t = now();
    trail.push({ t, y: lastYear });
    while (trail.length > 2 && t - trail[0].t > 1000) trail.shift();
    if (stopped || !captions.length) return;
    try { if (forecast && forecast.remaining(t) < LAST_CALL_S) return; } catch { /* no forecast, no last call */ }
    const slow = isSlow();
    const c = pickCaption({
      captions, from, to: y, shown,
      eligible: eligibleYears(captions, slow || slowForecast() ? SLOW_LIMIT : FAST_LIMIT),
      busy: now() - shownAt < HOLD_MS,
      count: shown.size,
      cap: slow ? SLOW_LIMIT : FAST_LIMIT,
      reach: Math.min(MAX_REACH, pace() * HOLD_MS),
    });
    if (c) show({ ...c, _ticker: y });
  }

  function setDeck(deck) {
    const list = Array.isArray(deck?.captions) ? deck.captions : [];
    captions = list.filter(c => Number.isInteger(c?.year) && typeof c.text === 'string' && c.text.trim());
    try { if (deck) onDeck(deck); } catch { /* the log is optional too */ }
    return captions.length;
  }

  async function load(url) {
    if (!fetcher || !url) return 0;
    try {
      const res = await fetcher(url, { cache: 'no-cache' });
      return res?.ok ? setDeck(await res.json()) : 0;
    } catch { return 0; }
  }

  function stop() {
    stopped = true;
    hide();
  }

  boot?.on?.('ready', stop);
  boot?.on?.('error', event => { if (event?.phase?.essential !== false) stop(); });

  return {
    passYear, setDeck, load, stop,
    get state() {
      return { stopped, count: shown.size, shown: log.map(r => ({ ...r })), slow: isSlow(), deck: captions.length };
    },
  };
}
