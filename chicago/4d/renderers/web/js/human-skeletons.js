// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-skeletons.js — one skeleton per set of bones a figure is skinned to (T-3639).
 *
 * The owner, 2026-11-17, at the Kinzie household in 1812: *"its very jumpy from frame to frame
 * and it skips frames"*. A person is drawn in up to eighteen skinned pieces (body, shirt, coat,
 * breeches, hair, hat, the strand cards, a musket), and every piece came out of the clone
 * (SkeletonUtils.clone, which gives each mesh a skeleton of its own) and out of GLTFLoader
 * (a new Skeleton per mesh, even of one skin) with its own Skeleton over the SAME bones and the
 * SAME inverse binds. three.js recomputes and re-uploads a skeleton's bone texture once a frame
 * for every skeleton it draws, so the household and the garrison in view cost 448 skeleton
 * updates and 448 bone-texture uploads a frame where 40-odd say everything.
 *
 * `shareSkeletons(root)` binds every skinned mesh under `root` whose skeleton has the same bones
 * (the same Bone objects, in the same order) and bit-identical inverse binds as one met before
 * it to that first skeleton. Each mesh keeps its own bind matrix, so the vertices skin exactly
 * as they did: the shared skeleton's bone matrices are, number for number, what each private
 * one computed. The skeletons it leaves without a mesh are disposed (nothing was uploaded for
 * them yet when this runs in a build). Returns { meshes, before, after }.
 *
 * No DOM; `tools/test_human_skeletons.mjs` drives it with real three.js skeletons.
 */

/** Whether two skeletons skin the same: the same bones in order, and equal inverse binds. */
export function sameSkeleton(a, b) {
  if (a === b) return true;
  if (!a || !b || a.bones.length !== b.bones.length || a.boneInverses.length !== b.boneInverses.length) return false;
  for (let i = 0; i < a.bones.length; i++) if (a.bones[i] !== b.bones[i]) return false;
  for (let i = 0; i < a.boneInverses.length; i++) {
    const x = a.boneInverses[i].elements, y = b.boneInverses[i].elements;
    if (x === y) continue;
    for (let k = 0; k < 16; k++) if (x[k] !== y[k]) return false;
  }
  return true;
}

/** Bind every skinned mesh under `root` to the first skeleton equal to its own. */
export function shareSkeletons(root) {
  const meshes = [];
  root?.traverse?.((o) => { if (o.isSkinnedMesh && o.skeleton) meshes.push(o); });
  const kept = [];                 // the skeletons kept, one per distinct set of bones
  const byFirst = new Map();       // first bone -> kept skeletons that start with it
  const before = new Set(meshes.map((m) => m.skeleton));
  const dropped = new Set();
  for (const mesh of meshes) {
    const own = mesh.skeleton;
    const list = byFirst.get(own.bones[0]) ?? [];
    const hit = list.find((s) => sameSkeleton(s, own));
    if (!hit) { list.push(own); byFirst.set(own.bones[0], list); kept.push(own); continue; }
    if (hit === own) continue;
    // bind() would recompute the inverse bind matrix from the bind matrix; the mesh's own is kept.
    const bindMatrixInverse = mesh.bindMatrixInverse.clone();
    mesh.bind(hit, mesh.bindMatrix);
    mesh.bindMatrixInverse.copy(bindMatrixInverse);
    dropped.add(own);
  }
  for (const s of dropped) if (!meshes.some((m) => m.skeleton === s)) s.dispose();
  return { meshes: meshes.length, before: before.size, after: kept.length };
}
