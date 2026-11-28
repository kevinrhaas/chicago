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
 * Watch again plays it from the beginning. A castmate who `mount`s is on a saddle horse
 * (Kevin, 2026-11-17: "maybe during the battle of fort Dearborn they would have had horses"):
 * the horse goes where the castmate's own walks take them, at their pace (a gallop where they
 * hurry), with them seated in the saddle and their coat laid over it (riding.js stageHorse,
 * handed in as `horses`), until a `dismount` beat sets them down on its near side and the horse
 * stands. With no horses handed in, they walk their way on foot. A stage may also take the town's horse teams
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
 * And what the blows do: a `wound` beat (body, head, neck, shoulder, scalp) on the one hit, at
 * the moment it lands, throws the blood, stains the body there and, once they are down, pools
 * under them (human-blood.js, handed in as `blood`). The compiler refuses `wound` outside an
 * adults jaunt too, and the gate refuses one on a child.
 *
 * And the burning of the fort (the owner, 2026-11-16: "witness and also join the party and help
 * light Fort Dearborn on fire"): a stop's `fire` names the buildings that burn (`burns`) and any
 * that stand through it (`stands`, smoked); a castmate takes up a firebrand (`torch` beat) and
 * puts it to a building (`ignite`: the structure id), where the fire catches as the torch
 * touches it; the heat carries to the buildings near it; and where `fire.visitor` is set the
 * visitor holds a torch too and may put it to the nearest building (`kindle`). The fire, its
 * smoke and the buildings' burning down are fort-fire.js's, handed in as `fire`. Burning
 * empty buildings is not a blow: students see it as adults do.
 *
 *   sync(stop, { arrived })  build `stop`'s stage (or keep it), and play it once arrived
 *   replay()                 from the beginning again
 *   release()                take every staged figure away
 *   update(dt)               one frame
 *   kindle(at)               the visitor's torch, put to the nearest building of the fire
 *   ids                      the person ids the stage plays now
 *   pick(raycaster)          T-3553: the castmate a ray from the eye meets first, or null
 *   meet(hit, visitor)       T-3553: one the visitor picked turns to them and greets, if free to
 *
 * Doors (the owner, 2026-11-16: "people appear outside doors the doors don't open and close ... they
 * vanish through the door"): a castmate whose walk ends at a door that is hung to swing
 * (house-doors.js passages, handed in as `doors`) walks on through it, and the door opens before
 * them and shuts behind them; one shown at such a door comes out of it, the door opening first.
 * A stage's `open_gates` (fort-gates.js ids, `<structure>:<side>`) stand open while it plays,
 * through `gates.open(ids)`, which gives back how to shut them again.
 * A `cross` beat seats a castmate in a drawn boat that crosses on its own (`boats.carry(id)`,
 * crossings.js), and they stand up on the far bank; a `borne` beat lays the dead on a bier
 * (`bier()`, stage-props.js) carried at the hands of the castmates named, front pair first, and
 * `borne: false` sets it down. Both are laid back or taken away when the stop is let go.
 *
 * The Great Fire (T-3814; the owner, 2026-11-27: "crowds running around existing buildings carrying
 * things or dumping things into wagons"): a castmate may `carry` a thing (goods, stage-props.js
 * GOODS: a bundle on the shoulder, a bolt of cloth, a bird cage or a basket in the hand, a feather
 * bed on the back, a trunk dragged on a cord), from the start or from a beat (`carry` a kind, or
 * null to put it down: it is gone, into the wagon or the house); the arm holds it (human-actions.js
 * setCarry). One borne (`borne`) with `bier: "mattress"` is carried in a doubled mattress, not on a
 * bier. A stage team may carry a `load` on its bed, and a stage's `props` stand on the ground
 * (chairs, trunks, bundles), all handed in as `goods`.
 *
 * The owner, 2026-11-16: "make sure there are interactive people". A castmate is picked as anyone
 * of the town is: a person opens their own card, an unnamed figure says who it stands for. One
 * standing free (not posed, armed, walking or talking) turns to the visitor and greets them; the
 * scene's next beat takes them on as written.
 */

/**
 * A beat's `pace`, m/s (`walk`: the figure's own). T-3553 (the owner, 2026-11-16: "make sure they
 * can run accurately ... there may be different speeds"): past about 2 m/s the people layer's
 * gait runs (human-gait.js), so `hurry` is the slowest jog; `jog`, `run` and `flee` are the
 * running dataset's own speeds (2.5-4.5 m/s, rounded), and `sprint` a flat-out dash past them.
 */
/** T-3560: how far from the horse's spine a castmate who gets down stands, on its near side. */
export const DISMOUNT_M = 1.0;
/** ... and how fast a ridden horse turns to a new heading, degrees a second. */
export const HORSE_TURN_DEG_S = 90;
export const PACES = Object.freeze({ walk: null, brisk: 1.75, hurry: 2.2, slow: 0.9, jog: 2.6, run: 3.6, flee: 4.5, sprint: 5.6 });
export const POSES = Object.freeze(['stand', 'kneel', 'kneel2', 'crouch', 'sit', 'prone', 'lie', 'fallen']);
/** How far beyond the people layer's animation range a posed figure keeps its pose drawn. */
export const STAGE_ANIMATE_M = 160;
/** T-3553: a stand with a run beginning within this many seconds of it is a spring up into the run. */
export const SPRING_S = 6;
/** A walk's end (or a figure shown) this near a hung door's way goes through that door. */
export const DOOR_NEAR_M = 1.8;
/** The door stands open while its castmate is this near its leaf, outside. */
export const DOOR_HOLD_M = 3.0;
/** One coming out waits this long at most for the door to open. */
const EMERGE_WAIT_S = 1.6;
/** A castmate in a boat: from the seat's eye point (crossings.js) down to where their feet go. */
const SEAT_EYE_TO_FEET_M = 0.92;
/** A bier carried at the bearers' hands, and set down on the ground; half a body's length. */
export const BIER_Y = 0.8;
const BIER_DOWN_Y = 0.1, BODY_HALF_M = 0.86;
/** T-3814: the cord a trunk is dragged on, hand to handle (m). */
export const CORD_M = 1.3;
/** T-3814: a team's load stands on its bed: the farm-box wagon's bed top (vehicle-local metres:
 *  the planks' top 0.955 m, the bed's middle a little behind the seat; loops.json passenger_basis). */
export const LOAD_SEAT = Object.freeze([0, 0.955, 0]);

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
    arm: c.arm ?? 'none', act: null, mounted: !!c.mount, horse: null, speed: 0, carry: typeof c.carry === 'string' ? c.carry : null };
  for (const b of sortedBeats(c)) {
    if (b.t > t) break;
    const to = pt(b.place);
    if (to) { s.e = to.e; s.n = to.n; }
    if (b.dismount && s.mounted) {
      // T-3560: down on the horse's near (left) side; the horse stands where it is.
      s.mounted = false; s.horse = { e: s.e, n: s.n, heading: s.heading };
      const h = ((s.heading - 90) * Math.PI) / 180;
      s.e += Math.sin(h) * DISMOUNT_M; s.n += Math.cos(h) * DISMOUNT_M;
    }
    if (to || b.dismount) s.speed = 0;
    if (Array.isArray(b.walk)) {
      s.speed = 0;
      const way = [{ e: s.e, n: s.n }, ...b.walk.map(pt).filter(Boolean)];
      const speed = Number.isFinite(b.pace) ? b.pace : PACES[b.pace] ?? walkSpeed;
      let left = Math.max(0, t - b.t) * speed;
      for (let i = 0; i < way.length - 1; i++) {
        const a = way[i], z = way[i + 1], len = Math.hypot(z.e - a.e, z.n - a.n);
        if (len > 1e-9) s.heading = bearing(z.e - a.e, z.n - a.n);
        if (left >= len) { s.e = z.e; s.n = z.n; left -= len; continue; }
        s.e = a.e + ((z.e - a.e) * left) / len; s.n = a.n + ((z.n - a.n) * left) / len; left = 0; s.speed = speed; break;
      }
      if (Number.isFinite(b.heading) && left > 0) s.heading = b.heading;
    } else if (Number.isFinite(b.heading)) s.heading = b.heading;
    if (b.pose) s.pose = b.pose;
    if (b.hide) s.hidden = true;
    if (b.show) s.hidden = false;
    if (typeof b.talk === 'boolean') s.talk = b.talk;
    if (b.arm) s.arm = b.arm;
    if (b.act) s.act = { act: b.act, t: b.t };
    if (b.carry !== undefined) s.carry = typeof b.carry === 'string' ? b.carry : null;
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
export function createJauntStage({ humans, parent = null, resolve = () => null, tier = () => 'full', eye = () => null, teams = null, fight = null, blood = null, fire = null, view = () => null,
  doors = () => null, gates = null, boats = null, bier = null, horses = null, goods = null } = {}) {
  let stopKey = null, stop = null, cast = [], clock = 0, playing = false;
  // T-3553: the hung doors' ways (house-doors.js passages), read once a build; the gates a stage opened.
  let ways = new Map(), shutGates = null;
  // T-3553: the boats castmates crossed in (crossings.js carry handles), laid back on their
  // banks when the stop is let go or watched again; and the biers the dead are carried on.
  let crossed = [], biers = [];
  // T-3814: the stage's still things (props on the ground, the teams' loads), let go with it.
  let stills = [];
  // The burning of the fort (fort-fire.js createFortFire): made the first time a stop has a `fire`.
  let burn = null;
  // Adults jaunts: the guns' flash and smoke (human-fight.js createFightFx), made once.
  const fx = fight?.createFightFx && parent ? fight.createFightFx(parent) : null;
  // ... and their blood (human-blood.js createBloodFx), made once too.
  const gore = blood?.createBloodFx && parent ? blood.createBloodFx(parent) : null;
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

  /** The hung doors, each with its way: [{ p, w }] (w: outside to in, `door` before the leaf). */
  function doorWays() {
    const out = [];
    for (const p of doors?.()?.passages ?? []) {
      if (!ways.has(p.id)) { let w = null; try { w = p.way?.() ?? null; } catch { w = null; } ways.set(p.id, w); }
      const w = ways.get(p.id);
      if (w?.length >= 2 && w.leaf && Number.isInteger(w.door)) out.push({ p, w });
    }
    return out;
  }
  /** The hung door whose way (its foot, the place before its leaf, the leaf) is nearest (e, n),
   *  within DOOR_NEAR_M, or null. */
  function doorAt(e, n) {
    let best = null;
    for (const x of doorWays()) {
      const d = Math.min(...[x.w[0], x.w[x.w.door], x.w.leaf].map((q) => Math.hypot(q.e - e, q.n - n)));
      if (d <= DOOR_NEAR_M && (!best || d < best.d)) best = { ...x, d };
    }
    return best;
  }
  const doorKey = (m) => `jaunt-stage:${stopKey}:${cast.indexOf(m)}`;
  /** A castmate done with their door lets it go. */
  function leaveDoor(m) { if (m.door) { m.door.p.release?.(doorKey(m)); m.door = null; } }
  /** Out of a door: shown once it is open (or after EMERGE_WAIT_S), walking out by its way, then
   *  on to where the scene has them (or the walk that came while they waited). */
  function emerge(m) {
    const a = m.actor, x = m.emerging, w = x.w;
    m.emerging = null;
    a.setIndoors?.(false);
    const out = w.slice(w.door).reverse().map((q) => ({ e: q.e, n: q.n }));
    const b = x.queued;
    const on = b ? b.walk.map(pt).filter(Boolean) : Math.hypot(x.to.e - out.at(-1).e, x.to.n - out.at(-1).n) > 0.3 ? [x.to] : [];
    const speed = b && Number.isFinite(b.pace) ? b.pace : PACES[b?.pace] ?? null;
    const end = b ? (Number.isFinite(b.heading) ? b.heading : null) : x.heading;
    a.walkPath?.([...out, ...on], { speed, endHeading: end, onArrive: () => { if (m.hideAtEnd) a.setIndoors?.(true); } });
    m.hideAtEnd = !!b?.hide;
    m.door = { p: x.p, leaf: w.leaf, until: -Infinity };
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
      // A torch burns at its head.
      if (frame && m.arm === 'torch' && burn?.active && m.weapon.userData.tip) {
        m.weapon.updateMatrixWorld(true);
        tipAt ??= m.weapon.position.clone();
        burn.flameNow(m.weapon.userData.tip.getWorldPosition(tipAt), { w: 0.34, h: 0.62, heat: 1, seed: m.seed ?? 1 });
      }
    }
    const shots = actions.takeShot?.() ?? 0;
    if (shots && m.weapon && fx) { const z = fight.muzzleOf(m.weapon); if (z) for (let i = 0; i < shots; i++) fx.shoot(z.at, z.dir); }
  }

  let tipAt = null; // (this module imports nothing: vectors are the figures' own kind, cloned)
  /** Where `m` puts their torch: its head, or before them at a hand's height. */
  function torchPoint(m) {
    if (m.weapon?.visible && m.weapon.userData.tip) { m.weapon.updateMatrixWorld(true); return m.weapon.userData.tip.getWorldPosition(m.weapon.position.clone()); }
    const r = m.actor.root.position, h = (m.actor.heading ?? 0) * Math.PI / 180;
    return r.clone().set(r.x + Math.sin(h) * 0.7, r.y + 1.0, r.z - Math.cos(h) * 0.7);
  }

  /** Where the blow that wounds `m` came from: the nearest castmate with a weapon in hand. */
  function woundFrom(m) {
    let best = null, far = Infinity;
    for (const x of cast) {
      if (x === m || !x.arm || x.arm === 'none') continue;
      const d = Math.hypot(x.actor.e - m.actor.e, x.actor.n - m.actor.n);
      if (d < far) { far = d; best = x; }
    }
    return best && far < 60 ? best.actor.root.position.clone() : null;
  }

  /** `m` is hit: its blood, now if its figure is drawn, else once it is. */
  function wound(m, kind) {
    if (!gore) return;
    if (m.actor.body && m.actor.root.visible) gore.wound(m.actor, kind, { from: woundFrom(m) });
    else (m.pendingWounds ??= []).push(kind);
  }

  function build(next, again = false) {
    teardown(again);
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
      const m = { c, actor, beats: sortedBeats(c), next: 0, seed: (i * 7.31) % 97 };
      if (c.ride && typeof c.ride.team === 'string' && Array.isArray(c.ride.seat) && c.ride.seat.length === 3) {
        m.ride = c.ride;
        actor.setPosture?.(c.pose ?? 'sit', { seconds: 0 });
      }
      if (c.mount && typeof c.mount.horse === 'string' && horses?.create) m.mount = { spec: c.mount, handle: null, loading: false, seating: false, failed: false, heading: null, face: null };
      begin(c, actor);
      arm(m, castAt(c, 0).arm);
      take(m, castAt(c, 0).carry);
      cast.push(m);
    });
    wagons = teamsFor(next).map((c) => ({ c, actor: null, heading: castAt(c, 0).heading, pose: null, load: still(c.load) }));
    for (const p of Array.isArray(next.stage?.props) ? next.stage.props : []) {
      const g = pt(p?.at) ? still(p.kind) : null;
      if (!g) continue;
      const at = pt(p.at), h = ((Number.isFinite(p.heading) ? p.heading : 0) * Math.PI) / 180;
      g.position.set(at.e, groundAt(at.e, at.n) + (Number.isFinite(p.y) ? p.y : 0), -at.n);
      g.rotation.set(0, Math.PI - h, 0);
      g.userData.groundAt = at;
    }
    const open = Array.isArray(next.stage?.open_gates) ? next.stage.open_gates.filter((id) => typeof id === 'string') : [];
    if (open.length && gates?.open) { try { shutGates = gates.open(open); } catch { shutGates = null; } }
    askedLoad = -Infinity;
    if (next.stage?.fire && fire?.create) {
      try { burn ??= fire.create(); burn.start(next.stage.fire, { camera: view() }); } catch { burn = null; }
    }
  }

  /** Let the stage go. A boat crossed in is left on the bank it was going to (the story goes on
   *  from there), or laid back where it set out when the stop is watched `again`. */
  function teardown(again = false) {
    for (const m of cast) {
      leaveDoor(m); if (m.emerging) m.emerging.p.release?.(doorKey(m)); m.weapon?.removeFromParent?.();
      if (m.mount) { m.mount.gone = true; try { m.mount.handle?.dispose(); } catch { /* gone already */ } }
      try { m.actor.dispose(); } catch { /* gone already */ }
    }
    ways = new Map();
    for (const h of crossed) { try { if (again) h.restore(); else h.settle?.(); } catch { /* gone already */ } }
    crossed = [];
    for (const b of biers) b.removeFromParent?.();
    biers = [];
    for (const m of cast) { m.goods?.removeFromParent?.(); m.cord?.removeFromParent?.(); }
    for (const g of stills) g.removeFromParent?.();
    stills = [];
    try { shutGates?.(); } catch { /* gone already */ }
    shutGates = null;
    fx?.clear();
    gore?.clear();
    burn?.clear();
    for (const w of wagons) { try { w.actor?.unstage?.(); } catch { /* gone already */ } try { teams?.release?.(w.c.team); } catch { /* gone already */ } }
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
    if (missing && now - askedLoad >= 2000) { askedLoad = now; try { teams?.load?.(wagons.filter((w) => !w.actor).map((w) => w.c.team)); } catch { /* asked again later */ } }
  }

  /**
   * T-3560: a castmate on a saddle horse. The horse is asked for once; until it comes the
   * castmate walks their way on foot. Up, the horse goes where the castmate's beats have them
   * (castAt: the same place a late arrival or a replay finds), turning at a horse's rate, with
   * the castmate seated; at their `dismount` they are stood beside it and walk on from there.
   * Returns whether the castmate's own figure is held by the horse this frame.
   */
  function mountFrame(m, step, shown, eyeAt) {
    const M = m.mount, a = m.actor;
    // Asked again every two seconds of the page's own time while the riding layer is not up.
    if (!M.handle && !M.loading && !M.failed && Date.now() >= (M.askAt ?? 0)) {
      M.loading = true; M.askAt = Date.now() + 2000;
      Promise.resolve(horses.create({ id: `${stopKey}:${m.c.person ?? m.c.extra}`, coat_row: M.spec.horse, tack: M.spec.tack ?? null }))
        .then((h) => { if (M.gone) h?.dispose?.(); else if (h) M.handle = h; }, () => { M.failed = true; })
        .finally(() => { M.loading = false; });
    }
    const h = M.handle;
    if (!h) return false;
    h.visible = shown;
    const s = castAt(m.c, clock);
    if (s.mounted) {
      const want = M.face ?? s.heading;
      M.heading ??= s.heading;
      const d = ((want - M.heading + 540) % 360) - 180, most = HORSE_TURN_DEG_S * step;
      M.heading = (M.heading + Math.max(-most, Math.min(most, d)) + 360) % 360;
      h.move({ e: s.e, n: s.n, bearing: M.heading, speed: s.speed, eye: eyeAt }, step);
      if (!h.seated && !M.seating && !M.failed) {
        M.seating = true;
        h.seat(a, { asset: a.instance?.appearance?.asset_id }).catch(() => { M.failed = true; }).finally(() => { M.seating = false; });
      }
      if (!h.seated) return false;
      a.path = null; a.e = s.e; a.n = s.n; a.heading = M.heading;
      return true;
    }
    if (h.seated) {
      h.unseat(parent);
      a.path = null; a.e = s.e; a.n = s.n; a.heading = s.heading; a.standY = null; a.place?.();
    }
    const at = s.horse ?? { e: s.e, n: s.n, heading: s.heading };
    h.move({ e: at.e, n: at.n, bearing: M.heading ?? at.heading, speed: 0, eye: eyeAt }, step);
    return false;
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

  /** The dead carried on a bier by the castmates `by` (two in front, two behind), or set down. */
  function bear(m, by) {
    if (by === false) { if (m.borne) { m.borne.lifted = false; m.borne.since = clock; } return; }
    const list = by.map((id) => cast.find((x) => x.c.person === id || x.c.extra === id)).filter(Boolean);
    if (list.length < 2) return;
    let prop = m.borne?.prop ?? null;
    // T-3814: a sick man or woman "half concealed in a mattress doubled up and borne by two men".
    const make = m.c.bier === 'mattress' && goods?.mattress ? goods.mattress : bier;
    if (!prop && make) { try { prop = make(); parent?.add?.(prop); biers.push(prop); } catch { prop = null; } }
    m.borne = { by: list, lifted: true, since: clock, y: BIER_Y, heading: m.actor.heading, e: m.actor.e, n: m.actor.n, prop };
    m.actor.path = null;
  }
  function carryFrame(m, step) {
    const a = m.actor, k = m.borne;
    if (k.lifted) {
      const half = Math.ceil(k.by.length / 2), mean = (xs) => xs.reduce((s, x) => s + x, 0) / xs.length;
      const front = k.by.slice(0, half).map((x) => x.actor), rear = k.by.slice(half).map((x) => x.actor);
      const fe = mean(front.map((x) => x.e)), fn = mean(front.map((x) => x.n)), re = mean(rear.map((x) => x.e)), rn = mean(rear.map((x) => x.n));
      if (Math.hypot(fe - re, fn - rn) > 0.3) k.heading = bearing(fe - re, fn - rn);
      k.e = (fe + re) / 2; k.n = (fn + rn) / 2;
      k.y = Math.min(BIER_Y, k.y + step * 0.8);
    } else k.y = Math.max(BIER_DOWN_Y, k.y - step * 0.6);
    const h = (k.heading * Math.PI) / 180, ground = a.heightAt?.(k.e, k.n) ?? 0;
    // Lying, a figure is tipped about its feet with its head to its heading: the feet go behind.
    a.path = null; a.heading = k.heading; a.e = k.e - Math.sin(h) * BODY_HALF_M; a.n = k.n - Math.cos(h) * BODY_HALF_M;
    a.standY = ground + k.y; a.place?.();
    if (k.prop) {
      // T-3814: the bier or mattress only once the one on it is drawn (never an empty mattress
      // going along the street while the figures load).
      k.prop.visible = !!a.body && !a.indoors && humans?.shown !== false;
      k.prop.position.set(k.e, ground + k.y - 0.02, -k.n); k.prop.rotation.set(0, Math.PI - h, 0);
    }
  }
  function boatFrame(m) {
    const a = m.actor, h = m.boat;
    if (h.done) { const [e, n] = h.stand(); a.e = e; a.n = n; a.standY = null; m.boat = null; a.setPosture?.('stand', { seconds: 0.6 }); a.place?.(); return; }
    const s = h.seat();
    a.path = null; a.e = s.e; a.n = s.n; a.heading = s.bearing; a.standY = s.y - SEAT_EYE_TO_FEET_M; a.place?.();
  }

  function play(m, b) {
    const a = m.actor;
    const to = pt(b.place);
    if (to && m.boat) { m.boat = null; a.setPosture?.('stand', { seconds: 0 }); }
    if (typeof b.cross === 'string') {
      // Into a drawn boat and across in it (crossings.js), sitting; with no boat drawn, gone
      // from sight as before. The beat after it places them on the far bank.
      const h = boats?.carry?.(b.cross, { near: [a.e, a.n] }) ?? null;
      // T-3754: the walk down to it ends here: still 'walking', the walk clip and the gait layer
      // stayed on under the seated legs and took the body down through the hull.
      if (h) { crossed.push(h); m.boat = h; a.path = null; if (a.state === 'walking') a.setState?.('standing'); a.setIndoors?.(false); a.setPosture?.('sit', { seconds: 0.8 }); }
      else a.setIndoors?.(true);
    }
    if (Array.isArray(b.borne) || b.borne === false) bear(m, b.borne);
    if (to) { a.path = null; a.e = to.e; a.n = to.n; a.standY = null; if (Number.isFinite(b.heading) && !Array.isArray(b.walk)) a.heading = b.heading; a.place?.(); }
    if (b.show) {
      // Shown at a hung door: they come out of it, once it has opened.
      const door = a.indoors ? doorAt(a.e, a.n) : null;
      if (door) {
        leaveDoor(m);
        m.emerging = { p: door.p, w: door.w, to: { e: a.e, n: a.n }, heading: Number.isFinite(b.heading) ? b.heading : a.heading, since: clock, queued: null };
        const inner = door.w.at(-1);
        a.path = null; a.e = inner.e; a.n = inner.n; a.standY = null; a.place?.();
        door.p.hold?.(doorKey(m));
      } else a.setIndoors?.(false);
    }
    if (Array.isArray(b.walk) && m.emerging) {
      m.emerging.queued = b;                 // taken up as they come out
    } else if (Array.isArray(b.walk)) {
      const pts = [{ e: a.e, n: a.n }, ...b.walk.map(pt).filter(Boolean)];
      // Still in a doorway they came out of: out by its way first.
      if (m.door && Math.hypot(a.e - m.door.leaf.e, a.n - m.door.leaf.n) < 1.2) {
        const w = ways.get(m.door.p.id);
        if (w) pts.splice(1, 0, { e: w[w.door].e, n: w[w.door].n });
      }
      // Into a hung door: on through it, the door opening before them (update()).
      const door = b.hide ? doorAt(pts.at(-1).e, pts.at(-1).n) : null;
      if (door) {
        leaveDoor(m);
        for (const q of door.w.slice(door.w.door)) pts.push({ e: q.e, n: q.n });
        m.door = { p: door.p, leaf: door.w.leaf, until: Infinity };
      }
      const speed = Number.isFinite(b.pace) ? b.pace : PACES[b.pace] ?? null;
      // (One getting up off the ground runs once up: humans.js holds the walk for it.)
      if (a.posture && !a.rising) a.setPosture?.('stand', { seconds: 0 });
      a.walkPath?.(pts, { speed, endHeading: Number.isFinite(b.heading) ? b.heading : null, onArrive: () => {
        if (!m.hideAtEnd) return;
        a.setIndoors?.(true);
        if (m.door) m.door.until = clock + 0.4;
      } });
      m.hideAtEnd = !!b.hide;
    } else {
      if (b.face != null) { const h = faceOf(m, b); if (h !== null) a.turnTo?.(h); }
      else if (Number.isFinite(b.heading)) a.turnTo?.(b.heading);
      if (b.hide) a.setIndoors?.(true);
    }
    // T-3553: up off the ground into a run that follows at once (a walk at a jog or faster within
    // SPRING_S): driven up leaning into the stride, not stood up and then set off (human-motions.js).
    const spring = b.pose === 'stand' && m.beats.some((x) => x !== b && x.t >= b.t && x.t - b.t <= SPRING_S && Array.isArray(x.walk)
      && (Number.isFinite(x.pace) ? x.pace : PACES[x.pace] ?? 0) >= PACES.jog);
    if (b.pose) a.setPosture?.(b.pose, { seconds: Number.isFinite(b.ease) ? b.ease : 0.9, spring });
    if (typeof b.talk === 'boolean') a.actions?.setTalk?.(b.talk);
    if (b.greet) a.actions?.greet?.();
    if (b.arm) arm(m, b.arm);
    // The burning of the fort: a torch taken up or thrown down, and put to a building.
    if (b.torch === true) arm(m, 'torch');
    if (b.torch === false) arm(m, 'none');
    if (typeof b.ignite === 'string') {
      if (a.actions?.act) { a.actions.wield?.(m.arm); a.actions.act('kindle'); } else m.pendingAct = 'kindle';
      m.pendingIgnite = { id: b.ignite, at: b.t + (fight?.MOTIONS?.kindle?.hit ?? 0.6) };
    }
    // A motion is begun on the hands once they are there (a figure still loading takes it then).
    if (b.act) { if (a.actions?.act) { a.actions.wield?.(m.arm); a.actions.act(b.act); } else m.pendingAct = b.act; }
    if (b.wound) wound(m, b.wound);
    if (b.carry !== undefined) take(m, typeof b.carry === 'string' ? b.carry : null);
  }

  /** T-3814: the ground's height at (e, n), as the figures stand on it. */
  function groundAt(e, n, a = null) {
    const f = a?.heightAt ?? humans?.heightAt ?? cast.find((x) => x.actor.heightAt)?.actor.heightAt;
    try { return f ? f.call(a ?? null, e, n) : 0; } catch { return 0; }
  }

  /** T-3814: a still thing (a ground prop or a team's load) of `kind`, added to the stage, or null. */
  function still(kind) {
    if (typeof kind !== 'string' || !goods?.create) return null;
    let g = null;
    try { g = goods.create(kind, { still: true }); } catch { g = null; }
    if (!g) return null;
    parent?.add?.(g); stills.push(g);
    return g;
  }

  /** T-3814: `m` takes up a thing of `kind` to carry (null: puts it down, out of sight). */
  function take(m, kind) {
    const spec = kind ? goods?.spec?.(kind) ?? null : null;
    if (m.goods) { m.goods.removeFromParent(); m.goods = null; }
    if (m.cord) { m.cord.removeFromParent(); m.cord = null; }
    m.load = spec ? { kind, spec } : null;
    if (spec && goods?.create) {
      try { m.goods = goods.create(kind); } catch { m.goods = null; }
      if (m.goods) { m.goods.visible = false; parent?.add?.(m.goods); }
      if (m.goods && spec.mode === 'drag' && goods.cord) { m.cord = goods.cord(); m.cord.visible = false; parent?.add?.(m.cord); }
      m.dragAt = null;
    }
    m.held = undefined; // the hold is told to the hands once they are there (goodsFrame)
  }

  /** T-3814: after the figure's frame, what it carries where its hand, shoulder or back is. */
  function goodsFrame(m) {
    const a = m.actor, want = m.load?.spec?.hold ?? null;
    if (a.actions?.setCarry && m.held !== want) { a.actions.setCarry(want); m.held = want; }
    const g = m.goods;
    if (!g) return;
    const mode = m.load.spec.mode;
    const down = !!a.posture?.kind?.match?.(/lie|prone|fallen/);
    const on = a.root.visible && !a.indoors && !!a.body && !(down && mode !== 'drag');
    g.visible = on;
    if (m.cord) m.cord.visible = false;
    if (!on) return;
    // Whoever dragged it lies down: it stays where it was let go, on the ground.
    if (down) { g.visible = !!m.dragAt; return; }
    const h = ((a.heading ?? 0) * Math.PI) / 180, yaw = Math.PI - h;
    const bone = (name) => {
      if (m.bonesOf !== a.body) { m.bonesOf = a.body; m.bones = {}; }
      if (!(name in m.bones)) m.bones[name] = a.body?.scene?.getObjectByName?.(name) ?? null;
      return m.bones[name];
    };
    const side = m.load.spec.hold?.side ?? 'r';
    if (mode === 'hand') {
      const f = a.actions?.gripFrame?.(side);
      if (!f) { g.visible = false; return; }
      g.position.copy(f.pos); g.rotation.set(0, yaw, 0);
    } else if (mode === 'shoulder' || mode === 'back') {
      const b = bone(mode === 'back' ? 'spine_03' : `upperarm_${side}`);
      if (!b) { g.visible = false; return; }
      b.getWorldPosition(g.position);
      g.rotation.set(0, yaw, 0);
      // The shoulder's top, over the joint; the back's middle, behind the spine.
      if (mode === 'shoulder') g.position.y += 0.05;
    } else if (mode === 'drag') {
      // Pulled along on its cord: it stays where it is until the cord is taut, then follows the
      // hand, its front toward it, on the ground.
      const f = a.actions?.gripFrame?.(side);
      if (!f) { g.visible = false; return; }
      const he = f.pos.x, hn = -f.pos.z;
      if (!m.dragAt) m.dragAt = { e: a.e - Math.sin(h) * CORD_M, n: a.n - Math.cos(h) * CORD_M, heading: a.heading };
      const d = m.dragAt, de = he - d.e, dn = hn - d.n, L = Math.hypot(de, dn);
      if (L > CORD_M) { d.e = he - (de / L) * CORD_M; d.n = hn - (dn / L) * CORD_M; d.heading = bearing(de, dn); }
      const ground = groundAt(d.e, d.n, a);
      const th = (d.heading * Math.PI) / 180;
      g.position.set(d.e, ground, -d.n); g.rotation.set(0, Math.PI - th, 0);
      if (m.cord) {
        // From the hand to the handle, 0.32 m up the trunk's front.
        const hx = d.e, hy = ground + 0.32, hz = -d.n;
        const dx = f.pos.x - hx, dy = f.pos.y - hy, dz = f.pos.z - hz, len = Math.hypot(dx, dy, dz);
        if (len > 0.05) {
          m.cord.visible = true;
          m.cord.position.set((f.pos.x + hx) / 2, (f.pos.y + hy) / 2, (f.pos.z + hz) / 2);
          m.cord.scale.set(0.012, len, 0.012);
          // The cylinder stands along +y: turn +y onto the cord.
          const ux = dx / len, uy = dy / len, uz = dz / len;
          m.cord.quaternion.set(uz, 0, -ux, 1 + uy).normalize();
          if (1 + uy < 1e-6) m.cord.quaternion.set(1, 0, 0, 0);
        }
      }
    }
  }

  /** T-3814: a team's load on its bed, where the bed is now. */
  function loadFrame(w) {
    const g = w.load;
    if (!g) return;
    g.visible = !!w.pose && Number.isFinite(w.pose.height) && humans?.shown !== false;
    if (!g.visible) return;
    const at = seatAt(w.pose, LOAD_SEAT);
    g.position.set(at.e, at.y, -at.n);
    g.rotation.set(0, Math.PI - (w.pose.heading * Math.PI) / 180, 0);
  }

  const api = {
    pick(raycaster) {
      if (!raycaster || humans?.shown === false) return null;
      const proxies = cast.filter((m) => m.actor.root.visible && m.actor.body && !m.actor.indoors && m.actor.proxy).map((m) => m.actor.proxy);
      if (!proxies.length) return null;
      parent?.updateMatrixWorld?.(true);
      const hit = raycaster.intersectObjects(proxies, false)[0];
      const m = hit && cast.find((x) => x.actor.proxy === hit.object);
      if (!m) return null;
      return { actor: m.actor, personId: m.c.person ?? null, person: m.actor.person ?? null,
        name: m.c.person ? (m.actor.person?.name ?? null) : (m.c.name ?? 'An unnamed figure'), about: m.c.person ? null : (m.c.about ?? null),
        distance: hit.distance, point: hit.point };
    },
    meet(hit, visitor = null) {
      const m = cast.find((x) => x.actor === hit?.actor);
      if (!m) return false;
      const a = m.actor;
      const free = (a.posture?.kind ?? 'stand') === 'stand' && !a.path && !m.ride && !m.mount?.handle?.seated && (!m.arm || m.arm === 'none') && !a.actions?.talking;
      if (!free) return false;
      if (visitor && Number.isFinite(visitor.e)) a.turnTo?.(bearing(visitor.e - a.e, visitor.n - a.n));
      a.actions?.greet?.();
      return true;
    },
    get ids() { return stageIds(stop); },
    get playing() { return playing; },
    /** T-3753: how many of the cast are still being drawn (asked for, no figure yet): the stop's
     *  scene is loading while any are, and the key that brought the visitor spins. */
    get loading() { let n = 0; for (const m of cast) if (!m.actor.disposed && !m.actor.body && (m.actor.pending || m.actor.inRange)) n++; return n; },
    get clock() { return clock; },
    /** The owner, 2026-11-16: how long the stage plays, to its last beat (the stop's meter). */
    get length() { let end = 0; for (const m of cast) for (const b of m.beats ?? []) if (Number.isFinite(b.t) && b.t > end) end = b.t; return end; },
    get cast() { return cast.map((m) => m.actor); },
    /** T-3614: the castmates the name cards name: a person by their own name, an extra by the cast's. */
    get named() {
      // An extra stands in no record of their own: reconstructed.
      return cast.map((m) => ({ key: m.actor.id, actor: m.actor, personId: m.c.person ?? null, staged: true,
        name: m.c.person ? (m.actor.person?.name ?? null) : (m.c.name ?? null),
        grade: m.c.person ? (m.actor.person?.grade ?? null) : 'reconstructed' }));
    },
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
      build(again, true);
      playing = true; clock = 0;
      return true;
    },
    release() { teardown(); stopKey = null; },
    /** The visitor puts their torch to the nearest building of the stop's fire within reach of
     *  `at` (world): { lit, name } or { none }; null where the stop has no fire for them. */
    kindle(at) {
      if (!burn?.active || !stop?.stage?.fire?.visitor || !playing || !at) return null;
      return burn.kindle(at);
    },
    get fire() { return burn?.active ? burn : null; },
    update(dt) {
      if (!cast.length && !wagons.length && !burn?.active) return;
      const step = Number.isFinite(dt) && dt > 0 ? dt : 0;
      const shown = humans?.shown !== false;
      if (playing) {
        clock += step;
        for (const m of cast) {
          while (m.next < m.beats.length && m.beats[m.next].t <= clock) {
            const b = m.beats[m.next++];
            // T-3560: on a horse, a beat that faces someone turns the horse; a walk ends it.
            if (m.mount) { if (Array.isArray(b.walk)) m.mount.face = null; else if (b.face != null) m.mount.face = faceOf(m, b) ?? m.mount.face; else if (Number.isFinite(b.heading)) m.mount.face = b.heading; }
            play(m, b);
          }
          if (m.pendingIgnite && clock >= m.pendingIgnite.at) { burn?.ignite(m.pendingIgnite.id, torchPoint(m)); m.pendingIgnite = null; }
        }
      }
      driveTeams(step);
      for (const w of wagons) loadFrame(w);
      // The doors: held open for whoever is coming out or going in, let go behind them.
      for (const m of cast) {
        if (m.emerging && (m.emerging.p.isOpen?.() || clock - m.emerging.since >= EMERGE_WAIT_S)) emerge(m);
        if (!m.door) continue;
        const a = m.actor, near = Math.hypot(a.e - m.door.leaf.e, a.n - m.door.leaf.n) < DOOR_HOLD_M;
        if (a.indoors ? clock >= m.door.until : !a.path) { leaveDoor(m); continue; }
        if (a.indoors ? clock < m.door.until : near) m.door.p.hold?.(doorKey(m));
        else m.door.p.release?.(doorKey(m));
      }
      for (const m of cast) {
        if (m.boat) boatFrame(m);
        if (m.borne) carryFrame(m, step);
      }
      const at = eye();
      for (const m of cast) {
        if (m.ride) seatRider(m);
        const up = m.mount ? mountFrame(m, step, shown, at) : false;
        if (!shown) { m.actor.root.visible = false; if (m.weapon) m.weapon.visible = false; if (m.goods) m.goods.visible = false; if (m.cord) m.cord.visible = false; continue; }
        if (up) { m.actor.root.visible = !m.actor.indoors; continue; }
        if (at) m.actor.update(step, at, step);
        wieldFrame(m);
        goodsFrame(m);
        if (m.pendingWounds && m.actor.body && m.actor.root.visible) { const due = m.pendingWounds; m.pendingWounds = null; for (const k of due) wound(m, k); }
      }
      for (const g of stills) if (!wagons.some((w) => w.load === g)) g.visible = shown;
      fx?.update(step);
      if (gore) { gore.visible = shown; gore.update(step); }
      if (burn?.active) { burn.holdTorch(!!stop?.stage?.fire?.visitor && playing); burn.update(playing ? step : 0, view()); }
    },
    snapshot() {
      return { stop: stopKey, playing, clock: +clock.toFixed(2), cast: cast.map((m) => ({ person: m.c.person ?? null, extra: m.c.extra ?? null,
        e: +m.actor.e.toFixed(2), n: +m.actor.n.toFixed(2), heading: +m.actor.heading.toFixed(1), posture: m.actor.posture?.kind ?? 'stand',
        hidden: !!m.actor.indoors, drawn: !!m.actor.root.visible, lod: m.actor.lod, ...(m.ride ? { ride: m.ride.team } : {}),
        ...(m.mount ? { mount: m.mount.handle ? (m.mount.handle.seated ? 'up' : 'down') : m.mount.failed ? 'failed' : 'coming' } : {}),
        ...(m.arm && m.arm !== 'none' ? { arm: m.arm, armed: !!m.weapon?.visible, act: m.actor.actions?.fight?.act ?? null } : {}),
        ...(m.load ? { carry: m.load.kind, carried: !!m.goods?.visible, held: m.actor.actions?.carrying ?? null } : {}) })),
        props: stills.length,
        smoke: fx?.count ?? 0,
        doors: cast.filter((m) => m.door || m.emerging).map((m) => ({ door: (m.door ?? m.emerging).p.id, swing: +((m.door ?? m.emerging).p.swing ?? 0).toFixed(2),
          who: m.c.person ?? m.c.extra, out: !!m.emerging })),
        ...(gore ? { blood: gore.counts } : {}),
        ...(burn?.active ? { fire: burn.snapshot() } : {}),
        teams: wagons.map((w) => ({ team: w.c.team, taken: !!w.actor, e: w.pose ? +w.pose.e.toFixed(2) : null,
          n: w.pose ? +w.pose.n.toFixed(2) : null, heading: w.pose ? +w.pose.heading.toFixed(1) : null, ...(w.c.load ? { load: w.c.load, loaded: !!w.load?.visible } : {}) })) };
    },
  };
  return api;
}
