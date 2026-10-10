"""Resolve a k13_conservatories structure record into what the K13 builder reads (T-2306).

A record of this archetype names ONE conservatory built from the K13 kit
(data/components/prairie_1904/k13_conservatories.json) and the wall it stands
against. Its phase's `form` carries both as attested-shaped entries:

    conservatory   a kit variant in full (form, sizes, bays, gutters, planting), the
                   house's own site-specific shape: what generators/archetypes/
                   k13_conservatories.py builds
    host_wall      the block the bay stands against: west_m and east_m of wall either
                   side of the bay's centre, depth_m back from it, height_m up

Nothing here imports Blender; `generators/mesh_inputs.py` hashes the dataclass this
returns, so every field the builder reads is in it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from archetypes.k01_frontage_params import CONFIDENCE_VALUE

REQUIRED = ("conservatory", "host_wall")
#: The form attributes that reach the mesh. `stories` and `construction` are stated on a
#: record for the card and declare `geometry: simplified`: the block is plain.
CONSUMED = frozenset(REQUIRED)
HOST_KEYS = ("west_m", "east_m", "depth_m", "height_m")


class ParamError(ValueError):
    pass


@dataclass
class K13ConservatoryParams:
    conservatory: dict
    host_wall: dict
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]


def from_phase(phase: dict, record: dict | None = None) -> K13ConservatoryParams:
    form = phase.get("form") or {}
    missing = [k for k in REQUIRED if k not in form]
    if missing:
        raise ParamError(f"{(record or {}).get('id')}/{phase.get('id')}: form lacks {', '.join(missing)}")
    host = form["host_wall"]["value"]
    bad = [k for k in HOST_KEYS if not isinstance(host.get(k), (int, float)) or host[k] <= 0]
    if bad:
        raise ParamError(f"{(record or {}).get('id')}: host_wall needs positive {', '.join(bad)}")
    return K13ConservatoryParams(
        conservatory=dict(form["conservatory"]["value"]),
        host_wall=dict(host),
        confidence={k: form[k]["confidence"] for k in REQUIRED},
    )
