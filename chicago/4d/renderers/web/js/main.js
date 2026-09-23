/**
 * main.js — boot, loop, and the test harness handle.
 *
 *   ?year=1835     which scene (default 1835)
 *   ?anchor=fort   start at a named camera anchor from the scene file
 *   ?data= ?assets=  override where the dataset lives
 *   ?debug=1       print budgets to the console after boot
 *
 * `window.__chicago4d` is the harness handle. `tools/smoke_renderer.mjs` drives
 * the real page through it: it is a view onto the running scene, not a parallel
 * code path, so a test that passes means the thing a visitor loads works.
 */

import * as THREE from 'three';

/** The horizontal field of view the walk holds (Hor+ — the vertical follows the
 *  aspect, see resize()). Named because the framing rule reads it too. */
const H_FOV_DEG = 76;
const DEG = Math.PI / 180;

import { createBoot, createCheckpoint, yieldToPaint } from './boot-phases.js';
import { loadScene, resolveBases } from './scene-loader.js';
import { createWorld } from './world.js';
import { createTerrain, enuToWorld, groundTiling, hazeReachM } from './terrain.js';
import { createBuildings } from './buildings.js';
import { createConfidenceView } from './confidence.js';
import { createIntent, createBackendSwitch } from './controls/intent.js';
import { createPointerLockBackend, isTyping } from './controls/pointerlock.js';
import { createTouchBackend, prefersTouch } from './controls/touch.js';
import { createWalker, footprintsFrom, decksFrom, WALK } from './walker.js';
import { createFlora } from './flora.js';
import { createTrees } from './trees.js';
import { createPopup } from './popup.js';
import { createHud } from './hud.js';
import { createNavigation } from './navigation.js';
import { createStreets } from './streets.js';
import { createEnclosures } from './enclosures.js';
import { loadOrdinanceLimits } from './ordinances.js';
import { loadAgencies } from './agencies.js';
import { createFencedGround } from './yards.js';
import { createSignage } from './signage.js';
import { createYardGoods } from './yard.js';
import { createFrontage } from './frontage.js';
import { createFarMerge } from './far-merge.js';
import { createWharves } from './wharves.js';
import { createBoats } from './boats.js';
import { createWells } from './wells.js';
import { mountExclusions } from './exclusions.js';
import { mountPopulation } from './population.js';
import { mountOrderBook } from './orderbook.js';
import { mountFauna } from './fauna.js';
import { mountPlants } from './plants.js';
import { mountResidents } from './residents.js';
import { mountGround } from './ground.js';
import { mountCityCensus } from './census.js';
import { mountLiberties } from './liberties.js';
import { createRouter } from './route.js';
import { createTravel } from './travel.js';
import { mountPeople } from './people.js';
import { firmCrosswalk, mountBusinesses } from './businesses.js';
import { createEvidenceHub } from './evidence.js';

const VERSION = '0.1.0';

/**
 * T-0150 — HOW FAR DOWN A STREET THE DERIVED FURNITURE IS DRAWN AT `light`, IN
 * METRES, AND THE MEASUREMENT THAT SET IT.
 *
 * T-0149's first piece. T-0135 walked five named stands instead of one and found
 * the town far over every ceiling at the two AXIAL views — Lake Street east from
 * Canal, and the forks from Wolf Point — because a long open sightline is where
 * the 2026-08-21 chunking cannot help: nothing is behind the camera, so no chunk
 * is culled and every one of them is a draw call the sightline has to pay. The
 * owner raised the ceilings to carry it ("raise it, I think") and opened T-0149
 * to win the floor back by TRIMMING the axial view rather than by carrying it,
 * naming a furniture distance cull as the first thing to try.
 *
 * MEASURED BEFORE IT WAS SET, at the whole stand set and at both release
 * viewports, with `tools/measure_furniture_reach.mjs` — which drives the shipped
 * cull rather than a model of it, holds the clock so the wind is not measured as
 * a change, and reports a residual of the baseline against itself (0 everywhere)
 * so the deltas below are known to be signal. Source tree, `light`:
 *
 *   desktop 1280x800        drawn whole      at 350 m       saved   frame 48^2
 *   Lake at Canal, east   998,073 / 177   745,933 /  70   252,140 / 107   0.01 / 4
 *   the forks             990,772 / 156   782,316 /  71   208,456 /  85   0.00 / 0
 *   Lake and Market       733,530 /  99   682,216 /  77    51,314 /  22   0.00 / 0
 *   the open aerial       617,538 /  83   588,198 /  66    29,340 /  17   0.03 / 6
 *   the Sauganash at 26 m 590,322 /  68   582,882 /  62     7,440 /   6   0.00 / 0
 *
 *   mobile 390x780
 *   Lake at Canal, east   966,541 / 167   717,793 /  65   248,748 / 102   0.00 / 2
 *   the forks             933,656 / 138   743,432 /  63   190,224 /  75   0.00 / 0
 *   Lake and Market       565,060 /  78   555,970 /  70     9,090 /   8   0.00 / 0
 *   the open aerial       511,561 /  65   506,891 /  59     4,670 /   6   0.00 / 3
 *   the Sauganash at 26 m 542,696 /  59   541,424 /  57     1,272 /   2   0.00 / 0
 *
 * So the worst stand at `light` goes from 998,073 triangles and 177 draw calls
 * to 745,933 and 70 — a quarter of the geometry and SIXTY PER CENT OF THE CALLS,
 * for a frame that moves by a worst cell of 4 counts out of 255 where the gates
 * that prove a whole layer is visible need 6 and a mean of 0.30.
 *
 * WHY 350 AND NOT 300, WHICH IS THE FIGURE T-0149 NAMES. Both were measured. At
 * 300 m the worst stand gives another 5,954 triangles and 3 calls — and the OPEN
 * AERIAL, the only stand in the table whose picture changes at all, doubles from
 * mean 0.03 / worst 6 to mean 0.06 / worst 13, and then runs away to 0.18 / 23 at
 * 250 m. That stand is a camera 175 m up, so its slant range reaches the whole
 * town at once and the cull arrives everywhere in the frame together; it is the
 * one view where furniture leaving is something you could see. 350 m is the knee:
 * it keeps 252,140 of the 258,094 triangles and 107 of the 110 calls that 300 m
 * would win, and halves the only cost the instrument can find.
 *
 * WHY NOT 400, WHICH COSTS THE AERIAL NOTHING AT ALL (0.01 / 6). It leaves 28,904
 * triangles and 37 calls on the table at the worst stand for a reading the aerial
 * already matches at 350. The trade was taken toward the tier's own purpose,
 * which is the machine that needs the floor.
 *
 * THE PIXEL ARGUMENT, for the record and not as the bar. This camera is 62
 * degrees over 800 CSS pixels, so a 1.2 m fence pale subtends 739 · 1.2 / d
 * pixels: 2.5 at 350 m, 2.2 at 400 m, 3.0 at 300 m. That is the intuition — a
 * pale at this range is a couple of pixels of a line — but the number above was
 * set from the frame measurement, because "how many pixels tall is a pale" and
 * "does the picture change when the fence goes" are different questions and only
 * the second one is the one being answered.
 */
const FURNITURE_REACH_LIGHT_M = 350;

/**
 * THE MIDDLE RUNG GETS A REACH TOO — T-0241, 2026-08-27, and it is the tier
 * ladder finally being a ladder.
 *
 * `light` has had a reach since T-0150 and `balanced` had NONE, so "turn the
 * quality down and less is drawn" was true of the bottom rung and false of the
 * one above it: `balanced` drew every plank walk, fence, barrel, wharf deck and
 * moored hull in Chicago at any distance, exactly as `full` does. That is what
 * refused Washington Street. With the street laid, `balanced` read 1,259,442 at
 * the axial stand against its 1,210,000 — OVER by 49,442 — while `full` passed
 * with 14,613 clear and `light` with 23,440. One rung, and not the town.
 *
 * The three honest routes past that were named in T-0241 and two of them were
 * already spent: T-0056 measured the enclosure layer and found it ALREADY
 * thinning at `balanced`, and T-0223's cull had landed and been given back as
 * T-0229's ceiling restoration. A sixth re-basing is what T-0223, T-0229 and
 * T-0237 exist to make harder. So: the trim.
 *
 * MEASURED BEFORE IT WAS SET, same instrument as `light` above
 * (`tools/measure_furniture_reach.mjs`, now with `--level` so it can be pointed
 * at a tier other than the floor), published mirror, WITH Washington laid, at
 * T-0135's five stands and both release viewports:
 *
 *   desktop 1280x800        drawn whole      at 800 m        saved   frame 48^2
 *   Lake at Canal, east   1,259,442 / 151  1,190,670 / 146   68,772   0.00 / 0
 *   the forks             1,245,668 / 157  1,195,188 / 152   50,480   0.00 / 0
 *   Lake and Market         969,677 / 157    969,677 / 157        0   0.00 / 0
 *   the open aerial         792,819 / 122    792,387 / 121      432   0.00 / 0
 *   the Sauganash at 26 m   811,265 / 115    810,401 / 113      864   0.00 / 0
 *
 *   mobile 390x780
 *   Lake at Canal, east   1,201,716 / 151  1,133,376 / 147   68,340   0.00 / 0
 *   the forks             1,101,700 / 142  1,062,216 / 136   39,484   0.00 / 0
 *   Lake and Market         784,108 / 143    784,108 / 143        0   0.00 / 0
 *   the open aerial         663,078 / 101    663,078 / 101        0   0.00 / 0
 *   the Sauganash at 26 m   733,227 / 105    733,227 / 105        0   0.00 / 0
 *
 * THE FRAME DOES NOT MOVE. Not "moves a little": the 48² signature reads a worst
 * cell of ZERO against the same frame drawn whole, at every stand, at both
 * viewports, with the clock held — where the residual of the baseline against
 * itself is also 0, so the instrument is known to be reading signal. `light`'s
 * own 350 m could not say that; it moves the open aerial by a worst cell of 6.
 * Say the limit of the claim as plainly as the claim: a 48² signature is a
 * downsample, and at 800 m a 1.2 m fence pale subtends 1.1 CSS pixels of this
 * frame, which is below what it can resolve. What is being asserted is that
 * nothing this instrument can see changes, and the pixel arithmetic says why.
 *
 * WHY 800 AND NOT 700, WHICH SAVES NEARLY TWICE AS MUCH (126,070 at the axial
 * stand). Because a cull is a deletion and the rule here is to cut as little as
 * buys the room. 800 m is the LONGEST reach in the sweep that gets `balanced`
 * inside its ceiling, and it lands the tier on 1,195,188 of 1,210,000 — 1.2 %
 * clear, against `full`'s 1.0 % and `light`'s 3.0 %. The ladder keeps its shape,
 * which is the test this table has been re-taught five times, and 700 m stays on
 * the table for whatever asks for room next rather than being spent here.
 *
 * WHAT THIS IS NOT: a ceiling raise. Nothing in `DETAIL` below moves.
 */
const FURNITURE_REACH_BALANCED_M = 800;

/**
 * Scene detail: how much geometry the visitor asks for.
 *
 * 600 000 triangles used to be a single hard ceiling written into the release
 * gate, and it had quietly become an architectural constraint — the reason a
 * finished parcel of buildings could not be added was a number, not a machine.
 * A ceiling is the wrong instrument for that. It is now a CHOICE with three
 * settings, the gate holds each one to ITS OWN ceiling, and the town can grow
 * into the top of the range while anyone on a slow machine steps down.
 *
 * `densityScale` scales the flora and tree CAPS only — the same species in the
 * same places, fewer of them. It never changes where a plant may stand, which
 * is evidence rather than performance. Buildings, terrain and the river do not
 * scale at all: the reconstruction is not allowed to get less true because a
 * machine is slow, so what gives way is the sward, which is the only layer whose
 * count is a rendering decision rather than a claim.
 *
 * ---------------------------------------------------------------------------
 * T-0115 — WHY THE SWARD ALONE COULD NOT HOLD THE BOTTOM RUNG, AND WHAT ELSE
 * GIVES WAY NOW.
 *
 * The paragraph above is the design as written, and by August 2026 it had
 * stopped being arithmetically possible. Measured on the published mirror at
 * the release gate's own stand (`frame('sauganash_hotel', 26)`), desktop:
 *
 *   full     850,657 of 1,000,000    85 % of its ceiling
 *   balanced 769,279 of   800,000    96 %
 *   light    668,293 of   600,000   111 %  — over, and the reason for T-0115
 *
 * The ladder PROMISES a 40 % step from `full` to `light` — that is what
 * 1,000,000 → 600,000 says. It DELIVERED 21.4 %. It could not deliver more,
 * because the setting had a lever on only 39 % of the frame: flora and trees.
 * The other 61 % — terrain, buildings, streets, fences, yard goods, plank
 * walks, signboards, wharves, boats, and the sun's second pass over all of
 * them — was drawn identically at every level. **A 40 % cut cannot be taken
 * out of 39 % of a scene.** Everything the town grew after the tiers were
 * written was grown outside the tiers' reach, which is exactly how the ceiling
 * eroded: nothing was wrong with any one merge, and the control had no hold on
 * any of them.
 *
 * The ceiling is NOT re-budgeted. What is added is two more things that give
 * way at `light`, chosen by the same test the sward passes — a rendering
 * decision rather than a claim — and both of them are the SUN rather than the
 * town:
 *
 *   `shadowReachM` — how far from the visitor the sun's shadow is cast. At
 *   `light` the box steps back to the ±120 m this project shipped between
 *   R-W3b(a) and R-W5a2, and the map halves with it so the TEXEL is unchanged
 *   (world.js `setShadowRig`). Nothing a visitor stands next to gets softer;
 *   what the step costs is reach — past 120 m the town meets the ground with
 *   nothing under it — and it also quarters the shadow map's memory, which is
 *   the largest single GPU allocation this scene makes and the one a weak
 *   machine feels first.
 *
 *   `furnitureCastsShadow` — whether the DERIVED FURNITURE casts into the
 *   shadow map at all. A fence, a barrel, a plank walk, a dock and a moored
 *   hull are drawn from committed records and their PRESENCE is a claim; the
 *   stripe each one lays on the ground is lighting, and lighting is not a
 *   claim. At `light` they stand exactly where they stand, drawn exactly as
 *   they are drawn, still RECEIVING the shadows of the buildings and the timber
 *   around them — they just stop being drawn a second time for the sun.
 *   Buildings, terrain and the timber keep casting at every level: a town whose
 *   houses and trees met the ground with nothing under them is the defect
 *   R-W3b(a) exists to have fixed, and this does not reopen it. The hanging
 *   signboards keep casting too, and FURNITURE_LAYERS below says why with the
 *   measurement that decided it.
 *
 * Measured together at the same stand: desktop 668,293 → 584,761 of 600,000,
 * 55 → 49 draw calls. Recorded in docs/LIBERTIES.md L156, which is L121's
 * entry for the wood one layer over.
 *
 * ---------------------------------------------------------------------------
 * T-0067 — AND THE THIRD THING THAT GIVES WAY, WHICH IS TIMBER RATHER THAN SUN.
 *
 * T-0115's ledger left two costed findings for whoever took the fence tickets,
 * and this is the second of them: a picket pale is a 10-triangle prism whose two
 * 22 mm edge faces and 22 mm top cap are SIX of those ten — three quarters of
 * the geometry for a fortieth of the silhouette. At `light` a pale is drawn as a
 * zero-thickness double-sided plank instead (`enclosures.js` `pushBox`), which
 * is 4 triangles: same width, same height, same place, same rhythm, and a
 * thickness you could only see by standing on the fence line and looking along
 * it. It passes the same test the sward and the shadow reach pass — a rendering
 * decision rather than a claim — and it is the lever that keeps the fence
 * tickets affordable, because every pale T-0067, T-0068 and T-0069 add now costs
 * 4 triangles at `light` rather than 10.
 *
 * T-0068 extended the same plank to `balanced`, and for the tier's own sake: the
 * middle tier had never taken anything off this layer, so a pale cost the same
 * ten triangles there as at `full` and the town's fences scaled identically at
 * both. With 3.5 km of lot line on the layer that put `balanced` at 794,000 of
 * its 800,000 while `full` sat 150,000 clear of its own — a ceiling doing no
 * work. `balanced` now gives up the 22 mm, worth about 56,000 triangles, and
 * `full` still draws the prism. `enclosures.js` `PLANK_LEVELS` is where that
 * lives, and no triangle ceiling moved to pay for any of it.
 *
 * (T-0115's FIRST finding, chunking the town-wide fence mesh so the frustum can
 * cull it, is not a tier at all — it costs a visitor nothing at any level and is
 * simply how `enclosures.js` builds now.)
 *
 * ---------------------------------------------------------------------------
 * T-0135, 2026-08-22 — THE CEILINGS RE-ARGUED AGAINST THE WORST STAND, AND
 * DELIBERATELY NOT MOVED.
 *
 * Every figure above, and every figure in `BUDGET` below, was read at ONE
 * camera: `frame('sauganash_hotel', 26)`. The release gate now walks a named set
 * of five stands and holds each tier to its ceiling at the worst of them
 * (`tools/smoke_renderer.mjs` `STANDS`, where each stand's reason is written).
 * This is the first reading of that set — source tree, 1280x800, desktop:
 *
 *                              full        balanced      light      light calls
 *   Lake at Canal, east    1,320,377     1,144,787     992,617          177
 *   the forks, Wolf Point  1,318,202     1,137,646     984,612          156
 *   Lake and Market        1,112,086       943,776     729,844           99
 *   the open aerial          971,455       808,920     615,266           83
 *   the Sauganash at 26 m    960,515       815,021     587,798           68
 *   ---------------------------------------------------------------------
 *   ceiling                1,000,000       900,000     600,000       80 (floor)
 *
 * Worst draw calls, `full`: 200 at Lake at Canal against a budget of 140.
 *
 * SO THE TOWN IS 32 % OVER AT `full`, 27 % OVER AT `balanced` AND 65 % OVER AT
 * `light` at the stands a visitor can walk to — and it was over before this
 * ticket, and before any of the four parcels that raised the ceiling on
 * 2026-08-21. Nothing regressed here. What changed is that something finally
 * looked.
 *
 * THE NUMBERS ARE NOT MOVED, and that is a decision rather than an oversight.
 * AGENTS.md's own ruling has two halves and this run can only honour one of
 * them. "Just raise it" is the first half; "`light` is the floor and stays the
 * floor" is the second, and raising `light` to carry 992,617 would put the
 * bottom rung ABOVE the ceiling `full` carries today. That is not a re-budget,
 * it is the ladder ceasing to exist — and the tier a weak machine boots into is
 * the one promise in this table that is made to a person rather than to a
 * number. Raising `full` and `balanced` while `light` sat 65 % over would be
 * worse still: a ceiling moved to fit the camera that flatters it, which is the
 * exact defect T-0135 was opened to end.
 *
 * The ladder itself still works — 25 % from `full` to `light` at Lake at Canal
 * against 39 % at the reference stand — so the honest reading is that the
 * ceilings were authored as REFERENCE-STAND numbers and the scene has outgrown
 * the shape of the question, not merely its answer. The two routes T-0135 names
 * are both open (raise, or trim the axial view to fit), and choosing between
 * them is the owner's: it trades a promise about weak machines against a
 * rendering programme. Recorded here, at the definition site, per the ruling's
 * third half — MEASURE, THEN MOVE. This is the measure. The move is his.
 */
const DETAIL = {
  // RAISED 2026-08-22 TO CARRY THE WORST STAND, ON THE OWNER'S RULING ("raise
  // it, I think"), and this is the entry that says what it cost. T-0135 built
  // the instrument that walks five named stands instead of one and found the
  // town 32% over at `full`, 27% at `balanced` and 65% at `light` — at
  // viewpoints the Go-to menu already offers. Nothing had regressed; the
  // ceilings were authored as reference-stand numbers and only the reference
  // stand was ever measured.
  //
  // WHAT WAS GIVEN UP, SAID PLAINLY: `light` now carries 1,050,000, which is
  // MORE than `full` promised the day before this commit. The bottom rung is
  // heavier than the old top rung, so `light` is no longer a floor a weak
  // machine can be promised — it is merely the cheapest of three expensive
  // tiers. That was the trade the owner took knowingly, and T-0149 exists to
  // win the floor back by trimming the axial view (distance culling or an LOD
  // down a long street) rather than by pretending the number is small.
  //
  // These are worst-stand numbers now, not reference-stand numbers, with about
  // 6% of headroom over the measured worst. The next parcel that breaches them
  // is breaching a bar that means something.
  //
  // T-0150, 2026-08-23 — AND THE FIRST INSTALMENT ON THAT DEBT IS PAID, THOUGH
  // NOT THE CEILINGS THEMSELVES. `furnitureReachM` below distance-culls the
  // derived furniture at `light` only, and the worst stand now reads 745,933
  // triangles and 70 draw calls where it read 998,073 and 177 — so the bottom
  // rung has stopped being the heaviest thing this project ever shipped, and
  // `light` sits 29% under its own ceiling instead of 5%. The NUMBERS in this
  // table are deliberately untouched all the same: re-lowering them is T-0147,
  // and it is a separate ticket precisely so that the trim has to be measured
  // before the ceiling is allowed to follow it down. A ceiling lowered in the
  // same breath as the trim that justified it is a ceiling nobody checked.
  // ── THE 2026-08-27 RAISE IS TAKEN BACK OUT, T-0229 ─────────────────────────
  //
  // For one day these two numbers read 1,425,000 and 1,260,000. They were
  // raised on the owner's decision to clear a breach that was real and whose
  // cause was measured and was NOT the town's content: `trees.js` submitted
  // kilometre-wide quadrant meshes whole to a ±240 m shadow box, so the sun
  // drew 180,100 triangles of timber it could not cast — 14.4 % of the worst
  // frame, roughly four times the headroom either ceiling needed (T-0223's
  // layer table). The raise was filed WITH an expiry TICKET rather than as a
  // comment promising to be temporary, and this is that ticket closing.
  //
  // T-0223 landed the cull: the near timber is chunked on a 120 m lattice and
  // submitted as one batched multi-draw, so the sun's box and the view frustum
  // both cull it per cell. Re-read afterwards on the published mirror with
  // `tools/measure_detail_ceilings.mjs` — the instrument that reproduces the
  // gate's own five-stand sweep to the triangle — at the WORST of T-0135's five
  // stands, on the tree these constants ship in:
  //
  //              desktop 1280x800              mobile 390x780        here
  //   full       1,252,879 (the forks)         1,145,313 (Lake)   1,400,000
  //   balanced   1,084,292 (the forks)         1,020,684 (Lake)   1,210,000
  //   light        703,610 (the forks)           649,296 (Lake)   1,050,000
  //
  // So `full` comes home with 147,121 triangles clear and `balanced` with
  // 125,708 — about 10 % of each ceiling. The raise had bought 12,880 at `full`,
  // and T-0237 measured 91 % of that spent within twelve hours by content
  // landing behind it: a ceiling raised to be temporary was consumed faster
  // than the trim that was meant to retire it could land.
  //
  // THE WORST STAND MOVED WITH THE CULL, from Lake Street at Canal to the forks
  // at Wolf Point, and that is the five-stand sweep earning its place. A
  // one-camera instrument pointed down the axial street reads 1,207,211 at
  // `full` here — 45,668 triangles short of the frame that actually costs the
  // most, and it was the axial street that was the worst stand before the cull.
  //
  // T-0229's escape clause was that if the cull recovered materially less than
  // 180,100 these ceilings had to be re-argued from a fresh measurement rather
  // than quietly kept at the raised numbers. It did not: both tiers land under
  // the ORIGINAL figures at both viewports, so the original figures are what
  // stand here and nothing in this table is provisional any more.
  //
  // FIVE RE-BASINGS OF THESE CEILINGS ARE RECORDED ABOVE THIS LINE AND THIS IS
  // THE FIRST ONE EVER GIVEN BACK. That is the count a sixth raise has to argue
  // against, and it is now a count of five raises and one return.
  // ── SIXTH RE-BASING, 2026-09-03, ON THE OWNER'S EXPLICIT RULING ──────────────
  // The count above was "five raises and one return", and said a sixth "has to
  // argue against" it. This is the argument, and the ruling that authorises it.
  //
  // THE RULING, verbatim: "i answered raise with stated headroom and a named
  // retirement from before but it may have been lost." It had been: PR #599
  // named T-0441 as the ticket holding the fork, and T-0441 WAS NEVER FILED —
  // a clean id gap between T-0440 and T-0442 — so four PRs sat parked for four
  // days on a question the ledger had never been asked. T-0673 is that receipt.
  // Told the raise would have to touch `light` as well, he ruled again, in as
  // many words: "raise all 3".
  //
  // WHERE IT IS NOT SPENT, and this is the first thing measured rather than the
  // last. `tools/measure_detail_ceilings.mjs --only desktop`, dev, 2026-09-03:
  //
  //   full      1,385,925 of 1,400,000   14,075 clear
  //   balanced  1,211,986 of 1,225,000   13,014 clear
  //   light       769,379 of   785,000   15,621 clear
  //
  // PR #599 (T-0432, four roofs, +2,174) and PR #601 (T-0431) had been parked as
  // breaches against a `balanced` of 1,210,000 — a figure this table left behind
  // on 2026-08-24 — and against a dev with 1,566 of room. They fit today with
  // ~10,840 to spare. THE RAISE IS NOT TAKEN FOR THEM. A ceiling raised to carry
  // a record that already fits is the exact fault the entries above forbid.
  //
  // WHAT IT IS SPENT ON. PR #432 (T-0219, the heightfield south to Madison) is
  // the one parcel that genuinely does not fit. Its tree was re-measured today
  // and reproduces its own PR's figures to the triangle, so the parcel cost is
  // isolated against the dev it was cut from and applied to the dev it would
  // land on:
  //
  //   tier      dev now    + parcel   would read   old ceiling   over by
  //   full     1,385,925    56,016     1,441,941    1,400,000     41,941
  //   balanced 1,211,986    51,208     1,263,194    1,225,000     38,194
  //   light      769,379    39,830       809,209      785,000     24,209
  //
  // WHERE THE NEW NUMBERS COME FROM, so they are a principle and not "enough for
  // me": each tier keeps AT LEAST THE ABSOLUTE HEADROOM IT CARRIES TODAY over
  // the measured worst stand with #432 in, rounded up to the nearest 5,000. The
  // ladder therefore keeps its shape; no tier is given proportionally more room
  // than it has now, and nothing was chosen to fit one record.
  //
  //   full      1,400,000 -> 1,460,000   18,059 clear (1.24 %)
  //   balanced  1,225,000 -> 1,280,000   16,806 clear (1.31 %)
  //   light       785,000 ->   825,000   15,791 clear (1.91 %)
  //
  // `light` IS RAISED, AND THAT BREAKS A STANDING CONSTRAINT THIS TABLE HAS KEPT
  // THROUGH EVERY PREVIOUS RE-BUDGET — "the floor a weak machine boots into is
  // not spent here". It is broken deliberately and only on the owner's second,
  // specific answer after being told that is what it would cost. A weak machine
  // now boots into a tier that draws 809,209 where it drew 769,379. Whoever
  // takes the retirement below should take `light` back FIRST.
  //
  // THE RETIREMENT IS T-0672, and it is written to be one that can actually fall
  // due. T-0229's expiry was blocked behind a flora ticket and would never have
  // come due (T-0231 records exactly that), so T-0672 depends on nothing: it
  // re-measures after #432 lands and lowers each tier back to the measured worst
  // plus the headroom carried here. `tools/measure_research_spend.py --tighten`
  // is the same shape one layer over — reclaiming slack is free and needs no
  // argument, only spending it does.
  //
  // NOT YET VERIFIED ON THE MERGED TREE, and this is the one weakness in the
  // numbers. #432 has been conflicted since 2026-08-28 and its re-derive needs
  // Blender, which the session that took this ruling did not have. The parcel
  // cost above is a measured 2026-08-28 delta applied to today's dev, not a
  // reading of the merged tree. T-0672 re-measures the moment #432 is green, and
  // if the merged tree reads under these numbers they come DOWN to it.
  full:     { triangles: 1460000, shadowReachM: 240, furnitureCastsShadow: true,
              furnitureReachM: null },
  // RE-BUDGETED 2026-08-21, 800000 -> 900000, on the owner's ruling that a
  // ceiling is a number this project chose rather than a claim about 1835.
  // Four parcels landed the same day - the street edge, the lot-line fences,
  // the fenced ground and sixty-four wagons - and stacked they read 814,860
  // here where each alone had fitted. The old figure was set before any of
  // them existed and nothing re-measured it as the town filled in. `light`
  // is UNTOUCHED at 600000 and still passes: the tier a weak machine boots
  // into keeps its floor, and this raise is spent only by machines that
  // asked for the middle setting.
  //
  // RE-BUDGETED AGAIN 2026-08-24, 1210000 -> 1225000 (T-0098), and the entry
  // above asked for exactly this to be justified: "the next parcel that
  // breaches them is breaching a bar that means something." It measured what
  // the bar means before moving it, twice, at the release smoke's own worst
  // stand (Lake Street at Canal, east down the axis, desktop 1280x800):
  //
  //   dev alone, this parcel unmounted     1,209,926 of 1,210,000   PASS by 74
  //   dev plus a twelve-stem tree stand    1,213,446 of 1,210,000   FAIL by 3,446
  //
  // SEVENTY-FOUR TRIANGLES. That is a quarter of one tree, on a frame of 1.2
  // million. The bar had not been reached by a parcel that overspent it; it had
  // been reached, full stop, and the next VISIBLE parcel of any size at all was
  // going to fail it whatever it was - which is a fact about the ceiling and not
  // about the parcel that found it. `full` was measured in the same runs with
  // 16,852 (1.2 %) of headroom, so the ladder was not uniformly full: the middle
  // rung alone had been squeezed to nothing.
  //
  // WHERE 1,225,000 COMES FROM, so it is a principle and not "enough for me":
  // it gives `balanced` the same PROPORTIONAL headroom `full` carries today
  // (about 1 %) over the measured worst stand WITH this parcel in. The ladder
  // keeps its shape; nothing was chosen to fit one record.
  //
  // WHAT WAS NOT DONE, and both halves matter. `light` IS UNTOUCHED at 1050000
  // and reads 815,777 - 22 % under its own ceiling. The floor a weak machine
  // boots into is not spent here, which is the standing constraint on every
  // re-budget this table has taken. And this raise does NOT buy room for the
  // parcel after this one: it restores about 1 % and no more, and the trim that
  // would actually win the middle rung back is still T-0149 (the axial view) and
  // T-0147 (the ceilings that follow a trim down). A ceiling raised to carry one
  // record is not a ceiling anybody should spend twice.
  // SUPERSEDED 2026-08-27, and the re-budget above is DEFERRED rather than
  // dismissed: it was careful reasoning that later measurement overtook, twice.
  //
  //   (i)  It rests on `balanced` measuring 1,213,446 at the worst stand. dev
  //        measures 1,252,802 there today, so 1,225,000 no longer clears the
  //        breach it was raised to clear. It also rests on `full` carrying
  //        1.2 % headroom; `full` is now OVER, at 1,412,120 of 1,400,000. Both
  //        halves of the proportional-headroom argument have moved.
  //   (ii) T-0223 measured what actually occupies the frame, which nobody had:
  //        `trees` draws 360,926 triangles out of 181,900 it owns -- the whole
  //        layer twice -- because trees.js submits kilometre-wide quadrant
  //        meshes whole to a +/-240 m shadow box. 180,100 triangles, 14.4 % of
  //        the frame, cast nothing any pixel of the shadow map can hold.
  //
  // Re-basing a ceiling with that still in it budgets for work the renderer
  // should not be doing, and it would be the fifth raise. So the number stays
  // at 1,210,000 and the budget question lives entirely in T-0223, which orders
  // the trim first and the ceiling after. The tree stand this parcel adds ships
  // regardless; its own smoke leg is red on dev with or without it.
  // Raised with `full` above on 2026-08-27 and RETURNED WITH IT (T-0229): it
  // read 1,260,000 for a day, on a worst stand of 1,252,802 that measured
  // 1,083,932 once T-0223's cull landed. The reading, both viewports, is in the
  // block above `full` rather than written out twice.
  // T-0241 GIVES THIS RUNG A FURNITURE REACH, 800 m — the first trim `balanced`
  // has ever carried, and the whole reading is at `FURNITURE_REACH_BALANCED_M`
  // above. The ceiling was UNTOUCHED at 1,210,000 by that entry; what changed is
  // what the tier draws, which is the other way round from every entry above it.
  //
  // -- 2026-08-31 -- T-0098's RULING IS APPLIED HERE, SEVEN DAYS LATE --
  //
  // The re-budget to 1,225,000 recorded above on 2026-08-24, and repeated in
  // `docs/LIBERTIES.md`, was written into the comment and into the ledger and
  // NEVER INTO THE VALUE. `git log -S"triangles: 1225000"` on this file is
  // empty: the number has read 1,210,000 without interruption since before that
  // ruling was made. The 1,260,000 in the ledger's table is a different episode
  // — T-0229 raised it with `full` and returned it with `full` a day later, from
  // 1,260,000 and not from 1,225,000 — so T-0098's figure was never in force and
  // was never revoked. It is simply missing, and this applies it unchanged.
  //
  // What it unblocks, measured: PR #599 stood at 1,210,608 at the release
  // smoke's worst stand and failed by 608 against the un-applied number. It is
  // inside this one by 14,392, and so is #601's block. T-0098's own sizing still
  // holds — this gives `balanced` about the 1 % headroom `full` carries, and buys
  // no room for the parcel after these; T-0149 and T-0147 still own the trim
  // that would win the rung back.
  balanced: { triangles: 1280000, shadowReachM: 240, furnitureCastsShadow: true,
              furnitureReachM: FURNITURE_REACH_BALANCED_M },
  // -- T-0147, 2026-08-27 -- AND THE FLOOR IS WON BACK: 1,050,000 -> 785,000 --
  //
  // The third and last piece of T-0149, whose whole complaint is the sentence
  // near the top of this block: `light` carried MORE than `full` had promised
  // the day before, so the tier a weak machine boots into was not a floor
  // anybody could be promised. The trims that were supposed to earn it back
  // have all landed -- T-0150 (the derived furniture distance-culled at `light`
  // alone, 350 m), T-0146 (far chunks merged back into single draws), and
  // T-0223's timber cull, which arrived between them and gave more than either.
  //
  // MEASURED FIRST AND LOWERED SECOND, which is the entire reason this is a
  // separate ticket from the trims: a ceiling lowered in the same breath as the
  // trim that justified it is a ceiling nobody checked.
  // `tools/measure_detail_ceilings.mjs`, published mirror, T-0135's five
  // stands, BOTH release viewports, dev @ f7aca445:
  //
  //                    desktop 1280x800          mobile 390x780
  //   worst frame      703,610 at the forks      649,296 at Lake/Canal
  //   worst calls           76 at Lake+Market         69 at Lake+Market
  //
  // WHERE 785,000 COMES FROM, so it is a principle and not "enough for today".
  // It gives `light` the same PROPORTIONAL headroom over its own measured worst
  // stand that `full` carries over its: 1,400,000 against 1,252,879 is 11.7 %,
  // and 785,000 against 703,610 is 11.6 %. The ladder keeps its shape, and the
  // figure is a WORST-STAND number rather than a reference-stand one, which is
  // the rule this table has now been re-taught five times. (`full`'s figure is
  // the 1,400,000 immediately above -- T-0229 landed its restoration while this
  // was being gated, so the two numbers this compares are both live.)
  //
  // WHAT IT RESTORES, said as plainly as the thing it answers: 785,000 is
  // 21.5 % BELOW the 1,000,000 `full` promised before 2026-08-22. The bottom
  // rung is a fifth cheaper than the old top rung again, so it is a floor and
  // not merely the cheapest of three expensive settings.
  //
  // AND THE DRAW-CALL PROMISE COMES BACK AS A COUNT, in
  // `tools/smoke_renderer.mjs`, where the check that used to hold `light` inside
  // 80 calls was weakened to a ratio on 2026-08-22 and its own comment asked
  // this ticket to turn it back. 80 is the number this project chose before any
  // of the 2026-08 content landed, not one tuned to today's 76 -- four calls of
  // room, and the next chunked layer that reaches it is reaching a bar that
  // means something. It is worth naming how thin that is: this branch read 75
  // before T-0194's hitching posts merged and 76 after, so one ordinary visible
  // parcel spent a quarter of the margin. That is the bar working, and the
  // answer when it goes red is a trim or an argued re-budget -- never a
  // weakening of the assertion, which is the move T-0223 forbade by name.
  //
  // WHAT THIS DELIBERATELY DOES NOT DO. `full` and `balanced` are untouched:
  // taking T-0229's raise back out was T-0229's own change with its own
  // reading, and this one does not reach across it. Nothing in the renderer
  // moves -- no geometry, no reach, no shadow tier, no cull. This is only the
  // ceiling following a trim DOWN, which T-0149 named as the strongest evidence
  // that a trim worked.
  light:    { triangles: 825000, shadowReachM: 120, furnitureCastsShadow: false,
              furnitureReachM: FURNITURE_REACH_LIGHT_M },
};
const DETAIL_ORDER = ['full', 'balanced', 'light'];
/**
 * THE DRAW-CALL BUDGET, RAISED FROM 80 TO 120 ON 2026-08-21 — a conscious
 * re-budget, written down here where the number is set, and never a silent one.
 *
 * THE OWNER'S RULING, verbatim: *"ok to raise the draw call budget, if you need
 * to make that a user friendly option in settings because it wont work on some
 * machines but will on others/most then that is ok"* — and immediately after,
 * *"or just raise the budget?"*. No new setting was built: the scene-detail
 * control below IS the user-facing option, and `light` remains the floor a weak
 * machine has to hold, inside its own unchanged 600,000-triangle ceiling.
 *
 * WHY 80 STOPPED MEANING WHAT IT MEANT. It was set when every derived layer was
 * ONE mesh — one fence mesh for the whole town, one plank-walk mesh, one yard
 * mesh — and a draw call was a thing to be hoarded. T-0115 measured what that
 * cost: a mesh spanning Chicago has a bounding sphere no frustum can cull, so
 * 33,166 triangles of fence were drawn in every frame including the fences
 * behind the camera. T-0067, T-0119 and T-0069 all took the same remedy and
 * chunked their layers, which DELIBERATELY converts triangles into draw calls —
 * and the sun's own pass draws every chunk inside its ±240 m box a second time,
 * so a chunk costs two. The triangle ceilings are the tiers a visitor chooses
 * between and they are unchanged; the call count is the price of the culling
 * that keeps those ceilings reachable, and holding it at 80 would mean giving
 * back the culling.
 *
 * MEASURED, at the release gate's own stand (`frame('sauganash_hotel', 26)`),
 * desktop, published mirror: 65 calls before T-0069's street edge and **78**
 * after it — inside the old 80, and with nothing left. That is the number this
 * raise is against: not a parcel that overran, but a budget with two calls of
 * headroom in a town that is still being built. 120 is half again the measured
 * worst, which is the same order of margin the triangle ceilings carry.
 *
 * WHAT WOULD MAKE IT SMALLER AGAIN, costed and not done here (T-0115's ledger,
 * T-0127): a plank walk lies 11 cm proud of the ground and its own shadow is
 * about 4 cm wide at noon. If the ground-hugging furniture stopped casting into
 * the shadow map while the standing furniture kept casting, the frontage layer's
 * six shadow-pass calls at this stand would go for nothing a visitor can see.
 * That needs a per-mesh opt-out in `applyShadowTier` and a smoke check that
 * counts the exempt meshes rather than assuming every furniture mesh casts.
 *
 * RECONCILED 2026-08-21, and the number stands at 120. Two parcels raised this
 * ceiling the same afternoon, each measuring only itself against dev: the street
 * edge (T-0069) read 78 calls and chose 120; the lot-line fences (T-0068) read 79
 * and chose 96. Neither had seen the other. Merged they stack — dev's 65 plus
 * roughly thirteen for the walks and fourteen for the fences — so 96 would have
 * been spent almost the moment both landed, which is how a ceiling comes to be
 * re-raised twice in a week. 120 is kept because it is the number with room in
 * it, and because the argument below is about what a ceiling is FOR, not about
 * the one parcel that happened to reach it first.
 */
// 120 -> 140 for the same reason and on the same day: the four parcels above
// read 121 calls together, one past a ceiling reconciled hours earlier from two
// parcels that had each measured only themselves. Chunking is what spends calls
// - it trades a draw call for the frustum's right to skip geometry - so the
// number climbs as layers learn to cull. 140 carries the measured 121 with room
// rather than the single call that would have to be re-argued tomorrow.
//
// T-0135, 2026-08-22 — AND 140 IS NOT MOVED EITHER, FOR THE REASON THE TABLE IN
// `DETAIL` ABOVE GIVES. Read at the release gate's new stand set rather than at
// the Sauganash alone, the worst frame is 200 calls at `full` down Lake Street
// from Canal, and 177 at `light` against a floor of 80 that has stood since
// before any layer was chunked. Every raise this ceiling has taken — 80 to 120
// to 140, all on 2026-08-21 — was argued against a camera that reads 121, so
// the honest thing to say is not "140 is too low by 60" but "nobody has ever
// budgeted this scene; they budgeted one view of it." Moving the number today
// would be the fourth raise in two days and the first one aimed at a reading
// taken specifically to show that raising to fit the reading is the bug. The
// gate is red at the worst stand on purpose. See T-0135.
// 140 -> 215 on the same ruling and the same measurement: the worst stand draws
// 200 calls at `full` where the reference stand drew 121. Chunking is what
// spends calls down a long street, and T-0149 is where that gets traded back.
const BUDGET = { drawCalls: 215, triangles: DETAIL.full.triangles };

/**
 * THE DERIVED FURNITURE — which layers `furnitureCastsShadow` governs, by the
 * name each one gives its own group.
 *
 * What they have in common is the thing that makes the rule defensible: every
 * one is small timber (or a small hull) built at load from a committed record
 * rather than baked, standing ON the town rather than being the town.
 * `structures`, `terrain`, `streets`, `trees` and `flora` are deliberately not
 * in this list — the first three are the reconstruction itself, and the last
 * two already give way through their own density.
 *
 * AND `signage` IS NOT IN IT EITHER, which is the one exception and was decided
 * by a measurement rather than by taste. A hanging board is the only furniture
 * in this town whose whole function is to be READ, from the street, at a few
 * metres — and the shadow it throws is what lifts it off the wall it is bolted
 * to. Dropping it from the shadow map cost exactly that: with the boards no
 * longer casting, hiding the whole signage layer moved the release gate's own
 * 12-cell signature at the Tremont's footway by mean 0.28 against its 0.30 bar,
 * where the same measurement reads 0.72 with the shadow in — so the shadow was
 * most of what the board was contributing to the frame. Keeping the boards
 * casting cost 1,380 triangles of this tier's 84,912-triangle saving: 1.6 % of
 * the saving, 0.2 % of the tier, for the only piece of furniture the visitor is
 * meant to look directly at. It costs 1,106 since T-0066 gave the signs their
 * names — a painted band is two triangles where a bracket board is sixty, and
 * the lettering itself is a texture atlas rather than geometry.
 */
const FURNITURE_LAYERS = ['enclosures', 'yard', 'frontage', 'wharves', 'boats', 'wells'];

/**
 * THE NEAR PLANE, AND WHY IT MOVES WITH ALTITUDE — ROADMAP R-BUG1.
 *
 * The owner reported the river's edge flickering when flying, and it is the
 * depth buffer running out of numbers. A perspective depth buffer spends its
 * precision near the camera: the smallest depth difference it can tell apart at
 * a distance z is about z² / (near · 2^bits). At the fixed 0.1 m near this
 * camera used to carry, two surfaces 350 m away had to be **10 cm** apart in
 * depth before the buffer could say which was in front — and the river's edge
 * is the one place in this scene where two surfaces are exactly co-planar by
 * design (`terrain.js`: the bank line IS where the ground crosses y = 0, so the
 * waterline can never drift out of step with the traced river). Inside that
 * band the winner is decided by rounding, and a camera that moves two
 * millimetres re-rolls it. That is the shimmer.
 *
 * Moving the near plane out with altitude fixes the CAUSE rather than picking a
 * winner. The alternative — a `polygonOffset` on the water — would settle the
 * tie by biasing the water toward the camera, and at 350 m one depth step is
 * ~10 cm of ground: the drawn waterline would climb the bank by up to that
 * much, which breaks the invariant the design exists to guarantee. Precision
 * costs nothing and moves no edge.
 *
 * `min` is the walking value and is unchanged: `altitude` is the eye's height
 * above the ground under it and is 0 on foot, so a walker gets exactly the
 * camera they had before. `divisor` keeps the near plane at a twenty-fifth of
 * the way to the ground — two orders inside anything the visitor could fly
 * close to — and `max` caps it so that a low pass beside a building cannot clip
 * its wall. `step` quantises the value so the projection matrix is rebuilt on a
 * change worth having rather than every frame.
 */
const NEAR = { min: 0.1, max: 8, divisor: 25, step: 0.05 };

/** The visitor's stored choice, read straight from the HUD's own settings blob so
 *  the two cannot disagree about which level is selected. Returns '' when they
 *  have never chosen, which is what lets the device guess stand. */
function readDetailPreference() {
  try {
    const raw = window.localStorage.getItem('chicago4d.settings');
    const level = raw ? JSON.parse(raw).detail : '';
    return DETAIL[level] ? level : '';
  } catch {
    return '';
  }
}

const params = new URLSearchParams(location.search);
const YEAR = (params.get('year') || '1835').replace(/[^0-9a-z_-]/gi, '');
const DEBUG = params.get('debug') === '1';

const canvas = document.getElementById('view');
const gate = document.getElementById('gate');
const gateBtn = document.getElementById('gate-btn');
const gateSub = document.getElementById('gate-sub');
const gateBar = document.getElementById('gate-bar');

/**
 * Loading progress, driven by the boot's REAL stages rather than by a timer.
 * A timer-driven bar tells a visitor nothing except that time is passing, which
 * they already know; this one only moves when something has actually finished,
 * so a bar that stops IS the diagnosis.
 */
function progress(pct, label) {
  if (gateSub && label) gateSub.textContent = label;
  if (!gateBar) return;
  const fill = gateBar.firstElementChild;
  if (fill) fill.style.width = `${Math.max(0, Math.min(100, pct))}%`;
  gateBar.setAttribute('aria-valuenow', String(Math.round(pct)));
  if (pct >= 100) gateBar.classList.add('done');
}
const hudRoot = document.getElementById('hud');
const popupRoot = document.getElementById('popup');

const problems = [];

/** The harness handle. Populated as boot proceeds so a failure is still legible. */
const api = {
  version: VERSION,
  three: THREE.REVISION,
  year: YEAR,
  ready: false,
  error: null,
  scene: null,
  datum: null,
  registry: new Map(),
  player: { e: 0, n: 0, y: 0, bearingDeg: 0, pitchDeg: 0, speed: 0, moving: false,
            altitude: 0, flying: false },
  problems,
  budget: BUDGET,
  // The town's two City ladders (T-0036/T-1292). Null until Evidence first opens,
  // and null forever if it could not be read — the smoke asserts the displayed
  // figures against this, so a silent failure reads as one.
  census: null,
  // T-1126: the town's roll call — indexed, expected to draw, and actually
  // standing, with every absentee named. Null until the buildings are batched.
  roll: null,
};
window.__chicago4d = api;
let bootStorage;
try { bootStorage = window.localStorage; } catch { /* private mode */ }
const bootController = createBoot({
  device: prefersTouch() ? 'mobile' : 'desktop',
  detail: DETAIL[readDetailPreference()] ? readDetailPreference() : (prefersTouch() ? 'light' : 'full'),
  build: document.getElementById('gate-build')?.textContent || VERSION,
  storage: bootStorage, problems, present: progress,
});
api.boot = bootController;
const bootCheckpoint = createCheckpoint();

boot().catch((err) => {
  const active = bootController.phases.find(phase => phase.essential && phase.startedAt !== null && phase.endedAt === null);
  bootController.fail(active?.id || 'scene', err);
  api.error = String(err?.message || err);
  problems.push(`boot: ${api.error}`);
  if (gateSub) gateSub.textContent = `Could not load the scene — ${api.error}`;
  if (gateBtn) gateBtn.textContent = 'Failed to load';
  console.error('[4D Chicago] boot failed', err);
});

async function boot() {
  bootController.start('scene');
  await yieldToPaint();
  const bases = resolveBases();
  const coarse = prefersTouch();

  /**
   * MULTISAMPLING, ON EVERY DEVICE INCLUDING A PHONE (T-0157).
   *
   * This read `antialias: !coarse` from Milestone 0 — the first commit of this
   * renderer, before there was a town to look at — so every touch device drew
   * the whole reconstruction with no multisampling at all. Nobody had ever
   * measured what that costs a phone: T-0013 established that all 627
   * interior-flickering pixels at `from_above` are edges and that only sample
   * density touches them, but every one of its readings was taken at 1280×800
   * on the DESKTOP boot, where MSAA was already absorbing most of it.
   *
   * `tools/measure_phone_aa.mjs` measures the phone, at 390×780 in a context
   * with `hasTouch` — which the release gate uses and which `TIE_VIEWPORT=mobile`
   * does not, so the older instrument had been booting the desktop renderer in a
   * narrow window. Published mirror, 2 mm nudge, shadow map off, control and
   * return-to-pose both 0 px:
   *
   *              flicker px      HARD FLIPS (a pixel that moved ≥ 64 of 255)
   *   from_above   1056 → 2482        25 → 0
   *   lake_market  4843 → 7310       124 → 0
   *
   * READ THE SECOND COLUMN, AND NOTE THAT THE FIRST ONE ARGUES THE OTHER WAY.
   * The flicker COUNT — the number T-0013 and three boxes of ROADMAP quote —
   * goes UP by 135 % aerial and 51 % at eye height when MSAA is switched on,
   * because a partial resample touches more pixels than a whole flip does. A run
   * that had measured only the count would have refused this. What actually
   * happens is that the SEVERITY collapses: the worst per-pixel movement falls
   * 105 → 28 aerial and 140 → 37 at Lake and Market, the mean 15.6 → 6.8 and
   * 14.8 → 6.4, and every one of the 149 pixels that were swapping surface
   * outright stops doing it. That is precisely the difference between an edge
   * that crawls and an edge that is resolved.
   *
   * WHAT IT COSTS, AND THE HONEST LIMIT OF THAT FIGURE. Timed over the ten scene
   * anchors the release gate walks, clock held, A/B/A: **+56 % of a frame**
   * (24,457 → 43,283 ms summed, against a mean-of-A baseline), with the runner
   * itself drifting +26 % between its two A passes — so the true reading is
   * "roughly half a frame again", not a digit. It is measured through ANGLE's
   * SwiftShader, a SOFTWARE rasteriser, which resolves every sample on the CPU
   * with no tile memory: that is the harshest possible witness for this change
   * and the figure is an UPPER bound. **The cost on real phone silicon was not
   * measured and is not claimed.**
   *
   * The floor is untouched and the escape hatch already ships. A phone still
   * boots into the `light` scene-detail tier, unchanged; and Render quality in
   * Settings drops the pixel ratio to 1, which cuts the multisampled pixel count
   * by 56 % — measured at 4 stations rather than asserted, see STATUS.md.
   */
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    powerPreference: 'high-performance',
    stencil: false,
  });
  /**
   * The boot-time ratio. Note that this is superseded a few hundred lines below
   * by `renderer.setPixelRatio(Math.min(dpr, hud.settings.quality))` once the
   * visitor's stored settings are read, and the shipped default of `quality` is
   * **1.5 on both platforms** — so the `: 2` here reaches a fresh visitor's
   * screen for the handful of frames before the HUD mounts and nowhere else.
   * T-0157's premise held that a phone was capped at 1.5 "rather than 2"; what
   * the renderer actually reports is 1.5 on a phone at dpr 2 and 1.0 on a
   * desktop at dpr 1, which is the phone supersampling MORE than the desktop.
   */
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, coarse ? 1.5 : 2));

  const scene3d = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(62, 1, NEAR.min, 3000);

  const loaded = await loadScene(YEAR, bases, {
    onProgress: (done, total) => bootController.progress('scene', done, total),
  });
  bootController.end('scene');
  bootController.start('terrain');
  await yieldToPaint();
  problems.push(...loaded.problems);
  api.scene = loaded.scene;
  api.datum = loaded.datum;
  api.registry = loaded.registry;
  // The survey junctions the Go-to menu offers, from the same list the menu is
  // built from. Exposed because the smoke asserted the menu's junction count
  // against a LITERAL 4, so committing a fifth control point failed a gate that
  // was measuring nothing: the intersections are compiled into the sidecar index
  // from data/traces/street_control.json on every check, and the count is
  // therefore data, not a constant. Same shape as `scene.anchors`, which the
  // next assertion in that block already reads (T-0245).
  api.intersections = loaded.index?.intersections ?? [];

  const world = createWorld({
    renderer, scene: scene3d, sceneJson: loaded.scene, datum: loaded.datum, lowSpec: coarse,
  });

  const confidence = createConfidenceView();

  // The ground, the river, and the heightfield the walker stands on, all from
  // the scene's terrain epoch. Awaited: everything after this asks it how high
  // the ground is, and a flat answer would place every building at the datum.
  const terrain = await createTerrain({
    dataBase: bases.dataBase,
    assetBase: bases.assetBase,
    epochId: loaded.scene.terrain_epoch,
    confidence,
    problems,
  });
  if (!terrain.loaded) throw new Error('Terrain heightfield did not load');
  scene3d.add(terrain.group);
  // T-1154 — the ground's reach, set from the fog the world just made rather
  // than from a literal here, so a scene that changes its haze moves the reach
  // with it and the two can never drift apart. See terrain.js hazeReachM().
  terrain.setGroundReach(hazeReachM(scene3d.fog?.density ?? 0));
  bootController.end('terrain');
  bootController.start('buildings', loaded.registry.size);
  await yieldToPaint();
  const buildings = await createBuildings({ registry: loaded.registry, confidence, terrain,
    checkpoint: bootCheckpoint,
    onProgress: (done, total) => bootController.progress('buildings', done, total),
  });
  problems.push(...buildings.problems);
  scene3d.add(buildings.group);
  bootController.end('buildings');
  bootController.start('ground');
  await yieldToPaint();

  /**
   * T-1126 — FURNITURE FOLLOWS ITS HOST, and the failure is SAID OUT LOUD.
   *
   * Everything a business hung on its wall or stood on its footway is derived
   * from the structure record, not from the structure's geometry, so when a GLB
   * failed to fetch the board and the crates went on drawing and the building
   * did not. The owner found exactly that on Dearborn Street: J. BATES, JR. /
   * AUCTIONEER floating at head height over a lot-line fence with two crates in
   * the grass beside it and no auction room between them. A reload had it back,
   * which is what says the record is sound and the SCENE is what misbehaved.
   *
   * Two things follow, and both are here rather than in the layers because only
   * this file knows both halves:
   *
   *   1. The layers below take `hostMissing` and take their furniture down with
   *      the building. A failed load then degrades into an ABSENCE — an empty
   *      lot, which is honest — instead of into a false scene, which is not.
   *   2. The shortfall is reported UNCONDITIONALLY, at error level, naming every
   *      structure. Everything this renderer knew about its own failures was
   *      already in `problems`, and `problems` is printed behind `?debug=1` —
   *      so a visitor, and the owner, got a finished-looking walk and silence.
   *      A load failure nobody is told about cannot be measured, and a rate
   *      nobody can measure is indistinguishable from an anomaly.
   */
  const hostMissing = (id) => (!!id && buildings.missing.has(id));
  api.roll = buildings.roll;
  if (buildings.roll.missing.length) {
    console.error(`[4D Chicago] ${buildings.roll.standing} of ${buildings.roll.expected} `
      + 'structures drew; the walk is SHORT of the town it is claiming. Missing: '
      + buildings.roll.missing.join(', '));
  }

  const footprints = footprintsFrom(loaded.registry);
  // The bridge decks: a walkable surface the heightfield does not carry — the
  // wall you are kept out of and the deck you stand on are the same polygon read
  // two ways, so both come off the same footprints. T-0001. They are no longer
  // the only ones: the street edge's boards and, since T-0058, the wharf decks
  // and their boarding stairs join this same array once their own layers have
  // drawn them and know how high they stood them. The walker holds it BY
  // REFERENCE and reads whatever is in it.
  const decks = decksFrom(loaded.registry);
  const spawn = anchorFor(loaded.scene, params.get('anchor')) ?? loaded.scene.spawn ?? {};
  const walker = createWalker({ camera, terrain, footprints, decks, spawn });
  walker.apply();

  // The dated street layer is a skin on the heightfield, never a replacement
  // for it.  Mount it before vegetation so the travelled strips can clear only
  // the plants that would otherwise grow through the visible wagon tracks.
  const streets = createStreets({
    terrain,
    records: loaded.index?.streets ?? [],
    confidence,
  });
  scene3d.add(streets.group);

  // WHICH DETAIL LEVEL, resolved here rather than beside the vegetation because
  // the fence layer is the first thing that needs it: a pale is 10 triangles at
  // `full` and 4 at `light` (T-0067), so the level has to be known before the
  // first fence is built. A phone starts at `light` and a desktop at `full`; the
  // visitor's own choice, once made, outranks the guess and is what
  // `hud.settings.detail` carries.
  let detailLevel = DETAIL[readDetailPreference()] ? readDetailPreference()
    : (coarse ? 'light' : 'full');
  const detailOpts = () => ({ detail: detailLevel });

  // The town's fence lines — yards, pens, garden pickets. An enclosure takes a
  // PERIMETER rather than a footprint and is roofless, which is why it is not a
  // structure record and carries no GLB: docs/LIBERTIES.md L10 and L60 have both
  // been waiting on exactly that shape, and this is the half of it that needs no
  // bake. Mounted after the streets so a frontage fence is drawn against the
  // travelled way it stands on, and before the vegetation because the ground
  // inside one now decides what may grow there — see the fenced ground below.
  const enclosures = await createEnclosures({
    dataBase: bases.dataBase, terrain, confidence, problems, ...detailOpts(),
  });
  scene3d.add(enclosures.group);
  api.enclosures = enclosures;

  /**
   * THE GROUND INSIDE THOSE FENCES (T-0067). The owner: *"everplace that is
   * fenced in would have a different ground, the wagon yard would probably be
   * dirty dusty ground and fences around properties inside the fence would not
   * be wild prairie but curated lawn and garden or animal pens."* Three of the
   * four enclosure records said the same thing about themselves, in their own
   * `ground` blocks, with `geometry: "absent"`.
   *
   * It is its own layer and its own scene child rather than a second mesh inside
   * `enclosures` for two reasons that are both about policy rather than tidiness:
   * a ground treatment casts no shadow and must not be swept into
   * FURNITURE_LAYERS' traverse, and hiding the FENCE (which several gates do) must
   * not take the ground with it. It takes the enclosure records straight off the
   * layer above rather than re-fetching them.
   */
  const yards = createFencedGround({
    records: enclosures.records, terrain, confidence, problems,
  });
  scene3d.add(yards.group);
  api.yards = yards;

  // The boards the businesses hung out over the footway. Like a fence, a
  // signboard is derived geometry rather than baked geometry — a plank on a
  // bracket hanging off a wall the GLBs already draw — so it needs no bake
  // either (T-0039). Mounted after the buildings it hangs on, and its height is
  // measured from the same wall base `buildings.js` anchors them at.
  const signage = await createSignage({
    dataBase: bases.dataBase, terrain, confidence, problems, hostMissing,
  });
  scene3d.add(signage.group);
  api.signage = signage;

  // The goods a working town left standing on its own ground — barrels and
  // cases on the footway at the taverns and the stores, and one wagon in the
  // yard a source calls a wagon yard (T-0040). Derived geometry like the fences
  // and the boards, so it needs no bake either. Mounted AFTER the signage
  // because the two are derived from the same wall and deliberately share it:
  // the board hangs 1.7 m one side of the facade's centre and the goods pile
  // from the other end. Unlike a board, a barrel stands on the TERRAIN rather
  // than on the building's wall base — it is resting on the ground it is on.
  const yard = await createYardGoods({
    dataBase: bases.dataBase, terrain, confidence, problems, hostMissing,
  });
  scene3d.add(yard.group);
  api.yard = yard;

  // The frontage works — the plank walks along a building's street walls, the
  // board crossing over the road and the named board on its post at the corner
  // (T-0082). Derived geometry like the fences, the boards and the goods, so it
  // needs no bake — but it is the first layer derived from a building AND a
  // street at once: where a walk may lie is decided by the travelled track's own
  // half-width out of data/streets/1835.json. Mounted after the yard because the
  // two divide one building's ground between them — the yard layer owns what
  // stands on its own lot and this owns what lies in the street outside it.
  const frontage = await createFrontage({
    dataBase: bases.dataBase, terrain, confidence, problems, hostMissing,
  });
  scene3d.add(frontage.group);
  api.frontage = frontage;
  /**
   * A walk that RIDES a committed deck registers its planks as a surface the
   * walker stands on (T-0119): the river walk's crossing footway lies over the
   * State slough's water at the mouth, where the terrain answers with the
   * wading barrier and only a deck may carry a visitor. The walker holds
   * `decks` by reference, so appending here is enough — and the planting
   * composition below picks the same rectangles up with the rest of `decks`.
   */
  for (const d of frontage.walkableDecks ?? []) decks.push(d);

  // The river docks at the two forwarding warehouses whose own records state
  // one (T-0041). Derived geometry like the fences, the boards and the goods, so
  // it needs no bake — but it is the first of these layers that stands OVER THE
  // WATER, and that is where its one hard rule comes from: the deck top is the
  // terrain's own height at the landward edge and each crib bent is stepped down
  // to the bed under it, so nothing here floats and nothing is drawn on a number
  // authored beside the mesh instead of taken from it. Mounted after the yard
  // for reading order; the two never touch, because the goods stand on the
  // town's trading frontages and the docks are out on the bank.
  const wharves = await createWharves({
    dataBase: bases.dataBase, terrain, confidence, problems,
  });
  scene3d.add(wharves.group);
  api.wharves = wharves;

  // The boats on the river (T-0063) — the owner's ask, verbatim: "you can add
  // boats correct for the era! they would exist." Derived at load like the
  // docks, but AUTHORED rather than ruled: no rule can derive where a moored
  // schooner lay, so data/boats/ states each hull and docs/LIBERTIES.md L146
  // claims the invention. An afloat hull rides the water plane at its own
  // draft and a beached one sits on the terrain; the layer refuses a boat its
  // own water cannot carry. Mounted after the wharves for reading order — the
  // two share the river and deliberately never touch: the wharf record draws
  // no vessel at its decks, and the boats ride the open reaches.
  const boats = await createBoats({
    dataBase: bases.dataBase, terrain, confidence, problems,
  });
  scene3d.add(boats.group);
  api.boats = boats;

  // The fort's well (T-0887) — the one well head this project can place to a
  // coordinate, drawn renderer-side for the reason its layer's header gives at
  // length: there is no well archetype, the nearest builds a roofed shed, and a
  // structure record with no buildable form does not validate, so until this
  // layer existed the measurement had nowhere to live at all. It mints no wells
  // — T-0592's refusal of a well CLASS for the town stands, and `wells.js`
  // enforces it by refusing any well a source does not PLACE. The curb is
  // invented and claimed at docs/LIBERTIES.md L232; nothing else is drawn.
  const wells = await createWells({
    dataBase: bases.dataBase, terrain, confidence, problems,
  });
  scene3d.add(wells.group);
  api.wells = wells;

  /**
   * What the PLANTERS treat as built ground: the buildings' footprints plus the
   * wharf decks. A deck is a floor, and a forb growing up through the planks
   * reads as a hole in the model. Kept as its own array rather than pushed into
   * `footprints`, which the walker holds by reference and the picker resolves by
   * structure id — a second polygon under a building's id would answer for the
   * building itself.
   */
  const planting = footprints.concat(
    wharves.keepOut, boats.keepOut, wells.keepOut,
    // The plank walks and crossings (T-0085/T-0124): a sidewalk is as much a
    // floor as a wharf deck, and the sward was rooting straight through it.
    frontage.keepOut,
    // And the walkable decks the registry itself carries (the bridges, the
    // slough crossing): their polygons already exist for the walker; the
    // planting layer now refuses them too, so nothing grows up between the
    // planks of a bridge deck either.
    decks,
  );

  // …AND THE WHARF PLANKS BECOME FLOORS — after `planting` has been taken and
  // not before. `decks` is the array the walker holds by reference, so a push
  // here reaches it; but the planters already have these same rectangles out of
  // `wharves.keepOut` above, and pushing earlier would hand them each one twice.
  // The layer publishes them rather than a record because a wharf has no
  // structure record to carry `placement.walk_surface_m`, and the height is the
  // one that layer drew the slab at (T-0058; see the header of `wharves.js`).
  decks.push(...wharves.decks);
  bootController.end('ground');
  bootController.start('flora');
  await yieldToPaint();

  // ---- vegetation ------------------------------------------------------- //
  // Awaited, like the terrain and for the same reason: the sward is what the
  // ground looks like from standing height, and a walkthrough that opened its
  // gate onto a bare plane and grew a prairie a second later would be showing
  // the visitor a loading state and calling it 1835. Missing records degrade to
  // NOTHING planted plus a recorded problem — never to an invented community.
  // (`detailLevel` is resolved much earlier — up beside the fences, which need
  // it to know what a pale costs.)
  /**
   * Vertical pixels per radian of field, for the horizon band — the one layer
   * whose correctness is measured in pixels, because it draws an angular
   * silhouette and a crown that subtends less than one cannot be textured, only
   * deleted. In CSS pixels, which is what the release viewports (390×780 and
   * 1280×800) are stated in; the device ratio would make the same frame answer
   * differently on a phone for no reason the eye can see.
   */
  const _size = new THREE.Vector2();
  const pixelsPerRadian = () => {
    renderer.getSize(_size);
    return _size.y / (camera.fov * Math.PI / 180);
  };
  BUDGET.triangles = DETAIL[detailLevel].triangles;

  /**
   * T-0115 — the half of a detail level that is the SUN rather than the town.
   *
   * Separate from `applyDetail` below because it is instant and reversible:
   * nothing is rebuilt, no record is re-read, and switching back restores the
   * frame exactly. It is applied here at boot as well as on every change, so a
   * phone — which starts at `light` without anybody touching the control —
   * boots into the same rig a desktop gets by choosing it.
   */
  function applyShadowTier(level) {
    const want = DETAIL[level] ?? DETAIL.full;
    world.setShadowRig(want.shadowReachM);
    const casts = want.furnitureCastsShadow !== false;
    for (const name of FURNITURE_LAYERS) {
      const group = scene3d.getObjectByName(name);
      // A layer that drew nothing (a record that failed to load, a fence whose
      // every post stood in water) simply has no group, and that is not an
      // error here — the problem is already recorded where it happened.
      if (!group) continue;
      // T-0127 — THE PER-MESH OPT-OUT T-0115'S LEDGER COSTED, and it is a
      // property of the MESH rather than of the layer because within one layer
      // the two halves differ: `frontage.js` marks the plank-walk and board-
      // crossing chunks `groundHugging` and leaves the street-lining fences on
      // their own meshes without it. A walk lies 0.11 m proud of the ground and
      // its own cast shadow is about 0.04 m wide at noon on 1 July, so drawing
      // 2.9 km of boards into the shadow map buys nothing a visitor can see and
      // costs their whole triangle count and one draw call per chunk, at the two
      // tiers that cast at all. The fences (1.37 m, about half a metre of real
      // shadow along the walk they stand behind) keep casting. `light` casts no
      // furniture at all, so nothing here changes it.
      group.traverse((o) => {
        if (!o.isMesh) return;
        // A merged far batch (T-0146) never casts: it is only ever drawn for a
        // cluster every part of which is beyond 340 m, which is outside the
        // sun's ±240 m box whatever the bearing, so its members were casting
        // nothing either. The shadow map reads the same with the merge on.
        o.castShadow = casts && !o.userData.groundHugging && !o.userData.farMerged;
      });
    }
    return { reachM: want.shadowReachM, furnitureCastsShadow: casts };
  }
  applyShadowTier(detailLevel);

  /**
   * T-0150 — THE FURNITURE'S REACH: how far down a long street the derived
   * furniture is drawn at all.
   *
   * The second half of what a scene-detail level does to the furniture, and the
   * first half that is about DISTANCE rather than about the sun. T-0135 walked
   * five named stands instead of one and found the town far over every ceiling
   * at the two axial views — Lake Street east from Canal, and the forks from
   * Wolf Point — because a long open sightline is exactly where the 2026-08-21
   * chunking cannot help: nothing is behind the camera, so no chunk is skipped
   * and every one of them is a draw call. The owner raised the ceilings to
   * carry it and opened T-0149 to win the floor back by TRIMMING that view; this
   * is the first of its three pieces.
   *
   * WHAT IS TRIMMED, AND WHY IT IS THE FURNITURE. `FURNITURE_LAYERS` is already
   * the set this project has argued is small timber standing ON the town rather
   * than being the town — the same set whose shadows `light` gives up. A fence
   * pale is 1.2 m of silhouette, and this camera is 62 degrees over 800 CSS
   * pixels, so it subtends 739 · 1.2 / d pixels: about 9 at 100 m, 4.4 at 200 m
   * and 3.0 at 300 m. Beyond the reach set below it is drawn at a scale where
   * the geometry has nothing left to say and the draw call is the whole cost.
   *
   * WHAT IS NOT TRIMMED, and each for its own reason. `structures`, `terrain`,
   * `streets` and the woody layer are the reconstruction itself and are never
   * distance-culled here. `signage` is out for the reason it is out of the
   * shadow policy — a board exists to be read — and it is a rounding error in
   * this frame besides. `flora` already has its own falloff. And the reach is
   * `null` at `full` and `balanced`: this is the bottom rung buying its floor
   * back, not a cheapening of the tier a visitor chose deliberately.
   *
   * IT IS A RENDERING DECISION AND NOT A CLAIM, which is the test everything in
   * this block has to pass. Nothing is moved, nothing is re-graded, nothing is
   * un-built: every fence stands exactly where its record puts it, is drawn
   * exactly as it is drawn the moment you walk toward it, and the confidence
   * view, the census and the cards all read the layer whole. What changes is
   * only whether a mesh whose members are three pixels tall is submitted.
   *
   * The cull is per CHUNK, which is what makes it worth having: the layers were
   * chunked in August 2026 so the frustum could skip what is behind you, and a
   * chunk is therefore already the unit that can be dropped without splitting a
   * fence run in half. A chunk is kept while any part of its bounding sphere is
   * inside the reach, so the boundary falls beyond the far edge of what is drawn
   * rather than through it.
   */
  const furniture = { reachM: null, spheres: [], drawn: 0, culled: 0 };
  /** Re-read the furniture meshes and bank each one's WORLD bounding sphere.
   *  Called wherever a furniture layer may have been rebuilt — the fence layer
   *  rebuilds its meshes in place when the level changes (T-0067), and a stale
   *  list would cull spheres belonging to geometry that no longer exists. */
  function collectFurniture() {
    furniture.spheres.length = 0;
    for (const name of FURNITURE_LAYERS) {
      const group = scene3d.getObjectByName(name);
      if (!group) continue;
      group.updateWorldMatrix(true, true);
      group.traverse((o) => {
        if (!o.isMesh || !o.geometry) return;
        // The merged far batches (T-0146) are drawn FROM these chunks, not
        // alongside them: banking one would have the reach culling a batch and
        // the batch drawing the chunks the reach had just culled.
        if (o.userData.farMerged) return;
        if (!o.geometry.boundingSphere) o.geometry.computeBoundingSphere();
        const sph = o.geometry.boundingSphere?.clone();
        if (!sph) return;
        sph.applyMatrix4(o.matrixWorld);
        furniture.spheres.push({ mesh: o, c: sph.center, r: sph.radius });
      });
    }
  }
  /** The reach in force, from the level — and every mesh made visible again on
   *  the way back up the ladder, so switching down and up returns the frame the
   *  visitor had rather than a permanently thinner one. */
  /**
   * T-0146 — the second half of the same idea, and the piece of T-0149 that is
   * about the two tiers with NO reach. Where the reach asks "is this too far to
   * be worth drawing", this asks "is the frustum skipping anything in return
   * for these chunk boundaries" — and where the answer is no, submits the
   * cluster as one call. `far-merge.js` states both conditions and why each one
   * makes the merge free; it is fed the spheres banked just above rather than
   * walking the layers a second time.
   */
  const farMerge = createFarMerge({
    scene: scene3d, camera, layers: FURNITURE_LAYERS,
  });
  function applyFurnitureReach(level) {
    const want = DETAIL[level] ?? DETAIL.full;
    collectFurniture();
    farMerge.rebuild(furniture.spheres);
    furniture.reachM = typeof want.furnitureReachM === 'number'
      ? want.furnitureReachM : null;
    updateFurnitureReach();
    return furniture.reachM;
  }
  /** Per frame, before the render: hide what is out of reach. Cheap by
   *  construction — one distance against a banked sphere per chunk, no matrix
   *  work and no allocation, over the couple of hundred meshes the five layers
   *  come to. */
  function updateFurnitureReach() {
    const reach = furniture.reachM;
    let drawn = 0;
    let culled = 0;
    // `eye` and `sph` rather than `p` and `s`: `tools/validate.py`'s sidecar
    // contract follows the local names a sidecar block is bound to, and a `p`
    // or an `s` here is read as `placement` and `sidecar` and reported missing.
    // The scanner says as much where it is defined; this is the one-minute
    // rename it asks for.
    const eye = camera.position;
    for (const sph of furniture.spheres) {
      let far = false;
      if (reach !== null) {
        const dx = sph.c.x - eye.x;
        const dy = sph.c.y - eye.y;
        const dz = sph.c.z - eye.z;
        far = Math.sqrt(dx * dx + dy * dy + dz * dz) - sph.r > reach;
      }
      sph.mesh.visible = !far;
      // Recorded on the mesh as well as counted, because two things now set
      // `visible` on a furniture chunk and only ONE of them is the reach: the
      // far merge (T-0146) hides a chunk it is drawing itself. The probes below
      // and the merge's own composition rule both read this flag rather than
      // `visible`, so "held back for distance" keeps meaning what T-0150's
      // gates assert it means.
      sph.mesh.userData.reachCulled = far;
      if (far) culled++; else drawn++;
    }
    furniture.drawn = drawn;
    furniture.culled = culled;
    // After the reach and never before it: a cluster with a member the reach is
    // holding back is left chunked, which is read off the flag just written.
    farMerge.update();
  }
  applyFurnitureReach(detailLevel);

  /**
   * WHERE THE SWARD MAY NOT GROW (T-0067), composed rather than replacing the
   * street's own answer. Two things block a prairie plant now: the travelled
   * track it would grow through, and a FENCE it would grow inside — the wagon
   * yard's dust, the pound's trodden earth, a dooryard's kept green are all
   * ground somebody worked, and none of them is 1.5 m of bluestem.
   *
   * THE TREES ARE DELIBERATELY NOT BLOCKED and the difference is the whole
   * reason this is composed here rather than pushed into `planting`. The
   * dooryard plantings (T-0074) and the Sauganash's own three stems stand INSIDE
   * these fences BY RECORD; a block-list entry that reached the woody layer
   * would delete every one of them and file a problem for each, which is this
   * ticket undoing another one. The sward is the only layer that gives way.
   */
  const swardBlocked = (e, n) => streets.blocksGrowth(e, n) || yards.suppressesSward(e, n);

  let floraUnits = 0, floraDone = 0, treeDone = 0;
  const plantingProgress = (done, total) => {
    if (done === 0) floraUnits += total;
    else floraDone++;
    bootController.progress('flora', floraDone, floraUnits);
  };
  let flora = await createFlora({
    checkpoint: bootCheckpoint,
    dataBase: bases.dataBase, terrain, footprints: planting,
    growthBlocked: swardBlocked,
    confidence, problems, ...detailOpts(),
  });
  scene3d.add(flora.group);
  let trees = await createTrees({
    checkpoint: bootCheckpoint,
    onProgress: (done, total) => {
      if (done === 0 && treeDone === 0) floraUnits = total;
      floraDone += done - treeDone; treeDone = done;
      bootController.progress('flora', floraDone, floraUnits);
    },
    dataBase: bases.dataBase, terrain, footprints: planting,
    growthBlocked: streets.blocksGrowth,
    confidence, problems, pixelsPerRadian, streetRecords: loaded.index?.streets ?? [],
    // Which sward a point stands in, so the woody layer plants the lakeshore
    // poplars on the ground the beach is actually drawn on rather than carrying
    // a second copy of the zone extents (ROADMAP K45(b) change one). Both call
    // sites build the sward first, and a dead `flora` would answer null, which
    // plants no dune rather than planting one somewhere invented.
    zoneAt: (e, n) => flora.zoneAt(e, n),
    ...detailOpts(),
  });
  scene3d.add(trees.group);
  await flora.prepare?.(camera, bootCheckpoint, plantingProgress);
  bootController.end('flora');
  bootController.start('interaction');
  await yieldToPaint();

  /**
   * Rebuild the two layers that scale, in place. Both are planted from a FIXED
   * seed, so the same setting always yields the same prairie — changing detail
   * and changing back gives you the town you had, not a reshuffled one.
   */
  let detailPending = null;
  async function applyDetail(level) {
    if (!DETAIL[level] || level === detailLevel) return;
    detailLevel = level;
    BUDGET.triangles = DETAIL[level].triangles;
    // The fence's half of the level, first: `light` draws a pale as a plank and
    // the other two as a prism (T-0067), and the layer rebuilds its own meshes
    // in place from records it has already loaded. It is done BEFORE the shadow
    // tier because every mesh is new after a rebuild and starts out casting —
    // `applyShadowTier` below is what settles that, and settling it first would
    // settle it on meshes that are about to be thrown away.
    enclosures.setDetail?.(level);
    // The sun's half of the level takes effect on THIS frame rather than after
    // the replanting: it costs nothing to apply, and a visitor who turns the
    // setting down on a machine that is struggling should get the cheap half of
    // the answer immediately instead of behind two layer rebuilds.
    applyShadowTier(level);
    // And the reach, for the same reason and in the same breath: the fence layer
    // has just rebuilt its meshes, so the banked spheres are re-read here rather
    // than left pointing at geometry that has been disposed (T-0150).
    applyFurnitureReach(level);
    // Serialise: a visitor clicking through the options faster than the rebuild
    // would otherwise interleave two plantings into one scene.
    const run = (detailPending ?? Promise.resolve()).then(async () => {
      scene3d.remove(flora.group);
      flora.dispose?.();
      flora = await createFlora({
        dataBase: bases.dataBase, terrain, footprints: planting,
        growthBlocked: swardBlocked,
        confidence, problems, ...detailOpts(),
      });
      scene3d.add(flora.group);

      scene3d.remove(trees.group);
      trees.dispose?.();
      trees = await createTrees({
        dataBase: bases.dataBase, terrain, footprints: planting,
        growthBlocked: streets.blocksGrowth,
        confidence, problems, pixelsPerRadian, streetRecords: loaded.index?.streets ?? [],
        zoneAt: (e, n) => flora.zoneAt(e, n),
        ...detailOpts(),
      });
      scene3d.add(trees.group);
      api.flora = flora;
      api.trees = trees;
      confidence.set(confidence.enabled);
    });
    detailPending = run.catch(() => {});
    return run;
  }

  // No `docBase` override: a dossier is read at one absolute address from every
  // tier, because the relative one resolved only in the source tree — the tree
  // nobody visits — and 404'd on the deployed site and its preview alike
  // (ROADMAP K26, popup.js DOSSIER_BASE).
  // …and one hook out of it: a firm named on a building card opens the firm's
  // own card in the drawer (T-1325). Late-bound on purpose — `openBusiness` is
  // declared with the business index, several hundred lines below, and only ever
  // runs on a tap.
  const popup = createPopup(popupRoot, { onBusiness: (id) => openBusiness(id) });
  const navigation = createNavigation({
    root: hudRoot, terrain, registry: loaded.registry, streets,
  });

  // The people directory, compiled by tools/compile_scene.py compile_people from
  // data/residents/ — one row per person, so the Go to list can offer a person
  // and the People section can filter a thousand of them without a fetch each.
  // Absent (an older mirror, a failed fetch) degrades to "no people listed";
  // it never takes the scene down.
  let people = null;
  bootController.start('people');
  try {
    const res = await fetch(new URL(`sidecars/${loaded.scene.id ?? YEAR}/people.json`, bases.dataBase), { cache: 'no-cache' });
    if (res.ok) people = await res.json();
    else throw new Error(`sidecars/${loaded.scene.id ?? YEAR}/people.json ${res.status} — nobody is listed in Go to or People`);
  } catch (err) {
    bootController.fail('people', err);
  }

  /** A structure's ground position in local ENU metres — footprint centroid where
   *  one is drawn, the placement otherwise. Go to measures distance from it;
   *  travel plans a route to it. */
  function structurePosition(id) {
    const fp = footprints.find((f) => f.id === id);
    if (fp && fp.pts.length) {
      return {
        e: fp.pts.reduce((a, p) => a + p[0], 0) / fp.pts.length,
        n: fp.pts.reduce((a, p) => a + p[1], 0) / fp.pts.length,
      };
    }
    const pl = loaded.registry.get(id)?.sidecar?.placement;
    if (!pl) return null;
    return { e: pl.local_e ?? 0, n: pl.local_n ?? 0 };
  }

  // The route planner and the travel controller. `travel` is assigned after the
  // HUD exists (it paints through it); the HUD's callbacks below reach it through
  // the binding, which is settled long before the first frame.
  const router = createRouter({
    terrain, streets, footprints, decks, surfaceAt: (e, n) => walker.surfaceAt?.(e, n) ?? terrain.surfaceHeight(e, n),
    // The walker's own capsule and step rule, so a route that plans is a route that walks.
    radius: WALK.radius, stepUp: WALK.stepUp,
  });
  let travel = null;
  api.router = router;

  /**
   * Where the last arrival stood (T-0824). While its card is up the building is
   * framed into the free part of the screen; when the card closes and the
   * visitor has not moved, the look swings back to centre the building, so the
   * crosshair is on it and the view is the plain one.
   */
  let lastArrival = null;
  function reaimAfterCard() {
    if (!lastArrival) return;
    const st = walker.state;
    const moved = Math.hypot(st.e - lastArrival.e, st.n - lastArrival.n) > 0.5;
    const id = lastArrival.id;
    lastArrival = null;
    if (moved || st.flying) return;
    const aim = focusPoint(id);
    if (!aim) return;
    const de = aim.x - st.e, dn = -aim.z - st.n;
    walker.teleport({
      local_e: st.e, local_n: st.n,
      yaw_deg: ((Math.atan2(de, dn) / DEG) + 360) % 360,
      pitch_deg: Math.atan2(aim.y - st.eyeY, Math.max(Math.hypot(de, dn), 0.1)) / DEG,
    });
  }
  new MutationObserver(() => {
    if (document.getElementById('popup')?.hasAttribute('hidden')) reaimAfterCard();
  }).observe(document.getElementById('popup'), { attributes: true, attributeFilter: ['hidden'] });

  const hud = createHud({
    root: hudRoot,
    scene: loaded.scene,
    registry: loaded.registry,
    intersections: loaded.index?.intersections ?? [],
    people,
    positionOf: structurePosition,
    visitor: () => ({ e: walker.state.e, n: walker.state.n, bearingDeg: walker.bearingDeg }),
    onTravelStop: () => travel?.stop('button'),
    isTouch: prefersTouch(),
    resolvedDetail: detailLevel,
    onConfidence: (on) => confidence.set(on),
    onFly: (on) => { intent.flying = !!on; },
    onGoTo: (target) => goToTarget(target),
    // Hiding a level removes it from the view outright — see confidence.setHidden.
    onHideLevel: (level, hide) => confidence.setHidden(level, hide),
    onSetting: (key, value) => {
      if (key === 'speed' || key === 'wagonSpeed' || key === 'horseSpeed' || key === 'eyeHeight' || key === 'pace') {
        // The slider values and the pace compose into WALK in one place —
        // travel.applyPace() — so a wagon seat and a raised eye-height slider
        // add rather than overwrite each other. Applied to the standing eye
        // immediately, not on the next step: a slider you have to walk away
        // from before it does anything reads as broken.
        travel?.applyPace();
      } else if (key === 'travelMode') {
        travel?.setMode(value);
      } else if (key === 'headBob') {
        travel?.setHeadBob(!!value);
      } else if (key === 'fov') {
        camera.fov = value;
        camera.updateProjectionMatrix();
      } else if (key === 'roadAid') {
        // R-A1. A uniform on the shared street materials — no recompile, and
        // the next frame carries it.
        streets.setLegibilityAid(value);
      } else if (key === 'brightness') {
        // K24. One scalar on the tone mapper — no recompile, no relight, and
        // the next frame carries it.
        world.setBrightness(value);
      } else if (key === 'quality') {
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, value));
      } else if (key === 'detail') {
        applyDetail(value);
      } else if (key === 'compass') {
        navigation.setCompassVisible(value);
      } else if (key === 'overviewMap') {
        navigation.setMapVisible(value);
      } else if (key === 'streetNames') {
        navigation.setStreetVisible(value);
      } else if (key === 'units') {
        navigation.setUnits(value);
      }
    },
  });

  // The liberties the scene takes, in the Evidence panel. Awaited rather than
  // fired and forgotten: it is one small JSON, and a visitor who opens the panel
  // in the first second should not find it empty. A failure here degrades the
  // panel and records a problem; it does not stop the walkthrough.

  // The Evidence panel as a hub of topics rather than one scroll; it reorganises
  // the section's own static markup, so the mounts below keep their ids.
  api.evidenceHub = createEvidenceHub({
    root: hudRoot.querySelector('[data-panel="evidence"]'),
    onTitle: (text, onBack) => hud.setTitle(text, onBack),
  });
  // The town summary used to be part of the loader. It now costs nothing on a
  // cold boot: the first visit to Evidence starts it, once, and the hub's
  // MutationObserver replaces the City tile's ellipsis when both files paint.
  let cityCensusPromise = null;
  const ensureCityCensus = () => {
    if (!cityCensusPromise) {
      cityCensusPromise = mountCityCensus({
        dataBase: bases.dataBase,
        root: document.getElementById('city'),
        buildStamp: document.getElementById('gate-build')?.textContent.trim() || `build ${VERSION}`,
        onError: err => problems.push(`city census: ${err?.message || err}`),
      }).then((c) => { api.census = c; return c; });
    }
    return cityCensusPromise;
  };
  hud.onTabChange((tab) => {
    if (tab === 'evidence') {
      void ensureCityCensus();
      api.evidenceHub?.showHub?.({ keep: true });
    }
    if (tab === 'goto') hud.goTo?.refreshDistances?.();
  });

  api.liberties = await mountLiberties({
    mount: document.getElementById('liberties'),
    noteMount: document.getElementById('liberties-note'),
    dataBase: bases.dataBase,
    registry: loaded.registry,
    problems,
  });
  // The same list, filtered to the building being inspected, in the provenance
  // popup. One fetch feeds both views: the panel says what the scene made up,
  // the card says what THIS building made up, and neither can drift from the
  // markdown they are both quoting.
  popup.setLiberties(api.liberties.liberties);

  // And the town's own law, which belongs to no attribute either. The 5 August 1835
  // ordinance fenced the ground the Trustees thought was built up closely enough to
  // burn — the only documented statement this project holds about where the built
  // town ended — and nothing is drawn in the scene for it, because a legal limit is
  // not a fence. The card carries it: pick a building and it says which side of the
  // line it stood on. A failed fetch leaves the row off rather than guessing a side.
  api.ordinances = await loadOrdinanceLimits({ dataBase: bases.dataBase, problems });
  popup.setOrdinanceLimits(api.ordinances);

  // And a relation, which belongs to no attribute at all. A house or a man could hold
  // an agency for a company that never stood in this town — Hubbard & Co. insured
  // property against loss by fire for the Howard of New-York, and three weeks before
  // the scene date the agency left the house for one man. The register has held that
  // since T-0410 and no surface read it; the card carries it now (T-1041). A failed
  // fetch leaves the block off rather than claiming the house held nothing.
  api.agencies = await loadAgencies({ dataBase: bases.dataBase, problems });
  popup.setAgencies(api.agencies);

  // And what the GROUND claims, which no building can carry either: the surface
  // every one of them stands on is graded as carefully as they are, and said so
  // nowhere a visitor could read it.
  api.ground = await mountGround({
    mount: document.getElementById('ground'),
    dataBase: bases.dataBase,
    sceneId: loaded.scene.id ?? YEAR,
    problems,
  });

  // And WHO was living here. This layer had a reader already — a household
  // travels in its building's sidecar and the building card names it — which
  // is exactly why nobody noticed that a household with no attested residence
  // and no attested workplace attaches to no building and so reached no card
  // anywhere: ROADMAP K52. Nothing of it is drawn; this is the record, on a card.
  api.residents = await mountResidents({
    mount: document.getElementById('residents'),
    noteMount: document.getElementById('residents-note'),
    dataBase: bases.dataBase,
    sceneId: loaded.scene.id ?? YEAR,
    problems,
  });
  // The town's FIRMS, read BEFORE the two directories that now cross-reference
  // them (T-1325). The index is one file and the crosswalk is one fold of it; a
  // person's card and a building's card both ask it the same two questions, so
  // neither is allowed to fold 196 rows for itself.
  api.businessIndex = await (async () => {
    try {
      const res = await fetch(new URL('businesses/index.json', bases.dataBase), { cache: 'no-cache' });
      if (res.ok) return res.json();
      problems.push(`businesses: businesses/index.json ${res.status} — no firm is listed in Businesses`);
    } catch (err) {
      problems.push(`businesses: ${err.message} — no firm is listed in Businesses`);
    }
    return null;
  })();
  const firms = firmCrosswalk(api.businessIndex);
  // A firm chip on a building card opens the firm in the drawer. Declared once
  // here, used by the popup and by both directories, so every route into a
  // business card lands the same way.
  const openBusiness = (businessId) => {
    hud.setPanel(true);
    hud.selectTab('businesses');
    api.businesses?.open?.(businessId);
  };
  popup.setBusinesses(firms.byStructure);

  // …and the same people as a DIRECTORY: one row a person, searchable and
  // filterable, with the way to the building they lived or worked at.
  try { api.people = await mountPeople({
    mount: document.getElementById('people-directory'),
    people,
    registry: loaded.registry,
    dataBase: bases.dataBase,
    sceneId: loaded.scene.id ?? YEAR,
    onGoTo: (target) => { hud.setPanel(false); goToTarget(target); },
    // The drawer's head shows the person's name with a back control while a card is open.
    onTitle: (text, onBack) => hud.setTitle(text, onBack),
    // …and the firms the register puts them in, which the business layer knew
    // about them and their own card never said (T-1325).
    firmsByPerson: firms.byPerson,
    onBusiness: openBusiness,
    problems,
  });
  bootController.end('people');
  } catch (err) { bootController.fail('people', err); }

  // …and the town's FIRMS, which until now reached a visitor only through the
  // roof they stood in. 166 of the 196 the register knows have no roof here — 26
  // reach a landmark, 61 a street and no further, 79 could be placed nowhere at
  // all — and the one
  // thing this project will not do to make them visible is invent a building for
  // them. So they get a directory and a card: every firm findable by trade,
  // street, grade and how far the record could place it, and every limit printed.
  api.businesses = await mountBusinesses({
    mount: document.getElementById('businesses-directory'),
    index: api.businessIndex,
    registry: loaded.registry,
    dataBase: bases.dataBase,
    // The scene id the resident join is cached under: the business card reads the
    // SAME address book the person card does (T-1493), so it must ask for it by
    // the same key or fetch a megabyte twice.
    sceneId: loaded.scene.id ?? YEAR,
    onGoTo: (target) => { hud.setPanel(false); goToTarget(target); },
    // A proprietor the town holds a card for is one tap from their firm: the
    // People view already knows how to open them, so this only has to ask.
    onPerson: (personId) => {
      hud.selectTab('people');
      api.people?.open?.(personId);
    },
    onTitle: (text, onBack) => hud.setTitle(text, onBack),
    problems,
  });

  // And what was LIVING here, which no building carries at all. The animal
  // records were researched to the scene date, graded, cited — and read by
  // nothing: ROADMAP K42 measured that no renderer source opened the directory
  // and the publish step did not copy it, so the layer stopped at the
  // repository. Nothing of it is drawn; this is the record, on a card.
  api.fauna = await mountFauna({
    mount: document.getElementById('fauna'),
    noteMount: document.getElementById('fauna-note'),
    dataBase: bases.dataBase,
    sceneId: loaded.scene.id ?? YEAR,
    problems,
  });

  // And what GROWS here, which flora.js has planted from the beginning and no
  // card has ever shown. The third time this project found a researched layer
  // reaching no reader, and the one that carries a finding of its own: nine of
  // the ten communities ask for more small plants than the sward lattice can
  // hold, and until this section the share a visitor actually stands in was
  // declared in docs/STATUS.md and nowhere a visitor reads.
  api.plants = await mountPlants({
    mount: document.getElementById('plants'),
    noteMount: document.getElementById('plants-note'),
    dataBase: bases.dataBase,
    sceneId: loaded.scene.id ?? YEAR,
    problems,
  });

  // And what was researched and left out, which no building can carry because
  // the buildings that would carry it are the ones not standing here.
  // …and the third category, which neither of those can hold: researched, and
  // still open. One of the four is standing in the scene, so it cannot go on the
  // not-here list without that list becoming false.
  api.exclusions = await mountExclusions({
    mount: document.getElementById('exclusions'),
    uncertainMount: document.getElementById('uncertain'),
    // …and what each of the two lists says it is, in the compiled document's own
    // words rather than a paraphrase typed into the markup beside it.
    standardMount: document.getElementById('exclusions-note'),
    uncertainStandardMount: document.getElementById('uncertain-note'),
    dataBase: bases.dataBase,
    sceneId: loaded.scene.id ?? YEAR,
    problems,
  });
  // And the open questions again, filtered to the building being inspected —
  // exactly as the liberties are, and for the same reason. One of the four is
  // standing in the scene, and the panel's entry for it promises that the
  // provenance card shows the claim carrying the doubt; the card is where a
  // visitor who walked up to that building would think to ask.
  popup.setOpenQuestions(api.exclusions.uncertain);

  // …and the shape of what is known about the people themselves (T-1160). The
  // walkthrough can stand a visitor next to a named resident; only this says how
  // few of them there are, how thin each attribute is, and what the reconstruction
  // bands below still have to supply. Rendered from the generated profile, so a
  // resident pass that moves the layer moves this panel too.
  api.population = await mountPopulation({
    mount: document.getElementById('population'),
    noteMount: document.getElementById('population-note'),
    dataBase: bases.dataBase,
    problems,
  });

  // …and the other half of the same question (T-1166). The profile says who the
  // sources name; the order book says how many people, households, businesses and
  // roofs the models say were here and the sources cannot, which ticket owes each
  // bucket, and how much of it has been built. It is the progress view of the three
  // reconstruction bands, filled by their own builds rather than by hand.
  api.orderBook = await mountOrderBook({
    mount: document.getElementById('order-book'),
    noteMount: document.getElementById('order-book-note'),
    dataBase: bases.dataBase,
    problems,
  });

  // Apply the visitor's stored settings before the first frame, so nothing
  // visibly snaps a moment after load.
  // The visitor's stored level choices, before the first frame — otherwise a
  // returning visitor who had hidden the reconstructed town sees it flash in.
  hud.applyHidden();

  camera.fov = hud.settings.fov;
  camera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, hud.settings.quality));
  streets.setLegibilityAid(hud.settings.roadAid);
  world.setBrightness(hud.settings.brightness);
  navigation.setCompassVisible(hud.settings.compass);
  navigation.setMapVisible(hud.settings.overviewMap);
  navigation.setStreetVisible(hud.settings.streetNames);
  navigation.setUnits(hud.settings.units);

  // ---- input ------------------------------------------------------------ //

  const intent = createIntent();
  const backends = createBackendSwitch(intent);

  // The travel controller: instantly, on foot, by wagon, on horseback, or flying.
  // It writes the shared intent the way a backend does, so the walker keeps its
  // collision and terrain honesty whoever is steering — see travel.js.
  travel = createTravel({
    walker, intent, hud, settings: hud.settings, router, terrain, footprints,
    focusPoint, structurePosition,
    // Where a ride or a flight ends: the framed stand-off, the same one Go to uses.
    standFor: (id) => framing(id, { card: true }),
    registry: loaded.registry,
    frame: (id) => frame(id, { card: true }),
    teleport: (where) => walker.teleport(where),
    goToAnchor: (id) => api.goTo(id),
    setFly: (on) => hud.setFly(on, { announce: false }),
    // Arriving is what opens the card: the menu closes, the building's card opens.
    onArrive: (id) => { hud.setPanel(false); pick(id); lastArrival = { id, e: walker.state.e, n: walker.state.n }; },
  });
  api.travel = travel;
  // The stored pace and travel mode, through the one function that writes WALK
  // (the slider values used to be copied into WALK by hand a few lines up).
  travel.setMode(hud.settings.travelMode);
  travel.setHeadBob(hud.settings.headBob !== false);
  travel.applyPace();

  const pointerlock = createPointerLockBackend({
    intent,
    domElement: canvas,
    onLockChange: (locked) => {
      hud.setLocked(locked);
      if (!locked) hud.say('Pointer released — click the view to look around again');
    },
  });

  const touch = createTouchBackend({
    intent,
    domElement: canvas,
    ui: {
      layer: document.getElementById('touch-layer'),
      stick: document.getElementById('stick'),
      knob: document.getElementById('stick-knob'),
      risePad: document.getElementById('rise-pad'),
      riseUp: document.getElementById('rise-up'),
      riseDown: document.getElementById('rise-down'),
    },
    onViewport: () => resize(),
  });

  let gateOpen = true;

  // Exactly one backend is live. Whichever device the visitor actually uses
  // wins, switched by the first real event of that kind — a laptop with a
  // touchscreen must not end up driving both.
  backends.activate(coarse ? touch : pointerlock);
  window.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'touch') backends.activate(touch);
    else if (e.pointerType === 'mouse') backends.activate(pointerlock);
  }, { capture: true });
  window.addEventListener('keydown', (e) => {
    // Not while typing. This capture handler switches the whole control backend
    // to keyboard-and-mouse, and the first keystroke into the Go-to search box
    // was doing exactly that — taking a visitor who had been tapping their way
    // around a phone and handing them a control scheme with no on-screen stick.
    if (isTyping(e.target)) return;
    if (!e.metaKey && !e.ctrlKey) backends.activate(pointerlock);
  }, { capture: true });

  canvas.addEventListener('click', () => {
    if (backends.active === pointerlock && !pointerlock.isLocked && !gateOpen) pointerlock.lock();
  });

  // Escape closes an open inspection card (T-0108). Escape is ALSO the
  // browser's own pointer-lock release, which no page may intercept — so this
  // cooperates rather than fights: while the pointer is locked the browser
  // eats the keystroke and unlocks, and the press that reaches us is the one
  // with nothing else to do. Acting only when a card is open leaves Escape's
  // meaning everywhere else untouched.
  window.addEventListener('keydown', (e) => {
    if (e.code !== 'Escape' || isTyping(e.target)) return;
    if (popup.openId) popup.close();
  });

  // ---- picking ---------------------------------------------------------- //

  function inspect(ndc = null) {
    let hit = buildings.pickAt(ndc, camera);
    /**
     * A fence can be the thing you are aiming at. The estray pen's geometry
     * lives on the enclosure layer now (T-0051), and it is still a structure
     * record with a card behind it — so a pick that misses every roof, or lands
     * on one standing further away than the fence in front of it, resolves
     * against the enclosures too. An enclosure with no structure behind it (the
     * wagon yard) answers null and the aim falls through to the roof, which is
     * the same behaviour as before this layer existed.
     */
    const fence = enclosures.pickAt(ndc, camera);
    if (fence && (!hit || fence.distance < hit.distance)) {
      const record = loaded.registry.get(fence.id);
      if (record) hit = { ...fence, record };
    }
    /**
     * And so can a signboard, which is the whole function of one: it hangs a
     * metre out from the wall, so at a shop door it is the nearest thing to the
     * crosshair, and the board a visitor aims at should open the business
     * behind it rather than whatever the ray finds past it (T-0039).
     */
    const board = signage.pickAt(ndc, camera);
    if (board && (!hit || board.distance < hit.distance)) {
      const record = loaded.registry.get(board.id);
      // `fromSign` rides along so the card can lead with the firm the board
      // advertises rather than the roof behind it (T-1325). A later layer that
      // wins the ray — the goods at the door, the walk underfoot — replaces the
      // hit and the flag with it, which is right: that aim was not at the board.
      if (record) hit = { ...board, record, fromSign: true };
    }
    /**
     * And so can a barrel at a shop door, which is where a visitor's crosshair
     * actually lands when they walk up to a frontage: the goods stand half a
     * metre out from the wall, so they are nearer than it. A barrel opens the
     * business whose door it stands at, and the wagon opens the hotel whose
     * yard it stands in (T-0040).
     */
    const goods = yard.pickAt(ndc, camera);
    if (goods && (!hit || goods.distance < hit.distance)) {
      const record = loaded.registry.get(goods.id);
      if (record) hit = { ...goods, record };
    }
    /**
     * And so can the walk under a visitor's feet, or the board on its post at
     * the corner — which is the whole function of a sign: it stands out at the
     * street edge, so from the road it is nearer to the crosshair than the inn
     * behind it. Both open the building whose frontage they are (T-0082).
     */
    const frontageHit = frontage.pickAt(ndc, camera);
    if (frontageHit && (!hit || frontageHit.distance < hit.distance)) {
      // The registry answers for a building's frontage; a record that is its
      // own subject — the river plank walk (T-0119) — carries its card on the
      // layer, the same arrangement the boats keep.
      const record = loaded.registry.get(frontageHit.id) ?? frontageHit.record;
      if (record) hit = { ...frontageHit, record };
    }
    /**
     * And so can a wharf, which is the largest thing on any of these derived
     * layers: it reaches out over the water in front of the warehouse, so from
     * the bank it is nearer to the crosshair than the shed it belongs to. A dock
     * opens the warehouse it serves (T-0041).
     */
    const dock = wharves.pickAt(ndc, camera);
    if (dock && (!hit || dock.distance < hit.distance)) {
      const record = loaded.registry.get(dock.id);
      if (record) hit = { ...dock, record };
    }
    /**
     * And so can a boat, which is the one pickable thing here that belongs to
     * no structure at all: a hull answers with its OWN card record, built by
     * the boat layer from data/boats/ — type, size, state and what bounded the
     * invention — rather than through the registry (T-0063).
     */
    const boat = boats.pickAt(ndc, camera);
    if (boat && boat.record && (!hit || boat.distance < hit.distance)) {
      hit = { ...boat };
    }
    /**
     * And so can the fort's well, which is the second thing here belonging to no
     * structure at all: a curb answers with its OWN card record, built by the
     * well layer from data/wells/ — where it is, what two witnesses say about
     * the place, and what was invented to draw it (T-0887).
     */
    const well = wells.pickAt(ndc, camera);
    if (well && well.record && (!hit || well.distance < hit.distance)) {
      hit = { ...well };
    }
    if (!hit) {
      popup.close();
      hud.say('Nothing there — aim at a building');
      return null;
    }
    popup.show(hit.record, { fromSign: !!hit.fromSign });
    return hit;
  }

  /** Programmatic pick: by structure_id, by NDC point, or down the crosshair. */
  function pick(target) {
    if (typeof target === 'string') {
      const record = loaded.registry.get(target);
      if (!record) return null;
      return popup.show(record) ? { id: target, record } : null;
    }
    if (target && typeof target.x === 'number' && typeof target.y === 'number') {
      return inspect(new THREE.Vector2(target.x, target.y));
    }
    return inspect(null);
  }

  /** Stand back and look at a structure — used by anchors and by the harness. */
  /**
   * THE ONE FRAMING RULE (T-0824). Where you stand when you arrive at a building
   * — by an instant Go to, at the end of a ride, or at the end of a flight — so
   * that the whole of it is in view: from its front, at the distance that fits
   * its width across the horizontal field of view and its height within the
   * vertical one, aimed at its middle. Derived from the footprint and the wall
   * height the record carries and from the camera's live field of view, never
   * from a fixed number, so a privy and a long store are each framed to fit.
   */
  function framing(id, { card = popup.openId !== null } = {}) {
    const centre = structurePosition(id);
    const aim = focusPoint(id);
    if (!centre || !aim) return null;
    const fp = footprints.find((f) => f.id === id);
    let r = 6;
    if (fp?.pts?.length) {
      let e0 = Infinity, n0 = Infinity, e1 = -Infinity, n1 = -Infinity;
      for (const [e, n] of fp.pts) { e0 = Math.min(e0, e); e1 = Math.max(e1, e); n0 = Math.min(n0, n); n1 = Math.max(n1, n); }
      r = Math.max(2, Math.hypot(e1 - e0, n1 - n0) / 2);
    }
    const record = loaded.registry.get(id);
    const wallH = record?.sidecar?.attributes?.wall_height_m?.value ?? 5;
    // A gabled roof adds roughly half a wall above the eaves.
    const h = record?.sidecar?.drawn_by ? (aim.y - terrain.surfaceHeight(centre.e, centre.n)) / 0.55 : wallH * 1.55;
    // The sphere that holds the whole building — centred at half its height,
    // reaching its furthest footprint corner — has to fit inside the NARROWER of
    // the two fields of view, with a margin of air around it. `sin`, not `tan`:
    // the near side of the sphere is closer than its centre, and a footprint
    // corner turned toward the eye is what a tangent rule cuts off (measured on
    // Hogan's store: corners at ±1.11 of the frame under the first draft).
    const R = Math.hypot(r, h / 2);
    // THE CARD IS PART OF THE FRAME. Arriving opens the building's card — 440 px
    // down the right of a desktop, a sheet over the lower 62 % of a phone — so
    // "centred in view" means centred in what the card leaves free: the sphere
    // fits inside THAT region's half-angles, and the look is turned so the
    // building sits at the free region's centre rather than the screen's.
    const free = freeRegion(card);
    // In ANGLE space, not screen space: a perspective frame is linear in the
    // tangent, so a strip at the edge of the screen is angularly narrow, and a
    // fit done on screen fractions leaves a corner out (measured: −1.05 on the
    // Sauganash under the first draft). Each axis: the free strip's angular
    // bounds, its middle as the look offset, its half-width as the largest
    // half-angle the building's sphere may subtend.
    const axis = (tanHalf, lo, hi) => {
      const aLo = Math.atan(lo * tanHalf);
      const aHi = Math.atan(hi * tanHalf);
      return { centre: (aLo + aHi) / 2, half: Math.max((aHi - aLo) / 2, 2 * DEG) };
    };
    const ax = axis(Math.tan(H_FOV_DEG * DEG / 2), free.x[0], free.x[1]);
    const ay = axis(Math.tan(camera.fov * DEG / 2), free.y[0], free.y[1]);
    const fit = (a) => (R * 1.25) / Math.sin(Math.min(a.half, 89 * DEG));
    const distance = THREE.MathUtils.clamp(Math.max(fit(ax), fit(ay), 10), 10, 90);
    // Turning RIGHT (a larger compass bearing) moves the building LEFT in frame;
    // pitching DOWN (a smaller pitch) moves it UP.
    const yawOffsetDeg = -ax.centre / DEG;
    const pitchOffsetDeg = -ay.centre / DEG;
    const stand = router.standOff(id, centre, r, { distance }) ?? centre;
    const bearingDeg = ((Math.atan2(stand.e - centre.e, stand.n - centre.n) / DEG) + 360) % 360;
    return { e: stand.e, n: stand.n, distance, bearingDeg, aim, radius: r, height: h,
      yawOffsetDeg, pitchOffsetDeg, free };
  }

  /**
   * The part of the screen the open card leaves free, as NDC ranges per axis. Mirrors card.css — 440 px on the right above 620 px wide, else
   * a sheet of min(62vh, vh − 120px) from the bottom. Read live, so a resized
   * window frames for the window it is.
   */
  function freeRegion(card = true) {
    if (!card) return { x: [-1, 1], y: [-1, 1] };
    const w = Math.max(1, window.innerWidth);
    const hgt = Math.max(1, window.innerHeight);
    if (w > 620) {
      const cardFrac = Math.min(0.9, Math.min(440, w - 24) / w);
      return { x: [-1, 1 - 2 * cardFrac], y: [-1, 1] };
    }
    const sheetFrac = Math.min(0.62, Math.max(0.3, (hgt - 120) / hgt));
    return { x: [-1, 1], y: [-1 + 2 * sheetFrac, 1] };
  }

  /** Stand back and look at a structure, framed whole — used by Go to, the rides and the harness. */
  function frame(id, { card = false } = {}) {
    // `card`: the arrival will open the building's card, so frame into the part
    // of the screen it leaves free. The harness's bare frame() aims straight, so
    // the crosshair lands on the building it was pointed at.
    const f = framing(id, { card });
    if (!f) return false;
    // lookAt places the eye `distance` from the AIM along `bearingDeg` — which is
    // the stand-off point framing() already probed for free ground — then the
    // look is turned so the building sits in the part of the screen the card
    // leaves free.
    walker.lookAt(f.aim, f.distance, f.bearingDeg);
    const st = walker.state;
    walker.teleport({
      local_e: st.e, local_n: st.n,
      yaw_deg: walker.bearingDeg + f.yawOffsetDeg,
      pitch_deg: st.pitch / DEG + f.pitchOffsetDeg,
    });
    return true;
  }

  function focusPoint(id) {
    const fp = footprints.find((f) => f.id === id);
    const record = loaded.registry.get(id);
    // A structure drawn by the enclosure layer has neither an obstruction
    // polygon nor a wall height any more, and both of the defaults below are
    // wrong for it: the placement is the pen's south-west CORNER, and 5 m of
    // assumed wall aims the crosshair nearly two metres over a fence that is
    // 1.83 m tall. So take the perimeter's own centre and its own height — the
    // Go-to menu still lists the pen, and it has to stand you in front of it.
    const fence = record?.sidecar?.drawn_by
      ? (enclosures.records ?? []).find((r) => r.structure_id === id)
      : null;
    let e; let n;
    if (fence) {
      const pts = (fence.runs ?? []).flatMap((r) => r.path_local_enu_m ?? []);
      if (!pts.length) return null;
      e = pts.reduce((a, p) => a + p[0], 0) / pts.length;
      n = pts.reduce((a, p) => a + p[1], 0) / pts.length;
      const h = fence.form?.height_m?.value ?? 1.5;
      return enuToWorld(e, n, terrain.surfaceHeight(e, n) + h * 0.55);
    }
    if (fp) {
      e = fp.pts.reduce((a, p) => a + p[0], 0) / fp.pts.length;
      n = fp.pts.reduce((a, p) => a + p[1], 0) / fp.pts.length;
    } else {
      const p = record?.sidecar?.placement;
      if (!p) return null;
      e = p.local_e ?? 0;
      n = p.local_n ?? 0;
    }
    const wallH = record?.sidecar?.attributes?.wall_height_m?.value ?? 5;
    return enuToWorld(e, n, terrain.surfaceHeight(e, n) + wallH * 0.55);
  }

  /** One route for the complete search: frame a structure, stand at a verified
   * intersection, or use one of the authored scene viewpoints. */
  function goToTarget(target) {
    if (!target?.kind) return false;
    // A person is a place by proxy: where they lived, else where they worked.
    if (target.kind === 'person') {
      const id = target.lives_at || target.works_at;
      if (!id || !loaded.registry.has(id)) return false;
      return travel.go({ kind: 'structure', id, person: target.id });
    }
    return travel.go(target);
  }

  // ---- gate ------------------------------------------------------------- //

  function openWorld() {
    if (!gateOpen) return;
    gateOpen = false;
    gate?.setAttribute('hidden', '');
    hud.show();
    hud.restore();
    const controlHelpOpen = hud.showControlHelp({ auto: true });
    // The gate doubles as the audio-unlock gesture: browsers only allow an
    // AudioContext to start from one, and ambience lands in a later slice.
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx && !api.audio) { api.audio = new Ctx(); api.audio.resume?.(); }
    } catch { /* no audio is fine; a thrown error is not */ }
    if (backends.active === pointerlock && !controlHelpOpen) pointerlock.lock();
    hud.say(backends.name === 'touch'
      ? 'Left thumb walks · drag the right side to look · tap a building'
      : 'W A S D to walk · E to inspect what you are looking at');
  }
  gateBtn?.addEventListener('click', openWorld);

  // ---- resize ----------------------------------------------------------- //

  function resize() {
    const vv = window.visualViewport;
    const w = Math.max(1, Math.round(vv?.width ?? window.innerWidth));
    const h = Math.max(1, Math.round(vv?.height ?? window.innerHeight));
    renderer.setSize(w, h, true);
    camera.aspect = w / h;
    // Hor+ : hold the horizontal field of view and let the vertical follow, so a
    // portrait phone does not end up looking down a drinking straw.
    const hFov = H_FOV_DEG * DEG;
    const vFov = 2 * Math.atan(Math.tan(hFov / 2) / camera.aspect);
    camera.fov = THREE.MathUtils.clamp(vFov * 180 / Math.PI, 55, 94);
    camera.updateProjectionMatrix();
    document.documentElement.style.setProperty('--vh', `${h}px`);
  }
  window.addEventListener('resize', resize);
  window.addEventListener('orientationchange', resize);
  window.visualViewport?.addEventListener('resize', resize);
  resize();

  // ---- loop ------------------------------------------------------------- //

  let resolveFirstFrame, rejectFirstFrame;
  const firstFrame = new Promise((resolve, reject) => { resolveFirstFrame = resolve; rejectFirstFrame = reject; });
  const clock = new THREE.Clock();
  let frames = 0;
  let fpsMark = performance.now();
  let fps = 0;
  /** Set by capture(); read back at the end of the frame it asked for. */
  let pendingCapture = null;
  /**
   * Harness only, default off: keep drawing, advance nothing. The gate compares
   * two captures of the same scene to decide whether the confidence view left
   * anything behind, and the wind blows between them — which is a comparison of
   * the weather, not of the tint. Holding the clock takes that variable out
   * instead of widening the tolerance around it.
   */
  let animationHold = false;

  /**
   * Hold the near plane at a twenty-fifth of the eye's height above the ground,
   * quantised, between `NEAR.min` and `NEAR.max`. See the NEAR block at the top
   * of this file for why the depth buffer needs it and why the water material
   * must not be biased instead. Returns the value in force, for the harness.
   */
  function setNearFor(altitude) {
    const wanted = THREE.MathUtils.clamp(
      Math.round(((altitude || 0) / NEAR.divisor) / NEAR.step) * NEAR.step,
      NEAR.min, NEAR.max);
    if (Math.abs(camera.near - wanted) > 1e-6) {
      camera.near = wanted;
      camera.updateProjectionMatrix();
    }
    return camera.near;
  }

  function tick() {
    // Keep visual simulation stable, but do not make a visitor crawl in direct
    // proportion to a slow renderer. At 2 fps the former 0.05 s clamp advanced
    // walking by only 0.10 s per real second. Movement now consumes up to a
    // quarter-second of real frame time in <= 0.05 s collision/terrain steps.
    // The clock is read either way, so releasing a hold does not deliver the
    // whole held interval as one enormous frame.
    const elapsed = Math.min(clock.getDelta(), 0.25);
    const frameDt = animationHold ? 0 : elapsed;
    const dt = Math.min(frameDt, 0.05);

    backends.active?.update?.(dt);
    // After the backend has written what the visitor is doing and before the
    // walker reads it: a ride in progress either yields to that input or steers.
    travel.update(dt, intent);
    terrain.update(dt);
    const asked = intent.takeInteract();
    // The inspect KEY toggles: the reach that opened the card also closes it
    // (T-0108). A click or tap always re-inspects — aiming at a second
    // building with a card open should open that building, not shut the first.
    if (asked && asked.source === 'key' && popup.openId) popup.close();
    else if (asked) inspect(asked.point ? new THREE.Vector2(asked.point.x, asked.point.y) : null);
    const walkSteps = Math.max(1, Math.ceil(frameDt / 0.05));
    const walkDt = frameDt / walkSteps;
    for (let i = 0; i < walkSteps; i++) walker.update(walkDt, intent);
    // The ride's bookkeeping, after the walker has consumed the intent: its own
    // writes are zeroed, the gait's head movement applied, arrival tested.
    travel.afterWalk(intent, frameDt);
    // Before the render, after the walker: the near plane is a function of where
    // the eye ended up this frame (R-BUG1, and the NEAR block above).
    setNearFor(walker.state.altitude);
    world.follow(camera.position);
    // After the camera has finished moving and before anything is submitted:
    // what the furniture's reach hides is a function of where the eye ended up
    // this frame (T-0150).
    updateFurnitureReach();
    // The same moment, for the same reason, one layer further down: what the
    // ground's reach holds back is a function of where the eye ended up this
    // frame (T-1154).
    terrain.updateGroundReach(camera.position);
    flora.update(dt, camera);
    trees.update(dt, camera);

    renderer.render(scene3d, camera);
    bootController.frameRendered();
    resolveFirstFrame();

    // Read back inside the frame that drew it. Outside the loop the drawing
    // buffer has already been composited and cleared, and readPixels quietly
    // returns the PREVIOUS frame — which makes a toggle look like it changed
    // nothing at all.
    if (pendingCapture) {
      const { grid, resolve } = pendingCapture;
      pendingCapture = null;
      resolve(readbackSignature(renderer, grid));
    }

    const st = walker.state;
    api.player.e = st.e;
    api.player.n = st.n;
    api.player.y = st.eyeY;
    api.player.bearingDeg = walker.bearingDeg;
    api.player.pitchDeg = st.pitch * 180 / Math.PI;
    api.player.speed = st.speed;
    api.player.moving = st.speed > 0.001;
    api.player.altitude = st.altitude;
    api.player.flying = st.flying;
    hud.setAltitude(st.altitude);
    navigation.update({ e: st.e, n: st.n, bearingDeg: walker.bearingDeg });

    // Wall-clock, not the clamped dt: a clamped dt reports a healthy 20 fps on
    // a machine that is actually drawing three frames a second.
    frames++;
    const now = performance.now();
    if (now - fpsMark >= 500) {
      fps = (frames * 1000) / (now - fpsMark);
      frames = 0;
      fpsMark = now;
    }
  }
  // Compile programs while the gate can still repaint, before the first draw.
  // The horizon creates its initial geometry on update, so include that too.
  trees.update(0, camera);
  await yieldToPaint();
  for (const layer of scene3d.children) {
    if (layer.isLight) continue; // targetScene already supplies the lights
    await renderer.compileAsync(layer, camera, scene3d);
    const pause = bootCheckpoint(); if (pause) await pause;
  }
  await yieldToPaint();
  renderer.setAnimationLoop(() => {
    try { tick(); } catch (err) {
      renderer.setAnimationLoop(null);
      if (bootController.readyAt === null) rejectFirstFrame(err);
      else throw err;
    }
  });

  // ---- harness ---------------------------------------------------------- //

  Object.assign(api, {
    renderer, camera, scene3d, world, terrain, buildings, walker, intent, popup, hud,
    confidence,
    backends, streets, flora, trees, navigation,
    // Where the dataset was loaded from, so a gate can re-read an authored
    // record and ask whether what it says reached the renderer — rather than
    // comparing the renderer against a copy of itself.
    dataBase: bases.dataBase,
    detailLevels: DETAIL,
    detailOrder: DETAIL_ORDER,
    // The setter side only. `detail` and `furnitureShadows` are LIVE readings
    // and are defined with the other live ones below — FOUND BY T-0115, and it
    // is the trap the K24 note twenty lines down already names: a getter
    // written in this literal is invoked ONCE by Object.assign and its value
    // copied, so `api.detail` had been frozen at whatever level the page booted
    // into ever since it was added. Nothing looked wrong, which is the trouble
    // with it — the smoke's "the level the visitor started on is restored"
    // check was comparing a constant with the constant it was made from and
    // could not fail. The rule was written down; it had simply not been applied
    // to this one.
    setDetail(level) { return applyDetail(level); },
    setConfidenceView(on) { return hud.setConfidence(!!on, { announce: false }); },
    // R-A1. The gates measure the DEFAULT, so they need to be able to read this
    // back as well as set it: "the aid is off unless a visitor moved it" is an
    // assertion, not a comment.
    setRoadAid(v) { return streets.setLegibilityAid(v); },
    // K24. The setter side only. Every LIVE reading — roadAid, brightness,
    // exposure — is defined below, because a getter written in this literal is
    // read once by Object.assign and frozen. See the note there.
    setBrightness(v) { return world.setBrightness(v); },
    // T-0002. Not a visitor setting — the town's facade tones are what the town
    // looks like. It is here because a gate has to be able to turn the tone off
    // to prove it is on (R-BUG6(a)), and the reading below is defined with the
    // other live ones for the reason K24 gives.
    setFacadeWeathering(v) { return buildings.setWeathering(v); },
    setFly(on) { return hud.setFly(!!on, { announce: false }); },
    get flying() { return walker.state.flying; },
    get altitude() { return walker.state.altitude; },
    pick,
    frame,
    framing,
    /** A local ENU point (metres, y above datum) through the live camera, as NDC
     *  — the harness's way of asking "is this corner of the building in frame". */
    project(e, n, y) {
      camera.updateMatrixWorld();
      const v = new THREE.Vector3().copy(enuToWorld(e, n, y)).project(camera);
      return { x: v.x, y: v.y, z: v.z };
    },
    goToTarget,
    structurePosition,
    setTravelMode(mode) { return hud.setTravelMode(mode); },
    setPace(pace) { return hud.setPace(pace, { announce: false }); },
    /** Harness only: run the ride forward `seconds` of simulated time, synchronously. */
    travelSimulate(seconds, dt = 1 / 30) { return travel.simulate(seconds, dt); },
    goTo(anchorId) {
      const a = anchorFor(loaded.scene, anchorId);
      if (!a) return false;
      // Set the MODE through the HUD, not on the walker: intent.flying is the
      // one master, and a walker flipped directly would be reverted on the very
      // next frame when update() reconciled it against an intent still reading
      // false. The HUD's setter is what writes the intent.
      const aerial = typeof a.altitude_m === 'number';
      hud.setFly(aerial, { announce: false });
      walker.teleport({
        local_e: a.local_e,
        local_n: a.local_n,
        yaw_deg: a.yaw_deg,
        altitude_m: aerial ? a.altitude_m : null,
        pitch_deg: typeof a.pitch_deg === 'number' ? a.pitch_deg : null,
      });
      return true;
    },
    /** The culling grid the ground was cut on, and the box it was derived from
     *  (T-0466). A reading, not a setting: `terrain.js` owns the rule. */
    groundTiling,
    /** What the ground's reach is doing, for the harness and `?debug=1`
     *  (T-1154). A reading, not a setting: `terrain.js` owns the rule. */
    groundReach() { return terrain.groundReach(); },
    setGroundReach(m) { return terrain.setGroundReach(m); },
    stats() {
      const info = renderer.info;
      return {
        drawCalls: info.render.calls,
        triangles: info.render.triangles,
        programs: info.programs?.length ?? 0,
        geometries: info.memory.geometries,
        textures: info.memory.textures,
        batches: buildings.batches.length,
        structures: loaded.registry.size,
        // T-1126 § 4: drawn against indexed. `structures` above counts what the
        // scene was TOLD to place; these two count what it managed to.
        structuresExpected: buildings.roll.expected,
        structuresStanding: buildings.roll.standing,
        bytes: loaded.bytes,
        fps: Math.round(fps),
        // R-BUG1: the near plane is no longer a constant, so a harness asking
        // why an edge is or is not stable can read the number that decides it.
        cameraNear: camera.near,
        budget: BUDGET,
        withinBudget: info.render.calls <= BUDGET.drawCalls
          && info.render.triangles <= BUDGET.triangles,
      };
    },
    /**
     * A pixel signature of the next rendered frame. Resolves from inside the
     * render loop, so it always measures a frame that includes whatever you
     * just changed — and it needs no `preserveDrawingBuffer`, which means the
     * test measures the same renderer configuration a visitor gets.
     */
    capture(grid = 12) {
      return new Promise((resolve, reject) => {
        pendingCapture = { grid, resolve };
        setTimeout(() => {
          if (pendingCapture?.resolve === resolve) {
            pendingCapture = null;
            reject(new Error('capture: no frame rendered within 10 s'));
          }
        }, 10000);
      });
    },
    /** T-0150, HARNESS ONLY and never a visitor setting: drive the furniture's
     *  reach directly, so `tools/measure_furniture_reach.mjs` can sweep candidate
     *  reaches at one page load and a gate can prove the cull is the thing doing
     *  the saving. `null` restores "draw it all". The live reading is
     *  `furnitureReach` below, defined with the other getters for the reason the
     *  K24 note gives. */
    setFurnitureReach(m) {
      furniture.reachM = typeof m === 'number' && Number.isFinite(m) ? m : null;
      updateFurnitureReach();
      return furniture.reachM;
    },
    /** T-0146, HARNESS ONLY and never a visitor setting, for the reason
     *  `setFurnitureReach` above is one: the merge's whole claim is that it
     *  changes the call count and not the triangle count, and the only honest
     *  way to read that is the same frame with it off and with it on.
     *  `tools/measure_far_merge.mjs` is what does. */
    setFarMerge(on) {
      const state = farMerge.setEnabled(on);
      // The merge only ever hides a chunk; the reach is what makes one visible
      // again, so turning the merge OFF has to run that pass rather than just
      // hiding the batches.
      updateFurnitureReach();
      return state;
    },
    /** Force one frame — for tests that must not race the animation loop. */
    step() { tick(); },
    /** Keep rendering, advance nothing — for tests comparing two frames of the
     *  same scene. Never set by the application. */
    setAnimationHold(on) { animationHold = !!on; return animationHold; },
    walkBudget: WALK,
  });

  // Live getters, defined rather than assigned: Object.assign COPIES the value
  // a getter returns at assignment time, which would have frozen these at their
  // boot-time answer and made every later reading wrong.
  //
  // K24 FOUND THAT THE NOTE ABOVE WAS TRUE AND THAT THE LITERAL HAD BEEN
  // ACQUIRING GETTERS ANYWAY. `get roadAid()` shipped inside the Object.assign
  // literal with R-A1 and was frozen at 0 from the moment it was written. Its
  // two gates both assert `=== 0` — off at boot, and back to 0 when dropped —
  // so a constant 0 passed both, and the third gate (raising it changes the
  // frame) reads a frame signature and never touched the getter. The control
  // itself was always live; the READBACK was the dead thing, which is R-A1's
  // own finding one level in: an assertion that can only ever see one value is
  // not an assertion. The brightness aid caught it because `exposure` is the
  // first of these readings whose expected value MOVES.
  //
  // So the rule, and it is why this block is the only place a live reading may
  // be written: anything on the harness whose answer changes after boot is
  // defined HERE. A getter in the literal above is a frozen snapshot.
  Object.defineProperties(api, {
    /** The level the visitor is actually on, now rather than at boot (T-0115). */
    detail: { get: () => detailLevel, enumerable: true },
    /** The ride in progress — phase, destination, distance left — live. */
    travelState: { get: () => travel?.state ?? { phase: 'idle' }, enumerable: true },
    /**
     * T-0115. What the level's shadow half actually DID to the scene, read off
     * the scene rather than off the table that asked for it — R-A1's rule about
     * assertions again: a gate that reads `DETAIL[level]` back is reading its
     * own intent, and the failure worth catching is a policy that reaches the
     * table and not the meshes. `casting` counts the furniture meshes still
     * drawn for the sun, so 0 is the claim `light` makes and anything else is
     * the bug — including a NEW furniture layer mounted outside the policy,
     * which is the way this will most likely be broken.
     */
    furnitureShadows: {
      get: () => {
        let meshes = 0;
        let casting = 0;
        // T-0127 — COUNTED, NOT ASSUMED. Before the per-mesh opt-out above, the
        // gate could read "every furniture mesh casts" as a single equality.
        // With an exemption in the layer that equality is false by design, so
        // the exempt meshes are counted here and the gate asserts
        // casting === meshes - groundHugging. A layer that silently stopped
        // casting would still fail; an exemption nobody declared cannot hide in
        // the difference.
        let groundHugging = 0;
        for (const name of FURNITURE_LAYERS) {
          const group = scene3d.getObjectByName(name);
          if (!group) continue;
          group.traverse((o) => {
            if (!o.isMesh) return;
            // The merged far batches are a BATCHING of these same meshes, not
            // furniture of their own, and they never cast (T-0146). Counting
            // them would put a non-caster into both sides of the bar
            // `casting === meshes - groundHugging` and quietly weaken it.
            if (o.userData.farMerged) return;
            meshes += 1;
            if (o.userData.groundHugging) groundHugging += 1;
            if (o.castShadow) casting += 1;
          });
        }
        return { layers: FURNITURE_LAYERS.slice(), meshes, casting, groundHugging };
      },
      enumerable: true,
    },
    /**
     * T-0150. What the level's REACH half did to the scene, read off the meshes
     * for the same reason `furnitureShadows` is: the failure worth catching is a
     * reach that reaches `DETAIL` and not the frame. `hidden` counts the
     * furniture meshes the reach is holding back at this instant, so it is a
     * function of WHERE THE VISITOR STANDS as well as of the level — 0 at every
     * level with a null reach, and 0 at `light` too if the whole town happens to
     * be inside it.
     */
    furnitureReach: {
      get: () => {
        let meshes = 0;
        let hidden = 0;
        for (const name of FURNITURE_LAYERS) {
          const group = scene3d.getObjectByName(name);
          if (!group) continue;
          group.traverse((o) => {
            if (!o.isMesh) return;
            if (o.userData.farMerged) return;
            meshes += 1;
            // `reachCulled` and not `!visible`: since T-0146 a chunk can also be
            // invisible because its cluster is being drawn as one mesh, and
            // reporting that as "the reach held it back" would make this
            // reading say `full` has a reach when it has none.
            if (o.userData.reachCulled) hidden += 1;
          });
        }
        return { reachM: furniture.reachM, layers: FURNITURE_LAYERS.slice(),
                 meshes, hidden, banked: furniture.spheres.length };
      },
      enumerable: true,
    },
    /**
     * T-0146. What the far merge is doing at this instant — clusters formed,
     * clusters merged in the frame just drawn, and the calls that saved. A
     * function of where the visitor stands, like `furnitureReach`: 0 merged in
     * a frame that is looking at a wall, and most of them merged down an axial
     * street. Read off the clusters rather than off the constants, for the
     * reason R-A1 gives above.
     */
    farMerge: { get: () => farMerge.state, enumerable: true },
    confidenceView: { get: () => confidence.enabled, enumerable: true },
    controlBackend: { get: () => backends.name, enumerable: true },
    footprints: { get: () => footprints, enumerable: false },
    decks: { get: () => decks, enumerable: false },
    roadAid: { get: () => streets.legibilityAid, enumerable: true },
    brightness: { get: () => world.brightness, enumerable: true },
    exposure: { get: () => renderer.toneMappingExposure, enumerable: true },
    facadeWeathering: { get: () => buildings.weathering, enumerable: true },
  });

  // Optional census work may finish later; it cannot hold the street closed.
  await firstFrame;
  bootController.end('interaction');
  if (gateBtn) { gateBtn.disabled = false; gateBtn.textContent = 'Tap to walk'; }
  api.ready = true;
  if (!bootController.finish()) {
    api.ready = false;
    if (gateBtn) gateBtn.disabled = true;
    throw new Error('Boot readiness barrier failed');
  }
  if (gateSub) {
    // T-0782: the count that used to open this line was `registry.size` — every
    // RECORD in the scene, bridges and the pier and the palisade and the parade
    // ground included — so it read as a building count and contradicted the 359
    // on the card three lines below it. The card counts the town; this line says
    // when the town is.
    gateSub.textContent = world.describe();
  }

  if (DEBUG) {
    console.info('[4D Chicago]', api.stats(), world.describe());
    if (problems.length) console.warn('[4D Chicago] problems:\n - ' + problems.join('\n - '));
  }
}

/**
 * Reduce the current drawing buffer to a small comparable signature: a mean, a
 * lit fraction, and a coarse grid of cell luminances. Small enough to hand back
 * over a debug protocol, specific enough that a shader change moves it.
 */
function readbackSignature(renderer, grid) {
  const gl = renderer.getContext();
  const w = renderer.domElement.width;
  const h = renderer.domElement.height;
  const px = new Uint8Array(w * h * 4);
  gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);

  const cells = new Array(grid * grid).fill(0);
  const counts = new Array(grid * grid).fill(0);
  let sum = 0;
  let lit = 0;
  let n = 0;
  for (let y = 0; y < h; y += 2) {
    const row = Math.min(grid - 1, ((h - 1 - y) * grid / h) | 0);   // readPixels is bottom-up
    for (let x = 0; x < w; x += 2) {
      const i = (y * w + x) * 4;
      const lum = 0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2];
      sum += lum;
      n++;
      if (lum > 8) lit++;
      const c = row * grid + Math.min(grid - 1, (x * grid / w) | 0);
      cells[c] += lum;
      counts[c]++;
    }
  }
  return {
    width: w,
    height: h,
    mean: sum / (n || 1),
    litFraction: lit / (n || 1),
    cells: cells.map((v, i) => Math.round(v / (counts[i] || 1))),
  };
}

/** Look up a named camera anchor in the scene file. */
function anchorFor(scene, id) {
  if (!id || !Array.isArray(scene?.anchors)) return null;
  return scene.anchors.find((a) => a.id === id) ?? null;
}
