#!/usr/bin/env node
/**
 * prebuild_layers.mjs — T-2676, the first piece of T-2560 ("ship the town
 * prebuilt"). Runs the page's OWN layer builder in Node, against the same data
 * and terrain.js's own Heightfield, and writes the finished buffers with a hash
 * of every input they were built from, so a phone can one day upload the town
 * instead of building it at every boot.
 *
 *   node tools/prebuild_layers.mjs [--out DIR] [--build ID] [--gzip] [--json]
 *       Build every scene that draws frontage (1835 today) into
 *       DIR/<year>/frontage.{bin,json}. DIR defaults to a temp dir.
 *       `tools/publish.sh` runs it into site/4d/data/prebuilt/ with --build set
 *       to the stamp it writes into the page, and the page uploads the buffers
 *       instead of building them when that stamp and the records it read match
 *       (T-2677; frontage.js § THE TOWN'S TIMBER, PREBUILT).
 *   node tools/prebuild_layers.mjs --check DIR
 *       Refuse a stale prebuild: re-hash the inputs DIR's index names and the
 *       inputs the builder reads now, and exit 1 if either moved.
 *   node tools/prebuild_layers.mjs --self-test
 *       The check.sh gate: two builds are byte-identical, the page's own
 *       createFrontage REPLAYING the prebuild yields the build's meshes, census,
 *       walks, decks, keep-outs and pick spans, a replay over other records is
 *       refused, --check accepts the fresh build, and --check refuses one whose
 *       inputs hash no longer matches.
 *   node tools/prebuild_layers.mjs --parity [--root DIR] [--json]
 *       The acceptance: boot the live page in Chromium (source tree by default,
 *       or a published root), read every frontage buffer it built and compare
 *       its sha256 with the Node build's, attribute by attribute.
 *   … --layer ground (or --layer frontage,ground) — T-2692, piece 1 of T-2678
 *       The same four modes for the GROUND: the epoch's ground GLB loaded,
 *       conformed, tiled and cut into spatial-batch pieces by terrain.js's and
 *       spatial-batch.js's own functions, into DIR/<year>/ground.{bin,json}. The
 *       self-test batches the file's pieces and holds every tile to the page's
 *       own spatialBatch of it; --parity reads the live page's ground tiles.
 *       Default is frontage alone, so publish.sh and check_published.mjs are
 *       unchanged until T-2693 makes the page upload the ground (see § the
 *       ground, below).
 *
 * WHAT IS AND IS NOT IN THE FILE. Every mesh the layer builds from its records:
 * the town's timber and each chunk (a block face's walk, crossing and fence).
 * Two meshes stay with the page, because neither is the expensive part and
 * neither can be made here: the far walk tops (`createFarWalkTops`, a copy of
 * the upward faces above, re-indexed as the visitor moves) and the lettering,
 * whose texture is drawn on a canvas. Materials and the relief grain are the
 * page's too; this file carries geometry and the census.
 *
 * THE TERRAIN. `createFrontage` asks its terrain three things: `surfaceHeight`,
 * `isWater` and `protectGroundUnder`. In the page those are one-liners over the
 * scene's Heightfield (terrain.js), and here they are the same one-liners over
 * the same class adopting the same heightfield. A scene with an apron field or
 * 1904's context coast is refused, not approximated: no scene that draws
 * frontage has one, and the parity read is what would catch the day that moves.
 */
import { register } from 'node:module';
import { MessageChannel } from 'node:worker_threads';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import zlib from 'node:zlib';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(here, '..');
const WEB = path.join(ROOT, 'renderers/web');
const THREE_DIR = path.join(WEB, 'vendor/three-0.185.1');
/** 2 since T-2677: the tape, pick spans, walk-top ranges, spheres and build.
 *  3 since T-2687: each mesh's position, uniform scale and quantization. */
const FORMAT = 4;
/** Built by the page for itself, never carried in the file (see the header). */
const PAGE_ONLY = new Set(['frontage-far-walk-tops', 'frontage-lettering']);

const argv = process.argv.slice(2);
const has = (f) => argv.includes(f);
const flag = (f) => { const i = argv.indexOf(f); return i >= 0 ? argv[i + 1] : null; };
const rel = (p) => path.relative(ROOT, p).split(path.sep).join('/');
const sha = (buf) => createHash('sha256').update(buf).digest('hex');

/* -------------------------------------------------------------------------- */
/* the page's modules, loaded in Node                                          */
/* -------------------------------------------------------------------------- */

// The import map's two entries, as a resolve hook; the load hook reports every
// module file the build touched, so the input hash covers the code as well as
// the data.
const HOOKS = `
let port, three, addons;
export function initialize(data) { port = data.port; three = data.three; addons = data.addons; }
export async function resolve(spec, ctx, next) {
  if (spec === 'three') return { url: three, shortCircuit: true };
  if (spec.startsWith('three/addons/')) return { url: addons + spec.slice(13), shortCircuit: true };
  return next(spec, ctx);
}
export async function load(url, ctx, next) {
  if (url.startsWith('file:')) port.postMessage(url);
  return next(url, ctx);
}`;
const modulesRead = new Set();
const dataRead = new Set();
let loaded = null;

async function pageModules() {
  if (loaded) return loaded;
  const { port1, port2 } = new MessageChannel();
  port1.on('message', (url) => modulesRead.add(fileURLToPath(url)));
  port1.unref();
  register('data:text/javascript,' + encodeURIComponent(HOOKS), {
    data: { port: port2, three: pathToFileURL(path.join(THREE_DIR, 'three.module.js')).href,
      addons: pathToFileURL(THREE_DIR).href + '/addons/' },
    transferList: [port2],
  });
  // What the page's modules reach for while building: the document's location
  // (scene-loader.js resolveBases), a canvas that answers no context (the
  // lettering declines to draw, as it does on a page with no 2D context) and
  // fetch over file: URLs, which Node's own fetch refuses.
  globalThis.window ??= { location: new URL(pathToFileURL(path.join(WEB, 'index.html')).href) };
  globalThis.document ??= { createElement: () => ({ getContext: () => null }) };
  const netFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    const u = new URL(String(url));
    if (u.protocol !== 'file:') return netFetch(url, init);
    const file = fileURLToPath(u);
    if (!fs.existsSync(file)) return new Response(null, { status: 404, statusText: 'Not Found' });
    dataRead.add(file);
    return new Response(fs.readFileSync(file), { status: 200 });
  };
  const { Heightfield, loadGlbMesh, conformGroundToField, tileGround, groundTileGrid, groundTiling } =
    await import(pathToFileURL(path.join(WEB, 'js/terrain.js')).href);
  const { createFrontage } = await import(pathToFileURL(path.join(WEB, 'js/frontage.js')).href);
  const { spatialPieces, spatialBatch, batchPieces } =
    await import(pathToFileURL(path.join(WEB, 'js/spatial-batch.js')).href);
  loaded = { Heightfield, createFrontage, loadGlbMesh, conformGroundToField, tileGround, groundTileGrid,
    groundTiling, spatialPieces, spatialBatch, batchPieces };
  return loaded;
}

/** A tick for the loader thread's last module reports to arrive. */
const drain = () => new Promise((resolve) => setTimeout(resolve, 50));

/* -------------------------------------------------------------------------- */
/* building                                                                    */
/* -------------------------------------------------------------------------- */

export function frontageScenes() {
  const dir = path.join(ROOT, 'data/scenes');
  return fs.readdirSync(dir).filter((f) => f.endsWith('.json')).sort()
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')))
    .filter((s) => Array.isArray(s.layers) && s.layers.includes('frontage'));
}

const sceneYear = (scene) => String(scene.scene_id ?? scene.id ?? scene.year);

async function sceneTerrain(scene, Heightfield, fieldOnly = false) {
  if (scene.terrain_apron) {
    throw new Error(`scene ${sceneYear(scene)} carries an apron field, which this harness does not lay`);
  }
  if (sceneYear(scene) === '1904') throw new Error('1904 samples a context coast this harness does not lay');
  const metaFile = path.join(ROOT, 'data/terrain/epochs', scene.terrain_epoch, 'heightfield.json');
  const meta = JSON.parse(fs.readFileSync(metaFile, 'utf8'));
  const binFile = path.join(path.dirname(metaFile), meta.bin);
  const bin = fs.readFileSync(binFile);
  dataRead.add(metaFile);
  dataRead.add(binFile);
  const hf = new Heightfield().adopt(meta, bin.buffer.slice(bin.byteOffset, bin.byteOffset + bin.length));
  const footprints = [];
  if (fieldOnly) return { hf, meta };
  // terrain.js createTerrain's own three answers, over the same field.
  const SHORE_Y = Number(fs.readFileSync(path.join(WEB, 'js/terrain.js'), 'utf8')
    .match(/^const SHORE_Y = (-?[\d.]+);/m)[1]);
  return {
    footprints,
    terrain: {
      surfaceHeight: (e, n) => hf.sample(e, n),
      isWater: (e, n) => hf.sample(e, n) < SHORE_Y,
      protectGroundUnder: (pts) => { footprints.push(...pts); },
    },
  };
}

/** The hash a prebuild is current against: every file the build read, by path. */
function inputsOf(files) {
  const list = [...files].map((f) => path.resolve(f)).filter((f) => f.startsWith(ROOT + path.sep))
    .sort().map((f) => ({ path: rel(f), sha256: sha(fs.readFileSync(f)) }));
  return { sha256: sha(list.map((f) => `${f.path} ${f.sha256}\n`).join('')), files: list };
}

/** A geometry's arrays, as the page holds them: name, typed-array kind, bytes. */
function geometryBuffers(g) {
  const attributes = Object.entries(g.attributes).map(([name, a]) => ({
    name, type: a.array.constructor.name, itemSize: a.itemSize, normalized: !!a.normalized,
    bytes: new Uint8Array(a.array.buffer, a.array.byteOffset, a.array.byteLength),
  }));
  const index = g.index ? { type: g.index.array.constructor.name,
    bytes: new Uint8Array(g.index.array.buffer, g.index.array.byteOffset, g.index.array.byteLength) } : null;
  return { attributes, index };
}

/** Each mesh's arrays, as the page holds them: name, typed-array kind, bytes. */
export function meshBuffers(group) {
  const meshes = [];
  for (const mesh of group.children) {
    if (!mesh.isMesh || PAGE_ONLY.has(mesh.name)) continue;
    const g = mesh.geometry;
    const { attributes, index } = geometryBuffers(g);
    const s = g.boundingSphere;
    // A quantized mesh's positions mean nothing without its box (T-2687): the
    // centre is the mesh's position and the half-extent its uniform scale.
    meshes.push({ name: mesh.name, userData: { ...mesh.userData }, castShadow: mesh.castShadow,
      receiveShadow: mesh.receiveShadow, renderOrder: mesh.renderOrder, attributes, index,
      bounding_sphere: s ? { center: s.center.toArray(), radius: s.radius } : null,
      position: mesh.position.toArray(), scale: mesh.scale.x,
      position_quantized: g.userData.positionQuantized ?? null,
      // The colour's fourth lane is the confidence (T-2689, compact-streams.js).
      confidence_lane: g.userData.confidenceLane ?? null });
  }
  return meshes;
}

export async function buildFrontage(scene, prebuilt = null) {
  const { Heightfield, createFrontage } = await pageModules();
  dataRead.clear();
  const { terrain, footprints } = await sceneTerrain(scene, Heightfield);
  const problems = [];
  const started = performance.now();
  const layer = await createFrontage({ dataBase: pathToFileURL(path.join(ROOT, 'data') + '/'),
    terrain, problems, record: !prebuilt, prebuilt });
  const ms = performance.now() - started;
  await drain();
  // The relief grain is a material's maps and loads from images; a Node build
  // has neither, and the geometry does not depend on it.
  const kept = problems.filter((p) => !/^frontage: .*(map|relief|grain|ktx2|Image)/i.test(p));
  if (kept.length) throw new Error(`frontage ${sceneYear(scene)}: ${kept.join('; ')}`);
  const meshes = meshBuffers(layer.group);
  if (layer.prebuild) {
    const { tape, spans, walkTopRanges } = layer.prebuild;
    // The tape travels as JSON, so it must come back exactly as it went.
    assert.deepStrictEqual(JSON.parse(JSON.stringify(tape)), tape, 'the tape does not survive JSON');
    assert.equal(walkTopRanges.length, meshes.length, 'one walk-top range list per mesh');
    meshes.forEach((m, i) => { m.walk_top_ranges = walkTopRanges[i]; });
    return { meshes, census: { ...layer.census }, footprints, ms, tape, spans, layer };
  }
  return { meshes, census: { ...layer.census }, footprints, ms, layer };
}

/** One buffer laid array by array, each 4-byte aligned: `place` says where. */
function layout() {
  const parts = [];
  let offset = 0;
  return {
    place(bytes) {
      const pad = (4 - (offset % 4)) % 4;
      if (pad) { parts.push(new Uint8Array(pad)); offset += pad; }
      parts.push(bytes);
      const at = offset;
      offset += bytes.byteLength;
      return { offset: at, byteLength: bytes.byteLength, sha256: sha(bytes) };
    },
    bin: () => Buffer.concat(parts.map((p) => Buffer.from(p.buffer, p.byteOffset, p.byteLength))),
  };
}

/** Lay the meshes into one buffer, each array 4-byte aligned, and its index. */
function pack(year, built, inputs, buildId, gzip = false) {
  const { place, bin: concat } = layout();
  const meshes = built.meshes.map((m) => ({
    name: m.name, userData: m.userData, castShadow: m.castShadow, receiveShadow: m.receiveShadow,
    renderOrder: m.renderOrder,
    attributes: m.attributes.map(({ bytes, ...a }) => ({ ...a, ...place(bytes) })),
    index: m.index ? { type: m.index.type, ...place(m.index.bytes) } : null,
    bounding_sphere: m.bounding_sphere, walk_top_ranges: m.walk_top_ranges,
    position: m.position, scale: m.scale, position_quantized: m.position_quantized, confidence_lane: m.confidence_lane,
  }));
  const bin = concat();
  const index = {
    layer: 'frontage', year, format: FORMAT, ticket: 'T-2677', build: buildId,
    bin: gzip ? 'frontage.bin.gz' : 'frontage.bin', encoding: gzip ? 'gzip' : null, passes: gzip ? GZIP_PASSES : 0,
    bytes: bin.length, sha256: sha(bin),
    inputs, census: built.census, protect_ground_under: built.footprints.length,
    spans: built.spans, tape: built.tape, meshes,
  };
  return { bin, index };
}

/**
 * `gzip` is how publish.sh writes it: 74.5 MiB raw would take the published tree
 * past validate.py's 320 MiB (it measured 373.7), and both the live site and the
 * dev preview share GitHub Pages' 1 GiB. Gzipped TWICE it is 6.93 MB — one pass
 * is 10.76 MB, because deflate's 32 KB window is far shorter than the runs the
 * timber repeats over — and a server that would have gzipped it again gains
 * nothing more. The page inflates both passes on a pool worker.
 */
const GZIP_PASSES = 2;
const gzipped = (bin) => { let b = bin; for (let i = 0; i < GZIP_PASSES; i += 1) b = zlib.gzipSync(b, { level: 9 }); return b; };

/* -------------------------------------------------------------------------- */
/* the ground (T-2692)                                                         */
/* -------------------------------------------------------------------------- */

/**
 * THE GROUND'S TILES, PARTITIONED — T-2692, the first piece of T-2678. The 1835
 * ground is 222 of the page's 231 spatial-batch calls (587k vertices), and at the
 * phone profile loading, conforming, tiling and partitioning it costs 3.0 s of
 * terrain's 8.8 s (measured 2026-10-16). createTerrain loads the epoch's ground
 * GLB, conforms it to the heightfield, cuts it into ~240 m tiles and hands every
 * tile but the thin remainder to spatialBatchAsync, which cuts it again into 40 m
 * pieces and batches them. Here the same functions — terrain.js's loadGlbMesh,
 * conformGroundToField, tileGround and groundTileGrid, and spatial-batch.js's
 * spatialPieces, the kernel the pool runs — read the same files, and the file
 * carries each tile's PIECES: exactly what the page's BatchedMesh is made of, so
 * a page reading them has only to batch them (`batchPieces`) and upload (T-2693).
 * The thin remainder travels as itself. Materials, shadows and the confidence
 * patch are the page's, as they are for frontage.
 */
const GROUND_FORMAT = 1;
const LAYERS = { frontage: { format: FORMAT }, ground: { format: GROUND_FORMAT } };
const ARRAYS = { Float32Array, Int8Array, Uint8Array, Int16Array, Uint16Array, Int32Array, Uint32Array };
const THREE_URL = () => pathToFileURL(path.join(THREE_DIR, 'three.module.js')).href;

export async function buildGround(scene) {
  const m = await pageModules();
  dataRead.clear();
  const year = sceneYear(scene);
  const { hf, meta } = await sceneTerrain(scene, m.Heightfield, true);
  const groundPath = meta.glb?.ground;
  if (!groundPath) throw new Error(`ground ${year}: the epoch names no ground GLB, so the page grids the field itself`);
  const started = performance.now();
  // scene-loader.js's source-tree asset base; publish.sh mirrors the same files.
  const ground = await m.loadGlbMesh(new URL(groundPath, pathToFileURL(path.join(ROOT, 'assets') + '/')));
  // The page's confidence.ensureAttribute ADDS a zero attribute to a ground that has
  // none. That is not copied here: such a ground is refused, and no epoch is one.
  if (!ground.geometry.getAttribute('_confidence')) throw new Error(`ground ${year}: ${groundPath} has no _CONFIDENCE`);
  const fit = m.conformGroundToField(ground.geometry, hf);
  if (fit && fit.residual_max_m > 1e-5) throw new Error(`ground ${year}: ${fit.residual_max_m} m off the field after conforming`);
  const source = m.tileGround(ground, m.groundTileGrid);
  if (!source) throw new Error(`ground ${year}: too coarse to tile, so the page draws it whole`);
  const tiles = source.map((tile) => (tile.name.endsWith('__tthin')
    ? { name: tile.name, thin: true, ...geometryBuffers(tile.geometry) }
    : { name: tile.name, pieces: m.spatialPieces(tile.geometry).map(geometryBuffers) }));
  const ms = performance.now() - started;
  await drain();
  return { tiles, source, ms, fit, tiling: { ...m.groundTiling() } };
}

function packGround(year, built, inputs, buildId, gzip = false) {
  const { place, bin: concat } = layout();
  // 9,405 pieces. Written out in full — a name, type and sha256 per array — the
  // index came to 9.5 MB, so a tile states its attributes ONCE and each piece is
  // only where its arrays lie: [[offset, byteLength] per attribute, index]. The
  // buffer's own sha256 covers every array in it.
  const at = (bytes) => { const { offset, byteLength } = place(bytes); return [offset, byteLength]; };
  const tiles = built.tiles.map((t) => {
    const pieces = t.thin ? [t] : t.pieces;
    const schema = ({ attributes }) => attributes.map(({ name, type, itemSize, normalized }) => ({ name, type, itemSize, normalized }));
    const attributes = schema(pieces[0]);
    for (const p of pieces) assert.deepStrictEqual(schema(p), attributes, `${t.name}: its pieces disagree on their attributes`);
    return { name: t.name, ...(t.thin ? { thin: true } : {}), attributes,
      pieces: pieces.map((p) => [p.attributes.map((x) => at(x.bytes)), p.index ? [p.index.type, ...at(p.index.bytes)] : null]) };
  });
  const bin = concat();
  const index = {
    layer: 'ground', year, format: GROUND_FORMAT, ticket: 'T-2692', build: buildId,
    bin: gzip ? 'ground.bin.gz' : 'ground.bin', encoding: gzip ? 'gzip' : null, passes: gzip ? GZIP_PASSES : 0,
    bytes: bin.length, sha256: sha(bin), inputs, tiling: built.tiling, conform: built.fit, tiles,
  };
  return { bin, index };
}

/** A prebuilt ground read back the way a page would: each tile's pieces batched. */
export async function replayGround(index, bin) {
  const { batchPieces } = await pageModules();
  const THREE = await import(THREE_URL());
  const view = (a) => new ARRAYS[a.type](bin.buffer.slice(bin.byteOffset + a.offset,
    bin.byteOffset + a.offset + a.byteLength));
  const geometry = (g) => {
    const geo = new THREE.BufferGeometry();
    for (const a of g.attributes) geo.setAttribute(a.name, new THREE.BufferAttribute(view(a), a.itemSize, a.normalized));
    if (g.index) geo.setIndex(new THREE.BufferAttribute(view(g.index), 1));
    return geo;
  };
  return index.tiles.map((t) => {
    const pieces = t.pieces.map(([arrays, ix]) => ({
      attributes: t.attributes.map((a, i) => ({ ...a, offset: arrays[i][0], byteLength: arrays[i][1] })),
      index: ix && { type: ix[0], offset: ix[1], byteLength: ix[2] } }));
    const mesh = t.thin ? new THREE.Mesh(geometry(pieces[0])) : batchPieces(pieces.map(geometry));
    mesh.name = t.name;
    return mesh;
  });
}

/** What a drawn ground tile is, by hash: the page's parity read is the same shape. */
export function tileHashes(mesh) {
  const hex = (a) => sha(new Uint8Array(a.buffer, a.byteOffset, a.byteLength));
  const g = mesh.geometry;
  return { name: mesh.name, batched: !!mesh.isBatchedMesh, pieces: mesh.userData.spatialBatch?.pieces ?? null,
    attributes: Object.entries(g.attributes).map(([name, a]) => [name, a.array.constructor.name, hex(a.array)]),
    index: g.index ? hex(g.index.array) : null };
}

/** The page's own path over the Node build's source tiles: spatialBatch, or the thin tile as it is. */
async function pageGround(built) {
  const { spatialBatch } = await pageModules();
  return built.source.map((tile) => {
    if (tile.name.endsWith('__tthin')) return tile;
    const batch = spatialBatch(tile.geometry);
    batch.name = tile.name;
    return batch;
  });
}

export async function build(outDir, buildId = null, { gzip = false, layers = ['frontage'] } = {}) {
  const results = [];
  for (const scene of frontageScenes()) {
    const year = sceneYear(scene);
    const dir = path.join(outDir, year);
    fs.mkdirSync(dir, { recursive: true });
    if (layers.includes('ground')) {
      const built = await buildGround(scene);
      const inputs = inputsOf([...dataRead, ...modulesRead]);
      const { bin, index } = packGround(year, built, inputs, buildId, gzip);
      fs.writeFileSync(path.join(dir, index.bin), gzip ? gzipped(bin) : bin);
      fs.writeFileSync(path.join(dir, 'ground.json'), JSON.stringify(index) + '\n');
      results.push({ layer: 'ground', year, dir, ms: Math.round(built.ms), bytes: bin.length, sha256: index.sha256,
        meshes: index.tiles.length, pieces: index.tiles.reduce((n, t) => n + t.pieces.length, 0),
        inputs: inputs.files.length, index, built });
    }
    if (!layers.includes('frontage')) continue;
    const built = await buildFrontage(scene);
    const inputs = inputsOf([...dataRead, ...modulesRead]);
    const { bin, index } = pack(year, built, inputs, buildId, gzip);
    fs.writeFileSync(path.join(dir, index.bin), gzip ? gzipped(bin) : bin);
    fs.writeFileSync(path.join(dir, 'frontage.json'), JSON.stringify(index, null, 1) + '\n');
    results.push({ layer: 'frontage', year, dir, ms: Math.round(built.ms), bytes: bin.length, sha256: index.sha256,
      meshes: index.meshes.length, inputs: inputs.files.length, index });
  }
  return results;
}

/* -------------------------------------------------------------------------- */
/* staleness                                                                   */
/* -------------------------------------------------------------------------- */

/** Why DIR's prebuild of `layer` may not ship, or [] when every index is current. */
export function stale(outDir, layer = 'frontage') {
  const why = [];
  const years = frontageScenes().map(sceneYear);
  const format = LAYERS[layer].format;
  for (const year of years) {
    const file = path.join(outDir, year, `${layer}.json`);
    if (!fs.existsSync(file)) { why.push(`${year}: no ${layer}.json`); continue; }
    const index = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (index.format !== format) { why.push(`${year}: format ${index.format}, this tool writes ${format}`); continue; }
    const bin = path.join(outDir, year, index.bin);
    const raw = (file) => {
      let b = fs.readFileSync(file);
      for (let i = 0; index.encoding === 'gzip' && i < (index.passes ?? 1); i += 1) b = zlib.gunzipSync(b);
      return b;
    };
    if (!fs.existsSync(bin) || sha(raw(bin)) !== index.sha256) {
      why.push(`${year}: ${index.bin} is not the buffer its index hashed`);
    }
    const missing = index.inputs.files.filter((f) => !fs.existsSync(path.join(ROOT, f.path)));
    for (const f of missing) why.push(`${year}: input ${f.path} is gone`);
    if (missing.length) continue;
    const now = inputsOf(index.inputs.files.map((f) => path.join(ROOT, f.path)));
    if (now.sha256 !== index.inputs.sha256) {
      const moved = now.files.filter((f, i) => f.sha256 !== index.inputs.files[i]?.sha256).map((f) => f.path);
      why.push(`${year}: built from inputs that have since changed${moved.length
        ? ` (${moved.slice(0, 5).join(', ')}${moved.length > 5 ? ', …' : ''})` : ' (the index was edited)'}`);
    }
  }
  return why;
}

/* -------------------------------------------------------------------------- */
/* parity with the live page                                                   */
/* -------------------------------------------------------------------------- */

async function parity(results, root) {
  const { environment } = await import('./measure_boot_phases.mjs');
  const env = await environment(root);
  const url = root === ROOT ? env.url.replace('/walk/', '/renderers/web/') : env.url;
  try {
    const page = await env.browser.newPage({ viewport: { width: 1280, height: 800 } });
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(url);
    await page.waitForFunction(() => window.__chicago4d?.ready, null, { timeout: 300000 });
    const live = await page.evaluate(async (pageOnly) => {
      const hex = async (a) => [...new Uint8Array(await crypto.subtle.digest('SHA-256',
        new Uint8Array(a.buffer, a.byteOffset, a.byteLength)))].map((b) => b.toString(16).padStart(2, '0')).join('');
      const api = window.__chicago4d;
      const out = [];
      for (const mesh of api.frontage.group.children) {
        if (!mesh.isMesh || pageOnly.includes(mesh.name)) continue;
        const g = mesh.geometry;
        const attributes = [];
        for (const [name, a] of Object.entries(g.attributes)) {
          attributes.push({ name, type: a.array?.constructor.name ?? null,
            sha256: a.array ? await hex(a.array) : null });
        }
        out.push({ name: mesh.name, attributes,
          index: g.index ? await hex(g.index.array) : null });
      }
      return { meshes: out, missing: [...(api.buildings?.missing ?? [])] };
    }, [...PAGE_ONLY]);
    const r = results.find((x) => x.year === '1835' && x.layer === 'frontage');
    const node = r.index.meshes;
    const diffs = [];
    if (live.missing.length) diffs.push(`the page lost buildings ${live.missing.join(', ')}, so its posts differ by design`);
    if (live.meshes.length !== node.length) diffs.push(`meshes: page ${live.meshes.length}, node ${node.length}`);
    let attributes = 0;
    let matched = 0;
    live.meshes.forEach((m, i) => {
      const n = node[i];
      if (!n || n.name !== m.name) { diffs.push(`mesh ${i}: page ${m.name}, node ${n?.name}`); return; }
      for (const a of m.attributes) {
        attributes += 1;
        const b = n.attributes.find((x) => x.name === a.name);
        if (b && b.type === a.type && b.sha256 === a.sha256) matched += 1;
        else diffs.push(`mesh ${i} (${m.name}) ${a.name}: page ${a.type}/${a.sha256?.slice(0, 12)}, node ${b?.type}/${b?.sha256.slice(0, 12)}`);
      }
      if (m.attributes.length !== n.attributes.length) diffs.push(`mesh ${i}: attribute count differs`);
      if ((m.index ?? null) !== (n.index?.sha256 ?? null)) diffs.push(`mesh ${i}: index differs`);
    });
    return { year: '1835', url: url.replace(/^http:\/\/127\.0\.0\.1:\d+/, ''), meshes: live.meshes.length,
      attributes, matched, bytes: r.bytes, pageerrors: errors, diffs };
  } finally {
    await env.close();
  }
}

/** The ground's acceptance: the live page's tiles, by hash, against the file batched in Node. */
async function parityGround(results, root) {
  const r = results.find((x) => x.year === '1835' && x.layer === 'ground');
  const bin = fs.readFileSync(path.join(r.dir, r.index.bin));
  const node = (await replayGround(r.index, bin)).map(tileHashes);
  const { environment } = await import('./measure_boot_phases.mjs');
  const env = await environment(root);
  const url = root === ROOT ? env.url.replace('/walk/', '/renderers/web/') : env.url;
  try {
    const page = await env.browser.newPage({ viewport: { width: 1280, height: 800 } });
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(url);
    await page.waitForFunction(() => window.__chicago4d?.ready, null, { timeout: 300000 });
    const live = await page.evaluate(async () => {
      const hex = async (a) => [...new Uint8Array(await crypto.subtle.digest('SHA-256',
        new Uint8Array(a.buffer, a.byteOffset, a.byteLength)))].map((b) => b.toString(16).padStart(2, '0')).join('');
      const out = [];
      for (const mesh of window.__chicago4d.scene3d.getObjectByName('terrain').children) {
        if (!/__t(\d+|thin)$/.test(mesh.name)) continue;
        const g = mesh.geometry;
        const attributes = [];
        for (const [name, a] of Object.entries(g.attributes)) {
          attributes.push([name, a.array?.constructor.name ?? null, a.array ? await hex(a.array) : null]);
        }
        out.push({ name: mesh.name, batched: !!mesh.isBatchedMesh, pieces: mesh.userData.spatialBatch?.pieces ?? null,
          attributes, index: g.index?.array ? await hex(g.index.array) : null });
      }
      return out;
    });
    const diffs = [];
    if (live.length !== node.length) diffs.push(`tiles: page ${live.length}, node ${node.length}`);
    let attributes = 0;
    let matched = 0;
    live.forEach((m, i) => {
      const n = node[i];
      if (!n || n.name !== m.name || n.batched !== m.batched || n.pieces !== m.pieces) {
        diffs.push(`tile ${i}: page ${m.name}/${m.pieces} pieces, node ${n?.name}/${n?.pieces} pieces`);
        return;
      }
      for (const [name, type, hash] of m.attributes) {
        attributes += 1;
        const b = n.attributes.find((x) => x[0] === name);
        if (b && b[1] === type && b[2] === hash) matched += 1;
        else diffs.push(`tile ${i} (${m.name}) ${name}: page ${type}/${hash?.slice(0, 12)}, node ${b?.[1]}/${b?.[2].slice(0, 12)}`);
      }
      if (m.attributes.length !== n.attributes.length) diffs.push(`tile ${i}: attribute count differs`);
      if (m.index !== n.index) diffs.push(`tile ${i}: index differs`);
    });
    return { layer: 'ground', year: '1835', url: url.replace(/^http:\/\/127\.0\.0\.1:\d+/, ''), meshes: live.length,
      pieces: live.reduce((s, m) => s + (m.pieces ?? 1), 0), attributes, matched, bytes: r.bytes, pageerrors: errors, diffs };
  } finally {
    await env.close();
  }
}

/* -------------------------------------------------------------------------- */

async function selfTestFrontage(a, b, ok) {
  const first = await build(a);
  const second = await build(b);
  ok(first.length > 0, `${first.length} scene(s) draw frontage and were built`);
  for (const [i, r] of first.entries()) {
    ok(r.sha256 === second[i].sha256, `${r.year}: two builds are byte-identical (${r.bytes} bytes, ${r.meshes} meshes)`);
  }
  ok(stale(a).length === 0, 'a fresh build is current');
  for (const r of first) {
    const scene = frontageScenes().find((x) => sceneYear(x) === r.year);
    const fresh = await buildFrontage(scene);
    const bin = fs.readFileSync(path.join(r.dir, 'frontage.bin'));
    const offered = { index: r.index, bin: bin.buffer.slice(bin.byteOffset, bin.byteOffset + bin.length) };
    const replayed = await buildFrontage(scene, offered);
    ok(replayed.layer.prebuilt.used, `${r.year}: the page's createFrontage takes the prebuild (${replayed.layer.prebuilt.why ?? 'used'})`);
    const same = (x, y) => { try { assert.deepStrictEqual(x, y); return true; } catch { return false; } };
    const bytes = (ms) => ms.map((m) => [m.name, m.userData, m.castShadow, m.receiveShadow, m.renderOrder,
      m.position, m.scale, m.position_quantized, m.confidence_lane, m.attributes.map((x) => [x.name, x.type, x.itemSize, x.normalized, sha(x.bytes)])]);
    ok(same(bytes(replayed.meshes), bytes(fresh.meshes)), `${r.year}: replayed meshes equal the build's, attribute for attribute (${fresh.meshes.length})`);
    const { relief: _a, ...cr } = replayed.census;
    const { relief: _b, ...cf } = fresh.census;
    ok(same(cr, cf), `${r.year}: replayed census equals the build's`);
    const plain = (l) => JSON.parse(JSON.stringify({ records: l.records.length, walks: l.walks.map((w) => w.id),
      posts: l.posts.map((x) => x.id), fittings: l.fittings.map((x) => x.id), fences: l.fences.map((x) => x.id),
      keepOut: l.keepOut, decks: l.walkableDecks, lettering: l.lettering ?? null,
      farTops: l.farWalkTops?.vertices ?? null, footprints: replayed === l ? replayed.footprints : fresh.footprints }));
    ok(same(plain(replayed.layer), plain(fresh.layer)), `${r.year}: replayed walks, posts, fittings, fences, keep-outs, decks and far tops equal the build's`);
    ok(same(r.index.spans, fresh.spans), `${r.year}: the index carries the build's pick spans (${fresh.spans.length})`);
    const moved = JSON.parse(JSON.stringify(r.index));
    moved.inputs.files.find((f) => f.path.startsWith('data/frontage/')).sha256 = '0'.repeat(64);
    const refused = await buildFrontage(scene, { index: moved, bin: offered.bin });
    ok(!refused.layer.prebuilt.used && /other frontage data/.test(refused.layer.prebuilt.why ?? ''),
      `${r.year}: a prebuild from other records is not replayed: ${refused.layer.prebuilt.why}`);
    ok(same(bytes(refused.meshes), bytes(fresh.meshes)), `${r.year}: …and the page builds its own instead`);
  }
  refusals(a, first[0], ok);
}

/** The two refusals --check makes, shown on DIR's first build of `r.layer`. */
function refusals(dir, r, ok) {
  const file = path.join(dir, r.year, `${r.layer}.json`);
  const index = JSON.parse(fs.readFileSync(file, 'utf8'));
  index.inputs.files[0].sha256 = '0'.repeat(64);
  index.inputs.sha256 = sha('edited');
  fs.writeFileSync(file, JSON.stringify(index));
  const refused = stale(dir, r.layer);
  ok(refused.length === 1 && /changed/.test(refused[0]), `${r.layer}: an index built from other inputs is refused: ${refused[0] ?? 'NOT refused'}`);
  fs.writeFileSync(path.join(dir, r.year, `${r.layer}.bin`), Buffer.from('not the build'));
  ok(stale(dir, r.layer).some((w) => /not the buffer/.test(w)), `${r.layer}: a buffer its index did not hash is refused`);
}

async function selfTestGround(a, b, ok) {
  const first = await build(a, null, { layers: ['ground'] });
  const second = await build(b, null, { layers: ['ground'] });
  ok(first.length > 0, `${first.length} scene(s) built their ground`);
  const same = (x, y) => { try { assert.deepStrictEqual(x, y); return true; } catch { return false; } };
  for (const [i, r] of first.entries()) {
    ok(r.sha256 === second[i].sha256, `${r.year}: two ground builds are byte-identical (${r.bytes} bytes, ${r.meshes} tiles, ${r.pieces} pieces)`);
    const bin = fs.readFileSync(path.join(r.dir, 'ground.bin'));
    const replayed = (await replayGround(r.index, bin)).map(tileHashes);
    const page = (await pageGround(r.built)).map(tileHashes);
    ok(same(replayed, page), `${r.year}: every tile batched from the file equals the page's own spatialBatch of it, attribute for attribute (${page.length} tiles)`);
    const inputs = r.index.inputs.files.map((f) => f.path);
    ok(['js/terrain.js', 'js/spatial-batch.js', 'js/jobs/spatial-kernel.js', 'heightfield.json', '.glb']
      .every((tail) => inputs.some((f) => f.endsWith(tail))), `${r.year}: the input hash covers the GLB, the field and the code that cut it`);
  }
  ok(stale(a, 'ground').length === 0, 'ground: a fresh build is current');
  refusals(a, first[0], ok);
}

async function main() {
  const layers = (flag('--layer') ?? 'frontage').split(',');
  for (const l of layers) if (!LAYERS[l]) { console.error(`prebuild_layers: no layer ${l} (${Object.keys(LAYERS).join(', ')})`); process.exit(2); }
  if (has('--check')) {
    const why = layers.flatMap((l) => stale(path.resolve(flag('--check')), l));
    for (const w of why) console.error(`stale: ${w}`);
    if (!why.length) console.log('prebuild_layers: current');
    process.exit(why.length ? 1 : 0);
  }
  if (has('--self-test')) {
    const a = fs.mkdtempSync(path.join(os.tmpdir(), 'prebuild-a-'));
    const b = fs.mkdtempSync(path.join(os.tmpdir(), 'prebuild-b-'));
    let fail = 0;
    const ok = (cond, what) => { console.log(`${cond ? 'ok  ' : 'FAIL'} ${what}`); if (!cond) fail += 1; };
    try {
      if (layers.includes('frontage')) await selfTestFrontage(a, b, ok);
      if (layers.includes('ground')) await selfTestGround(a, b, ok);
    } finally {
      fs.rmSync(a, { recursive: true, force: true });
      fs.rmSync(b, { recursive: true, force: true });
    }
    process.exit(fail ? 1 : 0);
  }
  const out = path.resolve(flag('--out') ?? fs.mkdtempSync(path.join(os.tmpdir(), 'prebuild-')));
  const results = await build(out, flag('--build'), { gzip: has('--gzip'), layers });
  const report = { out, scenes: results.map(({ index, dir, built, ...r }) => ({ ...r,
    ...(r.layer === 'frontage' ? { census: index.census } : { tiling: index.tiling, conform: index.conform }) })) };
  if (has('--parity')) {
    const root = path.resolve(flag('--root') ?? ROOT);
    if (layers.includes('frontage')) report.parity = await parity(results, root);
    if (layers.includes('ground')) report.ground_parity = await parityGround(results, root);
  }
  if (has('--json')) console.log(JSON.stringify(report, null, 1));
  else {
    for (const r of report.scenes) {
      console.log(`${r.year}: ${r.layer} built in ${r.ms} ms — ${r.meshes} ${r.layer === 'ground' ? `tiles, ${r.pieces} pieces` : 'meshes'}, `
        + `${r.bytes} bytes, ${r.inputs} inputs → ${path.join(out, r.year)}`);
    }
    for (const p of [report.parity, report.ground_parity].filter(Boolean)) {
      console.log(`parity ${p.layer ?? 'frontage'} ${p.year}: ${p.matched}/${p.attributes} attributes of ${p.meshes} meshes byte-equal `
        + `to the page; ${p.pageerrors.length} page errors`);
      for (const d of p.diffs) console.log(`  differs: ${d}`);
    }
  }
  const bad = (p) => p && (p.diffs.length || p.pageerrors.length || p.matched !== p.attributes);
  if (bad(report.parity) || bad(report.ground_parity)) process.exit(1);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
