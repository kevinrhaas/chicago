#!/usr/bin/env python3
"""The line a party-line street row stands on, out of the committed block boundary.

T-0077 wrote this arithmetic inside `tools/generate_inferred_infill.py`, where the
first frontage run was built. T-0078 needed the same three answers — which line a
face is, which way its fronts look, and where along it a wall lands — inside
`tools/generate_block_infill.py` for the South Water row, and a second copy of it
beside the first would be a second opinion about the same ground. That is the exact
defect the plat module exists to retire (a hand-typed northing beside the committed
geometry), so the rule lives in one module both generators import, as
`tools/plat_occupancy.py` and `tools/family_bands.py` already do for their own.

Everything here is derived: the caller hands in a block of the committed grid in
`data/traces/vectors/thompson_lots.json` and gets back its face. Nothing in this
module authors a coordinate.
"""

from __future__ import annotations

import math

FACES = ("north", "south", "east", "west")


def face_frame(block: dict, face: str) -> dict:
    """The face's frame: its west (or south) end, the axis running along it, the
    outward normal — which is the way the fronts look — the facade bearing under the
    renderer's convention, and the face length.

    The boundary is a closed ring wound from the north-west corner, so the north face
    is its first edge; all four are picked by measuring rather than by index, so a
    re-derived plat that winds the other way is a failure here instead of a silent
    ninety-degree error.
    """
    if face not in FACES:
        raise SystemExit(f"a block face is one of north, south, east, west — not {face!r}")
    ring = [tuple(p) for p in block["boundary_local_enu_m"]]
    edges = [(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring))]
    pick = {
        "north": lambda e: (e[0][1] + e[1][1]) / 2,
        "south": lambda e: -(e[0][1] + e[1][1]) / 2,
        "east": lambda e: (e[0][0] + e[1][0]) / 2,
        "west": lambda e: -(e[0][0] + e[1][0]) / 2,
    }
    a, b = max(edges, key=pick[face])
    length = math.dist(a, b)
    if length <= 0:
        raise SystemExit(f"{block.get('id')}: degenerate {face} face")
    along = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
    outward = (-along[1], along[0])
    # The face is picked as an edge of the ring, so it may run either way round it.
    # A run is anchored on the block's EAST (or north) corner and packs back along
    # the face, so the axis is normalised to point that way and the outward normal
    # with it — otherwise a re-wound ring would silently pack a row off the block.
    if (along[0] if face in ("north", "south") else along[1]) < 0:
        a, b = b, a
        along = (-along[0], -along[1])
        outward = (-outward[0], -outward[1])
    if (outward[1] if face in ("north", "south") else outward[0]) * (
            1 if face in ("north", "east") else -1) < 0:
        outward = (-outward[0], -outward[1])
    return {
        "origin": a, "far": b, "along": along, "outward": outward,
        "length": length,
        "bearing": round(math.degrees(math.atan2(outward[0], outward[1])) % 360.0, 3),
    }


def project(frame: dict, point: tuple[float, float]) -> tuple[float, float]:
    """(distance along the face from its origin, distance outward from its line)."""
    dx, dy = point[0] - frame["origin"][0], point[1] - frame["origin"][1]
    return (dx * frame["along"][0] + dy * frame["along"][1],
            dx * frame["outward"][0] + dy * frame["outward"][1])


def extent(frame: dict, polygon: list[tuple[float, float]]) -> tuple[float, float]:
    """(west wall, east wall) of a footprint, measured along the face."""
    spans = [project(frame, p)[0] for p in polygon]
    return (min(spans), max(spans))
