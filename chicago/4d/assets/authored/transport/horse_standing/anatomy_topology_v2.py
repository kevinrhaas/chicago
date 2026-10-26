"""Local, seam-consistent hoof refinement of the licensed canonical body.

Named ground-support anchors and the canonical vertical datum are retained.
Hoof-wall/coronet/toe edges receive one adaptive subdivision step, with a
disclosed bounded Loop-style fairing in the horizontal plane. The old sampled
contact patch remains an explicit lineage set, but its outline may change and
requires a fresh standing/contact proof against the new rest surface.
This changes topology and adds interpolated skin/UV rows: it is deliberately not
described as an index- or whole-lower-leg-preserving operation.
"""

from collections import defaultdict
import math


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(a, value):
    return tuple(x * value for x in a)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a):
    length = math.sqrt(sum(x * x for x in a))
    if length < 1e-20:
        raise ValueError("Degenerate refined normal")
    return scale(a, 1 / length)


def smoothstep(value):
    value = min(1.0, max(0.0, value))
    return value ** 3 * (10 - 15 * value + 6 * value ** 2)


def refine(positions, normals, uv, joints, weights, triangles, sidecar, settings):
    original_count = len(positions)
    original_positions = list(positions)
    # UV splits share geometry, not attributes. Keep separate UV/skin rows while
    # calculating curvature from a geometric weld graph so no seam is opened.
    weld = {}
    weld_of, weld_members, representatives = [], defaultdict(list), []
    for i, position in enumerate(positions):
        key = tuple(round(x, 7) for x in position)
        if key not in weld:
            weld[key] = len(representatives)
            representatives.append(position)
        wi = weld[key]
        weld_of.append(wi)
        weld_members[wi].append(i)
    contacts = sidecar["contacts"]
    protected_faces = set(face for contact in contacts.values() for face in contact["source_triangle_ids"])
    witness_vertices = set(vertex for face in protected_faces for vertex in triangles[face])
    protected_vertices = {contact["minimum_vertex_id"] for contact in contacts.values()}
    protected_vertices.update(i for i, p in enumerate(positions) if p[1] <= settings["ground_anchor_band_m"])
    protected_welds = {weld_of[i] for i in protected_vertices}
    centres = {name: tuple(sum(positions[i][axis] for i in
                             {v for face in contact["source_triangle_ids"] for v in triangles[face]}) /
                          len({v for face in contact["source_triangle_ids"] for v in triangles[face]})
                          for axis in range(3)) for name, contact in contacts.items()}

    def region(point):
        if point[1] > settings["region_top_m"]:
            return None
        distances = [(math.hypot(point[0] - centre[0], point[2] - centre[2]), name)
                     for name, centre in centres.items()]
        distance, name = min(distances)
        return name if distance <= settings["region_radius_m"] else None

    neighbours, opposites = defaultdict(set), defaultdict(list)
    for fi, tri in enumerate(triangles):
        for a, b, opposite in [(tri[0], tri[1], tri[2]), (tri[1], tri[2], tri[0]), (tri[2], tri[0], tri[1])]:
            a, b, opposite = weld_of[a], weld_of[b], weld_of[opposite]
            if a == b:
                continue
            key = tuple(sorted((a, b)))
            neighbours[a].add(b)
            neighbours[b].add(a)
            opposites[key].append(opposite)
    eligible = set()
    for edge, across in opposites.items():
        a, b = edge
        ra, rb = region(representatives[a]), region(representatives[b])
        if ra is not None and ra == rb and len(set(across)) == 2:
            eligible.add(edge)

    def taper(point):
        # Retain limb heights and named anchors. Fresh qualification, rather
        # than an unchanged old toe polygon, decides the new contact outline.
        return 1 - smoothstep((point[1] - settings["full_fairing_below_m"]) /
                              (settings["region_top_m"] - settings["full_fairing_below_m"]))

    fair = {}
    maximum_old_shift = 0.0
    maximum_raw_old_shift = 0.0
    for wi, point in enumerate(representatives):
        if wi in protected_welds or region(point) is None:
            fair[wi] = point
            continue
        adjacent = neighbours[wi]
        if len(adjacent) < 3:
            fair[wi] = point
            continue
        beta = 3 / (8 * len(adjacent)) if len(adjacent) > 3 else 3 / 16
        target = add(scale(point, 1 - len(adjacent) * beta),
                     scale(tuple(sum(representatives[j][axis] for j in adjacent) for axis in range(3)), beta))
        amount = settings["original_vertex_fairing"] * taper(point)
        displacement = ((target[0] - point[0]) * amount, 0.0, (target[2] - point[2]) * amount)
        distance = math.sqrt(sum(x * x for x in displacement))
        maximum_raw_old_shift = max(maximum_raw_old_shift, distance)
        # The source has irregular long incident edges at the coronary/pastern
        # transition. Bound their fairing geometrically instead of increasing
        # the declared displacement to accept an oversized smoothing step.
        bound = settings["maximum_old_vertex_shift_m"]
        displacement = scale(displacement, bound / math.hypot(bound, distance))
        distance = math.sqrt(sum(x * x for x in displacement))
        if distance > settings["maximum_old_vertex_shift_m"]:
            raise ValueError("Hoof fairing exceeds declared original-vertex displacement")
        fair[wi] = add(point, displacement)
        maximum_old_shift = max(maximum_old_shift, distance)
    positions = [add(p, tuple(fair[weld_of[i]][axis] - representatives[weld_of[i]][axis] for axis in range(3)))
                 for i, p in enumerate(positions)]
    normals, uv, joints, weights = list(normals), list(uv), list(joints), list(weights)
    mid_geometry = {}
    maximum_raw_edge_curvature = 0.0
    for a, b in eligible:
        # All Loop masks belong to the SAME original cage. Using already
        # faired endpoints/opposites applies a second smoothing step only to
        # edge vertices and introduces irregular toe corners.
        linear = scale(add(representatives[a], representatives[b]), .5)
        across = sorted(set(opposites[(a, b)]))
        curved = add(scale(add(representatives[a], representatives[b]), 3 / 8),
                     scale(add(representatives[across[0]], representatives[across[1]]), 1 / 8))
        amount = settings["edge_fairing"] * taper(linear)
        delta = ((curved[0] - linear[0]) * amount, 0.0, (curved[2] - linear[2]) * amount)
        raw_distance = math.sqrt(sum(x * x for x in delta))
        maximum_raw_edge_curvature = max(maximum_raw_edge_curvature, raw_distance)
        bound = settings["maximum_edge_curvature_m"]
        point = add(linear, scale(delta, bound / math.hypot(bound, raw_distance)))
        if math.dist(point, linear) > settings["maximum_edge_curvature_m"]:
            raise ValueError("Hoof edge curvature exceeds its declared bound")
        mid_geometry[(a, b)] = point

    midpoints, added = {}, []

    def midpoint(a, b):
        key = tuple(sorted((a, b)))
        if key in midpoints:
            return midpoints[key]
        geometric = tuple(sorted((weld_of[a], weld_of[b])))
        if geometric not in eligible:
            return None
        i = len(positions)
        positions.append(mid_geometry[geometric])
        normals.append(unit(add(normals[a], normals[b])))
        uv.append(scale(add(uv[a], uv[b]), .5))
        combined = defaultdict(float)
        for vertex in (a, b):
            for joint, weight in zip(joints[vertex], weights[vertex]):
                combined[joint] += .5 * weight
        active = sorted(((joint, weight) for joint, weight in combined.items() if weight > 0),
                        key=lambda item: (-item[1], item[0]))
        if len(active) > 4:
            raise ValueError("Refined hoof row needs more than four influences; no weight truncation is allowed")
        total = sum(weight for _, weight in active)
        js = [joint for joint, _ in active] + [0] * (4 - len(active))
        ws = [weight / total for _, weight in active] + [0.0] * (4 - len(active))
        joints.append(tuple(js))
        weights.append(tuple(ws))
        midpoints[key] = i
        added.append({"vertex": i, "source_edge": [a, b], "geometric_edge": list(geometric),
                      "source_interpolation": [.5, .5]})
        return i

    refined, face_map = [], []
    for fi, (a, b, c) in enumerate(triangles):
        ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
        mask = int(ab is not None) + 2 * int(bc is not None) + 4 * int(ca is not None)
        patterns = {0: [(a, b, c)], 1: [(a, ab, c), (ab, b, c)],
                    2: [(b, bc, a), (bc, c, a)], 4: [(c, ca, b), (ca, a, b)],
                    3: [(b, bc, ab), (a, ab, c), (ab, bc, c)],
                    5: [(a, ab, ca), (ab, b, c), (ab, c, ca)],
                    6: [(c, ca, bc), (a, b, ca), (b, bc, ca)],
                    7: [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]}
        children = patterns[mask]
        face_map.append(list(range(len(refined), len(refined) + len(children))))
        refined.extend(children)

    # Check actual serialized triangles separately; positive field Jacobians
    # alone do not prove orientation of a finite triangle after nonlinear edits.
    minimum_orientation = 1.0
    for fi, tri in enumerate(triangles):
        pa, pb, pc = [original_positions[i] for i in tri]
        old_normal = cross(tuple(pb[k] - pa[k] for k in range(3)), tuple(pc[k] - pa[k] for k in range(3)))
        old_length = math.sqrt(sum(x * x for x in old_normal))
        if old_length < 1e-14:
            continue
        for child in face_map[fi]:
            qa, qb, qc = [positions[i] for i in refined[child]]
            new_normal = cross(tuple(qb[k] - qa[k] for k in range(3)), tuple(qc[k] - qa[k] for k in range(3)))
            new_length = math.sqrt(sum(x * x for x in new_normal))
            if new_length < 1e-14:
                raise ValueError("Refinement creates a degenerate triangle")
            agreement = sum(x * y for x, y in zip(old_normal, new_normal)) / old_length / new_length
            if agreement <= 0:
                raise ValueError("Refinement reverses a real source triangle")
            minimum_orientation = min(minimum_orientation, agreement)

    affected = {i for i in range(original_count) if positions[i] != original_positions[i]}
    affected.update(range(original_count, len(positions)))
    moved_or_added = frozenset(affected)
    for fi, children in enumerate(face_map):
        if len(children) > 1 or any(i in moved_or_added for i in triangles[fi]):
            affected.update(i for child in children for i in refined[child])
    # Refined smooth normals use the geometric weld graph without welding UVs.
    normal_key = [tuple(round(x, 7) for x in p) for p in positions]
    sums = defaultdict(lambda: [0.0, 0.0, 0.0])
    for tri in refined:
        a, b, c = [positions[i] for i in tri]
        n = cross(tuple(b[k] - a[k] for k in range(3)), tuple(c[k] - a[k] for k in range(3)))
        for i in tri:
            for axis in range(3):
                sums[normal_key[i]][axis] += n[axis]
    for i in affected:
        normals[i] = unit(sums[normal_key[i]])
    for vertex in protected_vertices:
        if positions[vertex] != original_positions[vertex]:
            raise ValueError("Protected actual ground vertex moved")
    return {"positions": positions, "normals": normals, "uv": uv, "joints": joints, "weights": weights,
            "triangles": refined, "receipt": {"original_vertices": original_count,
                "new_vertices": len(positions), "original_triangles": len(triangles),
                "new_triangles": len(refined), "ground_support_anchor_vertex_ids": sorted(protected_vertices),
                "ground_witness_vertex_ids": sorted(witness_vertices),
                "moved_ground_witness_vertex_ids": sorted(i for i in witness_vertices
                                                         if positions[i] != original_positions[i]),
                "ground_witness_parent_face_ids": sorted(protected_faces),
                "source_face_to_children": face_map, "added_vertices": added,
                "maximum_original_vertex_shift_m": maximum_old_shift,
                "maximum_unbounded_loop_proposal_m": maximum_raw_old_shift,
                "maximum_unbounded_edge_proposal_m": maximum_raw_edge_curvature,
                "fairing_bound": "Smooth magnitude saturation d -> bound*d/hypot(bound, norm(d)); declared bounds unchanged",
                "loop_mask_cage": "Original rest cage for both old-vertex and edge masks; no double fairing",
                "normal_update": "All vertices of affected/refined faces, including fixed support anchors",
                "minimum_parent_child_face_normal_dot": minimum_orientation,
                "indices_unchanged": False, "skin_rows_added_by_declared_edge_interpolation": True,
                "original_skin_rows_unchanged": True, "ground_support_anchors_unchanged": True,
                "ground_witness_geometry_unchanged": False,
                "self_intersection_acceptance": False, "fresh_loaded_deformation_contact_acceptance": False}}
