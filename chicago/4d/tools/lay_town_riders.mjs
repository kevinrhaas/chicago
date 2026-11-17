#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/** The town's riders and its stabled saddle horses, written into data/transport/riding/saddle_horses.json.
 *
 * Kevin, 2026-11-17: "for 1835 and 1812 can you add some appropriate number of people seasonally
 * and by time of day looping around town in a horse and some stabled parked horses I could ride,
 * there may be a horse in 1904 also but not tons".
 *
 * HOW MANY. A frontier town went about on horseback: farmers in from the prairie, land agents,
 * the doctor on his rounds, the express from the east, Potawatomi and Métis men coming to trade
 * (Andreas 1884 vol. 1; the 1833-35 Chicago papers). 1835 (3,265 at the November census) gets
 * seven riders, six out on a summer morning and four in winter, the one riding for the doctor the
 * last home at night. 1812 had fewer horses about the fort: the garrison's, the traders' and the
 * Potawatomi's, who kept many; four ride, all by day.
 *
 * WHO. Each rider is an anonymous figure of the year whose clothes sit a saddle cleanly (the
 * settler, the engagé, the private; the 1904 driver as a groom): tools/test_riding.mjs seats every
 * one at walk and trot and holds its skin out of the horse. The figures with a coat's skirts or
 * tails, a blanket or a breechcloth (the trader, the officers, the Potawatomi man) hang them through
 * the horse's back as they are rigged, so they do not ride yet. By 1904 Prairie Avenue went in carriages, and a groom
 * exercising a carriage horse is the one rider. The counts, rounds, hours and seasons are
 * reconstructed (L-town-riders-3560).
 *
 * WHERE. In 1835 each rider goes round a ring of the worked streets clockwise, 3.5 m right of
 * the crown, on the kerb side of the wagons (which keep 1 m right, lay_driven_wagons_1835.mjs),
 * so a wagon and a rider on the same street pass side by side. In 1812 and 1904 a rider takes a
 * wagon's or carriage's own round, 2.5 m to the right of it. A rider gives way to the teams, the
 * other riders and the visitor (riding.js); the rounds are checked on the scene's own ground by
 * `api.riding.auditRounds()` in the browser.
 *
 * STABLED. A saddle horse stands tied outside each named stable (the hotels' and taverns' stables
 * of 1835, the fort's outer stables and Kinzie's horse mill in 1812, a Prairie Avenue stable in
 * 1904), on the side toward its street, along the wall. Every one can be mounted.
 *
 * `--check` refuses a saddle_horses.json whose generated rows differ from what this file writes.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { routeFor } from '../renderers/web/js/transport-loop.js';
import { streetsOf, ring, fit, footprintWorld } from './lay_driven_wagons_1835.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const FILE = path.join(ROOT, 'data/transport/riding/saddle_horses.json');
const LOOPS = path.join(ROOT, 'data/transport/driven/loops.json');
const LIBERTY = 'L-town-riders-3560';
const TOOL = 'tools/lay_town_riders.mjs';
const R = 6;               // a horse turns tighter than a wagon; the path minimum
const ALL = ['spring', 'summer', 'fall', 'winter'], OPEN = ['spring', 'summer', 'fall'];
const round2 = p => [Math.round(p[0] * 100) / 100, Math.round(p[1] * 100) / 100];

const RIDERS = [
  // 1835: rings of the worked streets [west, east, north, south].
  { id: 'rider_farmer_1835', scene: '1835', name: 'A farmer in from the prairie', asset: 'settler_1812',
    ring: ['franklin', 'lasalle', 'lake', 'washington'], hours: [7, 16], seasons: OPEN, pace: 1.45, at: .1,
    why: 'Farmers rode in from the Des Plaines and the Fox to trade and to see the land office.' },
  { id: 'rider_land_office_1835', scene: '1835', name: 'A settler come to the land office', asset: 'settler_1812',
    ring: ['lasalle', 'clark', 'lake', 'washington'], hours: [8, 18], seasons: ALL, pace: 1.4, at: .55,
    why: 'The town lots and the government land sold and resold all year in 1835; buyers rode in to bid and to file.' },
  { id: 'rider_doctor_1835', scene: '1835', name: 'A man riding for the doctor', asset: 'settler_1812',
    ring: ['market', 'wells', 'lake', 'washington'], hours: [6, 23], seasons: ALL, pace: 1.5, at: .3,
    why: 'A rider fetched the doctor to a patient, by night as well as by day.' },
  { id: 'rider_express_1835', scene: '1835', name: 'The express rider', asset: 'settler_1812',
    ring: ['franklin', 'clark', 'randolph', 'washington'], hours: [8, 12], seasons: ALL, pace: 1.5, at: .8,
    why: 'Letters and the eastern papers came on by horse between the stages and the boats.' },
  { id: 'rider_engage_1835', scene: '1835', name: "A Métis trader's man on horseback", asset: 'engage_1812',
    ring: ['clinton', 'canal', 'fulton', 'washington'], hours: [8, 18], seasons: OPEN, pace: 1.4, at: .2,
    why: 'The Métis and French Canadian men of the old trade still carried for the traders in 1835, mounted as often as afoot.' },
  { id: 'rider_north_side_1835', scene: '1835', name: 'A boatman riding the North Side', asset: 'engage_1812',
    ring: ['franklin_north', 'clark_north', 'kinzie', 'north_water'], hours: [9, 17], seasons: ALL, pace: 1.4, at: .6,
    why: 'The forwarding houses on North Water sent their men between the warehouses and the river.' },
  { id: 'rider_evening_1835', scene: '1835', name: 'A young man out riding in the evening', asset: 'settler_1812',
    ring: ['market', 'franklin', 'lake', 'washington'], hours: [17, 21.5], seasons: ['spring', 'summer'], pace: 1.5, at: .45,
    why: 'A summer evening ride along the river streets.' },
  // 1812 and 1904: a team's own round, `offset_m` to its right.
  { id: 'rider_soldier_1812', scene: '1812', name: 'A soldier of the garrison riding out', asset: 'private_first_infantry_1812',
    follow: 'shore_road_wagon_haul_1812', offset_m: 2.5, hours: [7, 19], seasons: ALL, pace: 1.45, at: .5,
    why: 'The fort kept horses, and its men rode the shore road to the farms south of the fort with messages and stores.' },
  { id: 'rider_engage_1812', scene: '1812', name: 'A Métis engagé riding to the traders', asset: 'engage_1812',
    follow: 'fort_wagon_loop_1812', offset_m: 3, hours: [6, 20], seasons: OPEN, pace: 1.4, at: .25,
    why: 'The traders\' Métis and French Canadian men rode between the fort, the factory and the houses about it.' },
  { id: 'rider_officers_horse_1812', scene: '1812', name: "A soldier exercising an officer's horse", asset: 'private_first_infantry_1812',
    follow: 'fort_wagon_loop_1812', offset_m: 3, hours: [8, 18], seasons: ALL, pace: 1.4, at: .75,
    why: 'The officers\' horses were kept at the fort and walked out by the men.' },
  { id: 'rider_settler_1812', scene: '1812', name: 'A settler riding the shore road', asset: 'settler_1812',
    follow: 'shore_road_wagon_haul_1812', offset_m: 2.5, hours: [6, 17], seasons: OPEN, pace: 1.4, at: .05,
    why: 'The families south of the fort came up the shore road on horseback.' },
  { id: 'rider_groom_1904', scene: '1904', name: 'A groom exercising a carriage horse', asset: 'anonymous_working_driver_1904',
    follow: 'prairie_driven_brougham_north_loop_1904', offset_m: 2.5, hours: [7, 11], seasons: OPEN, pace: 1.4, at: .5,
    why: 'Prairie Avenue went in carriages; its grooms rode the carriage horses out in the morning.' },
];

const STABLED = [
  ['1835', 'sauganash_hotel_stable'], ['1835', 'tremont_house_1_stable'], ['1835', 'western_hotel_stable'],
  ['1835', 'wolf_point_tavern_stable'], ['1835', 'new_york_house_stable'], ['1835', 'steamboat_hotel_stable'],
  ['1812', 'first_fort_outer_stable_north'], ['1812', 'first_fort_outer_stable_south'], ['1812', 'kinzie_horse_mill_1812'],
  ['1904', 'dexter_house_1721_prairie_coach_house'],
];

// ---- geometry -----------------------------------------------------------------------------
/** A closed polyline moved `off` metres to the right of travel, its corners where the moved legs meet. */
function offsetLoop(pts, off) {
  const n = pts.length;
  const legs = pts.map((p, i) => {
    const q = pts[(i + 1) % n], L = Math.hypot(q[0] - p[0], q[1] - p[1]);
    const d = [(q[0] - p[0]) / L, (q[1] - p[1]) / L];
    return { p, d, r: [d[1], -d[0]] };
  });
  return legs.map((leg, i) => {
    const prev = legs[(i + n - 1) % n];
    const pa = [prev.p[0] + prev.r[0] * off, prev.p[1] + prev.r[1] * off], pb = [leg.p[0] + leg.r[0] * off, leg.p[1] + leg.r[1] * off];
    const det = prev.d[0] * leg.d[1] - prev.d[1] * leg.d[0];
    if (Math.abs(det) < 1e-6) return pb;
    const t = ((pb[0] - pa[0]) * leg.d[1] - (pb[1] - pa[1]) * leg.d[0]) / det;
    return [pa[0] + prev.d[0] * t, pa[1] + prev.d[1] * t];
  });
}

/** A team row's round as path corners (a rounded block's four corners, or the path's own). */
function cornersOf(route) {
  if (route.kind === 'path') return route.points_enu_m.map(p => [...p]);
  if (route.kind !== 'rounded_block') throw Error(`${TOOL}: cannot follow a ${route.kind} round`);
  const [w, s, e, n] = route.bounds_enu_m, [oe, on] = route.origin_enu_m ?? [0, 0], th = route.rotation_rad ?? 0;
  const c = Math.cos(th), sn = Math.sin(th);
  // transport-loop.js roundedBlockRoute: clockwise false runs counter-clockwise (east along the south side).
  const local = route.clockwise ? [[w, n], [e, n], [e, s], [w, s]] : [[w, s], [e, s], [e, n], [w, n]];
  return local.map(([x, y]) => [oe + x * c - y * sn, on + x * sn + y * c]);
}

function riderRoute(spec, streets, teams) {
  let pts;
  if (spec.ring) pts = offsetLoop(fit(ring(streets, spec.ring), R + 2), 3.5);
  else {
    const team = teams.get(spec.follow);
    if (!team) throw Error(`${TOOL}: ${spec.id} follows ${spec.follow}, not in loops.json`);
    pts = offsetLoop(cornersOf(team.route), spec.offset_m);
  }
  const route = { kind: 'path', corner_radius_m: R, points_enu_m: fit(pts.map(round2), R) };
  routeFor(route); // throws if the corners are too close for their bends
  return route;
}

// ---- stabled horses ---------------------------------------------------------------------
const inside = (p, poly) => {
  let hit = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > p[1]) !== (yj > p[1]) && p[0] < (xj - xi) * (p[1] - yi) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
};
function nearestOn(lines, p) {
  let best = null;
  for (const line of lines) for (let i = 0; i + 1 < line.length; i++) {
    const a = line[i], b = line[i + 1], dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy || 1;
    const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2));
    const q = [a[0] + t * dx, a[1] + t * dy], d = Math.hypot(q[0] - p[0], q[1] - p[1]);
    if (!best || d < best.d) best = { q, d, dir: [dx / Math.sqrt(L2), dy / Math.sqrt(L2)] };
  }
  return best;
}
function stabledRow(scene, id, lines) {
  const sc = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sidecars', scene, `${id}.json`), 'utf8'));
  const poly = footprintWorld(sc);
  if (poly.length < 3) throw Error(`${TOOL}: ${id} has no footprint`);
  const c = poly.reduce((s, p) => [s[0] + p[0] / poly.length, s[1] + p[1] / poly.length], [0, 0]);
  const near = nearestOn(lines, c);
  const to = [near.q[0] - c[0], near.q[1] - c[1]], L = Math.hypot(...to), u = [to[0] / L, to[1] / L];
  // Out of the walls toward the street, then 2.2 m clear of them.
  let s = 0;
  while (inside([c[0] + u[0] * s, c[1] + u[1] * s], poly) && s < 60) s += .1;
  const at = round2([c[0] + u[0] * (s + 2.2), c[1] + u[1] * (s + 2.2)]);
  // Tied along the wall, facing the way the street runs.
  const bearing = Math.round(((Math.atan2(near.dir[0], near.dir[1]) * 180 / Math.PI) + 360) % 360 * 100) / 100;
  const name = String(sc.name ?? id).replace(/^The /, '');
  return { id: `saddle_horse_${id}`, scene, name: `Saddle horse at ${name.replace(/^First Fort Dearborn — /, 'the fort\'s ')}`,
    short_name: 'the saddle horse', at, bearing_deg: bearing, coat_row: `saddle_horse_${id}`.slice(0, 60),
    stable: id, grade: 'reconstructed', liberty: 'L-riding-tack-3560', generated_by: TOOL,
    basis: `Tied outside ${name}, on its street side (${TOOL}). Kevin, 2026-11-17: "some stabled parked horses I could ride". Where it stands, its tack and its coat are reconstructed (${LIBERTY}).` };
}

export function build() {
  const streets = streetsOf();
  const loops = JSON.parse(fs.readFileSync(LOOPS, 'utf8'));
  const teams = new Map(loops.rows.map(r => [r.id, r]));
  const riders = RIDERS.map(spec => {
    const route = riderRoute(spec, streets, teams);
    const length = routeFor(route).length;
    return { id: spec.id, scene: spec.scene, name: spec.name, short_name: spec.name.replace(/^(A|An|The) /, m => m.toLowerCase()),
      asset: spec.asset, coat_row: spec.id, hours: spec.hours, seasons: spec.seasons, speed_m_s: spec.pace,
      route, initial_distance_m: Math.round(length * spec.at * 4) / 4,
      ...(spec.ring ? { ring: spec.ring } : { follows: spec.follow, offset_m: spec.offset_m }),
      grade: 'reconstructed', liberty: LIBERTY, generated_by: TOOL, basis: `${spec.why} Who rides, the round, the hours and the seasons are reconstructed (${LIBERTY}).` };
  });
  const lines = {
    1835: [...streets.values()].map(s => s.path_local_enu_m),
    1812: ['fort_wagon_loop_1812', 'shore_road_wagon_haul_1812'].map(id => { const c = cornersOf(teams.get(id).route); return [...c, c[0]]; }),
    1904: loops.rows.filter(r => r.scene === '1904' && r.route.kind === 'path').map(r => [...r.route.points_enu_m, r.route.points_enu_m[0]]),
  };
  const stabled = STABLED.map(([scene, id]) => stabledRow(scene, id, lines[scene]));
  return { riders, stabled };
}

export function next(config, built = build()) {
  const keep = config.rows.filter(r => r.generated_by !== TOOL);
  return { ...config, rows: [...keep, ...built.stabled], riders: built.riders };
}

async function main() {
  const config = JSON.parse(fs.readFileSync(FILE, 'utf8'));
  const want = next(config);
  if (process.argv.includes('--check')) {
    if (JSON.stringify(config) !== JSON.stringify(want)) {
      console.error(`${TOOL}: saddle_horses.json's riders or stabled horses differ; run node ${TOOL}`);
      process.exit(1);
    }
    console.log(`${TOOL}: ${want.riders.length} riders and ${want.rows.filter(r => r.generated_by === TOOL).length} stabled horses current`);
    return;
  }
  fs.writeFileSync(FILE, `${JSON.stringify(want, null, 2)}\n`);
  for (const r of want.riders) console.log(`${r.id}: ${routeFor(r.route).length.toFixed(0)} m, ${r.hours.join('-')} h, ${r.seasons.join('/')}`);
  for (const r of want.rows.filter(x => x.generated_by === TOOL)) console.log(`${r.id}: ${r.at.join(', ')} facing ${r.bearing_deg}`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
