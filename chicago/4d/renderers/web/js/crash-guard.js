/**
 * CRASH-AWARE BOOT (T-2547, owner-reported 2026-10-16: phones dying for memory).
 *
 * When iOS kills a tab for memory, the next load used to boot into exactly the
 * configuration that died and die the same way; and a lost WebGL context used to
 * reload the page on every `webglcontextrestored`, which on a device under
 * pressure can loop. This module is the boot's memory of how the last one ended.
 *
 * THE MARKER. `boot()` writes `{year, detail, quality, t, beat}` to sessionStorage
 * and mirrors it to localStorage (iOS can lose session storage when it discards a
 * tab). `live()` arms a 60 s timer once the walk is ready, and the marker is
 * cleared when it fires or on a clean `pagehide`. A marker still there at the
 * next boot means the last session died in the load or soon after. The local
 * mirror holds one entry per tab, and another tab's entry is believed only when
 * its heartbeat (refreshed every 2 s while the page lives) is more than
 * BEAT_STALE_MS old, so a second open tab is not mistaken for a dead one.
 *
 * THE STEP-DOWN. A found marker lowers the scene detail one tier (never below
 * `light`) and Sharpness to Low, records that in localStorage as the step-down,
 * and shows a dismissible card saying so. The step-down holds at every boot
 * until the visitor picks Scene detail or Sharpness in Settings: each choice
 * made after it wins, and takes back its own half of the record.
 *
 * THE CONTEXT. A lost context is `preventDefault`ed (so it may be restored)
 * and said on the card. The first loss in a session reloads once on restore,
 * when the page has let go of the arrays a restored context would need. Any
 * later loss lowers the tier for the next boot and does NOT reload by itself:
 * the card offers a Reload the visitor taps. So a session reloads itself at
 * most once, and a device that keeps losing its context cannot loop.
 *
 * Every outcome is in `state`, which main.js publishes as
 * `window.__chicago4d.crashGuard` for the smoke.
 */

export const MARKER_KEY = 'c4d.crash.marker';
export const STEPDOWN_KEY = 'c4d.crash.stepdown';
export const LOSSES_KEY = 'c4d.crash.contextLosses';
export const RELOADS_KEY = 'c4d.crash.reloads';
export const TAB_KEY = 'c4d.crash.tab';
export const LIVE_MS = 60_000;
export const BEAT_MS = 2_000;
export const BEAT_STALE_MS = 15_000;
/** Sharpness Low: the pixel-ratio cap a step-down sets (sharpness.js's first stop). */
export const LOW_QUALITY = 1;

export const NOTICE = {
  memory: 'Detail lowered: this device ran out of memory last time. Settings can raise it again.',
  contextReset: 'The display was reset: this device ran short of graphics memory. Reloading once…',
  contextLowered: (tier) => `Detail lowered to ${tier}: this device ran short of graphics memory again. Reload to continue; Settings can raise it again.`,
  contextFloor: 'This device ran short of graphics memory again. Reload to continue.',
};

const DETAIL_NAMES = { full: 'Full', balanced: 'Balanced', light: 'Light' };

/**
 * One step down from `{detail, quality}` on `order` (most detail first): the next
 * tier, never past the last, and Sharpness Low. `lowered` is false at the floor.
 */
export function stepDown({ detail, quality }, order) {
  const i = order.indexOf(detail);
  const to = {
    detail: i < 0 ? order.at(-1) : order[Math.min(i + 1, order.length - 1)],
    quality: Math.min(Number(quality) || LOW_QUALITY, LOW_QUALITY),
  };
  return { ...to, lowered: to.detail !== detail || to.quality !== Number(quality) };
}

function reader(store) {
  return {
    get(key) {
      try { const raw = store?.getItem(key); return raw ? JSON.parse(raw) : null; } catch { return null; }
    },
    set(key, value) { try { store?.setItem(key, JSON.stringify(value)); } catch { /* storage refused */ } },
    drop(key) { try { store?.removeItem(key); } catch { /* storage refused */ } },
  };
}

function defaultStore(name) {
  try { return window[name]; } catch { return null; }
}

export function createCrashGuard({
  year,
  order,
  session = defaultStore('sessionStorage'),
  local = defaultStore('localStorage'),
  now = () => Date.now(),
  reload = () => window.location.reload(),
  doc = typeof document === 'undefined' ? null : document,
  win = typeof window === 'undefined' ? null : window,
} = {}) {
  const ss = reader(session);
  const ls = reader(local);
  const state = {
    found: null,          // the marker a dead session left, or null
    lowered: null,        // {why, from, to} when this boot or a lost context stepped down
    stepdown: ls.get(STEPDOWN_KEY),
    boot: null,           // {detail, quality} this boot runs at
    contextLosses: 0,     // this page
    sessionLosses: Number(ss.get(LOSSES_KEY)) || 0,
    reloads: Number(ss.get(RELOADS_KEY)) || 0,
    notice: null,         // the card's text while it shows
    cleared: false,       // the marker was taken down (60 s live, or pagehide)
    watching: false,      // the canvas's context events are ours
  };
  let beatTimer = null;
  let liveTimer = null;
  let card = null;

  // The local mirror is one entry per tab, so a second tab's clean exit cannot
  // take down the first one's marker. The tab's id lives in its session storage.
  const tabId = ss.get(TAB_KEY) || `${now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  ss.set(TAB_KEY, tabId);
  const mirror = () => { const m = ls.get(MARKER_KEY); return m && typeof m === 'object' ? m : {}; };
  function editMirror(fn) {
    const m = mirror();
    fn(m);
    if (Object.keys(m).length) ls.set(MARKER_KEY, m); else ls.drop(MARKER_KEY);
  }
  function writeMarker() {
    const m = { year, detail: state.boot.detail, quality: state.boot.quality, t: now(), beat: now() };
    ss.set(MARKER_KEY, m);
    editMirror((all) => { all[tabId] = m; });
  }
  function beat() {
    editMirror((all) => { if (all[tabId]) all[tabId].beat = now(); });
  }
  function startBeat() {
    if (beatTimer) return;
    beatTimer = setInterval(beat, BEAT_MS);
    beatTimer.unref?.();   // node's tests: a heartbeat must not hold the process open
  }
  function clearMarker() {
    ss.drop(MARKER_KEY);
    editMirror((all) => { delete all[tabId]; });
    clearInterval(beatTimer);
    beatTimer = null;
  }
  function writeStepdown(why, from, to) {
    state.stepdown = { detail: to.detail, quality: to.quality, why, from, year, t: now() };
    ls.set(STEPDOWN_KEY, state.stepdown);
    state.lowered = { why, from, to: { detail: to.detail, quality: to.quality } };
  }

  /** The card. Built on first use; one at a time; the visitor can always shut it. */
  function show(text, { reloadButton = false, copyText = null } = {}) {
    state.notice = text;
    if (!doc?.body) return;
    if (!card) {
      card = doc.createElement('div');
      card.className = 'crash-notice';
      card.id = 'crash-notice';
      card.setAttribute('role', 'status');
      card.innerHTML = '<svg class="crash-notice-icon" viewBox="0 0 24 24" aria-hidden="true">'
        + '<path d="M12 3 2.5 20h19L12 3Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'
        + '<path d="M12 10v4.5M12 17.2v.3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
        + '<p class="crash-notice-text"></p>'
        + '<button type="button" class="crash-notice-reload" hidden>Reload</button>'
        + '<button type="button" class="crash-notice-copy" hidden>Copy details</button>'
        + '<button type="button" class="crash-notice-close" aria-label="Dismiss">'
        + '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" '
        + 'stroke-width="2" stroke-linecap="round"/></svg></button>';
      card.querySelector('.crash-notice-close').addEventListener('click', dismiss);
      card.querySelector('.crash-notice-reload').addEventListener('click', () => reload());
      card.querySelector('.crash-notice-copy').addEventListener('click', (e) => {
        const button = e.currentTarget;
        const text = button.dataset.copy ?? '';
        const done = (ok) => { button.textContent = ok ? 'Copied' : 'Copy failed'; };
        try { win?.navigator?.clipboard?.writeText(text).then(() => done(true), () => done(false)); } catch { done(false); }
      });
      doc.body.append(card);
    }
    card.querySelector('.crash-notice-text').textContent = text;
    card.querySelector('.crash-notice-reload').hidden = !reloadButton;
    const copy = card.querySelector('.crash-notice-copy');
    copy.hidden = !copyText;
    copy.textContent = 'Copy details';
    if (copyText) copy.dataset.copy = copyText; else delete copy.dataset.copy;
    card.hidden = false;
  }
  function dismiss() {
    state.notice = null;
    if (card) card.hidden = true;
  }

  /**
   * Resolve the configuration this boot runs at, from what the visitor stored
   * (`detail`, `quality`: '' when never chosen) and the device's guess, then
   * write this boot's marker. Returns `{detail, quality, lowered}` where
   * `lowered` names which halves the step-down overrides.
   */
  function boot({ detail, quality }) {
    let run = { detail, quality: Number(quality) };
    const sd = state.stepdown;
    if (sd?.detail && order.includes(sd.detail)) run.detail = sd.detail;
    if (sd?.quality) run.quality = Number(sd.quality);

    // This tab's own marker, or any tab's whose heartbeat stopped (iOS lost this
    // tab's session storage, or discarded another): read once, then taken down.
    let dead = ss.get(MARKER_KEY);
    editMirror((all) => {
      for (const [id, m] of Object.entries(all)) {
        if (id === tabId || now() - (Number(m?.beat) || 0) > BEAT_STALE_MS) { dead ||= m; delete all[id]; }
      }
    });
    if (dead) {
      state.found = dead;
      // One step below what this boot would have run at, which is what died
      // unless the visitor has changed Settings since.
      const to = stepDown(run, order);
      if (to.lowered) {
        writeStepdown('memory', { ...run }, to);
        run = { detail: to.detail, quality: to.quality };
        show(NOTICE.memory);
      }
    }
    state.boot = run;
    writeMarker();
    startBeat();
    win?.addEventListener('pagehide', onPagehide);
    win?.addEventListener('pageshow', onPageshow);
    return {
      ...run,
      lowered: { detail: !!state.stepdown?.detail, quality: !!state.stepdown?.quality },
    };
  }

  function onPagehide() {
    clearMarker();
  }
  function onPageshow(e) {
    // Back from the back-forward cache inside the first minute: watch again.
    if (e.persisted && !state.cleared && state.boot) { writeMarker(); startBeat(); }
  }

  /** The walk is up: a session that lives `LIVE_MS` past this did not die loading. */
  function live() {
    if (liveTimer || state.cleared) return;
    liveTimer = setTimeout(() => { state.cleared = true; clearMarker(); }, LIVE_MS);
    liveTimer.unref?.();
  }

  /** The visitor chose `key` ('detail' | 'quality') in Settings: their choice wins. */
  function chosen(key) {
    const sd = state.stepdown;
    if (!sd || !(key in sd)) return;
    delete sd[key];
    if (!sd.detail && !sd.quality) { state.stepdown = null; ls.drop(STEPDOWN_KEY); } else ls.set(STEPDOWN_KEY, sd);
  }

  /**
   * Own the canvas's context events. `needsReload()` says whether the page has
   * let go of what a restored context would need (upload-release.js), which is
   * the only case a reload is for; otherwise three re-uploads on its own.
   */
  function watchContext(canvas, { needsReload = () => true } = {}) {
    if (!canvas) return;
    state.watching = true;
    let reloadOnRestore = false;
    canvas.addEventListener('webglcontextlost', (e) => {
      e.preventDefault();
      state.contextLosses += 1;
      state.sessionLosses += 1;
      ss.set(LOSSES_KEY, state.sessionLosses);
      if (state.sessionLosses === 1 && state.reloads === 0) {
        reloadOnRestore = true;
        show(NOTICE.contextReset);
        return;
      }
      // Lost again: lower the next boot, and leave the reload to the visitor.
      reloadOnRestore = false;
      const from = state.lowered?.to ?? state.boot;
      const to = stepDown(from, order);
      if (to.lowered) {
        writeStepdown('context', { detail: from.detail, quality: from.quality }, to);
        show(NOTICE.contextLowered(DETAIL_NAMES[to.detail] ?? to.detail), { reloadButton: true });
      } else {
        show(NOTICE.contextFloor, { reloadButton: true });
      }
    });
    canvas.addEventListener('webglcontextrestored', () => {
      if (!reloadOnRestore) return;
      reloadOnRestore = false;
      if (!needsReload()) { dismiss(); return; }
      state.reloads += 1;
      ss.set(RELOADS_KEY, state.reloads);
      reload();
    });
  }

  return { state, boot, live, chosen, watchContext, dismiss, show };
}
