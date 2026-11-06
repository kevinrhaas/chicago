#!/usr/bin/env python3
"""Export one structure's GLB as a watertight, standalone, 3D-printable 3MF.

    python3 tools/export_print_3mf.py --structure glessner_house --out glessner.3mf
    python3 tools/export_print_3mf.py --glb assets/gltf/<file>.glb --scale 300 --out x.3mf

A render GLB is a triangle soup built for the screen: single-sided planes, glass
panes, overlapping trim, grass blades, vines, a lawn. None of that is a solid, so
this tool does not try to boolean the parts together. It rebuilds the building as a
solid at print resolution instead, which makes the output watertight by
construction, whatever the input looked like:

  1. read the GLB (node transforms applied) and keep only the structure's own
     materials: ground, planting and vegetation materials are dropped by name
     (`DEFAULT_EXCLUDE`, extend with --exclude, rescue with --include);
  2. rasterise every kept triangle into a voxel grid at --voxel-mm on the print;
     the modelled roof tiles, far below what a nozzle can draw, are swapped for one
     uniform course pattern laid on the roof deck (--roof-tiles uniform);
  3. flood-fill the air from outside: whatever the air cannot reach is solid, so
     a closed shell (walls + roofs + glass) prints as a solid house with recessed
     windows rather than a hollow box;
  4. drop low ground clutter (walks, curbs, kerbs, stray paving) that lies
     beyond a margin around the building's walls;
  5. thicken only the parts thinner than --min-feature-mm (cresting, finials,
     railings, downpipes) so a 0.4 mm FDM nozzle can lay them, leaving thick
     walls at their true size;
  6. stand the house on a flat base slab under its footprint (--base-mm, with
     enclosed courts floored), and keep only the one piece that touches it, so
     nothing floats;
  7. mesh the solid (marching cubes), simplify it while keeping it manifold
     (manifold3d) and leaving no flat triangle or doubled vertex for a slicer to
     "repair", verify it independently, and write a millimetre 3MF. A file that
     fails verification is not written.

Print defaults (FDM, 0.4 mm nozzle): scale 1:250, voxel 0.2 mm, minimum feature
1.0 mm, base 1.6 mm. Glessner at 1:250 is about 208 x 98 x 62 mm on the bed.

This is an on-demand export, not part of the scene build: nothing it writes is
committed. It needs numpy, scipy, scikit-image and manifold3d
(`pip install numpy scipy scikit-image manifold3d`); the first two are the gate's
own dependencies, the last two are imported only when a mesh is made.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import math
import struct
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]

# Materials that are never the building: ground, planting and vegetation. Names are
# glob patterns matched against glTF material names (case-insensitive). A
# structure whose own walls carry one of these words is rescued with --include.
DEFAULT_EXCLUDE = (
    "lawn*", "turf*", "grass*", "drive*", "ground*", "terrain*", "soil*", "dirt*",
    "gravel*", "paving*", "sidewalk*", "walk_*", "road*", "street*", "water*",
    "*vine*", "*ivy*", "*leaf*", "*leaves*", "*foliage*", "*tree*", "*bark*",
    "*shrub*", "*hedge*", "*flower*", "*human*", "*skin*", "*hair*", "*cloth*",
    "*shadow*", "*decal*",
)

WRITE_DECIMALS = 5   # millimetres in the 3MF: 10 nm, far under any printer's step

FDM_NOTES = {
    "nozzle_mm": 0.4,
    "layer_mm": "0.12-0.2",
    "why_min_feature": "two 0.4 mm perimeters plus margin; freestanding pins thinner "
                       "than about 1 mm snap or curl on FDM",
}


# --------------------------------------------------------------------------- GLB

_COMPONENT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16,
              5125: np.uint32, 5126: np.float32}
_NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_glb(path: Path):
    data = path.read_bytes()
    magic, _version, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        raise SystemExit(f"{path}: not a GLB")
    off, gltf, binary = 12, None, b""
    while off < length:
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            gltf = json.loads(chunk)
        elif ctype == 0x004E4942:
            binary = chunk
        off += 8 + clen
    return gltf, binary


def _accessor(gltf, binary, index):
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    dtype = np.dtype(_COMPONENT[acc["componentType"]])
    ncomp = _NCOMP[acc["type"]]
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride") or dtype.itemsize * ncomp
    count = acc["count"]
    raw = np.frombuffer(binary, dtype=np.uint8, count=stride * (count - 1) + dtype.itemsize * ncomp,
                        offset=start)
    out = np.lib.stride_tricks.as_strided(raw, shape=(count, ncomp * dtype.itemsize),
                                          strides=(stride, 1)).copy()
    out = out.view(dtype).reshape(count, ncomp).astype(np.float64)
    if acc.get("normalized"):
        out /= {np.int8: 127.0, np.uint8: 255.0, np.int16: 32767.0, np.uint16: 65535.0}.get(dtype.type, 1.0)
    return out


def _node_matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=np.float64).reshape(4, 4).T
    t = node.get("translation", [0, 0, 0])
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    s = node.get("scale", [1, 1, 1])
    r = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])
    m = np.eye(4)
    m[:3, :3] = r * np.array(s)[None, :]
    m[:3, 3] = t
    return m


def load_triangles(path: Path):
    """[(material_name, triangles (n, 3, 3) in glTF metres, Y up)], node transforms applied."""
    gltf, binary = read_glb(path)
    materials = [m.get("name", f"material_{i}") for i, m in enumerate(gltf.get("materials", []))]
    out = []

    def walk(index, parent):
        node = gltf["nodes"][index]
        world = parent @ _node_matrix(node)
        if "mesh" in node:
            for prim in gltf["meshes"][node["mesh"]]["primitives"]:
                if prim.get("mode", 4) != 4:
                    continue
                pos = _accessor(gltf, binary, prim["attributes"]["POSITION"])
                pos = pos @ world[:3, :3].T + world[:3, 3]
                if "indices" in prim:
                    idx = _accessor(gltf, binary, prim["indices"]).astype(np.int64).reshape(-1, 3)
                else:
                    idx = np.arange(len(pos)).reshape(-1, 3)
                name = materials[prim["material"]] if "material" in prim else "default"
                out.append((name, pos[idx]))
        for child in node.get("children", []):
            walk(child, world)

    scene = gltf["scenes"][gltf.get("scene", 0)]
    for root in scene["nodes"]:
        walk(root, np.eye(4))
    return out


def select(parts, exclude, include):
    kept, dropped = [], {}
    for name, tris in parts:
        low = name.lower()
        rescued = any(fnmatch.fnmatch(low, p.lower()) for p in include)
        if not rescued and any(fnmatch.fnmatch(low, p.lower()) for p in exclude):
            dropped[name] = dropped.get(name, 0) + len(tris)
            continue
        kept.append((name, tris))
    return kept, dropped


# ----------------------------------------------------------------------- voxels

def voxelize(tris, origin, h, shape, chunk_points=20_000_000):
    """Mark every voxel a triangle passes through (sampled at h/3, so no 6-gaps)."""
    grid = np.zeros(shape, dtype=bool)
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    longest = np.max(np.stack([np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1),
                               np.linalg.norm(a - c, axis=1)]), axis=0)
    steps = np.maximum(1, np.ceil(longest / (h / 3.0))).astype(np.int64)
    limit = np.array(shape) - 1
    for n in np.unique(steps):
        sel = np.nonzero(steps == n)[0]
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
        keep = (i + j) <= n
        u = (i[keep] / n)[None, :, None]
        v = (j[keep] / n)[None, :, None]
        per = u.shape[1]
        batch = max(1, chunk_points // per)
        for k in range(0, len(sel), batch):
            s = sel[k:k + batch]
            pa, pb, pc = a[s][:, None, :], b[s][:, None, :], c[s][:, None, :]
            pts = pa + u * (pb - pa) + v * (pc - pa)
            ijk = np.floor((pts.reshape(-1, 3) - origin) / h).astype(np.int64)
            ok = np.all((ijk >= 0) & (ijk <= limit), axis=1)
            ijk = ijk[ok]
            grid[ijk[:, 0], ijk[:, 1], ijk[:, 2]] = True
    return grid


def course_field(deck, origin, h, shape, pitch_m, depth_m, ground=0.0):
    """One uniform course pattern on a roof deck, as an occupancy field (0..1 per voxel).

    A roof's own tiles are far below what a nozzle can draw (a 25 cm tile is 1 mm at
    1:250), and voxelized they come out as a different moire on every roof plane, with
    the odd tile proud of the rest. So the tiles are left out and each sloped deck
    triangle carries a shingle sawtooth instead: a course every `pitch_m` up the slope,
    standing `depth_m` proud at its butt and thinning to the deck under the next butt.
    The phase is counted along the slope from grade (z / sin(pitch)), so every roof,
    dormer and turret cone gets the same courses at the same spacing, level wherever
    the roof is. Flat (< 15 deg) and near-vertical (> 75 deg) faces are left plain.

    The field holds a signed distance to the sawtooth, scaled to a voxel, rather than
    a yes/no per voxel, so the contour puts every butt and every slope where it is to
    a fraction of a voxel: a yes/no grid would alias the courses against its own
    stair-steps and no two would come out alike.
    """
    field = np.zeros(shape, dtype=np.float32)
    flat_field = field.reshape(-1)
    a, b, c = deck[:, 0], deck[:, 1], deck[:, 2]
    n = np.cross(b - a, c - a)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    n *= np.where(n[:, 2:3] < 0, -1.0, 1.0)         # single-sided deck: always point up
    sloped = (n[:, 2] < math.cos(math.radians(15))) & (n[:, 2] > math.cos(math.radians(75)))
    a, b, c, n = a[sloped], b[sloped], c[sloped], n[sloped]
    sin_t = np.sqrt(np.maximum(1 - n[:, 2] ** 2, 1e-9))
    longest = np.max(np.stack([np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1),
                               np.linalg.norm(a - c, axis=1)]), axis=0)
    steps = np.maximum(1, np.ceil(longest / (h / 2.0))).astype(np.int64)
    offsets = np.arange(-1.0 * h, depth_m + 1.5 * h, h / 2.0)
    limit = np.array(shape) - 1
    strides = np.array([shape[1] * shape[2], shape[2], 1])
    for k in np.unique(steps):
        sel = np.nonzero(steps == k)[0]
        i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1), indexing="ij")
        keep = (i + j) <= k
        u = (i[keep] / k)[None, :, None]
        v = (j[keep] / k)[None, :, None]
        batch = max(1, 3_000_000 // (u.shape[1] * len(offsets)))
        for q in range(0, len(sel), batch):
            t = sel[q:q + batch]
            pts = a[t][:, None] + u * (b[t] - a[t])[:, None] + v * (c[t] - a[t])[:, None]
            nt = np.repeat(n[t], u.shape[1], axis=0)
            st = np.repeat(sin_t[t], u.shape[1])
            pa = np.repeat(a[t], u.shape[1], axis=0)
            pts = pts.reshape(-1, 3)
            for o in offsets:
                ijk = np.floor((pts + o * nt - origin) / h).astype(np.int64)
                ok = np.all((ijk >= 0) & (ijk <= limit), axis=1)
                ijk, nn, ss, aa = ijk[ok], nt[ok], st[ok], pa[ok]
                centre = origin + (ijk + 0.5) * h
                dn = np.einsum("ij,ij->i", centre - aa, nn)          # height above the deck
                foot_z = centre[:, 2] - dn * nn[:, 2]
                phase = np.mod((foot_z - ground) / ss / pitch_m, 1.0)
                top = depth_m * (1.0 - phase)
                inside = (dn >= 0) & (dn <= top)
                d_in = np.minimum(np.minimum(top - dn, phase * pitch_m), dn + 0.5 * h)
                up_face = np.where(dn < depth_m, (1.0 - phase) * pitch_m, np.inf)
                d_out = np.where(dn < 0, -dn, np.minimum(dn - top, up_face))
                occ = np.clip(0.5 + np.where(inside, d_in, -d_out) / h, 0.0, 1.0).astype(np.float32)
                flat = ijk @ strides
                occ = np.maximum(occ, flat_field[flat])
                order = np.argsort(occ, kind="stable")            # last write wins: the max
                flat_field[flat[order]] = occ[order]
    return field, int(sloped.sum())


def voxelize_courses(deck, origin, h, shape, pitch_m, depth_m, ground=0.0):
    """The course field as a yes/no voxel grid (what the field's contour encloses)."""
    field, used = course_field(deck, origin, h, shape, pitch_m, depth_m, ground)
    return field >= 0.5, used


def fill_enclosed(shell):
    """Solid = shell plus every air pocket the outside air cannot reach (6-connected)."""
    padded = np.pad(~shell, 1, constant_values=True)
    padded[:, :, 0] = False  # the ground is not air: a house has no floor in a render GLB
    labels, _ = ndimage.label(padded, structure=ndimage.generate_binary_structure(3, 1))
    outside = labels == labels[-1, -1, -1]
    del labels
    return ~outside[1:-1, 1:-1, 1:-1]


def _rooms_coarse(solid, k):
    """Room mask on one grid: ball-sized covered air cut off from the outside air,
    grown through the air against the outside air until the two meet."""
    pad = k + 2
    air = np.pad(~solid, ((pad, pad), (pad, pad), (0, pad)), constant_values=True)
    core = ndimage.distance_transform_edt(air) > k
    six = ndimage.generate_binary_structure(3, 1)
    labels, n = ndimage.label(core, structure=six)
    outside_id = labels[-1, -1, -1]
    # A room is under something: nearly all of its core has the building overhead.
    # That keeps an open court or a yard between a wall and a fence from counting.
    covered = np.flip(np.logical_or.accumulate(np.flip(~air, 2), axis=2), 2)
    ids = np.arange(n + 1)
    total = ndimage.sum(core, labels, ids)
    under = ndimage.sum(core & covered, labels, ids)
    del covered
    room_ids = [i for i in range(1, n + 1) if i != outside_id and under[i] >= 0.9 * total[i]]
    if not room_ids:
        return None
    rooms = np.isin(labels, room_ids)
    outside = labels == outside_id
    del labels, core
    # Grow both through the air one step at a time; a voxel both reach in the same
    # step stays outside, so an opening is shut no further out than its middle.
    free = air & ~rooms & ~outside
    for _ in range(4 * k):
        to_out = ndimage.binary_dilation(outside, six) & free
        to_room = ndimage.binary_dilation(rooms, six) & free & ~to_out
        if not to_out.any() and not to_room.any():
            break
        outside |= to_out
        rooms |= to_room
        free &= ~(to_out | to_room)
    return rooms[pad:-pad, pad:-pad, :-pad]


def fill_rooms(solid, k, coarse=2):
    """Fill the rooms an open doorway, a missing pane or a gap between roofs lets air into.

    A render GLB has no floors or interior walls and often an opening or two that
    nobody sees from the street (Glessner has one where its roofs meet above the
    court), so the outside air floods the whole house and it would print as a hollow
    shell. A ball of radius k voxels rolls through the outside air and through any
    room, but not through an opening narrower than 2k: covered, ball-sized air cut
    off from the outside that way is a room. Room and outside air then grow toward
    each other through the air until they meet, so the room fills out to its walls
    and corners while a window reveal, a porch or a carriage passage, which the
    outside air reaches first, keeps its air. Worked on a grid `coarse` times
    coarser (walls kept closed), then brought back to full resolution.
    """
    if k <= 0:
        return solid, 0
    if coarse > 1:
        sx, sy, sz = (-(-d // coarse) * coarse for d in solid.shape)
        padded = np.zeros((sx, sy, sz), bool)
        padded[: solid.shape[0], : solid.shape[1], : solid.shape[2]] = solid
        small = padded.reshape(sx // coarse, coarse, sy // coarse, coarse, sz // coarse, coarse).any(axis=(1, 3, 5))
        rooms = _rooms_coarse(small, max(1, k // coarse))
        if rooms is None:
            return solid, 0
        rooms = rooms.repeat(coarse, 0).repeat(coarse, 1).repeat(coarse, 2)[
            : solid.shape[0], : solid.shape[1], : solid.shape[2]]
        # The coarse walls were fattened by up to a voxel: reach back out to the fine ones.
        rooms = ndimage.binary_dilation(rooms, iterations=coarse, mask=~solid)
    else:
        rooms = _rooms_coarse(solid, k)
        if rooms is None:
            return solid, 0
    rooms &= ~solid
    filled = int(rooms.sum())
    return fill_enclosed(solid | rooms), filled


def ball(r):
    g = np.arange(-r, r + 1)
    x, y, z = np.meshgrid(g, g, g, indexing="ij")
    return (x * x + y * y + z * z) <= r * r + 1e-9


def thicken_thin(solid, r):
    """Grow only the parts an r-ball cannot sit inside, by r: thin -> at least 2r+1 voxels."""
    if r <= 0:
        return solid, 0
    se = ball(r)
    core = ndimage.binary_opening(solid, structure=se)
    thin = solid & ~core
    del core
    grown = ndimage.binary_dilation(thin, structure=se)
    return solid | grown, int(thin.sum())


# ------------------------------------------------------------------------- mesh

def mesh_solid(solid, h_mm, sigma=0.0, field=None):
    from skimage import measure

    vol = np.pad(solid, 2).astype(np.float32)
    if sigma > 0:
        # A light blur before contouring turns voxel stairs into flat faces and
        # rounded arrises; walls stay where they are (level 0.5 is the voxel face).
        vol = ndimage.gaussian_filter(vol, sigma, output=np.float32)
    if field is not None:                        # sub-voxel roof courses on top
        np.maximum(vol, np.pad(field, 2), out=vol)
    verts, faces, _n, _v = measure.marching_cubes(vol, level=0.5, allow_degenerate=False)
    verts = (verts - 2.0) * h_mm  # undo the pad; voxel index -> mm on the print
    # skimage winds its triangles toward the low side of the field (the air is 0, the
    # solid 1), so the normals point inward; 3MF wants them outward.
    return verts.astype(np.float64), faces[:, ::-1].astype(np.int64)


def _manifold(verts, faces):
    import manifold3d as mf

    return mf.Manifold(mf.Mesh(vert_properties=np.ascontiguousarray(verts, dtype=np.float32),
                               tri_verts=np.ascontiguousarray(faces, dtype=np.uint32)))


def _arrays(man):
    out = man.to_mesh()
    return np.asarray(out.vert_properties, dtype=np.float64)[:, :3], np.asarray(out.tri_verts, dtype=np.int64)


def _part_coincident(verts, faces, nudge=2e-3):
    """Two vertices on one spot (a pinch where two sheets of the solid touch) read as
    one to a slicer that merges by position, which would make the edge non-manifold.
    Move each a hair toward its own neighbours, so they stay two."""
    key = np.round(verts, WRITE_DECIMALS - 1)
    _u, inv, counts = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    shared = np.nonzero(counts[inv.ravel()] > 1)[0]
    if not len(shared):
        return verts, 0
    verts = verts.copy()
    total = np.zeros((len(verts), 3))
    n = np.zeros(len(verts))
    for i, j in ((0, 1), (1, 2), (2, 0), (1, 0), (2, 1), (0, 2)):
        np.add.at(total, faces[:, i], verts[faces[:, j]])
        np.add.at(n, faces[:, i], 1)
    toward = total[shared] / n[shared, None] - verts[shared]
    toward /= np.maximum(np.linalg.norm(toward, axis=1, keepdims=True), 1e-12)
    verts[shared] += nudge * toward
    return verts, len(shared)


def _flip_flat(verts, faces, passes=20):
    """Flip away zero-area 'cap' triangles: (a, b, c) with c lying on its long edge ab.

    With its neighbour (b, a, d) across ab the pair becomes (c, a, d) + (c, d, b): the
    same quad, same outline, orientation kept, and no triangle lies flat any more.
    Only a handful of triangles take part, so this is a plain dictionary walk.
    """
    faces = faces.copy()
    v = verts
    edge = {}
    for fi, (a, b, c) in enumerate(faces.tolist()):
        edge[(a, b)] = fi
        edge[(b, c)] = fi
        edge[(c, a)] = fi
    flipped = 0
    for _ in range(passes):
        area = np.linalg.norm(np.cross(v[faces[:, 1]] - v[faces[:, 0]], v[faces[:, 2]] - v[faces[:, 0]]), axis=1) / 2
        flat = np.nonzero(area < 1e-8)[0]
        if not len(flat):
            break
        changed = False
        for fi in flat.tolist():
            tri = faces[fi].tolist()
            if np.linalg.norm(np.cross(v[tri[1]] - v[tri[0]], v[tri[2]] - v[tri[0]])) / 2 >= 1e-8:
                continue                             # an earlier flip already fixed it
            lens = [np.linalg.norm(v[tri[(k + 1) % 3]] - v[tri[k]]) for k in range(3)]
            k = int(np.argmax(lens))                 # long edge tri[k] -> tri[k+1]
            a, b, c = tri[k], tri[(k + 1) % 3], tri[(k + 2) % 3]
            fj = edge.get((b, a))
            if fj is None or fj == fi:
                continue
            other = faces[fj].tolist()
            d = [x for x in other if x not in (a, b)]
            if len(d) != 1 or (c, d[0]) in edge or (d[0], c) in edge:
                continue
            d = d[0]
            for t in (tri, other):
                for m in range(3):
                    edge.pop((t[m], t[(m + 1) % 3]), None)
            faces[fi] = (c, a, d)
            faces[fj] = (c, d, b)
            for t, idx in (((c, a, d), fi), ((c, d, b), fj)):
                for m in range(3):
                    edge[(t[m], t[(m + 1) % 3])] = idx
            flipped += 1
            changed = True
        if not changed:
            break
    return faces, flipped


def _flaws(verts, faces):
    """What a slicer would 'repair': coincident vertices and zero-area triangles, as written."""
    v = verts
    area = np.linalg.norm(np.cross(v[faces[:, 1]] - v[faces[:, 0]], v[faces[:, 2]] - v[faces[:, 0]]), axis=1) / 2
    _u, counts = np.unique(v, axis=0, return_counts=True)
    return int((counts > 1).sum()), int((area < 1e-8).sum())


def mesh_clean(verts, faces, tolerance_mm, log=lambda *m: None):
    """Simplify (manifold kept), keep the one solid, and leave nothing a slicer would repair.

    Simplification can squeeze a triangle flat or land two vertices on one spot; the
    tolerance is halved until it does not (0 = the marching-cubes mesh as it came).
    Returns (manifold, verts, faces, stats).
    """
    base = _manifold(verts, faces)
    status = str(base.status())
    if not status.endswith("NoError"):
        raise SystemExit(f"marching-cubes mesh is not manifold: {status}")
    stats = {}
    ladder = [tolerance_mm / d for d in (1, 2, 4, 8)] + [0.0] if tolerance_mm > 0 else [0.0]
    for tol in ladder:
        man = base.simplify(tol) if tol > 0 else base
        pieces = man.decompose()
        if len(pieces) > 1:
            # The blur can seal a hair-wide air slit into a bubble (an inside-out shell,
            # negative volume: dropping it fills it) or part a crumb off (dropped).
            pieces.sort(key=lambda m: m.volume(), reverse=True)
            voids = [m.volume() for m in pieces[1:] if m.volume() < 0]
            crumbs = [m.volume() for m in pieces[1:] if m.volume() >= 0]
            stats["sealed_bubbles_filled_mm3"] = round(-math.fsum(voids), 2)
            stats["crumbs_dropped_mm3"] = round(math.fsum(crumbs), 2)
            man = pieces[0]
        v, f = _arrays(man)
        v, parted = _part_coincident(v, f)
        # Snap to exactly what the 3MF will hold (origin at the bed corner, 5 decimals),
        # so the flaws are counted on the written coordinates, not on finer ones.
        v = np.round(v - v.min(axis=0), WRITE_DECIMALS)
        f, flips = _flip_flat(v, f)
        coincident, flat = _flaws(v, f)
        log(f"simplified at {tol:.4f} mm: {len(f):,} triangles, {flat} flat, {coincident} coincident"
            + (f"; {parted} pinch vertices parted" if parted else "")
            + (f"; {flips} flat triangles flipped away" if flips else ""))
        if not flat and not coincident:
            break
    if flips or parted:
        man = _manifold(v, f)                        # the edited mesh is still a manifold
        status = str(man.status())
        if not status.endswith("NoError"):
            raise SystemExit(f"cleaned mesh is not manifold: {status}")
    stats.update({"simplify_mm_used": round(tol, 4), "pinch_vertices_parted": parted,
                  "flat_triangles_flipped": flips,
                  "flat_triangles": flat, "coincident_vertices": coincident})
    return man, v, f, stats


def verify(verts, faces):
    """Independent check: every undirected edge used exactly twice, once each way."""
    e = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    directed = e[:, 0] * (len(verts) + 1) + e[:, 1]
    reverse = e[:, 1] * (len(verts) + 1) + e[:, 0]
    unique_directed = np.unique(directed).size == directed.size
    matched = np.isin(directed, reverse).all()
    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    volume = float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)
    return {"edges_paired": bool(unique_directed and matched), "signed_volume_mm3": round(volume, 1)}


def render_preview(verts, faces, path: Path, views=((210, 28), (30, 28), (300, 55)), width=900):
    """Grey-shaded orthographic views of the print, side by side, as a PNG (needs Pillow).

    Splats points sampled on every triangle into a z-buffer: no GPU, no browser.
    Azimuth is degrees clockwise from looking north (+y), elevation above the bed.
    """
    from PIL import Image

    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    normal = np.cross(b - a, c - a)
    normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
    centre = (verts.max(axis=0) + verts.min(axis=0)) / 2
    longest = np.max(np.stack([np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1),
                               np.linalg.norm(a - c, axis=1)]), axis=0)
    height = int(width * 0.62)
    tiles = []
    for az, el in views:
        t, e = math.radians(az), math.radians(el)
        right = np.array([math.cos(t), -math.sin(t), 0.0])
        forward = np.array([math.sin(t) * math.cos(e), math.cos(t) * math.cos(e), -math.sin(e)])
        up = np.cross(right, forward)
        rel = verts - centre
        span_x, span_y = np.ptp(rel @ right), np.ptp(rel @ up)
        px = max(span_x / (width * 0.94), span_y / (height * 0.94))
        mid_x, mid_y = (rel @ right).min() + span_x / 2, (rel @ up).min() + span_y / 2
        steps = np.maximum(1, np.ceil(longest / (px * 0.5))).astype(np.int64)
        light = -forward * 0.55 + up * 0.6 + right * 0.35
        light /= np.linalg.norm(light)
        shade_face = 0.25 + 0.75 * np.clip(normal @ light, 0, 1)
        depth = np.full(width * height, np.inf)
        shade = np.ones(width * height)
        for n in np.unique(steps):
            sel = np.nonzero(steps == n)[0]
            i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
            keep = (i + j) <= n
            u, v = (i[keep] / n)[None, :, None], (j[keep] / n)[None, :, None]
            for k in range(0, len(sel), max(1, 4_000_000 // u.shape[1])):
                s = sel[k:k + max(1, 4_000_000 // u.shape[1])]
                pts = (a[s][:, None] + u * (b[s] - a[s])[:, None] + v * (c[s] - a[s])[:, None]) - centre
                sh = np.repeat(shade_face[s], u.shape[1])
                pts = pts.reshape(-1, 3)
                x = np.floor((pts @ right - mid_x) / px + width / 2).astype(np.int64)
                y = np.floor(-(pts @ up - mid_y) / px + height / 2).astype(np.int64)
                d = pts @ forward
                ok = (x >= 0) & (x < width) & (y >= 0) & (y < height)
                pix = y[ok] * width + x[ok]
                d, sh = d[ok], sh[ok]
                order = np.lexsort((d, pix))
                pix, d, sh = pix[order], d[order], sh[order]
                first = np.ones(len(pix), bool)
                first[1:] = pix[1:] != pix[:-1]
                pix, d, sh = pix[first], d[first], sh[first]
                nearer = d < depth[pix]
                depth[pix[nearer]] = d[nearer]
                shade[pix[nearer]] = sh[nearer]
        img = np.where(np.isinf(depth), 0.96, shade * 0.9).reshape(height, width)
        tiles.append((img * 255).astype(np.uint8))
    Image.fromarray(np.concatenate(tiles, axis=0)).save(path)


def write_3mf(path: Path, verts, faces, title, description):
    """Minimal 3MF core package: one mesh object, millimetres, one build item."""
    path.parent.mkdir(parents=True, exist_ok=True)
    vert_xml = "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in verts)
    tri_xml = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces)

    def esc(s):
        return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))

    model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
        f'<metadata name="Title">{esc(title)}</metadata>\n'
        f'<metadata name="Description">{esc(description)}</metadata>\n'
        '<metadata name="Application">chicago 4d tools/export_print_3mf.py</metadata>\n'
        f'<resources><object id="1" type="model" name="{esc(title)}"><mesh>'
        f'<vertices>{vert_xml}</vertices><triangles>{tri_xml}</triangles>'
        '</mesh></object></resources>\n'
        '<build><item objectid="1"/></build>\n</model>\n'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
        '</Types>\n'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        '</Relationships>\n'
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


# ------------------------------------------------------------------------ build

def solidify(tris, args, log=lambda *m: None, deck=None):
    """Print-ready voxel solid from Z-up triangles in real metres; steps 2-6 of the docstring.

    Returns (solid bool grid, voxel index -> print mm by * voxel_mm; stats dict).
    """
    scale = float(args.scale)                    # print = real / scale
    h_mm = float(args.voxel_mm)
    h = h_mm * scale / 1000.0                    # voxel edge in real metres
    ground = float(args.ground)
    tris = tris[tris[..., 2].max(axis=1) > ground]  # whatever lies wholly below grade
    lo = tris.reshape(-1, 3).min(axis=0)
    hi = tris.reshape(-1, 3).max(axis=0)
    lo[2] = ground
    margin = 2 * h
    origin = lo - np.array([margin, margin, 0.0])
    shape = tuple(int(x) for x in np.ceil((hi - origin + margin) / h).astype(int))
    log(f"grid {shape[0]}x{shape[1]}x{shape[2]} voxels of {h * 100:.1f} cm "
        f"({h_mm} mm on the print at 1:{scale:g}), {np.prod(shape) / 1e6:.0f} M cells")

    shell = voxelize(tris, origin, h, shape)
    log(f"rasterised: {int(shell.sum()):,} surface voxels")
    course_faces, field = 0, None
    if deck is not None and len(deck):
        pitch_m = args.course_mm * scale / 1000.0
        depth_m = args.course_depth_mm * scale / 1000.0
        field, course_faces = course_field(deck, origin, h, shape, pitch_m, depth_m, ground)
        log(f"roof courses: one {args.course_mm} mm course, {args.course_depth_mm} mm proud, "
            f"laid on {course_faces:,} sloped deck triangles")
    solid = fill_enclosed(shell)
    del shell
    log(f"filled: {int(solid.sum()):,} solid voxels")
    solid, rooms = fill_rooms(solid, int(round(args.room_ball_m / h)))
    log(f"rooms: {rooms:,} voxels of interior the air reached through openings narrower "
        f"than {2 * args.room_ball_m:g} m, filled")

    # Ground clutter: anything lower than --clutter-m above grade that lies more
    # than --keep-margin-m from the building's walls (walks, curbs, a lawn edging).
    clutter_z = max(1, int(round(args.clutter_m / h)))
    walls = solid[:, :, clutter_z:].any(axis=2)
    keep = ndimage.binary_dilation(walls, structure=np.ones((3, 3), bool),
                                   iterations=max(1, int(round(args.keep_margin_m / h))))
    low = solid[:, :, :clutter_z]               # a view: trimming it trims the solid
    cut = int((low & ~keep[:, :, None]).sum())
    low &= keep[:, :, None]
    log(f"ground clutter: removed {cut:,} voxels beyond {args.keep_margin_m} m of the walls")

    r = int(math.ceil((args.min_feature_mm / h_mm - 1) / 2))
    solid, thin = thicken_thin(solid, r)
    log(f"thin parts: {thin:,} voxels under {(2 * r + 1) * h_mm:.1f} mm thickened")

    base_layers = int(round(args.base_mm / h_mm))
    if base_layers:
        footprint = solid[:, :, : max(1, int(round(0.5 / h)))].any(axis=2)  # what stands on the ground
        footprint = ndimage.binary_fill_holes(footprint)            # enclosed courts get a floor
        footprint = ndimage.binary_closing(footprint, structure=np.ones((3, 3), bool), iterations=2)
        footprint = ndimage.binary_dilation(footprint, structure=np.ones((3, 3), bool),
                                            iterations=max(1, int(round(args.base_lip_mm / h_mm))))
        solid = np.concatenate([np.repeat(footprint[:, :, None], base_layers, axis=2), solid], axis=2)
        if field is not None:
            field = np.concatenate([np.zeros(field.shape[:2] + (base_layers,), np.float32), field], axis=2)
    labels, n = ndimage.label(solid, structure=ndimage.generate_binary_structure(3, 1))
    loose = 0
    if n > 1:
        sizes = np.bincount(labels.ravel())
        sizes[0] = 0
        main = int(sizes.argmax())
        loose = int(sizes.sum() - sizes[main])
        solid = labels == main
        log(f"kept the one connected piece; dropped {n - 1} loose bit(s), {loose:,} voxels")
    del labels
    solid = fill_enclosed(np.pad(solid, ((0, 0), (0, 0), (1, 0))))[:, :, 1:]  # voids sealed by thickening
    stats = {
        "min_feature_mm": round((2 * r + 1) * h_mm, 2),
        "base_mm": round(base_layers * h_mm, 2),
        "ground_clutter_voxels_removed": cut,
        "thin_voxels_thickened": thin,
        "room_voxels_filled": rooms,
        "loose_voxels_dropped": loose,
        "roof_course_deck_triangles": course_faces,
    }
    if field is not None:
        field[~ndimage.binary_dilation(solid, iterations=int(math.ceil(args.course_depth_mm / h_mm)) + 2)] = 0
        stats["_course_field"] = field                # handed to mesh_solid, not reported
    return solid, stats


def resolve_glb(args):
    if args.glb:
        return Path(args.glb)
    manifest = json.loads((ROOT / "assets/manifest.json").read_text())
    entries = manifest.get("assets", manifest)
    names = sorted(k for k, v in entries.items() if isinstance(v, dict)
                   and v.get("structure_id") == args.structure
                   and (args.phase is None or v.get("phase_id") == args.phase))
    if not names:
        raise SystemExit(f"no GLB in assets/manifest.json for structure {args.structure!r}"
                         + (f" phase {args.phase!r}" if args.phase else ""))
    if len(names) > 1:
        raise SystemExit(f"{args.structure} has several phases ({', '.join(names)}); pass --phase")
    path = ROOT / "assets/gltf" / names[0]
    if not path.exists():
        hint = (" (run python3 tools/recover_glessner_v4.py --materialize)"
                if args.structure == "glessner_house" else "")
        raise SystemExit(f"{path.relative_to(ROOT)} is not on disk{hint}")
    return path


def _offset_from(tris, deck, step=0.05, lateral=False):
    """Each triangle's centre height off the nearest point of the deck, along the deck's
    upward normal (real m; Y-up glTF triangles), and whether no deck lies within 0.5 m;
    with `lateral`, also how far it lies across the deck from that point."""
    from scipy.spatial import cKDTree

    pts, nrm = [], []
    longest = np.max(np.linalg.norm(deck - np.roll(deck, 1, axis=1), axis=2), axis=1)
    steps = np.maximum(1, np.ceil(longest / step)).astype(int)
    for k in np.unique(steps):
        sel = deck[steps == k]
        i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1), indexing="ij")
        keep = (i + j) <= k
        u, v = (i[keep] / k)[None, :, None], (j[keep] / k)[None, :, None]
        a, b, c = sel[:, 0][:, None], sel[:, 1][:, None], sel[:, 2][:, None]
        n = np.cross(sel[:, 1] - sel[:, 0], sel[:, 2] - sel[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        n *= np.where(n[:, 1:2] < 0, -1.0, 1.0)      # glTF Y-up: the deck faces the sky
        pts.append((a + u * (b - a) + v * (c - a)).reshape(-1, 3))
        nrm.append(np.repeat(n, u.shape[1], axis=0))
    pts, nrm = np.concatenate(pts), np.concatenate(nrm)
    centre = tris.mean(axis=1)
    dist, idx = cKDTree(pts).query(centre, distance_upper_bound=0.5)
    far = ~np.isfinite(dist)
    idx = np.where(far, 0, idx)
    off = np.einsum("ij,ij->i", centre - pts[idx], nrm[idx])
    if lateral:
        return off, far, np.sqrt(np.maximum(np.where(far, np.inf, dist) ** 2 - off ** 2, 0))
    return off, far


def _proud_of(tris, deck, min_m, step=0.05):
    """Which triangles stand more than min_m off the deck (along its normal), or have no
    deck under them at all: a ridge roll or hip cap, not a tile lying on the roof."""
    off, far = _offset_from(tris, deck, step)
    return far | (off > min_m)


def split_sheet_roof(tris, seam_m=0.04, min_width_m=0.05):
    """A sheet-metal roof (copper) as (sheet, seam) masks over its Y-up triangles.

    The sheets are its broad sloped faces (15 to 75 deg, the slopes that take courses, at
    least `min_width_m` across); the standing seams and folded stock are the narrow
    pieces lying on a sheet, over it and at most `seam_m` proud of it. A seam is 2 cm wide and 1.6 cm tall
    in the model, 0.06 mm on the print: rasterised it comes out as a line of one-voxel
    nubs that the thickener then swells into beads. Everything else made of the metal
    (flashing, finials, cresting, gutters) is neither and stays as modelled.
    """
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    n = np.cross(b - a, c - a)
    area2 = np.linalg.norm(n, axis=1)
    up = np.abs(n[:, 1]) / np.maximum(area2, 1e-12)            # glTF Y-up
    longest = np.max(np.stack([np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1),
                               np.linalg.norm(a - c, axis=1)]), axis=0)
    narrow = area2 / np.maximum(longest, 1e-12) < min_width_m
    sheet = (up > math.cos(math.radians(75))) & (up < math.cos(math.radians(15))) & ~narrow
    seam = np.zeros(len(tris), bool)
    if sheet.any() and narrow.any():
        off, far, across = _offset_from(tris[narrow], tris[sheet], lateral=True)
        seam[narrow] = ~far & (off > -0.005) & (off <= seam_m) & (across <= 0.05)
    return sheet, seam


def _z_up(tris):
    """glTF is Y-up; the print is Z-up. (x, y, z) -> (x, -z, y) is a rotation, so
    winding and handedness survive."""
    return np.stack([tris[..., 0], -tris[..., 2], tris[..., 1]], axis=-1)


def build(args):
    t0 = time.time()
    log = (lambda *m: print(f"[{time.time() - t0:6.1f}s]", *m, flush=True)) if not args.quiet else (lambda *m: None)
    glb = resolve_glb(args)
    parts = load_triangles(glb)
    exclude = tuple(DEFAULT_EXCLUDE) + tuple(args.exclude)
    deck = None
    if args.roof_tiles == "uniform":
        names = {n for n, _t in parts}
        tile_names = {n for n in names if any(fnmatch.fnmatch(n.lower(), g.lower()) for g in args.tile_material)}
        deck_names = {n for n in names if any(fnmatch.fnmatch(n.lower(), g.lower()) for g in args.deck_material)}
        if tile_names and deck_names:
            exclude += tuple(sorted(tile_names))
            deck_raw = np.concatenate([t for n, t in parts if n in deck_names])
            # Ridge and hip rolls are made of the same tile material: keep whatever
            # stands well off the deck, so only the courses themselves are replaced.
            rolls = [(f"{n} (ridge rolls)", t[m]) for n, t in parts if n in tile_names
                     for m in [_proud_of(t, deck_raw, args.roll_m)] if m.any()]
            parts = parts + rolls
            log(f"uniform roof: tiles {sorted(tile_names)} replaced by courses on {sorted(deck_names)}; "
                f"kept {sum(len(t) for _n, t in rolls):,} ridge/hip roll triangles standing over "
                f"{args.roll_m} m off the deck")
            # Sheet-metal roofs (Glessner's copper dining bay and courtyard hood) take
            # the same courses: their sheets join the deck, their seams go.
            sheet_names = {n for n in names if any(fnmatch.fnmatch(n.lower(), g.lower())
                                                   for g in args.sheet_material)} - tile_names - deck_names
            decks, split = [deck_raw], []
            for n, t in parts:
                if n in sheet_names:
                    sheet, seam = split_sheet_roof(t)
                    decks.append(t[sheet])
                    split.append((n, t[~seam]))
                    log(f"uniform roof: {n}: {int(sheet.sum()):,} sheet triangles take courses, "
                        f"{int(seam.sum()):,} seam triangles dropped")
                else:
                    split.append((n, t))
            parts = split
            deck = _z_up(np.concatenate(decks))
        else:
            log("uniform roof: no tile and deck materials found by name; roof kept as modelled")
    kept, dropped = select(parts, exclude, tuple(args.include))
    if not kept:
        raise SystemExit("every material was excluded")
    tris = _z_up(np.concatenate([t for _n, t in kept]))
    log(f"{glb.name}: kept {len(tris):,} triangles in {len(kept)} material(s); "
        f"dropped {sum(dropped.values()):,} in {sorted(dropped)}")

    solid, stats = solidify(tris, args, log, deck=deck)
    scale, h_mm = float(args.scale), float(args.voxel_mm)

    verts, faces = mesh_solid(solid, h_mm, args.smooth, stats.pop("_course_field", None))
    log(f"marching cubes: {len(faces):,} triangles")
    man, verts, faces, mesh_stats = mesh_clean(verts, faces, args.simplify_mm, log)
    stats.update(mesh_stats)
    pieces = len(man.decompose())
    check = verify(verts, faces)
    ok = (check["edges_paired"] and check["signed_volume_mm3"] > 0 and pieces == 1
          and not stats["flat_triangles"] and not stats["coincident_vertices"])
    size = (verts.max(axis=0) - verts.min(axis=0))
    verts = verts - np.array([verts[:, 0].min(), verts[:, 1].min(), verts[:, 2].min()])

    title = args.title or f"{glb.stem} 1:{scale:g}"
    desc = (f"Watertight print of {glb.name} at 1:{scale:g}; min feature {stats['min_feature_mm']} mm; "
            f"base {stats['base_mm']} mm; voxel {h_mm} mm. Generated by tools/export_print_3mf.py.")
    out = Path(args.out)
    if not ok:
        raise SystemExit(f"refusing to write {out}: verification failed: {check}, pieces={pieces}, "
                         f"flat={stats['flat_triangles']}, coincident={stats['coincident_vertices']}")
    write_3mf(out, verts, faces, title, desc)
    report = {
        "glb": str(glb.relative_to(ROOT)) if glb.is_relative_to(ROOT) else str(glb),
        "out": str(out),
        "scale": f"1:{scale:g}",
        "print_size_mm": [round(float(x), 1) for x in size],
        "real_size_m": [round(float(x) * scale / 1000, 2) for x in size],
        "voxel_mm": h_mm,
        "triangles": int(len(faces)),
        "vertices": int(len(verts)),
        "volume_cm3": round(man.volume() / 1000.0, 1),
        "genus": int(man.genus()),
        "pieces": pieces,
        "watertight": ok,
        **check,
        "kept_materials": sorted({n for n, _t in kept}),
        "dropped_materials": dropped,
        **stats,
        "fdm": FDM_NOTES,
        "bytes": out.stat().st_size,
    }
    log(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB): "
        f"{report['print_size_mm']} mm, watertight={ok}, genus {report['genus']}")
    if args.preview:
        render_preview(verts, faces, Path(args.preview))
        log(f"preview {args.preview}")
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--structure", help="structure_id; its GLB is found through assets/manifest.json")
    src.add_argument("--glb", help="a GLB path instead of a structure id")
    p.add_argument("--phase", help="phase_id when the structure has several GLBs")
    p.add_argument("--out", required=True, help="the .3mf to write")
    p.add_argument("--report", help="also write the measurements as JSON here")
    p.add_argument("--preview", help="also write shaded views of the print as a PNG here")
    p.add_argument("--title", help="3MF title (default: GLB name and scale)")
    p.add_argument("--scale", type=float, default=250, help="print scale denominator (default 250 -> 1:250)")
    p.add_argument("--voxel-mm", type=float, default=0.2, help="solid resolution on the print (default 0.2)")
    p.add_argument("--min-feature-mm", type=float, default=1.0,
                   help="thinner parts are thickened to about this (default 1.0 for a 0.4 mm nozzle)")
    p.add_argument("--base-mm", type=float, default=1.6, help="base slab thickness; 0 for none (default 1.6)")
    p.add_argument("--base-lip-mm", type=float, default=1.0, help="how far the base runs past the walls")
    p.add_argument("--ground", type=float, default=0.0, help="grade height in model metres (default 0)")
    p.add_argument("--clutter-m", type=float, default=0.6,
                   help="real height under which far-off ground pieces are clutter (default 0.6)")
    p.add_argument("--keep-margin-m", type=float, default=1.5,
                   help="low pieces within this many real metres of a wall are kept (steps, stoops)")
    p.add_argument("--room-ball-m", type=float, default=2.0,
                   help="rooms reached only through openings narrower than twice this (real m) are filled")
    p.add_argument("--smooth", type=float, default=0.6,
                   help="blur in voxels before contouring; 0 for raw voxel stairs (default 0.6)")
    p.add_argument("--simplify-mm", type=float, default=0.05,
                   help="simplification tolerance on the print, manifold kept (default 0.05)")
    p.add_argument("--roof-tiles", choices=("uniform", "modelled"), default="uniform",
                   help="uniform (default): replace the modelled tiles with one course pattern on "
                        "every roof; modelled: voxelize the tiles as they are")
    p.add_argument("--tile-material", action="append", default=None,
                   help="material glob of the roof tiles to replace (default roof_plane_*)")
    p.add_argument("--deck-material", action="append", default=None,
                   help="material glob of the roof deck the courses are laid on (default roof_plane)")
    p.add_argument("--sheet-material", action="append", default=None,
                   help="material glob of sheet-metal roofs whose sheets take the same courses and "
                        "whose seams are dropped (default copper; 'none' for none)")
    p.add_argument("--roll-m", type=float, default=0.08,
                   help="tile-material pieces standing more than this (real m) off the deck are "
                        "ridge/hip rolls and are kept (default 0.08)")
    p.add_argument("--course-mm", type=float, default=1.2,
                   help="course spacing up the slope on the print (default 1.2)")
    p.add_argument("--course-depth-mm", type=float, default=0.4,
                   help="how far each course's butt stands proud on the print (default 0.4)")
    p.add_argument("--exclude", action="append", default=[], help="extra material glob to drop")
    p.add_argument("--include", action="append", default=[], help="material glob to keep despite the defaults")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)
    args.tile_material = args.tile_material or ["roof_plane_*"]
    args.deck_material = args.deck_material or ["roof_plane"]
    args.sheet_material = [] if args.sheet_material == ["none"] else (args.sheet_material or ["copper"])
    report = build(args)
    if args.quiet:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
