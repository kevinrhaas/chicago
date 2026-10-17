// T-2621 — Navigator deep links and Back (js/nav-link.js).
//
//   node tools/test_nav_link.mjs
import assert from 'node:assert/strict';
import { parseNavLink, createNavHistory, navHoldsBack } from '../renderers/web/js/nav-link.js';

// ---- the link -----------------------------------------------------------------------
assert.deepEqual(parseNavLink('?nav=jaunts'), { app: 'jaunts', id: null, tab: null });
assert.deepEqual(parseNavLink('?nav=map'), { app: 'map', id: null, tab: null });
assert.deepEqual(parseNavLink('?nav=inspect:glessner_house&tab=design'), { app: 'inspect', id: 'glessner_house', tab: 'design' },
  'QA-15: the dossier link routes to Inspect, its building and its tab');
assert.deepEqual(parseNavLink('?year=1904&nav=people&seed=3'), { app: 'people', id: null, tab: null }, 'other parameters are left alone');
assert.equal(parseNavLink(''), null);
assert.equal(parseNavLink('?nav='), null);
assert.equal(parseNavLink('?nav=Inspect'), null, 'an app id is lower case, as the rail spells it');
assert.equal(parseNavLink('?nav=../evil'), null, 'nothing that is not an app id');
assert.equal(parseNavLink('?nav=inspect:a:b'), null);
assert.deepEqual(parseNavLink('?nav=inspect:<script>&tab=../x'), { app: 'inspect', id: null, tab: null },
  'an id or a tab that is not well formed is dropped, the app kept');

// ---- Back ---------------------------------------------------------------------------
function fakeWindow() {
  const stack = [{ state: null }];
  let at = 0;
  const fns = [];
  const win = {
    location: { href: 'https://example.test/4d/1904/' },
    history: {
      get state() { return stack[at].state; },
      get length() { return stack.length; },
      pushState(state) { stack.splice(at + 1); stack.push({ state }); at += 1; },
      back() { if (at > 0) { at -= 1; queueMicrotask(() => fns.forEach((fn) => fn({ state: stack[at].state }))); } else win.left = true; },
    },
    addEventListener(type, fn) { if (type === 'popstate') fns.push(fn); },
    removeEventListener() {},
    left: false,
    get at() { return at; },
    /** The browser's own Back button. */
    pressBack() { win.history.back(); },
  };
  return win;
}
function fakeNav() {
  let state = { app: 'home', level: 0 };
  const fns = new Set();
  const emit = () => fns.forEach((fn) => fn({ ...state }));
  return {
    onChange(fn) { fns.add(fn); return () => fns.delete(fn); },
    closeApp() { state = { app: 'home', level: 0 }; emit(); },
    set(next) { state = { ...state, ...next }; emit(); },
    get state() { return state; },
  };
}
const tick = () => new Promise((r) => setTimeout(r, 0));

assert.equal(navHoldsBack({ app: 'home', level: 0 }), false);
assert.equal(navHoldsBack({ app: 'home', level: 1 }), true);
assert.equal(navHoldsBack({ app: 'jump', level: 0 }), true);

{
  const win = fakeWindow(), nav = fakeNav();
  const h = createNavHistory({ nav, win });
  nav.set({ app: 'jump', level: 1 });
  assert.equal(win.history.length, 2, 'opening an app holds one history entry');
  nav.set({ app: 'people', level: 1 });
  assert.equal(win.history.length, 2, 'switching apps holds no more');
  win.pressBack();
  await tick();
  assert.deepEqual(nav.state, { app: 'home', level: 0 }, 'Back closes the app, to Home, docked');
  assert.equal(win.left, false, 'and stays on the page');
  assert.equal(h.held, false);
  win.pressBack();
  assert.equal(win.left, true, 'a second Back leaves');
}
{
  const win = fakeWindow(), nav = fakeNav();
  createNavHistory({ nav, win });
  nav.set({ level: 1 });
  assert.equal(win.history.length, 2);
  nav.set({ level: 0 });           // closed by hand
  await tick();
  assert.equal(win.at, 0, 'closing by hand gives the entry back');
  assert.deepEqual(nav.state, { app: 'home', level: 0 }, 'and the popstate that causes is not read as a Back');
  win.pressBack();
  assert.equal(win.left, true, 'so the next Back leaves at once');
}
assert.equal(createNavHistory({ nav: null }), null);
assert.equal(createNavHistory({ nav: fakeNav(), win: {} }), null, 'no history api, nothing held');

console.log('NAV LINK PASS — ?nav=app[:id]&tab= parsed and bad parts dropped quietly; Back closes the open app and stays, the next Back leaves');
