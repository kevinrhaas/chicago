/**
 * T-2614 (NAV-105, DESIGN §14 "Gesture gating without a gate"). With Tap to enter gone
 * (T-2613), nothing on the page is a gesture on purpose any more, yet the browser still
 * wants one before it lets audio play or the pointer be captured. So the gesture is the
 * visitor's first real tap after landing on one of three things:
 *
 *   - a Home choice (Take a Jaunt, Go to…, Free roam, or anything else on Home);
 *   - the scene itself (the canvas);
 *   - any Navigator control.
 *
 * That tap resumes the page's one AudioContext. The context is never made before it, so
 * neither Chrome ("The AudioContext was not allowed to start") nor iOS Safari has anything
 * to complain about, and on iOS (no pointer lock at all) audio is the whole story. The one
 * exception is js/sound.js's `mayStartEarly` (T-2659): where the browser says it will run
 * audio, or the page was opened by a jump tapped on this site, it makes the context on the
 * way in through `unlockAudio`, so the ticker can be heard; the next tap still resumes it.
 *
 * Pointer lock follows from the same rule, but only a click on the scene takes it: a
 * menu choice that grabbed the mouse would leave a desktop visitor with no cursor on the
 * card they just opened. Until the look is engaged a desktop visitor sees a CLICK TO
 * ENGAGE LOOK tag; it never shows on a touch device, and once the pointer has locked it
 * does not come back (a release says so in the HUD's own hint).
 *
 * Only a trusted event counts. A synthetic click carries no user activation, so trying
 * audio on one is exactly the call that logs the autoplay warning.
 */

/** Taps before the device has landed (the trip, Abort, Try again) are not Home's. */
export const UNARMED = Object.freeze(['observatory', 'locking', 'jumping', 'time-stream', 'recall']);

const CONTROL = ':is(button, a[href], input, select, [role="button"], [role="tab"], [role="option"])';
/** What a first tap may land on: Home's controls, the scene, the Navigator's controls. */
// T-2619: the docked pill's face (#nav-head) opens the device too, so it is a control here.
export const GESTURE_TARGETS = ['#view', `#welcome ${CONTROL}`, `#navigator ${CONTROL}`, '#nav-head'].join(', ');

/** The events a browser grants user activation on. pointerdown is not one for touch, and
 * iOS Safari only resumes audio from touchend or click, so those are the ones heard. */
export const GESTURE_EVENTS = Object.freeze(['pointerup', 'touchend', 'click', 'keydown']);

/** Should the CLICK TO ENGAGE LOOK tag show? Desktop only, in the town, before first lock. */
export function lookTagVisible({ inWorld = false, backend = 'none', locked = false, engaged = false } = {}) {
  return !!inWorld && backend === 'pointerlock' && !locked && !engaged;
}

export function createGestureGate({
  target = globalThis.window ?? null,
  journey = null,
  selector = GESTURE_TARGETS,
  AudioContext: Ctx = globalThis.window?.AudioContext ?? globalThis.window?.webkitAudioContext ?? null,
  tagEl = null,
  onGesture = null,
} = {}) {
  let audio = null;
  let gestured = false;
  let engaged = false;
  let look = { inWorld: false, backend: 'none', locked: false };

  const armed = () => !UNARMED.includes(journey?.state ?? 'landed');

  /** Make (first time) or resume the context. Called only from inside a gesture. */
  function unlockAudio() {
    if (!Ctx) return null;
    try {
      if (!audio) {
        audio = new Ctx();
        // Older iOS only counts a context as unlocked once something has played on it in
        // the gesture: one silent sample does that and is inaudible everywhere else.
        try {
          const source = audio.createBufferSource();
          source.buffer = audio.createBuffer(1, 1, 22050);
          source.connect(audio.destination);
          source.start(0);
        } catch { /* a context without buffers still resumes */ }
      }
      // iOS also suspends ("interrupted") a running context on a call or a lock screen;
      // the next qualifying tap resumes it, so this stays listening after the first.
      if (audio.state !== 'running' && audio.state !== 'closed') {
        const resumed = audio.resume?.();
        resumed?.catch?.(() => { /* refused: the next gesture tries again */ });
      }
    } catch { /* audio is optional */ }
    return audio;
  }

  function paintTag() {
    if (tagEl) tagEl.hidden = !lookTagVisible({ ...look, engaged });
  }

  function handle(event) {
    if (!event?.isTrusted || !armed()) return;
    // Enter or Space on a focused Home choice is a gesture; a stray key is not.
    if (event.type === 'keydown' && !['Enter', ' ', 'Spacebar'].includes(event.key)) return;
    if (!event.target?.closest?.(selector)) return;
    unlockAudio();
    if (!gestured) { gestured = true; onGesture?.(event); }
  }

  for (const type of GESTURE_EVENTS) target?.addEventListener?.(type, handle, { capture: true, passive: true });

  return {
    /** The page's AudioContext, or null until the first gesture after landing. */
    get audio() { return audio; },
    get gestured() { return gestured; },
    get engaged() { return engaged; },
    get armed() { return armed(); },
    get state() { return { gestured, engaged, audio: audio?.state ?? 'none', tag: tagEl ? !tagEl.hidden : false }; },
    /** The town, the control backend and the lock, as main.js knows them. */
    setLook(next = {}) {
      look = { ...look, ...next };
      if (look.locked) engaged = true;
      paintTag();
    },
    unlockAudio,
    handle,
    dispose() { for (const type of GESTURE_EVENTS) target?.removeEventListener?.(type, handle, { capture: true }); },
  };
}
