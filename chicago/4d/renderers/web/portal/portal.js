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
  const count = document.querySelector('.scan-count');
  const cards = [...document.querySelectorAll('.era')];
  const stages = ['Locating temporal signatures…','1835 · River settlement isolated','1904 · Prairie Avenue isolated','Three periods temporally isolated.'];
  let timers = [];
  function finish() { timers.forEach(clearTimeout); cards.forEach(c => c.classList.add('resolved'));status.textContent=stages[3];count.textContent='03 / 03';document.body.classList.add('resolved'); }
  if (!reduced.matches) {
    document.body.classList.add('acquiring');status.textContent=stages[0];count.textContent='00 / 03';
    cards.forEach((card,i) => timers.push(setTimeout(() => {card.classList.add('resolved');status.textContent=stages[i+1];count.textContent=`0${i+1} / 03`;},450+i*420)));
    timers.push(setTimeout(finish,1800));
  } else finish();
  reduced.addEventListener('change', finish);
  cards.forEach(card => card.addEventListener('focus', () => card.classList.add('resolved')));
  const overlay = document.getElementById('departure');
  let leaving = false;
  function reset() { leaving=false;overlay.hidden=true;document.body.classList.remove('departing');finish(); }
  window.addEventListener('pageshow', event => {if(event.persisted) reset();});
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && leaving) {clearTimeout(transferTimer);reset();} });
  let transferTimer;
  cards.forEach(card => card.addEventListener('click', event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || leaving) return;
    event.preventDefault(); leaving=true; finish();
    const year=card.dataset.year;
    document.getElementById('departure-year').textContent=year;
    document.getElementById('departure-label').textContent=year==='1812'?'Opening reconstruction status…':'Destination isolated. Crossing the interval…';
    document.getElementById('departure-link').href=card.href;
    overlay.hidden=false;document.body.classList.add('departing');
    try {sessionStorage.setItem('chicago4d.transfer',String(Date.now()));} catch {}
    transferTimer=setTimeout(()=>location.assign(card.href),reduced.matches?0:1000);
  }));
})();
