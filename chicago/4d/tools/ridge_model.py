#!/usr/bin/env python3
"""Which horizontal run a roof climbs, per archetype — the one thing a pitch needs
before it can be gated on the ridge it produces.

WHY THIS EXISTS (T-0145). `tools/family_bands.py` samples a pitch inside the family's
authored `N:12-M:12` band and wants to keep the resulting ridge inside the family's
authored `ridge_ft` band. The ridge is `eave + run x tan(pitch)`, and the `run` is the
only part of that the crosswalk does not author: it is the archetype's, because the
archetype decides which way the ridge points and whether a plane covers half the span
or all of it. So the run is named here, once, for the five archetypes the reconstructed
parcels instantiate.

THIS FILE DUPLICATES ARCHETYPE ARITHMETIC AND THAT IS ONLY SAFE BECAUSE IT IS CHECKED.
Retyping a rule into a second file is the exact fault `tools/family_bands.py` was
written to end. What makes it defensible here is that the copy cannot drift in silence:
`tools/measure_ridge_band.py` computes the ridge from THIS model and reads the ridge the
committed GLB actually carries — the top of the `roof` material, which is the ridge and
not the chimney over it — and fails when the two disagree by more than the roof's own
board thickness. The model is a claim about the generators and the gate tests it every
commit. If an archetype changes how its roof is set out, the gate goes red here before
anything downstream believes a wrong number.

WHAT EACH ARCHETYPE DOES, and where it does it:

  frame_dwelling      `_roof` -> `MeshBuilder.add_gable_roof(..., ridge_along_x=True)`.
                      "The ridge runs parallel to the facade, always" — the module says
                      so in as many words — so the span is the DEPTH, and `add_gable_roof`
                      grows the rectangle by its overhang on all four sides BEFORE it
                      raises the ridge, so the run is (depth + 2 x overhang) / 2.
  frame_tavern        `ridge_along_x=(w >= d)` — the ridge runs down the LONG axis, so
                      the span is the short one, grown the same way.
  log_dwelling        `_ridge_along_x(x0, y0, x1, y1)` is `(x1-x0) >= (y1-y0)`: the same
                      long-axis rule, so the span is the short one.
  frame_storefront    `_ridge_along_x(p)` is `not p.gable_front`, so the RECORD decides:
                      a gable front turns the ridge across the plan (span = depth), and
                      eaves to the street leaves it along the plan (span = width)... and
                      it is the other way round from how it reads, because
                      `ridge_along_x=True` means the ridge runs along x and the roof
                      therefore falls across y. Span = DEPTH when `gable_front` is false,
                      WIDTH when it is true.
  outbuilding         its OWN roof builder, and the one that does not grow the plan:
                      "THE OVERHANG CONTINUES THE SLOPE rather than being pinned at the
                      eave height". For its GABLE that costs nothing — the apex stands
                      over the building's own centre line and the overhang falls away
                      from it on both sides — so the run is half the span across the
                      ridge. For its SHED it costs `oh x tan(pitch)`, because a single
                      plane running from -oh to span+oh is still climbing when it gets
                      there, so the run is the whole span PLUS the overhang (T-0274).
                      `ridge_along_x` is `width >= depth`, the long-axis rule.

A shed roof has no ridge; its high eave is what `ridge_ft` has to be read against, and
the run is the whole span rather than half of it.

WHICH span, and this is the correction T-0179 made. A shed is not a gable with one
plane deleted, and it does not point where the gable points:

  * `frame_dwelling`, `frame_storefront` and `log_dwelling` each build their shed with
    a private `_shed_roof` that falls "from the back wall to the facade" — always along
    y, and it never consults `ridge_along_x` or `gable_front` at all. This model used to
    turn the shed's span with `gable_front` the way it turns the gable's, which was
    simply wrong about the mesh: a C1 storefront is dealt `gable_front=True`, so the
    model climbed its 14-20 ft WIDTH while the archetype climbs its 20-30 ft DEPTH.
    Nothing caught it because no committed GLB in this dataset is a storefront shed, so
    `tools/measure_ridge_band.py` — which is what keeps this file honest — had no roof
    to compare against. The span is the DEPTH, always, for all three.
  * `frame_tavern` has no shed branch at all: it never reads `roof_type` for its roof.
    A record that says shed gets a gable, so that is what this returns for it.
  * `outbuilding` is the one archetype where the shed's axis is a claim the RECORD
    makes: `shed_axis` derives it from the open sides (L73), so an open long side puts
    the fall across the short span and a closed shell falls front-to-back. The rule is
    imported from the archetype rather than retyped here, and `open_sides` is passed in.

That last one is the whole of the F4 finding: a lumber shed 24x45-36x70 ft cannot reach
its own 17-24 ft ridge band falling down its 45-70 ft length at any pitch, and reaches it
at every footprint in its band falling across its 24-36 ft width — which is the axis its
own crosswalk entry's "part-open sides" produces.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "generators"))

from archetypes.outbuilding_params import (  # noqa: E402
    eave_overhang_m, shed_axis_for,
)

# `MeshBuilder.add_gable_roof`'s default overhang, which `frame_tavern` and
# `frame_storefront` already name as a constant of their own for the same reason. The
# three private `_shed_roof` builders grow the plan by the same 0.25 m before they raise
# the slope, so a shed's run carries it too.
GABLE_OVERHANG_M = 0.25

# The archetypes that have a shed branch at all. `frame_tavern` does not read
# `roof_type` when it roofs, so a shed asked of it is built as a gable.
SHED_ARCHETYPES = ("frame_dwelling", "frame_storefront", "log_dwelling", "outbuilding")

# The archetypes whose roof is built by `MeshBuilder.add_gable_roof`, and how each
# decides which way the ridge points. `True` means the ridge runs along x, so the roof
# falls across y and the span is the DEPTH.
def _ridge_along_x(archetype: str, width_m: float, depth_m: float,
                   gable_front: bool | None) -> bool:
    if archetype == "frame_dwelling":
        return True                                   # parallel to the facade, always
    if archetype == "frame_storefront":
        return not bool(gable_front)                  # the record decides
    return width_m >= depth_m                         # frame_tavern, log_dwelling


def ridge_run_m(archetype: str, roof_type: str, width_m: float, depth_m: float,
                gable_front: bool | None = None,
                open_sides: tuple | list = ()) -> float | None:
    """The horizontal distance from the eave to the ridge, or None if not modelled.

    `open_sides` is read only by `outbuilding`, and only for a shed, because that is the
    only place in this dataset where the record decides which way a roof plane falls.
    It defaults to the closed shell every reconstructed anonymous outbuilding is dealt
    today, so every existing caller keeps the number it had.
    """
    is_shed = roof_type == "shed" and archetype in SHED_ARCHETYPES
    if archetype == "outbuilding":
        if is_shed:
            # The archetype's own rule, imported: an open long side puts the fall across
            # the SHORT span, a closed shell falls front-to-back down the depth.
            span = depth_m if shed_axis_for(open_sides) == "y" else width_m
            # ...AND THE OVERHANG IS PART OF THE RUN ON A SHED, which the paragraph
            # about `outbuilding` in the module note above had exactly backwards
            # (T-0274). "The overhang continues the slope rather than being pinned at
            # the eave height" is true of both of this archetype's roofs, and for a
            # GABLE it costs nothing because the apex stands over the centre line and
            # the overhang falls away from it on both sides. A shed has no centre line:
            # its single plane runs from -oh to span+oh and keeps climbing the whole
            # way, so its highest point is `oh` further along the slope than the high
            # wall. Left out, the modelled ridge was short by `oh x tan(pitch)` on every
            # shed in the dataset — 0.08 m at 12 degrees and 0.15 m at 25, which
            # `tools/measure_ridge_band.py` had been absorbing in the board-thickness
            # tolerance it compares the built GLB with until a steeper shed outgrew it.
            return span + eave_overhang_m(width_m, depth_m)
        # `ridge_along_x = width >= depth`; the ridge runs down the long axis, so the
        # plane covers half of the SHORT one.
        return (depth_m if width_m >= depth_m else width_m) / 2.0
    if archetype not in ("frame_dwelling", "frame_tavern", "frame_storefront",
                         "log_dwelling"):
        return None
    if is_shed:
        # All three private `_shed_roof` builders fall from the back wall to the facade
        # and never consult the gable's orientation, so the span is the depth whatever
        # `gable_front` says. See the module docstring.
        return depth_m + 2 * GABLE_OVERHANG_M
    along_x = _ridge_along_x(archetype, width_m, depth_m, gable_front)
    return ((depth_m if along_x else width_m) + 2 * GABLE_OVERHANG_M) / 2.0
