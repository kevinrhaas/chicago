#!/usr/bin/env node
/**
 * T-2671 — the grade colours are ONE set, and they hold up.
 *
 *   node tools/check_grade_colors.mjs              the gate
 *   node tools/check_grade_colors.mjs --print      …and print every measurement
 *   node tools/check_grade_colors.mjs --self-test  prove each assertion fires
 *
 * Owner, 2026-10-16: "they look too similar attested and reconstructed maybe you
 * could do it as gold silver bronze and bronze is obviously browner than gold. Gold
 * being attested of course." The palette lives in js/confidence.js `GRADE_COLORS`
 * (the scene tint reads it there) and, because a stylesheet cannot import a module,
 * as the `--grade-<level>` / `--grade-<level>-ink` tokens in css/walk.css (:root for
 * the dark theme, [data-theme="light"] for the light one). This holds:
 *
 *   1. the stylesheet's tokens are the module's hexes, in both themes;
 *   2. no stylesheet paints a grade from a literal colour of its own instead of a
 *      token (a `.conf-*`, `.fact-*`, `.grade-*`, `.sw-*`, `.gc-*-att|inf|rec` rule);
 *   3. contrast, against the solid panel of the base theme and of all four machine
 *      skins (css/skins.css), in the theme's own tone: a fill 3:1, an ink 4.5:1, and
 *      an ink 4.5:1 on a chip's 12% wash of its fill;
 *   4. bronze is BROWNER than gold, not a darker gold: apart in CIE LCh hue by at
 *      least 15° and below it in lightness by at least 10 L*, for every role and
 *      for the scene tint;
 *   5. the three stay distinct (CIE76 ΔE ≥ 12 for every pair) to normal vision and
 *      under simulated protanopia, deuteranopia and tritanopia (Machado, Oliveira &
 *      Fernandes 2009, severity 1.0), for the fills, the inks and the scene tint.
 */
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.resolve(HERE, '../renderers/web');
const PRINT = process.argv.includes('--print');
const SELF_TEST = process.argv.includes('--self-test');
const LEVELS = ['attested', 'inferred', 'reconstructed'];
const THEMES = ['dark', 'light'];

// ---- colour arithmetic --------------------------------------------------------- //
const hexRgb = (h) => {
  const s = String(h).replace(/^#|^0x/i, '').toLowerCase();
  const full = s.length === 3 ? [...s].map((c) => c + c).join('') : s.padStart(6, '0');
  return [0, 2, 4].map((i) => parseInt(full.slice(i, i + 2), 16) / 255);
};
const sceneHex = (n) => `#${n.toString(16).padStart(6, '0')}`;
const lin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const unlin = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055);
const lum = (c) => { const [r, g, b] = c.map(lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const mix = (a, b, t) => a.map((v, i) => v * t + b[i] * (1 - t));
function lab(c) {
  const [r, g, b] = c.map(lin);
  const X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047;
  const Y = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  const Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883;
  const f = (t) => (t > 216 / 24389 ? Math.cbrt(t) : (24389 / 27 * t + 16) / 116);
  return [116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))];
}
const lch = (c) => { const [l, a, b] = lab(c); return { l, c: Math.hypot(a, b), h: (Math.atan2(b, a) * 180 / Math.PI + 360) % 360 }; };
const dE = (a, b) => Math.hypot(...lab(a).map((v, i) => v - lab(b)[i]));
const hueGap = (a, b) => { const d = Math.abs(a - b) % 360; return d > 180 ? 360 - d : d; };
const CVD = {
  protanopia: [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
  deuteranopia: [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
  tritanopia: [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]],
};
const simulate = (c, m) => {
  const l = c.map(lin);
  return m.map((row) => unlin(Math.min(1, Math.max(0, row[0] * l[0] + row[1] * l[1] + row[2] * l[2]))));
};

// ---- reading the sources ------------------------------------------------------- //
async function loadModulePalette() {
  // The palette is plain data at the module's top level, so the module is loaded with
  // `three` stubbed out: nothing here needs a renderer, or the vendored version's path.
  const source = await readFile(path.join(WEB, 'js/confidence.js'), 'utf8');
  const stubbed = source.replace("import * as THREE from 'three';", 'const THREE = {};');
  if (stubbed === source) throw new Error("confidence.js no longer imports three as `import * as THREE from 'three';` — update this loader");
  const url = `data:text/javascript;base64,${Buffer.from(stubbed).toString('base64')}`;
  return (await import(url)).GRADE_COLORS;
}

/** The declarations of every top-level rule whose selector list matches `test`. */
function blocks(css, test) {
  const out = [];
  const clean = css.replace(/\/\*[\s\S]*?\*\//g, '');
  for (const m of clean.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    if (test(m[1].trim())) out.push({ selector: m[1].trim(), body: m[2] });
  }
  return out;
}
const prop = (body, name) => body.match(new RegExp(`(?:^|;|\\s)${name.replace(/[-]/g, '\\-')}\\s*:\\s*([^;]+)`))?.[1].trim();

function cssPalette(walk) {
  const pick = (test) => {
    const pal = {};
    for (const { body } of blocks(walk, test)) {
      for (const level of LEVELS) {
        const fill = prop(body, `--grade-${level}`), ink = prop(body, `--grade-${level}-ink`);
        if (fill || ink) pal[level] = { ...(pal[level] || {}), ...(fill && { fill }), ...(ink && { ink }) };
      }
    }
    return pal;
  };
  return { dark: pick((s) => s === ':root'), light: pick((s) => s === '[data-theme="light"]') };
}

function panels(walk, skins) {
  const out = { dark: { base: prop(blocks(walk, (s) => s === ':root')[0].body, '--panel-solid') },
                light: { base: prop(blocks(walk, (s) => s === '[data-theme="light"]')[0].body, '--panel-solid') } };
  for (const { selector, body } of blocks(skins, (s) => /^html\[data-skin="[\w-]+"\]/.test(s))) {
    const solid = prop(body, '--panel-solid');
    if (!solid) continue;
    const skin = selector.match(/data-skin="([\w-]+)"/)[1];
    const themed = selector.match(/data-theme="(\w+)"/)?.[1];
    const tone = themed || (/color-scheme\s*:\s*light/.test(body) ? 'light' : 'dark');
    out[tone][skin] = solid;
  }
  return out;
}

// ---- the assertions -------------------------------------------------------------- //
function audit({ module, css, panelSet, sheets }) {
  const fails = [];
  const lines = [];
  const fail = (msg) => fails.push(msg);

  // 1. one set
  for (const theme of THEMES) for (const level of LEVELS) for (const role of ['fill', 'ink']) {
    const want = module[level]?.[theme]?.[role]?.toLowerCase();
    const got = css[theme]?.[level]?.[role]?.toLowerCase();
    if (!want) fail(`confidence.js GRADE_COLORS.${level}.${theme}.${role} is missing`);
    else if (want !== got) fail(`walk.css ${theme} --grade-${level}${role === 'ink' ? '-ink' : ''} is ${got ?? 'missing'}, GRADE_COLORS says ${want}`);
  }
  for (const level of LEVELS) if (!Number.isInteger(module[level]?.scene)) fail(`GRADE_COLORS.${level}.scene is not a 0x hex`);

  // 2. no stray literal grade colour
  const GRADE_SELECTOR = /\.(conf|fact|grade|sw|cm-sw|gc-(seg|sw|done))-(attested|inferred|reconstructed|doc|inf|rec|att)\b/;
  for (const [name, text] of Object.entries(sheets)) {
    for (const { selector, body } of blocks(text, (s) => GRADE_SELECTOR.test(s))) {
      if (/#[0-9a-f]{3,8}\b|rgba?\(|hsla?\(/i.test(body)) fail(`${name}: \`${selector}\` paints a grade from a literal colour, not a --grade-* token`);
    }
  }

  // 3. contrast
  for (const theme of THEMES) {
    for (const level of LEVELS) {
      const { fill, ink } = module[level][theme];
      for (const [panelName, panel] of Object.entries(panelSet[theme])) {
        const p = hexRgb(panel);
        const rf = ratio(hexRgb(fill), p), ri = ratio(hexRgb(ink), p);
        const rw = ratio(hexRgb(ink), mix(hexRgb(fill), p, 0.12));
        lines.push(`${theme.padEnd(5)} ${panelName.padEnd(13)} ${level.padEnd(13)} fill ${rf.toFixed(2)}  ink ${ri.toFixed(2)}  ink-on-wash ${rw.toFixed(2)}`);
        if (rf < 3) fail(`${theme} ${level} fill ${fill} is ${rf.toFixed(2)}:1 on ${panelName}'s panel ${panel} (needs 3:1)`);
        if (ri < 4.5) fail(`${theme} ${level} ink ${ink} is ${ri.toFixed(2)}:1 on ${panelName}'s panel ${panel} (needs 4.5:1)`);
        if (rw < 4.5) fail(`${theme} ${level} ink ${ink} is ${rw.toFixed(2)}:1 on its chip wash over ${panelName} (needs 4.5:1)`);
      }
    }
  }

  // 4 + 5. bronze is brown; all three distinct, under each simulation
  const sets = [['scene', Object.fromEntries(LEVELS.map((l) => [l, sceneHex(module[l].scene)]))]];
  for (const theme of THEMES) for (const role of ['fill', 'ink']) {
    sets.push([`${theme} ${role}`, Object.fromEntries(LEVELS.map((l) => [l, module[l][theme][role]]))]);
  }
  for (const [name, set] of sets) {
    const gold = lch(hexRgb(set.attested)), bronze = lch(hexRgb(set.reconstructed));
    const hg = hueGap(gold.h, bronze.h), lg = gold.l - bronze.l;
    lines.push(`${name.padEnd(10)} gold L*${gold.l.toFixed(1)} h${gold.h.toFixed(0)}  bronze L*${bronze.l.toFixed(1)} h${bronze.h.toFixed(0)}  hue apart ${hg.toFixed(0)}°, ${lg.toFixed(1)} L* darker`);
    if (hg < 15) fail(`${name}: bronze ${set.reconstructed} is only ${hg.toFixed(0)}° of hue from gold ${set.attested} (needs 15°) — a darker gold, not a brown`);
    if (lg < 10) fail(`${name}: bronze ${set.reconstructed} is only ${lg.toFixed(1)} L* below gold ${set.attested} (needs 10)`);
    for (const vision of ['normal', ...Object.keys(CVD)]) {
      const see = (h) => (vision === 'normal' ? hexRgb(h) : simulate(hexRgb(h), CVD[vision]));
      const pairs = [['attested', 'inferred'], ['attested', 'reconstructed'], ['inferred', 'reconstructed']];
      const ds = pairs.map(([a, b]) => dE(see(set[a]), see(set[b])));
      lines.push(`${name.padEnd(10)} ${vision.padEnd(12)} ΔE ${pairs.map(([a, b], i) => `${a.slice(0, 3)}/${b.slice(0, 3)} ${ds[i].toFixed(1)}`).join('  ')}`);
      ds.forEach((d, i) => { if (d < 12) fail(`${name} under ${vision}: ${pairs[i].join(' and ')} are ΔE ${d.toFixed(1)} apart (needs 12)`); });
    }
  }
  return { fails, lines };
}

const walk = await readFile(path.join(WEB, 'css/walk.css'), 'utf8');
const skins = await readFile(path.join(WEB, 'css/skins.css'), 'utf8');
const sheets = {};
for (const f of ['walk.css', 'card.css', 'people.css', 'evidence.css', 'businesses.css', 'goto.css', 'drawer.css', 'skins.css']) {
  sheets[f] = await readFile(path.join(WEB, 'css', f), 'utf8');
}
const real = { module: await loadModulePalette(), css: cssPalette(walk), panelSet: panels(walk, skins), sheets };

if (SELF_TEST) {
  // Each fixture breaks one promise; each must be refused, and the real palette must pass.
  const clone = (o) => JSON.parse(JSON.stringify(o));
  const cases = [];
  { const m = clone(real.module); m.reconstructed.dark.fill = '#9c7a22'; // a darker gold
    const c = clone(real.css); c.dark.reconstructed.fill = '#9c7a22';
    cases.push(['a bronze that is only a darker gold', { ...real, module: m, css: c }, /hue from gold/]); }
  { const c = clone(real.css); c.light.inferred.ink = '#123456';
    cases.push(['a stylesheet token drifting from GRADE_COLORS', { ...real, css: c }, /GRADE_COLORS says/]); }
  { const m = clone(real.module); m.attested.light.ink = '#c9a43a'; const c = clone(real.css); c.light.attested.ink = '#c9a43a';
    cases.push(['a light-theme ink too pale to read', { ...real, module: m, css: c }, /needs 4\.5:1/]); }
  { const m = clone(real.module); m.inferred.dark.fill = '#d6b23e'; const c = clone(real.css); c.dark.inferred.fill = '#d6b23e';
    cases.push(['a silver that has drifted to gold', { ...real, module: m, css: c }, /attested and inferred are ΔE/]); }
  cases.push(['a grade chip painted from a literal colour',
    { ...real, sheets: { ...real.sheets, 'fixture.css': '.conf-attested { color: #a9cf93; }' } }, /literal colour/]);
  let ok = audit(real).fails.length === 0;
  console.log(`self-test: the real palette passes ${ok ? 'ok' : 'FAIL'}`);
  for (const [label, input, expect] of cases) {
    const { fails } = audit(input);
    const caught = fails.some((f) => expect.test(f));
    ok &&= caught;
    console.log(`self-test: ${label} is refused ${caught ? 'ok' : 'FAIL'}${caught ? '' : ` (got: ${fails[0] ?? 'nothing'})`}`);
  }
  process.exit(ok ? 0 : 1);
}

const { fails, lines } = audit(real);
if (PRINT) for (const l of lines) console.log(`  ${l}`);
const panelCount = Object.values(real.panelSet).reduce((n, t) => n + Object.keys(t).length, 0);
if (fails.length) {
  for (const f of fails) console.log(`  FAIL ${f}`);
  process.exit(1);
}
console.log(`PASS grade colours: one set in confidence.js and walk.css; fills 3:1 and inks 4.5:1 on ${panelCount} panels `
  + '(base + four machines, both themes); bronze browner than gold; all three distinct under protanopia, deuteranopia and tritanopia');
