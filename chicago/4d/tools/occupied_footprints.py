"""Occupied annex components beside a structure's unchanged core reference.

The core polygon remains the archetype's dimensional and coordinate reference.
Physical blockers read every occupied component, preserving gaps between them.
The pure archetype's resolved component frames also drive its actual builder.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def additional_parts(record: dict, phase: dict) -> list[dict]:
    """Compiler/native source view of the resolved annex solids, or no extras."""
    form = phase.get("form") or {}
    claim = form.get("enclosed_left_annex") or {}
    if record.get("archetype") != "frame_tavern" or claim.get("value") is None:
        return []
    if str(ROOT / "generators") not in sys.path:
        sys.path.insert(0, str(ROOT / "generators"))
    from archetypes.frame_tavern_params import from_phase
    params = from_phase(phase, record)
    return [{"id": part["id"], "polygon": part["polygon"],
             "confidence": claim.get("confidence", "reconstructed"),
             "sources": list(claim.get("sources") or []),
             "note": "Occupied ground of this reconstructed annex component; "
                     "its exact resolved frame also builds the walls and door. "
                     "The open yard bay is not a solid connecting polygon."}
            for part in params.left_annex_parts if part["occupied"]]


def local_polygons(sidecar: dict) -> list[list]:
    """Core first, then separate occupied polygons; never a filled convex hull."""
    raw = sidecar.get("footprint") or {}
    core = raw if isinstance(raw, list) else raw.get("polygon", [])
    out = [core] if isinstance(core, list) and len(core) >= 3 else []
    extras = [] if isinstance(raw, list) else raw.get("additional_polygons", [])
    if not isinstance(extras, list):
        raise ValueError("footprint.additional_polygons must be a list")
    for part in extras:
        poly = part.get("polygon") if isinstance(part, dict) else None
        if (not isinstance(poly, list) or len(poly) < 3
                or any(not isinstance(p, (list, tuple)) or len(p) != 2
                       or any(isinstance(n, bool) or not isinstance(n, (int, float))
                              or not math.isfinite(n) for n in p) for p in poly)):
            raise ValueError("malformed additional occupied polygon")
        out.append(poly)
    return out


def world_polygons(sidecar: dict) -> list[list[tuple]]:
    """Each occupied ring in local ENU, with its original owner kept separate."""
    place = sidecar.get("placement") or {}
    if place.get("local_e") is None or place.get("local_n") is None:
        return []
    theta = math.radians(place.get("rotation_deg") or 0.)
    cs, sn = math.cos(theta), math.sin(theta)
    e, n = place["local_e"], place["local_n"]
    return [[(e+u*cs+v*sn, n-u*sn+v*cs) for u, v in poly]
            for poly in local_polygons(sidecar)]


def additional_world_polygons(sidecar: dict) -> list[list[tuple]]:
    """Only the extra rings, so old readers can preserve their core arithmetic."""
    raw = sidecar.get("footprint") or {}
    if isinstance(raw, list) or not raw.get("additional_polygons"):
        return []
    return world_polygons(sidecar)[1:]


def phase_polygons(record: dict, phase: dict) -> list[list]:
    """The source-phase equivalent used by corridor/ground and siting gates."""
    return local_polygons({"footprint": {**(phase.get("footprint") or {}),
        "additional_polygons": additional_parts(record, phase)}})


def phase_world_polygons(record: dict, phase: dict, datum: dict) -> list[list[tuple]]:
    place = phase.get("position") or {}
    if place.get("utm_e") is None or place.get("utm_n") is None:
        return []
    return world_polygons({"placement": {
        "local_e": place["utm_e"]-datum["origin_utm_e"],
        "local_n": place["utm_n"]-datum["origin_utm_n"],
        "rotation_deg": place.get("rotation_deg", 0.)}, "footprint": {
            "polygon": (phase.get("footprint") or {}).get("polygon", []),
            "additional_polygons": additional_parts(record, phase)}})
