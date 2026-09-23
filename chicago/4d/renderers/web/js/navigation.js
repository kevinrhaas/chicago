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
const INSET = { wide: { w: 248, h: 98 }, narrow: { w: 188, h: 76 } };
const INSET_SPAN_E_M = 2020;
const M_PER_PX = INSET_SPAN_E_M / INSET.wide.w;
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
    out.push(polygon.map(([u, v]) => [
      e0 + u * cos + v * sin,
      n0 - u * sin + v * cos,
    ]));
  }
  return out;
}

export function createNavigation({ root, terrain, registry, streets } = {}) {
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
  const streetMode = root?.querySelector('#street-mode');
  const streetHistoric = root?.querySelector('#street-historic');
  const streetModern = root?.querySelector('#street-modern');
  const streetApproach = root?.querySelector('#street-approach');
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
    if (needle) needle.style.transform = `translate(-50%, -88%) rotate(${b}deg)`;
    if (direction) direction.textContent = cardinal(b);
    if (bearingLabel) bearingLabel.textContent = `${String(Math.round(b) % 360).padStart(3, '0')}°`;
    if (compass) compass.setAttribute('aria-label', `Heading ${cardinal(b)}, ${Math.round(b)} degrees`);
    if (overview) overview.setAttribute('aria-label',
      `Overview map. Position east ${formatDistance(e, units)}, north ${formatDistance(n, units)}; heading ${cardinal(b)}.`);

    if (Math.hypot(e - lastStreet.e, n - lastStreet.n) > 0.35
        || Math.abs(b - lastStreet.bearingDeg) > 2) {
      streetState = streets?.status?.(e, n, b) ?? null;
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

  function paintStreet() {
    const show = streetVisible && !!streetState;
    streetReadout?.toggleAttribute('hidden', !show);
    if (!show) return;
    const records = streetState.streets ?? [];
    const historic = joined(records, 'name_1835');
    const modern = joined(records, 'name_2026');
    let mode = 'On street';
    if (streetState.mode === 'intersection') mode = 'At intersection';
    if (streetState.mode === 'ahead') {
      mode = `Ahead · ${formatDistance(streetState.distance_m, units)}`;
    }
    if (streetMode) streetMode.textContent = mode;
    if (streetHistoric) streetHistoric.textContent = historic;
    if (streetModern) streetModern.textContent = `Today: ${modern}`;

    const upcoming = streetState.upcoming;
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
      `${mode}. In 1835: ${historic}. Today: ${modern}${approachLabel}`);
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

  openButton?.addEventListener('click', () => setFullVisible(!fullOpen));
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
    if (e.key.toLowerCase() === 'm') { e.preventDefault(); setFullVisible(!fullOpen); }
  });

  window.addEventListener('resize', resize);
  resize();

  return {
    bounds,
    update,
    setCompassVisible,
    setMapVisible,
    setStreetVisible,
    setFullVisible,
    setUnits,
    get compassVisible() { return compassVisible; },
    get mapVisible() { return mapVisible; },
    get fullOpen() { return fullOpen; },
    get streetVisible() { return streetVisible; },
    get units() { return units; },
    get streetState() { return streetState; },
    snapshot() {
      return {
        ...player, compassVisible, mapVisible, streetVisible, streetState, units,
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
