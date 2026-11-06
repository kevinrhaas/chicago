#!/usr/bin/env python3
"""tools/export_print_3mf.py makes one closed, solid, standing piece from a leaky render soup (T-3395).

A toy house written as a real GLB, built the way render GLBs are: four walls and a
roof as single-sided planes, no floor, an open doorway, a gap between the roof and
one wall, a wire-thin flagpole on the roof, a lawn quad under it all, a kerb out in
the street and a pebble floating in the air. The print must:

  - drop the lawn by its material name and the far kerb as ground clutter;
  - fill the room although the air reaches it through the door and the roof gap,
    yet leave the air outside the doorway alone;
  - thicken the flagpole to the minimum feature and keep it;
  - stand on a base and be one piece (the pebble goes);
  - when scikit-image and manifold3d are installed, mesh to a 3MF whose every edge
    is shared by exactly two triangles, with outward normals.

Needs numpy and scipy (the gate's own); the meshing half is skipped without the two
optional libraries, and says so.
"""
from __future__ import annotations

import importlib.util
import json
import struct
import sys
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_print_3mf as ex  # noqa: E402


def quad(a, b, c, d):
    return [(a, b, c), (a, c, d)]


def box(x0, y0, z0, x1, y1, z1):
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return [t for a, b, c, d in f for t in quad(p[a], p[b], p[c], p[d])]


def toy_house():
    """Z-up metres. A 8 x 6 x 5 m box of planes; door 1.2 m wide in the south wall."""
    walls = []
    # south wall (y = 0) with a door from x 3.4 to 4.6, 2.2 m tall
    walls += quad((0, 0, 0), (3.4, 0, 0), (3.4, 0, 5), (0, 0, 5))
    walls += quad((4.6, 0, 0), (8, 0, 0), (8, 0, 5), (4.6, 0, 5))
    walls += quad((3.4, 0, 2.2), (4.6, 0, 2.2), (4.6, 0, 5), (3.4, 0, 5))
    walls += quad((8, 0, 0), (8, 6, 0), (8, 6, 5), (8, 0, 5))          # east
    walls += quad((8, 6, 0), (0, 6, 0), (0, 6, 5), (8, 6, 5))          # north
    walls += quad((0, 6, 0), (0, 0, 0), (0, 0, 4.4), (0, 6, 4.4))      # west, 0.6 m short of the roof
    walls += quad((0, 0, 5), (8, 0, 5), (8, 6, 5), (0, 6, 5))          # flat roof
    pole = box(3.98, 2.98, 5, 4.02, 3.02, 7)                           # 4 cm flagpole
    lawn = quad((-3, -3, 0.01), (11, -3, 0.01), (11, 9, 0.01), (-3, 9, 0.01))
    kerb = box(-2.5, -2.8, 0, 10.5, -2.6, 0.15)                         # 2.6 m out
    pebble = box(10, 8, 3, 10.1, 8.1, 3.1)
    return {"stone": walls, "iron": pole, "lawn": lawn, "kerb_stone": kerb, "slate": pebble}


def write_glb(path: Path, parts):
    """Minimal GLB: one node, one mesh, one primitive per material, Y-up as glTF wants."""
    blobs, accessors, views, prims, mats = [], [], [], [], []
    offset = 0
    for i, (name, tris) in enumerate(parts.items()):
        pts = np.array(tris, dtype=np.float32).reshape(-1, 3)
        pts = np.stack([pts[:, 0], pts[:, 2], -pts[:, 1]], axis=1)    # Z-up -> glTF Y-up
        data = pts.tobytes()
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(data)})
        accessors.append({"bufferView": i, "componentType": 5126, "count": len(pts), "type": "VEC3",
                          "min": pts.min(axis=0).tolist(), "max": pts.max(axis=0).tolist()})
        prims.append({"attributes": {"POSITION": i}, "material": i})
        mats.append({"name": name})
        blobs.append(data)
        offset += len(data)
    gltf = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0, "name": "toy"}], "meshes": [{"primitives": prims}],
            "materials": mats, "accessors": accessors, "bufferViews": views,
            "buffers": [{"byteLength": offset}]}
    js = json.dumps(gltf).encode()
    js += b" " * (-len(js) % 4)
    binary = b"".join(blobs)
    binary += b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(js) + 8 + len(binary)
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(js), 0x4E4F534A) + js
                     + struct.pack("<II", len(binary), 0x004E4942) + binary)


def opts(**kw):
    base = dict(scale=100, voxel_mm=1.0, min_feature_mm=3.0, base_mm=2.0, base_lip_mm=1.0, ground=0.0,
                clutter_m=0.6, keep_margin_m=1.5, room_ball_m=1.0, smooth=0.6, simplify_mm=0.05,
                exclude=[], include=[])
    base.update(kw)
    return SimpleNamespace(**base)


def main():
    failures = []

    def expect(cond, what):
        print(("ok    " if cond else "FAIL  ") + what)
        if not cond:
            failures.append(what)

    with tempfile.TemporaryDirectory() as tmp:
        glb = Path(tmp) / "toy.glb"
        write_glb(glb, toy_house())
        parts = ex.load_triangles(glb)
        kept, dropped = ex.select(parts, ex.DEFAULT_EXCLUDE, ())
        expect(sorted(dropped) == ["lawn"], f"the lawn is dropped by name (dropped {sorted(dropped)})")
        tris = np.concatenate([t for _n, t in kept])
        tris = np.stack([tris[..., 0], -tris[..., 2], tris[..., 1]], axis=-1)
        expect(abs(tris[..., 2].max() - 7.0) < 1e-4 and abs(tris[..., 1].max() - 8.1) < 1e-4,
               "the GLB reads back Z-up in metres")

        a = opts()
        solid, stats = ex.solidify(tris, a)
        h = a.voxel_mm * a.scale / 1000.0            # 0.1 m a voxel
        lo = tris.reshape(-1, 3).min(axis=0)
        origin = np.array([lo[0] - 2 * h, lo[1] - 2 * h, -stats["base_mm"] / a.voxel_mm * h])

        def at(x, y, z):
            i, j, k = np.floor((np.array([x, y, z]) - origin) / h).astype(int)
            return bool(solid[i, j, k])

        expect(at(4.0, 3.0, 2.5) and at(1.0, 5.0, 1.0) and at(7.0, 1.0, 4.6),
               "the room is filled though the door and the roof gap let the air in")
        expect(stats["room_voxels_filled"] > 0, "…by the room fill, not by luck")
        expect(not at(4.0, -0.6, 1.0), "the air outside the doorway stays air")
        expect(at(4.0, 3.0, 6.5), "the 4 cm flagpole is kept")
        k = int(np.floor((6.5 - origin[2]) / h))
        pole = solid[:, :, k]
        expect(pole.sum() >= 9, f"…and thickened to the minimum feature ({int(pole.sum())} voxels across its section)")
        expect(not at(5.0, -2.7, 0.05), "the kerb out in the street is ground clutter and goes")
        expect(not at(10.05, 8.05, 3.05), "the floating pebble goes")
        expect(at(4.0, 3.0, -0.05) and at(-0.05, 3.0, -0.05), "the house stands on a base slab with a lip")
        from scipy import ndimage
        expect(ndimage.label(solid)[1] == 1, "one piece")

        have_mesh = all(importlib.util.find_spec(m) for m in ("skimage", "manifold3d"))
        if not have_mesh:
            print("skip  meshing half: scikit-image and manifold3d are not installed")
        else:
            out = Path(tmp) / "toy.3mf"
            verts, faces = ex.mesh_solid(solid, a.voxel_mm, a.smooth)
            man, verts, faces, mstats = ex.mesh_clean(verts, faces, a.simplify_mm)
            check = ex.verify(verts, faces)
            expect(check["edges_paired"], "every edge is shared by exactly two triangles, once each way")
            expect(check["signed_volume_mm3"] > 0, "normals point outward (positive signed volume)")
            expect(len(man.decompose()) == 1, "the mesh is one shell")
            expect(not mstats["flat_triangles"] and not mstats["coincident_vertices"],
                   "no flat triangle or doubled vertex for a slicer to 'repair'")
            ex.write_3mf(out, verts, faces, "toy", "test")
            with zipfile.ZipFile(out) as z:
                names = set(z.namelist())
                model = z.read("3D/3dmodel.model").decode()
            expect({"[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model"} <= names,
                   "the 3MF package has its three parts")
            expect('unit="millimeter"' in model and model.count("<triangle ") == len(faces),
                   "the model is in millimetres and carries every triangle")

    if failures:
        print(f"\n{len(failures)} check(s) failed")
        return 1
    print("\nprint export: all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
