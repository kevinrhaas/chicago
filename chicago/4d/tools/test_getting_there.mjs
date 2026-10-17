#!/usr/bin/env node
// T-2652 (NAV-702): getting there — Teleport, Ride there or Fly over — one choice that Go
// to, the Map and Jaunts all use. Reads js/getting-there.js, then drives the real Jaunt
// controller (js/jaunts.js) over a fake ride to show each choice is the mode it rides
// between stops. No browser; the smoke (part 13) makes the choice in a page.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { STYLES, styleOf, styleWords, jauntModeFor } from '../renderers/web/js/getting-there.js';
import { createJaunts } from '../renderers/web/js/jaunts.js';
import { PACES } from '../renderers/web/js/travel-settings.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const json = (p) => JSON.parse(read(p));
const labels = Object.fromEntries(Object.entries(PACES).map(([k, v]) => [k, v.label]));

// ---- the three choices -----------------------------------------------------------------
assert.deepEqual(STYLES.map((s) => s.label), ['Teleport', 'Ride there', 'Fly over']);
assert.deepEqual(['instantly', 'walk', 'run', 'horse', 'fly'].map(styleOf), ['instantly', 'ride', 'ride', 'ride', 'fly']);
assert.equal(styleWords({ travelMode: 'instantly', pace: 'horse' }, labels), 'Teleport');
assert.equal(styleWords({ travelMode: 'horse', pace: 'horse' }, labels), 'Ride there · Horse');
assert.equal(styleWords({ travelMode: 'run', pace: 'run' }, labels), 'Ride there · Run');
assert.equal(styleWords({ travelMode: 'fly', pace: 'walk' }, labels), 'Fly over');

// ---- a Jaunt's mode under the choice --------------------------------------------------------
const all = { allowed_modes: ['walk', 'wagon', 'horse', 'fly', 'instantly'], default_mode: 'horse' };
const footOnly = { allowed_modes: ['walk', 'instantly'], default_mode: 'walk' };
const chose = (travelMode, pace = 'walk') => ({ travelMode, pace, chosen: true });
assert.equal(jauntModeFor({ travelMode: 'instantly', pace: 'walk', chosen: false }, all), null,
  'until the visitor chooses, a Jaunt keeps its recommendation');
assert.equal(jauntModeFor({ travelMode: 'horse', pace: 'horse' }, all), null, 'chosen defaults to false');
assert.equal(jauntModeFor(chose('instantly'), all), 'instantly', 'Teleport: stop to stop at once');
assert.equal(jauntModeFor(chose('fly'), all), 'fly', 'Fly over: over the town');
assert.equal(jauntModeFor(chose('horse', 'horse'), all), 'horse', 'Ride there: at your mode');
assert.equal(jauntModeFor(chose('wagon', 'wagon'), all), 'wagon');
assert.equal(jauntModeFor(chose('run', 'run'), all), 'walk', 'running counts as on foot: no Jaunt lists running');
assert.equal(jauntModeFor(chose('horse', 'horse'), footOnly), null, 'not a way this Jaunt allows: its own');
assert.equal(jauntModeFor(chose('fly'), footOnly), null);
assert.equal(jauntModeFor(chose('instantly'), footOnly), 'instantly');
assert.equal(jauntModeFor(chose('walk'), null), null, 'no Jaunt, no mode');

// ---- the real Jaunt controller rides at the choice between stops ------------------------------
const walk = json('data/jaunts/_fixtures/fixture-walk.json');
function rig(preferredMode) {
  let mode = 'instantly', active = null;
  const travel = { get mode() { return mode; }, setMode(v) { mode = v; }, go(target, hooks) { active = hooks; return true; },
    stop(reason) { const old = active; active = null; if (old) old.onStop({ ...old.token, reason }); } };
  const controller = createJaunts({ load: async () => walk, resolve: (x) => x, place: () => true, enter: () => true, travel,
    render() {}, showMenu() {}, openDetail() {}, closeDetail() {}, onError: (e) => { throw e; }, storage: null, preferredMode });
  return { controller, travel };
}
for (const [style, want] of [[chose('instantly'), 'instantly'], [chose('fly'), 'fly'], [chose('wagon', 'wagon'), 'wagon'],
  [{ travelMode: 'instantly', pace: 'walk', chosen: false }, walk.default_mode]]) {
  const r = rig((jaunt) => jauntModeFor(style, jaunt));
  assert.equal(await r.controller.start('walk'), true);
  assert.equal(r.controller.state.mode, want, `${JSON.stringify(style)} starts the Jaunt at ${want}`);
  r.controller.next();
  assert.equal(r.controller.state.phase, 'travelling');
  assert.equal(r.travel.mode, want, `…and the ride between stops goes at ${want}`);
  r.controller.destroy?.();
}
// A mode picked on the Jaunt's own row still wins over the choice.
{
  const r = rig(() => 'fly');
  await r.controller.start('walk', { mode: 'horse' });
  assert.equal(r.controller.state.mode, 'horse', 'the row\'s own pick wins');
  r.controller.destroy?.();
}

// ---- the page: one choice, said to be everyone's; Go to and the Map use travel.go -----------------
const html = read('renderers/web/index.html');
assert(/id="arrive-note">Go to and Jaunts both use this choice/.test(html), 'Move says the choice is everyone\'s');
const main = read('renderers/web/js/main.js');
assert.equal((main.match(/preferredMode: \(jaunt\) => jauntModeFor\(hud\.gettingThere, jaunt\)/g) ?? []).length, 2,
  'the Jaunt menu and the Jaunt controller both read the choice');
assert(/function goToTarget[\s\S]{0,900}travel\.go\(/.test(main), 'Go to (and the Map\'s Go, which calls it) rides by travel.go, at the stored choice');
const hud = read('renderers/web/js/hud.js');
assert(/settings\.arriveChosen = true;\s*setTravelMode\(travelModeFor\(b\.dataset\.arrive/.test(hud), 'picking a choice marks it chosen');

console.log('test_getting_there: Teleport, Ride there and Fly over, one choice for Go to, the Map and Jaunts');
