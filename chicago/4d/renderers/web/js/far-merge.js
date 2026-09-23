/**
 * far-merge.js — give a draw call back when chunking has stopped buying
 * anything with it.
 *
 * T-0146, the second of T-0149's three pieces. The first (T-0150) stopped
 * drawing furniture beyond a reach at `light`. This one is about the two tiers
 * that have no reach: `full` and `balanced`, where the axial stands draw the
 * whole town and every chunk is its own call.
 *
 * ## The trade this undoes, exactly where it stops paying
 *
 * The 2026-08-21 chunking (T-0067, T-0068, T-0069, T-0119) deliberately
 * converted triangles into draw calls: one town-wide fence mesh has a bounding
 * sphere no frustum can cull, so 33,166 triangles of fence were drawn in every
 * frame including the fences behind you. Splitting the layer into patches of
 * ground gives the frustum something to skip, and at an ordinary stand it skips
 * a lot. `main.js` § BUDGET says so in the same words: *"the call count is the
 * price of the culling that keeps those ceilings reachable"*.
 *
 * A price is only worth paying while something is bought with it. Down Lake
 * Street from Canal nothing is behind the camera, the whole town is inside the
 * frustum, and the frustum skips **nothing** — so the chunk boundaries in that
 * frame are pure loss: 53 calls for the wagon yard's 64,640 triangles, 48 for
 * the fences, 38 for the plank walks, measured on the published mirror at
 * `full` (`tools/measure_stand_budget.mjs --stand lake_at_canal`). This module
 * watches for exactly that condition and, while it holds, submits the chunks as
 * ONE mesh instead of many.
 *
 * ## The two conditions, and why each one makes the merge free
 *
 * A cluster is a fixed patch of ground — `CLUSTER_M` across — holding the chunk
 * meshes whose own spheres centre inside it. It is merged for a frame only when
 * BOTH of these are true of the cluster's bounding sphere:
 *
 *  1. **It is wholly inside the view frustum.** Then no member of it could have
 *    been culled this frame, so drawing the cluster as one mesh submits the
 *    identical set of triangles — the saving is in calls and the triangle count
 *    is unchanged, not approximately but exactly. This is the condition that
 *    matters: the headroom under these ceilings had four figures at the axial
 *    stands when this was written (1,423,855 against 1,425,000 at `full`), and
 *    has six only because T-0223 culled the sun's pass over the far timber and
 *    T-0229 then handed the raise back — 1,207,211 against 1,400,000 down Lake
 *    Street today. A merge that could ADD a triangle would be a worse bargain
 *    than the calls it saves, at either figure. It cannot.
 *  2. **Every part of it is more than `FAR_M` from the eye.** The sun's pass
 *    draws a caster a second time, and its rig is an orthographic box `±r` in
 *    LIGHT space around the visitor (`world.setShadowRig`), r = 240 m at `full`
 *    and `balanced`. A point whose light-space |x| and |y| are both within 240
 *    lies within 240·√2 = 339.4 m of the centre, so anything beyond 340 m is
 *    outside that box whatever the sun's bearing. A merged cluster is therefore
 *    made of meshes that were contributing nothing to the shadow map, the
 *    merged mesh does not cast, and the shadow pass reads the same before and
 *    after. No bound, no tuning: a stated distance and the geometry of a box.
 *
 * Composition with T-0150 is the third condition and it is not a bound either:
 * a cluster with any member the reach is holding back is left alone, so at
 * `light` — where the reach is 300 m and this module's floor is 340 — nothing
 * is ever merged and nothing here can put back a triangle that tier gave up.
 *
 * ## What it is not
 *
 * It is not an LOD and not a simplification: no vertex is moved, dropped or
 * re-typed, no material changes, and the confidence attribute rides along in
 * the merged buffer so the confidence view colours a merged cluster exactly as
 * it colours the chunks. It is a change of BATCHING and nothing else — which is
 * why it can be applied at every tier without the tier meaning something
 * different.
 *
 * Picking is untouched for the same reason it has to be: the chunk meshes stay
 * in the scene and in the arrays each layer raycasts (`enclosures.pickAt`,
 * `yard.pickAt`, …). `THREE.Raycaster` does not test `visible` — it walks the
 * array it is handed — so a merged-away chunk still answers a click with its
 * own `pickId` and its own chunk-local `faceIndex`. The merged mesh itself is
 * given an empty `raycast` so it can never answer instead.
 *
 * Buffers are built LAZILY, the first frame a cluster actually qualifies, and
 * then kept. A cluster a visitor never stands far enough back from never costs
 * a byte, and a town walked end to end settles at roughly one extra copy of the
 * merged layers' vertex data.
 */
import * as THREE from 'three';

/**
 * How far a cluster may reach, in metres. Bigger clusters save more calls and
 * qualify less often — condition 1 asks the WHOLE cluster to be in frustum, and
 * a cluster subtending more than the field of view can never satisfy it. At the
 * 340 m floor a 200 m patch subtends at most about 33°, inside the 62° field,
 * so the two constants are chosen together rather than independently.
 */
const CLUSTER_M = 200;
/** The shadow floor derived above: 240 · √2 = 339.4, rounded up. */
const FAR_M = 340;
/**
 * Below this many members a cluster is left chunked. Merging two meshes saves
 * one call and costs a copy of their vertices; the copy is only worth making
 * where the call count is the thing being complained about.
 */
const MIN_MEMBERS = 4;

/** The signature two meshes must share to be mergeable at all. */
function signatureOf(mesh) {
  const geo = mesh.geometry;
  if (!geo || !geo.attributes?.position) return null;
  const names = Object.keys(geo.attributes).sort();
  const attrs = names.map((n) => {
    const a = geo.attributes[n];
    // An interleaved or instanced attribute has no plain array to concatenate,
    // and a morph target would need its own pass. Neither exists in these
    // layers today; refusing them here is what keeps that true.
    if (!a.array || a.isInterleavedBufferAttribute || a.isInstancedBufferAttribute) return null;
    return `${n}:${a.itemSize}:${a.array.constructor.name}:${a.normalized ? 1 : 0}`;
  });
  if (attrs.some((a) => a === null)) return null;
  if (geo.morphAttributes && Object.keys(geo.morphAttributes).length) return null;
  if (geo.groups && geo.groups.length > 1) return null;
  const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  if (mats.length !== 1 || !mats[0]) return null;
  return `${mats[0].uuid}|${geo.index ? 'i' : 'n'}|${attrs.join(',')}`;
}

/** The relative transform from a mesh's own space into its parent group's. */
const _inv = new THREE.Matrix4();
const _rel = new THREE.Matrix4();
const _identity = new THREE.Matrix4();
function relativeMatrix(mesh, group) {
  group.updateWorldMatrix(true, false);
  mesh.updateWorldMatrix(true, false);
  _inv.copy(group.matrixWorld).invert();
  return _rel.multiplyMatrices(_inv, mesh.matrixWorld);
}

/**
 * Concatenate a cluster's members into one geometry, in the parent group's
 * space. Returns null if anything about the set refuses — a refusal costs the
 * cluster its merge and nothing else.
 */
function mergeGeometries(members, group) {
  const first = members[0].geometry;
  const names = Object.keys(first.attributes);
  const indexed = !!first.index;
  let verts = 0;
  let indices = 0;
  for (const m of members) {
    verts += m.geometry.attributes.position.count;
    if (indexed) indices += m.geometry.index.count;
  }
  const out = new THREE.BufferGeometry();
  const dst = {};
  for (const name of names) {
    const src = first.attributes[name];
    dst[name] = { array: new src.array.constructor(verts * src.itemSize), at: 0, src };
  }
  const idx = indexed
    ? (verts > 65535 ? new Uint32Array(indices) : new Uint16Array(indices))
    : null;
  let idxAt = 0;
  let base = 0;
  const p = new THREE.Vector3();
  const nrm = new THREE.Matrix3();
  for (const mesh of members) {
    const geo = mesh.geometry;
    const rel = relativeMatrix(mesh, group);
    const moved = !rel.equals(_identity);
    if (moved) nrm.getNormalMatrix(rel);
    const count = geo.attributes.position.count;
    for (const name of names) {
      const src = geo.attributes[name];
      const slot = dst[name];
      if (!src || src.itemSize !== slot.src.itemSize) return null;
      if (moved && (name === 'position' || name === 'normal')) {
        for (let i = 0; i < count; i++) {
          p.fromBufferAttribute(src, i);
          if (name === 'position') p.applyMatrix4(rel);
          else p.applyMatrix3(nrm).normalize();
          slot.array[slot.at + i * 3] = p.x;
          slot.array[slot.at + i * 3 + 1] = p.y;
          slot.array[slot.at + i * 3 + 2] = p.z;
        }
      } else {
        slot.array.set(src.array.subarray(0, count * src.itemSize), slot.at);
      }
      slot.at += count * src.itemSize;
    }
    if (indexed) {
      const src = geo.index;
      for (let i = 0; i < src.count; i++) idx[idxAt + i] = src.getX(i) + base;
      idxAt += src.count;
    }
    base += count;
  }
  for (const name of names) {
    const slot = dst[name];
    out.setAttribute(name, new THREE.BufferAttribute(
      slot.array, slot.src.itemSize, slot.src.normalized));
  }
  if (indexed) out.setIndex(new THREE.BufferAttribute(idx, 1));
  out.computeBoundingSphere();
  out.computeBoundingBox();
  return out;
}

/**
 * @param {object} opts
 * @param {THREE.Object3D} opts.scene the scene the layer groups hang from
 * @param {THREE.Camera} opts.camera the visitor's camera
 * @param {string[]} opts.layers the group names eligible for merging
 */
export function createFarMerge({ scene, camera, layers }) {
  /** @type {Array<{group:THREE.Object3D, members:THREE.Mesh[], c:THREE.Vector3,
   *                r:number, mesh:THREE.Mesh|null, tris:number, refused:boolean}>} */
  let clusters = [];
  const frustum = new THREE.Frustum();
  const viewProj = new THREE.Matrix4();
  const census = { clusters: 0, merged: 0, callsSaved: 0, built: 0, builtTris: 0 };
  /**
   * HARNESS ONLY, and never a visitor setting. The saving has to be measured by
   * turning the merge off and reading the same frame twice — the pattern T-0150
   * established for the reach — because a figure taken from two different trees
   * can be satisfied by any unrelated layer getting cheaper, and because the
   * claim that the triangle count is UNCHANGED is only checkable that way.
   */
  let enabled = true;

  /** A conservative sphere over a set of member world spheres. */
  function enclose(members) {
    let minX = Infinity; let minY = Infinity; let minZ = Infinity;
    let maxX = -Infinity; let maxY = -Infinity; let maxZ = -Infinity;
    for (const m of members) {
      minX = Math.min(minX, m.c.x - m.r); maxX = Math.max(maxX, m.c.x + m.r);
      minY = Math.min(minY, m.c.y - m.r); maxY = Math.max(maxY, m.c.y + m.r);
      minZ = Math.min(minZ, m.c.z - m.r); maxZ = Math.max(maxZ, m.c.z + m.r);
    }
    const c = new THREE.Vector3((minX + maxX) / 2, (minY + maxY) / 2, (minZ + maxZ) / 2);
    let r = 0;
    for (const m of members) r = Math.max(r, c.distanceTo(m.c) + m.r);
    return { c, r };
  }

  /**
   * Re-read the layers and re-cluster. Called wherever the furniture's banked
   * spheres are re-read (`collectFurniture` in main.js), for the same reason:
   * a rebuilt layer has new meshes and disposed old ones, and a cluster holding
   * a disposed mesh would draw a buffer that is gone.
   *
   * @param {Array<{mesh:THREE.Mesh, c:THREE.Vector3, r:number}>} banked
   *   the world spheres main.js has already computed, so this walks nothing twice
   */
  function rebuild(banked) {
    dispose();
    const buckets = new Map();
    for (const entry of banked) {
      const mesh = entry.mesh;
      if (mesh.userData.farMerged) continue;
      const group = mesh.parent;
      if (!group || !layers.includes(group.name)) continue;
      const sig = signatureOf(mesh);
      if (!sig) continue;
      const cell = `${Math.floor(entry.c.x / CLUSTER_M)},${Math.floor(entry.c.z / CLUSTER_M)}`;
      const key = `${group.name}|${cell}|${sig}`;
      let b = buckets.get(key);
      if (!b) { b = { group, members: [] }; buckets.set(key, b); }
      b.members.push(entry);
    }
    for (const b of buckets.values()) {
      if (b.members.length < MIN_MEMBERS) continue;
      const { c, r } = enclose(b.members);
      clusters.push({
        group: b.group, members: b.members.map((m) => m.mesh),
        c, r, mesh: null, tris: 0, refused: false,
      });
    }
    census.clusters = clusters.length;
    census.merged = 0;
    census.callsSaved = 0;
  }

  /** Build a cluster's merged mesh the first frame it is actually wanted. */
  function ensure(cl) {
    if (cl.mesh || cl.refused) return cl.mesh;
    const geo = mergeGeometries(cl.members, cl.group);
    if (!geo) { cl.refused = true; return null; }
    const src = cl.members[0];
    const mesh = new THREE.Mesh(geo, src.material);
    mesh.name = `${cl.group.name}-far-merge`;
    mesh.visible = false;
    // Never a caster: condition 2 guarantees every member was already outside
    // the sun's box, so this is the shadow pass reading exactly what it read.
    mesh.castShadow = false;
    mesh.receiveShadow = src.receiveShadow;
    mesh.renderOrder = src.renderOrder;
    mesh.userData.farMerged = true;
    // The chunks answer clicks, and they still do — this must never intercept
    // one, whatever raycasts the scene.
    mesh.raycast = () => {};
    cl.group.add(mesh);
    cl.mesh = mesh;
    const pos = geo.attributes.position.count;
    cl.tris = Math.floor((geo.index ? geo.index.count : pos) / 3);
    census.built += 1;
    census.builtTris += cl.tris;
    return mesh;
  }

  /**
   * Per frame, after the reach has settled this frame's visibility. Cheap by
   * construction: one sphere against six planes and one distance per cluster,
   * over a few dozen clusters, with no allocation.
   */
  function update() {
    if (!clusters.length) return;
    if (!enabled) {
      for (const cl of clusters) if (cl.mesh) cl.mesh.visible = false;
      census.merged = 0;
      census.callsSaved = 0;
      return;
    }
    camera.updateMatrixWorld();
    viewProj.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    frustum.setFromProjectionMatrix(viewProj);
    const eye = camera.position;
    let merged = 0;
    let saved = 0;
    for (const cl of clusters) {
      let want = !cl.refused && eye.distanceTo(cl.c) - cl.r > FAR_M;
      if (want) {
        for (const pl of frustum.planes) {
          if (pl.distanceToPoint(cl.c) < cl.r) { want = false; break; }
        }
      }
      // T-0150 composes ahead of this one: a cluster the reach is holding back,
      // even partly, keeps the reach's answer.
      if (want) {
        for (const m of cl.members) {
          if (m.userData.reachCulled) { want = false; break; }
        }
      }
      if (want && !ensure(cl)) want = false;
      if (cl.mesh) cl.mesh.visible = want;
      if (want) {
        for (const m of cl.members) m.visible = false;
        merged += 1;
        saved += cl.members.length - 1;
      }
    }
    census.merged = merged;
    census.callsSaved = saved;
  }

  function dispose() {
    for (const cl of clusters) {
      if (!cl.mesh) continue;
      cl.group.remove(cl.mesh);
      cl.mesh.geometry.dispose();
    }
    clusters = [];
    census.clusters = 0;
    census.merged = 0;
    census.callsSaved = 0;
  }

  return {
    rebuild,
    update,
    dispose,
    /** @param {boolean} on — harness only; see `enabled` above. */
    setEnabled(on) { enabled = !!on; update(); return enabled; },
    /** What the merge is doing at this instant — read off the clusters, never
     *  off the constants that asked for it. */
    get state() {
      return {
        clusterM: CLUSTER_M, farM: FAR_M, minMembers: MIN_MEMBERS,
        enabled,
        clusters: census.clusters, merged: census.merged,
        callsSaved: census.callsSaved,
        built: census.built, builtTris: census.builtTris,
        layers: layers.slice(),
      };
    },
    scene,
  };
}
