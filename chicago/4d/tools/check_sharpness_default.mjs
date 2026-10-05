#!/usr/bin/env node
/**
 * T-2110 — Image sharpness starts where the owner ruled, and a stored choice wins.
 *
 * The owner's answer (a): a phone starts at Low (pixel ratio 1), a desktop at
 * Medium (1.5). This holds sharpness.js to that, and holds hud.js to storing
 * '' for "never chosen" — a numeric default there would be written into
 * storage the first time a visitor saved any other setting, and the device
 * guess would then read as their choice forever.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const { resolveSharpness, sharpnessGuess, SHARPNESS_STOPS } = await import(
  pathToFileURL(path.join(web, 'js/sharpness.js')).href);
const hud = await readFile(path.join(web, 'js/hud.js'), 'utf8');
const html = await readFile(path.join(web, 'index.html'), 'utf8');

const checks = [];
function check(name, run) { run(); checks.push(name); }

check('a phone that never chose starts at Low, a desktop at Medium', () => {
  assert.equal(sharpnessGuess(true), 1);
  assert.equal(sharpnessGuess(false), 1.5);
  for (const never of ['', undefined, null, 0, 'x']) {
    assert.equal(resolveSharpness(never, true), 1);
    assert.equal(resolveSharpness(never, false), 1.5);
  }
});
check('a stored choice is never overridden, on either device', () => {
  for (const q of SHARPNESS_STOPS) {
    assert.equal(resolveSharpness(q, true), q);
    assert.equal(resolveSharpness(q, false), q);
    assert.equal(resolveSharpness(String(q), true), q);
  }
});
check('every stop is an option in Settings, and nothing else is', () => {
  const sel = html.match(/<select id="s-quality">([\s\S]*?)<\/select>/);
  assert.ok(sel, 'index.html has no #s-quality');
  const values = [...sel[1].matchAll(/value="([^"]+)"/g)].map((m) => Number(m[1]));
  assert.deepEqual(values, [...SHARPNESS_STOPS]);
  assert.ok(SHARPNESS_STOPS.includes(sharpnessGuess(true)) && SHARPNESS_STOPS.includes(sharpnessGuess(false)));
});
check("hud.js keeps '' for never chosen, and shows the guess in force", () => {
  assert.match(hud, /^\s*quality: '',/m, "DEFAULT_SETTINGS.quality must be '' (never chosen)");
  assert.match(hud, /qual\.value = String\(settings\.quality \|\| resolvedQuality\)/);
});

console.log(`check_sharpness_default: ${checks.length} checks passed`);
for (const c of checks) console.log(`  ok  ${c}`);
