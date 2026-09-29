/**
 * angles.js — degrees, and the two conversions between a dataset bearing and a
 * three yaw. Nothing else, and nothing imported.
 *
 * They lived in terrain.js, which is the right place for them by subject and the
 * wrong place by dependency: terrain.js loads three, the GLTF loader and the
 * prairie tile, so a module that wanted `bearingToYaw` — a multiplication —
 * pulled the whole renderer in behind it. travel.js is that module, and
 * tools/test_leg_notes.mjs is what proved it: a Node test of the jaunt's pause
 * and route notes could not import the travel controller at all, because four
 * modules down something asked for `three` and node has no three to give.
 *
 * So the arithmetic moves to a leaf. terrain.js re-exports all three names, so
 * every existing importer is unaffected; the point is that a caller who only
 * needs the conversion can now say so.
 */

/** Radians per degree. */
export const DEG = Math.PI / 180;

/** dataset compass bearing (deg, 0 = N, clockwise) -> three yaw about +Y. */
export function bearingToYaw(deg) {
  return -deg * DEG;
}

/** three yaw about +Y -> dataset compass bearing, normalised to [0, 360). */
export function yawToBearing(yaw) {
  return ((-yaw / DEG) % 360 + 360) % 360;
}
