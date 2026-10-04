/**
 * turf_shots.mjs — T-2085, the town's short turf: captures and costs at the
 * in-town poses, at every Scene detail tier, before and after.
 *
 *   PW_EXECUTABLE=… node tools/turf_shots.mjs [--root DIR] [--against DIR]
 *       [--out DIR] [--viewport desktop|mobile] [--json out.json] [--no-shots]
 *
 *   --root     the published mirror to read (default ../../site/4d)
 *   --against  a second mirror, read the same way (the BEFORE: dev's mirror)
 *   --stands   a JSON file of stands to read instead of the five below, in their
 *              shape (T-2095 reads its alley stands this way)
 *
 * The rig is `woodpile_shots.mjs`'s and the levels are `measure_detail_ceilings.mjs`'s
 * (`setDetail` through `detailOrder` on one boot). At each stand it reads the whole
 * frame (`stats()`), the sward's own share (`flora.stats`), the time one
 * production `step()` takes to the end of the GPU's work, and the JS heap after a
 * forced collection. It is `measure_detail_ceilings.mjs --stepped`'s settle (T-2015):
 * the loop is stopped after boot and each stand is settled by two `step()` calls,
 * because the sward rebuilds synchronously inside one. Frame time on a software
 * rasteriser is a RELATIVE figure: read two trees against each other, never against
 * a real GPU. `--levels full,balanced` narrows the sweep so one call fits the
 * 600 s foreground ceiling.
 *
 * The stands are inside the settled-town community as committed today (its
 * polygon at the forks — T-2084 grows it over the whole town): Lake Street at
 * Market, the Green Tree's corner, a back lot behind the Lake Street row, the
 * forks, and the scene's open aerial.
 */
import { createServer } from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import { mkdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = execSync('npm root -g').toString().trim();
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const opt = (k, d = null) => (argv.includes(k) ? argv[argv.indexOf(k) + 1] : d);
const ROOT = path.resolve(opt('--root', path.join(HERE, '..', '..', '..', 'site', '4d')));
const AGAINST = opt('--against') ? path.resolve(opt('--against')) : null;
const OUT = path.resolve(opt('--out', '/tmp/turf-shots'));
const SHOTS = !argv.includes('--no-shots');
const VIEWPORTS = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const VP = opt('--viewport', 'desktop');
const LEVELS = opt('--levels') ? opt('--levels').split(',') : null;
mkdirSync(OUT, { recursive: true });

const DEFAULT_STANDS = [
  { id: 'lake_market', anchor: 'lake_market', label: 'Lake Street at Market, a road edge' },
  { id: 'green_tree', anchor: 'green_tree', label: 'the Green Tree, a storefront corner' },
  { id: 'back_lot', label: 'a back lot behind the Lake Street row, looking south',
    pose: { local_e: 100, local_n: -142, yaw_deg: 0, pitch_deg: -6 } },
  { id: 'forks', anchor: 'forks', label: 'the forks' },
  { id: 'from_above', anchor: 'from_above', label: 'the open aerial', fly: true },
];
const STANDS = opt('--stands')
  ? JSON.parse(await readFile(path.resolve(opt('--stands')), 'utf8')) : DEFAULT_STANDS;

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.svg': 'image/svg+xml',
  '.jpg': 'image/jpeg', '.webp': 'image/webp', '.ktx2': 'image/ktx2',
  '.geojson': 'application/json', '.webmanifest': 'application/manifest+json',
};
function serve(root) {
  const server = createServer(async (req, res) => {
    const url = new URL(req.url, 'http://x');
    let file = path.join(root, decodeURIComponent(url.pathname));
    try {
      if (file.endsWith('/')) file = path.join(file, 'index.html');
      const body = await readFile(file);
      res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
      res.end(body);
    } catch {
      res.writeHead(404).end('nope');
    }
  });
  return new Promise((r) => server.listen(0, () => r(server)));
}

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--js-flags=--expose-gc',
    '--enable-precise-memory-info'],
});

async function sweep(root, tag) {
  const server = await serve(root);
  const page = await browser.newPage({ viewport: VIEWPORTS[VP], deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.addInitScript(() => localStorage.setItem('chicago4d.entered', '1'));
  page.setDefaultTimeout(300000);
  await page.goto(`http://127.0.0.1:${server.address().port}/walk/?year=1835`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 300000 });
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      if (/got it|^\s*enter chicago\s*$/i.test(b.textContent ?? '')) b.click();
    }
    const style = document.createElement('style');
    style.textContent = 'body > *:not(#view) { visibility: hidden !important; }';
    document.head.appendChild(style);
  });
  const levels = (await page.evaluate(() => {
    window.__chicago4d.renderer.setAnimationLoop(null);
    return window.__chicago4d.detailOrder;
  })).filter((l) => !LEVELS || LEVELS.includes(l));
  const rows = [];
  for (const level of levels) {
    await page.evaluate((l) => window.__chicago4d.setDetail(l), level);
    for (const st of STANDS) {
      await page.evaluate((s) => {
        const a = window.__chicago4d;
        if (s.anchor) a.goTo(s.anchor);
        else { a.setFly(false); a.walker.teleport(s.pose); }
      }, st);
      const r = await page.evaluate(async () => {
        const a = window.__chicago4d;
        const gl = a.renderer.getContext();
        // readPixels, not finish(): only a read-back makes the renderer process
        // wait for the GPU process to have drawn the frame.
        const px = new Uint8Array(4);
        const sync = () => gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
        a.step(); a.step(); sync();
        const t0 = performance.now();
        a.step(); sync();
        const frameMs = performance.now() - t0;
        globalThis.gc?.();
        const s = a.stats();
        const f = a.flora?.stats ?? {};
        return {
          triangles: s.triangles, calls: s.drawCalls,
          floraTriangles: f.triangles ?? null, floraCalls: f.drawCalls ?? null,
          floraSets: f.sets ?? null, turf: f.turf ?? null,
          frameMs,
          heapMB: performance.memory ? performance.memory.usedJSHeapSize / 1048576 : null,
        };
      });
      if (SHOTS) {
        await page.screenshot({ path: path.join(OUT, `${VP}-${level}-${st.id}-${tag}.jpg`),
          type: 'jpeg', quality: 84 });
      }
      rows.push({ level, stand: st.id, ...r });
      console.log(`${tag.padEnd(6)} ${VP} ${level.padEnd(8)} ${st.id.padEnd(11)} `
        + `tris ${r.triangles} calls ${r.calls} flora ${r.floraTriangles}/${r.floraCalls} `
        + `frame ${r.frameMs.toFixed(0)} ms heap ${r.heapMB?.toFixed(1)} MB`);
    }
  }
  await page.close();
  server.close();
  return { root, errors, rows };
}

const report = { viewport: VP, levels: LEVELS, stands: STANDS,
  after: await sweep(ROOT, 'after') };
if (AGAINST) report.before = await sweep(AGAINST, 'before');
await writeFile(opt('--json', path.join(OUT, `report-${VP}.json`)), JSON.stringify(report, null, 2));
if (report.before) {
  console.log('\nstand / level           flora tris before -> after   total tris delta   calls   frame ms');
  for (const a of report.after.rows) {
    const b = report.before.rows.find((x) => x.level === a.level && x.stand === a.stand);
    if (!b) continue;
    console.log(`${(`${a.stand} ${a.level}`).padEnd(24)} ${String(b.floraTriangles).padStart(9)} -> `
      + `${String(a.floraTriangles).padEnd(9)} ${String(a.triangles - b.triangles).padStart(10)}   `
      + `${b.calls}->${a.calls}   ${b.frameMs.toFixed(0)}->${a.frameMs.toFixed(0)}`);
  }
}
for (const t of ['after', 'before']) {
  if (report[t]?.errors.length) console.log(`${t} pageerrors:`, report[t].errors.slice(0, 3));
}
await browser.close();
