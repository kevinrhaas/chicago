"""Glessner v4's original, metric PBR material library.

This module is deliberately local to the opt-in v4 builder. Nothing here changes
the shared town palette or a previous Glessner version. The maps are reconstructed
surface studies, made by the numeric generator beside them; photographs were read
as visual references, never sampled, traced, projected or embedded. Material names
retain the legacy roof_plane contract. Copper is a metal; the window surface is
dielectric glass with real environment reflections, not painted blue rectangles.

All scalar material colours are LINEAR. Albedo files are sRGB; normal and roughness
files are non-colour data. No atlas claims to be a measured surface of the house.
"""
from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEXTURES = ROOT / "assets" / "textures" / "glessner-v4"
SURFACE_UV = "SurfaceUV"
BAKE_UV = "BakeUV"

# One repeat in metres. The module sizes are reconstructed. The tall brick repeat
# covers 32 small courses; the roof repeat covers 16 flat overlapping tile courses.
TILE_M = {
    "granite": (1.6, 1.6),
    "brick": (1.7272, 2.1336),
    "limestone": (1.2, 1.2),
    "terracotta": (2.4384, 1.95072),
    "copper": (2.4, 2.4),
    "oak": (0.8, 2.4),
    "painted_wood": (0.8, 2.4),
    "turf": (2.4, 2.4),
    "gravel": (2.0, 2.0),
}

# Geometry and material module share these slots. New materials are appended so
# that the existing nine-part composition can be reused without reinterpretation.
GRANITE, BRICK, TRIM, ROOF, COPPER, GLASS, WOOD, LAWN, DRIVE = range(9)
MORTAR, IRON, GLASS_DARK = 9, 10, 11
GRANITE_VARIANTS = (12, 13, 14, 15)
BRICK_VARIANTS = (16, 17, 18)
ROOF_VARIANTS = (19, 20, 21)
LINEN = 22
PAINTED_WOOD = 23
ROUGH_TRIM = 24

SLOT_FABRIC = {
    0: "granite", 1: "brick", 2: "limestone", 3: "terracotta",
    4: "copper", 6: "oak", 7: "turf", 8: "gravel", 9: "limestone",
    12: "granite", 13: "granite", 14: "granite", 15: "granite",
    16: "brick", 17: "brick", 18: "brick",
    19: "terracotta", 20: "terracotta", 21: "terracotta",
    23: "painted_wood",
    24: "granite",
}


def _image(bpy, fabric, suffix, colour=False):
    """Load the exact committed map. Missing output is a build error, never a flat fallback."""
    ext = "jpg" if suffix == "basecolor" else "png"
    path = TEXTURES / f"{fabric}_{suffix}.{ext}"
    if not path.is_file():
        raise FileNotFoundError(f"Glessner v4 PBR map missing: {path}")
    image = bpy.data.images.load(str(path), check_existing=True)
    image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    return image


def _plain(bpy, name, colour, roughness=0.8, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.use_backface_culling = False
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour[:3], colour[3] if len(colour) > 3 else 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return material


def _pbr(bpy, name, fabric, tint=(1, 1, 1), normal_strength=1.0, metallic=0.0,
         normal_fabric=None, albedo_fabric=None):
    material = _plain(bpy, name, (*tint, 1), metallic=metallic)
    nt = material.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = SURFACE_UV
    for suffix, input_name, colour in (("basecolor", "Base Color", True),
                                        ("roughness", "Roughness", False),
                                        ("normal", "Normal", False)):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.label = f"Original {fabric} {suffix}"
        source_fabric = fabric
        if suffix == "normal" and normal_fabric:
            source_fabric = normal_fabric
        if suffix == "basecolor" and albedo_fabric:
            source_fabric = albedo_fabric
        tex.image = _image(bpy, source_fabric, suffix, colour)
        tex.interpolation = "Linear"
        tex.extension = "REPEAT"
        nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
        if suffix == "normal":
            normal = nt.nodes.new("ShaderNodeNormalMap")
            normal.uv_map = SURFACE_UV
            normal.inputs["Strength"].default_value = normal_strength
            nt.links.new(tex.outputs["Color"], normal.inputs["Color"])
            nt.links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
        elif suffix == "basecolor" and tint != (1, 1, 1):
            # The glTF exporter recognises this multiply and carries its constant
            # as baseColorFactor. Variants share images rather than cloning atlases.
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs[0].default_value = 1.0
            mix.inputs[7].default_value = (*tint, 1.0)
            nt.links.new(tex.outputs["Color"], mix.inputs[6])
            nt.links.new(mix.outputs[2], bsdf.inputs[input_name])
        else:
            nt.links.new(tex.outputs["Color"], bsdf.inputs[input_name])
    material["surface_tier"] = "reconstructed"
    material["texture_generator"] = "assets/textures/glessner-v4/generate.py"
    material["tile_m"] = list(TILE_M[fabric])
    return material


def build_materials(colours=None):
    """Return 25 slots. Colours comes from the structure's resolved data record.

    Textured fabrics carry reconstructed absolute albedo in their maps. Turf and
    pale compacted gravel preserve the record's courtyard material reading.
    """
    import bpy
    colours = colours or {}
    mats = [
        _pbr(bpy, "granite", "granite", normal_strength=1.15),
        _pbr(bpy, "brick", "brick", normal_strength=0.85),
        _pbr(bpy, "limestone_trim", "limestone", normal_strength=0.65),
        _pbr(bpy, "roof_plane", "terracotta", normal_strength=0.70),
        _pbr(bpy, "copper", "copper", normal_strength=0.18, metallic=0.78),
        _plain(bpy, "glass", (0.945, 0.97, 0.953, 1), roughness=0.065),
        _pbr(bpy, "oak", "oak", normal_strength=0.45),
        _pbr(bpy, "lawn", "turf", normal_strength=0.55),
        _pbr(bpy, "drive", "gravel", normal_strength=0.55),
        _pbr(bpy, "mortar", "limestone", tint=(0.52, 0.49, 0.44), normal_strength=0.25),
        _plain(bpy, "iron", (0.013, 0.017, 0.015, 1), roughness=0.40, metallic=0.70),
        _plain(bpy, "glass_dark", (0.005, 0.007, 0.006, 1), roughness=0.92),
    ]
    glass = mats[GLASS].node_tree.nodes.get("Principled BSDF")
    glass.inputs["IOR"].default_value = 1.52
    # Actual thin dielectric glazing, with a dark interior backing and separate
    # linen blinds supplied by the geometry. An opaque painted pane hid those
    # blinds and made every window an identical blue-grey rectangle in review.
    glass.inputs["Transmission Weight"].default_value = 0.94
    if "Specular IOR Level" in glass.inputs:
        glass.inputs["Specular IOR Level"].default_value = 0.50
    # Quarried blocks have restrained grey, pink-feldspar and cream variation.
    # The previous 1-7% linear variation vanished in the broad facade review.
    for i, tint in enumerate(((0.72, 0.79, 0.85), (0.97, 0.91, 0.87),
                              (0.86, 0.84, 0.81), (1.00, 0.985, 0.965))):
        mats.append(_pbr(bpy, f"granite_{i + 1}", "granite", tint=tint, normal_strength=1.15))
    # Kiln firing varies individual common bricks. The geometry deals mostly
    # the main red-brown slot1, then dark red16, buff17 and occasional smoky18.
    # The neutral limestone grain image supplies the latter colour fields only;
    # their relief and roughness remain brick. No additional atlas is duplicated.
    mats.append(_pbr(bpy, "brick_dark_red", "brick", tint=(0.70, 0.73, 0.76), normal_strength=0.85))
    mats.append(_pbr(bpy, "brick_buff", "brick", tint=(0.40, 0.28, 0.18), normal_strength=0.85,
                     albedo_fabric="limestone"))
    mats.append(_pbr(bpy, "brick_smoky", "brick", tint=(0.20, 0.16, 0.13), normal_strength=0.85,
                     albedo_fabric="limestone"))
    for i, tint in enumerate(((0.92, 0.90, 0.88), (1.0, 0.99, 0.976), (0.97, 0.93, 0.91))):
        mats.append(_pbr(bpy, f"roof_plane_{i + 1}", "terracotta", tint=tint, normal_strength=0.70))
    mats.append(_plain(bpy, "linen_blind", (0.74, 0.73, 0.68, 1), roughness=0.98))
    mats.append(_pbr(bpy, "painted_wood", "painted_wood", normal_strength=0.30))
    # Rock-faced window heads/sills share the visible grey mineral fabric of the
    # street stone. Dressed cornices and carved mouldings retain smoother slot2.
    # This is reconstructed appearance, not a petrographic identification.
    mats.append(_pbr(bpy, "rough_stone_trim", "granite", normal_strength=0.90))
    return mats


def assign_metric_uvs(ob):
    """Metric UVs for walls and pitched planes; preserve them through emit.unwrap.

    SurfaceUV is the first / render-active layer and every PBR node requests it
    explicitly. BakeUV is the edit-active layer: the legacy pipeline's smart
    unwrap edits that disposable layer instead. glTF therefore carries the
    textures on TEXCOORD_0, which the web batching renderer preserves.

    Facades project a horizontal tangent and global height. Roofs project a
    horizontal contour tangent and a unit vector uphill, so tile courses follow
    the physical slope instead of stretching vertically. All coordinates are
    metres before the per-fabric repeat is applied.
    """
    from mathutils import Vector
    mesh = ob.data
    surface = mesh.uv_layers.get(SURFACE_UV) or mesh.uv_layers.new(name=SURFACE_UV)
    for poly in mesh.polygons:
        n = poly.normal.normalized()
        horizontal = Vector((-n.y, n.x, 0.0))
        if horizontal.length < 1e-6:
            horizontal = Vector((1.0, 0.0, 0.0))
            uphill = Vector((0.0, 1.0, 0.0))
        else:
            horizontal.normalize()
            uphill = n.cross(horizontal).normalized()
            if uphill.z < 0:
                uphill.negate()
                horizontal.negate()
        fabric = SLOT_FABRIC.get(poly.material_index)
        tu, tv = TILE_M.get(fabric, (1.0, 1.0))
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            surface.data[li].uv = (co.dot(horizontal) / tu, co.dot(uphill) / tv)
    surface.active_render = True
    scratch = mesh.uv_layers.get(BAKE_UV) or mesh.uv_layers.new(name=BAKE_UV)
    mesh.uv_layers.active = scratch
    surface.active_render = True
    ob["metric_surface_uv"] = SURFACE_UV
    return ob
