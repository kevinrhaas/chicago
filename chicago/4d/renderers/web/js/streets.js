/**
 * streets.js — dated earth travelways, draped on the committed heightfield.
 *
 * The compiled scene index supplies two different widths and they stay
 * different here:
 *
 *   corridor_width_m  the 80-foot platted right-of-way used to answer
 *                     "which street am I standing in?"
 *   track_width_m     the narrower, visibly worn wagon path inside it
 *
 * The second is a stated visual liberty.  It is not allowed to flatten the
 * terrain or author a second collision surface: every ribbon vertex samples
 * terrain.surfaceHeight(), and the walker continues to stand on that exact same
 * heightfield.  Segments whose centres or edges are under water are omitted,
 * leaving honest gaps at unbridged channels rather than painting a ford.
 */

import * as THREE from 'three';

const STEP_M = 2.25;
const LIFT_M = 0.022;
// R-BUG4. Bisection steps used to find how far a panel's dry ground reaches
// before the water mask starts. Six halvings of a 5.25 m half-width settle to
// ~8 cm, which is finer than the heightfield the mask is sampled from, so more
// steps would be reporting precision the mask does not have.
const CLIP_STEPS = 6;
// A trimmed panel narrower than this is dropped rather than drawn: below about
// a metre it is no longer a road anybody could walk down, and a sliver at the
// waterline would be a claim rather than a rendering.
const MIN_PANEL_W_M = 1.0;
// T-0110. A panel is allowed to miss the ground between its own vertices by
// this much before it is subdivided; each subdivision halves the panel both
// ways, to at most 2^MAX_DRAPE_LEVEL pieces per axis (0.28 m along a 2.25 m
// step). The tolerance is the LIFT_M scale on purpose: a miss under it stays
// inside what the polygon offset already absorbs, so refining past it would
// spend triangles the picture cannot show. Measured on the shipped field, the
// whole town settles for +9k triangles (~1.5 % of the 'light' ceiling) and
// only bridge-approach and bank panels refine at all.
const DRAPE_TOL_M = 0.03;
const MAX_DRAPE_LEVEL = 3;
const LEVEL = { attested: 0, inferred: 0.5, reconstructed: 1 };
/**
 * T-0184 — A BEND USED TO OPEN A WEDGE OF PRAIRIE, AND THE MITRE THAT CLOSES IT.
 *
 * Every panel was built square to ITS OWN chord, so the row at a shared
 * centreline point was drawn twice — once perpendicular to the incoming chord
 * and once to the outgoing one. The two rows crossed at the centreline and
 * diverged towards the edges: on the outside of the turn that left a triangle of
 * unpainted ground, apex on the centreline and `half * tan(turn/2)` long at the
 * ribbon's edge, and on the inside it stacked a matching overlap that blended
 * the transparent surface over itself.
 *
 * MEASURED on the shipped build before the fix, `tools/measure_road_joints.mjs`,
 * a 2 cm plan lattice over every authored bend: **23.47 m2 of ground inside the
 * nominal ribbon carried no roadway**, worst at South Water Street's west
 * approach — 4.29 m2 at the single 17.8-degree bend at [120, -57], on a 10.5 m
 * track — with three more of South Water's own bends between 1.8 and 4.2 m2 and
 * the fort road's 39-degree turn at 2.59 m2. Dearborn's corner, the one L178
 * admitted, measures 0.00: South Water Street's roadway covers the whole of it.
 *
 * THE FIX. One offset direction per centreline POINT rather than per chord: the
 * bisector of the two chord normals, `1 / cos(turn/2)` long so it still stands
 * the recorded half-width from each chord. Both panels emit that same corner, so
 * neither a gap nor an overlap is arithmetically possible, and the ribbon's edge
 * runs continuously from one panel to the next.
 *
 * AND WHY IT IS CAPPED. A mitred corner necessarily stands `half *
 * (sec(turn/2) - 1)` beyond the bend vertex — 0.17 m at the fort road's turn,
 * 0.06 m at South Water's — while `drawn_placement_census.mjs` holds every drawn
 * vertex within 0.05 m of its own street's half-width, and that census is what
 * catches a mirrored ribbon. So the cap is the census's own tolerance with a
 * margin, and it is spent by CUTTING the turn rather than by truncating the
 * corner: a joint too sharp to mitre in one step is mitred in `k` steps, whose
 * outer corners are the intersections of `k + 1` lines each tangent to the
 * half-width circle. That polygon still covers every point the round buffer
 * does — a truncated corner would not — and no corner of it stands more than
 * MITRE_MAX_OVERHANG_M out. Four bends in this town need k = 2 and one needs
 * k = 3; the whole town pays 22 triangles for them.
 *
 * The concave side is never cut. There the two offset strips already overlap and
 * the nominal ribbon reaches exactly the full mitre point, so subdividing that
 * side would pull the ribbon INSIDE its own recorded width and open a gap on the
 * inside of the turn to close one on the outside. The asymmetry is the geometry,
 * not a preference.
 *
 * A point whose chords are collinear to within MITRE_MIN_TURN_RAD is left
 * square, which is every point of every straight street and every point
 * `sampled()` interpolates: the flat town emits byte-for-byte the geometry it
 * always did.
 */
const MITRE_MAX_OVERHANG_M = 0.04;
const MITRE_MIN_TURN_RAD = 1e-6;
// A guard rather than a path: nothing in `data/streets/` turns more than 39.3
// degrees, and at a hairpin the mitre point runs away as sec(turn/2). Past this
// the joint stays square and is COUNTED, so a dataset that grew one cannot lose
// its wedge in silence.
const MITRE_MAX_TURN_RAD = (120 * Math.PI) / 180;

/**
 * WHY A ROAD READS AT ALL — R-BUG2, and the two separate faults behind it.
 *
 * The owner reported roads that "disappear in places, and when you fly over
 * them you lose them". Three mechanisms were proposed; the harness measured
 * them at unoccluded road pixels (see `roadContrast()` in
 * `tools/smoke_renderer.mjs`), and only two of the three are real.
 *
 * REFUTED — mip-averaged alpha falling under `alphaTest`. Plausible, and the
 * shape of the v74 treeline bug, but turning mipmaps OFF made every band WORSE
 * (south_water 250-600 m: 22 % of probes reached the screen with mips, 6 %
 * without). The mip chain is holding a sub-pixel ribbon together, not erasing
 * it. `minFilter` is left alone.
 *
 * FAULT 1, at eye level and at range — THE DEPTH FIGHT. A road 250-600 m out
 * along South Water Street was unoccluded, in front of the camera, and changed
 * the picture by **0.3 L\*** (14 % of probes perceptible). One unit of polygon
 * offset is nothing once depth precision has degraded that far, so the coplanar
 * terrain won the test in patches — the reported "in places". Deepening the
 * offset alone took that band to **3.3 L\* / 71 %**.
 *
 * FAULT 2, from the air — THE ROAD IS 4 % OPAQUE. From `from_above` the ribbon
 * is many pixels wide, unoccluded, and wins the depth test, and it still moved
 * the picture by **1.1 L\*** with ZERO probes perceptible at 100-250 m. The
 * cause is the authored alpha: for a lightly worn track `body` was
 * `0.08 + ruts*0.54 - crown*0.04`, so away from the two wheel ruts the surface
 * was 8 % earth over 92 % prairie, and at the crown 4 %. A road nobody can see
 * is not a subtle road. The baselines below are raised so the FAINTEST surface
 * still reads, while the ordering graded > worn > light — which is a modelled
 * attribute with its own confidence — is preserved. Recorded in
 * `docs/LIBERTIES.md`.
 *
 * FLOOR, for the thin end — a ribbon narrower than this many screen pixels has
 * its alpha scaled up in proportion, capped, so that a track receding to the
 * horizon fades rather than dropping out. Same principle as the
 * `MIN_SILHOUETTE_PX` floor in `trees.js`: never let a feature fall below the
 * pixel it needs to be seen at all. It binds only where the ribbon is thin —
 * from the air 0.02 of a wide road is nothing, so this is not what fixed
 * fault 2.
 *
 * ---------------------------------------------------------------------------
 * R-BUG3 — AND THE ROAD AT YOUR FEET. The owner reported, on the dev preview
 * with both fixes above already in, that the ruts read in the mid-distance and
 * the road is simply not there in the near field. Measured at a station
 * standing on a crossing (`roadContrast()` gained one, because neither gated
 * station stood on a road at all): 2-40 m scored **1.5 L\* with 30 % of probes
 * perceptible**, against 3.4 / 87 % in the very next band out. It now reads
 * **3.1 / 80 % on mobile and 3.2 / 60 % on desktop**, measured on the published
 * mirror.
 *
 * REFUTED — near-field sward occlusion, the parcel's prime suspect. Every one
 * of the near probes was UNOCCLUDED: the harness re-shoots its road markers
 * with the sward and the trees hidden, and the near band's marked count does
 * not move. No grass is hiding this road; the road is painting almost nothing.
 * The clearing corridor is therefore not the fault either, and neither is
 * touched here — widening one to win a contrast score would falsify a recorded
 * ground cover, which the parcel forbids and this fix does not need.
 *
 * FAULT — ALPHA IS A COVERAGE FRACTION, AND COVERAGE ONLY AVERAGES AT RANGE.
 * The authored alpha says what share of the ground is bare earth: 0.46 at the
 * crown of a graded track, 0.30 for a lightly worn one. Far off, one pixel
 * spans many patches and a blend is the right picture of that mixture. At your
 * feet one pixel spans ONE patch, which in life is either earth or grass, and
 * the blend instead paints a uniform wash of grass-with-a-hint-of-dirt. The
 * harness measures both ends of it: the same near probes rendered fully opaque
 * score **3.4 L\*** (4.3 desktop), so the contrast is there in the ribbon's own
 * colour and the shipped alpha was throwing well over half of it away. (The ground is genuinely darker
 * underfoot than at range — L\* 51.0 against 52.7-56.3 — so the near field has
 * less contrast to spend, which is why spending it all matters here.)
 *
 * THE LIFT, and what it does not do. Inside `NEAR_FULL_M` the alpha is scaled
 * by `NEAR_GAIN`, fading back to unity by `NEAR_FADE_M` — which is the outer
 * edge of the band the report is about, so every band the earlier gates hold
 * is arithmetically untouched. It is a GAIN, not a floor: graded > worn >
 * light is a modelled attribute with its own confidence and it survives
 * scaling. Nothing in `data/` moves, no recorded cover changes, and the mean
 * coverage the record states is still what the picture shows at the distance
 * where a mixture is what a pixel means. Recorded in `docs/LIBERTIES.md`.
 *
 * ---------------------------------------------------------------------------
 * R-A1 — THE ACCESSIBILITY AID, AND WHY IT IS ALLOWED TO EXIST.
 *
 * A user control that boosts road contrast converts a defect into a preference
 * and takes the pressure off fixing the default, which is why this was
 * deliberately deferred on 2026-08-14. It ships now because R-BUG3 made the
 * default correct on 2026-08-15: the near band scores 3.1 L\* of a measured
 * ceiling of 3.4 on mobile. The aid is layered ON a correct default; it is not
 * a substitute for one, and it must never be allowed to retire R-W2's textured
 * coverage, which is the honest fix for the ceiling itself.
 *
 * What it is: a viewing accommodation, like the units toggle. Contrast
 * sensitivity varies and a phone screen in sunlight is brutal — which is the
 * exact condition R-BUG3 was reported from. It is NOT a claim about how visible
 * an 1835 street was, and nothing in `data/` moves when it is used.
 *
 * THE DEFAULT IS OFF AND OFF IS ARITHMETICALLY THE OLD SHADER. `uRoadAid` is 0
 * unless a visitor moves the slider, and at 0 the two lines below reduce to
 * `min(a * 1.0, MAX_ALPHA)` — which is the statement that was already there.
 * That is the K24 constraint inherited whole: `tools/critic_shots.mjs`,
 * `tools/light_probe.mjs` and every band in `smoke_renderer.mjs` measure the
 * default, so a gate must not be passable by moving this control. The smoke
 * asserts all three halves of that — the uniform reads 0 with no stored
 * preference, raising it CHANGES the frame, and dropping it back restores the
 * frame — because a control that does not reach the render reports "no effect"
 * for the same reason a broken thermometer reports a steady temperature
 * (R-BUG1's `--no-sun-shadow`).
 *
 * WHAT IT COSTS AT MAXIMUM, stated rather than buried. `AID_GAIN` is
 * `1 / 0.24`: 0.24 is the faintest body alpha any surface authors (a lightly
 * worn track at its crown), so at full aid the faintest road reaches opaque —
 * which is exactly the ceiling R-BUG3 measured by forcing the near probes
 * opaque. Below maximum the gain is a scale and the graded > worn > light
 * ordering survives it, the same way it survives `NEAR_GAIN`. AT maximum every
 * surface saturates and that ordering is gone: the aid has stopped depicting a
 * modelled attribute and is drawing a road you can follow. That is the point of
 * it, and it is why the readout names the default rather than only a number.
 */
const MIN_TRACK_PX = 2.0;
const MAX_THIN_BOOST = 6.0;
const MAX_ALPHA = 0.92;
// T-0713. How faint an entirely INVENTED track reads while the confidence view
// is on. It scales the worn texture only — never whether the ribbon is drawn,
// which is the line's claim and is carried on `_confidence` — and it is inert
// at uConfMode == 0, so the ordinary daylight frame is untouched. 0.45 was
// chosen to sit clear of the 0.34 the view already uses to dither invented
// massing: a track we made up should read fainter than one we did not, and
// still plainly fainter than the road it is painted on is solid.
const INVENTED_TRACK_ALPHA = 0.45;
const NEAR_FULL_M = 15.0;
const NEAR_FADE_M = 40.0;
const NEAR_GAIN = 2.4;
/**
 * T-0114 — THE MIDDLE OF THE ROAD, which had no remedy at all.
 *
 * Two boosts existed and each was right for its own end: `NEAR_GAIN` lifts the
 * road under the walker's feet (R-BUG3, which measured 1.5 L* / 30 % there), and
 * the `MIN_TRACK_PX` floor lifts a ribbon once it is thinner than two screen
 * pixels. **Between them nothing lifted anything**, and the gate read that hole
 * as a non-monotonic profile down one open street: 90 % · 87 % · **33 %** · 97 %.
 * Contrast that merely fell off with distance would not come back at 250 m.
 *
 * Nothing turned the band. The trough was created the day the near field was
 * fixed and the middle was left where it had always been — and no bake reached
 * the smoke for long enough afterwards for anyone to see it.
 *
 * MEASURED, AND THE FIRST SUSPECT WAS WRONG. The obvious reading is that the
 * thin-pixel floor should reach further in, so `MIN_TRACK_PX` was doubled to 4.0
 * and the band re-read: **ΔL* 1.8 of 3.2, 33 %, identical to the digit.** At
 * 100-250 m the ribbon is still many pixels wide, so `clamp(4.0/trackPx, 1, 6)`
 * is still 1.0 and that path cannot reach the trough at any setting.
 *
 * So the middle gets a boost of its own, on the one quantity that is neither a
 * pixel count nor a near-field ramp: distance from the eye, sustained across the
 * gap and released where the thin-pixel floor takes over. `MID_GAIN` is far
 * gentler than `NEAR_GAIN` because the middle is not invisible, only under its
 * bar — this lifts a 33 % band over 55 %, it does not repaint the town.
 *
 * WHY IT IS `max()` AND NOT A PRODUCT, below: the two ramps overlap between 15
 * and 40 m, and multiplying them would stack to 4.1x there — re-breaking the
 * near field that R-BUG3 tuned. Taking the larger leaves every metre under 40 m
 * reading exactly what it read before this change.
 */
const MID_FULL_M = 40.0;
const MID_FADE_M = 700.0;
const MID_GAIN = 1.7;
// R-A1. The faintest authored body alpha is 0.28 - 0.04 = 0.24 (light worn
// earth at the crown); this takes that one surface to opaque at full aid.
const AID_GAIN = 1 / 0.24;

function pointSegment(e, n, a, b) {
  const dx = b[0] - a[0];
  const dn = b[1] - a[1];
  const len2 = dx * dx + dn * dn || 1e-9;
  const t = Math.max(0, Math.min(1, ((e - a[0]) * dx + (n - a[1]) * dn) / len2));
  const pe = a[0] + dx * t;
  const pn = a[1] + dn * t;
  return { distance: Math.hypot(e - pe, n - pn), e: pe, n: pn, t };
}

/**
 * T-0111 — THE PLATTED LINE AND THE WHEEL LINE ARE TWO CLAIMS, AND ONE FIELD
 * WAS CARRYING BOTH.
 *
 * The widths were already split — `corridor_width_m` answers "which street am I
 * standing in?" and `track_width_m` is the worn earth drawn inside it — but the
 * LINE was not, and it turned out to matter at exactly one place in the town.
 * Dearborn's platted line stops at [699, 18], on the crest of the drawbridge
 * approach fill; the causeway deck's south edge is at [697.65, 20.70]. Measured
 * on the shipped build, every station up the fill to n 18 lands on drawn
 * roadway and every station past it lands on none: the ribbon ends exactly
 * where the record does, 2.70 m short of the boards, and a visitor climbing
 * from South Water crossed a band of bare crest to reach the bridge.
 *
 * THE ONE-LINE FIX IS THE WRONG FIX, AND IT WAS MEASURED RATHER THAN ARGUED.
 * Appending the bend to `path_local_enu_m` fails two gates, because that field
 * is the PLAT: `tools/generate_plat_lots.py --check` re-derives every block
 * face by offsetting the whole polyline (PLAT GRID DRIFT the length of
 * Dearborn) and `tools/measure_corridor_intrusion.py --gate` re-scores the
 * corridor against it (30 laps against a committed 29 — the drawbridge itself
 * newly lapping by 0.66 m). Both were run with the appended path before this
 * split existed.
 *
 * So a street may now carry `drawn_track_local_enu_m`, the wagon-worn wheel
 * line, and THIS MODULE IS THE ONLY THING THAT PREFERS IT. `hitsAt`, `status`
 * and `blocksGrowth` keep reading `path`, because "which street is this",
 * "what is ahead" and "where is the corridor cleared" are all questions about
 * the plat; the compiler bounds the drawn line inside that same corridor and
 * lets it overhang the platted ends by at most four metres, so it can meet an
 * abutment and cannot become a second plat. `bounds` covers both lines, since
 * a box that excluded the drawn one would answer "not near this street" for
 * ground the street is drawn on.
 */
function prepare(raw) {
  const path = (raw.path_local_enu_m ?? []).map(([e, n]) => [Number(e), Number(n)]);
  const authored = raw.drawn_track_local_enu_m;
  const drawn = Array.isArray(authored) && authored.length >= 2
    ? authored.map(([e, n]) => [Number(e), Number(n)])
    : path;
  const pad = Math.max(raw.corridor_width_m ?? 24.384, raw.track_width_m ?? 6) * 0.5;
  const es = [...path, ...drawn].map((p) => p[0]);
  const ns = [...path, ...drawn].map((p) => p[1]);
  return {
    ...raw,
    path,
    drawn,
    corridor_width_m: raw.corridor_width_m ?? 24.384,
    track_width_m: raw.track_width_m ?? 6,
    bounds: {
      e0: Math.min(...es) - pad, e1: Math.max(...es) + pad,
      n0: Math.min(...ns) - pad, n1: Math.max(...ns) + pad,
    },
  };
}

function nearestOn(record, e, n) {
  const b = record.bounds;
  if (e < b.e0 || e > b.e1 || n < b.n0 || n > b.n1) return null;
  let best = null;
  for (let i = 1; i < record.path.length; i++) {
    const hit = pointSegment(e, n, record.path[i - 1], record.path[i]);
    if (!best || hit.distance < best.distance) best = { ...hit, segment: i - 1 };
  }
  return best ? { ...best, street: record } : null;
}

function sampled(path) {
  const out = [];
  for (let i = 1; i < path.length; i++) {
    const a = path[i - 1];
    const b = path[i];
    const d = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const count = Math.max(1, Math.ceil(d / STEP_M));
    for (let j = 0; j < count; j++) {
      if (!out.length) out.push([a[0], a[1]]);
      const t = (j + 1) / count;
      out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]);
    }
  }
  return out;
}

/**
 * T-0110 — THE ROAD MUST FOLLOW THE GROUND IT CLAIMS TO LIE ON.
 *
 * The owner reported, walking Kinzie Street onto the North Branch bridge an
 * hour after T-0046 raised its approach earthworks: the track "gets pixely and
 * you can see grass triangles and it ends with a black line and more grass."
 * Replayed against the committed heightfield, the mechanism is not the water
 * trim the ticket first suspected — the trims hold full width up both ramps —
 * it is that a panel was ONE planar quad, 2.25 m long and two vertices wide,
 * and an embankment is not planar. Between the corners the fill's crest rose
 * through the ribbon by up to **1.49 m** (west approach nose; 1.41 m east,
 * 1.09 m at the Dearborn drawbridge approach on North Water). The terrain is
 * opaque and wins the depth test, so everywhere it broke the surface the road
 * simply was not drawn: his green wedges, and his road ending short of the
 * deck. The smoke's `worstDrape` gate never saw it because it samples
 * VERTICES, and every vertex was perfectly draped.
 *
 * The fix is refinement, not flattening: where a panel's own vertices miss the
 * field between themselves by more than DRAPE_TOL_M, the panel subdivides —
 * halving both axes per level — and every new vertex samples
 * `terrain.surfaceHeight()` exactly as the corners always have. The module's
 * standing contract is untouched: the terrain is never edited, the walker
 * still stands on the same heightfield, and a level-0 panel emits byte-for-byte
 * the geometry this function always emitted, so the flat town (94 % of panels)
 * is arithmetically unchanged.
 *
 * Three refusals, all deliberate:
 * - A level is REJECTED if any of its new row centres or vertices lands on
 *   water. The R-BUG4 rule ("clip, don't paint a ford") binds interior
 *   vertices the same as corners, and the smoke's wet-vertex gate counts
 *   positions, not heights.
 * - A panel that touches ground OFF the heightfield grid stays at level 0.
 *   Out there `surfaceHeight()` answers a fallback constant, not a
 *   measurement, and refining against a constant would manufacture cliffs at
 *   the map border.
 * - Interior rows re-run the SAME dryReach trim as panel ends, so the drawn
 *   edge follows the waterline at the refined resolution instead of
 *   interpolating across it.
 *
 * Neighbouring panels can settle on different levels; the shared row's edge
 * vertices coincide exactly (same centreline point, same trim), and any
 * T-junction gap between interior columns is bounded by DRAPE_TOL_M — the
 * coarser panel's own acceptance test ran on that very row.
 */
function refinedPanel(terrain, a, b, ue, un, half, ends, dryReach) {
  const build = (level) => {
    const R = 1 << level;
    const rows = [];
    for (let r = 0; r <= R; r++) {
      const t = r / R;
      const pe = a[0] + (b[0] - a[0]) * t;
      const pn = a[1] + (b[1] - a[1]) * t;
      if (r > 0 && r < R && terrain.isWater(pe, pn)) return null;
      // T-0184. The two END rows are handed in as positions rather than as
      // reaches, because at a bend they are the JOINT's corners and belong to
      // both panels — the same two numbers the neighbouring panel is emitting.
      // Interior rows stand on the chord between them, where the offset is the
      // chord's own normal and this is the arithmetic it always was.
      let left;
      let right;
      if (r === 0) { left = ends.aLeft; right = ends.aRight; } else if (r === R) {
        left = ends.bLeft; right = ends.bRight;
      } else {
        const reachL = dryReach(pe, pn, ue, un, half);
        const reachR = dryReach(pe, pn, -ue, -un, half);
        left = [pe + ue * reachL, pn + un * reachL];
        right = [pe - ue * reachR, pn - un * reachR];
      }
      const row = [];
      for (let c = 0; c <= R; c++) {
        const f = c / R;
        // Rounded to the float32 the position buffer will store, and sampled
        // AT that value: on the ~1:1 ramp flanks the double-precision position
        // and its stored float32 stand on ground ~1e-5 m apart, which is
        // exactly the drape budget the smoke holds vertices to.
        const e = Math.fround(left[0] * (1 - f) + right[0] * f);
        const n = Math.fround(left[1] * (1 - f) + right[1] * f);
        const interior = (r > 0 && r < R) || (c > 0 && c < R);
        if (interior && terrain.isWater(e, n)) return null;
        row.push([e, n, terrain.surfaceHeight(e, n) + LIFT_M]);
      }
      rows.push(row);
    }
    return rows;
  };
  // Worst |field − ribbon| between the grid's own vertices, probed at the
  // half-points of every sub-quad. Off-grid probes are skipped: no measurement,
  // no verdict.
  const residual = (rows) => {
    let worst = 0;
    for (let r = 0; r < rows.length - 1; r++) {
      for (let c = 0; c < rows[r].length - 1; c++) {
        const q = [rows[r][c], rows[r][c + 1], rows[r + 1][c], rows[r + 1][c + 1]];
        for (let i = 0; i <= 2; i++) {
          for (let j = 0; j <= 2; j++) {
            const ft = i / 2;
            const fs = j / 2;
            const e = (q[0][0] * (1 - fs) + q[1][0] * fs) * (1 - ft)
              + (q[2][0] * (1 - fs) + q[3][0] * fs) * ft;
            const n = (q[0][1] * (1 - fs) + q[1][1] * fs) * (1 - ft)
              + (q[2][1] * (1 - fs) + q[3][1] * fs) * ft;
            if (!terrain.inBounds(e, n)) continue;
            const y = (q[0][2] * (1 - fs) + q[1][2] * fs) * (1 - ft)
              + (q[2][2] * (1 - fs) + q[3][2] * fs) * ft;
            worst = Math.max(worst, Math.abs(terrain.surfaceHeight(e, n) + LIFT_M - y));
          }
        }
      }
    }
    return worst;
  };
  let grid = build(0);
  if (grid.some((row) => row.some(([e, n]) => !terrain.inBounds(e, n)))) return grid;
  let level = 0;
  let miss = residual(grid);
  while (miss > DRAPE_TOL_M && level < MAX_DRAPE_LEVEL) {
    const next = build(level + 1);
    if (!next) break;
    grid = next;
    level += 1;
    miss = residual(grid);
  }
  return grid;
}

function rotated(e, n, angle) {
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  return [e * c - n * s, e * s + n * c];
}

/**
 * T-0184. One join per centreline POINT — see the note beside
 * MITRE_MAX_OVERHANG_M for why it exists and why it is capped.
 *
 * `null` means "square to your own chord", which is the rule this module always
 * had and is what every point of a straight street gets. Otherwise a side
 * carries a POSITION both adjacent panels must emit, and `fan` carries the
 * corner patch for a turn too sharp to close in one mitre.
 *
 * `perp` travels with each side because it, not the reach, is what
 * MIN_PANEL_W_M means: a mitred reach is longer than the half-width by
 * construction, and comparing it against a width bar would let a joint keep a
 * panel the waterline had trimmed to a sliver.
 */
function mitreJoins(pts, half, dryReach, stats) {
  const joins = pts.map(() => null);
  // The largest turn one mitre may close without standing further than
  // MITRE_MAX_OVERHANG_M past the bend.
  const maxStep = Math.acos(half / (half + MITRE_MAX_OVERHANG_M));
  for (let p = 1; p < pts.length - 1; p++) {
    const A = pts[p - 1];
    const P = pts[p];
    const B = pts[p + 1];
    const d1e = P[0] - A[0];
    const d1n = P[1] - A[1];
    const d2e = B[0] - P[0];
    const d2n = B[1] - P[1];
    const l1 = Math.hypot(d1e, d1n);
    const l2 = Math.hypot(d2e, d2n);
    if (l1 < 1e-5 || l2 < 1e-5) continue;
    let turn = Math.atan2(d2n, d2e) - Math.atan2(d1n, d1e);
    if (turn > Math.PI) turn -= 2 * Math.PI;
    if (turn < -Math.PI) turn += 2 * Math.PI;
    if (Math.abs(turn) < MITRE_MIN_TURN_RAD) continue;
    stats.joints += 1;
    if (Math.abs(turn) > MITRE_MAX_TURN_RAD) { stats.squareJoints += 1; continue; }
    const u1e = -d1n / l1;
    const u1n = d1e / l1;
    const halfTurn = turn * 0.5;
    const cosHalf = Math.cos(halfTurn);
    const mitre = half / cosHalf;
    const k = Math.max(1, Math.ceil(Math.abs(halfTurn) / maxStep));
    // Which side is the INSIDE of the turn: left when the line turns left.
    const bis = rotated(u1e, u1n, halfTurn);
    const sgn = turn > 0 ? 1 : -1;
    const inSide = turn > 0 ? 'L' : 'R';
    const cornerAlong = (de, dn, max) => {
      const reach = dryReach(P[0], P[1], de, dn, max);
      return {
        e: P[0] + de * reach,
        n: P[1] + dn * reach,
        perp: reach * cosHalf,
        trimmed: reach < max - 1e-9,
      };
    };
    const join = { turn, k, L: null, R: null, fan: null };
    join[inSide] = cornerAlong(bis[0] * sgn, bis[1] * sgn, mitre);
    if (k === 1) {
      join[inSide === 'L' ? 'R' : 'L'] = cornerAlong(-bis[0] * sgn, -bis[1] * sgn, mitre);
      stats.mitredJoints += 1;
    } else {
      // The outside stays square to each chord and a fan of tangent segments
      // bridges the two corners. Its first and last vertices ARE those corners,
      // so the patch meets the panels exactly; the ones between are where
      // consecutive tangents to the half-width circle intersect.
      const outer = [];
      const at = (angle, radius) => {
        const v = rotated(u1e, u1n, angle);
        outer.push([P[0] - sgn * v[0] * radius, P[1] - sgn * v[1] * radius]);
      };
      const stepMitre = half / Math.cos(halfTurn / k);
      at(0, half);
      for (let j = 1; j <= k; j += 1) at(((2 * j - 1) * turn) / (2 * k), stepMitre);
      at(turn, half);
      join.fan = { apex: join[inSide], outer, apexSide: inSide };
      stats.fannedJoints += 1;
    }
    joins[p] = join;
  }
  return joins;
}

function addRecord(buffers, record, terrain, stats) {
  const key = record.surface;
  const buf = buffers.get(key) ?? { pos: [], uv: [], conf: [], track: [], idx: [] };
  buffers.set(key, buf);
  // T-0111. The ribbon is painted on the WHEEL line; every other question this
  // module answers is asked of the platted one. `drawn` is `path` for all but
  // the one street that authors a separate track, so this is the same call it
  // has always been everywhere else.
  const pts = sampled(record.drawn);
  const half = record.track_width_m * 0.5;
  // Distance along the ribbon at each centreline point, accumulated exactly as
  // the panel loop always accumulated it — degenerate chords add nothing — so
  // the texture's `v` is untouched. A joint fan needs to read it at a point
  // rather than only during the panel that reaches it.
  const alongAt = [0];
  for (let i = 1; i < pts.length; i += 1) {
    const step = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    alongAt.push(alongAt[i - 1] + (step < 1e-5 ? 0 : step));
  }
  // WHICH GRADE DECIDES WHAT, and it is two questions rather than one. T-0100
  // put `geometry_confidence` into the ribbon's grade because a route nobody
  // attested puts the visitor in an invented PLACE, not merely on an invented
  // surface; it did so by taking the weakest of all three, which answered the
  // fault but flattened the distinction. T-0713 separates them:
  //
  //   the LINE decides whether the ribbon STANDS — presence, dither, and which
  //   level hides it — because that is the claim "a street ran here", and it is
  //   the only one of the three the visitor's own position depends on;
  //
  //   SURFACE and WEAR decide only the TRACK painted on it — the rut texture
  //   and how firmly it reads — because they are claims about what the street
  //   looked like, not about whether it was there.
  //
  // The guard the old expression existed for is kept exactly: an invented line
  // under an attested surface still dithers out, because the line alone now
  // decides that, and a record with NO geometry grade still falls to
  // `reconstructed` rather than reading as attested. What changes is the
  // converse case the max() could not express — an ATTESTED line carrying an
  // invented wear used to dither away entirely, which told the visitor the
  // street was not there when what we do not know is how worn it was.
  //
  // This stopped being theoretical on 2026-09-04: T-0713 graded the seventeen
  // platted streets `attested` from the Thompson plat while every record in the
  // file still carries `wear_confidence: reconstructed`, so under the old max()
  // the whole platted town would have gone on dithering as invention. The layer
  // is no longer degenerate and `tools/test_street_confidence.mjs` measures it.
  const confidence = LEVEL[record.geometry_confidence] ?? 1;
  // The track's own grade, carried to the shader on its own channel so it can
  // fade the worn texture WITHOUT touching whether the ribbon is drawn. See
  // meshOf(): it is read only while the confidence view is on, so the ordinary
  // daylight frame is the frame that shipped before this.
  const trackConfidence = Math.max(
    LEVEL[record.surface_confidence] ?? 1,
    LEVEL[record.wear_confidence] ?? 1,
  );

  // But the EDGE test used to drop a panel too, and that was the wrong
  // instrument for the right aim. Its comment said it kept a bank road from
  // painting over water just because its legal corridor reached it — true, and
  // the remedy for "do not paint over water" is to CLIP the panel at the
  // waterline, not to delete it, because deleting takes the DRY HALF with it.
  // Owner-reported from South Water Street as a clean-edged green hole
  // punched through the roadway; replayed against the shipped mask it was
  // 13 panels and ~30 m of roadway removed while the centreline was dry land
  // a visitor can stand on, and 14.2 % of Kinzie Street.
  //
  // So each end is trimmed on each side INDEPENDENTLY: walk out from the dry
  // centreline to the recorded half-width and keep the furthest dry reach.
  // Asymmetric on purpose — a bank road is wet on one side only, and
  // shrinking it symmetrically would throw away the dry verge as well.
  //
  // T-0184 gave it a ceiling argument instead of closing over `half`, because a
  // mitred corner walks a longer half-width — `half / cos(turn/2)` — along the
  // bisector. At `max === half` this is the function it always was.
  const dryReach = (e0, n0, se, sn, max) => {
    if (!terrain.isWater(e0 + se * max, n0 + sn * max)) return max;
    let lo = 0;
    let hi = max;
    for (let k = 0; k < CLIP_STEPS; k++) {
      const mid = (lo + hi) * 0.5;
      if (terrain.isWater(e0 + se * mid, n0 + sn * mid)) hi = mid;
      else lo = mid;
    }
    return lo;
  };
  const joins = mitreJoins(pts, half, dryReach, stats);
  // A joint's fan may only be drawn between two panels that were both drawn and
  // whose outer corners were not trimmed back by the waterline — otherwise it
  // would bridge to an edge that is not there.
  const panelDrawn = pts.map(() => false);
  const fanBlocked = pts.map(() => false);

  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1];
    const b = pts[i];
    const de = b[0] - a[0];
    const dn = b[1] - a[1];
    const length = Math.hypot(de, dn);
    if (length < 1e-5) continue;
    const along = alongAt[i - 1];
    const ue = -dn / length;
    const un = de / length;

    // R-BUG4. The CENTRELINE test still drops the panel: a road whose centre is
    // in the river is a crossing, and a crossing is a bridge's job, not a
    // ribbon's.
    if (terrain.isWater(a[0], a[1]) || terrain.isWater(b[0], b[1])) continue;
    // T-0184. A side the join owns is a POSITION, identical in both panels that
    // meet there; a side it does not is square to this panel's own chord, which
    // is every side of every straight panel.
    const cornerOf = (P, join, side) => {
      const owned = join && join[side];
      if (owned) return owned;
      const se = side === 'L' ? ue : -ue;
      const sn = side === 'L' ? un : -un;
      const reach = dryReach(P[0], P[1], se, sn, half);
      return { e: P[0] + se * reach, n: P[1] + sn * reach, perp: reach,
        trimmed: reach < half - 1e-9 };
    };
    const aLeft = cornerOf(a, joins[i - 1], 'L');
    const aRight = cornerOf(a, joins[i - 1], 'R');
    const bLeft = cornerOf(b, joins[i], 'L');
    const bRight = cornerOf(b, joins[i], 'R');
    // A panel trimmed to nothing is a panel whose centreline is dry by a hair
    // and whose surroundings are not. Drawing a sliver there would be a claim
    // about a road too narrow to walk on, so it is dropped and counted. Read on
    // the PERPENDICULAR half-widths, which is what the bar has always meant.
    if (aLeft.perp + aRight.perp < MIN_PANEL_W_M
      || bLeft.perp + bRight.perp < MIN_PANEL_W_M) continue;
    for (const [p, join, ends] of [[i - 1, joins[i - 1], [aLeft, aRight]],
      [i, joins[i], [bLeft, bRight]]]) {
      if (!join?.fan) continue;
      const outerEnd = join.fan.apexSide === 'L' ? ends[1] : ends[0];
      if (outerEnd.trimmed) fanBlocked[p] = true;
    }
    // T-0110: a grid of (level+1)² draped vertices — one quad at level 0,
    // which is this function's historical output exactly.
    const grid = refinedPanel(terrain, a, b, ue, un, half, {
      aLeft: [aLeft.e, aLeft.n],
      aRight: [aRight.e, aRight.n],
      bLeft: [bLeft.e, bLeft.n],
      bRight: [bRight.e, bRight.n],
    }, dryReach);
    const rows = grid.length - 1;
    const cols = grid[0].length - 1;
    const base = buf.pos.length / 3;
    for (let r = 0; r <= rows; r++) {
      // Across first, distance along second. The texture repeats every eight
      // metres, long enough that its ruts read as travel rather than corduroy.
      const v = (along + (length * r) / rows) / 8;
      for (let c = 0; c <= cols; c++) {
        const [e, n, y] = grid[r][c];
        buf.pos.push(e, y, -n);
        buf.conf.push(confidence);
        buf.track.push(trackConfidence);
        buf.uv.push(c / cols, v);
      }
    }
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const i00 = base + r * (cols + 1) + c;
        const i10 = i00 + cols + 1;
        buf.idx.push(i00, i10, i00 + 1, i00 + 1, i10, i10 + 1);
      }
    }
    stats.panels += 1;
    if (rows > 1) stats.refinedPanels += 1;
    panelDrawn[i] = true;
  }

  // T-0184. The corner patch, emitted after the panels because it needs both of
  // its neighbours to exist. R-BUG4's rule binds it exactly as it binds a panel
  // vertex: a fan with any corner on water is not drawn, because a ford is not
  // a thing this module may paint.
  for (let p = 1; p < pts.length - 1; p++) {
    const join = joins[p];
    if (!join?.fan || fanBlocked[p] || !panelDrawn[p] || !panelDrawn[p + 1]) continue;
    const { apex, outer, apexSide } = join.fan;
    if (terrain.isWater(apex.e, apex.n)) continue;
    if (outer.some(([e, n]) => terrain.isWater(e, n))) continue;
    const base = buf.pos.length / 3;
    const v = alongAt[p] / 8;
    const push = (pe, pn, u) => {
      const e = Math.fround(pe);
      const n = Math.fround(pn);
      buf.pos.push(e, terrain.surfaceHeight(e, n) + LIFT_M, -n);
      buf.conf.push(confidence);
      buf.track.push(trackConfidence);
      buf.uv.push(u, v);
    };
    // `u` runs 0 at the left edge to 1 at the right, as it does across a panel,
    // so the surface's own edge fade lands on the fan's outer rim too.
    push(apex.e, apex.n, apexSide === 'L' ? 0 : 1);
    for (const [e, n] of outer) push(e, n, apexSide === 'L' ? 1 : 0);
    for (let t = 0; t < outer.length - 1; t++) {
      buf.idx.push(base, base + 1 + t, base + 2 + t);
    }
    stats.jointFans += 1;
    stats.jointFanTriangles += outer.length - 1;
  }
}

function hash(x, y) {
  let h = Math.imul(x + 17, 374761393) ^ Math.imul(y + 31, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
}

function roadTexture(surface) {
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  const image = ctx.createImageData(canvas.width, canvas.height);
  const graded = surface === 'graded_earth';
  const light = surface === 'light_worn_earth';
  const base = graded ? [113, 91, 55] : light ? [102, 85, 55] : [106, 84, 50];
  for (let y = 0; y < canvas.height; y++) {
    for (let x = 0; x < canvas.width; x++) {
      const q = x / (canvas.width - 1);
      const edge = Math.min(1, Math.max(0, Math.min(q, 1 - q) / 0.12));
      const ruts = Math.exp(-(((q - 0.29) / 0.065) ** 2))
        + Math.exp(-(((q - 0.71) / 0.065) ** 2));
      const crown = Math.exp(-(((q - 0.5) / 0.13) ** 2));
      const grain = (hash(x >> 1, y >> 1) - 0.5) * 18
        + (hash(x >> 3, y >> 3) - 0.5) * 11;
      const wet = ruts * (graded ? 13 : 18);
      const i = (y * canvas.width + x) * 4;
      image.data[i] = Math.max(0, Math.min(255, base[0] + grain - wet));
      image.data[i + 1] = Math.max(0, Math.min(255, base[1] + grain * 0.74 - wet));
      image.data[i + 2] = Math.max(0, Math.min(255, base[2] + grain * 0.48 - wet * 0.58));
      // Baselines raised for R-BUG2 fault 2 — see the note at the top of the
      // file. The modulation shape (ruts up, crown down) and the graded > worn
      // > light ordering are unchanged; only the floor each surface starts
      // from moved, from 0.54/0.20/0.08 to 0.54/0.38/0.28. The faintest
      // surface now bottoms out at 0.24 rather than 0.04.
      const body = graded
        ? 0.54 + ruts * 0.25 - crown * 0.08
        : light ? 0.28 + ruts * 0.54 - crown * 0.04
          : 0.38 + ruts * 0.55 - crown * 0.08;
      image.data[i + 3] = Math.round(255 * edge * Math.max(0, Math.min(MAX_ALPHA, body)));
    }
  }
  ctx.putImageData(image, 0, 0);
  const texture = new THREE.CanvasTexture(canvas);
  texture.name = `street-${surface}`;
  texture.wrapS = THREE.ClampToEdgeWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.magFilter = THREE.LinearFilter;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.anisotropy = 4;
  return texture;
}

function meshOf(surface, buf, confidence, aidUniform) {
  if (!buf.idx.length) return null;
  const geo = new THREE.BufferGeometry();
  geo.name = `streets-${surface}`;
  geo.setAttribute('position', new THREE.Float32BufferAttribute(buf.pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(buf.uv, 2));
  geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(buf.conf, 1));
  // T-0713. A SECOND channel, not a second meaning for the first one. `_confidence`
  // is the contract's channel and the confidence view reads it to decide what stands;
  // this one carries the surface-and-wear grade and is read nowhere but the block
  // below, which paints the track rather than deciding the road.
  geo.setAttribute('_trackConfidence',
    new THREE.Float32BufferAttribute(buf.track, 1));
  geo.setIndex(buf.idx);
  geo.computeVertexNormals();
  const map = roadTexture(surface);
  const mat = new THREE.MeshStandardMaterial({
    map,
    transparent: true,
    alphaTest: 0.025,
    depthWrite: false,
    roughness: 1,
    metalness: 0,
    side: THREE.DoubleSide,
    polygonOffset: true,
    // R-BUG2 fault 1. -1/-1 is a fraction of a depth unit and the terrain won
    // the test in patches beyond ~250 m. Deep enough to hold at the far end of
    // the town, shallow enough that the ribbon never lifts off its own drape —
    // the vertices are untouched, and `worstDrape` still gates them.
    // R-BUG3 deepened it again, and the reason it had to is the same reason
    // R-BUG2's number was too shallow: it was tuned until the bands AT THE TWO
    // STATIONS THEN GATED passed. Standing on Lake Street at Market, desktop,
    // 100-250 m, the ribbon lost the test again — 23 probes where the marker
    // pass is frontmost and the road changes the picture by 0.0 L\*, opaque or
    // not, which is a depth fight and nothing else. These are the marker's own
    // values, so "the road's surface is the frontmost thing here" and "the road
    // is drawn here" now mean the same thing rather than differing by a tuning
    // constant. The vertices are still untouched and `worstDrape` still gates
    // them to 1e-5 m.
    polygonOffsetFactor: -8,
    polygonOffsetUnits: -32,
  });
  mat.name = `street-${surface}`;
  // R-BUG2 floor. `u` runs 0 -> 1 exactly across the track, so 1/fwidth(u) IS
  // the ribbon's width in screen pixels — no uniform, no viewport to keep in
  // sync, and correct under any field of view. Set BEFORE confidence.patch(),
  // which chains whatever it finds here rather than replacing it.
  // T-0713. `uConfMode` and the varying below only exist once confidence.patch()
  // has run, and it is optional — createStreets({ confidence: null }) is a
  // supported call. So the track-grade block is COMPILED IN only when the view
  // is there to switch it on; without it this is the shader that shipped before.
  const graded = Boolean(confidence);
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uRoadAid = aidUniform;
    if (graded) {
      shader.vertexShader = `attribute float _trackConfidence;
varying float vTrackConfidence;
${shader.vertexShader}`.replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>
  // Sanitised at source for the reason confidence.js states at length: an
  // unbound attribute is not reliably zero and can arrive as NaN. The fallback
  // is 1.0 — the INVENTED end — because a track whose grade did not reach the
  // shader must not read as one somebody wrote down.
  float chicagoT = _trackConfidence;
  vTrackConfidence = (chicagoT == chicagoT) ? clamp(chicagoT, 0.0, 1.0) : 1.0;`,
      );
    }
    shader.fragmentShader = `uniform float uRoadAid;
${graded ? 'varying float vTrackConfidence;\n' : ''}${shader.fragmentShader}`.replace(
      '#include <map_fragment>',
      `#include <map_fragment>
      {
        float trackPx = 1.0 / max(fwidth(vMapUv.x), 1e-6);
        float thin = clamp(${MIN_TRACK_PX.toFixed(1)} / trackPx, 1.0, ${MAX_THIN_BOOST.toFixed(1)});
        diffuseColor.a = min(diffuseColor.a * thin, ${MAX_ALPHA.toFixed(2)});
        // R-BUG3. Distance from the eye, not a pixel count: the band this
        // answers is metres from the walker and must not mean something
        // different at 390 px than at 1280.
        float eyeM = length(vViewPosition);
        float near = 1.0 - smoothstep(${NEAR_FULL_M.toFixed(1)}, ${NEAR_FADE_M.toFixed(1)}, eyeM);
        // T-0114. The middle of the road, which had neither remedy. max(), not a
        // product: the ramps overlap under 40 m and multiplying would stack to
        // 4.1x there, re-breaking the near field R-BUG3 tuned.
        float mid = 1.0 - smoothstep(${MID_FULL_M.toFixed(1)}, ${MID_FADE_M.toFixed(1)}, eyeM);
        float gain = max(mix(1.0, ${NEAR_GAIN.toFixed(2)}, near),
                         mix(1.0, ${MID_GAIN.toFixed(2)}, mid));
        diffuseColor.a = min(diffuseColor.a * gain, ${MAX_ALPHA.toFixed(2)});
        ${graded ? `
        // T-0713. THE TRACK'S OWN GRADE, and it goes no further than the track.
        // Whether this ribbon is drawn at all was decided by \`_confidence\`,
        // which now carries the LINE's grade alone; what the surface and wear
        // records are worth is a different claim and it is answered here, by
        // fading the worn texture toward the bare corridor in proportion to how
        // invented it is. Only while the view is on: at uConfMode == 0 this is
        // mix(1.0, X, 0.0) == 1.0 and multiplies nothing.
        diffuseColor.a *= mix(1.0, ${INVENTED_TRACK_ALPHA.toFixed(2)},
                              vTrackConfidence * uConfMode);` : ''}
        // R-A1, and it is LAST on purpose: the aid scales whatever the
        // recorded surface and the two fixes above arrived at, so it can never
        // change which road is fainter than which. At uRoadAid == 0 this is
        // min(a * 1.0, ${MAX_ALPHA.toFixed(2)}) — the clamp the block above
        // arrived at, re-applied — so the default frame is the frame that
        // shipped before the control existed.
        diffuseColor.a = min(
          diffuseColor.a * mix(1.0, ${AID_GAIN.toFixed(4)}, uRoadAid),
          mix(${MAX_ALPHA.toFixed(2)}, 1.0, uRoadAid));
      }`,
    );
  };
  confidence?.patch(mat);
  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = `streets-${surface}`;
  mesh.receiveShadow = true;
  mesh.castShadow = false;
  mesh.renderOrder = 0;
  return { mesh, geo, mat, map };
}

export function createStreets({ terrain, records = [], confidence = null } = {}) {
  const group = new THREE.Group();
  group.name = 'streets';
  // A PLATTED BUT UNOPENED STREET DRAWS NOTHING. The twelve east-west lines Wright
  // rules across the School Section are survey lines over prairie, not roads: they
  // compile with `opened: false` and `track_width_m: 0`, and there is no worn strip
  // to paint. Excluded here rather than downstream so they also take no part in
  // `blocksGrowth` — the flora belts keep their timber across the grid, which is the
  // owner's own reading of the sheet (T-0797).
  const prepared = records.filter((r) => Array.isArray(r.path_local_enu_m)
      && r.path_local_enu_m.length >= 2
      && r.opened !== false && (r.track_width_m ?? 6) > 0).map(prepare);
  const buffers = new Map();
  // T-0110. With refinement a panel is no longer a fixed six indices, so the
  // smoke's panel-accounting gate reads these counters instead of index math.
  // T-0184 adds the joint counters. `squareJoints` is the one that matters: it
  // is the number of bends this module gave up on, and a gate that only ever
  // read `mitredJoints` could not tell a closed town from one where every turn
  // had quietly fallen through the guard.
  const stats = {
    panels: 0, refinedPanels: 0,
    joints: 0, mitredJoints: 0, fannedJoints: 0, squareJoints: 0,
    jointFans: 0, jointFanTriangles: 0,
  };
  for (const record of prepared) addRecord(buffers, record, terrain, stats);
  const resources = [];
  // R-A1. One uniform object shared by every surface's material, so the aid
  // cannot end up applied to the graded tracks and not the worn ones.
  const aidUniform = { value: 0 };
  for (const [surface, buf] of buffers) {
    const built = meshOf(surface, buf, confidence, aidUniform);
    if (!built) continue;
    group.add(built.mesh);
    resources.push(built);
  }

  function hitsAt(e, n, widthKey = 'corridor_width_m') {
    const hits = [];
    for (const street of prepared) {
      const hit = nearestOn(street, e, n);
      if (hit && hit.distance <= street[widthKey] * 0.5) hits.push(hit);
    }
    hits.sort((a, b) => a.distance - b.distance);
    return hits;
  }

  function ahead(e, n, bearingDeg, excluded = new Set()) {
    const th = bearingDeg * Math.PI / 180;
    const de = Math.sin(th);
    const dn = Math.cos(th);
    for (let d = 5; d <= 70; d += 2.5) {
      const pe = e + de * d;
      const pn = n + dn * d;
      const hits = hitsAt(pe, pn).filter((h) => !excluded.has(h.street.id));
      if (hits.length) return { ...hits[0], ahead_m: d };
    }
    return null;
  }

  function status(e, n, bearingDeg = 0) {
    const on = hitsAt(e, n);
    // At a crossing, report only streets whose travelled/platted centre is
    // genuinely near the visitor.  This prevents two broad 80-ft corridors
    // from being called an intersection near a far corner of the overlap.
    const crossing = on.filter((h) => h.distance <= Math.min(8, h.street.corridor_width_m * 0.5));
    if (crossing.length >= 2) {
      return { mode: 'intersection', streets: crossing.slice(0, 2).map((h) => h.street) };
    }
    if (on.length) {
      const current = on[0].street;
      const upcoming = ahead(e, n, bearingDeg, new Set([current.id]));
      return { mode: 'on', streets: [current], upcoming };
    }
    const coming = ahead(e, n, bearingDeg);
    return coming
      ? { mode: 'ahead', streets: [coming.street], distance_m: coming.ahead_m }
      : null;
  }

  function blocksGrowth(e, n) {
    // A small shoulder clears roots/blades off the visibly worn track while
    // preserving the grassy remainder of the 80-foot corridor.
    for (const street of prepared) {
      const hit = nearestOn(street, e, n);
      if (hit && hit.distance <= street.track_width_m * 0.5 + 0.65) return true;
    }
    return false;
  }

  return {
    group,
    records: prepared,
    stats,
    status,
    hitsAt,
    blocksGrowth,
    /**
     * R-A1. The road-legibility aid, 0 (off, the default) to 1 (the faintest
     * surface opaque). A uniform, so it costs no recompile and takes effect on
     * the next frame; the gates read `legibilityAid` to prove it is 0 when
     * nobody has touched it.
     */
    setLegibilityAid(v) {
      const next = Math.max(0, Math.min(1, Number(v) || 0));
      aidUniform.value = next;
      return next;
    },
    get legibilityAid() { return aidUniform.value; },
    dispose() {
      for (const r of resources) {
        r.geo.dispose();
        r.mat.dispose();
        r.map.dispose();
      }
    },
  };
}
