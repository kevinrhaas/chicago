#!/usr/bin/env node
/**
 * reading_leads.mjs — every building card's opening line, as a reader is shown it (T-3645).
 *
 *   node tools/reading_leads.mjs <scene>     # prints {"leads": [...]} for tools/reading_levels.py
 *
 * A building's card opens on the phase's own account or on the line popup.js `cardOpening`
 * composes from its sidecar (T-2636). The floating card prints that lead; Inspect's Overview
 * prints it where it fits the front page, else the templated summary (inspect-view.js
 * `fitsFrontPage`). Both are said through the scene's reader overlay first (T-2825), so the
 * strings here are the strings a card shows, and a retelling keyed by one finds its card.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const APP = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const JS = path.join(APP, 'renderers/web/js');
const { cardOpening } = await import(path.join(JS, 'popup.js'));
const { displayName } = await import(path.join(JS, 'display-name.js'));
const { fallbackSummary } = await import(path.join(JS, 'fallback-summary.js'));
const { readerCopy } = await import(path.join(JS, 'reader-text.js'));

const scene = process.argv[2];
const dir = path.join(APP, 'data/sidecars', scene);
const overlayPath = path.join(APP, 'data/reader', `structures_${scene}.json`);
const overlay = existsSync(overlayPath) ? JSON.parse(readFileSync(overlayPath, 'utf8')) : null;
const fits = (t) => String(t).split(/\s+/).filter((w) => /[A-Za-z0-9]/.test(w)).length <= 60
  && (String(t).match(/[.!?](\s|$)/g) ?? []).length <= 3;
const leads = new Set();
if (existsSync(dir)) {
  for (const f of readdirSync(dir).sort()) {
    if (!f.endsWith('.json')) continue;
    const raw = JSON.parse(readFileSync(path.join(dir, f), 'utf8'));
    if (!raw || typeof raw !== 'object' || !raw.placement || !raw.id) continue;
    const s = overlay ? readerCopy(raw, overlay) : raw;
    const o = cardOpening(s, displayName(s, s.id));
    if (o.lead) leads.add(o.lead.trim());
    if (o.lead && !fits(o.lead)) {
      const today = s?.attributes?.present_status?.value ? String(s.attributes.present_status.value) : '';
      const t = fallbackSummary(s, { kind: o.kind[0] ?? '', today }).text;
      if (t) leads.add(t.trim());
    }
  }
}
process.stdout.write(JSON.stringify({ scene, leads: [...leads].sort() }));
