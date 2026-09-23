#!/usr/bin/env node
/**
 * probe_missing_host.mjs — induce the fault of T-1126 and read what the scene does.
 *
 * On 14 September 2026 the owner walked Dearborn Street and found the board
 * J. BATES, JR. / AUCTIONEER hanging at head height over an empty lot, two
 * lettered crates in the grass beside it, and no auction room between them. A
 * reload had the building back. The record was sound in every place it could
 * have dropped out of; one GLB out of ~380 had simply failed to fetch.
 *
 * That is a transient, and a transient cannot be gated — so this probe MAKES it
 * happen. It serves the published mirror, blocks exactly one structure's GLB at
 * the network, and reports three things:
 *
 *   1. whether the scene says so — the structure named, at error level, and the
 *      roll call short by one;
 *   2. whether the furniture came down with it — the board, the goods, the
 *      fence and the posts that hang off that wall;
 *   3. the same two readings with nothing blocked, as the control.
 *
 * It is a DEMONSTRATION, not part of the staged gate: it costs a second boot
 * and it deliberately breaks the page, which is not a thing the smoke's
 * "no unexpected loader problems" assertion can be asked to tolerate. Run it by
 * hand when this path changes.
 *
 *   node tools/probe_missing_host.mjs [structure_id]
 *
 * Exit 0 if the scene degraded honestly, 1 if it drew a false scene.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../../../site/chicago/4d');
const PORT = 8129;
const YEAR = process.env.SMOKE_YEAR || '1835';
const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
  '.css': 'text/css', '.glb': 'model/gltf-binary', '.bin': 'application/octet-stream',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.wasm': 'application/wasm', '.md': 'text/markdown',
};

if (!fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}

const { chromium } = await import('playwright');

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
await new Promise((r) => { server.listen(PORT, r); });
const base = `http://127.0.0.1:${PORT}/walk/?year=${YEAR}`;

// The same launch tools/smoke_renderer.mjs uses: without PW_EXECUTABLE this
// tool can only run on a machine carrying the exact browser build Playwright
// installed for itself, which is not the runner this project gates on.
const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
});

/** Boot once, optionally refusing one structure's asset, and read the scene. */
async function boot(blockId) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const consoleErrors = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  if (blockId) {
    // The asset path carries the structure id, which is how the mirror names a
    // bake. Aborting rather than 404ing is the closer analogue of the fault:
    // a dropped request, not a file the host denies exists.
    await page.route(`**/*${blockId}*.glb`, (route) => route.abort('failed'));
  }
  await page.goto(base, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, { timeout: 120000 });
  const read = await page.evaluate(() => ({
    roll: window.__chicago4d.roll,
    signs: window.__chicago4d.signage.census,
    yard: window.__chicago4d.yard.census,
    frontage: window.__chicago4d.frontage.census,
    problems: window.__chicago4d.problems.filter((p) => /did not load|drew no geometry|taken down/.test(p)),
  }));
  await page.close();
  return { ...read, consoleErrors };
}

/**
 * Which structure to break. Given one, use it; otherwise take the first
 * structure the SIGNAGE layer hangs a board on, because the dependent geometry
 * is the whole point and a structure with nothing hanging off it proves nothing.
 */
const control = await boot(null);
let target = process.argv[2];
if (!target) {
  const page = await browser.newPage();
  await page.goto(base, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, { timeout: 120000 });
  target = await page.evaluate(() => {
    const ids = new Set(window.__chicago4d.signage.spans.map((s) => s.id));
    for (const id of ids) {
      const r = window.__chicago4d.registry.get(id);
      if (r?.sidecar?.asset) return id;
    }
    return null;
  });
  await page.close();
}

console.log(`probe: breaking ${target}\n`);
const broken = await boot(target);

const line = (label, c, b) => console.log(
  `  ${label.padEnd(26)} control ${String(c).padStart(5)}   broken ${String(b).padStart(5)}`
  + `   ${b === c ? '' : `(${b - c})`}`);

console.log('WITH ONE STRUCTURE’S ASSET REFUSED AT THE NETWORK\n');
line('structures standing', control.roll.standing, broken.roll.standing);
line('structures expected', control.roll.expected, broken.roll.expected);
line('signboards hung', control.signs.boards, broken.signs.boards);
line('boards orphaned', control.signs.orphaned, broken.signs.orphaned);
line('yard frontages stood out', control.yard.frontages, broken.yard.frontages);
line('yard goods orphaned', control.yard.orphaned, broken.yard.orphaned);
line('frontage timber orphaned', control.frontage.orphaned, broken.frontage.orphaned);
console.log('\n  said out loud:');
for (const p of broken.problems.slice(0, 6)) console.log(`    - ${p}`);
for (const e of broken.consoleErrors.filter((e) => /structures drew/.test(e))) {
  console.log(`    ! ${e}`);
}

await browser.close();
server.close();

const failures = [];
if (broken.roll.standing !== control.roll.standing - 1) {
  failures.push('the roll call did not report the structure as missing');
}
if (!broken.roll.missing.includes(target)) failures.push('the roll call did not name it');
if (!broken.consoleErrors.some((e) => /structures drew/.test(e))) {
  failures.push('the shortfall was not reported at error level');
}
if (broken.signs.boards !== control.signs.boards - 1) {
  failures.push('the signboard was drawn on a wall that is not there');
}
if (control.roll.standing !== control.roll.expected) {
  failures.push('the CONTROL boot was already short — this reading attributes nothing');
}

console.log('');
if (failures.length) {
  for (const f of failures) console.log(`  FAIL  ${f}`);
  process.exit(1);
}
console.log('  PASS  the scene degraded into an absence, named it, and counted it.');
