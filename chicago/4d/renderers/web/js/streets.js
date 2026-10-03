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
 * T-1811 adds a third, derived here and nowhere else: `drawn_width_m`, the
 * worked earth a frontier street actually was — packed full-width by wheels,
 * hooves and feet, thinning to grass at its shoulders — sized by the street's
 * traffic class from the corridor (see WORKED_SHARE). The recorded track keeps
 * its meaning as the opaque core; the generators that keep things out of the
 * travelled way still read `track_width_m` and nothing moved for them.
 *
 * The second is a stated visual liberty.  It is not allowed to flatten the
 * terrain or author a second collision surface: every ribbon vertex samples
 * terrain.surfaceHeight(), and the walker continues to stand on that exact same
 * heightfield.  Segments whose centres or edges are under water are omitted,
 * leaving honest gaps at unbridged channels rather than painting a ford.
 */

import * as THREE from 'three';
import { GRIT_TILE_PX, GRIT_TILE_M, gritTilePixels } from './ground-strip-mask.js';

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
// T-1811. Was 0.92: a translucent ribbon could never quite cover the prairie,
// and the 8 % of grass it let through is what read as a grassy median between
// two treads. The roadbed is now opaque earth where it is worked and gives way
// to grass by COVERAGE (clumps, shoulders), not by a ceiling on every pixel.
const MAX_ALPHA = 1.0;
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
// T-1811 kept the gain: it still lifts every partly-covered shoulder pixel.
const AID_GAIN = 1 / 0.24;
// T-1811. How far the aid lifts the opaque dirt's lightness at full strength.
const AID_LIFT = 0.25;

/**
 * T-1811 — THE WORKED ROADWAY, and why it is wider than the track.
 *
 * The owner, 2026-09-30: replace "the paired-tread appearance with a full dirt
 * roadway". `roadTexture` used to draw exactly that pair — two Gaussian ruts at
 * 0.29 and 0.71 of the track over a 0.28-0.93 alpha body — so every street read
 * as two brown lines on grass. A town street in a wet frontier summer was worn
 * across most of its width by wagons pulling out to pass, teams standing at
 * doors, droves and foot traffic; the peer-city views the owner supplied (St
 * Louis 1840, Detroit 1837, Cincinnati 1835) all show one broad worked plane
 * with no grass median. None of them is Chicago and none gives a width, so the
 * width is a RECONSTRUCTION (L327), bounded on both sides:
 *
 *   - never narrower than the recorded `track_width_m`, which stays the opaque
 *     core it always claimed to be;
 *   - never past the frontage: the 80 ft corridor less a walk (1.83 m) and its
 *     0.2 m clearance each side leaves 20.3 m, so principal streets stop short
 *     of the walks at 0.80 of the corridor (19.5 m) and lighter streets well
 *     inside it, by traffic class.
 *
 * WEAR_INTENSITY is how much of the core is bare. A principal street is bare
 * end to end; a `light` street keeps grass between irregular lanes — the
 * "sparse peripheral tracks" the ticket allows where use supports nothing more.
 * CORE_SHARE_FLOOR keeps the opaque core at least half the worked width, so the
 * shoulders never outgrow the road they belong to.
 */
export const WORKED_SHARE = { principal: 0.80, ordinary: 0.64, light: 0.44 };
// The shoulders past the recorded track stop where the ground falls away from
// the crown by more than this. A bridge approach fill is a causeway one track
// wide, and a worked shoulder draped down its flanks put the fill's crest
// through the ribbon by 0.58 m between vertices (Kinzie's approaches, Dearborn's
// drawbridge fill). Read in 0.5 m steps outward from the track's edge.
const SHOULDER_DROP_M = 0.35;
const SHOULDER_STEP_M = 0.5;
const WEAR_INTENSITY = { principal: 1.0, ordinary: 0.9, light: 0.68 };
const CORE_SHARE_FLOOR = 0.5;
/**
 * The dirt's tones, sRGB: dry July dust over packed earth, bounded by two
 * committed readings — T-1797's proof pair (lane 126,112,91 / between 96,86,69)
 * below, and the grey sand the same strip drew (136,128,106) above, since a
 * street's dust is the finer, drier and lighter fraction of what it is made of.
 * The smoke chose WHERE inside that bound, and it is worth recording how. The
 * road-legibility gate reads luminance, not hue: T-1797's pair as it stood drew
 * the road 7 L* LIGHTER than the grass at the walker's eye but only 2 L* apart
 * from the air, where the prairie reads brighter; a step darker made the air
 * pass and took the walker's eye to 2 L*. So the road sits at the bound's top,
 * lighter than the grass from both — which is also what the owner's peer views
 * show of a summer street. `graded_earth` is the dustiest (thrown up and
 * drained), the light streets a shade darker. Mud sits inside
 * `wet_prairie_muck`'s measured basecolor (L 47 of 255); the shoulder sod is
 * dirt carrying root and leaf. Reconstructed, all of it (L327).
 */
export const DIRT_TONES = {
  graded_earth: { lane: [146, 131, 107], rest: [117, 105, 84] },
  worn_earth: { lane: [142, 128, 104], rest: [113, 101, 81] },
  light_worn_earth: { lane: [137, 123, 100], rest: [108, 97, 78] },
};
const MUD_TONE = [64, 56, 44];
const SOD_TONE = [98, 92, 68];

function trafficOf(raw) {
  return WORKED_SHARE[raw.traffic] ? raw.traffic : 'light';
}

function seedOf(id) {
  let h = 2166136261;
  for (const ch of String(id ?? '')) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return ((h >>> 0) % 997) / 997;
}

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
  // T-1811. The worked width, derived — see WORKED_SHARE.
  const corridor = raw.corridor_width_m ?? 24.384;
  const track = raw.track_width_m ?? 6;
  const traffic = trafficOf(raw);
  const drawnWidth = Math.max(track, WORKED_SHARE[traffic] * corridor);
  return {
    ...raw,
    path,
    drawn,
    corridor_width_m: corridor,
    track_width_m: track,
    drawn_width_m: drawnWidth,
    core_share: Math.min(1, Math.max(track / drawnWidth, CORE_SHARE_FLOOR)),
    wear_intensity: WEAR_INTENSITY[traffic],
    wear_seed: seedOf(raw.id),
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

/**
 * T-1987 — WHERE A STREET ENDS ON ANOTHER, ITS END IS FADED INTO IT.
 *
 * Market runs into Lake, Franklin, Wells, La Salle and Clark into South Water,
 * every north-side street into North Water and Kinzie. Each ribbon stopped on a
 * straight line laid across the through street's dirt, its own ruts and lanes
 * running square into the other's, and the two transparent surfaces blended in
 * whatever order they were drawn: a hard seam across the junction, seen from
 * any height (owner, 2026-10-02, "misjoined roads").
 *
 * The ending street keeps its full cover until it is inside the through
 * street's opaque core, then fades out by the through street's centreline (or
 * by its own end, if that is short of it). Only a street that ends INSIDE
 * another's worked width, on a stretch of it that runs on, is faded — two
 * streets that both end at a corner keep both their ends, or the corner would
 * open. Read off the drawn lines, in metres along the ending ribbon, so the
 * shader needs one attribute and no lookups.
 */
const END_FADE_MIN_M = 1.5;
// "No fade" is a ramp that lies off the ribbon at both ends, a metre or two
// past it, never a far sentinel: the four numbers are interpolated across
// every triangle, and at 1e7 m one float step is a whole metre, so a ramp's
// two ends met or swapped in places and smoothstep() — undefined there —
// struck the road out in scanline stripes.
const NO_FADE = [-2, -1, 1e5, 2e5];
function endFades(records) {
  const length = (pts) => {
    let sum = 0;
    for (let i = 1; i < pts.length; i++) {
      const step = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      sum += step < 1e-5 ? 0 : step;
    }
    return sum;
  };
  const fades = new Map();
  for (const record of records) {
    const L = length(record.drawn);
    const fade = [-2, -1, L + 1, L + 2];
    const ends = [
      [record.drawn[0], record.drawn[1], 0],
      [record.drawn.at(-1), record.drawn.at(-2), 2],
    ];
    for (const [P, Q, slot] of ends) {
      const de = P[0] - Q[0];
      const dn = P[1] - Q[1];
      const dl = Math.hypot(de, dn);
      if (dl < 1e-6) continue;
      let best = null;
      for (const other of records) {
        if (other === record) continue;
        const oHalf = other.drawn_width_m * 0.5;
        const oLen = length(other.drawn);
        let walked = 0;
        for (let i = 1; i < other.drawn.length; i++) {
          const a = other.drawn[i - 1];
          const b = other.drawn[i];
          const hit = pointSegment(P[0], P[1], a, b);
          const seg = Math.hypot(b[0] - a[0], b[1] - a[1]);
          const at = walked + seg * hit.t;
          walked += seg < 1e-5 ? 0 : seg;
          if (hit.distance >= oHalf || (best && hit.distance >= best.distance)) continue;
          // A corner, not a T: the other street ends here too.
          if (at < oHalf || at > oLen - oHalf) continue;
          const beyond = ((P[0] - hit.e) * de + (P[1] - hit.n) * dn) / dl;
          best = { distance: hit.distance, beyond, core: oHalf * other.core_share };
        }
      }
      if (!best) continue;
      const zero = Math.max(0, best.beyond);
      const full = best.beyond + best.core;
      if (full - zero < END_FADE_MIN_M || full > L * 0.5) continue;
      if (slot === 0) { fade[0] = zero; fade[1] = full; } else {
        fade[2] = L - full;
        fade[3] = L - zero;
      }
    }
    fades.set(record, fade);
  }
  return fades;
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
// The float32 one step from `x` in the direction of `dir`'s sign.
function stepF32(x, dir) {
  if (dir === 0) return x;
  const ulp = 2 ** (Math.floor(Math.log2(Math.max(Math.abs(x), 2 ** -100))) - 23);
  return Math.fround(x + Math.sign(dir) * ulp);
}

/**
 * T-1812. Move a float32 vertex of a panel's end row onto, or just outside,
 * the straight line between that row's two (float32) corners, where "outside"
 * is the side the panel's far end `away` is not on. A neighbouring panel with
 * fewer columns draws exactly that line as its edge; a vertex left inside it
 * would open a sliver of bare ground between the two.
 */
function ontoEndLine(e, n, left, right, near, away) {
  const le = Math.fround(left[0]);
  const ln = Math.fround(left[1]);
  const de = Math.fround(right[0]) - le;
  const dn = Math.fround(right[1]) - ln;
  const side = (pe, pn) => de * (pn - ln) - dn * (pe - le);
  const inward = Math.sign(side(away[0], away[1]));
  const oe = near[0] - away[0];
  const on = near[1] - away[1];
  for (let k = 0; k < 8 && inward !== 0 && side(e, n) * inward > 0; k++) {
    e = stepF32(e, oe);
    n = stepF32(n, on);
  }
  return [e, n];
}

/**
 * T-1812. Where the line across a panel's middle crosses the terrain's sample
 * lattice, as fractions 0..1 from its left edge to its right — the only places
 * the bilinear ground can bend along that line. Crossings nearer than
 * LATTICE_MIN_GAP to each other or to an edge are merged, so no column is a
 * sliver.
 */
const LATTICE_MIN_GAP = 0.04;
function latticeFractions(grid, ends) {
  if (!grid || !(grid.cellM > 0)) return [0, 1];
  const le = (ends.aLeft[0] + ends.bLeft[0]) * 0.5;
  const ln = (ends.aLeft[1] + ends.bLeft[1]) * 0.5;
  const de = (ends.aRight[0] + ends.bRight[0]) * 0.5 - le;
  const dn = (ends.aRight[1] + ends.bRight[1]) * 0.5 - ln;
  const cuts = [];
  for (const [p, d, o] of [[le, de, grid.originE], [ln, dn, grid.originN]]) {
    if (Math.abs(d) < 1e-9) continue;
    const g0 = (p - o) / grid.cellM;
    const g1 = (p + d - o) / grid.cellM;
    for (let k = Math.ceil(Math.min(g0, g1)); k <= Math.floor(Math.max(g0, g1)); k++) {
      cuts.push((k - g0) / (g1 - g0));
    }
  }
  cuts.sort((x, y) => x - y);
  const out = [0];
  for (const f of cuts) {
    if (f - out[out.length - 1] >= LATTICE_MIN_GAP && 1 - f >= LATTICE_MIN_GAP) out.push(f);
  }
  out.push(1);
  return out;
}

function refinedPanel(terrain, a, b, ue, un, half, ends, dryReach) {
  const dyadic = (level) => Array.from({ length: (1 << level) + 1 }, (_, c) => c / (1 << level));
  const build = (levelR, fr = dyadic(0)) => {
    const R = 1 << levelR;
    const C = fr.length - 1;
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
      for (let c = 0; c <= C; c++) {
        const f = fr[c];
        // Rounded to the float32 the position buffer will store, and sampled
        // AT that value: on the ~1:1 ramp flanks the double-precision position
        // and its stored float32 stand on ground ~1e-5 m apart, which is
        // exactly the drape budget the smoke holds vertices to.
        let e = Math.fround(left[0] * (1 - f) + right[0] * f);
        let n = Math.fround(left[1] * (1 - f) + right[1] * f);
        // T-1812. An END row is shared with the next panel, which may have
        // settled on fewer columns, so its edge there is the straight line
        // between the two corners. This row's own midpoints, rounded to
        // float32, can land a few hundredths of a millimetre INSIDE that line,
        // and the sliver between the two panels is uncovered ground: it opened
        // the bisector of west_water's 7.7° bend to the smoke's joint stations.
        // Such a vertex is stepped one float32 at a time OUTWARD until it stands
        // on the line or just past it, so the finer panel always reaches the
        // shared edge and never falls short of it.
        if ((r === 0 || r === R) && c > 0 && c < C) {
          [e, n] = ontoEndLine(e, n, left, right, r === 0 ? a : b, r === 0 ? b : a);
        }
        const interior = (r > 0 && r < R) || (c > 0 && c < C);
        if (interior && terrain.isWater(e, n)) return null;
        // The fourth entry is where this column stands ACROSS the panel, 0 at
        // the left edge and 1 at the right: the texture's `u`. See addRecord.
        row.push([e, n, terrain.surfaceHeight(e, n) + LIFT_M, f]);
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
  let miss = residual(grid);
  if (miss <= DRAPE_TOL_M) return grid;
  // T-1812. COLUMNS WHERE THE GROUND BENDS, not where a halving lands. The
  // graded street section (terrain_gen.py) crowns the bed and drops it into a
  // gutter at each shoulder, so a panel one quad wide misses its own ground
  // ACROSS the street on every graded panel in the town. But the ground a
  // visitor stands on is `surfaceHeight()`, a bilinear field on a 2.5 m
  // lattice, and along a line it only bends where it crosses one of that
  // lattice's lines. So the columns go at those crossings (measured on the
  // panel's middle row): the cut is followed with as few columns as the
  // street is cells wide. Halving both axes answered the same miss with up to
  // 8 x 8 sub-quads per panel and took the layer from 59 k to 466 k
  // triangles; halving across first, to 296 k — which on its own put Lake
  // Street at Canal 238 k triangles over the `full` ceiling.
  // Rows are halved only when the columns alone cannot settle it (a bend, an
  // approach fill), which is the case the joint refinement was written for;
  // a panel the lattice does not settle falls back to halving across.
  let fr = latticeFractions(terrain.grid, ends);
  let levelR = 0;
  if (fr.length > 2) {
    const next = build(0, fr);
    if (next) { grid = next; miss = residual(grid); } else fr = dyadic(0);
  }
  let levelC = 0;
  let acrossShut = fr.length > 2;
  while (miss > DRAPE_TOL_M
    && ((!acrossShut && levelC < MAX_DRAPE_LEVEL) || levelR < MAX_DRAPE_LEVEL)) {
    const across = !acrossShut && levelC < MAX_DRAPE_LEVEL;
    const next = across ? build(levelR, dyadic(levelC + 1)) : build(levelR + 1, fr);
    if (!next && across) { acrossShut = true; continue; }
    if (!next) break;
    grid = next;
    if (across) { levelC += 1; fr = dyadic(levelC); } else levelR += 1;
    miss = residual(grid);
  }
  return grid;
}

/**
 * THE RIDGE DRAPE — where the panels above cannot follow the ground, the road is
 * laid on the ground's own cells instead (owner, 2026-10-02: walking a dirt road
 * on dev, "the grass area seems to grow and show up over the dirt road as you
 * approach it").
 *
 * WHY THE PANELS COULD NOT. `latticeFractions` above assumes the bilinear field
 * is straight along a line between two grid lines. It is — along a line PARALLEL
 * to a grid axis. Along any other line a bilinear cell is a parabola (the
 * `x·y` term), and the streets of this town do not run on the lattice's axes:
 * Lake Street at Market crosses it at about 24 degrees. So on the graded beds
 * T-1812 cut — a crown and two gutters, which is exactly where a cell twists —
 * the columns sat in the wrong places, the halving ran out of levels, and the
 * ribbon was left UNDER its own ground between its vertices. Measured town-wide
 * on the shipped build, probed inside every street triangle: 4,368 triangles
 * below the field, 1,180 of them by more than 3 cm, worst 0.30 m on the bridge
 * approaches; at Lake and Market 406 of 3,935, worst 0.21 m. Under a road the
 * opaque ground wins the depth test wherever that happens, and the polygon
 * offset only hides it at a grazing angle — which is why the grass "grew" as
 * the owner walked up to it.
 *
 * AND THE GROUND THAT IS DRAWN IS NOT EVEN THE BILINEAR FIELD. The baked mesh
 * splits each cell into two triangles, and between its vertices a triangulated
 * cell stands off the bilinear surface by up to a quarter of the cell's twist
 * (h00 + h11 − h10 − h01). Under the roads 2,126 of 37,931 cells twist by more
 * than 4 cm. A road that matched the bilinear field exactly would still lose to
 * whichever diagonal the bake chose.
 *
 * SO THE ROAD IS LAID ON THE CELLS' RIDGE. Of a cell's two diagonals, the one
 * joining the pair of corners with the larger sum gives a surface that is never
 * below the bilinear patch (the difference is T·y·(1−x) on one half and
 * T·x·(1−y) on the other, both ≥ 0 when that diagonal is chosen) — and so never
 * below the other triangulation either. Cut on the cells and their ridge
 * diagonals, each piece of road is planar on a plane that bounds the ground
 * from above, and nothing the ground draws can rise through it.
 *
 * WHAT IT COSTS AND WHERE IT IS SPENT. Only a panel whose refined grid still
 * sags more than SAG_TOL_M under the ridge is cut this way (and every joint
 * fan, whose rim was never refined at all); the flat town keeps its panels.
 * That is 1,392 of 6,937 panels and +43,634 triangles town-wide (106,891 →
 * 150,524), at every stand since the layer is drawn whole, and it is spent at
 * `full` and `balanced` only: `light` keeps the grids (`ridgeAt` in
 * createStreets) and the two ceilings above it moved for it, in main.js.
 * Read again after the terrain rebake (T-1956) and with the shoulders' edge
 * found by halving rather than on the 0.5 m ladder (groundReach): 1,395 panels,
 * 105,579 → 154,303 — the rim no longer lands on cell lines, so it is cut into
 * a few more pieces (+3,382 over the ladder's 150,921), inside both ceilings'
 * recorded headroom.
 * Looser tolerances were priced and refused (docs/measurements/
 * T-1987-road-ridge-cost.md): every millimetre over 15 is ground the bake can
 * push through the 22 mm lift.
 * A cut vertex inside a cell stands on the ridge, which is above the field by at
 * most that cell's quarter-twist — so the smoke's drape gate reads a vertex
 * against BOTH surfaces (`drapeBounds`): never under the field, never over the
 * ridge. The terrain is not touched and the walker stands on the same field.
 */
const SAG_TOL_M = 0.015;
// How far, and in what steps, a cut vertex on a trimmed side may step inside
// the panel to leave the water mask (see ridgeDrape): two centimetres at a
// time, at most a quarter metre — the order of dryReach's own 8 cm settle.
const WET_NUDGE_M = 0.02;
const WET_NUDGE_STEPS = 12;

/** The lattice node heights of the cell holding (e, n), with its fractions. */
function cellAt(terrain, e, n) {
  const g = terrain.grid;
  const gx = (e - g.originE) / g.cellM;
  const gy = (n - g.originN) / g.cellM;
  const i = Math.floor(gx);
  const j = Math.floor(gy);
  const node = (a, b) => terrain.surfaceHeight(g.originE + a * g.cellM, g.originN + b * g.cellM);
  return { i, j, fx: gx - i, fy: gy - j,
    h00: node(i, j), h10: node(i + 1, j), h01: node(i, j + 1), h11: node(i + 1, j + 1) };
}

/** The ridge of a cell at fractions (fx, fy): its upper triangulation. */
function ridgeOf({ fx, fy, h00, h10, h01, h11 }) {
  if (h00 + h11 >= h10 + h01) {
    return fx >= fy ? h00 + (h10 - h00) * fx + (h11 - h10) * fy
      : h00 + (h11 - h01) * fx + (h01 - h00) * fy;
  }
  return fx + fy <= 1 ? h00 + (h10 - h00) * fx + (h01 - h00) * fy
    : h11 + (h01 - h11) * (1 - fx) + (h10 - h11) * (1 - fy);
}

/** The ground's upper triangulation at (e, n) — see THE RIDGE DRAPE. Equal to
 *  `surfaceHeight()` on every lattice line; above it inside a twisted cell. */
export function ridgeHeight(terrain, e, n) {
  return ridgeOf(cellAt(terrain, e, n));
}

/** How far a draped grid falls under the ridge (+ LIFT_M) between its own
 *  vertices, probed as `residual` probes: the deepest deficit, ≥ 0. */
function gridSag(terrain, rows) {
  let worst = 0;
  for (let r = 0; r < rows.length - 1; r++) {
    for (let c = 0; c < rows[r].length - 1; c++) {
      const q = [rows[r][c], rows[r][c + 1], rows[r + 1][c], rows[r + 1][c + 1]];
      for (let i = 0; i <= 4; i++) {
        for (let j = 0; j <= 4; j++) {
          const ft = i / 4;
          const fs = j / 4;
          const e = (q[0][0] * (1 - fs) + q[1][0] * fs) * (1 - ft)
            + (q[2][0] * (1 - fs) + q[3][0] * fs) * ft;
          const n = (q[0][1] * (1 - fs) + q[1][1] * fs) * (1 - ft)
            + (q[2][1] * (1 - fs) + q[3][1] * fs) * ft;
          // The quad is drawn as two triangles split on (0,1)-(1,0), not as a
          // bilinear patch, so the height is read on the triangle it lands in.
          const y = fs + ft <= 1
            ? q[0][2] + (q[1][2] - q[0][2]) * fs + (q[2][2] - q[0][2]) * ft
            : q[3][2] + (q[2][2] - q[3][2]) * (1 - fs) + (q[1][2] - q[3][2]) * (1 - ft);
          if (!terrain.inBounds(e, n)) continue;
          worst = Math.max(worst, ridgeHeight(terrain, e, n) + LIFT_M - y);
        }
      }
    }
  }
  return worst;
}

/** Sutherland–Hodgman: a convex polygon clipped by a convex one (plan, [e, n]). */
function clipConvex(subject, clip) {
  let area = 0;
  for (let k = 0; k < clip.length; k++) {
    const [a, b] = [clip[k], clip[(k + 1) % clip.length]];
    area += a[0] * b[1] - b[0] * a[1];
  }
  const orient = Math.sign(area) || 1;
  let out = subject;
  for (let k = 0; k < clip.length && out.length; k++) {
    const A = clip[k];
    const B = clip[(k + 1) % clip.length];
    const side = (p) => orient * ((B[0] - A[0]) * (p[1] - A[1]) - (B[1] - A[1]) * (p[0] - A[0]));
    const input = out;
    out = [];
    for (let m = 0; m < input.length; m++) {
      const P = input[m];
      const Q = input[(m + 1) % input.length];
      const sp = side(P);
      const sq = side(Q);
      if (sp >= 0) out.push(P);
      if ((sp >= 0) !== (sq >= 0)) {
        const t = sp / (sp - sq);
        out.push([P[0] + (Q[0] - P[0]) * t, P[1] + (Q[1] - P[1]) * t]);
      }
    }
  }
  return out;
}

/** (u, t) of plan point P in the bilinear quad L0 (0,0) R0 (1,0) R1 (1,1) L1 (0,1). */
function quadCoords(P, L0, R0, R1, L1) {
  let u = 0.5;
  let t = 0.5;
  for (let k = 0; k < 8; k++) {
    const pe = (1 - t) * ((1 - u) * L0[0] + u * R0[0]) + t * ((1 - u) * L1[0] + u * R1[0]);
    const pn = (1 - t) * ((1 - u) * L0[1] + u * R0[1]) + t * ((1 - u) * L1[1] + u * R1[1]);
    const due = (1 - t) * (R0[0] - L0[0]) + t * (R1[0] - L1[0]);
    const dun = (1 - t) * (R0[1] - L0[1]) + t * (R1[1] - L1[1]);
    const dte = (1 - u) * (L1[0] - L0[0]) + u * (R1[0] - R0[0]);
    const dtn = (1 - u) * (L1[1] - L0[1]) + u * (R1[1] - R0[1]);
    const det = due * dtn - dun * dte;
    if (Math.abs(det) < 1e-12) break;
    const re = P[0] - pe;
    const rn = P[1] - pn;
    u += (re * dtn - rn * dte) / det;
    t += (due * rn - dun * re) / det;
  }
  return [Math.min(1, Math.max(0, u)), Math.min(1, Math.max(0, t))];
}

/**
 * One convex plan polygon laid on the ridge: cut by every lattice cell it
 * touches and by each cell's ridge diagonal, every piece planar on its half-cell.
 * `attrOf(e, n)` gives the vertex's [u, t]; `onEnd(e, n, t)` may nudge a vertex
 * that lands on an end line (see `ontoEndLine`). Returns null — keep the panel
 * as it was — if any piece would stand on water or off the grid, the same two
 * refusals `refinedPanel` makes.
 */
function ridgeDrape(terrain, polygon, attrOf, onEnd = null) {
  const g = terrain.grid;
  if (!g || !(g.cellM > 0)) return null;
  const es = polygon.map((p) => p[0]);
  const ns = polygon.map((p) => p[1]);
  const i0 = Math.floor((Math.min(...es) - g.originE) / g.cellM);
  const i1 = Math.floor((Math.max(...es) - g.originE) / g.cellM);
  const j0 = Math.floor((Math.min(...ns) - g.originN) / g.cellM);
  const j1 = Math.floor((Math.max(...ns) - g.originN) / g.cellM);
  const verts = [];
  const tris = [];
  const mid = [es.reduce((a, v) => a + v, 0) / es.length, ns.reduce((a, v) => a + v, 0) / ns.length];
  const X = (i) => g.originE + i * g.cellM;
  const Y = (j) => g.originN + j * g.cellM;
  for (let i = i0; i <= i1; i++) {
    for (let j = j0; j <= j1; j++) {
      const p00 = [X(i), Y(j)];
      const p10 = [X(i + 1), Y(j)];
      const p01 = [X(i), Y(j + 1)];
      const p11 = [X(i + 1), Y(j + 1)];
      const cell = clipConvex(polygon, [p00, p10, p11, p01]);
      if (cell.length < 3) continue;
      const h = cellAt(terrain, (p00[0] + p11[0]) / 2, (p00[1] + p11[1]) / 2);
      const halves = h.h00 + h.h11 >= h.h10 + h.h01
        ? [[p00, p10, p11], [p00, p11, p01]] : [[p00, p10, p01], [p10, p11, p01]];
      for (const tri of halves) {
        const piece = clipConvex(cell, tri);
        if (piece.length < 3) continue;
        let area = 0;
        for (let k = 0; k < piece.length; k++) {
          const [a, b] = [piece[k], piece[(k + 1) % piece.length]];
          area += a[0] * b[1] - b[0] * a[1];
        }
        if (Math.abs(area) < 1e-8) continue;
        // The piece's ridge plane, read at its centroid's half-cell rather than
        // per vertex, so a vertex on the diagonal cannot pick the other half.
        const cx = piece.reduce((s, p) => s + p[0], 0) / piece.length;
        const cy = piece.reduce((s, p) => s + p[1], 0) / piece.length;
        const fxC = (cx - p00[0]) / g.cellM;
        const fyC = (cy - p00[1]) / g.cellM;
        const base = verts.length;
        for (const [pe, pn] of piece) {
          let e = Math.fround(pe);
          let n = Math.fround(pn);
          // A side the waterline trimmed is straight between two dry corners
          // (dryReach) and can dip a centimetre into the mask between them;
          // the grid never put a vertex there, a cell edge can. Such a vertex
          // steps toward the polygon's own centre until it is dry — the same
          // step for every piece that shares it, so no seam opens.
          let nudged = false;
          if (terrain.isWater(e, n)) {
            nudged = true;
            const de = mid[0] - e;
            const dn = mid[1] - n;
            const len = Math.hypot(de, dn) || 1;
            for (let k = 1; k <= WET_NUDGE_STEPS && terrain.isWater(e, n); k++) {
              e = Math.fround(pe + (de / len) * WET_NUDGE_M * k);
              n = Math.fround(pn + (dn / len) * WET_NUDGE_M * k);
            }
          }
          const [u, t] = attrOf(e, n);
          if (onEnd) [e, n] = onEnd(e, n, t);
          if (!terrain.inBounds(e, n) || terrain.isWater(e, n)) return null;
          const fx = (e - p00[0]) / g.cellM;
          const fy = (n - p00[1]) / g.cellM;
          // Same half as the centroid: evaluate that half's plane directly. A
          // nudged vertex may have left the cell, so it reads the ridge where
          // it now stands — every piece sharing it reads the same.
          const ridge = nudged ? ridgeHeight(terrain, e, n) : halfPlane(h, fx, fy, fxC, fyC);
          verts.push([e, n, ridge + LIFT_M, u, t]);
        }
        // Wound as the panels are — clockwise in plan (e, n) — so the normals
        // computeVertexNormals() derives face the sky as theirs do.
        for (let k = 1; k < piece.length - 1; k++) {
          tris.push(area > 0 ? [base, base + k + 1, base + k] : [base, base + k, base + k + 1]);
        }
      }
    }
  }
  return tris.length ? { verts, tris } : null;
}

/** The plane of the ridge half-cell that (fxC, fyC) lies in, read at (fx, fy). */
function halfPlane({ h00, h10, h01, h11 }, fx, fy, fxC, fyC) {
  if (h00 + h11 >= h10 + h01) {
    return fxC >= fyC ? h00 + (h10 - h00) * fx + (h11 - h10) * fy
      : h00 + (h11 - h01) * fx + (h01 - h00) * fy;
  }
  return fxC + fyC <= 1 ? h00 + (h10 - h00) * fx + (h01 - h00) * fy
    : h11 + (h01 - h11) * (1 - fx) + (h10 - h11) * (1 - fy);
}

/**
 * A refined panel's grid re-laid on the ridge, or null to keep the grid. One
 * quad when the panel's sides are straight (every untrimmed panel: its interior
 * rows stand on the same offset lines its mitred ends do); one strip per row
 * where the waterline trimmed a row, so the trim is kept exactly.
 */
function offLine(P, A, B) {
  const de = B[0] - A[0];
  const dn = B[1] - A[1];
  const len = Math.hypot(de, dn) || 1;
  return Math.abs(de * (P[1] - A[1]) - dn * (P[0] - A[0])) / len;
}

/** True when a refined grid's two sides are straight lines: no row trimmed. */
function straightGrid(grid) {
  const R = grid.length - 1;
  const C = grid[0].length - 1;
  for (let r = 1; r < R; r++) {
    if (offLine(grid[r][0], grid[0][0], grid[R][0]) >= 1e-4
      || offLine(grid[r][C], grid[0][C], grid[R][C]) >= 1e-4) return false;
  }
  return true;
}

function ridgePanel(terrain, grid, ends, a, b) {
  const R = grid.length - 1;
  const C = grid[0].length - 1;
  const L = (r) => grid[r][0];
  const Rt = (r) => grid[r][C];
  const cuts = straightGrid(grid) ? [0, R] : Array.from({ length: R + 1 }, (_, r) => r);
  const onEnd = (e, n, t) => {
    if (t < 1e-6) return ontoEndLine(e, n, ends.aLeft, ends.aRight, a, b);
    if (t > 1 - 1e-6) return ontoEndLine(e, n, ends.bLeft, ends.bRight, b, a);
    return [e, n];
  };
  const verts = [];
  const tris = [];
  for (let k = 0; k < cuts.length - 1; k++) {
    const r0 = cuts[k];
    const r1 = cuts[k + 1];
    const quad = [L(r0), Rt(r0), Rt(r1), L(r1)].map(([e, n]) => [e, n]);
    const t0 = r0 / R;
    const t1 = r1 / R;
    const strip = ridgeDrape(terrain, quad, (e, n) => {
      const [u, tt] = quadCoords([e, n], quad[0], quad[1], quad[2], quad[3]);
      return [u, t0 + (t1 - t0) * tt];
    }, onEnd);
    if (!strip) return null;
    const base = verts.length;
    verts.push(...strip.verts);
    for (const [i, j, l] of strip.tris) tris.push([base + i, base + j, base + l]);
  }
  return { verts, tris };
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

function addRecord(buffers, record, terrain, stats, ridge = true, fades = null) {
  const key = record.surface;
  const buf = buffers.get(key)
    ?? { pos: [], uv: [], conf: [], track: [], road: [], ends: [], idx: [] };
  buffers.set(key, buf);
  // T-0111. The ribbon is painted on the WHEEL line; every other question this
  // module answers is asked of the platted one. `drawn` is `path` for all but
  // the one street that authors a separate track, so this is the same call it
  // has always been everywhere else.
  const pts = sampled(record.drawn);
  // T-1811. The worked earth, not the wheel track alone — see WORKED_SHARE.
  const half = record.drawn_width_m * 0.5;
  const road = [record.drawn_width_m, record.core_share, record.wear_intensity,
    record.wear_seed];
  const endFade = fades?.get(record) ?? NO_FADE;
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
  // T-1811. Past the recorded track a shoulder also stops where the ground
  // falls away from the crown (SHOULDER_DROP_M) — never inside the track, so the
  // waterline is still the only thing that can narrow the core.
  const trackHalf = record.track_width_m * 0.5;
  const groundReach = (e0, n0, se, sn, max) => {
    const dry = dryReach(e0, n0, se, sn, max);
    if (dry <= trackHalf) return dry;
    const h0 = terrain.surfaceHeight(e0, n0);
    const falls = (d) => Math.abs(terrain.surfaceHeight(e0 + se * d, n0 + sn * d) - h0)
      > SHOULDER_DROP_M;
    // The scan finds the first step that falls; the edge is then found inside
    // that step by halving, so the rim follows the ground's own contour rather
    // than snapping to the 0.5 m ladder, which drew it as stair steps along
    // every bank and cut wall (T-1987).
    const edge = (lo, hi) => {
      for (let k = 0; k < CLIP_STEPS; k++) {
        const mid = (lo + hi) * 0.5;
        if (falls(mid)) hi = mid; else lo = mid;
      }
      return Math.max(trackHalf, lo);
    };
    let last = trackHalf;
    for (let d = trackHalf + SHOULDER_STEP_M; d < dry; d += SHOULDER_STEP_M) {
      if (falls(d)) return edge(last, d);
      last = d;
    }
    return falls(dry) ? edge(last, dry) : dry;
  };
  const joins = mitreJoins(pts, half, groundReach, stats);
  // A joint's fan may only be drawn between two panels that were both drawn —
  // otherwise it would bridge to an edge that is not there. A rim the waterline
  // trimmed is clipped with it rather than dropped (T-1811, below).
  const panelDrawn = pts.map(() => false);

  function emitRidge(ridge, along, length) {
    const base = buf.pos.length / 3;
    for (const [e, n, y, u, t] of ridge.verts) {
      buf.pos.push(e, y, -n);
      buf.conf.push(confidence);
      buf.track.push(trackConfidence);
      buf.road.push(...road);
      buf.ends.push(...endFade);
      buf.uv.push(u, along + length * t);
    }
    for (const [p, q, w] of ridge.tris) buf.idx.push(base + p, base + q, base + w);
  }
  // A straight run of panels, laid as one quad when any of them needs the
  // ridge. A panel is 2.25 m long and a cell 2.5 m, so a panel laid on the
  // cells alone is nearly all edge pieces — 54 triangles a panel, measured —
  // where the whole straight run between two joints is about 19 a panel: less
  // than laying only the panels that sag, and no seam between a laid panel and
  // a gridded one. A panel joins the run when it starts on the run's own end
  // row and its two sides continue the run's: same chord, untrimmed, no joint.
  const run = {
    entries: [],
    start(entry) { this.entries = [entry]; },
    extend(entry) {
      const last = this.entries[this.entries.length - 1];
      if (!last || last.i !== entry.i - 1 || !straightGrid(entry.grid)) return false;
      if (!straightGrid(last.grid)) return false;
      if (!entry.grid.every((row) => row.every(([e, n]) => terrain.inBounds(e, n)))) return false;
      const first = this.entries[0];
      const same = (P, Q) => Math.abs(P[0] - Q[0]) < 1e-6 && Math.abs(P[1] - Q[1]) < 1e-6;
      if (!same(entry.ends.aLeft, last.ends.bLeft) || !same(entry.ends.aRight, last.ends.bRight)) {
        return false;
      }
      if (offLine(entry.ends.bLeft, first.ends.aLeft, last.ends.bLeft) > 1e-4
        || offLine(entry.ends.bRight, first.ends.aRight, last.ends.bRight) > 1e-4) return false;
      this.entries.push(entry);
      return true;
    },
    flush() {
      const list = this.entries;
      this.entries = [];
      if (!list.length) return;
      if (!list.some((x) => x.needsRidge)) {
        for (const x of list) emitGrid(x.grid, x.along, x.length);
        return;
      }
      const first = list[0];
      const last = list[list.length - 1];
      const length = list.reduce((sum, x) => sum + x.length, 0);
      let ridge = null;
      if (list.length > 1) {
        const quad = [first.ends.aLeft, first.ends.aRight, last.ends.bRight, last.ends.bLeft];
        ridge = ridgeDrape(terrain, quad, (e, n) => quadCoords([e, n], ...quad), (e, n, t) => {
          if (t < 1e-6) return ontoEndLine(e, n, first.ends.aLeft, first.ends.aRight, first.a, first.b);
          if (t > 1 - 1e-6) return ontoEndLine(e, n, last.ends.bLeft, last.ends.bRight, last.b, last.a);
          return [e, n];
        });
      }
      if (ridge) {
        emitRidge(ridge, first.along, length);
        for (const x of list) {
          stats.panels += 1;
          stats.refinedPanels += 1;
          stats.ridgePanels += 1;
        }
        return;
      }
      // One at a time: a run the water reaches, or a lone panel.
      for (const x of list) {
        const one = x.needsRidge ? ridgePanel(terrain, x.grid, x.ends, x.a, x.b) : null;
        if (one) {
          emitRidge(one, x.along, x.length);
          stats.panels += 1;
          stats.refinedPanels += 1;
          stats.ridgePanels += 1;
        } else {
          emitGrid(x.grid, x.along, x.length);
        }
      }
    },
  };

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
      const reach = groundReach(P[0], P[1], se, sn, half);
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
    // T-0110: a grid of (level+1)² draped vertices — one quad at level 0,
    // which is this function's historical output exactly.
    const grid = refinedPanel(terrain, a, b, ue, un, half, {
      aLeft: [aLeft.e, aLeft.n],
      aRight: [aRight.e, aRight.n],
      bLeft: [bLeft.e, bLeft.n],
      bRight: [bRight.e, bRight.n],
    }, groundReach);
    const ends = {
      aLeft: [aLeft.e, aLeft.n], aRight: [aRight.e, aRight.n],
      bLeft: [bLeft.e, bLeft.n], bRight: [bRight.e, bRight.n],
    };
    // THE RIDGE DRAPE: a grid that still sags under the ground's upper
    // triangulation is re-laid on the cells (see ridgeDrape). Off-grid panels
    // stay as they are, for the reason refinedPanel gives. The decision is
    // taken per panel and spent per RUN: see `run` above.
    const needsRidge = ridge
      && grid.every((row) => row.every(([e, n]) => terrain.inBounds(e, n)))
      && gridSag(terrain, grid) > SAG_TOL_M;
    const entry = { i, a, b, ends, grid, along, length, needsRidge };
    panelDrawn[i] = true;
    if (!needsRidge) {
      run.flush();
      emitGrid(grid, along, length);
      continue;
    }
    if (!run.extend(entry)) {
      run.flush();
      run.start(entry);
    }
  }
  run.flush();

  function emitGrid(grid, along, length) {
    const rows = grid.length - 1;
    const cols = grid[0].length - 1;
    const base = buf.pos.length / 3;
    for (let r = 0; r <= rows; r++) {
      // Across first, distance along second — in METRES since T-1811: the
      // wear is laid in the street's own frame and nothing repeats along it.
      const v = along + (length * r) / rows;
      for (let c = 0; c <= cols; c++) {
        // `u` is the column's own fraction across the panel, NOT c / cols. The
        // two agreed while every column was a halving; T-1812 put the columns
        // where the ground's lattice crosses the panel, which is a different
        // set of fractions on every panel, and `c / cols` then stretched the
        // street's across-coordinate differently panel by panel. Everything
        // the shader lays across the street — the shoulders giving way to
        // grass, the lanes, the sod islands — jumped at every 2.25 m panel
        // edge: the stepped, sawtooth grass and the blocky light-and-dark
        // patches at Lake and Market and South Water and Lake (owner,
        // 2026-10-02).
        const [e, n, y, u] = grid[r][c];
        buf.pos.push(e, y, -n);
        buf.conf.push(confidence);
        buf.track.push(trackConfidence);
        buf.road.push(...road);
        buf.ends.push(...endFade);
        buf.uv.push(u, v);
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
    if (rows > 1 || cols > 1) stats.refinedPanels += 1;
  }

  // T-0184. The corner patch, emitted after the panels because it needs both of
  // its neighbours to exist. R-BUG4's rule binds it exactly as it binds a panel
  // vertex: a fan with any corner on water is not drawn, because a ford is not
  // a thing this module may paint.
  for (let p = 1; p < pts.length - 1; p++) {
    const join = joins[p];
    if (!join?.fan || !panelDrawn[p] || !panelDrawn[p + 1]) continue;
    const { apex, apexSide } = join.fan;
    // T-1811. A fan whose rim reached the waterline used to be dropped whole
    // (`fanBlocked`), which at the core's old 5.25 m never happened on South
    // Water's west bend and at the worked 9.75 m always did — reopening the very
    // wedge T-0184 closed. Each rim vertex is now pulled back along its own ray
    // by the reach the panels use, so the fan's two end vertices are exactly the
    // trimmed panel corners and the rim between them stays on dry ground.
    const P = pts[p];
    const outer = join.fan.outer.map(([e, n]) => {
      const r = Math.hypot(e - P[0], n - P[1]);
      if (r < 1e-9) return [e, n];
      const se = (e - P[0]) / r;
      const sn = (n - P[1]) / r;
      const reach = groundReach(P[0], P[1], se, sn, r);
      return [P[0] + se * reach, P[1] + sn * reach];
    });
    if (terrain.isWater(apex.e, apex.n)) continue;
    if (outer.some(([e, n]) => terrain.isWater(e, n))) continue;
    const base = buf.pos.length / 3;
    const v = alongAt[p];
    // THE RIDGE DRAPE, for every fan: its rim reaches the full worked
    // half-width from one apex and was never refined at all, so it is the
    // likeliest surface in the town to sag under a crowned bed. All of its
    // triangles go on the ridge, or none do.
    const uApex = apexSide === 'L' ? 0 : 1;
    const ridged = [];
    for (let t = 0; ridge && t < outer.length - 1; t++) {
      const tri = [[apex.e, apex.n], outer[t], outer[t + 1]];
      const piece = ridgeDrape(terrain, tri, (e, n) => {
        const [A, B, C] = tri;
        const d = (B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1]);
        const wA = d ? ((B[1] - C[1]) * (e - C[0]) + (C[0] - B[0]) * (n - C[1])) / d : 1;
        return [uApex * wA + (1 - uApex) * (1 - wA), 0];
      });
      if (!piece) { ridged.length = 0; break; }
      ridged.push(piece);
    }
    if (ridged.length === outer.length - 1) {
      let at = base;
      for (const piece of ridged) {
        for (const [e, n, y, u] of piece.verts) {
          buf.pos.push(e, y, -n);
          buf.conf.push(confidence);
          buf.track.push(trackConfidence);
          buf.road.push(...road);
          buf.ends.push(...endFade);
          buf.uv.push(u, v);
        }
        for (const [i0, i1, i2] of piece.tris) buf.idx.push(at + i0, at + i1, at + i2);
        at += piece.verts.length;
      }
      stats.jointFans += 1;
      stats.ridgeFans += 1;
      stats.jointFanTriangles += outer.length - 1;
      continue;
    }
    const push = (pe, pn, u) => {
      const e = Math.fround(pe);
      const n = Math.fround(pn);
      buf.pos.push(e, terrain.surfaceHeight(e, n) + LIFT_M, -n);
      buf.conf.push(confidence);
      buf.track.push(trackConfidence);
      buf.road.push(...road);
      buf.ends.push(...endFade);
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

/**
 * T-1811. The one grit tile every street shares — T-1797's `gritTilePixels`,
 * 256 px over 1.6 m: R is height read as grain, G/B the OpenGL normal. It
 * replaces `roadTexture`'s per-surface canvas and its two painted ruts. Built
 * once per createStreets() and disposed with it. Exported, with the tones, for
 * `yards.js`'s `road_earth` (T-2013): the worn ground at the town's doors is
 * drawn from this same tile so a path that meets the road is the road's dirt.
 */
export function roadGrit() {
  const data = gritTilePixels();
  const canvas = document.createElement('canvas');
  canvas.width = GRIT_TILE_PX;
  canvas.height = GRIT_TILE_PX;
  canvas.getContext('2d').putImageData(new ImageData(data, GRIT_TILE_PX, GRIT_TILE_PX), 0, 0);
  const texture = new THREE.CanvasTexture(canvas);
  texture.name = 'street-grit';
  texture.colorSpace = THREE.NoColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.magFilter = THREE.LinearFilter;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.anisotropy = 4;
  let sum = 0;
  for (let i = 0; i < data.length; i += 4) sum += data[i];
  return { texture, mean: sum / (data.length / 4) / 255 };
}

export function linearTone(rgb) {
  return new THREE.Color().setRGB(...rgb.map((v) => v / 255), THREE.SRGBColorSpace);
}

const ROAD_VERTEX = /* glsl */`
  vRoad = _road;
  vRoadEnds = _roadEnds;
  vRoadUv = uv;
  vRoadWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;
`;

/**
 * T-1811 — the worked roadway, per fragment. No texture fetch but the grit:
 * the coarse scales are value noise in the street's own frame (u across, metres
 * along), so a lane runs WITH the street on every bearing — the T-1797 mask was
 * axis-aligned only because its strip was.
 *
 *   lanes     anisotropic, 11 x 1.3 m then 4 x 0.55 m cells: many overlapping
 *             irregular tracks, wandering off the centreline over ~23 m
 *   coverage  1 across the core; the shoulders give way to grass as CLUMPS
 *             (0.6-2 m) once a jittered ramp passes each clump's own value, and
 *             a light street keeps grass between its lanes too
 *   wet       7-18 m patches, only where wear has broken the sod: muck-dark,
 *             smoother, the grit's relief levelled
 *   tone      the lane / between-lane pair x the grit's grain, x a 35 m tone
 *
 * (No backticks in here: a JS template literal.)
 */
const ROAD_FRAGMENT = /* glsl */`
  vec2 chiEN = vec2(vRoadWorld.x, -vRoadWorld.z);
  float chiW = vRoad.x;
  float chiCore = vRoad.y;
  float chiInt = vRoad.z;
  float chiSeed = vRoad.w * 97.0;
  float chiAlong = vRoadUv.y;
  float chiX = vRoadUv.x - 0.5;
  float chiAcross = chiX * chiW;
  float chiWander = (chiNoise(vec2(chiAlong / 23.0 + chiSeed, 0.5)) - 0.5) * 0.22;
  float chiA = abs(chiX * 2.0);
  float chiAw = abs((chiX - chiWander) * 2.0);
  float chiLanes = 0.6 * chiNoise(vec2(chiAlong / 11.0 + chiSeed * 1.3, chiAcross / 1.3))
                 + 0.4 * chiNoise(vec2(chiAlong / 4.0 + chiSeed * 2.1, chiAcross / 0.55));
  float chiCentre = 1.0 - smoothstep(chiCore * 0.6, 1.05, chiAw);
  float chiWear = clamp(chiCentre * (0.35 + 0.85 * chiLanes), 0.0, 1.0);
  float chiClump = chiNoise(chiEN / 1.1 + chiSeed * 0.37);
  float chiJit = (chiNoise(vec2(chiAlong / 6.0 + chiSeed * 3.7, 2.5)) - 0.5) * 0.20
               + (chiNoise(vec2(chiAlong / 1.7 + chiSeed, 9.5)) - 0.5) * 0.08;
  float chiShoulder = smoothstep(chiCore + chiJit, 1.0 + chiJit * 0.4, chiA);
  float chiGrass = smoothstep(chiClump - 0.14, chiClump + 0.14, chiShoulder * 1.12);
  // A light street keeps sod wherever its lanes have not reached: grass
  // islands strung along the street between the worn ways.
  float chiSodIsle = chiNoise(vec2(chiAlong / 7.0 + chiSeed * 4.9, chiAcross / 0.9));
  float chiBetween = (1.0 - chiInt) * 1.8
                   * smoothstep(0.42, 0.62, chiSodIsle * 0.75 + chiClump * 0.25 - chiLanes * 0.35 + 0.15);
  float chiCover = (1.0 - chiGrass) * (1.0 - min(chiBetween, 1.0));
  // Ruts: narrow wheel-cut lines that run WITH the street and wander, many of
  // them and never the same two — 9 m along by 0.3 m across, cut where the
  // field crests, deepest where wear is.
  float chiRutF = chiNoise(vec2(chiAlong / 9.0 + chiSeed * 5.3, chiAcross / 0.32));
  float chiRut = smoothstep(0.70, 0.86, chiRutF) * smoothstep(0.3, 0.8, chiWear);
  float chiWet = smoothstep(0.66, 0.80, 0.65 * chiNoise(chiEN / 8.0 + chiSeed * 0.11)
                                     + 0.35 * chiNoise(chiEN / 2.6 + 3.1))
               * smoothstep(0.45, 0.85, chiWear);
  vec4 chiGrit = texture2D(uGrit, chiEN / uGritM);
  float chiGrain = chiGrit.r / max(uGritMean, 1e-6);
  float chiBroad = 0.93 + 0.14 * chiNoise(chiEN / 35.0 + chiSeed * 0.07);
  vec3 chiDirt = mix(uDirtRest, uDirtLane, smoothstep(0.30, 0.80, chiWear)) * chiBroad;
  chiDirt = mix(chiDirt, uSod, 0.55 * chiShoulder);
  chiDirt *= 1.0 - 0.18 * chiRut;
  chiDirt = mix(chiDirt, uMud, 0.7 * chiWet);
  diffuseColor.rgb = min(chiDirt * mix(1.0, chiGrain, mix(0.65, 0.2, chiWet)), vec3(1.0));
  diffuseColor.a = chiCover;
  float chiRough = mix(0.97 - 0.06 * chiWear, 0.55, chiWet);
`;

const ROAD_NORMAL = /* glsl */`
  // The grit's relief in a world tangent frame (east, north, up), as T-1797's
  // strip does: full on dry dirt, levelled where it is wet.
  vec2 chiXY = (chiGrit.gb * 2.0 - 1.0) * mix(1.0, 0.2, chiWet);
  vec3 chiTn = normalize(vec3(chiXY, 1.0));
  vec3 chiEastV = normalize((viewMatrix * vec4(1.0, 0.0, 0.0, 0.0)).xyz);
  vec3 chiT = normalize(chiEastV - normal * dot(chiEastV, normal));
  vec3 chiB = cross(normal, chiT);
  normal = normalize(chiT * chiTn.x + chiB * chiTn.y + normal * chiTn.z);
`;

const ROAD_HEAD = /* glsl */`
varying vec4 vRoad;
varying vec4 vRoadEnds;
varying vec2 vRoadUv;
varying vec3 vRoadWorld;
uniform sampler2D uGrit;
uniform float uGritM;
uniform float uGritMean;
uniform vec3 uDirtLane;
uniform vec3 uDirtRest;
uniform vec3 uMud;
uniform vec3 uSod;
float chiHash(vec2 p) {
  vec3 q = fract(vec3(p.xyx) * 0.1031);
  q += dot(q, q.yzx + 33.33);
  return fract((q.x + q.y) * q.z);
}
float chiNoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(chiHash(i), chiHash(i + vec2(1.0, 0.0)), u.x),
             mix(chiHash(i + vec2(0.0, 1.0)), chiHash(i + vec2(1.0, 1.0)), u.x), u.y);
}
`;

function geometryOf(surface, buf) {
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
  // T-1811. Worked width, core share, wear intensity, seed — per street.
  geo.setAttribute('_road', new THREE.Float32BufferAttribute(buf.road, 4));
  // T-1987. Where the ribbon fades into a street it ends on — see endFades().
  geo.setAttribute('_roadEnds', new THREE.Float32BufferAttribute(buf.ends, 4));
  geo.setIndex(buf.idx);
  geo.computeVertexNormals();
  weldNormals(geo);
  return geo;
}

/**
 * One normal per POSITION, not per vertex. A ridge-laid piece owns its
 * vertices (THE RIDGE DRAPE), and so does every panel and fan, so
 * `computeVertexNormals` alone shades each piece as its own facet: on the
 * cells that is a quilt of 2.5 m squares lit a shade apart, and at a panel
 * edge a crease the ground under it does not have. Vertices that stand at the
 * same place (to a tenth of a millimetre) take the sum of their normals —
 * each already weighted by the area of the triangles it came from — so the
 * road is lit as one surface, the way the ground beside it is.
 */
function weldNormals(geo) {
  const pos = geo.attributes.position;
  const nor = geo.attributes.normal;
  const Q = 1e4;
  const sums = new Map();
  const keys = new Array(pos.count);
  for (let i = 0; i < pos.count; i++) {
    const k = `${Math.round(pos.getX(i) * Q)},${Math.round(pos.getY(i) * Q)},${Math.round(pos.getZ(i) * Q)}`;
    keys[i] = k;
    // Summed facing ONE way: the layer is double-sided and a few triangles
    // are wound the other way round, which the shader answers by flipping a
    // back face's normal. Each vertex gets the welded normal back on its own
    // side, so that flip still lands it facing the sky.
    const f = nor.getY(i) > 0 ? -1 : 1;
    const sum = sums.get(k);
    if (sum) {
      sum[0] += f * nor.getX(i); sum[1] += f * nor.getY(i); sum[2] += f * nor.getZ(i);
    } else {
      sums.set(k, [f * nor.getX(i), f * nor.getY(i), f * nor.getZ(i)]);
    }
  }
  for (let i = 0; i < pos.count; i++) {
    let [x, y, z] = sums.get(keys[i]);
    // A point only zero-area slivers reach (a fan's collinear rim) has no
    // normal of its own to give; it is level ground for the light.
    if (!(y < -1e-6)) [x, y, z] = [0, -1, 0];
    const f = (nor.getY(i) > 0 ? -1 : 1) / Math.hypot(x, y, z);
    nor.setXYZ(i, x * f, y * f, z * f);
  }
  nor.needsUpdate = true;
}

function meshOf(surface, buf, confidence, aidUniform, grit) {
  if (!buf.idx.length) return null;
  const geo = geometryOf(surface, buf);
  const tones = DIRT_TONES[surface] ?? DIRT_TONES.worn_earth;
  const mat = new THREE.MeshStandardMaterial({
    transparent: true,
    alphaTest: 0.025,
    depthWrite: false,
    roughness: 1,
    metalness: 0,
    side: THREE.DoubleSide,
    // T-1812. A transparent double-sided material is drawn in TWO passes by
    // default — every back-facing triangle, then every front-facing one — so
    // the renderer submitted the whole layer twice and the frame budget paid
    // for it twice, though each triangle is rasterised in only one of the two.
    // One pass draws the same triangles with the same lighting (the shader
    // flips a back face's normal itself); only the blend order of the joint
    // fans' overlaps can differ, and they are one surface over itself.
    forceSinglePass: true,
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
    Object.assign(shader.uniforms, {
      uGrit: { value: grit.texture },
      uGritM: { value: GRIT_TILE_M },
      uGritMean: { value: grit.mean },
      uDirtLane: { value: linearTone(tones.lane) },
      uDirtRest: { value: linearTone(tones.rest) },
      uMud: { value: linearTone(MUD_TONE) },
      uSod: { value: linearTone(SOD_TONE) },
    });
    shader.vertexShader = `attribute vec4 _road;
attribute vec4 _roadEnds;
varying vec4 vRoad;
varying vec4 vRoadEnds;
varying vec2 vRoadUv;
varying vec3 vRoadWorld;
${shader.vertexShader}`.replace('#include <begin_vertex>',
      `#include <begin_vertex>${ROAD_VERTEX}`);
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
${ROAD_HEAD}${graded ? 'varying float vTrackConfidence;\n' : ''}${shader.fragmentShader}`
      .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = chiRough;')
      .replace('#include <normal_fragment_maps>', ROAD_NORMAL)
      .replace(
      '#include <map_fragment>',
      `${ROAD_FRAGMENT}
      {
        float trackPx = 1.0 / max(fwidth(vRoadUv.x), 1e-6);
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
        // T-1987. After the boosts, or they would buy the fade back.
        diffuseColor.a *= smoothstep(vRoadEnds.x, vRoadEnds.y, vRoadUv.y)
          * (1.0 - smoothstep(vRoadEnds.z, vRoadEnds.w, vRoadUv.y));
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
        // T-1811. The worked road is opaque, so scaling alpha alone left the
        // aid moving almost nothing (the smoke read a 0.02 mean cell change at
        // the crossing, against 0.15). It now does what it is for on an opaque
        // road: fills the core's sod islands and lifts the dirt's lightness away
        // from the grass by up to ${AID_LIFT * 100}%. Both are x uRoadAid, so the
        // default frame is untouched.
        diffuseColor.a = max(diffuseColor.a, uRoadAid * (1.0 - chiShoulder));
        diffuseColor.rgb = min(diffuseColor.rgb * (1.0 + ${AID_LIFT.toFixed(2)} * uRoadAid), vec3(1.0));
      }`,
    );
  };
  confidence?.patch(mat);
  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = `streets-${surface}`;
  mesh.receiveShadow = true;
  mesh.castShadow = false;
  mesh.renderOrder = 0;
  return { mesh, geo, mat };
}

export function createStreets({ terrain, records = [], confidence = null, detail = 'full' } = {}) {
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
  const fades = endFades(prepared);
  // THE RIDGE DRAPE IS A FULL- AND BALANCED-DETAIL COST. `light` is the tier a
  // weak machine boots into and it stays inside its own ceiling (AGENTS.md), so
  // there the panels keep their refined grids: the near-hole in the coarse base
  // and the per-column `u` are free and reach every tier; the cut does not.
  const ridgeAt = (level) => level !== 'light';
  let ridge = ridgeAt(detail);
  // T-0110. With refinement a panel is no longer a fixed six indices, so the
  // smoke's panel-accounting gate reads these counters instead of index math.
  // T-0184 adds the joint counters. `squareJoints` is the one that matters: it
  // is the number of bends this module gave up on, and a gate that only ever
  // read `mitredJoints` could not tell a closed town from one where every turn
  // had quietly fallen through the guard.
  const layOut = (withRidge) => {
    const counts = {
      panels: 0, refinedPanels: 0,
      joints: 0, mitredJoints: 0, fannedJoints: 0, squareJoints: 0,
      jointFans: 0, jointFanTriangles: 0, ridgePanels: 0, ridgeFans: 0,
    };
    const laid = new Map();
    for (const record of prepared) {
      addRecord(laid, record, terrain, counts, withRidge, fades);
    }
    return { buffers: laid, counts };
  };
  const first = layOut(ridge);
  const buffers = first.buffers;
  const stats = first.counts;
  const resources = [];
  // R-A1. One uniform object shared by every surface's material, so the aid
  // cannot end up applied to the graded tracks and not the worn ones.
  const aidUniform = { value: 0 };
  // T-1811. One grit tile for the whole town, shared by every surface.
  const grit = buffers.size ? roadGrit() : null;
  for (const [surface, buf] of buffers) {
    const built = meshOf(surface, buf, confidence, aidUniform, grit);
    if (!built) continue;
    group.add(built.mesh);
    resources.push({ ...built, surface });
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
    /** The ground's upper triangulation at (e, n), the surface a ridge-laid
     *  panel stands on (THE RIDGE DRAPE). For the smoke's drape gates. */
    ridgeHeight: (e, n) => ridgeHeight(terrain, e, n),
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
    /** Whether the panels are laid on the ridge at the current detail. */
    get ridged() { return ridge; },
    /**
     * A change of scene detail, applied in place: the same meshes and
     * materials, new geometry. Returns whether anything was rebuilt — only a
     * move across `light` changes how the road is laid.
     */
    setDetail(level) {
      if (!level || ridgeAt(level) === ridge) return false;
      ridge = ridgeAt(level);
      const next = layOut(ridge);
      for (const r of resources) {
        const buf = next.buffers.get(r.surface);
        if (!buf?.idx.length) continue;
        const geo = geometryOf(r.surface, buf);
        r.mesh.geometry = geo;
        r.geo.dispose();
        r.geo = geo;
      }
      Object.assign(stats, next.counts);
      return true;
    },
    dispose() {
      for (const r of resources) {
        r.geo.dispose();
        r.mat.dispose();
      }
      grit?.texture.dispose();
    },
  };
}
