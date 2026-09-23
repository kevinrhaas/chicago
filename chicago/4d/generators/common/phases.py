"""What the builder may read off a phase before it decides to build one.

TICKET T-0161. One rule lives here, and it lives here rather than in either
caller because it had FOUR restatements and one of them was missing.

`drawn_by` is a phase saying its geometry moved to another layer. The record
that started it is `data/structures/estray_pen.json`, whose note is as plain as
it gets:

    "A phase carrying this block builds NO MESH: no GLB is baked from it,
     tools/compile_scene.py writes `asset: null` into the sidecar, the renderer
     loads no asset for it and the walker is not stopped by its footprint."

`tools/validate.py`, `tools/compile_scene.py` and
`tools/generate_dooryard_plantings.py` each honoured that with their own copy of
`if ph.get("drawn_by")`. `generators/build.py` — the one program the sentence is
actually addressed to — had ZERO occurrences of the string. So the builder and
the validator disagreed about the same record and the bake sat between them:
`build.py --all` baked `estray_pen__pen_1833.glb`, `web_derivatives.sh` made a
derivative of it, and `validate.py` then failed twice, which made `check.sh` red
straight out of `tools/bake.sh`. Every full bake needed the GLB, the derivative
and three manifest entries deleted BY HAND to pass its own gate.

A predicate copied into four files is a rule in none of them: three copies
agreeing is not agreement, it is a coincidence that held until someone wrote a
fourth reader and did not know to copy it. So the copies are replaced by imports
of this one, and the fourth reader — the builder — is added.

WHY THIS FILE IS IN `common/`: because that is where a rule four callers share
belongs, and for no other reason. It is a filing decision and nothing hangs on it.

THIS FILE IS NOT IN THE INPUT HASH, and the paragraph that used to stand here
argued the opposite — that a rule about WHICH PHASES GET A MESH AT ALL had to be
inside `inputs_sha256`, so that changing it staled every asset. That reasoning
was followed and then measured (T-0164). Appending ONE COMMENT LINE to this file
staled **349 of 349** assets, because what the recipe hashed was this file's
BYTES and every byte of it is prose. A full-town rebake for a docstring is the
disbelieved gate `mesh_inputs.py` warns about, in its own words:

    A hash that cries stale for reasons that cannot change the geometry gets
    disbelieved, and a disbelieved gate is worse than no gate.

The rule is not unwatched for being out of the hash. Both directions of it are
gated by `tools/validate.py` on every `check.sh` run: a phase that starts being
`drawn_by` must leave no GLB and no manifest entry behind (`check_drawn_by`
asserts exactly that), and a phase that stops being `drawn_by` gains an asset the
manifest does not list, which is a MISSING asset rather than a stale one. The
staleness hash was the net under this rule, never the instrument for it — and it
was a net that caught every comment as well.

`generators/code_inputs.py` is where the exclusion is declared, with the reason
beside it, and it is a blocklist so that the NEXT module filed here is hashed by
default. Read it before moving anything in or out of this directory.
"""
from __future__ import annotations


def drawn_by_another_layer(phase: dict) -> bool:
    """True when nothing should bake a mesh for this phase.

    The test is deliberately the bare truthiness of the key, which is what all
    three original readers applied: `drawn_by` is either absent, or it is a block
    that `tools/validate.py::check_drawn_by` then holds to every half of its own
    promise — the named record exists, names this structure back, is listed in
    its layer's manifest, carries no `form`, and leaves NO GLB and NO manifest
    entry behind. Validating the block's CONTENTS is that function's job and is
    not repeated here; this answers only the one question a builder asks, which
    is whether to build at all.
    """
    return bool(phase.get("drawn_by"))
