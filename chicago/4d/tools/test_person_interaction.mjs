// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * test_person_interaction.mjs — T-3404: every person placed in town is interactive.
 *
 *   node tools/test_person_interaction.mjs
 *
 * Kevin, 2026-11-06: "making them fully available to interact with". Drives, with fakes:
 *   - follow.js: the stand right behind a person (T-3471), pulled in or swung round them at a
 *     wall, round a corner by their trail, set down when held on a wall; the
 *     intent written camera-relative and zeroed after the walker, a far person jumped to,
 *     a loading person waited for, and the visitor's own movement / a ride / a lost
 *     person ending it; the visitor's look holding the view;
 *   - people-look.js: the tag names a person nearer than the building behind them, the
 *     building otherwise, within its reach, and stops probing when nobody listens;
 *   - target-tag.js `tagName` for a person; transport-loop.js `heading_deg` against the
 *     driver Find's own yaw convention;
 *   - main.js goToTarget for a standing figure (beside them, facing them, router-guarded)
 *     and a card's "Go to where they lived" no longer diverted to the driver's seat;
 *   - person-card.js offers Follow only for someone placed in town.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createFollow, followStand, backOf, FOLLOW } from '../renderers/web/js/follow.js';
import { createPeopleLook } from '../renderers/web/js/people-look.js';
import { tagName } from '../renderers/web/js/target-tag.js';
import { createIntent } from '../renderers/web/js/controls/intent.js';
import { bearingToYaw } from '../renderers/web/js/angles.js';

const near = (a, b, eps = 1e-6) => Math.abs(a - b) <= eps;

// ---- follow.js -------------------------------------------------------------------------
// A walker that moves exactly as walker.js does: camera-relative, at the paces given, and
// (given `blocked`) stopped axis by axis at a wall the way walker.js tryStep is.
const mkWalker = (e, n, bearing = 0, { walk = { speed: 1.45, sprintSpeed: 3.4 }, blocked = () => false } = {}) => {
  const state = { e, n, yaw: bearingToYaw(bearing), pitch: 0, eyeY: 1.6, groundY: 0, flying: false };
  const w = { state, teleports: 0,
    teleport({ local_e, local_n, yaw_deg }) { w.teleports++; state.e = local_e; state.n = local_n; if (yaw_deg != null) state.yaw = bearingToYaw(yaw_deg); },
    update(dt, intent) {
      state.yaw += intent.yawDelta; state.pitch += intent.pitchDelta; intent.clearLook();
      let f = intent.forward, r = intent.strafe; const m = Math.hypot(f, r); if (m > 1) { f /= m; r /= m; }
      const sp = intent.sprint ? walk.sprintSpeed : walk.speed;
      const de = (-Math.sin(state.yaw) * f + Math.cos(state.yaw) * r) * sp * dt;
      const dn = (Math.cos(state.yaw) * f + Math.sin(state.yaw) * r) * sp * dt;
      if (!blocked(state.e + de, state.n)) state.e += de;
      if (!blocked(state.e, state.n + dn)) state.n += dn;
    } };
  return w;
};
const bearingOf = (from, to) => (Math.atan2(to.e - from.e, to.n - from.n) * 180 / Math.PI + 360) % 360;
const facingOf = (state) => ((-state.yaw * 180 / Math.PI) % 360 + 360) % 360;
const angleOff = (a, b) => Math.abs(((a - b + 540) % 360) - 180);

{
  // T-3471 (Kevin, 2026-11-07: "maybe when we follow we should go right behind them by
  // default instead of along side?"). On foot: BEHIND_M straight back along their way.
  const s = followStand({ e: 100, n: 50, heading_deg: 90 });
  assert(near(s.e, 100 - FOLLOW.BEHIND_M) && near(s.n, 50), `behind an eastbound person is west of them: ${JSON.stringify(s)}`);
  // Their way, not their facing, once they move.
  const back = backOf({ heading_deg: 90 }, 0, 1.4);
  assert(near(back.e, 0) && near(back.n, -1), 'walking north while facing east: behind is south');
  const still = backOf({ heading_deg: 90 }, 0.1, 0);
  assert(near(still.e, -1) && near(still.n, 0, 1e-9), 'standing: behind their back');
  // A driver: back past the carriage and off its line, right of an eastbound one is south.
  const d = followStand({ e: 0, n: 0, heading_deg: 90, driver: {} }, { side: 1 });
  assert(near(d.e, -FOLLOW.DRIVER_BEHIND_M) && near(d.n, -FOLLOW.DRIVER_SIDE_M), `behind a driver, off the carriage's line: ${JSON.stringify(d)}`);

  const walk = { speed: 1.45, sprintSpeed: 3.4 };
  let person = { e: 0, n: 0, heading_deg: 90, head_y: 1.62, name: 'Frances M. Glessner' };
  const walker = mkWalker(-1, -6, 0, { walk });
  const events = [];
  let riding = false;
  let blocked = () => false;
  const follow = createFollow({ walker, walk, locate: (id) => (id === 'frances' ? person : null),
    blockedAt: (e, n) => blocked(e, n), busy: () => riding, onChange: (st, why) => events.push([st?.personId ?? null, why]) });
  assert.equal(follow.start('nobody'), false, 'nobody to follow: refused');
  assert.equal(follow.start('frances'), true);
  assert.equal(follow.state.name, 'Frances M. Glessner');
  const intent = createIntent();
  const dt = 1 / 30;
  // She walks east at 1.4 m/s for 15 s; the follower falls in right behind her.
  for (let i = 0; i < 450; i++) {
    person = { ...person, e: person.e + 1.4 * dt };
    assert.equal(follow.steer(dt, intent), true);
    walker.update(dt, intent);
    follow.afterWalk(intent);
    assert.equal(intent.forward, 0); assert.equal(intent.strafe, 0); assert.equal(intent.sprint, false);
  }
  const want = { e: person.e - FOLLOW.BEHIND_M, n: person.n };
  assert(Math.hypot(walker.state.e - want.e, walker.state.n - want.n) < 0.4, `right behind her: ${walker.state.e.toFixed(2)},${walker.state.n.toFixed(2)} vs ${want.e.toFixed(2)},${want.n.toFixed(2)}`);
  assert(angleOff(facingOf(walker.state), 90) < 3, `looking her way, past her: ${facingOf(walker.state).toFixed(1)}`);
  assert.equal(walker.teleports, 0, 'walked there, not set down');

  // She stops and turns to face north: the stand swings behind her back (south).
  person = { ...person, heading_deg: 0 };
  for (let i = 0; i < 150; i++) { follow.steer(dt, intent); walker.update(dt, intent); follow.afterWalk(intent); }
  assert(Math.hypot(walker.state.e - person.e, walker.state.n - (person.n - FOLLOW.BEHIND_M)) < 0.4,
    `standing, behind her back: ${walker.state.e.toFixed(2)},${walker.state.n.toFixed(2)}`);
  assert(angleOff(facingOf(walker.state), bearingOf(walker.state, person)) < 3, 'standing: looking at her');

  // The visitor looks round: the view is theirs for LOOK_HOLD_S.
  intent.yawDelta = 0.3;
  const yaw0 = walker.state.yaw;
  follow.steer(dt, intent); walker.update(dt, intent); follow.afterWalk(intent);
  assert(near(walker.state.yaw, yaw0 + 0.3), 'their own look is not overwritten');
  follow.steer(dt, intent);
  assert.equal(intent.yawDelta, 0, 'and held a while after');
  walker.update(dt, intent); follow.afterWalk(intent);

  // A fence 1.6 m behind her: the stand is pulled in toward her, in front of the fence.
  blocked = (e, n) => n < person.n - 1.6;
  for (let i = 0; i < 30; i++) { follow.steer(dt, intent); walker.update(dt, intent); follow.afterWalk(intent); }
  const pulled = follow.state.offset;
  assert(pulled && pulled.n > -1.6 && pulled.n <= -FOLLOW.MIN_BEHIND_M + 1e-9 && Math.abs(pulled.e) < 0.01,
    `pulled in short of the fence, still behind her: ${JSON.stringify(pulled)}`);
  // Her back to a wall (out of a doorway): nowhere behind her is clear; swung round her.
  blocked = (e, n) => n < person.n - 0.6;
  for (let i = 0; i < 30; i++) { follow.steer(dt, intent); walker.update(dt, intent); follow.afterWalk(intent); }
  const swung = follow.state.offset;
  assert(swung && swung.n > -0.6 && Math.hypot(swung.e, swung.n) >= FOLLOW.MIN_BEHIND_M - 1e-9,
    `swung round her, out of the wall: ${JSON.stringify(swung)}`);
  assert(!blocked(person.e + swung.e, person.n + swung.n), 'the stand is never in the wall');
  // Walled in all round: hold where you are and watch.
  blocked = (e, n) => Math.hypot(e - person.e, n - person.n) > 0.55;
  for (let i = 0; i < 10; i++) { follow.steer(dt, intent); walker.update(dt, intent); follow.afterWalk(intent); }
  assert.equal(follow.state.held, true, 'nowhere clear: held');
  blocked = () => false;

  // Far away (a teleport elsewhere): set down at the stand at once. (Held, it looks again
  // every HELD_RESOLVE_S.)
  for (let i = 0; i < 30; i++) { follow.steer(dt, intent); walker.update(dt, intent); follow.afterWalk(intent); }
  walker.state.e += 500;
  follow.steer(dt, intent);
  assert(near(walker.state.e, person.e, 0.4) && near(walker.state.n, person.n - FOLLOW.BEHIND_M, 0.4), `jumped to the stand: ${walker.state.e.toFixed(3)},${walker.state.n.toFixed(3)}`);
  follow.afterWalk(intent);

  // A ride (Go to) takes over: follow ends.
  riding = true;
  assert.equal(follow.steer(dt, intent), false);
  assert.equal(follow.active, false);
  assert.deepEqual(events.at(-1), [null, 'travel']);
  riding = false;

  // The visitor's own movement ends it, untouched.
  follow.start('frances');
  intent.forward = 1;
  assert.equal(follow.steer(dt, intent), false);
  assert.equal(intent.forward, 1, 'the visitor\'s own move flows through');
  assert.deepEqual(events.at(-1), [null, 'input']);
  intent.clear();

  // A person still loading is waited for; then followed; then lost.
  let loaded = false;
  const w2 = mkWalker(0, -5);
  const f2 = createFollow({ walker: w2, walk, locate: () => (loaded ? person : null) });
  assert.equal(f2.start('hans'), false, 'no wait: refused');
  assert.equal(f2.start('hans', { name: 'Hans Johnson', wait: 1 }), true);
  assert.equal(f2.steer(0.5, intent), false); assert.equal(f2.active, true, 'waiting');
  loaded = true;
  assert.equal(f2.steer(dt, intent), true, 'found');
  f2.afterWalk(intent);
  loaded = false;
  assert.equal(f2.steer(dt, intent), false);
  assert.equal(f2.active, false, 'lost: stops');
  f2.start('hans', { wait: 0.2 });
  f2.steer(0.3, intent); f2.steer(0.3, intent);
  assert.equal(f2.active, false, 'never loaded: gives up');
  // Flying ends it.
  loaded = true; f2.start('hans'); w2.state.flying = true;
  assert.equal(f2.steer(dt, intent), false); assert.equal(f2.active, false);
  console.log('follow: right behind, looking her way, behind her back standing, pulled in at a fence, swung off a wall, held, look held, jump, wait, ride/input/fly/lost stop PASS');
}

// ---- follow.js round a corner, and never left pressed on a wall ---------------------------
// Kevin's screenshot (2026-11-07): following Frances by 1800 Prairie, the eye was pressed into
// the granite, looking at her through it.
{
  const walk = { speed: 4.47, sprintSpeed: 4.47 * 2.28 };
  const dt = 1 / 30;
  // A house on the inside of a corner: she walks north up a walk, then east along the front.
  const house = (e, n) => e > 1 && e < 30 && n < 9 && n > -30;
  let person = { e: 0, n: 0, heading_deg: 0, head_y: 1.62 };
  const walker = mkWalker(0, -3, 0, { walk, blocked: house });
  const follow = createFollow({ walker, walk, locate: () => person, blockedAt: house });
  follow.start('frances');
  const intent = createIntent();
  const legs = [[0, 1.4, 10 / 1.4], [1.4, 0, 14 / 1.4]];
  let worst = 0;
  for (const [ve, vn, secs] of legs) {
    person = { ...person, heading_deg: (Math.atan2(ve, vn) * 180 / Math.PI + 360) % 360 };
    for (let t = 0; t < secs; t += dt) {
      person = { ...person, e: person.e + ve * dt, n: person.n + vn * dt };
      follow.steer(dt, intent); walker.update(dt, intent); follow.afterWalk(intent);
      assert(!house(walker.state.e, walker.state.n), 'never inside the house');
      if (t > 3) worst = Math.max(worst, Math.hypot(walker.state.e - person.e, walker.state.n - person.n));
    }
  }
  for (let i = 0; i < 60; i++) { follow.steer(dt, intent); walker.update(dt, intent); follow.afterWalk(intent); }
  assert.equal(walker.teleports, 0, 'round the corner by her own trail, not set down');
  assert(worst < 6, `kept close round the corner: worst ${worst.toFixed(2)} m`);
  assert(Math.hypot(walker.state.e - (person.e - FOLLOW.BEHIND_M), walker.state.n - person.n) < 0.4, 'behind her along the front');

  // The follower on the far side of a garden wall with no way round in sight: set down.
  const wall = (e, n) => e > 1.2 && e < 1.5;
  person = { e: 0, n: 0, heading_deg: 0, head_y: 1.62 };
  const w2 = mkWalker(3, -2, 0, { walk, blocked: wall });
  const f2 = createFollow({ walker: w2, walk, locate: () => person, blockedAt: wall });
  f2.start('frances');
  let t = 0;
  for (; t < 4 && w2.teleports === 0; t += dt) {
    person = { ...person, n: person.n + 1.2 * dt };
    f2.steer(dt, intent); w2.update(dt, intent); f2.afterWalk(intent);
  }
  assert.equal(w2.teleports, 1, 'held on the wall: set down at the stand');
  assert(t < FOLLOW.STUCK_S * 2 + 0.5, `soon: after ${t.toFixed(2)} s`);
  assert(w2.state.e < 1.2 && Math.abs(w2.state.n - (person.n - FOLLOW.BEHIND_M)) < 0.5, `on her side, behind her: ${w2.state.e.toFixed(2)},${w2.state.n.toFixed(2)}`);
  console.log(`follow: round a corner by her trail (worst ${worst.toFixed(2)} m, no set-down), set down off a wall after ${t.toFixed(2)} s PASS`);
}

// ---- follow.js is smooth behind a carriage -----------------------------------------------
// Kevin, 2026-11-06: "when i follow hans it is very jittery along side him". The town moves
// a carriage AFTER the walker, at 60 fps with dropped frames; the driver's head bobs and the
// box sways. Before the fix the eye's speed swung by 1.8 m/s (standard deviation) round the
// carriage's 1.5 and the look turned at 25°/s of noise. Since T-3471 the follower is behind
// the carriage and off its line.
{
  const walk = { speed: 4.47, sprintSpeed: 4.47 * 2.28 };   // travel-settings.js defaults
  const walker = mkWalker(-1, -4, 0, { walk });
  const state = walker.state;
  let t = 0, pe = 0;
  const at = () => ({ e: pe, n: 0, heading_deg: 90 + Math.sin(t * 2 * Math.PI * 1.1) * 0.8,
    head_y: 2.6 + 0.035 * Math.sin(t * 2 * Math.PI * 2.2), driver: {} });
  let seen = at();
  const follow = createFollow({ walker, walk, locate: () => seen });
  follow.start('hans');
  assert.equal(follow.state.side, 1, 'the side of the carriage the visitor was on is kept');
  const intent = createIntent();
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const rows = [];
  for (let i = 0; i < 1200; i++) {
    const dt = rnd() < 0.12 ? 1 / 30 : 1 / 60 + (rnd() - 0.5) * 0.003;
    const steps = Math.max(1, Math.ceil(dt / 0.05)), sdt = dt / steps;   // main.js's walk steps
    for (let k = 0; k < steps; k++) { follow.steer(sdt, intent); walker.update(sdt, intent); follow.afterWalk(intent); }
    t += dt; pe += 1.5 * dt; seen = at();   // then the town moves the carriage
    if (i > 300) rows.push({ dt, e: state.e, n: state.n, rel: state.e - seen.e, yaw: state.yaw, pitch: state.pitch });
  }
  const sd = (a) => { const m = a.reduce((x, y) => x + y, 0) / a.length; return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length); };
  const rate = (k, scale = 1) => rows.slice(1).map((r, i) => (r[k] - rows[i][k]) * scale / r.dt);
  const speedSd = sd(rate('e')), yawSd = sd(rate('yaw', 180 / Math.PI)), pitchSd = sd(rate('pitch', 180 / Math.PI));
  assert(speedSd < 0.15, `the eye keeps the carriage's pace: speed sd ${speedSd.toFixed(3)} m/s`);
  assert(yawSd < 3, `the look turns smoothly: yaw rate sd ${yawSd.toFixed(2)} deg/s`);
  assert(pitchSd < 1, `the head's bob is not followed: pitch rate sd ${pitchSd.toFixed(2)} deg/s`);
  assert(Math.abs(rows.at(-1).rel + FOLLOW.DRIVER_BEHIND_M) < 0.3, `behind the carriage: ${rows.at(-1).rel.toFixed(2)} m along`);
  assert(Math.abs(rows.at(-1).n + FOLLOW.DRIVER_SIDE_M) < 0.3, `off its line, on the visitor's side: ${rows.at(-1).n.toFixed(2)} m`);
  console.log(`follow: smooth behind a carriage at 60 fps with dropped frames (speed sd ${speedSd.toFixed(3)} m/s, yaw ${yawSd.toFixed(2)}°/s, pitch ${pitchSd.toFixed(2)}°/s) PASS`);
}

// ---- people-look.js ----------------------------------------------------------------------
{
  const building = { id: 'house_1801_prairie', record: {}, distance: 25 };
  let fire = null;
  const target = { on(fn, { within }) { fire = (t) => fn(t && t.distance <= within ? t : null); return () => { fire = null; }; },
    current: (within) => (building.distance <= within ? building : null) };
  let probe = null, ticks = 0, tick = null;
  const look = createPeopleLook({ target, probe: () => probe, every: (fn) => { tick = fn; return ++ticks; }, stopEvery: () => { tick = null; } });
  const heard = [];
  const off = look.on((t) => heard.push(t?.id ?? null), { within: 40 });
  fire(building);
  assert.deepEqual(heard, ['house_1801_prairie']);
  probe = { personId: 'hans', distance: 9, label: 'Hans Johnson' };
  tick();
  assert.equal(heard.at(-1), 'person:hans', 'a person nearer than the house is named');
  const t = look.current(40);
  assert.equal(t.kind, 'person'); assert.equal(t.label, 'Hans Johnson'); assert.equal(tagName(t), 'Hans Johnson');
  assert.equal(tagName({ kind: 'person', label: null }), 'A person', 'never an id');
  probe = { personId: 'hans', distance: 31, label: 'Hans Johnson' };
  tick();
  assert.equal(heard.at(-1), 'house_1801_prairie', 'beyond the person reach: the house again');
  probe = { personId: 'hans', distance: 26, label: 'Hans Johnson' };
  tick();
  assert.equal(heard.at(-1), 'house_1801_prairie', 'behind the house: the house');
  building.distance = 60; fire(building);
  assert.equal(heard.at(-1), 'person:hans', 'the house out of the tag\'s reach: the person');
  const n = heard.length; tick();
  assert.equal(heard.length, n, 'an unchanged answer is not heard twice');
  probe = null; tick();
  assert.equal(heard.at(-1), null);
  off();
  assert.equal(tick, null, 'nobody listening: no probe');
  console.log('people-look: person nearer than the building, reach, unchanged answers, stop PASS');
}

// ---- transport-loop heading, against the Find stand's yaw convention -------------------
{
  const src = await readFile(new URL('../renderers/web/js/transport-loop.js', import.meta.url), 'utf8');
  assert(/get heading_deg\(\) \{ return \(\(180 - lastPose\.yaw \* 180 \/ Math\.PI\) % 360 \+ 360\) % 360; \}/.test(src), 'heading_deg is the root\'s +z bearing');
  // localToEnu: +z (ahead) is (sin yaw, -cos yaw); a bearing b is (sin b, cos b).
  for (const yaw of [0, 0.4, Math.PI / 2, 2.5, -1.2]) {
    const b = (((180 - yaw * 180 / Math.PI) % 360) + 360) % 360 * Math.PI / 180;
    assert(near(Math.sin(b), Math.sin(yaw)) && near(Math.cos(b), -Math.cos(yaw)), `yaw ${yaw}`);
  }
  console.log('transport heading_deg matches the vehicle root\'s ahead PASS');
}

// ---- main.js goToTarget: a standing figure, and a card's own address -------------------
{
  const source = await readFile(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
  const begin = source.indexOf('  function goToTarget(target) {');
  const end = source.indexOf('  /** The future welcome picker', begin);
  const body = source.slice(begin, end);
  const stand = { kind: 'intersection', local_e: 1, local_n: 2, label: 'House' };
  const visits = [];
  const figure = { id: 'hi_x', person: { name: 'Mary' }, position: { e: 10, n: 20, y: 0 }, heading: 0, root: { parent: {} }, disposed: false };
  const make = (blockedAt = () => false, driverAnchor = () => null) => Function('api', 'jauntRuntime', 'travel', 'router', 'hud', 'destinations', 'openBusiness', 'openBuilding',
    body + '\nreturn goToTarget;')(
    { townTransport: { driverAnchorForPerson: driverAnchor, cancelDriverApproaches() {}, requestDriverApproach: () => ({ cancel() {} }) },
      humans: { external: () => null, get: (id) => (id === 'mary' ? figure : null) } }, null,
    { go: (t, cb) => { visits.push([t, cb]); return t; } }, { blockedAt }, { say() {}, setPanel() {}, selectTab() {} },
    { resolve: () => stand, byId: () => null }, () => {}, () => {});
  const go = make();
  const t = go({ kind: 'person', id: 'mary' });
  assert.equal(t.kind, 'intersection');
  assert(near(t.local_e, 10) && near(t.local_n, 22.5), 'in front of a north-facing figure');
  assert(near(t.yaw_deg, 180), 'facing them');
  assert.equal(t.label, 'Mary');
  assert.equal(typeof visits.at(-1)[1].onArrive, 'function');
  const side = make((e, n) => n > 21)({ kind: 'person', id: 'mary' });
  assert(near(side.local_e, 12.5) && near(side.local_n, 20), 'front blocked: beside them');
  assert.equal(make(() => true)({ kind: 'person', id: 'mary' }), false, 'nowhere clear: refused');
  // "Go to where they lived" names the house: it goes there, not to the driver's seat.
  let asked = 0;
  const drv = make(() => false, () => { asked++; return { at: [0, 0], yaw_rad: 0 }; });
  assert.strictEqual(drv({ kind: 'person', id: 'otis', lives_at: 'house', works_at: null }), stand);
  assert.equal(asked, 0);
  const found = drv({ kind: 'person', id: 'otis' });
  assert.equal(found.kind, 'intersection'); assert.equal(asked, 1, 'Find this person: the seat');
  assert(near(found.yaw_deg, 270), 'arrives facing the seat');
  console.log('goToTarget: beside a standing figure facing them, router-guarded; card addresses go home PASS');
}

// ---- person-card.js offers Follow for someone in town ------------------------------------
{
  const { renderPersonCard, personModel } = await import('../renderers/web/js/person-card.js');
  const mkDoc = () => {
    const mk = (tag) => ({ tag, className: '', textContent: '', dataset: {}, children: [], attrs: {}, listeners: {},
      append(...c) { this.children.push(...c); }, prepend(...c) { this.children.unshift(...c); }, setAttribute(k, v) { this.attrs[k] = v; },
      addEventListener(k, fn) { this.listeners[k] = fn; }, set innerHTML(v) { this._html = v; } });
    return { createElement: mk, createTextNode: (t) => ({ text: t }) };
  };
  const all = (n, out = []) => { out.push(n); for (const c of n.children ?? []) all(c, out); return out; };
  const m = personModel({ row: { id: 'hans', name: 'Hans Johnson', grade: 'attested' }, sceneYear: 1904 });
  let followed = null;
  const yes = all(renderPersonCard(mkDoc(), m, { onFind() {}, onFollow: (id) => { followed = id; }, inTown: () => true }));
  const btn = yes.find((n) => n.className?.includes('insp-person-follow'));
  assert(btn, 'Follow offered'); let stopped = false; btn.listeners.click({ stopPropagation() { stopped = true; } }); assert.equal(followed, 'hans'); assert(stopped, 'the click is not let up to the pane, which would reopen the card');
  const no = all(renderPersonCard(mkDoc(), m, { onFind() {}, onFollow() {}, inTown: () => false }));
  // T-3531: someone not in town keeps Find and Follow, greyed, with no click, and the reason under them.
  const off = no.filter((n) => /insp-person-(follow|find)/.test(n.className ?? ''));
  assert.equal(off.length, 2, 'not in town: Find and Follow still shown');
  assert(off.every((n) => n.disabled && !n.listeners.click), 'not in town: Find and Follow greyed, no click');
  assert(no.some((n) => (n.className ?? '').includes('insp-person-unfound') && /Not out in town/.test(n.textContent)), 'not in town: the reason is said');
  const sau = personModel({ row: { id: 'caldwell_billy', name: 'Billy Caldwell (Sauganash)', grade: 'attested', present: 'absent',
    household_name: 'Billy Caldwell (Sauganash), who came to Chicago on 16 August 1812' }, sceneYear: 1812 });
  const gone = all(renderPersonCard(mkDoc(), sau, { onFind() {}, onFollow() {}, inTown: () => false }));
  assert(gone.some((n) => /came to Chicago on 16 August 1812/.test(n.textContent ?? '')), 'absent: says when they came');
  console.log('person card: Find and Follow live only for someone placed in town, greyed with the reason otherwise PASS');
}
console.log('ok person interaction (T-3404)');
