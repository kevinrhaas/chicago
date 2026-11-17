// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3627: what main.js needs from the headset backend at boot, on its own: whether this is a
 * standalone headset (it boots as a phone) and the framebuffer scale it would draw at. The
 * session half (controls/xr.js) loads only where the browser offers a headset, so a phone or
 * a computer without one never fetches it. controls/xr.js re-exports all three.
 */

export const VR_SCALE = Object.freeze({ headset: 0.6, computer: 1, min: 0.3, max: 1 });

/**
 * A standalone headset's browser, by its user agent: the Quest browser says
 * "OculusBrowser" (and "Quest"), Pico's "PicoBrowser", Wolvic and the Vive Focus
 * browser say so too. Their screens report a fine pointer and a desktop width, so
 * without this they would boot as a computer.
 */
export function isStandaloneHeadset(ua) {
  return /OculusBrowser|\bQuest\b|PicoBrowser|\bPico\b|Wolvic|VR Browser|Vive ?Focus/i.test(String(ua || ''));
}

/** The framebuffer scale for this device, `?vr-scale=` first. */
export function vrScale({ headset = false, search = '' } = {}) {
  let asked = null;
  try { asked = Number(new URLSearchParams(search || '').get('vr-scale')); } catch { asked = null; }
  if (Number.isFinite(asked) && asked > 0) return Math.max(VR_SCALE.min, Math.min(VR_SCALE.max, asked));
  return headset ? VR_SCALE.headset : VR_SCALE.computer;
}
