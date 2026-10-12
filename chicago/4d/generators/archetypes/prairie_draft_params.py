"""Resolve a prairie_draft structure record into what the draft builder reads (T-2329).

A record of this archetype is one building of the Prairie Avenue DISTRICT DRAFT (owner,
2026-10-08: "an initial pass of the whole district ... the tickets later for each
building can refine your initial serviceable good draft model layer"). It is written by
`tools/draft_prairie_1904.py`, never by hand, and its phase's `form` carries:

    stories          the full storeys the 1911 Sanborn notation prints (attested)
    construction     the sheet's fabric colour, read as a wall family (attested/inferred)
    draft_plan       the building in rectangles, each fitted inside one traced part of
                     data/traces/prairie_1904_footprints_s<sheet>.json (inferred)
    draft_elevation  heights, roof family, openings, features and palette: the draft
                     rules of data/components/prairie_1904/draft_prairie_1904.json
                     applied to this row (reconstructed)
    draft            the pass, the register row, census ids, seed and the ticket that
                     refines it (record_only: the card reads it, the mesh does not)

Nothing here imports Blender; `generators/mesh_inputs.py` hashes the dataclass this
returns, so every field the builder reads is in it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from archetypes.k01_frontage_params import CONFIDENCE_VALUE

REQUIRED = ("stories", "construction", "draft_plan", "draft_elevation")
#: The form attributes that reach the mesh; `draft` is the card's.
CONSUMED = frozenset(REQUIRED)
KINDS = ("house", "service")
ROOFS = ("hip", "hip_steep", "mansard", "shaped_gable", "flat", "gable")
ROLES = ("main", "wing", "bay", "range", "porch", "stone_front")
CONSTRUCTIONS = ("brick", "stone", "frame", "brick_with_stone_front", "stone_with_brick_rear")


class ParamError(ValueError):
    pass


@dataclass
class PrairieDraftParams:
    kind: str
    stories: int
    construction: str
    plan: dict
    elevation: dict
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the rule from docs/GLB-CONTRACT.md."""
        return max((self.conf(a) for a in attrs), default=1.0)


def from_phase(phase: dict, record: dict | None = None) -> PrairieDraftParams:
    sid = (record or {}).get("id")
    form = phase.get("form") or {}
    missing = [k for k in REQUIRED if k not in form]
    if missing:
        raise ParamError(f"{sid}/{phase.get('id')}: form lacks {', '.join(missing)}")
    plan = form["draft_plan"]["value"]
    elev = form["draft_elevation"]["value"]
    kind = elev.get("kind")
    if kind not in KINDS:
        raise ParamError(f"{sid}: draft_elevation.kind {kind!r} is not one of {KINDS}")
    construction = form["construction"]["value"]
    if construction not in CONSTRUCTIONS:
        raise ParamError(f"{sid}: construction {construction!r} is not one of {CONSTRUCTIONS}")
    stories = int(form["stories"]["value"])
    if not 1 <= stories <= 4:
        raise ParamError(f"{sid}: {stories} storeys is outside the draft's 1-4")
    parts = plan.get("parts") or []
    if not parts or parts[0].get("role") != "main":
        raise ParamError(f"{sid}: draft_plan.parts must open with the main body")
    for p in parts:
        u0, v0, u1, v1 = p["rect"]
        if p.get("role") not in ROLES:
            raise ParamError(f"{sid}: part {p.get('id')} has role {p.get('role')!r}")
        if not (u1 - u0 >= 0.8 and v1 - v0 >= 0.8):
            raise ParamError(f"{sid}: part {p['id']} is thinner than 0.8 m")
        if p.get("roof", "flat") not in ROOFS:
            raise ParamError(f"{sid}: part {p['id']} roof {p.get('roof')!r} is not one of {ROOFS}")
    heights = elev.get("storey_heights_m") or []
    if len(heights) < stories:
        raise ParamError(f"{sid}: {len(heights)} storey heights for {stories} storeys")
    pitch = float(elev.get("roof_pitch_deg", 40))
    if not 10 <= pitch <= 65:
        raise ParamError(f"{sid}: roof pitch {pitch} is outside the study's 10-65 degrees")
    return PrairieDraftParams(
        kind=kind, stories=stories, construction=construction,
        plan={k: plan[k] for k in sorted(plan)}, elevation={k: elev[k] for k in sorted(elev)},
        confidence={k: form[k]["confidence"] for k in REQUIRED},
    )
