/**
 * Getting there (T-2652, DESIGN §07 "Move"): one choice — Teleport, Ride there or Fly
 * over — that Go to, the Map and Jaunts all use.
 *
 * The choice is stored as the travel mode the controller already reads ('instantly', a
 * ground pace for Ride there, or 'fly'; js/move-modes.js § arriveOf), so Go to and the
 * Map, which both hand a place to travel.go(), follow it with nothing more. A Jaunt has
 * its own list of the ways it may be travelled (`allowed_modes`) and a recommended one
 * (`default_mode`); this turns the choice into the Jaunt's mode between stops. Pure.
 */
import { arriveOf, groundPace } from './move-modes.js';

/** The three choices, in the order Move offers them. */
export const STYLES = [
  { id: 'instantly', label: 'Teleport' },
  { id: 'ride', label: 'Ride there' },
  { id: 'fly', label: 'Fly over' },
];
export const styleOf = arriveOf;

/** "Teleport", "Ride there · Horse", "Fly over": the choice in words. */
export function styleWords({ travelMode, pace } = {}, labels = {}) {
  const style = styleOf(travelMode);
  const name = STYLES.find((s) => s.id === style).label;
  if (style !== 'ride') return name;
  const mode = travelMode in labels ? travelMode : groundPace(pace);
  return `${name} · ${labels[mode] ?? mode}`;
}

/**
 * The mode a Jaunt travels between its stops under the visitor's choice, or null for
 * the Jaunt's own recommendation. Null until the visitor has made the choice themselves
 * (`chosen`): a fresh visitor's Teleport is the default, not a wish, and a guided outing
 * teleported stop to stop by default would lose the ride it was written around. Once
 * chosen, Teleport and Fly over are the Jaunt's 'instantly' and 'fly', and Ride there
 * is the pace — running counts as on foot, since no Jaunt lists running — each only
 * where the Jaunt allows it.
 */
export function jauntModeFor({ travelMode, pace, chosen = false } = {}, jaunt = {}) {
  if (!chosen) return null;
  const allowed = Array.isArray(jaunt?.allowed_modes) ? jaunt.allowed_modes : [];
  const style = styleOf(travelMode);
  let want = style;
  if (style === 'ride') want = travelMode && travelMode !== 'instantly' && travelMode !== 'fly' ? travelMode : groundPace(pace);
  if (want === 'run') want = 'walk';
  return allowed.includes(want) ? want : null;
}
