"""A bounded, open masonry worksite for the Lake House in July 1835.

This is not a reconstruction of the completed hotel shown in the 1856 print.
No July picture or notice counts its bays or measures its walls. The construction
notice of 10 June 1835 supports work in progress; the dimensions, seven work bays,
uneven wall heights and working platforms below are declared reconstruction.
Only the explicit construction_site opt-in calls this builder. Existing fort
buildings continue through fort_structure._building unchanged.
"""
from __future__ import annotations


def build(b, p, timber_mat: int = 4) -> None:
    """Emit thick, genuinely open brick walls and two interior working stages.

    Keep every part inside the committed 24 by 15 m footprint, at grade and
    below the existing 4 m maximum. Materials use the parent's wall slot (0)
    and an explicitly appended timber slot. Nothing fills a doorway with a
    dark surface, and nothing caps the open interior or represents excavation.
    """
    w, d, h = p.width_m, p.depth_m, p.wall_height_m
    t = 0.46
    c = p.conf("construction_site", "reconstructed")

    def box(x0, y0, z0, x1, y1, z1, mat=0):
        if x1 > x0 and y1 > y0 and z1 > z0:
            b.add_box(x0, y0, z0, x1, y1, z1, c, mat)

    # A two-wythe-scale working wall, not a zero-thickness magazine surface.
    # Sills and piers are raised before the openings are bridged. Seven bays
    # are a chosen workable rhythm for this plan, not a count in a source.
    count = 7
    pitch = w / count
    opening = min(1.55, pitch * .48)
    for i in range(count):
        x0, x1 = i * pitch, (i + 1) * pitch
        a, z = (x0 + x1 - opening) / 2, (x0 + x1 + opening) / 2
        top = h * (1.0 if i < 3 else .82 if i < 5 else .61)
        door = i == count // 2
        sill = 0.0 if door else .85
        box(x0, d-t, 0, a, d, top)
        box(z, d-t, 0, x1, d, top)
        box(a, d-t, 0, z, d, min(sill, top))
        # Only the first three bays have their brickwork carried across.
        if i < 3:
            box(a, d-t, 2.65, z, d, top)

    # The opposite working front has reached a lower, stepped lift. A broad
    # break is left for moving material; there is no invented completed door.
    box(t, 0, 0, w*.43, t, h*.52)
    box(w*.43+2.0, 0, 0, w*.72, t, h*.40)
    box(w*.72, 0, 0, w-t, t, h*.30)
    # Side walls stair down toward that lower back lift.
    for side in (0.0, w-t):
        for j, fraction in enumerate((.52, .65, .80, 1.0)):
            y0, y1 = t + (d-2*t)*j/4, t + (d-2*t)*(j+1)/4
            if side > 0:
                fraction *= .70
            box(side, y0, 0, side+t, y1, h*fraction)

    # Two short, timber working stages stand INSIDE the walls. Vertical
    # standards, ledgers and separate deck planks explain how the higher lift
    # can be worked; no cranes, workers, masonry bond or historic tool is claimed.
    for x0, x1 in ((.8, w*.42), (w*.51, w*.81)):
        y0, y1, deck = d-2.1, d-.72, 1.65
        for x in (x0, (x0+x1)/2, x1):
            for y in (y0, y1):
                box(x-.065, y-.065, 0, x+.065, y+.065, deck+.20, timber_mat)
        for y in (y0, y1):
            box(x0-.10, y-.065, deck-.18, x1+.10, y+.065, deck-.04, timber_mat)
        for k in range(6):
            y = y0 + k*(y1-y0)/6
            box(x0-.12, y, deck, x1+.12, y+(y1-y0)/6-.012, deck+.055, timber_mat)
