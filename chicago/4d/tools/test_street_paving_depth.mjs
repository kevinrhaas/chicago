#!/usr/bin/env node
/**
 * T-3389 — no two 1904 pavings lie in one place at one height.
 *
 * The owner, 2026-11-05, on screenshots at Prairie & 18th and Prairie & 20th: "pixely flashy
 * transitions when moving over any of the transitions between the paved and gravely surface".
 * T-3088 had drawn every roadway and the seam overlay (T-2475) on ONE surface and ranked them
 * by polygon offset alone. But two pavings are triangulated differently over a field quantized
 * to 5 mm, so between their vertices they differ by up to 1.7 mm, far past any offset in depth
 * units: the fade dipped under the roadway it lies on and the strip a lower roadway runs on
 * under a higher one's edge (TUCK_M) lay exactly in it. Both fought for the depth buffer in
 * blocks wherever two pavings meet, and the blocks moved with the eye.
 *
 * Now each roadway stands at its own level (priority, then its place among the overlapping
 * roadways of that priority, PRIORITY_LIFT_M a level) and the overlay SEAM_LIFT_M over the
 * highest. This builds the shipped street grid headless on the real 1904 terrain (the
 * e1871_postfire heightfield, sampled as terrain.js samples it), drops a probe every
 * SAMPLE_M over every roadway, and at each point compares every paving drawn there:
 *
 *   overlay  a seam overlay stands at least MIN_GAP_M over every opaque roadway under it;
 *   stack    two opaque roadways of different pavings (or different roadways) that overlap
 *            stand at least MIN_GAP_M apart.
 *
 * One way's own pieces in its own paving may meet (they draw the same texel) and are skipped.
 *
 *   node tools/test_street_paving_depth.mjs [--self-test]
 *
 * --self-test loads street-grid.js with the per-way lift and then the overlay's lift taken back
 * out (the hook edits the source as it loads) and requires each check to fire. Exit 0 on pass,
 * 1 on a failed check, 2 if the source no longer has the shape the self-test edits (drift).
 */
import { readFileSync } from 'node:fs';
import { register } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const SRC = join(ROOT, 'renderers/web/js/street-grid.js');
const THREE_DIR = pathToFileURL(join(ROOT, 'renderers/web/vendor/three-0.185.1/')).href;
const SELF_TEST = process.argv.includes('--self-test');
const SAMPLE_M = 0.1;
/** Measured after the fix: 2.1 mm between roadways, 2.9 mm under the overlay. */
const MIN_GAP_M = 0.0015;

const UNDO = {
  stack: [['polys, lift: w.lift });', 'polys });']],
  overlay: [['lift: seam ? c.lift + topRoadLift + SEAM_LIFT_M :', 'lift: seam ? c.lift :']],
};
const src = readFileSync(SRC, 'utf8');
for (const [k, edits] of Object.entries(UNDO)) {
  for (const [from] of edits) {
    if (src.split(from).length !== 2) {
      console.error(`DRIFT — street-grid.js no longer holds the ${k} fix as \`${from.trim()}\` exactly once;`
        + ' fix this test against the source, do NOT weaken it');
      process.exit(2);
    }
  }
}

const hooks = `
const THREE_DIR = ${JSON.stringify(THREE_DIR)};
const UNDO = ${JSON.stringify(UNDO)};
export async function resolve(spec, ctx, next) {
  if (spec === 'three') return { url: THREE_DIR + 'three.module.js', shortCircuit: true };
  if (spec.startsWith('three/addons/')) return { url: THREE_DIR + 'addons/' + spec.slice(13), shortCircuit: true };
  return next(spec, ctx);
}
export async function load(url, ctx, next) {
  const undo = new URL(url).searchParams.get('undo');
  if (!undo) return next(url, ctx);
  const { readFileSync } = await import('node:fs');
  const { fileURLToPath } = await import('node:url');
  let source = readFileSync(fileURLToPath(url.split('?')[0]), 'utf8');
  for (const [from, to] of UNDO[undo]) source = source.replace(from, to);
  return { format: 'module', source, shortCircuit: true };
}
`;
register(`data:text/javascript,${encodeURIComponent(hooks)}`, import.meta.url);

globalThis.fetch = async (url) => {
  const u = new URL(String(url));
  try {
    const text = readFileSync(fileURLToPath(u), 'utf8');
    return { ok: true, status: 200, json: async () => JSON.parse(text) };
  } catch (err) {
    return { ok: false, status: 404, statusText: err.code ?? 'unreadable' };
  }
};

const read = (rel) => JSON.parse(readFileSync(join(ROOT, rel), 'utf8'));
const scene = read('data/scenes/1904.json');
const epoch = `data/terrain/epochs/${scene.terrain_epoch}`;
const meta = read(`${epoch}/heightfield.json`);
if (meta.encoding !== 'int16') { console.error(`DRIFT — ${epoch} is ${meta.encoding}, not int16`); process.exit(2); }
const raw = new Int16Array(new Uint8Array(readFileSync(join(ROOT, epoch, meta.bin))).buffer);
/** terrain.js `Heightfield.sample`, inside the grid (the district lies well inside it). */
function surfaceHeight(e, n) {
  const gx = (e - meta.origin_e) / meta.cell_m; const gy = (n - meta.origin_n) / meta.cell_m;
  if (gx < 0 || gy < 0 || gx > meta.cols - 1 || gy > meta.rows - 1) return 0;
  const x0 = Math.min(Math.floor(gx), meta.cols - 2); const y0 = Math.min(Math.floor(gy), meta.rows - 2);
  const fx = gx - x0; const fy = gy - y0;
  const h = (c, r) => raw[r * meta.cols + c] * (meta.scale ?? 0.01) + (meta.offset ?? 0);
  return (h(x0, y0) * (1 - fx) + h(x0 + 1, y0) * fx) * (1 - fy) + (h(x0, y0 + 1) * (1 - fx) + h(x0 + 1, y0 + 1) * fx) * fy;
}

async function build(undo = null) {
  const { createStreetGrid } = await import(`${pathToFileURL(SRC).href}${undo ? `?undo=${undo}` : ''}`);
  const problems = [];
  const terrain = { surfaceHeight, setGroundCut: () => {} };
  const sg = await createStreetGrid({ dataBase: pathToFileURL(join(ROOT, 'data/')).href, sceneId: '1904', terrain, problems });
  if (problems.length || !sg.grid) throw new Error(`the grid did not build: ${problems.join('; ')}`);
  return sg;
}

/** Every roadway triangle (the carriageways and their seam overlays), binned in plan. */
function roadTriangles(sg) {
  const BIN = 4; const bins = new Map();
  for (const m of sg.group.children) {
    if (!m.isMesh || m.userData.cls !== 'carriageway') continue;
    const overlay = !!m.geometry.getAttribute('seam');
    const p = m.geometry.getAttribute('position');
    const spans = m.userData.spans ?? [];
    for (let t = 0; t < p.count / 3; t += 1) {
      const way = (spans.find((s) => t >= s.from && t < s.to)?.id ?? '').split('#')[0];
      const v = [0, 1, 2].map((k) => [p.getX(t * 3 + k), -p.getZ(t * 3 + k), p.getY(t * 3 + k)]);
      const box = [Math.min(v[0][0], v[1][0], v[2][0]), Math.min(v[0][1], v[1][1], v[2][1]),
        Math.max(v[0][0], v[1][0], v[2][0]), Math.max(v[0][1], v[1][1], v[2][1])];
      const tri = { paving: `${m.name}@${way}`, mesh: m.name, way, overlay, v, box };
      for (let i = Math.floor(box[0] / BIN); i <= Math.floor(box[2] / BIN); i += 1) {
        for (let j = Math.floor(box[1] / BIN); j <= Math.floor(box[3] / BIN); j += 1) {
          const k = `${i},${j}`;
          if (!bins.has(k)) bins.set(k, []);
          bins.get(k).push(tri);
        }
      }
    }
  }
  return { BIN, bins };
}

/** Height of `tri` over plan point (e, n), or null where the point is not strictly inside it. */
function heightIn(e, n, [a, b, c]) {
  const d = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]);
  if (Math.abs(d) < 1e-12) return null;
  const l1 = ((b[0] - e) * (c[1] - n) - (c[0] - e) * (b[1] - n)) / d;
  const l2 = ((c[0] - e) * (a[1] - n) - (a[0] - e) * (c[1] - n)) / d;
  const l3 = 1 - l1 - l2;
  if (l1 < 1e-6 || l2 < 1e-6 || l3 < 1e-6) return null;
  return l1 * a[2] + l2 * b[2] + l3 * c[2];
}

function measure(sg) {
  const { BIN, bins } = roadTriangles(sg);
  const faults = { overlay: new Map(), stack: new Map() };
  const note = (kind, key, gap, e, n) => {
    const f = faults[kind].get(key) ?? { points: 0, worst: Infinity, at: null };
    f.points += 1;
    if (gap < f.worst) { f.worst = gap; f.at = [e, n]; }
    faults[kind].set(key, f);
  };
  for (const [k, tris] of bins) {
    const [i, j] = k.split(',').map(Number);
    for (let e = i * BIN + SAMPLE_M / 2; e < (i + 1) * BIN; e += SAMPLE_M) {
      for (let n = j * BIN + SAMPLE_M / 2; n < (j + 1) * BIN; n += SAMPLE_M) {
        const hits = [];
        for (const t of tris) {
          if (e < t.box[0] || e > t.box[2] || n < t.box[1] || n > t.box[3]) continue;
          const h = heightIn(e, n, t.v);
          if (h !== null) hits.push({ t, h });
        }
        if (hits.length < 2) continue;
        const opaque = hits.filter((x) => !x.t.overlay);
        for (let a = 0; a < opaque.length; a += 1) {
          for (let b = a + 1; b < opaque.length; b += 1) {
            const [p, q] = [opaque[a], opaque[b]];
            if (p.t.paving === q.t.paving) continue;
            const gap = Math.abs(p.h - q.h);
            if (gap < MIN_GAP_M) note('stack', [p.t.paving, q.t.paving].sort().join(' | '), gap, e, n);
          }
        }
        if (!opaque.length) continue;
        const top = Math.max(...opaque.map((x) => x.h));
        for (const x of hits.filter((y) => y.t.overlay)) {
          const gap = x.h - top;
          if (gap < MIN_GAP_M) note('overlay', x.t.paving, gap, e, n);
        }
      }
    }
  }
  const say = (kind, what) => {
    const all = [...faults[kind]];
    if (!all.length) return [];
    const points = all.reduce((s, [, f]) => s + f.points, 0);
    return [`${points} points (every ${SAMPLE_M} m) where ${what}, nearest ${(Math.min(...all.map(([, f]) => f.worst)) * 1000).toFixed(1)} mm: `
      + all.sort((a, b) => a[1].worst - b[1].worst).slice(0, 4)
        .map(([key, f]) => `${key} at ${f.at.map((x) => x.toFixed(1)).join(',')} (${f.points})`).join('; ')];
  };
  return {
    overlay: say('overlay', `a seam overlay is not ${MIN_GAP_M * 1000} mm over the roadway it fades onto`),
    stack: say('stack', `two overlapping roadways are not ${MIN_GAP_M * 1000} mm apart`),
  };
}

let failed = 0;
const report = (name, faults) => {
  if (faults.length) { failed += 1; for (const f of faults) console.log(`FAIL ${name}: ${f}`); } else console.log(`ok   ${name}`);
};

if (!SELF_TEST) {
  const sg = await build();
  const r = measure(sg);
  report('overlay', r.overlay);
  report('stack', r.stack);
  console.log(failed ? `${failed} check(s) failed`
    : `the 1904 pavings: every seam overlay over its roadway and every overlapping roadway apart, by ${MIN_GAP_M * 1000} mm or more (${sg.census.roadLevels} road levels)`);
  process.exit(failed ? 1 : 0);
}

let silent = 0;
for (const name of Object.keys(UNDO)) {
  const faults = measure(await build(name))[name];
  if (faults.length) console.log(`fired ${name}: ${faults[0].slice(0, 200)}`);
  else { silent += 1; console.log(`SILENT ${name}: the check did not fire with its fix taken out — it proves nothing`); }
}
process.exit(silent ? 1 : 0);
