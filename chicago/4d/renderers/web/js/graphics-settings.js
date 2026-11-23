/**
 * T-3736 — SETTINGS › GRAPHICS: Antialiasing, Frame pacing with Fast, and the line that
 * says what is being drawn.
 *
 * The owner, 2026-11-23, of the three changes proposed after the weak-computer work
 * (T-3728, T-3731): "Yes add them and organize integrate them cleanly so it it elegant and
 * simple for people to understand".
 *
 * - FRAME PACING has three choices. Adaptive is the T-2555 governor as it always was. Fast
 *   is T-3728's weak-computer rule (frame-governor.js `weakScale` while moving,
 *   `weakStillScale` standing, the sun's shadow every second frame; a capture, a photo and
 *   the welcome still drawn at full sharpness), which until now only the device profile
 *   could switch on. Fixed is every frame at the Sharpness chosen. A visitor who never
 *   chose ('') is on Auto: Fast on a weak computer that is not a phone or a headset,
 *   Adaptive everywhere else, which is exactly what each device drew before this.
 * - ANTIALIASING (multisampling) is a flag the drawing context is made with, so it is read
 *   once at boot and a change takes effect on the next load. Auto: off on a weak computer
 *   (turning it off there was worth about 3 fps standing on the owner's UHD 630 test PC),
 *   on everywhere else, phones included (T-0157).
 * - Neither choice can take a person, a horse, a carriage or a wagon out of the town: they
 *   change how many pixels are drawn and how often the shadow is, nothing else.
 *
 * Stored in `chicago4d.settings` as `pacing` ('' | 'adaptive' | 'fast' | 'fixed') and
 * `antialias` ('' | 'on' | 'off'). Before T-3736 pacing was stored as `governor`, where
 * 'adaptive' was both the default and what Use Auto wrote, so it carries over as Auto ('')
 * and 'fixed' as Fixed: every visitor keeps the frames they had.
 *
 * Pure: no DOM and no three.js, so tools/test_graphics_settings.mjs drives it in Node.
 */

import { t as str } from './strings/index.js';
import './strings/settings.js';

export const PACING = Object.freeze(['adaptive', 'fast', 'fixed']);
export const ANTIALIAS = Object.freeze(['on', 'off']);

/** A computer the T-3728 rule was written for: weak, not touch-first, not a headset. */
export function isWeakDesktop(device, { coarse = false, headset = false } = {}) {
  return device?.cls === 'weak' && !coarse && !headset;
}

/** The stored pacing choice, '' for Auto; reads the pre-T-3736 `governor` key once. */
export function storedPacing(settings) {
  const p = settings?.pacing;
  if (PACING.includes(p)) return p;
  return settings?.governor === 'fixed' ? 'fixed' : '';
}

/** The stored antialiasing choice, '' for Auto. */
export function storedAntialias(settings) {
  const a = settings?.antialias;
  return ANTIALIAS.includes(a) ? a : '';
}

/** What Auto picks on this device. */
export function autoPacing(weakDesktop) { return weakDesktop ? 'fast' : 'adaptive'; }
export function autoAntialias(weakDesktop) { return weakDesktop ? 'off' : 'on'; }

/** The pacing in force: the visitor's choice, else Auto's. */
export function resolvePacing(settings, weakDesktop) {
  return storedPacing(settings) || autoPacing(weakDesktop);
}

/** Whether to make the drawing context with multisampling. `?msaa=1` / `?msaa=0` win. */
export function resolveAntialias(settings, weakDesktop, query = null) {
  const q = query?.get?.('msaa');
  if (q === '1') return true;
  if (q === '0') return false;
  return (storedAntialias(settings) || autoAntialias(weakDesktop)) === 'on';
}

const DETAIL_WORD = Object.freeze({ full: 'Full', balanced: 'Balanced', light: 'Light' });
const SHARP_WORD = Object.freeze({ 1: 'Low', 1.5: 'Medium', 2: 'High' });
const pct = (x) => `${Math.round(x * 100)} %`;

/**
 * The "Drawing now" line: what the renderer is drawing this moment, in the visitor's words.
 * `state` is the governor's snapshot, `quality` the Sharpness chosen (1, 1.5, 2),
 * `multisample` whether this page was made with antialiasing, `pendingAntialias` the
 * choice stored for the next load ('on' / 'off'), said only when it differs.
 *
 *   "Drawing now: Balanced detail, 67 % of Low sharpness standing and 55 % moving, the
 *    shadow every other frame, antialiasing off. Photos are taken at full sharpness."
 */
export function describeDrawing({ detail, state, quality, multisample, pendingAntialias = null,
  weakScale = 0.55, weakStillScale = 0.67 } = {}) {
  const vars = {
    detail: DETAIL_WORD[detail] ?? DETAIL_WORD.full,
    sharp: SHARP_WORD[Number(quality)] ?? SHARP_WORD[1.5],
    aa: str(multisample ? 'settings.graphics.aa.on' : 'settings.graphics.aa.off'),
  };
  let line;
  if (!state || state.mode === 'fixed') line = str('settings.graphics.now.fixed', vars);
  else if (state.fast) line = str('settings.graphics.now.fast', { ...vars, still: pct(weakStillScale), moving: pct(weakScale) });
  else if (state.moving && (state.scale < 1 || state.pace === 2)) {
    line = str('settings.graphics.now.easing', { ...vars, cut: pct(state.scale),
      paced: state.pace === 2 ? str('settings.graphics.now.paced') : '' });
  } else line = str('settings.graphics.now.adaptive', vars);
  if ((pendingAntialias === 'on' || pendingAntialias === 'off') && (pendingAntialias === 'on') !== !!multisample) {
    line += ` ${str('settings.graphics.aa.next', { aa: str(`settings.graphics.aa.${pendingAntialias}`) })}`;
  }
  return line;
}

/** "Auto for this device: Balanced detail, Low sharpness, Fast pacing, antialiasing off." */
export function autoGraphicsLine({ detail, quality, weakDesktop }) {
  return str('settings.auto.line', {
    detail: DETAIL_WORD[detail] ?? detail,
    sharpness: SHARP_WORD[Number(quality)] ?? quality,
    pacing: str(`settings.graphics.pacing.${autoPacing(weakDesktop)}`),
    aa: str(`settings.graphics.aa.${autoAntialias(weakDesktop)}`),
  });
}
