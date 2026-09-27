#!/usr/bin/env python3
"""`generators/build.py` is the half of the bake that is NOT hashed. Keep it that way.

    tools/test_build_cli_has_no_geometry.py              gate the committed tree
    tools/test_build_cli_has_no_geometry.py --self-test  prove each refusal fires

TICKET T-1654. `mesh_inputs.py::_code_shas` used to hash `generators/build.py`
whole into every asset's input hash, so a change to its `argparse` block staled
**422 of 422** assets and the only remedy the gate offered was a full-town
rebake. The pipeline was split out into `generators/emit.py`, which the recipe
hashes instead, and `build.py` kept the command line.

## What this gate is for, and why the split needs one at all

`code_inputs.py` makes the case at length that an ALLOWLIST — *these lines are
hashed* — is the unsafe shape, because it silently drops the next thing somebody
adds. A file split is an allowlist wearing different clothes: it is safe only
while the unhashed file stays empty of geometry. Nothing about `build.py`'s name
stops a future edit putting a builder call back into it, and that edit would be
outside every asset's input hash, would move vertices, and would stale nothing.
No run would find out.

So the split is asserted rather than trusted, on the three routes by which
`build.py` could make geometry again:

  1. **importing an archetype.** The builders are what turn parameters into
     vertices; `emit.ARCHETYPES` is the one place that names them.
  2. **importing a shared builder from `common/`.** Same argument one level down —
     `common/mesh.py` and its neighbours are hashed through
     `code_inputs.geometry_modules()` precisely because they make geometry.
     `common/phases.py` is the exception and is allowed: it decides whether a mesh
     is built AT ALL, one step before anything is built, which is a selection
     rule and is why T-0164 took its bytes out of the hash in the first place.
  3. **touching `bpy` beyond `bpy.app`.** Every mesh in this project is made
     through `bpy.ops` and `bpy.data`. `bpy.app.version_string` is the one thing
     the CLI legitimately needs — it records the Blender that ran in the manifest
     — so `bpy.app` is allowed by name and the rest of the module is not.

A failure here is not "you wrote bad code". It is "this belongs in `emit.py`,
where the staleness gate can see it" — and the message says so.

WHAT IT DELIBERATELY DOES NOT CLAIM. It reads imports and attribute chains, not
behaviour: `build.py` could still reach geometry through `getattr`, an `exec`, or
a module that imports an archetype on its behalf. The gate is a ratchet against
the ordinary, likely edit — somebody adding a builder call back to `main()` —
and not a proof of isolation. The honest statement of what holds is the pair:
this, plus the fact that `emit.py` is where the pipeline currently is and is
hashed whole.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "generators" / "build.py"
sys.path.insert(0, str(ROOT / "generators"))

import code_inputs  # noqa: E402

# `bpy.app` is the manifest's record of which Blender ran. Everything else in the
# module makes or edits meshes.
BPY_ALLOWED = {"app"}

# Which `common/` modules the CLI may import — READ from the register that already
# answers it rather than restated here. `code_inputs.NO_GEOMETRY` is the project's
# one statement of which shared modules make no geometry, and it is the statement
# with teeth: a module named there is OUT of every asset's input hash, so importing
# it into build.py cannot move a vertex behind the staleness gate, which is the only
# thing this gate exists to stop.
#
# It was a literal `{"phases"}` until T-1652, and the step's own comment in check.sh
# had predicted what happened next: "an allowlist silently drops the next thing
# somebody adds". The next thing was `common/selection.py` — the `--only` rule, in
# NO_GEOMETRY with its reason, gated by tools/check_only_selection.py — and this gate
# refused it while its own self-test asserted that a selection rule is allowed. Two
# registers of the same fact disagreed within a day of the second one being written.
# Now there is one, and adding a module to NO_GEOMETRY (which `geometry_modules()`
# refuses to let rot) is what grants it.
COMMON_ALLOWED = {name[:-3] for name in code_inputs.NO_GEOMETRY if name.endswith(".py")}


def findings(source: str, filename: str = "generators/build.py") -> list[str]:
    """Every way this source would make geometry outside the hashed module."""
    out: list[str] = []
    tree = ast.parse(source, filename=filename)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "archetypes" or mod.startswith("archetypes."):
                names = ", ".join(a.name for a in node.names)
                out.append(f"line {node.lineno}: imports {names} from '{mod}'. The "
                           f"archetype builders are the geometry; they belong in "
                           f"generators/emit.py, whose bytes the staleness gate hashes")
            if mod == "common" or mod.startswith("common."):
                leaf = mod.split(".", 1)[1] if "." in mod else ""
                if leaf not in COMMON_ALLOWED:
                    out.append(f"line {node.lineno}: imports from '{mod}'. The shared "
                               f"builders under generators/common/ make geometry and are "
                               f"hashed as such — move the call into generators/emit.py")
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "archetypes" or a.name.startswith("archetypes."):
                    out.append(f"line {node.lineno}: imports '{a.name}'. The archetype "
                               f"builders are the geometry; they belong in "
                               f"generators/emit.py")

        # bpy.<attr>… — the attribute directly on the module, whatever is chained after
        elif isinstance(node, ast.Attribute):
            base = node.value
            if isinstance(base, ast.Name) and base.id == "bpy" and node.attr not in BPY_ALLOWED:
                out.append(f"line {node.lineno}: touches bpy.{node.attr}. Meshes are made "
                           f"through bpy; the CLI may read bpy.app (which Blender ran) and "
                           f"nothing else. Move it into generators/emit.py")
    return sorted(set(out))


def gate() -> int:
    if not CLI.exists():
        print(f"FAIL  {CLI.relative_to(ROOT)} is missing, so the half of the bake that "
              f"is not hashed cannot be checked")
        return 1
    hits = findings(CLI.read_text())
    if hits:
        print(f"FAIL  generators/build.py makes geometry, and generators/emit.py is what "
              f"mesh_inputs.py hashes — so this would move vertices without staling a "
              f"single committed mesh (T-1654):")
        for h in hits:
            print(f"        {h}")
        return 1
    print("ok    generators/build.py imports no archetype and no shared builder, and "
          "touches bpy only as bpy.app — the geometry is all in generators/emit.py, "
          "which is the module the input hash covers")
    return 0


CASES: list[tuple[str, str, bool]] = [
    ("an archetype import",
     "from archetypes import frame_tavern\n", True),
    ("an archetype params import",
     "from archetypes.frame_tavern_params import from_phase\n", True),
    ("a plain archetype import",
     "import archetypes.outbuilding\n", True),
    ("a shared builder import",
     "from common.mesh import reset_scene\n", True),
    ("a bpy.ops call",
     "import bpy\nbpy.ops.object.mode_set(mode='EDIT')\n", True),
    ("a bpy.data reach",
     "import bpy\nx = bpy.data.objects\n", True),
    ("a common/ module that is NOT in code_inputs.NO_GEOMETRY",
     "from common.materials import shade\n", True),
    ("the phase rule, which makes no geometry",
     "from common.phases import drawn_by_another_layer\n", False),
    ("the selection rule, which makes no geometry either",
     "from common.selection import parse_only, selects\n", False),
    ("bpy.app, which is the manifest's Blender stamp",
     "import bpy\nv = bpy.app.version_string\n", False),
    ("a CLI that only parses flags",
     "import argparse\nargparse.ArgumentParser()\n", False),
]


def self_test() -> int:
    failures = 0
    for label, src, should_fire in CASES:
        hits = findings(src, filename="<self-test>")
        fired = bool(hits)
        ok = fired == should_fire
        failures += not ok
        verdict = "ok  " if ok else "FAIL"
        print(f"   self-test | {verdict} {label} — "
              f"{'refused' if fired else 'allowed'}, "
              f"{'as it should be' if ok else 'which is wrong'}")
    # and the committed CLI itself, which is the case the gate actually runs on
    hits = findings(CLI.read_text())
    ok = not hits
    failures += not ok
    print(f"   self-test | {'ok  ' if ok else 'FAIL'} the committed build.py passes its "
          f"own gate")
    print(f"   self-test | {failures} failure(s)")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true",
                    help="prove each refusal fires when the split is broken")
    args = ap.parse_args()
    return self_test() if args.self_test else gate()


if __name__ == "__main__":
    sys.exit(main())
