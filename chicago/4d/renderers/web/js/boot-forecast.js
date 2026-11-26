/**
 * T-2164 — the arrival clock's forecast: CPU seconds AND bytes over the link.
 *
 * BOOT_WEIGHTS (boot-weights.js) are CPU seconds measured on a fast desktop over a
 * local mirror, so the network is in none of them: `scene` (every sidecar and GLB in
 * the town) was weighted 0.2 s and `terrain` (a 1.3 MB GLB and its heightfield) had no
 * units at all. On a slow link the year rolled to the end of a phase's weight and then
 * sat on one digit until the download finished.
 *
 * So each essential phase is forecast as `cpu × pace + bytes / link`:
 *   - bytes   — what this phase downloaded last time on this build (learned, like the
 *               timing history), else the committed first-visit figure in boot-bytes.js;
 *   - link    — measured live from Resource Timing: decoded bytes over the time the
 *               network was busy. The page's own modules have already arrived by the
 *               time main.js runs, so the first estimate is a real one, not a guess;
 *   - pace    — how much slower than the reference desktop this machine is, read off
 *               the phases already finished (a phone or a busy laptop is not an M5).
 *
 * The meter reads PerformanceObserver entries only. Nothing is cloned, teed or kept:
 * a phone already near its memory ceiling (the 1835 phone crashes) pays a few numbers
 * per finished request and nothing per byte.
 */
import { BOOT_BYTES } from './boot-bytes.js';

// v2 (T-3758): keyed by year as well. v1 keyed device/detail only, so whichever year was
// visited last stood for all four (1835's 17 MB forecast for 1904's 86 MB).
const BYTES_KEY = 'c4d.boot.bytes.v2';
const PACE_KEY = 'c4d.boot.pace.v1';
// An unmeasured machine is assumed slower than the M5 the CPU weights were read on:
// a forecast that runs long ends in a quick spin, one that runs short in a crawl.
const PACE_PRIOR = { desktop: 1.5, mobile: 2.5 };
// No connection hint at all: about a 4G phone. Replaced within the first requests.
const DEFAULT_RATE = 2.5e6;
// The prior is worth this many bytes of evidence — a few small requests — so the
// page's own modules (≈1.7 MB, already arrived when main.js runs) outweigh it at once.
const PRIOR_BYTES = 2e5;
const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));

/** The committed first-visit figures for one year's cell (boot-bytes.js is keyed year › device
 *  › detail, T-3758); the nearest cell the table has where it lacks this one. */
export function committedBytes({ year = '', device = 'desktop', detail = 'full' } = {}) {
  const years = Object.keys(BOOT_BYTES);
  const y = BOOT_BYTES[String(year)] ?? BOOT_BYTES[years.includes('1835') ? '1835' : years[0]] ?? {};
  return { ...(y[device]?.[detail] ?? y.desktop?.full ?? {}) };
}

/** First-visit bytes per phase for this year: what this device last downloaded for it, else the
 *  committed figure. A reading of an earlier build still counts (T-3758): a release moves a
 *  year's bytes by a few per cent, the committed table can be weeks old, and every deploy used to
 *  throw the reading away, so most visits forecast from the stale table and the total climbed. */
export function expectedBytes({ year = '', device = 'desktop', detail = 'full', build = '', storage } = {}) {
  const result = committedBytes({ year, device, detail });
  try {
    const history = JSON.parse(storage?.getItem(BYTES_KEY) || 'null');
    const sample = history?.cells?.[`${year}/${device}/${detail}`]?.bytes;
    for (const [id, value] of Object.entries(sample || {})) {
      // Bytes do not depend on the machine, so a reading is trusted outright: only bounded
      // against corruption, never against the default.
      if (Number.isFinite(value) && value >= 0 && value < 5e8) result[id] = value;
    }
  } catch { /* Storage denial/corruption must never prevent entering town. */ }
  return result;
}

/** Live link meter from Resource Timing. `rate()` is wire bytes per busy second. */
export function createNetMeter({ Observer = globalThis.PerformanceObserver,
  connection = globalThis.navigator?.connection, onEntry = () => {} } = {}) {
  const hinted = Number(connection?.downlink) > 0 ? connection.downlink * 125000 : null;
  const prior = hinted ?? DEFAULT_RATE;
  let bytes = 0, requests = 0;
  // Merged [start, end] intervals in ms: the time anything was on the wire.
  const busy = [];
  let closed = 0;
  let observer = null;
  function addInterval(a, b) {
    if (!(b > a)) return;
    let i = 0;
    while (i < busy.length && busy[i][1] < a) i++;
    let start = a, end = b, j = i;
    while (j < busy.length && busy[j][0] <= end) { start = Math.min(start, busy[j][0]); end = Math.max(end, busy[j][1]); j++; }
    busy.splice(i, j - i, [start, end]);
    // The oldest intervals are long finished and will not merge again: fold them
    // into a sum so the list stays short over ~1,500 requests.
    while (busy.length > 48) { const [s0, e0] = busy.shift(); closed += e0 - s0; }
  }
  const api = {
    onEntry,
    add(entry) {
      // Bytes as they crossed the wire (gzip on the live origin), so the link reads
      // in the units a connection is sold in; a cache hit still reports its size.
      const size = Number(entry.encodedBodySize) || Number(entry.decodedBodySize) || Number(entry.transferSize) || 0;
      bytes += size; requests += 1;
      addInterval(Number(entry.startTime) || 0, Number(entry.responseEnd) || 0);
      api.onEntry({ bytes: size, at: Number(entry.responseEnd) || 0, entry });
    },
    get bytes() { return bytes; },
    get requests() { return requests; },
    get busySeconds() { return busy.reduce((s, [a, b]) => s + (b - a), closed) / 1000; },
    get hinted() { return hinted; },
    /** Bytes per second: a prior worth PRIOR_BYTES blended with what was measured. */
    rate() {
      return clamp((PRIOR_BYTES + bytes) / (PRIOR_BYTES / prior + api.busySeconds), 2e4, 5e9);
    },
    stop() { try { observer?.disconnect(); } catch { /* optional */ } observer = null; },
  };
  if (typeof Observer === 'function') {
    try {
      observer = new Observer(list => { for (const e of list.getEntries()) api.add(e); });
      // buffered: the modules, styles and fonts that arrived before this ran.
      observer.observe({ type: 'resource', buffered: true });
    } catch { observer = null; }
  }
  return api;
}

/**
 * The forecast over the real boot controller. `remaining(now)` is the seconds left
 * until ready; `durations(now)` is each essential phase's forecast length, which is
 * what bootProgress weighs the finished work by.
 */
export function createForecast({ boot, meter, bytes = {}, now = () => performance.now(),
  year = '', device = 'desktop', detail = 'full', build = '', storage } = {}) {
  const cpu = boot.expected || {};
  const phaseBytes = Object.fromEntries(boot.phases.map(p => [p.id, 0]));
  const expected = { ...bytes };
  let learnedPace = null;
  try {
    const stored = Number(JSON.parse(storage?.getItem(PACE_KEY) || 'null')?.[`${device}/${detail}`]);
    if (stored > 0 && stored < 100) learnedPace = stored;
  } catch { /* optional */ }
  const priorPace = learnedPace ?? PACE_PRIOR[device] ?? 1.5;
  let pace = priorPace, settledPace = priorPace;
  const essential = () => boot.phases.filter(p => p.essential);
  // Which phase a finished request belongs to: the essential phase running when it
  // finished. Bytes that arrived before `scene` started are the page itself.
  const phaseAt = at => {
    let owner = null;
    for (const p of essential()) if (p.startedAt != null && p.startedAt <= at && (p.endedAt == null || p.endedAt >= at)) owner = p;
    return owner;
  };
  let preBytes = 0;
  const take = ({ bytes: size, at }) => {
    const p = phaseAt(at);
    if (p) phaseBytes[p.id] += size; else preBytes += size;
  };
  if (meter) meter.onEntry = take;
  const link = () => meter?.rate() ?? Infinity;
  let shownTotal = null;
  // T-3758: the ETA shown is the forecast finish TIME, eased (about a 3 s time constant), so it
  // counts down in real seconds and a re-forecast moves it over a few seconds rather than in one
  // jump (it read 16 s, then 251 s two seconds later, then 83 s). Moving later is eased harder
  // than moving sooner: a clock that runs up and down reads as broken, one that runs a little
  // long ends in a quick finish.
  let shownEnd = null, easedAt = null;
  function eta(at) {
    const raw = api.remaining(at);
    const target = at + raw * 1000;
    if (shownEnd == null || easedAt == null) shownEnd = target;
    else {
      const dt = Math.max(0, at - easedAt) / 1000;
      const tau = target > shownEnd ? 6 : 2;
      shownEnd += (target - shownEnd) * (1 - Math.exp(-dt / tau));
    }
    easedAt = at;
    return Math.max(0, (shownEnd - at) / 1000);
  }

  function forecastFor(p, rate = link()) {
    const expectedBytes = Math.max(expected[p.id] || 0, phaseBytes[p.id] || 0);
    return (cpu[p.id] || 0.05) * pace + expectedBytes / rate;
  }
  function fraction(p) {
    const parts = [];
    if (Number.isFinite(p.units) && p.units > 0) parts.push((Number(p.unitsDone) || 0) / p.units);
    if (expected[p.id] > 0) parts.push(phaseBytes[p.id] / expected[p.id]);
    return parts.length ? clamp(Math.max(...parts), 0, 0.99) : null;
  }
  function remainingFor(p, at, rate) {
    const total = forecastFor(p, rate);
    if (p.startedAt == null) return total;
    const elapsed = Math.max(0, at - p.startedAt) / 1000;
    const left = total - elapsed;
    if (left > 0.25) return left;
    // Overrunning. Never claim it is about to finish: the longer it has run past its
    // forecast, the more is assumed to be left, so the clock slows and keeps moving.
    const f = fraction(p);
    const extrapolated = f && f > 0.2 ? elapsed * (1 - f) / f : 0;
    return Math.max(0.25, 0.5 * (elapsed - total), extrapolated);
  }
  // Pace from the finished phases, with the prior worth 0.2 s of reference
  // work so one noisy early phase cannot swing the whole forecast.
  function updatePace() {
    let actual = 0, planned = 0;
    const rate = link();
    for (const p of essential()) {
      if (p.endedAt == null || p.startedAt == null || p.error) continue;
      const seconds = (p.endedAt - p.startedAt) / 1000;
      actual += Math.max(0, seconds - phaseBytes[p.id] / rate);
      planned += cpu[p.id] || 0.05;
    }
    settledPace = clamp((actual + 0.2 * priorPace) / (planned + 0.2), 0.5, 40);
  }
  // A phase still running past its forecast is evidence too: the machine is slower than
  // assumed, so every phase after it is re-forecast now rather than at its end.
  function livePace(at, rate) {
    let p = settledPace;
    for (const q of essential()) {
      if (q.startedAt == null || q.endedAt != null || q.error) continue;
      // Credit the phase its whole expected download before calling it slow: on a
      // slow link the wait for bytes not yet arrived is the link's, not the machine's.
      const cpuSoFar = Math.max(0, (at - q.startedAt) / 1000
        - Math.max(expected[q.id] || 0, phaseBytes[q.id]) / rate);
      const planned = cpu[q.id] || 0.05;
      // T-3758: one phase far over its weight is weak evidence about the others (in a 1904 boot
      // the buildings ran 100x theirs while the rest ran about 6x), so it pulls the pace to the
      // geometric mean of the settled pace and its own ratio, not all the way: the forecast read
      // four minutes for what took forty seconds.
      if (cpuSoFar > planned * p) p = clamp(Math.sqrt(settledPace * cpuSoFar / planned), p, 40);
    }
    return p;
  }
  boot.on('phaseend', ({ phase }) => { if (phase?.essential) updatePace(); });

  const api = {
    get pace() { return pace; },
    get phaseBytes() { return { ...phaseBytes }; },
    get expectedBytes() { return { ...expected }; },
    durations(at = now()) {
      const rate = link();
      return Object.fromEntries(boot.phases.map(p => [p.id, p.endedAt != null && p.startedAt != null
        ? Math.max(0.001, (p.endedAt - p.startedAt) / 1000) : forecastFor(p, rate)]));
    },
    remaining(at = now()) {
      const rate = link();
      pace = livePace(at, rate);
      let left = 0;
      for (const p of essential()) if (p.endedAt == null && !p.error) left += remainingFor(p, at, rate);
      // After the last phase the first frame still has to be drawn.
      return left + 0.15 * pace;
    },
    /** What the readout shows: bytes in hand, bytes expected, the link and the ETA.
     *  T-3758: the total is held, not re-added each time: it moves only when the bytes in hand
     *  pass it (then by the overrun, plus a margin, so it does not creep up a step per request),
     *  and the ETA is eased toward the forecast (eta()). */
    readout(at = now()) {
      const inPhases = Object.values(phaseBytes).reduce((s, n) => s + n, 0);
      const toCome = essential().reduce((s, p) => s + Math.max(expected[p.id] || 0, phaseBytes[p.id]), 0);
      const bytesNow = preBytes + inPhases;
      const forecastTotal = preBytes + Math.max(toCome, inPhases);
      if (shownTotal == null) shownTotal = forecastTotal;
      else if (bytesNow > shownTotal) shownTotal = Math.max(forecastTotal, bytesNow * 1.05);
      if (essential().every(p => p.endedAt != null || p.error)) shownTotal = bytesNow;
      return { bytes: bytesNow, total: Math.max(bytesNow, shownTotal),
        rate: meter ? meter.rate() : null, eta: eta(at), pace };
    },
    /** On ready: remember this build's bytes per phase for the next visit. */
    record() {
      try {
        let history = JSON.parse(storage?.getItem(BYTES_KEY) || 'null');
        if (!history || typeof history.cells !== 'object' || !history.cells) history = { cells: {} };
        const key = `${year}/${device}/${detail}`;
        delete history.cells[key];   // re-added last: the newest readings are the ones kept
        history.cells[key] = { build, bytes: Object.fromEntries(essential()
          .filter(p => !p.error && p.endedAt != null).map(p => [p.id, Math.round(phaseBytes[p.id])])) };
        history.cells = Object.fromEntries(Object.entries(history.cells).slice(-12));
        storage?.setItem(BYTES_KEY, JSON.stringify(history));
        // Pace belongs to the machine, not the build: keep it across releases.
        const paces = JSON.parse(storage?.getItem(PACE_KEY) || 'null') || {};
        paces[`${device}/${detail}`] = Math.round(settledPace * 100) / 100;
        storage?.setItem(PACE_KEY, JSON.stringify(paces));
      } catch { /* Byte history is optional. */ }
      meter?.stop();
    },
  };
  boot.on('ready', () => api.record());
  boot.on('error', ({ phase }) => { if (phase?.essential) meter?.stop(); });
  return api;
}
