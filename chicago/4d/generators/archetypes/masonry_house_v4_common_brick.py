"""T-3564: the walls the owner's photographs show in buff Chicago common brick.

His photographs of 2026-11-10 (nos. 20-22) show the stable's south wall and the
court wall's tall alley run in a buff-tan common brick with salmon and darker
units; he identified it as Chicago common brick on 2026-11-12. The geometry is
unchanged: after every piece is laid, each brick face whose centre stands in one
of the record's plan areas (v4_detail.common_brick) moves from the court's pink
slots to the common-brick slots, unit for unit, so the kiln split stays the court's.
"""
from __future__ import annotations

from archetypes.masonry_house_v4_materials import BRICK, BRICK_VARIANTS, COMMON_BRICK_SLOTS
from archetypes.masonry_house_v4_finish import FLAT_BRICK

BUFF, SALMON, DARK = COMMON_BRICK_SLOTS
# brick (60 %) and brick_buff (14 %) are buff; brick_dark_red (20 %) salmon;
# brick_smoky (6 %) the dark-burnt unit. The flat-brick plane, where a tier lays
# one, takes the buff body.
REMAP = {BRICK: BUFF, BRICK_VARIANTS[0]: SALMON, BRICK_VARIANTS[1]: BUFF,
         BRICK_VARIANTS[2]: DARK, FLAT_BRICK: BUFF}


def areas(params):
    return params.detail.get('common_brick') or []


def remap(b):
    """Move brick faces inside the record's areas to the common-brick slots."""
    boxes = areas(b.params)
    if not boxes:
        return 0
    moved = 0
    for i, (face, mat) in enumerate(zip(b.faces, b.mat_index)):
        to = REMAP.get(mat)
        if to is None:
            continue
        n = len(face)
        x = sum(b.verts[k][0] for k in face) / n
        y = sum(b.verts[k][1] for k in face) / n
        if any(a['x0'] <= x <= a['x1'] and a['y0'] <= y <= a['y1'] for a in boxes):
            b.mat_index[i] = to
            moved += 1
    if moved == 0:
        raise ValueError('Common-brick areas cover no brick face')
    b.common_brick_faces = moved
    return moved
