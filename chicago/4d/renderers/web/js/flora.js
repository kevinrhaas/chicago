/**
 * flora.js — the sward you stand in.
 *
 * The walkthrough's ground was a painted plane. This module puts the July 1835
 * lake-plain prairie on top of it: chest-high layered vegetation that hides the
 * ground a few metres from the camera and falls off into a green sea.
 *
 * It invents no plant. Which community is where (`extent`), what grows in it
 * (`species`), how tall it is ON 1 JULY (`height_m`), how much ground it covers
 * (`abundance`), its leaf colour and whether it flowers at all (`july`) all come
 * from `data/flora/`. A missing manifest draws NOTHING and says so; there is no
 * fallback community, because an invented prairie looks exactly like a
 * researched one and that is the failure this project exists to avoid
 * (AGENTS.md rule 2).
 *
 * THE JULY GATE, enforced here as well as in the data. A flower head is drawn
 * if and only if the record carries a `july.inflorescence` AND its phenology is
 * not `vegetative` or `budding`. Big bluestem, Indian grass and switchgrass are
 * vegetative in mid-July, and the dossier calls 2 m "turkey-foot" seed heads in
 * July "the single most common historical-reconstruction error". Keying the
 * head off the record makes that error impossible to draw: no code path puts an
 * inflorescence on a plant whose record has none. A record that contradicts
 * itself is a defect, not a licence, and it is reported.
 *
 * THREE LAYERS, because a prairie seen from inside it is three problems:
 *
 *   NEAR  to ~8 m   blade geometry. The layer the eye reads as plants, and the
 *                   one that has to hide the ground — at eye height the nearest
 *                   ground in frame is 3.4 m away.
 *   MID   to ~27 m  a blade is a third of a pixel at 20 m. Clump cards turned
 *                   to the camera: silhouette and colour, all that survives.
 *   FAR   beyond the instanced plants, the terrain material's procedural
 *                   prairie texture carries the unresolved colour. There is
 *                   deliberately no second horizontal vegetation surface:
 *                   one at plant-top height reads as elevated ground, hides
 *                   building bases, and leaves the visitor walking underneath
 *                   it at banks. Detailed plants remain rooted on the terrain.
 *
 * Placement is a deterministic world lattice: a plant's position, species,
 * height and colour are a hash of its cell, so re-centring on a walking camera
 * regenerates the same plants and nothing swims underfoot. Only the ring edge
 * changes, and it is scaled in rather than popped.
 *
 * Procedural per AGENTS.md and the publish budget: no image asset, no binary,
 * a bounded handful of draw calls. Every material carries `_CONFIDENCE` as a per-INSTANCE
 * attribute, so the confidence view grades each plant by its species' evidence.
 */

import * as THREE from 'three';
// The shrub archetype's LAYOUT, in a module that imports nothing, so
// `tools/measure_spray_grain.mjs` can measure the grain without a browser and
// without a second copy of the corner arithmetic. See K57.
import { SHRUB_GRAIN, shrubLayout } from './shrub-grain.js';

/** docs/PROVENANCE.md's three levels, as the shader reads them. */
const LEVEL = { attested: 0.0, inferred: 0.5, reconstructed: 1.0 };

/**
 * July midday light ON A LEAF, which is not the same problem as light on a wall.
 *
 * A sward lit only by reflection cannot be brighter than its own albedo, and a
 * green leaf's albedo is about 0.14 in the green channel: under any exposure
 * that keeps a whitewashed wall white, a purely reflective prairie tops out at
 * about half grey and stays there. Measured against the bar that is exactly the
 * failure — round 1 put ZERO pixels over luminance 180 in the near five metres
 * where the July photographs put 15.0% (Woodworth) and 4.0% even in the October
 * negative control, and its p99 was 132 against the photographs' 252.
 *
 * The missing physics is that a grass blade is a thin membrane. It TRANSMITS:
 * roughly a fifth of the light that lands on it comes out the other side, and
 * it comes out FORWARD-SCATTERED, so the lobe leaving the far face is several
 * times brighter than an isotropic one. That is why a backlit blade out-glows
 * every front-lit blade around it, and it is what makes the photographs' white
 * tail. The transmitted light is filtered by chlorophyll on the way through,
 * which is why the tail is GREEN and not a white blowout. On top of that the
 * cuticle is a waxy film with a narrow specular lobe, which supplies the
 * glints, and the sky passes through the blade as well, which is what keeps
 * the shaded face off black now that it is no longer given a fake sunward
 * normal.
 *
 * These are render tuning, not evidence — no source records the transmittance
 * of Chicago cordgrass. They are recorded as such in docs/LIBERTIES.md.
 */
const LEAF = {
  /**
   * Multiple scattering inside the canopy, on the front-lit path. A green
   * photon that enters a sward is scattered rather than absorbed and bounces
   * from leaf to leaf until it escapes, so a CANOPY is far brighter and far
   * more saturated in the green band than any single leaf in it, while red and
   * blue are absorbed on the first hit. A single-scattering Lambert model
   * cannot exceed one leaf's albedo — 0.14 in green — and that ceiling is
   * exactly the flat top the structure critic measured. In the Woodworth
   * photograph the pixels over luminance 180 are not glints: they are ordinary
   * sunlit leaf FACES at (219, 233, 172), 95% of them green-dominant.
   */
  scatter: 0.34,
  /** Effective transmittance x forward-lobe gain, green channel. */
  transmit: 0.74,
  /** Sharpness of the forward lobe, on a (0.5 + 0.5 cos) remap: a 70-degree
   *  sun is overhead, not behind, so a raw cos^n lobe would never fire. */
  forward: 3.2,
  /** What chlorophyll passes, relative to the leaf's own hue. Green through,
   *  red partly, blue absorbed. */
  tint: [0.66, 1.0, 0.42],
  /** Skylight through the blade. Small, and it is the shaded face's floor. */
  skyTransmit: 0.05,
  /** The cuticle. A narrow lobe and a Fresnel edge, at a dielectric F0. */
  gloss: 38.0,
  specular: 0.85,
  f0: 0.035,
};

/**
 * Where the sun is if the scene graph has no directional light to ask. 1 July,
 * 41.85 N, local noon — the same instant world.js computes from the scene
 * record. It is only a fallback: `sunFromScene` prefers the light the scene
 * actually built, so the sward and the buildings are lit by one sun.
 */
const SUN_FALLBACK = {
  elevationDeg: 70.6,
  azimuthDeg: 180,
  /** 0xfff2dc x 3.0 and 0xa8c4e0 x 2.4, linear — world.js's own values. */
  colour: [3.0, 2.66, 2.17],
  sky: [0.40, 0.55, 0.75],
};

/**
 * Render tuning: how many polygons we spend and where, not evidence. A tuft
 * instance is not a plant but a BUNDLE of shoots standing for the fraction of a
 * square metre the matrix covers — the records give cover fractions and no
 * source gives stem counts. The records set the mix; `tuftsPerM2` sets the
 * geometry spent on it, tuned to the one thing a photograph can settle: at eye
 * height the ground is invisible. LIBERTIES L32.
 */
const TUNE = {
  /**
   * `spreadOuter` / `spreadInner` — T-0093. THE NEAR/MID HANDOVER IS A DENSITY
   * RAMP, NOT A COVERAGE ONE, and these two flags are the whole of the change.
   *
   * A layer whose boundary carries one of these hands its ground over the way
   * `far` does: the band stops being an alpha the screen door resolves and
   * becomes a per-slot SPREAD of the boundary itself, so a plant is drawn whole
   * or not at all and what changes across the band is HOW MANY. See
   * `ringsFor` and `slotRing` for the arithmetic, and `handoverRank` for the
   * world-anchored draw that decides where in the band a given slot crosses.
   *
   * The expected ground cover across the band is UNCHANGED — the fraction of
   * slots drawn at `d` is exactly the alpha the ramp used to write, so the
   * tuning below still means what it meant. What is gone is the stipple.
   *
   * `mid.band` and `forb.band` are deliberately NOT spread, and T-0187 is why
   * it stays that way rather than why it was never tried. Those are the OUTER
   * edges, and an outer edge is the one the sward's reach is read off: a
   * boundary handed over by density is drawn out to the depth at which the
   * thinning still leaves a plant standing in a given bearing, which is a
   * SAMPLE and not a radius. Simulated slot by slot on the published mirror,
   * against every mid instance's own ring and the smoke's own 16 bearing bins:
   * a spread of the full band takes the mean drawn reach from 26.81 m to
   * 25.42 m at `full` — which the boundary check survives — and from 11.89 m
   * to 9.64 m at `light`, where the bar stands at 11.60 m and only 0.29 m of
   * it was unspent. Even a one-metre spread lands at 11.48 m there. The reach
   * a coverage ramp reports is bought by plants at two per cent coverage that
   * a visitor cannot see, so no representation that draws a plant whole or not
   * at all can match it on a ring that small (T-0209).
   *
   * So the outer edges keep their ramp, and what T-0187 fixes is the ramp's
   * WIDTH: it must not begin inside the verge. See `LOW` and `MID`.
   *
   * T-0225 — THE HALF OF THAT ARGUMENT THAT WAS THE INSTRUMENT'S, and it is
   * repaired now rather than restated. Every figure above was read at
   * `fadeAt > 0.02`, which the 4x4 screen door renders as nothing at all for
   * two instance phases in three, so the reach a coverage ramp "reports" was
   * very nearly the radius the placer stopped at: measured with
   * `tools/measure_sward_reach.mjs`, the placed boundary and the 2 % reading
   * are 0.54 m apart at `full` and 0.56 m at `light`. The gate now reads the
   * boundary at 1/16 — the screen door's own quantum, below which "drawn" is a
   * property of the dither phase and not of the coverage — and carries the
   * `band x 1/16` that costs, so a density handover is no longer compared
   * against a statistic only a coverage ramp can produce.
   *
   * What that does NOT do is settle whether these edges should be spread. The
   * bar is off the scale now; the measurement of what a spread costs was taken
   * against the old statistic and has to be retaken. T-0277 is that work.
   *
   * T-0277 — RETAKEN, AND THE RAMP STAYS. `tools/simulate_outer_spread.mjs`
   * deals every placed mid and forb slot the rank `slotRing` would give it,
   * bins the gate's own 16 bearings from the gate's own station, and prints the
   * drawn boundary under both representations. It agrees with
   * `measure_sward_reach.mjs` to the centimetre on today's reading, which is
   * what makes the other column worth reading.
   *
   *   mid ring, `full`   today 25.00 min / 26.61 mean against bars 21.76 /
   *                      24.46; fully spread 22.58 / 25.36 against 22.20 /
   *                      24.90 — CLEARS, by 0.38 m and 0.46 m.
   *   mid ring, `light`  today 10.32 / 11.96 against 9.50 / 11.50; fully
   *                      spread 8.56 / 11.23 against 9.60 / 11.60 — OVER on
   *                      both, by 1.04 m and 0.37 m. Three quarters of the
   *                      band is over too (11.57); half clears at 11.75.
   *   forb ring, `full`  today 23.52 / 24.74 against 20.89 / 23.59; fully
   *                      spread 16.41 / 21.73 against 21.20 / 23.90 — OVER,
   *                      and over from a quarter of the band upwards.
   *
   * THE BAR RISES WHEN THE BAND IS SPREAD, and that is half the answer.
   * `ringsFor` replaces a spread layer's `band` with `HARD`, so the `band/16`
   * a reading at the screen door's quantum sits inside the placed boundary —
   * 0.44 m at `full`, 0.10 m at `light` — simply vanishes. A spread has to
   * clear a HIGHER bar with a SHORTER reach.
   *
   * THE OTHER HALF IS SAMPLING DENSITY, and it is a better reason than the one
   * T-0187 gave. A density handover's drawn boundary is the furthest slot that
   * survives its OWN rank, so it is a sample and its expectation falls with the
   * number of slots in the bin. The desktop cone holds 642 mid slots — forty to
   * a 3.75-degree bin, and one of forty draws a low enough rank to stand near
   * the boundary. The `light` cone holds 132, about eight to a bin, and eight
   * draws do not reach it. At `light` the mid ring is as sparse as the forb
   * ring is at `full`, which is exactly the case
   * `tools/measure_sward_reach.mjs` already refuses to read a boundary off.
   *
   * AND IT CANNOT BE TAKEN ONE EDGE AT A TIME. `full` would carry a mid spread;
   * it will not carry a forb one. But the forb ring ends within a metre of the
   * mid ring on purpose — see `rebuildForbs` — so the two boundaries land on
   * the same screen row, and spreading only the grass would leave the flowers
   * dithering along the line the grass had just stopped drawing. That is the
   * stipple this ticket set out to remove, drawn by half as many plants and
   * against a step. A split decision is worse than either whole one.
   *
   * So both outer edges keep their ramp, on a measurement rather than on a
   * superseded one. Reopening this means changing what is measured, not the
   * bar: a sward dense enough at `light` for eight plants a bin to become
   * forty, or a forb layer that does not have to share the mid ring's boundary.
   */
  near: { radius: 7.6, cell: 0.74, perCell: 4, tuftsPerM2: 7.30, band: 2.2,
    spreadOuter: true },
  mid: { inner: 4.5, radius: 27.0, cell: 1.55, perCell: 4, band: 7.0, innerBand: 3.0, fringe: 3.0,
    spreadInner: true },
  forb: { radius: 26.0, cell: 3.4, perCell: 4, band: 5.0, fringe: 3.0 },
  /**
   * THE FAR BAND — T-0086, and the ONE rule it is built around.
   *
   * The owner, 2026-08-18: the sward "does not look right … you can see them
   * fade in when in long distance view … would be nice if you could see them in
   * the distance blurred faintly further out." Past the mid ring nothing at all
   * was drawn: the meadow ended at a radius and the ground beyond it carried
   * the prairie albedo's colour and no plants.
   *
   * **It is drawn with the mid ring's own clump card, not with a sheet.** A
   * solid far-field vegetation mesh was shipped here once and reverted, because
   * it hid foundations and plant roots while the visitor walked on the real
   * heightfield below it. Every far card is a ROOTED instance standing on
   * `terrain.surfaceHeight` at a station `station()` allows — the same building
   * footprints, the same travelled track, the same waterline — so there is no
   * second land surface to walk under and nothing stands where a plant may not.
   *
   * **And it fades by DENSITY, not by the screen-door dither**, which is the
   * other half of the report. A ramp in coverage resolved by a 4x4 Bayer matrix
   * is invisible at arm's length and a band of dots at fifty metres seen down a
   * shallow view, because distance compresses the whole ramp into a few screen
   * rows: at 60 m the mid ring's 7 m band is nine pixels tall. So a far card is
   * drawn whole or not at all, and what changes with distance is how MANY of
   * them there are — `keepAt` against a world-anchored per-slot rank. A
   * stochastic density ramp has no edge in it to dither.
   *
   * `inner`/`innerRamp` hand over to the detailed rings the same way: the band
   * thins to nothing as the walker closes on it, so a 3 m aggregate card is
   * never met at arm's length and never pops out of a hard inner circle.
   */
  far: {
    columns: 9,
    // TWO BANDS, and the reason is that one lattice cannot do this. A single
    // world-uniform spacing that is right at twenty-five metres is a thousand
    // cards at a hundred and fifty, and one that is right at a hundred and
    // fifty leaves a hole where the detailed rings hand over. So the near band
    // is a fine lattice of small clumps and the deep band a coarse lattice of
    // wide ones, each carrying its own ramps, and they overlap across forty to
    // sixty metres where each is thinning into the other.
    bands: [
      { inner: 16.0, innerRamp: 10.0, radius: 62.0, ramp: 30.0, cell: 3.4, perCell: 1, keep: 0.80, wide: [1.5, 2.6], lift: 1.14 },
      { inner: 44.0, innerRamp: 24.0, radius: 175.0, ramp: 92.0, cell: 9.5, perCell: 1, keep: 0.74, wide: [2.6, 4.6], lift: 1.20 },
    ],
    // How wide a flower must still be, in pixels of the smaller gate viewport,
    // for the far band to draw it — see `farHeadReach`. ONE pixel is the honest
    // bar for the tier that is asked to draw everything; the rungs below it buy
    // their headroom by asking a mark to be bigger before it is worth a head,
    // which is the same shape as `light`'s furniture reach and `balanced`'s
    // (T-0241) and not a different kind of concession. The reach falls linearly
    // and the heads inside it quadratically, so 2.0 draws a quarter of them.
    minPx: 1.0,
  },
  /** Hard caps. The palette's `budget` is advisory; this is the ceiling.
   *
   *  `head` is the average of the NINE head archetypes' ceilings and not any one
   *  of them — T-0214 split it by measured demand, so the nine sum to nine times
   *  this number and each gets `head x HEAD_SHARE[kind]`. Halving `head` at a
   *  detail tier still halves every archetype with it. */
  cap: { near: 2400, mid: 4400, forb: 900, head: 820, far: 420 },
  wind: { speedNear: 1.35, sway: 0.085, waveM: 9.0 },
  /**
   * Rebuild the lattice when the camera has moved this far. It is also the
   * margin the fade ring is inset by (`ringsFor`), so it is the width of the
   * annulus of already-placed, wholly-undrawn plants that stands between the
   * lattice edge and the first plant with any coverage in it. 1.2 m was the
   * figure while the fade was frozen between rebuilds; halved now that the
   * inset is what it buys, because a metre of the near ring is a lot of it.
   * (Since T-0093 the annulus is wider than the step on a spread boundary: a
   * near slot's own outer radius can sit a whole band inside the nominal one,
   * and that only ever adds margin.)
   */
  step: { near: 0.6, mid: 3.0, forb: 3.0 },
};

/**
 * The lattice is world-anchored and rebuilt only every `step` metres walked;
 * the fade ramp is evaluated per FRAME, in the vertex shader, against where the
 * camera actually is. Those two rates are what the pop was made of, and they
 * are reconciled here rather than in either of them.
 *
 * A ring returned as `[outer, band, inner, innerBand]` — the four numbers the
 * shader reads out of `aChiRing` — is inset from the lattice that carries it by
 * `step` at BOTH edges, so a plant is always already placed, at coverage zero,
 * before the distance at which it is worth drawing at all. Without the inset a
 * plant outside the lattice at one rebuild is up to `step` inside the fade ring
 * by the next, and arrives at `step / band` of the ramp in a single frame: 55%
 * for the near ring as it stood, which is the "grass and flowers appear out of
 * the ground as you walk towards them" the owner reported. That was the FIRST
 * of his two reports; T-0035 is the second, and the answer to it is that the
 * ramp no longer touches the geometry at all (see `heightOf`).
 *
 * The outer edge is bought by moving the fade IN — growing the lattice instead
 * would cost a 34% wider near annulus of instances against 6% of triangle
 * headroom. The inner edge is bought by moving the lattice OUT, because the
 * inner annulus of the mid ring is 1.3% of its area and free, and because
 * moving that fade outward would thin the near/mid crossover where the change
 * of representation is supposed to be invisible.
 *
 * `fringe` is the outermost ring's own correction, and it is a different
 * problem from the pop. A ring is a CIRCLE about the walker, so on flat ground
 * its outer edge maps to a constant screen ROW — measured at row 450, razor
 * straight across all 1280 columns, which is ROADMAP § S6a item 3. Each slot
 * therefore carries its own outer radius, `fade[0] + fringeOf(e, n)`, drawn
 * from a world-anchored field rather than from the camera: the boundary is
 * ragged, it is ragged in the same places whichever way the walker faces, and
 * it is a stochastic density ramp rather than an edge with a wobble in it.
 */
function ringsFor(layer, step) {
  const inner = layer.inner ?? 0;
  const fringe = layer.fringe ?? 0;
  const innerBand = layer.innerBand ?? 0;
  // T-0093. A boundary marked `spreadOuter`/`spreadInner` in TUNE is handed
  // over by DENSITY: the band moves out of the ring the shader ramps and into
  // `spread`, where `slotRing` deals it to the slots one at a time. What the
  // shader is left holding is a STEP — `HARD` is small enough that `chiFade`
  // lands on 0 or 1 for every plant on the layer, so the fragment program's own
  // guard (`vChiFade < 1.0`) never enters the Bayer branch and there is no
  // screen door to see. It is `FAR_RING`'s trick, on a ring that still has an
  // edge in it.
  const spread = {
    outer: layer.spreadOuter ? layer.band : 0,
    inner: layer.spreadInner ? innerBand : 0,
  };
  return {
    // The lattice has to reach the furthest a slot's own boundary can stand,
    // plus the step, or the outermost slots of the fringe would be placed for
    // the first time already carrying height.
    lattice: { outer: layer.radius + fringe, inner: Math.max(0, inner - step) },
    // The NOMINAL ring: the outer radius no slot's own boundary stands beyond
    // (a spread only ever moves it IN) and the inner radius none stands within
    // (a spread only ever moves it OUT). Both bounds are what keeps the lattice
    // inset — the gate reads them, and a spread that pushed the other way would
    // put a plant outside its own lattice.
    fade: [layer.radius - step, spread.outer ? HARD : layer.band,
      inner, spread.inner ? HARD : innerBand],
    spread,
    fringe,
  };
}

/**
 * A band narrow enough that the ramp across it is a STEP, so `chiFade` is 0 or
 * 1 and the dither branch is skipped.
 *
 * A micron, and the figure is measured rather than picked. At 0.1 mm — the old
 * floor in `fadeOf` and in the GLSL, and what `FAR_RING` still carries because
 * an outer radius of 1e9 is never within a millimetre of anything — a slot
 * whose own boundary happens to fall inside the band as the camera passes it
 * IS drawn at a partial coverage, for one frame, once in about fifty stands:
 * `partial = slots x HARD / band`, simulated at 40 000 slots and confirmed at
 * 1-3. That plant is invisible either way; what it is not is ZERO, and the
 * assertion T-0093 wants to be able to make is that no plant on this boundary
 * is EVER caught mid-ramp. A micron buys that with two orders of magnitude to
 * spare — and world positions are float32 out at 800 m, where the spacing is
 * already ~60 microns, so the difference the shader computes cannot land inside
 * it at all.
 */
const HARD = 1e-6;

/**
 * Where in a handover this slot crosses, in `[0, 1)`, from where it stands and
 * nothing else — `farRank`'s rule and `farRank`'s quantisation, on its own
 * salts. Two consequences, and both are the point: a plant crosses the boundary
 * at ITS OWN radius rather than the whole band crossing together, and it makes
 * the same decision from every camera, so nothing swims as the walker turns.
 *
 * Quantised to 1/8 m, which is finer than any lattice this module scatters on
 * — the near ring's is 0.37 m between slots — so one slot keeps one rank across
 * every rebuild.
 */
const HANDOVER_SALT = [0x3d5a9e77, 0x6f2c5b13];
function handoverRank(e, n, which) {
  return unitHash(Math.round(e * 8), Math.round(n * 8), HANDOVER_SALT[which]);
}

/** The world grid the ragged boundary lobes on, in metres. At 27 m in a
 *  1280-wide frame a metre is about 69 px, so 4 m lobes put five or six of them
 *  across the view — few enough to read as terrain rather than as noise, many
 *  enough that no one of them is a straight line. */
const LOBE_M = 4.0;

function unitHash(a, b, salt) {
  return hash3(a, b, salt) / 4294967296;
}

/** Value noise on the `LOBE_M` grid, in [0, 1] and continuous across cell
 *  edges — a grid of independent cells would trade one straight line for a
 *  field of short ones. */
function lobeNoise(e, n) {
  const ce = Math.floor(e / LOBE_M);
  const cn = Math.floor(n / LOBE_M);
  const te = e / LOBE_M - ce;
  const tn = n / LOBE_M - cn;
  const se = te * te * (3 - 2 * te);
  const sn = tn * tn * (3 - 2 * tn);
  const a = unitHash(ce, cn, 0x7f4a7c15);
  const b = unitHash(ce + 1, cn, 0x7f4a7c15);
  const c = unitHash(ce, cn + 1, 0x7f4a7c15);
  const d = unitHash(ce + 1, cn + 1, 0x7f4a7c15);
  return (a + (b - a) * se) * (1 - sn) + (c + (d - c) * se) * sn;
}

/**
 * How far this slot's own outer boundary stands beyond the layer's nominal one,
 * in metres, in `[-amp, +amp]`. A function of WORLD position only: two slots a
 * metre apart get nearly the same answer and the same slot gets the same answer
 * from every camera, which is what stops the ragged edge from swimming as the
 * walker moves.
 *
 * Two scales, because either alone still draws a line. The lobes carry the
 * shape; the per-slot dither turns each lobe's own edge into a thinning of the
 * sward rather than the end of it.
 */
function fringeOf(e, n, amp) {
  if (!amp) return 0;
  const lobe = lobeNoise(e, n);
  const dither = unitHash(Math.round(e * 64), Math.round(n * 64), 0x2f1b3c59);
  return amp * (2 * (0.7 * lobe + 0.3 * dither) - 1);
}

/**
 * Heads used to be gated at 35% of their plant's fade — a step in the middle of
 * a ramp, and the most conspicuous pop in the field, because a flower is the
 * brightest thing in it. Their own ring reaches zero exactly where the plant's
 * ramp passes 0.35, so the same heads are drawn as before and the cap sees the
 * same pressure; only the step is gone.
 *
 * On a SPREAD boundary (T-0093) the band is `HARD` and this collapses to "the
 * head's ring is its plant's ring, a hair inside it" — which is the invariant
 * R-BUG7 wants stated rather than a coincidence: a head can only be drawn where
 * its own plant is, because its ring is derived from that plant's. The forb
 * ring is still a coverage ramp and still gets the 35% the comment above
 * describes.
 */
const HEAD_FADE_AT = 0.35;
function headRingAt(fade, out) {
  out[0] = fade[0] - HEAD_FADE_AT * fade[1];
  out[1] = (1 - HEAD_FADE_AT) * fade[1];
  out[2] = fade[2];
  out[3] = fade[3];
  return out;
}
function headRingOf(fade) {
  return headRingAt(fade, [0, 0, 0, 0]);
}

/** A layer ring with this slot's own fringe on its outer radius, written into a
 *  scratch array — `push` copies the four numbers out of it immediately, so one
 *  buffer per rebuild loop is enough and a per-slot allocation would be a
 *  million-a-second one. */
function ringAt(base, off, out) {
  out[0] = base[0] + off;
  out[1] = base[1];
  out[2] = base[2];
  out[3] = base[3];
  return out;
}

/**
 * THIS SLOT'S OWN RING — T-0093. `ringAt` plus the handover: where the layer
 * spreads a boundary rather than ramping across it (`ringsFor`), the slot's own
 * boundary is moved off the nominal one by its world-anchored share of the band.
 *
 * The outer spread moves the boundary IN and the inner spread moves it OUT, both
 * by at most the band, so a slot's ring is always inside the layer's nominal one
 * and the lattice inset the pop-in gate measures still holds for every plant on
 * it. `off` is the fringe, already computed by the caller because the caller
 * needs it for its own reach test.
 */
function slotRing(ring, e, n, off, out) {
  out[0] = ring.fade[0] + off
    - (ring.spread.outer ? ring.spread.outer * handoverRank(e, n, 0) : 0);
  out[1] = ring.fade[1];
  out[2] = ring.fade[2]
    + (ring.spread.inner ? ring.spread.inner * handoverRank(e, n, 1) : 0);
  out[3] = ring.fade[3];
  return out;
}

/** The ramp the vertex shader applies, in JS, so the two cannot disagree about
 *  where a plant starts to be drawn. Kept identical to the GLSL in
 *  `plantMaterial`. Since T-0035 the ramp is COVERAGE, not height: it is the
 *  alpha the screen-door dither resolves, and `heightOf` below is the whole of
 *  what it does to the geometry. Since T-0093 the near ring's outer boundary
 *  and the mid ring's inner one are spread per slot instead, so on those two
 *  edges this function only ever returns 0 or 1 and nothing is dithered at all;
 *  the arithmetic is unchanged because a step is a ramp with a `HARD` band. */
function fadeOf(ring, d) {
  // The floor is `HARD` and not 1e-4, so a hard ring really is a step here as
  // well as in the GLSL — see `HARD`. It only ever guards the division.
  const outer = clamp01((ring[0] - d) / Math.max(ring[1], HARD));
  const inner = ring[3] > 0 ? clamp01((d - ring[2]) / ring[3]) : 1;
  return outer * inner;
}

/**
 * The ring a reader is asking about: the layer's own, or THIS INSTANCE'S.
 *
 * Since T-0093 both boundaries can be spread per slot, so a caller that knows
 * only the outer radius can no longer be answered exactly about a layer whose
 * INNER edge is the spread one. It may pass the whole four-number `aChiRing` it
 * read off the instance and get the drawing back; a bare number is still read as
 * an outer radius, which is what every caller before this passed and is exact
 * for every layer whose inner edge is not spread.
 */
function slotOf(ring, outer) {
  if (outer === undefined) return ring.fade;
  if (Array.isArray(outer) || ArrayBuffer.isView(outer)) return outer;
  return [outer, ring.fade[1], ring.fade[2], ring.fade[3]];
}

/**
 * How much of its own recorded height a plant on this ring is DRAWN at, in JS,
 * for the same reason `fadeOf` is here: the gates read the drawing back and
 * must not have to guess at the vertex program.
 *
 * It is `0` or `1` and nothing between, and that IS the fix for T-0035 — the
 * owner's "the flowers grow up out of the ground as you approach" was the ramp
 * driving `transformed *= chiFade`. Keep this in step with the GLSL: it is what
 * `tools/measure_head_support.mjs` and the smoke's R-BUG7 gate scale a plant's
 * top and a stalk's foot by, so a height ramp reintroduced without changing
 * this line puts those gates back to measuring a drawing that no longer exists.
 */
function heightOf(ring, d) {
  return fadeOf(ring, d) > 0 ? 1 : 0;
}

/**
 * THE FAR BAND'S RAMP — what fraction of its lattice slots carry a card at `d`
 * metres from the walker. T-0086.
 *
 * Zero at both ends and flat in the middle, and the ends are the whole point.
 * The outer one is the recession: over `ramp` metres of ground the band thins
 * from `keep` to nothing, so the meadow runs out instead of stopping, and it
 * does it without a coverage ramp for the screen-door dither to quantise into a
 * band of dots. The inner one is the handover: a card that stands for several
 * metres of sward has no business being met at arm's length, so the band thins
 * back to nothing over `innerRamp` as the walker closes on it and the detailed
 * rings — which reach past it — carry the ground from there in.
 *
 * A slot's own rank is a function of WORLD position (`farRank`), so a card
 * appears and disappears at ITS OWN radius rather than every card in a ring
 * doing it together, and it makes the same decision from every camera.
 */
function farKeepAt(d, band) {
  const inner = band.innerRamp > 0 ? clamp01((d - band.inner) / band.innerRamp) : 1;
  const outer = band.ramp > 0 ? clamp01((band.radius - d) / band.ramp) : 1;
  return band.keep * inner * outer;
}

/** The two bands' combined reach at `d`, which is the number a measurement
 *  wants: zero inside the detailed rings, zero past the deep band, and never
 *  zero in between — a hole there is the bald ring this whole band exists to
 *  close. */
function farCoverAt(d, t) {
  return t.bands.reduce((a, b) => a + farKeepAt(d, b), 0);
}

/** This slot's place in the queue for a card, in [0, 1), from where it stands
 *  and nothing else — quantised to 1/8 m, which is finer than any lattice this
 *  module scatters on, so one slot keeps one rank across every rebuild. */
function farRank(e, n, band) {
  return unitHash(Math.round(e * 8), Math.round(n * 8), 0x1b9f31c7 ^ (band * 0x9e3779b9));
}

/** The far band is not faded by the shader at all — see `farKeepAt`. This is
 *  the ring that says so: an outer radius nothing can reach, and a band wide
 *  enough that `chiFade` lands on 1 and the fragment shader's guard skips the
 *  dither branch entirely. */
const FAR_RING = [1e9, 1e-4, 0, 0];

/**
 * THE FAR BLOOM — T-0209, and the bar it answers is a PIXEL, not a radius.
 *
 * A flower head was drawn nowhere past 23.65 m, because the head ring hangs off
 * the forb ring and the forb ring ends where the far band begins. So the sward
 * was carried to 175 m and the bloom to 23.65, and T-0034 measured what that
 * costs: the bloom covers 1.8 % of the ground the sward covers, and the other
 * 98 % of a July prairie is grass-coloured whatever its records say is
 * flowering on it.
 *
 * THE CONVERSION T-0209 ASKS FOR, and the reason it is a distance. The flora
 * records give bloom IN PLAN — `density_per_ha` x `size_m`, 0.027-0.219 % of
 * the ground on the mesic prairie — and a frame reads bloom IN SCREEN SPACE at
 * a near-horizontal pose. Tint the far card by the plan figure and nothing
 * happens: run the records through an opaque-canopy model, where each element's
 * share of the drawn wall is its share of the community's silhouette-area
 * density, and the mesic prairie's bloom comes out at **0.05 % of the far
 * card** (`tools/measure_far_bloom.mjs`). A colour blended at five parts in ten
 * thousand is not a colour, and one blended at anything larger is invented.
 *
 * A HEAD IS NOT AN AREA, THOUGH — it is a saturated MARK, and a mark is
 * visible while it still covers a pixel. That is the honest conversion, and it
 * is per-record rather than per-community: the camera is 62 degrees vertical
 * (`main.js`), so the gate's two viewports carry 780/1.0821 = 721 and
 * 800/1.0821 = 739 pixels per radian. A head of `size_m` therefore falls under
 * one pixel at `size_m * 721` metres — the PHONE sets the bar, because mobile
 * is a release gate. The mesic prairie's median head is 0.07 m, so the bloom
 * can honestly be carried to about FIFTY metres and no further; a 0.10 m
 * compass-plant head reaches 72 m and a 0.0275 m purple-prairie-clover thimble
 * only 20 m, which is why the reach is the record's own and not a constant.
 *
 * Past that reach the bloom is genuinely under the pixel grid and the far
 * card's honest tint is the 0.05 % above. That is the number this parcel
 * records rather than a licence to paint one.
 */
const FAR_HEAD_PX_PER_RAD = 721;
/** How far a head of this record's own size stays a mark `minPx` wide. */
function farHeadReach(sp, minPx) {
  return mid(sp.head.size) * FAR_HEAD_PX_PER_RAD / minPx;
}
/** The ring a far head is drawn on: its own reach, faded over the last eighth
 *  of it so the bloom thins out rather than ending on a circle. */
function farHeadRing(sp, minPx, out) {
  const r = farHeadReach(sp, minPx);
  out[0] = r; out[1] = r * 0.125; out[2] = 0; out[3] = 0;
  return out;
}

/** Nearer than this, plants go all the way round whatever the cone says. */
const CONE_KEEP_M = 3.5;
/** Cosine of the cone half-angle, and the yaw change that forces a rebuild. */
const CONE_COS = Math.cos(62 * Math.PI / 180);
const CONE_YAW_STEP = 0.20;

/** Everything gets halved on a phone; mobile 390x780 is a release gate. */
const LOW = {
  // A phone is not a small desktop: the mobile pass draws a 585x1170 buffer,
  // MORE pixels than the desktop one, on a fraction of the fill rate. So the
  // sward is not scaled down here, it is a shallower field — tight near and
  // mid rings, with the terrain's prairie texture carrying the far field.
  near: { radius: 4.6, tuftsPerM2: 4.6 },
  // The fringe scales with the ring it ragged-edges: it is about an eighth of
  // the radius at every setting, so the boundary reads the same way on a phone
  // as on a desktop rather than being a fixed number of metres on a ring half
  // the size.
  //
  // T-0187 — AND SO DOES THE OUTER BAND, which it did not, and that was the
  // whole of the defect. `band` was left at TUNE's 7.0 m and 5.0 m on rings cut
  // from 27 m to 13 m, so a ramp sized for the far middle distance came to sit
  // across the middle of the phone's field: the mid ring's ran from 5.4 m and
  // the forb ring's from 7.4 m, both inside the verge, and every plant on them
  // was written through the 4x4 screen door. Measured on the published mirror
  // at 390x780: 15.4 % of the frame screen-doored inside 9 m at the open
  // prairie stand, off 179 mid cards and 35 forbs caught mid-ramp, 81 and 14
  // of them inside the verge.
  //
  // The width here is the widest that keeps the WHOLE ramp outside the verge —
  // `radius - step - fringe - 9.0`, the last term being the nine metres
  // tools/measure_near_verge.mjs calls the ground a walker looks at — which is
  // 1.8 m on this ring, taken at 1.6 for margin. It happens to equal the
  // fringe, and that is a fair statement of what is left: the sward's edge
  // thins over no more ground than it is ragged by.
  mid: { inner: 3.0, radius: 13.0, fringe: 1.6, band: 1.6 },
  forb: { radius: 13.0, fringe: 1.6, band: 1.6 },
  // ...and the far band is where the phone gains most, because thirteen metres
  // is where its detailed rings stop. It is also where it can least afford
  // geometry, so the band is shallower, coarser and smaller-carded than the
  // desktop's rather than the same band drawn thinly.
  far: {
    columns: 7,
    bands: [
      { inner: 9.5, innerRamp: 6.5, radius: 40.0, ramp: 20.0, cell: 3.9, perCell: 1, keep: 0.74, wide: [1.4, 2.3], lift: 1.14 },
      { inner: 30.0, innerRamp: 16.0, radius: 120.0, ramp: 64.0, cell: 11.0, perCell: 1, keep: 0.70, wide: [2.4, 4.2], lift: 1.20 },
    ],
    // NULL, and it is a tier decision rather than a big number chosen to make a
    // reach vanish. `light` is where the DRAW-CALL floor binds — 80 calls,
    // restored by T-0147 and already breached at 83 on an unmodified `dev`
    // (T-0248) — and a head archetype the far band lights up where the near
    // rings had none is a new draw call, not just more triangles. So the phone
    // tier carries the sward to its far band and the bloom no further, the same
    // way it culls furniture at 350 m and the rungs above it do not.
    minPx: null,
  },
  cap: { near: 420, mid: 900, forb: 260, head: 240, far: 190 },
};

/**
 * The middle setting. It has to be a real tune rather than a scale factor on
 * TUNE's caps, because at full detail the CAPS ARE NOT WHAT BINDS — the ring
 * radii are. Scaling the caps alone was measured at 8 177 triangles off 461 112,
 * which is a setting that says "fewer plants" and does essentially nothing.
 * What costs geometry is the mid ring's area: 27 m against LOW's 13 m is over
 * four times the ground. So this sits between the two, and every number here is
 * a RENDERING radius or ceiling. The species mix, the July states and the rules
 * about where a plant may stand are untouched, because those are evidence.
 */
const MID = {
  near: { radius: 6.2, tuftsPerM2: 6.4 },
  // T-0187, the same correction as LOW's and it binds less tightly here. The
  // proportionate band — 7.0 x 18/27 and 5.0 x 17.5/26 — is 4.7 m and 3.4 m,
  // and both already clear the verge on these rings (the widths that would
  // reach it are 6.2 m and 5.7 m), so this setting takes the proportion rather
  // than the clearance. Left at TUNE's 7.0 m the mid ramp began at 8.2 m here,
  // which is inside the verge too: the defect was never only the phone's.
  mid: { inner: 4.0, radius: 18.0, fringe: 2.2, band: 4.7 },
  forb: { radius: 17.5, fringe: 2.2, band: 3.4 },
  far: {
    columns: 8,
    bands: [
      { inner: 13.0, innerRamp: 8.5, radius: 52.0, ramp: 26.0, cell: 3.6, perCell: 1, keep: 0.78, wide: [1.5, 2.5], lift: 1.14 },
      { inner: 38.0, innerRamp: 20.0, radius: 150.0, ramp: 80.0, cell: 10.0, perCell: 1, keep: 0.72, wide: [2.5, 4.4], lift: 1.20 },
    ],
    minPx: 2.0,
  },
  cap: { near: 1500, mid: 2700, forb: 580, head: 520, far: 300 },
};

/** The closed `form` list, split by how it is drawn. */
const GRAMINOID_FORMS = new Set([
  'grass_fine', 'grass_arching', 'grass_clump', 'sedge_tussock', 'rush_culm',
  'cattail', 'mat_prostrate',
]);
const FORB_FORMS = new Set([
  'forb_spike', 'forb_umbel', 'forb_daisy', 'forb_pompom', 'forb_globe',
  'forb_basal_scape', 'shrub_low', 'scape_leafless',
]);
/** Roles this module draws. `tree` and `thicket` belong to trees.js. */
const OUR_ROLES = new Set(['matrix', 'forb', 'emergent', 'shrub_low', 'ground']);

/**
 * Head archetype per RECORDED INFLORESCENCE SHAPE — `july.inflorescence.shape`,
 * against `index.json`'s published 26-value `inflorescence_shapes` vocabulary.
 *
 * Round 1 picked the geometry off `form` instead, an eight-value field about
 * the whole PLANT, and never read `inflorescence.shape` anywhere in the repo.
 * All 154 rows fill the shape field correctly, so that was 26 values of
 * researched morphology thrown away at the last step: Liatris's dense button
 * spike and Culver's root's candelabra spire came out as the same mesh in two
 * colours, and every `forb_umbel` — 47% of the wet prairie's forb population —
 * came out as one flat horizontal disc seen 11 degrees off the horizontal,
 * which is three pixels at five metres.
 *
 * The map is exhaustive over the published vocabulary and `compileZones`
 * checks that it stays so: a shape this renderer cannot draw is REPORTED and
 * draws nothing, rather than being quietly substituted, which is the whole
 * point of keying off the record in the first place.
 *
 * Each row carries four things the record cannot:
 *
 *   kind   which archetype mesh draws it.
 *   count  how many inflorescences one plant carries in mid-July. The records
 *          give the density of PLANTS and the size of ONE inflorescence and
 *          nothing about multiplicity, so this is a liberty either way and the
 *          honest thing is to key it to the architecture and say so
 *          (docs/LIBERTIES.md L35). A mountain mint is a mass of corymbs and a
 *          prairie dock a branched scape of ray heads, while Culver's root's
 *          candelabra IS the whole inflorescence and there is exactly one.
 *   tilt   radians off vertical, per instance. A corymb is FLAT-TOPPED and at
 *          1.68 m eye height a head at 0.7 m is seen eleven degrees above the
 *          horizontal, so a tilt near zero is a head that is not there.
 *          `umbel_nodding` is past 90 degrees, which is what nodding means.
 *   band   how far DOWN the plant the non-terminal heads are carried, as a
 *          fraction of its height. Axillary clusters run up the whole stem;
 *          a terminal spike does not.
 */
const HEAD_OF_SHAPE = {
  // Wands and columns.
  spike: { kind: 'spike', count: [1, 4], tilt: [0.00, 0.24], band: 0.16 },
  one_sided_spike: { kind: 'spike', count: [1, 2], tilt: [0.06, 0.34], band: 0.10 },
  raceme: { kind: 'spike', count: [1, 4], tilt: [0.05, 0.36], band: 0.18 },
  head_thimble: { kind: 'spike', count: [3, 10], tilt: [0.00, 0.28], band: 0.30 },
  // Flowers in the leaf AXILS, all the way up the stem — not a terminal head.
  cluster_axillary: { kind: 'spike', count: [8, 22], tilt: [0.60, 1.35], band: 0.66 },
  panicle_dense: { kind: 'spike', count: [1, 4], tilt: [0.00, 0.32], band: 0.16 },
  spadix_brown: { kind: 'spike', count: [1, 1], tilt: [0.00, 0.10], band: 0.04 },
  capsule_green: { kind: 'spike', count: [1, 3], tilt: [0.10, 0.50], band: 0.18 },
  // Culver's root: a terminal spire with lateral spires off its shoulder.
  spire_candelabra: { kind: 'spire', count: [1, 3], tilt: [0.00, 0.16], band: 0.08 },
  // Bluejoint, wild rice, wood nettle: an airy diffuse cloud, not a wand.
  panicle_open: { kind: 'panicle', count: [1, 2], tilt: [0.05, 0.42], band: 0.10 },
  // Composites, held up and out on branches.
  head_ray: { kind: 'ray', count: [5, 17], tilt: [0.25, 0.85], band: 0.38 },
  head_ray_drooping: { kind: 'raydroop', count: [5, 15], tilt: [0.20, 0.72], band: 0.36 },
  // Balls and buttons. A berry cluster, a burr, a hazel husk and a wild plum
  // all read as a small dense sphere at these sizes.
  head_pompom: { kind: 'pompom', count: [3, 11], tilt: [0.00, 0.40], band: 0.30 },
  head_globe: { kind: 'pompom', count: [3, 12], tilt: [0.00, 0.42], band: 0.32 },
  head_button: { kind: 'pompom', count: [2, 8], tilt: [0.00, 0.48], band: 0.28 },
  burr_spherical: { kind: 'pompom', count: [2, 8], tilt: [0.00, 0.48], band: 0.26 },
  berry_cluster: { kind: 'pompom', count: [3, 11], tilt: [0.10, 0.62], band: 0.36 },
  cherry: { kind: 'pompom', count: [3, 12], tilt: [0.10, 0.72], band: 0.38 },
  nut_husk: { kind: 'pompom', count: [2, 7], tilt: [0.10, 0.62], band: 0.32 },
  cluster_terminal: { kind: 'pompom', count: [1, 4], tilt: [0.15, 0.66], band: 0.12 },
  // Umbels: a DOME, never a plate.
  umbel_domed: { kind: 'dome', count: [3, 10], tilt: [0.05, 0.48], band: 0.34 },
  umbel_nodding: { kind: 'dome', count: [1, 4], tilt: [1.70, 2.45], band: 0.14 },
  bulbil_umbel: { kind: 'dome', count: [1, 2], tilt: [0.05, 0.35], band: 0.06 },
  // Flat-topped clusters, drawn as a tilted disc with a per-instance tilt.
  corymb_flat: { kind: 'corymb', count: [6, 20], tilt: [0.44, 0.74], band: 0.42 },
  umbel_flat: { kind: 'corymb', count: [4, 14], tilt: [0.40, 0.70], band: 0.34 },
  // Umbellets on rays from one point — the Queen-Anne's-lace architecture.
  umbel_compound: { kind: 'compound', count: [4, 14], tilt: [0.10, 0.46], band: 0.32 },
};

/**
 * T-0214 — HOW THE ONE HEAD BUDGET IS SPLIT NINE WAYS, and why it is not split
 * evenly.
 *
 * Nine inflorescence archetypes are nine InstancedMeshes, and each carries its
 * own ceiling. Until this ticket that ceiling was `tune.cap.head` NINE TIMES:
 * the same number for the umbel that half a forest flowers with and for the
 * spire two records in the whole town carry. `maybeHead` stops pushing the
 * moment a set is full — it now says so through `skip`, but it still stops — so
 * a set at its ceiling loses the rest of that plant's inflorescences, silently
 * and mid-plant.
 *
 * TWO SETS WERE LOSING THEM. Measured by `tools/measure_bloom_headroom.mjs`
 * standing in every community at four bearings, plus its three named stands —
 * ASKED FOR against a 820 ceiling, at each set's own worst pose:
 *
 *     dome     1,202  z06_dense_forest facing 90    REFUSED 382
 *     spike      852  z10_settled_town facing 90    REFUSED  32
 *     pompom     804  z06_dense_forest facing 90
 *     raydroop   734  z02_mesic_prairie
 *     corymb     533  z10_settled_town facing 270
 *     ray        248  z02_mesic_prairie
 *     compound   160  z10_settled_town facing 270
 *     panicle     23  z01_wet_prairie facing 90
 *     spire       21  z10_settled_town facing 270
 *
 * **That is 4,577 against a 7,380-instance budget, so the shortfall is an
 * ALLOCATION and not a budget.** And 4,577 is already a bound no frame draws:
 * it sums every set's own worst pose, and those poses are in five different
 * communities. Two sets were full while seven stood a fifth spent.
 *
 * RE-MEASURED THE SAME DAY, after T-0209 carried the bloom out past the near
 * ring to 119.9 m, and the numbers in `HEAD_DEMAND` below are that second
 * reading. More reach is more heads: the total asked for goes 4,577 to 5,090,
 * `corymb` alone from 533 to 724, and the shares are sized on the new figures
 * rather than left standing on the old ones. This is what the last paragraph
 * means by re-measurable, on the first day it mattered.
 *
 * SO THE SHARE IS SIZED ON THE DEMAND, AND THE TOTAL DOES NOT MOVE. Each set
 * gets `tune.cap.head x HEAD_SHARE[kind]`, and the shares average exactly one —
 * so nine times `cap.head` is still the head budget at every detail tier, and a
 * tier that halves `cap.head` halves every share with it. Nothing here raises a
 * ceiling; it stops nine identical ceilings from being nine wrong ones.
 *
 * THE FLOOR is the third column of the arithmetic and it is `compound`'s own
 * measured demand. A share cut to a set's measured worst pose alone would give
 * `spire` twenty-one instances, and twenty-one is a ceiling one new flowering
 * record walks through — the demand figures are a reading of the flora records
 * as they stand today, not a property of the archetype. So no set is dealt off
 * less than the smallest genuinely-used set, which is what makes the four small
 * sets robust to a record being added rather than to a re-measurement.
 *
 * WHAT IT COSTS THE FRAME. The refusals are worth 12,640 triangles if every one
 * of them were drawn in one frame, and no frame draws them: a head is only ever
 * drawn inside the head ring, so `dome`'s 382 are only in the frame of a visitor
 * standing IN the dense forest, and `spike`'s 32 (416 triangles) only of one
 * standing in the settled town. None of T-0135's five gate stands stands in the
 * dense forest, and measured against `dev` the whole parcel moves four of the
 * five by nothing at all and the fifth — the open aerial — by 1,638 triangles
 * against 510,602 of headroom.
 *
 * THE DEMAND FIGURES ARE A MEASUREMENT AND ARE RE-MEASURABLE. Re-run
 * `node tools/measure_bloom_headroom.mjs` — its §2a is this table — and if a set
 * is at its cap there, the allocation is stale and this is where it is fixed.
 */
const HEAD_DEMAND = {
  dome: 1235,
  spike: 923,
  raydroop: 848,
  pompom: 804,
  corymb: 724,
  ray: 308,
  compound: 190,
  spire: 35,
  panicle: 23,
};
/** No archetype is dealt off less than the smallest genuinely-used set — see
 *  THE FLOOR above. It is `compound`'s own measured demand and not a round
 *  number chosen to look like one. */
const HEAD_DEMAND_FLOOR = HEAD_DEMAND.compound;
/**
 * The share of `cap.head` each archetype is given, normalised so the nine
 * average exactly 1. That normalisation is the promise: whatever
 * `tune.cap.head` is at a detail tier, the nine sets still sum to nine times
 * it, so this file cannot quietly buy instances by re-weighting them.
 */
const HEAD_SHARE = (() => {
  const kinds = Object.keys(HEAD_DEMAND);
  const weight = Object.fromEntries(kinds.map(
    (k) => [k, Math.max(HEAD_DEMAND[k], HEAD_DEMAND_FLOOR)]));
  const total = kinds.reduce((a, k) => a + weight[k], 0);
  return Object.fromEntries(kinds.map(
    (k) => [k, (weight[k] / total) * kinds.length]));
})();

/** How each graminoid form deforms the one canonical tuft: `arch` is how far
 *  the tips fall away (cordgrass fountain vs bulrush culm), `spread` scales the
 *  clump's width against its height when no `width_m` is recorded. */
const GRASS_SHAPE = {
  grass_fine: { arch: 0.30, spread: 0.42 },
  grass_arching: { arch: 0.46, spread: 0.60 },
  grass_clump: { arch: 0.22, spread: 0.40 },
  sedge_tussock: { arch: 0.52, spread: 0.55 },
  rush_culm: { arch: 0.05, spread: 0.20 },
  cattail: { arch: 0.16, spread: 0.34 },
  mat_prostrate: { arch: 0.80, spread: 1.10 },
};

/* -------------------------------------------------------------------------- */
/* the module                                                                  */
/* -------------------------------------------------------------------------- */

/**
 * @param {object} o  dataBase (data/ root) · terrain (createTerrain's return) ·
 *   footprints (nothing grows through a wall) · growthBlocked (a narrow dated
 *   travelway clears plants, without clearing its whole legal corridor) ·
 *   confidence (every material is patched into it) · problems (the shared
 *   collector) · lowSpec (touch/mobile)
 */
export async function createFlora({
  checkpoint = () => null,
  dataBase, terrain, footprints = [], growthBlocked = () => false,
  confidence = null, problems = [], lowSpec = false, detail = 'full',
} = {}) {
  const group = new THREE.Group();
  group.name = 'flora';
  const disposables = [];
  const stats = {
    instances: 0, drawCalls: 0, triangles: 0, zones: 0, species: 0,
    unimplementedForms: [], unimplementedShapes: [], unzonedLandFraction: 0, rebuilds: 0,
    // ROADMAP K49(a). The DRAWN population of the sward, per community and per
    // list: what each species' recorded abundance asks for against how many
    // slots it actually got in the frame the visitor is looking at. K48 built
    // this for the woody stems and found a species that was recorded, weighted,
    // banded, gated — and absent. Nothing had ever counted the sward, which is
    // 118 of this project's 154 plant records.
    draws: [],
    // ROADMAP K49(a). Which of those lists deal their slots off numbers that
    // are not in the same unit — see `auditAbundance`.
    abundance: null,
  };

  const dataset = await loadFlora(dataBase, problems);
  if (!dataset) return inertRig(group, stats);

  // `lowSpec` is the device guess and still means the lightest tune; an
  // explicit visitor choice arrives as `detail` and outranks it.
  const tune = mergeTune(lowSpec && detail === 'full' ? 'light' : detail);
  const zones = compileZones(dataset, terrain, problems, stats);
  if (!zones.length) {
    problems.push('flora: the manifest named no usable zone — nothing is planted');
    return inertRig(group, stats);
  }
  stats.zones = zones.length;

  stats.abundance = auditAbundance(zones);

  /**
   * ROADMAP K49(a) — THE DRAWN CENSUS OF THE SWARD.
   *
   * One row per (community, list), reset on every rebuild: the sward is dealt
   * from scratch each time the lattice re-centres, so this counts the
   * population of the frame in front of the visitor rather than a total
   * accumulated over a walk. It counts SLOTS DEALT — `stats.capped` is the
   * separate question of whether a set then had room for them.
   *
   * `expected` is computed against the subset the slot was actually drawn from,
   * not against the whole list: a species that may not stand over water is not
   * owed the wet slots, and scoring it against them would report a shortfall
   * every time the visitor stood at the river.
   */
  const censusIndex = new Map();
  for (const z of zones) {
    for (const [list, key] of [['matrix', 'graminoids'], ['forb', 'forbs'], ['shrub', 'shrubs']]) {
      const items = z[key];
      if (!items.length) continue;
      const row = {
        community: z.id, list, drawn: 0, drySlots: 0, wetSlots: 0,
        /** ROADMAP K49(e) / T-0018 — THE SAME CENSUS ONE STEP EARLIER.
         *  `drawn` counts the slots that survived `station()` and
         *  `crowdsTheWalker()`; `dealt` counts the slots the deal handed a
         *  species to before either filter got a vote, and the two rejection
         *  counters say which filter took the difference. Nothing here changes
         *  what is drawn — it is the population `deviation` is measured over,
         *  which until now could only be seen after the filtering. */
        dealt: 0, dryDealt: 0, wetDealt: 0, rejStation: 0, rejWalker: 0,
        species: items.map((s) => ({
          id: s.id, unit: s.unit, share: s.weight, stems: s.stems, expected: 0, drawn: 0,
          /** ROADMAP K49(e) / T-0018 — this species' half of the same pair. */
          dealt: 0, expectedDealt: 0,
          /** ROADMAP K54. The clump this species' record gives, and the ground
           *  cover that density implies — `stems × π(width/2)²`, which for a
           *  cover-recorded species is its own recorded `cover_fraction` back
           *  again. It is here so a census can ask the question K54 asks: not
           *  only whether the head count is faithful, but whether the GROUND
           *  the sample covers is. */
          width: s.width ? mid(s.width) : null,
          cover: coverOf(s),
        })),
      };
      const byId = new Map(row.species.map((s) => [s.id, s]));
      // The shares the two subsets renormalise to, which is what `pick` walks.
      const shares = items.map((s) => ({
        row: byId.get(s.id),
        dry: z.dry[key].items.includes(s) && z.dry[key].total > 0 ? s.weight / z.dry[key].total : 0,
        wet: z.wet[key].items.includes(s) && z.wet[key].total > 0 ? s.weight / z.wet[key].total : 0,
      }));
      censusIndex.set(`${z.id}:${list}`, { row, byId, shares });
      // The placer reaches the census row THROUGH THE ZONE it already has in
      // hand. The lookup used to rebuild `${z.id}:${list}` and hit the Map once
      // per drawn slot; T-0018 asks the same question of every DEALT slot,
      // which is a bigger population, and paying a string allocation for each
      // of them in the rebuild loop is not a measurement, it is a cost.
      (z.census ??= {})[list] = censusIndex.get(`${z.id}:${list}`);
      stats.draws.push(row);
    }
  }
  /** A slot the deal handed a species to, counted before `station()` and
   *  `crowdsTheWalker()` are asked. ROADMAP K49(e) / T-0018. */
  const countDealt = (c, sp, wet) => {
    if (!c) return;
    c.row.dealt++;
    if (wet) c.row.wetDealt++; else c.row.dryDealt++;
    const s = c.byId.get(sp.id);
    if (s) s.dealt++;
  };
  const countDraw = (c, sp, wet) => {
    if (!c) return;
    c.row.drawn++;
    if (wet) c.row.wetSlots++; else c.row.drySlots++;
    const s = c.byId.get(sp.id);
    if (s) s.drawn++;
  };
  const openCensus = () => {
    for (const { row } of censusIndex.values()) {
      row.drawn = 0;
      row.drySlots = 0;
      row.wetSlots = 0;
      row.dealt = 0;
      row.dryDealt = 0;
      row.wetDealt = 0;
      row.rejStation = 0;
      row.rejWalker = 0;
      for (const s of row.species) { s.drawn = 0; s.expected = 0; s.dealt = 0; s.expectedDealt = 0; }
    }
  };
  const closeCensus = () => {
    for (const { row, shares } of censusIndex.values()) {
      for (const s of shares) {
        s.row.expected = s.dry * row.drySlots + s.wet * row.wetSlots;
        // The same share against the DEALT population: what the layer's
        // disagreement with its own target would have been had nothing been
        // filtered out. ROADMAP K49(e) / T-0018.
        s.row.expectedDealt = s.dry * row.dryDealt + s.wet * row.wetDealt;
      }
    }
  };

  const water = await waterField(terrain, checkpoint);
  const blocks = footprintCircles(footprints);
  const finder = zoneFinder(zones, terrain, water);
  stats.unzonedLandFraction = await auditCoverage(terrain, finder, checkpoint);
  if (stats.unzonedLandFraction >= 0.999) {
    // Not a tolerance: records exist, ground exists, and NOTHING matches — the
    // layer would draw an empty prairie while looking healthy. Any fraction
    // short of that is a real mosaic and is reported through stats.
    problems.push('flora: no point on the modelled ground matches any zone extent — '
      + 'the sward is empty. Check data/flora/index.json extents against the heightfield.');
  }

  // ---- materials --------------------------------------------------------- //

  const uniforms = {
    uChiTime: { value: 0 },
    uChiWind: { value: new THREE.Vector2(0.82, 0.57) },
    uChiSway: { value: TUNE.wind.sway },
    uChiWaveK: { value: (Math.PI * 2) / TUNE.wind.waveM },
    // World space, pointing AT the sun. Filled from the scene's own light on
    // the first update; the fallback is the same instant world.js computes.
    uChiSun: { value: sunDirFallback() },
    uChiSunCol: { value: new THREE.Vector3(...SUN_FALLBACK.colour) },
    uChiSky: { value: new THREE.Vector3(...SUN_FALLBACK.sky) },
  };
  /** Resolved once, from the scene graph, at the first update. */
  let sunFound = false;

  const bladeMat = plantMaterial({ uniforms, billboard: false });
  const cardMat = plantMaterial({ uniforms, billboard: true, membrane: 0.30 });
  // Heads share the blade program deliberately. Under the software rasteriser
  // every extra shader program is seconds of compile time on the first frame,
  // and a flower head's own sway works out at four millimetres.
  const headMat = bladeMat;
  for (const m of [bladeMat, cardMat]) {
    confidence?.patch(m);
    disposables.push(m);
  }

  // ---- the layers -------------------------------------------------------- //

  const nearSet = instSet('flora-near', tuftGeometry(9, 2), bladeMat, tune.cap.near);
  const midSet = instSet('flora-mid', cardGeometry(7), cardMat, tune.cap.mid);
  const forbSet = instSet('flora-forb', forbGeometry(), bladeMat, tune.cap.forb);
  // A basal-scape plant is not a stem with leaves up it. Prairie dock and
  // compass plant are a 40 cm ROSETTE of huge paddle leaves at the ground with
  // a nearly naked flowering scape two or three metres over it — the dossier
  // names the rosette explicitly and it is the plant's whole diagnosis. Drawn
  // with the generic forb it became a leafy giant that filled the foreground.
  const rosetteSet = instSet('flora-rosette', rosetteGeometry(), bladeMat,
    Math.max(48, Math.round(tune.cap.forb * 0.45)));
  // ...and a shrub is not a stem with leaves up it either (K53). Twenty-one
  // records across eight zones carry `form: 'shrub_low'` — hazel, elder,
  // dogwood, buttonbush, the lakeshore's sand cherry and the black-oak grubs —
  // and every one of them was drawn with the forb above, which is one wand of
  // four leaves however wide the record says the clump is. The wet woods' own
  // dossier calls hazel the most common shrub-layer plant there was and says
  // under-rendering it is the specific mistake to avoid; it was a wand.
  const shrubSet = instSet('flora-shrub', shrubGeometry(), bladeMat, tune.cap.forb);
  // One instanced set per ARCHETYPE, so the geometry a species gets is the
  // shape its record names. The flat horizontal plate is gone; nothing draws
  // one, because at 1.68 m eye height a corymb at 0.7 m is seen 11 degrees off
  // the horizontal and a flat disc is three pixels of nothing.
  const headCap = (kind) => Math.round(tune.cap.head * HEAD_SHARE[kind]);
  const heads = {
    spike: instSet('flora-head-spike', spikeGeometry(), headMat, headCap('spike')),
    spire: instSet('flora-head-spire', spireGeometry(), headMat, headCap('spire')),
    panicle: instSet('flora-head-panicle', panicleGeometry(), headMat, headCap('panicle')),
    ray: instSet('flora-head-ray', rayGeometry(false), headMat, headCap('ray')),
    raydroop: instSet('flora-head-raydroop', rayGeometry(true), headMat, headCap('raydroop')),
    pompom: instSet('flora-head-pompom', pompomGeometry(), headMat, headCap('pompom')),
    dome: instSet('flora-head-dome', domeGeometry(), headMat, headCap('dome')),
    corymb: instSet('flora-head-corymb', corymbGeometry(), headMat, headCap('corymb')),
    compound: instSet('flora-head-compound', compoundGeometry(), headMat, headCap('compound')),
  };
  // T-0086. The far band, on the mid ring's own material and its own archetype:
  // one more instanced set, one more draw call, no new shader program. Nine
  // columns rather than seven because this card stands further off and for more
  // ground — a silhouette read at fifty metres wants more tops in it, and two
  // extra triangles is what they cost.
  const farSet = instSet('flora-far', cardGeometry(tune.far.columns), cardMat, tune.cap.far);
  const sets = [nearSet, midSet, forbSet, rosetteSet, shrubSet, farSet, ...Object.values(heads)];
  for (const s of sets) { group.add(s.mesh); disposables.push(s.mesh.geometry); }

  // ---- placement --------------------------------------------------------- //

  const centres = { near: null, yaw: null };
  const waterY = terrain.heightfield?.meta?.water_surface_m ?? 0;

  // The lattice each layer is scattered on, and the ring the shader fades it
  // over — the second strictly inside the first by `step`. See `ringsFor`.
  const step = tune.step.near;
  /** Scratch buffers for the per-slot rings. See `ringAt`. */
  const _ring = [0, 0, 0, 0];
  const _headRing = [0, 0, 0, 0];
  const rings = {};
  for (const layer of ['near', 'mid', 'forb']) {
    rings[layer] = ringsFor(tune[layer], step);
    rings[layer].head = headRingOf(rings[layer].fade);
  }
  /** Which ring each rooted set is drawn on. A rosette is a forb. */
  const ringOfSet = {
    'flora-near': rings.near, 'flora-mid': rings.mid,
    'flora-forb': rings.forb, 'flora-rosette': rings.forb, 'flora-shrub': rings.forb,
  };

  /** A community that stands in no water, for the plantable-ground question the
   *  gate asks without naming a species. */
  const NO_COMMUNITY = { standsInWater: false };

  /** Ground the plant stands on, or null if it may not stand here. `wet` is the
   *  caller's already-computed water test, since the placer asks it once per
   *  lattice slot to choose which half of the community it may pick from. */
  function station(e, n, zone, species, wet = water.isWater(e, n)) {
    if (growthBlocked(e, n)) return null;
    // THE FLOOR TEST COMES BEFORE THE WATER TEST, and the order is the bug it
    // fixes. This block-list rejection used to sit below the `wet` early return,
    // so it only ever governed DRY ground - and every deck standing over water
    // (a wharf, a bridge) was invisible to it. An emergent bulrush is exactly as
    // entitled to the riverbed under a dock as a bluestem is to the soil under a
    // walk, and neither may come up through the planks. Owner-reported twice:
    // reeds through the dock decks, sward through the sidewalks (T-0085/T-0124).
    for (const b of blocks) {
      const dx = e - b.e;
      const dz = n - b.n;
      if (dx * dx + dz * dz < b.r2 && pointInPolygon(b.pts, e, n)) return null;
    }
    if (wet) {
      // A water BUFFER is not permission for every member of that community to
      // stand in the channel. Only records whose recorded `substrate` puts them
      // in water may root there, and the corrected signed shore-distance field
      // below keeps even those inside the eight-metre marsh edge rather than
      // assigning distance zero to the entire river.
      return zone.standsInWater && species?.substrate && species.substrate !== 'soil'
        ? waterY : null;
    }
    // ...and the mirror of it, which is the half nothing enforced: a plant whose
    // leaves FLOAT has no station on dry ground. `nuphar_advena` and
    // `nymphaea_odorata` are 0.01-0.10 m tall, so the failure was quiet — pads at
    // ankle height standing on the soil of the marsh edge rather than on water.
    if (species?.substrate === 'open_water') return null;
    const y = terrain.surfaceHeight(e, n);
    // T-1056 — A WOODY PLANT HAS NO STATION ON GROUND THE LAKE STILL REWORKS,
    // and which ground that is comes off the ZONE RECORD.
    //
    // Andreas excepts "the sandy hills near the lake" from the North Division
    // timber, and the exception is to the HILLS. The sand bar across the mouth
    // is the other landform in the same sentence's neighbourhood — a surface
    // Fort Dearborn work parties trenched with hand tools and a February 1834
    // storm breached — and until this it inherited z08's whole 8c dune scrub
    // and z09's black-oak grubs, dealt on a uniform lattice over every square
    // metre of two `kind: "everywhere"` boxes that happen to contain it.
    //
    // The bound is `woody_stratum` on the zone record, graded `inferred` with
    // its reasoning, and NOT a constant here: its two ends are z09's recorded
    // +7.6 ft ridge floor and the terrain spec's argued +4 ft bar crest. This
    // function reads the record and interpolates; it does not know the numbers.
    // `hash3` makes the draw positional rather than per-slot, so the scrub that
    // survives stands in POCKETS on the ground that rises toward the band
    // instead of as an even thinning over the whole bar — the terrain is what
    // clusters it, and no length scale is invented here to do it.
    if (zone?.woody && zone.woody.roles.has(species?.role)) {
      const [lo, hi] = zone.woody.establishes;
      const t = smoothstep(lo, hi, y);
      if (t <= 0) return null;
      if (t < 1 && hash3(Math.round(e * 4), Math.round(n * 4), 0x5ad8a1) / 4294967296 >= t) {
        return null;
      }
    }
    return y;
  }

  function* rebuildGround(camE, camN, cone) {
    nearSet.reset();
    midSet.reset();
    for (const k in heads) heads[k].reset();

    const near = rings.near;
    const mid = rings.mid;
    // NEAR: individual tufts, dense enough to close the ground.
    //
    // T-0093 — the ring is PER SLOT here now, where it used to be one ring for
    // the whole set. The outer edge is a density handover (`slotRing`), so each
    // tuft carries its own outer radius drawn from the band and is written
    // solid up to it. The set-wide call is gone rather than left as a default:
    // a slot that missed its own `ring()` would be drawn on the nominal one and
    // would be the only stippled plant in the field.
    yield* scatter(camE, camN, tune.near.cell, tune.near.perCell,
      near.lattice.outer, near.lattice.inner, 0x51ed27, 'strata', cone,
      (e, n, r, rng, _cellSeed, u) => {
        // This slot's own outer boundary. The near ring carries no fringe (its
        // edge is never the one a visitor reads as a line — the mid ring's is),
        // so the offset is zero and the whole of the move is the handover.
        //
        // A slot the handover has already carried past is PLACED ANYWAY, at
        // coverage zero, and the mid ring's matching `return` is not copied
        // here on purpose: every slot inside the lattice is still dealt a
        // species and still counted by the drawn census, exactly as before, so
        // this run moves no community's population and no cover figure. The
        // vertex program collapses a plant outside its ring to a point, which
        // is what it already did for the annulus between the fade and the
        // lattice, so the frame pays nothing for them either.
        const ring = slotRing(near, e, n, 0, _ring);
        const zone = finder(e, n);
        if (!zone || !zone.graminoids.length) return;
        // The community's own recorded matrix cover decides whether this slot
        // carries a plant — the same rule the forb layer has always applied to
        // its own recorded densities, on the field the matrix layer ignored.
        // Cover and species come off the slot's ONE stratified draw (K49(d)):
        // the rank-1 lattice the forb layer uses stripes a dense layer, so this
        // one is a block permutation instead. See `stratum` and `dealt`.
        const wet = water.isWater(e, n);
        const sp = dealt(wet ? zone.wet.graminoids : zone.dry.graminoids,
          zone.matrixShare, u);
        if (!sp) return;
        const c = zone.census?.matrix;
        countDealt(c, sp, wet);
        const y = station(e, n, zone, sp, wet);
        if (y === null) { if (c) c.row.rejStation++; return; }
        if (crowdsTheWalker(sp, r)) { if (c) c.row.rejWalker++; return; }
        // The head is placed off the height the PLANT was actually given, and
        // only if the plant was actually drawn. Round 1 drew the two from
        // independent draws of the same range, so a 2.0 m cordgrass spike
        // could stand over a 1.25 m tuft — which is the pair of flower heads
        // the critic found floating unattached in the open sky.
        countDraw(c, sp, wet);
        nearSet.ring(ring);
        const h = placeGraminoid(nearSet, sp, e, y, n, rng);
        // The head rides its PLANT'S ring now, not the layer's. On a spread
        // boundary the layer's ring answers for no particular tuft, and a head
        // hung on it would go on being drawn out to 7 m over a plant whose own
        // handover had already taken it away at five — a flower in the sky with
        // nothing under it, which is R-BUG7 rebuilt from the other end.
        const headRing = headRingAt(ring, _headRing);
        if (h > 0 && r <= headRing[0] + step) {
          maybeHead(heads, sp, e, y, n, rng, h, headRing);
        }
      });

    // MID: clump cards. The inner edge overlaps the near ring so the change of
    // representation happens inside the field rather than at a visible circle.
    // The OUTER edge is the one that was a visible circle — a constant world
    // radius is a constant screen row on flat ground — so every slot carries
    // its own, offset by a world-anchored fringe. The slots the fringe pushes
    // out of reach are dropped here rather than pushed at zero height: the
    // lattice grew by `fringe` to carry the ones it pushes IN, and paying for
    // the whole annulus would be paying for the amplitude twice.
    yield* scatter(camE, camN, tune.mid.cell, tune.mid.perCell,
      mid.lattice.outer, mid.lattice.inner, 0x9e3779, 'strata', cone,
      (e, n, r, rng, _cellSeed, u) => {
        const off = fringeOf(e, n, mid.fringe);
        if (r > mid.fade[0] + off + step) return;
        const zone = finder(e, n);
        if (!zone || !zone.graminoids.length) return;
        // A clump card stands for the same matrix the near tufts do, so it is
        // thinned by the same recorded cover — and by the same STRATIFIED draw.
        // Applying it to one layer and not the other would put a seam at the
        // near/mid crossover exactly where the change of representation is
        // supposed to be invisible.
        const wet = water.isWater(e, n);
        const sp = dealt(wet ? zone.wet.graminoids : zone.dry.graminoids,
          zone.matrixShare, u);
        if (!sp) return;
        const c = zone.census?.matrix;
        countDealt(c, sp, wet);
        const y = station(e, n, zone, sp, wet);
        if (y === null) { if (c) c.row.rejStation++; return; }
        countDraw(c, sp, wet);
        // T-0093 — the INNER edge is a density handover too, and it is the half
        // of the near/mid crossover the ticket's own two stands turned out to
        // rest on: standing in a roadway the travel track carries no near tufts
        // at all, so every screen-doored pixel of the verge there was written by
        // this ramp fading IN. Each card carries its own inner radius across
        // 4.5-7.5 m and is drawn whole beyond it. The OUTER edge is untouched:
        // it is 18-27 m, the far band already stands over it, and its fringe is
        // what keeps the boundary off a constant screen row.
        midSet.ring(slotRing(mid, e, n, off, _ring));
        placeCard(midSet, sp, zone, e, y, n, rng);
      });
    stats.rebuilds++;
  }

  function* rebuildForbs(camE, camN, cone) {
    forbSet.reset();
    rosetteSet.reset();
    shrubSet.reset();
    const f = rings.forb;
    yield* scatter(camE, camN, tune.forb.cell, tune.forb.perCell,
      f.lattice.outer, f.lattice.inner, 0x2545f9, 'lattice', cone,
      (e, n, r, rng, _cellSeed, u) => {
        // The forb ring ends within a metre of the mid ring, so the two
        // boundaries land on the same screen row and both have to be ragged or
        // the flowers alone would draw the line the grass no longer does.
        const off = fringeOf(e, n, f.fringe);
        if (r > f.fade[0] + off + step) return;
        const zone = finder(e, n);
        if (!zone || !zone.forbs.length) return;
        // The forb layer's density is the zone's OWN summed density_per_ha, so a
        // sparse community stays sparse. `share` is the chance this lattice slot
        // is used at all — of the half of the community that may stand on this
        // side of the waterline, which is why there are two of them. It and the
        // species come off the slot's ONE low-discrepancy draw; see `dealt`.
        const wet = water.isWater(e, n);
        const sp = dealt(wet ? zone.wet.forbs : zone.dry.forbs,
          wet ? zone.forbShareWet : zone.forbShare, u);
        if (!sp) return;
        const c = zone.census?.forb;
        countDealt(c, sp, wet);
        const y = station(e, n, zone, sp, wet);
        if (y === null) { if (c) c.row.rejStation++; return; }
        if (crowdsTheWalker(sp, r)) { if (c) c.row.rejWalker++; return; }
        countDraw(c, sp, wet);
        const set = sp.form === 'forb_basal_scape' ? rosetteSet : forbSet;
        set.ring(ringAt(f.fade, off, _ring));
        const h = placeForb(set, sp, e, y, n, rng);
        if (h > 0 && r <= f.head[0] + off + step) {
          maybeHead(heads, sp, e, y, n, rng, h, ringAt(f.head, off, _headRing));
        }
      });

    // ROADMAP K54 — THE SHRUB STRATUM, ON ITS OWN PASS OVER THE SAME RING.
    //
    // Same lattice geometry, same fade ring, a different SALT: the two draws
    // have to be independent, because a shrub stands over the herb layer rather
    // than instead of it, and sharing one stratified draw would make every
    // shrub slot a slot the herbs did not get. That is the whole defect this
    // parcel repairs, and reusing `u` would rebuild it one line lower down.
    //
    // Everything else is the forb pass, unchanged: the fringe, the walker
    // clearance, the station rules and the head. `placeShrub` reads `width_m` as
    // the clump diameter it is on a shrub (K53).
    yield* scatter(camE, camN, tune.forb.cell, tune.forb.perCell,
      f.lattice.outer, f.lattice.inner, 0x7b5c1d, 'lattice', cone,
      (e, n, r, rng, _cellSeed, u) => {
        const off = fringeOf(e, n, f.fringe);
        if (r > f.fade[0] + off + step) return;
        const zone = finder(e, n);
        if (!zone || !zone.shrubs.length) return;
        const wet = water.isWater(e, n);
        const sp = dealt(wet ? zone.wet.shrubs : zone.dry.shrubs,
          wet ? zone.shrubShareWet : zone.shrubShare, u);
        if (!sp) return;
        const c = zone.census?.shrub;
        countDealt(c, sp, wet);
        const y = station(e, n, zone, sp, wet);
        if (y === null) { if (c) c.row.rejStation++; return; }
        if (crowdsTheWalker(sp, r)) { if (c) c.row.rejWalker++; return; }
        countDraw(c, sp, wet);
        shrubSet.ring(ringAt(f.fade, off, _ring));
        const h = placeShrub(shrubSet, sp, e, y, n, rng);
        if (h > 0 && r <= f.head[0] + off + step) {
          maybeHead(heads, sp, e, y, n, rng, h, ringAt(f.head, off, _headRing));
        }
      });
  }

  // Forbs and their heads share the head sets with the graminoids, so the two
  // ground rebuilds have to happen together or the heads would be half-cleared.
  /**
   * THE FAR BAND — T-0086. The sward past the detailed rings.
   *
   * One aggregate clump card per kept lattice slot, rooted on the heightfield at
   * a station the placer allows, drawn whole, and thinned toward both ends of
   * the band by `farKeepAt`. Nothing here fades in the shader: `FAR_RING` puts
   * every card wholly inside its ring, so the dither branch never runs and
   * there is no stipple to see.
   *
   * It is NOT counted into the drawn census. The census is a population — how
   * many plants of each species the frame drew against how many its recorded
   * abundance asks for — and a far card is not a plant. It is the several
   * metres of matrix the band no longer draws individually, so counting one as
   * a drawn stem would inflate every community's matrix count by the area of an
   * annulus four times the size of the ring the census is about. The species
   * deal is still made, and still off the community's own recorded weights,
   * because it is what gives the card its colour and its height.
   */
  function* rebuildFar(camE, camN, cone) {
    farSet.reset();
    farSet.ring(FAR_RING);
    for (const [i, band] of tune.far.bands.entries()) {
      yield* scatter(camE, camN, band.cell, band.perCell, band.radius, band.inner,
        0x3a91c7 ^ (i * 0x85ebca6b), 'lattice', cone,
        (e, n, r, rng, _cellSeed, u) => {
          if (farRank(e, n, i) >= farKeepAt(r, band)) return;
          const zone = finder(e, n);
          if (!zone || !zone.graminoids.length) return;
          const wet = water.isWater(e, n);
          // T-0209. THE FAR BAND DEALS THE WHOLE COMMUNITY, not just its grass.
          // Until this it dealt `graminoids` alone, so every flowering
          // community past the mid ring was a hundred per cent matrix however
          // its record read — and no card the far band drew could carry a
          // flower because no card the far band drew was a plant that has one.
          //
          // The split is made INSIDE the band this slot was already occupied
          // on, not beside it: the slot is used when `u < matrixShare` exactly
          // as before, and the forbs take their own recorded share OF that
          // range. So the card count, the instance count, the triangles and the
          // draw calls are what they were, and what changes is which plant a
          // card stands for. Widening the occupied band instead would have
          // bought the bloom with geometry, which is the budget the whole
          // ticket was told not to spend.
          //
          // T-0280. AND THE SHARE IT TAKES IS A COVER AGAINST A COVER.
          //
          // The split above was dealt on `forbShare`, and `forbShare` is the
          // FORB RING's lattice occupancy — `min(1, density × cell² / perCell)`
          // at one plant per 2.89 m² slot. Two things were wrong with it here,
          // and they compound.
          //
          // It is CLAMPED, and the clamp belongs to a different lattice. Nine of
          // the ten populated forb layers sit on that 1.000 ceiling
          // (`tools/forb_clamp_baseline.json`), so for nine communities the far
          // band's species mix was decided by the number 1.000 and not by
          // anything their records say: `z06_dense_forest` asks 66.381 plants
          // per m² and `z01_wet_prairie` asks 0.407, and the band split both as
          // though they had asked for the same thing. The far band is dealt on
          // its own lattice at 3.4 m and 9.5 m with `perCell: 1`, and nothing
          // about the forb ring's slot size bounds a PROPORTION drawn on it.
          //
          // And it is the wrong KIND of number even unclamped. `matrixShare` is
          // `cover.matrix_fraction`, a fraction of GROUND COVERED; `forbShare`
          // is a slot-occupancy chance derived from stem density. Dividing one
          // by the sum of both added an area to a probability — K49(a)'s unit
          // error, one stratum further out — so raising the clamp would have
          // replaced a wrong constant with a wrong quantity. At 66.381 plants
          // per m² the unclamped share is ~1 and every far card in the dense
          // forest would have been a flower.
          //
          // So both sides are now the AREAL COVER of their stratum.
          // `subsetOn().cover` sums `stems × π·clump²` over the subset that may
          // actually stand on this side of the waterline, which for a
          // cover-recorded species is its own `cover_fraction` returned intact;
          // the matrix side stays the record's own `matrix_fraction`, which is
          // that same quantity already written down. The ratio is then a mix of
          // two ground shares, which is what an aggregate card standing for
          // several square metres of ground is a mix of — the reading T-0225 is
          // in, arrived at here.
          //
          // THE CLUMP IS THE DRAWN ONE, and it has to be. Fifty of the sward
          // records state no `width_m` — every forb of the wet prairie, the
          // mesic prairie and the sand prairie, and both marsh forbs — so a sum
          // over recorded widths alone would not make those strata small, it
          // would make them ABSENT, and the far band would deal the sand
          // prairie as pure grass on the strength of a missing field. `coverOf`
          // falls back to `clumpRadiusOf`, which is the footprint the placer is
          // ALREADY giving those plants and has given them since the walker
          // clearance was written. `forbCoverFallbacks` on `communities()` says
          // how many of a community's forbs were measured that way.
          //
          // MIDPOINT, not `coverHigh`. T-0034 deals the forb RING off the top of
          // each recorded range because that ring is a slot COUNT and the count
          // had headroom; `matrix_fraction` is a single recorded central figure
          // with no upper end to match, and dividing a high end by a midpoint
          // would tilt the mix toward flowers by the width of the forb records'
          // ranges alone. Both sides central, or the ratio is an artefact of
          // which end each was read at.
          //
          // T-1106. AND THE COVER IS A FLOOR, WHILE THIS BAND IS A WALL.
          //
          // Ground cover is the honest mix for ground, and everything above
          // stands. It is not the honest mix for THIS band. The nearest far card
          // is 34 m out and the furthest 95; at fifty metres a 1.7 m eye looks
          // 1.9 degrees below horizontal, the sward is seen edge-on, and the
          // plant that fills a pixel is the first element the ray meets. That is
          // governed by silhouette area per element times elements per m² of
          // ground — `silhouetteOf` — and the depth of the wall cancels out of a
          // ratio between two strata standing in it.
          //
          // The two quantities disagree exactly where the strata differ in
          // SHAPE. A compass plant 1.8 m tall in 1.2 m grass stands up more wall
          // per square metre of floor than its footprint says, and under the
          // cover reading the band could not know it: T-0280's change cost
          // `prairie_west` every drawn head past 26.4 m, down from 135.7 m,
          // because the tall narrow stratum was priced as though the visitor
          // were looking down at it. `tools/measure_far_split.mjs` §1 carries all
          // three columns and the per-community move.
          //
          // THIS IS THE MODEL THE MODULE ALREADY USES ONE FIELD OVER.
          // `tools/measure_far_bloom.mjs` §1 has priced the bloom share on this
          // same edge-on `n x a` since T-0209 and states its liberty for it, so
          // until now the split and the bloom were two readings of one wall in
          // two different units.
          //
          // The card count does not move. This decides what a card stands for,
          // exactly as T-0209 above left it, and the boundary itself is summed
          // off `data/flora` once per community in `farSplitOf` — no constant
          // enters it here.
          const forbs = wet ? zone.wet.forbs : zone.dry.forbs;
          const split = wet ? zone.farSplit.wet : zone.farSplit.dry;
          const forb = u >= split;
          const sp = forb
            ? dealt(forbs, zone.matrixShare - split, u - split)
            : dealt(wet ? zone.wet.graminoids : zone.dry.graminoids, split, u);
          if (!sp) return;
          const y = station(e, n, zone, sp, wet);
          if (y === null) return;
          const h = placeFarCard(farSet, sp, zone, e, y, n, rng, band);
          // ...and a flowering forb's far card carries the flower, out to the
          // distance the record's own head size stays one pixel wide — see
          // `farHeadReach`. The head sets and their material are the ones the
          // forb ring already uses, so this is instances on a mesh that is
          // drawn either way, never a new draw call.
          if (forb && h > 0 && sp.head && tune.far.minPx
            && r <= farHeadReach(sp, tune.far.minPx)) {
            maybeHead(heads, sp, e, y, n, rng, h,
              farHeadRing(sp, tune.far.minPx, _headRing));
          }
        });
    }
  }

  function* rebuildAll(camE, camN, cone) {
    openCensus();
    yield* rebuildGround(camE, camN, cone);
    yield* rebuildForbs(camE, camN, cone);
    yield* rebuildFar(camE, camN, cone);
    closeCensus();
    for (const s of sets) s.commit();
    stats.instances = sets.reduce((a, s) => a + s.mesh.count, 0);
    stats.sets = Object.fromEntries(sets.map((s) => [s.mesh.name, s.mesh.count]));
    /** T-0034. The ceiling beside the count, because `capped` answers only
     *  "is this set full" and the question a bloom measurement has to ask is
     *  "how much of its ceiling is spent" — a set at 0.31 of its cap and one at
     *  0.99 are the same row otherwise, and they are the difference between a
     *  raise a lattice can carry and one an instance budget eats. */
    stats.caps = Object.fromEntries(sets.map((s) => [s.mesh.name, s.max]));
    stats.capped = sets.filter((s) => s.mesh.count >= s.max).map((s) => s.mesh.name);
    /** T-0214. What each set was ASKED for this pass, and what it had to refuse.
     *  A set sitting on its cap is not by itself a fault — a set that refused
     *  four hundred inflorescences the records asked for is, and until this the
     *  two looked identical from outside. `shortfall` carries only the sets with
     *  something in them, so an empty object is the assertion worth making. */
    stats.demand = Object.fromEntries(sets.map((s) => [s.mesh.name, s.demand()]));
    /** Triangles ONE instance of each set costs, so a shortfall in instances can
     *  be priced in the unit the frame budget is kept in without re-deriving an
     *  archetype's geometry outside the module that built it. */
    stats.trisPer = Object.fromEntries(sets.map((s) => [s.mesh.name, s.tris]));
    stats.shortfall = Object.fromEntries(sets
      .map((s) => [s.mesh.name, s.demand() - s.mesh.count])
      .filter(([, short]) => short > 0));
    stats.triangles = sets.reduce((a, s) => a + s.mesh.count * s.tris, 0);
    stats.drawCalls = sets.filter((s) => s.mesh.count > 0).length;
  }

  const tmpV = new THREE.Vector3();
  const tmpF = new THREE.Vector3();

  return {
    group,
    stats,
    zoneAt(e, n) { return finder(e, n)?.id ?? null; },
    shoreDistance(e, n) { return water.distance(e, n); },
    /** T-0280. Which SIDE of that waterline, which `shoreDistance` cannot say —
     *  it returns a positive distance either way, to land from water and to
     *  water from land. Every lattice pass picks its species list, and the far
     *  band makes its grass-or-flower split, on this exact test, so a gate
     *  sampling the ground the far band covers asks the placer for it rather
     *  than guessing from a distance that is symmetric. */
    isWaterAt(e, n) { return water.isWater(e, n); },
    /** May a rooted plant stand here at all — the travelled track, the
     *  building footprints and the water answered in one call. A gate
     *  measuring how densely a community was planted has to divide by the
     *  ground that was actually available to it, not by the disc it sampled. */
    plantableAt(e, n) { return station(e, n, NO_COMMUNITY, null) !== null; },
    /** The station a NAMED species of the community here would be given, or null
     *  if this is not a place that species may stand. The gate asks the placer
     *  itself rather than re-deriving its rules: `substrate` is only worth
     *  recording if the thing that plants the town reads it. */
    stationOf(e, n, speciesId) {
      const zone = finder(e, n);
      const sp = zone?.byId.get(speciesId);
      if (!sp) return null;
      return station(e, n, zone, sp);
    },
    /** What each community may plant on each side of its waterline, by id. */
    substrates() {
      return zones.map((z) => ({
        id: z.id,
        dry: z.dry.graminoids.items.concat(z.dry.forbs.items, z.dry.shrubs.items)
          .map((s) => s.id),
        wet: z.wet.graminoids.items.concat(z.wet.forbs.items, z.wet.shrubs.items)
          .map((s) => s.id),
      }));
    },
    /** What each compiled community carries out of its record, so the gate can
     *  ask whether the authored number reached the renderer rather than
     *  trusting that it did. */
    communities() {
      return zones.map((z) => ({
        id: z.id, matrixShare: z.matrixShare, bareSoil: z.bareSoil,
        /** T-1056. The recorded woody band, so a reader of this report can see
         *  WHY a sand zone's shrub count stands below its recorded density. */
        woodyBand: z.woody?.establishes ?? null,
        graminoids: z.graminoids.length,
        /** ROADMAP K55. The other two strata's slot chances, which K55 moves and
         *  which nothing outside this module could read until it did — the
         *  drawn census could see the plants that arrived and not the number
         *  that asked for them, so a share sitting on its 1.0 clamp looked
         *  exactly like one that had been tuned there. `z10_settled_town` is
         *  the case: K55 multiplies its forb density and draws the same 146
         *  plants, because both sides of the change are over the ceiling. */
        forbShare: z.forbShare,
        forbShareWet: z.forbShareWet,
        shrubShare: z.shrubShare,
        /** T-0282. The shrub stratum's own over-water share, the one of the four
         *  `shareOf` deals that was never exported. Without it the ceiling
         *  declaration cannot see a quarter of the lattice it exists to state. */
        shrubShareWet: z.shrubShareWet,
        /** The sum each is dealt off, so a reader can tell a share that is
         *  clamped from one that is small. `null` for the matrix by
         *  `SLOT_BASIS` — its slot count is `matrixShare` above.
         *
         *  T-0034: `forbDensity` is the sum `forbShare` is ACTUALLY dealt off,
         *  which is now the recorded upper bound. `forbDensityMid` is the
         *  midpoint sum it was dealt off before, kept beside it so a
         *  measurement can quote the size of the raise and the ceiling that
         *  ate the rest of it without re-deriving either. */
        forbDensity: z.dry.forbs.densityHigh,
        forbDensityMid: z.dry.forbs.density,
        /** T-0019. The same sum on the WET side of the waterline, which nothing
         *  outside this module could read: `forbShareWet` is clamped exactly as
         *  `forbShare` is, so a wet layer sitting on the ceiling was
         *  indistinguishable from one tuned to it. Four of the ten communities
         *  plant a different list over water, and two of them are among the
         *  layers the clamp binds. */
        forbDensityWet: z.wet.forbs.densityHigh,
        shrubDensity: z.dry.shrubs.density,
        /** T-0282. And the sum behind `shrubShareWet`, for the same reason
         *  T-0019 exported `forbDensityWet`: a clamped share is one plant per
         *  slot whatever the slot is, so the density is what says how far a
         *  layer is from the ceiling and how much of its record it loses. */
        shrubDensityWet: z.wet.shrubs.density,
        /**
         * T-0280. The AREAL COVER each stratum's own records sum to, on each
         * side of the waterline — the quantity `matrixShare` above is already
         * in, and the one the far band's grass-or-flower split is dealt on.
         *
         * Exported beside `forbShare` rather than instead of it, because the
         * pair is the measurement: `forbShare` is the clamped slot chance the
         * split USED to read, `forbCover` is the cover it reads now, and a
         * reader that has both can state the size of the change per community
         * without re-deriving either. `matrixCover` is the graminoid subset's
         * own cover, so a reader can also check `matrix_fraction` against what
         * its own species records sum to.
         */
        matrixCover: z.dry.graminoids.cover,
        matrixCoverWet: z.wet.graminoids.cover,
        forbCover: z.dry.forbs.cover,
        forbCoverWet: z.wet.forbs.cover,
        forbCoverHigh: z.dry.forbs.coverHigh,
        forbCoverHighWet: z.wet.forbs.coverHigh,
        /**
         * T-1106. AND THE SAME FOUR STRATA AS WALLS — the silhouette-area
         * density the far band's split is dealt on since T-1106, exported beside
         * the cover it was dealt on between T-0280 and T-1106 so the size of the
         * change is arithmetic on this table and not a diff of two runs.
         *
         * `matrixSilAspect` and `forbSilAspect` are `sil / cover` per stratum —
         * the square metres of wall one square metre of that stratum's floor
         * stands up. They are the entire content of the ticket: where the two
         * aspects are equal the split does not move at all, and where the forbs
         * are the taller narrower stratum it moves by exactly their ratio.
         *
         * `matrixSil` is the graminoid subset's own sum, NOT `matrixShare`
         * converted — see `rebuildFar`, which converts the record's own
         * `matrix_fraction` by `matrixSilAspect` rather than replacing it, and
         * carries both so the choice is visible here.
         */
        matrixSil: z.dry.graminoids.sil,
        matrixSilWet: z.wet.graminoids.sil,
        matrixSilAspect: z.dry.graminoids.cover > 0
          ? z.dry.graminoids.sil / z.dry.graminoids.cover : null,
        matrixSilAspectWet: z.wet.graminoids.cover > 0
          ? z.wet.graminoids.sil / z.wet.graminoids.cover : null,
        forbSil: z.dry.forbs.sil,
        forbSilWet: z.wet.forbs.sil,
        forbSilAspect: z.dry.forbs.cover > 0
          ? z.dry.forbs.sil / z.dry.forbs.cover : null,
        forbSilAspectWet: z.wet.forbs.cover > 0
          ? z.wet.forbs.sil / z.wet.forbs.cover : null,
        silUnknown: z.dry.graminoids.silUnknown + z.dry.forbs.silUnknown
          + z.wet.graminoids.silUnknown + z.wet.forbs.silUnknown,
        /** How many of the forb records behind those sums stated no `width_m`
         *  and were therefore measured at the footprint the placer gives them,
         *  and how many converted to no count at all. The provenance of the
         *  number, exported beside it: a fifth of the sward records state no
         *  width, and a reader of this table should not have to discover that
         *  by reading the records. */
        forbCoverFallbacks: z.dry.forbs.coverFallbacks,
        forbCoverFallbacksWet: z.wet.forbs.coverFallbacks,
        coverUnknown: z.dry.graminoids.coverUnknown + z.dry.forbs.coverUnknown
          + z.wet.graminoids.coverUnknown + z.wet.forbs.coverUnknown,
      }));
    },
    /** The lattice/fade rings and the rebuild step, for the gate that checks a
     *  plant cannot arrive already grown. The far band is deliberately NOT a
     *  layer here: it carries no fade ring for that gate to inset, and the
     *  invariant it does carry is the one below. */
    rings: { step, layers: rings },
    /**
     * T-0034. The forb lattice's own geometry — the ceiling `forbShareOf`
     * clamps against, stated rather than re-derived in a tool.
     *
     * `forbShare` alone cannot say how far a community is from the clamp in
     * PLANTS: a share of 1.0 is one plant per slot whatever the slot is, and
     * what a raise buys is decided by how much ground a slot stands for. K58's
     * six clamped layers are all one number away from that ceiling and nothing
     * outside this module could name it.
     *
     * It is `TUNE.forb`, not `tune.forb`: `forbShareOf` reads the base tune, so
     * the ceiling is the same at every detail setting and only the RING the
     * lattice is dealt over shrinks with `light`.
     */
    forbLattice: {
      cell: TUNE.forb.cell,
      perCell: TUNE.forb.perCell,
      /** Ground one lattice slot stands for, m². */
      slotArea: (TUNE.forb.cell ** 2) / TUNE.forb.perCell,
      /** The most plants per m² this lattice can carry: one per slot. */
      ceilingPerM2: TUNE.forb.perCell / (TUNE.forb.cell ** 2),
    },
    /** T-0086. The far band's own tuning and its ramp, so a measurement asks
     *  the placer what fraction of the ground carries a card at `d` rather than
     *  re-deriving it. Zero at both ends is the assertion worth making. */
    farBand: { ...tune.far, coverAt: (d) => farCoverAt(d, tune.far) },
    /**
     * The height multiplier the vertex shader gives an instance of `setName`
     * standing `d` metres from the camera — the same ramp, in JS.
     *
     * `outer` is that instance's OWN outer radius, off its `aChiRing`. Pass it:
     * since the outer boundary carries a per-slot fringe, the layer's nominal
     * ring answers for no particular plant, and it answers ZERO for one the
     * fringe pushed out — which would report a pop-in gate green by not looking
     * at the instances that can pop.
     */
    fadeAt(setName, d, outer) {
      const ring = ringOfSet[setName];
      if (!ring) return null;
      return fadeOf(slotOf(ring, outer), d);
    },
    /** What fraction of its recorded height this plant is drawn at — `heightOf`,
     *  reached the same way `fadeAt` reaches `fadeOf`. Since T-0035 a drawn
     *  plant is drawn whole, so this is 1 wherever `fadeAt` is above zero. */
    heightAt(setName, d, outer) {
      const ring = ringOfSet[setName];
      if (!ring) return null;
      return heightOf(slotOf(ring, outer), d);
    },
    /** Where this ground's own boundary stands relative to its layer's nominal
     *  one, in metres. The gate asks the placer rather than re-deriving the
     *  noise, which is the rule the substrate work set. */
    fringeAt(layer, e, n) {
      const r = rings[layer];
      return r ? fringeOf(e, n, r.fringe) : null;
    },

    /** This ground's share of a spread band, in `[0, 1)` — `handoverRank`, on
     *  the same terms `fringeAt` offers the fringe. `which` is 0 for an outer
     *  boundary and 1 for an inner one, as in `slotRing`.
     *
     *  T-0277 asks what a DENSITY handover would cost on the two outer edges
     *  that still ramp (`TUNE.mid.band`, `TUNE.forb.band`), and the only honest
     *  way to answer is to deal each placed slot the rank it would actually get
     *  and see where the drawn boundary lands. Re-deriving the hash in the tool
     *  would answer a question about the tool's copy of it; this asks the
     *  placer, which is the rule `fringeAt` set.
     */
    handoverAt(e, n, which = 0) { return handoverRank(e, n, which); },

    async prepare(camera, checkpoint = () => null, onProgress = () => {}) {
      camera.getWorldPosition(tmpV); camera.getWorldDirection(tmpF);
      const e = tmpV.x, n = -tmpV.z;
      const fl = Math.hypot(tmpF.x, tmpF.z) || 1;
      const fe = tmpF.x / fl, fn = -tmpF.z / fl;
      for (const row of rebuildAll(e, n, { fe, fn, cos: CONE_COS })) {
        onProgress(row.done, row.total);
        const pause = checkpoint(); if (pause) await pause;
      }
      centres.near = { e, n }; centres.yaw = Math.atan2(fe, fn);
    },

    update(dt, camera) {
      uniforms.uChiTime.value += dt * TUNE.wind.speedNear;
      if (!sunFound) {
        sunFound = sunFromScene(group, uniforms, problems);
      }
      if (!camera) return;
      camera.getWorldPosition(tmpV);
      const e = tmpV.x;
      const n = -tmpV.z;

      // Forward in ENU; -Z is north (terrain.js).
      camera.getWorldDirection(tmpF);
      const fl = Math.hypot(tmpF.x, tmpF.z) || 1;
      const fe = tmpF.x / fl;
      const fn = -tmpF.z / fl;
      const yaw = Math.atan2(fe, fn);
      const turned = centres.yaw === null
        || Math.abs(((yaw - centres.yaw + Math.PI * 3) % (Math.PI * 2)) - Math.PI)
           > CONE_YAW_STEP;
      if (turned || moved(centres.near, e, n, step)) {
        for (const _ of rebuildAll(e, n, { fe, fn, cos: CONE_COS })) { /* runtime synchronous path */ }
        centres.near = { e, n };
        centres.yaw = yaw;
      }
    },

    dispose() {
      for (const d of disposables) d?.dispose?.();
    },
  };
}

/** What it returns when there is nothing it is allowed to draw. */
function inertRig(group, stats) {
  return {
    group,
    stats,
    zoneAt() { return null; },
    update() {},
    dispose() {},
  };
}

function moved(centre, e, n, step) {
  if (!centre) return true;
  return Math.hypot(e - centre.e, n - centre.n) > step;
}

/** SUN_FALLBACK as a direction, in three's axes: +x east, +y up, -z north. */
function sunDirFallback() {
  const az = SUN_FALLBACK.azimuthDeg * Math.PI / 180;
  const el = SUN_FALLBACK.elevationDeg * Math.PI / 180;
  const horiz = Math.cos(el);
  return new THREE.Vector3(
    Math.sin(az) * horiz, Math.sin(el), -Math.cos(az) * horiz,
  ).normalize();
}

/**
 * Find the sun the SCENE already built and light the sward with it.
 *
 * main.js mounts this module with no reference to world.js, so the light is
 * found by walking up from our own group to the scene root. That is deliberate
 * rather than lazy: world.js derives the sun from the scene record's date,
 * latitude and local mean time, and a second sun invented here would light the
 * prairie from one direction and the buildings from another in the same frame.
 * If there is no directional light to find, the fallback is used and SAID —
 * silently lighting the sward from a guessed sun is the class of error this
 * project exists to avoid.
 *
 * @returns {boolean} true once it has an answer, right or fallback.
 */
function sunFromScene(group, uniforms, problems) {
  let root = group;
  while (root.parent) root = root.parent;
  if (root === group) return false;          // not mounted yet; ask again
  let sun = null;
  let sky = null;
  root.traverse((o) => {
    if (!sun && o.isDirectionalLight) sun = o;
    if (!sky && o.isHemisphereLight) sky = o;
  });
  if (!sun) {
    problems.push('flora: the scene carries no directional light — the sward is lit by '
      + `flora.js's own fallback sun (${SUN_FALLBACK.elevationDeg}° up, bearing `
      + `${SUN_FALLBACK.azimuthDeg}°) and may not agree with the rest of the frame`);
    return true;
  }
  sun.updateWorldMatrix(true, false);
  sun.target?.updateWorldMatrix(true, false);
  const from = new THREE.Vector3().setFromMatrixPosition(sun.matrixWorld);
  const to = sun.target
    ? new THREE.Vector3().setFromMatrixPosition(sun.target.matrixWorld)
    : new THREE.Vector3();
  uniforms.uChiSun.value.copy(from).sub(to).normalize();
  const i = sun.intensity;
  uniforms.uChiSunCol.value.set(sun.color.r * i, sun.color.g * i, sun.color.b * i);
  // The sky fill, from the scene's published value rather than from a light.
  //
  // world.js used to deliver the fill as a HemisphereLight, which this could
  // read; since W1 it delivers it as an environment map, which a Lambert
  // material cannot see at all — three applies `scene.environment` to the
  // physical materials only. Sniffing the light list would therefore have found
  // nothing and left the sward on its default, lighting the prairie by one sky
  // and the town beside it by another: the same class of error the sun above is
  // traversed for rather than invented. `scene.userData.chiSkyFill` is the
  // contract, the hemisphere light stays a fallback for any scene that still
  // ships one, and a scene offering neither says so instead of guessing.
  const fill = root.userData?.chiSkyFill;
  if (Array.isArray(fill) && fill.length === 3) {
    uniforms.uChiSky.value.set(fill[0], fill[1], fill[2]);
  } else if (sky) {
    const j = sky.intensity;
    uniforms.uChiSky.value.set(sky.color.r * j, sky.color.g * j, sky.color.b * j);
  } else {
    problems.push('flora: the scene publishes no sky fill and carries no hemisphere '
      + "light — the sward is lit by flora.js's own default ambient and may not "
      + 'agree with the rest of the frame');
  }
  return true;
}

function mergeTune(level) {
  const t = {
    near: { ...TUNE.near }, mid: { ...TUNE.mid }, forb: { ...TUNE.forb },
    far: { ...TUNE.far }, cap: { ...TUNE.cap }, step: { ...TUNE.step },
  };
  const preset = level === 'light' ? LOW : level === 'balanced' ? MID : null;
  if (preset) {
    Object.assign(t.near, preset.near);
    Object.assign(t.mid, preset.mid);
    Object.assign(t.forb, preset.forb);
    Object.assign(t.far, preset.far);
    Object.assign(t.cap, preset.cap);
  }
  return t;
}

/* -------------------------------------------------------------------------- */
/* the records                                                                 */
/* -------------------------------------------------------------------------- */

async function getJSON(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`);
  return res.json();
}

/** One fetch for the manifest, then exactly the files it names — never a probe.
 *  A 404 in the network log is indistinguishable from a broken boot. */
async function loadFlora(dataBase, problems) {
  if (!dataBase) {
    problems.push('flora: no data base URL — nothing is planted');
    return null;
  }
  let index;
  const indexUrl = new URL('flora/index.json', dataBase);
  try {
    index = await getJSON(indexUrl);
  } catch (err) {
    problems.push(`flora: ${err.message} — no vegetation is drawn, and the ground is `
      + 'the bare terrain surface');
    return null;
  }
  if (!Array.isArray(index.zones) || !index.zones.length) {
    problems.push('flora: the manifest lists no zones — no vegetation is drawn');
    return null;
  }
  const files = new Map();
  const wanted = [
    ...index.zones.map((z) => ['zone', z.id, z.file]),
    ...(index.palettes ?? []).map((p) => ['palette', p.id, p.file]),
  ];
  const loaded = await Promise.all(wanted.map(async ([kind, id, file]) => {
    if (!file) return [kind, id, null, 'the manifest gave no file'];
    try {
      return [kind, id, await getJSON(new URL(`flora/${file}`, dataBase)), null];
    } catch (err) {
      return [kind, id, null, err.message];
    }
  }));
  for (const [kind, id, body, why] of loaded) {
    if (!body) { problems.push(`flora: ${kind} ${id} — ${why}`); continue; }
    files.set(`${kind}:${id}`, body);
  }
  return { index, files };
}

/**
 * ROADMAP K55 — WHICH SUM EACH STRATUM'S SLOT COUNT IS DEALT OFF, IN ONE PLACE.
 *
 * A slot count is a number of plants standing on a square metre of ground, so
 * the only sum that can answer it is a sum of plants per square metre. Both
 * lattice-dealt strata now read `stems`, which is the record's own abundance in
 * that unit whatever field it was written in.
 *
 * **The matrix is `null`, and that is the parcel's own refusal made explicit.**
 * K55 was opened against four lists and named three matrix ones among them, but
 * a matrix slot count is `cover.matrix_fraction` read off the record directly —
 * it has never come off this sum, so there was nothing in those rows to move.
 * The sum was computed for the matrix anyway and read by nobody, which is how a
 * report came to name three refusals as work: the column printed the DEFAULT
 * argument rather than a fact about the renderer. `null` deletes the number
 * instead of relabelling it, so the next reader gets nothing to misuse.
 *
 * `auditAbundance` prints from this same object, so the report cannot drift
 * from the rule again.
 */
const SLOT_BASIS = { matrix: null, forb: 'stems', shrub: 'stems' };

/** Per zone: a weighted graminoid list, a weighted forb list, colours, extent. */
function compileZones({ index, files }, terrain, problems, stats) {
  const seenForms = new Set();
  const out = [];
  // The manifest PUBLISHES the shape vocabulary, so a value added there and
  // not here is a flower the renderer would silently drop. Caught at boot,
  // once, against the list itself rather than against whatever happens to be
  // planted near the visitor.
  for (const shape of index.vocabulary?.inflorescence_shapes ?? []) {
    if (!HEAD_OF_SHAPE[shape]?.kind) {
      stats.unimplementedShapes.push(shape);
      problems.push(`flora: the manifest publishes inflorescence shape '${shape}' and this `
        + 'renderer has no archetype for it — any species recording it draws no flower');
    }
  }
  const byPriority = [...index.zones]
    .map((z) => ({ ...z, record: files.get(`zone:${z.id}`) }))
    .filter((z) => {
      if (!z.record) return false;
      if (!Array.isArray(z.record.species)) {
        problems.push(`flora: zone ${z.id} carries no species list`);
        return false;
      }
      return true;
    });

  for (const entry of byPriority) {
    const rec = entry.record;
    const palette = files.get(`palette:${rec.palette ?? entry.palette}`) ?? null;
    const graminoids = [];
    const forbs = [];
    /**
     * ROADMAP K54 — THE SHRUB LAYER IS A STRATUM, NOT A TALL FORB, AND IT IS
     * DEALT ON ITS OWN LATTICE.
     *
     * K53 drew the twenty-one `shrub_low` records with their own archetype and
     * measured why only fourteen of them stood: they were competing for the
     * forb layer's slots on plants per square metre, against a wild leek at 40.
     * A slot is one plant and the forb lattice carries one plant per 2.89 m² of
     * ground, so where the herb layer's own density saturates that lattice —
     * which it does in five of the ten communities — the deal becomes a
     * count-proportional SUBSAMPLE, and a subsample by count thins the shrubs
     * by the whole saturation ratio. In the wet woods that ratio is 117.
     *
     * The two are not competing for the same ground in the first place. A hazel
     * clump stands OVER the leeks, and its record says so: nine `shrub_low`
     * records in `z06_dense_forest` sum to 92 % ground cover while the herb
     * layer beneath them is recorded separately at 40 plants per m². So the
     * shrubs are dealt from their OWN lattice pass, at their own recorded
     * density, and nothing is taken from the herb layer to pay for them.
     */
    const shrubs = [];

    for (const sp of rec.species) {
      if (!OUR_ROLES.has(sp.role)) continue;          // trees.js draws the rest
      const form = sp.form;
      const isGrass = GRAMINOID_FORMS.has(form);
      const isForb = FORB_FORMS.has(form);
      if (!isGrass && !isForb) {
        if (!seenForms.has(form)) {
          seenForms.add(form);
          stats.unimplementedForms.push(form);
          problems.push(`flora: form '${form}' is not implemented — `
            + `${sp.id ?? sp.binomial} is recorded and not drawn`);
        }
        continue;
      }
      const built = buildSpecies(sp, palette, problems, entry.id);
      if (!built) continue;
      stats.species++;
      if (isGrass) graminoids.push(built);
      else if (built.form === 'shrub_low') shrubs.push(built);
      else forbs.push(built);
    }

    /**
     * ROADMAP K49(c2) — THE LOTTERY IS DEALT ON PLANTS PER SQUARE METRE, AND
     * THE SLOT COUNT IS NOT.
     *
     * Two different questions had been answered off one number. How many slots
     * a list is dealt is a question about GROUND — the forb layer's own summed
     * density, the matrix layer's recorded `matrix_fraction` — and which
     * species fills a dealt slot is a question about the POPULATION standing on
     * it. K49(a) found the second one being answered by normalising three
     * different units against each other, so a species recorded as covering
     * 25 % of the ground was dealt slots as though it were 0.25 plants per
     * square metre, against a neighbour recorded at 6 plants per square metre.
     * The two-metre dogwood and the wild garlic, made identical by a division.
     *
     * `stems` is the record's own abundance read as a count — K49(c1) closed
     * the last gap in it, so all 98 sward records carry one — and the lottery
     * is normalised over THAT. The recorded sum was kept separately and set
     * `forbShare`, so K49(c2) moved no slot at all: it changed what fills a
     * slot, never how many are filled. `matrixShare` is read off the record
     * directly and was never in the arithmetic at all.
     *
     * The shares it moves are quoted in ROADMAP K49(c1), measured before this
     * half was written so it could not choose its own bar.
     *
     * ROADMAP K55 FINISHED IT, and the slot count moves this time — the two
     * lattice strata are dealt off `stems` as well (`SLOT_BASIS`), so the sum
     * below survives only as the lottery's fallback for a species with no
     * derivable count. There is no such species today.
     */
    for (const s of [...graminoids, ...forbs, ...shrubs]) {
      /** The abundance exactly as recorded, in whatever unit the record used.
       *  Read only where `stems` is null, which K49(c1) closed across all 98
       *  sward records — it is the fallback and not a second opinion. */
      s.recorded = s.weight;
      s.weight = s.stems ?? s.recorded;
    }
    const lotOf = (list) => list.reduce((t, s) => t + s.weight, 0);
    for (const list of [graminoids, forbs, shrubs]) {
      const total = lotOf(list);
      if (total > 0) for (const s of list) s.weight /= total;
    }

    // How much of the ground a community's matrix actually covers is AUTHORED,
    // per zone, in the record's own `cover` block — and nothing in this
    // renderer had ever asked for it. Every one of the ten communities was
    // planted at the single lattice density L32 tuned on the closed
    // wet-prairie sward, so the settled town (`bare_soil_fraction: 0.45` by
    // its own record), the shaded riverbank understory (`matrix_fraction`
    // 0.45) and the lakeshore sand (0.35) were all drawn as densely as prairie
    // that covers the ground completely. `tools/validate.py` gates this field
    // on every run and `index.json` denormalises `bare_soil_fraction` so the
    // ground shader can fetch it once: the number was written, checked and
    // shipped to the browser, and then never read.
    //
    // It is a probability directly, and that is the whole reason 1.0 is the
    // anchor rather than some scaling: a zone recording full matrix cover is
    // planted exactly as it was before, so the density tuned against the
    // reference photographs is untouched, and no zone can ask for more
    // geometry than the lattice already carries.
    const cover = rec.cover ?? {};
    let matrixShare = cover.matrix_fraction;
    if (typeof matrixShare !== 'number' || !(matrixShare >= 0)) {
      problems.push(`flora: zone ${entry.id} records no cover.matrix_fraction — its sward `
        + 'falls back to a fully closed one, which is a claim its record does not make');
      matrixShare = 1;
    }

    // A COMMUNITY IS NOT THE SAME LIST ON BOTH SIDES OF ITS WATERLINE. The marsh
    // record carries cattails, bulrushes and two floating-leaved water lilies,
    // and only the lilies are impossible on the bank. So each side gets its own
    // legal subset, drawn from with the weights RENORMALISED over that subset:
    // the recorded cover still decides how many slots carry a plant, and what
    // fills a slot is whatever can actually stand there.
    //
    // Filtering at the pick rather than dropping the slot at the station is the
    // whole point. A slot that picked a water lily on dry ground and was then
    // refused would simply be empty, which would thin the dry marsh edge by the
    // lilies' 6.5 % share of that sward — the record's `matrix_fraction` says
    // 0.75 there, and it does not stop meaning 0.75 because two of its species
    // cannot stand on a bank.
    const subsetOn = (list, wet, basis) => {
      const items = list.filter((s) => (
        wet ? s.substrate !== 'soil' : s.substrate !== 'open_water'));
      return {
        items,
        total: items.reduce((a, s) => a + s.weight, 0),
        /** The subset's abundance summed as PLANTS PER SQUARE METRE, which is
         *  the unit a slot count is in. `SLOT_BASIS` says which sum each
         *  stratum's is dealt off, and for the matrix the honest answer is that
         *  there is no sum: `null`, so a reader that reaches for one gets
         *  nothing rather than a number that means nothing.
         *
         *  ROADMAP K49(c2) moved the LOTTERY onto `stems` and left the slot
         *  count on the recorded sum, saying so. K54 moved the SHRUB stratum's
         *  count across. K55 moves the FORB stratum's, which is the last one
         *  dealt off this sum at all — a list mixing a cover fraction with a
         *  count was adding an area to a number of plants, exactly K49(a)'s
         *  fault one level up, and the two entirely area-recorded forb lists
         *  (`z05_riverbank_timber`, `z10_settled_town`) never registered as
         *  mixed because a list needs both units to look inconsistent.
         *
         *  `stems` is not a new number: it is the record's own cover divided by
         *  what one plant of that species covers, `stems × π(width/2)²`
         *  inverted, on the width K49(c1) put on all 98 sward records. */
        density: basis === null ? null
          : items.reduce((a, s) => a + (s.stems ?? 0), 0),
        /** T-0034. The same sum at the top of every record's own range. See
         *  `stemsHigh`: it is the FORB stratum's slot count that is dealt off
         *  this, and nothing else reads it. */
        densityHigh: basis === null ? null
          : items.reduce((a, s) => a + (s.stemsHigh ?? s.stems ?? 0), 0),
        /**
         * T-0280. The subset's abundance summed as the FRACTION OF GROUND IT
         * COVERS — `coverOf` over the subset — which is the same quantity, in
         * the same unit, as the `cover.matrix_fraction` sitting in `matrixShare`
         * below.
         *
         * It is not a slot count and it is not `basis`-gated: every stratum has
         * an areal cover whether or not its slots are dealt off a sum, and the
         * matrix's is exactly the number a reader would want to check
         * `matrix_fraction` against. What reads it is the far band's
         * grass-or-flower split, which needs a RATIO and therefore needs both
         * of its sides to be the same kind of number.
         *
         * `coverHigh` is the same sum at the top of each recorded range, the
         * end T-0034 deals the forb RING off. The split does not use it — see
         * `rebuildFar` — and it is carried so the choice can be seen and
         * re-argued without re-deriving it.
         *
         * It is the `drawn` reading: a record with no `width_m` contributes the
         * footprint the placer gives it rather than nothing at all. `fallbacks`
         * counts how many of the items that was, so no reader has to take the
         * sum's provenance on trust, and `coverUnknown` counts the items whose
         * abundance does not convert to a count at all — expected to be zero
         * since K49(c1), and exported so that expectation is checkable.
         */
        cover: items.reduce((a, s) => a + (coverOf(s, { drawn: true }) ?? 0), 0),
        coverHigh: items.reduce(
          (a, s) => a + (coverOf(s, { drawn: true, high: true }) ?? 0), 0),
        coverFallbacks: items.filter((s) => !s.width).length,
        coverUnknown: items.filter((s) => coverOf(s, { drawn: true }) === null).length,
        /**
         * T-1106. THE SAME SUBSET AS A WALL — `silhouetteOf` over the subset,
         * m² of upright silhouette per m² of ground. The far band's split reads
         * this; `cover` is kept beside it because the PAIR is the measurement
         * and because every other reader of a stratum's abundance is asking
         * about ground.
         *
         * `silAspect` on `communities()` is the conversion these sums embody,
         * `sil / cover` — the
         * abundance-weighted mean of `4h / (pi w)` over the subset, which is how
         * many square metres of wall one square metre of this stratum's floor
         * stands up. It is exported because it is the whole content of the
         * change: a stratum of tall narrow plants and one of low broad ones can
         * hold the same ground and not the same sky, and this number says by how
         * much. `silUnknown` counts the items that convert to no silhouette at
         * all — a missing `height_m`, which no sward record has today and which
         * is exported so that stays checkable.
         */
        sil: items.reduce((a, s) => a + (silhouetteOf(s, { drawn: true }) ?? 0), 0),
        silHigh: items.reduce(
          (a, s) => a + (silhouetteOf(s, { drawn: true, high: true }) ?? 0), 0),
        silUnknown: items.filter((s) => silhouetteOf(s, { drawn: true }) === null).length,
      };
    };

    const cell = TUNE.forb.cell;
    /** Chance one lattice slot of the forb-ring cell carries a plant: a
     *  stratum's own plants per m² times the ground one slot stands for. The
     *  clamp is the lattice's ceiling of one plant per slot and is the only
     *  bound in it — see K54's note on the wet woods, the one community whose
     *  recorded shrub density reaches it, and K58, which is the open parcel on
     *  what that clamp costs the six communities already sitting on it. */
    const shareOf = (density) => Math.min(
      1, density * cell * cell / TUNE.forb.perCell);
    /**
     * T-1106. THE FAR BAND'S GRASS-OR-FLOWER BOUNDARY, ONE NUMBER PER SIDE OF
     * THE WATERLINE, decided here rather than per lattice slot.
     *
     * `u < matrixShare` still says whether the slot is occupied at all — that is
     * T-0209's arrangement and does not move. This says WHERE inside that range
     * the grass ends and the flowering plants begin, and both of the quantities
     * it is dealt on are SILHOUETTE-AREA DENSITIES (`silhouetteOf`), because the
     * far band is a wall seen edge-on and not a floor seen from above.
     *
     * THE MATRIX SIDE IS THE RECORD'S OWN COVER, CONVERTED — not the graminoid
     * subset's raw sum. `cover.matrix_fraction` is a single authored figure and
     * T-0280 chose it deliberately over what the species rows happen to sum to;
     * this keeps that choice and multiplies it by the stratum's own measured
     * aspect, `sil / cover`, so the change of unit is the only thing T-1106
     * does. `matrixSil` on `communities()` carries the raw sum beside it for a
     * reader who wants to check the two against each other.
     *
     * A community whose matrix records give no silhouette to convert by keeps
     * the pre-T-1106 arrangement of dividing covers, which is the same refusal
     * `measure_far_bloom.mjs` §1 makes for the marsh: no silhouette, no ratio
     * between silhouettes.
     */
    const farSplitOf = (matrixShare, side) => {
      const aspect = side.graminoids.cover > 0
        ? side.graminoids.sil / side.graminoids.cover : null;
      const matrixSide = aspect === null ? matrixShare : matrixShare * aspect;
      const forbSide = aspect === null ? side.forbs.cover : side.forbs.sil;
      if (!side.forbs.items.length || !(forbSide > 0) || !(matrixSide > 0)) return matrixShare;
      return matrixShare * (1 - forbSide / (matrixSide + forbSide));
    };
    const dry = {
      graminoids: subsetOn(graminoids, false, SLOT_BASIS.matrix),
      forbs: subsetOn(forbs, false, SLOT_BASIS.forb),
      shrubs: subsetOn(shrubs, false, SLOT_BASIS.shrub),
    };
    const wet = {
      graminoids: subsetOn(graminoids, true, SLOT_BASIS.matrix),
      forbs: subsetOn(forbs, true, SLOT_BASIS.forb),
      shrubs: subsetOn(shrubs, true, SLOT_BASIS.shrub),
    };
    out.push({
      id: entry.id,
      zone: entry.zone,
      extent: rec.extent ?? entry.extent ?? null,
      priority: rec.extent?.priority ?? entry.priority ?? 0,
      standsInWater: rec.extent?.kind === 'buffer' && rec.extent?.of === 'water'
        && (wet.graminoids.items.length > 0 || wet.forbs.items.length > 0
          || wet.shrubs.items.length > 0),
      graminoids,
      forbs,
      shrubs,
      /** The same two lists split by `substrate`: what may be planted on the
       *  dry side of the waterline, and what may be planted over water. */
      dry,
      wet,
      /** Every drawn species of this community by id, so a gate can ask the
       *  placer about one by name. */
      byId: new Map([...graminoids, ...forbs, ...shrubs].map((s) => [s.id, s])),
      /** Chance a matrix lattice slot is used at all: the record's own
       *  `cover.matrix_fraction`. Clamped only because a fraction over 1 would
       *  be a bookkeeping error the validator already refuses. */
      matrixShare: clamp01(matrixShare),
      /** T-1106. Where the grass ends inside that occupied range, per side of
       *  the waterline — see `farSplitOf`. Constant per community, so the far
       *  band's per-slot work is a comparison and not a ratio. */
      farSplit: {
        dry: farSplitOf(clamp01(matrixShare), dry),
        wet: farSplitOf(clamp01(matrixShare), wet),
      },
      /**
       * T-1056 SETTLED WHAT THIS FIELD GATES, AND THE ANSWER IS NOTHING.
       *
       * `matrix_fraction` above is read as a probability because it is an AREAL
       * cover fraction and a slot count for an areal layer is a fraction of
       * ground. `bare_soil_fraction` is not its mirror: the herb and woody
       * strata are recorded as COUNTS — stems per m², clumps per hectare — and
       * thinning a count by an area fraction adds an area to a number of
       * plants, which is K49(a)'s and K55's unit error one level up. A shrub
       * also stands OVER the herb layer rather than instead of it (K54), so
       * bare soil under a sand cherry is not ground the sand cherry failed to
       * take. So this stays a record-only claim, read by the ground shader and
       * by the drawn census and by nothing else — written here, in
       * data/flora/index.json's `_doc` and in docs/LIBERTIES.md L32, so the
       * next parcel to reach for it finds the refusal rather than re-deciding.
       * The sand bar's even scatter of scrub was NOT this field's to fix: it is
       * `woody_stratum` below, an elevation bound in the unit an elevation is
       * in.
       */
      bareSoil: typeof cover.bare_soil_fraction === 'number' ? cover.bare_soil_fraction : null,
      /**
       * T-1056 — THE ELEVATION BAND THE WOODY STRATUM ESTABLISHES ACROSS, read
       * off the record and handed to `station` as-is.
       *
       * `applies_to_roles` is the record's own list and is kept as a Set rather
       * than hard-coded to `shrub_low`, because the same band binds the roles
       * `trees.js` draws (`tree`, `thicket`) and the two renderers have to be
       * reading ONE claim. `tools/validate.py` gates the range, the datum, the
       * roles against the index vocabulary and the grading, and refuses a band
       * that binds no species this zone records — so an absent block here means
       * the zone states no bound, never that one was dropped.
       */
      woody: (() => {
        const w = rec.woody_stratum;
        if (!w) return null;
        const band = w.establishes_m;
        if (!Array.isArray(band) || band.length !== 2 || !(band[0] < band[1])) {
          problems.push(`flora: zone ${entry.id} records a woody_stratum whose `
            + 'establishes_m is not a rising [low, high] band, so no woody bound is applied');
          return null;
        }
        return { establishes: band, roles: new Set(w.applies_to_roles ?? []) };
      })(),
      /**
       * Chance a forb lattice slot is used, from the record's own densities —
       * per side, because the legal subset is what stands there.
       *
       * T-0034 — AT THE TOP OF THE RECORDED RANGE, NOT ITS MIDDLE. The ticket
       * was "raise the bloom", and the owner's ruling on it allows the bloom to
       * be tuned as a reconstructed value provided the bound is stated. The
       * bound taken is the tightest one available: each species' own recorded
       * upper figure, so the town is a prairie at the dense end of what its
       * sources describe and not one plant past it (docs/LIBERTIES.md L182).
       *
       * It moves three communities and only three — the mesic prairie
       * (0.809 → 1.000), the wet prairie (0.798 → 1.000) and the sand prairie
       * (0.210 → 0.329). The other six forb layers were already over the
       * lattice's ceiling before this and are unchanged by it, which is K58 and
       * not this ticket: past the clamp a bigger number draws nothing.
       */
      forbShare: shareOf(dry.forbs.densityHigh),
      forbShareWet: shareOf(wet.forbs.densityHigh),
      /** ROADMAP K54. The same question of the shrub stratum's own lattice, off
       *  its own recorded clump density. Nothing here is taken from the forb
       *  layer: the two passes are independent draws over the same ring — and
       *  T-0034's upper-bound reading is deliberately NOT applied here, because
       *  a denser shrub stratum is more bushes and not more bloom. */
      shrubShare: shareOf(dry.shrubs.density),
      shrubShareWet: shareOf(wet.shrubs.density),
      matColor: meanColor(graminoids, palette),
      palette,
    });
  }
  out.sort((a, b) => b.priority - a.priority);
  for (let i = 1; i < out.length; i++) {
    if (out[i].priority === out[i - 1].priority) {
      problems.push(`flora: ${out[i - 1].id} and ${out[i].id} share priority `
        + `${out[i].priority} — which community wins where they overlap is undefined`);
      break;
    }
  }
  return out.filter((z) => z.extent);
}

/**
 * ROADMAP K49(a) — WHICH LISTS DEAL THEIR SLOTS OFF NUMBERS THAT ARE NOT IN THE
 * SAME UNIT, and which records cannot be converted into one.
 *
 * Reported and NOT gated, deliberately, the way R-M1 splits a measurement from
 * the bar it will eventually be held to: the repair needs a footprint this
 * dataset does not carry for every species, so a gate here today would either
 * fail the build over data nobody has researched yet or be satisfied by an
 * invented number. Both are worse than a figure printed every run. K49(c) is
 * the fix, and it starts by closing `unconvertible`.
 *
 * K49(c1) CLOSED `unconvertible`: the twenty-five sward records that gave a
 * cover and no footprint carry one now, each graded in its own
 * `width_provenance` because no source states one, and `tools/validate.py`
 * refuses a new sward record that carries a cover without a width. So this
 * list is expected to be EMPTY and an entry in it is a defect rather than a
 * research gap. `mixed` stays non-empty and stays a report: a list whose
 * species record their abundance in different fields is a fact about the
 * dataset, and it stops being a FAULT when K49(c2) deals the slots on `stems`.
 *
 * `mixed` is one row per (community, list) whose species do not agree on what
 * their abundance measures. `countedShare` is how much of that list's slot
 * lottery is currently held by its COUNT-recorded species — the share that is
 * being compared against an area and therefore means nothing as it stands.
 *
 * ROADMAP K54 — AND `basis` IS WHICH SUM THE LIST'S SLOT COUNT IS DEALT OFF,
 * because that is where the mixing still bites. K49(c2) moved the LOTTERY onto
 * `stems` and said in as many words that the slot count was left on the recorded
 * sum; a list dealt off `recorded` while mixing an area with a count is
 * therefore still adding cover fractions to plants per m², and that arithmetic
 * planted `z05_riverbank_timber`'s understory at 8.8× its own record.
 *
 * ROADMAP K55 CLOSED IT, and `basis` now comes from `SLOT_BASIS` rather than
 * from a rule written twice. Both lattice strata read `stems`; the matrix reads
 * `null` because its slot count is `cover.matrix_fraction` and never this sum,
 * so its `mixed` row is about the LOTTERY only and there is nothing in it to
 * move. That is why the column used to name three matrix rows as K55 work: it
 * printed `subsetOn`'s default argument, not what the renderer does with the
 * list. A mixed row is a fact about the dataset from here on, not a defect.
 */
function auditAbundance(zones) {
  const mixed = [];
  const unconvertible = [];
  let lists = 0;
  for (const z of zones) {
    for (const [list, items] of [['matrix', z.graminoids], ['forb', z.forbs],
      ['shrub', z.shrubs]]) {
      if (!items.length) continue;
      lists++;
      let counted = 0;
      let countedShare = 0;
      let area = 0;
      for (const s of items) {
        if (s.unit === 'cover_fraction') {
          area++;
          // The weights are already normalised over the list, so `weight` IS
          // the share of the slots this species is dealt today.
          if (s.stems === null) unconvertible.push({ zone: z.id, list, id: s.id, share: s.weight });
        } else if (s.unit !== 'none') {
          counted++;
          countedShare += s.weight;
        }
      }
      if (counted > 0 && area > 0) {
        mixed.push({
          zone: z.id, list, species: items.length, counted, area, countedShare,
          basis: SLOT_BASIS[list] ?? null,
        });
      }
    }
  }
  return { lists, mixed, unconvertible };
}

/** One species entry, reduced to numbers the placer can use per instance. */
function buildSpecies(sp, palette, problems, zoneId) {
  const h = sp.height_m;
  if (!Array.isArray(h) || h.length !== 2 || !(h[1] > 0)) {
    problems.push(`flora: ${zoneId}/${sp.id ?? sp.binomial} has no usable height_m`);
    return null;
  }
  const july = sp.july ?? {};
  const veg = july.phenology === 'vegetative' || july.phenology === 'budding';
  let inflor = july.inflorescence ?? null;
  if (veg && inflor) {
    // CONTRACT.md §5.4 rule 1. The record contradicts itself; the July gate wins
    // and the head is not drawn, because a flowering culm on a vegetative grass
    // is the error the whole season check exists to prevent.
    problems.push(`flora: ${zoneId}/${sp.id ?? sp.binomial} is '${july.phenology}' and `
      + 'still carries an inflorescence — no head is drawn; the record needs fixing');
    inflor = null;
  }
  const greens = palette?.greens ?? [];
  const base = rgb(july.foliage_rgb) ?? rgb(greens[1]) ?? [0.32, 0.40, 0.17];
  const alt = rgb(july.foliage_rgb_alt) ?? rgb(greens[2]) ?? base;

  const ab = sp.abundance ?? {};
  let weight = 0;
  if (Array.isArray(ab.cover_fraction)) weight = mid(ab.cover_fraction);
  else if (Array.isArray(ab.density_per_ha)) weight = mid(ab.density_per_ha) / 10000;
  else if (Array.isArray(ab.stems_per_m2)) weight = mid(ab.stems_per_m2);
  if (!(weight > 0)) weight = 0.01;

  /**
   * ROADMAP K49(a) — THREE UNITS, ONE SUM, AND THE SUM IS WHAT DEALS THE SLOTS.
   *
   * `pick()` deals SLOTS, and a slot is one drawn plant. The three abundance
   * fields a record may carry are not three spellings of one number:
   * `stems_per_m2` and `density_per_ha` are COUNTS of plants, `cover_fraction`
   * is the AREA of ground the species holds. The block above normalises all
   * three into one share, which reads "covers 25 % of the ground" as "0.25
   * plants per square metre" — a claim about a two-metre dogwood and a claim
   * about a wild garlic, made identical by a division.
   *
   * `stems` is the same abundance read as a count, and it is derivable only
   * where the record carries what converts an area into one: the plant's own
   * `width_m` — what one drawn plant covers on the ground. Where it does not,
   * this is NULL rather than a guess — the footprint the placer falls back on
   * for walker clearance is a clearance radius, and using it here would put an
   * invented number at the centre of the arithmetic that decides what the sward
   * is made of. AGENTS.md rule 2: the gap is recorded, not filled.
   *
   * K49(c1): every sward record carries a width now, so `stems` is derivable
   * for all 98 of them and `auditAbundance` reports none. It is still not what
   * deals the slots — `weight` is, and moving the lottery onto `stems` is
   * K49(c2), which is a split from this half because the conversion puts a
   * species the census owes 1.10 slots to at the edge of the K49(f) tail gate.
   * The numbers are committed in ROADMAP K49(c1) so the fix cannot redefine
   * its own success.
   */
  const width = Array.isArray(sp.width_m) ? sp.width_m : null;
  let stems = null;
  let stemsHigh = null;
  let unit = 'none';
  if (Array.isArray(ab.stems_per_m2)) {
    unit = 'stems_per_m2';
    stems = mid(ab.stems_per_m2);
    stemsHigh = ab.stems_per_m2[1];
  } else if (Array.isArray(ab.density_per_ha)) {
    unit = 'density_per_ha';
    stems = mid(ab.density_per_ha) / 10000;
    stemsHigh = ab.density_per_ha[1] / 10000;
  } else if (Array.isArray(ab.cover_fraction)) {
    unit = 'cover_fraction';
    if (width) {
      const one = Math.PI * (mid(width) * 0.5) ** 2;
      stems = mid(ab.cover_fraction) / one;
      stemsHigh = ab.cover_fraction[1] / one;
    }
  }
  if (stems !== null && !(stems > 0)) stems = null;
  if (stemsHigh !== null && !(stemsHigh > 0)) stemsHigh = null;

  return {
    id: sp.id ?? sp.binomial ?? 'unnamed',
    form: sp.form,
    role: sp.role,
    substrate: substrateOf(sp, problems, zoneId),
    weight,
    /** The abundance field this species' weight was read out of, and that
     *  same abundance as plants per m² where one is derivable. K49(a). */
    unit,
    stems,
    /**
     * T-0034 — THE SAME ABUNDANCE READ AT THE TOP OF ITS OWN RANGE.
     *
     * Every abundance in `data/flora` is a RANGE, because a prairie's forb load
     * is not one number: the record says 400–900 yellow coneflowers to the
     * hectare and means both ends of that. `stems` takes the midpoint, and the
     * midpoint is not a figure any source states — it is a reading this
     * renderer chose, silently, and it planted every hectare of the town as the
     * average hectare.
     *
     * This is the same abundance read at the recorded upper end. It is a
     * RECONSTRUCTED reading, not a sourced one (docs/LIBERTIES.md L182), and its
     * bound is the record itself: no species can be planted denser than its own
     * record's larger figure, so the sward never leaves the envelope its
     * evidence draws. `stems` is kept beside it because the LOTTERY still runs
     * on the midpoints — which species fills a slot is unchanged, and only how
     * many slots are filled moves.
     */
    stemsHigh,
    height: h,
    width,
    shape: GRASS_SHAPE[sp.form] ?? { arch: 0.28, spread: 0.45 },
    base,
    alt,
    dry: rgb(palette?.dry_accent) ?? [0.55, 0.53, 0.35],
    head: headOf(inflor, sp, problems, zoneId),
    conf: LEVEL[sp.confidence] ?? LEVEL.inferred,
  };
}

/** The published `substrates` vocabulary (data/flora/index.json), and the only
 *  thing in a record that says which side of the waterline a plant may stand on.
 *
 *  `soil` is rooted ground above the water; `saturated_soil` is the emergent
 *  habit — wet ground OR standing water, foliage carried above the surface —
 *  and `open_water` is rooted below the surface with the leaves floating ON it.
 *
 *  Before this field existed the placer read `role`, and a water lily and a
 *  cattail are both `emergent`: the pads were planted on the dry marsh edge
 *  like any other reed, ankle-high mats standing on soil. Their `appearance`
 *  said "floating pads in open water" the whole time, but that is prose. */
const SUBSTRATES = new Set(['soil', 'saturated_soil', 'open_water']);

function substrateOf(sp, problems, zoneId) {
  const declared = sp.substrate;
  if (declared === undefined) {
    // The validator requires the field of every `emergent` record, so a missing
    // one means the renderer is reading data older than its own rules. Report it
    // and fall back to the habit the role implies, which is what this module did
    // before the field existed.
    if (sp.role === 'emergent') {
      problems.push(`flora: ${zoneId}/${sp.id ?? sp.binomial} is emergent and records no `
        + 'substrate — it is planted as if it stood in the shallows, which is a guess '
        + 'about a plant that may float');
      return 'saturated_soil';
    }
    return 'soil';
  }
  if (!SUBSTRATES.has(declared)) {
    problems.push(`flora: ${zoneId}/${sp.id ?? sp.binomial} records substrate '${declared}', `
      + 'which is not in the published vocabulary — it is planted on dry ground');
    return 'soil';
  }
  return declared;
}

/**
 * The flower, off the record's own `july.inflorescence.shape`. A shape the
 * renderer has no archetype for is REPORTED and draws nothing: substituting a
 * different archetype is exactly the failure this dispatch exists to end, and
 * a missing flower that is written down is recoverable in a way that a wrong
 * one silently drawn is not.
 */
function headOf(inflor, sp, problems, zoneId) {
  if (!inflor) return null;
  const style = HEAD_OF_SHAPE[inflor.shape];
  if (!style) {
    problems.push(`flora: ${zoneId}/${sp.id ?? sp.binomial} records inflorescence shape `
      + `'${inflor.shape}', which has no archetype — its flower is not drawn`);
    return null;
  }
  return {
    kind: style.kind,
    count: style.count,
    tilt: style.tilt,
    band: style.band,
    color: rgb(inflor.rgb) ?? [0.8, 0.8, 0.7],
    frac: clamp01(inflor.height_frac ?? 0.9),
    size: Array.isArray(inflor.size_m) ? inflor.size_m : [0.06, 0.12],
  };
}

function meanColor(graminoids, palette) {
  const fallback = rgb(palette?.greens?.[1]) ?? [0.30, 0.38, 0.16];
  if (!graminoids.length) return fallback;
  const out = [0, 0, 0];
  let w = 0;
  for (const g of graminoids) {
    for (let i = 0; i < 3; i++) out[i] += (g.base[i] * 0.6 + g.alt[i] * 0.4) * g.weight;
    w += g.weight;
  }
  return w > 0 ? out.map((v) => v / w) : fallback;
}

function rgb(v) {
  if (!Array.isArray(v) || v.length < 3) return null;
  // sRGB bytes in the record; linear in the shader. three's Color does the
  // transfer, and doing it here means the palette is authored the way a
  // photograph is measured.
  const c = new THREE.Color(v[0] / 255, v[1] / 255, v[2] / 255).convertSRGBToLinear();
  return [c.r, c.g, c.b];
}
function mid(range) { return (range[0] + range[1]) / 2; }

/**
 * T-0280. THE RADIUS OF THE CLUMP ONE PLANT'S RECORD GIVES, in metres, and the
 * module's ONE answer to it. `crowdsTheWalker` has held that answer since the
 * timber critic handed back the three-metre prairie dock at arm's length, and
 * it is the general one: half the recorded `width_m` where a record states a
 * width, and where none does, the footprint the placer gives the plant anyway,
 * off its own recorded height. Fifty of the sward records state no width — every
 * forb of the wet prairie, the mesic prairie and the sand prairie among them —
 * so a rule that only worked on recorded widths would answer for half the town.
 */
function clumpRadiusOf(sp) {
  return sp.width ? mid(sp.width) * 0.5 : Math.min(0.35, mid(sp.height) * 0.16);
}

/**
 * T-0280. THE GROUND ONE SPECIES' RECORDED ABUNDANCE COVERS, as a fraction of
 * ground: `stems × π·clump²`. For a cover-recorded species this hands its own
 * `cover_fraction` straight back, because K49(c1) derived `stems` by dividing by
 * exactly this disc; for a stem- or hectare-recorded one it is the conversion in
 * the direction the record does not state.
 *
 * TWO QUESTIONS, and they want different answers where `width_m` is absent.
 *
 * `drawn: true` asks what ground the plants the renderer PUTS THERE cover, so
 * a missing width falls back to `clumpRadiusOf`'s height rule — the footprint
 * the placer is already giving that plant. This is the one a ratio between two
 * strata must use, because dropping the width-less records would not make a
 * stratum smaller, it would make it ABSENT: all five sand-prairie forbs and both
 * marsh forbs are width-less, and a sum over recorded widths alone calls those
 * two communities flowerless when their records plainly are not.
 *
 * `drawn: false` (the default) asks what the RECORD states, and answers `null`
 * rather than a fallback where it states no width. That is the census's
 * question — K54 put the field there to audit the authored numbers — and a
 * derived footprint would audit the renderer against itself.
 *
 * `high` reads the top of each recorded range, the end T-0034 deals the forb
 * ring off, instead of its midpoint.
 */
function coverOf(sp, { high = false, drawn = false } = {}) {
  const n = high ? (sp.stemsHigh ?? sp.stems) : sp.stems;
  if (n === null || n === undefined) return null;
  if (!drawn && !sp.width) return null;
  return n * Math.PI * clumpRadiusOf(sp) ** 2;
}

/**
 * T-1106. THE SAME STRATUM AS A WALL RATHER THAN AS A FLOOR — silhouette-area
 * density, `stems x w x h`, in m² of upright screen-filling area per m² of
 * ground.
 *
 * WHY A SECOND QUANTITY EXISTS AT ALL. `coverOf` above answers "how much GROUND
 * does this stratum's recorded abundance hold", and that is the honest question
 * for ground: a walker looking down sees footprints. The far band is not that
 * view. Its nearest card stands 34 m out and its furthest 95 m, and at fifty
 * metres a 1.7 m eye looks 1.9 degrees below horizontal — the sward is seen EDGE
 * ON, as a wall, and what fills a pixel is the first element the ray meets. The
 * quantity that governs which plant that is, is projected area per element times
 * elements per unit ground, which is this; the depth of the wall cancels out of
 * a RATIO between two strata standing in it.
 *
 * This is not a new model. `tools/measure_far_bloom.mjs` §1 has priced the BLOOM
 * on exactly this bridge since T-0209, stating the same edge-on argument and the
 * same `n x a`. What T-1106 found is that the far band's grass-or-flower SPLIT
 * was on the other quantity, so the module was answering two neighbouring
 * questions about the same wall in two different units.
 *
 * `w` IS THE DRAWN CLUMP, for the reason T-0280 gives at `coverOf`: fifty sward
 * records state no `width_m`, and a sum over recorded widths alone would not
 * make those strata thin, it would make them ABSENT. `h` is the record's own
 * `height_m` on 1 July, which every sward record states — a plant with no height
 * returns `null` and is counted as unknown rather than silently as nothing.
 *
 * THE SILHOUETTE IS THE CLUMP'S BOUNDING RECTANGLE, `w x h` — not an ellipse, not
 * a measured profile, and NOT the far card's own quad, whose width is the
 * aggregate `band.wide` L137 gives it rather than this plant's. That is a stated
 * liberty, docs/LIBERTIES.md L236: a shape factor would cancel out of the ratio
 * wherever the two strata share a growth form, the project has no measured
 * profile for either to make it not cancel, and applying one to a single side
 * would be a thumb on the scale.
 */
function silhouetteOf(sp, { high = false, drawn = false } = {}) {
  const n = high ? (sp.stemsHigh ?? sp.stems) : sp.stems;
  if (n === null || n === undefined) return null;
  if (!drawn && !sp.width) return null;
  if (!sp.height) return null;
  return n * (2 * clumpRadiusOf(sp)) * mid(sp.height);
}
function clamp01(v) { return Math.min(1, Math.max(0, v)); }

/* -------------------------------------------------------------------------- */
/* where a community is — CONTRACT.md §4                                       */
/* -------------------------------------------------------------------------- */

/** Distance-to-water, two chamfer passes over the committed heightfield.
 *  `buffer` extents ask it for every plant placed. */
async function waterField(terrain, checkpoint) {
  const hf = terrain.heightfield;
  const cell = 4.0;
  const surfaceY = hf?.meta?.water_surface_m ?? 0;
  if (!hf?.loaded) {
    return {
      surfaceY,
      isWater: (e, n) => terrain.isWater(e, n),
      distance: () => Infinity,
    };
  }
  const e0 = hf.originE;
  const n0 = hf.originN;
  const cols = Math.max(2, Math.ceil(hf.widthM / cell) + 1);
  const rows = Math.max(2, Math.ceil(hf.depthM / cell) + 1);
  const BIG = 1e6;
  // Two fields make this a distance to the SHORE, not merely a distance to
  // water. The old one seeded every water cell with zero, so a `0–8 m from
  // water` marsh extent matched the middle of the river just as strongly as
  // the bank. On land we ask for the nearest water cell; in water we ask for
  // the nearest land cell.
  const toWater = new Float32Array(cols * rows).fill(BIG);
  const toLand = new Float32Array(cols * rows).fill(BIG);
  for (let r = 0; r < rows; r++) {
    const pause = checkpoint(); if (pause) await pause;
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      if (terrain.isWater(e0 + c * cell, n0 + r * cell)) toWater[i] = 0;
      else toLand[i] = 0;
    }
  }
  const solve = async (d) => {
    const put = (i, v) => { if (v < d[i]) d[i] = v; };
    for (let r = 0; r < rows; r++) {
      const pause = checkpoint(); if (pause) await pause;
      for (let c = 0; c < cols; c++) {
        const i = r * cols + c;
        if (c > 0) put(i, d[i - 1] + cell);
        if (r > 0) put(i, d[i - cols] + cell);
        if (c > 0 && r > 0) put(i, d[i - cols - 1] + cell * 1.4142);
        if (c < cols - 1 && r > 0) put(i, d[i - cols + 1] + cell * 1.4142);
      }
    }
    for (let r = rows - 1; r >= 0; r--) {
      const pause = checkpoint(); if (pause) await pause;
      for (let c = cols - 1; c >= 0; c--) {
        const i = r * cols + c;
        if (c < cols - 1) put(i, d[i + 1] + cell);
        if (r < rows - 1) put(i, d[i + cols] + cell);
        if (c < cols - 1 && r < rows - 1) put(i, d[i + cols + 1] + cell * 1.4142);
        if (c > 0 && r < rows - 1) put(i, d[i + cols - 1] + cell * 1.4142);
      }
    }
  };
  await solve(toWater);
  await solve(toLand);
  return {
    surfaceY,
    isWater: (e, n) => terrain.isWater(e, n),
    distance(e, n) {
      const c = Math.round((e - e0) / cell);
      const r = Math.round((n - n0) / cell);
      if (c < 0 || r < 0 || c >= cols || r >= rows) return Infinity;
      const i = r * cols + c;
      return terrain.isWater(e, n) ? toLand[i] : toWater[i];
    },
  };
}

/** Highest priority wins; a point that matches nothing gets nothing. */
function zoneFinder(zones, terrain, water) {
  return function find(e, n) {
    for (const z of zones) {
      if (matches(z.extent, e, n, terrain, water)) return z;
    }
    return null;
  };
}

/**
 * `include_polygons` — ground a community holds that its own extent rule cannot
 * reach, and the exact mirror of `exclude_polygons` below.
 *
 * It exists because one community's evidence is a PLACE and its extent is a
 * RULE, and the two stopped agreeing. `docs/research/02-flora.md` heads ZONE 3
 * "SLOUGH & SEDGE MEADOW (Public Square → Tremont House site → river at State
 * St)" — the public square named first, by name — while `z03_sedge_meadow`'s
 * committed extent is an elevation band, which can only find the square if the
 * terrain gives the square a basin, and dossier zone 15 is deferred and
 * unmodelled, so it does not. The band was not selecting against the block; it
 * could not see it. Fitting the band down to reach it would have moved the
 * community everywhere else in the box to solve one address.
 *
 * The box test still binds — a polygon outside a zone's declared box is refused
 * with everything else — and the exclusions still run last, so a hole cut in a
 * community stays a hole. Which ground this admits, and on what evidence, is a
 * claim in the zone record's own extent note, never a rule in here.
 */
function matches(x, e, n, terrain, water) {
  if (!x) return false;
  if (x.box) {
    const be = x.box.e;
    const bn = x.box.n;
    if (be && (e < be[0] || e > be[1])) return false;
    if (bn && (n < bn[0] || n > bn[1])) return false;
  }
  let ok = false;
  switch (x.kind) {
    case 'everywhere':
      ok = true;
      break;
    case 'elevation_band': {
      const y = terrain.surfaceHeight(e, n);
      ok = Array.isArray(x.elev_m) && y >= x.elev_m[0] && y <= x.elev_m[1];
      break;
    }
    case 'polygon':
      ok = Array.isArray(x.polygon) && pointInPolygon(x.polygon, e, n);
      break;
    case 'buffer': {
      if (x.of !== 'water') return false;
      const dist = water.distance(e, n);
      const band = x.distance_m ?? [0, 0];
      ok = dist >= band[0] && dist <= band[1];
      break;
    }
    default:
      return false;
  }
  if (!ok) {
    for (const patch of x.include_polygons ?? []) {
      if (pointInPolygon(patch, e, n)) { ok = true; break; }
    }
  }
  if (!ok) return false;
  for (const hole of x.exclude_polygons ?? []) {
    if (pointInPolygon(hole, e, n)) return false;
  }
  return true;
}

function pointInPolygon(pts, e, n) {
  let inside = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i];
    const [xj, yj] = pts[j];
    if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

/** What fraction of the modelled DRY ground matches no community. Sampled over
 *  the whole heightfield, so it is a property of the dataset and not of where
 *  the visitor happens to stand. */
async function auditCoverage(terrain, finder, checkpoint) {
  const hf = terrain.heightfield;
  if (!hf?.loaded) return 0;
  const step = 8;
  let land = 0;
  let bare = 0;
  for (let n = hf.originN; n <= hf.originN + hf.depthM; n += step) {
    const pause = checkpoint(); if (pause) await pause;
    for (let e = hf.originE; e <= hf.originE + hf.widthM; e += step) {
      if (terrain.isWater(e, n)) continue;
      land++;
      if (!finder(e, n)) bare++;
    }
  }
  return land ? bare / land : 0;
}

/** Buildings as centre + radius + polygon, so most rejections are one test. */
function footprintCircles(footprints) {
  return footprints.map((f) => {
    let e = 0;
    let n = 0;
    for (const p of f.pts) { e += p[0]; n += p[1]; }
    e /= f.pts.length;
    n /= f.pts.length;
    let r2 = 0;
    for (const p of f.pts) r2 = Math.max(r2, (p[0] - e) ** 2 + (p[1] - n) ** 2);
    // A metre of clearance: a wall meeting the sward flush reads as a wall
    // sunk in a lawn.
    const r = Math.sqrt(r2) + 1.0;
    return { e, n, r2: r * r, pts: f.pts };
  });
}

/* -------------------------------------------------------------------------- */
/* the lattice                                                                 */
/* -------------------------------------------------------------------------- */

/** Hermite ramp, 0 below `lo` and 1 at or above `hi`. The shape a recorded
 *  elevation band is read over: see `station`'s woody bound (T-1056), and
 *  docs/LIBERTIES.md L233 for why the shape itself is an admission. */
function smoothstep(lo, hi, x) {
  if (!(hi > lo)) return x >= hi ? 1 : 0;
  const t = Math.min(1, Math.max(0, (x - lo) / (hi - lo)));
  return t * t * (3 - 2 * t);
}

/** Deterministic hash -> a repeatable per-slot random stream, so re-centring
 *  the lattice puts every plant back exactly where it was. */
function hash3(a, b, c) {
  // Math.imul throughout, and it is load-bearing rather than tidy: `a * k` on a
  // full 32-bit seed is a ~2^62 double, the low bits fall off the mantissa, and
  // the four plants in a cell all drew the same "random" number and stacked up
  // on the same blade of grass. The field looked a quarter as dense as it was.
  let h = Math.imul(a, 0x27d4eb2d) ^ Math.imul(b, 0x165667b1) ^ Math.imul(c, 0x9e3779b1);
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
}

/**
 * ROADMAP K49(b) — THE FORB SLOT'S DRAW, AND WHY IT IS NOT `rng()`.
 *
 * A slot's species used to come off the same xorshift stream as its jitter: an
 * independent uniform draw per slot. Independent draws lose their rare end. Six
 * species their own community's recipe owes a whole plant to were drawn NOWHERE
 * across 6,780 slots (K49(a)) — prairie dock, a two-metre landmark, owed 3.23 of
 * them in the wet prairie and standing none. **All six were forb lists**, which
 * is why this is the forb layer's draw and not the sward's.
 *
 * The repair WAS a low-discrepancy assignment (and read T-0265 below before
 * this paragraph is quoted for anything): a rank-1 lattice
 * `frac(c·α + r·β + k·γ)` on the slot's OWN world lattice coordinates, walked
 * against the same CDF `pick()` already walks. It was taken to be
 * equidistributed over any window, so a band of the CDF the width of prairie
 * dock's share gets its count to within one slot instead of to within a Poisson
 * tail — and it is a pure
 * function of the slot, so re-centring the lattice puts the same species back in
 * the same place, which is the promise `hash3` makes and K48's owed-draw picker
 * cannot keep (its running state would change the plant at your feet as you
 * walked up to it).
 *
 * α, β, γ were 1/g, 1/g², 1/g³ for the root of g⁴ = g + 1 — the R3 quasirandom
 * generators, chosen for equidistribution rather than for looking irrational.
 *
 * THE MATRIX LAYERS DO NOT TAKE THIS LATTICE, AND A SCREENSHOT IS WHY. Run
 * on the near and mid tufts as well, this made the west prairie grow in ROWS:
 * the lattice band that decides whether a slot carries a plant is a family of
 * near-diagonal lines, invisible where two slots in a hundred are planted and
 * unmissable where sixty are. The matrix lists lost no species to the tail — the
 * cost was all visible and the benefit all in a column that already read zero.
 * They are stratified a different way instead — see `stratum`, K49(d).
 *
 * T-0265 — AND "EQUIDISTRIBUTED OVER ANY WINDOW" IS NOT TRUE OF A PHONE'S
 * WINDOW. The sentence above is the claim the rank-1 lattice was taken on, and
 * on the mobile stand it fails: `tools/measure_sward_draw.mjs --gate` with
 * `SWARD_VIEWPORT=mobile` was RED on an unmodified `dev`, cocklebur owed 1.49
 * slots in the settled town and drawn nowhere in the scene. The measurement, off
 * the deal itself at the settled-town station: the forb ring reaches 12.4 m at
 * the `light` tune against a rotation block 54 m square, so the WHOLE frame sits
 * inside ONE Cranley–Patterson block and the 46 slots it deals are one
 * contiguous window of one rotation. Their `u` sorted leaves a gap of 0.0399
 * between 0.8247 and 0.8646, and cocklebur's band — 0.0324 wide, seventh of
 * seven in that list's CDF — lies wholly inside it. The species is not rare in
 * that frame; it is absent from it, and the desktop stand passed only because
 * its ring deals 7,153 slots instead of 2,763.
 *
 * FOUR REPAIRS WERE MEASURED AND THREE ARE REFUTED, so they are not tried again:
 *
 * - the sub-cell term made exact (`k/perCell` in place of `k·γ`, which fixes the
 *   pairing 2γ ≡ 0.099 leaves in a cell's four slots) — mobile still RED, the
 *   hole merely moved to two mesic-prairie forbs, and the forb deviation rose
 *   from 16.23 to 19.53 per 100 slots. A re-roll, not a repair;
 * - the forb and shrub passes moved onto `stratum` (K49(d)) — mobile still RED
 *   and the forb deviation 28.70 per 100, which is `stratum`'s own stated
 *   weakness read back at us: exactness over the block is not equidistribution
 *   over the sub-window, and the census reads zone ∩ ring, which is one;
 * - the rotation block cut to four cells so a phone's ring holds several of
 *   them, with the phases swept rather than hashed — mobile still RED, the hole
 *   at a wet-prairie forb instead;
 * - **the construction below — mobile GREEN, and the desktop stays green.**
 *
 * WHAT REPLACED THE LATTICE: the same hierarchical stratification K49(c2) built
 * for the dense layers, applied at the CELL rather than at the block.
 *
 *   u = frac(k / perCell + blockPhase(c, r, perCell, globalShift))
 *
 * Two properties, and the window needs both. Inside one cell the `perCell` slots
 * take values exactly `1/perCell` apart, so every cell that is dealt whole
 * offers all four quarters of the CDF. Across cells the offset is
 * `blockPhase`'s van der Corput sweep of that same step, indexed by the CELL's
 * Morton code, so the four cells of any aligned 2×2 group hold offsets exactly a
 * quarter of the step apart and sixteen of a 4×4 group a sixteenth. A window of
 * C contiguous cells therefore deals `C · perCell` values spread over [0, 1) at
 * about `1 / (C · perCell)`, BY CONSTRUCTION rather than by luck — 1/48 at the
 * settled-town stand against cocklebur's 0.0324 — where the rank-1 lattice gave
 * the same window gaps of two and a half times its mean spacing.
 *
 * It keeps everything K49(b) was taken for. It is still a pure function of the
 * slot's world coordinates, so re-centring puts the same species back in the
 * same place; `globalShift` is still one random start per layer, so it is still
 * unbiased; and it is still the SPARSE layers' draw only — the matrix lists
 * stay on `stratum`, for the screenshot reason above.
 *
 * WHAT IT COST, stated rather than left to be found: the forb body deviates
 * slightly more from its own recorded shares — 16.23 → 17.46 per 100 slots at
 * the phone, 8.44 → 9.47 at the desktop — while the shrub body deviates
 * markedly less (34.52 → 26.52 and 10.41 → 7.69). That is the trade this makes:
 * a per-cent of the shortfall column for the tail column, which is the one the
 * gate is on and the one a visitor can see, because a species standing nowhere
 * is a species the town does not have.
 */
/**
 * The block rotation, kept for `stratum` and no longer read by the sparse draw.
 *
 * It was the Cranley–Patterson offset that kept the rank-1 lattice from
 * repeating one diagonal across the field, sixteen cells square because at four
 * (64 slots) the rotation was all that survived — an independent draw in a
 * costume. T-0265 replaced the lattice, so nothing reads `shift` on that path
 * any more; the two constants stay because `scatter`'s block arithmetic is one
 * expression for both draws and `tools/measure_rank_bias.mjs` mirrors those
 * lines verbatim as its drift guard. Removing the dead branch is T-0371's, not
 * this ticket's — it is a change to the tool's contract, not to the deal.
 */
const LD_BLOCK_SHIFT = 4;
const LD_BLOCK_SALT = 0x2b1f3d7d;

function frac(x) { return x - Math.floor(x); }

/**
 * ROADMAP K49(d) — THE DENSE LAYER'S STRATIFICATION, AND WHY IT IS NOT A LATTICE.
 *
 * K49(b) left the near and mid tufts on an independent `rng()` because the
 * rank-1 lattice above ROWS the prairie. That was a veto on the construction,
 * not on the goal: the matrix lists' worst shortfall was **31.47 slots** — the
 * mesic prairie deals 793 slots between four grasses and one of them came up
 * thirty-one short of the cover its own record states — and nothing had reduced
 * it.
 *
 * The striping is not the rare end of the CDF, it is the common one. At
 * `matrixShare ≈ 0.6` the test `u < share` selects most of a lattice, so the
 * SELECTED SET inherits the lattice's structure and the field inherits it in
 * turn. Any construction whose slot-to-`u` map has a direction in it will do
 * this at that density. So the requirement is a stratification with no direction
 * to read.
 *
 * A keyed pseudorandom BIJECTION over the block's slots is that. Every slot in a
 * 16×16-cell block is dealt a distinct rank in `[0, n)`, so `u` takes each of the
 * n equally spaced values exactly once: a CDF band of width w gets its exact
 * count `round(w·n)` inside the block, not a Poisson draw around it. And because
 * the map from slot to rank is a hashed permutation rather than an arithmetic
 * progression, the ranks carry no gradient across the grid — the selected set is
 * spatially indistinguishable from the independent draw it replaces, which is
 * exactly what the screenshot in K49(b) demanded and the lattice could not give.
 *
 * A four-round Feistel network is the standard form and is used here: it is a
 * bijection by construction (each round is invertible whatever the round
 * function does), it needs no table, and it is a pure function of the slot's
 * world coordinates, so re-centring the lattice puts the same plant back — the
 * same promise `hash3` makes and K48's account-keeping picker cannot.
 *
 * ITS WEAKNESS, STATED RATHER THAN DISCOVERED: exactness over the BLOCK is not
 * equidistribution over a sub-window, and the census reads zone ∩ ring, which is
 * one. It bounds the error to what the block boundaries cut, instead of removing
 * it. The matrix tail is already empty (K49(a) found no absent matrix species),
 * so the tail is not what this is for — the shortfall is.
 *
 * THAT LAST SENTENCE WAS WRONG WITHIN THE DAY, AND K49(f) IS WHY. The tail was
 * empty when it was written and this construction emptied it the other way: a
 * fixed grid of `u` puts every band narrower than one step out of the scene
 * ALTOGETHER, and two of the dataset's forty-five matrix bands are. Read
 * `stratum`'s own doc block below before changing anything here — the repair is
 * the block's phase, and it also recovers most of the regression the paragraph
 * below blames on a filter.
 *
 * ...and it was thought to have a SECOND face that cost two rows of the census.
 * IT DOES NOT, AND THE PARAGRAPH THAT SAID SO IS STRUCK. What it said was: rank
 * is a deterministic function of position inside the block, so a filter running
 * AFTER the deal on a spatial rule of its own — `station()` refusing a building
 * footprint or the far side of a waterline — selects a BIASED set of ranks; and
 * therefore, do not reach for `stratum` in a heavily filtered layer. K49(f)
 * refuted the settled-town half the same day, by fixing the fixed grid instead.
 * **T-0018 / K49(e) refutes the mechanism itself** —
 * `tools/measure_rank_bias.mjs`, which runs the deal out of THIS file:
 *
 *   position → rank is `feistel(idx, half, blockHash)`, and `blockHash` is
 *   `hash3(bc, br, salt ^ STRAT_SALT)` — RE-KEYED IN EVERY BLOCK. A spatial rule
 *   does not know that key, so the ranks it accepts are an arbitrary subset,
 *   independently re-drawn block by block. Pooled, they are uniform.
 *
 * Measured over 400 independent layer keys, chi-square on 15 df against uniform:
 * a waterline half-plane **2.0**, a footprint disc **4.1**, a street stripe
 * **2.3** — against a rank-blind control at **4.7** and a critical value of 37.7
 * at p = 0.001. A filter deliberately written to read the rank scores
 * **100,800**, so the instrument goes red by four orders of magnitude when there
 * is something to catch.
 *
 * SO THE RULE IS THE OPPOSITE OF THE ONE THAT WAS WRITTEN HERE. Reach for
 * `stratum` in a filtered layer: filtered, it still beats an independent draw
 * (mix deviation per 100 planted slots — unfiltered **0.83**, thinned to ~60 %
 * **3.2–5.0**, independent **5.83**). What a filter costs is the STRATIFICATION,
 * not the accuracy: the surviving `u` are no longer equally spaced, so the deal
 * slides back towards Poisson at about the rate it thins. Expect precision to
 * degrade with filtering; do not expect a lean.
 */
const STRAT_SALT = 0x7f4a7c15;
/**
 * ...and the block is FOUR cells square, not the lattice's sixteen, because
 * K49(b) finding 3's rule — *the block size is set by PLANTED slots, not by
 * cells* — points the other way for a dense layer. The forb layer plants a few
 * per cent of what it deals and needed 1,024 slots to resolve a species band;
 * the matrix layer plants `matrixShare ≈ 0.6` of them, thirty times the rate, so
 * 64 slots already carry ~38 plants — more than the forb layer's 16×16 block
 * ever did.
 *
 * And the small block is not merely sufficient, it is BETTER, for the reason the
 * parcel's own weakness names: exactness holds over the block and the census
 * reads a sub-window, so the error is whatever the window's partial blocks cut.
 * A near ring is 15.2 m across and a 16-cell block is 11.8 m — the window
 * contained about ONE whole block, so almost every slot read was in a partial
 * one. At four cells it is 3.0 m and the same window holds ~20.
 *
 * So the rule has a FLOOR and a CEILING, and only the floor was written down.
 * Measured, all five, on the matrix `deviation` of `tools/measure_sward_draw.mjs`
 * — never on `worstShortfall`, which is a max of a max and ranks these in a
 * different order:
 *
 * | block | m (near) | slots | matrix deviation |
 * |---|---|---|---|
 * | independent draw | — | — | 368.80 |
 * | 1 cell | 0.74 | 4 | 2,725.88 |
 * | 2 cells | 1.48 | 16 | 602.95 |
 * | **4 cells** | **2.96** | **64** | **282.89** |
 * | 8 cells | 5.92 | 256 | 303.30 |
 * | 16 cells | 11.84 | 1,024 | 340.47 |
 *
 * The floor is not a soft one: at four slots per block `u ∈ {0.125, 0.375,
 * 0.625, 0.875}`, so at `share ≈ 0.6` exactly two are planted and `u / share`
 * takes TWO values — the CDF collapses onto two species and the deviation is
 * seven times the fault being repaired.
 */
const STRAT_BLOCK_SHIFT = 2;

/** One round-keyed Feistel pass over `2·half` bits. Invertible by construction,
 *  so the map is a permutation of `[0, 2^(2·half))` whatever `hash3` returns. */
function feistel(x, half, key) {
  const mask = (1 << half) - 1;
  let l = (x >>> half) & mask;
  let r = x & mask;
  for (let i = 0; i < 4; i++) {
    const t = l ^ (hash3(r, key, i + 1) & mask);
    l = r;
    r = t;
  }
  return ((l << half) | r) >>> 0;
}

/**
 * The slot's rank inside its block, as a `u` in `[0, 1)`.
 *
 * `half` is chosen so the Feistel's domain `2^(2·half)` covers `n`; when it
 * overshoots (it does not at `perCell = 4`, where a 16×16 block holds exactly
 * 1,024 slots and the domain is 1,024) the standard cycle-walk re-applies the
 * permutation until the image lands back in range, which is still a bijection on
 * `[0, n)`. The guard is a belt on a loop that provably terminates; falling back
 * to the identity keeps `u` in range rather than returning a rank that is not a
 * rank.
 *
 * ROADMAP K49(f) — AND THE GRID IT LANDS ON HAS TO MOVE, or the tail of the CDF
 * is not thin, it is EMPTY.
 *
 * The permutation decides which slot gets which rank. It does not change the SET
 * of `u` the block deals, which without `phase` is `{(k + 0.5) / n}` — the same n
 * numbers in every block of the world, for ever. A species owns a CDF band of
 * width `share × weight`, so a band narrower than `1/n` can contain none of them,
 * and then it contains none of them EVERYWHERE: the species is not rare in the
 * scene, it is absent from it, deterministically, at every station. That is the
 * exact fault K49(b) repaired in the forb lists — and it came back in the matrix
 * lists the moment K49(d) handed them a fixed grid. (The forb layer never had it:
 * its lattice `u` already carries the block's `shift`.)
 *
 * `phase` is the block's own offset, wrapped — a systematic sample with a random
 * start, which is the textbook form for exactly this reason. The n values stay
 * equally spaced, so the block is still an exact stratification and K49(d)'s
 * deviation result is untouched in construction; what changes is that a band of
 * width w now falls on a dealt value in about `w · n` of the blocks instead of in
 * all of them or none, which is the unbiased answer. A species owed a plant per
 * hundred square metres gets one per hundred square metres.
 */
function stratum(idx, n, half, key, phase) {
  let x = idx;
  for (let guard = 0; guard < 24; guard++) {
    x = feistel(x, half, key);
    if (x < n) return frac((x + 0.5) / n + phase);
  }
  return frac((idx + 0.5) / n + phase);
}

/**
 * ROADMAP K49(c2) — AND THE PHASE HAS TO SWEEP THE STEP, or a species owed ONE
 * plant in the frame gets it on a coin toss.
 *
 * K49(f) gave every block its own RANDOM phase, which is unbiased and is what
 * fixed the species drawn nowhere in the WORLD: a band of width `w` lands on a
 * dealt value in about `w · n` of the blocks instead of in all of them or none.
 * What it does not fix is the frame. A band with `w · n = 0.077` — the sedge
 * meadow's two bulrushes, measured — is a coin toss per block, and over the
 * fourteen blocks a station's ring holds it comes up empty about a third of the
 * time. The species is owed 1.10 slots and draws none, at random, which is the
 * one thing K49(f)'s gate is absolute about.
 *
 * So the phases are STRATIFIED ACROSS BLOCKS as well as within one. The block's
 * phase is `globalShift + vdc(morton(block)) / n`: a van der Corput sweep of the
 * step `[0, 1/n)`, indexed by the block's Morton code, on a random global start.
 * Three properties, and the parcel needs all three:
 *
 * - **The set inside a block is untouched** — the n values are still equally
 *   spaced by `1/n`, so it is still an exact stratification and K49(d)'s
 *   deviation result stands by construction.
 * - **Adjacent blocks get maximally separated phases.** Reversing the bits of
 *   the Morton code sends the block coordinates' LOW bits to the top of the
 *   fraction, so the four blocks of any aligned 2×2 group hold phases exactly
 *   `1/4` of the step apart, sixteen of a 4×4 group `1/16` apart. A band wider
 *   than the sweep's spacing is then hit BY CONSTRUCTION rather than by luck.
 * - **It stays unbiased.** `globalShift` is one random start for the layer, so
 *   a band of width `w` still lands in `w · n` of the blocks on average; what
 *   changes is the variance, which is the whole complaint.
 *
 * T-0265 — AND IT IS NOW BOTH DRAWS' SWEEP, at two scales. `stratum` calls it
 * per BLOCK with `n` the block's slot count; the sparse draw calls it per CELL
 * with `n = perCell`, because the frame that failed was smaller than a block.
 * The argument is the same one either way and the code is the same line.
 */
function blockPhase(c, r, n, globalShift) {
  return frac(globalShift + vdc(morton(c, r)) / n);
}

/** Interleave two block coordinates into one Morton code. Biased into the
 *  unsigned range first, so a block west or south of the origin indexes the
 *  same way as one east or north of it. */
function morton(c, r) {
  return ((spread16(r + 0x8000) << 1) | spread16(c + 0x8000)) >>> 0;
}

/** One 16-bit value spread into the even bits of a 32-bit word. */
function spread16(n) {
  let x = n & 0xffff;
  x = (x | (x << 8)) & 0x00ff00ff;
  x = (x | (x << 4)) & 0x0f0f0f0f;
  x = (x | (x << 2)) & 0x33333333;
  x = (x | (x << 1)) & 0x55555555;
  return x >>> 0;
}

/** The van der Corput sequence in base 2: the index with its bits reversed,
 *  read as a fraction. Consecutive indices are far apart by construction, which
 *  is the property `blockPhase` is built on. */
function vdc(i) {
  let x = i >>> 0;
  x = ((x & 0x55555555) << 1) | ((x >>> 1) & 0x55555555);
  x = ((x & 0x33333333) << 2) | ((x >>> 2) & 0x33333333);
  x = ((x & 0x0f0f0f0f) << 4) | ((x >>> 4) & 0x0f0f0f0f);
  x = ((x & 0x00ff00ff) << 8) | ((x >>> 8) & 0x00ff00ff);
  return (((x >>> 16) | (x << 16)) >>> 0) / 4294967296;
}

/** The half-width the Feistel needs to cover `n` slots. */
function stratumHalf(n) {
  let bits = 1;
  while ((1 << bits) < n) bits++;
  return (bits + 1) >> 1;
}

function rngFrom(seed) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >>> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

/** Walk the lattice cells around the camera, calling `emit` per jittered slot
 *  inside the ring. The grid is world-anchored, not camera-anchored.
 *
 *  `draw` picks how the slot's `u` — the one number that decides both whether it
 *  carries a plant and which species (see `dealt`) — is constructed. `'lattice'`
 *  is the SPARSE draw the forb, shrub and far passes take: the rank-1 sequence
 *  of K49(b) until T-0265 measured it empty-handed in a phone's window, and the
 *  cell-resolution stratification of K49(c2) since. `'strata'` is the block
 *  permutation of K49(d), which the DENSE matrix layers take because a lattice
 *  stripes them. Both are pure functions of the slot's world coordinates. */
function* scatter(camE, camN, cell, perCell, radius, inner, salt, draw, cone, emit) {
  const c0 = Math.floor((camE - radius) / cell);
  const c1 = Math.ceil((camE + radius) / cell);
  const r0 = Math.floor((camN - radius) / cell);
  const r1 = Math.ceil((camN + radius) / cell);
  const sub = Math.max(1, Math.round(Math.sqrt(perCell)));
  const rr = radius * radius;
  const ri = inner * inner;
  // ROADMAP K49(d). The block is the stratum: every slot in it is dealt a
  // distinct rank, so a CDF band gets its exact count rather than a Poisson one.
  const strata = draw === 'strata';
  const shiftBits = strata ? STRAT_BLOCK_SHIFT : LD_BLOCK_SHIFT;
  const span = 1 << shiftBits;
  const nSlots = span * span * perCell;
  const half = stratumHalf(nSlots);
  // ROADMAP K49(c2). ONE random start for the whole layer, not one per block:
  // the sweep is what separates neighbouring blocks, and a per-block random
  // start would put it back where K49(f) left it.
  const globalShift = hash3(salt, STRAT_SALT, 0x9e3779b9) / 4294967296;
  yield { done: 0, total: r1 - r0 + 1 };
  for (let r = r0; r <= r1; r++) {
    for (let c = c0; c <= c1; c++) {
      const cellSeed = hash3(c, r, salt);
      // ROADMAP K49(b). One rotation per 16×16-cell block of the WORLD lattice —
      // and, K49(d), one permutation key per the same block.
      const bc = c >> shiftBits;
      const br = r >> shiftBits;
      const blockHash = hash3(bc, br, salt ^ (strata ? STRAT_SALT : LD_BLOCK_SALT));
      // ROADMAP K49(c2). The lattice takes a Cranley–Patterson rotation, which
      // wants an independent offset per block; the stratification takes a phase
      // that SWEEPS its own step across neighbouring blocks, because a random
      // one leaves a narrow band to a coin toss in the frame. See `blockPhase`.
      const shift = strata
        ? blockPhase(bc, br, nSlots, globalShift)
        : blockHash / 4294967296;
      // The slot's index inside its own block. Arithmetic shift, so a block west
      // or south of the origin indexes the same way as one east or north of it.
      const base = ((c - ((c >> shiftBits) << shiftBits)) * span
        + (r - ((r >> shiftBits) << shiftBits))) * perCell;
      const cellPhase = strata ? 0 : blockPhase(c, r, perCell, globalShift);
      for (let k = 0; k < perCell; k++) {
        const rng = rngFrom(hash3(cellSeed, k, 0x68bc21eb));
        // ROADMAP K49(b). The slot's own place in the deal: it decides BOTH
        // whether this slot carries a plant at all and which species it is, so
        // that the thinning cannot resample the species draw back into an
        // independent one. See `dealt`.
        // ROADMAP K49(f). The stratification wraps its grid of ranks by the
        // block's own `shift`; without it the strata deal the same n values of
        // `u` in every block of the world and a CDF band narrower than `1/n` is
        // drawn nowhere at all. T-0265: the sparse draw takes the same medicine
        // one scale down — `cellPhase` above, swept per CELL — because at a
        // phone the whole ring fits inside one block and one rotation, so a
        // block offset is a coin tossed once for the frame.
        const u = strata
          ? stratum(base + k, nSlots, half, blockHash, shift)
          : frac(k / perCell + cellPhase);
        // A jittered sub-grid, not free scatter: free scatter leaves holes
        // the eye reads as bare soil and clusters it reads as one plant.
        const sx = k % sub;
        const sy = (k / sub) | 0;
        const e = (c + (sx + rng()) / sub) * cell;
        const n = (r + (sy + rng()) / sub) * cell;
        const d2 = (e - camE) ** 2 + (n - camN) ** 2;
        if (d2 > rr || d2 < ri) continue;
        const d = Math.sqrt(d2);
        // Outside the view cone there is nothing to see and everything to pay
        // for: three has no per-instance culling, so a plant behind the walker
        // still runs its vertex shader. The cone is far wider than the frame
        // (62 degrees against 38) so a turn of a dozen degrees is planted
        // before the lattice catches up; inside CONE_KEEP_M everything is kept,
        // because that ring must not flicker as you turn on the spot.
        if (cone && d > CONE_KEEP_M
          && ((e - camE) * cone.fe + (n - camN) * cone.fn) / d < cone.cos) continue;
        emit(e, n, d, rng, cellSeed, u);
      }
    }
    yield { done: r - r0 + 1, total: r1 - r0 + 1 };
  }
}

/** Weighted pick from a compiled species list (weights sum to 1). */
/**
 * One species out of a `{items, total}` subset, at its recorded weight. The
 * weights are normalised over the WHOLE community, so a subset sums to its own
 * share of it and `u` is scaled by that total — which is what renormalising over
 * the subset amounts to, without copying every entry to rewrite one number.
 */
function pick(subset, u) {
  const list = subset.items;
  if (!list.length) return null;
  let acc = 0;
  const target = u * subset.total;
  for (const item of list) {
    acc += item.weight;
    if (target <= acc) return item;
  }
  return list[list.length - 1];
}

/**
 * ROADMAP K49(b) — the slot's whole deal, out of ONE low-discrepancy draw.
 *
 * A lattice slot is asked two questions in a row: does the community's recorded
 * cover put a plant here at all (`share`), and if so which species (`pick`). Ask
 * them of two independent numbers and the second one's equidistribution is
 * spent: the surviving slots are a random subsample of the lattice, and a random
 * subsample of a low-discrepancy set is back to Poisson in its tail — which is
 * the fault K49(a) measured.
 *
 * So the two questions share one draw. `u` below the share carries the plant,
 * and its position INSIDE `[0, share)` is what walks the CDF: species i then
 * owns a band of width `share × weight_i`, and the lattice hits every band at
 * its own rate. That is the whole repair — the same marginal probabilities, in
 * one stratified draw instead of two independent ones.
 *
 * Returns null when the slot carries nothing.
 */
function dealt(subset, share, u) {
  if (!(share > 0) || u >= share) return null;
  return pick(subset, u / share);
}

/* -------------------------------------------------------------------------- */
/* placing one plant                                                           */
/* -------------------------------------------------------------------------- */

const _m = new THREE.Matrix4();
const _e = new THREE.Euler();
const _c = new THREE.Color();

/**
 * A plant may not be standing where the walker is standing.
 *
 * The near ring is camera-relative and had no inner radius, so a three-metre
 * prairie dock could be planted at arm's length and fill the frame — which is
 * what the timber critic handed back as "the giant yellow-flowered plant at
 * absurd scale in the immediate foreground". The clearance is not a fudge
 * factor: it is the walker's own shoulder half-width (walker.js WALK.radius,
 * 0.34 m) plus the radius of the clump the record itself gives, because a
 * plant whose crown overlaps the body of the person looking at it is a plant
 * that person has walked through.
 */
const WALKER_RADIUS_M = 0.34;
function crowdsTheWalker(sp, r) {
  const clump = clumpRadiusOf(sp);
  return r < WALKER_RADIUS_M + clump;
}

function instSet(name, geometry, material, max) {
  const mesh = new THREE.InstancedMesh(geometry, material, max);
  mesh.name = name;
  mesh.castShadow = false;
  mesh.receiveShadow = false;
  // Always around the viewer; culling can only throw it away by mistake.
  mesh.frustumCulled = false;
  // Drawn BEFORE the ground on purpose: the ground is a full-screen standard
  // material with a shadow lookup and is the most expensive thing in the frame,
  // so every sward fragment that lands first is one the depth test never
  // shades. Measured: at eye height in open prairie it pays for the sward.
  mesh.renderOrder = -3;
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  mesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(max * 3), 3);
  mesh.instanceColor.setUsage(THREE.DynamicDrawUsage);
  const params = new THREE.InstancedBufferAttribute(new Float32Array(max * 4), 4);
  params.setUsage(THREE.DynamicDrawUsage);
  geometry.setAttribute('aFlora', params);
  // docs/PROVENANCE.md: per-PLANT here, because the evidence behind a species
  // belongs to the species, not to the archetype it is drawn with. An instanced
  // attribute reaches the same shader declaration a per-vertex one would.
  const conf = new THREE.InstancedBufferAttribute(new Float32Array(max), 1);
  conf.setUsage(THREE.DynamicDrawUsage);
  geometry.setAttribute('_confidence', conf);
  // The ring this instance is faded over, and how far its origin stands above
  // the base of its own plant — zero for anything rooted, the stalk height for
  // a flower head, which is what lets the shader lower a head to the ground as
  // its plant shrinks instead of leaving it hanging where the CPU put it.
  const ringAttr = new THREE.InstancedBufferAttribute(new Float32Array(max * 4), 4);
  ringAttr.setUsage(THREE.DynamicDrawUsage);
  geometry.setAttribute('aChiRing', ringAttr);
  const riseAttr = new THREE.InstancedBufferAttribute(new Float32Array(max), 1);
  riseAttr.setUsage(THREE.DynamicDrawUsage);
  geometry.setAttribute('aChiRise', riseAttr);
  /** Never fades: overwritten before the first push of every pass. */
  let ringNow = [1e9, 1e-4, 0, 0];

  const tris = (geometry.index ? geometry.index.count : geometry.attributes.position.count) / 3;
  let n = 0;
  /**
   * T-0214. How many instances this set was ASKED for over the pass, against
   * the `n` it drew. A set at its cap refuses silently — `push` returns false
   * and the caller stops — so before this counter the difference between a set
   * that had nothing to draw and one that was cut off mid-plant was invisible
   * from outside the module, and the only way to see it was to notice that
   * `mesh.count` happened to equal `max`. That reads as a coincidence, and at
   * two of the nine head sets it was not one.
   *
   * It counts DEMAND, not refusals: every push attempt, plus whatever the
   * caller abandons on a refusal and tells us about through `skip`. So
   * `want - n` is the shortfall in instances, by name, and an allocation can
   * be sized against it instead of against a guess.
   */
  let want = 0;
  return {
    mesh,
    tris,
    max,
    /** Instances asked for since the last `reset` — see `want`. */
    demand() { return want; },
    /** Instances the caller gave up on after a refusal, so the demand figure
     *  is the whole of what the records asked for and not the part that was
     *  attempted before the set filled. */
    skip(k) { want += k; },
    reset() { n = 0; want = 0; },
    /** The ring every following push is drawn on, `[outer, band, inner,
     *  innerBand]`. A head set is pushed to from two different rings in one
     *  rebuild, so this is per-push state rather than per-set. */
    ring(r) { ringNow = r; },
    /**
     * @param {number} [tilt] radians off vertical, baked into the INSTANCE
     *   matrix rather than the vertex program: a flower head is held at an
     *   angle and the tilt has to vary per instance, while the yaw slot in
     *   `aFlora` can only turn it about the vertical. Pass `yaw` 0 alongside a
     *   tilt — the matrix carries the whole rotation.
     * @param {number} [tiltAz] which way it leans.
     * @param {number} [rise] metres this instance's origin stands above the
     *   base of its plant. The shader lowers it by `rise * (1 - fade)`.
     * @returns {boolean} false when the cap is reached — the caller stops.
     */
    push(e, y, n2, yaw, height, spread, arch, r, g, b, conf2, tilt = 0, tiltAz = 0, rise = 0) {
      want++;
      if (n >= max) return false;
      if (tilt !== 0) {
        // The yaw is NOT passed to the Euler, and that is R-BUG7. It is the
        // head's spin about its own stalk and the vertex program already
        // applies it, off `aFlora.w`, before this matrix runs. Turning the
        // whole tilted head by it a second time here spins `tiltAz` — the
        // bearing the caller computed so the stalk would lean BACK to its own
        // stem — to a uniformly random one. Four repairs in this file computed
        // that bearing correctly and not one of them reached the geometry:
        // measured on the published mirror, 38 drawn heads over 32 poses had
        // their stalk foot in open air, the worst 58 cm from any stem.
        _e.set(Math.cos(tiltAz) * tilt, 0, Math.sin(tiltAz) * tilt, 'YXZ');
        _m.makeRotationFromEuler(_e);
        _m.setPosition(e, y, -n2);
      } else {
        _m.makeTranslation(e, y, -n2);
      }
      mesh.setMatrixAt(n, _m);
      mesh.instanceColor.setXYZ(n, r, g, b);
      params.setXYZW(n, height, spread, arch, yaw);
      conf.setX(n, conf2);
      ringAttr.setXYZW(n, ringNow[0], ringNow[1], ringNow[2], ringNow[3]);
      riseAttr.setX(n, rise);
      n++;
      return true;
    },
    commit() {
      mesh.count = n;
      mesh.instanceMatrix.needsUpdate = true;
      mesh.instanceColor.needsUpdate = true;
      params.needsUpdate = true;
      conf.needsUpdate = true;
      ringAttr.needsUpdate = true;
      riseAttr.needsUpdate = true;
    },
  };
}

/** Uneven light is most of what separates the July photographs from the
 *  October one (luminance spanning 150-210 levels against 90). A per-plant
 *  patch factor from a smooth world-space field buys that mottling for one
 *  noise lookup — and it is patchiness in the vegetation, not a light. */
function patchOf(e, n) {
  return 0.66 + 0.72 * vnoise(e * 0.21 + 5.5, n * 0.21 - 2.3)
    * (0.72 + 0.42 * vnoise(e * 0.74 - 1.1, n * 0.74 + 6.2));
}

function tint(sp, u, v) {
  // Two greens per species, plus a small tonal jitter: the bar photographs show
  // several distinct greens within a metre, and one flat green reads as carpet.
  const t = u * u;
  const k = 0.82 + v * 0.40;
  return [
    (sp.base[0] * (1 - t) + sp.alt[0] * t) * k,
    (sp.base[1] * (1 - t) + sp.alt[1] * t) * k,
    (sp.base[2] * (1 - t) + sp.alt[2] * t) * k,
  ];
}

function placeGraminoid(set, sp, e, y, n, rng) {
  const u = rng();
  // The record's own height, at full size. The ring fade that used to be baked
  // in here is applied per frame in the vertex shader instead: baked, it could
  // only change when the lattice was rebuilt, which made it a step rather than
  // a ramp and put the plant's whole growth into one frame.
  const h = sp.height[0] + (sp.height[1] - sp.height[0]) * u;
  // width_m is the clump diameter the record gives; only fall back to a
  // proportion of the height when it does not. The proportion had cordgrass
  // splaying 1.1 m against a recorded 0.5-0.9.
  const spread = (sp.width ? mid(sp.width) : h * sp.shape.spread) * (0.78 + rng() * 0.5);
  const c = tint(sp, rng(), rng()).map((x) => x * patchOf(e, n));
  // A minority of dead thatch from last year's growth, at the base of the
  // clump. Kept a minority on purpose: a straw-coloured sward is October.
  const dry = rng() < 0.07;
  const col = dry
    ? [c[0] * 0.6 + sp.dry[0] * 0.5, c[1] * 0.6 + sp.dry[1] * 0.45, c[2] * 0.6 + sp.dry[2] * 0.5]
    : c;
  // The height is returned, and it is the height the HEAD must be hung off:
  // a zero says the cap was reached and nothing was drawn here, so nothing may
  // be hung off it either.
  return set.push(e, y, n, rng() * Math.PI * 2, h, spread,
    sp.shape.arch * (0.7 + rng() * 0.7), col[0], col[1], col[2], sp.conf) ? h : 0;
}

function placeCard(set, sp, zone, e, y, n, rng) {
  const u = rng();
  const h = (sp.height[0] + (sp.height[1] - sp.height[0]) * u) * 0.92;
  // A clump, not a hoarding. Width 1.25-2.15 x height made 2.5 m billboards
  // that tiled the mid-ground into flat-topped dark blocks.
  const w = h * (0.42 + rng() * 0.44);
  const c = tint(sp, rng(), rng()).map((x) => x * patchOf(e, n));
  // Mid-distance clumps carry a little of the zone's own mean, so the sea reads
  // as one community rather than as a spray of unrelated colours.
  const m = zone.matColor;
  set.push(e, y, n, 0, h, w, 0.5 + rng(),
    c[0] * 0.72 + m[0] * 0.28,
    c[1] * 0.72 + m[1] * 0.28,
    c[2] * 0.72 + m[2] * 0.28, sp.conf);
}

/**
 * A far card: the same clump archetype the mid ring draws, standing for the
 * several metres of sward the band no longer draws plant by plant. T-0086.
 *
 * Two things separate it from `placeCard`. Its height is drawn from the UPPER
 * half of the species' recorded range and lifted a little, because what an
 * aggregate shows against the sky is the tallest plants in the patch and not
 * the mean of them (LIBERTIES L137). And it carries much more of the
 * community's own mean colour — aerial perspective is not modelled below the
 * fog's reach, and a spray of unrelated hues at sixty metres reads as noise
 * where a patch of one green reads as a meadow.
 */
function placeFarCard(set, sp, zone, e, y, n, rng, band) {
  const u = 0.45 + 0.55 * rng();
  const plantH = sp.height[0] + (sp.height[1] - sp.height[0]) * u;
  const h = plantH * band.lift;
  const w = band.wide[0] + (band.wide[1] - band.wide[0]) * rng();
  const c = tint(sp, rng(), rng()).map((x) => x * patchOf(e, n));
  const m = zone.matColor;
  // The PLANT's height is returned, not the card's. `band.lift` widens and
  // lifts an aggregate so it reads as several metres of matrix rather than one
  // clump (L137); a flower hung off that lift would stand a hand's breadth over
  // the plant that is supposed to be carrying it. Zero says the set was capped
  // and nothing was drawn here, so nothing may be hung off it either — the same
  // contract `placeGraminoid` and `placeForb` keep with `maybeHead`.
  return set.push(e, y, n, 0, h, w, 0.5 + rng(),
    c[0] * 0.38 + m[0] * 0.62,
    c[1] * 0.38 + m[1] * 0.62,
    c[2] * 0.38 + m[2] * 0.62, sp.conf) ? plantH : 0;
}

function placeForb(set, sp, e, y, n, rng) {
  const h = sp.height[0] + (sp.height[1] - sp.height[0]) * rng();
  // The leaf archetype is drawn at a nominal one metre, so whatever scales the
  // plant also scales its leaves. `width_m` is the CLUMP diameter, and a
  // riverbank shrub recorded at two metres across therefore grew sixty-
  // centimetre leaves and filled the river-bank shot with pale green arrowheads.
  // The shrubs have their own archetype now (K53, `placeShrub`), so this clamp
  // no longer stands between a two-metre clump and its own recorded width — it
  // bounds the leaf of an actual forb, which is what it was always for.
  // Clamped to the size a broad prairie leaf actually is — EXCEPT for a basal
  // rosette, whose recorded width IS the leaf span and whose whole diagnosis is
  // that the leaves are huge (prairie dock, 0.6-1.0 m across the rosette).
  const rosette = sp.form === 'forb_basal_scape';
  const spread = rosette
    ? THREE.MathUtils.clamp((sp.width ? mid(sp.width) * 0.5 : h * 0.18), 0.05, 0.55)
    : THREE.MathUtils.clamp(sp.width ? mid(sp.width) * 0.45 : h * 0.26, 0.07, 0.40);
  const c = tint(sp, rng() * 0.6, rng()).map((x) => x * patchOf(e, n));
  return set.push(e, y, n, rng() * Math.PI * 2, h, spread, 0.1 + rng() * 0.2,
    c[0], c[1], c[2], sp.conf) ? h : 0;
}

/**
 * A shrub, which is a different plant from a tall forb in the two ways a
 * visitor can see: it is WOODY and MULTI-STEMMED from the ground, and its
 * clump is as wide as the record says rather than as wide as a leaf.
 *
 * `width_m` is the reading that changes. On a forb it is a clump diameter that
 * has to be clamped to 0.40 m or the leaves become arrowheads (`placeForb`);
 * on a shrub it is the thing itself — *"low sprawling mats 1-3 m across"* is
 * `prunus_pumila`'s own recorded appearance, and drawn through `placeForb` that
 * plant came out as a 70 cm wand. So the recorded half-width IS the spread
 * here, and the archetype is authored to fill it.
 *
 * The floor and the ceiling are the records' own range and not a taste: the
 * narrowest shrub width in `data/flora` is 0.6 m (`quercus_velutina_grubs` in
 * the wet woods) and the widest 3.5 m (`crataegus_spp`), so 0.30-1.75 m of
 * half-width passes every one of the twenty-one records through unchanged and
 * still refuses a mis-typed 30 m clump.
 *
 * `arch` is small on purpose. A woody stem does not bend to the wind the way a
 * forb's does, and the same slot carries the wind sway — 0.04-0.12 against the
 * forb's 0.10-0.30 is the difference between a bush moving and a bush swaying.
 */
function placeShrub(set, sp, e, y, n, rng) {
  const h = sp.height[0] + (sp.height[1] - sp.height[0]) * rng();
  const spread = THREE.MathUtils.clamp(
    sp.width ? mid(sp.width) * 0.5 : h * 0.45, 0.30, 1.75);
  const c = tint(sp, rng() * 0.6, rng()).map((x) => x * patchOf(e, n));
  return set.push(e, y, n, rng() * Math.PI * 2, h, spread, 0.04 + rng() * 0.08,
    c[0], c[1], c[2], sp.conf) ? h : 0;
}

/**
 * The flower, and ONLY when the record says there is one: `sp.head` is null for
 * every vegetative grass, so no branch here can put a seed head on big bluestem
 * in July. See the July gate in the file header — it is unchanged.
 *
 * `plantH` is the height the plant was ACTUALLY given, not a fresh draw of the
 * same range, and it is only ever non-zero when the plant was actually drawn.
 * Both of those are the fix for the two heads the critic found floating in the
 * open sky with no stem beneath them.
 */
function maybeHead(heads, sp, e, y, n, rng, plantH, ring) {
  if (!sp.head || !(plantH > 0)) return;
  const set = heads[sp.head.kind];
  if (!set) return;
  set.ring(ring);
  // A forb instance IS one plant. A matrix instance is a bundle of shoots, and
  // only a minority of shoots in a grass clump carry a culm in mid-July — a
  // head on every tuft made a flowering cordgrass sward look like a wheat
  // field. L32.
  if (sp.role === 'matrix' || sp.role === 'emergent') {
    if (rng() > 0.16) return;
  }
  _c.setRGB(sp.head.color[0], sp.head.color[1], sp.head.color[2]);
  // One plant, several inflorescences, by architecture — see HEAD_OF_SHAPE.
  // A grass culm carries one panicle however the forb beside it branches.
  const grass = sp.role === 'matrix' || sp.role === 'emergent';
  const range = sp.head.count;
  const many = grass ? 1 : range[0] + ((rng() * (range[1] - range[0] + 1)) | 0);
  const tilt = sp.head.tilt;
  const top = plantH * sp.head.frac;
  const reach = PEDUNCLE[sp.head.kind] ?? 1.5;
  for (let i = 0; i < many; i++) {
    const size = sp.head.size[0] + (sp.head.size[1] - sp.head.size[0]) * rng();
    const lean = tilt[0] + (tilt[1] - tilt[0]) * rng();
    const a = rng() * Math.PI * 2;
    // The first head is terminal. The rest are carried DOWN the plant over the
    // architecture's own band, and the lower a branch starts the further out it
    // reaches — which is what puts a mountain mint's colour at knee height and
    // a loosestrife's up the whole stem, instead of parking every flower in the
    // scene on one plane a metre and a half off the ground where a standing
    // eye can barely see it against the sky.
    const down = i === 0 ? 0 : sp.head.band * rng();
    // Where the flower ends up. It is not where the instance goes: since
    // R-BUG7 the archetype's origin is the FOOT of its own stalk (see
    // `peduncle`), so this is the height the head reaches once the stalk under
    // it has been stood up and leaned over.
    const rise = top * (1 - down) * (0.94 + rng() * 0.10);
    // ...and this is where the branch leaves the stem, which is the whole of
    // the placement now. The stalk is `reach` head-sizes long and leans by
    // `lean`, so it lifts the head `cos(lean)` of that and carries it
    // `sin(lean)` of it out to the side — and BOTH come out of one rotation
    // about a point that is on the plant, instead of out of a position and a
    // lean that have to be kept in agreement. Four repairs went into keeping
    // them in agreement and the fifth is not doing that again.
    // Clamped into the plant, both ends. The upper clamp is what makes the
    // assertion provable rather than measured: `foot <= plantH`, and since
    // T-0035 the shader scales neither of them, so the stalk's foot is under
    // the plant's own top at every distance the pair is drawn at.
    const foot = Math.min(plantH, Math.max(0, rise - reach * size * Math.cos(lean)));
    if (!set.push(
      e,
      y + foot,
      n,
      rng() * Math.PI * 2, size, size, 0, _c.r, _c.g, _c.b, sp.conf, lean,
      // Which way it leans out — a fresh bearing per head, so a plant's
      // inflorescences ring its stem instead of all leaning one way.
      a,
      foot,
    )) {
      // T-0214. The set is full and this plant loses the rest of its
      // inflorescences. Say how many, so the shortfall is a number with a name
      // on it rather than a set that silently happens to sit on its ceiling.
      set.skip(many - i - 1);
      return;
    }
  }
}

/* -------------------------------------------------------------------------- */
/* archetype geometry                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Every archetype is built at NOMINAL size — one metre tall, one across, at the
 * origin — and the vertex shader scales it per instance from the record's own
 * `height_m`, which is how one geometry is cordgrass at 1.8 m and little
 * bluestem at 0.5 m in the same draw call. `aDir` is the blade's azimuth; the
 * shader arches each blade outward along it, so a tuft opens into a fountain.
 */
function emptyGeo() {
  return { pos: [], nor: [], col: [], dir: [], side: [], idx: [], n: 0 };
}
function finishGeo(g, name) {
  const geo = new THREE.BufferGeometry();
  geo.name = name;
  geo.setAttribute('position', new THREE.Float32BufferAttribute(g.pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(g.nor, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(g.col, 3));
  geo.setAttribute('aDir', new THREE.Float32BufferAttribute(g.dir, 2));
  geo.setAttribute('aSide', new THREE.Float32BufferAttribute(g.side, 3));
  geo.setIndex(g.idx);
  return geo;
}
function vert(g, x, y, z, nx, ny, nz, r, gg, b, dx, dz, sx = 0, sy = 0, sz = 0) {
  g.pos.push(x, y, z);
  g.nor.push(nx, ny, nz);
  g.col.push(r, gg, b);
  g.dir.push(dx, dz);
  // aSide is the offset from the archetype's own axis, in REAL metres, added
  // AFTER the height and spread scales — otherwise a wide clump gets wide
  // leaves, and cordgrass (0.5-0.9 m across, blades a centimetre or two wide)
  // ended up with leaves the width of a hand. It carries Y as well as XZ
  // because a grass blade TWISTS as it rises, so its width vector leaves the
  // horizontal plane, and because a basal rosette's leaves are a real size in
  // metres and must not scale with a three-metre flowering scape.
  g.side.push(sx, sy, sz);
  return g.n++;
}

/**
 * Light inside a closed sward, as a multiple of the species' own colour.
 *
 * Two things the round-1 ramp got wrong, and they are most of the near field's
 * tone. First, the argument is the height IN THE CANOPY and not the distance
 * along the blade: keyed off the blade's own length, a basal leaf 30 cm up in
 * a metre-and-a-half sward got the same lit tip as a culm reaching the top, so
 * the upper half of EVERY tuft came out pale and the near field read as a
 * bleached gradient. Second, and more important, sunlight does not arrive in a
 * stand as a smooth gradient — it arrives in FLECKS. At midday a fraction of
 * the leaves deep inside a prairie are in full sun through a gap and the rest
 * are in their neighbours' shade, and in the Woodworth photograph's nearest
 * five metres that is exactly what the bright pixels are: whole leaf faces at
 * (219, 233, 172), scattered at every depth, against a dark mass. A smooth
 * ramp cannot produce that. It produced a 25th percentile of 92 where the
 * photograph's is 31.
 *
 * `u` is height in the canopy, 0 at the floor and 1 at the surface; `fleck` is
 * this blade's own sunfleck gain, 0 when it is in shade.
 */
const CANOPY = {
  /** Diffuse light on the floor of a closed sward, and at its surface. */
  floor: 0.135,
  gradient: 0.62,
  gamma: 1.35,
  /** Chance a blade sits in a sunfleck, on the floor and at the surface. */
  fleckFloor: 0.05,
  fleckTop: 0.60,
  /** What a fleck is worth, and how much of it survives to depth u. */
  fleckGain: [0.80, 1.55],
  fleckReach: 0.55,
};
function shade(u, fleck = 0) {
  return CANOPY.floor + CANOPY.gradient * u ** CANOPY.gamma
    + fleck * (CANOPY.fleckReach + (1 - CANOPY.fleckReach) * u);
}

/** The same, shallower: a card is read almost edge-on, so the near field's
 *  near-black base turned the whole mid-ground into a dark wall. */
function cardShade(t) { return 0.22 + 0.62 * t; }

/**
 * A tuft of blades: the near-field workhorse. Half the blades are BASAL — short,
 * wide, low-angled leaves — and they are what closes the ground. A clump of
 * equal straps at full height reads as reeds in a pond; a real grass clump is
 * mostly leaf near the soil with a few shoots reaching the top of the sward.
 */
function tuftGeometry(blades = 12, segments = 2) {
  const g = emptyGeo();
  const rng = rngFrom(0x1835f10a);
  for (let b = 0; b < blades; b++) {
    // Half the blades are basal. They sprawl outward at a low angle, which is
    // where ground cover is cheapest to buy: a leaf lying over the soil hides
    // far more of it per triangle than one standing up in the air, and a real
    // grass clump is mostly leaf near the ground anyway.
    const basal = b < Math.round(blades / 2);
    const phi = (b / blades) * Math.PI * 2 + rng() * 0.9;
    const dx = Math.sin(phi);
    const dz = Math.cos(phi);
    // Lengths biased short: many leaves, few culms.
    const len = basal ? 0.24 + rng() * 0.34 : 0.40 + 0.60 * rng() ** 0.8;
    // Real half-widths, in metres: a coarse basal leaf is 3-6 cm across, a
    // culm leaf 1.5-3 cm. These are no longer multiplied by the clump spread.
    const wide = (basal ? 0.020 + rng() * 0.016 : 0.008 + rng() * 0.010);
    const lean = basal ? 0.52 + rng() * 0.44 : 0.14 + rng() * 0.26;
    const tone = 0.86 + rng() * 0.30;
    // Is THIS blade in a sunfleck? Decided once per blade, at the height its
    // tip reaches, so the lit leaves are scattered through the depth of the
    // stand instead of banded across the top of it. Nothing shades the topmost
    // leaves of a canopy, which is why fleckTop is essentially 1.
    const uTip = Math.min(1, (len * (1 - lean * 0.62)) / 0.92);
    const fleck = rng() < CANOPY.fleckFloor + (CANOPY.fleckTop - CANOPY.fleckFloor) * uTip
      ? CANOPY.fleckGain[0] + (CANOPY.fleckGain[1] - CANOPY.fleckGain[0]) * rng()
      : 0;
    // How far the blade rolls about its own axis between base and tip. A grass
    // leaf is not a flat ribbon standing on edge: it twists, which is why a
    // sward catches the sun in flecks rather than as one sheet. Round 1 gave
    // every blade in every tuft the same hand-set normal, and that — far more
    // than the exposure — is why 204,748 near-field pixels resolved into 697
    // colours against a photograph's 4,837.
    const roll = (rng() - 0.5) * 2.3;
    let prev = null;
    for (let s = 0; s <= segments; s++) {
      const t = s / segments;
      const half = wide * Math.max(0, 1 - t ** 1.5);
      // A grass leaf ARCHES: it rises, slows, and its tip falls away. Without
      // the droop term the tuft is a spray of straight straps and reads as a
      // yucca, which is what the first pass looked like.
      const y = len * (t - lean * 0.62 * t * t);
      const out = lean * t * t;
      const cx = dx * out;
      const cz = dz * out;
      // The blade's own frame at this station: tangent along it, width across
      // it, normal off its face — the normal is DERIVED from the arch instead
      // of asserted, so the vertical base of a blade presents a vertical face
      // and its drooping tip presents its face to the sky, which is what puts
      // a 70-degree sun on the top of the sward and nothing on its floor.
      const tx = dx * 2 * lean * t;
      const ty = len * (1 - 1.24 * lean * t);
      const tz = dz * 2 * lean * t;
      let wx = dz;
      let wy = 0;
      let wz = -dx;
      let nx = -dx * ty;
      let ny = dx * tx + dz * tz;
      let nz = -dz * ty;
      const nl = Math.hypot(nx, ny, nz) || 1;
      nx /= nl; ny /= nl; nz /= nl;
      // Roll the (width, normal) pair about the tangent. Both turn together,
      // so the twist is in the GEOMETRY and not a shading trick painted on a
      // flat ribbon.
      const cs = Math.cos(roll * t);
      const sn = Math.sin(roll * t);
      const wx2 = wx * cs + nx * sn;
      const wy2 = wy * cs + ny * sn;
      const wz2 = wz * cs + nz * sn;
      const nx2 = nx * cs - wx * sn;
      const ny2 = ny * cs - wy * sn;
      const nz2 = nz * cs - wz * sn;
      wx = wx2; wy = wy2; wz = wz2;
      const px = wx * half;
      const py = wy * half;
      const pz = wz * half;
      // 0.92 is the tallest blade's own top: `len` runs to 1.0 and the droop
      // takes about eight per cent off it, so a culm tip lands at the sward's
      // surface and reads as fully lit.
      const k = shade(Math.min(1, y / 0.92), fleck) * tone;
      const a = vert(g, cx, y, cz, nx2, ny2, nz2, k, k, k, dx, dz, -px, -py, -pz);
      const c = vert(g, cx, y, cz, nx2, ny2, nz2, k, k, k, dx, dz, px, py, pz);
      if (prev) g.idx.push(prev[0], prev[1], a, prev[1], c, a);
      prev = [a, c];
    }
  }
  return finishGeo(g, 'flora-tuft');
}

/**
 * A serrated clump card for the mid field, turned to the camera in the shader.
 * Four columns of different heights, because a rectangle reads as a fence and a
 * flat top edge reads as mown.
 */
function cardGeometry(columns = 7) {
  const g = emptyGeo();
  const rng = rngFrom(0x5a17c001);
  for (let i = 0; i < columns; i++) {
    // Tapered blades with a gap either side. Adjacent columns tile into a
    // rectangle, and a rectangle at 20 m reads as a hoarding however finely
    // its top edge is stepped.
    const cx = -0.5 + (i + 0.5) / columns + (rng() - 0.5) * 0.20;
    // Narrow, with real gaps. A column at 1.15/columns is a 23 cm 'blade' at
    // the card's own width, and at five metres that reads as a pale sail
    // hanging over the sward rather than as a clump of grass.
    const w0 = (0.5 / columns) * (0.34 + rng() * 0.40);
    const top = 0.38 + rng() * 0.62;
    const tip = (rng() - 0.5) * 0.40 * top;
    const k0 = cardShade(0);
    const k1 = cardShade(top) * (0.86 + rng() * 0.30);
    const a = vert(g, cx - w0, 0, 0, 0, 0.90, 0.44, k0, k0, k0, 0, 0);
    const b = vert(g, cx + w0, 0, 0, 0, 0.90, 0.44, k0, k0, k0, 0, 0);
    const c = vert(g, cx + tip - w0 * 0.14, top, 0, 0, 0.90, 0.44, k1, k1, k1, 0, 0);
    const d = vert(g, cx + tip + w0 * 0.14, top, 0, 0, 0.90, 0.44, k1, k1, k1, 0, 0);
    g.idx.push(a, b, c, b, d, c);
  }
  return finishGeo(g, 'flora-card');
}

/** A forb: one stem, four leaves. The flower is a separate archetype. */
function forbGeometry() {
  const g = emptyGeo();
  const rng = rngFrom(0x7c0ffee1);
  const w = 0.012;
  for (const ang of [0, Math.PI / 2]) {
    const dx = Math.sin(ang) * w;
    const dz = Math.cos(ang) * w;
    const k0 = shade(0.15);
    const k1 = shade(0.95);
    const a = vert(g, -dx, 0, -dz, 0, 1, 0, k0, k0, k0, 0, 0);
    const b = vert(g, dx, 0, dz, 0, 1, 0, k0, k0, k0, 0, 0);
    const c = vert(g, -dx, 1, -dz, 0, 1, 0, k1, k1, k1, 0, 0);
    const d = vert(g, dx, 1, dz, 0, 1, 0, k1, k1, k1, 0, 0);
    g.idx.push(a, b, c, b, d, c);
  }
  for (let i = 0; i < 4; i++) {
    const y = 0.22 + i * 0.17;
    const phi = i * 1.9 + rng();
    const dx = Math.sin(phi);
    const dz = Math.cos(phi);
    // Broad leaves: a mid-July near field is as much milkweed and bergamot
    // foliage as grass, and a forb drawn as a wire with four slivers on it
    // vanishes into the sward instead of breaking it up.
    const len = 0.42 - i * 0.055;
    const half = 0.150 - i * 0.020;
    const k0 = shade(y * 0.8);
    const k1 = shade(Math.min(1, y + 0.2));
    const a = vert(g, -dz * half, y, dx * half, dx * 0.3, 0.9, dz * 0.3, k0, k0, k0, dx, dz);
    const b = vert(g, dz * half, y, -dx * half, dx * 0.3, 0.9, dz * 0.3, k0, k0, k0, dx, dz);
    const c = vert(g, dx * len, y + len * 0.30, dz * len,
      dx * 0.3, 0.9, dz * 0.3, k1, k1, k1, dx, dz);
    g.idx.push(a, b, c);
    const d = vert(g, -dx * len * 0.55, y + len * 0.22, -dz * len * 0.55,
      -dx * 0.3, 0.9, -dz * 0.3, k1, k1, k1, -dx, -dz);
    g.idx.push(b, a, d);
  }
  return finishGeo(g, 'flora-forb');
}

/* --- the nine flower archetypes, one per row of HEAD_OF_SHAPE ------------- */
/*
 * All nine are built in a NOMINAL unit box: one across and one tall, centred on
 * the attachment point at y = 0, so the record's `inflorescence.size_m` scales
 * a Liatris spike to 30 cm and a Dalea thimble to 3 cm through the same two
 * numbers. Each carries a PEDUNCLE below the head, proportioned to it, because
 * a flower that ends where its stalk should begin is the floating sprite the
 * critic caught in the sky. And each is drawn about the vertical: the tilt is
 * per instance, on the instance matrix, so no two heads of a species present
 * the same face and none of them is ever exactly edge-on.
 */

/**
 * How far below its own head each archetype's stalk reaches, in units of the
 * head's size. It is a module constant and not a local because `maybeHead` has
 * to know it: a head is only ever offset from the plant's stem by as far as its
 * own stalk can lean back to reach it. Without that the branched inflorescences
 * came out as lollipops hanging in the air beside the scape — the same
 * unattached-flower failure the critic caught, one level down.
 */
const PEDUNCLE = {
  spike: 1.6,
  spire: 1.2,
  panicle: 1.4,
  ray: 2.2,
  raydroop: 2.2,
  pompom: 2.2,
  dome: 2.0,
  corymb: 2.2,
  compound: 2.0,
};

/**
 * A thin stalk from the attachment point down, in the archetype's own units —
 * and then the whole archetype is LIFTED so that the foot of that stalk sits at
 * the origin. It is the last call in every head builder for exactly that
 * reason.
 *
 * **Anchoring a head at its foot rather than at its flower is what makes
 * "attached" an invariant instead of a number** (R-BUG7). The instance origin is
 * then the point on the stem where the branch leaves it; the tilt rotates the
 * head out about that point, so the offset from the stem is generated BY the
 * stalk instead of being a second number that has to agree with it; and
 * `chiFade` scales the whole thing about the foot, so a head slides down its own
 * stalk as its plant shrinks instead of staying out at a fixed offset while the
 * stalk that was supposed to reach it gets shorter. The head's rise is then
 * `footRise <= plantHeight`, and that inequality is the assertion — proved
 * rather than measured. Since T-0035 nothing shrinks at all: the ring ramp is
 * coverage, every drawn plant is drawn at its recorded height, and the clamp in
 * `maybeHead` carries the invariant on its own at the one size there is.
 */
function peduncle(g, drop = 1.5, wide = 0.022, k = 0.42) {
  for (let i = 0; i < 2; i++) {
    const a = (i / 2) * Math.PI;
    const dx = Math.sin(a) * wide;
    const dz = Math.cos(a) * wide;
    const p0 = vert(g, -dx, -drop, -dz, dx, 0.4, dz, k, k, k, 0, 0);
    const p1 = vert(g, dx, -drop, dz, dx, 0.4, dz, k, k, k, 0, 0);
    const p2 = vert(g, -dx, 0, -dz, dx, 0.4, dz, k * 1.5, k * 1.5, k * 1.5, 0, 0);
    const p3 = vert(g, dx, 0, dz, dx, 0.4, dz, k * 1.5, k * 1.5, k * 1.5, 0, 0);
    g.idx.push(p0, p1, p2, p1, p3, p2);
  }
  for (let i = 1; i < g.pos.length; i += 3) g.pos[i] += drop;
}

/** A dense column: Liatris's button spike, Physostegia, Amorpha, the cattail's
 *  brown spadix, Spiraea's conical panicle. A WAND, not a cone — a cordgrass
 *  spike is millimetres across on a culm a quarter-metre long. */
function spikeGeometry() {
  const g = emptyGeo();
  for (let i = 0; i < 3; i++) {
    const a = (i / 3) * Math.PI;
    // A WAND. Round 1's comment about a field of pale traffic cones was right
    // and this stays narrow: the whole one-sided cordgrass inflorescence is two
    // or three centimetres across on a spike a quarter-metre long.
    const dx = Math.sin(a) * 0.062;
    const dz = Math.cos(a) * 0.062;
    // Florets open from the top down, so a spike is paler at its shoulder.
    const p0 = vert(g, -dx * 0.55, -0.48, -dz * 0.55, dx, 0.2, dz, 0.72, 0.72, 0.72, 0, 0);
    const p1 = vert(g, dx * 0.55, -0.48, dz * 0.55, dx, 0.2, dz, 0.72, 0.72, 0.72, 0, 0);
    const p2 = vert(g, -dx, 0.06, -dz, dx, 0.2, dz, 1.10, 1.10, 1.10, 0, 0);
    const p3 = vert(g, dx, 0.06, dz, dx, 0.2, dz, 1.10, 1.10, 1.10, 0, 0);
    const p4 = vert(g, 0, 0.50, 0, dx, 0.5, dz, 1.22, 1.22, 1.22, 0, 0);
    g.idx.push(p0, p1, p2, p1, p3, p2, p2, p3, p4);
  }
  peduncle(g, PEDUNCLE.spike, 0.016);
  return finishGeo(g, 'flora-head-spike');
}

/**
 * Culver's root: a terminal spire with two to four lateral spires off its
 * shoulder, which is the candelabra the vocabulary names and the plant's whole
 * silhouette. Drawn as the same mesh as a Liatris button it scored under ten
 * pixels and was indistinguishable from it.
 */
function spireGeometry() {
  const g = emptyGeo();
  const wand = (cx, cz, base, top, wide, k) => {
    for (let i = 0; i < 2; i++) {
      const a = (i / 2) * Math.PI;
      const dx = Math.sin(a) * wide;
      const dz = Math.cos(a) * wide;
      const p0 = vert(g, cx - dx, base, cz - dz, dx, 0.2, dz, k * 0.72, k * 0.72, k * 0.72, 0, 0);
      const p1 = vert(g, cx + dx, base, cz + dz, dx, 0.2, dz, k * 0.72, k * 0.72, k * 0.72, 0, 0);
      const p2 = vert(g, cx - dx, top - 0.12, cz - dz, dx, 0.2, dz, k, k, k, 0, 0);
      const p3 = vert(g, cx + dx, top - 0.12, cz + dz, dx, 0.2, dz, k, k, k, 0, 0);
      const p4 = vert(g, cx, top, cz, dx, 0.5, dz, k * 1.15, k * 1.15, k * 1.15, 0, 0);
      g.idx.push(p0, p1, p2, p1, p3, p2, p2, p3, p4);
    }
  };
  wand(0, 0, -0.34, 0.50, 0.055, 1.06);
  for (let i = 0; i < 4; i++) {
    // The laterals spread about a third of the terminal spire's own length —
    // narrower than that and the candelabra collapses back into the single
    // wand it is supposed to be distinguishable from.
    const a = (i / 4) * Math.PI * 2 + 0.4;
    const r = 0.30 + (i % 2) * 0.10;
    wand(Math.sin(a) * r, Math.cos(a) * r, -0.40, 0.24 + (i % 2) * 0.16, 0.046, 0.94);
  }
  peduncle(g, PEDUNCLE.spire, 0.020);
  return finishGeo(g, 'flora-head-spire');
}

/** Bluejoint, wild rice, wood nettle: an OPEN panicle — a diffuse airy cloud
 *  of fine branches, which is nothing like a wand and is why the wet prairie's
 *  second grass read as a second cordgrass. */
function panicleGeometry() {
  const g = emptyGeo();
  const rng = rngFrom(0x9a11c1e0);
  for (let i = 0; i < 7; i++) {
    const a = rng() * Math.PI * 2;
    const t = rng();
    const y0 = -0.42 + t * 0.55;
    const len = 0.20 + rng() * 0.28;
    const dx = Math.sin(a);
    const dz = Math.cos(a);
    const w = 0.012;
    const k0 = 0.70;
    const k1 = 1.16;
    const p0 = vert(g, -dz * w, y0, dx * w, dx * 0.5, 0.7, dz * 0.5, k0, k0, k0, 0, 0);
    const p1 = vert(g, dz * w, y0, -dx * w, dx * 0.5, 0.7, dz * 0.5, k0, k0, k0, 0, 0);
    const p2 = vert(g, dx * len * 0.5, y0 + len * 0.62, dz * len * 0.5,
      dx * 0.5, 0.7, dz * 0.5, k1, k1, k1, 0, 0);
    g.idx.push(p0, p1, p2);
  }
  peduncle(g, PEDUNCLE.panicle, 0.014);
  return finishGeo(g, 'flora-head-panicle');
}

/**
 * A composite head. `droop` swings the rays DOWN around a raised central cone
 * — Ratibida and Echinacea — while the flat form is Rudbeckia, Heliopsis and
 * the Silphiums. Two shapes, one builder, because the difference between them
 * is exactly one sign and the vocabulary distinguishes them.
 */
function rayGeometry(droop) {
  const g = emptyGeo();
  // Enough rays that they OVERLAP into a disc with a toothed rim. Nine spokes
  // radiating off a small centre reads as a spider, not a flower, and at nine
  // centimetres on a prairie-dock scape it was a yellow star in the sky.
  const rays = 14;
  const coneY = droop ? 0.20 : 0.09;
  const tipY = droop ? -0.24 : 0.015;
  const disc = [];
  const rim = droop ? 0.30 : 0.34;
  const c0 = vert(g, 0, coneY, 0, 0, 1, 0, 0.55, 0.55, 0.55, 0, 0);
  for (let i = 0; i < rays; i++) {
    const a = (i / rays) * Math.PI * 2;
    disc.push(vert(g, Math.sin(a) * rim, coneY * 0.35, Math.cos(a) * rim,
      Math.sin(a) * 0.5, 0.86, Math.cos(a) * 0.5, 0.74, 0.74, 0.74, 0, 0));
  }
  for (let i = 0; i < rays; i++) g.idx.push(c0, disc[i], disc[(i + 1) % rays]);
  for (let i = 0; i < rays; i++) {
    // Each ray is a broad petal spanning two rim points and reaching past its
    // neighbours, so the outline closes.
    const a = ((i + 0.5) / rays) * Math.PI * 2;
    const dx = Math.sin(a);
    const dz = Math.cos(a);
    const nx = droop ? dx * 0.45 : dx * 0.16;
    const nz = droop ? dz * 0.45 : dz * 0.16;
    const b = disc[i];
    const c = disc[(i + 1) % rays];
    const d = vert(g, dx * 0.50, tipY, dz * 0.50, nx, 0.90, nz, 1.18, 1.18, 1.18, 0, 0);
    g.idx.push(b, c, d);
  }
  peduncle(g, droop ? PEDUNCLE.raydroop : PEDUNCLE.ray, 0.020);
  return finishGeo(g, droop ? 'flora-head-raydroop' : 'flora-head-ray');
}

/** Monarda, Dalea, a rattlesnake-master globe, a hazel husk, a dogwood berry
 *  cluster: a small dense ball on the stem tip. */
function pompomGeometry() {
  const g = emptyGeo();
  for (let i = 0; i < 3; i++) {
    const phi = (i / 3) * Math.PI;
    const dx = Math.sin(phi) * 0.5;
    const dz = Math.cos(phi) * 0.5;
    const nx = Math.cos(phi);
    const nz = -Math.sin(phi);
    const a = vert(g, -dx, -0.30, -dz, nx, 0.5, nz, 0.72, 0.72, 0.72, 0, 0);
    const b = vert(g, dx, -0.30, dz, nx, 0.5, nz, 0.72, 0.72, 0.72, 0, 0);
    const c = vert(g, -dx, 0.34, -dz, nx, 0.5, nz, 1.14, 1.14, 1.14, 0, 0);
    const d = vert(g, dx, 0.34, dz, nx, 0.5, nz, 1.14, 1.14, 1.14, 0, 0);
    g.idx.push(a, b, c, b, d, c);
  }
  peduncle(g, PEDUNCLE.pompom, 0.030);
  return finishGeo(g, 'flora-head-pompom');
}

/**
 * A DOMED umbel — swamp milkweed, common milkweed, a nodding onion. A
 * hemisphere of florets, and emphatically not the flat horizontal plate that
 * used to stand in for it: at 1.68 m eye height a head at 0.6-0.9 m is seen
 * about eleven degrees above the horizontal, so a plate presented its EDGE and
 * a seven-centimetre umbel came out three pixels wide at five metres.
 */
function domeGeometry() {
  const g = emptyGeo();
  const rings = 2;
  const seg = 7;
  const grid = [];
  for (let r = 0; r <= rings; r++) {
    const row = [];
    const th = (r / rings) * (Math.PI / 2);
    const rr = Math.sin(th) * 0.5;
    const yy = Math.cos(th) * 0.40;
    const k = 1.20 - 0.42 * (r / rings);
    for (let s = 0; s < seg; s++) {
      const a = (s / seg) * Math.PI * 2;
      const dx = Math.sin(a);
      const dz = Math.cos(a);
      row.push(vert(g, dx * rr, yy - 0.08, dz * rr,
        dx * Math.sin(th), Math.cos(th) + 0.15, dz * Math.sin(th), k, k, k, 0, 0));
    }
    grid.push(row);
  }
  for (let r = 0; r < rings; r++) {
    for (let s = 0; s < seg; s++) {
      const s1 = (s + 1) % seg;
      g.idx.push(grid[r][s], grid[r + 1][s], grid[r][s1],
        grid[r][s1], grid[r + 1][s], grid[r + 1][s1]);
    }
  }
  peduncle(g, PEDUNCLE.dome, 0.024);
  return finishGeo(g, 'flora-head-dome');
}

/**
 * A flat-topped corymb — ironweed, mountain mint, wild quinine, butterfly
 * weed. Still a disc, because that is what the plant is, but built with a
 * standing TILT so it is never read edge-on, and given a shallow crown so it
 * has a silhouette from the side as well as a face from above. The rest of the
 * tilt is per instance, on the instance matrix.
 */
function corymbGeometry() {
  const g = emptyGeo();
  const seg = 9;
  const ring = [];
  const c0 = vert(g, 0, 0.13, 0, 0, 1, 0, 1.22, 1.22, 1.22, 0, 0);
  for (let i = 0; i < seg; i++) {
    const a = (i / seg) * Math.PI * 2;
    const dx = Math.sin(a);
    const dz = Math.cos(a);
    // A corymb is a cluster of heads, not a wheel: the rim is uneven.
    const rr = 0.42 + 0.08 * Math.sin(a * 3.0 + 1.1);
    ring.push(vert(g, dx * rr, 0.02 + 0.03 * Math.sin(a * 2.0), dz * rr,
      dx * 0.30, 0.94, dz * 0.30, 0.90, 0.90, 0.90, 0, 0));
  }
  for (let i = 0; i < seg; i++) g.idx.push(c0, ring[i], ring[(i + 1) % seg]);
  // The under-side, so the disc has a body when it is seen from below.
  const u0 = vert(g, 0, -0.09, 0, 0, -1, 0, 0.58, 0.58, 0.58, 0, 0);
  for (let i = 0; i < seg; i++) g.idx.push(u0, ring[(i + 1) % seg], ring[i]);
  peduncle(g, PEDUNCLE.corymb, 0.020);
  return finishGeo(g, 'flora-head-corymb');
}

/** A COMPOUND umbel — water hemlock, golden alexanders, sweet cicely: several
 *  small domed umbellets on rays from one point, which is the architecture
 *  that reads as an umbellifer and nothing else does. */
function compoundGeometry() {
  const g = emptyGeo();
  const umbellets = 5;
  const seg = 4;
  for (let u = 0; u <= umbellets; u++) {
    const a = ((u - 1) / umbellets) * Math.PI * 2 + 0.3;
    const cx = u === 0 ? 0 : Math.sin(a) * 0.38;
    const cz = u === 0 ? 0 : Math.cos(a) * 0.38;
    const cy = u === 0 ? 0.16 : 0.02 + 0.05 * Math.sin(a * 2.0);
    const rr = u === 0 ? 0.15 : 0.13;
    const c0 = vert(g, cx, cy + 0.05, cz, 0, 1, 0, 1.20, 1.20, 1.20, 0, 0);
    const ring = [];
    for (let i = 0; i < seg; i++) {
      const b = (i / seg) * Math.PI * 2;
      ring.push(vert(g, cx + Math.sin(b) * rr, cy, cz + Math.cos(b) * rr,
        Math.sin(b) * 0.4, 0.9, Math.cos(b) * 0.4, 0.86, 0.86, 0.86, 0, 0));
    }
    for (let i = 0; i < seg; i++) g.idx.push(c0, ring[i], ring[(i + 1) % seg]);
    // The ray that carries it back to the centre.
    if (u > 0) {
      const w = 0.010;
      const p0 = vert(g, cx - Math.cos(a) * w, cy - 0.01, cz + Math.sin(a) * w,
        0, 1, 0, 0.50, 0.50, 0.50, 0, 0);
      const p1 = vert(g, cx + Math.cos(a) * w, cy - 0.01, cz - Math.sin(a) * w,
        0, 1, 0, 0.50, 0.50, 0.50, 0, 0);
      const p2 = vert(g, 0, -0.14, 0, 0, 1, 0, 0.44, 0.44, 0.44, 0, 0);
      g.idx.push(p0, p1, p2);
    }
  }
  peduncle(g, PEDUNCLE.compound, 0.022);
  return finishGeo(g, 'flora-head-compound');
}

/**
 * A basal-scape plant: prairie dock, compass plant, wild iris, plantain. A
 * ROSETTE of big paddle leaves lying at the ground and a nearly naked scape
 * over it — the dossier names prairie dock's 40 cm basal rosette explicitly,
 * and it is the plant's whole diagnosis. Drawn with the generic forb it became
 * a three-metre leafy stalk with sixty-centimetre leaves halfway up it, which
 * is the giant the timber critic handed back from the foreground.
 *
 * The rosette is scaled by the instance's SPREAD, which `placeForb` takes from
 * the record's own `width_m`, so the leaves are the recorded size of the
 * rosette and do not grow with the flowering scape above them.
 */
function rosetteGeometry() {
  const g = emptyGeo();
  const rng = rngFrom(0x51190010);
  // The scape: bare, thin, and the full height of the plant.
  for (const ang of [0.3, 0.3 + Math.PI / 2]) {
    const dx = Math.sin(ang) * 0.010;
    const dz = Math.cos(ang) * 0.010;
    const k0 = shade(0.10);
    const k1 = shade(0.98);
    const a = vert(g, -dx, 0, -dz, dz, 0.3, -dx, k0, k0, k0, 0, 0);
    const b = vert(g, dx, 0, dz, dz, 0.3, -dx, k0, k0, k0, 0, 0);
    const c = vert(g, -dx, 1, -dz, dz, 0.3, -dx, k1, k1, k1, 0, 0);
    const d = vert(g, dx, 1, dz, dz, 0.3, -dx, k1, k1, k1, 0, 0);
    g.idx.push(a, b, c, b, d, c);
  }
  // Five huge paddle leaves, rising out of the crown and arching back down.
  // Their SPAN is in the archetype's own units and is scaled by the rosette's
  // recorded radius; their rise is a small fraction of the plant's height, so a
  // 40 cm prairie-dock rosette stands about 15 cm proud of the ground while a
  // plantain's lies flat, which is what both plants do.
  for (let i = 0; i < 5; i++) {
    const phi = (i / 5) * Math.PI * 2 + rng() * 0.7;
    const dx = Math.sin(phi);
    const dz = Math.cos(phi);
    const len = 0.80 + rng() * 0.20;
    const wide = 0.30 + rng() * 0.12;
    const rise = 0.050 + rng() * 0.026;
    const k0 = shade(0.14);
    const k1 = shade(0.34 + rng() * 0.12);
    const k2 = shade(0.22);
    const nx = -dx * 0.30;
    const nz = -dz * 0.30;
    const a = vert(g, dx * 0.06, 0.004, dz * 0.06, nx, 0.95, nz, k0, k0, k0, 0, 0);
    const b = vert(g, dx * len * 0.45 - dz * wide, rise, dz * len * 0.45 + dx * wide,
      nx, 0.95, nz, k1, k1, k1, 0, 0);
    const c = vert(g, dx * len * 0.45 + dz * wide, rise, dz * len * 0.45 - dx * wide,
      nx, 0.95, nz, k1, k1, k1, 0, 0);
    const d = vert(g, dx * len, rise * 0.42, dz * len, nx, 0.95, nz, k2, k2, k2, 0, 0);
    g.idx.push(a, b, c, b, d, c);
  }
  return finishGeo(g, 'flora-rosette');
}

/**
 * The shrub: four woody stems out of one root and a broad leafy shell over
 * them — forty-eight leaf sprays in three bands, the lowest arching down over the
 * stems (K56, K57) — in the same nominal box every other archetype uses — one tall, one
 * across, so `height_m` scales the stems and the recorded clump half-width
 * scales the spread (`placeShrub`).
 *
 * **Multi-stemmed from the ground is the whole diagnosis, not decoration.** It
 * is what separates a shrub from a tree above it and from a forb beside it, and
 * three of these records say so in their own text: the black-oak grubs are
 * *"multi-stemmed low clonal oak sprouting from an old root system"*, the plum
 * is *"thicket-forming"*, the sand cherry a *"low sprawling mat"*. A single
 * stalk cannot read as any of those at any size.
 *
 * **The proportions are a RECONSTRUCTION and are recorded as one** (`docs/
 * LIBERTIES.md`). No source in this repository states the branching habit of a
 * Chicago hazel or a river-bank dogwood, and the alternative to inventing one
 * within bounds is the wand that is there today. What bounds it: the stems rise
 * to 0.55-0.95 of the recorded height and lean out to 0.30-0.55 of the recorded
 * half-width, so the SILHOUETTE is the record's own two numbers and only the
 * arrangement inside it is invented. Nothing here reads a figure the record
 * does not carry.
 *
 * Cost: 104 triangles against the forb's 12 and the near tuft's 27 — 40 until
 * K56 raised the spray count to 32 and K57 to 48, each +32. It is drawn from the
 * forb lattice, so it takes slots the forb archetype used to take rather than
 * adding any, and the 167 of them the census counts in the wet woods' ring is
 * 17,368 triangles there, 1.7 % of the scene's million. The layout and the grain are `shrub-grain.js`;
 * what they cost and what they buy is `tools/measure_spray_grain.mjs --gate`.
 */
function shrubGeometry() {
  const g = emptyGeo();
  const rng = rngFrom(0x5c123b00);
  // The stems, the bands, the spray plan and every corner are `shrub-grain.js`,
  // which imports nothing — so the grain can be measured in a second without a
  // browser, and the measurement reads the SAME arithmetic the scene draws. The
  // seed and the generator stay here, because a measurement that re-seeds is
  // measuring a different bush.
  const { stems, sprays } = shrubLayout(rng, SHRUB_GRAIN);
  for (const s of stems) {
    // Woody, but not a silhouette: `color.g` is this module's only occlusion
    // term, so a stem written at 0.05 is a black stick where the foliage does
    // not cover it, and a shrub's stems are exposed for the lower half of it.
    const k0 = shade(0.16);
    const k1 = shade(0.42);
    const [p0, p1, p2, p3] = s.corners;
    const a = vert(g, p0[0], p0[1], p0[2], s.dx, 0.35, s.dz, k0, k0, k0, 0, 0);
    const b = vert(g, p1[0], p1[1], p1[2], s.dx, 0.35, s.dz, k0, k0, k0, 0, 0);
    const c = vert(g, p2[0], p2[1], p2[2], s.dx, 0.35, s.dz,
      k1, k1, k1, s.dx, s.dz);
    const d = vert(g, p3[0], p3[1], p3[2], s.dx, 0.35, s.dz,
      k1, k1, k1, s.dx, s.dz);
    g.idx.push(a, b, c, b, d, c);
  }
  // The COUNT is what K56 moved and the GRAIN is what K57 set: sixteen plates
  // covered 17.7 % of the shell and could be seen straight through, thirty-two
  // covered 30.9 %, and the finer question — the same total plate area as more,
  // smaller masses — is answered by `tools/measure_spray_grain.mjs` rather than
  // by preference. `SHRUB_GRAIN` in `shrub-grain.js` carries the answer and the
  // reasoning; the shading is all that is left here.
  for (const p of sprays) {
    const k0 = shade(0.24 + p.top * 0.30);
    const k1 = shade(Math.min(1, 0.58 + p.top * 0.40));
    const [p0, p1, p2, p3] = p.corners;
    const a = vert(g, p0[0], p0[1], p0[2],
      p.dx * 0.3, 0.9, p.dz * 0.3, k0, k0, k0, p.dx, p.dz);
    const b = vert(g, p1[0], p1[1], p1[2],
      p.dx * 0.3, 0.9, p.dz * 0.3, k0, k0, k0, p.dx, p.dz);
    const c = vert(g, p2[0], p2[1], p2[2],
      p.dx * 0.3, 0.9, p.dz * 0.3, k1, k1, k1, p.dx, p.dz);
    const d = vert(g, p3[0], p3[1], p3[2],
      p.dx * 0.3, 0.9, p.dz * 0.3, k1, k1, k1, p.dx, p.dz);
    g.idx.push(a, b, c, b, d, c);
  }
  return finishGeo(g, 'flora-shrub');
}

/** Smooth value noise, 0..1. No texture, no table. */
function vnoise(x, z) {
  const xi = Math.floor(x);
  const zi = Math.floor(z);
  const fx = x - xi;
  const fz = z - zi;
  const sx = fx * fx * (3 - 2 * fx);
  const sz = fz * fz * (3 - 2 * fz);
  const h = (a, b) => (hash3(a, b, 0x2f1c) & 0xffff) / 65535;
  const a0 = h(xi, zi) * (1 - sx) + h(xi + 1, zi) * sx;
  const a1 = h(xi, zi + 1) * (1 - sx) + h(xi + 1, zi + 1) * sx;
  return a0 * (1 - sz) + a1 * sz;
}

/* -------------------------------------------------------------------------- */
/* materials                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * One material family for every plant: Lambert, vertex colours, double sided,
 * per-instance transform and wind in the vertex shader. The instance matrix
 * carries the POSITION ONLY; yaw, height, spread and arch arrive in `aFlora`,
 * which is what lets one canonical tuft be six species at six heights in one
 * draw call, and keeps the wind in world space — a rotation baked into the
 * instance matrix would have silently turned it per plant.
 */
function plantMaterial({ uniforms, billboard = false, membrane = 1.0 }) {
  const mat = new THREE.MeshLambertMaterial({
    color: 0xffffff,
    vertexColors: true,
    side: THREE.DoubleSide,
  });
  const prior = mat.onBeforeCompile;
  mat.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    Object.assign(shader.uniforms, {
      uChiTime: uniforms.uChiTime,
      uChiWind: uniforms.uChiWind,
      uChiSway: uniforms.uChiSway,
      uChiWaveK: uniforms.uChiWaveK,
    });
    Object.assign(shader.uniforms, {
      uChiSun: uniforms.uChiSun,
      uChiSunCol: uniforms.uChiSunCol,
      uChiSky: uniforms.uChiSky,
    });
    shader.vertexShader = `
attribute vec2 aDir;
attribute vec3 aSide;       // offset from the archetype's axis, in real metres
attribute vec4 aFlora;      // height, spread, arch, yaw
attribute vec4 aChiRing;    // fade ring: outer, band, inner, innerBand
attribute float aChiRise;   // metres this origin stands over its plant's base
                            // — read by the gates, no longer by this program
uniform float uChiTime;
uniform vec2  uChiWind;
uniform float uChiSway;
uniform float uChiWaveK;
varying vec3 vChiNW;        // world normal, unflipped
varying vec3 vChiPW;        // world position
varying float vChiLit;      // how much of the sky this point can see, 0..1.6
varying float vChiFade;     // the ring ramp, as coverage: 0 absent, 1 solid
varying float vChiDither;   // this plant's own phase on the ordered dither
` + shader.vertexShader
      .replace('#include <beginnormal_vertex>', /* glsl */`
#include <beginnormal_vertex>
{
  float cy = cos(aFlora.w), sy = sin(aFlora.w);
  objectNormal.xz = vec2(objectNormal.x * cy + objectNormal.z * sy,
                        -objectNormal.x * sy + objectNormal.z * cy);
}
`)
      .replace('#include <begin_vertex>', /* glsl */`
#include <begin_vertex>
{
  vec3 chiInst = vec3(instanceMatrix[3][0], instanceMatrix[3][1], instanceMatrix[3][2]);
  float chiT = clamp(transformed.y, 0.0, 1.0);
  // The ring ramp, measured from where the camera IS this frame. It used to be
  // baked into the height on the CPU, where it could only change when the
  // lattice was rebuilt — every 1.2 m walked, against a 2.2 m band, so a plant
  // came up out of the ground to 55% of its height between one frame and the
  // next. Here it is continuous, and the lattice is inset from it by the
  // rebuild step (see \`ringsFor\`) so nothing is ever drawn before it is placed.
  float chiD = distance(cameraPosition.xz, chiInst.xz);
  // The floor is a MICRON, not a tenth of a millimetre, and it is only there to
  // guard the division: a spread boundary hands its ring over as a step of
  // width \`HARD\`, and a floor wider than the step would put the step back into
  // a ramp a plant could be caught halfway up. See \`HARD\` in flora.js.
  float chiFade = clamp((aChiRing.x - chiD) / max(aChiRing.y, ${f(HARD)}), 0.0, 1.0);
  if (aChiRing.w > 0.0) chiFade *= clamp((chiD - aChiRing.z) / aChiRing.w, 0.0, 1.0);
  // **THE RAMP IS AN ALPHA, NOT A HEIGHT** (T-0035). The owner, twice: plants
  // "grow up out of the ground" as you walk at them rather than fading in. Both
  // repairs before this one made the ramp SMOOTHER — continuous per frame, then
  // inset inside its own lattice so no plant arrived already grown — and both
  // left the ramp driving SCALE, which is the thing he was describing. A plant
  // that goes from zero to full size about its own base is growing, however
  // finely you subdivide it.
  //
  // So the ramp is handed to the fragment shader as coverage and the geometry
  // is drawn at the height the record gives it, at every distance it is drawn
  // at at all. The plant stands its full height the first frame it exists;
  // what changes with distance is how much of it is written.
  //
  // Outside the ramp entirely it collapses to a point rather than rasterising
  // a full-size plant only to discard every fragment of it: the annulus between
  // the fade edge and the lattice edge is \`step\` metres wide plus the fringe,
  // and it carries a real share of the near lattice.
  vChiFade = chiFade;
  // A per-instance phase on the ordered dither below. The 4x4 matrix has
  // sixteen levels, and a ramp in DISTANCE quantised to sixteen levels is
  // sixteen concentric contours about the walker — the same "constant world
  // radius is a constant screen row" failure the fringe was built to break
  // (ROADMAP § S6a item 3). Offsetting each plant's threshold by a hash of its
  // own world position scatters the contour across the field: fract(bayer +
  // phase) is still uniform on [0,1), so the expected coverage is unchanged.
  vChiDither = fract(sin(dot(floor(chiInst.xz * 64.0), vec2(12.9898, 78.233))) * 43758.5453);
  // Arch each blade outward along its own azimuth, in nominal space.
  transformed.xz += aDir * (aFlora.z * chiT * chiT);
  // Scale: height from the record, spread from the archetype's own proportions.
  transformed.y *= aFlora.x;
  transformed.xz *= aFlora.y;
  transformed += aSide;
  // ...and nothing scales it by the ramp. See \`vChiFade\` above: a plant is
  // drawn at its own height or it is not drawn.
  transformed *= step(1e-4, chiFade);
  ${billboard ? /* glsl */`
  // Turn the card to the camera about Y. Nothing else uses the yaw slot here.
  vec2 chiToCam = cameraPosition.xz - chiInst.xz;
  float chiLen = length(chiToCam);
  vec2 chiF = chiLen > 0.001 ? chiToCam / chiLen : vec2(0.0, 1.0);
  transformed.xz = vec2(transformed.x * chiF.y + transformed.z * chiF.x,
                       -transformed.x * chiF.x + transformed.z * chiF.y);
  objectNormal.xz = vec2(objectNormal.x * chiF.y + objectNormal.z * chiF.x,
                        -objectNormal.x * chiF.x + objectNormal.z * chiF.y);
  ` : /* glsl */`
  float chiCy = cos(aFlora.w), chiSy = sin(aFlora.w);
  transformed.xz = vec2(transformed.x * chiCy + transformed.z * chiSy,
                       -transformed.x * chiSy + transformed.z * chiCy);
  `}
  ${/* glsl */`
  // Wind, in world space, after the plant has been turned: a travelling wave
  // across the field plus a slow gust, both fixed at the base and free at the
  // tip. This is the "wind-combed" reading the sources give the wet prairie.
  float chiPh = dot(chiInst.xz, uChiWind) * uChiWaveK + uChiTime;
  float chiGust = 0.62 + 0.38 * sin(chiPh * 0.31 + 1.7);
  transformed.xz += uChiWind
    * (uChiSway * chiGust * sin(chiPh) * chiT * chiT * aFlora.x);
  `}
  // The world-space frame the sun terms need, built HERE rather than read off
  // three's vNormal: <defaultnormal_vertex> has already run by this point, so
  // three's normal never sees the billboard turn above, and the instance
  // matrix carries a real rotation for the tilted flower heads.
  vChiNW = normalize(mat3(modelMatrix) * mat3(instanceMatrix) * objectNormal);
  vChiPW = (modelMatrix * instanceMatrix * vec4(transformed, 1.0)).xyz;
  // The archetype's own base-to-tip ramp, BEFORE the species colour multiplies
  // it. It is the one occlusion term this module has — how deep in the clump
  // this point sits — and it has to gate every light path, not just the
  // reflected one: a transmission term that ignores it puts the same glow on
  // the floor of the sward as on the blade tips, and a sward with no floor is
  // as wrong as one with no sun (measured: median 56 -> 148, nothing under 20).
  vChiLit = color.g;
}
`)
      // The head descent that used to live here — a world-space lowering of a
      // flower head's origin by `aChiRise * (1 - fade)`, patched in after the
      // instance transform because the instance matrix carries a real rotation —
      // is GONE with the scale it existed to chase. It kept a head on its stem
      // while its plant shrank; nothing shrinks now, so `foot <= plantH` holds
      // at the one size everything is drawn at (R-BUG7's invariant, and the
      // clamp in `maybeHead` is still what proves it). `aChiRise` stays on the
      // instance because `tools/measure_head_support.mjs` and the smoke read it
      // back to locate a stalk's foot.
      .replace('#include <project_vertex>', /* glsl */`
vec4 mvPosition = vec4(transformed, 1.0);
#ifdef USE_INSTANCING
  mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;
`);
    // The fake sunward normal that used to live at <normal_fragment_begin> —
    // `normal.y = abs(normal.y)` — is GONE. It was standing in for exactly the
    // transmission this block now models, and while it stopped back faces going
    // black it also meant nothing in the sward was ever properly lit or
    // properly shaded: every fragment got the same middling wash, which is the
    // truncated distribution the structure critic measured (p99 132, not one
    // pixel over 230). Three's own double-sided flip is left to do its job, so
    // dot(N, L) is now a real two-sided term.
    shader.fragmentShader = `
uniform vec3 uChiSun;
uniform vec3 uChiSunCol;
uniform vec3 uChiSky;
varying vec3 vChiNW;
varying vec3 vChiPW;
varying float vChiLit;
varying float vChiFade;
varying float vChiDither;

// Ordered 4x4 Bayer, the same screen-door translucency the confidence view
// dithers an unevidenced wall with (confidence.js) — a stable per-pixel
// threshold, so no sorting, no blending and no order dependence inside a batch.
// A sward is the case that most needs those properties: eight thousand
// double-sided instances that would have to be depth-sorted every frame to be
// drawn transparent, on a material three renders in the opaque pass.
float chiBayer4(vec2 fragXY) {
  int x = int(mod(fragXY.x, 4.0));
  int y = int(mod(fragXY.y, 4.0));
  int i = x + y * 4;
  float m[16];
  m[0]  =  0.0; m[1]  =  8.0; m[2]  =  2.0; m[3]  = 10.0;
  m[4]  = 12.0; m[5]  =  4.0; m[6]  = 14.0; m[7]  =  6.0;
  m[8]  =  3.0; m[9]  = 11.0; m[10] =  1.0; m[11] =  9.0;
  m[12] = 15.0; m[13] =  7.0; m[14] = 13.0; m[15] =  5.0;
  float v = 0.0;
  for (int k = 0; k < 16; k++) { if (k == i) v = m[k]; }
  return (v + 0.5) / 16.0;
}
` + shader.fragmentShader.replace('#include <clipping_planes_fragment>', /* glsl */`
#include <clipping_planes_fragment>
// T-0093. WHICH RINGS STILL REACH THIS LINE, because it is no longer all of
// them: the near ring's outer edge and the mid ring's inner edge hand their
// ground over by DENSITY now (TUNE \`spreadOuter\`/\`spreadInner\`), so every plant
// on either of those boundaries arrives with \`vChiFade\` at 0 or 1 and the guard
// below sends it straight past. What is left dithering is the mid and forb
// rings' OUTER edges, where a plant is a few pixels wide and the far band
// stands over the same ground.
//
// T-0187. That last sentence used to read "at 18–27 m", and it was only true
// of the desktop: \`band\` was not scaled with the ring, so on a phone the same
// ramps ran from 5.4 m and 7.4 m and 15.4 % of the frame inside nine metres
// was written through this line. The bands are cut to the ring now, at every
// setting, so the claim holds where it is made — the verge, which is what a
// walker looks at, is written solid at \`light\`, \`balanced\` and \`full\` alike.
//
// T-0035. Coverage first, before a single lighting instruction is spent on a
// fragment that is about to be thrown away — and guarded, so a plant that is
// wholly inside its ring reaches the shader that existed before this: the
// branch is what the confidence view's own comment warns about paying for.
if (vChiFade < 1.0 && fract(chiBayer4(gl_FragCoord.xy) + vChiDither) >= vChiFade) discard;
`).replace('#include <opaque_fragment>', /* glsl */`
{
  // The face we can see, whichever side of the sheet it is.
  vec3 chiN = normalize(vChiNW) * (gl_FrontFacing ? 1.0 : -1.0);
  vec3 chiV = normalize(cameraPosition - vChiPW);
  float chiNL = dot(chiN, uChiSun);

  // What the leaf lets through. Keyed on the NEGATIVE half of the same N.L
  // three used for the reflection, so a blade is lit on one side and glowing
  // on the other and never both. The lobe is a (0.5 + 0.5 cos) remap rather
  // than a raw cos^n: at 70 degrees the July sun is overhead, not behind the
  // subject, and a hard forward lobe would never fire at eye height.
  float chiFwd = pow(clamp(dot(chiV, -uChiSun) * 0.5 + 0.5, 0.0, 1.0), ${f(LEAF.forward)});
  // What comes THROUGH is the leaf's own hue at the leaf's own transmittance —
  // not its albedo, which is what caps a reflective model — gated by how much
  // of the sky this point in the clump can see.
  vec3 chiHue = diffuseColor.rgb
    / max(max(diffuseColor.r, diffuseColor.g), max(diffuseColor.b, 1e-4));
  // SQUARED, and that is the whole difference between a sward with a sun in it
  // and a sward painted lime. A linear gate spread the glow evenly over every
  // blade from floor to tip and lifted the median from 56 to 148 while the
  // photographs sit at 72 and 93; squared, the floor of a clump keeps a
  // hundredth of it and the exposed tips keep more than all of it, which is
  // what a canopy actually does to light on its way down.
  // ...and by how much of this fragment is one leaf rather than a stand-in for
  // many. A mid-field CARD is already an average of lit blades and shaded
  // interior, so giving it a whole leaf's transmission bleached the middle
  // distance into a field of pale spikes brighter than the near ground — a
  // clump at twenty metres is a dark green mass in every one of the bar
  // photographs.
  float chiOpen = pow(clamp(vChiLit, 0.0, 2.30), 2.0) * ${f(membrane)};
  vec3 chiFilter = chiHue
    * vec3(${f(LEAF.tint[0])}, ${f(LEAF.tint[1])}, ${f(LEAF.tint[2])}) * chiOpen;
  vec3 chiExtra = uChiSunCol * (
      ${f(LEAF.transmit)} * max(-chiNL, 0.0) * (0.42 + 0.58 * chiFwd)   // through it
    + ${f(LEAF.scatter)} * max(chiNL, 0.0)                              // and around it
  ) * chiFilter;
  chiExtra += uChiSky * (${f(LEAF.skyTransmit)} * chiFilter);

  // The cuticle: a waxy film over the leaf, so a narrow lobe at a dielectric
  // F0 with the Fresnel edge that makes a grazing blade flare.
  vec3 chiH = normalize(uChiSun + chiV);
  float chiSpec = pow(max(dot(chiN, chiH), 0.0), ${f(LEAF.gloss)});
  float chiF = ${f(LEAF.f0)} + ${f(1 - LEAF.f0)}
    * pow(1.0 - clamp(dot(chiV, chiH), 0.0, 1.0), 5.0);
  chiExtra += uChiSunCol
    * (chiSpec * chiF * ${f(LEAF.specular)} * step(0.0, chiNL) * chiOpen);

  outgoingLight += chiExtra;
}
#include <opaque_fragment>
`);
  };
  mat.needsUpdate = true;
  return mat;
}

/** A float that always carries a decimal point, because GLSL will not take
 *  `0` where it wants a float and a template literal will happily write one. */
function f(v) {
  return Number.isInteger(v) ? `${v}.0` : String(v);
}
