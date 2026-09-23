/**
 * shrub-grain.js — the shrub archetype's LAYOUT, with no renderer attached.
 *
 * `flora.js` owns the geometry: it seeds the generator, calls `vert`, shades the
 * wood dark and the foliage light, and hands three.js a buffer. None of that is
 * needed to answer *how big a leaf mass should be*, and K56 could not answer it
 * because the numbers only existed inside a function that imports three — so its
 * shell-fill figures (17.7 % → 30.9 %) were taken by a script nobody committed
 * and cannot be reproduced or re-pointed at a candidate.
 *
 * So the arithmetic lives here, imports nothing, and runs in node as happily as
 * in a browser. `tools/measure_spray_grain.mjs` is its second reader, and the
 * two agree by construction rather than by two people porting one loop.
 *
 * WHAT A SPRAY IS, restated because every number below depends on it (K56, L124):
 * a spray is a **leaf MASS** — a season's leaves on one shoot — not a leaf. Two
 * triangles cannot draw a 10 cm hazel leaf at any scale, and the same abstraction
 * carries the tree canopy's plates and the near tuft's bundle of shoots here.
 *
 * UNITS. The archetype is authored in clump half-widths: `1.0` horizontally is the
 * recorded half-width and `1.0` vertically the recorded height, and `flora.js`
 * scales both per instance from the record. So a length of 0.35 here is 0.39 m on
 * a 2.25 m hazel and 0.18 m on a 1 m sand cherry, which is the right direction for
 * both.
 */

/**
 * The knobs K57 exists to set, and the answer it measured.
 *
 * **K57 asked the wrong question and the tool says so.** The parcel asked whether
 * the shell is better read as 32 masses of 0.4 m or 64 of 0.2 m *at the same total
 * plate area* — and holding the area is exactly what cannot be done here, because
 * the plates are what carries the clump's RECORDED half-width. Measured over 24
 * bearings by `tools/measure_spray_grain.mjs`: holding the area at 64 sprays takes
 * the drawn reach from **0.990 of the recorded half-width to 0.890** and the plate
 * from 37 cm down to 26 cm on a 2.25 m hazel. It buys cover — 36.9 % → 45.4 % —
 * by spending a number the research owns on one the renderer owns.
 *
 * So the grain trades against TRIANGLES, not against area, and the size holds. At
 * `plate` 1.0 the count alone gives 32 → 48 → 64 sprays a foliage cover of
 * **36.9 % → 46.9 % → 51.3 %** for 72 → 104 → 136 triangles, with reach unmoved at
 * 0.990–0.998. Ten of the fourteen available points arrive in the first 32
 * triangles and four in the second, so K57 shipped **48 at the knee** and left the
 * last 4.4 points measured and unspent.
 *
 * **K59 SPENT THEM, and only because the frame was finally read (T-0020).** K57
 * justified 48 on a triangle count and a draw-call count, which is not a frame:
 * the shrub batch does not split, so the cost of a finer grain is fill and vertex
 * work, and neither had ever been measured anywhere in this archetype's history.
 * `tools/measure_shrub_frame_cost.mjs` measures it, in the wet woods where 158
 * stand in one ring, at the most expensive of eight bearings, with the clock held
 * and a one-pixel readback fencing every frame:
 *
 *   desktop 1280×800   4282.30 ms → 4410.30 ms   **+3.0 %**
 *   mobile  390×780    2739.60 ms → 2795.80 ms   **+2.1 %**
 *
 * and the A/B/A control — the shipped grain measured again after the candidate —
 * came back **+0.2 %**, so the 3.0 is fifteen times the runner's own drift rather
 * than inside it. 4.4 points of shell cover and 2.9 of stem cover for three per
 * cent of a frame, on a SOFTWARE rasteriser, which is the most fill-sensitive
 * witness this parcel could have been given. So **64 is what ships.**
 *
 * `fill` and `plate` move TOGETHER or not at all: shrinking a plate without adding
 * plates is the fault K56 diagnosed — an isolated plate with sky on both sides of
 * it reads as one enormous leaf.
 *
 * Total sprays = `2 * stems + fill`. Triangles per shrub = `2 * stems +
 * 2 * sprays`.
 */
export const SHRUB_GRAIN = {
  stems: 4,
  fill: 56,
  /** Linear scale on a spray's length and half-width. 1.0 is K56's plate, and
   *  K57 measured that it is the recorded clump width and must not shrink. */
  plate: 1.00,
};

/**
 * Three bands, and the LOWEST one arches DOWN (K56). Nothing in the first cut
 * hung below its own attachment, so the shell stayed open exactly where the four
 * stems are most exposed — and a stem is written dark enough to be a black stick
 * wherever foliage does not cover it.
 */
export const SHRUB_BANDS = [
  { top: 0.66, lean: 0.28, scale: 0.94, droop: false },
  { top: 0.46, lean: 0.44, scale: 0.86, droop: false },
  { top: 0.28, lean: 0.40, scale: 0.78, droop: true },
];

/** A stem's thickness in archetype units: ~3 cm on a 2.4 m hazel, ~1 cm on a
 *  1 m sand cherry. */
const STEM_W = 0.030;

/**
 * The whole archetype as numbers: four woody stems out of one root, and the leaf
 * masses hung over them.
 *
 * `rng` is passed in rather than seeded here so `flora.js` keeps ownership of the
 * archetype's seed, and so the draw order — every generator call, in sequence — is
 * identical to the loop this was lifted out of. A measurement that re-seeds is
 * measuring a different bush.
 *
 * Returns quad corners, because the corner arithmetic is the part both readers
 * need and the part that is easy to port wrongly.
 */
export function shrubLayout(rng, grain = SHRUB_GRAIN) {
  const stems = [];
  const tops = [];
  for (let i = 0; i < grain.stems; i++) {
    // Fanned, not radial: a clonal clump leans its stems out around one root,
    // and an even fan of four reads as a candelabra from every bearing.
    const phi = (i / grain.stems) * Math.PI * 2 + rng() * 0.8;
    const dx = Math.sin(phi);
    const dz = Math.cos(phi);
    const lean = 0.30 + rng() * 0.25;
    const top = 0.55 + rng() * 0.33;
    const px = -dz * STEM_W;
    const pz = dx * STEM_W;
    stems.push({
      dx, dz, lean, top,
      corners: [
        [px, 0, pz],
        [-px, 0, -pz],
        [dx * lean + px, top, dz * lean + pz],
        [dx * lean - px, top, dz * lean - pz],
      ],
    });
    tops.push([dx, dz, lean, top]);
  }

  // Two sprays per stem carry the stem's own bearing, then the fill spreads the
  // rest around the clump in the three bands. The order matters: it is the order
  // the generator was consumed in when the shell fill was measured.
  const plan = [];
  for (const [dx, dz, lean, top] of tops) {
    plan.push([dx, dz, lean, top, 1.00, false]);
    plan.push([dx, dz, lean * 0.62, top * 0.60, 0.86, false]);
  }
  for (let i = 0; i < grain.fill; i++) {
    const band = SHRUB_BANDS[i % SHRUB_BANDS.length];
    const phi = (i / grain.fill) * Math.PI * 2 + 0.9 + rng() * 0.5;
    plan.push([Math.sin(phi), Math.cos(phi),
      band.lean + rng() * 0.22, band.top + rng() * 0.16, band.scale, band.droop]);
  }

  const sprays = [];
  for (const [dx, dz, lean, top, scale, droop] of plan) {
    // K56 left this range alone deliberately and K57 scales it, because the two
    // only move together: 0.26-0.42 of the clump radius at `plate` 1.0.
    const len = (0.26 + rng() * 0.16) * scale * grain.plate;
    const half = (0.15 + rng() * 0.09) * scale * grain.plate;
    // The tip never leaves the nominal box: a plant is as tall as its record
    // says, and a spray that overshot 1.0 would make every shrub in the town
    // taller than the height the census reads back off it. A drooping shoot is
    // bounded the other way instead — it may fall at most half way back to the
    // ground from its own attachment, so no tip is ever pushed below y = 0.
    const rise = droop
      ? -Math.min(0.06 + rng() * 0.10, top * 0.5)
      : Math.min(0.05 + rng() * 0.09, 1 - top);
    const bx = dx * lean;
    const bz = dz * lean;
    sprays.push({
      dx, dz, lean, top, len, half, rise, droop,
      corners: [
        [bx - dz * half * 0.5, top, bz + dx * half * 0.5],
        [bx + dz * half * 0.5, top, bz - dx * half * 0.5],
        [bx + dx * len - dz * half, top + rise, bz + dz * len + dx * half],
        [bx + dx * len + dz * half, top + rise, bz + dz * len - dx * half],
      ],
    });
  }
  return { stems, sprays };
}

/** Triangles one shrub costs at a given grain. Two per stem, two per spray. */
export function shrubTriangles(grain = SHRUB_GRAIN) {
  return 2 * grain.stems + 2 * (2 * grain.stems + grain.fill);
}
