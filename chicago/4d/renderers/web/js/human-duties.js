// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-duties.js — what the men of a garrison are doing, not just where they stand (T-3490).
 *
 * The owner, 2026-11-07, of the T-3462 soldiers on the 1812 parade: *"the soldiers in 1812 are
 * standing in the dirt in the fort" … "maybe when placing them at this point they a few could
 * be in groups talking to each other and then they break up and come back together" … "like
 * all of them standing around aimlessly is awkward"*. A figure's record can say only where it
 * stands and whether it stands, walks or works (data/humans/human_instance.schema.json). A
 * record's `behaviour.duty` now names a duty shared with others, and this layer plays it:
 *
 *   knot   a few men standing together, facing in, talking: one speaks, his hand moving
 *          (human-actions.js `setTalk`), the others look at him (human-life.js `attend`) and
 *          now and then nod; the speaker changes every few seconds. After a while the knot
 *          breaks up: each man in his own moment walks off to his own place (`away`: a door,
 *          a porch, the gate passage), stands there a while, and comes back; whoever is back
 *          talks with whoever else is, and when all are back the knot talks again.
 *   beat   a sentry walking his post: from where he is placed to `to` and back, at each end
 *          a pause, turned to face `face_deg` (out from the pickets, or the magazine's door).
 *          The same with a longer pause is a man going to and fro between two doors.
 *   rank   men drawn up in a rank, standing still with their hands at their sides, looking at
 *          the man (`lead`) facing them, who speaks to them now and then (a fatigue party
 *          being told off, a roll called).
 *
 * HOURS. Kevin, 2026-11-07: *"I am concerned about all these soldiers around the fort hanging out
 * 24 7"*. A record's `behaviour.hours` [from, to] (local solar hours; `to` may pass midnight) is
 * when the man is out: outside it he is in quarters (humans.js `setIndoors`: not drawn, picked or
 * met), and the duty goes on without him. The guard at the gate and the magazine's sentry carry
 * no hours, so they stand and walk their posts all night.
 *
 * L1 holds (data/humans/contract.json § l1): nothing is said. The talk is a moving hand and
 * turned heads, never words, and no event of the day is acted out. Every timing is seeded by
 * the duty's id, so a harness sees the same afternoon on every load. A man far outside the
 * drawing range does not walk: he is put straight where he was going, so a knot is never held
 * up waiting for him and is where it should be when the visitor comes. Reconstructed
 * behaviour: liberty L-1812-garrison-stations-3462 (where and what) and L-human-actions-3415
 * (how the arms move).
 *
 * Nothing here knows the DOM; tools/test_human_duties.mjs drives it with stand-in actors.
 */

/** A deterministic PRNG of a string (FNV-1a into mulberry32), as driver-life.js's; kept here so
 *  this layer imports nothing (and its test needs no three.js). */
function seededRandom(key) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < key.length; i++) { h ^= key.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  let a = h || 1;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Seconds. A knot talks, then is apart; each man leaves within `leave_spread_s` of the break. */
export const KNOT = Object.freeze({ talk_s: [26, 58], apart_s: [9, 26], leave_spread_s: 6, speak_s: [2.6, 6.8], nod_p: 0.4,
  first_talk_s: [6, 40] });
/** Seconds a sentry stands at each end of his beat. */
export const BEAT = Object.freeze({ pause_s: [4, 10] });
/** Seconds the man facing a rank speaks, and is quiet. */
export const RANK = Object.freeze({ speak_s: [3, 7.5], quiet_s: [2.5, 7] });
/** Where a head is, over the feet, for a look (metres; the life layer only needs a point). */
const HEAD_M = 1.6;
export const DUTY_KINDS = Object.freeze(['knot', 'beat', 'rank']);

const bearing = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;
const pt = (p) => ({ e: p.local_e ?? p.e, n: p.local_n ?? p.n });

/** Whether `hour` (0-24) falls in [from, to), the span allowed to pass midnight. */
export function withinHours(hour, [from, to]) {
  if (!Number.isFinite(hour)) return true;
  return from <= to ? hour >= from && hour < to : hour >= from || hour < to;
}

export function createHumanDuties({ humans, three = null, hour = () => null } = {}) {
  let groups = [];
  let timed = [];
  let seen = -1;
  const Vec = three?.Vector3;

  function headOf(actor) {
    // The life layer reads a world point; the root's world position is the feet.
    if (Vec && actor.root?.getWorldPosition) { const v = actor.root.getWorldPosition(new Vec()); v.y += HEAD_M; return v; }
    return null;
  }
  const look = (actor, at, seconds) => { const p = headOf(at); if (p) actor.life?.attend?.(p, seconds); };
  const talk = (actor, on) => actor.actions?.setTalk?.(on);

  /**
   * Walk `actor` along `points` (local {e, n}), turning at the end to `heading`; then call
   * `done`. A man out of range is put there at once.
   */
  function go(actor, points, heading, done) {
    const end = points[points.length - 1];
    if (!actor.inRange || typeof actor.walkPath !== 'function') {
      actor.path = null;
      actor.e = end.e; actor.n = end.n;
      if (Number.isFinite(heading)) actor.heading = heading;
      actor.place?.();
      done(actor);
      return;
    }
    const ok = actor.walkPath([{ e: actor.e, n: actor.n }, ...points], { endHeading: heading, onArrive: done });
    if (!ok) done(actor);
  }

  function collect() {
    const byKey = new Map();
    for (const a of humans.actors) {
      const d = a.instance?.behaviour?.duty;
      if (!d || !DUTY_KINDS.includes(d.kind)) continue;
      const key = d.kind === 'beat' ? `beat:${a.id}` : `${d.kind}:${d.id}`;
      if (!byKey.has(key)) byKey.set(key, { key, kind: d.kind, id: d.id ?? a.id, members: [] });
      byKey.get(key).members.push({ actor: a, duty: d });
    }
    groups = [...byKey.values()].map(start);
    timed = humans.actors.filter((a) => Array.isArray(a.instance?.behaviour?.hours));
    seen = humans.actors.length;
  }

  function start(g) {
    const rand = seededRandom(`duty:${g.key}`);
    const between = ([a, b]) => a + (b - a) * rand();
    g.rand = rand; g.between = between; g.t = 0;
    for (const m of g.members) {
      const p = m.actor.instance.placement;
      m.home = { e: p.local_e, n: p.local_n, h: p.heading_deg };
    }
    if (g.kind === 'knot') {
      g.phase = 'talk'; g.until = between(KNOT.first_talk_s); g.speaker = null; g.speakT = between([0.5, 2.5]);
      for (const m of g.members) {
        const a = m.duty.away;
        m.away = a ? { e: a.local_e, n: a.local_n, h: a.heading_deg, via: (a.via ?? []).map(pt) } : null;
        m.mode = 'here'; m.left = false;
      }
    } else if (g.kind === 'beat') {
      const m = g.members[0], to = pt(m.duty.to);
      m.ends = [{ e: m.home.e, n: m.home.n }, to];
      m.face = Number.isFinite(m.duty.face_deg) ? m.duty.face_deg : m.home.h;
      m.pause = m.duty.pause_s ?? BEAT.pause_s;
      m.at = 0; m.mode = 'pause'; m.until = between(m.pause);
    } else if (g.kind === 'rank') {
      g.lead = g.members.find((m) => m.duty.lead) ?? null;
      g.speaking = false; g.until = between(RANK.quiet_s);
      for (const m of g.members) if (m !== g.lead) m.actor.actions?.hold?.('rest');
    }
    return g;
  }

  function stepKnot(g, dt) {
    const here = g.members.filter((m) => m.mode === 'here');
    // Whoever is together talks; one man alone does not.
    g.speakT -= dt;
    if (g.speaker && g.speaker.mode !== 'here') { talk(g.speaker.actor, false); g.speaker = null; g.speakT = 0; }
    if (g.speakT <= 0) {
      if (g.speaker) talk(g.speaker.actor, false);
      if (here.length >= 2) {
        const others = here.filter((m) => m !== g.speaker);
        const next = others[Math.floor(g.rand() * others.length)];
        const span = g.between(KNOT.speak_s);
        g.speaker = next; g.speakT = span;
        talk(next.actor, true);
        const listeners = here.filter((m) => m !== next);
        look(next.actor, listeners[Math.floor(g.rand() * listeners.length)].actor, span);
        for (const m of listeners) {
          look(m.actor, next.actor, span + 0.4);
          if (g.rand() < KNOT.nod_p) m.actor.life?.nod?.();
        }
      } else { g.speaker = null; g.speakT = 1; }
    }
    if (g.phase === 'talk' && g.t >= g.until) {
      g.phase = 'apart';
      for (const m of g.members) { m.leaveAt = g.t + g.rand() * KNOT.leave_spread_s; m.awayFor = g.between(KNOT.apart_s); m.left = false; }
    }
    if (g.phase !== 'apart') return;
    for (const m of g.members) {
      if (m.mode === 'here' && !m.left && m.away && g.t >= m.leaveAt) {
        m.left = true; m.mode = 'going';
        if (g.speaker === m) { talk(m.actor, false); g.speaker = null; g.speakT = 0.5; }
        go(m.actor, [...m.away.via, m.away], m.away.h, () => { m.mode = 'away'; m.backAt = g.t + m.awayFor; m.actor.setState?.('standing'); });
      } else if (m.mode === 'away' && g.t >= m.backAt) {
        m.mode = 'back';
        go(m.actor, [...[...m.away.via].reverse(), { e: m.home.e, n: m.home.n }], m.home.h, () => { m.mode = 'here'; m.actor.setState?.('talking'); });
      }
    }
    if (g.members.every((m) => m.mode === 'here' && (m.left || !m.away))) {
      g.phase = 'talk'; g.until = g.t + g.between(KNOT.talk_s);
    }
  }

  function stepBeat(g) {
    const m = g.members[0];
    if (m.mode !== 'pause' || g.t < m.until) return;
    m.mode = 'walk';
    const next = 1 - m.at, to = m.ends[next];
    // Turned to face his post's front at each end, whichever way he walked.
    go(m.actor, [to], m.face, () => { m.at = next; m.mode = 'pause'; m.until = g.t + g.between(m.pause); });
  }

  function stepRank(g) {
    if (!g.lead || g.t < g.until) return;
    g.speaking = !g.speaking;
    const span = g.between(g.speaking ? RANK.speak_s : RANK.quiet_s);
    g.until = g.t + span;
    talk(g.lead.actor, g.speaking);
    const men = g.members.filter((m) => m !== g.lead);
    if (g.speaking && men.length) {
      look(g.lead.actor, men[Math.floor(g.rand() * men.length)].actor, span);
      for (const m of men) look(m.actor, g.lead.actor, span + 0.5);
    }
  }

  const api = {
    get groups() { return groups; },
    /** One frame, after the figures' own (humans.update). */
    update(dt) {
      if (!humans || !(dt > 0)) return;
      if (humans.actors.length !== seen) collect();
      dt = Math.min(dt, 0.25);
      const h = hour();
      for (const a of timed) {
        const inside = !withinHours(h, a.instance.behaviour.hours);
        if (!!a.indoors !== inside) a.setIndoors?.(inside);
      }
      for (const g of groups) {
        g.t += dt;
        // A body loaded since the start: hold the rank's hands where the rank wants them.
        if (g.kind === 'rank') for (const m of g.members) if (m !== g.lead && m.actor.actions && m.actor.actions.held !== 'rest') m.actor.actions.hold?.('rest');
        if (g.kind === 'knot') stepKnot(g, dt);
        else if (g.kind === 'beat') stepBeat(g);
        else stepRank(g);
      }
    },
    /** Who is in quarters at this hour, for the harness. */
    get indoors() { return timed.filter((a) => a.indoors).map((a) => a.personId); },
    /** What each duty is doing, for the harness. */
    snapshot() {
      return groups.map((g) => ({
        key: g.key, kind: g.kind, t: +g.t.toFixed(2), phase: g.phase ?? null,
        speaker: g.kind === 'knot' ? g.speaker?.actor.personId ?? null : g.kind === 'rank' && g.speaking ? g.lead?.actor.personId ?? null : null,
        members: g.members.map((m) => ({ person: m.actor.personId, mode: m.mode ?? null, e: +m.actor.e.toFixed(2), n: +m.actor.n.toFixed(2) })),
      }));
    },
  };
  return api;
}
