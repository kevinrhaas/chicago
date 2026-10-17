#!/usr/bin/env node
// T-2662 (NAV-804): the Guide's glossary and questions, and a locked term's first appearance
// explained on tap. Mounts the real Guide screen (apps/guide-view.js) and the real term
// marker (term-tips.js) over a small hand-made DOM with text nodes, against the committed
// data/guide/ files and the string table. The smoke (part 12) opens Guide and taps a term.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const glossary = JSON.parse(read('data/guide/glossary.json'));
const faq = JSON.parse(read('data/guide/faq.json'));

// ---- a small DOM with text nodes --------------------------------------------------------
function makeDoc() {
  const listeners = {};
  const text = (data) => ({
    nodeType: 3, data, parentNode: null,
    get textContent() { return this.data; },
    get parentElement() { return this.parentNode; },
    splitText(at) {
      const rest = text(this.data.slice(at)); this.data = this.data.slice(0, at);
      const p = this.parentNode; const i = p.childNodes.indexOf(this); rest.parentNode = p; p.childNodes.splice(i + 1, 0, rest); return rest;
    },
    replaceWith(n) { const p = this.parentNode; const i = p.childNodes.indexOf(this); n.parentNode = p; p.childNodes[i] = n; this.parentNode = null; },
  });
  const el = (tag) => {
    const fns = {};
    const e = {
      nodeType: 1, tagName: tag.toUpperCase(), childNodes: [], parentNode: null, attrs: {}, dataset: {}, style: {}, hidden: false,
      className: '', id: '', type: '', title: '', isConnected: true, offsetHeight: 40,
      get children() { return this.childNodes.filter((c) => c.nodeType === 1); },
      get parentElement() { return this.parentNode; },
      get textContent() { return this.childNodes.map((c) => c.textContent).join(''); },
      set textContent(v) { this.childNodes = []; if (v !== '') this.append(String(v)); },
      get ownerDocument() { return doc; },
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      append(...cs) { for (const c of cs) { const n = typeof c === 'string' ? text(c) : c; n.parentNode = e; e.childNodes.push(n); } },
      replaceChildren(...cs) { e.childNodes = []; e.append(...cs); },
      addEventListener(t, f) { (fns[t] ??= []).push(f); },
      click() { for (const f of fns.click ?? []) f({ stopPropagation() {}, preventDefault() {} }); },
      closest(sel) {
        const tags = sel.split(',').map((s) => s.trim()).filter((s) => /^[a-z]+$/.test(s)).map((s) => s.toUpperCase());
        for (let n = e; n && n.nodeType === 1; n = n.parentNode) {
          if (tags.includes(n.tagName) || (sel.includes('.locked-term') && n.className.split(' ').includes('locked-term'))) return n;
        }
        return null;
      },
      contains(n) { for (let x = n; x; x = x.parentNode) if (x === e) return true; return false; },
      getBoundingClientRect: () => ({ left: 20, top: 100, bottom: 120, right: 120 }),
      focus() {},
    };
    e.classList = { toggle(c, on) { const set = new Set(e.className.split(' ').filter(Boolean)); if (on) set.add(c); else set.delete(c); e.className = [...set].join(' '); },
      contains: (c) => e.className.split(' ').includes(c), add(c) { this.toggle(c, true); }, remove(c) { this.toggle(c, false); } };
    return e;
  };
  const all = (root, out = []) => { for (const c of root.childNodes ?? []) { out.push(c); all(c, out); } return out; };
  const doc = {
    body: null, defaultView: { innerWidth: 390, innerHeight: 844 },
    createElement: el,
    createTreeWalker(root) { const nodes = all(root).filter((n) => n.nodeType === 3); let i = -1; return { nextNode: () => nodes[++i] ?? null }; },
    addEventListener(t, f) { (listeners[t] ??= []).push(f); },
  };
  doc.body = el('body');
  return doc;
}
globalThis.document = makeDoc();
const doc = globalThis.document;
const { LOCKED_TERMS } = await import('../renderers/web/js/strings/terms.js');
const { mount, unmount } = await import('../renderers/web/js/apps/guide-view.js');
const { markTerms, meaningOf, markedTerms, resetTerms } = await import('../renderers/web/js/term-tips.js');
const walk = (root, out = []) => { for (const c of root.children ?? []) { out.push(c); walk(c, out); } return out; };
const byId = (root, id) => walk(root).find((e) => e.id === id);

// ---- the glossary: every locked term with its meaning, from the string table ---------------------
assert.deepEqual(LOCKED_TERMS.map(([t, m]) => ({ term: t, meaning: m })), glossary.terms.map(({ term, meaning }) => ({ term, meaning })),
  'the string table and data/guide/glossary.json agree, term for term');
const screen = doc.createElement('div');
mount(screen, { controls: 'touch', coarse: true, actions: { guideFaq: async () => faq, onControls: () => () => {} } });
await new Promise((r) => setTimeout(r, 0));
const g = byId(screen, 'guide-glossary');
const dts = walk(g).filter((e) => e.tagName === 'DT').map((e) => e.textContent);
const dds = walk(g).filter((e) => e.tagName === 'DD').map((e) => e.textContent);
assert.deepEqual(dts, ['Attested', 'Inferred', 'Reconstructed', 'Confidence view', 'Liberties', 'Sources', 'Jaunts'], 'every locked term, exactly, in order');
assert.deepEqual(dds, glossary.terms.map((t) => t.meaning), 'each with its one line');
assert(/Attested A source says so/.test(g.textContent), 'a term and its line read apart');

// ---- the questions: both, each at most 60 words ----------------------------------------------
const f = byId(screen, 'guide-faq');
const items = walk(f).filter((e) => e.tagName === 'DETAILS');
assert.deepEqual(items.map((d) => d.children[0].textContent), ['Is this real?', 'What does Reconstructed mean?']);
for (const d of items) {
  const answer = d.children[1].textContent;
  assert(answer.split(/\s+/).filter(Boolean).length <= 60, `60 words or fewer: ${answer}`);
}
assert.equal(items[0].children[1].textContent, faq.questions[0].a, 'the answer as written');
assert(byId(screen, 'guide-controls'), 'the controls sheet is still first');
unmount(screen);
// The file unreadable: Guide says so, and the glossary still stands.
const offline = doc.createElement('div');
mount(offline, { controls: 'pointerlock', actions: { guideFaq: async () => { throw new Error('404'); } } });
await new Promise((r) => setTimeout(r, 0));
assert.match(byId(offline, 'guide-faq').textContent, /could not be read just now/);
assert.equal(walk(byId(offline, 'guide-glossary')).filter((e) => e.tagName === 'DT').length, 7);
unmount(offline);

// ---- a term's first appearance, tappable for its line --------------------------------------------
resetTerms();
const intro = doc.createElement('p');
intro.append('Destination locked: Chicago, 1 July 1835. Reconstructed from the sources under Sources.');
doc.body.append(intro);
assert.deepEqual(markTerms(intro), ['Reconstructed', 'Sources'], 'the intro marks Reconstructed and Sources');
assert.equal(intro.textContent, 'Destination locked: Chicago, 1 July 1835. Reconstructed from the sources under Sources.', 'the words are unchanged');
const btn = walk(intro).find((e) => e.dataset.locked === 'Reconstructed');
assert(btn && btn.tagName === 'BUTTON' && btn.className === 'locked-term', 'it is a button');
assert(!walk(intro).some((e) => e.dataset.locked === 'sources'), 'lower-case "sources" is a word, not the term');
btn.click();
const tip = walk(doc.body).find((e) => e.id === 'term-tip');
assert(tip && !tip.hidden, 'a tap shows the bubble');
assert.equal(tip.textContent, `Reconstructed ${meaningOf('Reconstructed')}`, 'with the term and its line');
assert.equal(btn.getAttribute('aria-expanded'), 'true');
btn.click();
assert.equal(tip.hidden, true, 'a second tap puts it away');
// Only the first appearance: a later one is left as words.
const later = doc.createElement('p');
later.append('Most buildings are Reconstructed. Confidence view hides them.');
doc.body.append(later);
assert.deepEqual(markTerms(later), ['Confidence view'], 'Reconstructed is already marked; Confidence view is new');
// Inside a control a tap already means something: never marked there.
const label = doc.createElement('label');
label.append('Attested');
doc.body.append(label);
assert.deepEqual(markTerms(label), [], 'not inside a label or button');
assert.deepEqual(markedTerms().sort(), ['Confidence view', 'Reconstructed', 'Sources']);

// ---- the page --------------------------------------------------------------------------------
const main = read('renderers/web/js/main.js');
assert(/markTerms\(document\.getElementById\('nav-home'\)\)/.test(main) && /data-topic="liberties"\] \.ev-topic-title/.test(main));
assert(/guideFaq: \(\) => \(guideFaq \?\?= fetch\(new URL\('guide\/faq\.json'/.test(main), 'the questions are read when Guide opens, never at boot');
assert(/markTerms\(gate\.querySelector\('\.welcome-intro'\)\)/.test(read('renderers/web/js/welcome.js')));
assert(/cp -f data\/guide\/\*\.json "\$SITE\/data\/guide\/"/.test(read('tools/publish.sh')), 'publish ships the Guide\'s files');

console.log('test_guide_glossary: seven locked terms with their lines, two answers within 60 words, and first appearances explained on tap');
