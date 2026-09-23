/**
 * wharves.js — the river docks and the South Water landings.
 *
 * Since T-0062 the record carries more than the two warehouse docks T-0041
 * derived: the owner's 2026-08-18 ruling ("you can add more docks!") added
 * reconstructed South Water merchant landings, stated per record and drawn by
 * this same layer wherever the traced 1834 bank reaches them. Nothing below
 * changed for it — the record grew, the drawing didn't.
 *
 * WHY THIS FILE EXISTS. `docs/ROADMAP.md` K5 (e) asks for *"docks/wharves at the
 * forwarding houses"*, and ticket T-0041 is that clause. Two records in this
 * dataset state a dock and both state it in the same sentence — *"Kinzie &
 * Hunter and Dole & Newberry each had a warehouse with its dock along the river
 * front"* — and until this layer existed both carried `geometry: "absent"` over
 * it: the strongest confidence chip the project hands out, in front of a bare
 * bank. `tools/generate_river_wharves.py` answers "which frontage" with a rule
 * and derives the outline from the traced bank, the committed footprint and the
 * committed heightfield; `tools/check.sh` re-derives its record byte for byte;
 * and this file only draws what that record says.
 *
 * WHAT IT WILL AND WILL NOT DO.
 *
 *  * THE DECK'S HEIGHT IS THE TERRAIN'S, NOT THE RECORD'S. It is sampled along
 *    the landward edge at load — the bridge's lesson (T-0001), where a deck
 *    height authored beside the mesh instead of taken from it stood a walker
 *    1.8 m over the planks. Where the bank is lower than the record's freeboard
 *    floor above the water plane, the deck holds the floor instead, because a
 *    working deck stands clear of its own river.
 *  * IT STANDS ON THE BED IT IS OVER. Each crib bent is stepped down to
 *    `terrain.surfaceHeight` at its own point, so the crib meets the channel
 *    floor the heightfield draws rather than a flat guess — which is the only
 *    reason a structure standing in water can be drawn honestly at all.
 *  * IT IS A WALK SURFACE SINCE T-0058, AND IT IS THIS LAYER THAT SAYS SO.
 *    Until then `walkHeight()`'s wading barrier stood over every deck, so a
 *    visitor saw a wharf from the bank and could not step out along it. The
 *    bridges' route is closed here: `placement.walk_surface_m` lives on a
 *    sidecar and a wharf has no structure record to carry one, and inventing a
 *    record to hold a height would be a SECOND opinion about a number this file
 *    already knows. So `createWharves` publishes `decks` in `walker.js`'s own
 *    `{ id, y, pts }` shape, each at the `deck_top_m` its slab was drawn at,
 *    and `main.js` hands them to the walker beside the bridges'. One number,
 *    not two that agree until they do not — T-0001's finding, 1.8 m over the
 *    North Branch planks.
 *  * AND IT DRAWS THE WAY ON. The deck top is the ground's, floored at the
 *    record's freeboard over the water, so at every one of these seven sites
 *    the planks stand PROUD of the bank they tie into — enough of it that the
 *    walker's 0.35 m step-up rule refuses most of the landward edges, which
 *    would leave a deck you can walk along and cannot get onto. A boarding
 *    stair of plank treads is drawn at the middle of each landward edge, as
 *    many treads as the terrain's own rise there needs at the record's greatest
 *    permitted rise, and each tread is published as a walk surface with the
 *    deck. The alternative was to regrade the bank, which is a claim about the
 *    LAND and needs a bake; this invents only timber this layer already draws
 *    (docs/LIBERTIES.md).
 *  * NO VESSEL, NO CARGO, NO CRANE, NO GANGWAY, NO NAME. The record says so and
 *    this file keeps it: the schooner cheered at one of these two wharves in
 *    1834 is not drawn, because a hull would be a larger invention than the
 *    deck it lay at.
 *  * It is ONE draw call for the whole layer, like the fences, the boards and
 *    the goods.
 *  * It marks itself. Every vertex carries `_confidence` at `reconstructed`,
 *    because the SIZE of these docks is invented — the weakest thing deciding
 *    that the vertex exists at all. So the whole layer disappears when a visitor
 *    hides `reconstructed`, and the warehouses go back to standing at an empty
 *    bank. That is the truthful behaviour.
 *  * It answers a pick. A wharf belongs to the warehouse it serves, so clicking
 *    it opens that building's card — the same contract the boards and the goods
 *    keep.
 */

import * as THREE from 'three';

/** attested · inferred · reconstructed, as the confidence view reads them. */
const LEVEL = { attested: 0, documented: 0, inferred: 0.5, reconstructed: 1 };

/** The vertical datum: the summer-1835 water surface, the same zero terrain.js
 *  draws the river plane at. Imported as a literal rather than from terrain.js
 *  so this layer keeps working if it is ever mounted without one. */
const WATER_Y = 0;

/**
 * HOW THE OUTLINE BECOMES TRIANGLES, and why these numbers are not the record's.
 * The record owns everything that is a CLAIM about the town — where the deck
 * stands, how far out its face reaches, how thick the planks are, how high it
 * holds above the water. What is here is only the grain of the drawing: how many
 * bents the crib is stepped into, how many posts stand on it, how far the crib
 * is inset under the deck it carries. Same division `yard.js` makes between a
 * barrel's girth and the number of staves it is drawn with.
 */
const BENT_M = 2.5;          // the crib is stepped at this spacing, along its run
const CRIB_INSET_M = 0.10;   // the crib sits this far in under the deck's edge
const CRIB_FOOT_M = 0.35;    // and is buried this far into the bed it stands on
const POSTS = 3;             // snubbing posts along the face
const POST_INSET_M = 0.45;   // set back this far from the face's own edge
/**
 * The boarding stair's grain, as opposed to its claim. How wide it is, how deep
 * a tread goes and the most one may rise are the record's (`form`, above); what
 * is here is how far the bottom tread's ground is looked for beyond the stair's
 * own foot, and the ceiling on treads that stops a hole in the heightfield
 * building a staircase.
 */
const STAIR_FOOT_REACH_M = 1.0;  // ground is sampled this far landward of the foot
const STAIR_MAX_TREADS = 4;      // beyond this the site is reported, not stepped
const TREAD_T_M = 0.10;          // a tread is a plank, and this is its thickness

/**
 * The layer's timber tone. Deliberately NOT the goods' warm cooperage colour and
 * not the fences' weathered grey: a dock is heavy structural timber standing in
 * water, wet at the foot and silvered on the deck, so it reads darker and cooler
 * than both. As in `signage.js`: `ColorManagement.enabled` is true and `setHex`
 * reads sRGB, so this is the hex, not a linear triple copied from a generator.
 */
const WHARF_COLOUR = 0x6f6a5e;

/* -------------------------------------------------------------------------- */
/* primitives                                                                  */
/* -------------------------------------------------------------------------- */

/**
 * One box, 12 triangles, flat-shaded from its own face normals. `u` is the
 * horizontal unit vector along the box's length; up is world Y always.
 * Deliberately the same helper shape as the enclosure, signage and yard layers'
 * — four layers drawing timber the same way is one thing to reason about.
 */
function pushBox(buf, cx, cy, cz, ux, uz, halfLen, halfW, halfH, level) {
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
  for (const [t1, t2, n] of faces) {
    for (const tri of [t1, t2]) {
      for (const i of tri) {
        buf.pos.push(p[i][0], p[i][1], p[i][2]);
        buf.nrm.push(n[0], n[1], n[2]);
        buf.conf.push(level);
      }
    }
  }
}

/* -------------------------------------------------------------------------- */
/* the wharf                                                                   */
/* -------------------------------------------------------------------------- */

/** Local ENU (e, n) to the renderer's world (x, z). World is (E, up, −N). */
const wx = (e) => e;
const wz = (n) => -n;

function groundAt(terrain, e, n) {
  const y = terrain.surfaceHeight(e, n);
  return Number.isFinite(y) ? y : null;
}

/**
 * A run of crib wall, stepped into bents that each reach the bed under them.
 *
 * `a` and `b` are the run's two ends in local ENU, on the CENTRELINE of the
 * wall; the wall is `width` across and hangs from `deckY` down to the bed. A
 * bent whose bed sample is above the deck is skipped rather than drawn inside
 * out — over dry ground the deck sits on the ground and needs no crib.
 */
function pushCribRun(buf, a, b, width, deckY, terrain, level) {
  const de = b[0] - a[0];
  const dn = b[1] - a[1];
  const run = Math.hypot(de, dn);
  if (run < 0.05) return 0;
  const ue = de / run;
  const un = dn / run;
  const bents = Math.max(1, Math.round(run / BENT_M));
  const step = run / bents;
  let drawn = 0;
  for (let i = 0; i < bents; i += 1) {
    const t = (i + 0.5) * step;
    const e = a[0] + ue * t;
    const n = a[1] + un * t;
    const bed = groundAt(terrain, e, n);
    if (bed === null) continue;
    const foot = Math.min(bed - CRIB_FOOT_M, deckY - 0.25);
    const h = deckY - foot;
    if (h <= 0.05) continue;
    pushBox(buf, wx(e), foot + h / 2, wz(n), ue, -un,
      step / 2, width / 2, h / 2, level);
    drawn += 1;
  }
  return drawn;
}

/**
 * THE BOARDING STAIR, and why the number of treads is not in the record.
 *
 * The deck top is `max(the ground along the landward edge, the record's
 * freeboard over the water)`, so how far it stands proud of the bank is a
 * TERRAIN answer and differs at every site — nothing that could honestly be
 * authored beside the outline. The record therefore states only what a stair
 * IS here (its width across, its going per tread, the most any one tread may
 * rise) and this function asks the heightfield how many that comes to.
 *
 * The count is a small fixed-point search rather than one division, because the
 * ground the stair steps off is the ground at its own FOOT and the foot moves
 * landward with every tread added. So: try one tread, look at where that puts
 * the foot, and add treads until the rise there divides under the record's
 * ceiling. `STAIR_MAX_TREADS` stops a hole in the heightfield from building a
 * staircase — a site that needs more is reported and left unstepped, which is
 * visible (the deck is not boardable there) where a guess would not be.
 *
 * Returns `{ treads, rise, footY, polys }`; `polys` are the tread rectangles in
 * local ENU, bottom tread first, ready to be published as walk surfaces.
 */
function planStair(heelL, heelR, ue, un, oe, on, deckY, form, terrain) {
  const midE = (heelL[0] + heelR[0]) / 2;
  const midN = (heelL[1] + heelR[1]) / 2;
  const half = form.stairW / 2;
  // The ground the stair steps off, sampled across its foot and a metre beyond
  // it. The MINIMUM is taken, not the mean: the walker climbs from wherever it
  // is standing and the worst of those stations is the rise that has to divide.
  const footGround = (dFoot) => {
    let g = Infinity;
    for (const across of [-half, 0, half]) {
      for (const back of [dFoot, dFoot + STAIR_FOOT_REACH_M]) {
        const e = midE + ue * across - oe * back;
        const n = midN + un * across - on * back;
        const y = groundAt(terrain, e, n);
        if (y !== null) g = Math.min(g, y);
      }
    }
    return Number.isFinite(g) ? g : null;
  };

  let treads = null;
  let footY = null;
  for (let n = 1; n <= STAIR_MAX_TREADS + 1; n += 1) {
    const g = footGround((n - 1) * form.stairTread);
    if (g === null) return null;
    if (deckY - g <= n * form.stairRise + 1e-9) { treads = n - 1; footY = g; break; }
  }
  if (treads === null) return null;

  const rise = (deckY - footY) / (treads + 1);
  const polys = [];
  for (let k = 1; k <= treads; k += 1) {
    // Tread k counts UP from the foot, so k = treads is the one against the
    // deck and sits in the first going landward of the heel.
    const far = (treads + 1 - k) * form.stairTread;
    const near = far - form.stairTread;
    const dm = (far + near) / 2;
    const ce = midE - oe * dm;
    const cn = midN - on * dm;
    const corner = (a, b) => [
      ce + ue * half * a + oe * (form.stairTread / 2) * b,
      cn + un * half * a + on * (form.stairTread / 2) * b,
    ];
    polys.push({
      y: footY + rise * k,
      centre: [ce, cn],
      pts: [corner(-1, -1), corner(1, -1), corner(1, 1), corner(-1, 1)],
    });
  }
  return { treads, rise, footY, polys };
}

/**
 * One wharf: the deck slab, the crib under its face and its two ends, and the
 * snubbing posts. Returns the number of vertices it emitted, or 0 if the record
 * could not be stood anywhere — which is always a recorded problem and never a
 * silently invented dock.
 */
function buildWharf(buf, w, form, terrain, level, problems) {
  const quad = w.deck_quad_local_enu_m;
  if (!Array.isArray(quad) || quad.length !== 4) {
    problems.push(`wharves: ${w.structure_id} has no deck outline — nothing is drawn`);
    return 0;
  }
  const [heelL, heelR, faceR, faceL] = quad;
  // The deck's own axes, taken from the outline rather than from the record's
  // tangent: if the two ever disagreed the outline is what a visitor sees.
  const alongE = heelR[0] - heelL[0];
  const alongN = heelR[1] - heelL[1];
  const length = Math.hypot(alongE, alongN);
  const ue = alongE / (length || 1);
  const un = alongN / (length || 1);
  const outE = faceL[0] - heelL[0];
  const outN = faceL[1] - heelL[1];
  const width = Math.hypot(outE, outN);
  if (!(length > 0.5 && width > 0.5)) {
    problems.push(`wharves: ${w.structure_id}'s deck outline is degenerate — nothing is drawn`);
    return 0;
  }
  const oe = outE / width;
  const on = outN / width;

  // THE DECK TOP IS THE GROUND'S. Sampled at both heel corners and at the middle
  // of the landward edge, so a deck tying into a bank that falls away along its
  // length still meets the highest ground it touches rather than floating over
  // the rest of it. Never below the record's freeboard floor over the water.
  const heelMid = [(heelL[0] + heelR[0]) / 2, (heelL[1] + heelR[1]) / 2];
  const samples = [heelL, heelMid, heelR]
    .map((p) => groundAt(terrain, p[0], p[1]))
    .filter((y) => y !== null);
  if (!samples.length) {
    problems.push(`wharves: ${w.structure_id} has no ground under its landward edge `
      + '— no wharf is drawn');
    return 0;
  }
  const deckY = Math.max(...samples, WATER_Y + form.freeboard);
  const before = buf.pos.length;

  // the deck: one slab, centred on the outline
  const cx = (heelL[0] + heelR[0] + faceL[0] + faceR[0]) / 4;
  const cn = (heelL[1] + heelR[1] + faceL[1] + faceR[1]) / 4;
  pushBox(buf, wx(cx), deckY - form.deckT / 2, wz(cn), ue, -un,
    length / 2, width / 2, form.deckT / 2, level);

  // the crib: under the outer face and under both ends, inset so the deck
  // oversails it the way a planked deck oversails the timber carrying it.
  const inset = (p, de, dn) => [p[0] + de, p[1] + dn];
  const halfCrib = form.cribW / 2 + CRIB_INSET_M;
  const faceCentreL = inset(faceL, -oe * halfCrib, -on * halfCrib);
  const faceCentreR = inset(faceR, -oe * halfCrib, -on * halfCrib);
  const cribDeck = deckY - form.deckT;
  let bents = pushCribRun(buf, faceCentreL, faceCentreR, form.cribW,
    cribDeck, terrain, level);
  bents += pushCribRun(buf,
    inset(heelL, ue * halfCrib + oe * halfCrib, un * halfCrib + on * halfCrib),
    inset(faceCentreL, ue * halfCrib, un * halfCrib),
    form.cribW, cribDeck, terrain, level);
  bents += pushCribRun(buf,
    inset(heelR, -ue * halfCrib + oe * halfCrib, -un * halfCrib + on * halfCrib),
    inset(faceCentreR, -ue * halfCrib, -un * halfCrib),
    form.cribW, cribDeck, terrain, level);
  if (!bents) {
    problems.push(`wharves: ${w.structure_id}'s deck stands on no crib — the bed `
      + 'under it could not be sampled');
  }

  // the snubbing posts, along the face
  for (let i = 0; i < POSTS; i += 1) {
    const t = ((i + 1) / (POSTS + 1) - 0.5) * (length - 2 * POST_INSET_M);
    const e = cx + ue * t + oe * (width / 2 - POST_INSET_M);
    const n = cn + un * t + on * (width / 2 - POST_INSET_M);
    pushBox(buf, wx(e), deckY + form.postH / 2, wz(n), ue, -un,
      form.postSide / 2, form.postSide / 2, form.postH / 2, level);
  }

  // THE WAY ON. Drawn last because it is the only part of a wharf whose size is
  // decided by the ground rather than by the record, and because a site the
  // heightfield cannot answer for has to leave the rest of the dock standing.
  const stair = planStair(heelL, heelR, ue, un, oe, on, deckY, form, terrain);
  if (!stair) {
    problems.push(`wharves: ${w.structure_id}'s landward edge has no ground to `
      + 'stand a boarding stair on — the deck is drawn and cannot be boarded');
  }
  for (const t of stair?.polys ?? []) {
    let under = groundAt(terrain, t.centre[0], t.centre[1]);
    if (under === null) under = t.y - TREAD_T_M;
    const foot = Math.min(under, t.y - TREAD_T_M) - 0.05;
    const h = t.y - foot;
    pushBox(buf, wx(t.centre[0]), foot + h / 2, wz(t.centre[1]), ue, -un,
      form.stairW / 2, form.stairTread / 2, h / 2, level);
  }

  w._drawn = {
    deck_top_m: deckY,
    from_terrain: deckY > WATER_Y + form.freeboard + 1e-6,
    bents,
    // The stair as built here, so the gate can ask the geometry rather than
    // re-deriving it: how many treads the ground needed, what each one rises,
    // and the height the bottom of it steps off.
    stair_treads: stair?.treads ?? null,
    stair_rise_m: stair?.rise ?? null,
    stair_foot_m: stair?.footY ?? null,
    vertices: (buf.pos.length - before) / 3,
  };
  w._decks = [
    { id: `${w.structure_id}__wharf`, y: deckY, pts: quad },
    ...(stair?.polys ?? []).map((t, i) => ({
      id: `${w.structure_id}__wharf_step${i + 1}`, y: t.y, pts: t.pts,
    })),
  ];
  return (buf.pos.length - before) / 3;
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
function readForm(record) {
  const f = record?.form ?? {};
  const v = (k, fallback) => (f[k]?.value ?? fallback);
  return {
    deckT: v('deck_thickness_m', 0.14),
    freeboard: v('freeboard_m', 0.9),
    cribW: v('crib_width_m', 1.2),
    postSide: v('post_side_m', 0.22),
    postH: v('post_height_m', 0.75),
    stairW: v('boarding_stair_width_m', 2.4),
    stairTread: v('boarding_stair_tread_m', 0.75),
    stairRise: v('boarding_stair_rise_m', 0.30),
  };
}

/**
 * @param {object} o dataBase (data/ root) · terrain · confidence · problems
 * @returns {Promise<{group: THREE.Group, records: object[], wharves: object[],
 *                    census: object, pickAt: function, dispose: function}>}
 */
export async function createWharves({
  dataBase, terrain, confidence = null, problems = [],
} = {}) {
  const group = new THREE.Group();
  group.name = 'wharves';
  const out = {
    group,
    records: [],
    wharves: [],
    /**
     * The decks as planting keep-outs, in `footprintsFrom()`'s own shape.
     * `flora.js` and `trees.js` refuse to plant inside a footprint plus a metre,
     * and a deck is a floor: a prairie dock growing up through the planks reads
     * as a hole in the model rather than as a wharf. Handed to the planters
     * ALONGSIDE the buildings' footprints and never merged into them — the
     * walker and the picker resolve a footprint by structure id, and a second
     * polygon under the same id would answer for the building.
     */
    keepOut: [],
    /**
     * The same planks as WALK SURFACES, in `decksFrom()`'s own `{ id, y, pts }`
     * shape, for `walker.js` (T-0058) — the deck slab and every tread of its
     * boarding stair.
     *
     * It is the LAYER that publishes them and not the record, deliberately. A
     * wharf carries no structure record, so there is no sidecar to hold the
     * bridges' `placement.walk_surface_m`; and the height is `deck_top_m`, the
     * identical number `buildWharf` just drew the slab at, so the plank a boot
     * is on and the plank the mesh draws are one value rather than two that
     * agree until they do not.
     *
     * Kept apart from `keepOut`, which the planters hold. They are the same
     * rectangles for the deck today and answers to different questions: a floor
     * nothing may grow through, and a floor a visitor stands on.
     */
    decks: [],
    census: {
      records: 0, wharves: 0, bents: 0, refused: 0, stairs: 0, treads: 0,
    },
    pickAt: () => null,
    dispose: () => {},
  };

  if (!dataBase || !terrain) {
    problems.push('wharves: no data base or no terrain — no dock is drawn');
    return out;
  }
  let index;
  try {
    index = await getJSON(new URL('wharves/index.json', dataBase));
  } catch (err) {
    // Degrade to NOTHING drawn plus a recorded problem, never to an invented
    // dock: the same contract the enclosure, signage, yard and vegetation
    // layers keep.
    problems.push(`wharves: ${err.message} — no dock is drawn`);
    return out;
  }
  const wanted = Array.isArray(index.wharves) ? index.wharves : [];
  const loaded = await Promise.all(wanted.map(async (w) => {
    if (!w.file) return [w.id, null, 'the manifest gave no file'];
    try {
      return [w.id, await getJSON(new URL(`wharves/${w.file}`, dataBase)), null];
    } catch (err) { return [w.id, null, err.message]; }
  }));

  const buf = { pos: [], nrm: [], conf: [] };
  /**
   * WHICH WAREHOUSE A TRIANGLE BELONGS TO. The layer is one draw call, so a hit
   * on the mesh knows nothing about which wharf it landed on unless each banks
   * the half-open range of triangles it emitted — the same span table
   * `signage.js` and `yard.js` keep, and for the same reason.
   */
  const spans = [];
  for (const [id, record, why] of loaded) {
    if (!record) { problems.push(`wharves: ${id} — ${why}`); continue; }
    out.records.push(record);
    out.census.records += 1;
    out.census.refused += (record.refused ?? []).length;
    const form = readForm(record);
    const level = LEVEL[record.existence?.confidence] ?? 1;
    for (const w of record.wharves ?? []) {
      const from = buf.pos.length / 9;
      if (!buildWharf(buf, w, form, terrain, LEVEL[w.confidence] ?? level, problems)) {
        continue;
      }
      spans.push({ id: w.structure_id, from, to: buf.pos.length / 9 });
      out.keepOut.push({ id: `${w.structure_id}__wharf`, pts: w.deck_quad_local_enu_m });
      // Every plank this wharf laid — the deck and its treads — as a floor the
      // walker stands on. The treads are keep-outs too: a stair is as much a
      // floor as the deck it climbs to, and a forb growing between the boards
      // reads as a hole in the model (T-0085/T-0124's finding, on new timber).
      for (const d of w._decks ?? []) {
        out.decks.push(d);
        if (d.id.endsWith('__wharf')) continue;
        out.keepOut.push({ id: d.id, pts: d.pts });
        out.census.treads += 1;
      }
      if ((w._drawn?.stair_treads ?? 0) > 0) out.census.stairs += 1;
      out.wharves.push(w);
      out.census.wharves += 1;
      out.census.bents += w._drawn?.bents ?? 0;
    }
  }
  if (!buf.pos.length) {
    if (out.census.records) {
      problems.push('wharves: the record loaded and not one dock was drawn');
    }
    return out;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(buf.pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(buf.nrm, 3));
  geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(buf.conf, 1));
  geo.computeBoundingSphere();

  const mat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(WHARF_COLOUR), roughness: 0.92, metalness: 0.0,
  });
  mat.name = 'wharf-timber';
  confidence?.patch(mat);
  /**
   * ITS OWN PROGRAM CACHE KEY, AND WHY THIS LINE IS NOT OPTIONAL. three caches a
   * compiled program under a key ending in `material.customProgramCacheKey()`,
   * whose default is the SOURCE TEXT of `onBeforeCompile` — so every material
   * `confidence.patch()` touches reports the same key, and two patched materials
   * that agree on their other program parameters share one program. The
   * enclosure layer was drawn in solid black by a building's shader that way,
   * with no page error and no warning; ticket T-0053 is the general fix.
   */
  mat.customProgramCacheKey = () => 'chicago4d-wharf-timber';

  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = 'wharves';
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);
  group.userData.census = out.census;

  const raycaster = new THREE.Raycaster();
  /** The warehouse this dock belongs to, or null. Same ray budget as the boards. */
  out.pickAt = (ndc, camera) => {
    if (!camera) return null;
    raycaster.setFromCamera(ndc ?? new THREE.Vector2(0, 0), camera);
    raycaster.far = Math.max(400, camera.position.y * 4);
    const hits = raycaster.intersectObject(mesh, false);
    if (!hits.length) return null;
    const hit = hits[0];
    const span = spans.find((sp) => hit.faceIndex >= sp.from && hit.faceIndex < sp.to);
    if (!span) return null;
    return { id: span.id, point: hit.point.clone(), distance: hit.distance };
  };

  out.dispose = () => { geo.dispose(); mat.dispose(); };
  return out;
}
