/**
 * The Navigator's Settings app (T-2656, NAV-903; DESIGN §07 "Settings", §13 type rules).
 *
 * The drawer's Settings section moved into the Settings app as it was (T-2620); this lays
 * it out the way the design asks and adds what it lacked:
 *
 *   Display      light or dark, text size (100-140 %), brightness, field of view, road
 *                visibility; then Show, the labels and the map
 *   Machine      the four skins as preview tiles (js/skin.js paints and applies them)
 *   Performance  detail, sharpness and frame pacing, with an Auto key that puts back what
 *                this device's profile recommends (js/device-profile.js)
 *   Sound        master, effects and ambience. T-2659 makes the sounds; until it lands
 *                the group says nothing in the town makes one, and pretends to nothing
 *   Units
 *   About        the build stamp (js/about.js, T-2629) and What's new. T-2657 adds
 *                Researcher mode here.
 *
 * Every choice is a key of the HUD's one settings object, stored the way the others are
 * (hud.js `store`, which swallows a refused storage), so nothing here persists on its own.
 * Light or dark keeps its own key, `chicago4d.theme`, which js/skin.js reads before paint.
 */
import { t as str } from './strings/index.js';
import './strings/settings.js';

/** Text size: every Navigator app's text, 100 % to 140 % (QA-18). */
export const TEXT_SCALES = Object.freeze([1, 1.1, 1.2, 1.3, 1.4]);
export function normalTextScale(value) {
  const n = Number(value);
  return TEXT_SCALES.includes(n) ? n : 1;
}

/** The sound levels the HUD's settings carry (0..1, all up by default: the owner ruled
 * sound on by default, 2026-10-16). T-2659 reads them; they are kept now so its controls
 * are where the design puts them and a choice made today is still the visitor's then. */
export const SOUND_KEYS = Object.freeze(['soundMaster', 'soundEffects', 'soundAmbience']);
export const SOUND_DEFAULTS = Object.freeze({ soundMaster: 1, soundEffects: 1, soundAmbience: 1 });
export function normalVolume(value, fallback = 1) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.min(1, Math.max(0, n)) : fallback;
}
export function volumeReadout(value) {
  const v = normalVolume(value, 0);
  return v <= 0 ? str('settings.sound.off') : `${Math.round(v * 100)} %`;
}

const DETAIL_WORD = Object.freeze({ full: 'Full', balanced: 'Balanced', light: 'Light' });
const SHARP_WORD = Object.freeze({ 1: 'Low', 1.5: 'Medium', 2: 'High' });

/** What Auto chooses on this device: the profile's detail and sharpness, adaptive pacing.
 * null when there is no profile to read (the Auto row then stays out of sight). */
export function autoChoice(device) {
  const c = device?.choice;
  if (!c || !DETAIL_WORD[c.detail] || !SHARP_WORD[Number(c.sharpness)]) return null;
  return { detail: c.detail, quality: Number(c.sharpness), governor: 'adaptive' };
}

/** "Auto for this device: Full detail, Medium sharpness, adaptive pacing." */
export function autoLine(choice) {
  if (!choice) return '';
  return str('settings.auto.line', { detail: DETAIL_WORD[choice.detail], sharpness: SHARP_WORD[choice.quality] });
}

/** On Auto: the visitor has chosen neither detail nor sharpness, and pacing is adaptive. */
export function onAuto(settings) {
  return !settings?.detail && !settings?.quality && (settings?.governor || 'adaptive') === 'adaptive';
}

/** Put the settings back on Auto: no stored detail or sharpness, adaptive pacing. */
export function useAuto(settings) {
  settings.detail = '';
  settings.quality = '';
  settings.governor = 'adaptive';
  return settings;
}

/** The interface's tone as the page has it now. */
export function themeOf(root) {
  return root?.getAttribute?.('data-theme') === 'light' ? 'light' : 'dark';
}

/** Set the text scale the Navigator's screens read (css/navigator.css, --text-scale), and
 * mark the page while it is above 100 % (html[data-text-scale]). */
export function applyTextScale(root, value) {
  const v = normalTextScale(value);
  root?.style?.setProperty?.('--text-scale', String(v));
  // The map's scope stays at its own size inside a zoomed screen (a picture, sized from its
  // box), so it is zoomed back by the inverse.
  root?.style?.setProperty?.('--text-unscale', String(Math.round(1e6 / v) / 1e6));
  if (root?.dataset) {
    if (v > 1) root.dataset.textScale = String(v);
    else delete root.dataset.textScale;
  }
  return v;
}

/**
 * Wire the Settings app's new rows. `settings` is the HUD's own object; `save()` stores it,
 * `saveTheme(tone)` stores light or dark, `onSetting(key, value)` is main.js's handler, and
 * `openWhatsNew()` shows the What's new section.
 */
export function wireSettingsApp({
  doc = globalThis.document, settings, device = null, save = () => {}, saveTheme = () => {},
  onSetting = null, openWhatsNew = null,
} = {}) {
  const $ = (id) => doc?.getElementById?.(id) ?? null;
  const root = doc?.documentElement;

  // ---- Display: light or dark (it left the HUD with T-2625; here it is a two-way choice).
  const themeSeg = $('s-theme');
  const paintTheme = () => {
    const now = themeOf(root);
    themeSeg?.querySelectorAll('.seg-btn').forEach((b) => {
      const on = b.dataset.themeChoice === now;
      b.classList.toggle('is-on', on);
      b.setAttribute('aria-checked', String(on));
    });
    return now;
  };
  const setTheme = (tone) => {
    const next = tone === 'light' ? 'light' : 'dark';
    root?.setAttribute('data-theme', next);
    saveTheme(next);
    paintTheme();
    return next;
  };
  themeSeg?.querySelectorAll('.seg-btn').forEach((b) => b.addEventListener('click', () => setTheme(b.dataset.themeChoice)));
  // A machine picked from its tile brings its own tone (js/skin.js): keep the choice true.
  if (root && typeof globalThis.MutationObserver === 'function') {
    new globalThis.MutationObserver(paintTheme).observe(root, { attributes: true, attributeFilter: ['data-theme'] });
  }
  paintTheme();

  // ---- Display: text size.
  settings.textScale = applyTextScale(root, settings.textScale);
  const textSize = $('s-text-size');
  if (textSize) {
    textSize.value = String(settings.textScale);
    textSize.addEventListener('change', () => {
      settings.textScale = applyTextScale(root, textSize.value);
      save();
      onSetting?.('textScale', settings.textScale);
    });
  }

  // ---- Performance: Auto.
  const auto = autoChoice(device);
  const autoRow = $('s-perf-auto')?.closest?.('.field') ?? null;
  const autoKey = $('s-perf-auto');
  const autoText = $('s-perf-auto-line');
  const paintAuto = () => {
    if (autoRow) autoRow.hidden = !auto;
    if (!auto) return false;
    const on = onAuto(settings);
    if (autoText) autoText.textContent = autoLine(auto);
    if (autoKey) {
      autoKey.textContent = str(on ? 'settings.auto.on' : 'settings.auto.use');
      autoKey.disabled = on;
      autoKey.setAttribute('aria-pressed', String(on));
    }
    return on;
  };
  autoKey?.addEventListener('click', () => {
    if (!auto) return;
    useAuto(settings);
    save();
    const selects = { 's-detail': auto.detail, 's-quality': String(auto.quality), 's-governor': 'adaptive' };
    for (const [id, value] of Object.entries(selects)) { const el = $(id); if (el) el.value = value; }
    onSetting?.('detail', auto.detail);
    onSetting?.('quality', auto.quality);
    onSetting?.('governor', 'adaptive');
    paintAuto();
  });
  // A choice made by hand leaves Auto; the HUD stores it first (its listener came first).
  for (const id of ['s-detail', 's-quality', 's-governor']) $(id)?.addEventListener('change', () => paintAuto());
  paintAuto();

  // ---- Sound: three levels, kept for T-2659's sounds.
  for (const key of SOUND_KEYS) {
    settings[key] = normalVolume(settings[key], SOUND_DEFAULTS[key]);
    const slug = key.replace(/^sound/, '').toLowerCase();
    const el = $(`s-sound-${slug}`);
    const out = $(`v-sound-${slug}`);
    if (!el) continue;
    el.value = String(settings[key]);
    const paint = () => { if (out) out.textContent = volumeReadout(el.value); };
    paint();
    el.addEventListener('input', () => {
      settings[key] = normalVolume(el.value, SOUND_DEFAULTS[key]);
      paint();
      save();
      onSetting?.(key, settings[key]);
    });
  }

  // ---- About & What's new.
  $('s-open-whatsnew')?.addEventListener('click', () => openWhatsNew?.());

  return { paintTheme, setTheme, paintAuto, auto };
}
