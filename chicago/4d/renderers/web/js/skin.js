/* Classic, tiny head script: share the machine (interface skin) across portal and renderer before paint.
   Four machines (T-2036). The three earlier skins migrate: scifi → control-room,
   spaceage → worlds-fair, steampunk → brass. */
(() => {
  // T-2656: `tile` is each machine's own panel, ink, accent and signal in its own tone
  // (css/skins.css), so its Settings tile is a small preview of it. tools/test_settings_app.mjs
  // holds them equal to skins.css.
  const MACHINES = [
    { id: 'control-room', name: 'Control Room', tone: 'dark', tile: ['#12233F', '#ECE6D8', '#8CF5A8', '#D6352B'] },
    { id: 'brass', name: 'Precision Brass', tone: 'dark', tile: ['#2A1E15', '#F4E6CD', '#F2B154', '#D4A85A'] },
    { id: 'worlds-fair', name: 'Retro Future', tone: 'light', tile: ['#F8F4EA', '#1E3A3D', '#138A92', '#EC6A1E'] },
    { id: 'deep-space', name: 'Deep Space', tone: 'dark', tile: ['#11141A', '#E4E2DC', '#7AD7F6', '#F5A742'] },
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
  // T-2615: a page opened within 10 s of the Observatory's transfer stamp is the far end
  // of that jump, so the arrival opens with the portal's ring still expanding (skins.css).
  // A direct visit, or one after 10 s, has no stamp young enough and opens plain.
  try { const age = Date.now() - Number(sessionStorage.getItem('chicago4d.transfer')); if (age >= 0 && age < 10000) root.dataset.transfer = 'true'; } catch {}
  // T-2735: the way home mirrors it. A page opened within 10 s of a recall stamp is the
  // Observatory end of the trip back, and opens on the reverse ring's last contraction. The
  // stamp is spent here, so a reload does not replay it.
  try { const age = Date.now() - Number(sessionStorage.getItem('chicago4d.recall')); if (age >= 0 && age < 10000) { root.dataset.recall = 'true'; sessionStorage.removeItem('chicago4d.recall'); } } catch {}

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
    document.querySelectorAll('.skin-tile').forEach(t => {
      const on = t.dataset.skinChoice === skin;
      t.classList.toggle('is-on', on); t.setAttribute('aria-checked', String(on)); t.tabIndex = on ? 0 : -1;
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
    // T-2656: Settings › Machine, the four machines as preview tiles.
    const t = event.target.closest && event.target.closest('.skin-tile');
    if (t) apply(t.dataset.skinChoice);
  });
  // The tiles are a radio group: the arrow keys move the choice along it.
  document.addEventListener('keydown', event => {
    const t = event.target.closest && event.target.closest('.skin-tile');
    const step = t && { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[event.key];
    if (!step) return;
    event.preventDefault();
    const next = keys[(keys.indexOf(t.dataset.skinChoice) + step + keys.length) % keys.length];
    apply(next);
    const host = t.parentElement; const b = host && host.querySelector(`[data-skin-choice="${next}"]`); if (b) b.focus();
  });
  // One tile: the machine's panel, painted in its own colours, with its accent bar and
  // signal key, and its name in its own ink.
  function tiles(host) {
    for (const m of MACHINES) {
      const [panel, ink, accent, signal] = m.tile;
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'skin-tile'; b.dataset.skinChoice = m.id;
      b.setAttribute('role', 'radio'); b.setAttribute('aria-checked', 'false');
      const face = document.createElement('span'); face.className = 'skin-tile-face'; face.setAttribute('aria-hidden', 'true');
      face.style.background = panel; face.style.color = ink;
      const bar = document.createElement('i'); bar.className = 'skin-tile-bar'; bar.style.background = accent;
      const key = document.createElement('i'); key.className = 'skin-tile-key'; key.style.background = signal;
      const lines = document.createElement('i'); lines.className = 'skin-tile-lines';
      face.append(bar, lines, key);
      const name = document.createElement('span'); name.className = 'skin-tile-name'; name.textContent = m.name;
      b.append(face, name); host.append(b);
    }
  }
  // T-2164: mount as soon as the document is parsed ('interactive'), not at
  // DOMContentLoaded — on a page with module scripts that waits for the whole module
  // graph, so on a slow link the arrival card grew a row seconds after first paint.
  let mounted = false;
  const mount = () => {
    if (mounted || document.readyState === 'loading') return;
    mounted = true;
    const card = document.querySelector('.gate-card');
    if (card && !card.querySelector('.skin-tools')) {
      const tools = document.createElement('div'); tools.className = 'skin-tools';
      const home = document.createElement('a'); home.href = new URL('../', document.baseURI).href; home.textContent = '← All destinations';
      tools.append(home, dial()); card.append(tools);
    }
    // T-2656: the renderer's Settings shows the machines as tiles; a page without that
    // group (none today) keeps the dial at the top of its settings.
    const skinTiles = document.getElementById('s-skins');
    const settings = document.querySelector('[data-panel="settings"]');
    if (skinTiles) { if (!skinTiles.children.length) tiles(skinTiles); } else if (settings) {
      const group = document.createElement('div'); group.className = 'settings-group skin-tools';
      const label = document.createElement('p'); label.className = 'skin-tools-label'; label.textContent = 'Appearance';
      group.append(label, dial()); settings.prepend(group);
    }
    sync();
  };
  document.addEventListener('readystatechange', mount);
  document.addEventListener('DOMContentLoaded', mount);
})();
