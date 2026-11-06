#!/usr/bin/env node
// T-3405 QA: ride the first-fort tour on the PUBLISHED mirror in each mode with the
// travel controller's own harness path (travel.simulate), and report, per leg, the mode
// it actually travelled in, the simulated seconds and whether it arrived.
// Needs ./tools/publish.sh first; about four minutes a mode under swiftshader.
//   node tools/qa_fort_tour_walk_t3405.mjs [--modes default,fly,instantly] [--jaunt first-fort-dearborn-tour]
// `default` is the jaunt's own mode (its authored legs apply); any other is a visitor's pick.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const arg = (name, fallback) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : fallback; };
const modes = arg('modes', 'default').split(','), jauntId = arg('jaunt', 'first-fort-dearborn-tour');
const planOnly = process.argv.includes('--plan-only');
const root = path.resolve('../../site/4d');
const types = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.json': 'application/json', '.glb': 'model/gltf-binary' };
const server = http.createServer((req, res) => {
  const file = path.join(root, new URL(req.url, 'http://x').pathname.replace(/\/$/, '/index.html'));
  fs.readFile(file, (err, bytes) => { res.writeHead(err ? 404 : 200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' }); res.end(err ? 'Not found' : bytes); });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
let failed = 0;
try {
  const page = await (await browser.newContext({ viewport: { width: 390, height: 780 }, reducedMotion: 'reduce' })).newPage();
  const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.text().startsWith('leg ')) console.log('   ', m.text()); }); page.setDefaultTimeout(240000);
  await page.goto(`http://127.0.0.1:${server.address().port}/walk/?year=1812&seed=1279`);
  await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', {}, { timeout: 240000 });
  for (const wanted of modes) {
    const run = await page.evaluate(async ({ id, wanted, planOnly }) => {
      const api = __chicago4d, state = () => api.jaunts.state;
      const settle = async test => { for (let i = 0; i < 800 && !test(); i++) await new Promise(r => setTimeout(r, 25)); return test(); };
      const opts = wanted === 'default' ? {} : { mode: wanted, chosen: true };
      if (!await api.jaunts.start(id, opts)) return { error: 'did not start' };
      if (!await settle(() => state()?.phase === 'atStop')) return { error: `start ended in ${state()?.phase}` };
      const legs = [];
      for (let guard = 0; guard < 30 && state().phase !== 'outcome'; guard++) {
        const from = state().visited[state().stopIndex].id;
        api.jaunts.next();
        if (state().phase === 'outcome') break;
        if (!await settle(() => ['travelling', 'atStop', 'outcome'].includes(state().phase))) return { error: `${from}: next left ${state().phase}` };
        const to = state().visited[state().stopIndex]?.id, rideMode = api.travel.mode, phase0 = api.travel.state.phase;
        let seconds = 0, laps = 0;
        while (api.travel.state.phase !== 'idle' && laps < 12) { seconds += api.travel.simulate(planOnly ? 0 : 15).seconds; laps++; if (planOnly) break; await new Promise(r => setTimeout(r, 0)); }
        if (planOnly) { api.travel.stop('jaunt'); }
        await settle(() => ['atStop', 'outcome', 'paused'].includes(state().phase) || state().error);
        legs.push({ from, to, rideMode, phase0, seconds: Math.round(seconds * 10) / 10, end: state().phase, error: state().error || null,
          at: [Math.round(api.walker.state.e * 10) / 10, Math.round(api.walker.state.n * 10) / 10, Math.round(api.walker.state.altitude * 10) / 10] });
        if (state().phase !== 'atStop') { if (state().phase === 'paused' || state().error) { api.jaunts.straight?.(); await settle(() => state().phase === 'atStop'); } }
      }
      const done = state().phase === 'outcome'; api.jaunts.end();
      return { done, legs };
    }, { id: jauntId, wanted, planOnly });
    console.log(`\n== ${jauntId} @ ${wanted}`);
    if (run.error) { console.log('  ERROR', run.error); failed++; continue; }
    for (const l of run.legs) {
      const ok = l.end === 'atStop' || l.end === 'outcome';
      if (!ok) failed++;
      console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${l.from} -> ${l.to}: ${l.rideMode} (${l.phase0}) ${l.seconds}s end=${l.end}${l.error ? ' ' + l.error : ''} at ${l.at.join(',')}`);
    }
    console.log(`  done=${run.done}`);
  }
  if (errors.length) { console.log('pageerrors:', errors); failed++; }
} finally { await browser.close(); server.close(); }
process.exit(failed ? 1 : 0);
