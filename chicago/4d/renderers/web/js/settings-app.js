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
 *   Sound        master, effects and ambience, which js/sound.js (T-2659) reads live; the
 *                note says what each covers, and that the ambience is mood, not a recording
 *   Units
 *   About        the build stamp (js/about.js, T-2629) and What's new. T-2657 adds
 *                Researcher mode here.
 *
 * T-3563 (the owner, 2026-11-12: "organize that settings card better with tabs and icons at the
 * top like ... the inspect card ... move whats new to one of those tabs maybe one of the last and
 * also the research mode should be at the end"): the groups are spread over one row of icon tabs
 * styled like Inspect's (T-3435): Display (with Machine and Units) · Show · Look (the new mouse
 * sensitivity, and Movement; not "Controls", which section 03 renamed Guide) · Graphics (Performance) · Sound · About · What's new ·
 * Research. What's new is still its own HUD section (its key, dot and every route to it stay);
 * its tab here selects that section, and the bar stays up over it.
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

/** The sound levels the HUD's settings carry (0..1). js/sound.js (T-2659) reads them on every
 * move. Sound is OFF by default (T-2941; the owner, 2026-10-20: "the sound is a bit much, can
 * you default that to off for now"), reversing the 2026-10-16 ruling: Master starts at 0, and
 * Effects and Ambience stay up, so moving Master alone turns every sound on. */
// T-3578: Narration (jaunt voices) joins them; at 1, like Effects and Ambience, it plays once Master is up.
export const SOUND_KEYS = Object.freeze(['soundMaster', 'soundEffects', 'soundAmbience', 'soundMusic', 'soundNarration']);
export const SOUND_DEFAULTS = Object.freeze({ soundMaster: 0, soundEffects: 1, soundAmbience: 1, soundMusic: 0.4, soundNarration: 1 });
/** The level every key had while sound was on by default (2026-10-16 to T-2941). */
const SOUND_WAS_DEFAULT = 1;

/**
 * The sound levels a stored settings object stands for (T-2941). The HUD stores its whole
 * settings object on any change, so a visitor who never touched Sound has the old all-on
 * defaults stored beside their real choices, and those 1s are not a choice to keep. A stored
 * level is the visitor's own when `soundChosen` is set (a slider was moved since T-2941), or
 * when any level differs from the old default (it can only have got there by a slider).
 * Otherwise every level is the default, which is silence. Returns the five levels and
 * `soundChosen`; never touches storage.
 */
export function soundLevelsFrom(saved) {
  const s = saved && typeof saved === 'object' ? saved : {};
  const moved = SOUND_KEYS.filter(k => k !== 'soundMusic' && k !== 'soundNarration').some((k) => s[k] != null && normalVolume(s[k], SOUND_WAS_DEFAULT) !== SOUND_WAS_DEFAULT);
  const chosen = s.soundChosen === true || moved;
  const out = { soundChosen: chosen };
  for (const k of SOUND_KEYS) out[k] = chosen ? normalVolume(s[k], SOUND_DEFAULTS[k]) : SOUND_DEFAULTS[k];
  return out;
}
export function normalVolume(value, fallback = 1) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.min(1, Math.max(0, n)) : fallback;
}
export function volumeReadout(value) {
  const v = normalVolume(value, 0);
  return v <= 0 ? str('settings.sound.off') : `${Math.round(v * 100)} %`;
}

/**
 * Look sensitivity (T-3563; the owner, 2026-11-12: "could you add a setting to adjust the mouse
 * sensitivity for the app?"). A multiple of the turn the app has always made: the mouse's
 * PointerLockControls.pointerSpeed (js/controls/pointerlock.js) and, on a touch screen, the
 * drag-to-look rate (js/controls/touch.js). 1 is Standard, which leaves both as they were.
 */
export const LOOK_SPEED = Object.freeze({ min: 0.2, max: 3, step: 0.1, standard: 1 });
export function normalLookSpeed(value) {
  const n = Number(value);
  if (value == null || value === '' || !Number.isFinite(n)) return LOOK_SPEED.standard;
  return Math.round(Math.min(LOOK_SPEED.max, Math.max(LOOK_SPEED.min, n)) * 10) / 10;
}
export function lookSpeedReadout(value) {
  const v = normalLookSpeed(value);
  return v === LOOK_SPEED.standard ? str('settings.look.standard') : `${v.toFixed(1)}×`;
}

/**
 * The card's tabs, in order (T-3563). Each group in the Settings section names its tab with
 * `data-set-pane`; `whatsnew` is the HUD's own What's new section, and Research is last.
 */
export const SETTINGS_TABS = Object.freeze(['display', 'show', 'look', 'graphics', 'sound', 'about', 'whatsnew', 'research']);
/** The HUD sections the bar stands over. */
export const SETTINGS_SECTIONS = Object.freeze(['settings', 'whatsnew']);
/** Each tab's glyph: single-colour line icons in currentColor, 24-unit box (as Inspect's). */
const SET_TAB_ICON = Object.freeze({
  display: '<rect x="3" y="4.5" width="18" height="12" rx="1.5"/><path d="M8.5 20h7M12 16.5V20"/>',
  show: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/>',
  look: '<rect x="6.5" y="3" width="11" height="18" rx="5.5"/><path d="M12 3v6.5M6.5 9.5h11"/>',
  graphics: '<path d="M4.2 17.5a8.5 8.5 0 1 1 15.6 0"/><path d="m12 13.5 4-4.5"/><circle cx="12" cy="13.5" r="1.3"/>',
  sound: '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11"/>',
  about: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.6v.4"/>',
  whatsnew: '<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2H4.5z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
  research: '<path d="M9 3h6M10 3v6l-5 9.5A1.7 1.7 0 0 0 6.5 21h11a1.7 1.7 0 0 0 1.5-2.5L14 9V3"/><path d="M7.5 15h9"/>',
});

/**
 * Draw and wire the tab bar (#settings-tabs). `selectSection(key)` is the HUD's selectTab and
 * `section()` reads which HUD section is showing. Returns `paint(section)` (the HUD calls it on
 * every section change), `select(tab)` and the tab in force, or null without the bar.
 */
export function wireSettingsTabs({ doc = globalThis.document, selectSection = () => {}, section = () => null } = {}) {
  const bar = doc?.getElementById?.('settings-tabs') ?? null;
  if (!bar) return null;
  const body = doc.querySelector?.('.panel-body[data-panel="settings"]') ?? null;
  let pane = SETTINGS_TABS[0];
  if (!bar.querySelector?.('[data-set-tab]')) {
    for (const key of SETTINGS_TABS) {
      const b = doc.createElement('button');
      b.type = 'button';
      b.className = 'set-tab';
      b.id = `set-tab-${key}`;
      b.dataset.setTab = key;
      b.setAttribute('role', 'tab');
      b.innerHTML = `<svg class="set-tab-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${SET_TAB_ICON[key]}</svg>`;
      const label = doc.createElement('span');
      label.className = 'set-tab-label';
      label.textContent = str(`settings.tab.${key}`);
      b.append(label);
      // What's new keeps its unread dot on its tab (hud.js paints it beside #whatsnew-dot).
      if (key === 'whatsnew') {
        const dot = doc.createElement('span');
        dot.className = 'set-tab-dot';
        dot.id = 'settings-whatsnew-dot';
        dot.hidden = true;
        dot.setAttribute('aria-hidden', 'true');
        b.append(dot);
      }
      bar.append(b);
    }
  }
  const buttons = () => [...bar.querySelectorAll('[data-set-tab]')];
  const paint = (now = section()) => {
    const shown = SETTINGS_SECTIONS.includes(now);
    bar.hidden = !shown;
    const sel = now === 'whatsnew' ? 'whatsnew' : pane;
    for (const b of buttons()) {
      const on = shown && b.dataset.setTab === sel;
      b.setAttribute('aria-selected', String(on));
      b.tabIndex = on ? 0 : -1;
    }
    for (const g of body?.querySelectorAll?.('.settings-group[data-set-pane]') ?? []) g.hidden = g.dataset.setPane !== pane;
    return sel;
  };
  const select = (key) => {
    if (!SETTINGS_TABS.includes(key)) return false;
    if (key === 'whatsnew') {
      if (section() !== 'whatsnew') selectSection('whatsnew');
      paint('whatsnew');
      return true;
    }
    pane = key;
    if (section() !== 'settings') selectSection('settings');
    paint('settings');
    // A tab opens at its top, as Inspect's do.
    const scroll = doc.getElementById?.('panel-scroll');
    if (scroll) scroll.scrollTop = 0;
    return true;
  };
  bar.addEventListener('click', (e) => {
    const b = e.target?.closest?.('[data-set-tab]');
    if (b) select(b.dataset.setTab);
  });
  bar.addEventListener('keydown', (e) => {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
    if (!step) return;
    const list = buttons();
    const i = list.indexOf(doc.activeElement);
    if (i < 0) return;
    e.preventDefault();
    const next = list[(i + step + list.length) % list.length];
    select(next.dataset.setTab);
    next.focus?.();
  });
  paint();
  return { paint, select, get pane() { return pane; } };
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
  onSetting = null, openWhatsNew = null, isTouch = false,
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

  // ---- Sound: five levels; main.js hands each move to js/sound.js (T-2659).
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
      // T-2941: a slider moved by the visitor is their choice, kept over the default from now on.
      settings.soundChosen = true;
      paint();
      save();
      onSetting?.(key, settings[key]);
    });
  }

  // ---- Look: mouse sensitivity (T-3563). A phone turns by a finger's drag, so it says Look.
  settings.lookSpeed = normalLookSpeed(settings.lookSpeed);
  const look = $('s-look-speed');
  const lookOut = $('v-look-speed');
  const lookLabel = $('s-look-speed-label');
  if (lookLabel) lookLabel.textContent = str(isTouch ? 'settings.look.touch' : 'settings.look.mouse');
  if (look) {
    look.value = String(settings.lookSpeed);
    const paintLook = () => { if (lookOut) lookOut.textContent = lookSpeedReadout(look.value); };
    paintLook();
    look.addEventListener('input', () => {
      settings.lookSpeed = normalLookSpeed(look.value);
      paintLook();
      save();
      onSetting?.('lookSpeed', settings.lookSpeed);
    });
  }

  // ---- About & What's new.
  $('s-open-whatsnew')?.addEventListener('click', () => openWhatsNew?.());

  return { paintTheme, setTheme, paintAuto, auto };
}
