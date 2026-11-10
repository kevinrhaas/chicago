// SPDX-License-Identifier: GPL-3.0-or-later
/** One reconstructed curbside door; no seat, camera, boarding or traffic API.
 * The V19 static master does not opt in. Installation needs fresh matching
 * near/mid delivery hashes AND measured aperture/sweep/appearance qualification.
 */
import * as THREE from 'three';

export const CHARLES_NELSON = 'pa1904_glessner_john_j_c1900_charles_nelson';

/** Extract only the measured articulated root. Both LODs keep their own leaf. */
export function broughamDoorRig({ root, midRoot, spec, vehicleHashes }) {
  const plan = spec?.door_operation;
  if (!plan) return null;
  if (plan.schema !== 'chicago-brougham-qualified-right-door-v1'
    || plan.boarding_enabled !== false || plan.driver_passenger_fit !== false
    || !['real_aperture', 'closed_appearance', 'sampled_surface_clearance', 'continuous_sweep', 'near_mid_visual']
      .every(key => plan.qualification?.[key] === true)
    || !/^[a-f0-9]{64}$/.test(plan.geometry_proof_sha256 ?? '')
    || !['near', 'mid'].every(key => /^[a-f0-9]{64}$/.test(plan.deliveries?.[key]?.sha256 ?? '')
      && vehicleHashes[key] === plan.deliveries[key].sha256)
    || !midRoot) throw Error('Unqualified Brougham door delivery');
  const leaves = [root, midRoot].map(r => r.getObjectByName(plan.door_node));
  if (leaves.some(n => !n || n.parent?.name !== 'vehicle_body')) throw Error('Missing independent Brougham door');
  const angle = Number(plan.open_angle_deg) * Math.PI / 180;
  if (!Number.isFinite(angle) || angle >= 0 || angle < -Math.PI / 2
    || !Number.isFinite(plan.duration_s) || plan.duration_s <= 0
    || !Number.isFinite(plan.runtime_sweep_margin_m) || plan.runtime_sweep_margin_m < .35
    || !Array.isArray(plan.staff_stand_local_m) || plan.staff_stand_local_m.length !== 3
    || !plan.staff_stand_local_m.every(Number.isFinite)) throw Error('Invalid Brougham door bounds');
  let radius = 0;
  const inverse = new THREE.Matrix4(), point = new THREE.Vector3();
  root.updateMatrixWorld(true);
  for (const leaf of leaves) {
    leaf.updateWorldMatrix(true, true); inverse.copy(leaf.matrixWorld).invert();
    leaf.traverse(n => {
      const positions = n.geometry?.getAttribute('position');
      if (!positions) return;
      const local = inverse.clone().multiply(n.matrixWorld);
      for (let i = 0; i < positions.count; i++) {
        point.fromBufferAttribute(positions, i).applyMatrix4(local);
        radius = Math.max(radius, Math.hypot(point.x, point.z));
      }
    });
  }
  if (!(radius > 0 && radius < 2)) throw Error('Invalid actual door sweep radius');
  let fraction = 0;
  const worldPoint = local => root.localToWorld(new THREE.Vector3(...local));
  const staff = () => {
    const p = worldPoint(plan.staff_stand_local_m);
    return { e: p.x, n: -p.z, y: p.y };
  };
  const blocked = people => {
    const pivot = leaves[0].getWorldPosition(new THREE.Vector3());
    // Conservative full horizontal circle, including body radius: never a
    // claim that point/frustum tests prove physical whole-solid clearance.
    return people.some(p => p && Number.isFinite(p.e) && Number.isFinite(p.n)
      && Math.hypot(p.e - pivot.x, p.n + pivot.z) < radius + plan.runtime_sweep_margin_m);
  };
  const reset = () => { fraction = 0; for (const n of leaves) n.rotation.y = 0; };
  return {
    plan, leaves, radius, staff, blocked,
    get fraction() { return fraction; },
    get state() { return fraction === 0 ? 'closed' : fraction === 1 ? 'open' : 'ajar'; },
    pose(next, people) {
      if (!Number.isFinite(next) || next < 0 || next > 1) throw Error('Invalid door pose');
      if (blocked(people)) return { ok: false, why: 'Someone is in the carriage door’s swing' };
      fraction = next;
      for (const n of leaves) { n.rotation.y = angle * next; n.updateMatrixWorld(true); }
      return { ok: true };
    },
    // Only after the entire parked layer is hidden/retired. Never used to clear
    // an obstructed close while the visitor can see the door.
    resetHidden: reset,
  };
}

/** Extra actions on Charles's EXISTING person thing, through interact.js.
 * His actual actor walks the existing router's path; no replacement coachman,
 * teleport, synthetic navigation, occupied socket or camera motion is created.
 */
export function createCoachmanDoorActions({ parkedTransport, humans, days, router, visitor, interactions }) {
  const held = new Map();
  const release = actor => {
    if (!held.has(actor.id)) return;
    held.delete(actor.id);
    actor.stopPath();
    days.unhost(actor.id);
    // Native unhost clears the day span and token. The NEXT actual hour/date
    // supplies his destination, with safeHostTravel retained: not an old fixed
    // post, a five-minute activity override, a chord or a visible teleport.
  };
  const unsubscribe = interactions.on((thing, event) => {
    if (event === 'done' && thing.actor && held.has(thing.actor.id)) release(thing.actor);
  });
  const live = () => {
    if (!parkedTransport.doorsAvailable) return null;
    return parkedTransport.instances.find(i => {
      if (!i.door || i.row.model !== 'studebaker_brougham_1893') return false;
      for (let n = i.group; n; n = n.parent) if (!n.visible) return false;
      return true;
    });
  };
  const actionsFor = actor => {
    if (actor.personId !== CHARLES_NELSON || actor.indoors || actor.disposed
      || humans.shown === false || humans.isHeld?.(actor) || days?.isHosted?.(actor)) return [];
    const instance = live();
    if (!instance) return [];
    const door = instance.door;
    const bodies = () => [visitor(), ...(humans.actors ?? []).filter(a => !a.indoors && !a.disposed)
      .map(a => ({ e: a.e, n: a.n }))].filter(Boolean);
    const open = door.fraction < 1, target = open ? 1 : 0;
    let arrived = false, refusal = null;
    let start = door.fraction;
    const isLive = () => live() === instance && !actor.disposed && !actor.indoors && humans.shown !== false;
    const short = (a, b) => Math.hypot(a.e - b.e, a.n - b.n) <= .15;
    return [{ id: open ? 'carriage:open' : 'carriage:close',
      label: open ? 'Ask Charles to open the carriage door' : 'Ask Charles to close the carriage door',
      to: 'out',
      refuse: () => {
        if (!isLive()) return 'The carriage is not available here';
        const stand = door.staff();
        if (door.blocked([stand])) return 'There is no measured safe place for Charles beside this door';
        const route = router?.plan({ e: actor.e, n: actor.n }, stand, { mode: 'walk' });
        const points = route?.points;
        if (!Array.isArray(points) || points.length < 2 || !points.every(p => Array.isArray(p)
          && p.length === 2 && p.every(Number.isFinite))
          || Math.hypot(points.at(-1)[0] - stand.e, points.at(-1)[1] - stand.n) > .05) return 'Charles has no clear path to the carriage';
        if (door.blocked(bodies())) return 'Please stand clear of the carriage door’s swing';
        if (actor.root?.visible !== true || !days?.host || !days?.unhost) return 'Charles is not available here';
        // Host before interact marks this SAME person thing running: the normal
        // human-days ownership guard must be allowed to reject another errand.
        const result = days.host(actor.id, stand, { safeTravel: true,
          heading: instance.row.bearing_deg + 90,
          onArrive: () => { arrived = short(actor, stand); } });
        if (!result.ok) return result.why ?? 'Charles is not available';
        held.set(actor.id, actor);
        return null;
      },
      said: () => refusal ?? (door.fraction === target
        ? `Charles has ${open ? 'opened' : 'closed'} the carriage door. Boarding is not available.`
        : 'The carriage door has stopped'),
      steps: [
        { label: 'Charles is walking to the carriage', until: () => arrived || !!refusal, timeout: 60,
          run: t => {
            if (t === 1 && !arrived) {
              actor.stopPath(); refusal ??= 'Charles has not reached the carriage door';
            }
          } },
        { label: open ? 'Opening the carriage door' : 'Closing the carriage door',
          seconds: door.plan.duration_s, run: t => {
            if (t === 0) start = door.fraction;
            if (refusal || !arrived) return;
            if (!isLive()) { refusal = 'The carriage is no longer available'; return; }
            const result = door.pose(start + (target - start) * t, bodies());
            if (!result.ok) refusal = result.why;
          } },
      ],
    }];
  };
  actionsFor.dispose = () => {
    unsubscribe();
    for (const actor of [...held.values()]) release(actor);
  };
  return actionsFor;
}
