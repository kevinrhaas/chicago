/**
 * main.js — boot, loop, and the test harness handle.
 *
 *   ?year=1835     which scene (default 1835)
 *   ?anchor=fort   start at a named camera anchor from the scene file
 *   ?structure=<id>&version=<label>
 *                  swap ONE structure for a committed alternate build of it
 *                  (T-1727; structure-versions.js). version=default names the
 *                  canonical record; an unknown id or label loads the default and
 *                  the HUD says so.
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
import { createForecast, createNetMeter, expectedBytes } from './boot-forecast.js';
import { createGateFrame } from './gate-frame.js';
import { createArrival } from './arrival.js';
import { createJourney } from './journey.js';
import { fieldLog, count as countField } from './field-log.js'; // T-2660
import { wireFieldLogView } from './field-log-view.js';
import { recall as recallHome } from './recall.js';
import { createGestureGate } from './gesture-gate.js';
import { loadScene, resolveBases, hasInspectionLod, detailAssetUrl,
  createLatestDetailSwitch, disposeLoadedAsset, bootPoolFromSearch } from './scene-loader.js';
import { readVersionRequest } from './structure-versions.js';
import { createWorld } from './world.js';
import { createTerrain, enuToWorld, fetchPrebuiltBase, fetchPrebuiltGround, groundTiling, hazeReachM } from './terrain.js';
import { createBuildings } from './buildings.js';
import { readGlassRequest, glassForDetail } from './glass.js';
import { createConfidenceView } from './confidence.js';
import { renderBudget } from './render-budget.js';
import { toggleByGrade, restoreLooks } from './confidence-presets.js';
import { createConfidenceLegend } from './confidence-legend.js';
import { createIntent, createBackendSwitch } from './controls/intent.js';
import { createPointerLockBackend, isTyping } from './controls/pointerlock.js';
import { createTouchBackend, prefersTouch } from './controls/touch.js';
import { createWalker, footprintsFrom, decksFrom, WALK } from './walker.js';
import { passageGroundFrom } from './passage-ground.js';
import { createFlora } from './flora.js';
import { createTrees } from './trees.js';
import { grownGroupName } from './tree-instances.js';
import { createPopup } from './popup.js';
import { loadReaderText } from './reader-text.js';
import { showHumanRoleCard } from './human-role-card.js';
import { createWelcome } from './welcome.js';
import { createYearPack } from './year-pack.js';
import { createDestinations } from './destinations.js';
import { createHud } from './hud.js';
import { createNavigation } from './navigation.js';
import { createStreets, fetchPrebuiltStreets } from './streets.js';
import { createEnclosures } from './enclosures.js';
import { loadOrdinanceLimits } from './ordinances.js';
import { loadAgencies } from './agencies.js';
import { createFencedGround, fetchPrebuiltYards } from './yards.js';
import { createSignage } from './signage.js';
import { createYardGoods } from './yard.js';
import { createParkedTransport } from './parked-transport.js';
import { createStandingHorses } from './standing-horses.js';
import { keptGround } from './kept-ground.js';
import { createFrontage, fetchPrebuiltFrontage, pageBuild } from './frontage.js';
import { setPickRenderer, setPickLog, pickResources } from './gpu-pick.js';
import { residentEstimate } from './resident-estimate.js';
import { createFarMerge } from './far-merge.js';
import { releaseAfterUpload, uploadLayerNow, uploadReleaseState, releaseSources,
  closeUploadedImages } from './upload-release.js';
import { compactStreams } from './compact-streams.js';
import { createTextureResidency } from './texture-residency.js';
import { createCrashGuard } from './crash-guard.js';
import { countDriverDraws } from './driver-draws.js';
import { createBlackbox, wasCut, summary as blackboxSummary, report as blackboxReport } from './blackbox.js';
import { createWharves } from './wharves.js';
import { createWorkingBank } from './working-bank.js';
import { createBoats } from './boats.js';
import { mountHumans } from './humans.js';
import { createWells } from './wells.js';
import { createTimeStream } from './time-stream.js';
import { createTelemetry } from './arrival-telemetry.js';
import { t, applyStrings } from './strings/index.js';
import './strings/arrival.js';
import { createFlags } from './flags.js';
import { createStreetGrid } from './street-grid.js';
import { initKTX2, ktx2State } from './ktx2.js';
import { jobsState } from './jobs/pool.js';
import { createStreetTrees } from './street-trees.js';
import { createStreetFurniture } from './street-furniture.js';
import { createFrontYards } from './front-yards.js';
import { SEASONS, SEASON_TREE_MODE, SEASON_CROWN, FOLIAGE, seasonDate, applySeasonLook, patchSeason, patchFoliage }
  from './season.js';
import { createContext } from './context.js';
import { createRailway } from './railway.js';
import { createViewOcclusion } from './view-occlusion.js';
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
import { createTravel, PACES } from './travel.js';
import { mountPeople } from './people.js';
import { openPictureViewer } from './pictures.js';
import { firmCrosswalk, mountBusinesses } from './businesses.js';
import { createEvidenceHub } from './evidence.js';
import { parseNavLink, createNavHistory } from './nav-link.js';
import { createNavigator } from './navigator.js';
import { paintAbout } from './about.js';
import { createResearcherMode } from './researcher.js';
import { wireWhyTips } from './why-tips.js';
import { createTour } from './tour.js';
import { createTourOverlay } from './tour-overlay.js';
import { markTerms } from './term-tips.js';
import { createRoamTip } from './roam-tip.js';
import { createTourOffer, createHints, takeJumped, HINT_MS } from './tour-offer.js';
import { createLicense } from './license.js';
import { isReconstructed } from './place-kinds.js';
import { plateFor as jauntPlate } from './pictures.js';
import { jauntModeFor, jauntChoice, styleWords } from './getting-there.js';
import { APPS as NAVIGATOR_APPS } from './apps/index.js';
import { install as installDrawerHost, goToPick } from './apps/drawer-host.js';
import { createTarget } from './target.js';
import { createTargetTag } from './target-tag.js';
import { createShowMe, plan as planShowMe, crosses as crossesShowMe } from './show-me.js';
import { spotTarget } from './photos-tab.js';
import { createWhere } from './where.js';
import { loadModernStreets } from './modern-streets.js';
import { resolveSharpness } from './sharpness.js';
import { createFrameGovernor, describeGovernor } from './frame-governor.js';
import { mountPacingRead } from './pacing-read.js';
import { decide as deviceChoice, profileDevice, readCached as cachedDeviceProfile } from './device-profile.js';

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
/*
 * T-1976, 2026-10-02 — 350 m BECOMES 250 m, AND THIS TIME THE AERIAL'S COST IS
 * TAKEN ON PURPOSE. Light had grown back over its own 825,000 across the ~60
 * owner-requested parcels of 2026-09-26..10-02 (944,550 at the forks on desktop,
 * 102 calls at Lake and Market against the 90-call floor), and AGENTS.md says the
 * floor is trimmed, not raised. Read on the published mirror of dev, desktop
 * 1280x800, by driving the shipped cull (`setFurnitureReach`) at one page load
 * with the 48² signature against 350 m, ground at its old 600 m:
 *   reach   the forks        Lake at Canal    Lake and Market   the open aerial
 *   350 m   947,294 /  75    945,213 /  79    818,341 / 102     932,220 / 86
 *   300 m   885,388 /  66        —            802,281 /  92         —
 *   250 m   878,840 /  63    833,657 /  62    754,381 /  80     878,218 / 67
 * with the frame at 250 m reading 0.00 / 0 at the forks and Lake and Market,
 * 0.01 / 4 down Lake Street and 0.05 / 9 from the air. Lake at Canal is the stand
 * that decides it: its whole excess is frontage down the axis, so no other lever
 * here reaches it (300 m leaves it at 847,663 even with the ground trimmed below).
 * The aerial is still the one view where furniture leaving can be seen, and the
 * trade is taken toward the tier's own purpose for the reason 350 was: the
 * machine that needs the floor. 200 m was not tried; T-0150 already read the
 * aerial running away below 250.
 */
const FURNITURE_REACH_LIGHT_M = 250;

/**
 * T-1976 — HOW FAR OUT THE DETAILED GROUND IS DRAWN AT `light`, IN METRES.
 *
 * Every tier drew the 2.5 m-sampled ground tiles out to terrain.js's
 * GROUND_DETAIL_REACH_M (600 m), with the continuous 15 m base carrying it
 * beyond. At `light` that is 222,772 triangles and 16 calls at the forks — the
 * second-largest layer in the frame — so this rung now hands the ground to the
 * base sooner. Nothing is un-built: the base is the same heightfield, already
 * drawn under every tile. Read with `setGroundDetailReach`, published mirror,
 * desktop, light, furniture at 250 m:
 *   reach   the forks   the open aerial (frame vs 600 m + 350 m furniture)
 *   600 m   878,840     878,218   0.05 / 9
 *   240 m   820,079     804,574   0.13 / 9
 *   120 m   805,315     754,282   0.37 / 44
 * 240 m is one tile (`GROUND_TILE_TARGET_M`) and the knee: 120 m moves the aerial
 * by a worst cell of 44 — the 15 m base showing through where the river banks
 * fold — and 240 m leaves every ground stand at a worst cell of 0 or 1. `full`
 * and `balanced` keep 600 m (null = terrain.js's own).
 */
const GROUND_DETAIL_REACH_LIGHT_M = 240;

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
const DETAIL_DECLARED = {
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
  //
  // -- T-1975, 2026-10-02 -- THE SEVENTH RE-BASING: `full` AND `balanced` ARE
  // SET TO THE TOWN THE OWNER ASKED FOR, AND `light` IS NOT --
  //
  // A CONSCIOUS RE-BUDGET, NOT A WEAKENED ASSERTION, and it is the owner's ask
  // in as many words: T-1215 ("converge the reconstructed town … the budgets
  // re-measured and set"), cut down through T-1969 and T-1974 to this piece.
  // The parcels that filled the frame are the ones he asked for — about sixty
  // merged 2026-09-26..10-02: every house finished by who lives in it, a privy
  // and a stable behind it, the walks and street edge dealt by business, the
  // boarding houses, the yards' goods. AGENTS.md's ruling of 2026-08-21 is the
  // rule ("the scene needing it IS the justification") and its three
  // constraints are the whole of what is done here.
  //
  // MEASURED FIRST. `tools/measure_detail_ceilings.mjs`, published mirror of
  // dev @ 652ca8ea, T-0135's five stands, BOTH release viewports — the reading
  // is committed as docs/measurements/t-1975-detail-ceilings-{desktop,mobile}.json:
  //
  //   tier      desktop 1280x800 worst          mobile 390x780 worst
  //   full      1,705,768 at Lake at Canal       1,556,676 at Lake at Canal
  //   balanced  1,472,889 at Lake at Canal       1,332,135 at Lake at Canal
  //   light       944,550 at the forks             845,385 at Lake at Canal
  //   calls       222 at Lake at Canal, `full`     215 at Lake at Canal, `full`
  //
  // NO ONE PARCEL TO BISECT, which is what T-1154 asked for in its day and
  // cannot be answered now: `full` read 1,383,428 worst on 2026-09-26 (the
  // `measured` line below) and the 322,340 since is spread over the sixty.
  // Each parcel was the owner's; none of them is a regression to take back.
  //
  // WHERE THE NEW NUMBERS COME FROM — the rule of the sixth re-basing and of
  // T-0672, unchanged, so the ladder keeps its shape and nothing is chosen to
  // fit one record: the measured worst stand at either viewport plus the
  // ABSOLUTE headroom T-0672 recorded for the tier, rounded up to 5,000.
  //
  //   full      1,705,768 + 18,059 = 1,723,827  ->  1,460,000 -> 1,725,000
  //   balanced  1,472,889 + 16,806 = 1,489,695  ->  1,280,000 -> 1,490,000
  //
  // NO PRE-EMPTIVE ROOM. The headroom is T-0672's and no more, so the next
  // parcel that reaches it (T-1959's woodpiles read +70,928 at Lake at Canal
  // on PR #272) brings its own number and argues its own raise here.
  //
  // -- T-1959, 2026-10-02 -- THE WOODPILES' OWN NUMBER, AS PROMISED ABOVE --
  //
  // 298 woodpiles, one mesh for the whole town (yard.js says why: the call
  // budget binds, and one mesh costs two calls everywhere), read with
  // `tools/woodpile_shots.mjs --anchor lake_at_canal` as the same pose with
  // the record refused at the network: +70,928 triangles and +2 calls at
  // `full`, and the same at every stand because the frustum keeps the whole
  // mesh. Then the sweep, published mirror of the branch on dev @ 768e0a57,
  // committed as docs/measurements/t-1959-detail-ceilings-desktop.json:
  //
  //   full      1,778,094 at Lake at Canal (1,707,166 without the woodpiles)
  //   balanced  1,545,215 at Lake at Canal (1,474,287 without)
  //   calls     224 at Lake at Canal, `full` -- inside 240, which does not move
  //
  // The same rule, worst stand plus T-0672's absolute headroom, rounded up to
  // 5,000; the desktop is the worst viewport (390x780 read 1,556,676 on dev
  // and a mesh cannot add more than its own 70,928 there):
  //
  //   full      1,778,094 + 18,059 = 1,796,153  ->  1,725,000 -> 1,800,000
  //   balanced  1,545,215 + 16,806 = 1,562,021  ->  1,490,000 -> 1,565,000
  //
  // `light` DOES NOT PAY FOR THEM: it does not draw them (`light.woodpiles`
  // below), and it read 944,714 / 102 calls to the triangle with or without,
  // before T-1976's trim brought it back inside 825,000.
  //
  // `light` DOES NOT MOVE, and it is OVER: 944,550 at the forks on desktop
  // against 825,000, 845,385 on mobile, and 102 calls at Lake and Market against
  // its 90-call floor. "`light` is the floor and stays the floor" — the tier a
  // weak machine boots into is not spent by a re-budget. It is won back by a
  // trim, and that is T-1976, which carries the layer-by-layer reading of the
  // forks. T-0672 still owes the return of the 2026-09-03 raise of this rung.
  //
  // T-1987, 2026-10-02 — THE ROAD'S OWN RAISE, on top of the woodpiles'. The
  // owner's grass growing over the dirt as he walked up to it was the ground
  // rising through road panels that sagged under it; the cure lays those
  // panels on the cells' ridge (streets.js, THE RIDGE DRAPE), and the street
  // layer is drawn whole, so it costs the same at every stand. First read on
  // dev @ 1da76db5 with `tools/measure_detail_ceilings.mjs --against`, desktop
  // 1280x800 (docs/measurements/T-1987-road-ridge-cost.md): +43,634, worst
  // 1,708,512 -> 1,752,146 at Lake at Canal. Read again on the street layer
  // itself after T-1956's terrain rebake and with the shoulders' edge halved
  // rather than laddered: 105,675 -> 154,303 triangles, +48,628, at every stand.
  // On the woodpiles' readings above, by the same rule:
  //
  //   full      1,778,094 + 48,628 = 1,826,722 + 18,059 = 1,844,781 -> 1,845,000
  //   balanced  1,545,215 + 48,628 = 1,593,843 + 16,806 = 1,610,649 -> 1,615,000
  //
  // Mobile reads lower at both tiers, so desktop sets it. `light` is NOT
  // spent: there the road keeps its refined grids (105,579, 96 under before).
  //
  // WHAT IS NOT RE-DERIVED: the timber's per-level thinning ratio (trees.js,
  // L121's refresh, 1 / 0.877 / 0.565) was read off these ceilings on
  // 2026-09-15. Re-reading it against 1,725,000 / 1,490,000 / 825,000 would
  // change the wood a visitor sees at `balanced` and `light`, which is not a
  // budget's job; it stays as stated there.
  //
  // T-0192, 2026-10-03 — THE CROSS STREETS' OWN RAISE. The seven north-south
  // streets (Market to State) take the plank walk the four east-west streets
  // carry, by the same rule: 46 platted faces, +4,764.9 m of walk and +47 board
  // crossings, the record going 47 faces / 3,865.7 m to 93 / 8,630.6 m. It was
  // refused on 2026-08-29 for want of headroom; T-1969/T-1975 re-set the
  // budget, and the owner's queue note of 2026-10-03 asked for the seven to be
  // priced and argued HERE, with `light` the floor. Read with
  // `tools/measure_detail_ceilings.mjs`, published mirrors of dev @ d8b7748d
  // and of this branch, T-0135's five stands, desktop 1280x800, same run:
  //
  //   tier      dev worst                 with the seven            delta there
  //   full      1,857,267 Lake at Canal   2,120,153 Lake at Canal   +262,886
  //   balanced  1,626,744 Lake at Canal   1,801,124 Lake at Canal   +174,380
  //   light       851,431 the forks         856,275 the forks          +4,844
  //   calls       224 at `full`             259 at `full`                 +35
  //
  // dev was ALREADY over `full` and `balanced` (by 12,267 and 11,744) before a
  // board was laid — parcels merged since T-1987 — so the rule below carries
  // that too; it is the rule of T-1975 and T-1987, unchanged: worst stand plus
  // T-0672's recorded headroom, rounded up to 5,000.
  //
  //   full      2,120,153 + 18,059 = 2,138,212 -> 2,140,000
  //   balanced  1,801,124 + 16,806 = 1,817,930 -> 1,820,000
  //   calls     259 + 15 = 274 -> 275 (`BUDGET` below)
  //
  // Mobile reads lower at every tier, so desktop sets it. `light` IS NOT
  // SPENT: it does not draw the cross streets' walks (`light.crossStreetWalks`),
  // which takes Lake and Market from 798,916 back to 738,536 and the open aerial
  // from 838,167 to 822,297 — inside 825,000. What is left at `light` (+4,844 at
  // the forks, +9,204 at the aerial) is not the boards, which are hidden there;
  // the walks still keep the sward and the planting off their own strips at
  // every tier, and that redistribution is the inferred remainder — it was not
  // attributed layer by layer on dev. The forks were over on dev already;
  // that rung is T-1976's to win back by a trim, not this ticket's to spend.
  // T-2015, 2026-10-03: final integration with dev b06a063a includes the
  // T-0192 cross-street walks and T-2014 distant shrubs. Six published stands,
  // desktop 1280x800 and narrow 390x780, two production steps per settled view:
  // full worst 2,456,812 at west prairie; balanced worst 1,860,932 there.
  // Preserve the defended margins, rounding UP to 5,000:
  // full +18,059 -> 2,475,000; balanced +16,806 -> 1,880,000.
  // These price the combined scene; they do not attribute other PRs' geometry
  // to the foliage upgrade. The owner explicitly authorized measured raises.
  // Receipt: docs/RESEARCH/vegetation-quality/integrated-ceilings.json.
  // The ordinary animation-loop smoke remains the release gate.
  // T-2035/T-2037: persistent same-root clumps retain visible plants during
  // motion. Integrated desktop six-stand maxima after zero-area tip removal:
  // full 2,820,988 +18,059 ->2,840,000; balanced 2,127,277 +16,806 ->2,145,000.
  // The owner authorized measured increases at 16:35 CDT, 2026-10-03.
  // Draw-call limits remain unchanged; these costs are not an FPS benchmark.
  //
  // -- T-0672, 2026-10-04 -- THE RETURN: EVERY TIER COMES BACK DOWN --
  //
  // Lowering is free and needs no argument; it can only make the gate stricter.
  // Read with `tools/measure_detail_ceilings.mjs`, published mirror of dev @
  // 7504e4fc (#432 in), six stands, both release viewports; the reading is
  // committed as docs/measurements/t-0672-detail-ceilings.json:
  //
  //   tier      desktop 1280x800 worst       390x780 worst
  //   full      2,665,994 west prairie       2,433,217 west prairie
  //   balanced  2,072,747 Lake at Canal      1,913,781 Lake at Canal
  //   light       988,055 west prairie         893,194 west prairie
  //
  // Desktop sets all three. T-0672's rule, unchanged: worst stand plus the
  // absolute headroom it recorded, rounded up to 5,000.
  //
  //   full      2,665,994 + 18,059 = 2,684,053  ->  2,840,000 -> 2,685,000
  //   balanced  2,072,747 + 16,806 = 2,089,553  ->  2,145,000 -> 2,090,000
  //   light       988,055 + 15,791 = 1,003,846  ->  1,040,000 -> 1,005,000
  //
  // `light` does NOT return to 785,000. The owner authorized its raises past
  // that figure twice on 2026-10-03 (T-2015, T-2035/T-2037, above), after
  // T-0672 was written, so the later ruling stands and this takes back only
  // the slack the town no longer uses. Nothing in the renderer moves. The
  // draw-call caps are unchanged (worst 275 at `full`, 81 at `light`).
  // PR #498 integration, 2026-10-07: conscious re-budget under AGENTS.md's
  // 2026-08-21 owner ruling. The 2026-10-04 ceilings above described dev
  // 7504e4fc, before the subsequent requested parcels. Current dev dbc788b2
  // itself fails all three triangle gates and the call gate on mobile; Wells
  // f899a73d adds the requested thirteen houses, not a reason to shrink them.
  // First retain Light's floor by batching ORIGINAL ground triangles and
  // applying its unchanged 240 m reach to small pieces. Then measure all six
  // published stands at both release viewports, through production setDetail
  // and two production steps plus GPU finish (Chrome headless shell 151).
  // docs/measurements/pr498-ground-batching.json retains the instrument,
  // pre-budget source hashes, full readings and its stored-Light boot choice.
  // No consumer FPS claim; the complete normal-loop smoke remains the gate.
  //
  // full:     3,139,013 (desktop West prairie) + 18,059 = 3,157,072 -> 3,160,000
  // balanced: 2,270,978 (desktop West prairie) + 16,806 = 2,287,784 -> 2,290,000
  // These are T-0672's original absolute margins, rounded up to 5,000; no
  // room is priced for a future parcel. Light remains 1,005,000 and 90 calls.
  //
  // T-2338, 2026-10-11: a conscious re-budget under the same 2026-08-21 ruling,
  // NOT a weakened assertion. Four owner-requested parcels since the last
  // passing tree (d3aa85ea5) put desktop parts 3-6 red: T-2278's openings kit
  // (windows, doors and trim on every 1835 building, +134,752 GLB triangles
  // town-wide, +104,996 of it trim) and T-2281/T-2282/T-2287's chained and
  // lettered signs. At West prairie, `light`, each group hidden in turn:
  // structures 419,859 -> 534,635, signage 5,952 -> 39,408, the sun's pass
  // 44,090 -> 65,362. Published mirror of dev 0a2491b51, six stands, both
  // release viewports, `--stepped`; docs/measurements/t-2338-detail-ceilings.json:
  //
  //   tier      desktop 1280x800 worst       390x780 worst
  //   full      3,379,890 West prairie       2,917,682 West prairie
  //   balanced  2,515,971 West prairie       2,217,707 West prairie
  //   light     1,173,622 West prairie         997,804 West prairie
  //
  // full:     3,379,890 + 18,059 = 3,397,949 -> 3,400,000
  // balanced: 2,515,971 + 16,806 = 2,532,777 -> 2,535,000
  // T-0672's absolute margins again, rounded up to 5,000; nothing priced for
  // the next parcel. `light` is NOT moved here: it is the floor, its raises
  // have only ever been the owner's (T-2015, T-2035), and T-2339 puts that
  // question to the owner. Draw calls are unchanged (worst 317, mobile prairie).
  // Period transport integration, 2026-10-19: fresh production-step pricing
  // after upstream T-2807's visible woods/tree integration. The tree parcel
  // changed the scene; separately, the corrected measurement takes two forced
  // production steps before reading renderer.info, rather than relying on two
  // RAF callbacks to have rendered a fresh, fully stepped scene. The difference
  // from earlier unforced CI samples is not attributed wholly to new trees.
  // At measured source379e7d3d, trees.js/tree-model.js match frozen e5e726ba8;
  // main.js differs only by the human role-card import/listener, with no actors.
  // This is the pricing snapshot, before the later a369c613 UI/dev merge.
  // Six stands x three tiers x both release viewports,
  // keep-geometry=1, two production steps and GPU finish: initial 27 rows plus
  // continuation 9 rows, validated as 36 unique measurements. This is split
  // diagnostic pricing, not one completed CI smoke run. Exact readings:
  // docs/measurements/period-transport-fresh-detail-2026-10-19.json.
  // Both full/balanced maxima are desktop West prairie:
  // full:     3,449,919 + 18,059 = 3,467,978 -> 3,470,000 (20,081 clear)
  // balanced: 2,607,952 + 16,806 = 2,624,758 -> 2,625,000 (17,048 clear)
  // Preserve T-0672's absolute margins, rounded up to 5,000. Light remains
  // 1,190,000 (measured 1,154,091). General draw-call cap stays 330; the
  // separate light floor stays 90 (measured 89: only one call clear). Earlier notes
  // and measured strings below are retained as the history of these rungs.
  full:     { triangles: 3470000, shadowReachM: 240, furnitureCastsShadow: true,
              furnitureReachM: null, groundDetailReachM: null,
              // T-3146: Full as well as Light runs T-2529's sun-pass test
              // (shadow-casters.js), unchanged: a structure piece is left out of
              // the shadow map only when its whole swept shadow lies outside one
              // plane of the view frustum. On Prairie 38 m east and 30 m south of
              // Glessner looking at it, 4,677,248 -> 4,383,566 against 4,600,000;
              // on 18th 45 m west and 32 m north, 4,601,509 -> 4,594,157 (the sun
              // throws Glessner's shadow toward that camera, so it keeps casting).
              // Every pixel of each held frame reads the same off and on.
              // Receipts: docs/RESEARCH/glessner-close-budget-3146/.
              castersTowardView: true,
              // T-0135's ruling asks every rung to say WHAT IT IS FOR and WHAT
              // MEASUREMENT SET IT, because "a rung that cannot say what it
              // protects is the next version of this ticket". The archaeology
              // above stays — it is how the number got here — and these two
              // lines are the answer a reader needs before any of it.
              protects: 'the machine this project targets: a desktop with a real '
                + 'GPU, running the town at 1280x800 with every layer at full detail',
              measured: '3,470,000 set 2026-10-19: fresh production-step split diagnostic '
                + 'pricing after T-2807 tree integration; 36 unique rows, six stands '
                + 'at both viewports and all tiers, 27 initial plus 9 continuation. '
                + 'At measured379e7d3d, tree modules match e5e726ba8; main differs by human '
                + 'role-card import/listener, with no human actors placed. Worst 3,449,919 at '
                + 'desktop West prairie, +18,059 rounded up to 5,000. Measurement '
                + 'freshness correction is separate from the visible tree parcel; '
                + 'the whole increase is not attributed to trees. '
                + 'docs/measurements/period-transport-fresh-detail-2026-10-19.json. '
                + 'Previously 3,400,000 set 2026-10-11 (T-2338): published dev 0a2491b51 after '
                + 'the owner-requested openings kit (T-2278) and chained signs (T-2281), '
                + 'six stands at both viewports: worst 3,379,890 at desktop West prairie; '
                + '+18,059 rounded up to 5,000. docs/measurements/t-2338-detail-ceilings.json. '
                + 'Previously 3,160,000 set 2026-10-07 (PR #498 integration): published Wells '
                + 'f899a73d plus exact ground batching, six stands at both viewports: '
                + 'worst 3,139,013 at desktop West prairie; +18,059 rounded up to '
                + '5,000. docs/measurements/pr498-ground-batching.json. Previously '
                + '2,685,000 set 2026-10-04 (T-0672), the return: dev 7504e4fc, '
                + 'six published stands, worst 2,665,994 and 250 calls at west prairie, '
                + '1280x800 (390x780 read 2,433,217); +18,059 rounded up to 5,000. '
                + 'Previously 2,840,000 set 2026-10-03 (T-2035/T-2037), owner-authorized '
                + 'at 16:35 CDT. Integrated dev a9c98af7, six published desktop '
                + 'stands after zero-area tuft-tip removal: worst 2,820,988 and '
                + '282 calls at west prairie; +18,059 rounded up to 5,000. '
                + 'Same-root vegetation carries remain visible during motion. '
                + 'Previously 2,475,000 set 2026-10-03 (T-2015), including dev b06a063a: '
                + 'six published stands, worst 2,456,812 at west prairie, 1280x800; '
                + 'the defended 18,059 rounded up to 5,000. Before it: '
                + '2,140,000 set 2026-10-03 (T-0192) for the seven cross '
                + "streets' plank walks: worst 2,120,153 at Lake Street at Canal at "
                + '1280x800 with them, +262,886 there on dev @ d8b7748d, plus '
                + "T-0672's 18,059 rounded up to 5,000. Before it: "
                + '1,845,000 set 2026-10-02 (T-1987) for the road laid on the '
                + "cells' ridge, +48,628 at every stand on 1,778,094 (the block above "
                + "`full`), plus T-0672's 18,059 rounded up to 5,000. Before it: "
                + '1,800,000 set 2026-10-02 (T-1959), the woodpiles\u2019 own '
                + 'number by T-1975\u2019s rule: worst 1,778,094 at Lake Street at Canal '
                + 'at 1280x800 with them, 70,928 of it theirs \u2014 21,906 clear, '
                + "T-0672's 18,059 rounded up to 5,000. Before it: "
                + '1,725,000 set 2026-10-02 (T-1975, the seventh re-basing, on '
                + "the owner's T-1215 \u201cthe budgets re-measured and set\u201d), from "
                + '1,460,000. Read on dev @ 652ca8ea, published mirror, T-0135\'s five '
                + 'stands: worst 1,705,768 at Lake Street at Canal at 1280x800 and '
                + '1,556,676 there at 390x780 \u2014 19,232 clear, 1.1 %, which is '
                + "T-0672's recorded 18,059 rounded up to 5,000 and nothing more" },
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
  // T-1975, 2026-10-02: 1,280,000 -> 1,490,000 in the seventh re-basing — the
  // reading and the rule are in the block above `full`.
  // T-1987, 2026-10-02: 1,565,000 -> 1,615,000 for the road's ridge, by the
  // same rule — the reading is in the block above `full`.
  // T-0672, 2026-10-04: 2,145,000 -> 2,090,000, the return — the reading and
  // the rule are in the block above `full`.
  // T-2338, 2026-10-11: 2,290,000 -> 2,535,000 with `full` — the reading and
  // the rule are in the block above `full`.
  balanced: { triangles: 2625000, shadowReachM: 240, furnitureCastsShadow: true,
              furnitureReachM: FURNITURE_REACH_BALANCED_M, groundDetailReachM: null,
              protects: 'the median visitor: integrated graphics on an ordinary '
                + 'laptop, which is what most people arrive on',
              measured: '2,625,000 set 2026-10-19: same fresh production-step split '
                + 'diagnostic pricing (27 initial plus 9 continuation rows), six '
                + 'stands at both viewports and all tiers; worst 2,607,952 at '
                + 'desktop West prairie, +16,806 rounded up to 5,000. '
                + 'docs/measurements/period-transport-fresh-detail-2026-10-19.json. '
                + 'Previously 2,535,000 set 2026-10-11 (T-2338): same published six-stand, '
                + 'two-viewport sweep of dev 0a2491b51, worst 2,515,971 at desktop West '
                + 'prairie; +16,806 rounded up to 5,000. Previously '
                + '2,290,000 set 2026-10-07 (PR #498 integration): same published '
                + 'six-stand, two-viewport sweep, worst 2,270,978 at desktop West '
                + 'prairie; +16,806 rounded up to 5,000. Previously '
                + '2,090,000 set 2026-10-04 (T-0672), the return: dev 7504e4fc, '
                + 'six published stands, worst 2,072,747 and 233 calls at Lake Street '
                + 'at Canal, 1280x800 (390x780 read 1,913,781); +16,806 rounded up to '
                + '5,000. Previously 2,145,000 set 2026-10-03 (T-2035/T-2037), owner-authorized '
                + 'at 16:35 CDT. Integrated dev a9c98af7, six published desktop '
                + 'stands after zero-area tuft-tip removal: worst 2,127,277 and '
                + '248 calls at west prairie; +16,806 rounded up to 5,000. '
                + 'Same-root carries and exact distant walk tops remain visible. '
                + 'Previously 1,880,000 set 2026-10-03 (T-2015), including dev b06a063a: '
                + 'six published stands, worst 1,860,932 at west prairie, 1280x800; '
                + 'the defended 16,806 rounded up to 5,000. Before it: '
                + '1,820,000 set 2026-10-03 (T-0192) for the seven cross '
                + "streets' plank walks: worst 1,801,124 at Lake Street at Canal at "
                + "1280x800 with them, +174,380 there, plus T-0672's 16,806 rounded "
                + 'up to 5,000. Before it: '
                + '1,615,000 set 2026-10-02 (T-1987) for the road laid on the '
                + "cells' ridge, +48,628 at every stand on 1,545,215, plus T-0672's "
                + '16,806 rounded up to 5,000. Before it: '
                + '1,565,000 set 2026-10-02 (T-1959) for the woodpiles by the '
                + 'same rule: worst 1,545,215 at Lake Street at Canal at 1280x800 with '
                + 'them, 70,928 of it theirs \u2014 19,785 clear. Before it: '
                + '1,490,000 set 2026-10-02 (T-1975) in the same re-basing and '
                + 'by the same rule. Read on dev @ 652ca8ea, published mirror: worst '
                + '1,472,889 at Lake Street at Canal at 1280x800 and 1,332,135 there at '
                + "390x780 \u2014 17,111 clear, 1.1 %, T-0672's recorded 16,806 rounded "
                + 'up to 5,000' },
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
  // T-2015, 2026-10-03: the owner explicitly authorized budget increases in
  // this session. The expanded six-stand sweep finds 887,259 at west prairie
  // after full -> light, despite every original stand being 2,720-20,480
  // triangles cheaper than before. 887,259 + the prior 21,933 margin, rounded
  // up to 5,000, gives 910,000. This changes the declared ceiling, not geometry,
  // plant density, visibility reach or the separate 90-call light cap. It is
  // an explicit owner-authorized exception to the repository's standing
  // keep-825,000 guidance; light remains the least expensive rung.
  // Final b06a063a integration reads 885,447 at desktop prairie and 790,681
  // at narrow prairie; the initial 910,000 ceiling still carries both.
  // T-2035/T-2037, 2026-10-03: the owner again authorized a measured increase
  // at 16:35 CDT. Same-root grass carries and exact distant walk tops cost
  // 1,015,035 at desktop prairie and 920,708 at mobile prairie after deleting
  // zero-area tuft-tip triangles. Retain the prior 21,933 margin, rounded up
  // to 5,000: 1,040,000. This knowingly raises the weak-device triangle budget;
  // it does not establish consumer FPS. The separate 90-call cap is unchanged.
  // T-0672, 2026-10-04: 1,040,000 -> 1,005,000, the return — the reading and
  // the rule are in the block above `full`; why not 785,000 is said there too.
  // T-2339, 2026-10-11: 1,005,000 -> 1,190,000, the THIRD owner-authorized
  // exception for this rung (after T-2015 and T-2035), answered (a) on
  // Manager's 4D Board on 2026-10-10. It is a conscious re-budget and NOT a
  // weakened assertion. The owner-requested openings kit (T-2278: windows,
  // doors and trim on every 1835 building, +104,996 trim triangles town-wide)
  // and chained signs (T-2281/T-2282/T-2287) put this rung over at desktop
  // 1280x800. At West prairie, with each group hidden in turn, structures
  // went 419,859 -> 534,635, signage 5,952 -> 39,408 and the sun's pass
  // 44,090 -> 65,362. Published dev 0a2491b51, six stands, `--stepped`, in
  // docs/measurements/t-2338-detail-ceilings.json (PR #679, T-2338):
  //   desktop worst 1,173,622 West prairie (Lake at Canal 1,030,925)
  //   390x780 worst   997,804 West prairie -- still under the OLD floor
  // 1,173,622 + 15,791 (T-0672's recorded headroom for this rung) = 1,189,413,
  // rounded up to 5,000 = 1,190,000. No trim was available: the town draws as
  // three merged batches with no level of detail, so the openings cannot drop
  // at distance without a GLB-contract change (the declined option b). The
  // 90-call cap, the reaches and the shadow tier are unchanged; nothing in
  // the scene moves. A later trim can still bring this back down, as T-0672 did.
  light:    { triangles: 1190000, shadowReachM: 120, furnitureCastsShadow: false,
              // T-2529: a structure piece casts only if its shadow can reach the
              // view (shadow-casters.js). Conservative, so the frame is the same
              // picture; the sun's pass stops drawing houses whose shadows fall
              // away from the screen. `full` and `balanced` are unchanged.
              castersTowardView: true,
              furnitureReachM: FURNITURE_REACH_LIGHT_M,
              groundDetailReachM: GROUND_DETAIL_REACH_LIGHT_M,
              // T-1959: NO WOODPILES AT `light`. They are one mesh for the whole
              // town (the call budget's choice, yard.js), so the reach cannot thin
              // them and they would cost this rung their whole colour pass at every
              // stand — about 35,000 triangles — on the rung T-1976 has just
              // trimmed back inside 825,000, which is won back, never spent. `full`
              // and `balanced` draw them, and `applyFurnitureReach` hides them here.
              woodpiles: false,
              // T-0192: NO CROSS-STREET WALKS AT `light` either. The seven
              // north-south streets' plank walks (4,765 m, 46 faces) cost this
              // rung +25,074 at the open aerial and +56,584 at Lake and Market,
              // desktop 1280x800 (the reading is in the block above `full`), on
              // a rung that is already over at the forks on dev. The floor is
              // won back, never spent: `full` and `balanced` draw them.
              crossStreetWalks: false,
              protects: 'the weak-machine floor \u2014 the tier a touch device and a '
                + 'machine without a GPU boot into, and the only rung that is a '
                + 'promise to a person rather than a budget for a parcel',
              measured: '1,190,000 set 2026-10-11 (T-2339), the third exception, '
                + 'explicitly authorized by the owner on 2026-10-10 after the '
                + 'owner-requested openings kit (T-2278) and chained signs (T-2281): '
                + 'published dev 0a2491b51, six stands, worst 1,173,622 at desktop '
                + 'West prairie, 1280x800 (390x780 read 997,804); +15,791, T-0672’s '
                + 'recorded headroom for this rung, rounded up to 5,000; 90 calls unchanged. '
                + 'docs/measurements/t-2338-detail-ceilings.json. '
                + 'Previously 1,005,000 set 2026-10-04 (T-0672), the return: dev 7504e4fc, '
                + 'six published stands, worst 988,055 and 62 calls at west prairie, '
                + '1280x800 (390x780 read 893,194); +15,791, T-0672’s recorded '
                + 'headroom for this rung, rounded up to 5,000. '
                + 'Previously 1,040,000 set 2026-10-03 (T-2035/T-2037), explicitly authorized '
                + 'by the owner at 16:35 CDT. Published six-stand worst after dev '
                + 'a9c98af7 and zero-area tuft-tip removal: desktop 1,015,035 and '
                + 'mobile 920,708, both at west prairie; maximum calls 77/75. '
                + 'Preserves a 21,933 triangle margin rounded up to 5,000; '
                + '90 calls unchanged. Same-root carries and exact far walk tops '
                + 'remain visible; this is not a consumer frame-rate claim. '
                + 'Previously 910,000 set 2026-10-03 (T-2015), explicitly authorized by '
                + 'the owner. Published six-stand worst 887,259 at west prairie after '
                + 'full -> light; +21,933 rounded up to 5,000. Existing-view geometry '
                + 'decreases versus baseline; density, reach and 90 calls are unchanged. '
                + 'Final integration with dev b06a063a reads 885,447 at desktop prairie. '
                + 'Before this exception: 825,000 set 2026-09-03, the one raise of this rung ever '
                + 'taken and taken only on a second explicit ruling. BACK INSIDE BY A '
                + 'TRIM, T-1976, 2026-10-02: furniture reach 350 -> 250 m, detailed '
                + 'ground 600 -> 240 m, tree keep 0.225 -> 0.191, all at this rung '
                + 'only. Published mirror, desktop 1280x800: worst 803,067 at the '
                + 'forks — 21,933 clear, 2.7 % — and worst calls 73 (Lake '
                + 'and Market) against the 90-call floor. It was OVER on dev @ '
                + '652ca8ea (T-1975, 2026-10-02): worst 944,550 at the forks at '
                + '1280x800 and 845,385 at Lake Street at Canal at 390x780, 102 calls '
                + 'at Lake and Market against the 90-call floor. NOT raised \u2014 this '
                + 'rung is won back by a trim, T-1976. The reading before it, which '
                + 'held: Re-read on dev '
                + '2026-09-26, published mirror, after T-1595: worst 772,025 at the '
                + 'open aerial \u2014 52,975 clear, 6.4 % \u2014 at 1280x800, and '
                + '698,550 at the same stand at 390x780. Its DRAW-CALL floor is a '
                + 'separate promise and it was RED at 99 against 90 until T-1595 '
                + "gave the ground's apron one draw call instead of 130; it is GREEN "
                + 'at 82 (Lake and Market) on desktop and 74 on mobile, and it was '
                + 'won by a trim and not by moving the number' },
};
const DETAIL_ORDER = ['full', 'balanced', 'light'];
/**
 * THE LADDER IS SEALED HERE, AND THAT IS WHY `DETAIL` IS BUILT RATHER THAN
 * WRITTEN (T-0135, the owner's ruling of 2026-09-21).
 *
 * The table above is a DECLARATION. This is the thing that turns it into a
 * ladder, and the distinction is the whole of the ruling: "three rungs that no
 * longer ascend are not a quality ladder — they are three numbers."
 *
 * SAY PRECISELY WHAT THE RISK IS, because the loose version of it is wrong and
 * checkable. The three numbers in this table have always descended at any one
 * instant, the ruling's own set included — 1,320,377 / 1,144,787 / 992,617 is a
 * descending set, and it is a descending set against today's rungs too. What
 * has NEVER existed is anything that made them. The raise of 2026-08-22 is the
 * near miss on the record and this table says so above: `light` went to
 * 1,050,000, "MORE than `full` promised the day before". Across that raise the
 * bottom rung passed the old top rung; only the fact that `full` was raised in
 * the same commit kept the set ordered, and nothing in the code cared either
 * way. Seven re-basings are recorded above, each one hand-checked by whoever
 * took it, and the ruling that asks for this seal opens by worrying — in the
 * owner's own words — that raising `light` "puts it above what `full` carries
 * today". The check was a person reading a table, every time, and a person is
 * what this replaces.
 *
 * So the ceiling a tier actually carries is the RUNNING MINIMUM down
 * `DETAIL_ORDER`, not the number typed beside it. A rung can be typed too high;
 * it cannot BE too high. That is what "monotonic by construction" has to mean
 * to be worth anything — an assertion can be deleted by the same edit that
 * breaks the thing it asserts, and a `throw` here would turn a mistyped ceiling
 * into a white screen for a visitor, which is a worse failure than the one it
 * guards. The construction cannot be deleted without deleting the ladder.
 *
 * A clamp that nobody can see is the other failure, so it is reported rather
 * than swallowed: the clamped rung carries `declared` and `clamped: true`,
 * `console.error` says so at boot, and `tools/smoke_renderer.mjs` gates BOTH —
 * that the declared numbers descend on their own, and that no rung is running
 * clamped. Today nothing clamps: 1,845,000 > 1,615,000 > 825,000, and the
 * running minimum is the identity. The seal costs nothing until the day it is
 * the only thing standing between a typo and a ladder that lies.
 *
 * `protects` and `measured` are required of every rung for the same reason and
 * gated the same way. A ceiling with no stated purpose is a number somebody
 * will raise, because there is nothing written down for the raise to argue
 * against — which is the fault T-0135 was opened on, one level up.
 */
const sealLadder = (declared, order) => {
  const sealed = {};
  let above = Infinity;
  for (const level of order) {
    const rung = declared[level];
    if (!rung) throw new Error(`scene detail: '${level}' is in the order and not in the table`);
    const ceiling = Math.min(rung.triangles, above - 1);
    if (ceiling !== rung.triangles) {
      console.error(`scene detail: the '${level}' ceiling is declared at `
        + `${rung.triangles.toLocaleString('en-US')}, which does not sit under the rung `
        + `above it (${(above).toLocaleString('en-US')}). It is running clamped to `
        + `${ceiling.toLocaleString('en-US')}. A ladder whose rungs do not descend is `
        + 'three numbers — fix the declaration (T-0135).');
    }
    sealed[level] = { ...rung, triangles: ceiling, declared: rung.triangles,
      clamped: ceiling !== rung.triangles };
    above = ceiling;
  }
  return sealed;
};
const DETAIL = sealLadder(DETAIL_DECLARED, DETAIL_ORDER);
// T-1730, 2026-09-30: FULL allowance for explicitly selected Glessner v4 only,
// on the owner's permission to spend rendering headroom for this inspection.
// Ref04's actual 47,037,292-byte optimized GLB, desktop 1280x800, read over
// Prairie / 18th / courtyard / stable / aerial: 3,360,569 / 3,430,985 /
// 3,407,033 / 3,377,651 / 3,380,925 rendered triangles, at most 105 calls.
// The 3,800,000 ceiling leaves 10.8% over that observed maximum. These are
// rendered passes, not the master inventory of 1,070,689 triangles. Final
// all-viewport validation still checks the released bytes. The ordinary town,
// balanced 1,280,000, light 825,000 and 215 draw calls are unchanged.
// T-2219, 2026-10-13: the existing T-2470 Full asset renders 3,890,920 /
// 3,836,612 / 3,655,925 triangles at the fixed service-junction / front /
// elevated-junction stands (1280x800, 225 calls maximum). The original 3.8M
// T-1730 allowance predates the completed masonry and roof detail and already
// fails before this repair. After integrating T-2473, the same stand with summer
// street trees reads 4,274,524 triangles / 229 calls. The final 4.6M allowance
// leaves 7.6% over that integrated reading. Keep the ordinary town, Balanced,
// Light and draw-call ceilings unchanged. Before/after receipts and cameras:
// docs/RESEARCH/glessner-service-junction-T-2219/ . This is a spot measurement,
// not a frame-rate guarantee; the existing Scene detail control selects Light.
// T-3084, 2026-10-26: a conscious Full-only allowance for the catalogue
// Brougham body, keeping its original 45,338 / 23,062 geometry intact. The
// separate thin-sheet optical delivery avoids the whole-world transmission
// pass. A fresh exact-e97 published diagnostic measured 24 two-step/GPU-readback
// frames at both widths and both tiers; desktop Full carriage quarter was
// 4,654,565 against the previous 4,600,000. Price selected inspection Full at
// 4,700,000 (45,435 triangles clear), not the unmeasured 4.65M proposal.
// Ordinary Full, Balanced, every Light/draw/shadow/reach/LOD setting stay exact.
// Both Light district-air readings still exceed their unchanged 1.27M floor;
// neither that shared failure nor memory is repaired by this Full allowance.
// Actual readings and limits: docs/measurements/brougham-optical-delivery-3084.json.
const GLESSNER_V4_FULL_TRIANGLES = 4700000;
// T-2217, 2026-10-14: the previously unmeasured carriage-door close-up
// already draws 340 calls on dev, before the door change (4,443,344 tris).
// The rebuilt door draws the SAME 340 calls (4,465,836 tris); the other four
// passage stands peak at 238. Price this Full inspection at 360 calls, 5.9%
// above the observed maximum, under the owner's explicit headroom ruling.
// This is a declared Full-only re-budget, not a mesh or rendering change.
// Balanced, Light and non-inspection scenes retain BUDGET.drawCalls (330).
// Receipts: docs/RESEARCH/glessner-porte-cochere-T-2217/.
// T-2970, 2026-10-20: RETIRED. Counted at the driver, the five carriage-door
// stands read 2,650-4,609 draws at Full (south leaf the worst; three's own
// counter said 279-492 there, so north leaf already stood over this 360), and
// the town's re-based ceiling below carries them, so Glessner's Full inspection
// is held to the ceiling every other scene is. Its 4.6M triangles stand.
// T-2218: the new courtyard stair-bottom stand already renders 1,224,656
// triangles / 213 calls in Light before the geometry change, exceeding the
// older 1.19M allowance. Price this Glessner inspection at 1.27M (3.7% margin),
// below Balanced's 1.28M. Other scenes retain 1.19M and all Light scenes retain
// 330 calls. This is a measured allowance under the owner's headroom ruling;
// it is not a frame-rate claim. Before/after: glessner-courtyard-steps-T-2218.
const GLESSNER_V4_LIGHT_TRIANGLES = 1270000;
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
//
// T-1975, 2026-10-02: 215 -> 240, in the same re-basing and on the same ask as
// `DETAIL` above (T-1215, "the budgets re-measured and set"). The town's worst
// frame is now 222 calls at `full` down Lake Street from Canal at 1280x800
// (215 at 390x780), published mirror of dev @ 652ca8ea. 215 was set against a
// measured worst of 200, so it carried 15 calls; 222 + 15 = 237, rounded up to
// 5. The same principle, no new room: the woodpiles of PR #272 add 2 calls at
// that stand and fit, and the parcel after them argues its own. `light`'s own
// 90-call floor in `tools/smoke_renderer.mjs` is a separate promise and does
// NOT move — it reads 102 and is T-1976's to win back by a trim.
//
// T-0192, 2026-10-03: 240 -> 275 for the cross streets' walks. A chunk is one
// block face and the seven add 46 of them, so the worst frame went 224 -> 259
// calls at `full` down Lake Street from Canal at 1280x800 (dev @ d8b7748d and
// this branch, same run); 259 + 15 = 274, rounded up to 5. `light` draws none
// of them and its 90-call floor does not move (72 at Lake and Market).
// T-2015: the six-stand integration sweep includes west prairie, where the
// narrow viewport reaches 277 calls (desktop 276). The defended 15-call margin,
// rounded up to five, gives 295. Light peaks at 74 and keeps its 90-call cap.
// PR #498 integration, 2026-10-07: six stands at both viewports after exact
// ground batching peak at 313 calls (mobile West prairie, full). The defended
// 15-call margin, rounded up to five, moves 295 -> 330. Light's separate 90
// remains unchanged; the complete normal-loop smoke rechecks both ceilings.
//
// T-2970, 2026-10-20: 330 -> 7,800, AND THE UNIT CHANGED, NOT THE SCENE. Every
// figure above was `renderer.info.render.calls`, which counts a BatchedMesh as ONE
// call while three submits it as a multi-draw with one driver draw per instance it
// kept; at the 1904 flight that read 339 where the GL received 27,895 (T-2927),
// so no ceiling here ever saw what a phone pays. `stats().drawCalls` is now the
// driver's count (driver-draws.js), audited draw for draw against a GL-level tally
// by tools/measure_pose_draws.mjs (3,288 = 3,288 at the 1904 flight, three: 360).
// Re-read at the gate's six stands after T-2927's coalescing, published mirror,
// tools/measure_detail_ceilings.mjs (receipts: docs/measurements/T-2970-driver-draws.json):
//
//                       full worst              light worst
//   desktop 1280x800    7,358 (the open aerial)  5,541 (West prairie)
//   mobile   390x780    5,898 (the open aerial)  4,347 (West prairie)
//
// The same principle as every raise above, in the new unit: the measured worst
// and about five per cent, rounded up to a hundred — 7,358 -> 7,800. It is a
// ratchet on what the town draws today, and NOT a claim that 7,800 draws is a
// cost a phone can carry; the tiers' triangle ceilings are unchanged.
const BUDGET = { drawCalls: 7800, triangles: DETAIL.full.triangles };

/** localStorage, or null where the page may not have it (a private window, a sandbox). */
const safeStorage = () => { try { return window.localStorage; } catch { return null; } };

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
 * T-2863 — THE GROWN WOOD GHOSTS AS A DITHER TOO, which is a draw-budget ruling and
 * not a claim that the trees are furniture (they keep their own shadow and reach).
 * Its four batches (`tree-instances.js`: shade and far, wood and leaves) held only
 * Inferred stems until T-2809 stood young apple, sour cherry and peach among them
 * at Reconstructed, so with Reconstructed set to Ghost every batch carried a ghosted
 * grade AND another one and was drawn in both passes: six more calls in the ghost
 * pass (each leaf batch twice, as a double-sided transparent material is), measured
 * at Hogan's store at 1280x800 as 320 -> 326, and read by the desktop smoke's
 * T-2648 frame as 331 of 330. Named here, a ghosted stem is screen-door dithered at
 * its opacity in the opaque pass instead, and the ghost pass never draws the wood.
 */
const GROWN_TIMBER_LAYER = grownGroupName('timber');

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

/** T-2481: the Season setting and whether the street trees show, from the
 *  chicago4d.settings blob. T-2473 stored the season in `streetTrees` itself
 *  ('summer' | 'spring' | 'winter' | 'hidden'); such a blob still reads right. */
function readSeasonPreference() {
  let saved = {};
  try { saved = JSON.parse(window.localStorage.getItem('chicago4d.settings') || '{}') ?? {}; } catch { /* none */ }
  const legacy = SEASONS.includes(saved.streetTrees) ? saved.streetTrees : null;
  const season = SEASONS.includes(saved.season) ? saved.season : (legacy ?? 'summer');
  return { season, treesShown: saved.streetTrees !== 'hidden' };
}
/** T-2692: whether Settings shows the 1904 lot lines; hidden unless chosen. */
function readLotLinesPreference() {
  try { return JSON.parse(window.localStorage.getItem('chicago4d.settings') || '{}')?.lotLines === 'shown'; } catch { return false; }
}
/** The street elms' mode for a season, or hidden. */
function streetTreeMode(season, treesShown) {
  return treesShown ? (SEASON_TREE_MODE[season] ?? 'summer') : 'hidden';
}

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

/** The visitor's stored Sharpness, '' when never chosen (hud.js stores '' for that). */
function readQualityPreference() {
  try {
    return JSON.parse(window.localStorage.getItem('chicago4d.settings') || '{}')?.quality ?? '';
  } catch {
    return '';
  }
}

const params = new URLSearchParams(location.search);
/**
 * The year a visitor asked for. `?year=` wins; otherwise the page's own path
 * names it — chicago.polecat.live/4d/1812/ and /4d/dev/1880/ are front doors that
 * `tools/write_entry_pages.mjs` writes for each year — and a bare /4d/ opens on
 * the target date. Other state (a structure to open, a camera) belongs in further
 * query parameters beside `year`, never in more path segments.
 */
const PATH_YEAR = (location.pathname.match(/\/(\d{4})\/?(?:index\.html)?$/) || [])[1];
const YEAR = (params.get('year') || PATH_YEAR || '1835').replace(/[^0-9a-z_-]/gi, '');
document.getElementById('view').setAttribute('aria-label', `Chicago, ${YEAR}`);
const DEBUG = params.get('debug') === '1';
// T-2109: which glass a transmissive pane is drawn with — `?glass=` when the
// address names one, otherwise the owner's pick for the detail level (glass.js).
const GLASS_REQUEST = readGlassRequest(params);
/** T-1727: `?structure=<id>&version=<label>` — one committed alternate of one structure,
 *  for comparing competing builds side by side. Null when the address asks for none. */
const VERSION_REQUEST = readVersionRequest(location.search);

const canvas = document.getElementById('view');
const gate = document.getElementById('gate');
const gateBtn = document.getElementById('gate-btn');
const gateSub = document.getElementById('gate-sub');
const gateBar = document.getElementById('gate-bar');

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
  // T-2058: `mountLiberties`'s handle. Null until the list is first needed —
  // Evidence opened, or a building card drawn — because 0.6 MB that only those
  // two read is not a cost every first visit should pay. `loadLiberties()`
  // starts it (once) and resolves to the handle.
  liberties: null,
  loadLiberties: () => Promise.resolve(null),
  welcome: { state: 'arrival', enter: () => false },
  // T-1126: the town's roll call — indexed, expected to draw, and actually
  // standing, with every absentee named. Null until the buildings are batched.
  roll: null,
  // T-1727: {requested, active, explicitDefault, notice, available, name} for
  // `?structure=&version=`, from structure-versions.js. Null until the scene loads.
  structureVersion: null,
  // T-2598: texture residency's counters (`residency`) and its handle
  // (`textureResidency`, for a tool's override). Null with `?residency=0`.
  residency: null,
  textureResidency: null,
};
window.__chicago4d = api;
// T-2657: Researcher mode, Settings › About. Read from this device before anything paints,
// so a researcher's page opens with the research already in place.
api.researcher = createResearcherMode({ storage: safeStorage() });
// The gate is up exactly when no control backend is live, so its hint row cannot wait
// for one: it follows the device's best guess (T-2045). A phone was shown W A S D and
// Esc through the whole arrival, on a failed boot, and back on the welcome.
document.body.classList.toggle('touch-first', prefersTouch());
let bootStorage;
try { bootStorage = window.localStorage; } catch { /* private mode */ }
// T-2547: if the last session died loading (a phone out of memory), this one boots a
// detail tier lower and at Sharpness Low, and says so. Resolved here, before the
// forecast and the GLB fetch, so nothing is downloaded for the tier that died.
// T-2559: the guess it steps down from is the device profile a previous visit
// cached (boot() re-reads it); a first visit guesses the platform default.
const crashGuard = createCrashGuard({ year: YEAR, order: DETAIL_ORDER });
api.crashGuard = crashGuard.state;
// A layer's positions in metres, quantized or not (T-2687, compact-streams.js):
// what the smoke's probes read, where `getAttribute('position')` now hands
// back the -1..1 the GPU sees on a quantized mesh.
api.positionsInMetres = compactStreams(THREE).positionsInMetres;
// Its confidence per vertex, wherever the layer keeps it (T-2689): what the smoke's
// probes read on a layer that keeps no float `_confidence` stream.
api.confidenceOf = compactStreams(THREE).confidenceOf;
const bootProfile = cachedDeviceProfile(bootStorage, null);
const bootGuess = bootProfile ? deviceChoice(bootProfile.cls, { touch: prefersTouch() }) : null;
const crashBoot = crashGuard.boot({
  detail: readDetailPreference() || bootGuess?.detail || (prefersTouch() ? 'light' : 'full'),
  quality: resolveSharpness(readQualityPreference(), prefersTouch(), bootGuess?.sharpness),
});
// T-2826: the page's last moments, kept for the next load (blackbox.js). A page
// that was cut off (a lost context, or a tab killed mid-visit) says on the card
// what it was doing, with the whole record a tap away for the owner's report.
let blackboxSample = () => null;
const blackbox = createBlackbox({ year: YEAR, build: document.getElementById('gate-build')?.textContent?.trim() || VERSION, sample: () => blackboxSample() });
api.blackbox = blackbox;
if (wasCut(blackbox.previous)) {
  const line = blackboxSummary(blackbox.previous);
  crashGuard.show(crashGuard.state.notice ? `${crashGuard.state.notice} ${line}` : line,
    { copyText: blackboxReport(blackbox.previous) });
}
blackbox.log('boot', { to: `${crashBoot.detail}@${crashBoot.quality}` });
window.addEventListener('pagehide', () => blackbox.end('left'));
document.addEventListener('visibilitychange', () => blackbox.log(document.hidden ? 'hidden' : 'shown'));
window.addEventListener('error', (e) => blackbox.log('error', { msg: String(e.message ?? e).slice(0, 120) }));
window.addEventListener('unhandledrejection', (e) => blackbox.log('error', { msg: String(e.reason?.message ?? e.reason).slice(0, 120) }));
const bootCell = {
  device: prefersTouch() ? 'mobile' : 'desktop',
  detail: crashBoot.detail,
  build: document.getElementById('gate-build')?.textContent || VERSION,
  storage: bootStorage,
};
const bootController = createBoot({ ...bootCell, problems });
api.boot = bootController;
// T-2164: the arrival clock forecasts the downloads too — bytes over the measured link.
const bootForecast = createForecast({ ...bootCell, boot: bootController,
  meter: createNetMeter(), bytes: expectedBytes(bootCell) });
bootController.forecast = bootForecast;
// T-2613: one journey for the page — time-stream › landing › landed › exploring …
const journey = createJourney();
// T-2621: a shared screen, read once (`?nav=app[:id]&tab=`), opened after the landing.
const navLink = parseNavLink(location.search);
api.journey = journey;
// T-2660: the field log, kept on this device only and never sent (js/field-log.js). A landing
// is the journey reaching `landed`; Settings › About shows the counts, with Clear.
journey.on(({ to }) => { if (to === 'landed') countField('landed'); });
api.fieldLog = fieldLog;
api.fieldLogView = wireFieldLogView({ log: fieldLog });
// Back to the Observatory is the journey's recall, from wherever the link sits. T-2735: the
// way home asks first and plays the reverse ring (js/recall.js), so the journey moves to
// `recall` only as the page actually leaves; a cancelled prompt leaves it where it was.
recallHome?.onReturn(() => journey.recall());
api.recall = recallHome;
// T-2614: with no gate to tap, the first tap after landing on a Home choice, the scene or a
// Navigator control is the gesture audio needs; the page's AudioContext exists only after it.
// T-2659: the Navigator's sounds (js/sound.js), off by default since T-2941. The module is fetched with the
// first gesture, or on the way in when the jump that opened the page lets audio play
// (sound.js § mayStartEarly), so it is never part of the boot payload.
const loadSound = (early = false) => (api.soundReady ??= import('./sound.js')
  .then(({ createSound }) => (api.sound = createSound({
    audio: () => gesture.audio, unlock: () => gesture.unlockAudio(), early, journey,
    settings: () => api.hud?.settings ?? null, scene: () => YEAR, navigator: () => api.navigator ?? null,
  })))
  .catch(() => { api.soundReady = null; return null; }));
const gesture = createGestureGate({ journey, tagEl: document.getElementById('look-tag'),
  onGesture: () => { void loadSound().then((sound) => sound?.sync()); } });
api.gesture = gesture;
if (document.documentElement.dataset.transfer === 'true') void loadSound(true);
Object.defineProperty(api, 'audio', { get: () => gesture.audio, enumerable: true, configurable: true });
// T-2624: the page's static words from the string table, before anything paints over them.
applyStrings(document);
// T-2658: each researched setting's "Why?" opens its bubble of 40 words at most; Researcher
// mode, which puts the button away for the full essay, closes an open one.
api.whyTips = wireWhyTips(document);
api.researcher?.onChange(() => api.whyTips.close());
const arrival = createArrival({
  boot: bootController,
  journey,
  deviceEl: gate.querySelector('.gate-card'),
  destinationEl: document.getElementById('arrival-destination'),
  announceEl: document.getElementById('arrival-announce'),
  targetDate: () => api.scene?.target_date,
  targetYear: YEAR,
  titleEl: document.getElementById('gate-title'),
  contentOptions: {
    seed: new URLSearchParams(location.search).get('seed') ?? Math.random(),
    warm: (() => { try { return sessionStorage.getItem(`c4d.loading.build.${YEAR}`) === VERSION; } catch { return false; } })(),
  },
  yearEl: document.getElementById('arrival-year'),
  phaseEl: gateSub,
  cardEl: document.getElementById('arrival-card'),
  barEl: gateBar,
  buttonEl: gateBtn,
  forecast: bootForecast,
  headlineEl: document.getElementById('arrival-headline'),
  // T-2612: the log is the telemetry's (one line per boot phase, from the deck), so the
  // arrival no longer files its status cards there.
  logEl: null,
  lampsEl: document.getElementById('arrival-lamps'),
  readoutEl: document.getElementById('arrival-readout'),
  observatoryEl: document.getElementById('gate-observatory'),
  detailsEl: document.getElementById('gate-details'),
  detailEl: document.getElementById('gate-detail'),
  onYear: year => { api.timeStream?.passYear(year); api.telemetry?.year(year); api.sound?.ticker(year); },
  onWelcome: () => api.welcome?.show(),
});
api.arrival = arrival;
// Start alongside scene loading; optional presentation never joins the ready barrier.
if (YEAR === '1835') void arrival.content?.load(new URL('loading/statuses.json', resolveBases().dataBase));
// T-2611: the time-stream captions — this destination's deck of landmark years, shown as
// the ticker passes each (3 at most on a fast load, up to 8 on a slow one). Optional:
// the fetch never joins the ready barrier, and no deck simply shows no caption.
// T-2612: YEARS TO GO, the four named lamps and the log, over the same boot.
api.telemetry = createTelemetry({ boot: bootController, targetYear: Number(YEAR) || 1835,
  lampsEl: document.getElementById('arrival-lamps'), logEl: document.getElementById('arrival-log'),
  yearsEl: document.querySelector('#arrival-readout [data-telemetry="years"]') });
api.timeStream = createTimeStream({ boot: bootController, forecast: bootForecast,
  el: document.getElementById('arrival-timestream'), sayEl: document.getElementById('arrival-timestream-say'),
  onDeck: deck => api.telemetry?.setDeck(deck) });
void api.timeStream.load(new URL(`timestream/${YEAR}.json`, resolveBases().dataBase));
bootController.on('ready', () => { try { sessionStorage.setItem(`c4d.loading.build.${YEAR}`, VERSION); } catch { /* optional */ } });
bootController.on('ready', () => crashGuard.live());
bootController.on('ready', () => blackbox.log('ready'));
const bootCheckpoint = createCheckpoint();

boot().catch((err) => {
  const active = bootController.phases.find(phase => phase.essential && phase.startedAt !== null && phase.endedAt === null);
  bootController.fail(active?.id || 'scene', err);
  api.error = String(err?.message || err);
  problems.push(`boot: ${api.error}`);
  // A year with no scene yet (a door such as /4d/1880/ that is ahead of the data)
  // is not a broken build, and should not read like one. T-2616: a year the Observatory
  // offers HAS a scene, so its scene file missing is a stalled jump, not an unbuilt year.
  const unbuilt = /^404\b/.test(api.error) && api.error.includes(`scenes/${YEAR}.json`)
    && !['1812', '1835', '1904'].includes(YEAR);
  // T-2616: the visitor reads "the jump stalled"; what failed goes under the folded details.
  arrival.fail(err, {
    message: t('arrival.fail.scene', { error: api.error }),
    headline: unbuilt ? t('arrival.fail.unbuilt', { year: YEAR }) : undefined,
  });
  console.error('[4D Chicago] boot failed', err);
});

async function boot() {
  bootController.start('scene');
  await yieldToPaint();
  const bases = resolveBases();
  const coarse = prefersTouch();
  // T-2559: read what the device offers and choose per device — see
  // device-profile.js. Before the scene is fetched, so a weak machine's tier
  // decides what is downloaded; a repeat visit reads its cached profile and pays
  // no benchmark. The touch screen still picks the controls and `lowSpec`; the
  // profile picks only the defaults below, and a stored choice beats both.
  const device = await profileDevice({ touch: coarse, build: bootCell.build, storage: bootStorage,
    search: location.search });
  api.device = device;
  // Resolve BEFORE the GLB fetch: a weak-machine boot must never download the
  // full inspection model simply to turn it down once Settings has mounted.
  // T-2547's step-down outranks everything; then the stored choice; then the
  // device profile (T-2559).
  let detailLevel = crashBoot.lowered.detail ? crashBoot.detail : (readDetailPreference() || device.choice.detail);
  api.bootDetail = detailLevel;
  /**
   * T-2598: texture residency — a house picture is on the GPU only within its tier's
   * reach of the eye and under its tier's budget (texture-residency.js). `?residency=0`
   * keeps every picture resident from boot, as before: the way the before is read.
   */
  const RESIDENCY_ON = params.get('residency') !== '0';
  let residency = null;
  const attachResidency = (group, eye, options) => {
    residency = null;
    api.residency = null;
    api.textureResidency = null;
    if (!RESIDENCY_ON) return;
    // `?residency-budget=<MiB>` overrides the tier's budget, for a tool reading what
    // the reach alone would hold.
    const budget = Number(params.get('residency-budget'));
    residency = createTextureResidency({ group, renderer, tier: detailLevel, closeImages: coarse,
      settings: budget > 0 ? { budgetBytes: budget * 1048576 } : null });
    residency.prime(eye, options);
    api.residency = residency.state;
    api.textureResidency = residency;
  };
  // Image sharpness for a visitor who never chose one: the profile's choice —
  // on a standard device the T-2110 default, Low on a phone and Medium on a
  // desktop (see sharpness.js).
  const qualityGuess = device.choice.sharpness;
  const bootQuality = crashBoot.lowered.quality ? crashBoot.quality
    : resolveSharpness(readQualityPreference(), coarse, qualityGuess);
  const detailOpts = () => ({ detail: detailLevel });

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
   * T-2716. The renderer's own `render`, taken before anything can swap it: the
   * flora's near deal pass is PLACEMENT, not a frame, and harnesses that hold or
   * time the frames by replacing `renderer.render` (the smoke's `holdDraws`,
   * `measure_walk_frames.mjs`) must neither skip it nor count it as a draw.
   */
  const placementRender = renderer.render.bind(renderer);
  /**
   * T-2970. What the GL driver receives, which is what every draw budget is held
   * to: `renderer.info.render.calls` counts a BatchedMesh's multi-draw as one call
   * where the driver gets one draw per kept instance (driver-draws.js).
   */
  const driverDraws = countDriverDraws(renderer);
  api.driverDraws = driverDraws;
  /**
   * The boot-time ratio. Note that this is superseded a few hundred lines below
   * by `renderer.setPixelRatio(Math.min(dpr, quality))` once the visitor's
   * stored settings are read. Until T-2110 the shipped default of `quality` was
   * **1.5 on both platforms**; since the owner's answer there it is the device
   * guess `qualityGuess` — **1 on a phone, 1.5 on a desktop** — and this boot
   * ratio is that same guess, so a fresh visitor's first frames are drawn at the
   * ratio they keep rather than snapping down once the HUD mounts.
   * T-0157's premise held that a phone was capped at 1.5 "rather than 2"; what
   * the renderer actually reports is 1.5 on a phone at dpr 2 and 1.0 on a
   * desktop at dpr 1, which is the phone supersampling MORE than the desktop.
   */
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, bootQuality));
  /**
   * T-2555, THE FRAME GOVERNOR (frame-governor.js). The visitor's Sharpness is
   * the CEILING: `sharpnessCap` is the ratio they chose, and the ratio drawn is
   * that times the governor's scale, which is 1 at rest and under Fixed. Every
   * place that used to set the pixel ratio sets the cap through
   * `applySharpness`, and the ratio itself is only ever written when it changes
   * — `setPixelRatio` resizes the drawing buffer even to the same size.
   */
  let sharpnessCap = renderer.getPixelRatio();
  const governorLine = document.getElementById('governor-line');
  const governor = createFrameGovernor({ tier: detailLevel, onChange: (state) => {
    if (governorLine) governorLine.textContent = describeGovernor(state, sharpnessCap * state.scale);
  } });
  function applySharpness(value) {
    if (value !== undefined) sharpnessCap = Math.min(window.devicePixelRatio || 1, value);
    const ratio = sharpnessCap * governor.scale;
    if (Math.abs(ratio - renderer.getPixelRatio()) > 1e-9) renderer.setPixelRatio(ratio);
  }
  // T-2572: a tap on the plank walks, fences and yard goods is answered by a
  // one-pixel id pass on this renderer, so a phone need not keep their triangles.
  setPickRenderer(renderer);
  // T-2582: GPU-compressed library sheets. One KTX2 loader, detected once against
  // this renderer before any layer loads (ktx2.js); the `light` texture tier drops
  // each sheet's top mip. `?ktx2=0` keeps every sheet on its image path.
  initKTX2(renderer, { textures: device.choice?.textures, disabled: params.get('ktx2') === '0' });
  api.ktx2 = ktx2State;
  // T-2599: whether procedural geometry is being built on workers, and how much.
  api.jobs = jobsState;
  // T-2547: a lost context is preventDefault'ed, said on a card, and reloads at most
  // once a session — only when the page has let go of what a restore would need.
  // T-2548: a closed building image is gone from the page as a released array is.
  crashGuard.watchContext(renderer.domElement, { needsReload: () => {
    const released = uploadReleaseState();
    return released.attributes > 0 || released.images > 0 || released.compressed > 0;
  } });
  renderer.domElement.addEventListener('webglcontextlost', () => blackbox.log('lost'));
  renderer.domElement.addEventListener('webglcontextrestored', () => blackbox.log('restored'));
  setPickLog((kind, data) => blackbox.log(kind, data));
  api.pickResources = pickResources;
  const blackboxSize = new THREE.Vector2();
  blackboxSample = () => {
    const { render, memory } = renderer.info;
    renderer.getDrawingBufferSize(blackboxSize);
    const pose = api.walker?.state;
    // T-2828: the bytes behind those counts, as far as the page can read them (MB).
    const est = residentEstimate(scene3d, renderer);
    return { calls: render.calls, draws: driverDraws.draws, tris: render.triangles, geo: memory.geometries, tex: memory.textures,
      geoMB: Math.round(est.geometry / 1048576), texMB: Math.round(est.textures / 1048576),
      w: blackboxSize.x, h: blackboxSize.y, ratio: +renderer.getPixelRatio().toFixed(2),
      heap: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : null,
      at: pose ? `${Math.round(pose.e)},${Math.round(pose.n)}` : null };
  };

  const scene3d = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(62, 1, NEAR.min, 3000);
  // T-2113. While the welcome is up the walk is held, so the town under it is
  // drawn only when something it is made of has changed — see gate-frame.js.
  const gateFrame = createGateFrame({ renderer, scene: scene3d, camera });

  // T-2693: the ground's tiles, prebuilt at publish, start downloading now so they
  // arrive under the scene phase; createTerrain uploads them in the ground GLB's
  // place when they are this page's, and loads the GLB otherwise. Never rejects.
  const groundPrebuilt = fetchPrebuiltGround({ dataBase: bases.dataBase, year: String(YEAR), build: pageBuild() });
  // T-2709: and the distant base, laid over frontage's crossings and cut at publish.
  const basePrebuilt = fetchPrebuiltBase({ dataBase: bases.dataBase, year: String(YEAR), build: pageBuild() });
  const loaded = await loadScene(YEAR, bases, {
    onProgress: (done, total) => bootController.progress('scene', done, total),
    version: VERSION_REQUEST,
    detail: detailLevel,
    // T-2548: a phone re-fetches on a detail switch rather than banking the GLB.
    keepAssetBytes: !coarse,
    // T-2598: and keeps each house picture's encoded bytes, so one that went distant
    // and had its decoded copy closed can be decoded again (texture-residency.js).
    keepEncodedImages: coarse && RESIDENCY_ON,
    // T-2597: every structure at once unless `?boot-pool=N` asks for a pool (BOOT_POOL).
    pool: bootPoolFromSearch(location.search),
  });
  const inspectionLod = hasInspectionLod(loaded.registry.get('glessner_house'));
  const detailLevels = inspectionLod ? { ...DETAIL,
    full: { ...DETAIL.full, triangles: GLESSNER_V4_FULL_TRIANGLES,
      declared: GLESSNER_V4_FULL_TRIANGLES,
      measured: 'Selected Glessner v4 inspection and T-3084 Brougham; fresh 4,654,565 at Full, priced at 4.7M. See GLESSNER_V4_FULL_TRIANGLES.' },
    light: { ...DETAIL.light, triangles: GLESSNER_V4_LIGHT_TRIANGLES,
      declared: GLESSNER_V4_LIGHT_TRIANGLES,
      measured: 'Glessner courtyard inspection; see T-2218 at GLESSNER_V4_LIGHT_TRIANGLES.' },
  } : DETAIL;
  // Which structure version the address asked for and what it got — the HUD chip and
  // the smoke both read it. A fallback is carried here as `notice`, NOT pushed onto
  // `problems`: an unknown label is the visitor's typo, not a defect in the build.
  api.structureVersion = loaded.versionState;
  bootController.end('scene');
  bootController.start('terrain');
  await yieldToPaint();
  problems.push(...loaded.problems);
  api.scene = loaded.scene;
  api.datum = loaded.datum;
  /**
   * T-1739 — WHICH OF THE TOWN'S LAYERS THIS SCENE DRAWS, from the scene file's own
   * `layers` list. Every derived layer below (the streets, the fences and the ground
   * inside them, the signs, the goods, the walks, the docks, the boats, the wells,
   * the plants and trees) and the residents' directory is authored for ONE date,
   * 1 July 1835, in directories that carry no date of their own. So a second scene
   * cannot simply inherit them: the 1904 scene on Prairie Avenue would stand an 1835
   * fence and an 1835 prairie on ground graded thirty years after the fire. A layer
   * the scene does not list is handed no data base, and each module's own "nothing
   * to draw" answer — the one it already gives a failed fetch — is what mounts, with
   * the note it would have raised kept out of `problems`, because leaving out a layer
   * the scene never asked for is not a defect. Nothing is fetched for it at all.
   */
  const sceneLayers = new Set(Array.isArray(loaded.scene.layers) ? loaded.scene.layers : []);
  const draws = (layer) => sceneLayers.has(layer);
  const layerBase = (layer) => (draws(layer) ? bases.dataBase : null);
  const layerProblems = (layer) => (draws(layer) ? problems : []);
  api.sceneLayers = [...sceneLayers];
  // T-2677: the frontage's timber, prebuilt at publish, starts downloading now so
  // it arrives under the phases ahead of the layer instead of after them. It
  // resolves `{ why }` rather than rejecting, and the layer builds its own then.
  const frontagePrebuilt = draws('frontage')
    ? fetchPrebuiltFrontage({ dataBase: bases.dataBase,
      year: String(loaded.scene.scene_id ?? loaded.scene.id ?? loaded.scene.year), build: pageBuild() })
    : null;
  // T-2710: and the road's surfaces at this detail's layout, which createStreets
  // batches instead of laying when they are this page's. Resolves `{ why }` too.
  const streetsPrebuilt = draws('streets')
    ? fetchPrebuiltStreets({ dataBase: bases.dataBase,
      year: String(loaded.scene.scene_id ?? loaded.scene.id ?? loaded.scene.year), build: pageBuild(), ...detailOpts() })
    : null;
  // T-2711: and the yards' five surfaces, which the fenced ground uploads in place
  // of laying them (yards.js § THE YARDS, PREBUILT). Never rejects.
  const yardsPrebuilt = draws('enclosures')
    ? fetchPrebuiltYards({ dataBase: bases.dataBase,
      year: String(loaded.scene.scene_id ?? loaded.scene.id ?? loaded.scene.year), build: pageBuild() })
    : null;
  /**
   * T-1740 — AND THE DRAWER FOLLOWS THE SAME LIST. The sections and Evidence topics
   * below read the 1835 town's records just as the drawn layers do — its residents,
   * its firms, its animals and plants, its census, its research record of buildings
   * left out — so the 1904 scene was offering 1,421 households of 1835, 286 of its
   * firms and its order book under a 1904 badge. Each one is now offered only by a
   * scene that lists the layer it reads; one that does not gets no tab, no tile and
   * no fetch, rather than a panel saying it failed to load.
   */
  const DRAWER_TABS = { people: 'residents', businesses: 'businesses' };
  const DRAWER_TOPICS = {
    city: 'residents', population: 'residents', orderbook: 'residents',
    fauna: 'fauna', plants: 'flora', exclusions: 'exclusions', uncertain: 'exclusions',
  };
  const notListed = (map) => Object.keys(map).filter((id) => !draws(map[id]));
  api.drawerOmitted = { tabs: notListed(DRAWER_TABS), topics: notListed(DRAWER_TOPICS) };
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
  // T-2981: public and frame statistics read the same current view/tier policy.
  const currentBudget = () => renderBudget(BUDGET, detailLevel, confidence.ghosting);
  Object.defineProperty(api, 'budget', { get: currentBudget });
  // T-2647: the furniture ghosts as a dither in the opaque pass, not in a second draw —
  // X-RAY one tap away has to fit the draw budget (confidence.js § setGhostAsDither).
  // T-2863: and so does the grown wood, since its batches hold a Reconstructed grade
  // (T-2809's fruit trees) beside the Inferred one and were drawn in both passes.
  confidence.setGhostAsDither([...FURNITURE_LAYERS, GROWN_TIMBER_LAYER]);
  // T-2647: the looks the visitor last chose (X-RAY's ghosts), before anything is drawn coloured.
  restoreLooks(confidence, safeStorage());

  // The ground, the river, and the heightfield the walker stands on, all from
  // the scene's terrain epoch. Awaited: everything after this asks it how high
  // the ground is, and a flat answer would place every building at the datum.
  const terrain = await createTerrain({
    dataBase: bases.dataBase,
    assetBase: bases.assetBase,
    epochId: loaded.scene.terrain_epoch,
    // The sand belt and the marsh are painted from the 1835 plant zones' extents.
    substrateBase: layerBase('flora'),
    sceneId: loaded.scene.id ?? YEAR,
    // T-2502: ground off the box, where the scene names one (1812: down the South Branch).
    apronPath: loaded.scene.terrain_apron ?? null,
    prebuilt: groundPrebuilt,
    prebuiltBase: basePrebuilt,
    confidence,
    problems,
  });
  if (!terrain.loaded) throw new Error('Terrain heightfield did not load');
  /** T-2693: whether the ground's tiles came prebuilt, and if not, why not. */
  api.terrainPrebuilt = terrain.prebuilt;
  /** T-2709: whether the distant base came prebuilt, and if not, why not. */
  api.terrainPrebuiltBase = terrain.prebuiltBase;
  scene3d.add(terrain.group);
  /** T-2158: on a phone, a heavy layer goes to the GPU the moment it is built
   *  and lets go of its page arrays (upload-release.js), keeping back what this
   *  tier never shows. */
  const settleOnGpu = (layer) => {
    if (!coarse) return;
    const want = DETAIL[detailLevel] ?? DETAIL.full;
    // What the reach will hold back from where the visitor stands is left for
    // the walk to upload when it comes near, as it always was.
    const reach = layer.name === 'terrain' ? want.groundDetailReachM
      : FURNITURE_LAYERS.includes(layer.name) ? want.furnitureReachM : null;
    const eye = camera.position;
    const sphere = new THREE.Sphere();
    const beyond = (o) => {
      if (typeof reach !== 'number' || !o.isMesh || !o.geometry?.attributes.position) return false;
      if (!o.geometry.boundingSphere) o.geometry.computeBoundingSphere();
      sphere.copy(o.geometry.boundingSphere).applyMatrix4(o.matrixWorld);
      return eye.distanceTo(sphere.center) - sphere.radius > reach;
    };
    layer.updateWorldMatrix(true, true);
    uploadLayerNow(renderer, scene3d, camera, layer, {
      hide: (o) => (want.crossStreetWalks === false && !!o.userData.crossStreet)
        || (want.woodpiles === false && !!o.userData.woodpiles) || beyond(o),
    });
  };
  // T-1154 — the ground's reach, set from the fog the world just made rather
  // than from a literal here, so a scene that changes its haze moves the reach
  // with it and the two can never drift apart. See terrain.js hazeReachM().
  terrain.setGroundReach(hazeReachM(scene3d.fog?.density ?? 0));
  bootController.end('terrain');
  bootController.start('buildings', loaded.registry.size);
  await yieldToPaint();
  // T-2529: one switch for every structure batch, old and rebuilt alike; the
  // detail tier sets it (applyShadowTier) and the sun is read when the shadow
  // map is drawn. See shadow-casters.js for the test and the reading behind it.
  const shadowCasters = { on: false, culled: 0, sun: () => world.direction,
    light: () => world.light, fresh: () => detailLevel === 'full' && governor.shadowFresh };
  let buildings = await createBuildings({ registry: loaded.registry, confidence, terrain,
    shadowCasters,
    preserveMaterials: inspectionLod,
    // T-3012: every tier collects them now, Full too (refreshGlessnerOcclusion says
    // why). Balanced draws without the filter but keeps them, because a Balanced ->
    // Light switch keeps the same asset and batches and Light filters with them.
    collectViewBackings: inspectionLod,
    // Balanced and Light share the reduced asset and its batches. Keep their
    // cells identical so a same-asset Balanced -> Light switch stays culled.
    spatialCells: inspectionLod && detailLevel !== 'full' ? { cellM: 4, heightM: 2 } : null,
    lowSpec: coarse,
    glass: glassForDetail(detailLevel, GLASS_REQUEST),
    checkpoint: bootCheckpoint,
    onProgress: (done, total) => bootController.progress('buildings', done, total),
  });
  problems.push(...buildings.problems);
  scene3d.add(buildings.group);
  // T-2598: before anything is uploaded, each house picture farther than its tier's
  // reach from where the visitor will arrive is swapped for its stand-in, so it never
  // goes up at all; the walk brings it in when it comes near (texture-residency.js).
  {
    // Where the walker will stand: the walker is made after the batches, and its
    // height is the terrain's, so this first decision reads plan distance only.
    const at = anchorFor(loaded.scene, params.get('anchor')) ?? loaded.scene.spawn ?? {};
    attachResidency(buildings.group, enuToWorld(at.local_e ?? 0, at.local_n ?? 0), { flat: true });
  }
  settleOnGpu(buildings.group);
  // T-2548: once the batch holds its copy and the GPU its maps, a phone lets go
  // of the source geometry and the decoded images (upload-release.js).
  if (coarse) {
    releaseSources(loaded.registry);
    closeUploadedImages(buildings.group, renderer);
  }
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
  // T-2976 — ground a building lays below the field (Glessner's sunk carriage way):
  // the field is cut out over it and the walk steps down onto its paving.
  const passageGround = passageGroundFrom(loaded.registry);
  terrain.setPassageGround?.(passageGround);
  // T-1797 — the ground-strip proof, drawn only under `?proof=ground`. Its
  // module is not imported otherwise, so the walk without the flag is untouched.
  // Its three vantage points join the scene's anchors for this run.
  const groundProof = params.get('proof') === 'ground' ? await import('./ground-strip.js') : null;
  if (groundProof && Array.isArray(loaded.scene.anchors)) {
    loaded.scene.anchors.push(...groundProof.STRIP_ANCHORS);
  }
  const spawn = anchorFor(loaded.scene, params.get('anchor'))
    ?? groundProof?.STRIP_ANCHORS[0] ?? loaded.scene.spawn ?? {};
  const walker = createWalker({ camera, terrain, footprints, decks, spawn });
  walker.apply();
  // From where the visitor will stand, so the ground's reach can be read.
  settleOnGpu(terrain.group);

  // The dated street layer is a skin on the heightfield, never a replacement
  // for it.  Mount it before vegetation so the travelled strips can clear only
  // the plants that would otherwise grow through the visible wagon tracks.
  // T-2600: its surfaces are partitioned on the job pool, so the layer resolves.
  // T-2710: measured as `streets`, the wall time measure_boot_phases.mjs quotes.
  performance.mark('streets:start');
  const streets = await createStreets({
    terrain,
    records: draws('streets') ? (loaded.index?.streets ?? []) : [],
    confidence,
    ...detailOpts(),
    prebuilt: streetsPrebuilt,
    sceneId: loaded.scene.scene_id ?? loaded.scene.id ?? loaded.scene.year,
  });
  performance.measure('streets', 'streets:start');
  /** T-2710: whether the streets came prebuilt, and if not, why not. */
  api.streetsPrebuilt = streets.prebuilt;
  scene3d.add(streets.group);
  settleOnGpu(streets.group);
  if (groundProof) {
    api.groundStrip = await groundProof.createGroundStrip({
      terrain, assetBase: bases.assetBase, problems,
    });
    scene3d.add(api.groundStrip.group);
  }

  // T-0474 — the 1904 Prairie Avenue grid: carriageways curb to curb, each block
  // face's margin, walk, parkway and curb, the alleys and the lot lines, read off
  // the Sanborn 1911 sheets (data/street_grid/<scene>.json). Only a scene listing
  // `street_grid` is handed a data base, so the 1835 town draws none of it.
  // T-1728 paves it: data/street_surfaces/<scene>.json names each surface's
  // material and tier, and the maps come from the asset base's
  // textures/prairie_1904_pbr/ (data/textures/ on the published site).
  const streetGrid = await createStreetGrid({
    dataBase: layerBase('street_grid'), assetBase: bases.assetBase, sceneId: loaded.scene.id ?? YEAR,
    terrain, confidence, problems: layerProblems('street_grid'),
  });
  scene3d.add(streetGrid.group);
  api.streetGrid = streetGrid;
  streetGrid.setLotLines(readLotLinesPreference());

  // T-2473 — the parkway elms of the 1904 district (data/street_trees/<scene>.json),
  // built with trees.js's own tree and drawn as one instanced batch. Only a scene
  // listing `street_trees` is handed a data base. The Season and Street trees
  // settings (T-2481) are read here so the first frame already shows the visitor's pick.
  const seasonPref = readSeasonPreference();
  // T-2477 — the context city: faded stand-ins on every part of the 1904 map not yet
  // built (data/context/<scene>.json, read off the Sanborn sheets where they reach and
  // projected past them), so Prairie Avenue reads in full colour against a sketch of the
  // city around it. Each gives way to any placed structure whose footprint it touches.
  // Built before the parkway elms, which draw its trees as their own (T-2833).
  let contextCity = await createContext({
    dataBase: layerBase('context'), sceneId: loaded.scene.id ?? YEAR, terrain, footprints,
    confidence, problems: layerProblems('context'), detail: detailLevel,
  });
  scene3d.add(contextCity.group);
  api.contextCity = contextCity;
  const streetTrees = await createStreetTrees({
    dataBase: layerBase('street_trees'), sceneId: loaded.scene.id ?? YEAR, terrain, confidence,
    problems: layerProblems('street_trees'), lowSpec: coarse,
    mode: streetTreeMode(seasonPref.season, seasonPref.treesShown),
    checkpoint: bootCheckpoint, levelAt: streetGrid.offsetAt ?? null, ...detailOpts(),
    contextTrees: (level) => contextCity.treeStems?.(level) ?? [],
  });
  scene3d.add(streetTrees.group);
  api.streetTrees = streetTrees;
  // T-3199 — the district's street furniture (data/street_furniture/<scene>.json): the gas
  // lamps at every corner and along the parkways, instanced, standing on the parkway's fall
  // toward the curb. Only a scene listing `street_furniture` is handed a data base.
  const streetFurniture = await createStreetFurniture({
    dataBase: layerBase('street_furniture'), sceneId: loaded.scene.id ?? YEAR, terrain, confidence,
    problems: layerProblems('street_furniture'), levelAt: streetGrid.offsetAt ?? null, ...detailOpts(),
  });
  scene3d.add(streetFurniture.group);
  api.streetFurniture = streetFurniture;
  // T-3203 — the house lots' front yards (data/front_yards/<scene>.json): a mown lawn to each
  // house, foundation shrubs along it, low beds, and ivy where a picture shows it; laid clear
  // of every stoop, walk, fence and door's way the houses' own models draw.
  const frontYards = await createFrontYards({
    dataBase: layerBase('front_yards'), sceneId: loaded.scene.id ?? YEAR, terrain, confidence,
    problems: layerProblems('front_yards'), levelAt: streetGrid.offsetAt ?? null, ...detailOpts(),
    // T-3223: grown as the parkway elms are, on their leaf and bark atlases, in the Season.
    grownMaterials: streetTrees.materials ?? null, lowSpec: coarse, checkpoint: bootCheckpoint,
    mode: SEASON_TREE_MODE[seasonPref.season] ?? 'summer',
  });
  scene3d.add(frontYards.group);
  api.frontYards = frontYards;


  // T-2478 — the Illinois Central along the lake east of Prairie Avenue: the tracks
  // the 1911 sheets draw, on cinder ballast, with ties, rails and weedy verges
  // (data/railway/<scene>.json; maps from textures/prairie_1904_rail/). Only a scene
  // listing `railway` is handed a data base.
  const railway = await createRailway({
    dataBase: layerBase('railway'), assetBase: bases.assetBase, sceneId: loaded.scene.id ?? YEAR,
    terrain, confidence, problems: layerProblems('railway'), ...detailOpts(),
    // Newly reached rail zones are marked before their next draw. This only
    // installs upload callbacks; it does not render from inside update().
    onGeometry: coarse ? (group) => releaseAfterUpload(group) : undefined,
  });
  scene3d.add(railway.group);
  api.railway = railway;
  // T-2775: on a phone the yard goes to the GPU now and lets go of its page arrays,
  // with the zones near the spawn already deciding which rails they draw.
  railway.update(camera);
  settleOnGpu(railway.group);

  let glessnerOcclusion=null;
  function refreshGlessnerOcclusion() {
    glessnerOcclusion?.dispose();glessnerOcclusion=null;
    // T-3012: Full as well as Light. From Calumet's east walk at 20th, looking north,
    // Glessner stands about 290 m off behind the Calumet houses and their elms, in the
    // frustum and hidden from it, and its full master still went to the colour pass
    // whole: 1,421,694 of the frame's 4,739,066 triangles against Full's 4,600,000. The
    // filter is the one Light has carried since T-2227, unchanged: a piece is left out
    // only when its whole box projects inside one opaque building triangle and behind
    // it, and the sun's pass is not filtered. With it, 2,921,468. Filter off against on
    // at eight stands, five of them round Glessner: seven pixel-identical, one with 3
    // pixels of 1,024,000 a few levels apart on its shaded granite. Costs about 8 MB of
    // heap for Full's backing triangles. Balanced shares Light's asset and stands inside
    // its ceiling without it. Receipts: docs/RESEARCH/calumet-walk-budget-3012/.
    if (!inspectionLod || detailLevel==='balanced') return;
    const batches=[...buildings.batches];
    for(const group of [railway.group,terrain.group,streets.group])
      group.traverse(o=>{if(o.isBatchedMesh)batches.push(o);});
    glessnerOcclusion=createViewOcclusion({camera,renderer,triangles:buildings.viewOccluders,batches,
      // T-3152: Glessner's flat backings, the cells of each proven covered (planar-occluders.js).
      planes:buildings.planarCovers??[],
      // Each backing triangle checks its own actual confidence range. Tinting
      // opaque stone is safe; a hidden or dithered backing fails open.
      // The pixel proof covers the scene's July appearance. Winter's on/off
      // comparison has a repeatable raster difference; alternate seasons retain
      // the complete draw list, then summer can safely restore this filter.
      allow:()=>buildings.group.visible && api.season?.current==='summer'});
  }

  // T-2481 — the Season setting: the ground's snow, sward and leaves (season.js
  // uniforms), the elms, the context city's crowns and the sun's date. A viewing
  // choice; the scene keeps its own date. T-2864 offers it in every year, and the
  // woods and the prairie take it too (`seasonPlants`, set once they are planted).
  const seasonal = true;
  const seasonState = { season: 'summer', treesShown: seasonPref.treesShown };
  let structuresSeasoned = false;
  let seasonPlants = () => null;
  const applySeason = async (season) => {
    const s = seasonal && SEASONS.includes(season) ? season : 'summer';
    // The lawns, steps and roofs inside the building GLBs take the season too.
    // Their materials learn it the first time a season other than summer is
    // chosen, so a summer visit compiles nothing for it.
    if (s !== 'summer' && !structuresSeasoned) {
      structuresSeasoned = true;
      scene3d.traverse((o) => {
        if (!o.isMesh) return;
        for (const m of [].concat(o.material)) if (m?.name === 'merged') patchSeason(m);
      });
      // The faded city's roofs and streets, and the railway's ballast, the same way.
      for (const g of [contextCity.group, railway.group]) g.traverse((o) => {
        if (!o.isMesh || /crowns/.test(o.name)) return;
        for (const m of [].concat(o.material)) if (m && !m.transparent) patchSeason(m, /street/.test(o.name) ? 0.3 : 1);
      });
      // T-2864: the earth roads of 1812 and 1835 (streets.js), as a travelled roadway.
      streets.group.traverse((o) => {
        if (o.isMesh) for (const m of [].concat(o.material)) patchSeason(m, 0.3);
      });
    }
    seasonState.season = applySeasonLook(s);
    world.setSunDate(seasonDate(s, loaded.scene.target_date));
    contextCity.setSeason?.(s);
    await seasonPlants(s);
    await frontYards.setSeason?.(SEASON_TREE_MODE[s] ?? 'summer');
    return streetTrees.setMode(streetTreeMode(s, seasonState.treesShown));
  };
  if (seasonal && seasonPref.season !== 'summer') await applySeason(seasonPref.season);
  api.season = {
    get current() { return seasonState.season; },
    set: (s) => applySeason(s),
    get sunDate() { return world.sunDate; },
  };

  // WHICH DETAIL LEVEL, resolved here rather than beside the vegetation because
  // the fence layer is the first thing that needs it: a pale is 10 triangles at
  // `full` and 4 at `light` (T-0067), so the level has to be known before the
  // first fence is built. A phone starts at `light` and a desktop at `full`; the
  // visitor's own choice, once made, outranks the guess and is what
  // `hud.settings.detail` carries.

  // The town's fence lines — yards, pens, garden pickets. An enclosure takes a
  // PERIMETER rather than a footprint and is roofless, which is why it is not a
  // structure record and carries no GLB: docs/LIBERTIES.md L10 and L60 have both
  // been waiting on exactly that shape, and this is the half of it that needs no
  // bake. Mounted after the streets so a frontage fence is drawn against the
  // travelled way it stands on, and before the vegetation because the ground
  // inside one now decides what may grow there — see the fenced ground below.
  // T-2711: hashed as they are read when the yards may come prebuilt from them.
  const enclosureHashes = yardsPrebuilt && globalThis.crypto?.subtle ? new Map() : null;
  const enclosures = await createEnclosures({
    dataBase: layerBase('enclosures'), terrain, confidence, problems: layerProblems('enclosures'), ...detailOpts(),
    hashes: enclosureHashes,
  });
  scene3d.add(enclosures.group);
  settleOnGpu(enclosures.group);
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
  performance.mark('yards:start');
  const yards = await createFencedGround({
    records: enclosures.records, terrain, confidence, problems,
    prebuilt: yardsPrebuilt, recordHashes: enclosureHashes,
    supportRegions: draws('standing_horses') ? (loaded.scene.static_support_regions ?? []) : [],
  });
  performance.measure('yards', 'yards:start');
  scene3d.add(yards.group);
  settleOnGpu(yards.group);
  api.yards = yards;

  // The boards the businesses hung out over the footway. Like a fence, a
  // signboard is derived geometry rather than baked geometry — a plank on a
  // bracket hanging off a wall the GLBs already draw — so it needs no bake
  // either (T-0039). Mounted after the buildings it hangs on, and its height is
  // measured from the same wall base `buildings.js` anchors them at.
  const signage = await createSignage({
    dataBase: layerBase('signage'), terrain, confidence, problems: layerProblems('signage'), hostMissing,
    assetBase: bases.assetBase, lowSpec: coarse,
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
  const parkedDrawingBuffer = new THREE.Vector2();
  const parkedTransport = await createParkedTransport({
    dataBase: layerBase('parked_transport'), sceneId: YEAR, terrain, confidence,
    detail: detailLevel, problems: layerProblems('parked_transport'), hostMissing,
    groundHeight: String(YEAR) === '1904' ? (e, n) => streetGrid.carriagewayHeight(e, n) : null,
    getDrawingBufferHeight: () => renderer.getDrawingBufferSize(parkedDrawingBuffer).y,
  });
  scene3d.add(parkedTransport.group);
  api.parkedTransport = parkedTransport;
  const standingHorses = await createStandingHorses({
    dataBase: layerBase('standing_horses'), sceneId: YEAR, confidence, detail: detailLevel,
    problems: layerProblems('standing_horses'), hostMissing,
    groundHeight: (e, n, recordId, regionId) => yards.drawnBaseHeightAt(e, n, recordId, regionId),
  });
  scene3d.add(standingHorses.group); settleOnGpu(standingHorses.group);
  api.standingHorses = standingHorses;
  standingHorses.update(camera);
  const yard = await createYardGoods({
    dataBase: layerBase('yard_goods'), terrain, confidence, problems: layerProblems('yard_goods'), hostMissing,
    lowSpec: coarse,
    replacementIds: parkedTransport.replacementIds,
  });
  scene3d.add(yard.group);
  settleOnGpu(yard.group);
  api.yard = yard;
  parkedTransport.setFallback((id, visible) => yard.setReplacementVisible(id, visible));
  parkedTransport.update(camera);

  // The frontage works — the plank walks along a building's street walls, the
  // board crossing over the road and the named board on its post at the corner
  // (T-0082). Derived geometry like the fences, the boards and the goods, so it
  // needs no bake — but it is the first layer derived from a building AND a
  // street at once: where a walk may lie is decided by the travelled track's own
  // half-width out of data/streets/1835.json. Mounted after the yard because the
  // two divide one building's ground between them — the yard layer owns what
  // stands on its own lot and this owns what lies in the street outside it.
  performance.mark('frontage:start');
  const frontage = await createFrontage({
    dataBase: layerBase('frontage'), terrain, confidence, problems: layerProblems('frontage'), hostMissing,
    prebuilt: frontagePrebuilt,
  });
  // Read by tools/measure_boot_phases.mjs: the layer has no boot phase of its own.
  performance.measure('frontage', 'frontage:start');
  scene3d.add(frontage.group);
  settleOnGpu(frontage.group);
  api.frontage = frontage;
  // T-2600: the distant base's cells are cut on the job pool. T-2709: unless it
  // came prebuilt, when it is already the batch and this resolves false at once.
  performance.mark('distant-base:start');
  await terrain.batchDistantGround();
  // Read by tools/measure_boot_phases.mjs, beside the frontage measure above.
  performance.measure('distant-base', 'distant-base:start');
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
    dataBase: layerBase('wharves'), terrain, confidence, problems: layerProblems('wharves'),
  });
  scene3d.add(wharves.group);
  api.wharves = wharves;

  // T-1771 — the working bank: South Water's river side as trodden earth and
  // mud, a haul apron behind every landing the wharf layer just drew, sward
  // only in the unworn patches. Mounted after the wharves because the aprons
  // lead off their decks, and before the planters, which it tells where not to
  // grow (`workingBank.blocksGrowth` / `blocksTrees` below).
  const workingBank = await createWorkingBank({
    dataBase: layerBase('wharves'), terrain,
    streetRecords: draws('streets') ? (loaded.index?.streets ?? []) : [],
    wharves: wharves.wharves, confidence, problems: layerProblems('wharves'),
    ...detailOpts(),
  });
  scene3d.add(workingBank.group);
  api.workingBank = workingBank;

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
    dataBase: layerBase('boats'), terrain, confidence, problems: layerProblems('boats'),
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
    dataBase: layerBase('wells'), terrain, confidence, problems: layerProblems('wells'),
  });
  scene3d.add(wells.group);
  api.wells = wells;

  // The colours on the fort's flagstaff (T-2124): hung from the staff the
  // buildings drew, at the pattern and grade the staff's own record carries
  // (`flag`, `flag_flying`). One draw call a flag, moved in the vertex shader.
  const flags = createFlags({ registry: loaded.registry, buildings, confidence, problems });
  scene3d.add(flags.group);
  api.flags = flags;

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
    // The sunk carriage way (T-2976): paving under the field, which nothing grows through.
    passageGround.map((g) => ({ id: g.id, pts: g.pts })),
    // The camps' ground (T-1803), which the walker crosses and the sward does not:
    // a bush rooting between the tents, or a tree through a wall tent, was the
    // first thing the bank showed once the canvas stood on it.
    footprintsFrom(loaded.registry, { camps: true }),
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
  BUDGET.triangles = detailLevels[detailLevel].triangles;

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
    shadowCasters.on = want.castersTowardView === true;
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
    return { reachM: want.shadowReachM, furnitureCastsShadow: casts,
      castersTowardView: shadowCasters.on };
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
        // A woodpile mesh its tier does not draw (T-1959) is neither the reach's
        // nor the far merge's to show again.
        if (o.parent?.userData.woodpiles && !o.parent.visible) return;
        // …and the same for a cross street's walk at a tier that leaves the
        // cross streets out (T-0192, `light.crossStreetWalks`).
        if (o.userData.crossStreet && !o.visible) return;
        // The merged far batches (T-0146) are drawn FROM these chunks, not
        // alongside them: banking one would have the reach culling a batch and
        // the batch drawing the chunks the reach had just culled.
        if (o.userData.farMerged || o.userData.farWalkTops) return;
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
    // T-1959: the woodpiles' group is shown or hidden by the tier, BEFORE the
    // furniture is banked, so a hidden one is never banked (see `light.woodpiles`).
    scene3d.getObjectByName('yard')?.traverse((o) => {
      if (o.userData.woodpiles) o.visible = want.woodpiles !== false;
    });
    // T-0192: the cross streets' plank walks, by the same mechanism and for the
    // same reason — hidden BEFORE the furniture is banked, so the reach and the
    // far merge never show one again.
    scene3d.getObjectByName('frontage')?.traverse((o) => {
      if (o.userData.crossStreet) o.visible = want.crossStreetWalks !== false;
    });
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
    // Ground-hugging walk tops survive only their source chunk's reach cull.
    // The tier exclusion is explicit: a stale cull flag must not resurrect a
    // cross-street walk after switching to light.
    frontage.updateFarWalks?.(camera,
      (DETAIL[detailLevel] ?? DETAIL.full).crossStreetWalks !== false);
  }
  applyFurnitureReach(detailLevel);
  /** T-1976 — the ground's half of the tier: how far the detailed tiles reach
   *  before the 15 m base carries the ground alone. Null is terrain.js's own. */
  function applyGroundDetailReach(level) {
    return terrain.setDetailReach((DETAIL[level] ?? DETAIL.full).groundDetailReachM);
  }
  applyGroundDetailReach(detailLevel);

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
  const stripBlocks = api.groundStrip?.blocksGrowth ?? null;
  // T-2715: the two halves the near field tile asks apart (flora.js
  // `nearField.atTexel`). The streets' track — the track and 0.65 m either side,
  // always wider than a texel's diagonal — at the texel's corners; the yards,
  // the ground strip and the worked bank (which answers a texel at a time
  // already) at its centre. Fort Dearborn's fences are thinner than a texel, so
  // corners alone would miss them.
  const swardEdges = (e, n) => streets.blocksGrowth(e, n);
  const swardPatch = (e, n) => yards.suppressesSward(e, n)
    || (stripBlocks !== null && stripBlocks(e, n)) || workingBank.blocksGrowth(e, n);
  const swardBlocked = (e, n) => swardEdges(e, n) || swardPatch(e, n);
  // The trees give way to the travelled track, as before, and since T-1771 to
  // the worked river bank: no willow on a dock approach. The fences above still
  // do not reach them, for the reason given there.
  const treesBlocked = (e, n) => streets.blocksGrowth(e, n) || workingBank.blocksTrees(e, n);
  // T-2094. Past the cleared track the rest of an opened street's corridor is
  // trodden: flora.js crops a turf community's tall plants there to the turf's
  // own height (`streets.verge` says where; the zone record says how tall).
  // T-2086 — THE KEPT YARDS. The forb layer alone stands back inside a lot's
  // kept ring (the yard layer carries the record), and a stated share of its
  // weeds is re-seated in the strip along the lot lines; the back corners and
  // the foot of an outbuilding keep theirs where they stood.
  const kept = keptGround((yard.records ?? []).find((r) => r.id === 'town_kept_ground') ?? null);
  api.keptGround = kept;
  const forbSeat = kept.forbSeat;

  let floraUnits = 0, floraDone = 0, treeDone = 0;
  const plantingProgress = (done, total) => {
    if (done === 0) floraUnits += total;
    else floraDone++;
    bootController.progress('flora', floraDone, floraUnits);
  };
  let flora = await createFlora({
    checkpoint: bootCheckpoint,
    dataBase: layerBase('flora'), terrain, footprints: planting, sceneId: loaded.scene.id ?? YEAR,
    growthBlocked: swardBlocked, growthEdges: swardEdges, growthPatch: swardPatch,
    verge: streets.verge, forbSeat,
    confidence, problems: layerProblems('flora'), ...detailOpts(), renderer, placementRender,
  });
  scene3d.add(flora.group);
  let trees = await createTrees({
    checkpoint: bootCheckpoint,
    onProgress: (done, total) => {
      if (done === 0 && treeDone === 0) floraUnits = total;
      floraDone += done - treeDone; treeDone = done;
      bootController.progress('flora', floraDone, floraUnits);
    },
    dataBase: layerBase('flora'), terrain, footprints: planting, sceneId: loaded.scene.id ?? YEAR,
    growthBlocked: treesBlocked,
    confidence, problems: layerProblems('flora'), pixelsPerRadian,
    streetRecords: draws('streets') ? (loaded.index?.streets ?? []) : [],
    // Which sward a point stands in, so the woody layer plants the lakeshore
    // poplars on the ground the beach is actually drawn on rather than carrying
    // a second copy of the zone extents (ROADMAP K45(b) change one). Both call
    // sites build the sward first, and a dead `flora` would answer null, which
    // plants no dune rather than planting one somewhere invented.
    zoneAt: (e, n) => flora.zoneAt(e, n),
    ...detailOpts(),
  });
  scene3d.add(trees.group);
  settleOnGpu(trees.group);
  /**
   * T-2864 — the Season on the plants: the sward and its forbs (flora.js, one
   * Lambert family) and the woods (trees.js setSeason: the grown trees re-grown
   * with the season's crown, the thickets' and far band's leaves recoloured). The
   * colour is installed only once a season other than summer is chosen, so a
   * summer visit compiles and draws what it did. Read through `flora` and `trees`
   * as they stand, so a detail rebuild's new layers take it the same way.
   */
  seasonPlants = (s) => {
    const on = s !== 'summer';
    if (on) {
      flora.group.traverse((o) => {
        if (!o.isMesh) return;
        for (const m of [].concat(o.material)) {
          if (m?.isMeshLambertMaterial && m.vertexColors) patchFoliage(m, FOLIAGE.grass, { xz: 'vChiPW.xz' });
        }
      });
    }
    return trees.setSeason?.(SEASON_CROWN[s] ?? {}, { foliage: on ? (m, role) => patchFoliage(m, role) : null });
  };
  if (seasonState.season !== 'summer') await seasonPlants(seasonState.season);
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
  // The one opt-in structure whose geometry changes with Settings. Everything
  // is prepared off-scene, then committed in one turn so no empty lot or mismatched
  // budget is rendered between the two. Ordinary scenes keep their existing path.
  const discardDetail = (next) => {
    next.buildings?.dispose();
    next.contextCity?.dispose?.();
    next.flora?.dispose?.();
    next.trees?.dispose?.();
    if (next.asset) disposeLoadedAsset(next.asset.gltf);
    for (const gltf of next.reread ?? []) disposeLoadedAsset(gltf);
  };
  /**
   * T-2548: a phone let go of every building's source geometry once its batch
   * held a copy, so a rebuild re-reads the GLBs of the rows it released — the
   * HTTP cache answers — into the candidate registry. The gltfs those rows held
   * are retired at commit (`next.retired`), the ones read here at discard.
   */
  const rereadReleased = async (next, skipId) => {
    next.reread = [];
    next.retired = [];
    const rows = [...next.registry.values()].filter((row) => row.sourceReleased && row.id !== skipId);
    const got = await Promise.allSettled(rows.map((row) => loaded.loadDetailAsset(row, row.assetDetail)));
    got.forEach((r) => { if (r.status === 'fulfilled') next.reread.push(r.value.gltf); });
    const failed = got.find((r) => r.status === 'rejected');
    if (failed) throw failed.reason;
    rows.forEach((row, i) => {
      next.retired.push(row.gltf);
      Object.assign(row, got[i].value, { node: null, instanceId: null, sourceReleased: false });
    });
  };
  const inspectionSwitch = inspectionLod ? createLatestDetailSwitch({
    initial: detailLevel,
    async prepare(level) {
      const next = {};
      try {
        const record = loaded.registry.get('glessner_house');
        if (String(detailAssetUrl(record, level, bases)) !== record.assetUrl) {
          next.asset = await loaded.loadDetailAsset(record, level);
          if (next.asset.assetIsPlaceholder) throw new Error('the requested detail asset is a placeholder');
          next.registry = new Map([...loaded.registry].map(([id, row]) => [id, { ...row }]));
          Object.assign(next.registry.get(record.id), next.asset,
            { node: null, instanceId: null, sourceReleased: false });
          await rereadReleased(next, record.id);
          // Reapply the requested glass when swapping the full/light asset.
          // T-2183 defaults both to dark; an explicit comparison stays selected.
          next.buildings = await createBuildings({ registry: next.registry, confidence, terrain,
            shadowCasters,
            checkpoint: bootCheckpoint, preserveMaterials: true, lowSpec: coarse,
            collectViewBackings: true,
            spatialCells: level !== 'full' ? { cellM: 4, heightM: 2 } : null,
            glass: glassForDetail(level, GLASS_REQUEST) });
          if (next.buildings.problems.length || next.buildings.roll.missing.length) {
            throw new Error(next.buildings.problems.join('; ') || 'the replacement did not draw every structure');
          }
          next.buildings.setWeathering(buildings.weathering);
          next.buildings.group.visible = buildings.group.visible;
        }
        // The background city selects a nearer ring at Light during creation.
        // Rebuild at that boundary too: otherwise entering Light retains the
        // larger ring from boot and can exceed the phone's frame allowance.
        if ((level === 'light') !== (detailLevel === 'light')) {
          const contextProblems = [];
          next.contextCity = await createContext({
            dataBase: layerBase('context'), sceneId: loaded.scene.id ?? YEAR,
            terrain, footprints, confidence, problems: contextProblems, detail: level,
          });
          if (contextProblems.length) throw new Error(contextProblems.join('; '));
          next.contextCity.group.visible = contextCity.group.visible;
        }
        next.flora = await createFlora({
          dataBase: layerBase('flora'), terrain, footprints: planting, sceneId: loaded.scene.id ?? YEAR,
          growthBlocked: swardBlocked, growthEdges: swardEdges, growthPatch: swardPatch,
          verge: streets.verge, forbSeat,
          confidence, problems: layerProblems('flora'), detail: level, renderer, placementRender,
        });
        next.trees = await createTrees({
          dataBase: layerBase('flora'), terrain, footprints: planting, sceneId: loaded.scene.id ?? YEAR,
          growthBlocked: treesBlocked,
          confidence, problems: layerProblems('flora'), pixelsPerRadian,
          streetRecords: draws('streets') ? (loaded.index?.streets ?? []) : [],
          zoneAt: (e, n) => next.flora.zoneAt(e, n), detail: level,
        });
        return next;
      } catch (error) { discardDetail(next); throw error; }
    },
    commit(next, level) {
      if (next.buildings) {
        const previous = buildings;
        const oldAsset = loaded.registry.get('glessner_house').gltf;
        // Keep the public registry and each record object stable. The new batch's
        // pick map is pointed at those same objects after the atomic replacement.
        for (const [id, row] of next.registry) {
          const original = loaded.registry.get(id);
          Object.assign(original, row);
          next.registry.set(id, original);
        }
        buildings = next.buildings;
        scene3d.add(buildings.group);
        scene3d.remove(previous.group);
        api.buildings = buildings;
        api.roll = buildings.roll;
        residency?.dispose();
        previous.dispose();
        disposeLoadedAsset(oldAsset);
        attachResidency(buildings.group, camera.position);
        for (const gltf of next.retired ?? []) disposeLoadedAsset(gltf);
        if (coarse) {
          settleOnGpu(buildings.group);
          releaseSources(loaded.registry);
          closeUploadedImages(buildings.group, renderer);
        }
      }
      if (next.contextCity) {
        const previous = contextCity;
        contextCity = next.contextCity;
        scene3d.add(contextCity.group);
        scene3d.remove(previous.group);
        api.contextCity = contextCity;
        previous.dispose();
      }
      if (next.buildings || next.contextCity) {
        // New materials must inherit the selected seasonal view too.
        structuresSeasoned = false;
        void applySeason(seasonState.season);
      }
      loaded.registry.get('glessner_house').assetDetail = level;
      const previousFlora = flora;
      const previousTrees = trees;
      flora = next.flora;
      trees = next.trees;
      scene3d.add(flora.group, trees.group);
      scene3d.remove(previousFlora.group, previousTrees.group);
      previousFlora.dispose?.();
      previousTrees.dispose?.();
      api.flora = flora;
      api.trees = trees;
      if (seasonState.season !== 'summer') void seasonPlants(seasonState.season).then(() => gateFrame.invalidate());
      detailLevel = level;
      blackbox.log('detail', { to: level });
      residency?.setTier(level);
      BUDGET.triangles = detailLevels[level].triangles;
      enclosures.setDetail?.(level);
      // T-2600: the road's new cells are cut on the job pool and swapped in when
      // they land, after this commit; a phone lets go of their page arrays then.
      const streetsRebuilt = streets.setDetail?.(level);
      void streetTrees.setDetail(level);
      streetFurniture.setDetail(level);
      frontYards.setDetail(level);
      railway.setDetail(level);
      refreshGlessnerOcclusion();
      api.humans?.setTier(level);
      void parkedTransport.setTier(level);
      void standingHorses.setTier(level);
      applyShadowTier(level);
      applyFurnitureReach(level);
      applyGroundDetailReach(level);
      if (coarse) releaseAfterUpload(scene3d);
      void Promise.resolve(streetsRebuilt).then((rebuilt) => {
        if (rebuilt && coarse) releaseAfterUpload(scene3d);
      }, (error) => {
        problems.push(`streets: the ${level} road could not be laid: ${error?.message ?? error}`);
        console.error('[4D Chicago] streets detail', error);
      });
      confidence.set(confidence.enabled);
      hud.say(`${level[0].toUpperCase()}${level.slice(1)} detail loaded.`);
    },
    discard: discardDetail,
    onError(error, wanted, retained) {
      const message = `Could not load ${wanted} detail; keeping ${retained}. ${error.message}`;
      problems.push(`Glessner v4 detail: ${message}`);
      console.error(`[4D Chicago] ${message}`);
      hud.say(message, 9000);
      hud.settings.detail = retained;
      const select = document.getElementById('s-detail');
      if (select) select.value = retained;
      try { window.localStorage.setItem('chicago4d.settings', JSON.stringify(hud.settings)); } catch { /* optional */ }
    },
  }) : null;
  async function applyDetail(level) {
    if (inspectionSwitch) {
      if (!DETAIL[level]) return false;
      if (level !== detailLevel) hud.say(`Loading ${level} detail…`, 9000);
      return inspectionSwitch.set(level);
    }
    if (!DETAIL[level] || level === detailLevel) return;
    detailLevel = level;
    blackbox.log('detail', { to: level });
    residency?.setTier(level);
    BUDGET.triangles = detailLevels[level].triangles;
    // The fence's half of the level, first: `light` draws a pale as a plank and
    // the other two as a prism (T-0067), and the layer rebuilds its own meshes
    // in place from records it has already loaded. It is done BEFORE the shadow
    // tier because every mesh is new after a rebuild and starts out casting —
    // `applyShadowTier` below is what settles that, and settling it first would
    // settle it on meshes that are about to be thrown away.
    enclosures.setDetail?.(level);
    // T-2473: the parkway elms rebuild their dozen crowns at the new spray count.
    void streetTrees.setDetail(level);
    streetFurniture.setDetail(level);
    frontYards.setDetail(level);
    // The road's: `light` keeps the refined grids, the two tiers above it lay
    // the panels that sag on the ground's ridge (streets.js, THE RIDGE DRAPE).
    // T-2600: cut on the job pool; awaited in the serialised run below, before
    // a phone's release, so the arrays it lets go of are the new road's.
    const streetsRebuilt = streets.setDetail?.(level);
    // The yard's weeds thin with the tier (T-2478).
    railway.setDetail(level);
    // The figures' LOD ladder follows the tier (T-1788; docs/HUMAN-ASSET-CONTRACT.md § 8).
    api.humans?.setTier(level);
    void parkedTransport.setTier(level);
    void standingHorses.setTier(level);
    // The sun's half of the level takes effect on THIS frame rather than after
    // the replanting: it costs nothing to apply, and a visitor who turns the
    // setting down on a machine that is struggling should get the cheap half of
    // the answer immediately instead of behind two layer rebuilds.
    applyShadowTier(level);
    // And the reach, for the same reason and in the same breath: the fence layer
    // has just rebuilt its meshes, so the banked spheres are re-read here rather
    // than left pointing at geometry that has been disposed (T-0150).
    applyFurnitureReach(level);
    applyGroundDetailReach(level);
    // Serialise: a visitor clicking through the options faster than the rebuild
    // would otherwise interleave two plantings into one scene.
    const run = (detailPending ?? Promise.resolve()).then(async () => {
      scene3d.remove(flora.group);
      flora.dispose?.();
      flora = await createFlora({
        dataBase: layerBase('flora'), terrain, footprints: planting, sceneId: loaded.scene.id ?? YEAR,
        growthBlocked: swardBlocked, growthEdges: swardEdges, growthPatch: swardPatch,
        verge: streets.verge, forbSeat,
        confidence, problems: layerProblems('flora'), ...detailOpts(), renderer, placementRender,
      });
      scene3d.add(flora.group);

      scene3d.remove(trees.group);
      trees.dispose?.();
      trees = await createTrees({
        dataBase: layerBase('flora'), terrain, footprints: planting, sceneId: loaded.scene.id ?? YEAR,
        growthBlocked: treesBlocked,
        confidence, problems: layerProblems('flora'), pixelsPerRadian,
        streetRecords: draws('streets') ? (loaded.index?.streets ?? []) : [],
        zoneAt: (e, n) => flora.zoneAt(e, n),
        ...detailOpts(),
      });
      scene3d.add(trees.group);
      await streetsRebuilt;
      if (coarse) releaseAfterUpload(scene3d);
      api.flora = flora;
      api.trees = trees;
      if (seasonState.season !== 'summer') void seasonPlants(seasonState.season).then(() => gateFrame.invalidate());
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
  // T-2663: what the Field Check reads — how often a building's record opened, and (T-2954)
  // how often each Navigator app opened.
  const tourCounts = { opens: 0, apps: {} };
  const popup = createPopup(popupRoot, {
    onBusiness: (id) => openBusiness(id),
    onShow: (record) => {
      tourCounts.opens++;
      countField('inspect'); // T-2660: the first since landing is the field log's
      // T-2664: the first Reconstructed building's card says, once, what the word means.
      if (isReconstructed(record?.sidecar)) api.hints?.show('reconstructed');
      void ensureLiberties(); void ensureHouseholdNotes(record); void ensurePictures(); void ensureReaderText();
    },
    // T-2954 (the owner, 2026-10-20: "the focus should be on the card until i either close
    // the card or click on the main display"). An open card holds the pointer and the
    // keyboard: the mouse is let go so the card can be read and clicked, nothing walks or
    // turns behind it (pointerlock.js `holding`), and the keys land on the card, where the
    // arrows scroll it. Esc, the card's Close, or a click or tap on the scene lets go.
    onShown: () => {
      if (document.pointerLockElement) { cardTookPointer = true; document.exitPointerLock?.(); }
      if (!popupRoot.contains(document.activeElement)) popupRoot.focus?.({ preventScroll: true });
    },
  });
  let cardTookPointer = false;
  // T-2825. The scene's reader overlay: the edits that say each research note on a building's
  // card without a ticket number, a record id or a file path (tools/compile_reader_text.py).
  // Off the boot path, like the liberties: the first card asks for it and is redrawn when it
  // lands, and until then a note that would leak is withheld rather than shown.
  let readerPromise = null;
  const ensureReaderText = () => (readerPromise ??= loadReaderText(bases.dataBase,
    `structures_${loaded.scene.id ?? YEAR}`, problems).then((doc) => {
    if (!doc) readerPromise = null;
    popup.setReader(doc);
    return doc;
  }));
  // The pictures of each building, for the card's Images tab (T-2389). Off the boot path
  // for the liberties' reason: only the card reads it, so it is fetched the first time a
  // card is drawn. publish.sh writes it (tools/compile_pictures.py); a failure leaves the
  // tab saying the index is offline and records a problem — never the walkthrough down.
  let picturesPromise = null;
  const ensurePictures = () => {
    if (!picturesPromise) {
      const url = new URL(`pictures/${loaded.scene.id ?? YEAR}.json`, bases.dataBase);
      picturesPromise = fetch(url, { cache: 'no-cache' })
        .then((res) => {
          if (!res.ok) throw new Error(`${res.status}`);
          return res.json();
        })
        .then((doc) => { popup.setPictures(doc); return doc; })
        .catch((err) => {
          problems.push(`pictures/${loaded.scene.id ?? YEAR}.json: ${err.message} — the cards' Images tab is empty`);
          popup.setPictures(null);
          return null;
        });
    }
    return picturesPromise;
  };
  // T-2638. The building summaries Inspect's front page reads: inspect/<scene>.json, written
  // at publish by tools/compile_summaries.py (T-2635), one small file per scene. Fetched the
  // first time a building is targeted or Inspect opens, never at boot; a failure leaves every
  // building on its templated fallback and records a problem.
  let inspectPromise = null;
  const ensureInspect = () => {
    if (!inspectPromise) {
      const url = new URL(`inspect/${loaded.scene.id ?? YEAR}.json`, bases.dataBase);
      inspectPromise = fetch(url, { cache: 'no-cache' })
        .then((res) => { if (!res.ok) throw new Error(`${res.status}`); return res.json(); })
        .catch((err) => {
          problems.push(`inspect/${loaded.scene.id ?? YEAR}.json: ${err.message} — Inspect shows every building's fallback`);
          return null;
        });
    }
    return inspectPromise;
  };
  api.inspectSummaries = ensureInspect;
  api.pictures = ensurePictures;
  // The households' reasoning, per record, on first need (T-2151). publish.sh ships a
  // seated record's households slim — names, roles, grades and basis, which the title,
  // the search and the card draw at once — and the paragraphs behind each `why` toggle
  // in sidecars/<scene>/households/<id>.json: 0.87 MB a first visit no longer loads.
  // A household with no `why` is one whose notes were deferred (tools/
  // defer_household_notes.mjs --check holds that every source household has one).
  // The popup holds the full households beside the record, which stays as shipped, and
  // redraws. A failure records a problem and leaves the card as drawn, toggles absent.
  const householdNotes = new Map();
  const ensureHouseholdNotes = (record) => {
    const s = record?.sidecar;
    const households = Array.isArray(s?.residents) ? s.residents : [];
    if (!households.some((h) => !Object.hasOwn(h, 'why')) || householdNotes.has(record.id)) return;
    const url = new URL(`sidecars/${loaded.scene.id ?? YEAR}/households/${record.id}.json`, bases.dataBase);
    householdNotes.set(record.id, fetch(url, { cache: 'no-cache' })
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status}`);
        return res.json();
      })
      .then((doc) => {
        if (!Array.isArray(doc?.residents) || doc.residents.length !== households.length) {
          throw new Error('does not hold this record\'s households');
        }
        popup.setHouseholds(record.id, doc.residents);
      })
      .catch((err) => {
        problems.push(`households/${record.id}.json: ${err.message} — this card shows its households without their notes`);
      }));
  };
  // The liberties the scene takes, in the Evidence panel and on the card. Not
  // on the boot path (T-2058): only those two read the list, and it was 0.6 MB
  // of a first visit's 13 MB budget (docs/SITE-BUDGET.md §4b). Fetched once, on
  // first need, and the card redraws when it lands. A failure degrades the panel
  // and records a problem; it does not stop the walkthrough.
  let libertiesPromise = null;
  const ensureLiberties = () => {
    if (!libertiesPromise) {
      libertiesPromise = mountLiberties({
        mount: document.getElementById('liberties'),
        noteMount: document.getElementById('liberties-note'),
        dataBase: bases.dataBase,
        registry: loaded.registry,
        problems,
      }).then((handle) => {
        api.liberties = handle;
        // The same list, filtered to the building being inspected, in the
        // provenance popup. One fetch feeds both views: the panel says what the
        // scene made up, the card says what THIS building made up, and neither
        // can drift from the markdown they are both quoting.
        popup.setLiberties(handle.liberties);
        return handle;
      });
    }
    return libertiesPromise;
  };
  // The harness's and the panel's load: loaded AND drawn (T-2834; a card only loads).
  api.loadLiberties = () => ensureLiberties().then((h) => { h?.render?.(); return h; });
  // T-2741: where you stand in the scene's own year — the 1835 streets, the 1904 grid and,
  // past it, the context city's named centrelines; 1812 has none — shared by the compass
  // readout and Navigator Home. Today's streets load after the scene (navigation.setModern).
  const contextStreetLines = (() => {
    const doc = contextCity?.doc;
    const S = Object.fromEntries((doc?.fields?.streets ?? []).map((k, i) => [k, i]));
    const names = doc?.enums?.street_name ?? [];
    return (doc?.streets ?? []).map((r) => ({
      name: names[r[S.name]] ?? null, e0: r[S.e0], n0: r[S.n0], e1: r[S.e1], n1: r[S.n1],
    })).filter((l) => l.name);
  })();
  const eraWhere = createWhere({ streets, grid: streetGrid?.grid ?? null, lines: contextStreetLines });
  const navigation = createNavigation({
    root: hudRoot, terrain, registry: loaded.registry, streets, year: loaded.scene.id ?? YEAR, where: eraWhere,
    // T-2626: the round instrument opens the Map app (its stub opens the whole field).
    onOpen: () => (navigatorUi ? navigatorUi.select('map') : navigation.setFullVisible(true)),
  });
  // T-2626: the year chip opens the Jump app.
  document.getElementById('year-badge')?.addEventListener('click', () => { void navigatorUi?.select('jump'); });

  // The people directory, compiled by tools/compile_scene.py compile_people from
  // data/residents/ — one row per person, so the Go to list can offer a person
  // and the People section can filter a thousand of them without a fetch each.
  // Absent (an older mirror, a failed fetch) degrades to "no people listed";
  // it never takes the scene down.
  let people = null;
  bootController.start('people');
  // T-1739: only a scene that lists `residents` has a directory compiled for it.
  if (draws('residents')) try {
    const res = await fetch(new URL(`sidecars/${loaded.scene.id ?? YEAR}/people.json`, bases.dataBase), { cache: 'no-cache' });
    if (res.ok) people = await res.json();
    else throw new Error(`sidecars/${loaded.scene.id ?? YEAR}/people.json ${res.status} — nobody is listed in Go to or People`);
  } catch (err) {
    bootController.fail('people', err);
  }

  // T-1788. The human figures, as scene objects: humans.js's actor, mounted only for a
  // scene that lists the `humans` layer. No scene does, and L1 stands besides
  // (data/humans/contract.json § l1), so this mounts an empty layer, fetches nothing and
  // draws nobody — the scene-year gate. A record that is drawn later is bound to a person
  // in the directory above and opens that person's own card.
  api.humans = await mountHumans({
    dataBase: layerBase('humans'), assetBase: bases.assetBase, sceneId: loaded.scene.id ?? YEAR,
    people, terrain, tier: detailLevel, problems: layerProblems('humans'),
  });
  api.humans.on('open', ({ personId }) => {
    if (!api.people) return;
    hud.setPanel(true); hud.selectTab('people'); api.people.open?.(personId);
  });
  api.humans.on('role_open', ({ roleCard }) => showHumanRoleCard(roleCard));
  scene3d.add(api.humans.group);

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
    if (!Number.isFinite(pl?.local_e) || !Number.isFinite(pl?.local_n)) return null;
    return { e: pl.local_e, n: pl.local_n };
  }

  /** T-3263 — what a jaunt stop or a Go to must not stand behind, as { e, n, r }. The
   *  list is rebuilt only when the timber is re-grown; the router drops its stands then. */
  const STAND_POST_R = { gas_lamp: 0.12, utility_pole: 0.15 };
  let standOccludersFor = null, standOccluderList = [];
  function standOccluders() {
    if (standOccludersFor === trees) return standOccluderList;
    standOccludersFor = trees;
    standOccluderList = [
      ...(streetTrees.records ?? []).map((t) => ({ e: t.e, n: t.n, r: 0.29 * (t.scale ?? 1) })),
      ...(streetFurniture.records ?? []).filter((f) => STAND_POST_R[f.kind])
        .map((f) => ({ e: f.e, n: f.n, r: STAND_POST_R[f.kind] })),
      ...(trees?.trunks?.() ?? []),
    ];
    return standOccluderList;
  }

  // The route planner and the travel controller. `travel` is assigned after the
  // HUD exists (it paints through it); the HUD's callbacks below reach it through
  // the binding, which is settled long before the first frame.
  const router = createRouter({
    terrain, streets, footprints, decks, surfaceAt: (e, n) => walker.surfaceAt?.(e, n) ?? terrain.surfaceHeight(e, n),
    streetGrid: streetGrid.grid, walks: frontage.walks,
    // T-3263: the trunks and posts a stand must see past — the parkway elms, the lamps
    // and poles, and the grown timber's trunks (re-read when a detail change re-grows it).
    occluders: standOccluders,
    // The walker's own capsule and step rule, so a route that plans is a route that walks.
    radius: WALK.radius, stepUp: WALK.stepUp, cell: 1, inflate: 0.1,
  });
  let travel = null;
  api.router = router;
  api.standOccluders = standOccluders;
  const buildingBounds = buildings.instanceBounds();

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
    const aim = framing(id, { card: false })?.aim ?? focusPoint(id);
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

  // The town's FIRMS, read BEFORE the two directories that now cross-reference
  // them (T-1325). The index is one file and the crosswalk is one fold of it; a
  // person's card and a building's card both ask it the same two questions, so
  // neither is allowed to fold 196 rows for itself.
  api.businessIndex = !draws('businesses') ? null : await (async () => {
    try {
      const res = await fetch(new URL('businesses/index.json', bases.dataBase), { cache: 'no-cache' });
      if (res.ok) return res.json();
      problems.push(`businesses: businesses/index.json ${res.status} — no firm is listed in Businesses`);
    } catch (err) {
      problems.push(`businesses: ${err.message} — no firm is listed in Businesses`);
    }
    return null;
  })();
  const destinations = createDestinations({
    scene: loaded.scene, index: loaded.index, registry: loaded.registry, people,
    businesses: api.businessIndex, positionOf: structurePosition,
    standFor: framing, router, terrain,
  });
  api.destinations = destinations;
  const hud = createHud({
    // T-2661: Settings' "Show the controls" opens Guide's controls sheet in the Navigator.
    onShowGuide: () => navigatorUi?.select('guide'),
    destinations,
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
    resolvedQuality: crashBoot.lowered.quality ? crashBoot.quality : qualityGuess,
    lowered: crashBoot.lowered,
    device,
    structureVersion: loaded.versionState,
    onConfidence: (on) => { confidence.set(on); },
    // T-2647: C toggles the BY GRADE preset (confidence-presets.js).
    onConfidenceKey: () => toggleByGrade({ hud, view: confidence, storage: safeStorage() }),
    onFly: (on) => { intent.flying = !!on; },
    onGoTo: (target) => goToTarget(target),
    // Hiding a level removes it from the view outright — see confidence.setHidden.
    onHideLevel: (level, hide) => { confidence.setHidden(level, hide); gateFrame.invalidate(); api.welcome?.refresh?.(); },
    onSetting: (key, value) => {
      api.sound?.setting(key); // T-2659: Settings › Sound's levels, live
      // A setting can write a value no material owns (a patched shader's
      // uniform), which the gate's signature cannot see: draw once regardless.
      gateFrame.invalidate();
      if (key === 'speed' || key === 'runSpeed' || key === 'wagonSpeed' || key === 'horseSpeed' || key === 'eyeHeight' || key === 'pace') {
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
        crashGuard.chosen('quality');
        applySharpness(value);
      } else if (key === 'governor') {
        governor.setEnabled(value !== 'fixed');
        applySharpness();
      } else if (key === 'detail') {
        crashGuard.chosen('detail');
        applyDetail(value);
      } else if (key === 'compass') {
        navigation.setCompassVisible(value);
      } else if (key === 'overviewMap') {
        navigation.setMapVisible(value);
      } else if (key === 'streetNames') {
        navigation.setStreetVisible(value);
      } else if (key === 'lookTag') {
        api.targetTag?.setTagShown(value);
      } else if (key === 'lookTagPlace') {
        api.targetTag?.setPlace(value);
      } else if (key === 'lookTagHold') {
        api.targetTag?.setHold(value);
      } else if (key === 'season') {
        void applySeason(value).then(() => gateFrame.invalidate());
      } else if (key === 'streetTrees') {
        seasonState.treesShown = value !== 'hidden';
        void streetTrees.setMode(streetTreeMode(seasonState.season, seasonState.treesShown))
          .then(() => gateFrame.invalidate());
      } else if (key === 'lotLines') {
        streetGrid.setLotLines(value === 'shown');
        gateFrame.invalidate();
      } else if (key === 'units') {
        navigation.setUnits(value);
      }
    },
  });

  // The Evidence panel as a hub of topics rather than one scroll; it reorganises
  // the section's own static markup, so the mounts below keep their ids.
  let sourcesPromise = null;
  const openSources = () => {
    if (!sourcesPromise) sourcesPromise = import('./sources.js').then(({attachSources}) => attachSources({
      api, registry: loaded.registry, hud, popup, dataBase: bases.dataBase, root: document.getElementById('sources'),
      scene: loaded.scene.id ?? YEAR,
    })).then(view => { api.sources=view; return view; }).catch(() => {
      sourcesPromise=null;
      document.getElementById('sources').textContent='Sources could not load. Reopen this topic to retry.';
    });
    void sourcesPromise.then(view => { if (api.evidenceHub.topic === 'sources') view?.show(); });
  };
  hud.omitTabs(api.drawerOmitted.tabs);
  // The Trees setting is offered only where there are parkway trees to set (T-2473).
  document.getElementById('row-street-trees')?.toggleAttribute('hidden', !streetTrees.records.length);
  document.getElementById('row-season')?.toggleAttribute('hidden', !seasonal);
  // T-2864: every year has its own day, so the choice says which one it is.
  const seasonDay = String(loaded.scene.target_date ?? '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (seasonDay) {
    const day = new Date(Date.UTC(+seasonDay[1], +seasonDay[2] - 1, +seasonDay[3]))
      .toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
    document.getElementById('s-season')?.setAttribute('title', `A viewing choice: the scene is dated ${day}`);
    const summer = document.querySelector('#s-season option[value="summer"]');
    if (summer) summer.textContent = `Summer — ${day.replace(/ \d{4}$/, '')}, full leaf`;
  }
  document.getElementById('row-lot-lines')?.toggleAttribute('hidden', !streetGrid.lotLines);
  api.evidenceHub = createEvidenceHub({
    root: hudRoot.querySelector('[data-panel="evidence"]'),
    omit: api.drawerOmitted.topics,
    onTopic: id => {
      if (id === 'sources') openSources();
      if (id === 'liberties') {
        // Drawn now if loaded (a card may have loaded it), else once it arrives (T-2834).
        if (api.liberties?.render) api.liberties.render();
        else void ensureLiberties().then((h) => h?.render?.());
      }
    },
    onTitle: (text, onBack) => hud.setTitle(text, onBack),
  });
  // The town summary used to be part of the loader. It now costs nothing on a
  // cold boot: the first visit to Evidence starts it, once, and the hub's
  // MutationObserver replaces the City tile's ellipsis when both files paint.
  let cityCensusPromise = null;
  const ensureCityCensus = () => {
    if (!cityCensusPromise && draws('residents')) {
      cityCensusPromise = mountCityCensus({
        dataBase: bases.dataBase,
        root: document.getElementById('city'),
        buildStamp: document.getElementById('gate-build')?.textContent.trim() || `build ${VERSION}`,
        onError: err => problems.push(`city census: ${err?.message || err}`),
      }).then((c) => { api.census = c; return c; });
    }
    return cityCensusPromise;
  };
  // T-2629: Settings › About — the build stamp, and the DEV mark on a dev build. The
  // preview's chrome is in the page's HTML before boot, so a paint now is the page's; the
  // section repaints whenever it is shown, and api.about.paint lets a test repaint it.
  api.about = { paint: () => paintAbout({ version: VERSION }) };
  api.about.paint();
  hud.onTabChange((tab) => {
    if (tab === 'settings') paintAbout({ version: VERSION });
    if (tab === 'evidence') {
      void ensureCityCensus();
      void ensureLiberties().then((h) => h?.render?.()); // the hub's tile counts the drawn list
      api.evidenceHub?.showHub?.({ keep: true });
    }
    if (tab === 'goto') hud.goTo?.refreshDistances?.();
  });

  // And the town's own law, which belongs to no attribute either. The 5 August 1835
  // ordinance fenced the ground the Trustees thought was built up closely enough to
  // burn — the only documented statement this project holds about where the built
  // town ended — and nothing is drawn in the scene for it, because a legal limit is
  // not a fence. The card carries it: pick a building and it says which side of the
  // line it stood on. A failed fetch leaves the row off rather than guessing a side.
  // It is 1835's law, so it rides 1835's cards and no other scene's (T-2609).
  api.ordinances = await loadOrdinanceLimits({ dataBase: bases.dataBase,
    sceneDate: loaded.scene.target_date ?? YEAR, problems });
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
  api.residents = !draws('residents') ? null : await mountResidents({
    mount: document.getElementById('residents'),
    noteMount: document.getElementById('residents-note'),
    dataBase: bases.dataBase,
    sceneId: loaded.scene.id ?? YEAR,
    problems,
  });
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
  if (draws('residents')) try { api.people = await mountPeople({
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
  else bootController.end('people');

  // …and the town's FIRMS, which until now reached a visitor only through the
  // roof they stood in. 166 of the 196 the register knows have no roof here — 26
  // reach a landmark, 61 a street and no further, 79 could be placed nowhere at
  // all — and the one
  // thing this project will not do to make them visible is invent a building for
  // them. So they get a directory and a card: every firm findable by trade,
  // street, grade and how far the record could place it, and every limit printed.
  api.businesses = !draws('businesses') ? null : await mountBusinesses({
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
  api.fauna = !draws('fauna') ? null : await mountFauna({
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
  api.plants = !draws('flora') ? null : await mountPlants({
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
  api.exclusions = !draws('exclusions') ? null : await mountExclusions({
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
  if (api.exclusions) popup.setOpenQuestions(api.exclusions.uncertain);

  // …and the shape of what is known about the people themselves (T-1160). The
  // walkthrough can stand a visitor next to a named resident; only this says how
  // few of them there are, how thin each attribute is, and what the reconstruction
  // bands below still have to supply. Rendered from the generated profile, so a
  // resident pass that moves the layer moves this panel too.
  api.population = !draws('residents') ? null : await mountPopulation({
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
  api.orderBook = !draws('residents') ? null : await mountOrderBook({
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
  // T-2649 (§09, §10): the Confidence view's legend chip under the year chip, shown while the
  // view is not Normal; a tap opens the app. It paints from the HUD and the renderer's view
  // each time either says the view moved, so after the colouring is restored on the way in
  // it is already right.
  api.confidenceLegend = createConfidenceLegend({ el: document.getElementById('conf-legend'), hud, view: confidence,
    open: () => { void navigatorUi?.select('confidence'); } });

  camera.fov = hud.settings.fov;
  camera.updateProjectionMatrix();
  applySharpness(crashGuard.state.stepdown?.quality || resolveSharpness(hud.settings.quality, coarse, qualityGuess));
  governor.setEnabled(hud.settings.governor !== 'fixed');
  streets.setLegibilityAid(hud.settings.roadAid);
  world.setBrightness(hud.settings.brightness);
  navigation.setCompassVisible(hud.settings.compass);
  navigation.setMapVisible(hud.settings.overviewMap);
  navigation.setStreetVisible(hud.settings.streetNames);
  navigation.setUnits(hud.settings.units);
  // T-2741: the compass's own street button is the Settings toggle, from the HUD.
  document.getElementById('street-toggle')?.addEventListener('click', () => {
    hud.setToggle('streetNames', !hud.settings.streetNames);
  });
  // Today's streets (data/modern/streets.json, the City's centrelines), in every year.
  // Off the boot path: until they land the readout says no street, and a failed fetch
  // leaves it saying so rather than holding the scene.
  void loadModernStreets(bases.dataBase).then((m) => {
    if (!m) { problems.push('modern streets: data/modern/streets.json did not load — today\'s names are not shown'); return; }
    navigation.setModern(m);
    api.modernStreets = m;
  });

  // ---- input ------------------------------------------------------------ //

  const intent = createIntent();
  const backends = createBackendSwitch(intent);
  // T-2614: CLICK TO ENGAGE LOOK belongs to the desktop backend only.
  backends.onChange(name => gesture.setLook({ backend: name }));

  // The travel controller: instantly, on foot, by wagon, on horseback, or flying.
  // It writes the shared intent the way a backend does, so the walker keeps its
  // collision and terrain honesty whoever is steering — see travel.js.
  travel = createTravel({
    walker, intent, hud, settings: hud.settings, router, terrain, footprints,
    focusPoint, structurePosition,
    // Where a ride or a flight ends: the framed stand-off, the same one Go to uses.
    // T-3022: the arrival opens the building in Inspect where it can, so frame for that.
    // (A ride says `card: false` when it opens nothing; any other ride opens the building.)
    standFor: (id, options) => framing(id, { ...options, card: options?.card === false ? false : arrivalPanel(id) }),
    registry: loaded.registry,
    frame: (id, options) => frame(id, { ...options, card: options?.card === false ? false : arrivalPanel(id) }),
    teleport: (where) => walker.teleport(where),
    goToAnchor: (id) => api.goTo(id),
    setFly: (on) => hud.setFly(on, { announce: false }),
    // Arriving is what opens the card: the menu closes, the building's card opens.
    onArrive: (id) => { hud.setPanel(false); openBuilding(id); lastArrival = { id, e: walker.state.e, n: walker.state.n }; },
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
      gesture.setLook({ locked });
      // A card opening lets the pointer go on purpose (T-2954): the card is the message.
      if (!locked && !cardTookPointer) hud.say('Pointer released — click the view to look around again');
      cardTookPointer = false;
    },
    holding: () => !!popup.openId && !gateOpen,
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
    // T-2653: Move › Comfort's snap-turn, read on each drag so a change takes at once.
    snapTurn: () => !!hud.settings.snapTurn,
  });

  let gateOpen = true;
  let enteredWorld = false;

  // Exactly one backend is live. Whichever device the visitor actually uses
  // wins, switched by the first real event of that kind — a laptop with a
  // touchscreen must not end up driving both.
  // The arrival and welcome are menus, so neither movement backend is live.
  window.addEventListener('pointerdown', (e) => {
    if (gateOpen || e.target.closest?.('#jaunt-panel')) return;
    if (e.pointerType === 'touch') backends.activate(touch);
    else if (e.pointerType === 'mouse') backends.activate(pointerlock);
  }, { capture: true });
  window.addEventListener('keydown', (e) => {
    // Not while typing. This capture handler switches the whole control backend
    // to keyboard-and-mouse, and the first keystroke into the Go-to search box
    // was doing exactly that — taking a visitor who had been tapping their way
    // around a phone and handing them a control scheme with no on-screen stick.
    if (gateOpen || isTyping(e.target) || e.target.closest?.('#jaunt-panel')) return;
    if (!e.metaKey && !e.ctrlKey) {
      backends.activate(pointerlock);
      // Not while a card holds the keyboard (T-2954): the arrows scroll the card.
      if (/^(Key[WASD]|Arrow(Up|Down|Left|Right))$/.test(e.code) && !popup.openId) pointerlock.lock();
    }
  }, { capture: true });

  canvas.addEventListener('click', () => {
    if (backends.active !== pointerlock || gateOpen) return;
    // A click on the scene with a card open is the release (T-2954): the card goes and
    // the same click takes the look back.
    if (popup.openId) popup.close();
    else if (inspectingByHand()) releaseInspect(); // T-3022: Inspect, the same
    if (!pointerlock.isLocked) pointerlock.lock();
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
    // T-3022: Inspect opened on a building is let go to where the Navigator was, rather than
    // the Navigator closing whole (its own Escape, which this press is kept from).
    else if (inspectingByHand()) { e.preventDefault(); releaseInspect(); }
  });

  // ---- picking ---------------------------------------------------------- //

  function inspect(ndc = null, { by = 'code' } = {}) {
    blackbox.log('tap', { to: ndc ? 'point' : 'crosshair' });
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
    const vehicle = parkedTransport.pickAt(ndc, camera);
    if (vehicle?.record && (!hit || vehicle.distance < hit.distance)) hit = vehicle;
    const horse = standingHorses.pickAt(ndc, camera);
    if (horse?.record && (!hit || horse.distance < hit.distance)) hit = horse;
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
    /**
     * And so can the 1904 street grid (T-0474), whose cards belong to no structure
     * either: a band of the sidewalk space, a roadway or an alley answers with its
     * width and tier, and the ground between them with the lot it lies in — its
     * frontage, the 1911 addresses printed on it and the sheet it was read from.
     */
    const gridHit = streetGrid.pickAt(ndc, camera);
    if (gridHit && gridHit.record && (!hit || gridHit.distance < hit.distance)) {
      hit = { ...gridHit };
    }
    // And a parkway elm's trunk (T-2473), with its own card.
    const treeHit = streetTrees.pickAt(ndc, camera);
    if (treeHit && treeHit.record && (!hit || treeHit.distance < hit.distance)) {
      hit = { ...treeHit };
    }
    // And a street lamp's post (T-3199), a fire hydrant (T-3201) or a wooden pole (T-3202), with its
    // own card: what it is, its grade, its pictures.
    const furnitureHit = streetFurniture.pickAt(ndc, camera);
    if (furnitureHit && furnitureHit.record && (!hit || furnitureHit.distance < hit.distance)) {
      hit = { ...furnitureHit };
    }
    // And a front yard's shrub, ivy or bed (T-3203): what it is and whether a picture shows it.
    const yardHit = frontYards.pickAt(ndc, camera);
    if (yardHit && yardHit.record && (!hit || yardHit.distance < hit.distance)) {
      hit = { ...yardHit };
    }
    // ...and a stand-in of the context city (T-2477) answers with what it is and what it
    // rests on: a sheet's outline or a projection, and the rule its height came from.
    const contextHit = contextCity.pickAt(ndc, camera);
    if (contextHit && contextHit.record && (!hit || contextHit.distance < hit.distance)) {
      hit = { ...contextHit };
    }
    // And the lakefront railway (T-2478): its ground answers with the track nearest
    // the point, or the right-of-way's own card.
    const railHit = railway.pickAt(ndc, camera);
    if (railHit && railHit.record && (!hit || railHit.distance < hit.distance)) {
      hit = { ...railHit };
    }
    // A figure answers with its PERSON, not a card of its own (T-1788): the layer's
    // `open` event takes the visitor to the resident card the directory already draws.
    const figure = api.humans?.pickAt(ndc, camera);
    if (figure && (!hit || figure.distance < hit.distance)) {
      popup.close();
      api.humans.select(figure);
      return figure;
    }
    if (!hit) {
      popup.close();
      hud.say('Nothing there — aim at a building');
      return null;
    }
    // T-3022: a building the visitor clicks or taps opens in the Navigator's Inspect; a
    // street, a tree, a stand-in or the railway keeps the floating card.
    if (by === 'hand' && loaded.registry.get(hit.record.id) && openBuilding(hit.record.id)) return hit;
    popup.show(hit.record, { fromSign: !!hit.fromSign });
    return hit;
  }

  // ---- T-3022: a building the visitor opens opens in the Navigator's Inspect ----------
  // The owner, 2026-10-22: "the detailed research card needs to be folded into" the
  // Navigator, behind a setting for expert research. So a click or tap on a building, an
  // arrival, a row in People and Home's Inspect key open it in Inspect, whose Research tab
  // (Settings › Expert research) carries the card's evidence, liberties and record. The
  // floating card stays for what Inspect does not show (a street, a tree, a stand-in, the
  // railway) and behind `pick`, the harness's reading of a record. Inspect opened this way
  // holds as the card did (T-2954): Esc, its Back key, or a click or tap on the town lets
  // it go, back to where the Navigator was (docked, if it was docked).
  let handInspect = null; // { id, wasLevel, opening } while Inspect shows a building the visitor opened
  let letting = null;     // one let go while still opening: Inspect closes as soon as it is up
  function openBuilding(id) {
    const record = loaded.registry.get(id);
    if (!record?.sidecar || !navigatorUi?.has?.('inspect')) return pick(id);
    if (popup.openId) popup.close();
    void ensureReaderText(); // T-2825: Inspect reads the record as the card says it
    if (isReconstructed(record.sidecar)) hints.show('reconstructed'); // T-2664
    const inspecting = !!handInspect && navigatorUi.app === 'inspect';
    // `opening` until Inspect is on screen: the device passes through other states on its way
    // there (a first open loads Inspect), and those must not let the building go.
    const hand = { id, wasLevel: inspecting ? handInspect.wasLevel : navigatorUi.level, opening: true };
    handInspect = hand;
    inspectHold = id;
    void Promise.resolve(navigatorUi.openLink({ app: 'inspect', id })).finally(() => {
      hand.opening = false;
      if (hand.released) { letGo(hand); if (letting === hand) letting = null; } // let go before it was on screen
    });
    // The panel is read and clicked, as the card was: the mouse is let go.
    if (document.pointerLockElement) { cardTookPointer = true; document.exitPointerLock?.(); }
    return { id, record };
  }
  /** What an arrival at `id` opens, for the framing: Inspect (as openBuilding does), else the card. */
  const arrivalPanel = (id) => (loaded.registry.get(id)?.sidecar && navigatorUi?.has?.('inspect') ? 'inspect' : true);
  // Held from the moment it is asked for, so Esc or the key a moment later lets it go even
  // while Inspect is still on its way (a slow frame, or its first load).
  const inspectingByHand = () => !!handInspect && (handInspect.opening || (navigatorUi?.app === 'inspect' && navigatorUi.level > 0));
  function letGo(was) {
    if (navigatorUi?.app !== 'inspect') return false;
    if (was.wasLevel === 0) navigatorUi.closeApp(); else void navigatorUi.back();
    return true;
  }
  function releaseInspect() {
    const was = handInspect;
    handInspect = null;
    if (!was) return false;
    if (was.opening) { was.released = true; letting = was; return true; }
    return letGo(was);
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
  function framing(id, { card = popup.openId !== null || (handInspect ? 'inspect' : false), mode = travel?.mode ?? 'walk' } = {}) {
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
    const h = buildingBounds[id]?.size[1]
      ?? (record?.sidecar?.drawn_by ? (aim.y - terrain.surfaceHeight(centre.e, centre.n)) / 0.55 : wallH * 1.55);
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
    const ax = axis(Math.tan(camera.fov * DEG / 2) * camera.aspect, free.x[0], free.x[1]);
    const ay = axis(Math.tan(camera.fov * DEG / 2), free.y[0], free.y[1]);
    const fit = (a) => (R * 1.25) / Math.sin(Math.min(a.half, 89 * DEG));
    const distance = THREE.MathUtils.clamp(Math.max(fit(ax), fit(ay), 10), 10, 90);
    // Turning RIGHT (a larger compass bearing) moves the building LEFT in frame;
    // pitching DOWN (a smaller pitch) moves it UP.
    const yawOffsetDeg = -ax.centre / DEG;
    const pitchOffsetDeg = -ay.centre / DEG;
    const stand = router.standOff(id, centre, r, { distance, mode });
    if (!stand) return null;
    // Aim at the street facade rather than the footprint centroid, which can
    // be deep in a courtyard. The parcel supplies the front on corner lots.
    if (stand.front) { aim.x = stand.front.e; aim.z = -stand.front.n; }
    const bearingDeg = ((Math.atan2(stand.e - centre.e, stand.n - centre.n) / DEG) + 360) % 360;
    return { e: stand.e, n: stand.n, distance: Math.hypot(stand.e - centre.e, stand.n - centre.n), bearingDeg, aim, radius: r, height: h,
      yawOffsetDeg, pitchOffsetDeg, free, front: stand.front ?? null };
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
    // T-3022: a building opens in the Navigator's Inspect now (`card` is 'inspect'), which
    // mirrors css/navigator.css instead: a 400 px panel 10 px in from the LEFT above 620 px
    // wide, else the half sheet over the lower 48 % of a phone.
    if (card === 'inspect') {
      if (w > 620) return { x: [-1 + 2 * Math.min(0.9, (Math.min(400, w - 20) + 10) / w), 1], y: [-1, 1] };
      return { x: [-1, 1], y: [-1 + 2 * 0.48, 1] };
    }
    if (w > 620) {
      const cardFrac = Math.min(0.9, Math.min(440, w - 24) / w);
      return { x: [-1, 1 - 2 * cardFrac], y: [-1, 1] };
    }
    const sheetFrac = Math.min(0.62, Math.max(0.3, (hgt - 120) / hgt));
    return { x: [-1, 1], y: [-1 + 2 * sheetFrac, 1] };
  }

  /** Stand back and look at a structure, framed whole — used by Go to, the rides and the harness. */
  function frame(id, { card = false, mode = travel?.mode ?? 'walk' } = {}) {
    return applyFraming(framing(id, { card, mode }));
  }

  function applyFraming(f) {
    if (!f) return false;
    // Use the router's actual safe point, including nearest-cell fallback.
    // Rebuilding it from the requested distance can put the walker inside a roof.
    walker.teleport({ local_e: f.e, local_n: f.n });
    const st = walker.state;
    const de = f.aim.x - st.e, dn = -f.aim.z - st.n;
    walker.teleport({
      local_e: st.e, local_n: st.n,
      yaw_deg: ((Math.atan2(de, dn) / DEG) + 360) % 360 + f.yawOffsetDeg,
      pitch_deg: Math.atan2(f.aim.y - st.eyeY, Math.max(Math.hypot(de, dn), 0.1)) / DEG + f.pitchOffsetDeg,
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
    const drawn = buildingBounds[id];
    const aimH = drawn ? (drawn.min[1] + drawn.max[1]) / 2 : wallH * 0.55;
    return enuToWorld(e, n, terrain.surfaceHeight(e, n) + aimH);
  }

  /** One route for the complete search: frame a structure, stand at a verified
   * intersection, or use one of the authored scene viewpoints. */
  function goToTarget(target) {
    if (jauntRuntime?.state.jaunt) jauntRuntime.explore();
    // Explicit coordinate viewpoints predate the shared picker and are used by
    // the scene measurement harness. Named picker rows still resolve strictly.
    if (!target?.id && target?.kind === 'intersection'
        && Number.isFinite(target.local_e) && Number.isFinite(target.local_n)) return travel.go(target);
    const resolved = destinations.resolve(target);
    if (!resolved) {
      const row = target && destinations.byId(target.kind, target.id);
      if (row?.kind === 'person') {
        hud.setPanel(true); hud.selectTab('people'); api.people?.open?.(row.id); return true;
      }
      if (row?.kind === 'business' && !row.derived_from) { openBusiness(row.id); return true; }
      if (row?.kind === 'business' && row.derived_from === 'structure') {
        // A fallback firm owns no separate register card; its source building does.
        hud.setPanel(false); openBuilding(row.at); hud.say(row.limit || 'No safe arrival point'); return true;
      }
      return false;
    }
    return travel.go(resolved.structureId
      ? { kind: 'structure', id: resolved.structureId, label: resolved.label, person: resolved.kind === 'person' ? resolved.id : null }
      : resolved);
  }

  /** The future welcome picker shares resolution, but starts exploration without a ride. */
  function spawnAtDestination(target) {
    const resolved = destinations.resolve(target, { card: false });
    if (!resolved || router.blockedAt(resolved.standOff.e, resolved.standOff.n)) return false;
    travel.stop('spawn'); lastArrival = null; popup.close(); hud.setPanel(false);
    hud.setFly(false, { announce: false });
    if (resolved.structureId) applyFraming(resolved.standOff);
    else walker.teleport({ local_e: resolved.standOff.e, local_n: resolved.standOff.n,
      yaw_deg: resolved.yaw_deg ?? 0, pitch_deg: resolved.pitch_deg ?? 0 });
    return true;
  }

  // ---- gate ------------------------------------------------------------- //

  // T-2617: the Navigator and the probe it reads, made once the welcome is (below).
  let navigatorUi = null, target = null, targetTag = null;
  let guideFaq = null; // T-2662
  const jauntCatalogs = {}; // T-2666: each destination's Jaunt catalog, for Guide › For teachers
  // T-2634: Free roam's one-time tip, once per device.
  const roamTip = createRoamTip({ el: document.getElementById('roam-tip') });
  api.roamTip = roamTip;
  // Any first move of the visitor's own puts the tip away: it has said its piece.
  for (const type of ['pointerdown', 'keydown']) {
    window.addEventListener(type, (e) => { if (roamTip.showing && e.target?.id !== 'roam-tip') roamTip.hide(); }, { capture: true });
  }
  // ---- T-2664: the Field Check offered once per device on Home (welcome.js paints it),
  // and the one-time hints after it: the first Jaunt, the first Jump, the first
  // Reconstructed building. A hint waits while the Field Check runs, and goes at the
  // visitor's next move or after a few seconds.
  const tourOffer = createTourOffer();
  const hints = createHints({ el: document.getElementById('nav-hint'), blocked: () => !!api.tour?.running });
  const jumpedIn = takeJumped();
  let tourEntering = false;
  api.tourOffer = tourOffer;
  api.hints = hints;
  // T-2665: the Navigator License, awarded once per device as the Field Check's Finish
  // closes it (below, at the tour), and kept with the Jaunt keepsakes in Jaunts' daybook.
  const license = createLicense();
  api.license = license;
  for (const type of ['pointerdown', 'keydown']) {
    window.addEventListener(type, () => { if (hints.showing) hints.hide(); }, { capture: true });
  }
  function enterWorld({ spawn: destination = null, resume = false } = {}) {
    if (!gateOpen || !api.ready) return false;
    if (!resume) {
      if (destination) {
        if (!spawnAtDestination(destination)) return false;
      } else {
        travel.stop('spawn'); popup.close();
        hud.setFly(false, { announce: false });
        walker.teleport(loaded.scene.spawn ?? spawn);
      }
    }
    const firstEntry = !enteredWorld;
    gateOpen = false;
    enteredWorld = true;
    gate.hidden = true;
    hudRoot.inert = false;
    hud.show();
    if (firstEntry) hud.restore();
    // T-2617: into the town with the Navigator docked (§07: Free roam docks it), and
    // the probe looks again at whatever the eye has just been set down in front of.
    navigatorUi?.dock();
    target?.invalidate();
    targetTag?.setEnabled(true);
    backends.activate(coarse ? touch : pointerlock);
    // T-2661: no control-help popover on the way in; the line below says the two moves
    // that matter, and Guide in the Navigator holds the rest.
    // T-2614: audio was resumed by the Home choice that brought us here (gesture-gate.js);
    // the look waits for a click on the scene, and the tag says so until it is taken.
    gesture.setLook({ inWorld: true, backend: backends.name, locked: pointerlock.isLocked });
    hud.say(backends.name === 'touch'
      ? 'Left thumb walks · drag the right side to look · tap a building'
      : 'W A S D to walk · E to inspect what you are looking at');
    // T-2634: Free roam (no destination, not a resume) docks the Navigator, above, and
    // the first time on this device says how to inspect.
    if (!resume && !destination && !tourEntering) roamTip.show({ touch: backends.name === 'touch' });
    // T-1727: an address that asked for a structure version hears, on the way in, what
    // it got — above all when it did NOT get it, which must never pass silently.
    if (firstEntry) hud.announceStructureVersion();
    // T-2663: a Field Check left running before a reload picks up at the same step.
    if (firstEntry && !api.tour?.running) api.tour?.resume();
    // T-2664: the far year of a first Jump says, once, how to go back.
    if (firstEntry && jumpedIn) hints.show('jump');
    return true;
  }
  let jauntPreview, jauntRuntime, jauntPanel, jauntReady, jauntReturnId;
  let jauntEntering = false;
  // T-1256: a saved outing is offered back once, the first time the Jaunts menu opens in
  // this visit, and never over an outing already under way.
  let jauntRestoreTried = false;
  const jauntRoot = document.getElementById('welcome-jaunts-content');
  function jauntError(error) {
    const message = document.createElement('p'); message.setAttribute('role', 'alert');
    message.textContent = `The outing could not start: ${error.message}. Choose Start Jaunt to try again.`;
    jauntRoot.append(message);
  }
  function ensureJaunts() {
    return jauntReady ??= Promise.all([import('./jaunt-preview.js'), import('./jaunts.js'), import('./jaunt-panel.js'), import('./travel-estimate.js'), import('./jaunt-context.js'), import('./jaunt-cards.js')]).then(([preview, runtime, panel, estimates, context, cards]) => {
      const resolveJaunt = target => {
        const resolved = destinations.resolve(target);
        return resolved?.structureId ? { kind: 'structure', id: resolved.structureId, label: resolved.label } : resolved;
      };
      const estimateOptions = mode => ({ resolve: target => {
        const resolved = resolveJaunt(target); return resolved && travel.destinationOf(resolved, { mode, card: false });
      }, settings: hud.settings, router: travel.router });
      jauntPreview = preview.createJauntPreview({ root: jauntRoot, scene: YEAR, dataBase: bases.dataBase, destinations, api: api.jaunts,
        onStart: (id, options) => jauntRuntime.start(id, options), onResume: () => jauntRuntime.resume(), getSession: () => jauntRuntime?.state,
        // T-2631: each card's plate, a credited picture of its stops (pictures.js § plateFor).
        plateFor: (row) => jauntPlate(jauntPictures, (row.destinations ?? [])
          .map((d) => (d.kind === 'structure' ? d.id : destinations.resolve(d)?.structureId)).filter(Boolean)),
        // T-2652/T-2727: with Jaunts use my choice on, the getting-there choice picks a Jaunt's
        // mode where the Jaunt allows it; one that cannot go that way keeps its own and says so.
        preferredMode: (jaunt) => jauntModeFor(hud.gettingThere, jaunt),
        modeNote: (jaunt) => jauntWay(jaunt).note,
        license,
        estimate: (row, mode) => estimates.estimateJaunt(row, mode, estimateOptions(mode)) });
      const actions = Object.fromEntries(['next', 'prev', 'end', 'menu', 'choose', 'revise', 'retry', 'detail', 'returnFromDetail', 'setMode', 'straight', 'resumeRide', 'dismissContext'].map(name => [name, (...args) => jauntRuntime[name](...args)]));
      const jauntCards = cards.createJauntCards({ registry: loaded.registry, popup, hud, api,
        sources: () => { openSources(); return sourcesPromise; }, onReturn: () => jauntRuntime.returnFromDetail() });
      actions.closeOverlay = jauntCards.close;
      jauntPanel = panel.createJauntPanel({ destinations, actions });
      jauntRuntime = runtime.createJaunts({ scene: YEAR, load: jauntPreview.load, travel,
        preferredMode: (jaunt) => jauntModeFor(hud.gettingThere, jaunt),
        resolve: resolveJaunt, place: spawnAtDestination,
        contextForRoute(state, route) {
          const to = runtime.currentStop(state), from = state.jaunt.stops.find(s => s.id === state.fromStopId);
          // T-2946: measured to the building's walls and named as the jaunt names it.
          const outlines = new Map(footprints.map(f => [f.id, f.pts]));
          const places = [...loaded.registry.values()].map(record => ({ id: record.id,
            label: context.placeName(state.jaunt, record.id, record.sidecar),
            point: structurePosition(record.id), outline: outlines.get(record.id),
            minor: context.minorPlace(record.sidecar) }));
          return context.legContext(state.jaunt, from?.id, to.id, route.points, places,
            [from && resolveJaunt(from.destination)?.id, resolveJaunt(to.destination)?.id]);
        },
        estimate: state => estimates.estimateJaunt(state.jaunt, state.mode, { ...estimateOptions(state.mode),
          startIndex: state.stopIndex, includeOpening: state.stopIndex === 0,
          from: ['travelling', 'paused'].includes(state.phase) ? { e: walker.state.e, n: walker.state.n, altitude: walker.state.altitude } : null }),
        enter(target, { resume = false } = {}) {
          jauntEntering = true;
          try {
            const ok = api.welcome.state === 'world' || (resume ? api.welcome.close() : api.welcome.enter(target.kind, target.id));
            // T-2630: a Jaunt started from the Navigator's Jaunts app pockets the device.
            if (ok) navigatorUi?.dock();
            return ok;
          } finally { jauntEntering = false; }
        },
        render: state => {
          jauntPanel.render(state);
          // T-2664: at the first Jaunt's first stop, once per device, how a Jaunt goes on.
          if (state?.jaunt && state.phase === 'atStop') hints.show('jaunt');
        },
        onComplete: state => jauntPreview.award(state),
        showMenu({ returnId }) { jauntReturnId = returnId; api.welcome.show({ focus: false }); api.welcome.enter('jaunts'); },
        closeDetail: jauntCards.close,
        openDetail: jauntCards.open, onError: jauntError,
      });
      return jauntRuntime;
    }).catch(error => { jauntReady = null; jauntPanel?.destroy(); throw error; });
  }
  // T-2727: how a Jaunt travels under Move › Jaunts use my choice: its mode, whether it kept
  // its own against the visitor's choice, and the line that says so. The Jaunt menu and the
  // controller read the same rule (preferredMode / modeNote above).
  function jauntWay(jaunt) {
    const c = jauntChoice(hud.gettingThere, jaunt);
    const labels = Object.fromEntries(Object.entries(PACES).map(([id, way]) => [id, way.label]));
    return { mode: c.mode ?? jaunt?.default_mode ?? 'walk', kept: c.kept,
      note: c.kept ? t('hud.jaunt.keeps', { way: styleWords(hud.gettingThere, labels) }) : '' };
  }
  api.jaunts = { catalog: null, get state() { return jauntRuntime?.state ?? null; },
    modeFor: (jaunt) => jauntWay(jaunt),
    async daybook() { await ensureJaunts(); return jauntPreview.daybook(); },
    async start(id, options) { try { return (await ensureJaunts()).start(id, options); } catch (error) { jauntError(error); return false; } },
    ...Object.fromEntries(['next', 'prev', 'end', 'menu', 'resume', 'restart', 'choose', 'revise', 'setMode', 'straight', 'resumeRide', 'detail', 'returnFromDetail', 'dismissContext'].map(name => [name, (...args) => jauntRuntime?.[name](...args)])),
  };
  // T-2561: "Keep <year> on this device" on the welcome — the year's pack in Cache
  // Storage behind a service worker, so a kept year boots from disk, offline too.
  api.pack = createYearPack({ year: YEAR, mount: document.getElementById('welcome-pack'), dev: resolveBases().dev });
  // The Jaunts list, for the Welcome card's Jaunts choice and for the Navigator's Jaunts
  // app (T-2630), which shows the same list wherever it is.
  let jauntPictures = null;
  async function openJauntList() {
    const root = document.getElementById('welcome-jaunts-content');
    try {
      root.setAttribute('aria-busy', 'true');
      // T-2631: the pictures file, for the cards' plates, fetched alongside — never at boot.
      [, jauntPictures] = await Promise.all([ensureJaunts(), ensurePictures().catch(() => null)]);
      if (!jauntRestoreTried) { jauntRestoreTried = true; if (!jauntRuntime.state.jaunt) await jauntRuntime.restore(); }
      await jauntPreview.open(jauntReturnId); jauntReturnId = null;
    } catch {
      root.textContent = 'Jaunt previews could not load. Choose Jaunts to try again, or explore on your own.';
    } finally { root.removeAttribute('aria-busy'); }
  }
  api.welcome = createWelcome({ gate, scene: loaded.scene, destinations, isTouch: coarse,
    // T-2632: each Go to row's distance and bearing, from where the visitor stands.
    visitor: () => ({ e: walker.state.e, n: walker.state.n, bearingDeg: walker.bearingDeg }),
    units: () => hud.settings.units,
    // T-2633: Go to dims the grades the Confidence view is hiding.
    hiddenGrades: () => hud.hiddenLevels,
    onExplore: () => { if (!jauntEntering && jauntRuntime?.state.jaunt) jauntRuntime.explore(); },
    onJaunts: () => openJauntList(),
    // T-2630: the Navigator's Jaunts app hands back what it borrowed before the card shows.
    onShow: () => api.jauntsApp?.restore(),
    // T-2613: into the town is the journey's next state — on a Jaunt, or exploring.
    // T-2620: in the town a pick goes through goToTarget (see goToPick); from the gate, in.
    enter: goToPick({
      inTown: () => !gateOpen && enteredWorld,
      goTo: (target) => goToTarget(target),
      enterWorld: (target) => enterWorld({ spawn: target }),
      dock: () => navigatorUi?.dock(),
      entered: () => journey.go(jauntEntering ? 'on-jaunt' : 'exploring'),
    }),
    resume: () => { const ok = enterWorld({ resume: true }); if (ok) journey.go(jauntEntering ? 'on-jaunt' : 'exploring'); return ok; },
    pause: () => {
      if (jauntRuntime?.state.jaunt && !['menu', 'outcome'].includes(jauntRuntime.state.phase)) jauntRuntime.menu();
      gateOpen = true;
      gateFrame.reset();
      backends.activate(null);
      gesture.setLook({ inWorld: false });
      targetTag?.setEnabled(false);
      api.showMe?.cancel(); // T-2640: no camera turn carries on behind the arrival device
      if (document.pointerLockElement) document.exitPointerLock?.();
      intent.clear();
      hud.setPanel(false);
      hudRoot.inert = true;
    },
    hasEntered: () => enteredWorld,
    // T-2664: Home's "First time? Take the 60-second tour": into the town as Free roam
    // goes (without Free roam's tip, which the tour's own steps cover), then step 01.
    offer: { due: () => tourOffer.due() && !api.tour?.running, spend: (how) => tourOffer.spend(how) },
    onTour: () => {
      tourEntering = true;
      let ok = false;
      try { ok = api.welcome.enter('spawn'); } finally { tourEntering = false; }
      if (ok) api.tour?.start();
      return ok;
    },
  });

  // ---- the Navigator (T-2617) ------------------------------------------- //
  // T-2618: whether this scene has a people directory, without paying for it at boot.
  const peopleDirectory = (() => {
    const url = new URL(`sidecars/${loaded.scene.id ?? YEAR}/people.json`, bases.dataBase);
    let known = people ? true : false, asked = !!people, loading = null;
    return {
      get known() { return known; },
      /** After ready: a HEAD, so a scene with no `residents` layer can still show People. */
      ask() {
        if (asked) return;
        asked = true;
        // Complete the zero-byte body too: discarding Chromium's HEAD response
        // can leave its request aborted even after a successful HTTP status.
        fetch(url, { method: 'HEAD', cache: 'no-cache' }).then(async (r) => {
          await r.arrayBuffer(); known = r.ok;
        }).catch(() => { known = false; });
      },
      load() {
        if (people) return Promise.resolve(people);
        loading ??= fetch(url, { cache: 'no-cache' }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
        return loading;
      },
    };
  })();

  // RIGHT IN FRONT OF YOU is inspect()'s own aim "down the crosshair" (no point
  // given), over the structure layers whose hits carry a building record, nearest
  // first, within 40 m. target.js decides when to look; T-2627 and T-2638 read it too.
  // T-2827: on a phone the probe draws nothing. It answers from the buildings'
  // boxes (gpu-pick.js `boxPick`): the pick it drew twice a second while you
  // walked is where an iPhone stopped the page (Kevin's black-box records). A tap
  // still draws its pick, now of only the batches its ray meets.
  // T-2723: elsewhere the look is drawn in the frame and read back when the GPU has
  // got to it (`pickAtAsync`): reading it on the spot waited for the whole frame.
  const probed = () => (coarse ? [buildings] : [buildings, enclosures, frontage]); // read at each look: a detail switch rebuilds them
  const nearestRecord = (hits) => {
    let best = null;
    for (const hit of hits) {
      if (!hit) continue;
      const record = loaded.registry.get(hit.id) ?? hit.record ?? null;
      if (!record) continue;
      if (!best || hit.distance < best.distance) best = { id: hit.id, record, distance: hit.distance };
    }
    return best;
  };
  target = createTarget({
    pick: () => nearestRecord(probed().map((layer) => (coarse ? layer?.pickAtBox?.(null, camera) : layer?.pickAt?.(null, camera)))),
    pickAsync: coarse ? null
      : () => Promise.all(probed().map((layer) => layer?.pickAtAsync?.(null, camera) ?? null)).then(nearestRecord),
    pose: () => ({ e: walker.state.e, n: walker.state.n, bearingDeg: walker.bearingDeg, pitchDeg: walker.state.pitch * 180 / Math.PI }),
  });
  api.target = target;
  let inspectHold = null; // T-2639: the building Inspect holds once it has closed the card
  // T-2654: the active Jaunt's stops as field points, for the Map app's dotted route. Each
  // stop resolves the way the Jaunt itself travels to it; kept until the Jaunt changes.
  let jauntRouteMemo = { id: null, stops: [] };
  // `jauntState`, not `s`: main.js binds `s` to a building's sidecar elsewhere, and
  // tools/validate.py's sidecar scan follows that name.
  function mapJauntRoute() {
    const jauntState = jauntRuntime?.state;
    if (!jauntState?.jaunt?.stops?.length) return null;
    if (jauntRouteMemo.id !== jauntState.jaunt.id) {
      const stops = [];
      for (const stop of jauntState.jaunt.stops) {
        const r = destinations.resolve(stop.destination);
        const t = r?.structureId ? { kind: 'structure', id: r.structureId } : r;
        const at = t ? travel.destinationOf(t, { card: false }) : null;
        if (at && Number.isFinite(at.e) && Number.isFinite(at.n)) stops.push({ id: stop.id, p: [at.e, at.n] });
      }
      jauntRouteMemo = { id: jauntState.jaunt.id, stops };
    }
    const current = jauntState.visited?.[jauntState.stopIndex]?.id;
    return { stops: jauntRouteMemo.stops.map((x) => x.p), at: jauntRouteMemo.stops.findIndex((x) => x.id === current) };
  }
  // T-2627 (§10): the HUD's target tag and the quick column's Inspect key — the same probe,
  // within 40 m, after a 400 ms dwell. Both open Inspect through the Navigator's registry
  // (Inspect's own screen since T-2638/T-2639), handing it this target.
  targetTag = createTargetTag({
    target,
    tagEl: document.getElementById('target-tag'),
    keyEl: document.getElementById('btn-inspect'),
    units: () => hud.settings.units,
    tagShown: hud.settings.lookTag !== false,
    // T-2942: right under the address by default, or the centre (its first place) or the
    // bottom row; fading by default. Docked, it never repeats the address the card shows.
    place: hud.settings.lookTagPlace,
    holdMode: hud.settings.lookTagHold,
    slots: (() => {
      const tagHome = document.getElementById('target-tag');
      const bottom = document.getElementById('hud-bottom');
      return {
        right: { parent: document.getElementById('instrument-below') },
        centre: { parent: tagHome?.parentNode ?? null, before: tagHome?.nextSibling ?? null },
        bottom: { parent: bottom, before: bottom?.firstElementChild ?? null },
      };
    })(),
    addresses: () => {
      const card = document.getElementById('street-readout');
      if (!card || card.hidden) return [];
      return ['street-historic', 'street-modern'].map((id) => document.getElementById(id)?.textContent ?? '');
    },
    onInspect: (t) => {
      // T-3022: as a click on the building does: Inspect, holding it until it is let go
      // (and a card left open on another building is put away first).
      if (t?.id && loaded.registry.get(t.id)) openBuilding(t.id);
      else if (navigatorUi?.select) void navigatorUi.select('inspect');
      else pick(t.id);
    },
  });
  targetTag.setEnabled(!gateOpen);
  api.targetTag = targetTag;
  // T-2640 (§08 "Look for", §13): Show me stands you outside the building on the line its
  // record's camera looks along, faces that bearing, and pulses an outline on the building.
  const showMeOutline = document.getElementById('show-me-outline');
  let showMeId = null, showMeOutlineGen = 0;
  function paintShowMeOutline() {
    const fp = footprints.find((f) => f.id === showMeId);
    if (!showMeOutline || !fp) return false;
    const record = loaded.registry.get(showMeId);
    const h = buildingBounds[showMeId]?.size?.[1] ?? record?.sidecar?.attributes?.wall_height_m?.value ?? 8;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, ahead = 0;
    const v = new THREE.Vector3();
    for (const [e, n] of fp.pts) {
      const g = terrain.surfaceHeight(e, n);
      for (const up of [0, h]) {
        v.copy(enuToWorld(e, n, g + up)).project(camera);
        if (v.z < 1) ahead++;
        const x = (v.x + 1) / 2 * innerWidth, y = (1 - v.y) / 2 * innerHeight;
        x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y);
      }
    }
    if (!ahead) return false;
    const pad = 8;
    Object.assign(showMeOutline.style, { left: `${Math.max(0, x0 - pad)}px`, top: `${Math.max(0, y0 - pad)}px`,
      width: `${Math.min(innerWidth, x1 + pad) - Math.max(0, x0 - pad)}px`, height: `${Math.min(innerHeight, y1 + pad) - Math.max(0, y0 - pad)}px` });
    return true;
  }
  const showMe = createShowMe({
    pose: () => ({ e: walker.state.e, n: walker.state.n, yaw: walker.bearingDeg, pitch: walker.state.pitch * 180 / Math.PI, flying: hud.flying }),
    place: ({ e, n, yaw, pitch }) => walker.teleport({ local_e: e, local_n: n, yaw_deg: yaw, pitch_deg: pitch }),
    land: () => hud.setFly(false, { announce: false }),
    // Drawn once the camera has drawn the frame it moved to (two animation frames); resolves
    // then, so show-me.js counts the 2 s from there. A later call supersedes a pending draw.
    outline: ({ on, pulse }) => {
      const gen = ++showMeOutlineGen;
      if (!showMeOutline) return undefined;
      if (!on) { showMeOutline.hidden = true; showMeOutline.classList.remove('is-pulsing'); return undefined; }
      return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => {
        if (gen === showMeOutlineGen && paintShowMeOutline()) {
          showMeOutline.hidden = false;
          showMeOutline.classList.toggle('is-pulsing', !!pulse);
        }
        resolve();
      })));
    },
  });
  function showMeFor(id, item) {
    const fp = footprints.find((f) => f.id === id);
    // Stand where the router lets you stand, and where no other building is in the way.
    const sighted = (e, n, we, wn) => {
      const lo = [Math.min(e, we) - 1, Math.min(n, wn) - 1], hi = [Math.max(e, we) + 1, Math.max(n, wn) + 1];
      const near = footprints.filter((f) => f.id !== id && f.pts.some(([x, y]) => x >= lo[0] - 30 && x <= hi[0] + 30 && y >= lo[1] - 30 && y <= hi[1] + 30));
      return !crossesShowMe([e, n], [we, wn], near.map((f) => f.pts));
    };
    const target = planShowMe(item, fp?.pts, { blocked: (e, n) => !!router.blockedAt?.(e, n), sighted });
    if (!target) return Promise.resolve(false);
    travel?.stop?.('show-me');
    showMeId = id;
    countField('showMe'); // T-2660
    return showMe.show(target);
  }
  api.showMe = { show: showMeFor, get last() { return showMe.last; }, cancel: () => showMe.cancel() };
  // T-2645: the Photos tab's From this spot — where a solved camera of the building says the
  // picture was taken, facing its way, with Show me's glide and outline. Never anywhere else.
  function fromSpotFor(id, picture) {
    const target = spotTarget(picture, loaded.registry.get(id)?.sidecar?.placement);
    if (!target) return Promise.resolve(false);
    travel?.stop?.('show-me');
    showMeId = id;
    return showMe.show(target);
  }
  api.fromSpot = fromSpotFor;
  navigatorUi = createNavigator({
    root: document.getElementById('navigator'),
    scene: loaded.scene,
    target,
    where: eraWhere,
    pose: () => ({ e: walker.state.e, n: walker.state.n, bearingDeg: walker.bearingDeg }),
    jaunt: () => jauntRuntime?.state ?? null,
    move: () => ({ flying: hud.flying, pace: hud.settings.pace, riding: (travel?.state?.phase ?? 'idle') !== 'idle' }),
    confidence: () => hud.confidenceOn,
    units: () => hud.settings.units,
    onInspect: (id) => openBuilding(id),
    // T-2622: its keys wait for the arrival to close, and Escape goes to the drawer or a
    // building card first when one is open.
    keysActive: () => !gateOpen,
    escFree: () => (document.getElementById('panel')?.hidden ?? true) && !popup.openId,
    // T-2618: the rail's apps (js/apps/), and what they read the page through. An app
    // takes what it needs from `ctx` — the api object included — and never imports main.js.
    apps: NAVIGATOR_APPS,
    context: () => ({
      api,
      scene: loaded.scene,
      journey: journey.state,
      // The card's building, or the one Inspect is holding: on a phone the card hides the
      // device, so Inspect closes it and holds its building for as long as Inspect stays open.
      selected: popup.openId ?? (navigatorUi?.app === 'inspect' ? inspectHold : (inspectHold = null)),
      // T-2627: what the HUD's tag is showing, for Inspect when the device's own probe is idle.
      target: targetTag?.current ?? null,
      // A scene has people when it has a people directory: 1835 loads its own at boot for the
      // drawer (the `residents` layer); a scene without that layer is asked after ready, with a
      // HEAD, and its directory is fetched only when People first opens (1904, T-2702).
      hasPeople: peopleDirectory.known,
      peopleSection: !document.querySelector('.panel-tab[data-tab="people"]')?.hidden && !!people,
      confidenceOn: hud.confidenceOn,
      jaunt: jauntRuntime?.state ?? null,
      whatsNewUnread: !document.getElementById('help-dot')?.hidden,
      // T-2661: the controls in use, for Guide's controls sheet (controls/intent.js).
      controls: backends.name,
      coarse,
      actions: {
        // The drawer's own sections, where they are until they move in (T-2620).
        openSection: (id) => { hud.setPanel(true); hud.selectTab(id); },
        inspect: (id) => (id ? openBuilding(id) : pick()),
        jaunts: () => { api.welcome.show(); api.welcome.enter('jaunts'); },
        // T-2630: what the Navigator's Jaunts app asks of the page.
        jauntList: () => openJauntList(),
        gotoList: () => api.welcome.refresh?.(),
        freeRoam: () => { navigatorUi?.dock(); roamTip.show({ touch: backends.name === 'touch' }); },
        map: () => navigation.setFullVisible(true),
        // T-2654: the Map app's Go (the getting-there style decides how), the active
        // Jaunt's stops for its dotted route, and a ride's remaining waypoints.
        goTo: (id) => goToTarget({ kind: 'structure', id }),
        jauntRoute: () => mapJauntRoute(),
        travelRoute: () => travel.routeAhead(),
        // T-2735: Recall asks first; the journey moves only as the page leaves.
        recall: (href) => recallHome?.ask(href),
        peopleDirectory: () => peopleDirectory.load(),
        onControls: (fn) => backends.onChange(fn),
        // T-2662: the Guide's questions, read the first time Guide opens, never at boot.
        guideFaq: () => (guideFaq ??= fetch(new URL('guide/faq.json', resolveBases().dataBase), { cache: 'no-cache' })
          .then((res) => { if (!res.ok) throw new Error(String(res.status)); return res.json(); })
          .catch((err) => { guideFaq = null; throw err; })),
        // T-2666: a destination's Jaunt catalog, for the teacher handout's suggested Jaunts;
        // read the first time Guide opens, never at boot. No catalog is no Jaunts.
        jauntCatalog: (year) => (jauntCatalogs[year] ??= fetch(new URL(`sidecars/${encodeURIComponent(year)}/jaunts/catalog.json`, resolveBases().dataBase), { cache: 'no-cache' })
          .then((res) => { if (res.status === 404) return []; if (!res.ok) throw new Error(String(res.status)); return res.json().then((doc) => doc?.jaunts ?? []); })
          .catch((err) => { delete jauntCatalogs[year]; throw err; })),
        // T-2667: Guide › About this destination opens one of its cards in the section
        // under the Guide's sheet (the old research hub, js/evidence.js).
        aboutCard: (id) => {
          if (!hud.panelOpen()) hud.setPanel(true);
          hud.selectTab('evidence');
          return api.evidenceHub?.showCard?.(id) ?? false;
        },
        // T-2638: what Inspect's front page reads. The compiled summaries (inspect/<scene>.json,
        // tools/compile_summaries.py), the pictures (the card's own file), a building's record,
        // and the card itself, on a tab, as the full record until the Inspect tabs (T-2639).
        inspectSummaries: () => Promise.all([ensureInspect(), ensureReaderText().catch(() => null)]).then(([doc]) => doc),
        pictures: () => ensurePictures(),
        // T-2825: the record as the card says it — its notes without a ticket, a record id or
        // a file path, once the scene's reader overlay is in (inspectSummaries waits for it).
        record: (id) => {
          const record = loaded.registry.get(id);
          return record ? { ...record, sidecar: popup.say(record.sidecar) } : null;
        },
        // T-2639: the card's content as Inspect's tabs show it, once the lazy data it reads
        // (liberties, pictures, a seated record's household notes) is in hand.
        cardSections: async (id) => {
          const record = loaded.registry.get(id);
          if (!record) return null;
          ensureHouseholdNotes(record);
          await Promise.all([ensureLiberties(), ensurePictures(), householdNotes.get(record.id), ensureReaderText()].map((x) => Promise.resolve(x).catch(() => null)));
          return popup.sections(record);
        },
        // A person by directory id: in the drawer's People section where the scene has one
        // (1835), else the Navigator's People screen (1904, T-1740).
        openPerson: (id) => {
          if (api.people && !document.querySelector('.panel-tab[data-tab="people"]')?.hidden) {
            hud.setPanel(true); hud.selectTab('people'); api.people.open?.(id); return true;
          }
          return navigatorUi?.select?.('people');
        },
        openPicture: (id, i) => openPictureViewer(popup.picturesDoc, id, i),
        holdInspect: (id) => { inspectHold = id ?? null; },
        closeCard: () => popup.close(),
        openCard: (id, tab) => {
          const hit = pick(id);
          if (hit && tab) document.querySelector(`#popup [data-pop-tab="${tab}"]`)?.click();
          return hit;
        },
        // T-2640: Show me — only along a camera the building's own summary record names.
        showMe: (id, item) => showMeFor(id, item),
        fromSpot: (id, picture) => fromSpotFor(id, picture),
      },
    }),
  });
  api.navigator = navigatorUi;
  // T-3022: Inspect opened on a building by hand is let go once the device leaves it.
  navigatorUi?.onChange?.(({ app, level }) => { if (handInspect && !handInspect.opening && (app !== 'inspect' || level === 0)) handInspect = null; });
  api.openBuilding = openBuilding;
  /** T-3022: put away what the visitor has open on a building: the card, or Inspect. */
  api.closeBuilding = () => { popup.close(); if (handInspect) releaseInspect(); };
  /** T-3022: the building on screen for the visitor — the card's, or Inspect's while it is open
   *  (from the moment it is asked for: a first open loads Inspect before it draws). */
  Object.defineProperty(api, 'inspecting', { enumerable: true, configurable: true,
    get: () => popup.openId ?? handInspect?.id ?? (!letting && navigatorUi?.app === 'inspect' && navigatorUi.level > 0
      ? (document.getElementById('nav-app-inspect')?.dataset.structure || null) : null) });
  // T-2620: the drawer's sections now live in the Navigator's apps; hud.setPanel and
  // hud.selectTab open and close them there.
  // Go to is not a drawer section any more but the Jaunts app's own segment (T-2630): G and
  // hud.selectTab('goto') open it. Its search takes focus for a keyboard, not on a phone,
  // where focusing raises the on-screen keyboard over the list the tap was for.
  installDrawerHost({ hud, navigator: navigatorUi, openGoTo: async () => {
    await api.openJaunts?.('goto');
    if (coarse && document.activeElement?.id === 'welcome-search') document.activeElement.blur();
  } });
  // (T-2655's year chip opens Jump through T-2626's #year-badge binding above.)
  // T-2662: a locked term's first appearance explains itself on tap — the Navigator's
  // Confidence view, and the Evidence hub's Liberties (the arrival's intro marks its own).
  markTerms(document.getElementById('nav-home'));
  markTerms(document.querySelector('.ev-topic[data-topic="liberties"] .ev-topic-title'));
  // T-2630 (§04 E, §07): the Navigator Home's three choices open the Jaunts app on their
  // segment — Jaunts, Go to, Free roam — as the Welcome card's three do on the arrival.
  api.openJaunts = async (segment = 'jaunts') => {
    const ok = await navigatorUi?.select('jaunts');
    if (ok) api.jauntsApp?.segment(segment, { by: 'hand' });
    return !!ok;
  };
  for (const choice of document.querySelectorAll('#nav-home [data-segment]')) {
    choice.addEventListener('click', () => { void api.openJaunts(choice.dataset.segment); });
  }
  // T-2621: Back closes the Navigator before it leaves the page (nav-link.js), and a deep
  // link (?nav=app[:id]&tab=) opens its app once the landing is over. A link to an app the
  // rail does not have, or to a building this scene does not hold, is dropped quietly.
  api.navHistory = createNavHistory({ nav: navigatorUi });
  if (navLink && navigatorUi?.has(navLink.app)) {
    const link = navLink.app === 'inspect' && navLink.id && !loaded.registry.has(navLink.id)
      ? null : navLink;
    const open = () => {
      if (!link) return;
      // Jaunts opens on the arrival device itself; every other app is in the town, so the
      // visitor is set down at the spawn (as Free roam does) and the device opens on it.
      if (link.app !== 'jaunts' && api.welcome?.state === 'welcome') api.welcome.enter('spawn');
      void navigatorUi.openLink(link);
      api.navLinkOpened = link;
    };
    if (journey.state === 'landed' || journey.state === 'exploring') open();
    else {
      const off = journey.on(({ to }) => { if (to === 'landed') { off(); setTimeout(open, 0); } });
    }
  }

  // ---- T-2663: Tour mode, the Field Check ------------------------------------------
  // Eight steps (js/tour.js), each completing on its real action, read here every quarter
  // second while it runs; replayed from the section Guide opens (#tour-start); a reload
  // mid-tour resumes at the same step once the visitor is back in the town.
  let tourTimer = null, tourApp = null;
  // T-2954: each Navigator app opened, counted as it opens (Move and Settings are steps).
  let navOpenWas = null;
  navigatorUi?.onChange?.(({ app, level }) => {
    const now = level > 0 ? app : null;
    if (now && now !== navOpenWas) tourCounts.apps[now] = (tourCounts.apps[now] ?? 0) + 1;
    navOpenWas = now;
  });
  const tourOverlay = createTourOverlay({ onNext: () => tour.press(), onSkip: () => tour.skip() });
  const tour = createTour({
    probe: () => {
      // Inspect opening on a structure counts as opening its record, as the card does.
      const app = navigatorUi?.app ?? null;
      if (app === 'inspect' && tourApp !== 'inspect') tourCounts.opens++;
      tourApp = app;
      const level = navigatorUi?.level ?? 0;
      return { yawDeg: walker.bearingDeg, e: walker.state.e, n: walker.state.n, opens: tourCounts.opens,
        apps: { ...tourCounts.apps }, touch: backends.name === 'touch', level,
        selected: !!popup.openId || (app === 'inspect' && level > 0), card: !!popup.openId,
        scene: loaded.scene?.id ?? YEAR, front: navigatorUi?.snapshot?.()?.front?.name ?? null };
    },
    render: (v) => {
      tourOverlay.paint(v);
      if (v && !tourTimer) tourTimer = setInterval(() => { tour.tick(); tourOverlay.place(); }, 250);
      if (!v && tourTimer) { clearInterval(tourTimer); tourTimer = null; }
    },
    onFinish: () => awardLicense(),
  });
  api.tour = tour;
  // T-2665: Finish (never Skip) awards the Navigator License, and the hint line says where it
  // is kept, once: a replay that finishes again keeps the one license and says nothing.
  let licenseTimer = null;
  function awardLicense() {
    if (!license.award()) return false;
    const el = document.getElementById('nav-hint');
    if (!el) return true;
    hints.hide();
    el.textContent = license.awardedText(); el.dataset.hint = 'license'; el.hidden = false;
    clearTimeout(licenseTimer);
    licenseTimer = setTimeout(() => { if (el.dataset.hint === 'license') el.hidden = true; }, HINT_MS);
    return true;
  }
  document.getElementById('tour-start')?.addEventListener('click', () => { hud.setPanel(false); tour.start(); });

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
    gate?.classList.toggle('welcome-compact', h <= 500);
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

  /**
   * T-2106. The milliseconds of a frame the flora's near rebuild may spend: the
   * animation loop spreads a pass over the frames its margin allows rather than
   * paying for it all in the frame that needs it, which on a phone was a 44 ms
   * hitch on every small turn. `step()` keeps the whole pass in one frame,
   * because every test that drives it reads the buffers straight after;
   * `setFloraSpread(true)` lets a measurement drive the loop's own behaviour.
   */
  const FLORA_SLICE_MS = 4;
  let stepFloraSpread = false;

  function tick(floraBudget = FLORA_SLICE_MS, force = false) {
    // Keep visual simulation stable, but do not make a visitor crawl in direct
    // proportion to a slow renderer. At 2 fps the former 0.05 s clamp advanced
    // walking by only 0.10 s per real second. Movement now consumes up to a
    // quarter-second of real frame time in <= 0.05 s collision/terrain steps.
    // The clock is read either way, so releasing a hold does not deliver the
    // whole held interval as one enormous frame.
    const elapsed = Math.min(clock.getDelta(), 0.25);
    const frameDt = animationHold || gateOpen ? 0 : elapsed;
    const dt = Math.min(frameDt, 0.05);

    if (!gateOpen) backends.active?.update?.(dt);
    else intent.clear();
    terrain.update(dt);
    const asked = intent.takeInteract();
    if (asked && !gateOpen) travel.stop('input');
    // The inspect KEY toggles: the reach that opened the card also closes it
    // (T-0108). Since T-2954 a click or tap on the scene does too: an open card
    // holds the visitor until it is closed or the town is touched again (the owner,
    // 2026-10-20), so a second building is one more click away, not one less.
    // T-3022: Inspect opened on a building by hand is released the same way.
    if (asked && popup.openId) popup.close();
    else if (asked && inspectingByHand()) releaseInspect();
    else if (asked) inspect(asked.point ? new THREE.Vector2(asked.point.x, asked.point.y) : null, { by: 'hand' });
    const walkSteps = Math.max(1, Math.ceil(frameDt / 0.05));
    const walkDt = frameDt / walkSteps;
    if (!gateOpen) for (let i = 0; i < walkSteps; i++) {
      // Steering and movement consume the same time step. Reusing one steering
      // decision for five walker steps on a slow frame overshot street corners.
      travel.update(walkDt, intent);
      walker.update(walkDt, intent);
      travel.afterWalk(intent, walkDt);
    }
    // Before the render, after the walker: the near plane is a function of where
    // the eye ended up this frame (R-BUG1, and the NEAR block above).
    setNearFor(walker.state.altitude);
    world.follow(camera.position);
    // T-1631, at the same moment and for the same reason: the haze is a
    // function of the bearing the eye ended up facing this frame. `aim` reports
    // whether it actually moved, so the two surfaces that copy the haze are
    // only rewritten on the frames the view crossed one of the ring's bearings.
    if (world.aim(camera)) terrain.setHaze(scene3d.fog?.color);
    // After the camera has finished moving and before anything is submitted:
    // what the furniture's reach hides is a function of where the eye ended up
    // this frame (T-0150).
    updateFurnitureReach();
    // The same moment, for the same reason, one layer further down: what the
    // ground's reach holds back is a function of where the eye ended up this
    // frame (T-1154).
    terrain.updateGroundReach(camera.position);
    flora.update(dt, camera, floraBudget);
    trees.update(dt, camera, scene3d.fog?.color);
    streetTrees.update(dt, camera);
    streetFurniture.update(dt, camera);
    frontYards.update(dt, camera);
    railway.update(camera);
    flags.update(dt);
    parkedTransport.update(camera);
    standingHorses.update(camera, frameDt, { paused: animationHold || gateOpen });
    // T-2598: which house pictures are on the GPU, from where the eye ended up; at
    // most a frame's allowance of them is uploaded here, before the draw.
    residency?.tick(camera.position);
    api.humans?.update(dt, camera, walker.state);

    // T-2113. Under the gate, draw only a frame that differs from the last one
    // drawn: the first, one a capture or a test asked for, or one in which
    // something the renderer reads has moved. Out in the town, every frame.
    if (!gateOpen || force || pendingCapture || gateFrame.due()) {
      // T-2646: `renderer.render(scene3d, camera)`, and — only while a grade is
      // ghosted with the Confidence view on — that grade drawn see-through, last,
      // in a pass of its own (confidence.js § render).
      confidence.render(renderer, scene3d, camera);
      bootController.frameRendered();
      resolveFirstFrame();
    }

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
    if (!gateOpen) { target?.tick(performance.now()); navigatorUi?.update(); }

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
  // T-2158: before anything is uploaded, a phone marks the layers that may let
  // go of their page arrays once the GPU has them (upload-release.js).
  if (coarse) releaseAfterUpload(scene3d);
  // Compile programs while the gate can still repaint, before the first draw.
  // The horizon creates its initial geometry on update, so include that too.
  trees.update(0, camera, scene3d.fog?.color);
  await yieldToPaint();
  for (const layer of scene3d.children) {
    if (layer.isLight) continue; // targetScene already supplies the lights
    await renderer.compileAsync(layer, camera, scene3d);
    const pause = bootCheckpoint(); if (pause) await pause;
  }
  await yieldToPaint();
  // T-2555. Whether the camera moved in the frame just drawn — position or
  // facing, so a turn in place is moving too. The governor reads only this and
  // the interval between drawn frames.
  const lastPose = { position: new THREE.Vector3(), quaternion: new THREE.Quaternion(), seen: false };
  function cameraMoved() {
    const moved = !lastPose.seen
      || camera.position.distanceToSquared(lastPose.position) > 1e-8
      || 1 - Math.abs(camera.quaternion.dot(lastPose.quaternion)) > 1e-10;
    lastPose.position.copy(camera.position);
    lastPose.quaternion.copy(camera.quaternion);
    lastPose.seen = true;
    return moved;
  }
  /** The governor's decision for the frame about to be drawn, put in force. */
  function applyGovernor() {
    applySharpness();
    const shadow = renderer.shadowMap;
    shadow.autoUpdate = governor.shadowFresh;
    if (!governor.shadowFresh) shadow.needsUpdate = false;
  }
  // T-2826: what the visitor has open, as a step in the black box when it changes.
  let seenCard = null, seenNav = null;
  function watchSteps() {
    const card = popup.openId ?? null;
    if (card !== seenCard) { blackbox.log(card ? 'card' : 'card-closed', card ? { id: card } : null); seenCard = card; }
    const nav = navigatorUi ? `${navigatorUi.level}:${navigatorUi.app ?? ''}` : null;
    if (nav !== seenNav) { if (seenNav !== null || nav !== '0:home') blackbox.log('nav', { level: navigatorUi?.level, app: navigatorUi?.app ?? null }); seenNav = nav; }
    blackbox.tick();
  }
  renderer.setAnimationLoop((t) => {
    try {
      watchSteps();
      governor.setTier(detailLevel);
      // A capture, the welcome and a held clock are still frames by definition,
      // and are drawn exactly as they were before the governor existed.
      if (pendingCapture || gateOpen || animationHold) governor.rest();
      else if (!governor.shouldDraw(t)) return;
      applyGovernor();
      tick();
      governor.frameDrawn(t, cameraMoved());
    } catch (err) {
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
    detailLevels,
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
    // T-2825: the scene's reader overlay, loaded and handed to the card; resolves to it.
    readerText: () => ensureReaderText(),
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
    spawnAtDestination,
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
      const budget = currentBudget();
      // T-2970: `drawCalls` is the driver's draws, the figure the budgets are held
      // to; `rendererCalls` is three's own count, which takes a BatchedMesh's whole
      // multi-draw as one and is kept so the readings before T-2970 stay comparable.
      const drawCalls = driverDraws.draws;
      return {
        drawCalls,
        rendererCalls: info.render.calls,
        multiDraw: driverDraws.native,
        triangles: info.render.triangles,
        programs: info.programs?.length ?? 0,
        geometries: info.memory.geometries,
        textures: info.memory.textures,
        batches: buildings.batches.length,
        // T-1963: what the walls were bound with, or `{ off: true }` under ?walls=flat.
        wallRelief: buildings.wallRelief,
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
        budget,
        withinBudget: drawCalls <= budget.drawCalls
          && info.render.triangles <= budget.triangles,
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
    /** T-1976, HARNESS ONLY and never a visitor setting, for the reason
     *  `setFurnitureReach` above is one: drive the detailed ground's reach
     *  directly so a sweep can read candidate reaches at one page load. `null`
     *  restores the tier's own. The live reading is `groundReach()`. */
    setGroundDetailReach(m) {
      return terrain.setDetailReach(typeof m === 'number'
        ? m : (DETAIL[detailLevel] ?? DETAIL.full).groundDetailReachM);
    },
    /** T-0146, HARNESS ONLY and never a visitor setting, for the reason
     *  `setFurnitureReach` above is one: the merge's whole claim is that it
     *  changes the call count and not the triangle count, and the only honest
     *  way to read that is the same frame with it off and with it on.
     *  `tools/measure_far_merge.mjs` is what does. */
    /** T-2529, HARNESS ONLY, for the same reason: the cull's claim is that it
     *  changes the triangle count and not the picture, and the only honest way
     *  to read that is the same frame with it off and on
     *  (`tools/qa_shadow_casters_t2529.mjs`). The tier sets it back on change.
     *  Returns what took effect and how many pieces it has left out so far;
     *  called with no argument it only reads. */
    setCastersTowardView(on) {
      if (on !== undefined) shadowCasters.on = Boolean(on);
      return { on: shadowCasters.on, culled: shadowCasters.culled };
    },
    setFarMerge(on) {
      const state = farMerge.setEnabled(on);
      // The merge only ever hides a chunk; the reach is what makes one visible
      // again, so turning the merge OFF has to run that pass rather than just
      // hiding the batches.
      updateFurnitureReach();
      return state;
    },
    /** Force one frame — for tests that must not race the animation loop. */
    step() { governor.rest(); applyGovernor(); tick(stepFloraSpread ? FLORA_SLICE_MS : Infinity, true); },
    /** T-2555: Adaptive (true) or Fixed (false), as Settings' Frame pacing sets
     *  it; the live reading is `governor` below. */
    setGovernor(on) { const v = governor.setEnabled(on); applyGovernor(); return v; },
    /** T-2555, HARNESS ONLY: force the governor's scale and pace, as a slow
     *  moving window would, so a GPU-less runner can ask what a rest does. */
    forceGovernor(state) { return governor.force(state); },
    /** T-2106. Let `step()` spread the flora rebuild as the animation loop
     *  does — for `tools/measure_walk_frames.mjs`, which times that loop. */
    setFloraSpread(on) { stepFloraSpread = !!on; return stepFloraSpread; },
    /** Keep rendering, advance nothing — for tests comparing two frames of the
     *  same scene. Never set by the application. */
    setAnimationHold(on) { animationHold = !!on; return animationHold; },
    /** Same-camera on/off proof, like setFarMerge; no visitor setting. */
    setGlessnerOcclusion(on) { return glessnerOcclusion?.setEnabled(on) ?? false; },
    glessnerOcclusionStats() { return glessnerOcclusion?.stats ?? {active:false}; },
    /** T-3152: the proven planar backings alone, for the same on/off proof. The filter
     *  caches its occluders by camera, so the next frame is re-projected either way. */
    setPlanarCovers(on) { const v=buildings.setPlanarCovers?.(on) ?? false; glessnerOcclusion?.setEnabled(glessnerOcclusion.enabled); return v; },
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
    /** T-2037, harness-only: exact deck tops currently replacing reach-culled chunks. */
    farWalkTops: { get: () => frontage.farWalkTops ?? null, enumerable: true },
    /** The level the visitor is actually on, now rather than at boot (T-0115). */
    detail: { get: () => detailLevel, enumerable: true },
    /** T-2555: what the frame governor is doing now — its mode, the scale of the
     *  Sharpness ceiling and the pixel ratio drawn, the paced rate, the shadow's
     *  cadence and whether the camera is moving. */
    governor: { get: () => ({ ...governor.state, ceiling: sharpnessCap, ratio: renderer.getPixelRatio() }),
      enumerable: true },
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
            if (o.userData.farMerged || o.userData.farWalkTops) return;
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
            if (o.userData.farMerged || o.userData.farWalkTops) return;
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
    /** T-2113. Ticks the welcome let pass without drawing an unchanged town. */
    gateFramesHeld: { get: () => gateFrame.held, enumerable: true },
    controlBackend: { get: () => backends.name, enumerable: true },
    footprints: { get: () => footprints, enumerable: false },
    decks: { get: () => decks, enumerable: false },
    roadAid: { get: () => streets.legibilityAid, enumerable: true },
    brightness: { get: () => world.brightness, enumerable: true },
    exposure: { get: () => renderer.toneMappingExposure, enumerable: true },
    facadeWeathering: { get: () => buildings.weathering, enumerable: true },
    uploadRelease: { get: () => uploadReleaseState(), enumerable: true },
    /** T-2548: GLBs banked for a detail switch — none on a phone. */
    bankedAssets: { get: () => loaded.bankedAssets, enumerable: true },
    /** T-2597: the boot pool, and the most GLB bytes it held unparsed at once. */
    bootPool: { get: () => loaded.bootPool, enumerable: true },
  });
  // T-2732: Settings' dev-only Read frame pacing, for the reading T-2733 takes on
  // a phone. Mounted after the live readings above, which it drives and restores.
  mountPacingRead({ api, hud });

  // Optional census work may finish later; it cannot hold the street closed.
  await firstFrame;
  bootController.end('interaction');
  // Ground protection can replace terrain batches while later layers build.
  // Install the hooks only after the final startup geometry is in the scene.
  refreshGlessnerOcclusion();
  api.ready = true;
  setTimeout(() => peopleDirectory.ask(), 0);
  if (!bootController.finish()) {
    api.ready = false;
    if (gateBtn) gateBtn.disabled = true;
    throw new Error('Boot readiness barrier failed');
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
