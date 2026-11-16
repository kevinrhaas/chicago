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
