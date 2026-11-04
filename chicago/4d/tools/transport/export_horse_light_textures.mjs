// SPDX-License-Identifier: GPL-3.0-or-later
// Image-only portable GLB derivative. Uses the same pinned Sharp encoder and
// Lanczos3/inside/no-upscale resize as tools/transport/farm_box/export_lods.mjs.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const flags = {};
for (let i = 2; i < process.argv.length; i += 2) { if (!process.argv[i].startsWith('--') || !process.argv[i + 1]) throw Error('Named arguments required'); flags[process.argv[i].slice(2)] = process.argv[i + 1]; }
for (const key of ['input', 'output-dir', 'tools-root', 'expect-sha256']) if (!flags[key]) throw Error(`Missing --${key}`);
const tools = path.resolve(flags['tools-root']);
if (JSON.parse(fs.readFileSync(path.join(tools, 'sharp/package.json'))).version !== '0.35.5') throw Error('Pinned Sharp0.35.5 required');
const sharp = require(path.join(tools, 'sharp'));
sharp.concurrency(1); sharp.cache(false);
const source = path.resolve(flags.input);
const output = path.resolve(flags['output-dir']);
fs.mkdirSync(output, { recursive: false });
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const raw = fs.readFileSync(source);
if (!/^[0-9a-f]{64}$/.test(flags['expect-sha256']) || digest(raw) !== flags['expect-sha256']) throw Error('Wrong immutable parent');
const jsonLength = raw.readUInt32LE(12), doc = JSON.parse(raw.subarray(20, 20 + jsonLength));
const original = structuredClone(doc), start = 20 + jsonLength;
if (raw.readUInt32LE(start + 4) !== 0x004e4942 || doc.buffers.length !== 1) throw Error('Single embedded BIN required');
const bin = raw.subarray(start + 8, start + 8 + raw.readUInt32LE(start));
const bytesOf = view => bin.subarray(view.byteOffset ?? 0, (view.byteOffset ?? 0) + view.byteLength);
const originalViews = doc.bufferViews.map(view => Buffer.from(bytesOf(view)));
const replacements = new Map(), images = [];
const mipBytes = (w, h) => { let n = 0; for (;;) { n += w * h * 4; if (w === 1 && h === 1) return n; w = Math.max(1, w >> 1); h = Math.max(1, h >> 1); } };
for (const [i, image] of doc.images.entries()) {
  if (typeof image.bufferView !== 'number' || image.uri) throw Error('Embedded source images required');
  const input = originalViews[image.bufferView], before = await sharp(input).metadata();
  if (![256, 1024].includes(before.width) || before.width !== before.height) throw Error('Unexpected source texture dimensions');
  const changed = before.width > 256;
  const result = changed ? await sharp(input).resize({ width: 256, height: 256, fit: 'inside', withoutEnlargement: true, kernel: 'lanczos3' }).png({ compressionLevel: 9 }).toBuffer() : input;
  const after = await sharp(result).metadata();
  if (after.width !== 256 || after.height !== 256) throw Error('Light texture dimension mismatch');
  if (changed) { replacements.set(image.bufferView, result); image.mimeType = 'image/png'; }
  // PNG is lossless relative to the declared resized pixel reference. No lossy
  // codec or additional normal-map quantisation is introduced.
  if (changed) {
    const reference = await sharp(input).resize({ width: 256, height: 256, fit: 'inside', withoutEnlargement: true, kernel: 'lanczos3' }).ensureAlpha().raw().toBuffer();
    const decoded = await sharp(result).ensureAlpha().raw().toBuffer();
    if (!reference.equals(decoded)) throw Error('Resized PNG pixel reference mismatch');
  } else if (!result.equals(input)) throw Error('Eye texture changed');
  images.push({ index: i, bufferView: image.bufferView, before: { width: before.width, height: before.height, mimeType: original.images[i].mimeType, bytes: input.length, sha256: digest(input), rgba8_full_mip_bytes: mipBytes(before.width, before.height) }, after: { width: after.width, height: after.height, mimeType: image.mimeType, bytes: result.length, sha256: digest(result), rgba8_full_mip_bytes: mipBytes(after.width, after.height) }, changed, resized_PNG_pixels_exact_to_declared_pipeline: true });
}
if (replacements.size !== 4 || images.filter(x => !x.changed).length !== 2) throw Error('Require four body replacements and two exact eye images');
const accessorsUsingImage = doc.accessors.filter(a => replacements.has(a.bufferView));
if (accessorsUsingImage.length) throw Error('Image buffer view unexpectedly used by geometry/animation');
const pieces = []; let cursor = 0;
doc.bufferViews.forEach((view, i) => {
  const pad = (4 - cursor % 4) % 4;
  if (pad) { pieces.push(Buffer.alloc(pad)); cursor += pad; }
  const piece = replacements.get(i) ?? originalViews[i];
  view.byteOffset = cursor; view.byteLength = piece.length;
  pieces.push(piece); cursor += piece.length;
});
doc.buffers[0].byteLength = cursor;
doc.asset.extras = { ...(doc.asset.extras ?? {}), light_texture_derivative: {
  source_sha256: digest(raw), policy: 'body-PNG256-eyes-original256-v1',
  scope: 'Image representations only; geometry, current26 rig, quiet and WALK streams retained. Actual phone rendering and aggregate cost unrun.',
  generated_by: 'tools/transport/export_horse_light_textures.mjs',
} };
let json = Buffer.from(JSON.stringify(doc)), data = Buffer.concat(pieces);
const jpad = (4 - json.length % 4) % 4; if (jpad) json = Buffer.concat([json, Buffer.alloc(jpad, 32)]);
const bpad = (4 - data.length % 4) % 4; if (bpad) data = Buffer.concat([data, Buffer.alloc(bpad)]);
const header = Buffer.alloc(20), bheader = Buffer.alloc(8);
header.writeUInt32LE(0x46546c67, 0); header.writeUInt32LE(2, 4); header.writeUInt32LE(28 + json.length + data.length, 8); header.writeUInt32LE(json.length, 12); header.writeUInt32LE(0x4e4f534a, 16);
bheader.writeUInt32LE(data.length, 0); bheader.writeUInt32LE(0x004e4942, 4);
const out = Buffer.concat([header, json, bheader, data]);
const filename = path.join(output, 'horse-current26-walk-light-body256-eye256.glb'); fs.writeFileSync(filename, out);
const reread = fs.readFileSync(filename), rjson = JSON.parse(reread.subarray(20, 20 + reread.readUInt32LE(12)));
const rstart = 20 + reread.readUInt32LE(12), rbin = reread.subarray(rstart + 8, rstart + 8 + reread.readUInt32LE(rstart));
const rows = originalViews.map((input, i) => {
  const view = rjson.bufferViews[i], actual = rbin.subarray(view.byteOffset ?? 0, (view.byteOffset ?? 0) + view.byteLength);
  if (!actual.equals(replacements.get(i) ?? input)) throw Error(`View ${i} byte preservation failed`);
  return { index: i, changed_image: replacements.has(i), original_sha256: digest(input), actual_sha256: digest(actual), bytes_exact: !replacements.has(i) };
});
// Compare the whole JSON after removing only layout, the four replaced image
// lengths, total buffer length and the explicit derivative provenance addition.
const strip = x => { const y = structuredClone(x); for (const v of y.bufferViews) { delete v.byteOffset; if (replacements.has(y.bufferViews.indexOf(v))) delete v.byteLength; } y.images.forEach((image, i) => { if (replacements.has(image.bufferView)) image.mimeType = original.images[i].mimeType; }); y.buffers[0].byteLength = 0; if (y.asset.extras) { delete y.asset.extras.light_texture_derivative; if (!Object.keys(y.asset.extras).length && !original.asset.extras) delete y.asset.extras; } return y; };
if (JSON.stringify(strip(original)) !== JSON.stringify(strip(rjson))) throw Error('Non-image JSON graph changed');
for (const [i, image] of rjson.images.entries()) {
  const view = rjson.bufferViews[image.bufferView];
  const actual = rbin.subarray(view.byteOffset, view.byteOffset + view.byteLength);
  const format = (await sharp(actual).metadata()).format;
  if (image.mimeType !== ({ png: 'image/png', jpeg: 'image/jpeg' }[format])) throw Error(`Image ${i} MIME does not describe actual bytes`);
}
const result = { status: 'ACTUAL_IMAGE_ONLY_LIGHT256_SOURCE_DERIVATION_PASS_NOT_ADOPTED', source: { path: source, bytes: raw.length, sha256: digest(raw) }, candidate: { path: filename, bytes: out.length, sha256: digest(out) }, images, all_buffer_view_rows: rows, complete_non_image_JSON_graph_exact: true, all_nonimage_bufferViews_byte_exact: true, geometry_skin_IBMs_animations_rig_clips_UVs_materials_slot_sampler_graph_exact: true, original_256_eye_image_bytes_exact: true, decoded_RGBA8_full_mip_image_bytes: images.reduce((sum, x) => sum + x.after.rgba8_full_mip_bytes, 0), actual_parent_native_qualification_receipt: null, actual_phone_visual_frame_memory_qualification: 'UNRUN', adoption: false, original_parent_unchanged: digest(fs.readFileSync(source)) === digest(raw), source_encoder: { sharp: '0.35.5', png: 'lossless', resize: 'Lanczos3 inside no-upscale256, existing portable pipeline semantics' }, command: process.argv };
fs.writeFileSync(path.join(output, 'CLOSED-IMAGE-ONLY-DERIVATION.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({ status: result.status, candidate: result.candidate, decoded_RGBA8_full_mip_image_bytes: result.decoded_RGBA8_full_mip_image_bytes }));
