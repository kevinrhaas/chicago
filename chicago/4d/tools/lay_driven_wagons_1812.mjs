#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/** T-3497: the 1812 fort's two wagons, written into data/transport/driven/loops.json.
 *
 * Kevin, 2026-11-08: "add some wagons that are driven by horses and in movement in 1812 just
 * like we have in 1904 ... have some wagons rotating around town on loops ... people taking
 * wagons places". Two rows, both led by a private of Heald's company walking at the near
 * horse's head (an army teamster's way, and no seated pose to solve for the uniform):
 *
 *   - the loop: Elias Mills round the fort's outbuildings, pulling up at the gate's foot,
 *     the stables and the merchant's shop;
 *   - the haul: William Moffett down the shore road to Lee's place and back up to the
 *     armourer's corner north of the fort, standing at each end to load.
 *
 * The roads are hand-laid along the 1812 tracks (corner points below); a stop is named by
 * where it is and resolved here to its distance along the route. `--check` refuses a
 * loops.json whose 1812 rows differ from what this file writes. Rendered-ground, clearance
 * and hoof-support readings of each route run in the browser (town-transport preflight) and
 * in tools/test_transport_loop.mjs's 1812 case.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { routeFor, routeDistanceNear } from '../renderers/web/js/transport-loop.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const FILE = path.join(ROOT, 'data/transport/driven/loops.json');
const LIBERTY = 'L-1812-army-wagons-3497';
const SOURCES = ['quaife_1913', 'kirkland_1893_chicago_massacre', 'kinzie_waubun_1856', 'currey_1912_story_of_old_fort_dearborn'];
const CART = {
  file: 'transport/farm-box-master/farm-box-near.glb',
  sha256: 'a1e8365d6369c417f86afda3a316d54a1a8b8591e729d6f23d2f7d75244bbf8d',
  // Phones and Light take the cart's own mid level (same nodes, 2.2 MB against 5.1 MB).
  light_file: 'transport/farm-box-master/farm-box-mid.glb',
  light_sha256: '6a5fa3f484afbed41d05f055858df57a8163b19ff0057e292449c51ccb360b36',
};
// The farm-box cart's measured interface (same as W01: wheels, axles, tongue, hitch).
const VEHICLE = {
  speed_m_s: 1.3, steering_limit_deg: 8, track_m: 1.21, wheelbase_m: 2.35,
  root_ahead_of_rear_axle_m: 1.175, wheel_radii_m: [0.685, 0.685, 0.535, 0.535],
  team_half_spacing_m: 0.65, horse_offset_m: [0, 0, 3.4987],
  // He walks off the near (left, +x) horse's shoulder, by its head.
  driver_local_m: [1.3, 0, 4.4],
  envelope_local_xz_m: [-1.21, -1.86, 1.75, 5.1],
  envelope_basis: 'Farm-box cart bed, wheels and tongue, the two-horse team at 3.5 m, and the teamster walking 1.3 m off the near side, plus 15 cm.',
};

const loop = {
  id: 'fort_wagon_loop_1812',
  name: 'Fort wagon going round the outbuildings',
  person_id: 'mills_elias',
  replace_human_instance: 'hi_mills_elias_1812',
  route: { kind: 'rounded_block', bounds_enu_m: [1078, 85, 1198, 147], corner_radius_m: 18, clockwise: false },
  stops: [
    { label: "the foot of the fort's south gate", at: [1150, 147], dwell_s: 40 },
    { label: 'the stables', at: [1078, 125], dwell_s: 45 },
    { label: "the merchant's shop", at: [1198, 135], dwell_s: 35 },
  ],
  initial_distance_m: 0,
  note: "Private Elias Mills of Heald's company leads the fort's wagon round its outbuildings on the eve of the evacuation, standing at the gate, the stables and the merchant's shop as if loading. The company had wagons for the march of 15 August (Quaife 1913; Kirkland 1893); this cart, its team, its round and its stops are reconstructed.",
};
const haul = {
  id: 'shore_road_wagon_haul_1812',
  name: "Fort wagon on the shore road to Lee's place",
  person_id: 'moffett_william',
  replace_human_instance: 'hi_moffett_william_1812',
  route: {
    kind: 'path', corner_radius_m: 18,
    points_enu_m: [
      [1225, 60], [1170, 60], [1170, 5],
      [1224, -5], [1220, -60], [1212, -130], [1205, -200], [1195, -255], [1178, -310], [1150, -372],
      [1143, -455], [1095, -455], [1095, -405], [1143, -405],
      [1150, -372], [1178, -310], [1195, -255], [1205, -200], [1212, -130], [1220, -60], [1224, -5],
    ],
  },
  stops: [
    { label: "Lee's house", at: [1145, -437], dwell_s: 60 },
    { label: "the armourer's corner north of the road", at: [1200, 60], dwell_s: 50 },
  ],
  initial_distance_m: 420,
  note: "Private William Moffett of Heald's company drives the fort's wagon down the shore road to the Lee family's house and back, standing at each end as if loading. The road follows the 1812 track south of the fort; the cart, team, timetable and errand are reconstructed.",
};

export function buildRows() {
  return [loop, haul].map(spec => {
    const route = routeFor(spec.route);
    const stops = spec.stops.map(stop => {
      const near = routeDistanceNear(route, ...stop.at);
      if (near.off_m > 3) throw Error(`${spec.id}: stop "${stop.label}" is ${near.off_m.toFixed(1)} m off its road`);
      return { label: stop.label, distance_m: Math.round(near.distance_m * 4) / 4, dwell_s: stop.dwell_s };
    });
    return {
      ...VEHICLE,
      id: spec.id, name: spec.name, scene: '1812', driver_mode: 'on_foot',
      route: spec.route, stops, initial_distance_m: spec.initial_distance_m,
      // His hours (hi_*_1812 behaviour.hours, human-duties.js): out 5:30 to 21:00; the wagon is put up between.
      hours: [5.5, 21],
      vehicle_file: CART.file, vehicle_glb_sha256: CART.sha256,
      vehicle_file_light: CART.light_file, vehicle_glb_sha256_light: CART.light_sha256,
      driver_asset: 'private_first_infantry_1812',
      person_id: spec.person_id, replace_human_instance: spec.replace_human_instance,
      driver_instance: {
        person_id: spec.person_id,
        interaction: { opens: 'resident_card', selectable: true },
        provenance: { grade: 'reconstructed', basis: spec.note, liberty: LIBERTY },
        review_required: false,
      },
      horse_model: 'current26_walk_v2',
      hitch: {
        harness_file: 'transport/driven-hitch/current26-collar-girth-v2.glb',
        units_file: 'transport/driven-hitch/connection-units-v1.glb',
        bindings_file: 'transport/driven/hitch-bindings-v2.json',
        vehicle_binding: 'farm_box_w01', web_assets: true,
      },
      source_ids: SOURCES, note: spec.note, liberty: LIBERTY,
    };
  });
}

function main() {
  const check = process.argv.includes('--check');
  const config = JSON.parse(fs.readFileSync(FILE, 'utf8'));
  const want = buildRows();
  const others = config.rows.filter(row => row.scene !== '1812');
  const next = { ...config, rows: [...others, ...want] };
  const text = `${JSON.stringify(next, null, 2)}\n`;
  if (check) {
    const have = config.rows.filter(row => row.scene === '1812');
    if (JSON.stringify(have) !== JSON.stringify(want)) {
      console.error('lay_driven_wagons_1812: the 1812 rows of loops.json differ; run node tools/lay_driven_wagons_1812.mjs');
      process.exit(1);
    }
    console.log(`lay_driven_wagons_1812: ${want.length} 1812 wagon rows current`);
    return;
  }
  fs.writeFileSync(FILE, text);
  for (const row of want) console.log(`${row.id}: ${routeFor(row.route).length.toFixed(1)} m, stops ${row.stops.map(s => s.distance_m).join(', ')}`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
