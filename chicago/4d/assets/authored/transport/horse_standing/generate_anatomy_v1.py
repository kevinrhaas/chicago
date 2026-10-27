"""Derive a versioned anatomical surface from the licensed standing horse.

This authored-asset path edits the selected canonical rest surface, rather than
the rejected procedural horse fixture. A reviewed JSON recipe supplies compact
smooth displacement fields in canonical metres. The original files, eye UVs,
texture payloads, topology, skin, inverse binds and animation remain immutable.
Actual exported deformation/contact and native reference-view acceptance are
separate requirements; writing a candidate does not satisfy them.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct


PARENT_SHA256 = "d4544c2845256858dfa614235bcb37cb964ab63095a53a2436225182cefbb914"
PARENT_FILE = "horse-sevket-v16-planted-standing-eye-uv-v1.glb"
SCHEMA = "standing-horse-source-bounded-anatomy-recipe-v1"
STREAMS = {0: (199, 200), 1: (203, 204)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_glb(raw):
    require(len(raw) >= 28, "Truncated GLB")
    magic, version, total = struct.unpack_from("<4sII", raw)
    require((magic, version, total) == (b"glTF", 2, len(raw)), "Exact GLB2 container required")
    size, kind = struct.unpack_from("<II", raw, 12)
    require(kind == 0x4E4F534A and size % 4 == 0, "First chunk must be aligned JSON")
    document = json.loads(raw[20:20 + size])
    offset = 20 + size
    bin_size, kind = struct.unpack_from("<II", raw, offset)
    require(kind == 0x004E4942 and offset + 8 + bin_size == len(raw), "One exact BIN chunk required")
    binary = raw[offset + 8:]
    require(len(document["buffers"]) == 1, "Only the pinned single-buffer parent is supported")
    return document, binary


def float_stream(document, binary, index):
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    require(accessor["type"] == "VEC3" and accessor["componentType"] == 5126,
            f"Accessor {index} must contain float32 VEC3")
    require(not accessor.get("sparse") and not accessor.get("normalized"), "Dense unnormalized stream required")
    stride = view.get("byteStride", 12)
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    require(stride >= 12 and offset + (accessor["count"] - 1) * stride + 12 <= len(binary),
            "Accessor outside parent buffer")
    values = [struct.unpack_from("<fff", binary, offset + i * stride)
              for i in range(accessor["count"])]
    require(all(math.isfinite(x) for v in values for x in v), "Nonfinite source coordinate")
    return accessor, offset, stride, values


def field(point, controls):
    """Compact C2 Wendland fields and their analytical deformation Jacobian.

    A single position gives one displacement, including at duplicated UV/normal
    seam vertices. Fields do not pick faces by a camera or move proxy markers.
    """
    displacement = [0.0, 0.0, 0.0]
    jacobian = [[float(i == j) for j in range(3)] for i in range(3)]
    for control in controls:
        centre, radii, delta = control["centre_m"], control["radii_m"], control["delta_m"]
        relative = [point[i] - centre[i] for i in range(3)]
        radius = math.sqrt(sum((relative[i] / radii[i]) ** 2 for i in range(3)))
        if radius >= 1:
            continue
        weight = (1 - radius) ** 4 * (4 * radius + 1)
        gradient = [-20 * (1 - radius) ** 3 * relative[i] / radii[i] ** 2 for i in range(3)]
        for i in range(3):
            displacement[i] += delta[i] * weight
            for j in range(3):
                jacobian[i][j] += delta[i] * gradient[j]
    return tuple(point[i] + displacement[i] for i in range(3)), jacobian


def normal_transform(normal, matrix):
    # Cofactor(J) * n = det(J) * inverse(J).T * n. The positive determinant
    # requirement preserves orientation; normalize before float32 serialization.
    a, b, c = matrix
    cofactors = [[b[1] * c[2] - b[2] * c[1], b[2] * c[0] - b[0] * c[2], b[0] * c[1] - b[1] * c[0]],
                [c[1] * a[2] - c[2] * a[1], c[2] * a[0] - c[0] * a[2], c[0] * a[1] - c[1] * a[0]],
                [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]]
    determinant = sum(a[i] * cofactors[0][i] for i in range(3))
    require(determinant > 0, "Anatomical field reverses the local orientation")
    result = [sum(cofactors[i][j] * normal[j] for j in range(3)) for i in range(3)]
    length = math.sqrt(sum(x * x for x in result))
    require(length > 1e-12, "Invalid transformed normal")
    return tuple(x / length for x in result), determinant


def validate_recipe(recipe):
    require(recipe.get("schema") == SCHEMA, "Unsupported anatomy recipe")
    require(recipe.get("parent_sha256") == PARENT_SHA256, "Recipe must name the true selected eye-UV parent")
    require(recipe.get("frame") == {"units": "metres", "up": "+Y", "forward": "+Z", "anatomical_left": "+X"},
            "Canonical frame is not negotiable")
    controls = recipe.get("controls")
    require(isinstance(controls, list) and controls, "No anatomy changes specified")
    ids = []
    for control in controls:
        ids.append(control["id"])
        for key in ("centre_m", "radii_m", "delta_m"):
            vector = control[key]
            require(len(vector) == 3 and all(isinstance(x, (int, float)) and math.isfinite(x) for x in vector),
                    f"Invalid {key}")
        require(all(x > 0 for x in control["radii_m"]), "Positive field radii required")
        require(control.get("source_ids") and control.get("reason") and control.get("confidence") == "reconstructed",
                "Every anatomical choice needs resolved sources, reasoning and reconstruction confidence")
    require(len(set(ids)) == len(ids), "Duplicate anatomy control id")
    require(0 < recipe["maximum_displacement_m"] <= 0.08, "Declare a bounded near-master change")
    require(recipe["protected_ground_band_max_y_m"] >= 0.2, "Protect actual feet and lower pasterns")
    require(0 < recipe["minimum_local_jacobian"] <= 1, "Declare a positive orientation/compression bound")


def derive(parent, recipe):
    require(digest(parent) == PARENT_SHA256, "Parent source drift")
    validate_recipe(recipe)
    document, original_binary = read_glb(parent)
    original_document = copy.deepcopy(document)
    binary = bytearray(original_binary)
    require(len(document["meshes"]) == 3 and len(document["materials"]) == 3, "Pinned hair/body/eyes layout changed")
    require(len(document["skins"]) == 1 and len(document["skins"][0]["joints"]) == 26, "Pinned canonical26 skin changed")
    require(len(document["animations"]) == 1, "Preserve only the accepted standing animation")
    touched_ranges, meshes = [], []
    for mesh, (position_index, normal_index) in STREAMS.items():
        primitive = document["meshes"][mesh]["primitives"][0]
        require(primitive["attributes"]["POSITION"] == position_index and
                primitive["attributes"]["NORMAL"] == normal_index, "Selected rest stream lineage changed")
        accessor, poffset, pstride, positions = float_stream(document, original_binary, position_index)
        naccessor, noffset, nstride, normals = float_stream(document, original_binary, normal_index)
        require(len(positions) == len(normals), "Position/normal count mismatch")
        output_positions, output_normals = [], []
        changed, maximum, minimum_det = [], 0.0, float("inf")
        for i, (position, normal) in enumerate(zip(positions, normals)):
            target, jacobian = field(position, recipe["controls"])
            distance = math.dist(position, target)
            require(distance <= recipe["maximum_displacement_m"], "Declared anatomical change bound exceeded")
            identity = jacobian == [[float(i == j) for j in range(3)] for i in range(3)]
            if position[1] <= recipe["protected_ground_band_max_y_m"]:
                require(distance == 0 and identity, "Anatomy field changes a protected actual foot/lower-pastern vertex")
            if distance == 0 and identity:
                output_positions.append(position)
                output_normals.append(normal)
                continue
            new_normal, determinant = normal_transform(normal, jacobian)
            require(determinant >= recipe["minimum_local_jacobian"], "Source field compression exceeds declared bound")
            target_bytes, normal_bytes = struct.pack("<fff", *target), struct.pack("<fff", *new_normal)
            target, new_normal = struct.unpack("<fff", target_bytes), struct.unpack("<fff", normal_bytes)
            require(math.dist(position, target) <= recipe["maximum_displacement_m"], "Serialized displacement exceeds bound")
            binary[poffset + i * pstride:poffset + i * pstride + 12] = target_bytes
            binary[noffset + i * nstride:noffset + i * nstride + 12] = normal_bytes
            touched_ranges += [(poffset + i * pstride, 12), (noffset + i * nstride, 12)]
            changed.append(i)
            maximum, minimum_det = max(maximum, math.dist(position, target)), min(minimum_det, determinant)
            output_positions.append(target)
            output_normals.append(new_normal)
        if changed:
            for access, values in ((accessor, output_positions), (naccessor, output_normals)):
                access["min"] = [min(v[k] for v in values) for k in range(3)]
                access["max"] = [max(v[k] for v in values) for k in range(3)]
        meshes.append({"mesh": mesh, "position_accessor": position_index, "normal_accessor": normal_index,
                       "changed_vertex_ids": changed, "maximum_displacement_m": maximum,
                       "minimum_local_jacobian_at_changed_vertices": minimum_det if changed else None})
    require(any(x["changed_vertex_ids"] for x in meshes), "Recipe changes no serialized anatomy")
    protected = bytearray(binary)
    for offset, size in touched_ranges:
        protected[offset:offset + size] = original_binary[offset:offset + size]
    require(bytes(protected) == original_binary, "Protected non-position/normal BIN bytes changed")
    note = {"parent_sha256": PARENT_SHA256, "recipe_sha256": digest(json.dumps(recipe, sort_keys=True).encode()),
            "source_credit": "Horse by sevketkabatas, CC BY4.0, via Objaverse",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "anatomy": "Source-bounded reconstructed near-surface derivative; not an identified historical animal",
            "eye_uv_and_images_exact": True, "rig_weights_binds_and_standing_clip_exact": True,
            "photographic_or_exported_deformation_acceptance": False}
    require("chicago4d_anatomy_derivative" not in document.get("asset", {}).get("extras", {}), "Never derive over this version")
    document.setdefault("asset", {}).setdefault("extras", {})["chicago4d_anatomy_derivative"] = note
    restored = copy.deepcopy(document)
    del restored["asset"]["extras"]["chicago4d_anatomy_derivative"]
    for position_index, normal_index in STREAMS.values():
        for index in (position_index, normal_index):
            restored["accessors"][index] = original_document["accessors"][index]
    require(restored == original_document, "Protected parent GLB JSON changed")
    packed = json.dumps(document, separators=(",", ":")).encode()
    packed += b" " * (-len(packed) % 4)
    total = 28 + len(packed) + len(binary)
    output = struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<II", len(packed), 0x4E4F534A)
    output += packed + struct.pack("<II", len(binary), 0x004E4942) + binary
    return bytes(output), {"meshes": meshes, "changed_BIN_ranges": touched_ranges,
                           "protected_non_position_normal_BIN_exact": True,
                           "protected_JSON_exact_except_declared_accessor_bounds_and_derivative_notice": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, default=Path(__file__).with_name(PARENT_FILE))
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    require(not output.exists(), "A fresh output directory is required; never overwrite source or a previous trial")
    output.mkdir(parents=True)
    parent, recipe_bytes = args.parent.read_bytes(), args.recipe.read_bytes()
    receipt = {"schema": "standing-horse-anatomy-source-derivation-v1", "status": "STARTED",
               "parent_sha256": digest(parent), "recipe_bytes_sha256": digest(recipe_bytes),
               "generator_sha256": digest(Path(__file__).read_bytes()), "photographic_acceptance": False,
               "fresh_export_deformation_contact_acceptance": False}
    try:
        candidate, boundary = derive(parent, json.loads(recipe_bytes))
        target = output / "horse-sevket-anatomy-v1.glb"
        target.write_bytes(candidate)
        require(digest(args.parent.read_bytes()) == PARENT_SHA256, "Parent changed after derivation")
        receipt.update(status="SOURCE_CANDIDATE_ONLY_NOT_INSTALLED_OR_ACCEPTED", candidate_sha256=digest(candidate),
                       candidate_bytes=len(candidate), candidate_file=str(target), boundary=boundary)
    except Exception as error:
        receipt.update(status="DERIVATION_REJECTED", error=str(error))
        raise
    finally:
        (output / "DERIVATION-RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
