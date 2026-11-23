// A reference camera stays in its anchor's footprint frame. Context meshes use
// the selected scene's actual phase, origin and bearing, on a common grade plane.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const idPattern = /^[a-z0-9_]+$/;

export function primaryGlb(root, id) {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'assets/manifest.json'), 'utf8'));
  const hit = Object.entries(manifest.assets || manifest).find(([key, value]) =>
    value?.structure_id === id && !/coach_house/.test(key));
  if (!hit) throw Error(`no GLB for ${id} in assets/manifest.json`);
  return path.join('assets/gltf', hit[0]);
}

/** T-3722: the GLB of a structure VERSION (docs/STRUCTURE-VERSIONS.md) — a picture of a later
 *  or earlier state than the default record stands is matched against that version's mesh
 *  (2126 Prairie's May 1905 plate shows the completed house; the record stands the July 1904
 *  works shell). Its one master in assets/manifest.versions.json, by structure and label. */
export function versionGlb(root, id, label) {
  if (typeof label !== 'string' || !/^[a-z0-9_]+$/.test(label)) throw Error(`version ${JSON.stringify(label)} is not a version label`);
  const file = path.join(root, 'assets/manifest.versions.json');
  const manifest = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : {assets: {}};
  const hits = Object.entries(manifest.assets || {}).filter(([, v]) => v?.structure_id === id && v?.version_label === label);
  if (hits.length !== 1) throw Error(`${hits.length ? 'more than one' : 'no'} GLB for ${id} version ${label} in assets/manifest.versions.json`);
  return path.join('assets/gltf', hits[0][0]);
}

/** The GLB a camera's own building is matched against: its version's, or the record's. */
export function cameraGlb(root, camera) {
  return camera.version !== undefined ? versionGlb(root, camera.structure_id, camera.version)
    : primaryGlb(root, camera.structure_id);
}

/** Resolve every requested member before launching the browser; never drop one. */
export function renderGroup(root, camera, {glb} = {}) {
  if (camera.also_render !== undefined && !Array.isArray(camera.also_render))
    throw Error('also_render must be an array of distinct structure ids');
  const extra = camera.also_render || [];
  if (!extra.length) return [{structure_id: camera.structure_id,
    glb: glb || cameraGlb(root, camera), position: [0, 0, 0], rotation_y: 0}];
  if (camera.version !== undefined) throw Error('version renders one building alone, not with also_render');
  const ids = [camera.structure_id, ...extra];
  if (ids.some(id => typeof id !== 'string' || !idPattern.test(id)) || new Set(ids).size !== ids.length)
    throw Error('also_render requires distinct structure ids and must not repeat the anchor');
  if (typeof camera.scene !== 'string' || !idPattern.test(camera.scene))
    throw Error('also_render requires an explicit scene id');
  const scene = JSON.parse(fs.readFileSync(path.join(root, 'data/scenes', camera.scene + '.json'), 'utf8'));
  const members = ids.map((id, index) => {
    const file = path.join(root, 'data/sidecars', camera.scene, id + '.json');
    if (!fs.existsSync(file)) throw Error(`${id} is absent from scene ${camera.scene}`);
    const sidecar = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (sidecar.id !== id || sidecar.scene !== camera.scene || sidecar.target_date !== scene.target_date)
      throw Error(`${id} has a stale or wrong-scene sidecar for ${camera.scene}`);
    const p = sidecar.placement;
    if (!p || !['local_e', 'local_n', 'rotation_deg'].every(key => Number.isFinite(p[key])))
      throw Error(`${id} needs finite scene placement and bearing`);
    if (typeof sidecar.asset !== 'string' || !/^gltf\/[^/]+\.glb$/.test(sidecar.asset))
      throw Error(`${id} has no usable scene GLB`);
    const asset = index === 0 && glb ? glb : path.join('assets', sidecar.asset);
    if (!fs.existsSync(path.resolve(root, asset))) throw Error(`${id}: missing GLB ${asset}`);
    return {structure_id: id, glb: asset, placement: {
      local_e: p.local_e, local_n: p.local_n, rotation_deg: p.rotation_deg,
      scene: sidecar.scene, target_date: sidecar.target_date, phase: sidecar.phase,
    }};
  });
  const anchor = members[0].placement, A = anchor.rotation_deg * Math.PI / 180;
  for (const member of members) {
    const p = member.placement, de = p.local_e - anchor.local_e, dn = p.local_n - anchor.local_n;
    member.position = [Math.cos(A) * de - Math.sin(A) * dn, 0,
      -(Math.sin(A) * de + Math.cos(A) * dn)];
    member.rotation_y = (anchor.rotation_deg - p.rotation_deg) * Math.PI / 180;
  }
  return members;
}

/** All meshes and placements, not just the anchor, are part of a group review. */
export function groupReview(root, members) {
  const rendered_members = members.map(member => ({...member,
    glb_sha256: sha(path.resolve(root, member.glb))}));
  return {rendered_members, group_sha256: crypto.createHash('sha256')
    .update(JSON.stringify(rendered_members)).digest('hex')};
}
