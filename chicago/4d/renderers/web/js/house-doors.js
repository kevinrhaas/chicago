/**
 * house-doors.js — a house's front door hung to swing, and the way up its steps (T-3442).
 *
 * The owner, 2026-11-07: *"maybe interacting at the front door of buildings would allow you
 * to ask for someone to come to the door and then they can come to the door and open it and
 * interact with you ... you will need to be able to handle steps and allowing people to
 * interact and walk up the steps to the door"*. This is the foundation that asks for: one
 * door that opens on its hinges, a visitor who can climb to it, and a path a drawn person
 * can walk from the sidewalk up the steps to just inside it. Calling at the door and the
 * person who answers it are later work, and drive what this module hands them.
 *
 * WHICH DOOR. Glessner House's front door, on Prairie Avenue. Richardson's office titled
 * the leaf's sheet "Main Entrance Door" (No. 95, `artic_glessner_sheet_95_main_entrance_door`)
 * and drew 1800 in its grille; the record carries it as `openings_prairie` → "front door".
 * The great arch on 18th Street is a recessed porch to a stair and a side door
 * (`v4_detail.north_entry_alcove`); it is not this door.
 *
 * WHAT IS THE RECORD'S, read here exactly as the generator builds it (masonry_house_params.py
 * frame, masonry_house_v4_front_door.py leaf, masonry_house_v4_entry.py threshold):
 *   - the doorway, S 30.4-35.4 by 7.50 ft over the door datum (`openings_prairie`), its sill
 *     0.74 ft over the walk (`frame_ft`);
 *   - the leaf, inset 0.025 m in the opening and standing 0.246-0.305 m behind the wall face;
 *   - the threshold, 0.6 ft proud of the face to 0.95 ft inside it, 9.1 ft wide
 *     (`v4_detail.prairie_entry`), at the sill;
 *   - the approach paving between the lawns, S 28.1-37.7 out to the walk join
 *     (`prairie_frontage`), at its 0.21 ft over north grade.
 *
 * WHAT IS OURS, docs/LIBERTIES.md L-glessner-front-door-swing-3442: that the leaf is hung on
 * its north (right-hand) jamb — inferred, because sheet 95 puts the latch plate and drop ring
 * at its left end and a latch is on the free edge; that it swings inward, through 90 degrees,
 * in 1.6 s; and the dark vestibule behind it, 1.9 m deep, which nothing records (HABS draws
 * the hall, not its finish) and which is there so the opening reads as a room, never as
 * daylight through the house.
 *
 * HOW IT IS DRAWN. The baked leaf is the photo-matched one, so it is not redrawn: the
 * buildings layer lifts its triangles (oak, iron, the grille's pane) out of the structure's
 * batch as it loads (`takeDoorLeaf`, buildings.js) and this layer hangs them on a pivot at
 * the hinge. Shut, the door is the triangles it always was; open, they have turned.
 *
 * HOW IT IS WALKED (walker.js § doorways). Three things:
 *   - the steps are DECKS — the approach paving and the threshold, each at the height it is
 *     drawn — so the walker's own step rule climbs them (and its step ease smooths them);
 *   - the footprint gets a DOORWAY: inside a small zone round the door, the walker reads an
 *     outline with the doorway's reveal cut into the façade (to the leaf while it is shut,
 *     on into the vestibule while it is open), so a visitor can stand on the threshold at
 *     the leaf, and through it once it is open;
 *   - Interact (interact.js) offers the door within DOOR_REACH_M on foot: Open door, Close
 *     door. Close is refused while someone stands where the leaf would swing.
 *
 * THE API LATER WORK CALLS (main.js exposes it as `api.houseDoors`):
 *   houseDoors.open(id) / close(id)     start the swing (through interact.js); { ok, why }
 *   houseDoors.get(id)                  the door thing: state 'closed' | 'open', running
 *   houseDoors.path(id, { from, inside, groundAt })
 *                                       [{ e, n, y }] local ENU metres and world height,
 *                                       from the sidewalk up every tread to `inside` metres
 *                                       past the leaf, a rise eased over each riser; reverse
 *                                       it to come out. `path.outward` is the bearing that
 *                                       faces the street.
 *   actor.walkPath(points, { endHeading, onArrive })   humans.js: a person walks it.
 */
import * as THREE from 'three';
import { footprintToWorld } from './walker.js';

/** The doors a visitor works, per structure. Only these. */
export const HOUSE_DOORS = Object.freeze({
  glessner_house: { front: 'Front door' },
});

/** How far the leaf swings from shut, and how long it takes. Ours (the header). */
export const DOOR_OPEN_DEG = 90;
export const DOOR_SWING_S = 1.6;
/** Within this far of the door, on foot, the Interact key offers it. */
export const DOOR_REACH_M = 3.5;
/** The dark vestibule behind the leaf: how deep, and how far its ceiling clears the head. */
export const VESTIBULE_DEPTH_M = 1.9;
const VESTIBULE_HEADROOM_M = 0.5;
/** The doorway zone reaches this far round the door, so the walker's notched outline and
 *  the plain one agree everywhere a capsule can touch either (> WALK.radius). */
const ZONE_MARGIN_M = 0.8;
/** Over a riser a path's height rises across this run each side of it, so a figure's feet
 *  step up the tread rather than gliding up a ramp from the last one. */
const RISER_EASE_M = 0.12;
/** Where the path starts: this far out on the public walk past the approach's join (the
 *  middle of Prairie Avenue's six-foot walk, T-1728). */
const SIDEWALK_IN_M = 0.91;

const FT = 0.3048;
// masonry_house_v4_front_door.py: the leaf's back and its border's face, metres behind the
// wall plane, and its inset in the opening (Door.__init__: a + .025, z0 + .02).
const LEAF_BACK_M = 0.305;
const LEAF_FRONT_M = 0.246;
const LEAF_INSET_M = 0.025;
const LEAF_FOOT_M = 0.02;
/** The materials a door leaf is drawn in. The grille's pane is glass; its dark backing,
 *  0.6 m behind the leaf, is dropped (the vestibule is what lies behind the grille now). */
const LEAF_MATERIALS = new Set(['oak', 'iron', 'glass', 'glass_dark']);

/** One of the record's attributes, its value where it is graded ({ value, confidence }). */
function val(sidecar, name, dflt = null) {
  const attrs = sidecar?.attributes ?? {};
  const graded = attrs[name];
  const v = graded && typeof graded === 'object' && !Array.isArray(graded) && 'value' in graded ? graded['value'] : graded;
  return v === undefined || v === null ? dflt : v;
}

/**
 * Glessner's front door in the structure's own frame (metres; plan [u, v], +u east and +v
 * north; heights y over the structure's base, which is the walk), read from its record as
 * masonry_house_params.py frames it. Null when the record does not carry what it needs.
 */
export function glessnerFrontPlan(sidecar) {
  const frame = val(sidecar, 'frame_ft');
  const frontage = val(sidecar, 'prairie_frontage');
  const entry = val(sidecar, 'v4_detail', {})?.['prairie_entry'];
  const items = val(sidecar, 'openings_prairie', {})?.['items'] ?? [];
  const door = items.find((o) => o?.['style'] === 'prairie_front_door');
  if (!frame || !frontage || !entry || !door) return null;
  const L = Number(frame['length_ft']), D = Number(frame['depth_ft']);
  const datums = { door: Number(frame['door_datum_above_grade_ft'] ?? 0),
    ng: Number(val(sidecar, 'grade_datum', {})?.['north_grade_above_grade_ft'] ?? 0) };
  const x = (w) => (L - Number(w)) * FT;            // _Frame.x
  const y = (s) => (D - Number(s)) * FT;            // _Frame.y
  const z = (spec) => (Array.isArray(spec) ? (Number(spec[0]) + datums[spec[1]]) : (Number(spec) + datums.ng)) * FT;
  const face = x(0);                                 // the Prairie face, W 0
  const jambs = door['at'].map(y).sort((a, b) => a - b);
  const [sill, head] = door['z'].map((h) => z([h, 'door']));
  const mid = (jambs[0] + jambs[1]) / 2;
  const recess = Number(entry['recess_base_width_ft']) * FT;
  const tFront = x(entry['threshold_front_W']) - face, tBack = x(entry['threshold_back_W']) - face;
  const entryS = frontage['entry_S'].map(y).sort((a, b) => a - b);
  const join = x(frontage['walk_join_W']) - face;
  return {
    id: 'glessner_house:front',
    structureId: sidecar.id,
    name: HOUSE_DOORS.glessner_house.front,
    // The face's plane and its frame: d outward from the wall, s along it to the right of
    // someone standing outside looking at the door (north, on this east face).
    origin: [face, 0], outward: [1, 0], along: [0, 1],
    jambs, sill, head,
    leaf: { front: -LEAF_FRONT_M, back: -LEAF_BACK_M, s: [jambs[0] + LEAF_INSET_M, jambs[1] - LEAF_INSET_M],
      foot: sill + LEAF_FOOT_M, top: head - LEAF_FOOT_M },
    // Sheet 95's latch is at the leaf's left end, so it hangs on its right (north) jamb.
    hinge: 'right',
    revealBack: tBack,
    treads: [
      { id: 'approach', d: [tFront, join], s: entryS, y: z(frontage['walk_z']) },
      { id: 'threshold', d: [tBack, tFront], s: [mid - recess / 2, mid + recess / 2], y: sill },
    ],
    sidewalk: join + SIDEWALK_IN_M,
    grades: { leaf: 'attested', hinge: 'inferred', swing: 'reconstructed', vestibule: 'reconstructed', treads: 'reconstructed' },
  };
}

/** The door plans a record carries (none for any record not in HOUSE_DOORS). */
export function doorPlansOf(record) {
  if (!record?.sidecar || !HOUSE_DOORS[record.id]) return [];
  if (record.id === 'glessner_house') {
    const plan = glessnerFrontPlan(record.sidecar);
    return plan ? [plan] : [];
  }
  return [];
}

/** A plan point at (d out from the face, s along it) to the structure frame's [u, v]. */
export function planPoint(plan, d, s) {
  return [plan.origin[0] + plan.outward[0] * d + plan.along[0] * s,
    plan.origin[1] + plan.outward[1] * d + plan.along[1] * s];
}

/** The hinge (d, s) and the leaf's direction from it, shut, in (d, s). */
function hingeOf(plan) {
  const right = plan.hinge === 'right';
  return { d: plan.leaf.back, s: right ? plan.leaf.s[1] : plan.leaf.s[0], toFree: right ? -1 : 1,
    width: plan.leaf.s[1] - plan.leaf.s[0] };
}

/**
 * The leaf at swing fraction t (0 shut, 1 open) in (d, s): its hinge, the direction to its
 * free edge, and the direction its outer face looks. Inward is -d.
 */
export function leafPose(plan, t) {
  const h = hingeOf(plan);
  const a = (DOOR_OPEN_DEG * Math.PI / 180) * Math.max(0, Math.min(1, t));
  // Shut the free edge lies along s (toFree); it turns toward -d (into the house).
  const dir = [-Math.sin(a), h.toFree * Math.cos(a)];
  const face = [Math.cos(a), h.toFree * Math.sin(a)];
  return { hinge: [h.d, h.s], dir, face, width: h.width };
}

/**
 * The box (structure frame: x = u, y up, z = -v) the baked leaf stands in, and how deep
 * behind it the pane's backing reaches. buildings.js lifts what lies inside.
 */
export function leafBox(plan) {
  const p0 = planPoint(plan, plan.leaf.back - 0.7, plan.jambs[0] + 0.004);
  const p1 = planPoint(plan, plan.leaf.front + 0.07, plan.jambs[1] - 0.004);
  return {
    x: [Math.min(p0[0], p1[0]), Math.max(p0[0], p1[0])],
    y: [plan.sill + 0.003, plan.head + 0.015],
    z: [-Math.max(p0[1], p1[1]), -Math.min(p0[1], p1[1])],
    // A triangle wholly behind this depth is the pane's backing, not the leaf.
    keepD: plan.leaf.back - 0.05,
  };
}

/**
 * T-3442, called by buildings.js for each of a structure's meshes as it loads: lift a
 * hung door's leaf out of the batch. `matrix` takes the mesh into the structure's frame
 * (metres). The leaf's triangles are cut from the mesh's index and returned as a geometry
 * of their own in that frame; the pane's backing is cut and dropped. Returns
 * [{ doorId, geometry }] (empty for every mesh that has none). Idempotent per geometry.
 */
export function takeDoorLeaf(record, mesh, matrix) {
  const plans = doorPlansOf(record);
  if (!plans.length || !mesh?.geometry) return [];
  const material = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
  if (!LEAF_MATERIALS.has(material?.name)) return [];
  const geo = mesh.geometry;
  if (geo.userData.doorLeaves) return geo.userData.doorLeaves;
  const pos = geo.getAttribute('position');
  if (!pos) return [];
  const index = geo.getIndex();
  const count = index ? index.count : pos.count;
  const at = (i) => (index ? index.getX(i) : i);
  // Every vertex in the structure's frame, once.
  const world = new Float32Array(pos.count * 3);
  const vec = new THREE.Vector3();
  for (let i = 0; i < pos.count; i += 1) {
    vec.fromBufferAttribute(pos, i).applyMatrix4(matrix);
    world[3 * i] = vec.x; world[3 * i + 1] = vec.y; world[3 * i + 2] = vec.z;
  }
  const out = [];
  const lifted = new Uint8Array(count / 3);
  for (const plan of plans) {
    const box = leafBox(plan);
    const inBox = (k) => world[3 * k] >= box.x[0] && world[3 * k] <= box.x[1]
      && world[3 * k + 1] >= box.y[0] && world[3 * k + 1] <= box.y[1]
      && world[3 * k + 2] >= box.z[0] && world[3 * k + 2] <= box.z[1];
    // Depth out from the face, for the plan's outward axis (x is u, z is -v).
    const depth = (k) => (world[3 * k] - plan.origin[0]) * plan.outward[0] + (-world[3 * k + 2] - plan.origin[1]) * plan.outward[1];
    const tris = [];
    for (let t = 0; t < count / 3; t += 1) {
      if (lifted[t]) continue;
      const a = at(3 * t), b = at(3 * t + 1), c = at(3 * t + 2);
      if (!(inBox(a) && inBox(b) && inBox(c))) continue;
      lifted[t] = 1;
      if (Math.min(depth(a), depth(b), depth(c)) >= box.keepD) tris.push(a, b, c);
    }
    if (tris.length) out.push({ doorId: plan.id, geometry: subGeometry(geo, tris, matrix) });
  }
  if (lifted.some(Boolean)) {
    const keep = [];
    for (let t = 0; t < count / 3; t += 1) if (!lifted[t]) keep.push(at(3 * t), at(3 * t + 1), at(3 * t + 2));
    const Arr = pos.count > 65535 ? Uint32Array : Uint16Array;
    geo.setIndex(new THREE.BufferAttribute(new Arr(keep), 1));
    geo.clearGroups();
  }
  geo.userData.doorLeaves = out;
  return out;
}

/** The triangles `tris` (vertex indices) of `geo` as a float geometry in the frame `matrix`
 *  takes it to: position, normal and every uv set, indexed over the vertices they use. */
function subGeometry(geo, tris, matrix) {
  const remap = new Map();
  const order = [];
  const index = tris.map((i) => {
    if (!remap.has(i)) { remap.set(i, order.length); order.push(i); }
    return remap.get(i);
  });
  const out = new THREE.BufferGeometry();
  const normalMatrix = new THREE.Matrix3().getNormalMatrix(matrix);
  const vec = new THREE.Vector3();
  for (const [name, attr] of Object.entries(geo.attributes)) {
    if (!['position', 'normal', 'uv', 'uv1'].includes(name)) continue;
    const size = attr.itemSize;
    const arr = new Float32Array(order.length * size);
    order.forEach((src, k) => {
      if (name === 'position' || name === 'normal') {
        vec.fromBufferAttribute(attr, src);
        if (name === 'position') vec.applyMatrix4(matrix); else vec.applyMatrix3(normalMatrix).normalize();
        arr[k * size] = vec.x; arr[k * size + 1] = vec.y; arr[k * size + 2] = vec.z;
      } else {
        for (let c = 0; c < size; c += 1) arr[k * size + c] = attr.getComponent(src, c);
      }
    });
    out.setAttribute(name, new THREE.BufferAttribute(arr, size));
  }
  out.setIndex(index);
  if (!out.getAttribute('normal')) out.computeVertexNormals();
  out.computeBoundingSphere();
  return out;
}

/**
 * The material a lifted leaf piece is drawn in: the GLB's own, copied before the batch
 * whitens it, painted `albedo` (the colour the batch would have given it). The grille's
 * transmissive pane becomes a dark pane, so twelve triangles cost no transmission pass.
 */
export function doorLeafMaterial(source, albedo = null) {
  if (source.transmission > 0 || source.isMeshPhysicalMaterial) {
    const pane = new THREE.MeshStandardMaterial({ name: source.name, color: source.color.clone().multiplyScalar(0.12),
      roughness: 0.12, metalness: 0, side: THREE.DoubleSide });
    pane.userData.doorLeaf = true;
    return pane;
  }
  const m = source.clone();
  if (albedo) m.color.setRGB(albedo[0], albedo[1], albedo[2]);
  m.userData = { doorLeaf: true };
  return m;
}

// ---------------------------------------------------------------- the walk

/** Point-in-polygon (ray casting) on [[x, y], ...]. */
function inside(x, y, pts) {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
}

/**
 * The footprint outline with the doorway cut into the façade, in the structure frame: the
 * reveal to the leaf's face while shut; open, on through the opening into the vestibule,
 * kept off the open leaf. Null when the face's edge is not in the polygon.
 */
export function notchedOutline(plan, polygon, open) {
  const pt = (d, s) => planPoint(plan, d, s);
  const [s0, s1] = plan.jambs;
  const a = pt(0, s0), b = pt(0, s1);
  const n = polygon.length;
  const onSeg = (p, q, r) => {
    const dx = r[0] - q[0], dy = r[1] - q[1], len = Math.hypot(dx, dy) || 1;
    const cross = Math.abs((p[0] - q[0]) * dy - (p[1] - q[1]) * dx) / len;
    const t = ((p[0] - q[0]) * dx + (p[1] - q[1]) * dy) / (len * len);
    return cross < 0.02 && t > 0 && t < 1;
  };
  for (let i = 0; i < n; i += 1) {
    const q = polygon[i], r = polygon[(i + 1) % n];
    if (!onSeg(a, q, r) || !onSeg(b, q, r)) continue;
    // Along the edge's own direction, so the dent goes in in the polygon's winding.
    const forward = (b[0] - a[0]) * (r[0] - q[0]) + (b[1] - a[1]) * (r[1] - q[1]) > 0;
    // Open, the leaf stands along its hinge jamb, its thickness off the hinge's line.
    const thick = plan.leaf.front - plan.leaf.back + 0.01;
    const leafIn = plan.hinge === 'right' ? plan.leaf.s[1] - thick : plan.leaf.s[0] + thick;
    const back = plan.revealBack - VESTIBULE_DEPTH_M;
    let dent = open
      ? (plan.hinge === 'right'
        ? [pt(0, s0), pt(back, s0), pt(back, leafIn), pt(plan.revealBack, leafIn), pt(plan.revealBack, s1), pt(0, s1)]
        : [pt(0, s0), pt(plan.revealBack, s0), pt(plan.revealBack, leafIn), pt(back, leafIn), pt(back, s1), pt(0, s1)])
      : [pt(0, s0), pt(plan.leaf.front, s0), pt(plan.leaf.front, s1), pt(0, s1)];
    if (!forward) dent = dent.reverse();
    return [...polygon.slice(0, i + 1), ...dent, ...polygon.slice(i + 1)];
  }
  return null;
}

/**
 * A walk from the sidewalk up every tread to `inside` metres past the leaf, in the
 * structure frame: [{ d, s, u, v, y }] with y over the base (null on open ground, where
 * the caller's ground answers). At each riser the height changes over RISER_EASE_M each
 * side, so a figure steps up rather than gliding. `from` is an extra (u, v) start.
 */
export function doorPathPlan(plan, { inside: past = 0.6, from = null } = {}) {
  const s = (plan.jambs[0] + plan.jambs[1]) / 2;
  const end = plan.leaf.back - Math.max(0.1, Math.min(VESTIBULE_DEPTH_M - 0.3, past));
  const heightAt = (d) => {
    if (d < plan.revealBack) return plan.sill;        // the vestibule's floor, at the sill
    let y = null;
    for (const t of plan.treads) {
      if (d >= t.d[0] - 1e-6 && d <= t.d[1] + 1e-6 && s >= t.s[0] && s <= t.s[1]) y = y === null ? t.y : Math.max(y, t.y);
    }
    return y;
  };
  const out = [];
  const push = (d, y) => {
    const [u, v] = planPoint(plan, d, s);
    const last = out.at(-1);
    if (last && Math.abs(last.d - d) < 1e-4) return;
    out.push({ d, s, u, v, y });
  };
  // Every riser between the sidewalk and the end, walked inward.
  const edges = [...new Set(plan.treads.flatMap((t) => t.d).concat([plan.revealBack]))]
    .filter((d) => d < plan.sidewalk && d > end).sort((a, b) => b - a);
  push(plan.sidewalk, heightAt(plan.sidewalk));
  for (const d of edges) {
    const before = heightAt(d + 0.01), after = heightAt(d - 0.01);
    if (before === after) continue;
    push(d + RISER_EASE_M, before);
    push(d - RISER_EASE_M, after);
  }
  push(plan.leaf.front, heightAt(plan.leaf.front));
  push(end, heightAt(end));
  const path = out.sort((a, b) => b.d - a.d);
  if (from) path.unshift({ d: null, s: null, u: from[0], v: from[1], y: null });
  return path;
}

// ---------------------------------------------------------------- the vestibule

/** A dark box behind the opening, its faces turned inward, unlit: a room seen from the
 *  street, never daylight through the house. About 24 triangles. */
function vestibuleGeometry(plan) {
  const back = plan.revealBack - VESTIBULE_DEPTH_M, front = plan.revealBack;
  const s0 = plan.jambs[0] - 0.02, s1 = plan.jambs[1] + 0.02;
  const y0 = plan.sill - 0.002, y1 = plan.head + VESTIBULE_HEADROOM_M;
  const pos = [], col = [];
  const P = (d, s, y) => { const [u, v] = planPoint(plan, d, s); return [u, y, -v]; };
  // Brightest at the door, nearly black at the back: what light the doorway lets in.
  const shade = (d) => 0.008 + 0.024 * Math.max(0, Math.min(1, (d - back) / (front - back)));
  const centre = P((front + back) / 2, (s0 + s1) / 2, (y0 + y1) / 2);
  const quad = (a, b, c, d4, ds) => {
    const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], ad = [d4[0] - a[0], d4[1] - a[1], d4[2] - a[2]];
    const nrm = [ab[1] * ad[2] - ab[2] * ad[1], ab[2] * ad[0] - ab[0] * ad[2], ab[0] * ad[1] - ab[1] * ad[0]];
    const mid = [0, 1, 2].map((k) => (a[k] + b[k] + c[k] + d4[k]) / 4 - centre[k]);
    // Faces turned to the box's middle (inward).
    const order = nrm[0] * mid[0] + nrm[1] * mid[1] + nrm[2] * mid[2] > 0 ? [[a, ds[0]], [d4, ds[3]], [c, ds[2]], [a, ds[0]], [c, ds[2]], [b, ds[1]]]
      : [[a, ds[0]], [b, ds[1]], [c, ds[2]], [a, ds[0]], [c, ds[2]], [d4, ds[3]]];
    for (const [p, d] of order) { pos.push(...p); const g = shade(d); col.push(g, g * 0.86, g * 0.72); }
  };
  const box = (d0, d1) => [d0, d1, d1, d0];
  quad(P(back, s0, y0), P(front, s0, y0), P(front, s1, y0), P(back, s1, y0), box(back, front));          // floor
  quad(P(back, s0, y1), P(front, s0, y1), P(front, s1, y1), P(back, s1, y1), box(back, front));          // ceiling
  quad(P(back, s0, y0), P(front, s0, y0), P(front, s0, y1), P(back, s0, y1), box(back, front));          // side
  quad(P(back, s1, y0), P(front, s1, y0), P(front, s1, y1), P(back, s1, y1), box(back, front));          // side
  quad(P(back, s0, y0), P(back, s1, y0), P(back, s1, y1), P(back, s0, y1), [back, back, back, back]);    // back
  // The front wall round the opening, seen from inside: over the head and the two slips.
  quad(P(front, s0, plan.head), P(front, s1, plan.head), P(front, s1, y1), P(front, s0, y1), [front, front, front, front]);
  quad(P(front, s0, y0), P(front, plan.jambs[0], y0), P(front, plan.jambs[0], plan.head), P(front, s0, plan.head), [front, front, front, front]);
  quad(P(front, plan.jambs[1], y0), P(front, s1, y0), P(front, s1, plan.head), P(front, plan.jambs[1], plan.head), [front, front, front, front]);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geo.computeBoundingSphere();
  return geo;
}

// ---------------------------------------------------------------- the layer

/**
 * @param {object} o
 * @param {Map} o.registry            scene-loader's records
 * @param {object} o.buildings        the buildings layer (matrixOf, doorLeaves)
 * @param {Array} o.footprints        walker.js footprints — a hung door's gets `doorways`
 * @param {Array} o.decks             walker.js decks — the door's treads join it
 * @param {object} [o.interactions]   interact.js engine; each door is added to it
 * @param {() => ({e:number, n:number})|null} [o.visitor]  where the walker stands
 * @param {(e:number, n:number) => number} [o.groundAt]  the ground a path's off-step points stand on
 * @param {object} [o.confidence]
 * @param {string[]} [o.problems]
 */
export function createHouseDoors({ registry, buildings, footprints = [], decks = [], interactions = null,
  visitor = null, groundAt: ground = null, confidence = null, problems = [] } = {}) {
  const group = new THREE.Group();
  group.name = 'house-doors';
  const doors = [];
  const hung = new Map();       // door id -> { thing, plan, holder, pivot, matrix }
  const vestibuleMaterial = new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.FrontSide });
  vestibuleMaterial.name = 'house-door-vestibule';

  /** A door's leaf pieces, from the buildings layer (which owns them), on the pivot. */
  function hangLeaf(entry, layer) {
    for (const mesh of [...entry.pivot.children]) entry.pivot.remove(mesh);
    const pieces = layer?.doorLeaves?.get(entry.plan.id) ?? [];
    const h = hingeOf(entry.plan);
    const [hu, hv] = planPoint(entry.plan, h.d, h.s);
    const conf = { attested: 0, inferred: 0.5, reconstructed: 1 }[entry.plan.grades.leaf] ?? 0;
    for (const piece of pieces) {
      const n = piece.geometry.getAttribute('position').count;
      if (!piece.geometry.getAttribute('_confidence')) {
        piece.geometry.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(n).fill(conf), 1));
      }
      if (confidence?.patch && !piece.material.userData.confidencePatched) {
        confidence.patch(piece.material);
        piece.material.userData.confidencePatched = true;
      }
      const mesh = new THREE.Mesh(piece.geometry, piece.material);
      // The pieces are in the structure's frame; the pivot stands at the hinge.
      mesh.position.set(-hu, 0, hv);
      mesh.name = `house-door-leaf:${entry.plan.id}:${piece.material.name}`;
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData.structure_id = entry.plan.structureId;
      entry.pivot.add(mesh);
    }
    entry.holder.updateMatrixWorld(true);
    return pieces.length;
  }

  for (const [id, sides] of Object.entries(HOUSE_DOORS)) {
    const record = registry.get(id);
    if (!record) continue;                            // not in this year's scene
    for (const plan of doorPlansOf(record)) {
      const m = buildings?.matrixOf?.(id);
      const fp = footprints.find((f) => f.id === id);
      const pieces = buildings?.doorLeaves?.get(plan.id) ?? [];
      const polygon = Array.isArray(record.sidecar.footprint) ? record.sidecar.footprint : record.sidecar.footprint?.polygon;
      const shut = Array.isArray(polygon) ? notchedOutline(plan, polygon, false) : null;
      if (!m || !fp || !pieces.length || !shut || !sides[plan.id.split(':')[1]]) {
        // Another build of the house (a structure version) need not carry this leaf.
        if (!pieces.length && record.version && record.version.label !== 'v4') continue;
        problems.push(`${plan.id}: a door to hang, but ${!m ? 'its house was not drawn' : !fp ? 'it has no footprint'
          : !pieces.length ? 'its baked leaf was not found in the mesh' : 'its doorway is not on the footprint\'s face'} — the door stays shut`);
        continue;
      }
      const holder = new THREE.Group();
      holder.name = `house-door:${plan.id}`;
      holder.matrixAutoUpdate = false;
      holder.matrix.copy(m);
      group.add(holder);
      const h = hingeOf(plan);
      const [hu, hv] = planPoint(plan, h.d, h.s);
      const pivot = new THREE.Object3D();
      pivot.position.set(hu, 0, -hv);
      holder.add(pivot);
      const vestibule = new THREE.Mesh(vestibuleGeometry(plan), vestibuleMaterial);
      vestibule.name = `house-door-vestibule:${plan.id}`;
      vestibule.userData.structure_id = id;
      holder.add(vestibule);
      const entry = { plan, holder, pivot, matrix: m.clone() };
      hangLeaf(entry, buildings);

      // Structure frame to local ENU (and world height), through the drawn placement.
      const v3 = new THREE.Vector3();
      const enu = (u, v, y = 0) => { v3.set(u, y, -v).applyMatrix4(entry.matrix); return { e: v3.x, n: -v3.z, y: v3.y }; };
      const toWorld = footprintToWorld(record.sidecar.placement);
      // The treads: decks at the heights they are drawn, which the walker climbs; and the
      // vestibule's floor, level with the sill, for a visitor through the open door.
      const floor = { id: 'vestibule', d: [plan.revealBack - VESTIBULE_DEPTH_M, plan.revealBack + 0.01],
        s: [plan.jambs[0] - 0.02, plan.jambs[1] + 0.02], y: plan.sill };
      for (const t of [...plan.treads, floor]) {
        const corners = [[t.d[0], t.s[0]], [t.d[1], t.s[0]], [t.d[1], t.s[1]], [t.d[0], t.s[1]]]
          .map(([d, s]) => planPoint(plan, d, s)).map(([u, v]) => enu(u, v, t.y));
        decks.push({ id: `${plan.id}:${t.id}`, y: corners[0].y, pts: corners.map((c) => [c.e, c.n]) });
      }
      // The doorway: in its zone, the walker reads the façade with the reveal cut in.
      const back = plan.revealBack - VESTIBULE_DEPTH_M;
      const zone = [[back - ZONE_MARGIN_M, plan.jambs[0] - ZONE_MARGIN_M], [ZONE_MARGIN_M, plan.jambs[0] - ZONE_MARGIN_M],
        [ZONE_MARGIN_M, plan.jambs[1] + ZONE_MARGIN_M], [back - ZONE_MARGIN_M, plan.jambs[1] + ZONE_MARGIN_M]]
        .map(([d, s]) => toWorld(planPoint(plan, d, s)));
      const outlineOpen = notchedOutline(plan, polygon, true).map(toWorld);
      const outlineShut = shut.map(toWorld);
      // Where the leaf sweeps, in the world: someone standing there stops it closing.
      const sweep = [[plan.leaf.front + 0.05, plan.jambs[0]], [back + 0.2, plan.jambs[0]], [back + 0.2, plan.jambs[1]],
        [plan.leaf.front + 0.05, plan.jambs[1]]].map(([d, s]) => toWorld(planPoint(plan, d, s)));

      const at = enu(...planPoint(plan, 0.4, (plan.jambs[0] + plan.jambs[1]) / 2));
      const thing = {
        id: plan.id,
        kind: 'door',
        structureId: id,
        name: plan.name,
        states: ['closed', 'open'],
        state: 'closed',
        at: [at.e, at.n],
        reach: DOOR_REACH_M,
        swing: 0,
        plan,
        actions: {
          closed: [{ id: 'open', label: 'Open door', to: 'open',
            steps: [{ label: 'Opening', seconds: DOOR_SWING_S, run: (t) => setSwing(t) }] }],
          open: [{ id: 'close', label: 'Close door', to: 'closed',
            refuse: () => (inSweep() ? 'Step out of the doorway first' : null),
            steps: [{ label: 'Closing', seconds: DOOR_SWING_S, run: (t) => setSwing(1 - t) }] }],
        },
      };
      const isOpen = () => thing.state === 'open' && !thing.running;
      fp.doorways = [...(fp.doorways ?? []), { id: plan.id, zone, shut: outlineShut, open: outlineOpen, isOpen }];
      footprints.wallsVersion = (footprints.wallsVersion ?? 0) + 1;
      function inSweep() {
        const here = visitor?.();
        return !!here && inside(here.e, here.n, sweep);
      }
      function setSwing(t) {
        thing.swing = t;
        const eased = t * t * (3 - 2 * t);
        // Plan (u, v) is glTF (x, -z): an inward turn of the free edge is a turn about +y of
        // the plan angle it makes. leafPose gives (d, s); this face's frame is (outward, along).
        const pose = leafPose(plan, eased);
        const du = plan.outward[0] * pose.dir[0] + plan.along[0] * pose.dir[1];
        const dv = plan.outward[1] * pose.dir[0] + plan.along[1] * pose.dir[1];
        const shut0 = leafPose(plan, 0).dir;
        const su = plan.outward[0] * shut0[0] + plan.along[0] * shut0[1], sv = plan.outward[1] * shut0[0] + plan.along[1] * shut0[1];
        pivot.rotation.y = Math.atan2(dv, du) - Math.atan2(sv, su);
        holder.updateMatrixWorld(true);
      }
      setSwing(0);
      thing.setSwing = setSwing;
      const span = planPoint(plan, plan.leaf.front, plan.jambs[0]), span1 = planPoint(plan, plan.leaf.front, plan.jambs[1]);
      thing.span = { a: toWorld(span), b: toWorld(span1) };
      /** The walk up to this door (house-doors.js header). */
      thing.path = ({ from = null, inside: past = 0.6, groundAt = ground } = {}) => {
        let fromUV = null;
        if (from) {
          // A start in ENU, back into the structure frame through the placement's inverse.
          v3.set(from[0], 0, -from[1]).applyMatrix4(new THREE.Matrix4().copy(entry.matrix).invert());
          fromUV = [v3.x, -v3.z];
        }
        const pts = doorPathPlan(plan, { inside: past, from: fromUV }).map((p) => {
          const w = enu(p.u, p.v, p.y ?? 0);
          return { e: w.e, n: w.n, y: p.y === null ? (groundAt ? groundAt(w.e, w.n) : w.y) : w.y };
        });
        // The bearing that looks out of the door to the street.
        const out0 = enu(...planPoint(plan, 0, 0)), out1 = enu(...planPoint(plan, 1, 0));
        pts.outward = (Math.atan2(out1.e - out0.e, out1.n - out0.n) * 180 / Math.PI + 360) % 360;
        return pts;
      };
      hung.set(plan.id, entry);
      entry.thing = thing;
      doors.push(thing);
      if (interactions) interactions.add(thing);
    }
  }

  const get = (id) => doors.find((d) => d.id === id) ?? null;
  function act(id, action) {
    const thing = typeof id === 'string' ? get(id) : id;
    if (!thing) return { ok: false, why: 'no such door' };
    const want = action === 'open' ? 'open' : 'closed';
    if (thing.state === want && !thing.running) return { ok: true, already: true };
    if (interactions) return interactions.act(thing, action);
    // No engine (a test): straight to the end of the swing.
    thing.setSwing(want === 'open' ? 1 : 0);
    thing.state = want;
    return { ok: true, started: action };
  }

  return {
    group,
    doors,
    get,
    open: (id) => act(id, 'open'),
    close: (id) => act(id, 'close'),
    /** The walk up to a door: [{ e, n, y }] (house-doors.js header). */
    path: (id, options) => get(id)?.path(options) ?? null,
    /** After the buildings layer is rebuilt (a detail switch): hang its leaf instead. */
    rebind(layer) {
      for (const entry of hung.values()) {
        const m = layer?.matrixOf?.(entry.plan.structureId);
        if (m) { entry.matrix.copy(m); entry.holder.matrix.copy(m); }
        if (!hangLeaf(entry, layer)) problems.push(`${entry.plan.id}: the rebuilt house carries no leaf to hang`);
        entry.thing.setSwing(entry.thing.swing);
      }
    },
    /** The leaf's geometry and materials are the buildings layer's, freed with it. */
    dispose() {
      group.traverse((o) => { if (o.isMesh && o.name.startsWith('house-door-vestibule')) o.geometry.dispose(); });
      vestibuleMaterial.dispose();
    },
  };
}
