/* Classic, tiny head script: share the machine (interface skin) across portal and renderer before paint.
   Four machines (T-2036). The three earlier skins migrate: scifi → control-room,
   spaceage → worlds-fair, steampunk → brass. */
(() => {
  const MACHINES = [
    { id: 'control-room', name: '1960s Control Room', swatch: ['#ECE6D8', '#1E3A66', '#D6352B', '#8CF5A8'], tone: 'dark' },
    { id: 'brass', name: 'Precision Brass', swatch: ['#F4E6CD', '#D4A85A', '#3A2416', '#3F8F7F'], tone: 'dark' },
    { id: 'worlds-fair', name: 'World’s Fair', swatch: ['#EFE9DC', '#138A92', '#EC6A1E', '#363A3B'], tone: 'light' },
    { id: 'deep-space', name: 'Deep Space', swatch: ['#E4E2DC', '#7AD7F6', '#F5A742', '#07090C'], tone: 'dark' },
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

  function sync() {
    document.querySelectorAll('.machine[data-machine]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.machine === skin)));
  }
  function apply(value) {
    if (!keys.includes(value)) return;
    skin = value;
    root.dataset.skin = value;
    root.dataset.theme = toneOf(value);
    try { localStorage.setItem('chicago4d.theme', toneOf(value)); localStorage.setItem('chicago4d.skin', value); } catch {}
    sync();
  }
  // A machine selector: one pressed button per machine. Pages may ship the markup
  // (the portal does, so it shows without JavaScript); otherwise it is built here.
  function selector() {
    const group = document.createElement('div');
    group.className = 'machines'; group.setAttribute('role', 'group'); group.setAttribute('aria-label', 'Machine');
    for (const m of MACHINES) {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'machine'; b.dataset.machine = m.id; b.title = m.name; b.setAttribute('aria-label', m.name);
      const sw = document.createElement('span'); sw.className = 'machine-swatch'; sw.setAttribute('aria-hidden', 'true');
      for (const c of m.swatch) { const s = document.createElement('span'); s.style.background = c; sw.append(s); }
      const name = document.createElement('span'); name.className = 'machine-name'; name.textContent = m.name;
      b.append(sw, name); group.append(b);
    }
    return group;
  }
  document.addEventListener('click', event => {
    const b = event.target.closest && event.target.closest('.machine[data-machine]');
    if (b) apply(b.dataset.machine);
  });
  document.addEventListener('DOMContentLoaded', () => {
    const card = document.querySelector('.gate-card');
    if (card && !card.querySelector('.skin-tools')) {
      const tools = document.createElement('div'); tools.className = 'skin-tools';
      const home = document.createElement('a'); home.href = new URL('../', document.baseURI).href; home.textContent = '← All coordinates';
      tools.append(selector(), home); card.append(tools);
    }
    const settings = document.querySelector('[data-panel="settings"]');
    if (settings) {
      const group = document.createElement('div'); group.className = 'settings-group skin-tools';
      const label = document.createElement('p'); label.className = 'skin-tools-label'; label.textContent = 'Machine';
      group.append(label, selector()); settings.prepend(group);
    }
    sync();
  });
})();
