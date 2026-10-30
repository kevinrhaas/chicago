// Optional picture context uses the app's native fence renderer and source records.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const idPattern = /^[a-z0-9_]+$/;
export const ENCLOSURE_RENDERER_SOURCES = [
  'tools/photo_match.mjs', 'tools/photo_match_enclosures.mjs',
  'renderers/web/js/enclosures.js', 'renderers/web/js/gates.js',
  'renderers/web/js/compact-streams.js', 'renderers/web/js/gpu-pick.js',
  'renderers/web/vendor/three-0.185.1/three.module.js',
  'renderers/web/vendor/three-0.185.1/three.core.js',
];

/** Resolve a selected native enclosure set before launching the review browser. */
export function enclosureReview(root, camera) {
  if (camera.enclosures === undefined) return null;
  if (!Array.isArray(camera.enclosures)
      || camera.enclosures.some(id => typeof id !== 'string' || !idPattern.test(id))
      || new Set(camera.enclosures).size !== camera.enclosures.length)
    throw Error('enclosures must be an array of distinct enclosure ids');
  if (!camera.enclosures.length) return null;
  if (typeof camera.structure_id !== 'string' || !idPattern.test(camera.structure_id))
    throw Error('enclosures require a valid anchor structure id');
  if (typeof camera.scene !== 'string' || !idPattern.test(camera.scene))
    throw Error('enclosures require an explicit scene id');
  const read = file => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
  const scene = read(`data/scenes/${camera.scene}.json`);
  const sidecar = read(`data/sidecars/${camera.scene}/${camera.structure_id}.json`);
  if (sidecar.id !== camera.structure_id || sidecar.scene !== camera.scene
      || sidecar.target_date !== scene.target_date)
    throw Error('enclosure anchor has a stale or wrong-scene sidecar');
  const p = sidecar.placement;
  if (!p || !['local_e', 'local_n', 'rotation_deg'].every(key => Number.isFinite(p[key])))
    throw Error('enclosure anchor needs finite scene placement and bearing');
  const index = read('data/enclosures/index.json');
  const records = camera.enclosures.map(id => {
    const entry = index.enclosures?.find(value => value.id === id);
    if (!entry || !/^[a-z0-9_]+\.json$/.test(entry.file))
      throw Error(`${id}: enclosure is absent from the native manifest or has an invalid file`);
    const file = `data/enclosures/${entry.file}`;
    const record = read(file);
    if (record.id !== id || record.scene !== camera.scene || record.target_date !== scene.target_date
        || !record.documented_range?.from || !record.documented_range?.to
        || record.documented_range.from > scene.target_date || record.documented_range.to < scene.target_date)
      throw Error(`${id}: enclosure has a stale or wrong-scene/date record`);
    const owners = [record.structure_id, ...(record.belongs_to || [])];
    if (!owners.includes(camera.structure_id))
      throw Error(`${id}: enclosure does not belong to the camera's anchor`);
    if (!Array.isArray(record.runs) || !record.runs.length || record.runs.some(run =>
      !Array.isArray(run.path_local_enu_m) || run.path_local_enu_m.length < 2
      || run.path_local_enu_m.some(point => !Array.isArray(point) || point.length !== 2
        || point.some(value => !Number.isFinite(value)))))
      throw Error(`${id}: enclosure needs finite native run coordinates`);
    if (!['board', 'picket', 'post_and_rail'].includes(record.form?.fence_type?.value)
        || !Number.isFinite(record.form?.height_m?.value) || record.form.height_m.value <= 0)
      throw Error(`${id}: enclosure needs a supported fence kind and positive height`);
    return {id, file, sha256: sha(path.join(root, file)), entry};
  });
  const anchor = {local_e: p.local_e, local_n: p.local_n, rotation_deg: p.rotation_deg,
    scene: sidecar.scene, target_date: sidecar.target_date, phase: sidecar.phase};
  const rendererSources = ENCLOSURE_RENDERER_SOURCES.map(file => ({file,
    sha256: sha(path.join(root, file))}));
  const rendered = records.map(({id, file, sha256}) => ({id, file, sha256}));
  const signature = {anchor, records: rendered, renderer_sources: rendererSources};
  return {records, anchor, index: {enclosures: records.map(record => record.entry)}, review: {
    rendered_enclosures: rendered, enclosure_anchor: anchor,
    enclosure_renderer_sources: rendererSources,
    enclosures_sha256: crypto.createHash('sha256').update(JSON.stringify(signature)).digest('hex'),
  }};
}
