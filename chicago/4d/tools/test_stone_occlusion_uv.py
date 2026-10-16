#!/usr/bin/env python3
"""T-2494: canonical UV caches must exist and reject changed inputs/corrupt layouts."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import sys
import tempfile
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generators"))
from archetypes import masonry_house_v4_occlusion as occlusion


class Collection:
    def __init__(self, count, **fields):
        self.count, self.fields = count, fields

    def __len__(self):
        return self.count

    def foreach_get(self, name, target):
        target[:] = np.asarray(self.fields[name]).ravel()


def check_committed():
    for size in (2048, 1024):
        occlusion.SIZE = size
        with np.load(occlusion._atlas_path(), allow_pickle=False) as atlas:
            assert {"unwrap_key", "uv", "uv_sha256"}.issubset(atlas.files), \
                f"{size}: atlas lacks canonical UVs; rebuild and commit the complete cache"
            key, loops = str(atlas["unwrap_key"]), len(atlas["uv"])
            assert len(key) == 64 and all(c in "0123456789abcdef" for c in key)
        assert occlusion._load_unwrap(np, key, loops) is not None, f"{size}: invalid UV cache"
        print(f"PASS {size}: committed canonical UV layout validates ({loops} corners)")


def test_cache():
    bpy = SimpleNamespace(app=SimpleNamespace(version_string="4.5.3 LTS"))
    mesh = SimpleNamespace(
        vertices=Collection(3, co=[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]),
        loops=Collection(3, vertex_index=[0, 1, 2]),
        polygons=Collection(1, loop_start=[0], loop_total=[3]))
    mask = np.array([True])
    key = occlusion._unwrap_key(bpy, np, mesh, mask)
    uv = np.array([[0., 0.], [1., 0.], [0., 1.]], np.float32)
    ao = np.full((4, 4), 128, np.uint8)
    covered = np.ones((4, 4), bool)
    with tempfile.TemporaryDirectory() as directory:
        occlusion.ATLAS_DIR, occlusion.SIZE = Path(directory), 4
        assert occlusion._load_unwrap(np, key, 3) is None
        path = occlusion._store_atlas(np, "a" * 64, ao, covered, key, uv)
        original_bytes = path.read_bytes()

        def failed_write(file, **_kwargs):
            file.write(b"partial write")
            raise OSError("simulated failed cache write")

        with patch.object(np, "savez_compressed", failed_write):
            try:
                occlusion._store_atlas(np, "a" * 64, ao, covered, key, uv)
                raise AssertionError("failed write was swallowed")
            except OSError:
                pass
        assert path.read_bytes() == original_bytes
        assert not list(Path(directory).glob("*.tmp"))
        assert np.array_equal(occlusion._load_unwrap(np, key, 3), uv)
        assert occlusion._load_unwrap(np, key, 4) is None
        assert occlusion._load_unwrap(np, "b" * 64, 3) is None
        assert np.array_equal(occlusion._load_atlas(np, "a" * 64)[0], ao)
        assert occlusion._load_atlas(np, "c" * 64) is None
        # Even a sub-millimetre geometry change invalidates the layout. So do
        # topology, mask, pinned Blender and each setting the unwrap reads.
        for collection, field in ((mesh.vertices, "co"), (mesh.loops, "vertex_index"),
                                  (mesh.polygons, "loop_start"), (mesh.polygons, "loop_total")):
            original = collection.fields[field]
            changed = np.asarray(original).copy()
            changed.flat[0] += .0001 if field == "co" else 1
            collection.fields[field] = changed
            assert occlusion._unwrap_key(bpy, np, mesh, mask) != key, field
            collection.fields[field] = original
        assert occlusion._unwrap_key(bpy, np, mesh, ~mask) != key
        bpy.app.version_string = "another Blender"
        assert occlusion._unwrap_key(bpy, np, mesh, mask) != key
        bpy.app.version_string = "4.5.3 LTS"
        for name in ("WELD_M", "ANGLE_LIMIT", "PACK_MARGIN", "UNWRAP_RECIPE"):
            original = getattr(occlusion, name)
            setattr(occlusion, name, original * 2)
            assert occlusion._unwrap_key(bpy, np, mesh, mask) != key, name
            setattr(occlusion, name, original)
        original = occlusion.PACK_OPTIONS["rotate"]
        occlusion.PACK_OPTIONS["rotate"] = not original
        assert occlusion._unwrap_key(bpy, np, mesh, mask) != key
        occlusion.PACK_OPTIONS["rotate"] = original
        # An AO-only recipe change keeps the valid unwrap; its separate atlas
        # key still determines whether Cycles must run.
        occlusion.SAMPLES += 1
        assert occlusion._unwrap_key(bpy, np, mesh, mask) == key
        occlusion.SAMPLES -= 1
        with np.load(path) as atlas:
            valid = {name: atlas[name] for name in atlas.files}
        mutations = [
            {name: value for name, value in valid.items() if name != "uv"},
            {**valid, "uv": uv.astype(np.float64)},
            {**valid, "uv": uv[:-1]},
            {**valid, "uv": uv + .01},
            {**valid, "uv_sha256": np.str_("0" * 64)},
        ]
        nan_uv = uv.copy()
        nan_uv[0, 0] = np.nan
        mutations.append({**valid, "uv": nan_uv,
                          "uv_sha256": np.str_(hashlib.sha256(nan_uv.tobytes()).hexdigest())})
        for corrupt in mutations:
            np.savez_compressed(path, **corrupt)
            assert occlusion._load_unwrap(np, key, 3) is None
    print("PASS stale mesh/recipe, missing layout, altered bytes, shape, dtype and NaNs are refused")
    print("PASS unchanged inputs retain UVs; the complete atlas key still guards AO reuse")
    print("PASS an interrupted cache write preserves the previous atlas")


if __name__ == "__main__":
    if "--fixtures-only" not in sys.argv:
        check_committed()
    test_cache()
