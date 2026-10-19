/**
 * tree-model.js — one tree of a species, grown as wood and leaf, built ONCE as
 * a template and stood wherever the planters put it (T-2743).
 *
 * WHY A GROWN TREE. The timber was a bole, a few straight limbs and a handful of
 * spray balls (`trees.js` addTree): from forty metres it read as a tree, from
 * ten it read as green clouds on a pole, and every species drew the same
 * architecture at a different size. A tree a visitor can name is named by its
 * ARCHITECTURE first — the elm's vase, the bur oak's low crooked horizontals,
 * the cottonwood's few massive ascending limbs, the willow's leaning stems —
 * and by its bark second; the leaf is the last thing the eye resolves.
 * So each species here carries an architecture (`ARCH`), and the tree is grown
 * from it: a trunk with its root flare, scaffold limbs at the species' angle,
 * branches off those toward the species' crown envelope, and foliage clumped
 * at the ends of the branches the way leaves are carried, with sky between the
 * clumps.
 *
 * WHAT IS EVIDENCE AND WHAT IS NOT. Nothing here is a source about a particular
 * tree of 1812 or 1835. The species, the height and crown bands and the July
 * colours stay the zone records' (`data/flora/zones/`); this file only decides
 * how a tree of that species is put together, from the species' ordinary
 * botanical habit (the `ARCH` table below), and it is recorded as a liberty
 * (docs/LIBERTIES.md L-tree-architecture-2743).
 *
 * THREE DETAIL LEVELS of one grown tree, never three different trees: `near`
 * draws every branch to the third order and a leaf clump per twig; `mid` drops
 * the third order and carries the same foliage on fewer, larger cards; `far`
 * keeps the trunk and scaffolds and a few broad cards that hold the crown's
 * silhouette. The skeleton and the clump centres are grown once, so the three
 * agree on where the tree's mass is and the swap between them is a change of
 * grain, not of shape.
 */

import * as THREE from 'three';

/* -------------------------------------------------------------------------- */
/* the species' habits                                                         */
/* -------------------------------------------------------------------------- */

/**
 * The architecture of each species, as an open-grown or stand-grown tree of the
 * Chicago lake plain would carry it. Every number is a reconstruction bounded
 * by the species' ordinary habit; none is a measurement of a tree that stood.
 *
 *   crown     envelope: 'oval' | 'vase' | 'spread' | 'round' | 'column' | 'cone' | 'irregular'
 *   crownBase where the crown begins, as a fraction of height (the clear bole)
 *   fork      'decurrent' (the trunk breaks into scaffolds) | 'excurrent' (a
 *             leader runs to the top and carries laterals)
 *   stems     [min, max] co-dominant stems from the ground (willows, silver maple);
 *             `stemSplay` their lean out of the clump, degrees (10 unless the species says)
 *   scaffolds [min, max] major limbs at the fork
 *   limbAngle degrees from vertical of a scaffold leaving the trunk
 *   rise      how the limb turns as it grows: > 0 climbs (cottonwood, elm),
 *             < 0 sags (bur oak, white oak); per metre of limb
 *   twist     tortuosity: 0 straight, 1 the bur oak's elbows
 *   order2    [count per limb, angle from the limb] for the second order
 *   order3    the same for the third
 *   droop     how far the twig ends hang (elm, willow)
 *   clump     foliage clump radius as a fraction of crown radius (`clumpMin`
 *             its floor in metres, 0.7 unless the species says)
 *   density   clumps per metre of terminal branch
 *   leaf      the leaf-atlas family; bark the bark tile
 */
export const ARCH = {
  populus_deltoides: {
    crown: 'irregular', crownBase: 0.34, fork: 'decurrent', stems: [1, 2], scaffolds: [3, 5],
    limbAngle: 32, rise: 0.05, twist: 0.45, order2: [5, 42], order3: [3, 46], droop: 0.10,
    clump: 0.17, density: 0.80, gaps: 0.40, leaf: 'poplar', bark: 'furrowed',
  },
  populus_deltoides_dune: {
    crown: 'irregular', crownBase: 0.14, fork: 'decurrent', stems: [1, 3], scaffolds: [3, 4],
    limbAngle: 48, rise: 0.02, twist: 0.65, order2: [4, 48], order3: [2, 50], droop: 0.06,
    clump: 0.20, density: 0.85, gaps: 0.42, leaf: 'poplar', bark: 'furrowed',
  },
  salix_nigra: {
    crown: 'irregular', crownBase: 0.18, fork: 'decurrent', stems: [2, 4], scaffolds: [2, 3],
    limbAngle: 30, rise: 0.02, twist: 0.50, order2: [5, 38], order3: [3, 40], droop: 0.35,
    clump: 0.18, density: 1.0, gaps: 0.32, leaf: 'willow', bark: 'furrowed_dark',
  },
  salix_amygdaloides: {
    crown: 'irregular', crownBase: 0.20, fork: 'decurrent', stems: [1, 3], scaffolds: [2, 4],
    limbAngle: 34, rise: 0.02, twist: 0.45, order2: [5, 40], order3: [3, 42], droop: 0.30,
    clump: 0.18, density: 1.0, gaps: 0.32, leaf: 'willow', bark: 'furrowed_dark',
  },
  acer_saccharinum: {
    crown: 'vase', crownBase: 0.18, fork: 'decurrent', stems: [1, 3], scaffolds: [3, 5],
    limbAngle: 24, rise: 0.04, twist: 0.25, order2: [6, 40], order3: [4, 42], droop: 0.12,
    clump: 0.15, density: 1.15, gaps: 0.28, leaf: 'maple', bark: 'shaggy',
  },
  ulmus_americana: {
    crown: 'vase', crownBase: 0.32, fork: 'decurrent', stems: [1, 1], scaffolds: [3, 6],
    limbAngle: 22, rise: 0.02, twist: 0.20, order2: [6, 44], order3: [4, 48], droop: 0.42,
    clump: 0.14, density: 1.20, gaps: 0.26, leaf: 'elm', bark: 'interlaced',
  },
  fraxinus_pennsylvanica: {
    crown: 'oval', crownBase: 0.36, fork: 'decurrent', stems: [1, 1], scaffolds: [3, 5],
    limbAngle: 34, rise: 0.06, twist: 0.20, order2: [5, 44], order3: [3, 44], droop: 0.10,
    clump: 0.17, density: 0.95, gaps: 0.34, leaf: 'compound', bark: 'interlaced',
  },
  fraxinus_nigra: {
    crown: 'column', crownBase: 0.42, fork: 'excurrent', stems: [1, 1], scaffolds: [5, 8],
    limbAngle: 48, rise: 0.08, twist: 0.20, order2: [4, 44], order3: [2, 44], droop: 0.08,
    clump: 0.20, density: 0.85, gaps: 0.36, leaf: 'compound', bark: 'corky',
  },
  quercus_bicolor: {
    crown: 'round', crownBase: 0.30, fork: 'decurrent', stems: [1, 1], scaffolds: [4, 6],
    limbAngle: 58, rise: -0.02, twist: 0.65, order2: [6, 48], order3: [4, 52], droop: 0.20,
    clump: 0.15, density: 1.10, gaps: 0.30, leaf: 'oak_round', bark: 'plated',
  },
  celtis_occidentalis: {
    crown: 'oval', crownBase: 0.34, fork: 'decurrent', stems: [1, 1], scaffolds: [3, 5],
    limbAngle: 38, rise: 0.03, twist: 0.40, order2: [5, 48], order3: [3, 50], droop: 0.22,
    clump: 0.16, density: 1.0, gaps: 0.32, leaf: 'elm', bark: 'warty',
  },
  juglans_nigra: {
    crown: 'round', crownBase: 0.45, fork: 'decurrent', stems: [1, 1], scaffolds: [3, 4],
    limbAngle: 42, rise: 0.02, twist: 0.35, order2: [4, 46], order3: [2, 48], droop: 0.12,
    clump: 0.20, density: 0.75, gaps: 0.42, leaf: 'compound', bark: 'blocky',
  },
  platanus_occidentalis: {
    crown: 'irregular', crownBase: 0.30, fork: 'decurrent', stems: [1, 1], scaffolds: [3, 5],
    limbAngle: 46, rise: 0.0, twist: 0.70, order2: [5, 50], order3: [3, 52], droop: 0.14,
    clump: 0.18, density: 0.85, gaps: 0.38, leaf: 'maple', bark: 'sycamore',
  },
  salix_interior: {
    crown: 'irregular', crownBase: 0.05, fork: 'decurrent', stems: [6, 11], scaffolds: [0, 0],
    limbAngle: 14, rise: 0.08, twist: 0.30, order2: [3, 30], order3: [0, 0], droop: 0.25,
    clump: 0.30, density: 1.2, gaps: 0.22, leaf: 'willow', bark: 'smooth',
  },
  tilia_americana: {
    crown: 'oval', crownBase: 0.26, fork: 'excurrent', stems: [1, 2], scaffolds: [7, 10],
    limbAngle: 58, rise: 0.06, twist: 0.20, order2: [5, 46], order3: [3, 46], droop: 0.12,
    clump: 0.14, density: 1.30, gaps: 0.22, leaf: 'heart', bark: 'ridged',
  },
  acer_saccharum: {
    crown: 'oval', crownBase: 0.30, fork: 'decurrent', stems: [1, 1], scaffolds: [4, 6],
    limbAngle: 32, rise: 0.06, twist: 0.25, order2: [6, 44], order3: [4, 44], droop: 0.08,
    clump: 0.14, density: 1.30, gaps: 0.22, leaf: 'maple', bark: 'shaggy',
  },
  quercus_rubra: {
    crown: 'round', crownBase: 0.36, fork: 'decurrent', stems: [1, 1], scaffolds: [3, 5],
    limbAngle: 42, rise: 0.02, twist: 0.45, order2: [5, 48], order3: [3, 50], droop: 0.10,
    clump: 0.16, density: 1.05, gaps: 0.30, leaf: 'oak_pointed', bark: 'ridged',
  },
  ostrya_virginiana: {
    crown: 'oval', crownBase: 0.30, fork: 'excurrent', stems: [1, 1], scaffolds: [6, 9],
    limbAngle: 58, rise: 0.0, twist: 0.30, order2: [4, 44], order3: [2, 44], droop: 0.20,
    clump: 0.20, density: 1.1, gaps: 0.28, leaf: 'elm', bark: 'shaggy',
  },
  quercus_macrocarpa: {
    crown: 'spread', crownBase: 0.24, fork: 'decurrent', stems: [1, 1], scaffolds: [4, 6],
    limbAngle: 66, rise: -0.03, twist: 0.90, order2: [6, 52], order3: [4, 56], droop: 0.12,
    clump: 0.14, density: 0.95, gaps: 0.36, leaf: 'oak_round', bark: 'blocky',
  },
  quercus_alba: {
    crown: 'spread', crownBase: 0.26, fork: 'decurrent', stems: [1, 1], scaffolds: [4, 6],
    limbAngle: 62, rise: -0.02, twist: 0.70, order2: [6, 50], order3: [4, 52], droop: 0.10,
    clump: 0.14, density: 1.0, gaps: 0.32, leaf: 'oak_round', bark: 'plated',
  },
  quercus_velutina: {
    crown: 'irregular', crownBase: 0.30, fork: 'decurrent', stems: [1, 1], scaffolds: [3, 5],
    limbAngle: 52, rise: 0.0, twist: 0.75, order2: [5, 50], order3: [3, 52], droop: 0.10,
    clump: 0.15, density: 0.95, gaps: 0.36, leaf: 'oak_pointed', bark: 'blocky',
  },
  carya_ovata: {
    crown: 'column', crownBase: 0.44, fork: 'excurrent', stems: [1, 1], scaffolds: [6, 9],
    limbAngle: 46, rise: 0.06, twist: 0.30, order2: [4, 44], order3: [2, 44], droop: 0.10,
    clump: 0.18, density: 0.90, gaps: 0.36, leaf: 'compound', bark: 'shaggy_strips',
  },
  populus_tremuloides: {
    crown: 'column', crownBase: 0.45, fork: 'excurrent', stems: [1, 1], scaffolds: [6, 9],
    limbAngle: 48, rise: 0.08, twist: 0.25, order2: [3, 44], order3: [2, 44], droop: 0.06,
    clump: 0.22, density: 0.85, gaps: 0.40, leaf: 'aspen', bark: 'aspen',
  },
  populus_balsamifera: {
    crown: 'column', crownBase: 0.40, fork: 'excurrent', stems: [1, 1], scaffolds: [6, 9],
    limbAngle: 42, rise: 0.10, twist: 0.25, order2: [3, 40], order3: [2, 40], droop: 0.06,
    clump: 0.22, density: 0.85, gaps: 0.38, leaf: 'poplar', bark: 'smooth',
  },
  // T-2768 — THE SAND HILLS' CONIFERS. "Low cedar trees, ground pine, and sand
  // cherry bushes" (Clarke 1890, south of the town); "stunted cedars, pines, and
  // dwarf-willow trees" (Wau-Bun 1856, north of it). The eastern red cedar of
  // an open dune: a dense cone foliated almost to the sand, the leader often
  // lost to wind so the top is blunt and the cone lopsided; shredding stringy
  // bark. Scale-leaf sprays, so `density` is the highest here and `gaps` low:
  // a cedar is a dark solid, not a lattice.
  juniperus_virginiana: {
    crown: 'cone', crownBase: 0.04, fork: 'excurrent', stems: [1, 1], scaffolds: [18, 26],
    limbAngle: 58, rise: 0.10, twist: 0.35, order2: [4, 42], order3: [2, 40], droop: 0.04,
    clump: 0.22, clumpMin: 0.26, density: 1.45, gaps: 0.10, leaf: 'scale', bark: 'shaggy_strips',
    farBins: [3, 2],
  },
  // The pine neither witness names. Jack pine is the pine of the established
  // Lake Michigan dune ridges (Cowles 1899), and "stunted" fits it: an open,
  // irregular crown of crooked whorled limbs carried low on the stem, needles in
  // brushes at the shoot ends, dark scaly bark.
  pinus_banksiana: {
    crown: 'irregular', crownBase: 0.14, fork: 'excurrent', stems: [1, 1], scaffolds: [11, 15],
    limbAngle: 70, rise: 0.03, twist: 0.85, order2: [4, 50], order3: [2, 46], droop: 0.03,
    clump: 0.17, clumpMin: 0.40, density: 0.80, gaps: 0.50, leaf: 'needle', bark: 'blocky',
    farBins: [4, 2],
  },
  // T-2807 — THE THICKET AT THE WOODS' EDGE. Where the North Side wood and the
  // river woods meet the prairie the fire stops, and the shrubs that resprout
  // after it stand in a band: hazel (the land survey's own undergrowth for the
  // township), wild plum, hawthorn and gray dogwood. Each is a clump of stems
  // from the ground, not a small tree, so `stems` carries the count and
  // `scaffolds` is empty: each stem runs on as its own leader (the sandbar
  // willow's habit, above). `stemSplay` is how far the outer stems lean out of
  // the clump, degrees from vertical; hazel's arch out, dogwood's stand up.
  corylus_americana: {
    crown: 'round', crownBase: 0.08, fork: 'decurrent', stems: [7, 12], scaffolds: [0, 0],
    stemSplay: 24, limbAngle: 18, rise: 0.02, twist: 0.30, order2: [4, 44], order3: [0, 0],
    droop: 0.16, clump: 0.24, clumpMin: 0.34, density: 1.30, gaps: 0.18, leaf: 'elm', bark: 'smooth',
    farBins: [4, 2],
  },
  // Wild plum suckers into thickets but each stem is a small crooked tree: a few
  // stems, a short bole, a round head of zigzag twigs, dark lenticelled bark.
  prunus_americana: {
    crown: 'round', crownBase: 0.28, fork: 'decurrent', stems: [2, 4], scaffolds: [3, 5],
    stemSplay: 16, limbAngle: 48, rise: 0.0, twist: 0.65, order2: [4, 50], order3: [0, 0],
    droop: 0.08, clump: 0.26, clumpMin: 0.36, density: 1.15, gaps: 0.30, leaf: 'elm', bark: 'smooth',
    farBins: [4, 2],
  },
  // Hawthorn: a low, flat-topped, spreading head on one to three crooked stems,
  // the limbs held out nearly level, scaly grey bark; small lobed leaves.
  crataegus_spp: {
    crown: 'spread', crownBase: 0.24, fork: 'decurrent', stems: [1, 3], scaffolds: [4, 6],
    stemSplay: 14, limbAngle: 62, rise: -0.02, twist: 0.75, order2: [4, 56], order3: [0, 0],
    droop: 0.06, clump: 0.24, clumpMin: 0.34, density: 1.20, gaps: 0.30, leaf: 'maple', bark: 'blocky',
    farBins: [4, 2],
  },
  // Gray dogwood: many upright grey stems in a dense colony, a rounded top of
  // opposite, entire leaves.
  cornus_racemosa: {
    crown: 'round', crownBase: 0.10, fork: 'decurrent', stems: [8, 13], scaffolds: [0, 0],
    stemSplay: 12, limbAngle: 14, rise: 0.04, twist: 0.25, order2: [3, 38], order3: [0, 0],
    droop: 0.06, clump: 0.24, clumpMin: 0.32, density: 1.30, gaps: 0.16, leaf: 'heart', bark: 'smooth',
    farBins: [4, 2],
  },
  populus_nigra_italica: {
    crown: 'column', crownBase: 0.06, fork: 'excurrent', stems: [1, 1], scaffolds: [16, 22],
    limbAngle: 16, rise: 0.12, twist: 0.10, order2: [3, 22], order3: [0, 0], droop: 0.0,
    clump: 0.62, density: 1.6, gaps: 0.18, leaf: 'poplar', bark: 'furrowed',
  },
  // T-2809 — THE FORT'S AND DR. HARMON'S YOUNG FRUIT TREES, and the currants
  // beside them. Nursery stock headed low: a short clear stem, three to five
  // scaffold limbs held wide, a round open head. Apple carries oval toothed
  // leaves on scaly grey wood; sour cherry is more upright, on smooth banded
  // bark; peach is the most open, a vase of a few limbs with long narrow
  // leaves (the willow sprays). The currant is a clump of arching stems from
  // the ground with lobed leaves (the maple sprays, at its own small size).
  malus_domestica: {
    crown: 'round', crownBase: 0.30, fork: 'decurrent', stems: [1, 1], scaffolds: [3, 5],
    limbAngle: 54, rise: 0.0, twist: 0.55, order2: [4, 48], order3: [2, 50], droop: 0.10,
    clump: 0.24, clumpMin: 0.30, density: 1.15, gaps: 0.30, leaf: 'elm', bark: 'plated',
    farBins: [4, 2],
  },
  prunus_cerasus: {
    crown: 'round', crownBase: 0.30, fork: 'decurrent', stems: [1, 1], scaffolds: [3, 5],
    limbAngle: 42, rise: 0.04, twist: 0.40, order2: [4, 44], order3: [2, 46], droop: 0.14,
    clump: 0.24, clumpMin: 0.28, density: 1.15, gaps: 0.30, leaf: 'elm', bark: 'smooth',
    farBins: [4, 2],
  },
  prunus_persica: {
    crown: 'vase', crownBase: 0.22, fork: 'decurrent', stems: [1, 1], scaffolds: [3, 4],
    limbAngle: 40, rise: 0.04, twist: 0.35, order2: [4, 42], order3: [2, 44], droop: 0.12,
    clump: 0.24, clumpMin: 0.28, density: 1.05, gaps: 0.36, leaf: 'willow', bark: 'smooth',
    farBins: [4, 2],
  },
  ribes_spp: {
    crown: 'round', crownBase: 0.06, fork: 'decurrent', stems: [6, 10], scaffolds: [0, 0],
    stemSplay: 26, limbAngle: 16, rise: 0.02, twist: 0.30, order2: [3, 40], order3: [0, 0],
    droop: 0.18, clump: 0.26, clumpMin: 0.20, density: 1.30, gaps: 0.20, leaf: 'maple', bark: 'smooth',
    farBins: [4, 2],
  },
};

/** A species with no habit of its own grows as the form its record names. */
const ARCH_OF_FORM = {
  gallery: 'fraxinus_pennsylvanica', open: 'quercus_alba', lean: 'salix_nigra',
  sub: 'ostrya_virginiana', columnar: 'populus_balsamifera', thicket: 'salix_interior',
};

export function archFor(spec) {
  const id = spec.speciesId ?? '';
  // The dune cottonwood is the gallery tree's binomial on another habit. Asked of
  // the cottonwood only: the sand hills' red cedar is a "dune form" too (T-2768).
  if (id === 'populus_deltoides' && /dune form/.test(spec.common ?? '') && ARCH.populus_deltoides_dune) {
    return ARCH.populus_deltoides_dune;
  }
  return ARCH[id] ?? ARCH[ARCH_OF_FORM[spec.form]] ?? ARCH.fraxinus_pennsylvanica;
}

/* -------------------------------------------------------------------------- */
/* atlases: which tile a leaf family and a bark draw from                      */
/* -------------------------------------------------------------------------- */

/** Leaf atlas: 4 x 5 tiles of 512 px (the fifth row since T-2768). Each family has a `sun` spray (the outer
 *  shell: smaller, denser, more leaves) and a `clump` (a broad mass of sprays the
 *  mid and far cards carry). */
export const LEAF_TILES = {
  poplar: [0, 1], willow: [2, 3], elm: [4, 5], maple: [6, 7],
  oak_round: [8, 9], oak_pointed: [10, 11], compound: [12, 13], heart: [14, 15],
  aspen: [0, 1],
  // T-2768: the fifth row (tools/generate_tree_atlas.py CONIFERS).
  scale: [16, 17], needle: [18, 19],
};
/** Bark atlas: 4 x 2 tiles of 512 px. */
export const BARK_TILES = {
  furrowed: 0, furrowed_dark: 0, interlaced: 1, blocky: 2, plated: 3, ridged: 3,
  shaggy: 4, shaggy_strips: 4, smooth: 5, aspen: 5, sycamore: 6, corky: 7, warty: 7,
};
const LEAF_GRID = [4, 5];
const BARK_GRID = [4, 2];

function atlasUV(grid, tile, u, v, padPx = 6, tilePx = 512) {
  const [gx, gy] = grid;
  const pad = padPx / tilePx;
  const cx = tile % gx;
  const cy = Math.floor(tile / gx);
  return [(cx + pad + u * (1 - 2 * pad)) / gx, 1 - (cy + pad + (1 - v) * (1 - 2 * pad)) / gy];
}

/* -------------------------------------------------------------------------- */
/* a growable buffer                                                           */
/* -------------------------------------------------------------------------- */

class Buf {
  constructor() {
    this.pos = []; this.nrm = []; this.col = []; this.uv = []; this.flex = []; this.idx = [];
  }
  get count() { return this.pos.length / 3; }
  vert(p, n, c, uv, flex) {
    this.pos.push(p[0], p[1], p[2]);
    this.nrm.push(n[0], n[1], n[2]);
    this.col.push(c[0], c[1], c[2]);
    this.uv.push(uv[0], uv[1]);
    this.flex.push(flex);
    return this.count - 1;
  }
  tri(a, b, c) { this.idx.push(a, b, c); }
  build(leaf, conf) {
    const g = new THREE.BufferGeometry();
    const n = this.count;
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(this.pos), 3));
    // Normals in a byte each: a template's vertices are repeated across every
    // instance's level, and a byte is as fine as lighting a leaf card needs.
    g.setAttribute('normal', new THREE.BufferAttribute(Int8Array.from(this.nrm, (v) => Math.round(v * 127)), 3, true));
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(this.col), 3));
    g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(this.uv), 2));
    g.setAttribute('aFlex', new THREE.BufferAttribute(new Float32Array(this.flex), 1));
    g.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(n).fill(conf), 1));
    g.setIndex(new THREE.BufferAttribute(n > 65535 ? new Uint32Array(this.idx) : new Uint16Array(this.idx), 1));
    g.computeBoundingSphere();
    g.computeBoundingBox();
    return g;
  }
}

/* -------------------------------------------------------------------------- */
/* small vector maths, on plain arrays so a grown tree is cheap to hold        */
/* -------------------------------------------------------------------------- */

const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const mul = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const len = (a) => Math.hypot(a[0], a[1], a[2]);
const norm = (a) => { const l = len(a) || 1e-6; return [a[0] / l, a[1] / l, a[2] / l]; };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const lerp = (a, b, t) => a + (b - a) * t;
const clamp01 = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);

/** A direction at `angle` (radians) from `axis`, turned `azimuth` around it. */
function deflect(axis, angle, azimuth) {
  const a = norm(axis);
  const ref = Math.abs(a[1]) < 0.95 ? [0, 1, 0] : [1, 0, 0];
  const u = norm(cross(a, ref));
  const v = cross(a, u);
  const s = Math.sin(angle);
  return norm(add(mul(a, Math.cos(angle)), add(mul(u, s * Math.cos(azimuth)), mul(v, s * Math.sin(azimuth)))));
}

function randUnit(rnd) {
  const z = rnd() * 2 - 1;
  const t = rnd() * Math.PI * 2;
  const r = Math.sqrt(1 - z * z);
  return [r * Math.cos(t), z, r * Math.sin(t)];
}

/* -------------------------------------------------------------------------- */
/* the crown envelope                                                          */
/* -------------------------------------------------------------------------- */

/**
 * The crown's outline as a radius at each height: the envelope a branch may not
 * leave and the shell the foliage clumps are carried in. `t` runs 0 at the
 * crown's base to 1 at its top.
 */
function envelopeRadius(shape, t) {
  if (t < 0 || t > 1) return 0;
  switch (shape) {
    case 'vase': return Math.pow(Math.sin(Math.PI * Math.min(1, t * 0.78 + 0.18)), 0.7) * (0.35 + 0.65 * Math.sqrt(t));
    case 'spread': return Math.pow(Math.sin(Math.PI * (0.10 + t * 0.85)), 0.55);
    case 'column': return Math.pow(Math.sin(Math.PI * (0.04 + t * 0.94)), 0.8);
    case 'cone': return Math.pow(1 - t, 0.85);
    case 'round': return Math.pow(Math.sin(Math.PI * (0.03 + t * 0.95)), 0.6);
    case 'irregular': return Math.pow(Math.sin(Math.PI * (0.06 + t * 0.92)), 0.62);
    default: return Math.pow(Math.sin(Math.PI * (0.02 + t * 0.96)), 0.75);
  }
}

/* -------------------------------------------------------------------------- */
/* growing the skeleton                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Grow one tree's skeleton: a list of branches, each a polyline with a radius
 * at every node and an order (0 the trunk), plus the foliage clumps.
 */
function growSkeleton(spec, arch, rnd) {
  const H = lerp(spec.h[0], spec.h[1], 0.5 + (rnd() - 0.5) * 0.6);
  const dbh = lerp(spec.dbh?.[0] ?? H * 0.025, spec.dbh?.[1] ?? H * 0.035, rnd());
  const crownW = spec.crownW
    ? lerp(spec.crownW[0], spec.crownW[1], rnd())
    : H * (spec.spreadK ?? 0.6) * (0.88 + rnd() * 0.24);
  const R = crownW / 2;
  const baseY = H * arch.crownBase * (0.85 + rnd() * 0.3);
  const crownH = Math.max(1, H - baseY);
  const centreY = baseY + crownH * 0.5;
  // The crown drifts a little off the trunk, as an open-grown crown does toward
  // its open side; a leaning tree throws it further.
  const leanA = rnd() * Math.PI * 2;
  const lean = (spec.lean ?? 0) * (0.5 + rnd() * 0.5);
  const off = [Math.cos(leanA) * (lean * baseY * 0.8 + R * 0.06), 0, Math.sin(leanA) * (lean * baseY * 0.8 + R * 0.06)];
  // Irregular crowns are lumpy: the envelope's radius varies by bearing.
  const lobes = [rnd(), rnd(), rnd(), rnd()].map((v) => v * Math.PI * 2);
  const lumpK = arch.crown === 'irregular' ? 0.22 : arch.crown === 'spread' ? 0.14 : 0.08;
  const envR = (p) => {
    const t = (p[1] - baseY) / crownH;
    const az = Math.atan2(p[2] - off[2], p[0] - off[0]);
    const lump = 1 + lumpK * (Math.sin(az * 2 + lobes[0]) * 0.6 + Math.sin(az * 3 + lobes[1]) * 0.4);
    return R * envelopeRadius(arch.crown, t) * lump;
  };
  const inside = (p, k = 1) => {
    const dx = p[0] - off[0];
    const dz = p[2] - off[2];
    return Math.hypot(dx, dz) <= envR(p) * k && p[1] <= H * 1.02;
  };

  const branches = [];
  const clumps = [];

  /** Grow a branch from `start` heading `dir`, `length` metres, radius r0 -> r1. */
  function branch(start, dir, length, r0, r1, order, opts = {}) {
    const steps = Math.max(2, Math.min(9, Math.round(length / Math.max(0.6, r0 * 7))));
    const segL = length / steps;
    const pts = [start];
    const rad = [r0];
    let d = norm(dir);
    let p = start;
    const rise = opts.rise ?? arch.rise;
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      // Tortuosity: the bur oak's elbows, the elm's clean sweep.
      const kink = mul(randUnit(rnd), arch.twist * (order === 0 ? 0.10 : 0.34));
      // Gravitropism, signed by the species: climbing limbs, sagging limbs, and
      // the twig ends hanging under their own leaves.
      const hang = order >= 2 ? -arch.droop * t * 0.9 : 0;
      d = norm(add(d, add(kink, [0, (rise * segL) + hang * 0.5, 0])));
      // Keep inside the crown: a branch that would leave the envelope turns back
      // along it rather than poking a stick into the sky.
      let next = add(p, mul(d, segL));
      if (order > 0 && !inside(next, 1.04)) {
        const out = norm([next[0] - off[0], 0, next[2] - off[2]]);
        d = norm(add(d, mul(out, -0.8)));
        next = add(p, mul(d, segL * 0.7));
      }
      p = next;
      pts.push(p);
      rad.push(lerp(r0, r1, Math.pow(t, 0.9)));
    }
    const b = { pts, rad, order };
    branches.push(b);
    return b;
  }

  /** Children off a branch, at the species' angle, phyllotaxis turning. */
  function children(parent, order, count, angleDeg, lengthK) {
    if (count <= 0) return [];
    const out = [];
    const az0 = rnd() * Math.PI * 2;
    for (let i = 0; i < count; i++) {
      const t = lerp(0.28, 0.94, (i + 0.3 + rnd() * 0.4) / count);
      const seg = t * (parent.pts.length - 1);
      const k = Math.min(parent.pts.length - 2, Math.floor(seg));
      const f = seg - k;
      const at = add(parent.pts[k], mul(sub(parent.pts[k + 1], parent.pts[k]), f));
      const pr = lerp(parent.rad[k], parent.rad[k + 1], f);
      const axis = norm(sub(parent.pts[k + 1], parent.pts[k]));
      const ang = (angleDeg + (rnd() - 0.5) * 22) * Math.PI / 180;
      const dir = deflect(axis, ang, az0 + i * 2.39996 + (rnd() - 0.5) * 0.6);
      // A child's reach is what is left of the crown in its direction.
      const toEdge = Math.max(0.4, envR(at) - Math.hypot(at[0] - off[0], at[2] - off[2]));
      const L = Math.max(0.5, lengthK * (0.55 + rnd() * 0.45) * Math.min(R * 0.9, toEdge * 1.35 + R * 0.25));
      const r0 = Math.max(0.006, pr * (0.55 + rnd() * 0.15));
      out.push(branch(at, dir, L, r0, r0 * 0.28, order));
    }
    return out;
  }

  /* the stems and the trunk */
  const nStems = arch.stems[0] + Math.floor(rnd() * (arch.stems[1] - arch.stems[0] + 1));
  const r0 = dbh / 2;
  const scaffolds = [];
  const stemAngle = nStems > 1 ? (arch.stemSplay ?? 10) + (spec.lean ?? 0) * 40 : 0;
  for (let s = 0; s < nStems; s++) {
    const az = leanA + (s / nStems) * Math.PI * 2 + (rnd() - 0.5) * 0.8;
    const dir0 = nStems > 1 ? deflect([0, 1, 0], (stemAngle + rnd() * 10) * Math.PI / 180, az)
      : norm(add([0, 1, 0], [Math.cos(leanA) * lean, 0, Math.sin(leanA) * lean]));
    const sr = nStems > 1 ? r0 * (0.62 + rnd() * 0.25) / Math.sqrt(nStems * 0.6) : r0;
    if (arch.fork === 'excurrent') {
      // A leader to the top, laterals filed up it.
      const leader = branch([0, 0, 0], dir0, H * 0.97, sr, sr * 0.12, 0, { rise: 0.02 });
      const n = arch.scaffolds[0] + Math.floor(rnd() * (arch.scaffolds[1] - arch.scaffolds[0] + 1));
      for (let i = 0; i < n; i++) {
        const t = lerp(baseY / H, 0.94, (i + rnd() * 0.6) / n);
        const seg = t * (leader.pts.length - 1);
        const k = Math.min(leader.pts.length - 2, Math.floor(seg));
        const at = add(leader.pts[k], mul(sub(leader.pts[k + 1], leader.pts[k]), seg - k));
        const pr = lerp(leader.rad[k], leader.rad[k + 1], seg - k);
        const ang = (arch.limbAngle + (1 - t) * 18 + (rnd() - 0.5) * 14) * Math.PI / 180;
        const dir = deflect([0, 1, 0], ang, i * 2.39996 + rnd() * 0.5);
        const reach = Math.max(0.6, envR(at)) * (0.85 + rnd() * 0.25);
        scaffolds.push(branch(at, dir, reach, Math.max(0.012, pr * 0.42), pr * 0.08, 1));
      }
    } else {
      // A clear bole to the fork, then the scaffolds. The trunk does not stop
      // at the fork: it runs on as the strongest scaffold (the leader), so the
      // limbs leave a tapering stem rather than the cut top of a post.
      const forkY = Math.max(0.8, baseY * (nStems > 1 ? 0.55 : 0.92));
      const trunk = branch([0, 0, 0], dir0, forkY / Math.max(0.3, dir0[1]), sr, sr * 0.86, 0, { rise: 0.01 });
      const top = trunk.pts[trunk.pts.length - 1];
      const topR = trunk.rad[trunk.rad.length - 1];
      const n = arch.scaffolds[0] + Math.floor(rnd() * (arch.scaffolds[1] - arch.scaffolds[0] + 1));
      const count = Math.max(1, Math.round(n / Math.sqrt(nStems)));
      const azBase = rnd() * Math.PI * 2;
      for (let i = 0; i < count; i++) {
        const lead = i === 0;
        // Scaffolds leave over the top of the bole and up the leader, not from one point.
        const drop = lead ? topR * 1.5 : (rnd() * 0.18) * forkY - rnd() * crownH * 0.12;
        const at = add(top, [0, -drop, 0]);
        const ang = (lead ? arch.limbAngle * 0.35 : arch.limbAngle + (rnd() - 0.5) * 16) * Math.PI / 180;
        const az = azBase + (i / count) * Math.PI * 2 + (rnd() - 0.5) * 0.9;
        const dir = deflect(nStems > 1 ? dir0 : [0, 1, 0], ang, az);
        // Long enough to carry foliage to the crown's far side and top.
        const reachH = (H - at[1]) * (lead ? 0.92 : 0.62 + rnd() * 0.3);
        const reachR = R * (lead ? 0.3 : 0.70 + rnd() * 0.25);
        const L = Math.hypot(reachH * Math.cos(ang) * 0.9, reachR * Math.sin(ang) * 1.1) + crownH * 0.18;
        // Pipe model, roughly: the limbs' cross-sections sum to the stem's.
        const lr = lead ? topR * 0.80 : topR * (0.55 + rnd() * 0.15) / Math.sqrt(Math.max(1, (count - 1) / 2.4));
        scaffolds.push(branch(at, dir, L, lr, lr * (lead ? 0.12 : 0.16), lead ? 0 : 1));
      }
      if (arch.scaffolds[1] === 0) scaffolds.push(trunk);
    }
  }

  /* the second and third orders */
  const second = [];
  for (const s of scaffolds) {
    const n = Math.round(arch.order2[0] * (0.75 + rnd() * 0.5));
    second.push(...children(s, 2, n, arch.order2[1], 0.62));
  }
  const third = [];
  for (const s of second) {
    const n = Math.round(arch.order3[0] * (0.6 + rnd() * 0.6));
    third.push(...children(s, 3, n, arch.order3[1], 0.55));
  }

  /* the foliage: clumps carried along the outer reach of the finest branches */
  const terminal = third.length ? [...third, ...second.filter(() => rnd() < 0.5)] : second.length ? second : scaffolds;
  // A clump is never smaller than a near card can carry a spray on (0.7 m), except
  // for the small dune conifers, whose whole crown is a few metres (`clumpMin`).
  const clumpR = Math.max(arch.clumpMin ?? 0.7, R * arch.clump);
  for (const b of terminal) {
    let L = 0;
    for (let i = 1; i < b.pts.length; i++) L += len(sub(b.pts[i], b.pts[i - 1]));
    const n = Math.max(1, Math.round(L * arch.density * FOLIAGE_K / Math.max(0.6, clumpR * 0.9)));
    for (let i = 0; i < n; i++) {
      const t = lerp(0.35, 1.0, (i + rnd()) / n);
      const seg = t * (b.pts.length - 1);
      const k = Math.min(b.pts.length - 2, Math.floor(seg));
      const at = add(b.pts[k], mul(sub(b.pts[k + 1], b.pts[k]), seg - k));
      // Gaps: a fraction of clumps are never grown, so sky shows between them.
      if (rnd() < arch.gaps * 0.5) continue;
      const dir = norm(sub(b.pts[k + 1], b.pts[k]));
      clumps.push({ at, dir, r: clumpR * (0.7 + rnd() * 0.5) });
    }
  }
  // Fill the crown's shell where branching left it bare, on the nearest wood.
  const shellN = Math.round((R * R * 0.9 + crownH * R * 0.3) * arch.density * 0.18 * SHELL_K);
  for (let i = 0; i < shellN; i++) {
    const t = rnd();
    const az = rnd() * Math.PI * 2;
    const y = baseY + crownH * (0.15 + 0.82 * t);
    const er = envR([off[0] + Math.cos(az), y, off[2] + Math.sin(az)]) * (0.72 + rnd() * 0.24);
    const at = [off[0] + Math.cos(az) * er, y, off[2] + Math.sin(az) * er];
    if (rnd() < arch.gaps) continue;
    clumps.push({ at, dir: norm([Math.cos(az), 0.3, Math.sin(az)]), r: clumpR * (0.7 + rnd() * 0.4), shell: true });
  }
  return { H, dbh, R, baseY, crownH, centreY, off, branches, clumps, envR };
}

/* -------------------------------------------------------------------------- */
/* meshing                                                                     */
/* -------------------------------------------------------------------------- */

/** How much foliage the skeleton carries. A crown is mostly leaf from outside:
 *  its shell area over a near card's area (a 24 m cottonwood: ~740 m2 of shell,
 *  ~1.7 m cards) wants several hundred clumps, three times the first growth. */
const FOLIAGE_K = 4.2;
/** The leaf atlas is painted at its own value (a lit leaf ~0.45, a shaded one
 *  ~0.06 linear, mean ~0.3), and the zone records' July colours are the
 *  foliage's reflectance; the vertex colour carries the record's colour over
 *  the atlas's mean so the two multiply back to the record. */
const LEAF_GAIN = 2.0;
const SHELL_K = 7.0;

// `distant` (T-2808): the trunk alone, three-sided, under a crown of a few masses.
const SIDES = { near: [10, 7, 5, 3], mid: [6, 4, 3, 0], far: [4, 3, 0, 0], distant: [3, 0, 0, 0] };

function linearRGB(hex) {
  const c = new THREE.Color().setHex(hex);
  return [c.r, c.g, c.b];
}

/** Every `k`th node of a limb, keeping its ends. */
function decimate(b, k) {
  const pts = [];
  const rad = [];
  for (let i = 0; i < b.pts.length; i += k) { pts.push(b.pts[i]); rad.push(b.rad[i]); }
  if ((b.pts.length - 1) % k) { pts.push(b.pts[b.pts.length - 1]); rad.push(b.rad[b.rad.length - 1]); }
  return { ...b, pts, rad };
}

/** A tube along a branch polyline. Bark v runs along the wood at the bark's own
 *  scale: one tile per circumference and a half, so a trunk and a twig carry
 *  furrows of the same size. */
function tube(buf, b, sides, barkTile, tint, flexOf) {
  if (sides < 3) return;
  const n = b.pts.length;
  // A frame per node, carried along the polyline so the seams do not twist.
  const tangents = b.pts.map((p, i) => norm(sub(b.pts[Math.min(n - 1, i + 1)], b.pts[Math.max(0, i - 1)])));
  let u = norm(cross(tangents[0], Math.abs(tangents[0][1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]));
  let vAcc = 0;
  const rings = [];
  for (let i = 0; i < n; i++) {
    const t = tangents[i];
    u = norm(sub(u, mul(t, dot(u, t))));
    const w = cross(t, u);
    let r = b.rad[i];
    // The root flare: the bottom of a trunk widens into its buttresses.
    if (b.order === 0 && i === 0) r *= 1.55;
    else if (b.order === 0 && i === 1) r *= 1.08;
    if (i > 0) vAcc += len(sub(b.pts[i], b.pts[i - 1])) / Math.max(0.05, 2 * Math.PI * r * 1.5);
    rings.push({ p: b.pts[i], u, w, r, v: vAcc });
  }
  // Each segment maps its own stretch of bark into the tile: v restarts so the
  // tile never needs to repeat inside the atlas, and the segments are short
  // enough (growSkeleton's steps) that the stretch stays near one tile.
  for (let i = 0; i < n - 1; i++) {
    const A = rings[i];
    const B = rings[i + 1];
    const span = Math.max(0.25, Math.min(1, B.v - A.v));
    const base = buf.count;
    for (const [ring, vv] of [[A, 0], [B, span]]) {
      const flex = flexOf(ring.p);
      for (let s = 0; s <= sides; s++) {
        const a = (s / sides) * Math.PI * 2;
        const nrm = add(mul(ring.u, Math.cos(a)), mul(ring.w, Math.sin(a)));
        const p = add(ring.p, mul(nrm, ring.r));
        // Darker low on the bole and on the underside of a limb.
        const ao = 0.72 + 0.28 * clamp01((p[1] + 1.5) / 6) * (0.80 + 0.20 * (nrm[1] * 0.5 + 0.5));
        buf.vert(p, nrm, mul(tint, ao), atlasUV(BARK_GRID, barkTile, s / sides, vv), flex);
      }
    }
    for (let s = 0; s < sides; s++) {
      const a = base + s;
      const b2 = base + s + 1;
      const c = a + sides + 1;
      const d = b2 + sides + 1;
      buf.tri(a, b2, c);
      buf.tri(b2, d, c);
    }
  }
}

/** One foliage card: a quad of the species' spray, turned the way the twig
 *  carries it. Its normal is bent toward the crown's outside, so a crown shades
 *  as a volume (lit cap, darker interior) while each card keeps its own cut-out
 *  silhouette. */
function card(buf, at, dir, size, tile, colour, outward, flex, rnd, facing = null) {
  // The card's plane holds the twig and a sideways axis turned at random; or,
  // given `facing`, the plane is turned square to it (the twig laid into it),
  // so a big card is seen flat from that side rather than as a streak.
  let t = norm(add(dir, mul(randUnit(rnd), 0.6)));
  let side;
  if (facing) {
    const along = sub(t, mul(facing, dot(t, facing)));
    t = len(along) > 0.2 ? norm(along) : norm(sub([0, 1, 0], mul(facing, facing[1])));
    side = norm(cross(t, facing));
  } else side = norm(cross(t, randUnit(rnd)));
  const w = size * (0.85 + rnd() * 0.3);
  const h = size * (1.0 + rnd() * 0.35);
  const flip = rnd() < 0.5;
  const base = buf.count;
  const corners = [[-0.5, -0.15], [0.5, -0.15], [0.5, 0.85], [-0.5, 0.85]];
  const cardN = norm(cross(side, t));
  const n = norm(add(mul(outward, 0.78), mul(cardN, 0.22 * (rnd() < 0.5 ? 1 : -1))));
  for (const [cu, cv] of corners) {
    const p = add(at, add(mul(side, cu * w), mul(t, cv * h)));
    buf.vert(p, n, colour, atlasUV(LEAF_GRID, tile, flip ? 0.5 - cu : cu + 0.5, cv + 0.15), flex + (cv + 0.15) * 0.18);
  }
  buf.tri(base, base + 1, base + 2);
  buf.tri(base, base + 2, base + 3);
}

/**
 * Build a species template at one level of detail. The skeleton is grown from
 * `seed`, so the same seed gives the same tree at every level.
 *
 * @returns {{ wood: THREE.BufferGeometry, leaves: THREE.BufferGeometry, height: number,
 *             crownR: number, trunkR: number }}
 */
export function buildTreeTemplate(spec, seed, lod = 'near', { conf = 0.5, skeleton = null, leafCover = 1, leafScale = 1 } = {}) {
  const rnd = mulberry32(seed);
  const arch = archFor(spec);
  const sk = skeleton ?? growSkeleton(spec, arch, rnd);
  const lrnd = mulberry32(seed ^ 0x9e3779b9);
  const wood = new Buf();
  const leaves = new Buf();
  const sides = SIDES[lod] ?? SIDES.near;
  const barkTile = BARK_TILES[arch.bark] ?? 0;
  const barkTint = barkLinear(spec.bark ?? 0x5a5246, arch.bark);
  const barkUpper = spec.barkUpper != null ? barkLinear(spec.barkUpper, arch.bark) : barkTint;
  const flexOf = (p) => clamp01((p[1] / Math.max(1, sk.H)) * 0.55 + Math.hypot(p[0], p[2]) / Math.max(1, sk.R) * 0.25) * 0.6;
  // Coarser levels walk every second (mid) or fourth (far) node of a limb:
  // the same limb, in fewer, longer segments.
  const stride = lod === 'near' ? 1 : lod === 'mid' ? 2 : lod === 'far' ? 4 : 8;
  const minRad = lod === 'near' ? 0 : lod === 'mid' ? 0.03 : 0.07;
  // A shrub's stems are all thinner than that, which would leave its coarse
  // levels with no wood at all: a batch geometry of zero vertices, which the
  // drawn-timber census cannot read back. Its stoutest stem stays.
  let keep = null;
  if (minRad > 0 && !sk.branches.some((b) => sides[Math.min(3, b.order)] && b.rad[0] >= minRad)) {
    for (const b of sk.branches) if (b.order === 0 && (!keep || b.rad[0] > keep.rad[0])) keep = b;
  }
  for (const b of sk.branches) {
    const s = sides[Math.min(3, b.order)];
    if (!s) continue;
    // Thin wood a far tree cannot resolve is not drawn at all.
    if (b.rad[0] < minRad && b !== keep) continue;
    // A far tree's limbs are a few strokes against the sky: twice the trunk's stride.
    const k = (lod === 'far' || lod === 'distant') && b.order > 0 ? stride * 2 : stride;
    tube(wood, k > 1 ? decimate(b, k) : b, s, barkTile, b.order === 0 ? barkTint : barkUpper, flexOf);
  }

  const dark = linearRGB(spec.dark ?? 0x3d5a2c);
  const light = linearRGB(spec.light ?? 0x86a252);
  const [sunTile, clumpTile] = LEAF_TILES[arch.leaf] ?? LEAF_TILES.elm;
  const centre = [sk.off[0], sk.centreY, sk.off[2]];
  const shade = (at) => {
    const rel = sub(at, centre);
    const outward = norm(add(norm([rel[0], rel[1] * 0.6, rel[2]]), [0, 0.35, 0]));
    // Light across the crown: the cap and the sun side bright, the inside dark.
    const shell = clamp01(Math.hypot(rel[0], rel[2]) / Math.max(0.5, sk.envR(at)));
    const up = clamp01((at[1] - sk.baseY) / sk.crownH);
    const lit = clamp01(0.20 + 0.45 * shell + 0.40 * up);
    const tint = 0.86 + lrnd() * 0.26;
    const colour = dark.map((v, j) => lerp(v, light[j], 0.25 + lit * 0.70) * lerp(0.72, 1, lit) * tint * LEAF_GAIN);
    return { outward, colour, flex: 0.45 + 0.4 * up };
  };
  // A season's crown (the 1904 Season setting): `leafCover` is the share of the
  // summer clumps in leaf and `leafScale` their size; 0 is a bare winter tree.
  const clumps = leafCover >= 1 ? sk.clumps : sk.clumps.filter(() => lrnd() < leafCover);
  if (!clumps.length) {
    // bare: the wood alone
  } else if (lod === 'far' || lod === 'distant') {
    // The crown as a few broad masses: clumps binned by bearing and height,
    // one card per bin sized to hold the bin's leaf area, so the silhouette
    // and the gaps between masses stay the tree's own.
    const bins = new Map();
    for (const c of clumps) {
      const rel = sub(c.at, centre);
      // A crown a few metres high is held by fewer masses (`farBins`, the dune
      // conifers): at the far ring it is a handful of pixels either way.
      // `distant` (T-2808): half the bearings and one band fewer.
      const [fSec, fBand] = arch.farBins ?? [6, 3];
      const [nSec, nBand] = lod === 'distant' ? [Math.max(3, fSec >> 1), Math.max(1, fBand - 1)] : [fSec, fBand];
      const sector = Math.floor(((Math.atan2(rel[2], rel[0]) + Math.PI) / (2 * Math.PI)) * nSec) % nSec;
      const band = Math.min(nBand - 1, Math.floor(clamp01((c.at[1] - sk.baseY) / sk.crownH) * nBand));
      const key = band === nBand - 1 && Math.hypot(rel[0], rel[2]) < sk.R * 0.35 ? 'cap' : `${sector}:${band}`;
      const g = bins.get(key) ?? { at: [0, 0, 0], area: 0, n: 0, dir: [0, 0, 0] };
      g.at = add(g.at, c.at);
      g.dir = add(g.dir, c.dir);
      g.area += c.r * c.r * leafScale * leafScale;
      g.n++;
      bins.set(key, g);
    }
    for (const g of bins.values()) {
      const at = mul(g.at, 1 / g.n);
      const { outward, colour, flex } = shade(at);
      // A card reaches about 0.6 of its size past its centre, so a big bin's
      // card is held inside the crown's own spread (1.1 R): a far tree is no
      // wider than its near self, and a bank tree hangs no further over the
      // water. What the cap takes off the one card, a second, crossed card
      // gives back.
      const want = Math.sqrt(g.area) * 1.45;
      const room = Math.max(sk.R * 0.35, (sk.R * 1.1 - Math.hypot(at[0], at[2])) / 0.6);
      const size = Math.min(want, room);
      // One card per mass, grown outward from the crown so it faces whoever is
      // looking at that side, set back by a third of its length so the mass is
      // centred on its bin, not hung outside it. The cap's card lies up.
      const d1 = norm(add(outward, [0, 0.35, 0]));
      card(leaves, sub(at, mul(d1, size * 0.35)), d1, size, clumpTile, colour, outward, flex, lrnd);
      if (size < want * 0.7) card(leaves, sub(at, mul(d1, size * 0.35)), d1, size, clumpTile, colour, outward, flex, lrnd);
    }
  } else {
    // Near: every clump as two sprays. Mid: every other clump as one card, a
    // little larger than a near spray, so the leaves on it stay near their true
    // size and the crown keeps most of its leaf area.
    let alt = 0;
    for (const c of clumps) {
      if (lod === 'mid' && (alt++ & 1)) continue;
      const { outward, colour, flex } = shade(c.at);
      if (lod === 'mid') {
        // Turned to face out of the crown, near square, so a card this size
        // reads as a spray from the street, not a blade seen edge-on.
        const facing = norm(add(outward, mul(randUnit(lrnd), 0.35)));
        card(leaves, c.at, c.dir, c.r * 2.2 * leafScale, clumpTile, colour, outward, flex, lrnd, facing);
      } else {
        for (let i = 0; i < 2; i++) {
          const jit = mul(randUnit(lrnd), c.r * 0.55);
          card(leaves, add(c.at, jit), c.dir, c.r * 1.5 * leafScale, i === 0 ? clumpTile : sunTile, colour, outward, flex, lrnd);
        }
      }
    }
  }
  return {
    wood: wood.build(0, conf),
    leaves: leaves.build(1, conf),
    height: sk.H,
    crownR: sk.R,
    trunkR: sk.dbh / 2,
    clumps: sk.clumps.length,
    skeleton: sk,
  };
}

/** Bark is tinted by the species' colour over a near-neutral tile. The tile
 *  carries its own furrow shading, so the tint is lifted to the bark's
 *  reflectance rather than the old dark placeholder pole (barkColour). */
function barkLinear(hex, kind) {
  const rgb = linearRGB(hex);
  const lum = rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
  // The tile carries the bark's value; the species colour only turns its hue,
  // so the tint is normalised to a luminance near one.
  const gain = 0.95 / Math.max(0.001, lum);
  const k = kind === 'sycamore' ? 1.1 : 1;
  // Two parts grey to one part the species' hue: the painted tile already
  // carries a bark's own brown-grey, and a full tint double-counts it.
  return rgb.map((v) => Math.min(1.6, (v * gain * 0.4 + 0.95 * 0.6) * k));
}

export function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
