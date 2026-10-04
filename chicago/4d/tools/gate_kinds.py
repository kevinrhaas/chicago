"""What hangs in a fence's gateway (T-2112) — one rule for every fence layer that has one.

The owner, 2026-10-04: *"if someone has a property and the fence runs the front of the
property they should have a gate or opening, i imagine a gate is period appropriate ...
vary by property what kind of gate/opening entrance they have based on correct 1835"*.

THE KINDS, and what each stands on. None of them is attested on any Chicago lot; they are
the gates the town's own fence types imply, graded `reconstructed` at docs/LIBERTIES.md L380.

  * `foot_gate` — one hung leaf, about 3 ft 6 in, in front of a dwelling's door. A board
    or paled fence on a house lot was a yard kept against hogs that ran at large (the
    1833 town code, `chicago_democrat_1833_11_26`), so its way in shut.
  * `carriage_gate` — a pair of leaves, a cart's width, on a trade lot's street line and
    on a yard's alley or street gateway: where a cart or a dray came in.
  * `bars` — slip bars: the rails of a split-rail fence slid out of slotted posts and laid
    down, the way into a rail-fenced lot on the edge of every Western town. No leaf.
  * `opening` — a gap with no gate hung, or the gate long gone.

VARIETY IS A HASH, NOT A DIE. Whether a gate stands shut, ajar or open, which side it is
hung on and, for a house gate, whether its leaf is boarded or paled, is read off a hash
of the opening's own id, so the record re-derives byte for byte and two neighbours do not
match by construction.
"""

from __future__ import annotations

import hashlib

FOOT_GATE_W_M = 1.067       # 3 ft 6 in: a person and a basket, not a cart
CARRIAGE_GATE_W_M = 2.743   # 9 ft: a team and a wagon between the posts


def _unit(seed: str, salt: str) -> float:
    """A stable number in [0, 1) for this gate and this question."""
    h = hashlib.sha1(f"{seed}|{salt}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) / 0x100000000


def _swing(seed: str, shut: float, ajar: float) -> float:
    """Degrees the leaf stands open: shut with probability `shut`, ajar with `ajar`,
    otherwise standing open against its stop."""
    u = _unit(seed, "swing")
    if u < shut:
        return 0.0
    if u < shut + ajar:
        return round(12 + 30 * _unit(seed, "ajar"), 1)
    return round(70 + 20 * _unit(seed, "open"), 1)


def gate_for(seed: str, use: str, fence_stock: str) -> dict:
    """The gate for one gateway.

    `use` is `dwelling` (a house's way in from the street), `trade` (a working lot's way
    in from the street) or `yard` (a 10 ft cart gateway on an alley or street line).
    `fence_stock` is the fence it hangs in: `board`, `picket` or `rail`.
    """
    if use == "yard" and _unit(seed, "hung") < 0.15:
        return {"kind": "opening", "leaves": 0}
    if fence_stock == "rail":
        if use == "dwelling":
            # A house gate even in a rail fence: a light paled leaf on its own posts.
            return {"kind": "foot_gate", "leaves": 1, "leaf_stock": "picket",
                    "hinge": "a" if _unit(seed, "hinge") < 0.5 else "b",
                    "swing_deg": _swing(seed, 0.45, 0.3)}
        down = 3 if _unit(seed, "bars") < 0.6 else 2
        return {"kind": "bars", "leaves": 0, "bars_down": down}
    if use == "dwelling":
        stock = "picket" if _unit(seed, "stock") < 0.4 or fence_stock == "picket" else "board"
        return {"kind": "foot_gate", "leaves": 1, "leaf_stock": stock,
                "hinge": "a" if _unit(seed, "hinge") < 0.5 else "b",
                "swing_deg": _swing(seed, 0.5, 0.3)}
    # A pair of leaves. Each stands on its own: a yard gate left with one leaf back is the
    # commonest thing in a working town.
    return {"kind": "carriage_gate", "leaves": 2, "leaf_stock": fence_stock,
            "swing_deg": [_swing(seed + "|a", 0.35, 0.2), _swing(seed + "|b", 0.35, 0.2)]}
