/**
 * enclosures.js — the town's fence lines, drawn from a perimeter instead of a
 * footprint.
 *
 * WHY THIS FILE EXISTS. Two liberties in docs/LIBERTIES.md have been waiting on
 * the same missing thing, and both name it in the same words. L10, the Western
 * Hotel: *"A yard is an enclosure — a fence line, two gateways and the ground
 * between them — and `outbuilding` builds a building; using it here would mean
 * calling a fence a building, which is a worse claim than the omission."* L60,
 * the estray pen: *"an enclosure archetype — post-and-rail or notched log,
 * ROOFLESS, gated, taking a perimeter rather than a footprint … it is the honest
 * fix."* Chicago's first public building was a fence, and this project could not
 * build one.
 *
 * The generator half of that fix is a Blender archetype and is not this. This is
 * the RENDERER half, and it needs no bake: an enclosure carries a polyline, a
 * fence type, a height and its gateways, so the same argument that lets
 * `streets.js` draw a wagon track and `flora.js` plant a prairie from committed
 * numbers at load lets this draw a fence. No GLB, no `assets/`, no nightly.
 *
 * WHAT IT WILL AND WILL NOT DO.
 *
 *  * It drapes. Every post samples `terrain.surfaceHeight()` at its own foot, so
 *    a fence crossing a slope steps down it. Nothing here regrades the ground
 *    and nothing here is a collision surface — the walker stands on the same
 *    heightfield it always did and walks THROUGH a fence, which is a stated
 *    shortcoming rather than an oversight (see the note in the changelog).
 *  * It knows three fences. `post_and_rail` is the open horizontal thing the wagon
 *    yard and the pound are built from: posts, and courses spanning between them.
 *    `picket` is the Kinzie-view plate's garden fence — the same posts and two
 *    stringers, closed with a run of vertical pales at the record's own pale width
 *    and gap. `board` is the Sauganash's yard fence: the same construction again,
 *    at the record's own board width and a butted gap, and tall. The difference is
 *    not decoration and it is the whole of what each one says: a rail fence turns a
 *    team and you see the yard through it, a picket fence keeps poultry out of the
 *    vegetables, and a board fence is a wall — it says the ground behind it was
 *    private, which is exactly what the three views of that hotel show.
 *  * It refuses water. A post whose foot is in the river mask is dropped, the
 *    way `trees.js` refuses a stem below the waterline. A fence marching into
 *    the water would be a claim about a shoreline this layer knows nothing of.
 *  * It draws in CULLING-SIZED CHUNKS. It used to be one draw call for the whole
 *    layer — posts and rails emitted into a single non-indexed buffer, because a
 *    fence is a lot of very small boxes and eighty draw calls for eighty sticks
 *    is how a phone loses its frame. That was right while the only enclosures
 *    were one yard and one pound, and it stopped being right the moment the
 *    dooryard pickets put fifteen plots across the whole South Division: one
 *    geometry spanning the town has a bounding sphere no frustum ever culls, so
 *    every fence in Chicago was drawn in every frame including the ones behind
 *    the camera — 33,166 triangles, everywhere, forever. T-0115 measured that
 *    and named it the largest free saving left in the scene, and T-0119 had
 *    already solved the same problem one layer over (`frontage.js` builds the
 *    river walk as one mesh per segment). So a mesh is a piece of fence no more
 *    than `CHUNK_M` across, with its own bounding sphere, on the SAME material,
 *    and the draw-call principle bends exactly as far as culling needs it to and
 *    no further. The chunk is a PATCH OF GROUND rather than a run (T-0068): a
 *    town of lot lines is hundreds of two-point runs a few metres long, and one
 *    mesh apiece would be hundreds of draw calls for fences you can see all at
 *    once — so neighbouring runs share a chunk while it stays under `CHUNK_M`,
 *    and the three sides of one lot's yard are one mesh.
 *  * IT KNOWS WHAT DETAIL LEVEL IT IS DRAWING AT, and T-0056 exists because it
 *    once did not. That ticket was filed against a layer that built once, at
 *    load, and consulted nothing: *"a pale is a very small box and there are
 *    thousands of them."* Four mechanisms have landed on it since, none of them
 *    in that ticket and none of them measured against it, so this is what the
 *    control actually costs the fences today —
 *    `tools/measure_enclosure_detail.mjs`, published mirror, 2026-08-27:
 *
 *      level       owns              at the aerial, colour + sun
 *      full        171,480 tris      342,960
 *      balanced    104,916 tris      209,832   -38.8 %
 *      light       104,916 tris       39,596   -88.5 %
 *
 *    The four are: the PLANK pale at `light` (T-0067) and at `balanced`
 *    (T-0068), which is where the whole 66,564-triangle owned saving comes from
 *    — 11,094 pales at 6 triangles apiece; the 350 m furniture REACH at `light`
 *    (T-0150), which is holding 20 to 37 of the layer's 48 chunks back at the
 *    five stands; and the SHADOW tier (`furnitureCastsShadow: false` at
 *    `light`), which stops the fences being drawn a second time for the sun.
 *    The first is this file's; the other three are `main.js`'s, and the reason
 *    they are named here is that a reader asking T-0056's question is reading
 *    this file. The instrument holds the ladder with `--gate`.
 *
 *    WHAT `light` STILL PAYS IN FULL, so the next reader does not have to
 *    re-derive it: a POST and a RAIL cost the same ten and eight triangles at
 *    every level, and about half of the layer's 5,187 m is `post_and_rail`,
 *    which has no pales to plank. That is deliberate rather than unfinished —
 *    a pale's 22 mm edge is a fortieth of its silhouette and a rail's 90 mm top
 *    face is not, so the same trade does not come round twice.
 *  * It marks itself. Every vertex carries `_confidence`, and it carries the
 *    grade of the WEAKEST thing that decides where that vertex is — which for
 *    every fence in this dataset is the fence type, and every fence type here is
 *    invented. So the whole layer disappears when a visitor hides
 *    `reconstructed`, which is the truthful behaviour: nobody wrote down what
 *    this fence looked like.
 */

import * as THREE from 'three';

/** attested · inferred · reconstructed, as the confidence view reads them. */
const LEVEL = { attested: 0, inferred: 0.5, reconstructed: 1 };

/** Rail stock, in metres. Not a record's numbers — see the note on WOOD below. */
const RAIL_W_M = 0.09;
const RAIL_H_M = 0.13;

/**
 * THE WOOD, AND WHY IT IS NOT IN THE DATA FILE. A rail's own thickness and the
 * colour of weathered oak are the renderer's business in exactly the way a
 * building's shingle colour is the archetype's: they are how a stick is DRAWN,
 * not a claim about the yard. What the record owns — the line, the height, the
 * course count, the post rhythm, the gateways — is read from the file and
 * nothing here overrides it. The tone is the silvered end of the facade palette
 * this project already uses for unpainted board (T-0002), because a yard fence
 * is the least maintained timber on a lot.
 */
const WOOD = 0x8d8272;

/**
 * Pale stock, in metres. Same argument as the rail above: a pale's THICKNESS is how a
 * stick is drawn, where its WIDTH and the gap beside it are the fence's rhythm and
 * belong to the record — `picket_width_m` / `picket_gap_m` and `board_width_m` /
 * `board_gap_m` — because they are what decides whether a visitor is looking at a
 * fence or at a wall. The THICKNESS is shared: a pale and a fence board are the same
 * sawn stuff, and nothing in any record here distinguishes them.
 */
const PALE_T_M = 0.022;

/** A drop this steep between neighbouring posts is a bank, not a yard. */
const MAX_STEP_M = 1.5;

/**
 * How far a chunk is allowed to reach before the layer starts a new one, in
 * metres of bounding-box diagonal. The number is a culling decision and nothing
 * else, and it is a TRADE between the two costs a chunked layer has: small
 * enough that a mesh's bounding sphere stays local to the fence it draws and
 * well inside the 40 m bar the release gate holds this layer to, large enough
 * that a town's worth of fence is tens of meshes rather than hundreds.
 *
 * It was 30 when the layer was four records and 594 m of fence, and 30 held a
 * sphere of 14.9 m. T-0068 put 3.5 km of lot-line fence on it and 30 came to
 * 139 meshes and 51 draw calls MORE than the town had drawn without them, against a
 * budget of 80, because every visible chunk costs one call in the frame and a
 * second in the shadow map. 65 holds a sphere under 33 m, still a fifth inside
 * the bar, and takes the same fence to 40 meshes and 8 calls. A chunk boundary
 * can only fall between two bays at any value, so no member is ever split.
 */
const CHUNK_M = 65;

/**
 * How deep a BAND the layer walks its runs in, west to east, before it moves to
 * the next one south. The number is the plat's: Lake Street to Randolph is about
 * 143 m, so one band holds a platted block and both of its lot tiers, and the
 * two rows of yard fence that face each other across a block's alley arrive
 * together instead of a hundred metres apart in the stream. Measured on the same
 * layer: walking the town in bands rather than in `CHUNK_M` cells is 40 meshes
 * against 70, for identical geometry — a chunker can only pack what it is handed
 * in order.
 */
const BAND_M = 140;

/* -------------------------------------------------------------------------- */
/* geometry                                                                    */
/* -------------------------------------------------------------------------- */

/**
 * WHICH FACES OF A STICK ARE WORTH DRAWING. A fence is thousands of very small
 * boxes, and a box is twelve triangles only if you intend to look at all six of
 * its faces. Every set below drops faces that are BURIED — in the ground, or in
 * the post at either end of a rail — or that carry a fortieth of the
 * silhouette. Nothing here moves a stick, resizes one or changes its rhythm.
 *
 *   `box`     all six. Nothing takes it today; it is the fallback and the
 *             reference the others are read against.
 *   `post`    ten. The underside of a post is under the ground it is driven into.
 *   `rail`    eight. A rail spans from post CENTRE to post centre, so both of its
 *             end caps are inside the post at that end — measured on the widest
 *             rail and the narrowest post on this layer, 45 mm of rail half-width
 *             inside a 50 mm post half-width, at every bay, on every record.
 *             T-0068 costed the six that remain: it is a quarter of the timber on
 *             a rail fence, and rail fences are most of what a town of lot lines
 *             is made of.
 *   `pale`    ten, the same argument as a post: at 3,500 pales the buried
 *             underside is 7,000 triangles nobody can ever see.
 *   `plank`   **four**, which is what a pale takes at `light` (T-0067, costed by
 *             T-0115). A pale is a 22 mm-thick prism, and of its ten triangles SIX
 *             are the two 22 mm edge faces and the 22 mm top cap — three quarters
 *             of the geometry for one fortieth of the silhouette. At `light` a
 *             pale is drawn as a zero-thickness double-sided plank instead: the two
 *             broad faces only, each with its own outward normal so it lights
 *             correctly from either side of the fence without a second material.
 *             The pale keeps its width, its height, its position and its rhythm;
 *             what it loses is a thickness you cannot see from more than a metre
 *             away and could never see at all from the side the fence is meant to
 *             be read from. `full` and `balanced` draw the prism, unchanged.
 *
 * The face order below is +u, -u, +v, -v, top, underside, where `u` runs along
 * the stick — so for a RAIL the ±u pair is the end caps, and for a PALE the ±v
 * pair is the two broad faces.
 */
const PARTS = {
  box: [0, 1, 2, 3, 4, 5],
  post: [0, 1, 2, 3, 4],
  rail: [2, 3, 4, 5],
  pale: [0, 1, 2, 3, 4],
  plank: [2, 3],
};

function pushBox(buf, cx, cy, cz, ux, uz, halfLen, halfW, halfH, level,
                 part = 'box') {
  const plank = part === 'plank';
  // `u` is the horizontal unit vector along the box; `v` is horizontal and
  // perpendicular to it. Up is world Y, always: a leaning fence post is a
  // claim about ground this layer does not make.
  const vx = -uz;
  const vz = ux;
  // A plank is the same box with its thickness taken out, so the two broad
  // faces below land exactly on the line the pale's centre is authored on —
  // which is where the prism's own centre stood.
  const w = plank ? 0 : halfW;
  const P = (a, b, c) => [
    cx + ux * a * halfLen + vx * b * w,
    cy + c * halfH,
    cz + uz * a * halfLen + vz * b * w,
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
  const wanted = (PARTS[part] ?? PARTS.box).map((i) => faces[i]);
  for (const [t1, t2, n] of wanted) {
    for (const tri of [t1, t2]) {
      for (const i of tri) {
        buf.pos.push(p[i][0], p[i][1], p[i][2]);
        buf.nrm.push(n[0], n[1], n[2]);
        buf.conf.push(level);
      }
    }
  }
}

/** Cumulative arc length along a local-ENU polyline. */
function measure(path) {
  const s = [0];
  for (let i = 1; i < path.length; i++) {
    const de = path[i][0] - path[i - 1][0];
    const dn = path[i][1] - path[i - 1][1];
    s.push(s[i - 1] + Math.hypot(de, dn));
  }
  return s;
}

/** The point at arc length `d` along the polyline, in local ENU. */
function at(path, s, d) {
  const t = Math.min(Math.max(d, 0), s[s.length - 1]);
  let i = 1;
  while (i < s.length - 1 && s[i] < t) i++;
  const span = s[i] - s[i - 1] || 1;
  const f = (t - s[i - 1]) / span;
  return [
    path[i - 1][0] + (path[i][0] - path[i - 1][0]) * f,
    path[i - 1][1] + (path[i][1] - path[i - 1][1]) * f,
  ];
}

/** Where along the polyline a gateway's stated centre falls. */
function arcOf(path, s, point) {
  let best = { d: 0, dist: Infinity };
  for (let i = 1; i < path.length; i++) {
    const ex = path[i - 1][0];
    const ny = path[i - 1][1];
    const dx = path[i][0] - ex;
    const dy = path[i][1] - ny;
    const len2 = dx * dx + dy * dy || 1;
    let t = ((point[0] - ex) * dx + (point[1] - ny) * dy) / len2;
    t = Math.min(Math.max(t, 0), 1);
    const dist = Math.hypot(ex + dx * t - point[0], ny + dy * t - point[1]);
    if (dist < best.dist) best = { d: s[i - 1] + t * Math.sqrt(len2), dist };
  }
  return best.d;
}

/**
 * The stretches of a run that carry fence: its whole length, minus a gap for
 * every gateway that lands on it. A gateway is a HOLE, deliberately — this
 * layer hangs no gate leaf, because no source describes one and a drawn gate
 * would be an invention on top of an invention.
 */
function stretches(path, s, gaps) {
  let spans = [[0, s[s.length - 1]]];
  for (const g of gaps) {
    const a = g.d - g.width / 2;
    const b = g.d + g.width / 2;
    const next = [];
    for (const [lo, hi] of spans) {
      if (b <= lo || a >= hi) { next.push([lo, hi]); continue; }
      if (a > lo) next.push([lo, a]);
      if (b < hi) next.push([b, hi]);
    }
    spans = next;
  }
  return spans.filter(([lo, hi]) => hi - lo > 0.2);
}

/* -------------------------------------------------------------------------- */
/* building the town's fences                                                  */
/* -------------------------------------------------------------------------- */

/**
 * A chunk under construction: one buffer, and the bounding box of the ground it
 * has covered so far. The DIAGONAL of that box is what `CHUNK_M` bounds — a mesh
 * whose bounding sphere is bigger than its own fence is a mesh the frustum
 * cannot cull.
 */
function newChunk() {
  return { pos: [], nrm: [], conf: [],
    minE: Infinity, maxE: -Infinity, minN: Infinity, maxN: -Infinity };
}
function cover(chunk, e, n) {
  if (e < chunk.minE) chunk.minE = e;
  if (e > chunk.maxE) chunk.maxE = e;
  if (n < chunk.minN) chunk.minN = n;
  if (n > chunk.maxN) chunk.maxN = n;
}
/**
 * Would this chunk still be culling-sized after it took the ground these feet
 * stand on? Asked BEFORE the bay is emitted rather than after, which is the whole
 * of the difference between this and the test T-0067 shipped.
 *
 * That one asked whether the chunk in hand had ALREADY overrun, so the bay that
 * pushed it over went in anyway and the overrun was capped only because every run
 * started a chunk of its own. That was right for four records and fifteen garden
 * plots; it is wrong for a town of lot lines, where a record holds a hundred
 * two-point runs a few metres long and one mesh per run is a hundred draw calls
 * for a hundred fences you can see at once. Asking first lets NEIGHBOURING runs
 * share a chunk — three sides of one lot's yard are one mesh now — while the
 * bounding box is held under `CHUNK_M` by construction rather than by accident.
 * A chunk boundary still falls only between two bays, so no member is split.
 */
function fits(chunk, ...feet) {
  let { minE, maxE, minN, maxN } = chunk;
  for (const f of feet) {
    if (!f) continue;
    if (f.e < minE) minE = f.e;
    if (f.e > maxE) maxE = f.e;
    if (f.n < minN) minN = f.n;
    if (f.n > maxN) maxN = f.n;
  }
  if (!Number.isFinite(minE)) return true;
  return Math.hypot(maxE - minE, maxN - minN) <= CHUNK_M;
}

/** The construction one record's `form` block states, read once for the record. */
function formOf(record) {
  const form = record.form ?? {};
  const height = form.height_m?.value ?? 1.37;
  const courses = Math.max(1, Math.round(form.rail_courses?.value ?? 3));
  const spacing = Math.max(1, form.post_spacing_m?.value ?? 2.9);
  const postHalf = (form.post_size_m?.value ?? 0.14) / 2;
  const kind = form.fence_type?.value ?? 'post_and_rail';
  // TWO CLOSED FENCES AND ONE OPEN ONE. A picket and a board fence are the same
  // construction — posts, stringers behind them, vertical stock nailed across —
  // and they differ in the STOCK, which is the whole of what a visitor reads:
  // a pale is a hand's width with a hand's width of daylight beside it, and a
  // board is butted to its neighbour so there is none. That is why the two are
  // one branch here and two values in the record: the difference between a
  // garden fence you see the garden through and a fence that makes a yard a
  // room is `board_gap_m`, and it belongs to the record for the same reason
  // `picket_gap_m` does.
  const closed = kind === 'picket' || kind === 'board';
  const board = kind === 'board';
  const paleW = Math.max(0.02,
    (board ? form.board_width_m?.value : form.picket_width_m?.value) ?? 0.089);
  // A board fence's gap is allowed to be the shrinkage gap between two butted
  // boards, which is millimetres; a pale's floor stays where it was.
  const palePitch = paleW + Math.max(board ? 0 : 0.01,
    (board ? form.board_gap_m?.value : form.picket_gap_m?.value) ?? 0.089);
  // The weakest grade on anything that decides where a stick of this fence is.
  // In practice that is the fence type, and no fence type in this dataset is
  // anything but invented; the max is here so the day a source describes one,
  // the geometry stops claiming to be a guess.
  const level = Math.max(
    LEVEL[form.fence_type?.confidence] ?? 1,
    LEVEL[form.height_m?.confidence] ?? 1,
  );
  return { height, courses, spacing, postHalf, closed, board, paleW, palePitch, level };
}

/**
 * THE CHUNKER, and why it is one object for the whole layer rather than one per
 * record.
 *
 * A chunk is a PATCH OF GROUND no more than `CHUNK_M` across, holding whatever
 * fence stands on it. Its boundaries fall only between two bays — a post, its
 * rails and its pales all go into the same buffer — so no member is ever split
 * and nothing moves by a millimetre.
 *
 * It is shared across records because the town is not laid out by record. The
 * three lot-line records interleave lot by lot down every block: a store's board
 * fence, its neighbour's pickets and the rail fence at the end of the row stand
 * within twenty metres of each other and are the same material, and one mesh
 * apiece is three draw calls for one back yard. So the layer walks EVERY run in
 * one spatial order and packs them together. The one thing a chunk may not mix
 * is OWNERSHIP: a chunk carries the `structure_id` of the record whose card a
 * click on it should open, so a record that has one (the estray pen) gets chunks
 * of its own and everything else — which has no card behind it — shares.
 */
function newChunker() {
  return { chunks: [], buf: newChunk(), owner: undefined, ids: new Set() };
}
function flushChunk(ch) {
  if (ch.buf.pos.length) {
    ch.buf.pickId = ch.owner ?? null;
    ch.buf.recordIds = [...ch.ids];
    ch.chunks.push(ch.buf);
  }
  ch.buf = newChunk();
  ch.ids = new Set();
}

/** One run's timber, emitted into the shared chunker. */
function emitRun(task, terrain, ch, tally, plankPales) {
  const { record, run, form: f } = task;
  const { height, courses, spacing, postHalf, closed, paleW, palePitch, level } = f;
  // Flushing mid-run starts an empty chunk, and the record this run belongs to has
  // to be named on that one too — `recordIds` is what a reader asking "what is in
  // this mesh" gets back.
  const flush = () => { flushChunk(ch); ch.ids.add(record.id); };
  const path = run.path_local_enu_m;
  // A chunk may hold timber from several records but never from two OWNERS: its
  // `pickId` is what a click on it answers with.
  const owner = record.structure_id ?? null;
  if (ch.owner !== undefined && owner !== ch.owner) flush();
  ch.owner = owner;
  ch.ids.add(record.id);
  const s = measure(path);
  const gaps = (record.openings ?? [])
    .map((o) => ({ d: arcOf(path, s, o.at_local_enu_m), width: o.width_m ?? 4.27, o }))
    // A gateway belongs to whichever run it actually stands on: the record
    // states a point, not a run id, so a gate that is 6 m from this line is
    // the other frontage's and must not punch a hole here.
    .filter((g) => {
      const p = at(path, s, g.d);
      return Math.hypot(p[0] - g.o.at_local_enu_m[0], p[1] - g.o.at_local_enu_m[1]) < 1.0;
    });

  for (const [lo, hi] of stretches(path, s, gaps)) {
    const n = Math.max(1, Math.round((hi - lo) / spacing));
    const step = (hi - lo) / n;
    // Post feet first, so a rail can be hung between two known heights and a
    // post standing in the river takes its rails with it.
    const feet = [];
    for (let i = 0; i <= n; i++) {
      const [e, north] = at(path, s, lo + i * step);
      if (terrain.isWater?.(e, north)) { feet.push(null); tally.dropped++; continue; }
      feet.push({ e, n: north, y: terrain.surfaceHeight(e, north) });
    }
    const post = (foot) => {
      if (!foot) return;
      cover(ch.buf, foot.e, foot.n);
      pushBox(ch.buf, foot.e, foot.y + height / 2, -foot.n, 1, 0,
        postHalf, postHalf, height / 2, level, 'post');
      tally.posts++;
    };
    for (let i = 0; i < n; i++) {
      // The bay's own near post, then its timber: one bay is the smallest
      // thing a chunk boundary may fall between, so it is emitted whole.
      if (!fits(ch.buf, feet[i], feet[i + 1])) flush();
      post(feet[i]);
      const a = feet[i];
      const b = feet[i + 1];
      if (!a || !b) continue;
      if (Math.abs(a.y - b.y) > MAX_STEP_M) { tally.dropped++; continue; }
      cover(ch.buf, b.e, b.n);
      const de = b.e - a.e;
      const dn = b.n - a.n;
      const len = Math.hypot(de, dn);
      if (len < 0.05) continue;
      // The renderer's world is (E, up, -N), so the along-run unit vector
      // has its north component negated with the position.
      const ux = de / len;
      const uz = -dn / len;
      for (let c = 1; c <= courses; c++) {
        // On a rail fence the courses ARE the fence, so the top one is the top of
        // it. On a picket fence they are stringers behind the pales and want to sit
        // inside the height, or the top rail reads as a cap rail nobody described.
        const at01 = closed
          ? (courses > 1 ? 0.22 + 0.58 * ((c - 1) / (courses - 1)) : 0.55)
          : c / courses;
        const h = height * at01 - RAIL_H_M / 2;
        pushBox(ch.buf,
          (a.e + b.e) / 2, (a.y + b.y) / 2 + h, -(a.n + b.n) / 2,
          ux, uz, len / 2, RAIL_W_M / 2, RAIL_H_M / 2, level, 'rail');
      }
      if (closed) {
        // The pales, centred on the run line exactly as the posts and rails are.
        // Nailing them to one face would be more like a real fence and would push
        // timber off the line the record authored, which is the one thing the
        // layer's own gate measures; the interpenetration costs nothing on screen.
        const count = Math.max(1, Math.floor(len / palePitch));
        const first = (len - (count - 1) * palePitch) / 2;
        for (let k = 0; k < count; k++) {
          const t = (first + k * palePitch) / len;
          pushBox(ch.buf,
            a.e + de * t, a.y + (b.y - a.y) * t + height / 2, -(a.n + dn * t),
            ux, uz, paleW / 2, PALE_T_M / 2, height / 2, level,
            plankPales ? 'plank' : 'pale');
          tally.pales++;
        }
      }
    }
    // The stretch's far post: the loop above emits each bay's NEAR post, so
    // the last one would otherwise be left off the end of every run.
    if (!fits(ch.buf, feet[n])) flush();
    post(feet[n]);
  }
}

/**
 * WHERE THE LAYER'S RUNS ARE WALKED FROM, and why the order is the layer's own
 * business rather than the manifest's. Two runs that end up in one chunk have to
 * arrive next to each other, so the whole layer is sorted into a coarse spatial
 * order first: by owner (a chunk may not mix them), then by the `BAND_M` band
 * the run's midpoint falls in, then west to east inside it. Sorting here rather
 * than in the data means three records that interleave lot by lot down a block
 * still pack into the same meshes.
 */
function orderRuns(records) {
  const tasks = [];
  for (const record of records) {
    const form = formOf(record);
    for (const run of record.runs ?? []) {
      const path = run.path_local_enu_m;
      if (!Array.isArray(path) || path.length < 2) continue;
      let e = 0;
      let n = 0;
      for (const p of path) { e += p[0]; n += p[1]; }
      tasks.push({ record, run, form,
        owner: record.structure_id ?? '',
        e: e / path.length, n: n / path.length });
    }
  }
  return tasks.sort((a, b) => (
    (a.owner < b.owner ? -1 : a.owner > b.owner ? 1 : 0)
    || Math.floor(-a.n / BAND_M) - Math.floor(-b.n / BAND_M)
    || a.e - b.e || (-a.n) - (-b.n)
  ));
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
 * The detail levels at which a pale is drawn as a plank rather than a prism.
 * Named here rather than read out of `main.js` so the layer answers for its own
 * geometry; `main.js` passes the level and this decides what that level means to
 * a fence. See the note on `pushBox`.
 *
 * `balanced` JOINED `light` IN T-0068, and the reason is the tier's own job. The
 * middle tier existed as a triangle ceiling that nothing on this layer had ever
 * given anything up to reach: a pale cost 10 triangles at `balanced` exactly as
 * it did at `full`, so the town's fences scaled the same at both and `balanced`
 * was `full` with thinner grass. Putting 3.5 km of lot-line fence on the layer
 * made that visible — the middle tier was reading 794,000 of its 800,000 while
 * `full` sat 150,000 clear of its own. What `balanced` now gives up is the same
 * 22 mm of pale thickness `light` gives up, worth about 56,000 triangles on the
 * town's 11,000 pales, and it is the same argument: a rendering decision rather
 * than a claim, invisible from anywhere but standing on the fence line looking
 * along it. `full` draws the prism. A pale's WIDTH, HEIGHT, PLACE and RHYTHM are
 * the record's and do not move at any tier.
 */
const PLANK_LEVELS = new Set(['light', 'balanced']);

/**
 * @param {object} o dataBase (data/ root) · terrain · confidence · problems ·
 *                   detail (the scene-detail level, `full` by default)
 * @returns {Promise<{group: THREE.Group, records: object[], census: object,
 *                    setDetail: function, dispose: function}>}
 */
export async function createEnclosures({
  dataBase, terrain, confidence = null, problems = [], detail = 'full',
} = {}) {
  const group = new THREE.Group();
  group.name = 'enclosures';
  const out = { group, records: [],
    census: { enclosures: 0, posts: 0, pales: 0, dropped: 0, chunks: 0 },
    // Replaced once there is a mesh to raycast; a layer that drew nothing still
    // answers a pick, with nothing.
    pickAt: () => null,
    setDetail: () => false,
    dispose: () => {} };

  if (!dataBase || !terrain) {
    problems.push('enclosures: no data base or no terrain — no fence is drawn');
    return out;
  }
  let index;
  try {
    index = await getJSON(new URL('enclosures/index.json', dataBase));
  } catch (err) {
    // Degrade to NOTHING drawn plus a recorded problem, never to an invented
    // fence: the same contract the vegetation layers keep.
    problems.push(`enclosures: ${err.message} — no fence, yard or pen is drawn`);
    return out;
  }
  const wanted = Array.isArray(index.enclosures) ? index.enclosures : [];
  const loaded = await Promise.all(wanted.map(async (e) => {
    if (!e.file) return [e.id, null, 'the manifest gave no file'];
    try {
      return [e.id, await getJSON(new URL(`enclosures/${e.file}`, dataBase)), null];
    } catch (err) { return [e.id, null, err.message]; }
  }));

  for (const [id, record, why] of loaded) {
    if (!record) { problems.push(`enclosures: ${id} — ${why}`); continue; }
    out.records.push(record);
  }
  if (!out.records.length) return out;

  const mat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(WOOD), roughness: 0.92, metalness: 0.0,
  });
  mat.name = 'enclosure-timber';
  confidence?.patch(mat);
  /**
   * THE PROGRAM CACHE KEY, AND WHY THIS ONE LINE IS NOT OPTIONAL.
   *
   * three caches a compiled program under a key that ends in
   * `material.customProgramCacheKey()`, whose default is
   * `this.onBeforeCompile.toString()` — the SOURCE TEXT of the hook, not the
   * closure. Every material `confidence.patch()` touches therefore reports the
   * same key text, so two patched materials that agree on every other program
   * parameter share one compiled program, and the one that compiles first wins.
   *
   * Measured on the first build of this layer: a plain patched
   * MeshStandardMaterial with no map, opaque, is parameter-for-parameter the
   * twin of a mapless building material out of `buildings.js`, which chains a
   * SECOND hook reading the per-vertex `_roughness` and facade-tone attributes
   * this geometry does not have. The fence drew in the right place, in the right
   * shape, casting the right shadow, in SOLID BLACK, at both viewports, with no
   * page error and no shader warning — because it was being drawn by another
   * layer's program against attributes it never bound. Unpatching the material
   * lit it perfectly, which is what made the cause so hard to see.
   *
   * The key below is this layer's own, so the fence gets its own program. The
   * general trap is not fixed here — any future layer that patches a plain lit
   * material walks into the same collision — and is filed as its own ticket.
   */
  mat.customProgramCacheKey = () => 'chicago4d-enclosure-timber';

  /**
   * WHICH RECORD A MESH BELONGS TO, and why this layer bothers.
   *
   * A hit on a merged buffer knows nothing about which fence it landed on. That
   * was fine while the only enclosure was a yard nobody could ask a question
   * about. It stopped being fine with the estray pen (T-0051): the pen is a
   * STRUCTURE RECORD whose geometry moved here, its card is still compiled from
   * `data/structures/estray_pen.json`, and a visitor who could click Chicago's
   * first public building while it was a roofed box must not lose the card
   * because the model got more honest about its roof.
   *
   * It used to be answered with banked triangle ranges and a `faceIndex` lookup.
   * Chunking answers it better and for free: a chunk may never hold timber from
   * two OWNERS, so the owner rides on the mesh (`userData.pickId`) exactly as it
   * does on the chunked plank walks in `frontage.js`. An enclosure with no
   * `structure_id` — the wagon yard, the town's garden pickets, the lot-line
   * yards — carries null and is not pickable, which is correct: there is no card
   * behind it, and those records are free to share a chunk with each other
   * because none of them has an answer to lose.
   */
  let meshes = [];

  /**
   * Build (or rebuild) the layer's meshes at the level in hand. Rebuilding is
   * what a change of scene detail costs here, and it costs no fetch: the records
   * are already loaded, and geometry this small is faster to rebuild than a
   * second copy of it is to keep. `problems` is only collected on the FIRST
   * build — a rebuild that re-reported every one of them would grow the panel
   * every time a visitor touched the detail control.
   */
  let level = detail;
  let firstBuild = true;
  function build() {
    for (const m of meshes) { group.remove(m); m.geometry.dispose(); }
    meshes = [];
    const sink = firstBuild ? problems : [];
    const census = { enclosures: 0, posts: 0, pales: 0, dropped: 0, chunks: 0 };
    const plankPales = PLANK_LEVELS.has(level);
    const ch = newChunker();
    // Per-record, so a record that drew nothing can still be named; the CHUNKS
    // themselves are the layer's and may hold more than one record's timber.
    const tallies = new Map(out.records.map((r) => [r.id, { posts: 0, pales: 0, dropped: 0 }]));
    for (const task of orderRuns(out.records)) {
      emitRun(task, terrain, ch, tallies.get(task.record.id), plankPales);
    }
    flushChunk(ch);
    for (const chunk of ch.chunks) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(chunk.pos, 3));
      geo.setAttribute('normal', new THREE.Float32BufferAttribute(chunk.nrm, 3));
      geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(chunk.conf, 1));
      // The whole point of the chunk: its own bounding sphere, around its own
      // fence, so the frustum can leave it out.
      geo.computeBoundingSphere();
      const mesh = new THREE.Mesh(geo, mat);
      mesh.name = 'enclosure-chunk';
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData.pickId = chunk.pickId ?? null;
      mesh.userData.recordIds = chunk.recordIds ?? [];
      group.add(mesh);
      meshes.push(mesh);
      census.chunks += 1;
    }
    for (const record of out.records) {
      const t = tallies.get(record.id);
      // A record with NO RUNS AT ALL is not a fence that failed to draw — it is a
      // record that rides this manifest to carry GROUND and says so (T-0097's fort
      // apron, whose enclosure is the palisade: a committed structure with a baked
      // GLB, so there is no fence here to draw and a second wall beside the first
      // is what drawing one would mean). Complaining about it would file a problem
      // on every load for a record behaving exactly as written.
      if (!t.posts && (record.runs ?? []).length) {
        sink.push(`enclosures: ${record.id} drew nothing — every post stood in water `
          + 'or the record carries no run with two points');
      }
      census.enclosures += 1;
      census.posts += t.posts;
      census.pales += t.pales;
      census.dropped += t.dropped;
    }
    firstBuild = false;
    Object.assign(out.census, census);
    group.userData.census = out.census;
  }
  build();
  if (!meshes.length) return out;

  /**
   * A change of scene detail, applied in place. Returns whether anything was
   * rebuilt, so the caller can re-apply the shadow policy only when it has to —
   * every mesh here is new after a rebuild and starts out casting.
   */
  out.setDetail = (next) => {
    if (!next || next === level) return false;
    const was = PLANK_LEVELS.has(level);
    level = next;
    if (PLANK_LEVELS.has(level) === was) return false;
    build();
    return true;
  };

  const raycaster = new THREE.Raycaster();
  /**
   * The structure this fence stands for, or null. Same ray budget as
   * `buildings.pickAt` — as far as you can see, which depends on how high you
   * are — so a fence and a roof answer a click on the same terms.
   */
  out.pickAt = (ndc, camera) => {
    if (!camera) return null;
    raycaster.setFromCamera(ndc ?? new THREE.Vector2(0, 0), camera);
    raycaster.far = Math.max(400, camera.position.y * 4);
    const hits = raycaster.intersectObjects(meshes, false);
    if (!hits.length) return null;
    const hit = hits[0];
    const id = hit.object?.userData?.pickId ?? null;
    if (!id) return null;
    return { id, point: hit.point.clone(), distance: hit.distance };
  };

  out.dispose = () => {
    for (const m of meshes) m.geometry.dispose();
    meshes = [];
    mat.dispose();
  };
  return out;
}
