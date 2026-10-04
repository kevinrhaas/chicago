/* Classic, tiny head script: share the machine (interface skin) across portal and renderer before paint.
   Four machines (T-2036). The three earlier skins migrate: scifi → control-room,
   spaceage → worlds-fair, steampunk → brass. */
(() => {
  const MACHINES = [
    { id: 'control-room', name: 'Control Room', tone: 'dark' },
    { id: 'brass', name: 'Precision Brass', tone: 'dark' },
    { id: 'worlds-fair', name: 'Retro Future', tone: 'light' },
    { id: 'deep-space', name: 'Deep Space', tone: 'dark' },
  ];
  const LEGACY = { scifi: 'control-room', spaceage: 'worlds-fair', steampunk: 'brass' };
  const keys = MACHINES.map(m => m.id);
  const toneOf = id => MACHINES.find(m => m.id === id).tone;
  const root = document.documentElement;
  let skin = 'control-room';
  try {
    let saved = localStorage.getItem('chicago4d.skin');
    if (LEGACY[saved]) { saved = LEGACY[saved]; localStorage.setItem('chicago4d.skin', saved); }
    if (keys.includes(saved)) skin = saved;
  } catch {}
  root.dataset.skin = skin;
  try { root.dataset.theme = localStorage.getItem('chicago4d.theme') || toneOf(skin); } catch { root.dataset.theme = toneOf(skin); }
  try { if (Number(sessionStorage.getItem('chicago4d.transfer')) > Date.now() - 15000) root.dataset.transfer = 'true'; } catch {}

  // The appearance dial: one small button that steps to the next machine, its hand
  // turning a quarter each step and a row of dots marking which of the four is on.
  // Deliberately quiet (T-2057): it should not draw the eye from the page it sits on.
  function sync() {
    const i = keys.indexOf(skin), name = MACHINES[i].name;
    document.querySelectorAll('.machine-dial').forEach(d => {
      d.style.setProperty('--turn', `${i * 90}deg`);
      d.setAttribute('aria-label', `Appearance: ${name}. Change appearance`);
      d.title = `Appearance: ${name}`;
      d.querySelectorAll('.machine-dots i').forEach((dot, j) => dot.classList.toggle('on', j === i));
      const label = d.querySelector('.machine-dial-name'); if (label) label.textContent = name;
    });
  }
  function apply(value) {
    if (!keys.includes(value)) return;
    skin = value;
    root.dataset.skin = value;
    root.dataset.theme = toneOf(value);
    try { localStorage.setItem('chicago4d.theme', toneOf(value)); localStorage.setItem('chicago4d.skin', value); } catch {}
    sync();
  }
  // Pages may ship the dial's markup (the portal does); otherwise it is built here.
  function dial() {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'machine-dial';
    b.innerHTML = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true"><circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor"/><path class="machine-dial-hand" d="M8 8V3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
      + '<span class="machine-dots" aria-hidden="true">' + MACHINES.map(() => '<i></i>').join('') + '</span><span class="machine-dial-name"></span>';
    return b;
  }
  document.addEventListener('click', event => {
    const d = event.target.closest && event.target.closest('.machine-dial');
    if (d) apply(keys[(keys.indexOf(skin) + 1) % keys.length]);
  });
  document.addEventListener('DOMContentLoaded', () => {
    const card = document.querySelector('.gate-card');
    if (card && !card.querySelector('.skin-tools')) {
      const tools = document.createElement('div'); tools.className = 'skin-tools';
      const home = document.createElement('a'); home.href = new URL('../', document.baseURI).href; home.textContent = '← All coordinates';
      tools.append(home, dial()); card.append(tools);
    }
    const settings = document.querySelector('[data-panel="settings"]');
    if (settings) {
      const group = document.createElement('div'); group.className = 'settings-group skin-tools';
      const label = document.createElement('p'); label.className = 'skin-tools-label'; label.textContent = 'Appearance';
      group.append(label, dial()); settings.prepend(group);
    }
    sync();
  });
})();
