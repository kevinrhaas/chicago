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

const HERE = path.dirname(new URL(import.meta.url).pathname);
const REPO = path.resolve(HERE, '..');
export const GLTF_DIR = 'data/gltf';
export const SHEETS = 'sheets';
const EXT = { 'image/ktx2': 'ktx2', 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp' };
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
 * Rewrite one GLB: every image in `move` (a Map of image index -> sheet URI)
 * points at an external buffer, and the binary chunk keeps only what is still
 * referenced in it. Each run of referenced bytes moves as a block to an offset
 * congruent to its old one mod 16, so no accessor or meshopt stream changes its
 * alignment.
 */
export function rewriteGlb(json, bin, move) {
  json = structuredClone(json);
  const bi = binIndex(json, bin);
  const views = json.bufferViews;
  const bufferFor = new Map();
  for (const [index, uri] of move) {
    const v = views[json.images[index].bufferView];
    if (!bufferFor.has(uri)) {
      bufferFor.set(uri, json.buffers.length);
      json.buffers.push({ uri, byteLength: v.byteLength });
    }
    v.buffer = bufferFor.get(uri);
    delete v.byteOffset;
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
export function shareSheets(site) {
  const dir = path.join(site, GLTF_DIR);
  const files = listGlbs(dir);
  const read = new Map();
  const holders = new Map();
  for (const rel of files) {
    const bytes = readFileSync(path.join(dir, rel));
    let parsed;
    try { parsed = readGlb(bytes); } catch { continue; }
    const images = movableImages(parsed.json, parsed.bin);
    read.set(rel, { ...parsed, images, size: bytes.length });
    for (const im of images) {
      const name = sheetName(im.bytes, im.mimeType);
      if (!holders.has(name)) holders.set(name, { bytes: im.bytes, files: new Set() });
      holders.get(name).files.add(rel);
    }
  }
  const shared = new Map([...holders].filter(([, h]) => h.files.size > 1));
  rmSync(path.join(dir, SHEETS), { recursive: true, force: true });
  if (!shared.size) return { glbs: 0, sheets: 0, before: 0, after: 0 };
  mkdirSync(path.join(dir, SHEETS), { recursive: true });
  for (const [name, h] of shared) writeFileSync(path.join(dir, SHEETS, name), h.bytes);
  let glbs = 0, before = 0, after = 0;
  for (const [rel, g] of read) {
    const move = new Map();
    const up = path.posix.relative(path.posix.dirname(rel), SHEETS);
    for (const im of g.images) {
      const name = sheetName(im.bytes, im.mimeType);
      if (shared.has(name)) move.set(im.index, `${up}/${name}`);
    }
    if (!move.size) continue;
    const { json, bin } = rewriteGlb(g.json, g.bin, move);
    const bytes = writeGlb(json, bin);
    writeFileSync(path.join(dir, rel), bytes);
    glbs++; before += g.size; after += bytes.length;
  }
  const sheetBytes = [...shared.values()].reduce((s, h) => s + h.bytes.length, 0);
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
export function checkSheets(site, sourceDir = path.join(REPO, 'assets/web')) {
  const dir = path.join(site, GLTF_DIR);
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
        if (!resolved.startsWith(`${SHEETS}/`)) throw new Error(`names ${uri}, outside ${GLTF_DIR}/${SHEETS}/`);
        const file = path.join(dir, resolved);
        if (!existsSync(file)) throw new Error(`names ${uri}, which is not published`);
        (held.get(resolved) || held.set(resolved, new Set()).get(resolved)).add(rel);
        return readFileSync(file);
      };
      if (placementFree(pub.json) !== placementFree(src.json)) throw new Error('its JSON is not its source\'s');
      const pv = pub.json.bufferViews ?? [];
      const sv = src.json.bufferViews ?? [];
      for (let i = 0; i < sv.length; i++) {
        const a = viewBytes(pub.json, pub.bin, readUri, pv[i]);
        const b = viewBytes(src.json, src.bin, () => null, sv[i]);
        if (!!a.data !== !!b.data || (a.data && !a.data.equals(b.data))) throw new Error(`bufferView ${i} differs`);
        if (!!a.meshopt !== !!b.meshopt || (a.meshopt && !a.meshopt.equals(b.meshopt))) throw new Error(`bufferView ${i}'s meshopt stream differs`);
      }
      for (const b of pub.json.buffers.slice(1)) {
        if (b.uri !== undefined && readUri(b.uri).length !== b.byteLength) throw new Error(`${b.uri} is not ${b.byteLength} bytes`);
      }
    } catch (err) {
      problems.push(`${GLTF_DIR}/${rel} is not its source assets/web/${rel} with sheets shared: ${err.message}`);
    }
  }
  const sheetDir = path.join(dir, SHEETS);
  const sheets = existsSync(sheetDir) ? readdirSync(sheetDir) : [];
  for (const name of sheets) {
    const bytes = readFileSync(path.join(sheetDir, name));
    const mime = Object.keys(EXT).find((m) => name.endsWith(`.${EXT[m]}`));
    if (!mime || sheetName(bytes, mime) !== name) problems.push(`${GLTF_DIR}/${SHEETS}/${name} is not named by its own hash`);
    const by = held.get(`${SHEETS}/${name}`)?.size ?? 0;
    if (by < 2) problems.push(`${GLTF_DIR}/${SHEETS}/${name} is held by ${by} GLB(s); a sheet ships only when two or more share it`);
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
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
  console.log(fails ? `share_glb_sheets self-test: ${fails} FAILED` : 'share_glb_sheets self-test: all passed');
  return fails ? 1 : 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  const args = process.argv.slice(2);
  if (args.includes('--self-test')) process.exit(selfTest());
  const site = args.find((a) => !a.startsWith('--'));
  if (!site || !statSync(site, { throwIfNoEntry: false })?.isDirectory()) {
    console.error('usage: share_glb_sheets.mjs SITE [--check] | --self-test');
    process.exit(2);
  }
  if (args.includes('--check')) {
    const r = checkSheets(site);
    if (r.problems.length) {
      console.error(`shared sheets FAILED (${r.problems.length}):`);
      for (const p of r.problems.slice(0, 20)) console.error(`  - ${p}`);
      process.exit(1);
    }
    console.log(`shared sheets: ${r.rewritten} GLB(s) read back to their sources through ${r.sheets} sheet(s)`);
  } else {
    const r = shareSheets(site);
    const mib = (n) => (n / 1048576).toFixed(3);
    console.log(`   sheets: ${r.sheets} shared by ${r.glbs} GLB(s), ${mib(r.before)} -> ${mib(r.after)} MiB`);
  }
}
