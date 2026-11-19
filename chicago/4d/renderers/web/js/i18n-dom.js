/**
 * The page in the visitor's language (gap analysis item 15: Spanish), for the words that do not
 * come from the string table: the static markup of index.html and the text a module writes
 * itself. js/strings/index.js loads this only when a language other than English is in force.
 *
 * It reads each text node, and each title / aria-label / placeholder, as a whole string. One the
 * locale's `text` map holds exactly (trimmed) is replaced by its translation, keeping the
 * node's own leading and trailing space; one a locale `pattern` matches is rebuilt from the
 * pattern's words with the matched values put back. Anything else stays as written, so a
 * string nobody translated yet reads in English, never as a key. A MutationObserver does the
 * same for whatever the HUD writes later; a replaced value no longer matches any English
 * entry, so the observer never loops on its own writes.
 *
 * It never touches the world itself (the canvas), the content of inputs, or anything inside
 * an element marked `translate="no"` or `data-no-translate`: a person's name, a quotation
 * already translated by its own layer, a code.
 */
import { localeText, localePatterns } from './strings/index.js';

const ATTRS = ['title', 'aria-label', 'placeholder', 'alt'];
const SKIP = new Set(['SCRIPT', 'STYLE', 'CANVAS', 'TEXTAREA', 'CODE', 'PRE', 'svg', 'SVG']);
let compiled = null;
const seen = new Map();

function patterns() {
  if (compiled) return compiled;
  compiled = [];
  for (const [en, tr] of localePatterns) {
    const names = [];
    const source = en.split(/(\{\w+\})/).map((part) => {
      const m = /^\{(\w+)\}$/.exec(part);
      if (!m) return part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      names.push(m[1]);
      return '(.+?)';
    }).join('');
    compiled.push({ re: new RegExp(`^${source}$`), names, tr });
  }
  return compiled;
}

/** `text` in the visitor's language, or null when there is nothing to change. */
export function translate(text) {
  if (!text) return null;
  const core = text.trim();
  if (!core || !/[A-Za-z]/.test(core)) return null;
  let out = localeText.get(core);
  if (out === undefined && seen.has(core)) out = seen.get(core);
  else if (out === undefined) {
    for (const { re, names, tr } of patterns()) {
      const m = re.exec(core);
      if (!m) continue;
      const vars = Object.fromEntries(names.map((n, i) => [n, localeText.get(m[i + 1]) ?? m[i + 1]]));
      out = tr.replace(/\{(\w+)\}/g, (s, n) => vars[n] ?? s);
      break;
    }
    // A line put together from parts ("fact — its source", "renderer · 8 GB · 4 cores") reads
    // part by part, when no entry holds it whole and at least one part is held.
    if (out === undefined && /\s[—·]\s/.test(core)) {
      const parts = core.split(/(\s[—·]\s)/);
      let changed = false;
      const done = parts.map((p, i) => {
        if (i % 2) return p;
        const got = localeText.get(p.trim());
        if (got === undefined) return p;
        changed = true;
        return got;
      });
      if (changed) out = done.join('');
    }
    // A HUD line rewritten every frame ("51 MB/s") is tried against the patterns once, not
    // each frame; the memo is dropped whole when it grows past a few thousand lines.
    if (seen.size > 4000) seen.clear();
    seen.set(core, out);
  }
  if (out === undefined || out === core) return null;
  if (core === text) return out;
  const lead = text.slice(0, text.indexOf(core));
  return lead + out + text.slice(lead.length + core.length);
}

function skipped(el) {
  for (let e = el; e && e.nodeType === 1; e = e.parentNode) {
    if (SKIP.has(e.nodeName) || e.getAttribute('translate') === 'no' || e.hasAttribute('data-no-translate')) return true;
  }
  return false;
}

function doText(node) {
  const parent = node.parentNode;
  if (!parent || skipped(parent)) return;
  const out = translate(node.nodeValue);
  if (out !== null) node.nodeValue = out;
}

function doAttrs(el) {
  if (skipped(el)) return;
  for (const a of ATTRS) {
    const v = el.getAttribute(a);
    if (!v) continue;
    const out = translate(v);
    if (out !== null) el.setAttribute(a, out);
  }
  if (el.nodeName === 'INPUT' && (el.type === 'button' || el.type === 'submit') && el.value) {
    const out = translate(el.value);
    if (out !== null) el.value = out;
  }
}

/** Translate everything under `root` once. */
export function translateTree(root) {
  if (!root) return;
  if (root.nodeType === 3) { doText(root); return; }
  if (root.nodeType !== 1 && root.nodeType !== 9 && root.nodeType !== 11) return;
  if (root.nodeType === 1) { if (skipped(root)) return; doAttrs(root); }
  const walker = root.ownerDocument
    ? root.ownerDocument.createTreeWalker(root, 5 /* SHOW_ELEMENT | SHOW_TEXT */)
    : root.createTreeWalker(root, 5);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (n.nodeType === 3) doText(n); else doAttrs(n);
  }
}

let observer = null;
export function start(doc = globalThis.document) {
  if (!doc?.documentElement || observer) return;
  const run = () => {
    translateTree(doc.documentElement);
    if (doc.title) { const out = translate(doc.title); if (out !== null) doc.title = out; }
    observer = new MutationObserver((records) => {
      for (const r of records) {
        if (r.type === 'characterData') doText(r.target);
        else if (r.type === 'attributes') { if (r.target.nodeType === 1) doAttrs(r.target); }
        else for (const n of r.addedNodes) translateTree(n);
      }
    });
    observer.observe(doc.documentElement, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS });
  };
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', run, { once: true }); else run();
}
