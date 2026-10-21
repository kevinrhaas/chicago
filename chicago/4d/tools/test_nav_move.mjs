#!/usr/bin/env node
// T-2651 (NAV-701): Move — one picker (Walk, Run, Wagon, Horse, Fly) and one slider for
// the mode picked, keeping the named speeds. Reads js/move-modes.js, the pure model the
// HUD paints, and the markup: the old two pickers and three sliders are gone. No browser;
// the smoke (part 13, part 7) drives the same section in a page.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { GROUND_MODES, MOVE_MODES, groundPace, nextPace, arriveOf, travelModeFor, speedOf, moveView } from '../renderers/web/js/move-modes.js';
import { PACES, paceSpeed, gaitName } from '../renderers/web/js/travel.js';
import { estimateLeg } from '../renderers/web/js/travel-estimate.js';
import APP from '../renderers/web/js/apps/move.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');

// ---- the modes ------------------------------------------------------------------
assert.deepEqual(MOVE_MODES, ['walk', 'run', 'wagon', 'horse', 'fly'], 'the picker: Walk, Run, Wagon, Horse, Fly');
assert.deepEqual(GROUND_MODES, ['walk', 'run', 'wagon', 'horse']);
assert.deepEqual(MOVE_MODES.map((m) => PACES[m].label), ['Walk', 'Run', 'Wagon', 'Horse', 'Fly']);
assert.equal(groundPace('instantly'), 'walk', 'anything but a ground mode reads as Walk');
assert.equal(groundPace(undefined), 'walk');
assert.deepEqual(GROUND_MODES.map(nextPace), ['run', 'wagon', 'horse', 'walk'], 'the pace chip cycles the ground modes');

// ---- Run is on foot, with its own slider -------------------------------------------
assert.equal(PACES.run.settingKey, 'runSpeed');
assert.equal(PACES.run.eyeOffset, 0, 'a runner sees from the walker\'s eye');
assert.equal(paceSpeed('run', {}), PACES.run.defaultSpeed);
assert.equal(paceSpeed('run', { runSpeed: 1 }), PACES.run.minSpeed, 'Run\'s slider starts at a jog');
assert.equal(paceSpeed('walk', { speed: 0.5 }), 0.5, 'Walk keeps its floor');
assert.equal(gaitName('run', 3.4), 'jog');
// T-2945: the faster defaults are named for what they are: 10 mph on foot is a run.
assert.equal(gaitName('walk', PACES.walk.defaultSpeed), 'run');
assert.equal(gaitName('run', PACES.run.defaultSpeed), 'sprint');
assert.equal(gaitName('wagon', PACES.wagon.defaultSpeed), 'rattling along');
assert.equal(gaitName('horse', PACES.horse.defaultSpeed), 'gallop');
assert.deepEqual(GROUND_MODES.map((m) => PACES[m].defaultSpeed), [4.47, 6.71, 7.15, 11.18], 'walk 10 mph, then run, wagon and horse faster in turn (owner, 2026-10-20)');
for (const m of GROUND_MODES) assert(PACES[m].defaultSpeed < PACES[m].maxSpeed * 0.6, `${m}'s default sits below the top of its slider`);
assert.equal(gaitName('run', 8.94), gaitName('walk', 8.94), 'Run speaks the walk\'s words');
const from = { e: 0, n: 0 }, to = { e: 300, n: 400 };
const runLeg = estimateLeg({ from, to, mode: 'run', settings: {} });
const walkLeg = estimateLeg({ from, to, mode: 'walk', settings: {} });
assert(runLeg && walkLeg && runLeg.seconds < walkLeg.seconds, 'Go to estimates a run as quicker than a walk');

// ---- one slider: the range and the named speeds follow the mode ----------------------
const base = { pace: 'walk', travelMode: 'instantly', units: 'imperial', speed: 1.45, runSpeed: 3.4, wagonSpeed: 3.6, horseSpeed: 6.5 };
const views = Object.fromEntries(GROUND_MODES.map((pace) => [pace, moveView({ ...base, pace })]));
for (const pace of GROUND_MODES) {
  const v = views[pace];
  assert.equal(v.mode, pace);
  assert.equal(v.slider.shown, true, `${pace} has its slider`);
  assert.equal(v.slider.key, PACES[pace].settingKey, `${pace}'s slider writes its own setting`);
  assert.equal(v.slider.label, `${PACES[pace].label} speed`);
  assert.match(v.slider.readout, /^[a-z][a-z ]*[a-z] · \d+(?:\.\d)? mph$/, `${pace} names its speed: ${v.slider.readout}`);
  assert(v.slider.value >= v.slider.min && v.slider.value <= v.slider.max);
}
const ranges = GROUND_MODES.map((p) => `${views[p].slider.min}-${views[p].slider.max}`);
assert.deepEqual(ranges, ['0.5-13.41', '2.6-13.41', '0.5-17.88', '0.5-35.76'], 'each mode its own range: 30, 30, 40 and 80 mph (T-2945)');
assert.equal(new Set(ranges).size, 4, 'changing mode changes the range');
assert.deepEqual(GROUND_MODES.map((p) => views[p].slider.readout),
  ['walk · 3.2 mph', 'jog · 7.6 mph', 'steady roll · 8.1 mph', 'canter · 14.5 mph']);
assert.equal(moveView({ ...base, pace: 'wagon', wagonSpeed: 10.97 }).slider.readout, 'rattling along · 24.5 mph',
  'the named speeds are kept: rattling along');
assert.equal(moveView({ ...base, pace: 'horse', horseSpeed: 26.82 }).slider.readout, 'beyond any horse · 60.0 mph');
assert.equal(moveView({ ...base, pace: 'horse', horseSpeed: 35.76 }).slider.readout, 'beyond any horse · 80.0 mph');
assert.equal(moveView({ ...base, pace: 'wagon', wagonSpeed: 10.97, units: 'metric' }).slider.readout, 'rattling along · 39.5 km/h');
assert.equal(speedOf('horse', { horseSpeed: 99 }), 35.76, 'a stored value past the top is held at the top');
assert.equal(speedOf('horse', { horseSpeed: 'nope' }), PACES.horse.defaultSpeed);
assert.match(views.horse.note, /×1\.7.*80\.0 mph/);
assert.match(views.wagon.note, /no faster gear/);

// ---- Fly: the picker shows it, and there is no slider ---------------------------------
const fly = moveView(base, { flying: true });
assert.equal(fly.mode, 'fly');
assert.equal(fly.pace, 'walk', 'the ground pace waits for you to land');
assert.equal(fly.slider.shown, false, 'Fly has no slider');
assert.match(fly.note, /The higher you are, the faster you go/);

// ---- Go to's choice under the picker ------------------------------------------------
assert.deepEqual(['instantly', 'walk', 'run', 'wagon', 'horse', 'fly', 'nonsense', undefined].map(arriveOf),
  ['instantly', 'ride', 'ride', 'ride', 'ride', 'fly', 'instantly', 'instantly']);
assert.equal(travelModeFor('ride', 'horse'), 'horse', 'Ride there rides at your mode');
assert.equal(travelModeFor('ride', 'run'), 'run');
assert.equal(travelModeFor('fly', 'horse'), 'fly');
assert.equal(travelModeFor('instantly', 'horse'), 'instantly');
assert.equal(moveView({ ...base, travelMode: 'wagon' }).arrive, 'ride');

// ---- the markup: one picker, one slider, the old controls gone ---------------------------
const html = read('renderers/web/index.html');
const a = html.indexOf('data-panel="travel"');
const panel = html.slice(a, html.indexOf('</section>', a));
for (const gone of ['s-travel', 's-pace', 's-wagon-speed', 's-horse-speed', 'v-wagon-speed', 'v-horse-speed']) {
  assert(!html.includes(`id="${gone}"`), `#${gone} is gone from the page`);
  assert(!read('renderers/web/js/hud.js').includes(`'${gone}'`), `hud.js no longer reads #${gone}`);
}
assert.deepEqual([...panel.matchAll(/data-mode="([a-z]+)"/g)].map((m) => m[1]), MOVE_MODES, 'one picker, in order');
assert.equal((panel.match(/role="radiogroup"/g) ?? []).length, 2, 'the picker, and Go to\'s choice');
assert.deepEqual([...panel.matchAll(/data-arrive="([a-z]+)"[^>]*>([^<]+)</g)].map((m) => m[2]), ['Teleport', 'Ride there', 'Fly over']);
// One speed slider; Comfort below it holds the eye height's own (T-2653).
const speedPart = panel.includes('id="move-comfort"') ? panel.slice(0, panel.indexOf('id="move-comfort"')) : panel;
assert.equal((speedPart.match(/type="range"/g) ?? []).length, 1, 'one slider');
// What a visitor reads: no ids, paths or snake_case in the section's words.
const words = panel.replace(/<!--[\s\S]*?-->/g, '').replace(/<[^>]+>/g, ' ');
assert(!/[a-z]+_[a-z]+|\.js\b|\//.test(words), `the section's words: ${words.replace(/\s+/g, ' ').trim()}`);
for (const v of [...Object.values(views), fly]) assert(!/_/.test(v.note + v.slider.label + v.slider.readout));
assert(/<span class="tab-label"[^>]*>Move<\/span>/.test(html.slice(html.indexOf('data-tab="travel"'), html.indexOf('data-tab="travel"') + 900)),
  'the drawer\'s tab is called Move, as the app is');

// ---- the Navigator's Move app opens the section ---------------------------------------
assert.equal(APP.id, 'move');
assert.equal(APP.label, 'Move');
// T-2620: the drawer's sections moved into the device, so Move is no longer a launch that
// opens the drawer's Move section: it holds that section in its own screen.
const { SECTION_HOME, APP_SECTIONS } = await import('../renderers/web/js/apps/drawer-host.js');
assert.equal(SECTION_HOME.travel, 'move', 'the one picker lives in the Move app');
assert.deepEqual(APP_SECTIONS.move, ['travel'], 'and Move holds only that section');
assert.ok(!APP.launch && typeof APP.mount === 'function' && typeof APP.shown === 'function', 'Move is a screen, not a launch');

console.log('test_nav_move: one picker, one slider, named speeds, Go to\'s choice and the markup hold');

// ---- T-2945: an untouched old default is no choice; a moved slider is kept -------------
{
  const { migratePaceDefaults, OLD_PACE_DEFAULTS, PACE_DEFAULTS_VERSION } = await import('../renderers/web/js/travel-settings.js');
  assert.deepEqual(OLD_PACE_DEFAULTS, { speed: 1.45, runSpeed: 3.4, wagonSpeed: 3.6, horseSpeed: 6.5 });
  const old = migratePaceDefaults({ speed: 1.45, runSpeed: 3.4, wagonSpeed: 3.6, horseSpeed: 6.5, fov: 70 });
  assert.deepEqual(old, { fov: 70, paceDefaults: PACE_DEFAULTS_VERSION }, 'the old defaults a whole-object save stored give way to the new');
  assert.equal(paceSpeed('walk', old), 4.47, 'so a returning visitor who never moved the slider walks at 10 mph');
  const mine = migratePaceDefaults({ speed: 2.2, horseSpeed: 6.5 });
  assert.equal(mine.speed, 2.2, 'a walk speed the visitor chose is kept');
  assert.equal(mine.horseSpeed, undefined);
  const later = migratePaceDefaults({ speed: 1.45, paceDefaults: PACE_DEFAULTS_VERSION });
  assert.equal(later.speed, 1.45, 'once read under the new defaults, 1.45 set on purpose is kept');
  assert.deepEqual(migratePaceDefaults(null), { paceDefaults: PACE_DEFAULTS_VERSION });
}
