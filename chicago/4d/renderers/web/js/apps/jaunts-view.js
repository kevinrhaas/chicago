/**
 * Jaunts (SCR 02), loaded the first time it opens (T-2630; DESIGN §07 "Jaunts", M5).
 *
 * Three segments — Jaunts · Go to · Free roam — the arrival's Home choices, in the
 * device. They are not a second copy of anything: the Jaunts list and the Go to search
 * are the Welcome card's own (the jaunt preview's list, #welcome-jaunts-content, and the
 * destination search, #welcome-picker), lent to this screen while it shows them and handed
 * back, ids and listeners intact, the moment the Welcome card is shown again (main.js
 * calls restore() from welcome.show). The Welcome card keeps its three choices.
 *
 * Free roam pockets the Navigator: it docks the device (its one-time tip is T-2634).
 * The segment control is a tablist; the rail, the Navigator Home's choices and a deep
 * link can each open a given segment (`segment(name)`).
 */

export const SEGMENTS = [
  { id: 'jaunts', label: 'Jaunts' },
  { id: 'goto', label: 'Go to' },
  { id: 'roam', label: 'Free roam' },
];

let view = null;

/** Lend a node to `into`, remembering where it lives, so restore() can hand it back. */
function lend(node, into, lent) {
  if (!node || !into || node.parentNode === into) return;
  if (!lent.has(node)) lent.set(node, { parent: node.parentNode, next: node.nextSibling });
  into.append(node);
}

export function mount(el, ctx = {}) {
  const doc = el.ownerDocument;
  el.replaceChildren();
  const lent = new Map();
  const tabs = doc.createElement('div');
  tabs.className = 'nav-segments';
  tabs.setAttribute('role', 'tablist');
  tabs.setAttribute('aria-label', 'Jaunts, Go to or Free roam');
  const panels = {};
  const buttons = {};
  for (const s of SEGMENTS) {
    const b = doc.createElement('button');
    b.type = 'button';
    b.className = 'nav-segment';
    b.id = `nav-seg-${s.id}`;
    b.dataset.segment = s.id;
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-selected', 'false');
    b.setAttribute('aria-controls', `nav-seg-panel-${s.id}`);
    b.tabIndex = -1;
    b.textContent = s.label;
    b.addEventListener('click', () => show(s.id, { by: 'hand' }));
    tabs.append(b);
    buttons[s.id] = b;
    const p = doc.createElement('div');
    p.className = 'nav-seg-panel';
    p.id = `nav-seg-panel-${s.id}`;
    p.setAttribute('role', 'tabpanel');
    p.setAttribute('aria-labelledby', b.id);
    p.hidden = true;
    panels[s.id] = p;
  }
  tabs.addEventListener('keydown', (e) => {
    const order = SEGMENTS.map((s) => s.id);
    const at = order.indexOf(e.target?.dataset?.segment);
    if (at < 0) return;
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (!step) return;
    e.preventDefault();
    show(order[(at + step + order.length) % order.length], { by: 'hand' });
    buttons[view.current]?.focus?.();
  });

  // Free roam: a line and the key that pockets the device.
  const roamText = doc.createElement('p');
  roamText.className = 'nav-sub nav-roam-line';
  roamText.textContent = 'Pocket the Navigator and wander the town on your own.';
  const roamKey = doc.createElement('button');
  roamKey.type = 'button';
  roamKey.className = 'nav-key nav-roam';
  roamKey.textContent = 'Free roam';
  roamKey.addEventListener('click', () => ctx.actions?.freeRoam?.() ?? ctx.navigator?.dock?.());
  panels.roam.append(roamText, roamKey);

  el.append(tabs, ...Object.values(panels));

  function show(id, { by = 'code' } = {}) {
    if (!panels[id]) return false;
    for (const s of SEGMENTS) {
      const on = s.id === id;
      buttons[s.id].setAttribute('aria-selected', String(on));
      buttons[s.id].tabIndex = on ? 0 : -1;
      buttons[s.id].classList.toggle('is-on', on);
      panels[s.id].hidden = !on;
    }
    view.current = id;
    if (id === 'jaunts') {
      lend(doc.getElementById('welcome-jaunts-content'), panels.jaunts, lent);
      ctx.actions?.jauntList?.();
    } else if (id === 'goto') {
      const picker = doc.getElementById('welcome-picker');
      lend(picker, panels.goto, lent);
      if (picker) picker.hidden = false;
      ctx.actions?.gotoList?.();
      if (by === 'hand') doc.getElementById('welcome-search')?.focus?.({ preventScroll: true });
    }
    return true;
  }

  /** Hand every lent node back to the Welcome card, where it lives. */
  function restore() {
    for (const [node, { parent, next }] of lent) {
      if (!parent) continue;
      if (next && next.parentNode === parent) parent.insertBefore(node, next); else parent.append(node);
      if (node.id === 'welcome-picker') node.hidden = true;
    }
    lent.clear();
  }

  view = { current: 'jaunts', segment: show, restore, get lent() { return lent.size; } };
  if (ctx.api) ctx.api.jauntsApp = view;
  show('jaunts');
}

/** Each time the app is opened (the rail, a Home choice): show its current segment again,
 * so a list the Welcome card took back is lent to it anew. */
export function shown(el, ctx = {}) {
  if (!view) return;
  if (ctx.api) ctx.api.jauntsApp = view;
  view.segment(view.current);
}

export function unmount(el) {
  view?.restore();
  view = null;
  el.replaceChildren();
}
