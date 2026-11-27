#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
// photo_face_runtime.mjs — T-3775: the part of a photo-face library the walk reads.
//
//   node tools/photo_face_runtime.mjs            write runtime.json beside each library's review.json
//   node tools/photo_face_runtime.mjs --check    exit 1 if a runtime.json is not what its review.json gives,
//                                                or if any person would be drawn differently from it
//
// WHY. Since T-3767/T-3768 every visitor's boot fetches the two photo-face libraries
// (renderers/web/js/human-variation.js loadVariationKit), and on 2026-11-26 that put the 1835
// first visit 0.167 MB past SITE-BUDGET § 4. Each review.json is the review record
// tools/photo_face_library.py writes: source URLs, fit cameras and residuals, scalp shells,
// input hashes, limits, and every float at 17 digits. The walk reads none of that. It reads
// which face a person gets (photoFaceFor), the face's shape values, its place on the atlas and
// its eyes (human-skin.js dressPhotoEyes). This file keeps exactly those, so the boot carries
// the library and not its review.
//
// WHAT IS KEPT, and how:
//   * the library fields attachPhotoLibrary tests and personVariation lays out (format,
//     review_only, activation, tile_px, padding_px, cols, size_px, the light sheet and each
//     page's full sheet with their sizes and GPU bytes), verbatim;
//   * per face: id, sex, age, population, texture_only, base_body, index, page, page_index,
//     values, tone_rgb, eyes (sclera_linear, iris_linear, iris_gain, lid_rest, centres_uv,
//     iris_radius_m) and hair_projection (u, v);
//   * tone_rgb VERBATIM, because it weights the seeded draw of which face a person gets: a
//     rounded tone could, at a weight's edge, hand somebody another face. Every other float
//     to 6 significant figures (a colour or a UV to one part in a million; an iris to a
//     ten-thousandth of a millimetre), which is below what a float32 GPU attribute holds of it.
//   * review_sha256: the bytes of the review.json it was read from, so a rebuilt library with
//     a stale runtime file is caught here and not on the street.
// review.json stays the record (photo_face_library.py --check, tools/photo_face_review.html).
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const LIBRARIES = ['assets/humans/web/photo_faces/pilot', 'assets/humans/web/photo_faces/children'];
const LIBRARY_KEYS = ['format', 'review_only', 'activation', 'tile_px', 'padding_px', 'cols', 'size_px'];
const FACE_KEYS = ['id', 'sex', 'age', 'population', 'texture_only', 'base_body', 'index', 'page', 'page_index',
  'values', 'tone_rgb', 'body_gain', 'reference_pool', 'hair_rgb', 'eyes', 'hair_projection'];
const EYE_KEYS = ['sclera_linear', 'iris_linear', 'iris_gain', 'lid_rest', 'centres_uv', 'iris_radius_m'];
const sheet = (t) => ({ file: t.file, size_px: t.size_px, gpu_bytes_rgba8_mipmaps: t.gpu_bytes_rgba8_mipmaps });
const pick = (o, keys) => Object.fromEntries(keys.filter((k) => k in o).map((k) => [k, o[k]]));
const round = (v) => typeof v === 'number' ? (Number.isInteger(v) ? v : Number(v.toPrecision(6)))
  : Array.isArray(v) ? v.map(round)
  : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, round(x)])) : v;

export function runtimeOf(review, reviewBytes) {
  const lib = pick(review, LIBRARY_KEYS);
  lib.review_sha256 = crypto.createHash('sha256').update(reviewBytes).digest('hex');
  lib.textures = { light: sheet(review.textures.light) };
  lib.pages = review.pages.map((p) => ({ cols: p.cols, size_px: p.size_px, textures: { full: sheet(p.textures.full) } }));
  lib.faces = review.faces.map((f) => {
    const face = pick(f, FACE_KEYS);
    if (face.eyes) face.eyes = pick(face.eyes, EYE_KEYS);
    if (face.hair_projection) face.hair_projection = pick(face.hair_projection, ['u', 'v', 'hairline_v', 'fallback_gain']);
    const tone = face.tone_rgb, out = round(face);
    out.tone_rgb = tone;
    return out;
  });
  // One face to a line: small on the wire, and a rebuilt library diffs face by face.
  const { faces, ...head } = lib;
  return JSON.stringify(head).slice(0, -1) + ',"faces":[\n' + faces.map((f) => JSON.stringify(f)).join(',\n') + '\n]}\n';
}

async function sameDraws(dir, review, runtime) {
  const three = pathToFileURL(path.join(ROOT, 'renderers/web/vendor/three-0.185.1/three.module.js')).href;
  registerHooks({ resolve: (s, c, next) => s === 'three' ? { url: three, shortCircuit: true } : next(s, c) });
  const V = await import(pathToFileURL(path.join(ROOT, 'renderers/web/js/human-variation.js')).href);
  const header = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/humans/web/hm08_variation_kit.json')));
  const url = new URL(`https://example.org/${dir}/review.json`);
  const child = dir.endsWith('children');
  const attach = (lib) => { const k = { header }; (child ? V.attachChildPhotoLibrary : V.attachPhotoLibrary)(k, lib, url); return k; };
  const a = attach(review), b = attach(runtime), A = child ? a.photoChildren : a.photoFaces, B = child ? b.photoChildren : b.photoFaces;
  assert(A && B, `${dir}: both the review and its runtime file attach`);
  assert.equal(B.url, A.url, `${dir}: the crowd sheet resolves to the same file`);
  const complexions = [null, ...Object.keys(header.faces?.complexions ?? {})];
  let draws = 0;
  for (let i = 0; i < 4000; i++) for (const sex of ['male', 'female', ...(child ? ['either'] : [])]) {
    const age = child ? 2 + (i % 16) : 18 + (i % 70), complexion = complexions[i % complexions.length];
    const p = V.photoFaceFor(a, { key: `p${i}`, sex, age, complexion }), q = V.photoFaceFor(b, { key: `p${i}`, sex, age, complexion });
    assert.equal(q?.id, p?.id, `${dir}: person p${i} (${sex}, ${age}) would be given another face`);
    draws++;
  }
  return draws;
}

const check = process.argv.includes('--check');
let bad = 0;
for (const dir of LIBRARIES) {
  const reviewBytes = fs.readFileSync(path.join(ROOT, dir, 'review.json'));
  const review = JSON.parse(reviewBytes), text = runtimeOf(review, reviewBytes), file = path.join(ROOT, dir, 'runtime.json');
  if (!check) { fs.writeFileSync(file, text); console.log(`wrote ${dir}/runtime.json (${text.length} bytes from ${reviewBytes.length})`); continue; }
  const held = fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : null;
  if (held !== text) { console.error(`STALE: ${dir}/runtime.json is not what its review.json gives; run node tools/photo_face_runtime.mjs`); bad++; continue; }
  const draws = await sameDraws(dir, review, JSON.parse(held));
  console.log(`PASS: ${dir}/runtime.json is its review.json's runtime part (${held.length} of ${reviewBytes.length} bytes); ${draws} drawn people get the same face from either`);
}
process.exit(bad ? 1 : 0);
