#!/usr/bin/env node
/** T-1246. Published boot timings, real 100 ms paint heartbeat and geometry receipt.
 * --published --json: all 12 cold/warm viewport/tier cells; --quick: mobile light.
 * --phone: the phone profile, a 4x CPU throttle (network unthrottled; see T-2677).
 * --no-prebuilt-streets: refuse data/prebuilt/<year>/streets.* alone, so the page lays
 *   its own road (T-2710's before). Each row carries `streets`: the layer's wall time,
 *   its longest task and whether its surfaces came prebuilt.
 * --no-prebuilt-ground: refuse data/prebuilt/<year>/ground.* alone, so the page loads
 *   and cuts the ground GLB itself while the frontage still comes prebuilt (T-2693's
 *   before: dev as it was). Each row carries `terrain`: the phase, its longest task
 *   and whether its ground came prebuilt.
 * --no-prebuilt-base: refuse data/prebuilt/<year>/base.* alone, so the page lays and
 *   cuts its own distant base (T-2709's before). Every row carries `base`: the
 *   distant-base measure after frontage, its longest task and whether it came prebuilt.
 * --no-prebuilt: refuse data/prebuilt/, so the page builds frontage itself (T-2677's
 * before). Every row quotes the frontage layer's wall time, the longest task inside
 * it, and whether its timber came prebuilt.
 * --root PATH measures an untouched published baseline (five legacy milestones).
 * --compare PATH asserts geometry, roll, flora/tree stats and placement census.
 * Viewports emulate input/size, NOT phone CPU. Warm = repeat navigation/context.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { CENSUS } from './drawn_placement_census.mjs';
const here = path.dirname(fileURLToPath(import.meta.url));
export async function environment(root = path.resolve(here, '../../../site/4d')) {
  let pw;
  try { pw = await import('playwright'); } catch {
    pw = await import(path.join(execSync('npm root -g', { encoding: 'utf8' }).trim(), 'playwright/index.mjs'));
  }
  const types = { '.js': 'text/javascript', '.json': 'application/json', '.html': 'text/html', '.css': 'text/css', '.wasm': 'application/wasm' };
  const server = http.createServer((q, r) => {
    let p = path.resolve(root, '.' + decodeURIComponent(q.url.split('?')[0]));
    if (!p.startsWith(root + path.sep) && p !== root) { r.writeHead(403); r.end(); return; }
    if (q.url.split('?')[0].endsWith('/')) p += '/index.html';
    fs.readFile(p, (err, data) => { r.writeHead(err ? 404 : 200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); r.end(err ? '' : data); });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    const browser = await pw.chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
    return { browser, url: `http://127.0.0.1:${server.address().port}/walk/?year=1835`,
      async close() { await browser.close(); await new Promise(resolve => server.close(resolve)); } };
  } catch (err) { server.close(); throw err; }
}
export function observeBoot({ detail }) {
  localStorage.setItem('chicago4d.settings', JSON.stringify({ detail }));
  const probe = window.bootProbe = { tasks: [], beats: [], labels: [], events: [] };
  new PerformanceObserver(list => { for (const e of list.getEntries()) probe.tasks.push({ at: e.startTime, duration: e.duration }); }).observe({ type: 'longtask', buffered: true });
  let pending = false;
  const timer = setInterval(() => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => { pending = false; probe.beats.push(performance.now()); });
  }, 100);
  const attach = setInterval(() => {
    const boot = window.__chicago4d?.boot;
    if (!boot) return;
    clearInterval(attach);
    for (const type of ['phasestart', 'phaseprogress', 'phaseend', 'ready', 'error']) boot.on(type, e => probe.events.push(e));
    boot.on('ready', () => clearInterval(timer));
  }, 0);
  addEventListener('DOMContentLoaded', () => {
    const node = document.querySelector('#gate-sub');
    new MutationObserver(() => probe.labels.push({ at: performance.now(), text: node.textContent })).observe(node, { childList: true, subtree: true, characterData: true });
  });
}
export async function snapshot(page) {
  const d = await page.evaluate(async () => {
    const a = window.__chicago4d;
    a.renderer.setAnimationLoop(null);
    const hashes = {};
    for (const group of [a.flora.group, a.trees.group]) {
      const all = [];
      group.traverse(o => {
        if (o.geometry) {
          for (const [name, attr] of Object.entries(o.geometry.attributes)) all.push([o.name, name, attr.array]);
          if (o.geometry.index) all.push([o.name, 'index', o.geometry.index.array]);
        }
        if (o.instanceMatrix) all.push([o.name, 'instances', o.instanceMatrix.array.slice(0, o.count * 16)]);
      });
      // A stream already handed to the GPU may have released its array (T-2677 found it).
      hashes[group.name] = await Promise.all(all.filter(([, , arr]) => arr).map(async ([name, attr, arr]) => ({ name, attr,
        hash: Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new Uint8Array(arr.buffer, arr.byteOffset, arr.byteLength)))), length: arr.length })));
    }
    const fr = performance.getEntriesByName('frontage', 'measure')[0];
    const frontage = fr ? { ms: Math.round(fr.duration), startedAt: fr.startTime, prebuilt: a.frontage?.prebuilt ?? null } : null;
    const sm = performance.getEntriesByName('streets', 'measure')[0];
    const streets = sm ? { ms: Math.round(sm.duration), startedAt: sm.startTime, prebuilt: a.streetsPrebuilt ?? null } : null;
    const bm = performance.getEntriesByName('distant-base', 'measure')[0];
    const base = bm ? { ms: Math.round(bm.duration), startedAt: bm.startTime, prebuilt: a.terrainPrebuiltBase ?? null } : null;
    const tp = a.boot?.timings()?.find(p => p.id === 'terrain');
    const terrain = tp ? { ms: Math.round((tp.endedAt - tp.startedAt)), startedAt: tp.startedAt, prebuilt: a.terrainPrebuilt ?? null } : null;
    return { frontage, base, terrain, streets, roll: a.roll, flora: a.flora.stats, trees: a.trees.stats, hashes,
      probe: window.bootProbe, phases: a.boot?.timings(), readyAt: a.boot?.readyAt, renderedAt: a.boot?.renderedAt };
  });
  // The census reads drawn buffers, and since streams are released after upload
  // some are gone; a timing run records why instead of dying (T-2677). --compare
  // still needs it whole and fails on the difference.
  try { d.census = await page.evaluate(CENSUS); } catch (err) { d.census = { error: err.message.split('\n')[0] }; }
  const phase = d.phases?.find(p => p.id === 'flora');
  const start = phase?.startedAt ?? d.probe.labels.find(l => l.text === 'Planting the prairie…')?.at;
  const end = phase?.endedAt ?? d.probe.labels.at(-1)?.at;
  const beats = [start, ...d.probe.beats.filter(t => t > start && t < end), end];
  d.floraMaxPaintGapMs = Math.max(...beats.slice(1).map((t, i) => t - beats[i]));
  d.longestTaskMs = Math.max(0, ...d.probe.tasks.filter(t => t.at < (d.readyAt ?? end)).map(t => t.duration));
  if (d.terrain) {
    const { startedAt, ms } = d.terrain;
    d.terrain.longestTaskMs = Math.round(Math.max(0, ...d.probe.tasks
      .filter(t => t.at + t.duration > startedAt && t.at < startedAt + ms).map(t => t.duration)));
  }
  for (const part of [d.base, d.streets].filter(Boolean)) {
    const { startedAt, ms } = part;
    part.longestTaskMs = Math.round(Math.max(0, ...d.probe.tasks
      .filter(t => t.at + t.duration > startedAt && t.at < startedAt + ms).map(t => t.duration)));
  }
  if (d.frontage) {
    const { startedAt, ms } = d.frontage;
    d.frontage.longestTaskMs = Math.round(Math.max(0, ...d.probe.tasks
      .filter(t => t.at + t.duration > startedAt && t.at < startedAt + ms).map(t => t.duration)));
  }
  return d;
}
async function main() {
  const args = process.argv.slice(2), arg = name => args.includes(name) ? args[args.indexOf(name) + 1] : undefined;
  const env = await environment(arg('--root'));
  const phone = args.includes('--phone');
  const result = { measuredAt: new Date().toISOString(), machine: `${os.type()} ${os.release()} ${os.arch()} / ${os.cpus()[0].model}`, browser: env.browser.version(), conditions: `Headless Chromium; 390×780 touch and 1280×800; ${phone ? '4x CPU throttle (the phone profile), network unthrottled' : 'no CPU throttle'}; fresh context cold, repeat navigation warm${args.includes('--no-prebuilt') ? '; data/prebuilt/ refused' : ''}${args.includes('--no-prebuilt-ground') ? '; data/prebuilt/*/ground.* refused' : ''}${args.includes('--no-prebuilt-base') ? '; data/prebuilt/*/base.* refused' : ''}${args.includes('--no-prebuilt-streets') ? '; data/prebuilt/*/streets.* refused' : ''}.`, rows: [] };
  const baselineDoc = arg('--compare') && JSON.parse(fs.readFileSync(arg('--compare'), 'utf8'));
  const baseline = baselineDoc?.rows ?? baselineDoc;
  try {
    for (const device of args.includes('--quick') ? ['mobile'] : ['mobile', 'desktop']) {
      for (const detail of args.includes('--quick') ? ['light'] : ['light', 'balanced', 'full']) {
        const ctx = await env.browser.newContext({ viewport: device === 'mobile' ? { width: 390, height: 780 } : { width: 1280, height: 800 }, hasTouch: device === 'mobile' });
        await ctx.addInitScript(observeBoot, { detail });
        if (args.includes('--no-prebuilt-streets')) await ctx.route('**/data/prebuilt/*/streets.*', route => route.fulfill({ status: 404, body: '' }));
        if (args.includes('--no-prebuilt-ground')) await ctx.route('**/data/prebuilt/*/ground.*', route => route.fulfill({ status: 404, body: '' }));
        if (args.includes('--no-prebuilt-base')) await ctx.route('**/data/prebuilt/*/base.*', route => route.fulfill({ status: 404, body: '' }));
        if (args.includes('--no-prebuilt')) await ctx.route('**/data/prebuilt/**', route => route.fulfill({ status: 404, body: '' }));
        const page = await ctx.newPage();
        if (phone) await (await ctx.newCDPSession(page)).send('Emulation.setCPUThrottlingRate', { rate: 4 });
        for (const cache of ['cold', 'warm']) {
          await page.goto(env.url);
          await page.waitForFunction(() => window.__chicago4d?.ready, null, { timeout: phone ? 480000 : 180000 });
          await page.waitForTimeout(500);
          const row = { device, detail, cache, ...await snapshot(page) };
          if (baseline) {
            const b = baseline.find(r => r.device === device && r.detail === detail && r.cache === cache);
            assert.ok(b, `Missing baseline ${device}/${detail}/${cache}`);
            for (const key of ['hashes', 'roll', 'flora', 'trees', 'census']) assert.deepEqual(row[key], b[key], `${device}/${detail}/${cache} ${key} changed`);
            row.matchesUnsliced = true;
          }
          result.rows.push(row);
          if (!args.includes('--json')) console.log(`${device}/${detail}/${cache}: flora paint gap ${row.floraMaxPaintGapMs.toFixed(1)} ms; longest task ${row.longestTaskMs} ms\n`
            + (row.terrain ? `  terrain: ${row.terrain.ms} ms, longest task in it ${row.terrain.longestTaskMs} ms, ground ${row.terrain.prebuilt?.used ? 'prebuilt' : `cut here (${row.terrain.prebuilt?.why})`}\n` : '')
            + (row.base ? `  distant base: ${row.base.ms} ms after frontage, longest task in it ${row.base.longestTaskMs} ms, ${row.base.prebuilt?.used ? 'prebuilt' : `cut here (${row.base.prebuilt?.why})`}\n` : '')
            + (row.streets ? `  streets: ${row.streets.ms} ms, longest task in it ${row.streets.longestTaskMs} ms, ${row.streets.prebuilt?.used ? `prebuilt (${row.streets.prebuilt.layout})` : `laid here (${row.streets.prebuilt?.why})`}\n` : '')
            + (row.frontage ? `  frontage: ${row.frontage.ms} ms, longest task in it ${row.frontage.longestTaskMs} ms, ${row.frontage.prebuilt?.used ? 'prebuilt' : `built here (${row.frontage.prebuilt?.why})`}\n` : '')
            + row.phases?.map(p => `  ${p.id}: ${p.seconds?.toFixed(3)} s`).join('\n'));
        }
        await ctx.close();
      }
    }
    if (args.includes('--json')) console.log(JSON.stringify(result, null, 2));
    if (args.includes('--check')) for (const row of result.rows) if (row.device === 'mobile' && row.detail === 'light') assert.ok(row.floraMaxPaintGapMs <= 250, `flora heartbeat ${row.floraMaxPaintGapMs} > 250 ms`);
  } finally { await env.close(); }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
