/**
 * building-feet.js — where a building actually meets the ground (T-3029).
 *
 * buildings.js stands every structure on the LOWEST ground under it. Until
 * T-3029 "under it" meant a 5 x 5 grid over the mesh's bounding box, and a box
 * is not a footprint: it reaches out to the eaves' overhang and fills in the
 * empty corners beside a wing. On flat ground that costs nothing. On the bank it
 * is the whole fault the owner saw — the Green Tree Tavern's rear ell runs down
 * the west bank of the South Branch, the box's far corner lands 1.3 m beside the
 * ell's wall and 0.25 m past its eave, on ground 0.33 m lower than anything a
 * wall stands on, and the whole inn was bedded there, 0.88 m under its own front
 * door.
 *
 * The GLB contract already says where the ground is in a structure's frame: the
 * base of its walls is y = 0 (docs/GLB-CONTRACT.md). So the feet are the
 * triangle edges that lie on that plane — the bottom of every wall, post and
 * stoop — sampled along their length, because a long wall on a slope meets its
 * lowest ground between its corners as often as at one. A structure with no
 * geometry on the plane (none in the shipped town) keeps the old box grid.
 */

/** How far off y = 0 a vertex may sit and still be standing on the ground. */
export const FOOT_Y = 0.05;
/** The longest stretch of a foot edge left unsampled. */
export const FOOT_STEP_M = 1.0;
/** Samples closer than this are one sample: a wall's two faces are one foot. */
export const FOOT_CELL_M = 0.5;

/**
 * Add one geometry's feet to `feet` (a Map the caller keeps per structure).
 * Positions are read in the structure's own frame, in metres.
 * @param {Map<string, [number, number]>} feet  cell key -> [x, z]
 * @param {{ getAttribute(name: string): any, getIndex(): any }} geo
 */
export function addFeet(feet, geo) {
  const pos = geo.getAttribute('position');
  if (!pos) return feet;
  const count = pos.count;
  const onGround = new Uint8Array(count);
  let any = false;
  for (let i = 0; i < count; i += 1) {
    if (Math.abs(pos.getY(i)) <= FOOT_Y) { onGround[i] = 1; any = true; }
  }
  if (!any) return feet;
  const put = (x, z) => {
    const key = `${Math.round(x / FOOT_CELL_M)},${Math.round(z / FOOT_CELL_M)}`;
    if (!feet.has(key)) feet.set(key, [x, z]);
  };
  const edge = (a, b) => {
    if (!onGround[a] || !onGround[b]) return;
    const ax = pos.getX(a); const az = pos.getZ(a);
    const bx = pos.getX(b); const bz = pos.getZ(b);
    const steps = Math.max(1, Math.ceil(Math.hypot(bx - ax, bz - az) / FOOT_STEP_M));
    for (let s = 0; s <= steps; s += 1) {
      put(ax + ((bx - ax) * s) / steps, az + ((bz - az) * s) / steps);
    }
  };
  const index = geo.getIndex();
  const tris = index ? index.count : count;
  const at = index ? (k) => index.getX(k) : (k) => k;
  for (let t = 0; t + 2 < tris; t += 3) {
    const a = at(t); const b = at(t + 1); const c = at(t + 2);
    edge(a, b); edge(b, c); edge(c, a);
  }
  return feet;
}

/** The feet packed as x, z pairs once loading is done: a few hundred bytes a
 *  building instead of an array per sample, kept for the app's lifetime. */
export function packFeet(feet) {
  const out = new Float32Array(feet.size * 2);
  let i = 0;
  for (const [x, z] of feet.values()) { out[i++] = x; out[i++] = z; }
  return out;
}

/** The feet as a plain list of [x, z], in the structure's frame, from either
 *  the loading Map or the packed pairs. */
export function feetPoints(feet) {
  if (!feet) return [];
  if (feet instanceof Float32Array) {
    const out = [];
    for (let i = 0; i + 1 < feet.length; i += 2) out.push([feet[i], feet[i + 1]]);
    return out;
  }
  return [...feet.values()];
}
