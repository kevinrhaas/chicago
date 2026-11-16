/**
 * The owner, 2026-11-16: "In 1904 you end the Glessner house jaunt with narration and a nice
 * closing but that is not on the screen ... All jaunts should be like that where if there is
 * narration at the end you can run it at the end while you can read it and the jaunt moves
 * ending to a nice place view while the narration goes and that should happen at the
 * beginning of the jaunt if possible while the opening background is read you are flying or
 * walking to the start of the jaunt".
 *
 * So a jaunt opens and closes on its own words. The flight to the first stop lasts as long as
 * the voice reading its opening (T-3432's glide is otherwise at most 8 s), and finishing the
 * last stop is not the end: a closing scene shows the ending, reads it aloud where it is
 * voiced, and flies the eye up and back over the place the jaunt began, and only then does
 * the Outing complete card come. Pure, so Node tests read the same numbers the app flies.
 */
import { bearingToYaw } from './angles.js';

/** Seconds a voiced opening may hold the flight (the longest voiced one is about 74 s). */
export const OPENING_MAX_S = 90;
/** The closing flight: at most this long, and about half the ending's voice, so the eye has
 *  settled on the view before the last words. Unvoiced, it is the plain glide's length. */
export const CLOSING_FLIGHT = Object.freeze({ min_s: 6, max_s: 20, share: 0.5 });
/** Where the closing view stands: this far behind the stand the jaunt began at, this high
 *  above the ground, looking steeply down onto it: over 1904 Prairie Avenue's parkway elms,
 *  which hide a house from any lower view (measured in the app, 2026-11-16: from 30 m up and
 *  45 m back the Glessner front was all leaves). */
export const CLOSING_VIEW = Object.freeze({ back_m: 32, up_m: 44, subject_m: 15, subject_up_m: 6 });
/** After the ending's voice finishes, the scene holds this long before the Outing complete card. */
export const CLOSING_HOLD_S = 2.5;
/** An unvoiced (or silenced) ending is on screen as long as a visitor takes to read it. */
export const READ_WPS = 3;
export const READ_MIN_S = 6;

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const words = text => String(text ?? '').split(/\s+/).filter(Boolean).length;

/** Seconds to read `text` on screen, at READ_WPS, plus a moment to look up. */
export function readingSeconds(text) {
  return Math.max(READ_MIN_S, words(text) / READ_WPS + 1.5);
}

/** A clip's length in seconds from the narration index: its bytes at its constant bitrate
 *  (`mp3_44100_64` is 64 kbit/s), else about 15 characters a second, else null. */
export function clipSeconds(clip) {
  if (!clip) return null;
  const kbps = Number(/^mp3_\d+_(\d+)$/.exec(clip.output_format ?? '')?.[1]);
  if (kbps > 0 && clip.bytes > 0) return clip.bytes / (kbps * 125);
  return clip.chars > 0 ? clip.chars / 15 : null;
}

/** How long the flight to the first stop takes while its opening is read: the voice's length
 *  less a second (so the eye lands as the narrator finishes), within OPENING_MAX_S; null for a
 *  jaunt with no voice to wait for, which keeps the plain glide. */
export function openingFlightSeconds(voiced) {
  return Number.isFinite(voiced) && voiced > 10 ? clamp(voiced - 1, 10, OPENING_MAX_S) : null;
}

/** The closing flight's seconds for an ending whose voice lasts `voiced` (null: not heard). */
export function closingFlightSeconds(voiced) {
  return Number.isFinite(voiced) && voiced > 0
    ? clamp(voiced * CLOSING_FLIGHT.share, CLOSING_FLIGHT.min_s, CLOSING_FLIGHT.max_s) : null;
}

/**
 * Where a long opening flight looks down from on its way in: high and well back behind the
 * first stop's stand, facing it, the town spread out below. `to` is the stand's eye pose
 * { e, n, altitude, yaw, pitch } (walker yaw, radians); the farther the voice, the higher.
 */
export function openingOverlook(to, seconds) {
  const back = clamp(seconds * 4, 120, 320), up = back * 0.45;
  const e = to.e + Math.sin(to.yaw) * back, n = to.n - Math.cos(to.yaw) * back;
  return { e, n, altitude: up, yaw: to.yaw, pitch: -Math.atan2(up, back + 20) };
}

/**
 * The jaunt's last view: up and back over the stand it began at, looking down onto what that
 * stand framed. `stand` is { e, n } with `bearing_deg` (where it faces) or `aim` ({ e, n },
 * what it frames); the result is a glide pose { e, n, altitude, yaw, pitch }.
 */
export function closingView(stand) {
  const aim = stand?.aim && Number.isFinite(stand.aim.e) && Number.isFinite(stand.aim.n) ? stand.aim : null;
  let bearing = Number.isFinite(stand?.bearing_deg) ? stand.bearing_deg : 0;
  if (aim && Math.hypot(aim.e - stand.e, aim.n - stand.n) > 0.5) bearing = Math.atan2(aim.e - stand.e, aim.n - stand.n) * 180 / Math.PI;
  const yaw = bearingToYaw(bearing), b = bearing * Math.PI / 180;
  const subject = aim ? Math.hypot(aim.e - stand.e, aim.n - stand.n) : CLOSING_VIEW.subject_m;
  const e = stand.e - Math.sin(b) * CLOSING_VIEW.back_m, n = stand.n - Math.cos(b) * CLOSING_VIEW.back_m;
  const pitch = -Math.atan2(CLOSING_VIEW.up_m - CLOSING_VIEW.subject_up_m, CLOSING_VIEW.back_m + subject);
  return { e, n, altitude: CLOSING_VIEW.up_m, yaw, pitch };
}

/**
 * The closing scene's clock. Each `update(state)` (every render) and `tick()` (a timer) asks:
 * is the scene done? It is once the flight has landed and either the ending's voice has
 * finished (and CLOSING_HOLD_S has passed) or, where nothing is heard, the ending has been
 * up for its reading time. A voice the visitor stopped leaves the reading time to run.
 * `voice` = { playing() -> bool, ended() -> bool } for this ending; `flying()` says the
 * closing flight is still in the air; `finish()` ends the scene (the runtime's FINISH).
 */
export function createClosingClock({ now = () => Date.now() / 1000, voice, flying = () => false, finish }) {
  let key = null, began = 0, read = READ_MIN_S, heard = false, doneAt = null, closed = false;
  function update(state) {
    if (state?.phase !== 'closing' || !state.outcome) { key = null; return; }
    const k = `${state.session}:${state.leg}`;
    if (k === key) return;
    key = k; began = now(); read = readingSeconds(state.outcome.text); heard = false; doneAt = null; closed = false;
  }
  function tick() {
    if (!key || closed) return false;
    const t = now(), playing = voice.playing();
    if (playing) { heard = true; doneAt = null; return false; }
    if (heard && doneAt === null) doneAt = voice.ended() ? t + CLOSING_HOLD_S : Math.max(t + CLOSING_HOLD_S, began + read);
    const due = doneAt ?? began + read;
    if (t < due || flying()) return false;
    closed = true; finish();
    return true;
  }
  return { update, tick, get active() { return !!key && !closed; } };
}
