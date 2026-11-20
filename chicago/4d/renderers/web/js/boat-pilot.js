/**
 * boat-pilot.js — take the helm of any boat: a schooner, a Mackinaw boat, a rowboat, a canoe, a
 * pirogue (T-3612).
 *
 * The owner, 2026-11-16: "I would also like you to have the option to drive the boat on your own
 * and pilot each boat down the river or in the lake ... Would be nice if I can board and pilot the
 * schooners and all boats".
 *
 * A layer that owns a boat (vessels.js, crossings.js) hands this a CRAFT:
 *   { id, name, kind, masted, length, beam, draft, helm: { x, y, z } (the eye, in the boat's
 *     frame: x ahead, y up from the water, z to starboard), pose: { e, n, bearing },
 *     begin(), move(pose, { speed, rudder }), end() }
 * and this steers it by the scene's navigation rules (data/boats/vessels_<scene>.json
 * `navigation`, written by tools/lay_vessels.py): the water must float the hull (its draft,
 * or only real water inside the harbour channel), nothing may cross a pier crib, a wharf deck
 * or a bridge that stops its kind (a drawbridge whose draw is down stops a masted vessel, a
 * raft bridge stops everything), nor another hull.
 *
 * The keys are the team's (transport-interactions.js): forward sets the pace and it holds,
 * back takes way off her (held, she goes astern), sideways is the helm. Look stays the
 * visitor's; the view turns with the boat. Go ashore puts the visitor down on the nearest
 * dry ground or deck, or, out on the lake, has a boat row them in.
 */
import { bearingToYaw } from './angles.js';

const DEG = Math.PI / 180;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const turn = (a, b) => ((b - a + 540) % 360) - 180;
const DEFAULT_KIND = { draft_m: 0.3, masted: false, max_speed_m_s: 1.6, turn_deg_s: 20, accel: 0.4 };

function insidePoly(e, n, pts) {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [x, y] = pts[i], [a, b] = pts[j];
    if ((y > n) !== (b > n) && e < (a - x) * (n - y) / (b - y) + x) hit = !hit;
  }
  return hit;
}

function segsCross(p1, p2, q1, q2) {
  const d = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  const d1 = d(q1, q2, p1), d2 = d(q1, q2, p2), d3 = d(p1, p2, q1), d4 = d(p1, p2, q2);
  return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0));
}

function segSegDist(a, b, c, d) {
  const sd = (p, s0, s1) => {
    const dx = s1[0] - s0[0], dy = s1[1] - s0[1], L2 = dx * dx + dy * dy;
    const t = L2 ? clamp(((p[0] - s0[0]) * dx + (p[1] - s0[1]) * dy) / L2, 0, 1) : 0;
    return Math.hypot(p[0] - s0[0] - t * dx, p[1] - s0[1] - t * dy);
  };
  if (segsCross(a, b, c, d)) return 0;
  return Math.min(sd(a, c, d), sd(b, c, d), sd(c, a, b), sd(d, a, b));
}

/** The hull's keel line and its two sides at the waterline, as segments in ENU. */
export function hullLines(e, n, bearing, length, beam) {
  const b = bearing * DEG, fe = Math.sin(b), fn = Math.cos(b), se = fn, sn = -fe;
  const P = (x, z) => [e + fe * x + se * z, n + fn * x + sn * z];
  const h = length / 2, w = beam / 2;
  return {
    keel: [P(h, 0), P(-h, 0)],
    sides: [[P(h * 0.8, w * 0.6), P(-h * 0.85, w * 0.9)], [P(h * 0.8, -w * 0.6), P(-h * 0.85, -w * 0.9)]],
    points: [P(h, 0), P(-h, 0), P(h * 0.5, w), P(h * 0.5, -w), P(-h * 0.5, w), P(-h * 0.5, -w), P(0, w), P(0, -w)],
  };
}

/**
 * Why a craft cannot lie at (e, n, bearing), or null when it can. `ground(e, n)` is the bed's
 * height (the water is 0); `hulls()` the other hulls on the water.
 */
export function blockedAt(nav, craft, e, n, bearing, { ground, hulls = () => [], depth = true, only = null } = {}) {
  const k = nav?.kinds?.[craft.kind] ?? DEFAULT_KIND;
  const draft = craft.draft ?? k.draft_m;
  const masted = craft.masted ?? k.masted;
  const L = craft.length, B = craft.beam;
  const lines = hullLines(e, n, bearing, L, B);
  const bounds = nav?.bounds;
  if (bounds) {
    for (const [pe, pn] of lines.points) {
      if (pe < bounds.e[0] || pe > bounds.e[1] || pn < bounds.n[0] || pn > bounds.n[1]) return 'the edge of the map';
    }
  }
  const channel = nav?.channel?.length > 2 ? nav.channel : null;
  if (depth) {
    for (const [pe, pn] of lines.points) {
      const d = -ground(pe, pn);
      const need = channel && insidePoly(pe, pn, channel) ? (nav.channel_depth_m ?? 0.3) : draft + (nav?.under_keel_m ?? 0.15) * 0.5;
      if (d < need) return d < 0.05 ? 'aground on the bank' : 'too shallow for her draft';
    }
  }
  if (only === 'depth') return null;
  for (const o of nav?.obstacles ?? []) {
    if (o.stops === 'masted' && !masted) continue;
    const pts = o.pts;
    const hit = lines.points.some(([pe, pn]) => insidePoly(pe, pn, pts))
      || [lines.keel, ...lines.sides].some(([a, b]) => pts.some((p, i) => segsCross(a, b, p, pts[(i + 1) % pts.length])));
    if (hit) {
      return { pier: 'the pier', wharf: 'a wharf', drawbridge: 'the draw is down', bridge: 'the bridge is too low for her masts', raft_bridge: 'the raft bridge' }[o.kind] ?? 'something in the way';
    }
  }
  for (const h of hulls()) {
    if (h.id === craft.id) continue;
    const other = hullLines(h.e, h.n, h.bearing, h.length, h.beam);
    if (Math.hypot(h.e - e, h.n - n) > (h.length + L) / 2 + 4) continue;
    if (segSegDist(lines.keel[0], lines.keel[1], other.keel[0], other.keel[1]) < (h.beam + B) / 2 + 0.2) return 'another boat';
  }
  return null;
}

/**
 * @param {object} o
 *   nav () => the scene's navigation rules · ground (e, n) => bed height · hulls () => every
 *   hull on the water · standable (e, n) => true where the visitor can be put down · onBoard
 *   (craft, aboard) · say (text)
 */
export function createBoatPilot({ nav = () => null, ground, hulls = () => [], standable = () => false, onBoard = () => {}, say = () => {} } = {}) {
  let craft = null, cruise = 0, astern = false, rudder = 0, speed = 0, blocked = null, lastBearing = null;
  let landing = null;
  const pilot = {
    get active() { return !!craft; },
    get craft() { return craft; },
    get speed() { return speed; },
    get blocked() { return blocked; },
    get cruise() { return cruise; },

    /** Aboard and at the helm. False if a boat is already held. */
    take(c) {
      if (craft || !c) return false;
      craft = c;
      cruise = 0; astern = false; rudder = 0; speed = 0; blocked = null; lastBearing = null;
      try { c.begin(); } catch { /* the layer keeps the boat as it was */ }
      onBoard(c, true);
      return true;
    },

    /**
     * Before the walk: the movement keys are the helm while aboard. A push forward sets the
     * pace and it holds; a pull back takes the way off, and held from a stand goes astern.
     */
    drive(intent) {
      if (!craft || !intent) return false;
      const f = clamp(intent.forward ?? 0, -1, 1), s = clamp(intent.strafe ?? 0, -1, 1);
      const push = Math.hypot(f, s);
      const along = push > 0.15 && Math.abs(f) >= Math.abs(s) - 1e-9;
      if (along && f > 0) { cruise = Math.max(cruise, Math.min(1, push)); astern = false; }
      else if (along && f < 0) {
        if (speed > 0.15) cruise = 0;
        else astern = true;
        cruise = 0;
      } else if (astern && !(along && f < 0)) astern = false;
      rudder = Math.abs(s) > 0.1 ? s : 0;
      intent.forward = 0; intent.strafe = 0; intent.rise = 0; intent.sprint = false;
      return true;
    },

    /** One frame: the boat makes her way, turns to her helm, and stops short of what she meets. */
    update(dt) {
      if (!craft) return;
      dt = Math.min(Math.max(dt, 0), 0.1);
      const rules = nav();
      const k = rules?.kinds?.[craft.kind] ?? DEFAULT_KIND;
      const max = k.max_speed_m_s;
      const target = astern ? -0.35 * max : cruise * max;
      const a = k.accel ?? 0.3;
      speed += clamp(target - speed, -a * 1.6 * dt, a * dt);
      if (Math.abs(speed) < 0.005 && target === 0) speed = 0;
      const p = craft.pose;
      // Steerage way: a big hull answers her helm only when moving; a small boat pivots on her oars.
      const way = craft.masted ? clamp(Math.abs(speed) / 1.4, 0.12, 1) : clamp(0.45 + Math.abs(speed) / max, 0.45, 1.2);
      const dB = rudder * k.turn_deg_s * way * dt * (speed < -0.05 ? -1 : 1);
      const nb = (p.bearing + dB + 360) % 360;
      const ne = p.e + Math.sin(nb * DEG) * speed * dt, nn = p.n + Math.cos(nb * DEG) * speed * dt;
      // A boat already touching (taken off a bank, left in the shallows) may work herself off:
      // only a crib, a deck, a bridge or another hull stops her until she floats free.
      const ask = { ground, hulls, depth: !blockedAt(rules, craft, p.e, p.n, p.bearing, { ground, hulls, depth: true, only: 'depth' }) };
      const why = (ne !== p.e || nn !== p.n || dB) ? blockedAt(rules, craft, ne, nn, nb, ask) : null;
      if (!why) { craft.move({ e: ne, n: nn, bearing: nb }, { speed, rudder }); blocked = null; return; }
      // Whatever stops her takes her way off; turning where she lies is still allowed if that is clear.
      const turnBlocked = dB ? blockedAt(rules, craft, p.e, p.n, nb, ask) : 'still';
      craft.move({ e: p.e, n: p.n, bearing: turnBlocked ? p.bearing : nb }, { speed: 0, rudder });
      if (why !== blocked) say(`Held: ${why}`);
      blocked = why;
      speed = 0; cruise = 0; astern = false;
    },

    /** After the walk: the eye is at the helm. The view turns with the boat. */
    hold(walker, WALK) {
      const s = walker?.state;
      if (!s) return false;
      if (landing && !craft) {
        const l = landing; landing = null;
        walker.teleport({ local_e: l.e, local_n: l.n, yaw_deg: walker.bearingDeg, pitch_deg: s.pitch / DEG });
        return false;
      }
      if (!craft) return false;
      if (s.flying) { pilot.leave({ land: false }); return false; }
      const p = craft.pose, h = craft.helm ?? { x: 0, y: 1.6, z: 0 };
      const b = p.bearing * DEG, fe = Math.sin(b), fn = Math.cos(b);
      const e = p.e + fe * h.x + fn * h.z, n = p.n + fn * h.x - fe * h.z;
      const y = (p.y ?? 0) + h.y;
      s.e = e; s.n = n; s.eyeY = y;
      s.groundY = y - (WALK?.eyeHeight ?? 1.6);
      s.altitude = 0; s.stepEase = 0; s.bob = 0;
      // Taking the helm, the visitor faces her bow; after that the view turns with her.
      s.yaw = bearingToYaw(lastBearing === null ? p.bearing : (walker.bearingDeg + turn(lastBearing, p.bearing) + 360) % 360);
      lastBearing = p.bearing;
      walker.apply();
      return true;
    },

    /**
     * Go ashore: the nearest dry ground or deck within a long step of the side, or, from out on
     * the water, the nearest anywhere (a boat rows the visitor in). Returns the words said.
     */
    leave({ land = true } = {}) {
      if (!craft) return null;
      const c = craft;
      let to = null, far = false;
      if (land) {
        const p = c.pose;
        const reach = c.beam / 2 + 6;
        const near = (r0, r1, dr, steps) => {
          for (let r = r0; r <= r1; r += dr) {
            let best = null;
            for (let i = 0; i < steps; i++) {
              const a = (i / steps) * Math.PI * 2;
              const e = p.e + Math.sin(a) * r, n = p.n + Math.cos(a) * r;
              if (standable(e, n)) { const d = Math.hypot(e - p.e, n - p.n); if (!best || d < best.d) best = { e, n, d }; }
            }
            if (best) return best;
          }
          return null;
        };
        to = near(c.beam / 2 + 0.8, reach + c.length / 2, 1, 36);
        if (!to) { to = near(reach + c.length / 2, 1600, 8, 48); far = !!to; }
        if (!to) { say('No shore to put you on'); return null; }
        landing = { e: to.e, n: to.n };
      }
      craft = null; speed = 0; cruise = 0; rudder = 0; blocked = null; lastBearing = null;
      try { c.end(); } catch { /* the layer takes her back as she lies */ }
      onBoard(c, false);
      const words = far ? 'A boat rows you ashore' : 'Ashore';
      if (land) say(words);
      return words;
    },
  };
  return pilot;
}
