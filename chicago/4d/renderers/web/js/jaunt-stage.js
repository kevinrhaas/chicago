// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * jaunt-stage.js — a jaunt stop's history, played by its people (T-3553).
 *
 * The owner, 2026-11-14, of the 1812 jaunts: *"place all the right people at the right scenes
 * from history so we can witness the events, the attack on lees, them fleeing, the people at
 * the murder site, etc. you should be able to watch the event unfold, like the argument
 * between la lime and kiznie, you should see the column coming down the shore and they can
 * come from the distance and pass you, for the natives they can be in groups collected,
 * laying down or kneeling in preparation for the attack"*. And, picked on a card the same day
 * for an audience of students, **"Build-up and aftermath"**: a scene plays up to the moment and
 * shows the fallen lying still after it; no blow, no shot, no blood is staged.
 *
 * So a stop may carry a `stage` (data/jaunts/schema.json): its `cast`, each a person of the
 * scene (`person`, their own carded figure, face and dress) or an unnamed figure (`extra`,
 * with the dress it wears), standing `at` a mark, turned to a `heading`, in a `pose` (stand,
 * kneel, kneel2, crouch, sit, prone, lie: human-life.js POSTURES), and `beats`: from `t`
 * seconds after the visitor arrives, walk a way (`walk`, at `pace` m/s), turn (`heading`) or
 * face a mark or a castmate (`face`), take a pose (`pose`, over `ease` s), talk with the hand
 * (`talk`), greet, go out of sight (`hide`: into a house, a boat) and come back (`show`), or
 * be found somewhere else (`place`, out of sight: across the river after a crossing). The stage is built at
 * the beginning (t = 0) while the visitor travels to the stop and plays when they arrive;
 * Watch again plays it from the beginning. A stage may also take the town's horse teams
 * (`teams`: a team by its row id in data/transport/driven/loops.json, with its own mark and
 * walking beats, its vehicle root walked along them): the 1812 column's wagons, driven by the
 * men who drive them every day, and castmates who `ride` one sit at a seat on it (vehicle-local
 * metres) and go where it goes. A `tier: "desktop"` castmate is left out at the
 * Light tier (phones), so a phone keeps the scene with fewer of its crowd (the owner,
 * 2026-11-10: people are never dropped on phones; fewer is not none).
 *
 * The staged figures are not the town's: each is a figure made as the people layer makes its
 * own (humans.createActor, its looks, ground and tier), driven only here, while the jaunt
 * holds the person's everyday figure out of the scene (jaunts.js keeps no castmate in the
 * crowd), so a person is never drawn twice. Nothing here says a word: the words are the
 * stop's text; the hand that talks is the only speech.
 *
 * An adults jaunt (the owner, 2026-11-15: "targeted at adults and shows everything incredibly
 * graphically") also stages the fighting the student jaunts leave to their text: a castmate holds
 * a weapon (`arm`: a tomahawk, a war club, a knife, a pistol, a musket) and makes its motions
 * (`act`: strike, stab, aim, fire, lower; `struck` when hit), turned to whoever `face` names;
 * the fallen go down (kneel2, then lie or `fallen`, face down). The weapons, the motions and the
 * smoke are human-fight.js's, handed in as `fight` (none: nothing is held, as in the gate's
 * harness). The compiler refuses `arm` and `act` in any jaunt not for adults.
 *
 *   sync(stop, { arrived })  build `stop`'s stage (or keep it), and play it once arrived
 *   replay()                 from the beginning again
 *   release()                take every staged figure away
 *   update(dt)               one frame
 *   ids                      the person ids the stage plays now
 */

export const PACES = Object.freeze({ walk: null, brisk: 1.75, hurry: 2.2, slow: 0.9 });
export const POSES = Object.freeze(['stand', 'kneel', 'kneel2', 'crouch', 'sit', 'prone', 'lie', 'fallen']);
/** How far beyond the people layer's animation range a posed figure keeps its pose drawn. */
export const STAGE_ANIMATE_M = 160;

const bearing = (de, dn) => ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360;
const pt = (p) => (Array.isArray(p) && p.length === 2 && p.every(Number.isFinite) ? { e: p[0], n: p[1] } : null);

/** The person ids a stop's stage casts (its unnamed figures have none). */
export function stageIds(stop) {
  return (Array.isArray(stop?.stage?.cast) ? stop.stage.cast : []).map((c) => c?.person).filter((id) => typeof id === 'string' && id);
}

/** The cast a tier draws: a `tier: "desktop"` castmate is left out at Light. */
export function castFor(stop, tier = 'full') {
  return (Array.isArray(stop?.stage?.cast) ? stop.stage.cast : []).filter((c) => c && pt(c.at) && (tier !== 'light' || c.tier !== 'desktop'));
}

/**
 * Where a castmate stands, and how, `t` seconds into the stage, by its beats alone (no
 * figure): { e, n, heading, pose, hidden, talk }. A walk under way is placed along its way
 * at its pace (the figure's own walk where none is given: `walkSpeed`). For the harness and
 * the gate, and to put a figure where a replay or a late arrival finds it.
 */
export function castAt(c, t, { walkSpeed = 1.3 } = {}) {
  const at = pt(c.at);
  const s = { e: at.e, n: at.n, heading: Number.isFinite(c.heading) ? c.heading : 0, pose: c.pose ?? 'stand', hidden: !!c.hidden, talk: !!c.talk,
    arm: c.arm ?? 'none', act: null };
  for (const b of sortedBeats(c)) {
    if (b.t > t) break;
    const to = pt(b.place);
    if (to) { s.e = to.e; s.n = to.n; }
    if (Array.isArray(b.walk)) {
      const way = [{ e: s.e, n: s.n }, ...b.walk.map(pt).filter(Boolean)];
      const speed = Number.isFinite(b.pace) ? b.pace : PACES[b.pace] ?? walkSpeed;
      let left = Math.max(0, t - b.t) * speed;
      for (let i = 0; i < way.length - 1; i++) {
        const a = way[i], z = way[i + 1], len = Math.hypot(z.e - a.e, z.n - a.n);
        if (len > 1e-9) s.heading = bearing(z.e - a.e, z.n - a.n);
        if (left >= len) { s.e = z.e; s.n = z.n; left -= len; continue; }
        s.e = a.e + ((z.e - a.e) * left) / len; s.n = a.n + ((z.n - a.n) * left) / len; left = 0; break;
      }
      if (Number.isFinite(b.heading) && left > 0) s.heading = b.heading;
    } else if (Number.isFinite(b.heading)) s.heading = b.heading;
    if (b.pose) s.pose = b.pose;
    if (b.hide) s.hidden = true;
    if (b.show) s.hidden = false;
    if (typeof b.talk === 'boolean') s.talk = b.talk;
    if (b.arm) s.arm = b.arm;
    if (b.act) s.act = { act: b.act, t: b.t };
  }
  return s;
}

/** The town teams a stop's stage takes (each by its row id, with a mark and beats). */
export function teamsFor(stop) {
  return (Array.isArray(stop?.stage?.teams) ? stop.stage.teams : []).filter((c) => c && typeof c.team === 'string' && pt(c.at));
}

/** A seat on a team posed at (e, n) facing `heading` (deg): vehicle-local [x, y, z] -> ENU, the
 *  same turn as transport-loop.js localToEnu (+z ahead, +x to the left). */
export function seatAt(pose, seat) {
  const yaw = Math.PI - (pose.heading * Math.PI) / 180, [x, y, z] = seat;
  return { e: pose.e + Math.cos(yaw) * x + Math.sin(yaw) * z, n: pose.n + Math.sin(yaw) * x - Math.cos(yaw) * z,
    y: (Number.isFinite(pose.height) ? pose.height : 0) + y };
}

function sortedBeats(c) {
  return (Array.isArray(c?.beats) ? c.beats : []).filter((b) => b && Number.isFinite(b.t)).slice().sort((a, b) => a.t - b.t);
}

/** How long a stage runs: its last beat, and the longest walk at a walking pace after it. */
export function stageLength(stop, { walkSpeed = 1.3 } = {}) {
  let end = 0;
  for (const c of [...castFor(stop), ...teamsFor(stop)]) {
    let here = pt(c.at);
    for (const b of sortedBeats(c)) {
      let t = b.t;
      if (Array.isArray(b.walk)) {
        const speed = Number.isFinite(b.pace) ? b.pace : PACES[b.pace] ?? walkSpeed;
        for (const p of b.walk.map(pt).filter(Boolean)) { t += Math.hypot(p.e - here.e, p.n - here.n) / speed; here = p; }
      }
      end = Math.max(end, t);
    }
  }
  return end;
}

/**
 * `humans` the people layer (createActor, get, shown, tier); `parent` the three.js group the
 * staged figures stand in; `resolve(personId)` -> { instance, person } for a person of the
 * scene not drawn in town (a gathering's inside-only resident), or null; `tier()` the people
 * tier now; `eye()` the eye (a world Vector3) each figure is updated from.
 */
export function createJauntStage({ humans, parent = null, resolve = () => null, tier = () => 'full', eye = () => null, teams = null, fight = null } = {}) {
  let stopKey = null, stop = null, cast = [], clock = 0, playing = false;
  // Adults jaunts: the guns' flash and smoke (human-fight.js createFightFx), made once.
  const fx = fight?.createFightFx && parent ? fight.createFightFx(parent) : null;
  // T-3553: the town teams this stage has taken: { c, actor, heading } (actor once loaded).
  let wagons = [], askedLoad = -Infinity;
  const TURN_DEG_S = 30;

  function instanceFor(c, i) {
    const at = pt(c.at);
    const placement = { local_e: at.e, local_n: at.n, heading_deg: Number.isFinite(c.heading) ? c.heading : 0, anchor: 'terrain' };
    const base = { contract_version: 1, scene: null, animation: { clip: 'idle', loop: true, phase: ((i * 0.618) % 1) },
      behaviour: { state: 'standing' }, interaction: { selectable: false, radius_m: 0, opens: 'none' }, lod: { policy: 'auto' },
      display: 'shown', review_required: false };
    if (c.person) {
      // T-3557: never a second of someone a vehicle has (riding in a carriage, on its box).
      if (humans?.external?.(c.person)) return null;
      const real = humans?.get?.(c.person);
      const own = real?.instance ?? resolve(c.person)?.instance ?? null;
      if (!own) return null;
      return { instance: { ...own, ...base, id: `stage:${stopKey}:${i}:${c.person}`, scene: own.scene, person_id: c.person, placement,
        appearance: { ...own.appearance } }, person: real?.person ?? resolve(c.person)?.person ?? null };
    }
    if (c.extra && c.dress) {
      return { instance: { ...base, id: `stage:${stopKey}:${i}:${c.extra}`, scene: String(c.scene ?? ''), placement,
        appearance: { asset_id: c.dress, ...(c.dress_of ? { dress_of: c.dress_of } : {}) }, provenance: null }, person: null };
    }
    return null;
  }

  function begin(c, actor) {
    const s = castAt(c, 0);
    actor.path = null;
    actor.e = s.e; actor.n = s.n; actor.heading = s.heading; actor.standY = null;
    actor.setState?.('standing');
    actor.setPosture?.(s.pose, { seconds: 0 });
    actor.actions?.setTalk?.(s.talk);
    actor.setIndoors?.(s.hidden);
    actor.place?.();
  }

  /** What the castmate's right hand holds: the weapon drawn in it, and the hand told. */
  function arm(m, kind) {
    m.arm = kind && kind !== 'none' ? kind : 'none';
    if (m.weapon) { m.weapon.removeFromParent(); m.weapon = null; }
    if (m.arm !== 'none' && fight?.weaponGroup) {
      m.weapon = fight.weaponGroup(m.arm);
      if (m.weapon) { m.weapon.visible = false; parent?.add?.(m.weapon); }
    }
    m.actor.actions?.wield?.(m.arm);
  }

  /** After the figure's frame: its weapon where its hand is, a soldier's own slung musket out of
   *  sight while he holds one, and a shot's flash and smoke. */
  function wieldFrame(m) {
    const a = m.actor, actions = a.actions;
    if (!actions?.wield) return;
    if (actions.fight?.arm !== m.arm) actions.wield(m.arm);
    if (m.pendingAct && actions.act) { actions.act(m.pendingAct); m.pendingAct = null; }
    const gun = m.arm === 'musket' || m.arm === 'rifle';
    if (gun !== !!m.slungHidden) {
      a.root.traverse((o) => { if (o.name === 'garrison_musket') o.visible = !gun; });
      m.slungHidden = gun;
    }
    if (m.weapon) {
      const frame = a.root.visible && !a.indoors ? actions.gripFrame?.('r') : null;
      m.weapon.visible = !!frame;
      if (frame) fight.placeWeapon(m.weapon, frame);
    }
    const shots = actions.takeShot?.() ?? 0;
    if (shots && m.weapon && fx) { const z = fight.muzzleOf(m.weapon); if (z) for (let i = 0; i < shots; i++) fx.shoot(z.at, z.dir); }
  }

  function build(next) {
    teardown();
    stop = next;
    const list = castFor(next, tier());
    cast = [];
    list.forEach((c, i) => {
      const made = instanceFor(c, i);
      if (!made || !humans?.createActor) return;
      let actor;
      try {
        actor = humans.createActor(made.instance, { person: made.person,
          identity: c.person ? { kind: 'person', personId: c.person, person: made.person, profile: null, role: null }
            : { kind: 'extra', personId: null, person: null, profile: null, role: null } });
      } catch { return; }
      actor.jauntStage = true;
      actor.stageName = c.person ? null : c.name ?? null;
      const posed = c.pose && c.pose !== 'stand' || sortedBeats(c).some((b) => b.pose && b.pose !== 'stand');
      if (posed) actor.animateM = STAGE_ANIMATE_M;
      parent?.add?.(actor.root);
      const m = { c, actor, beats: sortedBeats(c), next: 0 };
      if (c.ride && typeof c.ride.team === 'string' && Array.isArray(c.ride.seat) && c.ride.seat.length === 3) {
        m.ride = c.ride;
        actor.setPosture?.(c.pose ?? 'sit', { seconds: 0 });
      }
      begin(c, actor);
      arm(m, castAt(c, 0).arm);
      cast.push(m);
    });
    wagons = teamsFor(next).map((c) => ({ c, actor: null, heading: castAt(c, 0).heading, pose: null }));
    askedLoad = -Infinity;
  }

  function teardown() {
    for (const m of cast) { m.weapon?.removeFromParent?.(); try { m.actor.dispose(); } catch { /* gone already */ } }
    fx?.clear();
    for (const w of wagons) { try { w.actor?.unstage?.(); } catch { /* gone already */ } }
    cast = []; wagons = []; stop = null; playing = false; clock = 0;
  }

  /** Take each team once it is loaded, and stand it where the stage has it now. */
  function driveTeams(step) {
    if (!wagons.length) return;
    let missing = false;
    for (const w of wagons) {
      if (!w.actor || w.actor.disposed || w.actor.mode !== 'staged') {
        const actor = teams?.get?.(w.c.team) ?? null;
        if (!actor || !actor.stage?.()) { w.actor = null; missing = true; continue; }
        w.actor = actor; w.heading = castAt(w.c, clock).heading; w.pose = null;
      }
      const s = castAt(w.c, clock);
      // The team swings round a bend at a horse's pace, not on the spot.
      const d = ((s.heading - w.heading + 540) % 360) - 180, most = TURN_DEG_S * step;
      w.heading = (w.heading + (w.pose ? Math.max(-most, Math.min(most, d)) : d) + 360) % 360;
      w.actor.stageTo({ e: s.e, n: s.n, heading_deg: w.heading, dt: step });
      const p = w.actor.pose;
      w.pose = { e: s.e, n: s.n, heading: w.heading, height: p?.height ?? null };
    }
    // Asked again every two seconds of the page's own time (a held stage's frames carry none).
    const now = Date.now();
    if (missing && now - askedLoad >= 2000) { askedLoad = now; try { teams?.load?.(); } catch { /* asked again later */ } }
  }

  /** A rider sits where their seat on the team is now. */
  function seatRider(m) {
    const w = wagons.find((x) => x.c.team === m.ride.team);
    if (!w?.pose || !Number.isFinite(w.pose.height)) return;
    const at = seatAt(w.pose, m.ride.seat), a = m.actor;
    a.path = null; a.e = at.e; a.n = at.n; a.standY = at.y;
    a.heading = (w.pose.heading + (Number.isFinite(m.ride.heading) ? m.ride.heading : 0) + 360) % 360;
    a.place?.();
  }

  function faceOf(m, b) {
    const to = typeof b.face === 'string' ? cast.find((x) => x.c.person === b.face || x.c.extra === b.face)?.actor : pt(b.face);
    return to ? bearing(to.e - m.actor.e, to.n - m.actor.n) : null;
  }

  function play(m, b) {
    const a = m.actor;
    const to = pt(b.place);
    if (to) { a.path = null; a.e = to.e; a.n = to.n; a.standY = null; if (Number.isFinite(b.heading) && !Array.isArray(b.walk)) a.heading = b.heading; a.place?.(); }
    if (b.show) a.setIndoors?.(false);
    if (Array.isArray(b.walk)) {
      const pts = [{ e: a.e, n: a.n }, ...b.walk.map(pt).filter(Boolean)];
      const speed = Number.isFinite(b.pace) ? b.pace : PACES[b.pace] ?? null;
      if (a.posture) a.setPosture?.('stand', { seconds: 0 });
      a.walkPath?.(pts, { speed, endHeading: Number.isFinite(b.heading) ? b.heading : null, onArrive: () => { if (m.hideAtEnd) a.setIndoors?.(true); } });
      m.hideAtEnd = !!b.hide;
    } else {
      if (b.face != null) { const h = faceOf(m, b); if (h !== null) a.turnTo?.(h); }
      else if (Number.isFinite(b.heading)) a.turnTo?.(b.heading);
      if (b.hide) a.setIndoors?.(true);
    }
    if (b.pose) a.setPosture?.(b.pose, { seconds: Number.isFinite(b.ease) ? b.ease : 0.9 });
    if (typeof b.talk === 'boolean') a.actions?.setTalk?.(b.talk);
    if (b.greet) a.actions?.greet?.();
    if (b.arm) arm(m, b.arm);
    // A motion is begun on the hands once they are there (a figure still loading takes it then).
    if (b.act) { if (a.actions?.act) { a.actions.wield?.(m.arm); a.actions.act(b.act); } else m.pendingAct = b.act; }
  }

  const api = {
    get ids() { return stageIds(stop); },
    get playing() { return playing; },
    get clock() { return clock; },
    get cast() { return cast.map((m) => m.actor); },
    sync(next, { arrived = false } = {}) {
      const key = next?.stage?.cast?.length ? String(next.id ?? '') : null;
      if (!key) { if (stop) teardown(); stopKey = null; return api; }
      if (key !== stopKey || !stop) { stopKey = key; build(next); }
      if (arrived && !playing) { playing = true; clock = 0; }
      return api;
    },
    replay() {
      if (!stop) return false;
      const again = stop;
      build(again);
      playing = true; clock = 0;
      return true;
    },
    release() { teardown(); stopKey = null; },
    update(dt) {
      if (!cast.length && !wagons.length) return;
      const step = Number.isFinite(dt) && dt > 0 ? dt : 0;
      const shown = humans?.shown !== false;
      if (playing) {
        clock += step;
        for (const m of cast) {
          while (m.next < m.beats.length && m.beats[m.next].t <= clock) play(m, m.beats[m.next++]);
        }
      }
      driveTeams(step);
      const at = eye();
      for (const m of cast) {
        if (m.ride) seatRider(m);
        if (!shown) { m.actor.root.visible = false; if (m.weapon) m.weapon.visible = false; continue; }
        if (at) m.actor.update(step, at, step);
        wieldFrame(m);
      }
      fx?.update(step);
    },
    snapshot() {
      return { stop: stopKey, playing, clock: +clock.toFixed(2), cast: cast.map((m) => ({ person: m.c.person ?? null, extra: m.c.extra ?? null,
        e: +m.actor.e.toFixed(2), n: +m.actor.n.toFixed(2), heading: +m.actor.heading.toFixed(1), posture: m.actor.posture?.kind ?? 'stand',
        hidden: !!m.actor.indoors, drawn: !!m.actor.root.visible, lod: m.actor.lod, ...(m.ride ? { ride: m.ride.team } : {}),
        ...(m.arm && m.arm !== 'none' ? { arm: m.arm, armed: !!m.weapon?.visible, act: m.actor.actions?.fight?.act ?? null } : {}) })),
        smoke: fx?.count ?? 0,
        teams: wagons.map((w) => ({ team: w.c.team, taken: !!w.actor, e: w.pose ? +w.pose.e.toFixed(2) : null,
          n: w.pose ? +w.pose.n.toFixed(2) : null, heading: w.pose ? +w.pose.heading.toFixed(1) : null })) };
    },
  };
  return api;
}
