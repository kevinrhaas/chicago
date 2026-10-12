"""Resolve a k12_coach_house structure record into what the K12 builder reads (T-2321).

A record of this archetype names ONE coach house built from the K12 kit
(data/components/prairie_1904/k12_coach_house.json) on a named lot. Its phase's `form`
carries it as an attested-shaped entry:

    coach_house    a kit variant in full (width and depth along and back from the alley,
                   the alley's side, its ends, pitch, openings, the fittings it asks for
                   and its workyard): what generators/archetypes/k12_coach_house.py builds

Nothing here imports Blender; `generators/mesh_inputs.py` hashes the dataclass this
returns, so every field the builder reads is in it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from archetypes.k01_frontage_params import CONFIDENCE_VALUE

REQUIRED = ("coach_house",)
#: The form attributes that reach the mesh. `stories` and `construction` are stated on a
#: record for the card and declare `geometry: simplified`: the kit builds its own storeys
#: in its own brick.
CONSUMED = frozenset(REQUIRED)
SIZE_KEYS = ("width_m", "depth_m")


class ParamError(ValueError):
    pass


@dataclass
class K12CoachHouseParams:
    coach_house: dict
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]


def from_phase(phase: dict, record: dict | None = None) -> K12CoachHouseParams:
    form = phase.get("form") or {}
    rid = f"{(record or {}).get('id')}/{phase.get('id')}"
    missing = [k for k in REQUIRED if k not in form]
    if missing:
        raise ParamError(f"{rid}: form lacks {', '.join(missing)}")
    v = form["coach_house"]["value"]
    bad = [k for k in SIZE_KEYS if not isinstance(v.get(k), (int, float)) or v[k] <= 0]
    if bad:
        raise ParamError(f"{rid}: coach_house needs positive {', '.join(bad)}")
    if v.get("alley_side") not in ("west", "east"):
        raise ParamError(f"{rid}: coach_house needs alley_side 'west' or 'east'")
    return K12CoachHouseParams(
        coach_house=dict(v),
        confidence={k: form[k]["confidence"] for k in REQUIRED},
    )
