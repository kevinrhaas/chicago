#!/usr/bin/env python3
"""The portable human contract's gate (T-1786).

docs/HUMAN-ASSET-CONTRACT.md is the contract; data/humans/contract.json is its
machine-readable half and data/humans/human_instance.schema.json the instance record.
This tool holds all three to each other and holds anything that claims to follow them
to the contract:

  --check            the contract to its own rules (one rooted skeleton, every _l bone
                     with its _r twin, disjoint vocabularies, the schema's patterns the
                     contract's), then every GLB under assets/humans/ and every instance
                     under data/humans/instances/<scene>/. Run by check.sh.
  --glb FILE...      one or more GLBs, as an exporter (T-1787) will call it.
  --instance FILE... one or more instance records.
  --self-test        builds a conforming synthetic GLB and instance, proves they pass,
                     then breaks each in the ways the contract names (an incompatible
                     skeleton, a missing material slot or morph, duplicate clip names,
                     non-metric scale, missing provenance or licence, …) and requires
                     the named refusal for each.

Every refusal carries a code (`skeleton.missing_bone`) and a sentence saying what to
fix, because the ticket's own words are that a future exporter "must fail clearly".
It reads the GLB's JSON chunk only — names, hierarchy, accessor bounds, extras — so it
needs no decoder and runs in well under a second.
"""
from __future__ import annotations

import json
import math
import re
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "data/humans/contract.json"
SCHEMA = ROOT / "data/humans/human_instance.schema.json"
ASSETS = ROOT / "assets/humans"
INSTANCES = ROOT / "data/humans/instances"
SOURCES = ROOT / "data/sources"
SCENES = ROOT / "data/scenes"
SIDECARS = ROOT / "data/sidecars"
LIBERTIES = ROOT / "docs/LIBERTIES.md"


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


class Finding:
    def __init__(self, code: str, msg: str):
        self.code, self.msg = code, msg

    def __str__(self):
        return f"{self.code}: {self.msg}"


# --------------------------------------------------------------------------- contract

def check_contract(c: dict, schema: dict) -> list[Finding]:
    out: list[Finding] = []
    sk = c["skeleton"]
    names = [b for b, _ in sk["bones"]]
    seen: set[str] = set()
    for b, parent in sk["bones"]:
        if b in seen:
            out.append(Finding("contract.duplicate_bone", f"bone {b!r} is declared twice"))
        if parent is None:
            if b != sk["root"]:
                out.append(Finding("contract.second_root", f"{b!r} has no parent; only {sk['root']!r} may"))
        elif parent not in seen:
            out.append(Finding("contract.unknown_parent",
                               f"{b!r} names parent {parent!r}, which is not declared above it"))
        if b.startswith(sk["extension_prefix"]):
            out.append(Finding("contract.extension_in_core", f"{b!r} is an extension name in the core list"))
        seen.add(b)
    if names and names[0] != sk["root"]:
        out.append(Finding("contract.root_first", f"the first bone must be the root {sk['root']!r}"))
    parent_of = dict(sk["bones"])
    for b in names:
        for a, z in (("_l", "_r"), ("_r", "_l")):
            if b.endswith(a):
                twin = b[: -len(a)] + z
                if twin not in parent_of:
                    out.append(Finding("contract.asymmetric", f"{b!r} has no twin {twin!r}"))
                else:
                    p, tp = parent_of[b], parent_of[twin]
                    want = p[: -len(a)] + z if p and p.endswith(a) else p
                    if tp != want:
                        out.append(Finding("contract.asymmetric",
                                           f"{b!r} hangs from {p!r} but {twin!r} from {tp!r}"))
    for group in ("required", "optional"):
        for sock, bone in c["sockets"][group]:
            if not sock.startswith("socket_"):
                out.append(Finding("contract.socket_name", f"{sock!r} does not start socket_"))
            if bone not in parent_of:
                out.append(Finding("contract.socket_bone", f"{sock!r} rides on undeclared bone {bone!r}"))
    for key in ("materials", "morphs"):
        req, opt = c[key]["required"], c[key]["optional"]
        if len(set(req)) != len(req) or len(set(opt)) != len(opt) or set(req) & set(opt):
            out.append(Finding(f"contract.{key}_vocabulary",
                               f"{key}: a name is repeated, or both required and optional"))
    slot_re = re.compile(c["materials"]["name_pattern"])
    for s in c["materials"]["required"] + c["materials"]["optional"]:
        m = slot_re.match(s)
        if not m or m.group("variant"):
            out.append(Finding("contract.slot_name", f"slot {s!r} does not read as a bare slot"))
    clip_re = re.compile(c["clips"]["name_pattern"])
    for clip in c["clips"]["required_for_actor"]:
        if not clip_re.match(clip) or clip.split("_")[0] not in c["clips"]["verbs"]:
            out.append(Finding("contract.clip_name", f"required clip {clip!r} breaks the clip grammar"))
    levels = set(c["lods"]["levels"])
    for tier, lods in c["lods"]["tiers"].items():
        if not set(lods) <= levels:
            out.append(Finding("contract.tier_lods", f"tier {tier!r} names a LOD that does not exist"))
    if not set(c["morphs"]["required_lods"]) <= levels:
        out.append(Finding("contract.tier_lods", "morphs.required_lods names a LOD that does not exist"))
    if set(c["delivery"]["allowed_extensions"]) & set(c["delivery"]["refused_extensions"]):
        out.append(Finding("contract.delivery", "an extension is both allowed and refused"))
    # The schema restates three of the contract's vocabularies; one definition each.
    props = schema["properties"]
    if props["animation"]["properties"]["clip"]["pattern"] != c["clips"]["name_pattern"]:
        out.append(Finding("contract.pattern_drift",
                           "the instance schema's clip pattern is not the contract's clips.name_pattern"))
    if props["provenance"]["properties"]["grade"]["enum"] != c["provenance"]["grades"]:
        out.append(Finding("contract.pattern_drift",
                           "the instance schema's grades are not the contract's provenance.grades"))
    if props["contract_version"]["const"] != c["version"]:
        out.append(Finding("contract.pattern_drift", "the instance schema's contract_version is not the contract's"))
    try:
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(schema)
    except ImportError:
        out.append(Finding("contract.no_jsonschema",
                           "jsonschema is not installed (pip install jsonschema); a skip is not a pass"))
    except Exception as e:  # SchemaError
        out.append(Finding("contract.schema_invalid", f"the instance schema is not valid 2020-12: {e}"))
    return out


# --------------------------------------------------------------------------- GLB

def read_glb(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise ValueError("not a binary glTF (no glTF magic)")
    version, length = struct.unpack_from("<II", data, 4)
    if version != 2:
        raise ValueError(f"glTF version {version}, the contract is glTF 2.0")
    clen, ctype = struct.unpack_from("<II", data, 12)
    if ctype != 0x4E4F534A:
        raise ValueError("first chunk is not JSON")
    return json.loads(data[20:20 + clen].decode("utf-8"))


def _quat_mat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def _local(node) -> list[list[float]]:
    if "matrix" in node:
        m = node["matrix"]  # column-major
        return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
    t = node.get("translation", [0, 0, 0])
    r = _quat_mat(node.get("rotation", [0, 0, 0, 1]))
    s = node.get("scale", [1, 1, 1])
    return [[r[i][0] * s[0], r[i][1] * s[1], r[i][2] * s[2], t[i]] for i in range(3)] + [[0, 0, 0, 1]]


def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _node_scale(node) -> list[float]:
    if "matrix" in node:
        m = _local(node)
        return [math.sqrt(sum(m[r][c] ** 2 for r in range(3))) for c in range(3)]
    return node.get("scale", [1, 1, 1])


def check_glb(path: Path, c: dict, sources: set[str] | None = None) -> list[Finding]:
    out: list[Finding] = []
    try:
        g = read_glb(path)
    except Exception as e:
        return [Finding("glb.unreadable", f"{e}")]
    sources = known_sources() if sources is None else sources
    nodes = g.get("nodes", [])
    name_of = [n.get("name", f"#{i}") for i, n in enumerate(nodes)]
    parent: dict[int, int] = {}
    for i, n in enumerate(nodes):
        for ch in n.get("children", []):
            parent[ch] = i

    # --- provenance first: it says what kind of file this is
    scenes = g.get("scenes") or [{}]
    prov = (scenes[g.get("scene", 0)].get("extras") or {}).get("chicago4d_human")
    m = re.match(c["lods"]["file_pattern"], path.name)
    if not m:
        out.append(Finding("provenance.file_name",
                           f"{path.name!r} is not named <asset_id>.lod<0-3>.glb"))
    if not isinstance(prov, dict):
        out.append(Finding("provenance.missing",
                           "no scenes[].extras.chicago4d_human block (export the Blender scene's custom properties)"))
        prov = {}
    for f in c["provenance"]["required_fields"]:
        if prov and (f not in prov or prov[f] in (None, "", [])):
            out.append(Finding("provenance.missing_field", f"chicago4d_human.{f} is missing or empty"))
    kind = prov.get("kind", "body")
    if prov:
        if prov.get("contract_version") not in (None, c["version"]):
            out.append(Finding("provenance.contract_version",
                               f"built to contract v{prov.get('contract_version')}, this is v{c['version']}"))
        if prov.get("skeleton") not in (None, c["skeleton"]["id"]):
            out.append(Finding("skeleton.incompatible",
                               f"declares skeleton {prov.get('skeleton')!r}, the contract's is {c['skeleton']['id']!r}"))
        if kind not in c["provenance"]["kinds"]:
            out.append(Finding("provenance.kind", f"kind {kind!r} is not one of {sorted(c['provenance']['kinds'])}"))
        if m and prov.get("asset_id") not in (None, m.group("asset_id")):
            out.append(Finding("provenance.asset_mismatch",
                               f"asset_id {prov.get('asset_id')!r} but the file is {m.group('asset_id')!r}"))
        if m and prov.get("lod") is not None and prov.get("lod") != int(m.group("lod")):
            out.append(Finding("provenance.lod_mismatch",
                               f"lod {prov.get('lod')} but the file is lod{m.group('lod')}"))
        grade = prov.get("grade")
        if grade is not None and grade not in c["provenance"]["grades"]:
            out.append(Finding("provenance.grade", f"grade {grade!r} is not one of {c['provenance']['grades']}"))
        cited = prov.get("sources") or []
        for s in cited:
            if s not in sources:
                out.append(Finding("provenance.unknown_source", f"source {s!r} does not resolve in data/sources/"))
        if grade == "attested" and not cited:
            out.append(Finding("provenance.attested_unsourced", "an attested depiction names no source"))
        if grade == "reconstructed" and not prov.get("liberty"):
            out.append(Finding("provenance.liberty_missing",
                               "a reconstructed depiction names no docs/LIBERTIES.md entry in `liberty`"))
        lic = str(prov.get("license") or "")
        if lic.strip().lower() in ("check_required", "unknown", "tbd"):
            out.append(Finding("provenance.license",
                               f"licence {lic!r} is not one the repository can honour (AGENTS.md rule 6)"))

    # --- delivery: what the browser can open
    for ext in g.get("extensionsUsed", []):
        why = c["delivery"]["refused_extensions"].get(ext)
        if why:
            out.append(Finding("delivery.refused_extension", f"{ext}: {why}"))
        elif ext not in c["delivery"]["allowed_extensions"]:
            out.append(Finding("delivery.unknown_extension",
                               f"{ext} is not in the contract's allowed list; prove the loader, then add it"))

    # --- skeleton
    sk = c["skeleton"]
    want_parent = dict(sk["bones"])
    skins = g.get("skins", [])
    if not skins:
        out.append(Finding("skeleton.no_skin", "no skin: a human GLB carries the contract skeleton as a glTF skin"))
        return out
    joint_sets = [tuple(sorted(s.get("joints", []))) for s in skins]
    if len(set(joint_sets)) > 1:
        out.append(Finding("skeleton.split", "more than one skin, over different joints"))
    joints = skins[0].get("joints", [])
    jnames = {name_of[j]: j for j in joints}
    if len(jnames) != len(joints):
        out.append(Finding("skeleton.duplicate_bone", "two joints share a name"))
    for b in want_parent:
        if b not in jnames:
            out.append(Finding("skeleton.missing_bone", f"contract bone {b!r} is not a joint of the skin"))
    for b in jnames:
        if b not in want_parent and not b.startswith(sk["extension_prefix"]):
            out.append(Finding("skeleton.unknown_bone",
                               f"{b!r} is neither a contract bone nor an {sk['extension_prefix']}* extension"))
    for b, j in jnames.items():
        if b not in want_parent:
            continue
        # Walk up to the nearest joint: an ext_ bone in between is a contract bone hung
        # under an extension, which an engine that drops extensions cannot rebuild.
        p = parent.get(j)
        while p is not None and name_of[p] not in jnames:
            p = parent.get(p)
        got = name_of[p] if p is not None else None
        if got is not None and got.startswith(sk["extension_prefix"]):
            out.append(Finding("skeleton.under_extension", f"{b!r} hangs under extension bone {got!r}"))
        elif got != want_parent[b]:
            out.append(Finding("skeleton.wrong_parent",
                               f"{b!r} hangs from {got!r}; the contract says {want_parent[b]!r}"))

    # --- frame: no hidden scale anywhere above a joint or a mesh, root on the ground
    def chain(i):
        while i is not None:
            yield i
            i = parent.get(i)
    checked: set[int] = set()
    mesh_nodes = [i for i, n in enumerate(nodes) if "mesh" in n]
    for start in list(jnames.values()) + mesh_nodes:
        for i in chain(start):
            if i in checked:
                break
            checked.add(i)
            s = _node_scale(nodes[i])
            if any(abs(v - 1) > 1e-6 for v in s):
                out.append(Finding("frame.node_scale",
                                   f"node {name_of[i]!r} carries scale {s}; size belongs in vertex positions, not a transform"))
    if "root" in jnames:
        w = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        for i in reversed(list(chain(jnames["root"]))):
            w = _mul(w, _local(nodes[i]))
        x, y, z = w[0][3], w[1][3], w[2][3]
        lim = c["frame"]["max_root_offset_m"]
        if abs(y) > lim or math.hypot(x, z) > lim:
            out.append(Finding("frame.origin",
                               f"root bone stands at ({x:.3f}, {y:.3f}, {z:.3f}) m; it belongs at the origin, on the ground"))

    meshes = g.get("meshes", [])
    accessors = g.get("accessors", [])
    if kind == "body":
        if not mesh_nodes:
            out.append(Finding("body.no_mesh", "a body has no mesh node"))
        lo, hi = [math.inf] * 3, [-math.inf] * 3
        slots: set[str] = set()
        morphs: set[str] = set()
        slot_re = re.compile(c["materials"]["name_pattern"])
        known_slots = set(c["materials"]["required"]) | set(c["materials"]["optional"])
        materials = g.get("materials", [])
        for i in mesh_nodes:
            mesh = meshes[nodes[i]["mesh"]]
            if "skin" not in nodes[i]:
                out.append(Finding("body.unskinned", f"mesh node {name_of[i]!r} is not bound to the skin"))
            tnames = (mesh.get("extras") or {}).get("targetNames") or []
            morphs.update(tnames)
            for prim in mesh.get("primitives", []):
                attrs = prim.get("attributes", {})
                if "JOINTS_1" in attrs or "WEIGHTS_1" in attrs:
                    out.append(Finding("skeleton.influences",
                                       f"{name_of[i]!r} carries JOINTS_1/WEIGHTS_1: more than {sk['max_influences_per_vertex']} influences per vertex"))
                if len(prim.get("targets", [])) != len(tnames):
                    out.append(Finding("morph.unnamed",
                                       f"{name_of[i]!r} has {len(prim.get('targets', []))} morph targets and {len(tnames)} names"))
                acc = accessors[attrs["POSITION"]] if "POSITION" in attrs else {}
                if "min" in acc and "max" in acc:
                    lo = [min(a, b) for a, b in zip(lo, acc["min"])]
                    hi = [max(a, b) for a, b in zip(hi, acc["max"])]
                if "material" in prim:
                    mname = materials[prim["material"]].get("name", "")
                    mm = slot_re.match(mname)
                    slot = mm.group("slot") if mm else None
                    if slot not in known_slots:
                        out.append(Finding("material.unknown_slot",
                                           f"material {mname!r} is not <slot> or <slot>__<variant> on a contract slot"))
                    else:
                        slots.add(slot)
        for s in c["materials"]["required"]:
            if s not in slots:
                out.append(Finding("material.missing_slot", f"required material slot {s!r} is on no primitive"))
        if lo[1] != math.inf:
            height = hi[1] - lo[1]
            hb = c["frame"]["rest_height_m"]
            if not (hb["min"] <= height <= hb["max"]):
                out.append(Finding("frame.height",
                                   f"rest height {height:.3f} — outside {hb['min']}-{hb['max']} m; "
                                   f"non-metric scale? (a 1.75 m adult in centimetres reads 175)"))
            if abs(lo[1]) > 0.05:
                out.append(Finding("frame.origin", f"the soles stand at y = {lo[1]:.3f}; they belong at y = 0"))
        else:
            out.append(Finding("frame.no_bounds", "no POSITION accessor carries min/max, so scale cannot be read"))
        known_morphs = set(c["morphs"]["required"]) | set(c["morphs"]["optional"])
        for t in sorted(morphs):
            if t not in known_morphs and not t.startswith("ext_"):
                out.append(Finding("morph.unknown", f"morph {t!r} is not in the contract's vocabulary (or ext_*)"))
        lod = prov.get("lod", int(m.group("lod")) if m else 0)
        if lod in c["morphs"]["required_lods"]:
            for t in c["morphs"]["required"]:
                if t not in morphs:
                    out.append(Finding("morph.missing_required", f"lod{lod} owes the face: morph {t!r} is missing"))
        for sock, bone in c["sockets"]["required"]:
            idx = [i for i, n in enumerate(name_of) if n == sock]
            if not idx:
                out.append(Finding("socket.missing", f"socket {sock!r} is missing"))
            elif parent.get(idx[0]) is None or name_of[parent[idx[0]]] != bone:
                out.append(Finding("socket.wrong_bone", f"socket {sock!r} is not a child of {bone!r}"))
    elif kind == "clips" and not g.get("animations"):
        out.append(Finding("clip.none", "a clip library carries no animations"))

    # --- clips
    clip_re = re.compile(c["clips"]["name_pattern"])
    seen: set[str] = set()
    for a in g.get("animations", []):
        n = a.get("name", "")
        if n in seen:
            out.append(Finding("clip.duplicate", f"two clips are named {n!r}"))
        seen.add(n)
        if not clip_re.match(n):
            out.append(Finding("clip.bad_name", f"clip {n!r} is not lower snake case <verb>[_<variant>]"))
        elif n.split("_")[0] not in c["clips"]["verbs"]:
            out.append(Finding("clip.unknown_verb", f"clip {n!r}: verb not in {c['clips']['verbs']}"))
        for ch in a.get("channels", []):
            t = ch.get("target", {})
            if t.get("path") == "weights":
                continue
            node = t.get("node")
            nm = name_of[node] if node is not None and node < len(name_of) else None
            if nm not in want_parent:
                out.append(Finding("clip.off_skeleton",
                                   f"clip {n!r} animates {nm!r}, which is not a contract bone"))
                break
    return out


# --------------------------------------------------------------------------- instances

def known_sources() -> set[str]:
    return {p.stem for p in SOURCES.glob("*.json")}


def liberty_ids() -> set[str]:
    return set(re.findall(r"^### (L[0-9]+) ", LIBERTIES.read_text(encoding="utf-8"), re.M))


_people_cache: dict[str, dict | None] = {}


def people_of(scene: str):
    if scene not in _people_cache:
        p = SIDECARS / scene / "people.json"
        _people_cache[scene] = {r["id"]: r for r in load_json(p)["people"]} if p.exists() else None
    return _people_cache[scene]


def check_instance(rec, c: dict, schema: dict, where: str = "", ctx: dict | None = None) -> list[Finding]:
    from jsonschema import Draft202012Validator
    out: list[Finding] = []
    ctx = ctx if ctx is not None else {}
    errs = sorted(Draft202012Validator(schema).iter_errors(rec), key=lambda e: list(e.path))
    for e in errs:
        out.append(Finding("instance.schema", f"{'/'.join(map(str, e.path)) or '(record)'}: {e.message}"))
    if errs or not isinstance(rec, dict):
        return out
    scene = rec["scene"]
    if where:
        p = Path(where)
        if p.parent.name != scene or p.stem != rec["id"]:
            out.append(Finding("instance.location",
                               f"{p.parent.name}/{p.name} must be instances/{scene}/{rec['id']}.json"))
    if not (SCENES / f"{scene}.json").exists():
        out.append(Finding("instance.unknown_scene", f"scene {scene!r} has no data/scenes/{scene}.json"))
    people = people_of(scene)
    person = None
    if people is None:
        out.append(Finding("instance.no_people_layer",
                           f"scene {scene!r} has no people layer (data/sidecars/{scene}/people.json) to bind to"))
    else:
        person = people.get(rec["person_id"])
        if person is None:
            out.append(Finding("instance.unknown_person",
                               f"person {rec['person_id']!r} is not in data/sidecars/{scene}/people.json; this file never mints a person"))
    key = (scene, rec["person_id"])
    seen = ctx.setdefault("persons", {})
    if key in seen:
        out.append(Finding("instance.duplicate_person",
                           f"{rec['person_id']!r} already stands in {scene} as {seen[key]!r}"))
    seen[key] = rec["id"]
    flagged = bool(person and (person.get("review_required") or person.get("touches_removal")))
    if flagged and not rec["review_required"]:
        out.append(Finding("instance.review_dropped",
                           f"{rec['person_id']!r} is review_required on their record; the instance must say so too"))
    if rec["display"] == "shown":
        if c["l1"]["in_force"]:
            out.append(Finding("instance.l1",
                               "display `shown` while L1 stands: no human figure is drawn, for anyone (AGENTS.md)"))
        if rec["review_required"]:
            out.append(Finding("instance.review_unmet",
                               "a review_required person is shown before any review is recorded"))
    slots = set(c["materials"]["required"]) | set(c["materials"]["optional"])
    for s in (rec["appearance"].get("variants") or {}):
        if s not in slots:
            out.append(Finding("instance.unknown_slot", f"variant on {s!r}, which is not a contract material slot"))
    verb = rec["animation"]["clip"].split("_")[0]
    if verb not in c["clips"]["verbs"]:
        out.append(Finding("instance.unknown_verb", f"clip {rec['animation']['clip']!r}: verb not in the contract"))
    pv = rec["provenance"]
    srcs = ctx.get("sources") if "sources" in ctx else ctx.setdefault("sources", known_sources())
    for s in pv.get("sources", []):
        if s not in srcs:
            out.append(Finding("instance.unknown_source", f"source {s!r} does not resolve in data/sources/"))
    if pv["grade"] == "attested" and not pv.get("sources"):
        out.append(Finding("instance.attested_unsourced", "an attested depiction names no source"))
    if pv["grade"] == "reconstructed":
        libs = ctx.get("liberties") if "liberties" in ctx else ctx.setdefault("liberties", liberty_ids())
        if not pv.get("liberty"):
            out.append(Finding("instance.liberty_missing", "a reconstructed depiction names no LIBERTIES entry"))
        elif pv["liberty"] not in libs:
            out.append(Finding("instance.liberty_missing", f"{pv['liberty']} is not a heading in docs/LIBERTIES.md"))
    if rec["display"] == "shown":
        lod0 = ASSETS / f"{rec['appearance']['asset_id']}.lod0.glb"
        if not lod0.exists():
            out.append(Finding("instance.no_asset", f"shown, and {lod0.relative_to(ROOT)} does not exist"))
    return out


# --------------------------------------------------------------------------- self-test

def synth_gltf(c: dict, lod: int = 0) -> dict:
    """A conforming body, built from the contract itself, so the test moves with it."""
    bones = c["skeleton"]["bones"]
    idx = {b: i + 1 for i, (b, _) in enumerate(bones)}  # node 0 is the armature
    nodes = [{"name": "c4d_armature", "children": [idx["root"]]}]
    for b, p in bones:
        t = [0, 0, 0] if b == "root" else [0, 1.0 if b == "pelvis" else 0.1, 0]
        nodes.append({"name": b, "translation": t, "children": []})
    for b, p in bones:
        if p:
            nodes[idx[p]]["children"].append(idx[b])
    for sock, bone in c["sockets"]["required"]:
        nodes.append({"name": sock})
        nodes[idx[bone]]["children"].append(len(nodes) - 1)
    body = len(nodes)
    nodes.append({"name": "body", "mesh": 0, "skin": 0})
    morphs = c["morphs"]["required"] if lod in c["morphs"]["required_lods"] else []
    prims = [{"attributes": {"POSITION": 0, "JOINTS_0": 1, "WEIGHTS_0": 2}, "material": i,
              "targets": [{"POSITION": 0} for _ in morphs]}
             for i, _ in enumerate(c["materials"]["required"])]
    return {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0, body], "extras": {"chicago4d_human": {
            "contract_version": c["version"], "kind": "body", "asset_id": "fixture_body",
            "lod": lod, "skeleton": c["skeleton"]["id"], "grade": "reconstructed",
            "basis": "a synthetic fixture built by tools/human_contract.py --self-test",
            "license": "CC0-1.0", "master": "none (synthetic)", "authored_by": "self-test",
            "liberty": "L1", "sources": []}}}],
        "nodes": nodes,
        "skins": [{"joints": [idx[b] for b, _ in bones]}],
        "meshes": [{"primitives": prims, "extras": {"targetNames": list(morphs)}}],
        "materials": [{"name": s} for s in c["materials"]["required"]],
        "accessors": [{"count": 3, "type": "VEC3", "componentType": 5126,
                       "min": [-0.9, 0.0, -0.15], "max": [0.9, 1.78, 0.15]},
                      {"count": 3, "type": "VEC4", "componentType": 5121},
                      {"count": 3, "type": "VEC4", "componentType": 5126}],
        "animations": [{"name": n, "channels": [{"sampler": 0, "target": {"node": idx["pelvis"], "path": "rotation"}}],
                        "samplers": [{"input": 0, "output": 0}]} for n in ("idle", "walk", "gesture_point")],
    }


def write_glb(g: dict, path: Path):
    js = json.dumps(g).encode("utf-8")
    js += b" " * (-len(js) % 4)
    path.write_bytes(b"glTF" + struct.pack("<II", 2, 12 + 8 + len(js))
                     + struct.pack("<II", len(js), 0x4E4F534A) + js)


def self_test() -> int:
    import copy
    c, schema = load_json(CONTRACT), load_json(SCHEMA)
    fails = 0

    def expect(label, findings, code):
        nonlocal fails
        codes = [f.code for f in findings]
        ok = (not codes) if code is None else (code in codes)
        print(f"  {'ok  ' if ok else 'FAIL'} {label}: "
              + ("clean" if not codes else "; ".join(map(str, findings))[:220]))
        if not ok:
            fails += 1
            print(f"       wanted {code or 'no finding'}")

    print("the contract")
    expect("the committed contract holds to its own rules", check_contract(c, schema), None)
    for label, mut, code in [
        ("a bone declared twice", lambda k: k["skeleton"]["bones"].append(["pelvis", "root"]), "contract.duplicate_bone"),
        ("a bone whose parent is not declared", lambda k: k["skeleton"]["bones"].append(["toe_l", "nowhere"]), "contract.unknown_parent"),
        ("a left bone with no right twin", lambda k: k["skeleton"]["bones"].append(["toe_l", "ball_l"]), "contract.asymmetric"),
        ("a morph both required and optional", lambda k: k["morphs"]["optional"].append("jawOpen"), "contract.morphs_vocabulary"),
        ("the schema's clip pattern drifting from the contract's",
         lambda k: k["clips"].__setitem__("name_pattern", "^[a-z]+$"), "contract.pattern_drift"),
    ]:
        k = copy.deepcopy(c)
        mut(k)
        expect(label, check_contract(k, schema), code)

    srcs = known_sources() | {"fixture_portrait"}
    with tempfile.TemporaryDirectory() as td:
        def glb(g, name="fixture_body.lod0.glb"):
            p = Path(td) / name
            write_glb(g, p)
            return check_glb(p, c, srcs)

        def bone_node(g, b):
            return next(i for i, n in enumerate(g["nodes"]) if n.get("name") == b)

        print("GLB — conforming fixtures pass")
        expect("a conforming lod0 body", glb(synth_gltf(c, 0)), None)
        expect("a conforming lod2 body without a face", glb(synth_gltf(c, 2), "fixture_body.lod2.glb"), None)
        g = synth_gltf(c)
        ext = len(g["nodes"])
        g["nodes"].append({"name": "ext_coat_tail"})
        g["nodes"][bone_node(g, "pelvis")]["children"].append(ext)
        g["skins"][0]["joints"].append(ext)
        expect("an ext_ leaf bone", glb(g), None)

        print("GLB — each named incompatibility is refused, by name")

        def mutate(fn, lod=0, name=None):
            g = synth_gltf(c, lod)
            fn(g)
            return glb(g, name or f"fixture_body.lod{lod}.glb")

        def drop_joint(g, b):
            j = bone_node(g, b)
            g["skins"][0]["joints"].remove(j)
            g["nodes"][j]["name"] = "stray"

        def reparent(g, b, newp):
            j = bone_node(g, b)
            for n in g["nodes"]:
                if j in n.get("children", []):
                    n["children"].remove(j)
            g["nodes"][bone_node(g, newp)]["children"].append(j)

        def insert_ext(g):
            neck, sp = bone_node(g, "neck_01"), bone_node(g, "spine_03")
            g["nodes"][sp]["children"].remove(neck)
            g["nodes"].append({"name": "ext_collar", "children": [neck]})
            e = len(g["nodes"]) - 1
            g["nodes"][sp]["children"].append(e)
            g["skins"][0]["joints"].append(e)

        def scale_positions(g, f):
            for a in g["accessors"][:1]:
                a["min"] = [v * f for v in a["min"]]
                a["max"] = [v * f for v in a["max"]]

        def prov(g):
            return g["scenes"][0]["extras"]["chicago4d_human"]

        def strip_face(g):
            for p in g["meshes"][0]["primitives"]:
                p["targets"] = []
            g["meshes"][0]["extras"]["targetNames"] = []

        cases = [
            ("a missing contract bone (hand_l)", lambda g: drop_joint(g, "hand_l"), "skeleton.missing_bone"),
            ("a renamed bone (spine_02 -> spine2)",
             lambda g: g["nodes"][bone_node(g, "spine_02")].__setitem__("name", "spine2"), "skeleton.unknown_bone"),
            ("a reparented bone (calf_l under pelvis)", lambda g: reparent(g, "calf_l", "pelvis"), "skeleton.wrong_parent"),
            ("a contract bone hung under an ext_ bone", insert_ext, "skeleton.under_extension"),
            ("a different declared skeleton", lambda g: prov(g).__setitem__("skeleton", "mixamo"), "skeleton.incompatible"),
            ("more than four influences per vertex",
             lambda g: g["meshes"][0]["primitives"][0]["attributes"].__setitem__("JOINTS_1", 1), "skeleton.influences"),
            ("a missing material slot (footwear)",
             lambda g: g["materials"][c["materials"]["required"].index("footwear")].__setitem__("name", "skin__second"),
             "material.missing_slot"),
            ("a material on no contract slot (cloak)",
             lambda g: g["materials"][0].__setitem__("name", "cloak"), "material.unknown_slot"),
            ("lod0 without the face", strip_face, "morph.missing_required"),
            ("a morph outside the vocabulary",
             lambda g: g["meshes"][0]["extras"]["targetNames"].__setitem__(0, "smileBig"), "morph.unknown"),
            ("duplicate clip names", lambda g: g["animations"][1].__setitem__("name", "idle"), "clip.duplicate"),
            ("a clip not in lower snake case", lambda g: g["animations"][1].__setitem__("name", "Walk"), "clip.bad_name"),
            ("a clip with no contract verb", lambda g: g["animations"][1].__setitem__("name", "dance"), "clip.unknown_verb"),
            ("centimetres instead of metres", lambda g: scale_positions(g, 100), "frame.height"),
            ("metric positions hidden under a 0.01 armature",
             lambda g: (scale_positions(g, 100), g["nodes"][0].__setitem__("scale", [0.01, 0.01, 0.01])),
             "frame.node_scale"),
            ("soles off the ground", lambda g: (g["accessors"][0]["min"].__setitem__(1, 0.9),
                                                g["accessors"][0]["max"].__setitem__(1, 2.6)), "frame.origin"),
            ("a root bone moved off the origin",
             lambda g: g["nodes"][bone_node(g, "root")].__setitem__("translation", [2, 0, 0]), "frame.origin"),
            ("a missing socket (socket_hand_r)",
             lambda g: g["nodes"][bone_node(g, "socket_hand_r")].__setitem__("name", "grip"), "socket.missing"),
            ("no provenance block", lambda g: g["scenes"][0].pop("extras"), "provenance.missing"),
            ("no licence", lambda g: prov(g).pop("license"), "provenance.missing_field"),
            ("a check_required licence", lambda g: prov(g).__setitem__("license", "check_required"), "provenance.license"),
            ("attested with no source", lambda g: prov(g).__setitem__("grade", "attested"), "provenance.attested_unsourced"),
            ("a source that does not resolve",
             lambda g: prov(g).__setitem__("sources", ["no_such_source"]), "provenance.unknown_source"),
            ("reconstructed with no liberty", lambda g: prov(g).pop("liberty"), "provenance.liberty_missing"),
            ("a lod that disagrees with its file name", lambda g: prov(g).__setitem__("lod", 1), "provenance.lod_mismatch"),
            ("KTX2 textures the renderer cannot open",
             lambda g: g.__setitem__("extensionsUsed", ["KHR_texture_basisu"]), "delivery.refused_extension"),
            ("Draco geometry the renderer cannot open",
             lambda g: g.__setitem__("extensionsUsed", ["KHR_draco_mesh_compression"]), "delivery.refused_extension"),
        ]
        for label, fn, code in cases:
            expect(label, mutate(fn), code)
        expect("a file not named <asset_id>.lod<N>.glb", mutate(lambda g: None, name="fixture_body.glb"),
               "provenance.file_name")

    print("instances")
    people = people_of("1835") or {}
    plain = next((pid for pid, p in people.items()
                  if pid == "beaubien_mark" and not (p.get("review_required") or p.get("touches_removal"))), None) \
        or next(pid for pid, p in people.items() if not (p.get("review_required") or p.get("touches_removal")))
    flagged = next(pid for pid, p in people.items() if p.get("review_required") or p.get("touches_removal"))

    def inst(**over):
        r = {"id": f"hi_{plain}_1835", "contract_version": c["version"], "scene": "1835", "person_id": plain,
             "appearance": {"asset_id": "generic_adult_male", "variants": {"garment_upper": "frock_coat_brown"}},
             "placement": {"local_e": 0.0, "local_n": 0.0, "heading_deg": 90, "anchor": "terrain"},
             "animation": {"clip": "idle", "loop": True, "phase": 0.25},
             "behaviour": {"state": "standing"},
             "interaction": {"selectable": True, "radius_m": 3, "opens": "resident_card"},
             "lod": {"policy": "auto"}, "display": "withheld", "review_required": False,
             "provenance": {"grade": "reconstructed", "basis": "a generic adult body; nothing states this person's dress",
                            "liberty": "L1", "seed": f"{plain}:1835"}}
        for k, v in over.items():
            r[k] = v
        return r

    def ci(rec):
        return check_instance(rec, c, schema, ctx={})

    expect(f"a withheld 1835 instance bound to {plain}", ci(inst()), None)
    for label, rec, code in [
        ("display shown while L1 stands", inst(display="shown"), "instance.l1"),
        ("a person the residents layer does not hold", inst(person_id="nobody_at_all"), "instance.unknown_person"),
        (f"review dropped for {flagged}", inst(person_id=flagged, id=f"hi_{flagged}_1835"), "instance.review_dropped"),
        ("a scene with no people layer", inst(scene="1904"), "instance.no_people_layer"),
        ("a variant on no contract slot", inst(appearance={"asset_id": "x", "variants": {"cloak": "red"}}),
         "instance.unknown_slot"),
        ("a clip with no contract verb", inst(animation={"clip": "dance"}), "instance.unknown_verb"),
        ("a record missing `display`", {k: v for k, v in inst().items() if k != "display"}, "instance.schema"),
        ("walk_surface with no structure", inst(placement={"local_e": 0, "local_n": 0, "heading_deg": 0,
                                                           "anchor": "walk_surface"}), "instance.schema"),
        ("attested with no source", inst(provenance={"grade": "attested", "basis": "a portrait, but which one?"}),
         "instance.attested_unsourced"),
        ("reconstructed with no liberty", inst(provenance={"grade": "reconstructed",
                                                           "basis": "a generic adult body, nothing more"}),
         "instance.liberty_missing"),
    ]:
        expect(label, ci(rec), code)
    ctx: dict = {}
    check_instance(inst(), c, schema, ctx=ctx)
    expect("the same person standing twice in one scene",
           check_instance(inst(id=f"hi_{plain}_1835_b"), c, schema, ctx=ctx), "instance.duplicate_person")

    print(f"human_contract self-test: {'FAIL' if fails else 'OK'} ({fails} assertion(s) did not fire as required)")
    return 1 if fails else 0


# --------------------------------------------------------------------------- main

def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("--check", "--glb", "--instance", "--self-test"):
        print(__doc__)
        return 2
    if argv[0] == "--self-test":
        return self_test()
    c, schema = load_json(CONTRACT), load_json(SCHEMA)
    bad = 0
    if argv[0] == "--check":
        f = check_contract(c, schema)
        for x in f:
            print(f"FAIL contract: {x}")
        bad += len(f)
        nb = len(c["skeleton"]["bones"])
        print(f"contract v{c['version']}: skeleton {c['skeleton']['id']} ({nb} bones), "
              f"{len(c['materials']['required'])}+{len(c['materials']['optional'])} material slots, "
              f"{len(c['morphs']['required'])}+{len(c['morphs']['optional'])} morphs, "
              f"{len(c['clips']['verbs'])} clip verbs, L1 in force: {c['l1']['in_force']}")
        glbs = sorted(ASSETS.glob("*.glb")) if ASSETS.exists() else []
        insts = sorted(INSTANCES.glob("*/*.json")) if INSTANCES.exists() else []
    else:
        glbs = [Path(a) for a in argv[1:]] if argv[0] == "--glb" else []
        insts = [Path(a) for a in argv[1:]] if argv[0] == "--instance" else []
    srcs = known_sources()
    for p in glbs:
        f = check_glb(p, c, srcs)
        for x in f:
            print(f"FAIL {p.name}: {x}")
        bad += len(f)
    ctx: dict = {"sources": srcs}
    for p in insts:
        f = check_instance(load_json(p), c, schema, where=str(p), ctx=ctx)
        for x in f:
            print(f"FAIL {p.name}: {x}")
        bad += len(f)
    print(f"{len(glbs)} human GLB(s), {len(insts)} instance record(s) checked; "
          f"{'OK' if not bad else f'{bad} finding(s)'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
