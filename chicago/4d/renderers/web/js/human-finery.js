// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-finery.js — a person's own pattern, trimming and cloth finish (T-3553).
 *
 * The owner, 2026-11-14, of the women of Prairie Avenue: *"when i see shows like gilded age they
 * are very fancy and lots of details and you don't have that ... I would think maybe some of these
 * women would have nicer clothing ... Give the women some variation in their clothing appearance"*.
 * Ninety-nine ladies wore one dark suit in six colours. The dress of the years (the Met's day,
 * afternoon and dinner dresses of 1899–1905; docs/RESEARCH/finery-3553/) is carried by its
 * TRIMMING as much as its cut: lace yokes and insertion bands, rows of tucks, bands of velvet
 * ribbon and soutache at the hem, jet on a dark bodice, gathered flounces; by the cloth's figure
 * (stripes, foulard dots, a damask's tonal flower, a calico's sprig) and by its finish (silk
 * shines, velvet glows at its edges). None of that needs a new shape, so none of it is a new
 * GLB: a dress record's `finery` names, for a garment (its material's name, or one piece by its
 * mesh name as `dressCloth`'s `pieces` do):
 *
 *   pattern  { kind: stripe|check|dot|sprig|damask|plaid|pinstripe, rgb, repeat_m, contrast }
 *   trims    [ { kind: ribbon|lace|braid|tucks|jet|flounce|embroidery, from: hem|top|cuff, at_m,
 *                width_m, rgb, rows } ]   (at most four; `at_m` is the trim's centre from that
 *                edge of the garment, so a hem band follows any hem, long or short; a `top`
 *                trim is laid on the body only, never down the sleeves the bind pose holds
 *                out level with the shoulders; a `cuff` is laid round the sleeves' ends)
 *   silk     0..1, velvet 0..1
 *   ground   rgb: the cloth's own colour under its figure, where a two-colour cloth's mean is the
 *            colour the record gives it (tools/finery_words.py)
 *
 * and this turns those words into the numbers fabric.js draws, in the garment's own bind-pose
 * units (a quantised export's positions are not metres: human-skin.js restMatrix). The person's
 * material is their own clone (a cloth colour already made one; otherwise one is made here), so
 * a figure adds a few small material objects and no texture and no program: every garment,
 * plain or fine, compiles fabric.js's one program. Everything is a reconstructed rendering of
 * the period's dress (liberty L-finery-3553), not any person's recorded clothes.
 */
import * as THREE from 'three';
import { restMatrix } from './human-skin.js';

export const PATTERNS = Object.freeze({ stripe: 1, check: 2, dot: 3, sprig: 4, damask: 5, plaid: 6, pinstripe: 7 });
export const TRIMS = Object.freeze({ ribbon: 1, lace: 2, braid: 3, tucks: 4, jet: 5, flounce: 6, embroidery: 7 });

const clamp = (v, lo, hi, d) => (Number.isFinite(v) ? Math.min(hi, Math.max(lo, v)) : d);
const rgbOf = (a) => (Array.isArray(a) && a.length === 3 && a.every(Number.isFinite) ? a.map((x) => clamp(x, 0, 1, 0)) : null);

/** One garment's finery, held to what the shader can draw; null where it names nothing. */
export function finerySpec(spec) {
  if (!spec || typeof spec !== 'object') return null;
  const pat = spec.pattern && PATTERNS[spec.pattern.kind] && rgbOf(spec.pattern.rgb)
    ? { kind: spec.pattern.kind, rgb: rgbOf(spec.pattern.rgb), repeat_m: clamp(spec.pattern.repeat_m, .004, .3, .03), contrast: clamp(spec.pattern.contrast, 0, 1, 1) }
    : null;
  const trims = (Array.isArray(spec.trims) ? spec.trims : [])
    .filter((t) => t && TRIMS[t.kind] && rgbOf(t.rgb))
    .slice(0, 4)
    .map((t) => ({ kind: t.kind, from: ['top', 'cuff'].includes(t.from) ? t.from : 'hem', at_m: clamp(t.at_m, 0, 1.2, .1),
      width_m: clamp(t.width_m, .006, .5, .04), rgb: rgbOf(t.rgb), rows: clamp(t.rows, 2, 16, 5) }));
  const silk = clamp(spec.silk, 0, 1, 0), velvet = clamp(spec.velvet, 0, 1, 0), ground = rgbOf(spec.ground);
  if (!pat && !trims.length && !silk && !velvet) return null;
  return { pattern: pat, trims, silk, velvet, ground };
}

/** The meshes `key` names under `root`: a piece by its mesh name, else a garment by material. */
function meshesOf(root, key) {
  const piece = new RegExp(`(^|_)${key.replace(/[^a-z0-9_]/gi, '')}(_lod\\d+)?$`);
  const byPiece = [], byMaterial = [];
  root.traverse((o) => {
    if (!o.isMesh || Array.isArray(o.material)) return;
    if (piece.test(o.name)) byPiece.push(o);
    else if (o.material?.name === key) byMaterial.push(o);
  });
  return byPiece.length ? byPiece : byMaterial;
}

/**
 * The shader's numbers for one garment worn on `meshes` (all sharing one material): its own
 * height span and units a metre, its pattern and up to four trims.
 */
export function fineryNumbers(spec, meshes, root) {
  let lo = Infinity, hi = -Infinity, out = 0, upm = 0;
  for (const m of meshes) {
    if (!m.visible) continue;
    const p = m.geometry?.attributes?.position;
    if (!p) continue;
    for (let i = 0; i < p.count; i++) { const y = p.getY(i), x = Math.abs(p.getX(i)); if (y < lo) lo = y; if (y > hi) hi = y; if (x > out) out = x; }
    if (!upm) {
      const R = restMatrix(m, root);
      const s = new THREE.Vector3().setFromMatrixColumn(R, 1).length();
      upm = s > 0 ? 1 / s : 0;
    }
  }
  if (!(hi > lo) || !(upm > 0)) return null;
  const pat = spec.pattern;
  const bands = [], bandRgb = [];
  for (const t of spec.trims) {
    const half = t.width_m * upm / 2;
    const centre = t.from === 'top' ? hi - t.at_m * upm : t.from === 'cuff' ? out - t.at_m * upm : lo + t.at_m * upm;
    bands.push([centre, half, TRIMS[t.kind] + 16 * ({ hem: 0, top: 1, cuff: 2 })[t.from], t.rows]);
    bandRgb.push(t.rgb);
  }
  return {
    fin: [lo, hi, upm, spec.silk],
    pat: pat ? [PATTERNS[pat.kind], pat.repeat_m * upm, pat.contrast, spec.velvet] : [0, 1, 0, spec.velvet],
    patRgb: pat ? pat.rgb : [0, 0, 0],
    bands, bandRgb,
  };
}

/**
 * Put `finery` (a dress record's map of garment -> spec) on the figure at `root`, before
 * fabric.js clothes it. `owned` is the materials already this person's own (dressCloth's
 * clones), which take the numbers in place; any other is cloned first. Returns the new clones.
 */
export function dressFinery(root, finery, owned = []) {
  if (!root || !finery || typeof finery !== 'object') return [];
  const mine = new Set(owned);
  const made = [];
  for (const [key, raw] of Object.entries(finery)) {
    const spec = finerySpec(raw);
    if (!spec) continue;
    const meshes = meshesOf(root, key);
    if (!meshes.length) continue;
    // One clone for every mesh of this garment that shares a material, so its trims are laid
    // against the garment's whole height (a jacket's body and basque are one span).
    const byMaterial = new Map();
    for (const m of meshes) {
      if (!byMaterial.has(m.material)) byMaterial.set(m.material, []);
      byMaterial.get(m.material).push(m);
    }
    for (const [material, group] of byMaterial) {
      const numbers = fineryNumbers(spec, group, root);
      if (!numbers) continue;
      let next = material;
      if (!mine.has(material)) {
        next = material.clone();
        mine.add(next);
        made.push(next);
      }
      next.userData = { ...next.userData, chiFinery: numbers };
      if (spec.ground) { next.color.setRGB(...spec.ground, THREE.LinearSRGBColorSpace); if (next.map) { next.map = null; next.needsUpdate = true; } }
      for (const m of group) m.material = next;
    }
  }
  return made;
}
