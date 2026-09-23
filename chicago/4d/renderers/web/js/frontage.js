/**
 * frontage.js — the plank walks, the board crossings, the hitching posts and the
 * named boards on posts that stand between a building and the street it fronts
 * on. Written for the Green Tree Tavern (T-0082) and made a town layer by the
 * Sauganash Hotel (T-0090), which brought the second record and the first post
 * with nothing hanging on it. T-0119 brought the first record that is not a
 * building's frontage at all — the river plank walk, which rides a committed
 * bridge deck at the slough mouth (`deck_m`), runs on polyline centrelines in
 * culling-sized chunks, registers its over-water planks with the walker
 * (`walkableDecks`), and answers a pick with its own card.
 *
 * T-0069 MADE IT THE STREET'S EDGE. The owner, of the first Cook County jail
 * engraving: *"note the fences lining the street and what appears to be plank
 * sidewalks. all of the streets should be updated like this... at least south of
 * the river or near the river."* The record that answers it
 * (`data/frontage/town_street_edge.json`) is a town's worth of the same two
 * things this file already drew, laid on the platted block faces rather than on
 * a wall, and it brings three additions — all of them additive, and the two
 * inns' and the river walk's geometry comes out byte for byte unchanged:
 *
 *  * **`chunk`.** A walk, a crossing and a fence that carry the same `chunk` id
 *    build ONE mesh with one bounding sphere. That is culling AND draw calls at
 *    once: a block face's sidewalk, the crossing at its corner and the fence
 *    behind it are one street edge and one draw call, so a town's worth of them
 *    costs meshes by the block face rather than by the object.
 *  * **`stringer_pitch_m`.** The stringers under a walk used to be two boxes
 *    under EVERY board — three quarters of a walk's triangles for the strip of
 *    shadow under its edge. A record may now lay them in BAYS instead, and the
 *    generator only sets it where it has audited the ground flat enough for a
 *    bay-length stringer to meet it (see `tools/generate_frontage_works.py`).
 *  * **`fences`.** A board fence at the frontage line, with the walk at its
 *    foot, which is what the jail engraving shows. It is drawn HERE and not by
 *    `enclosures.js` for two reasons that are the same reason: an enclosure
 *    takes a closed PERIMETER and encloses ground that gets its own treatment
 *    (`yards.js`), and a street-lining run is an open line that encloses
 *    nothing — it is the street edge, which is this layer's whole subject. And
 *    sharing the walk's chunk is what keeps the pair inside the draw-call
 *    budget the scene actually has.
 *
 * WHY THIS IS A LAYER AND NOT MORE YARD GOODS. A barrel or a wagon stands on a
 * building's own ground and is derived from its walls alone, which is what
 * `yard.js` draws. A walk and a crossing stand in the STREET, and the number
 * that decides where they may lie belongs to the street — the travelled track's
 * own half-width out of `data/streets/1835.json`. This is the first thing in
 * the project derived from a building and a street at once.
 *
 * WHAT IT WILL AND WILL NOT DO.
 *
 *  * Every board sits on the TERRAIN, sampled under its own centre, exactly as
 *    a barrel does. A walk laid on one height would float at one end of a
 *    frontage and be buried at the other, and this ground is not flat.
 *  * It draws LETTERING, and it is the only thing in this renderer that does.
 *    `docs/LIBERTIES.md` L25 leaves the town's one documented board blank
 *    because nobody described the painting on it; this board's subject is a
 *    NAME that the reference view states in as many words, so the wording is
 *    the plate's and only the letterform is invented (L135). The record carries
 *    the text and the argument; this file only draws what the record says, and
 *    a record with no `text` gets a blank board.
 *  * The timber is ONE draw call for the whole layer, the way the fences and
 *    the signboards are. The lettering is a second, because a painted name is a
 *    texture and timber is not — and it exists only when a board carries text.
 *  * It marks itself. Every vertex carries `_confidence`, so the whole layer
 *    disappears when a visitor hides `reconstructed` and the frontage goes back
 *    to bare ground. That is the truthful behaviour: no source record in this
 *    repository states that a walk stood here on 1 July 1835.
 *  * It answers a pick. A walk, a crossing and a post all belong to the building
 *    they were derived from, so aiming at any of them opens that building's card
 *    — which is what a sign is FOR.
 *  * A post carries a board only where the building's own reference views show
 *    one. The Sauganash's posts are hitching posts: chest-high timber under a
 *    capped head, no arm, no board and nothing lettered, because none of its
 *    three views shows a name board at this hotel (its record's
 *    `board_on_a_post` block states that reading rather than leaving it silent).
 */

import * as THREE from 'three';

/** attested · inferred · reconstructed, as the confidence view reads them. */
const LEVEL = { attested: 0, documented: 0, inferred: 0.5, reconstructed: 1 };

/**
 * The two tones this layer needs, and why they are converted rather than picked.
 * `THREE.Color.setHex` reads sRGB with `ColorManagement.enabled` on, so these are
 * the sRGB hexes that land on the weathered-board linear triples the signage
 * layer and the yard already use — copying a glTF `baseColorFactor` straight
 * across would draw this walk two stops darker than the boards beside it.
 */
const TIMBER = 0xcbc2b1;        // sawn board, weathered — the signboard's own tone
const PAINT = '#2f2013';        // the letterform's paint: L135 claims the colour

/** How far a plank's box reaches below the deck: enough to meet the ground. */
const SKIRT_M = 0.02;
/** Daylight between two boards — a plank walk is not a slab. */
const PLANK_GAP_M = 0.02;
/** A crossing is subdivided this often ALONG its run so it follows the ground. */
const CROSSING_STEP_M = 0.9;
/** How far a fence board's stock reaches across the line it stands on. */
const FENCE_BOARD_T_M = 0.022;
/** A fence rail's section — the same sawn stuff `enclosures.js` hangs. */
const FENCE_RAIL_W_M = 0.09;
const FENCE_RAIL_H_M = 0.13;
/** A drop this steep between two fence posts is a bank, not a street line. */
const FENCE_MAX_STEP_M = 1.0;
/** The longest piece of walk deck handed to the planting block-list at once. */
const KEEPOUT_PIECE_M = 12;
/**
 * THE STRING PIECE (T-0460), and the stock it is cut from.
 *
 * A plank walk laid as boards alone ends, at each side, in a row of board ENDS:
 * at a 0.32 m pitch with a 0.02 m gap between them and a deck standing 0.11 m
 * over the road, the outer edge of the walk was ten thousand short end-grain
 * faces with daylight between them, each casting its own shadow onto the dirt.
 * That is the jagged sawtooth the owner reported, and it is why the walk read as
 * a row of loose boards rather than as a made footway.
 *
 * A plank sidewalk is not laid that way. Its boards are held between two string
 * pieces — the edge timbers that run ALONG the walk, take the board ends and
 * make the face a passer-by actually sees. So this layer lays them: one down
 * each side, its top flush with the boards it holds, its foot reaching the
 * lowest ground under its own length. The boards stop at its inner face, so the
 * walk's overall width does not move.
 *
 * The stock is 0.09 m, which is the section the bay stringers were already cut
 * from — this timber IS those stringers, moved out to the walk's own edge and
 * brought up flush with the deck instead of stopping under it, so the layer
 * gains a made edge without gaining a box.
 */
const KERB_STOCK_M = 0.09;

/**
 * One box, 12 triangles, flat-shaded from its own face normals. `u` is the
 * horizontal unit vector along the box's length; up is world Y always.
 * Deliberately the same helper shape as `signage.js` and `enclosures.js` — three
 * layers drawing small timber the same way is one thing to reason about.
 */
function pushBox(buf, cx, cy, cz, ux, uz, halfLen, halfW, halfH, level,
                 skipUnderside = false) {
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
  // `skipUnderside` drops the last pair, which is the buried face of a fence
  // board standing in the ground — the same two triangles `enclosures.js`
  // drops off a pale, for the same reason: at a town's worth of boards it is
  // thousands of triangles nobody can ever see.
  for (const [t1, t2, n] of (skipUnderside ? faces.slice(0, 5) : faces)) {
    for (const tri of [t1, t2]) {
      for (const i of tri) {
        buf.pos.push(p[i][0], p[i][1], p[i][2]);
        buf.nrm.push(n[0], n[1], n[2]);
        buf.conf.push(level);
      }
    }
  }
}

/** The ground under a point, or null where the heightfield has nothing to say. */
function groundAt(terrain, e, n) {
  const y = terrain.surfaceHeight(e, n);
  return Number.isFinite(y) ? y : null;
}

/**
 * One straight run of boards laid ACROSS the way a foot travels, pushed into
 * `buf`, held between two string pieces that run ALONG it and take the board
 * ends (T-0460 — see `KERB_STOCK_M`). Each string piece's top is flush with the
 * boards it holds and its foot reaches the lowest ground under its own length,
 * so the walk presents ONE made face to the road at every point of its length
 * rather than a comb of board ends standing over it.
 *
 * WHERE A BOARD'S TOP COMES FROM, and it moved with this ticket. A board used to
 * sample the terrain under its own centre, which put a fresh height on the deck
 * every 0.32 m; a walk laid in stringer bays does not do that, because the bay
 * is what carries the boards and the bay is one piece of timber. So on a record
 * that states a bay, every board in a bay takes THAT BAY's height — the ground
 * under the bay's own centre plus the walk's rise — which is what makes the top
 * of the string piece and the top of the boards it holds the same line to the
 * millimetre. What is left of the old jitter is one butted joint per bay, and
 * the generator has already audited the ground under a bay flat to
 * `EDGE_STRINGER_ROLL_M` (0.04 m). A record with no bay keeps sampling per
 * board, and its string piece is cut to the same pitch and butted end to end.
 *
 * `deckY` (T-0119) is the committed deck a walk may RIDE — the Slough Log
 * Bridge's own `walk_surface_m`, carried onto the record as `deck_m`. Where the
 * deck stands above the ground (over the carved channel), the boards take the
 * deck and the string piece is cut to the board's own thickness with no foot,
 * because boards on a deck lie on the deck and nothing has to reach the mud;
 * where the ground stands higher (the graded approaches), the ground wins,
 * exactly as the walker's own surface rule decides it.
 *
 * `stats` accumulates the two numbers the edge rule is reported on (T-0460):
 * how many string pieces were laid, and the largest step between two
 * consecutive ones — which is the whole of what is left of the sawtooth. That a
 * board is flush with the piece holding it is not reported, because on this
 * code path it is true by construction; the gate proves the edge GEOMETRICALLY
 * instead, by walking the outer edge line of a named walk in the loaded page
 * and asking for timber from the deck down to the ground at every station.
 */
function laySegment(buf, walk, ax, ay, bx, by, terrain, level, stats = null) {
  const az = -ay;
  const bz = -by;                 // local ENU (E, N) to the renderer's (E, up, -N)
  const dx = bx - ax;
  const dz = bz - az;
  const len = Math.hypot(dx, dz);
  if (len < 0.5) return 0;
  const rx = dx / len;
  const rz = dz / len;            // along the run
  const wx = -rz;
  const wz = rx;                  // across it
  const halfW = (walk.width_m ?? 1.83) / 2;
  const rise = walk.rise_m ?? 0.11;
  const thick = walk.plank_thickness_m ?? 0.055;
  const pitch = walk.plank_pitch_m ?? 0.26;
  const deckY = Number.isFinite(walk.deck_m) ? walk.deck_m : null;
  // The string piece takes the outermost 0.09 m of the walk's own width on each
  // side and the boards stop at its inner face, so the walk stays 1.83 m wide
  // and no two faces are coincident.
  const stock = Math.min(KERB_STOCK_M, halfW / 3);
  const boardHalf = halfW - stock;
  const kerbAt = halfW - stock / 2;
  // THE STRINGER BAY (T-0069). Without `stringer_pitch_m` the string pieces are
  // cut to the board pitch and butted, which is what this layer has done since
  // T-0082 and is exactly right for a walk a few metres long on ground that
  // tilts. A record that states a bay cuts them at that pitch instead — one
  // piece of timber carrying several boards — and the generator sets it only
  // where it has audited the ground flat enough across a bay for the piece to
  // still reach it.
  const bay = Number.isFinite(walk.stringer_pitch_m) && walk.stringer_pitch_m > pitch
    ? walk.stringer_pitch_m : null;
  // A record may say its boards carry no underside (T-0069). Two triangles a
  // board, facing the earth they are laid on, on a town's worth of them.
  const bare = walk.plank_underside === false;
  const n = Math.max(1, Math.round(len / pitch));
  const step = len / n;

  /** The lowest ground under one length of string piece: its ends and middle. */
  const footUnder = (cx, cz, ox, oz, halfLen) => {
    let low = null;
    for (const d of [-halfLen, 0, halfLen]) {
      const gs = groundAt(terrain, cx + ox + rx * d, -(cz + oz + rz * d));
      if (gs !== null && (low === null || gs < low)) low = gs;
    }
    return low;
  };

  /**
   * One length of string piece down each side: top flush with `top`, foot at the
   * lowest ground under its own line (or cut to the board thickness where the
   * boards ride a committed deck and there is no mud to reach).
   */
  const layKerb = (cx, cz, halfLen, top, onDeck) => {
    for (const s of [-1, 1]) {
      const ox = wx * s * kerbAt;
      const oz = wz * s * kerbAt;
      const low = onDeck ? null : footUnder(cx, cz, ox, oz, halfLen);
      const depth = low === null ? thick : Math.max(thick, top - low + SKIRT_M);
      pushBox(buf, cx + ox, top - depth / 2, cz + oz, rx, rz,
        halfLen, stock / 2, depth / 2, level, true);
      if (stats) stats.kerb += 1;
    }
  };

  // THE BAY LINE. On a record that states a bay, the height of every board in a
  // bay is the bay's own, so the boards and the string piece holding them are
  // one line. A bay whose centre finds no ground leaves its boards to fall back
  // on their own sample, the same way they always did.
  const bays = bay === null ? 0 : Math.max(1, Math.round(len / bay));
  const bstep = bays ? len / bays : 0;
  const bayTop = [];
  for (let i = 0; i < bays; i += 1) {
    const t = (i + 0.5) * bstep;
    const g = groundAt(terrain, ax + rx * t, -(az + rz * t));
    bayTop.push(g === null ? null : g + rise);
  }
  if (stats) {
    for (let i = 1; i < bayTop.length; i += 1) {
      if (bayTop[i] === null || bayTop[i - 1] === null) continue;
      stats.kerbStep = Math.max(stats.kerbStep, Math.abs(bayTop[i] - bayTop[i - 1]));
    }
  }

  let drawn = 0;
  for (let i = 0; i < n; i += 1) {
    const t = (i + 0.5) * step;
    const cx = ax + rx * t;
    const cz = az + rz * t;
    const g = groundAt(terrain, cx, -cz);
    if (g === null && deckY === null) continue;
    const onDeck = deckY !== null && (g === null || deckY > g);
    const bi = bays ? Math.min(bays - 1, Math.max(0, Math.floor(t / bstep))) : -1;
    const held = !onDeck && bi >= 0 && bayTop[bi] !== null ? bayTop[bi] : null;
    const top = held !== null ? held : (onDeck ? deckY : g) + rise;
    // The board itself, its long axis ACROSS the run, stopping at the inner
    // face of the string piece that holds its ends.
    pushBox(buf, cx, top - thick / 2, cz, wx, wz,
      boardHalf, Math.max(0.02, (step - PLANK_GAP_M) / 2), thick / 2, level, bare);
    // A board whose bay carries it is held by that bay's string piece, laid
    // once below; every other board carries its own, cut to the board pitch and
    // butted against its neighbours so the face stays unbroken.
    if (held === null) layKerb(cx, cz, step / 2, top, onDeck);
    drawn += 1;
  }
  // The bay-laid string pieces, marched on their own pitch. Each one is a box,
  // so its underside is FLAT: it takes the LOWEST ground under its own line —
  // its two ends and its middle — so the timber reaches the land everywhere
  // along the bay rather than leaving the downhill half of it open to daylight.
  if (bays && deckY === null) {
    for (let i = 0; i < bays; i += 1) {
      if (bayTop[i] === null) continue;
      const t = (i + 0.5) * bstep;
      layKerb(ax + rx * t, az + rz * t, bstep / 2, bayTop[i], false);
    }
  }
  return drawn;
}

/**
 * A plank walk: one straight run for a two-point centreline, or a connected
 * chain of them for a polyline (T-0119 — the river walk is the first record to
 * carry one; a 400 m run pinned as a list of two-point records would be nine
 * ids for one claim).
 */
function buildWalk(buf, walk, terrain, level, problems, stats = null) {
  const line = walk.centreline_local_enu_m;
  if (!Array.isArray(line) || line.length < 2) {
    problems.push(`frontage: ${walk.id} carries no centreline — nothing is laid`);
    return false;
  }
  let drawn = 0;
  for (let i = 0; i + 1 < line.length; i += 1) {
    drawn += laySegment(buf, walk, line[i][0], line[i][1],
      line[i + 1][0], line[i + 1][1], terrain, level, stats);
  }
  if (!drawn) {
    problems.push(`frontage: ${walk.id} found no ground under any board — nothing is laid`);
    return false;
  }
  return true;
}

/**
 * A crossing: boards laid ALONG the way a foot travels, which is what a crossing
 * is FOR — it spans the ruts instead of lying in them. Subdivided along the run
 * so that a board fifteen metres long still follows the camber of the road it
 * crosses.
 */
function buildCrossing(buf, walk, terrain, level, problems) {
  const line = walk.centreline_local_enu_m;
  if (!Array.isArray(line) || line.length < 2) {
    problems.push(`frontage: ${walk.id} carries no centreline — nothing is laid`);
    return false;
  }
  const [a, b] = line;
  const ax = a[0];
  const az = -a[1];
  const dx = b[0] - ax;
  const dz = -b[1] - az;
  const len = Math.hypot(dx, dz);
  if (len < 0.5) {
    problems.push(`frontage: ${walk.id} is ${len.toFixed(2)} m long — nothing is laid`);
    return false;
  }
  const rx = dx / len;
  const rz = dz / len;
  const wx = -rz;
  const wz = rx;
  const width = walk.width_m ?? 1.22;
  const boards = Math.max(1, walk.plank_count ?? 4);
  const bw = width / boards;
  const rise = walk.rise_m ?? 0.06;
  const thick = walk.plank_thickness_m ?? 0.055;
  // How often the crossing is cut along its run so it follows the camber. The
  // default is a board's own length; a record laid on ground its generator has
  // audited flat may state a longer one, which is the same trade the walk's
  // stringer bay makes and for the same reason (T-0069).
  const stride = Number.isFinite(walk.plank_step_m) && walk.plank_step_m > CROSSING_STEP_M
    ? walk.plank_step_m : CROSSING_STEP_M;
  const segs = Math.max(1, Math.round(len / stride));
  const step = len / segs;
  let drawn = 0;
  for (let i = 0; i < segs; i += 1) {
    const t = (i + 0.5) * step;
    const cx = ax + rx * t;
    const cz = az + rz * t;
    const g = groundAt(terrain, cx, -cz);
    if (g === null) continue;
    const top = g + rise;
    for (let j = 0; j < boards; j += 1) {
      const off = (j + 0.5) * bw - width / 2;
      pushBox(buf, cx + wx * off, top - thick / 2, cz + wz * off, rx, rz,
        step / 2, Math.max(0.02, (bw - PLANK_GAP_M) / 2), thick / 2, level,
        walk.plank_underside === false);
    }
    drawn += 1;
  }
  if (!drawn) {
    problems.push(`frontage: ${walk.id} found no ground under any board — nothing is laid`);
    return false;
  }
  return true;
}

/**
 * A FENCE LINING THE STREET (T-0069): posts on the frontage line, two stringers
 * between them and boards butted across, which is the fence the first Cook County
 * jail engraving puts at the lot line with a plank walk at its foot.
 *
 * Construction, dimensions and refusals are deliberately the same as
 * `enclosures.js` draws a `board` fence with — the same posts, the same courses
 * inside the height, the same butted stock, the same refusal of a post whose
 * foot is in the water and of a bay that drops like a bank. What is NOT the same
 * is which layer owns it, and the header says why: an enclosure is a closed
 * perimeter whose interior gets a ground treatment, and this is an open line at
 * the street's edge that encloses nothing. It shares its walk's chunk, so a
 * block face's whole street edge is one mesh.
 */
function buildFence(buf, fence, terrain, level, problems) {
  const path = fence.path_local_enu_m;
  if (!Array.isArray(path) || path.length < 2) {
    problems.push(`frontage: ${fence.id} carries no line — no fence is set`);
    return false;
  }
  const height = fence.height_m ?? 1.37;
  const courses = Math.max(1, Math.round(fence.rail_courses ?? 2));
  const spacing = Math.max(1, fence.post_spacing_m ?? 2.44);
  const postHalf = (fence.post_square_m ?? 0.12) / 2;
  const boardW = Math.max(0.05, fence.board_width_m ?? 0.254);
  const boardPitch = boardW + Math.max(0, fence.board_gap_m ?? 0.006);
  let posts = 0;
  for (let seg = 0; seg + 1 < path.length; seg += 1) {
    const a = path[seg];
    const b = path[seg + 1];
    const de = b[0] - a[0];
    const dn = b[1] - a[1];
    const len = Math.hypot(de, dn);
    if (len < 0.5) continue;
    const bays = Math.max(1, Math.round(len / spacing));
    const ux = de / len;
    const uz = -dn / len;            // local ENU to the renderer's (E, up, -N)
    const feet = [];
    for (let i = 0; i <= bays; i += 1) {
      const e = a[0] + de * (i / bays);
      const n = a[1] + dn * (i / bays);
      const y = terrain.isWater?.(e, n) ? null : groundAt(terrain, e, n);
      feet.push(y === null ? null : { e, n, y });
    }
    for (let i = 0; i <= bays; i += 1) {
      const f = feet[i];
      if (!f) continue;
      pushBox(buf, f.e, f.y + height / 2, -f.n, ux, uz,
        postHalf, postHalf, height / 2, level, true);
      posts += 1;
    }
    for (let i = 0; i < bays; i += 1) {
      const p = feet[i];
      const q = feet[i + 1];
      if (!p || !q || Math.abs(p.y - q.y) > FENCE_MAX_STEP_M) continue;
      const bayLen = Math.hypot(q.e - p.e, q.n - p.n);
      if (bayLen < 0.05) continue;
      for (let c = 1; c <= courses; c += 1) {
        const f = courses > 1 ? 0.22 + 0.58 * ((c - 1) / (courses - 1)) : 0.55;
        pushBox(buf,
          (p.e + q.e) / 2, (p.y + q.y) / 2 + height * f - FENCE_RAIL_H_M / 2,
          -(p.n + q.n) / 2, ux, uz,
          bayLen / 2, FENCE_RAIL_W_M / 2, FENCE_RAIL_H_M / 2, level, true);
      }
      const count = Math.max(1, Math.floor(bayLen / boardPitch));
      const first = (bayLen - (count - 1) * boardPitch) / 2;
      for (let k = 0; k < count; k += 1) {
        const t = (first + k * boardPitch) / bayLen;
        pushBox(buf,
          p.e + (q.e - p.e) * t, p.y + (q.y - p.y) * t + height / 2,
          -(p.n + (q.n - p.n) * t), ux, uz,
          boardW / 2, FENCE_BOARD_T_M / 2, height / 2, level, true);
      }
    }
  }
  if (!posts) {
    problems.push(`frontage: ${fence.id} found no dry ground under any post `
      + '— no fence is set');
    return false;
  }
  return true;
}

/**
 * The post, its cross-arm, two hangers and the board hanging under them. Returns
 * the board's own frame so the lettering can be laid on its two faces without
 * re-deriving any of this arithmetic.
 *
 * The frame, against docs/GLB-CONTRACT.md: `facade_bearing_deg` is a compass
 * bearing, so the outward normal is (sin b, cos b) in ENU and the along-wall
 * direction is (cos b, −sin b). The renderer's world is (E, up, −N), which is
 * where every negated north below comes from — the same three lines
 * `signage.js` composes.
 */
function buildPost(buf, post, terrain, level, problems) {
  const at = post.at_local_enu_m;
  if (!Array.isArray(at) || at.length !== 2) {
    problems.push(`frontage: ${post.id} carries no stand — no post is set`);
    return null;
  }
  const g = groundAt(terrain, at[0], at[1]);
  if (g === null) {
    problems.push(`frontage: ${post.id} has no ground under it — no post is set`);
    return null;
  }
  const b = ((post.facade_bearing_deg ?? 0) * Math.PI) / 180;
  const ox = Math.sin(b);
  const oz = -Math.cos(b);       // out of the facade, toward the street
  const wx = Math.cos(b);
  const wz = Math.sin(b);        // along the wall, away from the corner
  const px = at[0];
  const pz = -at[1];
  const h = post.post_height_m ?? 3.6;
  const sq = (post.post_square_m ?? 0.18) / 2;

  // A HITCHING POST IS A POST AND NOTHING ELSE (T-0090). The Sauganash's three
  // views put posts at its road edge and a horse tied to one; none of them puts
  // a board on any of them, so this branch draws chest-high timber under a
  // capped head and returns a frame carrying no text — the lettering pass never
  // sees it, and the record says in as many words why there is nothing to letter.
  if (post.kind === 'hitching_post') {
    const cap = (post.cap_square_m ?? 0.22) / 2;
    const capT = post.cap_thickness_m ?? 0.07;
    pushBox(buf, px, g + (h - capT) / 2, pz, wx, wz, sq, sq, (h - capT) / 2, level);
    pushBox(buf, px, g + h - capT / 2, pz, wx, wz, cap, cap, capT / 2, level);
    return { cx: px, cy: g + h, cz: pz, ox, oz, wx, wz, bw: 0, bh: 0, bt: 0, text: '' };
  }
  const arm = post.arm_m ?? 1.55;
  const armT = 0.09;
  const drop = post.hanger_drop_m ?? 0.18;
  const bw = post.board_w_m ?? 1.3;
  const bh = post.board_h_m ?? 0.55;
  const bt = post.board_thickness_m ?? 0.055;

  // The pole. One box standing on the ground the record's stand samples.
  pushBox(buf, px, g + h / 2, pz, wx, wz, sq, sq, h / 2, level);
  // The cross-arm at its head, running along the wall away from the corner.
  const armY = g + h - armT;
  pushBox(buf, px + wx * (arm / 2), armY, pz + wz * (arm / 2), wx, wz,
    arm / 2, armT / 2, armT / 2, level);
  // A knee brace under it, so the arm reads as carried rather than glued.
  pushBox(buf, px + wx * 0.30, armY - 0.30, pz + wz * 0.30, wx, wz,
    0.30, armT * 0.35, armT * 0.35, level);
  // Two hangers dropping from the arm, and the board under them. The board's
  // long axis runs along the arm and its face looks out of the facade, which is
  // how it is read from the street the inn fronts on.
  const hang = arm * 0.55;
  for (const s of [-1, 1]) {
    pushBox(buf,
      px + wx * (hang + s * bw * 0.36), armY - drop / 2, pz + wz * (hang + s * bw * 0.36),
      ox, oz, 0.022, 0.018, drop / 2, level);
  }
  const cy = armY - drop - bh / 2;
  const cx = px + wx * hang;
  const cz = pz + wz * hang;
  pushBox(buf, cx, cy, cz, wx, wz, bw / 2, bt / 2, bh / 2, level);
  return { cx, cy, cz, ox, oz, wx, wz, bw, bh, bt, text: post.text || '' };
}

/**
 * The painted name, as a canvas texture on a plane just proud of each board
 * face. Drawn rather than left blank because the wording is evidence this
 * project holds and the letterform is the only invented part — see
 * docs/LIBERTIES.md L135 and the record's own `lettering` block.
 */
function makeLettering(boards) {
  const lettered = boards.filter((b) => b && b.text);
  if (!lettered.length) return null;
  const pos = [];
  const nrm = [];
  const uv = [];
  const conf = [];
  // Only one texture is supported per draw call, so the layer draws the first
  // wording it meets and says so if a second ever appears. One board today.
  const first = lettered[0];
  for (const board of lettered) {
    if (board.text !== first.text) continue;
    const { cx, cy, cz, ox, oz, wx, wz, bw, bh, bt } = board;
    const mx = bw * 0.5 - 0.07;
    const my = bh * 0.5 - 0.07;
    const proud = bt / 2 + 0.006;
    for (const side of [1, -1]) {
      const nx = ox * side;
      const nz = oz * side;
      // WHICH WAY THE NAME RUNS. A reader standing off the face has the board's
      // along-wall axis on their LEFT when they look at the near face and on
      // their right at the far one, so the horizontal axis flips with the face
      // — and it is the NEAR face that takes the minus. Getting this backwards
      // draws a perfectly lit board with the name mirrored on both sides, which
      // is what the first build of this layer did.
      const ux = -wx * side;
      const uz = -wz * side;
      const P = (s, t) => [cx + nx * proud + ux * s * mx, cy + t * my, cz + nz * proud + uz * s * mx];
      const quad = [P(-1, -1), P(1, -1), P(1, 1), P(-1, 1)];
      const uvs = [[0, 0], [1, 0], [1, 1], [0, 1]];
      for (const [i, j, k] of [[0, 1, 2], [0, 2, 3]]) {
        for (const idx of [i, j, k]) {
          pos.push(quad[idx][0], quad[idx][1], quad[idx][2]);
          nrm.push(nx, 0, nz);
          uv.push(uvs[idx][0], uvs[idx][1]);
          conf.push(board.level ?? 1);
        }
      }
    }
  }
  if (!pos.length) return null;

  const W = 1024;
  const H = Math.round(W * (first.bh / first.bw));
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = PAINT;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  // Fit the wording to the board rather than choosing a size: the board is a
  // derived width and the name is a given, so the type is what gives way.
  let size = Math.round(H * 0.52);
  const face = (px) => `600 ${px}px Georgia, "Times New Roman", Times, serif`;
  ctx.font = face(size);
  const limit = W * 0.86;
  while (size > 8 && ctx.measureText(first.text).width > limit) {
    size -= 4;
    ctx.font = face(size);
  }
  ctx.fillText(first.text, W / 2, H / 2 + size * 0.03);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  texture.needsUpdate = true;
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(conf, 1));
  geo.computeBoundingSphere();
  return { geo, texture, text: first.text };
}

/* -------------------------------------------------------------------------- */
/* the layer                                                                   */
/* -------------------------------------------------------------------------- */

async function getJSON(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`);
  return res.json();
}

/**
 * @param {object} o dataBase (data/ root) · terrain · confidence · problems
 * @returns {Promise<{group: THREE.Group, records: object[], census: object,
 *                    pickAt: function, dispose: function}>}
 */
export async function createFrontage({
  dataBase, terrain, confidence = null, problems = [],
  /**
   * T-1126 — and here the answer is split, because this layer draws two
   * different kinds of thing off one record.
   *
   * The STANDING timber goes with its building: a board fence behind a shopfront
   * and a hitching post at a trading frontage are furniture belonging to a
   * business, and left standing around an empty lot they say a business was
   * there in exactly the way the auction room's signboard did.
   *
   * The PLANK WALKS do not. A footway is ground, not furniture — it is laid
   * along a street, the walker stands on it (`walkableDecks`), and a stretch of
   * boards with no shop behind it claims nothing about the shop. Taking the walk
   * away would put a hole in the surface a visitor is standing on to look at the
   * hole in the town, which trades a false claim for a worse one.
   */
  hostMissing = () => false,
} = {}) {
  const group = new THREE.Group();
  group.name = 'frontage';
  const out = {
    group,
    records: [],
    walks: [],
    posts: [],
    /** Deck rectangles in local ENU, for the planting block-list: a walk is a
     *  floor, and nothing may grow up through it (T-0085/T-0124). Same shape
     *  as the wharves' keepOut — `{ id, pts }`, consumed by flora's
     *  footprintCircles. */
    keepOut: [],
    /** Walker decks (T-0119): where a walk RIDES a committed deck over water,
     *  the planks are a surface a visitor stands ON, so the walk publishes the
     *  same `{ id, y, pts }` shape `decksFrom()` builds and main.js appends it
     *  to the walker's registry. `y` is the plank top — the deck the record
     *  rides plus the walk's own rise — so the boot and the board agree. */
    walkableDecks: [],
    /** The street-lining fence runs actually built (T-0069). */
    fences: [],
    census: {
      records: 0, walks: 0, crossings: 0, posts: 0, hitching: 0, lettered: 0,
      fences: 0, decks: 0, refused: 0, orphaned: 0, meshes: 0,
      /** THE EDGE RULE (T-0460). `kerb` is how many lengths of string piece the
       *  layer laid down the sides of its walks; `kerbStep_m` is the largest
       *  height step between two consecutive lengths on one run, which is what
       *  is left of the sawtooth once the boards stopped each taking their own
       *  sample of the mud. Both are reported rather than asserted here — the
       *  gate proves the edge on the drawn geometry. */
      kerb: 0, kerbStep_m: 0,
    },
    pickAt: () => null,
    dispose: () => {},
  };

  if (!dataBase || !terrain) {
    problems.push('frontage: no data base or no terrain — no walk is laid');
    return out;
  }
  let index;
  try {
    index = await getJSON(new URL('frontage/index.json', dataBase));
  } catch (err) {
    // Degrade to NOTHING drawn plus a recorded problem, never to an invented
    // walk: the same contract the enclosure, signage and yard layers keep.
    problems.push(`frontage: ${err.message} — no walk is laid`);
    return out;
  }
  const wanted = Array.isArray(index.frontage) ? index.frontage : [];
  const loaded = await Promise.all(wanted.map(async (f) => {
    if (!f.file) return [f.id, null, 'the manifest gave no file'];
    try {
      return [f.id, await getJSON(new URL(`frontage/${f.file}`, dataBase)), null];
    } catch (err) { return [f.id, null, err.message]; }
  }));

  const buf = { pos: [], nrm: [], conf: [] };
  const spans = [];
  const boards = [];
  /** What the string pieces down the walks' edges came to (T-0460). */
  const edgeStats = { kerb: 0, kerbStep: 0 };
  /**
   * CHUNKED TIMBER (T-0119). The layer's timber has been one draw call since
   * T-0082, and for walks a few metres long that is right. The river walk is
   * 400 m of boards, and one geometry spanning Wolf Point to the slough mouth
   * has a bounding sphere no frustum ever culls — every triangle of a walk
   * behind the camera would be drawn from everywhere in the town. So a walk
   * with a POLYLINE centreline builds one small mesh per segment instead
   * (same material, same render order — the draw-call principle bends only as
   * far as culling needs it to), each carrying the walk's owner for the pick.
   */
  const chunks = [];
  /**
   * NAMED CHUNKS (T-0069). A record may put a `chunk` id on a walk, a crossing
   * or a fence, and everything carrying the same id lands in one buffer and
   * becomes one mesh. The town street edge names a chunk per platted block face,
   * so a face's sidewalk, the crossing at its corner and the fence behind it are
   * one bounding sphere and one draw call rather than three of each.
   */
  const named = new Map();
  const bufFor = (chunk, pickId, standing = false) => {
    if (!chunk) return null;
    const key = standing ? `${chunk}__standing` : chunk;
    let hit = named.get(key);
    if (!hit) {
      hit = { buf: { pos: [], nrm: [], conf: [] }, pickId, standing };
      named.set(key, hit);
    }
    return hit;
  };
  /**
   * T-0127 — WHY A FENCE NO LONGER SHARES ITS WALK'S MESH, and it is a shadow
   * decision rather than a culling one.
   *
   * T-0069 put a face's sidewalk, its corner crossing and the fence behind it in
   * ONE buffer, because three meshes where one would do is three draw calls and
   * three bounding spheres. That was right while every furniture mesh cast the
   * same shadow. It stops being right once the two halves want different
   * answers from the sun: a plank walk lies 0.11 m proud of the ground and its
   * own shadow is about 0.04 m wide at noon on 1 July — nothing a visitor can
   * see — while a 1.37 m board fence throws about half a metre of it along the
   * walk it stands behind (T-0115's ledger costed both). Drawing the boards into
   * the shadow map buys nothing and costs their whole triangle count a second
   * time, at the two tiers that cast at all.
   *
   * So the standing timber goes into its own buffer, keyed PER STREET rather
   * than per face: one extra mesh for each covered street instead of one for
   * each fenced face. T-0194's hitching posts join it — they are standing
   * timber on the same faces and they ride the meshes that already exist, which
   * is why a post at every trading frontage costs no draw call at all. That is the whole of the draw-call cost — three calls in
   * the colour pass and three in the shadow pass — against the thirty-five
   * ground-hugging chunks that leave the shadow pass entirely. Per-face
   * standing meshes would have cost twenty-six of each and made the trade a
   * loss.
   */
  const standingChunk = (record, item) => (
    item.street ? `${record.id}__${item.street}__standing` : item.chunk);
  const cards = new Map();
  for (const [id, record, why] of loaded) {
    if (!record) { problems.push(`frontage: ${id} — ${why}`); continue; }
    out.records.push(record);
    out.census.records += 1;
    out.census.refused += (record.refused ?? []).length;
    // A record that is its own subject (the river walk) rather than a
    // building's frontage carries a `card` block, and the layer answers a pick
    // on it with a registry-shaped record of its own — the same shape the boat
    // layer builds, for the same reason: there is no structure to open.
    if (record.card?.id) {
      cards.set(record.card.id, {
        id: record.card.id,
        sidecar: {
          name: record.card.name ?? record.name ?? record.card.id,
          phase: null,
          placement: {
            symbolic_location: record.card.symbolic_location ?? '',
            position_confidence: 'reconstructed',
            position_sources: [],
            position_note: record.card.position_note ?? record.existence?.note ?? '',
          },
          attributes: record.card.attributes ?? {},
          citations: [],
          research_note: record.card.research_note ?? record.research_note ?? '',
        },
      });
    }
    for (const walk of record.walks ?? []) {
      const level = LEVEL[walk.confidence] ?? 1;
      const line = walk.centreline_local_enu_m ?? [];
      const crossing = walk.kind === 'board_crossing';
      const named0 = bufFor(walk.chunk, walk.belongs_to);
      const chunked = !named0 && !crossing && Array.isArray(line) && line.length > 2;
      let ok;
      if (named0) {
        // A named chunk: lay straight into the face's own buffer (T-0069).
        ok = crossing
          ? buildCrossing(named0.buf, walk, terrain, level, problems)
          : buildWalk(named0.buf, walk, terrain, level, problems, edgeStats);
      } else if (chunked) {
        // One chunk per segment; the walk is laid iff any segment laid boards.
        let laid = 0;
        for (let i = 0; i + 1 < line.length; i += 1) {
          const cbuf = { pos: [], nrm: [], conf: [] };
          const boardsLaid = laySegment(cbuf, walk, line[i][0], line[i][1],
            line[i + 1][0], line[i + 1][1], terrain, level, edgeStats);
          if (!boardsLaid) continue;
          chunks.push({ buf: cbuf, pickId: walk.belongs_to });
          laid += boardsLaid;
        }
        ok = laid > 0;
        if (!ok) {
          problems.push(`frontage: ${walk.id} found no ground under any board `
            + '— nothing is laid');
        }
      } else {
        const from = buf.pos.length / 9;
        ok = crossing
          ? buildCrossing(buf, walk, terrain, level, problems)
          : buildWalk(buf, walk, terrain, level, problems, edgeStats);
        if (ok) spans.push({ id: walk.belongs_to, from, to: buf.pos.length / 9 });
      }
      if (!ok) continue;
      out.walks.push(walk);
      out.census[crossing ? 'crossings' : 'walks'] += 1;
      // A walk that rides a committed deck registers the planks as a surface
      // the walker stands on (T-0119) — see `walkableDecks` above.
      if (Number.isFinite(walk.deck_m) && Array.isArray(walk.deck_span_local_enu_m)
          && walk.deck_span_local_enu_m.length >= 3) {
        out.walkableDecks.push({
          id: `${walk.id}__footway`,
          y: walk.deck_m + (walk.rise_m ?? 0.11),
          pts: walk.deck_span_local_enu_m,
        });
      }
      /**
       * AND THE WALK A VISITOR STANDS ON (T-0069). A sidewalk that a walker
       * sinks through is a painted stripe, not a walk, so every run and every
       * crossing on the town street edge publishes its own walking surfaces —
       * the same `{ id, y, pts }` the bridge decks and the river footway
       * publish, through the same registry (T-0045), because there is exactly
       * one mechanism in this project for "the visitor is standing on
       * something that is not the heightfield" and this is it. The heights are
       * the GENERATOR's: it cuts each run into the longest pieces whose ground
       * stays inside one flat deck and takes the highest ground under each,
       * which is what keeps `max(deck, ground)` on the planks from end to end.
       */
      for (const [i, deck] of (walk.footway_decks ?? []).entries()) {
        if (!Number.isFinite(deck?.y) || !Array.isArray(deck.pts) || deck.pts.length < 3) {
          problems.push(`frontage: ${walk.id} deck ${i} is not a surface — skipped`);
          continue;
        }
        out.walkableDecks.push({ id: `${walk.id}__footway_${i}`, y: deck.y, pts: deck.pts });
        out.census.decks += 1;
      }
      // The walk's deck rectangles, in ENU, for the planting block-list — one
      // per centreline segment, so a polyline blocks its whole run. The
      // builders work in world x/z; this stays in the (e, n) frame the flora
      // layer tests in. Exact width on purpose - a tuft leaning over the edge
      // is a verge, a tuft rooted mid-deck is a hole in the model.
      // A LONG SEGMENT IS CUT INTO PIECES, and it is the planting layer that
      // asks for it: `flora.js` rejects most candidates with one squared
      // distance against each block's own bounding circle, and a hundred-metre
      // rectangle has a fifty-metre circle — so a town-length walk would drag
      // every tuft within fifty metres of it down the slow path. Same ground,
      // same block, in pieces the circle test can actually reject.
      const hw = (walk.width_m ?? 1.83) / 2;
      for (let i = 0; i + 1 < line.length; i += 1) {
        const wa = line[i];
        const wb = line[i + 1];
        const de = wb[0] - wa[0];
        const dn = wb[1] - wa[1];
        const wl = Math.hypot(de, dn);
        if (wl < 0.5) continue;
        const cuts = Math.max(1, Math.ceil(wl / KEEPOUT_PIECE_M));
        for (let k = 0; k < cuts; k += 1) {
          const t0 = k / cuts;
          const t1 = (k + 1) / cuts;
          const ae = wa[0] + de * t0;
          const an = wa[1] + dn * t0;
          const be = wa[0] + de * t1;
          const bn = wa[1] + dn * t1;
          const pe = (-dn / wl) * hw;
          const pn = (de / wl) * hw;
          out.keepOut.push({
            id: `${walk.belongs_to}__walk`,
            pts: [[ae + pe, an + pn], [be + pe, bn + pn],
              [be - pe, bn - pn], [ae - pe, an - pn]],
          });
        }
      }
    }
    // The street-lining fences (T-0069). A fence that names a chunk lands in
    // that face's own buffer beside the walk it stands behind; one with no
    // chunk falls back to the layer's shared mesh, exactly as a post does.
    for (const fence of record.fences ?? []) {
      if (hostMissing(fence.belongs_to)) { out.census.orphaned += 1; continue; }
      const level = LEVEL[fence.confidence] ?? 1;
      const bucket = bufFor(standingChunk(record, fence), fence.belongs_to, true);
      const target = bucket ? bucket.buf : buf;
      const from = buf.pos.length / 9;
      if (!buildFence(target, fence, terrain, level, problems)) continue;
      if (!bucket) spans.push({ id: fence.belongs_to, from, to: buf.pos.length / 9 });
      out.fences.push(fence);
      out.census.fences += 1;
    }
    // The posts. A post that names a street (the street edge's hitching posts,
    // T-0194) is STANDING timber and lands in that street's own standing mesh
    // beside the fences — it culls with them, it casts with them, and it costs
    // no draw call of its own. A post with no street (the two inns' own, which
    // are one record each) falls back to the layer's shared mesh, exactly as it
    // always did.
    for (const post of record.posts ?? []) {
      if (hostMissing(post.belongs_to)) { out.census.orphaned += 1; continue; }
      const level = LEVEL[post.confidence] ?? 1;
      const bucket = bufFor(standingChunk(record, post), post.belongs_to, true);
      const target = bucket ? bucket.buf : buf;
      const from = buf.pos.length / 9;
      const board = buildPost(target, post, terrain, level, problems);
      if (!board) continue;
      if (!bucket) spans.push({ id: post.belongs_to, from, to: buf.pos.length / 9 });
      out.posts.push(post);
      out.census.posts += 1;
      if (post.kind === 'hitching_post') out.census.hitching += 1;
      if (board.text) out.census.lettered += 1;
      boards.push({ ...board, level });
    }
  }
  // The named chunks join the polyline ones: same material, same render order,
  // one bounding sphere each (T-0069).
  for (const [id, hit] of named) {
    if (hit.buf.pos.length) {
      chunks.push({ buf: hit.buf, pickId: hit.pickId, id, standing: hit.standing });
    }
  }
  if (!buf.pos.length && !chunks.length) {
    if (out.census.records) {
      problems.push('frontage: the records loaded and not one board was laid');
    }
    return out;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(buf.pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(buf.nrm, 3));
  geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(buf.conf, 1));
  geo.computeBoundingSphere();

  const mat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(TIMBER), roughness: 0.9, metalness: 0.0,
    /**
     * IN THE TRANSPARENT PASS ON PURPOSE, AND NOT BECAUSE ANY OF IT IS
     * TRANSPARENT (T-0625). This timber is opaque and is drawn opaque: alpha is
     * 1, `depthWrite` stays on, and nothing about the picture blends. The flag
     * is here for ONE reason — it is what puts the layer in the same render
     * list as the street ribbon, so that `renderOrder` below can order the two.
     *
     * WHY THAT IS NEEDED. three sorts opaques and transparents into SEPARATE
     * lists and draws every opaque before any transparent; `renderOrder` sorts
     * WITHIN a list and cannot reach across the two. The street ribbon is
     * `transparent: true` (its alpha is genuinely graded — the track feathers
     * at its edges and the ruts and crown modulate it), so a ribbon set to
     * renderOrder 0 was still drawn AFTER opaque timber set to renderOrder 1.
     * The order the comment on `mesh.renderOrder` describes was never the order
     * that ran, for as long as that comment has been there.
     *
     * WHAT IT COST. The ribbon carries `polygonOffset -8/-32` to stop the
     * terrain punching through its drape (R-BUG2, then R-BUG3 deepening it),
     * and `polygonOffsetFactor` scales with the polygon's depth SLOPE — which at
     * the grazing angle you view a road at is enormous. So the ribbon, drawn
     * last and biased hard toward the camera, painted over the plank crossings
     * standing 0.06 m above it, in hard triangular patches following the
     * terrain's own triangulation. The owner reported it twice: it is the
     * "jagged sawtooth" of T-0460 as seen from the street, and T-0460 fixed the
     * walk's board ends without touching this, which is why it survived that
     * ticket. Measured at the Sauganash crossing: 5.2 % of frame pixels wrong.
     *
     * WHY NOT THE OTHER TWO REPAIRS. Biasing the timber's own polygonOffset
     * past the road's works, but it is an arms race against a number tuned
     * twice already, and it pushes the timber through what it abuts — measured
     * worse than this at -10/-40 and worse again at -16/-64. Making the ribbon
     * opaque also works and is worse still: its alpha is real, and dropping the
     * blend hardens every feathered track edge in the town.
     */
    transparent: true,
  });
  mat.name = 'frontage-timber';
  confidence?.patch(mat);
  /**
   * ITS OWN PROGRAM CACHE KEY. three caches a compiled program under a key
   * ending in `customProgramCacheKey()`, whose default is the SOURCE TEXT of
   * `onBeforeCompile` — so every material `confidence.patch()` touches reports
   * the same key and two of them can silently share one program. That drew a
   * whole layer in another layer's shader once already; ticket T-0053 is the
   * general fix and this is the local guard every derived layer carries.
   */
  mat.customProgramCacheKey = () => 'chicago4d-frontage-timber';

  const mesh = new THREE.Mesh(geo, mat);
  /**
   * DRAWN AFTER THE STREET RIBBON, and the owner's report is why. The road is a
   * decal: depthWrite off, polygonOffset -8/-32 so it hugs the terrain without
   * z-fighting it. At a grazing angle that offset outweighs the 6-11 cm a board
   * stands above the ground, so a ribbon drawn after the planks paints STRAIGHT
   * OVER a board crossing. Order is the whole fix: drawn after the ribbon, the
   * planks pass their depth test (the decal writes no depth) and the crossing
   * sits on the road the way a board laid on dirt does. Real occlusion is
   * untouched - terrain writes depth, so a walk behind a rise stays hidden.
   *
   * THIS LINE ALONE DID NOT DO IT, and for two months it read as though it had
   * (T-0625). `renderOrder` orders a mesh within its own render list, and until
   * the material above joined the transparent list this mesh was in the other
   * one — where three draws every opaque before any transparent, whatever their
   * renderOrder. The ordering this comment describes only became real when the
   * material got `transparent: true`; keep the two together.
   */
  mesh.renderOrder = 1;
  mesh.name = 'frontage';
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);

  // The chunked walks (T-0119): one small mesh per polyline segment, sharing
  // the layer's material and render order, each with its own bounding sphere so
  // a reach of the river walk behind the camera culls instead of drawing. The
  // pick carries the owner on the mesh itself — a chunk is one walk's timber
  // and nothing else, so it needs no face-span arithmetic.
  const chunkMeshes = [];
  for (const chunk of chunks) {
    const cgeo = new THREE.BufferGeometry();
    cgeo.setAttribute('position', new THREE.Float32BufferAttribute(chunk.buf.pos, 3));
    cgeo.setAttribute('normal', new THREE.Float32BufferAttribute(chunk.buf.nrm, 3));
    cgeo.setAttribute('_confidence', new THREE.Float32BufferAttribute(chunk.buf.conf, 1));
    cgeo.computeBoundingSphere();
    const cmesh = new THREE.Mesh(cgeo, mat);
    cmesh.renderOrder = 1;                 // same street-decal ordering as above
    cmesh.name = 'frontage-chunk';
    // T-0127 — GROUND-HUGGING TIMBER OPTS OUT OF THE SHADOW MAP. The flag is on
    // the MESH and not on the layer, because within this one layer the boards
    // and the fences want different answers (see `standingChunk` above).
    // `applyShadowTier` in main.js reads it; a tier that casts still casts
    // everything else, and `light`, which casts nothing, is unaffected.
    cmesh.userData.groundHugging = !chunk.standing;
    cmesh.castShadow = !!chunk.standing;
    cmesh.receiveShadow = true;
    cmesh.userData.pickId = chunk.pickId;
    group.add(cmesh);
    chunkMeshes.push(cmesh);
  }
  out.census.meshes = group.children.length;
  out.census.kerb = edgeStats.kerb;
  out.census.kerbStep_m = Math.round(edgeStats.kerbStep * 1000) / 1000;

  const letters = makeLettering(boards);
  let letterMat = null;
  if (letters) {
    letterMat = new THREE.MeshStandardMaterial({
      map: letters.texture,
      color: new THREE.Color(0xffffff),
      roughness: 0.95,
      metalness: 0.0,
      transparent: false,
      alphaTest: 0.5,
      /**
       * DOUBLE-SIDED, and it is not laziness. Each face's quad is wound from the
       * board's own axes rather than from a camera, so one of the two comes out
       * back-facing — and under `FrontSide` the name simply did not draw, on a
       * board that looked perfectly finished. Four triangles is not worth a
       * winding rule that has to be right twice.
       */
      side: THREE.DoubleSide,
    });
    letterMat.name = 'frontage-lettering';
    confidence?.patch(letterMat);
    letterMat.customProgramCacheKey = () => 'chicago4d-frontage-lettering';
    const letterMesh = new THREE.Mesh(letters.geo, letterMat);
    letterMesh.name = 'frontage-lettering';
    letterMesh.castShadow = false;
    letterMesh.receiveShadow = false;
    group.add(letterMesh);
    out.census.meshes = group.children.length;
    out.lettering = letters.text;
  }
  group.userData.census = out.census;

  const raycaster = new THREE.Raycaster();
  /**
   * What a pick on this layer answers: the id of the building (or, for a
   * record that is its own subject, the walk) the timber belongs to — plus,
   * when the layer holds its own card for that id, the registry-shaped record
   * main.js hands the popup when the registry has nothing under it (T-0119).
   */
  out.pickAt = (ndc, camera) => {
    if (!camera) return null;
    raycaster.setFromCamera(ndc ?? new THREE.Vector2(0, 0), camera);
    raycaster.far = Math.max(400, camera.position.y * 4);
    const hits = raycaster.intersectObjects([mesh, ...chunkMeshes], false);
    if (!hits.length) return null;
    const hit = hits[0];
    let id = hit.object.userData.pickId ?? null;
    if (!id) {
      const span = spans.find((sp) => hit.faceIndex >= sp.from && hit.faceIndex < sp.to);
      if (!span) return null;
      id = span.id;
    }
    return {
      id, point: hit.point.clone(), distance: hit.distance,
      record: cards.get(id) ?? null,
    };
  };

  out.dispose = () => {
    geo.dispose();
    for (const c of chunkMeshes) c.geometry.dispose();
    mat.dispose();
    if (letters) { letters.geo.dispose(); letters.texture.dispose(); }
    if (letterMat) letterMat.dispose();
  };
  return out;
}
