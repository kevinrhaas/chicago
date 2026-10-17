/**
 * Map (SCR 05), loaded the first time it opens (T-2654, NAV-901; DESIGN §07 "Map").
 *
 * The whole field inside the device, in a scope panel: the same picture the round HUD
 * instrument looks through (navigation.js paints it once and both read it), your arrow
 * live on it, the active Jaunt's route as a dotted line through its stops, and a ride
 * under way as a dashed line to where it ends. Tap a building to preview it — its name,
 * its grade and how far — then Go, which travels there the way Move says you get places
 * (teleport, ride there or fly over). A legend toggle colours every footprint by its
 * grade in the Confidence view colours. It opens close up, around you (where a house is big
 * enough to tap); one key shows the whole field, fitted to the screen.
 *
 * It reads the page through `ctx` (ctx.api.navigation, ctx.api.registry, ctx.actions)
 * and never imports main.js. It repaints four times a second, only while its screen is
 * showing and something on it moved.
 */
import { formatDistance } from '../units.js';
import { displayName } from '../display-name.js';

export const GRADES = Object.freeze(['attested', 'inferred', 'reconstructed']);
const GRADE_LABEL = Object.freeze({ attested: 'Attested', inferred: 'Inferred', reconstructed: 'Reconstructed' });
const LEGEND_KEY = 'chicago4d.map.legend';
const TICK_MS = 250;
/** Close up: pixels per metre — a 15 m house is about 19 px, easy to tap. */
export const NEAR_K = 1.25;

/** Is the field point [e, n] inside the ring (even-odd)? */
export function inside([e, n], ring) {
  let hit = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [ei, ni] = ring[i], [ej, nj] = ring[j];
    if ((ni > n) !== (nj > n) && e < ((ej - ei) * (n - ni)) / (nj - ni) + ei) hit = !hit;
  }
  return hit;
}

function area(ring) {
  let a = 0;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) a += (ring[j][0] + ring[i][0]) * (ring[j][1] - ring[i][1]);
  return Math.abs(a / 2);
}

export function centroid(ring) {
  let e = 0, n = 0;
  for (const [x, y] of ring) { e += x; n += y; }
  return [e / ring.length, n / ring.length];
}

/**
 * The building under a field point: the smallest footprint holding it (a shed inside a
 * yard wins over the yard), else the nearest footprint centre within `slopM` metres, so
 * a fingertip on a small house still finds it.
 */
export function hitBuilding(outlines, e, n, slopM = 8) {
  let best = null, bestArea = Infinity;
  for (const ring of outlines ?? []) {
    if (!ring?.id || ring.length < 3 || !inside([e, n], ring)) continue;
    const a = area(ring);
    if (a < bestArea) { best = ring; bestArea = a; }
  }
  if (best) return best;
  let near = null, nearD = slopM;
  for (const ring of outlines ?? []) {
    if (!ring?.id || ring.length < 3) continue;
    const [ce, cn] = centroid(ring);
    const d = Math.hypot(ce - e, cn - n);
    if (d <= nearD) { near = ring; nearD = d; }
  }
  return near;
}

/** The whole field fitted inside `maxW` x `maxH` CSS px: its size and px per metre. */
export function fitField(field, maxW, maxH) {
  const k = Math.max(1e-6, Math.min(maxW / field.widthM, maxH / field.depthM));
  return { w: Math.max(1, Math.round(field.widthM * k)), h: Math.max(1, Math.round(field.depthM * k)), k };
}

/** A building's name for a visitor: never its id. */
export function buildingName(record, id) {
  const title = displayName(record?.sidecar ?? {}, id ?? '').title;
  return title && !/[a-z0-9]_[a-z0-9]/i.test(title) ? title : 'A building';
}

/**
 * The window a close-up shows: `w` x `h` px at `k` px/m, centred on the visitor and kept
 * inside the field (centred on it where the field is smaller than the window).
 */
export function nearView(field, at, w, h, k = NEAR_K) {
  const spanE = w / k, spanN = h / k;
  const centre = (min, max, v, span) => (span >= max - min ? (min + max) / 2 : Math.min(Math.max(v, min + span / 2), max - span / 2));
  const cE = centre(field.eMin, field.eMax, at.e, spanE), cN = centre(field.nMin, field.nMax, at.n, spanN);
  return { eMin: cE - spanE / 2, eMax: cE + spanE / 2, nMin: cN - spanN / 2, nMax: cN + spanN / 2 };
}

export function mount(el, ctx = {}) {
  const doc = el.ownerDocument;
  const win = doc.defaultView ?? globalThis;
  const api = ctx.api ?? {};
  const nav = () => api.navigation ?? null;
  const make = (tag, cls, text) => { const e = doc.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  el.replaceChildren();
  el.classList.add('nav-map');

  const scope = make('div', 'nav-scope nav-map-scope');
  const canvas = make('canvas', 'nav-map-canvas');
  canvas.setAttribute('role', 'img');
  scope.append(canvas);

  const bar = make('div', 'nav-map-bar');
  const zoomBtn = make('button', 'nav-map-toggle nav-map-zoom');
  zoomBtn.type = 'button';
  const legendBtn = make('button', 'nav-map-toggle nav-map-legend-toggle', 'Confidence view colours');
  legendBtn.type = 'button';
  const legend = make('ul', 'nav-map-legend');
  for (const g of GRADES) {
    const li = make('li', `nav-map-swatch is-${g}`);
    li.append(make('i'), make('span', null, GRADE_LABEL[g]));
    legend.append(li);
  }
  bar.append(zoomBtn, legendBtn, legend);

  const preview = make('section', 'nav-block nav-map-preview');
  preview.hidden = true;
  preview.setAttribute('aria-live', 'polite');
  const pname = make('strong', 'nav-place');
  const psub = make('span', 'nav-sub');
  const go = make('button', 'nav-key nav-map-go', 'Go');
  go.type = 'button';
  preview.append(make('span', 'nav-k', 'On the map'), pname, psub, go);

  const foot = make('p', 'nav-sub nav-map-foot');
  // The preview sits right under the map, so Go is in reach at HALF on a phone.
  el.append(scope, preview, bar, foot);

  let legendOn = false;
  try { legendOn = win.localStorage?.getItem(LEGEND_KEY) === '1'; } catch { /* a convenience */ }
  let zoom = 'near';
  let selected = null;
  let fit = { w: 0, h: 0, k: 1 };
  let view = null;
  let last = null;
  const units = () => api.hud?.settings?.units ?? nav()?.units ?? 'imperial';
  const style = () => win.getComputedStyle?.(doc.documentElement);
  const token = (name, fallback) => style()?.getPropertyValue?.(name)?.trim() || fallback;

  function paintBar() {
    legendBtn.setAttribute('aria-pressed', String(legendOn));
    legend.hidden = !legendOn;
    zoomBtn.textContent = zoom === 'near' ? 'Whole field' : 'Close up';
    zoomBtn.setAttribute('aria-label', zoom === 'near' ? 'Show the whole field' : 'Show close up, around you');
    canvas.setAttribute('aria-label', `${zoom === 'near' ? 'The map around you' : 'The whole field'}, with your arrow. Tap a building to preview it.`);
  }

  /** Size the canvas to the screen it is on; 'changed', 'same', or false with no field. */
  function layout() {
    const field = nav()?.field?.();
    if (!field) return false;
    const box = scope.getBoundingClientRect?.() ?? { width: 0 };
    const maxW = Math.max(120, Math.floor((box.width || el.clientWidth || 300) - 26));
    const screen = el.getBoundingClientRect?.()?.height || 360;
    const maxH = Math.max(150, Math.floor(screen - 170));
    const next = zoom === 'near'
      ? { w: maxW, h: Math.min(maxH, Math.round(maxW * 1.15)), k: NEAR_K }
      : fitField(field, maxW, maxH);
    foot.textContent = zoom === 'near'
      ? `Close up around you. ${formatDistance(field.widthM, units())} by ${formatDistance(field.depthM, units())} in all: Whole field shows it.`
      : `${formatDistance(field.widthM, units())} east to west, ${formatDistance(field.depthM, units())} north to south.`;
    if (next.w === fit.w && next.h === fit.h && next.k === fit.k) return 'same';
    fit = next;
    const dpr = Math.min(win.devicePixelRatio || 1, 2);
    canvas.style.width = `${fit.w}px`;
    canvas.style.height = `${fit.h}px`;
    canvas.width = Math.round(fit.w * dpr);
    canvas.height = Math.round(fit.h * dpr);
    last = null;
    return 'changed';
  }

  const toPx = (e, n) => [(e - view.eMin) * fit.k, (view.nMax - n) * fit.k];

  function line(g, pts, dash, colour, width) {
    if (!pts || pts.length < 2) return;
    g.save();
    g.setLineDash?.(dash);
    g.strokeStyle = colour;
    g.lineWidth = width;
    g.lineCap = 'round';
    g.beginPath();
    pts.forEach(([e, n], i) => { const [x, y] = toPx(e, n); if (i === 0) g.moveTo(x, y); else g.lineTo(x, y); });
    g.stroke();
    g.restore();
  }

  function paint() {
    const navigation = nav();
    const g = canvas.getContext?.('2d');
    if (!navigation || !g || !layout()) return false;
    const field = navigation.field();
    const p = navigation.player;
    view = zoom === 'near' ? nearView(field, p, fit.w, fit.h, fit.k) : { eMin: field.eMin, eMax: field.eMax, nMin: field.nMin, nMax: field.nMax };
    const dpr = canvas.width / fit.w;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    navigation.drawView(g, view, fit.w, fit.h);
    const ring = (r) => { g.beginPath(); r.forEach(([e, n], i) => { const [x, y] = toPx(e, n); if (i === 0) g.moveTo(x, y); else g.lineTo(x, y); }); g.closePath(); };
    if (legendOn) {
      const colours = Object.fromEntries(GRADES.map((gr) => [gr, token(`--grade-${gr}`, { attested: '#d4ae38', inferred: '#c9d0d8', reconstructed: '#a86a3a' }[gr])]));
      g.save();
      g.globalAlpha = 0.9;
      for (const r of navigation.outlines ?? []) {
        if (!colours[r.grade]) continue;
        ring(r); g.fillStyle = colours[r.grade]; g.fill();
      }
      g.restore();
    }
    // The active Jaunt: a dotted line through its stops, the one you are heading for ringed.
    const route = ctx.actions?.jauntRoute?.() ?? null;
    if (route?.stops?.length) {
      const accent = token('--accent', '#d8a24a');
      line(g, route.stops, [1.5, 4], accent, 2.2);
      route.stops.forEach(([e, n], i) => {
        const [x, y] = toPx(e, n);
        g.beginPath(); g.arc(x, y, i === route.at ? 4.5 : 3, 0, Math.PI * 2);
        g.fillStyle = i === route.at ? accent : '#f4ebd0'; g.fill();
        g.lineWidth = 1.2; g.strokeStyle = '#17140c'; g.stroke();
      });
    }
    // A ride under way: dashed, from where you are to where it ends.
    const ride = ctx.actions?.travelRoute?.() ?? null;
    if (ride?.length) line(g, [[p.e, p.n], ...ride], [5, 4], '#f4b54f', 1.6);
    if (selected) { g.save(); ring(selected); g.lineWidth = 2.4; g.strokeStyle = '#f4b54f'; g.stroke(); g.restore(); }
    const [mx, my] = toPx(p.e, p.n);
    navigation.drawMarker(g, mx, my);
    return true;
  }

  function showPreview(r) {
    selected = r;
    last = null;
    if (!r) { preview.hidden = true; return; }
    const record = api.registry?.get?.(r.id);
    const name = buildingName(record, r.id);
    const p = nav()?.player ?? { e: 0, n: 0 };
    const [ce, cn] = centroid(r);
    pname.textContent = name;
    psub.textContent = [GRADE_LABEL[r.grade], `${formatDistance(Math.hypot(ce - p.e, cn - p.n), units())} away`].filter(Boolean).join(' · ');
    go.setAttribute('aria-label', `Go to ${name}`);
    preview.hidden = false;
  }

  canvas.addEventListener('click', (ev) => {
    if (!view || !fit.k) return;
    const b = canvas.getBoundingClientRect();
    const e = view.eMin + (ev.clientX - b.left) / fit.k, n = view.nMax - (ev.clientY - b.top) / fit.k;
    showPreview(hitBuilding(nav()?.outlines, e, n, Math.max(4, 12 / fit.k)));
    paint();
  });
  go.addEventListener('click', () => {
    if (!selected) return;
    const ok = ctx.actions?.goTo?.(selected.id);
    // On a phone the device steps down so the ride (or the arrival) is in view.
    if (ok !== false && ['half', 'full'].includes(ctx.navigator?.detent)) ctx.navigator?.dock?.();
  });
  legendBtn.addEventListener('click', () => {
    legendOn = !legendOn;
    try { win.localStorage?.setItem(LEGEND_KEY, legendOn ? '1' : '0'); } catch { /* a convenience */ }
    paintBar(); paint();
  });
  zoomBtn.addEventListener('click', () => { zoom = zoom === 'near' ? 'field' : 'near'; paintBar(); paint(); });

  const visible = () => el.isConnected && !el.hidden && (ctx.navigator?.level ?? 1) > 0;
  function tick() {
    if (!visible()) return;
    // The sheet changes height under it (HALF, FULL, a drag): re-fit, which repaints.
    layout();
    const p = nav()?.player;
    const route = ctx.actions?.jauntRoute?.();
    const ride = ctx.actions?.travelRoute?.();
    const key = p ? `${p.e.toFixed(1)},${p.n.toFixed(1)},${Math.round(p.bearingDeg)},${route?.at ?? ''},${route?.stops?.length ?? 0},${ride?.length ?? 0},${fit.w}x${fit.h}` : '';
    if (key === last) return;
    if (paint()) last = key;
  }
  const timer = win.setInterval?.(tick, TICK_MS);
  el._mapTimer = timer;
  el._mapApi = {
    paint,
    setZoom(z) { zoom = z === 'field' ? 'field' : 'near'; paintBar(); paint(); return zoom; },
    select: (id) => showPreview((nav()?.outlines ?? []).find((r) => r.id === id) ?? null),
    get selected() { return selected?.id ?? null; },
    get legend() { return legendOn; },
    get zoom() { return zoom; },
    get size() { return { ...fit }; },
    get view() { return view ? { ...view } : null; },
  };
  paintBar();
  paint();
}

/** Each time Map is opened: re-fit to the screen it is shown at, and paint at once. */
export function shown(el) { el._mapApi?.paint(); }

export function unmount(el) {
  if (el._mapTimer) (el.ownerDocument.defaultView ?? globalThis).clearInterval(el._mapTimer);
  el._mapTimer = null;
  el._mapApi = null;
  el.replaceChildren();
}
