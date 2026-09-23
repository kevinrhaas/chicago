#!/usr/bin/env python3
"""The evidence ladder, read from the one place it is defined.

`docs/PROVENANCE.md` § Evidence tiers is the reasoning; `data/source.schema.json`
is the copy a machine can read, and it is the copy this project enforces. Six
rungs, from a period document to decorative cartography, with two rules attached:

    Tier 5 and 6 sources may inform inventory and cross-checks. They must never
    be the sole evidence for a `documented` attribute, and no geometry is traced
    from them.

That sentence was written into the schema and into the prose, and until now it
was enforced by neither — `tier` did not appear anywhere in `tools/validate.py`.
It is also the number the provenance card printed at a visitor, bare: `tier 4`,
with nothing saying what a tier 4 is. One ladder, parsed once, used by the gate
and by the card, so the rung a value is held to and the rung a visitor reads
cannot come apart.

The labels are parsed out of the schema's own `description` rather than restated
here. That is deliberate and it is the same argument the rest of this project
makes about enumerating from the data: a second list is a list that stops being
true. If the description is reworded into a shape this cannot read, the parse
raises and every gate that uses it fails loudly, which is the correct outcome —
a silently empty ladder would pass everything.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "data" / "source.schema.json"

# "1 period/eyewitness · 2 near-primary recollection · ..." — the rungs are
# separated by the middot the schema writes them with, and the trailing prose
# after the last rung is a sentence about the rules, not a rung.
_RUNG = re.compile(r"^\s*(\d+)\s+(.+?)\s*$")

# The two rules the ladder carries, as numbers. Both come off the schema's own
# sentence: tiers 5-6 are never sole evidence for `documented` and nothing is
# traced from them. Written as "the lowest rung that is still allowed" so the
# comparisons below read the way the sentence does.
SOLE_EVIDENCE_MAX_TIER = 4      # a `documented` value needs one source at or above this rung
TRACEABLE_MAX_TIER = 4          # an outline may not come off a rung below this

# Where "a period source" stops. The schema's ladder puts first-hand and
# testimony-derived evidence at 1-3 (period document, near-primary recollection,
# compiled secondary from pioneer testimony) and later scholarly synthesis at 4.
# `docs/PROVENANCE.md` says `documented` "still requires a period source"; this
# is that sentence as a number. It is a WARNING rather than an error, and
# `docs/STATUS.md` § 43 prices why.
TESTIMONY_MAX_TIER = 3


def tier_ladder(schema_path: Path | None = None) -> dict[int, str]:
    """`{tier: label}` for every rung the source schema declares.

    Raises if the schema's description cannot be read as a ladder, or if the
    rungs it spells out do not cover the range it validates against. A ladder
    with a hole in it would let a source carry a tier no rule has an opinion on.
    """
    schema = json.loads((schema_path or SCHEMA).read_text(encoding="utf-8"))
    spec = schema.get("properties", {}).get("tier", {})
    desc = spec.get("description", "")
    lo, hi = spec.get("minimum"), spec.get("maximum")
    if lo is None or hi is None:
        raise ValueError("source.schema.json: tier declares no minimum/maximum, so the "
                         "ladder has no extent to check its rungs against")

    ladder: dict[int, str] = {}
    for chunk in desc.split("·"):
        # the last rung is followed by the rules sentence; a rung's label ends at
        # the first full stop that is followed by a space or the end of the string
        text = re.split(r"\.(?:\s|$)", chunk, maxsplit=1)[0]
        m = _RUNG.match(text)
        if not m:
            continue
        ladder[int(m.group(1))] = m.group(2)

    missing = [t for t in range(int(lo), int(hi) + 1) if t not in ladder]
    if missing:
        raise ValueError(
            f"source.schema.json: the tier description spells out {sorted(ladder)} but the "
            f"schema validates {lo}..{hi} — no rule can be written about tier(s) {missing} "
            f"and no visitor could be told what one is")
    extra = [t for t in ladder if not (int(lo) <= t <= int(hi))]
    if extra:
        raise ValueError(f"source.schema.json: the tier description defines rung(s) {extra} "
                         f"outside the {lo}..{hi} the schema accepts")
    return ladder


def tier_label(tier, ladder: dict[int, str] | None = None) -> str:
    """The words for a rung, or an empty string for a tier the ladder has none for.

    Empty rather than "unknown": the caller decides whether a missing label is a
    finding, and the card would rather print a bare number than a wrong word.
    """
    if tier is None:
        return ""
    try:
        t = int(tier)
    except (TypeError, ValueError):
        return ""
    return (ladder if ladder is not None else tier_ladder()).get(t, "")


if __name__ == "__main__":
    for t, label in sorted(tier_ladder().items()):
        print(f"  tier {t}  {label}")
