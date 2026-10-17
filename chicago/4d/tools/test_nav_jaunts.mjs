// T-2630 — the Navigator's Jaunts app (js/apps/jaunts-view.js): Jaunts · Go to · Free roam,
// the Welcome card's own list and search lent to it and handed back, and Home's three
// choices opening the matching segment.
//
//   node tools/test_nav_jaunts.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { mount, shown, unmount, SEGMENTS } from '../renderers/web/js/apps/jaunts-view.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const web = path.join(here, '../renderers/web');

function fakeDoc() {
  const byId = new Map();
  const make = (tag, id = null) => {
    const fns = {};
    const el = {
      tagName: tag.toUpperCase(), className: '', textContent: '', dataset: {}, attrs: {}, children: [], parentNode: null,
      hidden: false, tabIndex: 0, focused: 0, classList: { set: new Set(), toggle(c, on) { if (on) this.set.add(c); else this.set.delete(c); }, contains(c) { return this.set.has(c); } },
      get id() { return this._id; }, set id(v) { this._id = v; byId.set(v, el); },
      get nextSibling() { const p = el.parentNode; return p ? p.children[p.children.indexOf(el) + 1] ?? null : null; },
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      append(...cs) { for (const c of cs) { c.parentNode?.children.splice(c.parentNode.children.indexOf(c), 1); c.parentNode = el; el.children.push(c); } },
      insertBefore(c, ref) {
        c.parentNode?.children.splice(c.parentNode.children.indexOf(c), 1);
        c.parentNode = el; const i = el.children.indexOf(ref); el.children.splice(i < 0 ? el.children.length : i, 0, c);
      },
      replaceChildren(...cs) { for (const c of el.children) c.parentNode = null; el.children = []; el.append(...cs); },
      addEventListener(type, fn) { (fns[type] ??= []).push(fn); },
      dispatch(type, extra = {}) { for (const fn of fns[type] ?? []) fn({ target: el, preventDefault() {}, ...extra }); },
      focus() { el.focused++; },
      get ownerDocument() { return doc; },
    };
    if (id) el.id = id;
    return el;
  };
  const doc = { createElement: (t) => make(t), getElementById: (id) => byId.get(id) ?? null, make };
  return doc;
}

const doc = fakeDoc();
// The Welcome card as the page has it: its Jaunts region holding the list, and the picker.
const welcome = doc.make('div', 'welcome');
const region = doc.make('section', 'welcome-jaunts-region');
const list = doc.make('div', 'welcome-jaunts-content');
const after = doc.make('p', 'after-list');
region.append(list, after);
const picker = doc.make('section', 'welcome-picker');
picker.hidden = true;
const search = doc.make('input', 'welcome-search');
picker.append(search);
const message = doc.make('p', 'welcome-message');
welcome.append(region, picker, message);

const calls = [];
const api = {};
const ctx = { api, actions: { jauntList: () => calls.push('list'), gotoList: () => calls.push('search'), freeRoam: () => calls.push('roam') } };
const panel = doc.make('div', 'nav-app-jaunts');
mount(panel, ctx);

const [tabs, pJaunts, pGoto, pRoam] = panel.children;
assert.equal(tabs.getAttribute('role'), 'tablist');
assert.deepEqual(tabs.children.map((b) => b.textContent), SEGMENTS.map((s) => s.label));
assert.deepEqual(tabs.children.map((b) => b.getAttribute('role')), ['tab', 'tab', 'tab']);
assert.deepEqual([pJaunts, pGoto, pRoam].map((p) => p.getAttribute('role')), ['tabpanel', 'tabpanel', 'tabpanel']);
assert.equal(api.jauntsApp?.current, 'jaunts', 'the app opens on Jaunts');
assert.equal(list.parentNode, pJaunts, 'the Welcome card\'s own Jaunts list is lent to the Jaunts segment');
assert.deepEqual(calls, ['list'], 'and asked to render');
assert.equal(pGoto.hidden, true);

// Home's Go to choice: the Go to segment, the search lent and shown, focus in it.
api.jauntsApp.segment('goto', { by: 'hand' });
assert.equal(picker.parentNode, pGoto, 'the Welcome card\'s search is lent to Go to');
assert.equal(picker.hidden, false, 'and shown there');
assert.equal(search.focused, 1, 'focus goes into the search');
assert.deepEqual(tabs.children.map((b) => b.getAttribute('aria-selected')), ['false', 'true', 'false']);
assert.equal(pJaunts.hidden, true);
assert.equal(calls.at(-1), 'search');

// The arrow keys move along the segments.
tabs.dispatch('keydown', { key: 'ArrowRight', target: tabs.children[1] });
assert.equal(api.jauntsApp.current, 'roam');
pRoam.children.find((c) => c.className.split(' ').includes('nav-roam')).dispatch('click');
assert.equal(calls.at(-1), 'roam', 'Free roam pockets the Navigator');

// The Welcome card shows again: everything it lent comes home, in place, the picker hidden.
api.jauntsApp.restore();
assert.equal(list.parentNode, region);
assert.equal(region.children[0], list, 'back in its own place, before what followed it');
assert.equal(picker.parentNode, welcome);
assert.equal(welcome.children.indexOf(picker), 1);
assert.equal(picker.hidden, true, 'hidden, as the card keeps it until its Go to is chosen');
assert.equal(api.jauntsApp.lent, 0);

// Reopened from the rail: the current segment is lent again.
api.jauntsApp.segment('jaunts');
shown(panel, ctx);
assert.equal(list.parentNode, pJaunts);
unmount(panel);
assert.equal(list.parentNode, region, 'unmounting hands everything back too');

// The page: Navigator Home's three choices, each naming its segment; the Welcome card keeps its three.
{
  const html = readFileSync(path.join(web, 'index.html'), 'utf8');
  const home = html.slice(html.indexOf('id="nav-home"'), html.indexOf('</section>\n\n<aside id="popup"'));
  for (const [seg, label] of [['jaunts', 'Take a Jaunt'], ['goto', 'Go to…'], ['roam', 'Free roam']]) {
    assert.match(home, new RegExp(`data-segment="${seg}"><strong>${label}</strong>`), `Home offers ${label}`);
  }
  for (const id of ['welcome-jaunts', 'welcome-explore', 'home-roam']) assert.match(html, new RegExp(`id="${id}"`), `the Welcome card keeps #${id}`);
  const main = readFileSync(path.join(web, 'js/main.js'), 'utf8');
  assert.match(main, /#nav-home \[data-segment\][\s\S]*api\.openJaunts\(choice\.dataset\.segment\)/, 'each Home choice opens its segment');
  assert.match(main, /onShow: \(\) => api\.jauntsApp\?\.restore\(\)/, 'the Welcome card takes back what it lent before it shows');
  const manifest = readFileSync(path.join(web, 'js/apps/jaunts.js'), 'utf8');
  assert.match(manifest, /load: \(\) => import\('\.\/jaunts-view\.js'\)/, 'Jaunts is a screen, no longer a stub');
}

console.log('NAV JAUNTS PASS — Jaunts · Go to · Free roam as tabs; the Welcome card\'s list and search lent and handed back in place; Home\'s choices open their segment');
