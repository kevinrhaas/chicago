/** T-2495: consume generated context coast/GLB sidecars. The core stays authoritative. */
import * as THREE from 'three';

export function coastE(line, n) {
  // Generated north-to-south stations. Clamp beyond the context-map boundary.
  if (n >= line[0][1]) return line[0][0];
  if (n <= line.at(-1)[1]) return line.at(-1)[0];
  let lo = 0, hi = line.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (line[mid][1] >= n) lo = mid; else hi = mid;
  }
  const f = (n - line[lo][1]) / (line[hi][1] - line[lo][1]);
  return line[lo][0] + f * (line[hi][0] - line[lo][0]);
}

export function contextSample(hf, e, n, sampleCore) {
  const e0 = hf.originE, e1 = e0 + hf.widthM;
  const n0 = hf.originN, n1 = n0 + hf.depthM;
  if (n < n0 || n > n1) {
    const side = hf.contextCoast[n > n1 ? 'north' : 'south'];
    e -= coastE(side.shoreline_local_m, n) - side.join_shore_e;
  }
  return sampleCore(Math.max(e0, Math.min(e1, e)), Math.max(n0, Math.min(n1, n)));
}

/** Replace only the baked, straight apron with the generated mapped apron.
 * Compact the used core vertices, so unused old apron vertices cannot inflate bounds.
 * Normals/confidence come from each GLB; no terrain or historical model lives here.
 */
export function replaceApron(core, apron, hf) {
  const result = new THREE.BufferGeometry();
  const attrs = ['position', 'normal', '_confidence'];
  const values = Object.fromEntries(attrs.map(k => [k, []]));
  const indices = [];
  for (const [geo, isCore] of [[core, true], [apron, false]]) {
    const p = geo.attributes.position;
    const ix = geo.index;
    const count = ix?.count ?? p.count;
    const ids = new Map();
    const pick = (v) => {
      if (ids.has(v)) return ids.get(v);
      const id = values.position.length / 3;
      ids.set(v, id);
      for (const key of attrs) {
        const a = geo.attributes[key];
        if (key === '_confidence') values[key].push(a ? a.getX(v) : 1);
        else values[key].push(a.getX(v), a.getY(v), a.getZ(v));
      }
      return id;
    };
    for (let i = 0; i < count; i += 3) {
      const tri = [0, 1, 2].map(k => ix ? ix.getX(i + k) : i + k);
      if (isCore && !tri.every(v => hf.contains(p.getX(v), -p.getZ(v)))) continue;
      for (const v of tri) indices.push(pick(v));
    }
  }
  for (const k of attrs) result.setAttribute(k, new THREE.Float32BufferAttribute(values[k], k === '_confidence' ? 1 : 3));
  result.setIndex(indices);
  result.computeBoundingBox();
  result.computeBoundingSphere();
  return result;
}
