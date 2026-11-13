"""monument_params — a bronze group on a granite pedestal (T-3567).

The first and only record is Carl Rohl-Smith's *The Fort Dearborn Massacre* (1893),
which stood on 18th Street by Calumet Avenue from 1893 to 1931
(data/structures/fort_dearborn_massacre_monument_1893.json). The pedestal is read off
its photographs as a stack of granite masses, bottom to top:

    base    the stage: one wide low block whose top `base_wash_m` is washed (sloped) in
            from its outer edge to a ledge 0.12 m round the plinth
    plinth  the second step, with a moulded top edge
    die     the block that carries a bronze panel on each face and the lettering
    cap     the moulded cornice over the die
    rock    the cast bronze ground the group stands on
    group   the figures (built by `generators/archetypes/monument.py`, its poses there)

Every dimension is a form attribute on the record, with its confidence and the reading
it rests on; the defaults below are only what an attribute missing from a record gets.
The footprint is the base's rectangle from its own (0, 0): u east along the front, v
north, the front facing -v (the street).
"""

from __future__ import annotations

import math
import zlib
from dataclasses import dataclass, field

#: Every form attribute the generator reads (tools/validate.py holds a record's other
#: attributes to a `build_status`).
CONSUMED = {
    "base_w_m", "base_d_m", "base_h_m", "base_wash_m",
    "plinth_w_m", "plinth_d_m", "plinth_h_m",
    "die_w_m", "die_d_m", "die_h_m",
    "cap_h_m", "cap_overhang_m",
    "rock_h_m", "group_h_m", "panels",
}

DEFAULTS = {
    "base_w_m": 3.5, "base_d_m": 3.0, "base_h_m": 0.85, "base_wash_m": 0.25,
    "plinth_w_m": 2.8, "plinth_d_m": 2.3, "plinth_h_m": 0.5,
    "die_w_m": 2.4, "die_d_m": 1.9, "die_h_m": 1.3,
    "cap_h_m": 0.4, "cap_overhang_m": 0.12,
    "rock_h_m": 0.3, "group_h_m": 2.75, "panels": 4,
}

#: docs/GLB-CONTRACT.md § The confidence channel: 0 attested, 1 reconstructed.
CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}


class ParamError(ValueError):
    """A record the monument generator cannot build."""


@dataclass
class MonumentParams:
    side_w_m: float
    side_d_m: float
    base_w_m: float
    base_d_m: float
    base_h_m: float
    base_wash_m: float
    plinth_w_m: float
    plinth_d_m: float
    plinth_h_m: float
    die_w_m: float
    die_d_m: float
    die_h_m: float
    cap_h_m: float
    cap_overhang_m: float
    rock_h_m: float
    group_h_m: float
    panels: int
    seed: int = 0
    confidence: dict = field(default_factory=dict)

    def validate(self) -> None:
        if not (self.base_w_m >= self.plinth_w_m > self.die_w_m > 0):
            raise ParamError("the steps must narrow upward: base >= plinth > die in width")
        if not (self.base_d_m >= self.plinth_d_m > self.die_d_m > 0):
            raise ParamError("the steps must narrow upward: base >= plinth > die in depth")
        if self.base_wash_m >= self.base_h_m:
            raise ParamError("the base's wash must be lower than the base")
        for name in ("base_h_m", "plinth_h_m", "die_h_m", "cap_h_m", "rock_h_m", "group_h_m"):
            if getattr(self, name) <= 0:
                raise ParamError(f"{name} must be positive")
        if self.panels not in (0, 1, 2, 4):
            raise ParamError("panels is how many die faces carry a bronze panel: 0, 1, 2 or 4")
        if abs(self.side_w_m - self.base_w_m) > 0.01 or abs(self.side_d_m - self.base_d_m) > 0.01:
            raise ParamError(f"the footprint ({self.side_w_m} x {self.side_d_m} m) must be the "
                             f"base's rectangle ({self.base_w_m} x {self.base_d_m} m)")

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the rule from docs/GLB-CONTRACT.md."""
        return max((self.conf(a) for a in attrs), default=1.0)

    @property
    def pedestal_h_m(self) -> float:
        return self.base_h_m + self.plinth_h_m + self.die_h_m + self.cap_h_m


def from_phase(phase: dict, record: dict | None = None) -> MonumentParams:
    """Resolve one structure phase into generator parameters."""
    form = phase.get("form", {})

    def val(attr):
        a = form.get(attr)
        return DEFAULTS[attr] if a is None else a.get("value", DEFAULTS[attr])

    poly = (phase.get("footprint") or {}).get("polygon") or []
    if len(poly) < 3:
        raise ParamError("a monument needs its base's rectangle as a footprint")
    us = [float(p[0]) for p in poly]
    vs = [float(p[1]) for p in poly]
    if not (math.isclose(min(us), 0.0, abs_tol=1e-9) and math.isclose(min(vs), 0.0, abs_tol=1e-9)):
        raise ParamError("a monument's footprint must start at its own (0, 0)")
    params = MonumentParams(
        side_w_m=max(us), side_d_m=max(vs),
        base_w_m=float(val("base_w_m")), base_d_m=float(val("base_d_m")),
        base_h_m=float(val("base_h_m")), base_wash_m=float(val("base_wash_m")),
        plinth_w_m=float(val("plinth_w_m")), plinth_d_m=float(val("plinth_d_m")),
        plinth_h_m=float(val("plinth_h_m")),
        die_w_m=float(val("die_w_m")), die_d_m=float(val("die_d_m")), die_h_m=float(val("die_h_m")),
        cap_h_m=float(val("cap_h_m")), cap_overhang_m=float(val("cap_overhang_m")),
        rock_h_m=float(val("rock_h_m")), group_h_m=float(val("group_h_m")),
        panels=int(val("panels")),
        seed=zlib.crc32(str((record or {}).get("id", "")).encode()),
        confidence={n: form[n].get("confidence", "reconstructed") for n in sorted(CONSUMED) if n in form},
    )
    for n, v in params.confidence.items():
        if v not in CONFIDENCE_VALUE:
            raise ParamError(f"{n}: confidence {v!r} is not one of {sorted(CONFIDENCE_VALUE)}")
    params.validate()
    return params
