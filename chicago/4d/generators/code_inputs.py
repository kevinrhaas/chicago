"""Which modules under `generators/common/` turn things into vertices.

TICKET T-0164. Both freshness recipes — `mesh_inputs.py::_code_shas` and
`terrain_inputs.py::_code_shas` — used to say `(gen / "common").glob("*.py")`,
and a glob is not a statement about geometry. It is a statement about a
directory. The two drifted apart the moment a module that makes no geometry was
filed there.

`mesh_inputs.py` writes the principle down and then broke it:

    A hash that cries stale for reasons that cannot change the geometry gets
    disbelieved, and a disbelieved gate is worse than no gate.

T-0161 moved the shared `drawn_by` rule into `common/phases.py`, which answers
*whether a mesh is built at all* one step before anything is built. Measured on
`dev` at c0436f2f, appending one comment line to it staled **344 of 344** assets;
re-measured on 2026-08-28 for this ticket, **349 of 349**. For a comment. That is
one full-town rebake — twenty minutes of Cycles and 349 GLBs whose bytes change
because Cycles is not bit-reproducible — bought by a docstring correction.

So the recipes ask this module instead, and this module answers with a NAMED set
rather than a directory listing.

## Why a blocklist and not an allowlist, which is the whole safety argument

The two designs fail in opposite directions, and only one of them fails safely.

An allowlist — *these four modules are hashed* — silently drops the NEXT module
somebody adds to `common/`. That module would be a geometry module, because
`common/` is where the archetypes' shared builders live; it would be outside
every asset's input hash; and nothing would go stale when it changed. The gate
would be quietly wrong and no run would ever find out.

A blocklist — *everything in `common/` is hashed except what is named here* —
makes the same mistake impossible. A new module is hashed by default. Taking one
out is a deliberate edit to this file, in a diff, with a sentence beside it
saying why. The cost of getting it wrong is a rebake somebody did not need,
which is loud and recoverable; the cost of the other mistake is a gate that
passes when it should not, which is neither.

## What leaving the hash does and does not give up, stated rather than assumed

`drawn_by_another_layer` is not unwatched now that its bytes are out. Its whole
effect is whether a phase gets a mesh, and BOTH directions of that are already
gated by `tools/validate.py`, in `check.sh`, on every run:

  * a phase that starts being `drawn_by` must leave **no GLB and no manifest
    entry** behind — `check_drawn_by` asserts exactly that, and the assets it
    would leave are the ones it fails on;
  * a phase that stops being `drawn_by` gains an asset that is not in the
    manifest, which is a MISSING asset rather than a stale one, and the missing
    check is what catches it.

The staleness hash was never the instrument for this rule; it was only the net
under it, and it is a net that also catches every docstring. What is genuinely
given up is narrower than "the rule is unwatched": it is that a rule change and
a rebake no longer arrive in the same event. `check.sh` still refuses the tree.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMON = ROOT / "generators" / "common"

# Each entry is a module under `generators/common/` whose bytes cannot change any
# vertex, and the sentence that says why. Both halves are required: a name with
# no reason is the beginning of the drift this file exists to stop.
NO_GEOMETRY: dict[str, str] = {
    "__init__.py": "the package marker — it declares the directory and builds "
                   "nothing, so its bytes reach no mesh.",
    "phases.py": "T-0161's shared `drawn_by` rule (see the module docstring). It "
                 "decides whether a mesh is built at all, one step before "
                 "anything is built, and makes no geometry itself. Both "
                 "directions of the rule are gated by tools/validate.py's "
                 "check_drawn_by and its missing-asset check instead.",
}


class CodeInputsError(ValueError):
    """What a mesh was built from cannot be established."""


def geometry_modules() -> list[Path]:
    """The `common/` modules whose bytes belong in an asset's input hash.

    Sorted, so the recipe is deterministic. Raises rather than guesses: a
    `common/` that has gone missing means no hash can be taken at all, and an
    exclusion naming a module that is no longer there is an exclusion doing
    nothing, which is how a blocklist rots into an allowlist without saying so.
    """
    present = sorted(p.name for p in COMMON.glob("*.py"))
    if not present:
        raise CodeInputsError(
            "generators/common/ holds no modules, so what a mesh was built from "
            "cannot be established")
    stale = sorted(set(NO_GEOMETRY) - set(present))
    if stale:
        raise CodeInputsError(
            f"code_inputs.NO_GEOMETRY names {', '.join(stale)}, which is not in "
            f"generators/common/ — an exclusion for a module that is gone "
            f"excludes nothing and hides the next one that moves in. Drop it.")
    return [COMMON / name for name in present if name not in NO_GEOMETRY]


def excluded() -> dict[str, str]:
    """The named exclusions and their reasons, for anything that reports them."""
    return dict(NO_GEOMETRY)
