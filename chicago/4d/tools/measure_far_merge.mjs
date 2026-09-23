/**
 * WHAT THE FAR MERGE SAVES, AND WHAT IT COSTS — read off the same frame twice.
 *
 *   PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
 *     node tools/measure_far_merge.mjs [--tiers full,balanced,light]
 *                                      [--only desktop|mobile|both]
 *                                      [--source] [--json f]
 *
 * T-0146's instrument. The claim the merge makes is a narrow one and it has two
 * halves, so it is measured in one page load with the merge turned OFF and back
 * ON at each of T-0135's five stands:
 *
 *   * **calls go down** — the thing it is for;
 *   * **triangles do not move, at all** — the thing that makes it free. A merge
 *     is only allowed while its cluster is wholly inside the frustum, so the
 *     same triangles are submitted either way and the delta must be exactly 0.
 *     A non-zero triangle delta here is the bug, not a tolerance.
 *
 * Turning the merge off and reading the same frame is the method T-0150's reach
 * gate uses and for its reason: a figure taken from two different trees can be
 * satisfied by any unrelated layer getting cheaper, and this one has to be
 * attributable by construction. `a.setFarMerge(false)` is harness-only and is
 * never a visitor setting.
 *
 * Defaults to the PUBLISHED mirror for the reason every renderer measurement
 * here does — the site loads the compressed derivatives. `--source` reads the
 * working tree instead.
 *
 * This is a measurement and not a gate; `tools/smoke_renderer.mjs` holds the
 * ceilings.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH
      || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const argAt = (name) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
};
const wantSource = process.argv.includes('--source');
const jsonOut = argAt('--json');
const ONLY = argAt('--only') || 'desktop';
const TIERS = (argAt('--tiers') || 'full,balanced,light').split(',').map((s) => s.trim());

/** T-0135's stands, by the ids `tools/smoke_renderer.mjs` gives them. */
const STANDS = [
  { id: 'lake_at_canal', kind: 'anchor', target: 'green_tree',
    label: 'Lake Street at Canal, east down the axis' },
  { id: 'the_forks', kind: 'anchor', target: 'forks', label: 'the forks, from Wolf Point' },
  { id: 'from_above', kind: 'anchor', target: 'from_above', label: 'the open aerial' },
  { id: 'lake_and_market', kind: 'anchor', target: 'lake_market', label: 'Lake and Market' },
  { id: 'sauganash_26', kind: 'frame', target: 'sauganash_hotel', distance: 26,
    label: 'the Sauganash at 26 m' },
];

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

const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
if (!wantSource && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}
const PORT = Number(process.env.FAR_MERGE_PORT || 4207);
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));
console.log(`serving ${ROOT} — ${wantSource ? 'source tree' : 'PUBLISHED mirror'}\n`);

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const passes = [];
for (const vp of VIEWPORTS) {
  const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=1835`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 300_000 });

  const measured = await page.evaluate(async ({ stands, tiers }) => {
    const a = window.__chicago4d;
    const settle = () => new Promise((r) => requestAnimationFrame(
      () => requestAnimationFrame(r)));
    const read = () => { const s = a.stats(); return { tris: s.triangles, calls: s.drawCalls }; };
    const started = a.detail;
    const rows = [];
    for (const tier of tiers) {
      await a.setDetail(tier);
      await settle();
      for (const st of stands) {
        if (st.kind === 'frame') { a.setFly(false); a.frame(st.target, st.distance); }
        else a.goTo(st.target);
        await settle();
        const on = read();
        const state = a.farMerge;
        a.setFarMerge(false);
        await settle();
        const off = read();
        a.setFarMerge(true);
        await settle();
        // The baseline re-read at the end, against itself: anything but zero
        // here is the instrument's own noise and not a saving.
        const again = read();
        rows.push({
          tier, id: st.id, label: st.label,
          onTris: on.tris, onCalls: on.calls,
          offTris: off.tris, offCalls: off.calls,
          clusters: state.clusters, merged: state.merged, callsSaved: state.callsSaved,
          builtTris: state.builtTris,
          residualTris: again.tris - on.tris, residualCalls: again.calls - on.calls,
        });
      }
    }
    await a.setDetail(started);
    return { rows, config: a.farMerge };
  }, { stands: STANDS, tiers: TIERS });

  passes.push({ viewport: vp.label, ...measured, errors });
  await page.close();
}
await browser.close();
server.close();

const num = (n) => n.toLocaleString('en-US');
let bad = 0;
for (const pass of passes) {
  const c = pass.config;
  console.log(`================  ${pass.viewport}  ================`);
  console.log(`cluster ${c.clusterM} m · floor ${c.farM} m · at least ${c.minMembers} chunks `
    + `· ${c.clusters} cluster(s) over ${c.layers.join(', ')}\n`);
  console.log('   tier      stand                  calls off -> on   saved   tris off -> on   dtris');
  for (const r of pass.rows) {
    const dTris = r.onTris - r.offTris;
    if (dTris !== 0 || r.residualTris !== 0 || r.residualCalls !== 0) bad += 1;
    console.log(`   ${r.tier.padEnd(9)} ${r.id.padEnd(17)} `
      + `${String(r.offCalls).padStart(6)} -> ${String(r.onCalls).padEnd(5)} `
      + `${String(r.offCalls - r.onCalls).padStart(6)}   `
      + `${num(r.offTris).padStart(10)} -> ${num(r.onTris).padEnd(10)} `
      + `${String(dTris).padStart(6)}`);
  }
  const worstOn = pass.rows.reduce((x, y) => (y.onCalls > x.onCalls ? y : x));
  const worstOff = pass.rows.reduce((x, y) => (y.offCalls > x.offCalls ? y : x));
  console.log(`\n   worst stand for calls: ${worstOff.offCalls} at ${worstOff.id} without the `
    + `merge, ${worstOn.onCalls} at ${worstOn.id} with it`);
  console.log(`   merged buffers built this run: ${num(pass.rows.at(-1)?.builtTris ?? 0)} `
    + 'triangles of vertex data, kept once built');
  if (pass.errors.length) console.log(`\nPAGE ERRORS: ${pass.errors.join('; ')}`);
  if (pass.errors.length) bad += 1;
}
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(passes, null, 2)}\n`);
if (bad) {
  console.log(`\nREFUSED: ${bad} reading(s) moved a triangle or left a residual — `
    + 'the merge is only free while it draws the identical set.');
  process.exit(1);
}
console.log('\nevery stand: the triangle count is identical with the merge on and off.');
