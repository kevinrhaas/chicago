/**
 * units.js — visitor-facing measurement formatting.
 *
 * Scene data, terrain sampling and movement stay in SI units.  This module is
 * the one presentation boundary: a visitor can choose Imperial or Metric in
 * Settings without changing any simulation value or historical record.
 */

const M_TO_FT = 3.280839895;
const MPS_TO_MPH = 2.236936292;
const MPS_TO_KPH = 3.6;
const METRES_PER_MILE = 1609.344;

export function normalUnitSystem(value) {
  return value === 'metric' ? 'metric' : 'imperial';
}

/** Short distances stay in feet/metres; map-scale distances use miles/km. */
export function formatDistance(metres, units = 'imperial') {
  const value = Number(metres) || 0;
  if (normalUnitSystem(units) === 'metric') {
    if (Math.abs(value) >= 1000) return `${(value / 1000).toFixed(1)} km`;
    return `${Math.round(value)} m`;
  }
  if (Math.abs(value) >= METRES_PER_MILE) {
    return `${(value / METRES_PER_MILE).toFixed(1)} mi`;
  }
  return `${Math.round(value * M_TO_FT)} ft`;
}

/** Height remains in feet/metres even at free-fly altitudes. */
export function formatHeight(metres, units = 'imperial') {
  const value = Number(metres) || 0;
  return normalUnitSystem(units) === 'metric'
    ? `${Math.round(value)} m`
    : `${Math.round(value * M_TO_FT)} ft`;
}

/**
 * A height at PERSON scale — feet and inches, or metres to the centimetre.
 *
 * Separate from `formatHeight` because they answer different questions at
 * different magnitudes. Altitude wants whole feet: "1378 ft up" is exactly as
 * precise as anyone needs 400 m in the air. A stature does not survive that
 * rounding — 1.68 m becomes "6 ft", which is both wrong by half a foot and
 * unchanged across a third of the eye-height slider's travel, so the control
 * reads as broken. Nobody has ever given their own height in whole feet.
 */
export function formatStature(metres, units = 'imperial') {
  const value = Number(metres) || 0;
  if (normalUnitSystem(units) === 'metric') return `${value.toFixed(2)} m`;
  const totalInches = Math.round(value * M_TO_FT * 12);
  return `${Math.floor(totalInches / 12)} ft ${totalInches % 12} in`;
}

export function formatSpeed(metresPerSecond, units = 'imperial') {
  const value = Number(metresPerSecond) || 0;
  return normalUnitSystem(units) === 'metric'
    ? `${(value * MPS_TO_KPH).toFixed(1)} km/h`
    : `${(value * MPS_TO_MPH).toFixed(1)} mph`;
}
