"""landmark_1871_params — the 1871 fire landmarks' masonry compositions (T-3688).

A landmark of the pre-fire city (the Court House, the great hotels, the Chamber of
Commerce, Crosby's Opera House, the State Street stores) is not a row house: it is a
composition of rectangular masses, each with its own storeys, its own bay rhythm on each
face, its own cornice and roof, and towers, pediments and porches set on them. The record
carries that composition as one form attribute, `composition`, read off the building's
pictures and texts (each element says which in the record's note), and the generator
(`generators/archetypes/landmark_1871.py`) lays it in the 1904 kits' materials: the K02
stone library's Lemont limestone and dressed trim, the K03 brick panels, the K04 slates
and tin, K06-style sash and glass.

The frame: the footprint polygon's own origin, x (u) east, y (v) north, z up, metres; the
record's `rotation_deg` turns the whole onto the 1870 grid. Every block is an axis-aligned
box in that frame. A face is named by the way it looks: S faces -y, N +y, E +x, W -x; a
distance `s` along a face runs left to right as a visitor standing in front of it sees it.

This module only resolves and refuses; it makes no geometry.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

#: The form attributes that reach the mesh. A record's other attributes (its stone named in
#: words, its storey count, its height in feet) are the evidence the composition was read
#: against and are stated, not built twice.
CONSUMED = {"composition"}

#: the fabrics a composition may name, each the 1904 kit's own (see landmark_1871.MATERIALS)
WALLS = ("marble", "lockport_marble", "limestone", "brick_red", "brick_cream", "iron_stone",
         "lockport_weathered", "limestone_pale", "clapboard", "clapboard_bare", "boards", "sod", "sand",
         "limestone_rubble", "wrought_iron")
ROOFS = ("slate", "tin", "tin_dark", "shingle", "stone_trim", "sod", "sand", "rubble_stone", "wrought_iron")
OPENINGS = ("flat", "segment", "round", "pair_round", "store", "door_round", "door_flat",
            "oculus", "blank", "pointed", "door_pointed")
HOODS = ("none", "cornice", "arch", "pediment", "segment", "crown")
CAPS = ("dome", "bell", "pyramid", "flat", "lantern_dome")
FACES = ("S", "N", "E", "W")


class ParamError(ValueError):
    """A composition the landmark generator cannot build."""


@dataclass
class LandmarkParams:
    composition: dict
    footprint: list
    seed: int = 0
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def validate(self) -> None:
        c = self.composition
        blocks = c.get("blocks") or []
        if not blocks:
            raise ParamError("a landmark needs at least one block")
        for i, b in enumerate(blocks):
            where = f"blocks[{i}] ({b.get('name', '?')})"
            x0, y0, x1, y1 = b["box"]
            if not (x1 - x0 > 0.2 and y1 - y0 > 0.2):
                raise ParamError(f"{where}: box must be at least 0.2 m each way (a pavilion breaks forward that little)")
            if not (x1 - x0 < 120 and y1 - y0 < 120):
                raise ParamError(f"{where}: box over 120 m — no 1871 building was that long")
            st = b.get("storeys") or []
            if not st or any(not (0.15 <= h <= 15.0) for h in st):
                raise ParamError(f"{where}: storey heights must each be 0.15-15 m (a grave's mound or a "
                                 f"frame cottage's floor raised on posts is a storey; a hall storey, like "
                                 f"the Chamber of Commerce's exchange room, is one)")
            if b.get("wall", "limestone") not in WALLS:
                raise ParamError(f"{where}: wall {b.get('wall')!r} is not one of {WALLS}")
            roof = b.get("roof") or {"kind": "flat"}
            if roof.get("kind") not in ("flat", "mansard", "hip", "gable"):
                raise ParamError(f"{where}: roof kind must be flat, mansard, hip or gable")
            if roof.get("kind") == "gable" and roof.get("ridge", "x") not in ("x", "y"):
                raise ParamError(f"{where}: a gable's ridge runs along x or y")
            if roof.get("covering", "slate") not in ROOFS:
                raise ParamError(f"{where}: roof covering must be one of {ROOFS}")
            for fk, f in (b.get("faces") or {}).items():
                if fk not in FACES:
                    raise ParamError(f"{where}: face {fk!r} is not one of {FACES}")
                if f in ("none", "blank"):
                    continue
                fst = f.get("levels") or st
                if abs(sum(fst) - sum(st)) > 0.01:
                    raise ParamError(f"{where} face {fk}: its levels {fst} must rise to the "
                                     f"block's wall head ({sum(st)} m)")
                for k, o in enumerate(f.get("storeys") or []):
                    if o is None:
                        continue
                    if o.get("kind", "flat") not in OPENINGS:
                        raise ParamError(f"{where} face {fk} storey {k}: opening kind "
                                         f"{o.get('kind')!r} is not one of {OPENINGS}")
                    if o.get("hood", "none") not in HOODS:
                        raise ParamError(f"{where} face {fk} storey {k}: hood "
                                         f"{o.get('hood')!r} is not one of {HOODS}")
                    if o.get("kind") != "blank" and k < len(fst):
                        if o.get("sill", 0.9) + o.get("h", 2.4) > fst[k] + 0.01:
                            raise ParamError(f"{where} face {fk} storey {k}: an opening "
                                             f"{o.get('sill', 0.9)} + {o.get('h', 2.4)} m does "
                                             f"not fit its {fst[k]} m storey")
        for i, t in enumerate(c.get("towers") or []):
            if (t.get("cap") or {}).get("kind", "dome") not in CAPS:
                raise ParamError(f"towers[{i}]: cap must be one of {CAPS}")
            if not t.get("stages"):
                raise ParamError(f"towers[{i}]: a tower needs at least one stage")


def from_phase(phase: dict, record: dict | None = None) -> LandmarkParams:
    form = phase.get("form") or {}
    comp = form.get("composition")
    if not isinstance(comp, dict) or not isinstance(comp.get("value"), dict):
        raise ParamError("form.composition must carry the building's composition as its value")
    confidence = {k: form[k].get("confidence", "reconstructed") for k in sorted(CONSUMED) if k in form}
    sid = (record or {}).get("id", "")
    seed = sum((i + 1) * ord(ch) for i, ch in enumerate(sid)) % 100003
    p = LandmarkParams(composition=copy.deepcopy(comp["value"]),
                       footprint=[list(map(float, q)) for q in phase["footprint"]["polygon"]],
                       seed=seed, confidence=confidence)
    p.validate()
    return p
