#!/usr/bin/env node
// T-2547: the crash guard's policy, without a browser. The smoke (part 6, 390x780)
// drives the same module in the real app: a stale marker, and two lost contexts.
import assert from 'node:assert/strict';
import {
  createCrashGuard, stepDown, MARKER_KEY, STEPDOWN_KEY, RELOADS_KEY, BEAT_STALE_MS, NOTICE,
} from '../renderers/web/js/crash-guard.js';

const ORDER = ['full', 'balanced', 'light'];
const store = () => {
  const m = new Map();
  return { getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k), m };
};
const tab = (local = store()) => ({ session: store(), local, win: new EventTarget() });
let clock = 1_000_000;
const guard = (t, extra = {}) => createCrashGuard({ year: '1835', order: ORDER, ...t, now: () => clock, doc: null, ...extra });
const hide = t => t.win.dispatchEvent(new Event('pagehide'));

// The ladder: one tier down, Sharpness Low, never below light.
assert.deepEqual(stepDown({ detail: 'full', quality: 1.5 }, ORDER), { detail: 'balanced', quality: 1, lowered: true });
assert.deepEqual(stepDown({ detail: 'balanced', quality: 2 }, ORDER), { detail: 'light', quality: 1, lowered: true });
assert.deepEqual(stepDown({ detail: 'light', quality: 1.5 }, ORDER), { detail: 'light', quality: 1, lowered: true });
assert.deepEqual(stepDown({ detail: 'light', quality: 1 }, ORDER), { detail: 'light', quality: 1, lowered: false });

// A clean boot: no marker found, nothing lowered, no notice; a clean pagehide clears it.
{
  const t = tab();
  const g = guard(t);
  const b = g.boot({ detail: 'full', quality: 1.5 });
  assert.deepEqual([b.detail, b.quality, b.lowered.detail, b.lowered.quality], ['full', 1.5, false, false]);
  assert.equal(g.state.found, null);
  assert.equal(g.state.notice, null);
  assert.ok(t.session.getItem(MARKER_KEY) && t.local.getItem(MARKER_KEY), 'the marker is written at boot');
  hide(t);
  assert.equal(t.session.getItem(MARKER_KEY), null);
  assert.equal(t.local.getItem(MARKER_KEY), null);
  const again = guard(t).boot({ detail: 'full', quality: 1.5 });
  assert.equal(again.detail, 'full', 'a session that ended cleanly does not step the next one down');
  hide(t);
}

// A session that died: the next boot is one tier lower at Low, says so, and stays
// there at later boots until the visitor chooses in Settings.
{
  const t = tab();
  guard(t).boot({ detail: 'full', quality: 2 });   // ...and the tab is killed: no pagehide
  const g = guard(t);
  const b = g.boot({ detail: 'full', quality: 2 });
  assert.deepEqual([b.detail, b.quality, b.lowered.detail, b.lowered.quality], ['balanced', 1, true, true]);
  assert.equal(g.state.found.detail, 'full');
  assert.deepEqual(g.state.lowered, { why: 'memory', from: { detail: 'full', quality: 2 }, to: { detail: 'balanced', quality: 1 } });
  assert.equal(g.state.notice, NOTICE.memory);
  hide(t);
  const later = guard(t);
  assert.equal(later.boot({ detail: 'full', quality: 2 }).detail, 'balanced', 'the step-down holds after a clean session');
  assert.equal(later.state.notice, null, 'and is said once, not at every boot');
  later.chosen('detail');
  assert.deepEqual(JSON.parse(t.local.getItem(STEPDOWN_KEY)).detail, undefined, 'a detail chosen after it wins');
  later.chosen('quality');
  assert.equal(t.local.getItem(STEPDOWN_KEY), null, 'and with both chosen the record is gone');
  hide(t);
  assert.equal(guard(t).boot({ detail: 'full', quality: 2 }).detail, 'full');
  hide(t);
}

// Two crashes walk the ladder down, and the floor is light.
{
  const t = tab();
  guard(t).boot({ detail: 'balanced', quality: 1.5 });
  assert.equal(guard(t).boot({ detail: 'balanced', quality: 1.5 }).detail, 'light');
  const g = guard(t);
  const b = g.boot({ detail: 'balanced', quality: 1.5 });
  assert.equal(b.detail, 'light');
  assert.equal(g.state.lowered, null, 'nothing below light, so nothing lowered');
  assert.equal(g.state.notice, null, 'and nothing said');
  hide(t);
}

// The local mirror alone (iOS lost session storage) is believed only once its
// heartbeat has gone stale — a second live tab is not a dead one.
{
  const local = store();
  const first = tab(local);
  guard(first).boot({ detail: 'full', quality: 1.5 });
  const second = tab(local);
  assert.equal(guard(second).boot({ detail: 'full', quality: 1.5 }).detail, 'full', 'a live sibling tab');
  hide(second);
  // ...and then iOS discards the first tab: its marker stays and its heartbeat stops.
  const discarded = tab(local);
  clock += BEAT_STALE_MS + 1;
  assert.equal(guard(discarded).boot({ detail: 'full', quality: 1.5 }).detail, 'balanced', 'a tab iOS discarded');
  hide(discarded);
}

// The context: lost twice in a session reloads ONCE, then lowers and leaves the
// reload to the visitor. A loss that needs no reload does not reload.
{
  const t = tab();
  let reloads = 0;
  const lose = c => { const e = new Event('webglcontextlost', { cancelable: true }); c.dispatchEvent(e); return e.defaultPrevented; };
  const restore = c => c.dispatchEvent(new Event('webglcontextrestored'));

  const g1 = guard(t, { reload: () => { reloads += 1; hide(t); } });
  g1.boot({ detail: 'full', quality: 1.5 });
  const c1 = new EventTarget();
  g1.watchContext(c1, { needsReload: () => true });
  assert.equal(lose(c1), true, 'the loss is preventDefaulted so the context may come back');
  assert.equal(g1.state.notice, NOTICE.contextReset);
  restore(c1);
  assert.equal(reloads, 1);
  assert.equal(t.session.getItem(RELOADS_KEY), '1');

  const g2 = guard(t, { reload: () => { reloads += 1; } });
  const b2 = g2.boot({ detail: 'full', quality: 1.5 });
  assert.equal(b2.detail, 'full', 'our own reload is not a crash');
  const c2 = new EventTarget();
  g2.watchContext(c2, { needsReload: () => true });
  lose(c2);
  restore(c2);
  assert.equal(reloads, 1, 'a second loss in the session does not reload by itself');
  assert.deepEqual(g2.state.lowered, { why: 'context', from: { detail: 'full', quality: 1.5 }, to: { detail: 'balanced', quality: 1 } });
  assert.equal(g2.state.notice, NOTICE.contextLowered('Balanced'));
  lose(c2); restore(c2);
  assert.equal(reloads, 1, 'nor a third');
  assert.equal(g2.state.lowered.to.detail, 'light', 'each further loss lowers the next boot one more tier');
  hide(t);
  assert.equal(guard(t).boot({ detail: 'full', quality: 1.5 }).detail, 'light', 'the next boot is the lowered tier');
  hide(t);

  const fresh = tab();
  let r = 0;
  const g3 = guard(fresh, { reload: () => { r += 1; } });
  g3.boot({ detail: 'light', quality: 1 });
  const c3 = new EventTarget();
  g3.watchContext(c3, { needsReload: () => false });
  lose(c3); restore(c3);
  assert.equal(r, 0, 'nothing was let go, so three restores on its own');
  assert.equal(g3.state.notice, null, 'and the card goes');
  lose(c3);
  assert.equal(g3.state.notice, NOTICE.contextFloor, 'at the floor there is nothing to lower; the card offers Reload');
  hide(fresh);
}

// Storage that refuses every call never throws out of the boot.
{
  const deny = { getItem() { throw Error('denied'); }, setItem() { throw Error('denied'); }, removeItem() { throw Error('denied'); } };
  const t = { session: deny, local: deny, win: new EventTarget() };
  assert.equal(guard(t).boot({ detail: 'full', quality: 1.5 }).detail, 'full');
  hide(t);
}

console.log('crash guard: marker, step-down, floor, sibling tab, context reloads once — ok');
