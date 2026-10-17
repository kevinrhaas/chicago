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

import { describeProfile } from './device-profile.js';
import { markSeen, renderWhatsNew, unseenCount } from './whatsnew.js';
import { isTyping } from './controls/pointerlock.js';
import { formatDistance, formatHeight, formatSpeed, formatStature, normalUnitSystem } from './units.js';
import { createGoTo } from './goto.js';
import { PACES } from './travel.js';
import { GROUND_MODES, groundPace as groundOf, nextPace, moveView, travelModeFor, arriveOf } from './move-modes.js';
import { versionBadge } from './structure-versions.js';
import { t as str } from './strings/index.js';
import './strings/hud.js';

const THEME_KEY = 'chicago4d.theme';
const CONF_KEY = 'chicago4d.confidence';
const HIDE_KEY = 'chicago4d.confidence.hidden';
const SET_KEY = 'chicago4d.settings';

const DEFAULT_SETTINGS = {
  // eyeHeight defaults to WALK.eyeHeight — the researched figure, not a taste.
  // It lives here so a visitor can raise it for comfort without the project
  // quietly restating the average height of an 1830s adult as something else.
  speed: 1.45, eyeHeight: 1.68, fov: 72,
  // Image sharpness, the pixel-ratio cap. '' = never chosen, so main.js's device
  // guess stands: a phone starts at Low (1), a desktop at Medium (1.5) — the
  // owner's pick on T-2110, where Low drew a phone's frame 26-29 % faster. A
  // stored number is the visitor's own choice and is never overridden.
  quality: '',
  // T-2555: Frame pacing — 'adaptive' lets the frame governor draw a moving
  // frame at fewer pixels or a steady 30 fps on a device that cannot hold 60,
  // and is back at the Sharpness above the moment the camera rests; 'fixed'
  // draws every frame exactly at that Sharpness.
  governor: 'adaptive',
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
  // T-2736 (owner, 2026-10-17): the tag naming the building in the reticle; on by default,
  // and a visitor who finds it in the way turns it off under Settings › Show.
  lookTag: true,
  // T-2481: the 1904 Season — 'summer' (1 July, the scene's own date and the
  // default), 'spring', 'fall' or 'winter': ground, trees and sun. A viewing choice.
  season: 'summer',
  // T-2473: the 1904 parkway elms, 'shown' or 'hidden'.
  streetTrees: 'shown',
  // T-2692: the 1904 parcel lines on the ground, 'hidden' or 'shown'.
  lotLines: 'hidden',
  // '' = never chosen, so main.js's device guess stands (phone light, desktop full).
  detail: '',
  // The drawer's own choices. `pace` is how YOU move (walk, run, wagon, horse) and
  // `travelMode` is how Go to takes you somewhere (instantly, or at a pace, or
  // flying); they are two questions, so they are two keys. (`gotoReconstructed`, the
  // Go to list's own checkbox, is gone: Go to follows the Confidence view, T-2633.)
  // `headBob`: the rider's eye moves with the horse's gait.
  pace: 'walk', travelMode: 'instantly', headBob: true,
  // The wagon's and the horse's own speeds (T-0823) and the run's (T-2651); `speed`
  // above is the walk's.
  wagonSpeed: 3.6, horseSpeed: 6.5, runSpeed: 3.4,
  // T-2652: whether the visitor has picked a getting-there choice themselves. Until they
  // have, a Jaunt rides at its own recommended mode (js/getting-there.js § jauntModeFor).
  arriveChosen: false,
  // T-2653: a drag to look on a touch screen turns in steps (Move › Comfort).
  snapTurn: false,
};

function readSettings() {
  try {
    const saved = JSON.parse(window.localStorage.getItem(SET_KEY) || '{}') ?? {};
    // T-2481: T-2473 kept the season in `streetTrees` ('summer' | 'spring' |
    // 'winter' | 'hidden'); it is now its own setting and the trees are shown or hidden.
    if (['summer', 'spring', 'winter'].includes(saved.streetTrees)) {
      saved.season ??= saved.streetTrees;
      saved.streetTrees = 'shown';
    }
    return { ...DEFAULT_SETTINGS, ...saved };
  } catch { return { ...DEFAULT_SETTINGS }; }
}

function readStored(key, fallback) {
  try { return window.localStorage.getItem(key) ?? fallback; } catch { return fallback; }
}

function store(key, value) {
  try { window.localStorage.setItem(key, value); } catch { /* private mode */ }
}

export function createHud({
  root, destinations, scene, registry, intersections = [], people = null, positionOf = null, visitor = null,
  onConfidence, onConfidenceKey = null, onFly, onHelp, onSetting, onGoTo, onHideLevel, onTravelStop, onShowGuide,
  isTouch, resolvedDetail = 'full', resolvedQuality = 1.5, lowered = null, device = null, structureVersion = null,
}) {
  // T-2620: the drawer's sections live inside the Navigator now (a sibling of #hud), so
  // lookups by id and of the sections' own parts are made in the document, not under #hud.
  const doc = root.ownerDocument ?? document;
  const $ = (id) => doc.getElementById(id) ?? root.querySelector(`#${id}`);
  const badgeYear = root.querySelector('.badge-year');
  const badgeSub = root.querySelector('.badge-sub');
  const badgeAlt = $('badge-alt');
  const btnConf = $('btn-confidence');
  const btnFly = $('btn-fly');
  const flyLabel = $('fly-label');
  const btnTheme = $('btn-theme');
  const btnHelp = $('btn-help');
  const panel = $('panel');
  const hint = $('hint');
  const settings = readSettings();
  settings.units = normalUnitSystem(settings.units);

  if (badgeYear) badgeYear.textContent = scene?.id ?? '';
  // T-2626: the year chip reads as LED digits, 1904 · 07.01; it says the date in words
  // to a screen reader, with what a tap does.
  if (badgeSub) badgeSub.textContent = (/^\d{4}-(\d{2})-(\d{2})/.exec(scene?.target_date ?? '') ?? []).slice(1).join('.');
  $('year-badge')?.setAttribute('aria-label',
    `${[formatSceneDate(scene?.target_date), scene?.id].filter(Boolean).join(' ')}. Open Jump`);

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

  // ---- which build of a structure is showing (T-1727) -----------------------
  //
  // `?structure=<id>&version=<label>` swaps one building for a committed alternate so
  // competing builds can be compared side by side. The chip rides in the year badge for
  // as long as the page is open, so two screenshots of the same corner can never be
  // confused — and when the label was NOT found it says "default shown" in the warning
  // tone rather than letting a typo pass for a comparison. Tap it for the full sentence.
  const badgeVersion = $('badge-version');
  const versionChip = versionBadge(structureVersion);
  if (badgeVersion && versionChip) {
    badgeVersion.textContent = versionChip.text;
    badgeVersion.title = versionChip.title;
    badgeVersion.setAttribute('aria-label', versionChip.title);
    badgeVersion.dataset.tone = versionChip.tone;
    badgeVersion.removeAttribute('hidden');
    badgeVersion.closest('.badge')?.classList.add('has-version');
    badgeVersion.addEventListener('click', () => say(versionChip.title, 7000));
  }
  function announceStructureVersion() {
    if (!versionChip) return false;
    say(versionChip.announce, versionChip.tone === 'notice' ? 9000 : 5000);
    return true;
  }

  let confidenceOn = false;
  /** Tell whoever shows the Confidence view's state (the Navigator's app, T-2647) that it moved. */
  function confidenceChanged() {
    try { document.dispatchEvent(new CustomEvent('chicago4d-confidence')); } catch { /* no DOM */ }
  }
  function setConfidence(on, { announce = true } = {}) {
    confidenceOn = !!on;
    btnConf?.setAttribute('aria-pressed', String(confidenceOn));
    store(CONF_KEY, confidenceOn ? '1' : '0');
    onConfidence?.(confidenceOn);
    confidenceChanged();
    if (announce) {
      say(confidenceOn
        ? 'Confidence view — gold is Attested, silver Inferred, dithered bronze Reconstructed'
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
  // The chip, its caret and its menu moved into the Navigator's Confidence view app
  // (T-2647, js/apps/confidence-view.js), which reads and sets this state through
  // `hiddenLevels`, `setHidden` and `levelCounts`; the HUD keeps the state.
  let hiddenLevels = readHidden();
  // T-2633: Go to dims what the Confidence view hides; repainted when that changes.
  let afterHide = null;

  function readHidden() {
    try {
      const raw = JSON.parse(window.localStorage.getItem(HIDE_KEY) || '[]');
      return new Set(Array.isArray(raw) ? raw.filter((l) => LEVELS.includes(l)) : []);
    } catch { return new Set(); }
  }

  // How many structures sit at each level, counted from the loaded registry.
  // A checkbox that says "Attested 12" and "Reconstructed 190" tells a visitor
  // the shape of this dataset before they have clicked anything, and it is a
  // number this project should lead with rather than bury. Counted by the
  // STRUCTURE's grade (T-2686, AGENTS.md rule 12): pictured, recorded, or placed by
  // our reconstruction — the stood-here grade only where a sidecar predates it.
  function paintCounts() {
    const tally = { attested: 0, inferred: 0, reconstructed: 0 };
    for (const record of registry?.values?.() ?? []) {
      const grade = record?.sidecar?.grade?.value ?? record?.sidecar?.documented_range?.confidence;
      if (grade in tally) tally[grade] += 1;
    }
    for (const level of LEVELS) {
      const el = $(`cm-count-${level}`);
      if (el) el.textContent = String(tally[level]);
    }
    return tally;
  }

  function paintHidden() {
    store(HIDE_KEY, JSON.stringify([...hiddenLevels]));
  }

  function setHidden(level, hide, { announce = true } = {}) {
    if (!LEVELS.includes(level)) return null;
    if (hide) hiddenLevels.add(level); else hiddenLevels.delete(level);
    paintHidden();
    onHideLevel?.(level, hide);
    afterHide?.();
    confidenceChanged();
    if (announce) {
      // Name what is GONE, not what was clicked: a visitor who has hidden two
      // levels needs to know the town in front of them is partial.
      const gone = LEVELS.filter((l) => hiddenLevels.has(l));
      say(gone.length
        ? `Hiding ${gone.map((l) => l[0].toUpperCase() + l.slice(1)).join(' and ')} — what stands is only what the rest of the evidence supports`
        : str('hud.levels.all'));
    }
    return hide;
  }

  // ---- free-fly -----------------------------------------------------------

  let flying = false;
  // Move's picker shows Fly while flying (T-2651); it is wired further down.
  let paintMoveHook = null;
  function setFly(on, { announce = true } = {}) {
    flying = !!on;
    btnFly?.setAttribute('aria-pressed', String(flying));
    if (flyLabel) flyLabel.textContent = str(flying ? 'hud.fly.walk' : 'hud.fly.fly');
    if (btnFly) {
      btnFly.title = str(flying ? 'hud.fly.back' : 'hud.fly.up');
    }
    if (!flying) { badgeAlt?.setAttribute('hidden', ''); badgeAlt?.parentElement?.classList.remove('has-alt'); }
    paintMoveHook?.();
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

  // T-2620: the drawer is gone; its sections are Navigator apps. `host` is the Navigator's
  // adapter (apps/drawer-host.js): setPanel and selectTab keep their meaning — open the
  // section, close it — and the host shows or docks the app that holds it.
  let host = null;
  function setPanel(open, { fromHost = false } = {}) {
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
    // Release the pointer lock on open. While the cursor is captured for
    // looking around, every click goes to the canvas and none of these controls
    // can be operated at all — the panel would look fine and do nothing.
    if (open && document.pointerLockElement) document.exitPointerLock?.();
    onHelp?.(!!open);
    if (!fromHost) host?.[open ? 'open' : 'close']?.(currentTab);
  }

  btnHelp?.addEventListener('click', () => setPanel(!panelOpen()));
  $('panel-close')?.addEventListener('click', () => setPanel(false));

  // ---- The controls: Guide's sheet in the Navigator (T-2661) ----------------
  //
  // The control-help popover is gone: the controls live in the Navigator's Guide, which
  // shows touch or keyboard from controls/intent.js. Settings' "Show the controls" opens it.
  function showControlHelp() {
    // T-2620: with the sections in the Navigator, switching to Guide puts Settings' section
    // away itself; closing it first would dock the device only to open it again.
    if (!host) setPanel(false);
    if (document.pointerLockElement) document.exitPointerLock?.();
    onShowGuide?.();
    return true;
  }
  /** Nothing to dismiss now that the popover is gone; kept for callers written before it. */
  function dismissControlHelp() { return false; }
  $('s-show-control-help')?.addEventListener('click', () => showControlHelp());

  // ---- What's new ---------------------------------------------------------
  //
  // Painted once, lazily, the first time the tab is actually opened. The
  // unseen marker clears on that same open — not on render — so the dot means
  // "you have not looked at this", which is the only thing it could honestly
  // mean if the panel paints the tab whether or not you visit it.

  const whatsNewDot = $('whatsnew-dot');
  const helpDot = $('help-dot');
  let whatsNewPainted = false;

  // The count is a promise since T-1973: on the published page it comes from the
  // release numbers publish.sh writes into the page and settles at once; the
  // changelog itself is imported only by the tab. A count that cannot be read
  // leaves the dots as the markup has them (hidden) rather than inventing news.
  async function paintUnseen() {
    let n;
    try { n = await unseenCount(); } catch { return; }
    whatsNewDot?.toggleAttribute('hidden', n === 0);
    helpDot?.toggleAttribute('hidden', n === 0);
    if (n > 0) {
      btnHelp?.setAttribute('title', str('hud.menu.unread', { n }));
    }
  }
  void paintUnseen();

  async function openWhatsNew() {
    const host = $('whatsnew');
    if (!whatsNewPainted) {
      whatsNewPainted = true;
      host?.setAttribute('aria-busy', 'true');
      try {
        await renderWhatsNew(host);
      } catch {
        whatsNewPainted = false;
        if (host) host.textContent = str('hud.notes.failed');
        return;
      } finally {
        host?.removeAttribute('aria-busy');
      }
    }
    await markSeen();
    await paintUnseen();
  }

  const panelTitle = $('panel-title');
  const panelBack = $('panel-back');
  let currentTab = 'goto';
  /** What the head row says. A section may push a sub-view (the Evidence hub
   *  opening a topic) and hand back a title and a back action; `setTitle(null)`
   *  restores the section's own name. */
  let backAction = null;
  function setTitle(text, onBack = null) {
    const tab = doc.querySelector(`.panel-tab[data-tab="${currentTab}"]`);
    // The head says the section's full name, which the rail cannot always afford:
    // eight tabs share 390 px on a phone, so a long one carries a short label and
    // a `data-title`. Where there is no `data-title` the two are the same word.
    const name = tab?.dataset.title || tab?.querySelector('.tab-label')?.textContent;
    if (panelTitle) panelTitle.textContent = text ?? name ?? '';
    backAction = onBack;
    panelBack?.toggleAttribute('hidden', !onBack);
  }
  panelBack?.addEventListener('click', () => backAction?.());

  const panelScroll = $('panel-scroll');
  function selectTab(want, { fromHost = false } = {}) {
    // A section the scene does not carry (T-1740) is never selected, by any route.
    // T-2620: Go to retired with the drawer; asking for it opens the Jaunts app's own Go to.
    if (doc.querySelector(`.panel-tab[data-tab="${want}"]`)?.hidden) {
      if (want === 'goto' && !fromHost) host?.show?.('goto');
      return;
    }
    currentTab = want;
    doc.querySelectorAll('.panel-tab').forEach((x) => {
      const on = x.dataset.tab === want;
      x.classList.toggle('is-on', on);
      x.setAttribute('aria-selected', String(on));
    });
    doc.querySelectorAll('.panel-body').forEach((s) => {
      s.toggleAttribute('hidden', s.dataset.panel !== want);
    });
    setTitle(null);
    // A new section starts at its top: the scroll column is shared, and the
    // Evidence list's depth must not carry over into Settings.
    if (panelScroll) panelScroll.scrollTop = 0;
    if (want === 'whatsnew') void openWhatsNew().catch(() => {});
    onTab?.(want);
    if (!fromHost && panelOpen()) host?.show?.(want);
  }
  /** A section can ask to be told when it is shown (the hub repaints, the
   *  Go to list refreshes its distances). */
  let onTab = null;

  // The rail is a list of sections: the arrow keys walk it when one has focus.
  doc.querySelector('.panel-tabs')?.addEventListener('keydown', (e) => {
    const tabs = [...doc.querySelectorAll('.panel-tab')].filter((t) => !t.hidden);
    const i = tabs.indexOf(document.activeElement);
    if (i < 0) return;
    const step = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[e.key];
    if (!step) return;
    e.preventDefault();
    const next = tabs[(i + step + tabs.length) % tabs.length];
    next.focus();
    selectTab(next.dataset.tab);
  });

  doc.querySelectorAll('.panel-tab').forEach((tab) => {
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
      paintEye?.();
      paintMove?.();
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
    // T-2547: after a crash the guard's step-down outranks the stored choice until
    // the visitor picks again, so show the level actually in force.
    detail.value = (lowered?.detail ? '' : settings.detail) || resolvedDetail;
    detail.addEventListener('change', () => {
      settings.detail = detail.value;
      onSetting?.('detail', settings.detail);
      store(SET_KEY, JSON.stringify(settings));
    });
  }

  // T-2559: what the device profile chose, and that a choice above beats it.
  const deviceLine = $('device-line');
  if (deviceLine && device) {
    deviceLine.textContent = `${describeProfile(device)} A choice you make above overrides it.`;
    deviceLine.title = device.why || '';
    deviceLine.hidden = false;
  }

  const qual = $('s-quality');
  if (qual) {
    // Like Scene detail: show the ratio in force, which for a visitor who never
    // chose is main.js's device guess — a phone at Low must not display Medium.
    qual.value = String((lowered?.quality ? '' : settings.quality) || resolvedQuality);
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
  const wireSelect = (id, key, fallback) => {
    const sel = $(id);
    if (!sel) return;
    sel.value = settings[key] || fallback;
    sel.addEventListener('change', () => {
      settings[key] = sel.value;
      onSetting?.(key, settings[key]);
      store(SET_KEY, JSON.stringify(settings));
    });
  };
  wireSelect('s-governor', 'governor', 'adaptive');
  wireSelect('s-season', 'season', 'summer');
  wireSelect('s-street-trees', 'streetTrees', 'shown');
  wireSelect('s-lot-lines', 'lotLines', 'hidden');
  wireToggle('s-compass', 'compass');
  wireToggle('s-overview-map', 'overviewMap');
  wireToggle('s-street-names', 'streetNames');
  wireToggle('s-look-tag', 'lookTag');

  // ---- Move: how you move, its speed, and how Go to takes you there (T-2651) ----
  //
  // DESIGN §07 M6. One picker — Walk, Run, Wagon, Horse, Fly — replaces the two the
  // Travel tab used to ask (how Go to takes you, and your own pace), and one slider
  // sets the speed of the mode picked: its range and its named speeds change with the
  // mode. Fly is the top bar's Walk/Fly key, so picking it here is the same free
  // flight and the picker shows it whichever way it was entered. Go to's choice is
  // its own small question underneath: Teleport, Ride there (along the streets at
  // the mode above) or Fly over. The numbers live in js/travel-settings.js PACES;
  // this only paints them. The pace chip in the top bar cycles the ground modes.
  const btnPace = $('btn-pace');
  const paceLabel = $('pace-label');
  const PACE_CYCLE = GROUND_MODES;
  // Single-colour stroke glyphs, the rail's icon family at chip size. A walker, a
  // runner, a cart, a horseshoe: the horseshoe rather than a horse because a horse's
  // head does not survive sixteen pixels of stroke and a shoe does.
  const svg = (body) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" `
    + `stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
  const PACE_GLYPH = {
    walk: svg('<circle cx="13.5" cy="4.5" r="1.9"/><path d="M12.6 8.2 11 13.4 8.2 20.5"/>'
      + '<path d="M11 13.4l3.2 2.6.3 4.5"/><path d="M12.6 8.2l3.4 2.6"/><path d="M12.6 8.2 9.6 10.6 7.4 9.6"/>'),
    run: svg('<circle cx="15" cy="4.5" r="1.9"/><path d="M13.6 8.4 11 14l-4 6"/>'
      + '<path d="M11 14l3.8 2.4-1.3 4.1"/><path d="M13.6 8.4l3 3.1 3.1-.7"/><path d="M13.6 8.4 9.6 9.6 7.6 12.4"/>'),
    wagon: svg('<path d="M3.5 9.5h11.5v6H4.5"/><path d="M15 12.5h3.2l2.3 3"/><circle cx="7.5" cy="18" r="2"/>'
      + '<circle cx="16.5" cy="18" r="2"/><path d="M9.5 18h5"/><path d="M5.5 9.5V6.5h7.5v3"/>'),
    horse: svg('<path d="M6.5 19.5v-8a5.5 5.5 0 0 1 11 0v8"/><path d="M4.5 19.5h4M15.5 19.5h4"/>'
      + '<path d="M8.5 9h.01M15.5 9h.01M7 13h.01M17 13h.01M7 16.5h.01M17 16.5h.01"/>'),
  };
  const groundPace = () => groundOf(settings.pace);
  const moveSlider = $('s-speed');
  const moveReadout = $('v-speed');
  const moveLabel = $('move-speed-label');
  const moveField = $('move-speed-field');
  function paintMove() {
    const view = moveView(settings, { flying });
    const { pace, mode, slider } = view;
    if (paceLabel) paceLabel.textContent = PACES[pace]?.label ?? pace;
    if (btnPace) {
      btnPace.dataset.pace = pace;
      const glyph = btnPace.querySelector('.pace-glyph');
      if (glyph) glyph.innerHTML = PACE_GLYPH[pace] ?? '';
      btnPace.title = `Your pace — ${PACES[pace]?.label ?? pace}. Tap for ${PACES[nextPace(pace)]?.label} (P)`;
    }
    doc.querySelectorAll('#s-move .seg-btn').forEach((b) => {
      b.setAttribute('aria-checked', String(b.dataset.mode === mode));
      b.classList.toggle('is-on', b.dataset.mode === mode);
    });
    // The one slider: the picked mode's range, value and named speed. Fly has no
    // slider — its speed grows with height — so the field is hidden and the note
    // says so.
    if (moveField) moveField.hidden = !slider.shown;
    if (moveSlider) {
      moveSlider.min = String(slider.min);
      moveSlider.max = String(slider.max);
      moveSlider.value = String(slider.value);
      moveSlider.setAttribute('aria-label', slider.label);
    }
    if (moveLabel) moveLabel.textContent = slider.label;
    if (moveReadout) moveReadout.textContent = slider.readout;
    const note = $('travel-note');
    if (note) note.textContent = view.note;
    doc.querySelectorAll('#s-arrive .seg-btn').forEach((b) => {
      b.setAttribute('aria-checked', String(b.dataset.arrive === view.arrive));
      b.classList.toggle('is-on', b.dataset.arrive === view.arrive);
    });
  }
  paintMoveHook = paintMove;
  function setTravelMode(mode) {
    if (!(mode in PACES)) return settings.travelMode;
    settings.travelMode = mode;
    store(SET_KEY, JSON.stringify(settings));
    paintMove();
    onSetting?.('travelMode', mode);
    return mode;
  }
  function setPace(pace, { announce = true } = {}) {
    if (!PACE_CYCLE.includes(pace)) return settings.pace;
    settings.pace = pace;
    store(SET_KEY, JSON.stringify(settings));
    // Ride there rides at the mode you move at, so it follows a new one.
    if (arriveOf(settings.travelMode) === 'ride' && settings.travelMode !== pace) setTravelMode(pace);
    paintMove();
    onSetting?.('pace', pace);
    if (announce) say(`${PACES[pace]?.label ?? pace} — ${PACES[pace]?.hint ?? ''}`.replace(/ — $/, ''));
    return pace;
  }
  /** The picker: a ground mode lands you if you were flying; Fly takes off. */
  function setMoveMode(mode) {
    if (mode === 'fly') { if (!flying) setFly(true); return 'fly'; }
    if (!PACE_CYCLE.includes(mode)) return flying ? 'fly' : groundPace();
    if (flying) setFly(false, { announce: false });
    if (settings.pace !== mode) setPace(mode); else paintMove();
    return mode;
  }
  // A Ride there stored before Run and the one picker (a ride by horse while the
  // pace was the wagon) rides at the pace now, as the choice says. Not stored: the
  // next choice the visitor makes stores it.
  if (arriveOf(settings.travelMode) === 'ride' && settings.travelMode !== groundPace()) {
    settings.travelMode = groundPace();
  }
  btnPace?.addEventListener('click', () => setPace(nextPace(groundPace())));
  doc.querySelectorAll('#s-move .seg-btn').forEach((b) => {
    b.addEventListener('click', () => setMoveMode(b.dataset.mode));
  });
  doc.querySelectorAll('#s-arrive .seg-btn').forEach((b) => {
    b.addEventListener('click', () => {
      settings.arriveChosen = true;
      setTravelMode(travelModeFor(b.dataset.arrive, groundPace()));
    });
  });
  moveSlider?.addEventListener('input', () => {
    const key = PACES[groundPace()].settingKey;
    settings[key] = Number(moveSlider.value);
    if (moveReadout) moveReadout.textContent = moveView(settings, { flying }).slider.readout;
    onSetting?.(key, settings[key]);
    store(SET_KEY, JSON.stringify(settings));
  });
  wireToggle('s-head-bob', 'headBob');
  wireToggle('s-snap-turn', 'snapTurn');
  paintMove();

  // The ride in progress: where to, how far is left, and the one way to stop it
  // that is not simply moving. Painted by travel.js through this, at most a few
  // times a second.
  const banner = $('travel-banner');
  function travelBanner(state) {
    if (!banner) return;
    if (!state) { banner.setAttribute('hidden', ''); return; }
    const verb = $('travel-verb'); const dest = $('travel-dest'); const dist = $('travel-dist');
    if (verb) verb.textContent = state.verb ?? str('hud.going');
    if (dest) dest.textContent = state.dest ?? '';
    if (dist) dist.textContent = Number.isFinite(state.dist_m) ? formatDistance(state.dist_m, settings.units) : '';
    banner.removeAttribute('hidden');
  }
  $('travel-stop')?.addEventListener('click', () => onTravelStop?.());

  // ---- Go to ---------------------------------------------------------------
  //
  // Everywhere you can stand and everyone who stood there, in one searchable
  // list. The list, its filters, its distances and its keyboard live in
  // js/goto.js; the HUD only hands it the section, the shared destinations
  // model, and the visitor's position, and tells it when to go.
  const goTo = createGoTo({
    root: doc.querySelector('[data-panel="goto"]'),
    destinations, visitor, isTouch, settings,
    units: () => settings.units,
    onGoTo: (target) => { setPanel(false); onGoTo?.(target); },
    onPersist: (key, value) => { settings[key] = value; store(SET_KEY, JSON.stringify(settings)); },
    hiddenGrades: () => [...hiddenLevels],
  });
  afterHide = () => goTo.paint();


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
    // C toggles BY GRADE (T-2647): the Confidence view's presets own what "on" means.
    else if (k === 'c') { e.preventDefault(); if (onConfidenceKey) onConfidenceKey(); else setConfidence(!confidenceOn); }
    // T-2622: N is the Navigator's now (navigator.js); What's new is under Settings and H.
    else if (k === 'g') { e.preventDefault(); openGoTo(); }
    else if (k === 'f') { e.preventDefault(); setFly(!flying); }
    else if (k === 'p') { e.preventDefault(); setPace(nextPace(groundPace())); }
    else if (e.key === 'Escape' && panelOpen()) setPanel(false);
  });

  return {
    say,
    announceStructureVersion,
    settings,
    setPanel,
    selectTab,
    setTitle,
    /** T-1740 — take sections out of the rail: a scene that does not list the
     *  layer a section reads offers no tab for it, so the arrow keys skip it and
     *  no route can select it. */
    omitTabs(ids) {
      for (const id of ids) {
        const tab = doc.querySelector(`.panel-tab[data-tab="${id}"]`);
        if (tab) tab.hidden = true;
        doc.querySelector(`.panel-body[data-panel="${id}"]`)?.setAttribute('hidden', '');
      }
      if (ids.includes(currentTab)) selectTab('goto');
    },
    /** T-2620: the Navigator's adapter for the sections it now holds. */
    setHost(h) { host = h; },
    /** Let one listener know which section is showing. */
    onTabChange(fn) { onTab = fn; },
    get tab() { return currentTab; },
    panelOpen,
    goTo,
    travelBanner,
    setPace,
    setTravelMode,
    setMoveMode,
    paintMove,
    /** The getting-there choice, for Go to, the Map and Jaunts (T-2652). */
    get gettingThere() { return { travelMode: settings.travelMode, pace: groundPace(), chosen: !!settings.arriveChosen }; },
    /** Move's mode: 'fly' while flying, else the ground pace (T-2651). */
    get moveMode() { return flying ? 'fly' : groundPace(); },
    showControlHelp,
    dismissControlHelp,
    get confidenceOn() { return confidenceOn; },
    setConfidence,
    get hiddenLevels() { return [...hiddenLevels]; },
    setHidden,
    /** How many structures sit at each grade (and the count cells painted, where shown). */
    levelCounts: () => paintCounts(),
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
