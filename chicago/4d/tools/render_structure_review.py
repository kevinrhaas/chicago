"""Render the actual Glessner GLB from fixed, reproducible review cameras.

Run with the project's pinned Blender, from any working directory::

    blender -b --factory-startup --python tools/render_structure_review.py -- \
      --glb assets/gltf/glessner_house__as_built_1887.glb --out /tmp/glessner-default \
      --exposure -1.5

    blender -b --factory-startup --python tools/render_structure_review.py -- \
      --glb assets/gltf/versions/glessner_house/v4/glessner_house__as_built_1887.glb \
      --out /tmp/glessner-v4 --size 1600 --samples 128 --exposure -1.5

This is a review renderer, not a geometry or material generator. The imported
GLB's meshes, UVs, textures and materials are unchanged. A neutral ground plane
and procedural daylight provide contact shadows and reflections. These additions
are explicitly recorded in review.json and are not a reconstruction of the site.
No contemporary surroundings or photograph is composited into the result.

Camera coordinates are metres in the imported building frame: X east, Y north,
Z up; SW footprint origin. The glTF importer converts the shipped Y-up GLB back
to this Z-up frame. Use the SAME command/settings for baseline and candidate.
The reviewed daylight exposure is -1.5 EV with AgX Base Contrast. Courtyard
closeups additionally use --sun-elevation 50 --sun-azimuth 225, keeping the
south-facing masonry illuminated. The default sun favours the street facades.
Use --sky overcast for a diffuse architectural review under a CIE overcast
distribution. This is a mathematical luminance field, with no photographic
backdrop, invented cloud patterns, or changes to the imported model.
Use --sky photographic for the licensed, sky-only HDR environment recorded in
docs/RESEARCH/glessner-v4-lighting. Its horizontal illuminance is normalized to
the mathematical overcast mode, preserving the -1.5 EV comparison exposure.
The same environment supplies illumination, reflections and the visible sky.
"""

from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector


CAMERAS = {
    "prairie-east": {"position": (86, 11, 1.7), "target": (49.15, 11, 6.0), "lens": 43},
    "prairie-northeast": {"position": (70, 43, 1.7), "target": (39, 14, 5.8), "lens": 32},
    "prairie-entry-detail": {"position": (60, 12.5, 1.7), "target": (49.15, 12.5, 4.5), "lens": 48},
    "18th-north": {"position": (20, 80, 1.7), "target": (25, 22.55, 6.0), "lens": 38},
    "alley-west": {"position": (-28, 7, 1.7), "target": (0, 12, 5.5), "lens": 32},
    "stable-south": {"position": (6, -21, 1.7), "target": (5.4, 4.34, 5.2), "lens": 38},
    "courtyard-north": {"position": (26, 0.8, 1.7), "target": (26, 14.2, 5.0), "lens": 18},
    "courtyard-east": {"position": (13, 5, 1.7), "target": (40, 9, 5.2), "lens": 28},
    "courtyard-west": {"position": (37, 5, 1.7), "target": (10.82, 9, 5.0), "lens": 28},
    "courtyard-bow-detail": {"position": (27, 2, 1.7), "target": (41, 9, 4.5), "lens": 30},
    "dining-bay-detail": {"position": (27.6, 1, 1.7), "target": (27.6, 12, 4.3), "lens": 32},
    "courtyard-access-detail": {"position": (18.2, 1, 1.7), "target": (18.2, 14.1, 3.7), "lens": 30},
    "overhead": {"position": (64, -38, 68), "target": (24.6, 11.3, 3.0), "lens": 48},
    "overhead-west": {"position": (-25, -35, 62), "target": (24.6, 11.3, 3.0), "lens": 48},
}
# Additional presentation angles; the fixed comparison cameras above are unchanged.
CAMERAS.update({
    "stable-north-detail": {"position": (6.17, 50, 1.7), "target": (6.17, 22.55, 6.1), "lens": 48},
    "stable-northwest-roof": {"position": (-9, 41, 18), "target": (6, 19, 8), "lens": 42},
    "prairie-entry-oblique": {"position": (62.5, 18, 1.7), "target": (49.15, 12.5, 4.15), "lens": 42},
    "courtyard-bow-oblique": {"position": (28, 1, 1.7), "target": (38.5, 10.3, 6.0), "lens": 26},
})
OVERCAST_ZENITH_RGB = (5.58, 5.79, 6.0)
DEFAULT_SKY_FILE = (Path(__file__).resolve().parents[1] / "docs" / "RESEARCH" /
                    "glessner-v4-lighting" / "overcast_soil_puresky_2k.hdr")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cameras", default=",".join(CAMERAS),
                        help="Comma-separated names, or 'all'.")
    parser.add_argument("--size", type=int, default=800, help="Image width; 5:4 ratio.")
    parser.add_argument("--samples", type=int, default=48)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--sky", choices=("clear", "overcast", "photographic"), default="clear")
    parser.add_argument("--sky-file", type=Path, default=DEFAULT_SKY_FILE)
    parser.add_argument("--sky-rotation", type=float, default=0, help="HDR environment Z rotation, degrees.")
    parser.add_argument("--sky-strength", type=float, default=1,
                        help="Multiplier after photographic-sky irradiance normalization.")
    parser.add_argument("--sun-elevation", type=float, default=32)
    parser.add_argument("--sun-azimuth", type=float, default=45,
                        help="Degrees in the building frame; keep equal for comparisons.")
    parser.add_argument("--exposure", type=float, default=0,
                        help="Photographic exposure in EV; keep equal for comparisons.")
    parser.add_argument("--look", default="AgX - Base Contrast")
    parser.add_argument("--save-blend", action="store_true")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


def configure_daylight(scene, args):
    world = bpy.data.worlds.new("Review daylight — not a site reconstruction")
    world.use_nodes = True
    scene.world = world
    tree = world.node_tree
    tree.nodes.clear()
    background = tree.nodes.new("ShaderNodeBackground")
    output = tree.nodes.new("ShaderNodeOutputWorld")
    tree.links.new(background.outputs["Background"], output.inputs["Surface"])
    if args.sky == "photographic":
        source = args.sky_file.resolve(strict=True)
        sky_image = bpy.data.images.load(str(source), check_existing=True)
        sky_image.colorspace_settings.name = "Linear Rec.709"
        width, height = sky_image.size
        pixels = array("f", [0.0]) * (width * height * 4)
        sky_image.pixels.foreach_get(pixels)
        # Integrate L*cos(zenith) over the upper hemisphere of the unchanged
        # equirectangular HDR. CIE-overcast target: E_horizontal=7*pi*Lz/9.
        irradiance = 0.0
        for y in range(height // 2, height):
            elevation = math.pi * ((y + 0.5) / height - 0.5)
            row = y * width * 4
            luminance = sum(0.2126 * pixels[i] + 0.7152 * pixels[i + 1] + 0.0722 * pixels[i + 2]
                            for i in range(row, row + width * 4, 4))
            irradiance += luminance * math.sin(elevation) * math.cos(elevation)
        irradiance *= (math.pi / height) * (2 * math.pi / width)
        target = 7 * math.pi / 9 * sum(a * b for a, b in zip(OVERCAST_ZENITH_RGB, (0.2126, 0.7152, 0.0722)))
        if not math.isfinite(irradiance) or irradiance <= 0 or args.sky_strength <= 0:
            raise ValueError("Photographic sky must have positive finite radiance and strength")
        strength = target / irradiance * args.sky_strength
        environment = tree.nodes.new("ShaderNodeTexEnvironment")
        environment.image = sky_image
        environment.projection = "EQUIRECTANGULAR"
        coordinates = tree.nodes.new("ShaderNodeTexCoord")
        mapping = tree.nodes.new("ShaderNodeMapping")
        mapping.inputs["Rotation"].default_value[2] = math.radians(args.sky_rotation)
        tree.links.new(coordinates.outputs["Generated"], mapping.inputs["Vector"])
        tree.links.new(mapping.outputs["Vector"], environment.inputs["Vector"])
        background.inputs["Strength"].default_value = strength
        tree.links.new(environment.outputs["Color"], background.inputs["Color"])
        sky_image.pack()
        return {"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "bytes": source.stat().st_size, "rotation_deg": args.sky_rotation,
                "strength": strength, "user_strength_multiplier": args.sky_strength,
                "source_horizontal_irradiance_relative": irradiance,
                "target_horizontal_irradiance_relative": target,
                "normalization": "Equal horizontal luminance-weighted irradiance to CIE overcast review sky"}
    if args.sky == "overcast":
        # CIE overcast: L(elevation)/L(zenith) = (1 + 2 sin(elevation))/3.
        # https://www.cie.co.at/publications/spatial-distribution-daylight-cie-standard-general-sky
        # Relative radiance is calibrated for the same -1.5 EV review exposure;
        # this is not an absolute photometric illuminance measurement.
        width, height = 256, 128
        pixels = []
        for y in range(height):
            elevation = math.pi * ((y + 0.5) / height - 0.5)
            relative = (1.0 + 2.0 * max(0.0, math.sin(elevation))) / 3.0
            rgb = [relative * channel for channel in OVERCAST_ZENITH_RGB]
            pixels.extend((rgb + [1.0]) * width)
        sky_image = bpy.data.images.new("REVIEW_ONLY_CIE_overcast", width, height,
                                        alpha=False, float_buffer=True)
        sky_image.colorspace_settings.name = "Linear Rec.709"
        sky_image.pixels.foreach_set(pixels)
        sky_image.pack()
        environment = tree.nodes.new("ShaderNodeTexEnvironment")
        environment.image = sky_image
        environment.projection = "EQUIRECTANGULAR"
        background.inputs["Strength"].default_value = 1.0
        tree.links.new(environment.outputs["Color"], background.inputs["Color"])
        return
    sky = tree.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_disc = True
    sky.sun_elevation = math.radians(args.sun_elevation)
    sky.sun_rotation = math.radians(args.sun_azimuth)
    sky.sun_size = math.radians(0.545)
    sky.sun_intensity = 0.7
    sky.altitude = 0.18
    sky.air_density = 1.0
    sky.dust_density = 1.0
    sky.ozone_density = 1.0
    background.inputs["Strength"].default_value = 0.25
    tree.links.new(sky.outputs["Color"], background.inputs["Color"])


def neutral_ground():
    bpy.ops.mesh.primitive_plane_add(size=2000, location=(24.6, 11.3, -0.005))
    obj = bpy.context.object
    obj.name = "REVIEW_ONLY_neutral_ground"
    material = bpy.data.materials.new("REVIEW_ONLY_neutral_ground")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.18, 0.17, 0.15, 1)
    bsdf.inputs["Roughness"].default_value = 0.88
    obj.data.materials.append(material)


def scene_settings(scene, args):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.015
    scene.cycles.seed = 1904
    scene.cycles.max_bounces = 10
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 6
    scene.render.threads_mode = "FIXED"
    scene.render.threads = args.threads
    scene.render.resolution_x = args.size
    scene.render.resolution_y = round(args.size * 0.8)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = args.look
    scene.view_settings.exposure = args.exposure
    scene.view_settings.gamma = 1.0


def model_description(imported):
    points = [obj.matrix_world @ Vector(corner) for obj in imported
              if obj.type == "MESH" for corner in obj.bound_box]
    meshes = [obj for obj in imported if obj.type == "MESH"]
    materials = {mat for obj in meshes for mat in obj.data.materials if mat}
    shader_parameters = {}
    for material in materials:
        if not material.use_nodes:
            continue
        bsdf = next((node for node in material.node_tree.nodes
                     if node.type == "BSDF_PRINCIPLED"), None)
        if bsdf is not None:
            shader_parameters[material.name] = {
                name: "texture-linked" if bsdf.inputs[name].is_linked
                else round(bsdf.inputs[name].default_value, 6)
                for name in ("Transmission Weight", "IOR", "Roughness", "Metallic")
            }
    return {
        "bounds_m": {"min": [min(p[i] for p in points) for i in range(3)],
                     "max": [max(p[i] for p in points) for i in range(3)]},
        "mesh_objects": len(meshes),
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "polygons": sum(len(obj.data.polygons) for obj in meshes),
        "materials": sorted(mat.name for mat in materials),
        "imported_shader_parameters": shader_parameters,
        "images": [{"name": img.name, "size": list(img.size)} for img in bpy.data.images
                   if img.name not in {"Render Result", "Viewer Node"}],
    }


def main():
    args = parse_args()
    names = list(CAMERAS) if args.cameras == "all" else args.cameras.split(",")
    unknown = set(names) - set(CAMERAS)
    if unknown:
        raise SystemExit(f"Unknown camera(s): {sorted(unknown)}; choices: {list(CAMERAS)}")
    glb = args.glb.resolve(strict=True)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    imported = list(bpy.context.scene.objects)
    model = model_description(imported)
    scene = bpy.context.scene
    scene_settings(scene, args)
    photographic_sky = configure_daylight(scene, args)
    neutral_ground()
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = "REVIEW_ONLY_camera"
    camera.data.sensor_width = 36
    camera.data.clip_start = 0.05
    camera.data.clip_end = 2000
    scene.camera = camera
    report = {
        "glb": str(glb), "sha256": hashlib.sha256(glb.read_bytes()).hexdigest(),
        "blender": bpy.app.version_string,
        "settings": {"engine": "CYCLES", "device": "CPU", "samples": args.samples,
                     "seed": 1904, "resolution": [args.size, round(args.size * 0.8)],
                     "view_transform": "AgX", "look": scene.view_settings.look,
                     "exposure_ev": args.exposure,
                     "neutral_ground_linear_rgb": [0.18, 0.17, 0.15],
                     "sky": args.sky,
                     "sun_elevation_deg": args.sun_elevation,
                     "sun_azimuth_deg": args.sun_azimuth,
                     "world_strength": photographic_sky["strength"] if photographic_sky else (1.0 if args.sky == "overcast" else 0.25),
                     "sun_intensity": 0.7 if args.sky == "clear" else 0.0,
                     "photographic_sky": photographic_sky,
                     "overcast_relative_distribution": "(1+2*sin(elevation))/3" if args.sky == "overcast" else None,
                     "overcast_zenith_linear_rgb": list(OVERCAST_ZENITH_RGB) if args.sky == "overcast" else None},
        "model": model,
        "review_additions": ["Neutral ground plane, z=-0.005 m",
                             {"clear": "Procedural Nishita sky", "overcast": "CIE overcast mathematical sky",
                              "photographic": "Licensed sky-only HDR environment; illumination, reflections and visible sky share one source"}[args.sky],
                             "Review camera; no GLB mesh or material edits"],
        "renders": [],
    }
    print("REVIEW_MODEL " + json.dumps(model), flush=True)
    for name in names:
        config = CAMERAS[name]
        camera.location = config["position"]
        camera.rotation_euler = (Vector(config["target"]) - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.lens = config["lens"]
        scene.render.filepath = str(out / f"{name}.png")
        start = time.monotonic()
        bpy.ops.render.render(write_still=True)
        report["renders"].append({"name": name, **config,
                                  "path": scene.render.filepath,
                                  "seconds": round(time.monotonic() - start, 2)})
        (out / "review.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"REVIEW_RENDER {name} {scene.render.filepath}", flush=True)
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(out / "review.blend"))
    print(f"REVIEW_DONE {out / 'review.json'}", flush=True)


if __name__ == "__main__":
    main()
