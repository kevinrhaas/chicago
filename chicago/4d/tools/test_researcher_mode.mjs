#!/usr/bin/env node
// T-2657 (NAV-S03): Researcher mode, a Settings › About switch, off by default and remembered
// per device. While it is on, <html data-researcher-mode> shows every [data-researcher]
// element and hides every [data-visitor-only] stand-in (css/skins.css). The owner, 2026-10-18:
// no internal ticket number, record id or file path in any mode, and a ticket only as a link
// behind plain words. This reads, with no browser: the switch's state and storage, the ticket
// link, and the page's markup and stylesheet. The rendered page is the smoke's, part 13.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createResearcherMode, readMode, ticketUrl, ticketLinkHtml, STORAGE_KEY, MODE_ATTR }
  from '../renderers/web/js/researcher.js';
import { t } from '../renderers/web/js/strings/index.js';
import { visitorTextProblems } from '../renderers/web/js/fallback-summary.js';
import { hubHtml, hubPlan, TOPIC_IDS } from '../renderers/web/js/evidence.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WEB = path.join(ROOT, 'renderers', 'web');
const json = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));

// ---- the switch: off by default, on and off, remembered, survives no storage --------------
function fakeDoc() {
  const attrs = new Map();
  const box = { checked: false, handlers: [], addEventListener(type, fn) { if (type === 'change') this.handlers.push(fn); } };
  return {
    box, attrs,
    documentElement: { setAttribute: (k, v) => attrs.set(k, v), removeAttribute: (k) => attrs.delete(k) },
    getElementById: (id) => (id === 's-researcher' ? box : null),
  };
}
function fakeStorage() {
  const m = new Map();
  return { m, getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) };
}
{
  const store = fakeStorage();
  const doc = fakeDoc();
  const mode = createResearcherMode({ doc, storage: store });
  assert.equal(mode.on, false, 'off by default');
  assert.equal(doc.attrs.has(MODE_ATTR), false, 'and the root carries no attribute');
  assert.equal(doc.box.checked, false, 'the switch reads off');
  let heard = [];
  mode.onChange((on) => heard.push(on));
  doc.box.checked = true; doc.box.handlers.forEach((fn) => fn());
  assert.equal(mode.on, true, 'the switch turns it on');
  assert.equal(doc.attrs.has(MODE_ATTR), true, 'the root carries data-researcher-mode');
  assert.equal(store.m.get(STORAGE_KEY), 'on', 'remembered on this device');
  // A reload: a new page reads the same storage.
  const doc2 = fakeDoc();
  const again = createResearcherMode({ doc: doc2, storage: store });
  assert.equal(again.on, true, 'it persists across a reload');
  assert.equal(doc2.attrs.has(MODE_ATTR), true, 'and the reloaded page opens with it on');
  assert.equal(doc2.box.checked, true, 'with the switch on');
  mode.set(false);
  assert.equal(doc.attrs.has(MODE_ATTR), false, 'turning it off clears the attribute');
  assert.equal(store.m.has(STORAGE_KEY), false, 'and forgets it on this device');
  assert.deepEqual(heard, [true, false], 'listeners hear each change once');
  mode.set(false);
  assert.deepEqual(heard, [true, false], 'and not a no-op');
  assert.equal(createResearcherMode({ doc: fakeDoc(), storage: fakeStorage() }).on, false, 'a fresh device is off');
  const broken = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); }, removeItem() { throw new Error('denied'); } };
  assert.equal(readMode(broken), false, 'storage that throws reads off');
  const b = createResearcherMode({ doc: fakeDoc(), storage: broken });
  assert.equal(b.set(true), true, 'and the switch still works for this page');
  assert.equal(createResearcherMode({ doc: null, storage: null }).toggle(), true, 'no page, no storage: no throw');
}

// ---- a ticket, only as a link behind plain words ----------------------------------------
{
  // The tickets clone (tools/tickets.sh) writes tickets.json; a tree without it reads a fixture.
  const tickets = fs.existsSync(path.join(ROOT, 'tickets/tickets.json')) ? json('tickets/tickets.json')
    : { tickets: [{ id: 'T-2657', path: 'T-2500-2749/T-2657-researcher-mode-a-settings-about-switch-off-by-d.md' }] };
  const one = tickets.tickets.find((x) => x.id === 'T-2657') ?? tickets.tickets[0];
  const url = ticketUrl(one.path);
  assert.equal(url, `https://github.com/kevinrhaas/chicago-tickets/blob/main/${one.path}`, 'a ticket opens in the tickets repository');
  assert.ok(tickets.tickets.every((x) => !x.path || ticketUrl(x.path)), 'every path tickets.json gives makes an address');
  assert.equal(ticketUrl('../etc/passwd'), '', 'and nothing else does');
  assert.equal(ticketUrl('javascript:alert(1)'), '');
  const html = ticketLinkHtml({ path: one.path });
  assert.match(html, /^<a class="research-link" data-researcher href="https:\/\/github\.com\/kevinrhaas\/chicago-tickets\/blob\/main\/[^"]+" target="_blank" rel="noopener">How this was decided<\/a>$/,
    'Researcher mode only, opening in a new tab');
  const label = html.replace(/<[^>]+>/g, '');
  assert.deepEqual(visitorTextProblems(label), [], 'its label is plain words');
  assert.doesNotMatch(label, /T-\d|ticket/i, 'with no number and no ticket language');
  assert.match(ticketLinkHtml({ path: one.path, label: 'record' }), />The work record<\/a>$/);
  assert.equal(ticketLinkHtml({ path: '' }), '', 'no address, no link');
}

// ---- the page and the stylesheet --------------------------------------------------------
{
  const page = fs.readFileSync(path.join(WEB, 'index.html'), 'utf8');
  // T-3022: the switch is Expert research, the first group of Settings.
  const group = page.slice(page.indexOf('id="s-research"'), page.indexOf('</div>', page.indexOf('id="s-researcher"')));
  assert(page.indexOf('id="s-research"') < page.indexOf('id="s-display"'), 'its group leads Settings, ahead of Display');
  assert.match(group, /<input type="checkbox" id="s-researcher">/, 'the switch is in Settings › Research');
  assert.match(group, /data-str="research.switch">Expert research</, 'named Expert research');
  assert.doesNotMatch(group, /id="s-researcher"[^>]*checked/, 'and is not checked in the markup');
  assert.match(page, /<span class="research-badge" id="research-badge" data-researcher data-str="research.badge">RESEARCHER<\/span>/,
    'a small RESEARCHER label, shown only while it is on');
  // T-2658: each essay's fold is Researcher mode's, and a visitor's one line and "Why?"
  // bubble (its own test, test_short_why.mjs) stand directly before it.
  const whys = [...page.matchAll(/<div class="why-line" data-visitor-only>([\s\S]*?)<\/div>\s*<details class="why" data-researcher>([\s\S]*?)<\/details>/g)]
    .map((m) => m[1] + m[2]);
  assert.equal(whys.length, 3, 'three "Why this default" essays');
  assert.equal(page.split('<details class="why"').length - 1, 3, 'and no other');
  for (const w of whys) {
    const short = w.match(/<span class="why-text" id="[\w-]+" hidden data-str="(research\.why\.\w+)">/);
    assert.ok(short, 'each has a short visitor hint');
    const words = t(short[1]).split(/\s+/).length;
    assert.ok(words <= 40, `${short[1]} is ${words} words (40 at most)`);
    const full = w.match(/<p class="legend-note why-full" id="[\w-]+" data-researcher>([\s\S]*?)<\/p>/);
    assert.ok(full && full[1].split(/\s+/).length > 40, 'and the full essay, for Researcher mode');
    assert.deepEqual(visitorTextProblems(full[1]), [], 'which carries no id, path or ticket number');
  }
  const css = fs.readFileSync(path.join(WEB, 'css', 'skins.css'), 'utf8');
  assert.match(css, /html:not\(\[data-researcher-mode\]\) \[data-researcher\] \{ display: none !important; \}/, 'off, research is hidden');
  assert.match(css, /html\[data-researcher-mode\] \[data-visitor-only\] \{ display: none !important; \}/, 'on, its stand-ins are');
  // The hub (T-2667's hubHtml): the order book's card is Researcher mode's, and a topic marked
  // `data-researcher` marks its own tile, whichever card it is filed under.
  const topic = (id, researcher) => [id, { id, title: id, gloss: 'g', icon: '',
    el: { hasAttribute: (a) => researcher && a === 'data-researcher' } }];
  const topics = new Map([topic('grades', false), topic('city', true), topic('orderbook', true)]);
  const hub = hubHtml([{ id: 'grading', researcher: false, topics: ['grades', 'city'], title: 'A', line: 'a' },
    { id: 'research', researcher: true, topics: ['orderbook'], title: 'B', line: 'b' }], topics);
  assert.match(hub, /<section class="ev-card" data-card="research" data-researcher/, 'the order book\'s card is Researcher mode\'s');
  assert.match(hub, /data-topic="orderbook" data-researcher /, 'and so is its tile');
  assert.match(hub, /data-topic="city" data-researcher /, 'a Researcher-mode topic\'s tile is marked too, in a visitor\'s card');
  assert.match(hub, /data-topic="grades" aria-label/, 'a visitor\'s topic\'s tile is not');
  assert.doesNotMatch(hub, /data-card="grading" data-researcher/, 'nor its card');
  const real = hubHtml(hubPlan(), new Map(TOPIC_IDS.map((id) => [id, { id, title: id, gloss: '', icon: '' }])));
  assert.match(real, /<section class="ev-card" data-card="research" data-researcher[\s\S]*?data-topic="orderbook"/,
    'in the committed plan, the order book\'s tile sits in the Researcher-mode card');
  const page2 = fs.readFileSync(path.join(WEB, 'index.html'), 'utf8');
  assert.match(page2, /<div class="ev-topic" data-topic="orderbook" data-researcher>/, 'and its topic is marked in the page');
}

// ---- T-3022: the building card folded into Inspect, as its Research tab ---------------------
{
  // The card's own research, for Inspect: one builder, the card's head without its title row.
  globalThis.document ??= { documentElement: { classList: { add() {}, remove() {} } } };
  const { createPopup } = await import('../renderers/web/js/popup.js');
  const root = { addEventListener() {}, setAttribute() {}, removeAttribute() {}, dispatchEvent() {}, style: {} };
  const sidecar = json('data/sidecars/1904/glessner_house.json');
  const r = createPopup(root).sections({ id: 'glessner_house', sidecar }).research;
  assert(r && r.head && r.facts && r.evidence && r.record, 'sections() carries the card\'s research for Inspect');
  assert.doesNotMatch(r.head, /pop-title-row|data-close/, 'without the card\'s own title row and Close');
  assert.match(r.evidence, /Attributes and evidence[\s\S]*<ol class="cites">/, 'Sources: the attributes and the citations');
  assert.match(r.record, /pop-foot/, 'Record: the dossier and phase line');
  // Inspect draws Research for every building, marked for the mode, so the switch shows or
  // hides it in place; a visitor never lands on it.
  const view = fs.readFileSync(path.join(WEB, 'js', 'apps', 'inspect-view.js'), 'utf8');
  assert.match(view, /\['research', 'Research'\]\]/, 'Inspect has a Research tab, last');
  assert.match(view, /if \(EXPERT_TABS\.has\(key\)\) b\.setAttribute\('data-researcher', ''\)/, 'marked for Expert research');
  assert.match(view, /if \(EXPERT_TABS\.has\(key\) && !expertOn\(root\.ownerDocument\)\) key = 'overview'/, 'and never selected with it off');
  // A building the visitor opens opens in Inspect, not the floating card.
  const main = fs.readFileSync(path.join(WEB, 'js', 'main.js'), 'utf8');
  assert.match(main, /if \(by === 'hand' && loaded\.registry\.get\(hit\.record\.id\) && openBuilding\(hit\.record\.id\)\) return hit;/,
    'a click or tap on a building opens Inspect');
  assert.match(main, /onArrive: \(id\) => \{ hud\.setPanel\(false\); openBuilding\(id\);/, 'and so does an arrival');
  assert.match(main, /onInspect: \(id\) => openBuilding\(id\),/, 'and Home\'s Inspect key');
}

console.log('RESEARCHER MODE PASS — off by default, remembered per device, the full essays in place while on, and a ticket only as a link behind plain words; Expert research adds Inspect\'s Research tab, the card folded in');
