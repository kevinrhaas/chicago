#!/usr/bin/env python3
"""What a generator half for a renderer-drawn layer would cost, measured.

    tools/measure_generator_half.py            print the three readings
    tools/measure_generator_half.py --gate     exit 1 if a stated figure has moved

WHY THIS EXISTS. Ticket T-0059 asked for *"a river-wharf mode of `pier_crib`"*, so
that a town assembled from GLBs alone would carry its docks. `docs/ROADMAP.md` K5
makes the same request of three other clauses in almost the same words — *"the
generator half, so a baked town carries its own yards"*. Before building one, three
things wanted a number rather than an opinion:

  1. **How many committed meshes does adding it re-stale?** `generators/
     mesh_inputs.py` hashes an archetype's builder, `generators/build.py` and
     the geometry-making half of `generators/common/` into every structure asset's
     `inputs_sha256`, and `generators/terrain_inputs.py` hashes `terrain_gen.py`
     and the same modules into every terrain asset's. Which half that is, is
     declared in `generators/code_inputs.py` (T-0164) rather than globbed. `tools/validate.py --stale` fails on
     any asset whose recomputed hash has moved. So the cost of adding a mode is not
     the mode: it is the rebake of everything the edited file's bytes reach. This
     measures that reach per candidate edit site.

  2. **Is a wharf the only layer that owes one?** The wharf is one of the data
     layers drawn at load out of committed JSON rather than loaded as a GLB. If the
     debt is general, paying it one layer at a time — by a route that re-stales the
     town each time — is the wrong shape of work, and the ticket is a fragment of a
     decision nobody has made rather than a unit anybody can ship.

  3. **Who would read the GLBs the mode would produce?** The ticket's motivation is
     *"a scene assembled from GLBs alone has no docks in it"*. That sentence has a
     consumer in it, and whether the consumer exists is checkable: it is the count
     of renderers under `renderers/`. A cost paid for a reader that does not exist
     is a different decision from one paid for a reader that does.

All three are printed. `--gate` holds them against the figures written into this
file's own `STATED` block, which is what makes them a measurement rather than a
number somebody remembers: the two are meant to be edited together, and a reading
that moves without the sentence beside it moving is the drift.

The drawn-layer denominator is derived from the tree — every `data/*/index.json` —
AND held against a named list. Deriving alone would silently absorb the next layer
somebody adds; naming alone would silently miss it. Held against each other, a new
layer fails this gate and gets read by a person, which is the only outcome worth
having.

NO BLENDER, NO NETWORK. It reads `assets/manifest.json`, the generator modules' own
hashing recipes and the committed layer manifests, all of which are in the tree —
the same standing this tool's neighbours in `tools/measure_*.py` have.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generators"
DATA = ROOT / "data"
MANIFEST = ROOT / "assets" / "manifest.json"
RENDERERS = ROOT / "renderers"
RENDERER_JS = RENDERERS / "web" / "js"

# The reading this file was written against, re-taken on 2026-08-27 on `dev`
# @ a638614c (T-0059). `--gate` holds the live measurement to it. Moving a figure
# here is a claim that the reach changed, and it belongs in the same commit as
# whatever changed it.
#
# The two zero rows are T-0164's, added 2026-08-28. `common/phases.py` decides
# whether a mesh is built at all and builds none, and while it was globbed into
# both recipes one comment line in it re-staled 349 of 349. It is out of the hash
# now, `generators/code_inputs.py` says why, and a zero here is what keeps it out:
# put it back and this row reads 349.
#
# 349 -> 350 and 347 -> 348 on 2026-08-28: T-0254 added one structure to the town,
# north_water_slough_crossing. One more committed asset, one more mesh that a change to
# the shared generator modules or to build.py would re-stale; the terrain and pier_crib
# reaches are untouched because the crossing is neither.
#
# 350 -> 353 and 348 -> 351 on 2026-08-28 (T-0028): `blk_lake_franklin` was opened and
# carries three roofs. This is the ordinary movement of the reading, not a change in
# reach — a structure asset is in `build.py`'s reach by construction — and the terrain
# and pier_crib reaches stay at 2 each, which is the point of stating them separately.
#
# 353 -> 354 and 351 -> 352 on 2026-08-28 (T-0096): `fort_dearborn_flagstaff__staff_1833_37.glb`,
# the garrison flagstaff Andreas attests. One new fort_structure record, so one more committed
# asset and one more mesh a change to the shared generator modules or to build.py would re-stale.
#
# 354 -> 358 and 352 -> 356 on 2026-08-29 (T-0317): `blk_randolph_market` took its second
# deal — a party-line run of three on the block's free corner lot and the stable in its yard.
# Four new structure assets, so four more meshes a change to the shared generator modules or
# to build.py would re-stale; the terrain and pier_crib reaches stay at 2 each.
#
# 358 -> 359 and 356 -> 357 on 2026-08-29 (T-0380): `new_york_house__frame_1834.glb`, the
# frame hotel on Lake Street near Wells this project had wrongly excluded. One new
# frame_tavern record, so one more committed asset and one more mesh a change to the shared
# generator modules or to build.py would re-stale; terrain and pier_crib stay at 2 each.
#
# 359 -> 360 and 357 -> 358 on 2026-08-30 (T-0384): `john_holbrook_store__frame_1835.glb`,
# the clothing store two papers place one door from Dearborn on South Water Street. One new
# frame_storefront record, so one more committed asset and one more mesh a change to the
# shared generator modules or to build.py would re-stale; terrain and pier_crib stay at 2.
#
# 359 -> 367 and 357 -> 365 on 2026-08-30 (T-0429): `blk_south_water_lasalle` took its second
# deal — a party-line run of six along the west half of the block's South Water frontage and the
# two yard buildings on the lots it stands on. Eight new structure assets, so eight more meshes a
# change to the shared generator modules or to build.py would re-stale; the terrain and pier_crib
# reaches stay at 2 each.
#
# 368 -> 372 and 366 -> 370 on 2026-09-03 (T-0430): `blk_south_water_franklin` took its
# second deal — a party-line run of three on the block's one free lot of South Water
# frontage and the privy in the yard behind them. Four new structure assets, so four more
# meshes a change to the shared generator modules or to build.py would re-stale; the
# terrain and pier_crib reaches stay at 2 each.
#
# 372 -> 374 and 370 -> 372 on 2026-09-05 (T-0431): `blk_south_water_clark` took its second
# deal — one C2 store-residence on the block's one free lot of South Water frontage, party-
# walled to Pruyne & Kimball's drug store, and the privy in the yard behind it. Two new
# structure assets, so two more meshes a change to the shared generator modules or to
# build.py would re-stale; the terrain and pier_crib reaches stay at 2 each.
#
# 375 -> 378 and 373 -> 376 on 2026-09-06 (T-0883): the Big Barn with Cupola, the Wash house
# and the Shop — three of the six things the 1830 Harrison plan names on Fort Dearborn's outer
# ground and nothing drew. Three new `outbuilding` records, so three more committed assets and
# three more meshes a change to the shared generator modules or to build.py would re-stale; the
# terrain and pier_crib reaches stay at 2 each.
#
# 378 -> 380 and 376 -> 378 on 2026-09-06 (T-0881): the fort's Out Buildings, which the same
# plate letters in the PLURAL and draws as TWO blocks rather than the one every earlier reading
# of the sheet took them for. Two new `outbuilding` records, so two more committed assets and
# two more meshes a change to the shared generator modules or to build.py would re-stale; the
# terrain and pier_crib reaches stay at 2 each. The Well is the sixth thing on that plate and
# adds nothing here: it is measured to a coordinate and deliberately not built, because this
# project has no well archetype (docs/RESEARCH/wells.md section 5, T-0887).
#
# 380 -> 383 and 378 -> 381 on 2026-09-11 (T-0432): the second deal on
# `blk_south_water_dearborn`, the last of the four South Water blocks T-0420 held in one
# ticket — two frame cottages on the South Water frontage of lot 2, one party-walled to each
# side wall of Frederick Thomas's shop, and the stable in the yard behind them. Three new
# structure assets, so three more meshes a change to the shared generator modules or to
# build.py would re-stale; the terrain and pier_crib reaches stay at 2 each.
#
# 383 -> 384 and 381 -> 382 on 2026-09-11 (T-1036): `fort_dearborn_us_factors_house`, the
# United States factory on the fort reservation — block A of the three the 1830 Harrison plate
# letters `U.S. Factor's House`, built as a `log_dwelling` where T-0894 read all three and
# built none. One new structure asset, so one more mesh a change to the shared generator
# modules or to build.py would re-stale; the terrain and pier_crib reaches stay at 2 each.
# Blocks B and C are drawn, unlettered and refused, and add nothing here: measured and
# deliberately not built.
#
# 9 -> 10 drawn-at-load layers on 2026-09-11 (T-0887): `data/wells/`, read by
# renderers/web/js/wells.js. The fort's well was the Well this block used to name as measured
# and not built — the plate letters it, Hubbard corroborates it and T-0881 measured it to a
# coordinate, and it stayed invisible because data/structures.schema.json has no well among its
# twelve archetypes and a structure record with no buildable form does not validate. The curb is
# derived at load from committed numbers, so THE ASSET COUNT DOES NOT MOVE and nothing re-stales:
# this layer, like the other nine, owes a generator half and has none.
#
STATED = {
    "assets": 384,
    "restales": {
        "generators/common/*.py": 384,
        "generators/common/__init__.py": 0,
        "generators/common/phases.py": 0,
        "generators/build.py": 382,
        "generators/terrain_gen.py": 2,
        "generators/archetypes/pier_crib.py": 2,
    },
    "layers_drawn_at_load": 10,
    "layers_with_a_generator": 0,
    "renderers": 1,
}

# The data layers a renderer draws at load out of committed JSON, rather than
# loading a baked GLB for. Each is a directory under `data/` carrying its own
# `index.json` manifest — a static host cannot be globbed, which is why every one
# of them has one — plus the renderer module that consumes it.
DRAWN_AT_LOAD = {
    "boats": "boats.js",
    "enclosures": "enclosures.js",
    "fauna": "fauna.js",
    "flora": "flora.js",
    "frontage": "frontage.js",
    "residents": "residents.js",
    "signage": "signage.js",
    "wells": "wells.js",
    "wharves": "wharves.js",
    "yard": "yard.js",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def restale_reach() -> tuple[dict, int, list]:
    """Per candidate edit site, how many committed assets its bytes are hashed into.

    The reach is not read off the files — it is read off the two hashing recipes,
    which is the only reading that cannot go stale behind them:

      * `mesh_inputs._code_shas(archetype)` names what a STRUCTURE asset's hash
        covers: `build.py`, that archetype's builder, and `common/*.py`.
      * `terrain_inputs._code_shas()` names what a TERRAIN asset's covers:
        `terrain_gen.py` and `common/*.py`.

    So a site's reach is the count of assets whose recipe names it.
    """
    problems: list[str] = []
    if not MANIFEST.exists():
        return {}, 0, ["assets/manifest.json is missing, so no reach can be measured"]
    sys.path.insert(0, str(GEN))
    try:
        import code_inputs                      # noqa: PLC0415
        import mesh_inputs                      # noqa: PLC0415
        import terrain_inputs                   # noqa: PLC0415
    except Exception as e:                      # noqa: BLE001
        return {}, 0, [f"cannot import the generators' hashing recipes: {e}"]

    assets = load(MANIFEST).get("assets", {})
    reach: dict[str, int] = {}
    for entry in assets.values():
        if entry.get("structure_id"):
            arch = entry.get("archetype")
            if not arch:
                problems.append("a structure asset in the manifest names no archetype")
                continue
            try:
                names = mesh_inputs._code_shas(arch)      # noqa: SLF001
            except Exception as e:                        # noqa: BLE001
                problems.append(f"archetype {arch}: {e}")
                continue
        elif entry.get("terrain_epoch"):
            names = terrain_inputs._code_shas()           # noqa: SLF001
        else:
            continue
        for rel in names:
            key = "generators/common/*.py" if rel.startswith("common/") \
                else f"generators/{rel}"
            reach[key] = reach.get(key, 0) + 1
    # `common/*.py` is counted once per FILE above; collapse it to once per asset.
    # The divisor is the RECIPE's own module list and not the directory listing,
    # because since T-0164 the two differ: dividing 349 assets x 3 hashed modules
    # by the 5 files in the folder reads 209, a reach nothing has.
    commons = len(code_inputs.geometry_modules()) or 1
    if "generators/common/*.py" in reach:
        reach["generators/common/*.py"] //= commons
    # The modules T-0164 took OUT of the recipe are reported at their reach, which
    # is zero, rather than omitted. That is the standing gate on the property the
    # ticket bought: drop an exclusion and this row goes straight back to 349, and
    # `--gate` says so with the sentence beside it instead of a rebake nobody
    # ordered turning up in the next bake's diff.
    for name in code_inputs.excluded():
        reach[f"generators/common/{name}"] = 0
    return reach, len(assets), problems


def layer_debt() -> tuple[list, list]:
    """Per drawn-at-load layer: is there anything under `generators/` that builds it?

    The test is deliberately blunt, because the answer is: an archetype module named
    for the layer, or a manifest asset whose archetype is. A layer with neither is
    drawn by the renderer and by nothing else, which is what "owes a generator half"
    means.
    """
    problems: list[str] = []
    assets = load(MANIFEST).get("assets", {}) if MANIFEST.exists() else {}
    baked = {e.get("archetype") for e in assets.values() if e.get("archetype")}

    # Derived and named, held against each other. See the module docstring.
    found = {p.parent.name for p in sorted(DATA.glob("*/index.json"))}
    for extra in sorted(found - set(DRAWN_AT_LOAD)):
        problems.append(f"data/{extra}/index.json is a manifested layer this file "
                        f"does not name; it is either a tenth drawn layer — in which "
                        f"case the reading below is out of date — or it is baked, in "
                        f"which case say so here")
    for gone in sorted(set(DRAWN_AT_LOAD) - found):
        problems.append(f"data/{gone}/index.json is named here and is not in the "
                        f"tree, so this reading counts a layer that no longer exists")

    rows = []
    for layer, module in sorted(DRAWN_AT_LOAD.items()):
        index = DATA / layer / "index.json"
        js = RENDERER_JS / module
        if not js.exists():
            problems.append(f"{layer}: renderers/web/js/{module} is missing, so "
                            f"nothing draws it and this reading is out of date")
        arch = GEN / "archetypes" / f"{layer}.py"
        records = 0
        if index.exists():
            doc = load(index)
            # The manifests do not agree on a key — `wharves`, `zones`,
            # `households`, and `flora` carries three lists at once — so the count
            # is not "the first list": it is every entry in the document that names
            # a record FILE, which is the one thing every one of these manifests agrees on
            # and the only thing this column is claiming.
            records = sum(1 for v in doc.values() if isinstance(v, list)
                          for e in v if isinstance(e, dict) and e.get("file"))
        rows.append({
            "layer": layer,
            "module": module,
            "records": records,
            "generator": arch.exists() or layer in baked,
        })
    return rows, problems


def renderers() -> list:
    """The things that could read a GLB. One directory under `renderers/` each."""
    return sorted(p.name for p in RENDERERS.iterdir()
                  if p.is_dir() and not p.name.startswith("."))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if a measured figure has moved off the stated one")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    reach, total, problems = restale_reach()
    rows, more = layer_debt()
    problems += more
    rend = renderers()
    drawn = len(rows)
    owed = sum(1 for r in rows if not r["generator"])

    if not args.quiet:
        print(f"COMMITTED, INPUT-TRACKED ASSETS: {total}\n")
        print(f"{'edit site':<42} {'re-stales':>9}   what a rebake would have to reach")
        for site, n in sorted(reach.items(), key=lambda kv: -kv[1]):
            share = ("nothing — outside both recipes (T-0164)" if n == 0
                     else "every committed mesh" if n >= total
                     else "every structure in the town" if n >= total - 2
                     else "the ground" if site.endswith("terrain_gen.py")
                     else "the meshes of that archetype alone")
            print(f"{site:<42} {n:>9}   {share}")
        print(f"\nLAYERS DRAWN AT LOAD FROM COMMITTED JSON: {drawn}, "
              f"{drawn - owed} with a generator, {owed} without\n")
        print(f"{'layer':<12} {'renderer module':<18} {'record files':>13}  "
              f"generator")
        for r in rows:
            print(f"{r['layer']:<12} {r['module']:<18} {r['records']:>13}  "
                  f"{'yes' if r['generator'] else 'NONE'}")
        print(f"\nRENDERERS THAT COULD READ A GLB: {len(rend)} — {', '.join(rend)}")

    for key, want in STATED["restales"].items():
        got = reach.get(key)
        if got != want:
            problems.append(f"{key} re-stales {got} asset(s); this file states {want}")
    if total != STATED["assets"]:
        problems.append(f"{total} committed asset(s); this file states {STATED['assets']}")
    if drawn != STATED["layers_drawn_at_load"]:
        problems.append(f"{drawn} layer(s) drawn at load; this file states "
                        f"{STATED['layers_drawn_at_load']}")
    if drawn - owed != STATED["layers_with_a_generator"]:
        problems.append(f"{drawn - owed} drawn layer(s) have a generator; this file "
                        f"states {STATED['layers_with_a_generator']}")
    if len(rend) != STATED["renderers"]:
        problems.append(f"{len(rend)} renderer(s) under renderers/; this file states "
                        f"{STATED['renderers']}. A second one is exactly the reader "
                        f"T-0059 was withdrawn for not having — re-read that ticket")

    for p in problems:
        print(f"FAIL  {p}", file=sys.stderr)
    if problems:
        return 1
    if args.gate:
        print(f"generator half: {owed} of {drawn} drawn layers owe one, for "
              f"{len(rend)} renderer; the cheapest route into the bake re-stales "
              f"{min(reach.values()) if reach else 0} committed mesh(es), the shared "
              f"ones {max(reach.values()) if reach else 0}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
