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

/** T-2784: the open plain's shrubs draw their stems with fewer sides at the
 *  near level (the trunk's, the stems', the twigs'), since a cane is a few
 *  millimetres to a centimetre thick; the coarser levels are the shared ones. */
const PRAIRIE_SIDES = { near: [5, 4, 3, 0] };

/* -------------------------------------------------------------------------- */
/* the species' habits                                                         */
/* -------------------------------------------------------------------------- */

/**
 * The architecture of each species, as an open-grown or stand-grown tree of the
 * Chicago lake plain would carry it. Every number is a reconstruction bounded
 * by the species' ordinary habit; none is a measurement of a tree that stood.
 *
 *   crown     envelope: 'oval' | 'vase' | 'spread' | 'round' | 'column' | 'cone' | 'spire' | 'irregular'
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
 *   core      a SHEARED plant's solid body under its sprays, as a share of the crown's
 *             envelope (T-1934; the arborvitae cone, ball and standard): see solidCore
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
  // T-3017 — THE OPEN-GROWN AMERICAN ELM, the 1904 parkway's (`spec.arch`). The
  // owner, 2026-10-22, with two photographs of street elms: the grown crowns read
  // "as fans of leaves and not branches with variation". An open-grown elm is the
  // fountain everyone knows it by: a clear bole to about a third of its height,
  // where it breaks into two to four co-dominant stems that climb in a V, fork
  // again, and arch outward, the outer branches long and the twigs hanging in a
  // fringe below them, so the crown is widest near its top, flat-domed, and open
  // underneath where the limbs show. `elm` switches growSkeleton to growElm;
  // its numbers are the habit's, reconstructed (docs/LIBERTIES.md
  // L-elm-vase-3017).
  ulmus_americana_vase: {
    crown: 'elm', crownBase: 0.30, fork: 'decurrent', stems: [1, 1], scaffolds: [2, 4],
    limbAngle: 20, rise: 0.02, twist: 0.18, order2: [5, 46], order3: [4, 0], droop: 0.55,
    clump: 0.10, clumpMin: 0.62, density: 1.0, gaps: 0.30, leaf: 'elm', bark: 'interlaced',
    // `distant` keeps the stoutest stems (16 cm and more), so a background elm
    // is a stem or a V into its crown, not a post under a floating mass. The
    // 1904 spawn sees 500 far and 2,630 distant elms, so those levels leave out
    // what they cannot resolve (T-3032): mid under 4.5 cm, far under 10 cm on
    // three-sided wood. The phone's tier (`coarse`) also drops far under 12 cm.
    farBins: [8, 3], sides: { near: [10, 7, 4, 3], far: [3, 3, 0, 0], distant: [3, 3, 0, 0] },
    minRad: { mid: 0.045, far: 0.1, distant: 0.16 }, minRadCoarse: { far: 0.12 }, elm: true,
  },
  // T-3164 — A YOUNG PARKWAY ELM'S HEAD, before it vases. The 1894 Inland
  // conservatory plate and Lowe's c. 1897 print both show the parkway tree before
  // the 1800 Calumet gate as one straight leader running up through its crown, its
  // limbs leaving it from about 3 m and spreading wide and low in an open head
  // over the walk: the habit of an elm still on its central leader, not the
  // forked fountain of the grown street elm above. The habit is read off the two
  // pictures; these numbers are reconstructed (docs/LIBERTIES.md
  // L-pullman-18th-street-trees-1934). Only a pictured tree that names
  // `form: 'broad_head'` grows on it (street-trees.js).
  ulmus_americana_young: {
    crown: 'round', crownBase: 0.30, fork: 'excurrent', stems: [1, 1], scaffolds: [6, 8],
    limbAngle: 52, rise: 0.03, twist: 0.22, order2: [5, 46], order3: [3, 48], droop: 0.14,
    clump: 0.08, clumpMin: 0.45, density: 0.70, gaps: 0.50, leaf: 'elm', bark: 'interlaced',
    winter: 'fringe',
  },
  // T-1934 — THE SAME YOUNG ELM, LIMBED UP. Taylor's 16555, at 16 m, draws the tree at
  // 18th Street's Calumet corner as one slender leader clear to about 5 m before its
  // first limbs, and 16554 sees its crown start as high; the head above is the young
  // elm's. Only the crown base differs (docs/LIBERTIES.md
  // L-pullman-18th-street-trees-1934). A pictured tree names it as `form: 'limbed_head'`.
  ulmus_americana_young_limbed: {
    crown: 'round', crownBase: 0.44, fork: 'excurrent', stems: [1, 1], scaffolds: [6, 8],
    limbAngle: 52, rise: 0.03, twist: 0.22, order2: [5, 46], order3: [3, 48], droop: 0.14,
    clump: 0.08, clumpMin: 0.45, density: 0.70, gaps: 0.50, leaf: 'elm', bark: 'interlaced',
    winter: 'fringe',
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
  // T-2784 — THE OPEN PLAIN'S SHRUBS. The prairie's own are knee- to waist-high
  // and resprout from the root after every fire, so each is a low clump of
  // canes rather than a bush with a stem: wild rose a loose colony of thin
  // arching canes with pinnate leaves; New Jersey tea a tight dome of many
  // slender stems off a woody crown; leadplant a few grey wands. The slough
  // edge's are taller: pussy willow a clump of upright stems that branch, the
  // slender willow a sheaf of thin straight wands, buttonbush a rounded bush of
  // crooked spreading stems with broad glossy leaves, meadowsweet a stand of
  // upright wands. Small clumps (`clumpMin`) so a knee-high shrub's leaf is not
  // a tree's. Habits, not measurements (docs/LIBERTIES.md L-prairie-woody-2784).
  // `sides` (PRAIRIE_SIDES): a cane a centimetre thick is a few pixels at any
  // range a visitor stands from it, so the near level's wood is cut sides.
  rosa_spp: {
    crown: 'round', crownBase: 0.12, fork: 'decurrent', stems: [5, 8], scaffolds: [0, 0],
    stemSplay: 28, limbAngle: 20, rise: 0.0, twist: 0.35, order2: [3, 46], order3: [0, 0],
    droop: 0.22, clump: 0.30, clumpMin: 0.12, density: 1.20, gaps: 0.26, leaf: 'compound', bark: 'smooth',
    farBins: [3, 2], sides: PRAIRIE_SIDES,
  },
  ceanothus_americanus: {
    crown: 'round', crownBase: 0.16, fork: 'decurrent', stems: [7, 11], scaffolds: [0, 0],
    stemSplay: 20, limbAngle: 18, rise: 0.03, twist: 0.25, order2: [3, 42], order3: [0, 0],
    droop: 0.06, clump: 0.30, clumpMin: 0.12, density: 1.30, gaps: 0.18, leaf: 'elm', bark: 'smooth',
    farBins: [3, 2], sides: PRAIRIE_SIDES,
  },
  amorpha_canescens: {
    crown: 'round', crownBase: 0.20, fork: 'decurrent', stems: [4, 7], scaffolds: [0, 0],
    stemSplay: 16, limbAngle: 14, rise: 0.04, twist: 0.20, order2: [2, 40], order3: [0, 0],
    droop: 0.04, clump: 0.32, clumpMin: 0.10, density: 1.20, gaps: 0.24, leaf: 'compound', bark: 'smooth',
    farBins: [3, 2], sides: PRAIRIE_SIDES,
  },
  salix_discolor: {
    crown: 'irregular', crownBase: 0.10, fork: 'decurrent', stems: [4, 7], scaffolds: [0, 0],
    stemSplay: 16, limbAngle: 16, rise: 0.06, twist: 0.30, order2: [4, 36], order3: [0, 0],
    droop: 0.12, clump: 0.24, clumpMin: 0.30, density: 1.15, gaps: 0.24, leaf: 'willow', bark: 'smooth',
    farBins: [4, 2], sides: PRAIRIE_SIDES,
  },
  salix_petiolaris: {
    crown: 'round', crownBase: 0.08, fork: 'decurrent', stems: [8, 12], scaffolds: [0, 0],
    stemSplay: 13, limbAngle: 12, rise: 0.06, twist: 0.20, order2: [3, 30], order3: [0, 0],
    droop: 0.14, clump: 0.26, clumpMin: 0.24, density: 1.25, gaps: 0.20, leaf: 'willow', bark: 'smooth',
    farBins: [4, 2], sides: PRAIRIE_SIDES,
  },
  cephalanthus_occidentalis: {
    crown: 'round', crownBase: 0.14, fork: 'decurrent', stems: [3, 6], scaffolds: [0, 0],
    stemSplay: 24, limbAngle: 30, rise: 0.0, twist: 0.60, order2: [4, 50], order3: [0, 0],
    droop: 0.08, clump: 0.26, clumpMin: 0.28, density: 1.20, gaps: 0.26, leaf: 'heart', bark: 'smooth',
    farBins: [4, 2], sides: PRAIRIE_SIDES,
  },
  spiraea_alba: {
    crown: 'column', crownBase: 0.14, fork: 'decurrent', stems: [8, 13], scaffolds: [0, 0],
    stemSplay: 10, limbAngle: 10, rise: 0.04, twist: 0.15, order2: [2, 36], order3: [0, 0],
    droop: 0.04, clump: 0.28, clumpMin: 0.12, density: 1.30, gaps: 0.20, leaf: 'willow', bark: 'smooth',
    farBins: [3, 2], sides: PRAIRIE_SIDES,
  },
  // T-3223 — THE 1904 FRONT YARDS' GARDEN PLANTS (front-yards.js). The nursery
  // shrubs a Prairie Avenue yard was planted from in the 1890s: lilac, a tall
  // clump of grey upright stems with broad heart leaves; Van Houtte's spiraea,
  // a fountain of thin canes arching to the ground; the smooth hydrangea, a
  // low dome of soft stems carrying its white July heads; the garden rose; and
  // the American arborvitae, sheared to a cone or a ball. The bedding plants of
  // the round beds are grown on the same path at their own small size: the
  // scarlet geranium's mound of round leaves and umbels, and coleus. Habits, not measurements of a plant that
  // grew (docs/LIBERTIES.md L-prairie-front-yards-3203).
  syringa_vulgaris: {
    crown: 'irregular', crownBase: 0.16, fork: 'decurrent', stems: [6, 10], scaffolds: [0, 0],
    stemSplay: 13, limbAngle: 12, rise: 0.05, twist: 0.30, order2: [4, 34], order3: [2, 38],
    droop: 0.05, clump: 0.20, clumpMin: 0.26, density: 1.35, gaps: 0.16, leaf: 'heart', bark: 'smooth',
    farBins: [4, 2], sides: PRAIRIE_SIDES, stemK: 0.7,
  },
  spiraea_vanhouttei: {
    crown: 'round', crownBase: 0.04, fork: 'decurrent', stems: [12, 18], scaffolds: [0, 0],
    stemSplay: 38, limbAngle: 26, rise: -0.05, twist: 0.20, order2: [4, 42], order3: [0, 0],
    droop: 0.42, clump: 0.20, clumpMin: 0.13, density: 1.55, gaps: 0.10, leaf: 'elm', bark: 'smooth',
    farBins: [3, 2], sides: PRAIRIE_SIDES, stemK: 0.75,
  },
  hydrangea_arborescens: {
    crown: 'round', crownBase: 0.05, fork: 'decurrent', stems: [10, 15], scaffolds: [0, 0],
    stemSplay: 22, limbAngle: 18, rise: 0.02, twist: 0.20, order2: [3, 40], order3: [0, 0],
    droop: 0.10, clump: 0.26, clumpMin: 0.16, density: 1.55, gaps: 0.08, leaf: 'heart', bark: 'smooth',
    farBins: [3, 2], sides: PRAIRIE_SIDES, shellK: 6, stemK: 0.7,
  },
  rosa_garden: {
    crown: 'round', crownBase: 0.10, fork: 'decurrent', stems: [6, 9], scaffolds: [0, 0],
    stemSplay: 22, limbAngle: 18, rise: 0.01, twist: 0.35, order2: [3, 46], order3: [0, 0],
    droop: 0.14, clump: 0.26, clumpMin: 0.12, density: 1.45, gaps: 0.14, leaf: 'compound', bark: 'smooth',
    farBins: [3, 2], sides: PRAIRIE_SIDES, stemK: 0.7,
  },
  thuja_occidentalis: {
    crown: 'cone', crownBase: 0.02, fork: 'excurrent', stems: [1, 1], scaffolds: [30, 40],
    limbAngle: 62, rise: 0.10, twist: 0.20, order2: [3, 40], order3: [0, 0], droop: 0.0,
    clump: 0.26, clumpMin: 0.18, density: 2.0, gaps: 0.02, leaf: 'scale', bark: 'shaggy_strips',
    farBins: [3, 2], shellK: 22, core: 0.8,
  },
  // T-1934: arborvitae clipped to a column, as the Pullman palm house's terrace grows four
  // in Taylor's 16554 (and three in 16555): a dense dark shape near its full width up to about
  // two fifths of its height, then tapering to a blunt point, where the yard's cone is widest
  // at its foot. The same plant as the cone, sheared to another shape.
  thuja_column: {
    crown: 'spire', crownBase: 0.02, fork: 'excurrent', stems: [1, 1], scaffolds: [30, 40],
    limbAngle: 62, rise: 0.10, twist: 0.20, order2: [3, 40], order3: [0, 0], droop: 0.0,
    clump: 0.26, clumpMin: 0.18, density: 2.0, gaps: 0.02, leaf: 'scale', bark: 'shaggy_strips',
    farBins: [3, 2], shellK: 22, core: 0.8,
  },
  thuja_globe: {
    crown: 'round', crownBase: 0.03, fork: 'decurrent', stems: [5, 8], scaffolds: [0, 0],
    stemSplay: 30, limbAngle: 30, rise: 0.04, twist: 0.20, order2: [4, 44], order3: [0, 0], droop: 0.0,
    clump: 0.26, clumpMin: 0.15, density: 1.8, gaps: 0.02, leaf: 'scale', bark: 'shaggy_strips',
    farBins: [3, 2], sides: PRAIRIE_SIDES, shellK: 26, stemK: 0.6, core: 0.8,
  },
  // T-1934: an evergreen sheared to a ball on one clear stem, the tubbed standard of the
  // Pullman palm house's terrace in the 1894 Inland plate: the stem bare to about half the
  // plant's height, then a dense clipped head.
  standard_ball: {
    crown: 'ball', crownBase: 0.42, fork: 'decurrent', stems: [1, 1], scaffolds: [6, 8],
    limbAngle: 38, rise: 0.04, twist: 0.15, order2: [4, 44], order3: [0, 0], droop: 0.0,
    clump: 0.26, clumpMin: 0.15, density: 1.9, gaps: 0.02, leaf: 'scale', bark: 'smooth',
    farBins: [3, 2], sides: PRAIRIE_SIDES, shellK: 26, stemK: 0.5, core: 0.8, headK: 1.0,
  },
  // T-1934: a palm house's palm set out in its tub for the summer, as Taylor's 16555 shows
  // one on the Pullman terrace before the drum: a short stout stem and a head of long
  // pinnate fronds that leave it steeply and arch over (`rise` < 0 sags each frond), the
  // leaf carried along the fronds themselves, no twigs and no clipped shell.
  phoenix_tub: {
    crown: 'spread', crownBase: 0.04, fork: 'decurrent', stems: [1, 1], scaffolds: [18, 22],
    limbAngle: 60, rise: -0.42, twist: 0.04, order2: [0, 0], order3: [0, 0], droop: 0.0,
    clump: 0.09, clumpMin: 0.08, density: 4.2, gaps: 0.02, leaf: 'compound', bark: 'shaggy',
    farBins: [3, 2], sides: PRAIRIE_SIDES, shellK: 0, stemK: 0.3,
  },
  pelargonium_bed: {
    crown: 'round', crownBase: 0.06, fork: 'decurrent', stems: [6, 9], scaffolds: [0, 0],
    stemSplay: 28, limbAngle: 30, rise: 0.02, twist: 0.30, order2: [2, 46], order3: [0, 0],
    droop: 0.04, clump: 0.2, clumpMin: 0.07, density: 1.4, gaps: 0.04, leaf: 'heart', bark: 'smooth',
    farBins: [3, 2], sides: PRAIRIE_SIDES, shellK: 5, stemK: 0.55,
  },
};

/** A species with no habit of its own grows as the form its record names. */
const ARCH_OF_FORM = {
  gallery: 'fraxinus_pennsylvanica', open: 'quercus_alba', lean: 'salix_nigra',
  sub: 'ostrya_virginiana', columnar: 'populus_balsamifera', thicket: 'salix_interior',
};

export function archFor(spec) {
  // T-3017: a planter may name a habit outright (the parkway elm's vase).
  if (spec.arch && ARCH[spec.arch]) return ARCH[spec.arch];
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
/**
 * T-3017 — EACH LEAF TILE'S OPAQUE BOX: [u0, u1, v0, v1] in the tile's own units
 * (atlasUV's), measured from the committed atlas with 8 px to spare and printed
 * by `python3 tools/generate_tree_atlas.py --crops` (re-run it whenever the atlas
 * is regenerated). A spray fills about 60 % of its square tile's width, so a card
 * cut to this box covers about 30 % less area (measured over every species and
 * level), and the GPU shades and alpha-tests that many fewer fragments in the
 * colour pass and in the shadow map, for the same leaves in the same place.
 */
export const LEAF_CROP = [
  [0.148, 0.794, 0.002, 1.000], [0.088, 0.858, 0.138, 0.944], [0.224, 0.846, 0.002, 1.000], [0.000, 1.000, 0.124, 0.850],
  [0.198, 0.830, 0.002, 1.000], [0.010, 1.000, 0.108, 0.838], [0.200, 0.832, 0.002, 1.000], [0.060, 1.000, 0.138, 0.902],
  [0.106, 0.782, 0.002, 1.000], [0.000, 1.000, 0.106, 0.920], [0.164, 0.828, 0.002, 1.000], [0.000, 1.000, 0.098, 0.964],
  [0.190, 0.824, 0.002, 1.000], [0.000, 0.930, 0.012, 0.982], [0.204, 0.958, 0.002, 1.000], [0.066, 0.994, 0.084, 0.954],
  [0.378, 0.972, 0.000, 0.902], [0.000, 1.000, 0.100, 0.908], [0.204, 0.808, 0.002, 0.902], [0.102, 0.942, 0.094, 0.816],
];
const FULL_TILE = [0, 1, 0, 1];
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
    // T-1934: arborvitae clipped to a column: near its full width from a little over the
    // foot to about two fifths up, then drawn in to a blunt point (Taylor's 16554).
    case 'spire': return Math.pow(Math.min(1, (1 - t) / 0.6), 0.75) * (0.8 + 0.2 * Math.min(1, t / 0.2));
    case 'round': return Math.pow(Math.sin(Math.PI * (0.03 + t * 0.95)), 0.6);
    // T-1881: a head sheared to a true ball (a standard's), as round at its foot as at its top.
    case 'ball': return Math.sqrt(Math.max(0, 1 - (2 * t - 1) * (2 * t - 1))) * 0.98 + 0.02;
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
  if (arch.elm) return growElm(spec, arch, rnd);
  const H = lerp(spec.h[0], spec.h[1], 0.5 + (rnd() - 0.5) * 0.6);
  const dbh = lerp(spec.dbh?.[0] ?? H * 0.025, spec.dbh?.[1] ?? H * 0.035, rnd());
  const crownW = spec.crownW
    ? lerp(spec.crownW[0], spec.crownW[1], rnd())
    : H * (spec.spreadK ?? 0.6) * (0.88 + rnd() * 0.24);
  const R = crownW / 2;
  // A clipped standard's head is a ball (`headK`, its height over its width): the 1894 Inland
  // plate prints both of Pullman's boxed standards' heads as wide as they are tall, where a
  // fixed share of the plant's height drew the taller one's head half again as tall as wide.
  const baseY = arch.headK ? Math.max(H * 0.25, H - crownW * arch.headK)
    : H * arch.crownBase * (0.85 + rnd() * 0.3);
  const crownH = arch.headK ? H - baseY : Math.max(1, H - baseY);
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
      // T-3223: a garden shrub's stems run up through its crown (`stemK` of its height),
      // where the wild shrubs' stop at 0.8 m and branch, and a bedding plant is shorter than that.
      // A standard's clear stem runs on into the foot of its head, so no bare fork shows under it.
      const forkY = arch.headK ? baseY + crownH * 0.2
        : arch.stemK ? H * arch.stemK : Math.max(0.8, baseY * (nStems > 1 ? 0.55 : 0.92));
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
  // T-3223: a sheared or massed plant (the front yards' arborvitae, a bed's geraniums) is
  // all shell, so its habit asks for more of it (`shellK`).
  const shellN = Math.round((R * R * 0.9 + crownH * R * 0.3) * arch.density * 0.18 * SHELL_K * (arch.shellK ?? 1));
  for (let i = 0; i < shellN; i++) {
    const t = rnd();
    const az = rnd() * Math.PI * 2;
    const y = baseY + crownH * (0.15 + 0.82 * t);
    const er = envR([off[0] + Math.cos(az), y, off[2] + Math.sin(az)]) * (0.72 + rnd() * 0.24);
    const at = [off[0] + Math.cos(az) * er, y, off[2] + Math.sin(az) * er];
    if (rnd() < arch.gaps) continue;
    clumps.push({ at, dir: norm([Math.cos(az), 0.3, Math.sin(az)]), r: clumpR * (0.7 + rnd() * 0.4), shell: true });
  }
  // THE SHEARS (T-1881): a clipped plant (`core`) has nothing outside its clipped shape. Its
  // twigs, grown as any shrub's, reach past it (a 1.5 m ball's half-metre shoots carried leaf
  // out to 1.3 m from its stem, read in Kevin's phone shot of Pullman's boxed standards as
  // cards flying loose round the ball); so every twig and leaf mass is cut back inside the
  // envelope, the masses a little inside it so their cards lie on the clipped face.
  if (arch.core) {
    const clip = (p, k) => {
      const y = Math.min(H, Math.max(baseY + crownH * 0.04, p[1]));
      const dx = p[0] - off[0]; const dz = p[2] - off[2];
      const r = Math.hypot(dx, dz); const lim = envR([p[0], y, p[2]]) * k;
      const f = r > lim ? lim / r : 1;
      return [off[0] + dx * f, y, off[2] + dz * f];
    };
    // the stems too, where they run up into the clipped shape (a ball's splayed stems reach
    // out of it); a standard's clear stem under its head is left as it grew
    for (const b of branches) {
      for (let i = b.order === 0 ? 1 : 0; i < b.pts.length; i++) {
        if (b.order === 0 && b.pts[i][1] < baseY) continue;
        b.pts[i] = clip(b.pts[i], 0.97);
      }
    }
    for (const c of clumps) c.at = clip(c.at, 0.86);
  }
  return { H, dbh, R, baseY, crownH, centreY, off, branches, clumps, envR };
}

/**
 * T-3017 — THE OPEN-GROWN ELM (`ARCH.ulmus_americana_vase`). Grown as the habit
 * is drawn in every field guide and in the owner's two photographs: a clear bole,
 * a fork into two to four co-dominant stems that climb in a V and fork again,
 * every limb ARCHING (its angle from the vertical grows along it, so it leaves
 * the fork steep and ends reaching out), branches off the limbs that sweep out
 * and down, and twigs that HANG from them. The leaf is carried on the hanging
 * twigs and the branch ends, so the crown is a dome of foliage over an open
 * interior where the limbs show, fringed below by hanging sprays, and widest
 * near its top. Every child starts on its parent's own polyline inside the
 * parent's radius and no thicker, so no limb is cut off or hangs in the air.
 * The returned skeleton is the shape growSkeleton returns.
 */
function growElm(spec, arch, rnd) {
  const H = lerp(spec.h[0], spec.h[1], 0.5 + (rnd() - 0.5) * 0.6);
  const dbh = lerp(spec.dbh?.[0] ?? H * 0.025, spec.dbh?.[1] ?? H * 0.035, rnd());
  const R = H * (spec.spreadK ?? 0.8) * (0.9 + rnd() * 0.2) / 2;
  const forkY = H * arch.crownBase * (0.8 + rnd() * 0.35);
  // The leaf's own base: the hanging fringe comes down to about two fifths of
  // the height at the crown's edge. The far levels bin and shade from here.
  const baseY = Math.max(forkY + 0.5, H * 0.40);
  const crownH = Math.max(1, H - baseY);
  const centreY = baseY + crownH * 0.55;
  const leanA = rnd() * Math.PI * 2;
  const lean = (spec.lean ?? 0) * (0.5 + rnd() * 0.5);
  const off = [Math.cos(leanA) * R * 0.05, 0, Math.sin(leanA) * R * 0.05];
  const lobes = [rnd(), rnd()].map((v) => v * Math.PI * 2);
  // The envelope: narrow at the fork, widest about seven tenths up the crown,
  // a flattened dome over it.
  const envR = (p) => {
    const t = (p[1] - forkY) / Math.max(1, H - forkY);
    if (t < -0.05 || t > 1.02) return 0;
    const tt = clamp01(t);
    const r = tt <= 0.72 ? 0.18 + 0.82 * Math.pow(Math.sin((tt / 0.72) * Math.PI / 2), 0.8)
      : Math.sqrt(Math.max(0, 1 - ((tt - 0.72) / 0.31) ** 2));
    const az = Math.atan2(p[2] - off[2], p[0] - off[0]);
    return R * r * (1 + 0.10 * (Math.sin(az * 2 + lobes[0]) * 0.6 + Math.sin(az * 3 + lobes[1]) * 0.4));
  };
  const branches = [];
  const clumps = [];
  const LIM = R * 1.06;

  /** A limb that arches: its angle from the vertical runs a0 -> a1 along it
   *  (`bend` > 1 keeps it steep longer), its bearing wandering a little. */
  function arc(start, az, a0, a1, L, r0, r1, order, { bend = 1.4, wander = arch.twist } = {}) {
    // A twig is two strokes, a branch up to six, a limb up to ten.
    const n = Math.max(2, Math.min(order >= 3 ? 2 : order === 2 ? 6 : 10, Math.round(L / Math.max(0.45, r0 * 6))));
    const pts = [start];
    const rad = [r0];
    let p = start;
    let b = az;
    for (let i = 1; i <= n; i++) {
      const t = i / n;
      const a = a0 + (a1 - a0) * Math.pow((i - 0.5) / n, bend);
      b += (rnd() - 0.5) * wander * 0.6;
      const d = norm(add([Math.sin(a) * Math.cos(b), Math.cos(a), Math.sin(a) * Math.sin(b)],
        mul(randUnit(rnd), wander * 0.10)));
      p = add(p, mul(d, L / n));
      // The crown's reach: a limb running past it slows its outward run and
      // bows down, as a long elm limb does under its own leaf, rather than
      // stopping at a wall; nothing grows over the top.
      const dx = p[0] - off[0];
      const dz = p[2] - off[2];
      const rr = Math.hypot(dx, dz);
      if (rr > LIM) {
        const k = (LIM + (rr - LIM) * 0.35) / rr;
        p = [off[0] + dx * k, p[1] - (rr - LIM) * 0.25, off[2] + dz * k];
      }
      if (p[1] > H) p = [p[0], H - rnd() * 0.25, p[2]];
      pts.push(p);
      rad.push(lerp(r0, r1, Math.pow(t, 0.85)));
    }
    const br = { pts, rad, order, az, a0, a1, L };
    branches.push(br);
    return br;
  }
  /** Where a branch is at `t` of its length: the point, radius, direction, and
   *  that direction's angle from the vertical and bearing. */
  function along(br, t) {
    const seg = clamp01(t) * (br.pts.length - 1);
    const k = Math.min(br.pts.length - 2, Math.floor(seg));
    const f = seg - k;
    const at = add(br.pts[k], mul(sub(br.pts[k + 1], br.pts[k]), f));
    const dir = norm(sub(br.pts[k + 1], br.pts[k]));
    return { at, r: lerp(br.rad[k], br.rad[k + 1], f), dir,
      theta: Math.acos(Math.max(-1, Math.min(1, dir[1]))), az: Math.atan2(dir[2], dir[0]) };
  }
  /** A limb's length for its tip to rise `dy`, given how it arches. */
  function lengthFor(dy, a0, a1, bend) {
    let c = 0;
    for (let i = 0; i < 8; i++) c += Math.cos(a0 + (a1 - a0) * Math.pow((i + 0.5) / 8, bend));
    return dy / Math.max(0.25, c / 8);
  }
  const D = Math.PI / 180;

  /* the bole, to the fork */
  const r0 = dbh / 2;
  const trunk = arc([0, 0, 0], leanA, lean * 0.5, lean, forkY / Math.cos(lean), r0, r0 * 0.80, 0, { bend: 1, wander: 0.04 });
  const top = trunk.pts[trunk.pts.length - 1];
  const topR = r0 * 0.80;

  /* the co-dominant stems: a V of two to four, each climbing and arching out */
  const nLead = arch.scaffolds[0] + Math.floor(rnd() * (arch.scaffolds[1] - arch.scaffolds[0] + 1));
  const azBase = rnd() * Math.PI * 2;
  const limbs = [];
  for (let i = 0; i < nLead; i++) {
    const az = azBase + (i / nLead) * Math.PI * 2 + (rnd() - 0.5) * 0.7;
    const a0 = (arch.limbAngle * (nLead === 2 ? 0.85 : 0.8) + (rnd() - 0.5) * 10) * D;
    const a1 = (66 + rnd() * 20) * D;
    const L = lengthFor(H * (0.80 + rnd() * 0.12) - forkY, a0, a1, 2.0);
    // Pipe model, roughly: the stems' cross-sections make up the bole's. The
    // first starts at the bole's top at its full section; the others leave a
    // little below it, inside the bole.
    const lr = i === 0 ? topR * 0.86 : topR * (0.62 + rnd() * 0.16) / Math.sqrt(Math.max(1, (nLead - 1) / 1.6));
    const start = add(top, [0, -(i === 0 ? topR * 0.4 : topR * (1.0 + rnd() * 1.4)), 0]);
    limbs.push(arc(start, az, a0, a1, L, lr, lr * 0.16, 1, { bend: 2.0, wander: 0.32 }));
  }
  /* each forks once low, and the forks again: the vase's repeated V */
  const forks = (lb, t0, t1, p, spread, k, climbP) => {
    if (rnd() > p) return null;
    const t = lerp(t0, t1, rnd());
    const w = along(lb, t);
    const side = rnd() < 0.5 ? -1 : 1;
    // Half the forks climb steeper than their limb, into the middle of the vase,
    // and arch over it; the rest run out wider. So the crown is one dome, not
    // a mass on each arm of a Y.
    const climb = rnd() < climbP;
    const a0 = climb ? Math.max(3 * D, w.theta - (14 + rnd() * 14) * D) : Math.min(w.theta + (6 + rnd() * 10) * D, 70 * D);
    const a1 = climb ? (34 + rnd() * 26) * D : Math.max(a0 + 8 * D, lb.a1 + (rnd() * 14) * D);
    const L = lb.L * (1 - t) * (0.85 + rnd() * 0.25);
    const az = lb.az + side * spread * (climb ? 0.5 : 1) * (0.7 + rnd() * 0.6);
    return arc(w.at, az, a0, a1, L, w.r * k, w.r * k * 0.2, 1, { bend: 1.3, wander: 0.32 });
  };
  // The first fork on each stem climbs (the middle of the vase is filled from
  // the start); later ones go either way.
  for (const [t0, t1, p, spread, k, climbP] of [[0.26, 0.44, 0.95, 0.62, 0.80, 1], [0.48, 0.66, 0.75, 0.55, 0.72, 0.4],
    [0.68, 0.84, 0.45, 0.50, 0.66, 0.4]]) {
    for (const lb of [...limbs]) {
      const f = forks(lb, t0, t1, p, spread, k, climbP);
      if (f) limbs.push(f);
    }
  }

  /* the branches: out and down off every limb's upper reach */
  const second = [];
  for (const lb of limbs) {
    const n = Math.max(2, Math.min(9, Math.round((lb.L / 1.6) * (0.8 + rnd() * 0.4) * arch.order2[0] / 5)));
    for (let i = 0; i < n; i++) {
      const t = lerp(0.30, 0.97, (i + 0.2 + rnd() * 0.6) / n);
      const w = along(lb, t);
      // Mostly to the limb's outer side and its flanks; a few climb inward to
      // fill the dome.
      const inward = rnd() < 0.28;
      const az = lb.az + (inward ? Math.PI + (rnd() - 0.5) * 1.2 : (rnd() - 0.5) * 2.6);
      const a0 = inward ? (10 + rnd() * 25) * D : Math.min(w.theta + (arch.order2[1] - 16 + rnd() * 18) * D, 75 * D);
      const a1 = (inward ? 70 + rnd() * 20 : 100 + rnd() * 28) * D;
      const L = R * (0.34 + rnd() * 0.28) * (inward ? 0.8 : 1.0) * (0.75 + 0.35 * t);
      const br0 = Math.min(w.r * 0.55, 0.10);
      second.push(arc(w.at, az, a0, a1, L, br0, Math.max(0.008, br0 * 0.18), 2, { bend: 1.7 }));
    }
  }
  /* the hanging twigs */
  const third = [];
  for (const b of second) {
    const n = Math.round(arch.order3[0] * (0.7 + rnd() * 0.6));
    for (let i = 0; i < n; i++) {
      const t = lerp(0.25, 1.0, (i + rnd()) / n);
      const w = along(b, t);
      const az = b.az + (rnd() - 0.5) * 1.8;
      const a0 = (75 + rnd() * 30) * D;
      const a1 = (140 + rnd() * 30) * D;
      const L = (0.9 + rnd() * 1.4) * (0.7 + 0.5 * t) * arch.droop / 0.55;
      third.push(arc(w.at, az, a0, a1, L, Math.max(0.006, Math.min(w.r * 0.6, 0.022)), 0.005, 3, { bend: 1.2, wander: 0.2 }));
    }
  }

  /* the leaf: on the hanging twigs and the outer half of each branch */
  const clumpR = Math.max(arch.clumpMin ?? 0.7, R * arch.clump);
  const carry = (b, t0, hang) => {
    const n = Math.max(1, Math.round(b.L * arch.density * ELM_FOLIAGE_K / Math.max(0.5, clumpR)));
    for (let i = 0; i < n; i++) {
      if (rnd() < arch.gaps * 0.5) continue;
      const w = along(b, lerp(t0, 1.0, (i + rnd()) / n));
      clumps.push({ at: w.at, dir: w.dir, r: clumpR * (0.7 + rnd() * 0.5), hang });
    }
  };
  for (const b of third) carry(b, 0.35, true);
  for (const b of second) carry(b, 0.55, false);
  for (const b of limbs) carry(b, 0.78, false);
  // The dome: short upright twigs off the upper wood, each carrying its leaf,
  // fill the top of the crown where the hanging sprays leave it thin. They
  // grow from the wood, so no leaf floats free of a branch.
  const upper = [...limbs, ...second].filter((b) => b.pts[b.pts.length - 1][1] > forkY + (H - forkY) * 0.45);
  const shellN = Math.round(R * R * arch.density * ELM_DOME_K);
  for (let i = 0; i < shellN && upper.length; i++) {
    const b = upper[Math.floor(rnd() * upper.length)];
    const w = along(b, 0.45 + rnd() * 0.55);
    if (w.at[1] < forkY + (H - forkY) * 0.4) continue;
    const out = Math.atan2(w.at[2] - off[2], w.at[0] - off[0]);
    const tw = arc(w.at, out + (rnd() - 0.5) * 1.6, (15 + rnd() * 35) * D, (50 + rnd() * 40) * D,
      0.8 + rnd() * 1.2, Math.max(0.006, Math.min(w.r * 0.5, 0.02)), 0.005, 3, { bend: 1.2, wander: 0.2 });
    if (rnd() < arch.gaps) continue;
    const e = along(tw, 0.7 + rnd() * 0.3);
    clumps.push({ at: e.at, dir: e.dir, r: clumpR * (0.8 + rnd() * 0.4), shell: true });
  }
  return { H, dbh, R, baseY, crownH, centreY, off, branches, clumps, envR, elm: true };
}

/** T-3017: the elm's leaf per metre of carrying wood, and the dome's fill per
 *  square metre of crown. */
const ELM_FOLIAGE_K = 2.3;
const ELM_DOME_K = 1.4;

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
/** T-2784: the leaf atlas's mean opaque texel is a pale green (sRGB 145, 165,
 *  125, measured over all twenty tiles, alpha over half), and a flower drawn
 *  on a leaf tile multiplies that cast in. This is its mean over each channel,
 *  so a bloom's vertex colour comes back to the record's. */
const BLOOM_CAST = [1.02, 0.77, 1.40];
const SHELL_K = 7.0;
/** T-3223 — the solid garden blooms (`bloom.shape`): how many florets make one, how far it
 *  stands up off its clump (in radii), how squat it is, its sphere's segments near, and the
 *  share of the upper clumps that carry one. */
const BLOOM_SHAPES = {
  umbel: { florets: 3, lift: 1.4, squash: 0.9, segs: [4, 3], share: 0.6 },
  head: { florets: 6, lift: 0.5, squash: 0.8, segs: [5, 3], share: 0.5 },
  cup: { florets: 3, lift: 0.3, squash: 0.7, segs: [5, 3], share: 0.75 },
};
/** The pale bark texel a solid bloom is drawn off is about this dark (linear), so its
 *  vertex colour is lifted by this much to come back to the flower's. */
const BLOOM_FLAT_GAIN = 2.6;
/** T-1934 — a sheared plant's solid body (solidCore): [sides, rings] at each level. The far
 *  level is the one that needs it most: there a sheared column is a handful of binned cards
 *  with its stem showing between them (the Pullman terrace's four, from Taylor's eye over
 *  70 m off). A `distant` shrub is not drawn at all. */
const CORE_SEGS = { near: [8, 8], mid: [6, 5], far: [5, 4] };

/**
 * T-1934 — A BARE CROWN'S TWIGS AT THE COARSE LEVELS. The `mid` and `far` levels leave
 * out the wood a summer crown covers (the third order, and anything thinner than the
 * level's `minRad`), because their leaf cards stand where it is. A winter crown has no
 * cards, so it was left a trunk and a few long limbs: Taylor's 16554 prints the parkway
 * elms at 15-70 m as dense fringes of fine twig, and the render drew them as poles and
 * sticks. So a bare crown at those levels draws the wood it was missing, as single
 * three-sided strokes held to at least `floor` metres of radius (a twig the level's ring
 * would otherwise show at under a pixel, so the antialiased fringe greys in as the
 * print's does), skipped limbs first, then branches, then a share of the twigs taken
 * evenly round the crown. `perClump` is its triangle budget per summer clump, which keeps
 * the bare tree at or under what the same level draws in leaf (measured over the elms,
 * oaks, ash, maple, cottonwood and willow: mid's leaf is 1.0-1.25 triangles a clump,
 * far's 0.04-0.22), so winter costs no more than summer.
 */
const BARE_TWIGS = { mid: { floor: 0.010, perClump: 1.0, segs: 2 }, far: { floor: 0.04, perClump: 0.04, segs: 1 } };

function bareTwigs(buf, sk, { floor, perClump, segs, spike: spikeR = 0, budget: given }, drawn, barkTile, tint, flexOf, rnd) {
  let budget = given ?? Math.floor(sk.clumps.length * perClump);
  const byOrder = [[], [], [], []];
  for (const b of sk.branches) if (b.order > 0 && !b.fringe && !drawn(b)) byOrder[Math.min(3, b.order)].push(b);
  // The twigs are taken evenly round the crown (shuffled once from the template's seed),
  // the rising ones first: a twig hangs under its leaf, and a bare one, seen as a single
  // chord from its foot to its tip, would cross the crown as a downward slash.
  const shuffled = (list) => {
    for (let i = list.length - 1; i > 0; i--) {
      const j = Math.floor(rnd() * (i + 1));
      [list[i], list[j]] = [list[j], list[i]];
    }
    return list;
  };
  const rises = (b) => b.pts[b.pts.length - 1][1] >= b.pts[0][1];
  const twigs = [...shuffled(byOrder[3].filter(rises)), ...shuffled(byOrder[3].filter((b) => !rises(b)))];
  for (const b of [...byOrder[1], ...byOrder[2], ...twigs]) {
    if (spikeR) {
      // A winter elm's skipped wood (T-1934): one spike from its foot to its tip, as its fringe.
      if (b.pts.length < 2 || budget < 3) continue;
      spike(buf, b, Math.max(spikeR, b.rad[0]), barkTile, tint, flexOf);
      budget -= 3;
      continue;
    }
    const n = Math.min(b.pts.length - 1, b.order >= 3 ? 1 : segs);
    if (n < 1 || budget < n * 6) continue;
    const pts = [];
    const rad = [];
    for (let i = 0; i <= n; i++) {
      const k = Math.round((i / n) * (b.pts.length - 1));
      pts.push(b.pts[k]);
      rad.push(Math.max(floor, b.rad[k]));
    }
    tube(buf, { ...b, pts, rad }, 3, barkTile, tint, flexOf);
    budget -= n * 6;
  }
  return budget;
}

/**
 * T-1934 — THE GROWN ELM'S WINTER HABIT. growElm grows the summer crown: its branches run
 * out and droop under their leaf, and the twigs off them hang, because they carry the
 * hanging sprays. Bare, that skeleton drew as long straight strokes at the drooping angles
 * crossing one another, with a few hundred hanging twigs, where Taylor's winter 16554 prints
 * the elms on both parkways as limbs that fork again and again into fine ascending twig, a
 * dense fringe at each crown's rim; the young elms on their leaders (`winter: 'fringe'`, the
 * nearest trees in that print) drew the same way. So a bare elm (Season: winter) is drawn on its winter
 * skeleton: the bole, the stems or leader and their forks as summer's; each branch only as far as it
 * rises (its drooping tail is where the summer leaf hung); none of the summer's hanging
 * twigs; and, off every limb's tip and along every branch's kept run, a sprout that forks
 * `depth` times into short ascending twig (`angle` degrees off the vertical, each fork
 * `forkK` of its parent's length), held inside the crown's reach (a young elm's leader sprouts
 * at its top too). The habit is read off the
 * print; the numbers are reconstructed (docs/LIBERTIES.md L-tree-architecture-2743).
 * Summer, spring and fall never see it: it is built only when no clump is in leaf.
 */
const ELM_WINTER = { droopDeg: 82, along: [0.45, 0.75, 1.0], depth: 3, rootL: [1.0, 1.8], forkK: 0.64,
  angle: [14, 40], twigR: 0.004 };

function winterElm(sk, rnd) {
  const D = Math.PI / 180;
  const W = ELM_WINTER;
  const kept = [];
  const groups = [];
  const lim = sk.R * 1.12;
  const inCrown = (p) => {
    const dx = p[0] - sk.off[0];
    const dz = p[2] - sk.off[2];
    const rr = Math.hypot(dx, dz);
    const k = rr > lim ? lim / rr : 1;
    return [sk.off[0] + dx * k, Math.min(p[1], sk.H + 0.4), sk.off[2] + dz * k];
  };
  const dirOf = (theta, az) => [Math.sin(theta) * Math.cos(az), Math.cos(theta), Math.sin(theta) * Math.sin(az)];
  // One twig: two strokes curling a little upward, then its forks off its tip.
  const twig = (group, at, az, theta, L, r, level) => {
    // A twig stops short of the crown's top and its reach rather than bending along them.
    const room = Math.min(sk.H + 0.4 - at[1], lim - Math.hypot(at[0] - sk.off[0], at[2] - sk.off[2]) + 0.6);
    L = Math.min(L, room / Math.max(0.5, Math.cos(theta)));
    if (L < 0.25) return;
    const curl = Math.max(4 * D, theta - (3 + rnd() * 9) * D);
    const mid = inCrown(add(at, mul(norm(add(dirOf(theta, az), mul(randUnit(rnd), 0.10))), L * 0.5)));
    const end = inCrown(add(mid, mul(dirOf(curl, az + (rnd() - 0.5) * 0.3), L * 0.5)));
    const rEnd = Math.max(W.twigR, r * 0.6);
    group.push({ pts: [at, mid, end], rad: [r, (r + rEnd) / 2, rEnd], order: 3, az, a0: theta, a1: curl, L,
      fringe: true, level });
    if (level >= W.depth) return;
    const n = rnd() < 0.3 ? 3 : 2;
    for (let i = 0; i < n; i++) {
      // A V: one arm a little steeper than its parent, one a little wider, a third between.
      const side = i === 0 ? -1 : i === 1 ? 1 : (rnd() - 0.5) * 0.6;
      const cth = Math.min(W.angle[1] * 1.4 * D, Math.max(6 * D, curl + side * (6 + rnd() * 12) * D));
      twig(group, end, az + side * (0.30 + rnd() * 0.45), cth, L * W.forkK * (0.85 + rnd() * 0.3),
        Math.max(W.twigR, rEnd * 0.8), level + 1);
    }
  };
  const sprout = (w, az) => {
    const group = [];
    const theta = (W.angle[0] + rnd() * (W.angle[1] - W.angle[0])) * D;
    twig(group, w.at, az + (rnd() - 0.5) * 1.2, theta, W.rootL[0] + rnd() * (W.rootL[1] - W.rootL[0]),
      Math.max(W.twigR, Math.min(w.r * 0.6, 0.02)), 0);
    groups.push(group);
  };
  const tip = (b) => {
    const n = b.pts.length - 1;
    const d = norm(sub(b.pts[n], b.pts[n - 1]));
    return { at: b.pts[n], r: b.rad[n], dir: d };
  };
  // A branch's bearing: growElm keeps it; the generic skeleton's, off its foot and tip.
  const bearing = (b) => b.az ?? Math.atan2(b.pts[b.pts.length - 1][2] - b.pts[0][2], b.pts[b.pts.length - 1][0] - b.pts[0][0]);
  for (const b of sk.branches) {
    if (b.order >= 3) continue;
    if (b.order < 2) {
      kept.push(b);
      // Every limb's tip, and a leader's that runs up into the crown (the young elm's).
      if (b.order === 1 || b.pts[b.pts.length - 1][1] > sk.baseY) sprout(tip(b), b.order === 0 ? rnd() * Math.PI * 2 : bearing(b));
      continue;
    }
    // A branch as far as it rises: cut where a stroke first turns past `droopDeg`.
    let k = b.pts.length - 1;
    for (let i = 1; i < b.pts.length; i++) {
      if (norm(sub(b.pts[i], b.pts[i - 1]))[1] < Math.cos(W.droopDeg * D)) { k = Math.max(1, i - 1); break; }
    }
    const run = { ...b, pts: b.pts.slice(0, k + 1), rad: b.rad.slice(0, k + 1) };
    if (run.pts.length < 2) continue;
    kept.push(run);
    for (const t of W.along) {
      const seg = t * (run.pts.length - 1);
      const j = Math.min(run.pts.length - 2, Math.floor(seg));
      const f = seg - j;
      sprout({ at: add(run.pts[j], mul(sub(run.pts[j + 1], run.pts[j]), f)), r: lerp(run.rad[j], run.rad[j + 1], f) }, bearing(b));
    }
  }
  return { ...sk, branches: [...kept, ...groups.flat()], fringe: groups };
}

/** The winter elm's fringe, sprout by sprout (a sprout is drawn whole or not at all, so no
 *  twig floats free of its fork), taken evenly round the crown within `budget` triangles:
 *  each twig as `segs` three-sided strokes, its forks to `depth`, held to `floor` metres.
 *
 *  T-1934 — `spike`: at the mid ring (10-44 m, where most of Taylor's 16554's parkway elms
 *  stand) a twig is under a pixel wide, and the stroke's six triangles bought it nothing a
 *  pyramid's three do not: so there each twig is one three-sided spike from its foot to its
 *  tip, its foot `spike` metres across at least (twice the stroke's floor, so a tapering
 *  twig covers about what the even stroke did), and the summer leaf's budget draws twice
 *  the twigs. The crowns at that ring had a few dozen strokes a tree against the print's
 *  hundreds.
 *
 *  T-1934 — at the far ring (past 44 m) the skipped wood spent the whole budget and no fringe
 *  twig was drawn at all: there `reserve` of the budget is kept for the fringe, each twig a
 *  spike at least `spike` metres across at its foot (a pixel near the ring's edge). */
const ELM_FRINGE = { near: { segs: 2, depth: 3, floor: 0 }, mid: { segs: 1, depth: 1, floor: 0.010, spike: 0.020 },
  far: { segs: 1, depth: 0, floor: 0.04, spike: 0.08, reserve: 0.5 } };

/** T-1934 — one twig as a three-sided pyramid: a ring of three at its foot (`r` across at
 *  least its own radius) and its tip, each face lit by its own outward normal. Three
 *  triangles where `tube` spends six on one segment. */
function spike(buf, b, r, barkTile, tint, flexOf) {
  const a = b.pts[0];
  const tip = b.pts[b.pts.length - 1];
  const t = norm(sub(tip, a));
  const u = norm(cross(t, Math.abs(t[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]));
  const w = cross(t, u);
  const at = (k) => add(mul(u, Math.cos((k / 3) * Math.PI * 2)), mul(w, Math.sin((k / 3) * Math.PI * 2)));
  const ao = (p, nrm) => 0.72 + 0.28 * clamp01((p[1] + 1.5) / 6) * (0.80 + 0.20 * (nrm[1] * 0.5 + 0.5));
  const base = buf.count;
  for (let s = 0; s < 3; s++) {
    const nrm = at(s);
    const p = add(a, mul(nrm, r));
    buf.vert(p, nrm, mul(tint, ao(p, nrm)), atlasUV(BARK_GRID, barkTile, s / 3, 0), flexOf(p));
  }
  for (let s = 0; s < 3; s++) {
    // The tip once per face, carrying that face's normal, so the faces stay apart in the light.
    const nrm = at(s + 0.5);
    buf.vert(tip, nrm, mul(tint, ao(tip, nrm)), atlasUV(BARK_GRID, barkTile, (s + 0.5) / 3, 1), flexOf(tip));
  }
  for (let s = 0; s < 3; s++) buf.tri(base + s, base + ((s + 1) % 3), base + 3 + s);
}

function drawFringe(buf, groups, budget, { segs, depth, floor, spike: spikeR = 0 }, barkTile, tint, flexOf, rnd) {
  const order = groups.map((g, i) => i);
  for (let i = order.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  const drawn = [];
  for (const gi of order) {
    const twigs = groups[gi].filter((b) => b.level <= depth);
    const cost = spikeR ? twigs.length * 3 : twigs.reduce((c, b) => c + Math.min(segs, b.pts.length - 1) * 6, 0);
    if (cost > budget) continue;
    for (const b of twigs) {
      if (spikeR) {
        spike(buf, b, Math.max(spikeR, b.rad[0]), barkTile, tint, flexOf);
        continue;
      }
      const n = Math.min(segs, b.pts.length - 1);
      const pts = [];
      const rad = [];
      for (let i = 0; i <= n; i++) {
        const k = Math.round((i / n) * (b.pts.length - 1));
        pts.push(b.pts[k]);
        rad.push(Math.max(floor, b.rad[k]));
      }
      tube(buf, { ...b, pts, rad }, 3, barkTile, tint, flexOf);
    }
    budget -= cost;
    drawn.push(gi);
  }
  // T-1934: what is left once every sprout is drawn to `depth` goes on the next fork, sprout by
  // sprout in the same order (spikes only), so a crown at the mid ring spends its summer leaf's
  // budget and every new twig grows off a drawn one.
  if (spikeR && drawn.length === groups.length) {
    for (const gi of drawn) {
      const next = groups[gi].filter((b) => b.level === depth + 1);
      if (!next.length || next.length * 3 > budget) continue;
      for (const b of next) spike(buf, b, Math.max(spikeR, b.rad[0]), barkTile, tint, flexOf);
      budget -= next.length * 3;
    }
  }
  return budget;
}

// `distant` (T-2808): the trunk alone, three-sided, under a crown of a few masses.
const SIDES ={ near: [10, 7, 5, 3], mid: [6, 4, 3, 0], far: [4, 3, 0, 0], distant: [3, 0, 0, 0] };

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

/** T-3223: a solid bloom, a small low sphere squashed by `sy`, drawn with the wood off one
 *  flat texel of the smooth bark tile. */
/**
 * T-1934 — A SHEARED PLANT'S BODY. Clipped arborvitae is a solid mass of scale leaf: the
 * shears leave no sky through it, and from the street it reads as one dense dark shape.
 * Grown as sprays alone it read as an open stack of small clumps with the stem showing
 * between them (Taylor's 16554, where the Pullman palm house terrace's four clipped columns
 * print as dense dark cones 10-14 px wide and the render drew them 8-10 px of scattered
 * clumps). So the habit's `core` stands a closed body of the crown's own envelope, `k` of its
 * radius, under the shell's sprays: the sprays still make the edge, and what shows between
 * them is the plant's own shaded interior instead of the wall behind it. It is drawn with the
 * wood (opaque, no cut-out) off the same flat bark texel as a solid bloom, so its vertex
 * colour is its own, and it sways with the leaf at its height. Closed at its foot and apex.
 */
function solidCore(buf, sk, k, colour, [seg, rings], flexAt) {
  const uv = atlasUV(BARK_GRID, BARK_TILES.smooth, 0.5, 0.5);
  const base = buf.count;
  const y0 = sk.baseY + sk.crownH * 0.02;
  const y1 = sk.baseY + sk.crownH * 0.97;
  const step = (y1 - y0) / rings;
  const rAt = (y, ph) => sk.envR([sk.off[0] + Math.cos(ph), y, sk.off[2] + Math.sin(ph)]) * k;
  // Top ring first, as blob() turns its rings, so the faces wind the same way.
  for (let j = 0; j <= rings; j++) {
    const y = y1 - step * j;
    const up = clamp01((y - sk.baseY) / sk.crownH);
    for (let i = 0; i <= seg; i++) {
      const ph = (i / seg) * Math.PI * 2;
      const end = j === 0 || j === rings;
      const r = end ? 0 : rAt(y, ph);
      const dr = (rAt(Math.min(y1, y + step * 0.5), ph) - rAt(Math.max(y0, y - step * 0.5), ph)) / step;
      const n = j === 0 ? [0, 1, 0] : j === rings ? [0, -1, 0] : norm([Math.cos(ph), -dr, Math.sin(ph)]);
      const shade = 0.82 + 0.18 * up;
      buf.vert([sk.off[0] + Math.cos(ph) * r, y, sk.off[2] + Math.sin(ph) * r], n, mul(colour, shade), uv, flexAt(up));
    }
  }
  for (let j = 0; j < rings; j++) {
    for (let i = 0; i < seg; i++) {
      const a = base + j * (seg + 1) + i;
      const b = a + seg + 1;
      buf.tri(a, a + 1, b);
      buf.tri(a + 1, b + 1, b);
    }
  }
}

function blob(buf, at, r, sy, colour, [seg, rings], flex) {
  const uv = atlasUV(BARK_GRID, BARK_TILES.smooth, 0.5, 0.5);
  const base = buf.count;
  for (let j = 0; j <= rings; j++) {
    const th = (j / rings) * Math.PI;
    for (let i = 0; i <= seg; i++) {
      const ph = (i / seg) * Math.PI * 2;
      const n = [Math.sin(th) * Math.cos(ph), Math.cos(th), Math.sin(th) * Math.sin(ph)];
      const shade = 0.78 + 0.22 * (n[1] * 0.5 + 0.5);
      buf.vert([at[0] + n[0] * r, at[1] + n[1] * r * sy, at[2] + n[2] * r], n, mul(colour, shade), uv, flex);
    }
  }
  for (let j = 0; j < rings; j++) {
    for (let i = 0; i < seg; i++) {
      const a = base + j * (seg + 1) + i;
      const b = a + seg + 1;
      buf.tri(a, a + 1, b);
      buf.tri(a + 1, b + 1, b);
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
  // T-3017: the quad is cut to the tile's opaque box (LEAF_CROP), in the tile's
  // own units, so every leaf stands exactly where the whole tile put it and the
  // GPU no longer shades and alpha-tests the empty margin round each spray.
  const [u0, u1, v0, v1] = LEAF_CROP[tile] ?? FULL_TILE;
  const cardN = norm(cross(side, t));
  const n = norm(add(mul(outward, 0.78), mul(cardN, 0.22 * (rnd() < 0.5 ? 1 : -1))));
  for (const [tu, tv] of [[u0, v0], [u1, v0], [u1, v1], [u0, v1]]) {
    const cu = flip ? 0.5 - tu : tu - 0.5;
    const cv = tv - 0.15;
    const p = add(at, add(mul(side, cu * w), mul(t, cv * h)));
    buf.vert(p, n, colour, atlasUV(LEAF_GRID, tile, tu, tv), flex + tv * 0.18);
  }
  buf.tri(base, base + 1, base + 2);
  buf.tri(base, base + 2, base + 3);
}

/**
 * T-3017 — THE ELM'S LEAF. An elm carries its leaves in flat two-ranked sprays
 * on twigs that hang, so a clump on a hanging twig is a SPRAY (the single-twig
 * tile, never the massed clump's fan) hung from where it grows: its length runs
 * down the twig and it faces out of the crown, with a second spray at the near
 * level lying nearly flat, as the sprays are held, so from under the tree the
 * leaf is a layered ceiling and not blades seen edge-on. The dome's clumps and
 * the branch ends take the massed tile, faced out. `mid` draws one spray for
 * most clumps (ELM_SHARE), each scaled to carry the leaf of the ones it stands
 * for, so a crown down the street is twigs of leaves with sky between them
 * rather than a few big fans; `far` a few large sprays grown out of the crown.
 */
function elmCards(leaves, c, lod, { outward, colour, flex }, leafScale, sunTile, clumpTile, lrnd, share = 1) {
  const out = norm([outward[0], 0, outward[2]]);
  // Faced out of the crown and tipped to the ground, so a spray shows its face
  // both to the street and to a visitor standing under it.
  const tipped = (k) => norm(add(add(out, [0, -k, 0]), mul(randUnit(lrnd), 0.3)));
  // A coarser level carries a share of the clumps on cards scaled to hold the
  // leaf of the ones it stands for.
  const k = 1 / Math.sqrt(share);
  if (lod === 'far') {
    // Few and large: each card is centred on its clump and grown up and out
    // of the crown, so a far spray does not hang below the tree's own leaf.
    const size = c.r * (c.hang ? 1.45 : 1.7) * k * 0.8 * leafScale;
    const up = norm([out[0], 0.6, out[2]]);
    card(leaves, sub(c.at, mul(up, size * 0.35)), up, size, c.hang ? sunTile : clumpTile, colour, outward, flex, lrnd, tipped(0.4));
    return;
  }
  if (c.hang) {
    const size = c.r * 1.45 * k * leafScale;
    card(leaves, c.at, c.dir, size, sunTile, colour, outward, flex, lrnd, tipped(0.45));
    if (lod === 'near') {
      const flat = norm(add([0, 1, 0], mul(add(out, mul(randUnit(lrnd), 0.4)), 0.8)));
      card(leaves, add(c.at, mul(randUnit(lrnd), c.r * 0.4)), c.dir, size * 0.95, sunTile, colour, outward, flex, lrnd, flat);
    }
    return;
  }
  if (lod !== 'near') {
    card(leaves, c.at, c.dir, c.r * 1.7 * k * leafScale, clumpTile, colour, outward, flex, lrnd, tipped(0.6));
    return;
  }
  card(leaves, c.at, c.dir, c.r * 1.5 * leafScale, clumpTile, colour, outward, flex, lrnd, tipped(0.3));
  const flat = norm(add([0, 1, 0], mul(out, 0.6)));
  card(leaves, add(c.at, mul(randUnit(lrnd), c.r * 0.5)), c.dir, c.r * 1.4 * leafScale, sunTile, colour, outward, flex, lrnd, flat);
}
/** The share of an elm's clumps each level draws (T-3017); `coarse`, the
 *  phone's tier, draws fewer, larger sprays, the same leaf area on fewer cards.
 *  Far is 0.02, not 0.05 (T-3032): the 1904 spawn sees 500 far elms, and at 0.05
 *  they took its frame to 4,603,239 triangles, over the 4.6M ceiling. */
const ELM_SHARE = { near: 1, mid: 0.62, far: 0.02 };
const ELM_SHARE_COARSE = { near: 1, mid: 0.40, far: 0.02 };

/**
 * Build a species template at one level of detail. The skeleton is grown from
 * `seed`, so the same seed gives the same tree at every level.
 *
 * @returns {{ wood: THREE.BufferGeometry, leaves: THREE.BufferGeometry, height: number,
 *             crownR: number, trunkR: number }}
 */
export function buildTreeTemplate(spec, seed, lod = 'near', { conf = 0.5, skeleton = null, leafCover = 1, leafScale = 1,
  coarse = false } = {}) {
  if (spec.form === 'vine_drape') return buildVineTemplate(spec, seed, lod, { conf });
  if (spec.form === 'vine_wall') return buildWallVineTemplate(spec, seed, lod, { conf, leafCover });
  const rnd = mulberry32(seed);
  const arch = archFor(spec);
  // T-2810: a dead tree is its species' skeleton, grown whole and then broken.
  const sk = skeleton ?? (spec.dead
    ? deadSkeleton(growSkeleton(spec, arch, rnd), spec.dead, mulberry32(seed ^ 0x2810))
    : growSkeleton(spec, arch, rnd));
  // T-1934: a bare elm stands on its winter skeleton (winterElm), grown once per skeleton
  // and shared by its levels; every other crown, and every elm in leaf, on its own.
  const wintry = leafCover <= 0 && (sk.elm || arch.winter === 'fringe') && !spec.dead && sk.clumps.length > 0;
  const wsk = wintry ? (sk.winter ??= winterElm(sk, mulberry32(seed ^ 0x1934e))) : sk;
  const lrnd = mulberry32(seed ^ 0x9e3779b9);
  const wood = new Buf();
  const leaves = new Buf();
  const sides = arch.sides?.[lod] ?? SIDES[lod] ?? SIDES.near;
  const barkTile = BARK_TILES[arch.bark] ?? 0;
  const barkTint = barkLinear(spec.bark ?? 0x5a5246, arch.bark);
  const barkUpper = spec.barkUpper != null ? barkLinear(spec.barkUpper, arch.bark) : barkTint;
  // Dead wood does not sway in the wind as a leafy crown does, and a log on the
  // ground does not move at all (T-2810).
  const stiff = spec.dead === 'log' ? 0 : spec.dead ? 0.35 : 1;
  const flexOf = (p) => clamp01((p[1] / Math.max(1, sk.H)) * 0.55 + Math.hypot(p[0], p[2]) / Math.max(1, sk.R) * 0.25) * 0.6 * stiff;
  // Coarser levels walk every second (mid) or fourth (far) node of a limb:
  // the same limb, in fewer, longer segments.
  const stride = lod === 'near' ? 1 : lod === 'mid' ? 2 : lod === 'far' ? 4 : 8;
  const minRad = (coarse ? arch.minRadCoarse?.[lod] : null) ?? arch.minRad?.[lod]
    ?? (lod === 'near' ? 0 : lod === 'mid' ? 0.03 : 0.07);
  // A shrub's stems are all thinner than that, which would leave its coarse
  // levels with no wood at all: a batch geometry of zero vertices, which the
  // drawn-timber census cannot read back. Its stoutest stem stays.
  let keep = null;
  if (minRad > 0 && !wsk.branches.some((b) => sides[Math.min(3, b.order)] && b.rad[0] >= minRad)) {
    for (const b of wsk.branches) if (b.order === 0 && (!keep || b.rad[0] > keep.rad[0])) keep = b;
  }
  // The triangles the main pass spends on a skeleton's wood (the winter elm's fringe is
  // drawn apart, within its budget, below).
  const woodTris = (branches) => branches.reduce((n, b) => {
    const s = sides[Math.min(3, b.order)];
    if (!s || b.fringe || (b.rad[0] < minRad && b !== keep)) return n;
    return n + (b.pts.length - 1) * s * 2;
  }, 0);
  for (const b of wsk.branches) {
    const s = sides[Math.min(3, b.order)];
    if (!s || b.fringe) continue;
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
  const elmShare = coarse ? ELM_SHARE_COARSE : ELM_SHARE;
  if (!clumps.length) {
    // bare: the wood alone, and at the coarse levels the twigs the leaf hid (T-1934)
    if (sk.clumps.length && !spec.dead && !arch.core && (BARE_TWIGS[lod] || (wintry && ELM_FRINGE[lod]))) {
      const brnd = mulberry32(seed ^ 0x1934);
      // A winter elm's branches are cut to their rising run, so one stroke draws each and
      // what that saves goes to the fringe.
      // T-1934: a bare elm at mid and far spends what its own summer leaf there costs (one
      // two-triangle card for each clump the level keeps, elmShare), never less than the bare
      // crown's share, and draws its skipped wood as spikes (three triangles a stroke, not six);
      // at far it keeps `reserve` of that budget back for its fringe, which the skipped wood
      // otherwise spent to the last triangle (the far ring drew no fringe twig at all).
      const F = wintry && lod !== 'near' ? ELM_FRINGE[lod] : null;
      const total = F ? Math.floor(sk.clumps.length * Math.max(BARE_TWIGS[lod].perClump, sk.elm ? elmShare[lod] * 2 : 0)) : 0;
      const kept = F ? Math.floor(total * (F.reserve ?? 0)) : 0;
      let left = BARE_TWIGS[lod] ? bareTwigs(wood, wsk, F ? { ...BARE_TWIGS[lod], segs: 1, spike: F.spike, budget: total - kept }
        : wintry ? { ...BARE_TWIGS[lod], segs: 1 } : BARE_TWIGS[lod],
        (b) => sides[Math.min(3, b.order)] && (b.rad[0] >= minRad || b === keep), barkTile, barkUpper, flexOf, brnd) + kept : 0;
      // The winter elm's fringe: at mid and far, in what the bare twigs left of the summer
      // leaf's budget; near, in the near leaf's own triangles (two sprays a clump) and the
      // wood the winter skeleton gave up (the hanging twigs, the branches' tails).
      if (wintry && ELM_FRINGE[lod]) {
        // (less the one empty leaf triangle a bare template still carries)
        if (lod === 'near') left = sk.clumps.length * 4 * elmShare.near + woodTris(sk.branches) - woodTris(wsk.branches) - 1;
        drawFringe(wood, wsk.fringe, left, ELM_FRINGE[lod], barkTile, barkUpper, flexOf, brnd);
      }
    }
  } else if (sk.elm && lod === 'far') {
    // T-3017: the elm's far crown is its own sprays, a few and large, not a
    // ring of binned fans: at the far ring's near edge it still fills a third
    // of a phone's screen.
    for (const c of clumps) {
      if (lrnd() > elmShare.far) continue;
      elmCards(leaves, c, lod, shade(c.at), leafScale, sunTile, clumpTile, lrnd, elmShare.far);
    }
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
    // T-3017: an elm's crown is wide and open, and a bin holding a few strays at
    // its edge would be a lone card in the sky; its leaf is the crown's, not lost.
    const strays = sk.elm ? clumps.length * 0.025 : 0;
    for (const g of bins.values()) {
      if (g.n < strays) continue;
      const at = mul(g.at, 1 / g.n);
      const { outward, colour, flex } = shade(at);
      // A card reaches about 0.6 of its size past its centre, so a big bin's
      // card is held inside the crown's own spread (1.1 R): a far tree is no
      // wider than its near self, and a bank tree hangs no further over the
      // water. What the cap takes off the one card, a second, crossed card
      // gives back.
      const want = Math.sqrt(g.area) * 1.45;
      // An elm's leaf is all at its crown's rim, where that cap would shrink every
      // mass to a scrap: its masses are held to the crown's reach instead.
      const room = sk.elm ? sk.R * 0.9 : Math.max(sk.R * 0.35, (sk.R * 1.1 - Math.hypot(at[0], at[2])) / 0.6);
      // T-1934: a sheared plant's masses are its body's texture, not its outline: held to
      // its own clipped face, so no spray stands out of the shape the shears left.
      const size = arch.core ? Math.min(want, room, sk.R * 0.7) : Math.min(want, room);
      // One card per mass, grown outward from the crown so it faces whoever is
      // looking at that side, set back by a third of its length so the mass is
      // centred on its bin, not hung outside it. The cap's card lies up.
      const d1 = norm(add(outward, [0, 0.35, 0]));
      card(leaves, sub(at, mul(d1, size * 0.35)), d1, size, clumpTile, colour, outward, flex, lrnd);
      if (size < want * 0.7 && !arch.core) card(leaves, sub(at, mul(d1, size * 0.35)), d1, size, clumpTile, colour, outward, flex, lrnd);
    }
  } else {
    // Near: every clump as two sprays. Mid: every other clump as one card, a
    // little larger than a near spray, so the leaves on it stay near their true
    // size and the crown keeps most of its leaf area.
    let alt = 0;
    for (const c of clumps) {
      if (sk.elm) {
        if (lod === 'mid' && lrnd() > elmShare.mid) continue;
        elmCards(leaves, c, lod, shade(c.at), leafScale, sunTile, clumpTile, lrnd, elmShare[lod]);
        continue;
      }
      if (lod === 'mid' && (alt++ & 1)) continue;
      const { outward, colour, flex } = shade(c.at);
      // T-1934: a sheared plant's sprays are smaller, so they stay on its clipped face
      // over its body (solidCore) and do not make it shaggy.
      const ks = arch.core ? 0.65 : 1;
      if (lod === 'mid') {
        // Turned to face out of the crown, near square, so a card this size
        // reads as a spray from the street, not a blade seen edge-on.
        const facing = norm(add(outward, mul(randUnit(lrnd), 0.35)));
        card(leaves, c.at, c.dir, c.r * 2.2 * leafScale * ks, clumpTile, colour, outward, flex, lrnd, facing);
      } else {
        for (let i = 0; i < 2; i++) {
          const jit = mul(randUnit(lrnd), c.r * 0.55 * ks);
          card(leaves, add(c.at, jit), c.dir, c.r * 1.5 * leafScale * ks, i === 0 ? clumpTile : sunTile, colour, outward, flex, lrnd);
        }
      }
    }
  }
  // T-1934: a sheared plant's body under its sprays (solidCore), at the near, mid and far
  // levels, so the gaps between them show its shaded interior and not what is behind it.
  const coreSegs = CORE_SEGS[lod];
  if (arch.core && clumps.length && coreSegs) {
    // Its leaf's own colour a little into the shade: Taylor's 16554 prints the terrace's
    // columns at about half the lit stone's value behind them.
    const cc = dark.map((v, j) => lerp(v, light[j], 0.5) * 1.3 * BLOOM_FLAT_GAIN);
    solidCore(wood, sk, arch.core, cc, coreSegs, (up) => 0.45 + 0.4 * up);
  }
  // T-2784 — A PRAIRIE SHRUB IN FLOWER (`bloom`, its record's July
  // inflorescence: the rose's pink, New Jersey tea's and meadowsweet's white,
  // the leadplant's violet, the buttonbush's cream balls), hung on the outer
  // clumps of the upper crown at the two near levels, blossoms a few
  // centimetres across that the far levels could not resolve. The leaf atlas
  // is a pale green, so the colour is set against its cast (`BLOOM_CAST`) to
  // come out the record's and not a green-grey.
  const bloom = spec.bloom;
  if (bloom && Array.isArray(bloom.rgb) && (lod === 'near' || lod === 'mid') && clumps.length) {
    const brnd = mulberry32(seed ^ 0x2784b);
    const [br, bg, bb] = bloom.rgb;
    const bc = linearRGB((br << 16) | (bg << 8) | bb).map((v, j) => v * LEAF_GAIN * BLOOM_CAST[j]);
    const low = clamp01((bloom.height_frac ?? 0.8) - 0.35);
    const size = ((bloom.size_m?.[0] ?? 0.04) + (bloom.size_m?.[1] ?? 0.08)) * (lod === 'near' ? 1.3 : 2.2);
    let alt = 0;
    // T-3223: a garden flower with a shape of its own is a solid bloom, not a leaf spray
    // tinted: a geranium's umbel of florets on its stalk, a hydrangea's round white head,
    // a rose. They are drawn with the wood (no cut-out), off one flat texel of the pale
    // bark tile, so the vertex colour is the flower's.
    const shaped = BLOOM_SHAPES[bloom.shape];
    const share = shaped?.share ?? 0.55;
    for (const c of clumps) {
      if (c.at[1] < sk.H * low || brnd() > share) continue;
      if (lod === 'mid' && (alt++ & 1)) continue;
      const rel = sub(c.at, centre);
      const outward = norm(add(norm([rel[0], rel[1] * 0.6, rel[2]]), [0, 0.6, 0]));
      const at = add(c.at, mul(outward, c.r * 0.55));
      if (!shaped) {
        card(leaves, at, outward, size, sunTile, bc, outward, 0.5, brnd, outward);
        continue;
      }
      const r = (bloom.size_m[0] + (bloom.size_m[1] - bloom.size_m[0]) * brnd()) / 2;
      const fc = linearRGB((br << 16) | (bg << 8) | bb).map((v) => v * BLOOM_FLAT_GAIN * (0.85 + brnd() * 0.3));
      const top = add(at, [0, shaped.lift * r, 0]);
      const segs = lod === 'near' ? shaped.segs : [4, 3];
      if (shaped.florets) {
        for (let f = 0; f < shaped.florets; f++) {
          const o = mul(randUnit(brnd), r * 0.55);
          blob(wood, add(top, [o[0], Math.abs(o[1]) * 0.5, o[2]]), r * 0.55, 0.9, fc, segs, 0.55);
        }
      } else blob(wood, top, r, shaped.squash, fc, segs, 0.55);
    }
  }
  // A bare template (a dead tree, a winter crown) still hands the leaf batch
  // one triangle, of no area, at its foot: a batch entry of no vertices is one
  // the drawn-timber census cannot read back (tools/drawn_timber_census.mjs).
  if (!leaves.count) {
    for (let i = 0; i < 3; i++) leaves.vert([0, 0.05, 0], [0, 1, 0], [0, 0, 0], [0.5, 0.5], 0);
    leaves.tri(0, 1, 2);
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

/* -------------------------------------------------------------------------- */
/* dead wood and vines (T-2810)                                                */
/* -------------------------------------------------------------------------- */

/**
 * T-2810 — A DEAD TREE, STANDING (`snag`) OR DOWN (`log`), from its species'
 * own grown skeleton: the twigs gone, most of the small limbs gone, the big
 * limbs broken off short, and the stem snapped below its top. A log is the same
 * wreck laid along +X on the ground, its root end at the origin, with the limbs
 * that would have gone into the ground broken off by the fall. What a dead tree
 * of 1812 or 1835 looked like is no witness's; the breakage is this file's
 * (docs/LIBERTIES.md L-deadwood-vines-2810).
 *
 * The skeleton's `H` is the height the template is scaled by: the snapped
 * stem's top for a snag, and the length on the ground for a log.
 */
function deadSkeleton(sk, kind, rnd) {
  const fallen = kind === 'log';
  const cutY = sk.H * (fallen ? lerp(0.45, 0.70, rnd()) : lerp(0.55, 0.85, rnd()));
  // How much of a limb is left, by order: a snag keeps stubs of its scaffolds
  // and a few of their branches; a log keeps short stubs only.
  const keepOf = { 1: fallen ? [0.15, 0.40] : [0.30, 0.75], 2: [0.35, 0.70] };
  const branches = [];
  for (const b of sk.branches) {
    if (b.order >= 3) continue;
    if (b.order === 2 && (fallen || rnd() > 0.30)) continue;
    let n = b.pts.length;
    if (b.order > 0) {
      const [lo, hi] = keepOf[b.order];
      n = Math.max(2, Math.round(n * lerp(lo, hi, rnd())));
    }
    // Nothing stands above the break.
    const over = b.pts.findIndex((p, i) => i < n && p[1] > cutY);
    if (over === 0 || over === 1) continue;
    if (over > 1) n = over;
    branches.push({ ...b, pts: b.pts.slice(0, n), rad: b.rad.slice(0, n) });
  }
  // `H` stays the living tree's height: the planter scales a stem by its height
  // over the template's, and a snag of a 20 m tree is that tree's girth, not a
  // 14 m tree's stretched to 20.
  if (!fallen) return { ...sk, branches, clumps: [] };
  // Down: the stem's axis (+Y) laid along +X, lifted so the trunk rests on the
  // ground, and every limb that would now be under it broken off in the fall.
  const lift = sk.dbh * 0.42;
  const down = [];
  for (const b of branches) {
    const pts = b.pts.map((p) => [p[1], lift - p[0], p[2]]);
    if (b.order > 0 && pts.some((p) => p[1] < -0.15)) continue;
    down.push({ ...b, pts });
  }
  return { ...sk, branches: down, clumps: [] };
}

/** Per level of detail: how many anchors to step over, and the card's size
 *  against the anchor spacing. Coarser levels carry the same curtain on fewer,
 *  larger cards, as a tree's levels do. */
const VINE_LOD = { near: [1, 1.5], mid: [2, 2.6], far: [4, 4.6], distant: [8, 8.6] };
/** T-3223: the wall ivy's leaf spacing at each level, metres. */
const VINE_SPACING = { near: 0.16, mid: 0.26, far: 0.5, distant: 1.0 };

/**
 * T-2810 — A VINE ON AN EDGE TREE, built in the tree's frame with its open
 * side to +X (trees.js turns +X toward the water or the shade).
 *
 * `habit` 'curtain' is the riverbank grape (z05: "heavy curtain vine on the
 * river-facing edge trees"): a sheet of leaf hung over the crown's edge from
 * near the top to a ragged hem, curving back into the crown at its sides.
 * 'trunk' is the Virginia creeper ("climbing the trunks on the shaded side"):
 * a narrow column on the bole. The anchors are laid out once from the seed, so
 * every level hangs the same curtain and only the grain changes.
 */
export function buildVineTemplate(spec, seed, lod = 'near', { conf = 0.5 } = {}) {
  const rnd = mulberry32(seed);
  const lrnd = mulberry32(seed ^ 0x9e3779b9);
  const curtain = spec.habit !== 'trunk';
  const H = (spec.h[0] + spec.h[1]) / 2;
  const W = curtain ? H * (0.42 + rnd() * 0.20) : Math.max(1.0, H * 0.10);
  const s0 = curtain ? 0.75 : 0.45;
  const cols = Math.max(2, Math.round(W / s0));
  // The hem, a smooth random walk across the curtain: festoons and gaps, never
  // a ruled bottom edge.
  const hem = [];
  let hv = rnd();
  for (let c = 0; c <= cols; c++) { hv = clamp01(hv + (rnd() - 0.5) * 0.45); hem.push(hv); }
  const anchors = [];
  for (let c = 0; c <= cols; c++) {
    const u = (c / cols) * 2 - 1;
    const z = u * W * 0.5;
    const x = curtain ? -u * u * W * 0.32 : 0;
    const yTop = H * (curtain ? 1 - 0.20 * u * u : 0.62 + 0.10 * rnd());
    const yBot = curtain ? lerp(0.5, H * 0.50, hem[c]) : lerp(0.3, H * 0.20, hem[c]);
    const rows = Math.max(1, Math.round((yTop - yBot) / s0));
    for (let r = 0; r <= rows; r++) {
      const y = yTop - (r / rows) * (yTop - yBot);
      // Alternate rows sit half a column over, so the sheet has no vertical slots.
      const zr = z + (r % 2 ? s0 * 0.5 : 0) + (rnd() - 0.5) * s0 * 0.4;
      anchors.push({ c, r, at: [x + (rnd() - 0.5) * 0.35, y, zr], up: (y - yBot) / Math.max(0.5, yTop - yBot) });
    }
  }
  const [stride, k] = VINE_LOD[lod] ?? VINE_LOD.near;
  const leaves = new Buf();
  const wood = new Buf();
  const [sunTile, clumpTile] = LEAF_TILES[spec.leaf] ?? LEAF_TILES.heart;
  const dark = linearRGB(spec.dark ?? 0x56763c);
  const light = linearRGB(spec.light ?? 0x7f9b5a);
  for (const a of anchors) {
    if (a.c % stride || a.r % stride) continue;
    // Brighter high on the curtain and on its outer face, as a crown's shell is.
    // A curtain is one leaf deep and hangs in its host's shade: it takes less of
    // the light colour than a crown's shell does.
    const lit = clamp01(0.15 + 0.45 * a.up);
    const tint = 0.86 + lrnd() * 0.26;
    const colour = dark.map((v, j) => lerp(v, light[j], 0.25 + lit * 0.7) * lerp(0.72, 1, lit) * tint * LEAF_GAIN);
    const facing = norm([1, (lrnd() - 0.5) * 0.3, (lrnd() - 0.5) * 0.5]);
    const tile = lod === 'near' && lrnd() < 0.5 ? sunTile : clumpTile;
    // Hung from the anchor: the card's length runs down, the way the sprays fall.
    card(leaves, a.at, [0, -1, 0], s0 * k, tile, colour, norm([1, 0.25, 0]), 0.25 + 0.35 * a.up, lrnd, facing);
  }
  // The record's July fruit (the grape's "hard green fruit"), hung in its band
  // of the curtain at the two near levels: clusters a hand long, which the far
  // levels could not resolve.
  const bunch = spec.berries;
  if (bunch && Array.isArray(bunch.rgb) && (lod === 'near' || lod === 'mid')) {
    const frnd = mulberry32(seed ^ 0x2810f);
    const [fr, fg, fb] = bunch.rgb;
    const fc = linearRGB((fr << 16) | (fg << 8) | fb).map((v) => v * LEAF_GAIN);
    const band = bunch.height_frac ?? 0.6;
    const fs = ((bunch.size_m?.[0] ?? 0.06) + (bunch.size_m?.[1] ?? 0.12)) * (lod === 'near' ? 1.4 : 2.4);
    for (const a of anchors) {
      if (a.c % stride || a.r % stride) continue;
      if (Math.abs(a.at[1] / H - band) > 0.17 || frnd() > 0.45) continue;
      card(leaves, add(a.at, [0.12, -0.2, 0]), [0, -1, 0], fs, clumpTile, fc, [1, 0, 0], 0.3, frnd, [1, 0, 0]);
    }
  }
  // The vine's own stems: a few ropes hung from the top of the curtain (one at
  // the coarse levels, so the wood batch is never empty).
  const strands = lod === 'near' ? 4 : lod === 'mid' ? 2 : 1;
  const barkTile = BARK_TILES.shaggy_strips;
  const barkTint = barkLinear(spec.bark ?? 0x6b5a48, 'shaggy');
  for (let i = 0; i < strands; i++) {
    const c = Math.round(((i + 0.5) / strands) * cols);
    const u = (c / cols) * 2 - 1;
    const z = u * W * 0.5;
    const x0 = curtain ? -u * u * W * 0.32 : 0;
    const yTop = H * (curtain ? 0.92 - 0.20 * u * u : 0.6);
    const yBot = curtain ? Math.max(0.2, lerp(0.5, H * 0.5, hem[c]) - 0.6) : 0.1;
    const pts = [];
    const rad = [];
    for (let j = 0; j <= 5; j++) {
      const t = j / 5;
      // A slack rope bellies out from the curtain.
      // Hung just behind the leaf, so the ropes show through the gaps, not as poles.
      pts.push([x0 - 0.2 + Math.sin(t * Math.PI) * 0.45, lerp(yTop, yBot, t), z + Math.sin(t * Math.PI * 2) * 0.3]);
      rad.push(lerp(0.035, 0.025, t));
    }
    tube(wood, { pts, rad, order: 1 }, lod === 'near' ? 5 : 3, barkTile, barkTint, () => 0.2);
  }
  return {
    wood: wood.build(0, conf),
    leaves: leaves.build(1, conf),
    height: H,
    crownR: W / 2,
    trunkR: 0.035,
    clumps: anchors.length,
    skeleton: { vine: true },
  };
}

/**
 * T-3223 — IVY ON A HOUSE WALL (front-yards.js): Boston ivy as the Detroit Publishing
 * views of the Pullman house show it, a mat of three-lobed leaves held flat against
 * the wall, thick at the foot, thinning upward to a ragged top, its edges loose, with a
 * few woody stems climbing out of the ground under it. Built in the wall's frame: the
 * wall is the plane x = 0, the leaves stand off it toward +x (the instance's yaw turns
 * +x out of the wall), z runs along it; `crownW` is its width and `h` its height.
 * T-1881: `arch: 'mantle'` is a stretch a picture shows wholly clothed (Pullman's ground
 * storey under its balcony in LC-D4-12551): the same mat, its top held near `h` with only
 * short tongues, so a row of overlapping patches reads as one level-topped mantle;
 * `mantle_sill` is the same mat kept under a window's sill in such a stretch.
 */
export function buildWallVineTemplate(spec, seed, lod = 'near', { conf = 0.5, leafCover = 1 } = {}) {
  const rnd = mulberry32(seed);
  const lrnd = mulberry32(seed ^ 0x3223);
  const H = (spec.h[0] + spec.h[1]) / 2;
  const W = spec.crownW ? (spec.crownW[0] + spec.crownW[1]) / 2 : Math.max(1.2, H * 0.4);
  // The top edge, a smooth random walk: tongues of ivy climbing ahead of the mat.
  const TOP_COLS = 12;
  const mantle = spec.arch === 'mantle' || spec.arch === 'mantle_sill';
  const [topFloor, edgeFloor] = mantle ? [0.88, 0.9] : [0.6, 0.7];
  const top = [];
  let tv = rnd();
  for (let c = 0; c <= TOP_COLS; c++) { tv = clamp01(tv + (rnd() - 0.5) * 0.55); top.push(tv); }
  const topAt = (u) => {
    const f = ((u + 1) / 2) * TOP_COLS; const c = Math.min(TOP_COLS - 1, Math.floor(f));
    return lerp(top[c], top[c + 1], f - c);
  };
  const [sunTile, clumpTile] = LEAF_TILES[spec.leaf] ?? LEAF_TILES.maple;
  const dark = linearRGB(spec.dark ?? 0x2f4a22);
  const light = linearRGB(spec.light ?? 0x6d8f3e);
  const sp = VINE_SPACING[lod] ?? VINE_SPACING.near;
  const leaves = new Buf();
  const wood = new Buf();
  // Two layers, as a wall of Boston ivy is seen: a dense, shaded under-mat of massed leaf
  // close on the brick, and over it the sunlit leaves held out on their stalks, shingled,
  // each turned its own way, so the mat has no rows and the wall shows only at the edges.
  const layers = lod === 'near' || lod === 'mid'
    ? [{ step: sp * 1.7, size: sp * 3.2, off: [0.02, 0.05], tile: clumpTile, lit: [0.05, 0.3], keep: 1 },
      { step: sp, size: sp * 2.3, off: [0.06, 0.16], tile: sunTile, lit: [0.3, 0.75], keep: 0.9 }]
    : [{ step: sp, size: sp * 2.6, off: [0.04, 0.12], tile: clumpTile, lit: [0.15, 0.6], keep: 1 }];
  for (const L of layers) {
    const cols = Math.max(2, Math.round(W / L.step));
    const rows = Math.max(2, Math.round(H / L.step));
    for (let c = 0; c <= cols; c++) {
      for (let r = 0; r <= rows; r++) {
        const u = clamp01((c + (lrnd() - 0.5) * 0.9) / cols) * 2 - 1;
        const y = ((r + (lrnd() - 0.5) * 0.9) / rows) * H;
        const edge = 1 - Math.pow(Math.abs(u), 5);
        const yTop = H * (topFloor + (1 - topFloor) * topAt(u)) * (edgeFloor + (1 - edgeFloor) * edge);
        if (y < 0 || y > yTop) continue;
        const up = y / H;
        // Thinner toward the ragged top and the loose side edges.
        const fringe = Math.min(1, (yTop - y) / (L.step * 2.5));
        if (lrnd() > L.keep * (0.35 + 0.65 * fringe) * (0.5 + 0.5 * edge) * leafCover) continue;
        const at = [lerp(L.off[0], L.off[1], lrnd()), y, u * W * 0.5];
        const lit = clamp01(lerp(L.lit[0], L.lit[1], lrnd()) + 0.15 * up);
        const tint = 0.86 + lrnd() * 0.28;
        const colour = dark.map((v, j) => lerp(v, light[j], 0.15 + lit * 0.75) * lerp(0.7, 1, lit) * tint * LEAF_GAIN);
        // A leaf's stalk is below its blade; each turned its own way in the wall's plane.
        const th = (lrnd() - 0.5) * Math.PI * 1.4;
        const facing = norm([1, (lrnd() - 0.3) * 0.5, (lrnd() - 0.5) * 0.5]);
        card(leaves, at, [0.25, Math.cos(th), Math.sin(th)], L.size * (0.85 + lrnd() * 0.35), L.tile, colour,
          [1, 0.15, 0], 0.12 + 0.2 * up, lrnd, facing);
      }
    }
  }
  const strands = lod === 'near' ? 3 : 1;
  const barkTile = BARK_TILES.shaggy_strips;
  const barkTint = barkLinear(spec.bark ?? 0x6b5a48, 'shaggy');
  for (let i = 0; i < strands; i++) {
    const z0 = ((i + 0.5) / strands - 0.5) * W * 0.6;
    const pts = [];
    const rad = [];
    for (let j = 0; j <= 4; j++) {
      const t = j / 4;
      pts.push([0.03, t * H * 0.45, z0 + Math.sin(t * 5 + i) * 0.12]);
      rad.push(lerp(0.025, 0.01, t));
    }
    tube(wood, { pts, rad, order: 1 }, lod === 'near' ? 4 : 3, barkTile, barkTint, () => 0);
  }
  if (!leaves.count) {
    for (let i = 0; i < 3; i++) leaves.vert([0, 0.05, 0], [0, 1, 0], [0, 0, 0], [0.5, 0.5], 0);
    leaves.tri(0, 1, 2);
  }
  return {
    wood: wood.build(0, conf),
    leaves: leaves.build(1, conf),
    height: H,
    crownR: W / 2,
    trunkR: 0.025,
    clumps: layers.length,
    skeleton: { vine: true },
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
