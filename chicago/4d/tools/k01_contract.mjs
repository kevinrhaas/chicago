#!/usr/bin/env node
/**
 * k01_contract.mjs — T-2265 (piece 1 of T-1843, package K01 of the owner's Prairie
 * Avenue 1904 programme T-1837). THE METRIC COMPONENT CONTRACT, AND THE CANONICAL
 * GLESSNER ASSET MEASURED AGAINST IT.
 *
 * Every reusable part of the Prairie programme (walls, openings, roofs, stairs) is to be
 * built in metres against declared datums, with stable ids, seeds, sockets, material
 * slots and per-parameter provenance. The contract is data —
 * data/components/prairie_1904/k01_contract.json — so a generator, a renderer and this
 * gate all read one statement of it. The baseline beside it,
 * data/components/prairie_1904/glessner_baseline.json, is the canonical Glessner v4
 * asset (all three tiers) measured by the contract's own rules: hashes, scale drift
 * between tiers, the plan and vertical origin against the record's footprint,
 * coincident (duplicated) faces, and full/web/light mesh and texture costs.
 *
 *   node tools/k01_contract.mjs --check      the gate: the contract is well-formed, the
 *                                             baseline answers every acceptance measure,
 *                                             and its hashes are the package's — so a
 *                                             rebake that is not re-measured fails here
 *   node tools/k01_contract.mjs --self-test  the measures, proved on synthetic GLBs
 *   node tools/k01_contract.mjs --measure-asset <structure_id>
 *                                             WRITES <structure_id>.measure.json beside
 *                                             the contract: an assembly BUILT to K01
 *                                             (T-2266), its full and web tiers measured
 *                                             by the same rules. Unlike Glessner's, its
 *                                             verdicts must all be ok — a new component
 *                                             may not carry a finding (coincident faces
 *                                             allowed new: 0) — and --check holds its
 *                                             hashes to the committed GLBs
 *   node tools/k01_contract.mjs --measure    WRITES the baseline from the three GLBs
 *                                             (`python3 tools/recover_glessner_v4.py
 *                                             --materialize` first on a fresh clone);
 *                                             ~1 min, a deliberate act after a rebake —
 *                                             never part of the gate
 *
 * The gate never decodes a GLB: the measurement is committed, and the hashes tie it to
 * the bytes it measured (docs/RESEARCH/glessner-v4-recovery/manifest.json).
 */
import { readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const APP = path.resolve(HERE, '..');
const CONTRACT = 'data/components/prairie_1904/k01_contract.json';
const BASELINE = 'data/components/prairie_1904/glessner_baseline.json';
const PACKAGE = 'docs/RESEARCH/glessner-v4-recovery/manifest.json';
const RECORD = 'data/structures/glessner_house.json';
const LIBRARY = 'assets/textures/glessner-v4/material-library.json';
// T-2293: the K04 roof library's fabrics, measured by the same metric-UV rule
const ROOF_LIBRARY = 'assets/textures/prairie_1904_roofs/manifest.json';
const fabricLibrary = () => [...readJson(LIBRARY).materials,
  ...(existsSync(path.join(APP, ROOF_LIBRARY)) ? readJson(ROOF_LIBRARY).materials.map((m) => ({ name: m.id, tile_m: m.tile_m })) : [])];
const TIERS = [
  ['full', 'assets/gltf/glessner_house__as_built_1887.glb'],
  ['web', 'assets/web/glessner_house__as_built_1887.glb'],
  ['light', 'assets/web/glessner_house__as_built_1887.light.glb'],
];
const readJson = (p) => JSON.parse(readFileSync(path.join(APP, p), 'utf8'));

// ---------------------------------------------------------------------------
// GLB reading: chunks, meshopt-compressed buffer views, quantized accessors
// ---------------------------------------------------------------------------

export function parseGlb(buf) {
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  if (dv.getUint32(0, true) !== 0x46546c67) throw new Error('not a GLB');
  let off = 12, json = null, bin = null;
  while (off < dv.getUint32(8, true)) {
    const len = dv.getUint32(off, true), type = dv.getUint32(off + 4, true);
    const chunk = buf.subarray(off + 8, off + 8 + len);
    if (type === 0x4e4f534a) json = JSON.parse(Buffer.from(chunk).toString('utf8'));
    else if (type === 0x004e4942 && !bin) bin = chunk;
    off += 8 + len + ((4 - (len % 4)) % 4);
  }
  return { json, bin };
}

async function decoder() {
  const m = await import('../renderers/web/vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js');
  await m.MeshoptDecoder.ready;
  return m.MeshoptDecoder;
}

function viewBytes(ctx, i) {
  if (ctx.views.has(i)) return ctx.views.get(i);
  const bv = ctx.json.bufferViews[i];
  const mo = bv.extensions?.EXT_meshopt_compression;
  let out;
  if (mo) {
    const src = ctx.bin.subarray(mo.byteOffset || 0, (mo.byteOffset || 0) + mo.byteLength);
    out = new Uint8Array(mo.count * mo.byteStride);
    ctx.meshopt.decodeGltfBuffer(out, mo.count, mo.byteStride, src, mo.mode, mo.filter || 'NONE');
  } else {
    out = ctx.bin.subarray(bv.byteOffset || 0, (bv.byteOffset || 0) + bv.byteLength);
  }
  ctx.views.set(i, out);
  return out;
}

const COMPONENTS = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 };
const KIND = {
  5120: [1, 'getInt8', 127], 5121: [1, 'getUint8', 255], 5122: [2, 'getInt16', 32767],
  5123: [2, 'getUint16', 65535], 5125: [4, 'getUint32', 0], 5126: [4, 'getFloat32', 0],
};

export function readAccessor(ctx, i) {
  const a = ctx.json.accessors[i];
  const n = COMPONENTS[a.type], [size, get, norm] = KIND[a.componentType];
  const bytes = viewBytes(ctx, a.bufferView);
  const stride = ctx.json.bufferViews[a.bufferView].byteStride
    || ctx.json.bufferViews[a.bufferView].extensions?.EXT_meshopt_compression?.byteStride || size * n;
  const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const out = a.componentType === 5125 || (!a.normalized && a.componentType !== 5126)
    ? new Uint32Array(a.count * n) : new Float64Array(a.count * n);
  for (let e = 0; e < a.count; e++) {
    for (let c = 0; c < n; c++) {
      let v = dv[get]((a.byteOffset || 0) + e * stride + c * size, true);
      if (a.normalized && norm) v = Math.max(v / norm, -1);
      out[e * n + c] = v;
    }
  }
  return out;
}

function nodeTransform(node) {
  if (node.matrix) return (p) => {
    const m = node.matrix;
    return [m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
      m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13],
      m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14]];
  };
  const [tx, ty, tz] = node.translation || [0, 0, 0];
  const [sx, sy, sz] = node.scale || [1, 1, 1];
  const [x, y, z, w] = node.rotation || [0, 0, 0, 1];
  return (p) => {
    const vx = p[0] * sx, vy = p[1] * sy, vz = p[2] * sz;
    // q * v * q^-1
    const ix = w * vx + y * vz - z * vy, iy = w * vy + z * vx - x * vz;
    const iz = w * vz + x * vy - y * vx, iw = -x * vx - y * vy - z * vz;
    return [ix * w + iw * -x + iy * -z - iz * -y + tx,
      iy * w + iw * -y + iz * -x - ix * -z + ty,
      iz * w + iw * -z + ix * -y - iy * -x + tz];
  };
}

function imageSize(bytes) {
  if (bytes[0] === 0x89 && bytes[1] === 0x50) {
    const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    return [dv.getUint32(16), dv.getUint32(20)];
  }
  for (let i = 2; i < bytes.length - 9;) {
    if (bytes[i] !== 0xff) { i++; continue; }
    const marker = bytes[i + 1], len = (bytes[i + 2] << 8) | bytes[i + 3];
    if (marker >= 0xc0 && marker <= 0xc3) {
      return [(bytes[i + 7] << 8) | bytes[i + 8], (bytes[i + 5] << 8) | bytes[i + 6]];
    }
    i += 2 + len;
  }
  return [0, 0];
}

// ---------------------------------------------------------------------------
// the measures
// ---------------------------------------------------------------------------

const box = () => ({ min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] });
const grow = (b, p) => { for (let k = 0; k < 3; k++) { b.min[k] = Math.min(b.min[k], p[k]); b.max[k] = Math.max(b.max[k], p[k]); } };
const r4 = (v) => Math.round(v * 1e4) / 1e4;
const roundBox = (b) => ({ min: b.min.map(r4), max: b.max.map(r4) });

/** Measure one GLB by the contract's rules. `envelope` names the wall materials. */
export async function measureGlb(buf, { envelope, walls: wallRule, band, quantum_m, library = [], meshopt = null }) {
  const { json, bin } = parseGlb(buf);
  const needsMeshopt = (json.extensionsUsed || []).includes('EXT_meshopt_compression');
  const ctx = { json, bin, views: new Map(), meshopt: needsMeshopt ? (meshopt || await decoder()) : null };
  const env = new RegExp(envelope), base = new RegExp(wallRule);
  const all = box(), walls = box();
  let wallBase = Infinity;
  const sunk = new Map();
  const faces = new Map();
  let triangles = 0, vertices = 0, degenerate = 0, primitives = 0, positionStep = 0;
  const uv = new Map();
  const q = (v) => Math.round(v / quantum_m);
  const nodes = json.nodes.filter((n) => n.mesh !== undefined);
  for (const node of nodes) {
    const xf = nodeTransform(node);
    for (const [pi, prim] of json.meshes[node.mesh].primitives.entries()) {
      primitives++;
      const material = json.materials?.[prim.material];
      const mat = material?.name ?? '(none)';
      const raw = readAccessor(ctx, prim.attributes.POSITION);
      const count = raw.length / 3;
      // The encoding's own position step in metres: one integer of a quantized
      // accessor under the node's scale (0 for float positions). T-2267.
      const pa = json.accessors[prim.attributes.POSITION];
      const scale = Math.max(...(node.scale || [1, 1, 1]).map(Math.abs));
      const step = pa.componentType === 5126 ? 0 : scale / (pa.normalized ? KIND[pa.componentType][2] : 1);
      positionStep = Math.max(positionStep, step);
      vertices += count;
      const pos = new Float64Array(raw.length), keys = new Array(count);
      for (let v = 0; v < count; v++) {
        const p = xf([raw[v * 3], raw[v * 3 + 1], raw[v * 3 + 2]]);
        pos.set(p, v * 3);
        grow(all, p);
        // the storey band: above stoops, paving and terraces, below cornices and eaves
        if (env.test(mat) && p[1] >= band[0] && p[1] <= band[1]) grow(walls, p);
        if (base.test(mat)) wallBase = Math.min(wallBase, p[1]);
        if (p[1] < 0) sunk.set(mat, Math.min(sunk.get(mat) ?? 0, p[1]));
        keys[v] = `${q(p[0])},${q(p[1])},${q(p[2])}`;
      }
      const tc = prim.attributes.TEXCOORD_0 !== undefined ? readAccessor(ctx, prim.attributes.TEXCOORD_0) : null;
      const idx = prim.indices !== undefined ? readAccessor(ctx, prim.indices)
        : Uint32Array.from({ length: count }, (_, i) => i);
      const densities = [];
      for (let t = 0; t + 2 < idx.length; t += 3) {
        triangles++;
        const a = idx[t], b = idx[t + 1], c = idx[t + 2];
        const ka = keys[a], kb = keys[b], kc = keys[c];
        if (ka === kb || kb === kc || ka === kc) { degenerate++; continue; }
        // A face is the same face whatever vertex it starts on; its winding is the
        // parity of the rotation/reflection that sorts it.
        const s = [ka, kb, kc].sort();
        const even = (s[0] === ka && s[1] === kb) || (s[0] === kb && s[1] === kc) || (s[0] === kc && s[1] === ka);
        const key = s.join('|');
        let f = faces.get(key);
        if (!f) faces.set(key, f = { plus: 0, minus: 0, prims: new Set(), edge: 0 });
        if (even) f.plus++; else f.minus++;
        f.prims.add(pi);
        const d = (u, w) => Math.hypot(pos[u * 3] - pos[w * 3], pos[u * 3 + 1] - pos[w * 3 + 1], pos[u * 3 + 2] - pos[w * 3 + 2]);
        f.edge = Math.max(f.edge, Math.min(d(a, b), d(b, c), d(c, a)));
        if (tc) {
          const ex = [pos[b * 3] - pos[a * 3], pos[b * 3 + 1] - pos[a * 3 + 1], pos[b * 3 + 2] - pos[a * 3 + 2]];
          const ey = [pos[c * 3] - pos[a * 3], pos[c * 3 + 1] - pos[a * 3 + 1], pos[c * 3 + 2] - pos[a * 3 + 2]];
          const cx = ex[1] * ey[2] - ex[2] * ey[1], cy = ex[2] * ey[0] - ex[0] * ey[2], cz = ex[0] * ey[1] - ex[1] * ey[0];
          const area = Math.hypot(cx, cy, cz) / 2;
          const uvArea = Math.abs((tc[b * 2] - tc[a * 2]) * (tc[c * 2 + 1] - tc[a * 2 + 1])
            - (tc[c * 2] - tc[a * 2]) * (tc[b * 2 + 1] - tc[a * 2 + 1])) / 2;
          if (area > 1e-4 && uvArea > 0) densities.push(Math.sqrt(uvArea / area));
        }
      }
      if (densities.length) {
        densities.sort((x, y) => x - y);
        const row = uv.get(mat) || { triangles: 0, medians: [] };
        row.triangles += densities.length;
        row.medians.push([densities[densities.length >> 1], densities.length]);
        uv.set(mat, row);
      }
    }
  }
  let sameWinding = 0, opposite = 0, crossPrimitive = 0, coincident = 0, sliver = 0;
  for (const f of faces.values()) {
    const n = f.plus + f.minus;
    if (n < 2) continue;
    coincident += n - 1;
    // how large a face the coincidence is: the group's longest shortest-edge
    sliver = Math.max(sliver, f.edge);
    sameWinding += Math.max(f.plus - 1, 0) + Math.max(f.minus - 1, 0);
    opposite += Math.min(f.plus, f.minus);
    if (f.prims.size > 1) crossPrimitive++;
  }
  // texture cost: what the file carries, and what the GPU holds once decoded (RGBA8 + mips)
  const images = (json.images || []).map((im) => {
    const bytes = viewBytes(ctx, im.bufferView);
    const [w, h] = imageSize(bytes);
    return { name: im.name, mime: im.mimeType, bytes: bytes.length, px: [w, h] };
  });
  const texture = {
    images: images.length,
    textures: (json.textures || []).length,
    encoded_bytes: images.reduce((s, i) => s + i.bytes, 0),
    pixels: images.reduce((s, i) => s + i.px[0] * i.px[1], 0),
    gpu_rgba8_mip_bytes: Math.round(images.reduce((s, i) => s + i.px[0] * i.px[1] * 4, 0) * 4 / 3),
    largest_px: images.reduce((m, i) => Math.max(m, i.px[0], i.px[1]), 0),
  };
  // metric UVs: TEXCOORD_0 is surface metres / the fabric's tile_m
  const uvRows = {};
  for (const [mat, row] of [...uv.entries()].sort()) {
    row.medians.sort((x, y) => x[0] - y[0]);
    let acc = 0, median = row.medians[0][0];
    for (const [m, n] of row.medians) { acc += n; if (acc >= row.triangles / 2) { median = m; break; } }
    // the fabric is the library entry the material's base-colour image is named for
    const info = (json.materials || []).find((m) => m.name === mat)?.pbrMetallicRoughness?.baseColorTexture;
    const image = info ? json.images?.[json.textures[info.index].source]?.name ?? '' : '';
    const fabric = library.filter((l) => image.startsWith(l.name)).sort((x, y) => y.name.length - x.name.length)[0];
    // TEXCOORD_0 = (metres along, metres up) / (tile u, tile v), so its area density is
    // 1 / sqrt(tile u * tile v) per metre
    const tile = fabric ? Math.sqrt(fabric.tile_m[0] * fabric.tile_m[1]) : null;
    const xform = info?.extensions?.KHR_texture_transform?.scale;
    uvRows[mat] = {
      median_uv_per_m: r4(median),
      ...(fabric ? { fabric: fabric.name, tile_m: fabric.tile_m, uv_per_m_times_tile_m: r4(median * tile) } : {}),
      ...(xform ? { texture_transform_scale: xform.map(r4) } : {}),
    };
  }
  return {
    generator: json.asset?.generator,
    extensions_required: json.extensionsRequired || [],
    nodes: nodes.map((n) => ({ name: n.name, transform: ['translation', 'rotation', 'scale', 'matrix'].filter((k) => k in n) })),
    mesh: { draw_primitives: primitives, materials: (json.materials || []).length, triangles, vertices },
    texture,
    bbox_m: roundBox(all),
    envelope_bbox_m: roundBox(walls),
    wall_base_y_m: r4(wallBase),
    below_grade_m: Object.fromEntries([...sunk.entries()].sort().map(([k, v]) => [k, r4(v)])),
    faces: { quantum_m, degenerate, coincident, same_winding: sameWinding, back_to_back: opposite, shared_across_primitives: crossPrimitive,
      position_step_m: Number(positionStep.toPrecision(4)), coincident_shortest_edge_max_m: r4(sliver) },
    metric_uv: uvRows,
  };
}

/**
 * The coincident-face verdict (T-2267). The full master must have none. A derived tier
 * may keep a remainder only when quantization alone explains it: its positions are
 * quantized, and it carries the master's triangles one for one, so re-encoding the
 * positions is the only thing that happened to them. The master has no coincident
 * face on the 1 mm grid, so any such tier's remainder is vertices rounded together on
 * the encoding's lattice. A tier built otherwise (light is its own reduced build) must
 * have none.
 */
export function coincidentVerdict(tiers) {
  const full = tiers.full;
  const why = {};
  const ok = full.faces.coincident === 0 && Object.entries(tiers).every(([t, r]) => {
    if (t === 'full' || r.faces.coincident === 0) return true;
    const explained = r.faces.position_step_m > 0 && r.mesh.triangles === full.mesh.triangles;
    if (explained) why[t] = `${r.faces.coincident} on the ${r.faces.position_step_m} m position lattice, none larger than a `
      + `${r.faces.coincident_shortest_edge_max_m} m shortest edge; the master has none and this tier carries its triangles one for one`;
    return explained;
  });
  return { ok, counts: Object.fromEntries(Object.entries(tiers).map(([t, r]) => [t, r.faces.coincident])),
    ...(Object.keys(why).length ? { quantization: why } : {}) };
}

/** The origin and scale verdicts, from measured boxes and the record's footprint. */
export function originVerdict(envelopeBox, wallBase, footprint, rules) {
  const xs = footprint.map((p) => p[0]), ys = footprint.map((p) => p[1]);
  // polygon u -> +X, v -> -Z (docs/GLB-CONTRACT.md § pinned conventions)
  const plan = { x: [Math.min(...xs), Math.max(...xs)], z: [-Math.max(...ys), -Math.min(...ys)] };
  const over = {
    west: r4(plan.x[0] - envelopeBox.min[0]), east: r4(envelopeBox.max[0] - plan.x[1]),
    north: r4(plan.z[0] - envelopeBox.min[2]), south: r4(envelopeBox.max[2] - plan.z[1]),
  };
  const base = r4(wallBase);
  const sides = Object.values(over);
  return {
    footprint_plan_m: { x: plan.x.map(r4), z: plan.z.map(r4) },
    overhang_m: over,
    base_y_m: base,
    ok: Math.abs(base) <= rules.base_tolerance_m
      && sides.every((s) => s >= -rules.inset_tolerance_m && s <= rules.max_overhang_m),
  };
}

export function driftVerdict(reference, other, rules, referenceWalls = null, otherWalls = null) {
  // SCALE drift is a ratio: each axis of the tier's whole extent over the master's. The
  // wall band's faces are reported beside it as relief: a reduced tier may pull a
  // rock-faced wall face in without its opposite face moving, which is not scale.
  const ratio = [0, 1, 2].map((k) => (other.max[k] - other.min[k]) / (reference.max[k] - reference.min[k]) - 1);
  const shift = referenceWalls && otherWalls
    ? [0, 2].flatMap((k) => [otherWalls.min[k] - referenceWalls.min[k], otherWalls.max[k] - referenceWalls.max[k]]) : [];
  return {
    scale_ratio_minus_1: ratio.map((r) => Math.round(r * 1e6) / 1e6),
    ...(shift.length ? { wall_face_shift_m: shift.map(r4) } : {}),
    ok: Math.max(...ratio.map(Math.abs)) <= rules.tier_scale_ratio,
  };
}

// ---------------------------------------------------------------------------
// the contract's own form
// ---------------------------------------------------------------------------

export function contractProblems(c) {
  const bad = [];
  const need = (cond, msg) => { if (!cond) bad.push(msg); };
  need(c.frame?.units === 'metres', 'frame.units must be metres');
  need(c.frame?.vertical_origin_datum === 'grade', 'the vertical origin must be the datum `grade`');
  const datumIds = new Set((c.datums || []).map((d) => d.id));
  need(datumIds.has('grade'), 'datums must declare `grade`');
  for (const d of c.datums || []) {
    need(/^[a-z][a-z0-9_]*$/.test(d.id || ''), `datum id '${d.id}' is not snake_case`);
    if (d.range_m) need(d.range_m[0] < d.range_m[1], `datum ${d.id}: range_m runs backwards`);
  }
  for (const [lo, hi] of c.datum_order || []) {
    need(datumIds.has(lo) && datumIds.has(hi), `datum_order names an undeclared datum: ${lo} <= ${hi}`);
  }
  const conf = new Set(c.provenance?.confidence || []);
  need(['attested', 'inferred', 'reconstructed'].every((k) => conf.has(k)) && conf.size === 3,
    'provenance.confidence is the validator\'s vocabulary: attested, inferred, reconstructed');
  const idRule = new RegExp(c.component_id?.pattern || '^$');
  const seen = new Set();
  for (const f of c.families || []) {
    need(/^[a-z_]+$/.test(f.family || ''), `family '${f.family}' is not a plain name`);
    need(f.sockets?.length > 0, `family ${f.family}: no sockets`);
    need(f.material_slots?.length > 0, `family ${f.family}: no material slots`);
    for (const s of f.sockets || []) need(!s.datum || datumIds.has(s.datum), `family ${f.family}: socket ${s.id} sits on an undeclared datum '${s.datum}'`);
    for (const [name, p] of Object.entries(f.parameters || {})) {
      need(p.unit, `${f.family}.${name}: no unit`);
      if (p.range) need(p.range[0] < p.range[1], `${f.family}.${name}: range runs backwards`);
      if (p.range || p.ranges) {
        need(p.confidence === 'reconstructed', `${f.family}.${name}: a starting range is a prior, so its confidence is reconstructed, not '${p.confidence}'`);
        need(typeof p.rule_source === 'string' && p.rule_source.length > 0, `${f.family}.${name}: a range must cite the rule it comes from`);
      }
      for (const r of Object.values(p.ranges || {})) need(r[0] < r[1], `${f.family}.${name}: a range runs backwards`);
      if (p.datum) need(datumIds.has(p.datum), `${f.family}.${name}: undeclared datum '${p.datum}'`);
    }
    for (const id of f.example_ids || []) {
      need(idRule.test(id), `${f.family}: example id '${id}' breaks the component id pattern`);
      need(id.split('.')[1] === f.family, `${f.family}: example id '${id}' names another family`);
      need(!seen.has(id), `component id '${id}' is declared twice`);
      seen.add(id);
    }
  }
  need(c.handedness?.variants?.join(',') === 'l,r', 'handedness.variants must be [l, r]');
  need(/sha256/.test(c.seed?.rule || ''), 'seed.rule must derive the seed from a hash, never a clock or a counter');
  const m = c.measures || {};
  for (const k of ['quantum_m', 'base_tolerance_m', 'inset_tolerance_m', 'max_overhang_m', 'tier_scale_ratio', 'uv_tolerance']) {
    need(typeof m[k] === 'number' && m[k] > 0, `measures.${k} must be a positive number`);
  }
  need(m.coincident_faces_allowed_new === 0, 'a component built to the contract may emit no coincident face');
  need(Array.isArray(m.storey_band_m) && m.storey_band_m[0] < m.storey_band_m[1], 'measures.storey_band_m must be [low, high] metres above grade');
  for (const k of ['envelope_materials', 'wall_base_materials']) {
    try { new RegExp(m[k]); } catch { bad.push(`measures.${k} is not a pattern`); }
  }
  return bad;
}

export function baselineProblems(c, b, pkg) {
  const bad = [];
  const need = (cond, msg) => { if (!cond) bad.push(msg); };
  for (const [tier, file] of TIERS) {
    const row = b.tiers?.[tier];
    need(row, `baseline has no '${tier}' tier`);
    if (!row) continue;
    const want = pkg.files?.[file];
    need(want && row.sha256 === want.sha256 && row.bytes === want.bytes,
      `${tier}: the baseline measured ${row.sha256?.slice(0, 12)} but the package holds ${want?.sha256?.slice(0, 12)} — `
      + 'the asset was rebaked; re-measure with `node tools/k01_contract.mjs --measure`');
    for (const k of ['mesh', 'texture', 'bbox_m', 'envelope_bbox_m', 'faces', 'metric_uv', 'origin']) need(row[k], `${tier}: no '${k}' measure`);
    if (row.faces) need(row.faces.quantum_m === c.measures.quantum_m, `${tier}: faces were measured at another quantum`);
  }
  need(b.verdicts && ['scale_drift', 'origin', 'coincident_faces', 'metric_uv'].every((k) => k in b.verdicts),
    'baseline must state a verdict for scale_drift, origin, coincident_faces and metric_uv');
  for (const [k, v] of Object.entries(b.verdicts || {})) {
    need(v.ok === true || (typeof v.finding === 'string' && /T-\d{4}/.test(v.finding)),
      `verdict ${k} is not ok and names no ticket that owns it`);
  }
  return bad;
}

// ---------------------------------------------------------------------------
// modes
// ---------------------------------------------------------------------------

async function measure() {
  const c = readJson(CONTRACT);
  const record = readJson(RECORD);
  const footprint = record.phases.find((p) => p.id === 'as_built_1887').footprint.polygon;
  const library = readJson(LIBRARY).materials;
  const m = c.measures;
  const tiers = {};
  for (const [tier, file] of TIERS) {
    const abs = path.join(APP, file);
    if (!existsSync(abs)) throw new Error(`${file} is missing — run python3 tools/recover_glessner_v4.py --materialize`);
    const buf = readFileSync(abs);
    const sha256 = createHash('sha256').update(buf).digest('hex');
    const row = await measureGlb(new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength),
      { envelope: m.envelope_materials, walls: m.wall_base_materials, band: m.storey_band_m, quantum_m: m.quantum_m, library });
    row.origin = originVerdict(row.envelope_bbox_m, row.wall_base_y_m, footprint, m);
    tiers[tier] = { path: file, bytes: buf.length, sha256, ...row };
    console.log(`${tier}: ${row.mesh.triangles} triangles, ${row.mesh.draw_primitives} primitives, ${row.faces.coincident} coincident faces`);
  }
  const drift = Object.fromEntries(['web', 'light'].map((t) => [t,
    driftVerdict(tiers.full.bbox_m, tiers[t].bbox_m, m, tiers.full.envelope_bbox_m, tiers[t].envelope_bbox_m)]));
  const uvOff = [];
  for (const [tier, row] of Object.entries(tiers)) {
    for (const [mat, u] of Object.entries(row.metric_uv)) {
      if (u.uv_per_m_times_tile_m !== undefined && Math.abs(u.uv_per_m_times_tile_m - 1) > m.uv_tolerance) uvOff.push(`${tier}:${mat}=${u.uv_per_m_times_tile_m}`);
    }
  }
  const prior = existsSync(path.join(APP, BASELINE)) ? readJson(BASELINE) : {};
  const keep = (k) => prior.verdicts?.[k]?.finding;
  const verdict = (ok, extra, k) => ({ ok, ...extra, ...(ok || !keep(k) ? {} : { finding: keep(k) }) });
  const out = {
    _doc: 'MEASURED, not authored: node tools/k01_contract.mjs --measure wrote this from the three canonical Glessner v4 GLBs by the rules in k01_contract.json (T-2265). The gate holds its hashes to docs/RESEARCH/glessner-v4-recovery/manifest.json, so a rebake that is not re-measured fails. A verdict that is not ok must name the ticket that owns it in `finding`; --measure carries an existing finding forward and never writes one.',
    contract: CONTRACT,
    structure_id: record.id,
    phase_id: 'as_built_1887',
    tiers,
    verdicts: {
      scale_drift: verdict(Object.values(drift).every((d) => d.ok), { against: 'full', tiers: drift }, 'scale_drift'),
      origin: verdict(Object.values(tiers).every((r) => r.origin.ok), {}, 'origin'),
      coincident_faces: (({ ok, ...extra }) => verdict(ok, extra, 'coincident_faces'))(coincidentVerdict(tiers)),
      metric_uv: verdict(uvOff.length === 0, { off: uvOff }, 'metric_uv'),
    },
  };
  writeFileSync(path.join(APP, BASELINE), JSON.stringify(out, null, 2) + '\n');
  console.log(`wrote ${BASELINE}`);
  for (const [k, v] of Object.entries(out.verdicts)) console.log(`  ${k}: ${v.ok ? 'ok' : 'NOT OK'}`);
}

// ---------------------------------------------------------------------------
// assemblies built TO the contract (T-2266)
// ---------------------------------------------------------------------------

const COMPONENTS_DIR = 'data/components/prairie_1904';
const sha256Of = (abs) => createHash('sha256').update(readFileSync(abs)).digest('hex');

function assetTiers(structureId) {
  const manifest = readJson('assets/manifest.json').assets;
  const name = Object.keys(manifest).find((n) => manifest[n].structure_id === structureId);
  if (!name) throw new Error(`${structureId}: no baked asset in assets/manifest.json`);
  return { name, phase: manifest[name].phase_id, tiers: [['full', `assets/gltf/${name}`], ['web', `assets/web/${name}`]] };
}

async function measureAsset(structureId) {
  if (!structureId) throw new Error('usage: --measure-asset <structure_id>');
  const c = readJson(CONTRACT);
  const m = c.measures;
  const record = readJson(`data/structures/${structureId}.json`);
  const { phase, tiers: files } = assetTiers(structureId);
  const footprint = record.phases.find((p) => p.id === phase).footprint.polygon;
  const library = fabricLibrary();
  const tiers = {};
  for (const [tier, file] of files) {
    const buf = readFileSync(path.join(APP, file));
    const row = await measureGlb(new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength),
      { envelope: m.envelope_materials, walls: m.wall_base_materials, band: m.storey_band_m, quantum_m: m.quantum_m, library });
    row.origin = originVerdict(row.envelope_bbox_m, row.wall_base_y_m, footprint, m);
    tiers[tier] = { path: file, bytes: buf.length, sha256: sha256Of(path.join(APP, file)), ...row };
    console.log(`${tier}: ${row.mesh.triangles} triangles, ${row.mesh.draw_primitives} primitives, ${row.faces.coincident} coincident faces`);
  }
  const drift = { web: driftVerdict(tiers.full.bbox_m, tiers.web.bbox_m, m, tiers.full.envelope_bbox_m, tiers.web.envelope_bbox_m) };
  const uvOff = [];
  for (const [tier, row] of Object.entries(tiers)) {
    for (const [mat, u] of Object.entries(row.metric_uv)) {
      if (u.uv_per_m_times_tile_m !== undefined && Math.abs(u.uv_per_m_times_tile_m - 1) > m.uv_tolerance) uvOff.push(`${tier}:${mat}=${u.uv_per_m_times_tile_m}`);
    }
  }
  const coincident = Object.fromEntries(Object.entries(tiers).map(([t, r]) => [t, r.faces.coincident + r.faces.degenerate]));
  const out = {
    _doc: `MEASURED, not authored: node tools/k01_contract.mjs --measure-asset ${structureId} wrote this from the committed full and web GLBs by the rules in k01_contract.json (T-2266). An assembly BUILT to K01 has no light tier yet (tools/web_derivatives.sh reduces Glessner alone), and none of its verdicts may carry a finding: the gate holds every one to ok and the hashes to the files on disk, so a rebuild that is not re-measured fails.`,
    contract: CONTRACT,
    structure_id: structureId,
    phase_id: phase,
    tiers,
    verdicts: {
      scale_drift: { ok: drift.web.ok, against: 'full', tiers: drift },
      origin: { ok: Object.values(tiers).every((r) => r.origin.ok) },
      coincident_faces: { ok: Object.values(coincident).every((n) => n <= m.coincident_faces_allowed_new), counts: coincident, allowed: m.coincident_faces_allowed_new },
      metric_uv: { ok: uvOff.length === 0, off: uvOff },
    },
  };
  const file = `${COMPONENTS_DIR}/${structureId}.measure.json`;
  writeFileSync(path.join(APP, file), JSON.stringify(out, null, 2) + '\n');
  console.log(`wrote ${file}`);
  for (const [k, v] of Object.entries(out.verdicts)) console.log(`  ${k}: ${v.ok ? 'ok' : 'NOT OK'}`);
  if (!Object.values(out.verdicts).every((v) => v.ok)) process.exitCode = 1;
}

/** Every committed assembly measure: all verdicts ok, every tier's hash the file's. */
export function assemblyProblems(measure, hashOf) {
  const bad = [];
  const id = measure.structure_id ?? '(no structure_id)';
  for (const k of ['scale_drift', 'origin', 'coincident_faces', 'metric_uv']) {
    if (measure.verdicts?.[k]?.ok !== true) bad.push(`${id}: verdict ${k} is not ok — an assembly built to K01 may not carry a finding`);
  }
  for (const [tier, row] of Object.entries(measure.tiers || {})) {
    const have = hashOf(row.path);
    if (have !== row.sha256) bad.push(`${id} ${tier}: measured ${row.sha256?.slice(0, 12)} but ${row.path} is ${have ? have.slice(0, 12) : 'missing'} — re-measure with --measure-asset ${id}`);
  }
  if (!measure.tiers?.full || !measure.tiers?.web) bad.push(`${id}: needs a full and a web tier`);
  return bad;
}

function assemblyMeasures() {
  return readdirSync(path.join(APP, COMPONENTS_DIR)).filter((f) => f.endsWith('.measure.json')).sort()
    .map((f) => readJson(`${COMPONENTS_DIR}/${f}`));
}

function check() {
  const c = readJson(CONTRACT);
  const measures = assemblyMeasures();
  const hashOf = (p) => (existsSync(path.join(APP, p)) ? sha256Of(path.join(APP, p)) : null);
  const bad = [...contractProblems(c), ...baselineProblems(c, readJson(BASELINE), readJson(PACKAGE)),
    ...measures.flatMap((mm) => assemblyProblems(mm, hashOf))];
  if (bad.length) {
    for (const b of bad) console.error(`  ✗ ${b}`);
    console.error(`k01_contract: ${bad.length} problem(s)`);
    process.exit(1);
  }
  const b = readJson(BASELINE);
  const t = b.tiers;
  console.log(`k01_contract: contract holds ${c.families.length} families on ${c.datums.length} datums; `
    + `Glessner baseline ${t.full.mesh.triangles}/${t.web.mesh.triangles}/${t.light.mesh.triangles} triangles full/web/light, `
    + `hashes match the package`
    + (measures.length ? `; ${measures.length} assembly built to it (${measures.map((mm) => `${mm.structure_id} ${mm.tiers.full.mesh.triangles} triangles, ${mm.verdicts.coincident_faces.counts.full} coincident`).join('; ')}), every verdict ok` : ''));
}

/** A GLB from plain triangles: one node, one primitive per entry. */
function syntheticGlb(prims, node = {}, step = 0) {
  const parts = [], views = [], accessors = [], primitives = [];
  let off = 0;
  const push = (arr, target) => {
    const bytes = Buffer.from(arr.buffer);
    views.push({ buffer: 0, byteOffset: off, byteLength: bytes.length, target });
    parts.push(bytes, Buffer.alloc((4 - (bytes.length % 4)) % 4));
    off += bytes.length + ((4 - (bytes.length % 4)) % 4);
    return views.length - 1;
  };
  for (const tris of prims) {
    // `step` writes integer positions under a node scale, as a quantizing encoder does
    const pos = step ? new Int16Array(tris.flat(2).map((v) => Math.round(v / step))) : new Float32Array(tris.flat(2));
    const n = pos.length / 3;
    const min = [0, 1, 2].map((k) => Math.min(...[...Array(n).keys()].map((i) => pos[i * 3 + k])));
    const max = [0, 1, 2].map((k) => Math.max(...[...Array(n).keys()].map((i) => pos[i * 3 + k])));
    accessors.push({ bufferView: push(pos, 34962), componentType: step ? 5122 : 5126, count: n, type: 'VEC3', min, max });
    const ix = new Uint32Array([...Array(n).keys()]);
    accessors.push({ bufferView: push(ix, 34963), componentType: 5125, count: n, type: 'SCALAR' });
    primitives.push({ attributes: { POSITION: accessors.length - 2 }, indices: accessors.length - 1, material: 0 });
  }
  const bin = Buffer.concat(parts);
  const json = {
    asset: { version: '2.0' }, scene: 0, scenes: [{ nodes: [0] }],
    nodes: [{ name: 'synthetic', mesh: 0, ...(step ? { scale: [step, step, step] } : {}), ...node }], meshes: [{ primitives }],
    materials: [{ name: 'granite' }], accessors, bufferViews: views, buffers: [{ byteLength: bin.length }],
  };
  let js = Buffer.from(JSON.stringify(json));
  js = Buffer.concat([js, Buffer.alloc((4 - (js.length % 4)) % 4, 0x20)]);
  const head = Buffer.alloc(12);
  head.writeUInt32LE(0x46546c67, 0); head.writeUInt32LE(2, 4); head.writeUInt32LE(12 + 8 + js.length + 8 + bin.length, 8);
  const chunk = (len, type) => { const h = Buffer.alloc(8); h.writeUInt32LE(len, 0); h.writeUInt32LE(type, 4); return h; };
  const glb = Buffer.concat([head, chunk(js.length, 0x4e4f534a), js, chunk(bin.length, 0x004e4942), bin]);
  return new Uint8Array(glb.buffer, glb.byteOffset, glb.byteLength);
}

async function selfTest() {
  let failed = 0;
  const ok = (cond, msg) => { console.log(`  ${cond ? '✓' : '✗'} ${msg}`); if (!cond) failed++; };
  const opts = { envelope: '^granite', walls: '^granite', band: [-100, 100], quantum_m: 0.001 };
  const A = [[0, 0, 0], [1, 0, 0], [0, 1, 0]];
  const B = [[1, 0, 0], [1, 1, 0], [0, 1, 0]];

  let m = await measureGlb(syntheticGlb([[A, B]]), opts);
  ok(m.faces.coincident === 0 && m.mesh.triangles === 2, 'two distinct triangles: no coincident face');
  m = await measureGlb(syntheticGlb([[A, B, [A[1], A[2], A[0]]]]), opts);
  ok(m.faces.same_winding === 1 && m.faces.back_to_back === 0, 'the same face started on another vertex is a same-winding duplicate');
  m = await measureGlb(syntheticGlb([[A, B], [[A[0], A[2], A[1]]]]), opts);
  ok(m.faces.back_to_back === 1 && m.faces.shared_across_primitives === 1, 'a reversed face in another primitive is back-to-back, across primitives');
  m = await measureGlb(syntheticGlb([[A, [[0, 0, 0], [0.0004, 0, 0], [0, 1, 0]]]]), opts);
  ok(m.faces.degenerate === 1, 'a triangle with two vertices inside one quantum is degenerate, not a face');
  m = await measureGlb(syntheticGlb([[A]], { translation: [2, 0.5, -3], scale: [2, 2, 2] }), opts);
  ok(m.bbox_m.min.join() === '2,0.5,-3' && m.bbox_m.max.join() === '4,2.5,-3', 'the node transform is applied before measuring');

  // A quantized tier: the position step is read from the accessor and node scale, and
  // a sliver folded back on itself reports how small it is.
  const q = 0.0008, P = [0, 0, 0], Q = [q, 0, 0], R = [0, 1, 0];
  m = await measureGlb(syntheticGlb([[[P, Q, R], [P, R, Q]]], {}, q), opts);
  ok(m.faces.coincident === 1 && m.faces.position_step_m === q && m.faces.coincident_shortest_edge_max_m === 0.0008,
    'a quantized tier reports its position step and the size of its coincident sliver');
  m = await measureGlb(syntheticGlb([[A, B]]), opts);
  ok(m.faces.position_step_m === 0, 'float positions have no position step');
  const tier = (coincident, triangles, step = q) => ({ mesh: { triangles }, faces: { coincident, position_step_m: step, coincident_shortest_edge_max_m: q } });
  const v = coincidentVerdict({ full: tier(0, 9, 0), web: tier(1, 9), light: tier(0, 4) });
  ok(v.ok && /lattice/.test(v.quantization.web), 'a master with none and a quantized one-for-one tier: the remainder is quantization, and says so');
  ok(!coincidentVerdict({ full: tier(1, 9, 0), web: tier(0, 9), light: tier(0, 4) }).ok, 'a coincident face in the master is refused');
  ok(!coincidentVerdict({ full: tier(0, 9, 0), web: tier(1, 8), light: tier(0, 4) }).ok,
    'a remainder in a tier that does not carry the master\'s triangles is not explained');
  ok(!coincidentVerdict({ full: tier(0, 9, 0), web: tier(1, 9, 0), light: tier(0, 4) }).ok, 'a remainder in an unquantized tier is not explained');
  ok(!coincidentVerdict({ full: tier(0, 9, 0), web: tier(0, 9), light: tier(1, 4) }).ok, 'the separately built light tier may keep none');

  const square = [[0, 0], [10, 0], [10, 5], [0, 5]];
  const rules = { base_tolerance_m: 0.01, inset_tolerance_m: 0.01, max_overhang_m: 1.0 };
  const walls = (dx, dy) => ({ min: [-0.2 + dx, 0 + dy, -5.2], max: [10.2 + dx, 9 + dy, 0.2] });
  ok(originVerdict(walls(0, 0), 0, square, rules).ok, 'walls about the footprint origin on grade pass');
  ok(!originVerdict(walls(1.5, 0), 0, square, rules).ok, 'a hidden 1.5 m plan offset is caught');
  ok(!originVerdict(walls(0, 0), 0.3, square, rules).ok, 'walls standing 0.3 m off grade are caught');
  const drift = { tier_scale_ratio: 0.0005 };
  ok(driftVerdict(walls(0, 0), walls(0, 0), drift).ok, 'an identical tier does not drift');
  ok(!driftVerdict(walls(0, 0), { min: [-0.2, 0, -5.2], max: [10.3, 9, 0.2] }, drift).ok, 'a tier 1% longer on one axis has drifted');
  const relief = driftVerdict(walls(0, 0), walls(0, 0), drift, walls(0, 0), { min: [-0.18, 0, -5.2], max: [10.2, 9, 0.2] });
  ok(relief.ok && relief.wall_face_shift_m[0] === 0.02, 'one wall face pulled in 2 cm is relief, reported, and not scale drift');
  const half = walls(0, 0);
  ok(!driftVerdict(half, { min: half.min.map((v) => v * 1.002), max: half.max.map((v) => v * 1.002) }, drift).ok, 'a tier uniformly scaled by 0.2% has drifted');
  const inStone = await measureGlb(syntheticGlb([[A]], {}), { ...opts, band: [0.5, 2] });
  ok(inStone.envelope_bbox_m.min[1] === 1 && inStone.envelope_bbox_m.max[1] === 1, 'the storey band leaves out the wall geometry below it');

  const c = readJson(CONTRACT);
  ok(contractProblems(c).length === 0, 'the committed contract is well-formed');
  const broken = JSON.parse(JSON.stringify(c));
  broken.families[0].parameters[Object.keys(broken.families[0].parameters).find((k) => broken.families[0].parameters[k].range || broken.families[0].parameters[k].ranges)].confidence = 'attested';
  ok(contractProblems(broken).some((p) => /prior/.test(p)), 'a starting range promoted to attested is refused');
  const twice = JSON.parse(JSON.stringify(c));
  twice.families[1].example_ids.push(twice.families[1].example_ids[0]);
  ok(contractProblems(twice).some((p) => /declared twice/.test(p)), 'a component id declared twice is refused');
  const pkg = readJson(PACKAGE), b = readJson(BASELINE);
  ok(baselineProblems(c, b, pkg).length === 0, 'the committed baseline answers every measure and matches the package');
  const rebaked = JSON.parse(JSON.stringify(pkg));
  rebaked.files[TIERS[2][1]].sha256 = '0'.repeat(64);
  ok(baselineProblems(c, b, rebaked).some((p) => /re-measure/.test(p)), 'a rebaked package with a stale baseline is refused');
  const silent = JSON.parse(JSON.stringify(b));
  silent.verdicts.origin = { ok: false };
  ok(baselineProblems(c, silent, pkg).some((p) => /names no ticket/.test(p)), 'a failed verdict that names no owning ticket is refused');

  if (failed) { console.error(`k01_contract self-test: ${failed} failed`); process.exit(1); }
  console.log('k01_contract self-test: all passed');
}

if (process.argv[1] && path.resolve(process.argv[1]) === new URL(import.meta.url).pathname) {
  const mode = process.argv[2] || '--check';
  if (mode === '--measure') await measure();
  else if (mode === '--measure-asset') await measureAsset(process.argv[3]);
  else if (mode === '--self-test') await selfTest();
  else if (mode === '--check') check();
  else { console.error('usage: k01_contract.mjs --check | --self-test | --measure | --measure-asset <structure_id>'); process.exit(2); }
}
