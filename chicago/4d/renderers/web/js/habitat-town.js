// SPDX-License-Identifier: GPL-3.0-or-later
// T-3585. The 1904 Prairie Avenue district's nature sounds: robins in the parkway
// elms, cicadas in their crowns on summer afternoons, field crickets in the
// parkway grass at dusk. Separately authored in the catalogue's `town_placements`;
// nothing here reinterprets the July 1835 fauna records or the 1812 woods.
//
// The habitat is the scene's own parkway elms (data/street_trees/1904.json, drawn
// by street-trees.js), not a second invented geometry: a bird phrase is anchored
// in the crown of one real tree, and an insect bed plays only while the listener
// is on the parkway, near the trees and the grass it stands in.
export const TOWN_HABITAT = Object.freeze({
  scene: '1904', habitat: 'parkway_elms',
  // Spatial choices are declared sound-design liberties (L-1904-nature-sounds-3585),
  // not measured distances: a robin is heard from one elm 24-110 m off, high in its
  // crown, and an insect bed needs the listener within 45 m of a parkway tree.
  birdNear: 24, birdFar: 110, crownHeight: 9, insectReach: 45,
});
const MODES = new Set(['habitat-insects', 'distant-bird']);
const PERIODS = new Set(['dawn', 'day', 'dusk', 'night']);
const SEASONS = new Set(['spring', 'summer', 'fall', 'winter']);
const finite = n => typeof n === 'number' && Number.isFinite(n);
const pair = (a, minimum) => Array.isArray(a) && a.length === 2
  && a.every(finite) && a[0] >= minimum && a[1] >= a[0];
const MONTH_DAY = /^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/;

/** Mar-May spring, Jun-Aug summer, Sep-Nov fall, Dec-Feb winter (jaunts.js seasonOfDate). */
export function townSeasonOfDate(date) {
  const month = Number(/^\d{4}-(\d{2})-\d{2}$/.exec(date ?? '')?.[1]);
  if (!(month >= 1 && month <= 12)) return null;
  return ['winter', 'winter', 'spring', 'spring', 'spring', 'summer', 'summer', 'summer', 'fall', 'fall', 'fall', 'winter'][month - 1];
}

/** A 1904 date whose own season is the visitor's season: the Season setting's
 * dates (07-01, 04-15, 10-15, 02-15) and a dated 1904 jaunt stop both qualify.
 * A date and season that disagree stay quiet rather than guessing which wins. */
export function townHabitatScene(env, year) {
  const date = env?.time?.date;
  return String(year) === TOWN_HABITAT.scene && SEASONS.has(env?.season)
    && typeof date === 'string' && date.startsWith('1904-') && townSeasonOfDate(date) === env.season
    && Array.isArray(env?.streetTrees) && env.streetTrees.length > 0;
}

/** Catalogue metadata is the authority; missing or duplicate metadata is quiet. */
export function townHabitatPlacement(asset, env, year) {
  if (!townHabitatScene(env, year) || asset?.runtime_enabled !== true
    || !asset.approved_eras?.includes(TOWN_HABITAT.scene) || !Array.isArray(asset.town_placements)) return null;
  const matches = asset.town_placements.filter(p => p?.scene_id === TOWN_HABITAT.scene && p.season === env.season);
  if (matches.length !== 1) return null;
  const p = matches[0];
  if (p.confidence !== 'reconstructed' || typeof p.id !== 'string' || !p.id
    || typeof p.species_id !== 'string' || !p.species_id || !MODES.has(p.mode)
    || p.habitat !== TOWN_HABITAT.habitat
    || !Array.isArray(p.active_periods) || !p.active_periods.length || !p.active_periods.every(t => PERIODS.has(t))
    || !finite(p.gain) || p.gain <= 0 || p.gain > 0.2 || !pair(p.gap_seconds, 20)
    || (p.initial_gap_seconds != null && !pair(p.initial_gap_seconds, 6))
    || (p.min_temperature_c != null && !finite(p.min_temperature_c))
    || (p.from_hour != null && (!finite(p.from_hour) || p.from_hour < 0 || p.from_hour >= 24))
    || (p.from_month_day != null && !MONTH_DAY.test(p.from_month_day))
    || !Array.isArray(p.source_ids) || !p.source_ids.length
    || typeof p.liberty !== 'string' || !p.liberty
    || typeof p.note !== 'string' || !p.note.trim()
    || typeof asset.url !== 'string' || !asset.delivery?.sha256) return null;
  // No insect chorus is inferred outside summer, as in the 1812 reconstruction.
  if (p.mode === 'habitat-insects' && p.season !== 'summer') return null;
  // A late-summer singer waits for its own date (a dated jaunt stop can reach it).
  if (p.from_month_day && env.time.date.slice(5) < p.from_month_day) return null;
  return p;
}

export function townHabitatEligible(p, env, period, hour) {
  return p.active_periods.includes(period) && (p.from_hour == null || hour >= p.from_hour)
    // No temperature is invented: only a supplied observation can suppress a call.
    && (env.temperatureC == null || p.min_temperature_c == null || env.temperatureC >= p.min_temperature_c);
}

/** The scene's parkway elms in scene coordinates (x = east, z = -north). */
export function parkwayElms(env) {
  const out = [];
  for (const t of env?.streetTrees ?? []) {
    if (!finite(t?.e) || !finite(t?.n) || t.kind === 'young') continue; // a sapling is no song post
    out.push({ id: t.id, x: t.e, z: -t.n });
  }
  return out;
}

/** Horizontal distance from the listener to the nearest parkway elm. */
export function nearestElm(env, elms = parkwayElms(env)) {
  const eye = env?.camera?.position;
  if (!eye) return Infinity;
  let best = Infinity;
  for (const t of elms) best = Math.min(best, Math.hypot(t.x - eye.x, t.z - eye.z));
  return best;
}
