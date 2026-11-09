#!/usr/bin/env node
/**
 * Ship each texture sheet once — T-3232 (docs/SITE-BUDGET.md § 15).
 *
 *     node tools/share_glb_sheets.mjs SITE            # publish.sh: rewrite SITE/data/gltf
 *     node tools/share_glb_sheets.mjs SITE --check    # the gate: the shipped form is the source's
 *     node tools/share_glb_sheets.mjs --self-test
 *
 * WHY. Every Prairie house built on a kit embeds the kit's sheets in its own GLB, so
 * one 625 KiB K01 sheet shipped in 28 files and the published tree paid for it 28
 * times: on 2026-10-28 the 1,036 GLBs under data/gltf/ carried 116.5 MiB of embedded
 * images and only 23.6 MiB of them were different pictures. The renderer already
 * decodes each picture once (shared-images.js, T-2464); the bytes on disk were the
 * last place the copies lived.
 *
 * WHAT IT DOES. After publish.sh copies assets/web/ into data/gltf/, an image whose
 * exact bytes sit in two or more of those GLBs is written once, to
 * `data/gltf/sheets/<sha256 prefix>.<ext>`, and every GLB that carried it gets an
 * external glTF buffer naming that file, its image's bufferView pointing into it.
 * The GLB's binary chunk is repacked without the image. It is a plain glTF 2.0
 * external buffer, so GLTFLoader fetches it itself, relative to the path the GLB
 * was parsed with (which is why scene-loader.js and terrain.js parse with the
 * GLB's directory, not its URL). The image still arrives as a bufferView, so
 * shared-images.js digests and shares it, and texture residency re-decodes it,
 * exactly as before.
 *
 * WHAT IT DOES NOT. The committed GLBs (assets/gltf masters, assets/web
 * derivatives) are untouched: the emitters, the bake, `validate.py --stale` and
 * the byte-identity of a re-emit all see the files they always saw. This is a
 * transform of the published copy alone, declared in check_published.mjs, and
 * `--check` is the gate that measures the shipped form: every rewritten GLB, with
 * its sheets read back in, must give its source's JSON, bufferView for bufferView
 * and image for image. An image only one GLB carries stays embedded.
 */
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { deflateSync, inflateSync } from 'node:zlib';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const REPO = path.resolve(HERE, '..');
export const GLTF_DIR = 'data/gltf';
export const SHEETS = 'sheets';
/** T-3463: not an image: a geometry or clip stream two figures carry byte for byte. */
export const STREAM = 'application/octet-stream';
/** A stream is shared only from this size: below it, a fetch costs more than the bytes (2 KiB: at most 23 sheets a figure file, each fetched once for every figure). */
export const STREAM_MIN = 2048;
const EXT = { 'image/ktx2': 'ktx2', 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp', [STREAM]: 'bin' };
/**
 * T-3463: the build's own records a figure's GLB carries in its scene extras, which the
 * renderer never reads (it reads `lod` and `wardrobe_assembly_json`): the source JSON of the
 * body, hair, skin and blend it was made from. The committed GLB keeps them; the published
 * copy does not, and --check compares the two with them set aside.
 */
export const BUILD_EXTRAS = Object.freeze(['body_source_json', 'hair_source_json', 'body_target_blend_json',
  'skin_source_json', 'body_parameters_json', 'person_reference_summary_json']);
const leanable = (json) => (json.scenes ?? []).some((sc) => BUILD_EXTRAS.some((k) => sc.extras?.chicago4d_human?.[k] !== undefined));
export function leanExtras(json) {
  let human = false;
  for (const sc of json.scenes ?? []) {
    const e = sc.extras?.chicago4d_human;
    if (e) { human = true; for (const k of BUILD_EXTRAS) delete e[k]; }
  }
  if (human) leanHumanJson(json);
  return json;
}

/**
 * T-3463: a figure's JSON chunk is about 90 KB of every GLB (a third of a far LOD), 10 MB
 * across the people. Two things in it say nothing: properties written at their glTF 2.0
 * default (an accessor's `normalized: false` and `byteOffset: 0`, a sampler's
 * `interpolation: "LINEAR"`), and the float64 spelling of numbers that are float32 values
 * (`0.00808150414377451`, which is the float32 0.0080815041). Defaults go; an accessor's
 * min/max and a node's translation, rotation, scale and matrix are written as the shortest
 * decimal that reads back as the SAME float32, and only where the number already is one, so
 * nothing the GPU or the skeleton sees changes. Human GLBs only: the buildings are untouched.
 */
const f32Short = (x) => {
  if (typeof x !== 'number' || Number.isInteger(x) || Math.fround(x) !== x) return x;
  for (let p = 1; p < 17; p++) { const t = Number(x.toPrecision(p)); if (Math.fround(t) === x) return t; }
  return x;
};
const shortAll = (a) => (Array.isArray(a) ? a.map(f32Short) : a);
function leanHumanJson(json) {
  for (const a of json.accessors ?? []) {
    if (a.normalized === false) delete a.normalized;
    if (a.byteOffset === 0) delete a.byteOffset;
    if (a.min) a.min = shortAll(a.min);
    if (a.max) a.max = shortAll(a.max);
  }
  for (const an of json.animations ?? []) for (const s of an.samplers ?? []) if (s.interpolation === 'LINEAR') delete s.interpolation;
  for (const n of json.nodes ?? []) for (const k of ['translation', 'rotation', 'scale', 'matrix']) if (n[k]) n[k] = shortAll(n[k]);
  return json;
}
const JSON_CHUNK = 0x4E4F534A;
const BIN_CHUNK = 0x004E4942;
const MESHOPT = 'EXT_meshopt_compression';

const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
export const sheetName = (bytes, mimeType) => `${sha256(bytes).slice(0, 16)}.${EXT[mimeType]}`;

export function readGlb(bytes) {
  if (bytes.length < 20 || bytes.readUInt32LE(0) !== 0x46546C67) throw new Error('not a GLB');
  const jsonLen = bytes.readUInt32LE(12);
  if (bytes.readUInt32LE(16) !== JSON_CHUNK) throw new Error('first chunk is not JSON');
  const json = JSON.parse(bytes.subarray(20, 20 + jsonLen).toString('utf8'));
  let bin = null;
  const off = 20 + jsonLen;
  if (off + 8 <= bytes.length && bytes.readUInt32LE(off + 4) === BIN_CHUNK) {
    bin = bytes.subarray(off + 8, off + 8 + bytes.readUInt32LE(off));
  }
  return { json, bin };
}

export function writeGlb(json, bin) {
  let j = Buffer.from(JSON.stringify(json), 'utf8');
  if (j.length % 4) j = Buffer.concat([j, Buffer.alloc(4 - (j.length % 4), 0x20)]);
  const parts = [null, Buffer.alloc(8), j];
  parts[1].writeUInt32LE(j.length, 0);
  parts[1].writeUInt32LE(JSON_CHUNK, 4);
  if (bin) {
    let b = Buffer.from(bin);
    if (b.length % 4) b = Buffer.concat([b, Buffer.alloc(4 - (b.length % 4))]);
    const h = Buffer.alloc(8);
    h.writeUInt32LE(b.length, 0);
    h.writeUInt32LE(BIN_CHUNK, 4);
    parts.push(h, b);
  }
  const body = parts.slice(1);
  const total = 12 + body.reduce((s, p) => s + p.length, 0);
  parts[0] = Buffer.alloc(12);
  parts[0].writeUInt32LE(0x46546C67, 0);
  parts[0].writeUInt32LE(2, 4);
  parts[0].writeUInt32LE(total, 8);
  return Buffer.concat(parts);
}

/** The buffer index the GLB's binary chunk answers, or -1. */
function binIndex(json, bin) {
  const b = json.buffers?.[0];
  return bin && b && b.uri === undefined && !b.extensions?.[MESHOPT]?.fallback ? 0 : -1;
}

/**
 * The embedded images this GLB carries that can be moved: each `{ index, view,
 * bytes, mimeType }`. A GLB this tool cannot rewrite with certainty — an extension
 * on a bufferView other than meshopt's, an image view shared with anything else —
 * offers none, and is shipped as it came.
 */
export function movableImages(json, bin) {
  const bi = binIndex(json, bin);
  if (bi < 0) return [];
  const views = json.bufferViews ?? [];
  if (views.some((v) => Object.keys(v.extensions ?? {}).some((k) => k !== MESHOPT))) return [];
  const uses = new Map();
  const use = (i) => uses.set(i, (uses.get(i) ?? 0) + 1);
  for (const a of json.accessors ?? []) {
    if (a.bufferView !== undefined) use(a.bufferView);
    if (a.sparse) { use(a.sparse.indices.bufferView); use(a.sparse.values.bufferView); }
  }
  for (const im of json.images ?? []) if (im.bufferView !== undefined) use(im.bufferView);
  const out = [];
  for (const [index, im] of (json.images ?? []).entries()) {
    const v = views[im.bufferView];
    if (!v || v.buffer !== bi || v.extensions || !EXT[im.mimeType] || uses.get(im.bufferView) !== 1) continue;
    const start = v.byteOffset ?? 0;
    out.push({ index, view: im.bufferView, mimeType: im.mimeType, bytes: bin.subarray(start, start + v.byteLength) });
  }
  return out;
}

/**
 * T-3463: the streams this GLB carries that can be moved as sheets are: each bufferView's own
 * bytes in the binary chunk (its meshopt stream where it has one, else its data), STREAM_MIN
 * or more, overlapping no other view's, and not an image's (movableImages has those). Each
 * `{ view, meshopt, bytes, mimeType: STREAM }`. Same refusals as movableImages.
 */
export function movableStreams(json, bin) {
  const bi = binIndex(json, bin);
  if (bi < 0) return [];
  const views = json.bufferViews ?? [];
  if (views.some((v) => Object.keys(v.extensions ?? {}).some((k) => k !== MESHOPT))) return [];
  const images = new Set((json.images ?? []).map((im) => im.bufferView));
  const regions = [];
  for (const [view, v] of views.entries()) {
    const m = v.extensions?.[MESHOPT];
    if (m && m.buffer === bi) regions.push({ view, meshopt: true, s: m.byteOffset ?? 0, len: m.byteLength });
    if (v.buffer === bi) regions.push({ view, meshopt: false, s: v.byteOffset ?? 0, len: v.byteLength });
  }
  const overlaps = (r) => regions.some((q) => q !== r && q.s < r.s + r.len && r.s < q.s + q.len);
  const out = [];
  for (const r of regions) {
    if (r.len < STREAM_MIN || images.has(r.view) || overlaps(r)) continue;
    if (!r.meshopt && views[r.view].extensions?.[MESHOPT]) continue;
    out.push({ view: r.view, meshopt: r.meshopt, mimeType: STREAM, bytes: bin.subarray(r.s, r.s + r.len) });
  }
  return out;
}

/**
 * Rewrite one GLB: every image in `move` (a Map of image index -> sheet URI)
 * points at an external buffer, and the binary chunk keeps only what is still
 * referenced in it. Each run of referenced bytes moves as a block to an offset
 * congruent to its old one mod 16, so no accessor or meshopt stream changes its
 * alignment.
 */
export function rewriteGlb(json, bin, move, streams = new Map()) {
  json = leanExtras(structuredClone(json));
  const bi = binIndex(json, bin);
  const views = json.bufferViews;
  const bufferFor = new Map();
  const bufferOf = (uri, len) => {
    if (!bufferFor.has(uri)) {
      bufferFor.set(uri, json.buffers.length);
      json.buffers.push({ uri, byteLength: len });
    }
    return bufferFor.get(uri);
  };
  for (const [index, to] of move) {
    const v = views[json.images[index].bufferView];
    const { uri, byteLength } = typeof to === 'string' ? { uri: to } : to;
    if (byteLength) v.byteLength = byteLength;   // a re-deflated PNG sheet (T-3463)
    v.buffer = bufferOf(uri, v.byteLength);
    delete v.byteOffset;
  }
  // T-3463: a stream moves the same way; a meshopt one moves the extension's buffer.
  for (const [key, uri] of streams) {
    const [view, kind] = key.split(':');
    const v = views[Number(view)];
    const o = kind === 'm' ? v.extensions[MESHOPT] : v;
    o.buffer = bufferOf(uri, o.byteLength);
    delete o.byteOffset;
  }
  const refs = [];
  for (const v of views) {
    if (v.buffer === bi) refs.push({ o: v, key: 'byteOffset', start: v.byteOffset ?? 0, len: v.byteLength });
    const m = v.extensions?.[MESHOPT];
    if (m && m.buffer === bi) refs.push({ o: m, key: 'byteOffset', start: m.byteOffset ?? 0, len: m.byteLength });
  }
  const spans = refs.map((r) => [r.start, r.start + r.len]).sort((a, b) => a[0] - b[0]);
  const merged = [];
  for (const [s, e] of spans) {
    const last = merged[merged.length - 1];
    if (last && s <= last[1]) last[1] = Math.max(last[1], e);
    else merged.push([s, e]);
  }
  const placed = [];
  let cursor = 0;
  for (const [s, e] of merged) {
    const at = cursor + ((((s % 16) - (cursor % 16)) + 16) % 16);
    placed.push({ s, e, at });
    cursor = at + (e - s);
  }
  const out = Buffer.alloc(cursor);
  for (const p of placed) bin.copy(out, p.at, p.s, p.e);
  for (const r of refs) {
    const p = placed.find((q) => r.start >= q.s && r.start + r.len <= q.e);
    const at = p.at + (r.start - p.s);
    if (at) r.o[r.key] = at; else delete r.o[r.key];
  }
  json.buffers[bi].byteLength = out.length;
  return { json, bin: out };
}

// ── T-3463: a shared PNG sheet ships re-deflated, pixel for pixel the same ──────────────
const PNG_SIG = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
function pngChunks(bytes) {
  if (bytes.length < 8 || !bytes.subarray(0, 8).equals(PNG_SIG)) return null;
  const out = [];
  for (let o = 8; o + 12 <= bytes.length;) {
    const len = bytes.readUInt32BE(o);
    const type = bytes.toString('latin1', o + 4, o + 8);
    out.push({ type, data: bytes.subarray(o + 8, o + 8 + len), raw: bytes.subarray(o, o + 12 + len) });
    o += 12 + len;
    if (type === 'IEND') break;
  }
  return out;
}
const CHANNELS = { 0: 1, 2: 3, 4: 2, 6: 4 };
/** The unfiltered scanlines of an 8-bit, non-interlaced PNG, with its chunks; else null. */
export function pngPixels(bytes) {
  const chunks = pngChunks(bytes);
  const hdr = chunks?.[0];
  if (!hdr || hdr.type !== 'IHDR') return null;
  const w = hdr.data.readUInt32BE(0), h = hdr.data.readUInt32BE(4);
  const depth = hdr.data[8], colour = hdr.data[9], interlace = hdr.data[12];
  if (depth !== 8 || !CHANNELS[colour] || interlace !== 0) return null;
  const bpp = CHANNELS[colour], stride = w * bpp;
  const z = inflateSync(Buffer.concat(chunks.filter((c) => c.type === 'IDAT').map((c) => c.data)));
  if (z.length !== h * (stride + 1)) return null;
  const px = Buffer.alloc(h * stride);
  for (let y = 0; y < h; y++) {
    const f = z[y * (stride + 1)];
    const src = y * (stride + 1) + 1, dst = y * stride, up = dst - stride;
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? px[dst + x - bpp] : 0, b = y ? px[up + x] : 0, c = x >= bpp && y ? px[up + x - bpp] : 0;
      let pr = 0;
      if (f === 0) pr = 0; else if (f === 1) pr = a; else if (f === 2) pr = b; else if (f === 3) pr = (a + b) >> 1;
      else if (f === 4) { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c); pr = pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      else return null;
      px[dst + x] = (z[src + x] + pr) & 255;
    }
  }
  return { w, h, bpp, stride, px, chunks };
}
const crcTable = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
function crc32(buf) { let c = 0xFFFFFFFF; for (const b of buf) c = crcTable[(c ^ b) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
function chunk(type, data) {
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0);
  out.write(type, 4, 'latin1');
  data.copy(out, 8);
  out.writeUInt32BE(crc32(out.subarray(4, 8 + data.length)), 8 + data.length);
  return out;
}
/**
 * The same PNG, its rows re-filtered (each row the filter whose bytes sum smallest) and
 * deflated at level 9, every chunk but the image data kept as it was. Returns the smaller of
 * that and the input, so it never grows a file.
 */
export function repackPng(bytes) {
  const p = pngPixels(bytes);
  if (!p) return bytes;
  const { h, bpp, stride, px, chunks } = p;
  const rows = Buffer.alloc(h * (stride + 1));
  const cand = [0, 1, 2, 3, 4].map(() => Buffer.alloc(stride));
  for (let y = 0; y < h; y++) {
    const row = y * stride, up = row - stride;
    let best = 0, bestSum = Infinity;
    for (let f = 0; f < 5; f++) {
      const out = cand[f];
      let sum = 0;
      for (let x = 0; x < stride; x++) {
        const a = x >= bpp ? px[row + x - bpp] : 0, b = y ? px[up + x] : 0, c = x >= bpp && y ? px[up + x - bpp] : 0;
        let pr = 0;
        if (f === 1) pr = a; else if (f === 2) pr = b; else if (f === 3) pr = (a + b) >> 1;
        else if (f === 4) { const q = a + b - c, pa = Math.abs(q - a), pb = Math.abs(q - b), pc = Math.abs(q - c); pr = pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
        const v = (px[row + x] - pr) & 255;
        out[x] = v;
        sum += v < 128 ? v : 256 - v;
        if (sum >= bestSum) break;
      }
      if (sum < bestSum) { bestSum = sum; best = f; }
    }
    // Re-run the winner in full (the loop above may have stopped it early only if it lost).
    rows[y * (stride + 1)] = best;
    cand[best].copy(rows, y * (stride + 1) + 1);
  }
  const idat = deflateSync(rows, { level: 9, memLevel: 9 });
  const parts = [PNG_SIG];
  let wrote = false;
  for (const c of chunks) {
    if (c.type === 'IDAT') { if (!wrote) { parts.push(chunk('IDAT', idat)); wrote = true; } continue; }
    parts.push(c.raw);
  }
  const out = Buffer.concat(parts);
  return out.length < bytes.length ? out : bytes;
}
/** Whether two PNGs draw the same pixels with the same header and chunks but their data. */
export function samePngPixels(a, b) {
  const p = pngPixels(a), q = pngPixels(b);
  if (!p || !q || !p.px.equals(q.px)) return false;
  const rest = (x) => x.chunks.filter((c) => c.type !== 'IDAT').map((c) => c.raw.toString('base64')).join();
  return rest(p) === rest(q);
}

function listGlbs(dir, rel = '') {
  const out = [];
  if (!existsSync(dir)) return out;
  for (const e of readdirSync(path.join(dir, rel), { withFileTypes: true })) {
    const r = rel ? `${rel}/${e.name}` : e.name;
    if (e.isDirectory()) { if (r !== SHEETS) out.push(...listGlbs(dir, r)); }
    else if (e.name.endsWith('.glb')) out.push(r);
  }
  return out.sort();
}

/** publish.sh's step. Returns what it did, for its one line of output. */
export function shareSheets(site, glbDir = GLTF_DIR, { streams: withStreams = false } = {}) {
  const dir = path.join(site, glbDir);
  const files = listGlbs(dir);
  const read = new Map();
  const holders = new Map();
  for (const rel of files) {
    const bytes = readFileSync(path.join(dir, rel));
    let parsed;
    try { parsed = readGlb(bytes); } catch { continue; }
    const images = movableImages(parsed.json, parsed.bin);
    const streams = withStreams ? movableStreams(parsed.json, parsed.bin) : [];
    read.set(rel, { ...parsed, images, streams, size: bytes.length });
    for (const im of [...images, ...streams]) {
      const name = sheetName(im.bytes, im.mimeType);
      if (!holders.has(name)) holders.set(name, { bytes: im.bytes, files: new Set() });
      holders.get(name).files.add(rel);
    }
  }
  const shared = new Map([...holders].filter(([, h]) => h.files.size > 1));
  rmSync(path.join(dir, SHEETS), { recursive: true, force: true });
  if (!shared.size) return { glbs: 0, sheets: 0, before: 0, after: 0 };
  mkdirSync(path.join(dir, SHEETS), { recursive: true });
  // T-3463: with --streams (the people's directory), a PNG sheet ships re-deflated when that
  // is smaller, under its new bytes' name; the GLBs' image views take its length.
  const shipped = new Map();
  for (const [name, h] of shared) {
    let bytes = h.bytes, out = name;
    if (withStreams && name.endsWith('.png')) {
      const small = repackPng(h.bytes);
      if (small.length < h.bytes.length) { bytes = small; out = sheetName(small, 'image/png'); }
    }
    shipped.set(name, { name: out, length: bytes.length });
    writeFileSync(path.join(dir, SHEETS, out), bytes);
  }
  let glbs = 0, before = 0, after = 0;
  for (const [rel, g] of read) {
    const move = new Map();
    const up = path.posix.relative(path.posix.dirname(rel), SHEETS);
    for (const im of g.images) {
      const name = sheetName(im.bytes, im.mimeType);
      if (shared.has(name)) {
        const sh = shipped.get(name);
        move.set(im.index, sh.name === name ? `${up}/${name}` : { uri: `${up}/${sh.name}`, byteLength: sh.length });
      }
    }
    const moveStreams = new Map();
    for (const st of g.streams) {
      const name = sheetName(st.bytes, st.mimeType);
      if (shared.has(name)) moveStreams.set(`${st.view}:${st.meshopt ? 'm' : 'd'}`, `${up}/${name}`);
    }
    if (!move.size && !moveStreams.size && !(withStreams && leanable(g.json))) continue;
    const { json, bin } = rewriteGlb(g.json, g.bin, move, moveStreams);
    const bytes = writeGlb(json, bin);
    writeFileSync(path.join(dir, rel), bytes);
    glbs++; before += g.size; after += bytes.length;
  }
  const sheetBytes = [...shipped.values()].reduce((s, h) => s + h.length, 0);
  return { glbs, sheets: shared.size, before, after: after + sheetBytes };
}

/** Every byte a bufferView (or its meshopt stream) addresses, read through its buffer. */
function viewBytes(json, bin, readUri, v) {
  const at = (buffer, start, len) => {
    const b = json.buffers[buffer];
    const src = b.uri === undefined ? bin : readUri(b.uri);
    if (!src || start + len > src.length) throw new Error(`buffer ${buffer} is shorter than a view into it`);
    return src.subarray(start, start + len);
  };
  const m = v.extensions?.[MESHOPT];
  return {
    data: json.buffers[v.buffer]?.extensions?.[MESHOPT]?.fallback ? null : at(v.buffer, v.byteOffset ?? 0, v.byteLength),
    meshopt: m ? at(m.buffer, m.byteOffset ?? 0, m.byteLength) : null,
  };
}

/** The JSON with every placement erased: what a GLB says, apart from where its bytes sit. */
function placementFree(json) {
  const j = structuredClone(json);
  delete j.buffers;
  for (const v of j.bufferViews ?? []) {
    delete v.buffer; delete v.byteOffset;
    const m = v.extensions?.[MESHOPT];
    if (m) { delete m.buffer; delete m.byteOffset; }
  }
  return JSON.stringify(j);
}

/**
 * The gate. Each published GLB under data/gltf/ is either its source's bytes, or
 * a rewrite whose JSON, bufferViews and meshopt streams — sheets read back in —
 * are its source's exactly. Every sheet is named by its own hash, held by at least
 * two GLBs, and nothing names a sheet that is not there.
 */
export function checkSheets(site, sourceDir = path.join(REPO, 'assets/web'), glbDir = GLTF_DIR) {
  const dir = path.join(site, glbDir);
  const srcRel = path.relative(REPO, sourceDir);
  const problems = [];
  const held = new Map();
  let rewritten = 0;
  for (const rel of listGlbs(dir)) {
    const pubBytes = readFileSync(path.join(dir, rel));
    const srcPath = path.join(sourceDir, rel);
    if (!existsSync(srcPath)) continue; // check_published.mjs reports a GLB with no source
    const srcBytes = readFileSync(srcPath);
    if (pubBytes.equals(srcBytes)) continue;
    rewritten++;
    try {
      const pub = readGlb(pubBytes);
      const src = readGlb(srcBytes);
      const readUri = (uri) => {
        const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(rel), uri));
        if (!resolved.startsWith(`${SHEETS}/`)) throw new Error(`names ${uri}, outside ${glbDir}/${SHEETS}/`);
        const file = path.join(dir, resolved);
        if (!existsSync(file)) throw new Error(`names ${uri}, which is not published`);
        (held.get(resolved) || held.set(resolved, new Set()).get(resolved)).add(rel);
        return readFileSync(file);
      };
      // T-3463: a PNG image whose bytes differ from its source's must draw the same pixels
      // (repackPng); its view's length is then the only thing the JSON may differ by.
      const said = structuredClone(pub.json);
      const repacked = new Set();
      for (const im of pub.json.images ?? []) {
        if (im.mimeType !== 'image/png' || im.bufferView === undefined) continue;
        const i = im.bufferView;
        const a = viewBytes(pub.json, pub.bin, readUri, pub.json.bufferViews[i]).data;
        const b = viewBytes(src.json, src.bin, () => null, src.json.bufferViews[i]).data;
        if (!a || !b || a.equals(b)) continue;
        if (!samePngPixels(a, b)) throw new Error(`bufferView ${i}'s PNG does not draw its source's pixels`);
        repacked.add(i);
        said.bufferViews[i].byteLength = src.json.bufferViews[i].byteLength;
      }
      if (placementFree(said) !== placementFree(leanExtras(structuredClone(src.json)))) throw new Error('its JSON is not its source\'s');
      const pv = pub.json.bufferViews ?? [];
      const sv = src.json.bufferViews ?? [];
      for (let i = 0; i < sv.length; i++) {
        if (repacked.has(i)) continue;
        const a = viewBytes(pub.json, pub.bin, readUri, pv[i]);
        const b = viewBytes(src.json, src.bin, () => null, sv[i]);
        if (!!a.data !== !!b.data || (a.data && !a.data.equals(b.data))) throw new Error(`bufferView ${i} differs`);
        if (!!a.meshopt !== !!b.meshopt || (a.meshopt && !a.meshopt.equals(b.meshopt))) throw new Error(`bufferView ${i}'s meshopt stream differs`);
      }
      for (const b of pub.json.buffers.slice(1)) {
        if (b.uri !== undefined && readUri(b.uri).length !== b.byteLength) throw new Error(`${b.uri} is not ${b.byteLength} bytes`);
      }
    } catch (err) {
      problems.push(`${glbDir}/${rel} is not its source ${srcRel}/${rel} with sheets shared: ${err.message}`);
    }
  }
  const sheetDir = path.join(dir, SHEETS);
  const sheets = existsSync(sheetDir) ? readdirSync(sheetDir) : [];
  for (const name of sheets) {
    const bytes = readFileSync(path.join(sheetDir, name));
    const mime = Object.keys(EXT).find((m) => name.endsWith(`.${EXT[m]}`));
    if (!mime || sheetName(bytes, mime) !== name) problems.push(`${glbDir}/${SHEETS}/${name} is not named by its own hash`);
    const by = held.get(`${SHEETS}/${name}`)?.size ?? 0;
    if (by < 2) problems.push(`${glbDir}/${SHEETS}/${name} is held by ${by} GLB(s); a sheet ships only when two or more share it`);
  }
  return { problems, rewritten, sheets: sheets.length };
}

/** The year packs' question: which sheets does each published GLB name? */
export function sheetsNamedBy(site, rel) {
  const file = path.join(site, rel);
  if (!rel.startsWith(`${GLTF_DIR}/`) || !rel.endsWith('.glb') || !existsSync(file)) return [];
  let json;
  try { ({ json } = readGlb(readFileSync(file))); } catch { return []; }
  return (json.buffers ?? []).filter((b) => typeof b.uri === 'string')
    .map((b) => path.posix.normalize(path.posix.join(path.posix.dirname(rel), b.uri)));
}

function selfTest() {
  let fails = 0;
  const ok = (cond, what) => { console.log(`${cond ? 'PASS' : 'FAIL'}  ${what}`); if (!cond) fails++; };
  const root = mkdtempSync(path.join(tmpdir(), 'share-sheets-'));
  try {
    const site = path.join(root, 'site');
    const src = path.join(root, 'web');
    mkdirSync(path.join(site, GLTF_DIR, 'versions/x'), { recursive: true });
    mkdirSync(path.join(src, 'versions/x'), { recursive: true });
    const sheet = Buffer.alloc(1000, 7);
    const own = (n) => Buffer.alloc(300, n);
    // A mesh stream at 0, an image, then an accessor at an odd 4-aligned offset, and
    // a meshopt stream after it: the repack must keep each one's bytes and alignment.
    const make = (n) => {
      const pos = Buffer.alloc(36, n);
      const mo = Buffer.alloc(20, 100 + n);
      const img = own(n);
      const bin = Buffer.alloc(36 + 4 + 1000 + 4 + 300 + 4 + 20);
      pos.copy(bin, 0); sheet.copy(bin, 40); img.copy(bin, 1044); mo.copy(bin, 1348);
      const json = {
        asset: { version: '2.0' },
        buffers: [{ byteLength: bin.length }, { byteLength: 64, extensions: { [MESHOPT]: { fallback: true } } }],
        bufferViews: [
          { buffer: 0, byteOffset: 0, byteLength: 36 },
          { buffer: 0, byteOffset: 40, byteLength: 1000 },
          { buffer: 0, byteOffset: 1044, byteLength: 300 },
          { buffer: 1, byteLength: 64, extensions: { [MESHOPT]: { buffer: 0, byteOffset: 1348, byteLength: 20, byteStride: 4, count: 16, mode: 'ATTRIBUTES' } } },
        ],
        accessors: [{ bufferView: 0, componentType: 5126, count: 3, type: 'VEC3' }, { bufferView: 3, componentType: 5126, count: 16, type: 'SCALAR' }],
        images: [{ bufferView: 1, mimeType: 'image/ktx2' }, { bufferView: 2, mimeType: 'image/ktx2' }],
      };
      return writeGlb(json, bin);
    };
    for (const [rel, n] of [['a.glb', 1], ['b.glb', 2], ['versions/x/c.glb', 3]]) {
      writeFileSync(path.join(site, GLTF_DIR, rel), make(n));
      writeFileSync(path.join(src, rel), make(n));
    }
    const lone = writeGlb({ asset: { version: '2.0' }, buffers: [{ byteLength: 8 }],
      bufferViews: [{ buffer: 0, byteLength: 8 }], images: [{ bufferView: 0, mimeType: 'image/png' }] }, Buffer.alloc(8, 9));
    writeFileSync(path.join(site, GLTF_DIR, 'lone.glb'), lone);
    writeFileSync(path.join(src, 'lone.glb'), lone);

    const did = shareSheets(site);
    ok(did.glbs === 3 && did.sheets === 1, `one sheet three GLBs share is written once (${did.glbs} GLBs, ${did.sheets} sheet)`);
    ok(did.after < did.before, `the published bytes fall (${did.before} -> ${did.after})`);
    ok(readFileSync(path.join(site, GLTF_DIR, 'lone.glb')).equals(lone), 'an image one GLB holds stays embedded, the file untouched');
    const a = readGlb(readFileSync(path.join(site, GLTF_DIR, 'a.glb')));
    ok(a.json.buffers[2]?.uri === `sheets/${sheetName(sheet, 'image/ktx2')}`, 'the GLB names the sheet beside it');
    ok(a.json.bufferViews[3].extensions[MESHOPT].byteOffset % 4 === 0 && (a.json.bufferViews[2].byteOffset ?? 0) % 4 === 0,
      'every block keeps its alignment');
    ok(sheetsNamedBy(site, `${GLTF_DIR}/versions/x/c.glb`)[0] === `${GLTF_DIR}/${SHEETS}/${sheetName(sheet, 'image/ktx2')}`,
      'a versioned GLB reaches the one sheet up the tree');
    let r = checkSheets(site, src);
    ok(!r.problems.length && r.rewritten === 3, `the gate reads every rewrite back to its source (${r.problems.join('; ') || 'clean'})`);

    // Break it four ways; each must be caught.
    const sheetFile = path.join(site, GLTF_DIR, SHEETS, sheetName(sheet, 'image/ktx2'));
    const bad = Buffer.from(sheet); bad[5] = 0;
    writeFileSync(sheetFile, bad);
    r = checkSheets(site, src);
    ok(r.problems.some((p) => /not named by its own hash/.test(p)) && r.problems.some((p) => /bufferView 1 differs/.test(p)),
      'a sheet whose bytes changed is refused');
    writeFileSync(sheetFile, sheet);
    const b = readGlb(readFileSync(path.join(site, GLTF_DIR, 'b.glb')));
    const moved = Buffer.from(b.bin); moved[0] ^= 0xff;
    writeFileSync(path.join(site, GLTF_DIR, 'b.glb'), writeGlb(b.json, moved));
    r = checkSheets(site, src);
    ok(r.problems.some((p) => /b\.glb .*bufferView 0 differs/.test(p)), 'a repack that loses a mesh byte is refused');
    writeFileSync(path.join(site, GLTF_DIR, 'b.glb'), writeGlb(b.json, b.bin));
    const j = structuredClone(b.json); j.images[0].mimeType = 'image/png';
    writeFileSync(path.join(site, GLTF_DIR, 'b.glb'), writeGlb(j, b.bin));
    r = checkSheets(site, src);
    ok(r.problems.some((p) => /JSON is not its source/.test(p)), 'a rewrite that changes what the GLB says is refused');
    writeFileSync(path.join(site, GLTF_DIR, 'b.glb'), writeGlb(b.json, b.bin));
    writeFileSync(path.join(site, GLTF_DIR, SHEETS, sheetName(own(9), 'image/ktx2')), own(9));
    r = checkSheets(site, src);
    ok(r.problems.some((p) => /held by 0 GLB/.test(p)), 'a sheet nothing names is refused');

    // T-3453: the people's directory is shared on its own, beside the houses'.
    const HUMANS = 'data/humans/web';
    const hsrc = path.join(root, 'humans');
    mkdirSync(path.join(site, HUMANS), { recursive: true });
    mkdirSync(hsrc, { recursive: true });
    for (const [rel, n] of [['p.lod0.glb', 4], ['q.lod0.glb', 5]]) {
      writeFileSync(path.join(site, HUMANS, rel), make(n));
      writeFileSync(path.join(hsrc, rel), make(n));
    }
    const hd = shareSheets(site, HUMANS);
    ok(hd.glbs === 2 && hd.sheets === 1 && existsSync(path.join(site, HUMANS, SHEETS, sheetName(sheet, 'image/ktx2'))),
      `another directory's GLBs share their own sheet beside them (${hd.glbs} GLBs, ${hd.sheets} sheet)`);
    r = checkSheets(site, hsrc, HUMANS);
    ok(!r.problems.length && r.rewritten === 2, `and read back to their own sources (${r.problems.join('; ') || 'clean'})`);

    // T-3463: with streams, a geometry stream two figures carry byte for byte ships once too.
    const SDIR = 'data/humans/streams';
    const ssrc = path.join(root, 'streams');
    mkdirSync(path.join(site, SDIR), { recursive: true });
    mkdirSync(ssrc, { recursive: true });
    const body = Buffer.alloc(STREAM_MIN + 12, 42);
    const makeS = (n) => {
      const mine = Buffer.alloc(300, n);
      const bin = Buffer.alloc(body.length + 4 + 300);
      body.copy(bin, 0); mine.copy(bin, body.length + 4);
      return writeGlb({
        asset: { version: '2.0' },
        buffers: [{ byteLength: bin.length }, { byteLength: 64, extensions: { [MESHOPT]: { fallback: true } } }],
        bufferViews: [
          { buffer: 1, byteLength: 64, extensions: { [MESHOPT]: { buffer: 0, byteOffset: 0, byteLength: body.length, byteStride: 4, count: 16, mode: 'ATTRIBUTES' } } },
          { buffer: 0, byteOffset: body.length + 4, byteLength: 300 },
        ],
        accessors: [{ bufferView: 0, componentType: 5126, count: 16, type: 'SCALAR' }, { bufferView: 1, componentType: 5126, count: 75, type: 'SCALAR' }],
      }, bin);
    };
    for (const [rel, n] of [['s.lod0.glb', 6], ['t.lod0.glb', 7]]) {
      writeFileSync(path.join(site, SDIR, rel), makeS(n));
      writeFileSync(path.join(ssrc, rel), makeS(n));
    }
    const none = shareSheets(site, SDIR);
    ok(none.glbs === 0, 'without --streams a stream stays where it is');
    const sd = shareSheets(site, SDIR, { streams: true });
    ok(sd.glbs === 2 && sd.sheets === 1 && existsSync(path.join(site, SDIR, SHEETS, sheetName(body, STREAM))),
      `with --streams the shared stream ships once (${sd.glbs} GLBs, ${sd.sheets} sheet, ${sd.before} -> ${sd.after} bytes)`);
    r = checkSheets(site, ssrc, SDIR);
    ok(!r.problems.length && r.rewritten === 2, `and each reads back to its source (${r.problems.join('; ') || 'clean'})`);
    // T-3463: a PNG re-deflates to the same pixels and never grows; a changed pixel is caught.
    {
      const w = 64, h = 32, raw = Buffer.alloc(h * (w * 4 + 1));
      for (let y = 0; y < h; y++) for (let x = 0; x < w * 4; x++) raw[y * (w * 4 + 1) + 1 + x] = (x * 7 + y * 3) & 255;
      const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 6;
      const loose = Buffer.concat([PNG_SIG, chunk('IHDR', ihdr), chunk('IDAT', deflateSync(raw, { level: 0 })), chunk('IEND', Buffer.alloc(0))]);
      const tight = repackPng(loose);
      ok(tight.length < loose.length && samePngPixels(tight, loose), `a PNG re-deflates smaller, pixel for pixel (${loose.length} -> ${tight.length})`);
      ok(repackPng(tight).length <= tight.length, 'and never grows');
      const px = pngPixels(tight).px; px[5] ^= 1;
      const bent = Buffer.concat([PNG_SIG, chunk('IHDR', ihdr), chunk('IDAT', deflateSync(Buffer.concat(
        Array.from({ length: h }, (_, y) => Buffer.concat([Buffer.from([0]), px.subarray(y * w * 4, (y + 1) * w * 4)]))))), chunk('IEND', Buffer.alloc(0))]);
      ok(!samePngPixels(bent, loose), 'one changed pixel is not the same picture');
    }
    const s0 = readGlb(readFileSync(path.join(site, SDIR, 's.lod0.glb')));
    ok(s0.bin.length < 400 && s0.json.bufferViews[0].extensions[MESHOPT].buffer === 2, 'the stream left the binary chunk for the sheet');
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
  console.log(fails ? `share_glb_sheets self-test: ${fails} FAILED` : 'share_glb_sheets self-test: all passed');
  return fails ? 1 : 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  const args = process.argv.slice(2);
  if (args.includes('--self-test')) process.exit(selfTest());
  const site = args.find((a, i) => !a.startsWith('--') && !['--dir', '--source'].includes(args[i - 1]));
  // T-3453: `--dir data/humans/web --source assets/humans/web` shares the people's
  // pictures the same way: every figure embeds the same hair, skin and eye maps.
  const opt = (name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : undefined; };
  const glbDir = opt('--dir') ?? GLTF_DIR;
  // T-3463: `--streams` shares the figures' identical geometry and clip streams as well.
  const withStreams = args.includes('--streams');
  const sourceDir = path.join(REPO, opt('--source') ?? 'assets/web');
  if (!site || !statSync(site, { throwIfNoEntry: false })?.isDirectory()) {
    console.error('usage: share_glb_sheets.mjs SITE [--dir D --source S] [--check] | --self-test');
    process.exit(2);
  }
  if (args.includes('--check')) {
    const r = checkSheets(site, sourceDir, glbDir);
    if (r.problems.length) {
      console.error(`shared sheets FAILED (${r.problems.length}):`);
      for (const p of r.problems.slice(0, 20)) console.error(`  - ${p}`);
      process.exit(1);
    }
    console.log(`shared sheets (${glbDir}): ${r.rewritten} GLB(s) read back to their sources through ${r.sheets} sheet(s)`);
  } else {
    const r = shareSheets(site, glbDir, { streams: withStreams });
    const mib = (n) => (n / 1048576).toFixed(3);
    console.log(`   sheets (${glbDir}): ${r.sheets} shared by ${r.glbs} GLB(s), ${mib(r.before)} -> ${mib(r.after)} MiB`);
  }
}
