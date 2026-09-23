/**
 * measure_ao_frame.mjs — is the AO bake too dark? Read it off the RENDERED FRAME.
 *
 *   node tools/measure_ao_frame.mjs <without-AO-dir> <with-AO-dir> [--stations a,b]
 *
 * Both arguments are `tools/critic_shots.mjs --metrics --out DIR` output trees
 * shot from the SAME tree with one asset swapped, so `<dir>/<viewport>/<station>.png`
 * and its `__bare.png` (the same pose with the `structures` group hidden) exist in
 * each. Prints, per station and viewport, the lightness of the pixels the swapped
 * asset actually paints, in both conditions.
 *
 * WHY IT EXISTS — T-0227. Every judgement this project has made about AO was made
 * on an ATLAS statistic, and every one of those statistics was wrong twice over
 * (T-0158: read off an sRGB-tagged buffer, and averaged over an atlas 68.9 % of
 * which is empty UV space). Worse, none was read off a file that carried the
 * occlusion at all, because the export shipped a uniformly black texture until
 * T-0158 fixed it. An atlas mean is not a statement about the walls: it says
 * nothing about how much of the wall a visitor can see, how big it is in frame,
 * or what light the renderer puts on it. This measures the walls.
 *
 * THE PIXEL SET, and it is the whole method. `full XOR bare` is every pixel the
 * town's structures paint; intersect that with the pixels that MOVED between the
 * two conditions and what is left is the swapped building's own visible surface —
 * no hand-drawn box, no assumption about where it stands in frame. A pixel is
 * "moved" if any channel differs by more than THRESH, which is set above the
 * antialiasing jitter the harness's own repeat contract tolerates.
 *
 * The reading is CIE L* (`critic_metrics.labL`), not the raw byte: the question is
 * how dark the wall LOOKS, and L* is the axis perception is uniform on. `literal
 * black` is counted in raw bytes because a pixel at 0,0,0 is a hole in the render
 * whatever the colour space says about it.
 */
import fs from 'node:fs';
import path from 'node:path';
import { decodePng, labL } from './critic_metrics.mjs';

const argv = process.argv.slice(2);
const dirs = argv.filter((a) => !a.startsWith('--'));
if (dirs.length !== 2) {
  console.error('usage: measure_ao_frame.mjs <without-AO-dir> <with-AO-dir> [--stations a,b]');
  process.exit(2);
}
const pickArg = argv.find((a) => a.startsWith('--stations'));
const PICK = pickArg ? (pickArg.split('=')[1] || argv[argv.indexOf(pickArg) + 1] || '').split(',').filter(Boolean) : [];
const [WITHOUT, WITH] = dirs;
const THRESH = 8;   // above the harness's own antialiasing jitter

const png = (f) => decodePng(fs.readFileSync(f));

function stats(img, idx) {
  let sum = 0; let black = 0; const hist = new Float64Array(101);
  for (const i of idx) {
    const L = labL(img.data[i], img.data[i + 1], img.data[i + 2]);
    sum += L;
    hist[Math.max(0, Math.min(100, Math.round(L)))] += 1;
    if (img.data[i] === 0 && img.data[i + 1] === 0 && img.data[i + 2] === 0) black += 1;
  }
  const n = idx.length || 1;
  const pct = (t) => {
    let c = 0;
    for (let L = 0; L <= 100; L++) { c += hist[L]; if (c / n >= t) return L; }
    return 100;
  };
  const below = (t) => {
    let c = 0;
    for (let L = 0; L < t; L++) c += hist[L];
    return c / n;
  };
  return { n: idx.length, mean: sum / n, p5: pct(0.05), p50: pct(0.5), p95: pct(0.95),
           belowL20: below(20), belowL35: below(35), black };
}

const rows = [];
for (const viewport of ['mobile', 'desktop']) {
  const dir = path.join(WITHOUT, viewport);
  if (!fs.existsSync(dir)) continue;
  for (const file of fs.readdirSync(dir).sort()) {
    if (!file.endsWith('.png') || file.includes('__')) continue;
    const station = file.replace(/\.png$/, '');
    if (PICK.length && !PICK.includes(station)) continue;
    const bare = path.join(WITHOUT, viewport, `${station}__bare.png`);
    const withFile = path.join(WITH, viewport, file);
    if (!fs.existsSync(bare) || !fs.existsSync(withFile)) continue;

    const a = png(path.join(dir, file));
    const b = png(bare);
    const c = png(withFile);
    const structure = [];
    const moved = [];
    for (let i = 0; i < a.data.length; i += 4) {
      const isStructure = Math.abs(a.data[i] - b.data[i]) > THRESH
        || Math.abs(a.data[i + 1] - b.data[i + 1]) > THRESH
        || Math.abs(a.data[i + 2] - b.data[i + 2]) > THRESH;
      if (isStructure) structure.push(i);
      const didMove = Math.abs(a.data[i] - c.data[i]) > THRESH
        || Math.abs(a.data[i + 1] - c.data[i + 1]) > THRESH
        || Math.abs(a.data[i + 2] - c.data[i + 2]) > THRESH;
      if (isStructure && didMove) moved.push(i);
    }
    rows.push({ station, viewport, frame: a.width * a.height,
                structure: structure.length,
                without: stats(a, moved), with: stats(c, moved) });
  }
}

const f = (v, d = 1) => (typeof v === 'number' ? v.toFixed(d) : String(v));
console.log('\nthe swapped asset\'s own visible pixels — CIE L*, 0 = black\n');
console.log('station          view      px  % frame   mean L*   p5   p50   p95  L*<20  L*<35  black px');
for (const r of rows) {
  for (const [label, s] of [['  without AO', r.without], ['  with AO   ', r.with]]) {
    console.log(`${(label === '  without AO' ? r.station.padEnd(15) : ''.padEnd(15))} ${r.viewport.padEnd(8)}`
      + `${label === '  without AO' ? String(r.structure).padStart(6) : ''.padStart(6)}`
      + `${label === '  without AO' ? (r.structure / r.frame * 100).toFixed(1).padStart(8) + '%' : ''.padStart(9)}`
      + `  ${label} ${f(s.mean).padStart(6)} ${String(s.p5).padStart(4)} ${String(s.p50).padStart(5)} `
      + `${String(s.p95).padStart(5)} ${(s.belowL20 * 100).toFixed(1).padStart(5)}% ${(s.belowL35 * 100).toFixed(1).padStart(5)}% `
      + `${String(s.black).padStart(8)}`);
  }
  console.log(`${''.padEnd(15)} ${''.padEnd(8)}${''.padStart(6)}${''.padStart(9)}  measured over ${r.with.n} moved pixels`);
}
