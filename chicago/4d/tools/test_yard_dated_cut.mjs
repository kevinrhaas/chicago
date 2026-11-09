#!/usr/bin/env node
/**
 * T-3527 — the 1812 gathering's camps come and go with the date.
 *
 * The owner, 2026-11-08, walked the camps in April, found them empty (the people follow
 * their August dates), and chose "Camps follow the date": the lodges and the ground their
 * people wore stand only on the gathering's days. Headless, no browser:
 *
 *   records   every Potawatomi camp and the Miami escort's camp states its range as
 *             `drawn_only_within`, and the compiled sidecar carries it (buildings.js reads
 *             the sidecar); no other 1812 structure does;
 *   ground    the camp ground states one window per ring, its own camp's range; the camp
 *             paths carry the gathering's days; the older trails (lake shore, Vincennes,
 *             cart road, bank paths) none;
 *   mask      read back as the GPU reads it (nearest), every ring's inside names its window,
 *             every every-day trail's centre line is uncut, and the windows are few enough
 *             for the shader's array;
 *   dates     onWindow: in on its first and last day, out the day either side, in with no
 *             date; the layer's setDate counts the windows away;
 *   wiring    the cut is compiled only with YARD_DATED, which declares its uniforms, and is
 *             spliced after the dwelling cut; buildings.js hides by collapsing instance
 *             matrices (not visibility, which the far hooks toggle) and main.js hands both
 *             layers the world's date when it changes.
 *
 *   node tools/test_yard_dated_cut.mjs
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

const THREE = await import('three');
const { datedMask, datedPiecesOf, onWindow, DATED_MAX } = await import('../renderers/web/js/yards.js');

const root = new URL('..', import.meta.url);
const read = (p) => JSON.parse(fs.readFileSync(new URL(p, root), 'utf8'));
let checks = 0;

// records
const isCamp = (id) => id.startsWith('potawatomi_camp_1812_') || id === 'miami_escort_camp_1812';
const ranges = new Map();
for (const f of fs.readdirSync(new URL('data/sidecars/1812/', root)).filter((x) => x.endsWith('.json'))) {
  const sc = read(`data/sidecars/1812/${f}`);
  const rng = sc.documented_range ?? {};
  if (isCamp(sc.id ?? f.replace(/\.json$/, ''))) {
    assert.equal(rng.drawn_only_within, true, `${f}: a gathering camp drawn every day`);
    assert.match(rng.from ?? '', /^1812-08-\d\d$/, `${f}: from ${rng.from}`);
    assert.match(rng.to ?? '', /^1812-08-\d\d$/, `${f}: to ${rng.to}`);
    const st = read(`data/structures/${f}`);
    assert.ok((st.phases ?? []).some((ph) => ph.documented_range?.drawn_only_within === true), `${f}: structure record lacks drawn_only_within`);
    ranges.set(sc.id, { from: rng.from, to: rng.to });
  } else {
    assert.notEqual(rng.drawn_only_within, true, `${f}: only the gathering's camps come and go`);
  }
  checks += 1;
}
assert.equal(ranges.size, 14, `dated camps: ${ranges.size}`);

// ground
const camp = read('data/enclosures/1812/potawatomi_camp_1812_ground.json');
const trails = read('data/enclosures/1812/worn_trails_1812.json');
const rings = camp.ground.interior_local_enu_m;
const wins = camp.ground.interior_drawn_within;
assert.equal(wins.length, rings.length, 'one window per camp ring');
const sorted = [...ranges.values()];
for (const w of wins) {
  assert.ok(w && sorted.some((r) => r.from === w.from && r.to === w.to), `ring window ${JSON.stringify(w)} is no camp's range`);
  checks += 1;
}
const pota = [...ranges].filter(([id]) => id.startsWith('potawatomi')).map(([, r]) => r);
const gather = { from: pota.map((r) => r.from).sort()[0], to: pota.map((r) => r.to).sort().at(-1) };
const campPaths = trails.ground.trails.filter((t) => t.drawn_within);
const everyDay = trails.ground.trails.filter((t) => !t.drawn_within);
assert.ok(campPaths.length >= 20, `camp paths dated: ${campPaths.length}`);
assert.ok(everyDay.length >= 10, `every-day trails: ${everyDay.length}`);
for (const t of campPaths) {
  assert.deepEqual(t.drawn_within, gather, `${t.id}: dated ${JSON.stringify(t.drawn_within)}`);
  assert.match(t.id, /camp|lodge|water|landing|factory|path/i, `${t.id}: dated but not a camp path`);
  checks += 1;
}
for (const id of ['lake_shore', 'vincennes', 'cart', 'bank']) {
  const t = trails.ground.trails.find((x) => x.id.includes(id));
  if (t) { assert.ok(!t.drawn_within, `${t.id}: an old trail drawn only in August`); checks += 1; }
}

// mask
const problems = [];
const mask = datedMask([camp, trails], problems);
assert.ok(mask, 'no dated mask for 1812');
assert.deepEqual(problems, []);
const { texture, box, windows, width, height, data } = mask;
assert.ok(windows.length >= 1 && windows.length <= DATED_MAX, `windows ${windows.length}`);
assert.equal(mask.away.length, DATED_MAX);
const at = (e, n) => {
  const u = (e - box.x) * box.z; const v = (n - box.y) * box.w;
  if (u <= 0 || v <= 0 || u >= 1 || v >= 1) return 0;
  return data[Math.floor(v * height) * width + Math.floor(u * width)];
};
const keyOf = (w) => `${w.from}|${w.to}`;
const nearEveryDay = (e, n) => everyDay.some((t) => t.line_local_enu_m.some(([a, b], i, L) => {
  if (i + 1 >= L.length) return false;
  const [c, d] = L[i + 1]; const dx = c - a; const dn = d - b; const L2 = dx * dx + dn * dn;
  const s = L2 > 0 ? Math.max(0, Math.min(1, ((e - a) * dx + (n - b) * dn) / L2)) : 0;
  return Math.hypot(e - a - s * dx, n - b - s * dn) < 4;
}));
rings.forEach((ring, i) => {
  const want = windows.findIndex((w) => keyOf(w) === keyOf(wins[i])) + 1;
  assert.ok(want > 0, `ring ${i}: its window is not in the mask`);
  let tried = 0;
  for (const [e, n] of ring) {
    // a point a quarter of the way in from each vertex toward the ring's centroid
    const ce = ring.reduce((s, p) => s + p[0], 0) / ring.length; const cn = ring.reduce((s, p) => s + p[1], 0) / ring.length;
    const pe = e + (ce - e) * 0.25; const pn = n + (cn - n) * 0.25;
    if (nearEveryDay(pe, pn)) continue;
    assert.equal(at(pe, pn), want, `ring ${i}: ${pe.toFixed(1)}, ${pn.toFixed(1)} not cut by its window`);
    tried += 1; checks += 1;
  }
  assert.ok(tried > 0, `ring ${i}: nothing checked`);
});
for (const t of everyDay) {
  for (const [e, n] of t.line_local_enu_m) { assert.equal(at(e, n), 0, `${t.id}: every-day trail cut at ${e}, ${n}`); checks += 1; }
}
for (const t of campPaths) {
  const L = t.line_local_enu_m; const [e, n] = L[Math.floor(L.length / 2)];
  if (!nearEveryDay(e, n)) { assert.ok(at(e, n) > 0, `${t.id}: camp path not cut mid-way`); checks += 1; }
}
assert.equal(texture.unpackAlignment, 1);
assert.equal(texture.format, THREE.RedFormat);
assert.equal(texture.magFilter, THREE.NearestFilter);
assert.equal(texture.minFilter, THREE.NearestFilter);
assert.equal(texture.generateMipmaps, false);
assert.ok(width * height < 1.5e6, `mask ${width} x ${height} is over its budget`);
assert.equal(datedMask([]), null);
assert.equal(datedMask([read('data/enclosures/1812/worn_yard_1812_factory.json')]), null);
assert.equal(datedPiecesOf([trails]).length, trails.ground.trails.length);

// dates
const w = { from: '1812-08-12', to: '1812-08-16' };
assert.ok(onWindow('1812-08-12', w) && onWindow('1812-08-16', w) && onWindow('1812-08-14T10:00', w));
assert.ok(!onWindow('1812-08-11', w) && !onWindow('1812-08-17', w) && !onWindow('1812-04-15', w));
assert.ok(onWindow(undefined, w) && onWindow('1812-04-15', null));
checks += 1;

// wiring
const src = fs.readFileSync(new URL('renderers/web/js/yards.js', root), 'utf8');
assert.match(src, /#ifdef YARD_DATED\s*\nuniform sampler2D uDated;\s*\nuniform vec4 uDatedBox;\s*\nuniform float uDatedAway\[\$\{DATED_MAX\}\];\s*\n#endif/,
  'YARD_HEAD declares the dated cut\'s uniforms under its define');
assert.match(src, /`#include <clipping_planes_fragment>\\n\$\{DWELLING_CUT\}\\n\$\{DATED_CUT\}`/, 'the dated cut follows the dwelling cut');
assert.match(src, /if \(dated\) mat\.defines = \{ \.\.\.\(mat\.defines \?\? \{\}\), YARD_DATED: '' \}/);
assert.match(src, /out\.setDate = \(date\) =>/);
const bsrc = fs.readFileSync(new URL('renderers/web/js/buildings.js', root), 'utf8');
assert.match(bsrc, /documented_range\?\.drawn_only_within === true/);
assert.match(bsrc, /batch\.setMatrixAt\(i, show \? matrix : ZERO_MATRIX\)/, 'dated structures hide by a zero matrix');
const msrc = fs.readFileSync(new URL('renderers/web/js/main.js', root), 'utf8');
assert.match(msrc, /buildings\?\.setDate\?\.\(world\.sunDate\)/);
assert.match(msrc, /api\.yards\?\.setDate\?\.\(world\.sunDate\)/);
const csrc = fs.readFileSync(new URL('tools/compile_scene.py', root), 'utf8');
assert.match(csrc, /"drawn_only_within": True\} if rng\.get\("drawn_only_within"\) is True/);

console.log(`yard dated cut OK — ${ranges.size} dated camps, ${campPaths.length} camp paths, ${windows.length} windows, mask ${width} x ${height}, ${checks} checks`);
