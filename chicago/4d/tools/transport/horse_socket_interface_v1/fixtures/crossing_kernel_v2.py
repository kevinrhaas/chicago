"""Compare proper static body-surface crossings with the immutable parent.

Tests open triangle interiors, including coplanar area overlap. Shared edges,
isolated contact and separations below the declared numerical tolerance are not
interior crossings. This does not certify watertightness or continuous motion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

APP = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(APP / 'assets/authored/transport/horse_standing'))
import generate_anatomy_v2 as anatomy

TOL = 1e-9


def crosses(a, b):
    """Strict edge/face crossing, or positive-area coplanar overlap."""
    na, nb = np.cross(a[1]-a[0], a[2]-a[0]), np.cross(b[1]-b[0], b[2]-b[0])
    na, nb = na / np.linalg.norm(na), nb / np.linalg.norm(nb)
    da, db = (a-b[0]) @ nb, (b-a[0]) @ na
    if (np.min(da) >= TOL or np.max(da) <= -TOL or
            np.min(db) >= TOL or np.max(db) <= -TOL):
        return False
    if np.max(np.abs(da)) <= TOL and np.max(np.abs(db)) <= TOL:
        keep = [i for i in range(3) if i != int(np.argmax(np.abs(na)))]
        x, y = a[:, keep], b[:, keep]
        for tri in (x, y):
            for k in range(3):
                edge = tri[(k+1) % 3]-tri[k]
                axis = np.array([-edge[1], edge[0]])
                axis /= np.linalg.norm(axis)
                p, q = x @ axis, y @ axis
                if min(p.max(), q.max()) - max(p.min(), q.min()) <= TOL:
                    return False
        return True
    # Each triangle cuts the opposite plane in an interval on the same line.
    # Overlap can lie inside BOTH triangles even when every interval endpoint
    # lands on both boundaries; testing only strict edge/face hits misses that.
    direction = np.cross(na, nb)
    direction /= np.linalg.norm(direction)
    intervals = []
    reference = None
    for source, distance in ((a, da), (b, db)):
        points = [source[k] for k in range(3) if abs(distance[k]) <= TOL]
        for k in range(3):
            j = (k+1) % 3
            if distance[k] * distance[j] < 0:
                t = distance[k] / (distance[k]-distance[j])
                points.append(source[k] + t*(source[j]-source[k]))
        if len(points) < 2:
            return False
        if reference is None:
            reference = points[0]
        values = np.array(points) @ direction
        intervals.append((values.min(), values.max()))
    low, high = max(v[0] for v in intervals), min(v[1] for v in intervals)
    if high-low <= TOL:
        return False
    midpoint = reference + direction*((low+high)/2 - np.dot(reference, direction))
    # A line along an actual triangle edge is a boundary touch, not an open-
    # interior crossing, even when the other triangle straddles that line.
    for triangle, normal in ((a, na), (b, nb)):
        for k in range(3):
            edge = triangle[(k+1) % 3]-triangle[k]
            side = np.dot(np.cross(edge, midpoint-triangle[k]), normal) / np.linalg.norm(edge)
            if side <= TOL:
                return False
    return True


def mesh(path):
    raw = path.read_bytes()
    doc, binary = anatomy.base.read_glb(raw)
    primitive = doc['meshes'][1]['primitives'][0]
    positions = np.array(anatomy.read_attribute(doc, binary, primitive['attributes']['POSITION']))
    indices = np.array(anatomy.read_attribute(doc, binary, primitive['indices'])).reshape(-1, 3)
    return raw, positions[indices]


def pairs(triangles):
    lo, hi = triangles.min(axis=1), triangles.max(axis=1)
    result, broad = [], 0
    for i in range(len(triangles)-1):
        mask = np.all(lo[i+1:] <= hi[i]+TOL, axis=1) & np.all(hi[i+1:] >= lo[i]-TOL, axis=1)
        for j in np.flatnonzero(mask) + i+1:
            broad += 1
            if crosses(triangles[i], triangles[j]):
                result.append((i, int(j)))
    return result, broad


def self_test():
    a = np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
    assert crosses(a, np.array([[.2,.2,-1.],[.2,.2,1.],[.4,.2,1.]]))
    # Independent-review counterexample: interval endpoints both on boundaries.
    boundary_endpoints = np.array([[0.,.25,-1.],[0.,.25,1.],[.75,.25,0.]])
    assert crosses(a, boundary_endpoints)
    assert crosses(boundary_endpoints, a)
    assert not crosses(a, np.array([[0.,0.,-1.],[0.,0.,1.],[1.,0.,0.]]))
    assert crosses(a, np.array([[.1,.1,0.],[.6,.1,0.],[.1,.6,0.]]))
    assert not crosses(a, a + [0,0,.01])
    assert not crosses(a, np.array([[0.,0.,0.],[1.,0.,0.],[0.,-1.,0.]]))
    assert not crosses(a, np.array([[1.,0.,0.],[2.,0.,0.],[1.,1.,0.]]))
    crossing = np.array([[.2,.2,-1.],[.2,.2,1.],[.4,.2,1.]])
    before, _ = pairs(np.array([a, crossing + [0,0,3.]]))
    after, _ = pairs(np.array([a, crossing]))
    assert before == [] and after == [(0, 1)]
    assert introduced_parent_pairs(before, after, {0:0, 1:1}) == [(0, 1)]
    assert introduced_parent_pairs(after, after, {0:0, 1:1}) == []
    # Different children of one original face are not exempt from proper overlap.
    assert introduced_parent_pairs([], after, {0:5, 1:5}) == [(0, 1)]


def introduced_parent_pairs(before, after, owners):
    old_pairs = set(before)
    return [pair for pair in after if tuple(sorted(owners[v] for v in pair)) not in old_pairs]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    self_test()
    started = time.monotonic()
    parent_raw, old = mesh(args.parent)
    candidate_raw, new = mesh(args.candidate)
    receipt = json.loads(args.receipt.read_text())
    assert receipt['candidate_sha256'] == hashlib.sha256(candidate_raw).hexdigest()
    mapping = receipt['source_boundary']['hoof_refinement']['source_face_to_children']
    owners = {child: parent for parent, children in enumerate(mapping) for child in children}
    assert sorted(owners) == list(range(len(new)))
    before, old_broad = pairs(old)
    after, new_broad = pairs(new)
    introduced = introduced_parent_pairs(before, after, owners)
    result = {'schema':'horse-anatomy-static-body-proper-crossings-v2',
        'parent_sha256':hashlib.sha256(parent_raw).hexdigest(),
        'candidate_sha256':hashlib.sha256(candidate_raw).hexdigest(),
        'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'tolerance_m':TOL, 'parent_triangles':len(old), 'candidate_triangles':len(new),
        'parent_aabb_pairs':old_broad, 'candidate_aabb_pairs':new_broad,
        'parent_proper_crossings':before, 'candidate_proper_crossings':after,
        'new_parent_pair_crossings':introduced, 'elapsed_seconds':time.monotonic()-started,
        'status':'NO_NEW_PROPER_STATIC_BODY_CROSSINGS' if not introduced else 'NEW_PROPER_STATIC_BODY_CROSSINGS',
        'scope':'Canonical static body primitive only; triangle-plane interval overlap with open-interior midpoint tests and coplanar positive-area overlaps at 1nm tolerance. Boundary contact, watertightness, eye/hair interfaces, continuous motion and full photographic acceptance are not certified.'}
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if not isinstance(v,list)}))
    return bool(introduced)


if __name__ == '__main__':
    sys.exit(main())
