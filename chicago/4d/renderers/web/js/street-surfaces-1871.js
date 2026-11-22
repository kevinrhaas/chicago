/**
 * street-surfaces-1871.js — what the 1871 streets are made of, close up (T-3685).
 *
 * The context city's streets.glb carries one material per surface, named by the
 * generator (generators/city_1871_emit.py `surface_plan`): `1871_woodblock`
 * (Nicholson end-grain block, where the Board of Public Works' 1871 report puts it
 * and on the principal thoroughfares up to its mileage), `1871_setts` (the boulder
 * pavement of the river streets), `1871_dirt` (every other street) and `1871_plank`
 * (the raised walks and the crossings). Their UVs run along the street (u) and
 * across it from the centreline (v), in half-metres, so ruts, block courses and
 * boards follow the street rather than the map grid.
 *
 * Each surface gets a small painted tile, colour plus a height for relief, drawn
 * once per page from a seeded generator: brown-grey wood blocks in courses across
 * the street with tar joints; packed earth with wheel ruts and hoof-worn centre;
 * rounded grey boulders; weathered boards laid across the walk. Mipmapping does the
 * distance: within a few metres the tile reads as the surface itself, and past
 * about 150 m it averages to the surface's own tone, which is the cheap far surface.
 * A phone (detail `light`) paints the same tiles at half the resolution.
 *
 * The walks' kerb boards and end risers, and a step at each end of a plank
 * crossing, are built here from `walk_surfaces` (the floors the walker already
 * stands on), so they cost the published files nothing. `light` keeps the kerb
 * along the street and the steps, and leaves out the lot-side boards and the
 * end risers.
 *
 * The tones are reconstructions (L-1871-street-surfaces), read against period
 * photographs of Lake and La Salle streets (late 1860s) and the Court House cupola
 * views (about 1858), not copied from them.
 */
import * as THREE from 'three';

function rng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6D2B79F5) >>> 0; let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rgb = (r, g, b, k = 1) => `rgb(${Math.round(r * k)},${Math.round(g * k)},${Math.round(b * k)})`;
const grey = v => { const g = Math.max(0, Math.min(255, Math.round(v))); return `rgb(${g},${g},${g})`; };

/**
 * The order the street layers draw in, as ground decals (Kevin, 2026-11-21: "any
 * intersections of sidewalks or streets is flashy and blinks when you cross it").
 * Where two streets meet, their roadway ribbons lie one on the other at the same
 * height, and so do two walks at a corner; drawn with depth writes, the two faces
 * fought for every pixel and the junction blinked as the eye moved. As 1904's
 * roadways do (street-grid.js ROAD_RENDER_ORDER, T-3389), they now draw after every
 * opaque thing at order 0 without writing depth: overlapping faces of one layer
 * resolve by draw order, the same every frame, and each layer lies over the one
 * below — roadways (dirt, then boulders, then wood block), the plank crossings,
 * then the raised walks. Keep anything opaque that lies under the streets below 10.
 */
export const STREET_DECAL_ORDER = Object.freeze({ streets: 10, crossings: 10.2, walks: 10.3 });
const ROADWAY_RANK = Object.freeze({ dirt: 0, setts: 0.01, woodblock: 0.02 });

/** Metres one tile covers (square), its roughness and relief. */
export const SURFACES = Object.freeze({
  woodblock: { metres: 2, roughness: 0.92, bump: 0.035 },
  dirt: { metres: 16, roughness: 1, bump: 0.05 },
  setts: { metres: 2, roughness: 0.9, bump: 0.06 },
  plank: { metres: 2.4, roughness: 0.94, bump: 0.025 },
  kerb: { metres: 2, roughness: 0.95, bump: 0.02 },
});

/** Paint one surface: { color, height } canvases of px × px, covering SURFACES[kind].metres. */
export function paintSurface(kind, px = 512, doc = globalThis.document) {
  const color = doc.createElement('canvas'), height = doc.createElement('canvas');
  color.width = color.height = height.width = height.height = px;
  const c = color.getContext('2d'), h = height.getContext('2d');
  const R = rng(kind.length * 7919 + kind.charCodeAt(0) * 31);
  const s = px / SURFACES[kind].metres; // pixels per metre
  const blots = (ctx, n, size, tone, alpha) => {
    for (let i = 0; i < n; i++) {
      const x = R() * px, y = R() * px, r = size * (0.4 + R());
      ctx.fillStyle = typeof tone === 'function' ? tone() : tone; ctx.globalAlpha = alpha * (0.4 + R() * 0.6);
      ctx.beginPath(); ctx.ellipse(x, y, r, r * (0.5 + R()), R() * Math.PI, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
  };
  h.fillStyle = grey(128); h.fillRect(0, 0, px, px);
  // Every mark that crosses an edge is drawn again on the far side, so the tile repeats without a seam.
  const wrapped = (x, y, r, draw) => {
    for (const dx of [0, -px, px]) for (const dy of [0, -px, px]) {
      if (x + dx + r < 0 || x + dx - r > px || y + dy + r < 0 || y + dy - r > px) continue;
      draw(x + dx, y + dy);
    }
  };
  const blotsWrapped = (ctx, n, size, tone, alpha, stretch = 1) => {
    for (let i = 0; i < n; i++) {
      const x = R() * px, y = R() * px, r = size * (0.4 + R()), t = typeof tone === 'function' ? tone() : tone;
      const a = alpha * (0.4 + R() * 0.6), ry = r * (0.5 + R() * 0.5) / stretch, rot = (R() - 0.5) * 0.4;
      wrapped(x, y, r, (X, Y) => { ctx.fillStyle = t; ctx.globalAlpha = a; ctx.beginPath(); ctx.ellipse(X, Y, r, ry, rot, 0, Math.PI * 2); ctx.fill(); });
    }
    ctx.globalAlpha = 1;
  };
  if (kind === 'woodblock') {
    // Courses of end-grain blocks laid across the street (x runs along it), tar and grit
    // between; worn brown-grey tops, a few darker where wet or oiled.
    c.fillStyle = rgb(44, 36, 28); c.fillRect(0, 0, px, px);
    h.fillStyle = grey(40); h.fillRect(0, 0, px, px);
    const courses = Math.round(SURFACES[kind].metres / 0.16), course = px / courses;
    for (let k = 0; k < courses; k++) {
      const x = k * course, lens = [];
      let total = 0;
      while (total < px) { const l = (0.13 + R() * 0.12) * s; lens.push(l); total += l; }
      const scale = px / total; let y = R() * 0.1 * s; // blocks fill the course exactly, then wrap
      for (const l0 of lens) {
        const l = l0 * scale, tone = 0.72 + R() * 0.4, warm = R() * 10;
        for (const Y of [y, y - px]) {
          c.fillStyle = rgb(120 + warm, 98 + warm * 0.6, 72, tone); c.fillRect(x + 1.5, Y + 1.5, course - 3, l - 3);
          h.fillStyle = grey(150 + R() * 60); h.fillRect(x + 2, Y + 2, course - 4, l - 4);
        }
        c.strokeStyle = rgb(72, 58, 44, tone); c.globalAlpha = 0.3; c.lineWidth = Math.max(1, px / 512);
        for (let r = 0; r < 2; r++) { // growth rings on the end grain
          const cx = x + course * (0.2 + R() * 0.6), cy = (y + l * (0.2 + R() * 0.6)) % px;
          c.beginPath(); c.arc(cx, cy, (0.02 + R() * 0.04) * s, 0, Math.PI * 2); c.stroke();
        }
        c.globalAlpha = 1;
        y += l;
      }
    }
    blotsWrapped(c, 500, 0.04 * s, rgb(150, 134, 108), 0.16); // dust and grit, worn tops
    blotsWrapped(c, 30, 0.3 * s, rgb(40, 32, 24), 0.12, 2);   // damp and oil stains
  } else if (kind === 'dirt') {
    // Packed earth; across (y) the tile spans 16 m centred on the street's line.
    c.fillStyle = rgb(118, 98, 70); c.fillRect(0, 0, px, px);
    blotsWrapped(c, 5000, 0.05 * s, () => rgb(124 + R() * 30, 104 + R() * 24, 74 + R() * 18), 0.3);
    blotsWrapped(c, 40, 1.2 * s, rgb(92, 76, 54), 0.1, 3);  // damp ground and dried puddles, long with the street
    blotsWrapped(c, 400, 0.12 * s, rgb(78, 64, 46), 0.12, 1.5); // hoof marks and droppings, mostly mid-lane
    const mid = px / 2;
    for (const lane of [-4.6, -2.6, -0.95, 0.95, 2.6, 4.6]) { // wheel ruts, about 1.65 m gauge a lane
      const y0 = mid + lane * s, phase = R() * Math.PI * 2;
      for (let x = 0; x < px; x += 2) {
        const wob = Math.sin((x / px) * Math.PI * 4 + phase) * 0.06 * s; // two whole waves: seamless along
        c.globalAlpha = 0.45; c.fillStyle = rgb(80, 64, 46); c.fillRect(x, y0 + wob - 0.07 * s, 2, 0.14 * s);
        c.globalAlpha = 0.25; c.fillStyle = rgb(146, 126, 96); c.fillRect(x, y0 + wob + 0.08 * s, 2, 0.06 * s); // the rut's lip
        h.fillStyle = grey(70); h.fillRect(x, y0 + wob - 0.08 * s, 2, 0.16 * s);
      }
      c.globalAlpha = 1;
    }
    blotsWrapped(h, 1600, 0.06 * s, () => grey(100 + R() * 70), 0.5);
  } else if (kind === 'setts') {
    // Rounded boulders set close in sand: irregular, mostly grey and buff, the joints
    // filled with dirt rather than open.
    c.fillStyle = rgb(92, 80, 62); c.fillRect(0, 0, px, px);
    h.fillStyle = grey(60); h.fillRect(0, 0, px, px);
    const n = Math.round(SURFACES[kind].metres / 0.17), step = px / n;
    for (let row = 0; row < n; row++) {
      for (let col = 0; col < n; col++) {
        const x = (col + (row % 2) * 0.5 + (R() - 0.5) * 0.25) * step, y = (row + (R() - 0.5) * 0.25) * step;
        const r = step * (0.44 + R() * 0.1), k = 0.7 + R() * 0.45, buff = R() < 0.35 ? 14 : 0;
        const rx = r * (0.85 + R() * 0.2), ry = r * (0.8 + R() * 0.2), rot = R() * Math.PI;
        wrapped(x, y, r * 1.2, (X, Y) => {
          c.fillStyle = rgb(118 + buff, 112 + buff * 0.7, 102, k); c.beginPath(); c.ellipse(X, Y, rx, ry, rot, 0, Math.PI * 2); c.fill();
          c.fillStyle = rgb(150 + buff, 144 + buff * 0.7, 132, k); c.globalAlpha = 0.35; // the worn top
          c.beginPath(); c.ellipse(X - rx * 0.15, Y - ry * 0.15, rx * 0.55, ry * 0.5, rot, 0, Math.PI * 2); c.fill(); c.globalAlpha = 1;
          const g = h.createRadialGradient(X, Y, 0, X, Y, r);
          g.addColorStop(0, grey(220)); g.addColorStop(0.7, grey(170)); g.addColorStop(1, grey(70));
          h.fillStyle = g; h.beginPath(); h.ellipse(X, Y, rx, ry, rot, 0, Math.PI * 2); h.fill();
        });
      }
    }
    blotsWrapped(c, 300, 0.05 * s, rgb(96, 82, 62), 0.25); // sand and dirt over the stones
  } else if (kind === 'plank') {
    // Boards laid across the walk: their long side runs across (y), joints along (x).
    const board = 0.24 * s;
    for (let x = 0; x < px; x += board) {
      const k = 0.78 + R() * 0.35;
      c.fillStyle = rgb(132, 110, 82, k); c.fillRect(x, 0, board, px);
      c.strokeStyle = rgb(88, 74, 58, k); c.globalAlpha = 0.25; c.lineWidth = 1;
      for (let g = 0; g < 7; g++) {
        const gx = x + R() * board;
        c.beginPath(); c.moveTo(gx, 0); c.bezierCurveTo(gx + 2, px / 3, gx - 2, px * 2 / 3, gx + 1, px); c.stroke();
      }
      c.globalAlpha = 1;
      c.fillStyle = rgb(40, 33, 26); c.fillRect(x, 0, Math.max(1, px / 340), px); // the gap between boards
      h.fillStyle = grey(40); h.fillRect(x, 0, Math.max(1, px / 300), px);
      c.fillStyle = rgb(50, 44, 38);
      for (const ny of [0.15, 0.85]) { c.fillRect(x + board * 0.3, px * ny, 2, 2); c.fillRect(x + board * 0.7, px * ny, 2, 2); }
    }
    blots(c, 300, 0.05 * s, rgb(96, 84, 66), 0.2);
  } else { // kerb: a weathered edge board, its grain along (x)
    c.fillStyle = rgb(92, 76, 56); c.fillRect(0, 0, px, px);
    c.strokeStyle = rgb(64, 52, 38); c.globalAlpha = 0.3; c.lineWidth = 1;
    for (let g = 0; g < 40; g++) { const gy = R() * px; c.beginPath(); c.moveTo(0, gy); c.bezierCurveTo(px / 3, gy + 3, px * 2 / 3, gy - 3, px, gy); c.stroke(); }
    c.globalAlpha = 1;
    blots(c, 200, 0.05 * s, rgb(60, 48, 34), 0.3);
  }
  return { color, height };
}

/** The painted tile for one surface, as map + bump textures (cached per call site). */
function tileTextures(kind, px, anisotropy, made, textures) {
  if (made.has(kind)) return made.get(kind);
  const { color, height } = paintSurface(kind, px);
  const map = new THREE.CanvasTexture(color), bump = new THREE.CanvasTexture(height);
  const repeat = 2 / SURFACES[kind].metres; // UVs are in half-metres
  for (const t of [map, bump]) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = anisotropy;
    t.repeat.set(repeat, repeat);
    // across-street v is centred on the line: the dirt tile's ruts sit either side of it
    if (kind === 'dirt') t.offset.set(0, 0.5);
  }
  map.colorSpace = THREE.SRGBColorSpace;
  textures.push(map, bump);
  made.set(kind, { map, bump });
  return made.get(kind);
}

function dress(material, kind, tile) {
  material.map = tile.map; material.bumpMap = tile.bump; material.bumpScale = SURFACES[kind].bump;
  material.color?.setRGB(1, 1, 1);
  if ('roughness' in material) material.roughness = SURFACES[kind].roughness;
  material.needsUpdate = true;
}

/**
 * Dress the context city's street materials in place and build the walks' edges.
 * Returns { textures, materials, meshes, census } for the caller to own and dispose.
 */
export function dressStreetSurfaces(meshes, { walkSurfaces = [], heights = {}, detail = 'full',
  anisotropy = 4, confidence = null } = {}) {
  const made = new Map(), textures = [], materials = [], out = [];
  const px = detail === 'light' ? 256 : 512;
  const dressed = new Set();
  let decals = 0;
  for (const mesh of meshes) {
    const material = mesh.material, kind = String(material?.name ?? '').replace(/^1871_/, '');
    if (!SURFACES[kind]) continue;
    const layers = mesh.userData?.layers ?? [];
    if (layers.length && layers.every(l => STREET_DECAL_ORDER[l] != null)) {
      // one layer a batch (city-context.js splits them); a roadway ranks by its surface
      mesh.renderOrder = Math.max(...layers.map(l => STREET_DECAL_ORDER[l])) + (layers.includes('streets') ? (ROADWAY_RANK[kind] ?? 0) : 0);
      material.depthWrite = false;
      decals++;
    }
    if (dressed.has(material)) continue;
    dress(material, kind, tileTextures(kind, px, anisotropy, made, textures));
    dressed.add(material);
  }
  const geometry = walkEdgeGeometry(walkSurfaces, { road: heights.road, ground: heights.ground,
    walk: heights.walk, light: detail === 'light' });
  let quads = 0;
  if (geometry) {
    const material = new THREE.MeshStandardMaterial({ name: '1871_kerb' });
    dress(material, 'kerb', tileTextures('kerb', px, anisotropy, made, textures));
    confidence?.patch?.(material);
    materials.push(material);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = 'context:1871:infrastructure:walk_edges:1871_kerb';
    mesh.receiveShadow = true;
    quads = geometry.getAttribute('position').count / 4;
    mesh.userData = { layer: 'infrastructure', layers: ['walk_edges'], confidence: 'reconstructed',
      liberty: 'L-1871-street-surfaces', triangles: quads * 2 };
    out.push(mesh);
  }
  return { textures, materials, meshes: out, census: { detail, dressed: dressed.size, decals, edgeQuads: quads, tilePx: px } };
}

/**
 * The vertical faces of the raised walks and the steps at the crossings, from the
 * floor ribbons: a kerb board along each walk's street side (from the roadway up to
 * the walk), and — above `light` — its lot-side board (from the ground) and its end
 * risers; and at each end of a plank crossing, a step half way between the two.
 */
export function walkEdgeGeometry(surfaces, { road = 3.23, ground = 3.2, walk = 3.38, light = false } = {}) {
  const pos = [], nrm = [], uv = [];
  const quad = (a, b, y0, y1, along = 0) => { // a vertical face from a to b, facing its right-hand side
    const de = b[0] - a[0], dn = b[1] - a[1], L = Math.hypot(de, dn);
    if (L < 0.01 || y1 - y0 < 0.005) return;
    const nx = dn / L, nz = de / L; // right of a→b in map e/n is (dn, -de); glTF z = -n
    for (const [p, y] of [[a, y0], [b, y0], [b, y1], [a, y1]]) { pos.push(p[0], y, -p[1]); nrm.push(nx, 0, nz); }
    uv.push(along / 2, y0 / 2, (along + L) / 2, y0 / 2, (along + L) / 2, y1 / 2, along / 2, y1 / 2);
  };
  const flat = (a, b, width, y) => { // a horizontal tread from a to b, facing up
    const de = b[0] - a[0], dn = b[1] - a[1], L = Math.hypot(de, dn);
    if (L < 0.01) return;
    const ox = -dn / L * width / 2, on = de / L * width / 2;
    for (const p of [[a[0] + ox, a[1] + on], [a[0] - ox, a[1] - on], [b[0] - ox, b[1] - on], [b[0] + ox, b[1] + on]]) {
      pos.push(p[0], y, -p[1]); nrm.push(0, 1, 0);
    }
    uv.push(0, -width / 4, 0, width / 4, L / 2, width / 4, L / 2, -width / 4);
  };
  for (const w of surfaces) {
    if (w.kind !== 'walk' && w.kind !== 'crossing') continue;
    const [a, b] = [w.a, w.b], de = b[0] - a[0], dn = b[1] - a[1], L = Math.hypot(de, dn);
    if (!(L > 0.01)) continue;
    const ue = de / L, un = dn / L, half = w.width_m / 2;
    const side = (p, o) => [p[0] - un * o, p[1] + ue * o]; // o > 0: left of a→b
    if (w.kind === 'walk') {
      const la = side(a, half), lb = side(b, half), ra = side(a, -half), rb = side(b, -half);
      // Which edge faces the street: the walk's id ends `_walk_<side>`, the
      // generator's side of the centreline (-1 right, 1 left of the street's run,
      // which runs the same way as the walk).
      const s = /_walk_(-?1)(?:_\d+)?$/.exec(w.id ?? '')?.[1];
      const streetLeft = s === '-1'; // a right-hand walk has the street on its left
      // Kerb toward the street, from the roadway; lot side from the ground.
      if (streetLeft) quad(lb, la, road - 0.02, w.y); else quad(ra, rb, road - 0.02, w.y);
      if (!light) {
        if (streetLeft) quad(ra, rb, ground - 0.02, w.y); else quad(lb, la, ground - 0.02, w.y);
        quad(la, ra, road - 0.02, w.y); quad(rb, lb, road - 0.02, w.y); // end risers
      }
    } else {
      // A step at each end, 0.35 m out from the walk and half way down.
      const yStep = (w.y + walk) / 2;
      const d = Math.min(0.35, L / 4);
      for (const [p, dir] of [[a, 1], [b, -1]]) {
        const q = [p[0] + ue * d * dir, p[1] + un * d * dir];
        flat(p, q, w.width_m, yStep);
        const l = side(q, half), r = side(q, -half);
        if (dir > 0) quad(r, l, w.y - 0.01, yStep); else quad(l, r, w.y - 0.01, yStep);
      }
    }
  }
  if (!pos.length) return null;
  const count = pos.length / 3, index = new Uint32Array(count / 4 * 6);
  for (let q = 0, k = 0; q < count; q += 4) index.set([q, q + 1, q + 2, q, q + 2, q + 3], k), k += 6;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(count).fill(1), 1));
  g.setIndex(new THREE.BufferAttribute(index, 1));
  g.computeBoundingBox(); g.computeBoundingSphere();
  return g;
}
