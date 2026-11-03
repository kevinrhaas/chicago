#!/usr/bin/env node
/**
 * check_jaunt_views.mjs — T-3263. Does every 1904 jaunt stop see its house?
 *
 * The owner, 2026-10-30, on the Women of Prairie Avenue walk's stop at 1834 Prairie,
 * where the camera stood a metre behind a parkway elm: "make sure that the stops are not
 * right behind a tree, that you can move and find a point that has a view of the house
 * a few feet north or south and look at it".
 *
 * A jaunt stop does not carry a camera. It names a structure, and the ride ends where
 * the one framing rule (main.js framing → route.js standOff) stands a visitor to look
 * at it. So this asks that rule, in node, against the committed 1904 data — the street
 * grid's walks, every sidecar footprint, the parkway elms (data/street_trees) and the
 * lamps and poles (data/street_furniture) — where it stands for every 1904 stop, on
 * foot and on horseback, and how much of the house's street front the trunks and posts
 * between hide (route.js frontView). A stop with a trunk or post near the eye in the
 * middle of the frame (VIEW_NEAR_BLOCKED) or over VIEW_BLOCKED of the front hidden fails.
 *
 * Flat ground, like test_street_travel.mjs: the stand is chosen on the plan, and the
 * walk the published terrain carries does not move it. The 1835 and 1812 timber is
 * grown in the browser (trees.js) and is not in data/, so those years are measured by
 * the same rule at runtime (main.js hands the router the grown trunks), not here.
 *
 *   node tools/check_jaunt_views.mjs            gate: every 1904 stop, both modes
 *   node tools/check_jaunt_views.mjs --report   every stop's share, blocked or not
 *   node tools/check_jaunt_views.mjs --self-test  the rule without trunks must fail
 */
import fs from 'node:fs';
import { register } from 'node:module';
import { createRouter, frontBlocked, frontView, VIEW_BLOCKED, VIEW_NEAR_BLOCKED } from '../renderers/web/js/route.js';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const { footprintsFrom } = await import('../renderers/web/js/walker.js');

const args = new Set(process.argv.slice(2));
const SELF_TEST = args.has('--self-test');
const REPORT = args.has('--report');
const SCENE = '1904';
const DEG = Math.PI / 180;
/** main.js H_FOV_DEG and a desktop 1280×800 window; a jaunt's arrival has no card up. */
const H_FOV_DEG = 76, ASPECT = 1280 / 800;
/** Trunk at eye height: half a parkway elm's 0.45-0.70 m breast-height diameter (the
 *  file's species note) at its scale; the furniture's own drawn foot radii. */
const ELM_R = 0.29;
const POST_R = { gas_lamp: 0.12, utility_pole: 0.15 };

const read = rel => JSON.parse(fs.readFileSync(new URL(`../data/${rel}`, import.meta.url)));
const registry = new Map();
for (const name of fs.readdirSync(new URL(`../data/sidecars/${SCENE}/`, import.meta.url)).filter(n => n.endsWith('.json') && n !== 'index.json')) {
  const sidecar = read(`sidecars/${SCENE}/${name}`);
  if (sidecar?.id && sidecar.footprint) registry.set(sidecar.id, { id: sidecar.id, sidecar });
}
const footprints = footprintsFrom(registry);
const trees = read(`street_trees/${SCENE}.json`).trees ?? [];
const furniture = read(`street_furniture/${SCENE}.json`).items ?? [];
const occluders = [
  ...trees.map(t => ({ e: t.e, n: t.n, r: ELM_R * (t.scale ?? 1), what: `elm ${t.id}` })),
  ...furniture.filter(f => POST_R[f.kind]).map(f => ({ e: f.e, n: f.n, r: POST_R[f.kind], what: f.id })),
];

let e0 = Infinity, e1 = -Infinity, n0 = Infinity, n1 = -Infinity;
for (const f of footprints) for (const [e, n] of f.pts) {
  e0 = Math.min(e0, e); e1 = Math.max(e1, e); n0 = Math.min(n0, n); n1 = Math.max(n1, n);
}
const terrain = { heightfield: { loaded: true, originE: e0 - 60, originN: n0 - 60, widthM: e1 - e0 + 120, depthM: n1 - n0 + 120 },
  surfaceHeight: () => 1, walkHeight: () => 1, isWater: () => false };
const make = occ => createRouter({ terrain, streetGrid: read(`street_grid/${SCENE}.json`), footprints,
  occluders: occ, cell: 1, inflate: 0.1 });
const router = make(SELF_TEST ? [] : occluders);

/** main.js framing(): the distance that fits the building's sphere in the view. */
function framingDistance(fp, sidecar) {
  let b0 = Infinity, b1 = -Infinity, c0 = Infinity, c1 = -Infinity;
  for (const [e, n] of fp.pts) { b0 = Math.min(b0, e); b1 = Math.max(b1, e); c0 = Math.min(c0, n); c1 = Math.max(c1, n); }
  const r = Math.max(2, Math.hypot(b1 - b0, c1 - c0) / 2);
  const h = (sidecar?.attributes?.wall_height_m?.value ?? 5) * 1.55;
  const R = Math.hypot(r, h / 2);
  const tanH = Math.tan(H_FOV_DEG * DEG / 2);
  const half = Math.min(Math.atan(tanH), Math.atan(tanH / ASPECT));
  return { r, distance: Math.min(90, Math.max(10, (R * 1.25) / Math.sin(half))) };
}

const stops = [];
for (const name of fs.readdirSync(new URL('../data/jaunts/', import.meta.url)).filter(n => n.endsWith('.json') && n !== 'schema.json')) {
  const jaunt = read(`jaunts/${name}`);
  if (jaunt.scene !== SCENE) continue;
  for (const stop of jaunt.stops ?? []) {
    if (stop.destination?.kind === 'structure') stops.push({ jaunt: jaunt.id, stop: stop.id, id: stop.destination.id });
  }
}

const seen = new Map();
const failures = [];
const rows = [];
for (const s of stops) {
  for (const mode of ['walk', 'horse']) {
    const key = `${s.id}:${mode}`;
    if (!seen.has(key)) {
      const fp = footprints.find(f => f.id === s.id);
      if (!fp) { seen.set(key, { missing: true }); continue; }
      const centre = { e: fp.pts.reduce((a, p) => a + p[0], 0) / fp.pts.length, n: fp.pts.reduce((a, p) => a + p[1], 0) / fp.pts.length };
      const { r, distance } = framingDistance(fp, registry.get(s.id)?.sidecar);
      const stand = router.standOff(s.id, centre, r, { distance, mode });
      // A stand the rule fell back to (no street walk in front) is measured against the
      // same front the rule aimed at.
      const front = stand?.front ?? router.frontage(s.id, centre);
      const view = stand ? frontView(stand, front, occluders) : null;
      // The nearest trunk or post in the way, to name in a failure.
      let worst = null;
      if (stand) for (const o of occluders) {
        const d = Math.hypot(o.e - stand.e, o.n - stand.n);
        if (frontBlocked(stand, front, [o]) > 0 && (!worst || d < worst.d)) worst = { what: o.what, d };
      }
      seen.set(key, { stand, view, worst });
    }
    const v = seen.get(key);
    if (v.missing) continue; // compile_jaunts gates a stop naming no structure
    const row = { ...s, mode, blocked: v.view?.hidden ?? null, near: v.view?.near ?? null, e: v.stand?.e, n: v.stand?.n, worst: v.worst };
    rows.push(row);
    if (!v.view || v.view.near > VIEW_NEAR_BLOCKED || v.view.hidden > VIEW_BLOCKED) failures.push(row);
  }
}

const pct = x => x === null ? 'no stand' : `${(x * 100).toFixed(0)}%`;
const line = r => `${r.jaunt} / ${r.stop} (${r.id}, ${r.mode}) at e ${r.e?.toFixed(1)} n ${r.n?.toFixed(1)}: `
  + `${pct(r.blocked)} of the front hidden, ${pct(r.near)} by a trunk or post near the eye${r.worst ? ` — nearest in the way ${r.worst.what} at ${r.worst.d.toFixed(1)} m` : ''}`;
if (REPORT) for (const r of rows) console.log(`  ${line(r)}`);
const stats = `${rows.length} stop arrivals (${stops.length} stops × walk, horse), ${occluders.length} trunks and posts`;

if (SELF_TEST) {
  // Without the trunks the rule stands where it did before T-3263, and the Women of
  // Prairie Avenue walk's Jones stop is behind its elm again: the gate has to see that.
  const jones = failures.find(r => r.id === 'jones_house_1834_prairie' && r.mode === 'walk');
  if (!jones) { console.log(`JAUNT VIEWS SELF-TEST FAIL — with no trunks given to the rule, the 1834 Prairie stop still reads clear`); process.exit(1); }
  console.log(`JAUNT VIEWS SELF-TEST PASS — with no trunks given to the rule, ${failures.length} stop arrivals stand blocked (${line(jones)})`);
  process.exit(0);
}
if (failures.length) {
  for (const r of failures) console.log(`  FAIL ${line(r)}`);
  console.log(`JAUNT VIEWS FAIL — ${failures.length} of ${stats} stand behind a trunk or post (over ${pct(VIEW_NEAR_BLOCKED)} near the eye) or with over ${pct(VIEW_BLOCKED)} of the house hidden`);
  process.exit(1);
}
const worst = rows.reduce((m, r) => Math.max(m, r.blocked ?? 0), 0);
console.log(`JAUNT VIEWS PASS — ${stats}; no stand is behind a trunk or post, and every one sees at least ${pct(1 - VIEW_BLOCKED)} of its house's front (worst ${pct(worst)} hidden)`);
