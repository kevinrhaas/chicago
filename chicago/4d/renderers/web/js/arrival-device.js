/**
 * T-3539: THE DEVICE METER ON EVERY YEAR'S LOADING SCREEN.
 *
 * The Observatory's front door scores a device 0-100 (portal/device-meter.js), but the
 * owner's Inspiron read in the 70s there and still crashed 1904, and nothing on the
 * loading screen said what the town had chosen for it. This panel carries the same
 * score, from the SAME profile the town boots on (device-profile.js `scoreProfile`,
 * clamped to the band of the class it chose), and two short lines under it:
 *
 *   assess  why the score is what it is: the graphics, "shared memory" when the GPU
 *           borrows the system's RAM (T-3537), the memory and cores the browser reports
 *   setup   what this device will draw: the detail tier in words, the resolution
 *           (Sharpness), and what the tier eases off, named, never as a failure
 *
 * The words say what is drawn, not what is missing: "every street, building, person and
 * carriage", then what is lighter. They are read from the settings in force at boot
 * (a stored choice, the crash step-down, else the profile's), so they never promise
 * more than the town draws.
 */
import { scoreProfile, sharesSystemMemory, shortGpu } from './device-profile.js';
import { t } from './strings/index.js';
import './strings/arrival.js';

const SHARP_WORD = { 1: 'low', 1.5: 'medium', 2: 'high' };

/**
 * The panel's words and number. Pure.
 * @param {object} o
 * @param {object} o.profile    device-profile.js profileDevice() result
 * @param {string} o.detail     the scene-detail tier in force ('full'|'balanced'|'light')
 * @param {number} o.sharpness  the pixel-ratio cap in force (1, 1.5, 2)
 * @param {boolean} [o.lowMemory]   the memory diet is on (main.js `lowMem`)
 * @param {boolean} [o.steppedDown] crash-guard lowered this boot
 * @param {boolean} [o.chosen]      the visitor's own stored detail or sharpness
 * @param {string} [o.keptAfter]   T-3542: the detail a failed switch wanted, when this level was kept for it
 */
export function arrivalDeviceStatus({ profile, detail, sharpness, lowMemory = false, steppedDown = false, chosen = false,
  keptAfter = null } = {}) {
  const { score, grade } = scoreProfile(profile);
  const s = profile?.signals || {};
  const touch = !!profile?.touch;
  const software = /software rasteriser/.test(profile?.why || '');
  const gpu = software ? t('arrival.device.software') : clip(shortGpu(s.renderer).replace(/\s*\((?:R|TM)\)|[®™]/gi, ''), 28);
  const assess = [
    gpu === 'GPU not reported' ? null : gpu,
    !touch && sharesSystemMemory(s.renderer) ? t('arrival.device.shared') : null,
    s.memoryGB ? t('arrival.device.memory', { gb: s.memoryGB >= 8 ? '8+' : String(s.memoryGB) }) : null,
    s.cores ? t('arrival.device.cores', { n: s.cores }) : null,
  ].filter(Boolean);
  const tier = ['full', 'balanced', 'light'].includes(detail) ? detail : 'full';
  const sharp = SHARP_WORD[sharpness] ?? (sharpness >= 2 ? 'high' : sharpness > 1 ? 'medium' : 'low');
  const setup = [
    t(`arrival.device.detail.${tier}`),
    t(`arrival.device.draws.${tier}`),
    t('arrival.device.resolution', { level: t(`arrival.device.level.${sharp}`) }),
    tier === 'full' ? null : t(`arrival.device.eases.${tier}`),
    profile?.choice?.textures === 'light' ? t('arrival.device.textures') : null,
    lowMemory ? t('arrival.device.saver') : null,
    steppedDown ? t('arrival.device.stepped')
      // T-3542: a level kept after a switch failed is said as that, not as the visitor's choice.
      : keptAfter ? t('arrival.device.kept', { wanted: t(`arrival.device.detail.${keptAfter}`) || keptAfter })
        : chosen ? t('arrival.device.chosen') : null,
  ].filter(Boolean);
  return { score, grade, assess, setup };
}

function clip(text, n) {
  return text.length > n ? `${text.slice(0, n - 1)}…` : text;
}

/**
 * Paint the panel (index.html #arrival-device). The bar fills to the score once; under
 * reduced motion it is simply set. Returns the status painted, or null with no panel.
 */
export function paintArrivalDevice(root, options) {
  if (!root) return null;
  const status = arrivalDeviceStatus(options);
  const segs = [...root.querySelectorAll('.arrival-device-bar i')];
  const lit = Math.max(1, Math.min(segs.length, Math.round(status.score / (100 / Math.max(1, segs.length)))));
  segs.forEach((seg, i) => { seg.classList.toggle('on', i < lit); seg.classList.toggle('top', i === lit - 1); });
  const set = (key, text) => { const el = root.querySelector(`[data-dev="${key}"]`); if (el) el.textContent = text; };
  set('score', String(status.score).padStart(2, '0'));
  set('grade', status.grade.label);
  set('assess', status.assess.join(' · '));
  set('setup', status.setup.join(' · '));
  root.setAttribute('aria-label', `${t('arrival.device.head')}: ${status.score} of 100, ${status.grade.label}. `
    + `${status.assess.join(', ')}. ${status.setup.join(', ')}.`);
  Object.assign(root.dataset, { state: 'ready', grade: status.grade.id, detail: options?.detail || '' });
  return status;
}
