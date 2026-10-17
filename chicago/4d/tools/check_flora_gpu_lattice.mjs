#!/usr/bin/env node
/**
 * THE FLORA WALK IN A SHADER IS THE FLORA WALK ON THE CPU — T-2697.
 *
 *   node tools/check_flora_gpu_lattice.mjs                 # the text check (check.sh)
 *   node tools/check_flora_gpu_lattice.mjs --self-test     # …and it can fail
 *   node tools/check_flora_gpu_lattice.mjs --gpu [--write] # the readback, in Chromium
 *   node tools/check_flora_gpu_lattice.mjs --gpu --self-test
 *
 * `renderers/web/js/flora-gpu-lattice.js` is flora.js's lattice walk as GLSL, one
 * slot per instance id: T-2557's GPU near grass stands on it (T-2698 adds the
 * field, T-2699 draws). It is a third text of the walk, after flora.js's `scatter`
 * and `jobs/lattice-kernel.js`, and `check_lattice_kernel.mjs` already holds those
 * two to the bit; this holds the shader to the kernel.
 *
 * THE TEXT CHECK (no browser, so `check.sh` can run it). Every constant the walk is
 * made of — hash3's three seeds and two finaliser multipliers, the slot stream's
 * salt, the global shift's salt, STRAT_SALT and the block shift — is read out of
 * flora.js's own source and must appear in the GLSL as the same `uint`. Changing
 * one in flora.js without the shader is refused here, before any browser sees it.
 *
 * THE READBACK (`--gpu`). Chromium (SwiftShader on the runner) compiles the GLSL
 * into a vertex program with transform feedback, draws one point per instance of
 * each walk's bounding square with the rasteriser off, and reads every slot back:
 * whether the ring keeps it, its position relative to the camera, its deal rank
 * and the cell seed and stream state behind it. Node walks the same camera with
 * `latticeSlots` (cone off — the shader has none, see the module) and compares:
 *
 *   - the slots kept, in order: an instance the ring keeps on one side and not the
 *     other is a RING DISAGREEMENT, and is allowed only within 0.1 mm of the ring's
 *     edge, where float32 and a double may honestly round a distance differently;
 *   - cell seed and stream state: equal to the bit, every kept slot;
 *   - position: within 1 mm of the double's, east and north;
 *   - deal rank `u`: within 2^-20 of the double's (on the circle, so a rank the
 *     two round to either side of 1.0 counts as close).
 *
 * The walks are each layer's own lattice at all 18 of the 1835 scene's anchors
 * (`data/scenes/1835.json`) and 200 random ones — every draw, cells from 0.4 to
 * 11 m, one to nine slots a cell, coordinates out to ±2 km on both signs.
 * `--write` files the reading at docs/measurements/t-2697-flora-gpu-lattice.json.
 * `--gpu --self-test` proves the readback can fail: a shader with the slot
 * stream's salt one bit off, and one with the stratum block shift one bit wide,
 * must each be refused.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { LATTICE_GLSL, latticeUniforms, STRAT_SALT, STRAT_BLOCK_SHIFT }
  from '../renderers/web/js/flora-gpu-lattice.js';
import { latticeSlots } from '../renderers/web/js/jobs/lattice-kernel.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');
const FLORA = path.join(APP, 'renderers/web/js/flora.js');
const OUT = path.join(APP, 'docs/measurements/t-2697-flora-gpu-lattice.json');

const argv = process.argv.slice(2);
const GPU = argv.includes('--gpu');
const SELF_TEST = argv.includes('--self-test');
const WRITE = argv.includes('--write');

const POS_TOL_M = 1e-3;
const U_TOL = 2 ** -20;
const EDGE_TOL_M = 1e-4;

// ---------------------------------------------------------------- the text check

/** The walk's constants as flora.js states them, read from its source. */
function floraConstants(src) {
  const fn = (name) => {
    const m = new RegExp(`^function\\*? ${name}\\([^]*?^}`, 'm').exec(src);
    if (!m) throw new Error(`flora.js: no function ${name}`);
    return m[0];
  };
  const hex = (s) => [...s.matchAll(/0x[0-9a-f]+/gi)].map((m) => Number(m[0]) >>> 0);
  const hash = hex(fn('hash3'));
  const scatter = fn('scatter');
  const stream = /hash3\(cellSeed, k, (0x[0-9a-f]+)\)/i.exec(scatter);
  const shift = /hash3\(salt, STRAT_SALT, (0x[0-9a-f]+)\)/i.exec(scatter);
  const strat = /^const STRAT_SALT = (0x[0-9a-f]+);/m.exec(src);
  const block = /^const STRAT_BLOCK_SHIFT = (\d+);/m.exec(src);
  if (!stream || !shift || !strat || !block) throw new Error('flora.js: a walk constant moved');
  return {
    hashSeeds: hash.slice(0, 3), hashMix: hash.slice(3, 5),
    stream: Number(stream[1]) >>> 0, globalShift: Number(shift[1]) >>> 0,
    stratSalt: Number(strat[1]) >>> 0, blockShift: Number(block[1]),
  };
}

const u32 = (v) => `0x${(v >>> 0).toString(16).padStart(8, '0')}u`;

function textFaults(glsl, k, exported) {
  const faults = [];
  const has = (v, what) => {
    if (!glsl.toLowerCase().includes(u32(v))) faults.push(`${what} ${u32(v)} is not in the shader`);
  };
  if (k.hashSeeds.length !== 3 || k.hashMix.length !== 2) faults.push('flora.js hash3 changed shape');
  k.hashSeeds.forEach((v, i) => has(v, `hash3 seed ${i + 1}`));
  k.hashMix.forEach((v, i) => has(v, `hash3 finaliser ${i + 1}`));
  has(k.stream, "the slot stream's salt");
  has(k.stratSalt, 'STRAT_SALT');
  if (exported.STRAT_SALT >>> 0 !== k.stratSalt) faults.push('the module\'s STRAT_SALT is not flora.js\'s');
  if (exported.STRAT_BLOCK_SHIFT !== k.blockShift) faults.push('the module\'s STRAT_BLOCK_SHIFT is not flora.js\'s');
  // The block shift is written into the GLSL as `>> N` / `<< N` and the span as 4.
  const shifts = [...glsl.matchAll(/[cr] (?:>>|<<) (\d+)|\(b[cr] << (\d+)\)/g)].map((m) => Number(m[1] ?? m[2]));
  if (!shifts.length || shifts.some((s) => s !== k.blockShift)) faults.push(`the shader's block shift is not ${k.blockShift}`);
  if (!new RegExp(`\\* ${1 << k.blockShift} \\+`).test(glsl)) faults.push(`the shader's block span is not ${1 << k.blockShift}`);
  // The global shift's salt lives in latticeUniforms, on the CPU side of the module.
  const mod = fs.readFileSync(path.join(APP, 'renderers/web/js/flora-gpu-lattice.js'), 'utf8');
  if (!new RegExp(`hash3\\(salt, STRAT_SALT, 0x${k.globalShift.toString(16)}\\)`, 'i').test(mod)) {
    faults.push(`the global shift's salt ${u32(k.globalShift)} is not latticeUniforms'`);
  }
  return faults;
}

function textCheck() {
  const k = floraConstants(fs.readFileSync(FLORA, 'utf8'));
  const exported = { STRAT_SALT, STRAT_BLOCK_SHIFT };
  const faults = textFaults(LATTICE_GLSL, k, exported);
  if (!SELF_TEST) {
    if (faults.length) {
      console.error('FAIL — the shader walk has drifted from flora.js:\n  ' + faults.join('\n  '));
      process.exit(1);
    }
    console.log(`PASS — the shader walk carries flora.js's ${5 + 4} walk constants `
      + `(hash3 ${k.hashSeeds.map(u32).join(' ')} · ${k.hashMix.map(u32).join(' ')}; `
      + `stream ${u32(k.stream)}; STRAT_SALT ${u32(k.stratSalt)}; block shift ${k.blockShift})`);
    return;
  }
  if (faults.length) { console.error('FAIL — the unbroken text is already refused:\n  ' + faults.join('\n  ')); process.exit(1); }
  const breaks = [
    ['a hash3 seed one bit off', LATTICE_GLSL.replace('0x27d4eb2du', '0x27d4eb2cu')],
    ["the slot stream's salt one bit off", LATTICE_GLSL.replace('0x68bc21ebu', '0x68bc21eau')],
    ['the block shift one bit wide', LATTICE_GLSL.replace('int bc = c >> 2;', 'int bc = c >> 3;')],
    ['STRAT_SALT changed', LATTICE_GLSL.replace('salt ^ 0x7f4a7c15u', 'salt ^ 0x7f4a7c14u')],
  ];
  for (const [what, glsl] of breaks) {
    if (glsl === LATTICE_GLSL) { console.error(`FAIL — self-test could not break: ${what}`); process.exit(1); }
    if (!textFaults(glsl, k, exported).length) { console.error(`FAIL — not refused: ${what}`); process.exit(1); }
    console.log(`   self-test | refused, as it must be: ${what}`);
  }
  console.log(`PASS — the text check refuses all ${breaks.length} broken shaders`);
}

// ---------------------------------------------------------------- the readback

function rngOf(seed) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}

/** Each layer's own lattice at every 1835 anchor, as check_lattice_kernel.mjs names them. */
function layerWalks() {
  const step = 0.6;
  const scene = JSON.parse(fs.readFileSync(path.join(APP, 'data/scenes/1835.json'), 'utf8'));
  const out = [];
  for (const a of scene.anchors) {
    const [e, n] = [a.local_e, a.local_n];
    out.push(
      { at: a.id, layer: 'near', camE: e, camN: n, cell: 0.74, perCell: 4, radius: 7.6, inner: 0, salt: 0x51ed27, draw: 'strata' },
      { at: a.id, layer: 'mid', camE: e, camN: n, cell: 1.55, perCell: 4, radius: 27 + 4 + step, inner: 4.5 - 3 - step, salt: 0x9e3779, draw: 'strata' },
      { at: a.id, layer: 'forb', camE: e, camN: n, cell: 3.4, perCell: 4, radius: 26 + 3 + step, inner: 0, salt: 0x2545f9, draw: 'lattice' },
      { at: a.id, layer: 'shrub', camE: e, camN: n, cell: 3.4, perCell: 4, radius: 26 + 3 + step, inner: 0, salt: 0x7b5c1d, draw: 'wild' },
      { at: a.id, layer: 'far1', camE: e, camN: n, cell: 3.4, perCell: 1, radius: 62 + step, inner: 16 - step, salt: 0x3a91c7, draw: 'lattice' },
      { at: a.id, layer: 'far2', camE: e, camN: n, cell: 9.5, perCell: 1, radius: 175 + step, inner: 44 - step, salt: (0x3a91c7 ^ 0x85ebca6b) >>> 0, draw: 'lattice' });
  }
  return out;
}

function randomWalks(count) {
  const r = rngOf(0x2697);
  const draws = ['strata', 'lattice', 'wild'];
  const out = [];
  for (let i = 0; i < count; i++) {
    const cell = 0.4 + r() * 11;
    const perCell = [1, 2, 3, 4, 9][Math.floor(r() * 5)];
    const radius = cell * (1 + r() * 14);
    const inner = r() < 0.4 ? 0 : radius * r() * 0.8;
    out.push({ at: `random ${i}`, layer: 'random', camE: (r() - 0.5) * 4000, camN: (r() - 0.5) * 4000,
      cell, perCell, radius, inner, salt: (r() * 4294967296) >>> 0, draw: draws[Math.floor(r() * 3)] });
  }
  return out;
}

/** The page's half: compile once, then one transform-feedback draw per walk. */
function pageRun({ glsl, walks }) {
  const gl = document.createElement('canvas').getContext('webgl2');
  if (!gl) return { error: 'no WebGL2' };
  const vs = `#version 300 es
precision highp float;
precision highp int;
${glsl}
out vec4 vF;
flat out uvec4 vU;
void main() {
  vec2 rel; float u; uint rng; uint seed;
  bool keep = flLatticeSlot(gl_VertexID, rel, u, rng, seed);
  vF = vec4(rel, u, keep ? 1.0 : 0.0);
  vU = uvec4(rng, seed, 0u, 0u);
  gl_Position = vec4(0.0);
  gl_PointSize = 1.0;
}`;
  const fs = `#version 300 es
precision highp float;
out vec4 o;
void main() { o = vec4(0.0); }`;
  const shader = (type, text) => {
    const s = gl.createShader(type);
    gl.shaderSource(s, text);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  };
  const prog = gl.createProgram();
  try {
    gl.attachShader(prog, shader(gl.VERTEX_SHADER, vs));
    gl.attachShader(prog, shader(gl.FRAGMENT_SHADER, fs));
  } catch (err) { return { error: `compile: ${err.message}` }; }
  gl.transformFeedbackVaryings(prog, ['vF', 'vU'], gl.INTERLEAVED_ATTRIBS);
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return { error: `link: ${gl.getProgramInfoLog(prog)}` };
  gl.useProgram(prog);
  const loc = (n) => gl.getUniformLocation(prog, n);
  const vao = gl.createVertexArray();
  gl.bindVertexArray(vao);
  const tf = gl.createTransformFeedback();
  gl.enable(gl.RASTERIZER_DISCARD);
  const info = gl.getExtension('WEBGL_debug_renderer_info');
  const renderer = info ? gl.getParameter(info.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
  const out = [];
  for (const w of walks) {
    gl.uniform4iv(loc('uLatGrid'), w.grid);
    gl.uniform4uiv(loc('uLatDeal'), w.deal);
    gl.uniform1ui(loc('uLatMode'), w.mode);
    gl.uniform4fv(loc('uLatRing'), w.ring);
    gl.uniform2fv(loc('uLatCell'), w.cell);
    const bytes = w.count * 32;
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER, buf);
    gl.bufferData(gl.TRANSFORM_FEEDBACK_BUFFER, bytes, gl.STREAM_READ);
    gl.bindTransformFeedback(gl.TRANSFORM_FEEDBACK, tf);
    gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER, 0, buf);
    gl.beginTransformFeedback(gl.POINTS);
    gl.drawArrays(gl.POINTS, 0, w.count);
    gl.endTransformFeedback();
    gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER, 0, null);
    gl.bindTransformFeedback(gl.TRANSFORM_FEEDBACK, null);
    const data = new ArrayBuffer(bytes);
    gl.bindBuffer(gl.COPY_READ_BUFFER, buf);
    gl.getBufferSubData(gl.COPY_READ_BUFFER, 0, new Uint8Array(data));
    gl.bindBuffer(gl.COPY_READ_BUFFER, null);
    gl.deleteBuffer(buf);
    const f = new Float32Array(data), u = new Uint32Array(data);
    // Send only what Node compares: id, rel e, rel n, u, rng and seed per kept slot.
    const kept = [];
    for (let i = 0; i < w.count; i++) {
      if (f[i * 8 + 3] !== 1) continue;
      kept.push(i, f[i * 8], f[i * 8 + 1], f[i * 8 + 2], u[i * 8 + 4], u[i * 8 + 5]);
    }
    out.push({ kept });
  }
  return { renderer, out };
}

function hash3(a, b, c) {
  let h = Math.imul(a, 0x27d4eb2d) ^ Math.imul(b, 0x165667b1) ^ Math.imul(c, 0x9e3779b1);
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
}

function jitterState(seed, k) {
  let s = hash3(seed, k, 0x68bc21eb) >>> 0 || 1;
  for (let i = 0; i < 2; i++) { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; }
  return s;
}

/**
 * The instance id a kernel slot is, recovered from the slot alone: its cell is the
 * one its position falls in (or a neighbour, where a double rounds onto the line)
 * whose seed is the slot's, and its k is the one whose stream is the slot's. Cell
 * seeds can collide, so a slot is never matched by its seed alone.
 */
function idOf(walk, U, cpu, i) {
  const [c0, r0, cols, perCell] = U.grid;
  const cc = Math.floor(cpu.e[i] / walk.cell), rc = Math.floor(cpu.n[i] / walk.cell);
  for (const dr of [0, -1, 1]) {
    for (const dc of [0, -1, 1]) {
      const c = cc + dc, r = rc + dr;
      if (hash3(c, r, walk.salt) !== cpu.cellSeed[i]) continue;
      for (let k = 0; k < perCell; k++) {
        if (jitterState(cpu.cellSeed[i], k) === cpu.rng[i]) return ((r - r0) * cols + (c - c0)) * perCell + k;
      }
    }
  }
  return -1;
}

/** Node's half: one walk's verdict against the kernel, slot by instance id. */
function compare(walk, gpu) {
  const cpu = latticeSlots({ ...walk, cone: null });
  const U = latticeUniforms(walk);
  const r = { slots: cpu.e.length, gpuKept: gpu.kept.length / 6, ringOnlyGpu: [], ringOnlyCpu: [],
    maxPosM: 0, maxDu: 0, bitFaults: 0, orderFaults: 0, unplaced: 0 };
  const gpuAt = new Map();
  for (let j = 0; j < gpu.kept.length; j += 6) gpuAt.set(gpu.kept[j], j);
  const edge = (d) => Math.min(Math.abs(d - walk.radius), walk.inner > 0 ? Math.abs(d - walk.inner) : Infinity);
  const matched = new Set();
  let last = -1;
  for (let i = 0; i < cpu.e.length; i++) {
    const id = idOf(walk, U, cpu, i);
    if (id < 0) { r.unplaced++; continue; }
    if (id <= last) r.orderFaults++;
    last = id;
    const j = gpuAt.get(id);
    if (j === undefined) { r.ringOnlyCpu.push({ edgeM: edge(cpu.d[i]) }); continue; }
    matched.add(id);
    const [, re, rn, u, rng, seed] = gpu.kept.slice(j, j + 6);
    if (rng !== cpu.rng[i] || seed !== cpu.cellSeed[i]) r.bitFaults++;
    r.maxPosM = Math.max(r.maxPosM, Math.abs(re - (cpu.e[i] - walk.camE)), Math.abs(rn - (cpu.n[i] - walk.camN)));
    const du = Math.abs(u - cpu.u[i]);
    r.maxDu = Math.max(r.maxDu, Math.min(du, 1 - du));
  }
  for (const [id, j] of gpuAt) {
    if (!matched.has(id)) r.ringOnlyGpu.push({ edgeM: edge(Math.hypot(gpu.kept[j + 1], gpu.kept[j + 2])) });
  }
  // A slot kept on one side only that is NOT at the ring's edge is a slot computed
  // wrong, and so is a kernel slot no instance id accounts for.
  r.bitFaults += r.unplaced + [...r.ringOnlyGpu, ...r.ringOnlyCpu].filter((x) => !(x.edgeM <= EDGE_TOL_M)).length;
  return r;
}

async function readback(glsl, walks) {
  let chromium;
  try { ({ chromium } = await import('playwright')); } catch {
    console.error('FAIL — playwright is not installed here; the readback needs a browser');
    process.exit(2);
  }
  const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    const jobs = walks.map((w) => latticeUniforms(w));
    const res = await page.evaluate(pageRun, { glsl, walks: jobs });
    if (errors.length) res.error = `page errors: ${errors.join('; ')}`;
    return res;
  } finally {
    await browser.close();
  }
}

function verdict(walks, res) {
  if (res.error) return { error: res.error };
  const per = walks.map((w, i) => ({ walk: w, ...compare(w, res.out[i]) }));
  const sum = (f) => per.reduce((a, p) => a + f(p), 0);
  const total = {
    walks: per.length, slots: sum((p) => p.slots), instances: walks.reduce((a, w) => a + latticeUniforms(w).count, 0),
    ringDisagreements: sum((p) => p.ringOnlyGpu.length + p.ringOnlyCpu.length),
    worstEdgeM: Math.max(0, ...per.flatMap((p) => [...p.ringOnlyGpu, ...p.ringOnlyCpu].map((x) => x.edgeM))),
    bitFaults: sum((p) => p.bitFaults), orderFaults: sum((p) => p.orderFaults),
    maxPosM: Math.max(...per.map((p) => p.maxPosM)), maxDu: Math.max(...per.map((p) => p.maxDu)),
  };
  const faults = [];
  if (total.bitFaults) faults.push(`${total.bitFaults} slot(s) with a wrong seed or stream, unplaced, or kept on one side only away from the ring's edge`);
  if (total.orderFaults) faults.push(`${total.orderFaults} slot(s) out of scatter's order`);
  if (!(total.maxPosM <= POS_TOL_M)) faults.push(`a position ${(total.maxPosM * 1000).toFixed(3)} mm off (limit ${POS_TOL_M * 1000} mm)`);
  if (!(total.maxDu <= U_TOL)) faults.push(`a deal rank ${total.maxDu.toExponential(2)} off (limit 2^-20)`);
  return { total, per, faults };
}

function layerTable(per) {
  const rows = {};
  for (const p of per) {
    const k = p.walk.layer;
    const row = rows[k] ??= { walks: 0, slots: 0, ringDisagreements: 0, maxPosMm: 0, maxDu: 0 };
    row.walks++;
    row.slots += p.slots;
    row.ringDisagreements += p.ringOnlyGpu.length + p.ringOnlyCpu.length;
    row.maxPosMm = Math.max(row.maxPosMm, p.maxPosM * 1000);
    row.maxDu = Math.max(row.maxDu, p.maxDu);
  }
  return rows;
}

async function gpuCheck() {
  const walks = [...layerWalks(), ...randomWalks(200)];
  if (SELF_TEST) {
    const breaks = [
      ["the slot stream's salt one bit off", LATTICE_GLSL.replace('0x68bc21ebu', '0x68bc21eau')],
      ['the stratum block shift one bit wide', LATTICE_GLSL.replace('int bc = c >> 2;', 'int bc = c >> 3;')],
    ];
    const near = walks.filter((w) => w.layer === 'near').slice(0, 3);
    for (const [what, glsl] of breaks) {
      const v = verdict(near, await readback(glsl, near));
      if (v.error) { console.error(`FAIL — self-test (${what}): ${v.error}`); process.exit(1); }
      if (!v.faults.length) { console.error(`FAIL — the readback did not refuse: ${what}`); process.exit(1); }
      console.log(`   self-test | refused, as it must be: ${what} — ${v.faults[0]}`);
    }
    console.log(`PASS — the readback refuses both broken shaders`);
    return;
  }
  const t0 = Date.now();
  const res = await readback(LATTICE_GLSL, walks);
  const v = verdict(walks, res);
  if (v.error) { console.error(`FAIL — ${v.error}`); process.exit(1); }
  const { total } = v;
  const table = layerTable(v.per);
  console.log(`renderer: ${res.renderer}`);
  for (const [k, r] of Object.entries(table)) {
    console.log(`  ${k.padEnd(7)} ${String(r.walks).padStart(4)} walks ${String(r.slots).padStart(8)} slots`
      + `  ring disagreements ${r.ringDisagreements}  max position ${r.maxPosMm.toFixed(4)} mm  max |du| ${r.maxDu.toExponential(2)}`);
  }
  console.log(`${total.walks} walks, ${total.slots} slots kept of ${total.instances} instances; `
    + `${total.ringDisagreements} ring disagreement(s), the farthest ${(total.worstEdgeM * 1000).toFixed(4)} mm from an edge; `
    + `${total.bitFaults} seed, stream or ring fault(s); position ≤ ${(total.maxPosM * 1000).toFixed(4)} mm; `
    + `|du| ≤ ${total.maxDu.toExponential(2)} (${(Date.now() - t0) / 1000} s)`);
  if (WRITE) {
    const near = v.per.filter((p) => p.walk.layer === 'near');
    fs.writeFileSync(OUT, JSON.stringify({
      ticket: 'T-2697',
      what: "flora-gpu-lattice.js's GLSL walk read back from Chromium against jobs/lattice-kernel.js (itself held bit-equal to flora.js's scatter by check_lattice_kernel.mjs), cone off",
      tool: 'node tools/check_flora_gpu_lattice.mjs --gpu --write',
      renderer: res.renderer,
      limits: { positionMm: POS_TOL_M * 1000, du: U_TOL, ringEdgeMm: EDGE_TOL_M * 1000 },
      total: { ...total, worstEdgeMm: total.worstEdgeM * 1000, maxPosMm: total.maxPosM * 1000, worstEdgeM: undefined, maxPosM: undefined },
      layers: table,
      nearAtAnchors: near.map((p) => ({ anchor: p.walk.at, slots: p.slots,
        instances: latticeUniforms(p.walk).count, ringDisagreements: p.ringOnlyGpu.length + p.ringOnlyCpu.length,
        maxPosMm: +(p.maxPosM * 1000).toFixed(5), maxDu: p.maxDu })),
      verdict: v.faults.length ? 'FAIL' : 'PASS',
      faults: v.faults,
    }, null, 2) + '\n');
    console.log(`wrote ${path.relative(APP, OUT)}`);
  }
  if (v.faults.length) { console.error('FAIL — ' + v.faults.join('; ')); process.exit(1); }
  console.log('PASS');
}

if (GPU) await gpuCheck();
else textCheck();
