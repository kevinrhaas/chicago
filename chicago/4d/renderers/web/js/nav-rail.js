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
 *     launch(ctx),                   // a stub: runs and docks the device — the drawer's
 *                                    // sections until they move in (T-2620)
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
  let current = null;
  let switching = 0;

  function makeButton(app) {
    const b = doc.createElement('button');
    b.type = 'button';
    b.className = 'nav-app';
    b.dataset.app = app.id;
    b.setAttribute('aria-label', app.label);
    b.setAttribute('aria-pressed', 'false');
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
      rail.insertBefore(s.button, before ?? null);
    }
  }

  function register(app) {
    if (!app?.id || !app.label) throw new Error('navigator.register needs at least { id, label }');
    if (apps.has(app.id)) throw new Error(`navigator.register: ${app.id} is already registered`);
    const ways = ['panel', 'load', 'mount', 'launch'].filter((k) => app[k]);
    if (ways.length !== 1 && !(ways.length === 2 && ways.includes('mount') && ways.includes('panel'))) {
      throw new Error(`navigator.register: ${app.id} needs exactly one of panel, load, mount or launch`);
    }
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
      el.setAttribute('role', 'group');
      el.setAttribute('aria-label', s.app.label);
      el.hidden = true;
      screens?.append(el);
      s.panel = el;
    }
    s.panel.dataset.app ??= s.app.id;
    return s.panel;
  }

  async function select(id, { by = 'code' } = {}) {
    const s = apps.get(id);
    if (!s) return false;
    const ctx = context();
    if (s.app.when && !seen.has(id)) { seen.add(id); writeSeen(storage, seen); }
    s.button.classList.remove('is-new');
    if (s.app.launch) {
      onLaunch(id, by);
      await s.app.launch(ctx);
      return true;
    }
    const ticket = ++switching;
    const panel = panelFor(s);
    if (!s.mounted) {
      if (s.app.load) {
        const mod = await s.app.load();
        s.module = mod?.default ?? mod;
      }
      if (ticket !== switching) return false; // a later choice won the race
      await (s.module ?? s.app).mount?.(panel, ctx);
      s.mounted = true;
    }
    const was = current;
    current = id;
    for (const other of apps.values()) {
      const on = other.app.id === id;
      other.button.classList.toggle('is-on', on);
      other.button.setAttribute('aria-pressed', String(on));
      if (other.panel) other.panel.hidden = !on;
    }
    if (codeEl && s.app.code) codeEl.textContent = s.app.code;
    if (was !== id && was !== null) warm(panel);
    onOpen(id, by);
    (s.module ?? s.app).shown?.(panel, ctx);
    return true;
  }

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
    get current() { return current; },
    has: (id) => apps.has(id),
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
