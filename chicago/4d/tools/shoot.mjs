/**
 * shoot.mjs — put the camera somewhere and save a PNG, plus dump what the scene
 * actually contains at that moment.
 *
 * A diagnostic, not a gate. The smoke test asserts; this one looks. It exists
 * because the smoke test passed a scene the user could see was broken, and the
 * only way past that is to stop reading assertions and start reading pixels.
 *
 *   node tools/shoot.mjs <root-dir> <entry> <out-dir> [--detail full|balanced|light]
 *                                                     [--at e,n,yaw[,name]]
 *                                                     [--anchors id,id,…]
 *
 * `--anchors` stands at the 1835 scene's own named anchors (data/scenes/1835.json),
 * in the order given, one PNG each named for its anchor — so a walk is a list of
 * stands a visitor can also reach, not a set of coordinates typed into a command
 * (T-1970: the fort-to-Wolf-Point walk in docs/RESEARCH/shots/).
 */
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { mkdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
import path from 'node:path';

// Same resolution dance as the smoke test: playwright is a global install here,
// and it is CommonJS, so imported as ESM its exports land under `.default`.
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

// Flags may sit anywhere, so the positional arguments are read off the list
// with the flags and their values removed. Before this, `--at` after the output
// directory was fine and `--at` before it became the output directory.
const FLAGS = new Set(['--detail', '--at', '--anchors']);
const argv = process.argv.slice(2);
const positional = [];
const flags = {};
for (let i = 0; i < argv.length; i++) {
  if (FLAGS.has(argv[i])) { flags[argv[i]] = argv[++i]; continue; }
  positional.push(argv[i]);
}
const ROOT = path.resolve(positional[0] ?? '.');
const ENTRY = positional[1] ?? '/renderers/web/';
const OUT = path.resolve(positional[2] ?? '/tmp/shots');
const DETAIL = flags['--detail'] ?? 'full';
// `--at e,n,yaw[,name]` replaces the anchor set with ONE station, which is what
// an archetype before/after pair needs: the anchors stand where a visitor
// stands, and a plant community is somewhere else. K56.
const AT = flags['--at']
  ? (() => {
    const [e, n, yaw, name] = flags['--at'].split(',');
    return [[name || 'at', { e: Number(e), n: Number(n), yaw: Number(yaw ?? 0) }]];
  })()
  : null;
const ANCHORS = flags['--anchors']
  ? await (async () => {
    const scene = JSON.parse(await readFile(new URL('../data/scenes/1835.json', import.meta.url), 'utf8'));
    const byId = new Map((scene.anchors ?? []).map((a) => [a.id, a]));
    return flags['--anchors'].split(',').map((id) => {
      const a = byId.get(id);
      if (!a) throw new Error(`--anchors: no anchor "${id}" in data/scenes/1835.json`);
      const t = { e: a.local_e, n: a.local_n, yaw: a.yaw_deg };
      if (typeof a.pitch_deg === 'number') t.pitch_deg = a.pitch_deg;
      if (typeof a.altitude_m === 'number') t.altitude_m = a.altitude_m;
      return [id, t];
    });
  })()
  : null;
mkdirSync(OUT, { recursive: true });

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.svg': 'image/svg+xml',
  '.geojson': 'application/json', '.webmanifest': 'application/manifest+json',
};

const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  let file = path.join(ROOT, decodeURIComponent(url.pathname));
  try {
    if (file.endsWith('/')) file = path.join(file, 'index.html');
    const body = await readFile(file);
    res.writeHead(200, {
      'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream',
      'access-control-allow-origin': '*',
    });
    res.end(body);
  } catch {
    res.writeHead(404).end('nope');
  }
});
await new Promise((r) => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
page.on('console', (m) => { if (m.type() === 'error') errors.push(`console: ${m.text()}`); });

await page.addInitScript((d) => {
  localStorage.setItem('chicago4d.detail', d);
  localStorage.setItem('chicago4d.entered', '1');
}, DETAIL);

page.setDefaultTimeout(180000);
// The app resolves data as `../data/`, so the served root is the directory
// ABOVE the renderer and the entry path names it. Serving the renderer folder
// directly 404s every dataset — which is the published layout's own shape, and
// worth reproducing rather than working around.
await page.goto(`${base}${ENTRY}?year=1835`, { waitUntil: 'load' });
try {
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 180000 });
} catch (e) {
  const state = await page.evaluate(() => ({
    ready: window.__chicago4d?.ready,
    error: window.__chicago4d?.error,
    problems: (window.__chicago4d?.problems ?? []).slice(0, 15),
    gate: document.getElementById('gate-sub')?.textContent,
  }));
  console.log(JSON.stringify({ stalled: state, errors: errors.slice(0, 20) }, null, 2));
  await browser.close();
  server.close();
  process.exit(1);
}

const gate = await page.$('#gate button, .gate button');
if (gate) { await gate.click(); await page.waitForTimeout(1500); }

// What is actually in the scene, in world units, per rendered structure. This
// is the reading the smoke test never took: it measured the tallest building
// and called the town checked.
const audit = await page.evaluate(() => {
  const api = window.__chicago4d;
  return {
    stats: api.stats?.(),
    batches: api.buildings?.batches?.length ?? 0,
    bounds: api.buildings?.instanceBounds?.() ?? null,
  };
});

// The scene's own anchors, so the camera stands where a visitor would rather
// than in a field the reconstruction never claimed to fill.
const shots = [
  ['spawn-sauganash', { e: 107, n: -103, yaw: 180 }],
  ['lake-market', { e: 89.2, n: -110.4, yaw: 90 }],
  ['green-tree', { e: -159.7, n: -108.4, yaw: 45 }],
  ['forks', { e: -100, n: -28, yaw: 120 }],
  ['south-water', { e: 260, n: -95, yaw: 270 }],
  ['from-above', { e: 60, n: -330, yaw: 0, altitude_m: 175, pitch_deg: -45 }],
  ['high-above', { e: 60, n: -160, yaw: 0, altitude_m: 420, pitch_deg: -75 }],
];

// Dismiss the help card — it covers a quarter of every frame — and the welcome
// card, which since the start experience (T-1259) covers the middle of it and is
// not answered by `chicago4d.entered`: "Enter Chicago" is the visitor's own way in.
await page.evaluate(() => {
  for (const b of document.querySelectorAll('button')) {
    if (/got it|^\s*enter chicago\s*$/i.test(b.textContent ?? '')) b.click();
  }
});
await page.waitForTimeout(600);

for (const [name, { e, n, yaw, ...rest }] of AT ?? ANCHORS ?? shots) {
  await page.evaluate((t) => {
    const api = window.__chicago4d;
    // Altitude only survives in fly mode: the walker reconciles itself against
    // the intent every frame and snaps a grounded camera straight back down, so
    // a teleport with altitude_m and no fly silently lands you in the grass.
    api.setFly(typeof t.altitude_m === 'number');
    api.walker.teleport(t);
  }, { local_e: e, local_n: n, yaw_deg: yaw, ...rest });
  await page.waitForTimeout(900);
  await page.screenshot({ path: path.join(OUT, `${name}.png`) });
}

const { writeFile } = await import('node:fs/promises');
await writeFile(path.join(OUT, 'audit.json'),
  JSON.stringify({ audit, errors: errors.slice(0, 20) }, null, 2));
console.log(JSON.stringify({ stats: audit.stats, measured: Object.keys(audit.bounds ?? {}).length,
  errors: errors.slice(0, 10) }, null, 2));
await browser.close();
server.close();
