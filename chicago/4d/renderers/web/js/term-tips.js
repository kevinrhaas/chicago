/**
 * Locked terms, explained on tap (T-2662, design doc section 03: "Each one gets a one-line
 * plain meaning wherever it first appears on a screen (shown on tap and in the Guide
 * glossary)").
 *
 * `markTerms(el)` finds, in the text of `el`, the first appearance on the page of each
 * locked term — spelled exactly, as a whole word — and makes it a small button that shows
 * the term's meaning in a bubble. A term already marked elsewhere on the page is left
 * alone, and so is text inside a control (a label, a button, a link, a field), where a tap
 * already means something else. The meanings are the string table's (strings/terms.js,
 * held equal to data/guide/glossary.json by tools/check_strings.py and check_guide.py).
 */
import { LOCKED_TERMS } from './strings/terms.js';

const MEANING = new Map(LOCKED_TERMS);
const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
// Longest first, so "Confidence view" is found whole.
const TERM_RE = new RegExp(`\\b(${[...MEANING.keys()].sort((a, b) => b.length - a.length).map(escape).join('|')})\\b`);
const INSIDE_CONTROL = 'button, a, label, input, select, textarea, summary, [role="button"], [role="tab"], [contenteditable]';

// term -> its button; a button its text has since replaced no longer counts.
const marked = new Map();
const isMarked = (term) => !!marked.get(term)?.isConnected;
let bubble = null;
let openFor = null;

/** The meaning of a locked term, or '' for anything else. */
export const meaningOf = (term) => MEANING.get(term) ?? '';

function ensureBubble(doc) {
  if (bubble?.isConnected) return bubble;
  bubble = doc.createElement('div');
  bubble.id = 'term-tip';
  bubble.className = 'term-tip';
  bubble.setAttribute('role', 'status');
  bubble.hidden = true;
  doc.body.append(bubble);
  doc.addEventListener('pointerdown', (e) => {
    if (!bubble.hidden && !bubble.contains(e.target) && e.target !== openFor) hideTerm();
  }, true);
  doc.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !bubble.hidden) { hideTerm(); openFor?.focus?.(); } }, true);
  return bubble;
}

/** Show `term`'s meaning beside `anchor`. */
export function showTerm(anchor, term) {
  const doc = anchor.ownerDocument;
  const b = ensureBubble(doc);
  b.replaceChildren();
  const name = doc.createElement('strong');
  name.textContent = term;
  b.append(name, ' ', meaningOf(term));
  b.hidden = false;
  openFor = anchor;
  anchor.setAttribute('aria-expanded', 'true');
  const r = anchor.getBoundingClientRect();
  const view = doc.defaultView;
  const width = Math.min(280, view.innerWidth - 32);
  b.style.width = `${width}px`;
  b.style.left = `${Math.max(16, Math.min(r.left, view.innerWidth - width - 16))}px`;
  const below = r.bottom + 8;
  b.style.top = `${below + 80 > view.innerHeight ? Math.max(16, r.top - 8 - b.offsetHeight) : below}px`;
}

export function hideTerm() {
  if (!bubble) return;
  bubble.hidden = true;
  openFor?.setAttribute('aria-expanded', 'false');
}

/** Make the first appearance of each locked term inside `el` tappable. Returns the terms marked. */
export function markTerms(el) {
  if (!el) return [];
  const doc = el.ownerDocument;
  const got = [];
  const walker = doc.createTreeWalker(el, 4 /* NodeFilter.SHOW_TEXT */);
  const texts = [];
  for (let n = walker.nextNode(); n; n = walker.nextNode()) texts.push(n);
  for (const text of texts) {
    if (text.parentElement?.closest(`${INSIDE_CONTROL}, .locked-term`)) continue;
    let node = text;
    for (;;) {
      const m = TERM_RE.exec(node.data);
      if (!m) break;
      const term = m[1];
      if (isMarked(term)) {
        // Look past an already-marked term for another in the same text.
        const rest = node.splitText(m.index + term.length);
        node = rest;
        continue;
      }
      const after = node.splitText(m.index);
      const rest = after.splitText(term.length);
      const button = doc.createElement('button');
      button.type = 'button';
      button.className = 'locked-term';
      button.dataset.locked = term; // data-locked: which locked term
      button.setAttribute('aria-expanded', 'false');
      button.setAttribute('aria-controls', 'term-tip');
      button.title = `What ${term} means`;
      button.textContent = term;
      button.addEventListener('click', (e) => {
        e.stopPropagation();
        if (openFor === button && bubble && !bubble.hidden) hideTerm(); else showTerm(button, term);
      });
      after.replaceWith(button);
      marked.set(term, button);
      got.push(term);
      node = rest;
    }
  }
  return got;
}

/** Harness only: forget which terms are marked. */
export function resetTerms() { marked.clear(); hideTerm(); }
export const markedTerms = () => [...marked.keys()].filter(isMarked);
