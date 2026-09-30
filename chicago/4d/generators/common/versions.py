"""Structure VERSIONS: one committed alternate build of one structure (T-1727).

The owner wants several builds of the same house on dev at once (the Glessner
House first, T-1729/T-1730), opened side by side by URL, and then one of them made
the default in a single reviewable pull request:

    …/4d/dev/1835/?structure=<id>&version=<label>

A version is a whole structure record. It lives beside the canonical one and never
replaces it until it is promoted:

    data/structures/<id>.json                    the canonical record, the DEFAULT
    data/structures/versions/<id>/<label>.json   one alternate: a full record, same id
    assets/gltf/versions/<id>/<label>/<id>__<phase>.glb   its master, baked by build.py
    assets/web/versions/<id>/<label>/<id>__<phase>.glb    its web derivative
    assets/manifest.versions.json                 data -> master and master -> derivative
                                                  for every version mesh

A version carries every provenance field a structure does, because it IS a
structure record: `tools/validate.py` holds it to the same schema, the same
source-resolution and tier rules, the same evidence ladder and the same liberties
coverage. The one extra key is `version`, which a canonical record may not carry:

    "version": {"label": "v2", "summary": "what differs, for a visitor",
                "test_fixture": false}

This module is the one place the layout and the label rule are written down, so
`generators/build.py` (which bakes versions), `tools/validate.py` (which gates them),
`tools/compile_scene.py` (which compiles their sidecars), `tools/structure_versions.py`
and `tools/promote_version.mjs` cannot disagree about where a version lives.

It builds nothing. It is listed in `generators/code_inputs.py` NO_GEOMETRY for the
reason `selection.py` is: it decides WHICH records are baked and where the file
goes, and a mesh built from a record is the same mesh whichever directory it lands in.

THE LABEL RULE. A label is a short neutral string — `v1`, `v2`, `b`, `hall-plan` —
lower-case letters and digits in hyphen-separated runs, at most 24 characters. It is
NEVER a model identifier, which this repository forbids in any artifact; the owner
keeps his own mapping from label to run. The refusal cannot list the names it
refuses without writing them into the repository, so it holds them as truncated
sha256 digests and hashes every letter run of a label against them.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

LABEL_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LABEL_MAX = 24

# `default` names the canonical record in the URL (`version=default` shows it with the
# HUD saying so, which is what makes two side-by-side screenshots unambiguous), so no
# version file may take it.
RESERVED = {"default"}

# Truncated sha256 of AI vendor and model-family names, lower-case. A label any of
# whose letter runs CONTAINS one of these is refused (see the module docstring for why
# the names themselves are not written here).
_REFUSED_DIGESTS = frozenset({
    "c857d09db23e6822", "c70eca6b0f88f44d", "e12ce8285efc67c6", "c9ad8f2cc1294afa",
    "5a5110ebe1544b31", "053ea4804ef1bb33", "60965168ce762e94", "7d3194f79e645c42",
    "5d72436256ada538", "fc5a1047f5919892", "920510199770f4d6", "c97504235ab15009",
    "add92b9cde2bdbf3", "6f7ac1823da81d2e", "67f2d22514622d1b", "57de4cf40144bdf7",
    "3ea125d0bff386e6", "72e8088a05b38ae3",
})
_REFUSED_LENGTHS = (3, 4, 5, 6, 7, 8, 9)

MANIFEST_NOTE = (
    "T-1727. The build record for STRUCTURE VERSIONS, the alternates under "
    "data/structures/versions/<id>/<label>.json. One entry per version mesh, keyed by its "
    "path under assets/gltf/: `inputs_sha256` is the same recipe as assets/manifest.json "
    "(generators/mesh_inputs.py over the VERSION record), written by generators/build.py or "
    "by `tools/structure_versions.py adopt` when the version's inputs hash equals a committed "
    "canonical bake; `web_master_sha256` is the master each assets/web/ derivative was made "
    "from, written by tools/web_derivatives.sh. DERIVED: `tools/validate.py --stale` "
    "recomputes both, plus each optional web_lods master/recipe/output hash, and the remedy for a mismatch is a bake, never an edit of this file."
)


def label_problem(label: str) -> str | None:
    """Why `label` cannot name a version, or None if it can."""
    if not isinstance(label, str) or not label:
        return "a label must be a non-empty string"
    if len(label) > LABEL_MAX:
        return f"'{label}' is {len(label)} characters; a label is at most {LABEL_MAX}"
    if not LABEL_RE.match(label):
        return (f"'{label}' is not a short neutral label — lower-case letters and digits in "
                f"hyphen-separated runs, e.g. v1, v2, b, hall-plan")
    if label in RESERVED:
        return f"'{label}' is reserved: version=default names the canonical record"
    for run in re.findall(r"[a-z]+", label):
        for n in _REFUSED_LENGTHS:
            for i in range(0, len(run) - n + 1):
                if hashlib.sha256(run[i:i + n].encode()).hexdigest()[:16] in _REFUSED_DIGESTS:
                    return (f"'{label}' contains a vendor or model-family name. Labels are "
                            f"neutral strings; no model identifier may enter this repository "
                            f"(the owner keeps his own label-to-run mapping)")
    return None


def versions_dir(root: Path = ROOT) -> Path:
    return root / "data" / "structures" / "versions"


def manifest_path(root: Path = ROOT) -> Path:
    return root / "assets" / "manifest.versions.json"


def record_path(sid: str, label: str, root: Path = ROOT) -> Path:
    return versions_dir(root) / sid / f"{label}.json"


def asset_key(sid: str, label: str, phase_id: str) -> str:
    """The version mesh's path under assets/gltf/ (and assets/web/, and the published
    data/gltf/): what a sidecar's `asset` names after `gltf/`."""
    return f"versions/{sid}/{label}/{sid}__{phase_id}.glb"



# A rendering derivative of this same version, never a substitute historical build.
# The opt-in is deliberately exact: default/v2/v3 and the rest of town are unchanged.
GLESSNER_V4_KEY = "versions/glessner_house/v4/glessner_house__as_built_1887.glb"
GLESSNER_LIGHT_RECIPE = {"id": "glessner-v4-light-1", "position_bits": 16,
                       "gltf_transform": "4.5.0", "max_triangles": 200000}


def lod_asset_keys(key: str) -> dict[str, str]:
    return {"light": key[:-4] + ".light.glb"} if key == GLESSNER_V4_KEY else {}


def lod_recipe_sha(root: Path = ROOT) -> str:
    """Hash the explicit light recipe and its producer implementation, not the town."""
    recipe = dict(GLESSNER_LIGHT_RECIPE)
    recipe["producer_sha256"] = {
        name: sha256_file(root / name) for name in
        ("tools/structure_versions.py", "tools/_glessner_lod.py")}
    # The current geometry source is part of the light recipe, not merely a
    # manifest claim. build-light also refuses a stale full master before it runs.
    inputs = [root / "data/structures/versions/glessner_house/v4.json",
              root / "generators/archetypes/masonry_house.py"]
    inputs.extend(sorted((root / "generators/archetypes").glob("masonry_house_v4*.py")))
    recipe["source_sha256"] = {p.relative_to(root).as_posix(): sha256_file(p)
                                for p in inputs if p.is_file()}
    return hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest()



def light_receipt(path: Path) -> tuple[dict, int]:
    """Read the producer receipt and real primitive count without decoding meshopt."""
    with path.open("rb") as stream:
        header = stream.read(20)
        if len(header) != 20:
            raise ValueError("light output is not a GLB")
        magic, version, size, length, kind = struct.unpack("<5I", header)
        if (magic, version, kind) != (0x46546C67, 2, 0x4E4F534A) or size != path.stat().st_size:
            raise ValueError("light output has an invalid GLB header")
        doc = json.loads(stream.read(length))
    receipt = doc.get("extras", {}).get("glessner_light", {})
    triangles = 0
    for mesh in doc.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            if primitive.get("mode", 4) != 4:
                raise ValueError("light output contains a non-triangle primitive")
            accessor = primitive.get("indices", primitive.get("attributes", {}).get("POSITION"))
            count = doc["accessors"][accessor]["count"]
            if count % 3:
                raise ValueError("light output has an incomplete triangle")
            triangles += count // 3
    if not 0 < triangles <= GLESSNER_LIGHT_RECIPE["max_triangles"]:
        raise ValueError(f"light output has {triangles} triangles, outside its declared budget")
    return receipt, triangles


def lod_problems(key: str, entry: dict, root: Path = ROOT) -> list[str]:
    """The reduced file must name this master, current recipe, and its actual bytes."""
    failures = []
    for level, light_key in lod_asset_keys(key).items():
        claim = entry.get("web_lods", {}).get(level, {})
        path = root / "assets/web" / light_key
        if claim.get("asset") != light_key or not path.is_file():
            failures.append(f"{level} derivative missing or not recorded at {light_key}")
            continue
        master = root / "assets/gltf" / key
        if not master.is_file() or claim.get("master_sha256") != sha256_file(master):
            failures.append(f"{level} derivative is stale against its version master")
        try:
            current_recipe = lod_recipe_sha(root)
        except OSError as error:
            failures.append(f"{level} derivative cannot read its rendering recipe: {error}")
        else:
            if claim.get("recipe_sha256") != current_recipe:
                failures.append(f"{level} derivative is stale against its rendering recipe")
        if claim.get("output_sha256") != sha256_file(path):
            failures.append(f"{level} derivative bytes differ from the producer record")
    return failures


def every_file(root: Path = ROOT) -> list[Path]:
    """Every file under data/structures/versions/, so a gate can refuse strays."""
    d = versions_dir(root)
    return sorted(p for p in d.rglob("*") if p.is_file()) if d.is_dir() else []


def parse_path(path: Path, root: Path = ROOT) -> tuple[str, str] | None:
    """(structure id, label) for `versions/<id>/<label>.json`, or None for any other shape."""
    try:
        rel = path.relative_to(versions_dir(root))
    except ValueError:
        return None
    if len(rel.parts) != 2 or rel.suffix != ".json":
        return None
    return rel.parts[0], rel.stem


def load_versions(root: Path = ROOT) -> list[dict]:
    """Every well-placed version record: [{id, label, path, record}], sorted.

    A file in the wrong shape is skipped here and refused by tools/validate.py, which
    walks `every_file()` itself; an unparseable one raises, as a record would.
    """
    out = []
    for p in every_file(root):
        got = parse_path(p, root)
        if got is None:
            continue
        out.append({"id": got[0], "label": got[1], "path": p,
                    "record": json.loads(p.read_text(encoding="utf-8"))})
    return out


def read_manifest(root: Path = ROOT) -> dict:
    p = manifest_path(root)
    doc = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    doc.setdefault("assets", {})
    return doc


def write_manifest(doc: dict, root: Path = ROOT) -> None:
    out = {"$note": MANIFEST_NOTE}
    out.update({k: v for k, v in doc.items() if k != "$note"})
    out["assets"] = dict(sorted(out.get("assets", {}).items()))
    manifest_path(root).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8")


def write_record(path: Path, record: dict) -> None:
    """Records are written the way data/structures/ writes them: indent 2, UTF-8, LF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()
