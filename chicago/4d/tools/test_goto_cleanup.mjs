#!/usr/bin/env node
// T-2632 (NAV-403): Go to cleanup — filters All · Places · People · Shops & work ·
// Viewpoints, no chip for a kind the scene has none of (QA-14: no "Corners 0" in 1904),
// long names on two lines, and every row's distance and bearing from where you stand.
// Reads the real destinations inventory over fixtures and the CSS; the smoke (part 13)
// opens Go to in the Navigator.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createDestinations } from '../renderers/web/js/destinations.js';
import { GO_TO_KINDS, offeredKinds, rowDistance } from '../renderers/web/js/welcome.js';
import { placeDistance, cardinal, arrowTurn } from '../renderers/web/js/goto.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');

// ---- the filters -------------------------------------------------------------------------
assert.deepEqual(GO_TO_KINDS.map(([, l]) => l), ['All', 'Places', 'People', 'Shops & work', 'Viewpoints']);
const terrain = { surfaceHeight: () => 2, isWater: () => false };
const record = (name, fn, e, n) => ({ sidecar: { name, attributes: { function: { value: fn } }, documented_range: { confidence: 'attested' },
  placement: { local_e: e, local_n: n, position_confidence: 'attested' } } });
// A 1904-like scene: houses and a viewpoint, no corners, no people, no firms.
const houses = createDestinations({ terrain, router: null, people: null, index: { intersections: [] },
  scene: { anchors: [{ id: 'prairie', label: 'Prairie Avenue', local_e: 0, local_n: 0, yaw_deg: 0 }] },
  registry: new Map([['glessner_house', record('Glessner House', 'house', 30, 40)]]) });
const offered = offeredKinds(houses).map(([, l]) => l);
assert(!offered.includes('People') && !offered.includes('Shops & work'), `no chip for a kind with nothing in it: ${offered}`);
assert(offered.includes('All') && offered.includes('Places') && offered.includes('Viewpoints'));
assert(!GO_TO_KINDS.some(([, l]) => l === 'Corners'), 'no Corners chip at all; corners stay in All');
// A town with everything offers all five.
const town = createDestinations({ terrain, router: null, index: { intersections: [{ id: 'k', label: 'Kinzie & Canal', local_e: 1, local_n: 1 }] },
  scene: { anchors: [{ id: 'a', label: 'A view', local_e: 0, local_n: 0 }] },
  registry: new Map([['peck_store', record("Peck's Store", 'store', 0, 0)]]),
  people: { people: [{ id: 'peck', name: 'Philip Peck', lives_at: { value: 'peck_store' } }] } });
assert.equal(offeredKinds(town).length, 5, 'a full town offers every filter');
assert(town.search('kinzie').length === 1, 'corners are still found in All');

// ---- distance and bearing from where you stand ----------------------------------------------
const here = { e: 0, n: 0, bearingDeg: 90 };
const d = placeDistance({ e: 30, n: 40 }, here);
assert.equal(d.m, 50);
assert.equal(cardinal(d.bearing), 'NE');
assert.equal(arrowTurn(d, here), Math.round(((d.bearing - 90) % 360 + 360) % 360), 'the arrow turns from the way you face');
assert.deepEqual(rowDistance({ e: 30, n: 40 }, here, 'metric'), { here: false, words: '50 m NE', turn: arrowTurn(d, here) });
assert.match(rowDistance({ e: 30, n: 40 }, here, 'imperial').words, /^\d+ ft NE$|^[\d.]+ (mi|yd) NE$/);
assert.deepEqual(rowDistance({ e: 1, n: 1 }, here), { here: true, words: 'here' });
assert.equal(rowDistance({ e: NaN, n: 0 }, here), null, 'no position, no distance');
assert.equal(rowDistance({ e: 1, n: 1 }, null), null, 'nowhere to stand, no distance');

// ---- two-line names, and the drawer's pills hide too ------------------------------------------
const goto = read('renderers/web/css/goto.css');
assert(/\.jump-result \.jump-name \{[\s\S]*?-webkit-line-clamp: 2;[\s\S]*?white-space: normal;/.test(goto), 'the drawer\'s names wrap to two lines');
assert(/\.jump-pill\[hidden\] \{ display: none; \}/.test(goto));
const walk = read('renderers/web/css/walk.css');
assert(/\.welcome-destination strong \{ display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2;/.test(walk), 'Go to\'s names wrap to two lines');
assert(/\.welcome-kinds button\[hidden\] \{ display: none; \}/.test(walk));
assert(/pill\.hidden = id !== 'all' && id !== kind && \(count === 0/.test(read('renderers/web/js/goto.js')), 'the drawer\'s pills hide a kind with nothing in it');
assert(/visitor: \(\) => \(\{ e: walker\.state\.e, n: walker\.state\.n, bearingDeg: walker\.bearingDeg \}\)/.test(read('renderers/web/js/main.js')), 'rows measure from the walker');

console.log('test_goto_cleanup: four filters and All, no empty chips, two-line names, distance and bearing on every row');
