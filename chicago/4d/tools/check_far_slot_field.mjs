#!/usr/bin/env node
/**
 * THE FAR FIELD ASKS EACH SLOT AT THE SLOT — T-2967.
 *
 *   node tools/check_far_slot_field.mjs               # the check (check.sh)
 *   node tools/check_far_slot_field.mjs --self-test   # …and it can fail
 *
 * T-2967 deals the near pass's far band on the GPU against a SLOT FIELD
 * (flora-gpu-far.js): per far lattice, one texel per slot, which the pool asks
 * at the slot's own jittered point (jobs/zone-kernel.js `slotPoint`) and the
 * shader finds by the slot's cell index and `k` (`FAR_SLOT_GLSL`). The field's
 * whole claim — its class IS the CPU's answer at the slot — rests on two
 * things this holds with no browser, at every tier's three far bands and the
 * far shrubs' walk (the forb cell, four slots a cell, the `wild` draw, which
 * T-2968 deals against the same machinery), from the 1835 scene's 18 anchors
 * and 200 random cameras out to ±2 km:
 *
 *   1. THE POINT. `slotPoint` of a slot's texel — the texel the shader reads
 *      for it, `(c * sub + k % sub, r * sub + k / sub)`, with `k` read off the
 *      walk's own stream — is the slot `latticeSlots`
 *      walks (jobs/lattice-kernel.js, which check_lattice_kernel.mjs holds to
 *      flora.js's `scatter` bit for bit), east and north, to the bit.
 *   2. THE TILE. Every slot of the walk has a texel of its own (no two slots
 *      share one), and that texel is inside the tile `farSlotSpec` keeps — at
 *      the re-centre origin of the camera itself and of a camera `inHand`
 *      metres past it in each direction (a strip still on the pool) — so the
 *      shader never reads a slot off the tile it was given.
 *
 * The bands are read out of flora.js's own TUNE text, so a band retuned there is
 * checked here as it is. `--self-test` must see the check refuse a `slotPoint`
 * with the slot stream's salt one bit off, one with the sub-grid's rows and
 * columns swapped, and a tile one cell too narrow.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { latticeSlots, hash3 } from '../renderers/web/js/jobs/lattice-kernel.js';
import { farSlotSpec, FAR_LATTICE_PAD_M, FAR_SLOT_GLSL } from '../renderers/web/js/flora-gpu-far.js';
import { FARSHRUB_LATTICE_PAD_M, FARSHRUB_SALT } from '../renderers/web/js/flora-gpu-farshrub.js';
import { fieldOrigin } from '../renderers/web/js/near-field.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');
const FLORA = fs.readFileSync(path.join(APP, 'renderers/web/js/flora.js'), 'utf8');
const SELF_TEST = process.argv.includes('--self-test');

// flora.js's far bands (TUNE, MID, LOW), the near step, the far salts, the forb cell.
const num = (re, what) => {
  const m = FLORA.match(re);
  if (!m) throw new Error(`flora.js: ${what} not found`);
  return Number(m[1]);
};
const bandRe = /\{ inner: ([\d.]+), innerRamp: [\d.]+, radius: ([\d.]+), ramp: [\d.]+, cell: ([\d.]+), perCell: (\d+),/g;
const bands = [...FLORA.matchAll(bandRe)].map((m) => ({ inner: +m[1], radius: +m[2], cell: +m[3], perCell: +m[4] }));
if (bands.length !== 9) throw new Error(`flora.js: ${bands.length} far bands, not three tiers of three`);
const STEP = num(/step: \{ near: ([\d.]+),/, 'the near step');
const forbCell = num(/ forb: \{ radius: [\d.]+, cell: ([\d.]+), perCell: \d+/, 'the forb cell');
const forbPerCell = num(/ forb: \{ radius: [\d.]+, cell: [\d.]+, perCell: (\d+)/, 'the forb perCell');
const farShrubRadius = Math.max(...[...FLORA.matchAll(/farShrub: \{ radius: ([\d.]+)/g)].map((m) => +m[1]));
if (!/function farSalt\(i\) \{ return 0x3a91c7 \^ \(i \* 0x85ebca6b\); \}/.test(FLORA)) {
  throw new Error('flora.js: farSalt is not the salt this check walks');
}
if (!/fs\.radius, inner, 0x7b5c1d, 'wild', cone,/.test(FLORA)) {
  throw new Error('flora.js: the far shrubs\' walk is not the one this check walks');
}
const farSalt = (i) => 0x3a91c7 ^ (i * 0x85ebca6b);
// The shader's side of the texel rule, as text: the texel FAR_SLOT_GLSL reads.
if (!FAR_SLOT_GLSL.includes('ivec2 t = ivec2(c * sub + k % sub, r * sub + k / sub) - uFarIdx0;')) {
  throw new Error('flora-gpu-far.js: FAR_SLOT_GLSL no longer reads texel (c * sub + k % sub, r * sub + k / sub)');
}

const WALKS = [
  ...bands.map((b, j) => ({ name: `far band ${(j % 3) + 1} (${['full', 'light', 'balanced'][Math.floor(j / 3)]})`,
    cell: b.cell, perCell: b.perCell, radius: b.radius + STEP + FAR_LATTICE_PAD_M,
    inner: Math.max(0, b.inner - STEP - FAR_LATTICE_PAD_M), salt: farSalt(j % 3), draw: 'lattice' })),
  // T-2968: the walk the far shrubs' deal pass and slot field are built on
  // (flora-gpu-farshrub.js `farShrubWalks().gpu`), padded as the far bands are.
  { name: 'far shrubs (full)', cell: forbCell, perCell: forbPerCell,
    radius: farShrubRadius + FARSHRUB_LATTICE_PAD_M, inner: 0, salt: FARSHRUB_SALT, draw: 'wild' },
];

function xorshift(s) {
  s ^= s << 13; s >>>= 0;
  s ^= s >>> 17;
  s ^= s << 5; s >>>= 0;
  return s;
}

/** The check takes its `slotPoint` and its spec as arguments, so the self-test
 *  can hand it broken ones. */
async function run({ slotPoint, spec: specOf, label }) {
  const scene = JSON.parse(fs.readFileSync(path.join(APP, 'data/scenes/1835.json'), 'utf8'));
  let seed = 0x2967;
  const rand = () => { seed = xorshift(seed); return seed / 4294967296; };
  const cams = scene.anchors.map((a) => [a.local_e, a.local_n]);
  for (let i = 0; i < 200; i++) cams.push([(rand() * 2 - 1) * 2000, (rand() * 2 - 1) * 2000]);
  const bad = [];
  let slots = 0;
  for (const w of WALKS) {
    const spec = specOf(w);
    const sub = spec.sub;
    const wild = w.draw === 'wild';
    for (const [camE, camN] of cams) {
      const got = latticeSlots({ camE, camN, cell: w.cell, perCell: w.perCell, radius: w.radius,
        inner: w.inner, salt: w.salt, draw: w.draw, cone: null });
      const n = got.e.length;
      slots += n;
      const seen = new Set();
      // The tile's origin from the camera and from a camera `inHand` (8 m) off.
      const origins = [[0, 0], [8, 0], [-8, 0], [0, 8], [0, -8]].map(([de, dn]) => {
        const o = fieldOrigin(camE + de, camN + dn, spec);
        return [Math.round(o.e0 / spec.texel), Math.round(o.n0 / spec.texel)];
      });
      for (let s = 0; s < n; s++) {
        const e = got.e[s], nn = got.n[s];
        const c = Math.floor(e / w.cell), r = Math.floor(nn / w.cell);
        // The slot's k, from its stream (the walk's own state after the two
        // jitter draws), and so the texel the shader reads for it.
        let k = -1;
        for (let q = 0; q < w.perCell && k < 0; q++) {
          let st = hash3(got.cellSeed[s], q, 0x68bc21eb) >>> 0 || 1;
          st = xorshift(xorshift(st));
          if (st === got.rng[s]) k = q;
        }
        const hit = [c * sub + (k % sub), r * sub + ((k / sub) | 0)];
        const p = k < 0 ? [NaN, NaN] : slotPoint({ salt: w.salt, cell: w.cell, sub, wild }, hit[0], hit[1]);
        if (p[0] !== e || p[1] !== nn) {
          if (bad.length < 8) bad.push(`${w.name} at (${camE.toFixed(1)}, ${camN.toFixed(1)}): slot (${e}, ${nn}) is not its texel's point`);
          continue;
        }
        const key = `${hit[0]},${hit[1]}`;
        if (seen.has(key)) {
          if (bad.length < 8) bad.push(`${w.name}: two slots share texel ${key}`);
        }
        seen.add(key);
        for (const [I0, J0] of origins) {
          const i = hit[0] - I0, j = hit[1] - J0;
          if (i < 0 || j < 0 || i >= spec.size || j >= spec.size) {
            if (bad.length < 8) bad.push(`${w.name} at (${camE.toFixed(1)}, ${camN.toFixed(1)}): texel ${key} off a ${spec.size}-texel tile`);
            break;
          }
        }
      }
    }
  }
  const sizes = WALKS.map((w) => `${w.name} ${specOf(w).size}`).join(', ');
  return { ok: bad.length === 0, slots, bad, sizes, label };
}

const { slotPoint } = await import('../renderers/web/js/jobs/zone-kernel.js');

if (!SELF_TEST) {
  const r = await run({ slotPoint, spec: farSlotSpec, label: 'the slot field' });
  console.log(`far slot field: ${r.slots} slots over ${WALKS.length} walks — ${r.ok ? 'every slot asked at its own point,'
    + ' on a texel of its own, inside its tile' : 'FAIL'}`);
  console.log(`  tile sizes (texels a side): ${r.sizes}`);
  for (const b of r.bad) console.log(`  FAIL ${b}`);
  process.exit(r.ok ? 0 : 1);
}

// The self-test: three broken texts, each of which must be refused.
const offSalt = ({ salt, cell, sub, wild }, I, J, out = [0, 0]) => {
  const c = Math.floor(I / sub), r = Math.floor(J / sub), sx = I - c * sub, sy = J - r * sub;
  let s = hash3(hash3(c, r, salt), sy * sub + sx, 0x68bc21eb ^ 1) >>> 0 || 1;
  s = xorshift(s); const je = s / 4294967296;
  s = xorshift(s); const jn = s / 4294967296;
  out[0] = (c + (wild ? je : (sx + je) / sub)) * cell;
  out[1] = (r + (wild ? jn : (sy + jn) / sub)) * cell;
  return out;
};
const swapped = (o, I, J, out) => {
  const sub = o.sub;
  const c = Math.floor(I / sub), r = Math.floor(J / sub);
  return slotPoint(o, c * sub + (J - r * sub), r * sub + (I - c * sub), out);
};
const narrow = (w) => {
  const s = farSlotSpec(w);
  return { ...s, size: s.size - 2 * Math.ceil(s.cell / s.texel) };
};
let failed = false;
for (const [label, opts] of [
  ['a slot stream salt one bit off', { slotPoint: offSalt, spec: farSlotSpec }],
  ['the sub-grid\'s rows and columns swapped', { slotPoint: swapped, spec: farSlotSpec }],
  ['a tile one cell too narrow', { slotPoint, spec: narrow }],
]) {
  const r = await run({ ...opts, label });
  const refused = !r.ok;
  console.log(`${refused ? 'refused' : 'NOT REFUSED'}: ${label}${r.bad[0] ? ` (${r.bad[0]})` : ''}`);
  if (!refused) failed = true;
}
console.log(failed ? 'self-test FAIL' : 'self-test PASS: the check refuses all three');
process.exit(failed ? 1 : 0);
