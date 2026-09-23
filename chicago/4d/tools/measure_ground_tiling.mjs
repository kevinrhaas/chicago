/**
 * WHAT THE GROUND'S CULLING GRID COSTS, ON THE FIELD IT NOW COVERS (T-0466).
 *
 *   PW_EXECUTABLE=/path/to/chrome \
 *     node tools/measure_ground_tiling.mjs [--only desktop|mobile|both]
 *                                          [--candidates 12x3,derived,...]
 *                                          [--source] [--json out.json]
 *   node tools/measure_ground_tiling.mjs --self-test    the rule's own assertions
 *   node tools/measure_ground_tiling.mjs --check        the committed reading
 *
 * ## The question
 *
 * `renderers/web/js/terrain.js` used to cut the ground on the literals 12 × 3, and
 * those two numbers were a measurement of ONE box — 2,020 m east-west by 800 m
 * north-south, long axis east-west, measured end to end through the smoke. The
 * southern field (T-0464) makes the box 2,020 × 4,920 m: deeper than it is wide,
 * long axis north-south, and the literals cannot see the difference. Three rows
 * over 4,920 m is a tile 1,640 m deep — a strip that reaches from the walker's feet
 * to the far end of the town, intersects the frustum from anywhere on it, and can
 * therefore never be culled. That is the fixed assumption this ticket was opened
 * against, and the answer has to be a RULE over the box rather than a better pair
 * of literals, because the box is going to move again.
 *
 * ## The method
 *
 * The same instrument `tools/measure_detail_ceilings.mjs` uses, and for the same
 * reason: serve a tree, boot the real renderer on it, drive it with the same
 * `__chicago4d` handle the gate drives, and read `stats()` — triangles and draw
 * calls as three.js itself counts them, not a model of the renderer that could be
 * wrong in its own way. What is added here is the CANDIDATE: the served copy of
 * `js/terrain.js` is rewritten in flight so `groundTileGrid()` returns a forced
 * grid, which is how one tree can be read at several tilings without committing
 * any of them. The production file is never touched, and `derived` is the
 * unpatched rule as committed.
 *
 * Every candidate gets its own page, because an ES module is cached per context
 * and a reload would re-use the first candidate's terrain.js.
 *
 * ## The stands
 *
 * The five downtown stands are COPIED from `tools/smoke_renderer.mjs` STANDS, the
 * way measure_detail_ceilings.mjs copies them and for the same reason. The four
 * south stands are NOT anchors — there are none south of the town yet, that is
 * T-0467 — so they are given as poses in local ENU metres, spread down the new
 * field to 3.2 km south of the datum, plus one aerial over it. A tiling measured
 * only downtown would be measured on the quarter of the box that did not change.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT4D = path.resolve(HERE, '..');
const argAt = (name) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
};
const wantSource = process.argv.includes('--source');
const jsonOut = argAt('--json');
const ONLY = argAt('--only') || 'desktop';
/** Which scene-detail tiers to read. Every boot of a tier costs a scene rebuild, so
 *  the default is the one the budget binds at; `--tiers light,balanced,full` reads all. */
const TIERS = (argAt('--tiers') || 'full').split(',').map((s) => s.trim()).filter(Boolean);
const YEAR = process.env.TILING_YEAR || '1835';
const READING = path.join(ROOT4D, 'data/render/ground_detail_lod.json');

/** The committed rule, re-implemented here so `--self-test` can hold the source
 *  file to it without a bundler. Kept identical to terrain.js groundTileGrid(). */
function grid(spanX, spanZ, targetM = 240) {
  if (!(spanX > 0) || !(spanZ > 0)) return { cols: 1, rows: 1 };
  return {
    cols: Math.max(1, Math.ceil(spanX / targetM)),
    rows: Math.max(1, Math.ceil(spanZ / targetM)),
  };
}

/** The source file's own rule, read out of terrain.js, so the two cannot drift. */
function committedRuleText() {
  const s = fs.readFileSync(path.join(ROOT4D, 'renderers/web/js/terrain.js'), 'utf8');
  const m = s.match(/export function groundTileGrid\([\s\S]*?\n}/);
  if (!m) throw new Error('groundTileGrid() not found in renderers/web/js/terrain.js');
  return m[0];
}

function selfTest() {
  const fails = [];
  const eq = (what, got, want) => {
    if (JSON.stringify(got) !== JSON.stringify(want)) {
      fails.push(`${what}: got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`);
    }
  };
  // 1. No side is wider than the measured 240 m target.
  eq('the former 2,020 x 800 m box', grid(2020, 800), { cols: 9, rows: 4 });
  // 2. It TRANSPOSES with the box; neither compass axis is privileged.
  eq('the same box, turned', grid(800, 2020), { cols: 4, rows: 9 });
  // 3. The committed mesh is the 31 x 43 grid the closing reading names.
  eq('the committed 7,340 x 10,240 m mesh', grid(7339.6875, 10239.6875),
    { cols: 31, rows: 43 });
  // 4. A square box is a square grid.
  eq('a square box', grid(1000, 1000), { cols: 5, rows: 5 });
  // 5. Degenerate boxes do not divide by zero or return a zero grid.
  eq('a zero-width box', grid(0, 800), { cols: 1, rows: 1 });
  // 6. The source file still carries the rule this file re-implements.
  const src = committedRuleText();
  for (const frag of ['Math.ceil(spanX / targetM)', 'Math.ceil(spanZ / targetM)']) {
    if (!src.includes(frag)) fails.push(`terrain.js groundTileGrid() no longer carries \`${frag}\``);
  }
  // 7. tileGround() must ASK the rule rather than carry literals again.
  const t = fs.readFileSync(path.join(ROOT4D, 'renderers/web/js/terrain.js'), 'utf8');
  if (!t.includes('tileGround(ground, groundTileGrid)')) {
    fails.push('terrain.js no longer passes groundTileGrid to tileGround()');
  }
  if (/GROUND_TILE_COLS|GROUND_TILE_ROWS/.test(t)) {
    fails.push('terrain.js has fixed GROUND_TILE_COLS/ROWS literals again');
  }
  for (const frag of ['const GROUND_TILE_TARGET_M = 240;',
                      'const GROUND_BASE_STEP = 6;',
                      'const GROUND_DETAIL_REACH_M = 600;',
                      'gridGeometry(heightfield, GROUND_BASE_STEP)',
                      'heightfield.contains(e, n)',
                      'dx * dx + dy * dy + dz * dz > reach * reach']) {
    if (!t.includes(frag)) fails.push(`terrain.js no longer carries the T-1245 rule \`${frag}\``);
  }
  return fails;
}

function check() {
  const fails = selfTest();
  if (!fs.existsSync(READING)) {
    fails.push(`no committed reading at ${path.relative(ROOT4D, READING)}`);
    return fails;
  }
  const r = JSON.parse(fs.readFileSync(READING, 'utf8'));
  // 1. The reading must be a reading of THIS rule on the committed mesh.
  const meta = JSON.parse(fs.readFileSync(path.join(ROOT4D,
    'data/terrain/epochs/e1834_harbor_cut/heightfield.json'), 'utf8'));
  const want = grid(7339.6875, 10239.6875, r.chosen.tile_target_m);
  if (r.chosen.grid_on_committed_mesh !== `${want.cols}x${want.rows}`) {
    fails.push(`the closing reading names ${r.chosen.grid_on_committed_mesh}, `
      + `but the rule gives ${want.cols}x${want.rows}`);
  }
  if (meta.cell_m !== r.chosen.navigation_cell_m) {
    fails.push(`the closing reading says navigation remains at ${r.chosen.navigation_cell_m} m, `
      + `but the heightfield is ${meta.cell_m} m`);
  }
  // 2. The rule's constants must still be the ones the reading states.
  const src = fs.readFileSync(path.join(ROOT4D, 'renderers/web/js/terrain.js'), 'utf8');
  for (const [what, literal] of [
    ['tile target', `const GROUND_TILE_TARGET_M = ${r.chosen.tile_target_m};`],
    ['base step', `const GROUND_BASE_STEP = ${r.chosen.base_sample_step};`],
    ['detail reach', `const GROUND_DETAIL_REACH_M = ${r.chosen.detail_reach_m};`],
  ]) {
    if (!src.includes(literal)) fails.push(`terrain.js no longer sets the ${what} in the closing reading (\`${literal}\`)`);
  }
  // 3. Both viewports and all three tiers close under their unchanged ceilings.
  for (const [vp, levels] of Object.entries(r.results)) {
    for (const [level, seen] of Object.entries(levels)) {
      if (seen.worst_triangles > r.ceilings[level]) {
        fails.push(`${vp} ${level}: ${seen.worst_triangles} triangles over ${r.ceilings[level]}`);
      }
      if (seen.worst_calls > r.ceilings.draw_calls) {
        fails.push(`${vp} ${level}: ${seen.worst_calls} calls over ${r.ceilings.draw_calls}`);
      }
    }
  }
  // 4. Grid refinement alone was measured and refused, rather than assumed.
  const rejected = r.rejected_grid_only_candidates ?? [];
  if (!rejected.length || rejected.at(-1).lake_at_canal_triangles <= r.ceilings.light) {
    fails.push('the closing reading no longer demonstrates that grid refinement alone stayed over light');
  }
  return fails;
}

if (process.argv.includes('--self-test') || process.argv.includes('--check')) {
  const fails = process.argv.includes('--check') ? check() : selfTest();
  if (fails.length) {
    for (const f of fails) console.error(`  FAIL  ${f}`);
    console.error(`${fails.length} assertion(s) failed`);
    process.exit(1);
  }
  console.log(process.argv.includes('--check')
    ? 'the committed ground-tiling reading still answers for the committed rule'
    : "the ground-tiling rule's own assertions hold");
  process.exit(0);
}

// ---------------------------------------------------------------- measurement //

const DOWNTOWN = [
  { id: 'lake_at_canal', kind: 'anchor', target: 'green_tree',
    label: 'Lake Street at Canal, east down the axis' },
  { id: 'the_forks', kind: 'anchor', target: 'forks', label: 'the forks, from Wolf Point' },
  { id: 'lake_and_market', kind: 'anchor', target: 'lake_market', label: 'Lake and Market' },
  { id: 'from_above', kind: 'anchor', target: 'from_above', label: 'the open aerial' },
];
const SOUTH = [
  { id: 'south_branch_below_town', kind: 'pose', label: 'the South Branch below the town, looking south',
    pose: { local_e: 250, local_n: -700, yaw_deg: 180 } },
  { id: 'mid_field_looking_north', kind: 'pose', label: 'mid-field, looking back at the town',
    pose: { local_e: 800, local_n: -1800, yaw_deg: 0 } },
  { id: 'south_end_looking_north', kind: 'pose', label: 'the south end of the field, looking north',
    pose: { local_e: 700, local_n: -3200, yaw_deg: 0 } },
  { id: 'above_south_field', kind: 'pose', label: 'from the air over the southern field',
    pose: { local_e: 600, local_n: -1600, yaw_deg: 0, altitude_m: 700, pitch_deg: -45 } },
];
const STANDS = [...DOWNTOWN, ...SOUTH];

const CANDIDATES = (argAt('--candidates') || 'derived,12x3,6x6,12x12,8x18')
  .split(',').map((s) => s.trim()).filter(Boolean)
  .map((id) => {
    if (id === 'derived') return { id, forced: null, label: 'the committed rule' };
    const m = id.match(/^(\d+)x(\d+)$/);
    if (!m) throw new Error(`candidate must be "derived" or COLSxROWS, got ${id}`);
    return { id, forced: { cols: Number(m[1]), rows: Number(m[2]) }, label: `${m[1]} x ${m[2]}, forced` };
  });

const VIEWPORTS = [
  { label: 'desktop 1280x800', width: 1280, height: 800 },
  { label: 'mobile 390x780', width: 390, height: 780 },
].filter((v) => ONLY === 'both' || v.label.startsWith(ONLY));

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
};
const ANCHOR = 'if (!(spanX > 0) || !(spanZ > 0)) return { cols: 1, rows: 1 };';

const ROOT = wantSource ? ROOT4D : path.resolve(ROOT4D, '../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
if (!wantSource && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}

let forced = null;   // the candidate the server is currently serving
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end(`not found: ${url}`);
    return;
  }
  if (forced && /\/js\/terrain\.js$/.test(url)) {
    let body = fs.readFileSync(file, 'utf8');
    if (!body.includes(ANCHOR)) {
      res.writeHead(500, { 'content-type': 'text/plain' });
      res.end('terrain.js no longer carries the patch anchor');
      return;
    }
    body = body.replace(ANCHOR, `return { cols: ${forced.cols}, rows: ${forced.rows} };`);
    res.writeHead(200, { 'content-type': 'text/javascript' });
    res.end(body);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

let chromium;
try { ({ chromium } = await import('playwright')); }
catch { ({ chromium } = await import(path.resolve(ROOT4D, '../../../node_modules/playwright/index.js'))); }

const PORT = Number(process.env.TILING_PORT || 4211);
await new Promise((r) => server.listen(PORT, r));
const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});

const out = [];
for (const vp of VIEWPORTS) {
  const perCandidate = [];
  for (const cand of CANDIDATES) {
    forced = cand.forced;
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.addInitScript((t) => { window.__tilingTiers = t; }, TIERS);
    await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 300_000 });
    const read = await page.evaluate(async (stands) => {
      const a = window.__chicago4d;
      const settle = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      const tiling = a.groundTiling ? a.groundTiling() : null;
      const started = a.detail;
      const tiers = {};
      let atStands = [];
      const wanted = window.__tilingTiers || a.detailOrder;
      for (const level of a.detailOrder.filter((l) => wanted.includes(l))) {
        await a.setDetail(level);
        await settle();
        const rows = [];
        for (const st of stands) {
          if (st.kind === 'anchor') a.goTo(st.target);
          else { a.setFly(typeof st.pose.altitude_m === 'number'); a.walker.teleport(st.pose); }
          await settle();
          const r = a.stats();
          rows.push({ id: st.id, label: st.label, tris: r.triangles, calls: r.drawCalls });
        }
        tiers[level] = {
          ceiling: a.detailLevels[level].triangles,
          worst_triangles: Math.max(...rows.map((r) => r.tris)),
          worst_calls: Math.max(...rows.map((r) => r.calls)),
        };
        if (level === wanted[wanted.length - 1]) atStands = rows;
      }
      await a.setDetail(started);
      return { tiling, tiers, atStands, budget: a.budget };
    }, STANDS);
    perCandidate.push({ id: cand.id, label: cand.label, ...read, errors });
    await page.close();
    const t = read.tiling;
    console.log(`${vp.label}  ${cand.id.padEnd(9)}  grid ${t ? `${t.cols} x ${t.rows}` : '?'}`
      + `  worst ${read.tiers[TIERS[TIERS.length - 1]].worst_triangles.toLocaleString('en-US').padStart(10)}`
      + `  worst calls ${String(read.tiers[TIERS[TIERS.length - 1]].worst_calls).padStart(4)}`
      + (errors.length ? `  PAGE ERRORS: ${errors.join('; ')}` : ''));
  }
  out.push({ viewport: vp.label, candidates: perCandidate });
}
await browser.close();
server.close();

console.log('');
for (const vp of out) {
  console.log(`================  ${vp.viewport}  ================`);
  console.log('   stand                                              '
    + CANDIDATES.map((c) => c.id.padStart(16)).join(''));
  for (const st of STANDS) {
    const cells = CANDIDATES.map((c) => {
      const row = vp.candidates.find((x) => x.id === c.id).atStands.find((r) => r.id === st.id);
      return `${row.tris.toLocaleString('en-US')}/${row.calls}`.padStart(16);
    });
    console.log(`   ${st.label.padEnd(50)}${cells.join('')}`);
  }
}
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(out, null, 2)}\n`);
