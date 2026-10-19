/**
 * navigation.js — compass, a moving overview window, and the whole field on demand.
 *
 * The overview is not a second map asset.  Land and water are sampled from the
 * same committed heightfield the walker stands on; streets and structure
 * outlines come from the same compiled scene index the 3D renderer places.
 * The only moving mark is the visitor: north stays at the top and the arrow
 * follows their bearing.
 *
 * The inset is a WINDOW on that field — a fixed frame at a fixed scale that
 * travels with the visitor — and the pop-out is the whole of it at once.  See
 * the note on INSET below for why it is built that way.
 */

import { formatDistance, normalUnitSystem } from './units.js';
import { isTyping } from './controls/pointerlock.js';
import { todayText } from './modern-streets.js';

const DEG = Math.PI / 180;
const CARDINALS = [
  'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW',
];

/**
 * T-1142.  THE INSET'S FRAME AND SCALE ARE CONSTANTS, not functions of the field.
 *
 * They used to be functions of it.  `resize()` pinned the width and derived the
 * height from the field's own aspect ratio —
 *
 *     logicalHeight = Math.max(76, Math.round(logicalWidth
 *       * (bounds.nMax - bounds.nMin) / (bounds.eMax - bounds.eMin)));
 *
 * — so the widget was the ground's shadow, and when the ground grew the widget
 * grew with it.  Three tickets grew it in two days: T-1067 carried the field
 * north, T-1123 took the north wall to +1120, T-0464 took the south wall to
 * Twenty-Second Street.  Reading cols/rows/cell_m out of each committed
 * heightfield.json and carrying them through `widthM`/`depthM` — which span
 * (cols - 1) cells, the sample centres, not (cols) — the inset went
 *
 *     2 020 x   800 m  ->  248 x  98 px   (through 2026-09-12)
 *     2 020 x 4 920 m  ->  248 x 604 px   (after T-0464)
 *
 * — six times taller, more than half a phone screen, with the town smeared
 * across the top of a long strip.
 *
 * These numbers are what that formula PRODUCED on the 2026-09-12 field, so
 * "the size it was before" is exact rather than chosen: 248x98 on a desktop,
 * and 188x76 on a phone, which is the old `Math.max(76, …)` floor.
 * INSET_SPAN_E_M is that field's full width, so a pixel still covers the ground
 * it covered then — the same frame AND the same zoom, a window that travels
 * instead of a squeeze that gets worse every time the ground is extended.
 *
 * ONE scale serves both frames, which is a small deliberate change on a phone.
 * The old narrow map squeezed the same 2 020 m into 188 px, so it was 10.7 m
 * per pixel against the desktop's 8.1; a window has no reason to carry two
 * zooms, so the phone takes the desktop's and shows 1 531 x 619 m of ground
 * rather than trying to hold a field it cannot.
 *
 * NOTHING HERE MAY BE RE-DERIVED FROM `bounds`.  T-0466 widens the field to
 * four kilometres for South Through Time and would walk the whole fault back
 * in.  tools/smoke_renderer.mjs asserts these numbers against the live element
 * at both viewports, so an edit that reintroduces the dependency fails there.
 */
/*
 * T-2626 (DESIGN §10). The compass and the inset are now ONE round instrument, so the
 * frame is a square the round face is cut from: 112 px on a desktop, 92 px on a phone.
 * The rule above is untouched — still constants, still never derived from `bounds` —
 * and so is the zoom: M_PER_PX keeps the T-1142 scale (2 020 m over 248 px), so the
 * window shows the same ground per pixel it always did, now through a round face.
 */
const INSET = { wide: { w: 112, h: 112 }, narrow: { w: 92, h: 92 } };
const INSET_SPAN_E_M = 2020;
const M_PER_PX = INSET_SPAN_E_M / 248;
const NARROW_MAX_PX = 560;

/**
 * The background holds the WHOLE field at twice the inset's scale.  Twice, so
 * the inset downsamples 2:1 — crisp, rather than the re-blocked look of a 1:1
 * blit — and so the pop-out, which fits the field to the screen and therefore
 * wants more pixels than the inset ever shows, also scales DOWN instead of
 * blowing a 248px-wide image up.  It is painted once and kept: it depends on
 * the field and the scale, and neither moves while the page is open.
 */
const SUPER = 2;

/** Seen only where a window runs past the field — the letterbox case. */
const OUTSIDE = '#3b3a30';

function normalBearing(value) {
  return ((Number(value) || 0) % 360 + 360) % 360;
}

function cardinal(bearing) {
  return CARDINALS[Math.round(normalBearing(bearing) / 22.5) % CARDINALS.length];
}

function structureOutlines(registry) {
  const out = [];
  for (const record of registry?.values?.() ?? []) {
    const sidecar = record.sidecar ?? {};
    const raw = sidecar.footprint;
    const polygon = Array.isArray(raw) ? raw : raw?.polygon;
    const placement = sidecar.placement ?? {};
    if (!Array.isArray(polygon) || polygon.length < 3) continue;
    const th = (placement.rotation_deg ?? 0) * DEG;
    const cos = Math.cos(th);
    const sin = Math.sin(th);
    const e0 = placement.local_e ?? 0;
    const n0 = placement.local_n ?? 0;
    const ring = polygon.map(([u, v]) => [
      e0 + u * cos + v * sin,
      n0 - u * sin + v * cos,
    ]);
    // T-2654: the Map app hit-tests these and colours them by the building's own grade.
    ring.id = record.id ?? sidecar.id ?? null;
    ring.grade = sidecar.grade?.value ?? sidecar.documented_range?.confidence ?? null;
    out.push(ring);
  }
  return out;
}

/** T-2741: today's streets on the maps — a cool blue under the period ground's browns. */
const MODERN_STROKE = 'rgba(96, 205, 235, .78)';
const MODERN_LABEL = '#bfefff';

export function createNavigation({ root, terrain, registry, streets, year = '', where = null, onOpen = null } = {}) {
  const compass = root?.querySelector('#compass');
  const needle = root?.querySelector('#compass-needle');
  const direction = root?.querySelector('#compass-direction');
  const bearingLabel = root?.querySelector('#compass-bearing');
  const overview = root?.querySelector('#overview-map');
  const canvas = root?.querySelector('#overview-map-canvas');
  const openButton = root?.querySelector('#overview-open');
  const full = root?.querySelector('#overview-full');
  const fullCanvas = root?.querySelector('#overview-full-canvas');
  const fullClose = root?.querySelector('#overview-full-close');
  const fullFoot = root?.querySelector('#overview-full-foot');
  const streetReadout = root?.querySelector('#street-readout');
  const streetYear = root?.querySelector('#street-era-year');
  const streetHistoric = root?.querySelector('#street-historic');
  const streetModern = root?.querySelector('#street-modern');
  const streetApproach = root?.querySelector('#street-approach');
  const streetToggle = root?.querySelector('#street-toggle');
  if (streetYear) streetYear.textContent = String(year || '');
  const ctx = canvas?.getContext('2d');
  const fullCtx = fullCanvas?.getContext('2d');
  const background = document.createElement('canvas');
  const bg = background.getContext('2d');
  const hf = terrain?.heightfield;
  const outlines = structureOutlines(registry);

  const bounds = hf?.loaded ? {
    eMin: hf.originE,
    eMax: hf.originE + hf.widthM,
    nMin: hf.originN,
    nMax: hf.originN + hf.depthM,
  } : { eMin: -320, eMax: 320, nMin: -400, nMax: 400 };
  const fieldE = bounds.eMax - bounds.eMin;
  const fieldN = bounds.nMax - bounds.nMin;

  // Background pixels per metre. Fixed for the life of the page — see SUPER.
  const bgScale = SUPER / M_PER_PX;

  let insetW = 0;
  let insetH = 0;
  // A fresh <canvas> reports 300x150, not 0x0, so "has it been painted?" cannot
  // be asked of its dimensions — it would answer yes and blit an empty buffer.
  let bgPainted = false;
  let fullSize = { w: 0, h: 0 };
  let fullOpen = false;
  let compassVisible = true;
  let mapVisible = true;
  let streetVisible = true;
  let units = 'imperial';
  let player = { e: 0, n: 0, bearingDeg: 0 };
  let lastPaint = { e: Infinity, n: Infinity, bearingDeg: Infinity };
  let lastStreet = { e: Infinity, n: Infinity, bearingDeg: Infinity };
  let streetState = null;
  // T-2741: where you are in the scene's own year (where.js — the 1835 streets, the 1904
  // grid and context city; nothing in 1812) and today (modern-streets.js, loaded late).
  let eraWhere = where;
  let modern = null;
  let eraState = null;
  let todayState = null;
  const modernLayer = document.createElement('canvas');
  const ml = modernLayer.getContext('2d');
  let modernPainted = false;

  /** World metres -> background pixels. The background IS the whole field. */
  function point(e, n) {
    return { x: (e - bounds.eMin) * bgScale, y: (bounds.nMax - n) * bgScale };
  }

  function paintBackground() {
    if (!bg) return;
    const w = Math.max(1, Math.round(fieldE * bgScale));
    const h = Math.max(1, Math.round(fieldN * bgScale));
    background.width = w;
    background.height = h;
    const image = bg.createImageData(w, h);
    const data = image.data;
    for (let y = 0; y < h; y++) {
      const gy = hf?.loaded
        ? Math.min(hf.rows - 1, Math.round((h - 1 - y) * (hf.rows - 1)
          / Math.max(1, h - 1))) : 0;
      for (let x = 0; x < w; x++) {
        const gx = hf?.loaded
          ? Math.min(hf.cols - 1, Math.round(x * (hf.cols - 1)
            / Math.max(1, w - 1))) : 0;
        const h0 = hf?.loaded ? hf.data[gy * hf.cols + gx] : 1;
        const water = h0 < -0.02;
        const shade = Math.max(0, Math.min(18, Math.round(Math.max(0, h0) * 4)));
        const i = (y * w + x) * 4;
        data[i] = water ? 45 : 105 + shade;
        data[i + 1] = water ? 79 : 101 + shade;
        data[i + 2] = water ? 91 : 70 + Math.round(shade * 0.45);
        data[i + 3] = 255;
      }
    }
    bgPainted = true;
    bg.putImageData(image, 0, 0);

    // The same compiled paths the earth ribbons use.  Legal corridor width is
    // deliberately not drawn here: at this scale a centreline is the truthful
    // distinction between a street and a whole block of tan pixels.
    // Widths are in BACKGROUND pixels, so they carry the SUPER factor: the
    // inset downsamples 2:1 and a 1.8px line lands as the 0.9px it always was.
    bg.save();
    bg.strokeStyle = 'rgba(77, 61, 36, .78)';
    bg.lineWidth = 0.9 * SUPER;
    for (const street of streets?.records ?? []) {
      bg.beginPath();
      street.path.forEach(([e, n], i) => {
        const screen = point(e, n);
        if (i === 0) bg.moveTo(screen.x, screen.y); else bg.lineTo(screen.x, screen.y);
      });
      bg.stroke();
    }
    bg.restore();

    // Every compiled footprint, including water-anchored bridges and piers.
    bg.save();
    bg.fillStyle = 'rgba(244, 235, 208, .82)';
    bg.strokeStyle = 'rgba(42, 34, 22, .72)';
    bg.lineWidth = 0.7 * SUPER;
    for (const polygon of outlines) {
      bg.beginPath();
      polygon.forEach(([e, n], i) => {
        const screen = point(e, n);
        if (i === 0) bg.moveTo(screen.x, screen.y); else bg.lineTo(screen.x, screen.y);
      });
      bg.closePath();
      bg.fill();
      bg.stroke();
    }
    bg.restore();
  }

  /** Today's streets, once, at the background's scale, for the inset and the pop-out. */
  function paintModernLayer() {
    if (!ml || !modern) return;
    modernLayer.width = Math.max(1, Math.round(fieldE * bgScale));
    modernLayer.height = Math.max(1, Math.round(fieldN * bgScale));
    ml.clearRect(0, 0, modernLayer.width, modernLayer.height);
    strokeModern(ml, (e, n) => { const p = point(e, n); return [p.x, p.y]; }, 0.9 * SUPER);
    modernPainted = true;
  }

  /** Stroke every modern centreline through `toPx` (and, given a `view`, only those in it). */
  function strokeModern(dest, toPx, width, view = null) {
    dest.save();
    dest.strokeStyle = MODERN_STROKE;
    dest.lineWidth = width;
    dest.lineCap = 'round';
    dest.lineJoin = 'round';
    dest.beginPath();
    for (const s of modern?.segments ?? []) {
      if (view && (s.box[2] < view.eMin || s.box[0] > view.eMax || s.box[3] < view.nMin || s.box[1] > view.nMax)) continue;
      for (let i = 0; i < s.pts.length; i += 2) {
        const [x, y] = toPx(s.pts[i], s.pts[i + 1]);
        if (i === 0) dest.moveTo(x, y); else dest.lineTo(x, y);
      }
    }
    dest.stroke();
    dest.restore();
  }

  /**
   * Today's street names, close up only (the Map app's near view): one label per street,
   * on its longest piece in the window, turned along it and kept upright.
   */
  function labelModern(dest, view, w, h) {
    const k = w / (view.eMax - view.eMin);
    if (k < 0.5 || !modern) return;
    const toPx = (e, n) => [(e - view.eMin) * k, (view.nMax - n) * k];
    const best = new Map();
    for (const s of modern.segments) {
      if (s.box[2] < view.eMin || s.box[0] > view.eMax || s.box[3] < view.nMin || s.box[1] > view.nMax) continue;
      for (let i = 0; i + 3 < s.pts.length; i += 2) {
        const [ax, ay] = toPx(s.pts[i], s.pts[i + 1]);
        const [bx, by] = toPx(s.pts[i + 2], s.pts[i + 3]);
        const mx = (ax + bx) / 2, my = (ay + by) / 2;
        if (mx < 20 || mx > w - 20 || my < 12 || my > h - 12) continue;
        const len = Math.hypot(bx - ax, by - ay);
        const prev = best.get(s.name);
        if (!prev || len > prev.len) best.set(s.name, { len, mx, my, ang: Math.atan2(by - ay, bx - ax) });
      }
    }
    dest.save();
    dest.font = '600 10px ui-sans-serif, system-ui, sans-serif';
    dest.textAlign = 'center';
    dest.textBaseline = 'middle';
    dest.lineJoin = 'round';
    for (const [name, b] of best) {
      const label = name;
      if (b.len < dest.measureText(label).width + 8) continue;
      let ang = b.ang;
      if (ang > Math.PI / 2) ang -= Math.PI;
      if (ang < -Math.PI / 2) ang += Math.PI;
      dest.save();
      dest.translate(b.mx, b.my);
      dest.rotate(ang);
      dest.lineWidth = 3;
      dest.strokeStyle = 'rgba(10, 22, 28, .85)';
      dest.strokeText(label, 0, 0);
      dest.fillStyle = MODERN_LABEL;
      dest.fillText(label, 0, 0);
      dest.restore();
    }
    dest.restore();
  }

  /** The modern layer's part under a window, when the street names are showing. */
  function blitModern(dest, view, dx, dy, dw, dh) {
    if (!streetVisible || !modern) return;
    if (!modernPainted) paintModernLayer();
    const eMin = Math.max(view.eMin, bounds.eMin);
    const eMax = Math.min(view.eMax, bounds.eMax);
    const nMin = Math.max(view.nMin, bounds.nMin);
    const nMax = Math.min(view.nMax, bounds.nMax);
    if (!(eMax > eMin && nMax > nMin)) return;
    const kx = dw / (view.eMax - view.eMin);
    const ky = dh / (view.nMax - view.nMin);
    dest.drawImage(modernLayer,
      (eMin - bounds.eMin) * bgScale, (bounds.nMax - nMax) * bgScale,
      (eMax - eMin) * bgScale, (nMax - nMin) * bgScale,
      dx + (eMin - view.eMin) * kx, dy + (view.nMax - nMax) * ky,
      (eMax - eMin) * kx, (nMax - nMin) * ky);
  }

  function resize() {
    if (!canvas || !ctx) return;
    const frame = window.innerWidth <= NARROW_MAX_PX ? INSET.narrow : INSET.wide;
    insetW = frame.w;
    insetH = frame.h;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.style.width = `${insetW}px`;
    canvas.style.height = `${insetH}px`;
    canvas.width = Math.round(insetW * dpr);
    canvas.height = Math.round(insetH * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    // The background is the whole field at a fixed scale, so a viewport change
    // cannot alter it. Paint it once; a resize only re-frames the window onto it.
    if (!bgPainted) paintBackground();
    lastPaint = { e: Infinity, n: Infinity, bearingDeg: Infinity };
    paintMap();
    if (fullOpen) { layoutFull(); paintFull(); }
  }

  /**
   * The ground the inset shows: its own pixels' worth at M_PER_PX, centred on
   * the visitor and CLAMPED to the field, so the window never runs past data
   * that exists.  A span wider than the field centres instead — the letterbox
   * case, where the frame paints OUTSIDE around what there is rather than
   * stretching the field to fill it.
   */
  function viewport() {
    const spanE = insetW * M_PER_PX;
    const spanN = insetH * M_PER_PX;
    const centre = (min, max, at, span) => (span >= max - min
      ? (min + max) / 2
      : Math.min(Math.max(at, min + span / 2), max - span / 2));
    const cE = centre(bounds.eMin, bounds.eMax, player.e, spanE);
    const cN = centre(bounds.nMin, bounds.nMax, player.n, spanN);
    return {
      eMin: cE - spanE / 2, eMax: cE + spanE / 2,
      nMin: cN - spanN / 2, nMax: cN + spanN / 2,
    };
  }

  /**
   * Blit the part of the background a window covers into a destination rect.
   * Both source and destination are derived from the window's INTERSECTION with
   * the field, so ground that does not exist is left as painted surround rather
   * than smeared out of the nearest edge pixel.
   */
  function blit(dest, view, dx, dy, dw, dh) {
    if (!bgPainted) return;
    const eMin = Math.max(view.eMin, bounds.eMin);
    const eMax = Math.min(view.eMax, bounds.eMax);
    const nMin = Math.max(view.nMin, bounds.nMin);
    const nMax = Math.min(view.nMax, bounds.nMax);
    if (!(eMax > eMin && nMax > nMin)) return;
    const kx = dw / (view.eMax - view.eMin);
    const ky = dh / (view.nMax - view.nMin);
    dest.drawImage(background,
      (eMin - bounds.eMin) * bgScale, (bounds.nMax - nMax) * bgScale,
      (eMax - eMin) * bgScale, (nMax - nMin) * bgScale,
      dx + (eMin - view.eMin) * kx, dy + (view.nMax - nMax) * ky,
      (eMax - eMin) * kx, (nMax - nMin) * ky);
  }

  /** The visitor, drawn at `x`,`y` in whatever context is being painted. */
  function marker(dest, x, y) {
    dest.save();
    dest.translate(x, y);
    dest.rotate(normalBearing(player.bearingDeg) * DEG);
    dest.beginPath();
    dest.moveTo(0, -8);
    dest.lineTo(5.2, 6);
    dest.lineTo(0, 3.5);
    dest.lineTo(-5.2, 6);
    dest.closePath();
    dest.fillStyle = '#f4b54f';
    dest.strokeStyle = '#17140c';
    dest.lineWidth = 1.4;
    dest.fill();
    dest.stroke();
    dest.restore();
  }

  function paintMap() {
    if (!ctx || !canvas || !mapVisible || overview?.hasAttribute('hidden')) return;
    const dpr = canvas.width / insetW;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = OUTSIDE;
    ctx.fillRect(0, 0, insetW, insetH);
    const view = viewport();
    blit(ctx, view, 0, 0, insetW, insetH);
    blitModern(ctx, view, 0, 0, insetW, insetH);
    marker(ctx,
      (player.e - view.eMin) / M_PER_PX,
      (view.nMax - player.n) / M_PER_PX);
  }

  // ---- the pop-out: the whole field at once --------------------------------

  function layoutFull() {
    if (!fullCanvas || !fullCtx) return;
    // Room for the dialog's own chrome — head, foot, card padding — taken off
    // before the field is fitted, so the map never grows past its card.
    const availW = Math.max(120, Math.min(window.innerWidth - 56, 760));
    const availH = Math.max(120, window.innerHeight - 156);
    const scale = Math.min(availW / fieldE, availH / fieldN);
    const w = Math.max(1, Math.round(fieldE * scale));
    const h = Math.max(1, Math.round(fieldN * scale));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    fullCanvas.style.width = `${w}px`;
    fullCanvas.style.height = `${h}px`;
    fullCanvas.width = Math.round(w * dpr);
    fullCanvas.height = Math.round(h * dpr);
    fullCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    fullSize = { w, h };
  }

  function paintFull() {
    if (!fullCtx || !fullOpen || !fullSize.w) return;
    const { w, h } = fullSize;
    const dpr = fullCanvas.width / w;
    fullCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    fullCtx.fillStyle = OUTSIDE;
    fullCtx.fillRect(0, 0, w, h);
    blit(fullCtx, bounds, 0, 0, w, h);
    blitModern(fullCtx, bounds, 0, 0, w, h);

    // Where the inset is looking, so the two maps read as one instrument.
    const view = viewport();
    const kx = w / fieldE;
    const ky = h / fieldN;
    const rx = (Math.max(view.eMin, bounds.eMin) - bounds.eMin) * kx;
    const ry = (bounds.nMax - Math.min(view.nMax, bounds.nMax)) * ky;
    fullCtx.save();
    fullCtx.strokeStyle = 'rgba(244, 181, 79, .95)';
    fullCtx.lineWidth = 1.5;
    fullCtx.strokeRect(rx, ry,
      Math.max(2, (Math.min(view.eMax, bounds.eMax) - Math.max(view.eMin, bounds.eMin)) * kx),
      Math.max(2, (Math.min(view.nMax, bounds.nMax) - Math.max(view.nMin, bounds.nMin)) * ky));
    fullCtx.restore();

    marker(fullCtx, (player.e - bounds.eMin) * kx, (bounds.nMax - player.n) * ky);
    if (fullFoot) {
      fullFoot.textContent = `${formatDistance(fieldE, units)} east to west, `
        + `${formatDistance(fieldN, units)} north to south. `
        + `The box is what the small map shows.`;
    }
  }

  function setFullVisible(on) {
    const next = !!on && mapVisible;
    if (next === fullOpen) return fullOpen;
    fullOpen = next;
    full?.toggleAttribute('hidden', !fullOpen);
    if (fullOpen) {
      // The pointer is captured while walking; a dialog nobody can click is
      // not a dialog. hud.js releases it for the panel the same way.
      if (document.pointerLockElement) document.exitPointerLock?.();
      layoutFull();
      paintFull();
      fullClose?.focus();
    } else {
      openButton?.focus();
    }
    return fullOpen;
  }

  function update({ e = 0, n = 0, bearingDeg = 0 } = {}) {
    const b = normalBearing(bearingDeg);
    player = { e, n, bearingDeg: b };
    // T-2626: the needle is the instrument ring's heading tick, turned about its centre.
    if (needle) needle.style.transform = `rotate(${b}deg)`;
    if (direction) direction.textContent = cardinal(b);
    if (bearingLabel) bearingLabel.textContent = `${String(Math.round(b) % 360).padStart(3, '0')}°`;
    if (compass) compass.setAttribute('aria-label', `Heading ${cardinal(b)}, ${Math.round(b)} degrees`);
    if (overview) overview.setAttribute('aria-label',
      `Overview map. Position east ${formatDistance(e, units)}, north ${formatDistance(n, units)}; heading ${cardinal(b)}.`);

    if (Math.hypot(e - lastStreet.e, n - lastStreet.n) > 0.35
        || Math.abs(b - lastStreet.bearingDeg) > 2) {
      streetState = streets?.status?.(e, n, b) ?? null;
      eraState = eraWhere?.at?.(e, n, b) ?? null;
      todayState = modern?.at?.(e, n) ?? null;
      paintStreet();
      lastStreet = { e, n, bearingDeg: b };
    }

    if (Math.hypot(e - lastPaint.e, n - lastPaint.n) > 0.08
        || Math.abs(b - lastPaint.bearingDeg) > 0.35) {
      paintMap();
      if (fullOpen) paintFull();
      lastPaint = { e, n, bearingDeg: b };
    }
  }

  function joined(items, key) {
    return [...new Set(items.map((s) => s[key]).filter(Boolean))].join(' & ');
  }

  /**
   * T-2741: the readout under the compass — the street in the scene's own year, and the
   * street and house number there today. 1812 has no streets; it says so and still gives
   * today's. 1835 also says the next cross street ahead (streets.js `status`).
   */
  function paintStreet() {
    const show = streetVisible;
    streetReadout?.toggleAttribute('hidden', !show);
    streetToggle?.setAttribute('aria-pressed', String(show));
    if (!show) return;
    const era = eraState?.place ?? (eraWhere?.empty ? 'no streets yet' : 'no street here');
    // Until today's streets have loaded, a dash rather than a claim that there are none.
    const today = modern ? todayText(todayState) : '—';
    if (streetHistoric) streetHistoric.textContent = era;
    if (streetModern) streetModern.textContent = today;

    const upcoming = streetState?.mode === 'on' ? streetState.upcoming : null;
    if (streetApproach) {
      const text = upcoming
        ? `Approaching ${upcoming.street.name_1835} · ${formatDistance(upcoming.ahead_m, units)}`
        : '';
      streetApproach.textContent = text;
      streetApproach.toggleAttribute('hidden', !text);
    }
    // A street record may carry no modern name: `market_north` does, because N Wacker
    // Drive north of the river is the riverside drive and not that line (T-0451). Say
    // the 1835 name alone rather than reading the word "null" out to a screen reader.
    const upcomingModern = upcoming?.street?.name_2026;
    const approachLabel = upcoming
      ? `. Approaching ${upcoming.street.name_1835}${upcomingModern ? `, today ${upcomingModern}` : ''}, in ${formatDistance(upcoming.ahead_m, units)}.`
      : '';
    streetReadout?.setAttribute('aria-label',
      `In ${year}: ${era}. Today: ${today}${approachLabel}`);
  }

  /** Today's streets, once they have loaded (main.js fetches them after the scene). */
  function setModern(m) {
    modern = m ?? null;
    modernPainted = false;
    lastStreet = { e: Infinity, n: Infinity, bearingDeg: Infinity };
    lastPaint = { e: Infinity, n: Infinity, bearingDeg: Infinity };
    update(player);
  }

  function setWhere(w) {
    eraWhere = w ?? null;
    lastStreet = { e: Infinity, n: Infinity, bearingDeg: Infinity };
    update(player);
  }

  function setCompassVisible(on) {
    compassVisible = !!on;
    compass?.toggleAttribute('hidden', !compassVisible);
    return compassVisible;
  }

  function setMapVisible(on) {
    mapVisible = !!on;
    overview?.toggleAttribute('hidden', !mapVisible);
    // Switching the map off switches off BOTH of it. A pop-out left standing
    // over a hidden inset is the setting not being obeyed.
    if (!mapVisible) setFullVisible(false);
    if (mapVisible) {
      lastPaint = { e: Infinity, n: Infinity, bearingDeg: Infinity };
      paintMap();
    }
    return mapVisible;
  }

  function setStreetVisible(on) {
    streetVisible = !!on;
    paintStreet();
    // Today's streets on the maps follow the same switch.
    lastPaint = { e: Infinity, n: Infinity, bearingDeg: Infinity };
    paintMap();
    if (fullOpen) paintFull();
    return streetVisible;
  }

  function setUnits(value) {
    units = normalUnitSystem(value);
    // Repaint text and accessibility labels immediately; the player may be
    // standing still, so the normal movement threshold would not do it for us.
    lastStreet = { e: Infinity, n: Infinity, bearingDeg: Infinity };
    update(player);
    return units;
  }

  // T-2626: the instrument opens the Map app (a stub that opens this pop-out until the
  // Map app lands), so the wiring is one line to change; without one, the pop-out itself.
  openButton?.addEventListener('click', () => (onOpen && !fullOpen ? onOpen() : setFullVisible(!fullOpen)));
  fullClose?.addEventListener('click', () => setFullVisible(false));
  // The backdrop, but not the card standing on it.
  full?.addEventListener('click', (e) => {
    if (e.target === full) setFullVisible(false);
  });
  // `m` for the map, and Escape to put it away. The typing test is imported
  // rather than rewritten: pointerlock.js owns the one definition of "a text
  // field has focus", and a second opinion here is how W-A-S-D once walked the
  // camera off while somebody typed a building's name.
  window.addEventListener('keydown', (e) => {
    // A synthetic event can arrive without a `key`, and an uncaught TypeError
    // in a keydown listener is a pageerror, which is a release gate.
    if (!e.key || isTyping(e.target)) return;
    if (e.key === 'Escape') { if (fullOpen) setFullVisible(false); return; }
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    // T-2654: M opens the Navigator's Map, as the instrument does; the pop-out without one.
    if (e.key.toLowerCase() === 'm') { e.preventDefault(); if (onOpen && !fullOpen) onOpen(); else setFullVisible(!fullOpen); }
  });

  window.addEventListener('resize', resize);
  resize();

  return {
    bounds,
    update,
    // T-2654: what the Navigator's Map app draws with — the same whole-field picture,
    // the same arrow and the same footprints — so the device and the inset agree.
    outlines,
    get player() { return { ...player }; },
    field() { return { ...bounds, widthM: fieldE, depthM: fieldN }; },
    /** Paint the whole field into `dest` (already scaled to CSS px), `w` x `h`. */
    drawField(dest, w, h) {
      if (!bgPainted) paintBackground();
      dest.fillStyle = OUTSIDE;
      dest.fillRect(0, 0, w, h);
      blit(dest, bounds, 0, 0, w, h);
      blitModern(dest, bounds, 0, 0, w, h);
    },
    /** Paint the window `view` ({ eMin, eMax, nMin, nMax }, metres) of the field into `dest`.
     *  T-2741: with the street names on, today's streets are stroked over it (crisp at any
     *  zoom, so not the inset's layer) and, close up, named. */
    drawView(dest, view, w, h) {
      if (!bgPainted) paintBackground();
      dest.fillStyle = OUTSIDE;
      dest.fillRect(0, 0, w, h);
      blit(dest, view, 0, 0, w, h);
      if (streetVisible && modern) {
        const k = w / (view.eMax - view.eMin);
        strokeModern(dest, (e, n) => [(e - view.eMin) * k, (view.nMax - n) * k], 1.2, view);
        labelModern(dest, view, w, h);
      }
    },
    drawMarker(dest, x, y) { marker(dest, x, y); },
    setCompassVisible,
    setMapVisible,
    setStreetVisible,
    setModern,
    setWhere,
    setFullVisible,
    setUnits,
    get compassVisible() { return compassVisible; },
    get mapVisible() { return mapVisible; },
    get fullOpen() { return fullOpen; },
    get streetVisible() { return streetVisible; },
    get units() { return units; },
    get streetState() { return streetState; },
    /** T-2741: the scene year's place (where.js) and today's (modern-streets.js). */
    get eraState() { return eraState; },
    get todayState() { return todayState; },
    get modernLoaded() { return !!modern; },
    /** T-2650: the scene draws no streets of its own year (1812), for the Confidence view's overlays. */
    get eraEmpty() { return !!eraWhere?.empty; },
    snapshot() {
      return {
        ...player, compassVisible, mapVisible, streetVisible, streetState, eraState, todayState, units,
        bounds: { ...bounds },
        // The window, so a test can assert that it MOVES and that it CLAMPS
        // without reading pixels back out of a canvas.
        inset: { w: insetW, h: insetH, mPerPx: M_PER_PX },
        viewport: viewport(),
        fullOpen,
      };
    },
  };
}
