/**
 * nav-rail.js — the Navigator's app registry and its contextual rail (T-2618,
 * NAV-202; DESIGN §06 "The rail: when each app shows", §14 "App registry").
 *
 * An app is one object, and each lives in its own file under js/apps/, so a lane
 * adds or grows its app without touching this file or navigator.js:
 *
 *   {
 *     id: 'inspect',                 // also data-app on its rail button and its panel
 *     label: 'Inspect',              // the button's name (aria-label, title)
 *     code: 'SCR 03 · INSPECT',      // the screen header while it is open
 *     icon: '<svg …>',               // a 24-unit, stroke="currentColor" icon (static markup)
 *     order: 20,                     // place in the rail, low first
 *     pin: 'bottom',                 // optional: Guide and Settings sit at the rail's foot
 *     when: (ctx) => bool,           // optional: absent means always
 *     linger: 300,                   // optional: ms an app stays after `when` turns false
 *     badge: (ctx) => bool,          // optional: a lamp dot (e.g. unread What's new)
 *     glow: (ctx) => bool,           // optional: the icon glows (the Confidence view is on)
 *     // Then ONE of:
 *     panel: 'nav-home',             // an element already in the page (Home)
 *     load: () => import('./x.js'),  // lazy: a module whose default (or itself) has
 *                                    // mount(el, ctx) and unmount(el, ctx), loaded on first open
 *     mount(el, ctx), unmount(el, ctx), // eager, for something tiny
 *     shown(el, ctx), hidden(el, ctx), // optional, on the app or its module: each time its
 *                                    // screen comes into sight, and when it leaves (another
 *                                    // app opens, or the device docks) — T-2620's sections
 *     launch(ctx),                   // a stub: runs and docks the device — the drawer's
 *                                    // sections until they move in (T-2620). It may go with
 *                                    // a screen: returning false falls through to it.
 *   }
 *
 * The rail shows at most `max` (10) icons. Apps whose `when` turns true slide in
 * (240 ms, with a glint) in their order — contextual ones sit under Jaunts — and
 * the first time a contextual app ever appears it carries a lamp-amber dot until it
 * is opened (remembered per visitor; storage refused, it is simply shown again).
 * Opening an app switches the screen with a 160 ms "tube warm-up" (a scanline sweep
 * and a header flicker); with reduced motion, a plain crossfade. `ctx` is whatever
 * the device's `context()` returns at that moment, so an app reads the page through
 * it and never imports main.js.
 */
export const MAX_ICONS = 10;
export const SLIDE_MS = 240;
export const WARM_MS = 160;
const SEEN_KEY = 'chicago4d.navigator.seen';

/** Rail order: the top group by `order`, then the pinned foot by `order`. */
export function railOrder(apps) {
  const key = (a) => [a.pin === 'bottom' ? 1 : 0, a.order ?? 50, a.id];
  return [...apps].sort((a, b) => {
    const ka = key(a), kb = key(b);
    return ka[0] - kb[0] || ka[1] - kb[1] || String(ka[2]).localeCompare(String(kb[2]));
  });
}

/**
 * Which apps show, given who wants to: at most `max`, and when there are more, the
 * always-on and pinned ones keep their place and the latest contextual ones in
 * order give way.
 */
export function capped(ordered, wants, max = MAX_ICONS) {
  const on = ordered.filter((a) => wants.get(a.id));
  if (on.length <= max) return new Set(on.map((a) => a.id));
  const keep = new Set(on.filter((a) => !a.when || a.pin === 'bottom').map((a) => a.id));
  for (const a of on) {
    if (keep.size >= max) break;
    keep.add(a.id);
  }
  return keep;
}

function readSeen(storage) {
  try { return new Set(JSON.parse(storage?.getItem(SEEN_KEY) ?? '[]')); } catch { return new Set(); }
}
function writeSeen(storage, seen) {
  try { storage?.setItem(SEEN_KEY, JSON.stringify([...seen])); } catch { /* a convenience */ }
}

export function createRail({
  rail,
  screens,
  codeEl = null,
  doc = rail?.ownerDocument ?? globalThis.document,
  context = () => ({}),
  before = null,                 // the element new buttons go in front of (the collapse key)
  onOpen = () => {},             // the device opens to show an app's screen
  onLaunch = () => {},           // a launch stub ran: the device docks
  reduced = () => globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false,
  storage = (() => { try { return globalThis.localStorage; } catch { return null; } })(),
  now = () => (globalThis.performance?.now?.() ?? Date.now()),
  wait = (fn, ms) => setTimeout(fn, ms),
  max = MAX_ICONS,
} = {}) {
  const apps = new Map(); // id → { app, button, shown, leaveAt, panel, mounted, module }
  const seen = readSeen(storage);
  // T-2622 (§14 Accessibility): the rail is a tablist and each app a tab of it, its
  // screen a tabpanel. The tabs sit in a wrapper of their own (display: contents, so the
  // rail lays them out as before), because the rail also holds the collapse key, and a
  // tablist may own nothing but tabs.
  const list = rail ? (rail.querySelector?.('.nav-tabs') ?? (() => {
    const el = doc.createElement('div');
    el.className = 'nav-tabs';
    el.setAttribute('role', 'tablist');
    el.setAttribute('aria-label', rail.getAttribute?.('aria-label') || 'Navigator apps');
    el.setAttribute('aria-orientation', 'vertical');
    rail.insertBefore(el, before ?? null);
    return el;
  })()) : null;
  let current = null;
  let switching = 0;

  function makeButton(app) {
    const b = doc.createElement('button');
    b.type = 'button';
    b.className = 'nav-app';
    b.dataset.app = app.id;
    b.id = `nav-tab-${app.id}`;
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-label', app.label);
    b.setAttribute('aria-selected', 'false');
    // Roving focus: Tab reaches the rail once, at the open app; the arrows move along it.
    b.tabIndex = -1;
    b.title = app.label;
    if (app.pin === 'bottom') b.classList.add('nav-app-foot');
    if (typeof app.icon === 'string') b.insertAdjacentHTML?.('beforeend', app.icon);
    else if (app.icon) b.append(app.icon);
    const dot = doc.createElement('span');
    dot.className = 'nav-app-dot';
    dot.setAttribute('aria-hidden', 'true');
    b.append(dot);
    b.hidden = !!app.when;
    b.addEventListener('click', () => { void select(app.id, { by: 'hand' }); });
    return b;
  }

  function place() {
    if (!rail) return;
    const order = railOrder([...apps.values()].map((s) => s.app));
    let firstFoot = true;
    for (const app of order) {
      const s = apps.get(app.id);
      s.button.classList.toggle('nav-app-foot-first', app.pin === 'bottom' && firstFoot);
      if (app.pin === 'bottom') firstFoot = false;
      list.append(s.button);
    }
  }

  function register(app) {
    if (!app?.id || !app.label) throw new Error('navigator.register needs at least { id, label }');
    if (apps.has(app.id)) throw new Error(`navigator.register: ${app.id} is already registered`);
    // One way to show it — a panel, a lazy module or an eager mount — and/or a launch; a
    // launch that returns false falls through to the screen (People: the drawer in 1835,
    // its own screen in 1904).
    const screens = ['panel', 'load', 'mount'].filter((k) => app[k]);
    const bad = app.panel && app.load ? true : screens.length > 2 || (!screens.length && !app.launch) || (app.load && app.mount);
    if (bad) throw new Error(`navigator.register: ${app.id} needs one of panel, load or mount, or a launch`);
    const s = { app, button: makeButton(app), shown: !app.when, leaveAt: null, panel: null, mounted: false, module: null };
    apps.set(app.id, s);
    place();
    return () => unregister(app.id);
  }

  function unregister(id) {
    const s = apps.get(id);
    if (!s) return false;
    if (s.mounted) (s.module ?? s.app).unmount?.(s.panel, context());
    s.button.remove?.();
    if (s.panel && !s.app.panel) s.panel.remove?.();
    apps.delete(id);
    if (current === id) current = null;
    return true;
  }

  function slide(s, on) {
    const b = s.button;
    b.classList.remove('is-entering', 'is-leaving');
    if (on) {
      b.hidden = false;
      if (!reduced()) {
        b.classList.add('is-entering');
        wait(() => b.classList.remove('is-entering'), SLIDE_MS);
      }
      if (s.app.when && !seen.has(s.app.id)) b.classList.add('is-new');
    } else if (reduced()) {
      b.hidden = true;
    } else {
      b.classList.add('is-leaving');
      wait(() => { if (!s.shown) { b.hidden = true; b.classList.remove('is-leaving'); } }, SLIDE_MS);
    }
  }

  /** Re-read every app's `when`, `badge` and `glow`; slide the changes in and out. */
  function evaluate(t = now()) {
    const ctx = context();
    const wants = new Map();
    for (const s of apps.values()) {
      let want = true;
      if (s.app.when) {
        try { want = !!s.app.when(ctx); } catch { want = false; }
      }
      if (want) s.leaveAt = null;
      else if (s.shown && s.app.linger) {
        s.leaveAt ??= t + s.app.linger;
        if (t < s.leaveAt) want = true;
      }
      wants.set(s.app.id, want);
    }
    const order = railOrder([...apps.values()].map((s) => s.app));
    const show = capped(order, wants, max);
    for (const s of apps.values()) {
      const on = show.has(s.app.id);
      if (on !== s.shown) { s.shown = on; if (!on) s.leaveAt = null; slide(s, on); }
      let badge = false, glow = false;
      try { badge = !!s.app.badge?.(ctx); } catch { /* a badge is decoration */ }
      try { glow = !!s.app.glow?.(ctx); } catch { /* so is a glow */ }
      s.button.classList.toggle('is-badged', badge);
      s.button.classList.toggle('is-glowing', glow);
    }
    // An open app whose `when` let go closes back to Home.
    if (current && !apps.get(current)?.shown && apps.has('home')) void select('home', { by: 'quiet' });
    return [...show];
  }

  function panelFor(s) {
    if (s.panel) return s.panel;
    if (s.app.panel) s.panel = doc.getElementById?.(s.app.panel) ?? screens?.querySelector?.(`#${s.app.panel}`) ?? null;
    if (!s.panel) {
      const el = doc.createElement('div');
      el.className = 'nav-screen';
      el.id = `nav-app-${s.app.id}`;
      el.dataset.app = s.app.id;
      el.setAttribute('role', 'tabpanel');
      el.setAttribute('aria-labelledby', s.button.id);
      // Focus moves into the app on open (navigator.js), so its screen takes focus.
      el.tabIndex = -1;
      el.hidden = true;
      screens?.append(el);
      s.panel = el;
    }
    s.panel.dataset.app ??= s.app.id;
    if (s.panel.getAttribute?.('role') !== 'tabpanel') s.panel.setAttribute?.('role', 'tabpanel');
    if (s.panel.id) s.button.setAttribute('aria-controls', s.panel.id);
    return s.panel;
  }

  async function select(id, { by = 'code' } = {}) {
    const s = apps.get(id);
    if (!s) return false;
    const ctx = context();
    if (s.app.when && !seen.has(id)) { seen.add(id); writeSeen(storage, seen); }
    s.button.classList.remove('is-new');
    // Await only what is asynchronous: an app already mounted (or mounted synchronously)
    // switches in the same task, so a caller can focus into it at once (G and Go to).
    const settle = (v) => (v && typeof v.then === 'function' ? v : null);
    if (s.app.launch) {
      let handled = s.app.launch(ctx);
      if (settle(handled)) handled = await handled;
      if (handled !== false) { onLaunch(id, by); return true; }
      if (!s.app.panel && !s.app.load && !s.app.mount) return false;
    }
    const ticket = ++switching;
    const panel = panelFor(s);
    if (!s.mounted) {
      if (s.app.load) {
        const mod = await s.app.load();
        s.module = mod?.default ?? mod;
      }
      if (ticket !== switching) return false; // a later choice won the race
      const mounting = settle((s.module ?? s.app).mount?.(panel, ctx));
      if (mounting) await mounting;
      s.mounted = true;
      if (ticket !== switching) return false;
    }
    const was = current;
    const prev = was && was !== id ? apps.get(was) : null;
    if (prev?.mounted) (prev.module ?? prev.app).hidden?.(prev.panel, ctx);
    current = id;
    for (const other of apps.values()) {
      const on = other.app.id === id;
      other.button.classList.toggle('is-on', on);
      other.button.setAttribute('aria-selected', String(on));
      other.button.tabIndex = on ? 0 : -1;
      if (other.panel) other.panel.hidden = !on;
    }
    if (codeEl && s.app.code) codeEl.textContent = s.app.code;
    if (was !== id && was !== null) warm(panel);
    onOpen(id, by);
    (s.module ?? s.app).shown?.(panel, ctx);
    return true;
  }

  /** The device's screen went out of sight (docked, or down to its rail) or came back. */
  let visible = true;
  function setVisible(on) {
    if (on === visible) return;
    visible = on;
    const s = current ? apps.get(current) : null;
    if (!s?.mounted) return;
    const ctx = context();
    if (on) (s.module ?? s.app).shown?.(s.panel, ctx);
    else (s.module ?? s.app).hidden?.(s.panel, ctx);
  }
  // The arrows move focus along the tabs that show (and Home and End to the ends);
  // Enter or Space opens one, as the button it is. Moving focus never opens an app on
  // its own: some apps are launches that dock the device.
  list?.addEventListener?.('keydown', (e) => {
    const tabs = railOrder([...apps.values()].map((s) => s.app)).map((a) => apps.get(a.id)).filter((s) => s.shown).map((s) => s.button);
    const at = tabs.indexOf(e.target);
    if (at < 0) return;
    const step = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[e.key];
    let next = null;
    if (step) next = tabs[(at + step + tabs.length) % tabs.length];
    else if (e.key === 'Home') next = tabs[0];
    else if (e.key === 'End') next = tabs.at(-1);
    if (!next) return;
    e.preventDefault();
    next.focus?.();
  });

  function warm(panel) {
    const cls = reduced() ? 'is-fading' : 'is-warming';
    panel.classList.remove('is-warming', 'is-fading');
    panel.classList.add(cls);
    codeEl?.classList?.add(cls);
    wait(() => { panel.classList.remove(cls); codeEl?.classList?.remove(cls); }, WARM_MS);
  }

  return {
    register,
    unregister,
    evaluate,
    select,
    setVisible,
    get current() { return current; },
    has: (id) => apps.has(id),
    /** The tab of an app, for the keyboard (navigator.js). */
    tab: (id) => apps.get(id)?.button ?? null,
    /** For the harness: what the rail shows, in order. */
    shown() {
      return railOrder([...apps.values()].map((s) => s.app)).filter((a) => apps.get(a.id).shown).map((a) => a.id);
    },
    snapshot() {
      return railOrder([...apps.values()].map((s) => s.app)).map((a) => {
        const s = apps.get(a.id);
        return { id: a.id, shown: s.shown, on: current === a.id, isNew: s.button.classList.contains('is-new'),
          badged: s.button.classList.contains('is-badged'), glowing: s.button.classList.contains('is-glowing') };
      });
    },
  };
}
