/**
 * WHAT ACTUALLY OCCUPIES THE TRIANGLE BUDGET AT ONE STAND, LAYER BY LAYER.
 *
 *   PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
 *     node tools/measure_stand_budget.mjs [--stand lake_at_canal]
 *                                         [--tiers full,balanced] [--source]
 *                                         [--only desktop|mobile|both] [--json f]
 *
 * The ceilings in `renderers/web/js/main.js` `DETAIL` have been raised four
 * times and breached five, and every one of those arguments was made against a
 * TOTAL. A total says the town is too expensive; it does not say what is
 * expensive, so each round has had to guess which lever to pull and then measure
 * whether the guess paid. This answers the other question, at the stand the gate
 * actually fails at.
 *
 * ## The method, and why it is the one this project already trusts
 *
 * Every layer is a named top-level group in the scene (`buildings.js` names its
 * group `structures`, `trees.js` names its `trees`, and so on). For each one:
 *
 *   1. **What it costs** — hide the group, let two frames pass, read
 *      `renderer.info.render`, restore. The delta is that layer's whole cost at
 *      this stand: its colour pass AND whatever it contributes to the sun's
 *      pass, because a hidden object is in neither.
 *   2. **What the sun costs on it** — put the group back, clear `castShadow` on
 *      every mesh in it, read again. That delta is the shadow pass alone, so the
 *      two readings separate "this layer is big" from "this layer is drawn
 *      twice".
 *
 * That is the same turn-it-off-and-read-it method `tools/measure_furniture_reach.mjs`
 * uses for the reach and T-0188 used to price the street fences, rather than a
 * model of the renderer that could be wrong in its own way. The RESIDUAL — the
 * baseline re-read at the end, against itself — is printed with the table, and
 * anything but zero there is the instrument's own noise.
 *
 * ## What the numbers mean, and what they do not
 *
 * The per-layer costs do not have to sum to the total and the printed residual
 * says by how much they miss. Two layers can occlude each other, so hiding
 * either one alone reveals what was behind it; and a batch is culled as a whole,
 * so a group whose chunks straddle the frustum edge is not a linear thing. The
 * sum is a sanity check, not an identity — read the ORDER and the magnitudes,
 * which is what a lever has to be chosen from.
 *
 * Defaults to the PUBLISHED mirror, for the reason every renderer measurement
 * here does: the source tree loads uncompressed masters and the site loads the
 * compressed derivatives. `--source` reads the working tree instead.
 *
 * This is a measurement and not a gate. `tools/smoke_renderer.mjs` holds the
 * ceilings; `tools/measure_detail_ceilings.mjs` reads them at all five stands.
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
const TIERS = (argAt('--tiers') || 'full,balanced').split(',').map((s) => s.trim());
const STAND_ID = argAt('--stand') || 'lake_at_canal';

/** T-0135's stands, by the ids `tools/smoke_renderer.mjs` gives them. */
const STANDS = {
  lake_at_canal: { kind: 'anchor', target: 'green_tree',
    label: 'Lake Street at Canal, east down the axis' },
  the_forks: { kind: 'anchor', target: 'forks', label: 'the forks, from Wolf Point' },
  from_above: { kind: 'anchor', target: 'from_above', label: 'the open aerial' },
  lake_and_market: { kind: 'anchor', target: 'lake_market', label: 'Lake and Market' },
  sauganash_26: { kind: 'frame', target: 'sauganash_hotel', distance: 26,
    label: 'the Sauganash at 26 m' },
};
const stand = STANDS[STAND_ID];
if (!stand) {
  console.error(`unknown stand '${STAND_ID}' — one of ${Object.keys(STANDS).join(', ')}`);
  process.exit(2);
}

/**
 * The named top-level groups, in the order they are added to the scene, with the
 * module that names each one. Read from the scene at run time as well, so a
 * layer added and not listed here still appears — it is named `(unlisted)` and
 * the run says so rather than quietly leaving it out of the budget.
 */
const KNOWN = {
  terrain: 'terrain.js — the ground and the water plane',
  structures: 'buildings.js — every committed roof',
  streets: 'streets.js — the road ribbons and their wear',
  enclosures: 'enclosures.js — fences, pickets, rails',
  'yard-ground': 'yards.js — fenced ground, gardens, yards',
  signage: 'signage.js — signboards and their posts',
  yard: 'yard.js — wagons, barrels, trade goods',
  frontage: 'frontage.js — plank walks, board crossings, street fences',
  wharves: 'wharves.js — dock decks and cribs',
  boats: 'boats.js — moored and beached hulls',
  flora: 'flora.js — the sward, forbs and shrubs',
  trees: 'trees.js — the timber, the treeline and planted stems',
};

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
const PORT = Number(process.env.BUDGET_PORT || 4199);
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
console.log(`serving ${ROOT} — ${wantSource ? 'source tree' : 'PUBLISHED mirror'}`);
console.log(`stand: ${stand.label}\n`);

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

  const measured = await page.evaluate(async ({ st, tiers }) => {
    const a = window.__chicago4d;
    const settle = () => new Promise((r) => requestAnimationFrame(
      () => requestAnimationFrame(r)));
    const groupsOf = () => a.scene3d.children
      .filter((o) => o.name && o.type === 'Group')
      .map((o) => o.name);
    const read = () => { const s = a.stats(); return { tris: s.triangles, calls: s.drawCalls }; };

    const started = a.detail;
    if (st.kind === 'frame') { a.setFly(false); a.frame(st.target, st.distance); }
    else a.goTo(st.target);
    await settle();

    const out = [];
    for (const tier of tiers) {
      await a.setDetail(tier);
      await settle();
      // Re-stand: setDetail can rebuild layers, and a rebuilt layer wants the
      // camera put back exactly where the reading is taken.
      if (st.kind === 'frame') { a.setFly(false); a.frame(st.target, st.distance); }
      else a.goTo(st.target);
      await settle();
      const base = read();
      const rows = [];
      for (const name of groupsOf()) {
        const g = a.scene3d.getObjectByName(name);
        if (!g) continue;
        // What the layer HOLDS, whether or not it is drawn: meshes and the
        // triangles resident in their geometry. The gap between this and the
        // drawn cost is what the frustum is saving.
        let meshes = 0;
        let heldTris = 0;
        let casters = 0;
        g.traverse((o) => {
          if (!o.isMesh) return;
          meshes += 1;
          if (o.castShadow) casters += 1;
          const geo = o.geometry;
          const n = geo?.index ? geo.index.count : (geo?.attributes?.position?.count ?? 0);
          heldTris += Math.floor(n / 3);
        });
        // 1. what it costs at all
        const wasVisible = g.visible;
        g.visible = false;
        await settle();
        const hidden = read();
        g.visible = wasVisible;
        await settle();
        // 2. what the sun costs on it
        const restore = [];
        g.traverse((o) => {
          if (o.isMesh && o.castShadow) { restore.push(o); o.castShadow = false; }
        });
        let noShadow = null;
        if (restore.length) {
          await settle();
          noShadow = read();
          for (const o of restore) o.castShadow = true;
          await settle();
        }
        rows.push({
          name, meshes, heldTris, casters,
          drawnTris: base.tris - hidden.tris,
          drawnCalls: base.calls - hidden.calls,
          shadowTris: noShadow ? base.tris - noShadow.tris : 0,
          shadowCalls: noShadow ? base.calls - noShadow.calls : 0,
        });
      }
      // THE WHOLE SUN, in one reading, so the per-layer sun column above has a
      // control. `renderer.shadowMap.enabled = false` skips the depth pass
      // outright, so the delta is every triangle the frame draws a second time
      // for the light — and the per-layer figures have to add up to it.
      const shadowWas = a.renderer.shadowMap.enabled;
      a.renderer.shadowMap.enabled = false;
      await settle();
      const noSun = read();
      a.renderer.shadowMap.enabled = shadowWas;
      await settle();
      // The residual: the baseline, re-read at the end, against itself.
      const again = read();
      out.push({ tier, ceiling: a.detailLevels[tier].triangles, base, rows,
                 sunTotal: { tris: base.tris - noSun.tris, calls: base.calls - noSun.calls },
                 residual: { tris: again.tris - base.tris, calls: again.calls - base.calls } });
    }
    await a.setDetail(started);
    return out;
  }, { st: stand, tiers: TIERS });

  passes.push({ viewport: vp.label, stand: stand.label, tiers: measured, errors });
  await page.close();
}
await browser.close();
server.close();

const num = (n) => n.toLocaleString('en-US');
for (const pass of passes) {
  console.log(`================  ${pass.viewport}  ·  ${pass.stand}  ================`);
  for (const t of pass.tiers) {
    const over = t.base.tris - t.ceiling;
    console.log(`\n${t.tier}: ${num(t.base.tris)} triangles, ${t.base.calls} calls, `
      + `ceiling ${num(t.ceiling)} — ${over > 0 ? `${num(over)} OVER` : `${num(-over)} clear`}`);
    console.log('   layer          drawn tris      %   calls   of which sun   held tris  meshes');
    const rows = t.rows.slice().sort((x, y) => y.drawnTris - x.drawnTris);
    for (const r of rows) {
      const pct = (100 * r.drawnTris / t.base.tris).toFixed(1);
      console.log(`   ${r.name.padEnd(13)} ${num(r.drawnTris).padStart(11)} `
        + `${pct.padStart(6)}   ${String(r.drawnCalls).padStart(5)} `
        + `${num(r.shadowTris).padStart(14)}   ${num(r.heldTris).padStart(9)} `
        + `${String(r.meshes).padStart(6)}`);
    }
    const sum = rows.reduce((n, r) => n + r.drawnTris, 0);
    console.log(`   ${'sum'.padEnd(13)} ${num(sum).padStart(11)} `
      + `${(100 * sum / t.base.tris).toFixed(1).padStart(6)}   `
      + `${String(rows.reduce((n, r) => n + r.drawnCalls, 0)).padStart(5)}`
      + `  (occlusion between layers is why this is not exactly the total)`);
    const sunSum = rows.reduce((n, r) => n + r.shadowTris, 0);
    console.log(`   the sun's own pass, whole frame: ${num(t.sunTotal.tris)} tris `
      + `(${(100 * t.sunTotal.tris / t.base.tris).toFixed(1)} % of the frame), `
      + `${t.sunTotal.calls} calls — per-layer column sums to ${num(sunSum)}`);
    console.log(`   residual (baseline against itself): `
      + `${t.residual.tris} tris, ${t.residual.calls} calls`);
    for (const r of rows) {
      if (KNOWN[r.name]) continue;
      console.log(`   NOTE: '${r.name}' is not in this tool's layer table — `
        + `add it so the next reader knows what it is`);
    }
  }
  if (pass.errors.length) console.log(`\nPAGE ERRORS: ${pass.errors.join('; ')}`);
}
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(passes, null, 2)}\n`);
