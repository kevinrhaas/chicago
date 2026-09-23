/**
 * T-0056 — WHAT THE SCENE-DETAIL CONTROL COSTS THE FENCES, LAYER BY LEVEL.
 *
 *   node tools/measure_enclosure_detail.mjs [--source] [--gate] [--json <file>]
 *                                           [--only "desktop"] [--write-baseline]
 *
 * T-0056 was filed with a claim and no instrument: *"the enclosure layer pays
 * its full triangle cost at every scene-detail level … `enclosures.js` builds
 * once, at load, and never consults the scene-detail level."* Three tickets have
 * landed on that since, each on its own reasoning, and NONE of them measured the
 * layer's own cost:
 *
 *   T-0067  a pale is drawn as a zero-thickness plank at `light` — 4 triangles
 *           where the prism is 10, same width, height, place and rhythm.
 *   T-0068  `balanced` takes the same plank, because the middle tier had never
 *           given this layer anything up.
 *   T-0150  `light` carries a 350 m furniture reach, and `enclosures` is one of
 *           the five layers in `FURNITURE_LAYERS` it culls.
 *
 * Plus the shadow tier: `light` sets `furnitureCastsShadow: false`, so a fence
 * stops being drawn a second time for the sun there.
 *
 * So the layer DOES consult the level now, by four separate mechanisms, and the
 * only thing nobody could state was the number. That is what this reads, and it
 * reads it in the two halves that answer different questions:
 *
 *   1. **OWNED** — the triangles in the layer's geometry, everything mounted,
 *      wherever the camera is. This is the half T-0067 and T-0068 move, and it
 *      is a property of the LEVEL alone. A level that owns what `full` owns is
 *      a level this layer never heard of.
 *   2. **DRAWN** — the triangles the layer actually submits from a stand, the
 *      colour pass and the sun's pass counted apart. This is the half T-0150 and
 *      the shadow tier move, and it is a property of the level AND of where the
 *      visitor is standing, so it is taken at the whole stand set T-0135 named
 *      rather than at one camera.
 *
 * Both are read off the SCENE — `api.scene3d`, the `enclosures` group, mesh by
 * mesh — rather than off `DETAIL`, for R-A1's reason: a gate that reads the
 * table back is reading its own intent, and the failure worth catching is a
 * policy that reaches the table and not the meshes.
 *
 * `--gate` exits non-zero when the ladder stops working — when a level stops
 * owning less than `full`, when `light` stops drawing less than `full` at some
 * stand, or when the saving falls materially below `enclosure_detail_baseline.json`.
 * That is T-0056's acceptance clause, held rather than asserted.
 *
 * Defaults to the PUBLISHED mirror, for the reason every renderer measurement
 * here does: the source tree loads uncompressed masters and the site loads
 * compressed derivatives, and bugs have shipped in that gap twice. `--source`
 * measures the working tree instead.
 *
 * This is a measurement, not the release gate — `tools/check.sh` has no
 * Playwright by design, and `tools/smoke_renderer.mjs` is where the ladder is
 * held for the WHOLE frame ("turning scene detail down actually draws less").
 * This one holds it for one layer, which is the layer the ticket is about.
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
const wantSource = process.argv.includes('--source');
const wantGate = process.argv.includes('--gate');
const wantWrite = process.argv.includes('--write-baseline');
const jsonAt = process.argv.indexOf('--json');
const jsonOut = jsonAt >= 0 ? process.argv[jsonAt + 1] : null;
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.ENCLOSURE_PORT || 4203);
const YEAR = process.env.ENCLOSURE_YEAR || '1835';
const BASELINE = path.join(HERE, 'enclosure_detail_baseline.json');

/**
 * The five stands, copied from `tools/smoke_renderer.mjs` STANDS — where each
 * one's reason is written and where the set is owned. Copied rather than
 * imported for the reason `measure_furniture_reach.mjs` states: the smoke is a
 * script and not a module, so a stand added there and not here makes this tool
 * less complete, never wrong.
 */
const STANDS = [
  { id: 'lake_at_canal', kind: 'anchor', target: 'green_tree', label: 'Lake at Canal, east' },
  { id: 'the_forks', kind: 'anchor', target: 'forks', label: 'the forks, Wolf Point' },
  { id: 'lake_and_market', kind: 'anchor', target: 'lake_market', label: 'Lake and Market' },
  { id: 'from_above', kind: 'anchor', target: 'from_above', label: 'the open aerial' },
  { id: 'sauganash_26', kind: 'frame', target: 'sauganash_hotel', distance: 26,
    label: 'the Sauganash at 26 m' },
];

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
};
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
if (!wantSource && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}
console.log(`serving ${ROOT} — ${wantSource ? 'source tree' : 'PUBLISHED mirror'}\n`);

/**
 * BOTH VIEWPORTS, and the mobile one is not an afterthought: `light` is the tier
 * a PHONE boots into without anybody touching the control, so the tier this
 * ticket is chiefly about is the one only the mobile pass reads by default.
 */
const onlyAt = process.argv.indexOf('--only');
const ONLY = onlyAt >= 0 ? process.argv[onlyAt + 1] : null;
const VIEWPORTS = [
  { label: 'desktop 1280x800', width: 1280, height: 800 },
  { label: 'mobile 390x780', width: 390, height: 780 },
].filter((v) => !ONLY || v.label.startsWith(ONLY));

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const errors = [];
const passes = [];
for (const vp of VIEWPORTS) {
  const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
  page.on('pageerror', (e) => errors.push(`${vp.label}: ${String(e)}`));
  await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });

  const measured = await page.evaluate(async ({ stands }) => {
    const a = window.__chicago4d;
    const settle = () => new Promise((r) => requestAnimationFrame(
      () => requestAnimationFrame(r)));
    const started = a.detail;

    /**
     * The layer's own ledger, read off the group. `farMerged` batches are a
     * BATCHING of the chunks beside them (T-0146), so they are excluded from
     * OWNED — counting them would report the layer's geometry twice — and
     * included in DRAWN, because when one is visible it is what the frame pays
     * for and its members are hidden.
     */
    const ledger = () => {
      const group = a.scene3d.getObjectByName('enclosures');
      const out = { owned: 0, ownedMeshes: 0, drawn: 0, drawnMeshes: 0,
                    shadow: 0, shadowMeshes: 0, merged: 0, reachCulled: 0 };
      if (!group) return out;
      group.traverse((o) => {
        if (!o.isMesh || !o.geometry) return;
        const pos = o.geometry.getAttribute('position');
        if (!pos) return;
        const tris = (o.geometry.index ? o.geometry.index.count : pos.count) / 3;
        if (o.userData.farMerged) out.merged += 1;
        else { out.owned += tris; out.ownedMeshes += 1; }
        if (o.userData.reachCulled) out.reachCulled += 1;
        // `visible` is the whole truth for what the frame pays: the reach hides
        // a chunk, the merge hides a chunk it is drawing itself, and the
        // frustum is the renderer's business and not read here.
        if (!o.visible) return;
        out.drawn += tris;
        out.drawnMeshes += 1;
        if (o.castShadow) { out.shadow += tris; out.shadowMeshes += 1; }
      });
      return out;
    };

    const seen = [];
    for (const level of a.detailOrder) {
      await a.setDetail(level);
      await settle();
      // Held for the whole level so the wind cannot move a reading between two
      // stands; the counts here are geometry rather than pixels, but the flora
      // rebuild that `setDetail` serialises is what `settle` is waiting on.
      const census = a.scene3d.getObjectByName('enclosures')?.userData?.census ?? null;
      const atStands = [];
      for (const st of stands) {
        if (st.kind === 'frame') { a.setFly(false); a.frame(st.target, st.distance); }
        else a.goTo(st.target);
        await settle();
        const l = ledger();
        atStands.push({ id: st.id, label: st.label, ...l,
                        frameTris: a.stats().triangles });
      }
      // OWNED is a property of the level alone, so it is taken back at the
      // reference stand and asserted equal across the five above.
      a.goTo(stands[0].target);
      await settle();
      const base = ledger();
      seen.push({ level, census,
                  owned: base.owned, ownedMeshes: base.ownedMeshes,
                  reachM: a.furnitureReach.reachM,
                  casts: a.detailLevels[level].furnitureCastsShadow,
                  ownedSpread: [...new Set(atStands.map((x) => x.owned))],
                  atStands });
    }
    await a.setDetail(started);
    return { seen, restored: a.detail === started };
  }, { stands: STANDS });

  passes.push({ viewport: vp.label, ...measured });
  await page.close();
}
await browser.close();
server.close();

/* ------------------------------------------------------------------ report */

const num = (n) => Math.round(n).toLocaleString('en-US');
for (const pass of passes) {
  console.log(`================  ${pass.viewport}  ================`);
  const [full] = pass.seen;
  console.log('THE LAYER\'S OWN GEOMETRY, by level — a property of the level, not the camera');
  console.log('   level        owned tris   meshes   posts    pales   chunks  vs full   reach  casts');
  for (const s of pass.seen) {
    const c = s.census ?? {};
    console.log(`   ${s.level.padEnd(10)} ${num(s.owned).padStart(11)} `
      + `${String(s.ownedMeshes).padStart(8)} `
      + `${num(c.posts ?? 0).padStart(7)} ${num(c.pales ?? 0).padStart(8)} `
      + `${String(c.chunks ?? 0).padStart(8)} `
      + `${`${((1 - s.owned / full.owned) * 100).toFixed(1)} %`.padStart(8)} `
      + `${String(s.reachM ?? '—').padStart(7)} ${s.casts ? '  yes' : '   no'}`);
  }
  console.log('');
  console.log('WHAT THE FRAME PAYS FOR IT, by stand — colour pass, and the sun\'s pass apart');
  for (const st of STANDS) {
    const row = (lv) => lv.atStands.find((x) => x.id === st.id);
    console.log(`   ${st.label}`);
    console.log('      level        drawn   +sun pass    total    meshes  reach-culled   frame');
    const f = row(pass.seen[0]);
    for (const lv of pass.seen) {
      const r = row(lv);
      const total = r.drawn + r.shadow;
      const fTotal = f.drawn + f.shadow;
      console.log(`      ${lv.level.padEnd(10)} ${num(r.drawn).padStart(8)} `
        + `${num(r.shadow).padStart(11)} ${num(total).padStart(8)} `
        + `${String(r.drawnMeshes).padStart(9)} ${String(r.reachCulled).padStart(13)} `
        + `${num(r.frameTris).padStart(11)}`
        + (lv === pass.seen[0] ? '' : `   ${((1 - total / fTotal) * 100).toFixed(1)} % off full`));
    }
  }
  console.log('');
}
if (errors.length) console.log(`PAGE ERRORS: ${errors.join('; ')}`);
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(passes, null, 2)}\n`);

/* -------------------------------------------------------------------- gate */

/**
 * The saving a level makes on the whole layer at a stand: colour pass plus the
 * sun's pass, against `full` at the same stand. One number, because that is what
 * a frame pays and what T-0056's acceptance is written in.
 */
function savingAt(pass, level, standId) {
  const at = (lv) => {
    const s = pass.seen.find((x) => x.level === lv).atStands.find((x) => x.id === standId);
    return s.drawn + s.shadow;
  };
  const f = at('full');
  return f ? 1 - at(level) / f : 0;
}

/**
 * `--write-baseline` MERGES rather than replaces, and that is the whole reason
 * it exists: two viewports do not fit inside one command on this project's
 * runners (a pass is about four minutes and the ceiling is ten), so the desktop
 * and the mobile entries are written by two separate runs. A whole-file rewrite
 * would have each run delete the other's reading.
 */
if (wantWrite) {
  const file = fs.existsSync(BASELINE)
    ? JSON.parse(fs.readFileSync(BASELINE, 'utf8')) : { viewports: {} };
  file.viewports = file.viewports ?? {};
  for (const pass of passes) {
    const level = (l) => pass.seen.find((x) => x.level === l);
    const drawnSavingLight = {};
    for (const st of STANDS) drawnSavingLight[st.id] = Number(savingAt(pass, 'light', st.id).toFixed(4));
    file.viewports[pass.viewport] = {
      ownedFull: level('full').owned,
      ownedBalanced: level('balanced').owned,
      ownedLight: level('light').owned,
      ownedSavingLight: Number((1 - level('light').owned / level('full').owned).toFixed(4)),
      drawnSavingLight,
      source: wantSource ? 'source tree' : 'published mirror',
    };
  }
  fs.writeFileSync(BASELINE, `${JSON.stringify(file, null, 2)}\n`);
  console.log(`baseline written for ${passes.map((p) => p.viewport).join(', ')} `
    + `→ ${path.basename(BASELINE)}`);
}

if (!wantGate) {
  console.log('measurement only — pass --gate to hold the ladder against '
    + path.basename(BASELINE));
} else {
  const have = fs.existsSync(BASELINE)
    ? JSON.parse(fs.readFileSync(BASELINE, 'utf8')) : null;
  const fails = [];
  const note = [];
  for (const pass of passes) {
    const level = (l) => pass.seen.find((x) => x.level === l);
    const full = level('full');
    // 1. THE LEVEL REACHES THE MESHES. `balanced` and `light` must own less
    //    geometry than `full` — the half T-0067 and T-0068 bought, and the half
    //    that is true wherever the camera is.
    for (const l of ['balanced', 'light']) {
      if (!(level(l).owned < full.owned)) {
        fails.push(`${pass.viewport}: '${l}' owns ${num(level(l).owned)} triangles against `
          + `full's ${num(full.owned)} — the level is not reaching the layer's geometry`);
      }
    }
    // 2. OWNED IS A PROPERTY OF THE LEVEL. If it moves between stands the
    //    reading above is a reading of one camera and means nothing.
    for (const s of pass.seen) {
      if (s.ownedSpread.length !== 1) {
        fails.push(`${pass.viewport}: '${s.level}' owns different geometry at different `
          + `stands (${s.ownedSpread.map(num).join(', ')}) — this tool's OWNED column is wrong`);
      }
    }
    // 3. T-0056's ACCEPTANCE, PER STAND. `light` draws measurably less than
    //    `full` everywhere a visitor is taken, not on average and not at one
    //    camera — the shape of the defect T-0115 found one layer over.
    for (const st of STANDS) {
      const saved = savingAt(pass, 'light', st.id);
      if (!(saved > 0)) {
        fails.push(`${pass.viewport}: at ${st.label} 'light' draws no less of this layer `
          + `than 'full' (${(saved * 100).toFixed(1)} %)`);
      }
    }
    // 4. AND IT HAS NOT QUIETLY SHRUNK. Five points of the baseline's own
    //    saving, which is wide enough that a parcel of new fence does not trip
    //    it and narrow enough that a mechanism silently coming off does.
    const was = have?.viewports?.[pass.viewport];
    if (was) {
      const wasOwned = 1 - level('light').owned / full.owned;
      if (wasOwned < was.ownedSavingLight - 0.05) {
        fails.push(`${pass.viewport}: 'light' now owns only ${(wasOwned * 100).toFixed(1)} % `
          + `less than full, against ${(was.ownedSavingLight * 100).toFixed(1)} % at the baseline`);
      }
      for (const st of STANDS) {
        const now = savingAt(pass, 'light', st.id);
        const then = was.drawnSavingLight?.[st.id];
        if (typeof then === 'number' && now < then - 0.05) {
          fails.push(`${pass.viewport}: at ${st.label} 'light' saves `
            + `${(now * 100).toFixed(1)} % against ${(then * 100).toFixed(1)} % at the baseline`);
        }
      }
    } else {
      note.push(`${pass.viewport}: no baseline entry — nothing to compare against`);
    }
  }
  for (const n of note) console.log(`note: ${n}`);
  if (fails.length) {
    console.log('\nGATE FAILED');
    for (const f of fails) console.log(`  · ${f}`);
  } else {
    console.log('\nGATE PASSED — the fences cost less at every step down the ladder');
  }
  if (fails.length) process.exit(1);
}

process.exit(errors.length ? 1 : 0);
