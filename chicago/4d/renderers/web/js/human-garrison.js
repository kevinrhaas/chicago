// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-garrison.js — the Fort Dearborn garrison of 14 August 1812 dressed by rank and armed
 * (T-3523).
 *
 * Kevin, 2026-11-08, beside an Ogden-style plate of the army about 1812: "and all the men
 * soldiers have the same hats? Dont the soldiers have different appearance based on rank? and
 * none of them appear to have firearms?" Every enlisted man stood in the one private's dress
 * (private_first_infantry_1812, T-3451) and nobody carried anything. This draws, at load, on
 * the figure each man already wears (no new figure file: the published site's 432 MB budget
 * and the 1812 phone's 350 MB), what his rank and his duty put on him:
 *
 *   - epaulettes: a sergeant's two of white worsted, a corporal's one on the right shoulder
 *     (the 1814 printing of the light dragoons' rule, read by analogy: docs/RESEARCH/
 *     people-1812-3461/dress.json); an officer's silver one where his grade wears it, the
 *     captain's on the right (in his figure already), the lieutenant's and the ensign's on the
 *     left (this module's, when the record hides the figure's own);
 *   - a crimson silk sash round the waist, knotted at the left hip, for a line officer on a
 *     tour of duty (the 1814 staff text: "to be worn only on a tour of duty, and round the
 *     waist"; Krimmel's officer);
 *   - a drum on the left thigh for a drummer and a fife case at the right hip for a fifer (the
 *     musicians' red coats faced blue are a recolour, in the record's `colours`);
 *   - a musket with its bayonet fixed, of the 1795 Springfield / French Charleville pattern,
 *     carried as his duty has it: a sentry walking his post at the shoulder (the firelock on
 *     the left shoulder, the butt in the left hand, the lock turned out), the guard's sergeant
 *     and corporal and a sentry standing at the order (the butt on the ground by the right toe,
 *     the right hand round the barrel); men at their chores carry none, and where the work is
 *     out at the forks their arms stand piled at the field's edge (createArmsPiles).
 *
 * Every piece is rigid on one bone of the figure's own skeleton (an epaulette on the clavicle,
 * a sash, drum or fife case on the pelvis, a musket in the hand), a child of that bone placed
 * from the figure's own bind pose: the T-pose's shoulder joints, neck, waist and coat surface.
 * A carried musket's hand is held where the carry puts it by human-actions.js (`carry`, the
 * same hold T-3481 gave a market basket), so it does not swing; the musket is laid in that hand
 * in the hand's own frame (its fingers and palm, as human-actions.js reads them), so it sits
 * where the hold puts the hand, whatever the arm's IK makes of the reach.
 *
 * Geometry is drawn here, small and textureless, like the spectacles (human-spectacles.js): a
 * musket is shared by every figure at a level of detail, an epaulette strap and a sash are
 * fitted to their own wearer. Shapes are reconstructed from the period descriptions in the
 * dress research and the regulation dimensions of the arm (about 59.5 in overall, a 44.75 in
 * barrel, a 15 in triangular bayonet blade); colours are reconstructed. Liberty
 * L-1812-garrison-dress-3523.
 */
import * as THREE from 'three';

/**
 * A skinned mesh's bind-pose positions in metres from `root` (a quantised derivative's raw
 * positions are not metres): as human-hair.js's metricSurface reads them, kept here so this
 * module stands alone.
 */
function metricPoints(mesh, root) {
  root.updateMatrixWorld(true);
  const R = new THREE.Matrix4().copy(root.matrixWorld).invert();
  const b0 = mesh.isSkinnedMesh ? mesh.skeleton?.bones?.[0] : null;
  if (b0) R.multiply(b0.matrixWorld).multiply(mesh.skeleton.boneInverses[0]).multiply(mesh.bindMatrix);
  else R.multiply(mesh.matrixWorld);
  const p = mesh.geometry.attributes.position, v = new THREE.Vector3(), out = [];
  for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i).applyMatrix4(R); out.push([v.x, v.y, v.z]); }
  return out;
}

const DEG = Math.PI / 180;

/** Linear-RGB cloths and metals of the pieces (reconstructed). */
const STUFF = Object.freeze({
  walnut: { color: [0.085, 0.04, 0.018], roughness: 0.5, metalness: 0 },
  iron: { color: [0.42, 0.42, 0.44], roughness: 0.38, metalness: 0.9 },
  brass: { color: [0.55, 0.38, 0.12], roughness: 0.35, metalness: 0.9 },
  buff: { color: [0.70, 0.67, 0.60], roughness: 0.75, metalness: 0 },
  worsted_white: { color: [0.74, 0.73, 0.68], roughness: 0.92, metalness: 0 },
  silver: { color: [0.70, 0.70, 0.71], roughness: 0.42, metalness: 0.7 },
  crimson_silk: { color: [0.36, 0.018, 0.03], roughness: 0.55, metalness: 0 },
  drum_shell: { color: [0.025, 0.04, 0.12], roughness: 0.5, metalness: 0 },
  drum_hoop: { color: [0.34, 0.03, 0.025], roughness: 0.6, metalness: 0 },
  drum_head: { color: [0.58, 0.52, 0.40], roughness: 0.7, metalness: 0 },
  cord_white: { color: [0.72, 0.70, 0.64], roughness: 0.85, metalness: 0 },
  black_leather: { color: [0.012, 0.011, 0.01], roughness: 0.45, metalness: 0 },
});

const materials = new Map();
function material(name) {
  let m = materials.get(name);
  if (!m) {
    const s = STUFF[name];
    m = new THREE.MeshStandardMaterial({ name: `garrison_${name}`, color: new THREE.Color().setRGB(...s.color, THREE.LinearSRGBColorSpace),
      roughness: s.roughness, metalness: s.metalness, side: name === 'worsted_white' || name === 'silver' || name === 'crimson_silk' ? THREE.DoubleSide : THREE.FrontSide });
    materials.set(name, m);
  }
  return m;
}

// ---------------------------------------------------------------------------------------------
// Primitive builders. Each pushes into a {position, normal, index} part, metres.

function part() { return { position: [], normal: [], index: [] }; }

function geometryOf(p) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(p.position, 3));
  if (p.normal.length === p.position.length) g.setAttribute('normal', new THREE.Float32BufferAttribute(p.normal, 3));
  g.setIndex(p.index);
  if (p.normal.length !== p.position.length) g.computeVertexNormals();
  g.computeBoundingSphere();
  return g;
}

/**
 * A loft along +Y of rounded-rectangle sections: stations [y, half-width x, half-height z,
 * centre z]. `sides` points round each section; `round` 2 is an ellipse, higher squarer.
 */
function loft(out, stations, sides, round = 3, capEnds = true) {
  const base = out.position.length / 3;
  const ring = (st) => {
    const [y, hx, hz, cz] = st;
    const pts = [];
    for (let s = 0; s < sides; s++) {
      const a = (s / sides) * Math.PI * 2, c = Math.cos(a), sn = Math.sin(a);
      const k = 2 / round;
      const x = hx * Math.sign(c) * Math.abs(c) ** k, z = hz * Math.sign(sn) * Math.abs(sn) ** k;
      pts.push([x, y, cz + z, c, sn]);
    }
    return pts;
  };
  for (const st of stations) for (const [x, y, z, c, sn] of ring(st)) { out.position.push(x, y, z); out.normal.push(c, 0, sn); }
  for (let i = 0; i < stations.length - 1; i++) for (let s = 0; s < sides; s++) {
    const a = base + i * sides + s, b = base + i * sides + (s + 1) % sides;
    out.index.push(a, a + sides, b, b, a + sides, b + sides);
  }
  if (capEnds) {
    for (const [i, dir] of [[0, -1], [stations.length - 1, 1]]) {
      const st = stations[i], c = out.position.length / 3;
      out.position.push(0, st[0], st[3]); out.normal.push(0, dir, 0);
      const r0 = base + i * sides;
      for (let s = 0; s < sides; s++) {
        const a = r0 + s, b = r0 + (s + 1) % sides;
        if (dir < 0) out.index.push(c, a, b); else out.index.push(c, b, a);
      }
    }
  }
}

/** A cylinder along +Y from y0 to y1, radius r0 to r1, centred at (cx, cz). */
function cylinder(out, y0, y1, r0, r1, sides, cx = 0, cz = 0, cap = true) {
  const base = out.position.length / 3;
  for (const [y, r] of [[y0, r0], [y1, r1]]) for (let s = 0; s < sides; s++) {
    const a = (s / sides) * Math.PI * 2;
    out.position.push(cx + r * Math.cos(a), y, cz + r * Math.sin(a)); out.normal.push(Math.cos(a), 0, Math.sin(a));
  }
  for (let s = 0; s < sides; s++) {
    const a = base + s, b = base + (s + 1) % sides;
    out.index.push(a, a + sides, b, b, a + sides, b + sides);
  }
  if (cap) for (const [row, y, dir] of [[0, y0, -1], [1, y1, 1]]) {
    const c = out.position.length / 3;
    out.position.push(cx, y, cz); out.normal.push(0, dir, 0);
    for (let s = 0; s < sides; s++) {
      const a = base + row * sides + s, b = base + row * sides + (s + 1) % sides;
      if (dir < 0) out.index.push(c, a, b); else out.index.push(c, b, a);
    }
  }
}

/** An axis-aligned box, centre and half sizes. */
function box(out, [cx, cy, cz], [hx, hy, hz]) {
  const faces = [[[1, 0, 0], [0, 1, 0], [0, 0, 1]], [[-1, 0, 0], [0, 0, 1], [0, 1, 0]], [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
    [[0, -1, 0], [1, 0, 0], [0, 0, 1]], [[0, 0, 1], [1, 0, 0], [0, 1, 0]], [[0, 0, -1], [0, 1, 0], [1, 0, 0]]];
  const h = [hx, hy, hz];
  for (const [n, u, v] of faces) {
    const base = out.position.length / 3;
    for (const [su, sv] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
      const p = [0, 1, 2].map((k) => [cx, cy, cz][k] + n[k] * h[k] + u[k] * su * h[k] + v[k] * sv * h[k]);
      out.position.push(...p); out.normal.push(...n);
    }
    out.index.push(base, base + 1, base + 2, base, base + 2, base + 3);
  }
}

/** Apply a Matrix4 to a part in place (positions and normals). */
function transformPart(p, m) {
  const v = new THREE.Vector3(), n = new THREE.Matrix3().getNormalMatrix(m);
  for (let i = 0; i < p.position.length; i += 3) {
    v.set(p.position[i], p.position[i + 1], p.position[i + 2]).applyMatrix4(m);
    p.position[i] = v.x; p.position[i + 1] = v.y; p.position[i + 2] = v.z;
    if (p.normal.length) {
      v.set(p.normal[i], p.normal[i + 1], p.normal[i + 2]).applyMatrix3(n).normalize();
      p.normal[i] = v.x; p.normal[i + 1] = v.y; p.normal[i + 2] = v.z;
    }
  }
  return p;
}

function append(into, p) {
  const base = into.position.length / 3;
  into.position.push(...p.position); into.normal.push(...p.normal);
  for (const i of p.index) into.index.push(base + i);
  return into;
}

// ---------------------------------------------------------------------------------------------
// The musket, in its own frame: +Y along the barrel from the butt plate (y = 0) to the muzzle,
// +Z the barrel's top (toward the sights), +X the lock side. Pattern of 1795 Springfield
// (after the French 1763/1766 Charleville): 1.51 m overall, a round barrel of 1.137 m, three
// bands, a walnut stock, a socket bayonet whose 0.38 m triangular blade lies under the barrel.

export const MUSKET = Object.freeze({
  length_m: 1.51, barrel_m: 1.137, bayonet_blade_m: 0.38, butt_z: -0.045,
  basis: 'Overall length, barrel and bayonet after the regulation 1795 Springfield musket and its French model (the 1763/1766 Charleville pattern); the stock\'s sections, the lock, bands and sling are reconstructed shapes, not traced from any picture.',
});

const musketCache = new Map();
function musketParts(detail) {
  const key = detail;
  if (musketCache.has(key)) return musketCache.get(key);
  const hi = detail === 'hi';
  const sides = hi ? 10 : 6;
  const wood = part(), iron = part(), buff = part();
  // The stock: the butt dropped below the line of the barrel, the small of the stock (the
  // wrist), the lock's swell, and the fore-end under the barrel to short of the muzzle.
  loft(wood, [
    [0.0, 0.022, 0.064, -0.050], [0.10, 0.021, 0.058, -0.045], [0.24, 0.019, 0.043, -0.034],
    [0.35, 0.016, 0.022, -0.014], [0.41, 0.020, 0.025, -0.010], [0.56, 0.019, 0.021, -0.010],
    [0.62, 0.017, 0.017, -0.012], [1.40, 0.015, 0.013, -0.012],
  ], hi ? 12 : 8, 3);
  // The barrel, tapering from the breech to the muzzle, sitting in the stock.
  cylinder(iron, 0.40, MUSKET.length_m, 0.0145, 0.0115, sides, 0, 0.006, true);
  // The lock plate and cock on the lock side, the trigger guard below, the butt plate.
  box(iron, [0.021, 0.49, -0.006], [0.0025, 0.07, 0.014]);
  box(iron, [0.025, 0.435, 0.014], [0.004, 0.013, 0.018]);
  box(iron, [0.0, 0.45, -0.036], [0.004, 0.05, 0.003]);
  box(iron, [0.0, 0.004, -0.050], [0.023, 0.004, 0.065]);
  // Three bands round barrel and stock.
  for (const y of [0.80, 1.07, 1.34]) cylinder(iron, y - 0.007, y + 0.007, 0.021, 0.020, sides, 0, -0.004, false);
  // The ramrod in its groove under the barrel.
  if (hi) cylinder(iron, 0.62, 1.505, 0.0045, 0.0045, 5, 0, -0.024, true);
  // The bayonet: its socket over the muzzle, the neck down to the blade, the blade itself
  // (a triangle in section) running on under and past the muzzle.
  cylinder(iron, 1.435, 1.512, 0.0138, 0.0138, sides, 0, 0.006, true);
  box(iron, [0, 1.495, -0.012], [0.004, 0.01, 0.017]);
  {
    const b = iron.position.length / 3, y0 = 1.49, y1 = y0 + MUSKET.bayonet_blade_m, z = -0.028;
    // three long faces from a triangular root (0.024 wide) to the point
    const root = [[0, y0, z + 0.006], [0.012, y0, z - 0.007], [-0.012, y0, z - 0.007]];
    const tip = [0, y1, z];
    for (let k = 0; k < 3; k++) {
      const a = root[k], c = root[(k + 1) % 3];
      const n = new THREE.Vector3().crossVectors(new THREE.Vector3(c[0] - a[0], 0, c[2] - a[2]), new THREE.Vector3(tip[0] - a[0], tip[1] - a[1], tip[2] - a[2])).normalize();
      const i = iron.position.length / 3;
      iron.position.push(...a, ...c, ...tip); iron.normal.push(n.x, n.y, n.z, n.x, n.y, n.z, n.x, n.y, n.z);
      iron.index.push(i, i + 1, i + 2);
    }
    void b;
  }
  // The sling, white buff, from the swivel on the middle band to the one before the guard,
  // hanging a little slack under the stock.
  if (hi) {
    const pts = [];
    for (let k = 0; k <= 8; k++) {
      const t = k / 8, y = 1.07 + (0.52 - 1.07) * t, z = -0.034 - 0.022 * Math.sin(Math.PI * t);
      pts.push([y, z]);
    }
    const base = buff.position.length / 3;
    for (const [y, z] of pts) for (const x of [-0.011, 0.011]) { buff.position.push(x, y, z); buff.normal.push(0, 0, -1); }
    for (let k = 0; k < pts.length - 1; k++) { const a = base + k * 2; buff.index.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
  }
  const out = { wood: geometryOf(wood), iron: geometryOf(iron), buff: buff.index.length ? geometryOf(buff) : null };
  musketCache.set(key, out);
  return out;
}

/** A musket as a group of meshes in its own frame. */
export function musketGroup(detail = 'hi') {
  const p = musketParts(detail);
  const g = new THREE.Group();
  g.name = 'garrison_musket';
  for (const [geo, m] of [[p.wood, 'walnut'], [p.iron, 'iron'], [p.buff, 'buff']]) {
    if (!geo) continue;
    const mesh = new THREE.Mesh(geo, material(m));
    mesh.name = `garrison_musket_${m}`;
    mesh.castShadow = true;
    g.add(mesh);
  }
  return g;
}

// ---------------------------------------------------------------------------------------------
// Carries. The hand's hold, in the figure's frame (+x his left, +y up, +z forward, metres from
// the shoulder joint), is human-actions.js's `carry`; `musket` places the musket in the same
// frame: its butt point (`at`, a point of the musket's own frame laid there), its axis and
// which way its lock turns.

export const CARRIES = Object.freeze({
  // Shouldered: the left arm hangs nearly straight, the hand under the butt, palm up; the
  // firelock rises in front of the hollow of the shoulder, the lock turned out.
  shoulder: Object.freeze({
    hold: { side: 'l', wrist_from_shoulder: [0.035, -0.455, 0.085], elbow_pole: [0.45, -0.1, -0.85], fingers: [-0.2, 0.05, 0.98], palm: [-0.4, 0.92, 0.0], curl: 0.55 },
    musket: { grip_from_wrist: [0.06, 0.03], at: [0, 0.015, MUSKET.butt_z], aim_from_shoulder: [-0.015, 0.02, 0.09], lock: [1, 0, 0] },
  }),
  // At the order: the right hand round the barrel at the side, the butt by the right toe.
  order: Object.freeze({
    hold: { side: 'r', wrist_from_shoulder: [-0.05, -0.49, 0.075], elbow_pole: [-0.55, -0.1, -0.8], fingers: [0.35, -0.12, 0.93], palm: [1, 0, 0.0], curl: 0.8 },
    musket: { grip_from_wrist: [0.075, 0.028], ground: true, axis: [0, 1, 0], lock: [-1, 0, 0] },
  }),
});

/** The carry human-actions.js holds the hand in for this garrison record, or null. */
export function garrisonCarry(garrison) {
  const c = CARRIES[garrison?.arms];
  return c ? { ...c.hold } : null;
}

const bone = (root, name) => {
  let found = null;
  root.traverse((o) => { if (!found && o.isBone && o.name === name) found = o; });
  return found;
};
/** A bone's rest matrix, root frame (the clone is in its bind pose when it is dressed). */
function restOf(root, b) {
  root.updateMatrixWorld(true);
  return new THREE.Matrix4().copy(root.matrixWorld).invert().multiply(b.matrixWorld);
}
const posOf = (root, name) => { const b = bone(root, name); return b ? new THREE.Vector3().setFromMatrixPosition(restOf(root, b)) : null; };

/** Hand axes as human-actions.js reads them, in the hand bone's own frame. */
function handAxes(hand, s) {
  const child = (n) => hand.children.find((c) => c.name === n) ?? null;
  const knuckle = child(`middle_01_${s}`), index = child(`index_01_${s}`), pinky = child(`pinky_01_${s}`);
  const along = knuckle ? knuckle.position.clone().normalize() : new THREE.Vector3(0, 1, 0);
  let palm = new THREE.Vector3(1, 0, 0);
  if (index && pinky) {
    const across = pinky.position.clone().sub(index.position);
    palm = s === 'r' ? along.clone().cross(across) : across.cross(along);
    if (palm.lengthSq() < 1e-10) palm.set(1, 0, 0);
    palm.addScaledVector(along, -palm.dot(along)).normalize();
  }
  return { along, palm };
}

/** Lay a musket in the carrying hand: a child of the hand bone, in the hold's hand frame. */
function carryMusket(root, carryName, detail) {
  const c = CARRIES[carryName];
  if (!c) return null;
  const s = c.hold.side, hand = bone(root, `hand_${s}`), up = posOf(root, `upperarm_${s}`);
  if (!hand || !up) return null;
  const V = (a) => new THREE.Vector3(...a);
  // The held hand's frame, figure frame: origin the wrist, axes fingers, palm, fingers x palm.
  const f = V(c.hold.fingers).normalize(), p0 = V(c.hold.palm);
  const p = p0.addScaledVector(f, -p0.dot(f)).normalize(), q = f.clone().cross(p);
  const wrist = up.clone().add(V(c.hold.wrist_from_shoulder));
  const H = new THREE.Matrix4().makeBasis(f, p, q).setPosition(wrist);
  const grip = wrist.clone().addScaledVector(f, c.musket.grip_from_wrist[0]).addScaledVector(p, c.musket.grip_from_wrist[1]);
  // The musket's axes, figure frame.
  let Y, anchor;
  if (c.musket.ground) {
    Y = V(c.musket.axis).normalize();
    // The barrel's centre is in the hand, at the height the grip is held above the ground.
    anchor = new THREE.Vector3(0, Math.max(0.6, grip.y - 0.012), 0.006);
  } else {
    Y = up.clone().add(V(c.musket.aim_from_shoulder)).sub(grip).normalize();
    anchor = V(c.musket.at);
  }
  const lockWant = V(c.musket.lock);
  const X = lockWant.addScaledVector(Y, -lockWant.dot(Y)).normalize();
  const Z = X.clone().cross(Y).normalize();   // right-handed: X x Y = Z
  const M = new THREE.Matrix4().makeBasis(X, Y, Z).setPosition(grip).multiply(new THREE.Matrix4().makeTranslation(-anchor.x, -anchor.y, -anchor.z));
  // Into the hand bone's frame: the hold turns the bone's own (along, palm) onto (f, p).
  const ax = handAxes(hand, s);
  const B = new THREE.Matrix4().makeBasis(ax.along, ax.palm, ax.along.clone().cross(ax.palm));
  const local = B.multiply(H.invert()).multiply(M);
  const g = musketGroup(detail);
  g.matrixAutoUpdate = false;
  g.matrix.copy(local);
  hand.add(g);
  return g;
}

// ---------------------------------------------------------------------------------------------
// Rank marks fitted to the wearer's own coat.

function coatSurface(root, re) {
  const pts = [];
  root.traverse((o) => {
    if (!o.isSkinnedMesh || !re.test(o.name)) return;
    for (const q of metricPoints(o, root)) pts.push(q);
  });
  return pts;
}

/**
 * An epaulette over shoulder `side` ('l' or 'r'), root frame, in two pieces: `shoulder`, a strap
 * from near the collar to the point of the shoulder lying on the coat and a crescent pad on the
 * point (worn on the collarbone), and `fringe`, hanging from the pad's rim over the top of the
 * arm (worn on the upper arm, so it drapes the arm as it hangs and swings with it). Built in the
 * T-pose: the arm lies along x there, so the fringe is a half-sleeve over the arm's top, which
 * is its outer side once the arm hangs. `kind` 'worsted' (an NCO's white wool, a short fringe)
 * or 'bullion' (an officer's silver, a longer one).
 */
function epaulettePart(root, side, kind, coat) {
  const sign = side === 'l' ? 1 : -1;
  const joint = posOf(root, `upperarm_${side}`), neck = posOf(root, 'neck_01');
  if (!joint || !neck) return null;
  // The sleeve's radius round the arm near the joint (T-pose: the arm along x).
  let r = 0;
  for (const [x, y, z] of coat) {
    const s = (x - joint.x) * sign;
    if (s > 0.02 && s < 0.05) r = Math.max(r, Math.hypot(y - joint.y, z - joint.z));
  }
  if (!(r > 0.04 && r < 0.11)) r = 0.062;
  // The coat's top along the shoulder line; the standing collar is not the shoulder.
  const capY = joint.y + 0.12;
  const topAt = (x, z) => {
    let best = -Infinity;
    for (const [px, py, pz] of coat) if (Math.abs(px - x) < 0.014 && Math.abs(pz - z) < 0.03 && py > neck.y - 0.2 && py < capY) best = Math.max(best, py);
    return Number.isFinite(best) ? best : joint.y + r;
  };
  const bullion = kind === 'bullion';
  const w = bullion ? 0.025 : 0.022, t = 0.004;
  // Stood clear of the coat as it lies posed: the shoulder rises ~1 cm off the T-pose as the arm
  // hangs, and these ride the collarbone, not the sleeve.
  const lift = 0.013;
  const shoulder = part();
  const zc = joint.z + 0.004;
  // The strap: from 0.42 of the way from the neck to the pad's inner end.
  const padIn = joint.x - sign * 0.04, padOut = joint.x + sign * 0.014;
  const strap = part();
  const n = 6, x0 = neck.x + (joint.x - neck.x) * 0.42, x1 = padIn;
  for (let k = 0; k < n; k++) {
    const x = x0 + (x1 - x0) * (k / (n - 1)), y = topAt(x, zc) + lift;
    for (const [dz, dy, nz, ny] of [[-w, -t, -1, 0], [-w, 0, 0, 1], [w, 0, 0, 1], [w, -t, 1, 0]]) {
      strap.position.push(x, y + dy, zc + dz); strap.normal.push(0, ny, nz);
    }
  }
  for (let k = 0; k < n - 1; k++) for (let j = 0; j < 3; j++) {
    const a = k * 4 + j, b = a + 1, c = a + 4, d = b + 4;
    // Wound to face out on either side (the strap runs toward the joint, +x left, -x right).
    if (sign > 0) strap.index.push(a, b, c, b, d, c); else strap.index.push(a, c, b, b, c, d);
  }
  append(shoulder, strap);
  // The pad: an oval cushion over the point of the shoulder, following the coat's slope.
  const pw = bullion ? 0.052 : 0.046, pu = Math.abs(padOut - padIn) / 2, pcx = (padIn + padOut) / 2;
  const pad = part(), seg = 18, rings = 4;
  const rimY = [];
  for (let i = 0; i <= rings; i++) {
    const ring = i / rings, dome = Math.sqrt(Math.max(0, 1 - ring * ring)) * 0.007;
    for (let s = 0; s < seg; s++) {
      const th = (s / seg) * Math.PI * 2;
      const x = pcx + Math.cos(th) * pu * ring, z = zc + Math.sin(th) * pw * ring;
      const y = topAt(Math.abs(x - joint.x) < 0.01 ? joint.x - sign * 0.01 : x, z) + lift + 0.002 + dome;
      pad.position.push(x, y, z);
      pad.normal.push(Math.cos(th) * ring * 0.5, 1, Math.sin(th) * ring * 0.5);
      if (i === rings) rimY.push(y);
    }
  }
  for (let i = 0; i < rings; i++) for (let s = 0; s < seg; s++) {
    const a = i * seg + s, b = i * seg + (s + 1) % seg;
    pad.index.push(a, b, a + seg, b, b + seg, a + seg);
  }
  append(shoulder, pad);
  // The fringe: round the top half of the arm (front, outer, back once it hangs), from a little
  // inboard of the joint, under the pad's rim, out along the arm, flaring as it falls.
  const L = bullion ? 0.085 : 0.065, R = Math.max(r, 0.068) + 0.01;
  const fringe = part(), fs = 16, p0 = -105 * DEG, p1 = 105 * DEG;
  for (let s = 0; s <= fs; s++) {
    const ph = p0 + (p1 - p0) * (s / fs), cy = Math.cos(ph), sz = Math.sin(ph);
    for (const [along, k] of [[-0.045, 1.0], [-0.045 + L, 1.2]]) {
      fringe.position.push(joint.x + sign * along, joint.y + cy * R * k, zc + sz * R * k);
      fringe.normal.push(0, cy, sz);
    }
  }
  for (let s = 0; s < fs; s++) {
    const a = s * 2;
    if (sign > 0) fringe.index.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); else fringe.index.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
  }
  return { shoulder, fringe };
}

/** A sash round the waist over the coat, knotted at the left hip with two ends hanging. */
function sashPart(root, coat) {
  const pelvis = posOf(root, 'pelvis'), spine = posOf(root, 'spine_01');
  if (!pelvis || !spine) return null;
  const yc = pelvis.y + (spine.y - pelvis.y) * 0.95 + 0.02, h = 0.036;
  const cx = pelvis.x, cz = (pelvis.z + spine.z) / 2;
  const bins = 28, rad = new Array(bins).fill(0);
  for (const [x, y, z] of coat) {
    if (Math.abs(y - yc) > h + 0.01) continue;
    const a = Math.atan2(z - cz, x - cx), b = ((Math.round((a / (2 * Math.PI)) * bins) % bins) + bins) % bins;
    rad[b] = Math.max(rad[b], Math.hypot(x - cx, z - cz));
  }
  // Fill any empty bin from its neighbours, and stand off the coat.
  for (let k = 0; k < bins; k++) if (!(rad[k] > 0.08)) rad[k] = Math.max(rad[(k + bins - 1) % bins], rad[(k + 1) % bins], 0.15);
  const out = part();
  const base = 0;
  for (const [y, bulge] of [[yc - h, 0.004], [yc - h * 0.35, 0.009], [yc + h * 0.35, 0.009], [yc + h, 0.004]]) {
    for (let k = 0; k < bins; k++) {
      const a = (k / bins) * Math.PI * 2, r = rad[k] + 0.006 + bulge;
      out.position.push(cx + r * Math.cos(a), y, cz + r * Math.sin(a)); out.normal.push(Math.cos(a), 0, Math.sin(a));
    }
  }
  for (let row = 0; row < 3; row++) for (let k = 0; k < bins; k++) {
    const a = base + row * bins + k, b = base + row * bins + (k + 1) % bins;
    out.index.push(a, a + bins, b, b, a + bins, b + bins);
  }
  // The knot and the ends, at the left hip a little forward (+x left, +z forward).
  const ka = 18 * DEG, kr = rad[Math.round((ka / (2 * Math.PI)) * bins) % bins] + 0.02;
  const kx = cx + kr * Math.cos(ka), kz = cz + kr * Math.sin(ka);
  const knot = part();
  box(knot, [kx, yc - 0.005, kz], [0.025, 0.03, 0.018]);
  append(out, knot);
  for (const [dx, len] of [[-0.018, 0.27], [0.02, 0.32]]) {
    const end = part(), wEnd = 0.028;
    const n = 6;
    for (let k = 0; k <= n; k++) {
      const tt = k / n, y = yc - 0.02 - len * tt, out2 = 0.006 + 0.02 * tt;
      for (const sx of [-wEnd, wEnd]) {
        end.position.push(kx + dx + sx * 0.4 + out2 * Math.cos(ka), y, kz + sx * 0.9 + out2 * Math.sin(ka));
        end.normal.push(Math.cos(ka), 0, Math.sin(ka));
      }
    }
    for (let k = 0; k < n; k++) { const a = k * 2; end.index.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    append(out, end);
  }
  return out;
}

/** A part in the root frame onto bone `name`, as a child mesh. */
function onBone(root, name, p, mat, label) {
  const b = bone(root, name);
  if (!b || !p) return null;
  const inv = restOf(root, b).invert();
  transformPart(p, inv);
  const mesh = new THREE.Mesh(geometryOf(p), material(mat));
  mesh.name = label;
  mesh.castShadow = true;
  b.add(mesh);
  return mesh;
}

// ---------------------------------------------------------------------------------------------
// The drum and the fife case, shared per level of detail.

const drumCache = new Map();
function drumParts(detail) {
  if (drumCache.has(detail)) return drumCache.get(detail);
  const hi = detail === 'hi', sides = hi ? 24 : 12;
  const R = 0.2, H = 0.38;
  const shell = part(), hoop = part(), head = part(), cord = part();
  cylinder(shell, -H / 2 + 0.03, H / 2 - 0.03, R, R, sides, 0, 0, false);
  cylinder(hoop, -H / 2, -H / 2 + 0.042, R + 0.008, R + 0.008, sides, 0, 0, false);
  cylinder(hoop, H / 2 - 0.042, H / 2, R + 0.008, R + 0.008, sides, 0, 0, false);
  cylinder(head, -H / 2 + 0.004, H / 2 - 0.004, R + 0.002, R + 0.002, sides, 0, 0, true);
  head.index.splice(0, sides * 6);   // the heads only: drop the side
  if (hi) {
    // The tension cords zig-zag between the hoops.
    const n = 10;
    for (let k = 0; k < n * 2; k++) {
      const a0 = (k / (n * 2)) * Math.PI * 2, a1 = ((k + 1) / (n * 2)) * Math.PI * 2;
      const [y0, y1] = k % 2 ? [H / 2 - 0.042, -H / 2 + 0.042] : [-H / 2 + 0.042, H / 2 - 0.042];
      const b = cord.position.length / 3, r = R + 0.004, wdt = 0.006;
      const p0 = [r * Math.cos(a0), y0, r * Math.sin(a0)], p1 = [r * Math.cos(a1), y1, r * Math.sin(a1)];
      cord.position.push(p0[0], p0[1] - wdt, p0[2], p0[0], p0[1] + wdt, p0[2], p1[0], p1[1] - wdt, p1[2], p1[0], p1[1] + wdt, p1[2]);
      for (const a of [a0, a0, a1, a1]) cord.normal.push(Math.cos(a), 0, Math.sin(a));
      cord.index.push(b, b + 2, b + 1, b + 1, b + 2, b + 3);
    }
  }
  const out = { shell: geometryOf(shell), hoop: geometryOf(hoop), head: geometryOf(head), cord: cord.index.length ? geometryOf(cord) : null };
  drumCache.set(detail, out);
  return out;
}

function drumGroup(detail) {
  const p = drumParts(detail), g = new THREE.Group();
  g.name = 'garrison_drum';
  for (const [geo, m] of [[p.shell, 'drum_shell'], [p.hoop, 'drum_hoop'], [p.head, 'drum_head'], [p.cord, 'cord_white']]) {
    if (!geo) continue;
    const mesh = new THREE.Mesh(geo, material(m)); mesh.name = `garrison_drum_${m}`; mesh.castShadow = true; g.add(mesh);
  }
  return g;
}

const fifeCache = new Map();
function fifeCase(detail) {
  if (!fifeCache.has(detail)) { const p = part(); cylinder(p, -0.21, 0.21, 0.02, 0.02, detail === 'hi' ? 10 : 6); fifeCache.set(detail, geometryOf(p)); }
  const mesh = new THREE.Mesh(fifeCache.get(detail), material('black_leather'));
  mesh.name = 'garrison_fife_case'; mesh.castShadow = true;
  return mesh;
}

/** A shared object placed on bone `name` with its transform given in the root frame. */
function placeOnBone(root, name, object, rootMatrix) {
  const b = bone(root, name);
  if (!b) return null;
  object.matrixAutoUpdate = false;
  object.matrix.copy(restOf(root, b).invert().multiply(rootMatrix));
  b.add(object);
  return object;
}

// ---------------------------------------------------------------------------------------------

/**
 * Dress one cloned (and varied) figure of the garrison by its record (`garrison`: rank, marks,
 * carry, arms). Call after the variation, like dressSpectacles. Returns { meshes, owned } —
 * `owned` the geometries made for this wearer alone, to dispose with the level.
 */
export function dressGarrison(root, garrison, { lod = 0 } = {}) {
  if (!root || !garrison) return null;
  const detail = lod <= 1 ? 'hi' : 'lo';
  const meshes = [], owned = [];
  const keep = (m) => { if (m) { meshes.push(m); if (m.isMesh && m.geometry && !isShared(m.geometry)) owned.push(m.geometry); } return m; };
  const marks = Array.isArray(garrison.marks) ? garrison.marks : [];
  const coatRe = /(coat_body|coat_collar|coat_tails|coat_skirts)(_lod\d+)?$/;
  let coat = null;
  const coatPts = () => (coat ??= coatSurface(root, coatRe));
  for (const mark of marks) {
    const m = /^epaulette_(worsted|bullion)_(l|r)$/.exec(mark);
    if (m) {
      const ep = epaulettePart(root, m[2], m[1], coatPts()), mat = m[1] === 'bullion' ? 'silver' : 'worsted_white';
      keep(onBone(root, `clavicle_${m[2]}`, ep?.shoulder, mat, `garrison_${mark}`));
      keep(onBone(root, `upperarm_${m[2]}`, ep?.fringe, mat, `garrison_${mark}_fringe`));
      continue;
    }
    if (mark === 'sash_crimson') keep(onBone(root, 'pelvis', sashPart(root, coatPts()), 'crimson_silk', 'garrison_sash'));
  }
  const pelvis = posOf(root, 'pelvis');
  if (garrison.carry === 'drum' && pelvis) {
    // On the left thigh, tilted (the top head toward the drummer's right), on its carriage.
    const m = new THREE.Matrix4().makeTranslation(pelvis.x + 0.15, pelvis.y - 0.27, pelvis.z + 0.17)
      .multiply(new THREE.Matrix4().makeRotationZ(62 * DEG)).multiply(new THREE.Matrix4().makeRotationX(-12 * DEG));
    const g = placeOnBone(root, 'pelvis', drumGroup(detail), m);
    if (g) meshes.push(g);
  } else if (garrison.carry === 'fife' && pelvis) {
    const m = new THREE.Matrix4().makeTranslation(pelvis.x - 0.17, pelvis.y - 0.12, pelvis.z - 0.03).multiply(new THREE.Matrix4().makeRotationX(-14 * DEG));
    const g = placeOnBone(root, 'pelvis', fifeCase(detail), m);
    if (g) meshes.push(g);
  }
  if (CARRIES[garrison.arms]) {
    const g = carryMusket(root, garrison.arms, detail);
    if (g) meshes.push(g);
  }
  return { meshes, owned };
}

function isShared(geo) {
  for (const c of [musketCache, drumCache]) for (const v of c.values()) if (Object.values(v).includes(geo)) return true;
  for (const v of fifeCache.values()) if (v === geo) return true;
  return false;
}

// ---------------------------------------------------------------------------------------------
// Piled arms: muskets stood butt-down in a ring and leaning in, their bayonets crossed and
// locked above, where men are at work out of the fort. A garrison record's `pile`
// ({ local_e, local_n, heading_deg, count }) puts one in the scene.

/** The pile as a group, its foot at the origin, +Y up. */
export function armsPileGroup(count = 3, detail = 'hi') {
  const g = new THREE.Group();
  g.name = 'garrison_arms_pile';
  const n = Math.max(2, Math.min(6, count | 0)), r = 0.42, reach = 1.13;
  const h = Math.sqrt(reach * reach - r * r);
  for (let k = 0; k < n; k++) {
    const a = (k / n) * Math.PI * 2;
    const butt = new THREE.Vector3(r * Math.cos(a), 0.0, r * Math.sin(a));
    const apex = new THREE.Vector3(0.012 * Math.cos(a + 1.3), h, 0.012 * Math.sin(a + 1.3));
    const Y = apex.clone().sub(butt).normalize();
    // The lock turned out, the barrel in toward the others.
    const out = new THREE.Vector3(Math.cos(a), 0, Math.sin(a));
    const Z = out.clone().negate().addScaledVector(Y, out.dot(Y)).normalize();
    const X = Y.clone().cross(Z).normalize();
    const m = musketGroup(detail);
    m.matrixAutoUpdate = false;
    m.matrix.makeBasis(X, Y, Z).setPosition(butt.clone().add(new THREE.Vector3(0, 0.03, 0)))
      .multiply(new THREE.Matrix4().makeTranslation(0, 0, -MUSKET.butt_z));
    g.add(m);
  }
  return g;
}

/**
 * Stand every pile the drawn garrison's records name into `group`, on the ground. `persons`
 * the variation persons file's records; `ids` the person ids drawn in this scene; `toWorld`
 * (e, n, h) → THREE.Vector3; `heightAt` (e, n) → metres.
 */
export function createArmsPiles({ group, persons, ids, sceneId, toWorld, heightAt }) {
  const made = [];
  for (const id of ids) {
    const pile = persons?.[id]?.dress?.garrison?.pile;
    if (!pile || (pile.scene && String(pile.scene) !== String(sceneId))) continue;
    const { local_e: e, local_n: n } = pile;
    if (!Number.isFinite(e) || !Number.isFinite(n)) continue;
    const g = armsPileGroup(pile.count ?? 3, 'hi');
    g.position.copy(toWorld(e, n, heightAt(e, n)));
    g.rotation.y = -((pile.heading_deg ?? 0) * DEG);
    g.name = `garrison_arms_pile_${id}`;
    group.add(g);
    made.push(g);
  }
  return made;
}
