#!/usr/bin/env node
// T-3445 (the owner, 2026-11-07): "you can also drop the wordy 'why this setting' for things
// like height of people sometimes you have paragraphs there". T-2658's short "Why?" lines,
// their bubbles and the Researcher-mode "Why this default" essays are gone, and Settings and
// Move keep terse labels. This holds that, with no browser: no "Why?" line, button, bubble or
// essay on the page, nor the module or strings that drew them; every note left in Settings
// and Move is one short line; and the three researched settings still name their default on
// their readout (hud.js), which is where the reasoning is said now.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { t } from '../renderers/web/js/strings/index.js';
import '../renderers/web/js/strings/research.js';
import '../renderers/web/js/strings/settings.js';
import '../renderers/web/js/strings/hud.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WEB = path.join(ROOT, 'renderers', 'web');
const read = (p) => fs.readFileSync(path.join(WEB, p), 'utf8');
const page = read('index.html');
const words = (s) => s.replace(/<[^>]+>/g, ' ').split(/\s+/).filter(Boolean).length;

// ---- nothing of the "Why?" left ----------------------------------------------------------
assert.doesNotMatch(page, /class="why-line"|class="why-btn"|class="why-text"|<details class="why"|Why this default/,
  'no "Why?" line, button, bubble or essay on the page');
for (const id of ['why-eye', 'why-brightness', 'why-road', 'eye-note', 'brightness-note', 'road-aid-note']) {
  assert.ok(!page.includes(`id="${id}"`), `#${id} is gone`);
}
assert.ok(!fs.existsSync(path.join(WEB, 'js', 'why-tips.js')), 'the bubble\'s module is gone');
assert.doesNotMatch(read('js/main.js'), /why-tips|whyTips/, 'and main.js wires none');
for (const css of ['css/drawer.css', 'css/walk.css']) {
  assert.doesNotMatch(read(css), /\.why-(line|btn|tip|hint|full)\b|details\.why\b/, `${css} styles none of it`);
}
for (const key of ['why.eye', 'why.road', 'why.brightness', 'hint.eye', 'hint.road', 'hint.brightness', 'why.ask']) {
  assert.ok(!t(`research.${key}`), `research.${key} is not in the string table`);
}

// ---- every note left in Settings and Move is one short line -------------------------------
const panel = (name) => { const a = page.indexOf(`data-panel="${name}"`); return page.slice(a, page.indexOf('</section>', a)); };
const MAX_WORDS = 16;
for (const name of ['settings', 'travel']) {
  for (const [, inner] of panel(name).matchAll(/<p class="legend-note"[^>]*>([\s\S]*?)<\/p>/g)) {
    const n = words(inner);
    assert.ok(n <= MAX_WORDS, `a ${name} note is ${n} words (${MAX_WORDS} at most): "${inner.replace(/\s+/g, ' ').trim().slice(0, 80)}"`);
  }
}
for (const key of ['settings.sound.note', 'research.switch.note', 'hud.move.note', 'hud.move.arrive.note']) {
  assert.ok(words(t(key)) <= MAX_WORDS, `${key} is ${words(t(key))} words`);
}
// The sound note still says the ambience is not a recording (T-2659's honesty line).
assert.match(t('settings.sound.note'), /not a recording of the past\./);

// ---- the researched defaults are named on their readouts ------------------------------------
const hud = read('js/hud.js');
assert.match(hud, /' · 1830s average'/, 'eye height at 1.68 m reads as the 1830s average');
assert.match(hud, /'Off · as recorded'/, 'road visibility at its default reads as recorded');
assert.match(hud, /'Calibrated'/, 'brightness at its default reads Calibrated');

console.log(`test_short_why: no "Why?" lines or essays in Settings or Move; every note there ${MAX_WORDS} words or fewer; defaults named on their readouts (T-3445)`);
