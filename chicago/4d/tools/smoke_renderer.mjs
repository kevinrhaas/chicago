/**
 * Smoke test for the three.js walkthrough.
 *
 *   PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
 *     node tools/smoke_renderer.mjs
 *
 * Drives the real page in a real browser at 390x780 AND 1280x800 and fails on
 * any page error. Mobile is a release gate, not a nice-to-have.
 *
 * `SMOKE_VIEWPORT=mobile` (or `desktop`) runs one of the two while iterating.
 * That is not the gate and the run says so on its first line.
 *
 * `SMOKE_STAGE=1` … `13` runs one part of each viewport's body (T-0060, re-cut
 * by T-0121, T-0167, T-0346, T-0173 and T-0170), and `SMOKE_STAGE=1-2` runs a
 * contiguous run.
 * The cuts sit at section boundaries measured for zero crossing bindings. It
 * exists because a steward run's single foreground command is capped at ten
 * minutes and by 2026-08-18 neither viewport's full pass fit inside it, so the
 * run was killed mid-suite and the page-error assertion — the LAST line of each
 * viewport — was never taken. T-0060 cut four; by 2026-08-23 the town had grown
 * until three of the four DESKTOP quarters ran past the ceiling too, so each
 * quarter was halved; T-0167 measured the desktop profile that eight-way cut
 * had never been sized from and halved part 8, the thinnest margin on it.
 * T-0346 cut PART 4 in three when it stopped fitting at all: profiled under this
 * lane's own eight-way contention on 2026-08-30 it was killed at the ceiling with
 * 6 m 17 s of its cost in ONE section, the scene-detail ladder. That section is
 * now part 5 and the gate-and-chrome tail is part 6, so parts 5-9 became 7-11 and
 * the mobile recipe's ranges move with them. The parts after the cut cost about
 * 1 m 10 s, 6 m 17 s and 1 m 55 s against the ten minutes, measured the same way.
 * T-0173 then HALVED PART 7, which had gone the same way: profiled on the steward
 * runner the same day it was killed at 9 m 25 s with its last two assertions
 * unrun, and 7 m 04 s of that was the three road-legibility stations. Two
 * stations stay in part 7 and the third goes to a new part 8 with the aid taken
 * standing at it and the batch merge under that — 4 m 48 s against 4 m 53 s of
 * work — so parts 8-11 became 9-12. See ROAD_STATIONS and `readRoadStations`.
 * T-0170 halved PART 10 for the same reason and on the same evidence: at
 * 1280x800 on an IDLE runner it was killed at 9 m 20 s with the street readouts
 * and the Settings units still to run, so old parts 11-12 became 12-13 and there
 * are thirteen.
 *
 * A staged run is not the gate either, and says so; the gate is both viewports,
 * every part, e.g.:
 *
 *   for s in 1-2 3-6 7-9 10-13;               do SMOKE_VIEWPORT=mobile  SMOKE_STAGE=$s node tools/smoke_renderer.mjs --published; done
 *   for s in 1 2 3 4 5 6 7 8 9 10 11 12 13;   do SMOKE_VIEWPORT=desktop SMOKE_STAGE=$s node tools/smoke_renderer.mjs --published; done
 *
 * `SMOKE_TIMING=1` stamps each check line with the elapsed clock. Off by
 * default; turn it on to profile a part, because a part that BREACHES the
 * ceiling is killed before it prints its wall clock, and the parts worth
 * cutting are exactly the ones a plain run therefore reports nothing about.
 *
 * (each command above fits the ten-minute ceiling, measured — every invocation
 * prints its own wall clock on its last line so the next margin to go is
 * visible without anyone re-measuring by hand. The unfiltered single-process
 * pass lives in .github/workflows/chicago-4d-smoke.yml, which has no ceiling.)
 *
 * Boot, the page-error check and the vendor checks run in EVERY invocation,
 * whichever stage is asked for: the summary separates "staged-section checks"
 * from those always-on checks so the parts can be audited to add up to an
 * unfiltered pass — the thirteen parts' section counts SUM to an unfiltered run's
 * section count, and the always-on count is identical in every one of them.
 *
 * What it asserts, and why each one is here:
 *
 *   scene reaches ready ......... the boot chain actually completed
 *   canvas renders non-black .... WebGL produced an image, not a cleared buffer
 *   confidence toggle ........... the deliverable measurably changes the render
 *   pick -> citation ............ the visual claim and the citable claim connect
 *   citation -> its document .... why a modern page is on the rung it is on, and
 *                                 what the source itself says it cannot supply
 *   pick -> liberties ........... and what we made up about THAT building
 *   the bridge floats ........... a water-anchored structure is placed on the
 *                                 water plane, not on the river bed under it
 *   walk moves the camera ....... input intent reaches the walker
 *   the bridge carries a walker . a deck is a surface you stand on, end to end,
 *                                 and not the wading barrier under it
 *   the river wharves ........... the first derived layer that stands over water:
 *                                 its deck ties into the bank it was derived
 *                                 from, its crib reaches the bed, and neither is
 *                                 answerable from the dataset alone
 *   a wharf carries a walker .... and since T-0058 the planks are a floor: off
 *                                 the bank, up the boarding stair and out over
 *                                 the water at every one of the seven docks
 *   the boats on the river ...... the first layer that RIDES the water: every
 *                                 afloat hull floats in its own depth, beached
 *                                 hulls sit at the bank, the drawbridge's
 *                                 navigation span stays clear, and a boat
 *                                 answers a pick with its own card
 *   one terrain surface ......... walker, structures and flora share the rendered land
 *   streets drape + identify .... earth tracks share the heightfield and dated names
 *   the roads reach the screen .. and are distinguishable from the ground they
 *                                 occupy, on foot and from the air — draped is
 *                                 not seen, and every check above passed while
 *                                 the roads were invisible
 *   the horizon reads as timber . the band meets the fogged ground in one colour,
 *                                 and the crown modulation never cuts a silhouette
 *                                 below the pixel it needs to be seen at all
 *   navigation aids ............. compass, moving overview marker, settings toggles
 *   complete jump search ........ every viewpoint, verified junction and loaded
 *                                 structure, in one Go to tab, each structure
 *                                 graded with its own record's position grade
 *   liberties are readable ...... what we made up is in the panel, not only in the repo
 *   draw calls under budget ..... the batch strategy is doing its job, against a
 *                                 ceiling this file pins rather than merely reads
 *   zero page errors ............ everywhere, both widths
 *
 * On failure it prints the failing URL or text, never a bare status: a smoke
 * result you have to reproduce by hand has not saved you anything.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// The critic harness's PNG reader and its CIE L*, so a road's contrast is
// measured on the same scale as everything else this project quotes.
import { decodePng, labL, relativeLuminance, weberContrast } from './critic_metrics.mjs';
// ROADMAP K50. The gate and `tools/measure_drawn_placement.mjs` run ONE census
// rather than two readings of it — see that module's header for why.
import { CENSUS } from './drawn_placement_census.mjs';
// T-0243. Same arrangement for the near-field timber, and for the same reason
// twice over: the gate below and `tools/measure_drawn_timber.mjs` run ONE
// census, and that census reads a `BatchedMesh` back through its own instance
// ranges — which is what the inline traversal that used to live here stopped
// being able to do the day T-0223 merged.
import { TIMBER_CENSUS } from './drawn_timber_census.mjs';

// Playwright is installed globally here, and ESM does not honour NODE_PATH, so
// resolve the global root and import by absolute path.
async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH
      || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  // playwright is CommonJS; imported as ESM its exports land under .default
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();
// T-0016 — the per-band movement report. Pure functions in their own file so
// the comparison is testable without a browser; see its --self-test.
import { collect as collectRoadBands, compare as compareRoadBands, render as renderRoadBands }
  from './road_band_movement.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.SMOKE_PORT || 4187);
const YEAR = process.env.SMOKE_YEAR || '1835';
const KEEP = process.env.SMOKE_SHOTS || '';

/**
 * WHICH TREE gets tested, and why it is a question at all.
 *
 * The source tree and the published mirror do not load the same geometry. A
 * sidecar names its asset as `gltf/<name>.glb`, and that path resolves against
 * a different base in each: in the source tree to `assets/gltf/` — the
 * UNCOMPRESSED masters — and on the site to `data/gltf/`, which publish.sh
 * fills from `assets/web/`, the meshopt + `KHR_mesh_quantization` derivatives.
 *
 * So for as long as this only ever ran against the source tree, it never once
 * loaded a compressed asset. Every check was green while the deployed town was
 * a field of two-metre boxes, because the defect lived in a code path — the
 * dequantisation of normalized integer attributes — that the gate could not
 * reach. A gate that cannot see the bytes that ship is not a gate.
 *
 * `--published` (or SMOKE_TARGET=published) serves the mirror and enters at
 * /walk/, which is the visitor's exact layout. It also catches the other class
 * of bug this project keeps hitting: a file that exists in the source tree and
 * was never copied, which 404s only once it is live.
 */
const wantPublished = process.argv.includes('--published')
  || process.env.SMOKE_TARGET === 'published';
const ROOT = process.env.SMOKE_ROOT
  || (wantPublished
    ? path.resolve(HERE, '../../../site/chicago/4d')
    : path.resolve(HERE, '..'));
const ENTRY = process.env.SMOKE_ENTRY || (wantPublished ? '/walk/' : '/renderers/web/index.html');
const MODULE_BASE = wantPublished ? '/walk/js/' : '/renderers/web/js/';

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
};

/**
 * R-BUG2 — CAN A ROAD BE SEEN? The gate that did not exist.
 *
 * Everything this file asserted about the streets was about the DATA reaching
 * the geometry: seventeen records, a hundred thousand vertices, drape error
 * under 1e-5 m, no vertex over water. All of it passed while the roads were
 * invisible from the air. Draped is not seen, and nothing anywhere asked
 * whether a road reaches the screen.
 *
 * The measurement, per station and per viewport, is three frames of one held
 * scene:
 *
 *   R  the real render
 *   M  the same geometry drawn as an opaque marker with a DEEP polygon offset
 *   O  the same scene with the street group hidden
 *
 * M is the denominator and it is the reason this works. A probe point counts
 * only where the marker reached the screen — which is to say where a road is
 * present, in front of the camera, and not hidden behind a building, a tree or
 * a rise in the ground. Roads that are genuinely occluded drop out of the
 * sample instead of being scored as faults. The marker's offset is deliberately
 * DEEPER than the real material's: losing the depth fight to the terrain is the
 * failure being hunted, so it must stay inside the denominator and show up as a
 * road that covers the pixel and does not change it.
 *
 * The number is then |L*(R) - L*(O)| at each surviving probe — how much the
 * road changed what a visitor sees at the spot it occupies, in CIE L* units on
 * the same `labL` the critic harness measures reference photographs with. It is
 * the "distinguishable from the ground beside it" of the parcel's acceptance,
 * with the ground beside it read at the same pixel rather than a few metres
 * across, so a road crossing grass and a road crossing mud are held to the same
 * standard.
 *
 * WHAT THE FAULT MEASURED, before the fix, at desktop (mobile in the same
 * direction, smaller n): South Water Street at 250-600 m, unoccluded, scored
 * **0.3 L\* with 14 % of probes perceptible**; the aerial anchor at 100-250 m
 * scored **1.1 L\* with 0 %**. Both are FAILURES under the thresholds below,
 * which is the point — the check names the fault when the fault is put back.
 *
 * PROVENANCE OF THE NUMBERS (T-0033 / R-M1b, owner ruling 2026-08-17): these
 * bars are a PROVISIONAL BASELINE, not derived from a source — the photograph
 * R-M1 named as the derivation source contains no dirt track, and the owner
 * ruled "keep this baseline until I complain about it more later". Do not
 * describe them as derived, and do not spend a run re-deriving them unless the
 * owner reopens the question.
 */
const ROAD_MIN_DELTA_L = 1.8;
const ROAD_MIN_PERCEPTIBLE = 0.55;
const ROAD_MIN_PROBES = 8;

/**
 * T-0016 (R-M1d) — THE BANDS ARE ALSO REPORTED AGAINST THEIR OWN BANK.
 *
 * The three bars above gate PER STATION; the measurement is PER BAND. A band
 * can therefore collapse 55 points (71 % → 16 % perceptible) without crossing
 * ROAD_MIN_PERCEPTIBLE, and the suite prints "229/2 before, 229/2 after" while
 * it happens. `road_band_movement.mjs` banks each gated band and says out loud
 * when one moves — in either direction.
 *
 * It is a REPORT and not a bar, deliberately. The thresholds above are the
 * owner's provisional baseline (T-0033 / R-M1b) and R-W1 is the standing proof
 * that tightening them punishes legitimate work. Nothing below can fail a run.
 *
 * Re-bank with `--update-road-bands` in the commit that moved the numbers on
 * purpose, the same way the far-timber census is re-banked.
 */
const ROAD_BAND_BASELINE = path.join(HERE, 'road_band_baseline.json');
const UPDATE_ROAD_BANDS = process.argv.includes('--update-road-bands');
const ROAD_BAND_BANKED = (() => {
  try { return JSON.parse(fs.readFileSync(ROAD_BAND_BASELINE, 'utf8')).bands || {}; }
  catch { return {}; }
})();
const ROAD_BAND_OBSERVED = {};

/**
 * ROADMAP R-BUG5 — the bodies of far timber whose authored polyline crosses
 * water, read from the same file `tools/measure_far_timber.py` writes rather
 * than restated here.
 *
 * Two readers of one number: the Python censuses `data/terrain/…/heightfield.bin`
 * and this censuses the mask the browser loaded off the published mirror. They
 * must agree, and importing the baseline is what makes disagreement a failure
 * instead of a discrepancy nobody compares.
 */
const FAR_TIMBER_BANKED_BY_ID = Object.fromEntries(
  Object.entries(JSON.parse(
    fs.readFileSync(path.join(HERE, 'far_timber_baseline.json'), 'utf8'),
  ).bodies).map(([id, entry]) => [id, entry.wet]),
);
const FAR_TIMBER_BANKED = Object.keys(FAR_TIMBER_BANKED_BY_ID);
/**
 * R-M1a — THE TWO NUMBERS THE BARS ABOVE CANNOT SEE, MEASURED AND NOT YET GATED.
 *
 * The owner ruled on 2026-08-14, after R-W1 broke this gate by legitimately
 * changing exposure: score exposure-invariant CONTRAST **and** keep an absolute
 * FLOOR. Both bars, not a replacement. The two thresholds above are neither —
 * ΔL* is compressive, so R-W1 preserved the road/ground ratio to within 0.4 %,
 * got 14–17 % darker, and lost a bar it had not actually regressed.
 *
 * So each band now also reports:
 *
 *   weber      |Y(road) − Y(ground)| / Y(ground) on LINEAR luminance, median
 *              over the same probes. Exposure cancels out of it; see
 *              `weberContrast` in `critic_metrics.mjs` for why it is that
 *              quantity and not a bare ratio.
 *   groundL    median CIE L* of the ground at those probes with the street
 *              layer hidden — the floor reading. "Is there enough light here to
 *              distinguish anything at all", which is the failure mode a pure
 *              ratio would happily pass.
 *
 * **They are REPORTED AND NOT GATED, deliberately, and that is R-M1's split
 * rather than a half-finished job.** This half lands the measurement and commits
 * its numbers on `dev`; R-M1b sets the bars against them, and against the
 * pre-R-BUG2 build, which the acceptance requires the new bars still to FAIL.
 * Landing them silent means this change cannot alter a single pass/fail while
 * the baseline is being taken — a gate that moves at the same moment as its own
 * baseline has no baseline.
 *
 * **R-M1b has no threshold source yet, and that is the finding of this half.**
 * The parcel says to derive the bars from the reference photograph — "what
 * contrast does a real dirt track hold against real prairie". It does not hold
 * one: `python3 tools/measure_reference.py` now surveys the frame and the widest
 * contiguous bare-earth run anywhere in it is 8.2 % of the frame width, at
 * −38.2°, at the photographer's feet. Do not pick a number to fill that gap.
 */
/**
 * Two stations because the report was two symptoms: roads that go "in places"
 * on foot, and roads you "lose" when you fly over them. `south_water` looks
 * east down an open street from eye height; `from_above` is the scene's own
 * aerial anchor. Both are anchors a visitor is offered, driven through `goTo`,
 * so the gate cannot drift from what is shipped.
 *
 * Bands beyond 600 m are measured and printed but not gated: at eye height a
 * road that far off is a couple of pixels tall through a mile of haze, and a
 * threshold there would be a claim about fog, not about roads.
 */
//
// T-0173 — and `part` says which PART reads each of them. The three together
// cost 7 m 04 s of a part measured at 9 m 25 s and still running, so parts 7 and
// 8 take two of them and one: 2 m 13 s + 2 m 02 s against 2 m 49 s, which is what
// puts the aid and the batch merge in the cheaper half, beside the station they
// are taken at. Moving a station between the parts is this field and nothing else.
const ROAD_STATIONS = [
  { id: 'south_water', part: 7, kind: 'anchor', what: 'from the walker’s eye, down an open street', minBands: 2 },
  { id: 'from_above', part: 7, kind: 'anchor', what: 'from the air, at the aerial anchor', minBands: 2 },
  // R-BUG3. Neither anchor above STANDS ON A ROAD — the `south_water` viewpoint
  // is 101 m from the centreline it is named after (T-V2) and 17 m from the
  // nearest one — so the near band was empty at both and no threshold could
  // have caught the owner's report. This station arrives the way a visitor
  // does, by clicking a verified street-control intersection in the Go to tab,
  // which puts the roadway under the camera and its coordinates stay in the
  // compiled index rather than being copied into this gate.
  // R-A1's three assertions are taken standing HERE, so this station and the aid
  // stay in one part however this list is re-divided (T-0173).
  { id: 'lake_market', part: 8, kind: 'intersection', what: 'standing on the crossing itself', minBands: 2 },
];
const ROAD_BANDS = [[2, 40], [40, 100], [100, 250], [250, 600], [600, 4000]];
const ROAD_GATED_BEYOND_M = 600;

/**
 * T-0173 — the road-legibility stations, read by whichever PART owns them.
 *
 * These three stations were one block inside part 7, and profiled on the steward
 * runner (SMOKE_TIMING=1, 2026-08-30) that block was 7 m 04 s of a part that was
 * killed at 9 m 25 s with its tail unrun. So the cut that makes part 7 fit had to
 * fall INSIDE the block: neither of the part's own `// --- ` section boundaries
 * leaves both sides more than 2 m 36 s of margin, and 2 m 36 s is what T-0121
 * already proved is not a margin on a machine whose cost tracks its neighbours.
 *
 * The stations are the natural grain and the only one that crosses no binding.
 * Each teleports to its own viewpoint, takes its own frames and answers its own
 * `check`; none reads anything a sibling station left standing. `part:` on the
 * station is therefore the whole of the split — see ROAD_STATIONS.
 *
 * The movement report moves with them, and it is the same report it always was:
 * printed, never gated, and comparing only what THIS invocation measured. That
 * is what already let `SMOKE_VIEWPORT=mobile` run without retiring desktop's
 * half of the bank, and it is why a part reporting on its own stations is not a
 * new rule. `--update-road-bands` merges per band and leaves untouched bands
 * alone, so a part banks what it read.
 */
async function readRoadStations(page, label, stations) {
  const roadRuns = [];   // T-0016: what each station's bands read this run
  for (const station of stations) {
    const road = await roadContrast(page, { id: station.id, kind: station.kind });
    roadRuns.push({ id: station.id, bands: road.bands });
    const bands = road.bands.filter((b) => b.gated);
    const bad = bands.filter((b) => b.medianDeltaL < ROAD_MIN_DELTA_L
      || b.perceptible < ROAD_MIN_PERCEPTIBLE);
    const report = road.bands.map((b) => `${b.lo}-${b.hi} m: `
      + (b.nProjected < ROAD_MIN_PROBES ? `projects ${b.nProjected}× (not gated)`
        : `ΔL* ${b.medianDeltaL.toFixed(1)} of ${b.opaqueDeltaL.toFixed(1)} opaque, `
          + `${(b.perceptible * 100).toFixed(0)} % perceptible of ${b.nBare} bare, `
          // R-M1a. Both halves of the owner's ruling, measured beside the bar
          // they are going to join: Weber says how distinguishable the road
          // is whatever the exposure, groundL says whether there is light to
          // distinguish it by. Neither is gated yet — R-M1b sets the bars.
          + `weber ${b.weber.toFixed(4)} (n ${b.weberN}) over ground L* `
          + `${b.groundL.toFixed(1)}, seen ${b.n} of `
          + `${b.nProjected} projected (${b.nBare} clear of flora)`
          + `${b.gated ? '' : ' (reported only)'}`)).join(' · ');
    check(`${label}: the roads reach the screen ${station.what}`,
      bands.length >= station.minBands && bad.length === 0, report);
    console.log(`        ${station.id}: ${report}`);
  }

  // T-0016 (R-M1d) — MOVEMENT AGAINST THE BANK, BOTH DIRECTIONS.
  //
  // Printed, never gated. Every check above has already run and its verdict
  // stands whatever this says; the point is only that a band which collapses
  // inside a passing station stops being invisible. A filtered run banks
  // nothing and compares only what it measured, so `SMOKE_VIEWPORT=mobile`
  // cannot silently retire desktop's half of the baseline.
  const vp = label.split(' ')[0];
  const observed = collectRoadBands(vp, roadRuns, {
    failing: (b) => b.medianDeltaL < ROAD_MIN_DELTA_L || b.perceptible < ROAD_MIN_PERCEPTIBLE,
  });
  Object.assign(ROAD_BAND_OBSERVED, observed);
  // T-0690 — AND TO THE STATIONS THIS INVOCATION READ, not only its viewport.
  //
  // The filter above was written when all three stations sat in one part, so
  // "compares only what THIS invocation measured" was true of it. T-0173 then
  // cut them across parts 7 and 8, and nothing here noticed: a part-filtered
  // run compared the bank's WHOLE viewport against the one station it visited
  // and reported every band it had not been to as `ungated — either the probes
  // stopped projecting or the station moved`. Neither had. `SMOKE_STAGE=8`
  // simply never goes to `south_water` or `from_above`, which are part 7's, and
  // six of the ten movements T-0690 was filed over were exactly that. A report
  // that cries wolf six times in ten is a report nobody reads, which is the one
  // thing a print-only report cannot survive.
  const visited = new Set(stations.map((st) => st.id));
  const bankedHere = Object.fromEntries(
    Object.entries(ROAD_BAND_BANKED).filter(([k]) => {
      const [bankedVp, stationId] = k.split('/');
      return bankedVp === vp && visited.has(stationId);
    }));
  if (!Object.keys(bankedHere).length) {
    console.log(`        road bands: nothing banked for ${vp}`
      + ` at ${[...visited].join(', ')} yet`
      + ' — re-run with --update-road-bands to bank this run (T-0016)');
  } else {
    for (const line of renderRoadBands(compareRoadBands(bankedHere, observed))) {
      console.log(`        ${line}`);
    }
  }
}

// R-A1. How much of the frame the aid has to move at full strength before this
// gate believes the control reaches the render at all.
//
// THE GRID IS THE MEASUREMENT AND IT WAS TAKEN, NOT ASSUMED. The 12² signature
// the confidence view is graded on is the wrong instrument for this one, and
// the first run said so: at `lake_market` the roadway is about a tenth of the
// frame, so a whole-frame cell averages the aid away to a worst of 2 counts
// against a restored residual of 0 — a real signal with no headroom to gate on.
// A finer grid concentrates road pixels into cells that are mostly road without
// changing what is being measured. Mobile 390×780, published mirror, full aid:
//
//   48²  mean 0.26, worst 6      12²  mean 0.29, worst 2
//   restored residual, 48²:  mean 0.00, worst 0
//
// The floors below sit a third under the measured 48² figures and four counts
// above the residual, so "the aid changed the frame" and "the aid changed
// nothing" cannot both be true. Both grids are printed; only 48² is gated.
/**
 * R-W3b(a) — the shadow rig `renderers/web/js/world.js` ships, asserted here as
 * a number rather than read back off itself. Changing the reach or either map
 * size there without changing it here fails the gate, which is the point: the
 * texel size the reach is bought at is the claim, and a rig that quietly
 * stretched one map over more ground would otherwise pass unremarked.
 */
const SHADOW_REACH_M = 240;
const SHADOW_MAP_FULL = 4096;
const SHADOW_MAP_LOW = 2048;
/**
 * T-0115 — and the rig now depends on the scene-detail level, so the gate has
 * to know BOTH rigs rather than one.
 *
 * At `light` the box steps back to the ±120 m the project shipped between
 * R-W3b(a) and R-W5a2, and the map halves with it, which is the whole of what
 * makes the step worth taking: 2·120/2048 is 11.7 cm on desktop and 2·120/1024
 * is 23.4 cm on a phone, both exactly the texel the ±240 m rig resolves. So the
 * assertion below is no longer "the reach is 240" — it is "whichever rig this
 * level asks for is carried AT THE UNCHANGED TEXEL", which is a stronger claim
 * than the one it replaces: it catches a level that bought its reach by
 * blurring the eave a visitor stands under instead of by halving the box.
 *
 * It bites hardest on mobile, which boots at `light` without anybody touching
 * the control, so the phone is the viewport that measures the stepped rig.
 */
const SHADOW_REACH_LIGHT_M = 120;
const shadowRigFor = (level, touch) => {
  const reachM = level === 'light' ? SHADOW_REACH_LIGHT_M : SHADOW_REACH_M;
  const mapSize = (touch ? SHADOW_MAP_LOW : SHADOW_MAP_FULL) * (reachM / SHADOW_REACH_M);
  return { reachM, mapSize, texelM: (2 * reachM) / mapSize };
};
/**
 * THE STAND SET — the cameras the frame budget is gated at (T-0135).
 *
 * Until 2026-08-22 everything this project believed about its own frame cost
 * came from ONE camera: `frame('sauganash_hotel', 26)`, the last move before the
 * scene-detail block. It is a courtyard view of a single hotel with the town
 * mostly behind the camera, and it is not the worst frame a visitor can reach —
 * it is close to the best.
 *
 * That mattered because the number the gate read was getting BETTER as the
 * number a visitor can hit got worse. Three layers were chunked in the week
 * before this ticket (frontage T-0119, enclosures T-0067, yard T-0064) so the
 * frustum can skip what is behind you. At an ordinary stand that is a large win.
 * Down a long street it is a loss: the whole town is in frustum at once, nothing
 * culls, and every chunk that bought the win becomes its own draw call. A guard
 * rail that improves when the thing it guards gets worse is the worst possible
 * shape for a guard rail, and it is why the draw-call ceiling could be raised
 * twice in one afternoon (80 -> 120 -> 140) with every raise honestly argued
 * against a reading now known to be optimistic.
 *
 * So the budget is read at a NAMED SET and gated on the WORST of it. Each stand
 * is here for a stated reason — a way this scene gets expensive that the others
 * do not cover — so the set can be argued with rather than trusted, and so a
 * stand can be added when somebody finds a worse one.
 *
 * MEASURED 2026-08-22 on the source tree at 1280x800, `full`, for the record and
 * for whoever wants to argue with the membership:
 *
 *   Lake at Canal, east      200 calls   1,320,377 tris   <- worst on both axes
 *   the forks, from Wolf Pt  181 calls   1,318,202 tris
 *   South Water at Wells     183 calls   1,267,605 tris
 *   Lake and Market          149 calls   1,112,086 tris
 *   the open aerial          119 calls     971,455 tris
 *   the Sauganash at 26 m    121 calls     960,515 tris   <- the old sole stand
 *   Newberry & Dole's wharf   94 calls     812,603 tris
 *
 * South Water is NOT in the set: it is inside the set's worst on both axes and
 * its shape — an axial street down built frontage — is already carried by Lake
 * at Canal, so it would cost the gate a stand's worth of time and buy no
 * coverage. Newberry & Dole's and the two Sauganash anchors are cheaper still.
 * Both readings are kept here so that judgement is checkable rather than
 * asserted.
 *
 * THE COST, measured on the same day, because a gate nobody can run is not a
 * gate either. Stage 2 of the DESKTOP pass ran **9 m 32 s** without this sweep,
 * against the ten-minute ceiling a steward run's single foreground command has;
 * fifteen more rendered frames of a 1.3-million-triangle scene on CI's software
 * renderer put it over, and the run is killed mid-section. The MOBILE pass runs
 * the whole sweep in 3 m 52 s and is unaffected. That is T-0121 — the four-way
 * stage split has outgrown its sections — and the answer to it is to re-cut the
 * stages, NOT to measure fewer stands: measuring one friendly stand is the
 * defect this set exists to close. T-0166 re-cut the four stages into eight, so
 * this sweep is now inside PART 5 — it was inside part 4 until T-0346, which cut
 * it out into a part of its own after measuring it at 6 m 17 s of a part the
 * ten-minute ceiling was killing outright. T-0167 had measured that part at
 * DESKTOP at **7 m 07 s**, inside the ceiling with 2 m 53 s to spare, so the
 * instruction that used to stand here — run part 4 outside the ceiling, or read
 * the mobile pass instead — is withdrawn. It is a reading and
 * not a constant: these desktop numbers move by minutes between runs on a
 * software renderer, which is why the margin is what this sweep is judged on
 * and why `SMOKE_TIMING=1` exists to re-take it.
 *
 * `kind` is how the harness gets there: `frame` stands a distance off a
 * structure, `anchor` teleports to one of `data/scenes/1835.json`'s authored
 * viewpoints — the same viewpoints the Go-to menu offers a visitor, which is
 * the point. Nothing here is a camera invented for the test.
 */
const STANDS = [
  {
    id: 'sauganash_26', kind: 'frame', target: 'sauganash_hotel', distance: 26,
    label: 'the Sauganash at 26 m',
    // Kept, and kept FIRST, so every figure this project has ever recorded stays
    // comparable with the new reading. It is also the only stand that is not an
    // authored viewpoint, which is why it cannot be the only one.
    why: 'the stand every earlier budget was measured at, kept for continuity',
  },
  {
    id: 'lake_at_canal', kind: 'anchor', target: 'green_tree',
    label: 'Lake Street at Canal, east down the axis',
    // The known worst, and the reason this ticket exists: standing at the west
    // end of Lake Street looking east puts the whole platted town inside one
    // frustum, so every chunked layer pays for all of its chunks and the sun
    // pays for them again.
    why: 'the long axial street — nothing culls, so chunking costs instead of saves',
  },
  {
    id: 'the_forks', kind: 'anchor', target: 'forks',
    label: 'the forks, from Wolf Point',
    // A different expensive shape from an axial street: across open water there
    // is no building to occlude another, so the far bank draws in full. It is
    // within two triangles per thousand of Lake at Canal and it gets there by an
    // unrelated route, which is what makes it worth its place.
    why: 'across open water — no occluders at all, and the far bank draws whole',
  },
  {
    id: 'from_above', kind: 'anchor', target: 'from_above',
    label: 'the open aerial',
    // The ceiling on what the scene can cost AT ALL: everything is in front of
    // the camera by construction. It reads cheaper than the axial views because
    // distance culling and the flora density falloff both bite from 175 m up —
    // which is itself worth gating, because a change that breaks the falloff
    // shows here first.
    why: 'everything in frustum by construction — the whole-scene upper bound',
  },
  {
    id: 'lake_and_market', kind: 'anchor', target: 'lake_market',
    label: 'Lake and Market, the corner itself',
    // Standing IN the densest built corner rather than looking at it: near
    // geometry at full detail, the tier the flora and fence LODs are least able
    // to help with.
    why: 'the densest built corner, stood in rather than looked at',
  },
];
/**
 * R-W5a2 — the whole untextured town is ONE batch, and it must stay one.
 *
 * This is the number the reach above is standing on. R-W3b(a) measured the reach
 * as draw-call-bound because every batch entering the shadow box costs a call in
 * the shadow pass as well as in the colour pass, and 16 batches is what made
 * ±180 m hit the 80-call budget exactly. Merging them is what bought ±240 m, so
 * a change that splits the town back into per-material batches has silently
 * taken the reach's headroom with it — assert the cause here, not only the
 * effect.
 *
 * 1 rather than "≤ 16" because the merge is total: colour and roughness are both
 * per-vertex now and nothing else in the 1,353 measured material slots differs
 * (R-W2a). A textured asset would legitimately raise this, and raising it is
 * then a deliberate edit with a reach measurement beside it.
 */
const STRUCTURE_BATCHES = 1;
/**
 * How many distinct roughness values the merged batch must still carry, and how
 * far the frame must move when they are flattened.
 *
 * The town ships **16** — the batch count R-W5a left behind, which is what those
 * 16 batches were separating on. Set at 12 rather than 16 so a block landing
 * with a finish the town already uses cannot fail the gate, and low enough that
 * a merge which kept two or three finishes still reads as the loss it is.
 *
 * `ROUGHNESS_MIN_WORST` is MEASURED BEFORE IT IS SET, the way R-A1's box says an
 * instrument owes: driving every building vertex to 0.02 moves the worst 48²
 * cell by the figure the run prints beside this assertion, and the floor is set
 * at roughly a third of the smaller viewport's reading.
 */
const ROUGHNESS_VALUES_MIN = 12;
const ROUGHNESS_MIN_WORST = 4;
/**
 * T-0002, the facade tones — how many distinct ones the town must draw, how
 * near two structures have to be to count as neighbours, and how far the frame
 * must move when the tone is wound off.
 *
 * MEASURED BEFORE THEY WERE SET, with `tools/measure_facade_variety.mjs` on the
 * published mirror: **331 distinct tones across 331 structures**, and winding
 * the tone to 0 moves the worst 48² cell by **10** (mean 0.27) at 1280x800. At
 * the smaller viewport the same reading was **7** at the ±10 % jitter this
 * parcel shipped with before the frames said it was too little. The floors are
 * set at 300 tones (a town that lost the jitter and kept only the age silvering
 * would draw about 45), worst 3 and mean 0.03 — under half and a third of the
 * smaller of those readings, the same margins `ROUGHNESS_MIN_WORST` and the
 * road aid took.
 *
 * `FACADE_PAIR_M` is 60 m because that is what "neighbouring" means in a town
 * whose platted blocks are 126 m long: the nearest structure within a block
 * face. The assertion on those pairs is an INVARIANT, not a number — no two
 * neighbours drawn the same colour — because the archetype town had **10 of
 * 321** such pairs identical to the bit and the whole ask is that it has none.
 */
const FACADE_TONES_MIN = 300;
const FACADE_PAIR_M = 60;
const FACADE_MIN_WORST = 3;
const FACADE_MIN_MEAN = 0.03;
/** How many structures must change colour when the tone is wound off: 329 are
 *  eligible today and two are excluded by attestation, so anything near the
 *  town's own size proves the channel is not dead on most of it. */
const FACADE_MOVED_MIN = 300;
/**
 * How much the 48² frame signature must move when the reach is wound back to
 * the pre-R-W3b(a) ±60 m.
 *
 * MEASURED BEFORE IT WAS SET, the way R-A1's box says an instrument owes:
 * `tools/measure_shadow_reach.mjs --stations lake_market --reaches 120,60` on
 * the published mirror moves 104 of 2,304 cells with a worst cell of **8** at
 * 1280×800 over a 2048² map, and 86 cells with a worst of **8** at 390×780 over
 * a 1024² one. Set at 4 — half the smaller of the two, and the same floor R-A1
 * measured the road aid against on the same grid.
 */
const SHADOW_REACH_MIN_WORST = 4;

/** The 48² frame signature THREE other assertions are measured on — the
 *  roughness merge, the facade tone and the shadow reach, each with a floor
 *  derived against this grid and this grid only. It keeps its name and its
 *  value: a finer grid reads a larger worst cell for an identical change, so
 *  moving it would quietly slacken all three at once. R-A1's own reach reading
 *  moved off it — see ROAD_AID_REACH_GRID below. */
const ROAD_AID_GRID = 48;
/**
 * T-0690 — THE GRID R-A1'S REACH IS READ ON, AND WHY IT IS NOT THE 48 ABOVE.
 *
 * The signature averages luma over `grid²` cells, so a roadway occupying about
 * a tenth of the frame is diluted inside every cell it only partly covers and a
 * coarser grid reports a smaller worst cell for the SAME change. R-A1 found
 * that on 2026-08-16 without naming it — the aid scored worst 2 at 12² and
 * worst 6 at 48² with nothing about the scene changed between the two runs —
 * and set its floor at 4 from the 48² desktop reading alone. Mobile was never
 * measured, and mobile is where the assertion has been red since 2026-09-04:
 * the aid moves the 390×780 frame by a worst cell of 3, one short, while the
 * mean clears its own floor comfortably.
 *
 * MEASURED BEFORE IT WAS SET, on the published mirror at `lake_market`, the
 * clock held, by `tools/measure_road_aid.mjs`. Reach worst cell / residual
 * worst cell, aid off → full on → off again:
 *
 *      grid    390×780      1280×800
 *      12²      2 / 0        2 / 0
 *      24²      3 / 0        4 / 0
 *      48²      3 / 0        7 / 0     <- was here; mobile one short of 4
 *      96²      7 / 0       11 / 0     <- here
 *     144²      9 / 0       15 / 0
 *
 * So the aid was never weak — the instrument was blind. The residual is 0 at
 * every grid on both viewports, which is the other half of the reading: this
 * is dilution and not noise, and a finer grid buys signal without buying any.
 *
 * 96² and not 144² because the floor below does not move and 96 already clears
 * it on the WEAKER viewport by the same margin the shipped rule asks for —
 * SHADOW_REACH_MIN_WORST's box states it as "half the smaller of the two", and
 * half of 7 is 3.5. Going finer would buy a headroom no assertion spends.
 */
const ROAD_AID_REACH_GRID = 96;
/** UNCHANGED BY T-0690, on purpose. The gate still asks the aid for four cells
 *  and 0.15 of mean; what changed is that both viewports can now be asked. At
 *  96² the reading is 7 / 0.35 at 390×780 and 11 / 0.28 at 1280×800, so each
 *  floor sits at roughly half the weaker of the two — the rule the shadow-reach
 *  floor beside it was set by — and far above a residual measured at 0. A red
 *  here is now a statement about the aid rather than about the grid. */
const ROAD_AID_MIN_WORST = 4;
const ROAD_AID_MIN_MEAN = 0.15;
// K24. The brightness aid's own floors, and the reason they are not the road
// aid's: exposure moves EVERY pixel, so the 12² whole-frame signature that was
// too coarse for a roadway occupying a tenth of the frame is exactly the right
// instrument here, and a finer grid would only cost time. Measured mobile
// 390×780 on the published mirror at `lake_market`, full aid (+1 stop):
//
//   12²  mean 49.40, worst 51      restored residual, 12²:  mean 0.00, worst 0
//
// That is two orders of magnitude more signal than the road aid's 0.29 at the
// same grid, which is the expected shape: one aid repaints a tenth of the frame
// and the other regrades all of it.
//
// The floors sit at roughly a third of the measured figures and far above the
// restored residual, so "the aid changed the frame" and "the aid changed
// nothing" cannot both be true — R-A1's third assertion, which is the one a
// control wired to nothing passes.
const BRIGHT_AID_GRID = 12;
const BRIGHT_AID_MIN_WORST = 17;
const BRIGHT_AID_MIN_MEAN = 15;
// The calibrated grade, asserted rather than assumed: every band, probe and
// critic frame this suite takes is read here. world.js § BASE_EXPOSURE.
const BASE_EXPOSURE = 0.95;

/** Project the street centrelines, then read R, M and O. Restores what it moved. */
async function roadContrast(page, station) {
  const shot = await page.evaluate((st) => {
    const a = window.__chicago4d;
    a.setAnimationHold(true);
    for (const id of ['hud', 'popup']) {
      const el = document.getElementById(id);
      if (el) { el.dataset.roadHidden = el.style.visibility; el.style.visibility = 'hidden'; }
    }
    if (st.kind === 'intersection') {
      // The visitor's own route: the Go to tab's list is painted at boot, so the
      // button is in the DOM whether or not the panel is open.
      document.querySelector(`[data-jump-id="${st.id}"]`)?.click();
      a.step();
      // Then turn to look ALONG the street being stood on. The arrival pose
      // aims at a fixed bearing, which at a crossing points diagonally into the
      // block and puts no roadway in the frame at all — 0 probes inside 100 m.
      // The bearing is read off the nearest committed centreline segment, so
      // the direction is the dataset's and not a number chosen here.
      const p = a.player;
      let best = null;
      for (const rec of a.streets.records) {
        const path = rec.path;
        for (let i = 1; i < path.length; i++) {
          const A = path[i - 1];
          const B = path[i];
          const dE = B[0] - A[0];
          const dN = B[1] - A[1];
          const len2 = dE * dE + dN * dN;
          const t = len2 ? Math.max(0, Math.min(1,
            ((p.e - A[0]) * dE + (p.n - A[1]) * dN) / len2)) : 0;
          const d = Math.hypot(p.e - (A[0] + t * dE), p.n - (A[1] + t * dN));
          if (!best || d < best.d) best = { d, bearing: (Math.atan2(dE, dN) * 180) / Math.PI };
        }
      }
      if (best) a.walker.teleport({ yaw_deg: (best.bearing + 360) % 360 });
    } else {
      a.goTo(st.id);
    }
    a.step();
    a.step();
    const cam = a.camera;
    cam.updateMatrixWorld(true);
    const w = a.renderer.domElement.clientWidth;
    const h = a.renderer.domElement.clientHeight;
    const v = new cam.position.constructor();
    const out = [];
    // Every four metres along every committed centreline. The lift matches
    // streets.js so the probe reads the ribbon and not the ground under it.
    for (const rec of a.streets.records) {
      const p = rec.path;
      for (let i = 1; i < p.length; i++) {
        const A = p[i - 1];
        const B = p[i];
        const d = Math.hypot(B[0] - A[0], B[1] - A[1]);
        const steps = Math.max(1, Math.round(d / 4));
        for (let s = 0; s <= steps; s++) {
          const t = s / steps;
          const e = A[0] + (B[0] - A[0]) * t;
          const n = A[1] + (B[1] - A[1]) * t;
          if (a.terrain.isWater(e, n)) continue;
          v.set(e, a.terrain.surfaceHeight(e, n) + 0.022, -n);
          const dist = v.distanceTo(cam.position);
          v.project(cam);
          const x = (v.x * 0.5 + 0.5) * w;
          const y = (-v.y * 0.5 + 0.5) * h;
          if (v.z < -1 || v.z > 1 || x < 2 || x >= w - 2 || y < 2 || y >= h - 2) continue;
          out.push({ dist, x, y });
        }
      }
    }
    // The CSS width these coordinates are in. The mobile context runs at
    // deviceScaleFactor 2, so a screenshot is twice this wide and every probe
    // lands in the wrong half of the frame unless it is scaled — which read as
    // "no road is anywhere" rather than as a broken probe, because a mask that
    // matches nothing and a road that paints nothing look identical from here.
    return { probes: out, cssWidth: w };
  }, station);

  const shotR = await page.screenshot({ type: 'png' });
  await page.evaluate(() => {
    const a = window.__chicago4d;
    a.__roadMarkers = [];
    a.streets.group.traverse((o) => {
      if (!o.material) return;
      a.__roadMarkers.push([o, o.material]);
      const marker = new o.material.constructor();
      marker.color.setHex(0x000000);
      marker.emissive?.setHex?.(0xff00ff);
      marker.side = o.material.side;
      marker.transparent = false;
      marker.depthWrite = true;
      marker.polygonOffset = true;
      marker.polygonOffsetFactor = -8;
      marker.polygonOffsetUnits = -32;
      o.material = marker;
    });
    a.step();
  });
  const shotM = await page.screenshot({ type: 'png' });
  // DIAGNOSTIC PASS — the same markers with the sward and the trees hidden. A
  // probe marked here but not in `shotM` is a road that is ON SCREEN and
  // COVERED BY VEGETATION, which the marked-only denominator drops instead of
  // failing.
  await page.evaluate(() => {
    const a = window.__chicago4d;
    a.__floraWas = [a.flora?.group?.visible, a.trees?.group?.visible];
    if (a.flora?.group) a.flora.group.visible = false;
    if (a.trees?.group) a.trees.group.visible = false;
    a.step();
  });
  const shotMF = await page.screenshot({ type: 'png' });
  await page.evaluate(() => {
    const a = window.__chicago4d;
    if (a.flora?.group) a.flora.group.visible = a.__floraWas[0] ?? true;
    if (a.trees?.group) a.trees.group.visible = a.__floraWas[1] ?? true;
    delete a.__floraWas;
    for (const [o, m] of a.__roadMarkers) { o.material.dispose(); o.material = m; }
    delete a.__roadMarkers;
    a.streets.group.visible = false;
    a.step();
  });
  const shotO = await page.screenshot({ type: 'png' });
  // DIAGNOSTIC PASS — the road painted at FULL opacity. A near band that still
  // scores flat here is not an alpha fault: it is the ribbon and the ground
  // sharing a lightness.
  await page.evaluate(() => {
    const a = window.__chicago4d;
    a.streets.group.visible = true;
    a.__roadOpaque = [];
    a.streets.group.traverse((o) => {
      if (!o.material) return;
      a.__roadOpaque.push([o.material, o.material.transparent, o.material.alphaTest,
        o.material.depthWrite]);
      o.material.transparent = false;
      o.material.alphaTest = 0;
      // depthWrite WITH it, exactly as the marker pass does. Leaving it false
      // moves the ribbon into the opaque queue without letting it hold the
      // depth buffer, so the terrain paints back over it and the band reports
      // a 0.0 ceiling under a perfectly healthy road — which is what this
      // measurement read at 100-250 m before the offset above was deepened.
      o.material.depthWrite = true;
      o.material.needsUpdate = true;
    });
    a.step();
  });
  const shotOP = await page.screenshot({ type: 'png' });
  await page.evaluate(() => {
    const a = window.__chicago4d;
    for (const [m, t, at, dw] of a.__roadOpaque) {
      m.transparent = t; m.alphaTest = at; m.depthWrite = dw; m.needsUpdate = true;
    }
    delete a.__roadOpaque;
    a.streets.group.visible = true;
    for (const id of ['hud', 'popup']) {
      const el = document.getElementById(id);
      if (el) { el.style.visibility = el.dataset.roadHidden ?? ''; delete el.dataset.roadHidden; }
    }
    a.step();
    a.setAnimationHold(false);
  });

  const R = decodePng(shotR);
  const M = decodePng(shotM);
  const MF = decodePng(shotMF);
  const O = decodePng(shotO);
  const OP = decodePng(shotOP);
  const scale = R.width / shot.cssWidth;
  const probes = shot.probes.map((p) => ({
    dist: p.dist,
    x: Math.min(R.width - 1, Math.max(0, Math.round(p.x * scale))),
    y: Math.min(R.height - 1, Math.max(0, Math.round(p.y * scale))),
  }));
  // Magenta survives tone mapping as a strongly red-and-blue, weakly green
  // pixel; nothing else in this scene is.
  const isMagenta = (img, x, y) => {
    const i = (y * img.width + x) * 4;
    return img.data[i] > 140 && img.data[i + 2] > 140 && img.data[i + 1] < 110;
  };
  const marked = (x, y) => isMagenta(M, x, y);
  const markedBare = (x, y) => isMagenta(MF, x, y);
  const deltaL = (x, y) => {
    const i = (y * R.width + x) * 4;
    return Math.abs(labL(R.data[i], R.data[i + 1], R.data[i + 2])
      - labL(O.data[i], O.data[i + 1], O.data[i + 2]));
  };
  const deltaLOpaque = (x, y) => {
    const i = (y * R.width + x) * 4;
    return Math.abs(labL(OP.data[i], OP.data[i + 1], OP.data[i + 2])
      - labL(O.data[i], O.data[i + 1], O.data[i + 2]));
  };
  // R-M1a. The same two frames on the other two scales: exposure-invariant
  // contrast, and the absolute light the ground under the road is carrying.
  // Magnitude, not sign — a road that is DARKER than the ground beside it is
  // exactly as distinguishable, and `south_water`'s earth is both in one frame.
  const groundY = (x, y) => {
    const i = (y * R.width + x) * 4;
    return relativeLuminance(O.data[i], O.data[i + 1], O.data[i + 2]);
  };
  const weber = (x, y) => {
    const i = (y * R.width + x) * 4;
    const w = weberContrast(relativeLuminance(R.data[i], R.data[i + 1], R.data[i + 2]),
      groundY(x, y));
    return w === null ? null : Math.abs(w);
  };
  const groundLabL = (x, y) => {
    const i = (y * R.width + x) * 4;
    return labL(O.data[i], O.data[i + 1], O.data[i + 2]);
  };
  const median = (xs) => {
    const s = xs.slice().sort((a, b) => a - b);
    return s.length ? s[Math.floor(s.length / 2)] : 0;
  };
  const bands = ROAD_BANDS.map(([lo, hi]) => {
    const inBand = probes.filter((p) => p.dist >= lo && p.dist < hi);
    const seen = inBand.filter((p) => marked(p.x, p.y));
    const ds = seen.map((p) => deltaL(p.x, p.y));
    const op = seen.map((p) => deltaLOpaque(p.x, p.y));
    const wb = seen.map((p) => weber(p.x, p.y)).filter((w) => w !== null);
    const gl = seen.map((p) => groundLabL(p.x, p.y));
    return {
      lo, hi, n: ds.length,
      // R-BUG3. How many road points landed in the frame at all, and how many
      // of those the marker pass can see once the sward and the trees are
      // taken away. `nProjected` is what the band is GATED on, so a road that
      // is on screen and invisible fails here instead of quietly leaving the
      // sample; `nBare` is what tells occlusion apart from flatness, which is
      // the distinction three gates in a row failed to draw.
      //
      // R-M1c: `nBare` is now also what `perceptible` is SCORED on. See its
      // box below — it was a diagnostic for two parcels before anything
      // divided by it, and the score it replaced could be raised by planting
      // a tree in front of a road.
      nProjected: inBand.length,
      nBare: inBand.filter((p) => markedBare(p.x, p.y)).length,
      // The ceiling: the same probes with the ribbon forced opaque. It says how
      // much contrast the road's own colour has to spend before its alpha
      // spends it, which is what separates "too transparent" from "the same
      // lightness as the ground".
      opaqueDeltaL: median(op),
      medianDeltaL: median(ds),
      // R-M1a, reported and not gated. `weber` is the exposure-invariant half
      // of the owner's ruling and `groundL` is the floor half; R-M1b sets the
      // bars. `weberN` is carried because a band can lose probes to a black
      // ground the ratio cannot be taken against, and a median over a silently
      // shorter sample is how this project has mis-stated a number before.
      weber: median(wb),
      weberN: wb.length,
      groundL: median(gl),
      /**
       * ROADMAP R-M1c. THE DENOMINATOR IS `nBare`, NOT `seen`.
       *
       * This read `/ ds.length` — the probes the marker pass could see THROUGH
       * the vegetation — until 2026-08-16. That makes the score go UP when
       * something stands in front of a faint stretch of road, because the
       * stretch leaves the sample instead of failing in it. **A gate that
       * improves when an occluder hides the thing it measures is dividing by
       * the wrong number**, and this one did, for as long as it has existed.
       *
       * The instrument to fix it was already here and already printing. The
       * `shotMF` pass hides the sward and the trees for exactly this reason and
       * its own comment says so: *"a road that is ON SCREEN and COVERED BY
       * VEGETATION, which the marked-only denominator drops instead of
       * failing."* It was built as a diagnostic and never wired to the score.
       *
       * `nBare` is the right denominator rather than `nProjected` because a
       * road behind a STORE is a road a visitor legitimately cannot see, and
       * demanding it read would be demanding X-ray vision. Vegetation is
       * different: it is ours, it moves when we change it, and it must not be
       * able to launder a faint road out of the sample. `seen ⊆ bare` always,
       * so this can only ever LOWER a score — it is not a route through a bar.
       *
       * Measured on one band across three builds the same evening, where
       * `seen` swung 157→177→163 and the old score swung 62 %→54 %→59 %
       * (aerial, 250–600 m: wood mirrored, wood repaired by R-BUG5b, wood
       * widened by K45(b2)). `nBare` was **182 in all three**, and this score
       * reads **53.3 / 52.7 / 52.7 %**. The town did not change by eight
       * points three times; the sample did.
       */
      /**
       * COUNTED AT THE DECLARED BAR. This used to count `d >= 2` — a second,
       * undeclared threshold sitting beside `ROAD_MIN_DELTA_L`, which is 1.8 and
       * is what this file everywhere else calls the line between a road you can
       * see and one you cannot. Two bars for one question, and the stricter one
       * was the one nobody had written down.
       *
       * It surfaced on T-0005's sloughs (PR #273). Carving them tilts ground
       * normals and darkens the ground about 0.4 L*; `lake_market` at 250–600 m
       * moved its median ΔL* 2.3 → 2.0 and this score fell 99 % → 48 %. That is
       * not a scene falling apart, it is a STEP FUNCTION being crossed: dev's
       * whole distribution sat 0.3 above the step, so a 0.3 shift put half the
       * probes under it. The band still cleared the declared 1.8 bar, and the
       * two renders are indistinguishable — 0.3 L* is far below any perceptual
       * threshold. A gate that fails a band passing its own standard is
       * measuring its own arithmetic.
       *
       * THIS IS AN ALIGNMENT, NOT A RELAXATION, and the difference is checked
       * rather than asserted: at 1.8 the two stations T-0114 already fails —
       * `south_water` 100–250 m and `from_above` 250–600 m — STILL FAIL, on the
       * same measurements, before and after. Had this edit turned a known fault
       * green it would have been the forbidden kind of change, and the re-run is
       * what would have caught it.
       *
       * The bar itself is still T-0033's provisional baseline. Counting at it
       * does not make it derived; it makes there be one of it.
       */
      perceptible: (() => {
        const nBare = inBand.filter((p) => markedBare(p.x, p.y)).length;
        return nBare ? ds.filter((d) => d >= ROAD_MIN_DELTA_L).length / nBare : 0;
      })(),
      gated: inBand.length >= ROAD_MIN_PROBES && hi <= ROAD_GATED_BEYOND_M,
    };
  });
  return { station, bands };
}

const failures = [];
const passes = [];
// T-0060: checks taken inside a stage block, as opposed to the always-on
// scaffolding (page serves, ready, loader problems, completion, page errors,
// vendor) that every invocation takes regardless of SMOKE_STAGE. The summary
// prints both so two staged halves can be audited to add up to an unfiltered
// pass: staged section counts sum, scaffolding counts match.
let inStageWork = false;
let stageWorkChecks = 0;
// T-0167: `SMOKE_TIMING=1` stamps every check line with the elapsed clock.
// A part that overruns the ten-minute ceiling is KILLED, and the wall clock it
// prints at the end is the one reading it never gets to give — so before this,
// the most expensive parts, the ones that actually need cutting, were the only
// ones a profile run learned nothing about. With the stamp on, a killed run's
// output is still a profile of everything it reached, which is what places the
// next cut. Off by default: the gate's output stays byte-comparable between
// runs, and a profile is something you ask for.
const TIMING = !!process.env.SMOKE_TIMING;
const stamp = () => {
  const secs = Math.round((Date.now() - startedAt) / 1000);
  return `[${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}] `;
};
// T-0187: `show` prints the detail on a PASS as well as on a failure, for the
// handful of checks whose measured figure is the thing a run has to be able to
// quote. The sward's outer reach is the case that asked for it: a change to the
// boundary has to be able to say what the reach was before and after, and a
// green line that prints nothing makes that a re-run with an edited gate.
// Deterministic figures only — the output stays comparable between runs.
// A mesh census reads as sixty-odd repetitions of two names, which is a wall of
// text nobody reads, so a name list is reported as a tally: `frontage x1,
// frontage-chunk x60`. Order is first-appearance, so the shared mesh stays at
// the head where the layer puts it.
function tallyNames(names) {
  const counts = new Map();
  for (const n of names ?? []) counts.set(n, (counts.get(n) ?? 0) + 1);
  return [...counts].map(([n, c]) => (c === 1 ? n : `${n} x${c}`)).join(', ');
}

function check(name, cond, detail = '', show = false) {
  if (inStageWork) stageWorkChecks += 1;
  const t = TIMING ? stamp() : '';
  if (cond) {
    passes.push(name);
    console.log(`  pass  ${t}${name}${show && detail ? ` — ${detail}` : ''}`);
  } else { failures.push(name); console.log(`  FAIL  ${t}${name}${detail ? ` — ${detail}` : ''}`); }
}

const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

await new Promise((r) => server.listen(PORT, r));
const base = `http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`;
console.log(`serving ${ROOT} on ${PORT} — ${wantPublished ? 'PUBLISHED mirror '
  + '(compressed assets, visitor layout)' : 'source tree (uncompressed masters)'}\n`);
if (wantPublished && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}

const launchBrowser = () => chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  // SwiftShader is the only GPU here. Chromium finds it unaided, but say so
  // rather than leaving a headless run to chance.
  args: ['--enable-unsafe-swiftshader'],
});

/** How different are two pixel signatures, 0..255 per cell. */
function signatureDistance(a, b) {
  if (!a?.cells || !b?.cells || a.cells.length !== b.cells.length) return Infinity;
  let sum = 0;
  let worst = 0;
  for (let i = 0; i < a.cells.length; i++) {
    const d = Math.abs(a.cells[i] - b.cells[i]);
    sum += d;
    worst = Math.max(worst, d);
  }
  return { mean: sum / a.cells.length, worst };
}

// The gate is both viewports and nothing less. SMOKE_VIEWPORT exists because a
// full pass takes upwards of ten minutes on a software renderer and an agent
// iterating on one half should not have to spend the other half to see it — it
// says so out loud when it is used, so a filtered run cannot be mistaken for the
// gate in a log somebody reads later.
const ONLY = process.env.SMOKE_VIEWPORT || '';
if (ONLY) console.log(`NOT THE FULL GATE — viewports filtered to "${ONLY}"\n`);

// T-0060 — the ten-minute ceiling (ROADMAP § THE RUN BUDGET). A steward run's
// single foreground command is capped at ten minutes, and by 2026-08-18 neither
// viewport's full pass fit: mobile was killed at 570 s at 208 passed, desktop
// at 143, and the check that went unrun was always `zero page errors`, because
// it was the tail. SMOKE_STAGE splits each viewport's body in four at section
// boundaries verified for crossing bindings, so each part fits a command —
// while boot, the page-error check and the vendor checks stay in every
// invocation.
// T-0121 re-cut the four into EIGHT, because the four had eroded: by
// 2026-08-23 three of the desktop quarters ran past the ten-minute ceiling and
// the fourth cleared it by two minutes, so the desktop half a run could reach
// was stage 1 alone. The erosion is monotonic — the town keeps growing — so the
// answer was a re-cut with margin rather than one more boundary nudged along.
// Each of T-0060's four stages was halved at a section boundary re-verified for
// crossing bindings, so PART 2k-1 + PART 2k was exactly T-0060's stage k and the
// mobile pass can still be taken in four commands with the range syntax below.
// T-0167 measured the DESKTOP profile the eight-way cut had never been sized
// from — see ROADMAP § THE RUN BUDGET for the eight readings — and halved the
// one part the profile put inside a minute and a quarter of the ceiling. Part 8
// was the tail, so the ninth part is APPENDED and parts 1-7 keep their numbers:
// the pairing rule survives as 1+2, 3+4, 5+6, 7+8+9, and the mobile recipe's
// last command widens from `7-8` to `7-9`.
// T-0346 cut PART 4 into THREE, and this one could not be an append: the two new
// sections sit in the middle of the body, so parts 5-9 are renumbered 7-11 and
// the old part 4 becomes 4 + 5 + 6. The cut is measured, not guessed — part 4 was
// being killed at the ceiling and 6 m 17 s of its cost was one section, the
// scene-detail ladder, which walks every stand at every tier and cannot be halved
// again without walking the set twice. So the ladder is part 5 on its own and the
// gate-and-chrome tail is part 6. Both boundaries are named section boundaries
// re-verified for crossing bindings: exactly one crossed (part 4's `stats`, read
// for its draw-call ceiling), and part 5 now reads that ceiling itself.
// The pairing rule survives as 1+2, 3+4+5+6, 7+8, 9+10+11 — the same content in
// the same four mobile commands, whose ranges become `1-2 3-6 7-8 9-11`.
// T-0173 HALVED PART 7 and this one could not be an append either, so parts 8-11
// are renumbered 9-12 and the old part 7 becomes 7 + 8. The cut is measured, not
// guessed: profiled with SMOKE_TIMING=1 on the steward runner on 2026-08-30 at
// load 0.8-2.9, part 7 was killed at 9 m 25 s with its last two assertions unrun,
// and 7 m 04 s of its cost was ONE block — the three road-legibility stations,
// each of which teleports to its own viewpoint and screenshots it. No boundary
// between the part's own `// --- ` section headers leaves both sides a margin
// (the best is 7 m 37 s against 1 m 30 s), so the cut falls at the station, which
// is the grain the block is made of and crosses no binding: `roadRuns` is local
// to the block, the movement report built from it is printed rather than gated
// and has always compared only what the invocation measured, and
// `--update-road-bands` merges per band. R-A1's three assertions are taken
// STANDING AT `lake_market`, so that station goes with them: part 7 keeps
// `south_water` and `from_above` at 2 m 13 s + 2 m 02 s, part 8 takes
// `lake_market` at 2 m 49 s plus the aid at 1 m 04 s and the batch merge.
// The pairing rule survives again as 1+2, 3+4+5+6, 7+8+9, 10+11+12 — the same
// content in the same four mobile commands, ranges `1-2 3-6 7-9 10-12`.
// T-0170 HALVED PART 10, the last part on T-0167's profile still over the
// ceiling: measured at 1280x800 on an IDLE runner (load average 0.27-1.48, no
// other Chromium on the box) it was killed at 9 m 20 s with the street readouts
// and the Settings units still to run, so the ten minutes had never contained
// it. It carried no `// --- section ---` headers, which is why T-0167 left it;
// the seams are named now and the cut is the one the profile chose — the ragged
// boundary and everything after it becomes part 11, so old parts 11 and 12 are
// renumbered 12 and 13. `anyStage(7, 10)` becomes `anyStage(7, 10, 11)`: both
// halves read `streetLayer`, the first for the road panels and the second for
// the readouts. The pairing rule is unchanged in content — 1+2, 3+4+5+6, 7+8+9,
// 10+11+12+13 — and the mobile recipe's last range widens from `10-12` to
// `10-13`, still four commands.
const PARTS = 13;
const STAGE = process.env.SMOKE_STAGE || '';
// `3` is one part; `3-4` is a contiguous run of them; `1,5-6` is any set. The
// range form exists so the cheap viewport does not pay eight boots to run a
// body that fits in two commands.
const wantedParts = (() => {
  if (!STAGE) return null;
  const want = new Set();
  for (const tok of STAGE.split(',').map((t) => t.trim()).filter(Boolean)) {
    const m = /^(\d+)(?:-(\d+))?$/.exec(tok);
    if (!m) return tok;
    const lo = Number(m[1]);
    const hi = m[2] === undefined ? lo : Number(m[2]);
    if (lo < 1 || hi > PARTS || lo > hi) return tok;
    for (let n = lo; n <= hi; n++) want.add(n);
  }
  return want.size ? want : null;
})();
if (typeof wantedParts === 'string') {
  console.error(`SMOKE_STAGE must be a part 1..${PARTS}, a range like 3-4, or a `
    + `comma-separated set of those; got "${wantedParts}" in "${STAGE}"`);
  process.exit(2);
}
if (STAGE) console.log(`NOT THE FULL GATE — stages filtered to "${STAGE}" of ${PARTS}\n`);
const stageOn = (n) => !wantedParts || wantedParts.has(n);
// Readability at the guard on a reading shared by several parts: `anyStage(7, 10, 11)`
// says which parts need it, and adding a part to that list is the whole edit.
const anyStage = (...ns) => ns.some(stageOn);
const startedAt = Date.now();

for (const [label, viewport, touch] of [
  ['mobile 390x780', { width: 390, height: 780 }, true],
  ['desktop 1280x800', { width: 1280, height: 800 }, false],
].filter(([label]) => !ONLY || label.includes(ONLY))) {
  console.log(`${label}:`);
  // Give each release viewport a fresh renderer process. Reusing one process
  // makes a software-only run measure the previous viewport's accumulated GPU
  // state and can starve the second walk test down to a single frame.
  const browser = await launchBrowser();
  const ctx = await browser.newContext({
    viewport,
    hasTouch: touch,
    isMobile: false,          // isMobile forces mobile emulation Chromium-side
    deviceScaleFactor: touch ? 2 : 1,
  });
  const page = await ctx.newPage();
  // A few checks import an app module directly to exercise a pure function. The
  // path to those modules differs between the source tree and the published
  // mirror, so it is handed to the page rather than written into each call.
  await page.addInitScript((b) => { window.__MODULE_BASE = b; }, MODULE_BASE);
  // Playwright's default 30 s action timeout is not an assertion, and on this
  // scene it had quietly become one. A click waits for the element to be stable
  // across animation frames and then hit-tests it, and every one of those steps
  // queues behind the render loop — which on a software renderer drawing 533 000
  // triangles takes 0.5–1.1 s per frame (measured, both viewports). So opening
  // the menu was timing out on a button that `elementFromPoint` returned as the
  // topmost element at its own centre, with no pointer lock, the page visible
  // and focused: nothing was wrong with the page and everything was wrong with
  // the budget. The desktop half of the gate had stopped running entirely
  // because of it. Ninety seconds is room for a slow machine, not permission
  // for a broken control: a click that never lands still fails, three times
  // slower.
  //
  // IT IS NOT RAISED AGAIN, AND T-0215 IS WHY. On 2026-08-27 the same starvation
  // took the desktop half down again, and the honest reading is that a budget
  // measured in frames is the wrong instrument for a scene whose frame cost is
  // set by whatever else the machine is doing (17-27 s per frame, measured, on a
  // runner where the identical scene also drew frames in 29 ms). Raising 90 to
  // 180 buys one more town-sized month and pays for it in wall clock against a
  // ten-minute per-command ceiling this gate has already been re-cut for twice.
  // The answer is `clickChrome` below — not paying for the frames at all where
  // the frames are not the subject. This number stays what it is: the backstop
  // for the clicks that must remain a visitor's own mouse.
  page.setDefaultTimeout(90_000);

  // A fresh boot stands at the GATE SCREEN, and the part that enters the town
  // is part 6's "the gate and the chrome" section (part 4's until T-0346). Every part after it that
  // measures a page.screenshot frame (those include DOM overlays; the
  // GL-capture checks do not) or clicks the panel chrome (which has no layout
  // at all while the gate stands, so a click waits ninety seconds for a
  // zero-size button and dies) has to stand where the full run stands: gate
  // entered, pointer free, guide down. Idempotent by construction — in a full
  // run every branch below is a no-op — which is what lets it be called at the
  // head of four different parts. T-0060 wrote it inline twice; T-0121 needed
  // it twice more and made it one function instead of four copies.
  const enterTown = () => page.evaluate(async () => {
    if (!document.getElementById('gate').hasAttribute('hidden')) {
      document.getElementById('gate-btn')?.click();
      await new Promise((r) => setTimeout(r, 150));
      document.exitPointerLock?.();
    }
    const help = document.getElementById('control-help');
    if (help && !help.hasAttribute('hidden')) {
      document.getElementById('control-help-gotit')?.click();
    }
  });

  // A click on the HUD chrome that does not have to race the render loop for it.
  //
  // THE HAZARD THE 90 s ABOVE ONLY POSTPONED. `page.click` is frame-bound three
  // ways over: it polls the target's box on consecutive animation frames until it
  // holds still, then scrolls it into view, then hit-tests it, and every one of
  // those steps queues behind whatever the render loop is doing. STATUS
  // 2026-08-13 raised the budget to 90 s for exactly that and said, in writing,
  // that it was **a standing hazard and not a fixed one**: *"the same starvation
  // will return as the town grows, and the next symptom will again look like a UI
  // bug rather than a budget."* It returned on 2026-08-27 (T-0215), and it
  // returned looking precisely like that: `SMOKE_VIEWPORT=desktop SMOKE_STAGE=8`
  // died on its FIRST click, on the Settings tab, before a single one of part 8's
  // assertions had run — and three agents in one day read that as the What's-new
  // panel being broken. It was not. Driven by hand at the same moment the gate was
  // dying, the panel opened and painted all 272 releases and cleared its unread
  // dot; the tab was the topmost element at its own centre with no pointer lock.
  // What had moved was the cost of a frame: **17.0 / 0.03 / 0.33 / 21.5 / 20.2 /
  // 0.12 / 4.4 / 22.3 / 12.2 / 26.6 seconds**, measured on the loaded runner
  // against the 0.46-1.10 s this file's comment above records. The 29 ms frames
  // in that list are the proof it is the machine and not the scene — the renderer
  // draws fast when it is given the CPU, and it was not being given it. Another
  // number is not the answer to that; not needing the frames is. And note there
  // is no trigger to find: timed at the same load, that identical click landed in
  // 10.9 s cold, 28.4 s settled and 53.8 s after a reload before it blew ninety
  // in the gate. It is a distribution with a tail across the budget, so any
  // budget is a coin toss and only removing the dependency ends it.
  //
  // NOTHING IS SKIPPED, AND THAT IS THE POINT. Everything `page.click` asserts
  // implicitly is asserted here explicitly, in the page, in ONE round trip: the
  // element exists, is enabled, has a real box, and is the topmost thing at its
  // own centre. That last one is T-0108's assertion verbatim — a control the
  // HUD's `pointer-events: none` swallows returns the CANVAS from
  // `elementFromPoint` and fails here exactly as it fails a visitor's mouse — and
  // it now fails in one round trip with a sentence naming what covered it,
  // instead of in ninety seconds with a call log that reads like a broken
  // control. A real `page.click` stays the instrument wherever the trusted event
  // ITSELF is the subject: the confidence menu in part 6 is the case, and it says
  // so where it stands.
  const clickChrome = async (sel) => {
    const why = await page.evaluate(async (s) => {
      const el = document.querySelector(s);
      if (!el) return `nothing matches ${s}`;
      if (el.disabled) return `${s} is disabled`;
      // T-0701: the drawer SLIDES. `#panel[hidden]` keeps its layout and sits at
      // translateX(102%), and opening it is a .24 s transform — so for a quarter
      // of a second after `setPanel(true)` a tab has a real box whose centre is
      // off the right edge of the viewport, and `elementFromPoint` answers
      // `null` for it. A visitor clicks a drawer that has arrived; so does this.
      // Waited for, never assumed: the hit-test below still runs on the settled
      // box, and a control that is genuinely covered still fails here.
      const drawer = el.closest('#panel');
      if (drawer) {
        for (let i = 0; i < 40 && getComputedStyle(drawer).transform !== 'none'; i++) {
          await new Promise((r) => setTimeout(r, 50));
        }
      }
      // The same scroll `page.click` would do, in the same round trip as the
      // reading — a result row far down the Go-to list is off the panel's
      // viewport until this runs, and `elementFromPoint` would then answer for
      // whatever is at those coordinates instead.
      el.scrollIntoView({ block: 'center', inline: 'center' });
      const b = el.getBoundingClientRect();
      if (b.width < 1 || b.height < 1) {
        return `${s} has no box (${Math.round(b.width)}x${Math.round(b.height)})`;
      }
      const top = document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2);
      if (!top || !(top === el || el.contains(top))) {
        const cls = top && typeof top.className === 'string' ? top.className : '';
        // NAME THE OVERLAY, NOT JUST THE TAG IT ENDS IN (T-0369). The first
        // report of this failure said only `<h2>`, and an `<h2>` is a heading
        // inside something — the thing worth naming is the panel that heading
        // belongs to. Walking up to the nearest ancestor carrying an id turns
        // "covered by <h2>" into "covered by <h2> inside #popup", which is the
        // whole diagnosis of a stale overlay left open by an earlier stage.
        let owner = top;
        while (owner && !owner.id && owner !== document.body) owner = owner.parentElement;
        const inside = owner && owner.id && owner !== el ? ` inside #${owner.id}` : '';
        return `${s} is covered at its own centre by `
          + `<${top ? top.tagName.toLowerCase() : 'nothing'}${cls ? ` class="${cls}"` : ''}>${inside}`;
      }
      // A real mouse press FOCUSES a focusable control, and an untrusted
      // `.click()` does not — which is a difference the suite already depends on
      // and which this helper got wrong on its first run, honestly and visibly.
      // Part 8 closes the panel and then presses `g`, and `g` only reaches the
      // window shortcut if focus has left the Go-to search box first: the shared
      // `isTyping(e.target)` guard swallows it otherwise, which is the whole
      // point of that guard. Without this line the panel stayed shut, `g` did
      // nothing, and the next reading was a result row with a 0x0 box. So this
      // is fidelity to the click being replaced, not a convenience.
      if (typeof el.focus === 'function') el.focus({ preventScroll: true });
      el.click();
      return null;
    }, sel);
    if (why) throw new Error(`clickChrome: ${why}`);
  };

  const errors = [];
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.message || e}`));
  page.on('response', (r) => {
    if (r.status() >= 400) errors.push(`HTTP ${r.status()} ${r.url()}`);
  });
  page.on('requestfailed', (r) => {
    const why = r.failure()?.errorText || '';
    if (!/ERR_ABORTED/.test(why)) errors.push(`request failed (${why}) ${r.url()}`);
  });
  page.on('console', (m) => {
    const t = m.text();
    if (m.type() === 'error' && !t.startsWith('Failed to load resource')) {
      errors.push(`console.error: ${t}`);
    }
  });

  const res = await page.goto(base, { waitUntil: 'domcontentloaded' });
  check(`${label}: page serves`, res.status() === 200, `status ${res.status()} at ${base}`);

  // --- boot ---------------------------------------------------------------
  let ready = false;
  let thrown = null;
  try {
    await page.waitForFunction(() => window.__chicago4d?.ready === true, { timeout: 30000 });
    ready = true;
  } catch {
    const state = await page.evaluate(() => ({
      error: window.__chicago4d?.error ?? null,
      problems: window.__chicago4d?.problems ?? [],
    })).catch(() => ({}));
    check(`${label}: scene reaches ready`, false,
      `${state.error ?? 'timed out'} | ${(state.problems || []).slice(0, 3).join(' | ')}`);
  }
  if (ready) check(`${label}: scene reaches ready`, true);

  if (ready) {
    const problems = await page.evaluate(() => window.__chicago4d.problems);
    // Provisional placement and placeholder-asset notes are expected findings,
    // not defects. `review_required` is also a deliberate release blocker, but
    // pin its exact records before excluding it so a new blocker cannot hide in
    // the general integration-problem list.
    const reviews = problems.filter((p) => /review_required is set/.test(p));
    const expectedReviews = await page.evaluate(() => [...window.__chicago4d.registry.values()]
      .filter((r) => r.sidecar?.review_required)
      .map((r) => r.sidecar.id)
      .sort());
    const reportedReviews = reviews.map((p) => p.split(':', 1)[0]).sort();
    check(`${label}: the scene declares its exact consultation blockers`,
      expectedReviews.length > 0
      && JSON.stringify(reportedReviews) === JSON.stringify(expectedReviews),
      `reported ${JSON.stringify(reportedReviews)}, expected ${JSON.stringify(expectedReviews)}`);
    const hard = problems.filter((p) => !/provisional|PLACEHOLDER|placeholder|review_required is set/i.test(p));
    check(`${label}: no unexpected loader problems`, hard.length === 0, hard.slice(0, 3).join(' | '));

    const structures = await page.evaluate(() => window.__chicago4d.registry.size);
    check(`${label}: scene has structures`, structures > 0, `${structures} loaded`);

    /**
     * DRAWN AGAINST INDEXED (T-1126). "The scene has structures" passes with one
     * building standing and three hundred and eighty missing, which is close to
     * the shape of the fault this came from: one auction room failed to fetch,
     * the walk went on looking finished, and the only detector was the owner
     * standing in front of the hole. The roll is the renderer's own count of how
     * many structures it was told to place against how many put geometry into a
     * batch, so the gate can now read the number rather than the adjective.
     */
    const roll = await page.evaluate(() => window.__chicago4d.roll);
    check(`${label}: every structure that should draw, drew`,
      !!roll && roll.expected > 0 && roll.standing === roll.expected,
      roll ? `${roll.standing} of ${roll.expected} standing; missing `
        + `${roll.missing.slice(0, 5).join(', ')}` : 'no roll call was taken');

    // T-0848 — THE POSE EVERY DELTA CHECK IS CALIBRATED AT, read here because
    // this is the last line before the stage-guarded body, and nothing above it
    // has moved the visitor. A *reaches the render* check winds a shipped value
    // off, photographs the frame and asserts the picture MOVED by at least so
    // much; what it is actually measuring is whatever the camera happens to be
    // pointed at, so its threshold is a number about a VIEW. The readings below
    // teleport to their own viewpoints and do not put the visitor back, and the
    // expensive ones are guarded on which PARTS were selected — so `SMOKE_STAGE=9`
    // photographed the boot view and passed (worst cell 10 and 22), while
    // `SMOKE_STAGE=9-12` photographed wherever part 10's shared street reading
    // had left the visitor and collapsed to 2, on a tree where nothing about
    // facades or shadows had changed. Since `smoke_budget.mjs --for-diff` packs
    // parts into ranges precisely because that is what fits under the foreground
    // ceiling, the packing the tooling recommends was the one packing those
    // checks could not survive. A delta check now states the view it needs and
    // takes it (`standAtBootPose`), which is the fix: the frame it photographs
    // is the same frame whichever other parts are selected.
    const bootPose = await page.evaluate(() => {
      const st = window.__chicago4d.walker.state;
      return {
        local_e: st.e,
        local_n: st.n,
        yaw_deg: window.__chicago4d.walker.bearingDeg,
        pitch_deg: (st.pitch * 180) / Math.PI,
        altitude_m: st.flying ? st.altitude : null,
      };
    });
    // Stand where the thresholds were measured. `step()` settles the walker the
    // same way the readings above do, so the first capture is not of a frame
    // caught mid-arrival.
    const standAtBootPose = async () => {
      await page.evaluate((pose) => {
        window.__chicago4d.walker.teleport(pose);
        window.__chicago4d.step();
      }, bootPose);
    };

    // ======================================================================
    // T-0060 — everything below, to the end of this viewport's body, runs in
    // four stages so each fits a ten-minute command. The sections are NOT
    // re-indented inside the stage braces on purpose: wrapping ~6,400 lines
    // would destroy blame and make the diff that introduced this unreviewable.
    // The try/catch is part of the same repair — a throw mid-suite used to
    // kill the process before the page-error check, the summary and the exit
    // code; now it is a recorded FAIL and the tail still runs.
    // ======================================================================

    // Read once, used in TWO stages: stage 1's "traced river loaded" check
    // and stage 2's terrain-problem check (R-BUG3c) share this one reading.
    // It crosses a stage boundary — found because a filtered run threw
    // ReferenceError on it; the indent-anchored scans (the ticket's and this
    // run's first) both missed it, sitting as it was at column 0 — so it is
    // taken here, before the splits: a scene fact settled at ready, cheap to
    // read, identical whenever it is taken.
    const terrainLoad = await page.evaluate(() => {
      const api = window.__chicago4d;
      let water = null;
      let groundTiles = 0;
      api.scene3d.traverse((o) => {
        if (!o.isMesh) return;
        if (/^water__/.test(o.name || '')) water = o;
        if (/^terrain__/.test(o.name || '')) groundTiles += 1;
      });
      let box = null;
      if (water) {
        water.geometry.computeBoundingBox();
        const b = water.geometry.boundingBox;
        box = { w: +(b.max.x - b.min.x).toFixed(1), d: +(b.max.z - b.min.z).toFixed(1) };
      }
      return { box, groundTiles,
               // ANCHORED, and the anchor is the whole point. `js/terrain.js` emits
               // `terrain <epoch>: …` and `water: …`, always at the start of the
               // string, so a problem ABOUT the ground or the river is recognisable
               // by its subject. The unanchored `/terrain|water/i` this replaced
               // matched the word anywhere, and the first block of the town whose
               // id contains one of them — `blk_south_water_franklin`, ROADMAP T-A8
               // — turned two ordinary placeholder-asset notes into a reported
               // terrain load failure. Five of the ten open blocks are
               // `blk_south_water_*`, so it would have fired on each of them in
               // turn. This narrows what the filter MATCHES, not what the check
               // ALLOWS: a real terrain or water problem still has to be zero.
               terrainProblems: api.problems.filter((t) => /^\s*(terrain|water)\b/i.test(t)) };
    });

    // Read once, shared by parts 7 and 9 (T-0060, re-cut by T-0121 and T-0346): the street
    // layer, the flora rooted around it, the building anchors and the two
    // readouts. Its checks span both of those parts, so the reading is taken
    // before the split — and skipped when neither runs, because it is the most
    // expensive single evaluate in the file. It teleports to its own
    // viewpoints, so it does not care what ran before it.
    //
    // T-0848: it does not put the visitor BACK, though, and that half matters as
    // much. Because the guard is on which parts were SELECTED, this block runs
    // for `SMOKE_STAGE=9-12` and not for `SMOKE_STAGE=9`, so it is the one thing
    // in the file that can change what a LATER part photographs according to
    // what a range asked for. Anything downstream that measures a frame must
    // state its own view — see `standAtBootPose` above.
    //
    // T-0121 narrowed the guard from "stage 3 or stage 4" to the two PARTS that
    // actually read it: parts 9 and 11 hold no reference to `streetLayer`, and
    // under the old guard each of them would have paid for it anyway — four
    // times over the desktop pass instead of twice, on the very reading this
    // gate can least afford.
    let streetLayer = null;
    if (anyStage(7, 10, 11)) {
      streetLayer = await page.evaluate(() => {
        const a = window.__chicago4d;
        // Sample the dynamic flora from a known dry South Division viewpoint.
        // The preceding overview check deliberately teleports over the river;
        // after the deep-channel vegetation fix an empty sward there is correct.
        a.walker.teleport({ local_e: 107, local_n: -103, yaw_deg: 180 });
        a.step();
        let vertices = 0;
        let worstDrape = 0;
        let wetVertices = 0;
        a.streets.group.traverse((o) => {
          const pos = o.geometry?.getAttribute?.('position');
          if (!pos) return;
          vertices += pos.count;
          const step = Math.max(1, Math.floor(pos.count / 900));
          for (let i = 0; i < pos.count; i += step) {
            const e = pos.getX(i);
            const n = -pos.getZ(i);
            worstDrape = Math.max(worstDrape,
              Math.abs(pos.getY(i) - a.terrain.surfaceHeight(e, n) - 0.022));
            if (a.terrain.isWater(e, n)) wetVertices++;
          }
        });

        // The former far-field canopy was a solid horizontal mesh at plant-top
        // height. It looked like a second terrain layer, hid the bases of the
        // buildings and let the visitor walk underneath it. The actual flora is
        // instanced geometry whose matrices must begin on the same terrain
        // sampler the buildings and streets use (or at the water surface for
        // emergent plants). There must be no replacement canopy slab.
        const canopyPresent = !!a.flora.group.getObjectByName('flora-canopy');
        const waterY = a.terrain.heightfield?.meta?.water_surface_m ?? 0;
        let rootedPlants = 0;
        let worstPlantRoot = 0;
        let waterPlants = 0;
        let deepWaterPlants = 0;
        for (const name of ['flora-near', 'flora-mid', 'flora-forb', 'flora-rosette',
          'flora-shrub']) {
          const mesh = a.flora.group.getObjectByName(name);
          const matrix = mesh?.instanceMatrix?.array;
          if (!matrix) continue;
          for (let i = 0; i < mesh.count; i++) {
            const o = i * 16;
            const e = matrix[o + 12];
            const y = matrix[o + 13];
            const n = -matrix[o + 14];
            const expected = a.terrain.isWater(e, n)
              ? waterY : a.terrain.surfaceHeight(e, n);
            worstPlantRoot = Math.max(worstPlantRoot, Math.abs(y - expected));
            if (a.terrain.isWater(e, n)) {
              waterPlants++;
              if (a.flora.shoreDistance(e, n) > 8.01) deepWaterPlants++;
            }
            rootedPlants++;
          }
        }
        const treeStations = a.trees.group.userData.stations ?? [];
        const wetTreeStations = treeStations.filter(({ e, n }) => a.terrain.isWater(e, n));
        // ...and the stronger question the river mask does not answer. `isWater`
        // asks whether the heightfield is below SHORE_Y, 100 mm UNDER the water
        // plane, so a stem rooted in that band passes the mask and still renders
        // standing in the river. Every station carries the ground height the
        // renderer built it at; the water surface comes from the epoch record.
        const drownedTreeStations = treeStations.filter(({ e, n, y }) => (
          (typeof y === 'number' ? y : a.terrain.surfaceHeight(e, n)) < waterY
        ));
        const lowestTreeStation = treeStations.reduce(
          (lo, { e, n, y }) => Math.min(lo, typeof y === 'number' ? y : a.terrain.surfaceHeight(e, n)),
          Infinity,
        );

        let anchoredBuildings = 0;
        let worstBuildingAnchor = 0;
        let deepestBedding = 0;
        let exchangeAnchor = null;
        for (const [id, record] of a.registry.entries()) {
          const p = record.sidecar?.placement;
          const at = a.buildings.positionOf(id);
          if (!p || !at) continue;
          // The anchor is the LOWEST ground under the footprint, not the ground at
          // the origin — see buildings.groundUnder(). So the origin sample is a
          // CEILING here, not an equality: a building on a slope beds down to its
          // downhill corner and sits below its own origin by up to the relief
          // beneath it. What this still pins is that the anchor comes from the
          // terrain sampler at all, and never floats above it; the companion check
          // "no building hovers above the ground beneath it" measures the corners
          // through the real instance matrix.
          const expected = p.vertical_anchor === 'water'
            ? waterY : a.terrain.surfaceHeight(p.local_e ?? 0, p.local_n ?? 0);
          // Signed: above the origin's ground is a fault, below it is bedding.
          worstBuildingAnchor = Math.max(worstBuildingAnchor, at.y - expected);
          deepestBedding = Math.max(deepestBedding, expected - at.y);
          const error = Math.abs(at.y - expected);
          anchoredBuildings++;
          if (id === 'exchange_coffee_house') {
            // Flat ground here, so the origin sample and the footprint minimum
            // agree and the equality is still the right assertion for this one.
            exchangeAnchor = { y: at.y, expected, error };
          }
        }

        // Dry land has one value no matter which compatibility entry point an
        // older caller uses. The walk-specific sampler differs only over water,
        // where it deliberately supplies the navigation barrier.
        let worstDrySurfaceAlias = 0;
        for (const [e, n] of [[319.12, -90.66], [140, -35], [89.2, -110.4]]) {
          if (!a.terrain.isWater(e, n)) {
            worstDrySurfaceAlias = Math.max(worstDrySurfaceAlias,
              Math.abs(a.terrain.surfaceHeight(e, n) - a.terrain.walkHeight(e, n)));
          }
        }
        a.walker.teleport({ local_e: 452.5, local_n: -110.4, yaw_deg: 0 });
        a.step();
        const crossing = {
          state: a.navigation.streetState,
          historic: document.getElementById('street-historic')?.textContent,
          modern: document.getElementById('street-modern')?.textContent,
          shown: !document.getElementById('street-readout')?.hasAttribute('hidden'),
        };
        a.walker.teleport({ local_e: 89.2, local_n: -180, yaw_deg: 0 });
        a.step();
        const approaching = {
          state: a.navigation.streetState,
          historic: document.getElementById('street-historic')?.textContent,
          modern: document.getElementById('street-modern')?.textContent,
          ahead: document.getElementById('street-approach')?.textContent,
        };
        // R-BUG4. A panel used to be DELETED outright when any one of its four
        // corners fell on water, which took the dry part of the panel with it —
        // the owner saw it as a clean-edged green hole punched through South
        // Water Street. It is clipped at the waterline now. This re-derives the
        // rule's own arithmetic and asserts the ribbon carries every panel whose
        // CENTRELINE is dry, so a future "simplification" back to dropping the
        // panel fails here instead of in a screenshot.
        const STEP = 2.25;
        const MIN_W = 1.0;
        let dryCentrelinePanels = 0;
        let clippedPanels = 0;
        let slivers = 0;
        // T-0111. Re-derived from the line the module DRAWS from — the worn
        // wheel line where a street commits one, the platted line everywhere
        // else (`drawn` is `path` unless `drawn_track_local_enu_m` is
        // authored). Re-deriving from the plat would count panels the module
        // never emitted and turn an authored track into a false failure here.
        for (const rec of a.streets.records) {
          const half = (rec.track_width_m ?? 10.5) * 0.5;
          const line = rec.drawn ?? rec.path;
          const pts = [];
          for (let i = 1; i < line.length; i++) {
            const A = line[i - 1];
            const B = line[i];
            const d = Math.hypot(B[0] - A[0], B[1] - A[1]);
            const c = Math.max(1, Math.ceil(d / STEP));
            for (let j = 0; j < c; j++) {
              if (!pts.length) pts.push([A[0], A[1]]);
              const t = (j + 1) / c;
              pts.push([A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t]);
            }
          }
          for (let i = 1; i < pts.length; i++) {
            const A = pts[i - 1];
            const B = pts[i];
            const de = B[0] - A[0];
            const dn = B[1] - A[1];
            const L = Math.hypot(de, dn);
            if (L < 1e-5) continue;
            if (a.terrain.isWater(A[0], A[1]) || a.terrain.isWater(B[0], B[1])) continue;
            dryCentrelinePanels++;
            const ue = -dn / L;
            const un = de / L;
            const reach = (e0, n0, se, sn) => {
              if (!a.terrain.isWater(e0 + se * half, n0 + sn * half)) return half;
              let lo = 0;
              let hi = half;
              for (let k = 0; k < 6; k++) {
                const mid = (lo + hi) * 0.5;
                if (a.terrain.isWater(e0 + se * mid, n0 + sn * mid)) hi = mid;
                else lo = mid;
              }
              return lo;
            };
            const aw = reach(A[0], A[1], ue, un) + reach(A[0], A[1], -ue, -un);
            const bw = reach(B[0], B[1], ue, un) + reach(B[0], B[1], -ue, -un);
            if (aw < half * 2 - 1e-6 || bw < half * 2 - 1e-6) clippedPanels++;
            if (aw < MIN_W || bw < MIN_W) slivers++;
          }
        }
        // T-0110. A panel is 6 indices only until it refines, so the module
        // counts its own panels now — index arithmetic would misread refinement
        // as extra roadway.
        const emittedQuads = a.streets.stats?.panels ?? NaN;
        const refinedPanels = a.streets.stats?.refinedPanels ?? NaN;

        // T-0110, the regression the vertex-drape gate above cannot see: the
        // ground rising THROUGH a panel between its vertices. T-0046's approach
        // fills rose through the planar ribbon by up to 1.49 m — every vertex
        // perfectly draped, the road erased by the depth test — and the owner
        // read it as "grass triangles" and a road "ending" short of the deck.
        // Probed at the half-points of every street triangle: refinement holds
        // the interior miss under DRAPE_TOL_M except two nose-tip panels at the
        // waterline (0.21 m, under the deck ends), so the bar is 0.35 — a third
        // of the failure this gate exists to catch, with headroom over the
        // measured worst. Off-grid probes are skipped: no sample, no verdict.
        let worstSink = 0;
        a.streets.group.traverse((o) => {
          const pos = o.geometry?.getAttribute?.('position');
          const idx = o.geometry?.index;
          if (!pos || !idx) return;
          for (let i = 0; i < idx.count; i += 3) {
            const tri = [idx.getX(i), idx.getX(i + 1), idx.getX(i + 2)];
            const pt = tri.map((v) => [pos.getX(v), pos.getY(v), -pos.getZ(v)]);
            // A triangle with a vertex off the grid stands on the fallback
            // height, not a measurement — the map-border cliff is a border
            // condition, not a drape defect, and the refiner refuses those
            // panels for the same reason.
            if (pt.some(([e, , n]) => !a.terrain.inBounds(e, n))) continue;
            for (const [wa, wb, wc] of [[0.5, 0.5, 0], [0, 0.5, 0.5], [0.5, 0, 0.5],
              [1 / 3, 1 / 3, 1 / 3]]) {
              const e = pt[0][0] * wa + pt[1][0] * wb + pt[2][0] * wc;
              const n = pt[0][2] * wa + pt[1][2] * wb + pt[2][2] * wc;
              if (!a.terrain.inBounds(e, n)) continue;
              const y = pt[0][1] * wa + pt[1][1] * wb + pt[2][1] * wc;
              worstSink = Math.max(worstSink,
                a.terrain.surfaceHeight(e, n) + 0.022 - y);
            }
          }
        });

        // T-0110, the join itself: the worn track must run onto each bridge
        // approach and meet the deck. Stations march the street's own centreline
        // up both North Branch approaches (deck ends e −117.5 / −45.67, T-0046's
        // terrain approaches) and up the Dearborn drawbridge fill.
        // Each station must land inside a drawn road triangle in plan.
        //
        // T-0111 CARRIED THE DEARBORN STATIONS THE LAST 2.7 M. They used to
        // stop at n 17.5 because the street record itself stopped at n 18, and
        // the comment here said so: the bare crest between the ribbon's end and
        // the causeway was outside what this gate could see. The worn track is
        // now drawn from `drawn_track_local_enu_m` onto the deck's own south
        // edge at [697.65, 20.70], so the stations run to n 20.5 — half a metre
        // short of the boards, which is the last ground that is ground — and
        // they are taken on the line the ribbon is drawn from, since a station
        // on the plat line past n 18 is asking about a place the plat does not
        // reach.
        const covered = (e, n) => {
          let hit = false;
          a.streets.group.traverse((o) => {
            if (hit) return;
            const pos = o.geometry?.getAttribute?.('position');
            const idx = o.geometry?.index;
            if (!pos || !idx) return;
            for (let i = 0; i < idx.count && !hit; i += 3) {
              const p = [idx.getX(i), idx.getX(i + 1), idx.getX(i + 2)]
                .map((v) => [pos.getX(v), -pos.getZ(v)]);
              const s = (A, B) => (B[0] - A[0]) * (n - A[1]) - (B[1] - A[1]) * (e - A[0]);
              const d0 = s(p[0], p[1]);
              const d1 = s(p[1], p[2]);
              const d2 = s(p[2], p[0]);
              hit = !((d0 < 0 || d1 < 0 || d2 < 0) && (d0 > 0 || d1 > 0 || d2 > 0));
            }
          });
          return hit;
        };
        const centreAt = (id, axis, value) => {
          const rec = a.streets.records.find((r) => r.id === id);
          const k = axis === 'e' ? 0 : 1;
          const line = rec.drawn ?? rec.path;
          for (let i = 1; i < line.length; i++) {
            const [A, B] = [line[i - 1], line[i]];
            const lo = Math.min(A[k], B[k]);
            const hi = Math.max(A[k], B[k]);
            if (value < lo || value > hi) continue;
            const t = (value - A[k]) / (B[k] - A[k] || 1e-9);
            return [A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t];
          }
          return null;
        };
        const approachGaps = [];
        for (let e = -135; e <= -118; e += 1) {
          const p = centreAt('kinzie', 'e', e);
          if (!p || !covered(p[0], p[1])) approachGaps.push(`kinzie w ${e}`);
        }
        for (let e = -45; e <= -32; e += 1) {
          const p = centreAt('kinzie', 'e', e);
          if (!p || !covered(p[0], p[1])) approachGaps.push(`kinzie e ${e}`);
        }
        for (let n = 8; n <= 20.5; n += 0.5) {
          const p = centreAt('dearborn', 'n', n);
          if (!p || !covered(p[0], p[1])) approachGaps.push(`dearborn ${n}`);
        }

        /**
         * T-0184 — THE OUTSIDE OF EVERY TURN, stationed the way the approaches
         * above are, and for the same reason: a claim about roadway is only
         * worth what a point standing on it is worth.
         *
         * Every panel used to be square to its own chord, so at a bend the two
         * rows crossed at the centreline and diverged towards the edges and the
         * outside of the turn carried a triangle of unpainted ground — 23.47 m2
         * of it town-wide, worst 4.29 m2 at South Water Street's west approach
         * (`tools/measure_road_joints.mjs`, a 2 cm plan lattice). Nine stations
         * are dropped INSIDE that sector at each authored bend, spread across
         * its angle and out to nine tenths of the half-width, and each must land
         * on drawn roadway. Every one of them was uncovered before the mitre.
         *
         * The full lattice lives in the instrument; these stations are the part
         * a release can afford. A bend whose own centreline is wet carries no
         * question — North Water Street's line runs inside the water mask from
         * E 330 to E 576, and no ribbon may be drawn there at all.
         */
        const jointGaps = [];
        let jointStations = 0;
        for (const rec of a.streets.records) {
          const line = rec.drawn ?? rec.path;
          const half = (rec.track_width_m ?? 6) * 0.5;
          for (let i = 1; i < line.length - 1; i++) {
            const [A, P, B] = [line[i - 1], line[i], line[i + 1]];
            let turn = Math.atan2(B[1] - P[1], B[0] - P[0])
              - Math.atan2(P[1] - A[1], P[0] - A[0]);
            if (turn > Math.PI) turn -= 2 * Math.PI;
            if (turn < -Math.PI) turn += 2 * Math.PI;
            if (Math.abs(turn) < 0.25 * Math.PI / 180) continue;
            if (a.terrain.isWater(A[0], A[1]) || a.terrain.isWater(P[0], P[1])
              || a.terrain.isWater(B[0], B[1])) continue;
            const l1 = Math.hypot(P[0] - A[0], P[1] - A[1]);
            const u1e = -(P[1] - A[1]) / l1;
            const u1n = (P[0] - A[0]) / l1;
            const sgn = turn > 0 ? 1 : -1;
            for (let s = 0; s < 3; s++) {
              const ang = ((s + 0.5) * turn) / 3;
              const c = Math.cos(ang);
              const sn = Math.sin(ang);
              const ve = u1e * c - u1n * sn;
              const vn = u1e * sn + u1n * c;
              for (const f of [0.35, 0.65, 0.9]) {
                const e = P[0] - sgn * ve * half * f;
                const n = P[1] - sgn * vn * half * f;
                if (a.terrain.isWater(e, n)) continue;
                jointStations++;
                if (!covered(e, n)) {
                  jointGaps.push(`${rec.id} [${P[0]}, ${P[1]}] ${(turn * 180 / Math.PI)
                    .toFixed(1)} deg at ${f}`);
                }
              }
            }
          }
        }

        return {
          worstSink, refinedPanels, approachGaps, jointGaps, jointStations,
          joints: a.streets.stats?.joints ?? null,
          squareJoints: a.streets.stats?.squareJoints ?? null,
          mitredJoints: a.streets.stats?.mitredJoints ?? null,
          fannedJoints: a.streets.stats?.fannedJoints ?? null,
          jointFanTriangles: a.streets.stats?.jointFanTriangles ?? null,
          // T-0713. THE TWO CHANNELS, censused off the geometry the browser
          // actually built. `_confidence` is the contract's channel and now
          // carries the LINE's grade alone, so it decides whether a ribbon
          // stands; `_trackConfidence` carries the weakest of surface and wear
          // and is spent only on the worn texture. A vertex census is the only
          // reading that can tell the two apart from out here, and it is what
          // would have caught the split being quietly reverted — the whole
          // platted town going back to dithering as invention while every
          // node-side test still passed.
          streetChannels: (() => {
            const band = (v) => (v >= 0.75 ? 'reconstructed' : v >= 0.25 ? 'inferred' : 'attested');
            const out = {
              ribbon: { attested: 0, inferred: 0, reconstructed: 0 },
              track: { attested: 0, inferred: 0, reconstructed: 0 },
              meshes: 0, missingTrack: 0, unequal: 0,
            };
            a.streets.group.traverse((o) => {
              const g = o.geometry;
              const conf = g?.getAttribute?.('_confidence');
              if (!conf) return;
              out.meshes += 1;
              const trk = g.getAttribute('_trackConfidence');
              if (!trk) { out.missingTrack += 1; return; }
              if (trk.count !== conf.count) out.unequal += 1;
              for (let i = 0; i < conf.count; i += 1) out.ribbon[band(conf.getX(i))] += 1;
              for (let i = 0; i < trk.count; i += 1) out.track[band(trk.getX(i))] += 1;
            });
            return out;
          })(),
          // ...and the records those channels were built from, so a census that
          // disagrees with the dataset is reported as the disagreement it is
          // rather than as a bare count nobody can check.
          streetGrades: (() => {
            const out = { attested: [], inferred: [], reconstructed: [], wornInvented: 0 };
            for (const rec of a.streets.records) {
              (out[rec.geometry_confidence] ?? out.reconstructed).push(rec.id);
              if (rec.wear_confidence === 'reconstructed'
                || rec.surface_confidence === 'reconstructed') out.wornInvented += 1;
            }
            return out;
          })(),
          records: a.streets.records.length, vertices, worstDrape, wetVertices,
          dryCentrelinePanels, clippedPanels, slivers, emittedQuads,
          canopyPresent, rootedPlants, worstPlantRoot, waterPlants, deepWaterPlants,
          treeStations: treeStations.length, wetTreeStations: wetTreeStations.length,
          drownedTreeStations: drownedTreeStations.length,
          lowestTreeStation, waterY,
          treeRejectedBelowWaterline: a.trees.stats?.rejectedBelowWaterline ?? null,
          // ROADMAP R-BUG5. The population both woody checks above are blind to:
          // `stations` is written only inside the near-field planter's 632 m
          // square, so the five FAR_TIMBER bodies drawn as a horizon silhouette
          // have never been asked where they stand. Measured against the mask the
          // BROWSER loaded, not the one in data/ — tools/measure_far_timber.py
          // asks the committed bytes and this project has twice shipped a bug
          // living exactly in that gap.
          farTimberWater: a.trees.farTimberWater?.() ?? null,
          // ...and the clip that keeps them off the screen, exercised. The band is
          // solved around the camera, so this has to stand far enough back that a
          // body in water clears MIN_FAR_M and the solver actually reaches it —
          // from the spawn point the nearest one is a metre inside the near
          // cut-off, which is a green gate that has run nothing. Since T-0031 the
          // body it exercises is `north_branch_belt`, whose wet crossing begins at
          // its first vertex (-95, 345) — 605 m from this stand, and the first
          // sample of a segment is emitted at the vertex itself, so the clip is
          // reached whatever the adaptive step does with the 16 m of wet run.
          horizonWetSkipped: (() => {
            a.walker.teleport({ local_e: -100, local_n: -260, yaw_deg: 44 });
            a.step();
            return a.trees.stats?.horizonWetSkipped ?? null;
          })(),
          anchoredBuildings, worstBuildingAnchor, deepestBedding, exchangeAnchor,
          worstDrySurfaceAlias,
          clearsLake: a.streets.blocksGrowth(452.5, -110.4),
          keepsBlockGreen: !a.streets.blocksGrowth(510, -180),
          crossing, approaching,
        };
      });
    }

    try {
    // PART 1 — "the gate counts the town" through the fort stockade and the
    // business signs: the enclosure and signage layers, all read off the scene
    // graph rather than off the screen.
    if (stageOn(1)) {
    inStageWork = true;

    // --- the frame is multisampled, phone included (T-0157) ----------------
    // `main.js` booted with `antialias: !coarse` from Milestone 0, so a touch
    // device drew the whole town with no multisampling and its edges flipped
    // whole. Measured at 390×780 on the published mirror by
    // `tools/measure_phone_aa.mjs`: switching MSAA on takes every one of the 149
    // pixels that were swapping surface outright under a 2 mm nudge — 25 aerial,
    // 124 at Lake and Market — to ZERO, and the worst per-pixel movement from
    // 105/140 to 28/37.
    //
    // This is asserted on the live CONTEXT rather than on a pixel count, and the
    // measurement is why: the flicker COUNT goes UP when MSAA is switched on
    // (1,056 → 2,482 aerial), because a partial resample touches more pixels
    // than a whole flip does. Any gate written on the count would have to be
    // written backwards.
    //
    // `antialias` is a context-creation attribute with no runtime handle, which
    // is exactly what makes it worth a gate: the only way to lose it is a reboot
    // with the flag off, and not one other check in this file would notice.
    // `getContextAttributes()` alone will not do — it echoes what was ASKED for.
    // `SAMPLES` is what the framebuffer actually has.
    const multisample = await page.evaluate(() => {
      const gl = window.__chicago4d.renderer.getContext();
      return {
        asked: gl.getContextAttributes().antialias,
        samples: gl.getParameter(gl.SAMPLES),
        coarse: window.matchMedia('(pointer: coarse)').matches,
      };
    });
    check(`${label}: the frame is multisampled — the town's edges are resolved on a phone too`,
      multisample.asked === true && multisample.samples >= 2,
      `antialias=${multisample.asked} SAMPLES=${multisample.samples} `
      + `pointer:coarse=${multisample.coarse}`);

    // --- the gate counts the town (T-0036) --------------------------------
    // The owner asked for the number of buildings and the number of people
    // living in them on the FRONT screen. The assertion that matters is not
    // "a row appeared" — it is that the row's NUMERALS are the committed
    // data's, read back out of the rendered DOM and compared against the JSON
    // the page fetched. A gate screen quoting a stale count is the failure this
    // is here to catch, and it is invisible to every other check in this file.
    //
    // The gate is still open at this point in the run (the walk tests click
    // through it much later), which is the only moment the row is on screen.
    //
    // T-0491. THE ROW COUNT IS NOT HARDCODED, and it was: this read `shown.length === 2`
    // and T-0490 added a third row — the evidence population, out of the residents
    // manifest — so the assertion failed on `dev` from 2 September without a word about
    // the row it had not been told about. A test that names how many figures there are
    // rots the next time the row is right; one that reads the same files the page read
    // and compares figure for figure cannot. The residents manifest is fetched here
    // rather than taken off the harness handle because `census.js` reads it directly and
    // nothing puts it on `window`.
    //
    // T-0782 rebuilt the card as TWO rows — buildings, then people — and demoted `people
    // housed` from a headline figure to a placement note under the people row, because
    // set against the town total it read as population coverage and is nothing of the
    // kind. So the headline figures are now the two numerators, and the housed count is
    // asserted where it moved to rather than dropped: it is the number this whole check
    // exists to keep honest. The two strings the owner asked be struck are asserted
    // ABSENT, because either of them coming back is a silent regression of the reading.
    const gateCensus = await page.evaluate(() => {
      const host = document.getElementById('gate-census');
      const visible = !!host && !host.hasAttribute('hidden');
      const figures = [...(host?.querySelectorAll('.gc-n') || [])].map((el) => el.textContent);
      const seg = (sel) => [...(host?.querySelectorAll(sel) || [])].map((el) => el.style.width);
      return {
        visible,
        figures,
        text: host ? host.textContent.replace(/\s+/g, ' ').trim() : '',
        aria: host ? (host.getAttribute('aria-label') || '') : '',
        note: host ? [...host.querySelectorAll('.gc-note')].map((el) => el.textContent.trim()) : [],
        bars: host ? host.querySelectorAll('.gc-bar').length : 0,
        grades: seg('.gc-seg-att, .gc-seg-inf, .gc-seg-rec'),
        keys: host ? [...host.querySelectorAll('.gc-key li')].map((el) => el.textContent.trim()) : [],
        gateSub: (document.getElementById('gate-sub')?.textContent || '').trim(),
        box: host ? host.getBoundingClientRect().width : 0,
        data: window.__chicago4d.census,
      };
    });
    // The people row's figure is not on the harness handle, so it is read off the
    // SERVED tree — `ROOT` is whichever of the source tree and the published mirror
    // this run is serving, which is the same file the page fetched.
    let residentCounts = null;
    try {
      residentCounts = JSON.parse(
        fs.readFileSync(path.join(ROOT, 'data', 'residents', 'index.json'), 'utf8'),
      ).counts || null;
    } catch { residentCounts = null; }
    const grouped = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    const shown = gateCensus.figures.map((t) => Number(String(t).replace(/,/g, '')));
    const want = [gateCensus.data?.buildings?.standing, residentCounts?.persons]
      .filter((n) => Number.isFinite(Number(n))).map(Number);
    check(`${label}: the gate shows the town census`,
      gateCensus.visible && gateCensus.box > 0 && shown.length === want.length && want.length >= 2,
      `visible=${gateCensus.visible} width=${gateCensus.box} figures=${JSON.stringify(gateCensus.figures)} wanted=${JSON.stringify(want)}`);
    check(`${label}: the gate's figures are the committed data's`,
      want.length >= 2 && shown.length === want.length && shown.every((n, i) => n === want[i]),
      `showed ${JSON.stringify(shown)}, data says ${JSON.stringify(want)}`);
    // Each numerator carries a bar it is a portion of, and the people bar carries the
    // three grades as segments of the town total — a key alone would let the bar rot.
    const housed = Number(gateCensus.data?.people?.housed);
    const byGrade = residentCounts?.by_grade || {};
    const gradeWant = ['attested', 'inferred', 'reconstructed']
      .filter((g) => Number.isFinite(Number(byGrade[g])));
    check(`${label}: both rows carry a completeness bar, the people bar graded`,
      gateCensus.bars === want.length && gateCensus.grades.length === gradeWant.length
      && gateCensus.keys.length === gradeWant.length
      && gradeWant.every((g, i) => gateCensus.keys[i]
        === `${grouped(Number(byGrade[g]))} ${g}`),
      `bars=${gateCensus.bars} segments=${JSON.stringify(gateCensus.grades)} keys=${JSON.stringify(gateCensus.keys)}`);
    // The placement figure survives as a note under the people row, in the committed
    // data's own number, and never again as a share of the town.
    check(`${label}: people housed reads as placement, under the people row`,
      Number.isFinite(housed) && gateCensus.note.length === 1
      && gateCensus.note[0] === `${grouped(housed)} of them are placed in a building that stands`
      && gateCensus.aria.includes(`${grouped(housed)} of them are placed`),
      `note=${JSON.stringify(gateCensus.note)} housed=${housed} aria=${JSON.stringify(gateCensus.aria)}`);
    // T-0782's two strikes, asserted as absences. `structures` was the ready line's
    // record count, which contradicted the buildings figure below it.
    check(`${label}: the card drops the projected count and the structures line`,
      !/projected/i.test(gateCensus.text) && !/projected/i.test(gateCensus.aria)
      && !/structures?\b/i.test(gateCensus.text) && !/structures?\b/i.test(gateCensus.gateSub),
      `card=${JSON.stringify(gateCensus.text)} ready=${JSON.stringify(gateCensus.gateSub)}`);
    // Neither figure is a total, and the row has to say so or it misleads: the
    // buildings are counted against the programme's target and the people
    // against the town's own recorded size, both quoted out of the same file.
    check(`${label}: the gate names both denominators`,
      Number.isFinite(gateCensus.data?.buildings?.target)
      && Number.isFinite(gateCensus.data?.people?.town_total)
      && gateCensus.text.includes(grouped(gateCensus.data.buildings.target))
      && gateCensus.text.includes(`roughly ${grouped(gateCensus.data.people.town_total)}`),
      gateCensus.text);

    // --- water anchoring (docs/GLB-CONTRACT.md) ---------------------------
    // A bridge's local y = 0 is the design water surface, not the ground, so
    // the renderer must NOT sample the heightfield for it. Mid-channel the
    // ground surface is the river BED, so a regression here sinks the bridge
    // out of sight and reads as a missing asset. The assertion is written as
    // the DIFFERENCE between the two anchors rather than "y === 0", because
    // over dry land the two agree and a test that passed there would prove
    // nothing.
    //
    // The bed is sampled at the deck's MIDPOINT, not at the placement origin.
    // That origin is the polygon's (0, 0) — for this bridge the west end, which
    // by construction sits exactly on the traced waterline where the ground
    // surface crosses zero. Sampling there compares zero against zero and the
    // check passes whatever the renderer does. Found by this assertion failing
    // on its first run, which is the argument for writing it as a difference.
    const anchored = await page.evaluate(() => {
      const api = window.__chicago4d;
      const rec = api.registry.get('north_branch_bridge');
      const p = rec?.sidecar?.placement;
      const poly = rec?.sidecar?.footprint?.polygon;
      if (!p || !poly?.length) return { missing: true };
      const world = api.buildings.positionOf('north_branch_bridge');
      // Footprint bbox centre, rotated by the facade bearing exactly as
      // walker.js's footprintsFrom does, then offset to world ENU.
      const us = poly.map(([u]) => u);
      const vs = poly.map(([, v]) => v);
      const u = (Math.min(...us) + Math.max(...us)) / 2;
      const v = (Math.min(...vs) + Math.max(...vs)) / 2;
      const th = (p.rotation_deg ?? 0) * Math.PI / 180;
      const midE = (p.local_e ?? 0) + u * Math.cos(th) + v * Math.sin(th);
      const midN = (p.local_n ?? 0) - u * Math.sin(th) + v * Math.cos(th);
      return {
        anchor: p.vertical_anchor,
        y: world ? world.y : null,
        // The real channel bed, and what the terrain anchor would have
        // returned here — which is NOT the bed: height() reports a wading
        // barrier over water, so the regression this catches lifts the bridge
        // metres into the air rather than sinking it.
        bed: api.terrain.groundHeight(midE, midN),
        terrainAnchor: api.terrain.height(midE, midN),
      };
    });
    check(`${label}: the bridge declares a water anchor`,
      anchored.anchor === 'water', `${anchored.anchor ?? 'record missing'}`);
    check(`${label}: the bridge sits on the water plane, not on the terrain`,
      anchored.y !== null && Math.abs(anchored.y) < 0.01
      && anchored.bed < -0.5 && Math.abs(anchored.terrainAnchor - anchored.y) > 1,
      `placed y ${anchored.y?.toFixed(2)}, bed ${anchored.bed?.toFixed(2)} m, `
      + `terrain anchor would give ${anchored.terrainAnchor?.toFixed(2)} m`);

    // --- the enclosure layer (T-0038) ---------------------------------------
    //
    // A fence is the first thing this project has drawn from a PERIMETER rather
    // than a footprint, and it is drawn by the renderer rather than baked, so
    // every one of these questions is answerable here and nowhere else. The last
    // one is the acceptance clause of its ticket: not "the data loaded" but "you
    // can see it from where a visitor stands".
    //
    // T-0067 replaced the layer's "one draw call" question with the OPPOSITE
    // one, and the swap is a strengthening rather than a relaxation. One mesh
    // spanning the whole town has a bounding sphere no frustum can cull, so
    // every fence in Chicago drew in every frame including the ones behind the
    // camera — 33,166 triangles of it, which T-0115 measured and named the
    // largest free saving left in the scene. The layer now builds culling-sized
    // chunks, and the assertion below is what makes a future re-merge fail
    // loudly instead of quietly costing a phone its frame.
    const encl = await page.evaluate(() => {
      const e = window.__chicago4d.enclosures;
      const meshes = (e?.group?.children ?? []).filter((c) => c.isMesh);
      const box = { minE: Infinity, maxE: -Infinity, minN: Infinity, maxN: -Infinity };
      for (const r of e?.records ?? []) {
        for (const run of r.runs ?? []) {
          for (const [pe, pn] of run.path_local_enu_m ?? []) {
            box.minE = Math.min(box.minE, pe); box.maxE = Math.max(box.maxE, pe);
            box.minN = Math.min(box.minN, pn); box.maxN = Math.max(box.maxN, pn);
          }
        }
      }
      let worst = 0;
      let verts = 0;
      let ungraded = 0;
      let graded = 0;
      // The widest bounding sphere on the layer: this is the number that decides
      // whether the frustum can do anything at all, so it is read rather than
      // inferred from the chunk count.
      let widestSphere = 0;
      for (const mesh of meshes) {
        const g = mesh.geometry;
        const pos = g.getAttribute('position');
        verts += pos.count;
        widestSphere = Math.max(widestSphere, g.boundingSphere?.radius ?? Infinity);
        for (let i = 0; i < pos.count; i++) {
          // world is (E, up, -N)
          const e0 = pos.getX(i);
          const n0 = -pos.getZ(i);
          worst = Math.max(worst,
            box.minE - e0, e0 - box.maxE, box.minN - n0, n0 - box.maxN);
        }
        const conf = g.getAttribute('_confidence');
        if (!conf) continue;
        graded += 1;
        for (let i = 0; i < conf.count; i++) {
          if (!(conf.getX(i) >= 0 && conf.getX(i) <= 1)) ungraded++;
        }
      }
      return {
        census: e?.census ?? null,
        meshes: meshes.length,
        runs: (e?.records ?? []).reduce((t, r) => t + (r.runs?.length ?? 0), 0),
        graded,
        verts,
        widestSphere,
        ungraded,
        outsideRuns: Number.isFinite(worst) ? worst : null,
        ids: (e?.records ?? []).map((r) => r.id),
      };
    });
    check(`${label}: the enclosure layer draws its records`,
      encl.census?.enclosures >= 1 && encl.census?.posts > 0 && encl.verts > 0,
      `${encl.census?.enclosures} enclosure(s), ${encl.census?.posts} posts, `
      + `${encl.verts} vertices, ${encl.census?.dropped} member(s) refused, `
      + `ids [${encl.ids.join(', ')}]`);
    // T-0068 added the second half of this. A layer of 3.5 km of lot-line fence
    // can fail the culling contract in the OPPOSITE direction too: one mesh per
    // run holds every sphere small and costs a draw call per fence, and at 189
    // runs that is 51 calls of the frame's whole budget (measured). So it packs
    // neighbouring runs into a shared chunk, and the bar is asserted from both
    // ends — the widest sphere stays under 40 m AND the mesh count stays well
    // under the run count, which is what says the packing is running at all.
    check(`${label}: the enclosure layer is chunked so the frustum can cull it`,
      encl.meshes > 1 && encl.widestSphere <= 40
      && encl.runs > 50 && encl.meshes <= encl.runs / 2,
      `${encl.meshes} mesh(es) for ${encl.runs} run(s) in the group, widest bounding `
      + `sphere ${encl.widestSphere?.toFixed(1)} m (one town-wide mesh reads ~700 m)`);
    // Unmarked geometry rendering as though it were evidence is the one failure
    // the confidence view exists to prevent, and a layer built in JS can put a
    // vertex on screen without ever passing through the GLB contract that would
    // have caught it.
    check(`${label}: every fence vertex carries a confidence grade`,
      encl.meshes > 0 && encl.graded === encl.meshes && encl.ungraded === 0,
      `${encl.graded} of ${encl.meshes} chunk(s) carry the attribute, `
      + `${encl.ungraded} value(s) out of range`);
    // The fence stands where the record puts it. The tolerance is the post's own
    // half-section plus a rail's, which is the most a member can legitimately
    // overhang the line its own centre is authored on.
    check(`${label}: no fence member stands outside its own authored run`,
      encl.outsideRuns !== null && encl.outsideRuns <= 0.15,
      `worst overhang ${encl.outsideRuns?.toFixed(3)} m beyond the authored extent`);

    // AND IT READS. Stand in the Western Hotel's yard, hold the clock so the
    // grass cannot supply the difference, and compare the frame with the layer
    // hidden. A fence nobody can see from the ground is the visible-progress
    // rule's own failure case, so it is asserted rather than described.
    await page.evaluate(() => window.__chicago4d.goToTarget(
      { kind: 'intersection', local_e: -127.7, local_n: -292 }));
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const yardWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.enclosures.group.visible = false; });
    const yardWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.enclosures.group.visible = true; });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    const dYard = signatureDistance(yardWith, yardWithout);
    check(`${label}: the yard fence reaches the screen from inside the yard`,
      dYard.worst >= 6 && dYard.mean >= 0.3,
      `cell delta mean ${dYard.mean?.toFixed(2)}, worst ${dYard.worst} (need worst>=6)`);

    // --- the town pound is a fence, not a box (T-0051) -----------------------
    //
    // Chicago's first public building is an enclosure — Andreas: "a small wooden
    // enclosure and quite roofless" — and it stood in this town as a roofed log
    // box because the only archetype that would build a low walled rectangle
    // cannot build a roofless one. Its geometry now lives on the layer above,
    // and a record whose mesh moves layers can go wrong in four ways that no
    // dataset gate can see: the GLB can still load, the card can become
    // unreachable, the retired footprint can stay behind as an invisible wall,
    // and the fence can fail to draw at all. One assertion each.
    const pen = await page.evaluate(() => {
      const api = window.__chicago4d;
      const rec = api.loaded?.registry?.get?.('estray_pen')
        ?? api.registry?.get?.('estray_pen') ?? null;
      return {
        inLayer: (api.enclosures?.records ?? []).some((r) => r.id === 'estray_pen'),
        asset: rec ? rec.sidecar?.asset ?? null : 'NO RECORD',
        drawnBy: rec?.sidecar?.drawn_by ?? null,
        hasGltf: !!rec?.gltf,
        obstructs: (api.footprints ?? []).some((f) => f.id === 'estray_pen'),
      };
    });
    check(`${label}: the estray pen is drawn as an enclosure and bakes no mesh`,
      pen.inLayer && pen.asset === null && pen.drawnBy === 'enclosures' && !pen.hasGltf,
      `on the layer ${pen.inLayer}, sidecar asset ${JSON.stringify(pen.asset)}, `
      + `drawn_by ${pen.drawnBy}, gltf loaded ${pen.hasGltf}`);
    check(`${label}: the retired box leaves no invisible wall on the public square`,
      !pen.obstructs, `walker footprint present: ${pen.obstructs}`);

    // Stand in the pound and look around it. Two questions in one stand: can you
    // SEE it (the visible-progress rule's own test), and can you still open the
    // card behind it — which used to come free with a roof to click on and now
    // has to be earned by picking the fence itself.
    await page.evaluate(() => window.__chicago4d.goToTarget(
      { kind: 'intersection', local_e: 473.07, local_n: -374.26 }));
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const penWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.enclosures.group.visible = false; });
    const penWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.enclosures.group.visible = true; });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    const dPen = signatureDistance(penWith, penWithout);
    check(`${label}: the pen reaches the screen from inside the pen`,
      dPen.worst >= 6 && dPen.mean >= 0.3,
      `cell delta mean ${dPen.mean?.toFixed(2)}, worst ${dPen.worst} (need worst>=6)`);

    const penPick = await page.evaluate(() => {
      const hits = [];
      for (const x of [-0.6, -0.3, 0, 0.3, 0.6]) {
        for (const y of [-0.4, -0.2, 0, 0.2]) {
          const hit = window.__chicago4d.pick({ x, y });
          if (hit?.id) hits.push(hit.id);
        }
      }
      return hits;
    });
    check(`${label}: aiming at the pen's fence still opens the pen's card`,
      penPick.includes('estray_pen'),
      `20 aims returned [${[...new Set(penPick)].join(', ') || 'nothing'}]`);

    // --- the dooryard garden pickets (T-0052) --------------------------------
    //
    // The first record on this layer whose evidence is a TREATMENT rather than a
    // place: the Kinzie-view plate shows picket-fenced garden plots and nothing
    // says which lot in the town had one, so the record is GENERATED from a rule
    // over the platted lots. Two things can go wrong that no dataset gate sees.
    // The rule can produce a record the renderer then draws as the wrong KIND of
    // fence — the layer knew only posts and horizontal rails until today, and a
    // picket drawn as three rails would pass every count in this file. And a
    // fence at the back of a lot can be invisible from anywhere a visitor stands.
    //
    // T-0516: THIRTEEN PLOTS BECAME ONE, and the floor here moved with them because
    // the twelve were never the town's to keep. Clause 4 of the rule admits a lot on
    // "a household recorded as living in it", read off the structure record's
    // `occupants` PROSE — and on 2026-09-02 the owner retired the reconstructed
    // resident population, so twelve of the thirteen were resting on the prose of
    // households that no longer exist. A garden behind a house nobody lives in claims
    // a gardener who does not exist. `generate_dooryard_pickets.py` said so itself,
    // in a comment naming T-0516 as the cause before T-0516 was worked.
    //
    // A floor of ten would now be an assertion about retired people, so it is
    // replaced rather than lowered — and by something STRONGER than a count. The one
    // plot that survives is the one lot in this town where the committed household
    // index carries a real `lives_at`: Elijah Harmon's, on Randolph, which is also the
    // garden the checks below walk into. Naming it asserts that the rule kept the
    // EVIDENCED plot and dropped the inferred ones, which a floor of ten never could.
    // Whether a garden should follow the HOUSE instead of the household is a claim
    // about the town rather than a bug, and it is the owner's: T-0727 asks him. If he
    // rules that way this floor rises again, and it should.
    const pickets = await page.evaluate(() => {
      const e = window.__chicago4d.enclosures;
      const rec = (e?.records ?? []).find((r) => r.id === 'town_dooryard_pickets');
      return {
        found: !!rec,
        runs: rec?.runs?.length ?? 0,
        ids: (rec?.runs ?? []).map((r) => r.id),
        type: rec?.form?.fence_type?.value ?? null,
        pales: e?.census?.pales ?? 0,
      };
    });
    check(`${label}: the town's house lots carry generated picket gardens`,
      pickets.found && pickets.runs >= 1 && pickets.type === 'picket'
      && pickets.ids.includes('blk_randolph_franklin_lot2'),
      `record ${pickets.found}, ${pickets.runs} plot(s) [${pickets.ids.join(', ')}], `
      + `fence type ${pickets.type}`);
    // A pale per 0.178 m of perimeter is what makes it a picket and not a rail
    // fence; the floor is deliberately far under the count so it asserts the
    // BRANCH ran, not a number that will drift with the rule's output.
    check(`${label}: the picket branch draws pales, not just posts and rails`,
      pickets.pales >= 500, `${pickets.pales} pale(s) on the layer`);

    // And stand in one of the gardens — Dr Harmon's lot on Randolph — holding the
    // clock so the grass cannot supply the difference.
    await page.evaluate(() => window.__chicago4d.goToTarget(
      { kind: 'intersection', local_e: 249.65, local_n: -282.7 }));
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const gardenWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.enclosures.group.visible = false; });
    const gardenWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.enclosures.group.visible = true; });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    const dGarden = signatureDistance(gardenWith, gardenWithout);
    check(`${label}: the garden fence reaches the screen from the dooryard`,
      dGarden.worst >= 6 && dGarden.mean >= 0.3,
      `cell delta mean ${dGarden.mean?.toFixed(2)}, worst ${dGarden.worst} (need worst>=6)`);

    // --- the town's lot-line yard fences (T-0068) ----------------------------
    //
    // The owner: *"i think there should be more fences."* Four enclosures in the
    // whole of Chicago, and every other lot open prairie from the house to the
    // alley. The three generated `town_lot_line_*` records enclose the YARD of
    // every improved platted lot the rule can find room behind, and the ticket's
    // acceptance clause is a TOWN-WIDE one — *"improved lots across the town read
    // as fenced"* — so the assertion has to be about COVERAGE and not about
    // existence. Four failures this catches that no dataset gate can:
    //
    //   * the rule silently narrowing (a footprint moves, a clause bites harder)
    //     until a handful of lots carry fences and the town reads as it did;
    //   * the coverage stacking in one corner — the records could name a hundred
    //     lots and the geometry stand in three blocks;
    //   * one of the three fence TYPES failing to reach the screen, which the
    //     board branch already did once (a type the renderer does not know falls
    //     back to open rails and draws a yard you can see straight through);
    //   * and a yard quietly acquiring a ground TREATMENT, which would take the
    //     prairie off a hundred lots. These records state none ON PURPOSE — a
    //     garden can say what it is, a yard cannot — and that decision is
    //     invisible in every other check in this file.
    const lotLines = await page.evaluate(() => {
      const a = window.__chicago4d;
      const recs = (a.enclosures?.records ?? []).filter((r) => /^town_lot_line_/.test(r.id));
      const lots = new Set();
      const blocks = new Set();
      const types = {};
      const graded = { existence: 0, form: 0, formValues: 0 };
      let runs = 0;
      let metres = 0;
      let declaresGround = 0;
      for (const r of recs) {
        for (const id of r.coverage?.lots ?? []) {
          lots.add(id);
          blocks.add(id.replace(/_lot\d+$/, ''));
        }
        types[r.form?.fence_type?.value ?? '?'] = (r.coverage?.lots ?? []).length;
        runs += (r.runs ?? []).length;
        if (r.ground?.treatment) declaresGround += 1;
        if (r.existence?.confidence === 'reconstructed') graded.existence += 1;
        for (const v of Object.values(r.form ?? {})) {
          graded.formValues += 1;
          if (v?.confidence === 'reconstructed') graded.form += 1;
        }
        for (const run of r.runs ?? []) {
          const p = run.path_local_enu_m ?? [];
          for (let i = 1; i < p.length; i++) {
            metres += Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]);
          }
        }
      }
      // AND WHAT IS DRAWN. Read off the MESHES rather than the records, so a
      // record that loaded and built nothing cannot pass this: which 40 m cells
      // of the town hold fence timber, and how tall the tallest stick in each
      // fence type stands. A cell count is the cheapest honest answer to "is the
      // enclosure spread across the town" that does not need the plat in here.
      const meshes = (a.enclosures?.group?.children ?? []).filter((c) => c.isMesh);
      const cells = new Set();
      let ungraded = 0;
      let lotMeshes = 0;
      for (const m of meshes) {
        // Scoped to the chunks these records reach: another record on this layer
        // is free to be graded better than reconstructed the day a source
        // describes its fence, and that must not fail this check.
        if (!(m.userData.recordIds ?? []).some((id) => /^town_lot_line_/.test(id))) continue;
        lotMeshes += 1;
        const pos = m.geometry.getAttribute('position');
        const conf = m.geometry.getAttribute('_confidence');
        for (let i = 0; i < pos.count; i += 3) {
          cells.add(`${Math.round(pos.getX(i) / 40)}:${Math.round(-pos.getZ(i) / 40)}`);
          if (conf && conf.getX(i) !== 1) ungraded += 1;
        }
      }
      return { records: recs.length, lots: lots.size, blocks: blocks.size, types, runs,
        metres: Math.round(metres), declaresGround, cells: cells.size,
        meshes: meshes.length, lotMeshes, graded, ungraded,
        pales: a.enclosures?.census?.pales ?? 0, posts: a.enclosures?.census?.posts ?? 0 };
    });
    check(`${label}: the town's improved lots read as fenced, block after block`,
      lotLines.records === 3 && lotLines.lots >= 100 && lotLines.blocks >= 17
      && lotLines.runs >= 240 && lotLines.metres >= 4000,
      `${lotLines.records} record(s) fencing ${lotLines.lots} platted lot(s) across `
      + `${lotLines.blocks} block(s), ${lotLines.runs} run(s), ${lotLines.metres} m`);
    check(`${label}: the lot fences are built in the period's three types`,
      Object.keys(lotLines.types).length === 3
      && ['board', 'picket', 'post_and_rail'].every((t) => lotLines.types[t] > 0),
      `types ${JSON.stringify(lotLines.types)}`);
    // 40 m cells, so this cannot be satisfied by one long fence: the town's
    // platted blocks span roughly 1,100 m by 330 m and a coverage that had
    // collapsed into one district would read well under half of this.
    check(`${label}: the enclosure is spread over the town, not stacked in one district`,
      lotLines.cells >= 95,
      `fence timber stands in ${lotLines.cells} cell(s) of 40 m`);
    check(`${label}: a lot's yard states no ground treatment, so its sward stands`,
      lotLines.declaresGround === 0,
      `${lotLines.declaresGround} of ${lotLines.records} lot-line record(s) declare one`);
    // Carded reconstructed, in both halves: what the RECORDS claim about
    // themselves, and what the drawn vertices carry. Nothing on this scheme is
    // evidence and the confidence view has to be able to take all of it away.
    check(`${label}: every lot fence is graded reconstructed, record and vertex`,
      lotLines.graded.existence === 3 && lotLines.graded.formValues > 0
      && lotLines.graded.form === lotLines.graded.formValues
      && lotLines.lotMeshes > 0 && lotLines.ungraded === 0,
      `${lotLines.graded.existence}/3 existence, ${lotLines.graded.form}/`
      + `${lotLines.graded.formValues} form values, ${lotLines.ungraded} vertex/vertices in `
      + `${lotLines.lotMeshes} chunk(s) graded better than reconstructed`);
    // AND IT READS, from the ground these fences actually face. The alley behind
    // the Randolph and Wells block, looking east down it: the plat drives a
    // service alley through the middle of every block, the back of every lot on
    // both sides opens onto it, and the yard fences stand within three metres of
    // a visitor walking it. Compared with the layer hidden, holding the clock so
    // the grass cannot supply the difference — the same instrument the wagon
    // yard, the pen and the gardens use.
    await page.evaluate(() => {
      window.__chicago4d.walker.teleport({ local_e: 370, local_n: -323.3, yaw_deg: 90 });
    });
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const lotWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.enclosures.group.visible = false; });
    const lotWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.enclosures.group.visible = true; });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    const dLot = signatureDistance(lotWith, lotWithout);
    check(`${label}: the lot fences reach the screen from the alley they face`,
      dLot.worst >= 6 && dLot.mean >= 0.3,
      `cell delta mean ${dLot.mean?.toFixed(2)}, worst ${dLot.worst} (need worst>=6)`);

    // --- the Sauganash's yard fence and its trees (T-0091) -------------------
    //
    // The first CLOSED fence this project builds that is not a garden pale, and
    // the first tree in this scene whose position a record states rather than a
    // density deals. Both failure modes are drawing faults that no dataset gate
    // can see: a `board` fence type the renderer does not know falls back to the
    // open rail branch and draws a yard you can see straight through, which is
    // the opposite of what three views of this hotel show; and a placed stem is
    // one bad axis away from standing in the neighbouring block, which is
    // exactly the fault R-BUG5b caught in the planter it borrows its archetype
    // from. So the geometry is measured against the record here.
    const sauganash = await page.evaluate(() => {
      const a = window.__chicago4d;
      const rec = (a.enclosures?.records ?? []).find((r) => r.id === 'sauganash_yard');
      const run = rec?.runs?.[0]?.path_local_enu_m ?? [];
      const segDist = (pe, pn, p0, p1) => {
        const dx = p1[0] - p0[0];
        const dy = p1[1] - p0[1];
        const len2 = dx * dx + dy * dy || 1;
        let t = ((pe - p0[0]) * dx + (pn - p0[1]) * dy) / len2;
        t = Math.min(Math.max(t, 0), 1);
        return Math.hypot(p0[0] + dx * t - pe, p0[1] + dy * t - pn);
      };
      const onRun = (pe, pn) => {
        let d = Infinity;
        for (let k = 1; k < run.length; k++) d = Math.min(d, segDist(pe, pn, run[k - 1], run[k]));
        return d;
      };
      // The DRAWN fence, off EVERY chunk the layer built (T-0067 — it used to be
      // one merged buffer and reading `children[0]` was enough): how much timber
      // stands on this record's own line, and how tall the tallest of it stands
      // over the ground under it. A rail fence and a board fence of the same
      // height differ by an order of magnitude in the first number, which is
      // what makes this a test of the branch rather than of the record.
      let onLine = 0;
      let top = 0;
      for (const mesh of a.enclosures?.group?.children ?? []) {
        const pos = mesh.geometry?.getAttribute('position');
        for (let i = 0; pos && i < pos.count; i++) {
          const pe = pos.getX(i);
          const pn = -pos.getZ(i);
          if (onRun(pe, pn) > 0.25) continue;
          onLine++;
          top = Math.max(top, pos.getY(i) - a.terrain.surfaceHeight(pe, pn));
        }
      }
      // And the stems the YARD's planting record placed, each asked whether it
      // stands inside the fence it is supposed to stand behind. Filtered to the
      // yard record since T-0074: the dooryard pass states stems all over the
      // town through the same loop, and a dooryard elm two blocks away is not
      // an escapee from this fence.
      const stems = (a.trees?.stats?.plantedStems ?? [])
        .filter((st) => st.record === 'sauganash_yard_trees')
        .map((st) => ({
          ...st,
          inYard: st.e > 101.4 && st.e < 117.42 && st.n < -130.6 && st.n > -151.07,
          clear: onRun(st.e, st.n),
        }));
      return {
        found: !!rec,
        type: rec?.form?.fence_type?.value ?? null,
        stated: rec?.form?.height_m?.value ?? null,
        onLine,
        top,
        planted: a.trees?.stats?.planted ?? 0,
        stems,
      };
    });
    check(`${label}: the Sauganash's rear yard is fenced with boards, not rails`,
      sauganash.found && sauganash.type === 'board' && sauganash.onLine >= 2000,
      `record ${sauganash.found}, type ${sauganash.type}, `
      + `${sauganash.onLine} vertices on its own line`);
    // Tall is the whole of what image 10 says about this fence, so the number
    // the record turned that word into has to be the number on the screen.
    check(`${label}: the yard fence is drawn at the height its record states`,
      sauganash.stated !== null && Math.abs(sauganash.top - sauganash.stated) <= 0.12,
      `drawn ${sauganash.top?.toFixed(2)} m against a stated ${sauganash.stated} m`);
    check(`${label}: every stem the yard's planting record places stands inside that yard`,
      sauganash.stems.length === 3
      && sauganash.stems.every((st) => st.inYard && st.clear >= 2),
      `${sauganash.stems.length} yard stem(s) of ${sauganash.planted} planted: `
      + sauganash.stems.map((st) => `${st.id} ${st.inYard ? 'in' : 'OUT'} `
        + `${st.clear.toFixed(1)} m off the fence`).join(', '));

    // AND IT READS, from the street the fence stands on. Market Street beside
    // the yard, looking east: the fence is six metres away and the trees the
    // same plate shows behind it stand over it. Both are compared with the
    // layer hidden, holding the clock so the grass cannot supply the difference.
    await page.evaluate(() => {
      window.__chicago4d.walker.teleport({ local_e: 95, local_n: -140, yaw_deg: 90 });
    });
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const yardAll = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.enclosures.group.visible = false; });
    const yardNoFence = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.enclosures.group.visible = true; });
    await page.evaluate(() => { window.__chicago4d.trees.group.visible = false; });
    const yardNoTrees = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.trees.group.visible = true; });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    const dFence = signatureDistance(yardAll, yardNoFence);
    const dTrees = signatureDistance(yardAll, yardNoTrees);
    check(`${label}: the yard fence reaches the screen from Market Street`,
      dFence.worst >= 6 && dFence.mean >= 0.3,
      `cell delta mean ${dFence.mean?.toFixed(2)}, worst ${dFence.worst} (need worst>=6)`);
    // The woody layer is hidden whole here, so this says "trees are visible from
    // this stand" rather than "these three are". It is the yard's own crowns
    // that carry it: the town is cleared ground and the nearest timber that is
    // not in this yard is the river gallery two blocks north, behind the walker.
    check(`${label}: the trees behind the fence reach the screen with it`,
      dTrees.worst >= 6 && dTrees.mean >= 0.3,
      `cell delta mean ${dTrees.mean?.toFixed(2)}, worst ${dTrees.worst} (need worst>=6)`);

    // --- fenced ground is not prairie (T-0067) --------------------------------
    //
    // The owner, 2026-08-18: "everplace that is fenced in would have a different
    // ground, the wagon yard would probably be dirty dusty ground and fences
    // around properties inside the fence would not be wild prairie but curated
    // lawn and garden or animal pens." Every fence above enclosed the same wild
    // sward as the ground outside it, and three of the four records SAID SO in
    // their own `ground` blocks with `geometry: "absent"`.
    //
    // Two halves, and both are asserted because either one alone looks finished:
    // a treatment laid over a sward that still grows through it is a hole in the
    // model, and a suppressed sward with nothing laid in its place is bare
    // terrain inside a fence. The placer is asked DIRECTLY at interior points —
    // the same instrument T-0124 uses on the plank decks, `plantableAt` plus
    // `stationOf` for every species the ground's own zone could deal there,
    // which is the half that regressed silently before.
    const fenced = await page.evaluate(() => {
      const a = window.__chicago4d;
      const y = a.yards;
      const subs = a.flora.substrates();
      // One interior of each treatment, probed at the OPENEST point in it — a
      // working yard, an animal pen and a picketed dooryard. Not a centroid: the
      // Western Hotel's yard is an L wrapped round the hotel's own corner and
      // the average of its six corners lands inside the hotel.
      const wanted = ['worn_earth', 'trodden_earth', 'dooryard_garden'];
      const stands = wanted.map((t) => {
        const i = (y?.interiors ?? []).find((x) => x.treatment === t);
        if (!i) return { treatment: t, missing: true };
        const [e, n] = i.at;
        const zone = a.flora.zoneAt(e, n);
        const z = subs.find((x) => x.id === zone);
        let speciesAsked = 0;
        let speciesHits = 0;
        for (const sp of (z ? z.dry.concat(z.wet) : [])) {
          speciesAsked += 1;
          if (a.flora.stationOf(e, n, sp) !== null) speciesHits += 1;
        }
        return {
          treatment: t, id: i.id, e, n,
          reads: y.treatmentAt(e, n),
          suppressed: y.suppressesSward(e, n),
          rootable: a.flora.plantableAt(e, n),
          zone, speciesAsked, speciesHits,
        };
      });
      // The treatment's own geometry: laid, graded, and casting nothing. A
      // ground treatment lying ON the ground has nothing to cast onto, and it is
      // deliberately outside the furniture-shadow policy for that reason.
      let tris = 0;
      let ungraded = 0;
      let notReconstructed = 0;
      let casting = 0;
      for (const mesh of y?.group?.children ?? []) {
        const g = mesh.geometry;
        tris += g.getAttribute('position').count / 3;
        if (mesh.castShadow) casting += 1;
        const conf = g.getAttribute('_confidence');
        if (!conf) { ungraded += 1; continue; }
        for (let i = 0; i < conf.count; i++) {
          const v = conf.getX(i);
          if (!(v >= 0 && v <= 1)) ungraded += 1;
          else if (v < 1) notReconstructed += 1;
        }
      }
      // AND THE SUPPRESSION IS CONFINED. Sampled over the whole modelled box, so
      // it is a property of the dataset rather than of where anyone stands: an
      // interior polygon that went wrong — an unclosed ring, a sign flipped —
      // would take the prairie off half the town and every check above would
      // still pass.
      const hf = a.terrain.heightfield;
      const STEP = 4;
      let land = 0;
      let inside = 0;
      for (let n = hf.originN; n <= hf.originN + hf.depthM; n += STEP) {
        for (let e = hf.originE; e <= hf.originE + hf.widthM; e += STEP) {
          if (a.terrain.isWater(e, n)) continue;
          land += 1;
          if (y.suppressesSward(e, n)) inside += 1;
        }
      }
      // AND THE SUPPRESSED GROUND IS THE GROUND THE RECORDS DECLARE (T-0097).
      // The sampled area above is compared against the shoelace area of the
      // interiors the layer actually built, so the assertion is about the
      // dataset agreeing with itself rather than about a constant somebody
      // fitted to the fences of the day. An unclosed ring, a flipped sign or a
      // lost coordinate moves the two apart; a new fence, a new yard or an
      // apron the size of the fort's moves them together.
      const shoelace = (pts) => {
        let acc = 0;
        for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
          acc += pts[j][0] * pts[i][1] - pts[i][0] * pts[j][1];
        }
        return Math.abs(acc) / 2;
      };
      const declaredArea = (y?.interiors ?? []).reduce((t, i) => t + shoelace(i.pts), 0);
      // A record that DECLARES a treatment and got no interior is the failure
      // this layer would most quietly make — an interior derived from runs that
      // no longer close, or an authored ring that lost a coordinate. Asked of
      // the records rather than of a count, so the assertion survives the town
      // growing another fence.
      const declared = (a.enclosures?.records ?? [])
        .filter((r) => r.ground?.treatment)
        .map((r) => ({ id: r.id, treatment: r.ground.treatment,
          interiors: (y?.interiors ?? []).filter((i) => i.record === r.id).length }));
      return {
        stands,
        declared,
        census: y?.census ?? null,
        meshes: (y?.group?.children ?? []).length,
        tris, ungraded, notReconstructed, casting,
        suppressedFraction: land ? inside / land : 1,
        declaredArea,
        sampledArea: inside * STEP * STEP,
      };
    });
    // T-0516 moved the interior floor from 18 to 8 for the same reason the picket
    // floor above moved: twelve of the eighteen interiors were the dooryard gardens
    // of households retired on 2026-09-02. What the check is FOR is untouched — every
    // record that declares a treatment still has to have got an interior, which is the
    // failure this layer would most quietly make, and all three treatments still have
    // to reach the ground.
    check(`${label}: every fenced interior in the town carries a ground treatment`,
      fenced.declared.length >= 4 && fenced.declared.every((d) => d.interiors >= 1)
      && fenced.census?.interiors >= 8 && fenced.meshes >= 3 && fenced.tris > 0
      && Object.keys(fenced.census?.byTreatment ?? {}).length === 3,
      `${fenced.declared.length} record(s) declare a treatment `
      + `[${fenced.declared.map((d) => `${d.id} ${d.treatment} x${d.interiors}`).join(', ')}]; `
      + `${fenced.census?.interiors} interior(s) in ${fenced.meshes} mesh(es), `
      + `${fenced.tris} triangles, ${fenced.census?.beds} bed(s), `
      + `${fenced.census?.paths} path(s), treatments `
      + JSON.stringify(fenced.census?.byTreatment ?? {}));
    for (const s of fenced.stands) {
      check(`${label}: the ground inside a '${s.treatment}' fence reads as its own type`,
        !s.missing && s.reads === s.treatment && s.suppressed === true,
        s.missing ? 'no interior carries this treatment at all'
          : `${s.id} at E ${s.e?.toFixed(1)} / N ${s.n?.toFixed(1)} reads `
            + `${JSON.stringify(s.reads)}`);
      check(`${label}: no prairie plant roots inside a '${s.treatment}' fence`,
        !s.missing && s.rootable === false && s.speciesHits === 0 && s.speciesAsked > 0,
        s.missing ? 'no interior carries this treatment at all'
          : `rootable ${s.rootable}, ${s.speciesHits} of ${s.speciesAsked} `
            + `${s.zone} species granted a station`);
    }
    check(`${label}: the fenced ground is graded reconstructed and casts no shadow`,
      fenced.ungraded === 0 && fenced.notReconstructed === 0 && fenced.casting === 0,
      `${fenced.ungraded} ungraded vertex/vertices, ${fenced.notReconstructed} graded `
      + `better than reconstructed, ${fenced.casting} mesh(es) casting`);
    // T-0097 REPLACED THE HAND-FITTED CEILING HERE, and it is worth saying which
    // act that is. The bar was `< 0.002` of the modelled dry ground — a number
    // fitted to the four fenced records that existed when T-0067 wrote it, and one
    // that a legitimate new record makes red without anything being wrong. The
    // fort's apron is 3,120 m² of ground the dataset DECLARES, which took the
    // figure to 0.368 %, and raising a constant to 0.005 would have bought the
    // same red again the next time the town encloses something.
    //
    // So the assertion now compares the SAMPLED suppression against the shoelace
    // area of the interiors the layer built. That is strictly sharper: the old
    // bar could not tell 3,120 m² of apron from 3,120 m² of prairie taken off by
    // a ring that lost a coordinate, and this one fails on the second while
    // passing the first. The tolerance is the 4 m sampling grid's, not a fudge:
    // twenty-odd polygons between 50 and 800 m² are counted by their corner
    // samples, so a fifth either way is what the method can resolve. The absolute
    // ceiling is kept as the blow-up guard the comment above describes — a
    // fiftieth of the modelled dry ground, two orders off "half the town".
    // MEASURED on the day it was written: 4,764 m² declared across 22 interiors
    // in 5 records, 4,592 m² recovered by the sampler — 3.6 % apart, so the
    // 20 % tolerance is five times the observed discretisation error and is a
    // bound on the METHOD rather than a margin fitted to today's polygons.
    const declaredGap = fenced.declaredArea
      ? Math.abs(fenced.sampledArea - fenced.declaredArea) / fenced.declaredArea : 1;
    check(`${label}: the sward is suppressed on the ground the records declare and nowhere else`,
      fenced.suppressedFraction > 0 && fenced.suppressedFraction < 0.02
      && fenced.declaredArea > 0 && declaredGap < 0.2,
      `${(fenced.suppressedFraction * 100).toFixed(3)} % of the modelled dry ground; `
      + `${fenced.sampledArea.toFixed(0)} m² sampled against ${fenced.declaredArea.toFixed(0)} m² `
      + `declared by ${fenced.declared.length} record(s) (${(declaredGap * 100).toFixed(1)} % apart)`);

    // AND IT READS, from inside two of the three. Stand in the Western Hotel's
    // wagon yard and in one of the town's picketed dooryards, look at the ground,
    // and hold the clock so the grass cannot supply the difference. Same bar as
    // the fences, the boards and the goods: worst >= 6 and mean >= 0.3.
    for (const stand of [
      { id: 'worn_earth', name: 'the wagon yard', yaw: 200 },
      { id: 'dooryard_garden', name: 'a picketed dooryard', yaw: 20 },
    ]) {
      const at = fenced.stands.find((s) => s.treatment === stand.id);
      if (!at || at.missing) continue;
      await page.evaluate(({ e, n, yaw }) => window.__chicago4d.walker.teleport(
        { local_e: e, local_n: n, yaw_deg: yaw, pitch_deg: -38 }),
      { e: at.e, n: at.n, yaw: stand.yaw });
      await page.waitForTimeout(350);
      await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
      const withGround = await page.evaluate(() => window.__chicago4d.capture());
      await page.evaluate(() => { window.__chicago4d.yards.group.visible = false; });
      const withoutGround = await page.evaluate(() => window.__chicago4d.capture());
      await page.evaluate(() => { window.__chicago4d.yards.group.visible = true; });
      await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
      const d = signatureDistance(withGround, withoutGround);
      check(`${label}: the ground in ${stand.name} reaches the screen from inside it`,
        d.worst >= 6 && d.mean >= 0.3,
        `cell delta mean ${d.mean?.toFixed(2)}, worst ${d.worst} (need worst>=6)`);
    }

    // --- the dooryard plantings (T-0074) -------------------------------------
    //
    // The town-wide pass the yard record above was the precedent for: trees and
    // currant bushes dealt around the dwellings by the rule in
    // tools/generate_dooryard_plantings.py. A refused stem is a `problems` line
    // and fails this suite on its own, so what is asserted here is the other
    // half of T-0074's acceptance: at an ORDINARY house — the old agency house,
    // a log dwelling on an unfenced lot — the dealt stems actually reach the
    // screen from the walker. Cobweb Castle's deal is two cottonwoods
    // north-west of the house and a currant clump by its south-east corner;
    // the ids are the record's own, so a re-deal that moves this house's stems
    // updates this list in the same commit or fails here, loudly.
    const dooryard = await page.evaluate(() => {
      const stems = (window.__chicago4d.trees?.stats?.plantedStems ?? [])
        .filter((st) => st.record === 'town_dooryard_plantings');
      return {
        count: stems.length,
        cobweb: stems.filter((st) => st.id.startsWith('cobweb_castle_')).map((st) => st.id),
      };
    });
    check(`${label}: the dooryard pass planted stems across the town`,
      dooryard.count >= 100,
      `${dooryard.count} dooryard stem(s) drawn (the record states 125; a refusal `
      + 'also fails the no-problems check)');
    check(`${label}: Cobweb Castle's dealt stems are among them`,
      dooryard.cobweb.length === 3,
      `drawn: ${dooryard.cobweb.join(', ') || 'none'}`);
    // The trees, from the road south-west of the house looking at its yard
    // quarter: two 19-20 m crowns about 15 m off. Same layer-toggle probe and
    // same declared bar as every screen check in this file.
    await page.evaluate(() => {
      window.__chicago4d.walker.teleport({ local_e: 788, local_n: 124, yaw_deg: 45 });
    });
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const doorWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.trees.group.visible = false; });
    const doorWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.trees.group.visible = true; });
    const dDoor = signatureDistance(doorWith, doorWithout);
    check(`${label}: Cobweb Castle's dooryard trees reach the screen`,
      dDoor.worst >= 6 && dDoor.mean >= 0.3,
      `cell delta mean ${dDoor.mean?.toFixed(2)}, worst ${dDoor.worst} (need worst>=6)`);
    // The bush, stood over from five metres with the trees out of frame behind
    // the walker — so this delta is the currant clump's own, not a crown's.
    await page.evaluate(() => {
      window.__chicago4d.walker.teleport({ local_e: 806, local_n: 131, yaw_deg: 135 });
    });
    await page.waitForTimeout(350);
    const bushWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.trees.group.visible = false; });
    const bushWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.trees.group.visible = true; });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    const dBush = signatureDistance(bushWith, bushWithout);
    check(`${label}: the currant clump by its door reaches the screen`,
      dBush.worst >= 6 && dBush.mean >= 0.3,
      `cell delta mean ${dBush.mean?.toFixed(2)}, worst ${dBush.worst} (need worst>=6)`);

    // --- the fort stockade against the garden fence (T-0123) -----------------
    //
    // The owner walked up to a wall at Fort Dearborn and reported it "way too
    // short ... below my height". Two structures on that reservation answer to
    // "a wall you can walk up to", and they are the SAME palisade archetype in
    // its two modes: the stockade — picket_height_m 3.7 m, the record's honest
    // number for Kinzie's "high pickets" — and the garrison garden's worm
    // fence, 1.3 m stated, 1.14 m built, chest height by design. This block
    // holds that pair as a gate, in the walker's own terms: the fence
    // deliberately under a visitor's eye, the stockade over it, and a tap on
    // either answering with its own name — so nobody ever takes this
    // measurement by hand again, and a change that flattens the wall or raises
    // the fence fails loudly. The stated heights are pinned literally: they
    // move only on the owner's say-so (T-0123 rule 3), and this line moves in
    // the same commit.
    //
    // WHERE THE WALKER STANDS FOR THE STOCKADE, AND WHY IT IS THE RIVER BANK.
    // A rigid mesh takes ONE anchor, and the contract anchors it at the LOWEST
    // ground under it (buildings.groundUnder; the "shares the terrain surface"
    // check gates that bedding at 3 m). For the stockade that is the bank foot
    // under the north-west bastion, and the stand below is there — where wall
    // and anchor meet and the full twelve feet is rendered fact, so this gate
    // answers for the BAKE whatever else moves.
    //
    // It once answered for the bake alone. The mound raise of v202 left the
    // parade standing ~2.5 m over that anchor, so from the fort road only
    // ~1.2 m of picket showed; T-0125 measured it and the owner ruled that the
    // GROUND should give (2026-08-21). It did — the bank face at the fort
    // narrows to 8 m, L155 — and the parade side is now gated too, at the
    // bottom of this block, instead of being left open.
    const fortPair = await page.evaluate(() => {
      const a = window.__chicago4d;
      const bounds = a.buildings.instanceBounds();
      const stated = (id, key) => a.registry.get(id)?.sidecar?.attributes?.[key]?.value ?? null;
      const topOf = (id) => {
        const b = bounds[id];
        const p = a.buildings.positionOf(id);
        return b && p ? p.y + b.max[1] : null;
      };
      // The bank foot below the north-west bastion, facing the wall corner.
      a.walker.teleport({ local_e: 1125.0, local_n: 256.5, yaw_deg: 143, pitch_deg: 0 });
      a.step();
      const stockadeEyeY = a.walker.state.eyeY;
      const stockadeHit = a.pick({ x: 0, y: 0 });
      const stockadeCard = document.querySelector('#popup h2')?.textContent ?? '';
      // The owner's stand: on the reservation outside the garden's north-east
      // fence, facing it on his own reported bearing — the fort at his back.
      a.walker.teleport({ local_e: 1106.2, local_n: 124.0, yaw_deg: 233, pitch_deg: 0 });
      a.step();
      const gardenEyeY = a.walker.state.eyeY;
      const levelHit = a.pick({ x: 0, y: 0 });
      // A tap where a hand would land: aims dropped a little below level, at
      // the rails of a chest-high fence three to four metres off. The spread
      // covers the zig-zag's own offset and the daylight between rail courses.
      const aims = [];
      let gardenNdc = null;
      for (const y of [-0.2, -0.35, -0.5]) {
        for (const x of [-0.5, -0.25, 0, 0.25, 0.5]) {
          const hit = a.pick({ x, y });
          if (hit?.id) aims.push(hit.id);
          if (!gardenNdc && hit?.id === 'fort_dearborn_garrison_garden') gardenNdc = { x, y };
        }
      }
      let gardenCard = '';
      if (gardenNdc) {
        a.pick(gardenNdc);
        gardenCard = document.querySelector('#popup h2')?.textContent ?? '';
      }
      a.popup.close();
      // The parade side, facing the south wall — the approach T-0125 was
      // opened on. NOT the middle of that wall: a level gaze from about
      // (1148, 189) returns nothing at all, because it goes straight through
      // the SOUTH GATEWAY into the parade beyond. Kinzie and Andreas both
      // state gates north and south, the record builds them, and a stand
      // aimed at the doorway measures the doorway. This one is offset east of
      // it, onto wall.
      a.walker.teleport({ local_e: 1155.0, local_n: 190.0, yaw_deg: 8, pitch_deg: 0 });
      a.step();
      const paradeEyeY = a.walker.state.eyeY;
      const paradeHit = a.pick({ x: 0, y: 0 });
      return {
        stockade: {
          statedM: stated('fort_dearborn_palisade', 'picket_height_m'),
          meshM: bounds.fort_dearborn_palisade
            ? bounds.fort_dearborn_palisade.max[1] - bounds.fort_dearborn_palisade.min[1]
            : null,
          topY: topOf('fort_dearborn_palisade'),
          eyeY: stockadeEyeY,
          levelPick: stockadeHit?.id ?? null,
          card: stockadeCard,
        },
        garden: {
          statedM: stated('fort_dearborn_garrison_garden', 'fence_height_m'),
          builtM: bounds.fort_dearborn_garrison_garden?.max[1] ?? null,
          topY: topOf('fort_dearborn_garrison_garden'),
          eyeY: gardenEyeY,
          levelPick: levelHit?.id ?? null,
          aims: [...new Set(aims)],
          card: gardenCard,
        },
        parade: {
          topY: topOf('fort_dearborn_palisade'),
          eyeY: paradeEyeY,
          levelPick: paradeHit?.id ?? null,
        },
      };
    });
    // The record's twelve feet reached the bake. 0.15 m of tolerance is the
    // cap rail the archetype adds over the stated picket, nothing more.
    check(`${label}: the stockade's pickets are baked at the record's twelve feet`,
      fortPair.stockade.statedM === 3.7 && fortPair.stockade.meshM !== null
      && Math.abs(fortPair.stockade.meshM - fortPair.stockade.statedM) <= 0.15,
      `record ${fortPair.stockade.statedM} m, mesh ${fortPair.stockade.meshM?.toFixed(2)} m`);
    check(`${label}: the stockade tops a walker's eye where wall and anchor meet`,
      fortPair.stockade.topY !== null
      && fortPair.stockade.topY - fortPair.stockade.eyeY >= 0.5,
      `wall top y ${fortPair.stockade.topY?.toFixed(2)}, `
      + `eye y ${fortPair.stockade.eyeY?.toFixed(2)} (need 0.5 m of wall over the eye)`);
    check(`${label}: a level gaze there stops at the stockade, and the card says so`,
      fortPair.stockade.levelPick === 'fort_dearborn_palisade'
      && /stockade/.test(fortPair.stockade.card),
      `pick ${fortPair.stockade.levelPick ?? 'nothing'}, card "${fortPair.stockade.card}"`);
    // The opposite number: 1.14 m of worm fence, deliberately below the eye.
    check(`${label}: the garden fence holds below the eye of the walker who meets it`,
      fortPair.garden.statedM === 1.3
      && fortPair.garden.builtM !== null && fortPair.garden.builtM <= 1.35
      && fortPair.garden.eyeY - fortPair.garden.topY >= 0.3,
      `built ${fortPair.garden.builtM?.toFixed(2)} m against a stated `
      + `${fortPair.garden.statedM} m, fence top y ${fortPair.garden.topY?.toFixed(2)}, `
      + `eye y ${fortPair.garden.eyeY?.toFixed(2)} (need 0.3 m of eye over the fence)`);
    check(`${label}: a level gaze sails clean over the garden fence`,
      fortPair.garden.levelPick !== 'fort_dearborn_garrison_garden',
      `level pick returned ${fortPair.garden.levelPick ?? 'nothing'}`);
    check(`${label}: a tap on the garden fence names the garden, not a fort wall`,
      fortPair.garden.aims.includes('fort_dearborn_garrison_garden')
      && /garrison garden/.test(fortPair.garden.card)
      && !/stockade/.test(fortPair.garden.card),
      `15 aims returned [${fortPair.garden.aims.join(', ') || 'nothing'}], `
      + `card "${fortPair.garden.card}"`);
    // T-0125, settled. The wall used to stand at 5.06 m over a parade at 3.65 m
    // — 1.41 m of picket against a 1.68 m eye, so a level gaze crossed the wall
    // into the compound and a visitor walked up to a twelve-foot stockade that
    // reached his chest. The ground gave, on the owner's ruling: the bank face
    // at the fort narrows to 8 m (L155) and the north wall's ground rises
    // 1.26 → 2.57 m, which lifts the anchor and stands 2.34 m of picket — a
    // little under eight feet — over the parade, where four feet showed.
    //
    // The bar is 0.5 m of wall over the eye: the same bar its sibling check
    // above holds for the same property at the bank foot, and a bar this
    // ground can keep. The full twelve feet from the parade would need the
    // north wall's ground to equal the parade's exactly, and across a 4.5 m
    // gap to the waterline that means a vertical face of earth at the river.
    // That is not ground, so it is not built; a stepped or draped bake
    // (T-0125 option 1) is the route to full height everywhere if it is ever
    // wanted. What this gate holds is that a visitor cannot see over the wall.
    check(`${label}: the stockade stands over a walker's eye from the parade side`,
      fortPair.parade.topY !== null
      && fortPair.parade.topY - fortPair.parade.eyeY >= 0.5,
      `wall top y ${fortPair.parade.topY?.toFixed(2)}, `
      + `eye y ${fortPair.parade.eyeY?.toFixed(2)} at the fort road `
      + `(need 1.0 m of wall over the eye)`);
    check(`${label}: a level gaze from the parade side stops at the stockade`,
      fortPair.parade.levelPick === 'fort_dearborn_palisade',
      `level pick returned ${fortPair.parade.levelPick ?? 'nothing'}`);

    // --- the business signs (T-0039, widened by T-0066) ----------------------
    //
    // A second layer drawn from the dataset rather than baked, and the first one
    // that hangs geometry OFF a building instead of standing it on the ground.
    // That is where its failure modes live: a sign is positioned by arithmetic
    // on the footprint, the placement and the facade bearing, so one sign error
    // anywhere in that chain puts three dozen planks inside the walls, or
    // floating in the road behind them, and every dataset gate in this repo
    // would pass. So the geometry is measured against the record here, and
    // nowhere else.
    //
    // T-0066 gave every sign a NAME, a MOUNTING and a STYLE, and each of those
    // is a new way for the layer to be wrong without erroring: a name that does
    // not match the card behind it, a mounting whose reach nobody bounded, or a
    // town that quietly goes back to thirty-three identical boards. Each is
    // asserted below rather than described.
    const boards = await page.evaluate(() => {
      const s = window.__chicago4d.signage;
      const mesh = s?.group?.children?.[0] ?? null;
      const g = mesh?.geometry ?? null;
      const signs = s?.signs ?? [];
      const spans = s?.spans ?? [];
      let ungraded = 0;
      let notReconstructed = 0;
      let worstOver = -Infinity;   // furthest PAST its own declared reach
      let worstReach = 0;          // the largest reach any sign declares
      let worstInside = 0;         // deepest a vertex sits BEHIND its own facade
      let unattributed = 0;        // a triangle belonging to no sign
      const conf = g?.getAttribute('_confidence');
      if (conf) {
        for (let i = 0; i < conf.count; i++) {
          const v = conf.getX(i);
          if (!(v >= 0 && v <= 1)) ungraded++;
          else if (v < 1) notReconstructed++;
        }
      }
      // EVERY VERTEX AGAINST ITS OWN SIGN. The layer publishes the half-open
      // triangle range each sign emitted, so this does not have to guess which
      // anchor a vertex belongs to by proximity — which with a post standing two
      // metres out in the street would sometimes guess the neighbour.
      const uvRects = new Map();
      const byId = new Map(signs.map((sg) => [sg.structure_id, sg]));
      if (g && spans.length) {
        const pos = g.getAttribute('position');
        const uv = g.getAttribute('uv');
        for (const sp of spans) {
          const sg = byId.get(sp.id);
          if (!sg) { unattributed++; continue; }
          const reach = sg.reach_m ?? 2.2;
          worstReach = Math.max(worstReach, reach);
          const b = ((sg.facade_bearing_deg ?? 0) * Math.PI) / 180;
          let u0 = Infinity; let v0 = Infinity; let u1 = -Infinity; let v1 = -Infinity;
          for (let t = sp.from; t < sp.to; t++) {
            for (let k = 0; k < 3; k++) {
              const i = t * 3 + k;
              const e = pos.getX(i);           // world is (E, up, -N)
              const n = -pos.getZ(i);
              const de = e - sg.anchor_local_enu_m[0];
              const dn = n - sg.anchor_local_enu_m[1];
              worstOver = Math.max(worstOver, Math.hypot(de, dn) - reach);
              // Positive is out of the wall, along the facade's own normal.
              worstInside = Math.min(worstInside, de * Math.sin(b) + dn * Math.cos(b));
              if (uv) {
                u0 = Math.min(u0, uv.getX(i)); u1 = Math.max(u1, uv.getX(i));
                v0 = Math.min(v0, uv.getY(i)); v1 = Math.max(v1, uv.getY(i));
              }
            }
          }
          if (uv) {
            uvRects.set(sp.id, [u0, v0, u1, v1].map((x) => x.toFixed(4)).join(','));
          }
        }
      }
      // The variation the owner asked for, measured on the record: no two signs
      // a walker can see at once may share a style or a ground colour.
      const NEAR_M = 40;
      let pairs = 0;
      let sameStyle = 0;
      let sameGround = 0;
      for (let i = 0; i < signs.length; i++) {
        for (let j = i + 1; j < signs.length; j++) {
          const a = signs[i];
          const b = signs[j];
          const d = Math.hypot(a.anchor_local_enu_m[0] - b.anchor_local_enu_m[0],
            a.anchor_local_enu_m[1] - b.anchor_local_enu_m[1]);
          if (d > NEAR_M) continue;
          pairs++;
          if (a.style?.id === b.style?.id) sameStyle++;
          if (a.style?.ground === b.style?.ground) sameGround++;
        }
      }
      // T-0459: NO BOARD OVER AN OPENING, and it is a VISIBLE-QUALITY fault so it
      // is tested here rather than only in the commit gate. The owner reported
      // boards sitting over doors and over windows on walls with blank face going
      // spare, and a sweep found it was all twenty of the flat-mounted ones. The
      // record now carries, per flat sign, the door and window rectangles of the
      // wall it hangs on — derived from the same archetype set-out the MESH is
      // built from — and the one rectangle it is deliberately fixed to, which is
      // only ever a door a board was shrunk onto. Anything else it covers is the
      // fault coming back.
      let flatSigns = 0;
      const overOpening = [];
      for (const sg of signs) {
        const fit = sg.opening_fit;
        if (!fit) continue;
        flatSigns++;
        const [ba, bc] = fit.board_span_local_m;
        // `arm_height_m` is the board's HEAD; a wall board carries a rain cap over
        // it, which signage.js stands 0.09 m proud of the same wall.
        const top = sg.arm_height_m + (sg.mounting === 'wall_board' ? 0.09 : 0);
        const bot = sg.arm_height_m - sg.board_h_m;
        const on = fit.fixed_to;
        for (const o of fit.openings || []) {
          if (o.u0 >= bc || o.u1 <= ba || o.z0 >= top || o.z1 <= bot) continue;
          const isFixture = on && o.kind === on.kind && o.u0 === on.u0
            && o.u1 === on.u1 && o.z0 === on.z0 && o.z1 === on.z1
            && ba >= on.u0 && bc <= on.u1 && bot >= on.z0 && top <= on.z1;
          if (!isFixture) overOpening.push(`${sg.structure_id} over ${o.kind}`);
        }
      }
      // The South Water row, which is the street the town actually reads as one:
      // every sign whose anchor sits on the frontage line north of the block.
      const row = signs.filter((sg) => sg.anchor_local_enu_m[1] > -10
        && sg.anchor_local_enu_m[1] < 12
        && sg.anchor_local_enu_m[0] > 180 && sg.anchor_local_enu_m[0] < 760);
      return {
        census: s?.census ?? null,
        meshes: s?.group?.children?.length ?? 0,
        verts: g?.getAttribute('position')?.count ?? 0,
        hasConfidence: !!conf,
        hasUV: !!g?.getAttribute('uv'),
        hasMap: !!mesh?.material?.map,
        casts: mesh?.castShadow === true,
        ungraded,
        notReconstructed,
        worstOver,
        worstReach,
        worstInside,
        unattributed,
        spans: spans.length,
        signs: signs.length,
        flatSigns,
        overOpening,
        named: signs.filter((sg) => (sg.sign_text || '').trim().length > 0).length,
        // T-0130: the board and the card have to agree about WHO, over the whole
        // set and not only at the Tremont. Punctuation is dropped because the
        // board keeps the advertisement's own spelling ("Steam-Boat Hotel") and
        // the card carries this project's ("Steamboat Hotel").
        identityMismatch: signs.filter((sg) => {
          const norm = (s) => String(s || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
          const id = norm(sg.sign_identity);
          return !id || !norm(sg.sign_text).includes(id) || !norm(sg.name).includes(id);
        }).map((sg) => sg.structure_id),
        // And no board has gone back to carrying this project's own way of
        // describing a BUILDING. "Log" is the tell T-0130 was raised over.
        labelled: signs.filter((sg) => /\blog\b/i.test(sg.sign_text || ''))
          .map((sg) => sg.structure_id),
        // Every board names a trade as well as a proprietor — the register the
        // advertisements use, and the thing a descriptive label never carried.
        withTrade: signs.filter((sg) => (sg.sign_lines || [])
          .some((l) => l.role === 'trade')).length,
        devices: signs.filter((sg) => sg.sign_device).map((sg) => sg.structure_id),
        distinctArt: new Set(uvRects.values()).size,
        mountings: new Set(signs.map((sg) => sg.mounting)).size,
        grounds: new Set(signs.map((sg) => sg.style?.ground)).size,
        faces: new Set(signs.map((sg) => sg.style?.face)).size,
        pairs,
        sameStyle,
        sameGround,
        rowSigns: row.length,
        rowMountings: new Set(row.map((sg) => sg.mounting)).size,
        rowGrounds: new Set(row.map((sg) => sg.style?.ground)).size,
        ids: signs.map((sg) => sg.structure_id),
      };
    });
    check(`${label}: the signage layer puts up the record's signs`,
      boards.census?.boards >= 20 && boards.signs === boards.census?.boards
        && boards.spans === boards.signs && boards.unattributed === 0
        && boards.verts > 0,
      `${boards.census?.boards} sign(s) from ${boards.census?.records} record(s), `
      + `${boards.verts} vertices, ${boards.census?.refused} frontage(s) refused`);
    check(`${label}: the whole signage layer is one draw call`,
      boards.meshes === 1, `${boards.meshes} mesh(es) in the group`);
    // T-0459. The count is asserted as well as the faults, so the test cannot pass
    // by finding no flat signs to look at.
    check(`${label}: no board is fixed over a door or a window`,
      boards.flatSigns >= 15 && boards.overOpening?.length === 0,
      `${boards.flatSigns} flat-mounted board(s) tested against their own wall's `
      + `openings, ${boards.overOpening?.length ?? '?'} over one`
      + (boards.overOpening?.length ? `: ${boards.overOpening.join(', ')}` : ''));
    // AND ITS SHADOW IS STILL IN THE FRAME. T-0115 dropped the derived furniture
    // out of the shadow map at `light` and put the signboards back in by
    // measurement, because the shadow is most of what a board contributes to the
    // frame at the Tremont's footway. A later trim that quietly swept them up
    // with the fences would fail here rather than in the liveness check below.
    check(`${label}: the signs still cast into the shadow map`,
      boards.casts, `signage mesh castShadow ${boards.casts}`);
    // NOT MERELY GRADED — graded reconstructed, every vertex of it. The fact of
    // a sign on these frontages is invented (L130) and so are its wording, its
    // colours and its mounting (L159); a single vertex claiming to be inferred
    // or attested would be this layer overstating the one thing it must not.
    check(`${label}: every signboard vertex is graded reconstructed`,
      boards.hasConfidence && boards.ungraded === 0 && boards.notReconstructed === 0,
      `attribute ${boards.hasConfidence ? 'present' : 'MISSING'}, ${boards.ungraded} out `
      + `of range, ${boards.notReconstructed} claiming better than reconstructed`);
    // EVERY SIGN INSIDE ITS OWN DECLARED REACH. The record computes, per sign,
    // how far its own mounting may put a vertex from its own anchor — 1.06 m for
    // a board fixed flat on a wall, 2.58 m for a post out at the street edge —
    // so this holds the smallest board to a bound a metre tighter than the
    // largest one needs, which one flat number never could. The 3 m ceiling on
    // the reaches themselves is the second half of it: a mounting that declared
    // itself twenty metres long would satisfy the first test and fail this one.
    check(`${label}: no sign strays past the reach its own mounting declares`,
      boards.worstOver > -Infinity && boards.worstOver <= 0.05
        && boards.worstReach <= 3.0,
      `worst vertex ${boards.worstOver?.toFixed(3)} m past its own reach; `
      + `largest reach declared ${boards.worstReach?.toFixed(2)} m`);
    // And it stands OUT of the wall, not into the parlour behind it. A painted
    // name lies ON the front by construction, so the bar is a few centimetres of
    // tolerance rather than zero.
    check(`${label}: every sign stands outside its own facade`,
      boards.worstInside >= -0.05,
      `deepest vertex ${boards.worstInside?.toFixed(3)} m behind the facade plane`);
    // --- what the signs SAY, and that no two of them are alike (T-0066) ------
    //
    // The owner asked for three things in one sentence — the name on the board,
    // variation in colour and style, and more signage — and all three are the
    // kind of thing that erodes silently. A refactor that lost the atlas would
    // draw thirty-three blank planks and error nowhere.
    check(`${label}: every sign carries its business's name, painted`,
      boards.named === boards.signs && boards.census?.lettered === boards.signs
        && boards.hasUV && boards.hasMap
        && boards.distinctArt === boards.signs,
      `${boards.named}/${boards.signs} named, ${boards.census?.lettered} lettered, `
      + `uv ${boards.hasUV ? 'present' : 'MISSING'}, `
      + `atlas ${boards.hasMap ? 'bound' : 'MISSING'}, `
      + `${boards.distinctArt} distinct painted face(s)`);
    check(`${label}: no two signs within sight of each other are alike`,
      boards.pairs > 0 && boards.sameStyle === 0 && boards.sameGround === 0,
      `${boards.pairs} pair(s) within 40 m — ${boards.sameStyle} share a style, `
      + `${boards.sameGround} share a ground colour`);
    check(`${label}: the town puts its signs up five different ways`,
      boards.mountings >= 5 && boards.grounds >= 8 && boards.faces >= 4,
      `${boards.mountings} mounting(s), ${boards.grounds} ground colour(s), `
      + `${boards.faces} letterform(s) across ${boards.signs} signs`);
    check(`${label}: one street's signs are visibly different from each other`,
      boards.rowSigns >= 6 && boards.rowMountings >= 3 && boards.rowGrounds >= 5,
      `South Water row: ${boards.rowSigns} sign(s), ${boards.rowMountings} `
      + `mounting(s), ${boards.rowGrounds} ground colour(s)`);

    // AND IT READS FROM THE STREET, which is the whole point of a sign. Stand on
    // the footway in front of the Tremont House — a south-facing hotel frontage —
    // hold the clock so the grass cannot supply the difference, and compare the
    // frame with the layer hidden.
    //
    // THE STAND IS 3.5 m AND THAT NUMBER IS LOAD-BEARING, so it is explained
    // rather than left as a coordinate. A board is 0.88 x 0.50 m. Measured on
    // this runner from 8 m back it is plainly on screen — the crosshair picks it
    // — and the 12-cell signature reads worst 4, because one cell of a 12x12
    // grid is wider than the whole board at that range and averages it away. The
    // answer is to stand where a person reading a sign stands, not to widen the
    // grid or drop the threshold: at 3.5 m the same measurement reads worst 11 /
    // mean 0.55 on desktop and 17 / 0.72 on mobile, against the SAME bar the two
    // fence gates above use.
    await page.evaluate(() => window.__chicago4d.walker.teleport(
      { local_e: 678.5, local_n: -104.06, yaw_deg: 0, pitch_deg: 8 }));
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const signWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.signage.group.visible = false; });
    const signWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.signage.group.visible = true; });
    const dSign = signatureDistance(signWith, signWithout);
    check(`${label}: the hotel's board reaches the screen from the street`,
      dSign.worst >= 6 && dSign.mean >= 0.3,
      `cell delta mean ${dSign.mean?.toFixed(2)}, worst ${dSign.worst} (need worst>=6)`);

    // A sign is a thing you read and then walk into, so aiming at the board has
    // to open the business behind it and not the wall past it — AND THE CARD IT
    // OPENS HAS TO BE THE SAME BUSINESS (T-0066, corrected by T-0130). The
    // record carries `sign_identity` for exactly that agreement, and this is
    // where the board and the card are put side by side.
    const boardPick = await page.evaluate(() => {
      const hits = [];
      let card = null;
      for (const x of [-0.2, -0.1, 0, 0.1, 0.2]) {
        for (const y of [-0.1, 0, 0.1, 0.2, 0.3]) {
          const hit = window.__chicago4d.pick({ x, y });
          if (!hit?.id) continue;
          hits.push(hit.id);
          if (hit.id === 'tremont_house_1' && !card) {
            card = hit.record?.sidecar?.name ?? null;
          }
        }
      }
      const sign = (window.__chicago4d.signage.signs ?? [])
        .find((s) => s.structure_id === 'tremont_house_1') ?? null;
      return {
        hits, card, painted: sign?.sign_text ?? null,
        identity: sign?.sign_identity ?? null,
      };
    });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    check(`${label}: aiming at a signboard opens the business behind it`,
      boardPick.hits.includes('tremont_house_1'),
      `25 aims returned [${[...new Set(boardPick.hits)].join(', ') || 'nothing'}]`);
    // THIS ASSERTION IS CORRECTED BY T-0130, NOT RELAXED BY IT, and the
    // difference is worth being explicit about because a check that gets weaker
    // usually got weaker to go green.
    //
    // T-0066 asserted STRING EQUALITY: the painted name IS the card's name, up
    // to a trailing parenthetical. That was enforcing the wrong invariant,
    // because it took two different objects to be one. A record's `name` is OUR
    // LABEL FOR A BUILDING — "Philo Carpenter's Log Drug Store", "Hogan's Store"
    // — written so a modern reader knows which structure is meant. A SIGNBOARD
    // carries what the trade lettered: the proprietor or firm and his trade, in
    // the register a signwriter worked in. Held to equality, the board could
    // only ever be the museum caption, which is the defect T-0130 was raised
    // over. The two are now allowed to differ.
    //
    // What must NOT differ is WHO. A visitor who reads a name off a plank and
    // then taps the plank must not be shown a different business, so the record
    // declares a `sign_identity` — the proprietor, the firm or the house — and
    // it has to appear in the board AND in the card. That is asserted here at
    // the Tremont's own board against the CARD THE PICK ACTUALLY OPENED, and
    // over every sign in the town in the check below, which is more than
    // equality ever covered: equality was only ever tested at this one board.
    const cardName = (boardPick.card ?? '').trim();
    const norm = (s) => String(s || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
    const who = norm(boardPick.identity);
    check(`${label}: the board and the card agree about whose business this is`,
      !!boardPick.painted && !!cardName && !!who
      && norm(boardPick.painted).includes(who) && norm(cardName).includes(who),
      `board reads "${boardPick.painted ?? 'nothing'}", card says `
      + `"${boardPick.card ?? 'nothing'}", both must carry `
      + `"${boardPick.identity ?? 'no declared identity'}"`);
    check(`${label}: every board names its proprietor and its trade, not our label`,
      boards.identityMismatch?.length === 0 && boards.labelled?.length === 0
        && boards.withTrade === boards.signs,
      `${boards.identityMismatch?.length} board(s) disagree with their card `
      + `[${(boards.identityMismatch ?? []).join(', ')}], `
      + `${boards.labelled?.length} carry a building label `
      + `[${(boards.labelled ?? []).join(', ')}], `
      + `${boards.withTrade}/${boards.signs} letter a trade`);
    // ONE PAINTED DEVICE IN THE TOWN, and it is the one a Chicago tradesman
    // described himself: Carpenter's golden mortar, from his own 1835 notice
    // "AT THE SIGN OF THE GOLDEN MORTAR". A device must not spread to trades
    // whose advertisements name none — that would be this layer generalising an
    // invention — so the count is pinned exactly rather than bounded below.
    check(`${label}: the golden mortar is on Carpenter's board and on no other`,
      boards.devices?.length === 1
        && boards.devices[0] === 'carpenter_south_water_store',
      `${boards.devices?.length} device(s) [${(boards.devices ?? []).join(', ')}]`);

    // --- and part 1 hands the page on clean (T-0369) -------------------------
    //
    // The twenty-five aims above are `pick()` calls, and a pick that lands on a
    // structure OPENS THE INSPECT CARD. The last one lands on the Tremont
    // House's signboard, so this part used to END with `#popup` standing —
    // `position: fixed`, `z-index: 30`, `top: 58px`, `right: 12px`, 392 px wide,
    // which on a 1280 x 800 viewport is squarely on top of the HUD panel's tab
    // strip. Nothing between here and part 7 reads panel chrome, so nothing
    // noticed. Part 8 is nothing BUT panel chrome and its first statement clicks
    // a tab, so it inherited an unclickable strip and died on it: same commit,
    // one command apart, `SMOKE_STAGE=8` reached the settings tab and
    // `SMOKE_STAGE=1,8` failed with `covered at its own centre by <h2>`.
    //
    // So the part that opened the card closes it, and the teardown is ASSERTED
    // rather than silent. A stage that hands on an overlay standing over the
    // chrome is the defect, and the next one to do it should be named here — at
    // the boundary where it happened — instead of surfacing four parts later
    // under some other gate's name.
    const part1Overlays = await page.evaluate(() => {
      window.__chicago4d.popup.close();
      return ['popup', 'control-help'].filter((id) => {
        const el = document.getElementById(id);
        return el && !el.hasAttribute('hidden');
      });
    });
    check(`${label}: part 1 hands the page on with nothing standing over the chrome`,
      part1Overlays.length === 0,
      `still showing: ${part1Overlays.map((id) => `#${id}`).join(', ') || 'nothing'}`);

    inStageWork = false;
    } // end PART 1 (T-0060 stage 1a, cut by T-0121)
    // PART 2 — the goods at the trading frontages through the confidence
    // machinery's inert state: the rest of T-0060's stage 1. The cut is a
    // section boundary with no crossing binding (checked scope-aware, the way
    // T-0060's three were) and no page state to inherit — everything below
    // reads the scene graph or takes its own capture, and the gate screen it
    // boots behind is exactly what an unfiltered run is standing at here.
    if (stageOn(2)) {
    inStageWork = true;

    // --- the goods at the trading frontages (T-0040) -------------------------
    //
    // The third layer drawn from the dataset rather than baked, and the first
    // one whose objects stand on the GROUND rather than on a building. That is
    // where its failure modes live and they are not the signboards': a barrel
    // hung off the wall base like a board would float or sink wherever the
    // footway is not level, and a barrel is a body of revolution built from a
    // frame this file has never had to check before, so a transposed axis puts
    // a hundred and fifty casks inside the shops they belong to. Every dataset
    // gate in this repo would pass through all of that. So the geometry is
    // measured against the record here, and nowhere else.
    const goods = await page.evaluate(() => {
      const y = window.__chicago4d.yard;
      // T-0064. The layer used to be one mesh and is now one mesh PER CHUNK of
      // the town, all on the same material — sixty-four more wagons over a square
      // kilometre would otherwise have drawn in every frame, behind the camera
      // included (T-0115 item 2). So everything below reads the chunks together:
      // the geometry is still one buffer's worth of contract, in several pieces.
      const meshes = (y?.group?.children ?? []).filter((m) => m.isMesh);
      const geos = meshes.map((m) => m.geometry).filter(Boolean);
      const frontages = y?.frontages ?? [];
      const wagons = y?.wagons ?? [];
      const benches = y?.benches ?? [];
      const sheds = y?.sheds ?? [];
      const items = [];
      for (const f of frontages) {
        for (const it of f.items ?? []) {
          items.push({ e: it.at_local_enu_m[0], n: it.at_local_enu_m[1],
            b: ((it.bearing_deg ?? 0) * Math.PI) / 180 });
        }
      }
      // T-0057. The building material on the one lot this town can say was going
      // up. A pile is measured by its OWN bound and against its OWN lot, exactly
      // as the wagon, the bench and the shed already are: a 0.75 m bar written
      // for a barrel would fail on a 3.66 m stick that is exactly right.
      const lots = y?.lots ?? [];
      const piles = [];
      for (const lot of lots) {
        for (const it of lot.items ?? []) {
          piles.push({ kind: it.kind, e: it.at_local_enu_m[0], n: it.at_local_enu_m[1],
            b: ((it.bearing_deg ?? 0) * Math.PI) / 180,
            quad: lot.ground_quad_local_enu_m ?? [] });
        }
      }
      let ungraded = 0;
      let notReconstructed = 0;
      let worstStray = 0;      // furthest a vertex sits from its own object's anchor
      let worstInside = 0;     // deepest a vertex sits BEHIND its own facade
      let wagonVerts = 0;
      // T-0080. A bench is 1.83 m of plank, so like the wagon it is measured by
      // its OWN bound instead of being lumped in with the casks — a 0.75 m bar
      // written for a barrel would fail on a bench that is exactly right.
      let benchVerts = 0;
      let benchStray = 0;
      let benchInside = 0;
      // T-0081. The shed is a BAY, not a point: what has to hold is that nothing
      // standing in it — its own timber or the covered wagon under it — reaches
      // through the inn's wall, out past its eaves or up through its roof. So it
      // is measured in the shed's own frame and it is measured FIRST, because the
      // wagon under it shares its centre and would otherwise absorb the roof.
      let pileVerts = 0;
      let pileStray = 0;       // furthest a vertex sits from its own pile's anchor
      let pileInLot = 0;       // vertices standing inside the building's own footprint
      let shedVerts = 0;
      let shedOut = -Infinity;    // furthest out from the wall, along its normal
      let shedIn = Infinity;      // deepest toward the wall (negative is behind it)
      let shedHigh = -Infinity;
      let shedLow = Infinity;
      let lowest = Infinity;
      let highest = -Infinity;
      let hasConfidence = geos.length > 0;
      for (const geo of geos) {
        const conf = geo.getAttribute('_confidence');
        if (!conf) { hasConfidence = false; continue; }
        for (let i = 0; i < conf.count; i++) {
          const v = conf.getX(i);
          if (!(v >= 0 && v <= 1)) ungraded++;
          else if (v < 1) notReconstructed++;
        }
      }
      // T-0064. Sixty-eight wagons against a hundred thousand vertices is seven
      // million distance tests if it is written the obvious way, so the wagons go
      // into 8 m buckets first and each vertex only asks the nine buckets round it.
      const BUCKET = 8;
      const wagonGrid = new Map();
      wagons.forEach((wg, i) => {
        const at = wg.at_local_enu_m;
        const key = `${Math.floor(at[0] / BUCKET)},${Math.floor(at[1] / BUCKET)}`;
        if (!wagonGrid.has(key)) wagonGrid.set(key, []);
        wagonGrid.get(key).push(i);
      });
      const wagonNear = (e, n) => {
        const ce = Math.floor(e / BUCKET);
        const cn = Math.floor(n / BUCKET);
        for (let de = -1; de <= 1; de++) {
          for (let dn = -1; dn <= 1; dn++) {
            for (const i of wagonGrid.get(`${ce + de},${cn + dn}`) ?? []) {
              const at = wagons[i].at_local_enu_m;
              if (Math.hypot(e - at[0], n - at[1]) <= 4.6) return wagons[i];
            }
          }
        }
        return null;
      };
      // The piles are nine objects on one lot 130 m from the nearest wagon and
      // further still from the nearest cask, so a plain radius claims them with
      // nothing to collide with. The radius is the widest pile's own reach — a
      // timber stick 3.66 m long lying across its pile — plus a margin.
      // It returns the NEAREST pile and not the first one inside the radius: the
      // brick stacks stand 3.2 m apart, so a vertex at the near end of one falls
      // inside its neighbour's radius too, and taking the first match measured
      // it against the wrong anchor and reported 2.49 m of stray on geometry
      // that is exactly where the record puts it.
      const pileNear = (e, n) => {
        let best = null;
        let bestD = 2.6;
        for (const pl of piles) {
          const d = Math.hypot(e - pl.e, n - pl.n);
          if (d <= bestD) { bestD = d; best = pl; }
        }
        return best;
      };
      const inQuad = (e, n, quad) => {
        let inside = false;
        for (let i = 0, j = quad.length - 1; i < quad.length; j = i, i += 1) {
          const [xi, yi] = quad[i];
          const [xj, yj] = quad[j];
          if ((yi > n) !== (yj > n)
            && e < xi + ((n - yi) * (xj - xi)) / ((yj - yi) || 1e-12)) inside = !inside;
        }
        return inside;
      };
      for (const geo of (items.length ? geos : [])) {
        const pos = geo.getAttribute('position');
        for (let i = 0; i < pos.count; i++) {
          // world is (E, up, -N)
          const e = pos.getX(i);
          const n = -pos.getZ(i);
          lowest = Math.min(lowest, pos.getY(i));
          highest = Math.max(highest, pos.getY(i));
          // The shed's bay first: along the wall and out of it, in the shed's own
          // frame. The wagon's tongue reaches past the bay and is left to the
          // wagon bound below, which is exactly where it belongs.
          let inBay = false;
          for (const sh of sheds) {
            const sb = ((sh.bearing_deg ?? 0) * Math.PI) / 180;
            const de = e - sh.at_local_enu_m[0];
            const dn = n - sh.at_local_enu_m[1];
            const along = de * Math.cos(sb) - dn * Math.sin(sb);
            const out = de * Math.sin(sb) + dn * Math.cos(sb);
            if (Math.abs(along) > (sh.length_m ?? 0) / 2 + 0.4) continue;
            if (Math.abs(out) > (sh.depth_m ?? 0) / 2 + 0.5) continue;
            shedVerts++;
            shedOut = Math.max(shedOut, out);
            shedIn = Math.min(shedIn, out);
            shedHigh = Math.max(shedHigh, pos.getY(i));
            shedLow = Math.min(shedLow, pos.getY(i));
            inBay = true;
            break;
          }
          if (inBay) continue;
          // T-0057's piles, claimed before the wagons: a pile is measured for how
          // far it reaches from its own anchor and for the one thing that would
          // make it wrong, which is a stack of brick standing inside the building
          // it was delivered for.
          const pl = pileNear(e, n);
          if (pl) {
            pileVerts++;
            pileStray = Math.max(pileStray, Math.hypot(e - pl.e, n - pl.n));
            if (inQuad(e, n, pl.quad)) pileInLot++;
            continue;
          }
          // A wagon is 3 m of body and a 2.75 m tongue, so it is measured by its
          // own bound rather than lumped in with the casks.
          const w = wagonNear(e, n);
          if (w) { wagonVerts++; continue; }
          // A bench's furthest corner is hypot(L/2, D/2) = 0.93 m from its
          // anchor, so 1.1 m catches it and nothing else on the layer.
          const bh = benches.find((bn) => Math.hypot(e - bn.at_local_enu_m[0],
            n - bn.at_local_enu_m[1]) <= 1.1);
          if (bh) {
            benchVerts++;
            benchStray = Math.max(benchStray, Math.hypot(e - bh.at_local_enu_m[0],
              n - bh.at_local_enu_m[1]));
            const bb = ((bh.bearing_deg ?? 0) * Math.PI) / 180;
            benchInside = Math.min(benchInside,
              (e - bh.at_local_enu_m[0]) * Math.sin(bb)
              + (n - bh.at_local_enu_m[1]) * Math.cos(bb));
            continue;
          }
          let best = null;
          let bestD = Infinity;
          for (const it of items) {
            const d = Math.hypot(e - it.e, n - it.n);
            if (d < bestD) { bestD = d; best = it; }
          }
          worstStray = Math.max(worstStray, bestD);
          // Positive is out of the wall, along the facade's own normal.
          const outward = (e - best.e) * Math.sin(best.b) + (n - best.n) * Math.cos(best.b);
          worstInside = Math.min(worstInside, outward);
        }
      }
      const verts = geos.reduce(
        (t, geo) => t + (geo.getAttribute('position')?.count ?? 0), 0);
      return {
        census: y?.census ?? null,
        meshes: meshes.length,
        // One material across every chunk, which is what makes the chunking a
        // CULLING decision rather than a second layer.
        materials: new Set(meshes.map((m) => m.material?.uuid)).size,
        // And every chunk has to carry its own bounding sphere, or the frustum
        // has nothing to test and the split bought nothing at all.
        bounded: geos.every((geo) => !!geo.boundingSphere),
        // T-0065. The marks ride on the ONE material as a canvas atlas, so what
        // has to hold is that the material carries a map at all, that every
        // chunk carries the uv to read it with, and that no uv leaves the sheet
        // — a uv off the atlas is a mark painted on nothing, silently.
        mapped: meshes.every((m) => !!m.material?.map?.image),
        hasUV: geos.length > 0 && geos.every((geo) => !!geo.getAttribute('uv')),
        uvOut: (() => {
          let bad = 0;
          for (const geo of geos) {
            const uv = geo.getAttribute('uv');
            if (!uv) { bad += 1; continue; }
            for (let i = 0; i < uv.count; i += 1) {
              const u = uv.getX(i);
              const v = uv.getY(i);
              if (!(u >= 0 && u <= 1 && v >= 0 && v <= 1)) bad += 1;
            }
          }
          return bad;
        })(),
        verts,
        tris: verts / 3,
        hasConfidence,
        ungraded,
        notReconstructed,
        worstStray,
        worstInside,
        wagonVerts,
        benchVerts,
        benchStray,
        benchInside,
        benches,
        pileVerts,
        pileStray,
        pileInLot,
        lots,
        piles: piles.length,
        shedVerts,
        shedOut,
        shedIn,
        shedSpan: Number.isFinite(shedLow) ? shedHigh - shedLow : null,
        shed: sheds[0] ?? null,
        sheds: sheds.length,
        // One material and the tilt still reads as canvas: the colour is per
        // vertex, so the whole layer must carry exactly its OWN tones and no
        // more. It was two — timber and duck — until T-0057 put brick and stone
        // on a building lot, and four is now the number a second material would
        // have been needed for.
        tones: (() => {
          const seen = new Set();
          for (const geo of geos) {
            const c = geo.getAttribute('color');
            if (!c) return 0;
            for (let i = 0; i < c.count; i++) {
              seen.add(`${c.getX(i).toFixed(4)},${c.getY(i).toFixed(4)},`
                + `${c.getZ(i).toFixed(4)}`);
            }
          }
          return seen.size;
        })(),
        span: Number.isFinite(lowest) ? highest - lowest : null,
        frontages: frontages.length,
        items: items.length,
        wagon: wagons.find((w) => w.in_enclosure === 'western_hotel_wagon_yard') ?? null,
        greenTreeWagons: wagons.filter((w) => w.belongs_to === 'green_tree_tavern'
          && !w.under_shed),
        tiltWagon: wagons.find((w) => w.under_shed) ?? null,
        // ---- T-0064: the town's wagons ------------------------------------ //
        // The record's own list, carried out whole so the checks below can ask
        // it questions the census cannot answer — where each one stands, what
        // kind it is, which way it faces, and whether it is graded.
        townWagons: wagons.filter((w) => w.stands_on || w.in_enclosure)
          .map((w) => ({ id: w.id, kind: w.kind ?? 'farm_box',
            e: w.at_local_enu_m[0], n: w.at_local_enu_m[1],
            bearing: w.bearing_deg ?? 0, street: w.stands_on ?? null,
            enclosure: w.in_enclosure ?? null, confidence: w.confidence,
            yoke: !!w.yoke, tilt: !!w.tilt,
            // T-0688. The deal T-0836 made, carried out whole: how far off its
            // square bearing this wagon stands, the envelope it was dealt inside
            // and how many steps that envelope was walked in. The two wagons the
            // record holds by hand — the attested Western Hotel wagon and the
            // Randolph Street water cart — carry no slew, and read as null here.
            drawnUp: w.drawn_up ?? null,
            slew: typeof w.slew_deg === 'number' ? w.slew_deg : null,
            slewEnvelope: typeof w.slew_envelope_deg === 'number' ? w.slew_envelope_deg : null,
            slewSteps: typeof w.slew_steps === 'number' ? w.slew_steps : null })),
        wagonsRefused: (y?.records ?? []).reduce(
          (t, r) => t + (r.wagons_refused ?? []).length, 0),
      };
    });
    check(`${label}: the yard layer stands the record's goods`,
      goods.census?.frontages >= 20 && goods.items >= 120 && goods.verts > 0
        && goods.census?.wagons >= 60 && goods.census?.benches === 1
        && goods.census?.sheds === 1,
      `${goods.items} object(s) on ${goods.census?.frontages} frontage(s) from `
      + `${goods.census?.records} record(s), ${goods.census?.wagons} wagon(s), `
      + `${goods.census?.benches} bench(es), ${goods.census?.sheds} shed(s), `
      + `${goods.verts} vertices, ${goods.census?.refused} frontage(s) refused`);
    // T-0064. The layer was ONE draw call while it was barrels on twenty-six
    // frontages; sixty-four more wagons spread over a square kilometre made a
    // single town-wide geometry the thing T-0115 item 2 measured and named — a
    // bounding sphere no frustum culls, so every wagon in Chicago drew in every
    // frame. It chunks now, the way `frontage.js` and `enclosures.js` do. What
    // must still hold, and is the whole reason chunking is cheap: ONE material
    // across every chunk, and every chunk carrying its own bounding sphere.
    check(`${label}: the yard layer chunks for culling on a single material`,
      goods.meshes > 1 && goods.meshes <= 64 && goods.materials === 1
        && goods.bounded,
      `${goods.meshes} chunk mesh(es), ${goods.materials} material(s), `
      + `bounding spheres ${goods.bounded ? 'on every chunk' : 'MISSING on one'}`);
    // T-0065. Every cask and every case carries a mark the record dealt it — a
    // stencilled commodity, the house's brand, or a shipping mark — and the
    // census counts what was actually PAINTED rather than what the record asked
    // for, so an atlas that silently refused a cell reads as a shortfall here.
    check(`${label}: every cask and case carries the mark its record deals it`,
      goods.census?.marked === goods.items && goods.census?.markCells >= 40,
      `${goods.census?.marked} of ${goods.items} object(s) marked, out of `
      + `${goods.census?.markCells} atlas cell(s)`);
    // And the marks cost the layer nothing it did not already spend: they are
    // painted on the SAME single material as a texture, so every chunk carries
    // a uv and every uv lands on the sheet. Everything unmarked reads the white
    // cell, which multiplies to the timber it was before there was an atlas.
    check(`${label}: the marks ride on the layer's own material, on the sheet`,
      goods.mapped && goods.hasUV && goods.uvOut === 0,
      `map ${goods.mapped ? 'present' : 'MISSING'}, uv `
      + `${goods.hasUV ? 'on every chunk' : 'MISSING on one'}, ${goods.uvOut} `
      + 'coordinate(s) off the atlas');
    // NOT MERELY GRADED — graded reconstructed, every vertex of it. That goods
    // stood at these doors on this day is invented (L131) and a single vertex
    // claiming to be inferred or attested would be this layer overstating the
    // one thing it must not.
    check(`${label}: every yard-goods vertex is graded reconstructed`,
      goods.hasConfidence && goods.ungraded === 0 && goods.notReconstructed === 0,
      `attribute ${goods.hasConfidence ? 'present' : 'MISSING'}, ${goods.ungraded} out `
      + `of range, ${goods.notReconstructed} claiming better than reconstructed`);
    // A cask is 0.53 m at the bilge and a case 1.05 m long, so nothing on a
    // frontage legitimately reaches 0.75 m from its own anchor — a transposed
    // axis or a dropped rotation would be metres out, not centimetres.
    check(`${label}: no barrel or case strays from the frontage it stands at`,
      goods.worstStray > 0 && goods.worstStray <= 0.75,
      `furthest vertex ${goods.worstStray?.toFixed(2)} m from its own object's anchor`);
    // And the goods stand ON the footway, not inside the shop. The record stands
    // them 0.55 m out from the facade plane and the widest thing here is a case
    // 0.72 m across, so 0.45 m back from an anchor is still 0.10 m clear of the
    // wall; a sign flip anywhere in the frame would put them a metre inside it.
    check(`${label}: every object stands outside its own facade`,
      goods.worstInside >= -0.45,
      `deepest vertex ${goods.worstInside?.toFixed(3)} m behind its object's anchor`);
    // The wagon is drawn, in the yard whose own name is the attestation, with
    // the clearance the record derived for it.
    check(`${label}: the attested wagon stands in the yard it is named for`,
      goods.wagonVerts > 0 && goods.wagon?.in_enclosure === 'western_hotel_wagon_yard'
        && goods.wagon?.clearance_m >= 1.6,
      `${goods.wagonVerts} wagon vertices, ${goods.wagon?.clearance_m} m clear in `
      + `${goods.wagon?.in_enclosure}`);
    // T-0080. The Green Tree's two, from the Trowbridge view: they stand square
    // to the inn's rear wall — the bearing is the facade's own plus 180 — and
    // every one of them cleared the committed walls by the margin a parked wagon
    // is given, or the generator would have refused it in writing instead.
    check(`${label}: the Green Tree's yard wagons stand clear, square to its rear wall`,
      goods.greenTreeWagons?.length === 2
        && goods.greenTreeWagons.every((w) => w.clearance_m >= 1.6
          && w.bearing_deg === 90 && w.confidence === 'reconstructed'),
      `${goods.greenTreeWagons?.length} wagon(s), clearances `
      + `${goods.greenTreeWagons?.map((w) => w.clearance_m).join(', ')}, bearings `
      + `${goods.greenTreeWagons?.map((w) => w.bearing_deg).join(', ')}`);
    // And the bench is drawn, against the wall rather than through it. Its
    // furthest corner is hypot(1.83/2, 0.36/2) = 0.93 m from its anchor, and the
    // record stands that anchor half the seat's depth off the facade plane, so
    // nothing may sit more than 0.18 m behind it — a sign flip on the standoff
    // would put the whole bench inside the bar-room.
    check(`${label}: the bench stands against the Green Tree's front wall`,
      goods.benchVerts > 0 && goods.benchStray > 0 && goods.benchStray <= 1.0
        && goods.benchInside >= -0.20,
      `${goods.benchVerts} bench vertices, furthest ${goods.benchStray?.toFixed(2)} m `
      + `from its anchor, deepest ${goods.benchInside?.toFixed(3)} m behind it`);

    // T-0081. THE WAGON SHED, which is the first roof this layer has ever drawn.
    // The record claims a bay, two plate heights and a fall between them; a shed
    // whose head is not above its eave is not a lean-to, and one whose eave does
    // not clear the tilt is a shed the covered wagon cannot stand in.
    const tiltTop = 0.95 + 0.55 + 1.10;   // bed + body + the tilt's rise
    check(`${label}: the Green Tree's wagon shed is a lean-to that clears its tilt`,
      goods.sheds === 1 && goods.shed?.confidence === 'reconstructed'
        && goods.shed?.head_m > goods.shed?.eave_m
        && goods.shed?.eave_m >= tiltTop
        && goods.shed?.length_m >= 3.05 && goods.shed?.depth_m >= 3.2
        && goods.shed?.clearance_m >= 1.0
        && goods.tiltWagon?.tilt === true,
      `${goods.sheds} shed(s), bay ${goods.shed?.length_m} x ${goods.shed?.depth_m} m, `
      + `eave ${goods.shed?.eave_m} m over a ${tiltTop.toFixed(2)} m tilt, head `
      + `${goods.shed?.head_m} m, ${goods.shed?.clearance_m} m clear, covered wagon `
      + `${goods.tiltWagon ? goods.tiltWagon.id : 'MISSING'}`);
    // And it is BUILT inside its own bay. Nothing standing in it may reach back
    // through the inn's clapboard, out past the eaves the record gives it, or up
    // through its own roof — the three ways a transposed axis or a dropped sign
    // would show, and none of them is visible from a census.
    check(`${label}: nothing in the shed's bay reaches through its wall or its roof`,
      goods.shedVerts > 0
        && goods.shedIn >= -(goods.shed?.depth_m / 2 + 0.05)
        && goods.shedOut <= goods.shed?.depth_m / 2 + 0.35
        && goods.shedSpan > 2.8 && goods.shedSpan <= goods.shed?.head_m + 0.25,
      `${goods.shedVerts} vertices in the bay, ${goods.shedIn?.toFixed(3)} m behind `
      + `the wall, ${goods.shedOut?.toFixed(3)} m out from it, `
      + `${goods.shedSpan?.toFixed(2)} m tall against a ${goods.shed?.head_m} m head`);
    // ---- T-0057: the other half of Ordinance 9 ---------------------------- //
    //
    // The ordinance names timber, stone, brick, boxes and barrels; T-0040 drew
    // the boxes and barrels and refused the rest, because building material
    // belongs to a building that is GOING UP and the goods record cannot say
    // which lot was. Exactly one structure in this scene states a construction
    // state in its own attributes — `lake_house_construction`, attested — so
    // what has to hold is that the material is on that lot, in all three
    // materials, and reaches the screen as geometry rather than as a record.
    check(`${label}: the building material stands on the lot that was going up`,
      goods.census?.lots === 1 && goods.census?.piles >= 6 && goods.pileVerts > 0
        && goods.lots?.[0]?.structure_id === 'lake_house_construction'
        && (goods.census?.byMaterial?.brick ?? 0) > 0
        && (goods.census?.byMaterial?.timber ?? 0) > 0
        && (goods.census?.byMaterial?.stone ?? 0) > 0,
      `${goods.census?.piles} pile(s) on ${goods.census?.lots} lot(s) `
      + `(${JSON.stringify(goods.census?.byMaterial ?? {})}), ${goods.pileVerts} `
      + `vertices, lot ${goods.lots?.[0]?.structure_id ?? 'MISSING'}`);
    // And it stands where a builder's material stands: round the shell, not
    // inside it. The widest pile is a 3.66 m stick lying across its own pile, so
    // 1.90 m is the furthest any vertex may sit from its anchor and 2.1 m is the
    // bar; a transposed axis would be metres out, not centimetres. The second
    // half is the one that would be visible from the street — the generator
    // turned its outward normal the wrong way on its first run and put every
    // one of the nine piles inside the building, which clause 5 caught then and
    // this catches now.
    check(`${label}: no pile of material stands inside the building it is for`,
      goods.pileStray > 0 && goods.pileStray <= 2.1 && goods.pileInLot === 0,
      `furthest vertex ${goods.pileStray?.toFixed(2)} m from its own pile's anchor, `
      + `${goods.pileInLot} vertex/vertices inside the lot's own footprint`);

    // The canvas is canvas. The tilt arrived without a second material, which is
    // only possible because the colour moved onto the geometry — so the whole
    // layer, chunks and all, has to carry exactly two tones: timber and duck.
    check(`${label}: the tilt is drawn in canvas on the layer's one material`,
      goods.tones === 4 && goods.materials === 1,
      `${goods.tones} vertex tone(s) across ${goods.meshes} chunk(s) on `
      + `${goods.materials} material(s)`);

    // ---- T-0064: more wagons, all over a frontier town ---------------------- //
    //
    // The owner, 2026-08-18: "there can be more wagons! of course there would be
    // more wagons all over the place in a frontier town." T-0040 put wagons at
    // two addresses because two addresses is as far as the evidence reaches; the
    // restraint is overruled and the tier is `reconstructed`. What has to hold
    // is not that the wagons are RIGHT — nothing can make an invented wagon right
    // — but that they are SPREAD, VARIED, GRADED and standing on ground the rest
    // of this town has already claimed for something else. Every one of those is
    // decided at load or in the record, and no dataset gate in this repo sees any
    // of it.
    const townWagons = goods.townWagons ?? [];
    const streets = new Set(townWagons.map((w) => w.street).filter(Boolean));
    const kinds = new Set(townWagons.map((w) => w.kind));
    // SPREAD, and it is measured rather than asserted: the wagons have to reach
    // across the town's own streets, not cluster at the two doors the evidence
    // named. Eight streets and 600 m of east-west spread is a walk, not a corner.
    const spanE = townWagons.length
      ? Math.max(...townWagons.map((w) => w.e)) - Math.min(...townWagons.map((w) => w.e))
      : 0;
    const spanN = townWagons.length
      ? Math.max(...townWagons.map((w) => w.n)) - Math.min(...townWagons.map((w) => w.n))
      : 0;
    check(`${label}: the town's wagons are spread across its streets, not at two doors`,
      townWagons.length >= 55 && streets.size >= 14 && spanE >= 1000 && spanN >= 700,
      `${townWagons.length} town wagon(s) on ${streets.size} street(s) plus the `
      + `working yards, spanning ${spanE.toFixed(0)} m east-west and `
      + `${spanN.toFixed(0)} m north-south`);
    // VARIED, in type and in the way they are drawn up. Three kinds, and no one
    // kind may be more than three quarters of them — a town of sixty identical
    // farm wagons is one wagon repeated, which is what the ticket asked against.
    const kindCounts = {};
    for (const w of townWagons) kindCounts[w.kind] = (kindCounts[w.kind] ?? 0) + 1;
    const commonest = Math.max(0, ...Object.values(kindCounts));
    check(`${label}: the town's wagons vary in type`,
      kinds.size >= 3 && kinds.has('covered') && kinds.has('cart')
        && kinds.has('farm_box') && commonest <= townWagons.length * 0.75,
      `${Object.entries(kindCounts).map(([k, v]) => `${v} ${k}`).join(', ')}`);
    // AND IN THE WAY THEY STAND — T-0688, and this clause measures THE WAGON
    // RULE, which the one it replaces did not. It used to count distinct
    // `bearing_deg` to the nearest five degrees against a floor of 8. A town
    // wagon drawn up along a road takes that road's bearing, so what it counted
    // was distinct STREET headings that happened to carry a wagon: re-deriving
    // one street's centreline (T-0447) took the reading from 9 buckets to 7 and
    // failed a gate no wagon rule controls, while the floor of 8 was only the
    // last green reading written down. What the rule does control is the SLEW —
    // T-0836 turns every derived wagon off its square bearing by an angle dealt
    // from its own id, inside an envelope graded by the manoeuvre — so the slew
    // is what is asked about, and every number below is read off the record's
    // own `slew_envelope_deg` and `slew_steps` rather than restated here.
    const dealt = townWagons.filter((w) => w.slew !== null);
    // The two the record holds by hand (the attested Western Hotel wagon, the
    // Randolph Street water cart) are the only ones that may stand undealt.
    const undealt = townWagons.filter((w) => w.slew === null);
    // Every slew inside the envelope its own manoeuvre was graded at. This is
    // the exact clause, not a floor: a wagon outside its envelope is a deal that
    // has escaped the rule, and _lateral_reach set its stand back for an angle
    // it no longer stands at.
    const escaped = dealt.filter((w) => !(w.slewEnvelope > 0)
      || Math.abs(w.slew) > w.slewEnvelope + 1e-6);
    // Three envelopes, because the rule grades the manoeuvre three ways — along
    // a road, backed square to one, and in a yard with no line to work to. All
    // three have to be standing or the grading is untested.
    const envelopes = new Set(dealt.map((w) => w.slewEnvelope));
    // AND THE DEAL HAS TO BE DEALING. The slew is `sha1(id) mod steps` walked
    // end to end over the envelope, which is a uniform deal into `slewSteps`
    // buckets; with sixty-odd wagons over nine steps every step is expected to
    // carry about seven, and the chance a uniform deal leaves even one step
    // empty is well under a percent. So the floor is `slewSteps - 1`: the deal's
    // own step count, with one step of slack for the town gaining or losing a
    // wagon — derived from the rule, not read off a green run. And no step may
    // carry more than a quarter, which is more than double the uniform share.
    const steps = Math.max(0, ...dealt.map((w) => w.slewSteps ?? 0));
    const stepCounts = {};
    for (const w of dealt) {
      const k = `${w.slewEnvelope}:${w.slew.toFixed(1)}`;
      stepCounts[k] = (stepCounts[k] ?? 0) + 1;
    }
    const alongSlews = new Set(dealt.filter((w) => w.drawnUp === 'along the road')
      .map((w) => w.slew.toFixed(1)));
    const commonestStep = Math.max(0, ...Object.values(stepCounts));
    check(`${label}: the town's wagons stand at the slew the rule dealt them`,
      dealt.length >= 55 && undealt.length <= 2 && escaped.length === 0
        && envelopes.size === 3 && steps > 0 && alongSlews.size >= steps - 1
        && commonestStep <= dealt.length * 0.25,
      `${dealt.length} dealt and ${undealt.length} held by hand; `
      + `${escaped.length} outside their own envelope; envelopes `
      + `${[...envelopes].sort((x, z) => x - z).join('/')} degrees; `
      + `${alongSlews.size} of ${steps} steps used along the road, `
      + `commonest step ${commonestStep} of ${dealt.length}`);
    // GRADED, every one of them, and the tilt/yoke flags have to agree with the
    // kind — a covered wagon without its canvas is a farm wagon the record is
    // lying about.
    check(`${label}: every wagon the town gained cards reconstructed`,
      townWagons.length > 0
        && townWagons.every((w) => w.confidence === 'reconstructed')
        && townWagons.every((w) => (w.kind === 'covered') === w.tilt),
      `${townWagons.filter((w) => w.confidence === 'reconstructed').length} of `
      + `${townWagons.length} graded reconstructed, `
      + `${townWagons.filter((w) => w.tilt).length} carrying a tilt`);
    // AND THEY STAND ON GROUND NOTHING ELSE HAS CLAIMED. This is the check the
    // ticket exists for: a wagon on a footway, in a kitchen garden or in the
    // pound is the failure that no census and no screenshot would show. Every
    // wagon's own GROUND — its body and the pole it has down on the grass — is
    // rebuilt here from the record and tested against the plank walks
    // (`frontage.keepOut`, T-0119), the fenced interiors and their treatments
    // (`yards.treatmentAt`, T-0067) and the travelled tracks (`streets`). The
    // page's own APIs answer, not a second copy of the rule.
    const clashes = await page.evaluate(() => {
      const a = window.__chicago4d;
      const wagons = (a.yard?.wagons ?? []).filter((w) => w.stands_on || w.in_enclosure);
      const walks = a.frontage?.keepOut ?? [];
      const inPoly = (pts, e, n) => {
        let inside = false;
        for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
          const [xi, yi] = pts[i];
          const [xj, yj] = pts[j];
          if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) {
            inside = !inside;
          }
        }
        return inside;
      };
      const out = { onWalk: [], inGarden: [], inPen: [], inTrack: [], tested: 0 };
      for (const w of wagons) {
        // The vehicle's ground: 3.05 m of body (1.98 m for a cart) and the pole
        // lying in front of it, 1.5 m across over the hubs. Sampled rather than
        // integrated — a 0.5 m walk of the centreline plus the two rails is far
        // finer than the 1.83 m walk or the 7 m track it is being asked about.
        const cart = w.kind === 'cart';
        const back = cart ? 0.99 : 1.525;
        const fore = cart ? 0.99 + 2.44 : 1.525 + 2.75;
        const b = ((w.bearing_deg ?? 0) * Math.PI) / 180;
        const fe = Math.sin(b);
        const fn = Math.cos(b);
        const se = Math.cos(b);
        const sn = -Math.sin(b);
        for (let t = -back; t <= fore + 1e-6; t += 0.5) {
          for (const s of [-0.75, 0, 0.75]) {
            const e = w.at_local_enu_m[0] + fe * t + se * s;
            const n = w.at_local_enu_m[1] + fn * t + sn * s;
            out.tested += 1;
            for (const rect of walks) {
              if (inPoly(rect.pts, e, n)) { out.onWalk.push(w.id); break; }
            }
            const treatment = a.yards?.treatmentAt?.(e, n) ?? null;
            if (treatment === 'dooryard_garden') out.inGarden.push(w.id);
            if (treatment === 'trodden_earth') out.inPen.push(w.id);
            if (a.streets?.blocksGrowth?.(e, n)) out.inTrack.push(w.id);
          }
        }
      }
      for (const k of ['onWalk', 'inGarden', 'inPen', 'inTrack']) {
        out[k] = [...new Set(out[k])];
      }
      return out;
    });
    check(`${label}: no wagon stands on a plank walk, in a garden or in a pen`,
      clashes.tested > 0 && clashes.onWalk.length === 0
        && clashes.inGarden.length === 0 && clashes.inPen.length === 0,
      `${clashes.tested} ground sample(s): ${clashes.onWalk.length} on a walk `
      + `[${clashes.onWalk.join(', ')}], ${clashes.inGarden.length} in a dooryard `
      + `garden [${clashes.inGarden.join(', ')}], ${clashes.inPen.length} in a pen `
      + `[${clashes.inPen.join(', ')}]`);
    // And out of the travelled way. `streets.blocksGrowth` is the same answer the
    // planters get — the track plus its own shoulder — so a wagon that fails this
    // is standing where the road is drawn and where a visitor walks.
    check(`${label}: no wagon stands in a street's travelled track`,
      clashes.inTrack.length === 0,
      `${clashes.inTrack.length} wagon(s) in the track [${clashes.inTrack.join(', ')}]`);
    // AND THE REFUSALS ARE IN WRITING. A rule that keeps sixty wagons off the
    // town's walks and out of its roads necessarily refuses stands, and a
    // generator that refused silently would leave nothing to argue with — the
    // discipline `generate_business_signboards.py` keeps with its eight.
    check(`${label}: the wagon rule wrote down what it refused`,
      goods.wagonsRefused >= 20,
      `${goods.wagonsRefused} refused wagon stand(s) recorded with a reason`);

    // AND THEY READ FROM THE FOOTWAY, which is the whole point of standing them
    // out. The Tremont House's south front on Lake Street carries the longest
    // group on the layer — four casks, an empty on its side and two cases — so
    // stand where a person walking past them stands, 3.2 m off the wall, and
    // hold the clock so the grass cannot supply the difference. Same bar as the
    // two fence gates and the signboard: worst >= 6 and mean >= 0.3.
    await page.evaluate(() => window.__chicago4d.walker.teleport(
      { local_e: 684.9, local_n: -104.3, yaw_deg: 0, pitch_deg: -10 }));
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const goodsWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.yard.group.visible = false; });
    const goodsWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.yard.group.visible = true; });
    const dGoods = signatureDistance(goodsWith, goodsWithout);
    check(`${label}: the goods reach the screen from the footway`,
      dGoods.worst >= 6 && dGoods.mean >= 0.3,
      `cell delta mean ${dGoods.mean?.toFixed(2)}, worst ${dGoods.worst} (need worst>=6)`);

    // A barrel at a shop door is the nearest thing to the crosshair when a
    // visitor walks up to that door, so aiming at one has to open the business
    // it belongs to rather than the wall behind it.
    const goodsPick = await page.evaluate(() => {
      const hits = [];
      for (const x of [-0.3, -0.15, 0, 0.15, 0.3]) {
        for (const y of [-0.3, -0.15, 0, 0.15, 0.3]) {
          const hit = window.__chicago4d.pick({ x, y });
          if (hit?.id) hits.push(hit.id);
        }
      }
      return hits;
    });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    check(`${label}: aiming at a barrel opens the business it stands at`,
      goodsPick.includes('tremont_house_1'),
      `25 aims returned [${[...new Set(goodsPick)].join(', ') || 'nothing'}]`);

    // --- the frontage layer: the Green Tree (T-0082) and the Sauganash (T-0090) ---
    //
    // The fifth layer drawn from the dataset rather than baked, and the first
    // derived from a building AND a street at once. Its failure modes are its
    // own: a deck laid on one height floats at one end of a frontage and is
    // buried at the other, and a name painted on a board is the first lettering
    // this renderer has ever drawn — a texture that fails to compose leaves a
    // board that looks perfectly finished and says nothing. Neither is visible
    // to any dataset gate in this repo, because both are decided at load.
    //
    // T-0090 added the second record, and with it the first post this layer
    // draws with nothing on it. A hitching post that silently took the sign
    // post's branch would stand 3.6 m tall under a blank board — geometry the
    // dataset gate cannot see either, because the record says 1.30 m and it is
    // the RENDERER that would be wrong. So each post is measured against its own
    // stand's terrain sample, and the lettering count is asserted to stay at one.
    const frontage = await page.evaluate(() => {
      const a = window.__chicago4d;
      const f = a?.frontage;
      const terrain = a?.terrain;
      // The layer's timber is the shared mesh plus the river walk's culling
      // chunks (T-0119) — one material, many bounding spheres. Every vertex
      // assertion below walks all of them.
      const timber = (f?.group?.children ?? [])
        .filter((c) => c.name === 'frontage' || c.name === 'frontage-chunk');
      const mesh = timber.find((c) => c.name === 'frontage');
      const letters = (f?.group?.children ?? []).find((c) => c.name === 'frontage-lettering');
      const post = f?.posts?.[0] ?? null;
      let sink = Infinity;
      let deckTop = -Infinity;
      let highest = -Infinity;
      let boardLow = Infinity;
      let ungraded = 0;
      let notReconstructed = 0;
      let verts = 0;
      for (const t of timber) {
        const conf = t.geometry?.getAttribute('_confidence');
        if (!conf) continue;
        for (let i = 0; i < conf.count; i++) {
          const v = conf.getX(i);
          if (!(v >= 0 && v <= 1)) ungraded++;
          else if (v < 1) notReconstructed++;
        }
      }
      // What a board must tie into is the surface a visitor walks: the ground,
      // or a registered walker deck standing over it — the river walk's
      // crossing footway rides the Slough Log Bridge's committed deck over the
      // slough pool, where the terrain under a board is the carved bed (T-0119).
      //
      // A WALK'S OWN WALKING SURFACE IS NOT SUCH A DECK, and T-0069 is where the
      // difference had to be drawn. The street edge publishes a deck per stretch
      // of its own planks so the visitor stands ON them, and that deck IS the top
      // of the timber being measured — counting it as the base would ask every
      // board to tie into itself and read the whole walk as sunk by its own rise.
      // Those decks are the ones named `…__footway_<n>`; the ground is what their
      // boards tie into and the ground is what they are measured against.
      //
      // AND A WHARF DECK IS NOT ONE EITHER — but since T-0228 it does not have
      // to be excused, because no board stands under one. Two of the seven docks
      // — Carpenter's and Jones's, both on the South Water reach — tie their
      // heels back into the bank the riverside plank walk runs along, and until
      // T-0228 their decks OVERSAILED about 3,000 of this layer's vertices by
      // roughly half a metre. That was excluded here so a walk which had not
      // moved would not read as newly sunk by the height of somebody else's
      // floor. The walk is now CUT at every landing that comes ashore across it,
      // so the exclusion is gone and the wharf decks are back in this probe: if
      // a board ever returns under a dock the band reads it as sunk half a
      // metre, and `underWharf` below names the dock it is under.
      const deckAt = (e, n) => {
        let y = null;
        for (const d of a.decks ?? []) {
          if (/__footway_\d+$/.test(d.id)) continue;
          if (y !== null && d.y <= y) continue;
          let hit = false;
          const pts = d.pts;
          for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
            const [xi, yi] = pts[i];
            const [xj, yj] = pts[j];
            if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
          }
          if (hit) y = d.y;
        }
        return y;
      };
      const postGround = post
        ? terrain.surfaceHeight(post.at_local_enu_m[0], post.at_local_enu_m[1]) : null;
      // A RIGID BOARD ON TILTED GROUND departs from grade by the relief across
      // its own width — the river walk (T-0119) crosses the Dearborn approach's
      // graded ramp and the pinched bank verge, where the land falls a quarter
      // metre inside a board's reach. So a vertex that leaves the flat band is
      // allowed exactly the relief the ground shows within a board's half-width
      // of it, and not a millimetre of licence more; on the flat ground the
      // original walks stand on, the original band still binds.
      let bandBreaches = 0;
      let worstBreach = 0;
      // A FENCE IS NOT A DECK (T-0069). The street-lining fences share their
      // walk's chunk — one street edge, one mesh — so the band below has to be
      // told which timber is a floor and which is a fence standing beside one.
      // The test is geometric and needs no new attribute: a fence's own line is
      // on the record, its stock reaches 0.085 m across it at the widest (the
      // post), and the nearest walk vertex is the deck's inner edge 0.25 m off.
      // Everything within 0.2 m of a fence line is fence and is not measured as
      // a deck; nothing else in the layer is within a metre of one.
      const fenceLines = [];
      for (const r of f?.records ?? []) {
        for (const fence of r.fences ?? []) {
          const line = fence.path_local_enu_m ?? [];
          for (let i = 0; i + 1 < line.length; i++) fenceLines.push([line[i], line[i + 1]]);
        }
      }
      const onFence = (e, n) => {
        for (const [a0, b0] of fenceLines) {
          const de = b0[0] - a0[0];
          const dn = b0[1] - a0[1];
          const l2 = de * de + dn * dn || 1;
          let t = ((e - a0[0]) * de + (n - a0[1]) * dn) / l2;
          t = Math.max(0, Math.min(1, t));
          if (Math.hypot(a0[0] + de * t - e, a0[1] + dn * t - n) <= 0.2) return true;
        }
        return false;
      };
      const reliefAt = (e, n) => {
        const g0 = terrain.surfaceHeight(e, n);
        let lo = g0;
        let hi = g0;
        for (const [de, dn] of [[0.95, 0], [-0.95, 0], [0, 0.95], [0, -0.95]]) {
          const gg = terrain.surfaceHeight(e + de, n + dn);
          if (Number.isFinite(gg)) { lo = Math.min(lo, gg); hi = Math.max(hi, gg); }
        }
        return Number.isFinite(hi - lo) ? hi - lo : 0;
      };
      // NO BOARD UNDER A LANDING (T-0228). The wharves publish their deck and
      // every stair tread to the walker as `<id>__wharf` / `<id>__wharf_step<n>`;
      // those outlines are the timber a plank walk must not run beneath. This
      // counts the frontage vertices standing inside one, by dock, and the check
      // below asks for none. It is the loaded-page half of the generator's own
      // audit: that one cuts the record, this one reads what was drawn from it.
      const wharfDecks = (a.decks ?? []).filter((d) => /__wharf(_step\d+)?$/.test(d.id));
      const underWharf = new Map();
      const inPoly = (e, n, pts) => {
        let hit = false;
        for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
          const [xi, yi] = pts[i];
          const [xj, yj] = pts[j];
          if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
        }
        return hit;
      };
      for (const t of timber) {
        const pos = t.geometry?.getAttribute('position');
        if (!pos) continue;
        verts += pos.count;
        for (let i = 0; i < pos.count; i++) {
          for (const d of wharfDecks) {
            if (inPoly(pos.getX(i), -pos.getZ(i), d.pts)) {
              underWharf.set(d.id, (underWharf.get(d.id) ?? 0) + 1);
              break;
            }
          }
        }
        for (let i = 0; i < pos.count; i++) {
          // world is (E, up, -N)
          const e = pos.getX(i);
          const y = pos.getY(i);
          const n = -pos.getZ(i);
          const ground = terrain.surfaceHeight(e, n);
          const deck = deckAt(e, n);
          const base = deck === null ? ground
            : (Number.isFinite(ground) ? Math.max(ground, deck) : deck);
          if (Number.isFinite(base) && !onFence(e, n)) {
            const d = y - base;
            highest = Math.max(highest, d);
            // The deck: everything under a metre. The post and its board are
            // measured against the post's own ground below, because a pole is
            // not laid on the land the way a walk is.
            if (d < 1.0) {
              if (d >= -0.06 && d <= 0.18) {
                sink = Math.min(sink, d);
                deckTop = Math.max(deckTop, d);
              } else {
                const relief = reliefAt(e, n);
                if (relief <= 0.12) {
                  // Flat ground, out of band: the original fault, unexcused.
                  sink = Math.min(sink, d);
                  deckTop = Math.max(deckTop, d);
                } else if (d < -(0.06 + relief) || d > 0.18 + relief) {
                  bandBreaches += 1;
                  worstBreach = Math.max(worstBreach,
                    d > 0 ? d - (0.18 + relief) : -(0.06 + relief) - d);
                }
              }
            }
          }
          if (Number.isFinite(postGround) && y - postGround > 2.0) {
            boardLow = Math.min(boardLow, y - postGround);
          }
        }
      }
      // Each hitching post against its OWN stand: the tallest and the lowest
      // vertex within 0.4 m of it, which is its own timber and nothing else —
      // the front walk's near edge is 0.9 m off and the crossing is metres away.
      // Measured over the record on 2026-08-29: the nearest fence line to any of
      // the fourteen is 2.98 m, and thirteen boxes hold exactly the 72 vertices
      // of one post's own shaft and cap and nothing else. The fourteenth is the
      // Mansion House's, where the board crossing over Lake Street brings its
      // near edge 0.13 m from the post and lays 15 more vertices in the box.
      // They move neither reading — a crossing deck stands 0.06 m over its
      // ground, so it is under the foot the min is looking for and a metre and a
      // quarter under the head the max is — and the box is left at 0.4 m rather
      // than tightened onto the 0.22 m cap, which would leave 0.02 m of margin
      // against that same crossing and fail on a plank laid a hand further in.
      //
      // IT WALKS EVERY MESH IN THE LAYER, and T-0244 is why. This read the
      // shared `frontage` mesh alone — `const g = mesh?.geometry`, with a
      // comment saying the posts live in it — which was true of the two the
      // Sauganash's own record stands and stopped being true the day T-0194
      // added twelve at the street edge. A post that names a street is STANDING
      // timber and lands in that street's `<record>__<street>__standing` chunk,
      // published as a `frontage-chunk` mesh beside the fences it culls and
      // casts with; the shared mesh never sees it. So all twelve reported a max
      // over an empty vertex set — `-Infinity` for a height and `Infinity` for a
      // foot — and the geometry was right the whole time. The lesson is the
      // resolution rule, not the count: a post is found by WHERE IT STANDS,
      // across every mesh the layer draws, because which mesh it is folded into
      // is a draw-call decision that may change again without the post moving.
      const hitching = (f?.posts ?? []).filter((q) => q.kind === 'hitching_post').map((q) => {
        const [e0, n0] = q.at_local_enu_m;
        const stand = terrain.surfaceHeight(e0, n0);
        let top = -Infinity;
        let low = Infinity;
        let found = 0;
        if (Number.isFinite(stand)) {
          for (const t of timber) {
            const pos = t.geometry?.getAttribute('position');
            if (!pos) continue;
            for (let i = 0; i < pos.count; i++) {
              if (Math.abs(pos.getX(i) - e0) > 0.4) continue;
              if (Math.abs(-pos.getZ(i) - n0) > 0.4) continue;
              found += 1;
              top = Math.max(top, pos.getY(i) - stand);
              low = Math.min(low, pos.getY(i) - stand);
            }
          }
        }
        return { id: q.id, top, low, found, street: q.street ?? null,
                 recorded: q.post_height_m ?? null,
                 clear: q.clear_of_track_m ?? null, text: q.text ?? null };
      });
      // THE EDGE RULE (T-0460), proved on the drawn geometry rather than on a
      // number the layer reports about itself.
      //
      // A plank walk used to end, at each side, in a row of board ENDS: at a
      // 0.32 m pitch with a 0.02 m gap between them over a deck standing 0.11 m
      // proud of the road, the outer edge was ten thousand short end-grain
      // faces with daylight between them. That is the sawtooth the owner
      // reported, and the rule that replaces it is: **a walk's side is a
      // continuous string piece — timber at the walk's own edge line, from the
      // deck it holds down to the ground it stands on, at EVERY station along
      // the run.**
      //
      // So this marches one named 98 m walk in 0.2 m stations, takes every
      // vertex in the layer standing within 0.03 m of that walk's edge line on
      // either side, and asks each station for two things: a vertex up at the
      // deck, and a vertex down at the ground. A comb of board ends answers the
      // first and not the second — the old bay stringer that did reach the
      // ground stood 0.09 m inboard, outside this band, which is exactly why
      // the edge read as ragged — so this check FAILS on the geometry it was
      // written against and passes on the string piece that replaced it.
      const edge = (() => {
        const walk = (f?.walks ?? []).find((w) => w.id === 'blk_lake_clark_north_walk_1');
        const line = walk?.centreline_local_enu_m;
        if (!Array.isArray(line) || line.length !== 2) return null;
        const half = (walk.width_m ?? 1.83) / 2;
        const rise = walk.rise_m ?? 0.11;
        const [a0, b0] = line;
        const de = b0[0] - a0[0];
        const dn = b0[1] - a0[1];
        const len = Math.hypot(de, dn);
        const ue = de / len;
        const un = dn / len;
        const STEP = 0.2;
        // The run's own ends are skipped: a walk is cut where its face stops and
        // the last half-metre is the joint, not the edge this rule is about.
        const from = 0.5;
        const to = len - 0.5;
        const cells = Math.max(1, Math.floor((to - from) / STEP));
        const hi = new Array(cells).fill(-Infinity);
        const lo = new Array(cells).fill(Infinity);
        // BY THE FACE, NOT BY THE VERTEX. A string piece is a box 2.08 m long,
        // so it carries vertices only at its two ends: asked for vertices, 441
        // of these 487 stations read empty on geometry that is in fact
        // continuous timber. What a station has to be covered by is a FACE, so
        // this walks the layer's triangles — the buffers are non-indexed, three
        // vertices to a triangle — takes those lying wholly in the edge band,
        // and fills every station the triangle spans with the height range it
        // covers there.
        for (const t of timber) {
          const pos = t.geometry?.getAttribute('position');
          if (!pos) continue;
          for (let i = 0; i + 2 < pos.count; i += 3) {
            let lo3 = Infinity;
            let hi3 = -Infinity;
            let a3 = Infinity;
            let b3 = -Infinity;
            let inBand = true;
            for (let k = 0; k < 3; k++) {
              const e = pos.getX(i + k) - a0[0];
              const n = -pos.getZ(i + k) - a0[1];
              if (Math.abs(Math.abs(-e * un + n * ue) - half) > 0.03) { inBand = false; break; }
              const along = e * ue + n * un;
              if (along < a3) a3 = along;
              if (along > b3) b3 = along;
              const y = pos.getY(i + k);
              if (y < lo3) lo3 = y;
              if (y > hi3) hi3 = y;
            }
            if (!inBand) continue;
            const c0 = Math.max(0, Math.ceil((a3 - from) / STEP));
            const c1 = Math.min(cells - 1, Math.floor((b3 - from) / STEP));
            for (let c = c0; c <= c1; c++) {
              if (hi3 > hi[c]) hi[c] = hi3;
              if (lo3 < lo[c]) lo[c] = lo3;
            }
          }
        }
        let open = 0;
        let empty = 0;
        let worst = 0;
        for (let c = 0; c < cells; c++) {
          if (hi[c] === -Infinity) { empty += 1; open += 1; continue; }
          const t = from + (c + 0.5) * STEP;
          const g = terrain.surfaceHeight(a0[0] + ue * t, a0[1] + un * t);
          if (!Number.isFinite(g)) continue;
          // Up at the deck AND down at the ground: a station that answers only
          // one of the two is an open edge, and how far the timber falls short
          // of the ground is what the sawtooth measured.
          const deep = lo[c] - (g + 0.02);
          const tall = (g + rise - 0.06) - hi[c];
          if (deep > 0 || tall > 0) {
            open += 1;
            worst = Math.max(worst, deep, tall);
          }
        }
        return { id: walk.id, len: Math.round(len * 10) / 10, cells, open, empty,
                 worst: Math.round(worst * 1000) / 1000 };
      })();
      // THE DECAL ORDER (T-0625), and it is asserted structurally because the
      // fault it catches is invisible to every count this layer reports about
      // itself. The street ribbon is a decal — depthWrite off, polygonOffset
      // -8/-32 so the terrain cannot punch through its drape — and that offset
      // scales with the polygon's depth slope, which at the grazing angle a road
      // is seen at is large enough to beat the 0.06 m a board crossing stands
      // above it. The ribbon then paints over the crossing in hard triangular
      // patches. frontage.js answers that by drawing the timber AFTER the
      // ribbon, which requires two things that are easy to separate by accident:
      // the two must be in the SAME render list (three draws every opaque before
      // any transparent, and renderOrder cannot reach across the two lists), and
      // the timber's renderOrder must be the higher. The layer shipped with only
      // the second for two months and the comment claiming both.
      const decal = (() => {
        let root = f?.group;
        while (root?.parent) root = root.parent;
        if (!root) return null;
        const street = [];
        const timber = [];
        root.traverse((o) => {
          const m = o.material;
          if (!m) return;
          for (const mm of (Array.isArray(m) ? m : [m])) {
            const nm = mm?.name || '';
            if (/^street-/.test(nm)) street.push({ transparent: !!mm.transparent, order: o.renderOrder });
            else if (nm === 'frontage-timber') timber.push({ transparent: !!mm.transparent, order: o.renderOrder });
          }
        });
        if (!street.length || !timber.length) return null;
        return {
          street: street.length,
          timber: timber.length,
          sameList: street.every((s) => timber.every((t) => t.transparent === s.transparent)),
          timberAfter: street.every((s) => timber.every((t) => t.order > s.order)),
          streetOrder: street[0].order,
          timberOrder: timber[0].order,
        };
      })();
      return {
        edge,
        decal,
        hitching,
        recordIds: (f?.records ?? []).map((r) => r.id),
        noBoardHere: (f?.records ?? []).find((r) => r.id === 'sauganash_frontage')
          ?.board_on_a_post?.value ?? null,
        census: f?.census ?? null,
        meshes: f?.group?.children?.length ?? 0,
        names: (f?.group?.children ?? []).map((c) => c.name),
        // AUTHORED AGAINST DRAWN (T-0349). A layer's group holds the meshes the
        // layer built AND whatever the frame's draw-call economy has since put
        // there: `far-merge.js` welds a distant cluster into one extra mesh,
        // parents it onto the same group and marks it `userData.farMerged`. So
        // `children.length` is not a census of the layer — it is the census plus
        // the camera's history, and it moves with where a stage last stood.
        // These two split that apart: `authored` is what the layer laid, which
        // is the number a census clause can hold across stages, and `merged` is
        // the artefact count, reported beside it rather than folded into it.
        authored: (f?.group?.children ?? []).filter((c) => !c.userData?.farMerged).length,
        authoredNames: (f?.group?.children ?? [])
          .filter((c) => !c.userData?.farMerged).map((c) => c.name),
        merged: (f?.group?.children ?? []).filter((c) => !!c.userData?.farMerged).length,
        mergedNames: (f?.group?.children ?? [])
          .filter((c) => !!c.userData?.farMerged).map((c) => c.name),
        verts,
        letterVerts: letters?.geometry?.getAttribute('position')?.count ?? 0,
        letterMap: !!letters?.material?.map,
        timberMap: !!mesh?.material?.map,
        lettering: f?.lettering ?? null,
        recordText: post?.text ?? null,
        textGrade: post?.text_confidence ?? null,
        postHeight: post?.post_height_m ?? null,
        clearOfTrack: post?.clear_of_track_m ?? null,
        walks: f?.walks ?? [],
        underWharf: [...underWharf.entries()].sort(),
        wharfDeckCount: wharfDecks.length,
        sink, deckTop, highest, boardLow, ungraded, notReconstructed,
        bandBreaches, worstBreach,
        problems: (a?.problems ?? []).filter((x) => /frontage/.test(x)),
      };
    });
    check(`${label}: the frontage layer lays all five records' walks and stands their posts`,
      // T-0241 laid Washington's seven block faces on top of Randolph's
      // thirteen: 42 walks to 49, 28 crossings to 33, 26 fence runs to 35 and
      // 74 refusals to 83. The post count does NOT move — Washington's
      // frontages carry no named trade the hitching rule accepts.
      // T-0196 then took three documented buildings off Lake Street's walk, which
      // opened one more run and FOUR more corner crossings (two on Lake's north
      // side, two on the South Water faces those walks now reach the corner of)
      // and retired two refusals: 49 walks to 50, 33 crossings to 37, 83
      // refusals to 81. Fences and posts do not move — a wall 1.50 m back from
      // the frontage line is still inside the 3.0 m a street fence needs.
      // T-0024 put the store on Randolph onto the street line, which refused one
      // more street-edge wall and left this figure a count behind: 81 to 82,
      // measured on an unmodified dev while T-0228 was taking its own reading.
      // T-0228 then cut the river walk's wharf reach in two where Carpenter's
      // and Jones's landings come ashore across it — 50 walks to 51 — and states
      // each gap where it refuses to lay boards: 82 refusals to 84.
      // T-0246 reconciled log_jail onto the committed plat, off the modern kerb
      // it was placed from. The WALK count does not move — the two steps it
      // returns extend an existing run to the full face rather than opening a
      // new one — but a walk that stopped short of its corner had refused the
      // corner CROSSING with it, and two of those are now laid: 37 crossings to
      // 39, and the refusal that named them retires, 84 to 83.
      // T-0028 opened blk_lake_franklin and the warehouse it was dealt stands
      // 1.50 m off that lot's frontage line — inside the 3.0 m a street fence
      // needs, so the building IS the street wall there and the fence is
      // refused: 83 to 84, and nothing else in this line moves. Left a count
      // behind for two days, the same way T-0024's did, and for the same reason
      // as T-0244 below: this suite is not the dev gate.
      // T-0380 stood the New York House on the Lake Street face of
      // blk_south_water_franklin — a documented public house, which is a trade
      // the hitching rule accepts — so ONE more post stands at that frontage:
      // 15 to 16. Nothing else moves. The walk along that face was already laid
      // for its whole length, so no run opens and no crossing is added, and the
      // house stands 1.50 m back from the frontage line, which is inside the
      // 3.0 m a street fence needs and was already refused there.
      // T-0263 settled the TRADE at frederick_thomas_shop — `drug_store`,
      // attested, out of Frederick Thomas's own advertisement heading in the
      // Chicago American — where it had read `shop` at the reconstructed grade.
      // The hitching rule takes its frontages from the trade, so the frontage
      // this record REFUSED IN WRITING now qualifies: 16 posts to 17, and the
      // refusal that named it retires with it, 84 to 83. Those two numbers move
      // together and only together, which is the check that this is the trade
      // and not a new placement — the refusal text is quoted on the retiring
      // entry ("the trade at frederick_thomas_shop is reconstructed ... a
      // hitching post there would be furniture standing on an invention").
      // Nothing else moves: no run opens, no crossing is added, and the shop's
      // own wall was never a street-fence refusal.
      // T-0384 stood john_holbrook_store on the South Water face of
      // blk_south_water_dearborn — a documented STORE, which is a trade the
      // hitching rule accepts — so ONE more post stands at that frontage: 17 to
      // 18. This is a building ARRIVING rather than a trade settling, so unlike
      // T-0263 no refusal retires with it and 83 does not move. Nothing else
      // moves either: the face's walk was already laid for its whole length so
      // no run opens and no crossing is added, and the shop stands 1.50 m back
      // from the frontage line, inside the 3.0 m a street fence needs, which was
      // already refused on that wall.
      // T-0461 asked whether a lot is improved by the building STANDING on it or
      // by where one corner of it landed, and it was the corner: `at` is the
      // placement origin, which is a footprint VERTEX on 366 of the 367 placed
      // records and the centroid on none. `_stands_on` now asks whether the
      // committed footprint and the lot share ground. It can only ADD occupancy
      // — 28 more across the town's 144 platted lots, none removed, 125 improved
      // lots to 131 — so every figure here moves in one direction each.
      // POSTS 18 to 20, and both are buildings whose own door is on the face
      // they now stand on: tremont_house_1, a documented hotel on the Lake face
      // of blk_south_water_clark, and exchange_coffee_house on the Lake face of
      // blk_south_water_franklin. Each had 90% and more of its frontage on the
      // lot and its origin corner just off it.
      // FENCES 35 to 32, and every one of the three is the SAME clause T-0028
      // and T-0380 are already recorded against — a wall inside the 3.0 m a
      // street fence needs, so the building IS the street wall there. They are
      // blk_south_water_clark lot 7 (tremont_house_1, 2.40 m),
      // blk_lake_dearborn lot 2 (mason_blacksmith_shop, 0.55 m) and
      // blk_south_water_lasalle lot 3 (recon_1835_blk_south_water_lasalle_a1_06,
      // 1.61 m). The first is what T-0461 was filed for: that fence stood
      // between the footway and the Tremont House's own goods.
      // REFUSED 83 to 85 — the two new setback refusals above that were not
      // already refused as prairie, plus one post refused for want of a walk at
      // harmon_loomis_store, less one lot (blk_randolph_clinton lot 4) that
      // stops reading as prairie and takes its fence. Six further refusals do
      // not move in COUNT but change their WORDING, from "no committed building
      // stands on this platted lot" to the building that does and how far back
      // it stands. WALKS and CROSSINGS do not move: this rule reads lots, and a
      // walk is laid off the block face.
      // T-1053 took a privy off blk_south_water_franklin lot 4 — it had been
      // standing in the yard of a lot its own household's cottage is not on, a
      // lot to the west of the row it serves — and re-lotted it behind that
      // cottage on lot 6. Lot 6 was already improved and already had its street
      // wall, so nothing arrives; lot 4 stops being improved at all, and an
      // unimproved lot is open prairie that takes no street fence. FENCES 32 to
      // 31 and REFUSED 85 to 86, and the two move together and only together,
      // which is the check that this is one lot changing class and not the rule
      // changing its mind: the retiring fence and the arriving refusal name the
      // same wall (`blk_south_water_franklin north face, lot 4`, "no committed
      // building stands on this platted lot"). WALKS, CROSSINGS AND POSTS DO NOT
      // MOVE — the face's walk was laid for its whole length either way, the
      // privy carries no trade the hitching rule accepts, and the two other
      // privies this ticket re-lotted moved between lots that are improved on
      // both sides of the move.
      frontage.census?.records === 5 && frontage.census?.walks === 51
        && frontage.census?.crossings === 39
        // T-0626 takes it back to NINETEEN, and it is the first time this count
        // has gone DOWN. Nothing was refused for being badly placed: the log
        // cabin beside the Sauganash stopped being a drug store. Its record was
        // titled Philo Carpenter's Log Drug Store and carried `drug_store` as
        // its function, three years after Carpenter moved out of it, and the
        // hitching rule stands a post at a frontage whose TRADE it accepts. With
        // the trade gone — the record now states three former uses and no
        // current one — the frontage has no trade to take custom from a stranger
        // off the street, so the post retires with the signboard that lettered
        // the same man's name over the same door. Walks, crossings, fences and
        // refusals do not move: the building is still there and still the street
        // wall on that face.
        && frontage.census?.posts === 19 && frontage.census?.fences === 31
        && frontage.census?.refused === 86
        && frontage.recordIds.join(',')
          === 'green_tree_frontage,sauganash_frontage,river_walk_frontage,'
            + 'lasalle_crossing_frontage,town_street_edge'
        && frontage.verts > 0 && frontage.problems.length === 0,
      `${frontage.census?.records} record(s) [${frontage.recordIds.join(', ')}], `
      + `${frontage.census?.walks} walk(s), ${frontage.census?.crossings} crossing(s), `
      + `${frontage.census?.posts} post(s), ${frontage.census?.fences} fence run(s), `
      + `${frontage.verts} vertices, `
      + `${frontage.census?.refused} wall(s) refused, `
      + `problems [${frontage.problems.join(' | ') || 'none'}]`);
    // NO BOARD UNDER A LANDING (T-0228). Found by T-0058, which made the wharf
    // decks walk surfaces and so made it matter: Carpenter's and Jones's decks
    // tie their heels 2.0 m back into the bank the riverside plank walk runs
    // along, and about 2,700 of this layer's vertices lay inside those two
    // outlines with a further 270 inside their boarding stairs — the slab half a
    // metre over the boards, 0.36 m of daylight under it, and a 0.50 m riser
    // across the walker's path that the 0.35 m step-up rule refuses. The walk is
    // now cut at every landing and the answer is stated where a visitor can read
    // it: the gaps are in the record's `refused`, and the landing's own deck is
    // the walking surface across it.
    check(`${label}: no frontage board stands under a wharf deck or its stair`,
      frontage.wharfDeckCount > 0 && frontage.underWharf.length === 0,
      `${frontage.wharfDeckCount} wharf surface(s) published; under them `
      + `[${frontage.underWharf.map(([id, k]) => `${id} ${k}`).join(', ') || 'no boards'}]`);
    // NOT MERELY GRADED — graded reconstructed, every vertex. No source record in
    // this repository states that a walk stood on this ground on 1 July 1835
    // (L135), and a single vertex claiming inferred or attested would be this
    // layer overstating the one thing it must not.
    check(`${label}: every frontage vertex is graded reconstructed`,
      frontage.ungraded === 0 && frontage.notReconstructed === 0 && frontage.verts > 0,
      `${frontage.ungraded} out of range, ${frontage.notReconstructed} claiming better `
      + 'than reconstructed');
    // THE DECK TIES INTO THE GROUND IT CROSSES. Every board samples the surface
    // a visitor walks under its own centre — the terrain, or a registered deck
    // over water — so no part of a walk may hang over the land or be swallowed
    // by it. On flat ground the whole layer under a metre lives in a band about
    // 0.13 m deep, and that band still binds; on tilted ground (the river
    // walk's ramp crossing and bank pinch, T-0119) a rigid board may depart by
    // at most the relief across its own width, measured per vertex, and each
    // stringer reaches the ground under its own line so the departure is
    // carried on timber rather than open to daylight.
    check(`${label}: the plank decks tie into the ground they cross`,
      frontage.sink >= -0.06 && frontage.deckTop > 0.05 && frontage.deckTop <= 0.18
        && frontage.bandBreaches === 0,
      `deepest ${frontage.sink?.toFixed(3)} m below grade, highest flat-ground deck `
      + `vertex ${frontage.deckTop?.toFixed(3)} m above it, ${frontage.bandBreaches} `
      + `vertice(s) past even their own relief allowance (worst by `
      + `${frontage.worstBreach?.toFixed(3)} m)`);
    // THE WALK'S SIDE IS A MADE EDGE, NOT A ROW OF BOARD ENDS (T-0460). The
    // owner reported the plank walk meeting the dirt road in a jagged sawtooth
    // — "it's like the first thing we see" — and the treatment chosen was the
    // first of the two he would accept: the walk sits consistently OVER the
    // road, held between two string pieces whose tops are flush with the boards
    // and whose feet reach the ground. The probe above walks one named 98 m run
    // in 0.2 m stations and asks every one of them for timber from the deck to
    // the ground at the walk's own edge line; it is written to fail on the comb
    // of board ends this replaced.
    // T-0625. The owner reported the crossing at Lake and South Water still
    // broken after T-0460 shipped: the road was painting over the plank deck in
    // triangular patches, which reads as the same sawtooth from the street but
    // is a render-order fault, not a geometry one. T-0460's probe above cannot
    // see it — the timber IS there, at the right height, with a continuous edge;
    // it is simply not the thing on the screen. So this asserts the ordering
    // contract itself: same render list, timber after the ribbon.
    check(`${label}: the street decal cannot paint over the timber laid on it`,
      frontage.decal !== null && frontage.decal.sameList && frontage.decal.timberAfter,
      frontage.decal === null
        ? 'no street ribbon or no frontage timber in the scene to compare'
        : `${frontage.decal.street} street material(s) and ${frontage.decal.timber} timber `
          + `mesh(es): sameList=${frontage.decal.sameList} (three draws every opaque before `
          + `any transparent, so renderOrder cannot order across the two lists), `
          + `timberAfter=${frontage.decal.timberAfter} `
          + `(street renderOrder ${frontage.decal.streetOrder}, timber ${frontage.decal.timberOrder})`);

    check(`${label}: a plank walk's side is one made edge for its whole length`,
      frontage.edge !== null && frontage.edge.open === 0 && frontage.edge.cells > 400
        && frontage.census?.kerb > 3000,
      `${frontage.edge?.id ?? 'no walk probed'}: ${frontage.edge?.open} of `
      + `${frontage.edge?.cells} station(s) over ${frontage.edge?.len} m show an open `
      + `edge (${frontage.edge?.empty} with no timber at all, worst by `
      + `${frontage.edge?.worst} m); the layer laid ${frontage.census?.kerb} length(s) `
      + `of string piece, the largest step between two consecutive ones `
      + `${frontage.census?.kerbStep_m} m`);
    // THE POST STANDS ON THE GROUND AND ITS BOARD HANGS OVER A HEAD. A pole whose
    // height came from a number beside the mesh rather than from a terrain sample
    // floats; a board hung too low is one a visitor walks through.
    check(`${label}: the named board hangs on a post that stands on the ground`,
      Math.abs(frontage.highest - frontage.postHeight) <= 0.05
        && frontage.boardLow >= 2.4 && frontage.clearOfTrack > 0,
      `post ${frontage.highest?.toFixed(2)} m over its grade against a recorded `
      + `${frontage.postHeight} m, board's underside ${frontage.boardLow?.toFixed(2)} m up, `
      + `${frontage.clearOfTrack} m clear of the travelled track`);
    // THE LAYER DRAWS THE MESHES IT LAID, AND ONLY THOSE ARE ITS OWN (T-0349).
    // This census used to be the seventh clause of the lettering check below,
    // and it was the only clause in that conjunction whose verdict depended on
    // what had run BEFORE it: stage 1-2 read 67 on desktop and failed, stage 2
    // alone read 62 and passed, on the same tree and the same published mirror
    // minutes apart, and the six lettering clauses were green in both. The five
    // extra were all `frontage-far-merge` — `far-merge.js` welds a distant
    // cluster of this layer's chunks into one more mesh, parents it onto this
    // same group and marks it `userData.farMerged`, and stage 1 walks the
    // desktop camera somewhere that causes five such merges where stage 2 alone
    // and the mobile viewport cause none. So `children.length` was never a
    // census of the layer; it was the layer plus the camera's history, reported
    // under a name that promised the painted name was wrong.
    //
    // The count is not dropped, it is re-stated over the set that can carry it:
    // the meshes the layer AUTHORED, which is every child that is not a merge
    // artefact. Sixty-two — the shared timber, the river walk's fifteen culling
    // chunks (T-0119), the town street edge's thirty-four (T-0069 laid
    // twenty-one; T-0198's six reconciled South Water placements welded two runs
    // into one and T-0199's last five welded two more, taking it to eighteen;
    // T-0240 laid Randolph Street's thirteen block faces and took it to
    // thirty-three; T-0196 reconciled three Lake Street placements, and clearing
    // old_bank_building off blk_lake_lasalle's north face opened a fourteenth
    // Lake run west of the ground break that still cuts it), the THREE
    // street-fence meshes — one per covered street that carries a fence, which
    // T-0198 split off so the boards could leave the shadow map while the fences
    // stayed in it, and which is why this number moves with `EDGE_STREETS` — and
    // the lettering mesh. 53 -> 61 with T-0241's Washington faces, because the
    // walk is chunked one mesh per run and Washington laid eight more of them;
    // T-0196's Lake Street repair opens a forty-first run, so 62.
    //
    // The merge artefacts are REPORTED and not asserted, and that asymmetry is
    // the finding: how many of them exist is a fact about where the camera has
    // been, so a number here would be asserting the walk this suite happens to
    // take. What is asserted about them is that they are the layer's own kind of
    // artefact — every extra child is a `frontage-far-merge` — so a stray mesh
    // parented onto this group by anything else still fails.
    check(`${label}: the frontage layer draws the meshes it authored`,
      frontage.authored === 62
        && frontage.mergedNames.every((nm) => nm === 'frontage-far-merge'),
      `${frontage.authored} authored mesh(es) (${tallyNames(frontage.authoredNames)}), `
      + `${frontage.merged} far-merge artefact(s) `
      + `[${tallyNames(frontage.mergedNames) || 'none'}], `
      + `${frontage.meshes} drawn in all`,
      // PRINTED ON A PASS TOO (the `show` flag, T-0187), because the drawn count
      // is the number this ticket found varying with run order and a reading
      // nobody can see is a reading nobody can check. A green line here states
      // both figures, so the next run that wonders whether the merge artefacts
      // are still arriving can read it off the log instead of re-measuring.
      true);
    // THE NAME IS DRAWN, AND IT IS THE RECORD'S. This is the only lettering in the
    // renderer (L135), and it is the record's wording rather than the renderer's:
    // a board whose painted name drifted from the record would be this project
    // inventing a sign, which is exactly what L25 and L130 refuse. The painted
    // name is on its own mesh, the only thing in this layer that may carry a
    // texture; the timber it hangs over is all on ONE material and carries none.
    check(`${label}: the board carries the record's own name, painted`,
      frontage.census?.lettered === 1 && frontage.letterVerts >= 6
        && frontage.letterMap === true && frontage.timberMap === false
        && frontage.lettering === frontage.recordText
        && frontage.recordText === 'GREEN TREE'
        && frontage.textGrade === 'inferred',
      `"${frontage.lettering}" on ${frontage.letterVerts} vertices, record says `
      + `"${frontage.recordText}" graded ${frontage.textGrade}`);

    // AND IT READS FROM THE STREET, which is what a walk and a signboard are FOR.
    // Stand out on Canal Street where a traveller coming up to the inn stands and
    // hold the clock, so the grass cannot supply the difference. Same bar as the
    // goods, the fence gates and the signboard: worst >= 6 and mean >= 0.3.
    await page.evaluate(() => window.__chicago4d.walker.teleport(
      { local_e: -163, local_n: -99, yaw_deg: 80, pitch_deg: 0 }));
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const frontWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.frontage.group.visible = false; });
    const frontWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.frontage.group.visible = true; });
    const dFront = signatureDistance(frontWith, frontWithout);
    check(`${label}: the walk and its board reach the screen from the street`,
      dFront.worst >= 6 && dFront.mean >= 0.3,
      `cell delta mean ${dFront.mean?.toFixed(2)}, worst ${dFront.worst} (need worst>=6)`);

    // A board on a post at a corner is the nearest thing to the crosshair when a
    // visitor walks up to that corner, so aiming at it has to open the inn. This
    // asks the LAYER rather than the app's pick, because the app would answer the
    // same building from the wall behind it and the assertion would pass while
    // the layer picked nothing at all.
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    await page.evaluate(() => window.__chicago4d.walker.teleport(
      { local_e: -155.0, local_n: -101.0, yaw_deg: 68, pitch_deg: 12 }));
    await page.waitForTimeout(600);
    const frontagePick = await page.evaluate(() => {
      const a = window.__chicago4d;
      const hits = [];
      for (const x of [-0.3, -0.15, 0, 0.15, 0.3]) {
        for (const y of [-0.3, -0.15, 0, 0.15, 0.3]) {
          // A plain {x, y} is all `Raycaster.setFromCamera` reads, and it saves
          // this file reaching for the app's three namespace to build a Vector2.
          const hit = a.frontage.pickAt({ x, y }, a.camera);
          if (hit?.id) hits.push(hit.id);
        }
      }
      return hits;
    });
    check(`${label}: aiming at the frontage opens the inn it belongs to`,
      frontagePick.includes('green_tree_tavern'),
      `25 aims returned [${[...new Set(frontagePick)].join(', ') || 'nothing'}]`);

    // --- and the same layer at the Sauganash (T-0090) and the street edge --
    //
    // THE POSTS ARE POSTS AND NOTHING ELSE. A hitching post that fell through to
    // the sign post's branch would stand 3.6 m tall with a cross-arm and a blank
    // board on it, and every dataset gate in this repo would still be green: the
    // record says 1.30 m and it is the renderer that would be wrong. Measured
    // against each post's own terrain sample, because a pole whose height came
    // from a number beside the mesh floats.
    //
    // TWO ON THE SAUGANASH'S OWN RECORD AND THIRTEEN AT THE STREET EDGE. This
    // asserted two, and T-0194 made it fourteen without touching the line, so it
    // was red on `dev` from that merge until T-0244 (the dev gate is `check.sh`
    // and this suite is dispatch-plus-one-path, so nothing stopped it).
    // T-0380 made it fifteen AND UPDATED THE LINE IN THE SAME COMMIT, which is
    // what the paragraph below asks of a run that adds a post: the New York
    // House is a documented public house on Lake Street, so the rule stands a
    // post at its frontage. T-0263 makes it sixteen the same way and by the
    // same bookkeeping, and this one is a TRADE moving rather than a building
    // arriving: frederick_thomas_shop already stood on South Water Street and
    // its frontage was refused a post in writing because its trade was
    // reconstructed, so settling that trade on the Chicago American's own
    // heading is what qualifies it. T-0384 makes it seventeen, and that one IS a building
    // arriving: John Holbrook's clothing store is a documented store on
    // South Water Street, so the rule stands a post at its frontage and no
    // refusal retires with it. The street-edge population is fifteen. The two
    // populations are told apart by `street`, which is exactly the field that
    // decides the mesh: a post naming a street is standing timber in that
    // street's chunk, and a post naming none falls back to the shared mesh. The
    // counts are exact on purpose — a post appearing or vanishing is a change
    // worth failing over — so a run that adds posts updates them here and says
    // so, the same bookkeeping the walk and crossing counts above carry.
    //
    // `found` is the vertex tally inside each post's box, and it is asserted
    // non-zero SEPARATELY from the heights: an empty set makes `top` -Infinity
    // and `low` Infinity, which fail the height tests too but read as a post of
    // the wrong height rather than as a post the gate cannot see. That was
    // twelve of these fifteen for two days.
    const postsBad = frontage.hitching.filter((h) => !(h.found > 0
      && Math.abs(h.top - h.recorded) <= 0.05
      && Math.abs(h.low) <= 0.02 && h.clear > 0 && !h.text));
    // T-0461 makes it NINETEEN, and neither is a building arriving or a trade
    // settling: both already stood, with a documented trade the rule accepts,
    // on a lot the containment test could not see them on. `_stands_on` asks
    // whether the footprint and the lot share ground instead of where the
    // placement origin — a footprint VERTEX, on 366 of 367 records — happened to
    // fall, and tremont_house_1 (a hotel, 13.76 m of its 15.24 m frontage on
    // lot 7 of blk_south_water_clark) and exchange_coffee_house are what it
    // finds. The street-edge population is seventeen; the two on a record's own
    // ground do not move, because those come from the Sauganash's own plates.
    // T-0626 makes it EIGHTEEN, the first fall in this line, and it is a trade
    // leaving rather than a building. `philo_carpenter_log_shop` — Mark
    // Beaubien's own cabin, let to Philo Carpenter in 1832, to John S. Wright,
    // then to Eliza Chappel's school until 1834 — stopped carrying `drug_store`
    // as its function, because on 1 July 1835 it is neither a drug store nor a
    // school and no source reached says what it was. The hitching rule accepts a
    // frontage by its TRADE, so the post retires with it. The street-edge
    // population is sixteen; the two on a record's own ground do not move.
    check(`${label}: the eighteen hitching posts stand on their own ground, carrying nothing`,
      frontage.hitching.length === 18
        && frontage.census?.hitching === 18
        && frontage.hitching.filter((h) => !h.street).length === 2
        && frontage.hitching.filter((h) => h.street).length === 16
        && postsBad.length === 0
        && frontage.census?.lettered === 1
        && frontage.noBoardHere === false,
      `${frontage.hitching.length} post(s) read, census says ${frontage.census?.hitching}`
      + ` — ${frontage.hitching.filter((h) => !h.street).length} on a record's own`
      + ` ground, ${frontage.hitching.filter((h) => h.street).length} at the street edge`
      + `; ${postsBad.length} bad: `
      + (postsBad.map((h) => `${h.id} ${h.top?.toFixed(2)}/${h.recorded} m, `
        + `foot ${h.low?.toFixed(3)} m, ${h.found} vert, ${h.clear} m clear`).join(' | ')
        || 'none')
      + ` — ${frontage.census?.lettered} board(s) lettered in the layer, `
      + `record says a board on a post here: ${frontage.noBoardHere}`);

    // AND IT READS FROM THE STREET, the same bar the Green Tree's frontage is
    // held to: stand on Lake Street where a traveller coming up to the hotel
    // stands, hold the clock so the grass cannot supply the difference, and ask
    // for worst >= 6 and mean >= 0.3.
    await page.evaluate(() => window.__chicago4d.walker.teleport(
      { local_e: 107.0, local_n: -113.0, yaw_deg: 180, pitch_deg: -6 }));
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const saugWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.frontage.group.visible = false; });
    const saugWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.frontage.group.visible = true; });
    const dSaug = signatureDistance(saugWith, saugWithout);
    check(`${label}: the Sauganash's walks and posts reach the screen from Lake Street`,
      dSaug.worst >= 6 && dSaug.mean >= 0.3,
      `cell delta mean ${dSaug.mean?.toFixed(2)}, worst ${dSaug.worst} (need worst>=6)`);

    // A walk is the thing a visitor is standing ON when they reach this corner,
    // so aiming at it has to open the hotel. Asked of the LAYER for the same
    // reason as at the Green Tree: the app would answer the same building off
    // the wall behind it and pass while the layer picked nothing at all.
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    await page.evaluate(() => window.__chicago4d.walker.teleport(
      { local_e: 102.62, local_n: -114.5, yaw_deg: 180, pitch_deg: -30 }));
    await page.waitForTimeout(600);
    const saugPick = await page.evaluate(() => {
      const a = window.__chicago4d;
      const hits = [];
      for (const x of [-0.3, -0.15, 0, 0.15, 0.3]) {
        for (const y of [-0.3, -0.15, 0, 0.15, 0.3]) {
          const hit = a.frontage.pickAt({ x, y }, a.camera);
          if (hit?.id) hits.push(hit.id);
        }
      }
      return hits;
    });
    check(`${label}: aiming at the Sauganash's frontage opens the hotel it belongs to`,
      saugPick.includes('sauganash_hotel'),
      `25 aims returned [${[...new Set(saugPick)].join(', ') || 'nothing'}]`);

    // --- and the river plank walk (T-0119) --------------------------------
    //
    // The first frontage record that is not a building's frontage: the plank
    // footway over the State slough's mouth on the Slough Log Bridge's
    // committed deck, and the riverside walk from it along the south bank to
    // Jones's landing. Its failure modes are its own, and none is visible to a
    // dataset gate: the footway must be a surface the walker STANDS ON over
    // water (a deck registered from the walk record, T-0045's machinery), the
    // planks must actually be under the boot at the mouth, and the whole run
    // must publish its floor to the planting block-list.
    const river = await page.evaluate(() => {
      const a = window.__chicago4d;
      const f = a?.frontage;
      const rec = (f?.records ?? []).find((r) => r.id === 'river_walk_frontage');
      const footway = (f?.walks ?? []).find((w) => w.id === 'river_plank_walk_crossing_footway');
      const deck = (a.decks ?? []).find((d) => d.id === 'river_plank_walk_crossing_footway__footway');
      const keepOut = (f?.keepOut ?? []).filter((k) => k.id === 'river_plank_walk__walk').length;
      // Planks under the boot at the mouth: timber vertices inside the deck
      // span, at the footway's own plank band and no other height.
      let boardVerts = 0;
      for (const t of f?.group?.children ?? []) {
        if (t.name !== 'frontage' && t.name !== 'frontage-chunk') continue;
        const pos = t.geometry?.getAttribute('position');
        if (!pos) continue;
        for (let i = 0; i < pos.count; i++) {
          const e = pos.getX(i);
          const n = -pos.getZ(i);
          if (e < 805.4 || e > 813.2 || n < 13.1 || n > 15.3) continue;
          const y = pos.getY(i);
          if (deck && y > deck.y - 0.06 && y <= deck.y + 1e-6) boardVerts += 1;
        }
      }
      // Stand mid-deck, over the water: the planks, not the wading barrier,
      // hold the walker up — the exact-equality contract the bridge decks keep.
      a.walker.teleport({ local_e: 809.4, local_n: 14.2, yaw_deg: 270 });
      const stood = {
        groundY: a.walker.state.groundY,
        wet: a.terrain.isWater(809.4, 14.2),
        barrier: a.terrain.walkHeight(809.4, 14.2),
      };
      // And the crossing is walkable END TO END: west off the deck onto the
      // graded bank, no step refusal, ground continuous under every stride.
      let worstStride = 0;
      let prevY = a.walker.state.groundY;
      let blocked = 0;
      a.intent.forward = 1;
      for (let i = 0; i < 220; i += 1) {
        a.walker.update(0.05, a.intent);
        worstStride = Math.max(worstStride, Math.abs(a.walker.state.groundY - prevY));
        prevY = a.walker.state.groundY;
        if (a.walker.state.blocked) blocked += 1;
      }
      a.intent.forward = 0;
      return {
        hasRecord: !!rec,
        cardId: rec?.card?.id ?? null,
        footwayDeckM: footway?.deck_m ?? null,
        deckY: deck?.y ?? null,
        walkRise: footway?.rise_m ?? null,
        keepOut,
        boardVerts,
        stood,
        walkedToE: a.walker.state.e,
        worstStride,
        blocked,
      };
    });
    check(`${label}: the river walk publishes its floor and registers its crossing deck`,
      river.hasRecord && river.cardId === 'river_plank_walk'
        && river.keepOut >= 15
        && river.deckY !== null && river.footwayDeckM !== null
        && Math.abs(river.deckY - (river.footwayDeckM + river.walkRise)) < 1e-9,
      `record ${river.hasRecord}, card ${river.cardId}, ${river.keepOut} keep-out `
      + `rect(s), walker deck at ${river.deckY} m against deck_m ${river.footwayDeckM} `
      + `+ rise ${river.walkRise}`);
    check(`${label}: the walker stands on the planks over the water at the mouth`,
      river.stood.wet === true && river.stood.groundY === river.deckY
        && river.stood.barrier > river.deckY + 1,
      `stood at ${river.stood.groundY} m over water=${river.stood.wet}, deck `
      + `${river.deckY} m, barrier ${river.stood.barrier} m`);
    check(`${label}: the crossing reads as planks underfoot, and walks off onto the bank`,
      river.boardVerts >= 100 && river.walkedToE < 802 && river.blocked === 0
        && river.worstStride <= 0.35,
      `${river.boardVerts} plank vertice(s) in the footway band, walked west to `
      + `E ${river.walkedToE?.toFixed(1)}, ${river.blocked} blocked stride(s), worst `
      + `step ${river.worstStride?.toFixed(2)} m`);

    // Aiming at the riverside run answers the walk's OWN card — there is no
    // building on this bank for it to belong to, so the layer carries the
    // record the popup shows, the same arrangement the boats keep (T-0063).
    await page.evaluate(() => window.__chicago4d.walker.teleport(
      { local_e: 600.0, local_n: 17.5, yaw_deg: 180, pitch_deg: -45 }));
    await page.waitForTimeout(600);
    const riverPick = await page.evaluate(() => {
      const a = window.__chicago4d;
      const hits = [];
      for (const x of [-0.3, -0.15, 0, 0.15, 0.3]) {
        for (const y of [-0.3, -0.15, 0, 0.15, 0.3]) {
          const hit = a.frontage.pickAt({ x, y }, a.camera);
          if (hit?.id) hits.push({ id: hit.id, name: hit.record?.sidecar?.name ?? null });
        }
      }
      return hits;
    });
    check(`${label}: aiming at the riverside walk answers its own reconstructed card`,
      riverPick.some((h) => h.id === 'river_plank_walk' && h.name === 'The river plank walk'),
      `25 aims returned [${[...new Set(riverPick.map((h) => `${h.id}:${h.name}`))].join(', ')
        || 'nothing'}]`);


    // --- the town's street edge (T-0069) ----------------------------------
    //
    // The owner, of the first Cook County jail engraving: "note the fences
    // lining the street and what appears to be plank sidewalks. all of the
    // streets should be updated like this... at least south of the river or
    // near the river." The record that answers it is generated from the platted
    // block faces, and everything a dataset gate can ask of it — which face,
    // which stretch, how far off the lot line — is already asked by
    // `tools/generate_frontage_works.py --check`. What CANNOT be asked there is
    // the only thing the owner would notice: that the walk is a surface a
    // visitor is standing ON rather than a stripe they sink through, that it is
    // continuous from one end of a street to the other, that a crossing carries
    // them over the road at a corner, and that no part of it lies in the
    // travelled way. All four are decided at load, out of a terrain sample and
    // the walker's own deck registry, so they are decided here or nowhere.
    const edge = await page.evaluate(() => {
      const a = window.__chicago4d;
      const f = a?.frontage;
      const rec = (f?.records ?? []).find((r) => r.id === 'town_street_edge');
      const walks = (f?.walks ?? []).filter((w) => w.belongs_to === 'town_street_edge');
      const decks = (a.decks ?? []).filter((d) => /^blk_.*__footway_/.test(d.id));

      // ---- WALKED END TO END, on Lake Street and, since T-0188, on the one
      // South Water block face whose walk the reconciliation made whole.
      // The walker is stood on the walk's own centreline every two metres and
      // asked what is under their boots — the deck the record published, or the
      // mud. One sample in the mud is a hole in the sidewalk, so the bar is
      // every one of them.
      const marchChain = (ids) => {
        const chain = ids.map((id) => walks.find((w) => w.id === id) ?? null);
        const out = { samples: 0, onPlanks: 0, worstLift: Infinity, gaps: 0, run: 0,
          missing: chain.filter((w) => !w).length };
        let previous = null;
        for (const w of chain) {
          if (!w) continue;
          const line = w.centreline_local_enu_m;
          for (let s = 0; s + 1 < line.length; s += 1) {
            const [ae, an] = line[s];
            const [be, bn] = line[s + 1];
            const len = Math.hypot(be - ae, bn - an);
            out.run += len;
            if (previous) {
              out.gaps += Math.hypot(ae - previous[0], an - previous[1]) > 1.0 ? 1 : 0;
            }
            const steps = Math.max(2, Math.round(len / 2));
            for (let i = 0; i <= steps; i += 1) {
              const e = ae + (be - ae) * (i / steps);
              const n = an + (bn - an) * (i / steps);
              a.walker.teleport({ local_e: e, local_n: n, yaw_deg: 90 });
              const lift = a.walker.state.groundY - a.terrain.walkHeight(e, n);
              out.samples += 1;
              if (lift > 0.04) out.onPlanks += 1;
              out.worstLift = Math.min(out.worstLift, lift);
            }
            previous = [be, bn];
          }
        }
        return out;
      };
      // LAKE STREET (T-0069): the north frontage through two whole platted
      // blocks and the board crossing over Wells Street between them, about
      // 220 m, all of it derived from the plat and none of it placed.
      const chain = ['blk_south_water_franklin_south_walk_1',
        'blk_south_water_franklin_south_crossing_blk_south_water_wells_south',
        'blk_south_water_wells_south_walk_1'];
      const march = marchChain(chain);
      // SOUTH WATER STREET (T-0188): the whole north face of
      // blk_south_water_franklin, 96.5 m of it, and it is the acceptance clause
      // this ticket had to EARN rather than assert. Before the reconciliation
      // that face carried two stumps of 25.4 m and 45.7 m with the Temple
      // Building and Kinzie's forwarding store standing in the roadway between
      // them; both were re-derived against this project's own committed street
      // line and the face is now one unbroken run — the first whole block face
      // of sidewalk this street has ever had.
      const southWater = marchChain(['blk_south_water_franklin_north_walk_1']);

      // ---- AND WALKED, not teleported, over the crossing at the corner.
      // Start on the planks a few metres short of the crossing, point along it,
      // and push forward: the boot must stay on boards the whole way over the
      // road and come off onto the far block's walk. A crossing that were only
      // drawn — no deck registered — would drop the walker into the ruts here
      // and every other check in this file would stay green.
      const cross = walks.find((w) => w.id === chain[1]) ?? null;
      const gait = { blocked: 0, offPlanks: 0, strides: 0, worstStride: 0,
        startE: null, endE: null };
      if (cross) {
        const [c0, c1] = cross.centreline_local_enu_m;
        const bearing = (Math.atan2(c1[0] - c0[0], c1[1] - c0[1]) * 180) / Math.PI;
        const back = 6.0;
        const len = Math.hypot(c1[0] - c0[0], c1[1] - c0[1]) || 1;
        a.walker.teleport({
          local_e: c0[0] - ((c1[0] - c0[0]) / len) * back,
          local_n: c0[1] - ((c1[1] - c0[1]) / len) * back,
          yaw_deg: bearing,
        });
        gait.startE = a.walker.state.e;
        let prevY = a.walker.state.groundY;
        a.intent.forward = 1;
        for (let i = 0; i < 500; i += 1) {
          a.walker.update(0.05, a.intent);
          const st = a.walker.state;
          gait.strides += 1;
          gait.worstStride = Math.max(gait.worstStride, Math.abs(st.groundY - prevY));
          prevY = st.groundY;
          if (st.blocked) gait.blocked += 1;
          if (st.groundY - a.terrain.walkHeight(st.e, st.n) <= 0.04) gait.offPlanks += 1;
          if (Math.hypot(st.e - c1[0], st.n - c1[1]) < 1.0) break;
        }
        a.intent.forward = 0;
        gait.endE = a.walker.state.e;
        gait.reached = Math.hypot(a.walker.state.e - c1[0], a.walker.state.n - c1[1]);
      }

      // ---- AND NOT ONE BOARD OF IT IN THE TRAVELLED WAY. A sidewalk is at the
      // lot line; the track is the street's own committed half-width out of
      // data/streets/1835.json, which is the number this layer has refused to
      // cross since T-0082. Measured on the walks themselves against the street
      // layer's own prepared centrelines, so it is the drawn geometry that
      // answers rather than a field the generator wrote about itself.
      const track = { checked: 0, inTrack: 0, worstVerge: Infinity, worst: null };
      for (const w of walks) {
        if (w.kind !== 'plank_walk') continue;   // a crossing crosses, by design
        const street = (a.streets?.records ?? []).find((r) => r.id === w.street);
        if (!street) continue;
        const line = w.centreline_local_enu_m;
        const hw = (w.width_m ?? 1.83) / 2;
        for (let s = 0; s + 1 < line.length; s += 1) {
          const [ae, an] = line[s];
          const [be, bn] = line[s + 1];
          const steps = Math.max(2, Math.round(Math.hypot(be - ae, bn - an) / 4));
          for (let i = 0; i <= steps; i += 1) {
            const e = ae + (be - ae) * (i / steps);
            const n = an + (bn - an) * (i / steps);
            let d = Infinity;
            for (let k = 1; k < street.path.length; k += 1) {
              const [x1, y1] = street.path[k - 1];
              const [x2, y2] = street.path[k];
              const dx = x2 - x1;
              const dy = y2 - y1;
              const l2 = dx * dx + dy * dy || 1;
              let t = ((e - x1) * dx + (n - y1) * dy) / l2;
              t = Math.max(0, Math.min(1, t));
              d = Math.min(d, Math.hypot(x1 + dx * t - e, y1 + dy * t - n));
            }
            const verge = d - hw - street.track_width_m / 2;
            track.checked += 1;
            if (verge < 0) {
              track.inTrack += 1;
              if (verge < track.worstVerge) track.worst = w.id;
            }
            track.worstVerge = Math.min(track.worstVerge, verge);
          }
        }
      }

      // ---- AND NOTHING GROWS THROUGH IT. The T-0124 instrument, asked of the
      // street edge's own deck rectangles: the placer at the centre of each,
      // for the generic community and for every species the ground's own zone
      // could deal there, wet and dry alike.
      const subs = a.flora.substrates();
      const floor = { decks: 0, rootable: 0, speciesAsked: 0, speciesHits: 0 };
      for (const k of (f?.keepOut ?? [])) {
        if (k.id !== 'town_street_edge__walk') continue;
        floor.decks += 1;
        let e = 0;
        let n = 0;
        for (const q of k.pts) { e += q[0]; n += q[1]; }
        e /= k.pts.length;
        n /= k.pts.length;
        if (a.flora.plantableAt(e, n)) floor.rootable += 1;
        const z = subs.find((x) => x.id === a.flora.zoneAt(e, n));
        for (const sp of (z ? z.dry.concat(z.wet) : [])) {
          floor.speciesAsked += 1;
          if (a.flora.stationOf(e, n, sp) !== null) floor.speciesHits += 1;
        }
      }
      return {
        hasRecord: !!rec,
        cardId: rec?.card?.id ?? null,
        fences: (rec?.fences ?? []).length,
        faces: rec?.rule?.faces_laid ?? null,
        walkM: rec?.rule?.walk_m ?? null,
        decks: decks.length,
        march, southWater, gait, track, floor,
      };
    });
    // T-0240 RAISED EVERY FIGURE HERE by laying Randolph Street: 16 block faces
    // to 29, 1,297.3 m of walk to 2,468.3, 11 street fence runs to 26 and 96
    // walking decks to 190. T-0241 raised them again with Washington's seven
    // faces: 29 to 36, 2,468.3 m to 3,129.1, 26 fence runs to 35 and 190 decks
    // to 239. `faces` is an equality and the other three are floors, which is
    // the same division as before — the face count is the scope statement and
    // has to be exact, and a walk that shrank under a floor would be a march
    // quietly refusing ground it used to lay.
    check(`${label}: the street edge is generated from the plat, not placed on one block`,
      // T-0461 LOWERS THE FENCE FLOOR, 34 to 32, and it is the one figure here
      // this project should expect to fall. The other three are laid ground —
      // faces, metres of walk, decks — and a rule that shrank those would be
      // refusing ground it used to lay, which is what a floor is for. Fence
      // RUNS are not: the street-fence rule refuses by design, and `_stands_on`
      // finding the building actually standing on a lot is how three lots came
      // to be refused under the clause that says a wall inside 3.0 m of the
      // frontage line IS the street wall. The exact count is asserted above in
      // the frontage census (32), so this stays a floor rather than becoming a
      // second place to keep the same number.
      // T-1053 LOWERS IT AGAIN, 32 to 31, for the same kind of reason and with
      // the same warrant: a privy left blk_south_water_franklin lot 4 for the
      // lot its household's cottage is on, so lot 4 stops being improved and its
      // street fence is refused as open prairie. Laid ground does not move —
      // faces, metres and decks are all where they were.
      edge.hasRecord && edge.cardId === 'town_street_edge'
        && edge.faces === 36 && edge.walkM >= 3050 && edge.fences >= 31
        && edge.decks >= 232,
      `record ${edge.hasRecord}, card ${edge.cardId}, ${edge.faces} block face(s), `
      + `${edge.walkM} m of walk, ${edge.fences} fence run(s), `
      + `${edge.decks} walking deck(s) registered`);
    // THE ACCEPTANCE CLAUSE, and it is a walking one: stand anywhere along
    // 220 m of Lake Street's north frontage and the boards are under the boot.
    // One sample in the mud is a hole in the sidewalk, so the bar is every one.
    check(`${label}: Lake Street's walk is continuous and walkable end to end`,
      edge.march.missing === 0 && edge.march.samples > 100
        && edge.march.onPlanks === edge.march.samples
        && edge.march.gaps === 0 && edge.march.run > 200,
      `${edge.march.onPlanks} of ${edge.march.samples} sample(s) stood on planks over `
      + `${edge.march.run?.toFixed(0)} m, ${edge.march.gaps} gap(s) in the chain, `
      + `least lift ${edge.march.worstLift?.toFixed(3)} m, `
      + `${edge.march.missing} run(s) missing from the record`);
    // T-0188 — AND THE SAME CLAUSE ON THE STREET THAT HAD NEVER PASSED IT.
    // South Water's frontages came out in pieces because eleven documented
    // buildings on that side were placed against the modern kerb and stood up to
    // 8.17 m out in the platted roadway. Six were reconciled against this
    // project's own committed street line; this is the face where that closed a
    // whole block. Asserted on the RUN as well as on the samples, because a
    // shorter run with the same lift would pass a sample-only bar.
    check(`${label}: South Water's reconciled block face is one walk, end to end`,
      edge.southWater.missing === 0 && edge.southWater.samples > 45
        && edge.southWater.onPlanks === edge.southWater.samples
        && edge.southWater.gaps === 0 && edge.southWater.run > 95,
      `${edge.southWater.onPlanks} of ${edge.southWater.samples} sample(s) stood on `
      + `planks over ${edge.southWater.run?.toFixed(0)} m, `
      + `${edge.southWater.gaps} gap(s), least lift `
      + `${edge.southWater.worstLift?.toFixed(3)} m, `
      + `${edge.southWater.missing} run(s) missing from the record`);
    check(`${label}: a board crossing carries the walker over the road at the corner`,
      edge.gait.strides > 0 && edge.gait.blocked === 0 && edge.gait.offPlanks === 0
        && edge.gait.reached < 1.5 && edge.gait.worstStride <= 0.35,
      `${edge.gait.strides} stride(s) from E ${edge.gait.startE?.toFixed(1)} to `
      + `E ${edge.gait.endE?.toFixed(1)}, ${edge.gait.blocked} blocked, `
      + `${edge.gait.offPlanks} stride(s) off the boards, ended `
      + `${edge.gait.reached?.toFixed(2)} m from the far walk, worst step `
      + `${edge.gait.worstStride?.toFixed(2)} m`);
    check(`${label}: no plank sidewalk lies in the travelled track`,
      edge.track.checked > 200 && edge.track.inTrack === 0,
      `${edge.track.inTrack} of ${edge.track.checked} station(s) inside a track edge`
      + `${edge.track.worst ? ` (worst ${edge.track.worst})` : ''}, least verge `
      + `${edge.track.worstVerge?.toFixed(2)} m`);
    check(`${label}: no street-edge walk admits a rooted plant through its deck`,
      edge.floor.decks > 90 && edge.floor.rootable === 0
        && edge.floor.speciesHits === 0,
      `${edge.floor.decks} deck(s), ${edge.floor.rootable} rootable, `
      + `${edge.floor.speciesHits} of ${edge.floor.speciesAsked} species stations granted`);

    // --- the river wharves (T-0041) --------------------------------------
    //
    // The fourth layer drawn from the dataset rather than baked, and the first
    // one that stands OVER WATER. That is where its failure modes live and they
    // are not the goods': a deck whose height came from a number beside the mesh
    // instead of from the mesh floats over the bank it ties into (T-0001's whole
    // finding), and a crib that does not reach the bed hangs in the river with
    // daylight under it. Neither is visible to any dataset gate in this repo,
    // because both are decided at load out of a terrain sample. So the geometry
    // is measured against the record and against the terrain here, and nowhere
    // else.
    const docks = await page.evaluate(() => {
      const w = window.__chicago4d.wharves;
      const terrain = window.__chicago4d.terrain;
      const mesh = w?.group?.children?.[0] ?? null;
      const g = mesh?.geometry ?? null;
      const list = w?.wharves ?? [];
      let ungraded = 0;
      let notReconstructed = 0;
      const conf = g?.getAttribute('_confidence');
      if (conf) {
        for (let i = 0; i < conf.count; i++) {
          const v = conf.getX(i);
          if (!(v >= 0 && v <= 1)) ungraded++;
          else if (v < 1) notReconstructed++;
        }
      }
      // Every vertex against its own deck outline: the quad's centre plus its
      // half-diagonal is the furthest any part of a wharf may legitimately be
      // from that centre, and a transposed axis or a dropped rotation would put
      // it tens of metres out rather than centimetres.
      let worstStray = 0;
      let lowest = Infinity;
      if (g && list.length) {
        const pos = g.getAttribute('position');
        const quads = list.map((d) => {
          const q = d.deck_quad_local_enu_m;
          const e = q.reduce((s, p) => s + p[0], 0) / 4;
          const n = q.reduce((s, p) => s + p[1], 0) / 4;
          const r = Math.max(...q.map((p) => Math.hypot(p[0] - e, p[1] - n)));
          return { e, n, r };
        });
        for (let i = 0; i < pos.count; i++) {
          const e = pos.getX(i);
          const n = -pos.getZ(i);        // world is (E, up, -N)
          lowest = Math.min(lowest, pos.getY(i));
          let best = Infinity;
          for (const q of quads) best = Math.min(best, Math.hypot(e - q.e, n - q.n) - q.r);
          worstStray = Math.max(worstStray, best);
        }
      }
      // Where each deck's own corners stand, asked of the terrain the browser
      // loaded rather than of the heightfield the generator read.
      const stands = list.map((d) => {
        const [heelL, heelR, faceR, faceL] = d.deck_quad_local_enu_m;
        return {
          id: d.structure_id,
          deckTop: d._drawn?.deck_top_m ?? null,
          bents: d._drawn?.bents ?? 0,
          treads: d._drawn?.stair_treads ?? null,
          stairRise: d._drawn?.stair_rise_m ?? null,
          stairFoot: d._drawn?.stair_foot_m ?? null,
          heelDry: [heelL, heelR].every((p) => !terrain.isWater(p[0], p[1])),
          faceWet: [faceL, faceR].every((p) => terrain.isWater(p[0], p[1])),
          bankY: Math.max(...[heelL, heelR].map((p) => terrain.surfaceHeight(p[0], p[1]))),
          depth: Math.min(...[faceL, faceR].map((p) => -terrain.surfaceHeight(p[0], p[1]))),
        };
      });
      // What the layer PUBLISHES to the walker, as against what it drew: one
      // entry per deck slab plus one per stair tread, each carrying the height
      // that slab was actually built at.
      const decks = (w?.decks ?? []).map((d) => ({ id: d.id, y: d.y, pts: d.pts.length }));
      const deckY = new Map(list.map((d) => [`${d.structure_id}__wharf`,
        d._drawn?.deck_top_m ?? null]));
      const publishedMatchesDrawn = decks
        .filter((d) => d.id.endsWith('__wharf'))
        .every((d) => d.y === deckY.get(d.id));
      const stairCeiling = w?.records?.[0]?.form?.boarding_stair_rise_m?.value ?? null;
      return {
        census: w?.census ?? null,
        decks,
        publishedMatchesDrawn,
        stairCeiling,
        keepOut: (w?.keepOut ?? []).length,
        meshes: w?.group?.children?.length ?? 0,
        verts: g?.getAttribute('position')?.count ?? 0,
        hasConfidence: !!conf,
        ungraded,
        notReconstructed,
        worstStray,
        lowest: Number.isFinite(lowest) ? lowest : null,
        stands,
      };
    });
    // SEVEN docks, and the count is the sum of two runs that landed together.
    // The two warehouses whose dock the dossier states; the four South Water
    // landings the owner's 2026-08-18 ruling reconstructed that are drawable
    // (J. H. Kinzie's, Jones's, and — since T-0106 — Carpenter's and Peck's);
    // and Robert A. Kinzie's storehouse on the WEST bank at Wolf Point, the
    // first landing this layer put on that shore (T-0107), which T-0062's
    // South-Water-only pass had left with no candidate at all.
    //
    // T-0106 moved the count because the BANK moved, not the rule. The layer
    // used to read only the forks tracing window, which closes at local E 390,
    // and refused three frontages east of it for standing off untraced bank.
    // They were never untraced — tools/trace_shoreline.py has carried the same
    // waterline off the same 1834 sheet past the drawbridge since 2026-08-10,
    // and the generator now composes both windows the way terrain_gen.py did.
    //
    // ONE refusal remains and it is a different kind from the three it replaces:
    // Harmon & Loomis's frontage IS reached by the trace, and the modelled
    // channel gives only 0.48 m under its deck face against the 0.50 m floor
    // asserted just below. It is refused by a SOUNDING, in writing, on the
    // record (clause 5b) rather than by a gap in the trace. A wharf appearing or
    // a refusal disappearing without this line moving is a rule change nobody
    // reviewed.
    // The keep-out count is SEVEN DECKS PLUS EVERY STAIR TREAD (T-0058) — a
    // tread is as much a floor as the deck it climbs to, and how many treads a
    // site takes is the terrain's answer, so the bar is the layer's own census
    // rather than a number written here that would go stale at the next regrade.
    check(`${label}: every stated dock that has traced bank under it is drawn`,
      docks.census?.wharves === 7 && docks.verts > 0
        && docks.keepOut === 7 + (docks.census?.treads ?? -1)
        && docks.census?.refused === 1
        && docks.stands.every((s) => s.bents > 0),
      `${docks.census?.wharves} wharf/wharves from ${docks.census?.records} record(s), `
      + `${docks.census?.bents} crib bent(s), ${docks.verts} vertices, `
      + `${docks.keepOut} planting keep-out(s) for 7 deck(s) and `
      + `${docks.census?.treads} tread(s), ${docks.census?.refused} refused`);
    check(`${label}: the whole wharf layer is one draw call`,
      docks.meshes === 1, `${docks.meshes} mesh(es) in the group`);
    // NOT MERELY GRADED — graded reconstructed, every vertex of it. That a dock
    // stood at these two frontages is stated; every metre of its size is
    // invented (L132), and a single vertex claiming to be inferred or attested
    // would be this layer overstating the one thing it must not.
    check(`${label}: every wharf vertex is graded reconstructed`,
      docks.hasConfidence && docks.ungraded === 0 && docks.notReconstructed === 0,
      `attribute ${docks.hasConfidence ? 'present' : 'MISSING'}, ${docks.ungraded} out `
      + `of range, ${docks.notReconstructed} claiming better than reconstructed`);
    check(`${label}: no wharf vertex strays off its own deck outline`,
      docks.worstStray <= 1.0,
      `furthest vertex ${docks.worstStray?.toFixed(2)} m outside its own deck's outline`);
    // A dock stands with its heel on the bank and its face over the water, and
    // that is the one thing about it that is derived rather than invented: if a
    // bank were re-traced or a warehouse moved and the generator not re-run, the
    // deck would be on the wrong ground and every dataset gate would still pass.
    check(`${label}: every deck ties into the bank and reaches over the water`,
      docks.stands.length === 7 && docks.stands.every((s) => s.heelDry && s.faceWet),
      docks.stands.map((s) => `${s.id} heel ${s.heelDry ? 'dry' : 'WET'} / face `
        + `${s.faceWet ? 'wet' : 'DRY'}`).join('; '));
    // The deck is neither floating over the bank nor drowned in the river, and
    // its crib reaches the bed under it — T-0001's finding, asked of a layer
    // that has no walk surface to catch it a second time.
    check(`${label}: no deck floats and every crib reaches the bed`,
      docks.stands.every((s) => s.deckTop >= 0.9 - 1e-6 && s.deckTop >= s.bankY - 1e-6
        && s.deckTop <= s.bankY + 1.0 && s.depth > 0.5)
        && docks.lowest !== null && docks.lowest < -0.5,
      docks.stands.map((s) => `${s.id} deck ${s.deckTop?.toFixed(2)} m over a bank at `
        + `${s.bankY?.toFixed(2)} m, ${s.depth?.toFixed(2)} m of water at the face`).join('; ')
      + `; lowest vertex ${docks.lowest?.toFixed(2)} m`);

    // --- and a visitor can walk out along one (T-0058) ---------------------
    //
    // THE DECK IS A FLOOR AND THE WAY ONTO IT IS DRAWN. Until T-0058 the wading
    // barrier `walkHeight()` puts over open water stood above every one of these
    // decks, so a visitor saw seven docks from the bank and could step onto none
    // of them. A wharf carries no structure record, so it cannot take the
    // bridges' `placement.walk_surface_m` route; the LAYER publishes what it drew
    // and `main.js` hands it to the walker beside the bridges'.
    //
    // That alone does not buy boarding, which is the half of this ticket that is
    // easy to declare done and is not. The deck top is the ground's, floored at
    // the record's 0.90 m freeboard over the water, and this terrain puts the
    // bank at these seven heels between 0.12 and 0.58 m — a 0.32 to 0.78 m riser
    // against the walker's 0.35 m step-up rule, which refuses six of the seven.
    // So the layer draws a boarding stair and the bar here is the WALK, not the
    // publication: start on the ground behind each dock, push forward, and be
    // standing on the planks over the water at the far end having been refused
    // nothing on the way.
    check(`${label}: every plank a wharf drew is published to the walker at the height it drew it`,
      docks.decks.length === 7 + (docks.census?.treads ?? -1)
        && docks.publishedMatchesDrawn
        && docks.decks.every((d) => d.pts === 4)
        && docks.census?.stairs === 7,
      `${docks.decks.length} walk surface(s) for 7 deck(s) and `
      + `${docks.census?.treads} tread(s) on ${docks.census?.stairs} stair(s), `
      + `heights ${docks.publishedMatchesDrawn ? 'match' : 'DISAGREE WITH'} the drawn slabs`);
    // The stair divides whatever rise the terrain leaves it into equal treads,
    // as many as it takes for none to exceed the record's ceiling — which is
    // itself under the walker's step-up rule. Asserted against BOTH, because a
    // record edited to 0.4 m would leave every other check here green and the
    // decks unboardable again.
    check(`${label}: no boarding tread rises past the record's ceiling or the step-up rule`,
      docks.stairCeiling !== null && docks.stairCeiling <= 0.35
        && docks.stands.every((s) => s.treads !== null && s.treads >= 0
          && s.stairRise !== null && s.stairRise <= docks.stairCeiling + 1e-9
          && s.stairRise <= 0.35),
      `ceiling ${docks.stairCeiling} m against the 0.35 m step-up rule; `
      + docks.stands.map((s) => `${s.id} ${s.treads} tread(s) of `
        + `${s.stairRise?.toFixed(3)} m off ${s.stairFoot?.toFixed(2)} m`).join('; '));

    const boarding = await page.evaluate(() => {
      const a = window.__chicago4d;
      const rows = [];
      for (const d of a.wharves.wharves ?? []) {
        const [heelL, heelR, faceR, faceL] = d.deck_quad_local_enu_m;
        const mid = [(heelL[0] + heelR[0]) / 2, (heelL[1] + heelR[1]) / 2];
        const face = [(faceL[0] + faceR[0]) / 2, (faceL[1] + faceR[1]) / 2];
        const span = Math.hypot(face[0] - mid[0], face[1] - mid[1]) || 1;
        const oe = (face[0] - mid[0]) / span;
        const on = (face[1] - mid[1]) / span;
        // Start on plain ground behind the stair's own foot, facing the river
        // down the deck's waterward normal — the approach a visitor coming from
        // the warehouse takes, and not a spot chosen to work.
        const back = (d._drawn?.stair_treads ?? 0) * 0.75 + 2.0;
        a.walker.teleport({
          local_e: mid[0] - oe * back,
          local_n: mid[1] - on * back,
          yaw_deg: (Math.atan2(oe, on) * 180) / Math.PI,
        });
        const row = { id: d.structure_id, blocked: 0, worstStride: 0, strides: 0,
          startY: a.walker.state.groundY };
        // A metre in from the face, which is deck by construction and is where a
        // visitor would stand to look at the river.
        const target = [face[0] - oe * 1.0, face[1] - on * 1.0];
        let prevY = a.walker.state.groundY;
        a.intent.forward = 1;
        for (let i = 0; i < 600; i += 1) {
          a.walker.update(0.05, a.intent);
          const st = a.walker.state;
          row.strides += 1;
          row.worstStride = Math.max(row.worstStride, Math.abs(st.groundY - prevY));
          prevY = st.groundY;
          if (st.blocked) row.blocked += 1;
          if (Math.hypot(st.e - target[0], st.n - target[1]) < 0.8) break;
        }
        a.intent.forward = 0;
        const st = a.walker.state;
        row.reached = Math.hypot(st.e - target[0], st.n - target[1]);
        row.endY = st.groundY;
        row.overWater = a.terrain.isWater(st.e, st.n);
        row.barrier = a.terrain.walkHeight(st.e, st.n);
        row.deckTop = d._drawn?.deck_top_m ?? null;
        rows.push(row);
      }
      return rows;
    });
    check(`${label}: a visitor walks off the bank, up the stair and out over the water`,
      boarding.length === 7 && boarding.every((r) => r.blocked === 0
        && r.reached < 1.0 && r.worstStride <= 0.35
        && r.overWater === true && r.endY === r.deckTop && r.barrier > r.endY + 1),
      boarding.map((r) => `${r.id}: ${r.strides} stride(s), ${r.blocked} blocked, `
        + `worst ${r.worstStride?.toFixed(3)} m, ended ${r.reached?.toFixed(2)} m short `
        + `at ${r.endY?.toFixed(2)} m over water=${r.overWater} `
        + `(barrier ${r.barrier?.toFixed(1)} m)`).join('; '));

    // AND IT READS FROM THE BANK, which is the whole point of building it. Stand
    // at the wharf anchor — on the ground outside Newberry & Dole's river wall,
    // looking down the dock's own waterward normal — and hold the clock so the
    // grass cannot supply the difference. Same bar as the fences, the boards and
    // the goods: worst >= 6 and mean >= 0.3.
    await page.evaluate(() => window.__chicago4d.walker.teleport(
      { local_e: 204.5, local_n: 9.8, yaw_deg: 339.4, pitch_deg: -6 }));
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const dockWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.wharves.group.visible = false; });
    const dockWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.wharves.group.visible = true; });
    const dDock = signatureDistance(dockWith, dockWithout);
    check(`${label}: the wharf reaches the screen from the bank`,
      dDock.worst >= 6 && dDock.mean >= 0.3,
      `cell delta mean ${dDock.mean?.toFixed(2)}, worst ${dDock.worst} (need worst>=6)`);

    // A dock is the largest thing on any of these derived layers and it stands
    // between a visitor on the bank and the warehouse behind them, so aiming at
    // it has to open the building it belongs to rather than answering nothing.
    const dockPick = await page.evaluate(() => {
      const hits = [];
      for (const x of [-0.3, -0.15, 0, 0.15, 0.3]) {
        for (const y of [-0.3, -0.15, 0, 0.15, 0.3]) {
          const hit = window.__chicago4d.pick({ x, y });
          if (hit?.id) hits.push(hit.id);
        }
      }
      return hits;
    });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    check(`${label}: aiming at a wharf opens the warehouse it serves`,
      dockPick.includes('newberry_dole_warehouse'),
      `25 aims returned [${[...new Set(dockPick)].join(', ') || 'nothing'}]`);

    // AND THE SAME, ON THE OTHER SHORE (T-0107). The capture above stands on the
    // SOUTH bank, so it proves the layer reads from one bank and says nothing
    // about the west one — which is exactly the shape of the gap T-0107 closed
    // in the data, and there is no reason to leave it open in the gate. Stand on
    // the west bank outside Robert Kinzie's own river wall, 7 m back along the
    // deck's waterward normal (bearing 45.3, the same geometry the Newberry
    // stand uses), and hold the clock so the river cannot supply the difference.
    await page.evaluate(() => window.__chicago4d.walker.teleport(
      { local_e: -58.3, local_n: -62.0, yaw_deg: 45.3, pitch_deg: -6 }));
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const westWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.wharves.group.visible = false; });
    const westWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.wharves.group.visible = true; });
    const westPick = await page.evaluate(() => {
      const hits = [];
      for (const x of [-0.3, -0.15, 0, 0.15, 0.3]) {
        for (const y of [-0.3, -0.15, 0, 0.15, 0.3]) {
          const hit = window.__chicago4d.pick({ x, y });
          if (hit?.id) hits.push(hit.id);
        }
      }
      return hits;
    });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    const dWest = signatureDistance(westWith, westWithout);
    check(`${label}: the west bank's landing reaches the screen from Wolf Point`,
      dWest.worst >= 6 && dWest.mean >= 0.3,
      `cell delta mean ${dWest.mean?.toFixed(2)}, worst ${dWest.worst} (need worst>=6)`);
    check(`${label}: aiming at the west bank's landing opens Robert Kinzie's store`,
      westPick.includes('robert_kinzie_store'),
      `25 aims returned [${[...new Set(westPick)].join(', ') || 'nothing'}]`);

    // Nothing grows through a plank floor (T-0124; T-0085 was the first
    // sighting). The placer is asked directly, at the centre of every deck
    // rectangle the frontage and wharf layers publish: no rooted stand for the
    // generic community, and no station for ANY species - wet or dry - that
    // the ground's own zone could deal there. The wet half is the half that
    // regressed silently before: the block-list ran after the water early
    // return, so an emergent bulrush rooted through a dock deck without any
    // gate ever asking about it.
    const floors = await page.evaluate(() => {
      const a = window.__chicago4d;
      const subs = a.flora.substrates();
      const probe = (list) => {
        const out = { decks: 0, rootable: 0, speciesHits: 0, speciesAsked: 0 };
        for (const { pts } of list ?? []) {
          if (!Array.isArray(pts) || pts.length < 3) continue;
          out.decks += 1;
          let e = 0; let n = 0;
          for (const q of pts) { e += q[0]; n += q[1]; }
          e /= pts.length; n /= pts.length;
          if (a.flora.plantableAt(e, n)) out.rootable += 1;
          const zone = a.flora.zoneAt(e, n);
          const z = subs.find((x) => x.id === zone);
          for (const sp of (z ? z.dry.concat(z.wet) : [])) {
            out.speciesAsked += 1;
            if (a.flora.stationOf(e, n, sp) !== null) out.speciesHits += 1;
          }
        }
        return out;
      };
      return { walks: probe(a.frontage?.keepOut), wharves: probe(a.wharves?.keepOut) };
    });
    check(`${label}: no plank walk admits a rooted plant through its deck`,
      floors.walks.decks > 0 && floors.walks.rootable === 0 && floors.walks.speciesHits === 0,
      `${floors.walks.decks} deck(s), ${floors.walks.rootable} rootable, `
        + `${floors.walks.speciesHits} of ${floors.walks.speciesAsked} species stations granted`);
    check(`${label}: no wharf deck admits a rooted plant - wet species included`,
      floors.wharves.decks > 0 && floors.wharves.rootable === 0 && floors.wharves.speciesHits === 0,
      `${floors.wharves.decks} deck(s), ${floors.wharves.rootable} rootable, `
        + `${floors.wharves.speciesHits} of ${floors.wharves.speciesAsked} species stations granted`);

    // --- the boats on the river (T-0063) ---------------------------------
    //
    // The first layer that RIDES the water rather than standing in it, and its
    // failure modes are new: an afloat hull whose keel is not under the water
    // plane is flying, one whose bed is nearer than its own draft is aground,
    // and a hull inside the drawbridge's clearance is a rule change nobody
    // reviewed. All of it is decided at load out of the record and a terrain
    // sample, so it is measured here against the terrain the browser actually
    // loaded, and nowhere else.
    const flotilla = await page.evaluate(() => {
      const b = window.__chicago4d.boats;
      const terrain = window.__chicago4d.terrain;
      const mesh = b?.group?.children?.[0] ?? null;
      const g = mesh?.geometry ?? null;
      let ungraded = 0;
      let notReconstructed = 0;
      const conf = g?.getAttribute('_confidence');
      if (conf) {
        for (let i = 0; i < conf.count; i++) {
          const v = conf.getX(i);
          if (!(v >= 0 && v <= 1)) ungraded++;
          else if (v < 1) notReconstructed++;
        }
      }
      const rec = (b?.records ?? [])[0] ?? {};
      const clearance = rec.clearances?.drawbridge_span_m?.value ?? 30;
      const form = rec.form ?? {};
      const stands = (b?.boats ?? []).map((boat) => {
        const [e, n] = boat.position_local_enu_m;
        const draft = form[boat.type]?.draft_m?.value ?? 0;
        const bed = terrain.surfaceHeight(e, n);
        return {
          id: boat.id,
          type: boat.type,
          afloat: boat._drawn?.afloat ?? null,
          keelY: boat._drawn?.keel_y_m ?? null,
          wet: terrain.isWater(e, n),
          bed,
          draft,
          clearOfSpan: n >= 120 || Math.abs(e - 699.17) >= clearance,
        };
      });
      return {
        census: b?.census ?? null,
        keepOut: (b?.keepOut ?? []).length,
        meshes: b?.group?.children?.length ?? 0,
        verts: g?.getAttribute('position')?.count ?? 0,
        hasConfidence: !!conf,
        ungraded,
        notReconstructed,
        stands,
      };
    });
    // Thirteen boats since T-0140 — three schooners in the reach below the
    // drawbridge and TWO AT THE WOLF POINT LANDINGS, four rowboats at the South
    // Water bank and two more at the west bank at the forks, two canoes at the
    // fort landing — and ZERO refused: every authored position was chosen
    // against the committed heightfield, so a refusal appearing here means the
    // terrain moved under the record and the record was not re-read. FIVE
    // planting keep-outs, one per BEACHED hull (the two South Water skiffs, the
    // Wolf Point skiff and the two fort canoes); an afloat hull needs none.
    check(`${label}: every authored boat is on the water`,
      flotilla.census?.boats === 13 && flotilla.census?.refused === 0
        && flotilla.census?.schooners === 5 && flotilla.census?.rowboats === 6
        && flotilla.census?.canoes === 2 && flotilla.verts > 0
        && flotilla.keepOut === 5,
      `${flotilla.census?.boats} boat(s) (${flotilla.census?.schooners} schooner(s), `
      + `${flotilla.census?.rowboats} rowboat(s), ${flotilla.census?.canoes} canoe(s)), `
      + `${flotilla.census?.refused} refused, ${flotilla.verts} vertices, `
      + `${flotilla.keepOut} planting keep-out(s)`);
    check(`${label}: the whole boat layer is one draw call`,
      flotilla.meshes === 1, `${flotilla.meshes} mesh(es) in the group`);
    check(`${label}: every boat vertex is graded reconstructed`,
      flotilla.hasConfidence && flotilla.ungraded === 0 && flotilla.notReconstructed === 0,
      `attribute ${flotilla.hasConfidence ? 'present' : 'MISSING'}, ${flotilla.ungraded} out `
      + `of range, ${flotilla.notReconstructed} claiming better than reconstructed`);
    // An afloat hull floats: keel below the water plane by its own draft, bed
    // below the keel by the record's under-keel margin, real water at the
    // position. A beached hull sits on ground at the water's edge — not out on
    // open water, not up on the prairie.
    check(`${label}: every afloat hull floats in its own water`,
      flotilla.stands.filter((s) => s.afloat).every((s) => s.wet
        && s.keelY !== null && Math.abs(s.keelY + s.draft) < 1e-6
        && s.bed <= s.keelY - 0.25),
      flotilla.stands.filter((s) => s.afloat).map((s) => `${s.id} keel `
        + `${s.keelY?.toFixed(2)} m, bed ${s.bed?.toFixed(2)} m`).join('; '));
    check(`${label}: every beached hull sits on the bank, at the water`,
      flotilla.stands.filter((s) => !s.afloat).every((s) => s.keelY !== null
        && s.keelY >= -0.6 && s.keelY <= 1.5),
      flotilla.stands.filter((s) => !s.afloat).map((s) => `${s.id} keel `
        + `${s.keelY?.toFixed(2)} m`).join('; '));
    check(`${label}: the drawbridge's navigation span stays clear`,
      flotilla.stands.every((s) => s.clearOfSpan),
      flotilla.stands.filter((s) => !s.clearOfSpan).map((s) => s.id).join(', ') || 'all clear');

    // AND THE REACH READS AS A HARBOUR, which is what the owner asked for.
    // Stand on the south bank looking down the reach at the moored schooners
    // and hold the clock, so the water and the grass cannot supply the
    // difference. Same bar as the fences, the boards, the goods and the docks.
    await page.evaluate(() => window.__chicago4d.walker.teleport(
      { local_e: 765, local_n: 15, yaw_deg: 353, pitch_deg: -2 }));
    await page.waitForTimeout(350);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const boatWith = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.boats.group.visible = false; });
    const boatWithout = await page.evaluate(() => window.__chicago4d.capture());
    await page.evaluate(() => { window.__chicago4d.boats.group.visible = true; });
    const dBoat = signatureDistance(boatWith, boatWithout);
    check(`${label}: the schooners reach the screen from the bank`,
      dBoat.worst >= 6 && dBoat.mean >= 0.3,
      `cell delta mean ${dBoat.mean?.toFixed(2)}, worst ${dBoat.worst} (need worst>=6)`);

    // A boat belongs to no structure, so aiming at one has to open its OWN
    // card — the type, the size and what bounded the invention — rather than
    // answering nothing or answering for a building behind it.
    const boatPick = await page.evaluate(() => {
      const hits = [];
      for (const x of [-0.3, -0.15, 0, 0.15, 0.3]) {
        for (const y of [-0.3, -0.15, 0, 0.15, 0.3]) {
          const hit = window.__chicago4d.pick({ x, y });
          if (hit?.id) hits.push(hit.id);
        }
      }
      const title = document.querySelector('#popup h2')?.textContent ?? '';
      return { hits, title };
    });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    check(`${label}: aiming at a schooner opens the boat's own card`,
      boatPick.hits.some((id) => id.startsWith('boat_schooner')),
      `25 aims returned [${[...new Set(boatPick.hits)].join(', ') || 'nothing'}] `
      + `(last card: "${boatPick.title}")`);

    // --- the scene actually draws ----------------------------------------
    await page.evaluate(() => window.__chicago4d.frame('sauganash_hotel', 26));
    await page.waitForTimeout(250);

    // Hold the visual clock across the three captures below. They ask what the
    // confidence view does to a frame, and the wind blows between them: without
    // the hold the residual is mostly swaying grass, which made the restore
    // check fail about two runs in three. Holding removes the variable rather
    // than widening the tolerance around it, and it makes the "changes the
    // render" assertion strictly harder, since sway can no longer supply any of
    // the difference it needs to find.
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const off = await page.evaluate(() => window.__chicago4d.capture());
    check(`${label}: canvas renders non-black`,
      off.mean > 12 && off.litFraction > 0.5,
      `mean luminance ${off.mean?.toFixed(1)}, lit ${(off.litFraction * 100).toFixed(0)}%`);
    check(`${label}: drawing buffer matches the viewport`,
      off.width >= viewport.width && off.height >= viewport.height * 0.8,
      `${off.width}x${off.height} for a ${viewport.width}x${viewport.height} viewport`);

    // --- the confidence view ---------------------------------------------
    const modeBefore = await page.evaluate(() => window.__chicago4d.confidenceView);
    await page.evaluate(() => window.__chicago4d.setConfidenceView(true));
    const on = await page.evaluate(() => window.__chicago4d.capture());
    const modeAfter = await page.evaluate(() => window.__chicago4d.confidenceView);
    const d = signatureDistance(off, on);
    check(`${label}: confidence toggle flips state`, modeBefore === false && modeAfter === true,
      `before ${modeBefore}, after ${modeAfter}`);
    check(`${label}: confidence view changes the render`,
      d.worst >= 6 && d.mean >= 0.6,
      `cell delta mean ${d.mean?.toFixed(2)}, worst ${d.worst} (need worst>=6)`);

    await page.evaluate(() => window.__chicago4d.setConfidenceView(false));
    const back = await page.evaluate(() => window.__chicago4d.capture());
    const dBack = signatureDistance(off, back);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    // With the clock held these are two captures of one unchanged scene, so the
    // restored frame should be the SAME frame. The residual left is readback
    // noise, not weather; a confidence tint left enabled changes the mean
    // broadly (the assertion immediately above pins that at >= 0.6).
    check(`${label}: turning it off restores the render`,
      dBack.mean <= 0.1 && dBack.worst <= 3,
      `residual mean ${dBack.mean?.toFixed(2)}, worst-cell delta ${dBack.worst}`);

    // --- the confidence machinery is INERT when nothing is switched on -------
    //
    // This is the assertion I owed after shipping a regression the whole suite
    // waved through. Adding the hide-a-level branch to the shared fragment
    // patch made the RIVER DISAPPEAR: the water surface stopped drawing and the
    // town rendered one flat olive from the air, with nothing hidden and the
    // uniform provably at (0,0,0). Every existing check passed, because they
    // all compare a frame against another frame taken the same way — and both
    // were equally wrong.
    //
    // What catches it is a claim about the WORLD rather than about a delta: the
    // river is there, it is much darker than the prairie, and from above it
    // occupies a large part of the frame. If the water stops drawing, the
    // contrast between the darkest and the median cell collapses.
    //
    // (`terrainLoad` itself is read before the stage split now — see the T-0060
    // banner above — because stage 2's terrain-problem check shares it.)
    //
    // The authored water surface spans the whole modelled box — about 5.4 km by
    // 4.2 km. The FALLBACK is a 2400 m square at the datum. Those are nowhere
    // near each other, which makes this a reliable test of "did the real river
    // load" rather than a test of how the river looks.
    //
    // It exists because the answer was NO on the published site and every check
    // passed: terrain.js built its own GLTFLoader without the meshopt decoder,
    // which was harmless for as long as the terrain GLBs were the only assets
    // gltf-transform had never been run over. The moment they were rebaked, the
    // ground quietly fell back to a grid rebuilt from the heightfield — which
    // looks right — and the water fell back to a flat square laid over the whole
    // town. The river vanished and the place read as flooded.
    check(`${label}: the traced river loaded, rather than the flat fallback plane`,
      terrainLoad.box !== null
      && terrainLoad.box.w > 3000 && terrainLoad.box.d > 3000
      && terrainLoad.groundTiles > 1,
      terrainLoad.box
        ? `water ${terrainLoad.box.w} x ${terrainLoad.box.d} m across `
          + `(the fallback is 2400 x 2400), ${terrainLoad.groundTiles} ground tile(s)`
        : 'no water mesh in the scene at all');

    inStageWork = false;
    } // end PART 2 (T-0060 stage 1b, cut by T-0121)
    // PART 3 — "the ground faces the sky" through the confidence card: the
    // ground, the invented residents, and every graded claim the card makes.
    // Every boundary sits where the crossing bindings were measured at zero
    // (scope-aware, brace-depth-anchored — the indent-anchored scans missed
    // `terrainLoad` at column 0); the two that did cross, `terrainLoad` and
    // `streetLayer`, are read above the split, so any single stage boots into
    // exactly the state its first line expects.
    if (stageOn(3)) {
    inStageWork = true;

    // --- the ground faces the sky ------------------------------------------
    //
    // `gltf-transform optimize` SIMPLIFIES BY DEFAULT, and on this dataset that
    // is damage rather than optimisation. The terrain was the one asset it had
    // never been run over, so nobody had seen what it does to a large, low-relief
    // surface: the ground came back at ~100 vertices per tile instead of 56,463,
    // with 33 of one tile's 99 remaining vertices facing straight DOWN — a
    // hard-edged black polygon across the south-east of the town, visible only
    // from the air, and only in the published tree.
    //
    // A downward normal on the ground is never right, at any level of detail, so
    // this asserts the surface rather than the toolchain. It also protects the
    // measured promise generators/terrain_gen.py makes: it ray-casts its
    // decimated mesh against the heightfield and refuses to export past 30 mm of
    // drift, and a second blind simplification pass silently voids that.
    const groundNormals = await page.evaluate(() => {
      const api = window.__chicago4d;
      let downward = 0;
      let verts = 0;
      const tiles = [];
      api.scene3d.traverse((o) => {
        if (!o.isMesh || !/^terrain__/.test(o.name || '')) return;
        const n = o.geometry.getAttribute('normal');
        if (!n) return;
        let tileDown = 0;
        for (let i = 0; i < n.count; i += 1) {
          const y = n.getY(i);
          if (!Number.isFinite(y) || y < 0.1) tileDown += 1;
        }
        verts += n.count;
        downward += tileDown;
        tiles.push({ name: o.name, verts: n.count, down: tileDown,
                     share: n.count ? tileDown / n.count : 0 });
      });
      tiles.sort((a, b) => b.share - a.share);
      return { tiles: tiles.length, verts, downward, worstTile: tiles[0] ?? null };
    });
    // TWO assertions, because there are two different things here and only one
    // of them is the bug this was written for.
    //
    // (a) NO TILE IS SUBSTANTIALLY DOWNWARD-FACING. That is the simplifier's
    //     signature and what a visitor actually sees: the wedge was 33 of one
    //     tile's 99 vertices — a third of it — and it read as a black polygon.
    //     One per cent of a tile is already far outside anything the terrain
    //     generator produces.
    check(`${label}: no ground tile faces away from the sky`,
      groundNormals.tiles > 1 && groundNormals.verts > 1000
      && (groundNormals.worstTile?.share ?? 1) < 0.01,
      `${groundNormals.tiles} tiles, worst ${groundNormals.worstTile?.name}: `
      + `${groundNormals.worstTile?.down}/${groundNormals.worstTile?.verts} down `
      + `(${((groundNormals.worstTile?.share ?? 0) * 100).toFixed(2)}%)`);
    // (b) AND THE SCATTERED ONES ARE GONE — the cap is 0, and it is 0 because
    //     the generator now proves the invariant instead of this gate banking
    //     the breaches. This assertion was written with a cap of 79 (ROADMAP
    //     T-BUG2): isolated vertices, inside the town rather than in any
    //     contiguous patch, that came out of the terrain generator facing down
    //     and produced no visible artefact — a real defect the gate could pin
    //     but not fix, so it pinned the measured number and let it only fall.
    //
    //     T-0014 fixed it at the source. `generators/terrain_gen.py`
    //     § _face_the_sky() re-winds the 33 backwards faces the n-gon
    //     triangulation produced and deletes the 197 that stand edge-on, on a
    //     classifier with no threshold in it — the plan-projected signed area,
    //     which on this 2.5 m lattice is either exactly 0.0 or at least
    //     3.125 m² and never in between. The shipped master's worst ground
    //     normal now points 0.737 up, so this is not a number sitting near its
    //     bar: nothing quantisation does to it can reach 0.1.
    //
    //     KEEP IT AT 0. A cap that can be raised is a defect that can be
    //     re-banked, and this one already was, for nine days.
    check(`${label}: no ground vertex faces downward`,
      groundNormals.downward === 0,
      `${groundNormals.downward} of ${groundNormals.verts} vertices face down `
      + `(the bar is 0 — see T-0014, was ROADMAP T-BUG2)`);

    // And the renderer's OWN account of it, which is the part that was ignored:
    // it pushed the fallback to `problems` every single load and nothing read it.
    check(`${label}: the terrain and river report no load problems`,
      terrainLoad.terrainProblems.length === 0,
      terrainLoad.terrainProblems.slice(0, 2).join(' | '));

    // --- the ground you see IS the ground the town stands on (R-BUG3c) ------
    //
    // The gate above protects the terrain generator's promise — 30 mm between
    // its decimated mesh and the heightfield — and it cannot see whether the
    // promise survived. It measures normals, and this project measured the fit
    // only at bake time, on the MASTER. The file a browser loads is the
    // derivative `gltf-transform optimize` writes afterwards, and it quantises
    // POSITION to 14 bits under one uniform node scale: on a mesh 5,020 m wide
    // and 8.6 m tall that is a 306 mm vertical lattice. Measured on the shipped
    // bytes, the ground was up to 228 mm off the field with an rms of 85 mm.
    //
    // Everything in the town anchors to the heightfield — collision, buildings,
    // flora roots, street drape — so the roadway was drawn 22 mm above a sampler
    // that sat up to 228 mm BELOW the visible ground, and the near field went
    // under it at a constant radius. That is R-BUG3c, reported twice by the
    // owner, and three gates missed it because they all compared the render to
    // itself.
    //
    // This one compares the SURFACE THAT IS DRAWN — the tiles, after every load
    // step — against the sampler the town is placed with, at the tiles' own
    // vertices. It is not a screenshot and it cannot be fooled by one.
    const groundFit = await page.evaluate((tol) => {
      const api = window.__chicago4d;
      const hf = api.terrain.heightfield;
      const eMin = hf.originE;
      const eMax = hf.originE + hf.widthM;
      const nMin = hf.originN;
      const nMax = hf.originN + hf.depthM;
      let worst = 0;
      let over = 0;
      let compared = 0;
      let worstAt = null;
      api.scene3d.traverse((o) => {
        if (!o.isMesh || !/^terrain__/.test(o.name || '')) return;
        const p = o.geometry.getAttribute('position');
        for (let i = 0; i < p.count; i += 1) {
          const e = p.getX(i);
          const n = -p.getZ(i);
          // The skirt reaches 1.55 km past the modelled box, where there is no
          // field to be right or wrong about. Scoring it would measure the
          // sampler's fallback rather than the ground.
          if (e < eMin || e > eMax || n < nMin || n > nMax) continue;
          compared += 1;
          const d = Math.abs(p.getY(i) - api.terrain.surfaceHeight(e, n));
          if (d > tol) over += 1;
          if (d > worst) { worst = d; worstAt = { e: +e.toFixed(1), n: +n.toFixed(1) }; }
        }
      });
      return { worst, over, compared, worstAt, fit: api.terrain.groundFit };
    }, 0.03);
    // The generator's own MESH_FIT_TOLERANCE_M, deliberately: the promise that
    // "the ground you stand on is the ground you see" is not weaker for the file
    // that ships than for the file that does not.
    check(`${label}: the drawn ground matches the heightfield the town anchors to`,
      groundFit.compared > 10000 && groundFit.over === 0 && groundFit.worst <= 0.03,
      `worst ${(groundFit.worst * 1000).toFixed(1)} mm of 30 mm over `
      + `${groundFit.compared.toLocaleString()} drawn vertices`
      + (groundFit.worstAt ? ` (at E ${groundFit.worstAt.e}, N ${groundFit.worstAt.n})` : '')
      + `, ${groundFit.over} beyond tolerance`);
    // And the renderer's own account of the repair, so a run that stops needing
    // it — because the terrain stopped shipping quantised — says so out loud
    // rather than silently doing nothing.
    check(`${label}: the ground was conformed to the field, with nothing left over`,
      !!groundFit.fit && groundFit.fit.residual_max_m <= 1e-5,
      groundFit.fit
        ? `${groundFit.fit.moved.toLocaleString()} of `
          + `${groundFit.fit.vertices.toLocaleString()} vertices moved, `
          + `up to ${(groundFit.fit.correction_max_m * 1000).toFixed(1)} mm; `
          + `residual ${(groundFit.fit.residual_max_m * 1000).toFixed(4)} mm`
        : 'the terrain reported no fit at all');
    await page.evaluate(() => {
      const api = window.__chicago4d;
      api.setFly(false);
      api.walker.teleport({ local_e: 107, local_n: -103, yaw_deg: 180 });
    });
    await page.waitForTimeout(250);

    // --- the evidence-only households, after the invented names went (T-0524) -
    //
    // WHAT THIS BLOCK USED TO ASSERT, AND WHY IT NO LONGER CAN. Until 2 September
    // 2026 the layer minted a `reconstructed` person for every household the
    // occupation census argued the town needed, gave each one an invented period
    // name, and carried a `name_basis` block declaring the invention. K18 pinned
    // the declaration: a visitor who reads a name must be able to see, in the same
    // card, that we made it up. The owner's T-0489 ruling retired that population —
    // `data/residents/index.json` now reads `by_grade.reconstructed: 0` — and the
    // records that survived it say so in as many words ("The invented name this
    // record used to carry, and its name_basis block, are retired: an invented name
    // is not kept beside a documented one").
    //
    // So the subject of the first two assertions is gone, and the honest move is
    // not to delete a passing-shaped check: it is to keep the wire and turn it
    // round. What the layer now promises is the OPPOSITE promise — that the
    // invented-name programme left nothing behind — and that is what is asserted,
    // over the manifest's own tally and over the record this block already fetches.
    // If a future run mints an invented name again, this trips.
    //
    // The `hh_inf_` households the ruling kept are `unplaced` evidence-only
    // households: one head the papers name, graded `inferred`, on no roof.
    const invented = await page.evaluate(async () => {
      const api = window.__chicago4d;
      const res = await fetch(new URL('residents/index.json', api.dataBase));
      const index = await res.json();
      const row = index.households.find((h) => h.id.startsWith('hh_inf_'));
      const hh = await (await fetch(new URL(`residents/${row.file}`, api.dataBase))).json();
      const head = hh.persons.find((p) => p.relationship === 'head') || hh.persons[0];
      return {
        id: hh.id,
        household: hh.name,
        name: head?.name,
        headGrade: head?.grade,
        headNote: (head?.note || '').slice(0, 400),
        // The retirement, read three ways: the layer's own tally, this record's
        // people, and the block that carried the declaration.
        reconstructedInLayer: index.counts?.by_grade?.reconstructed,
        reconstructedHere: hh.persons.filter((p) => p.grade === 'reconstructed').length,
        anyNameBasis: hh.persons.some((p) => !!p.name_basis),
        opening: String(hh.name ?? '').trim().split(/\s+/)[0]
          .replace(/[^A-Za-z]/g, '').toLowerCase(),
        grades: index.vocabulary.grades,
      };
    });
    check(`${label}: an evidence-only household's head is a person a source names`,
      /^[A-Z]/.test(invented.name ?? '')
      && !/unnamed|inferred resident/i.test(invented.name ?? '')
      && invented.grades?.includes(invented.headGrade)
      && invented.headGrade !== 'reconstructed',
      `head "${invented.name}" graded ${invented.headGrade}`);
    // The inverse of the retired K18 check, and the reason it is here rather than
    // deleted: `name_basis` is still rendered by `js/residents.js` (the "How this
    // person is named" row), so nothing in the renderer stops an invented name
    // coming back. The DATA is what the ruling changed, so the data is the gate.
    check(`${label}: the invented-name programme left nothing behind on this layer`,
      invented.reconstructedInLayer === 0 && invented.reconstructedHere === 0
      && invented.anyNameBasis === false,
      `${invented.reconstructedInLayer} reconstructed people in the manifest, `
      + `${invented.reconstructedHere} on ${invented.id}, `
      + `name_basis present: ${invented.anyNameBasis}`);
    // The layer-word in this label was `inferred` until K23a, and this assertion
    // was pinned to the HEAD'S OWN GRADE — which is how a name claiming a better
    // grade than its own record survived a release gate. T-0489 renamed these
    // households again, to "Evidence-only household — <head>", and that phrase is
    // NOT a grade word, so pinning to the head's grade now asserts a coincidence.
    // The two things worth keeping are kept instead: the household is named for
    // the person it is a household of, and its opening word may never be a grade
    // the record does not hold — the K23a rule, applied to household names too.
    check(`${label}: the household is named for its head and still says which layer it is`,
      /household/i.test(invented.household ?? '')
      && !!invented.name && (invented.household ?? '').includes(invented.name)
      && /evidence-only/i.test(invented.household ?? '')
      && !['attested', 'inferred', 'reconstructed', 'documented', 'conjectural',
        'recommended'].includes(invented.opening),
      `household "${invented.household}" for head "${invented.name}" `
      + `graded ${invented.headGrade}`);

    // --- the prose may not name a level the record is not (K23a) ------------
    //
    // Owner-reported from a card on the dev preview: the title read "Inferred A2
    // barn or carriage shed #08" while every chip beneath it read RECONSTRUCTED.
    // Both were honest once. `inferred` was the BOTTOM tier under the vocabulary
    // v76 retired; it is the MIDDLE one now — reasoned from evidence about this
    // particular thing — which an anonymous count-unit is exactly not. So 193
    // names were claiming a grade better than their own record, in the largest
    // text on the card, and nothing in the suite could see it.
    //
    // The gate is over the whole registry rather than a sample: this fault
    // arrived from a generator, so it arrives 193 at a time or not at all.
    const naming = await page.evaluate(() => {
      const LEVELS = ['attested', 'inferred', 'reconstructed'];
      // The words v76 retired. A name may never open with one of these again:
      // `documented` and `conjectural` were the old top and bottom tiers, and
      // `recommended` was the word this project renamed away from by name.
      const RETIRED = ['documented', 'conjectural', 'recommended'];
      const verdict = (name, grade) => {
        const first = String(name ?? '').trim().split(/\s+/)[0]
          .replace(/[^A-Za-z]/g, '').toLowerCase();
        if (RETIRED.includes(first)) return `names the retired level "${first}"`;
        if (LEVELS.includes(first) && first !== grade) {
          return `opens "${first}" over a record graded "${grade}"`;
        }
        return null;
      };
      const bad = [];
      let scanned = 0;
      for (const id of window.__chicago4d.registry.keys()) {
        const s = window.__chicago4d.registry.get(id)?.sidecar;
        if (!s?.name) continue;
        scanned += 1;
        const why = verdict(s.name, s.documented_range?.confidence);
        if (why) bad.push(`${id}: "${s.name}" ${why}`);
      }
      // Put the fault back, in memory, and require the predicate to name it —
      // otherwise a gate that scans a clean tree is indistinguishable from a
      // gate that scans nothing, and this file has shipped that mistake before
      // (STATUS § 28: a card flag tested against a key the data never wrote).
      const planted = [
        verdict('Inferred A1 stable #07', 'reconstructed'),
        verdict('Recommended A1 stable #07', 'reconstructed'),
        verdict('Reconstructed A1 stable #07', 'reconstructed'),
      ];
      return { bad, scanned, planted };
    });
    check(`${label}: no building's name claims a grade its own record does not`,
      naming.scanned > 100 && naming.bad.length === 0,
      `${naming.scanned} scanned, ${naming.bad.length} bad — ${naming.bad.slice(0, 3).join(' | ')}`);
    check(`${label}: that check still catches the fault when it is put back`,
      naming.planted[0] !== null && naming.planted[1] !== null
      && naming.planted[2] === null,
      `planted verdicts: ${JSON.stringify(naming.planted)}`);

    // --- and the title may not be a part number at all (T-0076) -------------
    //
    // Owner-reported from the same card: "this name is not great Reconstructed D3
    // one-room frame cottage #03 … give the locations useful names not technical D3 #03
    // names, you can have that somewhere on the card for reference identity purposes but
    // dont make it the title." The rule is `js/display-name.js`; this asserts the three
    // things that rule owes a visitor, on the shipped module rather than on a copy of it.
    //
    // Whole-registry again, for the naming gate's reason: the titles are composed by one
    // function over one dataset, so a regression arrives 222 at a time. The card check
    // underneath is what makes it about the CARD — a title composed correctly and never
    // rendered would satisfy a registry scan and satisfy nobody standing in the town.
    const titles = await page.evaluate(async () => {
      const mod = await import(new URL('js/display-name.js', location.href).href);
      const registry = window.__chicago4d.registry;
      const specShaped = [];
      let anonymous = 0;
      let empty = 0;
      for (const [id, record] of registry) {
        const s = record?.sidecar;
        if (!s) continue;
        const { title, spec } = mod.displayName(s, id);
        if (!title) empty += 1;
        if (s.reconstruction?.status === 'inferred_anonymous') {
          anonymous += 1;
          if (/#\s*\d+\s*$/.test(title) || /^Reconstructed\b/.test(title)) {
            specShaped.push(`${id}: "${title}"`);
          }
          // The other half of the owner's sentence: the production identity is kept.
          if (spec !== s.name) specShaped.push(`${id}: reference line lost "${s.name}"`);
        }
      }
      // A scan of a clean tree is indistinguishable from a scan of nothing, so the rule
      // is also run against records made up here — one occupied, one empty, one named.
      const anon = (extra) => ({
        name: 'Reconstructed D3 one-room frame cottage #03',
        reconstruction: { status: 'inferred_anonymous', family: 'D3' }, ...extra });
      const planted = {
        occupied: mod.displayName(anon({ residents: [{ name: 'The Tuttle household — a '
          + 'reconstructed carpenter (south division)', relation: 'lived here',
          persons: [{ name: 'Amos Tuttle', relationship: 'head' }] }] }), 'x').title,
        vacant: mod.displayName(anon({}), 'x').title,
        named: mod.displayName({ name: 'Green Tree Tavern' }, 'green_tree_tavern').title,
      };
      // And the search has to answer to BOTH names, which is the whole argument for
      // keeping the production identity anywhere.
      //
      // T-0524: this used to pick ONE record for both halves — an anonymous roof that
      // an inferred household had been placed on — and T-0489 emptied `residents` on
      // every one of the 249 anonymous roofs, so the find returned `undefined` and both
      // halves read off an empty object. The two halves are two claims and they now
      // take the subject each one is actually about: the production identity is the
      // anonymous programme's, so `bySpec` reads an anonymous roof (any of them, since
      // none is occupied any more); "found by the people in it" is a claim about a
      // record that HAS people, so `byHousehold` reads one of the 48 that do. Neither
      // half was weakened — the same two things are asserted, on subjects that exist.
      const anonId = [...registry.keys()].find((id) => registry.get(id)?.sidecar
        ?.reconstruction?.status === 'inferred_anonymous'
        && mod.displayName(registry.get(id).sidecar, id).spec);
      const sidecar = registry.get(anonId)?.sidecar ?? {};
      const terms = mod.searchTerms(sidecar, anonId);
      const housedId = [...registry.keys()].find((id) => /^The\s+(.+?)\s+household\b/
        .test((registry.get(id)?.sidecar?.residents ?? [])[0]?.name ?? ''));
      const housed = registry.get(housedId)?.sidecar ?? {};
      const surname = /^The\s+(.+?)\s+household\b/.exec(housed.residents?.[0]?.name ?? '');
      const housedTerms = mod.searchTerms(housed, housedId);
      // The card itself: opened on that record, reading what a visitor reads.
      window.__chicago4d.popup.show(registry.get(anonId));
      const card = {
        id: anonId,
        heading: document.querySelector('#popup h2')?.textContent?.trim() ?? '',
        reference: document.querySelector('#popup .pop-spec')?.textContent ?? '',
        expected: mod.displayName(sidecar, anonId).title,
        spec: sidecar.name,
      };
      window.__chicago4d.popup.close();
      return { specShaped, anonymous, empty, planted, card,
               searchable: {
                 bySpec: terms.includes(sidecar.name ?? '\u0000'),
                 byHousehold: !!surname && housedTerms.includes(surname[1]),
                 housedId, household: surname?.[1] ?? '',
               } };
    });
    check(`${label}: no building titles itself by its part number`,
      titles.anonymous > 100 && titles.empty === 0 && titles.specShaped.length === 0,
      `${titles.anonymous} anonymous roofs, ${titles.empty} untitled, `
      + `${titles.specShaped.length} still spec-titled — ${titles.specShaped.slice(0, 3).join(' | ')}`);
    check(`${label}: the naming rule titles a house for its people and an empty one plainly`,
      titles.planted.occupied === 'The Tuttle house'
      && titles.planted.vacant === 'A vacant one-room frame cottage'
      && titles.planted.named === 'Green Tree Tavern',
      `planted: ${JSON.stringify(titles.planted)}`);
    check(`${label}: the card shows that title and keeps the reference below it`,
      titles.card.heading === titles.card.expected
      && !!titles.card.spec && titles.card.reference.includes(titles.card.spec),
      `${titles.card.id}: "${titles.card.heading}" (want "${titles.card.expected}") `
      + `over reference "${titles.card.reference.trim()}"`);
    check(`${label}: search still finds a roof by its part number and a house by its household`,
      titles.searchable.bySpec && titles.searchable.byHousehold,
      `by spec ${titles.searchable.bySpec} on ${titles.card.id}, `
      + `by household ${titles.searchable.byHousehold} `
      + `("${titles.searchable.household}" on ${titles.searchable.housedId})`);

    // --- hiding a level (K17) ----------------------------------------------
    //
    // The other half of the confidence control. Colouring asks how sure we are;
    // hiding asks what is left if you keep only what somebody wrote down, and
    // turning off `reconstructed` empties most of this town — which is the true
    // shape of the evidence and the least comfortable thing the project can
    // show. Three things have to hold: it must actually REMOVE geometry (not
    // recolour it), it must work with the colouring OFF (the answer reads far
    // better in daylight than through an amber filter), and it must survive a
    // reload, because a visitor who hid a level and came back to a full town
    // would reasonably conclude the control did nothing.
    // Measured from ABOVE, because the difference has to be visible to be
    // measurable: at eye level the frame is mostly prairie and one or two
    // roofs, so removing 162 buildings barely moves a pixel signature. From the
    // aerial anchor the reconstructed town IS the picture.
    await page.evaluate(() => window.__chicago4d.setConfidenceView(false));
    await page.evaluate(async () => {
      const api = window.__chicago4d;
      api.goTo('from_above');
      await new Promise((r) => setTimeout(r, 400));
    });
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const fullTown = await page.evaluate(() => window.__chicago4d.capture());
    const hiddenState = await page.evaluate(async () => {
      const api = window.__chicago4d;
      api.hud.setHidden('reconstructed', true, { announce: false });
      await new Promise((r) => setTimeout(r, 120));
      const u = api.confidence.uniforms.uHideLevel.value;
      return { uniform: [u.x, u.y, u.z], hidden: api.hud.hiddenLevels,
               colouring: api.confidenceView,
               marked: !!document.getElementById('confidence-group')
                 ?.classList.contains('has-hidden'),
               stored: window.localStorage.getItem('chicago4d.confidence.hidden') };
    });
    const thinnedTown = await page.evaluate(() => window.__chicago4d.capture());
    const dHide = signatureDistance(fullTown, thinnedTown);
    // Thresholds calibrated against this suite's own measured noise floor, not
    // guessed: the "turning it off restores the render" check two blocks up
    // treats mean <= 0.1 with worst <= 3 as readback noise on an unchanged
    // frame. So worst >= 6 and mean >= 0.25 is comfortably a real change. The
    // mean bar is lower than the colour test's because the shapes of the two
    // effects differ — a tint moves every lit cell a little, while removing
    // buildings moves the cells that HAD buildings a lot and leaves sky and
    // prairie untouched. At 390x780 the frame is proportionally more sky, which
    // is why a bar set for the desktop frame failed a mobile run that was
    // showing the feature working perfectly.
    check(`${label}: hiding a level removes it from the view`,
      dHide.worst >= 6 && dHide.mean >= 0.25,
      `cell delta mean ${dHide.mean?.toFixed(2)}, worst ${dHide.worst}`);
    check(`${label}: hiding works with the colouring switched off`,
      hiddenState.colouring === false
      && JSON.stringify(hiddenState.uniform) === JSON.stringify([0, 0, 1]),
      `colouring ${hiddenState.colouring}, uHideLevel ${hiddenState.uniform}`);
    check(`${label}: a hidden level is marked on the control and remembered`,
      hiddenState.marked === true
      && /reconstructed/.test(hiddenState.stored ?? ''),
      `marked ${hiddenState.marked}, stored ${hiddenState.stored}`);

    // The panel says how much of the town each level is, counted from the
    // registry rather than written down — this dataset's own shape, stated
    // before a visitor clicks anything.
    const levelCounts = await page.evaluate(() => {
      const read = (l) => Number(document.getElementById(`cm-count-${l}`)?.textContent || -1);
      return { attested: read('attested'), inferred: read('inferred'),
               reconstructed: read('reconstructed'),
               structures: window.__chicago4d.registry.size };
    });
    check(`${label}: the control counts each level against the loaded town`,
      levelCounts.attested + levelCounts.inferred + levelCounts.reconstructed
        === levelCounts.structures
      && levelCounts.reconstructed > levelCounts.attested,
      JSON.stringify(levelCounts));

    await page.evaluate(() => window.__chicago4d.hud.setHidden('reconstructed', false,
      { announce: false }));
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    // Back on the ground where the rest of the suite expects to be standing.
    await page.evaluate(() => {
      const api = window.__chicago4d;
      api.setFly(false);
      api.walker.teleport({ local_e: 107, local_n: -103, yaw_deg: 180 });
    });
    await page.waitForTimeout(300);


    // --- pick -> provenance ----------------------------------------------
    const picked = await page.evaluate(() => {
      const hit = window.__chicago4d.pick('sauganash_hotel');
      const popup = document.getElementById('popup');
      return {
        ok: !!hit,
        visible: popup && !popup.hasAttribute('hidden'),
        text: popup?.textContent ?? '',
      };
    });
    check(`${label}: pick('sauganash_hotel') opens the popup`, picked.ok && picked.visible,
      `hit ${picked.ok}, visible ${picked.visible}`);
    check(`${label}: popup carries a real citation`,
      /Wau-Bun/.test(picked.text) && /Kinzie, Juliette/.test(picked.text),
      `popup text did not contain the Wau-Bun citation: ${picked.text.slice(0, 160)}`);
    check(`${label}: popup shows per-attribute confidence`,
      /attested/.test(picked.text) && /reconstructed/.test(picked.text),
      picked.text.slice(0, 160));

    // --- and what KIND of source each citation is ---------------------------
    // The card has printed a bare `tier 4` beside a citation since it was
    // written, at a visitor with no table to look it up in, while the panel
    // around it argues that a person can judge the evidence for themselves. The
    // words come off `data/source.schema.json` through the compiled sidecar.
    // Asserted as a pair on ONE card, each label matched to its own citation: the
    // Sauganash cites a period survey, a near-primary recollection and a modern
    // retrospective, so a card stamping one rung on every line — or the right
    // words on the wrong citation — fails where a presence check would pass.
    // `.cites > li` and not `.cites li`: a citation's stated limits are a nested
    // list, and counting their items as citations is how this assertion first
    // reported a card with no rung on it.
    const rungs = await page.evaluate(() => {
      window.__chicago4d.pick('sauganash_hotel');
      return [...document.querySelectorAll('#popup .cites > li')].map((li) => ({
        cite: li.querySelector('.cite-text')?.textContent.trim() ?? '',
        tier: li.querySelector('.tier')?.textContent.trim() ?? '',
      }));
    });
    const rungOf = (re) => rungs.find((r) => re.test(r.cite))?.tier ?? '(no such citation)';
    check(`${label}: every citation says what rung it is on`,
      rungs.length > 0 && rungs.every((r) => /^tier \d+ · \S/.test(r.tier)),
      JSON.stringify(rungs.map((r) => r.tier)));
    check(`${label}: the rung belongs to its own citation`,
      /^tier 2 · near-primary recollection$/.test(rungOf(/Wau-Bun/))
      && /^tier 1 · period\/eyewitness$/.test(rungOf(/Wright/))
      && /^tier 5 · modern retrospective/.test(rungOf(/Kurz/)),
      `Wau-Bun "${rungOf(/Wau-Bun/)}" · Wright "${rungOf(/Wright/)}" · Kurz "${rungOf(/Kurz/)}"`);
    // --- and WHY a citation is on that rung, and what it cannot be used for --
    // A rung is a judgement about a document, and on ten of these records the
    // document is not the page: a visitor following `chicagology_prefire273`
    // arrived at a modern blog stamped "tier 2 · near-primary recollection"
    // with nothing saying it reprints the Chicago Magazine of 15 May 1857. The
    // Sauganash's card carries the discriminating triple, which is why it is
    // asserted here rather than by presence: one citation that reprints a
    // document, one that IS one and reprints nothing (Wright's survey sheet,
    // which instead states what it does not supply), and one that has neither.
    // A card stamping the line on every citation fails on the second; a card
    // showing none fails on the first.
    const evidence = await page.evaluate(() => {
      window.__chicago4d.pick('sauganash_hotel');
      return [...document.querySelectorAll('#popup .cites > li')].map((li) => ({
        cite: li.querySelector('.cite-text')?.textContent.trim() ?? '',
        reprints: [...li.querySelectorAll('.cite-reprints')].map((p) => p.textContent.trim()),
        limits: [...li.querySelectorAll('.cite-lim li')].map((x) => x.textContent.trim()),
      }));
    });
    const ev = (re) => evidence.find((r) => re.test(r.cite)) ?? { reprints: [], limits: [] };
    check(`${label}: a citation says what document it reprints`,
      ev(/Chicagology/).reprints.length === 1
      && /reprints\s+Chicago Magazine/.test(ev(/Chicagology/).reprints[0])
      && /1857-05-15/.test(ev(/Chicagology/).reprints[0]),
      JSON.stringify(ev(/Chicagology/).reprints));
    check(`${label}: a source that IS its document reprints nothing`,
      ev(/Wright/).reprints.length === 0 && ev(/Wau-Bun/).reprints.length === 0,
      `Wright ${JSON.stringify(ev(/Wright/).reprints)} · `
      + `Wau-Bun ${JSON.stringify(ev(/Wau-Bun/).reprints)}`);
    // The limit that reached this project's own brief before anyone opened the
    // scan, and then stayed in the repository: a survey of streets and blocks
    // does not give you a building.
    check(`${label}: a source states what it does not supply`,
      ev(/Wright/).limits.includes('building footprints')
      && ev(/Wau-Bun/).limits.length === 0,
      `Wright ${JSON.stringify(ev(/Wright/).limits)} · `
      + `Wau-Bun ${JSON.stringify(ev(/Wau-Bun/).limits)}`);
    // --- the dossier link, which is a link and not a string ----------------
    // The assertion this replaces tested `picked.text` for the path, and it
    // passed on every run for months while every one of the 332 cards linked to
    // a 404: `publish.sh` leaves `docs/` out of the payload by design, so a
    // path relative to the walkthrough resolved in the source tree and nowhere a
    // visitor stands (ROADMAP K26). The text was right the whole time. So this
    // reads the HREF the card actually offers, and asserts it leaves the site —
    // that is the property, because nothing served from this origin can satisfy
    // it. And the discriminating case beside it: a record whose dossier nobody
    // has written must offer no link at all rather than a plausible one.
    const dossier = await page.evaluate(() => {
      const read = (id) => {
        window.__chicago4d.pick(id);
        const a = [...document.querySelectorAll('#popup a')]
          .find((el) => /docs\/RESEARCH\//.test(el.getAttribute('href') ?? ''));
        return {
          href: a?.href ?? '',
          offSite: !!a && new URL(a.href).origin !== window.location.origin,
          text: document.getElementById('popup')?.textContent ?? '',
        };
      };
      return { linked: read('sauganash_hotel'), unwritten: read('temple_building') };
    });
    check(`${label}: the card's dossier link leaves the payload it is not in`,
      dossier.linked.offSite
      && /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/blob\//.test(dossier.linked.href)
      && dossier.linked.href.endsWith('/chicago/4d/docs/RESEARCH/sauganash_hotel.md'),
      `href ${dossier.linked.href || '(none)'} · offSite ${dossier.linked.offSite}`);
    check(`${label}: a building with no dossier written offers no dossier link`,
      !dossier.unwritten.href && /no dossier written/.test(dossier.unwritten.text),
      `href ${dossier.unwritten.href || '(none)'} · `
      + `${dossier.unwritten.text.slice(-160)}`);

    // Restore the card the assertions after this one are written against.
    await page.evaluate(() => window.__chicago4d.pick('sauganash_hotel'));

    // --- what the chip cannot say: whether you are looking at it -----------
    // A confidence chip grades the evidence. It says nothing about whether the
    // value reached the mesh, and the two come apart in the worst direction — the
    // Wolf Point sign was `documented` on a building that had no sign until the
    // rename and re-bake of 2026-08-10 (LIBERTIES L20). Asserted
    // per-attribute rather than by presence, because a card that marked every row
    // — or the wrong rows — would pass a count.
    const geom = await page.evaluate(() => {
      const read = (id) => {
        window.__chicago4d.pick(id);
        const rows = {};
        for (const tr of document.querySelectorAll('#popup table.attrs tr')) {
          const mark = tr.querySelector('.geom');
          rows[tr.querySelector('th')?.textContent.trim() ?? '?'] =
            mark ? mark.textContent.trim() : null;
        }
        return rows;
      };
      return { western: read('western_hotel'), wolf: read('wolf_point_tavern'),
               greenTree: read('green_tree_tavern') };
    });
    check(`${label}: an attested feature the model omits says so on its row`,
      geom.western.stables === 'not built',
      `stables ${geom.western.stables}`);
    // The case this whole marker exists for, now from the other side. The Wolf
    // Point sign was `documented` on a building with no sign for a day, because
    // the record spelled it `signage` and the archetype reads `sign`. It is built
    // now, so its row must carry NO marker — an assertion that fails both if the
    // rename is reverted and if the marker is ever applied to a built attribute.
    check(`${label}: the documented wolf sign is built and its row is unmarked`,
      geom.wolf.sign === null && geom.wolf['frame addition'] === null,
      `sign ${geom.wolf.sign}, frame addition ${geom.wolf['frame addition']}`);
    check(`${label}: a value a fixed default stands in for is marked differently`,
      geom.western.cladding === 'not modelled from this',
      `cladding ${geom.western.cladding}`);
    // Chimneys were the other half of that marker until 2026-08-10: every record
    // counted its stacks and neither archetype read the number, so Miller's house
    // showed one stack over a record claiming two. The count is a parameter now, so
    // the row carries no marker — on the log building that gained a stack and on the
    // frame building whose pair was already right, which are different reasons to
    // pass and both have to hold.
    check(`${label}: the recorded chimney count is built, so its row is unmarked`,
      geom.wolf.chimneys === null && geom.western.chimneys === null,
      `wolf ${geom.wolf.chimneys}, western ${geom.western.chimneys}`);
    // The discriminating cases. An attribute the archetype builds must carry no
    // marker at all, or the card teaches a visitor to distrust the whole model;
    // and a rejected reading is not a thing missing from the view.
    check(`${label}: an attribute the generator builds carries no marker`,
      geom.western.stories === null && geom.western['roof type'] === null,
      `stories ${geom.western.stories}, roof type ${geom.western['roof type']}`);
    // Until T-0083 `side additions` asserted 'not built' here; the rear one IS
    // built now (form.rear_ell), so the testimony row is marked 'not modelled
    // from this' — the ell attribute drives the mesh, Gray's sentence does not —
    // and the ell's own row, being consumed, must carry no marker at all.
    check(`${label}: a reading recorded but never a build instruction is not marked`,
      geom.greenTree['log core'] === null && geom.greenTree.side_additions === undefined
      && geom.greenTree['side additions'] === 'not modelled from this'
      && geom.greenTree['rear ell'] === null,
      `log core ${geom.greenTree['log core']}, side additions `
      + `${geom.greenTree['side additions']}, rear ell ${geom.greenTree['rear ell']}`);

    // --- the liberties for THIS building, on the card ----------------------
    // The confidence chips answer "how sure are you of this value". They cannot
    // answer "what did you decide without evidence at all", which is what the
    // liberties record. Asserted per-building rather than as a count, because
    // the failure this guards against is the card showing the whole list (or the
    // wrong subset) instead of the ones the markdown attaches to this structure.
    const popLib = await page.evaluate(() => {
      const read = (id) => {
        window.__chicago4d.pick(id);
        const sec = document.querySelector('#popup .pop-liberties');
        return {
          present: !!sec,
          ids: [...document.querySelectorAll('#popup .pop-liberties .lib-id')]
            .map((n) => n.textContent.trim()),
          text: sec?.textContent ?? '',
        };
      };
      return { sauganash: read('sauganash_hotel'), greenTree: read('green_tree_tavern') };
    });
    check(`${label}: the popup carries the liberties taken with this building`,
      popLib.sauganash.present
      && ['L4', 'L4a', 'L5', 'L6', 'L18', 'L217'].every((id) => popLib.sauganash.ids.includes(id)),
      `got [${popLib.sauganash.ids.join(', ')}]`);
    check(`${label}: it shows the reasoning, not just the admission`,
      /invented/i.test(popLib.sauganash.text) && /Why/i.test(popLib.sauganash.text),
      popLib.sauganash.text.slice(0, 200));
    // The discriminating case: a different building, a different set. A popup
    // that dumped the whole list would pass every assertion above.
    check(`${label}: another building gets its own liberties, not the whole list`,
      popLib.greenTree.ids.includes('L9') && popLib.greenTree.ids.includes('L19')
      && !popLib.greenTree.ids.some((id) => ['L4', 'L5', 'L6', 'L1', 'L18'].includes(id)),
      `green tree got [${popLib.greenTree.ids.join(', ')}]`);
    check(`${label}: a scene-wide liberty is not attached to a building`,
      !popLib.sauganash.ids.includes('L1') && !popLib.sauganash.ids.includes('L14'),
      `sauganash got [${popLib.sauganash.ids.join(', ')}]`);

    // Collapsed by default here too — the card must stay skimmable, and a
    // building carrying several liberties would otherwise push the citations off it.
    // T-0712 RESTATED, NOT WEAKENED. The liberties live in the card's "What we
    // made up" PANE, hidden by default behind the Evidence pane. A
    // `checkVisibility()` read of an entry inside a hidden pane is false whether
    // the entry is collapsed or not, so the old read would have passed its first
    // half dishonestly; the pane's tab is clicked first, and the read also holds
    // that the pane itself came into view. The tab is put back to Evidence
    // afterwards — the card remembers the last pane for the session.
    const popLibOpen = await page.evaluate(() => {
      window.__chicago4d.pick('sauganash_hotel');
      document.querySelector('#popup [data-pop-tab="liberties"]').click();
      const pane = document.querySelector('#popup [data-pop-pane="liberties"]');
      const first = document.querySelector('#popup .pop-liberties details.lib');
      const body = first.querySelector('.lib-body');
      const paneShown = !pane.hasAttribute('hidden') && pane.checkVisibility();
      const before = body.checkVisibility();
      first.open = true;
      const after = body.checkVisibility();
      document.querySelector('#popup [data-pop-tab="evidence"]').click();
      return { paneShown, before, after, evidenceBack: !document.querySelector('#popup [data-pop-pane="evidence"]').hasAttribute('hidden') };
    });
    check(`${label}: popup liberties start collapsed on their own pane and open on demand`,
      popLibOpen.paneShown && popLibOpen.before === false && popLibOpen.after === true
      && popLibOpen.evidenceBack,
      `pane shown ${popLibOpen.paneShown}, ${popLibOpen.before} -> ${popLibOpen.after}`);

    // --- the agency held here, on the card --------------------------------
    // T-1041. A HOLDING IS A RELATION, and the card had no place for one: the
    // register has recorded since T-0410 that Hubbard & Co. of La Salle Street was
    // appointed agent for the Howard Fire Insurance Company of New-York, and that
    // three weeks before the scene date the identical notice starts running in the
    // singular over one man. Nothing read it. Pinned on the RENDERED card for the
    // same reason `documented_range` is: a compiled relation nothing renders is
    // exactly the failure this ticket reports, and it is green everywhere else.
    //
    // Three reads, and the second and third are the discriminating ones. A card
    // that printed the whole file would pass the first alone.
    const popAgency = await page.evaluate(() => {
      const read = (id) => {
        window.__chicago4d.pick(id);
        const sec = document.querySelector('#popup .pop-agency');
        return {
          present: !!sec,
          text: sec?.textContent?.replace(/\s+/g, ' ').trim() ?? '',
          refused: !!document.querySelector('#popup .pop-agency .agency-refused'),
          cites: [...document.querySelectorAll('#popup .pop-agency .agency-cites code')]
            .map((n) => n.textContent.trim()),
        };
      };
      return {
        hubbard: read('recon_1835_blk_randolph_wells_d2_07'),
        jonesKing: read('recon_1835_blk_south_water_franklin_d5_01'),
        sauganash: read('sauganash_hotel'),
      };
    });
    check(`${label}: the card names the agency this house held, and its principal`,
      popAgency.hubbard.present
      && /Hubbard & Co\. held the agency for Howard Fire Insurance Company/.test(popAgency.hubbard.text)
      && /city of New-York/.test(popAgency.hubbard.text),
      popAgency.hubbard.text.slice(0, 240));
    // The window is printings and says so, and it is dated in words rather than ISO.
    check(`${label}: it dates the holding by its printings and calls them printings`,
      /printed from 2 July 1834 to 20 May 1835/.test(popAgency.hubbard.text)
      && /first and last PRINTING/.test(popAgency.hubbard.text),
      popAgency.hubbard.text.slice(0, 400));
    // Every other line on this card cites its source; so does this one.
    check(`${label}: the holding cites the printings it rests on`,
      popAgency.hubbard.cites.includes('chicago_democrat_1834_07_02#c048')
      && popAgency.hubbard.cites.length === 3,
      `got [${popAgency.hubbard.cites.join(', ')}]`);
    // THE CAVEAT IS THE ACCEPTANCE CLAUSE. "Nothing on the card implies the holder
    // traded in the principal's line, held a roof for it, or was a partner in any
    // house he signed for." It is written in the compiled file beside the relation,
    // so this pins the rendered text and `compile_agencies.py --check` pins the file.
    check(`${label}: the card says a holding is only a holding`,
      /A holding is a relation and nothing more/.test(popAgency.hubbard.text)
      && /partner in any house that signed for it/.test(popAgency.hubbard.text),
      popAgency.hubbard.text.slice(-260));
    // The REFUSED holding is legible, on the house the reading was made about.
    check(`${label}: a refused holding is on the card of the house it was refused for`,
      popAgency.jonesKing.present && popAgency.jonesKing.refused
      && /Refused:/.test(popAgency.jonesKing.text),
      popAgency.jonesKing.text.slice(0, 240));
    // And the discriminating case: a building holding no agency shows no section.
    check(`${label}: a house that held no agency says nothing about one`,
      !popAgency.sauganash.present,
      `sauganash got "${popAgency.sauganash.text.slice(0, 120)}"`);

    // --- was it here at all? ----------------------------------------------
    // The claim the whole scene rests on, and the last one to reach the card.
    // `popup.js` read `documented_range` from the moment it was written and
    // `compile_scene.py` never emitted it, so the line rendered as nothing on
    // every building, silently, with every gate green — which is why the
    // assertion is written against the RENDERED card rather than the sidecar.
    //
    // Asserted per building and on the discriminating pair, because a card that
    // stamped one confidence on every presence claim would pass a check for
    // "there is a chip". The Sauganash's frame phase is `documented` — Wau-Bun
    // watched it go up and it burned on a recorded date in 1851. Hogan's store is
    // `inferred` and is the weakest presence claim in the dataset: attested to
    // about July 1834 and placed in a scene eleven months later on a continuity
    // argument. Those two must not read the same.
    const presence = await page.evaluate(() => {
      const read = (id) => {
        window.__chicago4d.pick(id);
        const sec = [...document.querySelectorAll('#popup .pop-sec')]
          .find((s) => /Was it here/i.test(s.querySelector('h3')?.textContent ?? ''));
        if (!sec) return null;
        const row = sec.querySelector('table.attrs tr');
        const note = row?.querySelector('[data-note]');
        // T-0711 RESTATED: the phase's own account no longer opens this
        // section — it is the card's LEAD, `#popup .pop-lead.pop-account`, the
        // first sentence a visitor reads. Same text, read where it now stands.
        const lead = document.querySelector('#popup .pop-lead.pop-account');
        return {
          span: row?.querySelector('.val')?.textContent.trim() ?? '',
          conf: row?.querySelector('.conf')?.textContent.trim() ?? '',
          account: lead?.textContent.trim() ?? '',
          composed: lead ? lead.hasAttribute('data-composed') : null,
          noteText: note?.textContent.trim() ?? '',
          noteHidden: note ? note.hasAttribute('hidden') : null,
        };
      };
      // And a record with NO change_note — the fort's powder magazine — gets a
      // lead composed strictly from its fields: its function and its location.
      window.__chicago4d.pick('fort_dearborn_magazine');
      const s = window.__chicago4d.registry.get('fort_dearborn_magazine')?.sidecar ?? {};
      const lead = document.querySelector('#popup .pop-lead.pop-account');
      const composed = {
        hasChangeNote: !!s.change_note,
        composed: lead ? lead.hasAttribute('data-composed') : null,
        text: lead?.textContent.trim() ?? '',
        fn: String(s.attributes?.function?.value ?? '').replace(/_/g, ' '),
        where: String(s.placement?.symbolic_location ?? '').replace(/\.$/, ''),
      };
      return { hogan: read('hogan_store'), saug: read('sauganash_hotel'), composed };
    });
    check(`${label}: the card says whether the building was here on the scene date`,
      presence.hogan?.span === '1831-03-31 → 1835-12-31',
      `span "${presence.hogan?.span}"`);
    check(`${label}: the presence claim is graded per building, not stamped`,
      presence.hogan?.conf === 'inferred' && presence.saug?.conf === 'attested',
      `hogan ${presence.hogan?.conf}, sauganash ${presence.saug?.conf}`);
    // The reasoning is the point: a span with a chip and no argument is what the
    // card already had everywhere else. Hogan's is the one that matters — the end
    // of that range is a continuity argument, not a source.
    check(`${label}: the presence claim carries its reasoning, folded away`,
      presence.hogan?.noteHidden === true
      && /NO SOURCE REACHED FOLLOWS THE BUILDING PAST IT/.test(presence.hogan?.noteText ?? ''),
      `hidden ${presence.hogan?.noteHidden}, note "${(presence.hogan?.noteText ?? '').slice(0, 120)}"`);
    // What no chip can express: this building held the post office for three
    // years and is not the post office on the day you are standing in.
    // Was read inside the "Was it here" section; T-0711 made it the card's lead.
    // The record's words are verbatim (not composed) on both, and each is its own.
    check(`${label}: the phase's own account of itself leads the card`,
      /post office/i.test(presence.hogan?.account ?? '')
      && presence.saug?.account !== presence.hogan?.account
      && presence.hogan?.composed === false && presence.saug?.composed === false,
      `account "${(presence.hogan?.account ?? '').slice(0, 120)}", composed ${presence.hogan?.composed}`);
    // T-0711: a record without a change_note is not left without a first
    // sentence — the lead is composed from its own function and location, and
    // says so with `data-composed`, so nothing composed can pass as recorded.
    check(`${label}: a record without an account gets a lead composed from its function and location, marked as composed`,
      presence.composed.hasChangeNote === false && presence.composed.composed === true
      && presence.composed.fn.length > 3
      && presence.composed.text.toLowerCase().includes(presence.composed.fn.toLowerCase())
      && presence.composed.text.toLowerCase().includes(presence.composed.where.toLowerCase().slice(0, 40)),
      `"${presence.composed.text.slice(0, 160)}" — function "${presence.composed.fn}", `
      + `location "${presence.composed.where.slice(0, 60)}"`);

    // The position's argument, on the line that shows the position. Three of the
    // eight placements are derived from bank geometry because no corner survives;
    // the card showed the conclusion and hid the reasoning behind nothing.
    // T-0712 RESTATED: the position row is a claim row in the "Where did it
    // stand?" section (`.pop-where`) of the Evidence pane — `.pop-meta` is gone.
    // The Evidence tab is activated first so the read is of a shown pane.
    const posWhy = await page.evaluate(() => {
      window.__chicago4d.pick('walker_meeting_house');
      document.querySelector('#popup [data-pop-tab="evidence"]').click();
      const where = document.querySelector('#popup .pop-where');
      const meta = document.querySelector('#popup .pop-where [data-note]');
      const btn = document.querySelector('#popup .pop-where [data-toggle-note]');
      const before = meta?.hasAttribute('hidden');
      btn?.click();
      return { whereShown: !!where && where.checkVisibility(), before,
        after: meta?.hasAttribute('hidden'), shown: meta ? meta.checkVisibility() : null,
        text: meta?.textContent ?? '' };
    });
    check(`${label}: the position's reasoning opens on demand`,
      posWhy.whereShown && posWhy.before === true && posWhy.after === false && posWhy.shown === true
      && posWhy.text.length > 200,
      `where shown ${posWhy.whereShown}, ${posWhy.before} -> ${posWhy.after} (visible ${posWhy.shown}), ${posWhy.text.length} chars`);

    // --- was it this shape? -----------------------------------------------
    // The footprint is the largest claim a visitor is standing in front of and
    // the card said nothing about it at all: `compile_scene.py` carried its
    // confidence and dropped its sources and its argument. Six of the eight
    // outlines here open with the word PLACEHOLDER and two are the opposite, and
    // none of that reached anybody.
    //
    // Asserted on the discriminating pair, as everywhere else on this card, and
    // the pair is the strongest one in the dataset: Hogan's store is the only
    // BUILDING footprint that is evidence — Andreas gives twenty by forty-five
    // feet twice — and the Sauganash's is the placeholder its own note calls the
    // central unresolved question of the record. A card stamping one grade on all
    // eight outlines would pass any check for "there is a chip".
    const shape = await page.evaluate(() => {
      const read = (id) => {
        window.__chicago4d.pick(id);
        const sec = [...document.querySelectorAll('#popup .pop-sec')]
          .find((s) => /Was it this shape/i.test(s.querySelector('h3')?.textContent ?? ''));
        const row = sec?.querySelector('table.attrs tr');
        return {
          present: !!sec,
          conf: row?.querySelector('.conf')?.textContent.trim() ?? '',
          shown: row?.querySelector('[data-note]')?.textContent ?? '',
          recorded: window.__chicago4d.registry.get(id)?.sidecar?.footprint?.note ?? '',
        };
      };
      const pair = { hogan: read('hogan_store'), saug: read('sauganash_hotel') };
      // Every building, because the omission below is a rule and not a property
      // of the two buildings the pair happens to name.
      let valued = [];
      for (const id of window.__chicago4d.registry.keys()) {
        window.__chicago4d.pick(id);
        if (document.querySelector('#popup .pop-shape .val')) valued.push(id);
      }
      return { ...pair, valued };
    });
    check(`${label}: the card says how much of the shape is evidence`,
      shape.hogan.present && shape.saug.present
      && shape.hogan.conf === 'attested' && shape.saug.conf === 'reconstructed',
      `hogan ${shape.hogan.conf}, sauganash ${shape.saug.conf}`);
    check(`${label}: the footprint's reasoning is the record's, verbatim`,
      shape.saug.shown === shape.saug.recorded && shape.saug.recorded.length > 300
      && /PLACEHOLDER/.test(shape.saug.shown)
      && shape.hogan.shown === shape.hogan.recorded
      && shape.hogan.shown !== shape.saug.shown,
      `${shape.saug.shown.length} shown of ${shape.saug.recorded.length} recorded`);
    // A deliberate omission, pinned so that a later slice cannot fill it by
    // accident. The only printable value is the polygon and the only way to print
    // a polygon in a table is to reduce it — a bounding box over Miller's L-plan
    // would be a measurement the record does not make, on the card that exists to
    // admit inventions. The shape is already in front of the visitor at full size.
    check(`${label}: and prints no dimension it would have had to invent`,
      shape.valued.length === 0,
      shape.valued.length ? `value printed on ${shape.valued.join(', ')}` : 'no value cell on any building');

    // The mechanism, rather than a third instance of the same discovery. Both
    // `documented_range` and the footprint were graded in the sidecar and silent
    // on the card, and each was found by somebody reading a file. A claim that
    // carries a confidence and reaches no chip is exactly what a program can see:
    // count the graded claims in the record and count the chips on the claim
    // tables, for every building, and require them to agree. Scoped to the claim
    // tables and the location line — the liberties carry their own chips and are
    // not claims about a recorded value.
    const chipCover = await page.evaluate(() => {
      const out = [];
      for (const id of window.__chicago4d.registry.keys()) {
        const s = window.__chicago4d.registry.get(id)?.sidecar;
        if (!s) continue;
        window.__chicago4d.pick(id);
        let graded = Object.keys(s.attributes ?? {}).length;
        if (s.documented_range?.confidence) graded += 1;
        if (s.placement?.position_confidence) graded += 1;
        if (s.footprint?.confidence) graded += 1;
        const chips = document.querySelectorAll(
          '#popup .pop-meta .conf, #popup .pop-sec table.attrs .conf').length;
        out.push({ id, graded, chips });
      }
      return out;
    });
    const uncovered = chipCover.filter((r) => r.graded !== r.chips);
    // T-0712: the selector above KEEPS ITS MEANING under the new card — `.pop-meta`
    // no longer exists and the position chip is a `table.attrs` row inside
    // `.pop-where`, so the union counts exactly the graded claim rows it always
    // did. Hidden panes are still in the DOM, so a chip count is honest whichever
    // pane is showing.
    check(`${label}: every graded claim in a record reaches the card as a chip`,
      chipCover.length >= 8 && uncovered.length === 0,
      uncovered.length
        ? uncovered.map((r) => `${r.id} ${r.graded} graded / ${r.chips} shown`).join('; ')
        : `${chipCover.length} building(s), ${chipCover.reduce((a, r) => a + r.graded, 0)} claims`);
    // T-0711: the FACTS above the tabs are labels with grade DOTS, never chips —
    // a `.conf` chip in the facts would be a second, competing tally of the
    // claims the chip-coverage gate has just counted. The Sauganash has at least
    // Standing, Use, Built and Roof graded, so three dots is the floor.
    const factDots = await page.evaluate(() => {
      window.__chicago4d.pick('sauganash_hotel');
      const facts = document.querySelector('#popup .pop-facts');
      return {
        facts: !!facts,
        dots: document.querySelectorAll('#popup .pop-facts .fact-dot').length,
        chips: document.querySelectorAll('#popup .pop-facts .conf').length,
        offScale: [...document.querySelectorAll('#popup .fact-dot')].filter((d) =>
          !/\bfact-(attested|inferred|reconstructed)\b/.test(d.className)).length,
        untitled: [...document.querySelectorAll('#popup .fact-dot')].filter((d) =>
          !/(attested|inferred|reconstructed)/.test(d.getAttribute('title') ?? '')).length,
      };
    });
    check(`${label}: the facts carry grade dots, not chips`,
      factDots.facts && factDots.dots >= 3 && factDots.chips === 0 && factDots.offScale === 0
      && factDots.untitled === 0,
      JSON.stringify(factDots));

    // --- and the summary of those chips, which is what a visitor reads first -
    // K23b, owner-reported from a card on the dev preview: *"when you say what we
    // made up, say what we included in the recreation, or what we included in the
    // inferred building, or what we included in the attested building."* Every
    // part of the answer was already on the card — nineteen rows, each with its
    // own chip — and a visitor could read all of it and still not say which parts
    // of the building in front of them are evidence and which are ours.
    //
    // The section is a PARTITION of the claims below it, so the gate is a
    // recount rather than a presence check: take the chips the assertion above
    // has just proved complete, tally them by level, and require the summary's
    // own three numbers to be those numbers. A summary that drifted from the card
    // it summarises would be a worse fault than no summary, because it would be
    // read first. Over the WHOLE registry, for the reason that assertion is:
    // right on the sample and wrong on an anonymous roof is wrong on nearly all
    // of this town.
    const basis = await page.evaluate(() => {
      const flat = (el) => (el?.textContent ?? '').replace(/\s+/g, ' ').trim();
      const rowsOf = () => [...document.querySelectorAll('#popup .pop-basis .basis-row')]
        .map((r) => {
          const m = /(\d+) of (\d+)/.exec(flat(r.querySelector('.basis-count')));
          return {
            level: r.dataset.level ?? '',
            count: m ? Number(m[1]) : -1,
            total: m ? Number(m[2]) : -1,
            gloss: flat(r.querySelector('.basis-gloss')),
            what: flat(r.querySelector('.basis-what')),
            from: flat(r.querySelector('.basis-from')),
            absent: flat(r.querySelector('.basis-absent')),
          };
        });
      // The same selector the chip-coverage gate above uses, deliberately: the
      // card's graded claims are whatever that assertion says they are, and two
      // definitions of "a claim on this card" is how the summary would come to
      // disagree with the card while both gates stayed green.
      const tallyOf = () => {
        const t = { attested: 0, inferred: 0, reconstructed: 0 };
        for (const c of document.querySelectorAll(
          '#popup .pop-meta .conf, #popup .pop-sec table.attrs .conf')) {
          const k = c.textContent.trim();
          if (k in t) t[k] += 1;
        }
        return t;
      };

      const bad = [];
      const keep = {};
      let n = 0;
      for (const id of window.__chicago4d.registry.keys()) {
        window.__chicago4d.pick(id);
        const rows = rowsOf();
        const tally = tallyOf();
        const total = tally.attested + tally.inferred + tally.reconstructed;
        const problems = [];
        if (rows.length !== 3) problems.push(`${rows.length} level rows, not 3`);
        for (const r of rows) {
          if (tally[r.level] === undefined) problems.push(`unknown level "${r.level}"`);
          else if (r.count !== tally[r.level]) {
            problems.push(`${r.level} claims ${r.count}, card shows ${tally[r.level]}`);
          }
          if (r.total !== total) problems.push(`${r.level} of ${r.total}, card shows ${total}`);
          if (!r.what) problems.push(`${r.level} lists nothing at all`);
          if (r.count && !r.from) problems.push(`${r.level} says nothing about where it came from`);
        }
        if (problems.length) bad.push(`${id}: ${problems.join('; ')}`);
        if (['sauganash_hotel', 'recon_1835_south_d3_001', 'western_hotel'].includes(id)) {
          keep[id] = rows;
        }
        n += 1;
      }
      const legend = [...document.querySelectorAll('.legend-list li')].map(flat);
      return {
        bad, n, legend,
        saug: keep.sauganash_hotel ?? [],
        anon: keep.recon_1835_south_d3_001 ?? [],
        western: keep.western_hotel ?? [],
      };
    });
    const row = (rows, level) => rows.find((r) => r.level === level) ?? {};
    check(`${label}: the card's per-level summary is a partition of its own claims`,
      basis.n >= 8 && basis.bad.length === 0 && basis.saug.length === 3 && basis.anon.length === 3,
      basis.bad.length ? basis.bad.slice(0, 4).join(' | ')
        : `${basis.n} building(s) summarised`);
    // The discriminating pair, because a section that printed the same three rows
    // on every card would pass a recount that only ever compared it to itself on
    // a well-documented building. The Sauganash is attested by Wau-Bun; the
    // anonymous roof is a count-unit toward the 665-roof programme and NOTHING
    // about it is attested — which is the single most useful thing this section
    // can tell a visitor, so it is said rather than left as a blank row.
    check(`${label}: and it says what is NOT there, per building rather than stamped`,
      row(basis.saug, 'attested').count > 0
      && row(basis.anon, 'attested').count === 0
      && /Nothing about this building is attested/.test(row(basis.anon, 'attested').what)
      && row(basis.anon, 'reconstructed').count > 0,
      `sauganash attested ${row(basis.saug, 'attested').count}, `
      + `anonymous attested ${row(basis.anon, 'attested').count} `
      + `("${row(basis.anon, 'attested').what.slice(0, 60)}")`);
    // What a citation MEANS changes with the level, and one label over all three
    // would be the category error this card's own history is made of. The
    // anonymous roof cites the reconstruction spec on every attribute: that is
    // what BOUNDED an invention, not where a value came from, and reading it as
    // attribution turns the citation into evidence for a building nobody claims
    // stood there.
    check(`${label}: a source on an invention is named as a bound, not as attribution`,
      /^Bounded by:/.test(row(basis.anon, 'reconstructed').from)
      && /reconstruction_spec/.test(row(basis.anon, 'reconstructed').from)
      && /^From:/.test(row(basis.saug, 'attested').from),
      `invention "${row(basis.anon, 'reconstructed').from.slice(0, 70)}", `
      + `attested "${row(basis.saug, 'attested').from.slice(0, 70)}"`);
    // "Included" is a claim about the VIEW, not only about the evidence, and the
    // two come apart in the direction that does the most damage: the Western
    // Hotel's stables are ATTESTED — the wagon yard is in a pre-fire account —
    // and there is nothing of them in the model. Counting that under "attested"
    // and stopping would be a summary of what we included that named something
    // we did not. The rows below already carry the mark; the summary repeats it
    // rather than averaging it away.
    check(`${label}: and separates what is attested from what is actually built`,
      row(basis.western, 'attested').count > 0
      && /^Not in the model:/.test(row(basis.western, 'attested').absent)
      && /stables/.test(row(basis.western, 'attested').absent)
      && !row(basis.saug, 'attested').absent,
      `western "${row(basis.western, 'attested').absent.slice(0, 60)}", `
      + `sauganash "${row(basis.saug, 'attested').absent}"`);
    // Two surfaces defining `inferred` differently is the drift K23a spent a run
    // cleaning up, and prose has no shared renderer to hold it — so the card's
    // gloss is required to be the Evidence panel's own words, literally.
    const glossDrift = ['attested', 'inferred', 'reconstructed'].filter((lvl) => {
      const g = row(basis.saug, lvl).gloss;
      return !g || !basis.legend.some((li) => li.includes(g));
    });
    check(`${label}: the summary defines each level in the Evidence panel's own words`,
      basis.legend.length >= 3 && glossDrift.length === 0,
      glossDrift.length
        ? `${glossDrift.join(', ')} not found in the legend`
        : `3 glosses matched against ${basis.legend.length} legend entries`);

    // Is the shape a bake from the record, or a stand-in?  The established
    // Sauganash asset must remain a real bake while the anonymous phase-one
    // roofs must say both that their mesh is provisional and that their
    // per-parcel placement is a reconstruction rather than a recovered parcel.
    const placeholder = await page.evaluate(() => {
      window.__chicago4d.pick('sauganash_hotel');
      const realFlags = [...document.querySelectorAll('#popup .pop-flag')]
        .map((f) => f.textContent);
      window.__chicago4d.pick('recon_1835_south_d3_001');
      const recommendedFlags = [...document.querySelectorAll('#popup .pop-flag')]
        .map((f) => f.textContent);
      return {
        real: window.__chicago4d.registry.get('sauganash_hotel')?.assetIsPlaceholder,
        realFlag: realFlags.some((t) => /placeholder massing/i.test(t)),
        recommended: window.__chicago4d.registry.get('recon_1835_south_d3_001')
          ?.assetIsPlaceholder,
        placeholderFlag: recommendedFlags.some((t) => /placeholder massing/i.test(t)),
        // THE THIRD TIME this literal has rotted. It tested `recommended` until
        // the merge of 2026-08-13, then `inferred reconstruction` until K23a —
        // and each rename broke it, because it pinned the WORDING rather than
        // the thing the assertion is actually about. What it has always asked is
        // that the card still says this roof is not a recovered building, in the
        // grade the record itself carries. So it asks that now, off the record,
        // and the next rename of the vocabulary cannot break it.
        grade: window.__chicago4d.registry.get('recon_1835_south_d3_001')
          ?.sidecar?.documented_range?.confidence,
        reconstructionFlag: recommendedFlags.some(
          (t) => /anonymous/i.test(t) && /not an attested named building/i.test(t)),
        flagNamesTheGrade: recommendedFlags.some((t) => new RegExp(
          window.__chicago4d.registry.get('recon_1835_south_d3_001')
            ?.sidecar?.documented_range?.confidence ?? 'x', 'i').test(t)),
      };
    });
    check(`${label}: established assets remain identified as real bakes`,
      placeholder.real === false && placeholder.realFlag === false,
      JSON.stringify(placeholder));
    // Two claims that were tangled into one, and came apart the first time a
    // canonical bake actually reached these roofs. "This building is anonymous
    // inferred infill" is a fact about the RECORD and is permanent. "Its mesh is
    // review massing" is a fact about the ASSET and stops being true the moment
    // generators/build.py bakes it properly. Asserting them together meant the
    // honest upgrade read as a regression.
    check(`${label}: anonymous infill is visibly flagged as a reconstruction`,
      placeholder.reconstructionFlag === true,
      JSON.stringify(placeholder));
    check(`${label}: that flag names the grade the record itself carries`,
      placeholder.flagNamesTheGrade === true && placeholder.grade === 'reconstructed',
      JSON.stringify(placeholder));
    // Both directions, which the single assertion never checked: placeholder
    // massing is claimed when the asset IS one, and — the half that was missing —
    // never claimed when it is not. A real bake wearing a placeholder label is a
    // lie in the opposite direction, and would previously have passed.
    check(`${label}: the placeholder label agrees with the asset it describes`,
      placeholder.placeholderFlag === (placeholder.recommended === true),
      JSON.stringify(placeholder));

    // --- the standing constraint, on the card ------------------------------
    // T-0268. Nine records are held under AGENTS.md's standing constraint, and the
    // flag used to reach a browser exactly once, as a console line about the scene.
    //
    // This is asserted over EVERY flagged record rather than one sampled id, because
    // the set is the thing: `measure_review_constraint.py` decides which buildings
    // are held and the card must not disagree with it about a single one. The two
    // ends of that agreement are gated in different places and both are needed — the
    // census re-derives `review_reason` against the committed sidecars, and this
    // asks the rendered DOM whether a visitor is actually handed it.
    //
    // The control is the other half. A held notice on a building that is not held
    // would be a worse fault than a missing one: it would put a consultation claim
    // on a record nobody made it for.
    const held = await page.evaluate(() => {
      const read = (id) => {
        window.__chicago4d.pick(id);
        const flag = document.querySelector('#popup .pop-flag-held');
        return {
          id,
          notice: !!flag && /held pending consultation/i.test(flag.textContent),
          why: flag?.querySelector('.pop-held-why')?.textContent?.trim() ?? '',
          recorded: window.__chicago4d.registry.get(id)?.sidecar?.review_reason ?? '',
          // Folded sections are not an answer to "without unfolding anything":
          // the reason lived inside a 400-word note behind a disclosure before
          // this, and that is the state the ticket was opened about.
          openable: !!flag?.closest('details'),
        };
      };
      const flagged = [...window.__chicago4d.registry.values()]
        .filter((r) => r.sidecar?.review_required)
        .map((r) => r.sidecar.id)
        .sort();
      const control = [...window.__chicago4d.registry.values()]
        .find((r) => r.sidecar && !r.sidecar.review_required)?.sidecar?.id;
      return { flagged: flagged.map(read), control: control ? read(control) : null };
    });
    check(`${label}: every held building says so on its card`,
      held.flagged.length > 0 && held.flagged.every((h) => h.notice && !h.openable),
      `${held.flagged.filter((h) => !h.notice || h.openable).map((h) => h.id).join(', ')
       || `${held.flagged.length} flagged`}`);
    // Verbatim, and for the same reason the account below is: this is the record's
    // sentence, not a gloss of it, and a renderer that trimmed it to a first clause
    // would pass any substring check written here.
    const whyDrift = held.flagged.filter((h) => !h.recorded || h.why !== h.recorded);
    check(`${label}: and says what it is held for, in the record's own words`,
      held.flagged.length > 0 && whyDrift.length === 0,
      whyDrift.map((h) => `${h.id}: shown ${JSON.stringify(h.why.slice(0, 40))}`
        + ` vs recorded ${JSON.stringify(h.recorded.slice(0, 40))}`).join(' | '));
    check(`${label}: and a building that is not held does not claim to be`,
      held.control !== null && held.control.notice === false,
      JSON.stringify(held.control));

    // --- the record's own account -----------------------------------------
    // `research_note` is on every record and in every compiled sidecar, and the
    // sidecar-contract gate reported it as compiled-and-never-read: an unshipped
    // claim rather than dead weight. It is the paragraph that says which of two
    // sources was believed, or that the likeliest reading of the evidence is that
    // the record models the wrong building. Nothing was broken — the field simply
    // had no surface — so unlike the two faults before it, this is asserted
    // against what a visitor reads for the first time here.
    //
    // The assertion that matters is VERBATIM, and it is deliberately an exact
    // string comparison against the sidecar rather than a substring match. A note
    // about the limit of the evidence is the last text on this card that should be
    // trimmed or summarised, and a renderer that showed a first sentence and an
    // ellipsis would pass every looser check written here.
    const account = await page.evaluate(() => {
      const read = (id) => {
        window.__chicago4d.pick(id);
        const sec = [...document.querySelectorAll('#popup .pop-sec')]
          .find((s) => /own account/i.test(s.querySelector('h3')?.textContent ?? ''));
        const body = sec?.querySelector('.research-body');
        return {
          present: !!sec,
          shown: body?.textContent ?? '',
          recorded: window.__chicago4d.registry.get(id)?.sidecar?.research_note ?? '',
        };
      };
      return { hogan: read('hogan_store'), saug: read('sauganash_hotel') };
    });
    check(`${label}: the record's own account reaches the card`,
      account.hogan.present && /THE BUILDING WHERE CHICAGO'S MAIL BEGAN/.test(account.hogan.shown),
      `present ${account.hogan.present}, "${account.hogan.shown.slice(0, 90)}"`);
    check(`${label}: it is the record's words, unabridged`,
      account.hogan.shown === account.hogan.recorded && account.hogan.recorded.length > 500,
      `${account.hogan.shown.length} chars shown of ${account.hogan.recorded.length} recorded`);
    // The discriminating case, as everywhere else on this card: a second building
    // gets its own account. A section rendering one fixed block of prose — or the
    // scene's, or the previous pick's — would pass both checks above.
    check(`${label}: another building gets its own account, not this one's`,
      account.saug.shown === account.saug.recorded
      && account.saug.shown !== account.hogan.shown
      && /MILESTONE 0 REFERENCE RECORD/.test(account.saug.shown),
      `sauganash "${account.saug.shown.slice(0, 90)}"`);

    // --- who was here -------------------------------------------------------
    // `data/residents/` draws nobody by design, so the ONLY place a visitor can
    // meet the town's people is this card. Before it existed the layer stopped at
    // the repo — the failure mode that looks identical, from the street, to the
    // work never having been done. The discriminating half is the third check: a
    // building whose household is there for a REASON has to say what the reason
    // is, or the card reads as bare evidence that somebody lived here.
    //
    // T-0524: that third read was `inf_cooperage_south` — a roof the inferred-
    // household programme had raised, whose section had to carry
    // "BECAUSE OF THIS HOUSEHOLD" over `grade-reconstructed` people. T-0489
    // retired that programme and emptied `residents` on all 31 `inferred_household`
    // roofs, so the section is not rendered on any of them and the assertion had no
    // subject; the string it looked for is in no record in the tree any more.
    // The claim it was making — the card states the BASIS on which this household
    // is attached to this building — survives on the five records that still carry
    // one, so it is read there. T-0516 is the open ticket that decides what those
    // 31 roofs now say; when a roof carries a household again, the reconstructed
    // half of this check belongs back here alongside the documented half.
    const who = await page.evaluate(() => {
      const read = (id) => {
        window.__chicago4d.pick(id);
        const sec = [...document.querySelectorAll('#popup .pop-sec')]
          .find((x) => /who was here/i.test(x.querySelector('h3')?.textContent ?? ''));
        return {
          present: !!sec,
          text: sec?.textContent ?? '',
          grades: [...(sec?.querySelectorAll('.grade') ?? [])].map((g) => g.className),
          basis: sec?.querySelector('.res-basis')?.textContent ?? '',
          recorded: window.__chicago4d.registry.get(id)?.sidecar?.residents ?? [],
        };
      };
      return {
        brown: read('brown_boarding_house'),
        basis: read('harmon_log_cabin'),
        none: read('log_jail'),
      };
    });
    check(`${label}: a building names the household the sources put in it`,
      who.brown.present && /Mrs Rufus Brown/.test(who.brown.text)
      && who.brown.grades.some((c) => c.includes('grade-attested')),
      `present ${who.brown.present}, grades ${who.brown.grades.join('|')}`);
    check(`${label}: a person's grade is shown, and it is not a confidence chip`,
      who.brown.grades.some((c) => c.includes('grade-inferred'))
      && !who.brown.grades.some((c) => c.includes('conf-')),
      who.brown.grades.join('|'));
    check(`${label}: a building's household says on the card why it is attached there`,
      who.basis.present && who.basis.grades.length > 0
      && who.basis.grades.every((c) => /\bgrade-(attested|inferred|reconstructed)\b/.test(c))
      && !who.basis.grades.some((c) => c.includes('conf-'))
      && /the household is the one the sources attach to it/.test(who.basis.basis)
      && who.basis.text !== who.brown.text,
      `basis "${who.basis.basis.slice(0, 80)}", grades ${who.basis.grades.join('|')}`);
    check(`${label}: a building with no household gets no section at all`,
      !who.none.present && who.none.recorded.length === 0,
      `present ${who.none.present}`);

    // Collapsed by default, for the same reason the liberties are: these run to
    // several hundred words, and on a phone the panel is 62vh — an open account
    // would push the citations off the card entirely.
    // T-0712 RESTATED, NOT WEAKENED: the research account lives in the Record
    // pane, hidden by default. Its tab is clicked first so the collapsed read is
    // of a shown pane (a hidden pane reads false either way), and Evidence is
    // put back afterwards.
    const accountOpen = await page.evaluate(() => {
      window.__chicago4d.pick('hogan_store');
      document.querySelector('#popup [data-pop-tab="record"]').click();
      const pane = document.querySelector('#popup [data-pop-pane="record"]');
      const d = document.querySelector('#popup .pop-research details.research');
      const body = d.querySelector('.research-body');
      const paneShown = !pane.hasAttribute('hidden') && pane.checkVisibility();
      const before = body.checkVisibility();
      d.open = true;
      const after = body.checkVisibility();
      document.querySelector('#popup [data-pop-tab="evidence"]').click();
      return { paneShown, before, after };
    });
    check(`${label}: the account starts collapsed on the Record pane and opens on demand`,
      accountOpen.paneShown && accountOpen.before === false && accountOpen.after === true,
      `pane shown ${accountOpen.paneShown}, ${accountOpen.before} -> ${accountOpen.after}`);

    // --- the card's order and its panes (T-0711, T-0712) ---------------------
    // The card reads top-down as a museum label: head, the lead sentence, the
    // facts, the households when there are any, then the tab strip and one pane
    // showing. The three sections that moved under tabs are asserted to be in
    // the pane NAMED for them — a heading rendered in the wrong pane would be
    // reachable and still wrong. Hogan's is the record with households and the
    // Standing row's year comes from its sidecar (`documented_range.from`
    // 1831-03-31), not a literal about the card.
    const cardShape = await page.evaluate(() => {
      const api = window.__chicago4d;
      const order = (sel) => {
        const els = sel.map((s) => document.querySelector(`#popup ${s}`));
        const missing = sel.filter((s, i) => !els[i]);
        let ordered = true;
        for (let i = 1; i < els.length; i++) {
          if (els[i - 1] && els[i]
            && !(els[i - 1].compareDocumentPosition(els[i]) & Node.DOCUMENT_POSITION_FOLLOWING)) ordered = false;
        }
        return { missing, ordered };
      };
      // A heading's OWN words: the liberties h3 carries a `.pop-count` badge
      // ("What we made up here 6"), which is not part of its name.
      const ownText = (h) => [...h.childNodes].filter((n) => n.nodeType === Node.TEXT_NODE)
        .map((n) => n.textContent).join('').trim();
      const paneOf = (h3text) => {
        const h3 = [...document.querySelectorAll('#popup .pop-pane h3')]
          .find((h) => ownText(h) === h3text);
        return h3?.closest('.pop-pane')?.dataset.popPane ?? null;
      };
      document.querySelector('#popup [data-pop-tab="evidence"]')?.click();
      api.pick('sauganash_hotel');
      const saug = {
        order: order(['.pop-head', '.pop-lead', '.pop-facts', '.pop-tabs', '.pop-pane']),
        residents: !!document.querySelector('#popup .pop-residents'),
        evidenceShown: (() => { const p = document.querySelector('#popup [data-pop-pane="evidence"]');
          return !!p && !p.hasAttribute('hidden') && p.checkVisibility(); })(),
        hiddenPanes: [...document.querySelectorAll('#popup .pop-pane[hidden]')].map((p) => p.dataset.popPane).sort(),
        tabs: [...document.querySelectorAll('#popup .pop-tab')].map((t) => t.dataset.popTab),
        homes: { where: paneOf('Where did it stand?'), liberties: paneOf('What we made up here'),
          record: paneOf("The record's own account") },
      };
      api.pick('hogan_store');
      const from = api.registry.get('hogan_store')?.sidecar?.documented_range?.from ?? '';
      const facts = [...document.querySelectorAll('#popup .pop-facts .fact')]
        .map((f) => `${f.querySelector('dt')?.textContent.trim()}: ${f.querySelector('dd')?.textContent.trim()}`);
      const hogan = {
        order: order(['.pop-head', '.pop-lead', '.pop-facts', '.pop-residents', '.pop-tabs', '.pop-pane']),
        residents: !!document.querySelector('#popup .pop-residents'),
        year: from.slice(0, 4),
        standing: facts.find((f) => /^Standing:/.test(f)) ?? '',
        facts,
      };
      api.popup.close();
      return { saug, hogan };
    });
    check(`${label}: the card reads head, lead, facts, tabs, pane — in that order`,
      cardShape.saug.order.ordered && !cardShape.saug.order.missing.length && !cardShape.saug.residents
      && cardShape.hogan.order.ordered && !cardShape.hogan.order.missing.length && cardShape.hogan.residents,
      `sauganash missing [${cardShape.saug.order.missing.join(', ')}] ordered ${cardShape.saug.order.ordered}; `
      + `hogan (with households) missing [${cardShape.hogan.order.missing.join(', ')}] ordered ${cardShape.hogan.order.ordered}`);
    check(`${label}: the card opens on its Evidence pane with the other two folded`,
      cardShape.saug.evidenceShown && cardShape.saug.hiddenPanes.join(',') === 'liberties,record'
      && cardShape.saug.tabs.join(',') === 'evidence,liberties,record',
      JSON.stringify({ evidenceShown: cardShape.saug.evidenceShown, hidden: cardShape.saug.hiddenPanes, tabs: cardShape.saug.tabs }));
    check(`${label}: each moved section lives in the pane named for it`,
      cardShape.saug.homes.where === 'evidence' && cardShape.saug.homes.liberties === 'liberties'
      && cardShape.saug.homes.record === 'record',
      JSON.stringify(cardShape.saug.homes));
    check(`${label}: Hogan's facts say it was standing, from the year its record gives`,
      cardShape.hogan.year === '1831' && /^Standing: 1831\b/.test(cardShape.hogan.standing)
      && cardShape.hogan.facts.length >= 3,
      `"${cardShape.hogan.standing}" from ${cardShape.hogan.year}; ${cardShape.hogan.facts.join(' | ').slice(0, 200)}`);

    inStageWork = false;
    } // end PART 3 (T-0060 stage 2a, cut by T-0121)
    // PART 4 — the raycast pick through the confidence menu's own clicks:
    // walking, the bridge deck, the budgets, life size, scene detail and the
    // chrome. The rest of T-0060's stage 2.
    //
    // The one thing this cut inherits is a POSE. Everything above it framed the
    // Sauganash to open its card, and the first check below picks whatever is
    // down the crosshair and requires it to be that building. So the frame is
    // re-taken here rather than assumed: in an unfiltered run it is the pose the
    // camera is already in, and in a part-4 run it is the difference between
    // measuring the Sauganash and measuring the prairie.
    if (stageOn(4)) {
    inStageWork = true;
    await page.evaluate(() => window.__chicago4d.frame('sauganash_hotel', 26));

    // --- a raycast pick down the crosshair, not just by id ----------------
    const rayPick = await page.evaluate(() => {
      const hit = window.__chicago4d.pick();
      return hit ? hit.id : null;
    });
    check(`${label}: raycast down the crosshair resolves a structure_id`,
      rayPick === 'sauganash_hotel', `got ${rayPick}`);

    await page.evaluate(() => window.__chicago4d.popup.close());

    // --- walking ----------------------------------------------------------
    const before = await page.evaluate(() => ({ ...window.__chicago4d.player }));
    // Software rasterisation runs this scene at a handful of frames a second,
    // so give the walk a wall-clock window that survives it.
    await page.keyboard.down('KeyW');
    await page.waitForTimeout(2200);
    await page.keyboard.up('KeyW');
    const after = await page.evaluate(() => ({ ...window.__chicago4d.player }));
    const moved = Math.hypot(after.e - before.e, after.n - before.n);
    check(`${label}: walk intent moves the camera`, moved > 0.3,
      `moved ${moved.toFixed(2)} m in 2.2 s (backend `
      + `${await page.evaluate(() => window.__chicago4d.controlBackend)})`);

    // Walking used to ease the eye toward the sampled ground. On a bank that
    // put the camera below the visible mesh uphill and left it floating
    // downhill, even though both are driven by the same heightfield. Disturb
    // the eye deliberately, then traverse the resolved slope in both directions:
    // every update must restore exact standing clearance, not approach it.
    const terrainLock = await page.evaluate(() => {
      const a = window.__chicago4d;
      const run = (n, bearing) => {
        a.walker.teleport({ local_e: 140, local_n: n, yaw_deg: bearing });
        a.walker.state.eyeY += 0.9;
        let worst = 0;
        let minGround = Infinity;
        let maxGround = -Infinity;
        a.intent.forward = 1;
        for (let i = 0; i < 520; i++) {
          a.walker.update(0.05, a.intent);
          const s = a.walker.state;
          const ground = a.terrain.walkHeight(s.e, s.n);
          minGround = Math.min(minGround, ground);
          maxGround = Math.max(maxGround, ground);
          worst = Math.max(worst, Math.abs(s.eyeY - ground - a.walkBudget.eyeHeight));
        }
        a.intent.forward = 0;
        return { worst, relief: maxGround - minGround };
      };
      return { uphill: run(-20, 180), downhill: run(-58, 0) };
    });
    check(`${label}: walking stays exactly on the terrain through rises and falls`,
      terrainLock.uphill.worst < 1e-6 && terrainLock.downhill.worst < 1e-6
      && terrainLock.uphill.relief > 0.25 && terrainLock.downhill.relief > 0.25,
      JSON.stringify(terrainLock));

    // --- you cannot stand inside a building --------------------------------
    const pushed = await page.evaluate(() => {
      const a = window.__chicago4d;
      const fp = a.footprints.find((f) => f.id === 'sauganash_hotel');
      if (!fp) return { skipped: true };
      const cx = fp.pts.reduce((s, p) => s + p[0], 0) / fp.pts.length;
      const cn = fp.pts.reduce((s, p) => s + p[1], 0) / fp.pts.length;
      a.walker.teleport({ local_e: cx, local_n: cn });
      a.step();
      const { e, n } = a.player;
      // ray-cast point-in-polygon, same test the walker uses
      let hit = false;
      const pts = fp.pts;
      for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
        const [xi, yi] = pts[i];
        const [xj, yj] = pts[j];
        if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
      }
      return { inside: hit, e, n, cx, cn };
    });
    check(`${label}: the walker is pushed out of a building footprint`,
      pushed.skipped || pushed.inside === false,
      `dropped at (${pushed.cx}, ${pushed.cn}), ended at (${pushed.e?.toFixed(2)}, ${pushed.n?.toFixed(2)})`);

    // --- and you CAN stand on a bridge deck (T-0001) -----------------------
    //
    // The owner's question was "how would a wagon cross that?", and the first
    // half of the answer is that a person cannot: the walker followed the
    // heightfield, which over the river reports a wading barrier at 4.0 m, so a
    // visitor set down on the North Branch bridge hovered 1.8 m above its planks
    // and walked across thin air. This drives the crossing and asserts the DECK
    // is under the boot for the whole span.
    //
    // Written as an exact equality rather than a tolerance, and that is the point
    // of it: `placement.walk_surface_m` is the same `deck_height_m` the mesh was
    // built from, so the number the walker stands on and the number the deck was
    // drawn at are one value. A tolerance here would pass a renderer that had
    // quietly grown a second definition, which is the fault docs/GLB-CONTRACT.md
    // exists to prevent.
    const crossing = await page.evaluate(() => {
      const a = window.__chicago4d;
      const deck = a.decks?.find((d) => d.id === 'north_branch_bridge');
      if (!deck) return { missing: true };
      const es = deck.pts.map((p) => p[0]);
      const ns = deck.pts.map((p) => p[1]);
      const west = Math.min(...es);
      const east = Math.max(...es);
      const mid = (Math.min(...ns) + Math.max(...ns)) / 2;
      const on = (e, n) => {
        let hit = false;
        const pts = deck.pts;
        for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
          const [xi, yi] = pts[i];
          const [xj, yj] = pts[j];
          if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
        }
        return hit;
      };

      // Start half a metre inside the west end, facing east down the deck.
      a.walker.teleport({ local_e: west + 0.5, local_n: mid, yaw_deg: 90 });
      const startedOn = a.walker.state.groundY;
      let offDeck = 0;              // samples on the deck at the wrong height
      let clearance = 0;            // worst eye-height error, on the deck
      let firstE = null;
      let lastE = null;
      let leftE = null;             // where the walker ended up after the far end
      a.intent.forward = 1;
      a.intent.sprint = true;
      for (let i = 0; i < 800; i += 1) {
        a.walker.update(0.05, a.intent);
        const s = a.walker.state;
        if (on(s.e, s.n)) {
          if (firstE === null) firstE = s.e;
          lastE = s.e;
          if (s.groundY !== deck.y) offDeck += 1;
          clearance = Math.max(clearance, Math.abs(s.eyeY - s.groundY - a.walkBudget.eyeHeight));
        } else if (lastE !== null && leftE === null) {
          leftE = s.e;
        }
      }
      a.intent.forward = 0;
      a.intent.sprint = false;
      const endState = { ...a.walker.state };
      return {
        deckY: deck.y,
        span: east - west,
        startedOn,
        walked: firstE === null ? 0 : lastE - firstE,
        offDeck,
        clearance,
        leftE,
        // What the terrain alone would have said mid-span — the barrier this
        // replaces. If this ever stops being well above the deck the assertion
        // below has stopped proving anything.
        barrier: a.terrain.walkHeight((west + east) / 2, mid),
        endGroundY: endState.groundY,
        endE: endState.e,
      };
    });
    check(`${label}: the North Branch bridge has a walkable deck`,
      !crossing.missing && crossing.deckY > 0,
      crossing.missing ? 'no deck compiled for north_branch_bridge'
        : `deck at ${crossing.deckY} m over the datum`);
    check(`${label}: the walker crosses the bridge end to end on its deck`,
      !crossing.missing
      && crossing.walked >= crossing.span - 2
      && crossing.offDeck === 0
      && crossing.clearance < 1e-9,
      `walked ${crossing.walked?.toFixed(1)} m of a ${crossing.span?.toFixed(1)} m deck, `
      + `${crossing.offDeck} sample(s) not at deck height, worst standing clearance error `
      + `${crossing.clearance?.toExponential(1)} m`);
    check(`${label}: the deck, not the wading barrier, is what holds the walker up`,
      !crossing.missing && crossing.barrier > crossing.deckY + 1
      && crossing.startedOn === crossing.deckY,
      `barrier ${crossing.barrier?.toFixed(2)} m vs deck ${crossing.deckY} m, `
      + `stood at ${crossing.startedOn?.toFixed(2)} m`);
    check(`${label}: and walks off the far end onto the bank`,
      !crossing.missing && crossing.leftE !== null
      && crossing.endGroundY < crossing.deckY,
      `left the deck at E ${crossing.leftE?.toFixed(1)}, `
      + `ended standing on ${crossing.endGroundY?.toFixed(2)} m at E ${crossing.endE?.toFixed(1)}`);

    // --- and walks ONTO the deck from the bank (T-0046) ---------------------
    //
    // The other half of the owner's "how would a wagon cross that?": for a year
    // the decks were walkable and unreachable — they stood 2.22 m over banks the
    // terrain put at zero, and the 0.35 m step-up rule refused the deck end the
    // way it refuses a wall. The approach earthworks grade the ground itself up
    // to each deck, so this starts a walker on the plain EAST of the North
    // Branch bridge, well below deck height, walks them west up Kinzie Street,
    // and requires that they end standing ON the planks — no teleport onto the
    // deck, no ramp object, just terrain rising at a wagon grade. If the ground
    // under the climb ever exceeds the step-up rule per stride, the walker
    // simply stops and this fails.
    const ascent = await page.evaluate(() => {
      const a = window.__chicago4d;
      const deck = a.decks?.find((d) => d.id === 'north_branch_bridge');
      if (!deck) return { missing: true };
      const es = deck.pts.map((p) => p[0]);
      const ns = deck.pts.map((p) => p[1]);
      const east = Math.max(...es);
      const mid = (Math.min(...ns) + Math.max(...ns)) / 2;
      const on = (e, n) => {
        let hit = false;
        const pts = deck.pts;
        for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
          const [xi, yi] = pts[i];
          const [xj, yj] = pts[j];
          if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
        }
        return hit;
      };
      // 18 m out: past the toe of the 1-in-12 ramp's upper half, on ground well
      // below the deck, so the climb is real and not a courtesy hop.
      a.walker.teleport({ local_e: east + 18, local_n: mid, yaw_deg: 270 });
      a.step();
      const startGround = a.walker.state.groundY;
      let onDeck = false;
      let worstStride = 0;
      let prevY = startGround;
      a.intent.forward = 1;
      for (let i = 0; i < 600 && !onDeck; i += 1) {
        a.walker.update(0.05, a.intent);
        const s = a.walker.state;
        worstStride = Math.max(worstStride, s.groundY - prevY);
        prevY = s.groundY;
        if (on(s.e, s.n) && s.groundY === deck.y) onDeck = true;
      }
      a.intent.forward = 0;
      return {
        deckY: deck.y,
        startGround,
        climbed: deck.y - startGround,
        onDeck,
        worstStride,
        endE: a.walker.state.e,
      };
    });
    check(`${label}: a walker on the bank climbs the approach onto the deck`,
      !ascent.missing && ascent.onDeck
      && ascent.startGround < ascent.deckY - 0.8,
      ascent.missing ? 'no deck compiled for north_branch_bridge'
        : `started on ${ascent.startGround?.toFixed(2)} m, climbed `
          + `${ascent.climbed?.toFixed(2)} m to the planks at ${ascent.deckY} m, `
          + `worst single stride +${ascent.worstStride?.toFixed(3)} m`
          + (ascent.onDeck ? '' : ` — never reached the deck (stopped at E ${ascent.endE?.toFixed(1)})`));

    await page.evaluate(() => window.__chicago4d.frame('sauganash_hotel', 26));

    // --- the touch backend, on the mobile pass only ------------------------
    if (touch) {
      const stick = await page.evaluate(async () => {
        const api = window.__chicago4d;
        const c = document.getElementById('view');
        const r = c.getBoundingClientRect();
        const send = (type, x, y, id = 7) => c.dispatchEvent(new PointerEvent(type, {
          pointerId: id, pointerType: 'touch', isPrimary: true, bubbles: true, cancelable: true,
          clientX: r.left + x, clientY: r.top + y,
        }));
        // Left half: push the thumbstick forward.
        send('pointerdown', r.width * 0.25, r.height * 0.75);
        await new Promise((res) => requestAnimationFrame(res));
        send('pointermove', r.width * 0.25, r.height * 0.75 - 60);
        await new Promise((res) => setTimeout(res, 60));
        const forward = api.intent.forward;
        const backend = api.controlBackend;
        send('pointerup', r.width * 0.25, r.height * 0.75 - 60);
        return { forward, backend, stickVisible: !!document.getElementById('stick')?.classList.contains('on') };
      });
      check(`${label}: touch activates the touch backend`, stick.backend === 'touch', stick.backend);
      check(`${label}: thumbstick writes forward intent`, stick.forward > 0.5,
        `intent.forward = ${stick.forward}`);

      // Right-half drag must turn the view and nothing else.
      const look = await page.evaluate(async () => {
        const api = window.__chicago4d;
        const c = document.getElementById('view');
        const r = c.getBoundingClientRect();
        const b0 = api.player.bearingDeg;
        const send = (type, x, y, id = 9) => c.dispatchEvent(new PointerEvent(type, {
          pointerId: id, pointerType: 'touch', isPrimary: true, bubbles: true, cancelable: true,
          clientX: r.left + x, clientY: r.top + y,
        }));
        send('pointerdown', r.width * 0.75, r.height * 0.4);
        for (let i = 1; i <= 6; i++) {
          send('pointermove', r.width * 0.75 - i * 12, r.height * 0.4);
          await new Promise((res) => requestAnimationFrame(res));
        }
        send('pointerup', r.width * 0.75 - 72, r.height * 0.4);
        await new Promise((res) => setTimeout(res, 80));
        return { turned: Math.abs(((api.player.bearingDeg - b0 + 540) % 360) - 180) };
      });
      check(`${label}: right-half drag turns the view`, look.turned > 1,
        `turned ${(180 - look.turned).toFixed(1)}°`);
    }

    // --- budgets ------------------------------------------------------------
    //
    // THE BUDGET IS NO LONGER GATED HERE. It is gated at a NAMED SET of stands
    // and on the WORST of them, in the scene-detail block below, which is the
    // one place the whole set can be walked at every tier for the price of
    // walking it once (T-0135; `STANDS` at the top of this file is the set, with
    // each stand's reason written beside it).
    //
    // What stays here is the reference reading — the Sauganash at 26 m, the
    // single camera this project measured itself at until 2026-08-22 — kept so
    // every figure ever recorded in `main.js`, LIBERTIES and the roadmap boxes
    // stays comparable, and kept LABELLED as a reference rather than as a gate so
    // nobody reads it as one again. The two assertions below are still hard: a
    // scene that regressed at the friendly stand has regressed everywhere.
    //
    // THE DRAW-CALL CEILING IS 140 SINCE 2026-08-21, raised from 80 in three
    // steps that afternoon — a conscious re-budget on the owner's ruling (*"or
    // just raise the budget?"*), argued in full where the number is set,
    // `main.js` BUDGET. The short of it: 80 was set when every derived layer was
    // one town-spanning mesh, and T-0067, T-0119 and T-0069 have since chunked
    // those layers so the frustum can cull them, which trades triangles for draw
    // calls on purpose — and the sun's pass draws every chunk in its box a second
    // time. The bar is still READ from `stats.budget` rather than written here, so
    // this check follows the definition site and cannot drift from it.
    const stats = await page.evaluate(() => window.__chicago4d.stats());
    // THE CALL CEILING IS PINNED HERE AS WELL AS READ (T-0068). This check used
    // to compare the frame against whatever number `main.js` happened to be
    // carrying, so a scene that had outgrown its budget could be made green by
    // editing the budget — the exact move T-0115's ledger exists to make
    // impossible to do quietly. Moving the number has to move this line too, in
    // the same commit, with the measurement that justified it.
    //
    // Only the CALL ceiling is pinned here, and deliberately: the triangle
    // budget follows the detail tier the visitor is on (`BUDGET.triangles` is
    // reset from `DETAIL[level]`), so it reads 600,000 on a phone booting into
    // `light` and 1,000,000 on a desktop. The three tier ceilings have their own
    // check further down, which is where a re-budget of those would show.
    check(`${label}: the scene's draw-call ceiling is the one this gate was written against`,
      stats.budget.drawCalls === 215,
      `budget reads ${stats.budget.drawCalls} calls / ${stats.budget.triangles} tris`);
    check(`${label}: draw calls under budget at the reference stand`,
      stats.drawCalls <= stats.budget.drawCalls,
      `${stats.drawCalls} calls (budget ${stats.budget.drawCalls}) — `
      + `the gate is the worst-stand check below`);
    check(`${label}: triangles under budget at the reference stand`,
      stats.triangles <= stats.budget.triangles,
      `${stats.triangles} tris (budget ${stats.budget.triangles}) — `
      + `the gate is the worst-stand check below`);
    console.log(`        ${stats.drawCalls} draw calls · ${stats.triangles} tris · `
      + `${stats.batches} batch(es) · ${stats.structures} structure(s) · `
      + `${(stats.bytes / 1024).toFixed(0)} KB of GLB · ${stats.fps} fps`);

    // --- the scene is at life size ------------------------------------------
    //
    // This gate ran green through a scene in which every building was a sixth of
    // its size and the ground had sunk under the water plane, because nothing it
    // checked was a LENGTH. Draw calls, triangles, page errors and even "the
    // walker stays on the terrain" all survive a uniform scale error: the walker
    // reads the heightfield, not the mesh, so it went on standing at the correct
    // height over a shrunken world and the owner got a photograph of a flood.
    //
    // So: measure the rendered geometry against the authored numbers it is a
    // rendering OF. A quantised GLB carries its dequantisation on the node, and
    // any loader that drops that transform fails here immediately.
    const scale = await page.evaluate(() => {
      const a = window.App ?? window.__chicago4d;
      const hf = a.terrain.heightfield;
      const wantW = (hf.cols - 1) * hf.cellM;
      const wantD = (hf.rows - 1) * hf.cellM;
      let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
      let terrainMeshes = 0;
      a.scene3d.traverse((o) => {
        if (!o.isMesh || !/^terrain__/.test(o.name || '')) return;
        terrainMeshes++;
        o.geometry.computeBoundingBox();
        const b = o.geometry.boundingBox;
        minX = Math.min(minX, b.min.x); maxX = Math.max(maxX, b.max.x);
        minZ = Math.min(minZ, b.min.z); maxZ = Math.max(maxZ, b.max.z);
      });
      // A documented two-storey hotel, so its rendered height is a fact with a
      // knowable range rather than a magic number.
      const rec = a.registry.get('sauganash_hotel');
      const wall = rec?.sidecar?.attributes?.wall_height_m?.value ?? null;

      // EVERY structure, measured against what its own record claims — not the
      // tallest one in the scene. See the note on the assertions below.
      const bounds = a.buildings.instanceBounds();
      const perStructure = [];
      for (const [id, box] of Object.entries(bounds)) {
        const r = a.registry.get(id);
        const attrs = r?.sidecar?.attributes ?? {};
        perStructure.push({
          id,
          size: box.size,
          wallHeight: attrs.wall_height_m?.value ?? null,
          footprint: [attrs.footprint_w_m?.value ?? null, attrs.footprint_d_m?.value ?? null],
        });
      }
      return { terrainMeshes, gotW: maxX - minX, gotD: maxZ - minZ, wantW, wantD,
        wall, perStructure, structureCount: a.registry.size };
    });
    // The ground is deliberately LARGER than the heightfield — it carries a
    // far-field skirt past the modelled box, which is what you see on the horizon
    // and what the fly-mode notice calls the edge of the detail. So the invariant
    // is COVERAGE, not equality: there must be no place with terrain data and no
    // ground under it. A dropped dequantisation shrinks the mesh and fails this
    // instantly, which is the failure it exists to catch; the upper bound only
    // stops the skirt growing without anyone noticing.
    check(`${label}: the rendered ground covers the whole heightfield`,
      scale.terrainMeshes > 0
      && scale.gotW >= scale.wantW && scale.gotD >= scale.wantD
      && scale.gotW <= scale.wantW * 8 && scale.gotD <= scale.wantD * 8,
      `${scale.gotW?.toFixed(0)}x${scale.gotD?.toFixed(0)} m rendered against `
      + `${scale.wantW?.toFixed(0)}x${scale.wantD?.toFixed(0)} m of heightfield `
      + `(${scale.terrainMeshes} mesh(es))`);
    // EVERY structure is measured, not the tallest one.
    //
    // The assertion this replaces read the largest bounding box in the whole
    // group and asked whether it was between 3 and 30 m. That passes with one
    // correct building and two hundred and forty-one collapsed ones — which is
    // precisely the town that shipped, twice. Quantised POSITION attributes were
    // being clamped to a 2 m cube, and the single uncompressed asset in the
    // scene kept the number green while the visitor stood in a field of boxes.
    //
    // A rendered size only means something against a claim, so the floor here is
    // the smallest thing the dataset actually contains — a privy, not a house —
    // and anything at or under the quantisation clamp is called out by name.
    const collapsed = scale.perStructure.filter((s) => Math.max(...s.size) <= 2.05);
    check(`${label}: no structure is collapsed to the quantisation clamp`,
      collapsed.length === 0,
      collapsed.length
        ? `${collapsed.length}/${scale.perStructure.length} at or under 2.05 m: `
          + collapsed.slice(0, 5).map((s) => s.id).join(', ')
        : `all ${scale.perStructure.length} structures larger than the 2 m clamp`);

    const absurd = scale.perStructure.filter((s) => {
      const m = Math.max(...s.size);
      // Piers and bridges are legitimately long; nothing is legitimately taller
      // than the courthouse cupola or smaller than a privy in every dimension.
      return m < 1.5 || s.size[1] > 30;
    });
    check(`${label}: every structure is rendered at a believable size`,
      absurd.length === 0,
      absurd.length
        ? absurd.slice(0, 5).map((s) => `${s.id} ${s.size.map((v) => v.toFixed(1)).join('x')}`).join('; ')
        : `${scale.perStructure.length} structures within range`);

    // --- the Sauganash is two masses, not one box (T-0626) ------------------
    //
    // The owner reported this building from the walk: a mass missing at the back
    // and a log hut standing in front of its street door. Both were record faults
    // and both are fixed, so the fix is asserted where a regression would show —
    // in the RENDERED bounds, not in the JSON, because a record that grew a
    // `cross_wing` attribute nothing built would read as fixed everywhere else.
    //
    // Orientation-agnostic on purpose. The plan is a 9.92 m frontage on Lake
    // Street with an 8 m block behind it and an 8 m wing behind THAT, so one
    // horizontal extent is about 16.5 m with the roof overhangs and the other
    // about 10.4 m; which of the two is x and which is z is the placement's
    // business and not this assertion's. The box it replaces was 12 x 8, whose
    // long side is 12.5 m — well under the floor here, so a revert fails.
    const saugBox = scale.perStructure.find((st) => st.id === 'sauganash_hotel');
    const saugPlan = saugBox ? [saugBox.size[0], saugBox.size[2]].sort((a, b) => b - a) : null;
    check(`${label}: the Sauganash is rendered as its two-mass plan`,
      !!saugPlan && saugPlan[0] >= 15.0 && saugPlan[0] <= 18.0
      && saugPlan[1] >= 9.5 && saugPlan[1] <= 11.5,
      saugPlan
        ? `plan ${saugPlan[0].toFixed(2)} x ${saugPlan[1].toFixed(2)} m `
          + `(want the long axis 15-18 m for block + cross wing, the short 9.5-11.5 m `
          + `for the measured five-bay frontage; the retired placeholder was 12 x 8)`
        : 'sauganash_hotel is not in the instance bounds at all');

    // --- nothing hovers -----------------------------------------------------
    //
    // Reported from use: "the building is hovering above the ground". Buildings
    // were stood on the ground sampled at ONE point — their origin — which is
    // right on flat land and wrong exactly where it shows. This town is nearly
    // flat, so it was right for 221 of 236 structures and wrong for the fifteen
    // on the riverbank and the fort mound, where the land falling away IS the
    // point. The Wolf Point Tavern hung 1.84 m in the air on its river side.
    //
    // Measured through the REAL instance matrix, at the four base corners, in
    // world space. My first pass at this measurement re-derived the placement
    // instead of reading it and sampled an unrotated box, which reported eight
    // failures that did not exist — a gate that guesses at what the renderer did
    // is worth nothing.
    const hover = await page.evaluate(() => {
      const api = window.__chicago4d;
      const bounds = api.buildings.instanceBounds();
      const rows = [];
      for (const [id, rec] of api.registry) {
        const p = rec?.sidecar?.placement;
        if (!p || typeof p.local_e !== 'number') continue;
        if (p.vertical_anchor === 'water') continue;   // bridges sit at the datum
        const b = bounds[id];
        const m = api.buildings.matrixOf(id);
        if (!b || !m) continue;
        let gap = -Infinity;
        for (const cx of [b.min[0], b.max[0]]) {
          for (const cz of [b.min[2], b.max[2]]) {
            const e = m.elements;
            const wx = e[0] * cx + e[4] * b.min[1] + e[8] * cz + e[12];
            const wy = e[1] * cx + e[5] * b.min[1] + e[9] * cz + e[13];
            const wz = e[2] * cx + e[6] * b.min[1] + e[10] * cz + e[14];
            gap = Math.max(gap, wy - api.terrain.surfaceHeight(wx, -wz));
          }
        }
        rows.push({ id, gap: +gap.toFixed(3) });
      }
      rows.sort((a, b2) => b2.gap - a.gap);
      return { n: rows.length, floating: rows.filter((r) => r.gap > 0.15), worst: rows[0] };
    });
    check(`${label}: no building hovers above the ground beneath it`,
      hover.n > 200 && hover.floating.length === 0,
      hover.floating.length
        ? `${hover.floating.length}/${hover.n} float: `
          + hover.floating.slice(0, 4).map((r) => `${r.id} ${r.gap} m`).join(', ')
        : `${hover.n} structures, worst corner ${hover.worst?.gap} m`);

    // Where a record states a wall height, the render has to honour it. This is
    // the provenance check hiding inside the scale check: a documented number
    // that the geometry ignores is a claim the walkthrough cannot support.
    const claimed = scale.perStructure.filter((s) => typeof s.wallHeight === 'number');
    const offClaim = claimed.filter((s) => {
      // The box includes the roof, so height must be at least the walls and at
      // most the walls plus a steep roof and a chimney.
      const h = s.size[1];
      return h < s.wallHeight * 0.9 || h > s.wallHeight * 2.6 + 3;
    });
    check(`${label}: rendered height matches the documented wall height`,
      claimed.length > 0 && offClaim.length === 0,
      claimed.length === 0
        ? 'no structure carried a wall_height_m to check against'
        : offClaim.length
          ? offClaim.slice(0, 5).map((s) => `${s.id} rendered ${s.size[1].toFixed(1)} m `
            + `against a documented ${s.wallHeight} m wall`).join('; ')
          : `${claimed.length} structures agree with their documented wall height`);

    inStageWork = false;
    } // end PART 4 (T-0060 stage 2b, cut by T-0121, cut again by T-0346)
    // PART 5 — the scene-detail ladder, and nothing else. T-0346 cut it out of
    // part 4 because it IS part 4's cost. Profiled under this lane's own eight-way
    // contention on 2026-08-30, part 4 reached this section at 1 m 10 s and left it
    // at 7 m 27 s: one section of the ten was 6 m 17 s of a part the ten-minute
    // ceiling was killing outright. The sweep walks every stand at every tier and
    // cannot be halved again without walking the set twice — which is the whole
    // saving T-0135 built it around — so it becomes a part on its own. That is the
    // honest shape for a section whose cost is one indivisible measurement.
    //
    // It inherits NO POSE. `order` below teleports to each stand itself and
    // finishes at the reference frame on purpose, so the cut needed no re-framing
    // here and no `enterTown()`: the town is not entered until part 6. The one
    // binding that did cross this boundary was the draw-call ceiling, read again
    // below rather than borrowed from part 4's `stats`.
    if (stageOn(5)) {
    inStageWork = true;

    // T-0346 — the call ceiling, read here rather than carried across the cut.
    // Part 4's budget block is the REFERENCE reading and is where the number is
    // pinned; this is the GATE. Since the cut they are separate commands, so a
    // `const` over there is not in scope here. Read out of `stats.budget` exactly
    // as it is there, so the bar still follows its definition site in main.js and
    // cannot be made green by editing this file.
    const callBudget = (await page.evaluate(
      () => window.__chicago4d.stats())).budget.drawCalls;

    // --- scene detail -------------------------------------------------------
    //
    // The triangle ceiling used to be one hard number for everyone. It is now the
    // visitor's choice, which is only worth having if each level MEANS something,
    // so this walks all three and asks two questions of each: does it stay inside
    // its OWN ceiling, and does turning it down actually draw less? A setting that
    // relabels the budget without changing the scene would pass the first and fail
    // the second, which is exactly the failure worth catching.
    //
    // T-0115 added a third question, and it is the one that keeps the first
    // answerable as the town grows. Until August 2026 the setting had a lever
    // on flora and trees and on nothing else, so 61 % of the light frame was
    // drawn exactly as `full` drew it, and the bottom rung went 11 % over a
    // ceiling no single merge had done anything wrong to. The level now also
    // decides how far the sun's shadow is cast and whether the derived
    // furniture — fences, yard goods, plank walks, signboards, wharves, boats —
    // is drawn a second time for it. So this reads back what each level DID to
    // the scene rather than what its table asked for: `light` must cast none of
    // that furniture and the other two must cast all of it, which is a claim
    // that fails loudly if a new furniture layer is mounted outside the policy.
    //
    // T-0135 added the fourth, and it is the one that makes the first mean
    // anything: every level is now walked at the WHOLE STAND SET and held to its
    // ceiling at the worst of them. A tier ceiling checked at one friendly camera
    // is a spot reading, and a spot reading is what let the ladder go on being
    // described as a 40 % step while the bottom rung was, at an axial view, doing
    // 25 %. The per-level rows below print the worst stand by name, so a level
    // that fails says WHERE.
    const detail = await page.evaluate(async (stands) => {
      const a = window.__chicago4d;
      const settle = () => new Promise((r) => requestAnimationFrame(
        () => requestAnimationFrame(r)));
      const started = a.detail;
      const seen = [];
      // The reference stand is walked LAST, and that is a cost decision with a
      // number behind it: a frame at this scene costs about three seconds on the
      // software renderer CI uses, and finishing the sweep where the rest of the
      // suite expects the visitor to be saves one per level rather than teleport
      // back afterwards. `restoredAt` below asserts the order actually did that,
      // so the saving cannot quietly become a camera left up in the air.
      const order = [...stands.filter((s) => s.kind !== 'frame'),
        ...stands.filter((s) => s.kind === 'frame')];
      for (const level of a.detailOrder) {
        await a.setDetail(level);
        await settle();
        const atStands = [];
        for (const st of order) {
          // `goTo` on the aerial anchor turns flight ON; every `frame` stand
          // turns it off again, which is why one has to be last.
          if (st.kind === 'frame') { a.setFly(false); a.frame(st.target, st.distance); }
          else a.goTo(st.target);
          await settle();
          const r = a.stats();
          const row = { id: st.id, label: st.label, tris: r.triangles, calls: r.drawCalls,
                        hidden: a.furnitureReach.hidden };
          // T-0150 — WHAT THE FURNITURE'S REACH IS ACTUALLY WORTH, measured by
          // turning it off and back on at the stand it exists for, rather than
          // by reading the table that asked for it. Taken at the axial stand
          // ONLY, and that is a cost decision: a frame is about three seconds on
          // the software renderer CI uses, and this stage is already the longest
          // in the suite (T-0121). Lake at Canal is the stand the trim was
          // designed against and the one whose reading it has to keep earning.
          if (st.id === 'lake_at_canal' && a.furnitureReach.reachM !== null) {
            const on = a.furnitureReach.reachM;
            a.setFurnitureReach(null);
            await settle();
            const off = a.stats();
            a.setFurnitureReach(on);
            await settle();
            row.trimTris = off.triangles - r.triangles;
            row.trimCalls = off.drawCalls - r.drawCalls;
          }
          // T-0146 — WHAT THE FAR MERGE IS WORTH, and the fact that it costs
          // nothing, taken the same way and at the same stand and for the same
          // cost reason: one tier only (`full`, where the worst frame is), one
          // stand only, two extra frames in the whole stage. The merge submits
          // a far cluster as one mesh only while the cluster is wholly inside
          // the frustum, so the triangle delta is 0 BY CONSTRUCTION — it is
          // asserted below rather than tolerated, because a merge that started
          // drawing what the frustum used to skip would be a ceiling breach
          // wearing a saving's clothes.
          if (st.id === 'lake_at_canal' && level === 'full') {
            row.mergeClusters = a.farMerge.clusters;
            row.mergeMerged = a.farMerge.merged;
            a.setFarMerge(false);
            await settle();
            const off = a.stats();
            // Restored without a settle of its own, deliberately: this stand is
            // never the last of the order, `setFarMerge` puts the visibility
            // back synchronously, and the next stand settles before it reads.
            // Part 4 is the thinnest margin in the desktop suite (T-0173) and a
            // frame here costs about three seconds on the software renderer.
            a.setFarMerge(true);
            row.mergeTris = off.triangles - r.triangles;
            row.mergeCalls = off.drawCalls - r.drawCalls;
          }
          atStands.push(row);
        }
        // The furniture and shadow-rig readings are properties of the LEVEL, not
        // of where the camera is standing, so they are taken once — and taken
        // with the visitor back at the reference stand, which is both where the
        // rest of the suite expects them and what keeps `tris`/`calls` below the
        // same reference figures this line has always reported.
        const s = a.stats();
        const f = a.furnitureShadows;
        seen.push({ level, tris: s.triangles, calls: s.drawCalls,
          ceiling: a.detailLevels[level].triangles,
          furnitureReachM: a.furnitureReach.reachM,
          furnitureMeshesReach: a.furnitureReach.meshes,
          bankedSpheres: a.furnitureReach.banked,
          atStands,
          worstTris: atStands.reduce((x, y) => (y.tris > x.tris ? y : x)),
          worstCalls: atStands.reduce((x, y) => (y.calls > x.calls ? y : x)),
          reachM: a.world.shadowRig.reachM, texelM: a.world.shadowRig.texelM,
          furnitureMeshes: f.meshes, furnitureCasting: f.casting,
          furnitureGroundHugging: f.groundHugging });
      }
      await a.setDetail(started);
      return { seen, restored: a.detail === started, flying: a.flying,
        restoredAt: order[order.length - 1].id };
    }, STANDS);
    for (const s of detail.seen) {
      check(`${label}: scene detail '${s.level}' stays inside its own ceiling at the WORST stand`,
        s.worstTris.tris <= s.ceiling && s.worstCalls.calls <= callBudget,
        `${s.worstTris.tris.toLocaleString('en-US')} tris of `
        + `${s.ceiling.toLocaleString('en-US')} at ${s.worstTris.label}, `
        + `${s.worstCalls.calls} calls of ${callBudget} at ${s.worstCalls.label} `
        + `— spread: ${s.atStands.slice().sort((a, b) => b.tris - a.tris)
          .map((x) => `${x.label} ${x.tris.toLocaleString('en-US')}/${x.calls}c`).join(' · ')}`);
    }
    const [full, balanced, light] = detail.seen;
    // THE DRAW-CALL GATE, and the whole of it (T-0135). The budget block above
    // reads the reference stand for continuity; this is the assertion. It takes
    // the maximum over every stand at every tier — a draw call is not a tier's
    // property the way its triangle ceiling is, so the number a visitor can
    // reach is the worst frame anywhere in the set, whatever level they chose.
    const townWorstCalls = detail.seen
      .flatMap((lv) => lv.atStands.map((x) => ({ ...x, level: lv.level })))
      .reduce((a, b) => (b.calls > a.calls ? b : a));
    check(`${label}: draw calls under budget at the town's WORST frame`,
      townWorstCalls.calls <= callBudget,
      `${townWorstCalls.calls} calls at ${townWorstCalls.label}, '${townWorstCalls.level}' `
      + `(budget ${callBudget}) — spread by level: `
      + detail.seen.map((lv) => `${lv.level} ${lv.worstCalls.calls} at ${lv.worstCalls.label}`)
        .join(' · '));
    // Asserted PER STAND rather than on one reading, because "turning it down
    // draws less" is a claim about the control and not about a camera: a level
    // that cut the near flora and nothing else would hold at the reference stand
    // and fail down the street, which is the shape of the defect T-0115 found.
    const ladderBroken = STANDS.map((s) => {
      const at = (lv) => lv.atStands.find((x) => x.id === s.id);
      return { label: s.label, f: at(full).tris, b: at(balanced).tris, l: at(light).tris };
    }).filter((r) => !(r.f > r.b && r.b > r.l));
    check(`${label}: turning scene detail down actually draws less, at every stand`,
      ladderBroken.length === 0,
      ladderBroken.length
        ? ladderBroken.map((r) => `${r.label} ${r.f} > ${r.b} > ${r.l}`).join('; ')
        : STANDS.map((s) => {
          const r = detail.seen.map((lv) => lv.atStands.find((x) => x.id === s.id).tris);
          return `${s.label} ${((1 - r[2] / r[0]) * 100).toFixed(0)} %`;
        }).join(' · '));
    // THIS ASSERTION WAS WEAKENED ON 2026-08-22, AND CALLING IT ANYTHING ELSE
    // WOULD BE A LIE. It used to hold that `light` draws inside the 80 calls
    // this project budgeted before any of the 2026-08 content landed — the
    // promise that the tier a weak machine boots into stays affordable. T-0135
    // measured it at the WORST stand for the first time and found 167 calls
    // down Lake Street. The owner ruled to raise the ceilings rather than trim
    // the view ("raise it, I think", 2026-08-22), which surrenders that promise
    // knowingly: `light` carried 1,050,000 triangles, more than `full` promised
    // the day before. In the count's place stood a RATIO — `light` merely had to
    // be materially cheaper than `full` — which guards the control doing
    // something but promises a person nothing.
    //
    // AND THE COUNT IS BACK, 2026-08-27 (T-0147), which is what the note that
    // stood here asked for in as many words: "when it does, this check should go
    // back to being a count — and a count is what a promise to a person looks
    // like." The trims that earned it are T-0150 (the derived furniture
    // distance-culled at `light`), T-0146 (far chunks merged back into single
    // draws) and T-0223's timber cull. Read on the published mirror at T-0135's
    // five stands, dev @ f7aca445: `light`'s worst frame is 76 calls on desktop
    // and 69 on mobile, against the 141 and 137 `full` reaches at its own worst.
    // 80 was the ORIGINAL number and not one tuned to sit just over 76 — four
    // calls of room, and the next chunked layer to reach it reaches a bar that
    // means something. Thin on purpose and thin in fact: the reading was 75
    // before T-0194's hitching posts merged and 76 after, so one ordinary
    // parcel spent a quarter of the margin. When it goes red the answer is a
    // trim or an argued re-budget at `DETAIL`, never a weakening of this line. `light`'s triangle ceiling came down in the same commit,
    // 1,050,000 -> 785,000, and `DETAIL` in `main.js` carries that reading.
    //
    // AND IT WENT RED, AND THE ANSWER WAS THE RE-BUDGET. 80 -> 90 on the
    // owner's ruling, 2026-08-28, taken against the current reading and not a
    // week-old one: 85 calls at Lake and Market, the corner itself (dev's
    // standing smoke, 2026-08-28T18:36Z, the T-0028 tree). The four calls of
    // room T-0147 restored were spent in a day — hitching posts, Randolph's
    // street edge, the jail — and the owner chose the re-budget over the trim
    // (T-0247 carried the trim and is withdrawn with the ruling on it). Say
    // what 90 surrenders: the pre-2026-08 count is gone for the second time,
    // this bar has now moved twice (surrendered 2026-08-22, restored
    // 2026-08-27, moved 2026-08-28), and a weak machine's promise is five
    // calls of slack over today's worst frame instead of a chosen constant.
    // 90 is still a bar: it moved BY a measured ten against a measured 85,
    // not to wherever the reading was, and the next parcel to spend the five
    // spare calls reaches it honestly. When THIS one goes red, same rule:
    // a trim or an argued re-budget, never a quiet weakening.
    //
    // The ratio is KEPT underneath rather than replaced: the count is the
    // promise to a weak machine, the ratio is the claim that the scene-detail
    // control is not decoration, and a reading can break either without the
    // other.
    const LIGHT_CALL_FLOOR = 90;
    check(`${label}: the light tier draws inside its ${LIGHT_CALL_FLOOR}-call floor at the worst stand`,
      light.worstCalls.calls <= LIGHT_CALL_FLOOR,
      `${light.worstCalls.calls} calls at light, worst stand ${light.worstCalls.label} `
      + `— floor ${LIGHT_CALL_FLOOR}, set by the owner 2026-08-28 against a measured 85 `
      + `at Lake and Market (was 80, the pre-2026-08 count restored by T-0147; `
      + `the ruling is recorded at the definition site and on T-0247)`);
    check(`${label}: the light tier stays materially cheaper than full at the worst stand`,
      light.worstCalls.calls <= full.worstCalls.calls * 0.9,
      `${light.worstCalls.calls} calls at light against ${full.worstCalls.calls} at full, `
      + `worst stand ${light.worstCalls.label}`);
    check(`${label}: the level the visitor started on is restored`,
      detail.restored && !detail.flying && detail.restoredAt === STANDS[0].id,
      `${detail.restored ? 'level restored' : 'level NOT restored'}, `
      + `${detail.flying ? 'left flying' : 'back on foot'}, `
      + `sweep ended at ${detail.restoredAt} (want ${STANDS[0].id})`);
    // The trim, asserted on the meshes rather than on the table that asked for
    // it: a policy that reaches `DETAIL` and not the scene passes every check
    // above unchanged, which is the failure this one exists to catch.
    //
    // T-0188 — AND THE TWO CASTING TIERS ARE NO LONGER HELD TO "EVERY MESH".
    // The ground-hugging furniture (the plank-walk and board-crossing chunks of
    // the town street edge and the river walk, 2.9 km of boards lying 0.11 m
    // proud of the ground) is exempt at every tier, because its own cast shadow
    // is about 0.04 m wide at noon and drawing it into the shadow map costs its
    // whole triangle count and a draw call per chunk for nothing a visitor can
    // see. The exemption is COUNTED rather than assumed: `furnitureShadows`
    // reports `groundHugging`, the bar is `casting === meshes - groundHugging`,
    // and the count is asserted to be non-zero — so a layer that silently
    // stopped casting still fails here, and an exemption nobody declared cannot
    // hide in the difference.
    check(`${label}: the light tier draws no furniture into the shadow map, and only the ground-hugging timber is exempt above it`,
      light.furnitureMeshes > 0 && light.furnitureCasting === 0
      && full.furnitureGroundHugging > 0
      && full.furnitureCasting === full.furnitureMeshes - full.furnitureGroundHugging
      && balanced.furnitureCasting === balanced.furnitureMeshes - balanced.furnitureGroundHugging,
      detail.seen.map((s) => `${s.level} ${s.furnitureCasting}/${s.furnitureMeshes} casting `
        + `(${s.furnitureGroundHugging} ground-hugging)`).join(', '));
    /**
     * T-0150 — THE FURNITURE'S REACH, asserted as three separate claims because
     * three separate things can break it.
     *
     * FIRST, that the reach is a LADDER and that `full` sits at the top of it
     * holding nothing back. Until T-0241 this check read "only the bottom rung
     * holds anything back", because only the bottom rung did; `balanced` now
     * carries 800 m to `light`'s 350 m, which is what makes "turn the quality
     * down and less is drawn" true of the middle rung as well as the floor.
     * What must never happen is a reach leaking into `full` — the tier whose
     * whole promise is that nothing is held back — or the rungs crossing, which
     * would be a visitor stepping DOWN a setting and getting more geometry.
     * Read off the MESHES (`hidden`, counted at every stand) as well as off the
     * level, for the reason `furnitureShadows` is: a policy that reaches `DETAIL`
     * and not the scene passes every ceiling check unchanged.
     */
    const hiddenAtFull = full.atStands.filter((x) => x.hidden > 0);
    check(`${label}: the furniture reach is a ladder — full holds nothing back, and each rung below reaches less far`,
      full.furnitureReachM === null && hiddenAtFull.length === 0
      && balanced.furnitureReachM !== null && light.furnitureReachM !== null
      && light.furnitureReachM < balanced.furnitureReachM
      && light.bankedSpheres > 0,
      hiddenAtFull.length
        ? `full hid ${hiddenAtFull[0].hidden} at ${hiddenAtFull[0].label}`
        : detail.seen.map((lv) => `${lv.level} reach ${lv.furnitureReachM ?? 'none'}`).join(', ')
          + ` — ${light.bankedSpheres} furniture chunk(s) banked`);
    /**
     * SECOND, that at `light` it reaches the frame at the stand it was built for.
     * A reach set to a number larger than the town would satisfy the first check
     * and do nothing at all.
     */
    /**
     * T-0146 — THE FAR MERGE, asserted as the one claim it makes: down the
     * axial street it gives back a large part of the call count the chunking
     * spent, and it moves NOT ONE TRIANGLE doing it. Both halves come from the
     * same frame read twice at the stand the trim was designed against, so
     * neither can be satisfied by an unrelated layer getting cheaper.
     *
     * The call bar is set at roughly half the 54 calls measured when it landed
     * (201 -> 147 at `full`, `tools/measure_far_merge.mjs`), which is the same
     * margin T-0150's reach bar carries: enough that the merge going dead is
     * caught, loose enough that a parcel adding a chunk somewhere does not have
     * to re-argue the number. The triangle bar has no margin at all and must
     * not be given one.
     */
    const merged = full.atStands.find((x) => x.id === 'lake_at_canal');
    check(`${label}: the far merge gives back draw calls down the axial street and moves no triangle doing it`,
      !!merged && merged.mergeTris === 0 && merged.mergeCalls >= 25
      && merged.mergeMerged > 0,
      merged
        ? `${merged.mergeCalls} call(s) saved over ${merged.mergeMerged} of `
          + `${merged.mergeClusters} cluster(s), ${merged.mergeTris} triangle(s) moved`
        : 'the axial stand was not walked at full');
    const axial = light.atStands.find((x) => x.id === 'lake_at_canal');
    check(`${label}: the light tier holds furniture back down the axial street`,
      !!axial && axial.hidden > 0,
      axial ? `${axial.hidden} of ${light.furnitureMeshesReach} furniture chunk(s) `
        + `beyond ${light.furnitureReachM} m at ${axial.label}`
        : 'the axial stand was not walked');
    /**
     * THIRD, AND IT IS THE ONE WITH THE NUMBER IN IT: the reach is what is doing
     * the saving. Measured in the gate by turning the cull off at that stand and
     * reading the same frame twice, so this cannot be satisfied by some unrelated
     * layer getting cheaper — the difference is attributable by construction.
     *
     * The bars are set at roughly half the measurement that chose the reach
     * (`main.js` FURNITURE_REACH_LIGHT_M: 252,140 triangles and 107 calls at
     * 1280x800, 248,748 and 102 at 390x780), which is the same order of margin
     * the ceilings carry. Half rather than just-under, because this is a ratchet
     * on a MECHANISM and not a budget: a change that halves what the trim is
     * worth has broken it, and one that trims a little less because the town got
     * denser inside 350 m has not.
     */
    check(`${label}: the furniture reach is what makes the light tier cheaper down that street`,
      !!axial && axial.trimTris >= 120000 && axial.trimCalls >= 50,
      axial?.trimTris === undefined
        ? 'the trim was not measured at the axial stand'
        : `turning the reach off adds ${axial.trimTris.toLocaleString('en-US')} triangles `
          + `and ${axial.trimCalls} draw calls at ${axial.label} `
          + `(need 120,000 and 50)`);
    /**
     * AND THE SAME TWO CLAIMS FOR THE MIDDLE RUNG — T-0241. `balanced`'s 800 m
     * is what carries Washington Street, so it is the reach whose going dead
     * would put a tier over its ceiling rather than merely cost it a saving.
     *
     * TRIANGLES ONLY, and the missing call bar is a measurement rather than an
     * omission: 800 m gives back 68,772 triangles at this stand and FIVE draw
     * calls (151 -> 146 desktop, 151 -> 147 mobile), because the chunks it hides
     * at that range are the ones T-0146's far merge had already collapsed into
     * single calls. A bar on five is a bar on noise. The triangle bar is half the
     * measured 68,772, the same ratchet-not-a-budget margin the `light` bar
     * above carries and for the same reason.
     */
    const axialBalanced = balanced.atStands.find((x) => x.id === 'lake_at_canal');
    check(`${label}: the balanced tier holds furniture back down the axial street`,
      !!axialBalanced && axialBalanced.hidden > 0,
      axialBalanced ? `${axialBalanced.hidden} of ${balanced.furnitureMeshesReach} furniture `
        + `chunk(s) beyond ${balanced.furnitureReachM} m at ${axialBalanced.label}`
        : 'the axial stand was not walked at balanced');
    check(`${label}: the furniture reach is what makes the balanced tier cheaper down that street`,
      !!axialBalanced && axialBalanced.trimTris >= 34000,
      axialBalanced?.trimTris === undefined
        ? 'the trim was not measured at the axial stand at balanced'
        : `turning the reach off adds ${axialBalanced.trimTris.toLocaleString('en-US')} `
          + `triangles at ${axialBalanced.label} (need 34,000)`);
    check(`${label}: the light tier's shorter shadow reach costs no texel`,
      light.reachM < full.reachM && Math.abs(light.texelM - full.texelM) < 1e-6,
      detail.seen.map((s) => `${s.level} ±${s.reachM} m at `
        + `${(s.texelM * 100).toFixed(1)} cm/texel`).join(', '));
    console.log(`        detail  ${detail.seen.map((s) =>
      `${s.level} ${s.tris}/${s.ceiling} (${s.calls} calls, ±${s.reachM} m, `
      + `${s.furnitureCasting}/${s.furnitureMeshes} furniture casting)`).join('  ·  ')}`);
    for (const s of detail.seen) {
      console.log(`        ${s.level.padEnd(9)} worst ${s.worstTris.tris.toLocaleString('en-US').padStart(11)} tris `
        + `of ${s.ceiling.toLocaleString('en-US')} at ${s.worstTris.label}  ·  `
        + `worst ${String(s.worstCalls.calls).padStart(4)} calls at ${s.worstCalls.label}`);
    }

    inStageWork = false;
    } // end PART 5 (the scene-detail ladder, cut out of part 4 by T-0346)
    // PART 6 — the gate, the chrome and the confidence menu's own clicks: the
    // tail of what was part 4, and the point at which an unfiltered pass ENTERS
    // THE TOWN. It stands alone because the sweep above it had to, and it is the
    // right side of the boundary to have been left on: every check in it is a
    // real click on the HUD, and none of them shares a reading with the budgets
    // or the ladder. Measured at about 1 m 55 s under load on 2026-08-30, the
    // cheapest of the three.
    if (stageOn(6)) {
    inStageWork = true;

    // --- the gate and the chrome -------------------------------------------
    await page.click('#gate-btn');
    await page.waitForTimeout(150);
    // Entering the walkthrough grabs the pointer on desktop; release it, or
    // every later click lands on the locked canvas instead of the HUD.
    await page.evaluate(() => document.exitPointerLock?.());
    await page.waitForTimeout(120);
    const chrome = await page.evaluate(() => ({
      gateHidden: document.getElementById('gate').hasAttribute('hidden'),
      hudShown: !document.getElementById('hud').hasAttribute('hidden'),
      controlHelpShown: !document.getElementById('control-help').hasAttribute('hidden'),
      desktopHelpShown: getComputedStyle(document.getElementById('control-help-desktop')).display !== 'none',
      touchHelpShown: getComputedStyle(document.getElementById('control-help-touch')).display !== 'none',
      overflow: document.documentElement.scrollWidth <= window.innerWidth + 1,
    }));
    check(`${label}: tap-to-start reveals the walkthrough`,
      chrome.gateHidden && chrome.hudShown,
      `gate hidden ${chrome.gateHidden}, hud shown ${chrome.hudShown}`);
    check(`${label}: first entry shows the navigation guide for the active input mode`,
      chrome.controlHelpShown
      && (touch ? chrome.touchHelpShown && !chrome.desktopHelpShown
        : chrome.desktopHelpShown && !chrome.touchHelpShown),
      JSON.stringify(chrome));
    check(`${label}: no horizontal overflow`, chrome.overflow);
    await page.click('#control-help-gotit');
    const controlHelpDismissed = await page.evaluate(() => ({
      hidden: document.getElementById('control-help').hasAttribute('hidden'),
      stored: localStorage.getItem('chicago4d.controlHelpDismissed'),
    }));
    check(`${label}: the navigation guide dismisses and remembers the choice`,
      controlHelpDismissed.hidden && controlHelpDismissed.stored === '1',
      JSON.stringify(controlHelpDismissed));

    // --- the confidence menu takes its own clicks (T-0108) -------------------
    //
    // The HUD is pointer-events: none so the world stays live underneath, and
    // every interactive piece re-enables it for itself. The level menu did not,
    // so a click on a checkbox fell THROUGH to the canvas — re-locking the
    // pointer and tripping the click-away close at once: the menu vanished and
    // nothing toggled. Owner-reported. A REAL Playwright click is the only
    // honest instrument for a pointer-events regression: it hit-tests like a
    // visitor's mouse, where an evaluate()'d .click() would quietly pass. It
    // runs here because the HUD only exists past the gate, and the guide that
    // covers this corner of it was dismissed by the check above.
    //
    // SO THESE FOUR STAY `page.click` (T-0215). Part 8's chrome clicks moved to
    // `clickChrome`, which hit-tests at the element's own centre and would catch
    // this same regression — but here the trusted event is not the means, it is
    // the SUBJECT, and the instrument should be the visitor's own mouse.
    await page.click('#btn-confidence-more');
    await page.click('#cm-reconstructed');
    await page.waitForTimeout(120);
    const cmClick = await page.evaluate(() => ({
      menuOpen: !document.getElementById('confidence-menu').hasAttribute('hidden'),
      unchecked: !document.getElementById('cm-reconstructed').checked,
      marked: document.getElementById('confidence-group').classList.contains('has-hidden'),
    }));
    check(`${label}: a level checkbox takes the click and the menu stays open`,
      cmClick.menuOpen && cmClick.unchecked && cmClick.marked,
      JSON.stringify(cmClick));
    // Put the town back the way it was, through the same real controls.
    await page.click('#cm-reset');
    await page.click('#btn-confidence-more');
    await page.waitForTimeout(120);
    const cmRestored = await page.evaluate(() => ({
      menuShut: document.getElementById('confidence-menu').hasAttribute('hidden'),
      allOn: ['cm-attested', 'cm-inferred', 'cm-reconstructed']
        .every((id) => document.getElementById(id).checked),
      marked: document.getElementById('confidence-group').classList.contains('has-hidden'),
    }));
    check(`${label}: reset restores every level and the caret shuts the menu`,
      cmRestored.menuShut && cmRestored.allOn && !cmRestored.marked,
      JSON.stringify(cmRestored));

    inStageWork = false;
    } // end PART 6 (the tail of T-0060 stage 2b, cut out of part 4 by T-0346)
    // PART 7 — navigation through the second road-legibility station: the
    // readouts, the streets the heightfield carries, and the roads read from the
    // walker's eye and from the air. T-0173 cut the crossing station, the aid
    // and the batch merge out of here into part 8.
    if (stageOn(7)) {
    inStageWork = true;

    // A fresh boot is still standing at the GATE SCREEN: part 6's "the gate
    // and the chrome" section is what enters the town, releases the pointer
    // and dismisses the first-entry navigation guide, and this point of an
    // unfiltered pass runs long after it did. The road-legibility bands
    // measure page.screenshot frames, which include DOM overlays (the
    // GL-capture checks do not) — so a staged run must stand where the full
    // run stands: gate entered, pointer free, guide down. In a full run every
    // branch below is a no-op.
    await enterTown();

    // --- navigation --------------------------------------------------------
    // Both readouts are derived from the live walker.  The overview's signature
    // is sampled from its own 2D canvas before and after a teleport so this
    // checks the visible marker, not merely an object property updated beside it.
    const nav = await page.evaluate(() => {
      const api = window.__chicago4d;
      const mapCanvas = document.getElementById('overview-map-canvas');
      const signature = () => {
        const p = mapCanvas.getContext('2d').getImageData(0, 0, mapCanvas.width, mapCanvas.height).data;
        let hash = 2166136261;
        for (let i = 0; i < p.length; i += 37) hash = Math.imul(hash ^ p[i], 16777619) >>> 0;
        return hash;
      };
      api.walker.teleport({ local_e: 20, local_n: -40, yaw_deg: 90 });
      api.step();
      const first = signature();
      const east = {
        direction: document.getElementById('compass-direction')?.textContent,
        bearing: document.getElementById('compass-bearing')?.textContent,
        snapshot: api.navigation.snapshot(),
      };
      api.walker.teleport({ local_e: 180, local_n: 90, yaw_deg: 225 });
      api.step();
      return {
        compassShown: !document.getElementById('compass')?.hasAttribute('hidden'),
        mapShown: !document.getElementById('overview-map')?.hasAttribute('hidden'),
        mapCaption: document.querySelector('.overview-caption')?.textContent?.trim(),
        mapAria: document.getElementById('overview-map')?.getAttribute('aria-label'),
        speedLabel: document.getElementById('v-speed')?.textContent?.trim(),
        paceLabels: ['v-speed', 'v-wagon-speed', 'v-horse-speed'].map(
          (id) => [id, document.getElementById(id)?.textContent?.trim() ?? null]),
        units: document.getElementById('s-units')?.value,
        mapSize: [mapCanvas.width, mapCanvas.height],
        // T-1142. The BACKING store is CSS px x dpr and so differs between the
        // two viewports for reasons that are not the frame; the box is what the
        // visitor sees, and it is the box that must not move when ground does.
        mapBox: (() => {
          const b = mapCanvas.getBoundingClientRect();
          return { w: Math.round(b.width), h: Math.round(b.height) };
        })(),
        east,
        first,
        second: signature(),
        moved: api.navigation.snapshot(),
      };
    });
    check(`${label}: compass shows the live heading`,
      nav.compassShown && nav.east.direction === 'E' && nav.east.bearing === '090°',
      `${nav.east.direction} ${nav.east.bearing}`);
    check(`${label}: the overview map is shown, captioned and read in imperial`,
      nav.mapShown && nav.mapSize[0] >= 188 && nav.mapSize[1] >= 76
      && nav.east.snapshot.bounds.eMax - nav.east.snapshot.bounds.eMin > 1900
      && nav.mapCaption === 'map' && nav.units === 'imperial'
      && /feet|ft/.test(nav.mapAria ?? ''),
      `${nav.mapSize.join('x')}, caption ${nav.mapCaption}, aria ${nav.mapAria}, `
      + `E ${nav.east.snapshot.bounds.eMin}…${nav.east.snapshot.bounds.eMax}`);
    // T-1142. THE FRAME IS A CONSTANT, and this is the assertion that keeps it
    // one. It used to be the field's own aspect ratio —
    //   logicalHeight = round(logicalWidth * (nMax - nMin) / (eMax - eMin))
    // — so the widget was the ground's shadow, and when T-1067, T-1123 and
    // T-0464 grew the field in two days the inset went 248x98 -> 248x604, more
    // than half a phone screen, with the town smeared across the top of it.
    // These numbers are what that formula PRODUCED on the 2026-09-12 field, so
    // an edit that re-derives the height from `bounds` fails HERE rather than
    // shipping — which matters because T-0466 widens the field to four
    // kilometres and would walk the whole fault back in.
    const frame = touch ? { w: 188, h: 76 } : { w: 248, h: 98 };
    check(`${label}: the overview inset is a fixed ${frame.w}x${frame.h} frame, not the field's shape`,
      Math.abs(nav.mapBox.w - frame.w) <= 1 && Math.abs(nav.mapBox.h - frame.h) <= 1,
      `inset ${nav.mapBox.w}x${nav.mapBox.h} css px (expected ${frame.w}x${frame.h}), `
      + `backing ${nav.mapSize.join('x')}, field `
      + `${Math.round(nav.east.snapshot.bounds.nMax - nav.east.snapshot.bounds.nMin)} m deep`);
    // T-1081. The readout is `gait · speed` — "walk · 3.2 mph" — since T-0823 gave
    // each pace a named gait, and this assertion's `^`-anchored bare-number pattern
    // had called dev red on that prefix on both viewports for a week, which is a
    // week of every PR touching parts 7-8 unable to merge. The pattern now reads the
    // shape the HUD actually ships, so the gait is COVERED rather than contradicted:
    // a readout that loses its unit still fires, and so does one that loses its name.
    const PACE_READOUT = /^[a-z][a-z ]*[a-z] · \d+(?:\.\d)? mph$/;
    check(`${label}: walking speed is presented as a named gait in miles per hour`,
      PACE_READOUT.test(nav.speedLabel ?? '') && !/m\/s/.test(nav.speedLabel ?? ''),
      `speed label ${nav.speedLabel}`);
    // And all three ground paces, because the readout is one function (hud.js
    // § gaitReadout) and a fault in it reaches the wagon and the horse too.
    const badPace = nav.paceLabels.filter(([, text]) => !PACE_READOUT.test(text ?? ''));
    check(`${label}: every pace slider names its gait beside an imperial speed`,
      nav.paceLabels.length === 3 && badPace.length === 0,
      badPace.length
        ? badPace.map(([id, text]) => `${id} reads ${JSON.stringify(text)}`).join('; ')
        : nav.paceLabels.map(([id, text]) => `${id} ${text}`).join(', '));
    check(`${label}: overview marker follows position and bearing`,
      nav.first !== nav.second && Math.abs(nav.moved.e - 180) < 0.1
      && Math.abs(nav.moved.n - 90) < 0.1 && Math.abs(nav.moved.bearingDeg - 225) < 0.1,
      `canvas ${nav.first} -> ${nav.second}; ${JSON.stringify(nav.moved)}`);

    // T-1142. The inset is a WINDOW on the field, so the three things that make
    // it one are read off `snapshot().viewport` — it travels with the visitor,
    // it carries the pre-growth scale, and it stops at the field's edge instead
    // of running off into ground that does not exist. Read as numbers rather
    // than pixels, because "the picture changed" cannot tell a window that
    // moved from a marker sliding over a static image of everything.
    const win = await page.evaluate(() => {
      const api = window.__chicago4d;
      const b = api.navigation.snapshot().bounds;
      const mapCanvas = document.getElementById('overview-map-canvas');
      const signature = () => {
        const p = mapCanvas.getContext('2d').getImageData(0, 0, mapCanvas.width, mapCanvas.height).data;
        let hash = 2166136261;
        for (let i = 0; i < p.length; i += 37) hash = Math.imul(hash ^ p[i], 16777619) >>> 0;
        return hash;
      };
      const at = (n) => {
        api.walker.teleport({ local_e: 20, local_n: n, yaw_deg: 0 });
        api.step();
        const s = api.navigation.snapshot();
        return { n, view: s.viewport, inset: s.inset, sig: signature() };
      };
      const mid = (b.nMin + b.nMax) / 2;
      const low = at(mid);
      const high = at(mid + 1000);
      const south = at(b.nMin + 5);
      const north = at(b.nMax - 5);
      // Hand the walker back where the checks above left it, so nothing after
      // this reading inherits a visitor standing 3.8 km out of town.
      api.walker.teleport({ local_e: 180, local_n: 90, yaw_deg: 225 });
      api.step();
      return { b, low, high, south, north };
    });
    const spanN = win.low.view.nMax - win.low.view.nMin;
    const spanE = win.low.view.eMax - win.low.view.eMin;
    check(`${label}: the overview window travels with the visitor at the scale it had before`,
      win.low.sig !== win.high.sig
      && Math.abs((win.high.view.nMin - win.low.view.nMin) - 1000) < 1
      && Math.abs(spanN - win.low.inset.h * win.low.inset.mPerPx) < 1
      && Math.abs(spanE - win.low.inset.w * win.low.inset.mPerPx) < 1
      && Math.abs(win.low.inset.mPerPx - 2020 / 248) < 0.01,
      `window ${Math.round(spanE)}x${Math.round(spanN)} m at `
      + `${win.low.inset.mPerPx.toFixed(3)} m/px; a 1 000 m step north moved nMin `
      + `${(win.high.view.nMin - win.low.view.nMin).toFixed(1)} m; `
      + `signature ${win.low.sig} -> ${win.high.sig}`);
    check(`${label}: the overview window clamps to the field instead of running past it`,
      Math.abs(win.south.view.nMin - win.b.nMin) < 0.5
      && win.south.view.nMax <= win.b.nMax + 0.5
      && Math.abs(win.north.view.nMax - win.b.nMax) < 0.5
      && win.north.view.nMin >= win.b.nMin - 0.5,
      `field N ${Math.round(win.b.nMin)}…${Math.round(win.b.nMax)}; `
      + `at the south edge the window is ${Math.round(win.south.view.nMin)}…`
      + `${Math.round(win.south.view.nMax)}, at the north edge `
      + `${Math.round(win.north.view.nMin)}…${Math.round(win.north.view.nMax)}`);

    // T-0467 — THE SOUTHERN FIELD IS REACHABLE, walked the way a visitor reaches
    // it: through the Go-to viewpoints, in one southward run from the fort to the
    // model's south wall. T-0464 carried the modelled box to Twenty-Second Street
    // and nothing was OFFERED down there — the southernmost viewpoint this scene
    // had was the aerial at n -330, so 3.4 km of modelled ground could only be
    // entered by walking off the edge of the town. Each stop is asserted on the
    // renderer's own samplers rather than on the scene file, because the failure
    // being gated is a camera that lands on ground the renderer does not have:
    // `inBounds` false is the constant outside the box, `isWater` true is the
    // lake, and the pre-fill shore crosses 390 m of easting on the way down, so
    // an easting that is dry at one row is in the water at another.
    // tools/measure_anchors.mjs holds the same property offline at commit; this
    // holds it in the running page, which is where a visitor meets it.
    const southRun = await page.evaluate(() => {
      const api = window.__chicago4d;
      const ids = ['fort_dearborn', 'lake_shore_south', 'sixteenth_prairie',
        'battle_reach_1812', 'eighteenth_prairie', 'cermak_prairie'];
      const stops = ids.map((id) => {
        const went = api.goTo(id);
        api.step();
        const p = api.player;
        const a = api.scene.anchors.find((x) => x.id === id);
        const s = api.navigation.snapshot();
        return {
          id,
          went,
          label: a?.label ?? null,
          offAnchor: a ? +Math.hypot(p.e - a.local_e, p.n - a.local_n).toFixed(2) : null,
          inBounds: api.terrain.inBounds(p.e, p.n),
          wet: api.terrain.isWater(p.e, p.n),
          ground: +api.terrain.surfaceHeight(p.e, p.n).toFixed(3),
          flying: p.flying,
          // The window travels with them all the way down, and stays a window.
          view: { nMin: +s.viewport.nMin.toFixed(1), nMax: +s.viewport.nMax.toFixed(1) },
        };
      });
      const bounds = api.navigation.snapshot().bounds;
      // Hand the walker back, as the reading above does.
      api.walker.teleport({ local_e: 180, local_n: 90, yaw_deg: 225 });
      api.step();
      return { stops, bounds };
    });
    const badStop = southRun.stops.filter(
      (st) => !st.went || st.offAnchor > 1 || !st.inBounds || st.wet || st.flying);
    check(`${label}: every southern viewpoint is reachable and stands on dry modelled ground`,
      southRun.stops.length === 6 && badStop.length === 0,
      badStop.length
        ? badStop.map((st) => `${st.id}: went ${st.went}, ${st.offAnchor} m off the anchor, `
          + `inBounds ${st.inBounds}, wet ${st.wet}, ground ${st.ground} m, flying ${st.flying}`).join('; ')
        : southRun.stops.map((st) => `${st.id} at ${st.ground} m`).join(', '));
    // The run is a TRAVERSE and not six teleports to the same place: it goes
    // south monotonically, and it ends on the far wall of the field the ground
    // ticket built rather than somewhere in the middle of it.
    const southmost = southRun.stops[southRun.stops.length - 1];
    const descends = southRun.stops.every(
      (st, i) => i === 0 || st.view.nMin <= southRun.stops[i - 1].view.nMin);
    check(`${label}: the run carries the visitor south to the model's own wall, and the map follows`,
      descends && Math.abs(southRun.bounds.nMin - (-3800)) < 1
      && southmost.id === 'cermak_prairie'
      && Math.abs(southmost.view.nMin - southRun.bounds.nMin) < 1,
      `field N ${Math.round(southRun.bounds.nMin)}…${Math.round(southRun.bounds.nMax)}; `
      + `window nMin ${southRun.stops.map((st) => st.view.nMin).join(' → ')}`);

    // The other half of the bargain: the whole field is still reachable, it has
    // just moved to a pop-out. This is where "renders the whole heightfield"
    // now lives. Opened through the real control with a real hit test, because
    // the opener is a transparent button laid over the inset and "covered by
    // something else" is exactly how that fails.
    await clickChrome('#overview-open');
    const pop = await page.evaluate(() => {
      const api = window.__chicago4d;
      const el = document.getElementById('overview-full');
      const c = document.getElementById('overview-full-canvas');
      const box = c.getBoundingClientRect();
      const p = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
      let ink = 0;
      for (let i = 3; i < p.length; i += 404) if (p[i] > 0) ink++;
      return {
        open: !el.hasAttribute('hidden'),
        apiOpen: api.navigation.fullOpen,
        w: Math.round(box.width),
        h: Math.round(box.height),
        onScreen: box.width > 0 && box.height > 0
          && box.top >= -1 && box.bottom <= window.innerHeight + 1,
        ink,
        foot: document.getElementById('overview-full-foot')?.textContent?.trim() ?? '',
        focus: document.activeElement?.id ?? '',
      };
    });
    const fieldAspect = (win.b.nMax - win.b.nMin) / (win.b.eMax - win.b.eMin);
    check(`${label}: the pop-out renders the whole heightfield`,
      pop.open && pop.apiOpen && pop.ink > 0 && pop.onScreen
      && Math.abs(pop.h / pop.w - fieldAspect) < 0.05
      // The foot says how far across the field is, in the visitor's own units —
      // `formatDistance` abbreviates, so this reads the abbreviations it emits
      // rather than the words it does not ("1.3 mi", not "1.3 miles").
      && /\b(ft|feet|yd|mi|miles?)\b/.test(pop.foot),
      `${pop.w}x${pop.h} px, aspect ${(pop.h / pop.w).toFixed(3)} against the field's `
      + `${fieldAspect.toFixed(3)}, ${pop.ink} inked samples, foot ${JSON.stringify(pop.foot)}`);
    await page.keyboard.press('Escape');
    const shut = await page.evaluate(() => ({
      hidden: document.getElementById('overview-full').hasAttribute('hidden'),
      apiOpen: window.__chicago4d.navigation.fullOpen,
      focus: document.activeElement?.id ?? '',
    }));
    check(`${label}: Escape puts the pop-out away and hands focus back to the map`,
      shut.hidden && !shut.apiOpen && shut.focus === 'overview-open',
      `hidden ${shut.hidden}, api ${shut.apiOpen}, focus ${JSON.stringify(shut.focus)} `
      + `(was ${JSON.stringify(pop.focus)} while open)`);
    // And the settings toggle owns BOTH of them: a pop-out standing over a map
    // the visitor has switched off is the setting not being obeyed.
    const offWhileHidden = await page.evaluate(() => {
      const api = window.__chicago4d;
      api.navigation.setMapVisible(false);
      const refused = api.navigation.setFullVisible(true);
      const state = {
        refused,
        hidden: document.getElementById('overview-full').hasAttribute('hidden'),
      };
      api.navigation.setMapVisible(true);
      return state;
    });
    check(`${label}: the pop-out cannot be opened while the map is switched off`,
      offWhileHidden.refused === false && offWhileHidden.hidden,
      `setFullVisible answered ${offWhileHidden.refused}, `
      + `overlay hidden ${offWhileHidden.hidden}`);

    // (The street-layer reading that lived here moved above the stage split —
    // T-0060 — because its checks span stages 3 and 4.)
    check(`${label}: earth streets are populated and draped on the rendered ground`,
      streetLayer.records >= 17 && streetLayer.vertices > 1000
      && streetLayer.worstDrape < 1e-5 && streetLayer.wetVertices === 0,
      `${streetLayer.records} streets, ${streetLayer.vertices} vertices, `
      + `drape ${streetLayer.worstDrape}, wet ${streetLayer.wetVertices}`);
    // R-BUG4. Every panel whose centreline is dry must reach the ribbon — the
    // only panels allowed to go missing are those clipped below a walkable
    // width, and they are counted rather than assumed to be few.
    check(`${label}: no panel of road is deleted because its EDGE reached the water`,
      streetLayer.emittedQuads === streetLayer.dryCentrelinePanels - streetLayer.slivers
      && streetLayer.clippedPanels > 0,
      `${streetLayer.emittedQuads} panels drawn of ${streetLayer.dryCentrelinePanels} `
      + `with a dry centreline — ${streetLayer.clippedPanels} clipped at the waterline, `
      + `${streetLayer.slivers} dropped as narrower than a metre`);
    // T-0713. The platted streets are `attested` from the Thompson plat and
    // every record in the file still grades its wear `reconstructed`, so under
    // the old Math.max() composition the whole platted town drew as invention.
    // This asserts the split reached the geometry the browser built: the ribbon
    // channel stands at `attested` for the seventeen platted streets, and the
    // grade that is NOT about whether the street was there rides its own
    // channel instead of pulling the road down with it.
    check(`${label}: the platted streets reach the picture as attested, not as invention`,
      streetLayer.streetGrades.attested.length >= 17
      && streetLayer.streetChannels.ribbon.attested > 0
      && streetLayer.streetChannels.ribbon.attested
         > streetLayer.streetChannels.ribbon.reconstructed,
      `${streetLayer.streetGrades.attested.length} attested lines, `
      + `${streetLayer.streetGrades.inferred.length} inferred `
      + `(${streetLayer.streetGrades.inferred.join(', ') || 'none'}), `
      + `${streetLayer.streetGrades.reconstructed.length} reconstructed `
      + `(${streetLayer.streetGrades.reconstructed.join(', ') || 'none'}) — `
      + `ribbon vertices ${JSON.stringify(streetLayer.streetChannels.ribbon)}`);
    // The other half, and it is the half that would fail silently: the track
    // grade must be CARRIED, on its own channel, on every street mesh and at
    // the same vertex count as the ribbon's. A missing attribute arrives at the
    // shader unbound, which is not reliably zero — it can be NaN, and NaN reads
    // as `attested` after a clamp. So absence is a failure here, not a default.
    check(`${label}: surface and wear ride their own channel and every street carries it`,
      streetLayer.streetChannels.meshes > 0
      && streetLayer.streetChannels.missingTrack === 0
      && streetLayer.streetChannels.unequal === 0
      && streetLayer.streetChannels.track.reconstructed > 0
      && streetLayer.streetChannels.track.attested === 0,
      `${streetLayer.streetChannels.meshes} street mesh(es), `
      + `${streetLayer.streetChannels.missingTrack} without a track channel, `
      + `${streetLayer.streetChannels.unequal} of unequal length — `
      + `track vertices ${JSON.stringify(streetLayer.streetChannels.track)}, `
      + `${streetLayer.streetGrades.wornInvented} record(s) grade a surface or wear invented`);
    // T-0110. Vertex drape above says every vertex touches the ground; this
    // says the ground stays UNDER the ribbon between them. The 0.35 bar is
    // documented at the probe: measured worst after refinement is 0.21 m
    // (two waterline nose tips), the failure class it guards is 0.9–1.5 m.
    check(`${label}: the ground never rises through a road panel between its vertices`,
      streetLayer.worstSink < 0.35 && streetLayer.refinedPanels > 0,
      `worst interior sink ${streetLayer.worstSink.toFixed(3)} m, `
      + `${streetLayer.refinedPanels} refined panels`);
    check(`${label}: the worn track runs onto each bridge approach and meets the deck`,
      streetLayer.approachGaps.length === 0,
      streetLayer.approachGaps.length
        ? `uncovered stations: ${streetLayer.approachGaps.join(', ')}`
        : 'every approach station lands on drawn roadway');
    // T-0184. Stations inside the sector on the OUTSIDE of every authored bend —
    // the wedge of prairie a square joint opened, 23.47 m2 town-wide before the
    // mitre. `squareJoints` is asserted at zero beside it because the module is
    // allowed to give up on a hairpin it cannot mitre, and a town where every
    // bend had quietly fallen through that guard would still have stations to
    // pass if they were the only thing read here.
    check(`${label}: no bend in the ribbon opens a wedge on the outside of its turn`,
      streetLayer.jointGaps.length === 0 && streetLayer.jointStations > 100
      && streetLayer.squareJoints === 0 && streetLayer.mitredJoints > 0,
      streetLayer.jointGaps.length
        ? `uncovered: ${streetLayer.jointGaps.slice(0, 6).join('; ')}`
        : `${streetLayer.jointStations} stations across ${streetLayer.joints} joints — `
          + `${streetLayer.mitredJoints} mitred, ${streetLayer.fannedJoints} cut into `
          + `sub-mitres for ${streetLayer.jointFanTriangles} triangles, `
          + `${streetLayer.squareJoints} left square`);
    check(`${label}: no elevated flora sheet can masquerade as a second terrain layer`,
      streetLayer.canopyPresent === false,
      `flora-canopy present ${streetLayer.canopyPresent}`);

    // R-BUG2. Draped is not seen: every assertion above passed while the roads
    // were invisible. See `roadContrast()` for what this measures and why.
    // R-BUG3 added the third station and the near band, and moved the gating
    // test from "enough probes were SEEN" to "enough probes were PROJECTED" —
    // under the old test a band nobody can see reports n=0 and gates itself
    // out, which is indistinguishable from a band with no road in it.
    // R-M1c finished that argument one level down: the band's SCORE divided by
    // `seen` too, so an occluder raised it. It divides by `nBare` now.
    // T-0173. The first two stations are part 7's; the third is part 8's, and
    // the movement report each part prints covers the stations that part read.
    await readRoadStations(page, label, ROAD_STATIONS.filter((st) => st.part === 7));

    inStageWork = false;
    } // end PART 7 (T-0060 stage 3a, cut by T-0121; renumbered by T-0346, halved by T-0173)
    // PART 8 — the crossing station, the road-legibility aid and the batch merge
    // the aid's reach stands on: the tail T-0173 cut out of part 7 when the three
    // road-legibility stations alone came to 7 m 04 s of a 9 m 25 s part. The
    // three assertions of R-A1 are taken STANDING AT `lake_market`, where the
    // bands were just read, so the station and the aid could not be separated —
    // they are both here, in that order, exactly as they ran before.
    if (stageOn(8)) {
    inStageWork = true;

    // The same prologue part 7 carries, and for the same reason: a fresh boot is
    // still standing at the gate screen, and every check below measures a
    // `page.screenshot` frame that includes the DOM overlays. In a full run this
    // is a no-op — part 6 entered the town long ago.
    await enterTown();

    await readRoadStations(page, label, ROAD_STATIONS.filter((st) => st.part === 8));

    // --- R-A1, the road-legibility aid, and the three things it owes --------
    //
    // The aid is a viewing accommodation. Every band printed above measures the
    // DEFAULT, and the whole reason this control was deferred for two days is
    // that a preference which boosts road contrast can quietly become a way to
    // launder a failing gate. So the aid owes three assertions and they are
    // taken HERE, standing at `lake_market` where the bands were just read:
    //
    //   1. it is OFF with no stored preference — so every number above, and
    //      every figure `critic_shots.mjs` and `light_probe.mjs` take, is the
    //      recorded surface and not a visitor's dial;
    //   2. raising it CHANGES the frame — because a control that reaches
    //      nothing reports "no effect" for the same reason a broken thermometer
    //      reports a steady temperature. R-BUG1's `--no-sun-shadow` cleared a
    //      suspect it never touched; the instrument is proved before it is
    //      quoted, not after;
    //   3. dropping it back RESTORES the frame — which is what makes 1 and 2
    //      compatible: the aid's existence changes no default.
    const aidAtBoot = await page.evaluate(() => window.__chicago4d.roadAid);
    check(`${label}: the road-legibility aid is off unless a visitor moves it`,
      aidAtBoot === 0, `uRoadAid ${aidAtBoot} with no stored preference`);

    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    // T-0690. ROAD_AID_REACH_GRID, not the 48² the three assertions further down
    // share: at 390×780 a 48² cell dilutes the roadway until the aid's worst cell
    // reads 3 against a floor of 4, and the same frame at 96² reads 7. Its box
    // carries the sweep both readings come from.
    const aidOff = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_REACH_GRID);
    const aidOff12 = await page.evaluate(() => window.__chicago4d.capture());
    const aidSet = await page.evaluate(() => window.__chicago4d.setRoadAid(1));
    // K24. The raised READING, which until now this suite never took: both of
    // the assertions around this one expect 0, so a frozen readback satisfied
    // them and only a value that is meant to MOVE can find that out. See
    // main.js § Live getters.
    const aidLive = await page.evaluate(() => window.__chicago4d.roadAid);
    const aidOn = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_REACH_GRID);
    const aidOn12 = await page.evaluate(() => window.__chicago4d.capture());
    const dAid = signatureDistance(aidOff, aidOn);
    const dAid12 = signatureDistance(aidOff12, aidOn12);
    await page.evaluate(() => window.__chicago4d.setRoadAid(0));
    const aidBack = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_REACH_GRID);
    const dAidBack = signatureDistance(aidOff, aidBack);
    const aidRestored = await page.evaluate(() => window.__chicago4d.roadAid);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));

    check(`${label}: raising the road-legibility aid reaches the render`,
      aidSet === 1 && aidLive === 1
      && dAid.worst >= ROAD_AID_MIN_WORST && dAid.mean >= ROAD_AID_MIN_MEAN,
      `set to ${aidSet}, reads back ${aidLive}: cell delta mean ${dAid.mean?.toFixed(2)}, `
      + `worst ${dAid.worst} (need worst>=${ROAD_AID_MIN_WORST}, `
      + `mean>=${ROAD_AID_MIN_MEAN})`);
    // With the clock held these are two captures of one unchanged scene, so an
    // aid that left anything behind shows up as a residual the sway cannot
    // explain. Same tolerance the confidence view is held to, for the same
    // reason: it is readback noise, not weather.
    check(`${label}: dropping the road-legibility aid restores the default frame`,
      aidRestored === 0 && dAidBack.mean <= 0.1 && dAidBack.worst <= 3,
      `uRoadAid ${aidRestored}, residual mean ${dAidBack.mean?.toFixed(2)}, `
      + `worst-cell delta ${dAidBack.worst}`);
    console.log(`        road aid: full-on delta mean ${dAid.mean?.toFixed(2)} / worst `
      + `${dAid.worst} at ${ROAD_AID_REACH_GRID}², ${dAid12.mean?.toFixed(2)} / ${dAid12.worst} `
      + `at 12²; restored residual mean ${dAidBack.mean?.toFixed(2)} / worst `
      + `${dAidBack.worst}`);

    // --- R-W5a2, the batch merge the reach below is standing on -------------
    //
    // Three assertions, and the shape is R-A1's: a count, the channel that count
    // is bought with, and a proof the channel reaches the render. The first two
    // on their own would pass identically on a town that had merged its batches
    // by THROWING ROUGHNESS AWAY — one batch, one finish, every wall the same
    // sheen — which is the failure that matters here and is not a crash.
    const batchCensus = await page.evaluate(() => {
      const bs = window.__chicago4d.buildings.batches;
      const seen = new Set();
      let min = Infinity, max = -Infinity;
      for (const b of bs) {
        const a = b.geometry.getAttribute('_roughness');
        if (!a) continue;
        for (let i = 0; i < a.array.length; i += 1) {
          const v = a.array[i];
          seen.add(v.toFixed(3));
          if (v < min) min = v;
          if (v > max) max = v;
        }
      }
      return { batches: bs.length, values: seen.size, min, max };
    });
    check(`${label}: the untextured town is one batch`,
      batchCensus.batches === STRUCTURE_BATCHES,
      `${batchCensus.batches} structure batch(es), want ${STRUCTURE_BATCHES}`);
    check(`${label}: the batch still carries the town's finishes`,
      batchCensus.values >= ROUGHNESS_VALUES_MIN
        && batchCensus.min <= 0.30 && batchCensus.max >= 0.95,
      `${batchCensus.values} distinct roughness values in the merged batch, `
      + `${batchCensus.min}–${batchCensus.max} (want >=${ROUGHNESS_VALUES_MIN} spanning 0.30–0.95)`);

    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const roughFull = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_GRID);
    await page.evaluate(() => {
      const a = window.__chicago4d.buildings.batches[0].geometry.getAttribute('_roughness');
      window.__chiRoughSaved = a.array.slice();
      a.array.fill(0.02);
      a.needsUpdate = true;
    });
    const roughFlat = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_GRID);
    const dRough = signatureDistance(roughFull, roughFlat);
    await page.evaluate(() => {
      const a = window.__chicago4d.buildings.batches[0].geometry.getAttribute('_roughness');
      a.array.set(window.__chiRoughSaved);
      a.needsUpdate = true;
      delete window.__chiRoughSaved;
    });
    const roughBack = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_GRID);
    const dRoughBack = signatureDistance(roughFull, roughBack);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));

    check(`${label}: the per-vertex roughness channel reaches the render`,
      dRough.worst >= ROUGHNESS_MIN_WORST,
      `driving every vertex to 0.02 moved the worst cell by ${dRough.worst}, `
      + `mean ${dRough.mean?.toFixed(2)} (need worst>=${ROUGHNESS_MIN_WORST})`);
    check(`${label}: restoring the roughness channel restores the frame`,
      dRoughBack.mean <= 0.1 && dRoughBack.worst <= 3,
      `residual mean ${dRoughBack.mean?.toFixed(2)}, worst-cell delta ${dRoughBack.worst}`);
    console.log(`        batches: ${batchCensus.batches} · roughness `
      + `${batchCensus.values} values ${batchCensus.min}–${batchCensus.max} · flattening moves `
      + `worst cell ${dRough.worst}, mean ${dRough.mean?.toFixed(2)}; restored worst `
      + `${dRoughBack.worst}`);

    inStageWork = false;
    } // end PART 8 (the tail of T-0060 stage 3a, cut out of part 7 by T-0173)
    // PART 9 — the facade tones, the shadow reach, the shadow box and the K24
    // brightness aid: the camera-heavy tail of T-0060's stage 3, and every
    // check in it measures a page.screenshot frame. So it enters the town on
    // its own account, and it holds no reference to the shared street reading —
    // which is why that reading is now gated on parts 7 and 9 alone.
    if (stageOn(9)) {
    inStageWork = true;
    await enterTown();

    // --- T-0002, the facade tones ------------------------------------------
    //
    // The owner's report was that the buildings "read as freshly painted and
    // identical", and the second half was exact: a wall took its colour from
    // its ARCHETYPE, so two neighbours of the same archetype were the same
    // brown to the bit — 10 of 321 adjacent pairs, measured.
    //
    // Four assertions, and they are shaped by R-A1's finding and K24's. The
    // census and the invariant say the town wears many faces; the INERTNESS
    // assertion says the two records a source speaks for were not touched, to
    // the bit; and the liveness pair says the difference reaches a pixel and
    // comes back. The first two would pass identically on a tone that never
    // left its array, which is exactly the failure R-A1's dead readback was.
    const facades = await page.evaluate(() => {
      const api = window.__chicago4d;
      const tones = api.buildings.facadeTones();
      return Object.entries(tones).map(([id, t]) => {
        const p = api.buildings.positionOf(id);
        return {
          id, drawn: t.drawn, eligible: t.eligible, confidence: t.confidence,
          x: p ? p.x : null, z: p ? p.z : null,
        };
      });
    });
    const facadeLum = (c) => 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
    const facadeDrawn = facades.filter((r) => r.drawn);
    const facadeTones = new Set(
      facadeDrawn.map((r) => r.drawn.map((v) => v.toFixed(6)).join(','))).size;
    const facadePlaced = facadeDrawn.filter((r) => Number.isFinite(r.x));
    let facadeTwins = 0;
    let facadePairs = 0;
    for (const a of facadePlaced) {
      let best = null;
      let bd = Infinity;
      for (const b of facadePlaced) {
        if (b === a) continue;
        const d = Math.hypot(a.x - b.x, a.z - b.z);
        if (d < bd) { bd = d; best = b; }
      }
      if (best && bd <= FACADE_PAIR_M) {
        facadePairs += 1;
        if (Math.abs(facadeLum(a.drawn) - facadeLum(best.drawn)) < 1e-6) facadeTwins += 1;
      }
    }
    const attested = facades.filter((r) => r.confidence === 'attested');

    // THE VIEW THIS CHECK REQUIRES (T-0848): the boot pose. The three captures
    // below are a delta measurement, and its floor — worst cell >=3, mean >=0.03
    // — was measured from there. Taken from the South Division stand that part
    // 10's street reading leaves behind, the same unchanged town moves the worst
    // cell by 2, because far fewer painted walls are in frame. So the pose is
    // part of the assertion and is taken here, not inherited.
    await standAtBootPose();
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const toneOn = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_GRID);
    const toneOff = await page.evaluate(() => window.__chicago4d.setFacadeWeathering(0));
    const flatFacades = await page.evaluate(() => {
      const t = window.__chicago4d.buildings.facadeTones();
      return Object.fromEntries(Object.entries(t).map(([id, v]) => [id, v.drawn]));
    });
    const toneOffShot = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_GRID);
    const toneBack = await page.evaluate(() => window.__chicago4d.setFacadeWeathering(1));
    const backFacades = await page.evaluate(() => {
      const t = window.__chicago4d.buildings.facadeTones();
      return Object.fromEntries(Object.entries(t).map(([id, v]) => [id, v.drawn]));
    });
    const toneBackShot = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_GRID);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    const dTone = signatureDistance(toneOn, toneOffShot);
    const dToneBack = signatureDistance(toneOn, toneBackShot);

    const facadeMoved = facadeDrawn.filter((r) => {
      const flat = flatFacades[r.id];
      return flat && r.drawn.some((v, i) => Math.abs(v - flat[i]) > 1e-6);
    }).length;
    const attestedMoved = attested.filter((r) => {
      const flat = flatFacades[r.id];
      return r.drawn && flat && flat.some((v, i) => v !== r.drawn[i]);
    });
    const restoreError = Math.max(0, ...facadeDrawn.map((r) => {
      const back = backFacades[r.id];
      return back ? Math.max(...r.drawn.map((v, i) => Math.abs(v - back[i]))) : 0;
    }));

    check(`${label}: the town wears more than one face`,
      facadeTones >= FACADE_TONES_MIN,
      `${facadeTones} distinct drawn facade tones across ${facadeDrawn.length} `
      + `structures (want >=${FACADE_TONES_MIN})`);
    check(`${label}: no two neighbouring buildings are drawn the same colour`,
      facadePairs > 0 && facadeTwins === 0,
      `${facadeTwins} of ${facadePairs} nearest-neighbour pairs within `
      + `${FACADE_PAIR_M} m are drawn identically (want 0)`);
    // The honesty half of this parcel, and the one assertion here that must
    // never be relaxed: `facades.js` hands an attested paint the identity tone,
    // so a record a source speaks for is drawn at the colour its archetype
    // baked whether the tone is on or off. Bit-exact, not close.
    check(`${label}: a documented paint is never modulated`,
      attested.length >= 1 && attestedMoved.length === 0,
      `${attested.length} record(s) with attested paint, ${attestedMoved.length} `
      + `changed when the tone was wound off (want 0): `
      + `${attested.map((r) => r.id).join(', ') || 'none found'}`);
    check(`${label}: the facade tones reach the render`,
      toneOff === 0 && facadeMoved >= FACADE_MOVED_MIN
        && dTone.worst >= FACADE_MIN_WORST && dTone.mean >= FACADE_MIN_MEAN,
      `winding the tone off changed ${facadeMoved} structure(s) (want >=${FACADE_MOVED_MIN}) `
      + `and moved the worst cell by ${dTone.worst}, mean ${dTone.mean?.toFixed(2)} `
      + `(need worst>=${FACADE_MIN_WORST}, mean>=${FACADE_MIN_MEAN})`);
    check(`${label}: restoring the facade tones restores the frame`,
      toneBack === 1 && restoreError <= 1e-6
        && dToneBack.mean <= 0.1 && dToneBack.worst <= 3,
      `weathering ${toneBack}, worst per-structure restore error `
      + `${restoreError.toExponential(2)}, residual mean ${dToneBack.mean?.toFixed(2)}, `
      + `worst-cell delta ${dToneBack.worst}`);
    console.log(`        facades: ${facadeTones} tones · ${facadeTwins}/${facadePairs} `
      + `neighbour pairs identical · winding off moves worst cell ${dTone.worst}, `
      + `mean ${dTone.mean?.toFixed(2)}; restored worst ${dToneBack.worst}`);

    // --- R-W3b(a), the shadow reach, and the liveness assertion it owes -----
    //
    // The rig is one orthographic box that follows the visitor, and its reach
    // decides how much of the town can cast a shadow AT ALL: at the old ±60 m,
    // measured at eight anchors on the published mirror, 5 to 8 of 331
    // structures and 0 to 41 of 730 stems were inside it. Everything else met
    // the ground with nothing under it.
    //
    // Two assertions, and the second is the one R-A1 says the first cannot do
    // without: the rig CARRIES the documented reach at the documented texel
    // size, and winding the reach back to the old ±60 m CHANGES the frame. A
    // reach wired to nothing passes the first on its own.
    //
    // T-0115: the rig the level asks for, not one rig. The reach and the map
    // both step at `light`, and `shadowRigFor` above holds the pair — so the
    // texel this asserts is the SAME number at either level, which is the
    // claim. `restored` below winds back to THIS level's reach rather than to
    // 240, or the phone (which boots at `light`) would be asked to restore a
    // frame it never drew.
    const rigLevel = await page.evaluate(() => window.__chicago4d.detail);
    const rig = await page.evaluate(() => window.__chicago4d.world.shadowRig);
    const want = shadowRigFor(rigLevel, touch);
    check(`${label}: the sun's shadow reaches ${want.reachM} m at the documented texel `
      + `(scene detail '${rigLevel}')`,
      rig.reachM === want.reachM && rig.mapSize === want.mapSize,
      `±${rig.reachM} m over a ${rig.mapSize}² map = ${(rig.texelM * 100).toFixed(1)} cm `
      + `per texel (want ±${want.reachM} m over ${want.mapSize}² = `
      + `${(want.texelM * 100).toFixed(1)} cm)`);

    // THE VIEW THIS CHECK REQUIRES (T-0848): the boot pose again, and re-taken
    // rather than assumed to have survived the facade section — the same reason.
    // `worst >= 4` is a number about how much of the town the rig can reach IN
    // FRAME; from a stand with little standing behind the visitor, winding the
    // reach from its documented value back to +/-60 m moves almost nothing and
    // the check silently becomes an assertion about the previous section.
    await standAtBootPose();
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const reachFull = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_GRID);
    const woundBack = await page.evaluate(() => window.__chicago4d.world.setShadowReach(60));
    const reachOld = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_GRID);
    const dReach = signatureDistance(reachFull, reachOld);
    const restored = await page.evaluate(
      (m) => window.__chicago4d.world.setShadowReach(m), want.reachM);
    const reachBack = await page.evaluate((g) => window.__chicago4d.capture(g), ROAD_AID_GRID);
    const dReachBack = signatureDistance(reachFull, reachBack);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));

    check(`${label}: the shadow reach reaches the render`,
      woundBack === 60 && dReach.worst >= SHADOW_REACH_MIN_WORST,
      `winding ±${want.reachM} m back to ±60 m moved the worst cell by `
      + `${dReach.worst}, mean ${dReach.mean?.toFixed(2)} `
      + `(need worst>=${SHADOW_REACH_MIN_WORST})`);
    check(`${label}: restoring the shadow reach restores the frame`,
      restored === want.reachM && dReachBack.mean <= 0.1 && dReachBack.worst <= 3,
      `±${restored} m, residual mean ${dReachBack.mean?.toFixed(2)}, `
      + `worst-cell delta ${dReachBack.worst}`);
    console.log(`        shadow reach: ±${rig.reachM} m at `
      + `${(rig.texelM * 100).toFixed(1)} cm/texel · winding back to ±60 m moves `
      + `worst cell ${dReach.worst}; restored residual worst ${dReachBack.worst}`);

    // --- R-BUG6, the shadow box moves in whole texels -----------------------
    //
    // The box follows the visitor. A shadow map is a raster fixed to that box,
    // so re-centring it on their exact position slid the sample lattice by a
    // fraction of a texel every frame and re-quantised every shadow edge in the
    // scene — the crawl along an eave line, and 14–16 % of the whole-frame
    // flicker `tools/measure_river_edge.mjs` catches under a 2 mm nudge.
    //
    // The invariant is exact, so it is asserted exactly rather than through a
    // pixel signature: two positions a MILLIMETRE apart must put the shadow box
    // in the same place to the bit. The equality is computed here, off
    // `light.target.position`, which is the input three itself builds the shadow
    // camera from — not off a reading the module makes about itself (K24).
    //
    // And it is asserted in BOTH directions, which is R-A1's lesson: "the box
    // did not move" passes identically on a rig that snaps and on a rig whose
    // follow() was never called, so the same millimetre with the snap OFF has to
    // move it. The whole-texel half is the third: walk a long way and the box
    // must land on the lattice, which is what says the quantisation is
    // world-anchored rather than a copy of the walker.
    const snapProbe = await page.evaluate((texel) => {
      const api = window.__chicago4d;
      const d = api.world.direction;
      // `follow` is what the render loop calls every frame with the visitor's
      // world position, so it is asked directly: no teleport and no capture, and
      // the next drawn frame re-centres the box on the real walker anyway.
      const centreAt = (x, z) => {
        api.world.follow({ x, y: 0, z });
        const t = api.world.light.target.position;
        return { x: t.x, y: t.y, z: t.z };
      };
      /**
       * THE DISTANCE THAT MATTERS IS ACROSS THE MAP, NOT ALONG THE SUN.
       *
       * The box is snapped on the two axes of the shadow map and deliberately not
       * on the third: the centre keeps the walker's own component along the sun's
       * direction, so it still slides by a tenth of a millimetre per millimetre
       * walked (measured). That slide cannot re-quantise anything — an
       * orthographic camera moved along its own view axis rasterises every world
       * point to the identical texel, and the depth it writes and the depth it
       * compares against shift together. So the perpendicular component is the
       * claim, and asserting the raw distance instead would have failed a correct
       * rig: it did, first time, at 0.107 mm.
       */
      const acrossMap = (p, q) => {
        const v = { x: p.x - q.x, y: p.y - q.y, z: p.z - q.z };
        const along = v.x * d.x + v.y * d.y + v.z * d.z;
        return Math.hypot(v.x - along * d.x, v.y - along * d.y, v.z - along * d.z);
      };
      // A millimetre: 1/117 of a desktop texel, and three orders of magnitude
      // under anything the walker's own stride resolves.
      const a = centreAt(107, 103);
      const snappedStep = acrossMap(a, centreAt(107.001, 103));
      // The lattice PITCH, measured from outside and without the light's basis.
      // Walk a metre in millimetres: each step can cross at most one lattice
      // line of each axis, so every move the box makes across its map is one
      // texel — or, if both axes cross on the same millimetre, a texel diagonal.
      // Nothing else is possible on a lattice of this pitch, so the set of jump
      // lengths IS the claim, and zero jumps would mean a box that never moves.
      const jumps = [];
      let prev = a;
      for (let mm = 1; mm <= 1000; mm++) {
        const c = centreAt(107 + mm / 1000, 103);
        const j = acrossMap(prev, c);
        if (j > 1e-9) jumps.push(j);
        prev = c;
      }
      const wasOn = api.world.shadowRig.snapped;
      api.world.setShadowSnap(false);
      const loose = centreAt(107, 103);
      const looseStep = acrossMap(loose, centreAt(107.001, 103));
      api.world.setShadowSnap(wasOn);
      const onLattice = jumps.every((j) => Math.abs(j - texel) < 1e-6
        || Math.abs(j - texel * Math.SQRT2) < 1e-6);
      return {
        snappedStep,
        looseStep,
        jumps: jumps.length,
        worstJumpTexels: jumps.length ? Math.max(...jumps.map((j) => j / texel)) : 0,
        onLattice,
        snapped: api.world.shadowRig.snapped,
      };
    }, rig.texelM);
    check(`${label}: the shadow box holds still under a sub-texel step`,
      snapProbe.snapped === true && snapProbe.snappedStep < 1e-9,
      `a 1 mm walk moved the box ${(snapProbe.snappedStep * 1e6).toFixed(3)} µm across its `
      + `map (texel ${(rig.texelM * 1000).toFixed(1)} mm); snapped=${snapProbe.snapped}`);
    check(`${label}: the snap reaches the box — without it the same step moves it`,
      snapProbe.looseStep > 0.0009,
      `with the snap off a 1 mm walk moves the box `
      + `${(snapProbe.looseStep * 1000).toFixed(3)} mm across its map (want >0.9)`);
    check(`${label}: the box moves in texels of its own map, and only in those`,
      snapProbe.jumps > 0 && snapProbe.onLattice,
      `a 1 m walk moved the box ${snapProbe.jumps} time(s), worst jump `
      + `${snapProbe.worstJumpTexels.toFixed(4)} texels of `
      + `${(rig.texelM * 100).toFixed(1)} cm (want every jump 1 or √2)`);
    console.log(`        shadow snap: 1 mm moves the box `
      + `${(snapProbe.snappedStep * 1e6).toFixed(2)} µm snapped, `
      + `${(snapProbe.looseStep * 1000).toFixed(3)} mm loose; a 1 m walk moves it `
      + `${snapProbe.jumps} time(s), worst ${snapProbe.worstJumpTexels.toFixed(3)} texels`);
    // --- K24, the brightness aid, and the same three things it owes ---------
    //
    // Owner-requested, and it carries a fourth assertion the road aid does not
    // need: the grade itself. The road aid moves a uniform on the street
    // materials, so nothing else in the suite can be reached through it; this
    // one moves `toneMappingExposure`, which lights the ground, the water and
    // every documented wall colour at once. That is the whole reason K24 was
    // written as an accommodation rather than a second grade, and the way to
    // hold it there is to assert the calibrated number a gate is standing at,
    // not merely the slider's own bookkeeping. A control that can be used to
    // launder a failing gate has become a different thing.
    const brightAtBoot = await page.evaluate(() => window.__chicago4d.brightness);
    const exposureAtBoot = await page.evaluate(() => window.__chicago4d.exposure);
    check(`${label}: the brightness aid is off unless a visitor moves it`,
      brightAtBoot === 0 && Math.abs(exposureAtBoot - BASE_EXPOSURE) < 1e-6,
      `brightness ${brightAtBoot} stops, exposure ${exposureAtBoot} `
      + `(calibrated ${BASE_EXPOSURE}) with no stored preference`);

    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    const brightOff = await page.evaluate((g) => window.__chicago4d.capture(g), BRIGHT_AID_GRID);
    const brightSet = await page.evaluate(() => window.__chicago4d.setBrightness(1));
    const brightOn = await page.evaluate((g) => window.__chicago4d.capture(g), BRIGHT_AID_GRID);
    const exposureOn = await page.evaluate(() => window.__chicago4d.exposure);
    const dBright = signatureDistance(brightOff, brightOn);
    // Past the ceiling on purpose: the clamp is what keeps "one stop" a bound
    // rather than a suggestion, and an unclamped slider is a way to reach an
    // exposure no gate has ever read.
    const brightClamped = await page.evaluate(() => window.__chicago4d.setBrightness(9));
    await page.evaluate(() => window.__chicago4d.setBrightness(0));
    const brightBack = await page.evaluate((g) => window.__chicago4d.capture(g), BRIGHT_AID_GRID);
    const dBrightBack = signatureDistance(brightOff, brightBack);
    const brightRestored = await page.evaluate(() => window.__chicago4d.brightness);
    const exposureRestored = await page.evaluate(() => window.__chicago4d.exposure);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));

    check(`${label}: raising the brightness aid reaches the render`,
      brightSet === 1 && brightClamped === 1
      && Math.abs(exposureOn - BASE_EXPOSURE * 2) < 1e-6
      && dBright.worst >= BRIGHT_AID_MIN_WORST && dBright.mean >= BRIGHT_AID_MIN_MEAN,
      `set to ${brightSet} stop (9 clamps to ${brightClamped}), exposure ${exposureOn}: `
      + `cell delta mean ${dBright.mean?.toFixed(2)}, worst ${dBright.worst} `
      + `(need worst>=${BRIGHT_AID_MIN_WORST}, mean>=${BRIGHT_AID_MIN_MEAN})`);
    check(`${label}: dropping the brightness aid restores the calibrated frame`,
      brightRestored === 0 && Math.abs(exposureRestored - BASE_EXPOSURE) < 1e-6
      && dBrightBack.mean <= 0.1 && dBrightBack.worst <= 3,
      `brightness ${brightRestored} stops, exposure ${exposureRestored}, `
      + `residual mean ${dBrightBack.mean?.toFixed(2)}, worst-cell delta `
      + `${dBrightBack.worst}`);
    console.log(`        brightness aid: +1 stop delta mean ${dBright.mean?.toFixed(2)} / worst `
      + `${dBright.worst} at ${BRIGHT_AID_GRID}²; restored residual mean `
      + `${dBrightBack.mean?.toFixed(2)} / worst ${dBrightBack.worst}`);

    inStageWork = false;
    } // end PART 9 (T-0060 stage 3b, cut by T-0121; renumbered by T-0346 and T-0173)
    // PART 10 — the flora census through the flower heads: the drawn population,
    // the horizon timber, the sward dealt in every community, the marsh's
    // substrate, T-0035's pop-in and R-BUG7's head-attachment census. The head
    // of T-0060's stage 4a; T-0170 cut the ragged boundary, the ground cover,
    // the street readouts and the Settings units off its tail into part 11,
    // because at 1280x800 the whole of it ran past the ten-minute foreground
    // ceiling and was killed there with two sections still to run.
    //
    // Every binding it shares with earlier parts (`streetLayer`) is read above
    // the split; the teleport below re-establishes the camera pose it expects on
    // its own.
    if (stageOn(10)) {
    inStageWork = true;

    // Same fresh-boot accommodation as stage 3: this stage drives the panel
    // chrome (`#btn-help` first), and while the gate screen stands the chrome
    // has no layout at all — the click waits ninety seconds for a zero-size
    // button and dies. In a full run every branch below is a no-op.
    await enterTown();

    // Put the visitor back where the street checks left them. `from_above` is
    // an AERIAL anchor, and the horizon-timber check further down reads the
    // band the tree solver builds around the camera — from 175 m up there is no
    // band to read, and it reported nought of nought covered bearings. A
    // measurement that moves the camera owes the next one its pose back.
    await page.evaluate(() => {
      const a = window.__chicago4d;
      a.setFly(false);
      a.walker.teleport({ local_e: 107, local_n: -103, yaw_deg: 180 });
      for (let i = 0; i < 3; i++) a.step();
    });
    // The count is an anti-vacuity guard — a run that plants nothing would
    // otherwise report a perfect worst error — and the tolerance below it is
    // the actual assertion. The guard moved from 100 to 50 on 2026-08-13, and
    // the reason is a dataset property rather than a weaker gate: this station
    // stands in the settled town, whose own record says 45 % of its ground is
    // bare and 45 % carries matrix, and that number now reaches the renderer.
    // The mobile cone here holds 67 rooted plants where it held about 150 while
    // every community was planted at prairie density. The 1e-5 m tolerance is
    // untouched.
    check(`${label}: detailed flora roots share the terrain and water surfaces`,
      streetLayer.rootedPlants > 50 && streetLayer.worstPlantRoot < 1e-5,
      `${streetLayer.rootedPlants} roots, worst error ${streetLayer.worstPlantRoot}`);
    check(`${label}: emergent flora stays within eight metres of a riverbank`,
      streetLayer.deepWaterPlants === 0,
      `${streetLayer.waterPlants} water plants, ${streetLayer.deepWaterPlants} in deep water`);
    check(`${label}: woody vegetation never occupies the river mask`,
      streetLayer.treeStations > 10 && streetLayer.wetTreeStations === 0,
      `${streetLayer.treeStations} trees, ${streetLayer.wetTreeStations} wet stations`);
    // The owner photographed a row of gallery trees standing mid-channel while
    // the mask check above was green: the mask's SHORE_Y sits 100 mm below the
    // water plane, so a stem could root under the water and still pass. This
    // asks the question the picture asks — is any stem's foot below the water
    // surface — and it must never be relaxed into the mask test again.
    check(`${label}: no tree stands below the waterline`,
      streetLayer.treeStations > 10 && streetLayer.drownedTreeStations === 0,
      `${streetLayer.drownedTreeStations} of ${streetLayer.treeStations} stations below `
      + `z=${streetLayer.waterY}; lowest station ${streetLayer.lowestTreeStation?.toFixed?.(3)} m, `
      + `${streetLayer.treeRejectedBelowWaterline} candidates rejected at placement`);

    /**
     * ROADMAP R-BUG5b — IS THE WOOD ON THE SCREEN THE WOOD THE STATION LIST
     * DESCRIBES? The question three green gates never asked.
     *
     * Every woody check this project had — the two above, and
     * `tools/measure_far_timber.py` — walks `stations`, the list the planter
     * writes at the moment it decides to plant. `stations` records the point
     * that was TESTED. Nothing anywhere read the geometry back and asked where
     * the tree was DRAWN, so a fault that separates the two was invisible to
     * all of them at once, and one was: the planter handed its ENU north
     * straight to `addTree`, which takes a three world z, and `enuToWorld` is
     * `(e, y, -n)` — so the whole near-field wood was drawn mirrored across the
     * datum's east-west line. 391 stations, 0 wet; 64 of the same 391 wet at
     * their mirror; 10,734 vertices of timber standing over open water, the
     * worst 48 m from the nearest dry ground. That is the owner's line of
     * crowns across the channel, and it survived #196 because #196 fixed the
     * horizon band, which is a different body of timber.
     *
     * So this reads the merged buffers back, converts each vertex to ENU with
     * the project's own `worldToEnu` convention, and asks two things of it:
     *
     *   1. every vertex stands within a crown's reach of SOME station, and
     *   2. no vertex stands over the water mask further than a bank willow can
     *      lean out over it.
     *
     * (1) is the structural half and is what could never have passed through
     * this bug: under the mirror the nearest station to a vertex is twice its
     * own northing away. (2) is the picture half, in the terms the owner
     * reported it. Neither may be relaxed into a test of the placement — that
     * is the test that was already green.
     */
    const drawnWood = await page.evaluate(`(${TIMBER_CENSUS.toString()})()`);
    // T-0243 — WHY THIS IS A MODULE AND NOT THE TRAVERSAL THAT USED TO BE HERE.
    //
    // The traversal matched `/^timber__/`, the four merged quadrant meshes
    // `timber__q0…q3`. T-0223 replaced them with a single `THREE.BatchedMesh`
    // named `timber`, and from that merge the regex matched NOTHING. The first
    // check below went red on its own `meshes > 0` liveness clause, on an
    // unmodified `dev`, so every branch cut from dev inherited a failure it had
    // to argue was not its own. The second one asserts `offshore === 0`, and an
    // empty traversal has zero offshore vertices — so it stayed GREEN, for a
    // fortnight, having asserted nothing whatever about the timber. The green
    // one was the worse half.
    //
    // Pointing the regex at `timber` would not have been the repair. A batch
    // holds every chunk in one pair of buffers with a per-instance transform the
    // batch owns, so the position attribute read through `matrixWorld` is not a
    // chunk's world position: `drawn_timber_census.mjs` walks each instance's
    // own geometry range under its own matrix, the two structures
    // `getBoundingBoxAt()` and `getMatrixAt()` read. It still reads a plain
    // `timber__*` mesh if one appears, so unwinding the batch cannot empty this
    // gate the way landing it did.
    //
    // Both bars come back FROM the census (`strayBarM`, `offshoreBarM`) rather
    // than being written again here. Neither moved: 24 m is the widest crown
    // plus its lean and 12 m is a bank willow leaning over the channel, both
    // argued in T-0110's box, and T-0243 repaired the traversal under them.
    //
    // The liveness clauses are now on BOTH checks, and that is the whole lesson:
    // `chunks`, `verts` and `unreadable` are what make each count an assertion
    // about timber that was walked rather than an assertion about an empty
    // traversal. `tools/measure_drawn_timber.mjs --refute` displaces two chunks
    // of the live scene — one mirrored across the datum, one shoved into open
    // water — and requires this census to report each; a gate of this shape is
    // believed because it can be made to fail, not because it is green.
    check(`${label}: every tree drawn stands at its own station`,
      drawnWood.chunks > 0 && drawnWood.verts > 1000 && drawnWood.stations > 10
      && drawnWood.unreadable === 0 && drawnWood.stray === 0,
      `${drawnWood.stray} of ${drawnWood.verts} vertices further than `
      + `${drawnWood.strayBarM} m from any of ${drawnWood.stations} stations across `
      + `${drawnWood.chunks} chunk(s) in ${drawnWood.batches} batch(es) and `
      + `${drawnWood.plainMeshes} plain mesh(es); worst measurable ${drawnWood.worstStray} m`
      + (drawnWood.worstStrayAt
        ? ` at E ${drawnWood.worstStrayAt.e} N ${drawnWood.worstStrayAt.n}` : '')
      + `, ${drawnWood.outOfHash} beyond the station hash altogether`
      + `; ${drawnWood.unreadable} chunk(s) the census could not read back`);
    // The same liveness clauses guard this one, because THIS is the check that
    // spent a fortnight passing on nothing at all.
    check(`${label}: no timber is drawn out in the channel`,
      drawnWood.chunks > 0 && drawnWood.verts > 1000 && drawnWood.unreadable === 0
      && drawnWood.offshore === 0,
      `${drawnWood.offshore} vertices over water more than ${drawnWood.offshoreBarM} m from `
      + `dry ground (${drawnWood.wet} over water at all, of ${drawnWood.verts} walked in `
      + `${drawnWood.chunks} chunk(s)); worst ${drawnWood.worstOffshore} m`
      + (drawnWood.worstOffshoreAt
        ? ` at E ${drawnWood.worstOffshoreAt.e} N ${drawnWood.worstOffshoreAt.n}` : ''));

    /**
     * ROADMAP K50 — the R-BUG5b question, asked of the two layers it has not
     * been asked of.
     *
     * R-BUG5b was invisible to three green gates because every one of them
     * asked where the wood was DECIDED and none read back where it was DRAWN.
     * Four layers in this renderer decide in ENU and draw in three's world
     * space, and the conversion between them is one sign: `enuToWorld` is
     * `(e, y, -n)`. `flora.js` was measured clean by R-BUG5b itself; the
     * ground is answered twice over — `the drawn ground matches the
     * heightfield the town anchors to` above reads every field sample off the
     * drawn surface, and `tools/measure_terrain_horizontal.mjs` holds its two
     * horizontal axes. That leaves `buildings.js` and `streets.js`, and
     * neither has ever had its geometry read back.
     *
     * What each layer DECIDED is committed and independent of the renderer:
     * a structure's `placement.local_e/local_n` in its sidecar, and a street's
     * `path_local_enu_m`. So both halves below compare the drawn vertices
     * against the DATA, never against another number the renderer computed.
     *
     * The buildings half reads the batch's own position buffer through the
     * instance matrix the renderer will hand the GPU — the same two structures
     * `BatchedMesh.getBoundingBoxAt()` and `getMatrixAt()` read, walked inside
     * the census so the gate needs no THREE in the page. A structure's anchor
     * is its FRONTAGE and the body grows from it (K30(b): 331 of 333 footprints
     * grow from the minimum corner), so the invariant is not "the centre is the
     * anchor" but the weaker, sign-sensitive one: **the anchor lies inside the
     * body's own plan footprint**, to a metre. Under a mirrored northing a
     * building 200 m north of the datum is drawn 400 m from its anchor, which
     * no footprint in this town spans.
     *
     * TWO THINGS THIS GATE MEASURED ABOUT ITSELF BEFORE IT MEASURED THE TOWN,
     * and both are in `drawn_placement_census.mjs` where the code is:
     *
     *   1. **a per-INSTANCE box is not a building.** A structure joins one
     *      batch per material it uses, so the first reading compared 1,310
     *      "bodies" for a town of 331 structures and reported 279 strays — one
     *      body's walls judged without its roof. `instanceBounds()` warns about
     *      exactly this in its own comment. The census unions per structure id.
     *   2. **the mirror test does not discriminate on a street grid.** Asking
     *      whether a road vertex is nearer to a street at its mirrored northing
     *      answered "yes" for 3,975 of 19,372 vertices on a build where every
     *      vertex is inside its own track, because a reflected point on a grid
     *      lands on another east-west street. It is reported and gates nothing;
     *      what catches a mirrored ribbon is the half-width test, because a
     *      reflected road runs where no centreline is recorded.
     */
    const drawnTown = await page.evaluate(`(${CENSUS.toString()})()`);
    check(`${label}: every building is drawn around the anchor its record gives it`,
      drawnTown.buildings.compared > 200 && drawnTown.buildings.unrecorded === 0
      && drawnTown.buildings.outside === 0 && drawnTown.buildings.mirrorCloser === 0,
      `${drawnTown.buildings.outside} of ${drawnTown.buildings.compared} structures whose own `
      + `anchor falls outside their drawn footprint — unioned from `
      + `${drawnTown.buildings.instances} instances in ${drawnTown.buildings.batches} batches, `
      + `${drawnTown.buildings.verts} vertices read back; worst `
      + `${drawnTown.buildings.worst.toFixed(2)} m`
      + (drawnTown.buildings.worstId ? ` (${drawnTown.buildings.worstId}, span `
        + `${drawnTown.buildings.worstSpan} m)` : '')
      + `; ${drawnTown.buildings.mirrorCloser} nearer to the MIRROR of their anchor`
      + (drawnTown.buildings.worstMirrorId ? ` (${drawnTown.buildings.worstMirrorId})` : '')
      + `; ${drawnTown.buildings.unrecorded} instances with no readable placement`);
    check(`${label}: every panel of road is drawn on a street the data records`,
      drawnTown.streets.verts > 1000 && drawnTown.streets.records >= 17
      && drawnTown.streets.stray === 0,
      `${drawnTown.streets.stray} of ${drawnTown.streets.verts} drawn vertices further than `
      + `half a track from any of ${drawnTown.streets.records} centrelines across `
      + `${drawnTown.streets.meshes} meshes; worst ${drawnTown.streets.worst.toFixed(2)} m`
      + (drawnTown.streets.worstAt
        ? ` at E ${drawnTown.streets.worstAt.e} N ${drawnTown.streets.worstAt.n}` : '')
      + `, ${drawnTown.streets.beyondBounds} off the grid altogether`
      + `; ${drawnTown.streets.mirrorAlsoOnRoad} whose MIRRORED northing is also on a road `
      + '(reported, not gated — see the census header)');

    // ROADMAP R-BUG5, and it is the same picture a third time. The two checks
    // above walk `stations`, which the near-field planter writes and which
    // therefore describes a 632 m square; the owner's line of trees was four
    // hundred metres out, in the FAR_TIMBER band, where neither check has ever
    // looked. Both halves are asserted: the solver refused water on this build
    // (a number that would be zero if the clip were removed OR if the run never
    // stood far enough back to reach the belt), and the browser's own census
    // agrees with what `tools/far_timber_baseline.json` banks — the mask the
    // page loaded and the mask in `data/` being the same mask is exactly the
    // R-BUG3c-class assumption that has cost this project two parcels.
    const farTimberWet = (streetLayer.farTimberWater ?? [])
      .filter((b) => b.wet > 0);
    check(`${label}: the horizon band refuses to draw timber over water`,
      streetLayer.horizonWetSkipped > 0
      && farTimberWet.length === FAR_TIMBER_BANKED.length
      && farTimberWet.every((b) => b.wet === FAR_TIMBER_BANKED_BY_ID[b.id]),
      `${streetLayer.horizonWetSkipped} samples clipped at the mask; census `
      + (farTimberWet.map((b) => `${b.id} ${b.wet}/${b.samples} wet, `
        + `${b.worstDepthM.toFixed(3)} m deep`).join(' · ') || 'nothing in water')
      + ` against banked ${JSON.stringify(FAR_TIMBER_BANKED_BY_ID)}`);

    // The horizon timber, in the two ways it was failing to read as timber.
    //
    // (1) COLOUR. The band opts out of the scene fog and out of tone mapping,
    // so it has to be authored where the fogged ground lands — and it was aimed
    // 16 red and 12 green past it, because `trees.js` ran the haze colour
    // through ACES to derive a value the renderer never asks for. This compares
    // the band's own hazed end against `scene.fog.color` rather than against a
    // hex written down in either file, so retargeting the atmosphere cannot
    // silently reopen the break.
    //
    // (2) CONTINUITY. The crown/gap modulation cuts a bearing to as little as
    // 2 % of its height to open sky through a stand. At four hundred metres
    // that is texture; on the dossier's three- to six-mile bodies, whose whole
    // silhouette is one or two pixels, it is a deletion — only 31 % of horizon
    // columns carried any timber at all. The solver now floors the result at a
    // pixel and this asks IT what the modulation did, in its own bins, rather
    // than re-deriving the noise or hunting the band in a screenshot.
    const horizon = await page.evaluate(() => {
      const a = window.__chicago4d;
      const c = a.trees.horizonContinuity();
      return {
        ...c,
        bandHaze: a.trees.hazeTargetHex(),
        fogHex: a.scene3d.fog?.color?.getHex('srgb') ?? null,
        bodies: a.trees.stats.horizonBodies,
        // The live field, so the check below compares the band against the
        // renderer's own viewport rather than against a second copy of main.js's
        // Hor+ arithmetic living in the gate.
        liveHeightCss: a.renderer.domElement.clientHeight,
        liveFovDeg: a.camera.fov,
      };
    });
    const expectedPxPerRad = horizon.liveHeightCss / (horizon.liveFovDeg * Math.PI / 180);
    check(`${label}: the horizon band and the fogged ground converge on one colour`,
      horizon.fogHex !== null && horizon.bandHaze === horizon.fogHex,
      `band haze #${horizon.bandHaze?.toString(16)} against fog #${horizon.fogHex?.toString(16)}`);
    // Anti-vacuity twice over: bodies must be on the horizon at all, and the
    // resolvable count must be a real share of the covered bearings — a solver
    // that silently stopped putting timber up would otherwise report a perfect
    // fraction of nothing.
    //
    // The bar is EVERY resolvable bearing, not a percentage. Measured with the
    // floor removed at the spawn station it fails at both viewports — 251 of
    // 280 mobile and 267 of 281 desktop, worst silhouette 0.18 px and 0.31 px —
    // so a 90 % bar would have passed the desktop half of the defect. A gate
    // whose bar is set below the failure it exists to catch is not a gate.
    check(`${label}: the crown modulation never deletes a resolvable silhouette`,
      horizon.bodies >= 4 && horizon.covered > 100 && horizon.resolvable > 100
      && horizon.drawn === horizon.resolvable
      && horizon.worstResolvablePx >= horizon.minSilhouettePx - 1e-3,
      `${horizon.drawn}/${horizon.resolvable} drawn of ${horizon.covered} covered bearings `
      + `(${(horizon.fraction * 100).toFixed(1)} %), worst `
      + `${horizon.worstResolvablePx?.toFixed?.(2)} px against a floor of `
      + `${horizon.minSilhouettePx} px, at ${horizon.pxPerRad?.toFixed?.(0)} px/rad`);
    // The floor is measured in pixels, so it has to be solved against the
    // viewport the visitor has. A band solved against a hard-coded desktop
    // field would over-cut a phone by 1.75x and this is what says so.
    check(`${label}: the band is solved against this viewport, not a default one`,
      Math.abs(horizon.pxPerRad - expectedPxPerRad) < expectedPxPerRad * 0.02,
      `${horizon.pxPerRad?.toFixed?.(1)} px/rad against ${expectedPxPerRad.toFixed(1)} live `
      + `(${horizon.liveHeightCss} css px over ${horizon.liveFovDeg?.toFixed?.(1)}°)`);

    // --- the drawn population (ROADMAP K48) ---------------------------------

    // THE DRAWN POPULATION — ROADMAP K48, and it is the census K47 found
    // missing. `tools/measure_planting_reach.py` proves a record can be
    // CHOSEN; nothing proved one is DRAWN, and the difference was a whole
    // species: the American sycamore is recorded, archetyped, weighted, banded
    // and gated, and stood NOWHERE in the scene — 0 of 163 stems. A census of
    // what was planted only exists inside a running renderer, so this is a
    // smoke assertion rather than a static scan.
    //
    // The bar is the draw's own two guarantees rather than a percentage, so a
    // renderer that went back to an independent draw fails it on both counts:
    // an independent draw overshoots freely (the gallery elm's 25/116 over 115
    // stems has a standard deviation of 4.4 stems) and it loses the tail (the
    // sycamore's 1.98 came out 0). Anti-vacuity: a census with no planted list,
    // or a list with no species in it, reads as a failure and not as a pass.
    const draws = await page.evaluate(() => (
      window.__chicago4d.trees.stats.draws ?? []
    ).map((d) => ({
      community: d.community,
      list: d.list,
      stems: d.stems,
      species: d.species.map((s) => ({ id: s.id, expected: s.expected, drawn: s.drawn })),
    })));
    const planted = draws.filter((d) => d.stems > 0);
    const absent = [];
    const over = [];
    let worstOver = 0;
    let worstUnder = 0;
    for (const d of planted) {
      for (const s of d.species) {
        const where = `${d.community}.${d.list}.${s.id}`;
        worstOver = Math.max(worstOver, s.drawn - s.expected);
        worstUnder = Math.max(worstUnder, s.expected - s.drawn);
        if (s.drawn === 0 && s.expected >= 1) absent.push(`${where} owed ${s.expected.toFixed(2)}`);
        if (s.drawn - s.expected >= 1) over.push(`${where} ${s.drawn} for ${s.expected.toFixed(2)}`);
      }
    }
    check(`${label}: every species the stand owes a stem to stands in it`,
      planted.length >= 3 && planted.every((d) => d.species.length > 0)
      && absent.length === 0 && over.length === 0,
      `${planted.length} planted list(s), ${planted.reduce((t, d) => t + d.stems, 0)} stems, `
      + `${planted.reduce((t, d) => t + d.species.length, 0)} weighted species; worst `
      + `overshoot ${worstOver.toFixed(2)} stem(s), worst shortfall `
      + `${worstUnder.toFixed(2)}`
      + `${absent.length ? `; DRAWN NOWHERE: ${absent.join(', ')}` : ''}`
      + `${over.length ? `; OVER BY A STEM: ${over.join(', ')}` : ''}`);
    // The species this parcel exists for, named rather than left to the
    // aggregate above: a gate that only reports a count would go green on the
    // day the sycamore came back and say nothing about it.
    const gallery = planted.find((d) => d.community === 'gallery' && d.list === 'mix');
    const sycamore = gallery?.species.find((s) => s.id === 'platanus_occidentalis');
    check(`${label}: the American sycamore stands on the riverbank`,
      !!sycamore && sycamore.drawn >= 1,
      sycamore
        ? `${sycamore.drawn} stem(s) for ${sycamore.expected.toFixed(2)} owed, of `
          + `${gallery.stems} in the gallery`
        : 'no gallery mix census at all');

    // --- the sward, asked what the wood was asked (ROADMAP K49(a)) ---------

    // ROADMAP K49(a) — THE SAME QUESTION, ASKED OF THE SWARD.
    //
    // K48 built the census above for the woody stems, which are 36 of this
    // project's 154 plant records. The other 118 are drawn by `flora.js` off
    // the same shape of weighted draw and had never been counted at all. This
    // counts them, and it reports what the count found rather than gating it,
    // for the reason R-M1 splits a measurement from its bar: the repair needs a
    // per-species footprint the dataset does not carry for 25 records, so a bar
    // set today would either fail over unresearched data or be met with an
    // invented number. K49(b) is the fix and closes `unconvertible` first.
    //
    // What IS gated is that the instrument works: every slot dealt is a slot
    // attributed to a species, and it is counting a populated sward rather than
    // an empty one.
    const sward = await page.evaluate(() => {
      const s = window.__chicago4d.flora.stats;
      return {
        abundance: s.abundance,
        draws: (s.draws ?? []).map((d) => ({
          community: d.community, list: d.list, drawn: d.drawn,
          species: d.species.map((x) => ({
            id: x.id, unit: x.unit, share: x.share, stems: x.stems,
            expected: x.expected, drawn: x.drawn,
          })),
        })),
      };
    });
    const dealt = sward.draws.filter((d) => d.drawn > 0);
    const unattributed = sward.draws.filter(
      (d) => d.species.reduce((t, x) => t + x.drawn, 0) !== d.drawn);
    check(`${label}: every slot the sward deals is counted against a species`,
      dealt.length >= 1 && unattributed.length === 0
      && dealt.every((d) => d.species.length >= 1),
      `${dealt.length} populated list(s) of ${sward.draws.length}, `
      + `${dealt.reduce((t, d) => t + d.drawn, 0)} slots dealt`
      + `${unattributed.length ? `; UNATTRIBUTED in ${unattributed.map((d) => (
        `${d.community}.${d.list}`)).join(', ')}` : ''}`);
    // Reported, not gated — the two numbers K49(b) has to move.
    const ab = sward.abundance ?? { lists: 0, mixed: [], unconvertible: [] };
    const swardAbsent = [];
    for (const d of dealt) {
      for (const x of d.species) {
        if (x.drawn === 0 && x.expected >= 1) {
          swardAbsent.push(`${d.community}.${d.list}.${x.id} owed ${x.expected.toFixed(2)}`);
        }
      }
    }
    console.log(`  note  ${label}: sward abundance — ${ab.mixed.length} of ${ab.lists} lists `
      + `mix an area with a count${ab.mixed.length ? ` (${ab.mixed.map((m) => (
        `${m.zone}.${m.list} ${(m.countedShare * 100).toFixed(1)}% of slots dealt off counts`
      )).join('; ')})` : ''}`);
    console.log(`  note  ${label}: ${ab.unconvertible.length} record(s) give cover with no `
      + `width_m, so no count can be derived without inventing a footprint`
      + `${ab.unconvertible.length ? `: ${ab.unconvertible.map((u) => (
        `${u.zone}.${u.list}.${u.id}`)).join(', ')}` : ''}`);
    // THE TAIL FIGURE HERE IS ABOUT THIS FRAME, AND THAT IS A WARNING LABEL
    // RATHER THAN A CAVEAT. The sward is re-dealt per rebuild, so this answers
    // for the community the gate is standing in — the settled town, 68 slots,
    // one of ten — and from there it reads "0 absent". Run in every community
    // by `tools/measure_sward_draw.mjs` the same census returns SIX species
    // owed a whole plant and drawn nowhere, over 6,780 slots (ROADMAP K49(a)).
    // Quote that tool for a claim about the dataset and this line for a claim
    // about the gate's own frame. The two figures above are dataset-wide and do
    // not move with the camera.
    console.log(`  note  ${label}: sward tail — ${swardAbsent.length} species owed a whole slot `
      + `and drawn nowhere${swardAbsent.length ? `: ${swardAbsent.join(', ')}` : ''}, over `
      + `${dealt.reduce((t, d) => t + d.drawn, 0)} slots in ${dealt.map((d) => (
        `${d.community}.${d.list}=${d.drawn}`)).join(' ')}`);

    // --- and the same sward census in every community (ROADMAP K49(f)) -----

    // ROADMAP K49(f) — AND NOW THE SAME CENSUS IN EVERY COMMUNITY, AS A GATE.
    //
    // The paragraph above is the reason this exists: the tail figure it prints
    // is honest and it is blind, because one station is one community of ten,
    // and the ten do not share a species list. K49(d) handed the matrix lists a
    // fixed grid of `u`, which put wild rice out of the marsh and the prickly
    // pear off the sand prairie in the same commit — and this gate, standing in
    // the settled town, read "0 absent" through all of it.
    //
    // It costs a page.evaluate and no frames: `flora.update` is handed a
    // synthetic camera at a plantable point inside each community in turn, which
    // is what `tools/measure_sward_draw.mjs` does and the same entry point the
    // render loop uses. The camera is put back afterwards, so nothing downstream
    // reads a sward dealt at the last station visited.
    //
    // The bar is ABSOLUTE and it is on the SCENE, not on a station: a species
    // counts as absent only where no station drew it at all while some station's
    // list owed it a whole slot. That is what "drawn nowhere" means, and the
    // distinction is not pedantry — a list is read from more than one community
    // (the wet prairie's is read at four stations), the ring is a few blocks
    // across, and a species owed 1.2 slots in one ring can legitimately take
    // both of them in the next one. The fault this gate exists for is not a
    // station missing a plant; it is a plant that is nowhere. `expected` is the
    // list's own recorded share of the slots dealt, so this asserts the deal
    // against the record rather than against a baseline.
    const everywhere = await page.evaluate(async () => {
      const a = window.__chicago4d;
      const wanted = a.flora.substrates().map((z) => z.id);
      const spots = {};
      for (let e = -900; e <= 1200 && Object.keys(spots).length < wanted.length; e += 6) {
        for (let n = -700; n <= 700; n += 6) {
          const z = a.flora.zoneAt(e, n);
          if (z && !spots[z] && a.flora.plantableAt(e, n)) spots[z] = [e, n];
        }
      }
      const started = a.detail;
      const levels = [];
      for (const level of a.detailOrder) {
        await a.setDetail(level);
        const rows = [];
        for (const [zone, [e, n]] of Object.entries(spots)) {
          const camera = {
            getWorldPosition: (v) => { v.set(e, 1.7, -n); return v; },
            getWorldDirection: (v) => { v.set(0, 0, -1); return v; },
          };
          a.flora.update(0.016, camera);
          a.flora.update(0.016, camera);
          for (const d of a.flora.stats.draws) {
            if (d.drawn <= 0) continue;
            rows.push({
              at: zone,
              community: d.community,
              list: d.list,
              drawn: d.drawn,
              species: d.species.map((s) => ({
                id: s.id, drawn: s.drawn, expected: s.expected,
              })),
            });
          }
        }
        levels.push({ level, rows });
      }
      // Put the visitor's own detail level and the walker's own camera back
      // before anything else reads either.
      await a.setDetail(started);
      if (a.camera) {
        a.flora.update(0.016, a.camera);
        a.flora.update(0.016, a.camera);
      }
      return { spots: Object.keys(spots), levels };
    });
    // Summed over every station, per (community, list, species) — the scene's
    // answer, at one detail level.
    const swardCensus = (rows) => {
      const tally = new Map();
      for (const r of rows) {
        for (const s of r.species) {
          const key = `${r.community}.${r.list}.${s.id}`;
          const t = tally.get(key) ?? { drawn: 0, owed: 0, at: [] };
          t.drawn += s.drawn;
          t.owed = Math.max(t.owed, s.expected);
          if (s.expected >= 1) t.at.push(r.at);
          tally.set(key, t);
        }
      }
      return {
        pairs: tally.size,
        lists: new Set(rows.map((r) => `${r.community}.${r.list}`)).size,
        slots: rows.reduce((t, r) => t + r.drawn, 0),
        nowhere: [...tally.entries()].filter(([, t]) => t.drawn === 0 && t.owed >= 1)
          .map(([k, t]) => `${k} owed ${t.owed.toFixed(2)} at ${t.at.join('/')}`),
      };
    };
    const censuses = everywhere.levels.map((l) => ({ level: l.level, ...swardCensus(l.rows) }));
    const richest = censuses[0] ?? { pairs: 0, lists: 0, slots: 0, nowhere: ['no census taken'] };
    check(`${label}: no sward species its own list owes a plant to is drawn nowhere, `
      + `in ANY community`,
      everywhere.spots.length >= 2 && richest.pairs >= 2 && richest.nowhere.length === 0,
      `${everywhere.spots.length} communities stood in, ${richest.lists} populated list(s), `
      + `${richest.pairs} (list, species) pairs, ${richest.slots} slots dealt at detail `
      + `'${richest.level}'`
      + `${richest.nowhere.length ? `; DRAWN NOWHERE: ${richest.nowhere.join(', ')}` : ''}`);
    // Reported, not gated: the same census at the levels a visitor can turn the
    // scene down to. THE RESIDUAL IS REAL AND IS NAMED RATHER THAN GATED AWAY —
    // at 'light' the wet prairie's prairie dock, owed 1.09 of the 2,670 slots
    // that level deals, can take none. It is the FORB layer, which K49(f) did
    // not touch, and one plant either side of an expectation of 1.09 is a
    // sample rather than an exclusion. Quote the gated line for a claim about
    // the deal, and this one for a claim about what a phone on 'light' shows.
    console.log(`  note  ${label}: sward census by detail — ${censuses.map((c) => (
      `${c.level} ${c.slots} slots, ${c.nowhere.length} drawn nowhere`
      + `${c.nowhere.length ? ` (${c.nowhere.join('; ')})` : ''}`)).join('  ·  ')}`);

    // A pad FLOATS. Both water lilies in the marsh record are `role: emergent`
    // exactly like the cattails, so the placer — which read the role — stood them
    // on the dry marsh edge: 0.01-0.10 m mats rooted in soil, about 7 % of the
    // tufts on that bank. The record's own `appearance` said "floating pads in
    // open water" the whole time, which is prose, and prose is not a gate. The
    // published `substrate` field is, and this asks the placer itself rather than
    // re-deriving its rules: sweep the modelled box and ask where each species
    // may stand. The cattail half is the anti-vacuity guard — a placer that
    // refused everything on that bank would otherwise read as a pass.
    const aquatics = await page.evaluate(() => {
      const a = window.__chicago4d;
      const FLOATING = ['nuphar_advena', 'nymphaea_odorata'];
      const EMERGENT = 'typha_latifolia';
      const seen = { floatingDry: 0, floatingWet: 0, emergentDry: 0, emergentWet: 0 };
      const worst = [];
      for (let e = -320; e <= 660; e += 8) {
        for (let n = -240; n <= 240; n += 8) {
          if (a.flora.zoneAt(e, n) !== 'z04_marsh') continue;
          const wet = a.terrain.isWater(e, n);
          for (const id of FLOATING) {
            if (a.flora.stationOf(e, n, id) === null) continue;
            seen[wet ? 'floatingWet' : 'floatingDry']++;
            if (!wet && worst.length < 4) worst.push(`${id} at ${e},${n}`);
          }
          if (a.flora.stationOf(e, n, EMERGENT) !== null) {
            seen[wet ? 'emergentWet' : 'emergentDry']++;
          }
        }
      }
      const marsh = a.flora.substrates().find((z) => z.id === 'z04_marsh') ?? { dry: [], wet: [] };
      return { ...seen, worst, marshDry: marsh.dry, marshWet: marsh.wet };
    });
    check(`${label}: no floating-leaved aquatic is planted on dry ground`,
      aquatics.floatingDry === 0 && aquatics.floatingWet > 20,
      `${aquatics.floatingDry} dry station(s) [${aquatics.worst.join('; ')}], `
      + `${aquatics.floatingWet} over water`);
    check(`${label}: the marsh's emergents still stand on both sides of its waterline`,
      aquatics.emergentDry > 20 && aquatics.emergentWet > 20,
      `cattail: ${aquatics.emergentDry} dry station(s), ${aquatics.emergentWet} over water`);
    check(`${label}: the marsh community is split by the substrate its records state`,
      !aquatics.marshDry.includes('nymphaea_odorata')
      && aquatics.marshWet.includes('nymphaea_odorata')
      && aquatics.marshDry.includes('typha_latifolia')
      && aquatics.marshWet.includes('typha_latifolia'),
      `dry [${aquatics.marshDry.join(',')}] wet [${aquatics.marshWet.join(',')}]`);

    // --- a plant arrives faint, and at its own height (T-0035) --------------

    // The owner: "grass and flowers appear out of the ground as you walk towards
    // them". The lattice is rebuilt every `step` metres walked and the fade ramp
    // is evaluated per frame, so the ramp has to be inset from the lattice by at
    // least the step — otherwise a plant that was outside the lattice at one
    // rebuild is already well inside the ramp by the next and arrives at a real
    // fraction of its height in a single frame. Two checks: the geometry of the
    // rings, and then an actual walk, which is the one that would have caught it.
    const popIn = await page.evaluate(() => {
      const a = window.__chicago4d;
      const SETS = ['flora-near', 'flora-mid', 'flora-forb', 'flora-rosette', 'flora-shrub'];
      const rings = a.flora.rings;
      const inset = Object.entries(rings.layers).map(([id, r]) => ({
        id,
        // The outer boundary carries a per-slot fringe, so the lattice has to
        // clear the FURTHEST a slot's own ring can stand, not the nominal one.
        // Measuring against the nominal radius would report three metres of
        // margin on the mid ring where a fringed slot has none.
        outer: r.lattice.outer - (r.fade[0] + (r.fringe ?? 0) + rings.step),
        // Only the mid ring HAS an inner ramp; where there is none there is
        // nothing for a plant to grow across on its way past the walker.
        inner: r.fade[3] > 0 ? r.fade[2] - (r.lattice.inner + rings.step) : 0,
      }));

      a.walker.teleport({ local_e: 107, local_n: -103, yaw_deg: 180 });
      a.step();
      const snap = () => {
        const p = a.camera.position;
        const f = p.clone();
        a.camera.getWorldDirection(f);
        const fl = Math.hypot(f.x, f.z) || 1;
        const seen = new Map();
        for (const name of SETS) {
          const mesh = a.flora.group.getObjectByName(name);
          const m = mesh?.instanceMatrix?.array;
          if (!m) continue;
          // Each instance's OWN ring, off the attribute the shader reads. The
          // layer's nominal ring answers for no particular plant once the
          // boundary is fringed, and it answers zero — a free pass — for
          // exactly the plants the fringe pushed furthest out.
          //
          // ALL FOUR NUMBERS, not just the outer radius: since T-0093 the mid
          // ring's INNER boundary is spread per slot too, so a reading that
          // carried only the outer one would ask `fadeAt` about the layer's
          // nominal inner edge and be told every mid card past 4.5 m is drawn —
          // including the ones whose own handover has not reached them yet.
          // `flora.fadeAt` takes the whole ring for this reason.
          const ring = mesh.geometry.getAttribute('aChiRing')?.array;
          for (let i = 0; i < mesh.count; i++) {
            const o = i * 16;
            const e = m[o + 12];
            const n = -m[o + 14];
            seen.set(`${name}|${e.toFixed(3)}|${n.toFixed(3)}`,
              { name, e, n, outer: ring
                ? [ring[i * 4], ring[i * 4 + 1], ring[i * 4 + 2], ring[i * 4 + 3]]
                : undefined });
          }
        }
        return { seen, e: p.x, n: -p.z, fe: f.x / fl, fn: -f.z / fl };
      };

      // Short paces, so the lattice is rebuilt several times inside the walk and
      // never by more than one pace beyond the step it is triggered on.
      const PACE = 0.15;
      const AHEAD = Math.cos(30 * Math.PI / 180);
      let prev = snap();
      let arrivals = 0;
      let worst = 0;
      let worstAt = null;
      // T-0035. The owner's second report on this ring: the flowers "do not fade
      // in as you walk towards, they grow up". The first report was answered by
      // making the ramp smoother; this one is answered by taking it off the
      // geometry, so the reading that settles it is the DRAWN HEIGHT of a plant
      // over the same walk. Two numbers, and neither is asked of ARRIVALS only:
      // the inset means a plant arrives at coverage zero, so an arrival-only
      // reading of its height would be asked of a plant that is not yet drawn
      // and would pass on anything. So: the shortest any plant is drawn at in
      // any frame of the walk, over every plant that is drawn at all, and the
      // most any plant already on screen gains between two frames a pace apart.
      let shortest = 1;
      let shortestAt = null;
      let drawnPlants = 0;
      let grew = 0;
      let grewAt = null;
      for (let k = 0; k < 20; k++) {
        a.walker.teleport({ local_e: prev.e + prev.fe * PACE, local_n: prev.n + prev.fn * PACE });
        a.step();
        const now = snap();
        for (const [key, plant] of now.seen) {
          {
            // Every drawn plant, arriving or not: how much of its own height is
            // it drawn at, this frame, at this distance?
            const d0 = Math.hypot(plant.e - now.e, plant.n - now.n) || 1e-6;
            if (a.flora.fadeAt(plant.name, d0, plant.outer) > 0) {
              const h0 = a.flora.heightAt(plant.name, d0, plant.outer);
              // `<=`, not `<`: the reading has to record that it READ something.
              // With `<` against a starting 1 the shortest plant of a healthy
              // field never sets it, and "no plant was ever drawn" would be
              // indistinguishable from "none was ever short".
              if (h0 <= shortest) { shortest = h0; shortestAt = { set: plant.name, d: d0, h: h0 }; }
              drawnPlants++;
            }
          }
          const was = prev.seen.get(key);
          if (was) {
            // Already on screen a pace ago, and still here: it may not have got
            // any taller in between.
            const dWas = Math.hypot(plant.e - prev.e, plant.n - prev.n) || 1e-6;
            const dNow = Math.hypot(plant.e - now.e, plant.n - now.n) || 1e-6;
            const hWas = a.flora.heightAt(plant.name, dWas, plant.outer);
            const hNow = a.flora.heightAt(plant.name, dNow, plant.outer);
            if (hWas > 0 && hNow - hWas > grew) {
              grew = hNow - hWas;
              grewAt = { set: plant.name, from: hWas, to: hNow, d: dNow };
            }
            continue;
          }
          const d = Math.hypot(plant.e - now.e, plant.n - now.n) || 1e-6;
          // Only what is in front of the walker. A plant may also arrive across
          // the view-cone edge, which is 62 degrees wide against a frame that is
          // never more than 40 — off-screen, and not what the owner saw.
          if (((plant.e - now.e) * now.fe + (plant.n - now.n) * now.fn) / d < AHEAD) continue;
          const fade = a.flora.fadeAt(plant.name, d, plant.outer);
          arrivals++;
          if (fade > worst) { worst = fade; worstAt = { set: plant.name, d, fade }; }
        }
        prev = now;
      }
      return { inset, arrivals, worst, worstAt, shortest, shortestAt, grew, grewAt,
        drawnPlants, pace: PACE, step: rings.step };
    });
    check(`${label}: every flora fade ring is inset inside its own lattice`,
      popIn.inset.length === 3
      && popIn.inset.every((r) => r.outer >= -1e-9 && r.inner >= -1e-9),
      popIn.inset.map((r) => `${r.id} outer +${r.outer.toFixed(2)} inner +${r.inner.toFixed(2)}`)
        .join(', ') + ` against a ${popIn.step} m rebuild step`);
    // The bound is one pace, not zero: the rebuild fires on the frame that
    // carries the walker past the step, so it can overshoot by however far that
    // one frame moved. 0.15 m of a 2.2 m near band is 7%.
    check(`${label}: a plant in front of the walker never arrives already visible`,
      popIn.arrivals >= 20 && popIn.worst <= 0.10,
      `${popIn.arrivals} arrivals over ${(20 * popIn.pace).toFixed(2)} m; worst coverage `
      + `${(popIn.worst * 100).toFixed(1)}% of full`
      + (popIn.worstAt ? ` (${popIn.worstAt.set} at ${popIn.worstAt.d.toFixed(2)} m)` : ''));

    // T-0035, and it is the owner's report read back off the drawing rather
    // than off the shader source: "the flowers still seem like they grow out of
    // the ground as you approach them, they do not fade in as you walk towards,
    // they grow up." A plant may arrive at any coverage the ring gives it — the
    // check above is the one that holds that faint — but it may not arrive
    // SHORT, and it may not gain height between two frames. Both halves matter:
    // the first would pass on a ramp that starts at 99%, the second would pass
    // on a scene where nothing ever arrives at all.
    check(`${label}: a plant is drawn at its own height, faint, never short`,
      popIn.arrivals >= 20 && popIn.drawnPlants > 500 && popIn.shortest === 1 && popIn.grew === 0,
      `${popIn.arrivals} arrivals, ${popIn.drawnPlants} plant-frames drawn; shortest `
      + `${(popIn.shortest * 100).toFixed(1)}% of its own height`
      + (popIn.shortestAt ? ` (${popIn.shortestAt.set} at ${popIn.shortestAt.d.toFixed(2)} m)` : '')
      + `; worst gain over one ${popIn.pace} m pace ${(popIn.grew * 100).toFixed(1)}%`
      + (popIn.grewAt
        ? ` (${popIn.grewAt.set} ${(popIn.grewAt.from * 100).toFixed(0)} -> `
          + `${(popIn.grewAt.to * 100).toFixed(0)}% at ${popIn.grewAt.d.toFixed(2)} m)`
        : ''));

    // --- the flower heads, read back off the drawing (R-BUG7) ---------------

    // R-BUG7 — flower heads hanging in the sky with nothing under them. The
    // owner photographed two of them over South Water Street on stalks that
    // stop in mid-air, and **the same symptom had been repaired four times in
    // `flora.js` by eye and asserted zero times here.** The two checks that
    // sound like this one are not it: `floating` is about BUILDINGS hovering
    // over their ground, and `floatingDry/floatingWet` asks where a water-lily
    // RECORD is placed — and R-BUG5b proved that a placement test cannot see a
    // drawing fault (391 stations dry, 10,734 vertices of timber in the river).
    //
    // So this reads the DRAWING back, off the instance buffers that went to the
    // GPU: for every head that is actually drawn, the foot of its own stalk has
    // to land inside a rooted plant's drawn body and under that plant's drawn
    // top. The foot is taken from the archetype's own lowest vertex rather than
    // from a constant here, so the assertion survives a change of anchoring.
    // `tools/measure_head_support.mjs` is the same reading with the numbers.
    const headSupport = await page.evaluate(() => {
      const a = window.__chicago4d;
      const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
      const fadeOf = (r, i, d) => clamp01((r[i] - d) / Math.max(r[i + 1], 1e-4))
        * (r[i + 3] > 0 ? clamp01((d - r[i + 2]) / r[i + 3]) : 1);
      /** Sets a head is ever hung from. A MID clump card is a billboard standing
       *  for a patch of matrix and carries no head, so counting one as support
       *  is a free pass — it is what made a first cut of this read zero.
       *
       *  `flora-far` is not that card, and since T-0209 it is not excluded:
       *  the far band deals the WHOLE community, and a flowering forb's far
       *  card carries its flower — `rebuildFar` calls `maybeHead` on it. The
       *  comment this replaces predates that and had gone false. Measured on
       *  the published mirror 2026-09-01: 2693 of 2693 orphans stood on a far
       *  card at 0.000 m whose top reached them. `flora-mid` stays out, and
       *  that is measured too — its scatter deals graminoids and never calls
       *  `maybeHead`, and no orphan stood on one. */
      const ROOTED = new Set(['flora-near', 'flora-forb', 'flora-rosette', 'flora-shrub',
        'flora-far']);
      /** A card's `spread` is its billboard HALF-WIDTH — 1.5 m at the near far
       *  band, not a stem's radius. Counting that as the support's reach would
       *  pass any head within a card's width of one, which is the free pass the
       *  note above refuses. A card carries only the head `maybeHead` puts at
       *  its own `e,n`, so it supports at its foot and nowhere else. */
      const CARD = new Set(['flora-far']);
      /** Under a twentieth of coverage the screen-door dither is writing one
       *  pixel in twenty of a head that is already only a few across at the
       *  distances its own ring covers. */
      const FADE_FLOOR = 0.05;
      const SLACK = 0.02; // a stem is centimetres thick; float is not a fault

      const meshes = [];
      a.flora.group.traverse((o) => { if (o.isInstancedMesh) meshes.push(o); });
      const footOf = (g) => {
        const p = g.getAttribute('position').array;
        let lo = Infinity;
        for (let i = 1; i < p.length; i += 3) if (p[i] < lo) lo = p[i];
        return lo;
      };
      const nominal = new Map(meshes.map((m) => [m.name, footOf(m.geometry)]));

      let drawn = 0; let unsupported = 0; let worst = null;
      let onCard = 0; const bySet = new Map();
      const anchors = a.scene?.anchors ?? [];
      for (const anchor of anchors) {
        for (const yaw of [0, 90, 180, 270]) {
          a.walker.teleport({ local_e: anchor.local_e, local_n: anchor.local_n, yaw_deg: yaw });
          // One frame is a rebuild — the sward is scattered from the camera on
          // the step that carries it, which is what `popIn` above walks on.
          a.step();
          const cx = a.camera.position.x; const cz = a.camera.position.z;
          // Every rooted plant, on a one-metre grid.
          const grid = new Map();
          for (const m of meshes) {
            if (!ROOTED.has(m.name) || !m.count) continue;
            const mm = m.instanceMatrix.array;
            const fl = m.geometry.getAttribute('aFlora').array;
            const rg = m.geometry.getAttribute('aChiRing').array;
            for (let i = 0; i < m.count; i++) {
              const o = i * 16;
              const x = mm[o + 12]; const z = mm[o + 14];
              const f = fadeOf(rg, i * 4, Math.hypot(x - cx, z - cz));
              // T-0035: the ring ramp is coverage, not height. A plant is drawn
              // whole or not at all, so the drawn top and the drawn reach are
              // the record's own numbers and the ramp only says WHETHER.
              if (f <= 0) continue;
              // `heightAt` is null for a set with no ring of its own, which is
              // what `flora-far` is — T-0035 draws every visible plant whole,
              // so the fraction is 1 and the null is "no ramp", not "no height".
              const h = a.flora.heightAt(m.name, Math.hypot(x - cx, z - cz), rg[i * 4]) ?? 1;
              const key = `${Math.floor(x)},${Math.floor(z)}`;
              let b = grid.get(key);
              if (!b) { b = []; grid.set(key, b); }
              b.push({ x, z, top: mm[o + 13] + fl[i * 4] * h, set: m.name,
                r: CARD.has(m.name) ? 0 : fl[i * 4 + 1] * h });
            }
          }
          // T-0448 diagnostic, second grid: the meshes ROOTED leaves out, built
          // the same way and consulted only to explain an orphan. The support
          // test above does not read it, so the count stays comparable.
          const cardGrid = new Map();
          for (const m of meshes) {
            if (ROOTED.has(m.name) || m.name.startsWith('flora-head-') || !m.count) continue;
            const mm = m.instanceMatrix.array;
            const fl = m.geometry.getAttribute('aFlora').array;
            const rg = m.geometry.getAttribute('aChiRing').array;
            for (let i = 0; i < m.count; i++) {
              const o = i * 16;
              const x = mm[o + 12]; const z = mm[o + 14];
              if (fadeOf(rg, i * 4, Math.hypot(x - cx, z - cz)) <= 0) continue;
              const h = a.flora.heightAt(m.name, Math.hypot(x - cx, z - cz), rg[i * 4]) ?? 1;
              const key = `${Math.floor(x)},${Math.floor(z)}`;
              let b = cardGrid.get(key);
              if (!b) { b = []; cardGrid.set(key, b); }
              b.push({ x, z, top: mm[o + 13] + fl[i * 4] * h, r: fl[i * 4 + 1] * h, set: m.name });
            }
          }
          for (const m of meshes) {
            if (!m.name.startsWith('flora-head-') || !m.count) continue;
            const lo = nominal.get(m.name);
            const mm = m.instanceMatrix.array;
            const fl = m.geometry.getAttribute('aFlora').array;
            const rg = m.geometry.getAttribute('aChiRing').array;
            const rise = m.geometry.getAttribute('aChiRise').array;
            for (let i = 0; i < m.count; i++) {
              const o = i * 16;
              const x = mm[o + 12]; const y = mm[o + 13]; const z = mm[o + 14];
              const f = fadeOf(rg, i * 4, Math.hypot(x - cx, z - cz));
              if (f <= FADE_FLOOR) continue;
              drawn++;
              // `rise` is still read back — it is what puts this head over its
              // plant's base — but the world-space descent that used to subtract
              // `rise * (1 - fade)` from it is gone with the scale it chased.
              const s = lo * fl[i * 4];
              const fx = x + mm[o + 4] * s;
              const fy = y + mm[o + 5] * s;
              const fz = z + mm[o + 6] * s;
              let best = -Infinity;
              // T-0448 diagnostic: the nearest rooted plant IGNORING the radius
              // test, so an orphan can be told from a stem the radius missed.
              let nearest = null;
              for (let kx = Math.floor(fx) - 1; kx <= Math.floor(fx) + 1; kx++) {
                for (let kz = Math.floor(fz) - 1; kz <= Math.floor(fz) + 1; kz++) {
                  const b = grid.get(`${kx},${kz}`);
                  if (!b) continue;
                  for (const p of b) {
                    const d = Math.hypot(p.x - fx, p.z - fz);
                    if (!nearest || d < nearest.d) nearest = { d, r: p.r, top: p.top, set: p.set };
                    if (p.top > best
                      && d <= Math.max(0.05, p.r) + SLACK) best = p.top;
                  }
                }
              }
              if (best < fy - SLACK) {
                unsupported++;
                // T-0448: does a mesh ROOTED excludes stand where the stem is
                // missing, and would it have counted? Answers whether these are
                // far-card heads (T-0209) or geometry over nothing at all.
                let card = null;
                for (let kx = Math.floor(fx) - 1; kx <= Math.floor(fx) + 1; kx++) {
                  for (let kz = Math.floor(fz) - 1; kz <= Math.floor(fz) + 1; kz++) {
                    const b = cardGrid.get(`${kx},${kz}`);
                    if (!b) continue;
                    for (const p of b) {
                      const d = Math.hypot(p.x - fx, p.z - fz);
                      if (!card || d < card.d) card = { d, r: p.r, top: p.top, set: p.set };
                    }
                  }
                }
                if (card && card.d <= Math.max(0.05, card.r) + SLACK && card.top >= fy - SLACK) {
                  onCard++;
                  bySet.set(card.set, (bySet.get(card.set) ?? 0) + 1);
                }
                const gap = best === -Infinity ? null : fy - best;
                if (!worst || (gap ?? 9) > (worst.gap ?? 9) || best === -Infinity) {
                  worst = { set: m.name, at: anchor.id, yaw, y: fy, gap, rise: rise[i],
                    orphan: best === -Infinity,
                    // What was actually there, and why it did not count.
                    nearest: nearest && { set: nearest.set, d: +nearest.d.toFixed(3),
                      r: +nearest.r.toFixed(3), reach: +(nearest.top - fy).toFixed(3) },
                    card: card && { set: card.set, d: +card.d.toFixed(3),
                      r: +card.r.toFixed(3), reach: +(card.top - fy).toFixed(3) } };
                }
              }
            }
          }
        }
      }
      return { drawn, unsupported, worst, poses: anchors.length * 4,
        onCard, bySet: [...bySet].sort((p, q) => q[1] - p[1]) };
    });
    check(`${label}: every drawn flower head has a plant under its own stalk`,
      headSupport.drawn > 500 && headSupport.unsupported === 0,
      `${headSupport.unsupported} of ${headSupport.drawn} drawn heads over `
      + `${headSupport.poses} poses had nothing under the foot of their own stalk`
      + (headSupport.worst
        ? `; worst ${headSupport.worst.set} at ${headSupport.worst.at} ${headSupport.worst.yaw}deg, `
          + `foot ${headSupport.worst.y.toFixed(2)} m, ${headSupport.worst.rise.toFixed(2)} m over its base `
          + (headSupport.worst.orphan ? 'over open ground' : `above a ${headSupport.worst.gap.toFixed(2)} m gap`)
          // T-0448: name what WAS there. An orphan with a rooted plant 0.2 m away
          // is the radius test being too tight; one with nothing for metres is the
          // flora layer placing a head its stem never got.
          + (headSupport.worst.nearest
            ? `; nearest rooted ${headSupport.worst.nearest.set} at ${headSupport.worst.nearest.d} m `
              + `(its own radius ${headSupport.worst.nearest.r} m, top ${headSupport.worst.nearest.reach} m from the foot)`
            : '; no rooted plant in the nine cells at all')
          // T-0448: and what a mesh ROOTED excludes had standing there instead.
          + (headSupport.worst.card
            ? `; excluded ${headSupport.worst.card.set} at ${headSupport.worst.card.d} m `
              + `(radius ${headSupport.worst.card.r} m, top ${headSupport.worst.card.reach} m from the foot)`
            : '; nothing ROOTED excludes was there either')
          + `; ${headSupport.onCard} of ${headSupport.unsupported} orphans stand on a mesh `
          + `ROOTED excludes that reaches them [`
          + headSupport.bySet.map(([k, v]) => `${k} ${v}`).join(', ') + ']'
        : ''));

    inStageWork = false;
    } // end PART 10 (T-0060 stage 4a, cut by T-0121; renumbered by T-0346 and T-0173, halved by T-0170)
    // PART 11 — the sward's ragged boundary through the units a visitor reads:
    // the boundary and its fringe, each community's own recorded ground cover,
    // the street readouts, the navigation guide and the Settings units. The
    // second half of T-0060's stage 4a.
    //
    // T-0170 CUT IT HERE, and the boundary had to be MADE before it could be
    // taken: this part carried no `// --- section ---` headers at all, which is
    // the reason T-0167 left it alone. The seams are named now, and the profile
    // is what chose this one out of them. The first candidate — one section
    // earlier, above the flower-head census — was cut, measured and rejected:
    // 5 m 05 s and 6 m 24 s, and 3 m 36 s is not a margin on a suite whose own
    // readings move by minutes with the load. Moving that one section up into
    // the head buys the balance, and both halves are measured under six minutes.
    //
    // Exactly one binding crosses, and it is the same one that already crossed
    // the stage split: `streetLayer`, read above it and now named in
    // `anyStage(7, 10, 11)` because BOTH halves read it — the first half for the
    // road panels and the horizon band, this one for the street readouts. The
    // scan turned up six other names below this line (`headSupport`, `horizon`,
    // `over`, `planted`, `popIn`, `sward`) and every occurrence is prose or a
    // string, not the binding.
    if (stageOn(11)) {
    inStageWork = true;

    // Same fresh-boot accommodation as the part above: the tail of this one
    // drives the panel chrome (`#btn-help`), and while the gate screen stands
    // the chrome has no layout at all — the click waits ninety seconds for a
    // zero-size button and dies. In a full run this is a no-op.
    await enterTown();

    // Every camera-bearing section below teleports itself, so this part takes
    // no pose. What they all assume is a walker ON THE GROUND — the boundary
    // sections measure screen rows against eye height, and the last thing this
    // part does is fly. The part above lands the walker there itself; from a
    // fresh boot this is what puts it there. Idempotent by construction, so an
    // unfiltered run pays one call for it.
    await page.evaluate(() => { window.__chicago4d.setFly(false); });

    // --- the sward's ragged boundary (ROADMAP § S6a) ------------------------

    // ROADMAP § S6a item 3: a ring is a circle about the walker, so on flat
    // ground its outer edge maps to a CONSTANT SCREEN ROW — measured at row
    // 450, razor straight across all 1280 columns. Measured the way the finding
    // was stated: bin the view by bearing, ask each bin how far out its own
    // sward reaches, and convert that distance to the row it lands on. The
    // second half is the one that stops this being satisfiable by breaking the
    // field — every bin's boundary has to lie inside the fringe's own range, so
    // a hole in the sward reads as a failure rather than as raggedness.
    const seam = await page.evaluate(() => {
      const a = window.__chicago4d;
      const SETS = { 'flora-mid': 'mid', 'flora-forb': 'forb' };
      // The station is FOUND rather than written down, because the ring radius
      // it has to be clear over is a detail setting: 27 m at full detail and
      // 13 m on a phone. A hand-picked point in the settled town carried six
      // mid cards at 390x780 — enough to look measured and not enough to
      // measure anything. Wanted: ground where a dense-matrix community covers
      // the whole disc the outer ring reaches over, so the boundary is drawn in
      // every bearing and a thin bin means a defect rather than a hedgerow.
      const dense = new Set(a.flora.communities()
        .filter((c) => c.graminoids && c.matrixShare >= 0.7).map((c) => c.id));
      const R = a.flora.rings.layers.mid.lattice.outer;
      const clear = (e, n) => {
        for (let k = 0; k < 12; k++) {
          const t = (k / 12) * Math.PI * 2;
          for (const rr of [R * 0.45, R * 0.75, R]) {
            const pe = e + Math.cos(t) * rr;
            const pn = n + Math.sin(t) * rr;
            if (!dense.has(a.flora.zoneAt(pe, pn))) return false;
            if (!a.flora.plantableAt(pe, pn)) return false;
          }
        }
        return dense.has(a.flora.zoneAt(e, n)) && a.flora.plantableAt(e, n);
      };
      let station = null;
      for (let e = -300; e <= 900 && !station; e += 8) {
        for (let n = -300; n <= 500 && !station; n += 8) {
          if (clear(e, n)) station = { e, n };
        }
      }
      if (!station) return { station: null };
      a.walker.teleport({ local_e: station.e, local_n: station.n, yaw_deg: 0 });
      a.step();
      a.step();
      const cam = a.camera.position;
      const f = cam.clone();
      a.camera.getWorldDirection(f);
      const fwd = Math.atan2(f.x, -f.z);
      const H = a.renderer.domElement.height;
      const halfTan = Math.tan((a.camera.fov * Math.PI / 180) / 2);
      // Rows below the horizon for a point on the ground `d` away. The whole
      // finding is in this arithmetic: the row goes as 1/d, so a constant d is
      // a constant row whatever the ground does either side of it.
      const rowOf = (d, groundY) => (H / 2) * ((cam.y - groundY) / d) / halfTan;

      const BINS = 16;
      const HALF = 30 * Math.PI / 180;
      // T-0225 — WHAT COUNTS AS DRAWN, and it is the screen door's number
      // rather than a small one.
      //
      // This read `fadeAt(...) > 0.02`. `fadeAt` is COVERAGE since T-0035: the
      // alpha the fragment program resolves through the ordered 4x4 Bayer
      // matrix in `plantMaterial` — `fract(chiBayer4(gl_FragCoord.xy) +
      // vChiDither) >= vChiFade` discards. That matrix has SIXTEEN levels, at
      // (v + 0.5)/16, and `vChiDither` slides the whole set by a per-instance
      // phase. So over a 4x4 tile the surviving pixels number floor(16F) or
      // ceil(16F) and nothing else, and BELOW F = 1/16 that is 0 or 1 — which
      // of the two being decided by the instance's dither phase, a number this
      // side of the GPU cannot see at all.
      //
      // At F = 0.02 that is one pixel in fifty kept, and only for the 32 % of
      // phases that keep any: the reading called a plant DRAWN that renders as
      // nothing whatever in two instances out of three. The boundary it
      // reported was therefore the radius at which the placer stopped placing,
      // which `plantableAt` and the lattice inset already guarantee.
      //
      // 1/16 is the smallest threshold that fixes it, and it is the screen
      // door's own quantum rather than a taste: it is exactly where "drawn"
      // stops being a property of the instance's dither phase and becomes a
      // property of its coverage. At or above it every instance keeps at least
      // one pixel in every 4x4 tile it covers, whatever phase it drew.
      const SEEN = 1 / 16;
      // The old threshold, still read, because the acceptance asks this check
      // to print the before and the after side by side rather than leave the
      // size of the correction to a re-run with an edited gate (T-0187's `show`
      // flag is here for the same reason).
      const FAINT = 0.02;
      const out = {};
      for (const [name, layer] of Object.entries(SETS)) {
        const mesh = a.flora.group.getObjectByName(name);
        const m = mesh?.instanceMatrix?.array;
        const ring = mesh?.geometry.getAttribute('aChiRing')?.array;
        const r = a.flora.rings.layers[layer];
        const bins = new Array(BINS).fill(null);
        const faint = new Array(BINS).fill(null);
        let ringLo = Infinity;
        let ringHi = -Infinity;
        for (let i = 0; m && ring && i < mesh.count; i++) {
          const o = i * 16;
          const e = m[o + 12];
          const n = -m[o + 14];
          const y = m[o + 13];
          const da = ((Math.atan2(e - cam.x, n + cam.z) - fwd + Math.PI * 3)
            % (Math.PI * 2)) - Math.PI;
          if (Math.abs(da) > HALF) continue;
          ringLo = Math.min(ringLo, ring[i * 4]);
          ringHi = Math.max(ringHi, ring[i * 4]);
          // The furthest plant in this bearing that is actually DRAWN — the
          // edge the eye sees, not the radius the placer assigned. A plant
          // faded to nothing is not a boundary, and asking the attribute alone
          // would report a ragged edge in a direction carrying no sward at all.
          const d = Math.hypot(e - cam.x, n + cam.z);
          // The whole ring, for the reason `snap()` above carries all four: the
          // mid ring's inner boundary is spread per slot since T-0093, and the
          // outer radius alone would have `fadeAt` answer off the layer's
          // nominal inner edge.
          const f = a.flora.fadeAt(name, d, [ring[i * 4], ring[i * 4 + 1],
            ring[i * 4 + 2], ring[i * 4 + 3]]);
          if (f <= FAINT) continue;
          const b = Math.min(BINS - 1, Math.floor((da + HALF) / (2 * HALF / BINS)));
          if (!faint[b] || d > faint[b].d) faint[b] = { d, y };
          if (f < SEEN) continue;
          if (!bins[b] || d > bins[b].d) bins[b] = { d, y };
        }
        const stat = (list) => {
          const used = list.filter(Boolean);
          const rows = used.map((b) => rowOf(b.d, b.y));
          const reach = used.map((b) => b.d);
          return {
            bins: used.length,
            spreadPx: rows.length ? Math.max(...rows) - Math.min(...rows) : 0,
            minReach: reach.length ? Math.min(...reach) : 0,
            maxReach: reach.length ? Math.max(...reach) : 0,
            meanReach: reach.length ? reach.reduce((s, v) => s + v, 0) / reach.length : 0,
          };
        };
        out[layer] = {
          ...stat(bins),
          faint: stat(faint),
          ringLo: Number.isFinite(ringLo) ? ringLo : 0,
          ringHi: Number.isFinite(ringHi) ? ringHi : 0,
          nominal: r.fade[0],
          fringe: r.fringe ?? 0,
          // The ramp the threshold is read on, so the bars below can carry the
          // inset it costs as arithmetic instead of as a measured constant.
          // `HARD` on a boundary handed over by density (T-0093), which is why
          // this is read rather than taken from TUNE.
          band: r.fade[1],
          seen: SEEN,
          faintAt: FAINT,
        };
      }
      // The placer's own answer, so the gate is not a second copy of the noise:
      // the same ground must give the same fringe from a camera 40 m away.
      const anchored = (() => {
        const pts = [];
        for (let k = 0; k < 9; k++) pts.push([station.e + k * 2.7, station.n - k * 1.9]);
        const at = () => pts.map(([e, n]) => a.flora.fringeAt('mid', e, n));
        const before = at();
        a.walker.teleport({ local_e: station.e + 40, local_n: station.n + 25, yaw_deg: 200 });
        a.step();
        const after = at();
        return {
          same: before.every((v, i) => v === after[i]),
          spread: Math.max(...before) - Math.min(...before),
        };
      })();
      return { ...out, station, anchored };
    });
    check(`${label}: an open station exists to measure the sward's boundary from`,
      !!seam.station,
      'no dense-matrix community covers a whole ring radius anywhere in the box');
    if (seam.station) {
      const s = seam.mid;
      // A boundary the eye reads as a line is one that holds the same row all
      // the way across; four pixels of drawing buffer is a modest floor, and
      // the measured figure is several times it at both viewports.
      // T-0225. THE INSET THE THRESHOLD COSTS, as arithmetic and not as a
      // constant somebody measured once.
      //
      // The bars below are stated against the PLACED boundary — `nominal` plus
      // or minus the slot's own `fringe` — and `minReach`/`meanReach` now read
      // the DRAWN boundary at coverage `seen`. The ramp is linear
      // (`flora.fadeOf`: `clamp01((outer - d) / band)`), so a slot reaches
      // coverage F at `outer - F x band` and the two boundaries differ by
      // exactly `band x seen`: 0.44 m on the 7.0 m desktop band, 0.10 m on the
      // phone's 1.6 m one. That term is a property of the STATISTIC, so it
      // belongs in the bar; leaving it out would fail a sward for being read
      // more honestly. It is not slack for the sward to spend — everything
      // else about the bars is unchanged, and if a viewport lands under one
      // even with the inset carried, that is a finding about the sward and
      // gets its own ticket rather than a wider bar.
      const inset = s.band * s.seen;
      check(`${label}: the sward's outer boundary is not a constant screen row`,
        s.bins >= 12 && s.spreadPx >= 4,
        `${s.bins}/16 bearing bins from E ${seam.station.e} N ${seam.station.n}, boundary rows `
        + `spread ${s.spreadPx.toFixed(1)} px, reach ${s.minReach.toFixed(2)}`
        + `-${s.maxReach.toFixed(2)} m at ${(s.seen * 100).toFixed(2)}% coverage `
        + `(at the old ${(s.faintAt * 100).toFixed(0)}%: ${s.faint.bins}/16 bins, `
        + `spread ${s.faint.spreadPx.toFixed(1)} px, reach ${s.faint.minReach.toFixed(2)}`
        + `-${s.faint.maxReach.toFixed(2)} m)`, true);
      // ...and it is the fringe doing it. A hole in the sward would satisfy the
      // check above and would be a worse defect than the seam, so no bearing
      // may fall short of what the fringe alone can take off the ring, and the
      // raggedness may not be bought by shrinking the ring on average.
      check(`${label}: the boundary's variation is the fringe, not a hole in the field`,
        s.bins >= 12
        && s.minReach >= s.nominal - s.fringe - 1.2 - inset
        && s.meanReach >= s.nominal - 0.5 * s.fringe - inset,
        `reach ${s.minReach.toFixed(2)}-${s.maxReach.toFixed(2)} m, mean `
        + `${s.meanReach.toFixed(2)} m at ${(s.seen * 100).toFixed(2)}% coverage `
        + `against a nominal ${s.nominal.toFixed(2)} `
        + `+/- ${s.fringe.toFixed(2)} m (bars: min >= `
        + `${(s.nominal - s.fringe - 1.2 - inset).toFixed(2)}, `
        + `mean >= ${(s.nominal - 0.5 * s.fringe - inset).toFixed(2)}, `
        + `both carrying the ${inset.toFixed(2)} m the ${(s.seen * 100).toFixed(2)}% `
        + `threshold insets a ${s.band.toFixed(2)} m ramp by); at the old `
        + `${(s.faintAt * 100).toFixed(0)}%: ${s.faint.minReach.toFixed(2)}-`
        + `${s.faint.maxReach.toFixed(2)} m, mean ${s.faint.meanReach.toFixed(2)} m`, true);
      // The forb ring ends within a metre of the mid ring, so if only the grass
      // were fringed the flowers would go on drawing the line — and a flower is
      // the brightest thing in the field. It is measured on its RINGS rather
      // than on its drawn edge: at 3.4 m cells and its recorded densities a
      // 3.75-degree bin holds one or two forbs, so "the furthest one drawn" is
      // a sampling statistic and not a boundary. Measured that way it reported
      // a nine-metre hole in ground that has none. A flat ring spans zero; the
      // bar is half the fringe's own range, which no flat ring can reach and no
      // fringed one has trouble with.
      const fb = seam.forb;
      check(`${label}: the flower layer's boundary is fringed too, not only the grass`,
        fb.ringHi - fb.ringLo >= fb.fringe
        && fb.ringLo >= fb.nominal - fb.fringe - 0.05
        && fb.ringHi <= fb.nominal + fb.fringe + 0.05,
        `forb rings span ${fb.ringLo.toFixed(2)}-${fb.ringHi.toFixed(2)} m about a nominal `
        + `${fb.nominal.toFixed(2)} +/- ${fb.fringe.toFixed(2)} m`, true);
    }
    // A fringe that moved with the walker would be a boundary that swims — the
    // pop-in defect over again, one ring further out. Nine points on the ground
    // answer identically from two cameras 40 m apart, and they are not all the
    // same answer, which is what says the field varies at all.
    check(`${label}: the ragged boundary is anchored to the ground, not to the camera`,
      seam.anchored.same && seam.anchored.spread > 0.5,
      `same from 40 m away: ${seam.anchored.same}; `
      + `spread over nine points ${seam.anchored.spread.toFixed(2)} m`);
    // --- what each community's own records say its ground carries -----------

    // Each flora zone record authors how much of the ground its matrix covers
    // — `cover.matrix_fraction`, with a `bare_soil_fraction` beside it that the
    // manifest even denormalises — and the renderer planted all ten communities
    // at the one lattice density L32 tuned on closed wet prairie. Two questions,
    // because answering only the first is exactly how a written, validated,
    // shipped field went unread: does the authored number reach the renderer,
    // and does the sward on the ground actually follow it?
    const swardCover = await page.evaluate(async () => {
      const a = window.__chicago4d;
      const index = await (await fetch(`${a.dataBase}flora/index.json`)).json();
      const authored = {};
      for (const z of index.zones) {
        const rec = await (await fetch(`${a.dataBase}flora/${z.file}`)).json();
        authored[z.id] = { matrix: rec.cover?.matrix_fraction, bare: rec.cover?.bare_soil_fraction };
      }
      const compiled = a.flora.communities();
      const drift = compiled.filter((c) => authored[c.id]?.matrix !== c.matrixShare
        || authored[c.id]?.bare !== c.bareSoil);

      // A station is a point whose whole sampling disc is ONE community and all
      // of it plantable ground, so the instance count and the area answer for
      // the same zone — the track, the buildings and the water are out of both.
      // Inside CONE_KEEP_M the lattice is complete in every direction, so a
      // disc of this size needs no knowledge of the view cone to be unbiased.
      const R = 3.2;
      const clean = (want, e, n) => {
        for (let k = 0; k < 16; k++) {
          const t = (k / 16) * Math.PI * 2;
          for (const rr of [R * 0.6, R]) {
            const pe = e + Math.cos(t) * rr;
            const pn = n + Math.sin(t) * rr;
            if (a.flora.zoneAt(pe, pn) !== want) return false;
            if (!a.flora.plantableAt(pe, pn)) return false;
          }
        }
        return a.flora.plantableAt(e, n);
      };
      const rows = [];
      for (const c of compiled) {
        if (!c.graminoids || !(c.matrixShare > 0)) continue;
        let station = null;
        for (let e = -300; e <= 900 && !station; e += 6) {
          for (let n = -300; n <= 500 && !station; n += 6) {
            if (a.flora.zoneAt(e, n) === c.id && clean(c.id, e, n)) station = { e, n };
          }
        }
        if (!station) continue;
        a.walker.teleport({ local_e: station.e, local_n: station.n, yaw_deg: 0 });
        a.step();
        a.step();
        const mesh = a.flora.group.getObjectByName('flora-near');
        const m = mesh.instanceMatrix.array;
        let instances = 0;
        for (let i = 0; i < mesh.count; i++) {
          const e = m[i * 16 + 12];
          const n = -m[i * 16 + 14];
          if (Math.hypot(e - station.e, n - station.n) <= R) instances++;
        }
        const area = Math.PI * R * R;
        rows.push({ id: c.id, share: c.matrixShare, instances,
          perM2: instances / area, implied: instances / area / c.matrixShare });
      }
      return { drift, rows, capped: a.flora.stats.capped ?? [] };
    });
    check(`${label}: every community's recorded ground cover reaches the renderer`,
      swardCover.drift.length === 0,
      swardCover.drift.map((d) => `${d.id} compiled ${d.matrixShare}/${d.bareSoil}`).join(', '));
    {
      const rows = swardCover.rows;
      const implied = rows.map((r) => r.implied).sort((x, y) => x - y);
      const median = implied[Math.floor(implied.length / 2)] || 0;
      const worst = rows.reduce((w, r) => (
        Math.abs(r.implied - median) > Math.abs(w?.implied - median || -1) ? r : w), null);
      const spread = Math.max(...rows.map((r) => r.perM2)) / Math.min(...rows.map((r) => r.perM2));
      // The second half is the discriminating case: with one density for every
      // community the per-square-metre counts would be equal — a spread near 1 —
      // and it is the IMPLIED figures that would then fan out across the 0.35 …
      // 1.00 the records give. This assertion fails in that direction too.
      check(`${label}: the sward is planted at each community's own recorded cover`,
        rows.length >= 5 && median > 0 && spread >= 2
        && rows.every((r) => Math.abs(r.implied - median) <= 0.25 * median),
        `${rows.length} communities, densities spread ${spread.toFixed(2)}x, implied full-cover `
        + `median ${median.toFixed(2)}/m²`
        + (worst ? `, worst ${worst.id} ${worst.perM2.toFixed(2)}/m² at a recorded `
          + `${worst.share} = ${worst.implied.toFixed(2)}` : ''));
    }

    // --- the streets a visitor reads ----------------------------------------

    check(`${label}: every structure, including Exchange Coffee House, shares the terrain surface`,
      streetLayer.anchoredBuildings > 20
      // Never ABOVE the origin's ground; below it only as far as the terrain
      // actually falls away under the building (the box is ~4 ft of relief, and
      // the fort mound is the deepest at about 2.4 m).
      && streetLayer.worstBuildingAnchor < 1e-6
      && streetLayer.deepestBedding < 3
      && streetLayer.exchangeAnchor?.error < 1e-6
      && streetLayer.worstDrySurfaceAlias < 1e-6,
      `${streetLayer.anchoredBuildings} structures, worst above-ground `
      + `${streetLayer.worstBuildingAnchor?.toFixed?.(4)}, deepest bedding `
      + `${streetLayer.deepestBedding?.toFixed?.(2)} m, `
      + `Exchange ${JSON.stringify(streetLayer.exchangeAnchor)}, `
      + `dry alias ${streetLayer.worstDrySurfaceAlias}`);
    check(`${label}: street clearing removes travel-track plants but preserves the block`,
      streetLayer.clearsLake && streetLayer.keepsBlockGreen, JSON.stringify(streetLayer));
    check(`${label}: the readout shows both 1835 and current names at an intersection`,
      streetLayer.crossing.shown
      && streetLayer.crossing.state?.mode === 'intersection'
      && /Lake Street/.test(streetLayer.crossing.historic)
      && /La Salle Street/.test(streetLayer.crossing.historic)
      && /W Lake Street/.test(streetLayer.crossing.modern)
      && /LaSalle/.test(streetLayer.crossing.modern),
      JSON.stringify(streetLayer.crossing));
    check(`${label}: the street readout announces the next cross street ahead`,
      streetLayer.approaching.state?.mode === 'on'
      && streetLayer.approaching.historic === 'Market Street'
      && /N Wacker Drive/.test(streetLayer.approaching.modern)
      && /Lake Street/.test(streetLayer.approaching.ahead)
      && /\d+ ft/.test(streetLayer.approaching.ahead)
      && !/\d+ m(?:\s|$)/.test(streetLayer.approaching.ahead),
      JSON.stringify(streetLayer.approaching));

    // --- the navigation guide, and the units the whole HUD reads in --------

    // The menu is built from the two runtime collections, not from a sampled
    // shortlist.  With an empty query every loaded structure and every compiled
    // control junction must have a button; a real search must narrow both kinds.
    await page.click('#btn-help');
    await page.click('.panel-tab[data-tab="settings"]');
    await page.click('#s-show-control-help');
    const reopenedGuide = await page.evaluate(() => ({
      shown: !document.getElementById('control-help').hasAttribute('hidden'),
      panelHidden: document.getElementById('panel').hasAttribute('hidden'),
    }));
    check(`${label}: Settings can reopen the dismissed navigation guide`,
      reopenedGuide.shown && reopenedGuide.panelHidden,
      JSON.stringify(reopenedGuide));
    await page.click('#control-help-close');
    await page.click('#btn-help');
    await page.click('.panel-tab[data-tab="settings"]');
    const unitChoice = await page.evaluate(async () => {
      const api = window.__chicago4d;
      const select = document.getElementById('s-units');
      const choose = (value) => {
        select.value = value;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        api.walker.teleport({ local_e: 89.2, local_n: -180, yaw_deg: 0 });
        api.step();
        api.hud.setFly(true, { announce: false });
        api.hud.setAltitude(100);
        const result = {
          value: select.value,
          navigation: api.navigation.units,
          speed: document.getElementById('v-speed')?.textContent?.trim(),
          altitude: document.getElementById('badge-alt')?.textContent?.trim(),
          map: document.getElementById('overview-map')?.getAttribute('aria-label'),
          street: document.getElementById('street-approach')?.textContent?.trim(),
        };
        api.hud.setFly(false, { announce: false });
        return result;
      };
      const metric = choose('metric');
      const imperial = choose('imperial');
      const { formatDistance } = await import(window.__MODULE_BASE + 'units.js');
      return {
        metric, imperial,
        mile: formatDistance(1609.344, 'imperial'),
        kilometre: formatDistance(1000, 'metric'),
        stored: JSON.parse(localStorage.getItem('chicago4d.settings') || '{}').units,
      };
    });
    check(`${label}: Settings switches every navigation measurement as one unit system`,
      unitChoice.metric.value === 'metric' && unitChoice.metric.navigation === 'metric'
      && /km\/h$/.test(unitChoice.metric.speed ?? '')
      && unitChoice.metric.altitude === '100 m up'
      && /\d+ m/.test(unitChoice.metric.map ?? '')
      && /\d+ m$/.test(unitChoice.metric.street ?? '')
      && unitChoice.imperial.value === 'imperial'
      && unitChoice.imperial.navigation === 'imperial'
      && /mph$/.test(unitChoice.imperial.speed ?? '')
      && unitChoice.imperial.altitude === '328 ft up'
      && /\d+ ft/.test(unitChoice.imperial.map ?? '')
      && /\d+ ft$/.test(unitChoice.imperial.street ?? '')
      && unitChoice.mile === '1.0 mi' && unitChoice.kilometre === '1.0 km'
      && unitChoice.stored === 'imperial',
      JSON.stringify(unitChoice));

    inStageWork = false;
    } // end PART 11 (the tail of T-0060 stage 4a, cut out of part 10 by T-0170)
    // PART 12 — eye height through What's-new: the settings, the Go-to tab and
    // the release notes. The head of T-0060's stage 4b; T-0167 cut the Evidence
    // panel and free-fly off its tail into part 13.
    //
    // It drives the panel chrome from its first line, so it enters the town on
    // its own account. It takes no pose of its own on purpose: the checks below
    // read eye height against the ground the visitor is standing on, and a
    // teleport here would be this part measuring somewhere the unfiltered run
    // never stands.
    //
    // EVERY CHROME CLICK IN THIS PART GOES THROUGH `clickChrome` (T-0215), and
    // the reason is written where that helper is defined. The short of it: this
    // part is nothing but panel chrome — fourteen clicks and almost no camera —
    // so it is the part with the most to lose to a starved action, and on
    // 2026-08-27 its FIRST click starved for ninety seconds and took the whole
    // part down before one assertion had run. Not one assertion is dropped or
    // softened by the change: `clickChrome` hit-tests the control at its own
    // centre the way a real click does, and says what covered it when it fails.
    if (stageOn(12)) {
    inStageWork = true;
    await enterTown();
    // …and the PANEL, which part 11 leaves open at its last line and this part
    // reaches straight into: its first statement clicks a tab inside it, and a
    // click on a tab that has no layout waits ninety seconds and dies. Guarded
    // on the panel's own hidden state rather than toggling, for the same reason
    // enterTown() is guarded: in an unfiltered run this must do nothing at all.
    // …and NOTHING STANDING OVER IT (T-0369). The inspect card is fixed at the
    // top right and overlaps this panel's tab strip on the desktop viewport, so
    // ANY predecessor that picked a structure and left its card open makes the
    // first click below fail — which is exactly what part 1 did. Part 1 no
    // longer leaks it, and this part no longer depends on that being true of
    // every predecessor either: a part that drives chrome establishes the
    // chrome's state, for the same reason the panel below is opened rather than
    // assumed. Both halves are the fix, because only the second one makes this
    // part's verdict independent of which stages ran in front of it.
    await page.evaluate(() => {
      window.__chicago4d.popup.close();
      if (document.getElementById('panel').hasAttribute('hidden')) {
        document.getElementById('btn-help').click();
      }
    });

    // --- eye height ---------------------------------------------------------
    //
    // The default is a claim about 1835 — the mean stature of an adult man of
    // the period — and a visitor found it uncomfortably low, which it is: the
    // prairie grass beside you is genuinely taller. So it is adjustable, and
    // three things have to hold. The default must still be the researched
    // figure, so the setting does not quietly become a restatement of it. The
    // eye must move the moment the slider does, or the control reads as dead.
    // And free-fly must NOT be resettled — up there the eye height is an
    // altitude the visitor is flying, and dropping them to standing height mid
    // flight would be the setting reaching somewhere it has no business.
    await clickChrome('.panel-tab[data-tab="settings"]');
    const eye = await page.evaluate(async () => {
      const api = window.__chicago4d;
      const el = document.getElementById('s-eye');
      const above = () => +(api.walker.state.eyeY - api.walker.state.groundY).toFixed(3);
      const move = async (v) => {
        el.value = String(v);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        await new Promise((r) => setTimeout(r, 60));
        return above();
      };
      api.setFly(false);
      const dflt = above();
      const readoutAtDefault = document.getElementById('v-eye')?.textContent ?? '';
      const raised = await move(2.2);
      const lowered = await move(1.5);
      await move(1.68);
      // Now in the air, where it must not apply.
      api.setFly(true);
      api.walker.teleport({ local_e: 60, local_n: -160, yaw_deg: 0, altitude_m: 200, pitch_deg: -60 });
      await new Promise((r) => setTimeout(r, 120));
      const flyingBefore = above();
      const flyingAfter = await move(1.5);
      api.setFly(false);
      await move(1.68);
      return { dflt, readoutAtDefault, raised, lowered, flyingBefore, flyingAfter,
        min: Number(el.min), max: Number(el.max),
        stored: JSON.parse(localStorage.getItem('chicago4d.settings') || '{}').eyeHeight };
    });
    check(`${label}: eye height starts at the researched period figure`,
      Math.abs(eye.dflt - 1.68) < 0.005 && /period eye level/.test(eye.readoutAtDefault),
      `${eye.dflt} m, readout "${eye.readoutAtDefault}"`);
    check(`${label}: the eye height readout is a stature, not rounded to whole feet`,
      /\d+ ft \d+ in/.test(eye.readoutAtDefault),
      // '6 ft' for 1.68 m is wrong by half a foot AND unchanging across a third
      // of the slider, which is what made the control look broken.
      `readout "${eye.readoutAtDefault}"`);
    check(`${label}: moving the eye height slider moves the eye immediately`,
      Math.abs(eye.raised - 2.2) < 0.005 && Math.abs(eye.lowered - 1.5) < 0.005,
      `raised to ${eye.raised} m, lowered to ${eye.lowered} m`);
    check(`${label}: eye height does not yank the camera down mid-flight`,
      Math.abs(eye.flyingAfter - eye.flyingBefore) < 1,
      `${eye.flyingBefore} m up before, ${eye.flyingAfter} m after`);
    check(`${label}: the eye height range covers short to tall without absurdity`,
      eye.min <= 1.5 && eye.max >= 2.0 && eye.max <= 3.0,
      `${eye.min}–${eye.max} m`);

    // --- typing is not driving ---------------------------------------------
    //
    // W, A, S, D, E, F, G and Q are movement keys AND ordinary letters. Typing a
    // building name into the Go-to search walked the camera, inspected twice and
    // toggled free-fly, all behind the open panel where none of it showed until
    // the panel closed and the visitor was somewhere else. Reported from use.
    const typed = await page.evaluate(async () => {
      const api = window.__chicago4d;
      api.setFly(false);
      api.walker.teleport({ local_e: 107, local_n: -103, yaw_deg: 180 });
      await new Promise((r) => setTimeout(r, 60));
      const before = { e: api.player.e, n: api.player.n, flying: api.flying };
      // Open the Go-to tab first: the field is in a hidden panel until then,
      // and a hidden field cannot take focus, which is not what this is testing.
      window.__chicago4d.hud.setPanel(true);
      document.querySelector('.panel-tab[data-tab="goto"]')?.click();
      await new Promise((r) => setTimeout(r, 120));
      const box = document.getElementById('jump-search');
      box.focus();
      // "sauganash" is w/a/s/d/g-rich on purpose: every letter here is bound.
      for (const ch of 'sauganash wafd') {
        const code = ch === ' ' ? 'Space' : `Key${ch.toUpperCase()}`;
        for (const type of ['keydown', 'keyup']) {
          box.dispatchEvent(new KeyboardEvent(type, { key: ch, code, bubbles: true }));
        }
      }
      await new Promise((r) => setTimeout(r, 300));
      api.step();
      return { before, after: { e: api.player.e, n: api.player.n, flying: api.flying },
               focused: document.activeElement?.id };
    });
    check(`${label}: typing in the search box does not walk the camera`,
      Math.abs(typed.after.e - typed.before.e) < 0.01
      && Math.abs(typed.after.n - typed.before.n) < 0.01,
      `moved from ${typed.before.e.toFixed(2)},${typed.before.n.toFixed(2)} `
      + `to ${typed.after.e.toFixed(2)},${typed.after.n.toFixed(2)}`);
    check(`${label}: typing an 'f' does not take off`,
      typed.after.flying === false && typed.focused === 'jump-search',
      `flying ${typed.after.flying}, focus ${typed.focused}`);

    // --- the Go to tab ------------------------------------------------------
    //
    // Going somewhere is not a setting, and it used to be two settings: a
    // "Named viewpoints" row of chips with, underneath it, a search containing
    // the same ground and more of it. Both are now one list in one tab, second
    // after Controls. These assertions are what would notice the duplicate
    // coming back, or the tab quietly moving to the end of the strip where
    // nobody opens it.
    // T-0701 RESTATED, NOT WEAKENED. The strip became a RAIL: seven sections
    // (Go to, Travel, People, Evidence, Settings, Controls, What's new) in a
    // 66 px icon column on the desktop drawer and one row across the top of the
    // phone sheet. The old read measured `offsetTop` alone, which on a column
    // would report seven "rows" and fail a correct rail — so both axes are read
    // and the viewport says which one has to collapse to a single value. The
    // overflow and squeeze reads are kept and widened to both axes: an item
    // whose scrollHeight exceeds its box is a label pushed out of its button
    // just as surely as one whose scrollWidth does. Labels are ALLOWED to wrap
    // onto two lines by design ("What's / new"), which is why the button is
    // measured and never the label.
    const tabStrip = await page.evaluate(() => {
      const bar = document.querySelector('.panel-tabs');
      const items = [...bar.querySelectorAll('.panel-tab')];
      return {
        order: items.map((el) => el.dataset.tab),
        // A rail that has silently become two columns (desktop) or two rows
        // (phone) is the failure mode this panel has already had once, so
        // measure the geometry rather than trust the flex direction to hold.
        // The tabs only: the close button lives in the head row, not the rail.
        rows: new Set(items.map((el) => Math.round(el.offsetTop))).size,
        cols: new Set(items.map((el) => Math.round(el.offsetLeft))).size,
        overflow: Math.max(Math.round(bar.scrollWidth - bar.clientWidth),
          Math.round(bar.scrollHeight - bar.clientHeight)),
        // The tabs are allowed to shrink, so "one line, no overflow" can also be
        // reached by squeezing a label out past its own button. Count that too,
        // in both directions.
        squeezed: items.filter((el) => el.scrollWidth > el.clientWidth + 1
          || el.scrollHeight > el.clientHeight + 1).map((el) => el.dataset.tab),
        // Every item has a real box: a rail item collapsed to nothing would
        // trivially satisfy "one column, unsqueezed".
        boxless: items.filter((el) => el.getBoundingClientRect().height < 40
          || el.getBoundingClientRect().width < 40).map((el) => el.dataset.tab),
        strayViewpointList: document.querySelectorAll(
          '[data-panel="settings"] .anchor-btn, #anchors').length,
      };
    });
    // Was "Go to is a tab of its own, immediately after Controls" (five tabs).
    // The claim is the same — the rail's order is exact and Go to leads it —
    // over the seven sections T-0701 gave the drawer.
    check(`${label}: the rail lists the seven sections in order, Go to first`,
      tabStrip.order.join(',') === 'goto,travel,people,evidence,settings,controls,whatsnew',
      tabStrip.order.join(','));
    // Was "five tabs still fit the panel on one row, unsqueezed". Seven items
    // now, one column on the desktop drawer and one row on the phone sheet.
    check(`${label}: seven rail items fit the panel unsqueezed — one column on desktop, one row on a phone`,
      (touch ? tabStrip.rows === 1 : tabStrip.cols === 1)
      && tabStrip.overflow <= 1 && !tabStrip.squeezed.length && !tabStrip.boxless.length,
      `${tabStrip.rows} row(s) x ${tabStrip.cols} column(s), ${tabStrip.overflow}px of rail `
      + `overflow, squeezed [${tabStrip.squeezed.join(', ')}], boxless [${tabStrip.boxless.join(', ')}]`);
    check(`${label}: Settings no longer carries a second list of viewpoints`,
      tabStrip.strayViewpointList === 0, `${tabStrip.strayViewpointList} stray node(s)`);

    // G, from the walk, with the panel shut.
    await clickChrome('#panel-close');
    await page.keyboard.press('g');
    await page.waitForTimeout(60);
    const viaKey = await page.evaluate(() => ({
      open: !document.getElementById('panel').hasAttribute('hidden'),
      tab: document.querySelector('.panel-tab.is-on')?.dataset.tab,
      focused: document.activeElement?.id,
    }));
    check(`${label}: G opens the Go to tab`,
      viaKey.open && viaKey.tab === 'goto'
      // The search takes focus for a visitor who arrived by keyboard, and must
      // not on a phone: focusing it there raises the on-screen keyboard over
      // the list the tap was for.
      && (touch ? viaKey.focused !== 'jump-search' : viaKey.focused === 'jump-search'),
      JSON.stringify(viaKey));

    // T-0702 RESTATED, NOT WEAKENED. The list now grades a row by the record's
    // PRESENCE — did the building stand here — and hides the roofs whose
    // presence is `reconstructed` until the visitor asks for them, so "every
    // loaded structure" is read in two halves that together say more than the
    // old single count did: the default list is exactly the non-reconstructed
    // records, and the toggle brings the list to exactly the registry. The
    // position grade did not leave the row — it moved to `data-jump-position`
    // and is compared record for record as before. The presence rule is
    // inlined here rather than imported, so the gate cannot agree with the app
    // by sharing its mistake: `documented_range.confidence`, else the position
    // grade, else `reconstructed`.
    const jumps = await page.evaluate(() => {
      const api = window.__chicago4d;
      const input = document.getElementById('jump-search');
      const registry = api.registry;
      const presenceOf = (s) => s?.documented_range?.confidence
        || s?.placement?.position_confidence || 'reconstructed';
      const positionOf = (s) => s?.placement?.position_confidence || 'reconstructed';
      const rowsNow = () => [...document.querySelectorAll('#jump-results .jump-result')];
      const structRows = () => rowsNow().filter((r) => r.dataset.jumpKind === 'structure');
      // The stated preconditions for everything below, and for the arrival
      // check that follows: the list on All, no query, reconstructed roofs
      // hidden (the default), travel mode `instantly` (the default) — a ride
      // would take minutes to reach Randolph and Canal and the arrival read
      // would measure a visitor still walking.
      api.setTravelMode('instantly');
      api.hud.goTo.setKind('all');
      input.value = '';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      const toggle = document.getElementById('jump-reconstructed');
      const setToggle = (on) => {
        if (toggle.checked === on) return;
        toggle.checked = on;
        toggle.dispatchEvent(new Event('change', { bubbles: true }));
      };
      setToggle(false);
      // The registry's own tallies, counted here and not read off the app.
      const tally = { attested: 0, inferred: 0, reconstructed: 0 };
      const posTally = { attested: 0, inferred: 0, reconstructed: 0 };
      for (const [, record] of registry) {
        const g = presenceOf(record?.sidecar);
        if (g in tally) tally[g]++;
        const p = positionOf(record?.sidecar);
        if (p in posTally) posTally[p]++;
      }
      const nonReconstructed = registry.size - tally.reconstructed;
      // And the colour has to carry the distinction, which is exactly what a
      // bare `.jump-result small` rule took away from it once: it outranks
      // `.conf-inferred` on specificity and painted all three grades the same
      // dim grey — a legend that lies, in a project whose whole product is the
      // grading.
      const colourOf = (grade) => {
        const chip = document.querySelector(`.jump-result .conf-${grade}`);
        return chip ? getComputedStyle(chip).color : null;
      };
      const rows = rowsNow();
      const dflt = {
        structures: structRows().length,
        anchors: rows.filter((r) => r.dataset.jumpKind === 'anchor').length,
        intersections: rows.filter((r) => r.dataset.jumpKind === 'intersection').length,
        chippedNonStructures: rows.filter((r) => r.dataset.jumpKind !== 'structure'
          && r.querySelector('.conf')).length,
        // Only the two grades that stood here should be chipped before the toggle.
        chipGrades: [...new Set(structRows().map((r) => r.querySelector('.conf')?.textContent.trim()))],
        note: document.getElementById('jump-note')?.textContent ?? '',
        colours: {
          attested: colourOf('attested'),
          inferred: colourOf('inferred'),
          reconstructed: colourOf('reconstructed'),
          plain: getComputedStyle(document.querySelector('.jump-result .jump-name')).color,
        },
      };
      // The toggle on: every roof, and every row compared to its record.
      setToggle(true);
      const mismatched = [];
      let graded = 0;
      for (const row of structRows()) {
        const s = registry.get(row.dataset.jumpId)?.sidecar;
        const wantPresence = presenceOf(s);
        const wantPosition = positionOf(s);
        const chip = row.querySelector('.conf');
        const shown = chip?.textContent?.trim();
        if (shown === wantPresence && chip.classList.contains(`conf-${wantPresence}`)
          && row.dataset.jumpConfidence === wantPresence
          && row.dataset.jumpPosition === wantPosition) graded++;
        else {
          mismatched.push({ id: row.dataset.jumpId, wantPresence, shown: shown ?? null,
            wantPosition, position: row.dataset.jumpPosition ?? null });
        }
      }
      const on = {
        structures: structRows().length,
        note: document.getElementById('jump-note')?.textContent ?? '',
        colours: { reconstructed: colourOf('reconstructed') },
      };
      setToggle(false);
      const all = {
        anchors: dflt.anchors,
        structures: dflt.structures,
        intersections: dflt.intersections,
        loaded: registry.size,
        sceneAnchors: api.scene?.anchors?.length ?? 0,
        sceneIntersections: api.intersections?.length ?? 0,
        chippedNonStructures: dflt.chippedNonStructures,
      };
      // The default colours, with the reconstructed chip's colour read while
      // the toggle was on (no reconstructed row is on the default list).
      const colours = { ...dflt.colours, reconstructed: on.colours.reconstructed };
      input.value = 'Randolph Canal';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      const filtered = [...document.querySelectorAll('#jump-results .jump-result')]
        .map((b) => ({ id: b.dataset.jumpId, kind: b.dataset.jumpKind, text: b.textContent }));
      return { all, filtered, graded, mismatched, tally, posTally, nonReconstructed,
        dflt: { structures: dflt.structures, chipGrades: dflt.chipGrades, note: dflt.note },
        on: { structures: on.structures, note: on.note }, colours, stored:
          JSON.parse(localStorage.getItem('chicago4d.settings') || '{}').gotoReconstructed };
    });
    // Was "jump menu includes every loaded structure" (=== registry.size). The
    // list now hides presence-reconstructed roofs by default, so the claim is
    // taken in both states: exactly the non-reconstructed records by default,
    // exactly the registry with the toggle on — and the toggle's own state is
    // persisted where the visitor's settings live.
    check(`${label}: jump menu lists every structure that stood here, and every roof once asked`,
      jumps.dflt.structures === jumps.nonReconstructed && jumps.nonReconstructed > 70
      && jumps.on.structures === jumps.all.loaded && jumps.all.loaded > jumps.nonReconstructed
      && jumps.dflt.chipGrades.every((g) => g === 'attested' || g === 'inferred')
      && jumps.stored === false,
      `${jumps.dflt.structures} listed of ${jumps.nonReconstructed} non-reconstructed by default `
      + `(chips ${jumps.dflt.chipGrades.join('/')}); ${jumps.on.structures} of ${jumps.all.loaded} `
      + `loaded with the toggle on; stored gotoReconstructed ${jumps.stored}`);
    // Against the compiled list, NOT against a literal. This assertion read
    // `=== 4` until T-0245 committed a fifth control point on South Water at
    // Franklin and turned a correct menu into a red gate — the same fault the
    // menu itself was built to avoid, one level up: the intersections are
    // compiled into the scene sidecar index from data/traces/street_control.json
    // on every check, so their number is data and a gate that hard-codes it is
    // measuring the constant rather than the menu.
    check(`${label}: jump menu includes every verified intersection`,
      jumps.all.intersections === jumps.all.sceneIntersections
        && jumps.all.intersections > 3,
      `${jumps.all.intersections} listed of ${jumps.all.sceneIntersections} compiled`);
    check(`${label}: jump menu includes every viewpoint the scene names`,
      jumps.all.anchors === jumps.all.sceneAnchors && jumps.all.anchors > 3,
      `${jumps.all.anchors} listed of ${jumps.all.sceneAnchors} in the scene`);
    // Was "every structure result carries its record's position grade" (the
    // chip). T-0702 made the chip the PRESENCE grade and moved the position
    // grade to `data-jump-position`; both are compared to the record on every
    // row, with the toggle on so all of them are checked, not the default 80-odd.
    check(`${label}: every structure result carries its record's presence grade as its chip and its position grade as data`,
      jumps.graded === jumps.all.loaded && !jumps.mismatched.length,
      `${jumps.graded} graded of ${jumps.all.loaded}, `
      + `mismatched ${JSON.stringify(jumps.mismatched.slice(0, 3))}`);
    check(`${label}: a viewpoint and a survey junction are not graded like a building`,
      jumps.all.chippedNonStructures === 0,
      `${jumps.all.chippedNonStructures} non-structure result(s) carry a confidence chip`);
    // Was "inferred vs reconstructed, and inferred vs plain". Attested chips are
    // on the default list now (the Sauganash stood here), reconstructed ones only
    // after the toggle — all three pairwise distinct and none the name's colour.
    check(`${label}: the three grades are told apart by colour, not only by their words`,
      (() => {
        const c = jumps.colours;
        const three = [c.attested, c.inferred, c.reconstructed];
        return three.every(Boolean) && new Set(three).size === 3
          && three.every((x) => x !== c.plain);
      })(),
      JSON.stringify(jumps.colours));
    // Was "N structures / N are attested / N inferred / N reconstructed" against
    // the position tally. The note now counts PRESENCE (REPORT-goto wording):
    // "83 of 371 structures — 288 reconstructed roofs are hidden until you ask
    // for them. Of all 371, 11 are attested to have stood here, 72 inferred and
    // 288 reconstructed." — every figure against the registry tally computed
    // above, in both toggle states.
    check(`${label}: the tab counts its own list rather than quoting a written total`,
      jumps.dflt.note.includes(`${jumps.nonReconstructed} of ${jumps.all.loaded} structures`)
      && jumps.dflt.note.includes(`${jumps.tally.reconstructed} reconstructed roofs are hidden`)
      && jumps.dflt.note.includes(`${jumps.tally.attested} are attested`)
      && jumps.dflt.note.includes(`${jumps.tally.inferred} inferred`)
      && jumps.dflt.note.includes(`${jumps.tally.reconstructed} reconstructed`)
      && jumps.on.note.includes(`${jumps.all.loaded} of ${jumps.all.loaded} structures`)
      && jumps.on.note.includes(`${jumps.tally.reconstructed} reconstructed roofs are showing`),
      `${jumps.dflt.note} / ${jumps.on.note} / ${JSON.stringify(jumps.tally)}`);
    check(`${label}: jump search finds an intersection by both street names`,
      jumps.filtered.some((r) => r.id === 'randolph_canal' && r.kind === 'intersection'),
      JSON.stringify(jumps.filtered));
    // Precondition stated inside `jumps`: `api.setTravelMode('instantly')`, the
    // default — in a ground mode this click would start a walk, not a jump.
    await clickChrome('[data-jump-id="randolph_canal"]');
    await page.waitForTimeout(80);
    const arrived = await page.evaluate(() => {
      // Leave the list as the visitor finds it: no query, All.
      const input = document.getElementById('jump-search');
      input.value = '';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      return { ...window.__chicago4d.player, mode: window.__chicago4d.travel.mode,
        phase: window.__chicago4d.travelState.phase };
    });
    check(`${label}: an intersection result moves the visitor there`,
      Math.abs(arrived.e + 155.24) < 0.2 && Math.abs(arrived.n + 251.19) < 0.2
      && arrived.mode === 'instantly' && arrived.phase === 'idle',
      `arrived (${arrived.e?.toFixed(2)}, ${arrived.n?.toFixed(2)}) in mode ${arrived.mode}, ${arrived.phase}`);

    // --- the drawer, and what T-0701…T-0710 put in it ------------------------
    //
    // New with the drawer. Each block below leaves the chrome as it found it:
    // panel CLOSED at the end, travel mode `instantly`, pace `walk`, head bob
    // on, the Go-to list on All with no query, no person card open, the
    // Evidence hub showing.

    // T-0701: the drawer and the building card share the right-hand slot. With
    // a card open, opening the drawer TUCKS the card (a transform + visibility,
    // never `hidden` — the card must not be collateral, see part 13) and
    // closing brings it back. The .24 s transition is polled to its end rather
    // than waited for: under load a fixed wait was not enough (REPORT-shell).
    // The drawer itself reaches the bottom of the viewport and starts under the
    // year badge on the desktop.
    const drawer = await page.evaluate(async () => {
      const api = window.__chicago4d;
      const popup = document.getElementById('popup');
      const panel = document.getElementById('panel');
      const badge = document.getElementById('year-badge');
      const settle = async (pred) => {
        for (let i = 0; i < 60 && !pred(); i++) await new Promise((r) => setTimeout(r, 100));
        return pred();
      };
      const intersects = (a, b) => !(a.right <= b.left || b.right <= a.left
        || a.bottom <= b.top || b.bottom <= a.top);
      api.hud.setPanel(false);
      api.pick('sauganash_hotel');
      await settle(() => getComputedStyle(popup).visibility === 'visible');
      const openHidden = popup.hasAttribute('hidden');
      api.hud.setPanel(true);
      const tucked = await settle(() => getComputedStyle(popup).visibility === 'hidden'
        || !intersects(popup.getBoundingClientRect(), panel.getBoundingClientRect()));
      const pr = panel.getBoundingClientRect();
      const br = badge.getBoundingClientRect();
      const out = {
        openHidden,
        tucked,
        tuckedHidden: popup.hasAttribute('hidden'),
        tuckedVisibility: getComputedStyle(popup).visibility,
        tuckedIntersects: intersects(popup.getBoundingClientRect(), pr),
        panelHidden: panel.hasAttribute('hidden'),
        panelBottom: Math.round(pr.bottom),
        panelTop: Math.round(pr.top),
        badgeBottom: Math.round(br.bottom),
        innerHeight,
      };
      api.hud.setPanel(false);
      out.back = await settle(() => getComputedStyle(popup).visibility === 'visible'
        && getComputedStyle(popup).transform === 'none');
      out.backHidden = popup.hasAttribute('hidden');
      api.popup.close();
      return out;
    });
    check(`${label}: opening the drawer tucks an open card aside without closing it`,
      drawer.openHidden === false && drawer.tucked && drawer.tuckedHidden === false
      && !drawer.tuckedIntersects && !drawer.panelHidden,
      `card hidden ${drawer.tuckedHidden}, visibility ${drawer.tuckedVisibility}, `
      + `intersects the drawer ${drawer.tuckedIntersects}`);
    check(`${label}: closing the drawer brings the tucked card back`,
      drawer.back && drawer.backHidden === false, `back ${drawer.back}, hidden ${drawer.backHidden}`);
    check(`${label}: the drawer reaches the bottom of the screen and starts under the year badge`,
      drawer.panelBottom >= drawer.innerHeight - 1 && (touch || drawer.panelTop >= drawer.badgeBottom),
      `drawer ${drawer.panelTop}–${drawer.panelBottom} of ${drawer.innerHeight}, badge bottom ${drawer.badgeBottom}`);

    // T-0702/T-0703: the Go-to pills, groups, distances and keyboard.
    await clickChrome('#btn-help');
    await clickChrome('.panel-tab[data-tab="goto"]');
    const gotoMore = await page.evaluate(async () => {
      const api = window.__chicago4d;
      const registry = api.registry;
      const rows = () => [...document.querySelectorAll('#jump-results .jump-result')];
      const KIND_IDS = ['viewpoints', 'corners', 'people', 'taverns', 'stores', 'trades',
        'homes', 'public', 'waterfront'];
      const out = {};
      const pill = document.querySelector('.jump-pill[data-kind="taverns"]');
      pill.click();
      const tav = rows();
      out.taverns = {
        pressed: pill.getAttribute('aria-pressed'),
        rows: tav.length,
        sauganash: tav.some((r) => r.dataset.jumpId === 'sauganash_hotel'),
        allStructures: tav.every((r) => r.dataset.jumpKind === 'structure'),
        offKind: tav.filter((r) => {
          const s = registry.get(r.dataset.jumpId)?.sidecar;
          const fn = String(s?.attributes?.function?.value ?? '').toLowerCase();
          return !(/tavern|inn|hotel|boarding|lodging/.test(fn) || s?.archetype === 'frame_tavern');
        }).map((r) => r.dataset.jumpId),
        heading: (document.querySelector('.jump-group[data-group="taverns"]')?.textContent ?? '')
          .replace(/\d+\s*$/, '').trim(),
        label: pill.querySelector('.jump-pill-label')?.textContent.trim() ?? pill.textContent.trim(),
        groups: document.querySelectorAll('.jump-group').length,
      };
      // Back to All, every roof shown so every structure row is judged.
      api.hud.goTo.setKind('all');
      api.hud.goTo.setIncludeReconstructed(true);
      const all = rows();
      const headingFor = (row) => {
        let el = row.previousElementSibling;
        while (el && !el.classList.contains('jump-group')) el = el.previousElementSibling;
        return el?.dataset.group ?? null;
      };
      out.groups = {
        rows: all.length,
        structures: all.filter((r) => r.dataset.jumpKind === 'structure').length,
        unknownGroup: all.filter((r) => !KIND_IDS.includes(r.dataset.jumpGroup)).map((r) => r.dataset.jumpId),
        misfiled: all.filter((r) => headingFor(r) !== r.dataset.jumpGroup).map((r) => r.dataset.jumpId),
      };
      // Distance and compass on every row.
      const DIST = /^(\d+(\.\d+)? (ft|m|mi|km)) (N|NNE|NE|ENE|E|ESE|SE|SSE|S|SSW|SW|WSW|W|WNW|NW|NNW)$|^here$/;
      out.dist = {
        bad: all.filter((r) => !DIST.test((r.querySelector('.jump-dist')?.textContent ?? '').trim()))
          .map((r) => `${r.dataset.jumpId} "${(r.querySelector('.jump-dist')?.textContent ?? '').trim()}"`),
        noMetres: all.filter((r) => !/^\d+$/.test(r.querySelector('.jump-dist')?.dataset.m ?? '')).length,
      };
      api.hud.goTo.setIncludeReconstructed(false);
      // Stand 100 m due east of the Sauganash, then 200 m: the row's metres
      // follow the visitor by ≈100 and the compass says west both times.
      const sp = api.structurePosition('sauganash_hotel');
      const rowM = () => {
        const d = document.querySelector('[data-jump-id="sauganash_hotel"] .jump-dist');
        return { m: Number(d?.dataset.m), text: d?.textContent.trim() ?? '' };
      };
      api.setFly(false);
      api.walker.teleport({ local_e: sp.e + 100, local_n: sp.n, yaw_deg: 270 });
      api.hud.goTo.refreshDistances();
      const at100 = rowM();
      api.walker.teleport({ local_e: sp.e + 200, local_n: sp.n, yaw_deg: 270 });
      api.hud.goTo.refreshDistances();
      const at200 = rowM();
      out.follow = { at100, at200, imperial: (api.hud.settings.units ?? 'imperial') !== 'metric' };
      // The keyboard: the list starts with NO row active (a fresh combobox), so
      // the first ArrowDown highlights the first row, the second the second —
      // which is what REPORT-goto measured (`jump-opt-1` after two). Three
      // presses reach the third row, and Enter goes there, instantly. The plan
      // wrote "ArrowDown×2 → the third row"; that would need the first row
      // pre-selected, which this list does not do (SMOKE-FINDINGS notes it).
      api.setTravelMode('instantly');
      api.popup.close();
      const input = document.getElementById('jump-search');
      input.value = '';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      const second = rows()[1];
      const third = rows()[2];
      const t = { kind: third?.dataset.jumpKind, id: third?.dataset.jumpId };
      const target = api.hud.goTo.targets.find((x) => x.kind === t.kind && x.id === t.id);
      input.focus();
      const activeId = () => document.querySelector('#jump-results .jump-result.is-active')?.dataset.jumpId;
      for (const key of ['ArrowDown', 'ArrowDown']) {
        input.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true }));
      }
      const afterTwo = { active: activeId(), second: second?.dataset.jumpId,
        described: input.getAttribute('aria-activedescendant') };
      input.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
      const active = activeId();
      input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      await new Promise((r) => setTimeout(r, 120));
      const p = api.player;
      const dest = t.kind === 'person' ? (target?.lives_at || target?.works_at) : t.id;
      const pos = (t.kind === 'structure' || t.kind === 'person') ? api.structurePosition(dest)
        : { e: target?.e, n: target?.n };
      out.enter = {
        third: t, afterTwo, active, dest,
        panelHidden: document.getElementById('panel').hasAttribute('hidden'),
        card: api.popup.openId,
        distToTarget: pos ? +Math.hypot(p.e - pos.e, p.n - pos.n).toFixed(1) : null,
        phase: api.travelState.phase,
      };
      return out;
    });
    check(`${label}: the Taverns pill narrows the list to taverns, inns and hotels, the Sauganash among them`,
      gotoMore.taverns.pressed === 'true' && gotoMore.taverns.rows >= 5 && gotoMore.taverns.sauganash
      && gotoMore.taverns.allStructures && !gotoMore.taverns.offKind.length
      && gotoMore.taverns.heading === gotoMore.taverns.label && gotoMore.taverns.groups === 1,
      `${gotoMore.taverns.rows} row(s), off-kind [${gotoMore.taverns.offKind.join(', ')}], heading `
      + `"${gotoMore.taverns.heading}" vs pill "${gotoMore.taverns.label}", ${gotoMore.taverns.groups} heading(s)`);
    check(`${label}: every row is filed under one of the nine kinds, beneath that kind's heading`,
      gotoMore.groups.structures > 300 && !gotoMore.groups.unknownGroup.length
      && !gotoMore.groups.misfiled.length,
      `${gotoMore.groups.rows} rows; unknown group [${gotoMore.groups.unknownGroup.slice(0, 3).join(', ')}]; `
      + `misfiled [${gotoMore.groups.misfiled.slice(0, 3).join(', ')}]`);
    check(`${label}: every row says how far and which way`,
      !gotoMore.dist.bad.length && gotoMore.dist.noMetres === 0,
      `bad [${gotoMore.dist.bad.slice(0, 3).join('; ')}], ${gotoMore.dist.noMetres} without metres`);
    check(`${label}: the distances follow the visitor — 100 m further east reads 100 m further`,
      Math.abs(gotoMore.follow.at100.m - 100) <= 2 && Math.abs(gotoMore.follow.at200.m - 200) <= 2
      && / W$/.test(gotoMore.follow.at100.text) && / W$/.test(gotoMore.follow.at200.text)
      && new RegExp(`^(${gotoMore.follow.imperial ? '327|328|329|330' : '99|100|101'}) `).test(gotoMore.follow.at100.text),
      `${JSON.stringify(gotoMore.follow.at100)} -> ${JSON.stringify(gotoMore.follow.at200)}`);
    check(`${label}: ArrowDown steps the list a row at a time — two reach the second, three the third — and Enter goes there`,
      gotoMore.enter.afterTwo.active === gotoMore.enter.afterTwo.second && !!gotoMore.enter.afterTwo.described
      && gotoMore.enter.active === gotoMore.enter.third.id && gotoMore.enter.panelHidden
      && gotoMore.enter.phase === 'idle'
      && (gotoMore.enter.third.kind === 'structure' || gotoMore.enter.third.kind === 'person'
        ? gotoMore.enter.card === gotoMore.enter.dest && gotoMore.enter.distToTarget <= 40
        : gotoMore.enter.distToTarget <= 0.5),
      JSON.stringify(gotoMore.enter));

    // T-0704/T-0705: Travel — five modes, persisted; the paces through the
    // walker's own WALK; the horse's gait; nothing under reduced motion.
    await clickChrome('#btn-help');
    await clickChrome('.panel-tab[data-tab="travel"]');
    const gaitLoop = `(() => {
      const a = window.__chicago4d; const w = a.walker; const T = a.travel; const I = a.intent;
      let peak = 0; let speed = 0;
      for (let i = 0; i < 30; i++) {
        I.forward = 1;
        T.update(1 / 30, I); w.update(1 / 30, I); T.afterWalk(I, 1 / 30);
        peak = Math.max(peak, Math.abs(w.state.bob));
        speed = Math.max(speed, w.state.speed);
      }
      I.clear();
      for (let i = 0; i < 15; i++) { T.update(1 / 30, I); w.update(1 / 30, I); T.afterWalk(I, 1 / 30); }
      // speed is the peak WHILE moving (this text is inside a template string,
      // so no backticks here) — proof the walker actually walked, not one stuck.
      return { peak: +peak.toFixed(3), after: +w.state.bob.toFixed(4), speed: +speed.toFixed(2) };
    })()`;
    const travelUi = await page.evaluate((loop) => {
      const api = window.__chicago4d;
      const WALK = api.walkBudget;
      const w = api.walker;
      const stored = () => JSON.parse(localStorage.getItem('chicago4d.settings') || '{}').travelMode;
      const modes = [...document.querySelectorAll('#s-travel .seg-btn')].map((b) => b.dataset.mode);
      document.querySelector('#s-travel .seg-btn[data-mode="horse"]').click();
      const chosen = { stored: stored(), mode: api.travel.mode,
        on: document.querySelector('#s-travel .seg-btn.is-on')?.dataset.mode,
        checked: document.querySelector('#s-travel .seg-btn[aria-checked="true"]')?.dataset.mode };
      document.querySelector('#s-travel .seg-btn[data-mode="instantly"]').click();
      const restored = { stored: stored(), mode: api.travel.mode };
      // The paces, read through the walker's WALK and its eye.
      const eye = () => +(w.state.eyeY - w.state.groundY).toFixed(3);
      api.setFly(false);
      api.walker.teleport({ local_e: -155.24, local_n: -251.19, yaw_deg: 0 });
      const paces = {};
      for (const pace of ['horse', 'wagon', 'walk']) {
        api.setPace(pace);
        paces[pace] = { speed: WALK.speed, sprint: WALK.sprintSpeed, eye: eye(),
          chip: document.getElementById('btn-pace')?.dataset.pace };
      }
      const slider = api.hud.settings.speed;
      // T-0823: each pace has its own slider, and the walker's WALK follows the
      // one for the pace in force. Read the three stored values, each slider's
      // ceiling, and what the readout SAYS as the horse's slider is dragged.
      const sliders = { walk: api.hud.settings.speed, wagon: api.hud.settings.wagonSpeed, horse: api.hud.settings.horseSpeed };
      const range = (id) => { const el = document.getElementById(id); return el && { min: Number(el.min), max: Number(el.max), value: Number(el.value) }; };
      const drag = (id, v) => { const el = document.getElementById(id); el.value = String(v); el.dispatchEvent(new Event('input', { bubbles: true })); return document.getElementById(id.replace('s-', 'v-'))?.textContent.trim() ?? ''; };
      const ranges = { walk: range('s-speed'), wagon: range('s-wagon-speed'), horse: range('s-horse-speed') };
      api.setPace('horse');
      const before = api.hud.settings.horseSpeed;
      const gaits = { canter: drag('s-horse-speed', 6.5), gallop: drag('s-horse-speed', 10), top: drag('s-horse-speed', 26.82) };
      const atTop = { speed: WALK.speed, sprint: WALK.sprintSpeed };
      drag('s-horse-speed', before);
      const afterDrag = { speed: WALK.speed, sprint: WALK.sprintSpeed };
      gaits.walkWord = drag('s-speed', api.hud.settings.speed);
      gaits.wagonWord = drag('s-wagon-speed', api.hud.settings.wagonSpeed);
      api.setPace('walk');
      const eyeSetting = api.hud.settings.eyeHeight;
      // The gait: horse, own input forward on a street, peak over one second.
      api.setPace('horse');
      const on = eval(loop);
      const bobBox = document.getElementById('s-head-bob');
      bobBox.click();
      const off = { ...eval(loop), setting: api.hud.settings.headBob, checked: bobBox.checked };
      bobBox.click();
      const back = { setting: api.hud.settings.headBob, checked: bobBox.checked };
      api.setPace('walk');
      return { modes, chosen, restored, paces, slider, sliders, ranges, gaits, atTop, afterDrag, eyeSetting, on, off, back };
    }, gaitLoop);
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const reduced = await page.evaluate((loop) => {
      const api = window.__chicago4d;
      api.setPace('horse');
      const r = { matches: matchMedia('(prefers-reduced-motion: reduce)').matches, ...eval(loop) };
      api.setPace('walk');
      return r;
    }, gaitLoop);
    await page.emulateMedia({ reducedMotion: 'no-preference' });
    check(`${label}: Travel offers instantly, walk, wagon, horse and fly`,
      travelUi.modes.join(',') === 'instantly,walk,wagon,horse,fly', travelUi.modes.join(','));
    check(`${label}: the travel mode chosen is the one the walker rides and the one stored`,
      travelUi.chosen.stored === 'horse' && travelUi.chosen.mode === 'horse'
      && travelUi.chosen.on === 'horse' && travelUi.chosen.checked === 'horse'
      && travelUi.restored.stored === 'instantly' && travelUi.restored.mode === 'instantly',
      `${JSON.stringify(travelUi.chosen)} -> ${JSON.stringify(travelUi.restored)}`);
    // T-0823 RESTATED, NOT WEAKENED. The horse's 6.5/11 and the wagon's 3.6 were
    // constants; each pace now has its own slider, so the claim is that WALK
    // follows THAT pace's stored value — sprint = value × factor (2.28 on foot,
    // 1 by wagon, 1.7 in the saddle) capped at the slider's top — and the seats
    // are unchanged. The defaults (1.45 / 3.6 / 6.5) are asserted where the store
    // is fresh, which it is in this run.
    const near = (a, b) => Math.abs(a - b) < 0.01;
    const sp = travelUi.sliders;
    check(`${label}: each pace sets the walker to its own slider, its Shift factor and its seat`,
      near(travelUi.paces.horse.speed, sp.horse) && near(travelUi.paces.horse.sprint, Math.min(sp.horse * 1.7, 26.82))
      && Math.abs(travelUi.paces.horse.eye - (travelUi.eyeSetting + 0.75)) < 0.01
      && near(travelUi.paces.wagon.speed, sp.wagon) && near(travelUi.paces.wagon.sprint, sp.wagon)
      && Math.abs(travelUi.paces.wagon.eye - (travelUi.eyeSetting + 0.5)) < 0.01
      && near(travelUi.paces.walk.speed, sp.walk) && near(travelUi.paces.walk.sprint, Math.min(sp.walk * 2.28, 8.94))
      && Math.abs(travelUi.paces.walk.eye - travelUi.eyeSetting) < 0.01
      && sp.walk === 1.45 && sp.wagon === 3.6 && sp.horse === 6.5
      && travelUi.paces.horse.chip === 'horse' && travelUi.paces.walk.chip === 'walk',
      JSON.stringify({ ...travelUi.paces, sliders: sp, eye: travelUi.eyeSetting }));
    check(`${label}: the three pace sliders top out at 20, 30 and 60 mph and name the gait as they move`,
      travelUi.ranges.walk?.max === 8.94 && travelUi.ranges.wagon?.max === 13.41 && travelUi.ranges.horse?.max === 26.82
      && /^canter · /.test(travelUi.gaits.canter) && /^gallop · /.test(travelUi.gaits.gallop)
      && /^beyond any horse · /.test(travelUi.gaits.top) && /60\.0 mph|96\.5 km\/h/.test(travelUi.gaits.top)
      && /^walk · /.test(travelUi.gaits.walkWord) && /^steady roll · /.test(travelUi.gaits.wagonWord)
      && travelUi.atTop.speed === 26.82 && travelUi.atTop.sprint === 26.82
      && near(travelUi.afterDrag.speed, 6.5) && near(travelUi.afterDrag.sprint, 11.05),
      JSON.stringify({ ranges: travelUi.ranges, gaits: travelUi.gaits, atTop: travelUi.atTop, afterDrag: travelUi.afterDrag }));
    check(`${label}: the horse's gait moves the rider's eye a few centimetres, and stops when they do`,
      travelUi.on.peak >= 0.03 && travelUi.on.peak <= 0.10 && travelUi.on.after === 0
      && travelUi.on.speed > 1,
      JSON.stringify(travelUi.on));
    check(`${label}: the gait is off with the setting off, and back with it`,
      travelUi.off.peak === 0 && travelUi.off.setting === false && travelUi.off.checked === false
      && travelUi.back.setting === true && travelUi.back.checked === true,
      JSON.stringify({ off: travelUi.off, back: travelUi.back }));
    check(`${label}: the gait is off under prefers-reduced-motion`,
      reduced.matches === true && reduced.peak === 0, JSON.stringify(reduced));

    // T-0706/T-0707: a ride. From the South Water viewpoint, on foot, to the
    // Sauganash: the banner says so, the ride ends at the door with the card
    // open, and it goes by the streets. The start is stated because the
    // on-street share depends on it (REQUESTS-travel §4: south_water 100 %,
    // the forks 47 % — the forks sit off any street). `streets.status()` is
    // null off-street, so the read is guarded.
    // T-0824: every arrival — a ride, a flight, an instant Go to — ends at the
    // framing distance for THAT building and with the whole of it in frame. The
    // probe projects the footprint's four extreme ground points and the ridge
    // through the live camera; all five must sit inside NDC ±0.95.
    const FRAMED = `(id) => {
      const a = window.__chicago4d; const w = a.walker;
      const f = a.framing(id); const c = a.structurePosition(id);
      const ground = a.terrain.surfaceHeight(c.e, c.n); const rr = f.radius;
      const pts = [[rr, 0], [-rr, 0], [0, rr], [0, -rr]].map(([de, dn]) => [c.e + de, c.n + dn, ground]);
      pts.push([c.e, c.n, ground + f.height]);
      const ndc = pts.map(([e, n, y]) => { const v = a.project(e, n, y); return [+v.x.toFixed(2), +v.y.toFixed(2), v.z]; });
      return { want: +f.distance.toFixed(1), got: +Math.hypot(c.e - w.state.e, c.n - w.state.n).toFixed(1),
        inFrame: ndc.every(([x, y, z]) => Math.abs(x) <= 0.95 && Math.abs(y) <= 0.95 && z < 1), ndc };
    }`;
    const ride = await page.evaluate(async (FRAMED) => {
      const api = window.__chicago4d;
      const framed = eval(FRAMED);
      const w = api.walker;
      const WALK = api.walkBudget;
      const out = {};
      const dist = (id) => { const p = api.structurePosition(id); return +Math.hypot(p.e - w.state.e, p.n - w.state.n).toFixed(2); };
      api.popup.close();
      api.setFly(false);
      api.goTo('south_water');
      api.setPace('walk');
      api.setTravelMode('walk');
      api.hud.setPanel(true);
      api.hud.selectTab('goto');
      api.hud.goTo.open();
      const row = document.querySelector('[data-jump-id="sauganash_hotel"]');
      row?.click();
      const st = api.travelState;
      const banner = document.getElementById('travel-banner');
      out.go = {
        row: !!row, phase: st.phase, mode: st.mode, dest_id: st.dest_id, dist_m: st.dist_m && +st.dist_m.toFixed(1),
        points: st.remaining_points, panelHidden: document.getElementById('panel').hasAttribute('hidden'),
        bannerHidden: banner.hasAttribute('hidden'), bannerShown: banner.checkVisibility(),
        verb: document.getElementById('travel-verb').textContent.trim(),
        dest: document.getElementById('travel-dest').textContent.trim(),
        distText: document.getElementById('travel-dist').textContent.trim(),
      };
      const budget = (st.dist_m ?? 400) / WALK.speed + 30;
      const r = api.travelSimulate(budget);
      let on = 0;
      for (const [e, n] of r.samples) {
        const m = api.streets.status(e, n)?.mode;
        if (m === 'on' || m === 'intersection') on++;
      }
      out.arrive = { phase: r.phase, seconds: +r.seconds.toFixed(1), budget: +budget.toFixed(0),
        samples: r.samples.length, onStreetPct: +(100 * on / Math.max(1, r.samples.length)).toFixed(0),
        distToCentre: dist('sauganash_hotel'), card: api.popup.openId, framed: framed('sauganash_hotel'),
        bannerHidden: banner.hasAttribute('hidden'), eye: +(w.state.eyeY - w.state.groundY).toFixed(2) };
      // Own input stops a ride — the same call tick() makes, with the visitor's
      // forward set; the intent is theirs and is left as they wrote it.
      api.popup.close();
      api.goTo('south_water');
      api.goToTarget({ kind: 'structure', id: 'sauganash_hotel', label: 'Sauganash Hotel' });
      for (let i = 0; i < 10; i++) { api.travel.update(1 / 30, api.intent); w.update(1 / 30, api.intent); api.travel.afterWalk(api.intent, 1 / 30); }
      const before = api.travelState.phase;
      api.intent.forward = 1;
      api.travel.update(1 / 30, api.intent);
      out.ownInput = { before, after: api.travelState.phase, forwardKept: api.intent.forward,
        bannerHidden: banner.hasAttribute('hidden') };
      api.intent.clear();
      // A second ride, left running for the Stop button below.
      api.goToTarget({ kind: 'structure', id: 'sauganash_hotel', label: 'Sauganash Hotel' });
      for (let i = 0; i < 10; i++) { api.travel.update(1 / 30, api.intent); w.update(1 / 30, api.intent); api.travel.afterWalk(api.intent, 1 / 30); }
      out.beforeStop = { phase: api.travelState.phase, bannerHidden: banner.hasAttribute('hidden') };
      return out;
    }, FRAMED);
    check(`${label}: choosing the Sauganash on foot starts a walk and says so`,
      ride.go.row && ride.go.phase === 'travelling' && ride.go.mode === 'walk'
      && ride.go.dest_id === 'sauganash_hotel' && ride.go.dist_m > 100 && ride.go.points > 1
      && ride.go.panelHidden && !ride.go.bannerHidden && ride.go.bannerShown
      && ride.go.verb === 'Walking to' && /Sauganash/.test(ride.go.dest)
      && /^\d+(\.\d+)? (ft|m|mi|km)$/.test(ride.go.distText),
      JSON.stringify(ride.go));
    check(`${label}: the walk ends at the Sauganash's door with its card open`,
      ride.arrive.phase === 'idle' && ride.arrive.card === 'sauganash_hotel'
      && ride.arrive.framed.inFrame && Math.abs(ride.arrive.framed.got - ride.arrive.framed.want) <= 2.5
      && ride.arrive.bannerHidden
      && Math.abs(ride.arrive.eye - 1.68) < 0.05,
      JSON.stringify(ride.arrive));
    check(`${label}: the walk from South Water keeps to the streets`,
      ride.arrive.samples >= 20 && ride.arrive.onStreetPct >= 70,
      `${ride.arrive.onStreetPct}% of ${ride.arrive.samples} samples on a street or at a corner`);
    check(`${label}: the visitor's own step ends a ride and is not swallowed`,
      ride.ownInput.before === 'travelling' && ride.ownInput.after === 'idle'
      && ride.ownInput.forwardKept === 1 && ride.ownInput.bannerHidden,
      JSON.stringify(ride.ownInput));
    // The Stop button, as a click on the chrome.
    await clickChrome('#travel-stop');
    const stopped = await page.evaluate(() => ({
      phase: window.__chicago4d.travelState.phase,
      bannerHidden: document.getElementById('travel-banner').hasAttribute('hidden'),
    }));
    check(`${label}: the banner's Stop button ends a ride`,
      ride.beforeStop.phase === 'travelling' && !ride.beforeStop.bannerHidden
      && stopped.phase === 'idle' && stopped.bannerHidden,
      `${JSON.stringify(ride.beforeStop)} -> ${JSON.stringify(stopped)}`);
    const flight = await page.evaluate((FRAMED) => {
      const api = window.__chicago4d;
      const framed = eval(FRAMED);
      const w = api.walker;
      const dist = (id) => { const p = api.structurePosition(id); return +Math.hypot(p.e - w.state.e, p.n - w.state.n).toFixed(1); };
      api.popup.close();
      api.setFly(false);
      api.goTo('south_water');
      api.setTravelMode('fly');
      const far = [...api.registry.keys()].map((id) => ({ id, d: dist(id) }))
        .filter((x) => x.d > 250).sort((p, q) => p.d - q.d)[0];
      const ok = api.goToTarget({ kind: 'structure', id: far.id, label: far.id });
      const r = api.travelSimulate(300);
      const fly = { target: far, ok, phase: r.phase, seconds: +r.seconds.toFixed(1),
        maxAltitude: +r.maxAltitude.toFixed(1), flying: w.state.flying, altitude: +w.state.altitude.toFixed(2),
        distToCentre: dist(far.id), card: api.popup.openId, framed: framed(far.id) };
      // And instantly is still instant.
      api.setTravelMode('instantly');
      api.popup.close();
      const okI = api.goToTarget({ kind: 'structure', id: 'sauganash_hotel', label: 'Sauganash Hotel' });
      const instant = { ok: okI, phase: api.travelState.phase, card: api.popup.openId,
        dist: dist('sauganash_hotel'), bannerHidden: document.getElementById('travel-banner').hasAttribute('hidden') };
      api.popup.close();
      return { fly, instant };
    }, FRAMED);
    check(`${label}: flying to a far building climbs to a cruise height, lands and opens its card`,
      flight.fly.ok && flight.fly.phase === 'idle' && flight.fly.maxAltitude >= 20
      && flight.fly.flying === false && flight.fly.altitude < 0.5
      && flight.fly.card === flight.fly.target.id && flight.fly.framed.inFrame
      && Math.abs(flight.fly.framed.got - flight.fly.framed.want) <= 2.5,
      JSON.stringify(flight.fly));
    check(`${label}: instantly is still instant`,
      flight.instant.ok && flight.instant.phase === 'idle' && flight.instant.card === 'sauganash_hotel'
      && flight.instant.dist <= 40 && flight.instant.bannerHidden,
      JSON.stringify(flight.instant));

    // T-0708/T-0709: the People directory — every person, searched, narrowed,
    // opened, and walked to. `open()` is awaited: under swiftshader the record
    // body settles in seconds, and a fixed wait would measure the machine.
    await page.evaluate(() => { window.__chicago4d.hud.setPanel(true); });
    await clickChrome('.panel-tab[data-tab="people"]');
    const people = await page.evaluate(async () => {
      const api = window.__chicago4d;
      const dir = api.people;
      const out = { api: !!dir && typeof dir.search === 'function', error: dir?.error ?? null };
      const scene = api.scene?.id ?? api.year;
      const pj = await (await fetch(new URL(`sidecars/${scene}/people.json`, api.dataBase))).json();
      const manifest = await (await fetch(new URL('residents/index.json', api.dataBase))).json();
      const rows = () => [...document.querySelectorAll('#people-results .person-row')];
      out.counts = { rows: rows().length, api: dir.people, file: pj.people?.length, stated: pj.counts?.people,
        manifest: manifest.counts?.persons,
        countText: document.getElementById('people-count')?.textContent ?? '' };
      out.search = { matched: dir.search('Beaubien'),
        mark: document.querySelector('#people-results [data-person-id="beaubien_mark"] .person-name')?.textContent.trim() ?? null,
        note: document.getElementById('people-result-note')?.textContent ?? '' };
      dir.search('');
      const all = dir.state?.matched;
      out.pill = { all, matched: dir.filter('occupation', 'tavern_keeper'),
        pressed: document.querySelector('.pill[data-filter="occupation"][aria-pressed="true"]')?.dataset.value,
        offTrade: rows().filter((r) => !/^tavern keeper/.test(r.querySelector('.person-sub')?.textContent.trim() ?? ''))
          .map((r) => r.dataset.personId), rows: rows().length };
      dir.filter('occupation', '');
      out.pill.cleared = dir.state?.matched;
      const opened = await dir.open('hogan_john_s_c');
      const card = document.getElementById('people-card');
      const go = card?.querySelector('.people-go');
      out.card = { opened, hidden: card?.hasAttribute('hidden'), shown: card?.checkVisibility(),
        name: card?.querySelector('.people-card-name')?.textContent.trim() ?? '',
        title: document.getElementById('panel-title')?.textContent.trim() ?? '',
        backShown: !document.getElementById('panel-back')?.hasAttribute('hidden'),
        go: go?.dataset.structure ?? null, goText: go?.textContent.replace(/\s+/g, ' ').trim() ?? '',
        fields: !!card?.querySelector('.res-fields') };
      return out;
    });
    check(`${label}: the People directory lists the town, and its count is the file's and the manifest's`,
      people.api && !people.error && people.counts.rows > 0 && people.counts.api === people.counts.file
      && people.counts.file === people.counts.stated && people.counts.stated === people.counts.manifest
      && people.counts.manifest > 1000
      && new RegExp(`^${String(people.counts.manifest).replace(/\B(?=(\d{3})+$)/g, ',?')} people`).test(people.counts.countText),
      JSON.stringify(people.counts));
    check(`${label}: searching "Beaubien" finds Mark Beaubien`,
      people.search.matched > 0 && people.search.matched < 100 && /Mark Beaubien/.test(people.search.mark ?? '')
      && /Beaubien/.test(people.search.note),
      JSON.stringify(people.search));
    check(`${label}: the tavern-keeper pill narrows the list to tavern keepers`,
      people.pill.matched > 0 && people.pill.matched < people.pill.all && people.pill.rows === people.pill.matched
      && !people.pill.offTrade.length && people.pill.pressed === 'tavern_keeper' && people.pill.cleared === people.pill.all,
      JSON.stringify(people.pill));
    check(`${label}: opening a person shows their card with a way to their building`,
      people.card.opened && people.card.hidden === false && people.card.shown && /Hogan/.test(people.card.name)
      && people.card.title === people.card.name && people.card.backShown && people.card.go === 'hogan_store'
      && /Go to where they/.test(people.card.goText) && people.card.fields,
      JSON.stringify(people.card));
    // Go there, on horseback: the drawer closes, the ride ends at Hogan's with its card.
    await page.evaluate(() => { window.__chicago4d.setTravelMode('horse'); window.__chicago4d.popup.close(); });
    await clickChrome('#people-card .people-go');
    const goThere = await page.evaluate((FRAMED) => {
      const api = window.__chicago4d;
      const framed = eval(FRAMED);
      const w = api.walker;
      const st = api.travelState;
      const start = { phase: st.phase, mode: st.mode, dest_id: st.dest_id, person: st.person,
        panelHidden: document.getElementById('panel').hasAttribute('hidden'),
        verb: document.getElementById('travel-verb').textContent.trim() };
      const r = api.travelSimulate(((st.dist_m ?? 300) / 6.5) + 30);
      const p = api.structurePosition('hogan_store');
      const end = { phase: r.phase, seconds: +r.seconds.toFixed(1), card: api.popup.openId,
        distToCentre: +Math.hypot(p.e - w.state.e, p.n - w.state.n).toFixed(2), framed: framed('hogan_store') };
      api.setTravelMode('instantly');
      api.popup.close();
      api.people.close();
      return { start, end, cardClosed: document.getElementById('people-card').hasAttribute('hidden') };
    }, FRAMED);
    check(`${label}: Go there rides to the person's building and opens its card`,
      goThere.start.phase === 'travelling' && goThere.start.mode === 'horse'
      && goThere.start.dest_id === 'hogan_store' && goThere.start.person === 'hogan_john_s_c'
      && goThere.start.panelHidden && goThere.start.verb === 'Riding to'
      && goThere.end.phase === 'idle' && goThere.end.card === 'hogan_store' && goThere.end.framed.inFrame
      && Math.abs(goThere.end.framed.got - goThere.end.framed.want) <= 2.5
      && goThere.cardClosed,
      JSON.stringify(goThere));

    // T-0710: the Evidence hub — eight tiles whose counts are their mounts'
    // entries, a topic that searches, and a way back. The eighth is T-1160's
    // population profile, whose "entries" are the axes it is profiled on.
    await page.evaluate(() => { window.__chicago4d.hud.setPanel(true); });
    await clickChrome('.panel-tab[data-tab="evidence"]');
    const hub = await page.evaluate(async () => {
      const api = window.__chicago4d;
      const hubEl = document.getElementById('evidence-hub');
      const tiles = () => [...hubEl.querySelectorAll('.ev-tile')];
      for (let i = 0; i < 50 && tiles().some((t) => /…/.test(t.querySelector('.ev-count')?.textContent ?? '')); i++) {
        await new Promise((r) => setTimeout(r, 100));
      }
      const mountCount = (id) => (id === 'grades'
        ? document.querySelectorAll('.ev-topic[data-topic="grades"] .legend-list > li').length
        : document.querySelectorAll(`#${id} > details`).length);
      const out = {
        hubShown: hubEl.checkVisibility(), title: document.getElementById('panel-title').textContent.trim(),
        tiles: tiles().map((t) => ({ id: t.dataset.topic, count: Number(t.querySelector('.ev-count')?.textContent),
          mount: mountCount(t.dataset.topic), title: t.querySelector('.ev-tile-title')?.textContent.trim(),
          h3: document.querySelector(`.ev-topic[data-topic="${t.dataset.topic}"] .ev-topic-title`)?.textContent.trim() })),
      };
      api.evidenceHub.showTopic('liberties');
      const total = document.querySelectorAll('#liberties details.lib').length;
      const search = document.querySelector('.ev-topic[data-topic="liberties"] .ev-search');
      search.value = 'roof';
      search.dispatchEvent(new Event('input', { bubbles: true }));
      const shown = document.querySelectorAll('#liberties details.lib:not([hidden])').length;
      const status = document.querySelector('.ev-topic[data-topic="liberties"] .ev-status')?.textContent.trim() ?? '';
      const m = /^(\d+) of (\d+) shown$/.exec(status);
      out.topic = { total, shown, status, statusN: m ? Number(m[1]) : null, statusM: m ? Number(m[2]) : null,
        title: document.getElementById('panel-title').textContent.trim(),
        backShown: !document.getElementById('panel-back').hasAttribute('hidden'),
        hubHidden: !hubEl.checkVisibility(), topic: api.evidenceHub.topic,
        libShown: document.getElementById('liberties').checkVisibility() };
      search.value = '';
      search.dispatchEvent(new Event('input', { bubbles: true }));
      out.cleared = document.querySelectorAll('#liberties details.lib:not([hidden])').length;
      document.getElementById('panel-back').click();
      out.back = { hubShown: hubEl.checkVisibility(), title: document.getElementById('panel-title').textContent.trim(),
        topic: api.evidenceHub.topic, backHidden: document.getElementById('panel-back').hasAttribute('hidden') };
      return out;
    });
    check(`${label}: the Evidence hub shows eight topics, each counting its own entries`,
      hub.hubShown && hub.title === 'Evidence' && hub.tiles.length === 8
      && hub.tiles.every((t) => Number.isFinite(t.count) && t.count > 0 && t.count === t.mount && t.title && t.title === t.h3),
      JSON.stringify(hub.tiles.map((t) => `${t.id} ${t.count}/${t.mount}`)));
    check(`${label}: a topic opens with the hub gone, and its search narrows the list and says so`,
      hub.topic.hubHidden && hub.topic.libShown && hub.topic.topic === 'liberties'
      && hub.topic.title === 'What we made up' && hub.topic.backShown
      && hub.topic.total > 17 && hub.topic.shown > 0 && hub.topic.shown < hub.topic.total
      && hub.topic.statusN === hub.topic.shown && hub.topic.statusM === hub.topic.total
      && hub.cleared === hub.topic.total,
      JSON.stringify(hub.topic));
    check(`${label}: Back returns to the hub`,
      hub.back.hubShown && hub.back.title === 'Evidence' && hub.back.topic === null && hub.back.backHidden,
      JSON.stringify(hub.back));
    // The chrome as the next block expects it: drawer closed.
    await clickChrome('#panel-close');

    await clickChrome('#btn-help');
    await clickChrome('.panel-tab[data-tab="settings"]');
    const toggles = await page.evaluate(() => {
      const compass = document.getElementById('s-compass');
      const map = document.getElementById('s-overview-map');
      const street = document.getElementById('s-street-names');
      compass.click(); map.click(); street.click();
      const hidden = {
        compass: document.getElementById('compass').hasAttribute('hidden'),
        map: document.getElementById('overview-map').hasAttribute('hidden'),
        street: document.getElementById('street-readout').hasAttribute('hidden'),
      };
      compass.click(); map.click(); street.click();
      return {
        hidden,
        restored: !document.getElementById('compass').hasAttribute('hidden')
          && !document.getElementById('overview-map').hasAttribute('hidden')
          && !document.getElementById('street-readout').hasAttribute('hidden'),
      };
    });
    check(`${label}: settings toggle all three navigation aids`,
      toggles.hidden.compass && toggles.hidden.map && toggles.hidden.street && toggles.restored,
      JSON.stringify(toggles));
    await clickChrome('#panel-close');

    // The HUD toggle must drive the same view the harness does.
    await clickChrome('#btn-confidence');
    await page.waitForTimeout(100);
    const viaHud = await page.evaluate(() => window.__chicago4d.confidenceView);
    check(`${label}: the HUD toggle drives the confidence view`, viaHud === true, `${viaHud}`);
    await clickChrome('#btn-confidence');

    // --- what's new ---------------------------------------------------------
    // The changelog is authored inside the app and mirrored out by publish.sh.
    // That import is the part worth guarding: it resolves differently in the
    // dev tree than in the published build if anyone reintroduces a fetch, and
    // this is the assertion that would catch it before it 404s live.
    await page.evaluate(() => window.localStorage.removeItem('chicago4d.whatsnew.seen'));
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 30000 });
    await clickChrome('#gate-btn');
    await page.waitForTimeout(150);
    await page.evaluate(() => document.exitPointerLock?.());

    const unread = await page.evaluate(() => ({
      chip: !document.getElementById('help-dot')?.hasAttribute('hidden'),
      tab: !document.getElementById('whatsnew-dot')?.hasAttribute('hidden'),
    }));
    check(`${label}: a first-time visitor is told there are unread notes`,
      unread.chip && unread.tab, `chip ${unread.chip}, tab ${unread.tab}`);

    await clickChrome('#btn-help');
    await clickChrome('.panel-tab[data-tab="whatsnew"]');
    await page.waitForTimeout(120);
    const wn = await page.evaluate(() => {
      const host = document.getElementById('whatsnew');
      return {
        entries: host.querySelectorAll('.wn-entry').length,
        items: host.querySelectorAll('.wn-items li').length,
        newest: host.querySelector('.wn-title')?.textContent || '',
        dated: /CT$/.test(host.querySelector('.wn-meta')?.textContent || ''),
        cleared: document.getElementById('help-dot')?.hasAttribute('hidden'),
        seen: window.localStorage.getItem('chicago4d.whatsnew.seen'),
      };
    });
    check(`${label}: the what's-new tab renders every release`,
      wn.entries >= 5 && wn.items >= wn.entries,
      `${wn.entries} entries, ${wn.items} items`);
    check(`${label}: entries carry a title and a stamped date`,
      wn.newest.length > 4 && wn.dated, `"${wn.newest}", dated ${wn.dated}`);
    check(`${label}: opening the tab clears the unread marker`,
      wn.cleared && Number(wn.seen) > 0, `cleared ${wn.cleared}, seen ${wn.seen}`);
    check(`${label}: a first visit flags nothing (no "last time" to differ from)`,
      await page.evaluate(() => document.querySelectorAll('#whatsnew .wn-entry.is-new').length) === 0);

    // A RETURNING visitor is the case the marker exists for: pin `seen` one
    // release back and exactly the newer entries should carry it.
    await page.evaluate(() => window.localStorage.setItem('chicago4d.whatsnew.seen', '3'));
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 30000 });
    await clickChrome('#gate-btn');
    await page.waitForTimeout(150);
    await page.evaluate(() => document.exitPointerLock?.());
    await clickChrome('#btn-help');
    await clickChrome('.panel-tab[data-tab="whatsnew"]');
    await page.waitForTimeout(120);
    const ret = await page.evaluate(() => ({
      flagged: [...document.querySelectorAll('#whatsnew .wn-entry.is-new .wn-title')]
        .map((n) => n.textContent),
      total: document.querySelectorAll('#whatsnew .wn-entry').length,
    }));
    check(`${label}: a returning visitor sees only what shipped since last time`,
      ret.flagged.length === ret.total - 3 && ret.flagged.length > 0,
      `${ret.flagged.length} of ${ret.total} flagged: ${ret.flagged.join(' | ')}`);

    inStageWork = false;
    } // end PART 12 (T-0060 stage 4b-i, cut by T-0121, halved by T-0167; renumbered by T-0346, T-0173 and T-0170)
    // PART 13 — the Evidence panel through inspecting from the air: the
    // liberties, the people, the wildlife, what is not here, what the ground
    // claims, free-fly and the two inspect keys. The tail of T-0060's stage 4.
    //
    // T-0167 cut it off part 12 (part 8 then) because it was the thinnest margin on the
    // measured DESKTOP profile — 8 m 46 s against a ten-minute ceiling, with
    // 107 staged checks, more than any other part — and the desktop readings
    // move by minutes between runs on a software renderer, so a 74-second
    // margin is not one. The boundary is this one because the desktop profile
    // put 6 m 05 s of part 12's cost above it and 2 m 41 s below, and because
    // nothing declared above it is read below it: the scope-aware scan found
    // `eye`, `toggles` and `typed` reaching across and all three are prose or a
    // different local (`typedE.typed`).
    //
    // Its prologue is `enterTown()` alone: the liberties reading below already
    // carries its own guarded panel-open and clicks the Evidence tab itself, so
    // unlike part 12 this part needs no panel guard bolted on. It takes no pose
    // — free-fly is entered from wherever the visitor stands.
    if (stageOn(13)) {
    inStageWork = true;
    await enterTown();
    // --- the liberties, in the Evidence panel ------------------------------
    // The claim this project makes is that a visitor can tell which parts we
    // made up. The confidence view covers attributes; these are the decisions
    // that belong to no attribute, and they are only a disclosure if they are
    // reachable from the page rather than from the repository.
    const lib = await page.evaluate(() => {
      // The what's-new checks above leave the panel open on their tab, and a
      // toggle here would close it — open only if it is shut.
      if (document.getElementById('panel').hasAttribute('hidden')) {
        document.getElementById('btn-help').click();
      }
      const tab = [...document.querySelectorAll('.panel-tab')]
        .find((t) => t.dataset.tab === 'evidence');
      tab?.click();
      const mount = document.getElementById('liberties');
      return {
        counted: window.__chicago4d.liberties?.count ?? 0,
        error: window.__chicago4d.liberties?.error ?? 'no liberties on the handle',
        rendered: mount ? mount.querySelectorAll('details.lib').length : 0,
        busy: mount ? mount.hasAttribute('aria-busy') : true,
        text: mount ? mount.textContent : '',
        overflow: document.documentElement.scrollWidth <= window.innerWidth + 1,
      };
    });
    check(`${label}: the liberties list loads`, lib.counted >= 17 && !lib.busy,
      `${lib.counted} loaded (${lib.error})`);
    check(`${label}: every loaded liberty is rendered`, lib.rendered === lib.counted,
      `${lib.rendered} rendered of ${lib.counted}`);
    check(`${label}: the list names a scene-wide liberty`,
      /No people, anywhere/.test(lib.text) && /L1\b/.test(lib.text),
      lib.text.slice(0, 160));
    check(`${label}: the Evidence panel does not overflow`, lib.overflow);

    // --- the town's people, in the same panel (ROADMAP K52) ----------------
    // The residents layer is the one that had a reader already: a household
    // travels in its building's sidecar and the building card names it. That is
    // why nothing caught it — `compile_residents()` reaches a building through
    // `lives_at` or `works_at`, so a household with neither attested at the
    // scene date attaches to no building and appeared on NO card anywhere. The
    // first two assertions are that count, because a regression here would be
    // silent in exactly the way the original fault was.
    const residents = await page.evaluate(async () => {
      const mount = document.getElementById('residents');
      const rows = mount ? [...mount.querySelectorAll('details.res-hh')] : [];
      // The lazy read: a row's body arrives on first open, from the household
      // record rather than the manifest. An unopened row proves only that the
      // manifest loaded, so one is opened here and read back.
      const target = rows.find((r) => r.dataset.id === 'hh_beaubien_mark') || rows[0];
      const collapsed = rows.length ? rows.every((r) => !r.open) : false;
      // T-0021. Two more rows, because the graded claims that were being printed
      // as objects are not on the Beaubien record: `age_on_scene_date` and
      // `birth_year` are on the nine the sources date. A row that carries neither
      // cannot fail for them.
      // T-0524: the third of those claims was `name_basis`, on the 113
      // reconstructed people, and this row was `hh_inf_baker_south_01` — one of
      // them. T-0489 retired that population and every id like it, so the lookup
      // matched nothing and every read off it was the empty string. The row is
      // taken from the manifest's own first `hh_inf_` household instead of a
      // literal id, so the next ruling that renames them does not silently empty
      // this read again; what it now carries is an evidence-only household.
      const named = rows.find((r) => String(r.dataset.id ?? '').startsWith('hh_inf_'));
      const dated = rows.find((r) => r.dataset.id === 'hh_egan_william_b');
      // T-0378. A fourth row, for the same reason: `letter_list_only` is on the
      // people the post office's letter lists minted and on nobody else, so no row
      // above can fail for it. Since T-0379 that row lives inside the letter-list
      // group, and `<details>` inside a closed `<details>` still renders — the
      // group is opened here so the row is reached the way a visitor reaches it.
      const group = mount ? mount.querySelector('details.res-ll-group') : null;
      const groupClosedOnMount = group ? !group.open : null;
      if (group) group.open = true;
      const letter = rows.find((r) => r.dataset.id === 'hh_luce_william');
      const candidate = rows.find((r) => r.dataset.id === 'hh_garrett_a');
      const noFind = rows.find((r) => r.dataset.id === 'hh_hail_aifred');
      for (const el of [target, named, dated, letter, candidate, noFind]) {
        if (!el) continue;
        el.open = true;
        for (let i = 0; i < 100 && el.querySelector('.res-hh-body .legend-note'); i++) {
          await new Promise((r) => setTimeout(r, 50));
        }
      }
      const bodyOf = (el) => (el ? el.textContent.replace(/\s+/g, ' ') : '');
      return {
        namedText: bodyOf(named),
        datedText: bodyOf(dated),
        letterText: bodyOf(letter),
        candidateText: bodyOf(candidate),
        noFindText: bodyOf(noFind),
        households: window.__chicago4d.residents?.households ?? 0,
        persons: window.__chicago4d.residents?.persons ?? 0,
        offCard: window.__chicago4d.residents?.offCard ?? -1,
        notResident: window.__chicago4d.residents?.notResident ?? 0,
        // T-0524: this fell back to a fixed sentence, so the failure detail read
        // "(no residents on the handle)" even when the handle was there and the
        // count had simply moved — which is how six correct-shaped reds read as a
        // missing section for a day. The handle's own message, or nothing.
        error: window.__chicago4d.residents
          ? (window.__chicago4d.residents.error ?? '')
          : 'no residents on the handle',
        rendered: rows.length,
        orphanChips: mount ? mount.querySelectorAll('.res-orphan').length : 0,
        // T-0379: the two halves of the list, and the group that holds the second.
        evidenced: window.__chicago4d.residents?.evidenced ?? -1,
        letterList: window.__chicago4d.residents?.letterList ?? -1,
        letterListOffCard: window.__chicago4d.residents?.letterListOffCard ?? -1,
        researchReviewed: window.__chicago4d.residents?.researchReviewed ?? -1,
        researchCounts: window.__chicago4d.residents?.researchCounts ?? {},
        groupRows: group ? group.querySelectorAll('details.res-hh').length : -1,
        groupText: group ? group.textContent.replace(/\s+/g, ' ').slice(0, 900) : '',
        // The group must be a DELIBERATE open. A section that renders 727 rows
        // expanded is the "wall of undifferentiated people" the ruling named as
        // the way to implement it badly, so this is read before anything opens it.
        groupClosedOnMount,
        busy: mount ? mount.hasAttribute('aria-busy') : true,
        collapsed,
        openedId: target?.dataset.id ?? '',
        openedText: target ? target.textContent.replace(/\s+/g, ' ') : '',
        openedPeople: target ? target.querySelectorAll('details.res-person').length : 0,
        openedCites: target ? target.querySelectorAll('.cites .cite-text').length : 0,
        text: mount ? mount.textContent.replace(/\s+/g, ' ') : '',
        prose: [document.getElementById('residents-note')?.textContent ?? '',
          ...[...document.querySelectorAll('[data-panel="evidence"] .legend-note')]
            .map((n) => n.textContent)].join(' ').replace(/\s+/g, ' '),
        overflow: document.documentElement.scrollWidth <= window.innerWidth + 1,
      };
    });
    // --- the agency on the PERSON'S card (T-1041) --------------------------
    // The relation has two ends and they are two different surfaces: the house's
    // end is on the building card in part 3, and the man's end is here, on his own
    // town card in the drawer. The agency LEFT Hubbard & Co. for E. K. Hubbard three
    // weeks before the scene date, so his card is the one where a visitor learns
    // what was true on the day — and it is rendered by the same module, which is
    // what stops the two ends describing one holding two ways.
    const personAgency = await page.evaluate(async () => {
      const mount = document.getElementById('residents');
      const row = mount ? mount.querySelector('details.res-hh[data-id="hh_hubbard_elijah_kent"]') : null;
      if (!row) return { found: false, text: '' };
      row.open = true;
      for (let i = 0; i < 100 && row.querySelector('.res-hh-body .legend-note'); i++) {
        await new Promise((r) => setTimeout(r, 50));
      }
      const sec = row.querySelector('.pop-agency');
      return {
        found: true,
        present: !!sec,
        text: sec ? sec.textContent.replace(/\s+/g, ' ').trim() : '',
      };
    });
    check(`${label}: a man who held an agency says so on his own card`,
      personAgency.found && personAgency.present
      && /E\. K\. Hubbard held the agency for Howard Fire Insurance Company/.test(personAgency.text)
      && /printed from 20 June 1835 to 5 August 1835/.test(personAgency.text),
      personAgency.found ? personAgency.text.slice(0, 260) : 'no hh_hubbard_elijah_kent row');
    // …and the caveat travels with it, because it is the file's sentence and not
    // the building card's.
    check(`${label}: the person's card carries the same caveat as the house's`,
      /A holding is a relation and nothing more/.test(personAgency.text)
      && /the notice was running on the day you are standing in/.test(personAgency.text),
      personAgency.text.slice(-260));

    // T-0524, and the shape every figure below now takes. These assertions carried
    // the layer's SIZE as a literal — 920 households, 956 people, 193 evidenced,
    // 764 off-card, 150 reviews — and a test that hardcodes a count rots the next
    // time the count is right: T-0489 moved all five on 2 September 2026 and six
    // assertions went red for being correct about a town that had changed. So the
    // expectation is READ, independently, out of the two committed files the page
    // itself fetched, exactly as T-0491 repaired the gate-census assertion (#682).
    //
    // The independence matters, or this is a tautology. Nothing here reads the
    // handle: `residents/index.json` and `residents/research_pilot.json` are
    // fetched again and the figures recomputed off the raw rows, so what is
    // asserted is that the SECTION agrees with the DATA. And each check carries a
    // floor besides, because a manifest that lost its households would otherwise
    // satisfy "the card shows all of them" with nothing on the card at all.
    const expected = await page.evaluate(async () => {
      const api = window.__chicago4d;
      const index = await (await fetch(new URL('residents/index.json', api.dataBase))).json();
      const pilot = await (await fetch(new URL('residents/research_pilot.json', api.dataBase))).json();
      const rows = Array.isArray(index.households) ? index.households : [];
      const off = rows.filter((e) => !e.lives_at && !e.works_at);
      const reviews = Array.isArray(pilot.reviews) ? pilot.reviews : [];
      return {
        households: rows.length,
        statedHouseholds: index.counts?.households,
        persons: index.counts?.persons,
        summedPersons: rows.reduce((n, e) => n + (e.persons || 0), 0),
        reconstructed: index.counts?.by_grade?.reconstructed,
        letterList: rows.filter((e) => e.letter_list_only).length,
        evidenced: rows.filter((e) => !e.letter_list_only).length,
        offCard: off.length,
        letterListOffCard: off.filter((e) => e.letter_list_only).length,
        researchReviewed: new Set(reviews.map((r) => r.person_id)).size,
        researchCounts: pilot.counts || {},
      };
    });
    check(`${label}: every household in the layer is on the card`,
      expected.households > 500 && expected.statedHouseholds === expected.households
      && residents.households === expected.households
      && residents.rendered === expected.households && !residents.busy,
      `${residents.households} loaded / ${residents.rendered} rendered of `
      + `${expected.households} in the manifest`
      + (residents.error ? ` (${residents.error})` : ''));
    check(`${label}: every person entry in the manifest is counted`,
      expected.persons > 500 && expected.persons === expected.summedPersons
      && residents.persons === expected.persons,
      `${residents.persons} on the handle, ${expected.persons} stated, `
      + `${expected.summedPersons} summed off the rows`);
    // T-0379, and the assertion the ruling itself asked for. Most of the layer is
    // a name on a post-office list and nothing else, and the ruling's own test of
    // a good implementation is that a visitor can tell which ones at a glance. So:
    // the cohort is ONE group holding every letter-list row and no other, the two
    // halves account for the whole layer, and the group is CLOSED when the section
    // mounts. A regression here does not break the page; it drowns it, which is
    // why it is a number and not an eyeball.
    // T-0524 took the literals out. It read `evidenced === 193`, whose comment
    // argued "the list did not become three-quarters noise" — after T-0489 removed
    // 108 reconstructed households the evidenced side is a far smaller share than
    // that, and the sentence was arguing for a town that no longer exists. What is
    // worth pinning is the PARTITION, which is true at any size.
    check(`${label}: the letter-list cohort is held apart from the evidenced town`,
      expected.letterList > 100 && expected.evidenced > 20
      && residents.evidenced === expected.evidenced
      && residents.letterList === expected.letterList
      && residents.evidenced + residents.letterList === expected.households
      && residents.groupRows === expected.letterList
      && residents.groupClosedOnMount === true,
      `${residents.evidenced} evidenced / ${residents.letterList} letter-list of `
      + `${expected.households}, ${residents.groupRows} in the group, closed on mount: `
      + `${residents.groupClosedOnMount}`);
    check(`${label}: the group says what that evidence is worth before it is opened`,
      /post office/.test(residents.groupText)
      && /does not.{0,40}establish/is.test(residents.groupText)
      && /weakest evidence/.test(residents.groupText),
      residents.groupText.slice(0, 240));
    // The finding itself, asserted as a number so it cannot quietly grow back:
    // the households that reach no building sidecar are each marked on their own
    // row. 17 of the 52 are the original fault — records whose residence and
    // workplace are both unattested. The other 35 reach no building BY
    // CONSTRUCTION, and they are three passes of the same kind: T-0376's 16
    // minted tradespeople, whose trade the papers print and whose address they
    // do not; 15 letter-list names, where a list of uncalled-for letters gives a
    // name and no address at all; and T-0373's 4 residency-tested people, whom
    // the papers name with no trade either. In every case the chip is the card
    // telling the truth rather than a regression.
    // T-0379 SPLIT THIS NUMBER IN TWO, and the split is the honest form of it. Of
    // the households that reach no building card, the letter-list cohort reaches
    // none BY DEFINITION — a list of uncalled-for letters gives a name and no
    // address, so a chip announcing it on every one of those rows is wallpaper,
    // and the group's own summary says it once instead. The chip stays where it is
    // a finding: the households the rest of the corpus documents and this project
    // still could not attach to a building.
    // T-0524 took the three literals (764 / 37 / 727) out for the reason above:
    // T-0489 moved the first two to 770 and 43 and the assertion went red for
    // being right about the wrong town. All three are derivable from the manifest
    // rows — off-card is "neither lives_at nor works_at", which is the same
    // predicate `js/residents.js` applies — and the CHIP COUNT is the one that
    // carries the finding, so it is asserted as the arithmetic difference rather
    // than as a number somebody typed. A chip appearing on a letter-list row, or
    // going missing from a documented one, still fails here.
    check(`${label}: the households no building card can reach are marked`,
      expected.offCard > 0 && expected.offCard > expected.letterListOffCard
      && residents.offCard === expected.offCard
      && residents.letterListOffCard === expected.letterListOffCard
      && residents.orphanChips === expected.offCard - expected.letterListOffCard,
      `${residents.offCard} off-card / ${residents.orphanChips} chip(s) / `
      + `${residents.letterListOffCard} of them letter-list — the manifest says `
      + `${expected.offCard} / ${expected.offCard - expected.letterListOffCard} / `
      + `${expected.letterListOffCard}`);
    check(`${label}: the researched non-residents are published too`,
      residents.notResident === 10, `${residents.notResident}`);
    // The lazy read, proved by opening the household that IS the finding: Mark
    // Beaubien has neither residence nor workplace attested on 1 July 1835, so
    // this record reached no visitor at all before this section.
    check(`${label}: opening a household fetches its record`,
      residents.openedId === 'hh_beaubien_mark' && residents.openedPeople === 2
      && /the original proprietor|Sauganash/.test(residents.openedText),
      `${residents.openedId}: ${residents.openedPeople} person row(s)`);
    // The reasoning is the finding on this layer, and the arrival year is the
    // sharpest case of it: a figure carried explicitly so a reader can see it is
    // NOT evidence. A card printing the value without the note would invert it.
    check(`${label}: a graded claim carries its reasoning, not just its value`,
      /general circulation/.test(residents.openedText)
      && /not evidence/.test(residents.openedText),
      residents.openedText.slice(0, 200));
    check(`${label}: the household records quote their sources, not their source ids`,
      residents.openedCites >= 1 && !/andreas_1884_v1/.test(residents.text),
      `${residents.openedCites} citation(s) rendered`);
    check(`${label}: the households start collapsed, like every other disclosure here`,
      residents.collapsed);
    check(`${label}: the people section does not overflow the panel`, residents.overflow);
    // T-0021, and the reason this check is a string match on four words. A
    // person's `name_basis`, `age_on_scene_date` and `birth_year` are graded
    // claim blocks, and this card handed all three whole to a text renderer:
    // 113 rows read "How this person is named — [object Object]" and nine said
    // it twice more. Every assertion above passed throughout, because a card
    // that renders the WRONG STRING renders a string. The layer-read census
    // (tools/measure_layer_reads.py) is what found it; this is what would have.
    check(`${label}: no figure reaches a person's row as [object Object]`,
      !/\[object Object\]/.test(residents.text),
      residents.text.slice(Math.max(0, residents.text.indexOf('[object Object]') - 80), 200));
    // And the row the fault was hiding. It matched the VALUE and not the note:
    // the note under "What the sources say" carried "THE NAME IS INVENTED" on
    // these records too and reached the card throughout, so an assertion on that
    // sentence passed on the broken build — checked, and it did. What was lost
    // was which pool the name was drawn from, and that was only in `name_basis`.
    //
    // T-0524: there is no invented name on this layer any more. T-0489 retired the
    // reconstructed population and the `hh_inf_` households that survived it carry
    // a head the papers name, with the `name_basis` block explicitly struck ("an
    // invented name is not kept beside a documented one"). So the assertion has no
    // subject, and deleting it would delete the wire this fault came down: the
    // [object Object] check above is a NEGATIVE, and it passes on a card that
    // renders nothing at all, which is exactly the state that check was written
    // against. The positive it needs is kept, on what that row now carries — the
    // reasoning that says the roof is not the man's evidence — and the retirement
    // is asserted alongside it, so a `name_basis` block reappearing on this layer
    // without a ruling fails here rather than passing quietly.
    check(`${label}: an evidence-only household's row says what its roof is not`,
      /What the sources say/.test(residents.namedText)
      && /THIS ROOF DID NOT COME FROM HIS RECORD/.test(residents.namedText)
      && !/How this person is named/.test(residents.namedText),
      residents.namedText.slice(0, 200));
    // The nine the sources actually date, with the reasoning that says which of
    // the two figures the source states and which is arithmetic off it.
    check(`${label}: a dated person carries an age and a birth year, both graded`,
      /Age on 1 July 1835/.test(residents.datedText)
      && /\bBorn\b/.test(residents.datedText)
      && /28 September 1808/.test(residents.datedText),
      residents.datedText.slice(0, 200));
    // T-0378, and the whole point of that ticket: the register reads two kinds of
    // person out of the papers and they are NOT the same claim. A man who
    // advertised his stock is named, dated, placed and given a trade; a name in
    // the post office's list of uncalled-for letters is a name. `letter_list_only`
    // reached `gazetteer.json` and `register_1835.json` and stopped there, so on
    // the card the two read identically — which is exactly what the owner's ruling
    // of 2026-08-28 says must never happen. Asserted in BOTH places it is said:
    // the person's own row, and the section's count sentence, because a visitor
    // who never opens a household still reads the second one.
    check(`${label}: a letter-list name says on its own row how thin that evidence is`,
      /How this person is known/.test(residents.letterText)
      && /uncalled-for letters/.test(residents.letterText)
      && /weakest evidence/.test(residents.letterText),
      residents.letterText.slice(0, 200));
    check(`${label}: the count sentence says how many people are known only that way`,
      // T-0524's rule, applied here at last: this one still carried 727 as a typed
      // literal and went red the day T-0723 folded the duplicate Norton card and the
      // cohort became 726 — right about a town that had changed, which is exactly the
      // rot that ticket named. The figure is read out of `residents/index.json` beside
      // every other count in this section, so what is asserted is that the SENTENCE
      // agrees with the DATA rather than with a number somebody typed. The floor keeps
      // it from passing on an empty cohort.
      expected.letterList > 0
      && new RegExp(`${expected.letterList} of the people here are known ONLY from the post office`)
        .test(residents.prose)
      && /per cent of this town/.test(residents.prose),
      residents.prose.slice(0, 240));
    // And the other half of the same ruling: none of the ten may carry a trade
    // the papers do not give them. The occupation on a letter-list person reads
    // that none is recorded, and a plausible-sounding job appearing there would
    // be an invention this section exists to make impossible.
    check(`${label}: a letter-list name carries no invented trade`,
      /none recorded/i.test(residents.letterText)
      && /No source records an occupation/.test(residents.letterText),
      residents.letterText.slice(0, 200));
    // T-0442/T-0462: a candidate biography is useful only if it remains visibly a
    // candidate. The same public payload also carries negative work so silence
    // cannot be mistaken for a person who was never researched.
    // T-0524 took the four literals (150 / 31 / 30 / 89) out. The review layer has
    // grown to 375 since, and a count that is right is not a regression. The
    // expectation is read out of `residents/research_pilot.json` — the file the
    // page fetched — and the three named buckets are cross-footed against the
    // review list itself, which is the half a hardcoded number never gave: a
    // `counts` block that stops agreeing with its own `reviews` array now fails,
    // and so does a card layer that shows fewer reviews than the file holds.
    check(`${label}: every resident research review reaches a resident card`,
      expected.researchReviewed > 100
      && Object.values(expected.researchCounts).reduce((n, v) => n + v, 0)
        === expected.researchReviewed
      && residents.researchReviewed === expected.researchReviewed
      && residents.researchCounts.corroborated_enrichment
        === expected.researchCounts.corroborated_enrichment
      && residents.researchCounts.candidate_identity
        === expected.researchCounts.candidate_identity
      && residents.researchCounts.no_corroboration
        === expected.researchCounts.no_corroboration,
      `${residents.researchReviewed}: ${JSON.stringify(residents.researchCounts)} — `
      + `the file holds ${expected.researchReviewed}: `
      + `${JSON.stringify(expected.researchCounts)}`);
    check(`${label}: candidate identities are visibly unmerged`,
      /Augustus Garrett/.test(residents.candidateText)
      && /candidate identity.{0,20}not merged/i.test(residents.candidateText)
      && /not an asserted identity/i.test(residents.candidateText),
      residents.candidateText.slice(0, 260));
    check(`${label}: a negative search is published without denying existence`,
      /no safe match found/i.test(residents.noFindText)
      && /not evidence that the person did not exist/i.test(residents.noFindText),
      residents.noFindText.slice(0, 260));
    // The one thing this section must never imply, and the constraint that
    // outranks every other consideration in this project: v1 draws no human
    // figures, and the removal of August 1835 is not staged anywhere.
    check(`${label}: the section says plainly that nobody is drawn`,
      /Nobody is drawn/.test(residents.prose)
      && /this is the research, not a population/i.test(residents.prose),
      residents.prose.slice(0, 200));

    // --- the wildlife, in the same panel (ROADMAP K51) ---------------------
    // `data/fauna/` was researched to the scene date, graded and cited, and read
    // by nothing: no renderer source opened the directory and publish.sh did not
    // copy it, so 139 animal records stopped at the repository while three
    // documents implied a reader existed. These assertions are what stops that
    // recurring — a section that 404s its layer on the published tree and works
    // in the source tree is exactly the failure the flora manifest once shipped.
    const fauna = await page.evaluate(() => {
      const mount = document.getElementById('fauna');
      const one = mount?.querySelector('details.fauna-sp');
      return {
        zones: window.__chicago4d.fauna?.zones ?? 0,
        species: window.__chicago4d.fauna?.species ?? 0,
        error: window.__chicago4d.fauna?.error ?? 'no fauna on the handle',
        renderedZones: mount ? mount.querySelectorAll('details.fauna-zone').length : 0,
        renderedSpecies: mount ? mount.querySelectorAll('details.fauna-sp').length : 0,
        busy: mount ? mount.hasAttribute('aria-busy') : true,
        text: mount ? mount.textContent : '',
        // The citation join is a separate fetch from a separate directory, and
        // a card quoting a bare `source_id` is the failure it exists to stop.
        cites: mount ? mount.querySelectorAll('.cites .cite-text').length : 0,
        collapsed: one ? !one.open : false,
        // The section's own prose plus the derived count sentence: the two
        // places this panel could make a claim about the town rather than about
        // the research.
        prose: [document.getElementById('fauna-note')?.textContent ?? '',
          ...[...document.querySelectorAll('[data-panel="evidence"] .legend-note')]
            .map((n) => n.textContent)].join(' ').replace(/\s+/g, ' '),
        overflow: document.documentElement.scrollWidth <= window.innerWidth + 1,
      };
    });
    check(`${label}: the wildlife list loads every habitat`,
      fauna.zones === 10 && fauna.renderedZones === 10 && !fauna.busy,
      `${fauna.zones} loaded / ${fauna.renderedZones} rendered (${fauna.error})`);
    check(`${label}: every animal record in the layer is on the card`,
      fauna.species === 139 && fauna.renderedSpecies === 139,
      `${fauna.renderedSpecies} rendered of ${fauna.species}`);
    // Discriminating rather than a count: the pigs are the signature street
    // animal of this scene and the muskrat is the one the public-square pond
    // quotation was re-graded around, so both are records whose absence would
    // mean the zone files were not the thing being read.
    check(`${label}: the card names what the records name`,
      /pigs at large/.test(fauna.text) && /muskrat/.test(fauna.text)
      && /Sus scrofa domesticus/.test(fauna.text),
      fauna.text.slice(0, 160));
    // The July gate is the hard part of this dataset and the reason it may not
    // be read as a year list: several animals are here as sign or sound only.
    check(`${label}: the card carries the July presence modes, not a species list`,
      /trace only/.test(fauna.text) && /flightless moult/.test(fauna.text),
      fauna.text.slice(0, 160));
    check(`${label}: the animal records quote their sources, not their source ids`,
      fauna.cites >= 20 && !/chicagology_prefire/.test(fauna.text),
      `${fauna.cites} citation(s) rendered`);
    check(`${label}: the animals start collapsed, like every other disclosure here`,
      fauna.collapsed);
    check(`${label}: the wildlife section does not overflow the panel`, fauna.overflow);
    // The one thing this section must never imply. Nothing is drawn from the
    // layer — no animal geometry exists — so the panel says so in words, and the
    // day that stops being true this assertion is the one that should fail.
    check(`${label}: the section says plainly that none of them is in the scene`,
      /None of them is drawn in the scene/.test(fauna.prose)
      && /this is the research, not a population/i.test(fauna.prose),
      fauna.prose.slice(0, 200));

    // --- what grows here, in the same panel (T-0281) ------------------------
    // The third layer this project found researched, graded, cited and reaching
    // no reader — after the animals (K51) and the households (K52) — and the one
    // that carries a finding of its own. `data/flora/` is planted by flora.js and
    // was on no card, so a visitor could see the sward and not judge it; and nine
    // of the ten communities ask for more small plants than the sward lattice can
    // hold, a fact declared in tools/forb_clamp_baseline.json and docs/STATUS.md
    // and, until this section, nowhere a visitor reads.
    const plants = await page.evaluate(async () => {
      // T-0710 RESTATED: the plants are a hub topic; `fits` below measures the
      // mount's own box, which reads 0 <= 0 (a dishonest pass) while the topic is
      // `display:none`. Shown first, so the measurement is of a laid-out mount.
      window.__chicago4d.evidenceHub.showTopic('plants');
      const mount = document.getElementById('plants');
      // Open one community and one species inside it: the figures, the reasoning
      // and the citation join are all in the collapsed half, which is exactly the
      // half a check on the closed card cannot see.
      const zone = mount?.querySelector('details.plant-zone');
      if (zone) zone.open = true;
      const sp = zone?.querySelector('details.plant-sp');
      if (sp) sp.open = true;
      // The dense forest is the sharpest case and the one the note names, so it
      // is read by id rather than by position.
      const dense = [...(mount?.querySelectorAll('details.plant-zone') ?? [])]
        .find((d) => /z06_dense_forest/.test(d.textContent));
      if (dense) dense.open = true;
      await new Promise((r) => setTimeout(r, 50));
      return {
        zones: window.__chicago4d.plants?.zones ?? 0,
        species: window.__chicago4d.plants?.species ?? 0,
        clamped: window.__chicago4d.plants?.clamped ?? 0,
        clampedZones: window.__chicago4d.plants?.clampedZones ?? 0,
        ceiling: window.__chicago4d.plants?.ceilingPerM2 ?? 0,
        error: window.__chicago4d.plants?.error ?? 'no plants on the handle',
        renderedZones: mount ? mount.querySelectorAll('details.plant-zone').length : 0,
        renderedSpecies: mount ? mount.querySelectorAll('details.plant-sp').length : 0,
        clampChips: mount ? mount.querySelectorAll('.plant-clamped').length : 0,
        clampLists: mount ? mount.querySelectorAll('.plant-clamp').length : 0,
        busy: mount ? mount.hasAttribute('aria-busy') : true,
        cites: mount ? mount.querySelectorAll('.cites .cite-text').length : 0,
        text: mount ? mount.textContent : '',
        denseText: (dense?.textContent ?? '').replace(/\s+/g, ' '),
        note: document.getElementById('plants-note')?.textContent ?? '',
        collapsed: zone ? [...mount.querySelectorAll('details.plant-zone')]
          .filter((d) => d !== zone && d !== dense).every((d) => !d.open) : false,
        // The section's own box, measured the way T-0281 found it broken: the
        // mount widened past the panel and every line of reasoning was clipped
        // at the right edge, on a grid track that resolves toward max-content.
        // …and it is a LAID-OUT mount being measured (clientWidth 0 is a hidden one).
        fits: mount ? mount.clientWidth > 0 && mount.scrollWidth <= mount.clientWidth : false,
        overflow: document.documentElement.scrollWidth <= window.innerWidth + 1,
      };
    });
    check(`${label}: the plant list loads every community`,
      plants.zones === 10 && plants.renderedZones === 10 && !plants.busy,
      `${plants.zones} loaded / ${plants.renderedZones} rendered (${plants.error})`);
    check(`${label}: every species in the ten communities is on the card`,
      plants.species === 155 && plants.renderedSpecies === 155,
      `${plants.species} counted / ${plants.renderedSpecies} rendered`);
    // The finding, asserted as numbers so it cannot quietly go away: ten
    // (community, stratum, side) layers are over the lattice's ceiling, across
    // eight communities, and each of those communities says so on its own card.
    check(`${label}: the communities the sward lattice cannot draw say so`,
      plants.clamped === 10 && plants.clampedZones === 8
      && plants.clampChips === 8 && plants.clampLists === 8,
      `${plants.clamped} clamped layer(s) in ${plants.clampedZones} community(ies), `
      + `${plants.clampChips} chip(s) / ${plants.clampLists} list(s)`);
    // And the number itself, read off the declaration rather than typed into the
    // renderer. If `tools/forb_clamp_baseline.json` moves and the sidecar does
    // not, `compile_scene.py --check` fails first; this is the other end of that
    // rope — the figure a visitor reads is the figure the gate holds.
    check(`${label}: the share a visitor is standing in comes off the declaration`,
      Math.abs(plants.ceiling - 0.34602076124567477) < 1e-9
      && /0\.5 %/.test(plants.denseText)
      && /66\.4 plants per m²/.test(plants.denseText)
      && /0\.346/.test(plants.denseText),
      `ceiling ${plants.ceiling} · dense forest says `
      + `"${plants.denseText.slice(Math.max(0, plants.denseText.indexOf('records ask')), 
        Math.max(240, plants.denseText.indexOf('records ask') + 240))}"`);
    check(`${label}: the note names the worst case rather than only the total`,
      /155 plants across 10 communities/.test(plants.note)
      && /dense forest/.test(plants.note) && /0\.5 %/.test(plants.note),
      plants.note.slice(0, 220));
    check(`${label}: the plant records quote their sources, not their source ids`,
      plants.cites >= 1 && !/chicagology_prefire273/.test(plants.text),
      `${plants.cites} citation(s) rendered`);
    // T-0021's fault, and this section shipped it on its first render: `july
    // .inflorescence` is a record and not a word, and handing it to a text
    // renderer put "[object Object]" on ninety-seven species. Every assertion
    // above passed while it did, because a card that renders the WRONG STRING
    // renders a string. Two more fields of the same shape sit beside it.
    check(`${label}: no figure reaches a plant's row as [object Object]`,
      !/\[object Object\]/.test(plants.text),
      plants.text.slice(Math.max(0, plants.text.indexOf('[object Object]') - 80), 200));
    check(`${label}: the communities start collapsed, like every other disclosure here`,
      plants.collapsed);
    // The layout fault this section found, and it was NOT only this section's:
    // `.liberties` and `.lib-body` are one-column grids on the default `auto`
    // track, which resolves toward max-content, so a card holding one long
    // unbreakable run widens the column and the panel clips its text instead of
    // wrapping it. Measured at 390 px: the mount reached 419 px against a 338 px
    // box. A check on `documentElement` alone cannot see it — the document did
    // not overflow while every line of reasoning was being cut off — so the
    // mount's own box is measured here.
    check(`${label}: the plants section wraps inside the panel rather than clipping`,
      plants.fits, `mount ${plants.fits ? 'fits' : 'is wider than its box'}`);
    check(`${label}: the plants section does not overflow the panel`, plants.overflow);
    // T-0302, the second acceptance clause: the same per-mount measure on ALL
    // SEVEN `.liberties` mounts, each shown first — six are hub topics on the
    // Evidence tab, the households mount is on the People tab since T-0708. A
    // document-width check cannot see this fault (the panel clips instead of
    // overflowing), and a hidden mount reads 0 <= 0, so every mount is asserted
    // to be laid out when it is measured.
    const mountFit = await page.evaluate(async () => {
      const api = window.__chicago4d;
      const measure = (id) => {
        const m = document.getElementById(id);
        return { id, client: m?.clientWidth ?? 0, scroll: m?.scrollWidth ?? 0,
          panel: m?.closest('.panel-body')?.clientWidth ?? 0 };
      };
      const out = [];
      api.hud.setPanel(true);
      api.hud.selectTab('evidence');
      for (const id of ['liberties', 'ground', 'fauna', 'plants', 'exclusions', 'uncertain', 'population']) {
        api.evidenceHub.showTopic(id);
        await new Promise((r) => setTimeout(r, 30));
        out.push(measure(id));
      }
      api.hud.selectTab('people');
      api.people?.close?.();
      await new Promise((r) => setTimeout(r, 30));
      out.push(measure('residents'));
      // Back to where this part's later reads expect the panel: Evidence, hub.
      api.hud.selectTab('evidence');
      api.evidenceHub.showHub();
      return out;
    });
    const unfit = mountFit.filter((m) => !(m.client > 0 && m.scroll <= m.client && m.client <= m.panel));
    check(`${label}: all eight evidence mounts wrap inside their panel rather than clipping`,
      mountFit.length === 8 && unfit.length === 0,
      unfit.length ? unfit.map((m) => `${m.id} ${m.scroll}/${m.client} in ${m.panel}`).join('; ')
        : mountFit.map((m) => `${m.id} ${m.scroll}/${m.client}`).join(', '));

    // T-0302's actual claim, and the reason the measure above was not enough:
    // *"it is invisible today only because their longest line happens to fit;
    // the first long `<dd>` any of them gains clips silently."* A check on the
    // content as it stands cannot see a latent clipper, so this one puts the
    // long line there. Each mount is CLONED, laid out as the next sibling of the
    // original — same parent, same column width, so the measurement is of this
    // section's real layout — every `<details>` in the copy is opened, a
    // 90-character unbreakable run replaces the text of every leaf, and the copy
    // is measured and removed. The original is never touched, which is what lets
    // this sit in the middle of a part whose later assertions read the same
    // sections' text.
    // Measured on this branch, 2026-09-13 at 390x780: before the rules in
    // css/evidence.css all seven clipped — liberties 1196/362, ground 1261,
    // fauna 1196, plants 749, exclusions 685, uncertain 685, residents 689 —
    // carried by ordinary furniture the old `dt`/`dd`-only rule did not name: a
    // citation `<li>`, the scope pill, a `<b>` in a household's prose. After,
    // every one of them is 362/362.
    const mountStress = await page.evaluate(async () => {
      const api = window.__chicago4d;
      const TOKEN = 'x'.repeat(90);
      const stress = (id) => {
        const mount = document.getElementById(id);
        if (!mount) return { id, client: 0, scroll: 1, leaves: 0 };
        const probe = mount.cloneNode(true);
        probe.id = `${id}-t0302-probe`;
        mount.after(probe);
        probe.querySelectorAll('details').forEach((d) => { d.open = true; });
        let leaves = 0;
        for (const el of probe.querySelectorAll('*')) {
          if (el.children.length || !el.textContent.trim()) continue;
          el.textContent = TOKEN;
          leaves += 1;
        }
        const out = { id, client: probe.clientWidth, scroll: probe.scrollWidth, leaves };
        probe.remove();
        return out;
      };
      const rows = [];
      api.hud.setPanel(true);
      api.hud.selectTab('evidence');
      for (const id of ['liberties', 'ground', 'fauna', 'plants', 'exclusions', 'uncertain', 'population']) {
        api.evidenceHub.showTopic(id);
        await new Promise((r) => setTimeout(r, 30));
        rows.push(stress(id));
      }
      api.hud.selectTab('people');
      api.people?.close?.();
      await new Promise((r) => setTimeout(r, 30));
      rows.push(stress('residents'));
      api.hud.selectTab('evidence');
      api.evidenceHub.showHub();
      return rows;
    });
    const clipped = mountStress.filter((m) => !(m.client > 0 && m.leaves > 0 && m.scroll <= m.client));
    check(`${label}: a run longer than the column breaks inside all eight mounts, not past them`,
      mountStress.length === 8 && clipped.length === 0,
      clipped.length ? clipped.map((m) => `${m.id} ${m.scroll}/${m.client} on ${m.leaves} leaves`).join('; ')
        : mountStress.map((m) => `${m.id} ${m.scroll}/${m.client}`).join(', '));

    // The document's own account of what this list is. It is compiled out of
    // `docs/LIBERTIES.md` and was rendered nowhere, while the panel opened with a
    // hand-written paraphrase of it — a restatement with nothing holding it to
    // the half it restates. Verbatim, and against the fetched document rather
    // than a phrase copied in here, because the failure this pins is a sentence
    // in the repository disagreeing with the sentence on the screen.
    const libNote = await page.evaluate(() => {
      const el = document.getElementById('liberties-note');
      const panel = document.querySelector('[data-panel="evidence"]');
      const recorded = window.__chicago4d.liberties?.note ?? '';
      const text = (panel?.textContent ?? '').replace(/\s+/g, ' ');
      return {
        shown: el?.textContent ?? '',
        recorded,
        busy: el ? el.hasAttribute('aria-busy') : true,
        // Once, not twice: the paraphrase is gone rather than joined.
        occurrences: recorded
          ? text.split(recorded.replace(/\s+/g, ' ')).length - 1 : 0,
      };
    });
    check(`${label}: the liberties list says what it is, in the document's words`,
      libNote.shown === libNote.recorded && libNote.recorded.length > 80 && !libNote.busy,
      `shown "${libNote.shown.slice(0, 80)}" of ${libNote.recorded.length} recorded`);
    check(`${label}: the panel states it once — the hand-written paraphrase is gone`,
      libNote.occurrences === 1, `${libNote.occurrences} occurrence(s)`);

    // The admissions themselves, on the page. `Covers:` is what the commit gate
    // reads to decide whether every invented footprint has been owned up to, and
    // a guarantee enforced in the repository but invisible in the walkthrough is
    // the same filed confession this panel exists to stop being. Asserted
    // discriminatingly: the entry that admits to the Sauganash's two invented
    // outlines shows footprint chips, and the scene-wide "no people" entry —
    // which invents nothing that gets drawn — claims nothing.
    const claims = await page.evaluate(() => {
      const entry = (id) => [...document.querySelectorAll('#liberties details.lib')]
        .find((d) => d.querySelector('.lib-id')?.textContent.trim() === id);
      const read = (id) => [...(entry(id)?.querySelectorAll('.lib-covers') ?? [])]
        .map((n) => n.textContent.trim());
      const tokens = (id) => [...(entry(id)?.querySelectorAll('.lib-covers') ?? [])]
        .map((n) => n.getAttribute('title') ?? '');
      return {
        l5: read('L5'), l8: read('L8'), l1: read('L1'), l4: read('L4'),
        l18: read('L18'), l19: read('L19'),
        bank: read('L31a'), slough: read('L31c'), bankTokens: tokens('L31a'),
      };
    });
    check(`${label}: an entry shows the inventions it admits to`,
      claims.l5.length > 0 && claims.l5.every((t) => /footprint/.test(t))
      && claims.l5.some((t) => /Sauganash/i.test(t)),
      `L5 claims [${claims.l5.join(' | ')}]`);
    check(`${label}: a claim over several buildings names each of them`,
      claims.l8.length === 3 && new Set(claims.l8).size === 3,
      `L8 claims [${claims.l8.join(' | ')}]`);
    check(`${label}: an entry that invented nothing drawn claims nothing`,
      claims.l1.length === 0 && claims.l4.length === 0,
      `L1 [${claims.l1.join(' | ')}] L4 [${claims.l4.join(' | ')}]`);

    // The admissions are not only about drawn geometry. A roof chosen because it
    // was usual and a porch left off because nobody found one are inventions a
    // visitor cannot see being made, so they get chips of their own — and the
    // chip reads as an attribute, not as the `form.` token the gate matches on.
    check(`${label}: an invented roof and height are admitted like an outline`,
      claims.l18.length === 2 && claims.l18.every((t) => /Sauganash/i.test(t))
      && claims.l18.some((t) => /roof type/.test(t))
      && claims.l18.some((t) => /wall height/.test(t))
      && !claims.l18.some((t) => /form\./.test(t)),
      `L18 claims [${claims.l18.join(' | ')}]`);
    check(`${label}: a decision made by default is admitted in two buildings`,
      claims.l19.length === 2 && new Set(claims.l19).size === 2
      && claims.l19.every((t) => /gallery/.test(t)),
      `L19 claims [${claims.l19.join(' | ')}]`);

    // The ground admits to its inventions on the same terms, and the chip has to
    // say which half of the dataset it lands in: a 6 m bank face nobody recorded
    // is the piece of ground every visitor walks down to the water on, and until
    // the coverage gate could read the terrain spec it was owned up to only
    // because somebody noticed. Asserted discriminatingly — a building's
    // admission must NOT read as the ground's, which a chip that simply printed
    // the token's first segment would have failed.
    check(`${label}: the ground admits to what it invented, and says it is the ground`,
      claims.bank.length === 1 && /the ground/.test(claims.bank[0])
      && /bank/.test(claims.bank[0]) && !claims.l5.some((t) => /the ground/.test(t)),
      `L31a claims [${claims.bank.join(' | ')}]`);
    check(`${label}: the chip carries the epoch the admission is about`,
      claims.bankTokens.length === 1
      && /^admitted for terrain\.[a-z0-9_]+\.bank$/.test(claims.bankTokens[0]),
      `L31a tokens [${claims.bankTokens.join(' | ')}]`);
    // The one ground invention nobody had written down until the gate demanded
    // it. A visitor reading "north side slough" here is reading a depth that no
    // source gives, on a watercourse whose course is Wright's.
    check(`${label}: the invention the gate found is on the page, not only in the repo`,
      claims.slough.length === 1 && /north side slough/.test(claims.slough[0]),
      `L31c claims [${claims.slough.join(' | ')}]`);

    // Collapsed by default, and opening one gives the reasoning — not just the
    // admission that a liberty was taken.
    // A closed <details> still lays its contents out — measuring the body's own
    // box reads the same number open or shut. checkVisibility() is the signal
    // that answers the question actually being asked, and the list's height
    // confirms the panel really grew around it.
    // T-0710 RESTATED, NOT WEAKENED: the Evidence panel is a HUB now, and the
    // liberties are a topic shown on demand. A `checkVisibility()` read of an
    // entry inside a topic that is `display:none` is false open or shut, and the
    // mount's height reads 0 both times — so the topic is shown first and the
    // read also holds that the mount itself is in view. Same claim, honestly
    // taken under the new layout.
    const opened = await page.evaluate(() => {
      window.__chicago4d.evidenceHub.showTopic('liberties');
      const mount = document.getElementById('liberties');
      const first = mount.querySelector('details.lib');
      const body = first.querySelector('.lib-body');
      const snap = () => ({
        shown: body.checkVisibility(),
        list: mount.getBoundingClientRect().height,
      });
      const before = snap();
      first.open = true;
      const after = snap();
      first.open = false;
      return { mountShown: mount.checkVisibility(), before, after, text: first.textContent,
        topic: window.__chicago4d.evidenceHub.topic };
    });
    check(`${label}: expanding a liberty on its topic page reveals its reasoning`,
      opened.mountShown && opened.topic === 'liberties'
      && opened.before.shown === false && opened.after.shown === true
      && opened.after.list > opened.before.list + 40 && /Why/i.test(opened.text),
      `mount shown ${opened.mountShown}, shown ${opened.before.shown} -> ${opened.after.shown}, `
      + `list ${opened.before.list.toFixed(0)} -> ${opened.after.list.toFixed(0)} px`);

    // --- what is not here, in the same panel --------------------------------
    // The liberties answer "which parts did you make up". They cannot answer
    // "which parts did you find and leave out", and an empty street looks the
    // same whether a building is missing because nobody researched it or because
    // the evidence puts it two years later. The second is a finding with a
    // citation, and it shipped nowhere a visitor could read it until now.
    const excl = await page.evaluate(() => {
      const mount = document.getElementById('exclusions');
      const entries = [...mount.querySelectorAll('details.excl')];
      const byName = (re) => entries.find((d) => re.test(d.querySelector('.lib-title')?.textContent ?? ''));
      const saloon = byName(/Saloon Building/);
      const kinzie = byName(/Kinzie House/);
      return {
        counted: window.__chicago4d.exclusions?.count ?? 0,
        error: window.__chicago4d.exclusions?.error ?? 'no exclusions on the handle',
        rendered: entries.length,
        busy: mount.hasAttribute('aria-busy'),
        text: mount.textContent,
        titles: entries.map((d) => d.querySelector('.lib-title')?.textContent.trim() ?? ''),
        saloonWhen: saloon?.querySelector('.lib-scope')?.textContent.trim() ?? '',
        saloonReason: saloon?.querySelector('.lib-body dd')?.textContent.trim() ?? '',
        saloonCite: saloon?.querySelector('.cites .cite-text')?.textContent.trim() ?? '',
        saloonLinks: [...(saloon?.querySelectorAll('.cites a') ?? [])].map((a) => a.href),
        reprints: mount.querySelectorAll('.cite-reprints').length,
        kinzieWhen: kinzie?.querySelector('.lib-scope')?.textContent.trim() ?? '',
        kinzieReason: kinzie?.querySelector('.lib-body dd')?.textContent.trim() ?? '',
        // Collapsed: the standing note wraps across source lines, so a raw
        // textContent match would be asserting the HTML's line breaks.
        heading: (document.querySelector('[data-panel="evidence"]')?.textContent ?? '')
          .replace(/\s+/g, ' '),
        // The list's own account of itself, compiled into the derived document
        // and — until this landed — read into a return value and rendered by
        // nobody, while the markup carried a paraphrase of it.
        noteShown: document.getElementById('exclusions-note')?.textContent ?? '',
        noteRecorded: window.__chicago4d.exclusions?.standard ?? '',
        noteBusy: document.getElementById('exclusions-note')?.hasAttribute('aria-busy') ?? true,
        overflow: document.documentElement.scrollWidth <= window.innerWidth + 1,
      };
    });
    check(`${label}: the researched exclusions load`,
      excl.counted >= 14 && !excl.busy && excl.rendered === excl.counted,
      `${excl.rendered} rendered of ${excl.counted} (${excl.error})`);
    check(`${label}: an exclusion gives its reason and the source it rests on`,
      /1836/.test(excl.saloonReason) && /Andreas/.test(excl.saloonCite)
      && excl.saloonLinks.length > 0,
      `"${excl.saloonReason}" — ${excl.saloonCite} [${excl.saloonLinks.length} link(s)]`);
    // The chip is the record's own `earliest_scene`, never a phrase derived from
    // its absence: the Kinzie house is not here because it was GONE, and stamping
    // it "not until 1836" would be an invention on a panel about inventions.
    check(`${label}: a later building says when, and a vanished one says why instead`,
      /not until 1837/.test(excl.saloonWhen) && excl.kinzieWhen === ''
      && /GONE/i.test(excl.kinzieReason),
      `saloon "${excl.saloonWhen}" · kinzie "${excl.kinzieWhen}" / "${excl.kinzieReason.slice(0, 40)}"`);
    // The discriminating case: this is the list of things NOT in the scene, so a
    // building the visitor can walk up to must not appear on it. A section that
    // dumped the whole dataset would still have passed every check above.
    check(`${label}: a building standing in the scene is not on the not-here list`,
      !excl.titles.some((t) => /Sauganash|Green Tree|Wolf Point Tavern|Western Hotel/.test(t)),
      excl.titles.join(' | '));
    // Which is WHY this section withholds what a citation reprints, and the
    // rule above is the reason rather than a preference: the Inter Ocean piece
    // behind two of these entries is headed "The Old Western Hotel", and the
    // Western Hotel is standing 200 m away. Pinned so the option cannot quietly
    // flip back on — the card carries the line and this list does not.
    check(`${label}: the not-here list withholds what its sources reprint`,
      excl.reprints === 0, `${excl.reprints} reprints line(s) under the exclusions`);
    // …and it says so itself. A list of fourteen absences with no such sentence
    // reads as "this is what is missing", which would be the largest false claim
    // the panel could make — the town is short about thirty more buildings.
    check(`${label}: the list says it is not everything missing`,
      /What is not here/.test(excl.heading)
      && /not a list of everything missing/i.test(excl.heading),
      excl.heading.slice(-200));
    // …and it says it in the DERIVED document's words. Asserted verbatim against
    // the compiled value rather than a phrase copied in here, because the failure
    // this pins is the sentence in the repository disagreeing with the sentence
    // on the screen — the same assertion the liberties note and the ground's
    // scope already carry.
    check(`${label}: the not-here list says what it is, in the compiled document's words`,
      excl.noteShown === excl.noteRecorded && excl.noteRecorded.length > 80
      && !excl.noteBusy,
      `shown "${excl.noteShown.slice(0, 80)}" of ${excl.noteRecorded.length} recorded`);
    // Once, not twice: the hand-written paraphrase beside it is gone rather than
    // joined by the compiled sentence.
    check(`${label}: the panel states it once — the paraphrase is gone`,
      excl.noteRecorded
        ? excl.heading.split(excl.noteRecorded.replace(/\s+/g, ' ')).length - 1 === 1
        : false,
      `${excl.noteRecorded
        ? excl.heading.split(excl.noteRecorded.replace(/\s+/g, ' ')).length - 1
        : 'no'} occurrence(s)`);
    check(`${label}: the Evidence panel still does not overflow`, excl.overflow);

    // --- and the third category: researched, and still open -----------------
    // The exclusions answer "what did you find and leave out". They cannot hold
    // a structure whose 1835 status nobody could settle — and two of those three
    // are STANDING in the scene, so putting them on the not-here list would make
    // that list false. They get their own section and their own chip.
    //
    // THE COURT-HOUSE WAS THE FOURTH AND IS NOT AN OPEN QUESTION ANY MORE
    // (ROADMAP T-I3, 2026-08-16). Its question — "was it standing on 1 July
    // 1835?" — is answered: Andreas dates it to the fall in three places, the
    // record is re-dated, and it resolves into 1836 rather than into this scene.
    // The entry was argued off the list, which is what that list's own doc says
    // happens when the evidence arrives, so the expectations below moved from
    // four entries to three. That is authored data changing under a gate, not an
    // assertion being relaxed: every claim the court-house carried here is still
    // claimed, of an entry that still needs it. The chip pair now runs the other
    // way round as well — two standing against one unbuilt, where it was one
    // against three — so the section is still held to discriminating between
    // them rather than stamping one chip on everything.
    const open = await page.evaluate(() => {
      const mount = document.getElementById('uncertain');
      const entries = [...mount.querySelectorAll('details.uncertain')];
      const byName = (re) => entries.find((d) => re.test(d.querySelector('.lib-title')?.textContent ?? ''));
      const read = (d) => ({
        chip: d?.querySelector('.lib-scope')?.textContent.trim() ?? '',
        body: d?.querySelector('.lib-body')?.textContent.replace(/\s+/g, ' ').trim() ?? '',
        text: d?.textContent.replace(/\s+/g, ' ') ?? '',
        cites: [...(d?.querySelectorAll('.cites .cite-text') ?? [])].map((c) => c.textContent.trim()),
      });
      return {
        counted: window.__chicago4d.exclusions?.uncertainCount ?? 0,
        rendered: entries.length,
        busy: mount.hasAttribute('aria-busy'),
        western: read(byName(/Western Hotel/)),
        cobweb: read(byName(/Cobweb Castle/)),
        caldwell: read(byName(/Caldwell/)),
        heading: (document.querySelector('[data-panel="evidence"]')?.textContent ?? '')
          .replace(/\s+/g, ' '),
        // The same repair on the same fetch: this section's own account of the
        // third category, compiled and until now rendered nowhere. Its paraphrase
        // was the worse of the two — it had drifted into a hand-typed COUNT of
        // the open questions, wrong the day a fifth is recorded.
        noteShown: document.getElementById('uncertain-note')?.textContent ?? '',
        noteRecorded: window.__chicago4d.exclusions?.uncertainStandard ?? '',
        noteBusy: document.getElementById('uncertain-note')?.hasAttribute('aria-busy') ?? true,
        // The open-questions BLOCK alone — heading, notes, list — for the
        // hand-count guard below. The whole-panel text will not do: the
        // liberties list legitimately contains "Three of these records
        // describe multi-stemmed plants" (the K53 shrub liberty), and whether
        // that list is rendered in full depends on the pick state earlier
        // sections left behind — the staged runs (T-0060) surfaced exactly
        // that order-dependence.
        uncertainBlockText: (() => {
          const note = document.getElementById('uncertain-note');
          const list = document.getElementById('uncertain');
          const parts = [note?.previousElementSibling?.textContent,
            note?.textContent, list?.textContent];
          let p = note?.nextElementSibling;
          while (p && p !== list) { parts.push(p.textContent); p = p.nextElementSibling; }
          return parts.filter(Boolean).join(' ').replace(/\s+/g, ' ');
        })(),
        overflow: document.documentElement.scrollWidth <= window.innerWidth + 1,
      };
    });
    // T-0380 made it FOUR. The New York House joined the watch list on 2026-08-29
    // when its record was written: it had been an EXCLUSION whose own text said it
    // would stay one "only until a structure record replaces it", and the entry it
    // leaves behind still carries a live question — Andreas says "near Wells" and
    // Wells has two sides. T-0305 made it FIVE on 2026-08-30: S. B. Cobb's saddlery
    // stands on a corner read once, in 1833, and the Chicago American loses the cross
    // street in all three of its 1835 printings of the same card. The count is exact
    // on purpose, the same bookkeeping the frontage censuses above carry: an open
    // question appearing is worth failing over.
    check(`${label}: the open questions load`,
      open.counted === 5 && !open.busy && open.rendered === open.counted,
      `${open.rendered} rendered of ${open.counted}`);
    // The discriminating pair, and it is the whole argument for the section: two
    // of these three are buildings the visitor can walk up to and one is empty
    // ground. A section that stamped one chip on all three would have passed any
    // check for "there is a chip" — and would be lying about the Western Hotel.
    check(`${label}: the standing ones say they are standing and the unbuilt one does not`,
      /standing here/.test(open.western.chip) && /inferred/.test(open.western.chip)
      && /standing here/.test(open.cobweb.chip) && open.caldwell.chip === 'not built',
      `western "${open.western.chip}" · cobweb "${open.cobweb.chip}" · caldwell "${open.caldwell.chip}"`);
    // …and the doubt is not restated here in this section's own words. It names
    // the claim on the record that carries it, which is the same claim the
    // provenance card shows, so the two cannot drift.
    check(`${label}: the standing one names the claim on its record that carries the doubt`,
      /frame_1834\.documented_range/.test(open.western.text)
      && /provenance card/i.test(open.western.body),
      open.western.body.slice(0, 200));
    // An entry resting on no source record says so in a sentence. An empty list
    // of citations would read as an oversight rather than the finding it is —
    // the dossier does not say which source calls the story unverified, and
    // naming one here would be inventing it.
    check(`${label}: an uncited open question says why it is uncited`,
      /No source record/i.test(open.caldwell.text)
      && open.caldwell.cites.length === 0 && open.western.cites.length > 0,
      `caldwell ${open.caldwell.cites.length} cite(s) · western ${open.western.cites.length}`);
    check(`${label}: the panel says what the third category is`,
      /still an open question/i.test(open.heading)
      && /standing in front of you/i.test(open.heading),
      open.heading.slice(-240));
    // …in the compiled document's words, verbatim, and once. The paraphrase this
    // replaces counted the entries — "three of these … and the fourth" — which no
    // gate could have held to a list that grows.
    check(`${label}: the open questions say what they are, in the compiled document's words`,
      open.noteShown === open.noteRecorded && open.noteRecorded.length > 80
      && !open.noteBusy,
      `shown "${open.noteShown.slice(0, 80)}" of ${open.noteRecorded.length} recorded`);
    check(`${label}: the panel states that once too — and counts nothing by hand`,
      (open.noteRecorded
        ? open.heading.split(open.noteRecorded.replace(/\s+/g, ' ')).length - 1 === 1
        : false)
      && !/Three of these/i.test(open.uncertainBlockText),
      `${open.noteRecorded
        ? open.heading.split(open.noteRecorded.replace(/\s+/g, ' ')).length - 1
        : 'no'} occurrence(s); block "${open.uncertainBlockText.slice(0, 60)}"`);
    check(`${label}: the Evidence panel still does not overflow with it`, open.overflow);

    // …and the same entry on the building it is about. The section above tells a
    // visitor that "the provenance card shows it", and until now the card showed
    // the CLAIM — a dated span with an `inferred` chip — and never that the claim
    // is a tracked open question with a live dispute behind it. The doubt reached
    // whoever opened a panel about the scene, not whoever walked up to the house.
    //
    // Asserted against the rendered card, per building, on the discriminating
    // pair — as everywhere else on this card, and for the reason `documented_range`
    // taught: reading the derived list would prove only that the list is fine.
    const openCard = await page.evaluate(() => {
      const read = (id) => {
        window.__chicago4d.pick(id);
        const sec = document.querySelector('#popup .pop-question');
        const entry = sec?.querySelector('details.uncertain');
        const body = entry?.querySelector('.lib-body');
        const presence = [...document.querySelectorAll('#popup .pop-sec')]
          .find((s) => /Was it here/i.test(s.querySelector('h3')?.textContent ?? ''));
        return {
          present: !!sec,
          chip: entry?.querySelector('.lib-scope')?.textContent.trim() ?? '',
          text: (sec?.textContent ?? '').replace(/\s+/g, ' ').trim(),
          collapsed: body ? body.checkVisibility() === false : null,
          presenceChip: presence?.querySelector('.conf')?.textContent.trim() ?? '',
        };
      };
      const western = read('western_hotel');
      // Every other building in the scene, because "no section" is the rule and
      // not a property of whichever second building this pair happens to name.
      const others = [...window.__chicago4d.registry.keys()]
        .filter((id) => id !== 'western_hotel')
        .filter((id) => read(id).present);
      return { western, others };
    });
    check(`${label}: the open question reaches the building it is about`,
      openCard.western.present
      && /W\. H\. Stow/.test(openCard.western.text)
      && /hotel chronology/i.test(openCard.western.text)
      && /frame_1834\.documented_range/.test(openCard.western.text),
      openCard.western.text.slice(0, 220));
    // What no chip can say: what settling it would change. The grade tells a
    // visitor we are unsure; only this says the dispute is between the builder's
    // own statement and a chronology, and that the answer decides whether the
    // house was new or still going up on the day they are standing in.
    check(`${label}: it says what settling it would change`,
      /What it would change/i.test(openCard.western.text)
      && /STANDING in the scene/i.test(openCard.western.text),
      openCard.western.text.slice(-260));
    // One uncertainty, two surfaces, one grade. The card's own presence chip and
    // the open question's chip are read from the same record field, so a card that
    // qualified the two differently is exactly the drift the shared renderer and
    // the `carried_by` gate exist to stop.
    check(`${label}: the card grades the doubt the same way the claim above it is graded`,
      openCard.western.chip === 'inferred'
      && openCard.western.presenceChip === 'inferred',
      `question "${openCard.western.chip}" · presence "${openCard.western.presenceChip}"`);
    check(`${label}: it starts collapsed like every other disclosure on the card`,
      openCard.western.collapsed === true, `collapsed ${openCard.western.collapsed}`);
    // The discriminating case, and it is a deliberate silence rather than a
    // missing empty state. The watch list has exactly FOUR structures in the
    // scene: the Western Hotel, Cobweb Castle, the New York House (T-0380,
    // 2026-08-29, whose open question is which side of Wells Street it stood on)
    // and Goss & Cobb's saddlery (T-0305, 2026-08-30, whose question is which
    // cross street its corner of Lake Street is). Every other building must stay
    // silent; a card dumping the whole list would fail this exact set. Membership
    // rather than order: the panel's ordering is the file's, and this assertion is
    // about which buildings speak.
    check(`${label}: only tracked in-scene buildings carry open questions`,
      openCard.others.length === 3
      && ['cobweb_castle', 'new_york_house', 'goss_cobb_saddlery']
        .every((id) => openCard.others.includes(id)),
      `beside western_hotel: ${openCard.others.join(', ') || 'none'}`);
    // Reading every card leaves one open over the panel, which the panel's own
    // close button then cannot be clicked through.
    await page.evaluate(() => window.__chicago4d.popup.close());

    // --- what the ground claims, in the same panel ---------------------------
    // Every building can say what it asserts and how sure of it we are. The
    // surface all of them stand on is graded just as carefully in
    // `terrain_spec.json` and said none of it to a visitor — while dithering
    // under the confidence view, which shows that a grade exists and nothing
    // about what was graded.
    const ground = await page.evaluate(() => {
      const mount = document.getElementById('ground');
      const entries = [...mount.querySelectorAll('details.ground')];
      const read = (d) => ({
        label: d.querySelector('.lib-title')?.textContent.trim() ?? '',
        group: d.querySelector('.lib-scope')?.textContent.trim() ?? '',
        conf: d.querySelector('summary .conf')?.textContent.trim() ?? '',
        body: d.querySelector('.lib-body')?.textContent.replace(/\s+/g, ' ').trim() ?? '',
        cites: [...d.querySelectorAll('.cites > li')].map((li) => li.textContent.trim()),
        // Which of this claim's figures say they are not in front of you, by the
        // figure's own name — a count would pass against a panel that marked the
        // wrong row.
        marks: [...d.querySelectorAll('.lib-body dd .geom')].map((g) => ({
          field: g.closest('dd')?.previousElementSibling?.textContent.trim() ?? '',
          text: g.textContent.trim(),
        })),
      });
      const all = entries.map(read);
      const find = (labelRe, groupRe) => all.find(
        (e) => labelRe.test(e.label) && (!groupRe || groupRe.test(e.group))) ?? null;
      return {
        counted: window.__chicago4d.ground?.count ?? 0,
        error: window.__chicago4d.ground?.error ?? 'no ground on the handle',
        rendered: entries.length,
        busy: mount.hasAttribute('aria-busy'),
        water: find(/^water$/, /water surface/),
        bank: find(/^bank$/, /the bank/),
        south: find(/South Division/, /divisions/),
        material: find(/^north division$/, /made of/),
        southMaterialWest: find(/^south division west of State St$/, /made of/),
        southMaterialEast: find(/^south division east of State St$/, /made of/),
        marshMaterial: find(/^south division marsh$/, /made of/),
        // The compiled claim, so the assertion below compares the panel with the
        // repository rather than with a phrase typed into this file.
        recordedNotes: Object.fromEntries(
          (window.__chicago4d.ground?.claims ?? []).map(
            (c) => [c.id, (c.notes ?? []).map((n) => n.replace(/\s+/g, ' ').trim())])),
        // Land vertices: the divisions, the bank, the marsh, the swales and the
        // micro-relief. Their grades are what the caveat is about.
        landGrades: all.filter((e) => /divisions|the bank|marshy|swales|texture/.test(e.group))
          .map((e) => e.conf),
        inferredWithoutReason: all.filter(
          (e) => e.conf === 'inferred' && /No reasoning is recorded/.test(e.body))
          .map((e) => `${e.group}/${e.label}`),
        scopeShown: mount.querySelector('.ground-scope')?.textContent
          .replace(/^\s*What these claims cover\s*—\s*/, '') ?? '',
        scopeRecorded: window.__chicago4d.ground?.scope ?? '',
        text: mount.textContent.replace(/\s+/g, ' '),
        overflow: document.documentElement.scrollWidth <= window.innerWidth + 1,
      };
    });
    check(`${label}: the ground's claims load`,
      ground.counted >= 19 && !ground.busy && ground.rendered === ground.counted,
      `${ground.rendered} rendered of ${ground.counted} (${ground.error})`);
    // THE discriminating pair, and the reason this section is worth having: the
    // water plane is documented and the bank face — the largest unsourced
    // assumption in the build — is inferred. A section that stamped one grade
    // on the whole terrain would pass any check for "there is a chip".
    check(`${label}: the ground is graded per claim, not stamped`,
      ground.water?.conf === 'attested' && ground.bank?.conf === 'reconstructed',
      `water "${ground.water?.conf}" · bank "${ground.bank?.conf}"`);
    // The spec's own caveat, asserted where a visitor reads it rather than in the
    // file: no land elevation in this scene is better than inferred.
    check(`${label}: no land elevation claims to be documented`,
      ground.landGrades.length >= 6 && !ground.landGrades.includes('attested'),
      `${ground.landGrades.length} land claim(s): ${[...new Set(ground.landGrades)].join(', ')}`);
    // WHICH ground these twenty claims are about. The spec has stated its own
    // extent since it was written, `compile_scene.py` has compiled it into every
    // terrain sidecar, and no renderer ever asked for it — so a visitor who flew
    // up, saw the ground end, and came to this section to find out what it covers
    // was told everything except that. Verbatim against the compiled value, for
    // the same reason as the record's own account above.
    check(`${label}: the ground says which ground these claims are about`,
      ground.scopeShown === ground.scopeRecorded && (ground.scopeRecorded ?? '').length > 40
      && /forks.*harbour/i.test(ground.scopeShown ?? ''),
      `shown "${(ground.scopeShown ?? '').slice(0, 90)}" of `
      + `${(ground.scopeRecorded ?? '').length} recorded`);
    check(`${label}: the panel quotes the spec's caveat that no survey exists`,
      /No contour survey of the 1835 town site exists/.test(ground.text)
      && /no land elevation in this spec is better than/i.test(ground.text),
      ground.text.slice(0, 120));
    // A claim carries the spec's own figures and the source it rests on.
    check(`${label}: a land claim shows its figures and its citation`,
      /far \(m\)/.test(ground.south?.body ?? '') && /300/.test(ground.south?.body ?? '')
      && (ground.south?.cites ?? []).some((c) => /chicagoarchitecturehistory|architecture/i.test(c)),
      `${(ground.south?.body ?? '').slice(0, 80)} | ${(ground.south?.cites ?? [])[0] ?? 'no cite'}`);
    // Until 2026-08-10 this asserted the opposite: three surface materials were
    // graded `inferred` with no reasoning at all, and the panel said so because
    // the empty state was the finding. The three notes are written now — what
    // held them back was the staleness hash, not the research — so what is worth
    // pinning is the gate's rule (`check_terrain_claims`) asserted where a
    // visitor reads it: nothing that calls itself an INFERENCE may show the
    // disclaimer. Scoped to inferred on purpose — a documented claim owes
    // evidence, not an argument, so an assertion over the whole panel would have
    // read the two documented soil claims as gaps. One of those two has since
    // grown a note for a different reason; see the next assertion.
    check(`${label}: every claim that calls itself an inference records its reasoning`,
      !ground.inferredWithoutReason.length
      && /north-side section measured on its own/i.test(ground.material?.body ?? ''),
      `${ground.inferredWithoutReason.join(', ') || 'none'} | material `
      + `"${(ground.material?.body ?? '').slice(0, 80)}"`);
    // A grade this project has decided is too high, said where the grade is read.
    // `surface_materials.south_division` is `documented` on a 2022 essay that was
    // opened on 2026-08-11 and prints no citation for anything; the value is to
    // become `inferred` and cannot move until a Blender bake lands, because a
    // confidence is an input to the ground mesh. So the correction ships as prose
    // — which the terrain hash strips — and a visitor reads it under a chip that
    // is still the old one.
    //
    // Verbatim against the compiled claim rather than a phrase copied here: the
    // failure being pinned is the sentence in the repository disagreeing with the
    // sentence on the screen. And the pair is discriminating rather than a
    // presence check — the OTHER documented soil claim (the marsh, on
    // `chicagology_prefire273`) is correctly graded and carries no such
    // correction, so a panel that stamped this disclosure on every documented
    // claim would fail here.
    const southNotes = ground.recordedNotes?.['surface_materials.south_division west of State St'] ?? [];
    const marshNotes = ground.recordedNotes?.['surface_materials.south_division_marsh'] ?? [];
    const overGraded = southNotes.find((n) => /over-graded/.test(n)) ?? '';
    check(`${label}: the soil claim that is graded too high says so where it is graded`,
      ground.southMaterialWest?.conf === 'attested'
      && overGraded.length > 200
      && (ground.southMaterialWest?.body ?? '').replace(/\s+/g, ' ').includes(overGraded)
      && ground.southMaterialEast?.conf === 'attested'
      && ground.marshMaterial?.conf === 'attested'
      && !marshNotes.some((n) => /over-graded/.test(n))
      && !/over-graded/.test(ground.marshMaterial?.body ?? ''),
      `south-west "${ground.southMaterialWest?.conf}" carries ${overGraded.length} chars · `
      + `south-east "${ground.southMaterialEast?.conf}" · `
      + `marsh "${ground.marshMaterial?.conf}" carries ${marshNotes.length} note(s)`);
    // The empty state stays: it is a guard now rather than a finding, and the
    // committed data no longer exercises the half that matters — a claim that
    // OWES a reason and gives none. That is exercised directly: the renderer must
    // still say so for a claim with no reasoning, and must not say it for one that
    // has some — the discriminating pair, one level down from the panel.
    const emptyState = await page.evaluate(async () => {
      const { groundClaimHtml } = await import(window.__MODULE_BASE + 'ground.js');
      const claim = { id: 'x', group: 'g', label: 'l', confidence: 'inferred',
        fields: [], sources: [], citations: [], notes: [] };
      return {
        without: groundClaimHtml(claim),
        with: groundClaimHtml({ ...claim, notes: ['because the sources say so'] }),
      };
    });
    check(`${label}: a claim with no reasoning would still say so`,
      /No reasoning is recorded/.test(emptyState.without)
      && !/No reasoning is recorded/.test(emptyState.with)
      && /because the sources say so/.test(emptyState.with),
      emptyState.without.slice(0, 120));
    // The ground's version of the Wolf Point wolf sign, and the reason this slice
    // exists: the surface materials are graded — two of them `documented`, the
    // strongest grade this project awards — and NOTHING in the model is made of
    // any of them. The assertion is the discriminating pair rather than "a mark
    // exists": the material row is marked and the dossier-zone row beside it is
    // not, and the bank, whose face_m is what shapes every bank in the box,
    // carries no mark at all.
    check(`${label}: a soil the ground is not made of says so, and the figures that are do not`,
      (ground.material?.marks ?? []).some(
        (m) => /material/.test(m.field) && m.text === 'not modelled from this')
      && !(ground.material?.marks ?? []).some((m) => /dossier/.test(m.field))
      && !(ground.bank?.marks ?? []).length,
      `material marks ${JSON.stringify(ground.material?.marks ?? [])} · `
      + `bank marks ${JSON.stringify(ground.bank?.marks ?? [])}`);
    // And the mark is exercised at the renderer, so it survives the data being
    // repaired: the day S6 colours the ground by zone, the declaration comes off
    // the spec and the committed panel stops carrying this case.
    const marking = await page.evaluate(async () => {
      const { groundClaimHtml } = await import(window.__MODULE_BASE + 'ground.js');
      const claim = { id: 'x', group: 'g', label: 'l', confidence: 'attested',
        sources: [], citations: [], notes: ['because'] };
      const html = (mesh) => groundClaimHtml({ ...claim,
        fields: [{ key: 'material', value: 'loam', ...(mesh ? { mesh } : {}) }] });
      return { unbuilt: html('simplified'), built: html(null),
        restated: html('restated_in_code') };
    });
    check(`${label}: the mark is the declaration's, not the row's`,
      /not modelled from this/.test(marking.unbuilt)
      && !/not modelled from this/.test(marking.built)
      && !/geom/.test(marking.restated),
      marking.unbuilt.slice(0, 140));
    check(`${label}: the Evidence panel still does not overflow with the ground on it`,
      ground.overflow);
    // T-0210, and it was the LAST frame-bound chrome click in the file. This one
    // close timed out at ninety seconds on an unmodified tree and took the desktop
    // half of part 13 down with it, which read as a broken control and was not one.
    // Measured here at the click site itself, on the published mirror at 1280x800,
    // at three machine loads on one runner:
    //
    //   frame cost   2.18 s      3.17 s      7.05 s
    //   page.click   28.4 s      43.5 s      89.8 s    (13.0 / 13.7 / 12.7 frames)
    //   clickChrome   3.9 s       6.0 s      13.5 s    ( 1.8 /  1.9 /  1.9 frames)
    //
    // and `elementFromPoint` answered THIS BUTTON at its own centre in all three:
    // 26x26, enabled, uncovered, no pointer lock. So the control is fine and the
    // cost is a CONSTANT NUMBER OF FRAMES — a `page.click` here is thirteen of
    // them however fast the box is, which is why 90 s is not a budget but a coin
    // toss: it is breached the moment a frame costs more than 6.9 s, and this
    // runner reached 7.05 s with four burners on four cores. The loaded reading
    // landed at 89.8 s against the 90 s budget with two tenths of a second to
    // spare, which is the failure the ticket saw, caught mid-air.
    //
    // NOTHING IS WEAKENED BY THE SWAP. `clickChrome` asserts everything the real
    // click asserts implicitly — the element exists, is enabled, has a real box,
    // and is the topmost thing at its own centre — and fails in one round trip
    // naming what covered it. T-0215 made that argument and this is the same
    // control on the same page; the trusted-event clicks it names stay as they are.
    await clickChrome('#panel-close');

    // --- free-fly -----------------------------------------------------------
    // Three properties worth pinning, all of which would rot silently:
    // the aerial anchor arrives IN the air, the terrain is still a floor, and
    // landing puts you back on the ground rather than stranding the eye.
    const aerial = await page.evaluate(async () => {
      const a = window.__chicago4d;
      a.goTo('from_above');
      await new Promise((r) => setTimeout(r, 400));
      return {
        alt: a.player.altitude, flying: a.player.flying, pitch: a.player.pitchDeg,
        label: document.getElementById('badge-alt')?.textContent?.trim(),
      };
    });
    check(`${label}: the aerial anchor arrives in the air, looking down`,
      aerial.flying === true && aerial.alt > 100 && aerial.pitch < -10
      && /^\d+ ft up$/.test(aerial.label ?? '') && !/\d+ m up/.test(aerial.label ?? ''),
      `flying ${aerial.flying}, internal ${aerial.alt?.toFixed(0)} m, `
      + `HUD ${aerial.label}, pitch ${aerial.pitch?.toFixed(0)}`);

    const aboveShot = await page.evaluate(() => window.__chicago4d.capture());
    check(`${label}: the view from above renders`,
      aboveShot.mean > 12 && aboveShot.litFraction > 0.5,
      `mean luminance ${aboveShot.mean?.toFixed(1)}`);

    // R-BUG1 — the near plane opens with altitude, and closes again on foot.
    // The owner's flickering river edge is the depth buffer running out of
    // numbers at range, and precision at range is bought with the near plane:
    // at the fixed 0.1 m this camera used to carry, two surfaces 350 m away had
    // to be 10 cm apart before the buffer could order them, and the waterline is
    // co-planar with the ground BY DESIGN. The pixel-level gate is
    // `tools/measure_river_edge.mjs --gate` (it costs three frames a station and
    // does not belong in a suite this size); this pins the mechanism that gate
    // depends on, in the run that happens every merge. It is structural, not a
    // threshold: a walker's camera must not change, and an aerial one must.
    const nearPlane = await page.evaluate(async () => {
      const a = window.__chicago4d;
      await a.capture(4);
      const flying = { near: a.stats().cameraNear, alt: a.player.altitude };
      a.goTo('sauganash');
      await new Promise((r) => setTimeout(r, 400));
      await a.capture(4);
      const walking = { near: a.stats().cameraNear, alt: a.player.altitude };
      // Put the visitor back in the air. The free-fly tests below inherit this
      // state — `teleport` with an `altitude_m` lands a GROUNDED walker straight
      // back down, so a check that leaves the scene on foot fails the next one.
      a.goTo('from_above');
      await new Promise((r) => setTimeout(r, 400));
      await a.capture(4);
      return { flying, walking };
    });
    check(`${label}: the near plane opens with altitude`,
      nearPlane.flying.near >= 1 && nearPlane.flying.near <= 8,
      `near ${nearPlane.flying.near} m at ${nearPlane.flying.alt?.toFixed(0)} m up`);
    check(`${label}: on foot the near plane is the walking value`,
      Math.abs(nearPlane.walking.near - 0.1) < 1e-6,
      `near ${nearPlane.walking.near} m at ${nearPlane.walking.alt?.toFixed(2)} m up`);



    // Terrain is a floor even in free-fly. Driven by pushing the eye under the
    // ground and stepping once, NOT by flying into it: tick() uses wall-clock
    // dt and this suite runs at a couple of frames a second under SwiftShader,
    // so a "hold forward and dive" test would cover four metres and prove
    // nothing. One frame against a violated invariant is the honest form.
    const floored = await page.evaluate(() => {
      const a = window.__chicago4d;
      a.walker.teleport({ local_e: 60, local_n: -200, yaw_deg: 0, altitude_m: 40, pitch_deg: -80 });
      a.walker.state.eyeY -= 200;             // straight through the world
      a.step();
      return { alt: a.player.altitude, flying: a.player.flying };
    });
    check(`${label}: free-fly cannot sink through the terrain`,
      floored.flying === true && floored.alt > 0.5 && floored.alt < 4,
      `${floored.alt?.toFixed(2)} m above ground`);

    // Landing snaps, so one frame settles it — see walker.setFlying() for why
    // the smoothed descent was rejected.
    const landed = await page.evaluate(() => {
      const a = window.__chicago4d;
      a.goTo('from_above');
      a.setFly(false);
      a.step();
      return { alt: a.player.altitude, flying: a.player.flying, y: a.player.y };
    });
    check(`${label}: leaving free-fly puts the visitor back on the ground`,
      landed.flying === false && Math.abs(landed.alt) < 0.2,
      `flying ${landed.flying}, ${landed.alt?.toFixed(2)} m off the ground`);

    // Space is mode-scoped: it ascends in the air and inspects on foot. If that
    // ever leaks, walking visitors levitate every time they try to inspect.
    await page.evaluate(() => {
      window.__chicago4d.goTo('sauganash');
      // Aim at the building, the same way the pick test does — Space inspects
      // down the crosshair, so a test that has not aimed is testing the prairie.
      window.__chicago4d.frame('sauganash_hotel', 26);
    });
    await page.evaluate(() => window.__chicago4d.popup.close());
    await page.keyboard.press('Space');
    await page.waitForTimeout(250);
    const spaceOnFoot = await page.evaluate(() => ({
      alt: window.__chicago4d.player.altitude,
      flying: window.__chicago4d.player.flying,
      inspected: !document.getElementById('popup').hasAttribute('hidden'),
    }));
    check(`${label}: Space inspects on foot instead of lifting off`,
      spaceOnFoot.flying === false && Math.abs(spaceOnFoot.alt) < 0.2 && spaceOnFoot.inspected,
      `flying ${spaceOnFoot.flying}, ${spaceOnFoot.alt?.toFixed(2)} m up, inspected ${spaceOnFoot.inspected}`);

    // --- the keys that close the card (T-0108) -------------------------------
    //
    // Owner-reported: nothing closed an inspection card from the keyboard —
    // the only way out was scrolling up to its close button. Escape closes,
    // and the inspect key toggles: the reach that opened the card also closes
    // it. Escape is the browser's own pointer-lock release, which the handler
    // cooperates with by acting only when a card is open; there is no lock in
    // this harness, so the keystroke reaches the page directly. The card is
    // open right now, left by the Space assertion above.
    await page.keyboard.press('Escape');
    await page.waitForTimeout(150);
    const escClosed = await page.evaluate(() =>
      document.getElementById('popup').hasAttribute('hidden'));
    check(`${label}: Escape closes the inspection card`, escClosed,
      `card hidden after Escape: ${escClosed}`);

    await page.keyboard.press('Space');            // same crosshair, reopens
    await page.waitForTimeout(300);
    const reopened = await page.evaluate(() =>
      !document.getElementById('popup').hasAttribute('hidden'));
    await page.keyboard.press('KeyE');
    await page.waitForTimeout(300);
    const keyToggled = await page.evaluate(() =>
      document.getElementById('popup').hasAttribute('hidden'));
    check(`${label}: the inspect key closes the card it opened`,
      reopened && keyToggled,
      `reopened ${reopened}, closed by the same key ${keyToggled}`);

    // And neither fires from inside the Go-to box: typing is not a command.
    // (Escape in the box still shuts the Go-to PANEL — that is the panel's own
    // long-standing binding — but the card must not be collateral.)
    await page.keyboard.press('Space');            // card open again
    await page.waitForTimeout(300);
    await page.evaluate(() => {
      window.__chicago4d.hud.setPanel(true);
      document.querySelector('[data-tab="goto"]')?.click();
      document.getElementById('jump-search')?.focus();
    });
    await page.keyboard.press('KeyE');
    await page.waitForTimeout(150);
    // Read the box BEFORE Escape: Chromium natively clears a type=search
    // input on Escape, so reading after would show empty even though the
    // keystroke typed rather than fired.
    const typedE = await page.evaluate(() => ({
      cardOpen: !document.getElementById('popup').hasAttribute('hidden'),
      typed: document.getElementById('jump-search')?.value ?? '',
    }));
    await page.keyboard.press('Escape');
    await page.waitForTimeout(150);
    const afterEsc = await page.evaluate(() =>
      !document.getElementById('popup').hasAttribute('hidden'));
    check(`${label}: neither key fires while typing in Go-to`,
      typedE.cardOpen && typedE.typed.includes('e') && afterEsc,
      `E typed "${typedE.typed}" with card open ${typedE.cardOpen}, `
      + `card open after Escape ${afterEsc}`);
    await page.evaluate(() => {
      const box = document.getElementById('jump-search');
      if (box) box.value = '';
      window.__chicago4d.hud.setPanel(false);
      window.__chicago4d.popup.close();
    });

    // --- inspecting from the air --------------------------------------------
    //
    // Reported from use: "would be nice to be able to inspect something... i get
    // the dot and hit space and can see it when walking but cant do that when
    // flying because of the role of the space bar". Space is ascend up here, and
    // that is the right call — every flycam does it — so the fix is that CLICK
    // inspects, in both modes, which is the gesture everyone already has.
    //
    // The aim points are swept rather than fixed. From 200 m a roof is a small
    // target and most of the view is ground; pinning one aim point would make
    // this a test of the camera's heading rather than of whether inspecting
    // works at all from up there.
    const aerialPick = await page.evaluate(async () => {
      const api = window.__chicago4d;
      api.goTo('from_above');
      await new Promise((r) => setTimeout(r, 400));
      api.walker.teleport({ local_e: 110, local_n: -125, yaw_deg: 180,
                            altitude_m: 120, pitch_deg: -88 });
      await new Promise((r) => setTimeout(r, 400));
      let hits = 0;
      let first = null;
      for (let x = -0.9; x <= 0.9; x += 0.1) {
        for (let y = -0.9; y <= 0.9; y += 0.1) {
          const h = api.pick({ x, y });
          if (h) { hits += 1; first = first ?? h.id; }
        }
      }
      return { altitude: Math.round(api.player.altitude), hits, id: first,
               flying: api.player.flying };
    });
    check(`${label}: a building can be inspected from the air`,
      aerialPick.flying === true && aerialPick.altitude > 50
      && aerialPick.hits > 0 && aerialPick.id !== null,
      `at ${aerialPick.altitude} m up, ${aerialPick.hits} aim point(s) resolved a `
      + `structure (first: ${aerialPick.id ?? 'nothing'})`);

    // And the gesture that makes it discoverable: a click under the crosshair,
    // which means the same thing on foot and in the air. Driven through the same
    // mousedown a visitor's mouse sends, not by calling pick() — the point is
    // that the EVENT is wired, which is exactly what was missing.
    const clickPick = await page.evaluate(async () => {
      const api = window.__chicago4d;
      api.setFly(false);
      api.walker.teleport({ local_e: 107, local_n: -103, yaw_deg: 180 });
      await new Promise((r) => setTimeout(r, 250));
      const before = document.querySelector('#popup')?.textContent ?? '';
      // The backend only listens while the pointer is locked, which is the state
      // a walking visitor is in.
      const locked = api.controlBackend;
      // PointerLockControls tracks isLocked from the pointerlockchange event, so
      // setting the property is not enough on its own — the event has to fire.
      Object.defineProperty(document, 'pointerLockElement',
        { value: document.getElementById('view'), configurable: true });
      document.dispatchEvent(new Event('pointerlockchange'));
      await new Promise((r) => setTimeout(r, 60));
      window.dispatchEvent(new MouseEvent('mousedown', { button: 0, bubbles: true }));
      await new Promise((r) => setTimeout(r, 400));
      api.step();
      await new Promise((r) => setTimeout(r, 200));
      return { locked, before: before.slice(0, 40),
               after: (document.querySelector('#popup')?.textContent ?? '').slice(0, 80) };
    });
    check(`${label}: a click under the crosshair inspects`,
      /Sauganash/i.test(clickPick.after),
      `popup after click: "${clickPick.after}"`);
    await page.evaluate(() => window.__chicago4d.popup.close());
    await page.evaluate(() => window.__chicago4d.frame('sauganash_hotel', 26));

    inStageWork = false;
    } // end PART 13 (T-0060 stage 4b-ii, cut by T-0167; renumbered by T-0346, T-0173 and T-0170)
    } catch (e) {
      inStageWork = false;
      thrown = e;
    }

    // T-0215 — WHEN AN ACTION TIMES OUT, SAY WHAT A FRAME COSTS, because that is
    // the question the log leaves unanswered and the wrong answer has now been
    // given twice. `TimeoutError: page.click: Timeout 90000ms exceeded` on a
    // control that is visible, enabled and stable reads like a broken control,
    // and on 2026-08-13 and again on 2026-08-27 it was not one: Playwright's
    // click waits on animation frames, and this scene's frames cost 0.46-1.10 s
    // on a quiet machine and 17-27 s on a loaded one. Three sampled frames turn a
    // whole run of guessing into one line. It is a REPORT, never a bar — the
    // failure above still fails, and a slow frame is not an excuse for a control
    // that is genuinely gone.
    if (thrown && /Timeout .* exceeded/.test(String(thrown))) {
      try {
        const f = await page.evaluate(() => new Promise((done) => {
          const ms = []; let prev = performance.now();
          const step = () => {
            const now = performance.now(); ms.push(Math.round(now - prev)); prev = now;
            if (ms.length >= 3) done(ms); else requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
        }), { timeout: 120_000 });
        console.log(`        one animation frame costs ${f.join(' / ')} ms here `
          + `(0.46-1.10 s is this scene's cost on a quiet machine — a reading in `
          + `seconds means the action starved on frames, not on a missing control)`);
      } catch { console.log('        the page would not report a frame at all'); }
    }

    if (KEEP) {
      await page.screenshot({ path: path.join(KEEP, `walk-${viewport.width}x${viewport.height}.png`) });
    }
  }

  // T-0060: taken in EVERY invocation, staged or not. Both used to be
  // unreachable in practice — `zero page errors` was the tail of a body that
  // outgrew its command ceiling, so a killed run merged without ever having
  // been told whether the page threw, and an exception mid-suite died as a
  // bare stack with no summary and no page-error verdict at all.
  check(`${label}: the suite body ran to completion`, thrown === null,
    String(thrown ?? ''));
  check(`${label}: zero page errors`, errors.length === 0,
    errors.slice(0, 4).join(' | '));
  await ctx.close();
  await browser.close();
  console.log('');
}

// The vendored meshopt decoder must be a working module, because the published
// web derivatives will need it and a broken vendor file would only surface then.
{
  const browser = await launchBrowser();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(base, { waitUntil: 'domcontentloaded' });
  const meshopt = await page.evaluate(async () => {
    const m = await import('./vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js');
    await m.MeshoptDecoder.ready;
    return { supported: m.MeshoptDecoder.supported, decode: typeof m.MeshoptDecoder.decodeGltfBuffer };
  }).catch((e) => ({ error: String(e) }));
  check('vendor: meshopt decoder loads and reports supported',
    meshopt.supported === true && meshopt.decode === 'function',
    JSON.stringify(meshopt));
  check('vendor: meshopt import raises no page error', errors.length === 0, errors.join(' | '));
  await ctx.close();
  await browser.close();
}
server.close();

// T-0016 — re-bank, in the commit that moved the numbers on purpose.
//
// MERGES rather than overwrites, and that is not a convenience. The road bands
// are measured in stage 3 only, and a full unfiltered pass does not fit the
// ten-minute foreground command ceiling this repo actually works under (T-0121,
// still open) — so the only way anyone banks these in practice is one filtered
// run per viewport. Overwriting would let `SMOKE_VIEWPORT=mobile … --update`
// silently retire every desktop band, which is the same class of fault as the
// one this report exists to catch: a number quietly leaving the record.
// Merging keeps what this run did not measure and says what it left alone.
if (UPDATE_ROAD_BANDS) {
  {
    // Deliberately NOT refused on a red run. A bank is a record of what the
    // bands read, not a certificate that they read well, and the band everyone
    // is worried about is exactly the one that is failing — refusing to bank it
    // would leave T-0114's two reds as the only bands nobody can watch for
    // further collapse. Bands below their bar are marked `failingGateWhenBanked`
    // instead, which is what stops the file being read as a pass.
    const merged = { ...ROAD_BAND_BANKED, ...ROAD_BAND_OBSERVED };
    const untouched = Object.keys(ROAD_BAND_BANKED).filter((k) => !(k in ROAD_BAND_OBSERVED));
    fs.writeFileSync(ROAD_BAND_BASELINE, `${JSON.stringify({
      note: 'T-0016 — what each GATED road band read, so movement against it can be '
          + 'reported in either direction. A record, NOT a bar: the gate is '
          + 'ROAD_MIN_DELTA_L / ROAD_MIN_PERCEPTIBLE / ROAD_MIN_PROBES in '
          + 'smoke_renderer.mjs and nothing here changes it. A band below its bar is '
          + 'still banked, marked failingGateWhenBanked, so it can be watched for '
          + 'further collapse. Re-bank with `--update-road-bands`, which MERGES: a '
          + 'run banks the bands it measured and leaves the rest alone, because the '
          + 'road bands live in stage 3 and a full unfiltered pass does not fit the '
          + 'ten-minute command ceiling (T-0121).',
      bands: Object.fromEntries(Object.entries(merged).sort()),
    }, null, 2)}\n`);
    console.log(`\nre-banked ${Object.keys(ROAD_BAND_OBSERVED).length} road band(s)`
      + ` → ${path.relative(process.cwd(), ROAD_BAND_BASELINE)}`
      + (untouched.length ? `; left ${untouched.length} band(s) this run did not measure `
        + `untouched (${[...new Set(untouched.map((k) => k.split('/')[0]))].join(', ')})` : ''));
  }
}

console.log(`\n${passes.length} passed, ${failures.length} failed`);
// T-0060: the audit line. In an unfiltered run the staged-section count is the
// sum of what SMOKE_STAGE=1 … 12 each report, and the always-on count is
// identical in every one of them — that arithmetic is how the parts are
// demonstrated to add up to the whole.
console.log(`${stageWorkChecks} staged-section check(s)`
  + `${STAGE ? ` (stage ${STAGE} of ${PARTS})` : ' (all stages)'}, `
  + `${passes.length + failures.length - stageWorkChecks} always-on check(s)`);
// T-0121: every invocation records its own fit. The stage split exists to hold
// each command under a ten-minute ceiling, and three separate runs had to
// re-measure it by hand before anyone knew it had been breached; a run that
// prints its own wall clock is the cheapest possible early warning that the
// town has grown into the next margin.
{
  const secs = Math.round((Date.now() - startedAt) / 1000);
  console.log(`${Math.floor(secs / 60)} m ${String(secs % 60).padStart(2, '0')} s`
    + `${STAGE ? ` for stage ${STAGE}` : ' unfiltered'}`
    + `${ONLY ? ` at ${ONLY}` : ''} — the ceiling on a steward run's single `
    + 'foreground command is 10 m 00 s');
}
if (failures.length) {
  console.log(`FAILURES:\n - ${failures.join('\n - ')}`);
  process.exit(1);
}
console.log('SMOKE PASS');
