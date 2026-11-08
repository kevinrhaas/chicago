// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-looks.js — a person's own complexion and eye colour (T-3491).
 *
 * The owner, 2026-11-07, of the 1812 garrison: *"they all have the same complexion and hair so
 * change all that up"*. Every drawn body shares one skin picture and one iris picture, so until
 * this every man had the same skin and eyes. A person whose row in hm08_variation_persons.json
 * carries `looks` (data/humans/variation/looks/, docs/RESEARCH/people-1812-3491/looks.py) gets
 * his own: the body's skin material is cloned for him and its colour multiplied by his
 * complexion's tint (the picture's pores, mottle and blood kept beneath it), and his irises are
 * drawn in his eyes' colour. His hair colour and cut go to human-hair.js as his style.
 *
 * A clone shares the shader program of the material it was made from (same patch, same cache
 * key), so this adds no program and no texture: a few small material objects a figure, freed
 * with its level (`disposeLooks`). The words are the Register of Enlistments' own (fair, light,
 * dark, ruddy, brown; blue, grey, hazel, brown, dark); the tints are a reconstructed rendering
 * of them (liberty L-1812-garrison-looks-3491), not a measured colour of anyone's skin.
 */
import * as THREE from 'three';

/** Linear multipliers over the shared skin picture (a light European skin), by the register's word. */
export const COMPLEXION_TINT = Object.freeze({
  fair: Object.freeze([1.04, 1.0, 0.97]),
  light: Object.freeze([1.0, 0.95, 0.9]),
  ruddy: Object.freeze([1.03, 0.86, 0.8]),
  dark: Object.freeze([0.84, 0.74, 0.64]),
  brown: Object.freeze([0.76, 0.63, 0.5]),
  // T-3463..T-3467, the town of 1812: the readings' own words for the French, Métis,
  // Potawatomi, Miami and Black people of the post (olive; light brown; a warm medium-to-deep
  // brown; dark brown). Reconstructed renderings as the five above are (liberty
  // L-1812-town-days-3463), with no exaggerated feature: only the colour moves.
  olive: Object.freeze([0.9, 0.79, 0.65]),
  tan: Object.freeze([0.8, 0.65, 0.49]),
  copper: Object.freeze([0.62, 0.46, 0.33]),
  deep_brown: Object.freeze([0.43, 0.3, 0.21]),
});
/** Iris colours, linear, by the register's word for the eyes. */
export const EYE_COLOUR = Object.freeze({
  blue: Object.freeze([0.10, 0.17, 0.30]),
  grey: Object.freeze([0.16, 0.18, 0.19]),
  hazel: Object.freeze([0.16, 0.11, 0.045]),
  brown: Object.freeze([0.075, 0.04, 0.018]),
  dark_brown: Object.freeze([0.03, 0.017, 0.009]),
});

/**
 * Give `root`'s skin and irises `looks`' colours, on clones. Returns the clones (to dispose
 * with the level), or [] where the body has nothing to tint or `looks` names nothing known.
 */
export function dressLooks(root, looks) {
  const tint = COMPLEXION_TINT[looks?.complexion?.drawn];
  const iris = EYE_COLOUR[looks?.eyes?.drawn];
  if (!root || (!tint && !iris)) return [];
  const made = new Map();
  const remake = (m) => {
    if (made.has(m)) return made.get(m);
    let next = null;
    if (tint && /^skin($|__)/.test(m?.name ?? '')) {
      next = m.clone();
      next.color.multiply(new THREE.Color().setRGB(...tint, THREE.LinearSRGBColorSpace));
    } else if (iris && /^eyes__iris$/.test(m?.name ?? '')) {
      next = m.clone();
      // The shared iris picture is one colour; his is drawn flat in his own, under the
      // cornea's dome and highlight (human-skin.js), which is what reads at any distance.
      next.map = null;
      next.color.setRGB(...iris, THREE.LinearSRGBColorSpace);
      next.needsUpdate = true;
    }
    made.set(m, next);
    return next;
  };
  root.traverse((o) => {
    if (!o.isMesh) return;
    if (Array.isArray(o.material)) o.material = o.material.map((m) => remake(m) ?? m);
    else { const n = remake(o.material); if (n) o.material = n; }
  });
  return [...made.values()].filter(Boolean);
}

export function disposeLooks(materials) {
  for (const m of materials ?? []) m.dispose();
}

/** The hair style a person's looks give: his cut, whiskers and colour over `base`'s. */
export function looksHairStyle(looks, base = null) {
  const h = looks?.hair;
  if (!h?.drawn) return null;
  return { ...(base ?? {}), cut: h.cut ?? base?.cut, facial: [...(h.facial ?? []), ...((base?.facial ?? []).filter((f) => /^(brows|lashes)/.test(f)))],
    colour: h.drawn, grade: looks.grade ?? 'reconstructed', basis: looks.basis ?? '' };
}
