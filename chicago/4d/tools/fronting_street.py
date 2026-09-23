#!/usr/bin/env python3
"""Which street a committed roof FRONTS, derived from geometry (T-0367).

    tools/fronting_street.py                     every reconstructed dwelling
    tools/fronting_street.py --all               every committed structure
    tools/fronting_street.py recon_1835_south_d4_014
    tools/fronting_street.py --place "the corner of Dearborn and Lake streets"

WHY THIS EXISTS.

`tools/replace_invented_residents.py` refused 27 documented tradesmen for one
reason: the papers say WHERE they were. J. K. Botsford advertised at the corner
of Dearborn and Lake, D. Graves baked on South Water Street, L. W. Montgomery
made boots on South Water. Every one practises a trade this town raised an
invented household for, and seating him on whichever reconstructed roof the deal
happened to reach would have contradicted the advertisement that names him.

What the deal could not do was ASK where a reconstructed roof stands. A
household's dwelling is a structure id, and the street it stands on lived in a
placement note in prose — in no field, readable by nothing. This module answers
the question from the committed geometry instead, so the frontage is a derivation
and not a claim anybody has to maintain by hand.

HOW THE ANSWER IS DERIVED — the plat first, the centreline only as a fallback.

**A roof on a platted lot fronts the street its lot faces.** That is not a
measurement, it is the plat: `data/traces/vectors/thompson_lots.json` divides
every block into a north and a south tier and names the four streets bounding
it, so a lot's tier IS its frontage. `plat_occupancy.lot_holders` says which lot
a footprint stands on, under the two tests that module already defends.

**A lot at the end of its tier also fronts the cross street it abuts** — the
westmost lot of a tier touches the block's west bounding street, the eastmost its
east one. It is reported as a SIDE frontage and kept distinct from the tier's
front, because the two are different claims: the lot's frontage is measured on
the tier face, and the cross street is the side the building shows to it. This is
what a corner address means; without it the plat could never answer 'Dearborn
Street' at all, since every tier in this grid faces an east–west street.

**A roof off the platted grid falls back to the centreline band.** The west and
north divisions hold reconstructed dwellings the Thompson lots do not reach. For
those, a roof fronts a street when its footprint centroid lies within
`FRONTAGE_BAND_M` of the platted centreline. 25 m is not a new number: it is the
band `tools/measure_street_frontage.py` already uses for 'on this street', set by
T-A13/T-A14 and quoted by every block parcel since. The platted corridor is
24.384 m wide, so the band reaches 12.8 m past the corridor edge — about a lot's
setback — and no further into the block. The two methods are reported separately
by `--all` and never merged into one number.

The drawn track is ignored throughout: `path_local_enu_m` is the platted line,
which is what every lot and corridor derivation in this project reads (see the
`_doc` in data/streets/1835.json).

RESOLVING A PRINTED PLACE TO A COMMITTED STREET.

`streets_named()` takes the gazetteer's `associated_places` prose and returns the
committed streets it names — and only those. It requires the word `street(s)`:
'Fort Dearborn' is not Dearborn Street, "Kinzie's Addition" is not Kinzie Street,
and neither resolves. 'Water Street' does not resolve either, because this scene
commits both a South Water and a North Water and the line does not say which; an
ambiguous reading is left unresolved rather than guessed. Streets the paper names
that this scene does not commit ('Main Street', 'Monroe Street') resolve to
nothing, which is the true answer: no roof in this model can front them.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from measure_street_frontage import centroids, distance_to_street  # noqa: E402
from plat_occupancy import lot_holders  # noqa: E402

FRONTAGE_BAND_M = 25.0
STREETS = ROOT / "data" / "streets" / "1835.json"
LOTS = ROOT / "data" / "traces" / "vectors" / "thompson_lots.json"
DATUM = ROOT / "data" / "datum.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

#: how a frontage was derived, in the order the module prefers them
FRONT, SIDE, BAND = "lot front", "corner side", "centreline band"

_cache: dict = {}


def streets() -> list[dict]:
    if "streets" not in _cache:
        _cache["streets"] = json.loads(STREETS.read_text(encoding="utf-8"))["streets"]
    return _cache["streets"]


def street_name(street_id: str) -> str:
    for street in streets():
        if street["id"] == street_id:
            return street.get("name_1835") or street_id
    return street_id


def _lot_frontages() -> dict[str, list[tuple[str, str]]]:
    """structure id -> [(street id, how)] from the platted lot it stands on."""
    grid = json.loads(LOTS.read_text(encoding="utf-8"))
    datum = json.loads(DATUM.read_text(encoding="utf-8"))
    out: dict[str, list[tuple[str, str]]] = {}
    for block in grid["blocks"]:
        bounds, lots = block["bounded_by"], block["lots"]
        # The westmost lot of a tier abuts the block's west street and the
        # eastmost its east one. Derived from the polygons rather than from the
        # index, so it does not depend on the order generate_plat_lots writes.
        ends: dict[int, str] = {}
        for tier in {lot["tier"] for lot in lots}:
            row = sorted((i for i, lot in enumerate(lots) if lot["tier"] == tier),
                         key=lambda i: sum(x for x, _ in lots[i]["polygon"])
                         / len(lots[i]["polygon"]))
            if len(row) > 1:
                ends[row[0]], ends[row[-1]] = "west", "east"
        held = _held().get(block["id"], {})
        for index, structure_ids in held.items():
            faces = [(bounds[lots[index]["tier"]], FRONT)]
            if index in ends:
                faces.append((bounds[ends[index]], SIDE))
            for structure_id in structure_ids:
                out.setdefault(structure_id, []).extend(
                    face for face in faces if face not in out.get(structure_id, []))
    return out


def _held() -> dict[str, dict[int, list[str]]]:
    if "held" not in _cache:
        _cache["held"] = lot_holders(
            json.loads(LOTS.read_text(encoding="utf-8")),
            json.loads(DATUM.read_text(encoding="utf-8")))
    return _cache["held"]


def _index() -> dict[str, list[tuple[str, str]]]:
    """structure id -> [(street id, how it was derived)], best evidence first."""
    if "index" in _cache:
        return _cache["index"]
    index = _lot_frontages()
    for structure_id, point in centroids().items():
        if structure_id in index:
            continue  # the plat has already answered; a band cannot improve on it
        near = sorted((round(distance_to_street(street, point), 2), street["id"])
                      for street in streets())
        band = [(street_id, BAND) for metres, street_id in near
                if metres <= FRONTAGE_BAND_M]
        if band:
            index[structure_id] = band
    _cache["index"] = index
    return index


def fronting(structure_id: str) -> list[tuple[str, str]]:
    """The committed streets this structure fronts, best evidence first.

    Empty for a roof standing inside a block off the platted grid, and empty for
    a structure with no placed footprint — different facts, neither a frontage.
    """
    return _index().get(structure_id, [])


def fronts(structure_id: str, street_id: str) -> str | None:
    """How `structure_id` fronts `street_id`, or None if it does not."""
    for sid, how in fronting(structure_id):
        if sid == street_id:
            return how
    return None


# ---------------------------------------------------------------------------
# a printed place -> the committed streets it names
# ---------------------------------------------------------------------------

def _flat(text: str) -> str:
    return re.sub(r"[^a-z]", "", text.lower())


def _by_flat_name() -> dict[str, str]:
    if "names" not in _cache:
        # 'The fort road' and 'The bank track' are not '<Name> Street' and the
        # corpus never prints them as an address.
        # Sorted southernmost-first and claimed with setdefault, because two records can
        # carry one name: T-0451's North Division lines are the committed South Division
        # streets continued across the river, and the plat letters no name in any of them.
        # An address printed as "Dearborn Street" is the South Division line — the reach
        # the corpus advertises on — so the record reaching furthest south takes the name.
        #
        # T-0877 ADDED THE FIRST KEY, because "furthest south" was only ever a proxy for
        # "the street the town walked on" and a rival appeared BELOW the town: Wright's
        # School Section is a mile of ruled grid south of Madison, and it letters Clinton,
        # Canal, Market, Wells, Clark and State on lines that reach a mile further south
        # than the streets of those names. Measured before the fix, seating them moved
        # 'Clark Street', 'Market Street', 'Wells Street' and 'the corner of South Water
        # and Clark streets' off the town and onto unopened prairie. A record the town
        # USED carries no `opened` flag at all — the twenty-eight streets of the 1830
        # plats, the fort's two ways — and every survey line seated since is
        # `opened: false`, "platted, unopened, unworn". A printed address is a place
        # somebody walked to, so an unopened line never takes a name from a street that
        # was open, whichever reaches further south. Within each group T-0451's rule is
        # untouched, which is what keeps `dearborn` ahead of `dearborn_north`.
        # tools/compile_register.py keys printed names the same way and says so there.
        names: dict[str, str] = {}
        for street in sorted(streets(),
                             key=lambda r: (r.get("opened") is False,
                                            min(p[1] for p in r["path_local_enu_m"]))):
            if (street.get("name_1835") or "").lower().endswith("street"):
                names.setdefault(_flat(street["name_1835"]), street["id"])
        _cache["names"] = names
    return _cache["names"]


def _stem(words: list[str]) -> str | None:
    """The longest trailing run of `words` that is a committed street name."""
    for start in range(max(0, len(words) - 3), len(words)):
        street_id = _by_flat_name().get(_flat(" ".join(words[start:]) + " street"))
        if street_id:
            return street_id
    return None


def streets_named(place: str) -> list[str]:
    """Committed street ids named by one `associated_places` string, in order."""
    found: list[str] = []
    flat = _flat(place)
    for name, street_id in _by_flat_name().items():
        if name in flat and street_id not in found:
            found.append(street_id)
    # 'the corner of Dearborn and Lake streets' names two streets and spells
    # 'street' once, at the end, so containment cannot see either of them.
    for match in re.finditer(r"([a-z .']+?)\s+and\s+([a-z .']+?)\s+streets\b",
                             place.lower()):
        for half in match.groups():
            street_id = _stem(half.split())
            if street_id and street_id not in found:
                found.append(street_id)
    # Report them in the order the line prints them, so 'Dearborn and Lake'
    # reads Dearborn first whichever pass above found it.
    stems = {sid: name[:-len("street")] for name, sid in _by_flat_name().items()}
    found.sort(key=lambda sid: flat.find(stems[sid]) if stems[sid] in flat else len(flat))
    return found


def streets_of(places) -> list[str]:
    """Committed street ids named anywhere in a gazetteer place list."""
    found: list[str] = []
    for place in places or []:
        for street_id in streets_named(place):
            if street_id not in found:
                found.append(street_id)
    return found


def describe(structure_id: str) -> str:
    """One phrase naming what a roof fronts, for a refusal or a record note."""
    near = fronting(structure_id)
    if not near:
        return "no committed street"
    return "; ".join(f"{street_name(sid)} ({how})" for sid, how in near)


# ---------------------------------------------------------------------------

def _reconstructed_dwellings() -> list[tuple[str, str]]:
    rows = []
    for path in sorted(HOUSEHOLDS.glob("hh_inf_*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        structure_id = (doc.get("lives_at") or {}).get("value")
        if structure_id:
            rows.append((doc["id"], structure_id))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("structures", nargs="*", help="structure ids to ask about")
    parser.add_argument("--all", action="store_true",
                        help="every committed structure the derivation reaches")
    parser.add_argument("--place", action="append", default=[],
                        help="resolve a printed place to committed streets")
    args = parser.parse_args()

    for place in args.place:
        named = streets_named(place)
        print(f"  {place!r} -> "
              + (", ".join(street_name(s) for s in named) if named
                 else "no committed street of this scene"))
    if args.place:
        return 0

    if args.structures:
        rows = [(structure_id, structure_id) for structure_id in args.structures]
    elif args.all:
        rows = [(sid, sid) for sid in sorted(_index())]
    else:
        rows = _reconstructed_dwellings()

    print("the platted lot answers first; a roof off the grid falls back to the "
          f"{FRONTAGE_BAND_M:g} m centreline band\n")
    counts = {FRONT: 0, SIDE: 0, BAND: 0}
    on_a_street = 0
    for label, structure_id in rows:
        near = fronting(structure_id)
        if near:
            on_a_street += 1
        for _, how in near:
            counts[how] += 1
        where = describe(structure_id)
        print(f"  {label:34s} {structure_id:30s} {where}")
    print(f"\n  {on_a_street} of {len(rows)} front a committed street — "
          f"{counts[FRONT]} lot front(s), {counts[SIDE]} corner side(s), "
          f"{counts[BAND]} by the band.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
