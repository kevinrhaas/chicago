#!/usr/bin/env node
/**
 * T-3233 — no hard straight line on the 1904 street ground.
 *
 * The owner, 2026-10-28, on four screenshots of the 1904 streets: *"we dont want harsh
 * linear transitions like that on the ground and grass"*. Each had a cause at its source,
 * and each is held here so it cannot come back:
 *
 *   margin   the one-foot margin inside the walk was drawn in the parkway's turf, a straight
 *            strip of another green between every lawn and the walk and over the end of every
 *            house's front walk. It is the lot's own ground now: no turf span `…|margin`.
 *   levels   a band vertex lying exactly on the curb line (the roadway's edge) could fall
 *            outside every band in the parity test and take the ROADWAY's level, so the curb's
 *            top ran down into the gutter (1,126 triangles on 28 faces). Every walk, parkway
 *            and curb vertex now stands at its sidewalk space's level; the corner crossings'
 *            slabs (`xf:`/`xr:`, T-3200/T-3231) are not this test's.
 *   holes    where a wider segment of a street runs on through a crossing beside a narrower
 *            one (Prairie 16th-18th past 18th-20th by 0.35 m a side), the strip left beside
 *            the narrower one was dropped as a stub on BOTH sides of the crossing, though on
 *            the near side it lies inside the wider roadway: a 0.35 m hole down the gutter at
 *            four corners, where the cut-away ground showed as a flat pale or teal strip. Every
 *            point of every roadway outside the sidewalk spaces is paved now, sampled every
 *            SAMPLE_M.
 *   seams    where one roadway's paving meets another's (18th Street's macadam at Prairie's
 *            asphalt), the edge is a worn fade, not a cut: every cut a higher roadway makes in a
 *            lower one carries a seam overlay (T-2475) —
 *   ends     — and the fade wears out at the two ends of its run as well, where the cross
 *            street's own curb line runs on over the avenue's gutter; it used to stop there on
 *            a straight cut, the crossing's paving square against the asphalt.
 *   yards    a K14 yard laid the kit's turf sheet over its front lawn, which met the app's own
 *            ground beside it (the side yard, the margin) in a straight line of another green
 *            (1801 Prairie's side yard). No yard lays it: the app's ground is the lawn.
 *
 * HOW. The shipped renderers/web/js/street-grid.js is IMPORTED, not sliced: a module hook
 * resolves `three` to the vendored copy, `fetch` reads data/, the terrain is flat and there is
 * no canvas (so no ground cut), and the whole 1904 grid is built as the browser builds it.
 *
 *   node tools/test_street_ground_seams.mjs [--self-test]
 *
 * --self-test rebuilds the grid from the same source with each fix taken back out (the hook
 * edits the source text as it loads), and a yard record with `lawn: turf`, and requires every
 * check to fire. Exit 0 on pass; 1 on a failed check; 2 if the source no longer has the shape
 * the self-test edits (drift).
 */
import { readFileSync, readdirSync } from 'node:fs';
import { register } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const SRC = join(ROOT, 'renderers/web/js/street-grid.js');
const THREE_DIR = pathToFileURL(join(ROOT, 'renderers/web/vendor/three-0.185.1/')).href;
const SELF_TEST = process.argv.includes('--self-test');
const SAMPLE_M = 0.25;

/** Each fix, as the text that makes it and the text it replaced (for --self-test). */
const UNDO = {
  levels: [['nearPolygon(e, n, q, BAND_EDGE_M)', 'pointInPolygon(e, n, q)']],
  holes: [[' || !onSidewalk(x)', '']],
  margin: [
    ["if (band === 'margin') {", "if (band === 'margin' && false) {"],
    ['const CLASSES = {\n', "const CLASSES = {\n  margin: { lift: 0.05, colour: 0x7c8a66, offset: -10, tier: 'inferred' },\n"],
  ],
  seams: [['w.margins.push({ poly: strip, frame: it.frame, edge: [p0, p1] });', '']],
  ends: [['seamEnds: m.run, ', '']],
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
const grid = read('data/street_grid/1904.json');
const section = read('data/street_section/1904.json');
const ROAD = section.section?.road_m;
if (!(ROAD < 0)) { console.error('DRIFT — data/street_section/1904.json has no road_m below the field'); process.exit(2); }

function pointInPolygon(e, n, poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i, i += 1) {
    const [ei, ni] = poly[i]; const [ej, nj] = poly[j];
    if ((ni > n) !== (nj > n) && e < ((ej - ei) * (n - ni)) / (nj - ni) + ei) inside = !inside;
  }
  return inside;
}
function nearEdge(e, n, poly, eps) {
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i, i += 1) {
    const [ax, ay] = poly[j]; const [bx, by] = poly[i];
    const dx = bx - ax; const dy = by - ay; const L2 = dx * dx + dy * dy || 1;
    const t = Math.max(0, Math.min(1, ((e - ax) * dx + (n - ay) * dy) / L2));
    if (Math.hypot(e - ax - t * dx, n - ay - t * dy) <= eps) return true;
  }
  return false;
}
const bbox = (pts) => pts.reduce((b, [e, n]) => [Math.min(b[0], e), Math.min(b[1], n), Math.max(b[2], e), Math.max(b[3], n)],
  [Infinity, Infinity, -Infinity, -Infinity]);

/** Every sidewalk-space polygon (each face's bands, the margin included). */
const sidewalk = grid.faces.flatMap((f) => Object.values(f.bands ?? {}).flat()).map((q) => ({ q, b: bbox(q) }));
const inSidewalk = (e, n) => sidewalk.some(({ q, b }) => e >= b[0] - 0.05 && e <= b[2] + 0.05 && n >= b[1] - 0.05
  && n <= b[3] + 0.05 && (pointInPolygon(e, n, q) || nearEdge(e, n, q, 0.05)));

async function build(undo = null) {
  const { createStreetGrid } = await import(`${pathToFileURL(SRC).href}${undo ? `?undo=${undo}` : ''}`);
  const problems = [];
  const terrain = { surfaceHeight: () => 0, setGroundCut: () => {} };
  const sg = await createStreetGrid({ dataBase: pathToFileURL(join(ROOT, 'data/')).href, sceneId: '1904', terrain, problems });
  if (problems.length || !sg.grid) throw new Error(`the grid did not build: ${problems.join('; ')}`);
  return sg;
}

/** The plan triangles of every mesh, with the span each belongs to. */
function triangles(sg) {
  const out = [];
  for (const m of sg.group.children) {
    if (!m.isMesh) continue;
    const p = m.geometry.getAttribute('position');
    const spans = m.userData.spans ?? [];
    for (let t = 0; t < p.count / 3; t += 1) {
      const span = spans.find((s) => t >= s.from && t < s.to)?.id ?? '';
      const v = [0, 1, 2].map((k) => [p.getX(t * 3 + k), -p.getZ(t * 3 + k), p.getY(t * 3 + k)]);
      out.push({ mesh: m.name, cls: m.userData.cls, span, v });
    }
  }
  return out;
}

function checkMargin(tris) {
  const bad = tris.filter((t) => t.span.endsWith('|margin'));
  return bad.length ? [`${bad.length} triangles of turf drawn in the one-foot margin (${[...new Set(bad.map((t) => t.span))].slice(0, 3).join(', ')})`] : [];
}

function checkLevels(tris) {
  // The sidewalk space's lowest point is its curb, a fall of about 0.12 m; the roadway is
  // ROAD (about 0.29 m) down. Half way is a line no band vertex of a face may cross.
  const floor = ROAD / 2;
  const bad = tris.filter((t) => ['walk', 'parkway', 'curb'].includes(t.cls) && !/^x[fr]:/.test(t.span)
    && !/^street-grid-(curb-face|carriage-posts)/.test(t.mesh) && t.v.some((p) => p[2] < floor));
  if (!bad.length) return [];
  const faces = new Map();
  for (const t of bad) faces.set(t.span, (faces.get(t.span) ?? 0) + 1);
  return [`${bad.length} band triangles on ${faces.size} faces have a vertex at the roadway's level (below ${floor.toFixed(3)} m): `
    + [...faces].slice(0, 4).map(([k, v]) => `${k} ${v}`).join(', ')];
}

function checkHoles(tris) {
  const paving = tris.filter((t) => t.cls === 'carriageway' && !/^street-grid-carriageway-[a-z_]+$/.test(t.mesh)
    || /^x[fr]:/.test(t.span) || t.cls === 'alley');
  const BIN = 4;
  const bins = new Map();
  for (const t of paving) {
    const b = bbox(t.v);
    for (let i = Math.floor(b[0] / BIN); i <= Math.floor(b[2] / BIN); i += 1) {
      for (let j = Math.floor(b[1] / BIN); j <= Math.floor(b[3] / BIN); j += 1) {
        const k = `${i},${j}`;
        if (!bins.has(k)) bins.set(k, []);
        bins.get(k).push(t.v);
      }
    }
  }
  const inTri = (e, n, [a, b, c]) => {
    const d = (p, q, r) => (p[0] - r[0]) * (q[1] - r[1]) - (q[0] - r[0]) * (p[1] - r[1]);
    const d1 = d([e, n], a, b); const d2 = d([e, n], b, c); const d3 = d([e, n], c, a);
    return !(((d1 < -1e-9) || (d2 < -1e-9) || (d3 < -1e-9)) && ((d1 > 1e-9) || (d2 > 1e-9) || (d3 > 1e-9)));
  };
  const holes = [];
  for (const c of grid.carriageways) {
    for (const q of c.quads_local_m ?? []) {
      const b = bbox(q);
      for (let e = Math.ceil(b[0] / SAMPLE_M) * SAMPLE_M; e <= b[2]; e += SAMPLE_M) {
        for (let n = Math.ceil(b[1] / SAMPLE_M) * SAMPLE_M; n <= b[3]; n += SAMPLE_M) {
          if (!pointInPolygon(e, n, q) || nearEdge(e, n, q, 0.05) || inSidewalk(e, n)) continue;
          const cands = bins.get(`${Math.floor(e / BIN)},${Math.floor(n / BIN)}`) ?? [];
          if (!cands.some((v) => inTri(e, n, v))) holes.push([c.id, e, n]);
        }
      }
    }
  }
  if (!holes.length) return [];
  const where = new Map();
  for (const [id, e, n] of holes) {
    const k = `${id} near ${Math.round(e)},${Math.round(n)}`;
    where.set(k, (where.get(k) ?? 0) + 1);
  }
  return [`${holes.length} points of roadway (every ${SAMPLE_M} m) are not paved — a hole down to the cut-away ground: `
    + [...where].slice(0, 6).map(([k, v]) => `${k} (${v})`).join(', ')];
}

function checkSeams(sg) {
  // Every cut a higher roadway makes in a lower one keeps a fading margin over it (T-2475).
  const { cuts = 0, seams = 0 } = sg.census;
  return cuts > 0 && seams >= cuts ? [] : [`${seams} seam overlays for ${cuts} cuts: a roadway's paving meets another's in a cut line`];
}

function checkEnds(sg) {
  // ...and each run of fade wears out at its two ends too, where the lower roadway's own side
  // line crosses the higher one: every overlay carries how far each point is from its run's
  // ends, some of its points stand at an end, and its shader rounds the fade off there.
  const faults = [];
  for (const m of sg.group.children) {
    if (!m.isMesh || !m.geometry.getAttribute('seam')) continue;
    const se = m.geometry.getAttribute('seamEnd');
    let atEnd = 0;
    for (let i = 0; se && i < se.count; i += 1) if (Math.min(se.getX(i), se.getY(i)) < 0.01) atEnd += 1;
    const shader = { uniforms: {}, vertexShader: '#include <begin_vertex>', fragmentShader: '#include <color_fragment>\n#include <alphamap_fragment>' };
    m.material.onBeforeCompile(shader);
    const rounds = /vChiSeamEnd/.test(shader.fragmentShader) && /attribute vec2 seamEnd/.test(shader.vertexShader);
    if (!se || !atEnd || !rounds) faults.push(`${m.name}: ${!se ? 'no seamEnd attribute' : !atEnd ? 'no point at either end of its run' : 'its shader does not round the fade off at the ends'}`);
  }
  return faults.length ? [`${faults.length} seam overlays stop on a straight cut at their ends: ${faults.slice(0, 3).join('; ')}`] : [];
}

function checkYards(records) {
  const bad = [];
  for (const [id, d] of records) {
    for (const ph of d.phases ?? []) {
      if (ph.form?.yard?.value?.lawn === 'turf') bad.push(`${id}.${ph.id}`);
    }
  }
  return bad.length ? [`${bad.length} yards lay the kit's turf sheet over the app's own ground: ${bad.slice(0, 4).join(', ')}`] : [];
}
const structures = readdirSync(join(ROOT, 'data/structures')).filter((f) => f.endsWith('.json'))
  .map((f) => [f.slice(0, -5), read(`data/structures/${f}`)]);

let failed = 0;
const report = (name, faults) => {
  if (faults.length) { failed += 1; for (const f of faults) console.log(`FAIL ${name}: ${f}`); } else console.log(`ok   ${name}`);
};

if (!SELF_TEST) {
  const sg = await build();
  const tris = triangles(sg);
  report('margin', checkMargin(tris));
  report('levels', checkLevels(tris));
  report('holes', checkHoles(tris));
  report('seams', checkSeams(sg));
  report('ends', checkEnds(sg));
  report('yards', checkYards(structures));
  console.log(failed ? `${failed} check(s) failed` : `the 1904 street ground: no turf margin, no dropped band, no hole, every cut faded, no yard turf (${tris.length} triangles)`);
  process.exit(failed ? 1 : 0);
}

// --self-test: each check must fire on the source with its fix taken out.
const fires = {
  margin: async () => checkMargin(triangles(await build('margin'))),
  levels: async () => checkLevels(triangles(await build('levels'))),
  holes: async () => checkHoles(triangles(await build('holes'))),
  seams: async () => checkSeams(await build('seams')),
  ends: async () => checkEnds(await build('ends')),
  yards: async () => checkYards([['a_yard_with_turf', { phases: [{ id: 'p', form: { yard: { value: { lawn: 'turf' } } } }] }]]),
};
let silent = 0;
for (const [name, run] of Object.entries(fires)) {
  const faults = await run();
  if (faults.length) console.log(`fired ${name}: ${faults[0].slice(0, 160)}`);
  else { silent += 1; console.log(`SILENT ${name}: the check did not fire with its fix taken out — it proves nothing`); }
}
process.exit(silent ? 1 : 0);
