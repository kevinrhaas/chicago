#!/usr/bin/env python3
"""Does the file the site ships still describe the building the repository baked?

ROADMAP K36(a). The geometry a visitor downloads reaches them along four links:

    data/  ->  assets/gltf/  ->  assets/web/  ->  site/chicago/4d/assets/web/

Link 1 is gated: `validate.py --stale` recomputes every master's input hash, so a
record edited into a different building fails. Link 3 is gated: `check_published.mjs`
asserts every published file is byte-identical to its source. **Link 2 was gated by
nothing at all** — no committed number, no hash, no assertion tied a shipped
derivative to the master it was compressed from — and it is the link with the moving
parts: `tools/bake.sh` runs two `gltf-transform` passes over every master, and its own
comments record what has already gone wrong in there:

  * *"a bug that collapsed every building to a two-metre box shipped past a fully
    green gate — twice"*;
  * `--texture-compress ktx2` *"silently turned every derivative into an uncompressed
    copy of its master, in every environment, since this step was written"*;
  * `optimize` runs mesh simplification by default, which on this dataset is damage
    rather than optimisation, so the bake passes `--simplify false` — a flag, in a
    script, with nothing asserting the outcome.

Every one of those was found by a person reading the script. This reads the bytes.

    tools/measure_web_derivatives.py                 print the census
    tools/measure_web_derivatives.py --gate          exit 1 on a divergence
    tools/measure_web_derivatives.py --self-test     break each assertion, in memory
    tools/measure_web_derivatives.py --write-baseline   bank a repair (deliberate act)

NO BLENDER, NO DECODER, NO NETWORK. Only the glTF JSON chunk is read. Positions in a
shipped derivative are EXT_meshopt_compression payloads this project cannot decode
here — but every claim below is answerable from the JSON alone, because the glTF spec
requires POSITION accessors to carry `min`/`max`, and a quantised file carries its
dequantisation in the node's own TRS. Counting triangles, composing node transforms
and comparing material tables costs about a second for all 334 assets.

## The assertions

1.  **Bijection** (absolute). Every master has a derivative and every derivative has a
    master. A derivative whose master was deleted is a building on the site that the
    dataset no longer describes.

2.  **Triangle count** (absolute). Equal, per asset. This is the assertion behind
    `--simplify false`: the flag says what the bake asks for, this says what arrived.

3.  **Identity** (absolute). Node names, node `extras` — `structure_id`, `phase_id` —
    and mesh names survive. These are the join key the sidecars and the provenance
    card use; a derivative that lost them is anonymous geometry.

4.  **The contract's attributes** (absolute). `docs/GLB-CONTRACT.md` names POSITION,
    NORMAL and `_CONFIDENCE`; whichever the master carries, the shipped file carries.
    `_CONFIDENCE` is how a visitor is told which parts we made up, and it travels in
    the mesh rather than in a sidecar. TEXCOORD_0 is deliberately NOT in this list:
    the master's UVs are unused on an untextured asset and `optimize`'s prune pass is
    right to drop them. That is reported, not gated.

5.  **The building is where it was** (absolute). The world-space bounding box of the
    two files must agree to within FOUR RUNGS of the asset's own widest extent, where
    a rung is `extent / 65535` — the 16-bit lattice a normalised SHORT position is
    stored on, whatever bit depth the bake asked the quantiser for. The bound is a
    lattice, not a millimetre count, because the assets differ in size by three orders
    of magnitude: measured 2026-08-16, the worst was 2.63 rungs (0.107 mm on a 2.7 m
    shed) and the terrain's 82.8 mm is 1.08 rungs of its own 5,020 m box — the same
    quantity R-W6 committed as a 76.6 mm lattice. A building collapsed to a two-metre
    box is thousands of rungs, not four.

6.  **The derivative is never bigger than the master** (absolute, K37). `meshopt`
    writes a compression header, a buffer-view table and an index buffer, and on a
    small enough mesh those cost more than they save: the 90 flagged placeholders
    come out **+107,328 bytes (+20.6 %)** when this step is run over them, 88 of the
    90 growing. K36(a) read that as an anomaly and K36(b)'s control read it as a
    non-reproduction; both were describing the same thing and neither was a rule.
    The rule is a measurement, and it is **not** a property of the asset's kind —
    three assets that have always been compressed here shipped *larger* than their
    masters until this assertion was written, and two of the ninety placeholders
    compress 9.3 % *smaller*. `tools/web_derivatives.sh` now keeps whichever file is
    smaller, per asset, and this says what arrived. **The two epoch meshes are
    excluded by name**: their bit depth is a geometric decision (R-W6, and the ground
    and waterline are what R-BUG3c, R-BUG4 and R-M1a measure against), and `water__` is
    +744 bytes under this rule — recorded, not silently applied. That depth is asserted
    on the shipped bytes by `tools/measure_terrain_fit.mjs --gate` (T-0151), not here:
    this gate compares triangles, node identity, materials and a bounding box within four
    rungs, and **a bit-depth change moves none of them** — which is how a 14-bit ground
    shipped, and later a 16-bit one arrived, with every assertion on this page green.

7.  **Material identity** (RATCHET, `tools/web_derivative_baseline.json`). The shipped
    file should resolve to the same material NAMES and base COLOURS as its master and
    should gain no texture the master does not have. 38 of 334 assets failed this when
    the assertion was written — `optimize`'s palette pass folded their five or six named
    materials — `log`, `chinking`, `board`, `roof`, … — into a single
    `PaletteMaterial001` carrying two generated PNGs. **K36(b) repaired all 38 and
    rebanked the baseline empty, so it is 334 of 334 today and the ratchet holds
    nothing.** It stays a ratchet rather than an absolute because the repair moves 334
    binary files and a permanently red dev gate would block every unrelated parcel
    behind it. A new offender fails. A repaired one fails too, and says to bank it.

8.  **The passthrough set is decided, not discovered** (absolute in BOTH directions,
    `tools/web_derivative_baseline.json`, K38). 93 of the 334 derivatives are
    byte-identical to their masters, because compressing them makes them bigger and
    `tools/web_derivatives.sh` keeps the smaller file (K37). Every one of those is a
    decision. **A 94th is not** — and until this assertion existed, nothing could tell
    the two apart, because a master copied over its own derivative satisfies assertions
    1 through 7 by construction: same triangles, same node identity, same attributes,
    zero rungs of bounding-box drift, identical materials, and a byte count that is
    equal rather than larger. Measured (K38): two masters copied through by
    `tools/publish.sh` added **1,212,760 bytes** to the payload and `tools/check.sh`
    printed **CHECK PASS**. `assets/web/` has three writers — this step,
    `generators/inferred_placeholder.py` and, until K38, `tools/publish.sh` — and the
    gate on a directory's contents is a gate on its last writer only. So the set is
    banked by name and both directions fail: an unbanked passthrough is a writer nobody
    watched, and a banked one that is now compressed is a repair that has to be recorded
    with `--write-baseline` rather than discovered.

9.  **The derivative records the master it was made from** (absolute in BOTH
    directions, `assets/manifest.web.json`, K39). Assertions 1-8 compare a derivative
    to *whatever master sits beside it today*. None of them asks whether that is the
    master it came from, and nothing else did either: K38 left `tools/publish.sh`
    refusing on **mtime**, and measured that on a fresh clone `git checkout`'s own
    write order makes 334 of 334 masters older than their derivatives — so the scan is
    silent on exactly the tree a steward run starts from. The gap that survived is
    narrow and named. A master rebuilt into a *different building* fails assertions
    2-5; a master rebuilt into the **same** geometry with different `_CONFIDENCE`
    values fails nothing at all. That is the failure `publish.sh`'s original comment
    was written about — *"a rebuilt building kept rendering with its old confidence
    values"* — and `_CONFIDENCE` is how a visitor is told which parts we made up, so a
    stale one is a provenance fault wearing a rendering fault's clothes.

    `tools/web_derivatives.sh` knows exactly which master it compressed. It now writes
    `name -> sha256(master)` as it produces each derivative, into a sidecar that
    travels with the artefact, and this asserts it: a derivative whose recorded hash is
    not its master's hash today is stale ABSOLUTELY, whatever the timestamps say, and a
    derivative with no record at all is a file no step in this repository claims to
    have produced. The remedy in both directions is a REGENERATION, never an edit of
    the record — which is why the record has no `--write` affordance here on purpose. A
    hash map you can rewrite to make a gate green is a hash map that says nothing.

    **What it does not answer, stated because measuring it is what opened K40.** The
    hash names the MASTER, not the STEP. A derivative produced by an older flag set
    from this same master carries the right hash and still reproduces nothing:
    measured on a 20-asset spread sample, **14 of 20 shipped derivatives cannot be
    reproduced by `tools/web_derivatives.sh` as it stands today** — they carry FEWER
    vertices than their masters, because the palette pass K36(b) turned off was welding
    them as a side effect nobody had measured. Assertion 9 is silent on all 14, and
    correctly so: their master is the right master.
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
MASTERS = ROOT / "assets" / "gltf"
SHIPPED = ROOT / "assets" / "web"
BASELINE = ROOT / "tools" / "web_derivative_baseline.json"

# K39. Written by tools/web_derivatives.sh as it produces each derivative, and by
# nothing else — not by this file, which only reads it.
#
# It sits beside assets/manifest.json deliberately: the two are the two links of the
# same chain. The manifest records data -> master (an inputs hash per asset, written by
# the Blender build); this records master -> derivative (the master's own hash, written
# by the step after it). Its lifecycle is the derivative's — same producer, same run,
# same commit. tools/web_derivative_baseline.json has the opposite lifecycle, a person
# banking a decision by hand with --write-baseline, and a map that changes on every
# bake does not belong in it.
RECORD = ROOT / "assets" / "manifest.web.json"

# A normalised position component is stored in a SHORT and dequantised by the node's
# own scale, so the finest step any shipped vertex can land on is the asset's widest
# extent over 65535 — regardless of the bit depth the bake asked for, which only makes
# the step coarser. Four of them is the bound; see the module docstring.
RUNGS = 65535
RUNG_TOLERANCE = 4.0

# Attributes docs/GLB-CONTRACT.md names. TEXCOORD_0 is not one of them.
CONTRACT_ATTRIBUTES = ("POSITION", "NORMAL", "_CONFIDENCE")

# The two epoch-scale meshes, excluded from assertion 6 by name rather than by a
# size threshold — a threshold would be a second unmeasured rule. Their derivative's
# bit depth is set independently (EPOCH_QUANT_BITS) because it is a geometric
# decision about the surface the ground gates measure against. That depth is
# asserted on the shipped bytes by tools/measure_terrain_fit.mjs --gate (T-0151),
# which is the assertion whose absence let a 14-bit ground ship with every gate
# here green. See the docstring.
EPOCH_PREFIXES = ("terrain__", "water__")

# glTF component types that carry a normalised integer, and their divisor.
NORMALISED = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}


# ---------------------------------------------------------------- reading the file

def glb_json(path: Path) -> dict:
    """The JSON chunk of a .glb. Never touches the binary chunk."""
    raw = path.read_bytes()
    if raw[:4] != b"glTF":
        raise ValueError(f"{path} is not a binary glTF")
    length, kind = struct.unpack_from("<I4s", raw, 12)
    if kind != b"JSON":
        raise ValueError(f"{path}: first chunk is {kind!r}, not JSON")
    return json.loads(raw[20:20 + length])


def node_matrix(node: dict) -> list[list[float]]:
    """The node's local transform as a 3x4 row-major matrix."""
    if "matrix" in node:
        m = node["matrix"]  # column-major, per the spec
        return [[m[0], m[4], m[8], m[12]],
                [m[1], m[5], m[9], m[13]],
                [m[2], m[6], m[10], m[14]]]
    tx, ty, tz = node.get("translation", [0.0, 0.0, 0.0])
    x, y, z, w = node.get("rotation", [0.0, 0.0, 0.0, 1.0])
    sx, sy, sz = node.get("scale", [1.0, 1.0, 1.0])
    rot = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
           [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
           [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    scale = (sx, sy, sz)
    trans = (tx, ty, tz)
    return [[rot[i][0] * scale[0], rot[i][1] * scale[1], rot[i][2] * scale[2], trans[i]]
            for i in range(3)]


def compose(parent, child):
    if parent is None:
        return child
    out = []
    for i in range(3):
        row = [sum(parent[i][k] * child[k][j] for k in range(3)) for j in range(3)]
        row.append(sum(parent[i][k] * child[k][3] for k in range(3)) + parent[i][3])
        out.append(row)
    return out


def transform(matrix, point):
    return [sum(matrix[i][k] * point[k] for k in range(3)) + matrix[i][3] for i in range(3)]


def world_bbox(doc: dict):
    """The scene's world-space bounding box, from accessor min/max alone.

    Dequantisation is the node's business in a meshopt file — the accessor holds
    normalised integers and the node holds the scale that puts them back in metres —
    so composing the hierarchy is what makes the two trees comparable at all.
    """
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    nodes = doc.get("nodes", [])
    meshes = doc.get("meshes", [])
    accessors = doc.get("accessors", [])

    def walk(index: int, parent):
        node = nodes[index]
        matrix = compose(parent, node_matrix(node))
        if "mesh" in node:
            for prim in meshes[node["mesh"]].get("primitives", []):
                pos = prim.get("attributes", {}).get("POSITION")
                if pos is None:
                    continue
                acc = accessors[pos]
                if "min" not in acc or "max" not in acc:
                    continue
                divisor = NORMALISED[acc["componentType"]] if acc.get("normalized") else 1.0
                lows = [v / divisor for v in acc["min"]]
                highs = [v / divisor for v in acc["max"]]
                for cx in (lows[0], highs[0]):
                    for cy in (lows[1], highs[1]):
                        for cz in (lows[2], highs[2]):
                            p = transform(matrix, [cx, cy, cz])
                            for k in range(3):
                                lo[k] = min(lo[k], p[k])
                                hi[k] = max(hi[k], p[k])
        for child in node.get("children", []):
            walk(child, matrix)

    scenes = doc.get("scenes", [])
    roots = scenes[doc.get("scene", 0)].get("nodes", []) if scenes else range(len(nodes))
    for root in roots:
        walk(root, None)
    if lo[0] is math.inf:
        return None, None
    return lo, hi


def triangles(doc: dict) -> int:
    total = 0
    accessors = doc.get("accessors", [])
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            if prim.get("mode", 4) != 4:
                continue
            if "indices" in prim:
                total += accessors[prim["indices"]]["count"] // 3
            else:
                total += accessors[prim["attributes"]["POSITION"]]["count"] // 3
    return total


def identity(doc: dict) -> dict:
    return {
        "nodes": [n.get("name") for n in doc.get("nodes", [])],
        "extras": [n.get("extras") for n in doc.get("nodes", [])],
        "meshes": [m.get("name") for m in doc.get("meshes", [])],
    }


def attributes(doc: dict) -> set:
    return {key
            for mesh in doc.get("meshes", [])
            for prim in mesh.get("primitives", [])
            for key in prim.get("attributes", {})}


def materials(doc: dict) -> dict:
    names, colours = set(), set()
    for mat in doc.get("materials", []):
        if mat.get("name"):
            names.add(mat["name"])
        factor = mat.get("pbrMetallicRoughness", {}).get("baseColorFactor")
        if factor:
            colours.add(tuple(round(c, 6) for c in factor))
    return {"names": names, "colours": colours, "textures": len(doc.get("textures", []))}


# ---------------------------------------------------------------- the measurement

def measure() -> dict:
    master_files = {p.name: p for p in sorted(MASTERS.glob("*.glb"))}
    shipped_files = {p.name: p for p in sorted(SHIPPED.glob("*.glb"))}

    record = load_record()

    rows = []
    for name in sorted(set(master_files) & set(shipped_files)):
        a = glb_json(master_files[name])
        b = glb_json(shipped_files[name])
        alo, ahi = world_bbox(a)
        blo, bhi = world_bbox(b)
        if alo is None or blo is None:
            drift, extent = None, 0.0
        else:
            drift = max(max(abs(alo[i] - blo[i]), abs(ahi[i] - bhi[i])) for i in range(3))
            extent = max(ahi[i] - alo[i] for i in range(3))
        ma, mb = materials(a), materials(b)
        master_bytes = master_files[name].stat().st_size
        shipped_bytes = shipped_files[name].stat().st_size
        rows.append({
            "name": name,
            "triangles": (triangles(a), triangles(b)),
            "identity_master": identity(a),
            "identity_shipped": identity(b),
            "attributes_lost": sorted(attributes(a) - attributes(b)),
            "attributes_gained": sorted(attributes(b) - attributes(a)),
            "bbox_drift_m": drift,
            "extent_m": extent,
            "rungs": (drift / extent * RUNGS) if (drift is not None and extent) else 0.0,
            "names_lost": sorted(ma["names"] - mb["names"]),
            "colours_lost": len(ma["colours"] - mb["colours"]),
            "master_materials": len(a.get("materials", [])),
            "shipped_materials": len(b.get("materials", [])),
            "textures_master": ma["textures"],
            "textures_shipped": mb["textures"],
            "bytes": (master_bytes, shipped_bytes),
            "uncompressed_copy": master_files[name].read_bytes()
                                 == shipped_files[name].read_bytes(),
            "master_sha256": hashlib.sha256(master_files[name].read_bytes()).hexdigest(),
        })
    return {
        "rows": rows,
        "master_only": sorted(set(master_files) - set(shipped_files)),
        "shipped_only": sorted(set(shipped_files) - set(master_files)),
        "record": record,
    }


def material_fault(row: dict) -> dict | None:
    """The shipped file's material table does not resolve to the master's."""
    if not row["names_lost"] and not row["colours_lost"] \
            and row["textures_shipped"] <= row["textures_master"]:
        return None
    return {
        "master_materials": row["master_materials"],
        "shipped_materials": row["shipped_materials"],
        "names_lost": row["names_lost"],
        "colours_lost": row["colours_lost"],
        "textures_gained": row["textures_shipped"] - row["textures_master"],
    }


# ---------------------------------------------------------------- the assertions

def assertions(result: dict, baseline: dict) -> list[str]:
    problems = []
    for name in result["master_only"]:
        problems.append(f"assets/gltf/{name} has no derivative in assets/web — the site "
                        f"cannot ship a building the bake did not compress")
    for name in result["shipped_only"]:
        problems.append(f"assets/web/{name} has no master in assets/gltf — the site ships "
                        f"geometry the dataset no longer describes")

    banked = baseline.get("material_identity", {})
    seen = set()
    for row in result["rows"]:
        name = row["name"]
        ta, tb = row["triangles"]
        if ta != tb:
            problems.append(f"{name}: the master has {ta} triangles and the shipped file has "
                            f"{tb} — the publish path changed the geometry, which "
                            f"tools/bake.sh's --simplify false says it must not")
        if row["identity_master"] != row["identity_shipped"]:
            problems.append(f"{name}: node names, node extras or mesh names differ between the "
                            f"master and the shipped file — the sidecars and the provenance "
                            f"card join on those")
        lost = [a for a in row["attributes_lost"] if a in CONTRACT_ATTRIBUTES]
        if lost:
            problems.append(f"{name}: the shipped file lost {', '.join(lost)}, which "
                            f"docs/GLB-CONTRACT.md names")
        if not name.startswith(EPOCH_PREFIXES):
            master_bytes, shipped_bytes = row["bytes"]
            if shipped_bytes > master_bytes:
                problems.append(
                    f"{name}: the shipped derivative is {shipped_bytes:,} bytes and the master "
                    f"it came from is {master_bytes:,} — {shipped_bytes - master_bytes:+,} "
                    f"({100 * (shipped_bytes / master_bytes - 1):+.1f} %). meshopt's header and "
                    f"index buffer cost more than they save on a mesh this small, and a "
                    f"derivative that is not smaller than its master has no reason to exist. "
                    f"tools/web_derivatives.sh passes the master through in that case (K37)")
        if row["rungs"] > RUNG_TOLERANCE:
            problems.append(f"{name}: the shipped bounding box is {row['bbox_drift_m'] * 1000:.1f} "
                            f"mm from the master's, {row['rungs']:.2f} rungs of its own "
                            f"{row['extent_m']:.1f} m extent against a bound of "
                            f"{RUNG_TOLERANCE:.0f} — this is not quantisation")

        fault = material_fault(row)
        if fault:
            seen.add(name)
            was = banked.get(name)
            if was is None:
                problems.append(f"{name}: the shipped file's materials do not resolve to the "
                                f"master's — {fault['master_materials']} material(s) became "
                                f"{fault['shipped_materials']}, "
                                f"{len(fault['names_lost'])} name(s) and "
                                f"{fault['colours_lost']} colour(s) lost, "
                                f"{fault['textures_gained']} texture(s) gained. K36(b) owns "
                                f"the repair; this is a new one")
            elif (len(fault["names_lost"]) > len(was.get("names_lost", []))
                    or fault["colours_lost"] > was.get("colours_lost", 0)
                    or fault["textures_gained"] > was.get("textures_gained", 0)):
                problems.append(f"{name}: the material fault GREW — "
                                f"{len(fault['names_lost'])} name(s) lost against "
                                f"{len(was.get('names_lost', []))} banked. The ratchet is not "
                                f"an allowance")
    for name in sorted(set(banked) - seen):
        problems.append(f"{name}: banked in {BASELINE.name} as losing its material identity on "
                        f"the way to the site, and it no longer does. That is the repair — "
                        f"re-run tools/measure_web_derivatives.py --write-baseline in the "
                        f"commit that made it")

    # Assertion 8 (K38). Absolute in both directions against the banked set.
    decided = set(baseline.get("passthrough", []))
    copies = {r["name"] for r in result["rows"] if r["uncompressed_copy"]}
    for name in sorted(copies - decided):
        problems.append(f"{name}: assets/web/{name} is byte-identical to its master and is not "
                        f"a decided passthrough. Something copied a master over its derivative "
                        f"— the site ships it uncompressed and assertions 1-7 cannot see it, "
                        f"because a copy has the master's triangles, identity, attributes, "
                        f"bounding box and materials. Regenerate it with "
                        f"tools/web_derivatives.sh --only {name}, or bank the decision with "
                        f"--write-baseline if the compressed file really is bigger (K38)")
    for name in sorted(decided - copies):
        problems.append(f"{name}: banked in {BASELINE.name} as a decided master passthrough and "
                        f"it is compressed now. That is a repair, not a discovery — re-run "
                        f"tools/measure_web_derivatives.py --write-baseline in the commit that "
                        f"made it (K38)")

    # Assertion 9 (K39). Staleness answered from CONTENT, in both directions.
    recorded = result.get("record", {})
    for row in result["rows"]:
        name = row["name"]
        was = recorded.get(name)
        if was is None:
            problems.append(
                f"{name}: nothing records which master assets/web/{name} was made from. "
                f"tools/web_derivatives.sh writes {RECORD.name} as it produces each "
                f"derivative, so a file it does not appear in was written by something "
                f"else — regenerate it with tools/web_derivatives.sh --only {name} (K39)")
        elif was != row["master_sha256"]:
            problems.append(
                f"{name}: the shipped derivative was made from a master with sha256 "
                f"{was[:12]}… and the master in the tree today is {row['master_sha256'][:12]}…. "
                f"The master has been rebuilt since; the site would ship the OLD building's "
                f"bytes, and assertions 2-7 cannot see it when the rebuild kept the geometry "
                f"and moved only the confidence values. Regenerate it with "
                f"tools/web_derivatives.sh --only {name} (K39). Do not edit {RECORD.name} — "
                f"it is written by the step and by nothing else")
    for name in sorted(set(recorded) - {r["name"] for r in result["rows"]}):
        problems.append(
            f"{name}: {RECORD.name} records a master hash for a derivative that is not in "
            f"assets/web/ beside a master of its own. The record is rewritten whole by a "
            f"full tools/web_derivatives.sh run; a stale entry means the file was deleted "
            f"without one (K39)")
    return problems


# ---------------------------------------------------------------- output

def print_census(result: dict) -> None:
    rows = result["rows"]
    copies = [r for r in rows if r["uncompressed_copy"]]
    compressed = [r for r in rows if not r["uncompressed_copy"]]
    master_bytes = sum(r["bytes"][0] for r in rows)
    shipped_bytes = sum(r["bytes"][1] for r in rows)

    print(f"{len(rows)} master/derivative pair(s); "
          f"{len(result['master_only'])} master(s) with no derivative, "
          f"{len(result['shipped_only'])} derivative(s) with no master")
    print(f"  payload  masters {master_bytes / 1048576:.2f} MB  ->  shipped "
          f"{shipped_bytes / 1048576:.2f} MB")
    if compressed:
        cm = sum(r["bytes"][0] for r in compressed)
        cs = sum(r["bytes"][1] for r in compressed)
        print(f"  compressed  {len(compressed)} asset(s), {cm / cs:.2f}x")
    if copies:
        cs = sum(r["bytes"][1] for r in copies)
        decided = set(load_baseline().get("passthrough", []))
        undecided = sorted(r["name"] for r in copies if r["name"] not in decided)
        print(f"  shipped as a MASTER PASSTHROUGH (byte-identical to the master)  "
              f"{len(copies)} asset(s), {cs / 1024:.0f} KB, "
              f"{100 * cs / shipped_bytes:.1f} % of the payload — compressing them makes "
              f"them bigger (K37), which is a decision now and not an accident")
        print(f"    of those, {len(copies) - len(undecided)} are banked decisions and "
              f"{len(undecided)} are not (bound: 0, K38 — a copy nothing decided is a "
              f"writer nobody watched)")
        for name in undecided[:5]:
            print(f"      unbanked  {name}")
    grew = [r for r in rows
            if not r["name"].startswith(EPOCH_PREFIXES) and r["bytes"][1] > r["bytes"][0]]
    excluded = [r for r in rows
                if r["name"].startswith(EPOCH_PREFIXES) and r["bytes"][1] > r["bytes"][0]]
    print(f"  derivative bigger than its master: {len(grew)} (bound: 0) "
          f"+ {len(excluded)} epoch mesh(es) excluded by name, R-W6 "
          f"(their bit depth is asserted by tools/measure_terrain_fit.mjs --gate, T-0151)")
    for r in excluded:
        print(f"    excluded  {r['name']}  {r['bytes'][0]:,} -> {r['bytes'][1]:,} bytes "
              f"({r['bytes'][1] - r['bytes'][0]:+,})")

    worst = sorted((r for r in rows if r["bbox_drift_m"] is not None),
                   key=lambda r: -r["rungs"])[:5]
    print("  worst bounding-box disagreement (bound: "
          f"{RUNG_TOLERANCE:.0f} rungs of the asset's own extent):")
    for r in worst:
        print(f"    {r['rungs']:5.2f} rung  {r['bbox_drift_m'] * 1000:8.2f} mm  "
              f"extent {r['extent_m']:7.1f} m  {r['name']}")

    faults = [(r["name"], material_fault(r)) for r in rows if material_fault(r)]
    print(f"  material identity: {len(rows) - len(faults)} of {len(rows)} asset(s) reach the "
          f"site with the master's material names and colours")
    if faults:
        gained = sum(f["textures_gained"] for _, f in faults)
        print(f"    {len(faults)} do not: {gained} texture(s) exist on the site that exist in "
              f"no master, and the names they replace are the key R-W2b plans to wire")
        for name, fault in faults[:5]:
            print(f"      {name}: {fault['master_materials']} -> "
                  f"{fault['shipped_materials']} material(s), "
                  f"+{fault['textures_gained']} texture(s), lost "
                  f"{', '.join(fault['names_lost'][:4])}")
        if len(faults) > 5:
            print(f"      … and {len(faults) - 5} more")

    recorded = result.get("record", {})
    matched = sum(1 for r in rows if recorded.get(r["name"]) == r["master_sha256"])
    print(f"  master lineage (K39): {matched} of {len(rows)} derivative(s) record the master "
          f"they were made from, and that master's bytes are still the ones in the tree — "
          f"{len(rows) - matched} do not (bound: 0), {len(set(recorded) - {r['name'] for r in rows})} "
          f"record(s) name a derivative that is not here")

    lost = {}
    for r in rows:
        for a in r["attributes_lost"]:
            lost[a] = lost.get(a, 0) + 1
    if lost:
        detail = ", ".join(f"{k} on {v}" for k, v in sorted(lost.items()))
        print(f"  attributes dropped on the way (not gated, see the docstring): {detail}")


# ---------------------------------------------------------------- self-test

def self_test() -> int:
    """Break each absolute assertion in memory and confirm it fires.

    A gate nobody has seen fail is a gate nobody has seen. This runs against the real
    tree, mutates the parsed result rather than the repository, and asserts that each
    mutation produces at least one problem the clean tree does not.
    """
    result = measure()
    baseline = load_baseline()
    clean = assertions(result, baseline)
    if clean:
        print("SELF-TEST CANNOT RUN — the tree is not clean:", file=sys.stderr)
        for p in clean:
            print(f"  {p}", file=sys.stderr)
        return 1

    def mutate(label, fn):
        """Apply one mutation and require the gate to notice.

        A mutation that returns False could not be applied to THIS tree — the
        ratchet's mutation has nothing to repair once the ratchet is empty, which
        K36(b) made it. That is a self-test with nothing to say, not a gate that
        missed something, and reporting it as MISSED made the whole run read FAIL
        on a clean tree from 2026-08-16 until K37 read it.
        """
        import copy
        broken = copy.deepcopy(result)
        if fn(broken) is False:
            print(f"  skipped  {label} — nothing in this tree to mutate")
            return True
        found = assertions(broken, baseline)
        print(f"  {'caught' if found else 'MISSED'}  {label}"
              + (f" — {found[0][:96]}" if found else ""))
        return bool(found)

    ok = True
    print("self-test: each assertion, broken deliberately")
    ok &= mutate("a derivative with no master",
                 lambda r: r["shipped_only"].append("ghost__phase.glb"))
    ok &= mutate("a master with no derivative",
                 lambda r: r["master_only"].append("orphan__phase.glb"))
    ok &= mutate("the shipped file was simplified",
                 lambda r: r["rows"][0].__setitem__(
                     "triangles", (r["rows"][0]["triangles"][0],
                                   r["rows"][0]["triangles"][1] - 12)))
    ok &= mutate("the shipped file lost its structure_id",
                 lambda r: r["rows"][0]["identity_shipped"].__setitem__("extras", [None]))
    ok &= mutate("the shipped file lost _CONFIDENCE",
                 lambda r: r["rows"][0].__setitem__("attributes_lost", ["_CONFIDENCE"]))
    ok &= mutate("the building collapsed to a two-metre box",
                 lambda r: r["rows"][0].__setitem__("rungs", 8000.0))
    ok &= mutate("compression made the shipped file bigger than its master",
                 lambda r: _grow_derivative(r, epoch=False))

    # And the other way round for assertion 6's one exclusion: an exclusion nobody
    # has watched hold is an exclusion nobody has watched. Growing an epoch mesh by
    # the same amount must NOT fire, or the exclusion is decorative.
    import copy
    broken = copy.deepcopy(result)
    grown = _grow_derivative(broken, epoch=True)
    if grown is None:
        print("  skipped  the epoch exclusion (no epoch mesh in the tree)")
    else:
        fired = assertions(broken, baseline)
        print(f"  {'held' if not fired else 'LEAKED'}  the epoch exclusion: {grown} "
              f"grown past its master fires nothing (R-W6 owns that file's bit depth)")
        ok &= not fired
    ok &= mutate("a new asset loses its material names",
                 lambda r: _break_materials(r))
    ok &= mutate("a banked asset was repaired and not banked",
                 lambda r: _repair_materials(r, baseline))
    # K38's two, and they are the mutation assertions 1-7 survive: a master copied over
    # its own derivative changes nothing any of them measure.
    ok &= mutate("a master was copied over its compressed derivative",
                 lambda r: _copy_master_through(r, baseline))
    ok &= mutate("a decided passthrough was regenerated and not banked",
                 lambda r: _uncopy_passthrough(r, baseline))
    # K39's two, and they are the mutation assertions 1-8 survive: a master rebuilt into
    # the same geometry with different confidence values changes no triangle, no node, no
    # attribute, no bounding box, no material and no byte count.
    ok &= mutate("the master was rebuilt after the derivative was made",
                 lambda r: _rebuild_master(r))
    ok &= mutate("a derivative nothing recorded a master for",
                 lambda r: _forget_master(r))
    print("SELF-TEST PASS" if ok else "SELF-TEST FAIL")
    return 0 if ok else 1


def _grow_derivative(result: dict, epoch: bool) -> str | None:
    """Make one asset's shipped file a byte bigger than its master."""
    for row in result["rows"]:
        if row["name"].startswith(EPOCH_PREFIXES) is not epoch:
            continue
        master_bytes = row["bytes"][0]
        row["bytes"] = (master_bytes, master_bytes + 1)
        return row["name"]
    return None


def _break_materials(result: dict) -> bool:
    for row in result["rows"]:
        if not material_fault(row):
            row["names_lost"] = ["log", "chinking"]
            row["colours_lost"] = 2
            row["textures_shipped"] = row["textures_master"] + 2
            return True
    return False


def _copy_master_through(result: dict, baseline: dict) -> bool:
    """Make one compressed derivative a byte-for-byte copy of its master.

    This is what tools/publish.sh did whenever a master was newer by mtime, and the
    point of the mutation is what it does NOT change: the triangles, the node identity,
    the contract attributes, the bounding box and the material table are the master's,
    so assertions 1-5 and 7 stay silent and assertion 6 sees an equal byte count rather
    than a larger one. Measured against the real tree before this assertion existed,
    two of these passed the whole of tools/check.sh (K38).
    """
    decided = set(baseline.get("passthrough", []))
    for row in result["rows"]:
        if row["name"] in decided or row["uncompressed_copy"]:
            continue
        row["uncompressed_copy"] = True
        row["bytes"] = (row["bytes"][0], row["bytes"][0])
        return True
    return False


def _uncopy_passthrough(result: dict, baseline: dict) -> bool:
    """One banked passthrough comes back compressed, without being re-banked."""
    decided = set(baseline.get("passthrough", []))
    for row in result["rows"]:
        if row["name"] in decided and row["uncompressed_copy"]:
            row["uncompressed_copy"] = False
            return True
    return False


def _rebuild_master(result: dict) -> bool:
    """One master comes back from a bake with the same geometry and a new hash.

    The point of the mutation is what it does NOT change: nothing this file measures
    about the shipped bytes moves, which is why K38's residual survived eight
    assertions and an mtime scan.
    """
    for row in result["rows"]:
        if row["name"] in result.get("record", {}):
            row["master_sha256"] = "f" * 64
            return True
    return False


def _forget_master(result: dict) -> bool:
    """A derivative appears in assets/web/ that the step never recorded producing."""
    record = result.get("record", {})
    for row in result["rows"]:
        if row["name"] in record:
            del record[row["name"]]
            return True
    return False


def _repair_materials(result: dict, baseline: dict) -> bool:
    banked = set(baseline.get("material_identity", {}))
    for row in result["rows"]:
        if row["name"] in banked:
            row["names_lost"] = []
            row["colours_lost"] = 0
            row["textures_shipped"] = row["textures_master"]
            return True
    return False


# ---------------------------------------------------------------- entry point

def load_baseline() -> dict:
    if not BASELINE.exists():
        return {}
    return json.loads(BASELINE.read_text())


def load_record() -> dict:
    """The master hash each derivative was made from (K39). Read-only, here.

    There is deliberately no writer in this file. `tools/web_derivatives.sh` authors
    the record in the same run that produces the bytes it describes; a `--write-record`
    flag on the GATE would let anyone answer a stale-derivative failure by re-recording
    the hash instead of regenerating the file, which is the fault wearing a green tick.
    """
    if not RECORD.exists():
        return {}
    return json.loads(RECORD.read_text()).get("masters", {})


def write_baseline(result: dict) -> None:
    faults = {}
    for row in result["rows"]:
        fault = material_fault(row)
        if fault:
            faults[row["name"]] = fault
    passthrough = sorted(r["name"] for r in result["rows"] if r["uncompressed_copy"])
    BASELINE.write_text(json.dumps({
        "$note.passthrough": "ROADMAP K38. Assets whose shipped derivative IS the master, "
                 "byte for byte, because tools/web_derivatives.sh measured the compressed "
                 "file as the bigger of the two and kept the smaller one (K37). This list is "
                 "the DECISION. It is asserted in both directions and it is not a ratchet: a "
                 "derivative that is a master copy and is not listed here means something "
                 "other than the web-derivative step wrote it — assets/web/ has three "
                 "writers, and assertions 1-7 cannot see a copy at all. A listed asset that "
                 "is compressed now is a repair, and repairs are recorded rather than "
                 "discovered. Regenerate with --write-baseline in the commit that moves it.",
        "$note": "ROADMAP K36(a). Assets whose shipped derivative does not resolve to the "
                 "material table of the master it was compressed from — gltf-transform's "
                 "palette pass folds their named materials into one PaletteMaterial and two "
                 "generated PNGs. DERIVED — regenerate with "
                 "tools/measure_web_derivatives.py --write-baseline, and only ever to record "
                 "a repair. This file is a RATCHET: tools/check.sh fails on an asset that is "
                 "not here, on a listed one whose loss has grown, and on a listed one that is "
                 "now clean and has not been banked. It is NOT an allowance — K36(b) owns the "
                 "fix, and these are the numbers it takes as its baseline.",
        "measured": "2026-08-16",
        "pairs": len(result["rows"]),
        "material_identity": faults,
        "passthrough": passthrough,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {BASELINE.relative_to(ROOT)}: {len(faults)} material fault(s), "
          f"{len(passthrough)} decided passthrough(s)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gate", action="store_true", help="exit 1 on a divergence")
    ap.add_argument("--quiet", action="store_true", help="one summary line on success")
    ap.add_argument("--self-test", action="store_true", dest="selftest",
                    help="break each absolute assertion in memory and confirm it fires")
    ap.add_argument("--write-baseline", action="store_true", dest="write",
                    help="rewrite the material-identity ratchet (deliberate act)")
    args = ap.parse_args()

    if not MASTERS.exists() or not SHIPPED.exists():
        print("no baked assets yet — nothing to compare")
        return 0
    if args.selftest:
        return self_test()

    result = measure()
    if args.write:
        write_baseline(result)
        return 0

    problems = assertions(result, load_baseline())
    if not args.quiet:
        print_census(result)
    for p in problems:
        print(f"FAIL  {p}", file=sys.stderr)
    if problems:
        return 1
    if args.gate or args.quiet:
        rows = result["rows"]
        faults = sum(1 for r in rows if material_fault(r))
        worst = max((r["rungs"] for r in rows), default=0.0)
        copies = sum(1 for r in rows if r["uncompressed_copy"])
        print(f"shipped derivatives: {len(rows)} pair(s) carry the master's triangles, node "
              f"identity and contract attributes; worst bounding-box disagreement "
              f"{worst:.2f} of {RUNG_TOLERANCE:.0f} rungs; {faults} asset(s) lose their "
              f"material identity to the publish path (banked, K36(b)); {copies} master "
              f"passthrough(s), all of them decided (K38); and every one of them records "
              f"the master it was made from, which is still the master in the tree (K39)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
