#!/usr/bin/env node
/**
 * Hold the derived relief maps to the row order of the maps beside them (T-2300).
 *
 *   node tools/check_relief_rows.mjs --check       # the packers, and who uses them
 *   node tools/check_relief_rows.mjs --self-test   # prove a canvas-order packer fails
 *
 * WHAT IT GUARDS. `wall-relief.js`'s `orl` and `frontage.js`'s board-face
 * modulation are packed in the page from canvas pixels (top row first) into a
 * `THREE.DataTexture`, which three uploads unflipped (data row 0 at v = 0), and
 * are sampled on the same uv as a `normal_gl` (and frontage's `orm`) uploaded as
 * an image with `flipY` (the image's top row at v = 1). Until T-2300 the bytes
 * went in canvas order, so every wall's and walk's AO, roughness and grain was
 * the relief's mirror along v. The packers now live in
 * `renderers/web/js/relief-pack.js`; this runs them under node on maps whose
 * every canvas row is distinct and asserts each lands in the DataTexture row
 * that puts it where the flipped image puts the same row — and that both
 * loaders still build their DataTexture from those packers, not a loop of
 * their own.
 *
 * It reads; it writes nothing.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const JS = join(ROOT, 'renderers', 'web', 'js');
const pack = await import(join(JS, 'relief-pack.js'));

/** A w x h canvas-order RGBA image whose row r reads `value(r)` in R, G and B. */
function rows(w, h, value) {
  const d = new Uint8ClampedArray(w * h * 4);
  for (let r = 0; r < h; r += 1) {
    for (let x = 0; x < w; x += 1) {
      const j = (r * w + x) * 4;
      d[j] = value(r); d[j + 1] = value(r); d[j + 2] = value(r); d[j + 3] = 255;
    }
  }
  return d;
}

/**
 * Where a flipY'd image texture puts canvas row r of h, as a DataTexture row:
 * the image's top (r = 0) at v = 1, which is DataTexture row h - 1. Stated here
 * from three's two upload conventions, not read back from the packer under test.
 */
const flippedRow = (r, h) => h - 1 - r;

/** Each fault, as a sentence. Empty is green. */
function faults({ packOrl, packGrain }) {
  const out = [];
  const px = 8;
  // R (AO) and G (roughness) pass through; B is a luminance ratio, so give the
  // basecolor a distinct value per row too and compare B by its order.
  const orm = rows(px, px, (r) => 10 + 20 * r);
  const col = rows(px, px, (r) => 40 + 25 * r);
  const { data } = packOrl(orm, col, px);
  for (let r = 0; r < px; r += 1) {
    const k = flippedRow(r, px) * px * 4;
    if (data[k] !== orm[r * px * 4] || data[k + 1] !== orm[r * px * 4 + 1]) {
      out.push(`packOrl: canvas row ${r} (AO ${orm[r * px * 4]}) is not in DataTexture row `
        + `${flippedRow(r, px)}, where the flipY'd normal_gl puts that row — it holds ${data[k]}`);
      break;
    }
  }
  // B rises with the basecolor's row, so it must FALL with the DataTexture row.
  const b = (row) => data[row * px * 4 + 2];
  if (!(b(0) > b(px - 1))) {
    out.push(`packOrl: B (the albedo ratio) runs the wrong way up the tile — bottom ${b(0)}, top ${b(px - 1)}`);
  }

  const w = 6;
  const h = 10;
  const base = rows(w, h, (r) => 30 + 20 * r);
  const mod = packGrain(base, w, h, 1, 8);   // headroom wide enough that no row clips
  const g = (row) => mod[row * w * 4];
  for (let r = 0; r + 1 < h; r += 1) {
    if (!(g(flippedRow(r, h)) < g(flippedRow(r + 1, h)))) {
      out.push(`packGrain: canvas rows ${r} and ${r + 1} do not land in DataTexture rows `
        + `${flippedRow(r, h)} and ${flippedRow(r + 1, h)} — the grain is mirrored against its relief`);
      break;
    }
  }

  // The loaders must build their DataTexture from the packers' bytes.
  for (const [file, name, bytes] of [
    ['wall-relief.js', 'packOrl', 'orl'],
    ['frontage.js', 'packGrain', 'mod'],
  ]) {
    const src = readFileSync(join(JS, file), 'utf8');
    if (!new RegExp(`import\\s*\\{[^}]*\\b${name}\\b[^}]*\\}\\s*from\\s*'\\./relief-pack\\.js'`).test(src)) {
      out.push(`${file}: does not import ${name} from relief-pack.js`);
    }
    const made = [...src.matchAll(/new THREE\.DataTexture\(\s*(\w+)/g)].map((m) => m[1]);
    if (!made.includes(bytes)) out.push(`${file}: builds no DataTexture from \`${bytes}\``);
    if (!new RegExp(`(const|let)\\s*(\\{[^}]*\\b${bytes}\\b[^}]*\\}|${bytes})\\s*=\\s*${name}\\(`).test(src)) {
      out.push(`${file}: \`${bytes}\` is not the output of ${name}()`);
    }
  }
  return out;
}

/** A packer in canvas order — the pre-T-2300 loop — for the self-test. */
function canvasOrder(fn, height) {
  return (...args) => {
    const res = fn(...args);
    const data = res.data ?? res;
    const h = height(args);
    const stride = data.length / h;
    const back = new Uint8Array(data.length);
    for (let r = 0; r < h; r += 1) back.set(data.subarray(r * stride, (r + 1) * stride), (h - 1 - r) * stride);
    return res.data ? { ...res, data: back } : back;
  };
}

const mode = process.argv[2];
if (mode === '--check') {
  const out = faults(pack);
  for (const f of out) console.log(`FAIL ${f}`);
  console.log(out.length ? `relief rows: ${out.length} fault(s)` : 'relief rows: orl and the board grain lie the way their normal_gl does (T-2300)');
  process.exit(out.length ? 1 : 0);
} else if (mode === '--self-test') {
  const cases = {
    'orl in canvas order': { ...pack, packOrl: canvasOrder(pack.packOrl, (a) => a[2]) },
    'board grain in canvas order': { ...pack, packGrain: canvasOrder(pack.packGrain, (a) => a[2]) },
  };
  let bad = 0;
  for (const [name, packers] of Object.entries(cases)) {
    const out = faults(packers);
    console.log(`${out.length ? 'ok  ' : 'MISS'} ${name}${out.length ? ` — ${out[0]}` : ' — passed a mirrored packer'}`);
    if (!out.length) bad += 1;
  }
  if (faults(pack).length) { console.log('MISS the committed packers do not pass'); bad += 1; }
  process.exit(bad ? 1 : 0);
} else {
  console.error('usage: node tools/check_relief_rows.mjs --check | --self-test');
  process.exit(2);
}
