"""One external canonical upper-lid strip prototype; never installs or publishes.

The named pleat faces are replaced in their existing continuous UV charts. All
boundary/exterior bytes, UVs, skin, feet, eyes and rig remain unchanged. Only
explicit interior position/normal rows and the removed face slots may change.
"""

import argparse
from collections import defaultdict
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def polygon_area(rows, uv):
    return sum(uv[a][0] * uv[b][1] - uv[a][1] * uv[b][0]
               for a, b in zip(rows, rows[1:] + rows[:1])) / 2


def inside_triangle(point, a, b, c):
    return min(orient(a, b, point), orient(b, c, point), orient(c, a, point)) >= -1e-14


def triangulate(boundary, interior, uv, forbidden_edges=frozenset()):
    """Constrained ear triangulation, original interior sites, then lawful flips."""
    require(polygon_area(boundary, uv) > 0, "Source UV boundary must retain its positive orientation")
    polygon = list(boundary)
    result = []
    while len(polygon) > 3:
        ears = []
        for i, b in enumerate(polygon):
            a, c = polygon[i - 1], polygon[(i + 1) % len(polygon)]
            area = orient(uv[a], uv[b], uv[c])
            if area <= 1e-14:
                continue
            if any(inside_triangle(uv[j], uv[a], uv[b], uv[c])
                   for j in polygon if j not in (a, b, c)):
                continue
            ears.append((area, -b, i, (a, b, c)))
        require(ears, "The exact boundary cannot be triangulated without a missing edge")
        _, _, index, triangle = max(ears)
        result.append(triangle)
        polygon.pop(index)
    require(orient(*(uv[i] for i in polygon)) > 1e-14, "Degenerate final source-UV ear")
    result.append(tuple(polygon))
    boundary_edges = {tuple(sorted((a, b))) for a, b in zip(boundary, boundary[1:] + boundary[:1])}
    for point in sorted(interior):
        containing = [index for index, triangle in enumerate(result)
                      if inside_triangle(uv[point], *(uv[i] for i in triangle))]
        require(containing, "An original interior UV site lies outside the exact patch boundary")
        triangle = result[containing[0]]
        on_edges = [(a, b) for a, b in zip(triangle, triangle[1:] + triangle[:1])
                    if abs(orient(uv[a], uv[b], uv[point])) <= 1e-14]
        if on_edges:
            edge = tuple(sorted(on_edges[0]))
            require(edge not in boundary_edges, "An interior site would alter the preserved boundary")
            updated = []
            for old in result:
                if set(edge) <= set(old):
                    for i in range(3):
                        a, b, c = old[i], old[(i + 1) % 3], old[(i + 2) % 3]
                        if tuple(sorted((a, b))) == edge:
                            updated.extend([(a, point, c), (point, b, c)])
                            break
                else:
                    updated.append(old)
            result = updated
        else:
            a, b, c = result.pop(containing[0])
            result.extend([(a, b, point), (b, c, point), (c, a, point)])

    # Improve the UV-domain element quality without moving a single UV or boundary.
    flips = 0
    for _ in range(5000):
        edges = defaultdict(list)
        for index, triangle in enumerate(result):
            for a, b in zip(triangle, triangle[1:] + triangle[:1]):
                edges[tuple(sorted((a, b)))].append(index)
        changed = False
        for (a, b), owners in sorted(edges.items(), key=lambda item:(item[0] not in forbidden_edges,item[0])):
            if len(owners) != 2 or (a, b) in boundary_edges:
                continue
            c = next(i for i in result[owners[0]] if i not in (a, b))
            d = next(i for i in result[owners[1]] if i not in (a, b))
            if c == d or tuple(sorted((c, d))) in edges or tuple(sorted((c, d))) in forbidden_edges:
                continue
            if orient(uv[c], uv[d], uv[a]) * orient(uv[c], uv[d], uv[b]) >= -1e-28:
                continue
            aa, bb, cc = [np.asarray(uv[i]) - uv[d] for i in (a, b, c)]
            determinant = float(np.linalg.det(np.array([[x[0], x[1], np.dot(x, x)] for x in (aa, bb, cc)])))
            if orient(uv[a], uv[b], uv[c]) < 0:
                determinant = -determinant
            if determinant <= 1e-18 and (a,b) not in forbidden_edges:
                continue
            replacement = [(c, d, a), (d, c, b)]
            replacement = [t if orient(*(uv[i] for i in t)) > 0 else (t[0], t[2], t[1]) for t in replacement]
            if min(orient(*(uv[i] for i in t)) for t in replacement) <= 1e-14:
                continue
            for index, triangle in zip(owners, replacement):
                result[index] = triangle
            flips += 1
            changed = True
            break
        if not changed:
            break
    else:
        raise ValueError("UV edge optimization did not converge within its computation bound")
    require(len(result) == len(boundary) - 2 + 2 * len(interior), "Disk triangulation has incomplete coverage")
    require(min(orient(*(uv[i] for i in t)) for t in result) > 1e-14, "A replacement UV face reversed or collapsed")
    area = sum(orient(*(uv[i] for i in t)) for t in result) / 2
    require(abs(area - polygon_area(boundary, uv)) < 1e-12, "Replacement UV chart does not cover its original boundary")
    forbidden_remaining = sorted({tuple(sorted((a,b))) for t in result for a,b in zip(t,t[1:]+t[:1])
                                  if tuple(sorted((a,b))) in forbidden_edges})
    require(not forbidden_remaining,
            "A replacement diagonal duplicates a protected exterior edge: " + json.dumps([
                {'edge':edge,'UV':[uv[i] for i in edge],
                 'adjacent_strip_triangles':[t for t in result if set(edge)<=set(t)]}
                for edge in forbidden_remaining]))
    return result, flips


def project_ball(point, centre, radius):
    delta = point - centre
    distance = float(np.linalg.norm(delta))
    return point if distance <= radius else centre + delta * (radius / distance)


def project_two_balls(point, a, b, radius):
    if max(np.linalg.norm(point - a), np.linalg.norm(point - b)) <= radius:
        return point
    current = point.copy()
    pa, pb = np.zeros(3), np.zeros(3)
    for _ in range(100):
        first = project_ball(current + pa, a, radius)
        pa = current + pa - first
        second = project_ball(first + pb, b, radius)
        pb = first + pb - second
        if np.linalg.norm(second - current) < 1e-12 and max(np.linalg.norm(second - a), np.linalg.norm(second - b)) <= radius + 1e-12:
            return second
        current = second
    raise ValueError("Bounded source-position projection did not converge")


def fair_strip(triangles, boundary, interior, uv, parent, original, bound):
    # Positive symmetric cotangent weights on the constrained Delaunay UV chart.
    edge_weights = defaultdict(float)
    for a, b, c in triangles:
        for centre, j, k in [(a, b, c), (b, c, a), (c, a, b)]:
            p, q = np.asarray(uv[j]) - uv[centre], np.asarray(uv[k]) - uv[centre]
            area = abs(float(p[0] * q[1] - p[1] * q[0]))
            require(area > 1e-14, "UV cotangent is degenerate")
            edge_weights[tuple(sorted((j, k)))] += float(np.dot(p, q)) / (2 * area)
    neighbors = defaultdict(list)
    owned = set(interior)
    for (a, b), weight in edge_weights.items():
        if a in owned or b in owned:
            require(weight >= -1e-8, "The replacement has a non-Delaunay interior UV edge")
            weight = max(weight, 0.0)
            if weight:
                neighbors[a].append((b, weight))
                neighbors[b].append((a, weight))
    positions = np.asarray(parent, dtype=float).copy()
    radius = bound - 2e-7  # Tighten, rather than weaken, the final float32 cap.
    for iteration in range(1000):
        maximum_step = 0.0
        for i in sorted(interior):
            total = sum(weight for _, weight in neighbors[i])
            require(total > 0, "An interior strip site has no positive connection to its boundary")
            target = sum((positions[j] * weight for j, weight in neighbors[i]), np.zeros(3)) / total
            target = project_two_balls(target, np.asarray(parent[i]), np.asarray(original[i]), radius)
            maximum_step = max(maximum_step, float(np.linalg.norm(target - positions[i])))
            positions[i] = target
        if maximum_step < 1e-10:
            return positions, iteration + 1
    raise ValueError("The bounded strip solve did not converge")


def patch_rows(binary, document, accessor_index, updates, format_string):
    accessor = document['accessors'][accessor_index]
    view = document['bufferViews'][accessor['bufferView']]
    size = struct.calcsize(format_string)
    stride = view.get('byteStride', size)
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    ranges = []
    for row, values in updates.items():
        start = offset + row * stride
        binary[start:start + size] = struct.pack(format_string, *values)
        ranges.append((start, start + size))
    return ranges


def preserved_bytes(before, after, ranges):
    require(len(before) == len(after), "The prototype changed unrelated buffer allocation")
    cursor = 0
    for start, stop in sorted(ranges):
        if start > cursor:
            require(before[cursor:start] == after[cursor:start], "Bytes outside the declared patch changed")
        cursor = max(cursor, stop)
    require(before[cursor:] == after[cursor:], "Protected bytes after the patch changed")


EXPECTED_SHA='5a2b2e87c3931e3ab82be3ce3bc69724a0a088aac30920cea9ad348bbaf8fad5'
APP=Path(__file__).resolve().parents[4]

def derive(parent_raw,original_raw,recipe_bytes,source_directory,reference_directory=None):
    """Pure repeatable geometry; reference pixels never enter this algorithm.

    Authoring CLI requires and verifies exact reference images. CI checks exact
    frozen recipe/source-rights bindings and reproduces the same geometry core.
    Creation-time unqualified flags remain historical GLB bytes; later proof is
    recorded separately, never forged by generation.
    """
    import generate_anatomy_v2 as anatomy
    recipe=json.loads(recipe_bytes)
    receipt={'generator_sha256':sha(Path(__file__).read_bytes()),'parent_sha256':sha(parent_raw),'recipe_sha256':sha(recipe_bytes),'app_edits':False,'photographic_acceptance':False,'proper_crossing_acceptance':False,'fresh_loaded129_acceptance':False}
    require(sha(parent_raw) == recipe['parent_sha256'], "Immutable925 parent changed")
    require(sha(original_raw) == recipe['preserved_original_container_sha256'], "Immutable original container changed")
    require(recipe['parent_sha256'] == '925fac957110b9b57b95c5abfed17fabf29f868b173f38f0569d984dd9999a48'
            and recipe['preserved_original_container_sha256'] == 'd4544c2845256858dfa614235bcb37cb964ab63095a53a2436225182cefbb914',
            "Only the named immutable anatomical sources are supported")
    require(recipe['maximum_original_source_displacement_m'] == recipe['maximum_parent_displacement_m'] == .02
            and recipe['maximum_source_bytes'] == 4 * 1024 * 1024 and recipe['maximum_triangles'] == 20000,
            "The established displacement/byte/triangle caps cannot be changed")
    require(len(recipe['patches']) == 2 and {p['side'] for p in recipe['patches']} == {-1, 1},
            "This prototype is restricted to the two named upper-lid patches")
    for reference in recipe['reference_bindings']:
        if reference_directory is not None:
            require(sha((reference_directory / reference['file']).read_bytes()) == reference['sha256'], "Cleared reference bytes changed")
        source = json.loads((source_directory / (reference['source_id'] + '.json')).read_text())
        require(source['id'] == reference['source_id'] and source['rights_status'] in ['public_domain', 'cleared'], "Retopology source identity/rights do not permit derivation")
    document, original_binary = anatomy.base.read_glb(parent_raw)
    original_document, d454_binary = anatomy.base.read_glb(original_raw)
    document = copy.deepcopy(document)
    primitive = document['meshes'][1]['primitives'][0]
    attributes = primitive['attributes']
    positions = anatomy.read_attribute(document, original_binary, attributes['POSITION'])
    normals = anatomy.read_attribute(document, original_binary, attributes['NORMAL'])
    uv = anatomy.read_attribute(document, original_binary, attributes['TEXCOORD_0'])
    uv_repairs = recipe.get('internal_BODY_UV_repairs', [])
    if uv_repairs:
        require(sha(recipe_bytes) == 'f77e115a340a6cbb8d6efb1b7887c8cdba001a47f493b97be6ffb0eee72dd133',
                "Only the frozen two-return-face/two-row chart amendment is supported")
        require(attributes['TEXCOORD_0'] == attributes['TEXCOORD_1'], "Both BODY UV aliases must remain identical")
        require({repair['row'] for repair in uv_repairs} == {2410, 2412} and len(uv_repairs) == 2,
                "The internal UV repair requires the strict two-row allowlist")
        require(recipe['maximum_internal_BODY_UV_displacement'] == .00030,
                "The tightly bounded source-chart repair cap changed")
        allowed_interpolation = {2410: [2372, 2373, 2411], 2412: [2374, 2375, 2413]}
        for repair in uv_repairs:
            row = repair['row']
            parents = allowed_interpolation[row]
            require(repair['preserved_boundary_interpolation_rows'] == parents and repair['weights'] == [1/3]*3,
                    "The declared preserved-triangle barycentre changed")
            expected = anatomy.f32([tuple(sum(uv[i][k] for i in parents)/3 for k in range(2))])[0]
            require(list(uv[row]) == repair['old_UV'] and list(expected) == repair['new_UV'],
                    "Declared old/new UVs differ from the exact source interpolation")
            require(math.dist(uv[row], expected) <= .00030, "The internal UV repair exceeds its cap")
            uv[row] = expected
    original_positions = anatomy.read_attribute(original_document, d454_binary, 203)
    indices = [row[0] for row in anatomy.read_attribute(document, original_binary, primitive['indices'])]
    triangles = [tuple(indices[i:i + 3]) for i in range(0, len(indices), 3)]
    new_triangles, new_positions, new_normals = list(triangles), list(positions), list(normals)
    all_owned, all_removed, patch_reports = set(), set(), []
    key = lambda i: tuple(round(x, 7) for x in positions[i])
    for patch in recipe['patches']:
        removed = set(patch['removed_parent_925_faces'])
        boundary = patch['boundary_parent_rows']
        boundary_keys = {key(i) for i in boundary}
        used = {i for face in removed for i in triangles[face]}
        interior = sorted(i for i in used if key(i) not in boundary_keys)
        require(10 <= len(boundary) <= 64 and 0 < len(removed) <= 100 and 0 < len(interior) <= 64,
                "The source cut exceeds its local authoring scope")
        require(all(patch['side'] * positions[i][0] > 0 and .05 < abs(positions[i][0]) < .16
                    and 1.47 < positions[i][1] < 1.60 and 1.27 < positions[i][2] < 1.42 for i in used),
                "A selected row lies outside the bounded orbital region")
        require(not (removed & set(recipe['protected_lower_parent_faces'])), "The cut includes a protected lower socket face")
        require(not (all_owned & set(interior)) and not (all_removed & removed), "The two source patches overlap")
        outside_used = {i for face, tri in enumerate(triangles) if face not in removed for i in tri}
        require(not (set(interior) & outside_used), "An owned interior row is used outside its patch")
        require(set(interior) <= set(range(len(original_positions))), "Retopology touched a source foot-added row")
        for repair in uv_repairs:
            if repair['row'] in used:
                require(repair['row'] in interior and set(repair['preserved_boundary_interpolation_rows']) <= set(boundary),
                        "The tiny UV repair is not an interior row interpolated from its fixed boundary")
        fixed_boundary_edges = {tuple(sorted((a,b))) for a,b in zip(boundary,boundary[1:]+boundary[:1])}
        exterior_edges = {tuple(sorted((a,b))) for face,t in enumerate(triangles) if face not in removed
                          for a,b in zip(t,t[1:]+t[:1])}
        forbidden_edges = exterior_edges - fixed_boundary_edges
        replacement, flips = triangulate(boundary, interior, uv, forbidden_edges)
        require(len(replacement) == len(removed), "This prototype cannot alter outside face slots or body counts")
        solved, iterations = fair_strip(replacement, boundary, interior, uv, positions, original_positions,
                                        min(recipe['maximum_original_source_displacement_m'], recipe['maximum_parent_displacement_m']))
        for i in interior:
            new_positions[i] = anatomy.f32([tuple(solved[i])])[0]
        for face, triangle in zip(sorted(removed), sorted(replacement)):
            new_triangles[face] = triangle
        sums = defaultdict(lambda: np.zeros(3))
        for triangle in replacement:
            vector = np.cross(np.asarray(new_positions[triangle[1]]) - new_positions[triangle[0]],
                              np.asarray(new_positions[triangle[2]]) - new_positions[triangle[0]])
            require(float(np.linalg.norm(vector)) > 1e-14, "A reconstructed skin-strip face collapsed")
            for i in triangle:
                sums[i] += vector
        for i in interior:
            length = float(np.linalg.norm(sums[i]))
            require(length > 1e-20, "A reconstructed strip normal is degenerate")
            new_normals[i] = anatomy.f32([tuple(sums[i] / length)])[0]
        all_owned.update(interior)
        all_removed.update(removed)
        patch_reports.append({'id': patch['id'], 'explicitly_removed_parent_faces': sorted(removed),
                              'replacement_face_slots': sorted(removed),
                              'face_slot_reuse_is_storage_not_old_refinement_ancestry': True,
                              'preserved_boundary_rows': boundary, 'owned_interior_rows': interior,
                              'source_UV_edge_flips': flips, 'bounded_skin_solver_iterations': iterations})
    original_displacement = max(math.dist(a, b) for a, b in zip(original_positions, new_positions))
    parent_displacement = max(math.dist(a, b) for a, b in zip(positions, new_positions))
    require(original_displacement <= recipe['maximum_original_source_displacement_m'], "The actual float32 original-source20mm cap was exceeded")
    require(parent_displacement <= recipe['maximum_parent_displacement_m'], "The actual float32925-parent20mm cap was exceeded")
    binary = bytearray(original_binary)
    ranges = patch_rows(binary, document, attributes['POSITION'], {i: new_positions[i] for i in all_owned}, '<fff')
    ranges += patch_rows(binary, document, attributes['NORMAL'], {i: new_normals[i] for i in all_owned}, '<fff')
    ranges += patch_rows(binary, document, primitive['indices'],
                         {3 * face + corner: (new_triangles[face][corner],) for face in all_removed for corner in range(3)}, '<H')
    ranges += patch_rows(binary, document, attributes['TEXCOORD_0'],
                         {repair['row']: uv[repair['row']] for repair in uv_repairs}, '<ff')
    preserved_bytes(original_binary, binary, ranges)
    require(bytes(binary[:len(d454_binary)]) == d454_binary, "Original d454 BIN prefix changed")
    for semantic, rows in [('POSITION', new_positions), ('NORMAL', new_normals)]:
        accessor = document['accessors'][attributes[semantic]]
        accessor['min'] = [min(row[k] for row in rows) for k in range(3)]
        accessor['max'] = [max(row[k] for row in rows) for k in range(3)]
    notice = {'parent_sha256': sha(parent_raw), 'original_d454_sha256': sha(original_raw),
              'recipe_sha256': sha(recipe_bytes), 'confidence': 'reconstructed',
              'changes': 'Named upper pleats replaced by a coherent fixed-boundary skin strip; old face refinement ancestry is superseded explicitly',
              'ancestor_anatomy_v2_notice_scope': 'Historical925 ancestor; upper-lid topology is superseded here',
              'photographic_acceptance': False, 'proper_crossing_acceptance': False,
              'fresh_loaded129_acceptance': False}
    if uv_repairs:
        notice['internal_BODY_UV_repair_rows'] = [2410, 2412]
        notice['UV_protection'] = 'All boundary/exterior BODY and every EYE UV exact; two declared internal BODY rows use preserved-boundary barycentres'
    document['asset'].setdefault('extras', {})['chicago4d_upper_lid_strip_v1'] = notice
    encoded = json.dumps(document, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    output = struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(binary))
    output += struct.pack('<II', len(encoded), 0x4E4F534A) + encoded
    output += struct.pack('<II', len(binary), 0x004E4942) + binary
    require(len(output) <= recipe['maximum_source_bytes'], "The unchanged4MiB cap was exceeded")
    whole_triangles = sum(document['accessors'][p['indices']]['count'] // 3 for mesh in document['meshes'] for p in mesh['primitives'])
    require(whole_triangles <= recipe['maximum_triangles'], "The unchanged20ktriangle cap was exceeded")
    receipt.update(state='EXACT_SOURCE_DERIVATION_ONLY_NO_ACCEPTANCE', candidate_sha256=sha(output),
                   candidate_bytes=len(output), whole_triangles=whole_triangles,
                   body_vertices=len(positions), body_triangles=len(new_triangles),
                   patches=patch_reports, original_source_maximum_displacement_m=original_displacement,
                   parent925_maximum_displacement_m=parent_displacement,
                   modified_position_normal_rows=sorted(all_owned), removed_parent_faces=sorted(all_removed),
                   boundary_exterior_BODY_UV_and_all_EYE_UV_skin_rig_globe_foot_bytes_exact=True,
                   internal_BODY_UV_repairs=uv_repairs,
                   original_d454_BIN_prefix_exact=True,
                   pending=['independent topology/source review and real corruption controls', 'whole-body proper crossings',
                            'fresh loaded129 with honest replacement-patch ownership', 'actual matched native images',
                            'published yard/phone and complete source gate'])
    require(sha(output)==EXPECTED_SHA,'Regeneration differs from the exactly qualified5a source; fresh binding/qualification required')
    return output,receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();require(not args.output_dir.exists(),'Fresh output directory required')
    source=Path(__file__).resolve().parent
    parent_path=source/'horse-sevket-anatomy-v2.glb';original_path=source/'horse-sevket-v16-planted-standing-eye-uv-v1.glb'
    parent,original=parent_path.read_bytes(),original_path.read_bytes();recipe=(source/'upper-lid-strip-v1-recipe.json').read_bytes()
    raw,receipt=derive(parent,original,recipe,APP/'data/sources',args.reference_dir)
    require(parent_path.read_bytes()==parent and original_path.read_bytes()==original,'Immutable source changed during derivation')
    args.output_dir.mkdir(parents=True)
    (args.output_dir/'horse-sevket-upper-lid-strip-v1.glb').write_bytes(raw)
    (args.output_dir/'DERIVATION-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'state':receipt['state'],'candidate_sha256':sha(raw),'out':str(args.output_dir)}))

if __name__=='__main__':main()
