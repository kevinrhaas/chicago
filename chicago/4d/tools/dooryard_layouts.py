"""How one 1835 dooryard garden is laid out inside its fence (T-3476).

The owner, 2026-11-07: *"all of the gardens seem to look identical with identical fencing so
all of those should vary, all of the gardens should be unique, not necessarily wildly
different crops but different sizes and layouts that are sensible for the design of the
property and the family"*. Until then every one of the town's dooryard gardens was the same
28 x 20 ft rectangle with the yards layer's four strips in it.

THE PATTERNS are reconstructed, and none is attested on a Chicago lot. M'Mahon (1806; the
1857 printing, `mmahon_1857_american_gardeners_calendar`) lays a kitchen garden out in
"quarters" divided by walks, with borders round them under the fence for the small fruit and
herbs, and beds about four feet wide for the small crops. The rest is ours: a cottager's plot
as beds across from a single walk, a larger house's as the four-square cross of walks, a log
dwelling's as a patch hoed in hills with a strip of small crops by the gate.
docs/LIBERTIES.md L-t3476-dooryard-gardens.

THE FRAME. A plot is `u` across (0..W, from the lot's left side line looking in from the
street) and `v` back from the house (0..D, 0 the side the gate is in). Every polygon here is
in that frame; `generate_dooryard_pickets.py` carries it into the world.

A bed is `(plan, poly)`; `plan` is the name `tools/plant_gardens.py` plants by. A walk is a
polygon. Nothing here draws or plants; the only randomness is the `rng` the caller seeds
from the lot's id, so a plot is laid out the same on every run.
"""

from __future__ import annotations

INSET_M = 0.3          # beds and walks stand this far inside the fence
WALK_M = 0.9           # a main walk: a barrow's width
ALLEY_M = 0.45         # the path between two beds
BED_M = 1.22           # a 4 ft bed
BORDER_M = 1.2         # the border under the fence, for bushes or herbs

# Which plans a household grows, in the order it would give them ground: the staples first.
STAPLES = ["potato", "roots", "cabbage", "onion_salad", "corn", "pole_bean", "herb", "vines"]
SMALL_FRUIT = ["bushes", "raspberry", "strawberry"]
# A quarter is ground for a crop grown in hills or rows across a block; a bed is a strip.
QUARTER_PLANS = {"corn", "potato", "vines", "pole_bean", "cabbage"}
BED_PLANS = {"roots", "onion_salad", "herb", "cabbage", "strawberry"}


def rect(u0, v0, u1, v1):
    return [[round(u0, 2), round(v0, 2)], [round(u1, 2), round(v0, 2)],
            [round(u1, 2), round(v1, 2)], [round(u0, 2), round(v1, 2)]]


def _area(poly):
    a = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2


def _deal(rng, n, quarters_first=False, big=False):
    """`n` plans for this household, staples before the rest, a little shuffled."""
    staples = STAPLES[:]
    # a family's staples are the same in kind; which comes first in its ground is not
    for i in range(len(staples) - 1):
        if rng.random() < 0.5:
            staples[i], staples[i + 1] = staples[i + 1], staples[i]
    if not big:
        # a small plot grows its corn and vines in the field or not at all
        staples = [p for p in staples if p not in ("vines",)] + ["vines"]
    if quarters_first:
        staples.sort(key=lambda p: 0 if p in QUARTER_PLANS else 1)
    out = []
    while len(out) < n:
        out.extend(staples)
    return out[:n]


def _strips_across(u0, u1, v0, v1, plans, rng, rows):
    """Beds running across (along u) from v0 to v1, each a 4 ft bed or a double one for a
    quarter crop, with alleys between; returns (beds, used plans)."""
    beds, v, k = [], v0, 0
    while k < len(plans):
        plan = plans[k]
        depth = BED_M * (2 if plan in QUARTER_PLANS and rows else 1) * rng.uniform(0.92, 1.12)
        if v + depth > v1 + 0.01:
            depth = v1 - v
            if depth < 0.8:
                break
        beds.append((plan, rect(u0, v, u1, v + depth)))
        v += depth + ALLEY_M
        k += 1
        if v >= v1 - 0.8:
            break
    return beds


def _strips_along(u0, u1, v0, v1, plans, rng):
    """Beds running back from the house (along v) side by side across u0..u1."""
    beds, u, k = [], u0, 0
    while k < len(plans) and u < u1 - 0.8:
        plan = plans[k]
        width = BED_M * (1.6 if plan in QUARTER_PLANS else 1) * rng.uniform(0.92, 1.1)
        width = min(width, u1 - u)
        beds.append((plan, rect(u, v0, u + width, v1)))
        u += width + ALLEY_M
        k += 1
    return beds


def layout(W, D, gate_u, style, rng, *, fruit=True, border_plan=None):
    """The beds and walks of one plot: {'style', 'beds': [(plan, poly)], 'walks': [poly]}.

    `fruit` false is a plot without bushes under its back fence (a first season's ground);
    `border_plan` names what that border grows when it is not the small fruit."""
    lo, hi = INSET_M, W - INSET_M
    top = D - INSET_M
    beds, walks = [], []
    half = WALK_M / 2
    g = min(max(gate_u, lo + half + 0.6), hi - half - 0.6)
    border = fruit and D >= 6.5
    rear = top - BORDER_M if border else top
    if border:
        x = rng.random()
        plan = border_plan or ("bushes" if x < 0.55 else "raspberry" if x < 0.8 else "strawberry")
        beds.append((plan, rect(lo, rear, hi, top)))
        rear -= ALLEY_M

    if style == "centre_walk":
        # one walk from the gate to the rear border, the beds across it on both sides
        walks.append(rect(g - half, 0.0, g + half, rear + (ALLEY_M if border else 0)))
        n = max(2, int((rear - INSET_M) / (BED_M * 1.5 + ALLEY_M)) + 1)
        left = _deal(rng, n, big=W * D > 70)
        right = _deal(rng, n, big=W * D > 70)
        right = right[1:] + right[:1]
        if g - half - ALLEY_M - lo > 1.0:
            beds += _strips_across(lo, g - half - ALLEY_M, INSET_M, rear, left, rng, rows=True)
        if hi - (g + half + ALLEY_M) > 1.0:
            beds += _strips_across(g + half + ALLEY_M, hi, INSET_M, rear, right, rng, rows=True)
    elif style == "four_square":
        # M'Mahon's quarters: the walk in from the gate crossed by one midway, a quarter
        # in each angle, and the small crops in a bed along the front
        walks.append(rect(g - half, 0.0, g + half, rear))
        mid = INSET_M + (rear - INSET_M) * rng.uniform(0.42, 0.58)
        walks.append(rect(lo, mid - half, hi, mid + half))
        plans = _deal(rng, 4, quarters_first=True, big=True)
        rng.shuffle(plans)
        quads = [(lo, INSET_M, g - half - ALLEY_M, mid - half - ALLEY_M),
                 (g + half + ALLEY_M, INSET_M, hi, mid - half - ALLEY_M),
                 (lo, mid + half + ALLEY_M, g - half - ALLEY_M, rear),
                 (g + half + ALLEY_M, mid + half + ALLEY_M, hi, rear)]
        for plan, (a, b, c, d) in zip(plans, quads):
            if c - a < 1.0 or d - b < 1.0:
                continue
            if plan in BED_PLANS and d - b > 2 * BED_M + ALLEY_M:
                # a small crop's quarter is cut in beds
                beds += _strips_across(a, c, b, d, [plan, "roots" if plan != "roots" else "onion_salad",
                                                     "herb" if rng.random() < 0.5 else "cabbage"], rng, rows=False)
            else:
                beds.append((plan, rect(a, b, c, d)))
    elif style == "long_beds":
        # a cross walk inside the gate, the beds running back from it side by side
        walks.append(rect(lo, INSET_M + 0.1, hi, INSET_M + 0.1 + WALK_M * 0.8))
        walks.append(rect(g - half, 0.0, g + half, INSET_M + 0.1))
        v0 = INSET_M + 0.1 + WALK_M * 0.8 + ALLEY_M * 0.6
        n = max(2, int((hi - lo) / (BED_M * 1.3 + ALLEY_M)) + 1)
        beds += _strips_along(lo, hi, v0, rear, _deal(rng, n, big=W * D > 70), rng)
    elif style == "side_walk":
        # the walk runs in along one fence, the beds across from it
        side_left = g < W / 2
        a, b = (lo, lo + WALK_M) if side_left else (hi - WALK_M, hi)
        walks.append(rect(a, 0.0, b, rear))
        walks.append(rect(min(g, a + half) - half, 0.0, max(g, b - half) + half, INSET_M + WALK_M * 0.7))
        u0, u1 = (b + ALLEY_M, hi) if side_left else (lo, a - ALLEY_M)
        n = max(2, int((rear - INSET_M) / (BED_M * 1.5 + ALLEY_M)) + 1)
        beds += _strips_across(u0, u1, INSET_M + WALK_M * 0.7 + ALLEY_M, rear,
                               _deal(rng, n, big=W * D > 70), rng, rows=True)
    elif style == "new_ground":
        # a first season's ground (Peck's 'truck patch'): the sod turned in two or three
        # broad strips across, potatoes in the most of it, cabbages and beans, and only a
        # trodden line in from the gate
        walks.append(rect(g - half * 0.7, 0.0, g + half * 0.7, INSET_M + 0.4))
        plans = ["potato", "potato", "cabbage", "pole_bean"] if rng.random() < 0.5 else ["potato", "cabbage", "potato", "corn"]
        n = 2 if D < 7 else 3
        v, depth = INSET_M + 0.4, (rear - INSET_M - 0.4 - ALLEY_M * (n - 1)) / n
        for k in range(n):
            beds.append((plans[k], rect(lo, v, hi, v + depth)))
            v += depth + ALLEY_M
    elif style == "patch":
        # a log house's ground: one patch in hills (corn, or potatoes, with squash among
        # the corn the way the field was planted), a strip of small crops by the gate
        walks.append(rect(g - half * 0.8, 0.0, g + half * 0.8, INSET_M + BED_M + ALLEY_M))
        strip_top = INSET_M + BED_M
        beds.append(("onion_salad" if rng.random() < 0.5 else "roots", rect(lo, INSET_M, g - half * 0.8 - ALLEY_M, strip_top)))
        beds.append(("cabbage" if rng.random() < 0.6 else "herb", rect(g + half * 0.8 + ALLEY_M, INSET_M, hi, strip_top)))
        v0 = strip_top + ALLEY_M + 0.3
        if rng.random() < 0.6:
            beds.append(("field_corn", rect(lo, v0, hi, rear)))
        else:
            mid = lo + (hi - lo) * rng.uniform(0.45, 0.62)
            beds.append(("field_corn", rect(lo, v0, mid, rear)))
            beds.append(("potato", rect(mid + ALLEY_M, v0, hi, rear)))
    else:
        raise ValueError(f"no layout style {style!r}")

    beds = [(p, poly) for p, poly in beds if _area(poly) >= 0.8]
    return {"style": style, "beds": beds, "walks": walks}


STYLES = ("centre_walk", "four_square", "long_beds", "side_walk", "patch", "new_ground")
