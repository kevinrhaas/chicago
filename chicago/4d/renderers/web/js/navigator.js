/**
 * navigator.js — the Navigator, the handheld that knows where you are (T-2617,
 * NAV-201; DESIGN §06, mockups M3 and M4).
 *
 * One device, two shapes, chosen by the width (the same 620 px line the drawer and
 * the card use):
 *
 *   phone    a bottom sheet with three heights — DOCK (64 px: the device's head and
 *            its grip), HALF (48 % of the screen, the world still in view above it, so
 *            you can keep walking), FULL (82 %, for reading). Drag the grip or the head
 *            and it snaps to the nearest height, or to the next one in the direction of
 *            a quick flick; tap the grip and it steps up a height, from FULL back to DOCK.
 *   desktop  a 400 px panel down the left edge that collapses to its rail.
 *
 * Home (SCR 01) is its one app so far: YOU ARE AT (the street, the way you face and the
 * scene's clock), RIGHT IN FRONT OF YOU (target.js, within 100 m, with the screen's one
 * signal-red key, Inspect), JAUNT IN PROGRESS when there is one, and MOVE and the
 * Confidence view, each a tile that opens its app (T-3021). The rail is the app registry (nav-rail.js, T-2618): every app,
 * Home included, is registered from its own file under js/apps/, and
 * `navigator.register(app)` adds one more.
 *
 * Every control is a plain <button>, so the gesture gate (T-2614) can hook the first
 * tap on any of them. Opening the device by hand moves focus into Home (DESIGN §14,
 * a non-modal region); nothing moves focus when the device docks itself. The device
 * reads its values once every half second, and only while Home is showing.
 */
import { t as str } from './strings/index.js';
import './strings/navigator.js';
import { facingWords, clockWords, screenDate } from './where.js';
import { mountTelemetry } from './nav-telemetry.js';
import { formatDistance } from './units.js';
import { displayName } from './display-name.js';
import { createRail } from './nav-rail.js';

export const PHONE_DETENTS = Object.freeze(['dock', 'half', 'full']);
export const DESK_DETENTS = Object.freeze(['rail', 'open']);
export const PHONE_MAX_PX = 620;
export const DOCK_PX = 64;
/** T-2619: the docked pill's width on a phone, and the bottom-left corner it keeps clear —
 * the touch stick's 116 px ring held against the left edge, plus an 8 px gutter — so a
 * resting left thumb walks instead of opening the device. 390 px leaves 127 px each side. */
export const DOCK_PILL_PX = 136;
export const JOYSTICK_CLEAR_PX = 124;

/** Where the docked pill stands on a phone `vw` px wide: centred, between `left` and `right`. */
export function dockPill(vw, width = DOCK_PILL_PX) {
  const left = Math.round((vw - width) / 2);
  return { left, right: left + width, width, clear: left >= JOYSTICK_CLEAR_PX };
}

/** The dock's year: the scene's own, from its date or its id. */
export function dockYear(scene = {}) {
  const m = /^(\d{4})/.exec(String(scene.target_date ?? scene.id ?? ''));
  return m ? m[1] : '';
}
const HALF = 0.48, FULL = 0.82;
/** RIGHT IN FRONT OF YOU: the building across the street, not only the one at your elbow. */
export const FRONT_M = 100;

/** The three heights of the sheet in pixels, for a screen `vh` pixels tall. */
export function detentHeights(vh) {
  return [DOCK_PX, Math.round(vh * HALF), Math.round(vh * FULL)];
}

/**
 * Where a drag lets go: the nearest height, unless the flick was quick (faster than
 * `flick` px/ms), in which case the next height in its direction from where the drag
 * started. `velocity` is upward-positive.
 */
export function snapLevel(height, velocity, heights, startLevel, flick = 0.45) {
  if (Math.abs(velocity) > flick) {
    const step = velocity > 0 ? 1 : -1;
    return Math.max(0, Math.min(heights.length - 1, startLevel + step));
  }
  let best = 0;
  for (let i = 1; i < heights.length; i++) if (Math.abs(heights[i] - height) < Math.abs(heights[best] - height)) best = i;
  return best;
}

/** A tap on the grip: up one height, and from the top back down to the dock. */
export function tapLevel(level, count = 3) { return level >= count - 1 ? 0 : level + 1; }

/** MOVE, in words. */
export function moveWords({ flying = false, pace = 'walk', riding = false } = {}) {
  if (flying) return str('nav.move.fly');
  const how = str(`nav.move.${pace}`, null, str('nav.move.walk'));
  return riding ? str('nav.move.riding', { how }) : how;
}

export function createNavigator({
  root,
  scene = {},
  target = null,
  where = null,
  pose = () => ({ e: 0, n: 0, bearingDeg: 0 }),
  jaunt = () => null,
  move = () => ({}),
  confidence = () => false,
  units = () => 'imperial',
  onInspect = () => {},
  apps = [],
  context = () => ({}),
  storage,
  isPhone = () => globalThis.matchMedia?.(`(max-width: ${PHONE_MAX_PX}px)`).matches ?? false,
  viewportHeight = () => globalThis.innerHeight ?? 780,
  now = () => (globalThis.performance?.now?.() ?? Date.now()),
  // T-2622: the keyboard. `keysActive` is false while the arrival gate is up; `escFree`
  // says no other surface (the drawer, a building card) is waiting for Escape.
  keysActive = () => true,
  escFree = () => true,
  keyTarget = root?.ownerDocument?.defaultView ?? globalThis,
} = {}) {
  if (!root) return null;
  const $ = (id) => root.querySelector(`#${id}`);
  const html = root.ownerDocument?.documentElement;
  const grip = $('nav-grip'), head = $('nav-head'), rail = $('nav-rail'), collapse = $('nav-collapse');
  const closeKey = $('nav-close');
  const title = $('nav-home-title');
  // T-2622: focus goes to Home's screen itself, which shows its focus ring; the heading
  // that names it is visually hidden, so focus on it would be invisible.
  const homeScreen = $('nav-home');
  if (homeScreen && homeScreen.getAttribute?.('tabindex') == null) homeScreen.tabIndex = -1;
  const focusTarget = (id) => (id && id !== 'home' ? root.querySelector(`#nav-app-${id}`) : homeScreen ?? title);
  const out = {
    where: $('nav-where'), whereDetail: $('nav-where-detail'),
    frontName: $('nav-front-name'), frontDetail: $('nav-front-detail'), inspect: $('nav-inspect'),
    jaunt: $('nav-jaunt'), jauntStep: $('nav-jaunt-step'), jauntTitle: $('nav-jaunt-title'), jauntBar: $('nav-jaunt-bar'),
    move: $('nav-move'), confidence: $('nav-confidence'),
  };
  const dateEl = $('nav-date');
  if (dateEl) dateEl.textContent = screenDate(scene.target_date);
  // T-2619: the closed device always shows its lamp, its label, the year and the icon of
  // the app it will open to (the last one opened; Home at first).
  const dockYearEl = $('nav-dock-year'), dockAppEl = $('nav-dock-app');
  if (dockYearEl) dockYearEl.textContent = dockYear(scene);
  let dockApp = null;
  const appButton = (id) => [...(rail?.querySelectorAll?.('.nav-app') ?? [])].find((b) => b.dataset?.app === id) ?? null;
  const appLabel = (id) => appButton(id)?.getAttribute?.('aria-label') ?? '';
  function paintDock(id = dockApp) {
    dockApp = id;
    const icon = id ? appButton(id)?.querySelector?.('svg') : null;
    if (dockAppEl) {
      dockAppEl.replaceChildren?.(...(icon ? [icon.cloneNode(true)] : []));
      if (dockAppEl.dataset) dockAppEl.dataset.app = id ?? '';
    }
    paintGrip();
  }
  const clock = clockWords(scene.lighting?.local_time);
  root.ownerDocument?.body?.classList.add('has-navigator');

  // ---- the rail: the app registry (T-2618) ----
  // `ctx` is the page's context (main.js) plus what only the device knows: the target
  // within 40 m (Inspect's rule), the shape it is in, and the device itself.
  let near = null;
  // T-2621: a deep link's { app, id, tab }, handed to the app it opens through ctx.link.
  // Until the dossier lands (T-2638), an Inspect link's building is offered as the one
  // selected, so Inspect's stub opens that building's card.
  // T-2627: while the rail is not looking (a docked phone), the page's own target — the
  // HUD's tag — stands in, so Inspect opened from the HUD knows what it was opened on.
  let link = null;
  const ctx = () => {
    const page = context();
    const linked = link?.app === 'inspect' && link.id ? { selected: link.id } : null;
    return { ...page, ...linked, link, target: near ?? page.target ?? null, isPhone: isPhone(), navigator: api };
  };
  // T-2621: who wants to hear the device change (nav-link.js holds Back for it).
  const changeFns = new Set();
  const changed = () => { for (const fn of changeFns) { try { fn({ app: registry?.current ?? null, level }); } catch { /* a listener never stops the device */ } } };
  const registry = createRail({
    rail, screens: root.querySelector('.nav-body'), codeEl: $('nav-code'), doc: root.ownerDocument,
    context: ctx, before: collapse ?? null, storage,
    onOpen: (id, by) => {
      if (id !== link?.app) link = null;
      // T-3021: where Back goes — the app open before this one.
      if (id !== openNow) { cameFrom = openNow; openNow = id; }
      queueMicrotask(changed);
      paintDock(id);
      if (by === 'quiet') return;
      if (level === 0) setLevel(1, { by, focus: false });
      if (by === 'hand') focusTarget(id)?.focus?.({ preventScroll: true });
      if (id === 'home') refresh(true);
    },
    onLaunch: () => setLevel(0, { by: 'app' }),
  });
  let api = null; // filled in below; ctx() is only ever called after
  let openNow = null, cameFrom = null;
  const railShows = () => !isPhone() || level > 0;
  let unNear = null;
  function listenNear() {
    const want = railShows();
    if (want && !unNear && target?.on) unNear = target.on((t) => { near = t; registry.evaluate(); }, { within: 40 });
    if (!want && unNear) { unNear(); unNear = null; near = null; }
  }
  let railAt = -Infinity;
  let telemetry = null;
  let telemetryAt = -Infinity;

  // ---- heights ----
  let level = 0;
  function names() { return isPhone() ? PHONE_DETENTS : DESK_DETENTS; }
  function paintLevel() {
    const list = names();
    const detent = list[Math.min(level, list.length - 1)];
    root.dataset.detent = detent;
    if (html?.dataset) {
      if (isPhone()) { delete html.dataset.navigator; html.dataset.sheet = detent; }
      else { html.dataset.navigator = detent; delete html.dataset.sheet; }
    }
    const open = level > 0;
    grip?.setAttribute('aria-expanded', String(open));
    paintGrip();
    collapse?.setAttribute('aria-label', str(open ? 'nav.collapse' : 'nav.open'));
    if (collapse) collapse.title = str(open ? 'nav.collapse.short' : 'nav.open.short');
    return detent;
  }
  function paintGrip() {
    const name = dockApp ? appLabel(dockApp) : '';
    grip?.setAttribute('aria-label', str(level > 0 ? 'nav.lower' : name ? 'nav.open.on' : 'nav.open', { app: name }));
  }
  function setLevel(next, { by = 'code', focus = by === 'hand' } = {}) {
    const max = names().length - 1;
    const was = level;
    level = Math.max(0, Math.min(max, next));
    paintLevel();
    listen(level > 0);
    listenNear();
    // T-2620: an app holding the drawer's sections closes them while the screen is out of sight.
    registry.setVisible(level > 0);
    telemetry?.sync();
    if (railShows()) registry.evaluate();
    if (level > 0 && registry.current === 'home') refresh(true);
    changed();
    if (focus && was === 0 && level > 0) {
      focusTarget(registry.current)?.focus?.({ preventScroll: true });
    }
    return root.dataset.detent;
  }

  grip?.addEventListener('click', (e) => {
    if (suppressClick) { suppressClick = false; e.preventDefault(); return; }
    setLevel(tapLevel(level, names().length), { by: 'hand' });
  });
  collapse?.addEventListener('click', () => setLevel(level > 0 ? 0 : 1, { by: 'hand' }));
  // T-2742: the header's X does what the collapse arrow does. It lives inside the head,
  // so it keeps its press from starting a sheet drag and its tap from reaching the
  // head's own "open when docked" tap, which would reopen the device it just closed.
  closeKey?.addEventListener('pointerdown', (e) => e.stopPropagation());
  closeKey?.addEventListener('click', (e) => { e.stopPropagation(); close(); });
  // T-3021: Home's MOVE and CONFIDENCE VIEW tiles open their apps.
  for (const [tile, app] of [[$('nav-tile-move'), 'move'], [$('nav-tile-confidence'), 'confidence']]) {
    tile?.addEventListener('click', () => { if (registry.has(app)) void registry.select(app, { by: 'hand' }); });
  }
  out.inspect?.addEventListener('click', () => {
    const t = shown;
    if (!t) return;
    // T-3022: the building opens in Inspect, in the device, so a phone's sheet stays up.
    onInspect(t.id);
  });

  // ---- drag (phone) ----
  let drag = null;
  let suppressClick = false;
  function startDrag(e) {
    if (!isPhone() || (e.button != null && e.button !== 0)) return;
    drag = { id: e.pointerId, y0: e.clientY, t0: now(), h0: root.getBoundingClientRect().height, l0: level, y: e.clientY, t: now(), moved: false };
  }
  function moveDrag(e) {
    if (!drag || e.pointerId !== drag.id) return;
    const dy = drag.y0 - e.clientY;
    if (!drag.moved && Math.abs(dy) < 6) return;
    if (!drag.moved) {
      drag.moved = true;
      root.classList.add('is-dragging');
      try { e.target.setPointerCapture?.(e.pointerId); } catch { /* optional */ }
    }
    const heights = detentHeights(viewportHeight());
    const h = Math.max(heights[0], Math.min(heights[2], drag.h0 + dy));
    root.style.height = `${h}px`;
    drag.vy = (drag.y - e.clientY) / Math.max(1, now() - drag.t);
    drag.y = e.clientY;
    drag.t = now();
  }
  function endDrag(e) {
    if (!drag || e.pointerId !== drag.id) return;
    const d = drag;
    drag = null;
    if (!d.moved) return; // a tap: the grip's click handles it
    suppressClick = true;
    setTimeout(() => { suppressClick = false; }, 0);
    root.classList.remove('is-dragging');
    const h = root.getBoundingClientRect().height;
    root.style.removeProperty('height');
    setLevel(snapLevel(h, d.vy ?? 0, detentHeights(viewportHeight()), d.l0), { by: 'hand' });
  }
  for (const handle of [grip, head]) {
    handle?.addEventListener('pointerdown', startDrag);
    handle?.addEventListener('pointermove', moveDrag);
    handle?.addEventListener('pointerup', endDrag);
    handle?.addEventListener('pointercancel', endDrag);
  }
  // The head is also a tap target: a docked device (the phone's pill, the desktop's rail)
  // opens from it to the last app it showed, at HALF on a phone (T-2619).
  head?.addEventListener('click', () => {
    if (suppressClick) { suppressClick = false; return; }
    if (level === 0) setLevel(1, { by: 'hand' });
  });

  // ---- Home ----
  let shown = null;
  let paintedAt = -Infinity;
  const put = (el, text) => { if (el && el.textContent !== text) el.textContent = text; };
  function paintFront(t) {
    shown = t;
    if (!t) {
      put(out.frontName, str('nav.front.none'));
      put(out.frontDetail, str('nav.front.turn', { distance: formatDistance(FRONT_M, units()) }));
      if (out.inspect) out.inspect.hidden = true;
      return;
    }
    const name = displayName(t.record?.sidecar ?? {}, t.id).title || str('nav.front.building');
    put(out.frontName, name);
    put(out.frontDetail, str('nav.front.away', { distance: formatDistance(t.distance, units()) }));
    if (out.inspect) {
      out.inspect.hidden = false;
      out.inspect.setAttribute('aria-label', str('nav.inspect', { name }));
    }
  }
  function refresh(force = false) {
    const t0 = now();
    if (!force && (level === 0 || registry.current !== 'home' || t0 - paintedAt < 500)) return false;
    paintedAt = t0;
    const p = pose();
    const at = where?.at?.(p.e, p.n, p.bearingDeg) ?? null;
    const here = at?.address ?? at?.place;
    put(out.where, here ? here.charAt(0).toUpperCase() + here.slice(1) : str('nav.where.off'));
    put(out.whereDetail, [facingWords(p.bearingDeg), clock].filter(Boolean).join(' · '));
    if (target) paintFront(target.current(FRONT_M));
    const j = jaunt();
    const stops = j?.jaunt?.stops?.length ?? 0;
    if (out.jaunt) out.jaunt.hidden = !(j?.jaunt && stops);
    if (j?.jaunt && stops) {
      const at1 = Math.min(stops, (j.stopIndex ?? 0) + 1);
      put(out.jauntStep, `${at1} / ${stops}`);
      put(out.jauntTitle, j.jaunt.title ?? '');
      if (out.jauntBar) out.jauntBar.style.width = `${Math.round((at1 / stops) * 100)}%`;
    }
    put(out.move, moveWords(move()));
    put(out.confidence, str(confidence() ? 'nav.on' : 'nav.off'));
    return true;
  }
  // The probe looks only while Home is showing: a docked device costs the frame nothing.
  let unlisten = null;
  function listen(open) {
    if (open && !unlisten && target?.on) unlisten = target.on((t) => paintFront(t), { within: FRONT_M });
    if (!open && unlisten) { unlisten(); unlisten = null; }
  }

  globalThis.matchMedia?.(`(max-width: ${PHONE_MAX_PX}px)`)?.addEventListener?.('change', () => setLevel(Math.min(level, names().length - 1)));

  // ---- the keyboard (T-2622, §14 Accessibility; QA-05, QA-19) ----
  // N toggles the device, and so does Tab while focus is on the scene itself; 1–9 open
  // the rail's apps in the order they show; Escape closes it. Focus goes into the app on
  // open (its screen, or Home's heading) and back to the grip on close, so a keyboard
  // visitor always has a visible place to stand. Nothing here fires while typing.
  const typing = (el) => !!el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName ?? ''));
  const onScene = (el) => !el || el === root.ownerDocument?.body || el.tagName === 'CANVAS';
  function close(by = 'hand') {
    setLevel(0, { by });
    // The handle that reopens it: the grip on a phone, the collapse key on the rail.
    const shown = (el) => !!el && (el.offsetParent !== null || el.getClientRects?.().length > 0);
    (shown(grip) ? grip : collapse ?? grip)?.focus?.({ preventScroll: true });
  }
  function onKey(e) {
    if (!e?.key || e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey || !keysActive()) return;
    const active = root.ownerDocument?.activeElement ?? null;
    if (typing(e.target) || typing(active)) return;
    const inside = !!active && root.contains?.(active);
    if (e.key === 'n' || e.key === 'N') {
      e.preventDefault();
      if (level > 0) close();
      else setLevel(1, { by: 'hand' });
      return;
    }
    if (e.key === 'Tab' && !e.shiftKey && level === 0 && onScene(active)) {
      e.preventDefault();
      setLevel(1, { by: 'hand' });
      return;
    }
    if (/^[1-9]$/.test(e.key)) {
      const id = registry.shown()[Number(e.key) - 1];
      if (!id) return;
      e.preventDefault();
      void registry.select(id, { by: 'hand' });
      return;
    }
    if (e.key === 'Escape' && level > 0 && (inside || escFree())) {
      // Escape inside the device closes it; elsewhere only when nothing else wants it.
      e.preventDefault();
      close();
    }
  }
  keyTarget?.addEventListener?.('keydown', onKey);

  api = {
    /** Add an app to the rail (nav-rail.js says what an app is); returns its unregister. */
    register: (app) => registry.register(app),
    unregister: (id) => registry.unregister(id),
    /** Open an app by id: the device opens to show it (or, for a stub, runs it and docks). */
    select: (id) => registry.select(id, { by: 'code' }),
    has: (id) => registry.has(id),
    /** T-2621: open what a deep link names; an app the rail does not have is ignored. */
    openLink(next) {
      if (!next?.app || !registry.has(next.app)) return Promise.resolve(false);
      link = { app: next.app, id: next.id ?? null, tab: next.tab ?? null };
      if (next.person) link.person = next.person; // T-3265: Inspect opens People on this person's card
      return registry.select(next.app, { by: 'link' });
    },
    get link() { return link; },
    /** T-2621: close whatever is open — back to Home, docked (what Back does). */
    closeApp() {
      link = null;
      if (registry.current && registry.current !== 'home' && registry.has('home')) void registry.select('home', { by: 'quiet' });
      return setLevel(0, { by: 'back' });
    },
    /** T-2621: hear the device change: fn({ app, level }); returns its unsubscribe. */
    onChange(fn) { changeFns.add(fn); return () => changeFns.delete(fn); },
    /** T-3021: Back from an app — to the one it was opened from, else Home. */
    backTo() {
      const id = cameFrom && cameFrom !== openNow && registry.has(cameFrom) ? cameFrom : 'home';
      return { id, label: appLabel(id) || 'Home' };
    },
    back() {
      const { id } = api.backTo();
      return registry.has(id) ? registry.select(id, { by: 'hand' }) : Promise.resolve(false);
    },
    get app() { return registry.current; },
    get apps() { return registry.shown(); },
    rail: () => registry.snapshot(),
    get detent() { return root.dataset.detent; },
    get level() { return level; },
    /** 0 dock / rail, 1 half / open, 2 full (phone). */
    setLevel,
    open(levelWanted = 1) { return setLevel(levelWanted, { by: 'code' }); },
    dock() { return setLevel(0, { by: 'code' }); },
    /** Once a frame from main.js: the rail re-reads its apps every 250 ms while it shows, and
     *  Home repaints at most every 500 ms, only while it shows. */
    update() {
      const t = now();
      if (railShows() && t - railAt >= 250) { railAt = t; registry.evaluate(t); }
      if (t - telemetryAt >= 250) { telemetryAt = t; telemetry?.sync(); }
      return refresh(false);
    },
    refresh: () => refresh(true),
    snapshot() {
      return {
        detent: root.dataset.detent, level,
        dock: { year: dockYearEl?.textContent ?? '', app: dockApp, label: grip?.getAttribute?.('aria-label') ?? '' },
        where: out.where?.textContent ?? '', whereDetail: out.whereDetail?.textContent ?? '',
        front: shown ? { id: shown.id, name: out.frontName?.textContent ?? '', distance: shown.distance } : null,
        jaunt: out.jaunt && !out.jaunt.hidden ? { step: out.jauntStep?.textContent ?? '', title: out.jauntTitle?.textContent ?? '' } : null,
        move: out.move?.textContent ?? '', confidence: out.confidence?.textContent ?? '',
        rail: registry.shown(), app: registry.current,
      };
    },
  };
  for (const app of apps) registry.register(app);
  paintLevel();
  // The telemetry strip at the foot of the device (T-2623, nav-telemetry.js): it ticks only
  // while the device is open and can be seen, and never under reduced motion.
  telemetry = mountTelemetry({ host: root, open: () => level > 0 });
  api.telemetry = telemetry;
  listenNear();
  registry.setVisible(level > 0);
  if (registry.has('home')) void registry.select('home', { by: 'quiet' });
  registry.evaluate();
  return api;
}
