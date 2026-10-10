"""Build the portable-human pipeline's CI fixture as a Blender master (T-1787).

    blender -b -noaudio --factory-startup --python tools/human_fixture_blend.py -- OUT.blend

The fixture is NOBODY. It is a deliberately plain, non-historical figure that exists
to prove the road docs/HUMAN-ASSET-CONTRACT.md describes, Blender -> GLB -> the
browser, on every LOD, with the contract's whole skeleton, its five required material
slots, the three required face morphs, the two clips an actor needs and the three
required sockets. It is built from code, so this script is its master: the .blend it
writes is an intermediate that tools/human_export.sh rebuilds on every run, and the
GLBs under assets/humans/ (and assets/humans/web/) are what that rebuild must
reproduce byte for byte.

Everything a real body (T-1789) will be authored by hand in Blender, this builds from
primitives: tapered cylinders on each bone, spheres for the head and eyes, boxes for
the feet and the light LODs' mitten hands. The master's layout is the part a real
master must copy, because tools/human_export.py reads it:

  * one armature object, `c4d_armature`, carrying the 56 contract bones, scale 1
  * one collection per LOD, `lod0` ... `lod3`, each holding that LOD's mesh objects,
    every one parented to the armature with an Armature modifier
  * the `socket_*` empties parented to their bones, in the armature's collection
  * one action per clip, named for the clip; a walk carries `speed_m_s`
  * the scene's `chicago4d_human` custom property: the provenance block, written
    into every GLB's scenes[0].extras by the exporter
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = json.loads((ROOT / "data/humans/contract.json").read_text(encoding="utf-8"))
ASSET_ID = "c4d_fixture"

# --------------------------------------------------------------------------- skeleton
# Blender frame: Z up, the figure faces -Y, so its left hand is at +X. The glTF
# exporter's Y-up conversion turns that into the contract's frame: +Y up, facing +Z.
H = {}  # bone -> (head, tail), metres, the figure's LEFT side; _r mirrors in X


def _b(name, head, tail):
    H[name] = (Vector(head), Vector(tail))


_b("root", (0, 0, 0), (0, 0, 0.12))
_b("pelvis", (0, 0, 0.95), (0, 0, 1.05))
_b("spine_01", (0, 0, 1.05), (0, 0, 1.18))
_b("spine_02", (0, 0, 1.18), (0, 0, 1.30))
_b("spine_03", (0, 0, 1.30), (0, 0, 1.42))
_b("neck_01", (0, 0, 1.42), (0, 0, 1.51))
_b("head", (0, 0, 1.51), (0, 0, 1.70))
_b("jaw", (0, -0.01, 1.565), (0, -0.085, 1.535))
_b("eye_l", (0.032, -0.082, 1.615), (0.032, -0.11, 1.615))
_b("clavicle_l", (0.02, 0, 1.40), (0.17, 0, 1.40))
_b("upperarm_l", (0.17, 0, 1.40), (0.46, 0, 1.40))
_b("lowerarm_l", (0.46, 0, 1.40), (0.71, 0, 1.40))
_b("hand_l", (0.71, 0, 1.40), (0.79, 0, 1.40))
_b("thumb_01_l", (0.73, -0.03, 1.395), (0.755, -0.055, 1.39))
_b("thumb_02_l", (0.755, -0.055, 1.39), (0.775, -0.07, 1.388))
_b("thumb_03_l", (0.775, -0.07, 1.388), (0.79, -0.08, 1.386))
for _k, (_f, _y) in enumerate((("index", -0.027), ("middle", -0.009), ("ring", 0.009), ("pinky", 0.026))):
    _len = (0.036, 0.024, 0.02) if _f != "pinky" else (0.028, 0.018, 0.016)
    _x = 0.79
    for _n, _l in enumerate(_len, start=1):
        _b(f"{_f}_0{_n}_l", (_x, _y, 1.40), (_x + _l, _y, 1.40))
        _x += _l
_b("thigh_l", (0.09, 0, 0.95), (0.09, 0, 0.50))
_b("calf_l", (0.09, 0, 0.50), (0.09, 0, 0.085))
_b("foot_l", (0.09, 0, 0.085), (0.09, -0.12, 0.025))
_b("ball_l", (0.09, -0.12, 0.025), (0.09, -0.18, 0.025))

for _n in [n for n in H if n.endswith("_l")]:
    hd, tl = H[_n]
    H[_n[:-2] + "_r"] = (Vector((-hd.x, hd.y, hd.z)), Vector((-tl.x, tl.y, tl.z)))

PARENT = dict(CONTRACT["skeleton"]["bones"])
assert set(PARENT) == set(H), sorted(set(PARENT) ^ set(H))

# ------------------------------------------------------------------------------ parts
# (bone, start, end, r_start, r_end, material, kind). A cylinder runs from start to end;
# its first ring is shared half-and-half with the parent bone, so a bent joint bends
# the surface instead of tearing it. A sphere is centred at `start`.
FINGERS = [f"{f}_0{n}" for f in ("thumb", "index", "middle", "ring", "pinky") for n in (1, 2, 3)]


def parts(lod: int):
    p = [
        ("pelvis", (0, 0, 0.86), (0, 0, 1.05), 0.150, 0.150, "garment_lower", "cyl"),
        ("spine_01", (0, 0, 1.05), (0, 0, 1.18), 0.150, 0.155, "garment_upper", "cyl"),
        ("spine_02", (0, 0, 1.18), (0, 0, 1.30), 0.155, 0.165, "garment_upper", "cyl"),
        ("spine_03", (0, 0, 1.30), (0, 0, 1.43), 0.165, 0.120, "garment_upper", "cyl"),
        ("neck_01", (0, 0, 1.42), (0, 0, 1.53), 0.050, 0.050, "skin", "cyl"),
        ("head", (0, 0, 1.61), None, 0.095, 0.095, "skin", "sphere"),
        ("jaw", (0, -0.035, 1.545), None, 0.055, 0.055, "skin", "sphere"),
        ("eye_l", (0.032, -0.082, 1.615), None, 0.014, 0.014, "eyes", "sphere"),
        ("eye_r", (-0.032, -0.082, 1.615), None, 0.014, 0.014, "eyes", "sphere"),
    ]
    for s in ("l", "r"):
        x = 1 if s == "l" else -1
        p += [
            (f"clavicle_{s}", (0.03 * x, 0, 1.40), (0.17 * x, 0, 1.40), 0.060, 0.060, "garment_upper", "cyl"),
            (f"upperarm_{s}", (0.17 * x, 0, 1.40), (0.46 * x, 0, 1.40), 0.055, 0.045, "garment_upper", "cyl"),
            (f"lowerarm_{s}", (0.46 * x, 0, 1.40), (0.71 * x, 0, 1.40), 0.045, 0.035, "garment_upper", "cyl"),
            (f"thigh_{s}", (0.09 * x, 0, 0.95), (0.09 * x, 0, 0.50), 0.075, 0.055, "garment_lower", "cyl"),
            (f"calf_{s}", (0.09 * x, 0, 0.50), (0.09 * x, 0, 0.10), 0.055, 0.040, "garment_lower", "cyl"),
            (f"foot_{s}", (0.09 * x, 0.035, 0.05), (0.09 * x, -0.12, 0.05), 0.045, 0.045, "footwear", "box"),
            (f"ball_{s}", (0.09 * x, -0.12, 0.03), (0.09 * x, -0.185, 0.03), 0.040, 0.030, "footwear", "box"),
        ]
        if lod <= 1:
            p.append((f"hand_{s}", (0.71 * x, 0, 1.40), (0.79 * x, 0, 1.40), 0.035, 0.030, "skin", "box"))
            for f in FINGERS:
                hd, tl = H[f"{f}_{s}"]
                r = 0.009 if f.startswith("thumb") else 0.0075
                p.append((f"{f}_{s}", tuple(hd), tuple(tl), r, r * 0.85, "skin", "cyl"))
        else:
            # The light LODs' mitten: the fingers keep their bones and carry no weight
            # (contract.json § skeleton.weights), so every LOD still plays every clip.
            p.append((f"hand_{s}", (0.71 * x, 0, 1.40), (0.86 * x, 0, 1.40), 0.035, 0.028, "skin", "box"))
    return p


RADIAL = {0: 16, 1: 10, 2: 6, 3: 4}
ATLAS = 8  # every part gets its own cell of an 8x8 UV grid: one non-overlapping set


def build_mesh(lod: int, name: str):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    deform = bm.verts.layers.deform.verify()
    tag = bm.verts.layers.int.new("part")
    groups = list(PARENT)  # vertex group index == contract bone order
    gi = {b: i for i, b in enumerate(groups)}
    mats = CONTRACT["materials"]["required"]
    seg = RADIAL[lod]
    cells = {}
    for cell, (bone, a, b, r0, r1, mat, kind) in enumerate(parts(lod)):
        a = Vector(a)
        if kind == "sphere":
            out = bmesh.ops.create_uvsphere(bm, u_segments=max(seg, 4), v_segments=max(seg // 2, 3), radius=r0)
            bmesh.ops.translate(bm, verts=out["verts"], vec=a)
            axis = Vector((0, 0, 1))
        else:
            b = Vector(b)
            d = b - a
            n = 4 if kind == "box" else seg
            out = bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r0, radius2=r1, depth=d.length)
            rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
            if kind == "box":
                rot = rot @ Matrix.Rotation(math.pi / 4, 4, "Z")
            bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=out["verts"])
            axis = d.normalized()
        verts = out["verts"]
        cells[cell] = bone
        for v in verts:
            v[tag] = cell
        par = PARENT.get(bone)
        z0 = min((v.co - a).dot(axis) for v in verts)
        z1 = max((v.co - a).dot(axis) for v in verts)
        for v in verts:
            t = 0.0 if z1 == z0 else ((v.co - a).dot(axis) - z0) / (z1 - z0)
            if kind == "cyl" and par and t < 0.05 and bone not in ("pelvis",):
                v[deform][gi[bone]] = 0.5
                v[deform][gi[par]] = 0.5
            else:
                v[deform][gi[bone]] = 1.0
        faces = {f for v in verts for f in v.link_faces}
        cu, cv = cell % ATLAS, cell // ATLAS
        for f in faces:
            f.material_index = mats.index(mat)
            f.smooth = kind != "box"
            for loop in f.loops:
                p = loop.vert.co - a
                ang = (math.atan2(p.y, p.x) / (2 * math.pi)) % 1.0
                h = 0.0 if z1 == z0 else (p.dot(axis) - z0) / (z1 - z0)
                loop[uv].uv = ((cu + 0.05 + 0.9 * ang) / ATLAS, (cv + 0.05 + 0.9 * h) / ATLAS)
    # bmesh's primitive ops do not create faces in a stable order from one run to the
    # next (the vertices are stable; the faces are not), and the exporter's index buffer
    # follows face order. Sort them, so the same script writes the same GLB bytes.
    bm.verts.index_update()
    rank = {f: i for i, f in enumerate(sorted(bm.faces, key=lambda f: sorted(v.index for v in f.verts)))}
    bm.faces.sort(key=lambda f: rank[f])
    bm.faces.index_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    # The part each vertex was built for, read back from the mesh: bmesh reuses freed
    # slots, so creation order is not the mesh's vertex order and an index range is not
    # a part. The tag is removed before export.
    ranges = {}
    for i, d in enumerate(me.attributes["part"].data):
        ranges.setdefault(cells[d.value], []).append(i)
    me.attributes.remove(me.attributes["part"])
    for m in mats:
        me.materials.append(MATERIALS[m])
    return me, groups, ranges


# -------------------------------------------------------------------------- materials
def _material(name, rgba, rough, image=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    if image is not None:
        tex = m.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = image
        tex.interpolation = "Closest"
        m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def _weave(size=64):
    """A 64 px twill, generated, so the fixture proves a texture path with no file
    whose licence could be questioned. It is a test pattern, not a cloth."""
    img = bpy.data.images.new("fixture_weave", size, size, alpha=False)
    px = []
    for y in range(size):
        for x in range(size):
            on = ((x + y) // 4) % 2 == 0
            v = 0.34 if on else 0.24
            px += [v, v * 0.92, v * 0.8, 1.0]
    img.pixels = px
    img.file_format = "PNG"
    img.pack()
    return img


def build(out: Path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    global MATERIALS
    MATERIALS = {
        "skin": _material("skin", (0.62, 0.62, 0.64, 1), 0.6),
        "eyes": _material("eyes", (0.05, 0.05, 0.06, 1), 0.2),
        "garment_upper": _material("garment_upper", (1, 1, 1, 1), 0.85, _weave()),
        "garment_lower": _material("garment_lower", (0.22, 0.24, 0.30, 1), 0.9),
        "footwear": _material("footwear", (0.10, 0.09, 0.08, 1), 0.5),
    }

    rig_col = bpy.data.collections.new("rig")
    scene.collection.children.link(rig_col)
    arm = bpy.data.armatures.new(CONTRACT["skeleton"]["id"])
    rig = bpy.data.objects.new("c4d_armature", arm)
    rig_col.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for b, _ in CONTRACT["skeleton"]["bones"]:
        eb = arm.edit_bones.new(b)
        eb.head, eb.tail = H[b]
        eb.roll = 0.0
    for b, p in CONTRACT["skeleton"]["bones"]:
        if p:
            arm.edit_bones[b].parent = arm.edit_bones[p]
            arm.edit_bones[b].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")

    for sock, bone, rx in (("socket_hand_l", "hand_l", 90), ("socket_hand_r", "hand_r", 90),
                           ("socket_head", "head", -90)):
        e = bpy.data.objects.new(sock, None)
        e.empty_display_size = 0.05
        rig_col.objects.link(e)
        e.parent = rig
        e.parent_type = "BONE"
        e.parent_bone = bone
        hd, tl = H[bone]
        world = Matrix.Translation(tl if bone == "head" else (hd + tl) / 2) @ Matrix.Rotation(math.radians(rx), 4, "X")
        bpy.context.view_layer.update()
        e.matrix_world = world

    for lod in CONTRACT["lods"]["levels"]:
        col = bpy.data.collections.new(f"lod{lod}")
        scene.collection.children.link(col)
        me, groups, ranges = build_mesh(lod, f"{ASSET_ID}_lod{lod}")
        ob = bpy.data.objects.new(f"{ASSET_ID}_lod{lod}", me)
        col.objects.link(ob)
        for g in groups:
            ob.vertex_groups.new(name=g)
        ob.parent = rig
        mod = ob.modifiers.new("skin", "ARMATURE")
        mod.object = rig
        if lod in CONTRACT["morphs"]["required_lods"]:
            face(ob, ranges)

    clips(rig)
    scene["chicago4d_human"] = {
        "contract_version": CONTRACT["version"],
        "kind": "body",
        "asset_id": ASSET_ID,
        "lod": 0,
        "skeleton": CONTRACT["skeleton"]["id"],
        "grade": "reconstructed",
        "basis": "a non-historical pipeline fixture, built from primitives by "
                 "tools/human_fixture_blend.py to prove Blender -> GLB -> browser; "
                 "it depicts nobody and no scene binds it",
        "sources": [],
        "liberty": "L417",
        "license": "CC0-1.0",
        "master": "tools/human_fixture_blend.py",
        "authored_by": "chicago4d steward loop (T-1787)",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)


def face(ob, ranges):
    me = ob.data
    ob.shape_key_add(name="Basis")
    for side in ("Left", "Right"):
        k = ob.shape_key_add(name=f"eyeBlink{side}")
        c = H["eye_l" if side == "Left" else "eye_r"][0]
        for i in ranges["eye_l" if side == "Left" else "eye_r"]:
            v = me.vertices[i].co
            k.data[i].co = Vector((v.x, v.y, c.z + (v.z - c.z) * 0.08))
    k = ob.shape_key_add(name="jawOpen")
    pivot = H["jaw"][0]
    rot = Matrix.Rotation(math.radians(18), 3, "X")
    for i in ranges["jaw"]:
        k.data[i].co = pivot + rot @ (me.vertices[i].co - pivot)


def clips(rig):
    """In place, contract bones only: `idle` breathes and `walk` swings, 1 s a stride."""
    rig.animation_data_create()
    pb = rig.pose.bones
    for b in pb:
        b.rotation_mode = "XYZ"

    def key(action_name, frames):
        act = bpy.data.actions.new(action_name)
        act.use_fake_user = True
        rig.animation_data.action = act
        for f, pose in frames:
            for b in pb:
                b.rotation_euler = (0, 0, 0)
            for bone, (x, y, z) in pose.items():
                pb[bone].rotation_euler = (math.radians(x), math.radians(y), math.radians(z))
            for bone in sorted({b for _, p in frames for b in p}):
                pb[bone].keyframe_insert("rotation_euler", frame=f)
        return act

    idle = key("idle", [(1, {"spine_02": (0, 0, 0), "head": (0, 0, 0)}),
                        (31, {"spine_02": (2, 0, 0), "head": (-2, 0, 3)}),
                        (61, {"spine_02": (0, 0, 0), "head": (0, 0, 0)})])
    s = 28  # thigh swing, degrees
    walk = key("walk", [
        (1, {"thigh_l": (s, 0, 0), "thigh_r": (-s, 0, 0), "calf_l": (0, 0, 0), "calf_r": (-30, 0, 0),
             "upperarm_l": (0, 0, -20), "upperarm_r": (0, 0, -20)}),
        (16, {"thigh_l": (-s, 0, 0), "thigh_r": (s, 0, 0), "calf_l": (-30, 0, 0), "calf_r": (0, 0, 0),
              "upperarm_l": (0, 0, 20), "upperarm_r": (0, 0, 20)}),
        (31, {"thigh_l": (s, 0, 0), "thigh_r": (-s, 0, 0), "calf_l": (0, 0, 0), "calf_r": (-30, 0, 0),
              "upperarm_l": (0, 0, -20), "upperarm_r": (0, 0, -20)}),
    ])
    walk["speed_m_s"] = 1.3
    rig.animation_data.action = None
    for b in pb:
        b.rotation_euler = (0, 0, 0)
    return idle, walk


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1:
        print("usage: blender -b --factory-startup --python tools/human_fixture_blend.py -- OUT.blend")
        sys.exit(2)
    build(Path(argv[0]))
    print(f"wrote {argv[0]}")
