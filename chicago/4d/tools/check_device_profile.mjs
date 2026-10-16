#!/usr/bin/env node
/**
 * T-2559 — the device profile chooses per device, and the visitor keeps the last word.
 *
 * Holds device-profile.js to its table: a forced `?device=` class, a software
 * rasteriser kept at the platform default, the resource floors, the benchmark
 * bounds, the crash step-down, the cache keyed by renderer and build, and the
 * Settings sentence. Holds main.js and hud.js to the wiring: a stored Scene
 * detail or Image sharpness is read FIRST, so the profile is only ever a
 * default. The browser half (the benchmark's real cost, the boot) is the
 * smoke's — see smoke_renderer.mjs § T-2559.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const dp = await import(pathToFileURL(path.join(web, 'js/device-profile.js')).href);
const { resolveSharpness, SHARPNESS_STOPS } = await import(pathToFileURL(path.join(web, 'js/sharpness.js')).href);
const main = await readFile(path.join(web, 'js/main.js'), 'utf8');
const hud = await readFile(path.join(web, 'js/hud.js'), 'utf8');
const html = await readFile(path.join(web, 'index.html'), 'utf8');

const checks = [];
function check(name, run) { run(); checks.push(name); }
async function checkAsync(name, run) { await run(); checks.push(name); }

const GPU = { webgl2: true, renderer: 'ANGLE (Apple, Apple M3, OpenGL 4.1)', cores: 8, memoryGB: 8, maxTexture: 16384 };
const DETAILS = ['full', 'balanced', 'light'];

check('a standard device boots exactly the T-2110 defaults on both platforms', () => {
  assert.deepEqual(dp.decide('standard', { touch: true }).detail, 'light');
  assert.equal(dp.decide('standard', { touch: true }).sharpness, 1);
  assert.equal(dp.decide('standard', { touch: false }).detail, 'full');
  assert.equal(dp.decide('standard', { touch: false }).sharpness, 1.5);
  assert.equal(dp.decide('nonsense', { touch: false }).detail, 'full', 'an unknown class reads as standard');
});
check('weak and strong move detail and Sharpness the documented way, inside the ladders', () => {
  assert.equal(dp.decide('weak', { touch: false }).detail, 'balanced');
  assert.equal(dp.decide('weak', { touch: false }).sharpness, 1);
  assert.equal(dp.decide('strong', { touch: false }).sharpness, 2);
  assert.equal(dp.decide('strong', { touch: true }).detail, 'light', 'a phone never earns geometry (T-2546)');
  assert.equal(dp.decide('strong', { touch: true }).sharpness, 1.5);
  for (const cls of dp.DEVICE_CLASSES) for (const touch of [true, false]) {
    const c = dp.decide(cls, { touch, cores: 8 });
    assert.ok(DETAILS.includes(c.detail), `${cls}/${touch}: ${c.detail} is not on the detail ladder`);
    assert.ok(SHARPNESS_STOPS.includes(c.sharpness), `${cls}/${touch}: ${c.sharpness} is not a Sharpness stop`);
    assert.ok(['light', 'full'].includes(c.textures));
    assert.ok(c.workers >= 1 && c.workers <= 6);
  }
  assert.equal(dp.decide('weak', { cores: 16 }).workers, 1);
  assert.equal(dp.decide('standard', { cores: 2 }).workers, 1);
  assert.equal(dp.decide('strong', { cores: 16 }).workers, 6);
});
check('?device= forces a class, and only the three classes', () => {
  for (const c of dp.DEVICE_CLASSES) {
    assert.equal(dp.forcedClass(`?year=1835&device=${c}`), c);
    assert.equal(dp.classify(GPU, null, { forced: c }).cls, c);
  }
  assert.equal(dp.forcedClass('?device=fast'), null);
  assert.equal(dp.forcedClass(''), null);
});
check('a software rasteriser keeps the platform default and is not benchmarked', () => {
  const sw = { ...GPU, renderer: 'ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero) (0x0000C0DE)), SwiftShader driver)' };
  assert.ok(dp.isSoftwareRenderer(sw.renderer));
  assert.ok(dp.isSoftwareRenderer('llvmpipe (LLVM 15.0.7, 256 bits)'));
  assert.ok(!dp.isSoftwareRenderer(GPU.renderer));
  const r = dp.classify(sw, { fill: 0.01, verts: 0.001 });
  assert.equal(r.cls, 'standard');
  assert.match(r.why, /software/);
});
check('the resource floors, then the benchmark bounds, decide a real GPU', () => {
  assert.equal(dp.classify({ ...GPU, cores: 2 }, { fill: 9, verts: 9 }).cls, 'weak');
  assert.equal(dp.classify({ ...GPU, memoryGB: 2 }, { fill: 9, verts: 9 }).cls, 'weak');
  assert.equal(dp.classify({ ...GPU, maxTexture: 2048 }, { fill: 9, verts: 9 }).cls, 'weak');
  assert.equal(dp.classify({ webgl2: false }, null).cls, 'weak');
  const { fill, verts } = dp.THRESHOLDS;
  assert.equal(dp.classify(GPU, { fill: fill.weak / 2, verts: verts.strong }).cls, 'weak');
  assert.equal(dp.classify(GPU, { fill: fill.strong, verts: verts.weak / 2 }).cls, 'weak');
  assert.equal(dp.classify(GPU, { fill: (fill.weak + fill.strong) / 2, verts: verts.strong }).cls, 'standard');
  assert.equal(dp.classify(GPU, { fill: fill.strong, verts: verts.strong }).cls, 'strong');
  assert.equal(dp.classify({ ...GPU, cores: 4 }, { fill: fill.strong, verts: verts.strong }).cls, 'standard',
    'strong needs the cores as well as the GPU');
  assert.equal(dp.classify(GPU, { fill: NaN, verts: NaN }).cls, 'standard', 'no reading is not a verdict');
});
check("T-2547's crash marker steps a class down, never below weak", () => {
  const up = { fill: 99, verts: 99 };
  assert.equal(dp.classify(GPU, up, { stepDown: 1 }).cls, 'standard');
  assert.equal(dp.classify(GPU, up, { stepDown: 5 }).cls, 'weak');
  assert.match(dp.classify(GPU, up, { stepDown: 1 }).why, /crash/);
});
check('the cache is keyed by renderer and build, and a stale key is a miss', () => {
  const store = new Map();
  const storage = { getItem: (k) => store.get(k) ?? null, setItem: (k, v) => store.set(k, v) };
  const key = dp.cacheKey(GPU.renderer, 'v900');
  storage.setItem(dp.PROFILE_KEY, JSON.stringify({ key, cls: 'strong', choice: {} }));
  assert.equal(dp.readCached(storage, key)?.cls, 'strong');
  assert.equal(dp.readCached(storage, dp.cacheKey(GPU.renderer, 'v901')), null);
  assert.equal(dp.readCached(storage, dp.cacheKey('another GPU', 'v900')), null);
  assert.equal(dp.readCached(storage, null)?.cls, 'strong', 'the forecast peeks without a key');
  storage.setItem(dp.PROFILE_KEY, '{not json');
  assert.equal(dp.readCached(storage, key), null);
});
await checkAsync('with no WebGL2 at all the profile says so, is weak, and never throws', async () => {
  const store = new Map();
  const storage = { getItem: (k) => store.get(k) ?? null, setItem: (k, v) => store.set(k, v) };
  const doc = { createElement: () => ({ getContext: () => null }) };
  const p = await dp.profileDevice({ touch: false, build: 'b', storage, doc, nav: { hardwareConcurrency: 8 }, win: {} });
  assert.equal(p.cls, 'weak');
  assert.equal(p.choice.detail, 'balanced');
  assert.equal(p.cached, false);
  const again = await dp.profileDevice({ touch: false, build: 'b', storage, doc, nav: { hardwareConcurrency: 8 }, win: {} });
  assert.equal(again.cached, true, 'a repeat visit reads the cache');
  const forced = await dp.profileDevice({ touch: false, build: 'b', storage: null, doc, nav: {}, win: {}, search: '?device=strong' });
  assert.equal(forced.cls, 'strong');
  assert.equal(forced.forced, 'strong');
  const broken = await dp.profileDevice({ doc: { createElement: () => { throw new Error('no canvas'); } }, nav: {}, win: {} });
  assert.ok(dp.DEVICE_CLASSES.includes(broken.cls));
});
check('Settings says the class and what it chose', () => {
  const p = { cls: 'strong', touch: false, choice: dp.decide('strong', { touch: false }) };
  assert.equal(dp.describeProfile(p), 'Your device: strong computer, chosen Full detail at High sharpness.');
  const q = { cls: 'weak', touch: true, choice: dp.decide('weak', { touch: true }) };
  assert.equal(dp.describeProfile(q), 'Your device: modest phone or tablet, chosen Light detail at Low sharpness.');
  assert.match(html, /<p class="legend-note" id="device-line" hidden><\/p>/);
  assert.match(hud, /describeProfile\(device\)/);
});
check('a stored choice is read before the profile, so the visitor keeps the last word', () => {
  assert.match(main, /let detailLevel = crashBoot\.lowered\.detail \? crashBoot\.detail : \(readDetailPreference\(\) \|\| device\.choice\.detail\);/,
    "T-2547's step-down, then the stored choice, then the profile");
  assert.match(main, /resolveSharpness\(readQualityPreference\(\), coarse, qualityGuess\)/);
  assert.match(main, /crashGuard\.boot\(\{\s*detail: readDetailPreference\(\) \|\| bootGuess\?\.detail/,
    'the crash guard steps down from the cached profile, not the platform default');
  assert.match(main, /const qualityGuess = device\.choice\.sharpness;/);
  assert.match(main, /resolveSharpness\(hud\.settings\.quality, coarse, qualityGuess\)/);
  for (const q of SHARPNESS_STOPS) assert.equal(resolveSharpness(q, false, 2), q);
  assert.equal(resolveSharpness('', false, 2), 2);
  assert.equal(resolveSharpness('', true), 1);
  // The profile is read before the scene: the first await of boot() that fetches.
  assert.ok(main.indexOf('await profileDevice(') < main.indexOf('await loadScene('), 'profile before the scene fetch');
});

console.log(`check_device_profile: ${checks.length} checks passed`);
for (const c of checks) console.log(`  ok  ${c}`);
