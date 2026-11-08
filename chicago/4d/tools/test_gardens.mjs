#!/usr/bin/env node
/**
 * T-3407 — the 1812 commanding officer's garden grows what data/gardens/1812.json plants,
 * inside a budget a phone can carry.
 *
 * With the real garden file, no browser:
 *   - every crop the file plants has a grower in gardens.js, and every grower is a crop
 *     the file's table names (no orphan on either side);
 *   - every kind grows at all three levels and every variant, with finite positions, a
 *     normal, a uv and the `_confidence` attribute confidence.js patches by;
 *   - a level never costs more than the one nearer it (near >= mid >= far);
 *   - the whole garden drawn at its FAR level (what a phone sees from the fort) stays under
 *     FAR_TRIS, and the template set every copy is drawn from stays under TEMPLATE_BYTES.
 *
 * T-3460, Settings > Season (the owner, 2026-11-07: "its winter in 1812 and we still have
 * a garden!"):
 *   - summer is the file's own planting: growTemplate(..., 'summer') is the same geometry
 *     as growTemplate(...) with no season;
 *   - every look names a kind the garden grows, and every kind a season keeps grows at
 *     every level and variant, finite, near >= mid >= far, within the same ceilings;
 *   - winter keeps no annual crop and no leaf: only the bushes and the canes stand;
 *   - spring has no corn, beans, melons, squash, cucumbers or potatoes above the ground
 *     (M'Mahon sows them in May), and fall no melons, onions or potatoes.
 *
 *   node tools/test_gardens.mjs
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
const { growTemplate, KINDS, SEASON_CROPS, seasonLook } = await import('../renderers/web/js/gardens.js');

// Measured 2026-11-06: 64k at far, ~2.3 MB of templates. The ceilings leave room to grow
// a crop's detail, not to double the garden.
// T-3477, 2026-11-07: the bank's other gardens (Kinzie's, the sutler's, Coursoll's field, the
// factory's and the agency's, Ouilmette's and La Lime's) all stand within the far ring of the
// officer's: 192k at far with every one of them in view, the officer's own 73k of it. A phone
// draws its far ring to 280 m, not 450, and its frame holds only part of the bank.
const FAR_TRIS = 200_000;
const TEMPLATE_BYTES = 3_500_000;

const doc = JSON.parse(fs.readFileSync(new URL('../data/gardens/1812.json', import.meta.url), 'utf8'));
let checks = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); checks += 1; };

const planted = new Set();
for (const g of doc.gardens) for (const k of Object.keys(g.plants)) planted.add(k);
const table = new Set(Object.keys(doc.crops));
for (const k of planted) ok(KINDS[k], `the garden plants ${k}, which gardens.js cannot grow`);
for (const k of Object.keys(KINDS)) ok(table.has(k), `gardens.js grows ${k}, which the garden's crop table does not name`);

const LEVELS = ['near', 'mid', 'far'];
let bytes = 0;
const tris = {};
for (const k of Object.keys(KINDS)) {
  tris[k] = {};
  for (const lod of LEVELS) {
    for (const v of [0, 1, 2]) {
      const t = growTemplate(k, v, lod, 1);
      ok(t && t.tris > 0, `${k} ${lod} v${v} grows nothing`);
      for (const part of ['leaves', 'solid']) {
        const geo = t[part];
        if (!geo) continue;
        for (const name of ['position', 'normal', 'uv', '_confidence']) {
          ok(geo.attributes[name], `${k} ${lod} v${v} ${part} has no ${name}`);
        }
        const p = geo.attributes.position.array;
        ok(p.every(Number.isFinite), `${k} ${lod} v${v} ${part} has a non-finite position`);
        for (const a of Object.values(geo.attributes)) bytes += a.array.byteLength;
        if (geo.index) bytes += geo.index.array.byteLength;
      }
      if (v === 0) tris[k][lod] = t.tris;
    }
  }
  ok(tris[k].near >= tris[k].mid && tris[k].mid >= tris[k].far,
    `${k}: a farther level costs more (near ${tris[k].near}, mid ${tris[k].mid}, far ${tris[k].far})`);
}

// T-3477: 1812 plants a dozen gardens a kilometre and more apart (the fort's bank, the forks, Lee's
// Place four kilometres off), so the ceiling holds what a phone sees at once: every garden within
// the far ring (450 m, the widest level's) of any one garden, at its far level.
const centre = (g) => {
  const [W, D] = g.size_m, [oe, on] = g.frame.origin, [ue, un] = g.frame.u, [ve, vn] = g.frame.v;
  return [oe + ue * W / 2 + ve * D / 2, on + un * W / 2 + vn * D / 2];
};
const REACH_M = 450;
const inReach = (costOf) => {
  let worst = 0, where = '';
  for (const g of doc.gardens) {
    const [ce, cn] = centre(g);
    let sum = 0;
    for (const h of doc.gardens) {
      const [he, hn] = centre(h);
      if (Math.hypot(he - ce, hn - cn) <= REACH_M) sum += costOf(h);
    }
    if (sum > worst) { worst = sum; where = g.id; }
  }
  return [worst, where];
};
const [far, farAt] = inReach((g) => Object.entries(g.plants).reduce((a, [k, list]) => a + tris[k].far * list.length, 0));
ok(far <= FAR_TRIS, `the gardens in reach of ${farAt} at their far level are ${far} triangles, over ${FAR_TRIS}`);
ok(bytes <= TEMPLATE_BYTES, `the garden's templates hold ${bytes} bytes, over ${TEMPLATE_BYTES}`);

/* ---- T-3460: the seasons ---- */
const sameGeo = (a, b) => {
  if (!a || !b) return a === b;
  for (const name of Object.keys(a.attributes)) {
    const x = a.attributes[name].array, y = b.attributes[name]?.array;
    if (!y || x.length !== y.length || x.some((v, i) => v !== y[i])) return false;
  }
  return true;
};
for (const k of Object.keys(KINDS)) {
  for (const lod of LEVELS) {
    const a = growTemplate(k, 0, lod, 1), b = growTemplate(k, 0, lod, 1, 'summer');
    ok(sameGeo(a.leaves, b.leaves) && sameGeo(a.solid, b.solid), `${k} ${lod}: summer is not the file's own planting`);
  }
}
const ANNUALS = ['corn', 'pole_bean', 'cabbage', 'potato', 'muskmelon', 'watermelon', 'squash', 'cucumber',
  'onion', 'beet', 'carrot', 'parsnip', 'lettuce'];
const NOT_IN_APRIL = ['corn', 'pole_bean', 'muskmelon', 'watermelon', 'squash', 'cucumber', 'potato'];
const DONE_BY_OCTOBER = ['muskmelon', 'watermelon', 'cucumber', 'onion', 'potato'];
for (const k of ANNUALS) ok(seasonLook(k, 'winter') === null, `winter still grows ${k}`);
for (const k of NOT_IN_APRIL) ok(seasonLook(k, 'spring') === null, `April already shows ${k}`);
for (const k of ['onion', 'potato']) ok(seasonLook(k, 'fall') === null, `October still shows ${k}`);
for (const k of DONE_BY_OCTOBER.filter((k) => seasonLook(k, 'fall'))) {
  ok(seasonLook(k, 'fall').stage === 'spent', `October's ${k} still bears`);
}
const seasonFar = {};
for (const season of Object.keys(SEASON_CROPS)) {
  let sBytes = 0;
  for (const k of Object.keys(SEASON_CROPS[season])) ok(KINDS[k], `${season} names ${k}, which gardens.js cannot grow`);
  const st = {};
  for (const k of Object.keys(KINDS)) {
    const look = seasonLook(k, season);
    if (!look) { ok(growTemplate(k, 0, 'far', 1, season) === null, `${season}: ${k} has no look but grows`); continue; }
    st[k] = {};
    for (const lod of LEVELS) {
      for (const v of [0, 1, 2]) {
        const t = growTemplate(k, v, lod, 1, season);
        ok(t && t.tris > 0, `${season}: ${k} ${lod} v${v} grows nothing`);
        for (const part of ['leaves', 'solid']) {
          const geo = t[part];
          if (!geo) continue;
          ok(geo.attributes.position.array.every(Number.isFinite), `${season}: ${k} ${lod} v${v} ${part} has a non-finite position`);
          ok(geo.attributes.color.array.every(Number.isFinite), `${season}: ${k} ${lod} v${v} ${part} has a non-finite colour`);
          for (const a of Object.values(geo.attributes)) sBytes += a.array.byteLength;
          if (geo.index) sBytes += geo.index.array.byteLength;
        }
        if (v === 0) st[k][lod] = t;
      }
    }
    ok(st[k].near.tris >= st[k].mid.tris && st[k].mid.tris >= st[k].far.tris, `${season}: ${k}: a farther level costs more`);
    if (season === 'winter') ok(!st[k].near.leaves, `winter: ${k} still carries leaves`);
  }
  const [f, fAt] = inReach((g) => Object.entries(g.plants).reduce((a, [k, list]) => a + (st[k] ? st[k].far.tris * list.length : 0), 0));
  seasonFar[season] = f;
  ok(f <= FAR_TRIS, `${season}: the gardens in reach of ${fAt} at their far level are ${f} triangles, over ${FAR_TRIS}`);
  ok(sBytes <= TEMPLATE_BYTES, `${season}: the garden's templates hold ${sBytes} bytes, over ${TEMPLATE_BYTES}`);
}

// T-3476: the 1835 town's dooryard gardens. Its summer is SEASON_CROPS.july, which must
// name every kind (a kind missing from a season is not drawn), and every kind it plants is in
// its crop table, in the beds it states.
{
  const town = JSON.parse(fs.readFileSync(new URL('../data/gardens/1835.json', import.meta.url), 'utf8'));
  ok(town.summer_stage === 'july', '1835 draws its summer as early July');
  for (const kind of Object.keys(KINDS)) ok(SEASON_CROPS.july[kind], `SEASON_CROPS.july has no row for ${kind}`);
  ok(town.gardens.length >= 60, `1835 plants ${town.gardens.length} gardens`);
  const sizes = new Set(town.gardens.map((g) => g.size_m.join('x')));
  ok(sizes.size === town.gardens.length, `two 1835 gardens share a size (${sizes.size} sizes for ${town.gardens.length})`);
  for (const g of town.gardens) {
    ok(g.ground === 'beds', `${g.id} lays its own beds`);
    for (const kind of Object.keys(g.plants)) ok(town.crops[kind] && KINDS[kind], `${g.id} plants ${kind}, not in the crop table`);
  }
  ok(Number.isFinite(town.reach_m) && town.reach_m <= 200, '1835 draws its plants no farther than 200 m');
}

console.log(`test_gardens: PASS (${checks} checks; far ${far} tris, templates ${(bytes / 1e6).toFixed(2)} MB; `
  + `far spring ${seasonFar.spring}, fall ${seasonFar.fall}, winter ${seasonFar.winter})`);
