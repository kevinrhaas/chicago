/**
 * wells.js — the well heads this project can place to a coordinate, drawn from a
 * point instead of a footprint (T-0887).
 *
 * WHY THIS FILE EXISTS. The 1830 Harrison plan draws a small ring on Fort
 * Dearborn's outer ground and letters it `Well`; Gurdon Hubbard, independently
 * and from memory, puts the fort's well *"in the outer inclosure and near the
 * south gate"*. T-0881 measured the ring — local east 1152.50, north 139.53,
 * all but exactly due south of the enclosure's centre — and then could not do
 * anything with the measurement, for a reason that is worth stating in full
 * because it is the whole argument for this layer: `data/structures.schema.json`
 * offers twelve archetypes and none of them is a well. The nearest,
 * `outbuilding`, builds a walled and roofed shed, and a shed is not a well head.
 * A structure record with no buildable form does not validate, so the fort's
 * well could not even be carried as an EVIDENCE record the way the estray pen
 * is — the pen has `data/enclosures/` and `enclosures.js` behind it, and there
 * was no equivalent here. The reading sat in `docs/RESEARCH/wells.md` § 5 with
 * nothing to attach it to.
 *
 * This is that equivalent, and it is the same argument one layer over: a curb is
 * a ring of low timber standing on the committed heightfield, so it is built at
 * load from committed numbers — no GLB, no `assets/`, no nightly, no archetype.
 *
 * WHAT IT WILL AND WILL NOT DO.
 *
 *  * IT MINTS NO WELLS. T-0592 refused a well CLASS for the town and that
 *    refusal stands in full: wells attach to houses everywhere, so drawing one
 *    unplaced well is a statement about all the others. What this layer draws is
 *    a PLACE — a well a source puts at a coordinate — and it enforces that
 *    mechanically rather than by good intentions: a well whose
 *    `position_confidence` is not `documented` or `attested` is REFUSED, with
 *    the reason recorded as a problem. The refusal is the point of the guard; it
 *    is what stops a future record quietly distributing well heads across the
 *    South Division.
 *  * IT DRAWS A CURB AND NOTHING MORE. No windlass, no sweep, no rope, no
 *    bucket and no roof. Water is got out of a well by one of those three
 *    mechanisms, they look completely different from one another, and no source
 *    reached says which stood here — so choosing one would be the largest
 *    invention on the record and the most visible thing in the scene. The
 *    residual is stated on the record (`lifting_gear`) rather than hidden.
 *  * THE CURB ITSELF IS INVENTED, all of it — plan, diameter, height, thickness
 *    and material — and `docs/LIBERTIES.md` L234 claims it. The plate's ring is
 *    a POINT SYMBOL: its 14 px would be 4.7 m, no well at this fort was four and
 *    a half metres across, and the record refuses to take any dimension from it.
 *  * IT DRAPES. The rim's ground line is `terrain.surfaceHeight()` at the well's
 *    own point, sampled at load — the bridge's lesson (T-0001) again: no height
 *    here is authored beside the mesh.
 *  * IT REFUSES WATER. A well head whose foot is under the river mask is dropped,
 *    the way `trees.js` refuses a stem below the waterline and `enclosures.js`
 *    refuses a post. A well standing in the river would be a claim about a
 *    shoreline this layer knows nothing of.
 *  * IT MARKS ITSELF. Every vertex carries `_confidence` at `reconstructed`, so
 *    the whole well disappears when a visitor hides that tier and the fort's
 *    outer ground goes honestly blank again. The POSITION is documented and the
 *    FABRIC is not, and the confidence view is how a visitor is told the
 *    difference.
 *  * IT ANSWERS A PICK. A well belongs to no structure, so aiming at one opens a
 *    card built from the well's OWN record — the same arrangement the boats keep
 *    (T-0063): where it is, what is read, and what was invented to draw it.
 */

import * as THREE from 'three';

/** attested · documented · inferred · reconstructed, as the confidence view reads them. */
const LEVEL = { attested: 0, documented: 0, inferred: 0.5, reconstructed: 1 };

/** A position this layer will draw. Anything else is a distribution, not a place. */
const PLACED = new Set(['documented', 'attested']);

/** Segments round the curb. Twenty reads round at arm's length and costs 120
 *  triangles for the one well in the dataset — a rounding error against the
 *  fence layer's 104,916 at `balanced`, so there is no detail tier here. */
const SEGMENTS = 20;

/** Curb timber, the same weathered grey-brown the boats and the fences use. */
const CURB_COLOUR = 0x7a7060;

/** The shaft mouth: near-black, unlit-looking, and no claim about water. */
const SHAFT_COLOUR = 0x0e0c0a;

const wx = (e) => e;
const wz = (n) => -n;

/** A triangle, with its confidence level on every vertex. */
function pushTri(buf, a, b, c, level) {
  const ux = b[0] - a[0]; const uy = b[1] - a[1]; const uz = b[2] - a[2];
  const vx = c[0] - a[0]; const vy = c[1] - a[1]; const vz = c[2] - a[2];
  let nx = uy * vz - uz * vy;
  let ny = uz * vx - ux * vz;
  let nz = ux * vy - uy * vx;
  const len = Math.hypot(nx, ny, nz) || 1;
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

/**
 * One curb: an annular wall of `SEGMENTS` facets — outer face, inner face and
 * the rim between them — standing on the terrain at the record's own point.
 * Returns the plan ring, which is the layer's planting keep-out.
 */
function pushCurb(buf, well, f, baseY, level) {
  const [E, N] = well.position_local_enu_m;
  const rOut = f.outer / 2;
  const rIn = f.mouth / 2;
  const top = baseY + f.height;
  // The curb is buried a little so no gap shows where the ground falls away
  // under it; a rim that floats is a worse artefact than one set too deep.
  const foot = baseY - 0.15;
  const plan = [];

  for (let i = 0; i < SEGMENTS; i += 1) {
    const a = (i / SEGMENTS) * Math.PI * 2;
    const b = ((i + 1) / SEGMENTS) * Math.PI * 2;
    const ca = Math.cos(a); const sa = Math.sin(a);
    const cb = Math.cos(b); const sb = Math.sin(b);

    const oa = [wx(E + ca * rOut), 0, wz(N + sa * rOut)];
    const ob = [wx(E + cb * rOut), 0, wz(N + sb * rOut)];
    const ia = [wx(E + ca * rIn), 0, wz(N + sa * rIn)];
    const ib = [wx(E + cb * rIn), 0, wz(N + sb * rIn)];
    plan.push([E + ca * rOut, N + sa * rOut]);

    // outer face, seen from outside
    pushQuad(buf,
      [oa[0], foot, oa[2]], [ob[0], foot, ob[2]],
      [ob[0], top, ob[2]], [oa[0], top, oa[2]], level);
    // inner face, seen from over the rim
    pushQuad(buf,
      [ib[0], foot, ib[2]], [ia[0], foot, ia[2]],
      [ia[0], top, ia[2]], [ib[0], top, ib[2]], level);
    // the rim itself
    pushQuad(buf,
      [oa[0], top, oa[2]], [ob[0], top, ob[2]],
      [ib[0], top, ib[2]], [ia[0], top, ia[2]], level);
  }
  return plan;
}

/**
 * The shaft mouth — a disc under the rim, so the curb reads as an opening rather
 * than as a ring of timber laid on unbroken sward. Its depth is the record's own
 * `shaft_draw_depth_m`, which the record grades as a drawing device and NOT as a
 * claim about how deep the well was or where its water stood.
 */
function pushShaft(buf, well, f, baseY, level) {
  const [E, N] = well.position_local_enu_m;
  const r = f.mouth / 2;
  const y = baseY - f.shaftDepth;
  const centre = [wx(E), y, wz(N)];
  for (let i = 0; i < SEGMENTS; i += 1) {
    const a = (i / SEGMENTS) * Math.PI * 2;
    const b = ((i + 1) / SEGMENTS) * Math.PI * 2;
    pushTri(buf, centre,
      [wx(E + Math.cos(b) * r), y, wz(N + Math.sin(b) * r)],
      [wx(E + Math.cos(a) * r), y, wz(N + Math.sin(a) * r)], level);
  }
}

/** Why this well is not drawn, or null. Refusals are recorded, never nudged. */
function refusalFor(well, terrain) {
  const pos = well.position_local_enu_m;
  if (!Array.isArray(pos) || pos.length !== 2
      || !Number.isFinite(pos[0]) || !Number.isFinite(pos[1])) {
    return 'it carries no position_local_enu_m this layer can read';
  }
  if (!PLACED.has(well.position_confidence)) {
    return `its position is graded '${well.position_confidence ?? 'nothing'}' — this `
      + 'layer draws a well a source PLACES and refuses to mint one, because T-0592 '
      + 'refused a well class for this town and one unplaced well is a claim about '
      + 'every house that had one';
  }
  if (terrain.isWater?.(pos[0], pos[1])) {
    return 'its foot is in the water mask — a well standing in the river would be a '
      + 'claim about a shoreline this layer knows nothing of';
  }
  return null;
}

async function getJSON(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`);
  return res.json();
}

/** The record's figures, read once so no draw reaches into the JSON. */
function readForm(record) {
  const f = record.form ?? {};
  const v = (k, fallback) => (f[k]?.value ?? fallback);
  const outer = v('curb_outer_diameter_m', 1.10);
  const wall = v('curb_thickness_m', 0.10);
  return {
    outer,
    mouth: v('shaft_mouth_m', Math.max(0.3, outer - wall * 2)),
    height: v('curb_height_m', 0.60),
    wall,
    shaftDepth: v('shaft_draw_depth_m', 0.25),
    material: v('curb_material', 'timber'),
    plan: v('curb_plan', 'round'),
  };
}

/** The card a visitor opens by aiming at the curb. */
function cardRecordFor(well, record, f) {
  const form = record.form ?? {};
  const attributes = {};
  for (const key of ['curb_plan', 'curb_outer_diameter_m', 'curb_height_m',
    'curb_thickness_m', 'curb_material', 'shaft_mouth_m', 'shaft_draw_depth_m']) {
    if (form[key]) attributes[key] = form[key];
  }
  if (record.plate_symbol) attributes.plate_symbol = record.plate_symbol;
  if (record.lifting_gear) attributes.lifting_gear = record.lifting_gear;
  return {
    id: well.id,
    sidecar: {
      name: well.name ?? record.name ?? well.id,
      phase: null,
      placement: {
        local_e: well.position_local_enu_m[0],
        local_n: well.position_local_enu_m[1],
        symbolic_location: well.symbolic_location ?? 'On the fort’s outer ground.',
        position_confidence: well.position_confidence ?? 'documented',
        position_sources: well.position_sources ?? [],
        position_note: well.position_note ?? '',
        uncertainty_m: well.uncertainty_m ?? null,
        vertical_anchor: 'terrain',
      },
      attributes,
      citations: [],
      documented_range: record.documented_range ?? null,
      research_note: 'A well from data/wells/ — not a structure record, because this '
        + 'project has no well archetype and a record with no buildable form does not '
        + 'validate. The POSITION is documented and the FABRIC is not: '
        + (record.research_note ?? ''),
    },
  };
}

/**
 * @param {object} o dataBase (data/ root) · terrain · confidence · problems
 * @returns {Promise<{group: THREE.Group, records: object[], wells: object[],
 *                    keepOut: object[], census: object, pickAt: function,
 *                    dispose: function}>}
 */
export async function createWells({
  dataBase, terrain, confidence = null, problems = [],
} = {}) {
  const group = new THREE.Group();
  group.name = 'wells';
  const out = {
    group,
    records: [],
    wells: [],
    /** The curb as a planting keep-out — sward growing up through a well head
     *  reads as a hole in the model, the same argument the beached hulls make. */
    keepOut: [],
    census: { records: 0, wells: 0, refused: 0 },
    pickAt: () => null,
    dispose: () => {},
  };

  if (!dataBase || !terrain) {
    problems.push('wells: no data base or no terrain — no well is drawn');
    return out;
  }
  let index;
  try {
    index = await getJSON(new URL('wells/index.json', dataBase));
  } catch (err) {
    // Degrade to NOTHING drawn plus a recorded problem, never to an invented
    // well: the same contract every derived layer here keeps.
    problems.push(`wells: ${err.message} — no well is drawn`);
    return out;
  }
  const wanted = Array.isArray(index.wells) ? index.wells : [];
  const loaded = await Promise.all(wanted.map(async (w) => {
    if (!w.file) return [w.id, null, 'the manifest gave no file'];
    try {
      return [w.id, await getJSON(new URL(`wells/${w.file}`, dataBase)), null];
    } catch (err) { return [w.id, null, err.message]; }
  }));

  const buf = { pos: [], nrm: [], conf: [] };
  const shaftBuf = { pos: [], nrm: [], conf: [] };
  /** Which well a triangle belongs to — the same span table `boats.js`,
   *  `wharves.js` and `signage.js` keep, and for the same reason. */
  const spans = [];
  const cards = new Map();

  for (const [id, record, why] of loaded) {
    if (!record) { problems.push(`wells: ${id} — ${why}`); continue; }
    out.records.push(record);
    out.census.records += 1;
    const f = readForm(record);
    for (const well of record.wells ?? []) {
      const refusal = refusalFor(well, terrain);
      if (refusal) {
        problems.push(`wells: ${well.id} refused — ${refusal}`);
        out.census.refused += 1;
        continue;
      }
      const [E, N] = well.position_local_enu_m;
      const baseY = terrain.surfaceHeight(E, N);
      // The FABRIC is reconstructed even where the PLACE is documented, and the
      // vertex grade is the fabric's: hiding `reconstructed` must take this curb
      // away, because nothing attests a single dimension of it.
      const level = LEVEL[well.confidence] ?? 1;
      const from = buf.pos.length / 9;
      const plan = pushCurb(buf, well, f, baseY, level);
      spans.push({ id: well.id, from, to: buf.pos.length / 9 });
      pushShaft(shaftBuf, well, f, baseY, level);
      out.keepOut.push({ id: `${well.id}__curb`, pts: plan });
      well._drawn = { ground_y_m: baseY, rim_y_m: baseY + f.height };
      cards.set(well.id, cardRecordFor(well, record, f));
      out.wells.push(well);
      out.census.wells += 1;
    }
  }
  if (!buf.pos.length) {
    if (out.census.records) problems.push('wells: the record loaded and not one well was drawn');
    return out;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(buf.pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(buf.nrm, 3));
  geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(buf.conf, 1));
  geo.computeBoundingSphere();

  const mat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(CURB_COLOUR),
    roughness: 0.92,
    metalness: 0.0,
    side: THREE.DoubleSide,   // a ring shows its inside over the rim
  });
  mat.name = 'well-curb';
  confidence?.patch(mat);
  // Its own program cache key — the T-0053 hazard: two patched materials that
  // agree on their other parameters share one compiled program, silently.
  mat.customProgramCacheKey = () => 'chicago4d-well-curb';

  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = 'wells';
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);

  const shaftGeo = new THREE.BufferGeometry();
  shaftGeo.setAttribute('position', new THREE.Float32BufferAttribute(shaftBuf.pos, 3));
  shaftGeo.setAttribute('normal', new THREE.Float32BufferAttribute(shaftBuf.nrm, 3));
  shaftGeo.setAttribute('_confidence', new THREE.Float32BufferAttribute(shaftBuf.conf, 1));
  shaftGeo.computeBoundingSphere();
  const shaftMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(SHAFT_COLOUR), roughness: 1.0, metalness: 0.0,
  });
  shaftMat.name = 'well-shaft';
  confidence?.patch(shaftMat);
  shaftMat.customProgramCacheKey = () => 'chicago4d-well-shaft';
  const shaftMesh = new THREE.Mesh(shaftGeo, shaftMat);
  shaftMesh.name = 'well-shafts';
  // The disc takes no shadow pass: it is already the darkest thing in the scene
  // and a second draw of it buys nothing.
  shaftMesh.castShadow = false;
  shaftMesh.receiveShadow = true;
  group.add(shaftMesh);

  group.userData.census = out.census;

  const raycaster = new THREE.Raycaster();
  /** The well under the crosshair, with its own card record. */
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

  out.dispose = () => {
    geo.dispose(); mat.dispose(); shaftGeo.dispose(); shaftMat.dispose();
  };
  return out;
}
