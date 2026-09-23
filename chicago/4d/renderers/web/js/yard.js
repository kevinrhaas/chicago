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
const BARREL_SIDES = 10;
const WHEEL_SIDES = 12;
/**
 * T-0064 CUT TWO OF THESE, and both cuts are the same argument the barrel's
 * missing hoops already make: triangles spent on something the eye cannot
 * resolve. The wheel keeps its 12 sides — a 1.37 m wheel at 10 would show its
 * facets to anyone standing beside it — but a wheel used to carry SIX spoke
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
 * are the tightest number in this scene (T-0115). At 100 m a chunk is about a
 * platted block and a half, which is the distance over which a visitor either
 * sees all of it or none of it.
 */
const CHUNK_M = 100;

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
    const { mark, shape, aspect } = wanted.get(key);
    const r = paintMark(ctx, x, y, mark, shape, aspect);
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
 * One box, 12 triangles, flat-shaded from its own face normals. `u` is the
 * horizontal unit vector along the box's length; up is world Y always.
 * Deliberately the same helper shape as the enclosure and signage layers' —
 * three layers drawing small timber the same way is one thing to reason about.
 */
function pushBox(buf, cx, cy, cz, ux, uz, halfLen, halfW, halfH, level,
  markRect = null) {
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
    [[1, 5, 6], [1, 6, 2], [ux, 0, uz]],
    [[4, 0, 3], [4, 3, 7], [-ux, 0, -uz]],
    [[3, 2, 6], [3, 6, 7], [vx, 0, vz]],
    [[0, 4, 5], [0, 5, 1], [-vx, 0, -vz]],
    [[4, 7, 6], [4, 6, 5], [0, 1, 0]],
    [[0, 1, 2], [0, 2, 3], [0, -1, 0]],
  ];
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
  faces.forEach(([t1, t2, n], fi) => {
    const marked = markRect && fi === 3;
    for (const t of [t1, t2]) {
      for (const i of t) {
        buf.pos.push(p[i][0], p[i][1], p[i][2]);
        buf.nrm.push(n[0], n[1], n[2]);
        buf.conf.push(level);
        buf.col.push(buf.tint[0], buf.tint[1], buf.tint[2]);
        const uv = marked ? uvAt(i) : buf.blank;
        buf.uv.push(uv[0], uv[1]);
      }
    }
  });
}

function tri(buf, a, b, c, n, level, uvs = null) {
  const P = [a, b, c];
  for (let i = 0; i < 3; i += 1) {
    const p = P[i];
    buf.pos.push(p[0], p[1], p[2]);
    buf.nrm.push(n[0], n[1], n[2]);
    buf.conf.push(level);
    // `buf.tint` is the colour the caller is currently drawing in, in the
    // renderer's working colour space. Every primitive on this layer goes
    // through here or through `pushBox`, so nothing can be emitted untinted.
    buf.col.push(buf.tint[0], buf.tint[1], buf.tint[2]);
    // And `buf.blank` is the white cell of the mark atlas (T-0065). Everything
    // that is not a marked face samples it, which multiplies to exactly the
    // timber the layer drew before it had a texture at all.
    const uv = uvs ? uvs[i] : buf.blank;
    buf.uv.push(uv[0], uv[1]);
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
  const unit = (v) => {
    const L = Math.hypot(v[0], v[1], v[2]) || 1;
    return [v[0] / L, v[1] / L, v[2] / L];
  };
  const P = (a, b, d) => [
    c[0] + ea[0] * a + eb[0] * b + ec[0] * d,
    c[1] + ea[1] * a + eb[1] * b + ec[1] * d,
    c[2] + ea[2] * a + eb[2] * b + ec[2] * d,
  ];
  const na = unit(ea);
  const nb = unit(eb);
  const nc = unit(ec);
  const neg = (v) => [-v[0], -v[1], -v[2]];
  const faces = [
    [P(1, -1, -1), P(1, 1, -1), P(1, 1, 1), P(1, -1, 1), na],
    [P(-1, 1, -1), P(-1, -1, -1), P(-1, -1, 1), P(-1, 1, 1), neg(na)],
    [P(-1, 1, -1), P(-1, 1, 1), P(1, 1, 1), P(1, 1, -1), nb],
    [P(-1, -1, 1), P(-1, -1, -1), P(1, -1, -1), P(1, -1, 1), neg(nb)],
    [P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1), nc],
    [P(1, -1, -1), P(-1, -1, -1), P(-1, 1, -1), P(1, 1, -1), neg(nc)],
  ];
  for (const [a, b, d, e, n] of faces) {
    tri(buf, a, b, d, n, level);
    tri(buf, a, d, e, n, level);
  }
}

/**
 * A barrel: two frusta belly to belly, so the staves bow the way a coopered cask
 * has to bow, plus its two heads. `axis` is a unit vector — up for a barrel
 * standing on its head, horizontal for one laid on its side — and `right` is any
 * unit vector across it.
 *
 * `sides` staves gives 4·sides side triangles and 2·(sides−2) head triangles;
 * at 10 that is 56 for a whole barrel, which is what lets a hundred and fifty of
 * them cost less than one building. It defaults to a cask's ten and is passed
 * down to six for a WHEEL HUB, which is the same solid at a fifth of the size
 * and does not need a cask's roundness (T-0064).
 */
function pushBarrel(buf, cx, cy, cz, axis, right, len, bellyR, headR, level,
  sides = BARREL_SIDES, headMark = null, sideMark = null) {
  const [ax, ay, az] = axis;
  const [rx, ry, rz] = right;
  // the third axis of the frame, right × axis
  const sx = ry * az - rz * ay;
  const sy = rz * ax - rx * az;
  const sz = rx * ay - ry * ax;
  const at = (t, r, k) => [
    cx + ax * t + (rx * Math.cos(k) + sx * Math.sin(k)) * r,
    cy + ay * t + (ry * Math.cos(k) + sy * Math.sin(k)) * r,
    cz + az * t + (rz * Math.cos(k) + sz * Math.sin(k)) * r,
  ];
  const half = len / 2;
  const ring = (t, r) => {
    const out = [];
    for (let i = 0; i < sides; i += 1) {
      out.push(at(t, r, (i / sides) * Math.PI * 2));
    }
    return out;
  };
  const lo = ring(-half, headR);
  const mid = ring(0, bellyR);
  const hi = ring(half, headR);
  const nOf = (p, t) => {
    const dx = p[0] - (cx + ax * t);
    const dy = p[1] - (cy + ay * t);
    const dz = p[2] - (cz + az * t);
    const L = Math.hypot(dx, dy, dz) || 1;
    return [dx / L, dy / L, dz / L];
  };
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
   * `-sin d`. `v` runs up the cask, 0 at the lower chine and 1 at the upper,
   * with the belly ring at the half — so the lettering bows out with the
   * staves, exactly as paint on a real cask does.
   */
  const step = (Math.PI * 2) / sides;
  let q0 = 0;
  if (sideMark) {
    // the stave whose own middle is nearest the direction that must face out
    q0 = Math.round(sideMark.center / step - 0.5);
  }
  const first = q0 - (BILGE_STAVES - 1) / 2;
  /** The uv of ring point `i` at height `t` (0 lower chine, 1 upper), or null. */
  const sideUV = (i, t) => {
    if (!sideMark) return null;
    // `i` counted forward from the arc's first stave, wrapped into one turn —
    // which is what lets the caller hand this `i + 1` on the last stave and get
    // the arc's own far edge rather than a jump back to its near one.
    let n2 = (i - first) % sides;
    if (n2 < 0) n2 += sides;
    if (n2 > BILGE_STAVES) return null;
    const u = 1 - n2 / BILGE_STAVES;
    return [
      sideMark.rect.u0 + u * (sideMark.rect.u1 - sideMark.rect.u0),
      sideMark.rect.v0 + t * (sideMark.rect.v1 - sideMark.rect.v0),
    ];
  };
  for (let i = 0; i < sides; i += 1) {
    const j = (i + 1) % sides;
    for (const [a, b, t0, t1] of [[lo, mid, 0, 0.5], [mid, hi, 0.5, 1]]) {
      const ai = sideUV(i, t0);
      const bi = sideUV(i, t1);
      const bj = sideUV(i + 1, t1);
      const aj = sideUV(i + 1, t0);
      const on = ai && bi && bj && aj;
      tri(buf, a[i], b[i], b[j], nOf(b[i], 0), level, on ? [ai, bi, bj] : null);
      tri(buf, a[i], b[j], a[j], nOf(a[i], 0), level, on ? [ai, bj, aj] : null);
    }
  }
  /**
   * A HEAD MARK GOES ON THE `hi` HEAD (T-0065) — for the empties laid along a
   * wall, whose bilge is turned up at the sky and whose head is the one face of
   * them a visitor reads the right way up. A standing cask is marked on its
   * BILGE instead, below. A ring point at angle k stands at `cos k` along
   * `right` and `sin k` along the frame's third axis, so the disc maps onto the
   * cell by exactly that, up to which way round the reader is.
   *
   * `rot` turns the lettering a quarter for the laid cask, and neither mapping
   * is a taste — both are `right = forward x up` worked through.
   *
   * UPRIGHT: a reader stands on the street and looks in at the head, so the
   * page's up is the frame's third axis (the inward normal, `sin k`) and its
   * rightward direction is MINUS `right` (`-cos k`), because
   * `third x y = -right`.
   *
   * LAID: the cask lies along the wall, so its head faces down the footway and
   * the reader is at the far end of it. The page's up is world up, which for a
   * laid cask IS `right` (`cos k`), and its rightward direction is the third
   * axis (`sin k`).
   *
   * Getting either sign wrong writes the mark mirrored, which is exactly what
   * the first build of this did to every case in the town.
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
  const ang = (i) => (i / sides) * Math.PI * 2;
  for (const [ringPts, sign] of [[lo, -1], [hi, 1]]) {
    const n = [ax * sign, ay * sign, az * sign];
    const marked = headMark && sign > 0;
    for (let i = 1; i < sides - 1; i += 1) {
      const uvs = marked
        ? [markUV(ang(0)), markUV(ang(i)), markUV(ang(i + 1))]
        : null;
      if (sign > 0) tri(buf, ringPts[0], ringPts[i], ringPts[i + 1], n, level, uvs);
      else tri(buf, ringPts[0], ringPts[i + 1], ringPts[i], n, level);
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
  for (let i = 0; i < WHEEL_SIDES; i += 1) {
    const k0 = (i / WHEEL_SIDES) * Math.PI * 2;
    const k1 = ((i + 1) / WHEEL_SIDES) * Math.PI * 2;
    const nOut = [rx * Math.cos((k0 + k1) / 2), Math.sin((k0 + k1) / 2),
      rz * Math.cos((k0 + k1) / 2)];
    const nIn = [-nOut[0], -nOut[1], -nOut[2]];
    // tyre
    tri(buf, at(radius, k0, -half), at(radius, k0, half), at(radius, k1, half), nOut, level);
    tri(buf, at(radius, k0, -half), at(radius, k1, half), at(radius, k1, -half), nOut, level);
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
  pushBarrel(buf, cx, cy, cz, axle, [rx, 0, rz], WHEEL_T_M * 2.2, HUB_R_M, HUB_R_M * 0.8,
    level, HUB_SIDES);
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

  if (item.kind === 'barrel') {
    const h = form.barrelHeight;
    const belly = form.barrelBelly / 2;
    const head = form.barrelHead / 2;
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
      pushBarrel(buf, x, base + belly, z, [wx, 0, wz], [0, 1, 0], h, belly, head, level,
        BARREL_SIDES, rect ? { rect, rot: 1 } : null);
    } else {
      // Upright, `right` is along the wall and the frame's third axis is the
      // INWARD normal, so the direction that has to face the street is the one
      // at three quarters of a turn: cos = 0, sin = -1, which is -third.
      const rect = item.mark && marks ? marks(item.mark, 'bilge') : null;
      pushBarrel(buf, x, base + h / 2, z, [0, 1, 0], [wx, 0, wz], h, belly, head, level,
        BARREL_SIDES, null, rect ? { rect, center: (3 * Math.PI) / 2 } : null);
    }
    return true;
  }
  if (item.kind === 'bench') {
    // A backless plank bench standing against a wall: a seat plank on two plank
    // ends. `at` is its centre and the record puts that half the seat's depth off
    // the wall plane, so the back edge touches the boards.
    const [L, D, H] = form.bench;
    const t = form.benchPlank;
    pushBox(buf, x, base + H - t / 2, z, wx, wz, L / 2, D / 2, t / 2, level);
    // the two ends, inset so the seat overhangs them the way a bench's does
    const endInset = Math.min(0.14, L / 8);
    for (const s2 of [-1, 1]) {
      pushBox(buf, x + wx * s2 * (L / 2 - endInset), base + (H - t) / 2,
        z + wz * s2 * (L / 2 - endInset), wx, wz, t / 2, (D * 0.82) / 2, (H - t) / 2,
        level);
    }
    return true;
  }
  if (item.kind === 'crate') {
    const [l, w, hh] = form.crate;
    const tier = item.tier || 0;
    const s = tier === 0 ? 1 : form.crate2Scale;
    const y = base + (tier === 0 ? hh / 2 : hh + (hh * s) / 2);
    // The shipping mark goes on the face that looks at the street, which is the
    // one `pushBox` calls face 3. A case stacked on another is the same aspect
    // — it is the same case scaled — so both tiers share the atlas cell.
    pushBox(buf, x, y, z, wx, wz, (l * s) / 2, (w * s) / 2, (hh * s) / 2, level,
      item.mark && marks ? marks(item.mark, 'case') : null);
    return true;
  }
  return false;
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

  // the body: a plank floor and four sides, so a visitor looking down into it
  // sees a wagon box and not a solid block.
  pushBox(buf, x, bed, z, fx, fz, L / 2, W / 2, 0.035, level);
  for (const s of [-1, 1]) {
    pushBox(buf, x + sx * s * (W / 2), bed + H / 2, z + sz * s * (W / 2),
      fx, fz, L / 2, 0.03, H / 2, level);
    pushBox(buf, x + fx * s * (L / 2), bed + H / 2, z + fz * s * (L / 2),
      sx, sz, W / 2, 0.03, H / 2, level);
  }
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
    buf.tint = buf.canvas;
    pushTilt(buf, x, bed + H, z, fx, fz, sx, sz, L / 2 + over, W / 2, rise, level);
    buf.tint = buf.timber;
  }
  if (wagon.yoke) pushYoke(buf, x, z, base, fx, fz, sx, sz, form, L, level);
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
  // the box: a floor and four sides, the wagon's own construction at the cart's
  // own size.
  pushBox(buf, x, bed, z, fx, fz, L / 2, W / 2, 0.035, level);
  for (const s of [-1, 1]) {
    pushBox(buf, x + sx * s * (W / 2), bed + H / 2, z + sz * s * (W / 2),
      fx, fz, L / 2, 0.03, H / 2, level);
    pushBox(buf, x + fx * s * (L / 2), bed + H / 2, z + fz * s * (L / 2),
      sx, sz, W / 2, 0.03, H / 2, level);
  }
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
    pushBarrel(buf, x, bed + 0.035 + caskR, z, [fx, 0, fz], [0, 1, 0],
      Math.min(caskL, L), caskR, (caskHead / caskBelly) * caskR, level);
  }
  if (wagon.yoke) pushYoke(buf, x, z, base, fx, fz, sx, sz, form, L, level);
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
  return false;
}

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
  };
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
    wagons: [],
    benches: [],
    sheds: [],
    census: { records: 0, frontages: 0, objects: 0, barrels: 0, crates: 0, wagons: 0,
      byKind: {}, benches: 0, sheds: 0, refused: 0, wagonsRefused: 0, chunks: 0,
      marked: 0, markCells: 0, lots: 0, piles: 0, orphaned: 0, byMaterial: {} },
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
  const atlas = markCells.size ? buildMarkAtlas(markCells) : null;
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
  const tones = {
    timber: [timber.r, timber.g, timber.b],
    canvas: [canvasTone.r, canvasTone.g, canvasTone.b],
    brick: [brickTone.r, brickTone.g, brickTone.b],
    stone: [stoneTone.r, stoneTone.g, stoneTone.b],
  };
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
        buf: { pos: [], nrm: [], conf: [], col: [], uv: [], ...tones,
          tint: tones.timber, blank: atlas ? atlas.blank : [0, 0] },
        spans: [],
      };
      chunks.set(key, chunk);
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
      const chunk = chunkAt(anchor[0], anchor[1]);
      let drew = 0;
      const from = chunk.buf.pos.length / 9;
      for (const item of lot.items ?? []) {
        if (!buildStack(chunk.buf, item, form, terrain,
          LEVEL[lot.confidence] ?? level, problems, lot.structure_id)) continue;
        drew += 1;
        out.census.piles += 1;
        out.census.objects += 1;
        out.census.byMaterial[item.kind] =
          (out.census.byMaterial[item.kind] ?? 0) + 1;
      }
      if (!drew) continue;
      chunk.spans.push({ id: lot.structure_id, from,
        to: chunk.buf.pos.length / 9 });
      out.lots.push(lot);
      out.census.lots += 1;
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
  }
  const built = [...chunks.values()].filter((c) => c.buf.pos.length);
  if (!built.length) {
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
  mat.customProgramCacheKey = () => 'chicago4d-yard-goods-timber';

  const meshes = [];
  for (const chunk of built) {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(chunk.buf.pos, 3));
    geo.setAttribute('normal', new THREE.Float32BufferAttribute(chunk.buf.nrm, 3));
    geo.setAttribute('_confidence',
      new THREE.Float32BufferAttribute(chunk.buf.conf, 1));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(chunk.buf.col, 3));
    if (atlas) geo.setAttribute('uv', new THREE.Float32BufferAttribute(chunk.buf.uv, 2));
    // The whole point of the chunk: its own bounding sphere, around its own
    // block of the town, so the frustum can leave it out.
    geo.computeBoundingSphere();
    const mesh = new THREE.Mesh(geo, mat);
    mesh.name = 'yard-chunk';
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.spans = chunk.spans;
    group.add(mesh);
    meshes.push(mesh);
  }
  out.census.chunks = meshes.length;
  group.userData.census = out.census;

  const raycaster = new THREE.Raycaster();
  /** The business these goods stand at, or null. Same ray budget as the boards. */
  out.pickAt = (ndc, camera) => {
    if (!camera) return null;
    raycaster.setFromCamera(ndc ?? new THREE.Vector2(0, 0), camera);
    raycaster.far = Math.max(400, camera.position.y * 4);
    const hits = raycaster.intersectObjects(meshes, false);
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
  };
  return out;
}
