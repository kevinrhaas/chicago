#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
// T-3559: the driven current26 horse's MID and FAR exports, from the exact near GLB, through
// the repository's pinned portable glTF stack (the farm box's: @gltf-transform 4.5.0,
// meshoptimizer 1.2.0, sharp 0.35.5; never downloaded here, pass --tools-root).
//
// Same 26-joint skin, inverse binds, node names, material names and three primitives (hair,
// body, eyes), so a far horse is the near horse's own skeleton under fewer triangles and
// smaller maps: the coat shader (horse-appearance.js) reads object-space position, which the
// simplifier keeps, so the coat does not change at a swap. Each primitive is simplified with
// meshoptimizer's attribute-aware simplifier inside a declared error bound (normals and UVs
// weighted), seams kept; the images are resized Lanczos3 and stored as WebP.
//
//   node tools/transport/horse_lods/export_horse_lods.mjs --tools-root <pinned node_modules> \
//     --output-dir <fresh dir>
// then copy horse-current26-{mid,far}.glb and EXPORT-RECEIPT.json where params.json says.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';

const flags = {};
for (let i = 2; i < process.argv.length; i += 2) { if (!process.argv[i]?.startsWith('--') || !process.argv[i + 1]) throw Error('Expected named arguments'); flags[process.argv[i].slice(2)] = process.argv[i + 1]; }
for (const name of ['output-dir', 'tools-root']) if (!flags[name]) throw Error(`Missing --${name}`);
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../..');
const paramsFile = path.join(here, 'params.json');
const P = JSON.parse(fs.readFileSync(paramsFile));
const tools = path.resolve(flags['tools-root']), require = createRequire(import.meta.url);
const pins = { '@gltf-transform/core': '4.5.0', '@gltf-transform/functions': '4.5.0', '@gltf-transform/extensions': '4.5.0', meshoptimizer: '1.2.0', sharp: '0.35.5' };
for (const [name, version] of Object.entries(pins)) if (JSON.parse(fs.readFileSync(path.join(tools, name, 'package.json'))).version !== version) throw Error(`Unreviewed ${name} version`);
const load = name => import(pathToFileURL(require.resolve(name, { paths: [tools] })).href);
const { NodeIO } = await load('@gltf-transform/core');
const { prune, weld, compactPrimitive, textureCompress } = await load('@gltf-transform/functions');
const { EXTMeshoptCompression, EXTTextureWebP } = await load('@gltf-transform/extensions');
const { MeshoptDecoder, MeshoptEncoder, MeshoptSimplifier } = await load('meshoptimizer');
const { default: sharp } = await load('sharp');
sharp.concurrency(1);
await Promise.all([MeshoptEncoder.ready, MeshoptDecoder.ready, MeshoptSimplifier.ready]);
const io = new NodeIO().registerExtensions([EXTMeshoptCompression, EXTTextureWebP]).registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });
const digest = raw => crypto.createHash('sha256').update(raw).digest('hex');
const mip = (w, h) => { let n = 0; for (;;) { n += w * h * 4; if (w === 1 && h === 1) return n; w = Math.max(1, w >> 1); h = Math.max(1, h >> 1); } };

const input = path.join(root, P.input), raw = fs.readFileSync(input);
if (digest(raw) !== P.input_sha256) throw Error('Wrong immutable near horse');
const output = path.resolve(flags['output-dir']);
if (fs.existsSync(output) && fs.readdirSync(output).length) throw Error('Fresh export directory required');
fs.mkdirSync(output, { recursive: true });

const rig = doc => {
  const skin = doc.getRoot().listSkins()[0];
  return { joints: skin.listJoints().map(j => j.getName()), ibm: Array.from(skin.getInverseBindMatrices().getArray()).map(x => Math.round(x * 1e6) / 1e6),
    nodes: doc.getRoot().listNodes().map(n => [n.getName(), n.getTranslation(), n.getRotation(), n.getScale()]),
    materials: doc.getRoot().listMaterials().map(m => m.getName()), meshes: doc.getRoot().listMeshes().map(m => m.listPrimitives().map(p => p.getMaterial().getName())) };
};
const cost = doc => { let triangles = 0, vertices = 0; for (const m of doc.getRoot().listMeshes()) for (const p of m.listPrimitives()) { triangles += p.getIndices().getCount() / 3; vertices += p.getAttribute('POSITION').getCount(); } return { triangles, vertices }; };
const near = await io.read(input), nearRig = JSON.stringify(rig(near)), nearCost = cost(near);
const receipt = { schema: 'chicago4d_horse_portable_lods_v1', ticket: 'T-3559', input: P.input, input_sha256: P.input_sha256,
  params_sha256: digest(fs.readFileSync(paramsFile)), exporter_sha256: digest(fs.readFileSync(fileURLToPath(import.meta.url))), tool_versions: pins,
  near: { file: P.input, sha256: P.input_sha256, bytes: raw.length, ...nearCost }, lods: [],
  contract: 'Same skin (26 joints, inverse binds), nodes, material names and primitive order as the near horse; only triangle indices (within each primitive) and image sizes change. Animation clips are dropped: the renderer drives these meshes from the near clone\'s bones.' };
for (const [level, spec] of Object.entries(P.levels)) {
  const doc = await io.read(input);
  for (const a of doc.getRoot().listAnimations()) a.dispose();
  await doc.transform(weld({ tolerance: 0 }));
  const rows = [];
  for (const mesh of doc.getRoot().listMeshes()) for (const prim of mesh.listPrimitives()) {
    const material = prim.getMaterial().getName(), want = spec.primitives[material];
    if (!want) throw Error(`no ${level} rule for ${material}`);
    const pos = prim.getAttribute('POSITION').getArray(), nor = prim.getAttribute('NORMAL').getArray(), uv = prim.getAttribute('TEXCOORD_0').getArray();
    const count = pos.length / 3, attrs = new Float32Array(count * 5);
    for (let i = 0; i < count; i++) attrs.set([nor[i * 3], nor[i * 3 + 1], nor[i * 3 + 2], uv[i * 2], uv[i * 2 + 1]], i * 5);
    const before = new Uint32Array(prim.getIndices().getArray());
    const [idx, err] = MeshoptSimplifier.simplifyWithAttributes(before, pos, 3, attrs, 5,
      [want.normal_weight, want.normal_weight, want.normal_weight, want.uv_weight, want.uv_weight], null,
      Math.floor(before.length * want.ratio / 3) * 3, want.error, []);
    if (err > want.error + 1e-7) throw Error(`${level} ${material}: error ${err} over ${want.error}`);
    prim.setIndices(prim.getIndices().clone().setArray(idx)); compactPrimitive(prim);
    rows.push({ material, input_triangles: before.length / 3, output_triangles: idx.length / 3, reported_error: err, ...want });
  }
  await doc.transform(prune({ keepLeaves: true, keepAttributes: true, keepIndices: true, keepSolidTextures: true }));
  await doc.transform(
    textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [spec.texture_size, spec.texture_size], quality: spec.quality, slots: /^(baseColorTexture|emissiveTexture)$/ }),
    textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [spec.texture_size, spec.texture_size], quality: 97, nearLossless: true, slots: /^(metallicRoughnessTexture|occlusionTexture)$/ }),
    textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [spec.texture_size, spec.texture_size], lossless: true, slots: /^normalTexture$/ }));
  if (JSON.stringify(rig(doc)) !== nearRig) throw Error(`${level}: rig, nodes or materials changed`);
  doc.createExtension(EXTMeshoptCompression).setRequired(true).setEncoderOptions({ method: EXTMeshoptCompression.EncoderMethod.QUANTIZE });
  const file = path.join(output, `horse-current26-${level}.glb`);
  await io.write(file, doc);
  const back = await io.read(file);
  if (JSON.stringify(rig(back)) !== nearRig) throw Error(`${level}: stored rig differs`);
  const sizes = back.getRoot().listTextures().map(t => t.getSize());
  const row = { level, file: path.basename(file), sha256: digest(fs.readFileSync(file)), bytes: fs.statSync(file).size, ...cost(back),
    texture_dimensions: sizes, texture_RGBA8_mip_estimate_bytes: sizes.reduce((n, [w, h]) => n + mip(w, h), 0), primitives: rows };
  receipt.lods.push(row); console.log(JSON.stringify({ level, bytes: row.bytes, triangles: row.triangles, sizes }));
}
fs.writeFileSync(path.join(output, 'EXPORT-RECEIPT.json'), JSON.stringify(receipt, null, 2) + '\n');
