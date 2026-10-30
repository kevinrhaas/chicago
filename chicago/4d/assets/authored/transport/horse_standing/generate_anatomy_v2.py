"""Build the reviewed source-bounded near anatomy with a locally refined hoof mesh.

All parent BIN bytes are retained. New selected body streams are appended, with
explicit source-face/edge ancestry for added geometry and skin/UV rows. Original
eye UVs/globes, images, hair, rig, original weight rows, binds and standing clip
remain immutable. New topology is not claimed to inherit an old physical proof.
"""

import argparse
import copy
import json
import math
from pathlib import Path
import struct

import generate_anatomy_v1 as base
import anatomy_topology_v2 as topology


D = Path(__file__).resolve().parent
APP = D.parents[3]
SCHEMA = "standing-horse-source-bounded-anatomy-recipe-v2"


def read_attribute(document, binary, index):
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    kind, size = {5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}[accessor["componentType"]]
    base.require(not accessor.get("sparse") and not accessor.get("normalized"), "Dense parent attributes required")
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    stride = view.get("byteStride", size * components)
    return [struct.unpack_from("<" + kind * components, binary, offset + i * stride)
            for i in range(accessor["count"])]


def f32(values):
    return [struct.unpack("<" + "f" * len(value), struct.pack("<" + "f" * len(value), *value)) for value in values]


def gated_field(point, controls):
    displacement = [0.0, 0.0, 0.0]
    jacobian = [[float(i == j) for j in range(3)] for i in range(3)]
    for control in controls:
        relative = [point[i] - control["centre_m"][i] for i in range(3)]
        radius = math.sqrt(sum((relative[i] / control["radii_m"][i]) ** 2 for i in range(3)))
        if radius >= 1:
            continue
        weight = (1 - radius) ** 4 * (4 * radius + 1)
        gradient = [-20 * (1 - radius) ** 3 * relative[i] / control["radii_m"][i] ** 2 for i in range(3)]
        if "lower_y_gate_m" in control:
            low, high = control["lower_y_gate_m"]
            t = min(1.0, max(0.0, (point[1] - low) / (high - low)))
            gate = topology.smoothstep(t)
            derivative = 30 * t ** 2 * (1 - t) ** 2 / (high - low) if 0 < t < 1 else 0.0
            gradient = [x * gate for x in gradient]
            gradient[1] += weight * derivative
            weight *= gate
        for i in range(3):
            displacement[i] += control["delta_m"][i] * weight
            for j in range(3):
                jacobian[i][j] += control["delta_m"][i] * gradient[j]
    return tuple(point[i] + displacement[i] for i in range(3)), jacobian


def append_stream(document, binary, values, kind, component_type, target):
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[kind]
    fmt = {5123: "H", 5126: "f"}[component_type]
    binary.extend(b"\0" * (-len(binary) % 4))
    offset = len(binary)
    for value in values:
        binary.extend(struct.pack("<" + fmt * components, *value))
    view = len(document["bufferViews"])
    document["bufferViews"].append({"buffer": 0, "byteOffset": offset,
                                  "byteLength": len(binary) - offset, "target": target})
    accessor = {"bufferView": view, "componentType": component_type, "count": len(values), "type": kind}
    if component_type == 5126:
        accessor["min"] = [min(value[k] for value in values) for k in range(components)]
        accessor["max"] = [max(value[k] for value in values) for k in range(components)]
    index = len(document["accessors"])
    document["accessors"].append(accessor)
    return index


def derive(parent, recipe, sidecar, source_directory):
    base.require(base.digest(parent) == base.PARENT_SHA256, "Selected eye-UV parent drift")
    base.require(recipe["schema"] == SCHEMA and recipe["parent_sha256"] == base.PARENT_SHA256,
                 "Exact anatomy V2 recipe and true parent required")
    base.require(recipe["frame"] == {"units": "metres", "up": "+Y", "forward": "+Z", "anatomical_left": "+X"},
                 "Canonical frame changed")
    base.require(0 < recipe["maximum_body_displacement_m"] <= .04 and 0 < recipe["minimum_local_jacobian"] <= 1,
                 "Bound the declared body correction")
    source_ids = set()
    for reference in recipe["reference_bindings"]:
        source_id = reference["source_id"]
        source = json.loads((source_directory / (source_id + ".json")).read_text())
        base.require(source["id"] == source_id and source["rights_status"] in ["public_domain", "cleared"],
                     "Every anatomy source must resolve and permit asset derivation")
        source_ids.add(source_id)
    for control in recipe["controls"]:
        base.require(set(control["source_ids"]) <= source_ids and control["confidence"] == "reconstructed"
                     and control["reason"], "Every body choice needs a cleared source and declared reasoning")
        for key in ["centre_m", "radii_m", "delta_m"]:
            base.require(len(control[key]) == 3 and all(math.isfinite(x) for x in control[key]), "Nonfinite control")
        base.require(all(x > 0 for x in control["radii_m"]), "Positive field radii required")
        if "lower_y_gate_m" in control:
            low, high = control["lower_y_gate_m"]
            base.require(math.isfinite(low) and math.isfinite(high) and low < high, "Invalid lower-lid gate")
    hoof = recipe["hoof_refinement"]
    base.require(set(hoof["source_ids"]) <= source_ids and hoof["confidence"] == "reconstructed" and hoof["reason"],
                 "Hoof reconstruction needs resolved cleared sources and reasoning")
    base.require(0 <= hoof["ground_anchor_band_m"] <= .02 and
                 0 < hoof["full_fairing_below_m"] < hoof["region_top_m"] <= .4 and
                 0 < hoof["region_radius_m"] <= .3 and
                 0 <= hoof["original_vertex_fairing"] <= 1 and 0 <= hoof["edge_fairing"] <= 1 and
                 0 < hoof["maximum_old_vertex_shift_m"] <= .02 and 0 < hoof["maximum_edge_curvature_m"] <= .02,
                 "Hoof recipe must declare bounded geometry choices")
    document, original_binary = base.read_glb(parent)
    original_document = copy.deepcopy(document)
    primitive = document["meshes"][1]["primitives"][0]
    base.require(primitive["attributes"] == {"JOINTS_0": 205, "NORMAL": 204, "POSITION": 203,
                 "TEXCOORD_0": 6, "TEXCOORD_1": 6, "WEIGHTS_0": 206} and primitive["indices"] == 7,
                 "Pinned body primitive layout changed")
    original_positions, original_normals = read_attribute(document, original_binary, 203), read_attribute(document, original_binary, 204)
    uv = read_attribute(document, original_binary, 6)
    joints, weights = read_attribute(document, original_binary, 205), read_attribute(document, original_binary, 206)
    indices = [value[0] for value in read_attribute(document, original_binary, 7)]
    triangles = [tuple(indices[i:i + 3]) for i in range(0, len(indices), 3)]
    positions, normals, changed, minimum_det = [], [], [], 1.0
    for i, (position, normal) in enumerate(zip(original_positions, original_normals)):
        target, jacobian = gated_field(position, recipe["controls"])
        distance = math.dist(position, target)
        base.require(distance <= recipe["maximum_body_displacement_m"], "Body control exceeds declared bound")
        if distance:
            new_normal, determinant = base.normal_transform(normal, jacobian)
            base.require(determinant >= recipe["minimum_local_jacobian"], "Body field exceeds declared compression")
            changed.append(i)
            minimum_det = min(minimum_det, determinant)
        else:
            new_normal = normal
        positions.append(target)
        normals.append(new_normal)
    positions, normals = f32(positions), f32(normals)
    shaped = topology.refine(positions, normals, uv, joints, weights, triangles, sidecar, recipe["hoof_refinement"])
    positions, normals = f32(shaped["positions"]), f32(shaped["normals"])
    minimum_dot = 1.0
    for fi, triangle in enumerate(triangles):
        a, b, c = [original_positions[i] for i in triangle]
        old = topology.cross(tuple(b[k] - a[k] for k in range(3)), tuple(c[k] - a[k] for k in range(3)))
        length = math.sqrt(sum(x * x for x in old))
        if length < 1e-14:
            continue
        for child in shaped["receipt"]["source_face_to_children"][fi]:
            a, b, c = [positions[i] for i in shaped["triangles"][child]]
            actual = topology.cross(tuple(b[k] - a[k] for k in range(3)), tuple(c[k] - a[k] for k in range(3)))
            current_length = math.sqrt(sum(x * x for x in actual))
            base.require(current_length > 1e-14, "Serialized body develops a degenerate triangle")
            dot = sum(x * y for x, y in zip(old, actual)) / length / current_length
            base.require(dot > 0, "Serialized body/hoof reverses a source triangle")
            minimum_dot = min(minimum_dot, dot)
    for vertex in shaped["receipt"]["ground_support_anchor_vertex_ids"]:
        base.require(positions[vertex] == original_positions[vertex], "Named source ground-support anchor moved")
    binary = bytearray(original_binary)
    attributes = {}
    for name, values, kind, component in [("POSITION", positions, "VEC3", 5126), ("NORMAL", normals, "VEC3", 5126),
            ("TEXCOORD_0", shaped["uv"], "VEC2", 5126), ("JOINTS_0", shaped["joints"], "VEC4", 5123),
            ("WEIGHTS_0", shaped["weights"], "VEC4", 5126)]:
        attributes[name] = append_stream(document, binary, values, kind, component, 34962)
    attributes["TEXCOORD_1"] = attributes["TEXCOORD_0"]
    primitive["attributes"] = attributes
    primitive["indices"] = append_stream(document, binary, [(i,) for tri in shaped["triangles"] for i in tri], "SCALAR", 5123, 34963)
    document["buffers"][0]["byteLength"] = len(binary)
    binary.extend(b"\0" * (-len(binary) % 4))
    base.require(bytes(binary[:len(original_binary)]) == original_binary, "An immutable parent BIN byte changed")
    document["asset"].setdefault("extras", {})["chicago4d_anatomy_master_v2"] = {
        "parent_sha256": base.PARENT_SHA256, "source_credit": "Horse by sevketkabatas, CC BY4.0, via Objaverse",
        "recipe_sha256": base.digest(json.dumps(recipe, sort_keys=True).encode()),
        "changes": "Reconstructed eyelid rest surface and adaptive hoof-wall/coronet geometry; no historical individual or breed",
        "parent_BIN_bytes_preserved": True, "body_topology_changed": True,
        "old_physical_proof_inherited": False, "photographic_acceptance": False}
    # The only parent JSON changes are body stream selection, buffer length and
    # the explicit ancestry notice. Every original accessor/view stays intact.
    restored = copy.deepcopy(document)
    restored["meshes"][1]["primitives"][0] = original_document["meshes"][1]["primitives"][0]
    restored["buffers"] = original_document["buffers"]
    restored["accessors"] = restored["accessors"][:len(original_document["accessors"])]
    restored["bufferViews"] = restored["bufferViews"][:len(original_document["bufferViews"])]
    del restored["asset"]["extras"]["chicago4d_anatomy_master_v2"]
    base.require(restored == original_document, "Unexpected protected parent JSON change")
    packed = json.dumps(document, separators=(",", ":")).encode()
    packed += b" " * (-len(packed) % 4)
    output = struct.pack("<4sII", b"glTF", 2, 28 + len(packed) + len(binary))
    output += struct.pack("<II", len(packed), 0x4E4F534A) + packed
    output += struct.pack("<II", len(binary), 0x004E4942) + binary
    base.require(len(output) <= 4 * 1024 * 1024, "Retain the unchanged 4MiB standing-asset byte ceiling")
    return output, {"body_field_changed_vertices": changed, "body_field_minimum_local_jacobian": minimum_det,
                    "serialized_minimum_parent_child_face_normal_dot": minimum_dot,
                    "parent_BIN_prefix_exact": True, "parent_JSON_protection": True,
                    "hoof_refinement": shaped["receipt"], "selected_body_attributes": attributes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, default=D / base.PARENT_FILE)
    parser.add_argument("--recipe", type=Path, default=D / "anatomy-v2-recipe.json")
    parser.add_argument("--sidecar", type=Path, default=APP / "tools/fixtures/horse-anatomy-parent-sidecar-v1.json")
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    base.require(not args.output_dir.exists(), "Fresh output directory required")
    args.output_dir.mkdir(parents=True)
    parent, recipe_bytes, sidecar_bytes = args.parent.read_bytes(), args.recipe.read_bytes(), args.sidecar.read_bytes()
    recipe = json.loads(recipe_bytes)
    receipt = {"schema": "standing-horse-anatomy-v2-source-derivation", "state": "STARTED",
               "parent_sha256": base.digest(parent), "recipe_sha256": base.digest(recipe_bytes),
               "generator_sha256": base.digest(Path(__file__).read_bytes()),
               "topology_source_sha256": base.digest((D / "anatomy_topology_v2.py").read_bytes()),
               "photographic_acceptance": False, "fresh_loaded_deformation_contact_acceptance": False}
    try:
        base.require(base.digest(sidecar_bytes) == recipe["parent_sidecar_sha256"], "Pinned contact witness sidecar drift")
        for reference in recipe["reference_bindings"]:
            base.require(base.digest((args.reference_dir / reference["file"]).read_bytes()) == reference["sha256"],
                         "Actual cleared reference-image bytes drifted")
        candidate, proof = derive(parent, recipe, json.loads(sidecar_bytes), APP / "data/sources")
        file = args.output_dir / "horse-sevket-anatomy-v2.glb"
        file.write_bytes(candidate)
        base.require(base.digest(args.parent.read_bytes()) == base.PARENT_SHA256, "Original source changed")
        receipt.update(state="CANDIDATE_NOT_INSTALLED_OR_ACCEPTED", candidate_sha256=base.digest(candidate),
                       candidate_bytes=len(candidate), candidate_file=str(file), source_boundary=proof)
    except Exception as error:
        receipt.update(state="DERIVATION_REJECTED", error=str(error))
        raise
    finally:
        (args.output_dir / "DERIVATION-RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
