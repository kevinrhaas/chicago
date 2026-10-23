#!/usr/bin/env node
/**
 * T-2656 (NAV-903) — the Navigator's Settings app: its groups in the design's order, every
 * id the page and the smoke read kept, light or dark as a two-way choice, text size
 * 100-140 %, Auto, Sound's three levels (and what each covers, T-2659), What's new from
 * About, and the machine tiles painted in each machine's own colours.
 *
 *   node tools/test_settings_app.mjs
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  TEXT_SCALES, normalTextScale, applyTextScale, SOUND_DEFAULTS, soundLevelsFrom, normalVolume, volumeReadout,
  autoChoice, autoLine, onAuto, useAuto, themeOf, wireSettingsApp,
} from '../renderers/web/js/settings-app.js';
import { decide } from '../renderers/web/js/device-profile.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WEB = path.join(ROOT, 'renderers/web');
const html = fs.readFileSync(path.join(WEB, 'index.html'), 'utf8');
const settingsHtml = html.slice(html.indexOf('data-panel="settings"'), html.indexOf('</section>', html.indexOf('data-panel="settings"')));

// ---- the markup: the design's order, and nothing the page or the smoke reads lost -------
{
  const heads = [...settingsHtml.matchAll(/<h4[^>]*>([^<]*)<\/h4>/g)].map((m) => m[1].replace('&amp;', '&'));
  // T-3022: Research (the Expert research switch) leads, ahead of the design's order.
  assert.deepEqual(heads, ['Research', 'Display', 'Show', 'Movement', 'Machine', 'Performance', 'Sound', 'Units', "About & What's new"],
    'Settings reads Research, then Display, Show, Movement, Machine, Performance, Sound, Units, About & What\'s new (DESIGN §07)');
  const kept = ['s-units', 's-fov', 'v-fov', 's-road-aid', 'v-road-aid', 'road-aid-note', 's-brightness', 'v-brightness',
    'brightness-note', 's-detail', 's-quality', 's-governor', 'governor-line', 'device-line', 'pacing-read', 's-pacing-read',
    's-pacing-copy', 'pacing-read-status', 'pacing-read-out', 's-compass', 's-overview-map', 's-street-names',
    's-street-names-label', 's-look-tag', 'row-season', 's-season', 'row-street-trees', 's-street-trees', 'row-lot-lines',
    's-lot-lines', 's-show-control-help', 's-about', 's-about-build', 's-about-dev', 's-about-dev-note'];
  const added = ['s-display', 's-theme', 's-text-size', 's-machine', 's-skins', 's-perf-auto', 's-perf-auto-line', 's-sound',
    's-sound-master', 's-sound-effects', 's-sound-ambience', 'v-sound-master', 'v-sound-effects', 'v-sound-ambience',
    's-sound-note', 's-open-whatsnew'];
  for (const id of [...kept, ...added]) {
    assert.equal((html.match(new RegExp(`id="${id}"`, 'g')) ?? []).length, 1, `#${id} is on the page once`);
    assert(settingsHtml.includes(`id="${id}"`), `#${id} is in Settings`);
  }
  // Display holds light or dark, text size, brightness, field of view and road visibility, in that order.
  const display = settingsHtml.slice(settingsHtml.indexOf('id="s-display"'), settingsHtml.indexOf('<h4>Show</h4>'));
  const at = ['s-theme', 's-text-size', 's-brightness', 's-fov', 's-road-aid'].map((id) => display.indexOf(`id="${id}"`));
  assert(at.every((i, k) => i > 0 && (k === 0 || i > at[k - 1])), `Display's rows in order: ${at}`);
  // Text size offers 100 % to 140 %, and only those.
  const sizes = [...settingsHtml.slice(settingsHtml.indexOf('id="s-text-size"')).matchAll(/<option value="([\d.]+)">(\d+) %<\/option>/g)].slice(0, 5);
  assert.deepEqual(sizes.map((m) => Number(m[1])), [...TEXT_SCALES]);
  assert.deepEqual(sizes.map((m) => Number(m[2])), [100, 110, 120, 130, 140]);
  // Light or dark left the HUD for good, and the old chip with it.
  assert(!/id="btn-theme"/.test(html), 'the HUD chip is gone');
  // Sound says what each level covers, and that the ambience is not a recording (T-2659).
  assert.match(settingsHtml, /id="s-sound-note"[^>]*>Effects are the year ticker, the landing, and the Navigator's clicks and hum\. Ambience is a quiet tone for each destination, made up for mood: it is not a recording of the past\./);
  // About keeps T-2629's stamp, and opens What's new.
  const about = settingsHtml.slice(settingsHtml.indexOf('id="s-about"'));
  assert(about.indexOf('id="s-about-build"') > 0 && about.indexOf('id="s-open-whatsnew"') > about.indexOf('id="s-about-build"'));
  // The HUD wires the app, and its own theme listener is gone.
  const hud = fs.readFileSync(path.join(WEB, 'js/hud.js'), 'utf8');
  assert.match(hud, /wireSettingsApp\(\{/);
  assert(!/btnTheme/.test(hud), 'hud.js no longer holds a theme chip');
}

// ---- the machine tiles are each machine's own colours (skins.css) -------------------------
{
  const skinJs = fs.readFileSync(path.join(WEB, 'js/skin.js'), 'utf8');
  const skins = fs.readFileSync(path.join(WEB, 'css/skins.css'), 'utf8');
  const rows = [...skinJs.matchAll(/\{ id: '([\w-]+)', name: '([^']+)', tone: '(\w+)', tile: \[([^\]]+)\] \}/g)];
  assert.equal(rows.length, 4, 'four machines, each with a tile');
  for (const [, id, , , list] of rows) {
    const [panel, ink, accent, signal] = list.split(',').map((c) => c.trim().replace(/'/g, ''));
    const block = new RegExp(`html\\[data-skin="${id}"\\] \\{([^}]*)\\}`).exec(skins)?.[1] ?? '';
    const token = (k) => new RegExp(`--${k}:(#[0-9A-Fa-f]{6})`).exec(block)?.[1];
    assert.deepEqual([panel, ink, accent, signal], [token('panel-solid'), token('ink'), token('accent'), token('signal')],
      `${id}'s tile is its own panel, ink, accent and signal`);
  }
  assert.match(skinJs, /closest\('\.skin-tile'\)/, 'a tap on a tile applies its machine');
}

// ---- the text-size rules: raised text wraps, and never weakens a column's own breaking ----
{
  const css = fs.readFileSync(path.join(WEB, 'css/navigator.css'), 'utf8');
  const block = css.slice(css.indexOf('T-2656: text size 100-140 %'), css.indexOf('T-2656: Settings › Machine'));
  assert(block.length > 200, 'the text-size block is found');
  // break-word keeps an unbroken run's min-content width, so it pushed the drawer's eight
  // mounts past their 292 px column (smoke part 14); the device breaks `anywhere`, as
  // css/evidence.css does, or leaves the inherited rule alone.
  assert(!/overflow-wrap:\s*break-word/.test(block), 'no break-word in the device');
  // Go to's two-line clamp lifts above 100 % (the runner found six names cut at 140 %).
  assert.match(block, /html\[data-text-scale\] \.navigator \.welcome-destination strong \{[^}]*line-clamp: none/);
}

// ---- the pure parts ------------------------------------------------------------------
{
  assert.equal(normalTextScale('1.4'), 1.4);
  assert.equal(normalTextScale(1.5), 1);
  assert.equal(normalTextScale(undefined), 1);
  assert.deepEqual(SOUND_DEFAULTS, { soundMaster: 0, soundEffects: 1, soundAmbience: 1 }, 'sound is off by default: Master at 0 (owner, 2026-10-20, T-2941)');
  // T-2941: a first visit is silent; the old all-on defaults a whole-object save stored are not
  // a choice; a level moved off them, or any level once `soundChosen`, is kept.
  const silent = { soundChosen: false, soundMaster: 0, soundEffects: 1, soundAmbience: 1 };
  assert.deepEqual(soundLevelsFrom({}), silent, 'a first visit starts muted');
  assert.deepEqual(soundLevelsFrom(null), silent);
  assert.deepEqual(soundLevelsFrom({ soundMaster: 1, soundEffects: 1, soundAmbience: 1, fov: 70 }), silent,
    'the old defaults stored beside another setting are no sound choice');
  assert.deepEqual(soundLevelsFrom({ soundMaster: 0.5, soundEffects: 1, soundAmbience: 1 }),
    { soundChosen: true, soundMaster: 0.5, soundEffects: 1, soundAmbience: 1 }, 'a moved Master is kept');
  assert.deepEqual(soundLevelsFrom({ soundMaster: 1, soundEffects: 1, soundAmbience: 0 }),
    { soundChosen: true, soundMaster: 1, soundEffects: 1, soundAmbience: 0 }, 'a moved Ambience keeps every level');
  assert.deepEqual(soundLevelsFrom({ soundChosen: true, soundMaster: 1, soundEffects: 1, soundAmbience: 1 }),
    { soundChosen: true, soundMaster: 1, soundEffects: 1, soundAmbience: 1 }, 'sound turned on in Settings is remembered');
  assert.deepEqual(soundLevelsFrom({ soundChosen: true }), { soundChosen: true, ...SOUND_DEFAULTS });
  assert.equal(normalVolume('0.35'), 0.35);
  assert.equal(normalVolume(7), 1);
  assert.equal(normalVolume('x', 0.5), 0.5);
  assert.equal(volumeReadout(0), 'Off');
  assert.equal(volumeReadout(0.8), '80 %');
  // Auto is the profile's own choice, on a phone and on a desktop.
  const phone = autoChoice({ choice: decide('standard', { touch: true }) });
  assert.deepEqual(phone, { detail: 'light', quality: 1, governor: 'adaptive' });
  assert.equal(autoLine(phone), 'Auto for this device: Light detail, Low sharpness, adaptive pacing.');
  assert.equal(autoLine(autoChoice({ choice: decide('strong') })), 'Auto for this device: Full detail, High sharpness, adaptive pacing.');
  assert.equal(autoChoice(null), null);
  assert.equal(autoChoice({ choice: { detail: 'ultra', sharpness: 3 } }), null);
  assert.equal(onAuto({ detail: '', quality: '', governor: 'adaptive' }), true);
  assert.equal(onAuto({ detail: 'full', quality: '', governor: 'adaptive' }), false);
  assert.equal(onAuto({ detail: '', quality: '', governor: 'fixed' }), false);
  assert.deepEqual(useAuto({ detail: 'full', quality: 2, governor: 'fixed', fov: 80 }), { detail: '', quality: '', governor: 'adaptive', fov: 80 });
}

// ---- wired: a small page of the Settings rows --------------------------------------------
function fakePage() {
  const byId = new Map();
  const make = (tag, { id = null, cls = [], data = {}, parent = null } = {}) => {
    const attrs = new Map();
    const listeners = {};
    const el = {
      tagName: tag.toUpperCase(), id, dataset: { ...data }, hidden: false, disabled: false, value: '', textContent: '',
      children: [], parentElement: parent, style: { props: {}, setProperty(k, v) { this.props[k] = v; } },
      classList: { set: new Set(cls), toggle(c, on) { if (on) this.set.add(c); else this.set.delete(c); }, contains(c) { return this.set.has(c); } },
      setAttribute(k, v) { attrs.set(k, String(v)); }, getAttribute(k) { return attrs.has(k) ? attrs.get(k) : null; },
      addEventListener(type, fn) { (listeners[type] ??= []).push(fn); },
      fire(type) { for (const fn of listeners[type] ?? []) fn({ type, target: el }); },
      click() { el.fire('click'); },
      querySelectorAll(sel) {
        const want = sel.replace(/^\./, '');
        const out = [];
        const walk = (n) => { for (const c of n.children) { if (c.classList.contains(want)) out.push(c); walk(c); } };
        walk(el);
        return out;
      },
      closest(sel) {
        const want = sel.replace(/^\./, '');
        for (let n = el; n; n = n.parentElement) if (n.classList.contains(want)) return n;
        return null;
      },
    };
    if (parent) parent.children.push(el);
    if (id) byId.set(id, el);
    return el;
  };
  const root = make('html');
  root.setAttribute('data-theme', 'dark');
  const seg = make('div', { id: 's-theme', cls: ['seg'], parent: root });
  make('button', { cls: ['seg-btn'], data: { themeChoice: 'dark' }, parent: seg });
  make('button', { cls: ['seg-btn'], data: { themeChoice: 'light' }, parent: seg });
  make('select', { id: 's-text-size', parent: root });
  for (const id of ['s-detail', 's-quality', 's-governor']) make('select', { id, parent: root });
  const row = make('div', { cls: ['field', 'row'], parent: root });
  make('span', { id: 's-perf-auto-line', parent: row });
  make('button', { id: 's-perf-auto', parent: row });
  for (const slug of ['master', 'effects', 'ambience']) {
    make('input', { id: `s-sound-${slug}`, parent: root });
    make('b', { id: `v-sound-${slug}`, parent: root });
  }
  make('button', { id: 's-open-whatsnew', parent: root });
  return { documentElement: root, getElementById: (id) => byId.get(id) ?? null, byId };
}

{
  const doc = fakePage();
  const $ = (id) => doc.byId.get(id);
  const settings = { detail: 'full', quality: 2, governor: 'fixed', textScale: 1.3, soundEffects: 0.4 };
  const saved = []; const tones = []; const told = []; let whatsNew = 0;
  const app = wireSettingsApp({
    doc, settings, device: { choice: decide('standard') },
    save: () => saved.push(JSON.stringify(settings)), saveTheme: (t) => tones.push(t),
    onSetting: (k, v) => told.push([k, v]), openWhatsNew: () => { whatsNew++; },
  });
  // Light or dark: the page's tone is the one marked, and a tap sets and stores the other.
  const [dark, light] = $('s-theme').children;
  assert.equal(dark.getAttribute('aria-checked'), 'true');
  assert.equal(light.getAttribute('aria-checked'), 'false');
  light.click();
  assert.equal(themeOf(doc.documentElement), 'light');
  assert.deepEqual(tones, ['light']);
  assert.equal(light.getAttribute('aria-checked'), 'true');
  assert(light.classList.contains('is-on') && !dark.classList.contains('is-on'));
  // Text size: the stored scale is applied at once and shown; a new one is applied and stored.
  assert.equal(doc.documentElement.style.props['--text-scale'], '1.3');
  assert.equal($('s-text-size').value, '1.3');
  $('s-text-size').value = '1.4';
  $('s-text-size').fire('change');
  assert.equal(settings.textScale, 1.4);
  assert.equal(doc.documentElement.style.props['--text-scale'], '1.4');
  assert.equal(doc.documentElement.dataset.textScale, '1.4');
  assert.equal(doc.documentElement.style.props['--text-unscale'], '0.714286', 'the map is zoomed back by the inverse');
  assert.deepEqual(told.at(-1), ['textScale', 1.4]);
  assert.equal(JSON.parse(saved.at(-1)).textScale, 1.4);
  $('s-text-size').value = '9';
  $('s-text-size').fire('change');
  assert.equal(settings.textScale, 1, 'an unknown size falls back to 100 %');
  assert.equal(doc.documentElement.dataset.textScale, undefined);
  // Auto: the line names the device's levels; off Auto the key offers it, on it says so.
  assert.equal($('s-perf-auto-line').textContent, 'Auto for this device: Full detail, Medium sharpness, adaptive pacing.');
  assert.equal($('s-perf-auto').textContent, 'Use Auto');
  assert.equal($('s-perf-auto').disabled, false);
  told.length = 0;
  $('s-perf-auto').click();
  assert.deepEqual([settings.detail, settings.quality, settings.governor], ['', '', 'adaptive']);
  assert.deepEqual(told, [['detail', 'full'], ['quality', 1.5], ['governor', 'adaptive']]);
  assert.deepEqual([$('s-detail').value, $('s-quality').value, $('s-governor').value], ['full', '1.5', 'adaptive']);
  assert.equal(JSON.parse(saved.at(-1)).detail, '');
  assert.equal($('s-perf-auto').textContent, 'Using Auto');
  assert.equal($('s-perf-auto').disabled, true);
  // A choice by hand (the HUD stores it first) leaves Auto.
  settings.detail = 'balanced';
  $('s-detail').fire('change');
  assert.equal($('s-perf-auto').textContent, 'Use Auto');
  // Sound: the levels are read, defaulted and stored; their readouts say Off at nothing.
  assert.equal($('s-sound-master').value, '0', 'Master starts at Off (T-2941)');
  assert.equal($('v-sound-master').textContent, 'Off');
  assert.equal($('v-sound-effects').textContent, '40 %');
  assert.notEqual(settings.soundChosen, true, 'reading the levels is not choosing them');
  $('s-sound-master').value = '1';
  $('s-sound-master').fire('input');
  assert.equal(settings.soundMaster, 1);
  assert.equal(JSON.parse(saved.at(-1)).soundChosen, true, 'turning sound on is stored as the visitor\'s choice');
  assert.deepEqual(soundLevelsFrom(JSON.parse(saved.at(-1))).soundMaster, 1, 'and read back on the next visit');
  $('s-sound-ambience').value = '0';
  $('s-sound-ambience').fire('input');
  assert.equal(settings.soundAmbience, 0);
  assert.equal($('v-sound-ambience').textContent, 'Off');
  assert.equal(JSON.parse(saved.at(-1)).soundAmbience, 0);
  assert.deepEqual(told.at(-1), ['soundAmbience', 0]);
  // What's new, from About.
  $('s-open-whatsnew').click();
  assert.equal(whatsNew, 1);
  assert.equal(app.auto.detail, 'full');
}

{
  // No device profile: the Auto row stays out of sight rather than offering nothing.
  const doc = fakePage();
  wireSettingsApp({ doc, settings: {}, device: null });
  assert.equal(doc.byId.get('s-perf-auto').closest('.field').hidden, true);
  // A fake root without a style is left alone.
  assert.equal(applyTextScale(null, 1.2), 1.2);
}

console.log('SETTINGS APP PASS — Display, Show, Movement, Machine, Performance, Sound, Units, About & What\'s new in order with every id kept; '
  + 'light or dark is a two-way choice; text size 100–140 % applies and persists; Auto names and restores the device\'s levels; '
  + 'Sound\'s three levels persist and say what each covers; the machine tiles are each machine\'s own colours');
