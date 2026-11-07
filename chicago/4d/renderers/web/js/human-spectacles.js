// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Spectacles for a person whose portrait shows them (T-3440).
 *
 * Kevin, 2026-11-07, on John J. Glessner's card: "his likeness is still not right". The 1897
 * plate (source glessner_commercial_club_1910_presidents_plate) shows him in round wire
 * spectacles; the model had none. This draws a pair at load, fitted to the person's own face
 * in its bind pose, in metres:
 *
 *  - two round rims centred on the eyes, set out in front of them by the lens's vertex
 *    distance, and tilted down a little at the bottom (pantoscopic tilt), as worn;
 *  - a bridge arched over the nose between the rims;
 *  - temples from each rim's outer edge back along the side of the head to just over the ear,
 *    where they bend down behind it;
 *  - lenses: thin clear discs, faintly reflective, so the eyes read through them.
 *
 * Skinned wholly to the head bone of the face's own skeleton (as human-hair.js binds its
 * cards), so they move with the head. One small geometry and two materials per pair, no
 * texture. Near levels only (LOD0, LOD1). The shape is drawn from the person's photograph; the
 * metal and its finish are not readable in a monochrome halftone and are reconstructed.
 */
import * as THREE from 'three';
import { boneRest, restMatrix } from './human-skin.js';
import { headFrame, metricSurface } from './human-hair.js';

/** Who wears spectacles, by the id their actor carries, and what is known of them. */
export const PEOPLE_SPECTACLES = Object.freeze({
  glessner_john_j: Object.freeze({
    shape: 'round', lens_mm: 38, wire_mm: .9, metal: 'gold',
    grade: 'attested',
    sources: Object.freeze(['glessner_commercial_club_1910_presidents_plate']),
    basis: 'Round wire-rimmed spectacles are worn in the 1897 portrait plate (The Commercial Club of Chicago, 1910, p. 81). The rims\' size and set are read from the plate against the fitted face; the metal (gold wire) and its finish are reconstructed, the plate being a monochrome halftone.',
  }),
});

/** Metal finishes, linear RGB. */
const METALS = Object.freeze({
  gold: Object.freeze({ color: [.62, .45, .22], roughness: .32 }),
  steel: Object.freeze({ color: [.42, .43, .45], roughness: .3 }),
});

/** How far in front of the cornea the lens sits (the vertex distance). */
const LENS_AHEAD_M = .012;
const TILT = 8 * Math.PI / 180;   // the lenses' lower edges toward the cheeks

export function spectaclesFor(personId) {
  return personId ? PEOPLE_SPECTACLES[personId] ?? null : null;
}

/** A tube along a polyline of points (metres), `r` its radius, `sides` around. */
function tube(points, r, sides, out) {
  const base = out.position.length / 3;
  const t = new THREE.Vector3(), a = new THREE.Vector3(), b = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    t.copy(points[Math.min(points.length - 1, i + 1)]).sub(points[Math.max(0, i - 1)]).normalize();
    a.copy(Math.abs(t.dot(up)) > .9 ? new THREE.Vector3(1, 0, 0) : up).cross(t).normalize();
    b.crossVectors(t, a);
    for (let s = 0; s < sides; s++) {
      const th = s / sides * Math.PI * 2, c = Math.cos(th), sn = Math.sin(th);
      const n = a.clone().multiplyScalar(c).addScaledVector(b, sn);
      out.position.push(p.x + n.x * r, p.y + n.y * r, p.z + n.z * r);
      out.normal.push(n.x, n.y, n.z);
    }
  }
  for (let i = 0; i < points.length - 1; i++) {
    for (let s = 0; s < sides; s++) {
      const i0 = base + i * sides + s, i1 = base + i * sides + (s + 1) % sides;
      out.index.push(i0, i0 + sides, i1, i1, i0 + sides, i1 + sides);
    }
  }
}

/**
 * The pair's geometry in the face's bind pose (metres from `root`), from its frame and its
 * own skin: { frame, wire: {position, normal, index}, lens: {...}, width_m }. Null when the
 * face has no eyes to fit to.
 */
/**
 * Each eye's front (the cornea's apex) in the bind pose, metres from `root`, from the eye
 * surfaces themselves (sclera, iris, pupil): the eye bones sit at the eyeball's back, not at
 * the eye a lens has to be centred on. [left, right] along the frame's x, or null.
 */
export function eyeFronts(root, f) {
  const sides = [[], []], v = new THREE.Vector3();
  root.traverse(o => {
    if (!o.isMesh || !/(sclera|iris|pupil|cornea)/.test(o.material?.name ?? '')) return;
    const s = metricSurface(o, root);
    for (let i = 0; i < s.count; i++) {
      v.set(s.P[3 * i], s.P[3 * i + 1], s.P[3 * i + 2]);
      sides[v.clone().sub(f.o).dot(f.x) > 0 ? 0 : 1].push(v.clone());
    }
  });
  if (!sides[0].length || !sides[1].length) return null;
  return sides.map(pts => {
    // The pupil's line: the centre of the eye's visible disc, at its front-most depth.
    let front = -Infinity;
    for (const p of pts) front = Math.max(front, p.clone().sub(f.o).dot(f.z));
    const disc = pts.filter(p => p.clone().sub(f.o).dot(f.z) > front - .004);
    const c = disc.reduce((a, p) => a.add(p), new THREE.Vector3()).divideScalar(disc.length);
    return c.addScaledVector(f.z, front - c.clone().sub(f.o).dot(f.z));
  });
}

export function fitSpectacles(skin, root, spec) {
  const f = headFrame(skin, root);
  if (!f) return null;
  const bones = skin.skeleton.bones, at = name => { const i = bones.findIndex(b => b.name === name); return i < 0 ? null : boneRest(skin, root, i); };
  const fronts = eyeFronts(root, f);
  // Without eye surfaces, the bones: a cornea about 12 mm in front of the eye bone.
  const [eyeL, eyeR] = fronts ?? [at('eye_l')?.addScaledVector(f.z, .012), at('eye_r')?.addScaledVector(f.z, .012)];
  if (!eyeL || !eyeR) return null;
  // The face's half-width at the eyes, just in front of the ears: where the temples run.
  const s = metricSurface(skin, root), v = new THREE.Vector3();
  let half = 0;
  for (let i = 0; i < s.count; i++) {
    v.set(s.P[3 * i], s.P[3 * i + 1], s.P[3 * i + 2]).sub(f.o);
    const y = v.dot(f.y), z = v.dot(f.z);
    if (y > -.012 && y < .025 && z > -.06 && z < .0) half = Math.max(half, Math.abs(v.dot(f.x)));
  }
  if (!(half > .05 && half < .1)) half = .072;
  const r = spec.lens_mm / 1000 / 2, wire = spec.wire_mm / 1000 / 2;
  // The lens plane is tilted about the frame's x: its down direction leans back toward the face.
  const down = f.y.clone().negate().applyAxisAngle(f.x, -TILT), across = f.x.clone();
  const fwd = new THREE.Vector3().crossVectors(across, down.clone().negate()).normalize();
  if (fwd.dot(f.z) < 0) fwd.negate();
  const wireOut = { position: [], normal: [], index: [] }, lensOut = { position: [], normal: [], index: [] };
  const centres = [];
  for (const eye of [eyeL, eyeR]) {
    const side = Math.sign(eye.clone().sub(f.o).dot(f.x)) || 1;
    // A rim a little above and outside the pupil, as spectacles sit.
    const c = eye.clone().addScaledVector(f.z, LENS_AHEAD_M).addScaledVector(f.y, .001).addScaledVector(f.x, side * .001);
    centres.push({ c, side });
    const ring = [];
    for (let k = 0; k <= 40; k++) {
      const th = k / 40 * Math.PI * 2;
      ring.push(c.clone().addScaledVector(across, Math.cos(th) * r).addScaledVector(down, Math.sin(th) * r));
    }
    tube(ring, wire, 6, wireOut);
    // The lens: a disc inside the rim.
    const base = lensOut.position.length / 3;
    lensOut.position.push(c.x, c.y, c.z); lensOut.normal.push(fwd.x, fwd.y, fwd.z);
    for (let k = 0; k < 40; k++) {
      const th = k / 40 * Math.PI * 2, p = c.clone().addScaledVector(across, Math.cos(th) * r * .98).addScaledVector(down, Math.sin(th) * r * .98);
      lensOut.position.push(p.x, p.y, p.z); lensOut.normal.push(fwd.x, fwd.y, fwd.z);
    }
    for (let k = 0; k < 40; k++) lensOut.index.push(base, base + 1 + k, base + 1 + (k + 1) % 40);
    // The temple: from the rim's outer edge, back along the head over the ear, then down behind it.
    const hinge = c.clone().addScaledVector(across, side * r);
    const bend = f.o.clone().addScaledVector(f.x, side * (half + .004)).addScaledVector(f.y, .004).addScaledVector(f.z, -.075);
    const pts = [hinge, hinge.clone().addScaledVector(f.x, side * .004).addScaledVector(f.z, -.006)];
    const startSide = pts[1];
    for (let k = 1; k <= 8; k++) {
      const t = k / 8;
      pts.push(startSide.clone().lerp(bend, t)
        .addScaledVector(f.x, side * .003 * Math.sin(Math.PI * t)));
    }
    pts.push(bend.clone().addScaledVector(f.y, -.012).addScaledVector(f.z, -.008), bend.clone().addScaledVector(f.y, -.024).addScaledVector(f.z, -.008));
    tube(pts, wire * .9, 5, wireOut);
  }
  // The bridge: an arch over the nose from rim to rim, a little above the lens centres.
  const [a, b] = centres;
  const inner = (q) => q.c.clone().addScaledVector(across, -q.side * r);
  const p0 = inner(a), p1 = inner(b), mid = p0.clone().add(p1).multiplyScalar(.5).addScaledVector(f.y, .004).addScaledVector(f.z, .002);
  const arch = [];
  for (let k = 0; k <= 10; k++) {
    const t = k / 10, u = 1 - t;
    arch.push(p0.clone().multiplyScalar(u * u).add(mid.clone().multiplyScalar(2 * u * t)).add(p1.clone().multiplyScalar(t * t)));
  }
  tube(arch, wire, 6, wireOut);
  return { frame: f, wire: wireOut, lens: lensOut, width_m: 2 * half };
}

function geometryOf(part, headIndex) {
  const g = new THREE.BufferGeometry(), n = part.position.length / 3;
  g.setAttribute('position', new THREE.Float32BufferAttribute(part.position, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(part.normal, 3));
  g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(new Uint16Array(n * 4).map((_, i) => i % 4 ? 0 : headIndex), 4));
  g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(new Float32Array(n * 4).map((_, i) => i % 4 ? 0 : 1), 4));
  g.setIndex(part.index);
  return g;
}

const materials = new Map();
function materialsFor(spec) {
  const key = spec.metal;
  if (!materials.has(key)) {
    const m = METALS[spec.metal] ?? METALS.steel;
    materials.set(key, {
      wire: new THREE.MeshStandardMaterial({ name: 'spectacles_wire', color: new THREE.Color().setRGB(...m.color, THREE.LinearSRGBColorSpace), metalness: 1, roughness: m.roughness }),
      lens: new THREE.MeshPhysicalMaterial({ name: 'spectacles_lens', color: 0xffffff, metalness: 0, roughness: .04, transparent: true, opacity: .1, depthWrite: false, side: THREE.DoubleSide, envMapIntensity: 1.4 }),
    });
  }
  return materials.get(key);
}

/**
 * Give one cloned (and varied) figure its spectacles, when its person wears them.
 * Returns { group, fit } or null. Call after the variation, like dressHair.
 */
export function dressSpectacles(root, { lod = 0, person = null, spec: given = null } = {}) {
  if (!root || lod > 1) return null;
  const spec = given ?? spectaclesFor(person);
  if (!spec) return null;
  let skin = null;
  root.traverse(o => { if (o.isSkinnedMesh && /^skin($|__)/.test(o.material?.name ?? '')) skin ??= o; });
  if (!skin?.skeleton || !skin.parent) return null;
  const headIndex = skin.skeleton.bones.findIndex(b => b.name === 'head');
  if (headIndex < 0) return null;
  const fit = fitSpectacles(skin, root, spec);
  if (!fit) return null;
  const R = restMatrix(skin, root), bind = skin.bindMatrix.clone().multiply(R.clone().invert());
  const m = materialsFor(spec), meshes = [];
  for (const [part, material, name] of [[fit.wire, m.wire, 'spectacles_wire'], [fit.lens, m.lens, 'spectacles_lens']]) {
    const mesh = new THREE.SkinnedMesh(geometryOf(part, headIndex), material);
    mesh.name = name;
    mesh.frustumCulled = false;
    mesh.castShadow = name === 'spectacles_wire';
    mesh.renderOrder = name === 'spectacles_lens' ? 2 : 0;
    mesh.bind(skin.skeleton, bind);
    skin.parent.add(mesh);
    meshes.push(mesh);
  }
  return { meshes, fit, spec };
}
