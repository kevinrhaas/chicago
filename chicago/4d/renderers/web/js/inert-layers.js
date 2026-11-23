// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * inert-layers.js — the empty form of each layer a scene may not list (T-3732).
 *
 * WHY. Every one of these layers is drawn by one year only (the 1904 street grid, parkway
 * elms, gas lamps, yards, Illinois Central and context city; the 1812 and 1835 shore's
 * crossings are their own list), and its factory, handed no data base, returns an empty
 * layer with nothing in it. Until T-3732 main.js imported every factory statically, so the
 * 1835 first visit downloaded 0.16 MB of 1904 code to be told "nothing here": nine modules,
 * each calling one or two functions of the dozens it carries (Chromium's coverage of the
 * boot, docs/SITE-BUDGET.md § 4s). main.js now imports a layer's module only when the scene
 * lists the layer, and builds the same empty layer from here when it does not.
 *
 * ONE SOURCE. Each module's factory starts from the builder below (`const out = …`) and
 * fills it in, so the empty layer main.js stands in is the same object the module itself
 * returns when it has nothing to draw, field for field. `tools/test_inert_layers.mjs`
 * holds the two equal and holds main.js to importing these modules only on demand.
 *
 * This module imports three alone, which the boot already holds: it adds nothing to fetch.
 */
import * as THREE from 'three';

const named = (name) => { const group = new THREE.Group(); group.name = name; return group; };

/** street-grid.js createStreetGrid: the 1904 carriageways, walks, alleys and parcels. */
export const inertStreetGrid = () => ({
  group: named('street-grid'),
  grid: null,
  surfaces: null,
  census: { carriageways: 0, faces: 0, alleys: 0, parcels: 0, triangles: 0, surfaced: 0, textured: 0 },
  parcelAt: () => null,
  carriagewayHeight: () => null,
  pedestrianHeight: () => null,
  pedestrianSupportReading: () => ({ initialized: false, owned_buffer_bytes: 0, duplicated_xyz_bytes: 0 }),
  setLotLines: () => {},
  pickAt: () => null,
  dispose: () => {},
});

/** street-trees.js createStreetTrees: the parkway elms. */
export const inertStreetTrees = ({ mode = 'summer', detail = 'full' } = {}) => ({
  group: named('street-trees'),
  stats: { trees: 0, young: 0, triangles: 0, drawCalls: 0, mode, detail, crowns: 0, context: 0 },
  records: [],
  pickAt: () => null, update() {}, setMode: async () => {}, setDetail: async () => {}, dispose() {},
});

/** street-furniture.js createStreetFurniture: the gas lamps and hydrants. */
export const inertStreetFurniture = ({ detail = 'full' } = {}) => ({
  group: named('street-furniture'),
  stats: { items: 0, lamps: 0, hydrants: 0, near: 0, far: 0, hydrantsDrawn: 0, triangles: 0, drawCalls: 0, detail },
  records: [],
  pickAt: () => null, update() {}, setDetail() {}, cardFor: () => null, dispose() {},
});

/** back-yards.js createBackYards: the house lots' back and side yards. */
export const inertBackYards = ({ detail = 'full', season = 'summer' } = {}) => ({
  group: named('back-yards'),
  stats: { lots: 0, surfaces: 0, doors: 0, stoops: 0, posts: 0, crops: 0, plants: 0, triangles: 0,
    drawCalls: 0, meshes: 0, chunks: 0, textured: 0, flat: 0, fixtureBoxes: 0, detail, season },
  records: [], doc: null,
  pickAt: () => null, cardFor: () => null, update() {}, setDetail() {}, setSeason() {}, settle() {}, dispose() {},
  /** The stoops as walker decks (stoopDecks), laid once with the first fixtures. */
  stairDecks: [],
});

/** front-yards.js createFrontYards: the lawns, shrubs, beds and creeper. */
export const inertFrontYards = ({ detail = 'full', mode = 'summer' } = {}) => ({
  group: named('front-yards'),
  stats: { lots: 0, shrubs: 0, trees: 0, beds: 0, bedPlants: 0, creeper: 0, plants: 0,
    triangles: 0, drawCalls: 0, detail, mode },
  records: [],
  pickAt: () => null, update() {}, setDetail: async () => {}, setSeason: async () => {}, settle() {},
  cardFor: () => null, dispose() {},
});

/** railway.js createRailway: the Illinois Central along the lake. */
export const inertRailway = () => ({
  group: named('railway'),
  data: null,
  census: { tracks: 0, track_m: 0, ties: 0, tufts: 0, zones: 0, nearZones: 0, textured: false, rocks: 0, piles: 0, edge_m: 0 },
  update: () => {},
  setDetail: () => {},
  pickAt: () => null,
  dispose: () => {},
});

/** context.js createContext: the 1904 context city's faded stand-ins. */
export const inertContext = () => ({
  group: named('context'), doc: null,
  census: { buildings: 0, trees: 0, dropped: 0, triangles: 0, meshes: 0 },
  pickAt: () => null, setSeason: () => {}, treeStems: () => [], dispose: () => {},
});

/** crossings.js createCrossings: the boats a visitor can take across. */
export const inertCrossings = () => ({
  group: named('crossings'), boats: [], things: [], keepOut: [], riding: null,
  census: { boats: 0, dugout: 0, bark_canoe: 0, skiff: 0, refused: 0 },
  pickAt: () => null, update: () => {}, holdVisitor: () => false, dispose: () => {},
});
