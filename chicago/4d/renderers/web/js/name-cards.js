// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * name-cards.js — a small card hovering over each person, with their name (T-3614).
 *
 * The owner, 2026-11-16: *"an option setting that is default on that puts a small 3d hovering
 * card floating over each person of what their name is, clicking on the card brings up their
 * detail, make sure the names fit and follow the style of the app"*, and *"For all years jaunt
 * people and time"*. So in every year, at every hour, each named person drawn in town (on foot,
 * on a driver's box, a jaunt's host, a jaunt stop's castmates) carries a card above their head:
 * the appearance's own panel, edge and accent light, and their name, set small enough to fit.
 *
 * THE CARD IS IN THE SCENE, NOT ON THE GLASS. It stands at its person's head, faces the camera
 * and is depth-tested, so a house in front hides it as it hides them. It keeps a readable size
 * on the screen as the visitor walks off (CARD_PX, from near to far), and fades at its reach.
 *
 * WHAT IT COSTS. All the cards are ONE instanced draw over ONE atlas: a slot per card, drawn once
 * on a 2-D canvas when its person comes near and copied into the atlas's own slot (a sub-upload
 * of one slot, never the atlas). The nearest few within reach are carded (NAME_CARD_TIERS, by the
 * scene detail: a phone on Light keeps 14 within 28 m); the rest pay a distance test five times
 * a second. A slot is redrawn only when the appearance or the fonts change. The atlas is
 * `atlasBytes(tier)`: 3.4 MiB on Light, 5.3 on Balanced, 6.8 on Full, with no mipmaps.
 *
 * Pure halves for the gate (tools/test_name_cards.mjs): `fitName` (the name's size, cut only
 * past the smallest size), `chooseCards` (who is carded), `cardPx` (the size on screen),
 * `cardTheme` (an appearance's colours from its CSS) and `pickCard` (the card under a point).
 */

/** How many cards, and out to how far, by the scene detail in force. */
export const NAME_CARD_TIERS = Object.freeze({
  full: Object.freeze({ max: 32, reach: 48 }),
  balanced: Object.freeze({ max: 24, reach: 40 }),
  light: Object.freeze({ max: 14, reach: 28 }),
});
/** The slot drawn for one card, in atlas pixels: the card's body and the notch under it. */
export const SLOT_W = 512;
export const SLOT_H = 96;
export const BODY_H = 72;
export const NOTCH_H = 14;
export const ATLAS_W = 1024;
/** The name's type on one line, largest first; then on two (NAME_SIZES_2), smaller. */
export const NAME_SIZES = Object.freeze([32, 30, 28, 26]);
export const NAME_SIZES_2 = Object.freeze([26, 24, 22, 20]);
/** A slot's height on screen, CSS pixels, near and at reach. */
export const CARD_PX = Object.freeze({ near: 40, far: 30 });
/** Metres above the top of the head to the foot of the notch. */
export const LIFT_M = 0.2;
/** Seconds between choosing who is carded; and a new card's fade, in and out. */
export const CHOOSE_S = 0.2;
export const FADE_S = 0.25;
/** A card's metres from its reach over which it fades away. */
export const EDGE_M = 6;
/** New slots drawn in one frame at most: a crowd coming into reach is drawn over a few. */
export const DRAWS_PER_FRAME = 3;
/** Slots beyond the carded, for cards fading out while new ones fade in. */
export const SPARE = 4;
/** The atlas's bytes for a tier: two columns of slots, RGBA. */
export const atlasBytes = (tier) => ATLAS_W * Math.ceil(((NAME_CARD_TIERS[tier] ?? NAME_CARD_TIERS.full).max + SPARE) / 2) * SLOT_H * 4;

const PAD_L = 20, PAD_R = 22, LIGHT_D = 12, LIGHT_GAP = 12, BORDER = 2;
export const TEXT_MAX = SLOT_W - PAD_L - LIGHT_D - LIGHT_GAP - PAD_R;

/**
 * The name at the largest size that fits TEXT_MAX on one line, else on two lines broken at the
 * space that evens them (a long 1812 label, "A man of the Chicago militia, name not recorded (1 of
 * 6)"), each `measure(text, size)` → pixels. Past the smallest two-line size the second line is
 * cut with an ellipsis; tools/test_name_cards.mjs holds that at zero for every person of every
 * year, at a wider measure than any appearance's type.
 */
export function fitName(name, measure, { sizes = NAME_SIZES, sizes2 = NAME_SIZES_2, max = TEXT_MAX } = {}) {
  const text = String(name ?? '').replace(/\s+/g, ' ').trim();
  for (const size of sizes) {
    const width = measure(text, size);
    if (width <= max) return { lines: [text], size, width, cut: false };
  }
  const words = text.split(' ');
  const split = (size) => {
    let best = null;
    for (let i = 1; i < words.length; i++) {
      const a = words.slice(0, i).join(' '), b = words.slice(i).join(' ');
      const w = Math.max(measure(a, size), measure(b, size));
      if (!best || w < best.width) best = { lines: [a, b], width: w };
    }
    return best;
  };
  for (const size of sizes2) {
    const best = split(size);
    if (best && best.width <= max) return { ...best, size, cut: false };
  }
  const size = sizes2[sizes2.length - 1];
  const best = split(size) ?? { lines: [text, ''] };
  const fit = (t) => { let cut = t; while (cut.length > 1 && measure(`${cut}…`, size) > max) cut = cut.slice(0, -1).trimEnd(); return cut; };
  let [a, b] = best.lines;
  if (measure(a, size) > max) a = `${fit(a)}…`;
  if (b && measure(b, size) > max) b = `${fit(b)}…`;
  const lines = b ? [a, b] : [a];
  return { lines, size, width: Math.max(...lines.map((l) => measure(l, size))), cut: true };
}

/** The candidates within `reach` and in view, nearest first, at most `max`. */
export function chooseCards(candidates, { max, reach }) {
  return candidates.filter((c) => Number.isFinite(c.distance) && c.distance <= reach && c.inView !== false)
    .sort((a, b) => a.distance - b.distance).slice(0, max);
}

/** A slot's height on screen at `distance`, CSS pixels: CARD_PX.near close by, .far at reach. */
export function cardPx(distance, reach, px = CARD_PX) {
  const t = Math.min(1, Math.max(0, (distance - 2) / Math.max(1, reach - 2)));
  return px.near + (px.far - px.near) * t;
}

/** How much a card at `distance` shows for its reach: 1 inside, falling to 0 over EDGE_M. */
export function reachAlpha(distance, reach, edge = EDGE_M) {
  if (distance <= reach - edge) return 1;
  if (distance >= reach) return 0;
  const t = (reach - distance) / edge;
  return t * t * (3 - 2 * t);
}

/** An appearance's card from its CSS custom properties (`read(name)` → value). */
export function cardTheme(read, skin = '') {
  const v = (k, d) => String(read(k) ?? '').trim() || d;
  const px = (k, d) => { const n = parseFloat(v(k, '')); return Number.isFinite(n) ? n : d; };
  return {
    skin,
    panel: v('--panel-solid', '#12233F'),
    ink: v('--ink', '#ECE6D8'),
    accent: v('--accent', '#8CF5A8'),
    edge: v('--edge-strong', '#3E5A86'),
    font: v('--font-body', 'ui-sans-serif, system-ui, sans-serif'),
    weight: skin === 'deep-space' ? 500 : 600,
    // The appearance's control radius, at the atlas's scale (a slot is about twice its size on
    // screen), held under the body's half height: Retro Future is a pill, the others a card.
    radius: Math.min(BODY_H / 2, px('--r-control', 4) * 2.2),
    // Deep Space cuts the top right corner, as its panels do.
    chamfer: Math.min(BODY_H / 2, px('--chamfer', 0)),
  };
}

/** A card's width in the atlas for a fitted name. */
export const cardWidth = (fit) => Math.min(SLOT_W, Math.ceil(PAD_L + LIGHT_D + LIGHT_GAP + fit.width + PAD_R));

/**
 * The card under `ndc` (x, y in -1..1), nearest first: `cards` carry their projected centre
 * (`cx`, `cy`, NDC), half sizes (`hw`, `hh`, NDC) and `depth` (metres). The notch and the clear
 * margins of a slot do not count; only the body does.
 */
export function pickCard(cards, ndc) {
  let best = null;
  for (const c of cards) {
    if (!(c.alpha > 0.3)) continue;
    if (Math.abs(ndc.x - c.cx) > c.hw || Math.abs(ndc.y - c.cy) > c.hh) continue;
    if (!best || c.depth < best.depth) best = c;
  }
  return best;
}

/**
 * Cards that would cover one another on the screen are stacked: nearest first, each card that
 * overlaps one already placed goes up above it (at most `most` steps; a crowd past that may
 * overlap). `rects` carry `cx`, `cy`, `hw`, `hh` (NDC) and `depth`; the result is each card's
 * rise in NDC, in the order given.
 */
export function stackCards(rects, { gap = 0.008, most = 4 } = {}) {
  const order = rects.map((_, i) => i).sort((a, b) => rects[a].depth - rects[b].depth);
  const placed = [], lift = new Array(rects.length).fill(0);
  for (const i of order) {
    const r = rects[i];
    let cy = r.cy;
    for (let k = 0; k < most; k++) {
      // (Just touching is not covering: a card set right above one must not find it again.)
      const p = placed.find((q) => Math.abs(r.cx - q.cx) < r.hw + q.hw + gap - 1e-6 && Math.abs(cy - q.cy) < r.hh + q.hh + gap - 1e-6);
      if (!p) break;
      cy = p.cy + p.hh + r.hh + gap;
    }
    lift[i] = cy - r.cy;
    placed.push({ cx: r.cx, cy, hw: r.hw, hh: r.hh });
  }
  return lift;
}

// ---------------------------------------------------------------------------------------------

const VERT = /* glsl */ `
attribute vec3 aCenter;
attribute vec2 aSize;
attribute vec4 aUv;
attribute float aAlpha;
varying vec2 vUv;
varying float vAlpha;
void main() {
  vec4 mv = viewMatrix * vec4(aCenter, 1.0);
  mv.xy += position.xy * aSize;
  gl_Position = projectionMatrix * mv;
  vUv = vec2(aUv.x + (position.x + 0.5) * aUv.z, aUv.y + (0.5 - position.y) * aUv.w);
  vAlpha = aAlpha;
}`;
const FRAG = /* glsl */ `
uniform sampler2D map;
varying vec2 vUv;
varying float vAlpha;
void main() {
  vec4 c = texture2D(map, vUv);
  float a = c.a * vAlpha;
  if (a < 0.02) discard;
  gl_FragColor = vec4(c.rgb, a);
}`;

function roundRect(ctx, x, y, w, h, r, chamfer) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  if (chamfer > 0) { ctx.lineTo(x + w - chamfer, y); ctx.lineTo(x + w, y + chamfer); }
  else { ctx.lineTo(x + w - r, y); ctx.arcTo(x + w, y, x + w, y + r, r); }
  ctx.lineTo(x + w, y + h - r); ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
  ctx.lineTo(x + r, y + h); ctx.arcTo(x, y + h, x, y + h - r, r);
  ctx.lineTo(x, y + r); ctx.arcTo(x, y, x + r, y, r);
  ctx.closePath();
}

/** Draw one card into `ctx` (a SLOT_W × SLOT_H canvas): its body, edge, light, notch and name. */
export function drawCard(ctx, fit, theme) {
  const w = cardWidth(fit), h = BODY_H, b = BORDER / 2;
  ctx.clearRect(0, 0, SLOT_W, SLOT_H);
  ctx.save();
  // The notch, under the body's middle, pointing down at the person.
  const mid = w / 2;
  ctx.beginPath();
  ctx.moveTo(mid - NOTCH_H, h - 2); ctx.lineTo(mid, h + NOTCH_H - 1); ctx.lineTo(mid + NOTCH_H, h - 2); ctx.closePath();
  ctx.fillStyle = theme.panel; ctx.fill();
  ctx.lineWidth = BORDER; ctx.strokeStyle = theme.edge; ctx.stroke();
  // The body: the appearance's own panel, edge and corner.
  roundRect(ctx, b, b, w - BORDER, h - BORDER, Math.max(0, theme.radius - b), theme.chamfer);
  ctx.globalAlpha = 0.94; ctx.fillStyle = theme.panel; ctx.fill(); ctx.globalAlpha = 1;
  ctx.lineWidth = BORDER; ctx.strokeStyle = theme.edge; ctx.stroke();
  // The notch's join with the body is the panel's, not a line across it.
  ctx.fillStyle = theme.panel; ctx.fillRect(mid - NOTCH_H + 3, h - BORDER - 1, NOTCH_H * 2 - 6, BORDER + 2);
  // The status light: the appearance's accent, as the machine's own lamps are.
  ctx.beginPath(); ctx.arc(PAD_L + LIGHT_D / 2, h / 2, LIGHT_D / 2, 0, Math.PI * 2);
  ctx.fillStyle = theme.accent; ctx.fill();
  // The name.
  ctx.fillStyle = theme.ink;
  ctx.font = `${theme.weight} ${fit.size}px ${theme.font}`;
  ctx.textBaseline = 'middle';
  const lh = fit.size * 1.12, top = h / 2 + 1 - (lh * (fit.lines.length - 1)) / 2;
  fit.lines.forEach((line, i) => ctx.fillText(line, PAD_L + LIGHT_D + LIGHT_GAP, top + i * lh));
  ctx.restore();
  return w;
}

/**
 * The layer. `list()` names the people who may be carded, each `{ key, actor, name, personId,
 * staged }` where `actor` is a HumanActor (its root, body, proxy and head are read); `theme()`
 * returns the appearance in force (cardTheme); `viewHeight()` is the canvas's CSS height.
 */
export function createNameCards({ THREE, renderer, camera, list, theme, viewHeight = () => 780,
  tier = 'full', shown = true, doc = globalThis.document ?? null, now = () => performance.now() / 1000 } = {}) {
  const group = new THREE.Group();
  group.name = 'name-cards';
  let limits = NAME_CARD_TIERS[tier] ?? NAME_CARD_TIERS.full;
  let slotsN = limits.max + SPARE;   // the carded plus a few fading out
  let on = shown !== false;
  let atlas = null, mesh = null, geometry = null, material = null;
  let attrs = null;
  const scratch = doc?.createElement?.('canvas') ?? null;
  if (scratch) { scratch.width = SLOT_W; scratch.height = SLOT_H; }
  const ctx = scratch?.getContext?.('2d', { willReadFrequently: false }) ?? null;
  const scratchTex = scratch ? new THREE.CanvasTexture(scratch) : null;
  if (scratchTex) { scratchTex.flipY = false; scratchTex.premultiplyAlpha = false; }
  const at = new THREE.Vector2();
  const entries = new Map();       // key -> { key, actor, name, personId, staged, slot, w, alpha, want, drawn, theme }
  let free = [];
  let chooseIn = 0, look = null, fontsWaiting = false, disposed = false;
  let picked = [];                 // the drawn cards' screen rects, for pickAt
  const heads = new WeakMap();     // body -> head bone
  const tmp = new THREE.Vector3(), view = new THREE.Vector3(), headV = new THREE.Vector3(), eyeV = new THREE.Vector3();
  const frustum = new THREE.Frustum(), pv = new THREE.Matrix4();
  const counters = { drawn: 0, uploads: 0, chosen: 0 };

  function build() {
    // Two columns of slots. No pixels are sent for the atlas itself: only its slots, one by one.
    atlas = new THREE.DataTexture(null, ATLAS_W, Math.ceil(slotsN / 2) * SLOT_H, THREE.RGBAFormat, THREE.UnsignedByteType);
    atlas.source.dataReady = false;
    atlas.generateMipmaps = false;
    atlas.minFilter = THREE.LinearFilter; atlas.magFilter = THREE.LinearFilter;
    atlas.flipY = false; atlas.premultiplyAlpha = false;
    atlas.needsUpdate = true;
    const quad = new THREE.PlaneGeometry(1, 1);
    geometry = new THREE.InstancedBufferGeometry();
    geometry.index = quad.index;
    geometry.setAttribute('position', quad.getAttribute('position'));
    const make = (n) => { const a = new THREE.InstancedBufferAttribute(new Float32Array(slotsN * n), n); a.setUsage(THREE.DynamicDrawUsage); return a; };
    attrs = { center: make(3), size: make(2), uv: make(4), alpha: make(1) };
    geometry.setAttribute('aCenter', attrs.center);
    geometry.setAttribute('aSize', attrs.size);
    geometry.setAttribute('aUv', attrs.uv);
    geometry.setAttribute('aAlpha', attrs.alpha);
    geometry.instanceCount = 0;
    material = new THREE.ShaderMaterial({
      uniforms: { map: { value: atlas } }, vertexShader: VERT, fragmentShader: FRAG,
      transparent: true, depthTest: true, depthWrite: false, toneMapped: false, fog: false,
    });
    mesh = new THREE.Mesh(geometry, material);
    mesh.name = 'name-cards';
    mesh.frustumCulled = false;
    mesh.renderOrder = 10;
    mesh.visible = on;
    group.add(mesh);
    free = Array.from({ length: slotsN }, (_, i) => slotsN - 1 - i);
  }
  function teardown() {
    mesh?.removeFromParent(); geometry?.dispose(); material?.dispose(); atlas?.dispose();
    mesh = geometry = material = atlas = attrs = null;
    entries.clear(); free = []; picked = [];
  }
  build();

  const slotXY = (slot) => [(slot % 2) * SLOT_W, Math.floor(slot / 2) * SLOT_H];

  function measure(text, size, t) {
    ctx.font = `${t.weight} ${size}px ${t.font}`;
    return ctx.measureText(text).width;
  }

  /** Draw an entry's slot and copy it into the atlas. */
  function draw(e, t) {
    if (!ctx || !renderer?.copyTextureToTexture) return false;
    // A web font not loaded yet is asked for; the cards are drawn again when it comes.
    const font = `${t.weight} ${NAME_SIZES[0]}px ${t.font}`;
    if (doc?.fonts?.check && !doc.fonts.check(font, e.name) && !fontsWaiting) {
      fontsWaiting = true;
      Promise.resolve(doc.fonts.load(font, e.name)).catch(() => {}).then(() => { fontsWaiting = false; refresh(); });
    }
    const fit = fitName(e.name, (s, z) => measure(s, z, t));
    e.w = drawCard(ctx, fit, t);
    e.fit = fit;
    const [x, y] = slotXY(e.slot);
    scratchTex.needsUpdate = true;
    renderer.copyTextureToTexture(scratchTex, atlas, null, at.set(x, y));
    e.drawn = t;
    counters.uploads++;
    return true;
  }

  function headOf(actor) {
    const body = actor.body;
    if (!body?.scene) return null;
    let bone = heads.get(body);
    if (bone === undefined) {
      bone = body.scene.getObjectByName?.('head') ?? null;
      heads.set(body, bone);
    }
    if (bone) { bone.getWorldPosition(headV); return headV.setY(headV.y + 0.16); }
    return actor.proxy ? actor.proxy.localToWorld(headV.set(0, 1.0, 0)) : actor.root.getWorldPosition(headV).setY(headV.y + 1.75);
  }

  function drawnInTree(actor) {
    if (!actor || actor.disposed || actor.indoors || !actor.body || !actor.root?.parent) return false;
    for (let node = actor.root; node; node = node.parent) if (!node.visible) return false;
    return true;
  }

  function choose() {
    const eye = camera.getWorldPosition(view);
    pv.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    frustum.setFromProjectionMatrix(pv);
    const cands = [];
    for (const p of list() ?? []) {
      const a = p.actor;
      if (!p.name || !a?.root) continue;
      const m = a.root.matrixWorld.elements;
      const d = Math.hypot(m[12] - eye.x, m[13] - eye.y, m[14] - eye.z);
      if (!(d <= limits.reach)) continue;
      if (!drawnInTree(a)) continue;
      tmp.set(m[12], m[13] + 1.2, m[14]);
      cands.push({ ...p, distance: d, inView: frustum.containsPoint(tmp) || d < 3 });
    }
    const chosen = chooseCards(cands, limits);
    counters.chosen = chosen.length;
    const keep = new Set(chosen.map((c) => c.key));
    for (const e of entries.values()) if (!keep.has(e.key)) e.want = 0;
    for (const c of chosen) {
      let e = entries.get(c.key);
      if (e && (e.actor !== c.actor || e.name !== c.name)) { e.actor = c.actor; if (e.name !== c.name) { e.name = c.name; e.drawn = null; } }
      if (!e) {
        if (!free.length) {
          // The faintest card going out gives its slot up.
          let worst = null;
          for (const x of entries.values()) if (!x.want && (!worst || x.alpha < worst.alpha)) worst = x;
          if (!worst) continue;
          entries.delete(worst.key); free.push(worst.slot);
        }
        e = { key: c.key, actor: c.actor, name: c.name, personId: c.personId ?? null, staged: !!c.staged,
          slot: free.pop(), w: 0, alpha: 0, want: 1, drawn: null, phase: (entries.size * 0.37) % 1 };
        entries.set(c.key, e);
      }
      e.want = 1;
      e.personId = c.personId ?? e.personId;
      e.staged = !!c.staged;
    }
  }

  function refresh() {
    look = null;
    for (const e of entries.values()) e.drawn = null;
  }

  function update(dt) {
    if (disposed || !mesh) return;
    if (!on) { mesh.visible = false; geometry.instanceCount = 0; picked = []; return; }
    mesh.visible = true;
    const step = Number.isFinite(dt) && dt > 0 ? Math.min(dt, 0.25) : 0;
    chooseIn -= step;
    if (chooseIn <= 0 || !entries.size) { chooseIn = CHOOSE_S; choose(); }
    const t = look ?? (look = theme());
    let draws = 0;
    const eye = camera.getWorldPosition(eyeV);
    const fov = (camera.fov ?? 72) * Math.PI / 180;
    const tanHalf = Math.tan(fov / 2);
    const vh = Math.max(200, viewHeight() || 780);
    const aspect = camera.aspect || 1;
    const clock = now();
    camera.updateMatrixWorld?.();
    const rows = [];
    for (const e of entries.values()) {
      if (!drawnInTree(e.actor)) e.want = 0;
      if (e.want) e.alpha = Math.min(1, e.alpha + step / FADE_S);
      else e.alpha = Math.max(0, e.alpha - step / FADE_S);
      if (!e.want && e.alpha <= 0) { entries.delete(e.key); free.push(e.slot); continue; }
      if (e.drawn !== t) {
        if (draws >= DRAWS_PER_FRAME) continue;
        if (!draw(e, t)) continue;
        draws++;
      }
      if (!drawnInTree(e.actor)) continue;
      const head = headOf(e.actor);
      if (!head) continue;
      const d = head.distanceTo(eye);
      const alpha = e.alpha * reachAlpha(d, limits.reach);
      if (alpha <= 0.01) continue;
      // Its depth in the view, for the size that keeps CARD_PX on the screen.
      tmp.copy(head).applyMatrix4(camera.matrixWorldInverse);
      const depth = Math.max(0.3, -tmp.z);
      const hSlot = cardPx(d, limits.reach) * (2 * depth * tanHalf) / vh;
      const wCard = hSlot * (e.w / SLOT_H);
      const bob = 0.012 * Math.sin((clock * 1.4 + e.phase) * Math.PI * 2);
      const cy = head.y + LIFT_M + hSlot / 2 + bob;
      // Its body on the screen: for the stacking, and for a click or a tap.
      const bodyH = hSlot * (BODY_H / SLOT_H);
      tmp.set(head.x, cy + hSlot / 2 - bodyH / 2, head.z).applyMatrix4(camera.matrixWorldInverse);
      const z = Math.max(0.3, -tmp.z);
      tmp.applyMatrix4(camera.projectionMatrix);
      rows.push({ e, x: head.x, y: cy, z: head.z, wCard, hSlot, alpha, d,
        cx: tmp.x, cy: tmp.y, hw: (wCard / 2) / (z * tanHalf * aspect), hh: (bodyH / 2) / (z * tanHalf), depth: z });
    }
    // Cards that would cover one another stack, nearest lowest; each eases to its place.
    const lift = stackCards(rows);
    let n = 0;
    picked = [];
    rows.forEach((r, i) => {
      const e = r.e, want = lift[i] * r.depth * tanHalf;
      e.lift = e.lift == null || !step ? want : e.lift + (want - e.lift) * Math.min(1, step * 8);
      attrs.center.setXYZ(n, r.x, r.y + e.lift, r.z);
      attrs.size.setXY(n, r.wCard, r.hSlot);
      const [x, y] = slotXY(e.slot);
      attrs.uv.setXYZW(n, x / ATLAS_W, y / atlas.image.height, e.w / ATLAS_W, SLOT_H / atlas.image.height);
      attrs.alpha.setX(n, r.alpha);
      n++;
      picked.push({ key: e.key, personId: e.personId, name: e.name, staged: e.staged, actor: e.actor, alpha: r.alpha,
        cx: r.cx, cy: r.cy + e.lift / (r.depth * tanHalf), hw: r.hw, hh: r.hh, depth: r.depth, distance: r.d });
    });
    geometry.instanceCount = n;
    if (n) for (const a of Object.values(attrs)) a.needsUpdate = true;
    counters.drawn = n;
  }

  return {
    group,
    get shown() { return on; },
    setShown(next) { on = next !== false; if (mesh) mesh.visible = on; if (!on) { for (const e of entries.values()) e.alpha = 0; } return on; },
    setTier(next) {
      const l = NAME_CARD_TIERS[next];
      if (!l || l === limits) return false;
      limits = l;
      if (l.max + SPARE !== slotsN) { teardown(); slotsN = l.max + SPARE; build(); }
      chooseIn = 0;
      return true;
    },
    /** The appearance or the fonts changed: every card is drawn again. */
    refresh,
    update,
    /** The card under `ndc` (the crosshair when null): { personId, name, staged, actor, distance }. */
    pickAt(ndc = null) {
      if (!on || !picked.length) return null;
      return pickCard(picked, ndc ?? { x: 0, y: 0 });
    },
    snapshot() {
      return { shown: on, tier: Object.keys(NAME_CARD_TIERS).find((k) => NAME_CARD_TIERS[k] === limits), slots: slotsN,
        atlas: atlas ? [atlas.image.width, atlas.image.height] : null, ...counters,
        cards: picked.map((c) => ({ name: c.name, personId: c.personId, distance: +c.distance.toFixed(1),
          ndc: [+c.cx.toFixed(3), +c.cy.toFixed(3)], cut: entries.get(c.key)?.fit?.cut ?? false,
          size: entries.get(c.key)?.fit?.size ?? null })) };
    },
    dispose() { disposed = true; teardown(); scratchTex?.dispose(); group.removeFromParent(); },
  };
}
