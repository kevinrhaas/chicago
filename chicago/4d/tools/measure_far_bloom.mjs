/**
 * measure_far_bloom.mjs — T-0209: how far does the bloom actually reach, and
 * what is the honest figure past the point where it stops being a mark?
 *
 *   node tools/measure_far_bloom.mjs                the published mirror
 *   node tools/measure_far_bloom.mjs --source       the working tree
 *   node tools/measure_far_bloom.mjs --records      the conversion alone, no browser
 *   FAR_BLOOM_VIEWPORT=mobile node tools/measure_far_bloom.mjs
 *
 * TWO MEASUREMENTS, because T-0209 asks two questions and they have different
 * instruments.
 *
 * §1 THE CONVERSION, out of the records alone. The flora records give bloom IN
 * PLAN — `density_per_ha` x the head's own `size_m` — and a frame reads bloom in
 * SCREEN SPACE at a near-horizontal pose. R-W4c(b1) named that bridge as its
 * second route and skipped it, and without it a far card tinted by the plan
 * figure is invisible and one tinted by anything larger is invented. The bridge
 * is an opaque-canopy model and it needs no constant that is not on a record:
 *
 *   Look across a prairie from eye height. At fifty metres the line of sight is
 *   1.9 degrees below horizontal, so the canopy is seen EDGE ON as a wall, and
 *   every pixel of that wall is filled by the first element the ray meets. The
 *   chance a pixel is a flower rather than foliage is therefore the flower's
 *   share of the community's SILHOUETTE-AREA DENSITY — projected area per
 *   element, times elements per unit volume — and the depth of the wall cancels
 *   out of the ratio. So:
 *
 *     matrix clump   n = cover_fraction / (pi (w/2)^2) clumps per m^2 of ground
 *                    a = w * h, the clump's own vertical silhouette
 *     flower head    n = density_per_ha / 10000 heads per m^2
 *                    a = pi (size_m/2)^2, taken isotropic (LIBERTIES: a head is
 *                        modelled as a sphere's silhouette, which is orientation
 *                        independent; a flat ray head seen edge-on is smaller and
 *                        seen face-on larger, and the project has no committed
 *                        head attitude to average over)
 *
 *   bloom share = sum(head n*a) / (sum(head n*a) + sum(clump n*a))
 *
 * §2 THE REACH, out of the renderer. A head is not an AREA, it is a saturated
 * MARK, and a mark reads while it still covers a pixel. The camera is 62 deg
 * vertical (`main.js`), so the gate's viewports carry 721 (390x780) and 739
 * (1280x800) pixels per radian and a head of `size_m` falls under one pixel at
 * `size_m * 721` metres — the phone sets the bar because mobile is a release
 * gate. This half walks the head InstancedMeshes themselves and reports how far
 * from the stand a head is actually drawn, which is the claim T-0209's
 * acceptance makes ("a visitor standing at prairie_west sees bloom past twenty
 * four metres") stated as a number rather than as a screenshot.
 *
 * NOT in `tools/check.sh`: it drives a real browser. `--records` does not, and
 * that half is deterministic off committed data.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const SOURCE = argv.includes('--source');
const RECORDS_ONLY = argv.includes('--records');
const APP = path.resolve(HERE, '..');

/* -------------------------------------------------------------------------- */
/* §1 the conversion — records only                                            */
/* -------------------------------------------------------------------------- */

/** The two viewports the release gate holds the scene to, as pixels per radian
 *  of a 62-degree vertical field. The SMALLER one sets the bar. */
const FOV_RAD = (62 * Math.PI) / 180;
const PX_PER_RAD = { mobile: 780 / FOV_RAD, desktop: 800 / FOV_RAD };
const BAR_PX_PER_RAD = Math.min(PX_PER_RAD.mobile, PX_PER_RAD.desktop);

const mid = (r) => (r[0] + r[1]) / 2;

function conversion() {
  const dir = path.join(APP, 'data/flora/zones');
  const rows = [];
  for (const f of fs.readdirSync(dir).sort()) {
    if (!f.endsWith('.json')) continue;
    const z = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
    let bloomLambda = 0;
    let matrixLambda = 0;
    let planBloom = 0;
    const reaches = [];
    for (const sp of z.species || []) {
      const inf = sp.july?.inflorescence;
      const dens = sp.abundance?.density_per_ha;
      const cover = sp.abundance?.cover_fraction;
      if (inf && inf.size_m && dens) {
        const n = mid(dens) / 10000;              // heads per m^2 of ground
        const s = mid(inf.size_m);
        const a = Math.PI * (s / 2) ** 2;          // isotropic head silhouette
        bloomLambda += n * a;
        planBloom += n * a;                        // plan cover uses the same disc
        reaches.push({ id: sp.id, size: s, reach: s * BAR_PX_PER_RAD });
      }
      if (cover && sp.width_m && sp.height_m) {
        const w = mid(sp.width_m);
        const h = mid(sp.height_m);
        const n = mid(cover) / (Math.PI * (w / 2) ** 2);
        matrixLambda += n * (w * h);
      }
    }
    if (!reaches.length && !matrixLambda) continue;
    // A community whose matrix records carry no `width_m`/`height_m` pair has no
    // silhouette to divide by, and the ratio is UNDEFINED rather than 1. The
    // marsh is the case: its emergents are recorded by cover and height with no
    // clump width, so it is reported as a gap in the records instead of as a
    // hundred per cent bloom, which is what dividing by zero said.
    const share = matrixLambda > 0
      ? bloomLambda / (bloomLambda + matrixLambda) : null;
    reaches.sort((a, b) => a.reach - b.reach);
    rows.push({
      id: z.id,
      planBloom,
      screenBloom: share,
      heads: reaches.length,
      minReach: reaches.length ? reaches[0].reach : 0,
      medReach: reaches.length ? reaches[(reaches.length / 2) | 0].reach : 0,
      maxReach: reaches.length ? reaches[reaches.length - 1].reach : 0,
    });
  }
  return rows;
}

console.log('§1 THE CONVERSION — what a far card could honestly be tinted by\n');
console.log(`  the bar: ${BAR_PX_PER_RAD.toFixed(1)} px per radian (390x780, 62 deg vertical),`
  + ' so a head of size s stays one pixel wide to s x that.\n');
console.log('  community                  plan bloom   screen bloom   heads   reach min/med/max (m)');
const CONV = conversion();
for (const r of CONV) {
  console.log(`  ${r.id.padEnd(24)}  ${(r.planBloom * 100).toFixed(3).padStart(8)} %`
    + `  ${(r.screenBloom === null ? 'no matrix w/h' : `${(r.screenBloom * 100).toFixed(3)} %`).padStart(13)}`
    + `  ${String(r.heads).padStart(6)}`
    + `   ${r.minReach.toFixed(1).padStart(5)} / ${r.medReach.toFixed(1).padStart(5)}`
    + ` / ${r.maxReach.toFixed(1).padStart(5)}`);
}
console.log('\n  READ IT THIS WAY. `screen bloom` is what a far card may honestly be tinted');
console.log('  by, and it is a few parts in ten thousand — under the eighth bit of an 8-bit');
console.log('  channel, so it is not a colour a frame can carry. `reach` is where the same');
console.log('  record stops being a MARK, and that is tens of metres. The bloom is carried');
console.log('  by geometry to the reach and by nothing at all past it, and this is why.\n');

if (RECORDS_ONLY) process.exit(0);

/* -------------------------------------------------------------------------- */
/* §2 the reach — the renderer's own head instances                            */
/* -------------------------------------------------------------------------- */

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

const ROOT = SOURCE ? APP : path.resolve(APP, '../../site/chicago/4d');
const ENTRY = SOURCE ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.FAR_BLOOM_PORT || 4397);
const YEAR = process.env.FAR_BLOOM_YEAR || '1835';
const VIEWPORT = process.env.FAR_BLOOM_VIEWPORT === 'mobile'
  ? { width: 390, height: 780 } : { width: 1280, height: 800 };

/** `measure_bloom_headroom.mjs`'s three prairie-sweep poses, verbatim. */
const STANDS = [
  { id: 'prairie_west', e: -250, n: -150, yaw: 90 },
  { id: 'prairie_south', e: 120, n: -330, yaw: 90 },
  { id: 'river_bank', e: 180, n: 0, yaw: 0 },
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
if (!SOURCE && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}
console.log(`§2 THE REACH — serving ${SOURCE ? 'source tree' : 'PUBLISHED mirror'}`
  + ` · ${VIEWPORT.width}x${VIEWPORT.height}\n`);

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const page = await browser.newPage({ viewport: VIEWPORT });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });

const rows = await page.evaluate((stands) => {
  const a = window.__chicago4d;
  const out = [];
  for (const st of stands) {
    const camera = {
      getWorldPosition: (v) => { v.set(st.e, 1.7, -st.n); return v; },
      getWorldDirection: (v) => {
        const r = (st.yaw * Math.PI) / 180;
        v.set(Math.sin(r), 0, -Math.cos(r));
        return v;
      },
    };
    a.flora.update(0.016, camera);
    a.flora.update(0.016, camera);
    const s = a.flora.stats;
    // The head instances themselves. The archetype's origin is the FOOT of its
    // own stalk (R-BUG7), so the translation column of the instance matrix is
    // where the flower stands on the ground — which is the distance wanted.
    let far = 0;
    let past24 = 0;
    let past40 = 0;
    let total = 0;
    const buckets = [0, 0, 0, 0, 0, 0];
    a.flora.group.traverse((m) => {
      if (!m.isInstancedMesh || !m.name.startsWith('flora-head-')) return;
      const arr = m.instanceMatrix.array;
      for (let i = 0; i < m.count; i++) {
        const x = arr[i * 16 + 12];
        const z = arr[i * 16 + 14];
        const d = Math.hypot(x - st.e, z - (-st.n));
        total++;
        if (d > far) far = d;
        if (d > 24) past24++;
        if (d > 40) past40++;
        const b = Math.min(5, Math.floor(d / 20));
        buckets[b]++;
      }
    });
    out.push({
      id: st.id,
      zone: a.flora.zoneAt(st.e, st.n),
      heads: total,
      far,
      past24,
      past40,
      buckets,
      far_cards: s.sets['flora-far'] ?? 0,
      triangles: s.triangles,
      instances: s.instances,
      drawCalls: s.drawCalls,
      capped: s.capped.slice(),
    });
  }
  return out;
}, STANDS);

console.log('  stand            zone                 heads   furthest   >24 m   >40 m'
  + '   far cards   sward tris');
for (const r of rows) {
  console.log(`  ${r.id.padEnd(15)}  ${String(r.zone).padEnd(20)}`
    + `${String(r.heads).padStart(6)}`
    + `   ${r.far.toFixed(1).padStart(7)} m`
    + `${String(r.past24).padStart(7)}${String(r.past40).padStart(8)}`
    + `${String(r.far_cards).padStart(12)}${String(r.triangles).padStart(13)}`);
}
console.log('\n  heads by distance, in twenty-metre bins (0-20, 20-40, 40-60, 60-80, 80-100, 100+)');
for (const r of rows) {
  console.log(`  ${r.id.padEnd(15)}  ${r.buckets.map((b) => String(b).padStart(6)).join('')}`);
}
const capped = [...new Set(rows.flatMap((r) => r.capped))];
console.log(`\n  head sets at their cap: ${capped.length ? capped.join(', ') : 'none'}`);
if (errors.length) {
  console.error(`\nPAGEERRORS (${errors.length}):`);
  for (const e of errors) console.error(`  ${e}`);
}
await browser.close();
server.close();
process.exit(errors.length ? 1 : 0);
