"""Terrain for a GRADED epoch: a zone table of street crowns + a traced waterline -> heightfield + GLB.

    # heightfield only (numpy is the one dependency)
    python3 generators/terrain_gen_graded.py --epoch e1871_postfire

    # re-derive and compare with the committed heightfield, writing nothing
    python3 generators/terrain_gen_graded.py --check

    # heightfield AND the terrain / water GLBs
    blender -b -noaudio --factory-startup --python generators/terrain_gen_graded.py -- --glb

T-1252. `generators/terrain_gen.py` builds the 1835 ground out of distance from a
natural waterline and three river-defined divisions, and nothing in that model fits
a city graded to street crowns by ordinance. So the post-fire ground has its own
field-builder, and it REUSES terrain_gen's meshing (`build_meshes`: the same grid,
the same derived skirt, the same mesh-versus-field refusal, the same GLB export) so
the renderer receives a ground of exactly the shape it already knows.

Inputs, all committed:

    data/datum.json
    data/terrain/epochs/<e>/terrain_spec.json     the zone table (T-1251)
    data/terrain/epochs/<e>/shoreline.geojson     the waterline (T-1250)

The field, in the spec's own words:

    land   the inverse-distance-weighted crown of `street_crowns` (graded_ground),
           plus micro relief, and falling to the water across the embankment's
           lakeward face at `earthworks[ic_row_embankment].face_slope`
    water  east of the scene line; `lake_shelf.bed_ft * (1 - exp(-d / e_fold_m))`
    conf   inferred inside the confirmed reach, reconstructed (conjectural channel)
           everywhere else and everything south of the evidence limit
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "generators") not in sys.path:
    sys.path.insert(0, str(ROOT / "generators"))

import terrain_gen as tg  # noqa: E402  (flat, generators/ is on sys.path)

np = tg.np
FT = 0.3048
CONF_INFERRED, CONF_CONJECTURAL = tg.CONF_INFERRED, tg.CONF_CONJECTURAL
PRAIRIE_HALF_BAND_M = 80.0     # the confirmed reach's width either side of the Prairie crowns

# THE APRON HAS TO OUTRUN THE AIR (L17, T-1635). The skirt's outer edge must lie past the
# distance at which the renderer's haze is total, or it shows at the horizon;
# tools/check_haze_reach.mjs holds every epoch's `skirt.margin_m` against that distance
# (2,644.9 m at HAZE_DENSITY 0.00089). terrain_gen.SKIRT_MARGIN_MIN_M, 1,500 m, predates
# T-1635, which solved the air against the 1835 apron of 2,659.84 m — the 1835 box is so
# wide that its lattice search lands far past its own floor. This box is 900 m across,
# so the 1,500 m floor would stop the search at 2,109.92 m, inside the haze. The floor
# here is the 1835 apron the air was solved against, so both epochs stand in the same
# air. It is raised in THIS process only (skirt_margin_m and build_meshes read the
# module global at call time): terrain_gen.py is hashed into the 1835 ground's
# staleness, and the 1835 apron already clears the air.
APRON_FLOOR_M = 2659.84
tg.SKIRT_MARGIN_MIN_M = max(tg.SKIRT_MARGIN_MIN_M, APRON_FLOOR_M)


def load(p: Path):
    return json.loads(p.read_text())


def build_field(spec, shore):
    g = spec["grid"]
    cell = float(g["cell_m"])
    e0, e1 = float(g["e_min_m"]), float(g["e_max_m"])
    n0, n1 = float(g["n_min_m"]), float(g["n_max_m"])
    cols = int(round((e1 - e0) / cell)) + 1
    rows = int(round((n1 - n0) / cell)) + 1
    E, N = np.meshgrid(e0 + np.arange(cols) * cell, n0 + np.arange(rows) * cell)

    # the waterline: the one run the spec names
    run_id = spec["shore_runs"][0]["id"]
    feat = next(f for f in shore["features"] if f["id"] == run_id)
    datum = load(ROOT / "data" / "datum.json")
    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]
    line = [(x - oe, y - on) for x, y in feat["geometry"]["coordinates"]]
    ns = np.array([p[1] for p in line])
    es = np.array([p[0] for p in line])
    order = np.argsort(ns)
    edge_e = np.interp(N[:, 0], ns[order], es[order])          # per row
    water = E > edge_e[:, None]
    d = tg.seg_distance(E, N, line)

    # land: the crowns, by inverse distance
    crowns = spec["street_crowns"]
    p = float(spec["graded_ground"]["power"])
    num = np.zeros(E.shape)
    den = np.zeros(E.shape)
    for c in crowns:
        r2 = (E - c["e_m"]) ** 2 + (N - c["n_m"]) ** 2
        w = 1.0 / np.maximum(r2, 1e-6) ** (p / 2.0)
        num += w * c["crown_ft"]
        den += w
    grade_ft = num / den

    mr = spec["surface_texture"]
    micro = np.zeros(E.shape)
    for wl in mr["wavelengths_m"]:
        micro += tg.value_noise(E, N, float(wl), int(mr["seed"]))
    micro *= float(mr["amplitude_ft"]) / len(mr["wavelengths_m"])

    emb = next(x for x in spec["earthworks"] if x["id"] == "ic_row_embankment")
    level_ft = grade_ft + micro
    face_m = level_ft * FT * float(emb["face_slope"])
    ramp = np.clip(d / np.maximum(face_m, 1e-6), 0.0, 1.0)
    land_ft = level_ft * ramp

    sh = spec["lake_shelf"]
    depth_ft = float(sh["bed_ft"]) * (1.0 - np.exp(-d / float(sh["e_fold_m"])))
    h_ft = np.where(water, depth_ft, land_ft)
    h_m = h_ft * FT

    # confidence: inferred only inside the confirmed reach
    ev = spec["evidence_limit"]
    reach = ev["confirmed_reach"]
    pr = [c for c in crowns if c["reading"].startswith("prairie_")]
    pr_e = np.interp(N[:, 0], sorted(c["n_m"] for c in pr),
                     [c["e_m"] for c in sorted(pr, key=lambda c: c["n_m"])])
    in_reach = ((N <= reach["n_from_m"]) & (N >= reach["n_to_m"])
                & (np.abs(E - pr_e[:, None]) <= PRAIRIE_HALF_BAND_M) & ~water)
    conf = np.where(in_reach, CONF_INFERRED, CONF_CONJECTURAL)
    conf = np.where(N < float(ev["south_of_n_m"]), CONF_CONJECTURAL, conf)

    meta = {
        "cols": cols, "rows": rows, "cell_m": cell, "origin_e": e0, "origin_n": n0,
        "box": {"e": [e0, e1], "n": [n0, n1]},
        "min_m": float(h_m.min()), "max_m": float(h_m.max()),
        "water_fraction": float(water.mean()),
        "land_min_ft": float(h_ft[~water].min()), "land_max_ft": float(h_ft[~water].max()),
    }
    return h_m, conf, water, meta


def write_heightfield(out_dir: Path, h_m, meta, spec, inputs_sha: str):
    scale = float(spec["grid"]["scale_m"])
    q = np.rint(h_m / scale).astype(np.int16)
    err = float(np.abs(q.astype(np.float64) * scale - h_m).max())
    (out_dir / "heightfield.bin").write_bytes(q.astype("<i2").tobytes(order="C"))
    doc = {
        "_doc": ("Runtime heightfield meta for terrain epoch " + spec["epoch"] + ". Row 0 is the SOUTH edge and "
                 "column 0 the WEST edge; the sample at [0][0] sits exactly on (origin_e, origin_n) in local ENU "
                 "metres from data/datum.json. Elevation in metres above the internal datum (the summer-1835 water "
                 "surface): y = raw * scale + offset. GENERATED by generators/terrain_gen_graded.py - do not "
                 "hand-edit."),
        "epoch": spec["epoch"], "spec": "terrain_spec.json", "bin": "heightfield.bin", "encoding": "int16",
        "scale": scale, "offset": 0.0, "cols": meta["cols"], "rows": meta["rows"], "cell_m": meta["cell_m"],
        "origin_e": meta["origin_e"], "origin_n": meta["origin_n"], "box_local_enu_m": meta["box"],
        "min_m": round(meta["min_m"], 4), "max_m": round(meta["max_m"], 4),
        "quantisation_error_m": round(err, 5), "water_surface_m": 0.0,
        "water_fraction": round(meta["water_fraction"], 4),
        "relief_ft": {"land_min": round(meta["land_min_ft"], 3), "land_max": round(meta["land_max_ft"], 3),
                      "channel_min": round(meta["min_m"] / FT, 3)},
        "skirt": meta["skirt"],
        "glb": {"ground": f"gltf/terrain__{spec['epoch']}.glb", "water": f"gltf/water__{spec['epoch']}.glb"},
        "inputs_sha256": inputs_sha,
    }
    (out_dir / "heightfield.json").write_text(json.dumps(doc, indent=1) + "\n")
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", default="e1871_postfire")
    ap.add_argument("--glb", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="re-derive the heightfield in memory and compare it with the committed bytes")
    ap.add_argument("--decimate-deg", type=float, default=0.03)
    ap.add_argument("--out", default=str(ROOT / "assets" / "gltf"))
    args = ap.parse_args(tg.argv_after_ddash())
    if np is None:
        print("REFUSING: numpy is required")
        return 2
    ep_dir = ROOT / "data" / "terrain" / "epochs" / args.epoch
    spec = load(ep_dir / "terrain_spec.json")
    shore = load(ep_dir / "shoreline.geojson")
    h_m, conf, water, meta = build_field(spec, shore)
    g = spec["grid"]
    margin, k = tg.skirt_margin_m(max(g["e_max_m"] - g["e_min_m"], g["n_max_m"] - g["n_min_m"]), g["cell_m"])
    meta["skirt"] = {"_doc": "The apron outside the modelled box; see generators/terrain_gen.skirt_terminations. "
                             "No landform here ends inside it, so it carries every boundary vertex outward at its own height.",
                     "margin_m": round(margin, 6), "position_rung_m": round(g["cell_m"] / k, 9), "terminations": {}}
    import terrain_inputs  # noqa: PLC0415
    sha = terrain_inputs.terrain_inputs_sha(ep_dir)
    if args.check:
        import tempfile  # noqa: PLC0415
        with tempfile.TemporaryDirectory() as tmp:
            write_heightfield(Path(tmp), h_m, meta, spec, sha)
            same = all((Path(tmp) / n).read_bytes() == (ep_dir / n).read_bytes()
                       for n in ("heightfield.json", "heightfield.bin"))
        print("OK the e1871_postfire heightfield re-derives byte for byte from its spec and scene line"
              if same else "FAIL the committed e1871_postfire heightfield is not what its spec and scene line derive; "
              "re-run generators/terrain_gen_graded.py and re-bake the meshes under Blender with --glb")
        return 0 if same else 1
    doc = write_heightfield(ep_dir, h_m, meta, spec, sha)
    print(f"grid {doc['cols']}x{doc['rows']} @ {doc['cell_m']} m; land {doc['relief_ft']['land_min']}..{doc['relief_ft']['land_max']} ft; "
          f"water {100 * doc['water_fraction']:.1f}%; quantisation {doc['quantisation_error_m'] * 1000:.2f} mm")
    if not args.glb:
        return 0
    if not tg.HAVE_BPY:
        print("--glb needs Blender")
        return 2
    built = tg.build_meshes(h_m, conf, spec, args.epoch, Path(args.out), args.decimate_deg, {})
    import bpy  # noqa: PLC0415
    from mesh_inputs import SCHEME  # noqa: PLC0415
    manifest_path = ROOT / "assets" / "manifest.json"
    manifest = load(manifest_path)
    manifest["inputs_scheme"] = SCHEME
    for b in built:
        pth = b["path"]
        manifest["assets"][pth.name] = {
            "kind": "generated", "generator": "generators/terrain_gen_graded.py", "terrain_epoch": args.epoch,
            "layer": "water" if pth.name.startswith("water__") else "ground", "inputs_sha256": sha,
            "bytes": pth.stat().st_size, "triangles": b["tris"],
            **({"mesh_vs_heightfield": b["fit"]} if "fit" in b else {}), "baked_ao": False,
        }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"manifest updated: {len(built)} terrain asset(s) (blender {bpy.app.version_string})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
