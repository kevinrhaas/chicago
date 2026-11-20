// SPDX-License-Identifier: GPL-3.0-or-later
// Separately authored 1812 seasonal acoustic reconstructions in the audio catalog.
// These do not reinterpret July 1835 fauna or move any historical event/date.
export const NATURE_1812_DATES = Object.freeze({
  spring: '1812-04-15', summer: '1812-08-14', fall: '1812-10-15', winter: '1812-02-15',
});
const ZONES = new Set(['z01_wet_prairie', 'z02_mesic_prairie', 'z03_sedge_meadow',
  'z04_marsh', 'z05_riverbank_timber', 'z06_dense_forest', 'z08_lakeshore', 'z09_sand_prairie']);
const MODES = new Set(['habitat-insects', 'distant-bird', 'distant-fauna']);
const PERIODS = new Set(['dawn', 'day', 'dusk', 'night']);
const finite = n => typeof n === 'number' && Number.isFinite(n);
const pair = (a, minimum) => Array.isArray(a) && a.length === 2
  && a.every(finite) && a[0] >= minimum && a[1] >= a[0];
const zoneList = a => Array.isArray(a) && a.length > 0 && a.every(z => ZONES.has(z));

/** The visitor's season owns the ecological view. A retained scene date is
 * allowed because date and season can be updated independently. A jaunt's other
 * date/year is not silently given this seasonal reconstruction. */
export function seasonalHabitatScene(env, year) {
  const date = Object.hasOwn(NATURE_1812_DATES, env?.season) ? NATURE_1812_DATES[env.season] : null;
  return String(year) === '1812' && !!date
    && [date, NATURE_1812_DATES.summer].includes(env?.time?.date)
    && env?.terrain?.epochId === 'e1830_natural';
}

/** Catalog metadata is the authority; no species defaults or era transfer.
 * One placement per recording/season keeps a single delivery from multiplying
 * voices or masquerading as several animals. Missing/duplicate metadata is quiet. */
export function seasonalHabitatPlacement(asset, env, year) {
  if (!seasonalHabitatScene(env, year) || asset?.runtime_enabled !== true
    || !asset.approved_eras?.includes('1812') || !Array.isArray(asset.seasonal_placements)) return null;
  const matches = asset.seasonal_placements.filter(p => p?.scene_id === '1812' && p.season === env.season);
  if (matches.length !== 1) return null;
  const p = matches[0];
  if (p.confidence !== 'reconstructed' || typeof p.id !== 'string' || !p.id
    || typeof p.species_id !== 'string' || !p.species_id || !MODES.has(p.mode)
    || !zoneList(p.flora_zone_ids) || !Array.isArray(p.active_periods) || !p.active_periods.length
    || !p.active_periods.every(t => PERIODS.has(t))
    || !finite(p.gain) || p.gain <= 0 || p.gain > 0.2 || !pair(p.gap_seconds, 20)
    || (p.initial_gap_seconds != null && !pair(p.initial_gap_seconds, 6))
    || (p.min_temperature_c != null && !finite(p.min_temperature_c))
    || (p.from_hour != null && (!finite(p.from_hour) || p.from_hour < 0 || p.from_hour >= 24))
    || (p.listener_flora_zone_ids != null && !zoneList(p.listener_flora_zone_ids))
    || typeof p.note !== 'string' || !p.note.trim()
    || typeof asset.url !== 'string' || !asset.delivery?.sha256) return null;
  // Cold-season silence is part of this reconstruction, even if a warm day is
  // supplied. No katydid/cricket/cicada chorus is inferred for mid-October/February.
  if (p.mode === 'habitat-insects' && p.season !== 'summer') return null;
  // An unseen mammal is a rare distant night source, never a nearby looping bed.
  if (p.mode === 'distant-fauna' && (p.species_id !== 'canis_latrans'
    || p.active_periods.length !== 1 || p.active_periods[0] !== 'night'
    || p.gap_seconds[0] < 300 || !pair(p.initial_gap_seconds, 120)
    || !zoneList(p.listener_flora_zone_ids) || p.require_dry_ground !== true)) return null;
  return p;
}

export function seasonalHabitatEligible(p, env, floraZone, period, hour) {
  return p.flora_zone_ids.includes(floraZone) && p.active_periods.includes(period)
    && (p.from_hour == null || hour >= p.from_hour)
    // No temperature is invented: supplied observations can suppress a summer
    // insect, otherwise season supplies only an explicitly reconstructed proxy.
    && (env.temperatureC == null || p.min_temperature_c == null || env.temperatureC >= p.min_temperature_c);
}

// Spatial choices are declared sound-design liberties, not measured distances.
// Existing 1835 bird constants/behavior remain in habitat-audio.js unchanged.
export function seasonalSourceProfile(p) {
  return p.mode === 'distant-fauna'
    ? { rings: [120, 180, 240], near: 90, far: 300, height: 0.65 }
    : { rings: [44, 64, 84], near: 36, far: 96, height: 1.5 };
}
