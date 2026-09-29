"""Render the actual Glessner GLB from fixed, reproducible review cameras.

Run with the project's pinned Blender, from any working directory::

    blender -b --factory-startup --python tools/render_structure_review.py -- \
      --glb assets/gltf/glessner_house__as_built_1887.glb --out /tmp/glessner-default

    blender -b --factory-startup --python tools/render_structure_review.py -- \
      --glb assets/gltf/versions/glessner_house/v4/glessner_house__as_built_1887.glb \
      --out /tmp/glessner-v4 --size 1600 --samples 128

This is a review renderer, not a geometry or material generator. The imported
GLB's meshes, UVs, textures and materials are unchanged. A neutral ground plane
and procedural daylight provide contact shadows and reflections. These additions
are explicitly recorded in review.json and are not a reconstruction of the site.
No contemporary surroundings or photograph is composited into the result.

Camera coordinates are metres in the imported building frame: X east, Y north,
Z up; SW footprint origin. The glTF importer converts the shipped Y-up GLB back
to this Z-up frame. Use the SAME command/settings for baseline and candidate.
"""

from __future__ import annotations

import argparse
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
    "overhead": {"position": (64, -38, 68), "target": (24.6, 11.3, 3.0), "lens": 48},
    "overhead-west": {"position": (-25, -35, 62), "target": (24.6, 11.3, 3.0), "lens": 48},
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cameras", default=",".join(CAMERAS),
                        help="Comma-separated names, or 'all'.")
    parser.add_argument("--size", type=int, default=800, help="Image width; 5:4 ratio.")
    parser.add_argument("--samples", type=int, default=48)
    parser.add_argument("--threads", type=int, default=4)
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
    background = tree.nodes.new("ShaderNodeBackground")
    background.inputs["Strength"].default_value = 0.25
    output = tree.nodes.new("ShaderNodeOutputWorld")
    tree.links.new(sky.outputs["Color"], background.inputs["Color"])
    tree.links.new(background.outputs["Background"], output.inputs["Surface"])


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
    return {
        "bounds_m": {"min": [min(p[i] for p in points) for i in range(3)],
                     "max": [max(p[i] for p in points) for i in range(3)]},
        "mesh_objects": len(meshes),
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "polygons": sum(len(obj.data.polygons) for obj in meshes),
        "materials": sorted({mat.name for obj in meshes for mat in obj.data.materials if mat}),
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
    configure_daylight(scene, args)
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
                     "sun_elevation_deg": args.sun_elevation,
                     "sun_azimuth_deg": args.sun_azimuth,
                     "world_strength": 0.25, "sun_intensity": 0.7},
        "model": model,
        "review_additions": ["Neutral ground plane, z=-0.005 m", "Procedural Nishita sky",
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
