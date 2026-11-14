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
 * Counter-clockwise because a team keeps to the right of the road: every corner of a
 * counter-clockwise loop is a left turn, swept wide across the crossing street, while a
 * clockwise loop's right turns hug the inside kerb, tighter than this brougham's 8° steering
 * and its 18 m corners allow on these 11-15 m carriageways. Adjacent counter-clockwise loops
 * run opposite ways along the street they share, so Hans meets each newcomer head on in the
 * other lane of 18th or 20th, and their left turns cross at Indiana and at Prairie: there one
 * gives way and waits for the other (transport-crossings.js), twice a lap for each pair.
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

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const FILE = path.join(ROOT, 'data/transport/driven/loops.json');
const GRID = path.join(ROOT, 'data/street_grid/1904.json');
const TEMPLATE = 'prairie_driven_brougham_loop_1904';
const HANS = 'pa1904_otis_f_r_c1900_hans_johnson';
const LIBERTY = 'L-1904-more-carriages-3555';
const CORNER_R = 18;

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
function loopOf(grid, legs) {
  const lanes = legs.map(([id, heading, off]) => lane(grid, id, heading, off));
  const points = lanes.map((l, i) => meet(lanes[(i + lanes.length - 1) % lanes.length], l));
  return { route: { kind: 'path', corner_radius_m: CORNER_R, points_enu_m: points }, sources: [...new Set(lanes.flatMap(l => l.sources))] };
}

const CARRIAGES = [
  {
    id: 'prairie_driven_brougham_north_loop_1904',
    name: 'Carriage driver on Prairie Avenue, 16th to 18th Street',
    person_id: 'pa1904_pullman_mrs_george_m_c1900_henry_windish',
    legs: [['e18th_indiana_prairie', 'east', 3], ['prairie_16_18', 'north', 2.5],
      ['e16th_indiana_prairie', 'west', 2.5], ['indiana_16_18', 'south', 3]],
    speed_m_s: 1.25,
    // He pulls up at his own employer's door, 1729 Prairie (the middle of its frontage).
    stops: [{ label: "the Pullman house's door", at: [1404.1, -3173.8], dwell_s: 45 }],
    initial_distance_m: 561,
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
    name: 'Carriage driver on Prairie Avenue, 20th to 22nd Street',
    person_id: 'pa1904_armour_mrs_philip_d_c1900_joseph_daniels',
    legs: [['e22nd_indiana_calumet', 'east', 3], ['prairie_20_22', 'north', 2.5],
      ['e20th_indiana_calumet', 'west', 3], ['indiana_20_22', 'south', 3]],
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
    note: "Joseph Daniels, coachman in Mrs. Philip D. Armour's household at 2115 Prairie Avenue in the 1900 census, drives a brougham round Prairie, 20th Street and Indiana. The census names him there four years before the scene; this coach, its colours, its team, his livery and the round are reconstructed.",
  },
];
// Hans's own coach keeps its catalogue green and black; it gets the road on it too.
const HANS_FINISH = { seed: 'otis-brougham-1904', gloss: 0.85, dust: 0.4, scuffs: 0.3 };

export function buildRows(config = JSON.parse(fs.readFileSync(FILE, 'utf8')), grid = JSON.parse(fs.readFileSync(GRID, 'utf8'))) {
  const template = config.rows.find(row => row.id === TEMPLATE);
  if (!template || template.person_id !== HANS) throw Error('lay_driven_carriages_1904: Hans\'s brougham row is the template');
  const { vehicle_finish: _, ...base } = template;
  const rows = CARRIAGES.map(spec => {
    const { route, sources } = loopOf(grid, spec.legs);
    const road = routeFor(route); // refuses a road too tight for its corners
    const stops = spec.stops.map(stop => {
      const near = routeDistanceNear(road, ...stop.at);
      if (near.off_m > 3) throw Error(`${spec.id}: stop "${stop.label}" is ${near.off_m.toFixed(1)} m off its road`);
      return { label: stop.label, distance_m: Math.round(near.distance_m * 4) / 4, dwell_s: stop.dwell_s };
    });
    return {
      ...base,
      id: spec.id, name: spec.name, scene: '1904',
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
  for (const key of ['source_lane_intersections_enu_m']) for (const row of rows) delete row[key];
  return { hans: { ...template, vehicle_finish: { ...HANS_FINISH, grade: 'reconstructed', liberty: LIBERTY } }, rows };
}

/** loops.json with Hans's finish and the two rows straight after his; every other row untouched. */
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
    console.log('lay_driven_carriages_1904: Hans\'s finish and 2 more 1904 carriage rows current');
    return;
  }
  fs.writeFileSync(FILE, `${JSON.stringify(next, null, 2)}\n`);
  for (const row of next.rows.filter(r => r.scene === '1904')) console.log(`${row.id}: ${routeFor(row.route).length.toFixed(1)} m, ${JSON.stringify(row.route.points_enu_m ?? row.route.bounds_enu_m)}`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
