#!/usr/bin/env node
/**
 * T-3488 — the 1904 back yards lie on the ground as paving does, in few draws, step from
 * the ground to their doors' sills, survive their maps not arriving, take the Season, and say
 * on a card what they are.
 *
 * Headless, on tools/fixtures/back_yards_test.json (two lots in data/back_yards/<scene>.json's
 * format) over a made-up sloping, rippled field with a 2.5 m lattice, no browser:
 *
 *   drape     every surface vertex stands exactly lift_m over the field where it is; every
 *             triangle lies inside one lattice cell (so none bridges a cell and floats or
 *             sinks); the triangles cover each polygon's area exactly, concave ones too;
 *   decal     every surface material writes no depth, carries a polygon offset with no slope
 *             term, and every surface mesh draws after the terrain's water plane and before
 *             the roadways (renderOrder strictly between terrain.js's water order and
 *             street-grid.js's ROAD_RENDER_ORDER, both read from their sources); a lot's higher
 *             `order` draws later; the decals cast no shadow;
 *   merged    one mesh per (material, order, chunk) and nothing else, materials shared across
 *             chunks, the fixtures one mesh per chunk, the clothes lines one draw: the layer's
 *             draw count stays inside that bound;
 *   steps     stoopPlan rises from the ground at the foot to the sill in risers of 0.15-0.21 m
 *             on 0.28 m treads, takes a rail only past 0.6 m; each door's stoop in the fixtures
 *             mesh reaches from under the ground at its foot to its sill, and a leaf to its head;
 *             the sill stands sill_m over the structure's own bed (bedOf), not the ground;
 *   fallback  the yard maps do not arrive here (no image loader, no files): each such material
 *             is a flat tone and a recorded problem, never a throw; a map another layer already
 *             holds (sharedMaps) is bound and not loaded again; a missing file records a problem
 *             and draws nothing;
 *   season    every surface and fixture material carries season.js's snow; winter's crop plan
 *             has no annual crop and setSeason('winter') replants it so; summer is the file's;
 *   card      a pick on a surface, a door and a post opens a card naming the lot's addresses,
 *             the kind, the material, the grade, the note and the liberty; `_confidence` is each
 *             item's own grade;
 *   plants    the back lots' shrubs grow through front-yards.js with their own `<parcel>.back`
 *             card ids and back-yard words, and front-yards.js with no `back` is unchanged;
 *   passages  (T-3554) each house's back door with a leaf and a stoop is a passage: its leaf is
 *             lifted out of the fixtures onto a hinge and swings out over the landing, the
 *             doorway dark behind it, and its way climbs from the ground beyond the stoop's foot
 *             up every tread, a riser at a time, to the landing and over the sill.
 *
 *   node tools/test_back_yards.mjs
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);

// A canvas that paints nothing, so gardens.js's crop atlas can be made without a browser.
globalThis.OffscreenCanvas ??= class {
  constructor(w, h) { this.width = w; this.height = h; }
  getContext() {
    const W = this.width; const H = this.height;
    const noop = () => {};
    return new Proxy({}, {
      get(_, k) {
        if (k === 'getImageData') return (x, y, w, h) => ({ data: new Uint8ClampedArray((w ?? W) * (h ?? H) * 4) });
        if (k === 'createLinearGradient' || k === 'createRadialGradient') return () => ({ addColorStop: noop });
        return noop;
      },
      set() { return true; },
    });
  }
};

const THREE = await import('three');
const by = await import('../renderers/web/js/back-yards.js');
const { createBackYards, drapeTriangles, stoopPlan, cropPlan, uvAt, BACK_YARD_RENDER_ORDER, CHUNK_M, RISE_M, TREAD_M, RAIL_RISE_M } = by;
const { applySeasonLook, seasonUniforms } = await import('../renderers/web/js/season.js');
const { seasonLook } = await import('../renderers/web/js/gardens.js');

const read = (rel) => fs.readFileSync(new URL(rel, import.meta.url), 'utf8');
const WATER_ORDER = Number(/water\.renderOrder = (\d+(?:\.\d+)?);/.exec(read('../renderers/web/js/terrain.js'))?.[1]);
const ROAD_ORDER = Number(/const ROAD_RENDER_ORDER = (\d+(?:\.\d+)?);/.exec(read('../renderers/web/js/street-grid.js'))?.[1]);
assert.ok(Number.isFinite(WATER_ORDER) && Number.isFinite(ROAD_ORDER), 'DRIFT: terrain.js water order or street-grid.js ROAD_RENDER_ORDER no longer read');

let checks = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); checks += 1; };
const near = (a, b, eps, msg) => ok(Math.abs(a - b) <= eps, `${msg} (${a} vs ${b})`);

const FIXTURE = JSON.parse(read('./fixtures/back_yards_test.json'));
const CELL = 2.5;
const terrain = {
  surfaceHeight: (e, n) => 2 + 0.015 * e - 0.01 * n + 0.12 * Math.sin(e * 0.37) * Math.cos(n * 0.29),
  grid: { cellM: CELL, originE: -1.25, originN: 0.5 },
};
const BEDS = { test_house_101: 2.6, test_house_105: 2.3 };
const bedOf = (id) => BEDS[id] ?? null;

// fetch: material.json and maps 404 here; the fixture is handed in as `doc`
const realFetch = globalThis.fetch;
globalThis.fetch = async (url) => ({ ok: false, status: 404, statusText: 'Not Found', json: async () => ({}), url: String(url) });

/* ---- the pure parts --------------------------------------------------------------- */
{
  // a concave L, cut on the lattice: area kept, every triangle in one cell
  const L = [[0, 0], [10, 0], [10, 3], [3, 3], [3, 9], [0, 9]];
  const tris = drapeTriangles(L, terrain.grid);
  const area = (t) => Math.abs((t[1][0] - t[0][0]) * (t[2][1] - t[0][1]) - (t[2][0] - t[0][0]) * (t[1][1] - t[0][1])) / 2;
  near(tris.reduce((s, t) => s + area(t), 0), 10 * 3 + 3 * 6, 1e-6, 'the draped L covers its own area');
  for (const t of tris) {
    const ci = Math.floor(((t[0][0] + t[1][0] + t[2][0]) / 3 - terrain.grid.originE) / CELL);
    const cj = Math.floor(((t[0][1] + t[1][1] + t[2][1]) / 3 - terrain.grid.originN) / CELL);
    for (const [e, n] of t) {
      ok(e >= terrain.grid.originE + ci * CELL - 1e-6 && e <= terrain.grid.originE + (ci + 1) * CELL + 1e-6
        && n >= terrain.grid.originN + cj * CELL - 1e-6 && n <= terrain.grid.originN + (cj + 1) * CELL + 1e-6,
      `a draped triangle leaves its lattice cell at (${e}, ${n})`);
    }
    const s = (t[1][0] - t[0][0]) * (t[2][1] - t[0][1]) - (t[2][0] - t[0][0]) * (t[1][1] - t[0][1]);
    ok(s > 0, 'a draped triangle is not counter-clockwise in plan (its face would point down)');
  }
  ok(drapeTriangles([[0, 0], [1, 0]], terrain.grid).length === 0, 'a polygon of two points drapes nothing');
  // uv: along the bearing, in tiles; a quarter turn swaps the axes
  const [u0, v0] = uvAt(3.2, 0, 90, 1.6, 1.6);
  near(u0, 2, 1e-9, 'uv: 3.2 m east along a bearing of 90 is two 1.6 m tiles');
  near(v0, 0, 1e-9, 'uv: nothing across');
  const [u1] = uvAt(0, 4.8, 0, 1.6, 1.6);
  near(u1, 3, 1e-9, 'uv: 4.8 m north along a bearing of 0 is three tiles');
  // the steps
  for (const H of [0.05, 0.18, 0.45, 0.9, 1.3, 1.62, 2.1]) {
    const p = stoopPlan(5 + H, 5, 1.2);
    if (H < RISE_M * 0.5) { ok(p.risers === 0, `a ${H} m rise takes no step`); continue; }
    near(p.risers * p.rise, H, 1e-9, `the risers of a ${H} m stoop do not add up to it`);
    ok(p.rise >= 0.15 && p.rise <= 0.21, `a ${H} m stoop's rise ${p.rise.toFixed(3)} is not a stair's`);
    ok(p.treads.length === p.risers - 1, 'a stoop has one tread fewer than risers (the landing is the top one)');
    for (const [i, t] of p.treads.entries()) {
      near(t.s1 - t.s0, TREAD_M, 1e-9, 'a tread is not a tread deep');
      near(t.top, 5 + H - (i + 1) * p.rise, 1e-9, 'a tread is not one rise below the one above');
    }
    ok(p.rail === H > RAIL_RISE_M, `a ${H} m stoop's rail is ${p.rail}`);
  }
  // the file's own riser count, and a stoop of two risers with no landing (depth 0)
  {
    const p = stoopPlan(6.4, 5, 1.1, 8);
    ok(p.risers === 8 && Math.abs(p.run - (1.1 + 7 * TREAD_M)) < 1e-9, `the file's 8 risers are not kept (${p.risers}, run ${p.run})`);
    const q = stoopPlan(5.36, 5, 0, 2);
    ok(q.risers === 2 && q.treads.length === 1 && q.treads[0].s0 === 0 && Math.abs(q.treads[0].top - 5.18) < 1e-9,
      'a two-riser stoop with no landing does not step straight down from the sill');
  }
  // crops by season: summer plants them all, winter no annual
  const lots = FIXTURE.lots;
  const summer = cropPlan(lots, 'summer');
  ok(new Set(summer.map((p) => p.kind)).size === 5, 'summer plants every row the fixture names');
  const winter = cropPlan(lots, 'winter');
  ok(winter.every((p) => p.kind === 'currant'), 'winter stands an annual crop');
  for (const s of ['spring', 'fall', 'winter']) {
    ok(cropPlan(lots, s).every((p) => seasonLook(p.kind, s)), `${s} plants a crop gardens.js does not keep then`);
  }
  const probs = [];
  ok(cropPlan([{ parcel: 'x', crops: [{ bed: 'b', rows: [[0, 0, 4, 0, 'mandrake']] }] }], 'summer', { problems: probs }).length === 0
    && /unknown crop "mandrake"/.test(probs[0] ?? ''), 'an unknown crop is planted or not reported');
}

/* ---- the layer --------------------------------------------------------------------- */
const assetBase = new URL('../assets/', import.meta.url);
const fakeTex = () => { const t = new THREE.Texture(); t.name = 'shared'; return t; };
const shared = { map: fakeTex(), normalMap: fakeTex(), orm: fakeTex() };
// material.json for the shared cement is fetched; let that one file through from disk
globalThis.fetch = async (url) => {
  const u = String(url);
  if (u.startsWith('file:') && u.endsWith('/walk/portland_cement_walk/material.json')) {
    const body = fs.readFileSync(new URL(u), 'utf8');
    return { ok: true, status: 200, json: async () => JSON.parse(body) };
  }
  return { ok: false, status: 404, statusText: 'Not Found', json: async () => ({}) };
};
const problems = [];
const yard = await createBackYards({
  doc: FIXTURE, assetBase, sceneId: 'test', terrain, problems, bedOf, detail: 'full', season: 'summer',
  confidence: { patch() {} }, sharedMaps: new Map([['walk/portland_cement_walk', shared]]),
});
const g = yard.group;
const surfaces = g.children.filter((o) => o.isMesh && o.userData.decal);
const fixtures = g.children.filter((o) => o.isMesh && /^back-yards-(fixtures|stone):/.test(o.name));
const lines = g.children.filter((o) => o.isLineSegments);

// fallback and sharing
for (const id of ['yard_brick_herringbone', 'bluestone_flags', 'pea_gravel', 'beaten_earth', 'garden_loam']) {
  ok(problems.some((p) => p.includes(`the ${id} maps did not arrive`)), `the missing ${id} maps record no problem`);
}
const matOf = (key) => surfaces.find((m) => m.userData.material === key)?.material;
ok(matOf('cement')?.map === shared.map && matOf('cement')?.normalMap === shared.normalMap,
  'the cement walk does not bind the maps the street grid already holds');
ok(!matOf('yard_brick')?.map && matOf('yard_brick')?.color.getHex() !== 0xffffff, 'a paving whose maps failed is not a flat tone');
ok(!surfaces.some((m) => m.userData.material === 'lawn'), "a 'turf' surface draws something (the sward is the ground's own)");
ok(yard.stats.textured === 1 && yard.stats.flat === 5, `textured ${yard.stats.textured}, flat ${yard.stats.flat}`);

// drape: every vertex lift_m over the field; decal state and order
const lift = new Map();
for (const lot of FIXTURE.lots) for (const s of lot.surfaces) lift.set(s.material, s.lift_m);
let verts = 0;
for (const m of surfaces) {
  const p = m.geometry.attributes.position;
  const lifts = FIXTURE.lots.flatMap((l) => l.surfaces).filter((s) => s.material === m.userData.material).map((s) => s.lift_m);
  for (let i = 0; i < p.count; i += 1) {
    const e = p.getX(i); const n = -p.getZ(i);
    const over = p.getY(i) - terrain.surfaceHeight(e, n);
    ok(lifts.some((l) => Math.abs(over - l) < 1e-4), `a ${m.userData.material} vertex stands ${over} over the field`);
    verts += 1;
  }
  const mat = m.material;
  ok(mat.depthWrite === false, `${m.name} writes depth: a ground decal must not`);
  ok(mat.polygonOffset === true && mat.polygonOffsetFactor === 0 && mat.polygonOffsetUnits < 0,
    `${m.name} has no polygon offset, or a slope term in it`);
  ok(mat.transparent === false, `${m.name} is transparent: it would draw after every roadway`);
  ok(m.renderOrder > WATER_ORDER && m.renderOrder < ROAD_ORDER, `${m.name} draws at ${m.renderOrder}, not between the water (${WATER_ORDER}) and the roads (${ROAD_ORDER})`);
  ok(m.castShadow === false && m.receiveShadow === true, `${m.name}: a decal casts a shadow or takes none`);
  const n0 = m.geometry.attributes.normal;
  for (let i = 0; i < n0.count; i += 7) ok(n0.getY(i) > 0.9, `${m.name} has a face pointing down`);
}
ok(verts > 0, 'no surface vertex was laid');
const bed = surfaces.find((m) => m.userData.material === 'loam'); const path = surfaces.find((m) => m.userData.material === 'trodden');
ok(bed.renderOrder > path.renderOrder, 'the garden bed (order 1) does not draw over the path under it (order 0)');
ok(Math.abs(BACK_YARD_RENDER_ORDER - path.renderOrder) < 1e-9, 'order 0 is not drawn at BACK_YARD_RENDER_ORDER');

// merged: one mesh per (material, order, chunk)
const keys = new Set();
for (const lot of FIXTURE.lots) for (const s of lot.surfaces) {
  if (FIXTURE.materials[s.material].texture === 'turf') continue;
  const ce = s.polygon_local_m.reduce((a, p) => a + p[0], 0) / s.polygon_local_m.length;
  const cn = s.polygon_local_m.reduce((a, p) => a + p[1], 0) / s.polygon_local_m.length;
  keys.add(`${s.material}|${s.order}|${Math.floor(ce / CHUNK_M)},${Math.floor(cn / CHUNK_M)}`);
}
ok(surfaces.length === keys.size, `${surfaces.length} surface meshes for ${keys.size} (material, order, chunk) keys`);
ok(new Set(surfaces.map((m) => m.material)).size === 6, 'surface materials are not shared across orders and chunks');
ok(surfaces.filter((m) => m.userData.material === 'cement').length === 3,
  'the cement walks are not three meshes: order 1 and order 0 in the first chunk, and the far walk in the next');
ok(fixtures.length === 2 && lines.length === 1, `${fixtures.length} fixture meshes and ${lines.length} line draws (want 2, paint and stone, and 1)`);
{
  const stone = fixtures.find((m) => /stone/.test(m.name));
  ok(stone.geometry.attributes.uv && stone.material.map === null,
    'the stone steps carry no uv, or bind a map where the street grid holds none');
}
const crops = g.children.filter((o) => o.isBatchedMesh);
ok(crops.length === 2, `${crops.length} crop batches (want leaves and solids)`);
const hungLeaves = g.children.filter((o) => o.isInstancedMesh && o.name.startsWith('back-yards-door-leaves:'));
ok(yard.stats.drawCalls === surfaces.length + fixtures.length + lines.length + crops.length + hungLeaves.length,
  `the layer counts ${yard.stats.drawCalls} draws for ${surfaces.length + fixtures.length + lines.length + crops.length + hungLeaves.length} objects`);
ok(yard.stats.drawCalls <= 6 * 2 * 2 + 2 + 1 + 2, 'the layer draws more than materials x orders x chunks + fixtures + lines + crops');

// steps: the fixtures reach from under the ground at a stoop's foot to the sill and the head
{
  const ys = (pred) => {
    const out = [];
    for (const m of fixtures) {
      const fx = m.geometry.attributes.position;
      for (let i = 0; i < fx.count; i += 1) { const e = fx.getX(i); const n = -fx.getZ(i); if (pred(e, n)) out.push(fx.getY(i)); }
    }
    return out;
  };
  for (const d of FIXTURE.lots.flatMap((l) => l.doors)) {
    const sill = BEDS[d.structure] + d.sill_m;
    const f = by.frameAt(d.e, d.n, d.facing_deg);
    const run = stoopPlan(sill, terrain.surfaceHeight(...f.plan(d.stoop.depth_m, 0)), d.stoop.depth_m).run;
    const inStoop = (e, n) => {
      const s = (e - d.e) * f.o[0] + (n - d.n) * f.o[1]; const w = (e - d.e) * f.t[0] + (n - d.n) * f.t[1];
      return s > -0.1 && s < run + 0.4 && Math.abs(w) < Math.max(d.width_m, d.stoop.width_m) / 2 + 0.2;
    };
    const y = ys(inStoop);
    const foot = terrain.surfaceHeight(...f.plan(run, 0));
    ok(Math.min(...y) < foot, `${d.id}: the stoop does not reach the ground at its foot (${Math.min(...y)} vs ${foot})`);
    ok(y.some((v) => Math.abs(v - (sill - 0.012)) < 0.002), `${d.id}: no landing at the sill (${sill})`);
    const head = sill + d.height_m;
    if (d.leaf) ok(Math.max(...y) > head && Math.max(...y) < head + 0.25, `${d.id}: the leaf's casing does not stand at the head (${Math.max(...y)} vs ${head})`);
    else ok(Math.max(...y) < sill + 1.2, `${d.id}: a door the model carries is drawn again`);
  }
  const without = await createBackYards({ doc: { ...FIXTURE, lots: FIXTURE.lots.map((l) => ({ ...l, doors: l.doors.map((d) => ({ ...d, sill_m: 0.4 })) })) },
    assetBase, terrain, problems: [], bedOf, confidence: { patch() {} } });
  ok(without.stats.fixtureBoxes < yard.stats.fixtureBoxes, 'a 0.4 m stoop draws as much as a 1.3 m one with its rail');
  without.dispose();
}

// season: every surface and the fixtures carry the snow; winter replants the crops
for (const m of [...surfaces, ...fixtures]) {
  ok(/chicago4d-season/.test(m.material.customProgramCacheKey?.() ?? ''), `${m.name} does not take Settings > Season`);
}
applySeasonLook('winter');
ok(seasonUniforms.uChiSnow.value === 1, 'winter lays no snow on the ground layers');
applySeasonLook('summer');
const summerPlants = yard.stats.plants;
ok(summerPlants > 0, 'summer grows no crop');
ok(yard.setSeason('winter') === true, 'setSeason(winter) does nothing');
ok(yard.stats.plants === cropPlan(FIXTURE.lots, 'winter').length && yard.stats.plants < summerPlants,
  `winter still stands ${yard.stats.plants} plants of ${summerPlants}`);
yard.setSeason('summer');
ok(yard.stats.plants === summerPlants, 'summer is not the file\'s planting again');

// confidence: each item's own grade
{
  const cement = surfaces.filter((m) => m.userData.material === 'cement' && m.geometry.boundingSphere.center.x < 100);
  const grades = (o) => new Set(cement.find((m) => m.renderOrder === BACK_YARD_RENDER_ORDER + o * 0.01).geometry.attributes._confidence.array);
  ok([...grades(1)].join() === '0.5' && [...grades(0)].join() === '1',
    'the inferred walk and the reconstructed gangway do not carry their own grades into the confidence view');
}

// cards
const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 500);
const lookDown = (e, n, h = 6) => {
  camera.position.set(e, terrain.surfaceHeight(e, n) + h, -n + 0.01);
  camera.lookAt(e, terrain.surfaceHeight(e, n), -n);
  camera.updateMatrixWorld(); camera.updateProjectionMatrix();
};
lookDown(22.5, 4);
let hit = yard.pickAt(new THREE.Vector2(0, 0), camera);
ok(hit?.id === 'back-yard.test_101.surface.0', `a pick on the terrace answers ${hit?.id}`);
let s = hit.record.sidecar;
ok(/^Rear terrace, brick paving, laid herringbone$/.test(s.name), `terrace card name: ${s.name}`);
ok(s.change_note.includes('101 Prairie Avenue') && s.change_note.includes('kitchen garden') && s.change_note.includes('Laid at the kitchen door.'),
  `terrace card note: ${s.change_note}`);
ok(s.attributes.kind.value === 'rear terrace' && s.attributes.kind.confidence === 'reconstructed', 'the card does not name the kind and grade');
ok(s.attributes.material.value === 'brick paving, laid herringbone', 'the card does not name the material');
ok(s.research_note.includes('L-prairie-back-yards-1904') && s.attributes.kind.note.includes('L-prairie-back-yards-1904'), 'the card does not name the liberty');
lookDown(33, 7.6);
hit = yard.pickAt(new THREE.Vector2(0, 0), camera);
ok(hit?.id === 'back-yard.test_101.surface.1' && hit.record.sidecar.attributes.kind.confidence === 'inferred'
  && /^Walk to the coach house, Portland cement walk$/.test(hit.record.sidecar.name), `a pick on the walk answers ${hit?.id} ${hit?.record?.sidecar?.name}`);
lookDown(33, 3.6);
hit = yard.pickAt(new THREE.Vector2(0, 0), camera);
ok(hit?.id === 'back-yard.test_101.crop.0.2' && /onion row in the kitchen garden/.test(hit.record.sidecar.name),
  `a pick on the onion row answers ${hit?.id} ${hit?.record?.sidecar?.name}`);
// the door from in front of it, a little above the landing
camera.position.set(24, BEDS.test_house_101 + 1.3 + 1.2, -7.6);
camera.lookAt(20, BEDS.test_house_101 + 1.3 + 1.0, -7.6); camera.updateMatrixWorld();
hit = yard.pickAt(new THREE.Vector2(0, 0), camera);
ok(hit?.id === 'back-yard.test_101.door.0' && /^The back door and its wooden steps$/.test(hit.record.sidecar.name)
  && hit.record.sidecar.change_note.includes('The kitchen door.'), `a pick on the back door answers ${hit?.id} ${hit?.record?.sidecar?.name}`);
camera.position.set(28, terrain.surfaceHeight(28, 11.5) + 1.6, -11.5 - 3);
camera.lookAt(28, terrain.surfaceHeight(28, 11.5) + 1.2, -11.5); camera.updateMatrixWorld();
hit = yard.pickAt(new THREE.Vector2(0, 0), camera);
ok(hit?.id === 'back-yard.test_101.post.0' && /clothes post/.test(hit.record.sidecar.name), `a pick on the clothes post answers ${hit?.id}`);
ok(yard.cardFor('back-yard.test_105.surface.1')?.sidecar.change_note.includes('105–107 Prairie Avenue'), 'cardFor does not name a lot of two addresses');
ok(yard.cardFor('back-yard.test_105.door.0')?.sidecar.attributes.material.value === 'stone steps', 'a stone stoop is not named stone steps');
ok(yard.cardFor('back-yard.nope.surface.0') === null, 'cardFor answers for a lot that is not there');

// detail: light drops boards and balusters, and the chunk past reach is not drawn
{
  const before = yard.stats.fixtureBoxes;
  yard.setDetail('light');
  ok(yard.stats.fixtureBoxes < before, 'light detail draws the stoops in as many boxes');
  camera.position.set(-300, 5, 0); camera.updateMatrixWorld();
  yard.settle(camera);
  ok(surfaces.filter((m) => m.visible).length < surfaces.length, 'a chunk 300 m beyond light reach is still drawn');
  yard.setDetail('full');
}

// a missing file and an absent layer
{
  const p = [];
  const none = await createBackYards({ dataBase: new URL('file:///nowhere/data/'), sceneId: '1904', terrain, problems: p });
  ok(none.group.children.length === 0 && /back yards: 404/.test(p[0] ?? ''), `a missing file: ${p[0]}`);
  const off = await createBackYards({ dataBase: null, sceneId: '1904', terrain, problems: p });
  ok(off.group.children.length === 0 && p.length === 1, 'a scene not listing back_yards draws or reports something');
}
yard.dispose();

/* ---- the plants, through front-yards.js -------------------------------------------- */
{
  const { createFrontYards } = await import('../renderers/web/js/front-yards.js');
  const mats = { woodMat: new THREE.MeshStandardMaterial(), leafMat: new THREE.MeshStandardMaterial(),
    woodDepth: new THREE.MeshDepthMaterial(), leafDepth: new THREE.MeshDepthMaterial(),
    woodDistance: new THREE.MeshDistanceMaterial(), leafDistance: new THREE.MeshDistanceMaterial(), dispose() {} };
  const fy = await createFrontYards({ dataBase: null, sceneId: 'test', terrain, problems: [], grownMaterials: mats, back: FIXTURE });
  ok(fy.stats.lots === 2 && fy.stats.shrubs === 1, `front-yards.js grew the back lots' plants as ${JSON.stringify(fy.stats)}`);
  const card = fy.cardFor('front-yard.test_101.back.shrub.0');
  ok(card?.id === 'front-yard.test_101.back.shrub.0' && /back yard/.test(card.sidecar.name)
    && /back_yards/.test(card.sidecar.research_note) && card.sidecar.research_note.includes('L-prairie-back-yards-1904'),
  `a back-yard shrub's card: ${JSON.stringify(card?.sidecar?.name)} ${card?.sidecar?.research_note}`);
  ok(fy.cardFor('front-yard.test_101.shrub.0') === null, "a back lot's plant answers to a front lot's id");
  fy.dispose();
  const empty = await createFrontYards({ dataBase: null, sceneId: 'test', terrain, problems: [] });
  ok(empty.stats.lots === 0 && empty.group.children.length === 0, 'front-yards.js with no data base and no back draws something');
}

/* ---- the real file, where it is in the tree: built whole, inside the draw bound ------ */
let real = '';
{
  const url = new URL('../data/back_yards/1904.json', import.meta.url);
  if (fs.existsSync(url)) {
    const doc = JSON.parse(fs.readFileSync(url, 'utf8'));
    const p = [];
    const flatField = { surfaceHeight: (e, n) => 4 + 0.002 * e, grid: { cellM: 2.5, originE: 0, originN: 0 } };
    const all = await createBackYards({ doc, assetBase, terrain: flatField, problems: p, confidence: { patch() {} } });
    const unexpected = p.filter((x) => !/maps did not arrive/.test(x));
    ok(unexpected.length === 0, `the real file raises ${unexpected.slice(0, 3).join(' | ')}`);
    ok(all.stats.surfaces === doc.lots.reduce((n, l) => n + (l.surfaces ?? []).length, 0), 'a surface of the real file was not laid');
    const mats = new Set(doc.lots.flatMap((l) => (l.surfaces ?? []).map((x) => x.material))).size;
    const orders = new Set(doc.lots.flatMap((l) => (l.surfaces ?? []).map((x) => x.order ?? 0))).size;
    ok(all.stats.meshes <= mats * orders * all.stats.chunks, 'the real file draws more meshes than materials x orders x chunks');
    real = `; real file ${all.stats.meshes} surface meshes in ${all.stats.chunks} chunks, ${all.stats.triangles} triangles, `
      + `${all.stats.fixtureBoxes} fixture boxes, ${all.stats.plants} crop plants, ${all.stats.drawCalls} draws whole`;
    all.dispose();
  }
}

// passages (T-3554): the back doors open and shut, and their ways climb the stoops
{
  const ids = yard.passages.map((x) => x.id).sort();
  ok(JSON.stringify(ids) === JSON.stringify(['test_house_101:back', 'test_house_105:back']),
    `one passage per house's back door with a leaf and a stoop, the model's own side door not one (${ids})`);
  const leaves = g.children.filter((o) => o.isInstancedMesh && o.name.startsWith('back-yards-door-leaves:'));
  ok(leaves.length === 1 && leaves[0].count === 2, 'the two leaves are one instanced draw');
  const corner = new THREE.Vector3(), m = new THREE.Matrix4();
  for (const x of yard.passages) {
    const d = x.door;
    const f = by.frameAt(d.e, d.n, d.facing_deg);
    const sill = BEDS[d.structure] + d.sill_m;
    const w = x.way();
    ok(w[0].y === null && w.at(-1).y === sill && w[w.door].y === sill, `${x.id}: from the ground to the landing and over the sill`);
    const ys = w.map((p) => p.y ?? terrain.surfaceHeight(p.e, p.n));
    for (let i = 1; i <= w.door; i += 1) {
      ok(ys[i] >= ys[i - 1] - 0.13, `${x.id}: the way in climbs (${i}: ${ys[i - 1]} -> ${ys[i]})`);
      if (w[i - 1].y !== null && w[i].y - w[i - 1].y > 1e-4) {
        ok(w[i].y - w[i - 1].y <= 0.21 && Math.hypot(w[i].e - w[i - 1].e, w[i].n - w[i - 1].n) <= 0.25, `${x.id}: a riser at a time (${i})`);
      }
    }
    const sOf = (p) => (p.e - d.e) * f.o[0] + (p.n - d.n) * f.o[1];
    ok(Math.abs(sOf(w[w.door]) - 0.95) < 1e-6 && sOf(w.at(-1)) < 0, `${x.id}: waits on the landing clear of the leaf, ends indoors`);
    // The free edge's foot, shut and open, from the instance's pose.
    const edge = (t) => {
      x.setSwing(t);
      leaves[0].getMatrixAt(x.slot, m);
      corner.set(d.width_m, 0, 0).applyMatrix4(m);
      return { s: (corner.x - d.e) * f.o[0] + (-corner.z - d.n) * f.o[1], w: (corner.x - d.e) * f.t[0] + (-corner.z - d.n) * f.t[1], y: corner.y };
    };
    const shut = edge(0), open = edge(1);
    ok(Math.abs(shut.s) < 1e-6 && Math.abs(shut.w - d.width_m / 2) < 1e-6 && Math.abs(shut.y - sill) < 1e-6, `${x.id}: shut, the leaf fills its opening`);
    ok(open.s > 0.9 && Math.abs(open.w + d.width_m / 2) < 0.15, `${x.id}: open, it stands out over the landing at its hinge (${open.s.toFixed(2)}, ${open.w.toFixed(2)})`);
    x.hold('k'); ok(x.holders.size === 1, `${x.id}: held`); x.release('k'); ok(x.holders.size === 0, `${x.id}: let go`); x.setSwing(0);
  }
  // The hung leaf is not baked again: the fixtures carry the doorway's dark where it shuts.
  const doorway = new THREE.Color(0x0b0a09);
  const darks = fixtures.some((mesh) => { const c = mesh.geometry.attributes.color; for (let i = 0; i < c.count; i += 1) if (Math.abs(c.getX(i) - doorway.r) < 0.01 && Math.abs(c.getY(i) - doorway.g) < 0.01) return true; return false; });
  ok(darks, 'the doorway behind a hung leaf is dark');
}

globalThis.fetch = realFetch;
console.log(`test_back_yards: PASS (${checks} checks; ${surfaces.length} surface meshes, ${yard.stats.triangles} triangles, `
  + `${yard.stats.drawCalls} draws, ${yard.stats.fixtureBoxes} fixture boxes${real})`);
