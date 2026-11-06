// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Loose garments over a portable human (T-3398, T-3409): a wardrobe file made by
 * the wardrobe kit (tools/human_wardrobe.py from data/humans/wardrobes/) and skinned
 * to the body's own skeleton. The first was the 1904 coachman's box coat, shoulder
 * cape, brass buttons and silk top hat.
 *
 * Kevin, 2026-11-06: "his clothing is form fitting and he looks too smooth and not
 * real". The coat stands off the body and its skirt and cape hang in the folds the
 * drape left, so the figure no longer reads as a body in a skin-tight suit.
 *
 * The file is bound by its sha256 (like the horse's walk clip) and by the body
 * master it was draped on; the pieces bind to the loaded body's bones BY NAME with
 * the inverse binds the file carries, so any LOD of the same rig wears it. No
 * texture: the coat is plain wool that fabric.js weaves.
 *
 * Spring tails (T-3409): cloth that hangs free (a cape, a skirt below the seat)
 * shares its weight with a few extra bones the file declares, parented to the
 * body's bones. Each frame `undo.update(dt)` swings them: each tail's tip is a damped
 * spring toward where the tail hangs at rest, driven by its head's acceleration, so
 * it swings when the body is jolted, turned or stopped and is carried without drag
 * at a steady pace, within the tail's own angle limit. At rest a tail
 * moves exactly with its parent, so the drape is unchanged.
 */
import * as THREE from 'three';

export const LIVERY_SCHEMA = 'chicago4d_wardrobe_v1';

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
  const inverses = livery.inverse_bind_matrices.map(m => new THREE.Matrix4().fromArray(m));
  // Spring tails: new bones under the body's own, at rest where their parent puts them.
  const tails = (livery.tails ?? []).map(t => {
    const parent = byName.get(t.parent), at = livery.joints.indexOf(t.parent);
    if (!parent || at < 0) throw Error(`driver livery: tail ${t.name} has no parent ${t.parent}`);
    const head = new THREE.Vector3(...t.head_bind_m);
    const rest = inverses[at].clone().multiply(new THREE.Matrix4().makeTranslation(head.x, head.y, head.z));
    const bone = new THREE.Bone(); bone.name = `livery:${t.name}`;
    rest.decompose(bone.position, bone.quaternion, bone.scale);
    parent.add(bone);
    const tip = new THREE.Vector3(...t.tip_bind_m).sub(head);
    return { name: t.name, bone, parent, rest, restQ: bone.quaternion.clone(), tipLocal: tip, length: tip.length(),
      omega: 2 * Math.PI * t.frequency_hz, zeta: t.damping_ratio, max: THREE.MathUtils.degToRad(t.max_deg),
      r: null, rv: new THREE.Vector3(), headLast: null, headVel: new THREE.Vector3(), angle: 0 };
  });
  const tailByName = new Map(tails.map(t => [t.name, t.bone]));
  const bones = livery.joints.map(name => {
    const bone = tailByName.get(name) ?? byName.get(name);
    if (!bone) throw Error(`driver livery: the body has no bone ${name}`);
    return bone;
  });
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
  const W = new THREE.Matrix4(), head = new THREE.Vector3(), target = new THREE.Vector3(), d = new THREE.Vector3(),
    rd = new THREE.Vector3(), a = new THREE.Vector3(), acc = new THREE.Vector3(), pp = new THREE.Vector3(), ps = new THREE.Vector3(),
    pq = new THREE.Quaternion(), q = new THREE.Quaternion(), I = new THREE.Quaternion();
  /** Swing the spring tails by `dt` seconds of the body's motion. */
  const update = dt => {
    if (!tails.length || !(dt > 0)) return;
    for (const t of tails) {
      t.parent.updateWorldMatrix(true, false);
      W.multiplyMatrices(t.parent.matrixWorld, t.rest);
      head.setFromMatrixPosition(W);
      target.copy(t.tipLocal).applyMatrix4(W);
      rd.subVectors(target, head); const len = rd.length(); rd.divideScalar(len);
      // First frame, a jump (a teleport, a rebuilt route) or a frame too long to
      // integrate: start at rest.
      if (!t.r || dt > .25 || head.distanceTo(t.headLast) > 1) {
        t.r = rd.clone().multiplyScalar(len); t.rv.set(0, 0, 0); t.headLast = head.clone(); t.headVel.set(0, 0, 0); t.angle = 0;
        t.bone.quaternion.copy(t.restQ); t.bone.updateMatrixWorld(true);
        continue;
      }
      // The tip, relative to the tail's head, is a damped spring toward where it hangs
      // at rest, pushed by the head's own acceleration: a jolt, a turn or a stop swings
      // it, and steady motion carries it without a drag.
      d.subVectors(head, t.headLast).divideScalar(dt);
      acc.subVectors(d, t.headVel).divideScalar(dt);
      t.headVel.copy(d); t.headLast.copy(head);
      const n = Math.min(4, Math.max(1, Math.ceil(dt * 60 - 1e-9))), h = dt / n, w2 = t.omega * t.omega, c = 2 * t.zeta * t.omega;
      for (let i = 0; i < n; i++) {
        a.copy(rd).multiplyScalar(len).sub(t.r).multiplyScalar(w2).addScaledVector(t.rv, -c).sub(acc);
        t.rv.addScaledVector(a, h); t.r.addScaledVector(t.rv, h);
      }
      // The tail is a rod: its tip stays its length from the head, within its angle limit.
      d.copy(t.r).normalize();
      let angle = rd.angleTo(d);
      if (angle > t.max) { q.setFromUnitVectors(rd, d); q.slerp(I, 1 - t.max / angle); d.copy(rd).applyQuaternion(q); angle = t.max; }
      t.r.copy(d).multiplyScalar(len);
      t.rv.addScaledVector(d, -t.rv.dot(d));
      t.angle = angle;
      q.setFromUnitVectors(rd, d);
      t.parent.matrixWorld.decompose(pp, pq, ps);
      // World swing q, carried into the parent's frame: local = pq^-1 q pq restQ.
      t.bone.quaternion.copy(pq).invert().multiply(q).multiply(pq).multiply(t.restQ);
      t.bone.updateMatrixWorld(true);
    }
  };
  const undo = () => {
    for (const t of tails) t.bone.removeFromParent();
    tails.length = 0;
    for (const mesh of added) {
      mesh.removeFromParent(); mesh.geometry.dispose();
      const i = body.meshes.indexOf(mesh); if (i >= 0) body.meshes.splice(i, 1);
    }
    for (const m of materials.values()) m.dispose();
    for (const d of dyed) d.material.color.copy(d.color);
    added.length = 0; dyed.length = 0;
  };
  undo.update = update;
  undo.tails = tails;
  return undo;
}
