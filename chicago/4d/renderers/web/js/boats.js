/**
 * boats.js — the era-correct watercraft on the river (T-0063).
 *
 * WHY THIS FILE EXISTS. The owner, 2026-08-18, verbatim: *"you can add boats
 * correct for the era! they would exist"* — and, of the drawbridge engravings,
 * *"also note the boats there."* Both drawbridge views in the 2026-08-18 brief
 * hang schooner masts over the reach below the bridge, the South Water 1834
 * view draws rowboats on the water and at the bank, and the committed fort
 * plates put bark canoes at the fort reach. Until this layer existed the river
 * carried docks and not one hull — a working waterfront with nothing to work.
 *
 * WHAT IT WILL AND WILL NOT DO.
 *
 *  * EVERY BOAT IS AUTHORED AND EVERY BOAT IS INVENTED. No rule can derive
 *    where a vessel lay on a July morning, so `data/boats/` states each hull
 *    with its own note and docs/LIBERTIES.md L146 claims the invention. This
 *    file only draws what that record says, and REFUSES what the committed
 *    terrain cannot carry: an afloat boat without its own draft of water under
 *    the whole keel, a beached boat authored onto open water or up on the
 *    prairie, or any hull inside the drawbridge's navigation clearance. A
 *    refusal is a recorded problem, never a nudged position.
 *  * AN AFLOAT HULL RIDES THE WATER PLANE — keel at `WATER_Y` minus the
 *    record's own draft — and a BEACHED hull sits on the terrain's surface at
 *    its own keel line, sampled at load. The bridge's lesson (T-0001) again:
 *    no height here is authored beside the mesh.
 *  * NO CREW, NO CARGO, NO SET SAILS, NO NAMES. L1 ships no human figures,
 *    uniformly; a named hull would claim a berth on a date no source gives.
 *    The two canoes are trade watercraft drawn unmanned from the fort plates —
 *    the standing constraint on depicting Native presence stands in full, and
 *    the record's own note says so.
 *  * It is ONE draw call for the whole layer, like the fences, the boards, the
 *    goods and the docks. Double-sided, because an open skiff shows its inside.
 *  * It marks itself: every vertex carries `_confidence` at `reconstructed`,
 *    so the whole flotilla disappears when a visitor hides `reconstructed` and
 *    the river goes honestly empty again.
 *  * It answers a pick. A boat belongs to no structure, so aiming at one opens
 *    a card built from the boat's OWN record — type, size, state and the note
 *    saying what bounded the invention — through the same popup the buildings
 *    use.
 */

import * as THREE from 'three';

/** attested · inferred · reconstructed, as the confidence view reads them. */
const LEVEL = { attested: 0, documented: 0, inferred: 0.5, reconstructed: 1 };

/** The summer-1835 water surface, the same zero terrain.js draws the river at. */
const WATER_Y = 0;

/** The Dearborn Street drawbridge's crossing line (its record's local_e) and
 *  the main-stem band it spans — the clearance rule in `data/boats/` is stated
 *  against this line, and the layer is what enforces it. */
const DRAWBRIDGE_E = 699.17;
const MAIN_STEM_N_MAX = 120;

/** Water an afloat hull must have under its keel beyond its own draft. */
const UNDER_KEEL_M = 0.3;

/**
 * THE DRAWING'S OWN GRAIN — how many stations a hull is lofted through, where
 * the chine sits, how thick a mast is drawn. The record owns every CLAIM about
 * the water (type, size, position, heading, clearances); these numbers are only
 * how a claim becomes triangles, the same division `wharves.js` draws between a
 * deck's outline and its crib's bent spacing.
 */
const STATIONS = 7;          // loft stations bow to stern
const CHINE_W = 0.82;        // chine half-breadth, as a fraction of the gunwale's
const CHINE_H = 0.22;        // chine height above keel, as a fraction of depth
const MAST_SIDE_M = 0.26;    // a mast is drawn this square
const BOWSPRIT_M = 3.8;      // and reaches this far past the stem

/** The layer's timber tone — between the wharves' wet structural grey and the
 *  yard's warm cooperage: working hulls, tarred and weathered. As everywhere
 *  else: `ColorManagement.enabled` is true, `setHex` reads sRGB. */
const BOAT_COLOUR = 0x7a7060;

/* -------------------------------------------------------------------------- */
/* primitives                                                                  */
/* -------------------------------------------------------------------------- */

/** One triangle with its own face normal. The loft's unit. */
function pushTri(buf, a, b, c, level) {
  const ux = b[0] - a[0]; const uy = b[1] - a[1]; const uz = b[2] - a[2];
  const vx = c[0] - a[0]; const vy = c[1] - a[1]; const vz = c[2] - a[2];
  let nx = uy * vz - uz * vy;
  let ny = uz * vx - ux * vz;
  let nz = ux * vy - uy * vx;
  const len = Math.hypot(nx, ny, nz);
  if (len < 1e-9) return;              // a degenerate loft quad's second half
  nx /= len; ny /= len; nz /= len;
  for (const p of [a, b, c]) {
    buf.pos.push(p[0], p[1], p[2]);
    buf.nrm.push(nx, ny, nz);
    buf.conf.push(level);
  }
}

function pushQuad(buf, a, b, c, d, level) {
  pushTri(buf, a, b, c, level);
  pushTri(buf, a, c, d, level);
}

/** One box — same helper shape as the wharf, fence and yard layers'. `u` is
 *  the horizontal unit vector along the box's length; up is world Y. */
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
    [1, 5, 6, 2], [4, 0, 3, 7], [3, 2, 6, 7], [0, 4, 5, 1], [4, 7, 6, 5], [0, 1, 2, 3],
  ];
  for (const [a, b, c, d] of faces) pushQuad(buf, p[a], p[b], p[c], p[d], level);
}

/* -------------------------------------------------------------------------- */
/* the hulls                                                                   */
/* -------------------------------------------------------------------------- */

/** Local ENU (e, n) to the renderer's world (x, z). World is (E, up, −N). */
const wx = (e) => e;
const wz = (n) => -n;

/**
 * The loft's plan and profile, per type. `halfB(t)` is the gunwale half-breadth
 * at station t ∈ [0 bow, 1 stern] as a fraction of beam/2; `sheer(t)` the
 * gunwale height above the midship keel as a fraction of depth; `keel(t)` the
 * keel's own rise toward the ends.
 */
const HULL_FORMS = {
  schooner: {
    depthOf: (f) => f.draft + f.freeboard,
    halfB: (t) => Math.sin(Math.PI * (0.08 + 0.84 * t)) ** 0.8,
    stern: 0.55,                         // transom, as a fraction of half-beam
    sheer: (t) => 1 + 0.14 * (1 - t) ** 2 + 0.06 * t ** 2,
    keel: () => 0,
    decked: true,
  },
  rowboat: {
    depthOf: (f) => f.draft + f.freeboard,
    halfB: (t) => Math.sin(Math.PI * (0.10 + 0.82 * t)) ** 0.9,
    stern: 0.62,
    sheer: (t) => 1 + 0.10 * (1 - t) ** 2 + 0.05 * t ** 2,
    keel: () => 0,
    decked: false,
  },
  bark_canoe: {
    depthOf: (f) => f.draft + f.freeboard,
    halfB: (t) => Math.sin(Math.PI * (0.04 + 0.92 * t)) ** 1.1,
    stern: 0,                            // double-ended
    sheer: (t) => 1 + 0.5 * (1 - t) ** 3 + 0.5 * t ** 3,   // the swept ends
    keel: (t) => 0.10 * ((1 - t) ** 3 + t ** 3),
    decked: false,
  },
};

/**
 * Loft one hull and its furniture. `baseY` is the world height of the midship
 * keel; the caller has already decided it from the water plane or the ground.
 * Returns the hull's rough deck corners in local ENU (for beached keep-outs).
 */
function pushHull(buf, boat, form, f, baseY, level) {
  const [E, N] = boat.position_local_enu_m;
  const rad = ((boat.heading_deg ?? 0) * Math.PI) / 180;
  const ue = Math.cos(rad); const un = Math.sin(rad);   // along, bow first
  const ve = -un; const vn = ue;                         // to port
  const L = f.length; const halfBeam = f.beam / 2;
  const depth = form.depthOf(f);

  /** A hull-frame point (x along from bow at t, b to port, y above keel) in world. */
  const P = (t, b, y) => {
    const along = (0.5 - t) * L;
    const e = E + ue * along + ve * b;
    const n = N + un * along + vn * b;
    return [wx(e), baseY + y, wz(n)];
  };

  // stations
  const st = [];
  for (let i = 0; i <= STATIONS; i += 1) {
    const t = i / STATIONS;
    let w = form.halfB(t) * halfBeam;
    if (form.stern > 0 && t === 1) w = form.stern * halfBeam;
    if (form.stern === 0 && (t === 0 || t === 1)) w = 0;
    if (t === 0) w = 0;
    st.push({
      t,
      w,
      keelY: form.keel(t) * depth,
      sheerY: form.sheer(t) * depth,
    });
  }

  for (let i = 0; i < STATIONS; i += 1) {
    const a = st[i]; const b = st[i + 1];
    const chin = (s) => ({ w: s.w * CHINE_W, y: s.keelY + CHINE_H * depth });
    const ca = chin(a); const cb = chin(b);
    // bottom, keel to chine, both sides
    pushQuad(buf, P(a.t, 0, a.keelY), P(b.t, 0, b.keelY),
      P(b.t, cb.w, cb.y), P(a.t, ca.w, ca.y), level);
    pushQuad(buf, P(a.t, -ca.w, ca.y), P(b.t, -cb.w, cb.y),
      P(b.t, 0, b.keelY), P(a.t, 0, a.keelY), level);
    // topsides, chine to gunwale
    pushQuad(buf, P(a.t, ca.w, ca.y), P(b.t, cb.w, cb.y),
      P(b.t, b.w, b.sheerY), P(a.t, a.w, a.sheerY), level);
    pushQuad(buf, P(a.t, -a.w, a.sheerY), P(b.t, -b.w, b.sheerY),
      P(b.t, -cb.w, cb.y), P(a.t, -ca.w, ca.y), level);
  }

  const stern = st[STATIONS];
  if (stern.w > 0.01) {
    // the transom
    const c = { w: stern.w * CHINE_W, y: stern.keelY + CHINE_H * depth };
    pushQuad(buf, P(1, -stern.w, stern.sheerY), P(1, stern.w, stern.sheerY),
      P(1, c.w, c.y), P(1, -c.w, c.y), level);
    pushTri(buf, P(1, -c.w, c.y), P(1, c.w, c.y), P(1, 0, stern.keelY), level);
  }

  if (form.decked) {
    // the deck, a hand under the sheer so the bulwark reads
    const dy = -0.22;
    for (let i = 0; i < STATIONS; i += 1) {
      const a = st[i]; const b = st[i + 1];
      pushQuad(buf, P(a.t, -a.w, a.sheerY + dy), P(b.t, -b.w, b.sheerY + dy),
        P(b.t, b.w, b.sheerY + dy), P(a.t, a.w, a.sheerY + dy), level);
    }
  } else {
    // the sole of an open boat, so it does not read as a bottomless shell
    const dy = CHINE_H * depth + 0.04;
    for (let i = 0; i < STATIONS; i += 1) {
      const a = st[i]; const b = st[i + 1];
      const aw = a.w * CHINE_W; const bw = b.w * CHINE_W;
      pushQuad(buf, P(a.t, -aw, a.keelY + dy), P(b.t, -bw, b.keelY + dy),
        P(b.t, bw, b.keelY + dy), P(a.t, aw, a.keelY + dy), level);
    }
    // thwarts
    for (const t of boat.type === 'bark_canoe' ? [0.3, 0.7] : [0.38, 0.72]) {
      const w = form.halfB(t) * halfBeam * 0.92;
      const y = baseY + form.sheer(t) * depth - 0.12;
      const along = (0.5 - t) * L;
      pushBox(buf, wx(E + ue * along), y, wz(N + un * along),
        ve, -vn, w, 0.12, 0.02, level);
    }
  }

  if (boat.type === 'schooner') {
    // two masts, raked aft; a bowsprit; the main boom stowed over the deck.
    const deckY = (t) => baseY + form.sheer(t) * depth - 0.22;
    for (const [t, h] of [[0.30, f.mast * 0.94], [0.62, f.mast]]) {
      const along = (0.5 - t) * L;
      const rake = 0.05 * h;             // the head falls this far aft
      const steps = 3;
      for (let s = 0; s < steps; s += 1) {
        const y0 = s / steps; const y1 = (s + 1) / steps;
        const cy = deckY(t) + ((y0 + y1) / 2) * h;
        const ca = along - rake * ((y0 + y1) / 2);
        const side = MAST_SIDE_M * (1 - 0.5 * ((y0 + y1) / 2));
        pushBox(buf, wx(E + ue * ca), cy, wz(N + un * ca),
          ue, -un, side / 2, side / 2, (h / steps) / 2, level);
      }
    }
    const tipY = baseY + form.sheer(0) * depth + 0.9;
    const rootA = 0.5 * L - 0.6;
    pushBox(buf, wx(E + ue * (rootA + BOWSPRIT_M / 2)),
      (deckY(0.04) + 0.35 + tipY) / 2,
      wz(N + un * (rootA + BOWSPRIT_M / 2)),
      ue, -un, BOWSPRIT_M / 2, 0.09, 0.09, level);
    // the main boom, stowed: from the mainmast aft over the transom
    const boomT = 0.62;
    const boomC = (0.5 - boomT) * L - 3.4;
    pushBox(buf, wx(E + ue * boomC), deckY(boomT) + 1.9, wz(N + un * boomC),
      ue, -un, 3.4, 0.08, 0.08, level);
  }

  // rough plan rectangle, for keep-outs and the pick spans
  const he = ue * (L / 2); const hn = un * (L / 2);
  const be = ve * halfBeam; const bn = vn * halfBeam;
  return [
    [E + he + be, N + hn + bn], [E + he - be, N + hn - bn],
    [E - he - be, N - hn - bn], [E - he + be, N - hn + bn],
  ];
}

/* -------------------------------------------------------------------------- */
/* placement — what the record claims, held against the committed terrain      */
/* -------------------------------------------------------------------------- */

function keelSamples(boat, length) {
  const [E, N] = boat.position_local_enu_m;
  const rad = ((boat.heading_deg ?? 0) * Math.PI) / 180;
  const ue = Math.cos(rad); const un = Math.sin(rad);
  return [-0.5, -0.25, 0, 0.25, 0.5].map((t) => [E + ue * t * length, N + un * t * length]);
}

/**
 * Why this boat cannot be drawn, or null if it can. The reasons are the
 * record's own rules — the refusal is data speaking, not the renderer editing.
 */
function refusalFor(boat, f, terrain, clearance) {
  const pts = keelSamples(boat, f.length);
  if (boat.state === 'beached') {
    const [E, N] = boat.position_local_enu_m;
    const g = terrain.surfaceHeight(E, N);
    if (!Number.isFinite(g)) return 'no modelled ground under a beached hull';
    if (g < -0.6) return `beached on open water (ground ${g.toFixed(2)} m)`;
    if (g > 1.5) return `beached on the prairie (ground ${g.toFixed(2)} m), not at the water`;
    const nearWater = [[8, 0], [-8, 0], [0, 8], [0, -8], [6, 6], [-6, 6], [6, -6], [-6, -6]]
      .some(([de, dn]) => terrain.isWater(E + de, N + dn));
    if (!nearWater) return 'no water within 8 m of a beached hull';
    return null;
  }
  for (const [e, n] of pts) {
    if (!terrain.isWater(e, n)) return `afloat over dry ground at (${e.toFixed(0)}, ${n.toFixed(0)})`;
    const bed = terrain.surfaceHeight(e, n);
    if (!Number.isFinite(bed)) return 'afloat off the modelled ground';
    const depth = WATER_Y - bed;
    if (depth < f.draft + UNDER_KEEL_M) {
      return `${depth.toFixed(2)} m of water for a ${f.draft.toFixed(2)} m draft `
        + `at (${e.toFixed(0)}, ${n.toFixed(0)})`;
    }
  }
  for (const [e, n] of pts) {
    if (n < MAIN_STEM_N_MAX && Math.abs(e - DRAWBRIDGE_E) < clearance) {
      return `inside the drawbridge's ${clearance} m navigation clearance`;
    }
  }
  return null;
}

/* -------------------------------------------------------------------------- */
/* the card — a boat is not a structure, so it carries its own                 */
/* -------------------------------------------------------------------------- */

const SYMBOLIC = {
  moored: 'Moored in the open reach',
  beached: 'Drawn up at the bank',
};

/** A registry-shaped record for `popup.show()`, built from the boat's own
 *  claims. Every attribute keeps its confidence, note and (empty) source list
 *  — the card renders the same partition it renders for a building: nothing
 *  attested, nothing inferred, everything reconstructed and saying what
 *  bounded it. */
function cardRecordFor(boat, record, f) {
  const form = record.form?.[boat.type] ?? {};
  const attributes = {
    type: {
      value: boat.type, confidence: 'reconstructed', sources: [],
      note: 'The TYPE is the era claim: schooners were the lake carriers, skiffs '
        + 'the working small boats, bark canoes the craft of the trade. See the '
        + 'record’s existence note for what the engravings show.',
    },
    state: {
      value: boat.state, confidence: 'reconstructed', sources: [],
      note: boat.state === 'beached'
        ? 'Hauled out: the hull sits on the terrain’s own surface, sampled at load.'
        : 'Riding the water plane at its own draft. Unmanned and unrigged for sea — '
          + 'no crew, no set sails, no name.',
    },
  };
  for (const key of ['length_m', 'beam_m', 'draft_m', 'mast_height_m', 'freeboard_m']) {
    if (form[key]) attributes[key] = form[key];
  }
  return {
    id: boat.id,
    sidecar: {
      name: boat.name ?? boat.id,
      phase: null,
      placement: {
        symbolic_location: boat.symbolic_location
          ?? SYMBOLIC[boat.state] ?? 'On the river',
        position_confidence: 'reconstructed',
        position_sources: [],
        position_note: boat.note ?? 'Invented position; see data/boats/.',
      },
      attributes,
      citations: [],
      research_note: 'A boat from data/boats/ — not a structure record. '
        + (record.existence?.note ?? '')
        + (boat.type === 'bark_canoe' && record.existence?.standing_constraint_note
          ? ` ${record.existence.standing_constraint_note}` : '')
        + ' The invention is claimed at docs/LIBERTIES.md L146.',
    },
  };
}

/* -------------------------------------------------------------------------- */
/* the layer                                                                   */
/* -------------------------------------------------------------------------- */

async function getJSON(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`);
  return res.json();
}

/** One type's figures, read once so no draw reaches into the JSON. */
function readForm(record, type) {
  const f = record.form?.[type] ?? {};
  const v = (k, fallback) => (f[k]?.value ?? fallback);
  return {
    length: v('length_m', 5),
    beam: v('beam_m', 1.5),
    draft: v('draft_m', 0.3),
    freeboard: v('freeboard_m', 0.5),
    mast: v('mast_height_m', 0),
  };
}

/**
 * @param {object} o dataBase (data/ root) · terrain · confidence · problems
 * @returns {Promise<{group: THREE.Group, records: object[], boats: object[],
 *                    keepOut: object[], census: object, pickAt: function,
 *                    dispose: function}>}
 */
export async function createBoats({
  dataBase, terrain, confidence = null, problems = [],
} = {}) {
  const group = new THREE.Group();
  group.name = 'boats';
  const out = {
    group,
    records: [],
    boats: [],
    /** Beached hulls as planting keep-outs, in `footprintsFrom()`'s shape —
     *  sward growing up through a hauled-out skiff reads as a hole in the
     *  model. Afloat hulls need none: nothing plants on water. */
    keepOut: [],
    census: {
      records: 0, boats: 0, schooners: 0, rowboats: 0, canoes: 0, refused: 0,
    },
    pickAt: () => null,
    dispose: () => {},
  };

  if (!dataBase || !terrain) {
    problems.push('boats: no data base or no terrain — no boat is drawn');
    return out;
  }
  let index;
  try {
    index = await getJSON(new URL('boats/index.json', dataBase));
  } catch (err) {
    // Degrade to NOTHING drawn plus a recorded problem, never to an invented
    // hull: the same contract every derived layer keeps.
    problems.push(`boats: ${err.message} — no boat is drawn`);
    return out;
  }
  const wanted = Array.isArray(index.boats) ? index.boats : [];
  const loaded = await Promise.all(wanted.map(async (b) => {
    if (!b.file) return [b.id, null, 'the manifest gave no file'];
    try {
      return [b.id, await getJSON(new URL(`boats/${b.file}`, dataBase)), null];
    } catch (err) { return [b.id, null, err.message]; }
  }));

  const buf = { pos: [], nrm: [], conf: [] };
  /** Which boat a triangle belongs to — the same span table `wharves.js`,
   *  `signage.js` and `yard.js` keep, and for the same reason. */
  const spans = [];
  const cards = new Map();
  const TYPE_COUNT = { schooner: 'schooners', rowboat: 'rowboats', bark_canoe: 'canoes' };

  for (const [id, record, why] of loaded) {
    if (!record) { problems.push(`boats: ${id} — ${why}`); continue; }
    out.records.push(record);
    out.census.records += 1;
    const clearance = record.clearances?.drawbridge_span_m?.value ?? 30;
    for (const boat of record.boats ?? []) {
      const form = HULL_FORMS[boat.type];
      if (!form) {
        problems.push(`boats: ${boat.id} has unknown type '${boat.type}' — not drawn`);
        out.census.refused += 1;
        continue;
      }
      const f = readForm(record, boat.type);
      const refusal = refusalFor(boat, f, terrain, clearance);
      if (refusal) {
        problems.push(`boats: ${boat.id} refused — ${refusal}`);
        out.census.refused += 1;
        continue;
      }
      const [E, N] = boat.position_local_enu_m;
      const baseY = boat.state === 'beached'
        ? terrain.surfaceHeight(E, N)
        : WATER_Y - f.draft;
      const level = LEVEL[boat.confidence] ?? 1;
      const from = buf.pos.length / 9;
      const plan = pushHull(buf, boat, form, f, baseY, level);
      spans.push({ id: boat.id, from, to: buf.pos.length / 9 });
      if (boat.state === 'beached') out.keepOut.push({ id: `${boat.id}__hull`, pts: plan });
      boat._drawn = {
        keel_y_m: baseY,
        afloat: boat.state !== 'beached',
        vertices: buf.pos.length / 3 - from * 3,
      };
      cards.set(boat.id, cardRecordFor(boat, record, f));
      out.boats.push(boat);
      out.census.boats += 1;
      out.census[TYPE_COUNT[boat.type]] += 1;
    }
  }
  if (!buf.pos.length) {
    if (out.census.records) problems.push('boats: the record loaded and not one boat was drawn');
    return out;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(buf.pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(buf.nrm, 3));
  geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(buf.conf, 1));
  geo.computeBoundingSphere();

  const mat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(BOAT_COLOUR),
    roughness: 0.9,
    metalness: 0.0,
    side: THREE.DoubleSide,   // an open hull shows its inside
  });
  mat.name = 'boat-timber';
  confidence?.patch(mat);
  // Its own program cache key — the T-0053 hazard: two patched materials that
  // agree on their other parameters share one compiled program, silently.
  mat.customProgramCacheKey = () => 'chicago4d-boat-timber';

  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = 'boats';
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);
  group.userData.census = out.census;

  const raycaster = new THREE.Raycaster();
  /** The boat under the crosshair, with its own card record. */
  out.pickAt = (ndc, camera) => {
    if (!camera) return null;
    raycaster.setFromCamera(ndc ?? new THREE.Vector2(0, 0), camera);
    raycaster.far = Math.max(400, camera.position.y * 4);
    const hits = raycaster.intersectObject(mesh, false);
    if (!hits.length) return null;
    const hit = hits[0];
    const span = spans.find((sp) => hit.faceIndex >= sp.from && hit.faceIndex < sp.to);
    if (!span) return null;
    return {
      id: span.id,
      record: cards.get(span.id) ?? null,
      point: hit.point.clone(),
      distance: hit.distance,
    };
  };

  out.dispose = () => { geo.dispose(); mat.dispose(); };
  return out;
}
