import { createLoadingContent } from './loading-content.js';
import { arrivalTitles, scenePresentation } from './scene-presentation.js';
/** Arrival presentation over the real boot controller (T-1247). */
const clamp01 = n => Math.max(0, Math.min(1, Number.isFinite(n) ? n : 0));

export function easeInOut(t) {
  t = clamp01(t);
  return t * t * (3 - 2 * t);
}

/** Progress is made only from essential work. Optional people/census failures
 * never hold the door closed or move the year backwards. */
export function bootProgress(phases, expected = {}, nowMs = 0) {
  const essential = (phases || []).filter(p => p.essential !== false);
  const weight = p => Math.max(0.001, Number(expected[p.id]) || 1);
  const total = essential.reduce((sum, p) => sum + weight(p), 0) || 1;
  let done = 0;
  for (const p of essential) {
    const w = weight(p);
    if (p.endedAt != null && !p.error) {
      done += w;
      continue;
    }
    if (p.startedAt == null || p.error) continue;
    let fraction = 0;
    if (Number.isFinite(p.units) && p.units > 0) {
      fraction = Math.min(0.99, Math.max(0, (Number(p.unitsDone) || 0) / p.units));
    } else {
      const elapsed = Math.max(0, nowMs - p.startedAt) / 1000;
      fraction = Math.min(0.92, elapsed / w);
    }
    done += w * fraction;
  }
  return Math.min(0.999999, clamp01(done / total));
}

export function yearForProgress(progress, currentYear = new Date().getFullYear(), ready = false, targetYear = 1835) {
  const floor = Number(targetYear) + 1;
  const present = Math.max(floor, Math.trunc(currentYear) || floor);
  if (ready) return Number(targetYear);
  const y = present - (present - floor) * easeInOut(progress);
  return Math.max(floor, y);
}

export function settleDurationMs({ reducedMotion = false, bootDurationMs = Infinity } = {}) {
  return reducedMotion || bootDurationMs < 1500 ? 0 : 300;
}

/** Four pre-ready buckets plus the ready state = at most five year updates. */
export function reducedProgress(progress) {
  return Math.min(0.75, Math.floor(clamp01(progress) * 4) / 4);
}

function setDigits(host, year, animate) {
  if (!host) return;
  const text = String(Math.round(year)).padStart(4, '0').slice(-4);
  if (!host.children.length) {
    host.textContent = '';
    for (const char of text) {
      const digit = document.createElement('span');
      digit.className = 'arrival-digit';
      digit.innerHTML = '<span class="arrival-digit-half arrival-digit-top"><span></span></span>'
        + '<span class="arrival-digit-half arrival-digit-bottom"><span></span></span>'
        + '<span class="arrival-digit-half arrival-digit-flap"><span></span></span>';
      host.appendChild(digit);
    }
  }
  [...host.children].forEach((digit, i) => {
    const char = text[i];
    if (!animate) digit.classList.remove('is-flipping');
    if (digit.dataset.value === char) return;
    const old = digit.dataset.value ?? char;
    digit.dataset.value = char;
    digit.querySelectorAll('.arrival-digit-top span, .arrival-digit-bottom span').forEach(span => { span.textContent = char; });
    digit.querySelector('.arrival-digit-flap span').textContent = old;
    if (animate) {
      digit.classList.remove('is-flipping');
      void digit.offsetWidth;
      digit.classList.add('is-flipping');
    }
  });
  host.dataset.year = text;
}

const MB = 1e6;
/** The readout's figures: fixed-width, so the device never reflows as they change. */
export function formatReadout({ bytes = 0, total = 0, rate = null, eta = null } = {}, ready = false) {
  const mb = n => (n / MB).toFixed(n >= 100 * MB ? 0 : 1);
  const secs = Math.max(0, Math.round(Number.isFinite(eta) ? eta : 0));
  return {
    bytes: `${mb(bytes)} / ${mb(Math.max(bytes, total))} MB`,
    rate: rate == null ? '— MB/s' : `${(rate / MB).toFixed(rate >= 10 * MB ? 0 : 1)} MB/s`,
    eta: ready ? 'LOCKED' : `T-${String(Math.floor(secs / 60)).padStart(2, '0')}:${String(secs % 60).padStart(2, '0')}`,
  };
}

function setBar(bar, progress) {
  if (!bar) return;
  const pct = progress >= 1 ? 100 : Math.min(99, Math.round(clamp01(progress) * 100));
  bar.setAttribute('aria-valuenow', String(pct));
  const fill = bar.firstElementChild;
  if (fill) fill.style.width = `${pct}%`;
}

export function createArrival({
  boot,
  yearEl,
  phaseEl,
  cardEl,
  barEl,
  buttonEl,
  contentOptions = {},
  targetYear = 1835,
  titleEl,
  onWelcome = () => {},
  currentYear = new Date().getFullYear(),
  reducedMotion = typeof matchMedia === 'function'
    ? matchMedia('(prefers-reduced-motion: reduce)').matches : false,
  now = () => performance.now(),
  reload = () => location.reload(),
  requestFrame = typeof requestAnimationFrame === 'function' ? requestAnimationFrame : null,
  cancelFrame = typeof cancelAnimationFrame === 'function' ? cancelAnimationFrame : () => {},
  // T-2164: the portable machine. All optional; without a forecast the clock runs on
  // the CPU weights alone, exactly as before.
  forecast = null,
  headlineEl = null,
  logEl = null,
  lampsEl = null,
  readoutEl = null,
} = {}) {
  if (!boot) throw new Error('createArrival requires api.boot');
  const presentation = scenePresentation(targetYear);
  targetYear = presentation.year;
  const titles = arrivalTitles(targetYear);
  let titleIndex = 0, titleAt = now();
  if (titleEl) titleEl.textContent = titles[0];
  if (headlineEl) headlineEl.textContent = titles[0];
  // The status log: a fixed number of rows made once, so a long line is clipped on
  // its row and the device's box never grows or shrinks as statuses cycle.
  const logRows = logEl ? [...logEl.children] : [];
  let previousEntry = null;
  const pushLog = entry => {
    if (previousEntry && logRows.length && entry?.phase !== 'land') {
      for (let i = 0; i < logRows.length - 1; i++) {
        logRows[i].textContent = logRows[i + 1].textContent;
        logRows[i].className = logRows[i + 1].className;
      }
      const last = logRows.at(-1);
      last.textContent = previousEntry.text;
      last.className = 'ok fresh';
    }
    previousEntry = entry;
  };
  const content = cardEl ? createLoadingContent({ boot, cardEl, now,
    entries: presentation.entries, arrivalLine: presentation.arrivalLine, onPaint: pushLog,
    ...contentOptions }) : null;
  const lamp = id => lampsEl?.querySelector(`[data-phase="${id}"]`);
  const setLamp = (id, state) => { const el = lamp(id); if (el) el.dataset.state = state; };
  let readoutAt = -Infinity;
  const readoutFields = readoutEl ? Object.fromEntries([...readoutEl.querySelectorAll('[data-read]')]
    .map(el => [el.dataset.read, el])) : {};
  function paintReadout(at, done = false) {
    if (!readoutEl || !forecast || (!done && at - readoutAt < 250)) return;
    readoutAt = at;
    const text = formatReadout(forecast.readout(at), done);
    for (const [key, el] of Object.entries(readoutFields)) if (el.textContent !== text[key]) el.textContent = text[key];
  }
  let forecastProgress = 0;
  let failed = false;
  let ready = false;
  let settleRaf = null;
  let lastShown = null;
  let progress = 0;
  let displayedYear = Math.max(targetYear + 1, currentYear);
  let tickerRaf = null;
  let lastFrame = now();

  if (phaseEl) phaseEl.setAttribute('aria-live', 'polite');
  if (yearEl) yearEl.setAttribute('aria-hidden', 'true');
  if (cardEl && !cardEl.textContent.trim()) {
    cardEl.textContent = 'Drawing on previously researched sources';
  }

  const firstStartedAt = () => {
    const starts = boot.phases.map(p => p.startedAt).filter(Number.isFinite);
    return starts.length ? Math.min(...starts) : now();
  };

  function showYear(value, animate = true) {
    const rounded = Math.round(value);
    if (rounded === lastShown) return;
    lastShown = rounded;
    setDigits(yearEl, rounded, animate && !reducedMotion);
  }

  function sync(event) {
    if (failed || ready) return;
    // Optional work cannot replace the essential phase's announcement.
    const label = event?.phase?.essential !== false && event?.phase?.label;
    if (label && phaseEl && phaseEl.textContent !== label) phaseEl.textContent = label;
    progress = Math.max(progress, bootProgress(boot.phases,
      forecast ? forecast.durations(now()) : boot.expected, now()));
    setBar(barEl, progress);
    if (reducedMotion) showYear(yearForProgress(reducedProgress(progress), currentYear, false, targetYear), false);
    else if (!requestFrame) showYear(yearForProgress(progress, currentYear, false, targetYear), false);
  }

  function tick() {
    if (failed || ready) return;
    const at = now();
    if (titleEl && !reducedMotion && at - titleAt >= 3000) {
      titleIndex = (titleIndex + 1) % titles.length; titleAt = at;
      titleEl.textContent = titles[titleIndex];
      if (headlineEl) headlineEl.textContent = titles[titleIndex];
    }
    if (forecast) {
      // T-2164. Move at the forecast's pace rather than waiting on events: each frame
      // covers its share of what is left, so the year lands as the forecast does, and
      // a forecast that grows only slows the roll — it never stops or reverses it.
      const dt = Math.max(0, at - lastFrame) / 1000;
      const left = Math.max(0.25, forecast.remaining(at));
      forecastProgress = Math.max(forecastProgress, progress);
      forecastProgress = Math.min(0.985, forecastProgress + (1 - forecastProgress) * Math.min(1, dt / left));
      progress = Math.max(progress, forecastProgress);
      paintReadout(at);
    }
    sync();
    const target = yearForProgress(progress, currentYear, false, targetYear);
    // Smooth discrete work events without running ahead of completed/estimated work.
    // A resumed tab reads the current clock once; it never replays queued ticks.
    const alpha = 1 - Math.exp(-Math.max(0, at - lastFrame) / 90);
    displayedYear = Math.min(displayedYear, displayedYear + (target - displayedYear) * alpha);
    lastFrame = at;
    if (!reducedMotion) showYear(displayedYear);
    tickerRaf = requestFrame(tick);
  }

  function stopTicker() {
    if (tickerRaf != null) cancelFrame(tickerRaf);
    tickerRaf = null;
  }

  function fail(error, { message } = {}) {
    if (ready) return;
    failed = true;
    if (phaseEl) phaseEl.hidden = false;
    if (cardEl) cardEl.hidden = true;
    content?.stop(true);
    stopTicker();
    if (settleRaf != null) cancelFrame(settleRaf);
    const msg = message || (error ? `Could not finish the reconstruction — ${String(error.message || error)}`
      : 'Could not finish the reconstruction.');
    if (phaseEl) phaseEl.textContent = msg;
    lampsEl?.querySelectorAll('[data-state="active"]').forEach(el => { el.dataset.state = 'fault'; });
    if (buttonEl) {
      buttonEl.disabled = false;
      buttonEl.textContent = 'Retry';
      buttonEl.dataset.arrivalRetry = 'true';
    }
  }

  function settle(event) {
    if (failed || ready) return;
    ready = true;
    content?.stop();
    stopTicker();
    const duration = settleDurationMs({
      reducedMotion,
      bootDurationMs: Math.max(0, (event?.at ?? now()) - firstStartedAt()),
    });
    const from = Math.max(targetYear + 1, lastShown ?? Math.round(yearForProgress(
      bootProgress(boot.phases, boot.expected, event?.at ?? now()), currentYear, false, targetYear)));
    if (buttonEl && duration > 0) buttonEl.disabled = true;
    const finish = () => {
      showYear(targetYear, false);
      content?.land();
      setBar(barEl, 1);
      barEl?.classList.add('done');
      paintReadout(now(), true);
      if (phaseEl) phaseEl.textContent = content ? 'Ready to explore.'
        : presentation.arrivalLine;
      if (buttonEl) {
        buttonEl.textContent = 'Tap to enter';
        buttonEl.disabled = false;
      }
      onWelcome();
    };
    if (!duration || !requestFrame) {
      finish();
      return;
    }
    const started = now();
    const frame = () => {
      const t = clamp01((now() - started) / duration);
      const y = from - (from - targetYear) * easeInOut(t);
      if (t < 1) {
        showYear(Math.max(targetYear + 1, y), true);
        settleRaf = requestFrame(frame);
      } else finish();
    };
    settleRaf = requestFrame(frame);
  }

  for (const type of ['phasestart', 'phaseprogress', 'phaseend']) boot.on(type, sync);
  boot.on('phasestart', ({ phase }) => { if (phase?.essential) setLamp(phase.id, 'active'); });
  boot.on('phaseend', ({ phase }) => { if (phase?.essential) setLamp(phase.id, phase.error ? 'fault' : 'done'); });
  boot.on('error', event => {
    if (event.phase?.essential !== false) fail(event.phase?.error || 'Boot failed',
      { message: `${event.phase?.label || 'Reconstruction'} failed — ${event.phase?.error || 'unknown error'}` });
  });
  boot.on('ready', settle);

  if (buttonEl) {
    buttonEl.addEventListener('click', event => {
      if (buttonEl.dataset.arrivalRetry !== 'true') return;
      event.preventDefault();
      event.stopImmediatePropagation();
      reload();
    }, true);
  }

  showYear(displayedYear, false);
  setBar(barEl, 0);
  if (cardEl) cardEl.textContent = cardEl.textContent.trim()
    || 'Drawing on previously researched sources';

  if (requestFrame) tickerRaf = requestFrame(tick);

  return {
    sync,
    content,
    fail,
    settle,
    get state() { return { failed, ready, year: lastShown }; },
  };
}
