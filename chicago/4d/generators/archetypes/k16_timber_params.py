"""Resolve a k16_timber structure record into what the K16 builder reads (T-2323).

A record of this archetype names the timber street front of ONE house, built from the K16
kit (data/components/prairie_1904/k16_timber.json), and the plain body it stands against.
Its phase's `form` carries each as an attested-shaped entry:

    layout       which street the front faces, and the gap left between abutting parts
    gable        a kit `gable` variant in full: the front gable, its shingle bands, its sash
    wing_wall    a kit `clapboard_wall` variant in full: the wall beside it, with its corner
    porch        a kit `porch` variant in full, built as two halves mirrored about its middle
    body         the stand-in envelope behind the front: depths, roof pitch, colour
    canted_bay   optional: a plain bay standing on the gable front's ground storey
    roof_covering optional: the roof's colour

Nothing here imports Blender; `generators/mesh_inputs.py` hashes the dataclass this
returns, so every field the builder reads is in it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from archetypes.k01_frontage_params import CONFIDENCE_VALUE

REQUIRED = ("layout", "gable", "wing_wall", "porch", "body")
OPTIONAL = ("canted_bay", "roof_covering")
#: The form attributes that reach the mesh. `stories` and `construction` are stated on a
#: record for the card and declare `geometry: simplified`.
CONSUMED = frozenset(REQUIRED + OPTIONAL)
KINDS = {"gable": "gable", "wing_wall": "clapboard_wall", "porch": "porch"}
BODY_KEYS = ("gable_depth_m", "wing_depth_m", "wing_roof_pitch_deg", "roof_under_m")


class ParamError(ValueError):
    pass


@dataclass
class K16TimberParams:
    layout: dict
    gable: dict
    wing_wall: dict
    porch: dict
    body: dict
    canted_bay: dict | None = None
    roof_covering: dict | None = None
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]


def from_phase(phase: dict, record: dict | None = None) -> K16TimberParams:
    rid = f"{(record or {}).get('id')}/{phase.get('id')}"
    form = phase.get("form") or {}
    missing = [k for k in REQUIRED if k not in form]
    if missing:
        raise ParamError(f"{rid}: form lacks {', '.join(missing)}")
    for k, kind in KINDS.items():
        if form[k]["value"].get("kind") != kind:
            raise ParamError(f"{rid}: {k} must be a kit {kind!r} variant, not {form[k]['value'].get('kind')!r}")
    if form["layout"]["value"].get("faces") not in ("east", "south"):
        raise ParamError(f"{rid}: layout.faces must be east or south")
    body = form["body"]["value"]
    bad = [k for k in BODY_KEYS if not isinstance(body.get(k), (int, float)) or body[k] < 0]
    if bad:
        raise ParamError(f"{rid}: body needs non-negative {', '.join(bad)}")
    if not isinstance(form["porch"]["value"].get("half_width_m"), (int, float)):
        raise ParamError(f"{rid}: porch needs half_width_m")
    return K16TimberParams(
        **{k: dict(form[k]["value"]) for k in REQUIRED},
        **{k: dict(form[k]["value"]) for k in OPTIONAL if k in form},
        confidence={k: form[k]["confidence"] for k in REQUIRED + OPTIONAL if k in form},
    )
