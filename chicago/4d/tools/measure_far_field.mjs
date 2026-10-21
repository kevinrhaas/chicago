/**
 * T-2967 — THE FAR FIELD'S CLASSES, AND THE FAR BAND'S CARDS, READ AGAINST THE CPU.
 *
 *   node tools/measure_far_field.mjs [--source] [--tiers light,balanced,full]
 *                                    [--stations a,b] [--bearings 4] [--texels 0.5,1,2]
 *                                    [--gate] [--self-test] [--write]
 *
 * THE QUESTION. T-2967 deals the near pass's far band (`rebuildFar`: three
 * lattices out to 120 m on the phone, 150 balanced, 175 at `full`) on the GPU
 * against the FAR FIELD (flora-gpu-far.js): per band, a SLOT FIELD kept by the
 * pool with one texel per lattice slot, holding the pool's answer at the
 * slot's own point. This tool reads what that field tells a slot against what
 * the CPU answers there, per class, and what the GPU's far band does to the
 * cards a visitor sees. Per tier, per station (the year's anchors and the four
 * critic poses):
 *
 *   1. THE SLOT FIELD, over every slot of the three far lattices (no cone):
 *      the point the pool asked the slot's texel at (zone-kernel.js
 *      `slotPoint`) against `scatter`'s own slot, to the bit; then the class
 *      the page's kept tile holds there (community, WET, TURF, BLOCKED for a
 *      floor, TRODDEN) against the CPU's answer at the slot (`flora.farField.at`,
 *      the far field's terms), each class's disagreement over every slot and
 *      over the CANDIDATE slots (the band's rank and the slot's own ring keep
 *      it: a card can stand there), and the slots on texels the pool did not
 *      answer (dealt whole on the page).
 *   2. THE ARGUMENT FOR THE SLOT FIELD: the texel-centre field it replaced, at
 *      each of `--texels` (rasterised from the CPU's answers at texel centres,
 *      with the texel-centre field's origin rule) — each class's disagreement,
 *      the share of slots its eight-texel edge test would hand back to the page
 *      (`ask`), and the RESIDUAL the edge test misses (a slot whose community,
 *      or water or floor where either side deals, differs).
 *   3. THE CARDS, at `--bearings` bearings per station: a fresh near pass dealt
 *      with the far band on the CPU (`nearDraw.setFarOnGpu(false)`, the far
 *      band as it was before this slice), and one dealt on the GPU and reaped,
 *      both read in the frame. Every `flora-far` card is matched by its root:
 *      the same card to the bit (every instance attribute), a card only one
 *      side has, or a card at the same root that differs. The flower heads and
 *      every other flora set are held to the bit as wholes.
 *
 * `--gate` holds the slot field's class differences and slot points at
 * SLOT_BOUND, and the cards at CARD_BOUND (no card differs, none on one side
 * only, heads and other sets the same, every pose dealt on the GPU).
 * `--self-test` reads the slot field one texel off (each slot against its
 * east neighbour's texel) and must find differences over SLOT_BOUND, so a green
 * run is a reading and not a comparison that cannot see a wrong texel.
 *
 * `--write` keeps the reading at docs/measurements/t-2967-far-field.json. It
 * renders, so it needs Playwright and is not part of `tools/check.sh`.
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
const APP = path.resolve(HERE, '..');
const argv = process.argv.slice(2);
const flag = (name) => { const i = argv.indexOf(name); return i < 0 ? null : argv[i + 1]; };
const wantSource = argv.includes('--source');
const WRITE = argv.includes('--write');
const GATE = argv.includes('--gate');
const SELF_TEST = argv.includes('--self-test');
const TIERS = (flag('--tiers') || 'light,balanced,full').split(',').filter(Boolean);
const PICK = (flag('--stations') || '').split(',').filter(Boolean);
const BEARINGS = Number(flag('--bearings') || 4);
const TEXELS = (flag('--texels') || '0.5,1,2').split(',').map(Number);
const ROOT = wantSource ? APP : path.resolve(APP, '../../site/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.FAR_FIELD_PORT || 4203);
const YEAR = process.env.FAR_FIELD_YEAR || '1835';
const OUT = path.join(APP, 'docs/measurements/t-2967-far-field.json');

/**
 * THE BOUNDS. Zero, both. A slot field's texel is asked at the slot's own
 * point by the same ground code the page runs (T-2696 holds the worker's
 * answers equal to the page's), and the shader finds it by the cell's integer
 * index, so there is no texel geometry left to be wrong about: any class
 * difference at all is a bug, not coarseness. The cards follow: the page
 * re-asks everything else in doubles (flora.js `farRun`), so a card that
 * differs, or stands on one side only, is a bug too. The texel-centre field's
 * readings (part 2) are reported, not gated: they are why the field is a slot
 * field.
 */
const SLOT_BOUND = 0;
const CARD_BOUND = 0;

/** tools/critic_shots.mjs SWEEP_STATIONS, the four that are poses (as the
 *  other flora tools copy them). */
const POSES = [
  { id: 'prairie_south', local_e: 120, local_n: -330 },
  { id: 'prairie_west', local_e: -250, local_n: -150 },
  { id: 'public_square', local_e: 550, local_n: -370 },
  { id: 'river_bank', local_e: 180, local_n: 0 },
];
const scene = JSON.parse(fs.readFileSync(path.join(APP, 'data/scenes', `${YEAR}.json`), 'utf8'));
const STATIONS = [
  ...scene.anchors.map((a) => ({ id: a.id, local_e: a.local_e, local_n: a.local_n })),
  ...POSES,
].filter((s) => !PICK.length || PICK.includes(s.id));

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
  '.ktx2': 'image/ktx2', '.webp': 'image/webp',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (url.endsWith('/')) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404); res.end('not found'); return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));
const base = `http://127.0.0.1:${PORT}`;

/** Runs in the page: one station's classes, at every texel asked. */
async function pageClasses({ st, texels }) {
  const a = window.__chicago4d;
  const ff = a.flora.farField;
  const kept = a.flora.nearDraw?.farField ?? null;
  const e = st.local_e, n = st.local_n;
  const slots = ff.slots(e, n);
  const S = slots.length / 7;
  const at = (x, y) => ff.at(x, y, [0, 0, 0]);
  const truth = [];
  for (let s = 0; s < S; s++) truth.push(at(slots[7 * s], slots[7 * s + 1]));
  const WET = 1, TURF = 2, BLOCKED = 4, TRODDEN = 8;
  const deals = new Map();
  const dealsZ = (z) => { if (!deals.has(z)) deals.set(z, ff.deals(z)); return deals.get(z); };
  /** One tile's reading: `cell(i, j)` is a texel's [zone, flags, height]. */
  const read = (texel, e0, n0, size, cell) => {
    const c = { slots: 0, cand: 0, zone: 0, wet: 0, turf: 0, blocked: 0, trodden: 0, unasked: 0,
      ask: 0, askCand: 0, residual: 0, residualCand: 0, residualNoEdge: 0, residualNoEdgeCand: 0,
      dh: [], first: [] };
    for (let s = 0; s < S; s++) {
      const se = slots[7 * s], sn = slots[7 * s + 1], cand = slots[7 * s + 4] === 1;
      const i = Math.floor((se - e0) / texel), j = Math.floor((sn - n0) / texel);
      if (i < 1 || j < 1 || i >= size - 1 || j >= size - 1) continue;
      const t = truth[s];
      const x = cell(i, j);
      c.slots++;
      if (cand) c.cand++;
      if (x[0] === 255) { c.unasked++; c.ask++; if (cand) c.askCand++; continue; }
      const dz = x[0] !== t[0];
      const df = x[1] ^ t[1];
      if (dz) c.zone++;
      if (df & WET) c.wet++;
      if (df & TURF) c.turf++;
      if (df & BLOCKED) c.blocked++;
      if (df & TRODDEN) c.trodden++;
      // FIELD_GLSL's height: bilinear between the four centres round the slot.
      const gx = (se - e0) / texel - 0.5, gy = (sn - n0) / texel - 0.5;
      const i0 = Math.floor(gx), j0 = Math.floor(gy), tx = gx - i0, ty = gy - j0;
      const h = (cell(i0, j0)[2] * (1 - tx) + cell(i0 + 1, j0)[2] * tx) * (1 - ty)
        + (cell(i0, j0 + 1)[2] * (1 - tx) + cell(i0 + 1, j0 + 1)[2] * tx) * ty;
      c.dh.push(Math.abs(h - t[2]));
      // The edge test (FAR_EDGE_GLSL), as the far deal asks it.
      const dealsHere = dealsZ(x[0]);
      const mask = dealsHere ? (WET | BLOCKED) : 0;
      let edge = false;
      for (let dj = -1; dj <= 1 && !edge; dj++) {
        for (let di = -1; di <= 1; di++) {
          if (!di && !dj) continue;
          const y = cell(i + di, j + dj);
          if (y[0] !== x[0] || y[0] === 255 || ((y[1] ^ x[1]) & mask)) { edge = true; break; }
        }
      }
      if (edge) { c.ask++; if (cand) c.askCand++; }
      const matters = dz || ((dealsHere || dealsZ(t[0])) && (df & (WET | BLOCKED)));
      if (matters) {
        c.residualNoEdge++;
        if (cand) c.residualNoEdgeCand++;
        if (!edge) {
          c.residual++;
          if (cand) c.residualCand++;
          if (c.first.length < 6) c.first.push({ e: +se.toFixed(2), n: +sn.toFixed(2), cand, slot: t.slice(0, 2), texel: x.slice(0, 2) });
        }
      }
    }
    c.dh.sort((p, q) => p - q);
    const dh = c.dh;
    c.heightMm = { p95: 1000 * (dh[Math.floor(0.95 * (dh.length - 1))] ?? 0), max: 1000 * (dh[dh.length - 1] ?? 0) };
    delete c.dh;
    return c;
  };
  const out = { id: st.id, slots: S, cand: 0, texels: {} };
  for (let s = 0; s < S; s++) if (slots[7 * s + 4] === 1) out.cand++;
  for (const texel of texels) {
    const spec = ff.spec(texel);
    const span = spec.texel * spec.size;
    const snap = (v) => Math.round(v / spec.recentre) * spec.recentre - span / 2;
    const e0 = snap(e), n0 = snap(n);
    const cache = new Map();
    const cell = (i, j) => {
      const k = i * 65536 + j;
      let v = cache.get(k);
      if (!v) { v = at(e0 + (i + 0.5) * texel, n0 + (j + 0.5) * texel); cache.set(k, v); }
      return v;
    };
    out.texels[texel] = { size: spec.size, bytes: spec.size * spec.size * 6, ...read(texel, e0, n0, spec.size, cell) };
  }
  // The slot field the page keeps (the pool's answers at each slot), band by
  // band: each slot's texel by its cell, against the CPU at the slot.
  if (kept?.bands) {
    const k = { slots: 0, cand: 0, zone: 0, wet: 0, turf: 0, blocked: 0, trodden: 0, unasked: 0, outside: 0,
      pointDiffer: 0, differ: 0, differCand: 0, shifted: 0, first: [] };
    const cellOf = (tile, I, J) => {
      const i = I - Math.round(tile.e0 / tile.texel), j = J - Math.round(tile.n0 / tile.texel);
      if (i < 0 || j < 0 || i >= tile.size || j >= tile.size) return null;
      const q = ((j + (tile.wj ?? 0)) % tile.size) * tile.size + (i + (tile.wi ?? 0)) % tile.size;
      return [tile.cls[2 * q], tile.cls[2 * q + 1]];
    };
    for (let s = 0; s < S; s++) {
      const se = slots[7 * s], sn = slots[7 * s + 1], band = slots[7 * s + 2];
      const cand = slots[7 * s + 4] === 1, c = slots[7 * s + 5], r = slots[7 * s + 6];
      const tile = kept.bands[band].tile;
      k.slots++;
      if (cand) k.cand++;
      const p = ff.slotPoint(band, c, r);
      if (p[0] !== se || p[1] !== sn) k.pointDiffer++;
      const x = tile ? cellOf(tile, c, r) : null;
      if (!x) { k.outside++; continue; }
      if (x[0] === 255) { k.unasked++; continue; }
      const t = truth[s];
      const df = x[1] ^ t[1];
      if (x[0] !== t[0]) k.zone++;
      if (df & WET) k.wet++;
      if (df & TURF) k.turf++;
      if (df & BLOCKED) k.blocked++;
      if (df & TRODDEN) k.trodden++;
      if (x[0] !== t[0] || df) {
        k.differ++;
        if (cand) k.differCand++;
        if (k.first.length < 6) k.first.push({ e: +se.toFixed(2), n: +sn.toFixed(2), band, cand, slot: t.slice(0, 2), texel: x });
      }
      // The self-test's reading: the texel one east, which is another slot's.
      const y = cellOf(tile, c + 1, r);
      if (y && y[0] !== 255 && (y[0] !== t[0] || y[1] !== t[1])) k.shifted++;
    }
    out.kept = k;
  }
  return out;
}

/** Runs in the page: the far band dealt on the CPU and on the GPU at one pose. */
async function pageCards({ st, bearing }) {
  const a = window.__chicago4d;
  const nd = a.flora.nearDraw;
  a.walker.teleport({ local_e: st.local_e, local_n: st.local_n, yaw_deg: bearing });
  const cam = a.camera.clone();
  cam.updateMatrixWorld(true);
  const deal = () => {
    // A fresh near pass from here: a metre east (not a jump: the kept tiles
    // stay), then back, each read in the frame (no budget).
    const c = cam.clone();
    c.position.x += 1;
    c.updateMatrixWorld(true);
    a.flora.update(0, c);
    a.flora.update(0, cam);
    nd?.flush?.();
  };
  const dump = () => {
    const sets = {};
    a.flora.group.traverse((o) => {
      if (!o.isInstancedMesh) return;
      const attrs = [o.instanceMatrix, o.instanceColor, ...Object.values(o.geometry.attributes)
        .filter((x) => x.isInstancedBufferAttribute && x !== o.instanceMatrix && x !== o.instanceColor)]
        .filter(Boolean);
      sets[o.name] = { count: o.count, attrs: attrs.map((x) => ({ size: x.itemSize,
        data: Array.from(x.array.subarray(0, o.count * x.itemSize)) })) };
    });
    return sets;
  };
  // The kept tiles home here before either deal.
  a.flora.update(0, cam);
  await nd?.settled?.();
  a.flora.update(0, cam);
  const s0 = { ...nd.stats };
  nd.setFarOnGpu(false);
  deal();
  const cpu = dump();
  nd.setFarOnGpu(true);
  const covered = !!nd.farField?.bands.every((b) => b.covers(st.local_e, st.local_n));
  deal();
  const gpu = dump();
  const s1 = nd.stats;
  const d = (k) => s1[k] - s0[k];
  return { cpu, gpu, covered, farDeals: d('farDeals'), farCpu: d('farCpu'), asked: d('farAsked'),
    redealt: d('farRedealt') };
}

/** The far cards of two dumps, matched by root. */
function compareCards(cpu, gpu) {
  const card = (set, i) => set.attrs.map((x) => x.data.slice(i * x.size, (i + 1) * x.size)).flat();
  const key = (set, i) => {
    const m = set.attrs[0].data;
    return `${m[16 * i + 12]},${m[16 * i + 14]}`;
  };
  const c = cpu['flora-far'], g = gpu['flora-far'];
  const gm = new Map();
  for (let i = 0; i < g.count; i++) gm.set(key(g, i), i);
  let same = 0, differ = 0, cpuOnly = 0;
  const firsts = [];
  for (let i = 0; i < c.count; i++) {
    const k = key(c, i);
    const j = gm.get(k);
    if (j === undefined) { cpuOnly++; if (firsts.length < 4) firsts.push({ cpuOnly: k }); continue; }
    gm.delete(k);
    const x = card(c, i), y = card(g, j);
    if (x.length === y.length && x.every((v, q) => Object.is(v, y[q]))) same++;
    else { differ++; if (firsts.length < 4) firsts.push({ differ: k }); }
  }
  const gpuOnly = gm.size;
  for (const k of [...gm.keys()].slice(0, Math.max(0, 4 - firsts.length))) firsts.push({ gpuOnly: k });
  // In the same order too: the far set is pushed in slot order on both sides.
  const order = c.count === g.count && same === c.count
    && card(c, 0).length === card(g, 0).length
    && c.attrs.every((x, q) => x.data.every((v, r) => Object.is(v, g.attrs[q].data[r])));
  const others = {};
  for (const name of Object.keys(cpu)) {
    if (name === 'flora-far') continue;
    const x = cpu[name], y = gpu[name];
    const eq = y && x.count === y.count
      && x.attrs.every((at, q) => at.data.every((v, r) => Object.is(v, y.attrs[q].data[r])));
    if (!eq) others[name] = { cpu: x.count, gpu: y?.count ?? null };
  }
  return { cpu: c.count, gpu: g.count, same, differ, cpuOnly, gpuOnly, order, firsts, others };
}

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const report = { ticket: 'T-2967', year: YEAR, measured: new Date().toISOString(),
  source: wantSource ? 'working tree' : 'published mirror', bounds: { slot: SLOT_BOUND,
    cards: CARD_BOUND }, texels: TEXELS, bearings: BEARINGS, tiers: [] };
let failed = false;
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
const page = await ctx.newPage();
page.setDefaultTimeout(600_000);
const errors = [];
page.on('pageerror', (x) => errors.push(String(x)));
await page.goto(`${base}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 480000 });
await page.evaluate(() => {
  const a = window.__chicago4d;
  a.setAnimationHold?.(true);
  a.renderer.render = () => {};
});
for (const tier of TIERS) {
  await page.evaluate((t) => window.__chicago4d.setDetail(t), tier);
  const meta = await page.evaluate(() => {
    const a = window.__chicago4d;
    const kept = a.flora.nearDraw?.farField;
    return { detail: a.detail, bands: kept?.bands.map((b) => ({ spec: b.spec, bytes: b.bytes })) ?? null,
      bytes: kept?.bytes ?? null };
  });
  console.log(`\n${tier}: far field ${meta.bands ? meta.bands.map((b, i) => `band ${i + 1} ${b.spec.size} x`
    + ` ${b.spec.size} texels of ${+b.spec.texel.toFixed(3)} m (re-centred every ${+b.spec.recentre.toFixed(3)} m)`)
    .join(', ') + `; ${meta.bytes.texels} texels, ${meta.bytes.gpu} bytes on the GPU, ${meta.bytes.page} on the page`
    : 'NONE'}`);
  const sum = {};
  const add = (k, v) => { sum[k] = (sum[k] ?? 0) + v; };
  const rows = [];
  const cards = { cpu: 0, gpu: 0, same: 0, differ: 0, cpuOnly: 0, gpuOnly: 0, unordered: 0, poses: 0,
    uncovered: 0, others: 0, asked: 0, redealt: 0 };
  const firstCards = [];
  for (const st of STATIONS) {
    // The station's own tiles home first: the kept far tile is read with it.
    await page.evaluate(async (s) => {
      const a = window.__chicago4d;
      a.walker.teleport({ local_e: s.local_e, local_n: s.local_n, yaw_deg: 0 });
      a.flora.update(0, a.camera);
      await a.flora.nearDraw?.settled?.();
      a.flora.update(0, a.camera);
    }, st);
    const r = await page.evaluate(pageClasses, { st, texels: TEXELS });
    rows.push(r);
    for (const t of TEXELS) {
      const x = r.texels[t];
      for (const k of ['slots', 'cand', 'zone', 'wet', 'turf', 'blocked', 'trodden', 'ask', 'askCand',
        'residual', 'residualCand', 'residualNoEdge', 'residualNoEdgeCand']) add(`${t}.${k}`, x[k]);
      sum[`${t}.hmax`] = Math.max(sum[`${t}.hmax`] ?? 0, x.heightMm.max);
    }
    if (r.kept) {
      for (const k of ['slots', 'cand', 'zone', 'wet', 'turf', 'blocked', 'trodden', 'unasked', 'outside',
        'pointDiffer', 'differ', 'differCand', 'shifted']) add(`kept.${k}`, r.kept[k]);
    }
    for (let b = 0; b < BEARINGS; b++) {
      const bearing = (360 / BEARINGS) * b;
      const got = await page.evaluate(pageCards, { st, bearing });
      const cmp = compareCards(got.cpu, got.gpu);
      cards.poses++;
      if (!got.covered || got.farDeals < 1) cards.uncovered++;
      for (const k of ['cpu', 'gpu', 'same', 'differ', 'cpuOnly', 'gpuOnly']) cards[k] += cmp[k];
      if (!cmp.order) cards.unordered++;
      if (Object.keys(cmp.others).length) {
        cards.others++;
        if (firstCards.length < 8) firstCards.push({ st: st.id, bearing, others: cmp.others });
      }
      cards.asked += got.asked;
      cards.redealt += got.redealt;
      if ((cmp.differ || cmp.cpuOnly || cmp.gpuOnly) && firstCards.length < 8) {
        firstCards.push({ st: st.id, bearing, ...cmp.firsts.length ? { firsts: cmp.firsts } : {} });
      }
    }
  }
  const pct = (x, y) => (y ? (100 * x / y).toFixed(3) : '-');
  const k = (x) => sum[`kept.${x}`] ?? 0;
  console.log(`  THE SLOT FIELD: ${k('slots')} far slots (${k('cand')} candidates); ${k('pointDiffer')} asked at`
    + ` another point than scatter's; classes that differ from the CPU's at the slot: zone ${k('zone')}, wet`
    + ` ${k('wet')}, turf ${k('turf')}, blocked ${k('blocked')}, trodden ${k('trodden')} — ${k('differ')} slots`
    + ` (${k('differCand')} candidates); ${k('unasked')} on texels the pool did not answer, ${k('outside')}`
    + ` outside their band's tile`);
  console.log('  the texel-centre field it replaced, over every far slot / the candidates, % that'
    + ' disagree with the slot\'s own answer:');
  console.log('  texel   bytes      zone    wet  turf blocked trodden  height p95/max mm | asked (all/cand)'
    + ' | residual (all/cand) | residual with no edge test (cand)');
  for (const t of TEXELS) {
    const g = (k) => sum[`${t}.${k}`] ?? 0;
    const bytes = rows[0]?.texels[t]?.bytes ?? 0;
    const hp95 = Math.max(...rows.map((r) => r.texels[t].heightMm.p95));
    console.log(`  ${String(t).padEnd(6)} ${String(bytes).padStart(8)}  ${pct(g('zone'), g('slots')).padStart(7)}`
      + ` ${pct(g('wet'), g('slots')).padStart(6)} ${pct(g('turf'), g('slots')).padStart(5)}`
      + ` ${pct(g('blocked'), g('slots')).padStart(7)} ${pct(g('trodden'), g('slots')).padStart(7)}`
      + `  ${hp95.toFixed(0)} / ${g('hmax').toFixed(0)}`
      + ` | ${pct(g('ask'), g('slots'))} / ${pct(g('askCand'), g('cand'))}`
      + ` | ${g('residual')} (${pct(g('residual'), g('slots'))} %) / ${g('residualCand')} of ${g('cand')}`
      + ` (${pct(g('residualCand'), g('cand'))} %) | ${g('residualNoEdgeCand')} (${pct(g('residualNoEdgeCand'), g('cand'))} %)`);
  }
  console.log(`  cards, ${cards.poses} poses (${cards.uncovered} not dealt on the GPU): CPU ${cards.cpu}, GPU`
    + ` ${cards.gpu}; ${cards.same} the same card to the bit, ${cards.differ} differ at the same root,`
    + ` ${cards.cpuOnly} only on the CPU, ${cards.gpuOnly} only on the GPU; ${cards.unordered} poses out of`
    + ` order; ${cards.others} poses where another flora set (the heads) differs; ${cards.asked} slots`
    + ` dealt whole on the page, ${cards.redealt} re-dealt in doubles`);
  for (const f of firstCards) console.log(`    ${JSON.stringify(f)}`);
  for (const r of rows) {
    if (r.kept?.first?.length) console.log(`    slot field differs at ${r.id}: ${JSON.stringify(r.kept.first)}`);
  }
  const slotRate = k('slots') ? (k('differ') + k('pointDiffer')) / k('slots') : 1;
  const cardRate = cards.cpu ? (cards.cpuOnly + cards.gpuOnly) / cards.cpu : 0;
  if (GATE) {
    if (!k('slots') || slotRate > SLOT_BOUND || k('outside')) {
      console.log(`  FAIL ${tier}: the slot field — ${k('differ')} classes and ${k('pointDiffer')} points differ`
        + ` (bound ${SLOT_BOUND}), ${k('outside')} slots outside their tile, ${k('slots')} read`);
      failed = true;
    }
    if (cards.differ || cardRate > CARD_BOUND || cards.others || cards.uncovered || !cards.cpu) {
      console.log(`  FAIL ${tier}: the cards — ${cards.differ} differ, ${cards.cpuOnly + cards.gpuOnly} on one side`
        + ` (bound ${CARD_BOUND}), ${cards.others} poses with another set differing,`
        + ` ${cards.uncovered} poses not dealt on the GPU`);
      failed = true;
    }
  }
  if (SELF_TEST) {
    const bites = k('slots') > 0 && k('shifted') / k('slots') > SLOT_BOUND;
    console.log(`  self-test ${tier}: read one texel east, the slot field differs at ${k('shifted')} of`
      + ` ${k('slots')} slots, ${bites ? 'over' : 'NOT over'} the bound — the gate ${bites ? 'bites' : 'DOES NOT BITE'}`);
    if (!bites) failed = true;
  }
  report.tiers.push({ tier, bands: meta.bands, bytes: meta.bytes, sums: sum, cards, firstCards,
    stations: rows.map((r) => ({ id: r.id, slots: r.slots, cand: r.cand,
      texels: Object.fromEntries(Object.entries(r.texels).map(([t, x]) => [t, { ...x }])),
      kept: r.kept ? { ...r.kept } : null })) });
}
console.log(`\npageerrors: ${errors.length}${errors.length ? ` ${JSON.stringify(errors.slice(0, 3))}` : ''}`);
if (errors.length) failed = true;
report.pageerrors = errors;
await browser.close();
server.close();
if (WRITE) {
  fs.writeFileSync(OUT, `${JSON.stringify(report, null, 1)}\n`);
  console.log(`wrote ${path.relative(APP, OUT)}`);
}
if (GATE || SELF_TEST) console.log(failed ? 'FAIL' : 'PASS');
process.exit(failed ? 1 : 0);
