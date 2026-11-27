"""T-3713: a K01 mansard stopped short of a side wall, the strip beyond it under a railed flat deck — 2115 Prairie.

TICKET T-3713 (piece 2 of T-1925, the image-gate sign-off of the Kelley/Armour house). K05's mansard
(T-2370) rings all four walls of the main body, so 2115's slated mansard ran on past its south
pavilion to the south wall. Both pictures of the house draw that stretch otherwise: in the Armour
photograph the front south of the pavilion's crown stands under no mansard, and in the Tribune's
1928 halftone the roof line there drops from the crown to a pale railing at the cornice, sky
showing over it. The main mansard ends against the crown; the strip of the body beyond it is
roofed flat at the wall head and railed.

The record names it as its mansard's `short_end`:

  resolve()     bounded: the wall the strip runs along (`north` only, the high-v wall, which is
                2115's real south: K01 counts its v from the real north there), the strip's width
                `width_m` in from that wall's face, and its `balustrade` (height, plinth, rail,
                baluster bar and pitch, thickness, inset from the fascia). The mansard is then
                resolved as if the body stopped `width_m` short of that wall (k01_frontage_params:
                its ring, deck, crown, dormers and stacks are read on the narrower plan)
  deck()        the strip's roof, one solid joined into the mansard's union: the eave's own box
                (soffit at the cornice's soffit, fascia, the tin deck at the wall head) carried
                `overhang` past the strip's three outer walls and run on into the mansard's end,
                where the mansard's own eave box buries its inner end; so the cornice's top is
                unbroken round the corner and the mansard's end face rises off the deck
  balustrade()  the railing on the deck's three outer edges (street, side, rear), in the front's
                trim stone: a plinth, square balusters at `pitch_m`, a rail, and a square die at
                each outer corner; each run's inner end stopped at the mansard's foot

docs/LIBERTIES.md L-k01-2115-armour-3712 says which numbers are read and which reconstructed.
"""

from __future__ import annotations

WALLS = ("north",)
WIDTH_M = (1.0, 4.0)          # the strip's width, from the wall's face in
BAL = {                       # the balustrade's numbers and their bounds
    "height_m": (0.6, 1.2),   # plinth to the rail's top
    "plinth_m": (0.08, 0.3),
    "rail_m": (0.08, 0.3),
    "bar_m": (0.06, 0.2),     # a baluster's square
    "pitch_m": (0.15, 0.6),   # baluster centres
    "thickness_m": (0.15, 0.4),   # the plinth's and the rail's
    "inset_m": (0.0, 0.3),    # its outer face inside the fascia's
}


def _err(msg):
    from .k01_frontage_params import ParamError
    return ParamError(f"mansard.short_end: {msg}")


def resolve(se: dict, *, width: float, overhang: float) -> dict:
    if not isinstance(se, dict) or set(se) != {"wall", "width_m", "balustrade"}:
        raise _err("takes wall, width_m and balustrade")
    if se["wall"] not in WALLS:
        raise _err(f"wall {se['wall']!r}: one of {', '.join(WALLS)} (the high-v side wall)")
    w = float(se["width_m"])
    if not WIDTH_M[0] <= w <= min(WIDTH_M[1], width / 3):
        raise _err(f"width_m {w}: {WIDTH_M[0]}-{WIDTH_M[1]} m, and no more than a third of the {width} m front")
    b = se["balustrade"]
    if not isinstance(b, dict) or set(b) != set(BAL):
        raise _err(f"balustrade takes {', '.join(BAL)}")
    bal = {}
    for k, (lo, hi) in BAL.items():
        x = float(b[k])
        if not lo <= x <= hi:
            raise _err(f"balustrade.{k} {x}: {lo}-{hi} m")
        bal[k] = x
    if bal["plinth_m"] + bal["rail_m"] > bal["height_m"] - 0.3:
        raise _err("balustrade: its plinth and rail leave the balusters under 0.3 m")
    if bal["bar_m"] >= bal["thickness_m"] or bal["pitch_m"] < bal["bar_m"] + 0.05:
        raise _err("balustrade: a baluster is thinner than the rail and stands at least 0.05 m clear of the next")
    if bal["inset_m"] + bal["thickness_m"] > overhang + 0.3:
        raise _err(f"balustrade: its back stands within 0.3 m behind the wall's face (the {overhang} m eave)")
    return {"wall": se["wall"], "width_m": w, "balustrade": bal}


def deck(k5, se, D, W, E, yf, o):
    """The strip's eave box and deck, one closed solid: (u, y) section extruded along z, from
    the outer fascia (z = -W - o) to the mansard's end ring line (z = -W + w), whose own eave box
    holds that end inside the union."""
    w = se["width_m"]
    return k5.extrude([(-o, yf), (D + o, yf), (D + o, E), (-o, E)], -W - o, -W + w, k5.frame("z"),
                      lambda i, p_, q_: ("soffit", "fascia", "covering", "fascia")[i], "fascia", "hidden")


def _runs(se, D, W, o):
    """The balustrade's three runs as frames ((origin, R, N), s0, s1): R along the run, N out of
    the house, the run's outer face on N's plane at 0. The inner ends stop at the mansard's foot
    (its eave box's outer line, `o` past the end ring line)."""
    b = se["balustrade"]
    t, ins = b["thickness_m"], b["inset_m"]
    w = se["width_m"]
    vf = W - w + o                     # the mansard's foot along the strip's street and rear edges
    vo = W + o - ins                   # the side run's outer face
    uf, ur = D + o - ins, -o + ins     # the street and rear runs' outer faces
    return [
        # street: s is v (from 0), N out to the street (+u); its back is `t` inside
        (((uf - t, 0.0, 0.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0)), vf, vo, "street"),
        # the side: s is u back from the front, N out past the wall (-z)
        (((0.0, 0.0, -(vo - t)), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0)), ur, uf, "side"),
        # rear: s is v, N out past the rear (-u)
        (((ur + t, 0.0, 0.0), (0.0, 0.0, -1.0), (-1.0, 0.0, 0.0)), vf, vo, "rear"),
    ]


def balustrade(a, se, D, W, E, o, seed, conf):
    """The deck's railing, in the front's trim stone (k01_frontage.proud_box, as flat_balustrade)."""
    b = se["balustrade"]
    t, h, pl, rl, bar, pitch = (b[k] for k in ("thickness_m", "height_m", "plinth_m", "rail_m", "bar_m", "pitch_m"))
    mat = "limestone_trim"
    die = t + 0.1                      # the corner dies' square
    for frame, s0, s1, name in _runs(se, D, W, o):
        O, R, N = frame
        # the frame's own origin carries the run's back at d = 0 out to its face at d = t
        a.proud_box(mat, frame, s0, s1, E, E + pl, t, seed, conf)
        a.proud_box(mat, frame, s0, s1, E + h - rl, E + h, t, seed, conf)
        # the balusters between the dies (or the mansard's foot), centred in the thickness
        lo = s0 + (die if name == "side" else 0.05)
        hi = s1 - die
        n = max(1, round((hi - lo) / pitch))
        step = (hi - lo) / n
        off = (t - bar) / 2
        inner = (tuple(O[i] + N[i] * off for i in range(3)), R, N)
        for i in range(n + 1):
            x = lo + i * step
            a.proud_box(mat, inner, x - bar / 2, x + bar / 2, E + pl, E + h - rl, bar, seed, conf)
    # a die at each outer corner, standing a little proud of the rail
    uf, ur, vo = D + o - b["inset_m"], -o + b["inset_m"], W + o - b["inset_m"]
    for u_out, sgn in ((uf, 1.0), (ur, -1.0)):
        u0 = u_out - die if sgn > 0 else u_out
        frame = ((0.0, 0.0, -(vo - die)), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
        a.proud_box(mat, frame, u0, u0 + die, E, E + h + 0.08, die, seed, conf)
