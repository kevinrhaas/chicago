#!/usr/bin/env node
/**
 * T-3675 — a classroom set's Chromebook is recognised, routed as a computer on the
 * memory diet, and offered "Prepare for class".
 *
 * The owner's list, item 17 (docs/CLASSROOM-FEATURES.md): a low-end Chromebook
 * (ChromeOS, a Celeron with Intel UHD 600/605 or HD Graphics, or MediaTek / Snapdragon
 * with Arm Mali, PowerVR or Adreno; 4 GB; 2-4 cores) boots as a `weak` computer:
 * Balanced, Sharpness Low, light textures, the memory diet, people, horses, carriages and
 * wagons all drawn. Never Light, touch screen or not (owner, 2026-11-10). Its controls
 * follow its primary pointer. The year's offline copy is offered to the teacher as
 * "Prepare for class" on the welcome and in Settings, with its size, progress and done
 * state, and says plainly that each device keeps its own copy.
 *
 * Pure checks in node over device-profile.js, arrival-device.js and year-pack.js, a
 * fake WebGL2 context through the real profileDevice(), and the wiring in main.js,
 * touch.js, measure_memory.mjs, memory_ceilings.json and the memory CI matrix. The
 * browser half is the memory gate's `chromebook` row (`measure_memory.mjs --gate
 * --only chromebook`), which fails unless the emulated Chromebook booted routed so.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { CHROMEBOOK, CHROMEBOOK_GPUS } from './chromebook_emulation.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const load = (rel) => import(pathToFileURL(path.join(web, rel)).href);
const dp = await load('js/device-profile.js');
const ad = await load('js/arrival-device.js');
const read = (rel) => readFile(path.join(root, rel), 'utf8');
const main = await read('renderers/web/js/main.js');
const touchJs = await read('renderers/web/js/controls/touch.js');
const packJs = await read('renderers/web/js/year-pack.js');
const measure = await read('tools/measure_memory.mjs');
const ceilings = JSON.parse(await read('tools/memory_ceilings.json'));
const workflow = await readFile(path.join(root, '../../.github/workflows/chicago-4d-frame-time.yml'), 'utf8')
  .catch(() => null);

// year-pack.js reads `document` only inside createYearPack; packWords is pure.
const { packWords } = await load('js/year-pack.js');

const checks = [];
function check(name, run) { run(); checks.push(name); }
async function checkAsync(name, run) { await run(); checks.push(name); }

const CROS = CHROMEBOOK.userAgent;
const WINDOWS = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';
const ANDROID = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36';

check('ChromeOS is read from the user agent or Chrome\'s userAgentData, and nothing else is', () => {
  assert.ok(dp.isChromeOS(CROS));
  assert.ok(dp.isChromeOS('Mozilla/5.0 (X11; CrOS aarch64 15633.69.0) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36'));
  assert.ok(dp.isChromeOS('', 'Chrome OS'));
  assert.ok(dp.isChromeOS('', 'ChromeOS'));
  for (const ua of [WINDOWS, ANDROID, 'Mozilla/5.0 (X11; Linux x86_64) Chrome/130.0.0.0', '']) assert.ok(!dp.isChromeOS(ua), ua);
  assert.ok(!dp.isChromeOS('', 'Windows'));
});

check('every classroom Chromebook GPU is named as one that shares the system\'s memory', () => {
  for (const r of CHROMEBOOK_GPUS) assert.ok(dp.sharesSystemMemory(r), r);
  assert.equal(dp.shortGpu(CHROMEBOOK.renderer), 'Intel(R) UHD Graphics 600', 'Mesa\'s prefix and the chip codename are dropped');
  assert.equal(dp.shortGpu('Mesa Intel(R) UHD Graphics 620 (KBL GT2)'), 'Intel(R) UHD Graphics 620');
  assert.equal(dp.shortGpu('ANGLE (ARM, Mali-G72, OpenGL ES 3.2)'), 'Mali-G72');
});

const base = { webgl2: true, maxTexture: 8192, chromeos: true, memoryGB: 4, cores: 4, automated: false };
check('a Chromebook is a weak computer whatever its GPU benchmark reads, and boots Balanced on the memory diet', () => {
  for (const renderer of CHROMEBOOK_GPUS) {
    for (const bench of [{ fill: 9, verts: 9 }, { fill: 2, verts: 0.2 }, null]) {
      const { cls, why } = dp.classify({ ...base, renderer }, bench);
      assert.equal(cls, 'weak', `${renderer} ${JSON.stringify(bench)}`);
      assert.match(why, /Chromebook|few resources/);
    }
  }
  // An 8 GB Chromebook Plus is still on graphics that share its memory.
  assert.equal(dp.classify({ ...base, memoryGB: 8, cores: 8, renderer: CHROMEBOOK_GPUS[4] }, { fill: 9, verts: 9 }).cls, 'weak');
  // A two-core Celeron meets the resource floor first; still weak.
  assert.equal(dp.classify({ ...base, cores: 2, renderer: CHROMEBOOK.renderer }, null).cls, 'weak');
  // ?device= still forces, for the harness.
  assert.equal(dp.classify({ ...base, renderer: CHROMEBOOK.renderer }, null, { forced: 'standard' }).cls, 'standard');
  const choice = dp.decide('weak', { touch: false, cores: 4 });
  assert.deepEqual([choice.detail, choice.sharpness, choice.textures, choice.lowMemory], ['balanced', 1, 'light', true],
    'Balanced, Sharpness Low, light textures, memory diet');
  assert.notEqual(choice.detail, 'light', 'Light is not a computer\'s floor (owner, 2026-11-10)');
});

check('an Arm Mali Chromebook is not treated as a phone, and an Android phone with the same GPU still is', () => {
  const mali = { ...base, renderer: 'ANGLE (ARM, Mali-G72, OpenGL ES 3.2)' };
  // touch: true is what a touch-screen Chromebook's coarse pointer used to make it.
  assert.equal(dp.classify(mali, { fill: 2, verts: 0.2 }, { touch: true }).cls, 'weak');
  const phone = { ...mali, chromeos: false };
  assert.equal(dp.classify(phone, { fill: 2, verts: 0.2 }, { touch: true }).cls, 'standard', 'a phone keeps its own table');
  assert.equal(dp.decide('standard', { touch: true }).detail, 'light');
});

/** A WebGL2 context just real enough for readGl() and a benchmark that cannot link. */
function fakeDoc(renderer, vendor = 'Google Inc. (Intel)') {
  const gl = {
    RENDERER: 0x1F01, VENDOR: 0x1F00, MAX_TEXTURE_SIZE: 0x0D33, VERTEX_SHADER: 1, FRAGMENT_SHADER: 2, LINK_STATUS: 3,
    getExtension: (n) => (n === 'WEBGL_debug_renderer_info' ? { UNMASKED_RENDERER_WEBGL: 0x9246, UNMASKED_VENDOR_WEBGL: 0x9245 } : null),
    getParameter: (p) => ({ 0x9246: renderer, 0x9245: vendor, 0x0D33: 8192 })[p] ?? '',
    getSupportedExtensions: () => ['WEBGL_debug_renderer_info', 'EXT_texture_compression_s3tc'],
    createShader: () => ({}), shaderSource() {}, compileShader() {}, createProgram: () => ({}),
    attachShader() {}, linkProgram() {}, getProgramParameter: () => false,
  };
  return { createElement: () => ({ getContext: () => gl }) };
}
const memStore = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v) }; };

await checkAsync('the real profileDevice(): a touch-screen Chromebook is profiled as the computer it is', async () => {
  for (const touch of [false, true]) {
    const nav = { userAgent: CROS, hardwareConcurrency: 4, deviceMemory: 4, webdriver: false };
    const p = await dp.profileDevice({ touch, build: 'b', storage: memStore(), doc: fakeDoc(CHROMEBOOK.renderer), nav,
      win: { screen: { width: 1366, height: 768 }, devicePixelRatio: 1 } });
    assert.equal(p.signals.chromeos, true);
    assert.equal(p.touch, false, `touch ${touch}: a Chromebook is a computer`);
    assert.equal(p.cls, 'weak', p.why);
    assert.deepEqual([p.choice.detail, p.choice.sharpness, p.choice.textures, p.choice.lowMemory], ['balanced', 1, 'light', true]);
    assert.equal(dp.describeProfile(p), 'Your device: modest Chromebook, chosen Balanced detail at Low sharpness.');
  }
  // The same chip under userAgentData alone (a reduced user agent), cached on the second visit.
  const storage = memStore();
  const nav = { userAgent: 'Mozilla/5.0 (X11; Linux x86_64) Chrome/130.0.0.0', userAgentData: { platform: 'Chrome OS' },
    hardwareConcurrency: 8, deviceMemory: 8 };
  const doc = fakeDoc('ANGLE (ARM, Mali-G57, OpenGL ES 3.2)', 'Google Inc. (ARM)');
  const first = await dp.profileDevice({ touch: true, build: 'b', storage, doc, nav, win: {} });
  const again = await dp.profileDevice({ touch: true, build: 'b', storage, doc, nav, win: {} });
  assert.equal(first.cls, 'weak');
  assert.equal(again.cached, true);
  assert.equal(again.choice.detail, 'balanced', 'the cached profile is decided as a computer too');
  // A Windows laptop is untouched by any of it.
  const win = await dp.profileDevice({ touch: false, build: 'b', storage: memStore(), doc: fakeDoc('ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)'),
    nav: { userAgent: WINDOWS, hardwareConcurrency: 12, deviceMemory: 8 }, win: {} });
  assert.equal(win.signals.chromeos, false);
  assert.notEqual(win.cls, 'weak', 'a discrete GPU with no benchmark reading stays standard');
});

check('controls: a Chromebook takes keyboard and trackpad unless its pointer is coarse (tablet mode)', () => {
  assert.equal(dp.touchDefault({ coarse: false, maxTouchPoints: 10, width: 683, chromeos: true }), false,
    'a touch-screen Chromebook in a half-screen window keeps its keyboard and trackpad');
  assert.equal(dp.touchDefault({ coarse: true, maxTouchPoints: 10, width: 1366, chromeos: true }), true, 'tablet mode');
  assert.equal(dp.touchDefault({ coarse: false, maxTouchPoints: 0, width: 1366, chromeos: true }), false);
  // Elsewhere, as before: a coarse pointer, or a touch screen in a narrow window.
  assert.equal(dp.touchDefault({ coarse: false, maxTouchPoints: 5, width: 390 }), true);
  assert.equal(dp.touchDefault({ coarse: true, maxTouchPoints: 5, width: 1024 }), true);
  assert.equal(dp.touchDefault({ coarse: false, maxTouchPoints: 0, width: 390 }), false);
  assert.match(touchJs, /return touchDefault\(\{ coarse: !!window\.matchMedia\?\.\('\(pointer: coarse\)'\)\.matches,/);
  assert.match(touchJs, /chromeos: isChromeOS\(navigator\.userAgent, navigator\.userAgentData\?\.platform\)/);
  // A touch on the screen still switches to the touch controls (main.js, first real event wins).
  assert.match(main, /if \(e\.pointerType === 'touch'\) backends\.activate\(touch\);/);
});

check('the loading screen names the Chromebook, its shared memory, and that everyone is still drawn', () => {
  const profile = { cls: 'weak', touch: false, why: 'a Chromebook: graphics sharing the system\'s memory',
    signals: { webgl2: true, renderer: CHROMEBOOK.renderer, chromeos: true, cores: 4, memoryGB: 4 },
    bench: { fill: 1.2, verts: 0.1 }, choice: dp.decide('weak', { touch: false, cores: 4 }) };
  const st = ad.arrivalDeviceStatus({ profile, detail: 'balanced', sharpness: 1, lowMemory: true });
  assert.deepEqual(st.assess, ['Chromebook', 'Intel UHD Graphics 600', 'shared memory', '4 GB', '4 cores']);
  assert.ok(st.setup.includes('Balanced detail'));
  assert.ok(st.setup.includes('every street, building, person and carriage'));
  assert.ok(st.setup.includes('memory saver on'));
  assert.ok(st.score < 40, `the meter reads in the weak band: ${st.score}`);
  // A Mali Chromebook whose renderer the browser masks is still said to share memory.
  const masked = ad.arrivalDeviceStatus({ profile: { ...profile, signals: { ...profile.signals, renderer: '' } },
    detail: 'balanced', sharpness: 1, lowMemory: true });
  assert.deepEqual(masked.assess.slice(0, 2), ['Chromebook', 'shared memory']);
});

check('"Prepare for class": size shown, progress, a done state that says how to check it offline, honest copy', () => {
  const idle = packWords({ year: '1904', size: '238 MB', classroom: true });
  assert.equal(idle.line, 'Prepare for class · 238 MB');
  assert.equal(idle.keep, 'Download 238 MB');
  assert.match(idle.note, /on each device before the lesson: every device keeps its own copy, and nothing is shared across the room/);
  assert.doesNotMatch(idle.note, /whole (class|room)|once for (the|your) (class|room)|shared download/i,
    'never promises a room-wide download');
  const going = packWords({ year: '1904', status: 'downloading', size: '238 MB', classroom: true,
    progress: { bytes: 119e6, total: 238e6 } });
  assert.equal(going.line, 'Preparing for class · 50 %');
  assert.equal(going.fraction, 0.5);
  assert.match(going.note, /119 MB of 238 MB\. Keep this page open\./);
  const done = packWords({ year: '1904', status: 'kept', classroom: true });
  assert.equal(done.line, 'Ready for class · works offline');
  assert.match(done.note, /opens with no connection\. To check, turn Wi-Fi off and reload this page\./);
  assert.equal(packWords({ year: '1904', status: 'error', error: 'offline', classroom: true }).keep, 'Try again');
  // Off a Chromebook the welcome line keeps its quiet T-2947 words; the note is the same.
  assert.equal(packWords({ year: '1835', size: '90 MB' }).line, 'Offline copy');
  assert.equal(packWords({ year: '1835', status: 'kept' }).line, 'Offline copy · kept');
  assert.match(packWords({ year: '1835' }).note, /every device keeps its own copy/);
  for (const s of ['idle', 'downloading', 'kept', 'error']) {
    const w = packWords({ year: '1812', status: s, size: '50 MB', progress: { bytes: 1, total: 2 } });
    for (const k of ['line', 'tip', 'note', 'setting', 'keep']) assert.ok(w[k], `${s}: ${k}`);
  }
});

check('main.js marks a Chromebook classroom and mounts the Settings twin on the Graphics tab', () => {
  assert.match(main, /api\.pack = createYearPack\(\{[^}]*classroom: !!device\.signals\?\.chromeos \}\);/);
  assert.match(main, /api\.pack\.attachSettings\(document\.querySelector\('\.panel-body\[data-panel="settings"\] \.settings-group\[data-set-pane="graphics"\]'\)\);/);
  assert.match(packJs, /group\.className = 'settings-group pack-settings'; group\.id = 's-offline';/);
  assert.match(packJs, /group\.hidden = settingsAnchor\.hidden;/, 'the Settings tab in view decides, as for every group');
  // The smoke's selectors on the welcome control are kept (tools/smoke_year_pack.mjs).
  for (const cls of ['welcome-pack-toggle', 'welcome-pack-keep', 'welcome-pack-remove']) assert.ok(packJs.includes(`'${cls}'`), cls);
});

check('the memory gate reads an emulated Chromebook in every year, under a ceiling, and holds its routing', () => {
  assert.match(measure, /\{ id: 'chromebook', label: CHROMEBOOK\.label,[^}]*emulate: CHROMEBOOK \}/);
  assert.match(measure, /if \(vp\.emulate\) await ctx\.addInitScript\(spoofDevice, vp\.emulate\);/);
  assert.match(measure, /if \(row\.viewport === 'chromebook'\) \{/);
  assert.ok(!/query: 'device=/.test(measure.match(/\{ id: 'chromebook'[^}]*\}/)[0]), 'emulated, never forced by ?device=');
  for (const year of ['1812', '1835', '1904']) {
    const c = ceilings.ceilings[year]?.chromebook;
    assert.ok(c && c.total_bytes > 0, `${year}: a chromebook ceiling`);
    assert.equal(c.tier, 'balanced', `${year}: read at Balanced`);
    assert.ok(c.total_bytes < ceilings.ceilings[year].desktop.total_bytes,
      `${year}: under the desktop's Full line: the diet is what a 4 GB Chromebook is booted on`);
    assert.ok(c.reading_bytes <= c.total_bytes, `${year}: its reading under it`);
    assert.ok(c.set_by?.reading, `${year}: names its reading`);
  }
  if (workflow) assert.match(workflow, /viewport: \[desktop, mobile, shared, chromebook\]/, 'CI reads it every year');
});

console.log(`check_chromebook: ${checks.length} checks passed`);
for (const c of checks) console.log(`  ok  ${c}`);
