#!/usr/bin/env node
/**
 * T-2829: THE OWNER'S PHONE AS A MODEL — the frame governor driven through a
 * simulated rAF loop fitted to the Fixed rows of his reading (T-2733), to name
 * the mechanism behind Adaptive's turn. A MODEL, NOT A READING: what it shows is
 * how the governor's own rules act on frames distributed like his, never how the
 * phone itself will read; that reading is his to take.
 *
 * The loop: rAF fires on a `vsync` grid; a drawn frame keeps the thread busy for
 * its cost (normal, `cost` ± `costSd` ms, seeded), so the next draw is the first
 * vsync after it; the reading's clock (`performance.now()` at the canvas draw, as
 * pacing-read.js times it) is the rAF time plus a dispatch delay with `jitterMs`
 * of sd. The governor sees the rAF times, as it does in main.js. A scale change is
 * a drawing-buffer resize; `resizeMs` adds that much to the frame it lands on —
 * NOT measured on any phone, so the table prints it at 0, 20 and 40 ms.
 *
 * Fitted on a 120 Hz grid, the turn's Fixed row comes back within a millisecond
 * on every column; on a 60 Hz grid no cost fits it (sd 8 against his 4.7), because
 * a median of 27 ms needs the 25 ms rung a 60 Hz display does not have.
 *
 *   node tools/model_governor_phone.mjs              the table (docs/measurements/T-2829-pacing-model.md)
 *   node tools/model_governor_phone.mjs --fit        re-derive the fitted devices
 *   node tools/model_governor_phone.mjs --governor <frame-governor.js>   another build's rules
 *   node tools/model_governor_phone.mjs --seconds 15 the longer run the readout now defaults to
 */
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const arg = (name, fallback) => {
  const i = process.argv.indexOf(name);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
};
const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
const governorFile = isMain ? path.resolve(arg('--governor', path.join(ROOT, 'renderers/web/js/frame-governor.js')))
  : path.join(ROOT, 'renderers/web/js/frame-governor.js');
const { createFrameGovernor } = await import(pathToFileURL(governorFile).href);
const { summarise } = await import(pathToFileURL(path.join(ROOT, 'renderers/web/js/pacing-read.js')).href);

/** The owner's rows (docs/measurements/t-2733-owner-phone-1835.json), [fixed, adaptive]. */
export const OWNER = {
  walk: [[163, 30.8, 6.0, 29, 43, 59, 34, 3], [161, 31.3, 5.0, 30, 41, 46, 47, 0]],
  turn: [[186, 27.1, 4.7, 27, 37, 44, 16, 0], [157, 32.0, 6.5, 32, 41, 73, 56, 3]],
  flight: [[162, 31.0, 3.9, 31, 38, 45, 42, 0], [161, 31.2, 5.0, 30, 41, 49, 48, 0]],
};
const COLS = ['draws', 'mean', 'sd', 'median', 'p95', 'max', 'over33', 'over50'];

/** The devices `--fit` finds for each move's Fixed row, on a 120 Hz grid. */
export const PHONE = {
  walk: { vsync: 1000 / 120, cost: 25, costSd: 5, jitterMs: 3 },
  turn: { vsync: 1000 / 120, cost: 23.5, costSd: 2, jitterMs: 3 },
  flight: { vsync: 1000 / 120, cost: 25.5, costSd: 2, jitterMs: 2 },
};

function rng(seed) {
  let s = seed >>> 0;
  return () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 2 ** 32; };
}
const gauss = (r) => Math.sqrt(-2 * Math.log(Math.max(1e-12, r()))) * Math.cos(2 * Math.PI * r());

/** One drive of `seconds` of moving at Fixed or Adaptive, as pacing-read.js times it. */
export function driveModel({ adaptive, seconds = 5, vsync, cost, costSd, jitterMs, resizeMs = 0, seed = 1,
  tier = 'light', make = createFrameGovernor }) {
  const r = rng(seed);
  const g = make({ enabled: adaptive, tier });
  let t = 0;
  let busyUntil = 0;
  let scale = g.scale;
  let resizes = 0;
  let paced = 0;
  const starts = [];
  while (t < seconds * 1000) {
    t += vsync;
    if (t < busyUntil || !g.shouldDraw(t)) continue;
    let hitch = 0;
    if (g.scale !== scale) { scale = g.scale; resizes += 1; hitch = resizeMs; }
    if (g.pace === 2) paced += 1;
    starts.push(t + Math.max(0, 2 + jitterMs * gauss(r)) + hitch);
    busyUntil = t + Math.max(vsync, Math.max(vsync / 2, cost + costSd * gauss(r)) + hitch) - 0.01;
    g.frameDrawn(t, true);
  }
  return { ...summarise(starts), resizes, paced };
}

/** The mean of each column over `seeds` drives. */
export function meanOf(o, seeds = 30) {
  const rows = Array.from({ length: seeds }, (_, i) => driveModel({ ...o, seed: i + 1 }));
  return Object.fromEntries([...COLS, 'resizes', 'paced'].map((k) => [k, rows.reduce((s, x) => s + x[k], 0) / seeds]));
}

const show = (x) => [x.draws.toFixed(0).padStart(5), ...['mean', 'sd', 'median', 'p95', 'max'].map((k) => x[k].toFixed(1).padStart(5)),
  x.over33.toFixed(0).padStart(4), x.over50.toFixed(1).padStart(4)].join(' ');
const owner = (row) => show(Object.fromEntries(COLS.map((k, i) => [k, row[i]])));

if (isMain && process.argv.includes('--fit')) {
  for (const [move, [fx]] of Object.entries(OWNER)) {
    const T = Object.fromEntries(COLS.map((k, i) => [k, fx[i]]));
    for (const vsync of [1000 / 120, 1000 / 60]) {
      let best = null;
      for (let cost = 14; cost <= 34; cost += 0.5) for (const costSd of [1, 2, 3, 4, 5, 6, 8]) for (const jitterMs of [1, 2, 3, 4]) {
        const a = meanOf({ adaptive: false, vsync, cost, costSd, jitterMs }, 6);
        const e = (a.mean - T.mean) ** 2 + ((a.sd - T.sd) / 0.5) ** 2 + (a.median - T.median) ** 2
          + ((a.p95 - T.p95) / 1.5) ** 2 + ((a.over33 - T.over33) / 5) ** 2 + ((a.draws - T.draws) / 6) ** 2;
        if (!best || e < best.e) best = { e, cost, costSd, jitterMs, a };
      }
      console.log(`${move.padEnd(6)} ${(1000 / vsync).toFixed(0)} Hz: misfit ${best.e.toFixed(1).padStart(5)}  cost ${best.cost}±${best.costSd}`
        + ` jitter ${best.jitterMs}  ->${show(best.a)}`);
    }
  }
} else if (isMain) {
  const seconds = Number(arg('--seconds', 5));
  console.log(`model of the owner's phone, ${seconds} s a drive, mean of 30 seeded drives; governor ${path.relative(ROOT, governorFile)}`);
  console.log('move    row                 draws  mean    sd   med   p95   max  >33  >50  resizes paced');
  for (const [move, [fx, ad]] of Object.entries(OWNER)) {
    const d = { ...PHONE[move], seconds };
    console.log(`${move.padEnd(7)} ${'owner fixed'.padEnd(19)}${owner(fx)}`);
    console.log(`${move.padEnd(7)} ${'owner adaptive'.padEnd(19)}${owner(ad)}`);
    const f = meanOf({ ...d, adaptive: false });
    console.log(`${move.padEnd(7)} ${'model fixed'.padEnd(19)}${show(f)}`);
    for (const resizeMs of [0, 20, 40]) {
      const a = meanOf({ ...d, adaptive: true, resizeMs });
      console.log(`${move.padEnd(7)} ${`model adaptive rz${resizeMs}`.padEnd(19)}${show(a)}  ${a.resizes.toFixed(1).padStart(6)} ${(a.paced / a.draws * 100).toFixed(0).padStart(4)} %`);
    }
  }
}
