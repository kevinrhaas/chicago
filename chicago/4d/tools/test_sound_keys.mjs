#!/usr/bin/env node
/**
 * T-3571 — the Navigator's MUTE ALL and MUTE MUSIC keys (and the arrival's speaker): each
 * flips one Settings › Sound level between silence and its last audible level; the keys
 * stand in the Navigator's head and stand down with it when it docks; and lit is the quiet
 * kind on every machine (the owner, 2026-11-12: "when lit don't make it too dark red ...
 * more subtle so its noticeable but not shouty"), never a solid fill or the signal red.
 *
 *   node tools/test_sound_keys.mjs
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { MUTE_KEYS, flipSound, isMuted } from '../renderers/web/js/sound-keys.js';
import { SOUND_DEFAULTS, soundLevelsFrom } from '../renderers/web/js/settings-app.js';

const WEB = path.join(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..'), 'renderers/web');
// WCAG contrast (check_navigator_contrast.mjs runs on import, so its pair is restated here).
const lum = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
  .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  .reduce((s, c, i) => s + c * [0.2126, 0.7152, 0.0722][i], 0);
const contrast = (a, b) => { const [x, y] = [lum(a), lum(b)]; return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
const read = (p) => fs.readFileSync(path.join(WEB, p), 'utf8');

// ---- the flip -------------------------------------------------------------------------
{
  assert.deepEqual(MUTE_KEYS, { all: 'soundMaster', music: 'soundMusic' });
  const fresh = soundLevelsFrom({});
  assert.equal(isMuted(fresh, MUTE_KEYS.all), true, 'sound is off by default (T-2941), so MUTE ALL starts lit');
  assert.equal(isMuted(fresh, MUTE_KEYS.music), false, 'music has its own default level, so MUTE MUSIC starts dark');

  const on = flipSound(fresh, MUTE_KEYS.all);
  assert.deepEqual(on, { soundMaster: 0.8, soundLastMaster: 0.8, soundChosen: true }, 'unmuting with nothing kept restores 80 %');
  const off = flipSound({ ...fresh, ...on, soundMaster: 0.35 }, MUTE_KEYS.all);
  assert.deepEqual(off, { soundMaster: 0, soundLastMaster: 0.35, soundChosen: true }, 'muting keeps the level it silenced');
  assert.equal(flipSound({ soundMaster: 0, soundLastMaster: 0.35 }, MUTE_KEYS.all).soundMaster, 0.35, 'unmute puts it back');

  const m = flipSound({ soundMusic: 0.6 }, MUTE_KEYS.music);
  assert.deepEqual(m, { soundMusic: 0, soundLastMusic: 0.6, soundChosen: true });
  assert.equal(flipSound({ soundMusic: 0, ...m }, MUTE_KEYS.music).soundMusic, 0.6);
  assert.equal(flipSound({ soundMusic: 0 }, MUTE_KEYS.music).soundMusic, SOUND_DEFAULTS.soundMusic,
    'music with nothing kept comes back at its default');
  assert.equal(flipSound({ soundMusic: 0, soundLastMusic: 0 }, MUTE_KEYS.music).soundMusic, SOUND_DEFAULTS.soundMusic,
    'a kept 0 is not a level to restore');
  assert.equal(Object.hasOwn(flipSound(fresh, MUTE_KEYS.music), 'soundMaster'), false, 'MUTE MUSIC never touches the master');
  assert.throws(() => flipSound(fresh, 'soundEffects'), /no mute/);
}

// ---- the markup ------------------------------------------------------------------------
{
  const html = read('index.html');
  const head = html.slice(html.indexOf('<header class="nav-head"'), html.indexOf('</header>', html.indexOf('<header class="nav-head"')));
  for (const id of ['nav-mute-all', 'nav-mute-music']) {
    const tag = new RegExp(`<button[^>]*id="${id}"[^>]*>`).exec(head)?.[0];
    assert.ok(tag, `#${id} stands in the Navigator's head`);
    assert.match(tag, /type="button"/);
    assert.match(tag, /aria-pressed="(true|false)"/, `#${id} is a toggle`);
    assert.match(tag, /aria-label="Mute (all sound|music)"/);
  }
  assert.ok(head.indexOf('nav-mute-music') < head.indexOf('id="nav-close"'), 'the mute keys sit before the close key');
  const strings = read('js/strings/navigator.js');
  for (const k of ['mute.all', 'mute.music', 'mute.all.off', 'mute.music.off']) assert.ok(strings.includes(`'${k}'`), `nav.${k} is in the string table`);
  const main = read('js/main.js');
  assert.match(main, /from '\.\/sound-keys\.js'/);
  assert.match(main, /flipSoundKey\(k\.key\)/, 'main.js wires both mute keys');
}

// ---- lit is the quiet kind, on every machine -------------------------------------------
{
  const nav = read('css/navigator.css');
  assert.match(nav, /\.navigator\[data-detent="dock"\] :is\([^)]*\.nav-mute[^)]*\) \{ display: none; \}/, 'the docked device hides the mute keys');
  const skins = read('css/skins.css');
  assert.match(skins, /--lit-ink:var\(--accent\);/);
  assert.match(skins, /--lit-wash:color-mix\(in srgb,var\(--accent\) 12%,transparent\);/);
  // Every lit control: no solid accent fill, no signal colour.
  const lit = [
    ['css/drawer.css', /\.seg-btn\.is-on:hover, \.seg-btn\[aria-checked="true"\]:hover \{([^}]*)\}/],
    ['css/navigator.css', /\.nav-preset\[aria-pressed="true"\] \{([^}]*)\}/],
    ['css/navigator.css', /\.nav-look\[aria-pressed="true"\] \{([^}]*)\}/],
    ['css/navigator.css', /\.nav-mute\[aria-pressed="true"\], \.nav-mute\[aria-pressed="true"\]:hover \{([^}]*)\}/],
    ['css/evidence.css', /\.ev-pill\[aria-pressed="true"\] \{([^}]*)\}/],
    ['css/goto.css', /\.jump-pill\[aria-pressed="true"\] \{([^}]*)\}/],
    ['css/people.css', /\.pill\[aria-pressed="true"\], \.pill\[aria-pressed="true"\]:hover \{([^}]*)\}/],
    ['css/walk.css', /\.arrival-sound\[aria-pressed="true"\] \{([^}]*)\}/],
  ];
  for (const [file, re] of lit) {
    const body = re.exec(read(file))?.[1];
    assert.ok(body, `${file}: ${re.source.slice(0, 40)}… found`);
    assert.doesNotMatch(body, /background:\s*var\(--accent\)/, `${file}: a lit control is not a solid accent fill`);
    assert.doesNotMatch(body, /--signal/, `${file}: a lit control is never the signal colour`);
    assert.match(body, /--lit-(wash|ink)/, `${file}: a lit control wears the LIT tokens`);
  }
  // The lit word clears 4.5:1 on its 12 % wash over every machine's panel, both tones.
  const mix = (a, b, s) => `#${[0, 2, 4].map((i) => Math.round(parseInt(a.slice(1 + i, 3 + i), 16) * s
    + parseInt(b.slice(1 + i, 3 + i), 16) * (1 - s)).toString(16).padStart(2, '0')).join('')}`;
  const tone = (sel) => Object.fromEntries([...(new RegExp(`${sel.replace(/[[\]"]/g, '\\$&')} \\{([^}]*)\\}`).exec(skins)?.[1] ?? '')
    .matchAll(/--([\w-]+):(#[0-9A-Fa-f]{6})/g)].map((m) => [m[1], m[2]]));
  const machines = { 'control-room': 'light', brass: 'light', 'worlds-fair': 'dark', 'deep-space': 'light' };
  const deep = { 'worlds-fair:light': '#0F7178', 'deep-space:light': '#0B6386' };
  for (const [skin, other] of Object.entries(machines)) {
    const base = tone(`html[data-skin="${skin}"]`);
    for (const theme of ['dark', 'light']) {
      const t = theme === (skin === 'worlds-fair' ? 'light' : 'dark') ? base : { ...base, ...tone(`html[data-skin="${skin}"][data-theme="${other}"]`) };
      const ink = deep[`${skin}:${theme}`] ?? t.accent;
      const r = contrast(ink, mix(t.accent, t['panel-solid'], 0.12));
      assert.ok(r >= 4.5, `${skin} ${theme}: the lit word ${ink} on its wash is ${r.toFixed(2)}:1, under 4.5`);
    }
  }
  for (const [k, v] of Object.entries(deep)) {
    const [skin, theme] = k.split(':');
    const sel = skin === 'worlds-fair' ? 'html[data-skin="worlds-fair"]:not([data-theme="dark"])' : `html[data-skin="${skin}"][data-theme="${theme}"]`;
    assert.ok(skins.includes(`${sel} { --lit-ink:${v}; }`), `${k} deepens its lit word to ${v}`);
  }
}

console.log('sound keys: mute all and mute music flip their levels, stand in the Navigator\'s head, and lit is the quiet kind on every machine — ok');
