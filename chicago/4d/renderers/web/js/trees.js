/**
 * trees.js — every woody plant taller than three metres, and the timber on the
 * horizon.
 *
 * Parcel `timber-edge`. It draws the two things the sward cannot:
 *
 *   1. **The near timber inside the 640 m box** — the riverbank gallery forest,
 *      the body of timber on the North Division, the sand-ridge oak stringers
 *      threading it, and the sandbar-willow thickets on the point bars.
 *   2. **The timber on the horizon** — the bodies the sources put BEYOND the
 *      modelled ground, drawn as a silhouette band at their true bearing,
 *      angular height and atmospheric contrast.
 *
 * `docs/research/02-flora.md` is the authority: § 1.4, § 1.5 (what the "Dense
 * Forest" north-east of the forks actually was), § 1.6 (the named groves), and
 * ZONE 5, ZONE 6, ZONE 7.
 *
 * The four rules this file is built to obey
 * -----------------------------------------
 *
 * **The plain was OPEN.** Andreas: *"The West Side was an open prairie, entirely
 * free from timber, except for a grove up the South Branch."* The West Division
 * therefore carries NO woody vegetation at all — no gallery, no thicket, not a
 * scattered oak. A treeline in the wrong place is a bigger error than an empty
 * horizon.
 *
 * **The timber was THIN.** § 0: across all PLS corners, 39% of the landscape was
 * open savanna (0–10 trees/ha) and 31% closed savanna (10–50/ha); even ground
 * the surveyors called *timber* was 64% savanna-density, and most bearing trees
 * were 12 inches dbh. Nothing here is a closed eastern hardwood forest: the mean
 * canopy tree is ~30 cm dbh and 15–20 m, and the crowns are open-grown.
 *
 * **Fire made the pattern.** McBride & Bowles found density and fire-intolerant
 * species concentrated on the EAST sides of watercourses, which broke prairie
 * fire running west to east. So the timber sits on the north and east banks and
 * the west banks stay prairie — independently what Andreas describes.
 *
 * **It is July.** Full summer canopy on every woody plant, no autumn colour. The
 * woodland floor (wood nettle, ferns, leaf litter — not spring ephemerals)
 * belongs to `flora.js`, which draws everything at or below 3 m.
 *
 * Why the horizon band computes its own haze
 * ------------------------------------------
 * The band is drawn on a ring at a fixed radius, so the scene's fog — which
 * works on distance to the geometry — would haze a grove four miles out exactly
 * as hard as a treeline at eleven hundred metres. It therefore runs `world.js`'s
 * own haze law by hand against each body's REAL distance, with `fog: false` so
 * the scene does not apply it twice, and one departure: a cap, because the
 * scene's haze is deliberately total by 1500 m and the dossier's horizon timber
 * is at three to six miles. See HAZE_MAX, and docs/LIBERTIES.md **L35**, which
 * records the cap as the liberty it is.
 *
 * What is deliberately NOT drawn
 * ------------------------------
 * The Big Woods of north-east Cook, Blue Island, La Framboise Woods and Cottage
 * Grove are all in § 1.6 and all are omitted: at 6 to 14 miles a 60-foot tree on
 * a flat lake plain stands less than a tenth of a degree above a standing eye's
 * horizon — under two pixels, below the contrast threshold, and in two cases
 * below the horizon entirely. `stats.omitted` carries the arithmetic so a critic
 * can check it. Drawing them would be prettier and would be a lie about how far
 * you can see from a flat plain.
 *
 * Where the numbers come from
 * ---------------------------
 * Species, July height, crown width, July foliage colour and confidence are
 * READ FROM `data/flora/zones/*.json` (roles `tree` and `thicket`) through the
 * manifest, per the CONTRACT: the dataset is the durable artifact and a renderer
 * with its own copy of the ecology drifts from it. What stays here is what the
 * records do not carry — the draw archetype per form, and WHERE a tree stands.
 * Zone extents describe ground communities; a tree's position is a question
 * about banks, ridges, fire and which side of the river the town was cutting,
 * answered from the heightfield. The tables below are render parameters and the
 * fallback for a species the records do not describe.
 */

import * as THREE from 'three';
import { floraInScene } from './flora.js';
import { createTreeAtlasSliced, leafFamily, treeAtlasUV, TREE_ALPHA_CUTOFF, patchTreeWind } from './tree-surface.js';
import { TreeInstances, createGrownTreeMaterials, isGrownForm } from './tree-instances.js';
import { resolveBases } from './scene-loader.js';

/**
 * The zone records this module reads, by the CONTRACT's `z<NN>_<slug>` id. Only
 * these are opened, and only through the path the manifest gives: the repo smoke
 * fails on any HTTP >= 400, so nothing here may probe for a file.
 */
const TIMBER_ZONES = [
  'z05_riverbank_timber', 'z06_dense_forest', 'z07_bur_oak_savanna', 'z08_lakeshore',
  'z10_settled_town',
  // T-2784: the prairie and slough zones, read for their shrubs only (none of
  // them records a tree or a thicket): PRAIRIE_WOODY draws them on the open plain.
  'z01_wet_prairie', 'z02_mesic_prairie', 'z03_sedge_meadow', 'z04_marsh',
];

/**
 * THE ZONE WHOSE GROUND THIS FILE ASKS THE SWARD FOR (ROADMAP K45(b) change one).
 *
 * Every other community here is selected from the heightfield — bank distance,
 * land division, a generated relief field. The dune cannot be: what makes it a
 * dune is the SUBSTRATE, and the substrate is not in the heightfield. It is in
 * `data/flora/zones/z08_lakeshore.json`'s extent, which `flora.js` already
 * resolves against every other zone's extent by priority to decide which sward
 * a visitor is standing in. So this file asks that classifier rather than
 * carrying a second copy of the beach: the cottonwoods stand on the sand you can
 * SEE, and moving the zone moves both together. If the sward did not load, the
 * answer is null and no dune is planted — the safe direction.
 */
const DUNE_ZONE = 'z08_lakeshore';
/** The roles THIS file draws out of a zone's woody list, so a `woody_stratum`
 *  block that binds only `shrub_low` (flora.js's stratum) does not silently
 *  thin the timber this loop plants. T-1056. */
const DUNE_WOODY_ROLES = ['tree', 'thicket'];
/** T-2768: the sand prairie the North Division's sand hills stand on, east of
 *  the timber's limit. */
const SAND_PRAIRIE_ZONE = 'z09_sand_prairie';

/* -------------------------------------------------------------------------- */
/* the physical constants this file reasons with                               */
/* -------------------------------------------------------------------------- */

/** Below this the heightfield is under water (same value terrain.js uses). */
const SHORE_Y = -0.10;
/**
 * How far ABOVE the water surface a stem's root has to stand.
 *
 * `terrain.isWater()` — the mask the gallery, the divisions and the release
 * smoke are all built on — asks whether the heightfield is below SHORE_Y, which
 * is 100 mm BELOW the water plane. It is the right question for "is this the
 * river", and it was the wrong question for "may a tree stand here": the water
 * surface is Z = 0 and the ground is drawn under it, so a stem rooted anywhere
 * in the 100 mm band between SHORE_Y and the datum passes the mask and then
 * renders standing in open water with its foot invisible. Thirty-six of the
 * scene's 618 stations were in that band, and because a gallery-edge willow may
 * stand at bank distance zero they were exactly the ones nearest the camera
 * across the channel. The fort views show timber ALONG the river and never in
 * it — see the module header and docs/research/02-flora.md ZONE 5.
 *
 * 0.20 m, and the number is the geometry rather than a taste: `addTree` sinks a
 * bole 0.15 m below its ground point so no trunk floats on uneven cells, and the
 * baked ground mesh is allowed to depart from the heightfield the placement
 * samples by up to 0.03 m (`generators/terrain_gen.py` MESH_FIT_TOLERANCE_M).
 * 0.15 + 0.03 puts the deepest modelled bark exactly at the water plane, so
 * 0.20 leaves 20 mm of daylight under the worst case and nothing more.
 *
 * This is a placement floor, NOT a new waterline: `isWater` still answers the
 * river question, the bank distance field is still measured to it, and the
 * willows the sources put at the water's edge still stand at the water's edge —
 * a few metres back up a bank that rises 0.2 m, which on the documented South
 * Division marsh strip is a handful of metres and on the north bank is under one.
 */
const TREE_DRY_MARGIN_M = 0.20;
/**
 * Below this is navigable channel rather than a shallow slough. Used only to
 * split the box into its three land divisions: the North Branch, the main stem
 * and the South Branch are all deeper than this, and the documented unnamed
 * slough on the north side is not, so the divisions come out as the three land
 * masses a person in 1835 would have named.
 */
const CHANNEL_Y = -0.60;

/**
 * WHERE THE TIMBER STOPS IN THE EAST, and why these are street ids rather than
 * two numbers written here.
 *
 * ROADMAP K45(b2). The woody planter used to sweep a fixed square, E/N
 * −316..+316, inside a field S2e carried east to E +1700 — so 73 % of the
 * modelled ground above the planter's own dry floor had never had a stem
 * offered to it. Widening the sweep to the field is one line. Deciding what may
 * grow on the ground it newly reaches is the parcel, and Andreas answers it for
 * both divisions in the same sentence the gallery is already built from:
 *
 *   "On the South Side, a body of timber grew along the river, extending east
 *    as far as WELLS STREET, and following the bend of the river, crossed Clark
 *    Street, and extending south two or three miles" — and the North Side
 *    carried "a body of thrifty heavy growth of timber", EXCEPTING "the sandy
 *    hills near the lake and the marshy places".
 *
 * So the South Division belt has a documented east end — Wells Street — and the
 * North Division one has a documented exception rather than a street: the sandy
 * hills. `z09_sand_prairie` places the relict beach-ridge belt from the State
 * Street break-of-slope east, and `generators/terrain_gen.py` builds that break
 * between E +780 and +880 off the two State Street ground-control points. State
 * Street is therefore where the North Division's timber gives way to the sand,
 * and the woody community that belongs east of it — the open-dune poplars of
 * `z08_lakeshore` — is ROADMAP K45(b) change one and is not built yet. Ground
 * with no community is ground with no stem, which is the honest state of it.
 *
 * They are ids and not numbers because `data/streets/1835.json` already holds
 * both centrelines, surveyed off Wright 1834, and a limit quoted from a street
 * has to move when the street does. Wells stands at E +329.3 and State at
 * E +825.8 in the committed data; the old square's east edge was E +316, so the
 * South Division belt was accidentally within 13 m of its documented end all
 * along and the North Division's was 510 m short of the sand.
 */
const TIMBER_EAST_LIMIT_STREETS = { south: 'wells', north: 'state' };
/** T-2745: the same two lines for a scene with no streets, at the mean eastings
 *  of `data/streets/1835.json`'s Wells and State centrelines (Wright 1834). */
const LANDFORM_EAST_M = { south: 328.7, north: 825.1 };

/** Earth radius corrected for standard atmospheric refraction (k = 0.13). */
const R_EFF = 6371000 / 0.87;

/**
 * The scene's own haze, copied from `world.js` — `FogExp2(HORIZON_HAZE,
 * HAZE_DENSITY)`. Copied, not imported: world.js belongs to another
 * parcel this round and a cross-parcel import that breaks takes the page with
 * it. **If world.js's haze moves, move these.** The band runs the law by hand
 * against each body's REAL distance because it is drawn on a ring at a fixed
 * radius, where the scene's own fog would haze a grove four miles out exactly
 * as hard as a treeline at eleven hundred metres.
 *
 * T-1635: that instruction is now GATED rather than left to whoever edits
 * world.js. `tools/check_haze_reach.mjs` reads both literals and refuses a tree
 * where they disagree, because the drift this copy invites is silent — the band
 * and the ground it stands on would simply run different atmospheres, which is
 * the same class of fault as the tone curve this file's own cap note records.
 */
const HAZE_DENSITY = 0.00089;
/**
 * The fog COLOUR, copied verbatim from `world.js`'s `HORIZON_HAZE`. It is the
 * colour distance goes to, and it is deliberately not the sky: real haze pushes
 * distance BLUE, and the value here is the one the atmosphere parcel retargeted
 * to for that reason (the bar's distant land runs B-R +27; the grey-green this
 * replaced ran -13).
 *
 * **This hex IS the rendered colour, and this file spent three weeks assuming
 * it was not.** `world.js` feeds it to `FogExp2`, whose lerp runs after the
 * tone curve on a uniform uploaded in the output colour space, so a fully
 * fogged pixel displays sRGB (136,163,192) — this value, unmodified. The band
 * matches the fogged GROUND by decoding the same hex once and no more; see
 * `hazeDisplayLinear()`, which used to do more and is what put the band and the
 * ground in different tonal worlds.
 */
const HORIZON_HAZE = 0x88a3c0;
/**
 * The cap, and the one place this file argues with the scene's atmosphere.
 * world.js's haze goes total at the outer edge of L17's ground apron, because
 * that edge is what it exists to close over. But the dossier § 1.6 is a table of
 * timber bodies at three, four and six miles, headed "for distant LOD / horizon
 * silhouettes", and total extinction anywhere inside three miles erases every
 * one of them. Capping the band's haze keeps them on the horizon at a contrast
 * that never exceeds what the scene's own air allows anything else. It is a
 * compromise between two parcels' instructions, and it is filed as
 * docs/LIBERTIES.md **L35**.
 *
 * **T-1635 MADE THE COMPROMISE SMALLER WITHOUT TOUCHING THE CAP.** The scene's
 * density fell from 0.00125 to 0.00089 — derived from the apron it has to close
 * over rather than from L17's retired "total by 1500 m" — so the air's own law
 * now reaches 0.82 at **1,471 m** instead of 1,048 m. The band therefore follows
 * the real law 423 m further out before this constant takes over, which is 423 m
 * less of the horizon held above what the atmosphere elsewhere permits. 0.82 is
 * unchanged and is deliberately unchanged: it is the figure L35 argues for, the
 * dossier's timber is why, and nothing in T-1635's measurement bears on it.
 *
 * A WARNING ABOUT WHY THIS CONSTANT LOOKS LOAD-BEARING, AND IS NOT.
 *
 * It was briefly recorded — here and in L35 — that this cap had become the only
 * thing keeping the band darker than its own sky, because a fully-hazed surface
 * displayed BRIGHTER than the sky (L 170 against L 162). That measurement was
 * real and its subject was not.
 *
 * The scene's fog does not run where this file assumed. In the vendored r185 the
 * fragment order is `opaque -> tonemapping -> colorspace -> fog`, and the fog
 * colour uniform is uploaded through `getUnlitUniformColorSpace()`. So FogExp2
 * is a straight lerp toward the literal hex IN DISPLAY SPACE, after the tone
 * curve: a fully-fogged pixel is exactly sRGB (136,163,192), L 159.4 — four
 * levels BELOW the horizon sky, which is what airlight is supposed to do.
 *
 * **T-1631: that last clause was true toward the sun and false everywhere
 * else, and this file could not have known it.** L 161.7 is the SOLAR-side
 * horizon sky. `world.js`'s own azimuth-blind sky fit leaves the anti-sun
 * horizon at L 128, so a fog pinned at L 159.4 sat ABOVE the sky it converges
 * on at every bearing — 31 luminance above it due north, which is where the
 * owner was flying when he reported the world looking flooded. The haze is
 * therefore no longer a constant: `world.js` samples its own sky at the
 * horizon and turns the fog with the view. The hex below is still what the
 * band starts at and still what it falls back to, and `update()` is what
 * keeps it on whatever the fog is now — see the `hazeNow` argument.
 *
 * The L 170 came from `hazeDisplayLinear()` below, which USED TO run
 * HORIZON_HAZE through ACES to derive this band's display colour. That was
 * arithmetically correct and answered a question the renderer never asks. The
 * consequence was live and was this file's bug, not the atmosphere's: the band
 * was aimed at (152,175,195) while the ground it stands on converges to
 * (136,163,192), so the far timber sat 16 red and 12 green off the far ground
 * it touches — and because the band is `toneMapped: false, fog: false`, nothing
 * downstream reconciles them. **Fixed 2026-08-13**: the tone curve is gone from
 * that function and both ends now decode the same hex once. The gate compares
 * the band's own hazed end against `scene.fog.color` rather than against a
 * number written down here.
 *
 * So: this cap is about EVIDENCE (holding the dossier's 3-6 mile timber on the
 * horizon), and only about that. Judge it on that argument alone. And do not
 * copy an atmosphere constant into this file and then transform it — the
 * copied values matched world.js exactly the whole time; it was the maths on
 * top of them that drifted, which no drift check on the constants would catch.
 */
const HAZE_MAX = 0.82;
/** Haze fraction for a body at `d` metres. */
function hazeAt(d) {
  const f = HAZE_DENSITY * d;
  return Math.min(HAZE_MAX, 1 - Math.exp(-f * f));
}
/** The colour of a mass of July deciduous canopy before any haze is added. */
const TIMBER_SRGB = 0x39482f;

/** Where the horizon band is drawn. Beyond any ground in the scene (the box's
 *  corner-to-corner diagonal is 905 m) and well inside the 3000 m far plane. */
const RING_RADIUS = 1100;
/** How far below the eye the band's foot reaches, in metres at RING_RADIUS.
 *  Enough to tuck under the water plane and under any far ground, not enough to
 *  occlude a horizon another parcel might extend. */
const RING_FOOT_M = -12;
/** Metres of camera movement that force the band to be re-solved. 0.75 m is
 *  about a sixth of a degree of parallax on the nearest far body — subpixel.
 *  T-0120: this schedules only the EXPENSIVE part — which bearings carry
 *  timber, at what distance and crown height. The eye-HEIGHT term is not
 *  quantised by any threshold: it is finished per frame in the band's vertex
 *  shader (see `uEyeY`), because theta depends on eyeY through one linear
 *  term and baking it in at solve time welded the band to the eye between
 *  solves. */
const RING_REBUILD_M = 0.75;
/**
 * T-1978 — the band's top as a share of the canopy, and how much it may move.
 *
 * Reconstructed, bounded by the owner's report (docs/LIBERTIES.md L367). A
 * treeline seen from a kilometre is the envelope of many crowns at many depths,
 * and the eye reads its MEAN top, level; the old modulation drew it between
 * 40 % and 100 % of the canopy with notches to 5 %, which read as hills.
 * `HORIZON_TOP_K` sits the top at 64 % of the solved canopy — under the old
 * average of 0.70, so filling the notches does not raise the band, and the
 * owner asked for it lower — and
 * `HORIZON_CROWN_AMP` lets the crowns move it ±14 % at the nearest bodies,
 * falling with distance (`farRelief`). `HORIZON_GAP_DEPTH` is how far a gap may
 * cut a near stand: 45 %, never to the ground.
 */
const HORIZON_TOP_K = 0.64;
const HORIZON_CROWN_AMP = 0.14;
const HORIZON_GAP_DEPTH = 0.45;
/**
 * How much of the crown relief survives at `d` metres: all of it at the
 * nearest body (MIN_FAR_M), a quarter by 1.2 km, and no less — a far
 * outline still carries a whisper of texture so it is not ruled with a pen.
 * The canopy's own height range is narrowed by the same factor (`canopyAt`).
 */
function farRelief(d) {
  const f = (d - 330) / (1200 - 330);
  return 1 - 0.75 * Math.min(1, Math.max(0, f));
}
/**
 * The canopy a far body carries at `s` metres along its near edge. The
 * dossier's range is the range of the STAND; how widely the drawn top swings
 * inside it falls with distance as `farRelief` does, around the middle of it,
 * on a ~110 m wavelength so a swing is a stand and never a hill.
 */
function canopyAt(body, bi, s, d) {
  const mid = (body.canopy[0] + body.canopy[1]) * 0.5;
  const half = (body.canopy[1] - body.canopy[0]) * 0.5 * farRelief(d);
  const h = mid + (noise1(s / 110, 3 + bi * 11) - 0.5) * 2 * half;
  // T-1978: an open body steps down over its last crown and a half, so its end
  // is a shoulder of lower crowns and not a sheer cliff — the owner's "big cut
  // down". Short enough (one or two crowns) that it cannot read as a hill.
  // ...and a body coming in toward MIN_FAR_M sinks to nothing well before the
  // cut (T-2103). The band is a far-field device: it draws angle, not depth.
  // T-1978 stepped a body down over its last 60 m, and that was not enough
  // where a body points AT the eye — `main_stem_belt_east` runs along South
  // Water's south side, so looking down the street every sample along it
  // lands in the same few bearings and the bin keeps the nearest, tallest
  // one: a narrow blob at the street end whose height rode the cut as you
  // walked (the owner's "massive moving up and down blobs", 2026-10-04).
  // Faded over NEAR_FADE_M instead, the tallest an end-on body can draw is
  // set by its far reaches, low, and it changes slowly with every step.
  const nearF = Math.min(1, Math.max(0, (d - MIN_FAR_M) / (NEAR_FADE_M - MIN_FAR_M)));
  const hn = h * nearF * nearF * (3 - 2 * nearF);
  const len = FAR_EDGE_LEN[bi];
  if (!len || FAR_EDGE_CLOSED[bi]) return hn;
  const f = Math.min(1, Math.max(0, Math.min(s, len - s) / (body.crown * 1.5)));
  return hn * (0.40 + 0.60 * Math.sqrt(f));
}
/**
 * How near a far body may come before it is dropped from the band. A silhouette
 * on a ring is a FAR-field device: it carries angular size but no depth, and a
 * stand of timber a hundred metres past the edge of the heightfield renders as a
 * smooth black wall ten degrees high and reads as a mountain. On a lake plain
 * that is a worse lie than the gap it leaves.
 */
const MIN_FAR_M = 330;
/** T-2103 — where a far body reaches its full height again; it rises from
 *  nothing at MIN_FAR_M on a smoothstep. See `canopyAt`. */
const NEAR_FADE_M = 800;
/**
 * T-2103 — eye heights between which the band fades out, in metres. The band
 * is a WALKER'S horizon: its foot is a fixed RING_FOOT_M below the eye, which
 * the near ground hides from a standing or riding eye and nothing hides from
 * the air, so from fifteen metres up it stood on the far ground as a dark
 * slab with sheer ends (the owner's "another when flying", 55 ft over La
 * Salle). Above the town the modelled trees carry the view; the band's top
 * sinks onto its foot between these two heights and is gone above the second.
 */
const BAND_FADE_EYE_M = [5, 12];
/**
 * The floor under the crown/gap modulation, in FRAME PIXELS, and the reason the
 * band is solved against the viewport at all.
 *
 * The modulation below breaks the profile up crown by crown and opens sky
 * through the stand — `k` runs down to about 0.02 in a gap. That is texture on
 * a treeline four hundred metres out, where the band is forty pixels tall. On
 * the dossier's three-, four- and six-mile bodies the same multiplier is a
 * DELETION: a 20 m canopy at 9.7 km subtends 1.4 px at desktop, and two per
 * cent of 1.4 px is nothing at all. Measured at the spawn station with this
 * floor removed, the modulation cut **30 of 280 bearings on a phone and 14 of
 * 281 on a desktop** below one pixel, with the worst silhouette drawn at
 * **0.18 px** and **0.31 px** — geometry solved, written into the buffer, and
 * too thin to land on a pixel. That is the mechanism ROADMAP § S6a item 5 names
 * behind the photographic finding that only 31 % of horizon columns carried any
 * timber; the photograph's own measure is not re-run here, and the item says so.
 *
 * So the modulation may take a bearing down to this and no further, whenever
 * the bearing's own unmodulated crown is at least this tall. Below it — a body
 * so far off that its raw silhouette is already sub-pixel — the modulation is
 * suppressed entirely, because a texture that cannot be drawn can only subtract.
 * Where the band IS resolvable (a treeline at 400 m is 40 px) the floor binds
 * on nothing: 0.02 of 40 px is 0.8 px and the gaps stay open.
 *
 * 1.0 px rather than 2: at 1 px the silhouette is continuous and still thin
 * enough that no crown reads as a ridge, which is the failure the modulation
 * exists to prevent. The gate measures both directions — see
 * `horizonContinuity()`.
 */
const MIN_SILHOUETTE_PX = 1.0;
/**
 * Pixels per radian of vertical field, used when nothing supplies the live
 * viewport. 800 rows over a 55° vertical field — the desktop release viewport
 * at its narrowest clamp, so an unwired caller gets the conservative answer
 * rather than a generous one.
 */
const DEFAULT_PX_PER_RAD = 800 / (55 * Math.PI / 180);

/* -------------------------------------------------------------------------- */
/* the species                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * One entry per woody species drawn. `h` is the JULY height in metres and `dbh`
 * the diameter at breast height, both straight out of the dossier's tables;
 * `dossier` names the section the row came from. The two greens are a shaded
 * and a sunlit July foliage colour — render tuning, not evidence, and the pair
 * the palette record will own once `data/flora/palettes/` is populated. `bark`
 * is the bole, and the optional `barkUpper` the upper bole and limbs where a
 * species is drawn in two tones; both are invented, as every colour here is,
 * and a species that omits `barkUpper` is drawn in one tone as before.
 *
 * form: gallery = tall crowded floodplain tree · open = open-grown, short bole
 * and heavy horizontal limbs · lean = bank willow leaning over the water ·
 * sub = subcanopy · thicket = clonal woody screen, no bole.
 */
const SPECIES = {
  // ---- ZONE 5, riverbank and floodplain timber --------------------------- //
  populus_deltoides: { common: 'eastern cottonwood', dossier: 'ZONE 5',
    form: 'gallery', h: [22, 30], dbh: [0.60, 1.00], spreadK: 0.56, boleK: 0.46, puffs: 7,
    dark: 0x3d5a2c, light: 0x86a252, bark: 0x6e6759,
  },
  salix_nigra: { common: 'black willow', dossier: 'ZONE 5',
    form: 'lean', h: [10, 16], dbh: [0.25, 0.55], spreadK: 0.74, boleK: 0.34, puffs: 5,
    dark: 0x44643a, light: 0x87a35c, bark: 0x38332a, lean: 0.30, water: true,
  },
  salix_amygdaloides: { common: 'peachleaf willow', dossier: 'ZONE 5',
    form: 'lean', h: [8, 14], dbh: [0.20, 0.45], spreadK: 0.70, boleK: 0.36, puffs: 5,
    dark: 0x53703f, light: 0x97ab63, bark: 0x4c4433, lean: 0.24, water: true,
  },
  acer_saccharinum: { common: 'silver maple', dossier: 'ZONE 5',
    form: 'gallery', h: [20, 28], dbh: [0.50, 0.90], spreadK: 0.62, boleK: 0.40, puffs: 7,
    dark: 0x425c32, light: 0x93a077, bark: 0x585144,
  },
  ulmus_americana: { common: 'American elm', dossier: 'ZONE 5',
    form: 'gallery', h: [18, 26], dbh: [0.35, 0.75], spreadK: 0.66, boleK: 0.46, puffs: 7,
    dark: 0x34502b, light: 0x6f8b46, bark: 0x4e4638,
  },
  fraxinus_pennsylvanica: { common: 'green ash', dossier: 'ZONE 5',
    form: 'gallery', h: [15, 22], dbh: [0.25, 0.55], spreadK: 0.54, boleK: 0.44, puffs: 6,
    dark: 0x3c5a2f, light: 0x76914b, bark: 0x4a4335,
  },
  quercus_bicolor: { common: 'swamp white oak', dossier: 'ZONE 5',
    form: 'open', h: [15, 20], dbh: [0.35, 0.70], spreadK: 0.92, boleK: 0.34, puffs: 9,
    dark: 0x2f4a27, light: 0x81916b, bark: 0x453d31,
  },
  celtis_occidentalis: { common: 'hackberry', dossier: 'ZONE 5',
    form: 'gallery', h: [12, 18], dbh: [0.20, 0.45], spreadK: 0.60, boleK: 0.42, puffs: 6,
    dark: 0x455f39, light: 0x7f954f, bark: 0x51493a,
  },
  juglans_nigra: { common: 'black walnut', dossier: 'ZONE 5',
    form: 'gallery', h: [18, 25], dbh: [0.35, 0.65], spreadK: 0.58, boleK: 0.48, puffs: 6,
    dark: 0x39552f, light: 0x718a49, bark: 0x3f382d,
  },
  // The one species carrying a second bark tone, and the only one whose record
  // says anything about its bark at all: "white mottled bark flashing on the
  // upper limbs" (`z05_riverbank_timber`). Both hexes are invented — no record
  // in `data/flora/` carries a colour — and bounded by this file's own barks:
  // the lower bole is the palest of the eighteen and the limbs are far paler
  // than any of them, because being the palest thing in the timber is the whole
  // of what that sentence describes. The MOTTLING is not drawn: the break is
  // between bole and limb, not a patchwork within either. docs/LIBERTIES.md
  // L118, ROADMAP K47. `dbh` sits at the top of this file's own height:diameter
  // ratios (0.035 against the gallery's 0.023–0.031) — the stoutest bole on the
  // bank, which is what a sycamore is; `boleK` forks it lower than the elm.
  platanus_occidentalis: { common: 'American sycamore', dossier: 'ZONE 5',
    form: 'gallery', h: [18, 25], dbh: [0.55, 0.95], spreadK: 0.62, boleK: 0.38, puffs: 6,
    dark: 0x60783e, light: 0x9bb06c, bark: 0x7a7263, barkUpper: 0xd9d3c2,
  },
  salix_interior: { common: 'sandbar willow', dossier: 'ZONE 5',
    form: 'thicket', h: [2.2, 4.0], dbh: [0.04, 0.08], spreadK: 1.30, boleK: 0, puffs: 4,
    dark: 0x63805a, light: 0xa4b487, bark: 0x4f4c3c,
  },

  // ---- ZONE 6a, the swampy timber thicket -------------------------------- //
  fraxinus_nigra: { common: 'black ash', dossier: 'ZONE 6a',
    form: 'gallery', h: [14, 20], dbh: [0.22, 0.45], spreadK: 0.48, boleK: 0.52, puffs: 5,
    dark: 0x35512c, light: 0x6b8743, bark: 0x474034,
  },

  // ---- ZONE 6b, the fire-protected mesic pocket -------------------------- //
  tilia_americana: { common: 'basswood', dossier: 'ZONE 6b',
    form: 'gallery', h: [18, 24], dbh: [0.35, 0.70], spreadK: 0.58, boleK: 0.46, puffs: 6,
    dark: 0x3d5c2e, light: 0x81994c, bark: 0x4d4638,
  },
  acer_saccharum: { common: 'sugar maple', dossier: 'ZONE 6b',
    form: 'gallery', h: [18, 24], dbh: [0.30, 0.65], spreadK: 0.56, boleK: 0.44, puffs: 7,
    dark: 0x2d4b26, light: 0x6a8940, bark: 0x4b4436,
  },
  quercus_rubra: { common: 'red oak', dossier: 'ZONE 6b',
    form: 'gallery', h: [20, 26], dbh: [0.40, 0.80], spreadK: 0.66, boleK: 0.44, puffs: 7,
    dark: 0x35502b, light: 0x728e45, bark: 0x494134,
  },
  ostrya_virginiana: { common: 'ironwood', dossier: 'ZONE 6b',
    form: 'sub', h: [6, 10], dbh: [0.12, 0.25], spreadK: 0.62, boleK: 0.42, puffs: 4,
    dark: 0x3e5a33, light: 0x789249, bark: 0x5a5142,
  },

  // ---- ZONE 6c / ZONE 7, the sand-ridge oaks ----------------------------- //
  quercus_macrocarpa: { common: 'bur oak', dossier: 'ZONE 6c / ZONE 7',
    form: 'open', h: [14, 19], dbh: [0.45, 0.95], spreadK: 1.18, boleK: 0.30, puffs: 10,
    dark: 0x334f29, light: 0x748d45, bark: 0x3a332a, fireScar: true,
  },
  quercus_alba: { common: 'white oak', dossier: 'ZONE 6c / ZONE 7',
    form: 'open', h: [16, 22], dbh: [0.40, 0.85], spreadK: 1.02, boleK: 0.34, puffs: 9,
    dark: 0x3a5730, light: 0x7c9349, bark: 0x6a6355, fireScar: true,
  },
  quercus_velutina: { common: 'black oak', dossier: 'ZONE 6c',
    form: 'open', h: [14, 20], dbh: [0.30, 0.65], spreadK: 0.92, boleK: 0.36, puffs: 8,
    dark: 0x2d4625, light: 0x67813e, bark: 0x332e26, fireScar: true,
  },
  carya_ovata: { common: 'shagbark hickory', dossier: 'ZONE 6c',
    form: 'gallery', h: [15, 20], dbh: [0.25, 0.50], spreadK: 0.50, boleK: 0.52, puffs: 5,
    dark: 0x405c2d, light: 0x7d974b, bark: 0x655c48,
  },
};

/**
 * THE ARCHETYPE TABLE IS KEYED BY SPECIES, AND A SPECIES CAN BE RECORDED TWICE.
 *
 * ROADMAP K45(b) change one, and it is the finding this parcel did not expect.
 * `SPECIES` above says "one entry per woody species drawn", and until the
 * lakeshore was routed here that was true. `populus_deltoides` is recorded in
 * BOTH `z05_riverbank_timber` — `tree_gallery`, 22–30 m, 14–22 m crown, the
 * emergent of the floodplain — AND `z08_lakeshore` — `tree_leaning`, 5–15 m,
 * 6–14 m crown, *"isolated, half-buried and leaning, with a sand mound at the
 * base"*. They are the same binomial and nothing else about them is the same.
 *
 * `loadTimberZones` keys its spec map by species id and takes the FIRST zone
 * that names one, so with nothing here the dune would have been planted with
 * twenty-five-metre gallery cottonwoods standing on the open beach — the record
 * read, routed, banded, and drawn as another zone's tree. That is K47's fault
 * one level in, and the reason it is caught here is that the dune is the first
 * community whose cited zone re-describes a species another zone already had.
 *
 * So the archetype — what the record does NOT carry: bole diameter, fork
 * height, foliage-mass count, lean, bark colour — may be given per zone. The
 * record still wins on everything it states. Only the lakeshore needs an entry
 * today; the general repair (a spec map keyed by zone AND species for every
 * community) would redeal the whole town's specs and is its own parcel.
 *
 * **Every number below is invented, as every number in `SPECIES` is**, bounded
 * by this file's own range and by the record's prose. docs/LIBERTIES.md L119.
 */
const ARCHETYPE_BY_ZONE = {
  z08_lakeshore: {
    // The dune pioneer. Stout for its height and forking low, because it is
    // half-buried: `boleK` 0.30 is the lowest fork in this file after the open-
    // grown oaks. `lean` 0.30 is the TOP of the range the file already uses
    // (the two bank willows sit at 0.24 and 0.30) — the record's one visual
    // claim about this tree is that it leans, so it takes the most this file
    // has ever leant anything. Bark is the gallery cottonwood's own: same
    // species, and no record anywhere states a bark colour.
    populus_deltoides: { common: 'eastern cottonwood (dune form)', dossier: 'ZONE 8c',
      form: 'lean', h: [5, 15], dbh: [0.30, 0.70], spreadK: 0.70, boleK: 0.30, puffs: 6,
      dark: 0x3d5a2c, light: 0x86a252, bark: 0x6e6759, lean: 0.30,
    },
    // Quaking aspen: a narrow clonal stem, and the one tree here whose bark a
    // visitor could name from thirty metres. 0xb9bdae is the palest BOLE in the
    // scene by design and is still darker than the sycamore's upper limbs
    // (0xd9d3c2, L118), which stay the palest wood in the timber.
    populus_tremuloides: { common: 'quaking aspen', dossier: 'ZONE 8c',
      form: 'columnar', h: [6, 12], dbh: [0.10, 0.25], spreadK: 0.42, boleK: 0.56, puffs: 5,
      dark: 0x6e864e, light: 0x98a876, bark: 0xb9bdae,
    },
    // Balsam poplar: the same narrow crown in the damper hollows, on ordinary
    // grey-brown wood — deliberately NOT the aspen's pale bole, because the two
    // stand side by side at the same height and the bark is what separates them.
    populus_balsamifera: { common: 'balsam poplar', dossier: 'ZONE 8c',
      form: 'columnar', h: [6, 12], dbh: [0.12, 0.28], spreadK: 0.42, boleK: 0.54, puffs: 5,
      dark: 0x58743e, light: 0x8a9c66, bark: 0x5d5748,
    },
    // T-2768 — THE SAND HILLS' CEDAR AND PINE. Shape is tree-model.js's ARCH;
    // these carry what the old archetype path still reads. The cedar's bark is
    // the reddish brown of its shredding strips, the pine's a dark grey-brown;
    // no record states either. `dbh` is stout for the height, as a wind-cut
    // tree on sand is. docs/LIBERTIES.md L-sand-hills-2768.
    juniperus_virginiana: { common: 'eastern red cedar (dune form)', dossier: 'ZONE 8c',
      form: 'columnar', h: [1.5, 6], dbh: [0.08, 0.26], spreadK: 0.55, boleK: 0.04, puffs: 6,
      dark: 0x3a5238, light: 0x5c7254, bark: 0x7a5c48,
    },
    pinus_banksiana: { common: 'jack pine', dossier: 'ZONE 8c',
      form: 'open', h: [3, 9], dbh: [0.12, 0.30], spreadK: 0.62, boleK: 0.28, puffs: 6,
      dark: 0x4a6236, light: 0x7a8e56, bark: 0x4c4238,
    },
  },
  z10_settled_town: {
    // THE LOMBARDY POPLAR (T-0117), and it is here rather than in `SPECIES` for
    // the reason this table exists: no community mix may ever select it. It is
    // a European cultivar that reaches this town as nursery stock, its zone
    // record carries a density of ZERO per hectare to say so, and every stem of
    // it in the scene is stated by `data/flora/plantings/town_planted_rows.json`.
    // Held per zone, it is reachable by the planting pass — which reads
    // `byZone[rec.zone]` — and by nothing else.
    //
    // `boleK` 0.12 is the LOWEST clear bole in this file and it is the species'
    // signature: an 'Italica' is foliated nearly to the ground, which is what
    // every committed plate of the Kinzie row draws — the spires stand in the
    // fence line as columns of leaf, not as trunks under crowns. `dbh` is a
    // slender stem for the height, because the tree runs to a single leader.
    // The bark is the grey-brown of the balsam poplar above rather than the
    // aspen's pale bole: no record states one, and this is not the tree a
    // visitor could name from its wood.
    //
    // `puffs` 14 is the highest count in this file and it is a consequence of
    // the record rather than a preference: the crown is 1.4-2.4 m on a 12-18 m
    // stem, so the columnar ladder below has about 14 m of leader to fill and
    // the masses have to be close enough together to touch. Ten was shot first
    // and the notches between the rungs were visible from thirty metres. The
    // cost is 412 triangles a tree — a five-sided bole in two segments, then a
    // limb and an icosahedral mass per rung.
    //
    // Every number here is invented, as every number in `SPECIES` is; the
    // record still wins on height, crown and foliage. docs/LIBERTIES.md L119.
    populus_nigra_italica: { common: 'Lombardy poplar', dossier: 'ZONE 10',
      form: 'columnar', h: [12, 18], dbh: [0.24, 0.42], spreadK: 0.14, boleK: 0.12, puffs: 14,
      dark: 0x426036, light: 0x7a9260, bark: 0x5f5849,
    },
    // T-2809 — THE YOUNG FRUIT TREES of the fort's company gardens and Dr.
    // Harmon's orchard. Here for the poplar's reason: each is recorded at a
    // density of zero, so no community deals one and the planting records are
    // the only way in. Shape is tree-model.js's ARCH; these carry what the old
    // path still reads. `dbh` is young nursery stock, a few centimetres; the
    // barks are invented (apple grey-brown and scaly, cherry red-brown, peach
    // dark). docs/LIBERTIES.md L-fruit-trees-1835-2809.
    malus_domestica: { common: 'apple (young, planted)', dossier: 'ZONE 10',
      form: 'open', h: [2.5, 6], dbh: [0.07, 0.16], spreadK: 0.95, boleK: 0.30, puffs: 5,
      dark: 0x3e5a2e, light: 0x7f9757, bark: 0x5e564a,
    },
    prunus_cerasus: { common: 'sour cherry (young, planted)', dossier: 'ZONE 10',
      form: 'open', h: [2, 5.5], dbh: [0.05, 0.13], spreadK: 0.80, boleK: 0.32, puffs: 5,
      dark: 0x355229, light: 0x76914a, bark: 0x5a3f36,
    },
    prunus_persica: { common: 'peach (seedling, planted)', dossier: 'ZONE 10',
      form: 'open', h: [2, 4.5], dbh: [0.05, 0.12], spreadK: 0.90, boleK: 0.24, puffs: 5,
      dark: 0x4a6b33, light: 0x8ba75a, bark: 0x4f3c34,
    },
  },
};

/**
 * The communities, and what fraction of the canopy each species holds in them.
 * Weights are the dossier's per-species densities; `perHa` is the STAND density
 * the dossier gives for the community as a whole, which is the number that
 * governs — the per-species figures are microsite densities and sum higher.
 *
 * THE WEIGHT WRITTEN HERE IS THE WEIGHT THAT PLANTS THE STEM (ROADMAP K46).
 * It was not, until 2026-08-16: `mixes` was rebuilt as
 * `records.density[id] ?? fallback`, so one global midpoint per species — taken
 * from whichever `TIMBER_ZONES` entry happened to name it first — overwrote
 * every per-community weight below, and seventeen of the twenty-six entries ran
 * at a number other than the one they are written to.
 *
 * K46 chose the literal, and the reason is a fact about the DATASET rather than
 * a preference. The alternative — key the density by (zone, species) and let
 * each community read the band from the zone its own `dossier` cites — cannot
 * express what this table says, because `wet_woods` cites ZONE 6a and
 * `mesic_pocket` cites ZONE 6b and BOTH resolve to the single record
 * `z06_dense_forest`. A zone-keyed density gives the elm 60 in both, and the
 * 12 that makes it incidental in the fire-protected pocket has nowhere to live.
 * The sub-community reading is real and is recorded nowhere else in this
 * project, so the file keeps it.
 *
 * The record is not discarded; it becomes the CONSTRAINT. Every weight below is
 * checked at load against the band of each zone its community's `zones` names,
 * and one that falls outside every such band is a claim no record carries: it
 * must be declared in that community's `departures`, with the reason, or the
 * load raises. Measured across the twenty-six entries: 23 sit inside their own
 * cited band, 3 fall below one, and none is above — so the hand weights were
 * never an inflation, and the three that depart are the three the prose already
 * explains. `perHa` is the STAND density the dossier gives for the community as
 * a whole, which is the number that governs — the per-species figures are
 * microsite densities and sum higher.
 *
 * `zones` is the machine-readable form of the `dossier` line and is held equal
 * to it by `tools/measure_planting_reach.py`, so the citation a reader sees and
 * the bands the loader checks against cannot drift apart.
 */
const COMMUNITIES = {
  gallery: {
    label: 'Riverbank & floodplain timber',
    dossier: 'ZONE 5 — “irregular gallery 30–120 m wide, canopy 30–80 trees/ha”',
    zones: ['z05_riverbank_timber'],
    perHa: [34, 62],
    mix: [
      ['populus_deltoides', 14], ['acer_saccharinum', 25], ['ulmus_americana', 25],
      ['fraxinus_pennsylvanica', 22], ['quercus_bicolor', 10], ['celtis_occidentalis', 8],
      ['juglans_nigra', 2], ['salix_amygdaloides', 8],
      // ROADMAP K45(b1). The American sycamore, at the midpoint of the [1, 3]
      // its own z05 record carries. K45(b) prescribed a 1: the bottom of the
      // band, and — under K46's rule, which plants the literal — a figure that
      // would now have halved the handful of sycamores actually standing.
      ['platanus_occidentalis', 2],
    ],
    /** At the water's edge the mix goes to willow, per the ZONE 5 densities. */
    edgeMix: [['salix_nigra', 42], ['salix_amygdaloides', 17], ['acer_saccharinum', 8]],
    /**
     * Weights that sit outside every band this community's `zones` record, and
     * why. A departure is an ecological claim of this file's own — see
     * docs/LIBERTIES.md L117 — so it is written down or the load raises.
     */
    departures: {
      'mix.salix_amygdaloides':
        'ZONE 5 bands the peachleaf willow at 10–25/ha across the whole gallery. This '
        + 'file splits that one band between its two lists — 17 at the water’s edge, '
        + 'inside the band, and 8 behind it — because the record describes a bank tree '
        + 'and the gallery is 30–120 m wide. The split is this file’s; the two lists '
        + 'together stand for the one recorded band.',
      'edgeMix.acer_saccharinum':
        'The edge mix exists to say what its own note says — at the water’s edge the mix '
        + 'goes to willow — and ZONE 5 bands the silver maple for the gallery as a whole '
        + '(15–35/ha) without banding the edge separately. Cutting it to 8 is how that '
        + 'sentence is expressed as a weight; the number is this file’s.',
    },
    confidence: 'inferred',
    sources: ['chicagology_prefire273'],
  },
  wet_woods: {
    label: 'Swampy timber thicket (the 1821 Walls note)',
    dossier: 'ZONE 6a — canopy 50–110/ha over the poorly drained clay',
    zones: ['z06_dense_forest'],
    perHa: [52, 84],
    mix: [
      ['ulmus_americana', 60], ['fraxinus_pennsylvanica', 32], ['fraxinus_nigra', 14],
      ['acer_saccharinum', 30], ['quercus_bicolor', 17],
    ],
    confidence: 'inferred',
    sources: ['chicagology_prefire273'],
  },
  mesic_pocket: {
    label: 'Fire-protected mesic pocket',
    dossier: 'ZONE 6b — east-of-water positions, the one place canopy closes',
    zones: ['z06_dense_forest'],
    perHa: [64, 96],
    mix: [
      ['tilia_americana', 25], ['acer_saccharum', 20], ['quercus_rubra', 14],
      ['ostrya_virginiana', 27], ['ulmus_americana', 12],
    ],
    departures: {
      'mix.ulmus_americana':
        'ZONE 6a, 6b and 6c share one record — `z06_dense_forest` — and its elm band, '
        + '40–80/ha, is the swamp thicket’s reading: the elm dominates the poorly drained '
        + 'clay. In the fire-protected pocket the closing canopy is basswood, sugar maple '
        + 'and ironwood and the elm is incidental to it, which is what 12 says. No record '
        + 'bands ZONE 6b apart from ZONE 6a, so this number is this file’s and is the '
        + 'reason K46 kept the hand weights at all.',
    },
    confidence: 'inferred',
    sources: ['chicagology_prefire273'],
  },
  ridge_oak: {
    label: 'Sand- and gravel-ridge oak stringers / bur oak savanna',
    dossier: 'ZONE 6c + ZONE 7 — 4–20/ha closed savanna, locally 1–4/ha open',
    // The dossier merges two zones and K45(b1) left "which band does it mean?"
    // as an open question. Under K46's rule it does not need answering: the
    // record is a constraint, not a source, and all four weights here sit
    // inside a band one of the two cited zones records.
    zones: ['z06_dense_forest', 'z07_bur_oak_savanna'],
    perHa: [7, 24],
    mix: [
      ['quercus_macrocarpa', 30], ['quercus_alba', 24], ['quercus_velutina', 12],
      ['carya_ovata', 8],
    ],
    confidence: 'inferred',
    sources: ['chicagology_prefire273'],
  },
  /**
   * THE OPEN DUNE — ROADMAP K45(b) change one, and the first community here
   * whose `perHa` is DERIVED rather than quoted.
   *
   * ZONE 8 gives no canopy figure, because a dune has no canopy. What it gives
   * is three absolute per-hectare densities on three isolated trees — the dune
   * cottonwood at 3–15/ha *"isolated, half-buried, leaning"*, the quaking aspen
   * and the balsam poplar at 2–8/ha each in *"clonal patches"* — and on open
   * sand those are not microsite densities competing for one canopy. They add.
   * So the stand is their sum, [7, 31]/ha, and the mix takes each species'
   * midpoint under K45(b1)'s rule: at the middle of the band the draw plants
   * 9 + 5 + 5 per hectare, which is each record's own midpoint reproduced
   * exactly. That is the test this arithmetic has to pass and the reason it is
   * written this way rather than normalised to a hundred.
   */
  dune: {
    label: 'Open-dune poplars on the lakeshore sand',
    dossier: 'ZONE 8c — stabilised back-dune, isolated trees over marram and sand cherry',
    zones: ['z08_lakeshore'],
    perHa: [7, 31],
    mix: [
      ['populus_deltoides', 9], ['populus_tremuloides', 5], ['populus_balsamifera', 5],
    ],
    /**
     * The dune's own species keep the dune's parameters. Without this the
     * cottonwood on the beach is drawn with `z05_riverbank_timber`'s archetype,
     * because the spec map is keyed by species id and the gallery is read
     * first — see ARCHETYPE_BY_ZONE.
     */
    specsFrom: 'z08_lakeshore',
    confidence: 'inferred',
    sources: ['mnfi_open_dunes', 'cowles_1901'],
  },
  /**
   * T-2768 — THE SAND HILLS, where the witnesses put a woody scrub on the same
   * ZONE 8 ground the dune poplars stand on, beyond the poplars' reach.
   *
   * Three reaches, each its own community because each witness describes a
   * different cover, and each held to its `reachN` (local N metres, faded over
   * `reachFadeM`):
   *
   *   north  Wau-Bun (1856): between the Kinzie house and the lake, "a vast
   *          range of sand-hills, covered with stunted cedars, pines, and
   *          dwarf-willow trees". From the house's northing to the field's edge.
   *   south  Clarke (1890): from about Twelfth to Twenty-Fifth Street, "covered
   *          with low cedar trees, ground pine, and sand cherry bushes". No pine
   *          tree: his "ground pine" is a mat, and the sand cherry and the dune
   *          willows are flora.js's shrub stratum on this zone already.
   *   scanty Currey (1912): south of the mouth to about Twelfth Street, "a
   *          scanty growth of cottonwoods and pines ... maintaining a precarious
   *          existence among the sand-dunes".
   *
   * WHERE NO WITNESS GOES: the positions, the density each word is read as, and
   * where one reach gives way to the next (Twelfth Street, by the 16th-22nd
   * Street anchors). docs/LIBERTIES.md L-sand-hills-2768.
   *
   * PLANTED IN CLUMPS. A dune scrub is thickets with sand between them, not an
   * even scatter, so the roll is weighted by a clump field (`clumpM`) with a
   * mean of one: the count is the record's, the pattern is clumped.
   *
   * THE SWALES. Where the modelled sand hills have a hollow (the dune fields'
   * `hollow` in terrain_spec.json), the ground stands lower than its
   * surroundings, and Cowles (1901, p. 153): "Seedlings of the Cottonwood, as
   * well as the long-leaved and glaucous willows, germinate in these wet
   * depressions." A hollow takes `swaleMix` instead: no cedar, which wants the
   * dry crest.
   *
   * These communities deal from their own position-seeded generator, not the
   * shared stream, so the rest of the wood stands exactly where it stood.
   */
  sand_hills_north: {
    label: 'Sand-hill cedar, pine and willow scrub north of the river (Wau-Bun)',
    dossier: 'ZONE 8c — stabilised back-dune; Wau-Bun 1856',
    zones: ['z08_lakeshore'],
    perHa: [40, 64],
    mix: [['juniperus_virginiana', 44], ['pinus_banksiana', 10], ['populus_deltoides', 6]],
    swaleMix: [['populus_deltoides', 9], ['populus_balsamifera', 5]],
    reachN: [330, 1200], reachFadeM: 60, clumpM: 24,
    // "Between the house and the lake": the sand hills run inland of the
    // lakeshore zone's band to the Kinzie house, so here the reach also takes
    // the sand prairie east of it (`inlandFromE`, just east of the house's two
    // cottonwoods at E 1146-1162).
    inlandFromE: 1175, inlandBeltM: 200,
    specsFrom: 'z08_lakeshore',
    confidence: 'inferred',
    sources: ['kinzie_waubun_1856', 'cowles_1901'],
  },
  sand_hills_south: {
    label: 'Sand-hill red cedar south of Twelfth Street (Clarke)',
    dossier: 'ZONE 8c — stabilised back-dune; Clarke 1890',
    zones: ['z08_lakeshore'],
    perHa: [40, 64],
    mix: [['juniperus_virginiana', 52]],
    swaleMix: [['populus_deltoides', 9], ['populus_balsamifera', 5]],
    reachN: [-4000, -2410], reachFadeM: 120, clumpM: 26,
    // Clarke gives the sand hills' length and not their depth; a belt of
    // 140 m behind the shore is the lakeshore band and as much again.
    inlandBeltM: 140,
    specsFrom: 'z08_lakeshore',
    confidence: 'inferred',
    sources: ['kirkland_1893_chicago_massacre_appendix_k', 'cowles_1901'],
  },
  sand_hills_scanty: {
    label: 'Scanty cottonwoods and pines on the dunes south of the mouth (Currey)',
    dossier: 'ZONE 8c — stabilised back-dune; Currey 1912',
    zones: ['z08_lakeshore'],
    perHa: [3, 9],
    mix: [['pinus_banksiana', 3], ['populus_deltoides', 3]],
    swaleMix: [['populus_deltoides', 9], ['populus_balsamifera', 5]],
    reachN: [-2410, -400], reachFadeM: 0, clumpM: 30,
    specsFrom: 'z08_lakeshore',
    confidence: 'inferred',
    sources: ['currey_1912_story_of_old_fort_dearborn', 'cowles_1901'],
  },
};
/** T-2768 — the sand-hill communities, in the order a point is offered to them. */
const SAND_HILLS = ['sand_hills_north', 'sand_hills_south', 'sand_hills_scanty'];

/**
 * T-2807 — THE WOOD IN CLUMPS. Dealt at one density per community, the wood read
 * from the air as an orchard: an even scatter of the same-sized trees. A wood on
 * the lake plain is a mosaic of patches: dense where the canopy closed, small
 * openings where a tree fell or a fire got in, and younger trees coming up in
 * those openings. So each woods community's density is multiplied by a clump
 * field with a mean of one: `floor` in an opening, `2 - floor` in a patch, on
 * value noise of `cellM` metres. The count each community plants is the
 * record's; only where its stems stand is changed. A stem in an opening is
 * grown smaller (`young`, the scale at the opening's heart).
 *
 * Every number here is invented: the records give a stand density and the
 * dossier says "mosaic", and nothing gives a patch size. docs/LIBERTIES.md
 * L-woods-structure-2807.
 */
const WOOD_CLUMP = {
  gallery: { cellM: 34, floor: 0.20, young: 0.62 },
  wet_woods: { cellM: 30, floor: 0.15, young: 0.58 },
  mesic_pocket: { cellM: 40, floor: 0.30, young: 0.66 },
  ridge_oak: { cellM: 48, floor: 0.10, young: 0.60 },
};

/**
 * T-2807 — THE THICKET AT THE WOODS' PRAIRIE EDGE. Where a wood meets the
 * prairie the fires that run before the west wind stop, and the shrubs that
 * resprout after them crowd the edge: the survey notes for these woodlands give
 * hazel as the commonest undergrowth and "thorn" as a term (McBride and Bowles
 * 2007, in `z06_dense_forest`), with wild plum, and gray dogwood on the river
 * woods' margins (`z05_riverbank_timber`). Two edges face open prairie in the
 * scene:
 *
 *   - the river woods' outer reach in the South and West Divisions, where the
 *     gallery thins into "a free and boundless prospect of open prairie"
 *     (`galleryBand`: the outer part of the gallery's width, as a fraction);
 *   - the North Side wood's east end, against the sand prairie at the State
 *     Street break of slope (`eastBandM` metres inside the east limit).
 *
 * In the oak ridges (the savanna) the same hazel stands scattered through the
 * grass at `savannaPerHa`.
 *
 * The shrubs are the zone records' own (`shrub_low`: height, width, July
 * colour) drawn as grown, instanced clumps of stems (tree-model.js ARCH), so a
 * thicket reads at the distance a tree does and costs a tree's few cards past
 * the near ring. They deal from their own position-seeded generator, like the
 * sand hills. The weights follow the records' cover fractions, with hawthorn,
 * plum and dogwood raised against hazel because the edge is where they stand;
 * the band widths and densities are this file's. docs/LIBERTIES.md
 * L-woods-structure-2807.
 */
const EDGE_THICKET = {
  label: "Hazel, plum, hawthorn and dogwood thicket at the woods' prairie edge",
  perHa: [320, 520], clumpM: 14, galleryBand: [0.66, 0.90], eastBandM: [12, 34],
  mix: [['corylus_americana', 35], ['crataegus_spp', 9], ['prunus_americana', 7], ['cornus_racemosa', 8]],
  savannaPerHa: [5, 12],
  savannaMix: [['corylus_americana', 30], ['crataegus_spp', 4], ['prunus_americana', 2]],
  zones: { corylus_americana: 'z06_dense_forest', crataegus_spp: 'z06_dense_forest',
    prunus_americana: 'z06_dense_forest', cornus_racemosa: 'z05_riverbank_timber' },
  // The records carry no bark; this file's, as every bark in SPECIES is. Hazel
  // and dogwood smooth grey-brown stems, plum dark, hawthorn grey and scaly.
  bark: { corylus_americana: 0x76675a, crataegus_spp: 0x6f6a60,
    prunus_americana: 0x4e4038, cornus_racemosa: 0x7c7870 },
  confidence: 'inferred',
  sources: ['mcbride_bowles_2007', 'swink_wilhelm_1994'],
};

/**
 * T-2810 — THE RIVER WOODS' DEAD WOOD: STANDING SNAGS AND FALLEN LOGS.
 *
 * A floodplain wood is full of dead wood: elms and ashes killed by standing
 * water, cottonwoods and willows broken by ice and wind, and the trunks they
 * drop lying where they fell, since nobody yet hauled them out. No witness of
 * 1812 or 1835 describes the dead wood on this river, so the shares here are
 * this file's, kept modest (the ecology analysis in the trees report grades
 * the dead wood "near-certain ecologically but no 1830s witness mentions it").
 * `snag` is the share of the canopy stems a community deals that stand dead
 * instead; `log` the chance a stem has a fallen trunk lying near it. The wet
 * woods take more of both: it is the swampy, waterlogged wood (the 1821 Walls
 * note) where trees drown. Both deal from their own position-seeded generator,
 * so no living stem moves, and both thin with the detail level as the stems
 * they ride on do. docs/LIBERTIES.md L-deadwood-vines-2810.
 */
const DEAD_WOOD = {
  shares: { gallery: { snag: 0.05, log: 0.06 }, wet_woods: { snag: 0.07, log: 0.08 } },
  // Weathered: the bark goes grey and silver as it dries and sloughs.
  bark: { snag: 0x8a8378, log: 0x6f675d },
  // A log lies within this many metres of the stem it rides on, in any direction.
  logOffsetM: [2, 7],
  // A log is drawn small at the levels a log is a few pixels at: it is
  // treated as standing this many times further off (tree-instances `lodK`).
  logLodK: 2.5,
  confidence: 'reconstructed',
  sources: [],
};

/**
 * T-2810 — WILD GRAPE CURTAINS AND VIRGINIA CREEPER ON THE RIVER-FACING EDGE.
 *
 * ZONE 5 records both vines (z05_riverbank_timber): the riverbank grape as a
 * "heavy curtain vine on the river-facing edge trees" that "drapes 10-20% of
 * the edge trees", and the Virginia creeper's "five-fingered leaves climbing
 * the trunks on the shaded side". So a gallery tree standing within `edgeM` of
 * the water carries a grape curtain on `grape` of the time, hung over its crown
 * edge on the water side, or failing that a creeper on `creeper` of the time,
 * up the north (shaded) side of its trunk. 0.15 is the middle of the record's
 * 10-20 %; the creeper's share, the edge's depth and the curtain's shape are
 * this file's (L-deadwood-vines-2810). Position-seeded, like DEAD_WOOD.
 */
const VINE_EDGE = {
  edgeM: 32,
  grape: 0.15,
  creeper: 0.08,
  // How far up the host the vine reaches, of the host's height.
  reach: { vitis_riparia: [0.78, 0.95], parthenocissus_quinquefolia: [0.45, 0.70] },
  habit: { vitis_riparia: 'curtain', parthenocissus_quinquefolia: 'trunk' },
  // The leaf atlas family: the grape's broad lobed heart, the creeper's five leaflets.
  leaf: { vitis_riparia: 'heart', parthenocissus_quinquefolia: 'compound' },
  zone: 'z05_riverbank_timber',
  confidence: 'inferred',
  sources: ['swink_wilhelm_1994'],
};

/**
 * T-2784 — THE WOODY PLANTS OF THE OPEN PLAIN, 1812 AND 1835.
 *
 * The prairie west and south of the river is treeless, and rightly so: fires
 * ran over it every year or two before the west and south-west wind. It was
 * not bare of woody plants. The trees report's ecology analysis (sections 2.4
 * and 2.5) reads three things on it, and this draws all three wherever
 * `communityAt` plants no wood, the water and the dry floor allow, and the
 * sward's zone is prairie, sedge meadow or marsh (`grounds`):
 *
 *   dry    the fire-tolerant shrubs scattered through the grass: wild rose
 *          everywhere, New Jersey tea and leadplant on the drier ground, each
 *          resprouting from its root after a burn. Thinned on wet ground
 *          (`wetCut`) and dealt on a mean-one clump field, so they come in
 *          little colonies with open grass between.
 *   wet    the slough edge: pussy and slender willow in clumps, meadowsweet in
 *          the wet prairie, and buttonbush in the wettest ground nearest the
 *          water (`wettest`). The survey's willow thickets of Cook County
 *          (McBride and Bowles, through the flora dossier's ZONE 6) are the
 *          evidence the thickets were here at all. On the modelled ground the
 *          sloughs are the wet prairie and sedge meadow of the low South
 *          Division and the river's margin, so wetness is the zone and the
 *          ground's height (`wetY`), and the slough's edge is the water's
 *          (`edgeM`, the share of the density kept far from it in `inland`).
 *   lone   now and then a bur oak or a cottonwood standing alone where the
 *          fire passed it by: within `upwindM` east or north-east of water,
 *          the water lying upwind of it on a bearing the fire ran from
 *          (`fireFrom`, degrees; 270 is a west wind). McBride and Bowles found
 *          the trees denser, and the fire-intolerant ones gathered, on the east
 *          sides of watercourses, which broke the fires running west to east
 *          (the flora dossier's ZONE 6). The bur oak is the savanna's open-grown tree
 *          (z07), the cottonwood the river's (z05), the one on drier ground and
 *          the other on wetter. Andreas's "good stretch of level grass" south
 *          of the town is why they stay in the shadow band and do not stray
 *          over the open plain.
 *
 * Species and heights are the zone records' own; the rose, New Jersey tea and
 * the two willows are records this ticket added at a density of zero, so the
 * sward deals none of them and every stem is this file's. Every density, band
 * and weight here is invented and none is a count: docs/LIBERTIES.md
 * L-prairie-woody-2784. The same in 1812 and 1835, ground for ground: each
 * stand is dealt from a generator seeded by where it stands, off the shared
 * stream, so the 1835 town's ground (which is not prairie, `grounds`) takes
 * none and every other place takes the same. The phone's tier thins the
 * shrubs further (`keepK`), and a shrub under `smallM` tall is drawn at the
 * levels it would take `smallLodK` times further off. The lone trees are a few
 * dozen stems over the whole field, so every tier keeps as many of them
 * (`lone.keep`, full's own keep): a phone that thins the lone trees loses the
 * landmarks and saves nothing it could measure.
 */
const PRAIRIE_WOODY = {
  label: 'Prairie shrubs, slough-edge willows and buttonbush, and lone trees in the fire shadow',
  grounds: ['z01_wet_prairie', 'z02_mesic_prairie', 'z03_sedge_meadow', 'z04_marsh', 'z05_riverbank_timber'],
  dry: { perHa: [16, 36], clumpM: 26, wetCut: 0.65,
    mix: [['rosa_spp', 46], ['ceanothus_americanus', 24], ['amorpha_canescens', 30]] },
  wet: { perHa: [6, 16], clumpM: 30, edgeM: [24, 170], inland: 0.45, wetY: [1.24, 0.74],
    mix: [['salix_petiolaris', 40], ['salix_discolor', 30], ['spiraea_alba', 22]],
    wettest: [['cephalanthus_occidentalis', 40], ['salix_petiolaris', 32], ['salix_discolor', 14]],
    wettestEdgeM: 70 },
  lone: { perHa: [2.0, 3.6], keep: 0.7, upwindM: [60, 280], fireFrom: [205, 230, 255, 280], stepM: 7,
    mix: [['quercus_macrocarpa', 55], ['populus_deltoides', 45]], scale: [0.72, 1.0] },
  zones: {
    rosa_spp: 'z02_mesic_prairie', ceanothus_americanus: 'z02_mesic_prairie',
    amorpha_canescens: 'z02_mesic_prairie', salix_discolor: 'z03_sedge_meadow',
    salix_petiolaris: 'z03_sedge_meadow', spiraea_alba: 'z01_wet_prairie',
    cephalanthus_occidentalis: 'z04_marsh',
    quercus_macrocarpa: 'z07_bur_oak_savanna', populus_deltoides: 'z05_riverbank_timber',
  },
  // The records carry no bark; these are this file's, as EDGE_THICKET's are:
  // rose and leadplant brown canes, New Jersey tea grey-brown, the willows'
  // grey and red-brown wands, buttonbush and meadowsweet brown.
  bark: { rosa_spp: 0x6a4a3c, ceanothus_americanus: 0x6c6258, amorpha_canescens: 0x6e6450,
    salix_discolor: 0x787068, salix_petiolaris: 0x6b4a3a, cephalanthus_occidentalis: 0x6a5a4a,
    spiraea_alba: 0x6e5444 },
  keepK: { full: 1, balanced: 0.85, light: 0.55 },
  smallM: 1.3, smallLodK: 1.35,
  confidence: 'reconstructed',
  sources: ['mcbride_bowles_2007', 'andreas_1884_v1'],
};

/**
 * T-2808 — THE NORTH SIDE WOOD ON THE SAND, EAST OF STATE STREET. The timber's
 * east limit north of the river is State Street (TIMBER_EAST_LIMIT_STREETS),
 * read off Andreas's exception for "the sandy hills near the lake". Two
 * witnesses put woods further east than that, over the sand prairie of the
 * beach ridges, and stop them at the shore's own sand hills:
 *
 *   - Juliette Kinzie, spring 1831 (Wau-Bun, 1856): "through the woods on the
 *     north side of the river ... a little bridle-path took us along what is
 *     now Rush street. The thick boughs of the trees arched over our heads, and
 *     we were often compelled ... to break away the projecting branches of the
 *     shrubs which impeded our path." Rush Street is E 1054 here, 230 m east of
 *     State.
 *   - Judge Blodgett, 1831-32 (reported by Kirkland, 1893; the research notes'
 *     B5, not yet a source record): "the thick, tangled underbrush which filled
 *     the woods, covering almost all the North Side west of the shore
 *     sand-hills".
 *
 * So from `fromN` north the wood runs on east of State to `toE`, short of the
 * Wau-Bun sand hills (`sand_hills_north.inlandFromE`). On dry sand ridges the
 * lake plain's wood is oak: the ridge-oak community, open, with the mesic
 * pocket's closed canopy in a band either side of the Rush Street path
 * (`PATHS`), which is the one place a witness says the boughs met. The band is
 * kept narrow on purpose: the mesic pocket's basswood carries its July flower
 * and is drawn on the chunked path at full detail at any distance, which is the
 * dearest stem in the wood (T-2808 measured it). Its east end faces the sand hills with the same
 * edge thicket as the woods' other prairie edges. Dealt from a position-seeded
 * generator, so the shared stream and every other stem stand where they stood.
 *
 * Read, not invented: woods here at all, and a closed canopy and shrubs along
 * Rush Street. Invented: `toE`, `fromN`, the oak, the band.
 * docs/LIBERTIES.md L-north-side-paths-2808.
 */
const SAND_WOOD = {
  label: 'The North Side wood on the beach-ridge sand, east of State Street',
  fromN: 300, fadeN: 40, toE: 1140, wobbleM: 36,
  confidence: 'inferred',
  sources: ['kinzie_waubun_1856'],
};

/**
 * T-2808 — THE TWO WAYS THROUGH THE NORTH SIDE WOOD, each on a street line the
 * scene already holds:
 *
 *   rush   Kinzie's "little bridle-path ... along what is now Rush street"
 *          (Wau-Bun, 1831): a bare tread `clearM` either side of the platted
 *          line, the closed wood `closeBandM` either side of it (SAND_WOOD), and
 *          the shrubs she broke away crowding its margins (`shrubM`).
 *   green  "The northern, or Green Bay road ... was surveyed in 1833, stakes
 *          driven and trees blazed along the line. It was somewhat improved as
 *          far as Milwaukee in 1834, by ... cutting out the trees to the width of
 *          two rods" (Andreas, vol. 1, p. 299 of the IA index). Two rods is
 *          10.06 m. Drawn on the Clark Street line north of the town's Clark
 *          Street, the later N. Clark Street that carries the road's name in
 *          the histories; nobody traced the 1834 line. A year after the cut its
 *          margins carry stump sprouts and hazel (`shrubM`) and its middle is
 *          bare.
 *
 * No trunk stands within `treeClearM` of either line, a little wider than the
 * tread, so the edge trees' crowns leave the cut open to the sky the way a cut
 * through grown wood is.
 *
 * Neither is a street record: no wheel track is graded or drawn (the State road
 * to Vincennes is, T-1702, and that regraded the terrain). Here the woods give
 * way and the ground is the sward's. The lines are the street records'
 * centrelines, carried past their platted ends (`fromN` / `toN`, null for the
 * field's edge). docs/LIBERTIES.md L-north-side-paths-2808.
 */
const PATHS = [
  { id: 'rush_bridle_path', street: 'rush', label: "Kinzie's bridle path along the Rush Street line",
    fromN: 300, toN: null, clearM: 1.3, treeClearM: 1.8, shrubM: [1.3, 4.5], shrubPerHa: [300, 480],
    closeBandM: 22,
    sources: ['kinzie_waubun_1856'] },
  { id: 'green_bay_road_cut', street: 'clark_north', label: 'The Green Bay road, cut two rods wide (1834)',
    fromN: 'end', toN: null, clearM: 3.2, treeClearM: 8.5, shrubM: [3.2, 8.5], shrubPerHa: [160, 300],
    closeBandM: 0,
    sources: ['andreas_1884_v1'] },
];

/* -------------------------------------------------------------------------- */
/* the timber beyond the modelled ground                                       */
/* -------------------------------------------------------------------------- */

/**
 * Every body of timber the sources put outside the 640 m box, as a polyline of
 * its NEAR EDGE in local ENU metres — the near edge is what sets a silhouette.
 * `canopy` is the July canopy height range.
 *
 * These coordinates are NOT survey positions. Bearings and distances come from
 * § 1.6 and from the modern course of the rivers the sources name; the working
 * uncertainty on anything traced from the 1834 sheets is ~20 m, and on these,
 * kilometres out, far more. What is asserted is *there was timber over there,
 * about that far away, standing about that tall* — which is all a silhouette
 * shows.
 */
const FAR_TIMBER = [
  {
    id: 'south_branch_belt',
    label: 'The South Branch timber belt',
    canopy: [15, 26],
    crown: 13,
    path: [
      [82, -430], [78, -700], [10, -1180], [-40, -1700], [-64, -2166],
      [-250, -2700], [-470, -3120], [-620, -3400], [-665, -4100], [-690, -4900],
    ],
    confidence: 'inferred',
    sources: ['chicagology_prefire273'],
    note: 'Andreas: the South Side timber "follow[ed] the bend of the river … and '
        + 'extend[ed] south two or three miles". Documented as a body; the line '
        + 'drawn here is the east bank of the South Branch on its modern course, '
        + 'offset ~60 m from the channel, which is an inference about geometry, '
        + 'not about existence.',
  },
  {
    id: 'north_division_timber',
    label: 'The North Side body of timber',
    canopy: [14, 22],
    crown: 12,
    path: [
      [-60, 352], [40, 336], [130, 358], [215, 334], [300, 349], [385, 331],
      [470, 356], [560, 337], [645, 361], [730, 340], [820, 366],
    ],
    confidence: 'inferred',
    sources: ['chicagology_prefire273'],
    note: 'Andreas: the North Side carried "a body of thrifty heavy growth of '
        + 'timber", continuous except for the sandy hills near the lake and the '
        + 'marshy places; the 1821 PLS calls the ground north of the forks a '
        + '"swampy timber thicket". The front is carried east to about e +820, '
        + 'roughly 300 m short of the 1835 shore, because the sandy hills near '
        + 'the lake are the stated exception. The waviness is generated.',
  },
  {
    id: 'north_branch_belt',
    label: 'The North Branch timber, toward the Caldwell reservation',
    canopy: [13, 21],
    crown: 12,
    path: [
      [-95, 345], [-190, 700], [-300, 1150], [-470, 1750], [-700, 2450],
      [-1050, 3400], [-1500, 4300], [-1900, 5000],
    ],
    confidence: 'inferred',
    sources: [],
    note: 'The PLS surveyed the Sauganash / Billy Caldwell reservation up the '
        + 'North Branch and noted timber there (dossier § 1.6, NNW 4–8 mi). The '
        + 'belt is placed on the EAST bank, the fire-protected side — McBride & '
        + 'Bowles found density and fire-intolerant species concentrated east of '
        + 'watercourses. West of the channel stays prairie.',
  },
  {
    id: 'main_stem_belt_east',
    label: 'The South Water Street belt, east to Wells Street',
    canopy: [16, 24],
    crown: 13,
    /**
     * DERIVED, not authored — `tools/derive_timber_belt.py`, re-derived and
     * drift-checked by `tools/check.sh` (T-0031, ROADMAP R-BUG5(b)). The line is
     * the committed `south_water` centreline offset half a platted corridor
     * (12.192 m) to the SOUTH and clipped east at the mean easting of the
     * committed `wells` centreline — the same E +329.3 `timberEastLimits()`
     * hands the near-field planter, so the far body and the near wood cannot
     * disagree about where Andreas's belt ends. Move the street and the gate
     * fails until the belt moves with it.
     */
    path: [[111.1, -106.05], [130.31, -63.79], [148.49, -43.78],
      [167.3, -27.8], [185.06, -16.25], [221.7, -6.18], [328.78, -5.2]],
    confidence: 'reconstructed',
    sources: ['chicagology_prefire273'],
    note: 'Andreas: the South Side timber grew "along the river", "extend[ed] '
        + 'east as far as Wells Street" and followed the bend of the river south '
        + '— which `south_branch_belt` carries on from the forks. WHICH SIDE OF '
        + 'THE STREET the standing timber was on is asserted and not attested: '
        + 'south, behind the platted lot line, because § 02-flora reads the same '
        + 'sentence as leaving relict trees in the riverside BLOCKS (South '
        + 'Water–Lake, west of Wells) and because on this date the 11.5–36.0 m '
        + 'of dry ground between the street and the water is the working '
        + 'waterfront. Recorded as docs/LIBERTIES.md L182. Until 2026-08-27 this '
        + 'was a three-point stub from (326, 46) to (396, 68), authored on a '
        + 'Wells Street 66.7 m east of the committed centreline and 39 of 39 '
        + 'samples over the main stem — the line of trees across the channel in '
        + 'the owner\'s screenshot (R-BUG5).',
  },
  {
    id: 'south_branch_grove',
    label: 'The grove up the South Branch (Hardscrabble / Lee\'s Place)',
    canopy: [13, 20],
    crown: 12,
    /** A closed ring: the near edge of a grove is its whole outline. */
    path: ringPath(-2323, -5355, 430, 14),
    confidence: 'inferred',
    sources: ['chicagology_prefire273'],
    note: 'Andreas names it as the ONE piece of West Side timber. Its bearing '
        + '(about 203°) and distance (about 3.6 mi) are read off the modern '
        + 'position of Bridgeport, which is where Hardscrabble was.',
  },
];

/** Each far body's near-edge length in metres, and whether it closes on itself. */
const FAR_EDGE_LEN = FAR_TIMBER.map((b) => b.path.reduce((acc, p, i) => (i === 0 ? 0
  : acc + Math.hypot(p[0] - b.path[i - 1][0], p[1] - b.path[i - 1][1])), 0));
const FAR_EDGE_CLOSED = FAR_TIMBER.map((b) => {
  const a = b.path[0];
  const z = b.path[b.path.length - 1];
  return Math.hypot(a[0] - z[0], a[1] - z[1]) < 1;
});

/**
 * The named groves § 1.6 lists that are NOT drawn, with the arithmetic that
 * rules each one out. `elevation_deg` is how far the top of a canopy tree at
 * that distance stands above a standing eye's horizon, refraction included.
 * Under about a tenth of a degree is under two pixels at this field of view and
 * under the contrast threshold through 15 km of July haze.
 */
const OMITTED_TIMBER = [
  { id: 'cottage_grove', label: 'Cottage Grove', bearing_deg: 180, distance_m: 9660,
    canopy_m: 18, confidence: 'inferred',
    why: 'inferred, and at 6 mi it clears the horizon by under a tenth of a degree' },
  { id: 'big_woods', label: 'The Big Woods of north-east Cook', bearing_deg: 350,
    distance_m: 17700, canopy_m: 18, confidence: 'documented',
    why: 'documented, but at 11 mi the curvature of a flat plain has taken all but '
       + 'a few centimetres of it below the horizon' },
  { id: 'la_framboise', label: 'La Framboise Woods, Des Plaines River', bearing_deg: 270,
    distance_m: 16100, canopy_m: 20, confidence: 'documented',
    why: 'documented, same arithmetic as the Big Woods' },
  { id: 'blue_island', label: 'Blue Island', bearing_deg: 200, distance_m: 22500,
    canopy_m: 36, confidence: 'inferred',
    why: 'the moraine lifts its oaks 18 m, the only reason it clears the horizon at '
       + 'all — and then by a third of a pixel' },
];

/** A closed ring of points, for a grove whose outline is its silhouette. */
function ringPath(e, n, radius, steps) {
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const a = (i / steps) * Math.PI * 2;
    pts.push([e + Math.cos(a) * radius, n + Math.sin(a) * radius]);
  }
  return pts;
}

/* -------------------------------------------------------------------------- */
/* the zone records                                                            */
/* -------------------------------------------------------------------------- */

async function fetchOk(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} ${url}`);
  return res.json();
}

/** sRGB [r,g,b] 0-255 from a record -> the hex this file's tables speak. */
function rgbHex(rgb) {
  if (!Array.isArray(rgb) || rgb.length < 3) return null;
  return ((rgb[0] & 255) << 16) | ((rgb[1] & 255) << 8) | (rgb[2] & 255);
}

/** A lighter companion green, for a record that carries only one. */
function lighten(hex) {
  const r = Math.min(255, Math.round(((hex >> 16) & 255) * 1.34 + 26));
  const g = Math.min(255, Math.round(((hex >> 8) & 255) * 1.28 + 22));
  const b = Math.min(255, Math.round((hex & 255) * 1.42 + 20));
  return (r << 16) | (g << 8) | b;
}

const FORM_OF = {
  tree_gallery: 'gallery',
  tree_open_crown: 'open',
  tree_leaning: 'lean',
  tree_columnar: 'columnar',
  thicket_clonal: 'thicket',
  // T-2810: the two vines, drawn on the river woods' edge trees (VINE_EDGE).
  vine_drape: 'vine_drape',
};

const CONFIDENCE_VALUE = { attested: 0.0, inferred: 0.5, reconstructed: 1.0 };

/* -------------------------------------------------------------------------- */
/* the woody head — ROADMAP K45(c)                                             */
/* -------------------------------------------------------------------------- */

/**
 * Head archetype per RECORDED INFLORESCENCE SHAPE, for the woody cohort.
 *
 * K44 measured that three recorded July inflorescences draw no flower and named
 * the cause exactly: *"`trees.js` has no head archetype at all"*. Two of the
 * three are this file's — the **American basswood in bloom** (`flowering`,
 * `cluster_terminal`, sRGB 222,214,152) and the **ironwood's hop-like fruit**
 * (`fruiting`, `cluster_terminal`, 214,212,180), both in `z06_dense_forest` and
 * both in the `mesic_pocket` mix, so both stand in this scene today with nothing
 * on them. The third is the riverbank grape, whose `vine_drape` form no reader
 * implements; it is a ROUTING gap and stays K45(b)'s, not this parcel's.
 *
 * **The repair K44 wrote down is one step short of the truth, and this is the
 * finding.** Handing this file `flora.js`'s `HEAD_OF_SHAPE` verbatim draws
 * `cluster_terminal`'s count — **1 to 4 heads** — because that table is
 * calibrated for a forb, where the whole plant IS one flowering scape. On a
 * basswood the arithmetic says what that looks like: the record's own
 * `size_m` is [0.06, 0.12] m for ONE inflorescence, and a 0.09 m cluster at the
 * 23 m slant range of a neighbouring crown (11 m up, 20 m out) subtends
 * 0.0039 rad — **3.3 px** at this file's `DEFAULT_PX_PER_RAD` of 833. The crown
 * carrying them is 10–16 m across, which is **580 px** at the same range. Four
 * 3-px specks on a 580-px crown is not a tree in flower; it is four pixels of
 * noise, and it would have banked a false pass on K44's own assertion 5.
 *
 * So SIZE comes from the record exactly and MULTIPLICITY is keyed to the crown,
 * which is a liberty and is recorded as one (docs/LIBERTIES.md L115) for the
 * same reason `flora.js`'s is (L35): **the records give the density of PLANTS
 * and the size of ONE inflorescence, and say nothing about how many a plant
 * carries.** Keying it to the crown rather than to a constant is what makes an
 * 18 m basswood and a 7 m ironwood differ by their own evidenced `width_m`
 * instead of by a number typed here.
 *
 *   kind   which archetype draws it. `cluster` is a small dense blob; a
 *          pendulous `catkin` is drawn longer than it is wide. At 3 px the
 *          difference is a silhouette, not a shape, which is why there are two
 *          and not nine — this file is not `flora.js` and must not pretend the
 *          extra archetypes are resolvable at the ranges it draws at.
 *   perM   heads per metre of crown width, before the clamp below.
 *   band   how far DOWN from `height_frac` the heads are carried, as a fraction
 *          of crown height. A terminal cluster sits in the outer shell of the
 *          canopy; it is not scattered through its interior, where nothing
 *          would see it.
 *
 * The map is exhaustive over the shapes the woody records actually carry, and a
 * shape it cannot draw is REPORTED and draws nothing rather than being quietly
 * substituted — the same rule as `flora.js`, for the same reason.
 */
const WOODY_HEAD_OF_SHAPE = {
  cluster_terminal: { kind: 'cluster', perM: 1.6, band: 0.30 },
  berry_cluster: { kind: 'cluster', perM: 1.3, band: 0.34 },
  cluster_axillary: { kind: 'catkin', perM: 1.8, band: 0.52 },
  raceme: { kind: 'catkin', perM: 1.4, band: 0.36 },
  nut_husk: { kind: 'cluster', perM: 0.9, band: 0.30 },
  cherry: { kind: 'cluster', perM: 1.2, band: 0.34 },
};

/**
 * The clamp on that multiplicity, and both ends of it are about legibility
 * rather than botany. Below the floor a crown reads as unflowered and the
 * layer may as well not have been drawn; above the ceiling the heads merge into
 * a pale cap and the tree stops reading as a tree in flower and starts reading
 * as a tree with a different foliage colour. A 13 m basswood crown lands on 21
 * and a 5.5 m ironwood on 9.
 */
const HEADS_MIN = 6;
const HEADS_MAX = 26;

/** The July gate, copied from `flora.js` rather than imported, because these two
 *  files share no module and the rule is CONTRACT.md §5.4 rule 1 rather than
 *  either file's. A record that is vegetative or in bud in mid-July draws no
 *  head even if it carries one, and the contradiction is reported. K44: the
 *  woody layer had no July gate at all, because `july.phenology` was read by
 *  `flora.js` alone. */
const VEGETATIVE_PHASES = ['vegetative', 'budding'];

/**
 * One species' head spec, or null. Mirrors `flora.js`'s `headOf` — same gate,
 * same refusal to substitute an archetype — and differs only in what it keys
 * the count to.
 */
function woodyHeadOf(sp, zoneId, problems) {
  const july = sp.july ?? {};
  // Named for the field it holds, and that is load-bearing rather than a style
  // choice: `rgb` is an ambiguous leaf, so `tools/measure_layer_reads.py` scans
  // it PARENT-QUALIFIED (`inflorescence.rgb`). A local called `inflor` reads
  // the record just as truly and is invisible to the scan, which is how
  // `flora.js` ends up needing its whole expression matched verbatim instead.
  const inflorescence = july.inflorescence;
  if (!inflorescence) return null;
  if (VEGETATIVE_PHASES.includes(july.phenology)) {
    problems.push(`trees: ${zoneId}/${sp.id ?? sp.binomial} is '${july.phenology}' and `
      + 'still carries an inflorescence — no head is drawn; the record needs fixing');
    return null;
  }
  const style = WOODY_HEAD_OF_SHAPE[inflorescence.shape];
  if (!style) {
    problems.push(`trees: ${zoneId}/${sp.id ?? sp.binomial} records inflorescence shape `
      + `'${inflorescence.shape}', which has no woody archetype — its flower is not drawn`);
    return null;
  }
  const size = Array.isArray(inflorescence.size_m) && inflorescence.size_m.length === 2
    ? inflorescence.size_m : [0.06, 0.12];
  // `inflorescence.fruit` is deliberately NOT read here. K44 measured that the
  // boolean reaches nothing and that 29 of the 31 records carrying it are drawn
  // in the fruit's own colour and shape anyway — it is redundant with
  // `phenology: 'fruiting'`, which this function does read. Storing it on the
  // spec and drawing nothing from it would BE the fault K44 named, one field
  // further along, and would take it off that gate's banked list while changing
  // nothing a visitor sees.
  return {
    kind: style.kind,
    perM: style.perM,
    band: style.band,
    // The record's sRGB bytes. See `linear()` for why the transfer happens
    // exactly once on the way to a vertex colour.
    rgb: rgbHex(inflorescence.rgb),
    frac: clamp01(inflorescence.height_frac ?? 0.8),
    size,
    phenology: july.phenology ?? null,
  };
}

/**
 * Read the timber zones and hand back one render spec per species. The record
 * wins on everything it carries — height, crown width, July foliage, density,
 * confidence — and this file supplies only the draw archetype (bole fraction,
 * puff count, bark colour) plus a fallback for a species the records do not
 * name. A `form` this module cannot draw is recorded in
 * `stats.unimplementedForms` and drawn as nothing: reported through stats
 * rather than `problems`, because it is a gap in the RENDERER and `problems` is
 * what the repo smoke reads to decide whether the DATA loaded.
 */
/**
 * The eastings of the two streets `TIMBER_EAST_LIMIT_STREETS` names, read out of
 * the street records the scene index already carries.
 *
 * A street here is a centreline of two or more points and it is not exactly
 * north–south — Wells runs E +328.1 at N −400 to E +330.5 at N +7 — so the
 * limit is the mean of its points' eastings. Half a metre of skew on a limit
 * that decides whether a wood reaches a sand ridge 500 m further on is not
 * worth carrying, and a mean cannot be wrong in the way picking one end can.
 *
 * They come from the scene index the sidecar loader already fetched rather than
 * from a fetch of this file's own. `data/streets/1835.json` is compiled into
 * that index and is NOT published as itself, so a second fetch 404s on the site
 * while passing in the source tree — which is exactly the gap AGENTS.md says has
 * shipped bugs twice, and it caught this one in the `--published` smoke.
 *
 * If the records cannot be read the limits FALL BACK to the old square's east
 * edge and say so. That is the safe direction: the failure plants nothing new
 * rather than planting a wood over the beach on a missing record.
 */
function timberEastLimits(streetRecords, problems = []) {
  const fallback = { south: 316, north: 316, streets: {} };
  // T-2745 — A SCENE THAT DRAWS NO STREETS (1812) STILL HAS THE LAND THEY
  // FOLLOWED. The limits are landforms first: Andreas's east end of the river
  // timber and the State Street break of slope where the clay gives way to the
  // beach-ridge sand (generators/terrain_gen.py builds it off the two State
  // Street control points). An empty street list is a scene before the
  // streets, not a failed load, so it takes those lines at the eastings the
  // 1835 records survey them at, and the North Side wood runs to the sand in
  // 1812 as it does in 1835. A list that lacks the street is still the failure
  // below.
  if (Array.isArray(streetRecords) && streetRecords.length === 0) {
    const out = { south: LANDFORM_EAST_M.south, north: LANDFORM_EAST_M.north, streets: {} };
    for (const [side, id] of Object.entries(TIMBER_EAST_LIMIT_STREETS)) {
      out.streets[side] = { id, name: `the line ${id} later took`, east_m: LANDFORM_EAST_M[side],
        landform: true };
    }
    return out;
  }
  const out = { south: 0, north: 0, streets: {} };
  for (const [side, id] of Object.entries(TIMBER_EAST_LIMIT_STREETS)) {
    const st = (streetRecords ?? []).find((s) => s.id === id);
    const pts = st?.path_local_enu_m;
    if (!Array.isArray(pts) || !pts.length) {
      problems.push(`trees: the scene index carries no centreline for ${id}, which is the `
        + `documented east end of the ${side} division's timber — the woody layer is held `
        + 'at the old E +316 edge rather than planting a wood over the beach ridges');
      return fallback;
    }
    const e = pts.reduce((a, p) => a + p[0], 0) / pts.length;
    out[side] = e;
    out.streets[side] = { id, name: st.name_1835 ?? id, east_m: Math.round(e * 10) / 10 };
  }
  return out;
}

async function loadTimberZones(dataBase, problems = [], sceneId = null) {
  const manifestUrl = new URL('flora/index.json', dataBase);
  const manifest = await fetchOk(manifestUrl);
  const specs = {};
  const byZone = {};
  const shrubByZone = {};
  const vineByZone = {};
  const bands = {};
  const woody = {};
  const unimplemented = new Set();
  const zonesRead = [];
  const heads = [];
  for (const id of TIMBER_ZONES) {
    const entry = (manifest.zones ?? []).find((z) => z.id === id);
    if (!entry) throw new Error(`flora/index.json names no zone ${id}`);
    const rec = await fetchOk(new URL(entry.file, manifestUrl));
    zonesRead.push(id);
    bands[id] = {};
    // T-1056 — THE SAME WOODY BOUND `flora.js` READS, OFF THE SAME RECORD.
    // A zone that states where woody growth establishes states it for every
    // woody role it lists, and the poplars this file plants on the dune are
    // three of them. Reading the block here rather than restating the numbers
    // is the whole point: two renderers, one claim, gated once in validate.py.
    if (rec.woody_stratum) woody[id] = rec.woody_stratum;
    for (const sp of rec.species ?? []) {
      // A DOORYARD SHRUB (T-0074). `shrub_low` is flora.js's stratum — dealt on
      // its own lattice at the zone's recorded density — and it stays that way:
      // nothing here enters `specs`, `byZone` or `bands`, so no community deal
      // moves. What a lattice cannot do is put a currant AT a particular door,
      // which is exactly what a planting record states — so the species is held
      // in a separate table the planting loop alone reads, drawn with its own
      // three-puff clump archetype (`addShrubClump`) at its own recorded band.
      // That path draws no head, so the July berry cluster the record carries
      // is NOT drawn — the planting record says so rather than leaving the
      // drop silent.
      // T-2784: every `shrub_low` record, whatever form flora.js draws it in
      // (the leadplant is its `forb_spike`), since PRAIRIE_WOODY grows it as a
      // shrub; and its open July flower or fruit as `flower`, which only
      // PRAIRIE_WOODY hangs on its shrubs (as `bloom`, tree-model.js), so no
      // other shrub here changes.
      if (sp.role === 'shrub_low') {
        const dark = rgbHex(sp.july?.foliage_rgb);
        const open = sp.july?.inflorescence && !VEGETATIVE_PHASES.includes(sp.july?.phenology);
        shrubByZone[id] = shrubByZone[id] ?? {};
        shrubByZone[id][sp.id] = {
          speciesId: sp.id,
          common: sp.common ?? sp.id,
          form: 'shrub',
          h: Array.isArray(sp.height_m) && sp.height_m.length === 2
            ? sp.height_m : [0.8, 1.5],
          crownW: Array.isArray(sp.width_m) && sp.width_m.length === 2
            ? sp.width_m : null,
          dark: dark ?? 0x53663c,
          light: dark != null ? lighten(dark) : 0x7d9159,
          // Invented, as every bark in SPECIES is: dull grey-brown shrub wood,
          // darker than the aspen's pale bole, lighter than the dark openings.
          bark: 0x6a5c4b,
          conf: Math.max(0.5, CONFIDENCE_VALUE[sp.confidence] ?? 0.5),
          july: sp.july?.appearance ?? null,
          head: null,
          // The four fields the bloom draws, and not the record's `fruit`
          // flag (see `headOf` on why that one stays unread).
          flower: open ? {
            shape: sp.july.inflorescence.shape,
            rgb: sp.july.inflorescence.rgb,
            height_frac: sp.july.inflorescence.height_frac,
            size_m: sp.july.inflorescence.size_m,
          } : null,
          fromRecord: true,
        };
        continue;
      }
      if (sp.role !== 'tree' && sp.role !== 'thicket') continue;
      const form = FORM_OF[sp.form];
      if (!form) { unimplemented.add(sp.form); continue; }
      // T-2810 — A VINE is neither a stem a community deals nor a thicket: it
      // hangs on a tree the wood already stands, so it is held apart, as the
      // dooryard shrubs are, and only VINE_EDGE reads it. Its recorded band is
      // the height it climbs to; the drawing caps it at its host's crown. The
      // grape's July fruit (hard green clusters a few centimetres across) is
      // hung in the curtain by the vine's own template (`berries`), not by the
      // head path.
      if (form === 'vine_drape') {
        const dark = rgbHex(sp.july?.foliage_rgb);
        vineByZone[id] = vineByZone[id] ?? {};
        vineByZone[id][sp.id] = {
          speciesId: sp.id,
          common: sp.common ?? sp.id,
          form,
          h: Array.isArray(sp.height_m) && sp.height_m.length === 2 ? sp.height_m : [4, 12],
          dark: dark ?? 0x56763c,
          light: dark != null ? lighten(dark) : 0x7f9b5a,
          conf: Math.max(0.5, CONFIDENCE_VALUE[sp.confidence] ?? 0.5),
          july: sp.july?.appearance ?? null,
          head: null,
          berries: sp.july?.phenology === 'fruiting' ? sp.july?.inflorescence ?? null : null,
          fromRecord: true,
        };
        continue;
      }
      // The recorded band, kept PER ZONE. It is the constraint a community's
      // hand weight is checked against (ROADMAP K46) and no longer a value
      // that replaces one: collapsing it to a first-zone-wins midpoint is
      // exactly what overwrote seventeen of the twenty-six mix entries.
      const perHa = sp.abundance?.density_per_ha;
      if (Array.isArray(perHa) && perHa.length === 2) {
        bands[id][sp.id] = [perHa[0], perHa[1]];
      }
      // The archetype this record is drawn with: the zone's own if it declares
      // one, and otherwise the species table's. A zone entry is needed only
      // where two zones describe the same species as different trees — see
      // ARCHETYPE_BY_ZONE, which is the dune cottonwood against the gallery one.
      const base = ARCHETYPE_BY_ZONE[id]?.[sp.id] ?? SPECIES[sp.id] ?? SPECIES.ulmus_americana;
      const dark = rgbHex(sp.july?.foliage_rgb);
      const light = rgbHex(sp.july?.foliage_rgb_alt);
      const spec = {
        ...base,
        speciesId: sp.id,
        common: sp.common ?? base.common,
        form,
        h: Array.isArray(sp.height_m) && sp.height_m.length === 2 ? sp.height_m : base.h,
        crownW: Array.isArray(sp.width_m) && sp.width_m.length === 2 ? sp.width_m : null,
        dark: dark ?? base.dark,
        light: light ?? (dark != null ? lighten(dark) : base.light),
        // Never better than `inferred`, whatever the species record says: the
        // record attests that the species stood in this community, and this
        // module invented the position of every individual stem in the scene.
        conf: Math.max(0.5, CONFIDENCE_VALUE[sp.confidence] ?? 0.5),
        july: sp.july?.appearance ?? base.july,
        // The recorded July inflorescence, or null. A thicket is drawn by
        // `addThicket`, which has no head path, so a head on one would be
        // silently dropped — reported here instead, because a dropped flower
        // that nothing says was dropped is exactly the fault K44 measured.
        head: woodyHeadOf(sp, id, problems),
        fromRecord: true,
      };
      if (spec.head) {
        if (form === 'thicket') {
          problems.push(`trees: ${id}/${sp.id} is a thicket carrying a `
            + `'${sp.july.inflorescence.shape}' inflorescence, and the clonal path draws `
            + 'no head — its flower is not drawn');
          spec.head = null;
        } else if (!heads.includes(sp.id)) {
          heads.push(sp.id);
        }
      }
      // Kept BOTH ways. `byZone` is what a community citing this zone plants
      // with; `specs` stays the first-zone-wins table every direct `addTree`
      // call site and every community without a `specsFrom` still reads, so
      // nothing outside the dune is redealt by this.
      byZone[id] = byZone[id] ?? {};
      byZone[id][sp.id] = spec;
      if (!specs[sp.id]) specs[sp.id] = spec;
    }
  }
  // THE STEMS A RECORD PLACES ITSELF. Everything above is ecology — what may
  // grow in a community and how densely — and it answers for the wood. It
  // cannot answer for a tree somebody KEPT: image 8 of the owner's brief shows
  // trees standing behind the Sauganash's yard fence, and no density over the
  // settled town will ever put one there rather than three doors down. So a
  // planting record states the stem, and it is read through the same manifest
  // and by the same rule as everything else here — exactly the files named,
  // never a probe. A planting is a claim about the scene it names (T-0471): the
  // 1812 shore is not planted with 1835's dooryards. The zone records above are
  // still read whole — they are ecology, and z10's poplar is reachable only
  // through a planting, so a scene without the rows cannot select it.
  const plantings = [];
  for (const entry of manifest.plantings ?? []) {
    if (!floraInScene(entry, sceneId)) continue;
    plantings.push(await fetchOk(new URL(entry.file, manifestUrl)));
  }
  return { specs, byZone, shrubByZone, vineByZone, bands, woody, unimplemented: [...unimplemented],
    zonesRead, heads, plantings };
}

/* -------------------------------------------------------------------------- */
/* small maths                                                                 */
/* -------------------------------------------------------------------------- */

function mulberry32(seed) {
  let a = seed >>> 0;
  return function rnd() {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const lerp = (a, b, t) => a + (b - a) * t;
const clamp01 = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);
function smoothstep(a, b, v) {
  const t = clamp01((v - a) / (b - a || 1e-6));
  return t * t * (3 - 2 * t);
}

/** Deterministic hash of two integers -> [0,1). */
function hash2(x, y) {
  let h = Math.imul(x | 0, 374761393) ^ Math.imul(y | 0, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

/** Smooth value noise on a lattice of `cell` metres, in [0,1]. */
function noise2(e, n, cell, salt = 0) {
  const x = e / cell;
  const y = n / cell;
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);
  const fx = x - x0;
  const fy = y - y0;
  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);
  const a = hash2(x0 + salt, y0);
  const b = hash2(x0 + 1 + salt, y0);
  const c = hash2(x0 + salt, y0 + 1);
  const d = hash2(x0 + 1 + salt, y0 + 1);
  return lerp(lerp(a, b, sx), lerp(c, d, sx), sy);
}

/** Smooth value noise along one axis, in [0,1]. */
function noise1(u, salt = 0) {
  const i = Math.floor(u);
  const f = u - i;
  const s = f * f * (3 - 2 * f);
  return lerp(hash2(i, salt), hash2(i + 1, salt), s);
}

/** Squared distance from a point to a segment, in the plane. */
function segDist2(px, py, ax, ay, bx, by) {
  const vx = bx - ax;
  const vy = by - ay;
  const wx = px - ax;
  const wy = py - ay;
  const len = vx * vx + vy * vy;
  const t = len > 0 ? clamp01((wx * vx + wy * vy) / len) : 0;
  const dx = wx - vx * t;
  const dy = wy - vy * t;
  return dx * dx + dy * dy;
}

/* -------------------------------------------------------------------------- */
/* a growable mesh                                                             */
/* -------------------------------------------------------------------------- */

/**
 * Trees are MERGED rather than instanced, on purpose. An InstancedMesh is one
 * draw call for the lot, but every tree of a species is then the same tree at a
 * different scale, and a stand of clones is exactly what an open-grown savanna
 * must not look like. Chunked spatially — a 120 m lattice since T-0223, each
 * cell culled on its own and all of them submitted as one batched multi-draw —
 * merging costs no more and buys real per-tree variation.
 */
class MeshBuf {
  constructor(detail = 'full') {
    this.detail = detail;
    this.leafFamily = 3;
    this.sprays = 0;
    /** How many inflorescences landed in this chunk (ROADMAP K45(c)). Counted
     *  where they are built rather than estimated from the stem count, because
     *  the multiplicity is a function of each tree's own crown width. */
    this.heads = 0;
    this.pos = [];
    this.nrm = [];
    this.col = [];
    this.flex = [];
    this.conf = [];
    this.uv = [];
    this.leaf = [];
    this.idx = [];
  }

  get count() { return this.pos ? this.pos.length / 3 : this.vertexCount; }

  vert(x, y, z, nx, ny, nz, r, g, b, flex, conf, uv = treeAtlasUV(15, 0.5, 0.5), leaf = 0) {
    this.pos.push(x, y, z);
    this.nrm.push(nx, ny, nz);
    this.col.push(r, g, b);
    this.flex.push(flex);
    this.conf.push(conf);
    this.uv.push(...uv);
    this.leaf.push(leaf);
    return this.count - 1;
  }

  tri(a, b, c) { this.idx.push(a, b, c); }

  build() {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(this.pos), 3));
    g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(this.nrm), 3));
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(this.col), 3));
    g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(this.uv), 2));
    g.setAttribute('aLeaf', new THREE.BufferAttribute(new Float32Array(this.leaf), 1));
    g.setAttribute('aFlex', new THREE.BufferAttribute(new Float32Array(this.flex), 1));
    g.setAttribute('_confidence',
      new THREE.BufferAttribute(new Float32Array(this.conf), 1));
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(this.idx), 1));
    g.computeBoundingSphere();
    return g;
  }

  /** Drop the scratch arrays once `build()` has copied them (T-2063). They are
   *  JS number arrays at twice a Float32Array's size, and the chunk map that
   *  holds them outlives the boot. Counts are kept so the stats still read. */
  release() {
    this.vertexCount = this.count;
    this.indexCount = this.idx.length;
    this.pos = this.nrm = this.col = this.flex = this.conf = this.uv = this.leaf = this.idx = null;
  }
}

/* -------------------------------------------------------------------------- */
/* building one tree                                                           */
/* -------------------------------------------------------------------------- */

const _c = new THREE.Color();
/**
 * sRGB hex -> linear rgb triple, which is what a vertex colour must be.
 *
 * ONE conversion, and the reason is worth stating because this function used to
 * do two. `THREE.ColorManagement.enabled` is true by default from r152, and
 * `Color.setHex(hex)` takes `SRGBColorSpace` as its default argument — so it has
 * ALREADY landed the value in the linear working space by the time it returns.
 * The `.convertSRGBToLinear()` that used to follow squared the transfer, which
 * for a July green is a factor of about twelve: the horizon band rendered at
 * L 102 where this file's own haze law asks for L 158, and the near timber was
 * only survivable because the error was being paid for twice over in the
 * lighting. `flora.js` builds its colours from a float triple, which
 * `Color(r,g,b)` does NOT convert, so its single explicit conversion is correct
 * — that asymmetry is exactly why the sward and the timber disagreed.
 */
function linear(hex) {
  _c.setHex(hex);
  return [_c.r, _c.g, _c.b];
}

/**
 * The vertex colour whose DISPLAYED value is the one a fully fogged surface
 * displays — the colour the band's hazed end has to reach for, because that is
 * where the far ground it stands on converges.
 *
 * **It is `linear(HORIZON_HAZE)`, and until 2026-08-13 it was that run through
 * ACES as well.** The tone curve was not wrong arithmetic; it answered a
 * question the renderer never asks. The band is a `MeshBasicMaterial` with
 * `toneMapped = false`, so its fragment goes `opaque → colorspace` and a linear
 * vertex colour displays as exactly the sRGB hex it decodes from. The ground's
 * fragment goes `opaque → tonemapping → colorspace → fog`, and in the vendored
 * r185 `fogColor` is uploaded through `getUnlitUniformColorSpace()` — so the
 * fog is a straight lerp toward the literal hex AFTER the tone curve. Both ends
 * therefore land on the same target by decoding the same hex once, and the tone
 * curve was applied to one of them and to nothing it had to match.
 *
 * What that error cost is measured in docs/LIBERTIES.md L35: the band was aimed
 * at sRGB (152,175,195) while the ground under it converges to (136,163,192),
 * so the far timber sat **16 red and 12 green** off the far ground it touches,
 * with nothing downstream to reconcile them — `fog: false` on this material
 * means the band never meets the lerp that would have closed the gap. That is
 * the hard chroma break along the horizon, and it is this file's bug rather
 * than the atmosphere's: the copied constants matched `world.js` exactly the
 * whole time; it was the maths on top of them that drifted.
 *
 * Kept as a function, and derived rather than pasted, so the band still cannot
 * silently drift when the atmosphere parcel next moves `HORIZON_HAZE`.
 */
function hazeDisplayLinear() {
  return linear(HORIZON_HAZE);
}

/* -------------------------------------------------------------------------- */
/* how a crown is lit                                                          */
/* -------------------------------------------------------------------------- */

/**
 * A last multiplier on the record's foliage colour before it is used as diffuse
 * reflectance — the one calibration knob for how dark the timber stands.
 *
 * It sits at 1.0, and that is the finding rather than a default: the record's
 * `july.foliage_rgb`, converted ONCE to linear, is already a plausible leaf
 * reflectance (sRGB 57,72,47 is 4 % / 6 % / 3 %), so nothing needs scaling. What
 * had to be modelled instead was the crown's own SELF-SHADOWING, below. That
 * distinction matters: round 1 hit roughly the right average by squaring the
 * sRGB transfer, which darkened the sunlit cap and the deep interior by the same
 * factor and so flattened the crown into a ball. The darkness of a stand is a
 * lighting fact, not a pigment fact, and it belongs in the shading term.
 *
 * Kept as a named constant because it is where a future change to `world.js`'s
 * rig (a 3.0 sun plus a 2.4 hemisphere today) has to be absorbed. The check is
 * measured, not judged, exactly as `world.js` does for `SKY_EXPOSURE`: the near
 * stand should hold the Weber contrast the bar photograph's own tree mass holds
 * against its sky — 0.625 in `bar/dupage_tallgrass_2018-07-24.jpg`, against
 * 0.655 here.
 */
const CANOPY_ALBEDO = 1.00;
/**
 * T-2015: the old closed crown's 0.060 occlusion floor was a stand-in for
 * thousands of absent leaves. Applying it to real cutout sprays double-counts
 * shade and makes each leaf almost black. Open sprays retain 44% indirect
 * reflectance; the light rig and cutout shadow map supply the real occlusion.
 * Bark is likewise a lit textured surface, not the old dark placeholder pole.
 */
const CROWN_SHADE_FLOOR = 0.44;
const BARK_ALBEDO = 0.90;
function barkColour(hex) {
  const rgb = linear(hex);
  const luminance = rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
  // The original flat bark swatches baked in crown shade. Grain and shadows
  // now supply that shade, so recover a plausible 22% minimum diffuse value
  // before applying them. Preserve each species' hue and its pale upper limbs.
  const gain = Math.max(1, 0.22 / Math.max(0.001, luminance)) * BARK_ALBEDO;
  return rgb.map(v => Math.min(0.78, v * gain));
}

/**
 * An open volume of branch sprays, NEVER a closed foliage solid. Each two-face
 * card has hundreds of leaf-scale alpha cutouts and bare twigs in a species
 * atlas. Diverse orientations prevent a cross-billboard/star silhouette.
 * Light keeps eight sprays (16 triangles vs the former 20-face solid), paying
 * for the bent limbs below without raising the mobile floor. Upper tiers buy
 * more overlapping branch layers, not larger leaves or a different tree mix.
 */
function addPuff(buf, cx, cy, cz, radius, squash, dark, light, shade, flexBase, rnd, conf) {
  // The placement stream is shared with the next tree. The retired primitive
  // used precisely 24 draws (jitter + light for each of 12 vertices). Consume
  // that same reservation, then grow all surface detail on a private stream.
  // Neither tier nor leaf count can re-deal a station or a species downstream.
  let seed = 0;
  for (let i = 0; i < 24; i++) seed = (Math.imul(seed, 31) ^ Math.floor(rnd() * 4294967296)) >>> 0;
  rnd = mulberry32(seed);
  // T-2473: a caller may cap the sprays a mass carries (the 1904 parkway elm's
  // early-spring crown is a few leafing tufts on bare wood); the 1835 timber sets no cap.
  const sprays = Math.min(buf.sprayCap ?? Infinity,
    buf.detail === 'light' ? 8 : buf.detail === 'balanced' ? 14 : 20);
  const phase = rnd() * Math.PI * 2;
  for (let i = 0; i < sprays; i++) {
    const a = phase + i * 2.3999632297;
    const up = (i + 0.5) / sprays;
    const yy = up * 2 - 1;
    const rr = Math.sqrt(Math.max(0, 1 - yy * yy));
    const k = radius * (0.38 + rnd() * 0.38);
    const px = cx + Math.cos(a) * rr * k;
    const py = cy + yy * k * squash;
    const pz = cz + Math.sin(a) * rr * k;
    const yaw = a + (rnd() - 0.5) * 1.8;
    const tilt = -0.65 + rnd() * 1.55;
    const ct = Math.cos(tilt), st = Math.sin(tilt);
    const cu = Math.cos(yaw), su = Math.sin(yaw);
    const roll = rnd() * Math.PI * 2, cr = Math.cos(roll), sr = Math.sin(roll);
    const ux = cu * cr - su * st * sr, uy = ct * sr, uz = su * cr + cu * st * sr;
    const vx = -cu * sr - su * st * cr, vy = ct * cr, vz = -su * sr + cu * st * cr;
    const nx = -su * ct, ny = -st, nz = cu * ct;
    const w = radius * (1.03 + rnd() * 0.34);
    const h = radius * (1.38 + rnd() * 0.42) * squash;
    const lit = clamp01(0.15 + shade * 0.47 + up * 0.38);
    const occ = CANOPY_ALBEDO * lerp(CROWN_SHADE_FLOOR, 1, lit);
    const tint = 0.83 + rnd() * 0.29;
    const colour = dark.map((v, j) => lerp(v, light[j], 0.35 + lit * 0.65) * occ * tint);
    const tile = buf.leafFamily + (rnd() < 0.5 ? 0 : 7);
    const flip = rnd() < 0.5;
    const base = buf.count;
    for (const [u, v] of [[0, 0], [1, 0], [1, 1], [0, 1]]) {
      const du = (u - 0.5) * w, dv = (v - 0.5) * h;
      // Smooth botanical normals follow the spray volume, not a flat billboard.
      const normal = new THREE.Vector3(nx + ux * (u - 0.5) * 0.7,
        ny + 0.32 + (v - 0.5) * 0.4, nz + uz * (u - 0.5) * 0.7).normalize();
      buf.vert(px + ux * du + vx * dv, py + uy * du + vy * dv, pz + uz * du + vz * dv,
        normal.x, normal.y, normal.z, ...colour, flexBase + v * 0.20, conf,
        treeAtlasUV(tile, flip ? 1 - u : u, v), 1);
    }
    buf.tri(base, base + 1, base + 2); buf.tri(base, base + 2, base + 3);
    buf.sprays++;
  }
}

/**
 * The head primitive: an OCTAHEDRON, six vertices and eight faces.
 *
 * The cheapest closed solid is a tetrahedron and it was rejected on its
 * silhouette rather than on its cost — edge-on a tetrahedron is a sliver, and a
 * flower cluster that disappears from a third of the bearings around the tree is
 * a worse artefact than the two extra vertices are a saving. Eight faces
 * remain cheaper than a spray volume, which is the
 * right ratio: at the ranges this file draws at a head is 3 px and a crown is
 * 580 (see `WOODY_HEAD_OF_SHAPE`), so the head is where the geometry budget must
 * NOT be spent.
 */
const OCT_V = [
  [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1],
];
const OCT_F = [
  [0, 2, 4], [2, 1, 4], [1, 3, 4], [3, 0, 4],
  [2, 0, 5], [1, 2, 5], [3, 1, 5], [0, 3, 5],
];

/**
 * Add one inflorescence: a small blob in the record's own flower colour,
 * sitting in the outer shell of the crown.
 *
 * `stretch` is what separates the two archetypes — a `catkin` hangs, so it is
 * drawn longer than it is wide and dropped below its anchor; a `cluster` is
 * roughly isotropic. `lit` carries the same crown self-shadowing the foliage
 * gets, because a flower deep in a canopy is in the same shade the leaves
 * around it are, and a bloom drawn at full brightness through the whole crown
 * is the "glowing lights in a dark tree" failure.
 */
function addHead(buf, cx, cy, cz, radius, stretch, colour, lit, flex, rnd, conf) {
  const base = buf.count;
  const shade = lerp(0.34, 1.0, lit);
  const r = colour[0] * shade;
  const g = colour[1] * shade;
  const b = colour[2] * shade;
  for (let i = 0; i < 6; i++) {
    const v = OCT_V[i];
    const k = radius * (0.72 + rnd() * 0.56);
    buf.vert(
      cx + v[0] * k,
      cy + v[1] * k * stretch,
      cz + v[2] * k,
      v[0], v[1], v[2],
      r, g, b, flex, conf,
    );
  }
  for (const f of OCT_F) buf.tri(base + f[0], base + f[1], base + f[2]);
}

/** Add a tapered n-sided prism — a bole, or a limb. */
function addStem(buf, x0, y0, z0, x1, y1, z1, r0, r1, colour, sides, flex0, flex1, conf) {
  const dx = x1 - x0;
  const dy = y1 - y0;
  const dz = z1 - z0;
  const len = Math.hypot(dx, dy, dz) || 1e-4;
  // A frame perpendicular to the stem.
  const ux = dx / len;
  const uy = dy / len;
  const uz = dz / len;
  let ax = 0;
  let ay = 0;
  let az = 1;
  if (Math.abs(uz) > 0.9) { ax = 1; az = 0; }
  let px = uy * az - uz * ay;
  let py = uz * ax - ux * az;
  let pz = ux * ay - uy * ax;
  const pl = Math.hypot(px, py, pz) || 1e-4;
  px /= pl; py /= pl; pz /= pl;
  const qx = uy * pz - uz * py;
  const qy = uz * px - ux * pz;
  const qz = ux * py - uy * px;

  const base = buf.count;
  for (let ring = 0; ring < 2; ring++) {
    const bx = ring ? x1 : x0;
    const by = ring ? y1 : y0;
    const bz = ring ? z1 : z0;
    const rr = ring ? r1 : r0;
    const fl = ring ? flex1 : flex0;
    for (let s = 0; s <= sides; s++) {
      const a = (s / sides) * Math.PI * 2;
      const ca = Math.cos(a);
      const sa = Math.sin(a);
      const nx = px * ca + qx * sa;
      const ny = py * ca + qy * sa;
      const nz = pz * ca + qz * sa;
      buf.vert(bx + nx * rr, by + ny * rr, bz + nz * rr, nx, ny, nz,
        colour[0], colour[1], colour[2], fl, conf, treeAtlasUV(14, s / sides, ring));
    }
  }
  for (let s = 0; s < sides; s++) {
    const a = base + s;
    const b = base + s + 1;
    const c = a + sides + 1;
    const d = b + sides + 1;
    // The ring frame is clockwise viewed down the stem. Outward winding must
    // agree with the radial normals: DoubleSide otherwise flips them inward,
    // turning even sunlit textured bark into a black silhouette.
    buf.tri(a, b, c);
    buf.tri(b, d, c);
  }
}

/**
 * A clonal thicket — sandbar willow on a point bar, and the one woody form in
 * this file that genuinely has no bole.
 *
 * Round 1 drew it as four loose icosahedra with `addStem` skipped entirely, so
 * a thicket was a handful of pale cushions scattered up to 3.6 m off-axis with
 * NOTHING underneath any of them, spreading to 7.8 m and with single puffs
 * about 5 m across. They read as floating polygons near the camera because that
 * is what they were. On the brief's own test — do the willow thickets screen
 * the point bars? — the answer was no; 202 isolated cushions screen nothing,
 * which is the exact opposite of the dossier's "dense clonal screens" at 2–6
 * stems/m².
 *
 * So it is built the way the plant grows: many thin whippy stems off one
 * rootstock, rising from a small basal patch and splaying into a fountain, with
 * every foliage mass centred ON a stem axis rather than hovering near one. That
 * is what makes the clump continuous from the ground up, and a row of them a
 * screen. A clump is about as wide as it is tall — sandbar willow gets its
 * width by standing shoulder to shoulder, not by each stool sprawling.
 */
function addThicket(buf, spec, x, groundY, z, rnd, scale = 1) {
  const conf = spec.conf ?? 0.5;
  const h = lerp(spec.h[0], spec.h[1], rnd()) * scale;
  const spread = h * 0.78 * (0.85 + rnd() * 0.30);

  const dark = linear(spec.dark);
  const light = linear(spec.light);
  const bark = barkColour(spec.bark);
  const tint = 0.90 + rnd() * 0.20;
  const d2 = dark.map((v) => v * tint);
  const l2 = light.map((v) => v * tint);

  const stems = 7 + Math.floor(rnd() * 5);
  const basal = 0.16 + rnd() * 0.26;
  for (let i = 0; i < stems; i++) {
    const a = (i / stems) * Math.PI * 2 + rnd() * 0.9;
    const br = basal * (0.30 + rnd() * 0.70);
    const bx = x + Math.cos(a) * br;
    const bz = z + Math.sin(a) * br;
    const out = (0.22 + rnd() * 0.28) * spread;
    const sh = h * (0.62 + rnd() * 0.38);
    const tx = x + Math.cos(a) * out;
    const tz = z + Math.sin(a) * out;
    const ty = groundY + sh;
    const rad = 0.018 + rnd() * 0.022;
    // Below ground at the foot, so a clump on uneven bar sand never floats.
    addStem(buf, bx, groundY - 0.10, bz, tx, ty, tz, rad, rad * 0.45,
      bark, 4, 0.10, 0.62, conf);

    // The foliage rides the stem: a mass at the tip, and on most stems a second
    // one lower down, which is what fills the screen from about knee height up.
    // A thicket is a DENSE mass, so most of its surface is shaded by the rest
    // of the clump — the shade values stay well below a free-standing crown's,
    // or the screen renders as a heap of pale pebbles rather than as willow.
    const pr = spread * (0.20 + rnd() * 0.12);
    addPuff(buf, tx, ty - pr * 0.25, tz, pr, 0.72, d2, l2,
      0.34 + rnd() * 0.38, 0.62, rnd, conf);
    if (rnd() < 0.55) {
      const f = 0.34 + rnd() * 0.30;
      addPuff(buf, lerp(bx, tx, f), lerp(groundY, ty, f), lerp(bz, tz, f),
        pr * 0.82, 0.78, d2, l2, 0.08 + rnd() * 0.24, 0.34, rnd, conf);
    }
  }
  return h;
}

/**
 * One dooryard shrub: a knee-high leaf clump on a few woody sticks (T-0074).
 *
 * NOT `addThicket` at small scale, and the difference is the budget: a thicket
 * is 7-12 full stems each carrying one or two foliage masses — right for a
 * 3 m bank willow screen read from across the river, and 685 scene triangles
 * for a currant bush a metre tall (measured on the published mirror,
 * 2026-08-20). A currant reads as ONE rounded mass with wood at its base, so
 * that is what is drawn: three short stems, three overlapping puffs, ~84
 * near-buffer triangles. The crown width is the record's own `width_m` band
 * when it carries one, the same rule the trees follow.
 */
function addShrubClump(buf, spec, x, groundY, z, rnd, scale = 1) {
  const conf = spec.conf ?? 0.5;
  const h = lerp(spec.h[0], spec.h[1], rnd()) * scale;
  const w = (Array.isArray(spec.crownW)
    ? lerp(spec.crownW[0], spec.crownW[1], rnd()) : h * 0.95) * scale;
  const dark = linear(spec.dark);
  const light = linear(spec.light);
  const bark = barkColour(spec.bark);
  const tint = 0.90 + rnd() * 0.20;
  const d2 = dark.map((v) => v * tint);
  const l2 = light.map((v) => v * tint);
  for (let i = 0; i < 3; i++) {
    const a = (i / 3) * Math.PI * 2 + rnd() * 1.2;
    const out = w * (0.10 + rnd() * 0.14);
    const sh = h * (0.45 + rnd() * 0.30);
    // Rooted below grade like the thicket's stems, so a clump on a slope sits.
    addStem(buf, x, groundY - 0.08, z,
      x + Math.cos(a) * out, groundY + sh, z + Math.sin(a) * out,
      0.014 + rnd() * 0.010, 0.008, bark, 4, 0.06, 0.42, conf);
  }
  // A knee-high clump is nearly all lit shell — there is no deep interior for
  // the thicket's low shade values to describe — so the lit fraction sits high,
  // or the bush renders as a shadow blob against the sward (it did).
  const pr = w * 0.42;
  addPuff(buf, x, groundY + h - pr * 0.55, z, pr, 0.80, d2, l2,
    0.62 + rnd() * 0.28, 0.30, rnd, conf);
  for (let i = 0; i < 2; i++) {
    const a = rnd() * Math.PI * 2;
    addPuff(buf, x + Math.cos(a) * w * 0.22, groundY + h * 0.55,
      z + Math.sin(a) * w * 0.22, pr * 0.82, 0.78, d2, l2,
      0.46 + rnd() * 0.30, 0.26, rnd, conf);
  }
  return h;
}

/**
 * One tree, written into `buf` at (x, groundY, z). The forms differ where the
 * sources say they differ: a bur oak is not a gallery elm with a wider crown,
 * it is a short bole under heavy horizontal limbs holding a wide flat crown —
 * the dossier's "signature of the 1835 Chicago horizon" — and it carries fire
 * scarring on the lower bole because the surveyors kept noting burned trees.
 */
function addTree(buf, spec, x, groundY, z, rnd, scale = 1) {
  buf.leafFamily = leafFamily(spec);
  if (spec.form === 'thicket') return addThicket(buf, spec, x, groundY, z, rnd, scale);
  if (spec.form === 'shrub') return addShrubClump(buf, spec, x, groundY, z, rnd, scale);
  const conf = spec.conf ?? 0.5;
  const h = lerp(spec.h[0], spec.h[1], rnd()) * scale;
  const dbh = lerp(spec.dbh[0], spec.dbh[1], rnd()) * scale;
  // Crown diameter: the zone record's `width_m` when it carries one, because
  // that is the evidenced figure; the archetype ratio only when it does not.
  const spread = spec.crownW
    ? lerp(spec.crownW[0], spec.crownW[1], rnd()) * scale
    : h * spec.spreadK * (0.86 + rnd() * 0.30);
  const boleH = Math.max(0.4, h * spec.boleK);
  const crownBase = groundY + boleH * 0.72;
  const crownTop = groundY + h;
  const crownH = Math.max(0.6, crownTop - crownBase);

  const dark = linear(spec.dark);
  const light = linear(spec.light);
  // Bark takes the same appearance -> reflectance scaling as the foliage (see
  // CANOPY_ALBEDO), at its own value: a bole stands UNDER its own crown, so
  // almost none of it is ever in direct sun, but bark is a lighter material
  // than a shaded leaf mass and must not go to a silhouette.
  const bark = barkColour(spec.bark);
  // A second bark tone, for the one species whose record singles its bark out:
  // the sycamore's upper limbs are the pale half of "white mottled bark
  // flashing on the upper limbs", and the trunk under them is not. The tree was
  // already drawn as three colours' worth of wood — lower bole, upper bole,
  // limbs — so carrying the pale tone is a value, not a mesh. A species that
  // does not declare one is unchanged: `barkUpper` falls back to `bark`.
  // docs/LIBERTIES.md L118 owns the invention; ROADMAP K47.
  const barkUpper = spec.barkUpper != null
    ? barkColour(spec.barkUpper)
    : bark;
  // Fire-scarred boles: blackened to 1–2 m on 20–40 % of trees in the savanna.
  const scarred = spec.fireScar && rnd() < 0.32;
  const bole = scarred ? [bark[0] * 0.34, bark[1] * 0.32, bark[2] * 0.30] : bark;

  // A per-tree tint, so no two crowns are exactly the same green.
  const tint = 0.90 + rnd() * 0.20;
  const d2 = [dark[0] * tint, dark[1] * tint, dark[2] * tint];
  const l2 = [light[0] * tint, light[1] * tint, light[2] * tint];

  const leanA = rnd() * Math.PI * 2;
  const leanR = (spec.lean ?? 0) * (0.4 + rnd() * 0.6);
  const topX = x + Math.cos(leanA) * leanR * boleH;
  const topZ = z + Math.sin(leanA) * leanR * boleH;

  {
    const r0 = dbh * 0.62;
    const midY = groundY + boleH * 0.55;
    addStem(buf, x, groundY - 0.15, z,
      x + (topX - x) * 0.55, midY, z + (topZ - z) * 0.55,
      r0, r0 * 0.66, bole, buf.detail === 'full' ? 8 : 5, 0, 0.10, conf);
    addStem(buf, x + (topX - x) * 0.55, midY, z + (topZ - z) * 0.55,
      topX, groundY + boleH, topZ,
      r0 * 0.66, r0 * 0.46, barkUpper, buf.detail === 'full' ? 8 : 5, 0.10, 0.22, conf);
  }

  // Where the foliage masses sit. `open` spreads them wide and low, `gallery`
  // stacks them, `lean` throws them out over the water, `columnar` files them up
  // the leader.
  //
  // THE COLUMNAR LADDER IS NEW WITH T-0117 AND IT REDRAWS THREE SPECIES, not
  // one. `columnar` was carried by `FORM_OF` and by the dune's aspen and balsam
  // poplar from the day this file learned the dune, and it drew through the
  // `else` branch above — a SCATTER: `hy` anywhere in 0.14–0.98, the offset up
  // to 0.36 of the crown. On a crown as wide as it is tall that reads as a tree.
  // On a Lombardy poplar it cannot: the record's own crown is 1.4–2.4 m on a
  // 12–18 m stem, an aspect near 8:1, and masses thrown at random heights up
  // fourteen metres of leader are separate blobs on a stick with daylight
  // between them — the same "you can see straight through the stand" failure
  // the limbs above were added to fix, one tree in. Shot rather than argued:
  // even on the even ladder, at ten masses the notches showed from thirty
  // metres, which is why the archetype above asks for fourteen.
  //
  // So a columnar crown is built the way the tree grows: the masses are FILED
  // EVENLY from the base of the crown to the tip, close to the axis, and each
  // one is drawn at half the crown's width so consecutive masses touch. The
  // even ladder is what makes a spire rather than a stack, and it is right for
  // all three species that declare the form — an aspen and a balsam poplar
  // carry their foliage up a narrow leader too; they were being drawn as small
  // round trees because nothing had ever asked the form to mean anything.
  // Triangle cost is UNCHANGED: same puff count, same primitives, different
  // positions and radii.
  const puffs = spec.puffs;
  const columnar = spec.form === 'columnar';
  const centres = [];
  for (let i = 0; i < puffs; i++) {
    const a = (i / puffs) * Math.PI * 2 + rnd() * 1.4;
    let rad;
    let hy;
    if (spec.form === 'open') {
      rad = (i === 0 ? 0.14 : 0.30 + rnd() * 0.24) * spread;
      hy = i === 0 ? 0.62 : 0.18 + rnd() * 0.62;
    } else if (columnar) {
      // Off-axis by a tenth of the crown at most: the jitter is there so the
      // silhouette is not a cylinder, not so the masses wander off the leader.
      rad = (0.04 + rnd() * 0.10) * spread;
      // The ladder. `i/(puffs-1)` spans base to tip exactly; the jitter is a
      // third of one rung, so the file stays a file. The last mass is pulled in
      // to 0.97 so the tip closes over it rather than sitting proud of it.
      const rung = puffs > 1 ? i / (puffs - 1) : 0.5;
      hy = clamp01(rung * 0.97 + (rnd() - 0.5) * (0.66 / Math.max(1, puffs - 1)));
    } else {
      rad = (i === 0 ? 0.10 : 0.14 + rnd() * 0.22) * spread;
      hy = i === 0 ? 0.34 : 0.14 + rnd() * 0.84;
    }
    centres.push([
      topX + Math.cos(a) * rad,
      crownBase + crownH * hy,
      topZ + Math.sin(a) * rad,
      hy,
    ]);
  }

  // Limbs — the wood that carries the foliage.
  //
  // Round 1 gated this whole block on `form === 'open'`, so 91 % of the near
  // timber drew no limbs at all: crowns hung as plates in clear sky over a bare
  // pole, and daylight ran straight through the stand. That is the "colonnade"
  // the round-1 critique measured, and it is a drawing error rather than an
  // ecological one — every one of these species carries its crown on wood.
  {
    const r0 = dbh * 0.62;
    const openForm = spec.form === 'open';
    // An open-grown oak forks LOW into a few heavy, near-horizontal limbs — the
    // dossier's "signature of the 1835 Chicago horizon". A crowded gallery tree
    // is the other shape: it sheds a lighter limb at intervals up the whole
    // bole. Drawing both the same way is what made every species read alike.
    const stride = openForm ? 2 : 1;
    for (let i = openForm ? 1 : 0; i < centres.length; i += stride) {
      const c = centres[i];
      const fork = openForm ? 0.94 : lerp(0.58, 1.0, c[3]);
      const fx = x + (topX - x) * fork;
      const fz = z + (topZ - z) * fork;
      const fy = groundY + boleH * fork;
      // Stop the limb INSIDE the puff, so no tip pokes out of the foliage.
      const tip = openForm ? 0.82 : 0.76;
      const ex = lerp(fx, c[0], tip), ez = lerp(fz, c[2], tip);
      const ey = lerp(fy, c[1], tip) - crownH * (openForm ? 0.12 : 0.04);
      const mx = lerp(fx, ex, 0.52), mz = lerp(fz, ez, 0.52);
      const my = lerp(fy, ey, openForm ? 0.27 : 0.43);
      const rb = r0 * (openForm ? 0.44 : 0.30);
      // Two tapered segments create the rising elbow of a living branch. The
      // 3-sided tips are subpixel; broad boles retain smooth circular normals.
      addStem(buf, fx, fy, fz, mx, my, mz, rb, rb * 0.60,
        barkUpper, 3, 0.20, 0.31, conf);
      addStem(buf, mx, my, mz, ex, ey, ez, rb * 0.60, rb * 0.19,
        barkUpper, 3, 0.31, 0.48, conf);
      if (buf.detail === 'full') {
        const dx = c[0] - fx, dz = c[2] - fz;
        for (const sign of [-1, 1]) {
          addStem(buf, mx, my, mz, ex + dz * sign * 0.24,
            ey + crownH * 0.11, ez - dx * sign * 0.24,
            rb * 0.28, rb * 0.035, barkUpper, 3, 0.30, 0.64, conf);
        }
      }
    }
  }

  for (const c of centres) {
    // The masses have to OVERLAP into one crown. Drawn small against a wide
    // scatter they read as a loose cloud of separate blobs with daylight
    // between them, which at town-edge range is the same "you can see straight
    // through the stand" failure the bare trunks were.
    //
    // A COLUMNAR MASS IS DRAWN AT HALF THE CROWN'S WIDTH, not a quarter, and
    // taller than it is wide. The quarter-width figure is calibrated for a
    // crown carrying five masses scattered through a volume as wide as it is
    // deep, where four of them overlap any line of sight. A file of masses up a
    // single leader has no such redundancy: each one is on its own, so it has to
    // reach the crown's own edge or the record's stated width is not what gets
    // drawn. `squash` above 1 is the same argument on the other axis — a mass on
    // a spire is an ellipsoid standing up, and the flattened dome that suits a
    // spreading crown leaves gaps between the rungs of the ladder. T-0117.
    // `puffScale` (T-2473) shrinks every mass of a crown at once, for a crown
    // only part-leafed; no 1835 record carries it, so the timber is unchanged.
    const rad = spread * (spec.form === 'open' ? 0.255 : columnar ? 0.50 : 0.245)
      * (0.72 + rnd() * 0.58) * (spec.puffScale ?? 1);
    const squash = spec.form === 'open' ? 0.58 : columnar ? 1.06 : 0.78;
    const flexBase = 0.42 + 0.44 * c[3];
    addPuff(buf, c[0], c[1], c[2], rad, squash, d2, l2, c[3], flexBase, rnd, conf);
  }

  // The flower, if the record carries one and July allows it. Drawn LAST so it
  // sits over the foliage it is carried on rather than being buried by a puff
  // added after it. Cutouts write depth normally; no transparent sorting is
  // needed within the merged buffer.
  //
  // Placement is on the outer SHELL: the record's `height_frac` picks the band
  // up the crown and `band` gives it depth, then each head is thrown out to
  // 0.72–1.0 of the crown radius at that height. A cluster at the centre of a
  // canopy is inside 12 m of leaves and is drawn for nobody.
  if (spec.head) {
    const head = spec.head;
    const n = Math.max(HEADS_MIN,
      Math.min(HEADS_MAX, Math.round(spread * head.perM)));
    const stretch = head.kind === 'catkin' ? 2.1 : 1.0;
    const colour = linear(head.rgb);
    // The crown radius at a given height, as an ellipsoid: widest at mid-crown,
    // closing at the cap. Without this the heads at `height_frac` 0.9 stand out
    // in clear air a metre off the foliage.
    const shellR = (t) => (spread * 0.5) * Math.sqrt(Math.max(0.08, 1 - Math.pow(2 * t - 1, 2)));
    for (let i = 0; i < n; i++) {
      const t = clamp01(head.frac - head.band * rnd());
      const a = (i / n) * Math.PI * 2 + rnd() * 1.1;
      const rr = shellR(t) * (0.72 + rnd() * 0.28);
      const hy = crownBase + crownH * t;
      const rad = lerp(head.size[0], head.size[1], rnd()) * 0.5;
      // Same self-shadowing law the foliage gets: high in the crown is lit,
      // low is interior. `t` is already that fraction.
      addHead(buf, topX + Math.cos(a) * rr, hy - (stretch > 1 ? rad * 1.4 : 0),
        topZ + Math.sin(a) * rr,
        rad, stretch, colour, Math.pow(clamp01(t), 1.5),
        0.42 + 0.44 * t, rnd, conf);
    }
    buf.heads += n;
  }
  return h;
}

/* -------------------------------------------------------------------------- */
/* the module                                                                  */
/* -------------------------------------------------------------------------- */

/**
 * @param {object} o
 * @param {URL} [o.dataBase]        where data/ lives (unused until the zone records land)
 * @param {object} o.terrain        what createTerrain() returned
 * @param {Array<{id:string, pts:number[][]}>} [o.footprints]
 * @param {object} [o.confidence]   the confidence view — every material goes through it
 * @param {string[]} [o.problems]   the shared collector
 * @param {boolean} [o.lowSpec]     true on touch/mobile: fewer stems, coarser band
 */
export async function createTrees({
  dataBase, terrain, footprints = [], growthBlocked = () => false,
  confidence = null, problems = [], lowSpec = false, detail = 'full',
  pixelsPerRadian = null, streetRecords = [], zoneAt = null, checkpoint = () => null, onProgress = () => {},
  sceneId = null,
} = {}) {
  const group = new THREE.Group();
  group.name = 'trees';
  // Placement stations are lightweight test observability: the release smoke
  // checks each against the authoritative water mask AND against the water
  // surface itself, which is stronger than a screenshot and cheaper than
  // reverse-engineering roots out of merged meshes. Each carries the ground
  // height the stem was actually built at, so the check is on the number the
  // renderer used rather than on one the test re-derives.
  group.userData.stations = [];

  const hf = terrain?.heightfield;
  const stats = {
    trees: 0, thickets: 0, drawCalls: 0, triangles: 0,
    // T-0223. How many cells of the 120 m lattice ended up carrying timber, so
    // a gate can ask what the batch was actually asked to cull rather than
    // re-deriving it from the cell size.
    timberChunks: 0,
    communities: {}, species: {},
    horizonBodies: 0, horizonBins: 0, timberedBearingFraction: 0,
    horizonDrawnFraction: 0, horizonPxPerRad: 0,
    omitted: OMITTED_TIMBER.map((o) => ({
      ...o, elevation_deg: apparentTopDeg(o.canopy_m, o.distance_m, 1.68) + horizonDipDeg(1.68),
    })),
    // T-0091. Stems a planting record placed itself, kept apart from `trees`
    // and from `species` on purpose: those two are the DEALT population the
    // census gates read against each community's recorded weights, and a tree
    // somebody kept in a yard answers to no density at all.
    planted: 0, plantedStems: [],
    zoneRecords: [], unimplementedForms: [], speciesFromRecord: 0,
    /** T-1056. Stems the dune's recorded woody band refused, so the count is
     *  reportable rather than a difference somebody has to notice. */
    rejectedBelowWoodyBand: 0,
    rejectedOutsideDuneReach: 0,
    /** T-2768: the sand-hill scrub's own tally. */
    sandHills: { offered: 0, reachFade: 0, belowBand: 0, planted: 0, swale: 0 },
    /** T-2807: the woods' edge thicket and the savanna hazel. */
    edgeThicket: { offered: 0, planted: 0, savanna: 0 },
    /** T-2810: the river woods' dead wood and the vines on their edge trees. */
    deadWood: { snags: 0, logs: 0, logsRefused: 0, grape: 0, creeper: 0, vinesRefused: 0 },
    /** T-2784: the open plain's shrubs, slough-edge clumps and lone trees. */
    prairie: { dry: 0, wet: 0, wettest: 0, lone: 0, shaded: 0, species: {},
      /** Where a few of each stand, spread along the sweep, for a shot or a check. */
      samples: { dry: [], wet: [], lone: [] } },
    sandWood: { offered: 0, planted: 0, mesic: 0 },
    paths: { lines: {}, cleared: 0, shrubs: 0 },
    /** T-2807: stems the clump field set in an opening, grown young. */
    youngInOpenings: 0,
    rejectedBelowWaterline: 0, lowestStationY: null,
    // ROADMAP K45(c). `headSpecies` is which records carry a July
    // inflorescence this file draws; `headStems` is how many stems actually
    // got one, which is the number that says whether the flower is IN the
    // scene rather than merely implemented.
    headSpecies: [], headStems: 0, heads: 0, headStations: [],
    // ROADMAP K48. The DRAWN population, per community and per list: what each
    // species' weight asks for against how many stems it actually got. K47
    // found a species that is recorded, weighted, banded, gated — and absent
    // from the frame, because nothing had ever counted what was drawn.
    draws: [],
  };

  if (!hf?.loaded) {
    problems.push('trees: no heightfield, so no bank, no ridge and no division to '
      + 'place woody vegetation from — nothing planted');
    return { group, update() {}, stats, dispose() {} };
  }

  /* ---- 0. the ecology, from the dataset ---------------------------------- */

  // Missing or unparseable records draw NOTHING. There is no fallback community
  // here on purpose: AGENTS.md rule 2 is that a gap is recorded, never filled,
  // and a renderer that plants a forest when the dataset failed to load is
  // asserting an ecology nobody wrote down.
  let records;
  try {
    if (!dataBase) throw new Error('no dataBase');
    records = await loadTimberZones(dataBase, problems, sceneId);
  } catch (err) {
    problems.push(`trees: the flora zone records did not load (${err.message}) — `
      + 'no woody vegetation placed');
    return { group, update() {}, stats, dispose() {} };
  }
  // ROADMAP K45(b2). Read after the zones and before anything is placed: the
  // planter now sweeps the whole modelled field, so the east end of the timber
  // is a question that gets asked at every cell rather than never.
  const eastLimit = timberEastLimits(streetRecords, problems);
  stats.eastLimits = eastLimit.streets;
  // T-2808: the wood on the sand east of State, wherever the north limit is
  // the State Street line (read off the 1835 streets, or T-2745's landform for
  // 1812); a fallback line has no sand wood.
  const sandWood = eastLimit.streets.north ? SAND_WOOD : null;
  // T-2808: the two ways through the North Side wood, on their street lines.
  const pathLines = [];
  for (const p of PATHS) {
    const pts = (streetRecords ?? []).find((s) => s.id === p.street)?.path_local_enu_m;
    if (!Array.isArray(pts) || pts.length < 2) continue;
    const a = pts.reduce((m, q) => (q[1] < m[1] ? q : m));
    const b = pts.reduce((m, q) => (q[1] > m[1] ? q : m));
    const k = (b[0] - a[0]) / Math.max(1e-6, b[1] - a[1]);
    const fromN = p.fromN === 'end' ? b[1] : p.fromN;
    const toN = p.toN ?? Infinity;
    pathLines.push({ ...p, fromN, toN, eAt: (n) => a[0] + (n - a[1]) * k });
    stats.paths.lines[p.id] = { street: p.street, fromN: Math.round(fromN), clearM: p.clearM };
  }
  /**
   * The path whose bare tread (e, n) is on, or null; with `trunks`, the wider
   * strip no tree stands in, so the edge trees' crowns leave the cut open.
   */
  const pathCutAt = (e, n, trunks = false) => {
    for (const l of pathLines) {
      if (n < l.fromN || n > l.toN) continue;
      if (Math.abs(e - l.eAt(n)) < (trunks ? l.treeClearM : l.clearM)) return l;
    }
    return null;
  };
  /** T-2808: where the sand wood ends in the east at northing n, wobbling. */
  const sandWoodEndE = (n) => SAND_WOOD.toE + (noise2(SAND_WOOD.toE, n, 120, 83) - 0.5) * SAND_WOOD.wobbleM;
  /** Distance from (e, n) to the path `id`'s line, Infinity off its reach. */
  const pathDist = (id, e, n) => {
    const l = pathLines.find((q) => q.id === id);
    return l && n >= l.fromN && n <= l.toN ? Math.abs(e - l.eAt(n)) : Infinity;
  };

  stats.zoneRecords = records.zonesRead;
  stats.unimplementedForms = records.unimplemented;
  stats.speciesFromRecord = Object.keys(records.specs).length;
  stats.headSpecies = records.heads;

  /** The render spec per species: the record's ecology over this file's forms. */
  const specs = {};
  for (const [id, base] of Object.entries(SPECIES)) {
    specs[id] = { ...base, conf: 0.5, crownW: null };
  }
  Object.assign(specs, records.specs);

  /**
   * The specs a NAMED community plants with (ROADMAP K45(b) change one).
   *
   * `specs` above is keyed by species id and the first zone to name a species
   * wins it, which is right for every community that shares its trees with the
   * gallery and wrong for exactly one: the dune, whose cottonwood is the same
   * binomial as the gallery's and a different tree. A community may therefore
   * name the zone its own species come from, and gets that zone's records laid
   * over the shared table. Every other community reads the shared table
   * unchanged, so nothing outside the dune is redealt by this.
   */
  const communitySpecs = {};
  for (const [key, c] of Object.entries(COMMUNITIES)) {
    if (!c.specsFrom) { communitySpecs[key] = specs; continue; }
    const own = records.byZone?.[c.specsFrom];
    if (!own) {
      problems.push(`trees: the community ${key} plants with ${c.specsFrom}'s own species `
        + 'parameters and that zone contributed none — its stems would be drawn as '
        + 'another zone\'s tree');
      communitySpecs[key] = specs;
      continue;
    }
    communitySpecs[key] = { ...specs, ...own };
  }

  /**
   * The community mixes, weighted as they are written (ROADMAP K46).
   *
   * The record's band is the CONSTRAINT and not the value: a weight outside
   * every band its own community's `zones` record is an ecological claim no
   * source carries, so it must be declared in that community's `departures` or
   * this raises. `problems` is what the repo smoke reads to decide whether the
   * data loaded, which is the right severity — an undeclared departure means
   * the file and the dataset disagree and nothing says which is meant.
   */
  const mixes = {};
  for (const [key, c] of Object.entries(COMMUNITIES)) {
    const cited = c.zones ?? [];
    if (!cited.length) {
      problems.push(`trees: the community ${key} names no zones, so nothing constrains `
        + 'the weights it plants by');
    }
    const w = (list, listName) => list.filter(([id]) => specs[id]).map(([id, weight]) => {
      const seen = cited.map((z) => records.bands[z]?.[id]).filter(Boolean);
      const declared = c.departures?.[`${listName}.${id}`];
      if (!seen.length) {
        problems.push(`trees: ${key}.${listName}.${id} is weighted ${weight} and no zone `
          + `this community cites (${cited.join(', ')}) records a density for it`);
      } else if (!seen.some(([lo, hi]) => weight >= lo && weight <= hi)) {
        if (!declared) {
          problems.push(`trees: ${key}.${listName}.${id} is weighted ${weight}, outside `
            + `every band its own community's zones record (${seen
              .map(([lo, hi]) => `${lo}–${hi}`).join(', ')}) — declare it in `
            + `${key}.departures with the reason, or move it inside the band`);
        }
      } else if (declared) {
        // Exact the other way too. A departure that has been repaired leaves a
        // note behind claiming the file disagrees with the dataset when it no
        // longer does, and a stale declaration is how a gate stops meaning
        // anything.
        problems.push(`trees: ${key}.departures declares ${listName}.${id}, and its weight `
          + `${weight} is inside a band its own zones record — drop the declaration in the `
          + 'commit that brought it back inside');
      }
      return [id, weight];
    });
    mixes[key] = {
      mix: w(c.mix, 'mix'),
      edgeMix: c.edgeMix ? w(c.edgeMix, 'edgeMix') : null,
      swaleMix: c.swaleMix ? w(c.swaleMix, 'swaleMix') : null,
    };
  }

  /* ---- 1. read the ground ------------------------------------------------ */

  const { cols, rows, cellM, originE, originN, data } = hf;
  const cells = cols * rows;

  // The water surface, read from the epoch's own heightfield record rather than
  // restated here: `water_surface_m` is what generators/terrain_gen.py wrote and
  // what the internal datum means. A renderer carrying its own copy of the datum
  // is how the two drift apart.
  const waterY = Number.isFinite(hf.meta?.water_surface_m) ? hf.meta.water_surface_m : 0;
  const dryFloorY = waterY + TREE_DRY_MARGIN_M;
  /**
   * The one question every stem must answer YES to. Sampled at the exact planting
   * point with the same bilinear sampler that supplies `groundY`, not at the
   * nearest cell centre: a 2.5 m cell is wider than a bank, so a nearest-cell
   * test can pass on the land side of a boundary the tree is then planted on the
   * water side of.
   */
  const standsDry = (e, n) => terrain.surfaceHeight(e, n) >= dryFloorY;

  // Distance from every cell to the nearest water, by two-pass chamfer. This is
  // the field the whole gallery depends on: ZONE 5 is defined as a band along
  // the bank, not as a polygon someone drew.
  const dw = new Float32Array(cells);
  const D1 = cellM;
  const D2 = cellM * Math.SQRT2;
  for (let r = 0; r < rows; r++) {
    const pause = checkpoint(); if (pause) await pause;
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      dw[i] = terrain.isWater(originE + c * cellM, originN + r * cellM) ? 0 : 1e9;
    }
  }
  for (let r = 0; r < rows; r++) {
    const pause = checkpoint(); if (pause) await pause;
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      let v = dw[i];
      if (c > 0) v = Math.min(v, dw[i - 1] + D1);
      if (r > 0) v = Math.min(v, dw[i - cols] + D1);
      if (c > 0 && r > 0) v = Math.min(v, dw[i - cols - 1] + D2);
      if (c < cols - 1 && r > 0) v = Math.min(v, dw[i - cols + 1] + D2);
      dw[i] = v;
    }
  }
  for (let r = rows - 1; r >= 0; r--) {
    const pause = checkpoint(); if (pause) await pause;
    for (let c = cols - 1; c >= 0; c--) {
      const i = r * cols + c;
      let v = dw[i];
      if (c < cols - 1) v = Math.min(v, dw[i + 1] + D1);
      if (r < rows - 1) v = Math.min(v, dw[i + cols] + D1);
      if (c < cols - 1 && r < rows - 1) v = Math.min(v, dw[i + cols + 1] + D2);
      if (c > 0 && r < rows - 1) v = Math.min(v, dw[i + cols - 1] + D2);
      dw[i] = v;
    }
  }

  // The three land divisions, as connected components of land separated by the
  // navigable channels. Nobody draws a polygon: the river already divides the
  // box the way 1835 Chicago was divided, and the documented shallow slough on
  // the north side is above CHANNEL_Y so it does not cut the North Division.
  //
  // ...AND IT DIVIDES ONLY THE GROUND THE RIVER IS TRACED ACROSS. The sentence
  // above is true exactly as far south as the South Branch is traced, and no
  // further. Below its last traced row there is no channel in the field, so the
  // land wraps underneath the branch and the West and South Divisions come back
  // as ONE component — measured on the T-0464 box: 4 components, WEST=1,
  // NORTH=3, SOUTH=1. The three-way test below then fails and NOTHING is
  // planted anywhere, including the town, which is how a box that reaches
  // Twenty-Second Street emptied the whole scene of trees.
  //
  // That is not a fault in the flood. Below the evidence limit the corpus says
  // nothing about this ground — terrain_spec.json's `evidence_limit` is the
  // line, every vertex under it is written CONF_CONJECTURAL, and "which bank is
  // this point on" has no answer there because there is no bank. So the flood
  // stops at that line: above it the divisions separate exactly as they always
  // did, below it no cell is labelled and nothing plants on ground nobody
  // described. The line is read from the heightfield's own runtime meta rather
  // than written here, so it cannot drift from the spec that sets it.
  // THE FLOOR IS FOUND, NOT DECLARED, and every declared line that was tried
  // for it was wrong. The spec's `evidence_limit` (N -2149.4, Twelfth Street) is
  // a SURVEY line and sits ~20 m south of where the traced water actually stops,
  // so a flood bounded there still joins the banks: WEST=1 NORTH=3 SOUTH=1,
  // measured. A cheaper proxy — "the southernmost row holding water with land
  // on both sides" — answers N -2140 where the flood itself answers -2130,
  // because enclosed water elsewhere in the box satisfies it without dividing
  // anything. Neither is the question; the question is where THIS flood stops
  // separating these three probes, so it is asked directly.
  //
  // Binary search over the cut row: the predicate is monotone in the direction
  // that matters — cutting further north can only remove connections, never add
  // one — so ~11 floods settle a 1 969-row field. Each is the same typed-array
  // pass that runs below.
  let divideFloorRow = 0;
  // One stack for every flood: it is scratch, and a fresh one per flood was
  // ~8 MB a time, a dozen times over, while the phone was mid-load (T-2158).
  const st = new Int32Array(cells);
  const floodSeparates = (cutRow) => {
    const d = new Int8Array(cells).fill(-1);
    let lab = 0;
    for (let s = cutRow * cols; s < cells; s++) {
      if (data[s] < CHANNEL_Y || d[s] >= 0) continue;
      let sp = 0; st[sp++] = s; d[s] = lab;
      while (sp > 0) {
        const j = st[--sp];
        const c = j % cols;
        const r = (j - c) / cols;
        if (c > 0 && d[j - 1] < 0 && data[j - 1] >= CHANNEL_Y) { d[j - 1] = lab; st[sp++] = j - 1; }
        if (c < cols - 1 && d[j + 1] < 0 && data[j + 1] >= CHANNEL_Y) { d[j + 1] = lab; st[sp++] = j + 1; }
        if (r > cutRow && d[j - cols] < 0 && data[j - cols] >= CHANNEL_Y) { d[j - cols] = lab; st[sp++] = j - cols; }
        if (r < rows - 1 && d[j + cols] < 0 && data[j + cols] >= CHANNEL_Y) { d[j + cols] = lab; st[sp++] = j + cols; }
      }
      lab++;
    }
    const pick = (e, n) => {
      const c = Math.round((e - originE) / cellM);
      const r = Math.round((n - originN) / cellM);
      if (c < 0 || r < cutRow || c >= cols || r >= rows) return -1;
      return d[r * cols + c];
    };
    const w = pick(-300, 0), nn = pick(200, 250), s2 = pick(200, -250);
    return w >= 0 && nn >= 0 && s2 >= 0 && w !== nn && nn !== s2 && w !== s2 ? d : null;
  };
  {
    let lo = 0, hi = rows - 1;
    if (!floodSeparates(0)) {
      while (lo < hi) {
        const pause = checkpoint(); if (pause) await pause;
        const mid = (lo + hi) >> 1;
        if (floodSeparates(mid)) hi = mid; else lo = mid + 1;
      }
      divideFloorRow = lo;
    }
  }
  const divisible = (s) => ((s - (s % cols)) / cols) >= divideFloorRow;
  const div = new Int8Array(cells).fill(-1);
  const stack = new Int32Array(cells);
  let labels = 0;
  for (let s = 0; s < cells; s++) {
    if (data[s] < CHANNEL_Y || div[s] >= 0 || !divisible(s)) continue;
    let sp = 0;
    stack[sp++] = s;
    div[s] = labels;
    while (sp > 0) {
      const j = stack[--sp];
      const c = j % cols;
      const r = (j - c) / cols;
      // `divisible` is tested on every neighbour and not only on the seed. Row 0
      // is the SOUTH edge, so `j - cols` walks south: a component seeded north of
      // the evidence limit would otherwise flood straight under it, rejoin the
      // far bank below the traced river, and put West and South back into one
      // label — the exact fault the limit is here to prevent, reintroduced by
      // the one step that was not guarded.
      if (c > 0 && div[j - 1] < 0 && data[j - 1] >= CHANNEL_Y && divisible(j - 1)) { div[j - 1] = labels; stack[sp++] = j - 1; }
      if (c < cols - 1 && div[j + 1] < 0 && data[j + 1] >= CHANNEL_Y && divisible(j + 1)) { div[j + 1] = labels; stack[sp++] = j + 1; }
      if (r > 0 && div[j - cols] < 0 && data[j - cols] >= CHANNEL_Y && divisible(j - cols)) { div[j - cols] = labels; stack[sp++] = j - cols; }
      if (r < rows - 1 && div[j + cols] < 0 && data[j + cols] >= CHANNEL_Y && divisible(j + cols)) { div[j + cols] = labels; stack[sp++] = j + cols; }
    }
    labels++;
  }
  const cellAt = (e, n) => {
    const c = Math.round((e - originE) / cellM);
    const r = Math.round((n - originN) / cellM);
    if (c < 0 || r < 0 || c >= cols || r >= rows) return -1;
    return r * cols + c;
  };
  const WEST = div[cellAt(-300, 0)];
  const NORTH = div[cellAt(200, 250)];
  const SOUTH = div[cellAt(200, -250)];
  if (WEST < 0 || NORTH < 0 || SOUTH < 0 || WEST === NORTH || NORTH === SOUTH || WEST === SOUTH) {
    problems.push('trees: the heightfield no longer divides into the West, North and '
      + 'South Divisions, so which bank a point is on cannot be answered — nothing planted');
    return { group, update() {}, stats, dispose() {} };
  }

  /* ---- 2. where a tree may stand ---------------------------------------- */

  // Nothing grows through a building, and the blocks around one are being
  // cleared: ZONE 10 puts relict trees at 8–25/ha in the riverside blocks against
  // 30–80/ha in the untouched belt, so the town reads as timber being taken.
  const fps = footprints.map((f) => {
    let e = 0;
    let n = 0;
    for (const p of f.pts) { e += p[0]; n += p[1]; }
    return { id: f.id ?? null, pts: f.pts, e: e / f.pts.length, n: n / f.pts.length };
  });
  const CLEAR_MARGIN = 4.5;
  // `insideId` names the one footprint a stem may stand in (T-2809): the fort's
  // company garden is a committed footprint, its fence's, and a planting record
  // that says its stems stand IN that garden is asking past that one polygon
  // and no other.
  function blocked(e, n, insideId = null) {
    if (growthBlocked(e, n)) return true;
    for (const f of fps) {
      if (insideId !== null && f.id === insideId) continue;
      if (Math.abs(e - f.e) > 60 || Math.abs(n - f.n) > 60) continue;
      const pts = f.pts;
      let inside = false;
      for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
        const [xi, yi] = pts[i];
        const [xj, yj] = pts[j];
        if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) inside = !inside;
        if (segDist2(e, n, xi, yi, xj, yj) < CLEAR_MARGIN * CLEAR_MARGIN) return true;
      }
      if (inside) return true;
    }
    return false;
  }
  // T-2809 — A PLOT A PLANTING RECORD CLEARS. Dr. Harmon's orchard stands in
  // the sand hills' ground, and a cedar the dealer drops among his rows is a
  // tree nobody would have left inside a fenced orchard. Asked only by the
  // position-seeded dealers (sand hills, edge thicket, sand wood), never by the
  // shared-stream sweep, so no stem outside a plot moves.
  const clearedPlots = (records.plantings ?? []).map((r) => r.clears_local_enu_m).filter(Boolean);
  const inClearedPlot = (e, n) => clearedPlots.some((p) =>
    e >= p.west_e && e <= p.east_e && n <= p.north_n && n >= p.south_n);
  function clearedFactor(e, n) {
    // The factor only rises with distance, so the nearest building decides it:
    // the same value as taking the least over every building, without boxing
    // a number per building per sample — about 4 GB of garbage over a load
    // (T-2158).
    let nearest = Infinity;
    for (const p of fps) {
      const d = Math.hypot(e - p.e, n - p.n);
      if (d < nearest) nearest = d;
    }
    return nearest === Infinity ? 1 : Math.min(1, lerp(0.20, 1, smoothstep(50, 135, nearest)));
  }

  /**
   * Which community stands at (e, n), or null for ground that carries no woody
   * plant at all — which is most of the box, and is the point.
   */
  function communityAt(e, n) {
    const i = cellAt(e, n);
    if (i < 0) return null;
    const y = data[i];
    if (terrain.isWater(e, n)) return null;      // authoritative traced water mask
    if (!standsDry(e, n)) return null;           // and not on the waterline either

    // THE OPEN DUNE (ROADMAP K45(b) change one), asked BEFORE the divisions and
    // their east limits, because it is a different claim from all of them. Those
    // limits are where the river TIMBER ends — Andreas's belt stops at Wells
    // Street and his North Division timber excepts "the sandy hills near the
    // lake". The sandy hills are not an absence of vegetation; they are the
    // lakeshore's own community, and ZONE 8 records three poplars standing on
    // it. Where that ground is is the sward's answer and not this file's: see
    // DUNE_ZONE. No sward, no dune.
    if (zoneAt?.(e, n) === DUNE_ZONE) return 'dune';

    const d = div[i];
    if (d === WEST) return null;                // Andreas: open prairie, entirely

    // THE EAST END OF THE TIMBER (ROADMAP K45(b2)). Before this parcel the
    // planting loop's own square answered this by accident at E +316; now the
    // loop sweeps the field and the answer has to come from the source. Andreas
    // gives the South Division a street — the belt runs "east as far as Wells
    // Street" — and the North Division an exception, "the sandy hills near the
    // lake", which `z09_sand_prairie` places from the State Street break-of-
    // slope east. Both are read from `data/streets/1835.json` at load; see
    // TIMBER_EAST_LIMIT_STREETS. Ground east of the limit carries no woody
    // community in this build: the open-dune poplars that belong on the sand are
    // recorded, archetyped and not yet placed (ROADMAP K45(b) change one).
    // T-2768: the "sandy hills near the lake" are not an absence of woody
    // growth either. Wau-Bun's cedars, pines and dwarf willows stand on them
    // north of the river and Clarke's low cedars south of Twelfth Street;
    // `plantSandHill` holds each reach to its own belt behind the shore.
    // T-2808: north of `fromN` the North Side wood runs on east of State over
    // the sand, to short of the shore's sand hills (SAND_WOOD).
    if (sandWood && d === NORTH && e > eastLimit.north && e < sandWoodEndE(n)) {
      const t = smoothstep(sandWood.fromN - sandWood.fadeN, sandWood.fromN, n);
      if (t >= 1 || (t > 0 && noise2(e, n, 8, 47) < t)) return 'sand_wood';
    }
    const pastTimber = e > (d === NORTH ? eastLimit.north : eastLimit.south);
    if (pastTimber && zoneAt?.(e, n) === SAND_PRAIRIE_ZONE) return 'sand_hill_inland';
    if (e > (d === NORTH ? eastLimit.north : eastLimit.south)) return null;

    const bank = dw[i];

    // ZONE 5: an irregular gallery 30–120 m wide. The width wanders rather than
    // being a constant offset, because a gallery forest follows the floodplain
    // and floodplains are not parallel to the channel. The low half of the
    // documented range is used: this is the reach where the town was taking
    // timber, and a belt that reaches its 120 m maximum everywhere would put a
    // wall of trees across the "free and boundless prospect of open prairie"
    // Andreas describes from the south.
    const width = lerp(30, 74, noise2(e, n, 130, 11));
    if (bank <= width) return bank <= 16 ? 'gallery_edge' : 'gallery';

    // Behind the gallery: the West Division is out, and the South Division is
    // "low and marshy ground" with "a free and boundless prospect of open
    // prairie" beyond it — so only the North Division carries a body of timber.
    if (d !== NORTH) return null;

    // The ZONE 6 mosaic — "build as four sub-patches, not one texture", with
    // more than 30 % of the area at savanna density. A generated field lays it
    // out, nudged by what relief the heightfield has (the natural levee crest
    // against the backswamp behind it). It has very little: the whole North
    // Division sits inside 11 cm of itself, so the terrain cannot answer this
    // question, and a generated pattern that says so is better than a
    // terrain-derived one that pretends.
    const relief = clamp01((y - 1.02) / 0.16);
    const f = noise2(e, n, 96, 27) + (relief - 0.5) * 0.30;
    if (f > 0.66) return 'ridge_oak';
    if (f < 0.34) return 'mesic_pocket';
    return 'wet_woods';
  }

  /* ---- 3. plant ---------------------------------------------------------- */

  const rnd = mulberry32(18350701);
  /**
   * THE NEAR TIMBER IS CHUNKED ON A 120 m LATTICE, and until T-0223 it was
   * chunked into FOUR WORLD QUADRANTS — which is a partition, but not one any
   * camera can cull against.
   *
   * The near wood spans 1,760 m east-west and 800 m north-south. Split at the
   * datum origin, each of the four pieces was most of a kilometre across, so its
   * bounding sphere touched every frustum the scene has: the colour camera drew
   * all four whole from any stand, and the sun's ±240 m box — `DETAIL.shadowReachM`,
   * ±60 m when the comment below was written and ±240 since T-0115 — took all four
   * whole as well. T-0223 measured what that cost at the release smoke's worst
   * stand (Lake Street at Canal, east): `trees` drew **360,926 triangles out of
   * the 181,900 the layer owns** — the whole layer twice — and **180,100 of it
   * was the sun's pass over timber standing outside the box**, casting nothing
   * any pixel of the shadow map could hold. 14.4 % of the entire frame.
   *
   * 120 m is the lattice because it is the coarsest cell that still lets the
   * ±240 m box reject most of the wood: a chunk enters the shadow pass when its
   * bounding sphere touches the box, so the wasted margin is about one chunk
   * radius all round.
   *
   * WHY THIS DOES NOT COST 70 DRAW CALLS — see the `BatchedMesh` below. Fine
   * chunks are only affordable because the whole lattice is submitted as ONE
   * multi-draw, culled per chunk by three itself, in both passes.
   */
  const CHUNK_M = 120;
  const buffers = new Map();
  const chunkOf = (e, n) => {
    const k = `${Math.floor(e / CHUNK_M)},${Math.floor(n / CHUNK_M)}`;
    let b = buffers.get(k);
    if (!b) { b = new MeshBuf(level); buffers.set(k, b); }
    return b;
  };
  /**
   * T-2743 — A TREE IS GROWN ONCE PER SPECIES AND STOOD AS AN INSTANCE. Every
   * tree-form stem goes to `grown` (tree-instances.js), which draws it from its
   * species' grown model; thickets, dooryard shrubs and the stems carrying a
   * July head stay on the chunked path above. `grown` takes no draw from `rnd`:
   * a grown stem's height, turn and variant come from its own position, so what
   * stands after it does not move when a tree's shape changes.
   */
  const plant = (spec, e, gy, n, r, scale = 1) => {
    if (isGrownForm(spec)) return grown.add(spec, e, gy, worldZ(n), scale);
    addTree(chunkOf(e, n), spec, e, gy, worldZ(n), r, scale);
    return null;
  };

  // Scene detail sets how many stems are drawn and how coarsely the ground is
  // sampled for them. It does NOT touch the species mix, the zone rules or the
  // waterline margin: fewer of the same trees in the same places, never a
  // different wood. `lowSpec` is the device guess; an explicit choice outranks it.
  const level = lowSpec && detail === 'full' ? 'light' : detail;
  const grown = new TreeInstances({ level, cull: true });
  /**
   * The stem budget, scaled to the ground the loop now sweeps (ROADMAP K45(b2)).
   *
   * These were 820/520/300 trees and 420/270/170 thickets, set when the planter
   * swept 52,163 of the field's dry nodes. It now sweeps all 192,844 of them —
   * 3.70× the ground — and 300 is a number the widened wood REACHES: measured on
   * this build, `light` planted exactly 300 trees, which is the cap truncating
   * the sweep rather than a count. That truncation is not a thinning: the loop
   * runs south to north, so a bound cap deletes the north end of the wood and
   * leaves a straight edge across the town. Every figure below is its old value
   * × 3.70, rounded, which keeps the budget the backstop it was written as.
   *
   * A cap that binds is now a REPORTED problem rather than a silent cut — see
   * the check after the planting loop. That is the assertion this parcel owes:
   * the reason the truncation could arrive unannounced is that nothing said so.
   *
   * FOUND ON THE WAY by K45(b2), and REPAIRED HERE (ROADMAP K45(b3)): the caps
   * had never bound at all, so `light`, `balanced` and `full` planted the same
   * wood in slightly different places. `step` is count-neutral by construction —
   * the acceptance roll is `perHa * step² / 10000`, so halving the cell area
   * doubles the number of cells and halves each one's chance — which means the
   * timber's detail control WAS the caps, and the caps did nothing. `keep` below
   * is the control the level actually needs, and the caps stay the backstop
   * K45(b2) made them.
   */

  /**
   * `keep` — THE DETAIL CONTROL, AND IT IS A THINNING RATHER THAN A CAP.
   *
   * ROADMAP K45(b3), RE-CUT BY T-1127 FOR THE FIELD T-1123 ENLARGED. A fraction
   * on the acceptance roll thins the wood UNIFORMLY:
   * every cell of the swept field is offered the same reduced chance, so a phone
   * gets the same wood at a lower density — same species, same mix, same rules
   * about where a stem may stand, fewer stems everywhere. A cap cannot do that.
   * The loop runs south to north, so a cap that binds stops the planting partway
   * and leaves a straight edge across the town: the same number of stems, and
   * three quarters of a wood rather than a whole thinner one.
   *
   * WHERE THE RATIO COMES FROM, because it is a choice and not a source.
   * It is the levels' OWN triangle ceilings in `main.js`, read as a ratio. That
   * is the only live per-level statement this renderer makes about how much
   * geometry a level is for, and the release smoke holds each level to it
   * (`BUDGET.triangles` follows the tier the visitor is on). K45(b3) read them
   * as 1,000,000 / 800,000 / 600,000 = 1 / 0.8 / 0.6; the ceilings have since
   * moved to **1,460,000 / 1,280,000 / 825,000**, so the ratio is refreshed here
   * to **1 / 0.877 / 0.565**. The obvious alternative, the ratio of the
   * pre-K45(b2) caps (820/520/300 = 1 / 0.634 / 0.366), is still NOT used: those
   * were a backstop that never bound, so they are an intent nothing ever
   * executed, and K45(b2) then multiplied them by 3.70. A number that has never
   * had an effect is not evidence of what a level should draw — and a backstop
   * that has STARTED to bind is a defect (below), not a promotion to a control.
   *
   * WHERE THE SCALE COMES FROM, which is what T-1127 changed. The ratio says how
   * the levels stand to each other; one factor says how thin the whole wood is.
   * Until T-1123 that factor was 1 and nothing bound. T-1123 carried the modelled
   * ground north into Kinzie's Addition, which is Andreas's "body of thrifty
   * heavy growth of timber" and takes the TOP of ZONE 5's range, and the wood the
   * record asks for grew with it. MEASURED on this tree, 2026-09-15, with the
   * caps lifted so the loop could finish: the field wants **4,052** stems at
   * `full`'s step, 3,981 at `balanced`'s and 3,970 at `light`'s — one wood
   * counted three ways, which is `step` count-neutrality doing what it says. The
   * caps are 3,030 / 1,920 / 1,110, so at 1 / 0.8 / 0.6 ALL THREE bound and all
   * three woods stopped partway north: the planted maxima were N +949.8 /
   * +803.3 / +722.6 m against a field that runs to N +1,117.8 m.
   *
   * The scale is therefore set by the level with the least room — `light`, whose
   * cap is the smallest fraction of the wood — at 80 % of that cap, which leaves
   * the backstop a fifth of headroom rather than a rounding error:
   *
   *     lambda = (1,110 x 0.80) / (3,970 x 0.565) = 0.396  ->  0.400
   *
   * and the three fractions are `lambda` times the ceiling ratio. They plant a
   * measured 1,621 / 1,393 / 893 stems against caps of 3,030 / 1,920 / 1,110, and
   * every level reaches the north end of the field.
   *
   * `light` IS NO LONGER ON THIS RULE, and that is a trim and not a refresh
   * (T-1976, 2026-10-02). The floor had grown back over its own 825,000 and is
   * won back by trimming, never by raising (AGENTS.md). The furniture and ground
   * reaches in `main.js` carried most of it, and left the forks 4,921 triangles
   * clear on desktop; dropping `light`'s keep from 0.225 to 0.191 gives 14,352
   * more there, which is what puts the floor's headroom back over the absolute
   * 16,806 T-0672 recorded for the rungs above it. (Re-running the rule against
   * T-1975's ceilings would NOT have produced this: lambda is pinned to
   * `light`'s own cap, so it rises as the ratio falls and `light` lands on 0.224
   * again.) Same species, same zones, same places — about 15 % fewer stems at
   * this level only. `full` and `balanced` are untouched.
   *
   * This is a RENDERING density, not a claim about the town: `perHa`, the mixes,
   * `edgeFade`, `clearedFactor`, the waterline gate and the east limits are
   * untouched, and the record's own stand is what the roll would accept at
   * `keep = 1`. What changed at T-1127 is that `full` is no longer that stand —
   * it is 40 % of it — because the enlarged field's wood does not fit the
   * geometry any level of this renderer is for. Recorded in docs/LIBERTIES.md.
   *
   * T-2766 RAISES ALL THREE, because the instrument L238 asked for now exists.
   * Since T-2743 every tree-form stem is an instance of a grown species tree at
   * three levels, so a far stem costs a few crossed cards rather than a whole
   * crown, and 1835's trees at the town_backyard stand fell from 994k triangles
   * to 418k. That saving is spent on the wood the sources describe ("all wooded"
   * north of the river): 0.700 / 0.500 / 0.300. `balanced` is held below the
   * ratio rule because the West prairie stand was 5k under its 2,535,000 on dev
   * and 0.600 put it 15k over; the caps are raised so the backstop still has
   * about a fifth of headroom at each level.
   *
   * T-2768 raises the caps again, and only the caps: the sand hills' cedars
   * and pines are dealt by the same roll and the same `keep`, about 700 more
   * stems at `full`, which the T-2766 cap of 3800 would have cut off partway
   * north. The keep fractions do not move.
   */
  /*
   * T-2784 adds `prairie`, the backstop on the open plain's shrubs and lone
   * trees (PRAIRIE_WOODY), which deal from their own rolls and never count
   * against `trees` or `shrubs`. Set at about a fifth over what each level
   * plants in 1812, which has the most open ground.
   */
  const STEMS = {
    full:     { step: 4.0, keep: 0.700, trees: 4700, thickets: 1550, shrubs: 3000, prairie: 14000 },
    balanced: { step: 4.7, keep: 0.500, trees: 3800, thickets: 1000, shrubs: 2200, prairie: 9000 },
    light:    { step: 5.6, keep: 0.300, trees: 2100, thickets: 630, shrubs: 1300, prairie: 3600 },
  };
  const stems = STEMS[level] ?? STEMS.full;
  const step = stems.step;
  const cellArea = step * step;
  // T-3106: 1812 has more uncleared ground than 1835. Its Light and Full
  // sweeps reached their unchanged 2100/4700-tree backstops and lost the wood's
  // north end. Thin the existing acceptance rolls everywhere in these tiers
  // by a further 25%, before any stem is chosen; caps, source densities and
  // stated plantings remain unchanged. Balanced and other scenes retain keep.
  const keep = stems.keep * (String(sceneId) === '1812'
    && (level === 'light' || level === 'full') ? 0.75 : 1);
  const maxTrees = stems.trees;
  const maxThickets = stems.thickets;
  const maxShrubs = stems.shrubs;
  const maxPrairie = stems.prairie;
  stats.keep = keep;

  /**
   * THE POINT-BAR SCREEN'S OWN ROLL, AND WHY IT DOES NOT TAKE `keep`.
   *
   * ROADMAP K45(b3), measured rather than reasoned. The sandbar-willow branch
   * rolls a FIXED per-cell chance, so unlike the tree roll it is not count-
   * neutral in `step`: a coarser grid visits fewer bar cells and accepts the
   * same fraction of each, and the screen thins with the sampling step. Measured
   * on the published mirror before this parcel: 258 stools at `full`, 190 at
   * `balanced`, 133 at `light` — 52 % of the screen gone on the level phones
   * start at, as a side effect of a grid spacing, which nothing had ever said.
   *
   * That is the one population here that must NOT thin. A sandbar willow thicket
   * is a screen and a screen needs its clumps to touch; the branch's own comment
   * records that halving them left them standing as separate cushions on open
   * sand. So the roll now scales with the cell it is offered — a bigger cell
   * stands for more ground and takes a proportionally bigger chance — and `keep`
   * is deliberately not applied to it.
   *
   * IT SATURATES, AND THE RESIDUAL IS STATED RATHER THAN HIDDEN. A probability
   * cannot exceed 1, and at 0.84 in a 4 m cell both coarser steps clamp — so the
   * screen recovers to every bar cell the grid offers and no further. The bar is
   * a 6–9 m strip, so at a 5.6 m step there are simply fewer points on it than
   * the screen wants stools. `light` therefore still carries a thinner screen
   * than `full`; it is thinner because of what a coarse grid can resolve, which
   * is honest, rather than because of an unstated 0.84.
   */
  const THICKET_ACCEPT = Math.min(1, 0.84 * (cellArea / 16));
  stats.thicketAccept = THICKET_ACCEPT;

  /**
   * WHICH SPECIES STANDS AT THIS STEM — drawn against its own running deficit.
   *
   * ROADMAP K48. The weights in `COMMUNITIES` are SHARES of the stand: `perHa`
   * decides how many stems a hectare of this community holds and the mix
   * decides what they are, so a species' expected count is `share × stems`.
   * Until 2026-08-16 every stem was an INDEPENDENT draw on that share, and an
   * independent draw loses the rare end of a distribution. The American
   * sycamore is 2 of the gallery's 116 over 115 gallery stems — 1.98 expected —
   * and the seeded shuffle dealt NONE. That is a 13.5 % outcome on independent
   * draws, and because this scene is seeded it was not bad luck that would come
   * out next time: it was permanent. Three more species stood as a single stem,
   * so the sycamore was the tail of a distribution rather than a special case.
   *
   * So the draw is corrected against what it already owes. Each species carries
   * `share × drawn − placed`, its shortfall at this stem, and the draw is made
   * proportional to that shortfall instead of to the share — except that a
   * species already owed a WHOLE stem takes the next one outright. Two bounds
   * follow by construction, and they are what the smoke asserts:
   *
   *   - **Nothing overshoots by a stem.** `placed` only ever increments while
   *     `placed < share × drawn`, so no species can end up more than one stem
   *     above what its own weight asks for.
   *   - **Nothing owed a whole stem gets none.** The moment a shortfall reaches
   *     one stem the next stem is that species'.
   *
   * Stress-tested over 35,880 (mix, stand size, seed) cases on the four
   * communities and the edge list, at stand sizes 4 to 900: worst overshoot
   * 0.99 stems, worst shortfall 1.21, and not one species owed a whole stem
   * standing nowhere. Without the outright rule the worst shortfall is 2.32 and
   * 17 of those cases lose a species that the stand owed a stem to.
   *
   * It stays a DRAW. Which species stands at any one stem is still random
   * except where a shortfall has reached a stem (22 % of them), so a stand does
   * not come out combed the way a strict rotation over a raster scan order
   * would.
   *
   * THE WHOLE WOOD IS RE-DEALT, and saying otherwise would be the easy lie
   * here. This consumes exactly the one `rnd()` per stem the independent draw
   * consumed, at the same point in the same stream — but `addTree` draws a
   * tree's own bole, taper and puffs from that same stream and takes a
   * different NUMBER of draws per species, so changing which species stands at
   * one stem shifts every draw after it. Measured on the published mirror at
   * both viewports: 163 stems became 178 and 214 thicket stools became 213.
   * Nothing that decides HOW MANY stems a hectare holds changed — `perHa`,
   * `edgeFade`, `clearedFactor` and the waterline gate are untouched — so that
   * is the same Bernoulli placement re-dealt, not a denser wood.
   *
   * Nothing about WHERE a stem stands changes. This consumes exactly the one
   * `rnd()` per stem the independent draw consumed, at the same point in the
   * same stream, so the positions, the thickets, the shapes and every other
   * consumer of that stream are untouched. What changes is which tree you are
   * standing under.
   *
   * It also does not touch a weight, a density or a band — see K48's box for
   * why neither of the two repairs that DO can be built.
   */
  const pickerFor = (community, list, mix) => {
    const n = mix.length;
    const census = { community, list, stems: 0, species: [] };
    stats.draws.push(census);
    if (!n) return () => null;
    let total = 0;
    for (const m of mix) total += m[1];
    const share = mix.map((m) => (total > 0 ? m[1] / total : 1 / n));
    const placed = new Array(n).fill(0);
    const owed = new Array(n).fill(0);
    let drawn = 0;
    census.species = mix.map(([id, weight], i) => ({
      id, weight, share: share[i], expected: 0, drawn: 0,
    }));
    return (r) => {
      drawn++;
      let sum = 0;
      let most = 0;
      for (let i = 0; i < n; i++) {
        owed[i] = Math.max(0, share[i] * drawn - placed[i]);
        sum += owed[i];
        if (owed[i] > owed[most]) most = i;
      }
      // The raw shortfalls sum to exactly one stem — `drawn` of expectation
      // against `drawn - 1` placed — so `sum` is only ever zero if every
      // species has overshot, which the bound above forbids. The fallback, and
      // the outright rule, are both the hungriest species rather than the last
      // one written.
      let k = most;
      if (owed[most] < 1 && sum > 0) {
        const t = r * sum;
        let acc = 0;
        for (let i = 0; i < n; i++) { acc += owed[i]; if (t < acc) { k = i; break; } }
      }
      placed[k]++;
      census.stems = drawn;
      for (let i = 0; i < n; i++) {
        census.species[i].expected = share[i] * drawn;
        census.species[i].drawn = placed[i];
      }
      return mix[k][0];
    };
  };

  const pickers = {};
  for (const [key, m] of Object.entries(mixes)) {
    pickers[key] = {
      mix: pickerFor(key, 'mix', m.mix),
      edgeMix: m.edgeMix ? pickerFor(key, 'edgeMix', m.edgeMix) : null,
      swaleMix: m.swaleMix ? pickerFor(key, 'swaleMix', m.swaleMix) : null,
    };
  }
  const bump = (obj, key) => { obj[key] = (obj[key] ?? 0) + 1; };

  /**
   * ENU north -> three's world z, and it is a named function because leaving it
   * implicit is what put the trees in the river.
   *
   * ROADMAP R-BUG5b. Every question this planter asks is asked in local ENU
   * metres — `terrain.isWater(e, n)`, `communityAt(e, n)`, `surfaceHeight(e, n)`,
   * `cellAt(e, n)`, `blocked(e, n)`, `noteStation(e, n, y)`. `addTree` takes a
   * three WORLD z, and `enuToWorld` in terrain.js is `(e, y, -n)`: the two axes
   * point OPPOSITE ways. Until 2026-08-16 the loop handed its ENU north
   * straight to `addTree`, so every tree in the wood was TESTED at (px, pz) and
   * DRAWN at (px, -pz) — the whole near-field wood mirrored across the datum's
   * east-west line through the forks.
   *
   * That is the owner's screenshot, and it is why three green gates disagreed
   * with his window. `wetTreeStations`, `drownedTreeStations` and
   * `tools/measure_far_timber.py` all walk `stations`, which records the point
   * that was TESTED — so they were describing a wood that was never drawn. 391
   * stations, 0 of them wet; 64 of the same 391 wet at their mirror, and 10,734
   * vertices of drawn timber standing up to 48 m from the nearest dry ground.
   * `flora.js` had it right all along (`_m.setPosition(e, y, -n2)`), which is
   * why the sward was never in the channel and the wood always was.
   *
   * The gate that holds it is `no drawn timber stands away from its own
   * station` in the smoke: it reads the merged geometry back and asks whether
   * the wood on the screen is the wood the station list describes. A test of
   * the placement alone cannot see this class of fault and never could.
   */
  const worldZ = (n) => -n;

  /** Record a planted stem for the smoke suite, with the height it stands at. */
  const noteStation = (e, n, y) => {
    group.userData.stations.push({ e, n, y });
    if (stats.lowestStationY === null || y < stats.lowestStationY) stats.lowestStationY = y;
  };

  /**
   * THE SWEPT DOMAIN — the modelled field, not a square inside it.
   *
   * ROADMAP K45(b2). This was `const half = 320 - step`, a square left over from
   * the 640 m heightfield the scene began as; S2e carried the field to
   * E −320..+1700, N −400..+400 and the square never moved, so 140,681 of the
   * 192,844 heightfield nodes standing above the planter's own dry floor —
   * 87.9 ha, 73 % of the walkable ground — had never had a stem offered to them,
   * while `flora.js`'s sward lattice follows the visitor over all of it. The
   * bounds are the heightfield's own, inset by one planting step so a stem's
   * jitter cannot land outside the field it was sampled from.
   *
   * The loop is O(cells) and the field is about four times the square, so this
   * is the cost this parcel had to measure rather than assume — it is in the
   * ROADMAP box and in `stats`. What may GROW on the ground newly reached is
   * `communityAt`'s answer, not this loop's: see TIMBER_EAST_LIMIT_STREETS.
   */
  /**
   * T-2768 — one offered point on the sand hills: which reach it is in, whether
   * the woody band and the clump field let a stem stand, and which species.
   * Every draw is from a generator seeded by the point itself, so planting the
   * sand hills moves no other stem in the scene. Returns true when the point
   * belonged to a sand-hill reach (planted or not).
   */
  /** T-2768 — the shore's easting per heightfield row: the easternmost cell of
   *  the row standing a metre above the water, read once. */
  const shoreRow = new Float32Array(rows).fill(NaN);
  for (let j = 0; j < rows; j++) {
    for (let i = cols - 1; i >= 0; i--) {
      if (data[j * cols + i] > waterY + 1.0) { shoreRow[j] = originE + i * cellM; break; }
    }
  }
  const shoreE = (n) => {
    const j = Math.round((n - originN) / cellM);
    const v = j >= 0 && j < rows ? shoreRow[j] : NaN;
    return Number.isNaN(v) ? null : v;
  };
  const sandHillReach = (n) => {
    for (const key of SAND_HILLS) {
      const c = COMMUNITIES[key];
      const [n0, n1] = c.reachN;
      const f = c.reachFadeM ?? 0;
      const r = smoothstep(n0 - f, n0, n) * (1 - smoothstep(n1, n1 + f, n));
      if (r > 0) return { key, c, r };
    }
    return null;
  };
  const plantSandHill = (px, pz, gy, w, inland = false) => {
    const hit = sandHillReach(pz);
    if (!hit) return false;
    const { key, c, r } = hit;
    if (inland) {
      // Inland of the lakeshore band only within the reach's belt behind the
      // shore, and (north) east of the Kinzie house.
      if (!c.inlandBeltM) return true;
      const shore = shoreE(pz);
      if (shore == null || px < shore - c.inlandBeltM) return true;
      if (c.inlandFromE != null && px < c.inlandFromE) return true;
    }
    stats.sandHills.offered++;
    const hr = mulberry32(Math.floor(hash2(Math.round(px * 8), Math.round(pz * 8)) * 4294967296) ^ 0x2768);
    if (r < 1 && hr() >= r) { stats.sandHills.reachFade++; return true; }
    // The woody band, exactly as the dune's: nothing woody on ground the lake reworks.
    const band = w?.establishes_m;
    if (band) {
      const t = smoothstep(band[0], band[1], gy);
      if (t <= 0 || (t < 1 && noise2(px, pz, 8, 41) >= t)) { stats.sandHills.belowBand++; return true; }
    }
    // A hollow: the point stands 0.12 m or more below the mean of a ring 9 m out.
    let ring = 0;
    for (let k = 0; k < 6; k++) {
      const a = (k / 6) * Math.PI * 2;
      ring += terrain.surfaceHeight(px + Math.cos(a) * 9, pz + Math.sin(a) * 9);
    }
    const swale = c.swaleMix && gy < ring / 6 - 0.12;
    // The clump field: mean one, so the record's density is kept and its pattern
    // is thickets and openings.
    const clump = 2 * smoothstep(0.30, 0.78, noise2(px, pz, c.clumpM ?? 24, 61));
    const perHa = lerp(c.perHa[0], c.perHa[1], noise2(px, pz, 58, 7)) * clump * clearedFactor(px, pz);
    if (hr() > (perHa * cellArea * keep) / 10000) return true;
    if (stats.trees >= maxTrees || blocked(px, pz) || inClearedPlot(px, pz)) return true;
    const p = pickers[key];
    const id = (swale ? p.swaleMix : p.mix)(hr());
    const spec = communitySpecs[key][id];
    if (!spec) return true;
    plant(spec, px, gy, pz, hr);
    noteStation(px, pz, gy);
    stats.trees++;
    stats.sandHills.planted++;
    if (swale) stats.sandHills.swale++;
    bump(stats.communities, key);
    bump(stats.species, id);
    return true;
  };

  /** T-2807 — the edge thicket's shrubs: the zone records' own, grown. */
  const edgeSpecs = {};
  for (const [id, zone] of Object.entries(EDGE_THICKET.zones)) {
    const rec = records.shrubByZone?.[zone]?.[id];
    if (!rec) {
      problems.push(`trees: the woods' edge thicket plants ${id} from ${zone} and that record `
        + 'did not load — the thicket is drawn without it');
      continue;
    }
    // `form` 'edge_shrub' is a grown form (tree-instances.js isGrownForm): the
    // record's shrub drawn as a clump of stems from tree-model.js's ARCH, not
    // as the dooryard planting's three-puff clump.
    edgeSpecs[id] = { ...rec, form: 'edge_shrub', bark: EDGE_THICKET.bark[id] ?? rec.bark };
  }
  const edgePick = {
    mix: pickerFor('edge_thicket', 'mix', EDGE_THICKET.mix.filter(([id]) => edgeSpecs[id])),
    savanna: pickerFor('edge_thicket', 'savannaMix',
      EDGE_THICKET.savannaMix.filter(([id]) => edgeSpecs[id])),
  };
  /**
   * T-2807. Offer a woods cell to the edge thicket before the tree roll: true
   * when a shrub took the cell. `key` is the community, `d` the division,
   * `bank` the distance to water. Deals from its own position-seeded generator,
   * as the sand hills do.
   */
  const plantEdgeThicket = (px, pz, gy, key, d, bank) => {
    const t = EDGE_THICKET;
    let band = 0;
    if (key === 'gallery' && d !== NORTH) {
      const width = lerp(30, 74, noise2(px, pz, 130, 11));
      band = smoothstep(t.galleryBand[0], t.galleryBand[1], bank / width);
    } else if (d === NORTH && key !== 'gallery') {
      // T-2808: on the sand east of State the wood's own east end is the edge.
      const endE = sandWood && px > eastLimit.north ? sandWoodEndE(pz) : eastLimit.north;
      const inside = endE - px;
      band = 1 - smoothstep(t.eastBandM[0], t.eastBandM[1], inside);
    }
    const savanna = key === 'ridge_oak' && band <= 0;
    if (band <= 0 && !savanna) return false;
    stats.edgeThicket.offered++;
    const hr = mulberry32(Math.floor(hash2(Math.round(px * 8), Math.round(pz * 8)) * 4294967296) ^ 0x2807);
    const range = savanna ? t.savannaPerHa : t.perHa;
    // Thickets with gaps between, on the same mean-one clump field as the sand hills.
    const clump = savanna ? 1 : 2 * smoothstep(0.30, 0.78, noise2(px, pz, t.clumpM, 67));
    const cleared = clearedFactor(px, pz);
    const perHa = lerp(range[0], range[1], noise2(px, pz, 58, 9)) * (savanna ? 1 : band)
      * clump * cleared * cleared;
    if (hr() > (perHa * cellArea * keep) / 10000) return false;
    if (stats.edgeThicket.planted >= maxShrubs || blocked(px, pz) || inClearedPlot(px, pz)) return false;
    const id = (savanna ? edgePick.savanna : edgePick.mix)(hr());
    const spec = edgeSpecs[id];
    if (!spec) return false;
    plant(spec, px, gy, pz, hr, 0.85 + hr() * 0.30);
    noteStation(px, pz, gy);
    stats.edgeThicket.planted++;
    if (savanna) stats.edgeThicket.savanna++;
    bump(stats.species, id);
    return true;
  };

  /**
   * T-2808. The shrubs at a path's margins (PATHS `shrubM`: the bridle path's
   * crowding shrubs, the road cut's sprouts), from the edge thicket's mix and
   * their own position-seeded generator. True when a shrub took the cell.
   */
  const plantPathShrub = (px, pz, gy) => {
    for (const l of pathLines) {
      if (pz < l.fromN || pz > l.toN) continue;
      const dist = Math.abs(px - l.eAt(pz));
      if (dist < l.shrubM[0] || dist >= l.shrubM[1]) continue;
      const hr = mulberry32(Math.floor(hash2(Math.round(px * 8), Math.round(pz * 8)) * 4294967296) ^ 0x28080);
      const clump = 2 * smoothstep(0.30, 0.78, noise2(px, pz, EDGE_THICKET.clumpM, 67));
      const perHa = lerp(l.shrubPerHa[0], l.shrubPerHa[1], noise2(px, pz, 58, 9)) * clump
        * clearedFactor(px, pz);
      if (hr() > (perHa * cellArea * keep) / 10000) return false;
      if (stats.edgeThicket.planted >= maxShrubs || blocked(px, pz) || inClearedPlot(px, pz)) return false;
      const id = edgePick.mix(hr());
      const spec = edgeSpecs[id];
      if (!spec) return false;
      plant(spec, px, gy, pz, hr, 0.80 + hr() * 0.30);
      noteStation(px, pz, gy);
      stats.edgeThicket.planted++;
      stats.paths.shrubs++;
      bump(stats.species, id);
      return true;
    }
    return false;
  };
  /**
   * T-2808. A cell of the wood on the sand east of State (SAND_WOOD): the Rush
   * Street path's tread and margins first, then the edge thicket and the
   * savanna hazel, then a tree. Its own position-seeded generator throughout.
   */
  const closeBandOf = (id) => PATHS.find((p) => p.id === id)?.closeBandM ?? 0;
  const plantSandWood = (px, pz, gy) => {
    stats.sandWood.offered++;
    if (pathCutAt(px, pz)) { stats.paths.cleared++; return; }
    if (plantPathShrub(px, pz, gy)) return;
    const near = pathDist('rush_bridle_path', px, pz) < closeBandOf('rush_bridle_path');
    const key = near ? 'mesic_pocket' : 'ridge_oak';
    if (plantEdgeThicket(px, pz, gy, key, NORTH, Infinity)) return;
    if (pathCutAt(px, pz, true)) return;
    const c = COMMUNITIES[key];
    const wc = WOOD_CLUMP[key];
    const hr = mulberry32(Math.floor(hash2(Math.round(px * 8), Math.round(pz * 8)) * 4294967296) ^ 0x2808);
    const ct = smoothstep(0.28, 0.72, noise2(px, pz, wc.cellM, 73));
    // Along the path the boughs met: no openings in the band, the patches' density.
    const clumpK = near ? 1 + 0.6 * ct : wc.floor + (2 - 2 * wc.floor) * ct;
    const perHa = lerp(c.perHa[0], c.perHa[1], noise2(px, pz, 58, 7)) * clearedFactor(px, pz) * clumpK;
    if (hr() > (perHa * cellArea * keep) / 10000) return;
    if (stats.trees >= maxTrees || blocked(px, pz) || inClearedPlot(px, pz)) return;
    const id = pickers[key].mix(hr());
    const spec = communitySpecs[key][id];
    if (!spec) return;
    const young = !near && ct < 0.35 ? lerp(wc.young, 1, ct / 0.35) : 1;
    if (young < 1) stats.youngInOpenings++;
    plant(spec, px, gy, pz, hr, young);
    noteStation(px, pz, gy);
    stats.trees++;
    stats.sandWood.planted++;
    if (key === 'mesic_pocket') stats.sandWood.mesic++;
    bump(stats.communities, key);
    bump(stats.species, id);
  };
  /**
   * T-2808. A stem the shared stream dealt onto a path's bare tread is grown
   * nowhere, but its draws are still taken, so every stem after it stands where
   * it stood: a grown tree takes none, the chunked path's into a buffer that is
   * thrown away.
   */
  let scratchBuf = null;
  const dryPlant = (spec, e, gy, n, scale) => {
    if (isGrownForm(spec)) return;
    scratchBuf = scratchBuf ?? new MeshBuf(level);
    addTree(scratchBuf, spec, e, gy, worldZ(n), rnd, scale);
  };

  /* ---- T-2810: dead wood and vines in the river woods -------------------- */

  /** A generator seeded by where a stem stands, so nothing here takes a draw
   *  from the shared stream and no living stem moves. */
  const seededAt = (px, pz, salt) =>
    mulberry32(Math.floor(hash2(Math.round(px * 8), Math.round(pz * 8)) * 4294967296) ^ salt);
  const deadSpecs = new Map();
  /** The species' own tree, dead: standing (`snag`) or down (`log`). */
  const deadSpecOf = (spec, kind) => {
    const key = `${spec.speciesId}|${kind}`;
    let d = deadSpecs.get(key);
    if (!d) {
      d = { ...spec, dead: kind, head: null, bark: DEAD_WOOD.bark[kind], barkUpper: DEAD_WOOD.bark[kind],
        common: `${spec.common} (dead, ${kind === 'log' ? 'down' : 'standing'})`,
        conf: CONFIDENCE_VALUE[DEAD_WOOD.confidence] };
      deadSpecs.set(key, d);
    }
    return d;
  };
  const vineSpecs = records.vineByZone?.[VINE_EDGE.zone] ?? {};
  /** The way to the nearest water from (px, pz): down the distance field. */
  const towardWater = (px, pz) => {
    const g = cellM * 2;
    const at = (de, dn) => { const j = cellAt(px + de, pz + dn); return j < 0 ? NaN : dw[j]; };
    const we = at(-g, 0) - at(g, 0);
    const wn = at(0, -g) - at(0, g);
    const m = Math.hypot(we, wn);
    return m > 0 ? [we / m, wn / m] : null;
  };
  /**
   * A vine on a gallery tree within VINE_EDGE.edgeM of the water: a grape
   * curtain at its crown's edge on the water side, or a creeper up the north
   * side of its trunk. `hostH` is the height the host was grown to.
   */
  const dressEdgeTree = (px, pz, gy, hostH, bank) => {
    if (!(bank <= VINE_EDGE.edgeM) || !(hostH > 0)) return;
    const vr = seededAt(px, pz, 0x28101);
    const roll = vr();
    const id = roll < VINE_EDGE.grape ? 'vitis_riparia'
      : roll < VINE_EDGE.grape + VINE_EDGE.creeper ? 'parthenocissus_quinquefolia' : null;
    const rec = id && vineSpecs[id];
    if (!rec) return;
    const [r0, r1] = VINE_EDGE.reach[id];
    const vh = Math.min(rec.h[1], hostH * lerp(r0, r1, vr()));
    const habit = VINE_EDGE.habit[id];
    let e = px;
    let n = pz;
    let yaw;
    if (habit === 'curtain') {
      const w = towardWater(px, pz);
      if (!w) { stats.deadWood.vinesRefused++; return; }
      // At the crown's drip line on the water side, and never out past the bank.
      const off = Math.min(hostH * 0.30, Math.max(0, bank - 2));
      e = px + w[0] * off;
      n = pz + w[1] * off;
      // The template's open side is +X; world +X turned by `yaw` about the
      // vertical is (cos, 0, -sin), which is (e, n) = (cos, sin).
      yaw = Math.atan2(w[1], w[0]);
    } else {
      n = pz + 0.45;
      yaw = Math.PI / 2;
    }
    if (terrain.isWater(e, n)) { stats.deadWood.vinesRefused++; return; }
    grown.add({ ...rec, h: [vh, vh], habit, leaf: VINE_EDGE.leaf[id] }, e, gy, worldZ(n), 1, { yaw });
    noteStation(e, n, gy);
    stats.deadWood[id === 'vitis_riparia' ? 'grape' : 'creeper']++;
  };
  /**
   * A fallen trunk of the stem's species, lying a few metres from it. Refused
   * (and counted) where any of its length would lie in water, under the dry
   * floor, on a footprint or a track, in a cleared plot, or across a slope it
   * could not lie flat on.
   */
  const plantLog = (spec, px, pz, dr) => {
    const a = dr() * Math.PI * 2;
    const d = lerp(DEAD_WOOD.logOffsetM[0], DEAD_WOOD.logOffsetM[1], dr());
    const e = px + Math.cos(a) * d;
    const n = pz + Math.sin(a) * d;
    const yaw = dr() * Math.PI * 2;
    // The trunk is grown at the living tree's height `hh` and broken at up to
    // 0.70 of it (tree-model.js deadSkeleton), so its whole length is checked.
    const hh = lerp(spec.h[0], spec.h[1], dr());
    const L = hh * 0.70;
    const pts = [0, 0.5, 1].map((t) => [e + Math.cos(yaw) * L * t, n + Math.sin(yaw) * L * t]);
    const ys = [];
    for (const [qe, qn] of pts) {
      if (terrain.isWater(qe, qn) || !standsDry(qe, qn) || blocked(qe, qn) || inClearedPlot(qe, qn)) {
        stats.deadWood.logsRefused++;
        return;
      }
      ys.push(terrain.surfaceHeight(qe, qn));
    }
    if (Math.max(...ys) - Math.min(...ys) > 1.2) { stats.deadWood.logsRefused++; return; }
    const gy = Math.min(...ys);
    grown.add({ ...deadSpecOf(spec, 'log'), h: [hh, hh] }, e, gy, worldZ(n), 1,
      { yaw, lodK: DEAD_WOOD.logLodK });
    noteStation(pts[1][0], pts[1][1], gy);
    stats.deadWood.logs++;
  };

  /* ---- T-2784: the woody plants of the open plain ------------------------ */

  const PW = PRAIRIE_WOODY;
  const loneIds = new Set(PW.lone.mix.map(([id]) => id));
  /** The records' own species: the shrubs grown as clumps of stems, hanging
   *  their July flower (`bloom`); the lone trees as their zone's tree. */
  const prairieSpecs = {};
  for (const [id, zone] of Object.entries(PW.zones)) {
    const rec = loneIds.has(id) ? records.byZone?.[zone]?.[id] : records.shrubByZone?.[zone]?.[id];
    if (!rec) {
      problems.push(`trees: the open plain's woody plants take ${id} from ${zone} and that record `
        + 'did not load — the plain is drawn without it');
      continue;
    }
    prairieSpecs[id] = loneIds.has(id) ? rec
      : { ...rec, form: 'edge_shrub', bark: PW.bark[id] ?? rec.bark, bloom: rec.flower ?? null };
  }
  const sampleStand = (kind, id, e, n) => {
    const list = stats.prairie.samples[kind];
    const count = kind === 'lone' ? stats.prairie.lone : stats.prairie[kind];
    if (list.length < 16 && count % (kind === 'lone' ? 2 : 97) === 1) {
      list.push({ id, e: Math.round(e * 10) / 10, n: Math.round(n * 10) / 10 });
    }
  };
  /** A weighted pick by one draw, off no shared state, so a stand's species is
   *  its own whatever was dealt before it. */
  const pickOf = (list, r) => {
    let total = 0;
    for (const [id, w] of list) if (prairieSpecs[id]) total += w;
    let a = r * total;
    for (const [id, w] of list) {
      if (!prairieSpecs[id]) continue;
      a -= w;
      if (a < 0) return id;
    }
    return null;
  };
  const prairieKeep = keep * (PW.keepK[level] ?? 1);
  const groundsOk = new Set(PW.grounds);
  // The most either roll can ask for (the clump fields peak at two), so a cell
  // that cannot take a stem is refused on its first draw, before any ground is read.
  const shrubRollMax = ((PW.dry.perHa[1] + PW.wet.perHa[1]) * 2 * cellArea * prairieKeep) / 10000;
  const loneRollMax = (PW.lone.perHa[1] * cellArea * PW.lone.keep) / 10000;
  const fireDirs = PW.lone.fireFrom.map((deg) => {
    const a = (deg * Math.PI) / 180;
    // A bearing clockwise from north, as (e, n): the way TO the fire's side.
    return [Math.sin(a), Math.cos(a)];
  });
  /**
   * The open plain at (e, n), or null: no wood stands there (`communityAt`),
   * nothing blocks it, and the sward's zone is one of `grounds`. `wet` is 1 in
   * the sedge meadow and the marsh and follows the ground's height in the wet
   * prairie (and the river woods' outer reach); the mesic prairie is dry.
   */
  const prairieSite = (e, n) => {
    if (terrain.isWater(e, n)) return null;
    const gy = terrain.surfaceHeight(e, n);
    if (gy < dryFloorY) return null;
    if (communityAt(e, n) !== null) return null;
    const zone = zoneAt?.(e, n) ?? null;
    if (!groundsOk.has(zone)) return null;
    if (blocked(e, n) || inClearedPlot(e, n)) return null;
    const i = cellAt(e, n);
    const bank = i < 0 ? Infinity : dw[i];
    const wet = zone === 'z03_sedge_meadow' || zone === 'z04_marsh' ? 1
      : zone === 'z02_mesic_prairie' ? 0
        : smoothstep(PW.wet.wetY[0], PW.wet.wetY[1], gy);
    const cleared = clearedFactor(e, n);
    return { gy, zone, wet, bank, cleared: cleared * cleared };
  };
  /**
   * How far the fire's shadow reaches here, 0..1: 1 where water lies within
   * `upwindM[0]` upwind on any bearing the fire ran from, fading to 0 at
   * `upwindM[1]`. Asked only of the few cells the lone trees' first roll lets
   * through.
   */
  const fireShadow = (e, n) => {
    const [d0, d1] = PW.lone.upwindM;
    let near = Infinity;
    for (const [de, dn] of fireDirs) {
      for (let d = PW.lone.stepM; d <= d1 && d < near; d += PW.lone.stepM) {
        if (terrain.isWater(e + de * d, n + dn * d)) { near = d; break; }
      }
    }
    return near === Infinity ? 0 : 1 - smoothstep(d0, d1, near);
  };
  /**
   * One cell of the sweep's lattice (e0, n0), offered to the open plain. Its
   * own generators, seeded by the lattice point and never by the shared
   * stream's jitter, so the same ground deals the same stems in 1812 and 1835.
   */
  const plantPrairie = (e0, n0) => {
    if (stats.prairie.dry + stats.prairie.wet + stats.prairie.lone >= maxPrairie) return;
    let site;
    const sr = seededAt(e0, n0, 0x2784);
    const roll = sr();
    if (roll < shrubRollMax) {
      const qe = e0 + (sr() - 0.5) * step * 0.92;
      const qn = n0 + (sr() - 0.5) * step * 0.92;
      const clumpD = 2 * smoothstep(0.30, 0.78, noise2(qe, qn, PW.dry.clumpM, 71));
      const clumpW = 2 * smoothstep(0.30, 0.78, noise2(qe, qn, PW.wet.clumpM, 79));
      const dryN = lerp(PW.dry.perHa[0], PW.dry.perHa[1], noise2(qe, qn, 58, 13)) * clumpD;
      const ci = cellAt(qe, qn);
      const edge = 1 - smoothstep(PW.wet.edgeM[0], PW.wet.edgeM[1], ci < 0 ? Infinity : dw[ci]);
      const wetN = lerp(PW.wet.perHa[0], PW.wet.perHa[1], noise2(qe, qn, 58, 17))
        * (PW.wet.inland + (1 - PW.wet.inland) * edge) * clumpW;
      // The most this point can take whatever its ground (the dry share falls and
      // the wet share rises with `wet`, and `cleared` is at most 1), so the ground
      // and the sward's zone, the dear questions, are asked only of a point whose
      // roll that leaves standing, and the open grass between colonies asks nothing.
      site = roll < ((dryN + wetN) * cellArea * prairieKeep) / 10000 ? prairieSite(qe, qn) : null;
      if (site) {
        const { gy, wet, bank, cleared } = site;
        const dry = dryN * (1 - PW.dry.wetCut * wet);
        const wetD = wetN * wet;
        const p = ((dry + wetD) * cleared * cellArea * prairieKeep) / 10000;
        if (roll < p) {
          // `roll / p` is uniform on [0, 1) here: it chooses the stratum by its share.
          const isWet = roll / p < wetD / (dry + wetD);
          const wettest = isWet && wet >= 0.9 && bank <= PW.wet.wettestEdgeM;
          const id = isWet ? pickOf(wettest ? PW.wet.wettest : PW.wet.mix, sr())
            : pickOf(PW.dry.mix.map(([k, w]) => [k, k === 'rosa_spp' ? w : w * (1 - wet)]), sr());
          const spec = id && prairieSpecs[id];
          if (spec) {
            const small = spec.h[1] <= PW.smallM;
            grown.add(spec, qe, gy, worldZ(qn), 0.85 + sr() * 0.30,
              { lodK: small ? PW.smallLodK : 1 });
            noteStation(qe, qn, gy);
            stats.prairie[wettest ? 'wettest' : isWet ? 'wet' : 'dry']++;
            if (wettest) stats.prairie.wet++;
            bump(stats.prairie.species, id);
            sampleStand(isWet ? 'wet' : 'dry', id, qe, qn);
          }
        }
      }
    }
    // The lone trees, on their own roll.
    const lr = seededAt(e0, n0, 0x27841);
    const lroll = lr();
    if (lroll >= loneRollMax) return;
    const le = e0 + (lr() - 0.5) * step * 0.92;
    const ln = n0 + (lr() - 0.5) * step * 0.92;
    const ls = prairieSite(le, ln);
    if (!ls || ls.wet >= 0.95) return;
    const shade = fireShadow(le, ln);
    if (shade <= 0) return;
    stats.prairie.shaded++;
    const lp = (lerp(PW.lone.perHa[0], PW.lone.perHa[1], noise2(le, ln, 90, 19)) * shade * ls.cleared
      * cellArea * PW.lone.keep) / 10000;
    if (lroll >= lp) return;
    // The bur oak on the drier ground, the cottonwood on the wetter.
    const oak = PW.lone.mix[0][1] * (1 - ls.wet);
    const cot = PW.lone.mix[1][1] * (0.35 + ls.wet);
    const id = lr() * (oak + cot) < oak ? PW.lone.mix[0][0] : PW.lone.mix[1][0];
    const spec = prairieSpecs[id];
    if (!spec) return;
    grown.add(spec, le, ls.gy, worldZ(ln), lerp(PW.lone.scale[0], PW.lone.scale[1], lr()));
    noteStation(le, ln, ls.gy);
    stats.prairie.lone++;
    bump(stats.prairie.species, id);
    sampleStand('lone', id, le, ln);
  };

  const sweepE0 = originE + step;
  const sweepE1 = originE + (cols - 1) * cellM - step;
  const sweepN0 = originN + step;
  const sweepN1 = originN + (rows - 1) * cellM - step;
  stats.sweep = { e: [sweepE0, sweepE1], n: [sweepN0, sweepN1], step };
  const rowsToPlant = Math.floor((sweepN1 - sweepN0) / step) + 1;
  let rowsPlanted = 0;
  onProgress(0, rowsToPlant);
  for (let n = sweepN0; n <= sweepN1; n += step) {
    const pause = checkpoint(); if (pause) await pause;
    for (let e = sweepE0; e <= sweepE1; e += step) {
      // T-2784: the open plain's woody plants, off the shared stream entirely.
      plantPrairie(e, n);
      const px = e + (rnd() - 0.5) * step * 0.92;
      const pz = n + (rnd() - 0.5) * step * 0.92;
      if (terrain.isWater(px, pz)) continue;
      // THE WATERLINE GATE, and it is deliberately the first thing after the
      // river mask and ahead of every ecological question below. `gy` is the
      // height the stem will actually be built at, so testing anything else here
      // — the nearest cell, the community's own idea of the bank — is testing a
      // different point from the one the tree stands on.
      const gy = terrain.surfaceHeight(px, pz);
      if (gy < dryFloorY) { stats.rejectedBelowWaterline++; continue; }
      const comm = communityAt(px, pz);
      if (!comm) continue;
      // T-2768: the sand hills inland of the lakeshore band. Nothing above drew
      // from `rnd` for this point, and `plantSandHill` does not either.
      if (comm === 'sand_hill_inland') {
        plantSandHill(px, pz, gy, records.woody?.[DUNE_ZONE], true);
        continue;
      }
      // T-2808: the wood on the sand east of State, likewise off the stream.
      if (comm === 'sand_wood') {
        plantSandWood(px, pz, gy);
        continue;
      }
      // T-1056 — THE DUNE'S POPLARS STAND ON THE SANDY HILLS, NOT ON THE BAR.
      //
      // `communityAt` answers 'dune' for the whole of z08_lakeshore's box, and
      // measured on the committed e1834_harbor_cut field 1,650 of the 1,653
      // land samples that zone actually WINS are the traced sand bar, none
      // higher than 1.58 m. So every dune cottonwood, aspen and balsam poplar
      // this loop planted stood on a surface the lake reworks — the even
      // scatter of woody growth T-1056 was opened against, the half of it that
      // is this file's rather than flora.js's.
      //
      // The bound is the zone record's `woody_stratum`, read at load and
      // interpolated here exactly as `flora.js` interpolates it for the shrub
      // stratum: below the band nothing woody stands, across it the chance
      // ramps, above it the community is untouched. `noise2` makes the survivors
      // POCKETS rather than an even thinning, on the same 8 m grain the rest of
      // this loop's ecology already uses. No zone without the block moves.
      if (comm === 'dune') {
        const w = records.woody?.[DUNE_ZONE];
        // T-1819 — THE POPLARS KEEP THE REACH THEY HAD. The beach now runs the
        // whole 4.9 km shore, and on the south terrace (2.87 m, above the whole
        // woody band) every metre of it would deal ZONE 8c's 7-31 stems/ha: about
        // seven hundred new trees, which bound `light`'s budget on the first
        // mobile smoke. Whether the back-dune carried poplars the length of the
        // shore is a question about the dune LANDFORM, which T-1820 shapes; until
        // it does, the stratum's `reach_n_m` holds them to the reach the dune had,
        // fading over `reach_fade_m` in pockets rather than along a line.
        const reach = w?.reach_n_m;
        if (Array.isArray(reach)) {
          const fade = w.reach_fade_m ?? 0;
          const r = smoothstep(reach[0] - fade, reach[0], pz)
            * (1 - smoothstep(reach[1], reach[1] + fade, pz));
          if (r <= 0 || (r < 1 && noise2(px, pz, 8, 43) >= r)) {
            // T-2768: beyond the poplars' reach the same sand carries the
            // witnesses' sand-hill scrub. Nothing above this line drew from
            // `rnd` for this point, and `plantSandHill` does not either.
            if (plantSandHill(px, pz, gy, w)) continue;
            stats.rejectedOutsideDuneReach++;
            continue;
          }
        }
        const band = w?.establishes_m;
        if (band && DUNE_WOODY_ROLES.some((r) => (w.applies_to_roles ?? []).includes(r))) {
          const t = smoothstep(band[0], band[1], gy);
          if (t <= 0) { stats.rejectedBelowWoodyBand++; continue; }
          if (t < 1 && noise2(px, pz, 8, 41) >= t) {
            stats.rejectedBelowWoodyBand++;
            continue;
          }
        }
      }

      const i = cellAt(px, pz);
      const y = data[i];
      const bank = dw[i];

      // Sandbar willow: "thickets 2–6 stems/m² on point bars". Point bars are
      // the low, freshly worked ground between the waterline and about half a
      // metre above it — which the heightfield resolves as a 6–9 m strip.
      //
      // A point bar is a RIVER feature and this test asks only about height and
      // distance to water, so on the lakeshore it would read the beach as one
      // and hang a willow screen along the open lake — which ZONE 8a refuses in
      // as many words: the active beach is 85–98 % bare sand, "do not vegetate
      // this". Measured on the committed heightfield the exclusion changes
      // nothing today (0 of the dune's 2,687 dry nodes qualify; the nearest is
      // 9.66 m from water against this branch's 9 m), and it is written because
      // 0.66 m is the whole of that margin. The lakeshore's own willow scrub is
      // recorded — `salix_cordata` at 15–50 clumps/ha, `salix_interior` — and is
      // still planted by nothing; that is a stated omission, not this branch.
      if (comm !== 'dune' && bank <= 9 && y <= 0.60) {
        if (stats.thickets >= maxThickets) continue;
        // Nearly every bar cell takes a stool. A sandbar-willow thicket is a
        // SCREEN, and a screen needs its clumps to touch: at a 4 m planting step
        // and a clump about 3 m across, thinning these to half was what left
        // them standing as separate cushions on open sand. `THICKET_ACCEPT` is
        // that 0.84 carried to whatever cell the detail level offers, so the
        // screen is the same screen at every setting rather than the sampling
        // step's by-product (ROADMAP K45(b3)).
        if (rnd() > THICKET_ACCEPT || blocked(px, pz)) continue;
        addTree(chunkOf(px, pz), specs.salix_interior, px, gy, worldZ(pz), rnd,
          0.8 + rnd() * 0.5);
        noteStation(px, pz, gy);
        stats.thickets++;
        bump(stats.species, 'salix_interior');
        continue;
      }

      const key = comm === 'gallery_edge' ? 'gallery' : comm;
      const c = COMMUNITIES[key];
      // The gallery is not the same on both sides of the river. The North Side
      // is Andreas's "body of thrifty heavy growth of timber" and takes the top
      // of ZONE 5's 30–80/ha range; the South Water Street belt is the one being
      // cut for a town that has grown tenfold in two years, and takes the bottom.
      const range = key === 'gallery' && div[i] === NORTH ? [50, 78] : c.perHa;
      // A gallery forest does not stop at a line: it thins into the prairie it
      // is standing in. Without this the belt has a cut face, which is the
      // silhouette of a plantation and not of a floodplain wood.
      const edgeFade = key === 'gallery'
        ? 1 - smoothstep(0.5, 1.0, bank / lerp(30, 74, noise2(px, pz, 130, 11))) * 0.74
        : 1;
      // T-2807: the woods' prairie edge is a thicket, offered the cell first.
      if (comm !== 'gallery_edge' && plantEdgeThicket(px, pz, gy, key, div[i], bank)) continue;
      // T-2808: on a path's tread (the Green Bay road cut) the margins take the
      // sprouts, from their own generator; the stream's stem is dealt dry below.
      const cut = pathLines.length ? pathCutAt(px, pz, true) : null;
      if (cut) plantPathShrub(px, pz, gy);
      // T-2807: patches and openings, mean one (WOOD_CLUMP).
      const wc = WOOD_CLUMP[key];
      const ct = wc && comm !== 'gallery_edge'
        ? smoothstep(0.28, 0.72, noise2(px, pz, wc.cellM, 73)) : 0.5;
      const clumpK = wc && comm !== 'gallery_edge' ? wc.floor + (2 - 2 * wc.floor) * ct : 1;
      const perHa = lerp(range[0], range[1], noise2(px, pz, 58, 7))
        * clearedFactor(px, pz) * edgeFade * clumpK;
      // `keep` is the detail level's thinning and the ONLY thing here that is a
      // rendering decision: `perHa` is the community's recorded density and
      // `cellArea` is the ground this cell stands for, so the roll without it is
      // the stand the record asks for (ROADMAP K45(b3)).
      if (rnd() > (perHa * cellArea * keep) / 10000) continue;
      if (stats.trees >= maxTrees) continue;
      // A canopy tree needs its roots out of the channel; a bank willow does not.
      if (bank < 3.0 && comm !== 'gallery_edge') continue;
      if (blocked(px, pz)) continue;

      const p = pickers[key];
      const pick = comm === 'gallery_edge' && p.edgeMix ? p.edgeMix : p.mix;
      const id = pick(rnd());
      // The community's own parameters where it declares them — the dune
      // cottonwood is not the gallery cottonwood. See `communitySpecs`.
      const spec = communitySpecs[key][id];
      if (!spec) continue;
      // In an opening the stem is a young one: smaller toward the opening's heart.
      const young = wc && ct < 0.35 ? lerp(wc.young, 1, ct / 0.35) : 1;
      if (cut) { dryPlant(spec, px, gy, pz, young); stats.paths.cleared++; continue; }
      if (young < 1) stats.youngInOpenings++;
      // T-2810: in the river woods some stems stand dead, some have a fallen
      // trunk beside them, and the gallery's edge trees carry the vines.
      const dead = DEAD_WOOD.shares[key] && isGrownForm(spec) ? DEAD_WOOD.shares[key] : null;
      const dr = dead ? seededAt(px, pz, 0x2810) : null;
      const snag = dr ? dr() < dead.snag : false;
      const hostH = plant(snag ? deadSpecOf(spec, 'snag') : spec, px, gy, pz, rnd, young);
      if (dr) {
        if (snag) stats.deadWood.snags++;
        else if (key === 'gallery') dressEdgeTree(px, pz, gy, hostH, bank);
        if (dr() < dead.log) plantLog(spec, px, pz, dr);
      }
      noteStation(px, pz, gy);
      stats.trees++;
      if (spec.head) {
        stats.headStems++;
        // Where the flowering stems actually stand. A layer that is implemented
        // and a layer a visitor can SEE are different claims, and this is the
        // only field that lets anything downstream tell them apart: the mesic
        // pocket is a minority community and its two flowering species are 14
        // stems of 159 (ROADMAP K45(c)).
        stats.headStations.push({ e: px, n: pz, id });
      }
      bump(stats.communities, key);
      bump(stats.species, id);
    }
    onProgress(++rowsPlanted, rowsToPlant);
  }

  /* ---- 3b. the stems a record places itself ------------------------------ */

  /**
   * T-0091. The planter above deals a wood from the land, and a KEPT tree is
   * not dealt: it stands where somebody left it, in a yard, and no density over
   * a cleared town block will ever put one behind a particular fence. So a
   * planting record states the stem and this places exactly that stem.
   *
   * It runs AFTER the sweep on purpose. Everything above draws from the shared
   * `rnd` in a fixed order, so a placed stem inserted earlier would redeal the
   * whole wood; here it changes nothing that was already planted.
   *
   * Every refusal below is the sweep's own refusal, asked of a point the record
   * chose rather than of one the loop offered, and each one is REPORTED rather
   * than skipped quietly — a stem a record asks for and the renderer declines
   * to draw is a fault in the record, and a silent decline is how a record goes
   * on saying a tree is there for months after it stopped being drawn.
   */
  onProgress(rowsToPlant, rowsToPlant);
  for (const rec of records.plantings ?? []) {
    for (const stem of rec.stems ?? []) {
      const where = `${rec.id}/${stem.id}`;
      const at = stem.at_local_enu_m;
      if (!Array.isArray(at) || at.length !== 2) {
        problems.push(`trees: planting ${where} carries no at_local_enu_m pair — not drawn`);
        continue;
      }
      const [pe, pn] = at;
      // THE ZONE THE RECORD NAMES, not the shared first-zone-wins table. The
      // same binomial is a different tree in two communities — the gallery elm
      // is recorded at 18-26 m and the settled town's relict survivor at 16-24 —
      // and a planting is always a claim about ONE of them. `byZone` is the same
      // per-community table the dune cottonwood already reads.
      const table = records.byZone?.[rec.zone];
      if (!table) {
        problems.push(`trees: planting ${rec.id} names zone ${rec.zone}, which this module `
          + 'reads no woody species from — nothing in the record is drawn');
        break;
      }
      // The zone's woody table first, then its dooryard shrubs (T-0074) — a
      // stated stem may be either, and both tables are built from the zone's
      // own species records, so the rule holds: the ecology of a stem belongs
      // to the zone records and not to a planting file.
      const spec = table[stem.species] ?? records.shrubByZone?.[rec.zone]?.[stem.species];
      if (!spec) {
        problems.push(`trees: planting ${where} names species ${stem.species}, which `
          + `${rec.zone} does not describe — not drawn, because the ecology of a stem `
          + 'belongs to the zone records and not to a planting file');
        continue;
      }
      // The stated height has to lie inside the species' OWN recorded band. A
      // planting record may choose where in that band a stem sits — a kept tree
      // is a cut-back tree — and it may not invent a tree the records do not
      // describe, which is what a height outside the band would be.
      const band = spec.h;
      const h = stem.height_m;
      if (!(typeof h === 'number' && h >= band[0] && h <= band[1])) {
        problems.push(`trees: planting ${where} states ${h} m against ${stem.species}'s `
          + `recorded ${band[0]}-${band[1]} m — not drawn`);
        continue;
      }
      if (terrain.isWater(pe, pn)) {
        problems.push(`trees: planting ${where} stands in the river mask — not drawn`);
        continue;
      }
      const gy = terrain.surfaceHeight(pe, pn);
      if (gy < dryFloorY) {
        problems.push(`trees: planting ${where} stands ${(dryFloorY - gy).toFixed(2)} m `
          + 'below the planter\'s own dry floor — not drawn');
        continue;
      }
      if (blocked(pe, pn, rec.in_structure ?? null)) {
        problems.push(`trees: planting ${where} stands inside a committed footprint or on `
          + 'the travelled track — not drawn');
        continue;
      }
      // A stated shrub is drawn grown (T-2809), as the woods' edge thicket is
      // (T-2807): the record's own currant as a clump of stems from
      // tree-model.js's ARCH rather than the dooryard's three-puff clump. Its
      // July berries were never drawn on either path (`head` is null).
      const grownSpec = spec.form === 'shrub' ? { ...spec, form: 'edge_shrub' } : spec;
      plant({ ...grownSpec, h: [h, h] }, pe, gy, pn, rnd);
      noteStation(pe, pn, gy);
      stats.planted++;
      stats.plantedStems.push({ id: stem.id, record: rec.id, e: pe, n: pn,
        species: stem.species, height_m: h });
    }
  }

  // THE BUDGET IS A BACKSTOP AND A BOUND BACKSTOP IS A DEFECT (ROADMAP K45(b2)).
  // The loop sweeps south to north, so a cap reached partway through does not
  // thin the wood — it deletes its north end and leaves a straight edge. That is
  // what `light`'s old 300 did the moment the sweep reached the field, and it
  // would have shipped looking like a rendering choice. `problems` is what the
  // release smoke reads, so this is red rather than a console note.
  //
  // Since K45(b3) there IS a thinning instrument, so the remedy names it: `keep`
  // is the number to lower, and the cap stays the thing that must never bind.
  if (stats.trees >= maxTrees) {
    problems.push(`trees: the ${level} stem budget bound at ${maxTrees} trees, so the `
      + 'planting loop stopped partway north and the wood is cut off in a straight line '
      + `rather than thinned — lower ${level}'s keep fraction, do not lower the budget`);
  }
  if (stats.thickets >= maxThickets) {
    problems.push(`trees: the ${level} thicket budget bound at ${maxThickets} stools, so `
      + 'the bank scrub stops partway north rather than thinning — raise the budget; the '
      + 'point-bar screen is deliberately not thinned by detail');
  }
  if (stats.prairie.dry + stats.prairie.wet + stats.prairie.lone >= maxPrairie) {
    problems.push(`trees: the ${level} open-plain budget bound at ${maxPrairie} stems, so the `
      + 'prairie shrubs stop partway north rather than thinning — raise the budget');
  }
  if (stats.edgeThicket.planted >= maxShrubs) {
    problems.push(`trees: the ${level} edge-thicket budget bound at ${maxShrubs} shrubs, so `
      + 'the woods\' edge stops partway north rather than thinning — raise the budget');
  }

  /* ---- 4. the material --------------------------------------------------- */

  const uWind = { value: 0 };
  const surfaceAtlas = await createTreeAtlasSliced(checkpoint);
  // T-2743: since the grown trees took the tree-form stems, this atlas draws only
  // the bank thickets and the dooryard shrubs, so a phone keeps it from its
  // second level down, as the parkway elms did (T-2158, PR 773): a quarter of
  // its memory.
  if ((lowSpec || level === 'light') && surfaceAtlas.mipmaps?.length > 1) {
    surfaceAtlas.mipmaps = surfaceAtlas.mipmaps.slice(1);
    surfaceAtlas.image = surfaceAtlas.mipmaps[0];
  }
  const nearMat = new THREE.MeshStandardMaterial({
    vertexColors: true, map: surfaceAtlas, bumpMap: surfaceAtlas, bumpScale: 0.015,
    roughness: 0.92, metalness: 0,
    side: THREE.DoubleSide, alphaTest: TREE_ALPHA_CUTOFF,
  });
  nearMat.name = 'timber';
  patchTreeWind(nearMat, uWind, { surface: true });
  confidence?.patch(nearMat);
  const depthMat = new THREE.MeshDepthMaterial({
    map: surfaceAtlas, alphaTest: TREE_ALPHA_CUTOFF, side: THREE.DoubleSide,
    depthPacking: THREE.RGBADepthPacking,
  });
  const distanceMat = new THREE.MeshDistanceMaterial({
    map: surfaceAtlas, alphaTest: TREE_ALPHA_CUTOFF, side: THREE.DoubleSide,
  });
  patchTreeWind(depthMat, uWind);
  patchTreeWind(distanceMat, uWind);
  confidence?.patch(depthMat);
  confidence?.patch(distanceMat);
  const disposables = [nearMat, depthMat, distanceMat, surfaceAtlas];
  /**
   * ONE BATCH, CULLED PER CHUNK, IN BOTH PASSES — T-0223 step one.
   *
   * The lattice above is only affordable because of what this object is. A
   * `BatchedMesh` holds every chunk in one pair of buffers and submits the
   * visible ones as a SINGLE `WEBGL_multi_draw` call, deciding per chunk which
   * to include from that chunk's own bounding sphere. It does it in the colour
   * pass through `onBeforeRender` (the view camera) and in the shadow pass
   * through `onBeforeShadow`, which three routes to the same code with the
   * SHADOW camera — so the sun's ±240 m box finally rejects the timber standing
   * outside it, which is the whole of what T-0223 measured and costed.
   *
   * The old four quadrant meshes were four calls in the colour pass and four
   * more in the sun's. This is one and one. Draw calls FALL by six at the worst
   * stand while the chunk count rises from 4 to about seventy, which is the
   * trade the ticket said had to be watched: "the colour pass must NOT gain 40
   * calls to save the shadow pass."
   *
   * WHAT IS NOT CLAIMED. `renderer.info` counts a multi-draw as one call
   * because it is one call, but the driver still issues a sub-draw per chunk,
   * so this is not free on a real GPU the way the counter makes it look. The
   * lattice is 120 m rather than 40 for that reason — the shadow saving is
   * nearly all won by the first halving, and the sub-draw count is what pays
   * for the rest.
   *
   * The batch matrices are all identity: the chunk geometries carry absolute
   * world coordinates, exactly as the four quadrant meshes did. That is what
   * keeps the wind shader above correct — it reads `modelMatrix * transformed`
   * for its world position, which under batching skips the (identity) per-chunk
   * matrix that `project_vertex` would otherwise apply.
   */
  const chunks = [...buffers.values()].filter((b) => b.count > 0);
  if (chunks.length) {
    const vertexTotal = chunks.reduce((t, b) => t + b.count, 0);
    const indexTotal = chunks.reduce((t, b) => t + b.idx.length, 0);
    const batch = new THREE.BatchedMesh(
      chunks.length, vertexTotal, indexTotal, nearMat,
    );
    batch.name = 'timber';
    batch.customDepthMaterial = depthMat;
    batch.customDistanceMaterial = distanceMat;
    // Timber that casts no shadow is pasted onto the ground rather than
    // standing on it, and a crown that receives none is lit from every side at
    // once — which is half of why round 1's crowns read as flat green balls.
    // What decides how much of the wood pays for that is the sun's box, and
    // since T-0115 that box is ±240 m (`DETAIL.shadowReachM`), not the ±60 m an
    // earlier note here claimed — see the lattice comment at `chunkOf`.
    batch.castShadow = true;
    batch.receiveShadow = true;
    for (const b of chunks) {
      const pause = checkpoint(); if (pause) await pause;
      const geo = b.build();
      batch.addInstance(batch.addGeometry(geo));
      // The batch owns a copy from here; the source geometry is scratch.
      geo.dispose();
      b.release();
    }
    batch.computeBoundingSphere();
    group.add(batch);
    disposables.push(batch);
    stats.drawCalls++;
    stats.triangles += indexTotal / 3;
  }
  stats.timberChunks = chunks.length;
  stats.foliageSprays = chunks.reduce((t, b) => t + b.sprays, 0);
  stats.foliageRepresentation = 'species-alpha-sprays';
  stats.surfaceAtlasSize = 2048;
  for (const b of chunks) stats.heads += b.heads;

  /* ---- 4b. the grown trees (T-2743) ------------------------------------- */

  // Every tree-form stem, drawn from its species' grown model: see
  // tree-instances.js for the levels and the shadow ring. `stats.grown` is live:
  // its level counts and triangles are re-read as the visitor walks.
  let forest = null;
  let grownMats = null;
  if (grown.count) {
    grownMats = await createGrownTreeMaterials({
      assetBase: resolveBases().assetBase, uWind, confidence, patchWind: patchTreeWind,
      lowSpec: lowSpec || level === 'light', alphaCutoff: TREE_ALPHA_CUTOFF, problems,
    });
    disposables.push(grownMats);
    forest = await grown.build({ ...grownMats, checkpoint });
    group.add(forest.group);
    stats.drawCalls += forest.stats.drawCalls;
  }
  stats.grown = forest?.stats ?? { stems: 0 };
  // T-2864: the crown the Season setting asks for (tree-model.js leafCover and
  // leafScale), and the materials that take its colour.
  let crownNow = '{}';

  /* ---- 5. the horizon ---------------------------------------------------- */

  const BINS = lowSpec ? 480 : 900;
  const binRad = (Math.PI * 2) / BINS;
  const topRad = new Float32Array(BINS);
  const binDist = new Float32Array(BINS);
  // T-1978: where on its body's near edge each bin's crown stands, in metres
  // along the edge (offset per body so two bodies do not share a pattern).
  const binEdge = new Float32Array(BINS);
  // The profile BEFORE the crown/gap modulation, kept so the gate can ask what
  // the modulation did rather than re-deriving the noise that drives it.
  const rawRad = new Float32Array(BINS);
  // T-0120 — each bin's modulated elevation as a LINEAR FUNCTION of the eye
  // height, theta(eyeY) = binA - binS * eyeY. The solve's theta depends on the
  // eye through exactly one linear term ((hgt - eyeY)/d - d/(2*R_EFF)), so the
  // expensive part — which bearings carry timber, at what distance and crown
  // height — can stay on the RING_REBUILD_M schedule while the eye-height term
  // is finished per frame in the vertex shader against `uEyeY`. Before this,
  // eyeY was baked into each vertex at solve time: between solves the band was
  // welded to the eye, rode up and down with it, and SNAPPED to the re-solved
  // profile when a threshold tripped — the owner's "up and down wildly".
  const binA = new Float32Array(BINS);
  const binS = new Float32Array(BINS);
  // Vertical pixels per radian, re-read from the live viewport each solve. The
  // band is the one thing in this file whose correctness is measured in pixels
  // rather than in metres, because what it draws is an angular silhouette.
  let pxPerRad = DEFAULT_PX_PER_RAD;
  const readPxPerRad = () => {
    const v = pixelsPerRadian?.();
    return Number.isFinite(v) && v > 0 ? v : DEFAULT_PX_PER_RAD;
  };
  const continuity = {
    bins: BINS, pxPerRad, covered: 0, resolvable: 0, drawn: 0,
    fraction: 0, worstResolvablePx: 0, minSilhouettePx: MIN_SILHOUETTE_PX,
  };

  const horizon = new THREE.Group();
  horizon.name = 'horizon-timber';
  const hPos = new Float32Array(BINS * 4 * 3);
  const hCol = new Float32Array(BINS * 4 * 3);
  const hIdx = new Uint32Array(BINS * 6);
  // T-0120 — the two halves of theta(eyeY) = aTheta0 - aSlope * eyeY, carried
  // per vertex so the shader can finish the eye-height term every frame. A
  // foot vertex carries slope 0: the foot is a fixed RING_FOOT_M below the eye
  // by design, tucked under the water plane and any far ground.
  const hTheta0 = new Float32Array(BINS * 4);
  const hSlope = new Float32Array(BINS * 4);
  const hGeo = new THREE.BufferGeometry();
  hGeo.setAttribute('position', new THREE.BufferAttribute(hPos, 3).setUsage(THREE.DynamicDrawUsage));
  hGeo.setAttribute('color', new THREE.BufferAttribute(hCol, 3).setUsage(THREE.DynamicDrawUsage));
  hGeo.setAttribute('aTheta0', new THREE.BufferAttribute(hTheta0, 1).setUsage(THREE.DynamicDrawUsage));
  hGeo.setAttribute('aSlope', new THREE.BufferAttribute(hSlope, 1).setUsage(THREE.DynamicDrawUsage));
  hGeo.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(BINS * 4).fill(0.5), 1));
  hGeo.setIndex(new THREE.BufferAttribute(hIdx, 1));
  hGeo.setDrawRange(0, 0);
  // The band is drawn as a ring around the camera; frustum culling a bounding
  // sphere that always contains the camera can only ever throw it away by
  // mistake, exactly as with the ground.
  hGeo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), RING_RADIUS * 1.2);

  const farMat = new THREE.MeshBasicMaterial({ vertexColors: true, fog: false });
  farMat.name = 'horizon-timber';
  // Authored in display space against the rendered sky, so it must not be tone
  // mapped a second time. See the header: this band opts out of the scene fog.
  farMat.toneMapped = false;
  // T-0120 — the eye height, per FRAME rather than per solve. The CPU writes
  // each top vertex at the height the solve's own eyeY gives it, and this
  // shader recomputes the same expression against the LIVE eye, so between
  // solves the band stands where the world says instead of riding the eye.
  // At the moment of a re-solve the two agree exactly — theta is exactly
  // linear in eyeY — which is what removes the snap.
  const uEyeY = { value: 2.7 };
  // T-2103: how much of the band stands up at this eye height, 1 walking and
  // 0 from the air — computed once per frame by `bandLift` and read by both
  // the shader and `horizonLift()`, so the gate and the frame cannot disagree.
  const uBandUp = { value: 1 };
  {
    const prior = farMat.onBeforeCompile;
    farMat.onBeforeCompile = (shader, renderer) => {
      if (typeof prior === 'function') prior(shader, renderer);
      shader.uniforms.uEyeY = uEyeY;
      shader.uniforms.uBandUp = uBandUp;
      shader.vertexShader = `
attribute float aTheta0;
attribute float aSlope;
uniform float uEyeY;
uniform float uBandUp;
` + shader.vertexShader.replace('#include <begin_vertex>', /* glsl */`
#include <begin_vertex>
  // T-2103: from the air the top sinks onto the foot (BAND_FADE_EYE_M). A
  // foot vertex carries theta0 = the foot and slope 0, so it is unmoved.
  float bandFoot = ${(RING_FOOT_M / RING_RADIUS).toFixed(6)};
  transformed.y = ${RING_RADIUS.toFixed(1)} * tan(mix(bandFoot, aTheta0 - aSlope * uEyeY, uBandUp));
`);
    };
    farMat.needsUpdate = true;
  }
  confidence?.patch(farMat);
  const hMesh = new THREE.Mesh(hGeo, farMat);
  hMesh.name = 'horizon-timber';
  hMesh.frustumCulled = false;
  hMesh.renderOrder = -1;
  horizon.add(hMesh);
  group.add(horizon);
  disposables.push(hGeo, farMat);

  // The band's hazed end, in the renderer's linear working space. NOT a const
  // since T-1631: `world.js` turns the scene's haze with the view, and this
  // band is authored to land exactly where the fogged ground lands — the
  // release smoke asserts the two are one colour — so it has to be able to
  // follow. `update()` refreshes it from `scene.fog.color` and re-solves when
  // it has moved. The fixed derivation is still what it starts at, so a
  // renderer that never passes a haze in draws exactly what it drew before.
  const haze = hazeDisplayLinear();
  let hazeHex = new THREE.Color().setRGB(haze[0], haze[1], haze[2])
    .getHex(THREE.SRGBColorSpace);
  const timber = linear(TIMBER_SRGB);

  // The stand of the LIVE solve, so `horizonCensus()` can re-run exactly the
  // solve the visitor is looking at rather than one at a guessed position.
  let solvedE = 0;
  let solvedN = 0;
  let solvedY = 2.7;

  /**
   * Solve the band for an eye at (e, n, eyeY) and write it into the buffers.
   *
   * `record`, when given, is the T-0120 measuring instrument: it is called at
   * every decision that removes a sample or bin from the band —
   * `('near'|'wet'|'below', bodyId, bearingRad, d)` — at every winning
   * coverage update — `('top', bodyId, bin, d)` — and once per timbered bin
   * after modulation — `('bin', bin, rawPx, drawnPx, kFloor)`. Normal frames
   * pass nothing and pay one falsy check per sample.
   */
  function solveHorizon(camE, camN, eyeY, record) {
    solvedE = camE;
    solvedN = camN;
    solvedY = eyeY;
    topRad.fill(-1);
    binDist.fill(0);
    binEdge.fill(0);
    rawRad.fill(0);
    binA.fill(0);
    binS.fill(0);
    pxPerRad = readPxPerRad();

    let wetSkipped = 0;
    for (let bi = 0; bi < FAR_TIMBER.length; bi++) {
      const body = FAR_TIMBER[bi];
      const path = body.path;
      // T-1978: metres along the body's own near edge, so the profile's noise
      // is a property of the WORLD. It was keyed on bearing × distance from the
      // eye, which every step of the walk, the wagon or the flight changes, so
      // each re-solve dealt a fresh silhouette — the owner's "wobbly".
      let segStart = 0;
      for (let s = 0; s < path.length - 1; s++) {
        const [ax, ay] = path[s];
        const [bx, by] = path[s + 1];
        const segLen = Math.hypot(bx - ax, by - ay);
        const ux = segLen > 0 ? (bx - ax) / segLen : 0;
        const uy = segLen > 0 ? (by - ay) / segLen : 0;
        let t = 0;
        while (t <= segLen) {
          const f = segLen > 0 ? t / segLen : 0;
          const pe = ax + (bx - ax) * f;
          const pn = ay + (by - ay) * f;
          const dx = pe - camE;
          const dn = pn - camN;
          const d = Math.hypot(dx, dn);
          // Adaptive: a body four kilometres out does not need a sample every
          // twenty metres, and a body four hundred metres out does.
          const stepM = Math.max(16, d * 0.030);
          t += stepM;
          const bearing = Math.atan2(dx, dn);
          if (d < MIN_FAR_M) { record?.('near', body.id, bearing, d); continue; }
          // ROADMAP R-BUG5. THE ONE QUESTION EVERY BODY OF TIMBER MUST ANSWER,
          // and until 2026-08-16 this loop never asked it. `communityAt()` has
          // refused the traced water mask outright since the near-field planter
          // was written, and a stand drawn at four hundred metres makes exactly
          // the same claim about exactly the same water — so the mask binds here
          // too. `main_stem_belt_east` was authored between the two banks of the
          // main stem, 39 of 39 census samples over water and up to 3.347 m
          // below its surface, and drew a straight line of crowns out across the
          // channel with the solver's gap modulation scattering the rest of the
          // run into separate trees. That is the owner's screenshot, both
          // populations of it, from one cause.
          //
          // Sampled at the emitted point rather than at the body's vertices: a
          // belt may cross a channel between two dry ends, which is what the
          // North Branch belt does. Outside the modelled heightfield the mask
          // returns the fallback height and answers "dry" — which is the honest
          // answer there, because this project has no survey of that ground and
          // a clip that claimed one would be inventing it.
          if (terrain.isWater(pe, pn)) { wetSkipped++; record?.('wet', body.id, bearing, d); continue; }

          const sHere = segStart + (t - stepM);
          const theta = (canopyAt(body, bi, sHere, d) - eyeY) / d - d / (2 * R_EFF);
          if (theta <= 0) { record?.('below', body.id, bearing, d); continue; }
          const halfAng = (stepM * 0.5 + body.crown * 0.5) / d;
          const lo = Math.floor((bearing - halfAng) / binRad);
          const hi = Math.ceil((bearing + halfAng) / binRad);
          for (let k = lo; k <= hi; k++) {
            const b = ((k % BINS) + BINS) % BINS;
            // T-1978: each bin reads the canopy at ITS OWN point on the edge —
            // the sample moved along the segment by the bin's offset in bearing
            // — so a run of bins under one sample is not a flat step, and the
            // point a bin reads moves smoothly as the eye does.
            const bb = (k + 0.5) * binRad;
            const sb = sHere + ((Math.sin(bb) - Math.sin(bearing)) * ux
              + (Math.cos(bb) - Math.cos(bearing)) * uy) * d;
            const th = (canopyAt(body, bi, sb, d) - eyeY) / d - d / (2 * R_EFF);
            if (th > topRad[b]) {
              topRad[b] = th;
              binDist[b] = d;
              binEdge[b] = sb + bi * 7919;
              record?.('top', body.id, b, d);
            }
          }
        }
        segStart += segLen;
      }
    }

    // Break the profile up crown by crown, measured in METRES along the
    // treeline rather than in degrees, so the bumps stay crown-sized whether
    // the timber is four hundred metres away or four kilometres.
    let timbered = 0;
    let resolvable = 0;
    let drawn = 0;
    let worstResolvablePx = Infinity;
    for (let b = 0; b < BINS; b++) {
      if (topRad[b] <= 0) { topRad[b] = 0; continue; }
      timbered++;
      rawRad[b] = topRad[b];
      const rawPx = topRad[b] * pxPerRad;
      const d = binDist[b];
      // T-1978: crown-sized in METRES ALONG THE EDGE (see `binEdge`), so the
      // bumps belong to the trees and stay put as the eye moves.
      const u = binEdge[b] / 15;
      const crownN = noise1(u, 5) * 0.28 + noise1(u * 2.6, 9) * 0.24
        + noise1(u * 6.4, 17) * 0.26 + noise1(u * 13.1, 23) * 0.22;
      const gapN = noise1(u / 6, 13);
      // T-1978 — the owner, from Lake Street at Clark facing west, of the belt
      // 330–530 m out: "it probably should be much less wobble if any at this
      // distance, be more stable and lower". Until then k ran 0.40–1.00 on the
      // crowns and down to 0.05 in a gap at EVERY distance, so a 20 m canopy
      // drew a top swinging between 8 m and 24 m with notches to the ground:
      // a range of hills. Now the top sits at a steady share of the canopy
      // (a far treeline's outline is the mean of many crowns, not the tallest)
      // with a crown texture that shrinks with distance, and sky opens through
      // the stand only near, and only part way.
      const relief = farRelief(d);
      let k = HORIZON_TOP_K * (1 + (crownN - 0.5) * 2 * HORIZON_CROWN_AMP * relief);
      // Sky through the stand: without any, a near treeline is a silhouette
      // with one outline. Shallow, and gone by about 700 m.
      const gapDepth = HORIZON_GAP_DEPTH * Math.max(0, (relief - 0.5) / 0.5);
      if (gapN < 0.30 && gapDepth > 0) k *= 1 - gapDepth * (1 - gapN / 0.30);
      // ...but a hole the frame cannot resolve is not sky through a stand, it
      // is the stand deleted. The modulation may cut a bearing to
      // MIN_SILHOUETTE_PX and no further; where the raw crown is already under
      // that it is suppressed outright (kFloor reaches 1). This is a floor on
      // the RESULT rather than a cap on `k`, so it binds exactly where the
      // pixels are scarce and nowhere else — the near treelines keep their
      // gaps to the last per cent.
      //
      // T-0120: COMPRESSED into [kFloor, 1] rather than clamped at kFloor. The
      // clamp took every bin whose modulated crown fell under the floor to
      // exactly MIN_SILHOUETTE_PX, and on a body whose raw crown is one or two
      // pixels that is MOST bins — the owner's frame shows the result, a
      // dead-flat run at the left horizon, exactly the flat-topped block this
      // file warns "reads as a distant BUILDING". Remapping keeps the floor's
      // whole contract (nothing drawn under MIN_SILHOUETTE_PX where the raw
      // crown affords it; raw sub-pixel bearings still get k = 1) while the
      // crown texture survives above the floor. Where the band is well
      // resolved, kFloor is small and the remap is within a few per cent of
      // the old clamp — a 0.02 gap on a 40 px treeline still opens to a
      // couple of pixels of sky.
      const kFloor = Math.min(1, MIN_SILHOUETTE_PX / Math.max(rawPx, 1e-6));
      k = kFloor + (1 - kFloor) * k;
      topRad[b] = topRad[b] * k;
      // T-0120: the same modulated elevation, decomposed against the eye.
      // theta(eyeY) = k*((hgt/d - d/(2*R_EFF)) - eyeY/d); rawRad holds the
      // bracket evaluated at the SOLVE eye, so add the solve eye back in.
      binA[b] = k * (rawRad[b] + eyeY / d);
      binS[b] = k / d;
      const px = topRad[b] * pxPerRad;
      record?.('bin', b, rawPx, px, kFloor);
      if (rawPx >= MIN_SILHOUETTE_PX) {
        resolvable++;
        if (px < worstResolvablePx) worstResolvablePx = px;
      }
      if (px >= MIN_SILHOUETTE_PX - 1e-6) drawn++;
      if (topRad[b] <= 1e-5) topRad[b] = 0;
    }
    continuity.pxPerRad = pxPerRad;
    continuity.covered = timbered;
    continuity.resolvable = resolvable;
    continuity.drawn = drawn;
    continuity.fraction = resolvable > 0 ? drawn / resolvable : 0;
    continuity.worstResolvablePx = Number.isFinite(worstResolvablePx) ? worstResolvablePx : 0;

    // Emit each contiguous run of timbered bearings as ONE strip, with the
    // profile carried on shared vertices. Quad-per-bin looks like a staircase:
    // at four hundred metres a bin is six pixels wide and eight tall, and a
    // flat-topped six-pixel block reads as a distant BUILDING, not as a tree.
    let verts = 0;
    let indices = 0;
    const footTheta = RING_FOOT_M / RING_RADIUS;
    const y0 = RING_RADIUS * footTheta;
    // T-0120: a top vertex carries theta as its (aTheta0, aSlope) pair; the
    // CPU height written here is the same expression at the SOLVE eye, kept so
    // anything reading the buffer (raycasts, tests) sees what the last solve
    // saw. A foot vertex is a fixed RING_FOOT_M below the eye — slope 0.
    const putVert = (ang, thA, thS, d) => {
      const sx = Math.sin(ang) * RING_RADIUS;
      const sz = -Math.cos(ang) * RING_RADIUS;
      const mixTop = hazeAt(d);
      // The foot of a treeline is a shade deeper than its crowns, never paler:
      // haze applies to both equally and the trunk zone is in its own shadow.
      const mixBot = mixTop * 0.94;
      const i0 = verts * 3;
      hPos[i0] = sx; hPos[i0 + 1] = y0; hPos[i0 + 2] = sz;
      hCol[i0] = lerp(timber[0], haze[0], mixBot);
      hCol[i0 + 1] = lerp(timber[1], haze[1], mixBot);
      hCol[i0 + 2] = lerp(timber[2], haze[2], mixBot);
      hTheta0[verts] = footTheta; hSlope[verts] = 0;
      verts++;
      const i1 = verts * 3;
      hPos[i1] = sx; hPos[i1 + 1] = RING_RADIUS * Math.tan(thA - thS * eyeY); hPos[i1 + 2] = sz;
      hCol[i1] = lerp(timber[0], haze[0], mixTop);
      hCol[i1 + 1] = lerp(timber[1], haze[1], mixTop);
      hCol[i1 + 2] = lerp(timber[2], haze[2], mixTop);
      hTheta0[verts] = thA; hSlope[verts] = thS;
      verts++;
    };

    let b = 0;
    // Start on a bearing that has no timber, so a run that wraps past north is
    // not cut in half by the seam.
    let start = 0;
    while (start < BINS && topRad[start] > 0) start++;
    if (start >= BINS) start = 0;
    while (b < BINS) {
      const idx = (start + b) % BINS;
      if (topRad[idx] <= 0) { b++; continue; }
      let len = 0;
      while (b + len < BINS && topRad[(start + b + len) % BINS] > 0) len++;
      if (verts + 2 * (len + 1) > BINS * 4) break;

      const first = verts;
      for (let j = 0; j <= len; j++) {
        const left = (start + b + j - 1 + BINS) % BINS;
        const right = (start + b + j) % BINS;
        // A run ends in its outermost CROWN, at nearly full height. Tapering
        // the ends to the ground instead draws a smooth dome, and a smooth dome
        // on a lake-plain horizon reads as a hill — there are no hills here, so
        // that silhouette is a geological claim the sources flatly contradict.
        // The same end taper and shared-vertex average are applied to the
        // (A, S) pair — theta is linear in eyeY, so combining the halves
        // combines the function.
        // T-2103: ...but a full-height last crown on a run of a few bins is a
        // sheer edge on a narrow block, which read as a slab. The last few
        // vertices of a run step down on a quarter-sine to 45 %, over at most
        // a quarter of the run so a short run keeps a top: a shoulder, still
        // well short of the dome described above.
        const edge = Math.min(j, len - j);
        const span = Math.max(1, Math.min(4, Math.floor(len / 4)));
        const sh = edge >= span ? 1 : 0.45 + 0.55 * Math.sin((edge / span) * Math.PI * 0.5);
        let thA = (j === 0 ? binA[right]
          : j === len ? binA[left] : (binA[left] + binA[right]) * 0.5) * sh;
        let thS = (j === 0 ? binS[right]
          : j === len ? binS[left] : (binS[left] + binS[right]) * 0.5) * sh;
        if (thA - thS * eyeY < 1e-5) { thA = 1e-5; thS = 0; }
        const d = j === len ? binDist[left] : binDist[right];
        putVert((start + b + j) * binRad, thA, thS, d);
      }
      // Wound so the INSIDE of the ring faces the camera at its centre. The
      // other winding is silently invisible — a back-faced band culls away and
      // leaves an empty horizon that looks exactly like an honest one.
      for (let j = 0; j < len; j++) {
        const q = first + j * 2;
        hIdx[indices++] = q; hIdx[indices++] = q + 2; hIdx[indices++] = q + 1;
        hIdx[indices++] = q + 1; hIdx[indices++] = q + 2; hIdx[indices++] = q + 3;
      }
      b += len;
    }

    hGeo.attributes.position.needsUpdate = true;
    hGeo.attributes.color.needsUpdate = true;
    hGeo.attributes.aTheta0.needsUpdate = true;
    hGeo.attributes.aSlope.needsUpdate = true;
    hGeo.index.needsUpdate = true;
    hGeo.setDrawRange(0, indices);
    // R-BUG5: how much of the band this solve refused to draw because the mask
    // said the ground under it was river. Zero on a clean dataset — a non-zero
    // number here means a body is authored into water and the clip is the only
    // thing standing between it and the owner's screen.
    stats.horizonWetSkipped = wetSkipped;
    stats.horizonBins = timbered;
    stats.timberedBearingFraction = timbered / BINS;
    stats.horizonDrawnFraction = continuity.fraction;
    stats.horizonPxPerRad = pxPerRad;
    stats.triangles = stats.triangles - (stats.horizonTriangles ?? 0) + indices / 3;
    stats.horizonTriangles = indices / 3;
  }

  stats.horizonBodies = FAR_TIMBER.length;
  stats.drawCalls++;
  solveHorizon(0, 0, 2.7);

  /* ---- 6. the frame ------------------------------------------------------ */

  let wind = 0;
  let lastE = Infinity;
  let lastN = Infinity;
  let lastY = Infinity;

  /** T-3263 — the grown trees' trunks as { e, n, r } (r at breast height, from the
   *  species' dbh at the stem's grown height), for the stand-off rule to see past. Not
   *  the shrubs, vines or thickets: a step along the street does not clear those. */
  let trunkList = null;
  const trunks = () => trunkList ??= grown.stems
    .filter((s) => s.kind.spec.dbh && s.kind.spec.form !== 'edge_shrub' && !s.kind.spec.habit)
    .map((s) => {
      const [d0, d1] = s.kind.spec.dbh, [h0, h1] = s.kind.spec.h;
      return { e: s.x, n: -s.z, r: ((d0 + d1) / 4) * (s.h / ((h0 + h1) / 2 || 1)) };
    });

  return {
    group,
    trunks,
    /** The far-timber table, so a test can assert what is on the horizon. */
    farTimber: FAR_TIMBER,

    /**
     * ROADMAP R-BUG5 — every body of far timber, sampled against the water mask
     * the browser actually loaded.
     *
     * `tools/measure_far_timber.py` asks the same question of the committed
     * bytes and is the gate that runs on every commit. This is the runtime half,
     * and it is not redundant: the Python reads `heightfield.bin` from `data/`
     * and the page loads the published mirror, and this project has twice
     * shipped a bug that lived exactly in that gap. The step is the same 2 m,
     * finer than the solver's own minimum emission step of 16 m, so a reach the
     * band could draw into cannot fall between two samples.
     *
     * `unmodelled` is the honest third answer: past the edge of the heightfield
     * the mask returns a fallback and knows nothing, and four of the five bodies
     * run kilometres past it.
     */
    farTimberWater(stepM = 2) {
      return FAR_TIMBER.map((body) => {
        let samples = 0;
        let wet = 0;
        let unmodelled = 0;
        let worst = 0;
        const hf = terrain.heightfield;
        const inBox = (e, n) => !hf?.loaded || (
          e >= hf.originE && n >= hf.originN
          && e <= hf.originE + (hf.cols - 1) * hf.cellM
          && n <= hf.originN + (hf.rows - 1) * hf.cellM);
        for (let s = 0; s < body.path.length - 1; s++) {
          const [ax, ay] = body.path[s];
          const [bx, by] = body.path[s + 1];
          const segLen = Math.hypot(bx - ax, by - ay);
          const steps = Math.max(1, Math.ceil(segLen / stepM));
          for (let k = 0; k <= steps; k++) {
            if (k === steps && s < body.path.length - 2) break;
            const f = k / steps;
            const e = ax + (bx - ax) * f;
            const n = ay + (by - ay) * f;
            samples++;
            if (!inBox(e, n)) { unmodelled++; continue; }
            if (terrain.isWater(e, n)) {
              wet++;
              worst = Math.min(worst, terrain.surfaceHeight(e, n));
            }
          }
        }
        return { id: body.id, samples, wet, unmodelled, worstDepthM: -worst };
      });
    },
    omitted: OMITTED_TIMBER,
    stats,

    /**
     * What the crown/gap modulation did to the silhouette, in the band's own
     * terms — asked of the solver rather than re-derived from its noise.
     *
     * `covered` is the bearings a timber body reaches at all; `resolvable`
     * those whose unmodulated crown is at least one pixel of THIS viewport;
     * `drawn` those the modulation leaves at a pixel or more. The fraction is
     * drawn/resolvable, because a body whose raw silhouette is already
     * sub-pixel — a 20 m canopy at 9.7 km is 0.7 px on a phone — cannot be
     * made visible by any choice this function has, and counting it as a
     * failure would only invite the floor to be raised until it lies.
     */
    /**
     * T-2103 — how much of the band stands up at the live eye: 1 for a walker
     * or a rider, 0 from the air (`BAND_FADE_EYE_M`), and whether it is drawn.
     */
    horizonLift() {
      return { lift: uBandUp.value, visible: hMesh.visible, eyeY: uEyeY.value,
        fadeEyeM: [...BAND_FADE_EYE_M] };
    },

    horizonContinuity() {
      return { ...continuity };
    },

    /**
     * T-0120 — the measuring instrument for "the band stops where it should
     * carry on". Re-runs the LIVE solve (same stand, same viewport) with a
     * recorder attached and returns, bearing by bearing, what the band drew
     * and what each rule cut, so a reported gap can be attributed to
     * MIN_FAR_M, to the water mask, to the eye-level cull, to the sub-pixel
     * floor, or to the dossier's own silence — measured, not guessed. The
     * rewritten buffers are identical (the same arguments produce the same
     * solve), so calling this from a console or a test changes nothing on
     * screen.
     *
     * `bins` lists every timbered bearing: `{ bin, bearingDeg, body, d,
     * rawPx, drawnPx, kFloor }` — `kFloor` at 1 means the raw silhouette was
     * already sub-pixel and the crown modulation was suppressed. `cuts` lists
     * every sample a rule removed: `{ rule: 'near'|'wet'|'below', body,
     * bearingDeg, d }`. A bearing in neither list has no recorded timber at
     * all — the dossier's silence, not a renderer rule.
     */
    horizonCensus() {
      const bodyOf = new Array(BINS).fill(null);
      const bins = [];
      const cuts = [];
      const record = (kind, a1, a2, a3, a4) => {
        if (kind === 'top') { bodyOf[a2] = a1; return; }
        if (kind === 'bin') {
          bins.push({
            bin: a1,
            bearingDeg: ((((a1 + 0.5) * binRad) * 180 / Math.PI) + 360) % 360,
            body: bodyOf[a1],
            d: binDist[a1],
            rawPx: a2,
            drawnPx: a3,
            kFloor: a4,
          });
          return;
        }
        cuts.push({
          rule: kind,
          body: a1,
          bearingDeg: ((a2 * 180 / Math.PI) + 360) % 360,
          d: a3,
        });
      };
      solveHorizon(solvedE, solvedN, solvedY, record);
      return {
        stand: { e: solvedE, n: solvedN, eyeY: solvedY },
        pxPerRad,
        binDeg: 360 / BINS,
        minSilhouettePx: MIN_SILHOUETTE_PX,
        minFarM: MIN_FAR_M,
        bins,
        cuts,
      };
    },

    /**
     * The sRGB the band's fully-hazed end displays at, so the gate can compare
     * it against `scene.fog.color` — the two must be the same colour, and were
     * 16 red and 12 green apart until 2026-08-13.
     */
    hazeTargetHex() {
      const c = new THREE.Color().setRGB(haze[0], haze[1], haze[2]);
      return c.getHex(THREE.SRGBColorSpace);
    },

    /**
     * @param {number} dt              seconds since the last frame
     * @param {THREE.Camera} camera    the camera about to render
     * @param {THREE.Color} [hazeNow]  the scene fog's live colour (T-1631)
     */
    update(dt, camera, hazeNow) {
      wind += (dt || 0);
      uWind.value = wind;
      if (!camera) return;
      forest?.update(camera.position);
      // T-1631. A turn in place moves the haze and moves nothing else, so the
      // band's own re-solve trigger — which is distance walked — would never
      // fire and the band would sit at the colour of a bearing the visitor has
      // stopped looking at. Compare the DISPLAYED hex rather than the floats:
      // that is the quantity the gate compares and the only one a visitor can
      // see, so a difference too small to show is not paid for with a re-solve.
      let hazeMoved = false;
      if (hazeNow) {
        const nowHex = hazeNow.getHex(THREE.SRGBColorSpace);
        if (nowHex !== hazeHex) {
          hazeHex = nowHex;
          haze[0] = hazeNow.r; haze[1] = hazeNow.g; haze[2] = hazeNow.b;
          hazeMoved = true;
        }
      }
      const p = camera.position;
      horizon.position.set(p.x, p.y, p.z);
      // T-0120: the eye-height term of every vertex is finished in the vertex
      // shader against THIS value, every frame — the band no longer rides the
      // eye between solves and no longer snaps when a solve lands. The
      // vertical re-solve below survives only to refresh the DISCRETE
      // decisions eyeY feeds (the theta <= 0 cull, the pixel floor); the
      // re-solved profile agrees with the shader-corrected one to under a
      // fiftieth of a pixel, because theta is exactly linear in eyeY.
      uEyeY.value = p.y;
      uBandUp.value = bandLift(p.y);
      // Nothing to draw when the top has sunk onto the foot.
      hMesh.visible = uBandUp.value > 0;
      const e = p.x;
      const n = -p.z;
      // A viewport change moves the pixel the floor is measured in, so it is a
      // reason to re-solve exactly as walking is. 2 % keeps a drag-resize from
      // re-solving every frame.
      const pxNow = readPxPerRad();
      if (hazeMoved || Math.abs(e - lastE) > RING_REBUILD_M || Math.abs(n - lastN) > RING_REBUILD_M
        || Math.abs(p.y - lastY) > 0.30 || Math.abs(pxNow - pxPerRad) > pxPerRad * 0.02) {
        lastE = e; lastN = n; lastY = p.y;
        solveHorizon(e, n, p.y);
      }
    },

    /**
     * T-2864 — the Season setting. `crown` is tree-model.js's season crown
     * ({} summer, leafCover/leafScale otherwise): the grown trees are re-grown from
     * the same stems with it, so spring is first leaf, fall a thinner crown and
     * winter bare limbs. The leaves', thickets' and far band's colour is the
     * shared season uniforms' (season.js chiFoliage), installed on first use.
     */
    async setSeason(crown = {}, { foliage = null } = {}) {
      if (foliage) for (const [m, role] of [[grownMats?.leafMat, 0], [nearMat, 0], [farMat, 2]]) foliage(m, role);
      const key = JSON.stringify(crown);
      if (!grownMats || key === crownNow) return;
      crownNow = key;
      if (forest) { group.remove(forest.group); forest.dispose(); forest = null; }
      forest = await grown.build({ ...grownMats, checkpoint, season: crown });
      group.add(forest.group);
      stats.grown = forest.stats;
    },

    dispose() {
      for (const d of disposables) d?.dispose?.();
      forest?.dispose();
    },
  };
}

/** T-2103 — the band's lift at an eye height: 1 below the fade, 0 above it. */
function bandLift(eyeY) {
  const [a, b] = BAND_FADE_EYE_M;
  const t = Math.min(1, Math.max(0, (eyeY - a) / (b - a)));
  return 1 - t * t * (3 - 2 * t);
}
/** How far a canopy top at `d` metres stands above a level line of sight. */
function apparentTopDeg(canopyM, d, eyeY) {
  return ((canopyM - eyeY) / d - d / (2 * R_EFF)) * 180 / Math.PI;
}
/** How far the visible horizon sits below a level line of sight, in degrees. */
function horizonDipDeg(eyeY) {
  return Math.sqrt((2 * eyeY) / R_EFF) * 180 / Math.PI;
}

export { SPECIES, COMMUNITIES, FAR_TIMBER, OMITTED_TIMBER };
/** T-2473: the 1904 parkway elms are built by this file's own tree, not a copy of it. */
export { addTree, MeshBuf };
