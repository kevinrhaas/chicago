// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3557 (Kevin, 2026-11-12: "ride the Glessner carriage"): the brougham's curbside door
 * opens, so a visitor can step up and get in.
 *
 * The brougham GLB has no door of its own: its right door is part of the body's surfaces
 * (vehicle_body/surface_vehicle_body_*). ROOT's door study (T-2797, chicago-evidence
 * evidence/transport/T2797/, source commit 74aea12f tools/transport/brougham/door-aperture.json)
 * drew the right leaf as a convex outline in the body's side view, hung it on a rear hinge
 * at (-0.655, 0, -0.43) m and swung it -65°; its producer was never delivered. Here the
 * same outline is cut out of THIS assembly's own parse of the vehicle, once, when the row
 * asks for it (`cab_door`): every body triangle is clipped exactly against the leaf's
 * convex regions, the inside pieces become the leaf (hung on the hinge) and the rest stay
 * the body. Closed, the two together are the body as it was, triangle for triangle (the
 * cut pieces only re-tessellated); open, the doorway is clear. The step (blackened iron)
 * is never cut and stays where it is. Hinge, outline, angle and swing are engineering
 * reconstructions, as ROOT's study says of them; not catalogue hardware (L-glessner-ride-3557).
 *
 * The clipping math below is plain arrays, so a node test can run it on the real GLB.
 */
import * as THREE from 'three';

const EPS = 1e-9;

/** Counter-clockwise convex hull of 2D points (monotone chain). */
export function convexHull2(points) {
  const p = points.map(q => [q[0], q[1]]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (p.length < 3) throw Error('cab door: an outline of at least three points is required');
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower = [], upper = [];
  for (const q of p) { while (lower.length >= 2 && cross(lower.at(-2), lower.at(-1), q) <= 0) lower.pop(); lower.push(q); }
  for (const q of p.reverse()) { while (upper.length >= 2 && cross(upper.at(-2), upper.at(-1), q) <= 0) upper.pop(); upper.push(q); }
  return lower.slice(0, -1).concat(upper.slice(0, -1));
}

/**
 * The leaf's convex regions in vehicle-root metres, each a list of half-spaces
 * { n: [x, y, z], d } with inside where n·p + d >= 0. The outline (side view, [y, z]) is
 * shared; each region adds its own x and y bands (`regions: [{ x_m: [lo, hi], y_m: [lo, hi] }]`),
 * so the leaf can take the thin door skins low down without the floor's edge above them.
 */
export function doorRegions(spec) {
  const hull = convexHull2(spec.profile_yz_m);
  const planes = [];
  for (let i = 0; i < hull.length; i++) {
    const a = hull[i], b = hull[(i + 1) % hull.length];
    // CCW in (y, z): inside is to the left of a->b. Left normal of (dy, dz) is (-dz, dy).
    const dy = b[0] - a[0], dz = b[1] - a[1], len = Math.hypot(dy, dz);
    if (len < 1e-9) continue;
    const ny = -dz / len, nz = dy / len;
    planes.push({ n: [0, ny, nz], d: -(ny * a[0] + nz * a[1]) });
  }
  return spec.regions.map(r => {
    const [x0, x1] = r.x_m, [y0, y1] = r.y_m;
    if (!(x1 > x0) || !(y1 > y0)) throw Error('cab door: each region needs increasing x and y bands');
    return { planes: [...planes, { n: [1, 0, 0], d: -x0 }, { n: [-1, 0, 0], d: x1 }, { n: [0, 1, 0], d: -y0 }, { n: [0, -1, 0], d: y1 }],
      box: { min: [x0, Math.max(y0, Math.min(...hull.map(q => q[0]))), Math.min(...hull.map(q => q[1]))],
        max: [x1, Math.min(y1, Math.max(...hull.map(q => q[0]))), Math.max(...hull.map(q => q[1]))] } };
  });
}

const side = (plane, v) => plane.n[0] * v.p[0] + plane.n[1] * v.p[1] + plane.n[2] * v.p[2] + plane.d;
const lerpVertex = (a, b, t) => ({ p: a.p.map((x, k) => x + (b.p[k] - x) * t), a: a.a.map((x, k) => x + (b.a[k] - x) * t) });
/** Sutherland–Hodgman: the part of a convex polygon on one side of a plane (keep >= 0, or < 0). */
function clipPolygon(poly, plane, keepInside) {
  const out = [];
  for (let i = 0; i < poly.length; i++) {
    const a = poly[i], b = poly[(i + 1) % poly.length];
    const da = keepInside ? side(plane, a) : -side(plane, a), db = keepInside ? side(plane, b) : -side(plane, b);
    if (da >= -EPS) out.push(a);
    if ((da >= -EPS) !== (db >= -EPS)) out.push(lerpVertex(a, b, da / (da - db)));
  }
  return out.length >= 3 ? out : null;
}
const area = poly => {
  let x = 0, y = 0, z = 0;
  for (let i = 1; i + 1 < poly.length; i++) {
    const a = poly[0].p, b = poly[i].p, c = poly[i + 1].p;
    const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], w = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    x += u[1] * w[2] - u[2] * w[1]; y += u[2] * w[0] - u[0] * w[2]; z += u[0] * w[1] - u[1] * w[0];
  }
  return Math.hypot(x, y, z) / 2;
};
/** The pieces of `poly` inside a convex region, and the pieces outside it (each convex). */
function splitByRegion(poly, region) {
  const outside = [];
  let rest = poly;
  for (const plane of region.planes) {
    const out = clipPolygon(rest, plane, false);
    if (out && area(out) > 1e-12) outside.push(out);
    rest = clipPolygon(rest, plane, true);
    if (!rest) break;
  }
  return { inside: rest && area(rest) > 1e-12 ? rest : null, outside };
}
const boxHits = (box, tri) => [0, 1, 2].every(k => Math.max(tri[0][k], tri[1][k], tri[2][k]) >= box.min[k] - EPS
  && Math.min(tri[0][k], tri[1][k], tri[2][k]) <= box.max[k] + EPS);

/**
 * Split one triangle mesh. `position` is Float32Array (xyz per vertex, vehicle-root metres);
 * `attributes` is { name: { array, itemSize } } of every other vertex stream (interpolated
 * linearly; `normal` and the xyz of `tangent` renormalised); `index` the triangle list.
 * Returns { body, leaf }: each { position, attributes, index } (the body keeps every original
 * vertex and untouched triangle; cut pieces are new vertices), and the areas for a check.
 */
export function splitMesh({ position, attributes = {}, index }, regions) {
  const names = Object.keys(attributes);
  const count = position.length / 3;
  const tri = index ?? Uint32Array.from({ length: count }, (_, i) => i);
  const vertex = i => {
    const a = [];
    for (const name of names) { const { array, itemSize } = attributes[name]; for (let k = 0; k < itemSize; k++) a.push(array[i * itemSize + k]); }
    return { p: [position[i * 3], position[i * 3 + 1], position[i * 3 + 2]], a };
  };
  const kept = [], cutBody = [], leaf = [];
  let areaIn = 0, areaBody = 0, areaLeaf = 0;
  for (let t = 0; t < tri.length; t += 3) {
    const ids = [tri[t], tri[t + 1], tri[t + 2]];
    const corners = ids.map(i => [position[i * 3], position[i * 3 + 1], position[i * 3 + 2]]);
    if (!regions.some(r => boxHits(r.box, corners))) { kept.push(...ids); continue; }
    // A triangle wholly beyond one plane of every region is the body's, untouched.
    const beyond = r => r.planes.some(pl => corners.every(c => pl.n[0] * c[0] + pl.n[1] * c[1] + pl.n[2] * c[2] + pl.d < -EPS));
    if (regions.every(beyond)) { kept.push(...ids); continue; }
    const poly = ids.map(vertex);
    const a0 = area(poly); areaIn += a0;
    let pieces = [poly];
    for (const region of regions) {
      const next = [];
      for (const piece of pieces) {
        const { inside, outside } = splitByRegion(piece, region);
        if (inside) leaf.push(inside);
        next.push(...outside);
      }
      pieces = next;
    }
    cutBody.push(...pieces);
  }
  for (const p of cutBody) areaBody += area(p);
  for (const p of leaf) areaLeaf += area(p);
  const sizes = names.map(n => attributes[n].itemSize);
  const pack = (polys, base, appendTo = null) => {
    const verts = [], idx = [];
    let n = base;
    for (const poly of polys) {
      const start = n;
      for (const v of poly) { verts.push(v); n++; }
      for (let i = 1; i + 1 < poly.length; i++) idx.push(start, start + i, start + i + 1);
    }
    const pos = new Float32Array((appendTo ? count : 0) * 3 + verts.length * 3);
    if (appendTo) pos.set(position);
    const off = appendTo ? count : 0;
    verts.forEach((v, i) => pos.set(v.p, (off + i) * 3));
    const attrs = {};
    names.forEach((name, j) => {
      const size = sizes[j], src = attributes[name].array, Kind = src.constructor === Float64Array ? Float64Array : Float32Array;
      const arr = new Kind((off + verts.length) * size);
      if (appendTo) arr.set(src);
      let at = 0; for (let q = 0; q < j; q++) at += sizes[q];
      verts.forEach((v, i) => { for (let k = 0; k < size; k++) arr[(off + i) * size + k] = v.a[at + k]; });
      if (name === 'normal' || name === 'tangent') for (let i = off; i < off + verts.length; i++) {
        const l = Math.hypot(arr[i * size], arr[i * size + 1], arr[i * size + 2]) || 1;
        for (let k = 0; k < 3; k++) arr[i * size + k] /= l;
      }
      attrs[name] = { array: arr, itemSize: size };
    });
    return { position: pos, attributes: attrs, index: idx };
  };
  const body = pack(cutBody, count, true);
  body.index = Uint32Array.from([...kept, ...body.index]);
  const leafMesh = pack(leaf, 0, false);
  leafMesh.index = Uint32Array.from(leafMesh.index);
  return { body, leaf: leafMesh, cut: { triangles_read: tri.length / 3, kept: kept.length / 3,
    body_pieces: cutBody.length, leaf_pieces: leaf.length, area_cut_m2: areaIn, area_body_m2: areaBody, area_leaf_m2: areaLeaf } };
}

/** The door's eased swing: fraction 0 shut .. 1 open, `duration_s` either way. */
export function doorSwing({ duration_s = 1.6 } = {}) {
  let fraction = 0, target = 0;
  return {
    get fraction() { return fraction; },
    get state() { return fraction === target ? (target ? 'open' : 'shut') : target ? 'opening' : 'closing'; },
    open() { target = 1; }, close() { target = 0; },
    set(f) { fraction = target = Math.max(0, Math.min(1, f)); },
    update(dt, { reducedMotion = false } = {}) {
      if (!(dt >= 0)) return fraction;
      if (reducedMotion) fraction = target;
      else fraction = target > fraction ? Math.min(target, fraction + dt / duration_s) : Math.max(target, fraction - dt / duration_s);
      return fraction;
    },
  };
}
const ease = f => f * f * (3 - 2 * f);

/**
 * Cut the door out of a loaded brougham (`vehicle`, its GLB scene, before anything else
 * patches or batches it) per the row's `cab_door`, and hang it. Returns the door:
 * open()/close() (Promises resolved when it stands open/shut), update(dt), fraction, state,
 * angle_deg, leaf (the Group), cut (the counts, for a test), dispose().
 */
export function createCabDoor(vehicle, spec) {
  if (!vehicle?.getObjectByName || !spec || !Array.isArray(spec.hinge_local_m) || !Number.isFinite(spec.open_deg)
    || !Array.isArray(spec.profile_yz_m) || !Array.isArray(spec.regions)) throw Error('cab door: a vehicle and its door outline, hinge and swing are required');
  const regions = doorRegions(spec);
  const bodyNode = vehicle.getObjectByName(spec.body_node ?? 'vehicle_body');
  if (!bodyNode) throw Error('cab door: the vehicle body node is missing');
  const skip = new RegExp(spec.uncut_materials ?? 'iron');
  vehicle.updateMatrixWorld(true);
  const toVehicle = new THREE.Matrix4().copy(vehicle.matrixWorld).invert();
  const pivot = new THREE.Group(); pivot.name = 'cab_door_right';
  pivot.position.fromArray(spec.hinge_local_m);
  const hung = new THREE.Group(); hung.name = 'cab_door_leaf';
  hung.position.set(-spec.hinge_local_m[0], -spec.hinge_local_m[1], -spec.hinge_local_m[2]);
  pivot.add(hung);
  const owned = [], cut = { meshes: 0, leaf_triangles: 0, body_triangles: 0, area_cut_m2: 0, area_body_m2: 0, area_leaf_m2: 0 };
  const meshes = [];
  bodyNode.traverse(node => { if (node.isMesh && !node.isSkinnedMesh) meshes.push(node); });
  for (const mesh of meshes) {
    if (Array.isArray(mesh.material) || skip.test(mesh.material?.name ?? '')) continue;
    const g = mesh.geometry, pos = g.getAttribute('position');
    if (!pos || pos.isInterleavedBufferAttribute) continue;
    const toLocal = new THREE.Matrix4().multiplyMatrices(toVehicle, mesh.matrixWorld);
    const back = toLocal.clone().invert(), normalBack = new THREE.Matrix3().getNormalMatrix(back);
    const normalTo = new THREE.Matrix3().getNormalMatrix(toLocal);
    const v = new THREE.Vector3();
    const position = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(toLocal); position.set([v.x, v.y, v.z], i * 3); }
    const attributes = {};
    for (const [name, attr] of Object.entries(g.attributes)) {
      if (name === 'position' || attr.isInterleavedBufferAttribute) continue;
      const array = new Float32Array(attr.count * attr.itemSize);
      for (let i = 0; i < attr.count; i++) for (let k = 0; k < attr.itemSize; k++) array[i * attr.itemSize + k] = attr.getComponent(i, k);
      if (name === 'normal') for (let i = 0; i < attr.count; i++) {
        v.fromArray(array, i * 3).applyMatrix3(normalTo).normalize(); v.toArray(array, i * 3);
      }
      attributes[name] = { array, itemSize: attr.itemSize, normalized: attr.normalized };
    }
    const index = g.index ? Uint32Array.from(g.index.array) : null;
    const split = splitMesh({ position, attributes, index }, regions);
    if (!split.leaf.index.length) continue;
    const make = (part, local) => {
      const out = new THREE.BufferGeometry();
      const p = part.position.slice();
      if (local) for (let i = 0; i < p.length; i += 3) { v.fromArray(p, i).applyMatrix4(back); v.toArray(p, i); }
      out.setAttribute('position', new THREE.BufferAttribute(p, 3));
      for (const [name, a] of Object.entries(part.attributes)) {
        const arr = Float32Array.from(a.array);
        if (local && name === 'normal') for (let i = 0; i < arr.length; i += 3) { v.fromArray(arr, i).applyMatrix3(normalBack).normalize(); v.toArray(arr, i); }
        out.setAttribute(name, new THREE.BufferAttribute(arr, a.itemSize));
      }
      out.setIndex(new THREE.BufferAttribute(part.index, 1));
      out.computeBoundingBox(); out.computeBoundingSphere();
      return out;
    };
    const old = mesh.geometry;
    mesh.geometry = make(split.body, true);
    old.dispose();
    const leafMesh = new THREE.Mesh(make(split.leaf, false), mesh.material);
    leafMesh.name = `${mesh.name}:door`;
    leafMesh.castShadow = mesh.castShadow; leafMesh.receiveShadow = mesh.receiveShadow;
    hung.add(leafMesh);
    owned.push(leafMesh.geometry);
    cut.meshes++; cut.leaf_triangles += split.leaf.index.length / 3; cut.body_triangles += split.body.index.length / 3;
    cut.area_cut_m2 += split.cut.area_cut_m2; cut.area_body_m2 += split.cut.area_body_m2; cut.area_leaf_m2 += split.cut.area_leaf_m2;
  }
  if (!cut.meshes) throw Error('cab door: nothing of the body lies inside the door outline');
  // The pivot hangs from the vehicle root, in the frame the outline was drawn in.
  vehicle.add(pivot);
  const swing = doorSwing({ duration_s: spec.duration_s ?? 1.6 });
  const waiting = [];
  const settle = () => {
    for (let i = waiting.length - 1; i >= 0; i--) {
      const w = waiting[i];
      if (swing.state === w.want) { waiting.splice(i, 1); w.resolve(true); }
    }
  };
  const pose = () => { pivot.rotation.y = ease(swing.fraction) * spec.open_deg * Math.PI / 180; pivot.updateMatrixWorld(true); };
  let disposed = false;
  const door = {
    leaf: pivot, cut, spec,
    get fraction() { return swing.fraction; },
    get state() { return swing.state; },
    get angle_deg() { return ease(swing.fraction) * spec.open_deg; },
    open() { swing.open(); return new Promise(resolve => { waiting.push({ want: 'open', resolve }); settle(); }); },
    close() { swing.close(); return new Promise(resolve => { waiting.push({ want: 'shut', resolve }); settle(); }); },
    set(f) { swing.set(f); pose(); settle(); },
    update(dt, options) { if (disposed) return; swing.update(dt, options); pose(); settle(); },
    dispose() {
      if (disposed) return;
      disposed = true; pivot.removeFromParent();
      for (const g of owned) g.dispose();
      for (const w of waiting.splice(0)) w.resolve(false);
    },
  };
  pose();
  return door;
}
