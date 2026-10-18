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
  const about = page.slice(page.indexOf('id="s-about"'), page.indexOf('</div>', page.indexOf('id="s-researcher"')));
  assert.match(about, /<input type="checkbox" id="s-researcher">/, 'the switch is in Settings › About');
  assert.doesNotMatch(about, /id="s-researcher"[^>]*checked/, 'and is not checked in the markup');
  assert.match(page, /<span class="research-badge" id="research-badge" data-researcher data-str="research.badge">RESEARCHER<\/span>/,
    'a small RESEARCHER label, shown only while it is on');
  const whys = [...page.matchAll(/<details class="why">([\s\S]*?)<\/details>/g)].map((m) => m[1]);
  assert.equal(whys.length, 3, 'three "Why this default" essays');
  for (const w of whys) {
    const short = w.match(/<p class="legend-note" data-visitor-only data-str="(research\.why\.\w+)">/);
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
  const evidence = fs.readFileSync(path.join(WEB, 'js', 'evidence.js'), 'utf8');
  assert.match(evidence, /t\.el\.hasAttribute\('data-researcher'\) \? ' data-researcher'/, 'a Researcher-mode hub topic\'s tile is marked too');
}

console.log('RESEARCHER MODE PASS — off by default, remembered per device, the full essays in place while on, and a ticket only as a link behind plain words');
