#!/usr/bin/env node
/**
 * street_edge_review.mjs — the street edge's fixed review rig (T-1815).
 *
 *   node tools/street_edge_review.mjs <mirror-root> <out-dir> [--tag before|after]
 *                                     [--viewport desktop|mobile|both] [--detail full]
 *
 * `<mirror-root>` is the directory that HOLDS a published `4d/` (the repo's
 * `site/`, or a copy of it taken before a change). The page is the published
 * walkthrough, `/4d/walk/?year=1835`, so what is judged is what ships.
 *
 * Four stands, chosen so a forwarding frontage, a store and a tavern and a
 * smithy are seen under ONE camera and ONE light (T-1211's benchmark asks for
 * exactly that comparison):
 *
 *   lake-trades   Lake Street at Dole's warehouse, looking south: Dole's wagon
 *                 apron, Mason's smithy tie rail and bare ground, the walk.
 *   lake-close    the same front from 2 m, pitched down onto the boards.
 *   tavern        the Mansion House across Lake: mounting block and stoop.
 *   store-stoops  the row of store stoops on Lake's north side at Dearborn.
 *
 * Each stand is shot at the walker's own eye height with the animation clock
 * held, the chrome hidden, and `__chicago4d.stats()` read on the frame, so a
 * before/after pair differs only by the tree it was served from. It writes
 * `<tag>-<stand>-<viewport>.jpg` and `<tag>-stats.json`, and exits 1 on any
 * page error or console error.
 */
import { createServer } from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import { mkdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
import path from 'node:path';

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

const argv = process.argv.slice(2);
const flag = (name, dflt) => {
  const i = argv.indexOf(name);
  return i >= 0 ? argv[i + 1] : dflt;
};
const positional = argv.filter((a, i) => !a.startsWith('--') && !argv[i - 1]?.startsWith('--'));
const ROOT = path.resolve(positional[0] ?? '../../site');
const OUT = path.resolve(positional[1] ?? '/tmp/street-edge');
const TAG = flag('--tag', 'after');
const DETAIL = flag('--detail', 'full');
const VIEW = flag('--viewport', 'both');
mkdirSync(OUT, { recursive: true });

const VIEWPORTS = {
  desktop: { width: 1280, height: 800 },
  mobile: { width: 390, height: 780 },
};

/** The stands: local ENU, compass yaw, pitch down in degrees. */
const STANDS = [
  ['lake-trades', { local_e: 727.0, local_n: -112.5, yaw_deg: 185, pitch_deg: -9 }],
  ['lake-close', { local_e: 721.0, local_n: -118.2, yaw_deg: 205, pitch_deg: -36 }],
  ['tavern', { local_e: 716.0, local_n: -113.5, yaw_deg: 10, pitch_deg: -12 }],
  ['store-stoops', { local_e: 595.5, local_n: -124.6, yaw_deg: 120, pitch_deg: -16 }],
];

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.geojson': 'application/json', '.woff2': 'font/woff2',
  '.webmanifest': 'application/manifest+json',
};
const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  let file = path.join(ROOT, decodeURIComponent(url.pathname));
  try {
    if (file.endsWith('/')) file = path.join(file, 'index.html');
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404).end('nope');
  }
});
await new Promise((r) => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'],
});
const errors = [];
const stats = {};
for (const [vp, size] of Object.entries(VIEWPORTS)) {
  if (VIEW !== 'both' && VIEW !== vp) continue;
  const page = await browser.newPage({ viewport: size, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => errors.push(`${vp}: ${e}`));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(`${vp} console: ${m.text()}`); });
  await page.addInitScript((d) => {
    localStorage.setItem('chicago4d.detail', d);
    localStorage.setItem('chicago4d.entered', '1');
  }, DETAIL);
  page.setDefaultTimeout(240000);
  await page.goto(`${base}/4d/walk/?year=1835`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000 });
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      if (/got it|^\s*enter chicago\s*$/i.test(b.textContent ?? '')) b.click();
    }
    window.__chicago4d.setAnimationHold?.(true);
  });
  await page.waitForTimeout(600);
  // The chrome is hidden so the frame is the render and not the overlay.
  await page.addStyleTag({
    content: 'body > *:not(canvas):not(#view):not(main) { visibility: hidden !important; }'
      + ' #hud, .hud, #help, .card, .popup, .toast, header, nav, footer { visibility: hidden !important; }',
  });
  for (const [name, pose] of STANDS) {
    await page.evaluate((t) => {
      const api = window.__chicago4d;
      api.setFly(false);
      api.walker.teleport(t);
    }, pose);
    await page.waitForTimeout(1500);
    const s = await page.evaluate(() => window.__chicago4d.stats());
    stats[`${name}-${vp}`] = { drawCalls: s.drawCalls, triangles: s.triangles, textures: s.textures, programs: s.programs };
    await page.screenshot({ path: path.join(OUT, `${TAG}-${name}-${vp}.jpg`), type: 'jpeg', quality: 82 });
  }
  // The layer's whole cost, wherever the camera stands: it is one material at
  // every detail tier, so its triangles are an upper bound on what it adds to
  // any stand's frame and its draw calls are its mesh count.
  const census = await page.evaluate(() => {
    const g = window.__chicago4d.frontage?.group;
    if (!g) return null;
    let triangles = 0;
    g.traverse((o) => {
      const pos = o.geometry?.getAttribute?.('position');
      if (pos) triangles += (o.geometry.index ? o.geometry.index.count : pos.count) / 3;
    });
    return { ...g.userData.census, layerTriangles: triangles, layerMeshes: g.children.length };
  });
  stats[`census-${vp}`] = census;
  await page.close();
}
await writeFile(path.join(OUT, `${TAG}-stats.json`), JSON.stringify({ detail: DETAIL, stats, errors }, null, 2));
console.log(JSON.stringify({ stats, errors: errors.slice(0, 10) }, null, 2));
await browser.close();
server.close();
process.exit(errors.length ? 1 : 0);
