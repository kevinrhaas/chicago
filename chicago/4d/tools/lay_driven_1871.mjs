#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/** 1871's moving teams, written into data/transport/driven/loops.json (T-3690).
 *
 * The owner, 2026-11-19: "1871 people, horses and wagons on every street", reusing "the 1835 town
 * wagons (farm-box teams, rough_road ruts mode), horses and riders", and "No horse stands
 * mid-street. No vehicle moves without its driver. Vehicles stop or steer round obstacles."
 *
 * WHAT. Sunday 8 October 1871: the stores shut, the drays and lumber wagons of the week standing
 * in their barns. What was out on the streets on a Sunday afternoon were the wagons that never
 * stopped (the milkman's, the express companies' and the hotels' baggage wagons meeting the
 * trains, the grocers' and the breweries' for the beer gardens, the livery stables' and the hay
 * for the barns) and the city's carriages and horse cars. These are the wagons: the photographic
 * farm-box wagon the 1812 and 1835 towns drive (Old Cart, Lyskilde, CC BY 4.0, adapted:
 * renderers/web/transport/farm-box-master/), its driver walking at the near horse's head as the
 * 1835 teamsters do. Phones and Light take its far level, and every row is `streamed`
 * (town-transport.js): only the teams near the visitor are built.
 *
 * WHERE. data/transport/driven/drivers_1871.json: each team a round of four platted streets,
 * clockwise, so its corners are right turns about its own block. It keeps LANE_M right of the
 * crown where the carriageway allows, and less on a narrower one (the row's `lanes_m`: half the
 * carriageway less 5.5 m), so its 17 m turn (the wagon steers to 8 degrees) stays on the roadway
 * of the two streets it joins. The lattice's reconstructed streets carry no round. Rounds share no street in the same direction. A team never stands at a door (no
 * `stops`): it halts only where its way is held (transport-crossings.js, the visitor, a horse),
 * so no team stands in the street with nobody at its head. The roadways are the context city's
 * level ribbons (wood block), so a team stands on the certified level plane, not in ruts: its
 * wheels and hooves read the roadway ribbon alone (town-1871.js roadHeightOf), never the walk
 * that crosses it at a corner.
 *
 * WHO. Each team's driver is a carded person of the 1871 town (tools/town_people_1871.py, his
 * household from the row's `home_hub`), out with his team all day (the `driver` routine), so he is
 * never also at home or in the crowd.
 *
 * `--check` refuses a loops.json whose 1871 rows differ from what this writes; `--audit` walks
 * each round against the context city's buildings and its walks.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { routeFor } from '../renderers/web/js/transport-loop.js';
import { fit } from './lay_driven_wagons_1835.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const FILE = path.join(ROOT, 'data/transport/driven/loops.json');
const DRIVERS = path.join(ROOT, 'data/transport/driven/drivers_1871.json');
const INSIDE = path.join(ROOT, 'data/humans/inside_1871.json');
const LIBERTY = 'L-1871-town-traffic';
const LANE_M = 3.0;
const CORNER_R = 17;
const CART = {
  file: 'transport/farm-box-master/farm-box-near.glb',
  sha256: 'a1e8365d6369c417f86afda3a316d54a1a8b8591e729d6f23d2f7d75244bbf8d',
  light_file: 'transport/farm-box-master/farm-box-far.glb',
  light_sha256: '097c293885341c4d166c0121b921da3e89846cd04b3c6507576401e96d568a25',
};
// The farm-box wagon's measured interface, as the 1812 and 1835 wagons carry it.
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
const SOURCES = ['edwards_chicago_directory_1871', 'census_1870_us_vol1', 'mitchell_1870_chicago_map', 'chicago_public_works_1871'];
// The driver routine's hours out with the team (tools/town_people_1871.py "driver"), a little inside them.
const OUT_FROM = 6, OUT_TO = 20;

/** The round's lane: each leg moved right of its direction (LANE_M, or the leg's own entry of
 * `off` on a narrower street), corners where the moved legs meet. */
export function lane(pts, off = LANE_M) {
  const offs = Array.isArray(off) ? off : pts.map(() => off);
  const n = pts.length;
  const legs = pts.map((p, i) => {
    const q = pts[(i + 1) % n], L = Math.hypot(q[0] - p[0], q[1] - p[1]);
    const d = [(q[0] - p[0]) / L, (q[1] - p[1]) / L];
    return { p, d, r: [d[1], -d[0]] };
  });
  return legs.map((leg, i) => {
    const prev = legs[(i + n - 1) % n];
    const oa = offs[(i + n - 1) % n], ob = offs[i];
    const pa = [prev.p[0] + prev.r[0] * oa, prev.p[1] + prev.r[1] * oa];
    const pb = [leg.p[0] + leg.r[0] * ob, leg.p[1] + leg.r[1] * ob];
    const det = prev.d[0] * leg.d[1] - prev.d[1] * leg.d[0];
    const t = ((pb[0] - pa[0]) * leg.d[1] - (pb[1] - pa[1]) * leg.d[0]) / det;
    return [Math.round((pa[0] + prev.d[0] * t) * 100) / 100, Math.round((pa[1] + prev.d[1] * t) * 100) / 100];
  });
}

export function buildRows() {
  const drivers = JSON.parse(fs.readFileSync(DRIVERS, 'utf8')).drivers;
  const inside = JSON.parse(fs.readFileSync(INSIDE, 'utf8')).people;
  const byRow = new Map(inside.filter(p => p.drives).map(p => [p.drives, p]));
  // The ride bar names the wagon by its driver's first name, or by his surname where two
  // drivers share one: every team has its own ride name (test_transport_boarding.mjs).
  const firsts = new Map();
  for (const p of byRow.values()) { const f = p.name.split(' ')[0]; firsts.set(f, (firsts.get(f) ?? 0) + 1); }
  return drivers.map((d, k) => {
    const who = byRow.get(d.row);
    if (!who?.asset_id) throw Error(`lay_driven_1871: ${d.row} has no driver in data/humans/inside_1871.json (run tools/town_people_1871.py)`);
    const points = lane(fit(d.corners, CORNER_R), d.lanes_m ?? LANE_M);
    const spec = { kind: 'path', corner_radius_m: CORNER_R, points_enu_m: points };
    const route = routeFor(spec);
    const shift = Number(who.shift) || 0;
    const first = who.name.split(' ')[0];
    const called = firsts.get(first) > 1 ? `${who.name.split(' ').at(-1)}` : first;
    const note = `${who.name} drives ${d.words} round ${d.streets[0].replace(/ Street| Avenue/, '')}, ${d.streets[2].replace(/ Street| Avenue/, '')}, ${d.streets[1].replace(/ Street| Avenue/, '')} and ${d.streets[3].replace(/ Street| Avenue/, '')} on the Sunday afternoon. No source names him or his round: he, his trade, his team, its wagon and its hours are reconstructed for the 1871 city's Sunday traffic (see ${LIBERTY}).`;
    return {
      ...VEHICLE,
      id: d.row, name: `${d.name}, ${who.name} at the horses' heads`, ride_name: `${called}'s wagon`, scene: '1871',
      driver_mode: 'on_foot', streamed: true,
      route: spec, stops: [],
      initial_distance_m: Math.round(route.length * ((k * 0.37) % 1) * 4) / 4,
      hours: [OUT_FROM + shift, OUT_TO + shift],
      vehicle_file: CART.file, vehicle_glb_sha256: CART.sha256,
      vehicle_file_light: CART.light_file, vehicle_glb_sha256_light: CART.light_sha256,
      driver_asset: who.asset_id,
      person_id: who.person, replace_human_instance: `hi_inside_${who.person}`,
      driver_instance: {
        person_id: who.person,
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
  const others = config.rows.filter(row => row.scene !== '1871');
  return { ...config, rows: [...others, ...rows] };
}

async function audit(rows) {
  const { footprintAt } = await import('../renderers/web/js/transport-crossings.js');
  const ctx = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/context/1871.json'), 'utf8'));
  const cells = new Map(), CELL = 64;
  for (const b of ctx.buildings) {
    const [e, n] = [b.e, b.n], r = Math.hypot(b.width_m, b.depth_m) / 2;
    const th = -b.bearing_deg * Math.PI / 180, c = Math.cos(th), s = Math.sin(th);
    const rec = { e, n, c, s, w: b.width_m, d: b.depth_m };
    for (let i = Math.floor((e - r) / CELL); i <= Math.floor((e + r) / CELL); i++)
      for (let j = Math.floor((n - r) / CELL); j <= Math.floor((n + r) / CELL); j++) {
        const key = `${i},${j}`; if (!cells.has(key)) cells.set(key, []); cells.get(key).push(rec);
      }
  }
  const inBuilding = (e, n) => (cells.get(`${Math.floor(e / CELL)},${Math.floor(n / CELL)}`) ?? []).some(r => {
    const dx = e - r.e, dz = -(n - r.n), x = r.c * dx - r.s * dz, z = r.s * dx + r.c * dz;
    return Math.abs(x) < r.w / 2 && Math.abs(z) < r.d / 2;
  });
  const walks = ctx.walk_surfaces.filter(s => s.kind === 'walk');
  const onWalk = (e, n) => walks.some(s => {
    const de = s.b[0] - s.a[0], dn = s.b[1] - s.a[1], L = Math.hypot(de, dn);
    const t = ((e - s.a[0]) * de + (n - s.a[1]) * dn) / L;
    return t > 0 && t < L && Math.abs((-(e - s.a[0]) * dn + (n - s.a[1]) * de) / L) < s.width_m / 2;
  });
  let bad = 0;
  for (const row of rows) {
    const route = routeFor(row.route);
    let hits = 0, walk = 0;
    for (let s = 0; s < route.length; s += 1) {
      const fp = footprintAt(route, row, s, 0);
      for (const [e, n] of fp.corners ?? []) { if (inBuilding(e, n)) hits++; if (onWalk(e, n)) walk++; }
    }
    console.log(`${row.id}: ${route.length.toFixed(0)} m, hours ${row.hours.join('-')}${hits ? `, BUILDING ${hits}` : ''}${walk ? `, walk ${walk}` : ''}`);
    if (hits) bad++;
  }
  return bad;
}

async function main() {
  const config = JSON.parse(fs.readFileSync(FILE, 'utf8'));
  const want = buildRows();
  if (process.argv.includes('--audit')) process.exit(await audit(want) ? 1 : 0);
  if (process.argv.includes('--check')) {
    const have = config.rows.filter(row => row.scene === '1871');
    if (JSON.stringify(have) !== JSON.stringify(want)) {
      console.error('lay_driven_1871: the 1871 rows of loops.json differ; run node tools/lay_driven_1871.mjs');
      process.exit(1);
    }
    console.log(`lay_driven_1871: ${want.length} 1871 wagon rows current`);
    return;
  }
  fs.writeFileSync(FILE, `${JSON.stringify(nextConfig(config, want), null, 2)}\n`);
  for (const row of want) console.log(`${row.id}: ${routeFor(row.route).length.toFixed(1)} m`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
