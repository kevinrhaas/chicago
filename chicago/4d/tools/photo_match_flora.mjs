// T-1881: a picture's planting is part of what it is judged on. The owner, 2026-10-28, on
// 1729 Prairie: "the surrounding wall/fence around the property also should be included in
// the match, as well as the flora". A camera's optional `flora` draws the app's own grown
// plants into the review render, in the anchor's frame on the common grade plane:
//
//   flora: {
//     front_yards: ["prairie_1729", ...]   lots of data/front_yards/<scene>.json, each required
//     street_trees_m: 60                   optional: the parkway trees of data/street_trees/<scene>.json
//                                          standing within this many metres of the anchor
//     street_furniture_m: 60               optional (T-1934): the gas lamps, hydrants and poles of
//                                          data/street_furniture/<scene>.json within this many metres,
//                                          and the wires between two of them
//     season: "spring"                     summer | spring | fall | winter, as the picture's trees are
//   }
//
// The camera's `scene` names the scene. The plants drawn, the renderers that draw them and the
// anchor's placement are hashed into the match record, so the image gate asks for a new look
// when any of them changes (tools/image_gate.mjs).
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const idPattern = /^[a-z0-9_]+$/;
export const FLORA_SEASONS = ['summer', 'spring', 'fall', 'winter'];
export const FLORA_RENDERER_SOURCES = [
  'tools/photo_match.mjs', 'tools/photo_match_flora.mjs',
  'renderers/web/js/front-yards.js', 'renderers/web/js/street-trees.js',
  'renderers/web/js/tree-instances.js', 'renderers/web/js/tree-model.js',
  'renderers/web/js/tree-surface.js', 'renderers/web/js/season.js', 'renderers/web/js/trees.js',
];

/** Resolve a camera's planting before launching the review browser; never drop a lot. */
export function floraReview(root, camera) {
  if (camera.flora === undefined) return null;
  const fl = camera.flora;
  const keys = ['front_yards', 'street_trees_m', 'street_furniture_m', 'season'];
  if (!fl || typeof fl !== 'object' || Array.isArray(fl) || Object.keys(fl).some(k => !keys.includes(k)))
    throw Error(`flora takes ${keys.join(', ')}`);
  const lots = fl.front_yards ?? [];
  if (!Array.isArray(lots) || lots.some(id => typeof id !== 'string' || !idPattern.test(id))
      || new Set(lots).size !== lots.length)
    throw Error('flora.front_yards must be an array of distinct lot parcel ids');
  if (fl.street_trees_m !== undefined && (!Number.isFinite(fl.street_trees_m)
      || fl.street_trees_m <= 0 || fl.street_trees_m > 200))
    throw Error('flora.street_trees_m must be a radius over 0 and at most 200 m');
  if (fl.street_furniture_m !== undefined && (!Number.isFinite(fl.street_furniture_m)
      || fl.street_furniture_m <= 0 || fl.street_furniture_m > 200))
    throw Error('flora.street_furniture_m must be a radius over 0 and at most 200 m');
  if (!lots.length && fl.street_trees_m === undefined)
    throw Error('flora names front_yards lots, a street_trees_m radius or both');
  if (!FLORA_SEASONS.includes(fl.season)) throw Error(`flora.season is one of ${FLORA_SEASONS.join(', ')}`);
  if (typeof camera.scene !== 'string' || !idPattern.test(camera.scene))
    throw Error('flora requires an explicit scene id');
  const read = file => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
  const scene = read(`data/scenes/${camera.scene}.json`);
  const sidecar = read(`data/sidecars/${camera.scene}/${camera.structure_id}.json`);
  if (sidecar.id !== camera.structure_id || sidecar.scene !== camera.scene
      || sidecar.target_date !== scene.target_date)
    throw Error('flora anchor has a stale or wrong-scene sidecar');
  const p = sidecar.placement;
  if (!p || !['local_e', 'local_n', 'rotation_deg'].every(key => Number.isFinite(p[key])))
    throw Error('flora anchor needs finite scene placement and bearing');
  const docs = {};
  if (lots.length) {
    const doc = read(`data/front_yards/${camera.scene}.json`);
    const picked = lots.map(id => {
      const lot = (doc.lots ?? []).find(l => l.parcel === id);
      if (!lot) throw Error(`${id}: no such lot in data/front_yards/${camera.scene}.json`);
      return lot;
    });
    docs.front_yards = {...doc, lots: picked};
  }
  if (fl.street_trees_m !== undefined) {
    const doc = read(`data/street_trees/${camera.scene}.json`);
    const near = (doc.trees ?? []).filter(t => Number.isFinite(t.e) && Number.isFinite(t.n)
      && Math.hypot(t.e - p.local_e, t.n - p.local_n) <= fl.street_trees_m);
    docs.street_trees = {...doc, trees: near};
  }
  if (fl.street_furniture_m !== undefined) {
    const doc = read(`data/street_furniture/${camera.scene}.json`);
    const near = (doc.items ?? []).filter(t => Number.isFinite(t.e) && Number.isFinite(t.n)
      && Math.hypot(t.e - p.local_e, t.n - p.local_n) <= fl.street_furniture_m);
    const ids = new Set(near.map(t => t.id));
    docs.street_furniture = {...doc, items: near, wires: (doc.wires ?? []).filter(w => ids.has(w.from) && ids.has(w.to))};
  }
  const anchor = {local_e: p.local_e, local_n: p.local_n, rotation_deg: p.rotation_deg,
    scene: sidecar.scene, target_date: sidecar.target_date, phase: sidecar.phase};
  const rendererSources = [...FLORA_RENDERER_SOURCES,
    ...(docs.street_furniture ? ['renderers/web/js/street-furniture.js'] : [])].map(file => ({file, sha256: sha(path.join(root, file))}));
  const rendered = {
    season: fl.season,
    lots: lots.map(id => {
      const l = docs.front_yards.lots.find(x => x.parcel === id);
      return {parcel: id, shrubs: (l.shrubs ?? []).length, trees: (l.trees ?? []).length,
        beds: (l.beds ?? []).length, creeper: (l.creeper ?? []).length};
    }),
    ...(docs.street_trees ? {street_trees: docs.street_trees.trees.length, street_trees_m: fl.street_trees_m} : {}),
    ...(docs.street_furniture ? {street_furniture: docs.street_furniture.items.map(t => t.id),
      street_furniture_m: fl.street_furniture_m} : {}),
  };
  const signature = {anchor, rendered, docs, renderer_sources: rendererSources};
  return {anchor, docs, season: fl.season, review: {
    rendered_flora: rendered, flora_anchor: anchor, flora_renderer_sources: rendererSources,
    flora_sha256: crypto.createHash('sha256').update(JSON.stringify(signature)).digest('hex'),
  }};
}
