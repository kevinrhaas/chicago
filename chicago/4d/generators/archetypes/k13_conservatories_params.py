"""Resolve a k13_conservatories structure record into what the K13 builder reads (T-2306).

A record of this archetype names ONE conservatory built from the K13 kit
(data/components/prairie_1904/k13_conservatories.json) and the wall it stands
against. Its phase's `form` carries both as attested-shaped entries:

    conservatory   a kit variant in full (form, sizes, bays, gutters, planting), the
                   house's own site-specific shape: what generators/archetypes/
                   k13_conservatories.py builds
    host_wall      the block the bay stands against: west_m and east_m of wall either
                   side of the bay's centre, depth_m back from it, height_m up. Only a
                   form that stands against a wall needs one (HOST_FORMS); a free-standing
                   span, span_lantern or span_apse has none (T-3164)

Nothing here imports Blender; `generators/mesh_inputs.py` hashes the dataclass this
returns, so every field the builder reads is in it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from archetypes.k01_frontage_params import CONFIDENCE_VALUE

REQUIRED = ("conservatory",)
#: The form attributes that reach the mesh. `stories` and `construction` are stated on a
#: record for the card and declare `geometry: simplified`: the block is plain.
CONSUMED = frozenset(("conservatory", "host_wall"))
#: generators/archetypes/k13_conservatories.py HOST_FORMS, restated so this module stays
#: free of the builder's imports
HOST_FORMS = frozenset({"lean_to", "curvilinear_lean_to", "canted_bay", "segmental_bay"})
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
    hosted = form["conservatory"]["value"].get("form") in HOST_FORMS
    if hosted and "host_wall" not in form:
        raise ParamError(f"{(record or {}).get('id')}/{phase.get('id')}: a "
                         f"{form['conservatory']['value'].get('form')} stands against a wall, so form lacks host_wall")
    host = form["host_wall"]["value"] if "host_wall" in form else {}
    bad = [k for k in HOST_KEYS if not isinstance(host.get(k), (int, float)) or host[k] <= 0]
    # T-1905: or the wall is another record's own, named and nothing else, and nothing is built for it
    if "structure" in host:
        if set(host) != {"structure"} or not isinstance(host["structure"], str) or not host["structure"]:
            raise ParamError(f"{(record or {}).get('id')}: a host_wall naming the structure whose wall it is "
                             f"names that and nothing else")
        bad = []
    if hosted and bad:
        raise ParamError(f"{(record or {}).get('id')}: host_wall needs positive {', '.join(bad)}")
    return K13ConservatoryParams(
        conservatory=dict(form["conservatory"]["value"]),
        host_wall=dict(host),
        confidence={k: form[k]["confidence"] for k in ("conservatory", "host_wall") if k in form},
    )
