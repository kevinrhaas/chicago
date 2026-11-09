/**
 * qa_person_find_t3521.mjs — Find this person and Go to house, for everyone (T-3521).
 *
 *   bash tools/publish.sh && node tools/qa_person_find_t3521.mjs [1812 1835 1904]
 *
 * The owner, 2026-11-08, on John Kinzie's and Jean Baptiste Chandonnai's 1812 cards: "i
 * could not get to him when i click find or his house", "a lot of people you cant click
 * find this person and go to them". Serves ../../site/4d, boots each scene on a desktop,
 * enters the town, and for every person in the scene's directory asks what their card asks:
 * Go to house (the building they lived or worked in) and, for anyone placed in town, Find
 * this person. Each ask must start a ride (or set the visitor down); a refusal is a failure.
 * Writes docs/RESEARCH/person-find-3521/<scene>.json and exits non-zero on any failure.
 */
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';

const root = process.cwd();
const require = createRequire(path.join(root, 'tools/qa.mjs'));
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }
const site = path.resolve(root, '../../site/4d');
const out = path.join(root, 'docs/RESEARCH/person-find-3521');
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp',
  '.glb': 'model/gltf-binary', '.ktx2': 'image/ktx2', '.svg': 'image/svg+xml', '.wasm': 'application/wasm' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try {
    if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
    res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const scenes = process.argv.slice(2).length ? process.argv.slice(2) : ['1812', '1835', '1904'];
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
let failed = 0;
try {
  for (const scene of scenes) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
    const page = await context.newPage();
    page.setDefaultTimeout(300000);
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto(`http://127.0.0.1:${server.address().port}/${scene}/`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 300000, polling: 1000 });
    await page.waitForFunction(() => window.__chicago4d?.welcome.state === 'welcome', null, { timeout: 300000, polling: 1000 });
    await page.evaluate(async () => {
      const a = __chicago4d;
      if (!a.welcome.enter('spawn')) throw Error('welcome entry failed');
      document.exitPointerLock?.();
      document.getElementById('control-help-gotit')?.click();
      // 1904's detail switch can outlast a run; the asks need the town, not the detail.
      await Promise.race([a.setDetail('balanced'), new Promise((r) => setTimeout(r, 60000))]);
    });
    await page.waitForFunction(() => document.getElementById('gate').hidden);
    // Let the people load and take their places.
    await page.waitForTimeout(Number(process.env.QA_SETTLE_MS ?? 45000));
    const result = await page.evaluate(async ([scene, mode]) => {
      const a = __chicago4d;
      const res = await fetch(new URL(`sidecars/${scene}/people.json`, document.baseURI.replace(/\/[^/]*$/, '/') + '../data/'), { cache: 'no-cache' }).catch(() => null);
      let dir = res?.ok ? await res.json() : null;
      if (!dir) dir = { people: [] };
      const said = [];
      const hudSay = a.hud?.say?.bind(a.hud);
      if (a.hud) a.hud.say = (t, ...r) => { said.push(String(t)); return hudSay?.(t, ...r); };
      a.setTravelMode?.(mode);
      const rides = [];
      const go = a.travel.go;
      a.travel.go = (t, cb) => { const v = go(t, cb); rides.push(!!v); return v; };
      const ask = async (fn) => {
        said.length = 0; rides.length = 0;
        a.travel.stop?.('qa');
        let v;
        try { v = await fn(); } catch (e) { return { ok: false, why: `threw ${e.message}` }; }
        a.travel.stop?.('qa');
        return { ok: rides.some(Boolean), value: String(v), rides: rides.slice(), said: said.slice() };
      };
      const rows = [];
      for (const r of dir.people) {
        const house = [r.lives_at, r.works_at].find((s) => s && a.registry.has(s)) ?? null;
        const row = { id: r.id, name: r.name, house, named: r.lives_at ?? r.works_at ?? null };
        row.go = house ? await ask(() => a.goToTarget({ kind: 'structure', id: house })) : { ok: false, why: 'no house in this scene' };
        row.placed = typeof a.placedInTown === 'function' ? a.placedInTown(r.id) : null;
        // Find is live on the card of someone placed in town now; anyone else's card greys it
        // and says why (T-3531), so it is asked only of them.
        if (row.placed) row.find = await ask(() => a.findPerson(r.id));
        rows.push(row);
      }
      return { scene, count: rows.length, rows };
    }, [scene, process.env.QA_MODE || 'walk']);
    result.errors = errors;
    const bad = result.rows.filter((r) => (r.house && !r.go.ok) || (r.find && !r.find.ok));
    const noHouse = result.rows.filter((r) => !r.house);
    result.summary = { people: result.count, placed: result.rows.filter((r) => r.placed).length,
      goFails: result.rows.filter((r) => r.house && !r.go.ok).length,
      findFails: result.rows.filter((r) => r.find && !r.find.ok).length, noHouse: noHouse.length };
    fs.writeFileSync(path.join(out, `${scene}.json`), JSON.stringify(result, null, 1));
    console.log(scene, JSON.stringify(result.summary), errors.length ? `pageerrors ${errors.length}` : '');
    for (const r of bad.slice(0, 15)) console.log('  FAIL', r.id, JSON.stringify({ go: r.go, find: r.find }));
    for (const r of noHouse.slice(0, 10)) console.log('  NOHOUSE', r.id, r.named);
    failed += bad.length;
    await context.close();
  }
} finally { await browser.close(); server.close(); }
process.exit(failed ? 1 : 0);
