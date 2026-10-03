#!/usr/bin/env node
// T-2041: time every available jaunt's primary path on the PUBLISHED mirror.
//
// Each jaunt is started in the real walkthrough at a mode, and every leg is ridden by
// the travel controller itself (`travel.simulate`, the harness path of tick()) until it
// arrives. The measured time is the opening's read time, plus each visited stop's read
// and action time, plus the simulated seconds of every ride. Beside it stands the
// estimate the menu would print (`jaunts.state.estimate` at the first stop), so a
// reader can see the measurement and the displayed figure disagree, and by how much.
//
//   node tools/time_jaunts.mjs [--modes recommended,fly,instantly] [--only id,id]
//                              [--out docs/measurements/jaunt-timing.json]
//
// The primary path is the stop list in authored order, the same list the estimate
// prices. At a stop with choices the walk takes the choice that leads to the next
// listed stop (else the first), and a run whose visited stops differ from the list is
// reported, never silently counted. Exits 1 when a ride stalls, a jaunt cannot start,
// the page throws, or a recommended-mode path falls outside 3-6 minutes.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url), { chromium } = require('playwright');

const arg = (name, fallback) => {
  const i = process.argv.indexOf(`--${name}`);
  return i > 0 ? process.argv[i + 1] : fallback;
};
const modes = arg('modes', 'recommended,fly,instantly').split(',');
const only = arg('only', '') ? arg('only').split(',') : null;
const outFile = arg('out', 'docs/measurements/jaunt-timing.json');
// --merge a.json,b.json: combine runs taken in separate processes (the whole library
// does not fit one 600 s foreground call) and judge them as one.
const merge = arg('merge', '') ? arg('merge').split(',') : null;
// --also other.json: a second viewport's recommended-mode readings, shown beside these.
const also = arg('also', '') ? JSON.parse(fs.readFileSync(arg('also'))) : null;
// --continue: keep the runs already in --out and take only the missing ones. Every run
// is written the moment it finishes, so a process stopped at the foreground cap loses
// at most the ride it was on.
const resume = process.argv.includes('--continue') && fs.existsSync(outFile) ? JSON.parse(fs.readFileSync(outFile)) : null;
// The phone is the default: the clock is simulated, so a viewport moves a reading only
// through where each stop is framed from (a few seconds a path), and the phone is a
// real visitor's screen that the software renderer draws several times faster than
// the desktop one. `--viewport 1280x800` takes the desktop reading.
const [width, height] = arg('viewport', '390x780').split('x').map(Number);
const phone = width < 600;
const MIN_S = 180, MAX_S = 360;

const root = path.resolve('../../site/4d');
if (!fs.existsSync(path.join(root, 'walk/index.html'))) {
  console.error('JAUNT TIMING FAIL — no published mirror at site/4d; run ./tools/publish.sh first');
  process.exit(1);
}
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'data/sidecars/1835/jaunts/catalog.json')));
const rows = catalog.jaunts.filter(row => row.availability === 'available' && (!only || only.includes(row.id)));
fs.mkdirSync(path.dirname(outFile), { recursive: true });
const results = [...resume?.results ?? []], failures = (resume?.runFailures ?? []).filter(f => resume.results.some(r => f.startsWith(`${r.id} @ ${r.mode}:`))), errors = [...resume?.pageErrors ?? []];
let viewport = `${width}x${height}`;
const save = () => fs.writeFileSync(outFile, JSON.stringify({ viewport, modes, results, runFailures: failures, pageErrors: errors }, null, 2) + '\n');
if (merge) {
  for (const file of merge) {
    const part = JSON.parse(fs.readFileSync(file));
    results.push(...part.results); failures.push(...part.runFailures); errors.push(...part.pageErrors);
    if (part.viewport !== merge.viewport) merge.viewport = merge.viewport ? 'mixed' : part.viewport;
  }
  viewport = merge.viewport;
  if (merge.length) modes.splice(0, modes.length, ...new Set(merge.flatMap(f => JSON.parse(fs.readFileSync(f)).modes)));
} else await measure();
const runFailures = [...failures];

async function measure() {
  const types = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.json': 'application/json', '.glb': 'model/gltf-binary' };
  const server = http.createServer((req, res) => {
    const pathname = new URL(req.url, 'http://local').pathname;
    const file = path.join(root, pathname.endsWith('/') ? pathname + 'index.html' : pathname);
    fs.readFile(file, (err, bytes) => { res.writeHead(err ? 404 : 200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' }); res.end(err ? 'Not found' : bytes); });
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
  try {
    const context = await browser.newContext({ viewport: { width, height }, hasTouch: phone, isMobile: phone, reducedMotion: 'reduce' });
    const page = await context.newPage();
    page.setDefaultTimeout(120000);
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/walk/?year=1835&seed=1279`);
    await page.waitForFunction(() => window.__chicago4d?.welcome?.state === 'welcome', {}, { timeout: 180000 });
    for (const row of rows) {
      for (const wanted of modes) {
        const mode = wanted === 'recommended' ? row.default_mode : wanted;
      if (results.some(r => r.id === row.id && r.mode === mode)) continue;
        const t0 = Date.now();
        const run = await page.evaluate(async ({ id, mode }) => {
          const api = __chicago4d, state = () => api.jaunts.state;
          const settle = async test => {
            for (let i = 0; i < 600 && !test(); i++) await new Promise(r => setTimeout(r, 25));
            return test();
          };
          if (!await api.jaunts.start(id, { mode })) return { error: 'did not start' };
          if (!await settle(() => state()?.phase === 'atStop')) return { error: `start ended in ${state()?.phase}` };
          const jaunt = state().jaunt, listed = jaunt.stops.map(s => s.id);
          const estimate = state().estimate?.seconds ?? null, approx = !!state().estimate?.approx;
          const content = { opening: jaunt.opening?.read_s ?? 0, stops: 0 }, legs = [], visited = [];
          for (let guard = 0; guard < 20 && state().phase !== 'outcome'; guard++) {
            const s = state(), stop = jaunt.stops.find(x => x.id === s.visited[s.stopIndex].id);
            visited.push(stop.id); content.stops += (stop.read_s ?? 0) + (stop.action_s ?? 0);
            const after = listed[listed.indexOf(stop.id) + 1];
            // Prefer the choice that leads on to the next listed stop; a choice the stop
            // refuses (a `when` the purse cannot meet) leaves it where it was, so fall
            // through to the next one.
            const ordered = [...stop.choices ?? []].sort((a, b) => (b.next === after) - (a.next === after));
            const here = s.visited.length;
            for (const choice of ordered.length ? ordered : [null]) {
              if (choice) api.jaunts.choose(choice.id);
              api.jaunts.next();
              if (state().phase !== 'atStop' || state().visited.length !== here) break;
            }
            if (state().phase === 'outcome') break;
            if (state().phase !== 'travelling') {
              if (!await settle(() => ['travelling', 'atStop', 'outcome'].includes(state().phase))) return { error: `${stop.id}: next left ${state().phase}` };
            }
            if (state().phase !== 'travelling') continue;
            let seconds = 0, laps = 0, distance = 0, last = [api.walker.state.e, api.walker.state.n];
            while (api.travel.state.phase !== 'idle' && laps < 3) {
              const ride = api.travel.simulate(600); seconds += ride.seconds; laps++;
              for (const [e, n] of ride.samples) { distance += Math.hypot(e - last[0], n - last[1]); last = [e, n]; }
            }
            if (api.travel.state.phase !== 'idle') return { error: `${stop.id}: ride still ${api.travel.state.phase} after ${Math.round(seconds)} s` };
            if (!await settle(() => ['atStop', 'outcome'].includes(state().phase))) return { error: `${stop.id}: arrival left ${state().phase}` };
            legs.push({ from: stop.id, seconds: Math.round(seconds * 10) / 10, metres: Math.round(distance) });
          }
          const done = state().phase === 'outcome';
          api.jaunts.end();
          await settle(() => !api.jaunts.state?.jaunt);
          return { listed, visited, done, estimate, approx, content, legs };
        }, { id: row.id, mode });
        if (run.error) { failures.push(`${row.id} @ ${mode}: ${run.error}`); console.log(`  FAIL ${row.id} @ ${mode}: ${run.error}`); save(); continue; }
        const travel = run.legs.reduce((n, leg) => n + leg.seconds, 0);
        const measured = run.content.opening + run.content.stops + travel;
        const entry = { id: row.id, title: row.title, mode, recommended: mode === row.default_mode, ...run,
          travel_s: Math.round(travel), measured_s: Math.round(measured), estimate_s: run.estimate == null ? null : Math.round(run.estimate) };
        results.push(entry);
        if (!run.done) failures.push(`${row.id} @ ${mode}: never reached an outcome`);
        if (run.visited.join() !== run.listed.join()) failures.push(`${row.id} @ ${mode}: walked ${run.visited.join(' > ')}, listed ${run.listed.join(' > ')}`);
        save();
      console.log(`  ${row.id.padEnd(24)} ${mode.padEnd(9)} measured ${(measured / 60).toFixed(2)} min (travel ${Math.round(travel)} s) · estimate ${run.estimate == null ? '—' : (run.estimate / 60).toFixed(2)} min · ${((Date.now() - t0) / 1000).toFixed(1)} s wall`);
      }
    }
    await context.close();
  } finally {
    await browser.close(); server.close();
  }
}
for (const row of rows) {
  if (!results.some(r => r.id === row.id)) { if (merge) failures.push(`${row.id}: not measured`); continue; }
  const at = mode => results.find(r => r.id === row.id && r.mode === mode);
  const rec = at(row.default_mode);
  if (!rec) continue;
  if (modes.includes('recommended') && (rec.measured_s < MIN_S || rec.measured_s > MAX_S)) failures.push(`${row.id}: recommended ${row.default_mode} measures ${(rec.measured_s / 60).toFixed(2)} min, outside 3-6`);
  for (const fast of ['fly', 'instantly']) {
    const r = at(fast);
    if (r && fast !== row.default_mode && r.measured_s >= rec.measured_s) failures.push(`${row.id}: ${fast} (${r.measured_s} s) is not faster than ${row.default_mode} (${rec.measured_s} s)`);
  }
}
for (const e of errors) failures.push(`pageerror: ${e}`);
fs.writeFileSync(outFile, JSON.stringify({ viewport, seed: 1279, modes, bounds_s: [MIN_S, MAX_S],
  results, runFailures, failures, pageErrors: errors }, null, 2) + '\n');
fs.writeFileSync(outFile.replace(/\.json$/, '.md'), report());
for (const f of failures) console.error(`  FAIL ${f}`);
console.log(`JAUNT TIMING ${failures.length ? 'FAIL' : 'PASS'} — ${results.length} run(s) over ${rows.length} jaunt(s), ${failures.length} finding(s) → ${outFile}`);
process.exit(failures.length ? 1 : 0);

// The table a reader checks: one row per jaunt, recommended mode first, minutes to two
// places, and the figure the menu actually prints (travel-estimate.js formatEstimate).
function report() {
  const min = s => s == null ? '—' : (s / 60).toFixed(2);
  const shown = s => s == null ? '—' : `about ${Math.round(s / 30) / 2}`;
  const lines = [`# Jaunt timing — every primary path ridden on the published mirror`, '',
    `Written by \`node tools/time_jaunts.mjs\` (T-2041 and its children). Viewport ${viewport}, seed 1279, default pace settings.`,
    `Each leg is ridden by the travel controller itself (\`travel.simulate\`, 30 steps a simulated second) until it arrives;`,
    `**measured** = opening read + every visited stop's read and action time + the simulated seconds of every ride.`,
    `**estimate** is \`jaunts.state.estimate\` at the first stop — the figure the menu rounds to the half minute.`,
    `The band is ${MIN_S / 60}–${MAX_S / 60} minutes at the recommended mode; Fly and Instantly must each be faster.`, '',
    `| Jaunt | Recommended | Stops | Content s | Travel s | Measured min | Estimate min | Menu says | Fly min | Instantly min | ${also ? `${also.viewport} min | ` : ''}Verdict |`,
    `|---|---|---:|---:|---:|---:|---:|---|---:|---:|${also ? '---:|' : ''}---|`];
  const ordered = rows.map(row => ({ row, rec: results.find(r => r.id === row.id && r.mode === row.default_mode) }))
    .filter(x => x.rec).sort((a, b) => b.rec.measured_s - a.rec.measured_s);
  for (const { row, rec } of ordered) {
    const at = mode => results.find(r => r.id === row.id && r.mode === mode)?.measured_s;
    const other = also?.results.find(r => r.id === row.id && r.mode === row.default_mode)?.measured_s;
    const inBand = rec.measured_s >= MIN_S && rec.measured_s <= MAX_S;
    const verdict = inBand ? 'in band' : `**${rec.measured_s > MAX_S ? 'over' : 'under'} by ${Math.abs(rec.measured_s - (rec.measured_s > MAX_S ? MAX_S : MIN_S))} s**`;
    lines.push(`| ${row.id} | ${row.default_mode} | ${rec.visited.length} | ${Math.round(rec.content.opening + rec.content.stops)} | ${rec.travel_s} | ${min(rec.measured_s)} | ${min(rec.estimate_s)} | ${shown(rec.estimate_s)} | ${min(at('fly'))} | ${min(at('instantly'))} | ${also ? `${min(other)} | ` : ''}${verdict} |`);
  }
  const over = ordered.filter(x => x.rec.measured_s > MAX_S).length, under = ordered.filter(x => x.rec.measured_s < MIN_S).length;
  lines.push('', `${ordered.length} jaunts measured: ${ordered.length - over - under} in band, ${over} over, ${under} under.`);
  if (failures.length) lines.push('', '## Findings', '', ...failures.map(f => `- ${f}`));
  return lines.join('\n') + '\n';
}
