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

/** The mode the visitor's choice asks a Jaunt for: Teleport and Fly over are the Jaunt's
 * 'instantly' and 'fly', and Ride there is the pace (running counts as on foot, since no
 * Jaunt lists running). */
function wantedMode({ travelMode, pace } = {}) {
  const style = styleOf(travelMode);
  let want = style;
  if (style === 'ride') want = travelMode && travelMode !== 'instantly' && travelMode !== 'fly' ? travelMode : groundPace(pace);
  return want === 'run' ? 'walk' : want;
}

/**
 * How a Jaunt travels between its stops (T-2727, replacing T-2652's hidden "until you
 * choose" rule with a switch the visitor can see, Move › Jaunts use my choice).
 * Off (`follow` false, the default): every Jaunt keeps the way it recommends — `mode` is
 * null, and the Jaunt's own `default_mode` stands. On: the Jaunt takes the visitor's
 * choice where it allows it; where it does not, `mode` is null and `kept` is true, so the
 * Jaunt keeps its own and can say so, naming the choice it could not take (`want`).
 */
export function jauntChoice({ travelMode, pace, follow = false } = {}, jaunt = {}) {
  if (follow !== true || !jaunt) return { mode: null, kept: false, want: null };
  const allowed = Array.isArray(jaunt.allowed_modes) ? jaunt.allowed_modes : [];
  const want = wantedMode({ travelMode, pace });
  return allowed.includes(want) ? { mode: want, kept: false, want } : { mode: null, kept: true, want };
}

/** The mode a Jaunt travels by under the visitor's choice, or null for its own. */
export function jauntModeFor(choice = {}, jaunt = {}) {
  return jauntChoice(choice, jaunt).mode;
}

/**
 * The stored switch, read from saved settings (T-2727): on only if it was turned on —
 * a stored `true`. Anything else, missing, corrupt or a string, reads as off, and T-2652's
 * retired `arriveChosen` key says nothing about it.
 */
export function jauntsFollowFrom(saved) {
  return !!saved && typeof saved === 'object' && saved.jauntsFollowChoice === true;
}
