#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/** Two more 1904 carriages on their own loops, written into data/transport/driven/loops.json.
 *
 * Kevin, 2026-11-13: "for 1904 we should have another 2 carriages going on different loops
 * around prairie avenue and at least one of them should be counter clockwise and they should
 * potentially cross paths and one will wait for the other to cross while they proceed", and
 * "make the carriages look differnt ... the horses will vary and the coachmen will vary and
 * be as real as possible ... i imagine they were typically black".
 *
 * Hans Johnson's brougham already goes round Indiana–18th–Prairie–20th, counter-clockwise.
 * The two new ones take the blocks either side of his, also counter-clockwise:
 *
 *   - Henry Windish, coachman to Mrs. George M. Pullman (1729 Prairie), round Indiana–16th–
 *     Prairie–18th: up Prairie past the Pullman and Kimball houses, along 16th, down Indiana.
 *   - Joseph Daniels, coachman to Mrs. Philip D. Armour (2115 Prairie), round Indiana–20th–
 *     Prairie–22nd: up Prairie past the Armour house, along 20th, down Indiana.
 *
 * Kevin, 2026-11-14: "fix the brougham and allow it to make right turns and make one of
 * those loops clockwise". A team keeps to the right of the road, so a clockwise loop's
 * corners are right turns that hug the inside kerb. The brougham's authored 8° steering
 * (an 18 m turn) could not make them; its front wheels clear the body to about 17° of lock
 * (checked on the GLB's own wheel and body surfaces), so the coach now steers to 15° (an
 * 8.6 m turn) and its team swings with the front axle and pole (town-transport.js). Hans
 * and Henry Windish keep their counter-clockwise rounds (left turns, 18 m corners). Joseph
 * Daniels now goes round the next block east CLOCKWISE: up Prairie past the Armour house,
 * right along 20th, right down Calumet, right along 22nd and right again onto Prairie, his
 * lanes 2 m right of the crown and his corners 11 m. A clockwise loop beside a counter-
 * clockwise one would share a lane on the street between them; east of Prairie he shares
 * none, and his right turn into 20th crosses Hans's left turn out of it at Prairie: there
 * one gives way and waits for the other (transport-crossings.js). Hans meets Henry head on
 * in the other lane of 18th, and their left turns cross at Indiana and at Prairie.
 *
 * Every route is walked here at quarter-metre steps: each wheel, and each hoof of the
 * swung team, must stand on the 1904 carriageways with room to the kerb, or the tool
 * refuses it. Each row's envelope is its measured one with the fore-carriage (team, pole,
 * front gear) swung to the sharpest lock its own round asks for.
 *
 * Each lane is read off data/street_grid/1904.json: the carriageway's centre line, moved to
 * the right of the direction of travel by the lane offset below (Hans's own lanes measured
 * at 3 m on Indiana, 18th and 20th; the narrower 16th and Prairie take 2.5 m). The corners
 * are where the lanes meet. Both coachmen are named in the 1900 census at their employers'
 * houses (sidecars/1904/people.json); their faces, looks and ages are their own records'
 * (data/humans/variation/looks/), their box coats their own house colours, their coaches
 * (vehicle_finish, coachwork.js) and their driving reconstructed. They sit the brougham's
 * proved seated export, made for Hans (`driver_export_person_id`): the seat, the reins and
 * the draped box coat are fitted to that body, which is the same body for all three.
 *
 * `--check` refuses a loops.json whose two rows differ from what this file writes. The
 * rendered ground, clearance and hoof-support readings of each route run in the browser
 * (town-transport preflight), as Hans's do.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { routeFor, routeDistanceNear } from '../renderers/web/js/transport-loop.js';
import { refineRouteDistance } from '../renderers/web/js/team-drive.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const FILE = path.join(ROOT, 'data/transport/driven/loops.json');
const GRID = path.join(ROOT, 'data/street_grid/1904.json');
const PLACEMENTS = path.join(ROOT, 'data/transport/parked/placements.json');
const TEMPLATE = 'prairie_driven_brougham_loop_1904';
const HANS = 'pa1904_otis_f_r_c1900_hans_johnson';
const LIBERTY = 'L-1904-more-carriages-3555';
const CORNER_R = 18;
const STEERING_LIMIT_DEG = 15; // the front wheels clear the body to about 17°
const WHEEL_ROOM_M = .25, HOOF_ROOM_M = .2;
const ENVELOPE_BASIS = 'Actual native assembled mesh vertices incl hitch instances, both driverLOD0+3, steering-8/0/+8, WALK0/.5/1.3/1.6. Add clearance15cm margin; actual world/between-sample envelope remains a qualification question.';

// A four-corner carriageway's centre line: from the middle of one short end to the other.
function centreLine(poly) {
  if (poly.length !== 4) throw Error('lay_driven_carriages_1904: a four-corner carriageway expected');
  const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  return [mid(poly[3], poly[0]), mid(poly[1], poly[2])];
}
// The lane: the centre line, pointed the way the team drives and moved to its right.
function lane(grid, id, heading, offset_m) {
  const c = grid.carriageways.find(cw => cw.id === id);
  if (!c) throw Error(`lay_driven_carriages_1904: no carriageway ${id}`);
  let [a, b] = centreLine(c.polygon_local_m);
  const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
  let d = [(b[0] - a[0]) / len, (b[1] - a[1]) / len];
  const want = { north: [0, 1], south: [0, -1], east: [1, 0], west: [-1, 0] }[heading];
  if (d[0] * want[0] + d[1] * want[1] < 0) { [a, b] = [b, a]; d = [-d[0], -d[1]]; }
  const right = [d[1], -d[0]];
  return { id, sources: c.sources, p: [a[0] + right[0] * offset_m, a[1] + right[1] * offset_m], d };
}
function meet(l1, l2) {
  const [x1, y1] = l1.p, [dx1, dy1] = l1.d, [x2, y2] = l2.p, [dx2, dy2] = l2.d;
  const den = dx1 * dy2 - dy1 * dx2;
  if (Math.abs(den) < 1e-6) throw Error(`lay_driven_carriages_1904: ${l1.id} and ${l2.id} do not cross`);
  const t = ((x2 - x1) * dy2 - (y2 - y1) * dx2) / den;
  return [Math.round((x1 + dx1 * t) * 100) / 100, Math.round((y1 + dy1 * t) * 100) / 100];
}
// Corners in driving order; leg i runs from corner i to corner i + 1.
function loopOf(grid, legs, corner_radius_m = CORNER_R) {
  const lanes = legs.map(([id, heading, off]) => lane(grid, id, heading, off));
  const points = lanes.map((l, i) => meet(lanes[(i + lanes.length - 1) % lanes.length], l));
  return { route: { kind: 'path', corner_radius_m, points_enu_m: points }, sources: [...new Set(lanes.flatMap(l => l.sources))] };
}

const insidePoly = (p, poly) => {
  let yes = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const a = poly[i], b = poly[j];
    if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) yes = !yes;
  }
  return yes;
};
/** True when a disc of `room` (eight points round it and its centre) lies on the carriageways. */
function onRoad(grid, p, room) {
  const ring = [[0, 0], [room, 0], [-room, 0], [0, room], [0, -room]].concat([[1, 1], [-1, 1], [1, -1], [-1, -1]].map(([x, y]) => [x * room * Math.SQRT1_2, y * room * Math.SQRT1_2]));
  return ring.every(([dx, dy]) => grid.carriageways.some(c => insidePoly([p[0] + dx, p[1] + dy], c.polygon_local_m)));
}
/**
 * Walk a row's road at quarter-metre steps, posed as transport-loop.js poses it: each wheel,
 * and each hoof of the team swung with the front axle, on the carriageways. Returns the
 * sharpest lock the road asks for, in radians; throws where a wheel or hoof leaves the road.
 */
export function auditRoad(row, grid) {
  const road = routeFor(row.route), L = row.wheelbase_m, ra = row.root_ahead_of_rear_axle_m, half = row.track_m / 2;
  const toEnu = (o, x, z) => [o.e + Math.cos(o.yaw) * x + Math.sin(o.yaw) * z, o.n + Math.sin(o.yaw) * x - Math.cos(o.yaw) * z];
  const pivot = L - ra;
  let lock = 0;
  for (let s = 0; s < road.length; s += .25) {
    const rear = road.at(s), [e, n] = toEnu(rear, 0, ra), at = { ...rear, e, n };
    const steer = Math.atan(L * rear.curvature), c = Math.cos(steer), sn = Math.sin(steer);
    lock = Math.max(lock, Math.abs(steer));
    const wheels = [[half, -ra], [-half, -ra], [half * c, pivot - half * sn], [-half * c, pivot + half * sn]];
    const swing = (x, z) => [c * x + sn * (z - pivot), pivot - sn * x + c * (z - pivot)];
    const hooves = [];
    for (const side of [-1, 1]) for (const dz of [-.9, .9]) for (const dx of [-.2, .2]) hooves.push(swing(side * row.team_half_spacing_m + dx, row.horse_offset_m[2] + dz));
    for (const [x, z] of wheels) if (!onRoad(grid, toEnu(at, x, z), WHEEL_ROOM_M)) throw Error(`${row.id}: a wheel leaves the carriageway ${s.toFixed(2)} m along its road`);
    for (const [x, z] of hooves) if (!onRoad(grid, toEnu(at, x, z), HOOF_ROOM_M)) throw Error(`${row.id}: a hoof leaves the carriageway ${s.toFixed(2)} m along its road`);
  }
  if (lock > STEERING_LIMIT_DEG * Math.PI / 180) throw Error(`${row.id}: its road asks more lock than the brougham has`);
  return lock;
}
/**
 * Does the brougham's front gear turn to `deg` of lock without a front wheel meeting the body?
 * Reads the GLB the rows drive: every body surface (sampled across each triangle) against
 * each front wheel's disc (its radius and 7 cm either side of its plane), the wheels swung
 * about vehicle_steer_front as town-transport.js swings them.
 */
export function frontWheelsClear(glbPath, deg) {
  const glb = fs.readFileSync(glbPath), jsonLength = glb.readUInt32LE(12);
  const json = JSON.parse(glb.subarray(20, 20 + jsonLength)), bin = glb.subarray(28 + jsonLength);
  const read = index => {
    const a = json.accessors[index], view = json.bufferViews[a.bufferView];
    const width = { SCALAR: 1, VEC3: 3 }[a.type], Kind = { 5126: Float32Array, 5123: Uint16Array, 5125: Uint32Array }[a.componentType];
    const size = Kind.BYTES_PER_ELEMENT, stride = view.byteStride ?? size * width, start = (view.byteOffset ?? 0) + (a.byteOffset ?? 0);
    const out = [];
    for (let k = 0; k < a.count; k++) {
      const row = [];
      for (let j = 0; j < width; j++) {
        const at = bin.byteOffset + start + k * stride + j * size;
        row.push(new Kind(bin.buffer.slice(at, at + size))[0]);
      }
      out.push(width === 1 ? row[0] : row);
    }
    return out;
  };
  const nodes = json.nodes, byName = name => nodes.find(n => n.name === name);
  const steer = byName('vehicle_steer_front'), wheel = byName('vehicle_wheel_front_left');
  const pivot = steer.translation, offset = Math.abs(wheel.translation[0]);
  let radius = 0;
  for (const c of wheel.children ?? []) if (nodes[c].mesh != null) for (const p of json.meshes[nodes[c].mesh].primitives) {
    const a = json.accessors[p.attributes.POSITION]; radius = Math.max(radius, a.max[1], a.max[2]);
  }
  const points = [];
  const walk = (index, at, gear) => {
    const n = nodes[index], here = at.map((v, k) => v + (n.translation?.[k] ?? 0));
    if (n.rotation && n.rotation.some((v, k) => Math.abs(v - [0, 0, 0, 1][k]) > 1e-9)) throw Error('frontWheelsClear: a rotated node; translations only expected');
    const inGear = gear || /^vehicle_(steer_front|running_gear|wheel_|team_pole)|^hubcap$/.test(n.name ?? '');
    if (n.mesh != null && !inGear) for (const p of json.meshes[n.mesh].primitives) {
      const P = read(p.attributes.POSITION), I = p.indices != null ? read(p.indices) : P.map((_, k) => k);
      for (let k = 0; k < I.length; k += 3) {
        const [A, B, C] = [P[I[k]], P[I[k + 1]], P[I[k + 2]]];
        for (let u = 0; u <= 6; u++) for (let w = 0; w <= 6 - u; w++) {
          const x = u / 6, y = w / 6, z = 1 - x - y;
          points.push([0, 1, 2].map(j => here[j] + A[j] * x + B[j] * y + C[j] * z));
        }
      }
    }
    for (const c of n.children ?? []) walk(c, here, inGear);
  };
  for (const i of json.scenes[0].nodes) walk(i, [0, 0, 0], false);
  for (const a of [deg, -deg].map(d => d * Math.PI / 180)) for (const side of [1, -1]) for (const q of points) {
    const dx = q[0] - pivot[0], dz = q[2] - pivot[2];
    const x = Math.cos(a) * dx - Math.sin(a) * dz, z = Math.sin(a) * dx + Math.cos(a) * dz;
    if (Math.abs(x - side * offset) < .07 && Math.hypot(q[1] - pivot[1], z) < radius + .005) return false;
  }
  return true;
}

/** The measured envelope, its fore-carriage (ahead of the front axle) swung to ± `lock`. */
function sweptEnvelope([x0, z0, x1, z1], pivot, lock) {
  const out = [x0, z0, x1, z1];
  for (const a of [-lock, lock]) for (const [x, z] of [[x0, pivot], [x1, pivot], [x0, z1], [x1, z1]]) {
    const X = Math.cos(a) * x + Math.sin(a) * (z - pivot), Z = pivot - Math.sin(a) * x + Math.cos(a) * (z - pivot);
    out[0] = Math.min(out[0], X); out[2] = Math.max(out[2], X); out[1] = Math.min(out[1], Z); out[3] = Math.max(out[3], Z);
  }
  return out.map(v => Math.round(v * 1e4) / 1e4);
}

const CARRIAGES = [
  {
    id: 'prairie_driven_brougham_north_loop_1904',
    name: 'Carriage driver on Prairie Avenue, 16th to 18th Street',
    // T-3557: the ride bar's short name (a phone cuts the long one).
    ride_name: 'Pullman brougham',
    person_id: 'pa1904_pullman_mrs_george_m_c1900_henry_windish',
    legs: [['e18th_indiana_prairie', 'east', 3], ['prairie_16_18', 'north', 2.5],
      ['e16th_indiana_prairie', 'west', 2.5], ['indiana_16_18', 'south', 3]],
    // A gentler pace than Hans's, so their rounds drift past each other and meet at the
    // crossings every few laps rather than once in hours.
    speed_m_s: 1.1,
    // He pulls up at his own employer's door, 1729 Prairie (the middle of its frontage).
    stops: [{ label: "the Pullman house's door", at: [1404.1, -3173.8], dwell_s: 45 }],
    initial_distance_m: 372,
    livery: {
      // His own plum (his record's working clothes), dark trousers, silver buttons, brown gloves.
      garment_outer__box_coat_wool: [0.062, 0.028, 0.042],
      garment_lower__highwaist_pantaloons: [0.03, 0.028, 0.03],
      accessory__brass_livery_buttons: [0.72, 0.72, 0.7],
      accessory__pale_driving_gloves: [0.16, 0.09, 0.05],
    },
    finish: {
      seed: 'pullman-brougham-1904',
      // Black, with deep claret panels, carmine running gear and gilt trim: a kept coach.
      panels: [0.03, 0.005, 0.008], timber: [0.005, 0.005, 0.006], gear: [0.2, 0.012, 0.012],
      quarter: [0.006, 0.005, 0.006], upholstery: [0.02, 0.035, 0.026], trim: [0.62, 0.46, 0.2], trim_metalness: 0.9,
      gloss: 0.92, dust: 0.28, scuffs: 0.18,
    },
    note: "Henry Windish, coachman in Mrs. George M. Pullman's household at 1729 Prairie Avenue in the 1900 census, drives a brougham round Prairie, 16th Street and Indiana. The census names him there four years before the scene; this coach, its colours, its team, his livery and the round are reconstructed.",
  },
  {
    id: 'prairie_driven_brougham_south_loop_1904',
    name: 'Carriage driver on Prairie Avenue and Calumet, 20th to 22nd Street',
    ride_name: 'Armour brougham',
    person_id: 'pa1904_armour_mrs_philip_d_c1900_joseph_daniels',
    // Clockwise (Kevin, 2026-11-14): every corner a right turn, round the block east of Prairie.
    legs: [['prairie_20_22', 'north', 2], ['e20th_indiana_calumet', 'east', 2],
      ['calumet_20_22', 'south', 2], ['e22nd_indiana_calumet', 'west', 2]],
    corner_radius_m: 11,
    speed_m_s: 1.35,
    stops: [{ label: "the Armour house's door", at: [1409.3, -3664.5], dwell_s: 40 }],
    initial_distance_m: 324,
    livery: {
      // His own slate (his record's working clothes), drab trousers, brass buttons, pale gloves.
      garment_outer__box_coat_wool: [0.05, 0.058, 0.07],
      garment_lower__highwaist_pantaloons: [0.07, 0.06, 0.045],
    },
    finish: {
      seed: 'armour-brougham-1904',
      // All black, the panels a blue-black, the lacquer dulled and the road on it: a coach in hard use.
      panels: [0.006, 0.008, 0.016], timber: [0.006, 0.006, 0.006], gear: [0.008, 0.008, 0.008],
      quarter: [0.007, 0.007, 0.008], upholstery: [0.11, 0.065, 0.033], trim: [0.5, 0.5, 0.48], trim_metalness: 0.85,
      gloss: 0.7, dust: 0.62, scuffs: 0.55,
    },
    note: "Joseph Daniels, coachman in Mrs. Philip D. Armour's household at 2115 Prairie Avenue in the 1900 census, drives a brougham clockwise round Prairie, 20th Street, Calumet and 22nd Street. The census names him there four years before the scene; this coach, its colours, its team, his livery and the round are reconstructed.",
  },
];
/**
 * T-3557 (Kevin, 2026-11-15: build the rest of the Glessner ride). The waiting Glessner
 * brougham (data/transport/parked/placements.json `prairie_parked_studebaker_brougham`, on
 * Prairie's west side south of 18th, before the house) is this row while the visitor rides:
 * Charles Nelson, coachman in John J. Glessner's household at 1800 Prairie in the 1900 census,
 * on its box, Mr. Glessner inside. It is ON CALL: not loaded until asked for, and loaded where
 * the parked one stands, the same coach, coats and harness, so one takes over from the other.
 *
 * Its round is the block west of Prairie, CLOCKWISE (every corner a right turn, its corners
 * 10 m): down Prairie from the house, right along 20th, right up Indiana, right along 18th past
 * the coach-house doors and right again onto Prairie. Hans goes round the same block the other
 * way, in the far lane of each street; Henry Windish shares its lane of 18th from Indiana to
 * Prairie (his left turn in, its right turn in at Indiana, then his left out and its right out
 * at Prairie); Joseph Daniels's right turn into 20th lies across Prairie from its own. Where any
 * two footprints can meet, one waits (transport-crossings.js).
 *
 * The stand: Prairie's lane is 2.5 m right of its crown, the parked coach 4.29 m (by the kerb).
 * Its road leaves the lane for a straight lay-by through the parked coach's own root, on its
 * own bearing, a few metres of it either side of the rear axle, and eases back after; the
 * team holds there (`hold`) until the visitor is in. Everything of the ride is reconstructed.
 */
const GLESSNER_LIBERTY = 'L-glessner-ride-3557';
const PARKED_ID = 'prairie_parked_studebaker_brougham';
const GLESSNER = {
  id: 'prairie_driven_brougham_glessner_1904',
  name: 'The Glessner brougham, Charles Nelson driving',
  ride_name: 'Glessner brougham',
  person_id: 'pa1904_glessner_john_j_c1900_charles_nelson',
  replace_human_instance: 'hi_pa1904_glessner_john_j_c1900_charles_nelson_1904',
  // Lanes 2 m right of each crown (Prairie's 2.5): 3 m (Hans's) puts a hoof on the walk at its right turns.
  legs: [['prairie_18_20', 'south', 2.5], ['e20th_indiana_calumet', 'west', 2],
    ['indiana_18_20', 'north', 2], ['e18th_indiana_prairie', 'east', 2]],
  corner_radius_m: 10,
  speed_m_s: 1.2,
  // The lay-by: its straight from `behind_m` before the rear axle at the stand to `ahead_m` after.
  stand: { behind_m: 5, ahead_m: 8, radius_m: [60, 100], approach: [[-18.5, 0, 20]], leave: [[190, 0.8, 100], [215, 0, 40]], label: 'the Glessner house' },
  livery: {
    // His own colours as he stands at the stand (data/humans/recipes/coachman_livery_1904.json):
    // the bottle-green coat, white breeches, white-metal buttons and white cotton gloves, so the
    // coachman who drives off is the one who stood there.
    garment_outer__box_coat_wool: [0.014, 0.026, 0.019],
    garment_lower__highwaist_pantaloons: [0.66, 0.64, 0.58],
    accessory__brass_livery_buttons: [0.62, 0.62, 0.6],
    accessory__pale_driving_gloves: [0.72, 0.71, 0.68],
  },
  // The coach keeps its own paint, as the parked twin it stands in for shows it; the road on it only.
  finish: { seed: 'glessner-brougham-1904', gloss: 0.88, dust: 0.3, scuffs: 0.2 },
  note: "Charles Nelson, coachman in John J. Glessner's household at 1800 Prairie Avenue in the 1900 census, drives the Glessner brougham round Prairie, 20th Street, Indiana and 18th Street, and home to the coach house on 18th. The census names him there four years before the scene; Mr. Glessner riding with the visitor, this round, the coach and its team are reconstructed.",
  // The cab (brougham-near.glb, measured: tools/test_glessner_ride.mjs). Vehicle-root metres.
  cab_seat_local_m: [-0.27, 1.296, -0.45],
  cab_eye_m: 0.58,
  // The eye's way in (vehicle-root [x, y, z], y over the road): from the kerb's edge (the walk is
  // 0.15 m up) forward of the open leaf, onto the step, stooping through the doorway, to the seat.
  cab_via_local_m: [[-1.4, 1.75, 0.3], [-0.95, 1.75, 0.08], [-0.62, 1.7, -0.05], [-0.35, 1.8, -0.4]],
  cab_stand_local_xz_m: [-1.4, 0.3],
  passengers: [{
    person_id: 'glessner_john_j', short_name: 'Mr. Glessner', asset_id: 'glessner_john_j_1904',
    instance_id: 'hi_glessner_john_j_1904', seat_local_m: [0.2, 1.307, -0.72], sink_m: 0.06,
    basis: "John J. Glessner (1843-1936) of 1800 Prairie Avenue, his own 1904 figure and record, seated in his household's brougham beside the visitor. That he rides, when and where, is reconstructed play; his figure plays the coachmen's seated clip (sit_drive_look_v2), bent to the cab's lower seat and roof, hat off (renderers/web/js/cab-passenger.js).",
  }],
};

/** The cab door: cut from the body at runtime (renderers/web/js/cab-door.js) after ROOT's right-door study. */
const CAB_DOOR_STUDY = 'evidence/transport/T2797 right-door study v3 (chicago-brougham-right-door-study-v3)';
const CAB_DOOR = {
  hinge_local_m: [-0.655, 0, -0.43], open_deg: -65, duration_s: 1.6,
  regions: [{ x_m: [-0.95, -0.47], y_m: [0.93, 2.04] }, { x_m: [-0.95, -0.5], y_m: [0.87, 0.93] }, { x_m: [-0.95, -0.40], y_m: [0.3, 0.87] }],
};

/** The study's door outline in the body's side, (y, z) vehicle-root metres, its `aperture_profile_yz_m`. */
const CAB_DOOR_PROFILE = [[0.4899,-0.0875], [0.4901,-0.1178], [0.4915,-0.1488], [0.4947,-0.1794], [0.5001,-0.2088], [0.5083,-0.2359], [0.5191,-0.2608], [0.5322,-0.2842], [0.5478,-0.3058], [0.5659,-0.3256], [0.5867,-0.3434], [0.6088,-0.3592], [0.6322,-0.3732], [0.6589,-0.3854], [0.6908,-0.3955], [0.7299,-0.4036], [0.7762,-0.4092], [0.8282,-0.4124], [0.8861,-0.4138], [1.206,-0.4169], [1.3083,-0.4171], [1.3966,-0.4121], [2.0025,-0.3617], [2.0784,-0.1224], [2.1013,0.0708], [2.0458,0.2324], [1.3927,0.2926], [1.306,0.2899], [0.8478,0.2524], [0.7996,0.2473], [0.7552,0.2399], [0.7152,0.2303], [0.6802,0.2192], [0.6494,0.2063], [0.6218,0.1916], [0.5965,0.1749], [0.5736,0.156], [0.5539,0.135], [0.5371,0.1122], [0.5229,0.0879], [0.5111,0.0622], [0.5021,0.0345], [0.4961,0.0048], [0.4925,-0.0261], [0.4906,-0.0571]];

function laybyRoute(grid, spec, parked) {
  const { route, sources } = loopOf(grid, spec.legs, spec.corner_radius_m);
  const b = parked.bearing_deg * Math.PI / 180, d = [Math.sin(b), Math.cos(b)];
  const ra = 1.15; // the brougham's root is 1.15 m ahead of its rear axle (the template row's)
  const rear = [parked.at_local_enu_m[0] - d[0] * ra, parked.at_local_enu_m[1] - d[1] * ra];
  const at = k => [Math.round((rear[0] + d[0] * k) * 1e4) / 1e4, Math.round((rear[1] + d[1] * k) * 1e4) / 1e4];
  // Back onto the lane (leg 0, from corner 0 to corner 1) `ease_m` past the lay-by's end.
  const [c0, c1] = route.points_enu_m;
  const u = [c1[0] - c0[0], c1[1] - c0[1]], len = Math.hypot(...u), un = [u[0] / len, u[1] / len];
  const along = p => (p[0] - c0[0]) * un[0] + (p[1] - c0[1]) * un[1];
  // `approach` and `leave`: [metres from the rear axle at the stand, share of the way from the
  // lane to the lay-by, the bend's radius] — wide bends, so the team (which leads, and swings
  // with the lock) is never turned toward the kerb near it; the stand's own two bends `radius_m`.
  const lay = along(rear), off = [rear[0] - (c0[0] + un[0] * lay), rear[1] - (c0[1] + un[1] * lay)];
  const blend = (k, f) => [Math.round((c0[0] + un[0] * (lay + k) + off[0] * f) * 1e4) / 1e4,
    Math.round((c0[1] + un[1] * (lay + k) + off[1] * f) * 1e4) / 1e4];
  const { approach, leave, behind_m, ahead_m, radius_m } = spec.stand;
  route.points_enu_m = [c0, ...approach.map(([k, f]) => blend(k, f)), at(-behind_m), at(ahead_m),
    ...leave.map(([k, f]) => blend(k, f)), ...route.points_enu_m.slice(1)];
  const r = spec.corner_radius_m;
  route.corner_radii_m = [r, ...approach.map(x => x[2]), ...radius_m, ...leave.map(x => x[2]), r, r, r];
  return { route, sources, rear };
}

function glessnerRow(base, grid, placements) {
  const spec = GLESSNER;
  const parked = Object.values(placements.scenes).flat().find(r => r.id === PARKED_ID);
  if (!parked) throw Error(`lay_driven_carriages_1904: no parked ${PARKED_ID}`);
  const { route, sources, rear } = laybyRoute(grid, spec, parked);
  const road = routeFor(route);
  const near = routeDistanceNear(road, ...rear, .05);
  const stand = refineRouteDistance(road, rear[0], rear[1], near.distance_m, .5, .01);
  if (stand.off_m > .005) throw Error(`${spec.id}: its road misses the parked coach's rear axle by ${stand.off_m.toFixed(3)} m`);
  const distance_m = Math.round(stand.distance_m * 1000) / 1000;
  const cab = {
    hinge_local_m: CAB_DOOR.hinge_local_m, open_deg: CAB_DOOR.open_deg, duration_s: CAB_DOOR.duration_s,
    profile_yz_m: CAB_DOOR_PROFILE, regions: CAB_DOOR.regions, uncut_materials: 'iron',
    basis: `Right (kerbside) leaf, rear-hung, opened ${-CAB_DOOR.open_deg} degrees: its outline, hinge line and angle are ${CAB_DOOR_STUDY}'s; here it is cut from the coach's own body at runtime and its step left fixed. Reconstructed.`,
    liberty: GLESSNER_LIBERTY,
  };
  return {
    ...base,
    id: spec.id, name: spec.name, ride_name: spec.ride_name, scene: '1904',
    speed_m_s: spec.speed_m_s, route,
    stops: [{ label: spec.stand.label, distance_m, dwell_s: 0, hold: true }],
    initial_distance_m: distance_m, initial_state: 'stopped', initial_reason: 'stand',
    on_call: true, stand_in_for: PARKED_ID, coach_house: { house: 'glessner_house', from: 'west' },
    horse_coat_row: PARKED_ID,
    person_id: spec.person_id, replace_human_instance: spec.replace_human_instance,
    driver_export_person_id: HANS,
    driver_livery_colours: spec.livery,
    vehicle_finish: { ...spec.finish, grade: 'reconstructed', liberty: GLESSNER_LIBERTY },
    driver_instance: {
      person_id: spec.person_id,
      interaction: { opens: 'resident_card', selectable: true },
      provenance: { grade: 'reconstructed', basis: spec.note, liberty: GLESSNER_LIBERTY },
      review_required: false,
    },
    cab_seat_local_m: spec.cab_seat_local_m, cab_eye_m: spec.cab_eye_m,
    cab_via_local_m: spec.cab_via_local_m, cab_stand_local_xz_m: spec.cab_stand_local_xz_m,
    cab_basis: 'Inside the brougham, on the kerbside half of its seat (brougham-near.glb: cushion top 1.296 m, roof lining 2.046 m over it), the eye 0.58 m over the cushion: lower than a man sits upright, as the cab is lower than one (tools/test_glessner_ride.mjs measures its clearance to the roof, walls and door).',
    cab_door: cab,
    passengers: spec.passengers.map(p => ({ ...p, liberty: GLESSNER_LIBERTY })),
    source_ids: ['studebaker_1893_illustrated_souvenir', 'census_1900_chicago_t623_roll245', ...sources],
    note: spec.note, liberty: GLESSNER_LIBERTY,
  };
}

// Hans's own coach keeps its catalogue green and black; it gets the road on it too.
const HANS_FINISH = { seed: 'otis-brougham-1904', gloss: 0.85, dust: 0.4, scuffs: 0.3 };

export function buildRows(config = JSON.parse(fs.readFileSync(FILE, 'utf8')), grid = JSON.parse(fs.readFileSync(GRID, 'utf8')),
  placements = JSON.parse(fs.readFileSync(PLACEMENTS, 'utf8'))) {
  const template = config.rows.find(row => row.id === TEMPLATE);
  if (!template || template.person_id !== HANS) throw Error('lay_driven_carriages_1904: Hans\'s brougham row is the template');
  const { vehicle_finish: _, ...base } = template;
  const rows = CARRIAGES.map(spec => {
    const { route, sources } = loopOf(grid, spec.legs, spec.corner_radius_m);
    const road = routeFor(route); // refuses a road too tight for its corners
    const stops = spec.stops.map(stop => {
      const near = routeDistanceNear(road, ...stop.at);
      if (near.off_m > 3) throw Error(`${spec.id}: stop "${stop.label}" is ${near.off_m.toFixed(1)} m off its road`);
      return { label: stop.label, distance_m: Math.round(near.distance_m * 4) / 4, dwell_s: stop.dwell_s };
    });
    return {
      ...base,
      id: spec.id, name: spec.name, ride_name: spec.ride_name, scene: '1904',
      speed_m_s: spec.speed_m_s, route, stops, initial_distance_m: spec.initial_distance_m,
      person_id: spec.person_id,
      driver_export_person_id: HANS,
      driver_livery_colours: spec.livery,
      vehicle_finish: { ...spec.finish, grade: 'reconstructed', liberty: LIBERTY },
      driver_instance: {
        person_id: spec.person_id,
        interaction: { opens: 'resident_card', selectable: true },
        provenance: { grade: 'reconstructed', basis: spec.note, liberty: LIBERTY },
        review_required: false,
      },
      source_ids: ['studebaker_1893_illustrated_souvenir', 'census_1900_chicago_t623_roll245', ...sources],
      note: spec.note, liberty: LIBERTY,
    };
  });
  rows.push(glessnerRow(base, grid, placements));
  for (const key of ['source_lane_intersections_enu_m']) for (const row of rows) delete row[key];
  const hans = { ...template, vehicle_finish: { ...HANS_FINISH, grade: 'reconstructed', liberty: LIBERTY } };
  // The brougham's lock, and each row's envelope swept to the lock its own road asks for.
  const measured = template.envelope_measured_local_xz_m ?? template.envelope_local_xz_m;
  const glb = path.join(ROOT, 'renderers/web', template.vehicle_file);
  if (!frontWheelsClear(glb, STEERING_LIMIT_DEG + 1)) throw Error(`lay_driven_carriages_1904: the brougham's front wheels meet its body within ${STEERING_LIMIT_DEG + 1}° of lock`);
  for (const row of [hans, ...rows]) {
    row.steering_limit_deg = STEERING_LIMIT_DEG;
    const lock = auditRoad(row, grid);
    row.envelope_measured_local_xz_m = measured;
    row.envelope_local_xz_m = sweptEnvelope(measured, row.wheelbase_m - row.root_ahead_of_rear_axle_m, lock);
    row.envelope_basis = `${ENVELOPE_BASIS} Fore-carriage (team, pole, front gear) swung to ±${(lock * 180 / Math.PI).toFixed(1)}° about the front axle, this road's sharpest lock (tools/lay_driven_carriages_1904.mjs).`;
  }
  return { hans, rows };
}

/** loops.json with Hans's finish and the three rows straight after his; every other row untouched. */
export function nextConfig(config) {
  const { hans, rows } = buildRows(config);
  const ids = new Set(rows.map(row => row.id));
  const others = config.rows.filter(row => !ids.has(row.id));
  const at = others.findIndex(row => row.id === TEMPLATE);
  return { ...config, rows: [...others.slice(0, at), hans, ...rows, ...others.slice(at + 1)] };
}

function main() {
  const check = process.argv.includes('--check');
  const config = JSON.parse(fs.readFileSync(FILE, 'utf8'));
  const next = nextConfig(config);
  if (check) {
    if (JSON.stringify(next) !== JSON.stringify(config)) {
      console.error('lay_driven_carriages_1904: the 1904 carriage rows of loops.json differ; run node tools/lay_driven_carriages_1904.mjs');
      process.exit(1);
    }
    console.log('lay_driven_carriages_1904: Hans\'s finish and 3 more 1904 carriage rows current (the Glessner brougham on call)');
    return;
  }
  fs.writeFileSync(FILE, `${JSON.stringify(next, null, 2)}\n`);
  for (const row of next.rows.filter(r => r.scene === '1904')) console.log(`${row.id}: ${routeFor(row.route).length.toFixed(1)} m, ${JSON.stringify(row.route.points_enu_m ?? row.route.bounds_enu_m)}`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
