/**
 * Does every flower head drawn in the sward have a plant under it — ROADMAP R-BUG7.
 *
 * The owner photographed two yellow heads hanging above the horizon on South
 * Water Street, each on a short stalk that stops in mid-air. **That symptom has
 * been repaired four times in `renderers/web/js/flora.js` and asserted zero
 * times.** Every one of those repairs was a change to the DRAWING checked by
 * eye; the two things in `tools/smoke_renderer.mjs` that sound like a check for
 * it are not — `floating` is about buildings hovering over their ground, and
 * `floatingDry/floatingWet` asks where a water-lily RECORD is placed. R-BUG5b
 * proved that a placement test cannot see a drawing fault: 391 stations were
 * dry and 10,734 vertices of timber stood in the river at the same moment.
 *
 * So this reads the DRAWING back. It takes the instance buffers that were
 * uploaded to the GPU for this frame — every head set and every rooted set —
 * reproduces the vertex program's ring fade and head descent in JS, and asks of
 * each drawn head:
 *
 *   is there a drawn plant, within the furthest its own stalk could reach, whose
 *   drawn top comes up to the bottom of that stalk?
 *
 * A head that fails is one a visitor sees hanging with clear ground under it.
 *
 * The arithmetic, all of it copied from `flora.js` so the two cannot drift:
 *
 *   fade(ring, d)    = clamp01((ring.x - d) / ring.y) * innerRamp   (the GLSL)
 *   drawn?           = fade > 0
 *   plant top        = y + height                      (T-0035: no height ramp)
 *   head origin      = the matrix translation, and nothing lowers it
 *   stalk foot       = head origin + M * (0, minY(archetype) * size, 0)
 *
 * Until T-0035 the ring ramp scaled the geometry and every line above carried a
 * `* fade`: a plant was drawn at `fade` of its height, a head's origin was
 * lowered by `rise * (1 - fade)` to keep it on the shrinking stem, and this file
 * reproduced both. The ramp is COVERAGE now — `flora.js` § `heightOf` — so a
 * drawn plant is drawn whole and the descent has nothing left to chase.
 *
 * The stalk foot is read off the ARCHETYPE — the lowest vertex of the geometry
 * the set is drawn with — rather than assumed, so the same measurement reads a
 * head anchored at its flower (`minY = -PEDUNCLE[kind]`) and a head anchored at
 * its foot (`minY = 0`) and reports the same point on the model. That is what
 * makes the before and after numbers in R-BUG7's box comparable across the
 * repair that moved the anchor.
 *
 * "Under it" is asked of the PLANT, not of a radius this file invented: a rooted
 * instance supports a foot when its own drawn body — `aFlora.y`, shrunk by the
 * same fade — reaches that foot horizontally and its drawn top is not below it.
 *
 *   node tools/measure_head_support.mjs                 the published mirror
 *   node tools/measure_head_support.mjs --source        the source tree
 *   node tools/measure_head_support.mjs --pose e,n,yaw  somewhere else
 *   node tools/measure_head_support.mjs --shot out.png  photograph the pose too
 *   node tools/measure_head_support.mjs --json out.json
 *
 * Exit status is 1 when any head is unsupported, so it can be quoted as a gate;
 * `tools/smoke_renderer.mjs` carries the same assertion at both viewports.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const argv = process.argv.slice(2);
const has = (f) => argv.includes(f);
const val = (f, d) => (argv.indexOf(f) > -1 ? argv[argv.indexOf(f) + 1] : d);

const SOURCE = has('--source');
// The page resolves its dataset by page path — `walk/` and `renderers/web/` both
// look for `../data/` — so the served root is the directory ABOVE the renderer
// in each tree, not the renderer folder. Serving `renderers/web` directly 404s
// every dataset and the boot hangs on the gate, which is what `tools/shoot.mjs`
// records in its own header.
const ROOT = SOURCE ? APP : path.resolve(APP, '../../site/chicago/4d');
const ENTRY = SOURCE ? '/renderers/web/' : '/walk/';
const DETAIL = val('--detail', 'full');
const SHOT = val('--shot', null);
const JSON_OUT = val('--json', null);
const VIEWPORT = val('--viewport', 'desktop') === 'mobile'
  ? { width: 390, height: 780 } : { width: 1280, height: 800 };

/** The owner's pose: on South Water Street, looking NNE across the main stem.
 *  Overridden with `--pose e,n,yaw`; `--pose anchor` uses the scene's own
 *  `south_water` anchor, wherever T-V2 left it. */
const POSE = (() => {
  const raw = val('--pose', '');
  if (!raw || raw === 'anchor') return { anchor: 'south_water', yaw: 25 };
  const [e, n, yaw] = raw.split(',').map(Number);
  return { e, n, yaw: yaw ?? 25 };
})();

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.json': 'application/json', '.css': 'text/css', '.glb': 'model/gltf-binary',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.bin': 'application/octet-stream',
  '.md': 'text/markdown', '.webp': 'image/webp', '.svg': 'image/svg+xml',
  '.geojson': 'application/json', '.webmanifest': 'application/manifest+json',
};

const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) {
    res.writeHead(404); res.end('not here'); return;
  }
  res.writeHead(200, { 'content-type': MIME[path.extname(f)] ?? 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
});
await new Promise((r) => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;

async function loadPlaywright() {
  let ns;
  try { ns = await import('playwright'); } catch {
    ns = await import(path.join(execSync('npm root -g').toString().trim(), 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();
const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'],
});
const page = await browser.newPage({ viewport: VIEWPORT });
const pageErrors = [];
page.on('pageerror', (e) => pageErrors.push(String(e)));
await page.addInitScript((d) => {
  localStorage.setItem('chicago4d.detail', d);
  localStorage.setItem('chicago4d.entered', '1');
}, DETAIL);
page.setDefaultTimeout(180000);
await page.goto(`${base}${ENTRY}?year=1835`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 180000 });
const gateBtn = await page.$('#gate button, .gate button');
if (gateBtn) { await gateBtn.click(); await page.waitForTimeout(1200); }
await page.evaluate(() => {
  for (const b of document.querySelectorAll('button')) {
    if (/got it/i.test(b.textContent ?? '')) b.click();
  }
});

/**
 * The poses to read at. One head fault is an anecdote: the sward is scattered in
 * a CONE around the view direction, so a bearing that does not look at a plant
 * never draws it, and the owner's own frame and the committed evidence frame are
 * the same spot at two bearings. `--stations` walks the scene's own anchors at
 * four bearings each, which is the population this defect lives in.
 */
const STATIONS = has('--stations');
const BEARINGS = [0, 90, 180, 270];
const poses = STATIONS
  ? await page.evaluate((bearings) => {
    const api = window.__chicago4d;
    const out = [];
    for (const a of api.scene?.anchors ?? []) {
      for (const yaw of bearings) out.push({ id: a.id, e: a.local_e, n: a.local_n, yaw });
    }
    return out;
  }, BEARINGS)
  : [await page.evaluate((p) => {
    const api = window.__chicago4d;
    let e = p.e; let n = p.n; let id = 'pose';
    if (p.anchor) {
      const a = (api.scene?.anchors ?? []).find((x) => x.id === p.anchor)
        ?? (api.scene?.anchors ?? [])[0];
      e = a?.local_e ?? 0; n = a?.local_n ?? 0; id = a?.id ?? 'pose';
    }
    return { id, e, n, yaw: p.yaw };
  }, POSE)];

/** Stand somewhere, let the lattice rebuild, and read the buffers back. */
async function readAt(p) {
  await page.evaluate((t) => {
    const api = window.__chicago4d;
    api.setFly(false);
    api.walker.teleport({ local_e: t.e, local_n: t.n, yaw_deg: t.yaw });
  }, p);
  await page.waitForTimeout(2200);
  return audit();
}

function audit() {
  return page.evaluate(() => {
  const api = window.__chicago4d;
  const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
  /** The GLSL ramp in `plantMaterial`, in JS. */
  const fadeOf = (rx, ry, rz, rw, d) => {
    const outer = clamp01((rx - d) / Math.max(ry, 1e-4));
    const inner = rw > 0 ? clamp01((d - rz) / rw) : 1;
    return outer * inner;
  };

  /** Where this archetype's stalk FOOT sits, in its own nominal units, read off
   *  the geometry rather than assumed. It is `-PEDUNCLE[kind]` while the head
   *  is anchored at its flower and `0` once it is anchored at its foot, so the
   *  same measurement reads both builds and the before/after numbers are
   *  comparable — the point on the model is identical either way. */
  const footOf = (g) => {
    const pos = g.getAttribute('position').array;
    let lo = Infinity;
    for (let i = 1; i < pos.length; i += 3) if (pos[i] < lo) lo = pos[i];
    return lo;
  };

  const cam = api.camera;
  const camX = cam.position.x; const camZ = cam.position.z;
  const meshes = [];
  api.flora.group.traverse((o) => { if (o.isInstancedMesh && o.count > 0) meshes.push(o); });

  const read = (m) => {
    const g = m.geometry;
    const mat = m.instanceMatrix.array;
    const flora = g.getAttribute('aFlora').array;
    const ring = g.getAttribute('aChiRing').array;
    const rise = g.getAttribute('aChiRise').array;
    const out = [];
    for (let i = 0; i < m.count; i++) {
      const o = i * 16;
      out.push({
        x: mat[o + 12], y: mat[o + 13], z: mat[o + 14],
        // Column 1 of the instance matrix is the archetype's own +Y after the
        // per-instance tilt, which is the direction the stalk runs.
        uy: [mat[o + 4], mat[o + 5], mat[o + 6]],
        h: flora[i * 4], spread: flora[i * 4 + 1],
        ring: [ring[i * 4], ring[i * 4 + 1], ring[i * 4 + 2], ring[i * 4 + 3]],
        rise: rise[i],
      });
    }
    return out;
  };

  // Rooted plants first, on a coarse grid so the pairing is not O(heads x plants).
  // `flora-mid` is excluded on purpose: a mid clump card is a billboard that
  // stands for a patch of matrix, no head is ever hung from one, and counting
  // them as support is how a first cut of this measurement read 0 unsupported
  // while the evidence frame showed the fault.
  //
  // `flora-far` is NOT that card, and T-0448 measured why: since T-0209 the far
  // band deals the whole community, so a flowering forb's far card carries its
  // own flower — `rebuildFar` calls `maybeHead` on it and places the head at the
  // card's own e,n. All 2,693 orphans that ticket read stood on a far card at
  // 0.000 m whose top reached them. This file kept the pre-T-0209 set for a
  // fortnight after `tools/smoke_renderer.mjs` fixed its own, so the two DID
  // drift after all, and the 14.7 % it went on reporting was the drift and not
  // the scene (T-0279).
  const CARRIES_HEADS = new Set(['flora-near', 'flora-forb', 'flora-rosette',
    'flora-shrub', 'flora-far']);
  // A far card's `spread` is its billboard HALF-WIDTH — metres, not a stem's
  // radius — so reading it as reach would pass any head within a card's width
  // of one, which is the free pass the note above refuses. A card supports the
  // head it carries at its own foot and nowhere else: reach 0, which `under`
  // floors at 5 cm.
  const CARD = new Set(['flora-far']);
  const CELL = 1.0;
  const grid = new Map();
  let plants = 0;
  for (const m of meshes) {
    if (!CARRIES_HEADS.has(m.name)) continue;
    for (const p of read(m)) {
      const d = Math.hypot(p.x - camX, p.z - camZ);
      const f = fadeOf(p.ring[0], p.ring[1], p.ring[2], p.ring[3], d);
      if (f <= 0) continue;
      const top = p.y + p.h;
      // The drawn body's horizontal reach: the archetypes are built in a unit
      // box and the shader scales xz by `aFlora.y`, so `spread` IS the radius
      // of the leafy envelope — at its whole size, since T-0035.
      const rec = { x: p.x, z: p.z, top, set: m.name, h: p.h,
        r: CARD.has(m.name) ? 0 : p.spread, fade: f };
      plants++;
      const kx = Math.floor(p.x / CELL); const kz = Math.floor(p.z / CELL);
      const key = `${kx},${kz}`;
      let bucket = grid.get(key);
      if (!bucket) { bucket = []; grid.set(key, bucket); }
      bucket.push(rec);
    }
  }

  /** Every rooted plant whose own drawn body reaches the point (x, z) — that is
   *  the acceptance's "within its own spread", asked of the plant rather than
   *  of a radius this file made up. `SLACK` is the one number here that is a
   *  choice: two centimetres, because a stem is centimetres thick and a gate
   *  held to millimetres would fire on float. */
  const SLACK = 0.02;
  const REACH = 0.60; // the widest bucket sweep; no drawn spread exceeds it
  const under = (x, z) => {
    const out = [];
    const k0 = Math.floor((x - REACH) / CELL); const k1 = Math.floor((x + REACH) / CELL);
    const j0 = Math.floor((z - REACH) / CELL); const j1 = Math.floor((z + REACH) / CELL);
    for (let kx = k0; kx <= k1; kx++) {
      for (let kz = j0; kz <= j1; kz++) {
        const b = grid.get(`${kx},${kz}`);
        if (!b) continue;
        for (const p of b) {
          if (Math.hypot(p.x - x, p.z - z) <= Math.max(0.05, p.r) + SLACK) out.push(p);
        }
      }
    }
    return out;
  };
  /** How far the nearest rooted axis of any kind is, for the diagnosis. */
  const nearestAxis = (x, z) => {
    let best = Infinity;
    const k0 = Math.floor((x - REACH) / CELL); const k1 = Math.floor((x + REACH) / CELL);
    const j0 = Math.floor((z - REACH) / CELL); const j1 = Math.floor((z + REACH) / CELL);
    for (let kx = k0; kx <= k1; kx++) {
      for (let kz = j0; kz <= j1; kz++) {
        const b = grid.get(`${kx},${kz}`);
        if (!b) continue;
        for (const p of b) best = Math.min(best, Math.hypot(p.x - x, p.z - z));
      }
    }
    return best;
  };

  /** Below this the head is drawn at a size a visitor cannot resolve, and the
   *  fade has already taken it most of the way into the ground. */
  const FADE_FLOOR = 0.05;

  let heads = 0; let drawn = 0; let unsupported = 0; let nothingUnder = 0;
  const worst = [];
  const axisGaps = [];
  const byKind = {};
  for (const m of meshes) {
    if (!m.name.startsWith('flora-head-')) continue;
    const kind = m.name.replace('flora-head-', '');
    const nominalFoot = footOf(m.geometry);
    for (const p of read(m)) {
      heads++;
      const d = Math.hypot(p.x - camX, p.z - camZ);
      const f = fadeOf(p.ring[0], p.ring[1], p.ring[2], p.ring[3], d);
      if (f <= FADE_FLOOR) continue;
      drawn++;
      const size = p.h;
      // The stalk foot, through the instance matrix's own +Y column (which is
      // where the per-instance tilt lives). `nominalFoot` is signed, so this one
      // expression covers a head anchored at its flower and a head anchored at
      // its foot. `p.rise` is still read off the instance and still reported —
      // it is how far this origin stands over its plant's base — but since
      // T-0035 nothing lowers the head by any part of it.
      const stalk = nominalFoot * size;
      const fx = p.x + p.uy[0] * stalk;
      const fy = p.y + p.uy[1] * stalk;
      const fz = p.z + p.uy[2] * stalk;
      const candidates = under(fx, fz);
      let best = -Infinity; let bestSet = null;
      for (const c of candidates) {
        if (c.top > best) { best = c.top; bestSet = c.set; }
      }
      const axis = nearestAxis(fx, fz);
      axisGaps.push(axis);
      const k = byKind[kind] ?? (byKind[kind] = { drawn: 0, unsupported: 0 });
      k.drawn++;
      if (!candidates.length) nothingUnder++;
      if (best < fy - SLACK) {
        unsupported++;
        k.unsupported++;
        worst.push({
          kind,
          gap_m: best === -Infinity ? null : Number((fy - best).toFixed(3)),
          // T-0035 took the world-space descent away and with it the `drop`
          // this line still subtracted, so the file threw `drop is not defined`
          // the instant it found the fault it exists to describe (T-0279). The
          // head origin IS `p.y`; nothing lowers it any more.
          headY_m: Number(p.y.toFixed(2)),
          stalkFootY_m: Number(fy.toFixed(2)),
          bestPlantTop_m: best === -Infinity ? null : Number(best.toFixed(2)),
          bestPlantSet: bestSet,
          nearestAxis_m: Number.isFinite(axis) ? Number(axis.toFixed(3)) : null,
          bodiesUnderFoot: candidates.length,
          size_m: Number(size.toFixed(3)),
          stalkDrop_m: Number(Math.abs(stalk).toFixed(3)),
          rise_m: Number(p.rise.toFixed(2)),
          fade: Number(f.toFixed(2)),
          fromCamera_m: Number(d.toFixed(1)),
        });
      }
    }
  }
  worst.sort((a, b) => b.gap_m - a.gap_m);
  return {
    pose: {
      e: Number(api.player.e.toFixed(1)), n: Number(api.player.n.toFixed(1)),
      bearing_deg: Number(api.player.bearingDeg.toFixed(0)),
    },
    sets: meshes.map((m) => `${m.name}:${m.count}`),
    plants,
    heads,
    drawn,
    unsupported,
    nothingUnder,
    /** How far each stalk foot landed from the nearest rooted stem, in metres. */
    axisGaps: axisGaps.map((x) => (Number.isFinite(x) ? Number(x.toFixed(3)) : 9.999)),
    byKind,
    worst: worst.slice(0, 6),
  };
  });
}

const perPose = [];
for (const p of poses) {
  const r = await readAt(p);
  r.station = p.id;
  r.bearing = p.yaw;
  perPose.push(r);
  if (SHOT && perPose.length === 1) {
    fs.mkdirSync(path.dirname(path.resolve(SHOT)), { recursive: true });
    await page.screenshot({ path: path.resolve(SHOT) });
  }
}
await browser.close();
server.close();

const gaps = perPose.flatMap((r) => r.axisGaps).sort((a, b) => a - b);
const q = (t) => (gaps.length ? gaps[Math.min(gaps.length - 1, Math.floor(t * gaps.length))] : null);
const worst = perPose.flatMap((r) => r.worst.map((w) => ({ ...w, station: r.station, bearing: r.bearing })))
  .sort((a, b) => (b.nearestAxis_m ?? 0) - (a.nearestAxis_m ?? 0));
const byKind = {};
for (const r of perPose) {
  for (const [k, v] of Object.entries(r.byKind)) {
    const t = byKind[k] ?? (byKind[k] = { drawn: 0, unsupported: 0 });
    t.drawn += v.drawn; t.unsupported += v.unsupported;
  }
}
const report = {
  tree: SOURCE ? 'source' : 'published',
  viewport: `${VIEWPORT.width}x${VIEWPORT.height}`,
  detail: DETAIL,
  poses: perPose.length,
  stations: [...new Set(perPose.map((r) => r.station))],
  heads: perPose.reduce((a, r) => a + r.heads, 0),
  drawn: perPose.reduce((a, r) => a + r.drawn, 0),
  unsupported: perPose.reduce((a, r) => a + r.unsupported, 0),
  nothingUnder: perPose.reduce((a, r) => a + r.nothingUnder, 0),
  posesWithAFault: perPose.filter((r) => r.unsupported > 0).length,
  footToNearestStem_m: { p50: q(0.50), p90: q(0.90), p99: q(0.99), max: gaps.at(-1) ?? null },
  byKind,
  worst: worst.slice(0, 12),
  perPose: perPose.map((r) => ({
    station: r.station, bearing: r.bearing, drawn: r.drawn, unsupported: r.unsupported,
  })),
  pageErrors: pageErrors.slice(0, 5),
};
if (JSON_OUT) {
  fs.mkdirSync(path.dirname(path.resolve(JSON_OUT)), { recursive: true });
  fs.writeFileSync(path.resolve(JSON_OUT), `${JSON.stringify(report, null, 2)}\n`);
}
console.log(JSON.stringify(report, null, 2));
const pct = report.drawn ? (100 * report.unsupported / report.drawn).toFixed(2) : '0.00';
console.log(`\n${report.unsupported} of ${report.drawn} drawn heads have nothing under them `
  + `(${pct}%), over ${report.poses} pose(s)`);
process.exit(report.unsupported > 0 || pageErrors.length ? 1 : 0);
