#!/usr/bin/env node
/**
 * reading_why.mjs — every "why" a building's floating card folds away (T-3645).
 *
 *   node tools/reading_why.mjs <scene>     # prints {"notes": [...]} for tools/reading_levels.py
 *
 * The floating card (popup.js) qualifies each value with its reasoning behind a `why` button
 * (`noteToggle`): the claim's own note, in the record's own words. Its Design, Story and People
 * sections and its research panes (which Inspect's Research tab shows too) are built here by
 * the card's own `sections`, with the scene's reader overlay, so the strings are the strings the
 * card shows, and a retelling keyed by one finds its note.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const APP = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const JS = path.join(APP, 'renderers/web/js');
// popup.js reads the page's document only to draw; the strings need none of it.
const inert = { innerHTML: '', removeAttribute() {}, setAttribute() {}, addEventListener() {}, querySelector() { return null; },
  querySelectorAll() { return []; }, style: { setProperty() {} }, classList: { add() {}, remove() {} }, dataset: {} };
globalThis.document ??= { documentElement: { classList: { add() {}, remove() {} } }, getElementById() { return null; }, addEventListener() {} };
const { createPopup } = await import(path.join(JS, 'popup.js'));

const scene = process.argv[2];
const popup = createPopup(inert, {});
const overlay = path.join(APP, 'data/reader', `structures_${scene}.json`);
if (existsSync(overlay)) popup.setReader(JSON.parse(readFileSync(overlay, 'utf8')));
const unescape = (t) => t.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
const notes = new Set();
const dir = path.join(APP, 'data/sidecars', scene);
if (existsSync(dir)) {
  for (const f of readdirSync(dir).sort()) {
    if (!f.endsWith('.json')) continue;
    const s = JSON.parse(readFileSync(path.join(dir, f), 'utf8'));
    if (!s || typeof s !== 'object' || !s.placement || !s.id) continue;
    const sec = popup.sections({ id: s.id, sidecar: s });
    const html = [sec.design, sec.story, sec.people, sec.research?.evidence, sec.research?.record].filter(Boolean).join('\n');
    for (const m of html.matchAll(/<span class="attr-note" data-note hidden>([^<]*)<\/span>/g)) {
      const t = unescape(m[1]).trim();
      if (t.length > 1) notes.add(t);
    }
  }
}
process.stdout.write(JSON.stringify({ scene, notes: [...notes].sort() }));
