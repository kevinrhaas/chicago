// SPDX-License-Identifier: GPL-3.0-or-later
// human-mouth.js — a mouth that opens: the teeth behind the lips, and what plays the smile (T-3553).
//
// The owner, 2026-11-13, of the Greys' stand-in likenesses: "add what is needed to the face
// model to make it work and eventually speak, i want them photographic matched". A person
// whose front picture grins (or who has a picture of their smile of its own) rests with their
// mouth shut, as their other pictures show it, and moves into the grin: human-variation.js gives their body a morph target for it (SMILE), from
// the smile their record fitted to that picture (tools/bake_likeness_skin.py). Two things here:
//
// The teeth. Between parted lips something has to stand. The record (`texture.teeth`) gives a
// strip of points behind the lips: where each stands (metres, the body's rest frame) and where
// on the body's own map its colour is, a patch of their skin sheet that holds the front
// picture's teeth. The strip is added to the body's skin geometry as rows of its own, carried
// whole by one bone (the head's), so it is drawn by the skin's own material in the skin's own
// draw call, at every level of detail. With the mouth shut the lips stand in front of it, and
// what shows between lips that do not seal is in their shade (human-skin.js MOUTH_SHADE: the
// strip takes the light as the face moves into its smile).
//
// What a caller may rely on:
//   - the first rows of every attribute are the source's own, in its order;
//   - the strip's rows follow: `cols` across by `rows` down, a row of the record at a time,
//     two triangles a cell, facing out of the mouth;
//   - every morph target leaves the strip where it stands;
//   - a geometry drawn in groups, or with no index, comes back as null, and the source is
//     never changed.
//
// The mouth's play (createMouth). A person with a smile gives it to a visitor who stands near
// in front of them, and with a greeting; talking, they keep some of it and their jaw moves
// with the talk (the skeleton's `jaw` bone turned about its hinge in an uneven run of syllables,
// no words; the body's exported `jawOpen` target turns both lips together and opens nothing).
// human-skin.js leaves one on each figure whose face has the smile (`userData.chiMouth`), and
// human-actions.js, which knows when the person greets and talks, tells it each frame.
// `say(level)` is where a voice goes when one speaks for them: it takes the jaw outright, a
// level at a time, in place of that run. Everyone without a smile is left exactly as drawn.
// Reconstructed motion: liberties L-grey-smile-3553 and L-grey-sarah-smile-3553.
import * as THREE from 'three';
import { rawView, isWhole, fullOf } from './human-fine.js';
import { SMILE, seededRandom } from './human-variation.js';

/** A record's `teeth` block as numbers ({ cols, rows, at, uv, bone, rect }), or null where it does not parse. */
export function teethStrip(teeth) {
  const [cols, rows] = teeth?.grid ?? [], n = cols * rows;
  if (!(cols >= 2) || !(rows >= 2) || !Number.isInteger(n) || typeof teeth.bone !== 'string') return null;
  const { at_m, uv } = teeth;
  if (!Array.isArray(at_m) || !Array.isArray(uv) || at_m.length !== n || uv.length !== n) return null;
  if (!at_m.every(p => p?.length === 3 && p.every(Number.isFinite)) || !uv.every(p => p?.length === 2 && p.every(Number.isFinite))) return null;
  // The strip's own part of the body's map, a hair wider than its points.
  const us = uv.map(p => p[0]), vs = uv.map(p => p[1]), e = 1e-4;
  return { cols, rows, at: Float32Array.from(at_m.flat()), uv: Float32Array.from(uv.flat()), bone: teeth.bone,
    rect: [Math.min(...us) - e, Math.min(...vs) - e, Math.max(...us) + e, Math.max(...vs) + e] };
}

/** `attr` with `added` rows more, each number of a new row given by `value(row, part)` in the attribute's own meaning. */
function withRows(attr, n0, added, value) {
  const { array, stride, offset } = rawView(attr), k = attr.itemSize, out = new array.constructor((n0 + added) * k);
  const whole = isWhole(out), full = whole && attr.normalized ? fullOf(out) : 1;
  const lo = whole ? (out instanceof Int8Array ? -127 : out instanceof Int16Array ? -32767 : 0) : -Infinity;
  const hi = whole ? (out instanceof Uint8Array ? 255 : out instanceof Int8Array ? 127 : out instanceof Uint16Array ? 65535 : out instanceof Int16Array ? 32767 : 4294967295) : Infinity;
  for (let i = 0; i < n0; i++) for (let c = 0; c < k; c++) out[i * k + c] = array[i * stride + offset + c];
  for (let j = 0; j < added; j++) for (let c = 0; c < k; c++) {
    const v = value(j, c) * full;
    out[(n0 + j) * k + c] = whole ? Math.min(hi, Math.max(lo, Math.round(v))) : v;
  }
  const made = new THREE.BufferAttribute(out, k, attr.normalized);
  made.name = attr.name;
  return made;
}

/**
 * `src` with the strip of teeth added: a new geometry, or null where it cannot be (no strip, no
 * index, drawn in groups, no texture coordinates).
 *
 *   metres   the matrix taking `src`'s positions to metres (human-skin.js restMatrix)
 *   strip    teethStrip(...)
 *   bone     the number, in the mesh's skeleton, of the bone that carries the strip
 */
export function teethGeometry(src, { metres, strip, bone } = {}) {
  const pos = src?.attributes?.position, tex = src?.attributes?.uv;
  if (!pos || !tex || !src.index || src.groups?.length || !strip || !metres || !(bone >= 0)) return null;
  const { cols, rows, at, uv } = strip, added = cols * rows, n0 = pos.count;
  const back = new THREE.Matrix4().copy(metres).invert(), turn = new THREE.Matrix3().setFromMatrix4(metres).transpose();
  // Where each point stands in the geometry's own numbers, and which way the strip faces there.
  const P = new Float32Array(added * 3), N = new Float32Array(added * 3), v = new THREE.Vector3(), a = new THREE.Vector3(), b = new THREE.Vector3();
  const point = (c, r, out) => out.fromArray(at, 3 * (Math.min(rows - 1, Math.max(0, r)) * cols + Math.min(cols - 1, Math.max(0, c))));
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const i = r * cols + c;
    v.fromArray(at, 3 * i).applyMatrix4(back).toArray(P, 3 * i);
    // across (the body's left) by up: out of the mouth
    a.subVectors(point(c + 1, r, a), point(c - 1, r, v));
    b.subVectors(point(c, r - 1, b), point(c, r + 1, v));
    v.crossVectors(a, b).applyMatrix3(turn).normalize().toArray(N, 3 * i);
  }
  const tri = Array.from(src.index.array);
  for (let r = 0; r + 1 < rows; r++) for (let c = 0; c + 1 < cols; c++) {
    const i = n0 + r * cols + c;
    tri.push(i, i + cols, i + 1, i + 1, i + cols, i + cols + 1);
  }
  const n = n0 + added, g = new THREE.BufferGeometry();
  g.name = `${src.name || 'skin'}~teeth`;
  g.setIndex(new THREE.BufferAttribute(n > 65535 ? Uint32Array.from(tri) : Uint16Array.from(tri), 1));
  for (const [name, attr] of Object.entries(src.attributes)) {
    const value = name === 'position' ? (j, c) => P[3 * j + c]
      : name === 'normal' ? (j, c) => N[3 * j + c]
        : /^uv\d*$/.test(name) ? (j, c) => uv[2 * j + c]
          : name === 'skinIndex' ? (j, c) => (c === 0 ? bone : 0)
            : name === 'skinWeight' ? (j, c) => (c === 0 ? 1 : 0)
              : name === 'tangent' ? (j, c) => (c === 0 || c === 3 ? 1 : 0)
                : name === 'color' ? () => 1 : () => 0;
    g.setAttribute(name, withRows(attr, n0, added, value));
  }
  // A morph target that moves (the blink, a jaw) leaves the strip alone; one that states
  // positions outright states the strip's own.
  for (const [name, list] of Object.entries(src.morphAttributes ?? {})) {
    g.morphAttributes[name] = list.map(t => t && withRows(t, n0, added, src.morphTargetsRelative || name !== 'position' ? () => 0 : (j, c) => P[3 * j + c]));
  }
  g.morphTargetsRelative = src.morphTargetsRelative;
  // The strip stands inside the head: the source's bounds hold.
  g.boundingBox = src.boundingBox; g.boundingSphere = src.boundingSphere;
  g.userData = { ...src.userData, chiTeeth: { of: n0, added } };
  return g;
}

const kept = new WeakMap();   // source geometry -> Map(key -> geometry with teeth, or null)

/**
 * teethGeometry, once for each source and `key` (a person's sheet), freed when its source is.
 * A geometry that already has its teeth is handed back as it is.
 */
export function teethOf(src, key, opts) {
  if (!src || src.userData?.chiTeeth) return src ?? null;
  let own = kept.get(src);
  if (!own) {
    kept.set(src, (own = new Map()));
    src.addEventListener('dispose', () => { for (const g of own.values()) g?.dispose(); own.clear(); });
  }
  if (!own.has(key)) own.set(key, teethGeometry(src, opts));
  return own.get(key) ?? src;
}

/**
 * The mouth's play, for a person whose body has the smile.
 *   within_m, front_deg   a visitor this near, and no further round from straight ahead, is smiled at
 *   in_s, out_s         how fast the smile comes and goes
 *   after_s             how long it stays after a greeting
 *   talk                how much of it a person keeps while talking
 *   jaw_deg, syllable_hz  talking: how far the jaw turns at a syllable's height, and their rate
 *   say_deg             a voice's level 1 turns the jaw this far
 */
export const MOUTH = Object.freeze({ within_m: 3.2, front_deg: 60, in_s: .3, out_s: .7, after_s: 2.2, talk: .4, jaw_deg: 7, syllable_hz: 3.6, say_deg: 12 });
const JAW = 'jaw', DEG = Math.PI / 180;

export function createMouth({ id = 'human', scene = null } = {}) {
  const rand = seededRandom(`mouth:${id}`);
  let faces = [], jaw = null, time = rand() * 40, smile = 0, after = 0, open = 0, said = null;
  const off = [rand() * 6.283, rand() * 6.283], turn = new THREE.Quaternion();
  // The jaw's bone is the clip's to pose: what it holds is taken as found each frame, unless it
  // is what this left there, and the opening is turned on over it.
  const turnJaw = () => {
    if (!jaw) return;
    const q = jaw.bone.quaternion;
    if (q.equals(jaw.out)) q.copy(jaw.base); else jaw.base.copy(q);
    if (open > 0) { q.premultiply(turn.setFromAxisAngle(jaw.axis, open * DEG)); jaw.out.copy(q); } else jaw.out.set(NaN, NaN, NaN, NaN);
  };
  const show = () => { for (const f of faces) f.mesh.morphTargetInfluences[f.smile] = smile; turnJaw(); };
  const api = {
    /** The meshes of `next` that take the smile, and its jaw; false where the figure has no smile. */
    bind(next) {
      // A jaw this left turned (a level set aside while talking) goes back to the clip's first.
      if (jaw?.bone.quaternion.equals(jaw.out)) jaw.bone.quaternion.copy(jaw.base);
      faces = []; jaw = null;
      next?.traverse((o) => {
        const at = o.isMesh ? o.morphTargetDictionary?.[SMILE] : undefined;
        if (at !== undefined && o.morphTargetInfluences) faces.push({ mesh: o, smile: at });
        if (jaw || !o.isSkinnedMesh) return;
        // The hinge: the body's own left-to-right, as its jaw's parent bone holds it in the bind
        // pose, so it does not depend on how the head is turned when this is read.
        const bones = o.skeleton?.bones ?? [], k = bones.findIndex(b => b.name === JAW), p = k < 0 ? -1 : bones.indexOf(bones[k].parent);
        if (p < 0) return;
        const axis = new THREE.Vector3(1, 0, 0).transformDirection(new THREE.Matrix4().multiplyMatrices(o.skeleton.boneInverses[p], o.bindMatrix));
        jaw = { bone: bones[k], axis, base: bones[k].quaternion.clone(), out: new THREE.Quaternion(NaN, NaN, NaN, NaN) };
      });
      if (!faces.length) jaw = null;
      show();
      return faces.length > 0;
    },
    get bound() { return faces.length > 0; },
    /** A voice's level now (0..1) turns the jaw in place of the talk's own run; null gives it back. */
    say(level) { said = Number.isFinite(level) ? Math.min(1, Math.max(0, level)) : null; return api; },
    /** Hold the face so (a still): `smile` 0..1 of the smile, `jaw` degrees open. */
    pose({ smile: s = smile, jaw: j = open } = {}) {
      smile = Math.min(1, Math.max(0, Number(s) || 0)); open = Math.max(0, Number(j) || 0);
      show();
      return api;
    },
    /** Carry on from another mouth of the same person (the level drawn before this one). */
    follow(prev) {
      const s = prev?.state?.();
      if (s) { ({ time, smile, after, open, said } = s); show(); }
      return api;
    },
    state() { return { time, smile, after, open, said }; },
    /**
     * A frame of `dt` seconds. `greeting`: the person is greeting someone; `talk`: how much they
     * are talking (0..1); `viewer` (a world position) and `root` (the figure's own root, which
     * faces its +Z): where the visitor stands, or `facing` outright.
     */
    apply(dt, { greeting = false, talk = 0, viewer = null, root = null, facing = null } = {}) {
      if (!faces.length) return;
      dt = Number.isFinite(dt) && dt > 0 ? Math.min(dt, .1) : 0;
      time += dt;
      if (facing === null) {
        facing = false;
        if (viewer && root) {
          const dx = viewer.x - root.position.x, dz = viewer.z - root.position.z, a = root.rotation.y;
          // The visitor in the figure's own frame (turned back by its heading about the upright).
          const x = dx * Math.cos(a) - dz * Math.sin(a), z = dx * Math.sin(a) + dz * Math.cos(a);
          facing = Math.hypot(x, z) < MOUTH.within_m && Math.abs(Math.atan2(x, z)) < MOUTH.front_deg * DEG;
        }
      }
      after = greeting ? MOUTH.after_s : Math.max(0, after - dt);
      const talking = Math.min(1, Math.max(0, talk));
      const want = greeting || after > 0 || facing ? 1 : talking > .05 || said > 0 ? MOUTH.talk * (said > 0 ? 1 : talking) : 0;
      smile += (want - smile) * (1 - Math.exp(-dt / (want > smile ? MOUTH.in_s : MOUTH.out_s)));
      if (Math.abs(want - smile) < 1e-3) smile = want;
      // Talk with no words: syllables at about the rate of speech, uneven in height, with a
      // breath between phrases.
      let to = 0;
      if (said !== null) to = MOUTH.say_deg * said;
      else if (talking > 1e-3) {
        const beat = .5 - .5 * Math.cos(time * 2 * Math.PI * MOUTH.syllable_hz);
        const height = .6 + .4 * Math.sin(time * 1.9 + off[0]);
        const phrase = Math.min(1, Math.max(0, 1.6 + 2.2 * Math.sin(time * .7 + off[1])));
        to = MOUTH.jaw_deg * talking * beat * height * phrase;
      }
      open += (to - open) * (1 - Math.exp(-dt / .04));
      if (open < 1e-3 && to === 0) open = 0;
      show();
    },
    snapshot() { return { smile: +smile.toFixed(3), jaw_deg: +open.toFixed(3), faces: faces.length, said }; },
  };
  if (scene) api.bind(scene);
  return api;
}
