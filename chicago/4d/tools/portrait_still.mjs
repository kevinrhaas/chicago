/**
 * portrait_still.mjs — the fitted-face still a person's card shows beside their portrait (T-3413).
 *   node tools/portrait_still.mjs [person_id …]      (default: every data/humans/variation/portraits/*.json)
 *
 * For each portrait record with a `card` block, it serves chicago/4d, opens
 * tools/human_variation_lineup.html on the record's `card.body` with only that person (their
 * persons.json row: age and the fitted face), turned to the fit's own camera yaw, hair left out
 * where the record says so, and writes `card.model` as a JPEG the size of `card.portrait`.
 * It also writes `card.model`'s sidecar `<name>.json` naming the sha256 of the fit file it was
 * made from, so tools/fit_portrait_face.py --check can refuse a still a later fit left behind.
 */
import { createServer } from 'node:http';
import { readFile, writeFile, readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try { ns = await import('playwright'); } catch {
    const root = execSync('npm root -g').toString().trim();
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PORTRAITS = path.join(ROOT, 'data/humans/variation/portraits');
const want = process.argv.slice(2);
const people = want.length ? want
  : (await readdir(PORTRAITS)).filter((f) => f.endsWith('.json')).map((f) => f.slice(0, -5));

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.wasm': 'application/wasm', '.png': 'image/png', '.jpg': 'image/jpeg', '.ktx2': 'image/ktx2' };
const server = createServer(async (req, res) => {
  const file = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  try { const body = await readFile(file); res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' }); res.end(body); }
  catch { res.writeHead(404).end('nope'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
let bad = 0;
for (const person of people) {
  const rec = JSON.parse(await readFile(path.join(PORTRAITS, `${person}.json`), 'utf8'));
  const card = rec.card;
  if (!card) continue;
  const fitPath = path.join(ROOT, 'data/humans/variation/fits', `${person}.json`);
  const fitBytes = await readFile(fitPath);
  const fit = JSON.parse(fitBytes);
  const [w, h] = card.size_px;
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  const q = new URLSearchParams({ asset: card.body, keys: person, view: 'faces', aim: 'head', labels: '0',
    yaw: String(fit.fit.camera.yaw_deg), bg: card.background, dist: String(card.distance_m), look: String(card.aim_above_head_m),
    ...(card.hide ? { hide: card.hide } : {}), ...(card.dress ? { dress: '1' } : {}) });
  await page.goto(`${base}/tools/human_variation_lineup.html?${q}`);
  await page.waitForFunction(() => window.__lineupReady === true, null, { timeout: 240000 });
  const applied = await page.evaluate(() => window.__variations?.[0] ?? null);
  if (errors.length || !applied?.applied || applied.grade !== fit.grade) {
    console.log(`FAIL ${person}: the still did not draw the fitted face`, errors, applied?.grade);
    bad++; await page.close(); continue;
  }
  const out = path.join(ROOT, card.model);
  await page.screenshot({ path: out, type: 'jpeg', quality: 82, timeout: 240000 });
  await writeFile(out.replace(/\.jpg$/, '.json'), JSON.stringify({
    person_id: person, ticket: 'T-3413', generated_by: 'tools/portrait_still.mjs',
    fit: path.relative(ROOT, fitPath), fit_sha256: createHash('sha256').update(fitBytes).digest('hex'),
    body: card.body, yaw_deg: fit.fit.camera.yaw_deg,
  }, null, 1) + '\n');
  console.log(`wrote ${card.model} (${w}x${h}) from ${path.relative(ROOT, fitPath)}`);
  await page.close();
}
await browser.close();
server.close();
process.exit(bad ? 1 : 0);
