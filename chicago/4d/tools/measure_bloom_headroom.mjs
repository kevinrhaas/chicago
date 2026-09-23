/**
 * measure_bloom_headroom.mjs — T-0034: which bar actually holds the bloom down?
 *
 *   node tools/measure_bloom_headroom.mjs                 the published mirror
 *   node tools/measure_bloom_headroom.mjs --source        the working tree
 *   node tools/measure_bloom_headroom.mjs --assert        hold it to the numbers
 *   BLOOM_VIEWPORT=mobile node tools/measure_bloom_headroom.mjs
 *
 * WHY THIS EXISTS. T-0034 is "raise the bloom", and R-W4c(b1) already measured
 * that the thing it was to be raised TO — a 4–6 % flower-load target — is
 * unsourced on one half and does not reproduce on the other. The owner's ruling
 * on the ticket removed the need for that target: the bloom may be tuned as a
 * RECONSTRUCTED value, bounded and declared. What no ruling can remove is the
 * second half of the ticket's title. Raising a number is only a raise if
 * something downstream can carry it, and three separate ceilings stand between
 * `density_per_ha` and a flower on the screen:
 *
 *   1  THE RECORD. Each community's summed forb `density_per_ha`, in plants/m².
 *   2  THE LATTICE. `forbShareOf` is `min(1, density × cell² / perCell)`, and
 *      the clamp is a hard ceiling of ONE PLANT PER SLOT — 4 slots per 3.4 m
 *      cell, so 0.346 plants/m² and not one plant more, whatever any record
 *      says. K58 is the open parcel on exactly this: six forb layers of ten
 *      already ask for more than the lattice can carry.
 *   3  THE INSTANCE CAPS. Nine head archetypes, each its own InstancedMesh with
 *      its own `TUNE.cap.head` ceiling. `maybeHead` stops pushing when a set is
 *      full, silently, mid-plant.
 *
 * **A raise applied above a binding ceiling changes nothing and reads as
 * success.** That is not hypothetical here: K55 multiplied `z10_settled_town`'s
 * forb density and drew the same 146 plants, "because both sides of the change
 * were over the ceiling". This tool exists so T-0034 cannot repeat that, and so
 * the size of any raise it does make is quoted against the ceiling it has to
 * live under rather than against a target nobody can re-derive.
 *
 * WHAT IT FOUND, 2026-08-27, desktop at full detail. **The bar that governs the
 * bloom is the lattice, and at the two prairies there was 24 % of it left.**
 *
 *   · the ceiling is 0.3460 forbs per m² — 4 slots to a 3.4 m cell — and EIGHT
 *     of ten forb layers now sit exactly on it;
 *   · the mesic prairie's records sum to 0.2800 plants/m² at their midpoints and
 *     0.4080 at their upper bounds, so the RECORDS ALREADY ASK FOR MORE BLOOM
 *     THAN THE LATTICE CAN DRAW. Nothing had to be invented to raise it: T-0034
 *     reads the top of the recorded range instead of its midpoint (L67), which
 *     is 1.236x at the mesic prairie, 1.254x at the wet prairie, 1.572x on the
 *     sand prairie, and — measurably — NOTHING at the other six;
 *   · at `prairie_west` that is 206 forbs and 1,617 heads before, 256 and 1,968
 *     after, for 8,191 more sward triangles;
 *   · and it is the LAST raise those two can be given. Both now read 1.00 share
 *     with no headroom, so the next flower needs a different lattice (K58) and
 *     not a different number.
 *
 * The one thing it found that T-0034 did NOT cause: `flora-head-spike` in the
 * settled town and `flora-head-dome` in the dense forest stood AT 820 of 820 and
 * truncated silently, before and after the raise alike. Those were heads the
 * placer dealt and the frame never drew.
 *
 * **T-0214 CLOSED IT, and §2a is what it added.** The nine head sets shared one
 * ceiling written nine times; they now share one BUDGET split by measured
 * demand (`HEAD_SHARE` in `renderers/web/js/flora.js`), and the total is the
 * same 7,380 instances it was. The demand figures the shares are sized on are
 * §2a's own table, so this tool is both the measurement and the gate: `--assert`
 * fails if any head set is at its cap at any pose in the mosaic, or if the nine
 * ceilings stop summing to 7,380. What made the truncation measurable at all is
 * that the placer now counts DEMAND — every instance the records asked a set
 * for, including the ones a plant abandons after the set fills — so a set that
 * had nothing to draw and one that was cut off mid-plant stopped looking alike.
 *
 * It measures the placer through its own entry points — `flora.update` with a
 * synthetic camera, then `flora.stats` and `flora.communities()` — the way
 * `tools/measure_sward_draw.mjs` does, so it reports the renderer and not a
 * re-implementation of it. `flora.forbLattice` and `flora.stats.caps` were
 * added for it: the ceilings were inside the module and unreadable from outside,
 * which is how a share sitting on its clamp looked like a share that was simply
 * small.
 *
 * NOT in `tools/check.sh`: it drives a real browser. It is a measurement to be
 * re-run and quoted, in the shape of `tools/measure_sward_draw.mjs`.
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
const argv = process.argv.slice(2);
const SOURCE = argv.includes('--source');
const ASSERT = argv.includes('--assert');
const ROOT = SOURCE ? path.resolve(HERE, '..') : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = SOURCE ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.BLOOM_PORT || 4391);
const YEAR = process.env.BLOOM_YEAR || '1835';
const VIEWPORT = process.env.BLOOM_VIEWPORT === 'mobile'
  ? { width: 390, height: 780 } : { width: 1280, height: 800 };

/**
 * The three prairie-sweep poses out of `tools/critic_shots.mjs`, verbatim, plus
 * the two town stands where a visitor meets the herb layer at arm's length. A
 * bloom claim made at one stand is a spot reading (T-0115 item 1), so the tool
 * reports every stand and the verdict quotes the worst.
 */
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
console.log(`serving ${ROOT} — ${SOURCE ? 'source tree' : 'PUBLISHED mirror'} `
  + `· ${VIEWPORT.width}x${VIEWPORT.height}\n`);

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const page = await browser.newPage({ viewport: VIEWPORT });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });

const out = await page.evaluate((stands) => {
  const a = window.__chicago4d;
  const lattice = a.flora.forbLattice;
  const communities = a.flora.communities();
  const rows = [];
  for (const st of stands) {
    const camera = {
      getWorldPosition: (v) => { v.set(st.e, 1.7, -st.n); return v; },
      getWorldDirection: (v) => {
        const r = (st.yaw * Math.PI) / 180;
        v.set(Math.sin(r), 0, -Math.cos(r));
        return v;
      },
    };
    // Twice: the first call places the lattice, the second is the steady state
    // the visitor stands in — the same two-call shape `measure_sward_draw` uses.
    a.flora.update(0.016, camera);
    a.flora.update(0.016, camera);
    const s = a.flora.stats;
    const heads = Object.fromEntries(Object.entries(s.sets)
      .filter(([k]) => k.startsWith('flora-head-')));
    const forbRows = s.draws.filter((d) => d.list === 'forb' && d.drawn > 0)
      .map((d) => ({ community: d.community, drawn: d.drawn, dealt: d.dealt }));
    rows.push({
      id: st.id,
      zone: a.flora.zoneAt(st.e, st.n),
      heads,
      forbs: s.sets['flora-forb'] ?? 0,
      rosettes: s.sets['flora-rosette'] ?? 0,
      headTotal: Object.values(heads).reduce((t, v) => t + v, 0),
      capped: s.capped.slice(),
      instances: s.instances,
      triangles: s.triangles,
      forbRows,
      far: s.sets['flora-far'] ?? 0,
      demand: { ...s.demand },
      shortfall: { ...s.shortfall },
    });
  }
  // EVERY COMMUNITY, not only the three sweep poses. A head set that truncates
  // does it silently — `maybeHead` stops pushing mid-plant — so a raise that
  // clears the caps at three stands and blows them at a fourth would ship as a
  // raise and draw as a gap. The spot per community is found through the
  // placer's own zone finder and its own plantability rule, the way
  // `tools/measure_sward_draw.mjs` finds one.
  const spots = {};
  const wanted = new Set(a.flora.substrates().map((z) => z.id));
  for (let e = -900; e <= 1200 && Object.keys(spots).length < wanted.size; e += 6) {
    for (let n = -700; n <= 700; n += 6) {
      const z = a.flora.zoneAt(e, n);
      if (z && !spots[z] && a.flora.plantableAt(e, n)) spots[z] = [e, n];
    }
  }
  const sweep = [];
  for (const [zone, [e, n]] of Object.entries(spots)) {
    // Four bearings: the lattice is built in the view cone, so one yaw measures
    // one third of the ground a stand can be asked to draw.
    for (const yaw of [0, 90, 180, 270]) {
      const camera = {
        getWorldPosition: (v) => { v.set(e, 1.7, -n); return v; },
        getWorldDirection: (v) => {
          const r = (yaw * Math.PI) / 180;
          v.set(Math.sin(r), 0, -Math.cos(r));
          return v;
        },
      };
      a.flora.update(0.016, camera);
      a.flora.update(0.016, camera);
      const s = a.flora.stats;
      sweep.push({
        zone,
        yaw,
        sets: { ...s.sets },
        capped: s.capped.slice(),
        // T-0214: what the records asked each set for at this pose, so the
        // table below can report a shortfall by name rather than inferring one
        // from a count that happens to equal a ceiling.
        demand: { ...s.demand },
      });
    }
  }
  const ring = a.flora.rings.layers.forb;
  return {
    sweep,
    lattice,
    communities,
    caps: a.flora.stats.caps,
    trisPer: a.flora.stats.trisPer,
    rows,
    reach: {
      forbOuter: ring.fade[0],
      forbBand: ring.fade[1],
      headOuter: ring.head[0],
      far: a.flora.farBand.bands.map((b) => b.radius),
    },
  };
}, STANDS);

const pct = (v) => `${(v * 100).toFixed(1)} %`;
const fx = (v, n = 3) => (v === null || v === undefined ? '—' : Number(v).toFixed(n));

// ---- §1 the lattice ------------------------------------------------------ //

console.log('§1 THE LATTICE — one plant per slot, and how many communities are on it\n');
const L = out.lattice;
console.log(`  cell ${L.cell} m · ${L.perCell} slots per cell · one slot stands for `
  + `${L.slotArea.toFixed(3)} m²`);
console.log(`  CEILING: ${L.ceilingPerM2.toFixed(4)} forbs per m², and not one more, `
  + 'whatever a record says.\n');
// `forbDensity` is the sum the share is dealt off (T-0034: the recorded upper
// bound) and `forbDensityMid` the midpoint sum it was dealt off before, so the
// raise and the ceiling that ate the rest of it are both readable here.
console.log(`  ${'community'.padEnd(24)}${'mid'.padStart(10)}${'top'.padStart(10)}`
  + `${'was'.padStart(8)}${'now'.padStart(8)}${'raise'.padStart(9)}`
  + `${'headroom'.padStart(10)}`);
let clamped = 0;
let raised = 0;
for (const c of out.communities) {
  if (c.forbDensity === null || c.forbDensity === undefined) continue;
  const share = c.forbShare;
  const wasShare = Math.min(1, (c.forbDensityMid ?? 0) / L.ceilingPerM2);
  const room = share > 0 ? 1 / share : Infinity;
  const onClamp = share >= 0.9999;
  if (onClamp) clamped++;
  const gain = wasShare > 0 ? share / wasShare : 1;
  if (gain > 1.0001) raised++;
  console.log(`  ${c.id.padEnd(24)}${fx(c.forbDensityMid, 4).padStart(10)}`
    + `${fx(c.forbDensity, 4).padStart(10)}${fx(wasShare, 3).padStart(8)}`
    + `${fx(share, 3).padStart(8)}${(gain > 1.0001 ? `${gain.toFixed(3)}x` : '—').padStart(9)}`
    + `${(onClamp ? 'NONE' : `${room.toFixed(2)}x`).padStart(10)}`);
}
console.log(`\n  ${raised} communities took a raise; ${clamped} of ${out.communities.length} `
  + 'are ON the clamp (K58). For those the recorded');
console.log('  upper bound and the recorded midpoint are the same number to the renderer, '
  + 'because both\n  are over the ceiling — a raise applied there is a raise that draws nothing.');

// ---- §2 the head sets ---------------------------------------------------- //

console.log('\n§2 THE INSTANCE CAPS — nine head archetypes, each with its own ceiling\n');
const kinds = Object.keys(out.rows[0].heads).sort();
console.log(`  ${'stand'.padEnd(15)}${'zone'.padEnd(22)}${'forbs'.padStart(7)}`
  + `${'heads'.padStart(7)}${'busiest head set'.padStart(28)}${'spent'.padStart(8)}`);
let worstSpend = 0;
for (const r of out.rows) {
  let busy = null;
  for (const k of kinds) {
    const spend = out.caps[k] ? r.heads[k] / out.caps[k] : 0;
    if (!busy || spend > busy.spend) busy = { k, spend, n: r.heads[k], cap: out.caps[k] };
  }
  worstSpend = Math.max(worstSpend, busy.spend);
  console.log(`  ${r.id.padEnd(15)}${String(r.zone).padEnd(22)}${String(r.forbs).padStart(7)}`
    + `${String(r.headTotal).padStart(7)}`
    + `${`${busy.k.replace('flora-head-', '')} ${busy.n}/${busy.cap}`.padStart(28)}`
    + `${pct(busy.spend).padStart(8)}`);
}
const anyCapped = out.rows.filter((r) => r.capped.some((c) => c.startsWith('flora-head-')));
console.log(`\n  head sets AT their cap: ${anyCapped.length
  ? anyCapped.map((r) => `${r.id} (${r.capped.filter((c) => c.startsWith('flora-head-')).join(', ')})`).join('; ')
  : 'none, at any sweep stand'}`);
console.log(`  busiest head set at the sweep stands: ${pct(worstSpend)} of its ceiling.`);

// THE WHOLE MOSAIC, four bearings a community — the guard against a raise that
// clears three stands and truncates at a fourth.
const peak = {};
let peakStand = null;
for (const s of out.sweep) {
  for (const k of Object.keys(out.caps)) {
    if (!out.caps[k]) continue;
    const spend = (s.sets[k] ?? 0) / out.caps[k];
    if (!peak[k] || spend > peak[k].spend) peak[k] = { spend, zone: s.zone, yaw: s.yaw, n: s.sets[k] ?? 0 };
  }
}
const overCapped = out.sweep.filter((s) => s.capped.length);
const worstSets = Object.entries(peak).sort((a, b) => b[1].spend - a[1].spend).slice(0, 4);
console.log(`\n  across ${out.sweep.length} stands (${new Set(out.sweep.map((s) => s.zone)).size} `
  + 'communities x 4 bearings), the four busiest sets at their own worst stand:');
for (const [k, p] of worstSets) {
  console.log(`    ${k.padEnd(22)}${String(p.n).padStart(5)}/${out.caps[k]}  ${pct(p.spend).padStart(7)}`
    + `   at ${p.zone} facing ${p.yaw}°`);
}
console.log(`  sets AT a cap anywhere in the mosaic: ${overCapped.length
  ? [...new Set(overCapped.flatMap((s) => s.capped))].join(', ')
  : 'NONE — no set truncates, so every head the placer deals is drawn'}`);

// ---- §2a the shortfall, by name and count (T-0214) ----------------------- //
//
// A set sitting on its ceiling says nothing about how much it refused. The
// placer now counts DEMAND — every instance the records asked each set for,
// including the ones a plant gave up on after the set filled — so the two
// questions this ticket exists to separate can be asked separately: how full is
// a set, and how many inflorescences did the frame drop.
console.log('\n§2a WHAT WAS ASKED FOR, AND WHAT WAS REFUSED — every set, every pose\n');
const want = {};
for (const st of [...out.sweep, ...out.rows.map((r) => ({ zone: r.zone, yaw: 'stand', demand: r.demand, sets: r.heads }))]) {
  for (const [k, d] of Object.entries(st.demand || {})) {
    if (!k.startsWith('flora-head-')) continue;
    if (!want[k] || d > want[k].demand) {
      want[k] = { demand: d, drawn: st.sets[k] ?? 0, zone: st.zone, yaw: st.yaw };
    }
  }
}
const headTotalCap = Object.entries(out.caps)
  .filter(([k]) => k.startsWith('flora-head-')).reduce((a, [, v]) => a + v, 0);
const wantRows = Object.entries(want).sort((a, b) => b[1].demand - a[1].demand);
console.log(`  ${'set'.padEnd(22)}${'cap'.padStart(6)}${'asked'.padStart(8)}${'drawn'.padStart(7)}`
  + `${'refused'.padStart(9)}   at its own worst pose`);
let refusedTotal = 0;
for (const [k, w] of wantRows) {
  const short = Math.max(0, w.demand - out.caps[k]);
  refusedTotal += short;
  console.log(`  ${k.padEnd(22)}${String(out.caps[k]).padStart(6)}${String(w.demand).padStart(8)}`
    + `${String(Math.min(w.demand, out.caps[k])).padStart(7)}${(short ? String(short) : '—').padStart(9)}`
    + `   ${w.zone} facing ${w.yaw}${w.yaw === 'stand' ? '' : '°'}`);
}
const wantSum = wantRows.reduce((a, [, w]) => a + w.demand, 0);
console.log(`  ${'—'.padEnd(22)}${String(headTotalCap).padStart(6)}${String(wantSum).padStart(8)}`
  + `${''.padStart(7)}${String(refusedTotal).padStart(9)}   summed over each set's OWN worst pose`);
const refusedTris = wantRows.reduce((a, [k, w]) => a
  + Math.max(0, w.demand - out.caps[k]) * (out.trisPer[k] ?? 0), 0);
console.log(`\n  Every set's worst pose at once is a bound no single frame ever draws, and it is `
  + `\n  ${wantSum} against a ${headTotalCap}-instance head budget. So the shortfall is an ALLOCATION `
  + '\n  and not a budget: what a set needs is what it is asked for at its own worst pose.');
console.log(`\n  What the refusals cost the frame if every one of them were drawn: `
  + `${refusedTris.toLocaleString()} triangles`);
console.log(`  ${Object.entries(out.trisPer).filter(([k]) => k.startsWith('flora-head-'))
  .map(([k, t]) => `${k.replace('flora-head-', '')} ${t}`).join(' · ')} triangles an instance`);

// ---- §2b the reach ------------------------------------------------------- //

console.log('\n§2b THE REACH — how far out any bloom is drawn at all\n');
const R = out.reach;
console.log(`  forb ring  ${R.forbOuter.toFixed(2)} m outer, ${R.forbBand.toFixed(2)} m band`);
console.log(`  head ring  ${R.headOuter.toFixed(2)} m outer  (HEAD_FADE_AT off the forb ring)`);
console.log(`  far band   ${R.far.map((r) => `${r} m`).join(' then ')}  — aggregate clump cards, `
  + 'and they carry NO head');
console.log(`\n  So bloom is drawn over ${((R.headOuter / R.far[R.far.length - 1]) ** 2 * 100)
  .toFixed(1)} % of the ground the sward covers, and the rest of the`);
console.log('  meadow is grass-coloured whatever its records say is flowering on it. That is a '
  + 'reach\n  question, not a density one, and no amount of `density_per_ha` reaches past it.');
for (const r of out.rows) {
  console.log(`  ${r.id.padEnd(15)} far cards ${String(r.far).padStart(4)}/${out.caps['flora-far']}`
    + `   sward triangles ${r.triangles.toLocaleString()}`);
}

// ---- §3 the verdict ------------------------------------------------------ //

console.log('\n§3 WHICH BAR BINDS\n');
const prairie = out.rows.filter((r) => r.id.startsWith('prairie'));
const zoneOf = new Map(out.communities.map((c) => [c.id, c]));
for (const r of prairie) {
  const c = zoneOf.get(r.zone);
  if (!c) continue;
  const room = c.forbShare > 0 ? 1 / c.forbShare : Infinity;
  const headRoom = kinds.reduce((worst, k) => {
    const spend = out.caps[k] ? r.heads[k] / out.caps[k] : 0;
    return spend > 0 ? Math.min(worst, 1 / spend) : worst;
  }, Infinity);
  const bind = room <= headRoom ? 'THE LATTICE' : 'AN INSTANCE CAP';
  console.log(`  ${r.id}: standing in ${r.zone}, the lattice allows ${room.toFixed(2)}x more `
    + `plants and the\n    busiest head set allows ${headRoom.toFixed(2)}x more heads. `
    + `${bind} binds first.`);
}
console.log('\n  A raise larger than the smaller of those two numbers is not a raise. It is a '
  + 'number\n  changed in a file, and the frame does not move — which is exactly what happened '
  + 'to K55.');

if (errors.length) {
  console.log(`\nPAGE ERRORS (${errors.length}):`);
  for (const e of errors.slice(0, 5)) console.log(`  ${e}`);
}

await browser.close();
server.close();

if (ASSERT) {
  const problems = [];
  const want = (label, got, exp, tol) => {
    if (got === null || got === undefined || Math.abs(got - exp) > tol) {
      problems.push(`${label}: ${got} where T-0034 committed ${exp} (±${tol})`);
    }
  };
  want('the lattice ceiling, forbs per m²', out.lattice.ceilingPerM2, 0.3460, 0.0002);
  const mesic = out.communities.find((c) => c.id === 'z02_mesic_prairie');
  want('z02_mesic_prairie forb share', mesic?.forbShare, 1.0, 0.0001);
  want('z02_mesic_prairie summed forb density, recorded top',
    mesic?.forbDensity, 0.4080, 0.0005);
  want('z02_mesic_prairie summed forb density, recorded midpoint',
    mesic?.forbDensityMid, 0.2800, 0.0005);
  const west = out.rows.find((r) => r.id === 'prairie_west');
  // Desktop, full detail. The placer is world-anchored and deterministic, so
  // these are exact readings and not samples; the tolerance is for a build that
  // moves the ground under the stand, which is a real change and should fail.
  want('prairie_west forbs drawn', west?.forbs, 256, 12);
  // T-0214 RESTATED THIS FROM T-0034's 1,968, and the reason is not this ticket:
  // T-0209 carried the bloom out past the near ring the same day, and more reach
  // is more heads. On `dev` at c39167b4 the figure reads 2,441 and `--assert`
  // fails on BOTH this line and the truncation line below — `flora-head-raydroop`
  // stands at its cap at prairie_west there, which is 2,441 drawn out of 2,469
  // asked for. With the head budget allocated on measured demand nothing
  // truncates and the stand draws all 2,469, so this is the figure with no set
  // refusing anything, and the two lines agree again.
  want('prairie_west heads drawn', west?.headTotal, 2469, 60);
  // The raise is only a raise if nothing downstream truncates it. The two sets
  // that DO stand at their cap are `spike` in the settled town and `dome` in
  // the wet woods, and both were at it before T-0034 — see the header.
  if (west && west.capped.some((c) => c.startsWith('flora-head-'))) {
    problems.push(`prairie_west truncates ${west.capped.join(', ')} — the raise is not all drawn`);
  }
  // T-0214, and this is the ticket's own gate: NO head set at its cap at any
  // pose in the mosaic, not merely at the three named stands. The allocation in
  // `HEAD_SHARE` is sized on the demand §2a measures, so a set that fills again
  // means the demand has moved and the shares are stale.
  const stillCapped = [...new Set(out.sweep.flatMap((st) => st.capped)
    .concat(out.rows.flatMap((r) => r.capped)))].filter((c) => c.startsWith('flora-head-'));
  if (stillCapped.length) {
    problems.push(`head sets still at their cap: ${stillCapped.join(', ')} — `
      + 're-measure §2a and re-size HEAD_SHARE in renderers/web/js/flora.js');
  }
  // ...and the allocation must never be a raise. Nine shares averaging one is
  // the promise `HEAD_SHARE` makes; this is it read back off the built meshes.
  const headCapTotal = Object.entries(out.caps)
    .filter(([k]) => k.startsWith('flora-head-')).reduce((a, [, v]) => a + v, 0);
  want('the nine head ceilings summed', headCapTotal, 7380, 9);
  console.log('');
  if (problems.length) {
    for (const p of problems) console.log(`FAIL  ${p}`);
    process.exit(1);
  }
  console.log('ASSERTIONS OK — the ceilings T-0034 measured are still the ceilings.');
}
if (errors.length) process.exit(1);
