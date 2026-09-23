#!/usr/bin/env python3
"""Build honest, pure-Python placeholder GLBs for all inferred anonymous infill.

These are review massings, not substitutes for the repository's Blender archetype
bakes.  The glTF asset declares ``asset.extras.placeholder = true`` so the loader and
provenance card flag that fact from the file itself.  Geometry is still generated
entirely from the committed structure record and follows the normal axis/origin,
identity and ``_CONFIDENCE`` contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STRUCTURES = ROOT / "data" / "structures"
MASTER = ROOT / "assets" / "gltf"
WEB = ROOT / "assets" / "web"
MANIFEST = ROOT / "assets" / "manifest.json"
PREFIX = "recon_1835_"

sys.path.insert(0, str(ROOT / "generators"))

from common import materials  # noqa: E402

# THIS GENERATOR'S PALETTE IS NOW THE TOWN'S (T-0007). The six wall finishes and the
# four roof conditions below were written here and read nowhere else, which is
# docs/RESEARCH/materials.md finding 5: 27 % of the town was painted by a generator
# sharing not one colour and not one roughness with the other 73 %. They have moved
# to `common/materials.py` — the sheet — where the nine Blender archetypes now read
# them too, and these names stay as the local view of it. The VALUES are unchanged to
# the last bit, deliberately: 94 committed GLBs are gated on their exact bytes, and
# this parcel converges the two palettes by moving the archetypes onto the records'
# vocabulary rather than by moving the vocabulary.
WALL_COLOURS = {k: materials.FINISHES[k].rgba
                for k in ("fresh_timber", "weathered_timber", "whitewash",
                          "ochre", "red_oxide", "mixed_patch")}
ROOF_COLOURS = {k: v.rgba for k, v in materials.ROOF_CONDITIONS.items()}

# AND THE OPENING FOLLOWS THEM (T-0126). `placeholder_opening_dark` was the fourth of
# the four values materials.md §2.3 measured for "what you see through an opening",
# and the only one of the four that was GREEN — #2D3D33, a colour nothing in this
# repository argues for and nothing in a Chicago building is. It is pointed at the
# sheet's `DARK` row with the rest of them. NOTE WHAT THIS DOES AND DOES NOT CHANGE:
# `--check` reports "0 flagged placeholder GLBs; 226 superseded by a canonical bake",
# so this generator paints nothing that ships and the edit repaints no building. It
# is here so the divergence cannot walk back in the day a placeholder is emitted
# again, and §2.3's count of four is corrected to the three that were real.


def load(path: Path):
    return json.loads(path.read_text())


def normal(a, b, c):
    ux, uy, uz = (b[i] - a[i] for i in range(3))
    vx, vy, vz = (c[i] - a[i] for i in range(3))
    x, y, z = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(x*x + y*y + z*z) or 1.0
    return (x/length, y/length, z/length)


def tri(group: list, a, b, c):
    n = normal(a, b, c)
    group.extend((tuple(a) + n + (1.0,), tuple(b) + n + (1.0,), tuple(c) + n + (1.0,)))


def quad(group: list, a, b, c, d):
    tri(group, a, b, c)
    tri(group, a, c, d)


def box(group: list, x0, x1, y0, y1, z0, z1):
    p = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
         (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    for face in ((0,3,2,1),(4,5,6,7),(0,4,7,3),(1,2,6,5),(3,7,6,2),(0,1,5,4)):
        quad(group, *(p[i] for i in face))


def record_geometry(record: dict) -> tuple[dict[str, list], list[dict]]:
    phase = record["phases"][0]
    poly = phase["footprint"]["polygon"]
    w = max(p[0] for p in poly) - min(p[0] for p in poly)
    d = max(p[1] for p in poly) - min(p[1] for p in poly)
    form = {k: v["value"] for k, v in phase["form"].items()}
    stories = float(form.get("stories", 1))
    wall_h = float(form.get("wall_height_m", 2.6))
    roof_type = form.get("roof_type", "gable")
    pitch = math.radians(float(form.get("roof_pitch_deg", 34)))
    meta = record["reconstruction"]
    groups = {"wall": [], "roof": [], "opening": [], "chimney": []}

    box(groups["wall"], 0, w, 0, wall_h, -d, 0)
    if roof_type == "shed":
        rise = min(wall_h * .72, math.tan(pitch) * d)
        quad(groups["roof"], (-.12,wall_h, .12), (w+.12,wall_h,.12),
             (w+.12,wall_h+rise,-d-.12), (-.12,wall_h+rise,-d-.12))
        # AND THE TWO ENDS THE SLOPE LEAVES OPEN (T-0061). A shed roof rises from
        # the front wall to the back, so each side wall finishes as a right
        # triangle between the two — and without them a visitor sees straight
        # through the building to the sky under the slope. The gable branch below
        # has always filled its ends; this branch drew the slope and stopped, so
        # every placeholder carrying `roof_type: shed` stood open. Wound the same
        # way round as the gable's own end fills, and put in the `wall` group
        # because that is what they are: the top of the wall, not roof covering,
        # which also keeps them off the roof material the record grades.
        tri(groups["wall"], (0,wall_h,0), (0,wall_h+rise,-d), (0,wall_h,-d))
        tri(groups["wall"], (w,wall_h,-d), (w,wall_h+rise,-d), (w,wall_h,0))
    else:
        rise = min(wall_h * .85, math.tan(pitch) * d / 2)
        ridge = wall_h + rise
        quad(groups["roof"], (-.14,wall_h,.12), (w+.14,wall_h,.12),
             (w+.14,ridge,-d/2), (-.14,ridge,-d/2))
        quad(groups["roof"], (-.14,ridge,-d/2), (w+.14,ridge,-d/2),
             (w+.14,wall_h,-d-.12), (-.14,wall_h,-d-.12))
        tri(groups["wall"], (0,wall_h,0), (0,ridge,-d/2), (0,wall_h,-d))
        tri(groups["wall"], (w,wall_h,-d), (w,ridge,-d/2), (w,wall_h,0))

    # One readable front door and restrained dark openings. This is intentionally
    # type-level massing; the popup says no opening belongs to an observed elevation.
    door_w = min(1.25, max(.68, w * .18))
    door_h = min(2.25, wall_h * .78)
    dx = w * .5 - door_w * .5
    quad(groups["opening"], (dx,.04,-d-.018), (dx+door_w,.04,-d-.018),
         (dx+door_w,door_h,-d-.018), (dx,door_h,-d-.018))
    bays = max(1, min(5, int(form.get("bays", form.get("shopfront_bays", round(w / 2.2))))))
    for level in range(max(1, int(stories))):
        sill = .78 + level * 2.42
        if sill + 1.0 > wall_h - .16:
            continue
        for i in range(bays):
            cx = (i + .5) * w / bays
            if level == 0 and abs(cx - w*.5) < door_w:
                continue
            ww = min(.74, w / (bays * 2.1))
            quad(groups["opening"], (cx-ww/2,sill,-d-.021), (cx+ww/2,sill,-d-.021),
                 (cx+ww/2,sill+1.0,-d-.021), (cx-ww/2,sill+1.0,-d-.021))

    chimneys = int(form.get("chimneys", 0))
    if chimneys:
        top = wall_h + (math.tan(pitch) * d / 2 if roof_type == "gable" else .8) + .65
        for i in range(chimneys):
            cx = w * (.35 if i == 0 else .68)
            box(groups["chimney"], cx-.18, cx+.18, wall_h+.35, top, -d*.56, -d*.45)

    # AND THE CHIMNEY IS THE LAST OF THEM (T-0138). `placeholder_chimney_brick` was
    # the one row left holding a local literal — #89503F, (0.537, 0.314, 0.247) linear,
    # written here and argued nowhere — while T-0008 gave the 112 brick stacks on the
    # archetype buildings the sheet's BRICK at (0.45, 0.23, 0.17). The two are
    # about 20 % apart in linear red and they stand on the same streets, which is
    # docs/RESEARCH/materials.md §4 finding 4 in one line: *an atlas that textures one
    # path and not the other splits the town visibly in half.*
    #
    # WHICH VALUE SURVIVES, and it is not a coin toss. #89503F has no witness behind
    # it: no source record, no note, nothing in this repository that argues for the
    # number. BRICK — named `CHIMNEY_BRICK` until T-0332 — is `frame_tavern`'s
    # committed BRICK_RGBA, read off the Petford watercolour of the Sauganash
    # (T-0092, L154) — the ONE coloured witness
    # to any Chicago chimney — and generalised to the town's other framed stacks on
    # the town's own warrant, Blodgett's North Side brick-yard from the spring of 1833.
    # An `inferred` value with a source beats an undocumented literal, so the literal
    # goes and nothing about the brick is re-argued here.
    #
    # THE SELECTOR, not the row, because the sheet owns the choice as well as the
    # colour: this generator builds ONE kind of stack — a box inside the footprint
    # depth, rising through the roof — which is `chimney_finish`'s `interior` case, the
    # framed house's masonry flue. It is asked the question rather than told the
    # answer, so a placeholder cannot drift from the archetypes again by being pointed
    # at a row that has since moved. (What this does NOT do is give a log dwelling the
    # exterior-gable stick-and-clay stack its archetype builds: the placeholder's
    # GEOMETRY puts every stack inside the roof, so claiming the daub here would paint
    # a fabric onto the wrong silhouette. That is the placeholder's massing, not its
    # palette, and it is out of this parcel.)
    #
    # NOTHING REPAINTS, AND THE TICKET EXPECTED OTHERWISE. T-0138 was written against
    # "90 committed masters" and asked for them, their derivatives and the banked
    # passthrough set to be regenerated in the same commit. There are none left:
    # `--check` reports **0 flagged placeholder GLBs; 230 superseded by a canonical
    # bake**, and no committed GLB in `assets/` carries the string
    # `placeholder_chimney_brick`. So this is T-0126's shape exactly — the divergence
    # is closed at the source so it cannot walk back in the day a placeholder is
    # emitted again, and no building changes colour today.
    _chimney = materials.chimney_finish("interior")

    # `mats`, not `materials`: the module of that name is the sheet these values now
    # come from, and shadowing it here would silently reintroduce the local palette.
    mats = [
        {"name": f"placeholder_wall_{meta['finish_key']}", "pbrMetallicRoughness": {"baseColorFactor": list(WALL_COLOURS[meta["finish_key"]]), "metallicFactor": 0, "roughnessFactor": .86}, "doubleSided": True},
        {"name": f"placeholder_roof_{meta['roof_condition']}", "pbrMetallicRoughness": {"baseColorFactor": list(ROOF_COLOURS[meta["roof_condition"]]), "metallicFactor": 0, "roughnessFactor": .9}, "doubleSided": True},
        {"name": "placeholder_opening_dark", "pbrMetallicRoughness": {"baseColorFactor": list(materials.DARK.rgba), "metallicFactor": 0, "roughnessFactor": materials.DARK.roughness}, "doubleSided": True},
        {"name": f"placeholder_{_chimney.key}", "pbrMetallicRoughness": {"baseColorFactor": list(_chimney.rgba), "metallicFactor": 0, "roughnessFactor": _chimney.roughness}, "doubleSided": True},
    ]
    return groups, mats


def glb_for(record: dict) -> bytes:
    groups, mats = record_geometry(record)
    blob = bytearray()
    views, accessors, primitives = [], [], []
    material_index = {name: i for i, name in enumerate(("wall", "roof", "opening", "chimney"))}

    def add_accessor(values: list[float], kind: str, count: int, mins=None, maxs=None):
        offset = len(blob)
        blob.extend(struct.pack(f"<{len(values)}f", *values))
        view = len(views)
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(values)*4})
        acc = {"bufferView": view, "componentType": 5126, "count": count, "type": kind}
        if mins is not None: acc["min"] = mins
        if maxs is not None: acc["max"] = maxs
        accessors.append(acc)
        return len(accessors)-1

    for name, verts in groups.items():
        if not verts:
            continue
        positions = [c for v in verts for c in v[:3]]
        normals = [c for v in verts for c in v[3:6]]
        conf = [v[6] for v in verts]
        xs, ys, zs = positions[0::3], positions[1::3], positions[2::3]
        p = add_accessor(positions, "VEC3", len(verts), [min(xs),min(ys),min(zs)], [max(xs),max(ys),max(zs)])
        n = add_accessor(normals, "VEC3", len(verts))
        c = add_accessor(conf, "SCALAR", len(verts), [1.0], [1.0])
        primitives.append({"attributes": {"POSITION": p, "NORMAL": n, "_CONFIDENCE": c},
                           "material": material_index[name], "mode": 4})

    sid, phase = record["id"], record["phases"][0]["id"]
    doc = {
        "asset": {"version": "2.0", "generator": "inferred_placeholder.py",
                  "extras": {"placeholder": True, "generated_from": f"data/structures/{sid}.json",
                             "reason": "Review massing pending canonical archetype bake"}},
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [{"name": f"{sid}__{phase}", "mesh": 0,
                   "extras": {"structure_id": sid, "phase_id": phase, "scene_ids": ["1835"]}}],
        "meshes": [{"name": f"{sid}__{phase}", "primitives": primitives}],
        "materials": mats, "buffers": [{"byteLength": len(blob)}],
        "bufferViews": views, "accessors": accessors,
    }
    js = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    blob += b"\0" * ((4 - len(blob) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(blob)
    return (struct.pack("<III", 0x46546C67, 2, total)
            + struct.pack("<II", len(js), 0x4E4F534A) + js
            + struct.pack("<II", len(blob), 0x004E4942) + blob)


def expected() -> tuple[dict[str, bytes], dict[str, dict]]:
    files, entries = {}, {}
    for path in sorted(STRUCTURES.glob(f"{PREFIX}*.json")):
        record = load(path)
        phase = record["phases"][0]["id"]
        name = f"{record['id']}__{phase}.glb"
        data = glb_for(record)
        files[name] = data
        entries[name] = {
            "archetype": record["archetype"], "bytes": len(data),
            "generator": "generators/inferred_placeholder.py",
            "inputs_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "kind": "placeholder", "phase_id": phase, "placeholder": True,
            "source_record": f"data/structures/{path.name}",
        }
    return files, entries


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files, entries = expected()
    manifest = load(MANIFEST)
    drift = []
    superseded = 0
    for name, data in files.items():
        # The build path stands aside for a superseded asset for exactly the reason
        # the --check path below does, and it did not, which made this command a
        # quiet way to destroy a night's Blender work: run once for a new record and
        # it also rewrote all 128 already-baked ones with placeholder massing —
        # 113 KB of canonical archetype back down to a 4.9 KB flagged box — and
        # stamped their manifest entries `kind: placeholder` so nothing downstream
        # could tell. Every gate stayed green, because a placeholder that matches
        # its record is what the gates are checking for. Asymmetry between a check
        # and the build it checks is the whole bug; the two now ask the same question.
        entry = manifest["assets"].get(name)
        superseded_here = entry is not None and entry.get("kind") != "placeholder"

        if not args.check:
            if superseded_here:
                superseded += 1
                continue
            for folder in (MASTER, WEB):
                (folder / name).write_bytes(data)
            manifest["assets"][name] = entries[name]
            continue

        # A placeholder is a placeholder only until the canonical archetype bake
        # produces the same asset.  generators/build.py writes that same filename
        # and stamps the manifest entry `kind: generated`; from that moment this
        # generator's bytes are the OLD answer, and demanding them back would
        # forbid the upgrade the bake exists to perform.  Hand off to the ordinary
        # staleness gate in tools/validate.py, which hashes a generated asset
        # against its own recorded inputs.
        if superseded_here:
            superseded += 1
            continue

        master = MASTER / name
        if not master.exists() or master.read_bytes() != data:
            drift.append(f"{master.relative_to(ROOT)} is missing or stale")
        # The web tree is a DERIVATIVE, not a second copy.  tools/bake.sh runs
        # gltf-transform over it when the optimiser is available, so requiring
        # byte-equality with the master asserts that compression never happens —
        # which is why the nightly content build was red wherever npx could reach
        # the network and green wherever it could not.  Require it to be there.
        web = WEB / name
        if not web.exists():
            drift.append(f"{web.relative_to(ROOT)} is missing")
        if entry != entries[name]:
            drift.append(f"assets/manifest.json entry for {name} is missing or stale")
    if not args.check:
        MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    if drift:
        print("INFERRED PLACEHOLDER DRIFT")
        for item in drift:
            print(f"  - {item}")
        return 1
    tail = f"; {superseded} superseded by a canonical bake" if superseded else ""
    print(f"{'verified' if args.check else 'built'} {len(files) - superseded}"
          f" flagged placeholder GLBs{tail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
