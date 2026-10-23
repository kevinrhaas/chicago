/** Explicit roof-staff anchors; pure logic, with no renderer dependency.
 *
 * Existing freestanding staffs retain their bounding-box mount. An explicit
 * anchor is phase/date-specific and never silently falls back to a hotel box.
 * Its local frame is footprint metres [east, north, up], mapped to glTF's
 * [east, up, south] before the building's existing placement matrix is applied.
 */
// Read by validate.py as well as exercised by test_flag_anchors.mjs.
export const CONSUMED_FORM = Object.freeze(["flag", "flag_flying", "flag_anchor"]);

const valueOf = a => a && typeof a === 'object' && !Array.isArray(a) ? a.value : a;

export function flownFlags(registry, levels) {
  const grade = a => levels[a && typeof a === 'object' ? a.confidence : null] ?? levels.reconstructed;
  const out = [];
  for (const record of registry.values()) {
    const sidecar = record.sidecar ?? {};
    const at = sidecar.attributes ?? {};
    const pattern = valueOf(at.flag);
    if (!pattern || valueOf(at.flag_flying) !== true) continue;
    const anchored = Object.hasOwn(at, 'flag_anchor');
    out.push({ id: record.id, pattern,
      confidence: Math.max(grade(at.flag), grade(at.flag_flying), ...(anchored ? [grade(at.flag_anchor)] : [])),
      ...(anchored ? { anchor: valueOf(at.flag_anchor), phase: sidecar.phase, targetDate: sidecar.target_date } : {}),
    });
  }
  return out;
}

function validDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const millis = Date.parse(value + 'T00:00:00Z');
  return Number.isFinite(millis) && new Date(millis).toISOString().slice(0, 10) === value;
}

/** Returns a mount in local glTF coordinates, or throws a reported refusal. */
export function flagMount(flag, box, { fly, hoistToFly, truckGap }) {
  if (!Object.hasOwn(flag, 'anchor')) {
    return { axis: [(box.min[0]+box.max[0])/2, box.max[1], (box.min[2]+box.max[2])/2],
      foot: [(box.min[0]+box.max[0])/2, box.min[1], (box.min[2]+box.max[2])/2],
      radius: Math.max(.04, Math.min(box.max[0]-box.min[0], box.max[2]-box.min[2])/2*.6),
      fly, hoist: fly*hoistToFly };
  }
  const a = flag.anchor;
  if (!a || typeof a !== 'object' || Array.isArray(a)) throw new Error('flag_anchor must be an object');
  if (a.frame !== 'footprint_enu_m') throw new Error('flag_anchor frame must be footprint_enu_m');
  if (!a.phase || a.phase !== flag.phase) throw new Error('flag_anchor phase disagrees with the drawn phase');
  if (![a.valid_from, a.valid_to, flag.targetDate].every(validDate) || a.valid_from > a.valid_to)
    throw new Error('flag_anchor needs a valid inclusive date interval and scene target_date');
  if (flag.targetDate < a.valid_from || flag.targetDate > a.valid_to)
    throw new Error('flag_anchor is outside its supported pattern/date interval');
  const vector = v => Array.isArray(v) && v.length === 3 && v.every(n => typeof n === 'number' && Number.isFinite(n));
  if (!vector(a.head) || !vector(a.foot)) throw new Error('flag_anchor head/foot must be finite [east,north,up] triples');
  const map = v => [v[0], v[2], -v[1]];
  const axis = map(a.head), foot = map(a.foot), height = axis[1]-foot[1];
  if (Math.abs(axis[0]-foot[0]) > 1e-6 || Math.abs(axis[2]-foot[2]) > 1e-6 || height < .5)
    throw new Error('flag_anchor needs an upright staff at least half a metre tall');
  if (typeof a.radius_m !== 'number' || !Number.isFinite(a.radius_m) || a.radius_m < .005 || a.radius_m > .5)
    throw new Error('flag_anchor radius_m outside .005..0.5 metres');
  if (typeof a.fly_m !== 'number' || !Number.isFinite(a.fly_m) || a.fly_m < .1 || a.fly_m > 12 ||
      typeof a.hoist_m !== 'number' || !Number.isFinite(a.hoist_m) || a.hoist_m < .1 || a.hoist_m > height-truckGap)
    throw new Error('flag_anchor cloth dimensions are invalid or extend below the staff');
  // Catch a stale head/foot after a model change instead of flying it elsewhere.
  if ([axis, foot].some(p => p.some((v, i) => v < box.min[i]-.03 || v > box.max[i]+.03)))
    throw new Error('flag_anchor head/foot fall outside the drawn model');
  return { axis, foot, radius: a.radius_m, fly: a.fly_m, hoist: a.hoist_m };
}
