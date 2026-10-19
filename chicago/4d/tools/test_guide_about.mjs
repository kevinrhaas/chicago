#!/usr/bin/env node
// T-2667 (NAV-1002): Guide › About this destination. The old research hub's topics fold into
// four cards — How we grade, Sources, Liberties, What lived and grew here — and the order book
// moves behind Researcher mode (owner ruling 2026-10-16). Holds:
//   - every topic is in exactly one card, the four visitor cards in that order, and the order
//     book alone in a researcher card;
//   - each destination (its scene's own layers, read the way main.js reads them) keeps all four
//     visitor cards, each with a topic, and 1904 carries no researcher card;
//   - the hub's markup marks the researcher card `data-researcher`, and nothing a visitor reads
//     outside it carries an id, a path, "tier", "ticket", "order book" or "commit gate";
//   - the page keeps every topic's container and mount id, the order book's topic is marked
//     `data-researcher`, its tab is "About" with the head "About this destination", and
//     css/skins.css hides a marked element until Researcher mode is on;
//   - Guide's own block lists the four cards and a fifth only Researcher mode shows, and a tap
//     asks the page to open that card;
//   - the source list names a kind of source, never a tier number.
// The smoke (part 12) opens it in the page, in 1835; part 14 reads the 1904 hub's cards.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const WEB = 'renderers/web';

// ---- a small DOM, enough for the Guide screen -------------------------------------------
function makeDoc() {
  const text = (data) => ({ nodeType: 3, data, parentNode: null, get textContent() { return this.data; },
    remove() { const p = this.parentNode; if (p) p.childNodes.splice(p.childNodes.indexOf(this), 1); this.parentNode = null; } });
  const el = (tag) => {
    const fns = {};
    const e = {
      nodeType: 1, tagName: tag.toUpperCase(), childNodes: [], parentNode: null, attrs: {}, dataset: {}, className: '', id: '', type: '',
      get children() { return this.childNodes.filter((c) => c.nodeType === 1); },
      get textContent() { return this.childNodes.map((c) => c.textContent).join(''); },
      set textContent(v) { this.childNodes = []; if (v !== '') this.append(String(v)); },
      get ownerDocument() { return doc; },
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      hasAttribute(k) { return k in this.attrs; },
      removeAttribute(k) { delete this.attrs[k]; },
      append(...cs) { for (const c of cs) { const n = typeof c === 'string' ? text(c) : c; n.remove?.(); n.parentNode = e; e.childNodes.push(n); } },
      replaceChildren(...cs) { for (const c of e.childNodes) c.parentNode = null; e.childNodes = []; e.append(...cs); },
      remove() { const p = this.parentNode; if (p) p.childNodes.splice(p.childNodes.indexOf(this), 1); this.parentNode = null; },
      addEventListener(t, f) { (fns[t] ??= []).push(f); },
      click() { for (const f of fns.click ?? []) f({ preventDefault() {}, stopPropagation() {} }); },
    };
    e.classList = {
      add(c) { const s = new Set(e.className.split(' ').filter(Boolean)); s.add(c); e.className = [...s].join(' '); },
      remove(c) { e.className = e.className.split(' ').filter((x) => x && x !== c).join(' '); },
      contains: (c) => e.className.split(' ').includes(c),
      toggle(c, on) { if (on) this.add(c); else this.remove(c); },
    };
    return e;
  };
  const doc = { createElement: el, defaultView: { addEventListener() {}, removeEventListener() {}, print() {} } };
  doc.documentElement = el('html');
  doc.body = el('body');
  doc.documentElement.append(doc.body);
  doc.getElementById = (id) => all(doc.documentElement).find((n) => n.id === id) ?? null;
  return doc;
}
const all = (root, out = []) => { for (const c of root?.children ?? []) { out.push(c); all(c, out); } return out; };
const byClass = (root, cls) => all(root).filter((e) => e.className.split(' ').includes(cls));

globalThis.document = makeDoc();
const doc = globalThis.document;
const { CARDS, TOPIC_IDS, VISITOR_CARDS, hubPlan, hubHtml, topicSpec, cardOf, researcherOn } = await import(`../${WEB}/js/evidence.js`);
const { mount, unmount } = await import(`../${WEB}/js/apps/guide-view.js`);
const { t, isResearcherKey, entries } = await import(`../${WEB}/js/strings/index.js`);

// The words a visitor must never read in this section (design doc section 12; the
// visitor-UI lint's words, and the MED finding's "commit gate").
const INTERNAL = /\btiers?\b|\btickets?\b|\border[\s-]+books?\b|\bcommit[\s-]+gate\b|\bT-\d{3,4}\b|[a-z0-9]+_[a-z0-9]+|\b[\w-]+\/[\w./-]+\.(json|js|py|md)\b/i;

// ---- the four cards ---------------------------------------------------------------------
assert.deepEqual(VISITOR_CARDS, ['grading', 'sources', 'liberties', 'living'], 'the four cards, in the design doc\'s order');
assert.deepEqual(VISITOR_CARDS.map((id) => t(`guide-about.card.${id}`)),
  ['How we grade', 'Sources', 'Liberties', 'What lived and grew here'], 'each card is named as the ticket names it');
const filed = CARDS.flatMap((c) => c.topics);
assert.equal(TOPIC_IDS.length, 11, 'the hub has eleven topics');
assert.deepEqual([...filed].sort(), [...TOPIC_IDS].sort(), 'every topic is filed under a card');
assert.equal(new Set(filed).size, filed.length, 'and under one card only');
const research = CARDS.filter((c) => c.researcher);
assert.equal(research.length, 1);
assert.deepEqual(research[0].topics, ['orderbook'], 'the order book, and nothing else, is behind Researcher mode');
assert.equal(cardOf('orderbook'), 'research');
// The design doc's own list for this section: city numbers, fauna, plants, exclusions and
// open questions move under About this destination — onto visitor cards, not the researcher's.
for (const id of ['city', 'fauna', 'plants', 'exclusions', 'uncertain']) {
  assert(VISITOR_CARDS.includes(cardOf(id)), `${id} is on a visitor card`);
}

// ---- each destination keeps all four ------------------------------------------------------
// The omitted topics, as main.js computes them: a topic is offered only by a scene that
// lists the layer it reads (DRAWER_TOPICS, T-1740), read from main.js rather than copied.
const main = read(`${WEB}/js/main.js`);
const literal = /const DRAWER_TOPICS = \{([^}]*)\}/.exec(main);
assert(literal, 'main.js carries DRAWER_TOPICS');
const drawerTopics = Object.fromEntries([...literal[1].matchAll(/(\w+):\s*'(\w+)'/g)].map((m) => [m[1], m[2]]));
assert(Object.keys(drawerTopics).length >= 7 && drawerTopics.orderbook, 'DRAWER_TOPICS read');
const omitFor = (year) => {
  const scene = JSON.parse(read(`data/scenes/${year}.json`));
  const layers = new Set(scene.layers ?? []);
  return Object.keys(drawerTopics).filter((id) => !layers.has(drawerTopics[id]));
};
for (const year of ['1835', '1904', '1812']) {
  const omit = omitFor(year);
  const plan = hubPlan(omit);
  const visitor = plan.filter((c) => !c.researcher);
  assert.deepEqual(visitor.map((c) => c.id), VISITOR_CARDS, `${year}: all four cards`);
  for (const c of visitor) {
    assert(c.topics.length > 0, `${year}: ${c.id} holds a topic`);
    assert(c.topics.every((id) => !omit.includes(id)), `${year}: ${c.id} holds no topic the scene omits`);
  }
  assert.equal(plan.some((c) => c.researcher), !omit.includes('orderbook'), `${year}: a researcher card only where the order book is`);
}
assert.deepEqual(omitFor('1835'), [], '1835 carries every topic');
assert(!hubPlan(omitFor('1904')).some((c) => c.researcher), '1904 has no order book');
assert.deepEqual(hubPlan(omitFor('1904')).find((c) => c.id === 'living').topics, ['ground'], '1904: the ground is what lived and grew here');

// ---- the hub's markup -------------------------------------------------------------------------
const topics = new Map(TOPIC_IDS.map((id) => [id, { ...topicSpec(id), title: id }]));
const html = hubHtml(hubPlan([]), topics);
const sections = [...html.matchAll(/<section class="ev-card" data-card="(\w+)"( data-researcher)?/g)].map((m) => [m[1], !!m[2]]);
assert.deepEqual(sections, [['grading', false], ['sources', false], ['liberties', false], ['living', false], ['research', true]],
  'four visitor cards, then the researcher card, marked');
assert.deepEqual([...html.matchAll(/class="ev-tile" type="button" data-topic="(\w+)"/g)].map((m) => m[1]),
  ['grades', 'city', 'sources', 'liberties', 'exclusions', 'uncertain', 'ground', 'fauna', 'plants', 'population', 'orderbook'],
  'one tile per topic, inside its card, How we grade first');
const visitorHtml = html.split('<section class="ev-card" data-card="research"')[0];
const visible = visitorHtml.replace(/<svg[\s\S]*?<\/svg>/g, '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');
assert(!INTERNAL.test(visible.replace(/\b(grades|city|sources|liberties|exclusions|uncertain|ground|fauna|plants|population)\b/g, '')),
  `no internal word outside the researcher card: ${visible.match(INTERNAL)?.[0]}`);
assert.match(visitorHtml, /class="ev-card-hint">One building&#39;s own sources are on its Sources tab in Inspect\./, 'Sources points to Inspect');
assert.match(visitorHtml, /class="ev-card-hint">One building&#39;s own Liberties are on its Sources tab in Inspect\./, 'Liberties points to Inspect');
assert.match(html, /data-researcher[^>]*>[\s\S]*Reconstructing the town/, 'the researcher card is the order book\'s');

// ---- the string table: visitor strings carry no internal word ---------------------------------
for (const [key, value] of entries().filter(([k]) => k.startsWith('guide-about.'))) {
  if (isResearcherKey(key)) continue;
  assert(!INTERNAL.test(value), `${key} carries an internal word: ${value}`);
}
assert(isResearcherKey('guide-about.researcher.card') && isResearcherKey('guide-about.researcher.topic.orderbook'),
  'the order book\'s words are researcher keys');
assert.match(t('guide-about.researcher.card.line'), /order book/, 'and they may say "order book"');

// ---- the page ------------------------------------------------------------------------------------
const page = read(`${WEB}/index.html`);
for (const id of TOPIC_IDS) assert.match(page, new RegExp(`<div class="ev-topic" data-topic="${id}"`), `${id} keeps its container`);
for (const id of ['evidence-hub', 'city', 'sources', 'liberties', 'liberties-note', 'ground', 'fauna', 'fauna-note', 'plants', 'plants-note',
  'exclusions', 'exclusions-note', 'uncertain', 'uncertain-note', 'population', 'population-note', 'order-book', 'order-book-note']) {
  assert.match(page, new RegExp(`id="${id}"`), `#${id} is kept`);
}
assert.match(page, /<div class="ev-topic" data-topic="orderbook" data-researcher>/, 'the order book\'s topic is marked for Researcher mode');
const tab = /<button class="panel-tab" data-tab="evidence"[^>]*>[\s\S]*?<\/button>/.exec(page)?.[0] ?? '';
assert.match(tab, /data-title="About this destination"/, 'the section\'s head is About this destination');
assert.match(tab, /<span class="tab-label" data-str="guide-about.tab">About<\/span>/, 'its tab says About');
assert.equal(t('guide-about.tab.title'), 'About this destination');
const evidence = page.slice(page.indexOf('<section class="panel-body" data-panel="evidence"'), page.indexOf('<section class="panel-body" data-panel="settings"'));
const shown = evidence.replace(/<!--[\s\S]*?-->/g, '').split('data-topic="orderbook" data-researcher')[0].replace(/<[^>]+>/g, ' ');
assert(!/\bcommit[\s-]+gate\b|\border[\s-]+books?\b|\btickets?\b|\btiers?\b/i.test(shown),
  `the section's own words, outside the order book, name no internal process: ${shown.match(/\bcommit[\s-]+gate\b|\border[\s-]+books?\b|\btickets?\b|\btiers?\b/i)?.[0]}`);
for (const term of ['Attested', 'Inferred', 'Reconstructed']) assert.match(evidence, new RegExp(`<b>${term}</b> —`), `How we grade spells ${term} as locked`);
assert.match(read(`${WEB}/css/skins.css`), /html:not\(\[data-researcher-mode\]\)\s*\[data-researcher\]\s*\{\s*display:\s*none/,
  'a marked element is hidden until Researcher mode is on');
assert.match(read(`${WEB}/js/census.js`), /<div data-researcher><dt>Derived by<\/dt>/, 'the City\'s tool path is for researchers');

// ---- Researcher mode is read off the root ---------------------------------------------------------
assert.equal(researcherOn(doc), false);
doc.documentElement.setAttribute('data-researcher-mode', '');
assert.equal(researcherOn(doc), true);
doc.documentElement.removeAttribute('data-researcher-mode');

// ---- Guide's own block -----------------------------------------------------------------------------
const asked = [];
const el = doc.createElement('div');
doc.body.append(el);
mount(el, { controls: 'keyboard', coarse: false, scene: '1835',
  actions: { aboutCard: (id) => { asked.push(id); return true; }, guideFaq: () => ({ questions: [] }), jauntCatalog: () => [] } });
const block = doc.getElementById('guide-about');
assert(block, 'Guide shows About this destination');
assert.equal(byClass(block, 'nav-k')[0]?.textContent, 'About this destination');
const order = byClass(el, 'nav-block').map((b) => b.id);
assert(order.indexOf('guide-faq') < order.indexOf('guide-about') && order.indexOf('guide-about') < order.indexOf('guide-teachers'),
  `after the questions, before For teachers: ${order.join(', ')}`);
const buttons = byClass(block, 'nav-about-card');
assert.deepEqual(buttons.map((b) => b.dataset.card), [...VISITOR_CARDS, 'research']);
assert.deepEqual(buttons.filter((b) => b.hasAttribute('data-researcher')).map((b) => b.dataset.card), ['research'],
  'only the order book\'s button waits for Researcher mode');
assert.deepEqual(buttons.slice(0, 4).map((b) => byClass(b, 'nav-about-title')[0]?.textContent),
  ['How we grade', 'Sources', 'Liberties', 'What lived and grew here']);
const blockText = buttons.filter((b) => !b.hasAttribute('data-researcher')).map((b) => b.textContent).join(' ')
  + ' ' + byClass(block, 'nav-place')[0]?.textContent + ' ' + byClass(block, 'nav-sub')[0]?.textContent;
assert(!INTERNAL.test(blockText), `the block reads no internal word: ${blockText.match(INTERNAL)?.[0]}`);
for (const b of buttons) b.click();
assert.deepEqual(asked, [...VISITOR_CARDS, 'research'], 'a tap asks the page to open that card');
unmount(el);

// ---- the source list says what kind a source is ----------------------------------------------------
const sources = read(`${WEB}/js/sources.js`);
assert(!/· tier \$\{/.test(sources) && !/'Source tier'/.test(sources) && !/\[DOC\]|\[CONJ\]/.test(sources),
  'no tier number, tier filter or old grade alias on the source list');
const { sourceTag } = await import(`../${WEB}/js/inspect-sources.js`);
assert.equal(sourceTag(3, '1884', '1835'), 'gathered from witnesses', 'Andreas (1884, tier 3) is gathered from witnesses in 1835');

console.log(`test_guide_about: four cards in ${VISITOR_CARDS.length === 4 ? 'every' : 'some'} destination (1835, 1904, 1812), `
  + `${TOPIC_IDS.length} topics each filed once, the order book behind Researcher mode, ids kept, Guide's block opens each card`);
