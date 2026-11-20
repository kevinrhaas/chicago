// T-3586. One gust rhythm for the swaying plants and the wind you hear.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { GUST, GUST_GLSL, WIND_SOUND, gustAt, gustAtScene, windGustGain, advanceGust, setGustClock, gustClock }
  from '../renderers/web/js/wind-gust.js';
const src = f => fs.readFileSync(new URL(`../renderers/web/js/${f}`, import.meta.url), 'utf8');

test('a gust never swings a plant past the sway it had, and lulls are calmer', () => {
  let lo = Infinity, hi = -Infinity;
  for (let t = 0; t < GUST.period; t += 0.05) for (const [e, n] of [[0, 0], [1200, -2900], [-400, 800]]) {
    const g = gustAt(e, n, t); lo = Math.min(lo, g); hi = Math.max(hi, g);
  }
  assert(lo >= GUST.min - 1e-9 && hi <= 1 + 1e-9, `${lo}..${hi}`);
  assert(hi - lo > 0.5, 'gusts and lulls are far enough apart to see');
});

test('the rhythm wraps with no seam, and the clock stays small for phone shaders', () => {
  for (const [p] of GUST.swells) assert.equal(GUST.period % p, 0, `${p} s divides the period`);
  for (const t of [0, 3.7, 119]) assert(Math.abs(gustAt(37, -12, t) - gustAt(37, -12, t + GUST.period)) < 1e-9);
  setGustClock(GUST.period - 0.01); advanceGust(0.05);
  assert(gustClock() < 0.05 && gustClock() >= 0);
  advanceGust(NaN); advanceGust(-1); assert(gustClock() < 0.05, 'a bad frame time never moves it');
});

test('a gust is a front crossing the town: downwind gets it later', () => {
  const d = 70, [ex, ny] = GUST.dir;
  for (const t of [5, 40, 133]) assert(Math.abs(gustAt(ex * d, ny * d, t + d / GUST.speed) - gustAt(0, 0, t)) < 1e-9);
  assert.equal(gustAtScene(10, -20, 7), gustAt(10, 20, 7), 'scene z is minus north');
});

test('the GLSL twin carries the same numbers as the JS', () => {
  assert.match(GUST_GLSL, /float chiTownGust\(vec3 w\)/);
  for (const [p, a, ph] of GUST.swells) {
    assert(GUST_GLSL.includes((2 * Math.PI / p).toFixed(6)), `swell ${p} s`);
    assert(GUST_GLSL.includes(`${a.toFixed(4)} * sin(`)); assert(GUST_GLSL.includes(ph.toFixed(4)));
  }
  assert(GUST_GLSL.includes(`w.x * ${GUST.dir[0].toFixed(4)} - w.z * ${GUST.dir[1].toFixed(4)}`));
});

test('every swaying shader and the wind sound read the one gust', () => {
  assert.match(src('tree-surface.js'), /chiS \*= chiTownGust\(chiW\);/);
  assert.match(src('tree-surface.js'), /shader\.uniforms\.uGustClock = uGustClock;/);
  assert.match(src('flora.js'), /\* chiTownGust\(chiInst\);/);
  assert.match(src('flora.js'), /uGustClock,\n/);
  assert.match(src('main.js'), /advanceGust\(dt\); syncGustUniform\(\);/);
  assert.match(src('recorded-audio.js'), /windGustGain\(gustAtScene\(eye\.x, eye\.z\)\)/);
});

test('the wind you hear swells with the gust, and on average stays at the quiet town mix', () => {
  assert.equal(windGustGain(GUST.min), WIND_SOUND.lull);
  assert.equal(windGustGain(1), WIND_SOUND.peak);
  assert(WIND_SOUND.peak <= 1.6 && WIND_SOUND.lull >= 0.25);
  let sum = 0, n = 0, prev = -Infinity;
  for (let g = GUST.min; g <= 1; g += 0.01) { const v = windGustGain(g); assert(v >= prev); prev = v; }
  for (let t = 0; t < GUST.period; t += 0.1) { sum += windGustGain(gustAt(0, 0, t)); n++; }
  assert(sum / n <= 1, `average ${sum / n} of the old level`);
});
