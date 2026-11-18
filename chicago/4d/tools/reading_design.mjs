#!/usr/bin/env node
/**
 * reading_design.mjs — every line a building's Inspect Design tab shows (T-3645).
 *
 *   node tools/reading_design.mjs <scene>     # prints {"lines": [...]} for tools/reading_levels.py
 *
 * The Design tab (inspect-design.js `designModel`, drawn by `renderDesign`) shows the written
 * guide (style-guide.js: its lead, look-for, the five parts and the basis line), the style
 * module's card where one is named (description, cues, compare) and the record's own "On this
 * house" items. These are the strings it draws, from the same call the tab makes, so a retelling
 * keyed by one finds its line. Names, chips and other labels are not prose and are left out.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const APP = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const JS = path.join(APP, 'renderers/web/js');
const { designModel } = await import(path.join(JS, 'inspect-design.js'));

const scene = process.argv[2];
const inspectPath = path.join(APP, 'data/inspect', `${scene}.json`);
const inspect = existsSync(inspectPath) ? JSON.parse(readFileSync(inspectPath, 'utf8')) : {};
const lines = new Set();
const add = (t) => { if (typeof t === 'string' && t.trim().length > 1) lines.add(t.trim()); };
const card = (c) => { if (!c) return; add(c.description?.text); for (const x of c.cues ?? []) add(x.text); };
const dir = path.join(APP, 'data/sidecars', scene);
if (existsSync(dir)) {
  for (const f of readdirSync(dir).sort()) {
    if (!f.endsWith('.json')) continue;
    const s = JSON.parse(readFileSync(path.join(dir, f), 'utf8'));
    if (!s || typeof s !== 'object' || !s.placement || !s.id) continue;
    const m = designModel({ sum: inspect.summaries?.[s.id] ?? null, sidecar: s, styles: inspect.styles ?? null, scene });
    for (const l of m.guide.lead ?? []) add(l.text);
    for (const l of m.guide.look ?? []) { add(l.text); add(l.detail); }
    for (const p of m.guide.parts ?? []) for (const l of p.lines ?? []) add(l.text);
    add(m.guide.basis?.text);
    if (m.style) {
      card(m.style);
      for (const c of m.style.compare ?? []) { add(c.text); card(c.card); }
    }
    for (const h of m.hot.items ?? []) { add(h.text); add(h.detail); }
  }
}
process.stdout.write(JSON.stringify({ scene, lines: [...lines].sort() }));
