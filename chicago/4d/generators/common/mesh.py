"""Shared bpy mesh helpers.

Everything here builds raw vertex/face lists and hands them to Blender in one go,
rather than using bpy.ops. Operators depend on selection state, the active object,
and the current mode — all of which are global and all of which make a generator
non-deterministic the moment two archetypes run in the same session.

Every builder returns geometry tagged with a confidence value per vertex, because
the confidence channel is not an afterthought that gets applied later; it is a
property of the geometry at the moment it is created, and the generator is the only
thing that knows it. See docs/GLB-CONTRACT.md.
"""

from __future__ import annotations

import math

import bpy  # noqa: F401  (imported for type context; used by callers)

from common import materials


class MeshBuilder:
    """Accumulates vertices, faces and per-vertex confidence, then emits a mesh."""

    def __init__(self, name: str):
        self.name = name
        self.verts: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, ...]] = []
        self.conf: list[float] = []
        self.mat_index: list[int] = []

    def add_poly(self, points, confidence: float, mat: int = 0) -> list[int]:
        """Add one n-gon from a list of (x, y, z). Returns its vertex indices."""
        base = len(self.verts)
        for p in points:
            self.verts.append((float(p[0]), float(p[1]), float(p[2])))
            self.conf.append(float(confidence))
        idx = list(range(base, len(self.verts)))
        self.faces.append(tuple(idx))
        self.mat_index.append(mat)
        return idx

    def add_box(self, x0, y0, z0, x1, y1, z1, confidence: float, mat: int = 0,
                skip: tuple[str, ...] = ()) -> None:
        """Axis-aligned box. `skip` omits faces by name so abutting volumes do not
        leave coincident interior surfaces (z-fighting, and wasted triangles)."""
        f = {
            "bottom": [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
            "top":    [(x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)],
            "front":  [(x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)],
            "back":   [(x1, y1, z0), (x1, y1, z1), (x0, y1, z1), (x0, y1, z0)],
            "left":   [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
            "right":  [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)],
        }
        for k, pts in f.items():
            if k not in skip:
                self.add_poly(pts, confidence, mat)

    def add_gable_roof(self, x0, y0, x1, y1, eave_z, pitch_deg, confidence,
                       mat: int = 0, overhang: float = 0.25,
                       ridge_along_x: bool = True) -> float:
        """Gable roof over the given footprint. Returns the ridge height.

        Period frame buildings carry a modest eave overhang; without it the
        silhouette reads as a shoebox and a knowledgeable viewer notices
        immediately.
        """
        x0, y0, x1, y1 = x0 - overhang, y0 - overhang, x1 + overhang, y1 + overhang
        span = (y1 - y0) if ridge_along_x else (x1 - x0)
        rise = (span / 2.0) * math.tan(math.radians(pitch_deg))
        ridge_z = eave_z + rise

        if ridge_along_x:
            ym = (y0 + y1) / 2.0
            self.add_poly([(x0, y0, eave_z), (x1, y0, eave_z),
                           (x1, ym, ridge_z), (x0, ym, ridge_z)], confidence, mat)
            self.add_poly([(x1, y1, eave_z), (x0, y1, eave_z),
                           (x0, ym, ridge_z), (x1, ym, ridge_z)], confidence, mat)
            # gable ends
            self.add_poly([(x0, y0, eave_z), (x0, ym, ridge_z), (x0, y1, eave_z)],
                          confidence, mat)
            self.add_poly([(x1, y1, eave_z), (x1, ym, ridge_z), (x1, y0, eave_z)],
                          confidence, mat)
        else:
            xm = (x0 + x1) / 2.0
            self.add_poly([(x0, y0, eave_z), (xm, y0, ridge_z),
                           (xm, y1, ridge_z), (x0, y1, eave_z)], confidence, mat)
            self.add_poly([(xm, y0, ridge_z), (x1, y0, eave_z),
                           (x1, y1, eave_z), (xm, y1, ridge_z)], confidence, mat)
            self.add_poly([(x0, y0, eave_z), (x1, y0, eave_z), (xm, y0, ridge_z)],
                          confidence, mat)
            self.add_poly([(x1, y1, eave_z), (x0, y1, eave_z), (xm, y1, ridge_z)],
                          confidence, mat)
        return ridge_z

    def to_object(self, materials=None):
        """Emit the accumulated geometry as a Blender object.

        Writes _CONFIDENCE as a FLOAT attribute on the POINT domain — the form the
        glTF exporter turns into a SCALAR float custom attribute with
        export_attributes=True. Do NOT use COLOR_0: glTF defines it as a base-colour
        multiplier, so a documented value of 0.0 renders the surface black.
        """
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.verts, [], self.faces)
        me.update()

        attr = me.attributes.new(name="_CONFIDENCE", type="FLOAT", domain="POINT")
        for i, c in enumerate(self.conf):
            attr.data[i].value = c

        if materials:
            for m in materials:
                me.materials.append(m)
            for poly, mi in zip(me.polygons, self.mat_index):
                poly.material_index = min(mi, len(materials) - 1)

        for poly in me.polygons:
            poly.use_smooth = False

        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


def reset_scene() -> None:
    """Factory-clean scene. Called before every structure so one bake cannot
    leak state into the next."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def simple_material(name: str, rgba=(0.8, 0.8, 0.8, 1.0), roughness: float = 0.75):
    """A plain PBR material. Colour comes from the record's `paint` attribute;
    the confidence channel is deliberately NOT wired into the material, so nothing
    is ever tinted by accident."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


# The paints, READ OFF THE SHEET rather than declared here (T-0007). `materials.py`
# is docs/RESEARCH/materials.md in code. Two of these four values move as a result,
# and both moves are the sheet's finding 5: the town was painted by two generators
# with not one colour in common, and whitewash and iron-oxide red are the two
# finishes both of them named. The vocabulary the RECORDS speak wins, because it is
# the one 222 records already carry and no archetype was reading.
PAINT_RGBA = {
    "white": materials.FINISHES["white_paint"].rgba,
    "unpainted": materials.FINISHES["unpainted"].rgba,
    "whitewash": materials.FINISHES["whitewash"].rgba,
    "red": materials.FINISHES["red_oxide"].rgba,
}

# Not on the sheet, and deliberately: exactly one record in the dataset states
# shutters (the Sauganash's documented bright blue) and the archetypes build them
# only where a record attests them, so `green` and `black` have never shipped a
# single slot. materials.md §1 records that the palette is not carrying dead weight
# into the scene; a sheet row for a surface that does not exist would be.
SHUTTER_RGBA = {
    "bright_blue": (0.14, 0.32, 0.62, 1.0),
    "green": (0.16, 0.30, 0.20, 1.0),
    "black": (0.06, 0.06, 0.07, 1.0),
}

# LOG_RGBA is GONE. It was the paler of the two hewn-log values this project held —
# materials.md finding 2 — and `frame_tavern` was the only importer left, which made
# the Sauganash's wing the one log wall in Chicago built from a different timber than
# the other 52. `common.materials.HEWN_LOG` is now the town's only log.
ROOF_RGBA = materials.ROOF_DEFAULT.rgba
