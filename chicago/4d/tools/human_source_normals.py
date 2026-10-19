# SPDX-License-Identifier: GPL-3.0-or-later
"""Original area-weighted smooth normals across explicit source UV duplicates.

No position welding, topology/UV/weight changes or input mutation. Rest geometry
only; decimation/morph/export normal preservation requires canonical CI review.
"""
import math


def source_shared_normals(
    points, triangles, source_vertex_indices, coincidence_tolerance=1e-9
):
    if len(points) != len(source_vertex_indices) or not points:
        raise ValueError('source map must match nonempty geometry')
    if not math.isfinite(coincidence_tolerance) or coincidence_tolerance < 0:
        raise ValueError('invalid coincidence tolerance')
    groups = {}
    terms = {}
    for p, sid in zip(points, source_vertex_indices):
        if len(p) != 3 or not all((math.isfinite(v) for v in p)):
            raise ValueError('invalid position')
        if not isinstance(sid, int) or isinstance(sid, bool) or sid < 0:
            raise ValueError('invalid source vertex id')
        if sid in groups and math.dist(groups[sid], p) > coincidence_tolerance:
            raise ValueError('source UV duplicates have noncoincident rest positions')
        groups.setdefault(sid, p)
        terms.setdefault(sid, [[], [], []])
    for face in triangles:
        if len(face) != 3 or any(
            not isinstance(i, int) or isinstance(i, bool) or not 0 <= i < len(points)
            for i in face
        ):
            raise ValueError('invalid triangle')
        a, b, c = [points[i] for i in face]
        u = [b[k] - a[k] for k in range(3)]
        v = [c[k] - a[k] for k in range(3)]
        cross = [
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
        ]
        if math.hypot(*cross) <= 1e-20:
            raise ValueError('degenerate triangle has no oriented normal')
        for i in face:
            for k in range(3):
                terms[source_vertex_indices[i]][k].append(cross[k])
    normals = {}
    for sid, axes in terms.items():
        n = [math.fsum(axis) for axis in axes]
        length = math.hypot(*n)
        if length <= 1e-20:
            raise ValueError('source group has no nonzero oriented normal')
        normals[sid] = [x / length for x in n]
    return [list(normals[sid]) for sid in source_vertex_indices]
