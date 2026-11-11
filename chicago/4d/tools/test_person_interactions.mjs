// T-3543: walking targets remain selectable, explicit picks persist, and menus release attention.
import assert from 'node:assert/strict';
import { createInteractions, createInteractKey, PERSON_GRACE_S } from '../renderers/web/js/interact.js';

const doc = { createElement(tag) {
  return { tag, children: [], dataset: {}, attrs: {}, listeners: {}, hidden: false,
    append(...nodes) { this.children.push(...nodes); }, appendChild(node) { this.children.push(node); },
    replaceChildren(...nodes) { this.children = nodes; }, setAttribute(k, v) { this.attrs[k] = v; },
    addEventListener(k, fn) { this.listeners[k] = fn; }, removeEventListener() {}, focus() {} };
} };
let clock = 0, flying = false, enabled = true, held = 0, released = 0;
const acted = [], ix = createInteractions(), keys = doc.createElement('window');
const keyEl = doc.createElement('button'), moreEl = doc.createElement('div');
const person = (id, e) => ix.add({ id, name: id, kind: 'person', states: ['out'], state: 'out', at: [e, 0], reach: 2.5,
  actions: { out: [
    { id: 'greet', label: 'Greet', icon: '👋', steps: [], refuse: () => { acted.push([id, 'greet']); } },
    { id: 'go_home', label: 'Go home', steps: [] },
    { id: 'work', label: 'Tend garden', icon: '❧', steps: [], refuse: () => { acted.push([id, 'work']); } },
    { id: 'go_inside', label: 'Go inside', steps: [] },
  ] } });
const a = person('John', 1), b = person('Passerby', 50);
const key = createInteractKey({ interactions: ix, keyEl, moreEl, doc, keys, now: () => clock,
  where: () => ({ e: 0, n: 0, flying }), enabled: () => enabled,
  onExpand: () => { held++; return () => { released++; }; } });
const press = code => keys.listeners.keydown({ code, preventDefault() {} });
assert.equal(key.refresh(), a);
a.at = [4, 0]; clock = PERSON_GRACE_S - .1;
assert.equal(key.refresh(), a, 'a person walking out of arm’s reach keeps the key long enough to open it');
press('KeyR'); assert.equal(held, 1);
clock = 50; a.at = [20, 0]; b.at = [1, 0];
assert.equal(key.refresh(), a, 'an open list stays on its person despite a nearer passerby');
assert.deepEqual(key.choices, ['greet', 'work', 'go_inside', 'go_home']);
const buttons = moreEl.children.filter(n => n.tag === 'button');
assert.equal(moreEl.children[0].children[0].textContent, 'John', 'the retained target is named');
assert(buttons.every(n => n.children[0].innerHTML.startsWith('<svg') && !/👋|❧/.test(n.children[0].innerHTML)), 'actions draw line icons, not emoji');
assert.equal(buttons.at(-2).dataset.tone, 'return'); assert.equal(buttons.at(-1).dataset.tone, 'return');
assert(buttons.at(-2).className.includes('ik-return-first'), 'indoor destinations form the final group');
buttons[1].listeners.click({ preventDefault() {} });
assert.deepEqual(acted, [['John', 'work']], 'a moving target cannot change under the selected action');
assert.equal(released, 1); assert(moreEl.hidden);
assert(key.select('John')); a.at = [100, 0]; clock = 1000;
assert.equal(key.refresh(), a, 'a deliberate pick persists beyond proximity and the grace period');
press('KeyR'); press('Escape');
assert.equal(released, 2); assert.equal(key.refresh(), b, 'Escape dismisses the selected person');
assert(key.select('John')); press('KeyR'); a.at = null;
assert.equal(key.refresh(), b, 'going indoors releases a pinned target'); assert.equal(released, 3);
a.at = [1, 0]; key.select('John'); press('KeyR'); ix.remove('John');
assert.equal(key.refresh(), b); assert.equal(released, 4, 'retired figures release attention');
key.select('Passerby'); press('KeyR');
moreEl.children[0].children[1].listeners.click({ preventDefault() {} });
assert.equal(released, 5); assert(moreEl.hidden, 'the visible close control dismisses the list');
key.select('Passerby'); flying = true; assert.equal(key.refresh(), null);
flying = false; key.select('Passerby'); enabled = false; assert.equal(key.refresh(), null);
enabled = true; b.at = [100, 0];
const gate = ix.add({ id: 'gate', kind: 'gate', name: 'Gate', states: ['shut'], state: 'shut', at: [1, 0], reach: 2,
  actions: { shut: [{ id: 'open', label: 'Open', steps: [] }] } });
assert.equal(key.refresh(), gate); gate.at = [3, 0];
assert.equal(key.refresh(), null, 'fixed objects retain their ordinary reach requirement');
key.dispose(); assert.equal(released, held, 'every menu attention hold was released exactly once');
console.log('person interactions: walking grace, pinned selection, stable actions, dismissal, SVG icons and destination order pass');
