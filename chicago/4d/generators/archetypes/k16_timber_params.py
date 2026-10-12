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

OR, since T-2357, a WHOLE small frame house closed on every face from the kit:

    frame_house  blocks in the lot plan frame (u toward the street, v along it), each a
                 closed run of `clapboard_wall`s with its cased sash and doors under a
                 boxed, bracketed eave and a hip or flat roof; the kit porch on the street
                 wall with its steps; one brick stack
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
# T-2357: the whole-house layout, read instead of the front's five
HOUSE_REQUIRED = ("frame_house",)
HOUSE_OPTIONAL = ("roof_covering",)
CONSUMED = frozenset(REQUIRED + OPTIONAL + HOUSE_REQUIRED)
SIDES = ("east", "north", "west", "south")   # counter-clockwise from above, the walls' order
ROOFS = ("hip", "flat")
KINDS = {"gable": "gable", "wing_wall": "clapboard_wall", "porch": "porch"}
BODY_KEYS = ("gable_depth_m", "wing_depth_m", "wing_roof_pitch_deg", "roof_under_m")


class ParamError(ValueError):
    pass


@dataclass
class K16TimberParams:
    layout: dict | None = None
    gable: dict | None = None
    wing_wall: dict | None = None
    porch: dict | None = None
    body: dict | None = None
    canted_bay: dict | None = None
    roof_covering: dict | None = None
    frame_house: dict | None = None
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]


def from_phase(phase: dict, record: dict | None = None) -> K16TimberParams:
    rid = f"{(record or {}).get('id')}/{phase.get('id')}"
    form = phase.get("form") or {}
    if "frame_house" in form:
        bad = frame_house_errors(form["frame_house"]["value"])
        if bad:
            raise ParamError(f"{rid}: frame_house: {'; '.join(bad)}")
        return K16TimberParams(
            frame_house=dict(form["frame_house"]["value"]),
            **{k: dict(form[k]["value"]) for k in HOUSE_OPTIONAL if k in form},
            confidence={k: form[k]["confidence"] for k in HOUSE_REQUIRED + HOUSE_OPTIONAL if k in form},
        )
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


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def frame_house_errors(fh: dict) -> list[str]:
    """What the whole-house builder cannot read (T-2357). The first block stands free and
    is walled on all four sides; every later block stands `against` one side of it and is
    walled on its other three, the last of them ending on that wall without a corner. A
    house of a pair (T-1867) names its `party_wall` (the side, and the house `with` it): its
    first block stands `against` that side, so the pair's shared wall is built by neither half
    and the eave, the deck and the front and rear walls run on to the partner's."""
    out = []
    if not _num(fh.get("foundation_m")) or fh["foundation_m"] <= 0:
        out.append("foundation_m must be a positive number")
    if not _num(fh.get("return_m")) or not 0.2 <= fh["return_m"] <= 1.0:
        out.append("return_m (each corner's return) must lie in 0.2-1.0 m")
    blocks = fh.get("blocks") or []
    if not blocks:
        out.append("no blocks")
    pw = fh.get("party_wall")
    if pw is not None and (pw.get("side") not in SIDES or not isinstance(pw.get("with"), str) or not pw["with"]
                           or not blocks or blocks[0].get("against") != pw.get("side")):
        out.append("party_wall names a side and the house `with` it, and the first block stands against that side")
    for i, b in enumerate(blocks):
        bid = b.get("id", f"#{i}")
        r = b.get("rect_uv")
        if not (isinstance(r, list) and len(r) == 4 and all(_num(x) for x in r) and r[0] < r[2] and r[1] < r[3]):
            out.append(f"{bid}: rect_uv must be [u0, v0, u1, v1] with u0 < u1 and v0 < v1")
            continue
        if not _num(b.get("wall_top_m")) or b["wall_top_m"] <= fh.get("foundation_m", 0) + 1.0:
            out.append(f"{bid}: wall_top_m must stand a storey above the foundation")
        if (b.get("roof") or {}).get("kind") not in ROOFS:
            out.append(f"{bid}: roof.kind must be one of {', '.join(ROOFS)}")
        against = b.get("against")
        if i == 0 and against and against != (pw or {}).get("side"):
            out.append(f"{bid}: the first block stands free, or against the party wall the record names")
        if i > 0 and against not in SIDES:
            out.append(f"{bid}: a later block names the side it stands against")
        sides = [w.get("side") for w in b.get("walls") or []]
        want = list(SIDES) if not against else [SIDES[(SIDES.index(against) + k) % 4] for k in (1, 2, 3)]
        if sides != want:
            out.append(f"{bid}: walls must run {', '.join(want)} in that order, not {', '.join(map(str, sides))}")
    po = fh.get("porch")
    if po is not None and (po.get("kind") != "porch" or not _num(po.get("half_width_m"))
                           or not _num(po.get("centre_m"))):
        out.append("porch must be a kit 'porch' variant with half_width_m and centre_m")
    ch = fh.get("chimney")
    if ch is not None and not all(_num(ch.get(k)) for k in ("u_m", "v_m", "width_m", "depth_m", "above_ridge_m")):
        out.append("chimney needs u_m, v_m, width_m, depth_m and above_ridge_m")
    return out
