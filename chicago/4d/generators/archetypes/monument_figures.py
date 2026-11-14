"""monument_figures — the Fort Dearborn group's five figures on the people rigs (T-3583).

The owner, 2026-11-13, on T-3583: *"if there are a bumch of people in that monument maybe
you can use some of the existing people harness"*. So each figure's BODY is a portable-human
rig (`assets/humans/*.lodN.glb`, MakeHuman hm08, the 56-joint skeleton), posed to the joints
T-3582 read on ICHi-19208 and J. W. Taylor's 1893 print (`TARGETS` below, the same pose units
as `monument.FIGURES`), skinned, and baked to a static mesh in the monument's frame. T-3565's
ruling stands: the rigs are an ARMATURE and a body only. Of each rig's dress only the pieces
the sculpture also shows are kept, as starting shapes cast in the same bronze (the
breechcloths, Black Partridge's leggings, Mrs. Helm's gown, the surgeon's coat and
pantaloons, the child's jacket and trousers); the project's dress and variation rules do
not apply to a sculpture (`dress_1812_native.json` is not read), and no face is fitted to a
portrait of anyone — the faces are the rig's neutral hm08 face, which is what this ticket
leaves to be modelled to the sculpted ones.

## The pose, bone by bone

Pure numpy, no Blender. The rig's rest pose is read from its inverse bind matrices (a T
pose facing +z in glTF, i.e. facing the street once turned z-up). Each figure is placed as
the photographs read it:

- the TORSO (pelvis, spine, clavicles) is turned so its rest axis, pelvis to neck, lies
  along the figure's pelvis-to-neck reading and its shoulder line along the shoulders
  read, and stretched along that axis to reach the neck;
- the NECK and HEAD are aimed at the head's centre, unstretched (a stretched head is a
  different face);
- each ARM and LEG is a chain from where the torso puts its root: the upper bone aimed at
  the elbow or knee and stretched along itself to reach it, the lower one aimed at the
  wrist or ankle and stretched to it, the hand carried rigid with the forearm and the foot
  aimed at the toe, unstretched.

A vertex is moved by the weighted sum of its bones' transforms (linear blend skinning),
its normal by their rotations. Fingers, jaw, eyes and toes ride on their parents. Mrs.
Helm's legs, under the skirt in both photographs, are set standing under her hem, and the
surgeon's left arm, which neither photograph shows, lies along his side; both are said in
the liberty.

## Determinism

`monument_emit.py --check` holds the committed GLB to these bytes, so nothing here reaches
BLAS: every product is an elementwise multiply and an ordered sum, and the emitter rounds
every coordinate to 0.1 mm.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HUMANS = ROOT / "assets" / "humans"

#: The rig LOD the monument's master is built from. LOD2 is the people's walking-distance
#: level (about 6,000 body triangles); the monument is seen 5-15 m off from the walk.
LOD = 2

#: figure -> (rig, the dress pieces kept as the sculpture's starting shapes)
RIGS = {
    "warrior": ("potawatomi_man_1812",
                ("body_0", "short04_hair", "breechcloth", "leather_belt", "closed_shoes", "eyes__sclera")),
    "helm": ("lady_1812",
             ("body_0", "short04_hair", "gown_bodice", "gown_skirt", "gown_waist_band", "closed_shoes",
              "eyes__sclera")),
    "black_partridge": ("potawatomi_man_1812",
                        ("body_0", "short04_hair", "breechcloth", "stroud_leggings", "leather_belt",
                         "closed_shoes", "eyes__sclera")),
    "surgeon": ("surgeons_mate_first_infantry_1812",
                ("body_0", "short04_hair", "black_leather_stock", "coat_collar", "coat_body",
                 "coat_cuffs_scarlet", "coat_skirts", "coat_turnbacks_white", "white_waistcoat",
                 "white_pantaloons", "boot_shafts", "closed_shoes", "eyes__sclera")),
    "child": ("child_boy_1812",
              ("body_0", "short04_hair", "skeleton_jacket", "shirt_collar", "skeleton_trousers",
               "closed_shoes", "eyes__sclera")),
}

# The joints, in monument.FIGURES' pose units (x along the front to the right as the street
# sees it, y back from the front, z up off the rock). P pelvis, C the neck's root, H the
# head's centre; sh/el/wr shoulder, elbow, wrist; kn/an/to knee, ankle, toe; _r and _l the
# figure's own right and left. Every figure faces the street, so its right is at -x: the
# side each limb is put on is the one its root stands on in the photographs.
TARGETS = {
    # tomahawk in the right hand, over his head; the right leg stretched back to the west edge
    "warrior": {
        "P": (-0.60, -0.10, 0.93), "C": (-0.52, -0.38, 1.25), "H": (-0.36, -0.28, 1.42),
        "sh_r": (-0.62, -0.25, 1.31), "el_r": (-0.71, -0.34, 1.60), "wr_r": (-0.50, -0.03, 1.80),
        "sh_l": (-0.44, -0.38, 1.19), "el_l": (-0.29, -0.47, 1.11), "wr_l": (-0.12, -0.60, 1.07),
        "kn_r": (-0.73, 0.30, 0.53), "an_r": (-0.86, 0.39, 0.17), "to_r": (-0.93, 0.36, 0.10),
        "kn_l": (-0.44, -0.60, 0.44), "an_l": (-0.43, -0.11, 0.11), "to_l": (-0.49, -0.17, 0.05),
    },
    # the right arm across to the warrior; her legs, unseen, stand under the hem
    "helm": {
        "P": (0.03, -0.72, 0.85), "C": (0.03, -0.72, 1.14), "H": (-0.01, -0.72, 1.31),
        "sh_r": (-0.06, -0.72, 1.11), "el_r": (-0.21, -0.64, 1.01), "wr_r": (-0.45, -0.45, 0.98),
        "sh_l": (0.11, -0.72, 1.13), "el_l": (0.16, -0.62, 1.01), "wr_l": (0.22, -0.52, 1.14),
        "kn_r": (-0.03, -0.80, 0.47), "an_r": (-0.01, -0.70, 0.08), "to_r": (-0.02, -0.82, 0.03),
        "kn_l": (0.11, -0.78, 0.47), "an_l": (0.12, -0.66, 0.08), "to_l": (0.13, -0.78, 0.03),
    },
    # the open hand raised to the upper left (his right, as he faces the street); the other
    # arm round her; striding to the right
    "black_partridge": {
        "P": (0.42, -0.62, 0.93), "C": (0.32, -0.53, 1.49), "H": (0.27, -0.55, 1.63),
        "sh_r": (0.16, -0.46, 1.49), "el_r": (-0.09, -0.63, 1.57), "wr_r": (-0.31, -0.65, 1.69),
        "sh_l": (0.56, -0.58, 1.39), "el_l": (0.63, -0.13, 1.26), "wr_l": (0.27, -0.55, 1.18),
        "kn_r": (0.30, -0.47, 0.47), "an_r": (0.34, -0.32, 0.05), "to_r": (0.34, -0.40, 0.01),
        "kn_l": (0.58, -0.44, 0.50), "an_l": (0.83, 0.26, 0.12), "to_l": (0.92, 0.20, 0.05),
    },
    # half lying back, propped on his right arm; the left, unseen, along his side
    "surgeon": {
        "P": (-0.04, 0.12, 0.21), "C": (-0.22, -0.10, 0.35), "H": (-0.30, -0.15, 0.39),
        "face": (0.0, -0.45, 0.89),
        "el_r": (-0.18, -0.35, 0.17), "wr_r": (-0.22, -0.42, 0.02),
        "el_l": (-0.06, 0.10, 0.36), "wr_l": (0.08, 0.06, 0.30),
        "kn_r": (-0.49, -0.05, 0.26), "an_r": (-0.73, -0.25, 0.08), "to_r": (-0.81, -0.28, 0.04),
        "kn_l": (0.16, -0.10, 0.32), "an_l": (0.28, -0.22, 0.05), "to_l": (0.30, -0.30, 0.03),
    },
    # kneeling at the rock's right edge, both arms out to the right
    "child": {
        "P": (0.56, -0.72, 0.11), "C": (0.56, -0.72, 0.31), "H": (0.55, -0.72, 0.37),
        "sh_r": (0.52, -0.72, 0.28), "el_r": (0.65, -0.72, 0.34), "wr_r": (0.75, -0.72, 0.39),
        "sh_l": (0.60, -0.72, 0.29), "el_l": (0.79, -0.51, 0.33), "wr_l": (1.00, -0.30, 0.39),
        "kn_r": (0.53, -0.80, 0.02), "an_r": (0.52, -0.50, 0.03), "to_r": (0.52, -0.44, 0.00),
        "kn_l": (0.60, -0.80, 0.02), "an_l": (0.64, -0.45, 0.04), "to_l": (0.62, -0.39, 0.00),
    },
}

#: The parts of monument.FIGURES the rigs do not have, kept as they were: feathers, the
#: tomahawk, the hip ornament, Mrs. Helm's knot of hair, Black Partridge's headdress and
#: musket. (Her cloak and her skirt's fall to the rock were members here too until T-3594
#: modelled them as drapery: `DRAPED` below.)
#: Indices into each figure's list there.
PROPS = {
    "warrior": (1, 6, 12, 13),
    "helm": (1,),
    "black_partridge": (1, 2, 3, 4, 19, 20),
    "surgeon": (),
    "child": (),
}

#: The drapery modelled to the sculpture (T-3594): `monument.DRAPERY` pieces per figure. Mrs.
#: Helm's skirt, overskirt and cloak replace the cone of skirt and the cloak's two members
#: the poses had kept (her `FIGURES` parts 4, 5 and 6).
DRAPED = {
    "helm": ("helm_skirt", "helm_overskirt", "helm_cloak"),
}

#: The rest pose's head centre over the `head` joint (hm08: the joint is at the skull's
#: base, the crown about 0.15 m above it).
HEAD_CENTRE_UP_M = 0.08

_DTYPES = {5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
_COMPS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def rig_files() -> list[Path]:
    """Every rig file a figure is built from — inputs to the monument's mesh."""
    return sorted({HUMANS / f"{rig}.lod{LOD}.glb" for rig, _ in RIGS.values()})


_CACHE: dict = {}


def _load(path: Path):
    if path in _CACHE:
        return _CACHE[path]
    raw = path.read_bytes()
    jlen = struct.unpack("<I", raw[12:16])[0]
    gltf = json.loads(raw[20:20 + jlen])
    blen = struct.unpack("<I", raw[20 + jlen:24 + jlen])[0]
    blob = raw[28 + jlen:28 + jlen + blen]
    _CACHE[path] = (gltf, blob)
    return gltf, blob


def _acc(gltf, blob, i) -> np.ndarray:
    a = gltf["accessors"][i]
    bv = gltf["bufferViews"][a["bufferView"]]
    dt = np.dtype(_DTYPES[a["componentType"]])
    n = _COMPS[a["type"]]
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride") or dt.itemsize * n
    if stride == dt.itemsize * n:
        out = np.frombuffer(blob, dtype=dt, count=a["count"] * n, offset=off).reshape(a["count"], n)
    else:
        rows = [np.frombuffer(blob, dtype=dt, count=n, offset=off + k * stride) for k in range(a["count"])]
        out = np.stack(rows)
    out = out.astype(np.float64)
    if a.get("normalized"):
        out = out / float(np.iinfo(dt).max)
    return out


def _zup(v: np.ndarray) -> np.ndarray:
    """glTF y-up (x, y, z) to the archetype's z-up (x, -z, y)."""
    return np.stack([v[:, 0], -v[:, 2], v[:, 1]], axis=1)


def _rest(rig: str, keep):
    gltf, blob = _load(HUMANS / f"{rig}.lod{LOD}.glb")
    skin = gltf["skins"][0]
    names = [gltf["nodes"][j]["name"] for j in skin["joints"]]
    ibm = _acc(gltf, blob, skin["inverseBindMatrices"]).reshape(-1, 4, 4)
    heads = {}
    for name, m in zip(names, ibm):
        world = np.linalg.inv(m.T)          # glTF stores the matrix column-major
        heads[name] = _zup(world[None, :3, 3])[0]
    meshes = []
    for mesh in gltf["meshes"]:
        part = next((k for k in keep if mesh["name"] == f"{rig}_{k}_lod{LOD}"), None)
        if part is None:
            continue
        for prim in mesh["primitives"]:
            at = prim["attributes"]
            meshes.append({
                "pos": _zup(_acc(gltf, blob, at["POSITION"])),
                "nrm": _zup(_acc(gltf, blob, at["NORMAL"])),
                "jnt": _acc(gltf, blob, at["JOINTS_0"]).astype(np.int64),
                "wgt": _acc(gltf, blob, at["WEIGHTS_0"]),
                "idx": _acc(gltf, blob, prim["indices"]).astype(np.int64).reshape(-1),
            })
    return names, heads, meshes


def _unit(v):
    v = np.asarray(v, dtype=np.float64)
    n = np.sqrt(float(np.sum(v * v)))
    return v / n if n else v


def _cross(a, b):
    return np.array([a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]])


def _mat(a, b):
    """a @ b for 3x3 matrices, elementwise (no BLAS)."""
    return np.array([[float(np.sum(a[i, :] * b[:, j])) for j in range(3)] for i in range(3)])


def _apply(m, v):
    return np.array([float(np.sum(m[i, :] * v)) for i in range(3)])


def _rot_between(a, b):
    """The least rotation taking direction a onto direction b (Rodrigues)."""
    a, b = _unit(a), _unit(b)
    v = _cross(a, b)
    c = float(np.sum(a * b))
    if c < -0.999999:
        axis = _unit(_cross(a, np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])))
        return 2.0 * np.outer(axis, axis) - np.eye(3)
    k = np.array([[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]])
    return np.eye(3) + k + _mat(k, k) / (1.0 + c)


def _frame(r, u):
    u = _unit(u)
    r = _unit(r - float(np.sum(r * u)) * u)
    f = _cross(u, r)
    return np.stack([r, f, u], axis=1)     # columns: right, forward, up


def _axial(d0, sigma):
    """Stretch by sigma along direction d0, unchanged across it."""
    d = _unit(d0)
    return np.eye(3) + (sigma - 1.0) * np.outer(d, d)


class _Bones:
    """Each bone's transform v -> L v + t (on rest positions) and its rotation R."""

    def __init__(self):
        self.L, self.t, self.R = {}, {}, {}

    def set(self, name, rot, lin, root_rest, root_to):
        self.R[name] = rot
        self.L[name] = lin
        self.t[name] = np.asarray(root_to) - _apply(lin, root_rest)

    def copy(self, name, frm):
        self.R[name], self.L[name], self.t[name] = self.R[frm], self.L[frm], self.t[frm]

    def at(self, name, v):
        return _apply(self.L[name], v) + self.t[name]


def _chain(b: _Bones, J, parent_rot, bones, targets, root_to, stretch):
    """Aim each bone of `bones` at the next target, from `root_to`; return the end rotation."""
    rot, here = parent_rot, np.asarray(root_to, dtype=np.float64)
    for k, (name, nxt) in enumerate(zip(bones[:-1], bones[1:])):
        d0 = J[nxt] - J[name]
        want = np.asarray(targets[k]) - here
        r = _mat(_rot_between(_apply(rot, d0), want), rot)
        sigma = (np.sqrt(float(np.sum(want * want))) / np.sqrt(float(np.sum(d0 * d0)))) if stretch[k] else 1.0
        b.set(name, r, _mat(r, _axial(d0, sigma)), J[name], here)
        here = b.at(name, J[nxt])
        rot = r
    return rot, here


def pose(figure: str, k: float):
    """The figure posed in metres off the rock's centre: (positions, normals, triangles)."""
    rig, keep = RIGS[figure]
    names, J, meshes = _rest(rig, keep)
    T = {key: np.array(v, dtype=np.float64) * k for key, v in TARGETS[figure].items()}
    b = _Bones()

    # the torso: rest pelvis-to-neck onto P-to-C, the shoulder line onto the shoulders read
    u0 = J["neck_01"] - J["pelvis"]
    F0 = _frame(J["upperarm_r"] - J["upperarm_l"], u0)
    up = T["C"] - T["P"]
    if "sh_r" in T:
        right = T["sh_r"] - T["sh_l"]
    else:
        right = _cross(_unit(T["face"]), _unit(up))
    Ft = _frame(right, up)
    rot_t = _mat(Ft, F0.T)
    sig_t = np.sqrt(float(np.sum(up * up))) / np.sqrt(float(np.sum(u0 * u0)))
    b.set("pelvis", rot_t, _mat(rot_t, _axial(u0, sig_t)), J["pelvis"], T["P"])
    for n in ("root", "spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r"):
        b.copy(n, "pelvis")

    # the neck and head, aimed at the head's centre and not stretched
    hc0 = J["head"] + np.array([0.0, 0.0, HEAD_CENTRE_UP_M])
    neck_at = b.at("pelvis", J["neck_01"])
    r = _mat(_rot_between(_apply(rot_t, hc0 - J["neck_01"]), T["H"] - neck_at), rot_t)
    b.set("neck_01", r, r, J["neck_01"], neck_at)
    for n in ("head", "jaw", "eye_l", "eye_r"):
        b.copy(n, "neck_01")

    for s in ("l", "r"):
        rot, here = _chain(b, J, rot_t, [f"upperarm_{s}", f"lowerarm_{s}", f"hand_{s}"],
                           [T[f"el_{s}"], T[f"wr_{s}"]], b.at("pelvis", J[f"upperarm_{s}"]), (True, True))
        b.set(f"hand_{s}", rot, rot, J[f"hand_{s}"], here)
        for n in names:
            if n.endswith(f"_{s}") and n.split("_")[0] in ("thumb", "index", "middle", "ring", "pinky"):
                b.copy(n, f"hand_{s}")
        rot, here = _chain(b, J, rot_t, [f"thigh_{s}", f"calf_{s}", f"foot_{s}"],
                           [T[f"kn_{s}"], T[f"an_{s}"]], b.at("pelvis", J[f"thigh_{s}"]), (True, True))
        _chain(b, J, rot, [f"foot_{s}", f"ball_{s}"], [T[f"to_{s}"]], here, (False,))
        b.copy(f"ball_{s}", f"foot_{s}")

    missing = [n for n in names if n not in b.L]
    if missing:
        raise ValueError(f"{figure}: bones with no transform: {missing}")
    L = np.stack([b.L[n] for n in names])
    t = np.stack([b.t[n] for n in names])
    R = np.stack([b.R[n] for n in names])

    pos_out, nrm_out, tri_out, base = [], [], [], 0
    for m in meshes:
        w = m["wgt"] / np.maximum(np.sum(m["wgt"], axis=1, keepdims=True), 1e-9)
        p, nr = m["pos"], m["nrm"]
        acc_p = np.zeros_like(p)
        acc_n = np.zeros_like(nr)
        for slot in range(4):
            j = m["jnt"][:, slot]
            ws = w[:, slot][:, None]
            Lj, tj, Rj = L[j], t[j], R[j]
            moved = np.sum(Lj * p[:, None, :], axis=2) + tj
            turned = np.sum(Rj * nr[:, None, :], axis=2)
            acc_p = acc_p + ws * moved
            acc_n = acc_n + ws * turned
        acc_n = acc_n / np.maximum(np.sqrt(np.sum(acc_n * acc_n, axis=1, keepdims=True)), 1e-9)
        pos_out.append(acc_p)
        nrm_out.append(acc_n)
        tri_out.append(m["idx"] + base)
        base += len(p)
    return np.concatenate(pos_out), np.concatenate(nrm_out), np.concatenate(tri_out)
