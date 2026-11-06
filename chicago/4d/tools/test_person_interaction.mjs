// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * test_person_interaction.mjs — T-3404: every person placed in town is interactive.
 *
 *   node tools/test_person_interaction.mjs
 *
 * Kevin, 2026-11-06: "making them fully available to interact with". Drives, with fakes:
 *   - follow.js: the stand beside a person, the side kept or switched when blocked, the
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
import { createFollow, followStand, FOLLOW } from '../renderers/web/js/follow.js';
import { createPeopleLook } from '../renderers/web/js/people-look.js';
import { tagName } from '../renderers/web/js/target-tag.js';
import { createIntent } from '../renderers/web/js/controls/intent.js';
import { bearingToYaw } from '../renderers/web/js/angles.js';

const near = (a, b, eps = 1e-6) => Math.abs(a - b) <= eps;

// ---- follow.js -------------------------------------------------------------------------
{
  // The stand: SIDE_M to the right of a person facing east (90°), BEHIND_M back (west).
  const s = followStand({ e: 100, n: 50, heading_deg: 90 }, 1);
  assert(near(s.e, 100 - FOLLOW.BEHIND_M) && near(s.n, 50 - FOLLOW.SIDE_M), `right of an eastbound person is south: ${JSON.stringify(s)}`);
  const l = followStand({ e: 100, n: 50, heading_deg: 0 }, -1);
  assert(near(l.e, 100 - FOLLOW.SIDE_M) && near(l.n, 50 - FOLLOW.BEHIND_M), 'left of a northbound person is west');

  // A walker that moves exactly as walker.js does: camera-relative, at the paces given.
  const walk = { speed: 1.45, sprintSpeed: 3.4 };
  const mkWalker = (e, n, bearing = 0) => {
    const state = { e, n, yaw: bearingToYaw(bearing), pitch: 0, eyeY: 1.6, groundY: 0, flying: false };
    return { state, teleport({ local_e, local_n, yaw_deg }) { state.e = local_e; state.n = local_n; if (yaw_deg != null) state.yaw = bearingToYaw(yaw_deg); },
      update(dt, intent) {
        state.yaw += intent.yawDelta; state.pitch += intent.pitchDelta; intent.clearLook();
        let f = intent.forward, r = intent.strafe; const m = Math.hypot(f, r); if (m > 1) { f /= m; r /= m; }
        const sp = intent.sprint ? walk.sprintSpeed : walk.speed;
        state.e += (-Math.sin(state.yaw) * f + Math.cos(state.yaw) * r) * sp * dt;
        state.n += (Math.cos(state.yaw) * f + Math.sin(state.yaw) * r) * sp * dt;
      } };
  };
  let person = { e: 0, n: 0, heading_deg: 90, head_y: 2.4, name: 'Hans Johnson' };
  const walker = mkWalker(-1, -6, 0);  // south of an eastbound person: their right side
  const events = [];
  let riding = false;
  let blocked = () => false;
  const follow = createFollow({ walker, walk, locate: (id) => (id === 'hans' ? person : null),
    blockedAt: (e, n) => blocked(e, n), busy: () => riding, onChange: (st, why) => events.push([st?.personId ?? null, why]) });
  assert.equal(follow.start('nobody'), false, 'nobody to follow: refused');
  assert.equal(follow.start('hans'), true);
  assert.equal(follow.state.side, 1, 'the side the visitor stands on is kept');
  assert.equal(follow.state.name, 'Hans Johnson');
  const intent = createIntent();
  const dt = 1 / 30;
  // The person drives east at 1.3 m/s for 20 s; the follower keeps beside them.
  for (let i = 0; i < 600; i++) {
    person = { ...person, e: person.e + 1.3 * dt };
    assert.equal(follow.steer(dt, intent), true);
    walker.update(dt, intent);
    follow.afterWalk(intent);
    assert.equal(intent.forward, 0); assert.equal(intent.strafe, 0); assert.equal(intent.sprint, false);
  }
  const want = followStand(person, 1);
  assert(Math.hypot(walker.state.e - want.e, walker.state.n - want.n) < 0.4, `kept at the stand: ${walker.state.e.toFixed(2)},${walker.state.n.toFixed(2)} vs ${want.e.toFixed(2)},${want.n.toFixed(2)}`);
  const bearingTo = (Math.atan2(person.e - walker.state.e, person.n - walker.state.n) * 180 / Math.PI + 360) % 360;
  const facing = ((-walker.state.yaw * 180 / Math.PI) % 360 + 360) % 360;
  assert(Math.abs(((bearingTo - facing + 540) % 360) - 180) < 3, `looking at them (${facing.toFixed(1)} vs ${bearingTo.toFixed(1)})`);
  assert(walker.state.pitch > 0, 'looks up to a driver on the box');

  // The visitor looks round: the view is theirs for LOOK_HOLD_S.
  intent.yawDelta = 0.3;
  const yaw0 = walker.state.yaw;
  follow.steer(dt, intent); walker.update(dt, intent); follow.afterWalk(intent);
  assert(near(walker.state.yaw, yaw0 + 0.3), 'their own look is not overwritten');
  follow.steer(dt, intent);
  assert.equal(intent.yawDelta, 0, 'and held a while after');
  walker.update(dt, intent); follow.afterWalk(intent);

  // The stand blocked on this side (a fence): the other side.
  blocked = (e, n) => n < person.n;
  follow.steer(dt, intent); walker.update(dt, intent); follow.afterWalk(intent);
  assert.equal(follow.state.side, -1, 'switched to the clear side');
  blocked = () => false;

  // Far away (a teleport elsewhere): set down at the stand at once.
  walker.state.e += 500;
  follow.steer(dt, intent);
  const jump = followStand(person, -1);
  assert(near(walker.state.e, jump.e) && near(walker.state.n, jump.n), 'jumped to the stand');
  follow.afterWalk(intent);

  // A ride (Go to) takes over: follow ends.
  riding = true;
  assert.equal(follow.steer(dt, intent), false);
  assert.equal(follow.active, false);
  assert.deepEqual(events.at(-1), [null, 'travel']);
  riding = false;

  // The visitor's own movement ends it, untouched.
  follow.start('hans');
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
  assert.notEqual(f2.state.side, null);
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
  console.log('follow: stand beside, kept side / switched when blocked, look held, jump, wait, ride/input/fly/lost stop PASS');
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
  assert(btn, 'Follow offered'); btn.listeners.click(); assert.equal(followed, 'hans');
  const no = all(renderPersonCard(mkDoc(), m, { onFind() {}, onFollow() {}, inTown: () => false }));
  assert(!no.some((n) => n.className?.includes('insp-person-follow')), 'not in town: no Follow');
  console.log('person card: Follow only for someone placed in town PASS');
}
console.log('ok person interaction (T-3404)');
