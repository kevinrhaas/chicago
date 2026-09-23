/**
 * THE THREE SCENE-DETAIL CEILINGS, READ AT T-0135's FIVE STANDS, ON ITS OWN.
 *
 *   PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
 *     node tools/measure_detail_ceilings.mjs [--source] [--only desktop|mobile]
 *                                            [--json out.json] [--against DIR]
 *
 * `tools/smoke_renderer.mjs` already walks this sweep and holds each tier to its
 * ceiling — that is the GATE and this is not it. The problem is where the sweep
 * SITS: inside desktop stage 4, behind about a hundred and fifty other checks, so
 * on a runner with a ten-minute per-command ceiling the first reading most branches
 * ever get is the nightly bake's, hours after the branch was cut. Twice now that has
 * put a ceiling failure on a PR that did not cause it (T-0089, and T-0126 below),
 * and both times the first job was to find out WHOSE triangles they were.
 *
 * So: the same five stands, the same three levels, the same `__chicago4d.stats()`
 * the gate reads, in one command against any tree you can point it at. Verified
 * against the instrument it copies — on `steward/t-0126-openings-glazing` at
 * `69eb7175` it reproduces bake run 32761900576's desktop numbers exactly, to the
 * triangle and to the draw call (1,390,060 / 1,244,766 / 826,817 and 203 / 201 / 71
 * calls). A measurement tool that does not reproduce the gate's own figure is
 * measuring something else, so that check is the reason to trust the numbers below.
 *
 * `--against DIR` is the whole point of it. Point it at a second published mirror —
 * `git archive <ref> site/chicago/4d | tar -x -C /tmp/somewhere` is enough — and it
 * prints both trees side by side with the delta per stand per tier. THAT is the
 * question a red ceiling actually asks: not "is the town over?" but "did THIS
 * branch put it over?", and the two are answered by different numbers.
 *
 * Defaults to the PUBLISHED mirror for the reason every renderer measurement here
 * does: the source tree loads uncompressed masters and the site loads compressed
 * derivatives, and bugs have shipped in the gap twice. `--source` reads the working
 * tree instead.
 *
 * The stand list is COPIED from `tools/smoke_renderer.mjs` STANDS, where the set is
 * owned and each stand's reason is written, and copied rather than imported for the
 * same reason `tools/measure_furniture_reach.mjs` copies it: the smoke is a script
 * and not a module, so a stand added there and not here makes this tool less
 * complete, never wrong.
 *
 * `--south` (T-1148) ADDS the four southern poses to the sweep — and adds them, never
 * replaces, because the five above are what every ceiling this project holds was
 * measured at and the comparison is the point. They are poses and not anchors because
 * there are no anchors south of the town yet; T-0467 is the ticket that puts them
 * down, and when it does these four should become anchors like the rest. The four are
 * COPIED, coordinate for coordinate, from `tools/measure_ground_tiling.mjs` SOUTH, so
 * that the two instruments stand in the SAME four places and the only thing that
 * differs between their readings is the instrument — which is exactly the question
 * T-1148 asks, the ground-tiling reading having declined to answer it against a
 * ceiling in its own `what_this_is_not`.
 *
 * With `--south` the verdict line is printed TWICE per tier, once for the five
 * downtown stands and once for the four southern ones, and the PASS/OVER exit tally
 * still counts only the downtown five. A tool whose default verdict changed the day
 * a new stand was added would stop answering the question it was built for ("did THIS
 * branch put the town over?"), and a southern stand that is over is a finding for
 * T-1148 to argue, not a red this tool may declare on a branch that never went there.
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
const wantSouth = process.argv.includes('--south');
const jsonOut = argAt('--json');
const against = argAt('--against');
const ONLY = argAt('--only') || 'desktop';
const YEAR = process.env.DETAIL_YEAR || '1835';

const DOWNTOWN = [
  { id: 'sauganash_26', kind: 'frame', target: 'sauganash_hotel', distance: 26,
    label: 'the Sauganash at 26 m' },
  { id: 'lake_at_canal', kind: 'anchor', target: 'green_tree',
    label: 'Lake Street at Canal, east down the axis' },
  { id: 'the_forks', kind: 'anchor', target: 'forks',
    label: 'the forks, from Wolf Point' },
  { id: 'from_above', kind: 'anchor', target: 'from_above',
    label: 'the open aerial' },
  { id: 'lake_and_market', kind: 'anchor', target: 'lake_market',
    label: 'Lake and Market' },
];

// T-1148. The southern field, at the four poses `tools/measure_ground_tiling.mjs`
// read it at — same eastings, same northings, same yaws, same altitude on the
// aerial. Do not "improve" these numbers: their whole value is that they are the
// other instrument's, so the two readings are comparable stand for stand.
const SOUTH = [
  { id: 'south_branch_below_town', kind: 'pose',
    label: 'the South Branch below the town, looking south',
    pose: { local_e: 250, local_n: -700, yaw_deg: 180 } },
  { id: 'mid_field_looking_north', kind: 'pose',
    label: 'mid-field, looking back at the town',
    pose: { local_e: 800, local_n: -1800, yaw_deg: 0 } },
  { id: 'south_end_looking_north', kind: 'pose',
    label: 'the south end of the field, looking north',
    pose: { local_e: 700, local_n: -3200, yaw_deg: 0 } },
  { id: 'above_south_field', kind: 'pose',
    label: 'from the air over the southern field',
    pose: { local_e: 600, local_n: -1600, yaw_deg: 0, altitude_m: 700, pitch_deg: -45 } },
];
const STANDS = wantSouth ? [...DOWNTOWN, ...SOUTH] : DOWNTOWN;

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

/** One tree, served and swept. Returns `{ label, seen }`. */
async function sweep(browser, root, entry, port, treeLabel) {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split('?')[0]);
    let file = path.join(root, url);
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) {
      file = path.join(file, 'index.html');
    }
    if (!file.startsWith(root) || !fs.existsSync(file)) {
      res.writeHead(404, { 'content-type': 'text/plain' });
      res.end(`not found: ${url}`);
      return;
    }
    res.writeHead(200, {
      'content-type': TYPES[path.extname(file)] || 'application/octet-stream',
    });
    fs.createReadStream(file).pipe(res);
  });
  await new Promise((r) => server.listen(port, r));
  const passes = [];
  for (const vp of VIEWPORTS) {
    const page = await browser.newPage({
      viewport: { width: vp.width, height: vp.height },
    });
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`http://127.0.0.1:${port}${entry}?year=${YEAR}`, { waitUntil: 'load' });
    // The scene boots on a software renderer here; the gate allows the same.
    await page.waitForFunction(() => window.__chicago4d?.ready === true,
      null, { timeout: 300_000 });
    const seen = await page.evaluate(async (stands) => {
      const a = window.__chicago4d;
      const settle = () => new Promise((r) => requestAnimationFrame(
        () => requestAnimationFrame(r)));
      // `goTo` on the aerial anchor turns flight ON and every `frame` stand turns
      // it off again, so one has to be last — the smoke orders it the same way.
      const order = [...stands.filter((s) => s.kind !== 'frame'),
        ...stands.filter((s) => s.kind === 'frame')];
      const started = a.detail;
      const rows = [];
      for (const level of a.detailOrder) {
        await a.setDetail(level);
        await settle();
        const atStands = [];
        for (const st of order) {
          if (st.kind === 'frame') { a.setFly(false); a.frame(st.target, st.distance); }
          else if (st.kind === 'pose') {
            // Same two lines the ground-tiling instrument uses. `setFly` is driven
            // from the pose and not left where the last stand put it, because the
            // aerial anchor above turns flight on and a walking pose taken while
            // flying is a different stand.
            a.setFly(typeof st.pose.altitude_m === 'number');
            a.walker.teleport(st.pose);
          } else a.goTo(st.target);
          await settle();
          const r = a.stats();
          atStands.push({ id: st.id, label: st.label,
                          tris: r.triangles, calls: r.drawCalls });
        }
        rows.push({ level, ceiling: a.detailLevels[level].triangles, atStands });
      }
      await a.setDetail(started);
      return rows;
    }, STANDS);
    passes.push({ viewport: vp.label, seen, errors });
    await page.close();
  }
  server.close();
  return { tree: treeLabel, root, passes };
}

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});

const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
if (!wantSource && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}
const basePort = Number(process.env.DETAIL_PORT || 4198);
const results = [await sweep(browser, ROOT, ENTRY, basePort,
  wantSource ? 'source tree' : 'this tree')];
if (against) {
  const other = path.resolve(against);
  const otherEntry = fs.existsSync(path.join(other, 'walk', 'index.html'))
    ? '/walk/' : '/renderers/web/index.html';
  results.push(await sweep(browser, other, otherEntry, basePort + 1, 'against'));
}
await browser.close();

const num = (n) => n.toLocaleString('en-US');
let over = 0;
let southOver = 0;
for (const vp of VIEWPORTS) {
  console.log(`================  ${vp.label}  ================`);
  for (const level of results[0].passes.find((p) => p.viewport === vp.label)
    .seen.map((s) => s.level)) {
    const rows = results.map((r) => ({
      tree: r.tree,
      lv: r.passes.find((p) => p.viewport === vp.label).seen
        .find((s) => s.level === level),
    }));
    const mine = rows[0].lv;
    // The verdict is per GROUP. The downtown five are what the ceilings were set
    // against and what the exit tally counts; the southern four are reported beside
    // them and counted separately, for the reason in the header.
    const groupWorst = (group) => {
      const seen = group
        .map((st) => mine.atStands.find((x) => x.id === st.id))
        .filter(Boolean);
      if (!seen.length) return null;
      const w = seen.reduce((x, y) => (y.tris > x.tris ? y : x));
      return { ...w, verdict: w.tris <= mine.ceiling
        ? `PASS by ${num(mine.ceiling - w.tris)}`
        : `OVER by ${num(w.tris - mine.ceiling)}` };
    };
    const worst = groupWorst(DOWNTOWN);
    if (worst.tris > mine.ceiling) over += 1;
    console.log(`\n${level}  ceiling ${num(mine.ceiling)}  `
      + `worst ${num(worst.tris)} at ${worst.label}  — ${worst.verdict}`);
    if (wantSouth) {
      const s4 = groupWorst(SOUTH);
      southOver += s4.tris > mine.ceiling ? 1 : 0;
      console.log(`${' '.repeat(level.length)}  the southern four        `
        + `worst ${num(s4.tris)} at ${s4.label}  — ${s4.verdict}`);
    }
    const head = rows.length > 1
      ? '   stand                                        triangles    calls'
        + '        against        delta'
      : '   stand                                        triangles    calls';
    console.log(head);
    for (const st of STANDS) {
      const a = mine.atStands.find((x) => x.id === st.id);
      let line = `   ${st.label.padEnd(42)} ${num(a.tris).padStart(11)} `
        + `${String(a.calls).padStart(6)}`;
      if (rows.length > 1) {
        const b = rows[1].lv.atStands.find((x) => x.id === st.id);
        const d = a.tris - b.tris;
        line += ` ${num(b.tris).padStart(14)} `
          + `${(d === 0 ? '0' : `${d > 0 ? '+' : ''}${num(d)}`).padStart(12)}`;
      }
      console.log(line);
    }
  }
  const errs = results.flatMap((r) => r.passes
    .filter((p) => p.viewport === vp.label).flatMap((p) => p.errors));
  if (errs.length) console.log(`\nPAGE ERRORS: ${errs.join('; ')}`);
}
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(results, null, 2)}\n`);
console.log(`\n${over === 0 ? 'every tier inside its ceiling'
  : `${over} tier(s) OVER — the gate is tools/smoke_renderer.mjs, this only reports`}`);
if (wantSouth) {
  console.log(southOver === 0
    ? 'the southern four are inside the same ceilings'
    : `the southern four are over at ${southOver} tier(s) — T-1148; no ceiling is `
      + 'held against them and none is moved by this reading');
}
