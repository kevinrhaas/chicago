// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553: small things a jaunt stage's people handle (jaunt-stage.js). A bier: two carrying
 * poles and a bed of plank under a grey blanket, long along local +z and centred on the origin,
 * its bed's top at y 0. The owner, 2026-11-16, of the murder jaunt's grave: "they should be
 * carrying the body by hand". Its make is reconstructed (L-1812-staged-jaunts-3553): no account
 * says what Lalime was carried on.
 */
import * as THREE from 'three';

const POLE_M = 2.6, POLE_R = 0.024, POLE_X = 0.3, BED_L = 1.95, BED_W = 0.56;
let shared = null;

function parts() {
  if (shared) return shared;
  shared = {
    pole: new THREE.CylinderGeometry(POLE_R, POLE_R, POLE_M, 8).rotateX(Math.PI / 2),
    bed: new THREE.BoxGeometry(BED_W, 0.035, BED_L),
    cloth: new THREE.BoxGeometry(BED_W + 0.08, 0.012, BED_L - 0.1),
    wood: new THREE.MeshStandardMaterial({ color: 0x6b5338, roughness: 0.9 }),
    blanket: new THREE.MeshStandardMaterial({ color: 0x77736a, roughness: 1 }),
  };
  return shared;
}

/** A bier, ready to be placed. */
export function createBier() {
  const p = parts(), g = new THREE.Group();
  g.name = 'jaunt-stage-bier';
  for (const side of [-1, 1]) {
    const pole = new THREE.Mesh(p.pole, p.wood);
    pole.position.set(side * POLE_X, -0.03, 0);
    g.add(pole);
  }
  const bed = new THREE.Mesh(p.bed, p.wood);
  bed.position.y = -0.035;
  g.add(bed);
  const cloth = new THREE.Mesh(p.cloth, p.blanket);
  cloth.position.y = -0.012;
  g.add(cloth);
  g.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return g;
}

/**
 * T-3814: the goods the people of the Great Fire carried out of its way, a jaunt stage's
 * castmates carry (`carry`), a staged team's bed is heaped with (`load`), or that stand on the
 * ground (`props`). The accounts list them (docs/RESEARCH/fire-night-scenes-3814): "some with
 * bundles of clothing on their shoulders; others, dragging trunks along the sidewalk by means of
 * strings and ropes fastened to the handles" (Andreas II, p. 734); "numbers had canary birds in
 * cages", "on his back was a huge feather bed" (p. 746); "a sick man or women ... half concealed
 * in a mattress doubled up and borne by two men" (p. 734); men "carrying goods out of the lower
 * floor into wagons" at Field, Leiter and Co.'s (Colbert and Chamberlin). Their make is
 * reconstructed (L-1871-fire-night-3814): the period's ordinary kinds, in plain boxes and
 * cylinders, shared across every copy.
 *
 * Each kind says how it is carried (`mode`): `hand` hangs from the grip of the held hand,
 * `shoulder` lies over the shoulder with that hand up holding it, `back` rides across the
 * shoulders, `drag` is pulled along the ground on a cord from the hand behind. `hold` is the
 * arm's hold (human-actions.js setCarry: figure frame, metres from the shoulder joint; +x the
 * figure's left, +y up, +z ahead).
 */
const GOODS_RGB = {
  calico: 0x8a5a48, shawl: 0x4a4f63, linen: 0xc8c2b0, ticking: 0xbab3a0, stripe: 0x5a6378, leather: 0x4d3423,
  trunkPaint: 0x3f4a3a, iron: 0x2b2b2b, brass: 0x8f7a3a, wicker: 0x9a7d4f, wood: 0x6b5338, walnut: 0x5c3d26,
  paper: 0xd8d2c0, twine: 0x8c7a58, cloth1: 0x6a2e2e, cloth2: 0x2f3e57, cloth3: 0x7a6a4a, cord: 0x7a6a50,
  oak: 0x7a5a36, blanket: 0xd9d2bf, stroud: 0x7d2a24, dark: 0x0e0d0c, stone: 0x6e6a60,
};
let goodsShared = null;
function goodsParts() {
  if (goodsShared) return goodsShared;
  const mat = {};
  for (const [k, c] of Object.entries(GOODS_RGB)) mat[k] = new THREE.MeshStandardMaterial({ color: c, roughness: k === 'brass' || k === 'iron' ? 0.55 : 0.92, metalness: k === 'brass' ? 0.4 : k === 'iron' ? 0.3 : 0 });
  goodsShared = { mat, box: new THREE.BoxGeometry(1, 1, 1), cyl: new THREE.CylinderGeometry(0.5, 0.5, 1, 10), ball: new THREE.IcosahedronGeometry(0.5, 1),
    bar: new THREE.CylinderGeometry(0.5, 0.5, 1, 4) };
  return goodsShared;
}
/** A part: `geo` box|cyl|ball|bar, scaled to (w, h, d), its centre at (x, y, z), turned (rx, ry, rz). */
function gp(g, geo, mat, [w, h, d], [x, y, z], [rx, ry, rz] = [0, 0, 0]) {
  const p = goodsParts(), m = new THREE.Mesh(p[geo], p.mat[mat]);
  m.scale.set(w, h, d); m.position.set(x, y, z); m.rotation.set(rx, ry, rz);
  g.add(m);
  return m;
}
// The holds (figure frame, from the shoulder joint), tuned on the stage's figures.
const HAND_L = { side: 'l', wrist_from_shoulder: [0.205, -0.39, 0.05], elbow_pole: [0.7, -0.1, -0.7], fingers: [0.10, -1, 0.06], palm: [-1, 0, 0], curl: 0.75 };
const HAND_R = { side: 'r', wrist_from_shoulder: [-0.205, -0.39, 0.05], elbow_pole: [-0.7, -0.1, -0.7], fingers: [-0.10, -1, 0.06], palm: [1, 0, 0], curl: 0.75 };
const SHOULDER_R = { side: 'r', wrist_from_shoulder: [0.06, 0.1, 0.16], elbow_pole: [-0.55, -0.75, 0.35], fingers: [0.15, 0.45, -0.88], palm: [0.25, -0.2, -0.95], curl: 0.85 };
const DRAG_R = { side: 'r', wrist_from_shoulder: [-0.16, -0.5, -0.14], elbow_pole: [-0.6, 0, 0.8], fingers: [0, -1, -0.15], palm: [0.9, 0, -0.3], curl: 0.9 };

/** A keg lying along its axis (y before turning), 0.44 m long: oak staves and two iron hoops. */
function keg(g, at, rot) {
  const k = new THREE.Group(); k.position.set(...at); k.rotation.set(...rot); g.add(k);
  gp(k, 'cyl', 'oak', [0.34, 0.44, 0.34], [0, 0, 0]);
  gp(k, 'cyl', 'oak', [0.38, 0.2, 0.38], [0, 0, 0]);                    // the belly
  for (const y of [-0.17, 0.17]) gp(k, 'cyl', 'iron', [0.36, 0.025, 0.36], [0, y, 0]);
  return k;
}
/** A musket lying along -z from `at` (its butt at +z), turned up by `tilt` about x. */
function musket(g, at, tilt = 0) {
  const m = new THREE.Group(); m.position.set(...at); m.rotation.set(tilt, 0, 0); g.add(m);
  gp(m, 'box', 'walnut', [0.045, 0.1, 0.62], [0, -0.02, 0.32]);
  gp(m, 'cyl', 'iron', [0.022, 0.95, 0.022], [0, 0.02, -0.45], [Math.PI / 2, 0, 0]);
  return m;
}

/** How each kind is carried, and how it is made (its origin: the grip for `hand`, the shoulder's
 *  top for `shoulder`, the middle of the back for `back`, the front of its bottom for `drag`). */
export const GOODS = Object.freeze({
  bundle: { mode: 'shoulder', hold: SHOULDER_R, make(g) {
    gp(g, 'ball', 'calico', [0.48, 0.34, 0.42], [0, 0.12, -0.16]);
    gp(g, 'ball', 'calico', [0.12, 0.1, 0.12], [0, 0.1, 0.1]);          // the knot over the shoulder
  } },
  shawl_bundle: { mode: 'hand', hold: HAND_L, make(g) {
    gp(g, 'ball', 'shawl', [0.42, 0.3, 0.3], [0, -0.2, 0]);
    gp(g, 'ball', 'shawl', [0.1, 0.12, 0.1], [0, -0.02, 0]);
  } },
  birdcage: { mode: 'hand', hold: HAND_L, make(g) {
    gp(g, 'cyl', 'wood', [0.24, 0.03, 0.24], [0, -0.36, 0]);
    for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2; gp(g, 'bar', 'brass', [0.006, 0.28, 0.006], [Math.sin(a) * 0.11, -0.22, Math.cos(a) * 0.11]); }
    gp(g, 'ball', 'brass', [0.24, 0.12, 0.24], [0, -0.08, 0]);
    gp(g, 'cyl', 'brass', [0.012, 0.05, 0.012], [0, -0.01, 0]);
    gp(g, 'ball', 'paper', [0.05, 0.05, 0.07], [0, -0.28, 0.02]);        // the canary
  } },
  basket: { mode: 'hand', hold: HAND_L, make(g) {
    gp(g, 'box', 'wicker', [0.4, 0.2, 0.28], [0, -0.3, 0]);
    gp(g, 'box', 'linen', [0.36, 0.05, 0.24], [0, -0.18, 0]);
    gp(g, 'cyl', 'wicker', [0.02, 0.18, 0.02], [0.17, -0.1, 0], [0, 0, 0.5]);
    gp(g, 'cyl', 'wicker', [0.02, 0.18, 0.02], [-0.17, -0.1, 0], [0, 0, -0.5]);
  } },
  papers: { mode: 'hand', hold: HAND_R, make(g) {
    gp(g, 'box', 'paper', [0.12, 0.42, 0.32], [0, -0.24, 0]);
    gp(g, 'box', 'twine', [0.13, 0.012, 0.33], [0, -0.18, 0]);
    gp(g, 'box', 'twine', [0.13, 0.43, 0.012], [0, -0.24, 0]);
  } },
  bolt: { mode: 'shoulder', hold: SHOULDER_R, make(g) {
    gp(g, 'box', 'cloth1', [0.34, 0.16, 1.05], [0, 0.05, -0.2], [0.18, 0, 0]);
  } },
  bolt_blue: { mode: 'shoulder', hold: SHOULDER_R, make(g) {
    gp(g, 'box', 'cloth2', [0.34, 0.16, 1.05], [0, 0.05, -0.2], [0.18, 0, 0]);
  } },
  featherbed: { mode: 'back', hold: null, make(g) {
    gp(g, 'cyl', 'ticking', [0.42, 0.95, 0.42], [0, 0.12, -0.22], [0, 0, Math.PI / 2]);
    for (const x of [-0.3, 0, 0.3]) gp(g, 'cyl', 'stripe', [0.43, 0.04, 0.43], [x, 0.12, -0.22], [0, 0, Math.PI / 2]);
    gp(g, 'box', 'cord', [0.02, 0.5, 0.02], [0.18, -0.02, -0.04], [0.5, 0, 0]);
  } },
  // T-3553 (the owner, 2026-11-28, 1812): "the fort dearborn people should be carrying goods out of
  // the factor and piling them ... and also the soldiers are carrying and dumping arms and whiskey
  // out the sally port". A keg (powder or whiskey), an armful of muskets, a bale of trade blankets,
  // each on the shoulder. Reconstructed make (L-1812-staged-jaunts-3553).
  keg: { mode: 'shoulder', hold: SHOULDER_R, make(g) { keg(g, [0, 0.16, -0.06], [Math.PI / 2 - 0.15, 0, 0]); } },
  muskets: { mode: 'shoulder', hold: SHOULDER_R, make(g) {
    for (const x of [-0.05, 0, 0.05]) musket(g, [x, 0.05 + Math.abs(x) * 0.4, -0.1], 0.2);
  } },
  blanket_bale: { mode: 'shoulder', hold: SHOULDER_R, make(g) {
    gp(g, 'box', 'blanket', [0.44, 0.24, 0.62], [0, 0.11, -0.16], [0.15, 0, 0]);
    for (const z of [-0.36, 0.04]) gp(g, 'box', 'stroud', [0.45, 0.25, 0.05], [0, 0.11, z], [0.15, 0, 0]);
  } },
  trunk: { mode: 'drag', hold: DRAG_R, make(g) {
    gp(g, 'box', 'trunkPaint', [0.52, 0.42, 0.8], [0, 0.23, -0.4]);
    gp(g, 'box', 'trunkPaint', [0.54, 0.08, 0.82], [0, 0.46, -0.4]);
    for (const z of [-0.12, -0.68]) gp(g, 'box', 'iron', [0.54, 0.44, 0.03], [0, 0.24, z]);
    gp(g, 'box', 'leather', [0.12, 0.03, 0.04], [0, 0.32, 0.01]);       // the handle the cord is tied to
  } },
});
/** Ground props and wagon loads (not carried). */
const STILL = Object.freeze({
  chair: (g) => {
    gp(g, 'box', 'walnut', [0.42, 0.04, 0.4], [0, 0.45, 0]);
    for (const [x, z] of [[-0.18, -0.17], [0.18, -0.17], [-0.18, 0.17], [0.18, 0.17]]) gp(g, 'box', 'walnut', [0.035, 0.45, 0.035], [x, 0.225, z]);
    gp(g, 'box', 'walnut', [0.42, 0.45, 0.035], [0, 0.68, -0.18]);
  },
  trunk: (g) => { GOODS.trunk.make(g); g.children.forEach((c) => { c.position.z += 0.4; }); },
  bundle: (g) => { gp(g, 'ball', 'calico', [0.5, 0.32, 0.42], [0, 0.15, 0]); },
  shawl_bundle: (g) => { gp(g, 'ball', 'shawl', [0.46, 0.3, 0.36], [0, 0.14, 0]); },
  featherbed: (g) => { gp(g, 'cyl', 'ticking', [0.44, 1.0, 0.44], [0, 0.2, 0], [0, 0, Math.PI / 2]); },
  // T-3553, 1812: the factory's goods piled on the grass, the powder and whiskey kegs, the well
  // in the sally port the muskets went down, and a keg with its head knocked in at the river.
  keg: (g) => { keg(g, [0, 0.22, 0], [0, 0, 0]); },
  keg_staved: (g) => {
    keg(g, [0, 0.22, 0], [0, 0, 0]);
    gp(g, 'cyl', 'dark', [0.3, 0.01, 0.3], [0, 0.445, 0]);                // the open head, the keg empty
    gp(g, 'cyl', 'oak', [0.32, 0.02, 0.32], [0.42, 0.012, 0.1], [0, 0, 0.08]);   // the head knocked in, on the ground
  },
  muskets: (g) => { for (const x of [-0.12, -0.04, 0.04, 0.12]) musket(g, [x, 0.05, 0], 0.02); },
  blanket_bale: (g) => {
    gp(g, 'box', 'blanket', [0.46, 0.26, 0.64], [0, 0.13, 0]);
    for (const z of [-0.2, 0.2]) gp(g, 'box', 'stroud', [0.47, 0.27, 0.05], [0, 0.13, z]);
  },
  bolt: (g) => { gp(g, 'box', 'cloth1', [0.34, 0.16, 1.05], [0, 0.08, 0]); },
  bolt_blue: (g) => { gp(g, 'box', 'cloth2', [0.34, 0.16, 1.05], [0, 0.08, 0]); },
  well: (g) => {
    for (let i = 0; i < 10; i++) {
      const a = (i / 10) * Math.PI * 2;
      gp(g, 'box', 'oak', [0.34, 0.5, 0.12], [Math.sin(a) * 0.52, 0.25, Math.cos(a) * 0.52], [0, a, 0]);
    }
    gp(g, 'cyl', 'dark', [0.98, 0.02, 0.98], [0, 0.4, 0]);
  },
  /** A load of a store's dry goods on a wagon bed (bolts and cases), its origin on the bed's top. */
  load_dry_goods: (g) => {
    gp(g, 'box', 'wood', [0.8, 0.45, 0.6], [0, 0.225, 0.75]);
    gp(g, 'box', 'wood', [0.7, 0.4, 0.55], [0.05, 0.65, 0.7]);
    const rolls = ['cloth1', 'cloth2', 'cloth3', 'linen', 'cloth2', 'cloth1'];
    rolls.forEach((k, i) => gp(g, 'box', k, [0.32, 0.15, 1.0], [(i % 3 - 1) * 0.3, 0.08 + Math.floor(i / 3) * 0.16, -0.45]));
    gp(g, 'box', 'cloth3', [0.32, 0.15, 1.0], [0.15, 0.4, -0.4]);
  },
  /** A family's goods on a wagon bed: trunks, a bureau, a mattress, bundles, a chair on top. */
  load_household: (g) => {
    gp(g, 'box', 'trunkPaint', [0.5, 0.42, 0.78], [-0.2, 0.21, 0.6]);
    gp(g, 'box', 'leather', [0.48, 0.38, 0.7], [0.22, 0.19, 0.5]);
    gp(g, 'box', 'walnut', [0.85, 0.7, 0.45], [0, 0.35, -0.35]);
    gp(g, 'box', 'ticking', [0.9, 0.12, 1.8], [0, 0.78, 0.05], [0.04, 0, 0]);
    gp(g, 'ball', 'calico', [0.45, 0.3, 0.4], [-0.2, 0.98, 0.5]);
    gp(g, 'ball', 'shawl', [0.42, 0.28, 0.36], [0.22, 0.97, -0.2]);
  },
});

/** A carried thing of `kind` (GOODS), or a still one (a ground prop or a wagon load), ready to be
 *  placed; null for a kind there is none of. Its meshes share one geometry and material set. */
export function createGoods(kind, { still = false } = {}) {
  const spec = still ? (STILL[kind] ? { make: STILL[kind] } : null) : GOODS[kind];
  if (!spec) return null;
  const g = new THREE.Group();
  g.name = `jaunt-stage-goods:${kind}`;
  spec.make(g);
  g.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return g;
}
export const STILL_GOODS = Object.freeze(Object.keys(STILL));

/** The cord a dragged trunk is pulled by: a thin line from the hand to the handle, set each frame. */
export function createCord() {
  const p = goodsParts(), m = new THREE.Mesh(p.cyl, p.mat.cord);
  m.name = 'jaunt-stage-cord';
  m.scale.set(0.012, 1, 0.012);
  return m;
}

/**
 * The doubled mattress a sick man or woman was carried in (Andreas II, p. 734): borne as the
 * bier is (its bed's top at y 0, long along +z), its foot half folded up and over them.
 */
export function createMattress() {
  const g = new THREE.Group();
  g.name = 'jaunt-stage-mattress';
  gp(g, 'box', 'ticking', [0.62, 0.11, 1.95], [0, -0.055, 0]);
  for (const z of [-0.6, 0, 0.6]) gp(g, 'box', 'stripe', [0.63, 0.112, 0.05], [0, -0.055, z]);
  gp(g, 'box', 'ticking', [0.6, 0.1, 0.95], [0, 0.34, -0.45], [0.06, 0, 0]);   // the half folded over
  gp(g, 'box', 'ticking', [0.6, 0.36, 0.1], [0, 0.15, -0.94]);                 // the fold at the foot
  g.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return g;
}
