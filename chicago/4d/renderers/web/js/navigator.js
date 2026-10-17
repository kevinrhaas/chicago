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
 * Confidence view. The rail is the app registry (nav-rail.js, T-2618): every app,
 * Home included, is registered from its own file under js/apps/, and
 * `navigator.register(app)` adds one more.
 *
 * Every control is a plain <button>, so the gesture gate (T-2614) can hook the first
 * tap on any of them. Opening the device by hand moves focus into Home (DESIGN §14,
 * a non-modal region); nothing moves focus when the device docks itself. The device
 * reads its values once every half second, and only while Home is showing.
 */
import { facingWords, clockWords, screenDate } from './where.js';
import { mountTelemetry } from './nav-telemetry.js';
import { formatDistance } from './units.js';
import { displayName } from './display-name.js';
import { createRail } from './nav-rail.js';

export const PHONE_DETENTS = Object.freeze(['dock', 'half', 'full']);
export const DESK_DETENTS = Object.freeze(['rail', 'open']);
export const PHONE_MAX_PX = 620;
export const DOCK_PX = 64;
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
  if (flying) return 'Flying';
  const ways = { walk: 'Walking', wagon: 'By wagon', horse: 'On horseback' };
  const how = ways[pace] ?? 'Walking';
  return riding ? `${how}, on the way` : how;
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
} = {}) {
  if (!root) return null;
  const $ = (id) => root.querySelector(`#${id}`);
  const html = root.ownerDocument?.documentElement;
  const grip = $('nav-grip'), head = $('nav-head'), rail = $('nav-rail'), collapse = $('nav-collapse');
  const title = $('nav-home-title');
  const out = {
    where: $('nav-where'), whereDetail: $('nav-where-detail'),
    frontName: $('nav-front-name'), frontDetail: $('nav-front-detail'), inspect: $('nav-inspect'),
    jaunt: $('nav-jaunt'), jauntStep: $('nav-jaunt-step'), jauntTitle: $('nav-jaunt-title'), jauntBar: $('nav-jaunt-bar'),
    move: $('nav-move'), confidence: $('nav-confidence'),
  };
  const dateEl = $('nav-date');
  if (dateEl) dateEl.textContent = screenDate(scene.target_date);
  const clock = clockWords(scene.lighting?.local_time);
  root.ownerDocument?.body?.classList.add('has-navigator');

  // ---- the rail: the app registry (T-2618) ----
  // `ctx` is the page's context (main.js) plus what only the device knows: the target
  // within 40 m (Inspect's rule), the shape it is in, and the device itself.
  let near = null;
  const ctx = () => ({ ...context(), target: near, isPhone: isPhone(), navigator: api });
  const registry = createRail({
    rail, screens: root.querySelector('.nav-body'), codeEl: $('nav-code'), doc: root.ownerDocument,
    context: ctx, before: collapse ?? null, storage,
    onOpen: (id, by) => {
      if (by === 'quiet') return;
      if (level === 0) setLevel(1, { by, focus: false });
      if (by === 'hand') (id === 'home' ? title : root.querySelector(`#nav-app-${id}`))?.focus?.({ preventScroll: true });
      if (id === 'home') refresh(true);
    },
    onLaunch: () => setLevel(0, { by: 'app' }),
  });
  let api = null; // filled in below; ctx() is only ever called after
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
      if (isPhone()) delete html.dataset.navigator;
      else html.dataset.navigator = detent;
    }
    const open = level > 0;
    grip?.setAttribute('aria-expanded', String(open));
    grip?.setAttribute('aria-label', open ? 'Lower the Navigator' : 'Open the Navigator');
    collapse?.setAttribute('aria-label', open ? 'Collapse the Navigator' : 'Open the Navigator');
    if (collapse) collapse.title = open ? 'Collapse' : 'Open';
    return detent;
  }
  function setLevel(next, { by = 'code', focus = by === 'hand' } = {}) {
    const max = names().length - 1;
    const was = level;
    level = Math.max(0, Math.min(max, next));
    paintLevel();
    listen(level > 0);
    listenNear();
    telemetry?.sync();
    if (railShows()) registry.evaluate();
    if (level > 0 && registry.current === 'home') refresh(true);
    if (focus && was === 0 && level > 0) {
      (registry.current && registry.current !== 'home' ? root.querySelector(`#nav-app-${registry.current}`) : title)?.focus?.({ preventScroll: true });
    }
    return root.dataset.detent;
  }

  grip?.addEventListener('click', (e) => {
    if (suppressClick) { suppressClick = false; e.preventDefault(); return; }
    setLevel(tapLevel(level, names().length), { by: 'hand' });
  });
  collapse?.addEventListener('click', () => setLevel(level > 0 ? 0 : 1, { by: 'hand' }));
  out.inspect?.addEventListener('click', () => {
    const t = shown;
    if (!t) return;
    if (isPhone()) setLevel(0, { by: 'app' });
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
  // The head is also a tap target on a phone: a docked device opens from it.
  head?.addEventListener('click', () => {
    if (suppressClick) { suppressClick = false; return; }
    if (isPhone() && level === 0) setLevel(1, { by: 'hand' });
  });

  // ---- Home ----
  let shown = null;
  let paintedAt = -Infinity;
  const put = (el, text) => { if (el && el.textContent !== text) el.textContent = text; };
  function paintFront(t) {
    shown = t;
    if (!t) {
      put(out.frontName, 'Nothing close by');
      put(out.frontDetail, `Turn toward a building within ${formatDistance(FRONT_M, units())}.`);
      if (out.inspect) out.inspect.hidden = true;
      return;
    }
    const name = displayName(t.record?.sidecar ?? {}, t.id).title || 'A building';
    put(out.frontName, name);
    put(out.frontDetail, `${formatDistance(t.distance, units())} away`);
    if (out.inspect) {
      out.inspect.hidden = false;
      out.inspect.setAttribute('aria-label', `Inspect ${name}`);
    }
  }
  function refresh(force = false) {
    const t0 = now();
    if (!force && (level === 0 || registry.current !== 'home' || t0 - paintedAt < 500)) return false;
    paintedAt = t0;
    const p = pose();
    const at = where?.at?.(p.e, p.n, p.bearingDeg) ?? null;
    put(out.where, at?.place ? at.place.charAt(0).toUpperCase() + at.place.slice(1) : 'Off the streets');
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
    put(out.confidence, confidence() ? 'On' : 'Off');
    return true;
  }
  // The probe looks only while Home is showing: a docked device costs the frame nothing.
  let unlisten = null;
  function listen(open) {
    if (open && !unlisten && target?.on) unlisten = target.on((t) => paintFront(t), { within: FRONT_M });
    if (!open && unlisten) { unlisten(); unlisten = null; }
  }

  globalThis.matchMedia?.(`(max-width: ${PHONE_MAX_PX}px)`)?.addEventListener?.('change', () => setLevel(Math.min(level, names().length - 1)));

  api = {
    /** Add an app to the rail (nav-rail.js says what an app is); returns its unregister. */
    register: (app) => registry.register(app),
    unregister: (id) => registry.unregister(id),
    /** Open an app by id: the device opens to show it (or, for a stub, runs it and docks). */
    select: (id) => registry.select(id, { by: 'code' }),
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
  if (registry.has('home')) void registry.select('home', { by: 'quiet' });
  registry.evaluate();
  return api;
}
