#!/usr/bin/env node
/**
 * T-3407 — the 1812 commanding officer's garden grows what data/gardens/1812.json plants,
 * inside a budget a phone can carry.
 *
 * With the real garden file, no browser:
 *   - every crop the file plants has a grower in gardens.js, and every grower is a crop
 *     the file's table names (no orphan on either side);
 *   - every kind grows at all three levels and every variant, with finite positions, a
 *     normal, a uv and the `_confidence` attribute confidence.js patches by;
 *   - a level never costs more than the one nearer it (near >= mid >= far);
 *   - the whole garden drawn at its FAR level (what a phone sees from the fort) stays under
 *     FAR_TRIS, and the template set every copy is drawn from stays under TEMPLATE_BYTES.
 *
 *   node tools/test_gardens.mjs
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const { growTemplate, KINDS } = await import('../renderers/web/js/gardens.js');

// Measured 2026-11-06: 64k at far, ~2.3 MB of templates. The ceilings leave room to grow
// a crop's detail, not to double the garden.
const FAR_TRIS = 90_000;
const TEMPLATE_BYTES = 3_500_000;

const doc = JSON.parse(fs.readFileSync(new URL('../data/gardens/1812.json', import.meta.url), 'utf8'));
let checks = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); checks += 1; };

const planted = new Set();
for (const g of doc.gardens) for (const k of Object.keys(g.plants)) planted.add(k);
const table = new Set(Object.keys(doc.crops));
for (const k of planted) ok(KINDS[k], `the garden plants ${k}, which gardens.js cannot grow`);
for (const k of Object.keys(KINDS)) ok(table.has(k), `gardens.js grows ${k}, which the garden's crop table does not name`);

const LEVELS = ['near', 'mid', 'far'];
let bytes = 0;
const tris = {};
for (const k of Object.keys(KINDS)) {
  tris[k] = {};
  for (const lod of LEVELS) {
    for (const v of [0, 1, 2]) {
      const t = growTemplate(k, v, lod, 1);
      ok(t && t.tris > 0, `${k} ${lod} v${v} grows nothing`);
      for (const part of ['leaves', 'solid']) {
        const geo = t[part];
        if (!geo) continue;
        for (const name of ['position', 'normal', 'uv', '_confidence']) {
          ok(geo.attributes[name], `${k} ${lod} v${v} ${part} has no ${name}`);
        }
        const p = geo.attributes.position.array;
        ok(p.every(Number.isFinite), `${k} ${lod} v${v} ${part} has a non-finite position`);
        for (const a of Object.values(geo.attributes)) bytes += a.array.byteLength;
        if (geo.index) bytes += geo.index.array.byteLength;
      }
      if (v === 0) tris[k][lod] = t.tris;
    }
  }
  ok(tris[k].near >= tris[k].mid && tris[k].mid >= tris[k].far,
    `${k}: a farther level costs more (near ${tris[k].near}, mid ${tris[k].mid}, far ${tris[k].far})`);
}

let far = 0;
for (const g of doc.gardens) for (const [k, list] of Object.entries(g.plants)) far += tris[k].far * list.length;
ok(far <= FAR_TRIS, `the garden at its far level is ${far} triangles, over ${FAR_TRIS}`);
ok(bytes <= TEMPLATE_BYTES, `the garden's templates hold ${bytes} bytes, over ${TEMPLATE_BYTES}`);

console.log(`test_gardens: PASS (${checks} checks; far ${far} tris, templates ${(bytes / 1e6).toFixed(2)} MB)`);
