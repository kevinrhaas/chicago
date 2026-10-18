/**
 * The Confidence view's overlays (T-2650, NAV-605; DESIGN §09, M9: "Overlays sit at the
 * bottom of the app: street names, building labels, people pins and the Jaunt route").
 *
 * Four switches at the foot of the Confidence view, each on its own. Each draws only what
 * the destination's data has, and its line says what that is, or that there is none:
 *
 *   Street names    T-2741's street readout under the compass (and today's streets on the
 *                   Map): the same switch as Settings › Show and the compass's own button,
 *                   through hud.setToggle('streetNames'). 1812 draws no streets, so it says
 *                   only today's names show there.
 *   Building labels the name the building card and the target tag already give a building
 *                   (display-name.js, cleaned by the card's own cardTitle; its lead phrase),
 *                   floated over the nearest few in sight, each name once. Only buildings with a name of their own: "A vacant
 *                   dwelling" is a description, not a name, and is not labelled. A building
 *                   at a grade the Confidence view hides is not labelled either.
 *   People pins     plain markers (L1: no figure is drawn) on the addresses the people
 *                   directory gives (`lives_at`, `works_at`) — the same directory the People
 *                   app reads. A pin lists who is there, with the standing-review line any
 *                   flagged record carries, and a name opens that person's card.
 *   Jaunt route     the Map app's dotted route through the active Jaunt's stops
 *                   (ctx.actions.jauntRoute), stood up in the town, the next stop ringed.
 *
 * Performance: none of this is scene geometry. The three in-town overlays are one DOM layer
 * over the canvas, placed from the camera's own matrices once an animation frame, and that
 * loop runs only while one of them is on: with all three off there is no loop, no listener
 * and no layer work at all, so the frame costs nothing. A switch never touches the scene.
 *
 * Choices hold for the visit (street names keep their own Settings choice). The persistence
 * of the Confidence view itself is T-2649's, and this module does not write it.
 */
import { t as str } from './strings/index.js';
import { gradeTerm } from './strings/terms.js';
import { displayName } from './display-name.js';
import { cardTitle } from './fallback-summary.js';
import './strings/confidence-overlays.js';

export const OVERLAYS = Object.freeze(['streets', 'labels', 'people', 'route']);
/** How many labels at once, and how far (m): a phone gets fewer, so the town stays legible. */
export const LABELS = Object.freeze({ phone: 6, desk: 12, withinM: 140 });
/** People pins further than this (m) are not drawn. */
export const PINS_WITHIN_M = 400;
/** Names in one pin's list before "and N more in People". */
export const PIN_LIST_MAX = 8;
const s = (key, vars) => str(`confidence-overlays.${key}`, vars);

// ---- pure helpers (tools/test_confidence_overlays.mjs drives each) -------------------- //

/**
 * A label is a name, not the card's whole title: the title's lead phrase, before its first
 * aside — "The Burns house, on the north bank…" is labelled "The Burns house", "1730 Prairie
 * Avenue — Brick masonry" is labelled by its address. The card keeps the full title.
 */
export function labelText(title) {
  const lead = String(title ?? '').split(/\s\(|[,:]\s|\s[—–]\s/)[0].trim();
  return lead.length >= 4 ? lead : String(title ?? '').trim();
}

/** A building's own name for a label — the card's title, its lead phrase — or null when it has none. */
export function ownName(record, id) {
  const raw = displayName(record?.sidecar ?? {}, id ?? '').title;
  const title = labelText(cardTitle(raw).title);
  if (!title || /^(A|An)\s/.test(title) || /[a-z0-9]_[a-z0-9]/i.test(title)) return null;
  return title;
}

/** The card's title for a place, generic or not (a pin says where it stands). */
export function placeName(record, id) {
  const title = cardTitle(displayName(record?.sidecar ?? {}, id ?? '').title).title;
  return title && !/[a-z0-9]_[a-z0-9]/i.test(title) ? title : 'A building';
}

export function centroid(ring) {
  let e = 0, n = 0;
  for (const [x, y] of ring) { e += x; n += y; }
  return [e / ring.length, n / ring.length];
}

/**
 * The labellable buildings: every footprint whose record has a name of its own, at its
 * centre and roof height. `heightOf(id, record)` gives metres.
 */
export function labelSet(outlines, registry, heightOf = () => 8) {
  const out = [];
  for (const ring of outlines ?? []) {
    if (!ring?.id || !(ring.length >= 3)) continue;
    const record = registry?.get?.(ring.id) ?? null;
    const name = ownName(record, ring.id);
    if (!name) continue;
    const [e, n] = centroid(ring);
    out.push({ id: ring.id, e, n, h: heightOf(ring.id, record), name, grade: ring.grade ?? null });
  }
  return out;
}

/**
 * The people directory as pins: one per address, with who lives or works there. A person
 * the directory marks absent at the scene date is left off. `where(id)` gives { e, n }
 * for a structure, or null (an address the town does not draw gets no pin).
 */
export function pinPlaces(people, where) {
  const byPlace = new Map();
  let count = 0;
  for (const p of people ?? []) {
    if (!p?.id || !p.name || p.present === 'absent') continue;
    let placed = false;
    for (const [key, how] of [['lives_at', 'lives'], ['works_at', 'works']]) {
      const at = p[key];
      if (!at) continue;
      if (!byPlace.has(at)) {
        const pos = where(at);
        byPlace.set(at, pos && Number.isFinite(pos.e) && Number.isFinite(pos.n) ? { id: at, e: pos.e, n: pos.n, people: [] } : null);
      }
      const place = byPlace.get(at);
      if (!place || place.people.some((x) => x.id === p.id)) continue;
      place.people.push({ id: p.id, name: p.name, how, grade: p.grade ?? null, review: p.review_required === true });
      placed = true;
    }
    if (placed) count++;
  }
  const places = [...byPlace.values()].filter(Boolean);
  for (const place of places) place.people.sort((a, b) => (a.how === b.how ? a.name.localeCompare(b.name) : a.how === 'lives' ? -1 : 1));
  return { places, people: count };
}

/** NDC through a camera's own matrices (three's column-major arrays); null without one. */
export function projector(camera) {
  const v = camera?.matrixWorldInverse?.elements, p = camera?.projectionMatrix?.elements;
  if (!v || !p) return null;
  return (x, y, z) => {
    const vx = v[0] * x + v[4] * y + v[8] * z + v[12];
    const vy = v[1] * x + v[5] * y + v[9] * z + v[13];
    const vz = v[2] * x + v[6] * y + v[10] * z + v[14];
    const vw = v[3] * x + v[7] * y + v[11] * z + v[15];
    const cw = p[3] * vx + p[7] * vy + p[11] * vz + p[15] * vw;
    return {
      x: (p[0] * vx + p[4] * vy + p[8] * vz + p[12] * vw) / cw,
      y: (p[1] * vx + p[5] * vy + p[9] * vz + p[13] * vw) / cw,
      z: (p[2] * vx + p[6] * vy + p[10] * vz + p[14] * vw) / cw,
      w: cw,
    };
  };
}

/** A local ENU point (metres) on screen: { x, y } in CSS px, or null behind or far off it. */
export function toScreen(project, e, n, up, w, h, margin = 0.1) {
  const q = project(e, up, -n); // enuToWorld: (e, y, -n)
  if (!(q.w > 0) || q.z > 1 || Math.abs(q.x) > 1 + margin || Math.abs(q.y) > 1 + margin) return null;
  return { x: (q.x + 1) / 2 * w, y: (1 - q.y) / 2 * h };
}

/**
 * The labels to draw this frame: the nearest named buildings in sight within `withinM`,
 * not at a hidden grade, none overlapping a nearer one, at most `max`.
 */
export function pickLabels(set, { player, project, w, h, ground = () => 0, hidden = [], max = 12, withinM = 140 }) {
  const near = [];
  for (const b of set) {
    if (b.grade && hidden.includes(b.grade)) continue;
    const d = Math.hypot(b.e - player.e, b.n - player.n);
    if (d <= withinM) near.push([d, b]);
  }
  near.sort((a, b) => a[0] - b[0]);
  const out = [], boxes = [], said = new Set();
  for (const [d, b] of near) {
    if (out.length >= max) break;
    // One label per name: a house and its alley building, or a fort's parts, are named once.
    const key = b.name.toLowerCase().replace(/\b[nsew]\.\s/g, '');
    if (said.has(key)) continue;
    const at = toScreen(project, b.e, b.n, ground(b.e, b.n) + b.h + 2, w, h, 0);
    if (!at) continue;
    const bw = Math.min(220, 18 + b.name.length * 6.4), bh = 24;
    const box = [at.x - bw / 2, at.y - bh, at.x + bw / 2, at.y];
    if (boxes.some((o) => box[0] < o[2] && box[2] > o[0] && box[1] < o[3] && box[3] > o[1])) continue;
    boxes.push(box);
    said.add(key);
    out.push({ ...b, x: at.x, y: at.y, d });
  }
  return out;
}

/** The words under each switch: what this destination has for it, or that it has none. */
export function notes({ year, streetsEmpty = false, labels = 0, hiddenGrades = 0, people = null, route = null, jaunts = null }) {
  const out = {};
  out.streets = { ok: true, text: s(streetsEmpty ? 'streets.none' : 'streets.note', { year }) };
  out.labels = labels > 0
    ? { ok: true, text: [s(labels === 1 ? 'labels.one' : 'labels.note', { count: labels.toLocaleString('en-US'), year }), hiddenGrades ? s('labels.hidden') : ''].filter(Boolean).join(' ') }
    : { ok: false, text: s('labels.none', { year }) };
  if (people === 'reading') out.people = { ok: true, text: s('people.reading') };
  else if (!people) out.people = { ok: false, text: s('people.none', { year }) };
  else if (!people.places.length) out.people = { ok: false, text: s('people.nowhere', { year }) };
  else out.people = { ok: true, text: s('people.note', { people: people.people.toLocaleString('en-US'), places: people.places.length, year }) };
  if (route?.stops?.length) out.route = { ok: true, text: s('route.note', { stops: route.stops.length }) };
  else if (route) out.route = { ok: true, text: s('route.nowhere') };
  else if (jaunts === 0) out.route = { ok: false, text: s('route.none', { year }) };
  else out.route = { ok: true, text: s('route.idle') };
  return out;
}

// ---- the layer -------------------------------------------------------------------- //

const shared = new WeakMap();

/** The page's one overlay controller (one per document), made on first use. */
export function overlaysFor(doc, ctx = {}) {
  let o = shared.get(doc);
  if (!o) { o = createOverlays(doc); shared.set(doc, o); }
  o.bind(ctx);
  return o;
}

export function createOverlays(doc) {
  const win = doc.defaultView ?? globalThis;
  const raf = (fn) => (win.requestAnimationFrame ? win.requestAnimationFrame(fn) : setTimeout(fn, 16));
  const caf = (id) => (win.cancelAnimationFrame ? win.cancelAnimationFrame(id) : clearTimeout(id));
  let ctx = {};
  const on = { labels: false, people: false, route: false };
  let layer = null, svg = null, path = null, pop = null;
  const pool = { labels: new Map(), pins: new Map(), stops: [] };
  let frameId = null, frames = 0;
  let labels = null, labelsAt = -1, bounds = null;
  let people = undefined, peopleLoading = null; // undefined: not asked; null: none
  let jaunts = null;
  const drawn = { labels: 0, pins: 0, stops: 0 };
  const api = () => ctx.api ?? {};
  const year = () => ctx.scene?.id ?? api().scene?.id ?? api().year ?? '';
  const make = (tag, cls) => { const e = doc.createElement(tag); if (cls) e.className = cls; return e; };

  function heightOf(id, record) {
    bounds ??= api().buildings?.instanceBounds?.() ?? {};
    const h = bounds[id]?.size?.[1] ?? record?.sidecar?.attributes?.wall_height_m?.value;
    return Number.isFinite(h) && h > 0 ? h : 8;
  }
  function labelList() {
    const size = api().registry?.size ?? 0;
    if (!labels || size !== labelsAt) { labels = labelSet(api().navigation?.outlines, api().registry, heightOf); labelsAt = size; }
    return labels;
  }
  function where(id) {
    const a = api();
    const pos = a.structurePosition?.(id);
    if (!pos) return null;
    return { ...pos, h: heightOf(id, a.registry?.get?.(id) ?? null) };
  }
  /** The people directory, read once (the People app's own, already in hand in 1835). */
  function loadPeople() {
    if (people !== undefined || peopleLoading) return peopleLoading ?? Promise.resolve(people);
    const ask = ctx.actions?.peopleDirectory;
    if (!ask) { people = null; return Promise.resolve(null); }
    peopleLoading = Promise.resolve().then(() => ask()).catch(() => null).then((dir) => {
      const rows = dir?.people ?? null;
      people = rows ? pinPlaces(rows, where) : null;
      peopleLoading = null;
      return people;
    });
    return peopleLoading;
  }
  function loadJaunts() {
    if (jaunts !== null) return;
    jaunts = undefined;
    Promise.resolve().then(() => ctx.actions?.jauntCatalog?.(year())).then((list) => { jaunts = Array.isArray(list) ? list.length : undefined; }, () => { jaunts = undefined; });
  }

  function ensureLayer() {
    if (layer) return layer;
    layer = make('div', 'cv-overlays');
    layer.id = 'cv-overlays';
    svg = doc.createElementNS ? doc.createElementNS('http://www.w3.org/2000/svg', 'svg') : make('svg');
    svg.setAttribute('class', 'cv-route');
    svg.setAttribute('aria-hidden', 'true');
    path = doc.createElementNS ? doc.createElementNS('http://www.w3.org/2000/svg', 'path') : make('path');
    svg.append(path);
    layer.append(svg);
    (doc.body ?? doc.documentElement)?.append?.(layer);
    return layer;
  }

  function place(el, x, y) {
    el.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px)`;
    el.hidden = false;
  }
  function hideRest(map, keep) { for (const [k, el] of map) if (!keep.has(k)) el.hidden = true; }

  function closePop() { if (pop) { pop.remove?.(); pop = null; } }
  function openPop(placeRec, x, y) {
    closePop();
    const a = api();
    pop = make('div', 'cv-pop');
    pop.id = 'cv-pop';
    pop.setAttribute('role', 'dialog');
    const title = placeName(a.registry?.get?.(placeRec.id) ?? null, placeRec.id);
    pop.setAttribute('aria-label', title);
    const head = make('div', 'cv-pop-head');
    const name = make('strong', 'cv-pop-title');
    name.textContent = title;
    const close = make('button', 'cv-pop-close');
    close.type = 'button';
    close.textContent = '×';
    close.setAttribute('aria-label', s('people.close'));
    close.addEventListener('click', closePop);
    head.append(name, close);
    const list = make('ul', 'cv-pop-list');
    for (const p of placeRec.people.slice(0, PIN_LIST_MAX)) {
      const li = make('li');
      const b = make('button', 'cv-pop-person');
      b.type = 'button';
      b.dataset.person = p.id;
      const who = make('span', 'cv-pop-name');
      who.textContent = p.name;
      const sub = make('span', 'cv-pop-sub');
      sub.textContent = [s(p.how === 'works' ? 'people.works' : 'people.lives'), gradeTerm(p.grade).label].filter(Boolean).join(' · ');
      b.append(who, sub);
      if (p.grade) b.dataset.grade = p.grade;
      b.addEventListener('click', () => { closePop(); ctx.actions?.openPerson?.(p.id); });
      li.append(b);
      if (p.review) {
        const note = make('span', 'cv-pop-review');
        note.textContent = s('people.review');
        li.append(note);
      }
      list.append(li);
    }
    pop.append(head, list);
    pop.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') { ev.stopPropagation?.(); closePop(); } });
    const more = placeRec.people.length - PIN_LIST_MAX;
    if (more > 0) {
      const b = make('button', 'cv-pop-more');
      b.type = 'button';
      b.textContent = s('people.more', { count: more });
      b.addEventListener('click', () => { closePop(); void ctx.navigator?.select?.('people'); });
      pop.append(b);
    }
    const w = win.innerWidth || 390, h = win.innerHeight || 780;
    pop.style.left = `${Math.round(Math.min(Math.max(12, x - 130), w - 272))}px`;
    pop.style.top = `${Math.round(Math.min(Math.max(12, y + 14), h - 220))}px`;
    ensureLayer().append(pop);
    close.focus?.({ preventScroll: true });
  }

  function pinEl(placeRec) {
    let el = pool.pins.get(placeRec.id);
    if (el) return el;
    el = make('button', 'cv-pin');
    el.type = 'button';
    el.dataset.place = placeRec.id;
    const count = placeRec.people.length;
    el.textContent = count > 1 ? String(count) : '';
    el.setAttribute('aria-label', count === 1 ? s('people.pin.one', { name: placeRec.people[0].name }) : s('people.pin', { count }));
    el.addEventListener('click', (ev) => { ev?.stopPropagation?.(); openPop(placeRec, el._x ?? 0, el._y ?? 0); });
    ensureLayer().append(el);
    pool.pins.set(placeRec.id, el);
    return el;
  }

  /** One frame of the in-town overlays. Returns what it drew, for the harness. */
  function frame() {
    const a = api();
    const project = projector(a.camera);
    const w = win.innerWidth || 0, h = win.innerHeight || 0;
    const player = a.player ?? { e: 0, n: 0 };
    const ground = (e, n) => a.terrain?.surfaceHeight?.(e, n) ?? 0;
    drawn.labels = drawn.pins = drawn.stops = 0;
    if (!project || !layer) return drawn;
    // Building labels.
    const keepL = new Set();
    const labelled = new Map(); // id -> the label's top, so a pin on the same roof stands above it
    if (on.labels) {
      const phone = ctx.isPhone ?? (win.matchMedia?.('(max-width: 620px)')?.matches ?? false);
      const picked = pickLabels(labelList(), { player, project, w, h, ground, hidden: a.hud?.hiddenLevels ?? [],
        max: phone ? LABELS.phone : LABELS.desk, withinM: LABELS.withinM });
      for (const b of picked) {
        let el = pool.labels.get(b.id);
        if (!el) {
          el = make('span', 'cv-label');
          el.setAttribute('aria-hidden', 'true');
          el.textContent = b.name;
          if (b.grade) el.dataset.grade = b.grade;
          layer.append(el);
          pool.labels.set(b.id, el);
        }
        place(el, b.x, b.y);
        keepL.add(b.id);
        labelled.set(b.id, b.y);
      }
      drawn.labels = picked.length;
    }
    hideRest(pool.labels, keepL);
    // People pins.
    const keepP = new Set();
    if (on.people && people?.places?.length) {
      for (const pl of people.places) {
        if (Math.hypot(pl.e - player.e, pl.n - player.n) > PINS_WITHIN_M) continue;
        const at = toScreen(project, pl.e, pl.n, ground(pl.e, pl.n) + (pl.h ?? heightOf(pl.id, a.registry?.get?.(pl.id))) + 4, w, h, 0);
        if (!at) continue;
        const el = pinEl(pl);
        const y = labelled.has(pl.id) ? Math.min(at.y, labelled.get(pl.id) - 28) : at.y;
        el._x = at.x; el._y = y;
        place(el, at.x, y);
        keepP.add(pl.id);
      }
      drawn.pins = keepP.size;
    }
    hideRest(pool.pins, keepP);
    // The Jaunt route: dotted between stops in front of you, each stop numbered.
    let d = '';
    const route = on.route ? ctx.actions?.jauntRoute?.() ?? null : null;
    const pts = (route?.stops ?? []).map(([e, n]) => toScreen(project, e, n, ground(e, n) + 2, w, h, 4));
    pts.forEach((p, i) => {
      if (!p) return;
      const prev = pts[i - 1];
      d += prev ? ` L${p.x.toFixed(1)} ${p.y.toFixed(1)}` : ` M${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
    });
    path.setAttribute('d', d.trim());
    pts.forEach((p, i) => {
      let el = pool.stops[i];
      if (!el) {
        el = make('span', 'cv-stop');
        el.setAttribute('aria-hidden', 'true');
        el.textContent = String(i + 1);
        layer.append(el);
        pool.stops[i] = el;
      }
      el.classList.toggle('is-next', i === route.at);
      if (p && Math.abs(p.x - w / 2) <= w * 0.55 && Math.abs(p.y - h / 2) <= h * 0.55) { place(el, p.x, p.y); drawn.stops++; } else el.hidden = true;
    });
    for (let i = pts.length; i < pool.stops.length; i++) pool.stops[i].hidden = true;
    return drawn;
  }

  function loop() {
    frameId = null;
    if (!running()) return;
    frames++;
    try { frame(); } catch { /* an overlay never stops the town */ }
    frameId = raf(loop);
  }
  const running = () => on.labels || on.people || on.route;
  function sync() {
    if (running()) {
      ensureLayer().hidden = false;
      if (frameId == null) frameId = raf(loop);
    } else {
      if (frameId != null) caf(frameId);
      frameId = null;
      closePop();
      if (layer) layer.hidden = true;
    }
    if (!on.people) closePop();
  }

  const handle = {
    bind(next) { ctx = { ...ctx, ...next }; if (ctx.api) ctx.api.confidenceOverlays = handle; },
    /** Is this overlay on? Street names read the HUD's own setting. */
    get(id) {
      if (id === 'streets') return api().hud?.settings?.streetNames !== false;
      return !!on[id];
    },
    async set(id, value) {
      const v = !!value;
      if (id === 'streets') { api().hud?.setToggle?.('streetNames', v); return v; }
      if (!(id in on)) return false;
      if (id === 'people' && v) await loadPeople();
      on[id] = v;
      sync();
      return v;
    },
    /** What each switch has here, for its line (and whether it can be turned on at all). */
    notes() {
      const a = api();
      const hidden = a.hud?.hiddenLevels ?? [];
      return notes({
        year: year(),
        streetsEmpty: a.navigation?.eraEmpty === true,
        labels: labelList().length,
        hiddenGrades: hidden.length,
        people: peopleLoading ? 'reading' : people,
        route: ctx.actions?.jauntRoute?.() ?? null,
        jaunts,
      });
    },
    prepare() { loadJaunts(); return loadPeople(); },
    frame,
    closePop,
    get running() { return frameId != null; },
    get frames() { return frames; },
    get drawn() { return { ...drawn }; },
    get layer() { return layer; },
    get places() { return people?.places?.length ?? 0; },
    /** For the harness: where a label or a pin would stand (field metres), nothing drawn. */
    get labelSet() { return labelList().map(({ id, e, n, grade }) => ({ id, e, n, grade })); },
    get pinPlaces() { return (people?.places ?? []).map(({ id, e, n, people: here }) => ({ id, e, n, count: here.length })); },
  };
  return handle;
}

// ---- the switches, at the foot of the Confidence view ------------------------------- //

/**
 * Append the Overlays block to the Confidence view's screen `el`. Mounted once per open of
 * the app (apps/confidence-view.js); the overlays themselves outlive it, so a switch left
 * on keeps drawing after the device closes.
 */
export function mountOverlays(el, ctx = {}) {
  const doc = el.ownerDocument;
  const win = doc.defaultView ?? globalThis;
  const ov = overlaysFor(doc, ctx);
  const make = (tag, cls, text) => { const e = doc.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  const block = make('section', 'nav-block cv-ov');
  block.id = 'cv-ov';
  block.setAttribute('aria-label', s('group'));
  block.append(make('span', 'nav-k', s('title')));
  const rows = {};
  for (const id of OVERLAYS) {
    const box = make('input');
    box.type = 'checkbox';
    box.id = `cv-ov-${id}`;
    const note = make('span', 'nav-sub cv-ov-note');
    note.id = `cv-ov-${id}-note`;
    box.setAttribute('aria-describedby', note.id);
    const label = make('label', 'cv-ov-row');
    label.dataset.overlay = id;
    label.append(box, make('span', 'cv-ov-name', s(id)), note);
    box.addEventListener('change', async () => { await ov.set(id, box.checked); paint(); });
    block.append(label);
    rows[id] = { box, note, label };
  }
  el.append(block);
  function paint() {
    const n = ov.notes();
    for (const id of OVERLAYS) {
      const r = rows[id];
      const isOn = ov.get(id);
      r.box.checked = isOn;
      // A layer this destination does not have cannot be switched on; one left on stays
      // switchable so it can be turned off.
      r.box.disabled = !n[id].ok && !isOn;
      r.label.classList.toggle('is-off', !n[id].ok);
      if (r.note.textContent !== n[id].text) r.note.textContent = n[id].text;
    }
  }
  void ov.prepare().then(paint, () => {});
  paint();
  // The lines follow the town: a Jaunt starting, the directory arriving, a grade hidden.
  const timer = win.setInterval?.(() => {
    if (el.isConnected === false || block.isConnected === false) { win.clearInterval(timer); return; }
    paint();
  }, 1000);
  timer?.unref?.(); // a test's stand-in page never keeps its process alive
  return { paint, overlays: ov };
}
