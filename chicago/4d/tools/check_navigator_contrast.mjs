#!/usr/bin/env node
/**
 * T-2656 (QA-21) — every Navigator app legible at 4.5:1 or better in all four machines.
 *
 *   node tools/check_navigator_contrast.mjs              the gate
 *   node tools/check_navigator_contrast.mjs --print      …and print every measurement
 *   node tools/check_navigator_contrast.mjs --self-test  prove the assertions fire
 *
 * The Navigator reads only skin tokens (css/skins.css), and deepens three of them for
 * itself (the `contrast:begin` … `contrast:end` block in css/navigator.css). For every
 * machine, in its own tone and in the other one, this resolves the tokens as the device
 * sees them and holds WCAG 2.x contrast of 4.5:1 for:
 *
 *   ink, ink-dim, ink-faint and accent on the solid panel — reading text, labels, the
 *     screen code and date, links and the open app's icon;
 *   the signal key's ink on the signal (Inspect, Recall, Take a Jaunt), the signal itself never
 *     re-coloured by the device (T-2655 holds RECALL to the page's own --signal);
 *   the accent's own ink on the accent (a chosen segment, a chosen tile's ring is not text);
 *   the accent and the ink on the wash (a chosen Navigator segment, the open section's tab).
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MACHINES = ['control-room', 'brass', 'worlds-fair', 'deep-space'];
const NATIVE = { 'control-room': 'dark', brass: 'dark', 'worlds-fair': 'light', 'deep-space': 'dark' };
const MIN = 4.5;

function declarations(body) {
  return Object.fromEntries([...body.matchAll(/--([\w-]+)\s*:\s*([^;]+);/g)].map((m) => [m[1], m[2].trim()]));
}

/** The machine's tokens in a tone: its own block, then the other tone's block over it. */
export function skinTokens(css, skin, theme) {
  const out = {};
  for (const m of css.matchAll(/html\[data-skin="([\w-]+)"\](\[data-theme="(\w+)"\])?\s*\{([^}]*)\}/g)) {
    if (m[1] !== skin) continue;
    if (!m[3]) Object.assign(out, declarations(m[4]));
  }
  if (theme !== NATIVE[skin]) {
    for (const m of css.matchAll(/html\[data-skin="([\w-]+)"\]\[data-theme="(\w+)"\]\s*\{([^}]*)\}/g)) {
      if (m[1] === skin && m[2] === theme) Object.assign(out, declarations(m[3]));
    }
  }
  return out;
}

/** The Navigator's own overrides that apply to this machine and tone. */
export function navigatorOverrides(navCss, skin, theme) {
  const block = /\/\* contrast:begin \*\/([\s\S]*?)\/\* contrast:end \*\//.exec(navCss)?.[1] ?? '';
  const out = {};
  for (const m of block.matchAll(/([^{}]+)\{([^}]*)\}/g)) {
    const sel = m[1].trim();
    const skinOk = !/data-skin="/.test(sel) || sel.includes(`data-skin="${skin}"`);
    const themeNot = /:not\(\[data-theme="(\w+)"\]\)/.exec(sel)?.[1];
    const themeIs = /\]\[data-theme="(\w+)"\]/.exec(sel)?.[1];
    const themeOk = (!themeNot || themeNot !== theme) && (!themeIs || themeIs === theme);
    if (skinOk && themeOk) Object.assign(out, declarations(m[2]));
  }
  return out;
}

function resolve(tokens, value, depth = 0) {
  const v = String(value ?? '').trim();
  const ref = /^var\(--([\w-]+)\)$/.exec(v);
  if (ref && depth < 8) return resolve(tokens, tokens[ref[1]], depth + 1);
  return v;
}

function luminance(hex) {
  const h = hex.replace('#', '');
  const full = h.length === 3 ? [...h].map((c) => c + c).join('') : h.slice(0, 6);
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(full.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
/** `a` laid at `share` over `b`, as color-mix(in srgb, a share, transparent) over b. */
export function mix(a, b, share) {
  const rgb = (hex) => { const h = hex.replace('#', ''); const f = h.length === 3 ? [...h].map((c) => c + c).join('') : h.slice(0, 6);
    return [0, 2, 4].map((i) => parseInt(f.slice(i, i + 2), 16)); };
  if (!/^#[0-9a-f]{3,8}$/i.test(a) || !/^#[0-9a-f]{3,8}$/i.test(b)) return '';
  const [x, y] = [rgb(a), rgb(b)];
  return `#${x.map((c, i) => Math.round(c * share + y[i] * (1 - share)).toString(16).padStart(2, '0')).join('')}`;
}
export function contrast(a, b) {
  const [la, lb] = [luminance(a), luminance(b)];
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}

export function measure(skinsCss, navCss) {
  const rows = [];
  for (const skin of MACHINES) {
    for (const theme of ['dark', 'light']) {
      const base = skinTokens(skinsCss, skin, theme);
      const tokens = { ...base };
      for (const [k, v] of Object.entries(navigatorOverrides(navCss, skin, theme))) tokens[k] = v;
      const get = (k) => resolve({ ...base, ...tokens }, tokens[k]);
      // A self-reference (--ink-faint: var(--ink-dim)) resolves against the machine's own value.
      const panel = get('panel-solid');
      // The wash: skins.css mixes the accent at 16 %; the Navigator may mix it again.
      const share = Number(/var\(--accent\)\s*([\d.]+)%/.exec(tokens.wash ?? '')?.[1] ?? 16) / 100;
      const pairs = [
        ['ink on panel', get('ink'), panel], ['ink-dim on panel', get('ink-dim'), panel],
        ['ink-faint on panel', resolve(base, tokens['ink-faint']), panel], ['accent on panel', get('accent'), panel],
        ['signal ink on signal', get('signal-ink'), get('signal')], ['accent ink on accent', get('accent-ink'), get('accent')],
        // The wash (skins.css: the accent at 16 % over the panel) under a chosen Navigator
        // segment and the open section's tab, whose word is the accent or the ink.
        ['accent on its wash', get('accent'), mix(get('accent'), panel, share)],
        ['ink on the wash', get('ink'), mix(get('accent'), panel, share)],
      ];
      for (const [what, fg, bg] of pairs) {
        if (!/^#[0-9a-f]{3,8}$/i.test(fg) || !/^#[0-9a-f]{3,8}$/i.test(bg)) {
          rows.push({ skin, theme, what, ratio: 0, fg, bg, error: 'not a hex colour' });
          continue;
        }
        rows.push({ skin, theme, what, ratio: contrast(fg, bg), fg, bg });
      }
    }
  }
  return rows;
}

/** The device never re-colours the signal itself: RECALL is the machine's own signal red
 * (T-2655 reads the key's background against the page's --signal). Only its ink moves. */
export function signalMoved(navCss) {
  const block = /\/\* contrast:begin \*\/([\s\S]*?)\/\* contrast:end \*\//.exec(navCss)?.[1] ?? '';
  return /--signal\s*:/.test(block);
}

function run(skinsCss, navCss, { print = false } = {}) {
  const rows = measure(skinsCss, navCss);
  const bad = rows.filter((r) => !(r.ratio >= MIN));
  if (signalMoved(navCss)) bad.push({ skin: 'all', theme: '-', what: 'the Navigator re-colours --signal', ratio: 0, fg: '-', bg: '-',
    error: 'RECALL must stay the machine\'s own signal red; deepen --signal-ink instead' });
  if (print) for (const r of rows) console.log(`${r.ratio >= MIN ? 'ok  ' : 'FAIL'} ${r.skin}/${r.theme} ${r.what}: ${r.ratio.toFixed(2)} (${r.fg} on ${r.bg})`);
  return { rows, bad };
}

const args = process.argv.slice(2);
const skinsCss = fs.readFileSync(path.join(ROOT, 'renderers/web/css/skins.css'), 'utf8');
const navCss = fs.readFileSync(path.join(ROOT, 'renderers/web/css/navigator.css'), 'utf8');

if (args.includes('--self-test')) {
  let failures = 0;
  const expect = (label, cond) => { console.log(`   self-test | ${cond ? 'ok  ' : 'FAIL'} ${label}`); if (!cond) failures++; };
  expect('the tree as it stands passes', run(skinsCss, navCss).bad.length === 0);
  const noBlock = navCss.replace(/\/\* contrast:begin \*\/[\s\S]*?\/\* contrast:end \*\//, '');
  const without = run(skinsCss, noBlock).bad;
  expect('without the Navigator’s overrides the faint ink fails', without.some((r) => r.what === 'ink-faint on panel'));
  expect('…Retro Future’s light accent fails', without.some((r) => r.skin === 'worlds-fair' && r.theme === 'light' && r.what === 'accent on panel'));
  expect('…the wash under Deep Space’s light accent fails', without.some((r) => r.skin === 'deep-space' && r.theme === 'light' && r.what === 'accent on its wash'));
  expect('…and the two signal keys fail', without.some((r) => r.skin === 'control-room' && r.what === 'signal ink on signal')
    && without.some((r) => r.skin === 'worlds-fair' && r.what === 'signal ink on signal'));
  const pale = skinsCss.replace('--ink-dim:#A7B4C8', '--ink-dim:#3A4A66');
  expect('a dim ink drifted toward the panel is refused', run(pale, navCss).bad.some((r) => r.skin === 'control-room' && r.what === 'ink-dim on panel'));
  expect('re-colouring the signal itself is refused (RECALL stays the machine\'s red)',
    run(skinsCss, navCss.replace('/* contrast:end */', 'html[data-skin="brass"] .navigator { --signal: #9A6A20; }\n/* contrast:end */')).bad
      .some((r) => r.what === 'the Navigator re-colours --signal'));
  expect('contrast() is WCAG’s: black on white is 21:1', Math.abs(contrast('#000000', '#ffffff') - 21) < 1e-9);
  console.log(`   self-test | ${failures} failure(s)`);
  process.exit(failures ? 1 : 0);
}

const { rows, bad } = run(skinsCss, navCss, { print: args.includes('--print') });
if (bad.length) {
  console.error(`NAVIGATOR CONTRAST FAIL — ${bad.length} pair(s) under ${MIN}:1`);
  for (const r of bad) console.error(`  ${r.skin}/${r.theme} ${r.what}: ${r.ratio.toFixed(2)} (${r.fg} on ${r.bg})${r.error ? ` — ${r.error}` : ''}`);
  process.exit(1);
}
console.log(`NAVIGATOR CONTRAST PASS — ${rows.length} pairs across 4 machines x 2 tones, every one at ${MIN}:1 or better `
  + `(lowest ${Math.min(...rows.map((r) => r.ratio)).toFixed(2)})`);
