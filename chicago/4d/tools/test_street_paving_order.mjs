#!/usr/bin/env node
/**
 * T-3389 — where two 1904 pavings overlap, the one on top is drawn last, and never by the
 * depth buffer's say.
 *
 * The owner, 2026-11-05, on screenshots at Prairie & 18th and Prairie & 20th: "pixely flashy
 * transitions when moving over any of the transitions between the paved and gravely surface".
 * T-3088 had laid every roadway and the seam overlay (T-2475) on one surface (vehicles and
 * horses stand on the drawn triangles; a horse's hooves must meet within 1 mm) and ranked
 * them by polygon offset alone. Two pavings triangulated differently over the 5 mm field
 * differ by up to 1.7 mm between their vertices, far past any offset in depth units, so the
 * fades dipped under their roadway and the strips a lower roadway runs on under a higher
 * one's edge (TUCK_M) lay in it: they fought for the depth buffer in moving blocks. Lifting
 * the roadways apart again fixed the picture and broke the horses' 1 mm footing, so instead
 * the roadways are ground decals (street-grid.js, ROAD_RENDER_ORDER):
 *
 *   decal   every roadway writes no depth and is drawn after every other opaque street
 *           surface (so a walk, a curb, a ramp holds the depth buffer over it); every fade
 *           is transparent and writes no depth (so it is drawn after every roadway);
 *   order   this builds the shipped grid headless on the real 1904 field (e1871_postfire,
 *           sampled as terrain.js samples it) and at every SAMPLE_M over every roadway,
 *           where two roadways of different pavings overlap, the one that must show (higher
 *           priority, then later in the grid, then the later piece) is drawn after the other:
 *           a higher renderOrder, never an equal one, which three would break by material
 *           and distance, differently as the eye moves.
 *
 *   node tools/test_street_paving_order.mjs [--self-test]
 *
 * --self-test loads street-grid.js with the roadways' depthWrite and then their renderOrder
 * taken back out (the hook edits the source as it loads) and requires each check to fire.
 * Exit 0 on pass, 1 on a failed check, 2 if the source no longer has the shape the self-test
 * edits (drift).
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

const UNDO = {
  decal: [['      mat.depthWrite = false;\n      mesh.renderOrder = ROAD_RENDER_ORDER', '      mesh.renderOrder = ROAD_RENDER_ORDER']],
  order: [['mesh.renderOrder = ROAD_RENDER_ORDER + buf.level * ROAD_LEVEL_ORDER;', '']],
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

const surfaces = read('data/street_surfaces/1904.json');
const grid = read('data/street_grid/1904.json');
const gridIndex = new Map((grid.carriageways ?? []).map((c, i) => [c.id, i]));
/** Which of two roadway pieces must show where they overlap: priority, then grid order, then piece. */
function rank(way) {
  const [id, piece] = way.split('#');
  return [surfaces.carriageways?.[id]?.priority ?? 0, gridIndex.get(id) ?? -1, Number(piece ?? 0)];
}
const above = (a, b) => { const x = rank(a); const y = rank(b); return x[0] - y[0] || x[1] - y[1] || x[2] - y[2]; };

function checkDecal(sg) {
  const faults = [];
  const meshes = sg.group.children.filter((m) => m.isMesh);
  const roads = meshes.filter((m) => m.userData.cls === 'carriageway' && !m.geometry.getAttribute('seam'));
  const fades = meshes.filter((m) => m.geometry.getAttribute('seam'));
  const others = meshes.filter((m) => !roads.includes(m) && !fades.includes(m) && !m.material.transparent);
  for (const m of roads) {
    if (m.material.depthWrite !== false) faults.push(`${m.name} writes depth`);
    if (m.material.transparent) faults.push(`${m.name} is in the transparent list`);
    const over = others.filter((o) => o.renderOrder >= m.renderOrder);
    if (over.length) faults.push(`${m.name} (order ${m.renderOrder}) is not drawn after ${over.slice(0, 2).map((o) => o.name).join(', ')}`);
  }
  for (const m of fades) if (!m.material.transparent || m.material.depthWrite !== false) faults.push(`${m.name}: a fade must be transparent and write no depth`);
  if (!roads.length || !fades.length) faults.push(`${roads.length} roadway draws and ${fades.length} fades: the grid did not lay its roadways`);
  return faults.length ? [`${faults.length} roadway draws are not ground decals: ${faults.slice(0, 4).join('; ')}`] : [];
}

/** Every opaque roadway triangle, binned in plan, with its mesh's draw order. */
function roadTriangles(sg) {
  const BIN = 4; const bins = new Map();
  for (const m of sg.group.children) {
    if (!m.isMesh || m.userData.cls !== 'carriageway' || m.geometry.getAttribute('seam')) continue;
    const p = m.geometry.getAttribute('position');
    const spans = m.userData.spans ?? [];
    for (let t = 0; t < p.count / 3; t += 1) {
      const way = spans.find((s) => t >= s.from && t < s.to)?.id ?? '';
      const v = [0, 1, 2].map((k) => [p.getX(t * 3 + k), -p.getZ(t * 3 + k)]);
      const box = [Math.min(v[0][0], v[1][0], v[2][0]), Math.min(v[0][1], v[1][1], v[2][1]),
        Math.max(v[0][0], v[1][0], v[2][0]), Math.max(v[0][1], v[1][1], v[2][1])];
      const tri = { mesh: m, paving: `${m.userData.material}@${way.split('#')[0]}`, way, v, box };
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

function inside(e, n, [a, b, c]) {
  const d = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]);
  if (Math.abs(d) < 1e-12) return false;
  const l1 = ((b[0] - e) * (c[1] - n) - (c[0] - e) * (b[1] - n)) / d;
  const l2 = ((c[0] - e) * (a[1] - n) - (a[0] - e) * (c[1] - n)) / d;
  return l1 > 1e-6 && l2 > 1e-6 && 1 - l1 - l2 > 1e-6;
}

function checkOrder(sg) {
  const { BIN, bins } = roadTriangles(sg);
  const faults = new Map();
  let overlaps = 0;
  for (const [k, tris] of bins) {
    const [i, j] = k.split(',').map(Number);
    for (let e = i * BIN + SAMPLE_M / 2; e < (i + 1) * BIN; e += SAMPLE_M) {
      for (let n = j * BIN + SAMPLE_M / 2; n < (j + 1) * BIN; n += SAMPLE_M) {
        const hits = tris.filter((t) => e >= t.box[0] && e <= t.box[2] && n >= t.box[1] && n <= t.box[3] && inside(e, n, t.v));
        for (let a = 0; a < hits.length; a += 1) {
          for (let b = a + 1; b < hits.length; b += 1) {
            let [lo, hi] = [hits[a], hits[b]];
            if (lo.paving === hi.paving) continue;
            if (above(lo.way, hi.way) > 0) [lo, hi] = [hi, lo];
            overlaps += 1;
            if (hi.mesh.renderOrder > lo.mesh.renderOrder) continue;
            const key = `${hi.paving} under ${lo.paving} (order ${hi.mesh.renderOrder} vs ${lo.mesh.renderOrder})`;
            const f = faults.get(key) ?? { points: 0, at: [e, n] };
            f.points += 1;
            faults.set(key, f);
          }
        }
      }
    }
  }
  if (!overlaps) return ['no two pavings overlap anywhere: the sampling found no crossing to check'];
  if (!faults.size) return [];
  const points = [...faults.values()].reduce((s, f) => s + f.points, 0);
  return [`${points} of ${overlaps} overlap points (every ${SAMPLE_M} m) where the paving that must show is not drawn after the other: `
    + [...faults].slice(0, 4).map(([key, f]) => `${key} at ${f.at.map((x) => x.toFixed(1)).join(',')} (${f.points})`).join('; ')];
}

let failed = 0;
const report = (name, faults) => {
  if (faults.length) { failed += 1; for (const f of faults) console.log(`FAIL ${name}: ${f}`); } else console.log(`ok   ${name}`);
};

if (!SELF_TEST) {
  const sg = await build();
  report('decal', checkDecal(sg));
  report('order', checkOrder(sg));
  console.log(failed ? `${failed} check(s) failed`
    : `the 1904 pavings: every roadway a ground decal drawn in its stacking order (${sg.census.roadLevels} levels), every fade over them`);
  process.exit(failed ? 1 : 0);
}

const checks = { decal: checkDecal, order: checkOrder };
let silent = 0;
for (const name of Object.keys(UNDO)) {
  const faults = checks[name](await build(name));
  if (faults.length) console.log(`fired ${name}: ${faults[0].slice(0, 200)}`);
  else { silent += 1; console.log(`SILENT ${name}: the check did not fire with its fix taken out — it proves nothing`); }
}
process.exit(silent ? 1 : 0);
