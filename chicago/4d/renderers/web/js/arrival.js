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

export function yearForProgress(progress, currentYear = new Date().getFullYear(), ready = false) {
  const present = Math.max(1836, Math.trunc(currentYear) || 1836);
  if (ready) return 1835;
  const y = present - (present - 1836) * easeInOut(progress);
  return Math.max(1836, y);
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
  currentYear = new Date().getFullYear(),
  reducedMotion = typeof matchMedia === 'function'
    ? matchMedia('(prefers-reduced-motion: reduce)').matches : false,
  now = () => performance.now(),
  reload = () => location.reload(),
  requestFrame = typeof requestAnimationFrame === 'function' ? requestAnimationFrame : null,
  cancelFrame = typeof cancelAnimationFrame === 'function' ? cancelAnimationFrame : () => {},
} = {}) {
  if (!boot) throw new Error('createArrival requires api.boot');
  let failed = false;
  let ready = false;
  let settleRaf = null;
  let tickerRaf = null;
  let lastShown = null;
  let progress = 0;
  let displayedYear = Math.max(1836, currentYear);
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
    progress = Math.max(progress, bootProgress(boot.phases, boot.expected, now()));
    setBar(barEl, progress);
    if (reducedMotion) showYear(yearForProgress(reducedProgress(progress), currentYear), false);
    else if (!requestFrame) showYear(yearForProgress(progress, currentYear), false);
  }

  function tick() {
    if (failed || ready) return;
    const at = now();
    sync();
    const target = yearForProgress(progress, currentYear);
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
    stopTicker();
    if (settleRaf != null) cancelFrame(settleRaf);
    const msg = message || (error ? `Could not finish the reconstruction — ${String(error.message || error)}`
      : 'Could not finish the reconstruction.');
    if (phaseEl) phaseEl.textContent = msg;
    if (buttonEl) {
      buttonEl.disabled = false;
      buttonEl.textContent = 'Retry';
      buttonEl.dataset.arrivalRetry = 'true';
    }
  }

  function settle(event) {
    if (failed || ready) return;
    ready = true;
    stopTicker();
    const duration = settleDurationMs({
      reducedMotion,
      bootDurationMs: Math.max(0, (event?.at ?? now()) - firstStartedAt()),
    });
    const from = Math.max(1836, lastShown ?? Math.round(yearForProgress(
      bootProgress(boot.phases, boot.expected, event?.at ?? now()), currentYear, false)));
    if (buttonEl && duration > 0) buttonEl.disabled = true;
    const finish = () => {
      showYear(1835, false);
      setBar(barEl, 1);
      barEl?.classList.add('done');
      if (phaseEl) phaseEl.textContent = 'You have arrived in Chicago, summer 1835.';
      if (buttonEl) {
        buttonEl.textContent = 'Tap to enter';
        buttonEl.disabled = false;
      }
    };
    if (!duration || !requestFrame) {
      finish();
      return;
    }
    const started = now();
    const frame = () => {
      const t = clamp01((now() - started) / duration);
      const y = from - (from - 1835) * easeInOut(t);
      if (t < 1) {
        showYear(Math.max(1836, y), true);
        settleRaf = requestFrame(frame);
      } else finish();
    };
    settleRaf = requestFrame(frame);
  }

  for (const type of ['phasestart', 'phaseprogress', 'phaseend']) boot.on(type, sync);
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
    fail,
    settle,
    get state() { return { failed, ready, year: lastShown }; },
  };
}
