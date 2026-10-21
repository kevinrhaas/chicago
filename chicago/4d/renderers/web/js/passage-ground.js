/**
 * passage-ground.js — T-2976: ground a building lays BELOW the field, and nothing else.
 *
 * Glessner's carriage passage is sunk: HABS sheet 6 runs the porte-cochère's floor and
 * its oak leaves down to 1.9 ft under the door datum (1.16 ft under the sidewalk), and
 * sheet 4 draws its court mouth about a foot under the court ground. The house's mesh
 * lays that floor, the approach falling to it from the walk and the ramp rising out of
 * it into the court. The field's own ground lies above all of it, so the renderer has to
 * cut the field out there and the walk has to step down onto the paving.
 *
 * compile_scene.py declares the pieces on the sidecar, `footprint.passages[].ground`,
 * from the generator's own `passage_ground()`: each a convex plan quad in the
 * footprint's frame and the paving's height at its four corners, over the structure's
 * anchor. This module turns them into world pieces (`passageGroundFrom`) and answers
 * how far below the field a point's paving is (`passageDepth`). terrain.js cuts the
 * field and offsets the walk with them; main.js keeps planting off them.
 *
 * Kept free of three.js and of walker.js/terrain.js so both can import it.
 */

const DEG = Math.PI / 180;

/** Sunk ground pieces of every structure in `registry`, in world [e, n]. */
export function passageGroundFrom(registry) {
  const out = [];
  for (const record of registry.values()) {
    const raw = record.sidecar?.footprint;
    const passages = Array.isArray(raw?.passages) ? raw.passages : [];
    if (!passages.some((one) => Array.isArray(one.ground))) continue;
    const p = record.sidecar.placement ?? {};
    const th = (p.rotation_deg ?? 0) * DEG;
    const cos = Math.cos(th);
    const sin = Math.sin(th);
    const e0 = p.local_e ?? 0;
    const n0 = p.local_n ?? 0;
    // Compass-bearing rotation, as walker.js footprintsFrom() places the footprint.
    const toWorld = ([u, v]) => [e0 + u * cos + v * sin, n0 - u * sin + v * cos];
    for (const passage of passages) {
      for (const g of passage.ground ?? []) {
        if (!Array.isArray(g.polygon) || g.polygon.length !== 4 || !Array.isArray(g.z_m)) continue;
        out.push({ id: record.id, pts: g.polygon.map(toWorld), z: g.z_m.map(Number) });
      }
    }
  }
  return out;
}

/** Height of `piece`'s paving over the field at (e, n), or null outside it. The quad
 *  is read as its two triangles (0, 1, 2) and (0, 2, 3), the way the mesh lays it. */
function depthIn(piece, e, n) {
  const [a, b, c, d] = piece.pts;
  for (const [i, j, k] of [[0, 1, 2], [0, 2, 3]]) {
    const P = [a, b, c, d];
    const [x0, y0] = P[i]; const [x1, y1] = P[j]; const [x2, y2] = P[k];
    const den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2);
    if (Math.abs(den) < 1e-12) continue;
    const w0 = ((y1 - y2) * (e - x2) + (x2 - x1) * (n - y2)) / den;
    const w1 = ((y2 - y0) * (e - x2) + (x0 - x2) * (n - y2)) / den;
    const w2 = 1 - w0 - w1;
    if (w0 >= -1e-9 && w1 >= -1e-9 && w2 >= -1e-9) {
      return w0 * piece.z[i] + w1 * piece.z[j] + w2 * piece.z[k];
    }
  }
  return null;
}

/** How far the sunk paving at (e, n) lies from the field (negative below it), or null
 *  where no piece covers the point. Where pieces meet, the first that holds it. */
export function passageDepth(pieces, e, n) {
  for (const piece of pieces) {
    const z = depthIn(piece, e, n);
    if (z !== null) return z;
  }
  return null;
}
