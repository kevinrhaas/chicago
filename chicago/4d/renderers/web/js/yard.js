/**
 * yard.js — the goods a working town left standing on its own ground.
 *
 * WHY THIS FILE EXISTS. `docs/ROADMAP.md` K5 (c) asks for *"crates and barrels
 * at the stores"* and *"wagons/drays"*, and ticket T-0040 is that clause for
 * the taverns and the stores. Unlike the signboards one layer over, it does not
 * start from silence: the village corporation's **Ordinance 9 of 7 November
 * 1833** is about timber, stone, brick, boxes and barrels stacked in the
 * streets, and a corporation does not legislate against a thing nobody does.
 * What the ordinance gives is the treatment and no location at all, so
 * `tools/generate_yard_goods.py` answers "which frontage" with a rule,
 * `tools/check.sh` re-derives its record byte for byte, and this file only
 * draws what that record says.
 *
 * WHAT IT WILL AND WILL NOT DO.
 *
 *  * It stands its goods on the TERRAIN, not on a building's wall base. A
 *    barrel on a footway rests on the ground it is standing on, so each object
 *    samples `terrain.surfaceHeight` at its own point — which is the opposite
 *    of `signage.js`, where a board must hang off the same datum as the wall it
 *    is bolted to or it floats. Two layers, two right answers.
 *  * IT MARKS THE GOODS (T-0065). This bullet used to say the opposite — no
 *    mark, no brand, no stencil, no label, not on any barrel or case, ever —
 *    and the owner overruled it on 2026-08-18: *"you can add period correct
 *    names and brands and labels to things."* So every cask carries a
 *    stencilled commodity word or the house's own brand burned into its head,
 *    and every case carries a shipping mark. WHAT a mark may say is fenced in
 *    `tools/generate_yard_goods.py` and bounded in docs/LIBERTIES.md L166; this
 *    file only paints what the record says, on ONE CANVAS ATLAS, so a mark
 *    costs no triangles and the layer keeps its one material and its chunked
 *    draw calls. Every vertex that carries no mark samples a white cell, which
 *    multiplies to exactly the timber it was before.
 *  * It carries ONE MATERIAL and draws in CULLING-SIZED CHUNKS (T-0064). It was
 *    one draw call for the whole layer for as long as the layer was a hundred
 *    and fifty barrels on twenty-six frontages and four wagons — and it kept
 *    that one call when the canvas arrived, because a tilt is not timber and
 *    must not read as timber, so the tone moved onto the VERTICES rather than
 *    into a second material. Then T-0064 put sixty-four more wagons across the whole
 *    town, and a single geometry spanning the whole town has a bounding sphere
 *    no frustum ever culls: every wagon in Chicago would draw in every frame,
 *    including the ones behind the camera. T-0115 measured exactly that on the
 *    fences and named it the largest free saving left in the scene; T-0119 fixed
 *    it for the river walk and T-0067 for the fences. So the goods now go into
 *    `CHUNK_M`-square buckets by where they stand, one mesh each, all on the
 *    same material — and the draw-call principle bends exactly as far as culling
 *    needs it to and no further.
 *  * It marks itself. Every vertex carries `_confidence` at `reconstructed`,
 *    because the FACT of goods on these frontages is reconstructed — the
 *    weakest thing deciding that the vertex exists at all. So the whole layer
 *    disappears when a visitor hides `reconstructed`, and the town goes back to
 *    standing on swept ground. That is the truthful behaviour.
 *  * It answers a pick. A barrel belongs to the business whose door it stands
 *    at, so clicking it opens that business's card — the same contract the
 *    signboards keep.
 *  * IT DRAWS THE OTHER HALF OF THE ORDINANCE (T-0057), and it is a second record
 *    rather than a second column on the first. Ordinance 9 names *timber, stone,
 *    brick, boxes and barrels*; the boxes and barrels are a merchant's stock on his
 *    own frontage, and the three building materials are stock of a completely
 *    different kind — they belong to a building that is GOING UP. Only one structure
 *    in this scene says it was: `lake_house_construction`, a roofless brick shell
 *    whose `function` is `hotel_under_construction`, attested. So brick, squared
 *    timber and footing stone stand on that lot and on no other, `data/yard/
 *    lot_building_material.json` argues which face each gets, and this file only
 *    draws them. They are the only things on the layer that are not timber or
 *    canvas: brick is the town's own chimney brick and stone is a bounded grey.
 *  * It draws A ROOF, once: the open-sided wagon shed at the Green Tree's yard
 *    end (T-0081), posts and plates and a lean-to over a covered wagon. It is
 *    still not a structure record and still not baked — it is derived from that
 *    inn's committed footprint the way a fence is derived from a perimeter — and
 *    the record argues which wall and how big. This file only draws it.
 *  * It draws NO PEOPLE, and the bench at the Green Tree is where that bites.
 *    The Trowbridge view of that inn shows a bench of SITTERS against its front
 *    wall; AGENTS.md's standing constraint is not relaxed by a plate, so what is
 *    taken from the picture is the bench and the sitters stay reference. A bench
 *    with nobody on it is the honest half of that image.
 *  * It draws NO DRAFT ANIMALS either, and after T-0064 that is the constraint
 *    with the most geometry hanging off it. Sixty-eight wagons — farm boxes,
 *    covered emigrant wagons and two-wheeled carts — stand at the verges of this
 *    town's streets and in its working yards — and every one of them stands
 *    UNHITCHED, because this project models no animal in the scene at all
 *    (`fauna.js` is a card, not a herd). A wagon's tongue and a cart's shafts lie
 *    DOWN ON THE GROUND at their own inclination, and the covered wagons and the
 *    yard wagons have an ox-yoke lying on the grass beside them. The yoke is the
 *    honest half of a team, the same way the empty bench is the honest half of
 *    the Trowbridge sitters.
 *  * T-0759 ADDS ONE MORE VEHICLE AND IT IS NOT ON A STREET. Andreas's Water
 *    Works section says how this town drank in 1835 — from the lake, by cart —
 *    and describes the vehicle exactly: "two wheeled vehicles, upon which
 *    hogsheads were mounted", driven into the water "generally at the foot of
 *    Randolph Street". So `buildCart` gained a cask, mounted when the record
 *    says `hogshead`, and `data/yard/town_water_cart.json` stands ONE of them
 *    at the point Randolph's committed line meets the committed waterline. One,
 *    and only there: the same sentence sends the watermen "around town" to
 *    "their customers' houses" and names no street, no door and no count, and
 *    dealing barrels to doors off that would be inventing a business's customer
 *    list. What is refused is written on the record, not only here.
 */

import * as THREE from 'three';
import { resolveBases } from './scene-loader.js';
import { loadTimberRelief } from './frontage.js';

/** attested · inferred · reconstructed, as the confidence view reads them. */
const LEVEL = { attested: 0, documented: 0, inferred: 0.5, reconstructed: 1 };

/**
 * THE OBJECTS' SECTIONS, AND WHY THESE NUMBERS ARE SPLIT THE WAY THEY ARE. The
 * record owns everything that is a CLAIM — a barrel's height and girth, a case's
 * size, the wagon's body and wheels are all in `form`, graded and noted there,
 * because they are inventions about the town. What is here is only how those
 * numbers are turned into triangles: how many staves a barrel is drawn with, how
 * many spokes a wheel gets, how thick a rim is. Those are the renderer's, the
 * same division `enclosures.js` makes between a fence's line and a rail's
 * thickness, and a visitor who hides `reconstructed` loses all of it either way.
 */
const BARREL_SIDES = 12;
const WHEEL_SIDES = 16;
/**
 * T-0064 CUT TWO OF THESE, and both cuts are the same argument the barrel's
 * missing hoops already make: triangles spent on something the eye cannot
 * resolve. The wheel kept its 12 sides — a 1.37 m wheel at 10 would show its
 * facets to anyone standing beside it, and T-2121 took it to 16 when the owner
 * stood beside one and saw a dodecagon — but a wheel used to carry SIX spoke
 * boxes (twelve spokes' worth) where five reads identically at any distance a
 * visitor can be, and its hub was a 10-sided cask 9 cm in radius, which is a
 * cylinder drawn finer than the plank next to it. Together that is 32 triangles off
 * every wheel — 128 off a four-wheeled wagon, 64 off a cart, 7,744 across the
 * sixty-eight now standing — and it is part of what pays for them (T-0115's
 * ledger).
 */
const WHEEL_SPOKES = 5;
const HUB_SIDES = 6;
const WHEEL_RIM_M = 0.09;    // the felloe's radial depth
const WHEEL_T_M = 0.07;      // the tyre's width
const HUB_R_M = 0.09;
const SPOKE_T_M = 0.032;
const AXLE_T_M = 0.05;
const TONGUE_T_M = 0.055;

/**
 * THE RUNNING GEAR'S SECTIONS (T-0087). Only the sections are here; every
 * POSITION the gear takes is derived in `buildWagon` from numbers the record
 * already owns — the two wheel diameters, the body's length and width, and the
 * bed height — because that is what the members physically are. A bolster is
 * exactly as deep as the space between its axle and the floor it carries; the
 * reach runs from the top of the front axle to the underside of the rear one.
 * Change `wagon_body_m` or a wheel and the gear follows, which is the point:
 * the gap this closes was a gap precisely because nothing was derived from
 * those numbers at all.
 *
 * Recorded nowhere, so RECONSTRUCTED at the tier (docs/LIBERTIES.md L138),
 * bounded by the recorded wheel diameters and body — no dimension here is free
 * to be anything, because the box has to land on the bolsters and the bolsters
 * have to land on the axles.
 */
const BOLSTER_T_M = 0.11;    // a bolster's fore-and-aft thickness
const BOLSTER_OUT_M = 0.06;  // how far its end shows past the box's side
const REACH_W_M = 0.09;      // the coupling pole, across
const HOUND_W_M = 0.07;      // a hound, across
const HOUND_BACK_M = 0.45;   // how far the hounds reach back past the front axle
const KINGBOLT_T_M = 0.038;  // the pivot pin, square-sectioned like every other
                             // small timber on this layer
const KINGBOLT_DROP_M = 0.05; // and how far its nut shows below the front axle

/**
 * The layer's own timber tone, and it is deliberately NOT the fence's. The
 * enclosures are weathered post-and-rail at 0x8d8272 and the boards are the
 * archetype's silvered plank; a cask and a packing case are newer wood, out of a
 * cooperage or off a schooner, so they read a shade warmer and darker. Like
 * `signage.js`'s note: `ColorManagement.enabled` is true and `setHex` reads
 * sRGB, so this is the hex, not a linear triple copied from a generator.
 */
const GOODS_COLOUR = 0x8a7a5f;

/**
 * And the tilt's canvas, which is the one thing on this layer that is not wood.
 * A wagon cover of the period is hemp or cotton duck, weathered and grey-buff
 * rather than white — white canvas at noon would be the brightest thing in the
 * town. Carried as a VERTEX COLOUR so the layer keeps one material and one draw
 * call: `mat.color` is left white and every vertex is tinted, which is also why
 * `THREE.Color` is used to convert (the attribute is read in the working colour
 * space, so an sRGB hex pushed raw would be visibly wrong).
 */
const CANVAS_COLOUR = 0xbfb49b;

/**
 * THE WEATHERED WOODS (T-2121). The owner, 2026-10-05: the barrels were "so janky
 * compared to what else you have done", and the wagons "look eerily similar" — make
 * them "different colors weathered wood like we did with the plank sidewalks". One
 * goods tone dealt to every cask, case and wagon in town is exactly what reads as a
 * copy, so each object is now DEALT a wood from these, seeded on its own id or place,
 * and then shaded a little lighter or darker again, piece by piece.
 *
 * RECONSTRUCTED (docs/LIBERTIES.md L384), bounded by what this town already ships:
 * the silvered end sits by the fences' weathered 0x8d8272 and the outbuildings' grey
 * pine; the warm end by the goods' old 0x8a7a5f and the board face's own mean
 * (rgb 126/112/91). Oak casks run browner than pine cases because white oak is a
 * browner wood; none of these is a claim about any one object.
 */
const WOODS = {
  silver: 0x7e786d,      // pine or oak a few summers out: bleached grey
  greybrown: 0x86796a,   // weathered, not yet silvered
  pine: 0xa08a68,        // seasoned pine, the colour of a packing case
  honey: 0x96744f,       // newer oak, warm
  oak: 0x7b644b,         // white oak staves, brown
  darkoak: 0x5f4c3b,     // oak dark with wet, tar or age
};
/** Who gets which wood, and how often — weights, not shares of anything recorded. */
const WOOD_DEALS = {
  barrel: [['oak', 4], ['honey', 2], ['greybrown', 3], ['darkoak', 2], ['silver', 1]],
  crate: [['pine', 3], ['silver', 2], ['greybrown', 2], ['honey', 1]],
  timber: [['greybrown', 3], ['silver', 3], ['pine', 2], ['oak', 1]],
};
/**
 * A WAGON IS OFTEN PAINTED, and that is the period's own answer to "eerily similar".
 * The freight wagon of the 1830s is remembered blue in the body and red in the gear,
 * and the farm wagon after it in the same pair or bare; so a share of the wagons and
 * carts here wear a FADED paint — the grain shows through, as worn paint on a board
 * does — and the rest are bare wood of the woods above. RECONSTRUCTED (the same
 * liberty): no wagon in this town has a recorded colour.
 */
const WAGON_PAINT = {
  blue: 0x5e7080,        // Prussian blue, faded chalky by the sun
  red: 0x8a5040,         // Venetian red body
  green: 0x6b735c,       // a dull green, the least common
  oxide: 0x7a4536,       // red-oxide running gear
};
const WAGON_SCHEMES = [
  // [weight, body, gear] — a wood name or a paint name
  [3, 'blue', 'oxide'], [2, 'red', 'oxide'], [1, 'green', 'oxide'],
  [1, 'blue', 'greybrown'],
  [2, 'greybrown', 'greybrown'], [2, 'silver', 'silver'], [1, 'oak', 'darkoak'],
  [1, 'pine', 'oxide'],
];
/** Iron — a tyre, a hoop, a stake's band: black gone rusty. */
const IRON_COLOUR = 0x3d3631;
/** A split-wood hoop: hickory or ash, paler than the staves it binds. */
const WOOD_HOOP_COLOUR = 0xa38d6a;

/** Pick from `[[name, weight], ...]` with a 0..1 draw. */
function dealFrom(list, r) {
  const total = list.reduce((a, [, w]) => a + w, 0);
  let x = r * total;
  for (const [name, w] of list) { x -= w; if (x < 0) return name; }
  return list[list.length - 1][0];
}
/** A tone triple in the working colour space, `k` lighter or darker. */
const toneCache = new Map();
function toneOf(name, k = 1) {
  const hex = WOODS[name] ?? WAGON_PAINT[name] ?? name;
  const key = `${hex}:${k.toFixed(3)}`;
  let t = toneCache.get(key);
  if (!t) {
    const c = new THREE.Color(hex).multiplyScalar(k);
    t = [c.r, c.g, c.b];
    toneCache.set(key, t);
  }
  return t;
}

/** A wagon side's stake, square (T-2121). */
const WAGON_STAKE_M = 0.05;
/** A packing case's end cleat: its face and how far it stands proud (T-2121). */
const CRATE_CLEAT_M = [0.07, 0.018];

/** The tilt: how many facets the canvas arch is drawn with. */
const TILT_SEGS = 8;

/**
 * THE TWO TONES THE BUILDING MATERIAL BRINGS (T-0057), and only one of them is new.
 *
 * BRICK IS NOT NEW. It is this town's ONE brick — `generators/common/materials.py`'s
 * `CHIMNEY_BRICK`, off the Petford watercolour's brick chimneys, and the same brick
 * every framed house in the scene carries on its stack. It is written here as the
 * sheet's own LINEAR triple rather than as an sRGB hex, which is why this constant is
 * a `setRGB` and its neighbours are `setHex`: a glTF base colour factor is linear by
 * definition and `THREE.Color.setRGB` defaults to the working colour space, so the two
 * agree by construction instead of by a conversion somebody did once.
 *
 * STONE IS NEW, and the material sheet has no row for it — its `stone` substrate
 * carries a roughness and no colour, because the one record that uses it says bare
 * masonry is unattested here. So the tone is RECONSTRUCTED and bounded by two values
 * this project already ships. It is paler and greyer than the layer's own timber
 * (0x8a7a5f), or a heap of footing stone stops reading as stone beside the sticks
 * piled next to it; and it is darker than the chinking clay the log walls are daubed
 * with (linear 0.700/0.670/0.590), which is the same mineral sitting sheltered under
 * an eave while a heap in a yard takes the weather. docs/LIBERTIES.md L173.
 */
const BRICK_LINEAR = [0.45, 0.23, 0.17];
const STONE_COLOUR = 0xa8a49b;

/**
 * T-1961's two new tones, both RECONSTRUCTED (docs/LIBERTIES.md L351). Hay cured
 * in a rick weathers from green-gold to a dull straw on its outside within weeks,
 * so the rick is drawn the dull straw of an old stack rather than fresh-cut gold,
 * and darker than the canvas tilt so it does not out-shine it. A green hide drying
 * over a rail is a raw brown, darker than any timber on this layer.
 */
const HAY_COLOUR = 0xa89160;
const HIDE_COLOUR = 0x5e4231;

/**
 * The stone heap's own yaw and stagger, which are the RENDERER's the way the barrel's
 * stave count is: the record says nine blocks in two tiers, and how each one happens
 * to be lying is not a claim anybody can make about a heap of rubble. Fixed numbers,
 * not a random deal — a load that changed shape between two loads of the same page
 * would be a lottery, and this layer has never had one.
 */
const STONE_YAW_DEG = [0, 34, -21, 12, -47, 63, -8, 27, -35];
const STONE_JITTER = [
  [-0.62, -0.20], [0.08, -0.26], [0.70, -0.14], [-0.30, 0.24], [0.42, 0.20],
  [-0.72, 0.16], [0.00, 0.02], [0.58, 0.30], [-0.16, -0.02],
];

/**
 * THE CART'S SHAFTS AND THE YOKE'S BOWS (T-0064) — sections only, as everywhere
 * else on this layer. How long a shaft is and how wide a yoke's beam are the
 * record's claims (`cart_m`, `ox_yoke_m`); how thick the stick is drawn is the
 * renderer's, exactly as the barrel's stave count and the wheel's spokes are.
 */
const SHAFT_T_M = 0.045;
const CART_SHAFT_GAUGE_M = 0.62;   // between the two shafts, at their roots
const YOKE_BOW_DROP_M = 0.10;      // how far a bow's end shows below the beam

/**
 * How far a chunk may reach before the layer starts a new one, in metres of
 * ground. Deliberately larger than the fences' 30 m: a fence is a continuous run
 * of very small boxes and chunking it finely costs nothing, while the goods are
 * a few dozen isolated objects spread over a square kilometre — small buckets
 * here would buy culling at the price of a draw call per wagon, and draw calls
 * are the tightest number in this scene (T-0115). At 110 m a chunk remains about
 * a platted block and a half. T-1766 measured 61 original chunks at 100 m plus
 * four lazy far-merge meshes: 65 after walking the town, over the 64-mesh limit.
 * The 110 m grid gives 55 originals plus at most two far merges (57), leaving
 * room without changing a vertex, material or pick span. Each chunk still has
 * its own bounding sphere; this trades a 10% wider cell for fewer submissions.
 * T-1961 put goods in 29 working yards, eight of them in cells nothing stood in:
 * 60 chunks became 68 at 110 m. At 120 m the town is 60 again — the same draw
 * calls as before the trade yards, under the same ceiling.
 */
const CHUNK_M = 120;

/** The shed's roof boards, as thick as a board and no thicker. */
const DECK_T_M = 0.04;

/* -------------------------------------------------------------------------- */
/* the marks (T-0065)                                                          */
/* -------------------------------------------------------------------------- */

/**
 * ONE CELL PER DISTINCT MARK, and the size is arithmetic rather than taste. A
 * barrel head is 0.45 m across and a case face 1.05 m; a visitor reads either
 * from about a metre and a half, where the head fills roughly a third of a
 * 1280-wide viewport. 192 px across a head is a shade over 2 px per millimetre
 * of stave, which puts a 40 px capital on the head — more is texture nobody
 * resolves and less is a smudge. The town deals about seventy distinct marks,
 * so eight columns is nine rows and the whole atlas is 1536 x 1728.
 */
const MARK_TILE = 192;
const MARK_COLS = 8;
const MARK_PAD = 8;

/**
 * THE THREE LETTERFORMS, and they are the signboards' faces one layer down
 * (`signage.js` FACES, T-0066) rather than a second invention. A browser has no
 * 1830s specimen book in it, so each is a family, a weight, a horizontal scale
 * and a tracking:
 *
 *  * STENCIL — a commodity word cut through a plate. Condensed, heavy, widely
 *    tracked, and drawn with the BRIDGES a stencil plate has to leave, which is
 *    the one thing that makes a stencil read as a stencil rather than as type.
 *  * BRAND — the house's own mark, burned into the head with a hot iron. A
 *    roman with weight, tighter, and in a browner ink than the stencil's black,
 *    because a brand is scorched wood and not paint.
 *  * SHIPPING — the consignee's mark on a case, brush-written by whoever crated
 *    it. Plain, upright, unbridged.
 *
 * The letterform is invented exactly as the boards' is (docs/LIBERTIES.md L159,
 * and L166 for this layer), and what it has to do is be legible from the footway
 * and not read as modern type.
 */
const MARK_FACES = {
  stencil: {
    family: 'Helvetica, Arial, "Liberation Sans", sans-serif',
    weight: 800, scaleX: 0.86, track: 0.14, ink: '#3a3125', bridges: true,
  },
  brand: {
    family: 'Georgia, "Times New Roman", Times, serif',
    weight: 700, scaleX: 0.98, track: 0.06, ink: '#4a3a24', bridges: false,
  },
  shipping: {
    family: 'Georgia, "Times New Roman", Times, serif',
    weight: 600, scaleX: 0.94, track: 0.09, ink: '#37301f', bridges: false,
  },
};

/** How much of a cell the lettering is allowed, by what it is painted on. */
const MARK_BOX = {
  // A head is a disc inscribed in its cell, so a block wider than this would run
  // off the chine: at 0.78 x 0.46 the corners sit at 0.90 of the radius.
  head: [0.78, 0.46],
  case: [0.88, 0.68],
  // A bilge is a band around the belly of a standing cask, so the lettering runs
  // the full width of the arc and takes a third of its height — which is where a
  // stencil goes on a barrel, and is the only face of one a visitor reads from
  // the footway without looking down into it.
  bilge: [0.92, 0.34],
};

/**
 * How much of a cask's circumference the bilge mark is painted across, in
 * STAVES. Three of the ten is 108 degrees, which is the widest arc that still
 * turns its whole face toward one reader: at four the outer stave is 72 degrees
 * off and reads as a smear.
 */
const BILGE_STAVES = 3;

/** The key two marks share iff they can share a cell. */
function markKey(mark, shape) {
  return `${shape}|${mark.letterform}|${mark.lines.join('|')}`;
}

/** The width one line takes, tracking and horizontal scale included. */
function markLineWidth(ctx, str, size, face) {
  ctx.font = `${face.weight} ${size}px ${face.family}`;
  let w = 0;
  for (const ch of str) w += ctx.measureText(ch).width;
  if (str.length > 1) w += face.track * size * (str.length - 1);
  return w * face.scaleX;
}

/** One line, centred, letter by letter so the tracking is real. */
function markDrawLine(ctx, str, cx, cy, size, face) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.scale(face.scaleX, 1);
  ctx.font = `${face.weight} ${size}px ${face.family}`;
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';
  const tr = face.track * size;
  let w = 0;
  for (const ch of str) w += ctx.measureText(ch).width;
  if (str.length > 1) w += tr * (str.length - 1);
  let x = -w / 2;
  for (const ch of str) {
    ctx.fillText(ch, x, 0);
    x += ctx.measureText(ch).width + tr;
  }
  ctx.restore();
}

/**
 * One mark's cell: white everywhere the paint is not, because the map MULTIPLIES
 * the timber tone the vertices already carry. A ground of anything but white
 * would repaint the whole barrel, and a mark is paint on wood, not a new wood.
 *
 * Returns the sub-rectangle, in canvas pixels, that the marked face samples —
 * square for a barrel head, the case's own aspect for a case face — so the
 * letters are not stretched when the quad reads them.
 */
function paintMark(ctx, x, y, mark, shape, aspect) {
  const face = MARK_FACES[mark.letterform] || MARK_FACES.stencil;
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(x, y, MARK_TILE, MARK_TILE);
  const inner = MARK_TILE - 2 * MARK_PAD;
  let rw = inner;
  let rh = inner / (aspect || 1);
  if (rh > inner) { rh = inner; rw = inner * (aspect || 1); }
  const rx = x + MARK_PAD + (inner - rw) / 2;
  const ry = y + MARK_PAD + (inner - rh) / 2;

  const [boxW, boxH] = MARK_BOX[shape];
  const maxW = rw * boxW;
  const maxH = rh * boxH;
  const lines = mark.lines.filter(Boolean);
  if (!lines.length) return { rx, ry, rw, rh };
  // The type is what gives way: the words are a given and the head is a size.
  let lo = 4;
  let hi = Math.ceil(rh);
  while (lo < hi) {
    const mid = Math.ceil((lo + hi + 1) / 2);
    const fits = lines.length * mid * 1.22 <= maxH
      && lines.every((l) => markLineWidth(ctx, l, mid, face) <= maxW);
    if (fits) lo = mid; else hi = mid - 1;
  }
  const size = lo;
  if (size < 5) return { rx, ry, rw, rh };
  const lh = size * 1.22;
  const top = ry + rh / 2 - ((lines.length - 1) * lh) / 2;
  ctx.fillStyle = face.ink;
  for (let i = 0; i < lines.length; i += 1) {
    markDrawLine(ctx, lines[i], rx + rw / 2, top + i * lh, size, face);
  }
  // THE BRIDGES, and they are what a stencil IS. A plate cannot cut a closed
  // counter loose, so every stencil letterform of the period carries ties
  // across its strokes; two thin ones through the cap height read as a stencil
  // at any distance a visitor can be, and cost two rectangles.
  if (face.bridges) {
    ctx.fillStyle = '#ffffff';
    const t = Math.max(1, size * 0.075);
    for (let i = 0; i < lines.length; i += 1) {
      const cy = top + i * lh;
      for (const at of [-0.20, 0.22]) {
        ctx.fillRect(rx + rw / 2 - maxW / 2, cy + size * at - t / 2, maxW, t);
      }
    }
  }
  return { rx, ry, rw, rh };
}

/**
 * Lay every distinct mark in the town on one canvas and hand back the texture
 * plus, per mark, the uv rectangle its face samples.
 *
 * Cell 0 is left BLANK — pure white — and everything on this layer that carries
 * no mark samples a single point inside it. That is what lets a textured
 * material draw a barrel, a wagon and a wagon shed exactly as they were drawn
 * before this file had a texture at all: white multiplies to nothing.
 *
 * `null` when there is no document to draw on (a headless parse of this module,
 * or a browser that refuses a 2d context) — the caller then draws untextured
 * timber, which is the layer as T-0040 shipped it and is a degradation rather
 * than a failure.
 */
function buildMarkAtlas(wanted) {
  if (typeof document === 'undefined') return null;
  const keys = [...wanted.keys()].sort();
  const cells = keys.length + 1;                    // + the blank
  const rows = Math.max(1, Math.ceil(cells / MARK_COLS));
  const canvas = document.createElement('canvas');
  canvas.width = MARK_COLS * MARK_TILE;
  canvas.height = rows * MARK_TILE;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const W = canvas.width;
  const H = canvas.height;
  const rects = new Map();
  keys.forEach((key, i) => {
    const cell = i + 1;
    const x = (cell % MARK_COLS) * MARK_TILE;
    const y = Math.floor(cell / MARK_COLS) * MARK_TILE;
    const { mark, shape, aspect, paint } = wanted.get(key);
    // A wood cell (T-1959) paints itself; a mark is lettering on a shape.
    const r = paint ? paint(ctx, x, y) : paintMark(ctx, x, y, mark, shape, aspect);
    // Canvas y runs down and uv v runs up, so the rect's top edge is v1.
    rects.set(key, {
      u0: r.rx / W, u1: (r.rx + r.rw) / W,
      v0: 1 - (r.ry + r.rh) / H, v1: 1 - r.ry / H,
    });
  });
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  texture.needsUpdate = true;
  return {
    texture,
    rects,
    // dead centre of the blank cell, far from any painted neighbour
    blank: [(MARK_TILE / 2) / W, 1 - (MARK_TILE / 2) / H],
    cells,
    size: [W, H],
  };
}

/* -------------------------------------------------------------------------- */
/* primitives                                                                  */
/* -------------------------------------------------------------------------- */

/**
 * THE GRAIN AND THE WEATHER (T-2121), and how every primitive below writes them.
 *
 * Each vertex carries a second uv, `uv1`, in METRES of the board face the plank
 * walks wear (`frontage.js`, T-1815): `u` runs along the grain, `v` across it, and
 * each piece starts the tile at its own seeded offset so two staves or two boards
 * never show the same figure. The material binds that face's normal map and its
 * albedo modulation on `uv1`, so a barrel, a case and a wagon side carry the same
 * raised grain and checks as the walk they stand on. Anything that is not wood —
 * the tilt's duck, an iron tyre or hoop, brick, stone, hay, a hide, a woodpile's
 * painted cells — writes the NO_GRAIN sentinel and the shader leaves it flat.
 *
 * The buffer carries the state the current object is drawn in, set by its builder
 * and restored after it: `tint` (its tone), `k` (a multiplier, for end grain and a
 * piece's own spread), `ground` (the grade it stands on, for the contact darkening),
 * `grainAxis` and `grainOff` (which way its grain runs and where on the tile it
 * starts), and `grainOn` (false for a whole chunk that is never wood).
 */
const NO_GRAIN = [-8192, -8192];
/** End grain reads darker than face grain — the frontage's own 0.72 (L320). */
const END_GRAIN_K = 0.72;
/**
 * Contact: the foot of anything standing in the mud carries the mud. Darkened by up to
 * this much at grade, fading out over CONTACT_M — the frontage's contact rule (L320) at
 * the scale of a barrel rather than a post.
 */
const CONTACT_K = 0.32;
const CONTACT_M = 0.22;
/** How deep the grain's relief reads on the goods (the walk's is 1). */
const GRAIN_NORMAL_SCALE = 1.35;
/** The board face's tile, metres — `clapboard_board_face`'s span_m. */
const GRAIN_TILE_M = 4.48;

/** A stable 32-bit hash of a string or number list (FNV-1a). */
function hashOf(...parts) {
  const s = parts.join('|');
  let h = 2166136261;
  for (let i = 0; i < s.length; i += 1) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
/** A seeded 0..1 stream — the same object draws the same way on every load. */
function streamOf(seed) {
  let s = seed >>> 0 || 1;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
/** Where a piece of timber starts on the tile, seeded on where it lies (to the cm). */
function seededOff(x, y, z) {
  const r = streamOf(hashOf(Math.round(x * 100), Math.round(y * 100), Math.round(z * 100)));
  return [r() * GRAIN_TILE_M, r() * GRAIN_TILE_M];
}

function isGrained(buf) {
  return buf.grainOn !== false && !(buf.bare && buf.bare.has(buf.tint));
}
function unit3(v) {
  const L = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / L, v[1] / L, v[2] / L];
}
function cross3(a, b) {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}
function dot3(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }

/**
 * The grain uv of a flat face: `u` along the buffer's grain axis laid into the face,
 * `v` across it. A face the grain runs INTO (a timber's end) has no along — it takes
 * the next axis instead, and its tone is the caller's end-grain business.
 */
function planarGrain(buf, P, fn) {
  if (!isGrained(buf)) return null;
  const axis = buf.grainAxis ?? [0, 1, 0];
  let g = [axis[0] - fn[0] * dot3(axis, fn), axis[1] - fn[1] * dot3(axis, fn),
    axis[2] - fn[2] * dot3(axis, fn)];
  if (Math.hypot(g[0], g[1], g[2]) < 0.3) {
    const alt = Math.abs(fn[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
    g = [alt[0] - fn[0] * dot3(alt, fn), alt[1] - fn[1] * dot3(alt, fn),
      alt[2] - fn[2] * dot3(alt, fn)];
  }
  g = unit3(g);
  const w = cross3(fn, g);
  const [ou, ov] = buf.grainOff ?? [0, 0];
  return P.map((p) => [dot3(p, g) + ou, dot3(p, w) + ov]);
}

/** One vertex, with every stream the layer carries. */
function emitV(buf, p, n, level, uv, g, k) {
  buf.pos.push(p[0], p[1], p[2]);
  buf.nrm.push(n[0], n[1], n[2]);
  buf.conf.push(level);
  // `buf.tint` is the colour the caller is currently drawing in, in the renderer's
  // working colour space; `k` is the piece's own spread and the end grain, and the
  // contact term darkens what stands within a hand of the grade it stands on.
  let m = k * (buf.k ?? 1);
  if (buf.ground != null) {
    const above = Math.max(0, p[1] - buf.ground);
    m *= 1 - CONTACT_K * Math.max(0, 1 - above / CONTACT_M);
  }
  buf.col.push(buf.tint[0] * m, buf.tint[1] * m, buf.tint[2] * m);
  // And `buf.blank` is the white cell of the mark atlas (T-0065). Everything that is
  // not a marked face samples it, which multiplies to exactly the timber's own tone.
  const t = uv ?? buf.blank;
  buf.uv.push(t[0], t[1]);
  const q = g ?? NO_GRAIN;
  buf.uv1.push(q[0], q[1]);
}

/**
 * One box, 12 triangles, flat-shaded from its own face normals. `u` is the
 * horizontal unit vector along the box's length; up is world Y always.
 * Deliberately the same helper shape as the enclosure and signage layers' —
 * three layers drawing small timber the same way is one thing to reason about.
 *
 * ITS GRAIN RUNS ALONG ITS LONGEST SIDE (T-2121), as the walk's boards do — along a
 * plank, up a post, along a bolster — and the two faces the grain runs into are its
 * END GRAIN, drawn a half stop darker.
 */
function pushBox(buf, cx, cy, cz, ux, uz, halfLen, halfW, halfH, level,
  markRect = null, open = false) {
  const vx = -uz;
  const vz = ux;
  const P = (a, b, c) => [
    cx + ux * a * halfLen + vx * b * halfW,
    cy + c * halfH,
    cz + uz * a * halfLen + vz * b * halfW,
  ];
  const p = [
    P(-1, -1, -1), P(1, -1, -1), P(1, 1, -1), P(-1, 1, -1),
    P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1),
  ];
  const faces = [
    [[1, 5, 6], [1, 6, 2], [ux, 0, uz], 0],
    [[4, 0, 3], [4, 3, 7], [-ux, 0, -uz], 0],
    [[3, 2, 6], [3, 6, 7], [vx, 0, vz], 1],
    [[0, 4, 5], [0, 5, 1], [-vx, 0, -vz], 1],
    [[4, 7, 6], [4, 6, 5], [0, 1, 0], 2],
    [[0, 1, 2], [0, 2, 3], [0, -1, 0], 2],
  ];
  // The grain's axis: whichever of the three half-extents is longest.
  const ext = [halfLen, halfW, halfH];
  const along = ext[0] >= ext[1] && ext[0] >= ext[2] ? 0 : (ext[1] >= ext[2] ? 1 : 2);
  const axes = [[ux, 0, uz], [vx, 0, vz], [0, 1, 0]];
  const keepAxis = buf.grainAxis;
  const keepOff = buf.grainOff;
  buf.grainAxis = axes[along];
  if (!buf.pieceOff) buf.grainOff = seededOff(cx, cy, cz);
  /**
   * THE MARKED FACE IS FACE 3, and which one that is falls out of the frame
   * rather than out of a preference. `u` is along the wall and `v` is `u`
   * turned left, so the face whose normal is `-v` is the one looking AWAY from
   * the wall the goods stand at — the street side, the only side of a packing
   * case anybody reads. Its four corners are p0, p4, p5, p1, at (a, c) of
   * (-1,-1), (-1,1), (1,1) and (1,-1); the vertical of the mark runs with `c`
   * and its horizontal runs with `-a`, because screen-right for a viewer
   * standing off `-v` with world up is `forward x up` = `v x y` = `-u`. The
   * sign is not a taste and it is not guessable: with `+a` the whole town's
   * cases came out mirror-written, which is what caught it.
   */
  const CORNER = { 0: [1, 0], 4: [1, 1], 5: [0, 1], 1: [0, 0] };
  const uvAt = (i) => {
    const [sx2, ty] = CORNER[i];
    return [markRect.u0 + sx2 * (markRect.u1 - markRect.u0),
      markRect.v0 + ty * (markRect.v1 - markRect.v0)];
  };
  faces.forEach(([t1, t2, n, axis], fi) => {
    // `open` leaves the underside off a box lying on the ground (T-1959): two
    // triangles nobody can see, on several hundred small things.
    if (open && fi === 5) return;
    const marked = markRect && fi === 3;
    const k = axis === along ? END_GRAIN_K : 1;
    for (const t of [t1, t2]) {
      const pts = t.map((i) => p[i]);
      const g = planarGrain(buf, pts, n);
      t.forEach((i, j) => emitV(buf, p[i], n, level, marked ? uvAt(i) : null,
        g ? g[j] : null, k));
    }
  });
  buf.grainAxis = keepAxis;
  buf.grainOff = keepOff;
}

/**
 * One triangle. `n` is its normal, or three per-vertex normals; `uvs` the atlas
 * coordinates of a marked or painted face; `g` explicit grain coordinates, which
 * default to the face projected on the buffer's grain axis.
 */
function tri(buf, a, b, c, n, level, uvs = null, g = null, k = 1) {
  const P = [a, b, c];
  const N = Array.isArray(n[0]) ? n : null;
  let grain = g;
  if (!grain && isGrained(buf)) {
    const fn = unit3(cross3([b[0] - a[0], b[1] - a[1], b[2] - a[2]],
      [c[0] - a[0], c[1] - a[1], c[2] - a[2]]));
    grain = planarGrain(buf, P, fn);
  }
  if (g && !isGrained(buf)) grain = null;
  for (let i = 0; i < 3; i += 1) {
    emitV(buf, P[i], N ? N[i] : n, level, uvs ? uvs[i] : null, grain ? grain[i] : null, k);
  }
}

/**
 * A box given as a centre and three half-edge vectors, for the timber `pushBox`
 * cannot draw: a rafter and a roof deck are SLOPED, and `pushBox`'s long axis is
 * horizontal by construction. The three vectors must be mutually perpendicular —
 * every caller builds them from one cross product, so they are.
 */
function pushBoxV(buf, c, ea, eb, ec0, level) {
  // A box is symmetrical in each of its three axes, so flipping one half-edge
  // changes nothing about the solid — and it is what makes the winding below
  // right whichever way round a caller happened to build its frame.
  const hand = (ea[1] * eb[2] - ea[2] * eb[1]) * ec0[0]
    + (ea[2] * eb[0] - ea[0] * eb[2]) * ec0[1]
    + (ea[0] * eb[1] - ea[1] * eb[0]) * ec0[2];
  const ec = hand < 0 ? [-ec0[0], -ec0[1], -ec0[2]] : ec0;
  const P = (a, b, d) => [
    c[0] + ea[0] * a + eb[0] * b + ec[0] * d,
    c[1] + ea[1] * a + eb[1] * b + ec[1] * d,
    c[2] + ea[2] * a + eb[2] * b + ec[2] * d,
  ];
  const na = unit3(ea);
  const nb = unit3(eb);
  const nc = unit3(ec);
  const neg = (v) => [-v[0], -v[1], -v[2]];
  // T-2121: the grain runs along the longest half-edge, as `pushBox`'s does.
  const lens = [ea, eb, ec].map((v) => Math.hypot(v[0], v[1], v[2]));
  const along = lens[0] >= lens[1] && lens[0] >= lens[2] ? 0 : (lens[1] >= lens[2] ? 1 : 2);
  const keepAxis = buf.grainAxis;
  const keepOff = buf.grainOff;
  buf.grainAxis = [na, nb, nc][along];
  if (!buf.pieceOff) buf.grainOff = seededOff(c[0], c[1], c[2]);
  const faces = [
    [P(1, -1, -1), P(1, 1, -1), P(1, 1, 1), P(1, -1, 1), na, 0],
    [P(-1, 1, -1), P(-1, -1, -1), P(-1, -1, 1), P(-1, 1, 1), neg(na), 0],
    [P(-1, 1, -1), P(-1, 1, 1), P(1, 1, 1), P(1, 1, -1), nb, 1],
    [P(-1, -1, 1), P(-1, -1, -1), P(1, -1, -1), P(1, -1, 1), neg(nb), 1],
    [P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1), nc, 2],
    [P(1, -1, -1), P(-1, -1, -1), P(-1, 1, -1), P(1, 1, -1), neg(nc), 2],
  ];
  for (const [a, b, d, e, n, axis] of faces) {
    const k = axis === along ? END_GRAIN_K : 1;
    tri(buf, a, b, d, n, level, null, null, k);
    tri(buf, a, d, e, n, level, null, null, k);
  }
  buf.grainAxis = keepAxis;
  buf.grainOff = keepOff;
}

/**
 * A triangle wound to face `out` whatever order its corners arrive in — the cask
 * below is built in a frame its callers turn every way, and a head wound inward is
 * a lid the back-face cull throws away (the open-topped casks T-2121 was filed on).
 * Swaps the second and third corner, with everything that rides on them.
 */
function triOut3(buf, P, N, out, level, uvs = null, g = null, k = 1) {
  const x = cross3([P[1][0] - P[0][0], P[1][1] - P[0][1], P[1][2] - P[0][2]],
    [P[2][0] - P[0][0], P[2][1] - P[0][1], P[2][2] - P[0][2]]);
  if (dot3(x, out) >= 0) {
    tri(buf, P[0], P[1], P[2], N, level, uvs, g, k);
    return;
  }
  const sw = (q) => (q ? [q[0], q[2], q[1]] : null);
  tri(buf, P[0], P[2], P[1], Array.isArray(N[0]) ? sw(N) : N, level, sw(uvs), sw(g), k);
}

/**
 * THE STAVE PROFILE, as fractions of the half-length from the belly (0) to the
 * chine (1): the ring edges a hoop sits between. A cask of the period was hooped
 * either with split-wood hoops — hickory or ash, wide and bound in pairs, what
 * slack flour and provision barrels carried — or with iron bands, narrower and dark;
 * both a head hoop near each chine and a quarter hoop either side of the bilge.
 * RECONSTRUCTED (docs/LIBERTIES.md L384): the widths are a cooper's proportions,
 * not a measurement of any cask in this town.
 */
const HOOP_RINGS = {
  wood: { rings: [0, 0.42, 0.62, 0.72, 0.94, 1], hoops: [[0.42, 0.62], [0.72, 0.94]] },
  iron: { rings: [0, 0.48, 0.58, 0.80, 0.92, 1], hoops: [[0.48, 0.58], [0.80, 0.92]] },
};
/** How far the staves stand past the head (the chime), and how thick a stave is. */
const CHIME_M = 0.028;
const STAVE_T_M = 0.02;

/**
 * A CASK (T-2121, replacing T-0040's two frusta). Staves bowed on a true bilge, read
 * as staves; hoops; the stave ends standing proud of a recessed head at each chime;
 * and lit as a round thing, with a normal per vertex rather than one per facet.
 *
 * WHAT WAS WRONG WITH THE OLD ONE, in the owner's word "janky": its two heads were
 * wound inward, so the back-face cull threw them away and every cask in the town was
 * an open tube; and each stave was two triangles lit by two different normals, the
 * one through its top corner and the one through its bottom, so ten staves read as
 * twenty zigzag teeth. Both are gone by construction — `triOut3` winds every face to
 * its own outward normal, and the normals come from the surface, not from a corner.
 *
 * `axis` is a unit vector — up for a barrel standing on its head, horizontal for one
 * laid on its side — and `right` is any unit vector across it. `o`:
 *   sides       staves (12; a wheel hub passes 6)
 *   plain       a hub: belly ring, flat heads, no hoops, no chime
 *   hoops       'wood' | 'iron'; `hoopTint` the hoops' tone
 *   capLow      false for a cask standing on its low head: nobody sees under it
 *   rng         the cask's own stream, for each stave's tone and grain
 *   headMark / sideMark   as T-0065 dealt them (see below)
 */
function pushCask(buf, cx, cy, cz, axis, right, len, bellyR, headR, level, o = {}) {
  const sides = o.sides ?? BARREL_SIDES;
  const plain = !!o.plain;
  const rng = o.rng ?? (() => 0.5);
  const headMark = o.headMark ?? null;
  const sideMark = o.sideMark ?? null;
  const [ax, ay, az] = axis;
  const [rx, ry, rz] = right;
  // the third axis of the frame, right × axis
  const sx = ry * az - rz * ay;
  const sy = rz * ax - rx * az;
  const sz = rx * ay - ry * ax;
  const dir = (k) => [rx * Math.cos(k) + sx * Math.sin(k), ry * Math.cos(k) + sy * Math.sin(k),
    rz * Math.cos(k) + sz * Math.sin(k)];
  const half = len / 2;
  const at = (t, r, k) => {
    const d = dir(k);
    return [cx + ax * t + d[0] * r, cy + ay * t + d[1] * r, cz + az * t + d[2] * r];
  };
  // The bilge: a parabola from the head's radius at each chine to the belly's at the
  // middle, which is the curve a bent stave takes to within a millimetre at this girth.
  const bulge = bellyR - headR;
  const rOf = (s) => headR + bulge * (1 - s * s);
  // The surface's own normal at (s, k): outward, tipped by the bilge's slope.
  const nAt = (s, k) => {
    const d = dir(k);
    const slope = (-2 * bulge * s) / (half || 1);       // dr/dt
    return unit3([d[0] - ax * slope, d[1] - ay * slope, d[2] - az * slope]);
  };
  const step = (Math.PI * 2) / sides;
  const ang = (i) => i * step;

  /**
   * THE BILGE MARK (T-0065), and it is painted across `BILGE_STAVES` of the
   * cask's staves rather than around the whole of it, because a stencil is a
   * plate laid against one face and not a wrapper.
   *
   * WHICH staves is `sideMark.center` — the angle, in the cask's own frame,
   * that has to face the reader. Upright, that is the outward normal of the
   * frontage; the nearest whole stave to it is taken with one either side, so
   * the painted arc is symmetric about a stave rather than about a joint.
   *
   * `u` runs BACKWARDS around the arc, and the sign is the same one the cases
   * needed: a reader standing off the cask with world up sees screen-right at
   * `forward x up`, which for a point `d` round from the centre works out as
   * `-sin d`. `v` runs up the cask, 0 at the lower chine and 1 at the upper —
   * so the lettering bows out with the staves, exactly as paint on a real cask does.
   */
  let q0 = 0;
  if (sideMark) q0 = Math.round(sideMark.center / step - 0.5);
  const first = q0 - (BILGE_STAVES - 1) / 2;
  const sideUV = (i, t) => {
    if (!sideMark) return null;
    let n2 = (i - first) % sides;
    if (n2 < 0) n2 += sides;
    if (n2 > BILGE_STAVES) return null;
    const u = 1 - n2 / BILGE_STAVES;
    return [
      sideMark.rect.u0 + u * (sideMark.rect.u1 - sideMark.rect.u0),
      sideMark.rect.v0 + t * (sideMark.rect.v1 - sideMark.rect.v0),
    ];
  };

  // ---- the staves and the hoops ------------------------------------------- //
  const spec = plain ? { rings: [0, 1], hoops: [] } : HOOP_RINGS[o.hoops ?? 'iron'];
  const ringS = [...spec.rings.slice(1).reverse().map((s) => -s), ...spec.rings];
  const inHoop = (s0, s1) => {
    const m = Math.abs((s0 + s1) / 2);
    return spec.hoops.some(([a, b]) => m > a && m < b);
  };
  const keepTint = buf.tint;
  const keepOn = buf.grainOn;
  for (let i = 0; i < sides; i += 1) {
    const j = i + 1;
    // Each stave its own board: its own place on the grain's tile and its own
    // shade of the cask's tone, so the staves read as staves.
    const ou = rng() * GRAIN_TILE_M;
    const ov = rng() * GRAIN_TILE_M;
    const kStave = 0.9 + rng() * 0.2;
    // A stave is a flat board, so its normal leans a little toward its own middle:
    // round in the light, and still a ring of boards rather than a turned post.
    const mid = ang(i) + step / 2;
    const nS = (s, k) => {
      const a2 = nAt(s, k);
      const b2 = nAt(s, mid);
      return unit3([a2[0] * 0.65 + b2[0] * 0.35, a2[1] * 0.65 + b2[1] * 0.35,
        a2[2] * 0.65 + b2[2] * 0.35]);
    };
    for (let r = 0; r < ringS.length - 1; r += 1) {
      const s0 = ringS[r];
      const s1 = ringS[r + 1];
      const hoop = inHoop(s0, s1);
      const t0 = s0 * half;
      const t1 = s1 * half;
      const A0 = at(t0, rOf(s0), ang(i));
      const B0 = at(t1, rOf(s1), ang(i));
      const B1 = at(t1, rOf(s1), ang(j));
      const A1 = at(t0, rOf(s0), ang(j));
      const N = [nS(s0, ang(i)), nS(s1, ang(i)), nS(s1, ang(j)), nS(s0, ang(j))];
      // grain: along the stave for a stave; around the cask for a split-wood hoop
      const arc0 = ang(i) * bellyR;
      const arc1 = ang(j) * bellyR;
      let G = null;
      if (hoop) {
        G = [[arc0 + ou, t0 + ov], [arc0 + ou, t1 + ov], [arc1 + ou, t1 + ov],
          [arc1 + ou, t0 + ov]];
      } else {
        G = [[t0 + ou, arc0 + ov], [t1 + ou, arc0 + ov], [t1 + ou, arc1 + ov],
          [t0 + ou, arc1 + ov]];
      }
      let U = null;
      if (!hoop && sideMark) {
        const v0 = (s0 + 1) / 2;
        const v1 = (s1 + 1) / 2;
        const u = [sideUV(i, v0), sideUV(i, v1), sideUV(i + 1, v1), sideUV(i + 1, v0)];
        if (u.every(Boolean)) U = u;
      }
      let k = kStave;
      if (hoop) {
        buf.tint = o.hoopTint ?? keepTint;
        buf.grainOn = o.hoops === 'wood' ? keepOn : false;
        k = 0.94 + (kStave - 1) * 0.3;
      }
      const out = dir(mid);
      triOut3(buf, [A0, B0, B1], [N[0], N[1], N[2]], out, level,
        U ? [U[0], U[1], U[2]] : null, [G[0], G[1], G[2]], k);
      triOut3(buf, [A0, B1, A1], [N[0], N[2], N[3]], out, level,
        U ? [U[0], U[2], U[3]] : null, [G[0], G[2], G[3]], k);
      if (hoop) { buf.tint = keepTint; buf.grainOn = keepOn; }
    }
  }

  // ---- the heads ----------------------------------------------------------- //
  /**
   * A HEAD MARK GOES ON THE `hi` HEAD (T-0065) — for the empties laid along a
   * wall, whose bilge is turned up at the sky and whose head is the one face of
   * them a visitor reads the right way up. A ring point at angle k stands at
   * `cos k` along `right` and `sin k` along the frame's third axis, so the disc
   * maps onto the cell by exactly that, up to which way round the reader is.
   *
   * UPRIGHT: the page's up is the frame's third axis and its rightward direction is
   * MINUS `right`. LAID: the page's up is world up, which for a laid cask IS `right`,
   * and its rightward direction is the third axis. `rot` selects the second.
   */
  const markUV = (k) => {
    const c = Math.cos(k);
    const sn = Math.sin(k);
    const [mx, my] = headMark.rot ? [sn, c] : [-c, sn];
    return [
      headMark.rect.u0 + (0.5 + 0.5 * mx) * (headMark.rect.u1 - headMark.rect.u0),
      headMark.rect.v0 + (0.5 + 0.5 * my) * (headMark.rect.v1 - headMark.rect.v0),
    ];
  };
  for (const e of [-1, 1]) {
    if (e < 0 && o.capLow === false) continue;
    const outN = [ax * e, ay * e, az * e];
    const marked = headMark && e > 0;
    // The head's boards run across it, along `right`.
    const headOff = [rng() * GRAIN_TILE_M, rng() * GRAIN_TILE_M];
    const headG = (p) => [dot3(p, [rx, ry, rz]) + headOff[0], dot3(p, [sx, sy, sz]) + headOff[1]];
    if (plain) {
      const ring = [];
      for (let i = 0; i < sides; i += 1) ring.push(at(e * half, headR, ang(i)));
      for (let i = 1; i < sides - 1; i += 1) {
        const P = [ring[0], ring[i], ring[i + 1]];
        triOut3(buf, P, outN, outN, level, null, P.map(headG), END_GRAIN_K);
      }
      continue;
    }
    const tRim = e * half;
    const tHead = e * (half - CHIME_M);
    const rIn = headR - STAVE_T_M;
    for (let i = 0; i < sides; i += 1) {
      const k0 = ang(i);
      const k1 = ang(i + 1);
      // the chime: the stave ends, an annulus of end grain round the rim
      const o0 = at(tRim, headR, k0);
      const o1 = at(tRim, headR, k1);
      const i0 = at(tRim, rIn, k0);
      const i1 = at(tRim, rIn, k1);
      triOut3(buf, [o0, o1, i1], outN, outN, level, null, null, END_GRAIN_K * 0.95);
      triOut3(buf, [o0, i1, i0], outN, outN, level, null, null, END_GRAIN_K * 0.95);
      // and the inside of the staves down to the head, in the cask's own shade
      const d0 = at(tHead, rIn, k0);
      const d1 = at(tHead, rIn, k1);
      const n0 = dir(k0).map((v) => -v);
      const n1 = dir(k1).map((v) => -v);
      const inward = dir((k0 + k1) / 2).map((v) => -v);
      const gi = [[0, k0 * rIn], [tRim - tHead, k0 * rIn], [tRim - tHead, k1 * rIn], [0, k1 * rIn]]
        .map(([u, v]) => [u + headOff[1], v + headOff[0]]);
      triOut3(buf, [d0, i0, i1], [n0, n0, n1], inward, level, null, [gi[0], gi[1], gi[2]], 0.62);
      triOut3(buf, [d0, i1, d1], [n0, n1, n1], inward, level, null, [gi[0], gi[2], gi[3]], 0.62);
    }
    // the head itself, recessed in its croze
    const ring = [];
    for (let i = 0; i < sides; i += 1) ring.push(at(tHead, rIn, ang(i)));
    for (let i = 1; i < sides - 1; i += 1) {
      const P = [ring[0], ring[i], ring[i + 1]];
      const uvs = marked ? [markUV(ang(0)), markUV(ang(i)), markUV(ang(i + 1))] : null;
      triOut3(buf, P, outN, outN, level, uvs, P.map(headG), 0.9);
    }
  }
}

/**
 * A cart wheel, standing in the plane across `axle` (a unit vector along the
 * hub). It is drawn as a RIM — an annulus you can see through — plus spokes and
 * a hub, and the see-through is the whole point: a solid disc reads as a
 * millstone, and the one wagon in this town should not be the object a visitor
 * remembers for being wrong.
 */
function pushWheel(buf, cx, cy, cz, axle, radius, level) {
  const [ax, ay, az] = axle;
  // a frame across the axle; the wheel stands upright, so up is one of its axes
  const ux = -az;
  const uz = ax;
  const uL = Math.hypot(ux, uz) || 1;
  const rx = ux / uL;
  const rz = uz / uL;
  const at = (r, k, t) => [
    cx + rx * Math.cos(k) * r + ax * t,
    cy + Math.sin(k) * r + ay * t,
    cz + rz * Math.cos(k) * r + az * t,
  ];
  const half = WHEEL_T_M / 2;
  const inner = radius - WHEEL_RIM_M;
  // T-2121: the tyre is IRON — a wheel of the period ran on a shrunk-on iron tyre —
  // so it is drawn dark and without grain; the felloe's grain runs round the wheel
  // and each spoke's along the spoke.
  const keepTint = buf.tint;
  const keepAxis = buf.grainAxis;
  const keepOn = buf.grainOn;
  for (let i = 0; i < WHEEL_SIDES; i += 1) {
    const k0 = (i / WHEEL_SIDES) * Math.PI * 2;
    const k1 = ((i + 1) / WHEEL_SIDES) * Math.PI * 2;
    const km = (k0 + k1) / 2;
    const nOut = [rx * Math.cos(km), Math.sin(km), rz * Math.cos(km)];
    const nIn = [-nOut[0], -nOut[1], -nOut[2]];
    // tyre
    buf.tint = buf.iron ?? keepTint;
    buf.grainOn = false;
    tri(buf, at(radius, k0, -half), at(radius, k0, half), at(radius, k1, half), nOut, level);
    tri(buf, at(radius, k0, -half), at(radius, k1, half), at(radius, k1, -half), nOut, level);
    buf.tint = keepTint;
    buf.grainOn = keepOn;
    buf.grainAxis = [-rx * Math.sin(km), Math.cos(km), -rz * Math.sin(km)];
    // the felloe's inside face
    tri(buf, at(inner, k0, -half), at(inner, k1, half), at(inner, k0, half), nIn, level);
    tri(buf, at(inner, k0, -half), at(inner, k1, -half), at(inner, k1, half), nIn, level);
    // the two side rings
    for (const [t, n] of [[half, [ax, ay, az]], [-half, [-ax, -ay, -az]]]) {
      const a = at(inner, k0, t);
      const b = at(radius, k0, t);
      const c = at(radius, k1, t);
      const d = at(inner, k1, t);
      if (t > 0) { tri(buf, a, b, c, n, level); tri(buf, a, c, d, n, level); } else {
        tri(buf, a, c, b, n, level); tri(buf, a, d, c, n, level);
      }
    }
  }
  // ONE SPOKE BOX SPANS THE WHEEL, so six boxes give twelve spokes' worth of
  // timber for half the triangles — a wheel is symmetrical and nobody counts.
  // Built by hand rather than with `pushBox`: a spoke's long axis is not
  // horizontal and `pushBox`'s `u` is.
  for (let i = 0; i < WHEEL_SPOKES; i += 1) {
    const k = (i / WHEEL_SPOKES) * Math.PI;
    const ck = Math.cos(k);
    const sk = Math.sin(k);
    const d = [rx * ck, sk, rz * ck];              // along the spoke, unit
    const q = [-rx * sk, ck, -rz * sk];            // across it, in the wheel plane
    buf.grainAxis = d;
    const half3 = SPOKE_T_M / 2;
    const L = inner;
    const corners = [];
    for (const s of [-1, 1]) {
      for (const a2 of [-1, 1]) {
        for (const b2 of [-1, 1]) {
          corners.push([
            cx + d[0] * s * L + q[0] * a2 * half3 + ax * b2 * half3,
            cy + d[1] * s * L + q[1] * a2 * half3 + ay * b2 * half3,
            cz + d[2] * s * L + q[2] * a2 * half3 + az * b2 * half3,
          ]);
        }
      }
    }
    const face = (i0, i1, i2, i3, n) => {
      tri(buf, corners[i0], corners[i1], corners[i2], n, level);
      tri(buf, corners[i0], corners[i2], corners[i3], n, level);
    };
    face(0, 1, 3, 2, [-q[0], -q[1], -q[2]]);
    face(4, 6, 7, 5, q);
    face(0, 4, 5, 1, [-d[0], -d[1], -d[2]]);
    face(2, 3, 7, 6, d);
  }
  // the hub
  buf.grainAxis = keepAxis;
  pushCask(buf, cx, cy, cz, axle, [rx, 0, rz], WHEEL_T_M * 2.2, HUB_R_M, HUB_R_M * 0.8,
    level, { sides: HUB_SIDES, plain: true });
}

/**
 * THE TILT — the covered wagon's canvas, drawn as an elliptical arch swept along
 * the body. `cy` is the springing line (the body's top rail), `rise` the canvas's
 * height over it and `halfW` its half-width, so the section is the ellipse the
 * bows make and not a half-round, which is what a tilt actually is.
 *
 * IT IS DRAWN TWICE, front and back, and that is deliberate. A canvas is a
 * surface with no thickness worth drawing, so a single-sided sweep would vanish
 * from inside the shed the moment a visitor walked under it — and this layer has
 * ONE material, which it keeps, so `side: DoubleSide` is not available without
 * making every barrel on the layer double-sided too. Sixteen extra triangles is
 * the cheaper answer.
 *
 * The ends are left OPEN. The record says why: a gathered canvas end is a shape
 * nothing this project holds can state, and the plate shows the arch.
 */
function pushTilt(buf, cx, cy, cz, fx, fz, sx, sz, halfLen, halfW, rise, level) {
  const at = (seg, end) => {
    const t = (seg / TILT_SEGS) * Math.PI;
    const across = halfW * Math.cos(t);
    const up = rise * Math.sin(t);
    const along = end * halfLen;
    return [
      cx + fx * along + sx * across,
      cy + up,
      cz + fz * along + sz * across,
    ];
  };
  // The outward normal of an ellipse at parameter t, which is NOT its radius.
  const normalAt = (seg) => {
    const t = (seg / TILT_SEGS) * Math.PI;
    const na = (Math.cos(t) / halfW);
    const nb = (Math.sin(t) / rise);
    const L = Math.hypot(na, nb) || 1;
    return [(sx * na) / L, nb / L, (sz * na) / L];
  };
  for (let i = 0; i < TILT_SEGS; i += 1) {
    const a = at(i, -1);
    const b = at(i, 1);
    const c = at(i + 1, 1);
    const d = at(i + 1, -1);
    const n0 = normalAt(i);
    const n1 = normalAt(i + 1);
    const n = [(n0[0] + n1[0]) / 2, (n0[1] + n1[1]) / 2, (n0[2] + n1[2]) / 2];
    tri(buf, a, b, c, n, level);
    tri(buf, a, c, d, n, level);
    const flip = [-n[0], -n[1], -n[2]];
    tri(buf, a, c, b, flip, level);
    tri(buf, a, d, c, flip, level);
  }
}

/**
 * A POLE LYING DOWN — a wagon's tongue, a cart's shaft — from its root at the
 * vehicle to its tip resting on the grass. Factored out of `buildWagon` when
 * T-0064 gave the cart a pair of them: the arithmetic that settles where the tip
 * lands is the same arithmetic in both places, and two copies of a fixed point
 * is two chances to get it wrong.
 *
 * `rootAlong`/`rootY` are where the pole leaves the vehicle, `len` is its own
 * length (NOT its horizontal run — the recorded number is the stick), and
 * `across` offsets it sideways so a cart's two shafts run either side of where
 * an animal would be if one were drawn, which one never is.
 */
function pushPole(buf, x, z, base, fx, fz, sx, sz, rootAlong, rootY, len, across,
  half, level) {
  // The tip rests ON the ground rather than in it, so its centre sits half the
  // pole's VERTICAL section above the grass — which is `half / cos θ`, and θ is
  // itself set by the drop. One pass of the fixed point settles it to a hundredth
  // of a millimetre at these inclinations, so it does not need a loop.
  const drop0 = Math.max(rootY - base - half, 0);
  const cos0 = Math.sqrt(Math.max(len ** 2 - drop0 ** 2, 0)) / (len || 1);
  const tipY = base + half / Math.max(cos0, 1e-6);
  const drop = Math.max(rootY - tipY, 0);
  const run = Math.sqrt(Math.max(len ** 2 - drop ** 2, 0));
  const midAlong = rootAlong + run / 2;
  const midY = (rootY + tipY) / 2;
  const poleLen = Math.hypot(run, drop) || 1;
  const pa = [(fx * run) / poleLen, -drop / poleLen, (fz * run) / poleLen];
  const pb = [sx, 0, sz];
  const pc = [pa[1] * pb[2] - pa[2] * pb[1], pa[2] * pb[0] - pa[0] * pb[2],
    pa[0] * pb[1] - pa[1] * pb[0]];
  pushBoxV(buf,
    [x + fx * midAlong + sx * across, midY, z + fz * midAlong + sz * across],
    [pa[0] * (poleLen / 2), pa[1] * (poleLen / 2), pa[2] * (poleLen / 2)],
    [pb[0] * half, pb[1] * half, pb[2] * half],
    [pc[0] * half, pc[1] * half, pc[2] * half], level);
}

/* -------------------------------------------------------------------------- */
/* the objects                                                                 */
/* -------------------------------------------------------------------------- */

/** The ground under a point, or null when the terrain has nothing there. */
function groundAt(terrain, e, n) {
  const y = terrain.surfaceHeight(e, n);
  return Number.isFinite(y) ? y : null;
}

function buildItem(buf, item, form, terrain, level, problems, who, marks = null) {
  const at = item.at_local_enu_m;
  if (!Array.isArray(at) || at.length !== 2) return false;
  const base = groundAt(terrain, at[0], at[1]);
  if (base === null) {
    problems.push(`yard: ${who} has no ground under its ${item.kind} — it is not drawn`);
    return false;
  }
  // world is (E, up, -N); the record's bearing is a compass bearing, so along the
  // wall is (cos b, -sin b) in ENU and out of it is (sin b, cos b).
  const b = ((item.bearing_deg ?? 0) * Math.PI) / 180;
  const wx = Math.cos(b);
  const wz = Math.sin(b);
  const x = at[0];
  const z = -at[1];

  // T-2121: every object is DEALT its own wood and its own shading, seeded on where
  // it stands and whose door it is at, so a rank of casks is a rank of different
  // casks and the same page draws the same ones on every load.
  const rng = streamOf(hashOf(who ?? '', item.kind, Math.round(at[0] * 100),
    Math.round(at[1] * 100), item.tier ?? 0));
  const keep = { tint: buf.tint, ground: buf.ground, k: buf.k };
  buf.ground = base;
  const done = (drew) => {
    buf.tint = keep.tint;
    buf.ground = keep.ground;
    buf.k = keep.k;
    return drew;
  };

  if (item.kind === 'barrel') {
    const h = form.barrelHeight;
    const belly = form.barrelBelly / 2;
    const head = form.barrelHead / 2;
    buf.tint = toneOf(dealFrom(WOOD_DEALS.barrel, rng()), 0.9 + rng() * 0.18);
    // Split-wood hoops on most — the slack barrels of flour and provisions — and
    // iron on the rest, the tight casks.
    const iron = rng() < 0.4;
    const cask = {
      rng, hoops: iron ? 'iron' : 'wood',
      // A split hoop weathers with the cask it binds, so it is the cask's own tone
      // taken half way to fresh hickory — a band, not a stripe of paint.
      hoopTint: iron ? buf.iron : buf.tint.map((c, n) => {
        const h = toneOf(WOOD_HOOP_COLOUR, 0.9 + rng() * 0.1)[n];
        return (c + h) / 2;
      }),
    };
    /**
     * T-0065, AND WHERE THE MARK GOES DEPENDS ON WHICH WAY THE CASK IS LYING.
     * A cask STANDING on its head is read from the footway, so its stencil is
     * across the BILGE — three staves of the belly, turned to the street. A
     * cask LAID on its side has its bilge turned up at the sky and its HEAD
     * turned down the footway, which is then the only face of it a visitor can
     * read the right way up; so the empties are marked on the head. Both are
     * where the period put them, and both are chosen by what can be read.
     */
    if (item.pose === 'laid') {
      // an empty put back out, lying ALONG the wall and out of the way rather
      // than across the footway: the axis is the along-wall direction.
      const rect = item.mark && marks ? marks(item.mark, 'head') : null;
      pushCask(buf, x, base + belly, z, [wx, 0, wz], [0, 1, 0], h, belly, head, level,
        { ...cask, headMark: rect ? { rect, rot: 1 } : null });
    } else {
      // Upright, `right` is along the wall and the frame's third axis is the
      // INWARD normal, so the direction that has to face the street is the one
      // at three quarters of a turn: cos = 0, sin = -1, which is -third. Standing
      // on its low head, that head is never seen and is not drawn.
      const rect = item.mark && marks ? marks(item.mark, 'bilge') : null;
      pushCask(buf, x, base + h / 2, z, [0, 1, 0], [wx, 0, wz], h, belly, head, level,
        { ...cask, capLow: false,
          sideMark: rect ? { rect, center: (3 * Math.PI) / 2 } : null });
    }
    return done(true);
  }
  if (item.kind === 'bench') {
    // A backless plank bench standing against a wall: a seat plank on two plank
    // ends. `at` is its centre and the record puts that half the seat's depth off
    // the wall plane, so the back edge touches the boards.
    const [L, D, H] = form.bench;
    const t = form.benchPlank;
    buf.tint = toneOf(dealFrom(WOOD_DEALS.timber, rng()), 0.9 + rng() * 0.15);
    pushBox(buf, x, base + H - t / 2, z, wx, wz, L / 2, D / 2, t / 2, level);
    // the two ends, inset so the seat overhangs them the way a bench's does
    const endInset = Math.min(0.14, L / 8);
    for (const s2 of [-1, 1]) {
      buf.k = 0.88 + rng() * 0.12;
      pushBox(buf, x + wx * s2 * (L / 2 - endInset), base + (H - t) / 2,
        z + wz * s2 * (L / 2 - endInset), wx, wz, t / 2, (D * 0.82) / 2, (H - t) / 2,
        level);
    }
    return done(true);
  }
  if (item.kind === 'crate') {
    const [l, w, hh] = form.crate;
    const tier = item.tier || 0;
    const s = tier === 0 ? 1 : form.crate2Scale;
    const y = base + (tier === 0 ? hh / 2 : hh + (hh * s) / 2);
    buf.tint = toneOf(dealFrom(WOOD_DEALS.crate, rng()), 0.9 + rng() * 0.18);
    // The shipping mark goes on the face that looks at the street, which is the
    // one `pushBox` calls face 3. A case stacked on another is the same aspect
    // — it is the same case scaled — so both tiers share the atlas cell.
    pushBox(buf, x, y, z, wx, wz, (l * s) / 2, (w * s) / 2, (hh * s) / 2, level,
      item.mark && marks ? marks(item.mark, 'case') : null);
    // T-2121: and the CLEATS a packing case is nailed up with — two battens up each
    // end, standing proud of the boards. A box without them reads as a block.
    const cl = CRATE_CLEAT_M;
    for (const e of [-1, 1]) {
      for (const c of [-1, 1]) {
        buf.k = 0.84 + rng() * 0.12;
        const along = e * ((l * s) / 2 + cl[1] / 2);
        const across = c * ((w * s) / 2 - cl[0] / 2 - 0.02);
        pushBox(buf, x + wx * along - wz * across, y, z + wz * along + wx * across,
          wx, wz, cl[1] / 2, cl[0] / 2, (hh * s) / 2, level);
      }
    }
    return done(true);
  }
  return done(false);
}

/**
 * WHAT A WAGON OR CART IS PAINTED, OR NOT (T-2121) — dealt from `WAGON_SCHEMES` on
 * the vehicle's own id, so the same wagon wears the same coat on every load, and
 * then aged: a body a little lighter or darker, a canvas a little dirtier.
 */
function wagonCoat(wagon) {
  const rng = streamOf(hashOf('wagon', wagon.id ?? '', ...(wagon.at_local_enu_m ?? [])));
  const total = WAGON_SCHEMES.reduce((a, [w]) => a + w, 0);
  let r = rng() * total;
  let pick = WAGON_SCHEMES[0];
  for (const sc of WAGON_SCHEMES) { r -= sc[0]; if (r < 0) { pick = sc; break; } }
  const age = 0.88 + rng() * 0.18;
  return {
    rng,
    body: toneOf(pick[1], age),
    gear: toneOf(pick[2], age * (0.92 + rng() * 0.1)),
    canvas: toneOf(CANVAS_COLOUR, 0.84 + rng() * 0.18),
  };
}

/**
 * A WAGON BOX OF BOARDS (T-2121): a plank floor, each side two boards on edge, each
 * end two boards, and stakes up the outside of the sides — so a visitor looking at
 * one sees planks, each its own shade, and not four slabs. The box's outer size is
 * the record's `wagon_body_m` (or `cart_m`) exactly as before; the boards divide it.
 */
function pushWagonBox(buf, x, z, bed, fx, fz, sx, sz, L, W, H, level, coat, stakes) {
  const keep = buf.tint;
  buf.tint = coat.body;
  buf.k = 0.94 + coat.rng() * 0.08;
  pushBox(buf, x, bed, z, fx, fz, L / 2, W / 2, 0.035, level);
  const lowH = H * 0.55;
  const highH = H - lowH;
  for (const s of [-1, 1]) {
    for (const [y0, h] of [[0, lowH], [lowH, highH]]) {
      buf.k = 0.86 + coat.rng() * 0.2;
      pushBox(buf, x + sx * s * (W / 2), bed + y0 + h / 2, z + sz * s * (W / 2),
        fx, fz, L / 2, 0.03, h / 2, level);
      buf.k = 0.86 + coat.rng() * 0.2;
      pushBox(buf, x + fx * s * (L / 2), bed + y0 + h / 2, z + fz * s * (L / 2),
        sx, sz, W / 2 - 0.03, 0.03, h / 2, level);
    }
  }
  // The stakes, in the gear's coat, standing a hand proud of the top board.
  buf.tint = coat.gear;
  for (const s of [-1, 1]) {
    for (let i = 0; i < stakes; i += 1) {
      const along = -L / 2 + 0.18 + (i * (L - 0.36)) / Math.max(stakes - 1, 1);
      buf.k = 0.9 + coat.rng() * 0.12;
      const off = W / 2 + 0.03 + WAGON_STAKE_M / 2;
      pushBox(buf, x + fx * along + sx * s * off, bed + H / 2, z + fz * along + sz * s * off,
        fx, fz, WAGON_STAKE_M / 2, WAGON_STAKE_M / 2, H / 2 + 0.05, level);
    }
  }
  buf.k = 1;
  buf.tint = keep;
}

function buildWagon(buf, wagon, form, terrain, level, problems) {
  const at = wagon.at_local_enu_m;
  if (!Array.isArray(at) || at.length !== 2) return false;
  const base = groundAt(terrain, at[0], at[1]);
  if (base === null) {
    problems.push(`yard: ${wagon.id} has no ground under it — no wagon is drawn`);
    return false;
  }
  const b = ((wagon.bearing_deg ?? 0) * Math.PI) / 180;
  // along the wagon, and across it, in the renderer's world axes
  const fx = Math.sin(b);
  const fz = -Math.cos(b);
  const sx = Math.cos(b);
  const sz = Math.sin(b);
  const x = at[0];
  const z = -at[1];
  const [L, W, H] = form.wagonBody;
  const bed = base + form.wagonBedY;
  const coat = wagonCoat(wagon);
  const keepTint = buf.tint;
  buf.ground = base;

  // the body: a plank floor and four sides, so a visitor looking down into it
  // sees a wagon box and not a solid block.
  pushWagonBox(buf, x, z, bed, fx, fz, sx, sz, L, W, H, level, coat, 3);
  // everything under the box — gear, wheels, tongue — is in the gear's coat
  buf.tint = coat.gear;
  // the two axles and their wheels
  const pairs = [
    [-L / 2 + 0.35, form.wagonRearWheel / 2],
    [L / 2 - 0.35, form.wagonFrontWheel / 2],
  ];
  for (const [along, r] of pairs) {
    const axY = base + r;
    pushBox(buf, x + fx * along, axY, z + fz * along, sx, sz,
      W / 2 + WHEEL_T_M, AXLE_T_M / 2, AXLE_T_M / 2, level);
    for (const s of [-1, 1]) {
      pushWheel(buf,
        x + fx * along + sx * s * (W / 2 + WHEEL_T_M),
        axY,
        z + fz * along + sz * s * (W / 2 + WHEEL_T_M),
        [sx * s, 0, sz * s], r, level);
    }
  }
  // THE RUNNING GEAR — what carries the box, and what ties the two axles
  // together (T-0087).
  //
  // Until this was written the wagon was a floor, two axle sticks and four
  // wheels, and NOTHING between them: the floor sat at 0.95 m, the rear axle at
  // 0.685 m and the front at 0.535 m, so the box hovered 0.27 m above one axle
  // and 0.42 m above the other, on air. The owner read it from the Green Tree's
  // yard as "that bar is supposed to be below the carriage of the wagon holding
  // the wheels together" — the bar he found was the tongue (T-0084), because
  // the member he was looking for was not drawn.
  //
  // A farm wagon of the period has, between box and axles: a BOLSTER over each
  // axle, which is what the box actually rests on; a REACH (coupling pole) tying
  // the rear axle forward to the front gear and setting the wagon's length; and
  // HOUNDS at the front, bracketing the reach and carrying the KINGBOLT the
  // whole front gear swivels on — a farm wagon steers by turning its front gear,
  // so without the hounds the front axle is attached to nothing.
  //
  // THE ONE NUMBER THAT MAKES THE REST FALL OUT: both bolsters are the same
  // depth, because a bolster's job is to bring two different axle heights up to
  // one level floor. The rear wheels are the bigger pair, so the REAR axle sets
  // that level — `gearTop` — and the front bolster reaches down to the same
  // line. What is left under the front bolster is exactly the space the hounds
  // and the reach occupy. Nothing here is chosen; it is read off the wheels.
  const floorY = bed - 0.035;                     // the underside of the floor
  const rearAlong = pairs[0][0];
  const frontAlong = pairs[1][0];
  const rearAxleTop = base + form.wagonRearWheel / 2 + AXLE_T_M / 2;
  const frontAxleTop = base + form.wagonFrontWheel / 2 + AXLE_T_M / 2;
  const gearTop = rearAxleTop;                    // both bolsters' underside
  const bolsterHalf = Math.max(floorY - gearTop, 0) / 2;
  // The two bolsters. They run ACROSS the wagon and their ends show a little
  // past the box's sides — which is where a wagon's stakes would stand, and is
  // what makes them read as bolsters from where the owner was standing rather
  // than as a thicker floor.
  for (const along of [rearAlong, frontAlong]) {
    pushBox(buf, x + fx * along, gearTop + bolsterHalf, z + fz * along, sx, sz,
      W / 2 + BOLSTER_OUT_M, BOLSTER_T_M / 2, bolsterHalf, level);
  }
  // The reach, on the centreline: it sits ON the front axle and runs back UNDER
  // the rear one, which is both how the pole is actually hung and, here, simply
  // where the two axle tops put it. Its rear end carries past the rear axle so
  // it is visibly bolted to it, and its front end stops short of the front axle
  // so the hounds bracket it rather than butt it.
  const reachLow = frontAxleTop;
  const reachHigh = base + form.wagonRearWheel / 2 - AXLE_T_M / 2;
  const reachBack = rearAlong - 0.10;
  const reachFore = frontAlong - 0.08;
  pushBox(buf, x + fx * (reachBack + reachFore) / 2, (reachLow + reachHigh) / 2,
    z + fz * (reachBack + reachFore) / 2, fx, fz,
    (reachFore - reachBack) / 2, REACH_W_M / 2,
    Math.max(reachHigh - reachLow, 0) / 2, level);
  // The hounds, one each side of the reach and touching it, filling the rest of
  // the space under the front bolster. They run forward past the front axle to
  // the tongue's root at the body's nose, so the tongue is carried BY the front
  // gear instead of ending in the air beside it — the other half of what the
  // owner was looking at.
  const houndOff = REACH_W_M / 2 + HOUND_W_M / 2;
  const houndBack = frontAlong - HOUND_BACK_M;
  const houndFore = L / 2 + 0.06;
  for (const s of [-1, 1]) {
    pushBox(buf,
      x + fx * (houndBack + houndFore) / 2 + sx * s * houndOff,
      (frontAxleTop + gearTop) / 2,
      z + fz * (houndBack + houndFore) / 2 + sz * s * houndOff,
      fx, fz, (houndFore - houndBack) / 2, HOUND_W_M / 2,
      Math.max(gearTop - frontAxleTop, 0) / 2, level);
  }
  // And the kingbolt, through bolster, hounds and axle. Most of its length is
  // inside the timber it pins — which is what a bolt is — so what is drawn for
  // is the nut below the front axle, the one part of it a visitor can see and
  // the only evidence from outside that the front gear turns.
  const boltLow = base + form.wagonFrontWheel / 2 - AXLE_T_M / 2 - KINGBOLT_DROP_M;
  pushBox(buf, x + fx * frontAlong, (boltLow + floorY) / 2, z + fz * frontAlong,
    fx, fz, KINGBOLT_T_M / 2, KINGBOLT_T_M / 2,
    Math.max(floorY - boltLow, 0) / 2, level);
  // THE TONGUE — a pole at its own section, along its own inclination, running
  // down to the ground at its far end because nothing is hitched to it.
  //
  // It was one horizontal box deep enough to span the drop from the front axle
  // to the ground: a 2.75 m stick 0.055 m thick drawn 0.48 m deep, which is a
  // plank lying in the grass and not a tongue (T-0084, found in this code and
  // reported from the Green Tree's yard on the same day). The old comment was
  // right about the ANGLE — a stick's exact inclination is not a claim this
  // record makes — and the box only had to be that deep because it was
  // axis-aligned. `pushBoxV` takes a frame, so the same modest claim about the
  // angle is now made by a box of the tongue's OWN section, inclined.
  //
  // The recorded 2.75 m is now the pole's LENGTH rather than its horizontal
  // run, which is what the number means: the tip lands 2.71 m ahead of the body
  // instead of 2.75 m, well inside the 4.6 m the wagon is measured by.
  pushPole(buf, x, z, base, fx, fz, sx, sz, L / 2,
    base + form.wagonFrontWheel / 2, form.wagonTongue, 0, TONGUE_T_M / 2, level);
  // AND THE TILT, on the wagons the record marks covered. The canvas springs
  // from the body's top rail, is pulled a little past the end bows, and is the
  // only thing on this layer drawn in something other than the timber tone.
  if (wagon.tilt) {
    const [rise, over] = form.wagonTilt;
    buf.tint = coat.canvas;
    buf.grainOn = false;
    pushTilt(buf, x, bed + H, z, fx, fz, sx, sz, L / 2 + over, W / 2, rise, level);
    buf.grainOn = undefined;
    buf.tint = coat.gear;
  }
  if (wagon.yoke) pushYoke(buf, x, z, base, fx, fz, sx, sz, form, L, level);
  buf.tint = keepTint;
  buf.ground = null;
  return true;
}

/**
 * A TWO-WHEELED CART (T-0064), and the whole reason it exists is that "more
 * wagons all over the place" is not one vehicle repeated sixty times. One axle,
 * tall wheels, a short box sitting straight on the axle because there is no
 * second one to balance against, and a pair of SHAFTS instead of a tongue —
 * down on the grass at their own inclination, because nothing is in them and
 * nothing ever will be.
 *
 * Everything it is made of is already here: the wheel, the box and the pole are
 * the wagon's own primitives, and the only numbers it adds are the record's
 * `cart_m`. It costs a little over half a farm wagon's triangles, which is what
 * lets the lanes of this town have vehicles on them at all.
 */
function buildCart(buf, wagon, form, terrain, level, problems) {
  const at = wagon.at_local_enu_m;
  if (!Array.isArray(at) || at.length !== 2) return false;
  const base = groundAt(terrain, at[0], at[1]);
  if (base === null) {
    problems.push(`yard: ${wagon.id} has no ground under it — no cart is drawn`);
    return false;
  }
  const b = ((wagon.bearing_deg ?? 0) * Math.PI) / 180;
  const fx = Math.sin(b);
  const fz = -Math.cos(b);
  const sx = Math.cos(b);
  const sz = Math.sin(b);
  const x = at[0];
  const z = -at[1];
  const [L, W, H, wheelD, bedY, shaft] = form.cart;
  const bed = base + bedY;
  const coat = wagonCoat(wagon);
  const keepTint = buf.tint;
  buf.ground = base;
  // the box: a floor and four sides, the wagon's own construction at the cart's
  // own size.
  pushWagonBox(buf, x, z, bed, fx, fz, sx, sz, L, W, H, level, coat, 2);
  buf.tint = coat.gear;
  // ONE axle, under the box's middle where a cart's has to be: the load is
  // balanced over it rather than carried between two of them.
  const r = wheelD / 2;
  const axY = base + r;
  pushBox(buf, x, axY, z, sx, sz, W / 2 + WHEEL_T_M, AXLE_T_M / 2, AXLE_T_M / 2,
    level);
  for (const s of [-1, 1]) {
    pushWheel(buf, x + sx * s * (W / 2 + WHEEL_T_M), axY,
      z + sz * s * (W / 2 + WHEEL_T_M), [sx * s, 0, sz * s], r, level);
  }
  // And the two shafts, either side of the empty ground where an animal would
  // stand if this project drew one, which it does not.
  for (const s of [-1, 1]) {
    pushPole(buf, x, z, base, fx, fz, sx, sz, L / 2, bed - 0.035, shaft,
      s * (CART_SHAFT_GAUGE_M / 2), SHAFT_T_M / 2, level);
  }
  // A HOGSHEAD MOUNTED ON IT, and only when the record says so (T-0759).
  // Andreas gives the water cart its two defining facts and no third — "two
  // wheeled vehicles, upon which hogsheads were mounted" — so the cask is a
  // flag on the vehicle rather than a fourth `kind`: it changes what the cart
  // carries, not what the cart is, exactly as `tilt` does for a wagon. It lies
  // on its side ALONG the cart's own line, resting on the box floor, because a
  // cask filled by pail and run off through a hose at the bung lies down; the
  // record's own numbers give its length and its two diameters, and the belly
  // is checked against the box it has to sit inside rather than assumed to fit.
  if (wagon.hogshead) {
    const [caskL, caskBelly, caskHead] = form.hogshead;
    const caskR = Math.min(caskBelly, W - 0.06) / 2;
    buf.tint = toneOf('darkoak', 0.95 + coat.rng() * 0.15);
    pushCask(buf, x, bed + 0.035 + caskR, z, [fx, 0, fz], [0, 1, 0],
      Math.min(caskL, L), caskR, (caskHead / caskBelly) * caskR, level,
      { rng: coat.rng, hoops: 'iron', hoopTint: buf.iron });
    buf.tint = coat.gear;
  }
  if (wagon.yoke) pushYoke(buf, x, z, base, fx, fz, sx, sz, form, L, level);
  buf.tint = keepTint;
  buf.ground = null;
  return true;
}

/**
 * THE OX-YOKE LAID BY — a beam and its two bows, lying flat on the grass beside
 * a wagon whose team is out. It is the one object on this layer that exists
 * BECAUSE of what this project refuses to draw: there are no animals in this
 * scene, so a covered wagon standing with its tongue on the ground and nothing
 * else to say for itself reads as abandoned rather than outspanned. The yoke is
 * the honest half of a team, exactly as the Green Tree's empty bench is the
 * honest half of the sitters in its plate.
 *
 * Laid ACROSS the wagon's line, a little ahead of the body and out on the near
 * side, which is where a yoke comes off. The bows are drawn as two short sticks
 * dropping from the beam's ends rather than as bent timber: a bow is a curve,
 * and a curve this small is triangles spent on something a visitor reads as two
 * pegs either way.
 */
function pushYoke(buf, x, z, base, fx, fz, sx, sz, form, bodyL, level) {
  const [beam, sq, bow, bowSq] = form.yoke;
  const along = bodyL / 2 + 0.55;
  const across = form.yokeOffset;
  const cx = x + fx * along + sx * across;
  const cz = z + fz * along + sz * across;
  // The beam lies across the wagon's own line, flat on the ground.
  pushBox(buf, cx, base + sq / 2, cz, sx, sz, beam / 2, sq / 2, sq / 2, level);
  for (const s of [-1, 1]) {
    pushBox(buf, cx + sx * s * (beam / 2 - bowSq), base + sq + bow / 2 - YOKE_BOW_DROP_M,
      cz + sz * s * (beam / 2 - bowSq), fx, fz, bowSq / 2, bowSq / 2, bow / 2, level);
  }
}

/**
 * THE OPEN-SIDED WAGON SHED. A lean-to spiked to a wall: a plate on that wall at
 * `head_m`, a plate on posts at `eave_m` out at `depth_m`, rafters between them
 * and a boarded deck over the lot. Three sides open, which is what makes it a
 * wagon shed and not an outbuilding — and what lets a visitor see the covered
 * wagon standing in it.
 *
 * EVERY NUMBER COMES FROM THE RECORD. The bay, the depth, the two plate heights
 * and the bearing are the record's claims; how many posts hold the front and how
 * many rafters cross it are this file's, the same division the barrel's stave
 * count and the wheel's spokes already make.
 */
function buildShed(buf, shed, form, terrain, level, problems) {
  const at = shed.at_local_enu_m;
  if (!Array.isArray(at) || at.length !== 2) return false;
  const base = groundAt(terrain, at[0], at[1]);
  if (base === null) {
    problems.push(`yard: ${shed.id} has no ground under it — no shed is drawn`);
    return false;
  }
  const len = shed.length_m ?? 0;
  const depth = shed.depth_m ?? 0;
  const eave = shed.eave_m ?? 0;
  const head = shed.head_m ?? 0;
  if (!(len > 0 && depth > 0 && head > eave && eave > 0)) {
    problems.push(`yard: ${shed.id} is not a shed the record can draw — it is skipped`);
    return false;
  }
  const [post, plate] = form.shedTimber;
  const b = ((shed.bearing_deg ?? 0) * Math.PI) / 180;
  // Same frame as every other object here: along the wall is (cos b, sin b) in
  // world XZ and out of the wall is (sin b, -cos b).
  const ax = Math.cos(b);
  const az = Math.sin(b);
  const ox = Math.sin(b);
  const oz = -Math.cos(b);
  const x = at[0];
  const z = -at[1];
  // The wall face and the open front, either side of the record's own centre.
  const wallOff = -depth / 2;
  const frontOff = depth / 2;
  const P = (along, out, y) => [
    x + ax * along + ox * out, base + y, z + az * along + oz * out,
  ];

  // ---- the posts under the open side ------------------------------------- //
  // One at each end of the bay and enough between them that no span of the
  // plate exceeds 2.5 m, which is as far as a plate of this section carries.
  const posts = Math.max(2, Math.ceil(len / 2.5) + 1);
  for (let i = 0; i < posts; i += 1) {
    const along = -len / 2 + (i * len) / (posts - 1);
    // Set in by half their own thickness so the plate lands on them square.
    const a2 = Math.max(-len / 2 + post / 2, Math.min(len / 2 - post / 2, along));
    const p = P(a2, frontOff - post / 2, (eave - plate) / 2);
    pushBox(buf, p[0], p[1], p[2], ax, az, post / 2, post / 2,
      (eave - plate) / 2, level);
  }
  // ---- the two plates ----------------------------------------------------- //
  const front = P(0, frontOff - post / 2, eave - plate / 2);
  pushBox(buf, front[0], front[1], front[2], ax, az, len / 2, post / 2,
    plate / 2, level);
  const wall = P(0, wallOff + plate / 2, head - plate / 2);
  pushBox(buf, wall[0], wall[1], wall[2], ax, az, len / 2, plate / 2,
    plate / 2, level);

  // ---- the rafters and the deck over them --------------------------------- //
  // The slope, from the wall plate down to the front plate. `run` is the ground
  // it covers and `drop` the fall over it; both come from the record.
  const run = depth - post / 2 - plate / 2;
  const drop = head - eave;
  const sLen = Math.hypot(run, drop);
  const su = [(ox * run) / sLen, -drop / sLen, (oz * run) / sLen];
  // The roof's own normal: across the slope and across the bay, pointing up.
  let rn = [az * su[1] * -1, az * su[0] - ax * su[2], ax * su[1]];
  const rl = Math.hypot(rn[0], rn[1], rn[2]) || 1;
  rn = [rn[0] / rl, rn[1] / rl, rn[2] / rl];
  if (rn[1] < 0) rn = [-rn[0], -rn[1], -rn[2]];
  const mid = P(0, (wallOff + plate / 2 + frontOff - post / 2) / 2,
    (head + eave) / 2 - plate);
  const rafters = Math.max(2, Math.round(len) + 1);
  for (let i = 0; i < rafters; i += 1) {
    const along = -len / 2 + (i * len) / (rafters - 1);
    const a2 = Math.max(-len / 2 + plate / 4, Math.min(len / 2 - plate / 4, along));
    const c = [mid[0] + ax * a2, mid[1], mid[2] + az * a2];
    pushBoxV(buf, c,
      [su[0] * (sLen / 2), su[1] * (sLen / 2), su[2] * (sLen / 2)],
      [ax * (plate / 4), 0, az * (plate / 4)],
      [rn[0] * (plate / 2), rn[1] * (plate / 2), rn[2] * (plate / 2)], level);
  }
  // The boarded deck: over the rafters, overhanging the front plate so the drip
  // clears the posts, and a hand's width past each end of the bay.
  const over = 0.2;
  const deckC = [
    mid[0] + su[0] * (over / 2) + rn[0] * (plate / 2 + DECK_T_M / 2),
    mid[1] + su[1] * (over / 2) + rn[1] * (plate / 2 + DECK_T_M / 2),
    mid[2] + su[2] * (over / 2) + rn[2] * (plate / 2 + DECK_T_M / 2),
  ];
  pushBoxV(buf, deckC,
    [su[0] * (sLen / 2 + over / 2), su[1] * (sLen / 2 + over / 2),
      su[2] * (sLen / 2 + over / 2)],
    [ax * (len / 2 + 0.15), 0, az * (len / 2 + 0.15)],
    [rn[0] * (DECK_T_M / 2), rn[1] * (DECK_T_M / 2), rn[2] * (DECK_T_M / 2)], level);
  return true;
}

/**
 * A PRIVY OR A STABLE IN A HOUSE'S YARD (T-1960). `data/yard/town_yard_outbuildings.json`
 * deals one privy to every dwelling lot with a yard behind the house and no committed
 * privy, and a stable to the households that kept a horse; it decides the corner, the
 * size, the finish and the weather from the house's own class and age, and this file
 * only draws what it says. Like the wagon shed above it is not a structure record and is
 * not baked — a board box is derived at load from the record's numbers and the committed
 * heightfield — and it carries `reconstructed` on every vertex, because the fact of THIS
 * privy in THIS corner is dealt by rule (L353).
 *
 * THE FRAME IS THE LAYER'S: along the face is (cos b, sin b) in world XZ and out of it is
 * (sin b, -cos b). `out` points into the yard, toward the house — the side the door is
 * on — so the back of the box is the side nearest the alley.
 *
 * IT STANDS ON ITS LOWEST CORNER, with its sill run a hand below grade, so a box on a
 * slope is buried on the high side rather than floating on the low one.
 */
// Pine boards go from new-sawn straw to the silver of a few summers; the lighter end
// is deliberate, because a yard building's door side is as often in shade as not and
// the layer's darker goods tone reads as black there.
const OUTBUILDING_TONE = {
  fresh: 0xb59c78, seasoned: 0xa69886, weathered: 0x9c968c, grey: 0x908e89,
};
const WHITEWASH_TONE = { fresh: 0xdcd7c9, seasoned: 0xd2ccbd, weathered: 0xc6c0b1,
  grey: 0xbab5a8 };
const OB_BOARD_T = 0.03;     // a wall board
const OB_BATTEN = [0.07, 0.022];  // a batten's face and how far it stands proud
const OB_SILL_SINK = 0.12;   // how far the sill runs below the lowest corner's grade
const OB_DECK_T = 0.035;     // a roof board
const obToneCache = new Map();
function obTone(hex, k) {
  const key = `${hex}:${k.toFixed(3)}`;
  let t = obToneCache.get(key);
  if (!t) {
    const c = new THREE.Color(hex).multiplyScalar(k);
    t = [c.r, c.g, c.b];
    obToneCache.set(key, t);
  }
  return t;
}
/** A small, stable spread per building, so two neighbours dealt the same tone differ. */
function obJitter(id) {
  let h = 2166136261;
  for (let i = 0; i < id.length; i += 1) { h ^= id.charCodeAt(i); h = Math.imul(h, 16777619); }
  return ((h >>> 0) % 1000) / 1000;
}
function triOut(buf, a, b, c, n, level) {
  const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const v = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
  const x = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
  if (x[0] * n[0] + x[1] * n[1] + x[2] * n[2] < 0) tri(buf, a, c, b, n, level);
  else tri(buf, a, b, c, n, level);
}

function buildOutbuilding(buf, ob, terrain, level, problems) {
  const at = ob.at_local_enu_m;
  const A = ob.along_m ?? 0;
  const D = ob.depth_m ?? 0;
  const E = ob.eave_m ?? 0;
  const H = ob.head_m ?? 0;
  if (!(A > 0 && D > 0 && E > 0 && H > E)) {
    problems.push(`yard: ${ob.id} is not an outbuilding the record can draw — skipped`);
    return false;
  }
  const b = ((ob.bearing_deg ?? 0) * Math.PI) / 180;
  const ax = Math.cos(b);
  const az = Math.sin(b);
  const ox = Math.sin(b);
  const oz = -Math.cos(b);
  const x = at[0];
  const z = -at[1];
  let base = Infinity;
  for (const [sa, so] of [[0, 0], [-1, -1], [1, -1], [1, 1], [-1, 1]]) {
    const pe = x + ax * sa * (A / 2) + ox * so * (D / 2);
    const pz = z + az * sa * (A / 2) + oz * so * (D / 2);
    const g = groundAt(terrain, pe, -pz);
    if (g !== null) base = Math.min(base, g);
  }
  if (!Number.isFinite(base)) {
    problems.push(`yard: ${ob.id} has no ground under it — it is not drawn`);
    return false;
  }
  const P = (al, out, y) => [x + ax * al + ox * out, base + y, z + az * al + oz * out];
  const AL = [ax, 0, az];
  const OUT = [ox, 0, oz];
  const UP = [0, 1, 0];
  const sc = (v, k) => [v[0] * k, v[1] * k, v[2] * k];
  /** A box in the building's own frame: centre (along, out, y) and half-extents. */
  const box = (al, out, y, hA, hO, hY) => {
    pushBoxV(buf, P(al, out, y), sc(AL, hA), sc(OUT, hO), sc(UP, hY), level);
  };
  // THE TONE: the house's weather, whitewash where the record says, a spread per box.
  const weather = OUTBUILDING_TONE[ob.weather] ? ob.weather : 'weathered';
  const j = obJitter(ob.id);
  const k = 0.95 + 0.1 * j;
  let wall;
  if (ob.finish === 'whitewash') wall = obTone(WHITEWASH_TONE[weather], k);
  else if (ob.finish === 'slab') wall = obTone(OUTBUILDING_TONE[weather], k * 0.84);
  else wall = obTone(OUTBUILDING_TONE[weather], k);
  const timber = obTone(OUTBUILDING_TONE[weather], k * 0.9);
  const roof = obTone(OUTBUILDING_TONE[weather === 'fresh' ? 'seasoned' : 'grey'], k * 0.82);
  const door = ob.finish === 'whitewash' ? obTone(OUTBUILDING_TONE[weather], k * 0.95)
    : obTone(OUTBUILDING_TONE[weather], k * 0.86);
  const keep = buf.tint;
  const gable = ob.roof === 'gable';
  const t = OB_BOARD_T;
  const y0 = -OB_SILL_SINK;
  // Height of the wall top at a point across the depth: a shed falls from the door
  // side (head) to the alley side (eave); a gable's long walls both stop at the eave.
  const topAt = (out) => (gable ? E : E + ((H - E) * (out + D / 2)) / D);

  // ---- the walls --------------------------------------------------------- //
  buf.tint = wall;
  const hF = topAt(D / 2);
  const hB = topAt(-D / 2);
  box(0, D / 2 - t / 2, (y0 + hF) / 2, A / 2, t / 2, (hF - y0) / 2);
  box(0, -D / 2 + t / 2, (y0 + hB) / 2, A / 2, t / 2, (hB - y0) / 2);
  for (const s of [-1, 1]) {
    box(s * (A / 2 - t / 2), 0, (y0 + E) / 2, t / 2, D / 2 - t, (E - y0) / 2);
    // Above the eave the end wall is a triangle: the shed's fall, or the gable.
    const n = sc(AL, s);
    const al = s * (A / 2);
    if (gable) {
      triOut(buf, P(al, -D / 2, E), P(al, D / 2, E), P(al, 0, H), n, level);
    } else {
      triOut(buf, P(al, -D / 2, E), P(al, D / 2, E), P(al, D / 2, H), n, level);
    }
  }
  // ---- battens over the board joints — the relief that reads at walking distance
  const [bw, bp] = OB_BATTEN;
  const spacing = ob.finish === 'board_and_batten' ? 0.6 : 0.4;
  for (const s of [-1, 1]) {
    const n = Math.max(1, Math.floor(A / spacing) - 1);
    for (let i = 1; i <= n; i += 1) {
      const al = -A / 2 + (i * A) / (n + 1);
      const out = s * (D / 2 + bp / 2);
      const top = topAt(s * D / 2);
      if (s > 0 && Math.abs(al - (gable ? -A / 4 : 0)) < (gable ? 1.3 : 0.4)) continue;
      box(al, out, (y0 + top) / 2, bw / 2, bp / 2, (top - y0) / 2);
    }
    const m = Math.max(1, Math.floor(D / spacing) - 1);
    for (let i = 1; i <= m; i += 1) {
      const out = -D / 2 + (i * D) / (m + 1);
      const top = gable ? E + (H - E) * (1 - Math.abs(out) / (D / 2)) - 0.08 : topAt(out) - 0.04;
      box(s * (A / 2 + bp / 2), out, (y0 + top) / 2, bp / 2, bw / 2, (top - y0) / 2);
    }
  }
  // ---- the frame: corner posts and the sill ------------------------------ //
  buf.tint = timber;
  const post = gable ? 0.15 : 0.09;
  for (const [sa, so] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
    const top = topAt(so * D / 2);
    box(sa * (A / 2), so * (D / 2), (y0 + top) / 2, post / 2, post / 2, (top - y0) / 2);
  }
  box(0, D / 2 + 0.01, 0.06, A / 2 + post / 2, 0.06, 0.06 - y0 / 2);
  box(0, -D / 2 - 0.01, 0.06, A / 2 + post / 2, 0.06, 0.06 - y0 / 2);

  // ---- the door(s) ------------------------------------------------------- //
  buf.tint = door;
  if (gable) {
    // A pair of stable doors off-centre on the yard side, a loft door in one gable.
    const dw = Math.min(2.4, A * 0.45);
    const dh = Math.min(2.1, E - 0.25);
    const dc = -A / 4;
    for (const s of [-1, 1]) {
      box(dc + (s * dw) / 4, D / 2 + 0.03, dh / 2, dw / 4 - 0.01, 0.025, dh / 2);
      box(dc + (s * dw) / 4, D / 2 + 0.06, dh * 0.3, dw / 4 - 0.04, 0.015, 0.05);
      box(dc + (s * dw) / 4, D / 2 + 0.06, dh * 0.8, dw / 4 - 0.04, 0.015, 0.05);
    }
    const loftSide = j < 0.5 ? -1 : 1;
    const lh = Math.min(0.9, (H - E) * 0.6);
    box(loftSide * (A / 2 + 0.03), 0, E + 0.05 + lh / 2, 0.025, 0.45, lh / 2);
    // A small stall window on the yard side, shuttered.
    box(A / 4 + 0.2, D / 2 + 0.03, E * 0.62, 0.35, 0.025, 0.3);
  } else {
    const dw = Math.min(0.68, A - 0.36);
    const dh = Math.min(1.78, E - 0.1);
    box(0, D / 2 + 0.025, dh / 2 + 0.02, dw / 2, 0.02, dh / 2);
    // The two ledges a board door is nailed to, and its latch block.
    box(0, D / 2 + 0.05, 0.38, dw / 2 - 0.04, 0.012, 0.05);
    box(0, D / 2 + 0.05, dh - 0.3, dw / 2 - 0.04, 0.012, 0.05);
    box(dw / 2 - 0.08, D / 2 + 0.07, dh * 0.55, 0.03, 0.02, 0.06);
  }

  // ---- the roof ---------------------------------------------------------- //
  buf.tint = roof;
  const over = 0.18;
  const deck = (fromOut, fromY, toOut, toY, overA) => {
    const run = toOut - fromOut;
    const rise = toY - fromY;
    const L = Math.hypot(run, rise);
    const su = [ox * (run / L), rise / L, oz * (run / L)];
    let rn = [AL[1] * su[2] - AL[2] * su[1], AL[2] * su[0] - AL[0] * su[2],
      AL[0] * su[1] - AL[1] * su[0]];
    if (rn[1] < 0) rn = sc(rn, -1);
    const extFrom = over;
    const midOut = (fromOut + toOut) / 2;
    const c = P(0, midOut, (fromY + toY) / 2);
    // Overhang only at the eave end (the `from` end); the top end stops at its line.
    const shift = -extFrom / 2;
    const cc = [c[0] + su[0] * shift + rn[0] * OB_DECK_T / 2,
      c[1] + su[1] * shift + rn[1] * OB_DECK_T / 2,
      c[2] + su[2] * shift + rn[2] * OB_DECK_T / 2];
    pushBoxV(buf, cc, sc(su, L / 2 + extFrom / 2), sc(AL, A / 2 + overA),
      sc(rn, OB_DECK_T / 2), level);
  };
  if (gable) {
    deck(-D / 2, E, 0, H, 0.2);
    deck(D / 2, E, 0, H, 0.2);
    buf.tint = timber;
    box(0, 0, H + 0.02, A / 2 + 0.2, 0.05, 0.06);
  } else {
    // The shed falls toward the alley: the eave end is the back.
    deck(-D / 2, E, D / 2 + over, H + (H - E) * (over / D), 0.12);
  }
  buf.tint = keep;
  return true;
}

/* -------------------------------------------------------------------------- */
/* the layer                                                                   */
/* -------------------------------------------------------------------------- */

async function getJSON(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`);
  return res.json();
}

/** The record's `form` block, read once so no draw reaches into the JSON. */
/**
 * ONE PILE OF BUILDING MATERIAL on a lot that was going up — T-0057, and the other
 * half of Ordinance 9. The ordinance names *timber, stone, brick, boxes and barrels*;
 * T-0040 drew the boxes and barrels at the trading frontages and left these three,
 * because they are a different claim about a different kind of ground — building
 * material belongs to a building that is being BUILT, and only one record in this
 * scene says any building was.
 *
 * THE FRAME IS THE LAYER'S OWN, unchanged: the record's `bearing_deg` is the compass
 * bearing of the face the pile stands off, so along that face is (cos b, sin b) in
 * world XZ and out of it is (sin b, -cos b) — the same two lines every barrel and
 * every signboard in this town is placed by. The pile stands on the TERRAIN at its own
 * point, like everything else on this layer and unlike the boards one layer over.
 *
 * EVERY SIZE IS THE RECORD'S. How many courses a timber pile is, how many blocks a
 * heap holds and how the two brick tiers step are all in `form`, graded and noted
 * there. What is this file's is what a triangle is made of: which way a block of
 * rubble happens to be lying, which is not a claim anybody can make about a heap.
 */
function buildStack(buf, item, form, terrain, level, problems, who) {
  if (WOOD_KINDS.has(item.kind)) return buildWood(buf, item, form, terrain, level, problems, who);
  const at = item.at_local_enu_m;
  if (!Array.isArray(at) || at.length !== 2) return false;
  const base = groundAt(terrain, at[0], at[1]);
  if (base === null) {
    problems.push(`yard: ${who} has no ground under its ${item.kind} — it is not drawn`);
    return false;
  }
  const b = ((item.bearing_deg ?? 0) * Math.PI) / 180;
  const wx = Math.cos(b);
  const wz = Math.sin(b);
  // `pushBox`'s own across-axis, so an offset written here lands where the box's
  // width does.
  const vx = -wz;
  const vz = wx;
  const x = at[0];
  const z = -at[1];

  if (item.kind === 'brick') {
    const [L, W, H] = form.brickStack;
    const [inset, split] = form.brickTier;
    const low = H * split;
    buf.tint = buf.brick;
    pushBox(buf, x, base + low / 2, z, wx, wz, L / 2, W / 2, low / 2, level);
    const up = H - low;
    if (up > 0) {
      pushBox(buf, x, base + low + up / 2, z, wx, wz,
        Math.max(L / 2 - inset, 0.05), Math.max(W / 2 - inset, 0.05), up / 2, level);
    }
    buf.tint = buf.timber;
    return true;
  }

  if (item.kind === 'timber') {
    const [len, sq] = form.timberStick;
    const [per, , short] = form.timberPile;
    const courses = item.courses ?? 4;
    for (let c = 0; c < courses; c += 1) {
      // The top course is short, and it is short at ONE END rather than at both:
      // a pile being worked off loses its sticks from the side the barrow is on,
      // and a symmetrically shortened top reads as a design.
      const top = c === courses - 1 && courses > 1;
      const count = Math.max(1, top ? per - short : per);
      const shift = top ? (short * sq) / 2 : 0;
      for (let i = 0; i < count; i += 1) {
        const acr = (i - (per - 1) / 2) * sq + shift;
        pushBox(buf, x + vx * acr, base + sq / 2 + c * sq, z + vz * acr,
          wx, wz, len / 2, sq / 2, sq / 2, level);
      }
    }
    return true;
  }

  if (item.kind === 'stone') {
    const [bl, bw, bh] = form.stoneBlock;
    const [blocks, tiers] = form.stoneHeap;
    const n = Math.max(1, Math.min(item.blocks ?? blocks, STONE_YAW_DEG.length));
    // The upper tier is the tail of the deal and is drawn pulled toward the middle,
    // which is what makes a tipped load read as a heap and not as two layers.
    const upper = tiers > 1 ? Math.max(1, Math.round(n / 3)) : 0;
    buf.tint = buf.stone;
    for (let i = 0; i < n; i += 1) {
      const high = i >= n - upper;
      const pull = high ? 0.5 : 1.0;
      const [ja, jc] = STONE_JITTER[i];
      const along = ja * 1.0 * pull;
      const acr = jc * 1.2 * pull;
      const yaw = b + (STONE_YAW_DEG[i] * Math.PI) / 180;
      const ux = Math.cos(yaw);
      const uz = Math.sin(yaw);
      pushBox(buf,
        x + wx * along + vx * acr,
        base + (high ? bh * 1.4 : bh / 2),
        z + wz * along + vz * acr,
        ux, uz, bl / 2, bw / 2, bh / 2, level);
    }
    buf.tint = buf.timber;
    return true;
  }

  /**
   * T-1961: THE WORKING TRADES' YARDS. Same frame and same contract as the piles
   * above — the record (`town_trade_yards.json`) owns every size, graded and noted
   * in its `form`, and this owns only what a triangle is made of.
   *
   * A joiner's BOARDS are stacked and stickered to season: each course is boards
   * laid side by side along the pile, on three cross-sticks so the air goes
   * through, which is what makes a pile of boards read as lumber rather than as
   * one block.
   */
  if (item.kind === 'boards') {
    const [len, wide, thick] = form.board;
    const [per, courses, sticker] = form.boardPile;
    const gap = 0.03;
    const span = per * wide + (per - 1) * gap;
    const n = item.courses ?? courses;
    let y = base;
    for (let c = 0; c < n; c += 1) {
      for (const a of [-0.42, 0, 0.42]) {
        pushBox(buf, x + wx * a * len, y + sticker / 2, z + wz * a * len,
          vx, vz, span / 2 + 0.04, 0.025, sticker / 2, level);
      }
      y += sticker;
      for (let i = 0; i < per; i += 1) {
        const acr = -span / 2 + wide / 2 + i * (wide + gap);
        pushBox(buf, x + vx * acr, y + thick / 2, z + vz * acr,
          wx, wz, len / 2, wide / 2, thick / 2, level);
      }
      y += thick;
    }
    return true;
  }

  /**
   * A tanner's HIDES hang folded over a drying rail on two posts. A hide is drawn
   * as a thin slab either side of the rail, hanging the record's drop, in the
   * hide's own tone; the rail and posts are the layer's timber.
   */
  if (item.kind === 'hides') {
    const [len, high, sq] = form.hideRail;
    const [w, drop, t] = form.hide;
    for (const s2 of [-1, 1]) {
      pushBox(buf, x + wx * s2 * (len / 2 - sq), base + high / 2, z + wz * s2 * (len / 2 - sq),
        wx, wz, sq / 2, sq / 2, high / 2, level);
    }
    pushBox(buf, x, base + high + sq / 2, z, wx, wz, len / 2, sq / 2, sq / 2, level);
    const n = Math.max(1, item.hides ?? 3);
    const pitch = (len - 4 * sq) / n;
    buf.tint = buf.hide;
    for (let i = 0; i < n; i += 1) {
      const a = -len / 2 + 2 * sq + pitch * (i + 0.5);
      for (const s2 of [-1, 1]) {
        const off = s2 * (sq / 2 + t);
        pushBox(buf, x + wx * a + vx * off, base + high + sq - drop / 2,
          z + wz * a + vz * off, wx, wz, Math.min(w, pitch * 0.92) / 2, t / 2, drop / 2,
          level);
      }
    }
    buf.tint = buf.timber;
    return true;
  }

  /**
   * A stable's HAY stands in a rick: a body to the eave and a raked top to a
   * ridge along its length, so the rain runs off. The body is a box; the top is
   * two sloped faces and two gable ends, each a plain triangle in the hay's tone.
   */
  if (item.kind === 'hay') {
    const [L, W, eave, ridge] = form.hayRick;
    buf.tint = buf.hay;
    pushBox(buf, x, base + eave / 2, z, wx, wz, L / 2, W / 2, eave / 2, level);
    const P = (a, c, y) => [x + wx * a + vx * c, base + y, z + wz * a + vz * c];
    const lo = eave;
    const hi = ridge;
    const hl = L / 2;
    const hw = W / 2 + 0.06;
    const rise = hi - lo;
    const nl = Math.hypot(rise, hw) || 1;
    for (const s2 of [-1, 1]) {
      const n = [vx * s2 * (rise / nl), hw / nl, vz * s2 * (rise / nl)];
      const a0 = P(-hl, s2 * hw, lo);
      const a1 = P(hl, s2 * hw, lo);
      const r0 = P(-hl, 0, hi);
      const r1 = P(hl, 0, hi);
      // Wound so the face looks out along `n`.
      if (s2 > 0) {
        tri(buf, a0, a1, r1, n, level);
        tri(buf, a0, r1, r0, n, level);
      } else {
        tri(buf, a0, r1, a1, n, level);
        tri(buf, a0, r0, r1, n, level);
      }
      const g = s2 * hl;
      const gn = [wx * s2, 0, wz * s2];
      const e0 = P(g, -hw, lo);
      const e1 = P(g, hw, lo);
      const er = P(g, 0, hi);
      if (s2 > 0) tri(buf, e1, e0, er, gn, level);
      else tri(buf, e0, e1, er, gn, level);
    }
    buf.tint = buf.timber;
    return true;
  }
  return false;
}

/* -------------------------------------------------------------------------- */
/* the woodpiles (T-1959)                                                      */
/* -------------------------------------------------------------------------- */

/**
 * A WOODPILE AT EVERY DWELLING, and it is drawn here rather than in a layer of its
 * own because it is the same kind of thing this file already draws: a small object
 * standing on the town's own ground, derived from a committed footprint, picked to
 * the card of the house it stands behind. `tools/generate_woodpiles.py` deals
 * `data/yard/town_woodpiles.json` from the yard-by-household rule
 * (`tools/yard_rule_1835.py`); this file only draws what that record says.
 *
 * WHAT A STICK LOOKS LIKE IS PAINTED, NOT BUILT. Three hundred piles of split wood
 * built stick by stick would cost the town a hundred thousand triangles and more,
 * and every one of them would be a box that reads as a brick. So a rick is a few
 * dozen faces and the sticks are PAINTED onto them, on the cells of the mark atlas
 * this layer already carries (T-0065): the stick ends on its two long faces, the
 * sticks' bark and split sides on its top and its ends. A cell is a fixed patch of
 * wood (`WOOD_CELL_M` across), so a stick is the same size on a short rick and a
 * long one, and each face samples its own window of the cell so two neighbouring
 * faces never repeat. The silhouette is built, because a painted outline is not one:
 * the top of a rick steps column by column where it has been worked off, its ends
 * are held by stakes, and it stands on two skids off the wet.
 *
 * Everything here that is a CLAIM is the record's (`form`, graded and noted there).
 * What is this file's is only how a stick is drawn: the painting, the column width,
 * the stake's section. Every pile is `reconstructed` at the vertex, so hiding that
 * tier hides the layer.
 */
const WOOD_KINDS = new Set(['cordwood', 'log_heap', 'slab_heap', 'chopping_block']);
/** How much wood one atlas cell depicts, square, in metres. */
const WOOD_CELL_M = 0.85;
/** How far the top of a rick may step between columns, below and above its height. */
const RICK_RAGGED_M = [0.12, 0.04];
const STAKE_M = 0.07;
const SKID_M = 0.1;
const LOG_SIDES = 7;
const BLOCK_SIDES = 7;
const BARK_COLOUR = 0x7a6b5a;
const SPLIT_COLOUR = 0xb59c7a;
/** The three end-grain cells: fresh-split, a season stacked, and silvered. */
const ENDGRAIN = [
  { face: [210, 176, 134], ring: [168, 128, 88], check: [92, 64, 42] },
  { face: [181, 150, 113], ring: [140, 108, 76], check: [74, 54, 38] },
  { face: [150, 142, 130], ring: [118, 110, 100], check: [62, 56, 50] },
];

/** A small deterministic generator, so a pile is the same pile on every load. */
function woodRng(seed) {
  let a = (seed >>> 0) || 1;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rgb = (c, k = 1) => `rgb(${Math.round(c[0] * k)},${Math.round(c[1] * k)},${Math.round(c[2] * k)})`;

/**
 * The stick ends of a rick, one cell: split quarters, halves and whole rounds
 * racked in courses, each with its growth rings drawn round its own pith, its bark
 * edge, and a check or two, on the dark of the gaps between them. Fifty-odd ends to
 * a cell is a 0.13 m stick at 192 px a cell, which is the record's `billet_m`.
 */
function paintEndgrain(ctx, x, y, variant, seed) {
  const rng = woodRng(seed);
  const pal = ENDGRAIN[variant];
  const p = MARK_PAD;
  const s = MARK_TILE - 2 * p;
  ctx.save();
  ctx.beginPath();
  ctx.rect(x + p, y + p, s, s);
  ctx.clip();
  // the shadow between sticks: deep brown, not black — a rick is mostly wood
  ctx.fillStyle = '#3d2f23';
  ctx.fillRect(x + p, y + p, s, s);
  const rows = 5;
  const rh = s / rows;
  for (let r = -1; r <= rows; r += 1) {
    let cx = x + p - rng() * rh;
    while (cx < x + p + s + rh) {
      const w = rh * (0.75 + rng() * 0.5);
      const top = y + p + r * rh + (rng() - 0.5) * rh * 0.12;
      // A split stick's end is an irregular polygon that all but fills its slot: a
      // quarter is a wedge, a half a slab with one round side, a small stick a round.
      const shape = rng();
      const inset = 1.2;
      const x0 = cx + inset;
      const x1 = cx + w - inset;
      const y0 = top + inset;
      const y1 = top + rh - inset;
      const corner = Math.floor(rng() * 4);
      const corners = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
      const [px, py] = shape < 0.55 ? corners[corner]
        : [(x0 + x1) / 2 + (rng() - 0.5) * w * 0.2, shape < 0.85 ? (corner < 2 ? y0 : y1)
          : (y0 + y1) / 2];
      const pts = [];
      const n = 7;
      for (let i = 0; i < n; i += 1) {
        const a = (i / n) * Math.PI * 2;
        const ex = (x0 + x1) / 2 + Math.cos(a) * (x1 - x0) * 0.5 * (0.86 + rng() * 0.2);
        const ey = (y0 + y1) / 2 + Math.sin(a) * (y1 - y0) * 0.5 * (0.86 + rng() * 0.2);
        // a wedge's corner is square, so the polygon reaches its slot's corner there
        const [kx, ky] = corners[corner];
        const toward = shape < 0.55 && Math.hypot(ex - kx, ey - ky) < (x1 - x0) * 0.55;
        pts.push(toward ? [kx, ky] : [Math.max(x0, Math.min(x1, ex)), Math.max(y0, Math.min(y1, ey))]);
      }
      ctx.beginPath();
      pts.forEach(([qx, qy], i) => (i ? ctx.lineTo(qx, qy) : ctx.moveTo(qx, qy)));
      ctx.closePath();
      const k = 0.86 + rng() * 0.24;
      ctx.fillStyle = rgb(pal.face, k);
      ctx.fill();
      ctx.save();
      ctx.clip();
      // sapwood paler at the bark side, the rings round the pith, the checks out of it
      const far = Math.hypot(x1 - x0, y1 - y0);
      ctx.strokeStyle = rgb(pal.ring, k);
      ctx.globalAlpha = 0.4;
      ctx.lineWidth = 1;
      for (let ring = 2 + rng() * 2; ring < far; ring += 2.4 + rng() * 2) {
        ctx.beginPath();
        ctx.arc(px, py, ring, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.globalAlpha = 0.8;
      ctx.strokeStyle = rgb(pal.check);
      ctx.lineWidth = 1.1;
      const checks = Math.floor(rng() * 3);
      for (let c = 0; c < checks; c += 1) {
        const a = rng() * Math.PI * 2;
        ctx.beginPath();
        ctx.moveTo(px, py);
        ctx.lineTo(px + Math.cos(a) * far * (0.3 + rng() * 0.4),
          py + Math.sin(a) * far * (0.3 + rng() * 0.4));
        ctx.stroke();
      }
      // the bark, a thin dark rind on the side away from the pith
      ctx.globalAlpha = 0.9;
      ctx.strokeStyle = '#5a4838';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(px, py, far * 0.98, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
      cx += w;
    }
  }
  ctx.restore();
  return { rx: x + p, ry: y + p, rw: s, rh: s };
}

/**
 * The sticks seen from the side, one cell: courses of bark — grey-brown, fissured
 * along the stick — and of pale split face with its grain, in no order, with the
 * dark line of the gap under each. Drawn with the courses running ACROSS the cell,
 * so a face that shows the sticks lengthwise maps the cell's u along them.
 */
function paintStickSides(ctx, x, y, seed) {
  const rng = woodRng(seed);
  const p = MARK_PAD;
  const s = MARK_TILE - 2 * p;
  ctx.save();
  ctx.beginPath();
  ctx.rect(x + p, y + p, s, s);
  ctx.clip();
  ctx.fillStyle = '#231b14';
  ctx.fillRect(x + p, y + p, s, s);
  const rows = 5;
  const rh = s / rows;
  for (let r = 0; r < rows; r += 1) {
    let cx = x + p - rng() * s * 0.5;
    while (cx < x + p + s) {
      const len = s * (0.7 + rng() * 0.6);
      const top = y + p + r * rh + 1.5;
      const h = rh - 3 + (rng() - 0.5) * 2;
      const bark = rng() < 0.55;
      const k = 0.85 + rng() * 0.25;
      ctx.fillStyle = bark ? rgb([88, 76, 64], k) : rgb([176, 146, 108], k);
      ctx.fillRect(cx, top, len, h);
      ctx.strokeStyle = bark ? 'rgba(34,26,20,0.75)' : 'rgba(110,84,56,0.55)';
      ctx.lineWidth = bark ? 1.4 : 0.8;
      const lines = bark ? 5 : 4;
      for (let l = 0; l < lines; l += 1) {
        const ly = top + h * (0.15 + 0.7 * rng());
        const lx = cx + rng() * len * 0.3;
        ctx.beginPath();
        ctx.moveTo(lx, ly);
        ctx.lineTo(lx + len * (0.3 + rng() * 0.6), ly + (rng() - 0.5) * 2);
        ctx.stroke();
      }
      cx += len + 2 + rng() * 4;
    }
  }
  ctx.restore();
  return { rx: x + p, ry: y + p, rw: s, rh: s };
}

/**
 * One round's sawn end, one cell — the chopping block's top and a log's end: the
 * rings round a pith set a little off centre, the checks a season opens, a bark
 * ring, and on the block the scores an axe leaves.
 */
function paintRound(ctx, x, y, seed) {
  const rng = woodRng(seed);
  const p = MARK_PAD;
  const s = MARK_TILE - 2 * p;
  const cx = x + p + s / 2;
  const cy = y + p + s / 2;
  const R = s / 2;
  ctx.save();
  ctx.fillStyle = '#4a3c30';
  ctx.fillRect(x + p, y + p, s, s);
  ctx.beginPath();
  ctx.arc(cx, cy, R * 0.9, 0, Math.PI * 2);
  ctx.fillStyle = '#b69873';
  ctx.fill();
  ctx.clip();
  const px = cx + (rng() - 0.5) * R * 0.2;
  const py = cy + (rng() - 0.5) * R * 0.2;
  ctx.strokeStyle = 'rgba(126,96,66,0.5)';
  ctx.lineWidth = 1.2;
  for (let ring = 4; ring < R; ring += 3 + rng() * 3) {
    ctx.beginPath();
    ctx.arc(px, py, ring, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.strokeStyle = 'rgba(70,50,34,0.85)';
  ctx.lineWidth = 1.6;
  for (let c = 0; c < 4; c += 1) {
    const a = rng() * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.lineTo(px + Math.cos(a) * R * (0.4 + rng() * 0.5), py + Math.sin(a) * R * (0.4 + rng() * 0.5));
    ctx.stroke();
  }
  ctx.strokeStyle = 'rgba(58,42,30,0.7)';
  ctx.lineWidth = 2;
  for (let c = 0; c < 6; c += 1) {
    const a = rng() * Math.PI;
    const ox = cx + (rng() - 0.5) * R;
    const oy = cy + (rng() - 0.5) * R;
    ctx.beginPath();
    ctx.moveTo(ox - Math.cos(a) * R * 0.25, oy - Math.sin(a) * R * 0.25);
    ctx.lineTo(ox + Math.cos(a) * R * 0.25, oy + Math.sin(a) * R * 0.25);
    ctx.stroke();
  }
  ctx.restore();
  return { rx: x + p, ry: y + p, rw: s, rh: s };
}

/** The wood cells the atlas paints when a woodpile record is loaded. */
function woodCells() {
  const cells = new Map();
  ENDGRAIN.forEach((_, i) => {
    cells.set(`wood|end|${i}`, { paint: (ctx, x, y) => paintEndgrain(ctx, x, y, i, 0x1959 + i) });
  });
  cells.set('wood|sides', { paint: (ctx, x, y) => paintStickSides(ctx, x, y, 0x5ade) });
  cells.set('wood|round', { paint: (ctx, x, y) => paintRound(ctx, x, y, 0x0b10c) });
  return cells;
}

/**
 * A quad, a → b → c → d round its edge, with uvs from a cell window. The winding is
 * put right against the normal here, so a caller lists corners in whatever order the
 * face is easiest to think about.
 */
function pushQuad(buf, a, b, c, d, n, level, uv = null) {
  const e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const e2 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
  const g = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2],
    e1[0] * e2[1] - e1[1] * e2[0]];
  const flip = g[0] * n[0] + g[1] * n[1] + g[2] * n[2] < 0;
  const uvs = uv ?? [null, null, null, null];
  if (!flip) {
    tri(buf, a, b, c, n, level, uv ? [uvs[0], uvs[1], uvs[2]] : null);
    tri(buf, a, c, d, n, level, uv ? [uvs[0], uvs[2], uvs[3]] : null);
  } else {
    tri(buf, a, c, b, n, level, uv ? [uvs[0], uvs[2], uvs[1]] : null);
    tri(buf, a, d, c, n, level, uv ? [uvs[0], uvs[3], uvs[2]] : null);
  }
}

/**
 * The uvs of a quad that shows `su` x `sv` of a cell (each <= 1), at a window the
 * generator chooses — so a short face and a long face show sticks of one size, and
 * two faces side by side do not show the same sticks.
 */
function cellWindow(rect, su, sv, rng) {
  if (!rect) return null;
  const fu = Math.min(1, su);
  const fv = Math.min(1, sv);
  const u0 = (1 - fu) * rng();
  const v0 = (1 - fv) * rng();
  const U = (t) => rect.u0 + (u0 + t * fu) * (rect.u1 - rect.u0);
  const V = (t) => rect.v0 + (v0 + t * fv) * (rect.v1 - rect.v0);
  return [[U(0), V(0)], [U(1), V(0)], [U(1), V(1)], [U(0), V(1)]];
}

/** The lowest ground under a set of (e, n) points, or null if any has none. */
function groundUnder(terrain, pts) {
  let lo = Infinity;
  for (const [e, n] of pts) {
    const g = groundAt(terrain, e, n);
    if (g === null) return null;
    lo = Math.min(lo, g);
  }
  return lo;
}

/**
 * A round of wood: a prism of `sides` faces, its outline a little out of true,
 * bark on the sides and the sawn end painted on the caps. `axis` is unit; the caps
 * at both ends are drawn unless `capLow` is false (a block's foot is in the ground).
 */
function pushRound(buf, c, axis, len, r, sides, level, rng, endRect, capLow = true) {
  const [ax, ay, az] = axis;
  // any vector not parallel to the axis, crossed twice, gives the ring's frame
  const ref = Math.abs(ay) > 0.9 ? [1, 0, 0] : [0, 1, 0];
  let rx = ay * ref[2] - az * ref[1];
  let ry = az * ref[0] - ax * ref[2];
  let rz = ax * ref[1] - ay * ref[0];
  const rl = Math.hypot(rx, ry, rz) || 1;
  rx /= rl; ry /= rl; rz /= rl;
  const sx = ay * rz - az * ry;
  const sy = az * rx - ax * rz;
  const sz = ax * ry - ay * rx;
  const radii = [];
  for (let i = 0; i < sides; i += 1) radii.push(r * (0.9 + rng() * 0.16));
  const at = (t, i) => {
    const k = (i / sides) * Math.PI * 2;
    const rr = radii[i % sides];
    return [
      c[0] + ax * t + (rx * Math.cos(k) + sx * Math.sin(k)) * rr,
      c[1] + ay * t + (ry * Math.cos(k) + sy * Math.sin(k)) * rr,
      c[2] + az * t + (rz * Math.cos(k) + sz * Math.sin(k)) * rr,
    ];
  };
  const h = len / 2;
  const tint = buf.tint;
  buf.tint = buf.bark;
  for (let i = 0; i < sides; i += 1) {
    const k = ((i + 0.5) / sides) * Math.PI * 2;
    const n = [rx * Math.cos(k) + sx * Math.sin(k), ry * Math.cos(k) + sy * Math.sin(k),
      rz * Math.cos(k) + sz * Math.sin(k)];
    pushQuad(buf, at(-h, i), at(-h, i + 1), at(h, i + 1), at(h, i), n, level);
  }
  buf.tint = buf.white;
  const capUV = (i) => {
    if (!endRect) return null;
    const k = (i / sides) * Math.PI * 2;
    return [endRect.u0 + (0.5 + 0.45 * Math.cos(k)) * (endRect.u1 - endRect.u0),
      endRect.v0 + (0.5 + 0.45 * Math.sin(k)) * (endRect.v1 - endRect.v0)];
  };
  for (const sign of capLow ? [-1, 1] : [1]) {
    const n = [ax * sign, ay * sign, az * sign];
    for (let i = 1; i < sides - 1; i += 1) {
      const pts = [at(h * sign, 0), at(h * sign, i), at(h * sign, i + 1)];
      const uvs = endRect ? [capUV(0), capUV(i), capUV(i + 1)] : null;
      // a triangle fan has the winding of its ring, so check it against the normal
      const e1 = [pts[1][0] - pts[0][0], pts[1][1] - pts[0][1], pts[1][2] - pts[0][2]];
      const e2 = [pts[2][0] - pts[0][0], pts[2][1] - pts[0][1], pts[2][2] - pts[0][2]];
      const g = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2],
        e1[0] * e2[1] - e1[1] * e2[0]];
      if (g[0] * n[0] + g[1] * n[1] + g[2] * n[2] >= 0) tri(buf, pts[0], pts[1], pts[2], n, level, uvs);
      else tri(buf, pts[0], pts[2], pts[1], n, level, uvs && [uvs[0], uvs[2], uvs[1]]);
    }
  }
  buf.tint = tint;
}

/**
 * ONE RICK — a stack of split wood racked against a wall. Built as columns across
 * its length, each with its own height, so the top steps where the pile has been
 * worked off; the long faces carry the stick ends, the top and the ends the
 * sticks' sides; two skids under it and a stake at each corner of each end.
 */
function pushRick(buf, x, z, base, wx, wz, L, D, H, level, rng, wood) {
  const vx = -wz;
  const vz = wx;
  const P = (al, ac, yy) => [x + wx * al + vx * ac, yy, z + wz * al + vz * ac];
  const tint = buf.tint;
  // The bottom course stands a hand off the ground — on the skids a rick is built on,
  // which are under the wood and are not drawn.
  const y0 = base + SKID_M;
  const body = Math.max(0.25, H - SKID_M);
  const cols = Math.max(1, Math.ceil(L / WOOD_CELL_M));
  const cw = L / cols;
  // The worked-off end: some ricks have been drawn down at one end since the spring.
  const worked = rng() < 0.45 ? (rng() < 0.5 ? 0 : cols - 1) : -1;
  const tops = [];
  for (let i = 0; i < cols; i += 1) {
    let t = body - RICK_RAGGED_M[0] + rng() * (RICK_RAGGED_M[0] + RICK_RAGGED_M[1]);
    if (i === worked) t *= 0.55 + rng() * 0.25;
    tops.push(y0 + Math.max(0.2, t));
  }
  const ends = wood?.end ?? [];
  const pick = () => (ends.length ? ends[Math.floor(rng() * ends.length)] : null);
  const main = pick();
  const along = [wx, 0, wz];
  const back = [-wx, 0, -wz];
  const out = [vx, 0, vz];
  const across = Math.max(1, Math.ceil(D / WOOD_CELL_M));
  const dw = D / across;
  buf.tint = buf.white;
  for (let i = 0; i < cols; i += 1) {
    const a0 = -L / 2 + i * cw;
    const a1 = a0 + cw;
    const top = tops[i];
    const rows = Math.max(1, Math.ceil((top - y0) / WOOD_CELL_M));
    const rh = (top - y0) / rows;
    // The OUTWARD face only: the other stands a hand's gap off the house wall, where
    // nobody can stand to see it, and its triangles would be a third of the rick's.
    for (const [ac, n] of [[D / 2, out]]) {
      for (let r = 0; r < rows; r += 1) {
        const ya = y0 + r * rh;
        const rect = rng() < 0.8 ? main : pick();
        pushQuad(buf, P(a0, ac, ya), P(a1, ac, ya), P(a1, ac, ya + rh), P(a0, ac, ya + rh),
          n, level, cellWindow(rect, cw / WOOD_CELL_M, rh / WOOD_CELL_M, rng));
      }
    }
    // The top: sticks lie ACROSS the rick, so the cell's courses run along it.
    for (let j = 0; j < across; j += 1) {
      const c0 = -D / 2 + j * dw;
      const c1 = c0 + dw;
      const win = cellWindow(wood?.sides, cw / WOOD_CELL_M, dw / WOOD_CELL_M, rng);
      pushQuad(buf, P(a0, c0, top), P(a0, c1, top), P(a1, c1, top), P(a1, c0, top),
        [0, 1, 0], level, win);
    }
    // The step down to the next column, where the top changes height.
    if (i < cols - 1 && Math.abs(tops[i + 1] - top) > 0.005) {
      const lo = Math.min(top, tops[i + 1]);
      const hi = Math.max(top, tops[i + 1]);
      const n = tops[i + 1] < top ? along : back;
      for (let j = 0; j < across; j += 1) {
        const c0 = -D / 2 + j * dw;
        const c1 = c0 + dw;
        pushQuad(buf, P(a1, c0, lo), P(a1, c1, lo), P(a1, c1, hi), P(a1, c0, hi), n, level,
          cellWindow(wood?.sides, dw / WOOD_CELL_M, (hi - lo) / WOOD_CELL_M, rng));
      }
    }
  }
  // The two ends, which show the sides of the last sticks in each course.
  for (const [al, n, top] of [[-L / 2, back, tops[0]], [L / 2, along, tops[cols - 1]]]) {
    const rows = Math.max(1, Math.ceil((top - y0) / WOOD_CELL_M));
    const rh = (top - y0) / rows;
    for (let r = 0; r < rows; r += 1) {
      for (let j = 0; j < across; j += 1) {
        const c0 = -D / 2 + j * dw;
        const c1 = c0 + dw;
        const ya = y0 + r * rh;
        pushQuad(buf, P(al, c0, ya), P(al, c1, ya), P(al, c1, ya + rh), P(al, c0, ya + rh),
          n, level, cellWindow(wood?.sides, dw / WOOD_CELL_M, rh / WOOD_CELL_M, rng));
      }
    }
  }
  // A stake driven at each end, on the outward side, standing a hand over the wood.
  buf.tint = buf.bark;
  for (const [al, top] of [[-L / 2 - STAKE_M / 2, tops[0]], [L / 2 + STAKE_M / 2, tops[cols - 1]]]) {
    const ac = D / 2 - STAKE_M / 2;
    const h = top - base + 0.12 + 0.15;
    pushBox(buf, x + wx * al + vx * ac, base - 0.15 + h / 2, z + wz * al + vz * ac,
      wx, wz, STAKE_M / 2, STAKE_M / 2, h / 2, level, null, true);
  }
  // And a stick or two thrown across the top, not yet racked.
  buf.tint = buf.split;
  const loose = rng() < 0.45 ? 1 : 0;
  for (let k = 0; k < loose; k += 1) {
    const i = Math.floor(rng() * cols);
    const al = -L / 2 + (i + 0.2 + rng() * 0.6) * cw;
    const yaw = (rng() - 0.5) * 0.5;
    const ux = vx * Math.cos(yaw) + wx * Math.sin(yaw);
    const uz = vz * Math.cos(yaw) + wz * Math.sin(yaw);
    pushBox(buf, x + wx * al, tops[i] + 0.05, z + wz * al, ux, uz,
      Math.min(D, 0.61) / 2, 0.06, 0.05, level, null, true);
  }
  buf.tint = tint;
}

/**
 * THE WOODPILE KINDS, dispatched from `buildStack` — every one stands on the
 * terrain at its own point (the lowest ground under its footprint, so nothing
 * floats on a slope), along the wall the record's bearing names.
 */
function buildWood(buf, item, form, terrain, level, problems, who) {
  const at = item.at_local_enu_m;
  if (!Array.isArray(at) || at.length !== 2) return false;
  const b = ((item.bearing_deg ?? 0) * Math.PI) / 180;
  const wx = Math.cos(b);
  const wz = Math.sin(b);
  const vx = -wz;
  const vz = wx;
  const x = at[0];
  const z = -at[1];
  // (e, n) of a point `al` along and `ac` across, for the ground samples
  const EN = (al, ac) => [at[0] + wx * al + vx * ac, at[1] - (wz * al + vz * ac)];
  const rng = woodRng(item.seed ?? 1);
  const wood = buf.wood;
  const none = () => {
    problems.push(`yard: ${who} has no ground under its ${item.kind} — it is not drawn`);
    return false;
  };

  if (item.kind === 'cordwood') {
    const L = item.length_m ?? 2;
    const D = item.depth_m ?? form.stoveStick;
    const base = groundUnder(terrain, [EN(-L / 2, -D / 2), EN(L / 2, -D / 2),
      EN(L / 2, D / 2), EN(-L / 2, D / 2)]);
    if (base === null) return none();
    pushRick(buf, x, z, base, wx, wz, L, D, item.height_m ?? 1, level, rng, wood);
    return true;
  }

  if (item.kind === 'log_heap') {
    const n = Math.max(1, item.logs ?? 3);
    const len = item.log_length_m ?? 3;
    const [rBig, rSmall] = form.logDiameter;
    const depth = item.depth_m ?? 0.36 * n + 0.3;
    const base = groundUnder(terrain, [EN(-len / 2, -depth / 2), EN(len / 2, -depth / 2),
      EN(len / 2, depth / 2), EN(-len / 2, depth / 2)]);
    if (base === null) return none();
    const tint = buf.tint;
    buf.tint = buf.bark;
    // two cross skids the logs were rolled onto
    for (const s of [-1, 1]) {
      const al = s * len * 0.3;
      pushBox(buf, x + wx * al, base + 0.06, z + wz * al, vx, vz, depth / 2, 0.07, 0.06, level,
        null, true);
    }
    const lower = Math.max(1, Math.ceil(n * 0.6));
    const pitch = depth / (lower + 0.5);
    for (let i = 0; i < n; i += 1) {
      const upper = i >= lower;
      const r = (rSmall + (rBig - rSmall) * rng()) / 2;
      const slot = upper ? (i - lower) + 0.5 : i;
      const ac = -depth / 2 + pitch * (slot + 0.75);
      const al = (rng() - 0.5) * 0.3;
      const y = base + 0.12 + r + (upper ? r * 1.5 : 0);
      const l = len * (0.85 + rng() * 0.15);
      pushRound(buf, [x + wx * al + vx * ac, y, z + wz * al + vz * ac], [wx, 0, wz], l, r,
        LOG_SIDES, level, rng, wood?.round ?? null);
    }
    buf.tint = tint;
    return true;
  }

  if (item.kind === 'slab_heap') {
    const [sl, sw, st] = form.slab;
    const n = Math.max(1, item.pieces ?? 8);
    const base = groundUnder(terrain, [EN(-0.85, -0.65), EN(0.85, -0.65), EN(0.85, 0.65),
      EN(-0.85, 0.65)]);
    if (base === null) return none();
    const tint = buf.tint;
    const laid = [];
    for (let i = 0; i < n; i += 1) {
      const al = (rng() - 0.5) * 0.5;
      const ac = (rng() - 0.5) * 0.7;
      const yaw = b + (rng() - 0.5) * 0.7;
      // a slab lies on whatever is under its middle already
      const under = laid.filter((p) => Math.hypot(p[0] - al, p[1] - ac) < 0.35).length;
      laid.push([al, ac]);
      buf.tint = rng() < 0.5 ? buf.bark : buf.split;
      pushBox(buf, x + wx * al + vx * ac, base + st / 2 + under * st, z + wz * al + vz * ac,
        Math.cos(yaw), Math.sin(yaw), (sl / 2) * (0.75 + rng() * 0.25), sw / 2, st / 2, level,
        null, true);
    }
    buf.tint = tint;
    return true;
  }

  if (item.kind === 'chopping_block') {
    const [bh, bd] = form.block;
    const base = groundAt(terrain, at[0], at[1]);
    if (base === null) return none();
    pushRound(buf, [x, base + bh / 2 - 0.04, z], [0, 1, 0], bh + 0.08, bd / 2, BLOCK_SIDES,
      level, rng, wood?.round ?? null, false);
    // the split sticks lying where they fell, and on some a stick stood on the block
    const tint = buf.tint;
    buf.tint = buf.split;
    const k = Math.max(0, item.billets ?? 3);
    for (let i = 0; i < k; i += 1) {
      const a = rng() * Math.PI * 2;
      const d = 0.45 + rng() * 0.5;
      const ex = at[0] + Math.cos(a) * d;
      const en = at[1] + Math.sin(a) * d;
      const g = groundAt(terrain, ex, en);
      if (g === null) continue;
      const yaw = rng() * Math.PI * 2;
      pushBox(buf, ex, g + 0.04, -en, Math.cos(yaw), Math.sin(yaw), 0.3, 0.05, 0.04, level,
        null, true);
    }
    if (rng() < 0.5) {
      pushBox(buf, x, base + bh + 0.15, z, wx, wz, 0.05, 0.05, 0.15, level, null, true);
    }
    buf.tint = tint;
    return true;
  }
  return false;
}

/** The kinds `buildStack` draws; anything else on a lot is a cask or a case. */
const STACK_KINDS = new Set(['brick', 'timber', 'stone', 'boards', 'hides', 'hay']);

function readForm(record) {
  const f = record?.form ?? {};
  const v = (k, fallback) => (f[k]?.value ?? fallback);
  const crate = v('crate_size_m', [1.05, 0.72, 0.62]);
  const body = v('wagon_body_m', [3.05, 1.07, 0.55]);
  return {
    barrelHeight: v('barrel_height_m', 0.84),
    barrelBelly: v('barrel_belly_diameter_m', 0.53),
    barrelHead: v('barrel_head_diameter_m', 0.45),
    crate,
    crate2Scale: 0.72,
    wagonBody: body,
    wagonBedY: 0.95,
    wagonRearWheel: 1.37,
    wagonFrontWheel: 1.07,
    wagonTongue: 2.75,
    bench: v('bench_size_m', [1.83, 0.36, 0.46]),
    benchPlank: v('bench_plank_m', 0.045),
    wagonTilt: v('wagon_tilt_m', [1.1, 0.12]),
    shedTimber: v('shed_timber_m', [0.14, 0.16]),
    // T-0064's two additions: the two-wheeled cart and the yoke laid by. Same
    // contract as everything above — the record owns the claim, this file owns
    // only what a triangle is made of.
    cart: v('cart_m', [1.98, 1.07, 0.5, 1.42, 0.86, 2.44]),
    // T-0759's one addition: the cask a WATER CART carries. Same contract as
    // every line here — the record owns the claim, and the fallback exists only
    // so a record written before this parcel does not throw.
    hogshead: v('hogshead_m', [1.22, 0.84, 0.7]),
    yoke: v('ox_yoke_m', [1.42, 0.12, 0.34, 0.05]),
    yokeOffset: 1.35,
    // T-0057's building material. Same contract again: every size is the record's
    // claim, graded and noted there, and the fallbacks are only what keeps a record
    // written before this parcel from throwing.
    brickStack: v('brick_stack_m', [2.2, 1.1, 1.05]),
    brickTier: v('brick_tier_m', [0.18, 0.62]),
    timberStick: v('timber_stick_m', [3.66, 0.2, 0.2]),
    timberPile: v('timber_pile', [5, [5, 4], 2]),
    stoneBlock: v('stone_block_m', [0.7, 0.45, 0.35]),
    stoneHeap: v('stone_heap', [9, 2]),
    // T-1961's working yards. Same contract: the record's claim, and fallbacks only
    // so an older record does not throw.
    board: v('board_m', [3.66, 0.3, 0.05]),
    boardPile: v('board_pile', [3, 6, 0.05]),
    hideRail: v('hide_rail_m', [2.4, 1.5, 0.08]),
    hide: v('hide_m', [0.55, 1.0, 0.012]),
    hayRick: v('hay_rick_m', [3.0, 2.0, 1.5, 2.4]),
    // T-1959's woodpiles. The same contract once more: the record owns every size.
    stoveStick: v('stove_stick_m', 0.61),
    logDiameter: v('log_m', [0.32, 0.22]),
    block: v('block_m', [0.5, 0.46]),
    slab: v('slab_m', [1.4, 0.26, 0.06]),
  };
}

/**
 * THE BOARD FACE ON THE GOODS (T-2121): the walk's grain, bound on `uv1`.
 *
 * The layer keeps its ONE material and its one draw call per chunk. Its `map` is the
 * mark atlas on `uv` (T-0065) and stays so; the grain rides on the second uv set:
 *   normalMap   the board face's relief — a CLONE of the walks' texture with its
 *               `channel` set to 1, which shares the walks' image and upload
 *   uChiGrain   the face's albedo modulation, multiplied into the diffuse after the
 *               atlas and before the vertex tone, exactly as the walk wears it
 * and both are switched off, per vertex, where `uv1` holds the NO_GRAIN sentinel —
 * duck, iron, brick, stone, hay and hides stay as smooth as they were.
 */
function bindGrain(mat, grain) {
  const normalMap = grain.normalMap.clone();
  normalMap.channel = 1;
  normalMap.needsUpdate = true;
  mat.normalMap = normalMap;
  // A little deeper than the walk wears it: a cask or a wagon side is seen close and
  // across the grain, where a walk is seen grazing along it.
  mat.normalScale.set(GRAIN_NORMAL_SCALE, GRAIN_NORMAL_SCALE);
  // The packed occlusion/roughness: R darkens the checks and the open grain in the
  // ambient light, G roughens and smooths it, so worn faces catch the sun differently
  // from the raised grain beside them. Rescaled so its mean lands on the layer's 0.88.
  let orm = null;
  if (grain.ormMap) {
    orm = grain.ormMap.clone();
    orm.channel = 1;
    orm.needsUpdate = true;
    mat.roughnessMap = orm;
    mat.aoMap = orm;
    mat.roughness = 0.88 / (grain.meanRough || 0.88);
  }
  const uniforms = {
    uChiGrainMod: { value: grain.modMap },
    uChiGrainHead: { value: grain.headroom },
    uChiGrainTile: { value: 1 / (grain.tileM || GRAIN_TILE_M) },
  };
  const prior = mat.onBeforeCompile;
  mat.onBeforeCompile = function (shader, renderer) {
    prior?.call(this, shader, renderer);
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = /* glsl */`
uniform float uChiGrainTile;
varying float vChiGrain;
varying vec2 vChiGrainUv;
` + shader.vertexShader.replace('#include <uv_vertex>', /* glsl */`
#include <uv_vertex>
vChiGrain = uv1.x > ${(NO_GRAIN[0] / 2).toFixed(1)} ? 1.0 : 0.0;
vChiGrainUv = uv1 * uChiGrainTile;
`);
    shader.fragmentShader = /* glsl */`
uniform sampler2D uChiGrainMod;
uniform float uChiGrainHead;
varying float vChiGrain;
varying vec2 vChiGrainUv;
` + shader.fragmentShader
      .replace('#include <map_fragment>', /* glsl */`
#include <map_fragment>
diffuseColor.rgb *= mix(1.0, texture2D(uChiGrainMod, vChiGrainUv).r * uChiGrainHead, vChiGrain);
`)
      .replace('#include <normal_fragment_maps>', /* glsl */`
if (vChiGrain > 0.5) {
#include <normal_fragment_maps>
}
`)
      .replace('#include <roughnessmap_fragment>', /* glsl */`
#include <roughnessmap_fragment>
roughnessFactor = mix(${(0.88).toFixed(2)}, roughnessFactor, vChiGrain);
`)
      .replace('#include <aomap_fragment>', /* glsl */`
if (vChiGrain > 0.5) {
#include <aomap_fragment>
}
`);
  };
  return [normalMap, orm].filter(Boolean);
}

/**
 * @param {object} o dataBase (data/ root) · terrain · confidence · problems
 * @returns {Promise<{group: THREE.Group, records: object[], census: object,
 *                    pickAt: function, dispose: function}>}
 */
export async function createYardGoods({
  dataBase, terrain, confidence = null, problems = [],
  /** T-1126: does this structure's geometry exist in the scene? Goods stand on
   *  the footway of a building that is there; when the building is not, the
   *  crates in the grass are the only thing left saying it was, which is worse
   *  than an empty lot. See `createSignage` for the whole argument. */
  hostMissing = () => false,
} = {}) {
  const group = new THREE.Group();
  group.name = 'yard';
  const out = {
    group,
    records: [],
    frontages: [],
    lots: [],
    woodpiles: [],
    wagons: [],
    benches: [],
    sheds: [],
    outbuildings: [],
    census: { records: 0, frontages: 0, objects: 0, barrels: 0, crates: 0, wagons: 0,
      byKind: {}, benches: 0, sheds: 0, outbuildings: 0, byOutbuilding: {}, refused: 0, wagonsRefused: 0, chunks: 0,
      marked: 0, markCells: 0, lots: 0, piles: 0, orphaned: 0, byMaterial: {},
      woodpiles: 0, woodByKind: {}, woodChunks: 0, relief: null },
    pickAt: () => null,
    dispose: () => {},
  };

  if (!dataBase || !terrain) {
    problems.push('yard: no data base or no terrain — nothing is stood out');
    return out;
  }
  let index;
  try {
    index = await getJSON(new URL('yard/index.json', dataBase));
  } catch (err) {
    // Degrade to NOTHING drawn plus a recorded problem, never to an invented
    // barrel: the same contract the enclosure, signage and vegetation layers keep.
    problems.push(`yard: ${err.message} — no goods are stood out`);
    return out;
  }
  // T-2121: the plank walks' board face, shared with them (one copy in memory),
  // loading beside the records; the material waits for it below.
  const reliefP = loadTimberRelief(resolveBases().assetBase);
  const wanted = Array.isArray(index.yard) ? index.yard : [];
  const loaded = await Promise.all(wanted.map(async (y) => {
    if (!y.file) return [y.id, null, 'the manifest gave no file'];
    try {
      return [y.id, await getJSON(new URL(`yard/${y.file}`, dataBase)), null];
    } catch (err) { return [y.id, null, err.message]; }
  }));

  /**
   * THE MARKS ARE COLLECTED BEFORE ANYTHING IS DRAWN (T-0065), because a
   * vertex cannot be given a uv into a cell that does not exist yet. Two casks
   * stencilled FLOUR at opposite ends of the town share one cell — the key is
   * the wording, the letterform and the shape it is painted on, and nothing
   * else — which is what keeps seventy-odd marks in one atlas instead of a
   * hundred and forty-eight.
   */
  const markCells = new Map();
  for (const [, record] of loaded) {
    if (!record) continue;
    const f = readForm(record);
    // A case's face is as wide as the case and as tall; a cask's bilge band is
    // as wide as the arc it is painted on — the developed length of
    // `BILGE_STAVES` of the belly, not its chord, because paint follows the
    // stave — and as tall as the cask. A head is a disc, so it is square.
    const shapes = {
      case: (f.crate[0] || 1) / (f.crate[2] || 1),
      bilge: ((f.barrelBelly / 2) * BILGE_STAVES * ((Math.PI * 2) / BARREL_SIDES))
        / (f.barrelHeight || 1),
      head: 1,
    };
    for (const frontage of record.frontages ?? []) {
      for (const item of frontage.items ?? []) {
        const mark = item.mark;
        if (!mark || !Array.isArray(mark.lines) || !mark.lines.length) continue;
        let shape = 'bilge';
        if (item.kind === 'crate') shape = 'case';
        else if (item.pose === 'laid') shape = 'head';
        const key = markKey(mark, shape);
        if (!markCells.has(key)) {
          markCells.set(key, { mark, shape, aspect: shapes[shape] });
        }
      }
    }
  }
  // T-1959. The woodpiles' sticks are painted on cells of this same atlas, so they
  // cost the layer no material and no texture it did not already have.
  const hasWood = loaded.some(([, r]) => (r?.lots ?? []).some(
    (lot) => (lot.items ?? []).some((it) => WOOD_KINDS.has(it.kind))));
  if (hasWood) for (const [key, cell] of woodCells()) markCells.set(key, cell);
  const atlas = markCells.size ? buildMarkAtlas(markCells) : null;
  const woodRects = atlas && hasWood ? {
    end: ENDGRAIN.map((_, i) => atlas.rects.get(`wood|end|${i}`)).filter(Boolean),
    sides: atlas.rects.get('wood|sides') ?? null,
    round: atlas.rects.get('wood|round') ?? null,
  } : null;
  if (markCells.size && !atlas) {
    // No document, or a context refused: the goods stand exactly as T-0040
    // shipped them, unmarked. A degradation with a name, not a silent one.
    problems.push('yard: no canvas to paint the goods\u2019 marks on — the barrels and '
      + 'cases are drawn unmarked');
  }
  /** The cell a mark is painted in, or null when there is no atlas. */
  const markRect = (mark, shape) => {
    if (!atlas) return null;
    return atlas.rects.get(markKey(mark, shape)) ?? null;
  };
  out.census.markCells = atlas ? atlas.cells : 0;

  /**
   * THE TINT IS PART OF THE BUFFER, not of the material. One material, one draw
   * call, and a per-vertex colour is what lets the tilt's canvas be canvas
   * without a second mesh — `buf.tint` is whatever the current primitive is
   * being drawn in and every push reads it. Converted through `THREE.Color`
   * because the attribute is read in the renderer's working colour space and
   * these constants are sRGB hexes.
   */
  const timber = new THREE.Color(GOODS_COLOUR);
  const canvasTone = new THREE.Color(CANVAS_COLOUR);
  // Brick goes in as the material sheet's own LINEAR triple; `setRGB` defaults to the
  // working colour space, so no conversion happens and none can go wrong.
  const brickTone = new THREE.Color().setRGB(...BRICK_LINEAR);
  const stoneTone = new THREE.Color(STONE_COLOUR);
  const hayTone = new THREE.Color(HAY_COLOUR);
  const hideTone = new THREE.Color(HIDE_COLOUR);
  const tones = {
    timber: [timber.r, timber.g, timber.b],
    canvas: [canvasTone.r, canvasTone.g, canvasTone.b],
    brick: [brickTone.r, brickTone.g, brickTone.b],
    stone: [stoneTone.r, stoneTone.g, stoneTone.b],
    hay: [hayTone.r, hayTone.g, hayTone.b],
    hide: [hideTone.r, hideTone.g, hideTone.b],
  };
  // T-1959: a woodpile's bark and split faces, and white for a face whose colour is
  // all in its painted cell. Without an atlas a painted face would read white, so it
  // falls back to the split tone and the pile is still wood.
  const barkTone = new THREE.Color(BARK_COLOUR);
  const splitTone = new THREE.Color(SPLIT_COLOUR);
  tones.bark = [barkTone.r, barkTone.g, barkTone.b];
  tones.split = [splitTone.r, splitTone.g, splitTone.b];
  tones.white = woodRects ? [1, 1, 1] : tones.split;
  // T-2121: iron, and the tones that are never wood and so never carry its grain.
  tones.iron = toneOf(IRON_COLOUR);
  tones.bare = new Set([tones.canvas, tones.brick, tones.stone, tones.hay, tones.hide,
    tones.white, tones.bark, tones.split, tones.iron]);
  /**
   * THE CHUNKS, and what decides which one a thing goes in: WHERE IT STANDS.
   * Every object on this layer is anchored at a point in local ENU, so the
   * bucket is that point's `CHUNK_M` cell and nothing else — no sorting, no
   * clustering pass, and the same answer every load. Objects that belong to one
   * frontage go in one bucket even if a case at the far end of a long wall would
   * technically fall over a boundary: a frontage is one pick target and one
   * bounding sphere's worth of ground, and splitting it would buy nothing.
   *
   * WHICH BUSINESS A TRIANGLE BELONGS TO is still a span table, per chunk. The
   * fences answered the same question with `userData.pickId` once they chunked,
   * because a fence chunk is one record's timber — but a yard chunk is a block
   * of the town and holds three shops' barrels and a wagon that belongs to
   * nobody, so the range each object emitted is still the only honest answer.
   */
  const chunks = new Map();
  const chunkAt = (e, n) => {
    const key = `${Math.floor(e / CHUNK_M)},${Math.floor(n / CHUNK_M)}`;
    let chunk = chunks.get(key);
    if (!chunk) {
      chunk = {
        key,
        buf: { pos: [], nrm: [], conf: [], col: [], uv: [], uv1: [], ...tones,
          tint: tones.timber, blank: atlas ? atlas.blank : [0, 0], wood: woodRects },
        spans: [],
      };
      chunks.set(key, chunk);
    }
    return chunk;
  };
  /**
   * WHERE A WOODPILE GOES (T-1959): into ONE mesh for the whole town, in a group of
   * its own. Every chunk is a draw call wherever it is in view and a second one in the
   * sun's pass, and the call budget is the one that binds — the worst stand reads 210
   * of 215 without the woodpiles. Measured on the published mirror at `full`, at
   * back-lot stands: chunks three cells across (19 of them) cost 9-20 calls, eight
   * across (5) still 6-11, and goods chunks shared with one outlying mesh 2-6. One mesh
   * costs exactly two, everywhere. What it gives up is the frustum's cull on three
   * hundred piles of about a hundred triangles each — the cheaper side of the trade.
   * It also keeps the goods' chunks exactly what the gate measures them as: timber,
   * duck, brick and stone, and a pile reach written for the building material.
   */
  const woodChunks = new Map();
  const woodChunkAt = () => {
    const key = 'w-town';
    let chunk = woodChunks.get(key);
    if (!chunk) {
      chunk = {
        key,
        // The woodpiles' sticks are painted in the atlas (T-1959) and carry no
        // board-face grain over that.
        buf: { pos: [], nrm: [], conf: [], col: [], uv: [], uv1: [], ...tones,
          tint: tones.timber, blank: atlas ? atlas.blank : [0, 0], wood: woodRects,
          grainOn: false },
        spans: [],
      };
      woodChunks.set(key, chunk);
    }
    return chunk;
  };
  /** The anchor a group of objects is bucketed by — the first one that has one. */
  const anchorOf = (things) => {
    for (const t of things) {
      const at = t?.at_local_enu_m;
      if (Array.isArray(at) && at.length === 2) return at;
    }
    return null;
  };
  /** Emit into one chunk, banking the triangle range under `id` if there is one. */
  const emit = (chunk, id, draw) => {
    const from = chunk.buf.pos.length / 9;
    const drew = draw(chunk.buf);
    if (!drew) return false;
    if (id) chunk.spans.push({ id, from, to: chunk.buf.pos.length / 9 });
    return true;
  };

  for (const [id, record, why] of loaded) {
    if (!record) { problems.push(`yard: ${id} — ${why}`); continue; }
    out.records.push(record);
    out.census.records += 1;
    out.census.refused += (record.refused ?? []).length;
    out.census.wagonsRefused += (record.wagons_refused ?? []).length;
    const form = readForm(record);
    const level = LEVEL[record.existence?.confidence] ?? 1;
    for (const frontage of record.frontages ?? []) {
      if (hostMissing(frontage.structure_id)) { out.census.orphaned += 1; continue; }
      const anchor = anchorOf(frontage.items ?? []);
      if (!anchor) continue;
      const chunk = chunkAt(anchor[0], anchor[1]);
      let drew = 0;
      const from = chunk.buf.pos.length / 9;
      for (const item of frontage.items ?? []) {
        if (!buildItem(chunk.buf, item, form, terrain,
          LEVEL[frontage.confidence] ?? level, problems, frontage.structure_id,
          markRect)) continue;
        drew += 1;
        out.census.objects += 1;
        if (item.kind === 'barrel') out.census.barrels += 1;
        if (item.kind === 'crate') out.census.crates += 1;
        if (item.mark && atlas) out.census.marked += 1;
      }
      if (!drew) continue;
      chunk.spans.push({ id: frontage.structure_id, from,
        to: chunk.buf.pos.length / 9 });
      out.frontages.push(frontage);
      out.census.frontages += 1;
    }
    /**
     * THE LOTS THAT WERE GOING UP (T-0057). Same shape as a frontage and for the same
     * reason: a lot's piles are one pick target — aim at a stack of brick and the
     * Lake House's card opens — so they go in one chunk and bank one span, exactly as
     * a shop's barrels do.
     */
    for (const lot of record.lots ?? []) {
      if (hostMissing(lot.structure_id)) { out.census.orphaned += 1; continue; }
      const anchor = anchorOf(lot.items ?? []);
      if (!anchor) continue;
      // A woodpile lot (T-1959) is the same shape and the same pick, but it is not
      // building material: it goes in the woodpile mesh and is counted on its own, so
      // `lots`, `piles` and `byMaterial` still mean what Ordinance 9's half says.
      const woodpile = (lot.items ?? []).some((it) => WOOD_KINDS.has(it.kind));
      const chunk = woodpile ? woodChunkAt() : chunkAt(anchor[0], anchor[1]);
      let drew = 0;
      const from = chunk.buf.pos.length / 9;
      for (const item of lot.items ?? []) {
        // T-1961: a cooper's or a packer's casks stand on a lot as a rank, so a
        // lot can hold barrels as well as piles; the frontage's own builder draws
        // them, unmarked. A woodpile's kinds (T-1959) go to `buildStack` too, which
        // hands them to `buildWood`.
        const draw = STACK_KINDS.has(item.kind) || WOOD_KINDS.has(item.kind)
          ? buildStack : buildItem;
        if (!draw(chunk.buf, item, form, terrain,
          LEVEL[lot.confidence] ?? level, problems, lot.structure_id)) continue;
        drew += 1;
        out.census.objects += 1;
        const tally = woodpile ? out.census.woodByKind : out.census.byMaterial;
        tally[item.kind] = (tally[item.kind] ?? 0) + 1;
        if (!woodpile) out.census.piles += 1;
      }
      if (!drew) continue;
      chunk.spans.push({ id: lot.structure_id, from,
        to: chunk.buf.pos.length / 9 });
      if (woodpile) {
        out.woodpiles.push(lot);
        out.census.woodpiles += 1;
      } else {
        out.lots.push(lot);
        out.census.lots += 1;
      }
    }
    for (const wagon of record.wagons ?? []) {
      // A wagon in a yard goes with the yard's building; one standing in a public
      // street names no owner, so `hostMissing` is never asked about it and it
      // stays. That is the right answer both ways round — the street is there.
      if (hostMissing(wagon.belongs_to)) { out.census.orphaned += 1; continue; }
      const at = wagon.at_local_enu_m;
      if (!Array.isArray(at) || at.length !== 2) continue;
      // A CART IS NOT A WAGON WITH TWO WHEELS MISSING, so the record's `kind`
      // picks the builder rather than a flag inside one. `farm_box` is the
      // default for a record written before T-0064 gave the field a name.
      const build = (wagon.kind === 'cart' ? buildCart : buildWagon);
      // A wagon standing in a yard belongs to the building whose yard it is, so a
      // pick on it opens that card. `belongs_to` names it; without one the wagon
      // is unpickable and the aim falls through, which is the fences' behaviour —
      // and it is the RIGHT answer for a wagon standing in a public street, which
      // belongs to nobody this record can name.
      if (!emit(chunkAt(at[0], at[1]), wagon.belongs_to,
        (b) => build(b, wagon, form, terrain, LEVEL[wagon.confidence] ?? level,
          problems))) continue;
      out.wagons.push(wagon);
      out.census.wagons += 1;
      out.census.byKind[wagon.kind ?? 'farm_box'] =
        (out.census.byKind[wagon.kind ?? 'farm_box'] ?? 0) + 1;
      out.census.objects += 1;
    }
    for (const bench of record.benches ?? []) {
      const at = bench.at_local_enu_m;
      if (!Array.isArray(at) || at.length !== 2) continue;
      // Same pick contract as the wagons: a bench against an inn's front wall
      // belongs to that inn, so aiming at it opens the inn's card.
      if (!emit(chunkAt(at[0], at[1]), bench.belongs_to,
        (b) => buildItem(b, bench, form, terrain, LEVEL[bench.confidence] ?? level,
          problems, bench.belongs_to ?? bench.id))) continue;
      out.benches.push(bench);
      out.census.benches += 1;
      out.census.objects += 1;
    }
    for (const shed of record.sheds ?? []) {
      const at = shed.at_local_enu_m;
      if (!Array.isArray(at) || at.length !== 2) continue;
      // Same pick contract as the wagons and the bench: the shed at an inn's
      // yard end belongs to that inn, so aiming at it opens the inn's card.
      if (!emit(chunkAt(at[0], at[1]), shed.belongs_to,
        (b) => buildShed(b, shed, form, terrain, LEVEL[shed.confidence] ?? level,
          problems))) continue;
      out.sheds.push(shed);
      out.census.sheds += 1;
      out.census.objects += 1;
    }
    /**
     * THE YARD OUTBUILDINGS (T-1960): a privy behind every house the record reaches and a
     * stable for the horse-keepers. Same pick contract as the shed: a privy belongs to
     * the house whose yard it stands in, so aiming at it opens that house's card — and
     * when that house is not in the scene its privy is not either.
     */
    for (const ob of record.outbuildings ?? []) {
      if (hostMissing(ob.belongs_to)) { out.census.orphaned += 1; continue; }
      const at = ob.at_local_enu_m;
      if (!Array.isArray(at) || at.length !== 2) continue;
      if (!emit(chunkAt(at[0], at[1]), ob.belongs_to,
        (b) => buildOutbuilding(b, ob, terrain, LEVEL[ob.confidence] ?? level,
          problems))) continue;
      out.outbuildings.push(ob);
      out.census.outbuildings += 1;
      out.census.byOutbuilding[ob.kind] = (out.census.byOutbuilding[ob.kind] ?? 0) + 1;
      out.census.objects += 1;
    }
  }
  const built = [...chunks.values()].filter((c) => c.buf.pos.length);
  const woodBuilt = [...woodChunks.values()].filter((c) => c.buf.pos.length)
    .sort((a, b) => (a.key < b.key ? -1 : 1));
  if (!built.length && !woodBuilt.length) {
    if (out.census.records) {
      problems.push('yard: the records loaded and not one object was stood out');
    }
    return out;
  }
  // Sorted by key so the scene graph is the same on every load — a chunk order
  // that depended on Map insertion would depend on the record's own order, and a
  // gate comparing two runs would be comparing two orders.
  built.sort((a, b) => (a.key < b.key ? -1 : 1));

  /**
   * White, and the colour comes off the geometry. `<color_fragment>` multiplies
   * the vertex colour into the diffuse, and `confidence.patch()` tints AFTER
   * that include — so the amber of the confidence view still reads on a canvas
   * tilt exactly as it does on a barrel.
   */
  const mat = new THREE.MeshStandardMaterial({
    color: 0xffffff, vertexColors: true, roughness: 0.88, metalness: 0.0,
  });
  /**
   * AND THE MARKS RIDE ON THE SAME MATERIAL (T-0065). `<map_fragment>` runs
   * before `<color_fragment>`, so the atlas multiplies first and the vertex
   * tone second: a stencil on a cask is paint on that cask's own timber, and a
   * mark on the canvas tilt would be paint on canvas — which is exactly right,
   * and is why the marks did not need a material of their own. Everything
   * unmarked samples the atlas's white cell and is unchanged to the bit.
   */
  if (atlas) mat.map = atlas.texture;
  mat.name = 'yard-goods-timber';
  const grain = await reliefP;
  if (grain.problem) problems.push(`yard: ${grain.problem} — the goods are drawn without grain`);
  const grainMaps = grain.problem ? [] : bindGrain(mat, grain);
  out.census.relief = grain.problem ? null : grain.id;
  confidence?.patch(mat);
  /**
   * ITS OWN PROGRAM CACHE KEY, AND WHY THIS LINE IS NOT OPTIONAL. three caches a
   * compiled program under a key ending in `material.customProgramCacheKey()`,
   * whose default is the SOURCE TEXT of `onBeforeCompile` — so every material
   * `confidence.patch()` touches reports the same key, and two patched materials
   * that agree on their other program parameters share one program. The
   * enclosure layer was drawn in solid black by a building's shader that way,
   * with no page error and no warning. This layer is the same shape of material
   * and would walk into the same collision; ticket T-0053 is the general fix.
   */
  mat.customProgramCacheKey = () => (grain.problem ? 'chicago4d-yard-goods-timber'
    : 'chicago4d-yard-goods-timber-grain');

  const meshes = [];
  /**
   * THE WOODPILE MESH HANGS IN A GROUP OF ITS OWN, named as this layer is, so the
   * furniture reach and the far merge (both of which find a layer by its group's
   * name) treat it exactly as they treat the goods. Its own group because it is its
   * own grid: the goods' chunks are `CHUNK_M` cells and this is the whole town.
   */
  const woodGroup = new THREE.Group();
  woodGroup.name = 'yard';
  woodGroup.userData.woodpiles = true;
  for (const chunk of [...built, ...woodBuilt]) {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(chunk.buf.pos, 3));
    geo.setAttribute('normal', new THREE.Float32BufferAttribute(chunk.buf.nrm, 3));
    geo.setAttribute('_confidence',
      new THREE.Float32BufferAttribute(chunk.buf.conf, 1));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(chunk.buf.col, 3));
    if (atlas) geo.setAttribute('uv', new THREE.Float32BufferAttribute(chunk.buf.uv, 2));
    if (!grain.problem) {
      geo.setAttribute('uv1', new THREE.Float32BufferAttribute(chunk.buf.uv1, 2));
    }
    // The whole point of the chunk: its own bounding sphere, around its own
    // block of the town, so the frustum can leave it out.
    geo.computeBoundingSphere();
    // The geometry holds a Float32 copy now; the JS arrays (twice its size) are
    // scratch, and the chunk maps would otherwise keep them for the life of the
    // page (T-2063 — what got the 1835 tab killed on an iPhone).
    chunk.buf.pos = chunk.buf.nrm = chunk.buf.conf = chunk.buf.col = chunk.buf.uv = null;
    chunk.buf.uv1 = null;
    const mesh = new THREE.Mesh(geo, mat);
    mesh.name = 'yard-chunk';
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.spans = chunk.spans;
    if (woodChunks.has(chunk.key)) {
      mesh.name = 'yard-woodpile-chunk';
      woodGroup.add(mesh);
    } else {
      group.add(mesh);
    }
    meshes.push(mesh);
  }
  if (woodGroup.children.length) group.add(woodGroup);
  out.census.woodChunks = woodGroup.children.length;
  out.census.chunks = meshes.length - out.census.woodChunks;
  group.userData.census = out.census;

  const raycaster = new THREE.Raycaster();
  /** The business these goods stand at, or null. Same ray budget as the boards. */
  out.pickAt = (ndc, camera) => {
    if (!camera) return null;
    raycaster.setFromCamera(ndc ?? new THREE.Vector2(0, 0), camera);
    raycaster.far = Math.max(400, camera.position.y * 4);
    // A raycast does not skip what is hidden, so the woodpiles' group, which the
    // `light` tier hides (main.js, T-1959), is left out of it while it is hidden.
    const hits = raycaster.intersectObjects(
      meshes.filter((m) => !m.parent?.userData.woodpiles || m.parent.visible), false);
    if (!hits.length) return null;
    const hit = hits[0];
    // The span table is the CHUNK's, so a hit resolves against the objects that
    // chunk actually holds and a face index cannot be read against another
    // block's table.
    const spans = hit.object?.userData?.spans ?? [];
    const span = spans.find((sp) => hit.faceIndex >= sp.from && hit.faceIndex < sp.to);
    if (!span) return null;
    return { id: span.id, point: hit.point.clone(), distance: hit.distance };
  };

  out.dispose = () => {
    for (const m of meshes) m.geometry.dispose();
    atlas?.texture?.dispose();
    mat.dispose();
    grain.dispose?.();
    for (const t of grainMaps) t.dispose();
  };
  return out;
}
