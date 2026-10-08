/**
 * THE THREE SCENE-DETAIL CEILINGS, READ AT THE GATE'S SIX STANDS, ON ITS OWN.
 *
 *   PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
 *     node tools/measure_detail_ceilings.mjs [--source] [--only desktop|mobile]
 *                                            [--json out.json] [--against DIR]
 *                                            [--stepped] [--south] [--town]
 *                                            [--flora] [--shots DIR]
 *                                            [--stands a,b] [--levels a,b]
 *                                            [--mirror DIR [--tree NAME]]
 *
 * `tools/smoke_renderer.mjs` already walks this sweep and holds each tier to its
 * ceiling — that is the GATE and this is not it. The problem is where the sweep
 * SITS: inside desktop stage 4, behind about a hundred and fifty other checks, so
 * on a runner with a ten-minute per-command ceiling the first reading most branches
 * ever get is the nightly bake's, hours after the branch was cut. Twice now that has
 * put a ceiling failure on a PR that did not cause it (T-0089, and T-0126 below),
 * and both times the first job was to find out WHOSE triangles they were.
 *
 * So: the same stand set, the same three levels, the same `__chicago4d.stats()`
 * the gate reads, in one command against any tree you can point it at. Verified
 * against the instrument it copies — on `steward/t-0126-openings-glazing` at
 * `69eb7175` it reproduces bake run 32761900576's desktop numbers exactly, to the
 * triangle and to the draw call (1,390,060 / 1,244,766 / 826,817 and 203 / 201 / 71
 * calls). A measurement tool that does not reproduce the gate's own figure is
 * measuring something else, so that check is the reason to trust the numbers below.
 *
 * `--against DIR` is the whole point of it. Point it at a second published mirror —
 * `git archive <ref> site/4d | tar -x -C /tmp/somewhere` is enough — and it
 * prints both trees side by side with the delta per stand per tier. THAT is the
 * question a red ceiling actually asks: not "is the town over?" but "did THIS
 * branch put it over?", and the two are answered by different numbers.
 *
 * Defaults to the PUBLISHED mirror for the reason every renderer measurement here
 * does: the source tree loads uncompressed masters and the site loads compressed
 * derivatives, and bugs have shipped in the gap twice. `--source` reads the working
 * tree instead.
 *
 * `--stepped` (T-2015) stops the background render loop after boot and settles
 * each view with two production `api.step()` calls followed by a GPU finish.
 * It preserves the stands, tier order, placement update and actual draw-count
 * reading while avoiding unrelated background frames on a contended software
 * renderer. This is a diagnostic cost reading; published smoke part 5 remains
 * the release assertion and uses the normal animation loop. Each stand is
 * logged immediately so an interrupted sweep retains its completed readings.
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
 *
 * `--price` (T-1674) ANSWERS THE OTHER END OF THE PARCEL. Everything above reads a
 * town that has already been built: the reading is taken after the deal, after the
 * generators and after the bake, which is the wrong end of a parcel to discover a
 * breach at. On 2026-09-27 desktop `balanced` was clearing its ceiling by 1.91 per
 * cent at the forks — 24,420 triangles, which is a handful of cottages — with T-1201
 * (the Lake Street and Dearborn-Clark-LaSalle core) next in the queue and raising its
 * roofs inside the same frusta. `--price` turns that margin into the number a parcel
 * can act on BEFORE it deals:
 *
 *   PW_EXECUTABLE=... node tools/measure_detail_ceilings.mjs --price
 *   PW_EXECUTABLE=... node tools/measure_detail_ceilings.mjs --price --deal D3=6,C2=2
 *   node tools/measure_detail_ceilings.mjs --from data/render/<a reading>.json --deal D3=6
 *
 * It prices a roof from the bytes the roof ships as. Every structure is baked to one
 * GLB under `assets/gltf/`; the triangles in that file are counted here straight out
 * of its glTF chunk — indices over three, per primitive, times the instance count any
 * `EXT_mesh_gpu_instancing` node carries — and attributed to the archetype FAMILY the
 * reconstruction's own records give it (`data/reconstruction/*.json`, anything holding
 * a `structure_id` and a `family` together). That is a committed footprint and not a
 * model of one: it is read from the same bytes `buildings.js` loads, and 251 of the
 * town's 423 structure records carry a family, which is every reconstructed roof — the
 * only kind a parcel deals.
 *
 * WHAT THE TIER DOES TO A ROOF IS MEASURED, NOT ASSUMED. `applyDetail` rebuilds the
 * flora and the trees, re-tiers the shadows and pulls the furniture reach in; it does
 * not decimate `structures`, so the same roof submits the same triangles at all three
 * rungs and the only per-tier term is whether the sun draws it a second time. Rather
 * than assert that, `--price` measures it at each tier's own tightest stand by the
 * method `tools/measure_stand_budget.mjs` owns: hide the `structures` group and read
 * the drop, put it back, clear `castShadow` across it and read again. The ratio of
 * those two IS the tier's multiplier on a roof, and if a future tier ever does
 * decimate a building this table will say so without anyone editing this comment.
 *
 * `--town` (T-2084) ADDS three poses INSIDE the town, where a visitor walks among the
 * houses rather than looks at them from a street anchor: a back yard on a Washington
 * Street block, the shoulder of Lake Street, and a storefront on South Water Street.
 * The owner walked exactly those places and found prairie standing in them, which no
 * stand above sees from close enough to count. Like `--south` they are reported beside
 * the five and never counted in the exit tally. Two of the three stood a metre from a
 * wall, so T-2100 ADDED `town_yard` and `town_store_front` beside them, re-posed to
 * take the yard and the shop front in frame; the old ids keep their coordinates as
 * the baselines they are (see TOWN below). `--flora` reads, at every stand, what
 * the `flora` group alone costs (the frame drawn once with it hidden), and `--shots
 * DIR` writes one capture per in-town pose at the tier the page booted into, named
 * `<tree>-<viewport>-<pose>.png`, so a before and an after sit side by side. Every
 * pass also records the JS heap after a forced collection, because content added to
 * 1835 has cost the phone its heap before (T-2063).
 * The tightest stand and nowhere else, because that is the only stand whose headroom
 * is being divided — and because three extra settled reads at all five stands at all
 * three tiers cost this sweep more than its own 600 s foreground ceiling, which is a
 * measurement nobody can afford to take.
 *
 * WHAT THE NUMBER CLAIMS, EXACTLY. `carries K roofs of family F` means: K roofs of F,
 * ALL of them landing in view of the tightest stand, spend the whole of that stand's
 * headroom. A roof outside the frustum costs that stand nothing, so K is a FLOOR on
 * what the parcel may deal and never a cap on it — a parcel of thirty cottages spread
 * across the town can clear a stand that carries eight. It is the conservative number,
 * which is the one a budget wants.
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
// The import is deferred to the launch below rather than taken here, because
// `--from` (T-1674) prices a banked reading and must not need a browser — nor a
// machine with one installed — to do it.
const HERE = path.dirname(fileURLToPath(import.meta.url));
const argAt = (name) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
};
const wantSource = process.argv.includes('--source');
const wantStepped = process.argv.includes('--stepped');
const wantSouth = process.argv.includes('--south');
const wantTown = process.argv.includes('--town');
const wantFlora = process.argv.includes('--flora');
const shotsDir = argAt('--shots');
const jsonOut = argAt('--json');
const against = argAt('--against');
const ONLY = argAt('--only') || 'desktop';
const YEAR = process.env.DETAIL_YEAR || '1835';
// T-1674. `--from` re-prices a reading this tool already wrote, with no browser at
// all, because the whole point of pricing before a deal is that it has to be cheaper
// than the deal. It implies `--price`.
const priceFrom = argAt('--from');
const wantPrice = process.argv.includes('--price') || !!priceFrom;
const dealArg = argAt('--deal');

const DOWNTOWN = [
  { id: 'sauganash_26', kind: 'frame', target: 'sauganash_hotel', distance: 26,
    label: 'the Sauganash at 26 m' },
  { id: 'lake_at_canal', kind: 'anchor', target: 'lake_at_canal',
    label: 'Lake Street at Canal, east down the axis' },
  { id: 'the_forks', kind: 'anchor', target: 'forks',
    label: 'the forks, from Wolf Point' },
  { id: 'from_above', kind: 'anchor', target: 'from_above',
    label: 'the open aerial' },
  { id: 'lake_and_market', kind: 'anchor', target: 'lake_market',
    label: 'Lake and Market' },
  // T-2015: the fixed flora-review view already exceeded the five-town-stand
  // budget BEFORE the richer vegetation: 1,949,552 triangles / 243 calls at
  // full, 1280x800. Keep its exact pitch as well as its ground and bearing.
  { id: 'prairie_west', kind: 'pose',
    label: 'West prairie, east across the sward toward town',
    pose: { local_e: -250, local_n: -150, yaw_deg: 90, pitch_deg: -8 } },
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
// T-2084. Inside the town, at walking height, where the owner found prairie standing
// in yards, on road shoulders and before shop fronts. Coordinates are scene-local
// metres read off the committed blocks and roofs on 2026-10-04: the back yards of
// the Washington Street houses on blk_washington_wells (h1_02 / h1_03 stand at
// n -418.6, their lots run back to the alley at about -452); Lake Street's north
// shoulder beside blk_south_water_lasalle (the block's south line is at n -102,
// the street's centreline near -112); and the South Water Street frontage of the
// same block, before the two narrow stores c3_12 and c3_13 (n -18 to -20).
const TOWN = [
  { id: 'town_backyard', kind: 'pose',
    label: 'a back yard on Washington and Wells',
    pose: { local_e: 385, local_n: -450, yaw_deg: 0, pitch_deg: -6 } },
  { id: 'town_lake_shoulder', kind: 'pose',
    label: 'the shoulder of Lake Street, looking west',
    pose: { local_e: 520, local_n: -104, yaw_deg: 270, pitch_deg: -6 } },
  { id: 'town_south_water_store', kind: 'pose',
    label: 'a storefront on South Water Street',
    pose: { local_e: 501, local_n: -2, yaw_deg: 180, pitch_deg: -6 } },
  // T-2100. RE-POSED UNDER NEW IDS, and the two above keep theirs and their
  // coordinates. Both stood about a metre from a wall (T-2092's captures are a
  // wall and a door), so neither picture showed the yard or the shop front it was
  // placed to judge. They stay because every number taken there is a baseline —
  // T-2091 and T-2092's triangles, T-2099's still frame, and the still-frame
  // gate's own ceilings in `still_frame_ceilings.json`, which stand on
  // `town_backyard` — and a moved stand would have silently re-based all of them.
  // `town_yard` is 10 m further into the same yards, looking north at the backs of
  // h1_02 and h1_03 (their back walls at n -418.6): the yard ground, the woodpile
  // and the fence line between the lots. `town_store_front` steps back 14 m into
  // South Water Street, looking south at the c3_12 / c3_13 fronts from the street,
  // so the walk, the doors and the ground before them are in frame.
  { id: 'town_yard', kind: 'pose',
    label: 'back yards behind two Washington St houses',
    pose: { local_e: 388, local_n: -440, yaw_deg: 0, pitch_deg: -6 } },
  { id: 'town_store_front', kind: 'pose',
    label: 'South Water St store fronts, from the street',
    pose: { local_e: 501, local_n: 12, yaw_deg: 180, pitch_deg: -4 } },
];
// `--stands a,b` keeps only the named stands, for a reading that has to fit one
// 600 s foreground call: on a four-core runner one tier at eight stands with
// `--flora` is about that long (T-2084). A verdict over a filtered set is printed
// only for the groups that are still whole.
const standFilter = argAt('--stands')?.split(',').filter(Boolean) ?? null;
// T-2092. `--levels a,b` keeps only the named tiers, and `--mirror DIR` (with
// `--tree NAME` to label it) reads a published mirror other than this checkout's —
// so a reading too big for one 600 s call can be cut by tier and by tree and taken
// as several calls, each of which finishes and writes its own JSON.
const levelFilter = argAt('--levels')?.split(',').filter(Boolean) ?? null;
const mirrorDir = argAt('--mirror');
const treeName = argAt('--tree');
const STANDS = [...DOWNTOWN, ...(wantSouth ? SOUTH : []), ...(wantTown ? TOWN : [])]
  .filter((st) => !standFilter || standFilter.includes(st.id));

const VIEWPORTS = [
  { label: 'desktop 1280x800', width: 1280, height: 800 },
  { label: 'mobile 390x780', width: 390, height: 780 },
].filter((v) => ONLY === 'both' || v.label.startsWith(ONLY));

// ── THE COMMITTED FAMILY FOOTPRINTS (T-1674) ─────────────────────────────────
// Read from the baked bytes, node-side, with no browser and no Blender. A GLB is a
// 12-byte header and then length-tagged chunks; the first JSON chunk is the glTF
// document, and the triangle count of a mesh is the sum over its `TRIANGLES`
// primitives of the index count over three (or the position count over three where
// a primitive is not indexed). A mesh is counted once per node that references it,
// and a node carrying `EXT_mesh_gpu_instancing` counts once per instance — which is
// how the generators ship a shed's repeated members.
function glbTriangles(file) {
  const buf = fs.readFileSync(file);
  if (buf.length < 12 || buf.toString('ascii', 0, 4) !== 'glTF') {
    throw new Error(`${file}: not a GLB`);
  }
  let off = 12;
  let doc = null;
  while (off + 8 <= buf.length) {
    const len = buf.readUInt32LE(off);
    const type = buf.readUInt32LE(off + 4);
    off += 8;
    if (type === 0x4e4f534a) { doc = JSON.parse(buf.toString('utf8', off, off + len)); break; }
    off += len;
  }
  if (!doc) throw new Error(`${file}: no JSON chunk`);
  const accessors = doc.accessors || [];
  const instances = new Map();
  for (const node of doc.nodes || []) {
    if (typeof node.mesh !== 'number') continue;
    let n = 1;
    const gi = node.extensions?.EXT_mesh_gpu_instancing;
    if (gi) {
      const attr = Object.values(gi.attributes || {})[0];
      if (typeof attr === 'number') n = accessors[attr]?.count ?? 1;
    }
    instances.set(node.mesh, (instances.get(node.mesh) || 0) + n);
  }
  let total = 0;
  (doc.meshes || []).forEach((mesh, i) => {
    let tris = 0;
    for (const prim of mesh.primitives || []) {
      if ((prim.mode ?? 4) !== 4) continue;
      const count = typeof prim.indices === 'number'
        ? accessors[prim.indices]?.count
        : accessors[prim.attributes?.POSITION]?.count;
      tris += Math.floor((count ?? 0) / 3);
    }
    total += tris * (instances.get(i) || 0);
  });
  return total;
}

// Which family a roof belongs to, taken from the reconstruction's own records rather
// than from its id: anything in `data/reconstruction/*.json` that holds a
// `structure_id` (or `roof_id`) and a `family` in the same object is an assignment,
// and the scan is a union across all of them. A disagreement between two files is a
// fault in the records and is reported rather than silently resolved.
function familyByStructure(root) {
  const dir = path.join(root, 'data', 'reconstruction');
  const map = new Map();
  const conflicts = [];
  const walk = (node) => {
    if (Array.isArray(node)) { for (const v of node) walk(v); return; }
    if (!node || typeof node !== 'object') return;
    const id = node.structure_id || node.roof_id;
    const family = node.family;
    if (typeof id === 'string' && typeof family === 'string' && /^[A-Z]\d$/.test(family)) {
      if (map.has(id) && map.get(id) !== family) conflicts.push(`${id}: ${map.get(id)} vs ${family}`);
      map.set(id, family);
    }
    for (const v of Object.values(node)) walk(v);
  };
  if (!fs.existsSync(dir)) return { map, conflicts };
  for (const f of fs.readdirSync(dir)) {
    if (!f.endsWith('.json')) continue;
    try { walk(JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'))); } catch { /* not a record */ }
  }
  return { map, conflicts };
}

const median = (xs) => {
  const a = [...xs].sort((x, y) => x - y);
  const i = a.length >> 1;
  return a.length % 2 ? a[i] : Math.round((a[i - 1] + a[i]) / 2);
};

/** `{ families: [{family, roofs, min, median, mean, max}], unfamilied, conflicts }` */
function committedFootprints() {
  const root = path.resolve(HERE, '..');
  const manifestPath = path.join(root, 'assets', 'manifest.json');
  if (!fs.existsSync(manifestPath)) throw new Error(`no ${manifestPath} — nothing to price from`);
  const assets = JSON.parse(fs.readFileSync(manifestPath, 'utf8')).assets || {};
  const { map: fam, conflicts } = familyByStructure(root);
  const byFamily = new Map();
  let unfamilied = 0;
  let missing = 0;
  for (const [file, entry] of Object.entries(assets)) {
    const sid = entry.structure_id;
    if (!sid) continue;
    const family = fam.get(sid);
    if (!family) { unfamilied += 1; continue; }
    const glb = path.join(root, 'assets', 'gltf', file);
    if (!fs.existsSync(glb)) { missing += 1; continue; }
    if (!byFamily.has(family)) byFamily.set(family, []);
    byFamily.get(family).push(glbTriangles(glb));
  }
  const families = [...byFamily.entries()].map(([family, tris]) => ({
    family,
    roofs: tris.length,
    min: Math.min(...tris),
    median: median(tris),
    mean: Math.round(tris.reduce((a, b) => a + b, 0) / tris.length),
    max: Math.max(...tris),
  })).sort((a, b) => (a.family < b.family ? -1 : 1));
  return { families, unfamilied, missing, conflicts };
}

/** `--deal D3=6,C2=2` → `[{family:'D3',roofs:6}, …]`. */
function parseDeal(arg) {
  if (!arg) return null;
  return arg.split(',').map((part) => {
    const [family, n] = part.split('=');
    const roofs = Number(n);
    if (!family || !Number.isFinite(roofs) || roofs <= 0) {
      console.error(`--deal: cannot read "${part}" — the form is FAMILY=COUNT, e.g. D3=6,C2=2`);
      process.exit(2);
    }
    return { family: family.trim(), roofs };
  });
}

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
    await page.exposeFunction('reportDetailStand', (row) => {
      console.log(JSON.stringify({ viewport: vp.label, ...row }));
    });
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`http://127.0.0.1:${port}${entry}?year=${YEAR}`, { waitUntil: 'load' });
    // The scene boots on a software renderer here; the gate allows the same.
    await page.waitForFunction(() => window.__chicago4d?.ready === true,
      null, { timeout: 300_000 });
    const seen = await page.evaluate(async ({ stands, price, budgetStandIds, stepped,
      floraShare, levels }) => {
      const a = window.__chicago4d;
      if (stepped) a.renderer.setAnimationLoop(null);
      const settle = stepped
        ? async () => { a.step(); a.step(); a.renderer.getContext().finish(); }
        : () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      // `goTo` on the aerial anchor turns flight ON and every `frame` stand turns
      // it off again, so one has to be last — the smoke orders it the same way.
      const order = [...stands.filter((s) => s.kind !== 'frame'),
        ...stands.filter((s) => s.kind === 'frame')];
      const started = a.detail;
      const rows = [];
      for (const level of a.detailOrder.filter((l) => !levels || levels.includes(l))) {
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
          // T-2084. The flora group's share: the same frame drawn once without it.
          let flora = null;
          const fg = floraShare ? a.scene3d.getObjectByName('flora') : null;
          if (fg) {
            const was = fg.visible;
            fg.visible = false;
            await settle();
            const without = a.stats();
            fg.visible = was;
            await settle();
            flora = { tris: r.triangles - without.triangles,
                      calls: r.drawCalls - without.drawCalls };
          }
          await window.reportDetailStand({ level, stand: st.id,
            triangles: r.triangles, calls: r.drawCalls, flora });
          atStands.push({ id: st.id, label: st.label,
                          tris: r.triangles, calls: r.drawCalls, flora, structures: null });
        }
        // T-1674. What the frame spends on STRUCTURES, and how much of that is the
        // sun drawing them a second time — `tools/measure_stand_budget.mjs` owns
        // this method and the reason to prefer it to a walk of the scene graph: a
        // `BatchedMesh` submits a subset of its chunks through one multi-draw, so
        // only the renderer knows what it actually drew. The ratio of the two is the
        // multiplier a roof costs at this stand at this tier.
        //
        // TAKEN AT THE WORST BUDGET STAND OF THIS TIER AND NOWHERE ELSE. It is the
        // only stand the pricing uses — the headroom is that stand's — and three
        // extra settled reads at all five cost this sweep more than its own 600 s
        // foreground ceiling when it was written that way, which is a measurement
        // nobody can afford to take.
        if (price) {
          // T-2015's prairie is a pose AND a permanent budget stand. Exclude
          // the optional southern sweep by membership, not by camera kind.
          const downtown = atStands.filter((x) => budgetStandIds.includes(x.id));
          const worst = downtown.reduce((x, y) => (y.tris > x.tris ? y : x), downtown[0]);
          const st = order.find((o) => o.id === worst?.id);
          const g = a.scene3d.getObjectByName('structures');
          if (worst && st && g) {
            if (st.kind === 'frame') { a.setFly(false); a.frame(st.target, st.distance); }
            else if (st.kind === 'pose') {
              a.setFly(typeof st.pose.altitude_m === 'number');
              a.walker.teleport(st.pose);
            } else a.goTo(st.target);
            await settle();
            const base = a.stats().triangles;
            const wasVisible = g.visible;
            g.visible = false;
            await settle();
            const drawn = base - a.stats().triangles;
            g.visible = wasVisible;
            await settle();
            const restore = [];
            g.traverse((o) => {
              if (o.isMesh && o.castShadow) { restore.push(o); o.castShadow = false; }
            });
            let shadow = 0;
            if (restore.length) {
              await settle();
              shadow = base - a.stats().triangles;
              for (const o of restore) o.castShadow = true;
              await settle();
            }
            // Re-stood, so the base is re-read against the reading the table above
            // holds for this stand. Anything but zero here is the instrument's own
            // noise and is printed with the price table rather than swallowed.
            worst.structures = { drawn, shadow, residual: base - worst.tris };
          }
        }
        rows.push({ level, ceiling: a.detailLevels[level].triangles, atStands });
      }
      await a.setDetail(started);
      return rows;
    }, { stands: STANDS, price: wantPrice, budgetStandIds: DOWNTOWN.map((s) => s.id),
      stepped: wantStepped, floraShare: wantFlora, levels: levelFilter });
    // T-2084. The heap after a forced collection, so the reading is the scene's
    // own retained size and not whatever garbage the sweep left behind.
    const heap = await page.evaluate(() => {
      window.gc?.();
      return performance.memory ? performance.memory.usedJSHeapSize : null;
    });
    if (shotsDir && wantTown) {
      fs.mkdirSync(shotsDir, { recursive: true });
      // Into the town first, the way the smoke's `enterTown` does it: the gate and
      // the welcome are HTML over the canvas, so the counters above never saw them,
      // but a capture taken with them up is a picture of the welcome (T-2092).
      await page.evaluate(async () => {
        const gate = document.getElementById('gate');
        if (gate && !gate.hasAttribute('hidden')) {
          if (window.__chicago4d.welcome) window.__chicago4d.welcome.enter('spawn');
          else document.getElementById('gate-btn')?.click();
          await new Promise((r) => setTimeout(r, 150));
        }
        const help = document.getElementById('control-help');
        if (help && !help.hasAttribute('hidden')) document.getElementById('control-help-gotit')?.click();
      });
      for (const st of TOWN) {
        // Under `--stepped` the animation loop is off, so a capture waited on two
        // animation frames would show whichever stand the sweep drew last; step the
        // production loop instead (T-2092).
        await page.evaluate(async ({ pose, stepped }) => {
          const a = window.__chicago4d;
          a.setFly(false);
          a.walker.teleport(pose);
          if (stepped) { a.step(); a.step(); a.renderer.getContext().finish(); }
          else await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
        }, { pose: st.pose, stepped: wantStepped });
        const tag = `${treeLabel.replace(/\W+/g, '_')}-${vp.label.split(' ')[0]}-${st.id}`;
        await page.screenshot({ path: path.join(shotsDir, `${tag}.png`), timeout: 180_000 });
      }
    }
    passes.push({ viewport: vp.label, seen, errors, heap });
    await page.close();
  }
  server.close();
  return { tree: treeLabel, root,
    renderLoop: wantStepped ? 'two production steps and GPU finish' : 'normal animation loop',
    passes };
}

const num = (n) => n.toLocaleString('en-US');

// ── THE PRICE REPORT (T-1674) ────────────────────────────────────────────────
// Reads one sweep — this run's, or a committed one through `--from` — and turns
// each tier's headroom at its own tightest stand into a count of roofs.
function priceReport(res, deal) {
  const foot = committedFootprints();
  const cost = new Map(foot.families.map((f) => [f.family, f]));
  console.log('\n================  PRICING THE NEXT PARCEL (T-1674)  ================');
  console.log('\nCOMMITTED FAMILY FOOTPRINTS — triangles in the GLB each roof ships as,');
  console.log('read from assets/gltf and attributed by the reconstruction\'s own records.\n');
  console.log('   family   roofs        min     median       mean        max');
  for (const f of foot.families) {
    console.log(`   ${f.family.padEnd(8)} ${String(f.roofs).padStart(5)} `
      + `${num(f.min).padStart(10)} ${num(f.median).padStart(10)} `
      + `${num(f.mean).padStart(10)} ${num(f.max).padStart(10)}`);
  }
  console.log(`\n   ${foot.unfamilied} structure(s) carry no family in the records — documented `
    + 'roofs, which a parcel does not deal — and are not priced here.');
  if (foot.missing) console.log(`   ${foot.missing} familied structure(s) have no GLB under assets/gltf.`);
  for (const c of foot.conflicts) console.log(`   RECORDS DISAGREE — ${c}`);

  let unpriceable = 0;
  for (const pass of res[0].passes) {
    console.log(`\n----------------  ${pass.viewport}  ----------------`);
    for (const lv of pass.seen) {
      const downtown = lv.atStands.filter((st) => DOWNTOWN.some((d) => d.id === st.id));
      if (!downtown.length) continue;
      const worst = downtown.reduce((x, y) => (y.tris > x.tris ? y : x));
      const headroom = lv.ceiling - worst.tris;
      const pc = ((headroom / lv.ceiling) * 100).toFixed(2);
      console.log(`\n${lv.level}  ceiling ${num(lv.ceiling)}  worst ${num(worst.tris)} `
        + `at ${worst.label}  — headroom ${num(headroom)} (${pc} %)`);
      const st = worst.structures;
      if (!st) {
        unpriceable += 1;
        console.log('   NO STRUCTURES READING AT THIS STAND — the sweep was not run with '
          + '--price, so there is no multiplier and nothing is priced here.');
        continue;
      }
      const colour = st.drawn - st.shadow;
      if (colour <= 0) {
        unpriceable += 1;
        console.log(`   the structures layer reads ${num(st.drawn)} drawn and ${num(st.shadow)} `
          + 'of it shadow, which leaves no colour pass to divide by — not priced.');
        continue;
      }
      const mult = st.drawn / colour;
      console.log(`   structures here: ${num(st.drawn)} drawn, ${num(st.shadow)} of it the sun `
        + `— a roof in view costs ${mult.toFixed(2)}x its own triangles`
        + `${st.residual ? `  [instrument residual ${num(st.residual)}]` : ''}`);
      if (headroom <= 0) {
        console.log('   THIS TIER IS OVER ALREADY — it carries no roofs at all, and the '
          + 'parcel to run is a trim.');
        continue;
      }
      console.log('   family   per roof in view   the stand carries');
      for (const f of foot.families) {
        const inView = Math.round(f.median * mult);
        console.log(`   ${f.family.padEnd(8)} ${num(inView).padStart(15)}   `
          + `${String(Math.floor(headroom / inView)).padStart(6)} roofs`);
      }
      if (deal) {
        let spend = 0;
        const parts = [];
        for (const d of deal) {
          const f = cost.get(d.family);
          if (!f) {
            console.log(`   THE DEAL NAMES ${d.family}, WHICH NO STANDING ROOF CARRIES — `
              + 'there is no committed footprint to price it from, so this deal is not priced.');
            spend = null;
            break;
          }
          spend += d.roofs * Math.round(f.median * mult);
          parts.push(`${d.family}x${d.roofs}`);
        }
        if (spend !== null) {
          const left = headroom - spend;
          console.log(`   THE DEAL ${parts.join(', ')} — ${num(spend)} in view of this stand, `
            + `${num(left)} left of the headroom — ${left >= 0 ? 'FITS' : 'BREACHES'}`);
        }
      }
    }
  }
  console.log('\nK roofs means K roofs ALL IN VIEW of that stand; a roof outside its frustum');
  console.log('costs it nothing, so K is a floor on what the parcel may deal, not a cap on it.');
  console.log('The gate is tools/smoke_renderer.mjs and this moves no ceiling: AGENTS.md');
  console.log('§ the frame budget is where a raise is argued, and it wants the number first.');
  return unpriceable;
}

if (priceFrom) {
  // No browser, no mirror, no sweep: price a reading this tool already wrote.
  let banked;
  try { banked = JSON.parse(fs.readFileSync(priceFrom, 'utf8')); } catch (e) {
    console.error(`--from ${priceFrom}: ${e.message}`);
    process.exit(2);
  }
  if (!Array.isArray(banked) || !banked[0]?.passes) {
    console.error(`--from ${priceFrom}: not a --json reading from this tool`);
    process.exit(2);
  }
  console.log(`priced from the banked reading ${priceFrom} — NOT a reading of this tree`);
  const unpriceable = priceReport(banked, parseDeal(dealArg));
  if (unpriceable) {
    console.error('\nthat reading was taken without --price, so it holds no structures '
      + 'measurement to price from; re-take it with --price');
    process.exit(3);
  }
  process.exit(0);
}

const { chromium } = await loadPlaywright();
const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader', '--enable-precise-memory-info',
    '--js-flags=--expose-gc'],
});

const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(mirrorDir ?? path.resolve(HERE, '../../../site/4d'));
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
if (!wantSource && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}
const basePort = Number(process.env.DETAIL_PORT || 4198);
const results = [await sweep(browser, ROOT, ENTRY, basePort,
  treeName ?? (wantSource ? 'source tree' : 'this tree'))];
if (against) {
  const other = path.resolve(against);
  const otherEntry = fs.existsSync(path.join(other, 'walk', 'index.html'))
    ? '/walk/' : '/renderers/web/index.html';
  results.push(await sweep(browser, other, otherEntry, basePort + 1, 'against'));
}
await browser.close();

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
      if (seen.length < group.length) return null;
      const w = seen.reduce((x, y) => (y.tris > x.tris ? y : x));
      return { ...w, verdict: w.tris <= mine.ceiling
        ? `PASS by ${num(mine.ceiling - w.tris)}`
        : `OVER by ${num(w.tris - mine.ceiling)}` };
    };
    const worst = groupWorst(DOWNTOWN);
    if (worst && worst.tris > mine.ceiling) over += 1;
    console.log(`\n${level}  ceiling ${num(mine.ceiling)}  ` + (worst
      ? `worst ${num(worst.tris)} at ${worst.label}  — ${worst.verdict}`
      : 'the downtown stands were filtered out — no verdict'));
    const t3 = wantTown ? groupWorst(TOWN) : null;
    if (t3) {
      console.log(`${' '.repeat(level.length)}  the in-town three        `
        + `worst ${num(t3.tris)} at ${t3.label}  — ${t3.verdict}`);
    }
    const s4 = wantSouth ? groupWorst(SOUTH) : null;
    if (s4) {
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
      if (!a) continue;
      let line = `   ${st.label.padEnd(42)} ${num(a.tris).padStart(11)} `
        + `${String(a.calls).padStart(6)}`;
      if (a.flora) line += `  flora ${num(a.flora.tris).padStart(9)} / ${a.flora.calls}`;
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
  for (const r of results) {
    const h = r.passes.find((p) => p.viewport === vp.label)?.heap;
    if (h != null) console.log(`   JS heap after gc (${r.tree}): ${(h / 1048576).toFixed(1)} MiB`);
  }
  if (errs.length) console.log(`\nPAGE ERRORS: ${errs.join('; ')}`);
}
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(results, null, 2)}\n`);
if (wantPrice) priceReport(results, parseDeal(dealArg));
console.log(`\n${over === 0 ? 'every tier inside its ceiling'
  : `${over} tier(s) OVER — the gate is tools/smoke_renderer.mjs, this only reports`}`);
if (wantSouth) {
  console.log(southOver === 0
    ? 'the southern four are inside the same ceilings'
    : `the southern four are over at ${southOver} tier(s) — T-1148; no ceiling is `
      + 'held against them and none is moved by this reading');
}
