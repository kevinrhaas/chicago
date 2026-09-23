"""What determines a mesh — the hash the staleness gate compares against.

NO bpy import, deliberately. `tools/validate.py` has to recompute this on every
commit in a bare Python 3.11, because a staleness check that only runs where
Blender runs is a check that runs nightly at best, and the commit that breaks
the correspondence is not the commit that discovers it.

## What is hashed, and why it is not "the files that were involved"

The first version of this hash (in `build.py`, replaced by this module) hashed
the phase record, *every* `.py` under `generators/`, and `blender.pin`. It was
never actually compared against anything, and when it finally was, all six
committed buildings came out stale — none of them for a reason that could move a
vertex. Two whole classes of false positive:

- **Record prose.** The phase JSON went in whole, so a `note` rewrite, a new
  source id, or the `geometry:` declarations added on 2026-08-10 all read as
  "the mesh changed". None of them are read by any generator.
- **Unrelated code.** One hash over every generator meant an edit to
  `terrain_gen.py` invalidated the taverns, and a comment added to one
  archetype's parameter module invalidated the other archetypes' buildings.

A hash that cries stale for reasons that cannot change the geometry gets
disbelieved, and a disbelieved gate is worse than no gate: it teaches the reader
that "stale" means nothing. So this one hashes **what the builder can actually
see**:

1. the *resolved* archetype parameters — `from_phase(phase, record)`, not the phase
   and not the record — so only a value the generator reads counts, and it counts
   after defaulting. The record joined the phase in T-0007, when the archetypes
   started reading the finish the 665-roof programme dealt them; it is passed rather
   than hashed, for the same reason the phase is;
2. every `@property` the parameter class derives from those fields, because
   `addition_height_m`'s 2.55/4.7 constants are as load-bearing as any field;
3. the confidence *floats*, not the labels, so a change to `CONFIDENCE_VALUE`
   registers even though it never appears in a field;
4. the bytes of the code that turns parameters into vertices — this archetype's
   builder, `generators/common/`, `build.py`, and the pinned Blender.

`<arch>_params.py` bytes are deliberately NOT hashed. That module's entire effect
on the mesh is the object it returns, and that object is hashed above in more
detail than its source would give: two params modules that resolve a record
identically produce the same building, and the hash should say so.

The residual is stated rather than papered over: this compares inputs, not
output. Cycles AO is not bit-reproducible across hardware, which is why the
project defines freshness on inputs in the first place; a hand-edited GLB with an
untouched record still passes, and nothing here can catch that.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path

import code_inputs

ROOT = Path(__file__).resolve().parent.parent

# Bump when the recipe below changes. assets/manifest.json records the scheme it
# was stamped under, so a definition change is a visible, dated event rather than
# an unexplained wave of staleness — and the gate refuses a manifest whose scheme
# it does not know instead of comparing hashes that mean different things.
SCHEME = "resolved-params-v3"


class InputsError(ValueError):
    """The inputs to a mesh cannot be resolved, so no hash can be taken."""


def _sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _code_shas(archetype: str) -> dict[str, str]:
    """The modules whose bytes turn parameters into vertices.

    Not the parameter modules — see the note above. Not `terrain_gen.py`, which
    builds the ground and shares nothing with a building. Not this file, which
    computes the hash and makes no geometry.

    And not, since T-0164, whatever happens to be filed in `common/`: the
    directory is asked through `code_inputs.geometry_modules()`, which names the
    modules that make geometry rather than listing the ones that share a folder.
    `common/phases.py` decides whether a mesh is built at all and makes none, and
    while it was globbed in, one comment line in it staled 349 of 349 assets.
    """
    gen = ROOT / "generators"
    wanted = [gen / "build.py", gen / "archetypes" / f"{archetype}.py"]
    wanted += code_inputs.geometry_modules()
    out = {}
    for p in wanted:
        if not p.exists():
            raise InputsError(f"{p.relative_to(ROOT)} is missing, so what this mesh "
                              f"was built from cannot be established")
        out[p.relative_to(gen).as_posix()] = _sha_file(p)
    return out


def _params_doc(params) -> dict:
    """Everything the builder can read off a resolved parameter object."""
    if not is_dataclass(params):
        raise InputsError(f"{type(params).__name__} is not a dataclass, so its fields "
                          f"cannot be enumerated")
    fields = asdict(params)
    confidence = fields.pop("confidence", {}) or {}
    derived = {name: getattr(params, name)
               for name, member in sorted(vars(type(params)).items())
               if isinstance(member, property)}
    return {
        "fields": fields,
        # the floats that reach the _CONFIDENCE attribute, not the labels that
        # name them — the mapping between the two is itself an input
        "confidence": {a: params.conf(a) for a in sorted(confidence)},
        "inferred": derived,
    }


def resolve_params(archetype: str, phase: dict, record: dict | None = None):
    """`from_phase` for one archetype, imported without Blender.

    The record travels alongside the phase because the finish the 665-roof programme
    dealt a building is not a form attribute — it sits one level up, in the record's
    `reconstruction` block — and since T-0007 the archetypes read it. `build.py`
    passes the same pair, which is the property this module exists to hold: the hash
    is taken over what the builder can actually see, and over nothing else.
    """
    gen = str(ROOT / "generators")
    if gen not in sys.path:
        sys.path.insert(0, gen)
    try:
        mod = __import__(f"archetypes.{archetype}_params", fromlist=["from_phase"])
    except Exception as e:  # noqa: BLE001
        raise InputsError(f"no importable parameter module for archetype "
                          f"'{archetype}': {e}") from e
    return mod.from_phase(phase, record)


def structure_inputs_doc(structure: dict, phase: dict, archetype: str | None = None) -> dict:
    """Everything the hash is taken over, as a readable document.

    Exposed separately from the hash because a hash tells you *that* two builds
    differ and never *how*, and "why has everything gone stale" is the question
    this file exists to make answerable. Diff two of these.
    """
    arch = archetype or structure.get("archetype")
    if not arch:
        raise InputsError(f"structure {structure.get('id')} declares no archetype")
    return {
        "scheme": SCHEME,
        "structure": structure.get("id"),
        "phase": phase.get("id"),
        "archetype": arch,
        "params": _params_doc(resolve_params(arch, phase, structure)),
        "code": _code_shas(arch),
        "blender_pin": (ROOT / "generators" / "blender.pin").read_text().strip(),
    }


def structure_inputs_sha(structure: dict, phase: dict, archetype: str | None = None) -> str:
    """The input hash for one structure phase's GLB."""
    doc = structure_inputs_doc(structure, phase, archetype)
    return hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
