(() => {
  // Preserve the old explicit root deep links, including spawn, jaunt and structure parameters.
  const params = new URLSearchParams(location.search);
  if ([...params.keys()].some(key => !['skin','utm_source','utm_medium','utm_campaign'].includes(key))) {
    const year = /^\d{4}$/.test(params.get('year') || '') ? params.get('year') : '1835';
    location.replace(new URL(`${year}/${location.search}${location.hash}`, location.href).href);
    return;
  }
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const status = document.getElementById('scan-status');
  const station = document.getElementById('station-status');
  const count = document.querySelector('.scan-count');
  const cards = [...document.querySelectorAll('.era')];
  const states = cards.map(card => card.querySelector('.era-state'));
  const settled = states.map(s => s && s.lastChild.textContent);
  const stages = ['Sweeping the interval…','1835 · signature resolved at the forks','1904 · Prairie Avenue resolved','Three coordinates resolved. Field nominal.'];
  let timers = [];
  function setState(i, text) { const s = states[i]; if (s) s.lastChild.textContent = text; }
  function finish() {
    timers.forEach(clearTimeout);
    cards.forEach((c, i) => { c.classList.add('resolved'); setState(i, settled[i]); });
    status.textContent = stages[3]; count.textContent = '03 / 03'; station.textContent = 'FIELD NOMINAL';
    document.body.classList.remove('acquiring'); document.body.classList.add('resolved');
  }
  if (!reduced.matches) {
    document.body.classList.add('acquiring'); status.textContent = stages[0]; count.textContent = '00 / 03'; station.textContent = 'ACQUIRING';
    cards.forEach((card, i) => { if (!card.classList.contains('era-pending')) setState(i, 'RESOLVING…'); });
    cards.forEach((card, i) => timers.push(setTimeout(() => {
      card.classList.add('resolved'); setState(i, settled[i]);
      status.textContent = stages[Math.min(i + 1, 3)]; count.textContent = `0${i + 1} / 03`;
      if (i === cards.length - 1) finish();
    }, 500 + i * 450)));
  } else finish();
  reduced.addEventListener('change', finish);
  cards.forEach(card => card.addEventListener('focus', () => card.classList.add('resolved')));

  const overlay = document.getElementById('departure');
  const label = document.getElementById('departure-label');
  let leaving = false, transferTimer;
  function reset() { clearTimeout(transferTimer); leaving = false; overlay.hidden = true; document.body.classList.remove('departing'); finish(); }
  window.addEventListener('pageshow', event => { if (event.persisted) reset(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && leaving) reset(); });
  document.getElementById('departure-abort').addEventListener('click', reset);
  cards.forEach(card => card.addEventListener('click', event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || leaving) return;
    event.preventDefault(); leaving = true; finish();
    const year = card.dataset.year;
    document.getElementById('departure-year').textContent = year;
    label.textContent = card.classList.contains('era-pending')
      ? 'Signature acquired. Opening the survey status…'
      : 'Coordinate locked. Breaching the interval — mind the gap between centuries.';
    document.getElementById('departure-link').href = card.href;
    overlay.hidden = false; document.body.classList.add('departing');
    try { sessionStorage.setItem('chicago4d.transfer', String(Date.now())); } catch {}
    transferTimer = setTimeout(() => location.assign(card.href), reduced.matches ? 0 : 1200);
  }));
})();
