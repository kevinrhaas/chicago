#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/** 1835's moving wagons, written into data/transport/driven/loops.json.
 *
 * Kevin, 2026-11-16: "Yes let's add wagons to 1835, we should have a lot of them running on
 * loops around the city, based on your town analysis put a correct number of wagons and horses
 * in motion around the city based on what would be a normal level of traffic at time of day and
 * year", then "Photographic wagons".
 *
 * HOW MANY. The first directory of the town (Fergus 1839) lists 41 teamsters and 30 draymen:
 * one working team a man. The 1835 town (3,265 at the November census, smaller in July) holds
 * the men its own records and the staffing model make teamsters: the eight the forwarding
 * houses employ (data/reconstruction/1835_business_staffing_model.json, on the 1839 directory),
 * Charles White the drayman, and four men the 1839 directory later lists as teamsters. Eleven of
 * them have a door in the drawn town (data/humans/inside_1835.json); S. Foot has no door and
 * Fitzsimmons is a lad in 1835. Ten drive here, one round a district each: the worked streets
 * hold no eleventh round that keeps off the others' streets (the slough across Dearborn and
 * Randolph and down State, the river bank under South Water east of Wells, Jefferson and
 * Madison unopened), so William Smith, the last of the directory's men, stays at home. Ten
 * teams of thirteen men is the town's whole carting trade on a July weekday, which is when it
 * was busiest: the harbour open, the schooners in (the Marine Journal), the land sales of June
 * just past. A teamster takes his dinner at the noon stand by his wagon (town_people_1835.py
 * "teamster"), so the road is not emptied at noon: each team is out from harnessing to putting
 * up, at its own man's hours.
 *
 * WHERE. Each team goes round its own district clockwise, keeping a metre right of the crown,
 * so its corners are right turns about its own blocks. No two districts share a street: they
 * meet only at crossings, where one gives way to the other (transport-crossings.js). Each
 * stands at its employer's door or at the stores of its round, as if loading. The streets are
 * graded and worn earth, sunk below their lots with gutters at the sides, so the wagons ride
 * their ruts (`rough_road`, transport-loop.js and transport-support.js).
 *
 * WHAT. The photographic farm-box wagon (Old Cart, Lyskilde, CC BY 4.0, adapted:
 * renderers/web/transport/farm-box-master/), the 1812 wagons' wagon, its teamster walking at the
 * near horse's head. Phones and Light take its far level. Every row is `streamed`
 * (town-transport.js): only the teams near the visitor are built, the rest go on their rounds
 * unseen, so a phone carries a few teams at a time, never all of them.
 *
 * `--check` refuses a loops.json whose 1835 rows differ from what this file writes; `--audit`
 * walks every round against the committed footprints, the other rounds and the 1835 ground.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { routeFor, routeDistanceNear } from '../renderers/web/js/transport-loop.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const FILE = path.join(ROOT, 'data/transport/driven/loops.json');
const STREETS = path.join(ROOT, 'data/streets/1835.json');
const INSIDE = path.join(ROOT, 'data/humans/inside_1835.json');
const LIBERTY = 'L-1835-town-wagons';
const LANE_M = 1.0;
const CORNER_R = 17;
const CART = {
  file: 'transport/farm-box-master/farm-box-near.glb',
  sha256: 'a1e8365d6369c417f86afda3a316d54a1a8b8591e729d6f23d2f7d75244bbf8d',
  // Phones and Light take the far level: its six maps are 256 px (2 MB on the GPU against the
  // middle level's 8), a town of teams at a phone's cost; the wagon is the same.
  light_file: 'transport/farm-box-master/farm-box-far.glb',
  light_sha256: '097c293885341c4d166c0121b921da3e89846cd04b3c6507576401e96d568a25',
};
// The farm-box wagon's measured interface, as the 1812 wagons carry it (lay_driven_wagons_1812.mjs).
const VEHICLE = {
  speed_m_s: 1.3, steering_limit_deg: 8, track_m: 1.21, wheelbase_m: 2.35,
  root_ahead_of_rear_axle_m: 1.175, wheel_radii_m: [0.685, 0.685, 0.535, 0.535],
  team_half_spacing_m: 0.65, horse_offset_m: [0, 0, 3.4987],
  driver_local_m: [1.3, 0, 4.4],
  passenger_local_m: [0, 0.955, 0.4],
  passenger_eye_m: 0.78,
  passenger_basis: 'Sitting on the farm-box bed boards (farm-box-near.glb planks top 0.955 m, x ±0.3 m, z -1.17 to 1.18 m), centre line, 0.4 m forward of the middle; the teamster walks. Reconstructed play (L-board-drive-3557).',
  envelope_local_xz_m: [-1.21, -1.86, 1.75, 5.1],
  envelope_basis: 'Farm-box cart bed, wheels and tongue, the two-horse team at 3.5 m, and the teamster walking 1.3 m off the near side, plus 15 cm.',
};
const SOURCES = ['fergus_directory_1839', 'chicago_newspapers_1833_1835', 'andreas_1884_v1', 'chicago_dpw_1891_streets'];
// The teamster routine's hours out with the team (tools/town_people_1835.py "teamster").
const OUT_FROM = 5.75, OUT_TO = 18.75;

// Each team: its district (west and east cross streets, north and south streets), its man, the
// business he drives for, and the doors it stands at (structure ids; resolved to the round).
const TEAMS = [
  { id: 'kinzie_wagon_south_water_1835', name: "J. H. Kinzie's wagon on South Water and Lake, Franklin to Wells",
    ride: "Kinzie's wagon", person: 'rc_gallagher_daniel', district: ['franklin', 'wells', 'south_water', 'lake'],
    stops: [['jh_kinzie_forwarding_store', 75]],
    note: "Daniel Gallagher drives for J. H. Kinzie's forwarding house, round its river block between Franklin and Wells, standing at Kinzie's door on South Water Street." },
  { id: 'reed_wagon_market_1835', name: 'Thomas Reed with his wagon on Market, Lake to Randolph',
    ride: "Reed's wagon", person: 'reed_thomas', district: ['market', 'franklin', 'lake', 'randolph'],
    stops: [['sauganash_hotel', 75]],
    note: 'Thomas Reed, a teamster in the 1839 directory, carts round the Market Street block from Lake to Randolph, standing at the Sauganash.' },
  { id: 'jones_wagon_lake_1835', name: "B. Jones's wagon on Lake and Randolph, Wells to LaSalle",
    ride: "Jones's wagon", person: 'rc_ingalls_chauncey', district: ['wells', 'lasalle', 'lake', 'randolph'],
    stops: [],
    note: "Chauncey Ingalls drives for B. Jones's storage and forwarding house on South Water Street, round the Lake Street block between Wells and LaSalle." },
  { id: 'cook_wagon_randolph_1835', name: 'Thomas Cook with his wagon on Randolph and Washington, Franklin to Wells',
    ride: "Cook's wagon", person: 'cook_thomas', district: ['franklin', 'wells', 'randolph', 'washington'],
    stops: [],
    note: 'Thomas Cook, a teamster in the 1839 directory, carts round the block between Franklin and Wells, Randolph to Washington.' },
  { id: 'kinzie_wagon_washington_1835', name: "J. H. Kinzie's second wagon on Randolph and Washington, LaSalle to Clark",
    ride: "Kinzie's other wagon", person: 'rc_newell_samuel', district: ['lasalle', 'clark', 'randolph', 'washington'],
    stops: [],
    note: "Samuel Newell drives J. H. Kinzie's second team round the block between LaSalle and Clark, Randolph to Washington." },
  { id: 'kinzie_wagon_state_1835', name: "John S. Kinzie's wagon on Randolph and Washington, Dearborn to State",
    ride: "J. S. Kinzie's wagon", person: 'rc_reilly_martin', district: ['dearborn', 'state', 'randolph', 'washington'],
    stops: [],
    note: "Martin Reilly drives for John S. Kinzie's forwarding house, round the block between Dearborn and State, Randolph to Washington." },
  { id: 'white_dray_west_side_1835', name: 'Charles White, drayman, on Canal and Clinton, Fulton to Lake',
    ride: "White's dray", person: 'rc_fb_white_charles', district: ['clinton', 'canal', 'fulton', 'lake'],
    stops: [],
    note: 'Charles White, a drayman of the West Side, carts round Canal and Clinton between Fulton and Lake.' },
  { id: 'western_hotel_driven_wagon_loop_1835', name: 'Otis Bardwell with the wagon on Canal and Clinton, Randolph to Washington',
    ride: 'Western Hotel wagon', person: 'rc_bardwell_otis', instance: 'hi_rc_bardwell_otis_1835', district: ['clinton', 'canal', 'randolph', 'washington'],
    stops: [['western_hotel', 75]],
    note: "Otis Bardwell drives for John S. Kinzie's forwarding house, round Clinton and Canal between Randolph and Washington, standing at the Western Hotel, in the rear of which was the yard the trains were driven into." },
  { id: 'sabine_wagon_north_water_1835', name: "Wm. Sabine's wagon on North Water and Kinzie, LaSalle to Clark",
    ride: "Sabine's wagon", person: 'rc_flynn_martin', district: ['lasalle_north', 'clark_north', 'kinzie', 'north_water'],
    stops: [],
    note: "Martin Flynn drives for Wm. Sabine's storage and forwarding house on North Water Street (advertised in June 1835 with lumber waggons for sale), round the North Side block between LaSalle and Clark." },
  { id: 'jones_wagon_north_side_1835', name: "B. Jones's second wagon on North Water and Kinzie, Franklin to Wells",
    ride: "Jones's other wagon", person: 'rc_leland_david', district: ['franklin_north', 'wells_north', 'kinzie', 'north_water'],
    stops: [],
    note: "David Leland drives B. Jones's second team round the North Side block between Franklin and Wells." },
];

// ---- street geometry --------------------------------------------------------------------
const streetsOf = () => new Map(JSON.parse(fs.readFileSync(STREETS, 'utf8')).streets.map(s => [s.id, s]));

/** Where two street centre lines cross: [e, n] and each one's segment index and parameter. */
function crossing(a, b) {
  const P = a.path_local_enu_m, Q = b.path_local_enu_m;
  for (let i = 0; i + 1 < P.length; i++) for (let j = 0; j + 1 < Q.length; j++) {
    const [p1, p2] = [P[i], P[i + 1]], [q1, q2] = [Q[j], Q[j + 1]];
    const d = (p2[0] - p1[0]) * (q2[1] - q1[1]) - (p2[1] - p1[1]) * (q2[0] - q1[0]);
    if (Math.abs(d) < 1e-9) continue;
    const t = ((q1[0] - p1[0]) * (q2[1] - q1[1]) - (q1[1] - p1[1]) * (q2[0] - q1[0])) / d;
    const u = ((q1[0] - p1[0]) * (p2[1] - p1[1]) - (q1[1] - p1[1]) * (p2[0] - p1[0])) / d;
    if (t >= -0.02 && t <= 1.02 && u >= -0.02 && u <= 1.02) {
      return { at: [p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])], [a.id]: i + t, [b.id]: j + u };
    }
  }
  throw Error(`lay_driven_wagons_1835: ${a.id} and ${b.id} do not cross`);
}
/** A street's centre line from one crossing to another (the street's own bends between). */
function along(street, from, to) {
  const P = street.path_local_enu_m, a = from[street.id], b = to[street.id];
  const pts = [from.at];
  if (a < b) for (let k = Math.floor(a) + 1; k <= Math.ceil(b) - 1; k++) pts.push(P[k]);
  else for (let k = Math.ceil(a) - 1; k >= Math.floor(b) + 1; k--) pts.push(P[k]);
  return pts;
}
/** The district's centre-line ring, clockwise: north street east, east street south, south street west, west street north. */
function ring(streets, [west, east, north, south]) {
  const S = id => { const s = streets.get(id); if (!s) throw Error(`lay_driven_wagons_1835: no street ${id}`); return s; };
  const nw = crossing(S(north), S(west)), ne = crossing(S(north), S(east));
  const se = crossing(S(south), S(east)), sw = crossing(S(south), S(west));
  const pts = [...along(S(north), nw, ne), ...along(S(east), ne, se), ...along(S(south), se, sw), ...along(S(west), sw, nw)];
  // Drop near-repeats and nearly straight bends (a street's own small kinks).
  const out = [];
  for (const p of pts) if (!out.length || Math.hypot(p[0] - out.at(-1)[0], p[1] - out.at(-1)[1]) > 1) out.push(p);
  if (Math.hypot(out[0][0] - out.at(-1)[0], out[0][1] - out.at(-1)[1]) <= 1) out.pop();
  return straighten(out);
}
function straighten(pts, deg = 4) {
  let changed = true;
  while (changed && pts.length > 4) {
    changed = false;
    for (let i = 0; i < pts.length; i++) {
      const a = pts[(i + pts.length - 1) % pts.length], p = pts[i], b = pts[(i + 1) % pts.length];
      const t = Math.abs(Math.atan2((p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0]),
        (p[0] - a[0]) * (b[0] - p[0]) + (p[1] - a[1]) * (b[1] - p[1]))) * 180 / Math.PI;
      if (t < deg) { pts.splice(i, 1); changed = true; break; }
    }
  }
  return pts;
}
/** The team's road round its district. On a straight it keeps LANE_M right of the crown, in the
 * worn roadway: 1835's streets are sunk about 18 cm below their lots, with banks from about 5 m
 * out (data/terrain e1834_harbor_cut); on a bank the ruts lean the wagon and its team furthest
 * (`rough_road`). The farm-box wagon steers to 8 degrees (a 17 m turn), so at each corner the teamster
 * swings out to SWING_M left of the crown and makes his right turn from there; the inside rear
 * wheel then passes about 4.4 m from the middle of the crossing, still in the roadway. The swing
 * starts SWING_AT_M before the corner and takes SWING_OVER_M. A street's own small bends are
 * taken in the lane. */
const SWING_M = -1.0, SWING_AT_M = 19, SWING_OVER_M = 16, CORNER_DEG = 30;
function lane(pts) {
  const n = pts.length;
  const legs = pts.map((p, i) => {
    const q = pts[(i + 1) % n], L = Math.hypot(q[0] - p[0], q[1] - p[1]);
    const d = [(q[0] - p[0]) / L, (q[1] - p[1]) / L];
    return { p, q, L, d, r: [d[1], -d[0]] };
  });
  const major = legs.map((leg, i) => {
    const prev = legs[(i + n - 1) % n];
    return Math.abs(Math.atan2(prev.d[0] * leg.d[1] - prev.d[1] * leg.d[0], prev.d[0] * leg.d[0] + prev.d[1] * leg.d[1])) > CORNER_DEG * Math.PI / 180;
  });
  const at = (leg, s, off) => [leg.p[0] + leg.d[0] * s + leg.r[0] * off, leg.p[1] + leg.d[1] * s + leg.r[1] * off];
  const meet = (a, offA, b, offB) => {
    const pa = at(a, 0, offA), pb = at(b, 0, offB), det = a.d[0] * b.d[1] - a.d[1] * b.d[0];
    const t = ((pb[0] - pa[0]) * b.d[1] - (pb[1] - pa[1]) * b.d[0]) / det;
    return [pa[0] + a.d[0] * t, pa[1] + a.d[1] * t];
  };
  // A vertex is taken swung out when it is a corner, or when a leg beside it is too short to
  // swing back to the lane between (North Water's bends by the river, a crossing's kink).
  const swung = major.slice();
  const need = (i, j) => (swung[i] ? (major[i] ? SWING_AT_M : 2) + SWING_OVER_M : 0) + (swung[j] ? (major[j] ? SWING_AT_M : 2) + SWING_OVER_M : 0);
  for (let changed = true, guard = 0; changed && guard < 4 * n; guard++) {
    changed = false;
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      if (swung[i] !== swung[j] && legs[i].L < need(i, j) + 4) { swung[i] = swung[j] = true; changed = true; }
    }
  }
  const off = i => (swung[i % n] ? SWING_M : LANE_M);
  const out = [];
  legs.forEach((leg, i) => {
    const prev = legs[(i + n - 1) % n], j = (i + 1) % n;
    out.push(meet(prev, off(i), leg, off(i)));
    if (swung[i] && swung[j] && leg.L < need(i, j) + 4) return; // stays swung out along it
    if (swung[i]) { const a = major[i] ? SWING_AT_M : 2; out.push(at(leg, a, SWING_M), at(leg, a + SWING_OVER_M, LANE_M)); }
    if (swung[j]) { const a = major[j] ? SWING_AT_M : 2; out.push(at(leg, leg.L - a - SWING_OVER_M, LANE_M), at(leg, leg.L - a, SWING_M)); }
  });
  return out.map(p => [Math.round(p[0] * 100) / 100, Math.round(p[1] * 100) / 100]);
}

/** Corners the team can round: where two bends are too close for their arcs, the gentler goes
 * (a street's own kink by a crossing, the river bank's bends along North Water). */
function fit(pts, r = CORNER_R) {
  const turnAt = (a, p, b) => Math.abs(Math.atan2((p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0]),
    (p[0] - a[0]) * (b[0] - p[0]) + (p[1] - a[1]) * (b[1] - p[1])));
  for (let guard = 0; guard < 64 && pts.length > 3; guard++) {
    const n = pts.length, turns = pts.map((p, i) => turnAt(pts[(i + n - 1) % n], p, pts[(i + 1) % n]));
    let worst = -1;
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n, leg = Math.hypot(pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]);
      if (r * Math.tan(turns[i] / 2) + r * Math.tan(turns[j] / 2) > leg - 0.5) { worst = turns[i] < turns[j] ? i : j; break; }
    }
    if (worst < 0) return pts;
    pts = pts.filter((_, i) => i !== worst);
  }
  return pts;
}

// ---- the rows ---------------------------------------------------------------------------
const doorOf = id => {
  const sc = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sidecars/1835', `${id}.json`), 'utf8'));
  return { name: sc.name, at: [sc.placement.local_e, sc.placement.local_n], fp: footprintWorld(sc) };
};
export function footprintWorld(sc) {
  const fp = sc?.footprint?.polygon ?? [], pl = sc?.placement ?? {};
  const th = (pl.rotation_deg ?? 0) * Math.PI / 180, c = Math.cos(th), s = Math.sin(th);
  return fp.map(([x, y]) => [pl.local_e + x * c + y * s, pl.local_n - x * s + y * c]);
}

export function buildRows() {
  const streets = streetsOf();
  const inside = new Map(JSON.parse(fs.readFileSync(INSIDE, 'utf8')).people.map(p => [p.person, p]));
  return TEAMS.map((team, k) => {
    const points = lane(fit(ring(streets, team.district)));
    const spec = { kind: 'path', corner_radius_m: CORNER_R, points_enu_m: points };
    const route = routeFor(spec);
    const stops = team.stops.map(([sid, dwell]) => {
      const door = doorOf(sid);
      // The place on the round nearest the building's own walls.
      let best = null;
      for (const p of door.fp.length ? door.fp : [door.at]) {
        const near = routeDistanceNear(route, ...p);
        if (!best || near.off_m < best.off_m) best = near;
      }
      if (best.off_m > 16) throw Error(`${team.id}: stop "${door.name}" is ${best.off_m.toFixed(1)} m off its round`);
      return { label: door.name, distance_m: Math.round(best.distance_m * 4) / 4, dwell_s: dwell };
    });
    const who = inside.get(team.person);
    const shift = Number(who?.shift) || 0;
    const asset = team.person === 'rc_bardwell_otis' ? 'bardwell_otis_1835' : who?.asset_id;
    if (!asset) throw Error(`${team.id}: ${team.person} has no figure in the drawn town`);
    const hours = [OUT_FROM + shift, OUT_TO + shift];
    const note = `${team.note} The town's own records make him a teamster (see L-1835-town-wagons); this wagon, its team, its round, its stops and his hours are reconstructed.`;
    return {
      ...VEHICLE,
      id: team.id, name: team.name, ride_name: team.ride, scene: '1835', driver_mode: 'on_foot', streamed: true,
      // The streets are graded and worn earth: the wagon rides their ruts (transport-loop.js).
      rough_road: true,
      route: spec, stops,
      // Spread round their rounds, so the town does not start with every team at a corner.
      initial_distance_m: Math.round(route.length * ((k * 0.37) % 1) * 4) / 4,
      hours,
      vehicle_file: CART.file, vehicle_glb_sha256: CART.sha256,
      vehicle_file_light: CART.light_file, vehicle_glb_sha256_light: CART.light_sha256,
      driver_asset: asset,
      person_id: team.person, replace_human_instance: team.instance ?? `hi_inside_${team.person}`,
      driver_instance: {
        person_id: team.person,
        interaction: { opens: 'resident_card', selectable: true },
        provenance: { grade: 'reconstructed', basis: note, liberty: LIBERTY },
        review_required: false,
      },
      horse_model: 'current26_walk_v2',
      hitch: {
        harness_file: 'transport/driven-hitch/current26-collar-girth-v2.glb',
        units_file: 'transport/driven-hitch/connection-units-v1.glb',
        bindings_file: 'transport/driven/hitch-bindings-v2.json',
        vehicle_binding: 'farm_box_w01', web_assets: true,
      },
      source_ids: SOURCES, note, liberty: LIBERTY,
    };
  });
}

export function nextConfig(config, rows = buildRows()) {
  const at = config.rows.findIndex(row => row.scene === '1835');
  const others = config.rows.filter(row => row.scene !== '1835');
  const i = at < 0 ? others.length : at;
  return { ...config, rows: [...others.slice(0, i), ...rows, ...others.slice(i)] };
}

async function audit(rows) {
  const { conflictZones } = await import('../renderers/web/js/transport-crossings.js');
  const { footprintAt, overlaps } = await import('../renderers/web/js/transport-crossings.js');
  const index = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sidecars/1835/index.json'), 'utf8'));
  const prints = index.structures.map(s => {
    try {
      const sc = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', s.sidecar), 'utf8'));
      const pts = footprintWorld(sc);
      if (pts.length < 3) return null;
      const es = pts.map(p => p[0]), ns = pts.map(p => p[1]);
      return { id: s.id, corners: pts, w: Math.min(...es), e: Math.max(...es), s: Math.min(...ns), n: Math.max(...ns) };
    } catch { return null; }
  }).filter(Boolean);
  let bad = 0;
  for (const row of rows) {
    const route = routeFor(row.route);
    const hits = new Map();
    for (let s = 0; s < route.length; s += .5) {
      const fp = footprintAt(route, row, s, 0.3);
      for (const p of prints) if (p.corners.length === 4 && overlaps(fp, p)) hits.set(p.id, (hits.get(p.id) ?? 0) + 1);
      for (const p of prints) if (p.corners.length !== 4 && !(fp.e < p.w || p.e < fp.w || fp.n < p.s || p.n < fp.s)) hits.set(`~${p.id}`, (hits.get(`~${p.id}`) ?? 0) + 1);
    }
    console.log(`${row.id}: ${route.length.toFixed(0)} m, hours ${row.hours.join('-')}, stops ${row.stops.map(s => `${s.label}@${s.distance_m}`).join(', ') || 'none'}${hits.size ? `, HITS ${[...hits].map(([k, v]) => `${k}×${v}`).join(' ')}` : ''}`);
    if (hits.size) bad++;
  }
  // The 1835 ground, read as the scene reads it for its teams: the committed heightfield,
  // bilinear (terrain.js sample), and smoothed for wheels and hooves (transport-ground.js).
  const { createSmoothedGround } = await import('../renderers/web/js/transport-ground.js');
  const { teamSupportAt, certifiedHorseSupportDomain } = await import('../renderers/web/js/transport-support.js');
  const { preflightTransportRoute } = await import('../renderers/web/js/transport-loop.js');
  const dir = path.join(ROOT, 'data/terrain/epochs/e1834_harbor_cut');
  const hf = JSON.parse(fs.readFileSync(path.join(dir, 'heightfield.json'), 'utf8'));
  const raw = new Int16Array(fs.readFileSync(path.join(dir, 'heightfield.bin')).buffer.slice(0));
  const cells = Float32Array.from(raw.subarray(0, hf.cols * hf.rows), v => v * hf.scale + hf.offset);
  const bilinear = (e, n) => {
    const gx = (e - hf.origin_e) / hf.cell_m, gy = (n - hf.origin_n) / hf.cell_m;
    const x0 = Math.min(Math.floor(gx), hf.cols - 2), y0 = Math.min(Math.floor(gy), hf.rows - 2), fx = gx - x0, fy = gy - y0;
    const r0 = y0 * hf.cols, r1 = r0 + hf.cols;
    return (cells[r0 + x0] * (1 - fx) + cells[r0 + x0 + 1] * fx) * (1 - fy) + (cells[r1 + x0] * (1 - fx) + cells[r1 + x0 + 1] * fx) * fy;
  };
  const smooth = createSmoothedGround({ sample: bilinear, grid: { cellM: hf.cell_m, originE: hf.origin_e, originN: hf.origin_n } });
  const config = JSON.parse(fs.readFileSync(FILE, 'utf8'));
  const spec = config.horse_models.current26_walk_v2;
  const domain = certifiedHorseSupportDomain(spec, JSON.parse(fs.readFileSync(path.join(ROOT, 'data', spec.support_domain.certificate_file), 'utf8')));
  for (const row of rows) {
    for (const [label, ground] of [['bilinear', bilinear], ['smoothed', smooth]]) {
      try {
        const reading = preflightTransportRoute({ row, route: routeFor(row.route), heightAt: ground, clear: () => true,
          support: pose => teamSupportAt(row, pose, ground, domain) });
        console.log(`  ${row.id} ${label}: ${reading.status} wheel gap ${(reading.maximum_wheel_gap_m * 1000).toFixed(1)} mm`);
      } catch (error) { console.log(`  ${row.id} ${label}: FAIL ${error.message}`); if (label === 'smoothed') bad++; }
    }
  }
  const circuits = rows.map(row => ({ id: row.id, row, route: routeFor(row.route) }));
  const zones = conflictZones(circuits);
  const long = zones.map(z => ({ z, len: Math.max(...Object.values(z.at).map(([a, b]) => b - a)) })).filter(x => x.len > 40);
  console.log(`crossings: ${zones.length} zones; longest ${Math.max(0, ...zones.map(z => Math.max(...Object.values(z.at).map(([a, b]) => b - a)))).toFixed(1)} m`);
  for (const { z, len } of long) console.log(`  LONG ${z.a} | ${z.b}: ${len.toFixed(1)} m`);
  return bad + long.length;
}

async function main() {
  const check = process.argv.includes('--check');
  const config = JSON.parse(fs.readFileSync(FILE, 'utf8'));
  const want = buildRows();
  if (process.argv.includes('--audit')) { process.exit(await audit(want) ? 1 : 0); }
  if (check) {
    const have = config.rows.filter(row => row.scene === '1835');
    if (JSON.stringify(have) !== JSON.stringify(want)) {
      console.error('lay_driven_wagons_1835: the 1835 rows of loops.json differ; run node tools/lay_driven_wagons_1835.mjs');
      process.exit(1);
    }
    console.log(`lay_driven_wagons_1835: ${want.length} 1835 wagon rows current`);
    return;
  }
  fs.writeFileSync(FILE, `${JSON.stringify(nextConfig(config, want), null, 2)}\n`);
  for (const row of want) console.log(`${row.id}: ${routeFor(row.route).length.toFixed(1)} m, stops ${row.stops.map(s => s.distance_m).join(', ')}`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
