"""What determines the ground — the staleness hash for a terrain epoch.

The building half of this rule lives in `generators/mesh_inputs.py`, and its
docstring explains at length why a hash over "the files that were involved" is
the wrong hash. The ground was left on exactly that hash: whole file bytes of
`terrain_spec.json`, `river.geojson`, `hydrology.geojson`, `datum.json` and
`terrain_gen.py`, concatenated.

So the false positive `mesh_inputs` was written to end was still standing here,
and it was not hypothetical — it was blocking a repair. `terrain_spec.json` is
the only place a terrain claim's reasoning can be written, three `inferred`
claims carried none, and the validator had to warn rather than fail because
adding a sentence of prose to that file reported the ground as stale and could
not land without a Blender bake. A gate that makes writing a note cost a bake is
a gate that stops notes being written.

## What is hashed

1. **The spec, the traced vectors and the datum with their prose removed** — the
   graded numbers, ids, confidences and coordinates, and nothing that only a
   reader consumes. `note`, `*_note`, `_doc`, `label`, `scope`,
   `critical_caveat`, `why` and `sources` are stripped wherever they appear.
   That set is a DENYLIST on purpose: strip prose and everything else counts, so
   a zone, a reach or a watercourse added to the spec tomorrow is a mesh input
   the day it appears. An allowlist of keys the generator reads today would
   silently stop asking about the newest one, which is the failure this family
   of checks exists to prevent.

   `mesh` joins them (scheme `resolved-spec-v2`), and it is the one member of the
   set that is not prose. A `mesh:` declaration states what the ground does with a
   figure the generator does NOT read — `absent`, `simplified`, `record_only`,
   `restated_in_code` — so by its own definition it cannot move a vertex, and
   hashing it would make writing an admission cost a bake for exactly the reason
   writing a note used to. `tools/validate.py` checks it against this generator's
   `CONSUMED` sets, and its one state that asserts an agreement rather than an
   absence — `restated_in_code` — against the `RESTATES` map below.

   **It is called `mesh` and not `geometry`, which is what the structure records
   call it, because `geometry` is already taken and the test caught it on the
   first run.** In a GeoJSON, `geometry` is the feature's coordinates: stripping
   that key would have taken every traced bank line, river ring and slough
   centreline out of the ground's hash — a bank could have been redrawn and the
   committed mesh would still have read fresh. That is the precise opposite of
   what this file is for, and it is the same trap `name` is kept for (a CRS is
   named too). `test_terrain_prose_is_not_read_by_the_generator` is what refused
   it, by scanning the generator for reads of every stripped key.
2. **The bytes of the code that turns the spec into vertices** —
   `terrain_gen.py`, `generators/common/`, and the pinned Blender.

`sources` is stripped for the same reason a `note` is: a citation is an
obligation the record answers to (`check_terrain_claims` enforces it) and it
cannot move a vertex. `name` is deliberately NOT stripped — in a GeoJSON it also
names the CRS, and dropping `crs.properties.name` would take the coordinate
reference system out of the hash to save a feature title.

This file's own bytes are not hashed. It computes the hash and makes no
geometry — the same rule `mesh_inputs` applies to itself.

## The residual, stated rather than papered over

`terrain_gen.py` goes in whole, so a docstring edit in the generator still
re-stales the ground. That is the identical residual the building hash carries on
`build.py`, it is one file rather than a data file every claim has to be written
in, and no repair is queued behind it. It is written down here so the next person
to meet it knows it is known.

And, as on the building side: this compares inputs, not output. A hand-edited GLB
behind an untouched spec passes, and nothing here can see it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import code_inputs

ROOT = Path(__file__).resolve().parent.parent

# Bump when the recipe below changes. assets/manifest.json records the scheme its
# terrain entries were stamped under, so a definition change is a visible, dated
# event and the gate refuses a manifest it cannot compute rather than comparing
# two hashes that mean different things.
SCHEME = "resolved-spec-v5"

# Keys whose values are written for a reader, plus the one that is written for a
# reader AND a gate: `mesh` declares what the ground does with a figure this
# generator does not read, which cannot be an input to the mesh without being a
# contradiction. (`mesh`, not `geometry`: see the docstring — in a GeoJSON that
# word is the coordinates, and stripping it would gut the hash.) Nothing under
# `generators/` reads any of them —
# `test_terrain_prose_is_not_read_by_the_generator` holds that open.
PROSE_KEYS = frozenset({"note", "_doc", "label", "scope", "critical_caveat",
                        "why", "sources", "mesh", "box_derivation"})

# `box_derivation` joined the set in v5 (T-1067), and it is the plainest member
# of it: four paragraphs arguing each wall of the box from evidence, read by a
# person and by nothing else. It is where the reasoning for e_min, e_max, n_min
# and n_max has to be written, and until now writing a sentence into it reported
# both terrain meshes as STALE and demanded a twenty-minute Blender bake for text
# — the exact fault this module's docstring opens with, arriving through the one
# block whose whole purpose is prose. The GRID is what the generator reads and
# the grid is hashed; moving a number there still costs a bake, as it must,
# because that number moves every vertex in the field.


# Per graded block of `terrain_spec.json`, the field keys whose VALUE reaches a
# vertex in `terrain_gen.build_field`. The structure side of this rule is each
# archetype's `CONSUMED` (generators/archetypes/*_params.py) and the argument is
# identical: the confidence model grades how sure we are of a value and says
# nothing about whether the thing was built, so a claim a visitor reads with a
# chip over it may be a claim the mesh does not contain. `tools/validate.py`
# holds every stated figure outside these sets to a `mesh:` declaration on its
# block.
#
# WHY IT IS HERE AND NOT BESIDE THE CODE THAT DOES THE READING, which is where an
# archetype keeps its own: `terrain_gen.py` goes into the ground's hash whole, so
# writing this map into it would have re-staled the terrain and demanded a
# Blender bake for a constant that cannot move a vertex — the exact fault this
# module was written to end, arriving one more time from one more direction. The
# building side does not have the problem because a params module's bytes are
# already out of the hash. This file's bytes are out for the same reason (it
# computes the hash), and "what determines the ground" is its subject.
#
# What co-location bought is bought instead by a check:
# `test_declared_terrain_reads_are_real_reads` scans `terrain_gen.py` for a
# subscript or `.get()` of every key named here, so a declaration that stops
# being true fails rather than quietly excusing an omission.
#
# Keys that are the claim's machinery rather than a figure — `id`, `zone`,
# `label`, `confidence`, `sources`, notes — never reach the gate: they are
# stripped by `compile_scene.ground_fields`, the same enumeration the Evidence
# panel renders from. The gate therefore asks about exactly what a visitor is
# shown, and nothing else.
CONSUMED = {
    "water": frozenset(),
    "reaches": frozenset({"anchor_e", "anchor_n", "bed_ft", "e_fold_m"}),
    "channel_profile": frozenset({"e_fold_m"}),
    "bank": frozenset({"face_m"}),
    "divisions": frozenset({"crest_profile", "plain_profile", "face_profile", "far_m"}),
    "marsh_strips": frozenset({"applies_to", "width_m", "blend_m", "level_ft", "e_taper"}),
    "swales": frozenset({"line", "half_width_m", "depth_ft", "depth_profile"}),
    "approaches": frozenset({"line", "mode", "deck_ft", "grade", "half_width_m",
                             "side_slope", "end_overhang_m"}),
    "watercourses": frozenset({"bed_ft", "e_fold_m"}),
    "micro_relief": frozenset({"amplitude_ft", "wavelengths_m", "seed",
                               "south_limit_n_m"}),
    "surface_materials": frozenset(),
}


# Per graded block, the figures declared `restated_in_code` and WHERE the other
# half of each restatement lives.
#
# `restated_in_code` is the one `mesh:` state that asserts an AGREEMENT rather
# than an absence. `absent`, `simplified` and `record_only` all say the mesh does
# not contain a thing, and a reader who doubts one can go and look at the ground.
# This one says the mesh contains exactly what the figure says and gets it from
# somewhere else — so it is a claim about two documents at once, and until this
# map existed nothing held the pair together. `docs/STATUS.md` § 35 wrote it down
# as "the one state that asserts an agreement nothing enforces, which is a
# smaller version of the fault this whole family of checks exists to end".
#
# Three kinds, in descending order of how much the check buys, because saying so
# is cheaper than letting the next reader assume the strongest one:
#
#   ("artifact", "<file>:<key>", scale)
#       The figure restates a value in a committed GENERATED artifact — the
#       heightfield meta the bake wrote. Compared numerically after `scale`, so a
#       spec figure in feet is held against a mesh figure in metres. This is the
#       strongest of the three: the thing being agreed with is the ground itself,
#       not a description of it.
#   ("figure", "<sibling key>")
#       The figure restates another figure in the same block, one the generator
#       DOES read. Compared numerically. Also exact, and the drift it catches is
#       the ordinary one — somebody edits the build instruction and leaves the
#       restatement behind.
#   ("code", "<expression>")
#       The figure is prose describing an expression in `terrain_gen.py`. Prose
#       cannot be compared to Python, so the check is that the named expression
#       is still in the generator, exactly once, with comments stripped (a regex
#       that matches its own explanatory comment proves nothing — see
#       `check_sidecar_contract`, which reported itself on its first run). That
#       is one step weaker than the two above and is the same strength as
#       `test_declared_terrain_reads_are_real_reads`. Its failure mode is a false
#       positive on a reformat, which is the right way round: the sentence in the
#       spec and the line in the code are supposed to be edited together, and a
#       gate that fires when only one of them moves is the warning § 35 says this
#       state owes to whoever edits the generator.
#
# It lives here rather than in `terrain_spec.json` for the reason CONSUMED does
# not live in `terrain_gen.py`: it is a statement ABOUT the generator, and a new
# key in the spec outside the `mesh` block would be a mesh input and would cost a
# Blender bake to write down. `mesh` itself is stripped (see PROSE_KEYS), which is
# why re-declaring a figure `restated_in_code` is free and adding a `restates:`
# beside it would not have been.
RESTATES = {
    "water": {
        # Z = 0 is the definition of this project's vertical datum. The generator
        # writes the water plane at a literal zero and `heightfield.json` records
        # it, so editing this figure moves nothing and would leave the panel
        # telling a visitor the river stands somewhere the ground says it does not.
        "surface_ft": ("artifact", "heightfield.json:water_surface_m", 0.3048),
    },
    "channel_profile": {
        "shape": ("code", "depth_ft = bed_ft * (1.0 - np.exp(-d_in / efold))"),
    },
    "bank": {
        "profile": ("code", "ramp = 1.0 - (1.0 - t_bank) ** 2"),
    },
    "divisions": {
        # The crest the bank ramp arrives at IS `near_ft` — the ramp multiplies
        # the division level and reaches 1.0 at the top of the face. The two have
        # carried the same number by hand since the terrain landed, which the
        # block's own `mesh_note` said in as many words while declaring the figure
        # `record_only`, a state that owes nothing and asks nothing.
        "bank_crest_ft": ("figure", "near_ft"),
    },
    "micro_relief": {
        "applies_to": ("code",
                       "h_ft = np.where(water, depth_ft, (level_ft + micro) * ramp)"),
    },
}


class TerrainInputsError(ValueError):
    """The inputs to the ground cannot be resolved, so no hash can be taken."""


def is_prose(key: str) -> bool:
    """Is this key documentation of a claim rather than the claim itself?"""
    return key in PROSE_KEYS or key.endswith("_note")


def strip_prose(node):
    """The same document with every prose key removed, at any depth."""
    if isinstance(node, dict):
        return {k: strip_prose(v) for k, v in node.items() if not is_prose(k)}
    if isinstance(node, list):
        return [strip_prose(v) for v in node]
    return node


def _load(path: Path) -> dict:
    if not path.exists():
        raise TerrainInputsError(f"{path.relative_to(ROOT)} is missing, so what this "
                                 f"ground was built from cannot be established")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise TerrainInputsError(f"{path.relative_to(ROOT)} is not loadable: {e}") from e


def _sha_file(p: Path) -> str:
    if not p.exists():
        raise TerrainInputsError(f"{p.relative_to(ROOT)} is missing, so what this "
                                 f"ground was built from cannot be established")
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _code_shas() -> dict[str, str]:
    """The modules whose bytes turn a spec into a ground mesh.

    Not this file, which computes the hash. Not `build.py` or the archetypes,
    which build structures and share nothing with the ground.

    `common/` is asked through `code_inputs.geometry_modules()` since T-0164,
    for the reason written there. The ground had the worse end of the old glob:
    it was hashing `common/phases.py`, a rule about which STRUCTURE phases get a
    mesh, which the ground does not have and never reads.
    """
    gen = ROOT / "generators"
    wanted = [gen / "terrain_gen.py"] + code_inputs.geometry_modules()
    return {p.relative_to(gen).as_posix(): _sha_file(p) for p in wanted}


def terrain_inputs_doc(ep_dir: Path) -> dict:
    """Everything the hash is taken over, as a readable document.

    Exposed separately from the hash for the reason `structure_inputs_doc` is: a
    hash says *that* two builds differ and never *how*, and "why has the ground
    gone stale" is the question this file exists to make answerable. Diff two of
    these.
    """
    ep_dir = Path(ep_dir)
    return {
        "scheme": SCHEME,
        "epoch": ep_dir.name,
        "spec": strip_prose(_load(ep_dir / "terrain_spec.json")),
        "vectors": {
            name: strip_prose(_load(ep_dir / name))
            for name in ("river.geojson", "hydrology.geojson", "shoreline.geojson",
                         "branches.geojson")
        },
        "datum": strip_prose(_load(ROOT / "data" / "datum.json")),
        "code": _code_shas(),
        "blender_pin": (ROOT / "generators" / "blender.pin").read_text().strip(),
    }


def terrain_inputs_sha(ep_dir: Path) -> str:
    """The input hash for one epoch's ground and water GLBs.

    One definition, two callers: the bake writes it into `assets/manifest.json`
    and `tools/validate.py` recomputes it to decide whether the committed meshes
    still match the data. Two copies of this list would agree until the day one
    of them mattered.

    `shoreline.geojson` IS hashed, and the sentence that said it was not is the
    reason this had to be repaired rather than merely written. It was excluded on
    a premise — "traced evidence that `build_field` does not yet read, so
    including it would report the ground as stale for a file that cannot change
    it" — that stopped being true when the spec started naming its features. The
    spec's `water`, `divisions` and `surface_materials` blocks resolve
    `harbor_reach_water`, `north_shore_harbor_reach`, `south_shore_harbor_reach`
    and `sand_bar_1834` by id, `terrain_gen.main` loads all three GeoJSONs into
    one id table before it calls `build_field`, and those four features are the
    planform of the harbour, the lake shore and the sand bar. They move vertices.

    `branches.geojson` IS hashed too, and for the same reason one commit later:
    T-0219 carried the box south to Madison Street and the spec now resolves
    `south_branch_school_section`, `south_branch_west_bank` and
    `south_branch_east_bank` by id. The rule this list is actually keeping is
    simple — a vector file joins it the moment the spec names a feature in it,
    not the moment somebody remembers.

    WHAT THE OMISSION COST, because it is the argument for the denylist upstairs:
    T-0799 re-traced the whole east edge off the full Wright sheet — both pier
    lines, the cut, the bar to its tip, the old channel — and rewrote every one of
    those four features. `heightfield.bin` and both GLBs stayed on the old trace
    and the gate called them fresh, because the one file that had changed was the
    one file the hash had been told to look away from. The ground a visitor
    downloaded was a shore the project no longer believed in, for a week, greenly.

    So this list is now the same shape as the spec's: everything `main` loads,
    with its prose stripped. A file that reaches `build_field` is hashed whether
    or not today's spec happens to name a feature in it — the alternative is this
    exact failure, waiting on the next id the spec learns to resolve.
    """
    doc = terrain_inputs_doc(ep_dir)
    return hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()


if __name__ == "__main__":  # pragma: no cover — the "why is it stale" helper
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--epoch", default="e1834_harbor_cut")
    ap.add_argument("--doc", action="store_true", help="print the input document, not the hash")
    a = ap.parse_args()
    d = ROOT / "data" / "terrain" / "epochs" / a.epoch
    print(json.dumps(terrain_inputs_doc(d), sort_keys=True, indent=1) if a.doc
          else terrain_inputs_sha(d))
