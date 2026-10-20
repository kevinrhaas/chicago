#!/usr/bin/env node
// T-2652 (NAV-702): getting there — Teleport, Ride there or Fly over — one choice that Go
// to, the Map and Jaunts all use; T-2727: Jaunts take it only with Move › Jaunts use my choice on. Reads js/getting-there.js, then drives the real Jaunt
// controller (js/jaunts.js) over a fake ride to show each choice is the mode it rides
// between stops. No browser; the smoke (part 13) makes the choice in a page.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { STYLES, styleOf, styleWords, jauntModeFor, jauntChoice, jauntsFollowFrom } from '../renderers/web/js/getting-there.js';
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

// ---- a Jaunt's mode under the choice (T-2727: the switch, not T-2652's hidden rule) ------------
const all = { allowed_modes: ['walk', 'wagon', 'horse', 'fly', 'instantly'], default_mode: 'horse' };
const footOnly = { allowed_modes: ['walk', 'instantly'], default_mode: 'walk' };
const on = (travelMode, pace = 'walk') => ({ travelMode, pace, follow: true });
const off = (travelMode, pace = 'walk') => ({ travelMode, pace, follow: false });
// Off (the default): every Jaunt keeps the way it recommends, whatever the choice.
for (const choice of [off('instantly'), off('fly'), off('horse', 'horse'), off('wagon', 'wagon'), { travelMode: 'fly', pace: 'walk' }]) {
  assert.equal(jauntModeFor(choice, all), null, `off: ${JSON.stringify(choice)} leaves the Jaunt its own`);
  assert.deepEqual(jauntChoice(choice, all), { mode: null, kept: false, want: null }, 'and says nothing: it was not asked');
}
assert.equal(jauntModeFor({ travelMode: 'fly', follow: 'yes' }, all), null, 'only true turns it on');
// On: the visitor's choice, where the Jaunt allows it.
assert.equal(jauntModeFor(on('instantly'), all), 'instantly', 'Teleport: stop to stop at once');
assert.equal(jauntModeFor(on('fly'), all), 'fly', 'Fly over: over the town');
assert.equal(jauntModeFor(on('horse', 'horse'), all), 'horse', 'Ride there: at your mode');
assert.equal(jauntModeFor(on('wagon', 'wagon'), all), 'wagon');
assert.equal(jauntModeFor(on('run', 'run'), all), 'walk', 'running counts as on foot: no Jaunt lists running');
assert.equal(jauntModeFor(on('instantly'), footOnly), 'instantly');
// On, but not a way this Jaunt can be travelled: it keeps its own, and says which choice it could not take.
assert.deepEqual(jauntChoice(on('horse', 'horse'), footOnly), { mode: null, kept: true, want: 'horse' }, 'a horse on a foot-only outing: kept');
assert.deepEqual(jauntChoice(on('fly'), footOnly), { mode: null, kept: true, want: 'fly' });
assert.deepEqual(jauntChoice(on('horse', 'horse'), all), { mode: 'horse', kept: false, want: 'horse' });
assert.equal(jauntModeFor(on('walk'), null), null, 'no Jaunt, no mode');
// The stored switch: a stored true is on; missing, corrupt or anything else is off.
assert.equal(jauntsFollowFrom({ jauntsFollowChoice: true }), true);
for (const saved of [{}, { jauntsFollowChoice: false }, { jauntsFollowChoice: 'true' }, { jauntsFollowChoice: 1 }, null, 'x', { arriveChosen: true }]) {
  assert.equal(jauntsFollowFrom(saved), false, `${JSON.stringify(saved)} reads as off`);
}

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
for (const [style, want] of [[on('instantly'), 'instantly'], [on('fly'), 'fly'], [on('wagon', 'wagon'), 'wagon'],
  [off('fly'), walk.default_mode], [off('wagon', 'wagon'), walk.default_mode]]) {
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
assert(/id="arrive-note" data-str="hud\.move\.arrive\.note">Go to and the map use this choice\. Jaunts keep the way each recommends, unless Jaunts use my choice is on/.test(html),
  'Move says plainly what the choice and the switch do');
assert(/<span data-str="hud\.move\.jaunts">Jaunts use my choice<\/span>\s*<input type="checkbox" id="s-jaunts-choice">/.test(html),
  'Move › When you pick a place carries the switch');
const main = read('renderers/web/js/main.js');
assert.equal((main.match(/preferredMode: \(jaunt\) => jauntModeFor\(hud\.gettingThere, jaunt\)/g) ?? []).length, 2,
  'the Jaunt menu and the Jaunt controller both read the choice');
assert(/function goToTarget[\s\S]{0,900}travel\.go\(/.test(main), 'Go to (and the Map\'s Go, which calls it) rides by travel.go, at the stored choice');
const hud = read('renderers/web/js/hud.js');
assert(!/arriveChosen\s*[=:]\s*(true|false)|settings\.arriveChosen/.test(hud), 'T-2652\'s hidden rule is retired');
assert(/jauntsFollowChoice: false,/.test(hud), 'the switch is off by default');
assert(/saved\.jauntsFollowChoice = jauntsFollowFrom\(saved\)/.test(hud), 'and read from storage strictly');
assert(/follow: settings\.jauntsFollowChoice === true/.test(hud), 'the choice Jaunts read carries the switch');
assert(/modeNote: \(jaunt\) => jauntWay\(jaunt\)\.note/.test(main) && /function jauntWay[\s\S]{0,420}t\('hud\.jaunt\.keeps'/.test(main),
  'a Jaunt that keeps its own says so, in the table\'s words');

console.log('test_getting_there: Teleport, Ride there and Fly over, one choice for Go to and the Map; Jaunts take it only with Jaunts use my choice on, and one that cannot keeps its own and says so');
