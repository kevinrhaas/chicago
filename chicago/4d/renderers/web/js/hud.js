/**
 * hud.js — year badge, confidence toggle, theme, hints.
 *
 * Deliberately small. The interface competes with the thing it is showing, so it
 * stays out of the way: a date, one switch that matters, and a line of text that
 * appears when there is something to say and fades when there is not.
 *
 * The confidence toggle is the only control here that changes what you are
 * looking at, and it is styled as the primary one for that reason.
 */

import { markSeen, renderWhatsNew, unseenCount } from './whatsnew.js';
import { isTyping } from './controls/pointerlock.js';
import { formatDistance, formatHeight, formatSpeed, formatStature, normalUnitSystem } from './units.js';
import { createGoTo } from './goto.js';
import { PACES, gaitName } from './travel.js';

const THEME_KEY = 'chicago4d.theme';
const CONF_KEY = 'chicago4d.confidence';
const HIDE_KEY = 'chicago4d.confidence.hidden';
const SET_KEY = 'chicago4d.settings';
const CONTROL_HELP_KEY = 'chicago4d.controlHelpDismissed';

const DEFAULT_SETTINGS = {
  // eyeHeight defaults to WALK.eyeHeight — the researched figure, not a taste.
  // It lives here so a visitor can raise it for comfort without the project
  // quietly restating the average height of an 1830s adult as something else.
  speed: 1.45, eyeHeight: 1.68, fov: 72, quality: 1.5,
  // R-A1. The road-legibility aid is OFF by default and off is the frame that
  // shipped before it existed. It is a viewing accommodation, not an
  // alternative reconstruction — see streets.js § R-A1 and ROADMAP R-A1.
  roadAid: 0,
  // K24, owner-requested. Brightness is OFF at 0 stops and 0 is the calibrated
  // grade the scene has always rendered at. Same standing as roadAid: a viewing
  // accommodation, never an alternative reconstruction — see world.js
  // § BASE_EXPOSURE and ROADMAP K24.
  brightness: 0,
  compass: true, overviewMap: true, streetNames: true, units: 'imperial',
  // '' = never chosen, so main.js's device guess stands (phone light, desktop full).
  detail: '',
  // The drawer's own choices. `pace` is how YOU move (walk, wagon, horse) and
  // `travelMode` is how Go to takes you somewhere (instantly, or at a pace, or
  // flying); they are two questions, so they are two keys. `gotoReconstructed`
  // is whether the Go to list shows the reconstructed roofs (off by default —
  // the owner's ruling). `headBob`: the rider's eye moves with the horse's gait.
  pace: 'walk', travelMode: 'instantly', headBob: true, gotoReconstructed: false,
  // The wagon's and the horse's own speeds (T-0823); `speed` above is the walk's.
  wagonSpeed: 3.6, horseSpeed: 6.5,
};

function readSettings() {
  try {
    return { ...DEFAULT_SETTINGS, ...JSON.parse(window.localStorage.getItem(SET_KEY) || '{}') };
  } catch { return { ...DEFAULT_SETTINGS }; }
}

function readStored(key, fallback) {
  try { return window.localStorage.getItem(key) ?? fallback; } catch { return fallback; }
}

function store(key, value) {
  try { window.localStorage.setItem(key, value); } catch { /* private mode */ }
}

export function createHud({
  root, scene, registry, intersections = [], people = null, positionOf = null, visitor = null,
  onConfidence, onFly, onHelp, onSetting, onGoTo, onHideLevel, onTravelStop,
  isTouch, resolvedDetail = 'full',
}) {
  const $ = (id) => root.querySelector(`#${id}`);
  const badgeYear = root.querySelector('.badge-year');
  const badgeSub = root.querySelector('.badge-sub');
  const badgeAlt = $('badge-alt');
  const btnConf = $('btn-confidence');
  const btnFly = $('btn-fly');
  const flyLabel = $('fly-label');
  const btnTheme = $('btn-theme');
  const btnHelp = $('btn-help');
  const panel = $('panel');
  const controlHelp = $('control-help');
  const hint = $('hint');
  const settings = readSettings();
  settings.units = normalUnitSystem(settings.units);

  if (badgeYear) badgeYear.textContent = scene?.id ?? '';
  if (badgeSub) badgeSub.textContent = formatSceneDate(scene?.target_date);

  // Theme: dark by default — this is a walkthrough, and a bright interface over
  // a daylight scene is the one combination that reads as neither.
  const theme = readStored(THEME_KEY, 'dark');
  document.documentElement.setAttribute('data-theme', theme === 'light' ? 'light' : 'dark');

  let hintTimer = 0;
  function say(text, ms = 2600) {
    if (!hint) return;
    hint.textContent = text;
    hint.classList.add('on');
    clearTimeout(hintTimer);
    if (ms) hintTimer = setTimeout(() => hint.classList.remove('on'), ms);
  }

  let confidenceOn = false;
  function setConfidence(on, { announce = true } = {}) {
    confidenceOn = !!on;
    btnConf?.setAttribute('aria-pressed', String(confidenceOn));
    store(CONF_KEY, confidenceOn ? '1' : '0');
    onConfidence?.(confidenceOn);
    if (announce) {
      say(confidenceOn
        ? 'Confidence view — amber is inferred, dithered massing is a guess'
        : 'Confidence view off');
    }
    return confidenceOn;
  }

  btnConf?.addEventListener('click', () => setConfidence(!confidenceOn));

  // ---- hiding a level ------------------------------------------------------
  //
  // The other half of the same control. Colouring answers "how sure are we";
  // hiding answers "what is left if you keep only what somebody wrote down",
  // and the second is the more searching question — turning off `reconstructed`
  // empties most of this town. That is the honest picture of how much of 1835
  // Chicago is recoverable, and it should be one click away rather than
  // something only the dataset knows.
  const LEVELS = ['attested', 'inferred', 'reconstructed'];
  const confGroup = $('confidence-group');
  const confMenu = $('confidence-menu');
  const btnConfMore = $('btn-confidence-more');
  let hiddenLevels = readHidden();

  function readHidden() {
    try {
      const raw = JSON.parse(window.localStorage.getItem(HIDE_KEY) || '[]');
      return new Set(Array.isArray(raw) ? raw.filter((l) => LEVELS.includes(l)) : []);
    } catch { return new Set(); }
  }

  // How many structures sit at each level, counted from the loaded registry.
  // A checkbox that says "Attested 12" and "Reconstructed 190" tells a visitor
  // the shape of this dataset before they have clicked anything, and it is a
  // number this project should lead with rather than bury.
  function paintCounts() {
    const tally = { attested: 0, inferred: 0, reconstructed: 0 };
    for (const record of registry?.values?.() ?? []) {
      const grade = record?.sidecar?.documented_range?.confidence;
      if (grade in tally) tally[grade] += 1;
    }
    for (const level of LEVELS) {
      const el = $(`cm-count-${level}`);
      if (el) el.textContent = String(tally[level]);
    }
    return tally;
  }

  function paintHidden() {
    for (const level of LEVELS) {
      const box = $(`cm-${level}`);
      if (box) box.checked = !hiddenLevels.has(level);
    }
    confGroup?.classList.toggle('has-hidden', hiddenLevels.size > 0);
    store(HIDE_KEY, JSON.stringify([...hiddenLevels]));
  }

  function setHidden(level, hide, { announce = true } = {}) {
    if (!LEVELS.includes(level)) return null;
    if (hide) hiddenLevels.add(level); else hiddenLevels.delete(level);
    paintHidden();
    onHideLevel?.(level, hide);
    if (announce) {
      // Name what is GONE, not what was clicked: a visitor who has hidden two
      // levels needs to know the town in front of them is partial.
      const gone = LEVELS.filter((l) => hiddenLevels.has(l));
      say(gone.length
        ? `Hiding ${gone.join(' and ')} — what stands is only what the rest of the evidence supports`
        : 'Showing every level again');
    }
    return hide;
  }

  function setConfMenu(open) {
    if (!confMenu) return;
    confMenu.toggleAttribute('hidden', !open);
    btnConfMore?.setAttribute('aria-expanded', String(!!open));
    if (open && document.pointerLockElement) document.exitPointerLock?.();
  }

  btnConfMore?.addEventListener('click', (e) => {
    e.stopPropagation();
    setConfMenu(confMenu?.hasAttribute('hidden'));
  });
  for (const level of LEVELS) {
    $(`cm-${level}`)?.addEventListener('change', (e) => setHidden(level, !e.target.checked));
  }
  $('cm-reset')?.addEventListener('click', () => {
    for (const level of LEVELS) setHidden(level, false, { announce: false });
    say('Showing every level again');
  });
  // Click-away, but not click-inside: the panel holds three checkboxes a visitor
  // will often want to toggle in one visit.
  document.addEventListener('click', (e) => {
    if (!confMenu || confMenu.hasAttribute('hidden')) return;
    if (confGroup?.contains(e.target)) return;
    setConfMenu(false);
  });

  // ---- free-fly -----------------------------------------------------------

  let flying = false;
  function setFly(on, { announce = true } = {}) {
    flying = !!on;
    btnFly?.setAttribute('aria-pressed', String(flying));
    if (flyLabel) flyLabel.textContent = flying ? 'Walk' : 'Fly';
    if (btnFly) {
      btnFly.title = flying ? 'Back to walking (F)' : 'Free-fly — rise above the town (F)';
    }
    if (!flying) { badgeAlt?.setAttribute('hidden', ''); badgeAlt?.parentElement?.classList.remove('has-alt'); }
    onFly?.(flying);
    if (announce) {
      say(flying
        // Said on entry because it is the honest frame for the view they are
        // about to get: from above, the edge of what has been built is visible,
        // and the ground beyond it is a skirt rather than a claim.
        // Say that inspect still works up here, and which key. Space is taken by
        // ascend in this mode, so a visitor who learned Space on foot finds the
        // one view that shows the whole town is the one where nothing answers.
        ? (isTouch ? 'Flying — ▲ ▼ to rise and descend, tap a building to inspect it.'
          : 'Flying — Space and Q to rise and descend, E or click to inspect a building.')
        : 'Back on foot');
    }
    return flying;
  }

  btnFly?.addEventListener('click', () => setFly(!flying));

  /** Altitude readout, driven from the frame loop. Stored internally in metres. */
  let lastAltitudeM = 0;
  function setAltitude(m) {
    lastAltitudeM = m;
    if (!badgeAlt) return;
    const show = flying && m > 1;
    badgeAlt.toggleAttribute('hidden', !show);
    badgeAlt.parentElement?.classList.toggle('has-alt', show);
    if (show) badgeAlt.textContent = `${formatHeight(m, settings.units)} up`;
  }

  btnTheme?.addEventListener('click', () => {
    const next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    store(THEME_KEY, next);
  });

  // ---- the controls / settings panel -------------------------------------
  //
  // Everything here was discoverable only by guessing before: run already
  // existed on Shift and nobody could know that. A walkthrough that does not
  // say how to walk is not finished.

  function panelOpen() { return panel && !panel.hasAttribute('hidden'); }

  function setPanel(open) {
    if (!panel) return;
    // Leaving focus on a control inside a drawer that has slid off-screen
    // strands the keyboard: the next Tab goes somewhere invisible.
    if (!open && panel.contains(document.activeElement)) document.activeElement.blur?.();
    panel.toggleAttribute('hidden', !open);
    // `.panel-open` on the HUD is what drawer.css keys the rest off: the card
    // TUCKS aside (never closes — its `hidden` is the state the gate reads),
    // and on a phone the navigation readouts hide under the sheet.
    root.classList.toggle('panel-open', !!open);
    btnHelp?.setAttribute('aria-pressed', String(!!open));
    // The navigation guide and the drawer share the right-hand slot; the guide
    // steps aside without being marked read, so it returns on the next boot.
    if (open && controlHelp && !controlHelp.hasAttribute('hidden')) dismissControlHelp({ remember: false });
    // Release the pointer lock on open. While the cursor is captured for
    // looking around, every click goes to the canvas and none of these controls
    // can be operated at all — the panel would look fine and do nothing.
    if (open && document.pointerLockElement) document.exitPointerLock?.();
    onHelp?.(!!open);
  }

  btnHelp?.addEventListener('click', () => setPanel(!panelOpen()));
  $('panel-close')?.addEventListener('click', () => setPanel(false));

  function dismissControlHelp({ remember = true } = {}) {
    if (!controlHelp) return;
    controlHelp.setAttribute('hidden', '');
    if (remember) store(CONTROL_HELP_KEY, '1');
    onHelp?.(false);
  }

  function showControlHelp({ auto = false } = {}) {
    if (!controlHelp || (auto && readStored(CONTROL_HELP_KEY, '0') === '1')) return false;
    setPanel(false);
    controlHelp.removeAttribute('hidden');
    if (document.pointerLockElement) document.exitPointerLock?.();
    onHelp?.(true);
    return true;
  }

  $('control-help-close')?.addEventListener('click', () => dismissControlHelp());
  $('control-help-gotit')?.addEventListener('click', () => dismissControlHelp());
  $('s-show-control-help')?.addEventListener('click', () => showControlHelp());
  $('control-help-desktop')?.toggleAttribute('hidden', !!isTouch);
  $('control-help-touch')?.toggleAttribute('hidden', !isTouch);

  // ---- What's new ---------------------------------------------------------
  //
  // Painted once, lazily, the first time the tab is actually opened. The
  // unseen marker clears on that same open — not on render — so the dot means
  // "you have not looked at this", which is the only thing it could honestly
  // mean if the panel paints the tab whether or not you visit it.

  const whatsNewDot = $('whatsnew-dot');
  const helpDot = $('help-dot');
  let whatsNewPainted = false;

  function paintUnseen() {
    const n = unseenCount();
    whatsNewDot?.toggleAttribute('hidden', n === 0);
    helpDot?.toggleAttribute('hidden', n === 0);
    if (n > 0) {
      btnHelp?.setAttribute('title',
        `Controls, settings and what's new — ${n} unread (H)`);
    }
  }
  paintUnseen();

  function openWhatsNew() {
    if (!whatsNewPainted) { renderWhatsNew($('whatsnew')); whatsNewPainted = true; }
    markSeen();
    paintUnseen();
  }

  const panelTitle = $('panel-title');
  const panelBack = $('panel-back');
  let currentTab = 'goto';
  /** What the head row says. A section may push a sub-view (the Evidence hub
   *  opening a topic) and hand back a title and a back action; `setTitle(null)`
   *  restores the section's own name. */
  let backAction = null;
  function setTitle(text, onBack = null) {
    const tab = root.querySelector(`.panel-tab[data-tab="${currentTab}"] .tab-label`);
    if (panelTitle) panelTitle.textContent = text ?? tab?.textContent ?? '';
    backAction = onBack;
    panelBack?.toggleAttribute('hidden', !onBack);
  }
  panelBack?.addEventListener('click', () => backAction?.());

  const panelScroll = $('panel-scroll');
  function selectTab(want) {
    currentTab = want;
    root.querySelectorAll('.panel-tab').forEach((x) => {
      const on = x.dataset.tab === want;
      x.classList.toggle('is-on', on);
      x.setAttribute('aria-selected', String(on));
    });
    root.querySelectorAll('.panel-body').forEach((s) => {
      s.toggleAttribute('hidden', s.dataset.panel !== want);
    });
    setTitle(null);
    // A new section starts at its top: the scroll column is shared, and the
    // Evidence list's depth must not carry over into Settings.
    if (panelScroll) panelScroll.scrollTop = 0;
    if (want === 'whatsnew') openWhatsNew();
    onTab?.(want);
  }
  /** A section can ask to be told when it is shown (the hub repaints, the
   *  Go to list refreshes its distances). */
  let onTab = null;

  // The rail is a list of sections: the arrow keys walk it when one has focus.
  root.querySelector('.panel-tabs')?.addEventListener('keydown', (e) => {
    const tabs = [...root.querySelectorAll('.panel-tab')];
    const i = tabs.indexOf(document.activeElement);
    if (i < 0) return;
    const step = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[e.key];
    if (!step) return;
    e.preventDefault();
    const next = tabs[(i + step + tabs.length) % tabs.length];
    next.focus();
    selectTab(next.dataset.tab);
  });

  root.querySelectorAll('.panel-tab').forEach((tab) => {
    tab.addEventListener('click', () => selectTab(tab.dataset.tab));
  });

  /** G, and the one route the touch build reaches by tapping the tab. */
  function openGoTo() {
    setPanel(true);
    selectTab('goto');
    // Only for a visitor who came by keyboard: focusing this on a phone raises
    // the on-screen keyboard over the list the tap was meant to open.
    if (!isTouch) {
      const input = $('jump-search');
      input?.focus();
      input?.select?.();
    }
  }

  // Show the control list that matches how this visitor is actually driving.
  $('keys-desktop')?.toggleAttribute('hidden', !!isTouch);
  $('keys-touch')?.toggleAttribute('hidden', !isTouch);

  function wireRange(id, label, key, fmt) {
    const el = $(id); const out = $(label);
    if (!el) return;
    el.value = String(settings[key]);
    const paint = () => { if (out) out.textContent = fmt(Number(el.value)); };
    paint();
    el.addEventListener('input', () => {
      settings[key] = Number(el.value);
      paint();
      onSetting?.(key, settings[key]);
      store(SET_KEY, JSON.stringify(settings));
    });
    return paint;
  }
  // Each pace's slider names the gait as it moves — "trot · 8.1 mph" — because a
  // number alone says nothing about what a horse is doing at it (T-0823).
  const gaitReadout = (pace) => (v) => `${gaitName(pace, v)} · ${formatSpeed(v, settings.units)}`;
  const paintSpeed = wireRange('s-speed', 'v-speed', 'speed', gaitReadout('walk'));
  const paintWagon = wireRange('s-wagon-speed', 'v-wagon-speed', 'wagonSpeed', gaitReadout('wagon'));
  const paintHorse = wireRange('s-horse-speed', 'v-horse-speed', 'horseSpeed', gaitReadout('horse'));
  // The readout names the researched default rather than only the number, so
  // moving off it is a visible choice instead of a silent drift.
  const paintEye = wireRange('s-eye', 'v-eye', 'eyeHeight',
    (v) => `${formatStature(v, settings.units)}${Math.abs(v - 1.68) < 0.01 ? ' — period eye level' : ''}`);
  wireRange('s-fov', 'v-fov', 'fov', (v) => `${Math.round(v)}°`);
  // R-A1, and it copies the eye-height precedent for the same reason: the
  // default position is the one the evidence and R-BUG3's measurement put
  // there, so the readout names it rather than showing a bare zero. Moving off
  // it is then a visible choice about your screen, not a silent drift into a
  // different claim about the town.
  wireRange('s-road-aid', 'v-road-aid', 'roadAid',
    (v) => (v <= 0 ? 'Off — the roads as recorded' : `+${Math.round(v * 100)}%`));
  // K24. Stops, not percent, and the calibrated position is named on its face
  // for the eye-height reason: this control brightens your screen, and the
  // readout has to make it impossible to read the brighter end as a claim that
  // the town was brighter. A stop is also the honest unit — it is what the
  // ceiling is bounded in (world.js § BASE_EXPOSURE).
  wireRange('s-brightness', 'v-brightness', 'brightness',
    (v) => (v <= 0 ? 'Calibrated — the light as measured' : `+${v.toFixed(2)} stop`));

  const units = $('s-units');
  if (units) {
    units.value = settings.units;
    units.addEventListener('change', () => {
      settings.units = normalUnitSystem(units.value);
      units.value = settings.units;
      paintSpeed?.();
      paintWagon?.();
      paintHorse?.();
      paintEye?.();
      paintTravelMode?.();
      goTo?.refreshDistances?.();
      setAltitude(lastAltitudeM);
      onSetting?.('units', settings.units);
      store(SET_KEY, JSON.stringify(settings));
    });
  }

  // Scene detail. Distinct from Render quality on purpose: quality is how many
  // PIXELS are drawn, detail is how much GEOMETRY. Conflating them would hide
  // which one a visitor with a slow machine actually needs to turn down.
  const detail = $('s-detail');
  if (detail) {
    // '' means the visitor has never chosen, and the level in force is the
    // device guess main.js made. Show THAT, not the first option in the list:
    // a phone running `light` must not display `Full`.
    detail.value = settings.detail || resolvedDetail;
    detail.addEventListener('change', () => {
      settings.detail = detail.value;
      onSetting?.('detail', settings.detail);
      store(SET_KEY, JSON.stringify(settings));
    });
  }

  const qual = $('s-quality');
  if (qual) {
    qual.value = String(settings.quality);
    qual.addEventListener('change', () => {
      settings.quality = Number(qual.value);
      onSetting?.('quality', settings.quality);
      store(SET_KEY, JSON.stringify(settings));
    });
  }

  function wireToggle(id, key) {
    const el = $(id);
    if (!el) return;
    el.checked = settings[key] !== false;
    el.addEventListener('change', () => {
      settings[key] = el.checked;
      onSetting?.(key, settings[key]);
      store(SET_KEY, JSON.stringify(settings));
    });
  }
  wireToggle('s-compass', 'compass');
  wireToggle('s-overview-map', 'overviewMap');
  wireToggle('s-street-names', 'streetNames');

  // ---- Travel: how Go to takes you there, and the pace you move at -------------
  //
  // Two questions, two controls. The segmented control in the Travel tab answers
  // "how do I get to a place I chose"; the pace chip in the top bar (mirrored by
  // the second control in the tab) answers "how fast do I move on my own". The
  // numbers behind both live in js/travel.js PACES; this only paints them.
  const btnPace = $('btn-pace');
  const paceLabel = $('pace-label');
  const PACE_CYCLE = ['walk', 'wagon', 'horse'];
  // Single-colour stroke glyphs, the rail's icon family at chip size. A walker,
  // a cart, a horseshoe: the horseshoe rather than a horse because a horse's
  // head does not survive sixteen pixels of stroke and a shoe does.
  const svg = (body) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" `
    + `stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
  const PACE_GLYPH = {
    walk: svg('<circle cx="13.5" cy="4.5" r="1.9"/><path d="M12.6 8.2 11 13.4 8.2 20.5"/>'
      + '<path d="M11 13.4l3.2 2.6.3 4.5"/><path d="M12.6 8.2l3.4 2.6"/><path d="M12.6 8.2 9.6 10.6 7.4 9.6"/>'),
    wagon: svg('<path d="M3.5 9.5h11.5v6H4.5"/><path d="M15 12.5h3.2l2.3 3"/><circle cx="7.5" cy="18" r="2"/>'
      + '<circle cx="16.5" cy="18" r="2"/><path d="M9.5 18h5"/><path d="M5.5 9.5V6.5h7.5v3"/>'),
    horse: svg('<path d="M6.5 19.5v-8a5.5 5.5 0 0 1 11 0v8"/><path d="M4.5 19.5h4M15.5 19.5h4"/>'
      + '<path d="M8.5 9h.01M15.5 9h.01M7 13h.01M17 13h.01M7 16.5h.01M17 16.5h.01"/>'),
  };
  function paintPace() {
    const pace = PACE_CYCLE.includes(settings.pace) ? settings.pace : 'walk';
    if (paceLabel) paceLabel.textContent = PACES[pace]?.label ?? pace;
    if (btnPace) {
      btnPace.dataset.pace = pace;
      const glyph = btnPace.querySelector('.pace-glyph');
      if (glyph) glyph.innerHTML = PACE_GLYPH[pace] ?? '';
      btnPace.title = `Your pace — ${PACES[pace]?.label ?? pace}. Tap for ${
        PACES[PACE_CYCLE[(PACE_CYCLE.indexOf(pace) + 1) % PACE_CYCLE.length]]?.label} (P)`;
    }
    root.querySelectorAll('#s-pace .seg-btn').forEach((b) => {
      b.setAttribute('aria-checked', String(b.dataset.pace === pace));
      b.classList.toggle('is-on', b.dataset.pace === pace);
    });
  }
  function setPace(pace, { announce = true } = {}) {
    if (!PACE_CYCLE.includes(pace)) return settings.pace;
    settings.pace = pace;
    store(SET_KEY, JSON.stringify(settings));
    paintPace();
    onSetting?.('pace', pace);
    if (announce) say(`${PACES[pace]?.label ?? pace} — ${PACES[pace]?.hint ?? ''}`.replace(/ — $/, ''));
    return pace;
  }
  btnPace?.addEventListener('click', () => {
    setPace(PACE_CYCLE[(PACE_CYCLE.indexOf(settings.pace) + 1) % PACE_CYCLE.length]);
  });
  root.querySelectorAll('#s-pace .seg-btn').forEach((b) => {
    b.addEventListener('click', () => setPace(b.dataset.pace));
  });

  function paintTravelMode() {
    const mode = settings.travelMode in PACES ? settings.travelMode : 'instantly';
    root.querySelectorAll('#s-travel .seg-btn').forEach((b) => {
      b.setAttribute('aria-checked', String(b.dataset.mode === mode));
      b.classList.toggle('is-on', b.dataset.mode === mode);
    });
    const note = $('travel-note');
    if (note) {
      const cap = (id) => formatSpeed(PACES[id].maxSpeed, settings.units);
      note.textContent = `Shift hurries you: ×${PACES.walk.sprintFactor} on foot, a gallop ×${PACES.horse.sprintFactor} `
        + `in the saddle, nothing on a wagon — never past the slider's top (${cap('walk')} on foot, `
        + `${cap('wagon')} by wagon, ${cap('horse')} on horseback).`;
    }
  }
  function setTravelMode(mode) {
    if (!(mode in PACES)) return settings.travelMode;
    settings.travelMode = mode;
    store(SET_KEY, JSON.stringify(settings));
    paintTravelMode();
    onSetting?.('travelMode', mode);
    return mode;
  }
  root.querySelectorAll('#s-travel .seg-btn').forEach((b) => {
    b.addEventListener('click', () => setTravelMode(b.dataset.mode));
  });
  wireToggle('s-head-bob', 'headBob');
  paintPace();
  paintTravelMode();

  // The ride in progress: where to, how far is left, and the one way to stop it
  // that is not simply moving. Painted by travel.js through this, at most a few
  // times a second.
  const banner = $('travel-banner');
  function travelBanner(state) {
    if (!banner) return;
    if (!state) { banner.setAttribute('hidden', ''); return; }
    const verb = $('travel-verb'); const dest = $('travel-dest'); const dist = $('travel-dist');
    if (verb) verb.textContent = state.verb ?? 'Going to';
    if (dest) dest.textContent = state.dest ?? '';
    if (dist) dist.textContent = Number.isFinite(state.dist_m) ? formatDistance(state.dist_m, settings.units) : '';
    banner.removeAttribute('hidden');
  }
  $('travel-stop')?.addEventListener('click', () => onTravelStop?.());

  // ---- Go to ---------------------------------------------------------------
  //
  // Everywhere you can stand and everyone who stood there, in one searchable
  // list. The list, its filters, its distances and its keyboard live in
  // js/goto.js; the HUD only hands it the section, the collections the renderer
  // loaded, and the visitor's position, and tells it when to go.
  const goTo = createGoTo({
    root: root.querySelector('[data-panel="goto"]'),
    scene, registry, intersections, people,
    positionOf, visitor, isTouch, settings,
    units: () => settings.units,
    onGoTo: (target) => { onGoTo?.(target); setPanel(false); },
    onPersist: (key, value) => { settings[key] = value; store(SET_KEY, JSON.stringify(settings)); },
  });


  window.addEventListener('keydown', (e) => {
    // One shared test, so the panel's shortcuts and the walker's movement keys
    // cannot come to disagree about what counts as typing. This one missed
    // <textarea> and contenteditable.
    if (isTyping(e.target)) {
      if (e.key === 'Escape' && panelOpen()) setPanel(false);
      return;
    }
    const k = e.key.toLowerCase();
    if (k === 'h' || k === '?') { e.preventDefault(); setPanel(!panelOpen()); }
    else if (k === 'c') { e.preventDefault(); setConfidence(!confidenceOn); }
    else if (k === 'n') { e.preventDefault(); setPanel(true); selectTab('whatsnew'); }
    else if (k === 'g') { e.preventDefault(); openGoTo(); }
    else if (k === 'f') { e.preventDefault(); setFly(!flying); }
    else if (k === 'p') { e.preventDefault(); setPace(PACE_CYCLE[(PACE_CYCLE.indexOf(settings.pace) + 1) % PACE_CYCLE.length]); }
    else if (e.key === 'Escape' && panelOpen()) setPanel(false);
  });

  return {
    say,
    settings,
    setPanel,
    selectTab,
    setTitle,
    /** Let one listener know which section is showing. */
    onTabChange(fn) { onTab = fn; },
    get tab() { return currentTab; },
    panelOpen,
    goTo,
    travelBanner,
    setPace,
    setTravelMode,
    paintTravelMode,
    showControlHelp,
    dismissControlHelp,
    get confidenceOn() { return confidenceOn; },
    setConfidence,
    get hiddenLevels() { return [...hiddenLevels]; },
    setHidden,
    /** Push the stored choice into the renderer at boot, without announcing it. */
    applyHidden() {
      paintCounts();
      paintHidden();
      for (const level of LEVELS) onHideLevel?.(level, hiddenLevels.has(level));
      return [...hiddenLevels];
    },
    get flying() { return flying; },
    setFly,
    setAltitude,
    /** Restore the visitor's last choice without narrating it back at them. */
    restore() {
      if (readStored(CONF_KEY, '0') === '1') setConfidence(true, { announce: false });
    },
    show() { root.removeAttribute('hidden'); },
    setLocked(locked) { document.body.classList.toggle('is-locked', !!locked); },
  };
}

function formatSceneDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December'];
  if (!y || !m || !d) return iso;
  return `${d} ${months[m - 1]}`;
}
