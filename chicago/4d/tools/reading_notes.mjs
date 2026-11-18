#!/usr/bin/env node
/**
 * reading_notes.mjs — every evidence note a building's Details tab shows (T-3645).
 *
 *   node tools/reading_notes.mjs <scene>     # prints {"notes": [...]} for tools/reading_levels.py
 *
 * Inspect's Details tab (inspect-sources.js `detailsPaneHtml`) lists a building's facts by
 * grade, each with its "Why": the claim's own note, shown in the record's own words where it
 * passes `clean` (no ticket number, record id or file path) and withheld where it does not.
 * The facts are `buildingFacts(sidecar, summary)`, the same call the tab makes, so the strings
 * here are the strings the tab shows, and a retelling keyed by one finds its line.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const APP = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const JS = path.join(APP, 'renderers/web/js');
const { buildingFacts } = await import(path.join(JS, 'inspect-sources.js'));
const { clean } = await import(path.join(JS, 'fallback-summary.js'));

const scene = process.argv[2];
const inspectPath = path.join(APP, 'data/inspect', `${scene}.json`);
const summaries = existsSync(inspectPath) ? JSON.parse(readFileSync(inspectPath, 'utf8')).summaries ?? {} : {};
const dir = path.join(APP, 'data/sidecars', scene);
const notes = new Set();
if (existsSync(dir)) {
  for (const f of readdirSync(dir).sort()) {
    if (!f.endsWith('.json')) continue;
    const s = JSON.parse(readFileSync(path.join(dir, f), 'utf8'));
    if (!s || typeof s !== 'object' || !s.placement || !s.id) continue;
    for (const fact of buildingFacts(s, summaries[s.id] ?? null)) {
      const n = fact.note.trim();
      if (n && clean(n)) notes.add(n);
    }
  }
}
process.stdout.write(JSON.stringify({ scene, notes: [...notes].sort() }));
