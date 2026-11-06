// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * A coachman's livery over the 1904 brougham driver (T-3398): box coat, shoulder
 * cape, brass buttons and a silk top hat, draped in his seated pose by
 * tools/human_driver_livery_1904.py and skinned to his own skeleton.
 *
 * Kevin, 2026-11-06: "his clothing is form fitting and he looks too smooth and not
 * real". The coat stands off the body and its skirt and cape hang in the folds the
 * drape left, so the figure no longer reads as a body in a skin-tight suit.
 *
 * The file is bound by its sha256 (like the horse's walk clip) and by the body
 * master it was draped on; the pieces bind to the loaded body's bones BY NAME with
 * the inverse binds the file carries, so any LOD of the same rig wears it. No
 * texture: the coat is plain wool that fabric.js weaves.
 */
import * as THREE from 'three';

export const LIVERY_SCHEMA = 'chicago4d_driver_livery_v1';

const hex = bytes => [...new Uint8Array(bytes)].map(n => n.toString(16).padStart(2, '0')).join('');
const unb64 = text => Uint8Array.from(atob(text), c => c.charCodeAt(0)).buffer;

/** Fetch and verify a livery file. Resolves to its parsed, decoded document. */
export async function loadLivery(url, sha256, fetchImpl = fetch) {
  const response = await fetchImpl(url);
  if (!response.ok) throw Error(`driver livery: HTTP${response.status}`);
  const bytes = await response.arrayBuffer();
  if (hex(await crypto.subtle.digest('SHA-256', bytes)) !== sha256) throw Error('driver livery: file differs from its binding');
  return parseLivery(new TextDecoder().decode(bytes));
}

export function parseLivery(text) {
  const doc = JSON.parse(text);
  if (doc.schema !== LIVERY_SCHEMA || !Array.isArray(doc.parts) || !Array.isArray(doc.joints)
    || doc.inverse_bind_matrices?.length !== doc.joints.length) throw Error('driver livery: not a livery document');
  const parts = doc.parts.map(p => {
    const wide = p.vertex_count >= 65536;
    const out = {
      name: p.name, material: p.material,
      position: new Float32Array(unb64(p.position)), normal: new Float32Array(unb64(p.normal)),
      joints: new Uint8Array(unb64(p.joints)), weights: new Float32Array(unb64(p.weights)),
      index: wide ? new Uint32Array(unb64(p.index)) : new Uint16Array(unb64(p.index)),
    };
    if (out.position.length !== p.vertex_count * 3 || out.joints.length !== p.vertex_count * 4
      || out.index.length !== p.triangle_count * 3 || !doc.materials[p.material]) throw Error(`driver livery: ${p.name} is malformed`);
    return out;
  });
  return { ...doc, parts };
}

/**
 * Dress a loaded human body ({ scene, meshes }) in a parsed livery. The pieces are
 * added beside the body's own skinned meshes and pushed onto `body.meshes`, so the
 * actor's shadow and teardown handling covers them. Returns an undo.
 */
export function dressInLivery(body, livery) {
  const reference = body?.meshes?.find(m => m.isSkinnedMesh && m.skeleton);
  if (!reference) throw Error('driver livery: no skinned body to dress');
  const byName = new Map(reference.skeleton.bones.map(b => [b.name, b]));
  const bones = livery.joints.map(name => {
    const bone = byName.get(name);
    if (!bone) throw Error(`driver livery: the body has no bone ${name}`);
    return bone;
  });
  const inverses = livery.inverse_bind_matrices.map(m => new THREE.Matrix4().fromArray(m));
  const skeleton = new THREE.Skeleton(bones, inverses);
  const materials = new Map();
  const material = name => {
    if (!materials.has(name)) {
      const m = livery.materials[name];
      materials.set(name, new THREE.MeshStandardMaterial({ name,
        color: new THREE.Color().setRGB(...m.color, THREE.LinearSRGBColorSpace),
        roughness: m.roughness, metalness: m.metalness, side: m.double_sided ? THREE.DoubleSide : THREE.FrontSide }));
    }
    return materials.get(name);
  };
  // Livery trousers: the body's own garment re-dyed, restored on undo.
  const dyed = [];
  for (const mesh of body.meshes) {
    const colour = livery.recolor_body_materials?.[mesh.material?.name];
    if (!colour || dyed.some(d => d.material === mesh.material)) continue;
    dyed.push({ material: mesh.material, color: mesh.material.color.clone() });
    mesh.material.color.setRGB(...colour, THREE.LinearSRGBColorSpace);
  }
  const added = [];
  for (const part of livery.parts) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(part.position, 3));
    geometry.setAttribute('normal', new THREE.BufferAttribute(part.normal, 3));
    geometry.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(Uint16Array.from(part.joints), 4));
    geometry.setAttribute('skinWeight', new THREE.BufferAttribute(part.weights, 4));
    geometry.setIndex(new THREE.BufferAttribute(part.index, 1));
    const mesh = new THREE.SkinnedMesh(geometry, material(part.material));
    mesh.name = `livery:${part.name}`;
    mesh.frustumCulled = false;   // as the body's own: a skinned bound is the bind pose's
    mesh.castShadow = reference.castShadow; mesh.receiveShadow = reference.receiveShadow;
    reference.parent.add(mesh);
    mesh.bind(skeleton, reference.bindMatrix);
    body.meshes.push(mesh);
    added.push(mesh);
  }
  return () => {
    for (const mesh of added) {
      mesh.removeFromParent(); mesh.geometry.dispose();
      const i = body.meshes.indexOf(mesh); if (i >= 0) body.meshes.splice(i, 1);
    }
    for (const m of materials.values()) m.dispose();
    for (const d of dyed) d.material.color.copy(d.color);
    added.length = 0; dyed.length = 0;
  };
}
