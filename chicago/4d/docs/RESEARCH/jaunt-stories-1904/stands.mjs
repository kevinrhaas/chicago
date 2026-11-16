#!/usr/bin/env node
// The stands the one framing rule (main.js framing -> route.js standOff) gives each 1904
// structure a story jaunt stops at, and the middle of that structure's street front, so
// build.py can set a stop's cast between the visitor and the house. The same router, data
// and distance rule as tools/check_jaunt_views.mjs. Prints JSON: { id: { stand, front } }.
//   node docs/RESEARCH/jaunt-stories-1904/stands.mjs id [id ...]
import fs from 'node:fs';
import { register } from 'node:module';
import { createRouter } from '../../../renderers/web/js/route.js';

const vendor = new URL('../../../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const { footprintsFrom } = await import('../../../renderers/web/js/walker.js');
const SCENE = '1904', DEG = Math.PI / 180, H_FOV_DEG = 76, ASPECT = 1280 / 800, ELM_R = 0.29;
const POST_R = { gas_lamp: 0.12, utility_pole: 0.15 };
const read = rel => JSON.parse(fs.readFileSync(new URL(`../../../data/${rel}`, import.meta.url)));
const registry = new Map();
for (const name of fs.readdirSync(new URL(`../../../data/sidecars/${SCENE}/`, import.meta.url)).filter(n => n.endsWith('.json') && n !== 'index.json')) {
  const sidecar = read(`sidecars/${SCENE}/${name}`);
  if (sidecar?.id && sidecar.footprint) registry.set(sidecar.id, { id: sidecar.id, sidecar });
}
const footprints = footprintsFrom(registry);
const trees = read(`street_trees/${SCENE}.json`).trees ?? [];
const furniture = read(`street_furniture/${SCENE}.json`).items ?? [];
const occluders = [...trees.map(t => ({ e: t.e, n: t.n, r: ELM_R * (t.scale ?? 1) })),
  ...furniture.filter(f => POST_R[f.kind]).map(f => ({ e: f.e, n: f.n, r: POST_R[f.kind] }))];
let e0 = Infinity, e1 = -Infinity, n0 = Infinity, n1 = -Infinity;
for (const f of footprints) for (const [e, n] of f.pts) { e0 = Math.min(e0, e); e1 = Math.max(e1, e); n0 = Math.min(n0, n); n1 = Math.max(n1, n); }
const terrain = { heightfield: { loaded: true, originE: e0 - 60, originN: n0 - 60, widthM: e1 - e0 + 120, depthM: n1 - n0 + 120 },
  surfaceHeight: () => 1, walkHeight: () => 1, isWater: () => false };
const router = createRouter({ terrain, streetGrid: read(`street_grid/${SCENE}.json`), footprints, occluders, cell: 1, inflate: 0.1 });
function framingDistance(fp, sidecar) {
  let b0 = Infinity, b1 = -Infinity, c0 = Infinity, c1 = -Infinity;
  for (const [e, n] of fp.pts) { b0 = Math.min(b0, e); b1 = Math.max(b1, e); c0 = Math.min(c0, n); c1 = Math.max(c1, n); }
  const r = Math.max(2, Math.hypot(b1 - b0, c1 - c0) / 2);
  const h = (sidecar?.attributes?.wall_height_m?.value ?? 5) * 1.55;
  const R = Math.hypot(r, h / 2), tanH = Math.tan(H_FOV_DEG * DEG / 2);
  const half = Math.min(Math.atan(tanH), Math.atan(tanH / ASPECT));
  return { r, distance: Math.min(90, Math.max(10, (R * 1.25) / Math.sin(half))) };
}
const out = {};
for (const id of process.argv.slice(2)) {
  const fp = footprints.find(f => f.id === id);
  if (!fp) { out[id] = null; continue; }
  const centre = { e: fp.pts.reduce((a, p) => a + p[0], 0) / fp.pts.length, n: fp.pts.reduce((a, p) => a + p[1], 0) / fp.pts.length };
  const { r, distance } = framingDistance(fp, registry.get(id)?.sidecar);
  const stand = router.standOff(id, centre, r, { distance, mode: 'walk' });
  const front = stand?.front ?? router.frontage(id, centre);
  const r2 = v => Math.round(v * 100) / 100;
  out[id] = { stand: [r2(stand.e), r2(stand.n)], front: [r2(front.e), r2(front.n)], bearing_deg: r2(((front.bearing / DEG) + 360) % 360),
    width: r2(front.width), centre: [r2(centre.e), r2(centre.n)], distance: r2(distance) };
}
console.log(JSON.stringify(out, null, 1));
