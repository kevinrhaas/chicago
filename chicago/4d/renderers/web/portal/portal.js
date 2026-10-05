(() => {
  // Preserve the old explicit root deep links, including spawn, jaunt and structure parameters.
  const params = new URLSearchParams(location.search);
  if ([...params.keys()].some(key => !['skin','utm_source','utm_medium','utm_campaign'].includes(key))) {
    const year = /^\d{4}$/.test(params.get('year') || '') ? params.get('year') : '1835';
    location.replace(new URL(`${year}/${location.search}${location.hash}`, location.href).href);
    return;
  }
  // The front door is a working machine (T-2119): it cold-starts, finds each coordinate on the
  // chronometer, then keeps holding them — holds drift and are pulled back, the log never stops.
  // One slow tick drives the numbers; everything that moves is CSS. Reduced motion skips the
  // cold start and the tick, and leaves the console lit and still.
  const root = document.documentElement;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  const status = $('#scan-status'), station = $('#station-status'), count = $('.scan-count');
  const aperture = $('.aperture'), apertureState = $('#aperture-state'), log = $('#machine-log');
  const monitor = $('.monitor'), readout = $('#readout'), lock = $('.core .lock');
  const cards = $$('.era');
  const states = cards.map(card => card.querySelector('.era-state'));
  const settled = states.map(s => s && s.lastChild.textContent);
  const coords = Object.fromEntries($$('.coord').map(c => [c.dataset.coord, c]));
  const lamps = Object.fromEntries($$('.lamps li').map(l => [l.dataset.lamp, l]));
  const gauges = Object.fromEntries($$('.gauge').map(g => [g.dataset.gauge, g]));
  const tele = Object.fromEntries($$('.telemetry-cell[data-t]').map(c => [c.dataset.t, c]));
  const holds = cards.map((card, i) => {
    // 1835 holds at lock nominal; 1904 and 1812 are only partly built, so they are cleared for
    // entry but calibrating: a lower hold that wanders more and slips more often.
    const calibrating = card.classList.contains('era-calibrating');
    const base = calibrating ? (card.dataset.year === '1904' ? 86 : 71) : 99.4;
    return { i, card, year: card.dataset.year, calibrating, base, target: base, value: base,
      bar: card.querySelector('.era-hold-bar i'), out: card.querySelector('.era-hold b'),
      checks: [...card.querySelectorAll('.era-checks b')] };
  });
  const rand = (a, b) => a + Math.random() * (b - a);
  let timers = [], booted = false, leaving = false, ticker = 0, ticks = 0, nextDrift = 0, lastLine = -1, checkCard = 0;

  function later(ms, fn) { timers.push(setTimeout(fn, ms)); }
  function setState(i, text) { const s = states[i]; if (s) s.lastChild.textContent = text; }
  function say(text, warn) {
    if (!log) return;
    const li = document.createElement('li'); li.textContent = text; li.className = warn ? 'fresh warn' : 'fresh';
    log.append(li); while (log.children.length > 6) log.firstElementChild.remove();
  }
  function lamp(name, on, blink) { const l = lamps[name]; if (l) { l.classList.toggle('on', on); l.classList.toggle('blink', !!blink); } }
  function gauge(name, v) {
    const g = gauges[name]; if (!g) return;
    v = Math.max(0, Math.min(1, v)); g.style.setProperty('--v', v.toFixed(3));
    const b = g.querySelector('b'); if (b) b.textContent = String(Math.round(v * 100)).padStart(2, '0');
  }
  function paintHold(h) { h.bar.style.setProperty('--hold', (h.value / 100).toFixed(3)); h.out.textContent = `${h.value.toFixed(1)}%`; }
  function setAperture(state, text) { aperture.dataset.state = state; apertureState.textContent = text; }
  function telemetry(name, text, state) { const c = tele[name]; if (!c) return; c.querySelector('b').textContent = text; if (state) c.dataset.state = state; }

  // The destination readout and the reticle follow whichever coordinate you point at.
  const PLACES = { 1835: 'RIVER SETTLEMENT', 1904: 'PRAIRIE AVENUE', 1812: 'FORT DEARBORN' };
  let shown = '1835', rollTimer;
  function roll(year) {
    if (!readout || year === shown) return; shown = year;
    const spans = [...readout.children];
    clearInterval(rollTimer);
    if (reduced.matches) { spans.forEach((s, i) => { s.textContent = year[i]; }); return; }
    let n = 0; readout.classList.add('rolling');
    rollTimer = setInterval(() => {
      n++; spans.forEach((s, i) => { s.textContent = n > 3 + i * 2 ? year[i] : String(Math.floor(Math.random() * 10)); });
      if (n > 10) { clearInterval(rollTimer); readout.classList.remove('rolling'); }
    }, 45);
  }
  function aim(year) {
    const dot = coords[year] && coords[year].querySelector('.coord-dot');
    if (dot && lock) lock.style.transform = `translate(${dot.getAttribute('cx')}px,${dot.getAttribute('cy')}px)`;
    if (year !== shown && booted) say(`TARGET ${year} · ${PLACES[year] || 'COORDINATE'}`);
    roll(year);
  }
  function found(i) {
    const card = cards[i]; card.classList.add('resolved'); setState(i, settled[i]);
    if (coords[card.dataset.year]) coords[card.dataset.year].classList.add('found');
    paintHold(holds[i]);
  }

  function finish() {
    timers.forEach(clearTimeout); timers = [];
    holds.forEach(h => {
      if (!h.drifting) return;
      h.drifting = false; h.target = h.base; h.value = h.base; delete h.card.dataset.hold;
      if (coords[h.year]) coords[h.year].classList.remove('drift');
    });
    if (monitor) monitor.classList.remove('noisy');
    cards.forEach((c, i) => found(i));
    status.textContent = '3 coordinates online · 1 nominal · 2 calibrating'; count.textContent = '03 / 03';
    station.textContent = 'HOLDING'; setAperture('open', 'OPEN');
    lamp('time', true); lamp('map', true); lamp('archive', true, true); lamp('field', true); lamp('recall', true, true); lamp('drift', false);
    gauge('flux', .72); gauge('coherence', .86); gauge('drift', .28);
    root.classList.remove('booting'); document.body.classList.remove('acquiring'); document.body.classList.add('resolved');
    booted = true;
    if (!reduced.matches && !ticker) { nextDrift = Date.now() + rand(5000, 8000); ticker = setInterval(tick, 800); }
    if (reduced.matches) { clearInterval(ticker); ticker = 0; }
  }

  // The cold start, about three seconds: tubes, sweep, three signatures, matrix stable.
  function boot() {
    root.classList.add('booting'); document.body.classList.add('acquiring');
    if (log) log.replaceChildren();
    say('APPARATUS MK II · COLD BOOT'); setAperture('sealed', 'SEALED');
    status.textContent = 'Scanning the interval…'; count.textContent = '00 / 03'; station.textContent = 'COLD START';
    Object.keys(lamps).forEach(n => lamp(n, false)); Object.keys(gauges).forEach(n => gauge(n, 0));
    cards.forEach((card, i) => setState(i, 'SCANNING…'));
    holds.forEach(h => { h.value = 0; paintHold(h); });
    later(250, () => { say('POWER ON… OK'); lamp('time', true); station.textContent = 'ACQUIRING'; });
    later(500, () => { lamp('map', true); gauge('flux', .95); });
    later(700, () => { say('SCANNING INTERVAL…'); lamp('archive', true, true); gauge('coherence', .55); gauge('drift', .7); });
    later(1050, () => { say('RETICULATING SPLINES…'); lamp('field', true); gauge('flux', .6); });
    const lines = cards.map(c => `${c.dataset.year} FOUND · ${c.classList.contains('era-calibrating') ? 'CALIBRATING' : 'LOCK NOMINAL'}`);
    const stages = cards.map(c => `${c.dataset.year} found`);
    cards.forEach((card, i) => later(1400 + i * 450, () => {
      found(i); holds[i].value = holds[i].target; paintHold(holds[i]);
      say(lines[i] || `${card.dataset.year} · resolved`); status.textContent = stages[i] || status.textContent; count.textContent = `0${i + 1} / 03`;
    }));
    later(2650, () => { say('STABILIZING…'); setAperture('opening', 'OPENING'); gauge('coherence', .86); gauge('drift', .28); });
    later(3050, () => { say('MATRIX STABLE · 3 COORDS HELD'); lamp('recall', true, true); finish(); });
  }

  const LINES = [
    'SYNCING TIME MESH… OK', 'MATRIX STABLE', 'RETICULATING SPLINES…', 'SCANNING INTERVAL… 3 SIGNALS',
    'RE-CENTERING ON WOLF POINT… OK', 'COMPENSATING LAKE DRIFT', 'DOSIMETRY NOMINAL', 'CACHE WARM',
    'PING 1835… 12 MS', 'PING 1904… 31 MS', 'PING 1812… 44 MS', 'CALIBRATING 1904 MESH…', 'SURVEYING 1812 PRAIRIE…',
    'RETURN WINDOW OPEN', 'DAMPING NORTH BRANCH HARMONIC', 'EVIDENCE INDEX LINKED', 'SWEEP 4.0 S · STEADY', 'BUFFERING 1904 STREETSCAPE…',
  ];
  function chatter() {
    let n; do { n = Math.floor(Math.random() * LINES.length); } while (n === lastLine);
    lastLine = n; say(LINES[n]);
  }

  // Every so often one coordinate's hold slips; the machine pulls it back.
  function drift() {
    const free = holds.filter(h => !h.drifting); if (!free.length) return;
    const shaky = free.filter(h => h.calibrating);
    const pool = shaky.length && Math.random() < .7 ? shaky : free;
    const h = pool[Math.floor(Math.random() * pool.length)];
    h.drifting = true; h.target = h.base - rand(9, 15);
    h.card.dataset.hold = 'drift'; setState(h.i, 'HOLD SLIPPING');
    if (coords[h.year]) coords[h.year].classList.add('drift');
    lamp('drift', true, true); monitor && monitor.classList.add('noisy'); station.textContent = 'COMPENSATING';
    say(`${h.year} HOLD SLIPPING · ${Math.round(h.target)}% · COMPENSATING`, true);
    later(1300, () => { setState(h.i, 'RE-ACQUIRING'); say(`RE-ACQUIRING ${h.year}…`, true); });
    later(2900, () => {
      h.target = h.base; h.drifting = false; delete h.card.dataset.hold; setState(h.i, settled[h.i]);
      if (coords[h.year]) coords[h.year].classList.remove('drift');
      lamp('drift', false); monitor && monitor.classList.remove('noisy'); station.textContent = 'HOLDING';
      say(`${h.year} HOLD RESTORED`);
    });
  }

  // Each tick one destination re-runs one of its status checks: a moment of '···', then the
  // reading comes back and flashes. It is a loading screen that never quite finishes.
  function recheck() {
    const h = holds[checkCard++ % holds.length]; if (!h.checks.length) return;
    const b = h.checks[Math.floor(Math.random() * h.checks.length)];
    const text = b.dataset.text || (b.dataset.text = b.textContent);
    b.classList.add('checking'); b.textContent = '···';
    setTimeout(() => { b.textContent = text; b.classList.remove('checking'); b.classList.add('ok'); setTimeout(() => b.classList.remove('ok'), 700); }, 450);
  }
  function tick() {
    if (document.hidden || leaving) return;
    ticks++;
    const slipping = holds.some(h => h.drifting);
    holds.forEach(h => {
      const noise = h.calibrating ? rand(-2.2, 2.2) : rand(-.25, .25);
      h.value = Math.max(0, Math.min(99.9, h.value + (h.target - h.value) * .45 + noise));
      if (h.calibrating && !h.drifting && Math.random() < .2) h.target = h.base + rand(-4, 4);
      paintHold(h);
    });
    telemetry('reactor', `${rand(86.4, 88.1).toFixed(1)}%`);
    telemetry('coherence', slipping ? rand(.962, .981).toFixed(3) : rand(.994, .999).toFixed(3), slipping ? 'warn' : 'ok');
    telemetry('drift', slipping ? `±${rand(1.2, 2.1).toFixed(1)} d` : `±${rand(.3, .5).toFixed(1)} d`, 'warn');
    gauge('flux', rand(.64, .8)); gauge('coherence', slipping ? rand(.5, .65) : rand(.82, .92)); gauge('drift', slipping ? rand(.8, .93) : rand(.2, .36));
    recheck();
    if (ticks % 3 === 0 && !slipping) chatter();
    if (Date.now() > nextDrift && !slipping) { nextDrift = Date.now() + rand(9000, 14000); drift(); }
  }

  if (!reduced.matches) boot(); else finish();
  reduced.addEventListener('change', finish);
  cards.forEach(card => {
    card.addEventListener('focus', () => { card.classList.add('resolved'); aim(card.dataset.year); });
    card.addEventListener('pointerenter', () => aim(card.dataset.year));
  });

  // The manual: a dialog the machine's operator can pull open and put away.
  const manual = $('#manual');
  const openManual = $('.manual-open');
  if (manual && openManual && typeof manual.showModal === 'function') {
    openManual.addEventListener('click', () => { manual.showModal(); if (booted) say('MANUAL OPEN'); });
    manual.querySelector('.manual-close').addEventListener('click', () => manual.close());
    manual.addEventListener('click', event => { if (event.target === manual) manual.close(); });
  } else if (openManual) openManual.hidden = true;

  const overlay = $('#departure');
  const label = $('#departure-label');
  let transferTimer;
  function reset() { clearTimeout(transferTimer); leaving = false; overlay.hidden = true; document.body.classList.remove('departing'); finish(); }
  window.addEventListener('pageshow', event => { if (event.persisted) reset(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && leaving) reset(); });
  $('#departure-abort').addEventListener('click', reset);
  cards.forEach(card => card.addEventListener('click', event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || leaving) return;
    event.preventDefault(); finish(); leaving = true;
    const year = card.dataset.year; aim(year);
    $('#departure-year').textContent = year;
    const h = holds.find(x => x.year === year);
    const calibrating = h && h.calibrating;
    const final = calibrating ? `JUMPING TO ${year} · CALIBRATING, EXPECT GAPS` : `JUMPING TO ${year}`;
    label.textContent = reduced.matches ? final : 'SYNCING TIME MESH…';
    if (!reduced.matches) {
      later(400, () => { label.textContent = calibrating ? `MESH STABLE · HOLD ${Math.round(h.value)}%` : 'LOCK CONFIRMED · MATRIX STABLE'; });
      later(800, () => { label.textContent = final; });
    }
    $('#departure-link').href = card.href;
    overlay.hidden = false; document.body.classList.add('departing');
    try { sessionStorage.setItem('chicago4d.transfer', String(Date.now())); } catch {}
    transferTimer = setTimeout(() => location.assign(card.href), reduced.matches ? 0 : 1200);
  }));
})();
