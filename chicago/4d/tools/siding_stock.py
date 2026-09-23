#!/usr/bin/env python3
"""The stock a clapboard wall hangs — the set, the deal, and who may be dealt from it.

T-0049 invented the set and dealt it to the 24 NAMED frame buildings
(`tools/deal_siding_stock.py`, docs/LIBERTIES.md L148). It could not reach the
anonymous roofs: every one of them re-derives byte-for-byte from a parcel recipe
(`tools/generate_block_infill.py` and kin), so a value written into the record by a
second tool is drift the moment the recipe runs again. They kept the archetypes'
0.14 m default and the deal counted them as fixed 0.140 m neighbours — which is
131 buildings hanging one board rhythm, the uniformity L22 named, one number over.

T-0112 deals them IN their recipes, and this module is the one place the set and
the rule are authored so that the two populations cannot drift apart.

## The set

Four period mill sidings, stated as the exposed face — the part of the board left
"to the weather" once the course above laps it:

    4.5 in -> 0.114 m      5 in -> 0.127 m
    5.5 in -> 0.140 m      6 in -> 0.152 m

## The two deals, and why they do not key the same way

The named deal keys a building's base stock to its phase's construction season,
because a town supplied by separate shipments of St Joseph sawn lumber
(docs/research/02-flora.md) sided the buildings of one season from one pile. That
key works on the named records because they carry real, differing construction
dates — 1831, 1833-08-16, 1834-01-04, 1835-06-08.

**It is degenerate on the anonymous ones, and that is the whole reason this module
exists.** Every one of the 131 carries `documented_range.from = 1835-01-01`, which
is not a construction season: it is the programme's count-unit convention, the same
literal on every anonymous roof in the town. Keyed to it, all 131 would be dealt
ONE stock — the archetypes' single course put back a step over, a range collapsed to
a point, which is the fault T-V1 and T-0142 already found twice in this dataset.

So an anonymous roof's base stock is DRAWN from the set on the record's own stable
key, the way `tools/family_bands.py` draws a footprint, an eave and a pitch from the
bands the crosswalk authors as ranges. Slot 11, because slots 1-10 are spoken for and
two decisions sharing a slot would make a building's siding a function of its porch.

## Then the same separation, and what it does and does not reach

Both deals then advance a roof's stock until no roof already dealt within 60 m wears
it. The separation is not a claim about 1835 — it is the surface variety T-0049
reconstructs, recorded as such.

A recipe deals **its own parcel** and no other. It could not do otherwise without
reading the other parcels' committed records, which would mean that moving one North
roof re-deals the platted blocks and restales their meshes — a coupling that turns
every future building into a town-wide rebake. So the separation holds inside a
parcel and between the named population and all of them (the named deal runs last and
reads what the recipes wrote); a pair straddling two parcels may share, and 18 of the
192 anonymous pairs standing within 60 m of each other do. Some sharing is
unavoidable in any case: four stocks cannot separate a roof with nine neighbours, and
the densest stands here have nine.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

# The one sampling rule, shared rather than retyped — `tools/family_bands.py` exists
# because the same arithmetic in two files means only one of them runs it.
from family_bands import stable_fraction  # noqa: E402

# The period stock set, exposed face in metres, keyed by the original inches.
STOCKS = [("4.5 in", 0.114), ("5 in", 0.127), ("5.5 in", 0.140), ("6 in", 0.152)]
DEFAULT_M = 0.140            # the archetypes' own default, what an undealt wall wears
NEIGHBOUR_M = 60.0           # within this, two clapboard walls must not share a stock
SLOT = 11                    # the stable-key slot this deal draws on; see the docstring

FRAME_ARCHETYPES = ("frame_dwelling", "frame_storefront", "frame_tavern")

ATTRIBUTE = "siding_exposure_m"

# The note on every value a RECIPE deals. The named deal's own sentence lives with the
# named deal, because the two differ in exactly the way the docstring above explains and
# one note covering both would have to be vague about which key was used.
NOTE = (
    "INVENTED WITHIN A STOCK SET, NOT DERIVED. No source states the exposed face of any "
    "Chicago building's siding. The value is one of four period mill sidings — 4.5, 5, "
    "5.5 or 6 in to the weather; this roof wears {inches} — dealt in this building's own "
    "parcel recipe: drawn from the set on this record's stable key, then advanced so that "
    "no roof of the parcel standing within 60 m hangs the same course. It is NOT keyed to "
    "a construction season the way the named buildings' stocks are: this record's "
    "1835-01-01 is the programme's count-unit convention and not a date anything was "
    "built, so keying to it would deal every anonymous roof in the town one stock. The "
    "separation is the surface variety T-0049 reconstructs, not a claim about 1835. "
    "docs/LIBERTIES.md L148 owns the invention and the recipe half is recorded beside "
    "it, under `tools/siding_stock.py`."
)


def cladding_of(form: dict | None) -> str:
    """What the wall wears. Absent means the archetype's default, which is clapboard."""
    a = (form or {}).get("cladding")
    return "clapboard" if a is None else a.get("value", "clapboard")


def hangs_clapboard(archetype: str | None, form: dict | None) -> bool:
    """A frame wall with courses to expose. A vertical-board wall has none."""
    return archetype in FRAME_ARCHETYPES and cladding_of(form) == "clapboard"


def exposure_of(form: dict | None) -> float:
    """The stock a committed wall wears — its dealt value, or the archetype default."""
    a = (form or {}).get(ATTRIBUTE)
    if not isinstance(a, dict):
        return DEFAULT_M
    try:
        return float(a["value"])
    except (KeyError, TypeError, ValueError):
        return DEFAULT_M


def drawn_index(key: str) -> int:
    """The base stock for an anonymous roof: drawn from the set on the record's key."""
    return min(int(stable_fraction(key, SLOT) * len(STOCKS)), len(STOCKS) - 1)


def advance(base: int, near: set[float]) -> tuple[str, float]:
    """The first stock at or after `base` that no neighbour in `near` wears.

    Four stocks and no more: a roof hemmed in by all four keeps the last one tried
    rather than inventing a fifth. That best-effort is deliberate and is the same one
    the named deal has always made — the alternative is widening the invention to make
    an arithmetic problem go away.
    """
    inches, metres = STOCKS[base % len(STOCKS)]
    for step in range(len(STOCKS)):
        inches, metres = STOCKS[(base + step) % len(STOCKS)]
        if metres not in near:
            break
    return inches, metres


def deal(entries, fixed=()) -> dict[str, tuple[str, float]]:
    """Deal a stock to each of `entries`, in the order given.

    `entries` are `(id, position | None, base_index)`; `fixed` are
    `(position, metres)` walls already standing that this deal may not move.
    Returns `{id: (inches, metres)}`.
    """
    taken = [(e, n, m) for (e, n), m in fixed]
    dealt: dict[str, tuple[str, float]] = {}
    for sid, pos, base in entries:
        near: set[float] = set()
        if pos is not None:
            near = {m for e, n, m in taken
                    if math.hypot(e - pos[0], n - pos[1]) <= NEIGHBOUR_M}
        inches, metres = advance(base, near)
        dealt[sid] = (inches, metres)
        if pos is not None:
            taken.append((pos[0], pos[1], metres))
    return dealt


def attribute(inches: str, metres: float) -> dict:
    """The form attribute a recipe writes. No `sources`: the bound is the stock set.

    The named deal's values carry none either — the reconstruction specification does
    not speak to a board width, so a citation to it here would be a provenance claim
    with nothing behind it (the fault tools/band_notes.py exists to stop).
    """
    return {"value": metres, "confidence": "reconstructed",
            "note": NOTE.format(inches=inches)}


# --------------------------------------------------------------------------
# the recipe side
# --------------------------------------------------------------------------

def _phase(record: dict) -> dict:
    phases = record.get("phases") or []
    if len(phases) != 1:
        raise SystemExit(f"{record.get('id')}: the siding deal reads one phase per "
                         f"generated record and this one has {len(phases)}")
    return phases[0]


def _position(phase: dict) -> tuple[float, float] | None:
    pos = phase.get("position") or {}
    e, n = pos.get("utm_e"), pos.get("utm_n")
    return None if e is None or n is None else (float(e), float(n))


def is_invented(record: dict) -> bool:
    """Whose siding a recipe may deal.

    The `reconstruction` block is what separates the two kinds of record a recipe
    writes. An anonymous count-unit and a roof raised for a reconstructed household
    both carry one and are inventions whole (docs/LIBERTIES.md L91 admits every form
    value on them); the inferred-household programme's DOCUMENTED buildings — the
    Heacock house, the Temple Lake Street building, the two Wright buildings to let —
    carry none, because they are attested buildings this parcel happens to regenerate.
    Dealing those a stock would be inventing a board width for a real building outside
    the entry that owns that invention, so they stay on the default and the deal counts
    them as the fixed neighbours they are.
    """
    return isinstance(record.get("reconstruction"), dict)


def deal_records(records: list[dict]) -> int:
    """Deal every invented clapboard frame roof in ONE parcel its stock, in place.

    Records are walked in id order — the order the files are written, and the order
    the named deal walks — so the outcome is a function of the parcel and nothing
    else, and `--check` re-derives it byte for byte. Returns the number dealt.
    """
    fixed: list[tuple[tuple[float, float], float]] = []
    entries = []
    for record in sorted(records, key=lambda r: r["id"]):
        phase = _phase(record)
        form = phase.get("form")
        if not hangs_clapboard(record.get("archetype"), form):
            continue
        pos = _position(phase)
        if not is_invented(record):
            # An attested wall this recipe rebuilds: a neighbour, never a subject.
            if pos is not None:
                fixed.append((pos, exposure_of(form)))
            continue
        if isinstance((form or {}).get(ATTRIBUTE), dict):
            # Already authored by the parcel's own overrides — a recipe that states a
            # board width outright has said something this deal must not overwrite.
            if pos is not None:
                fixed.append((pos, exposure_of(form)))
            continue
        entries.append((record["id"], pos, drawn_index(record["id"])))

    dealt = deal(entries, fixed)
    by_id = {r["id"]: r for r in records}
    for sid, (inches, metres) in dealt.items():
        _phase(by_id[sid]).setdefault("form", {})[ATTRIBUTE] = attribute(inches, metres)
    return len(dealt)
