#!/usr/bin/env python3
"""Structure versions from the command line (T-1727). No Blender.

    python3 tools/structure_versions.py list
    python3 tools/structure_versions.py check-label <label>
    python3 tools/structure_versions.py seed <id> <label> --summary "…" [--test-fixture]
    python3 tools/structure_versions.py adopt <id> <label>
    python3 tools/structure_versions.py build-light <key> <out.glb>  # reduced same-version mesh
    python3 tools/structure_versions.py record-web <key>        # tools/web_derivatives.sh
    python3 tools/structure_versions.py status <id>             # what needs a bake
    python3 tools/structure_versions.py promote <id> <label> [--keep-as L] [--dry-run]
                                         # the file moves; run it via tools/promote_version.mjs

A version is one committed alternate of one structure — a whole record at
`data/structures/versions/<id>/<label>.json` with its own mesh — opened by URL with
`?structure=<id>&version=<label>`. The layout and the label rule are in
`generators/common/versions.py`; `docs/STRUCTURE-VERSIONS.md` is the how-to.

`seed` starts a version as a copy of the canonical record, with the `version` block
added, and then runs `adopt`. Edit the copy afterwards into the alternate it is for.

`adopt` gives a version the mesh it needs WITHOUT Blender, in the one case where that is
honest: when the version's inputs hash (generators/mesh_inputs.py — the same recipe the
staleness gate uses) EQUALS the committed canonical bake's. Freshness in this project is
defined on inputs, so two records whose builder inputs hash the same are the same mesh by
the project's own definition, and the canonical master and derivative are copied into the
version's paths with a manifest entry saying so (`adopted_from`). When the hashes differ,
nothing is copied and it prints the bake that is needed instead — a version whose geometry
differs gets its geometry from `generators/build.py`, never from a copy.

`record-web` is what `tools/web_derivatives.sh` calls after writing a version derivative,
so the master -> derivative link is recorded in the same run as the bytes (ROADMAP K39's
rule, applied to versions).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

from common import versions as V  # noqa: E402
from common.phases import drawn_by_another_layer  # noqa: E402


def scene_targets() -> list[tuple[str, dt.date]]:
    out = []
    for p in sorted((ROOT / "data" / "scenes").glob("*.json")):
        sc = json.loads(p.read_text())
        try:
            out.append((p.stem, dt.date.fromisoformat(sc["target_date"])))
        except (KeyError, ValueError):
            continue
    return out


def resolve_phase(structure: dict, target: dt.date):
    """The scene rule shared by build.py, compile_scene.py and validate.py."""
    from compile_scene import resolve_phase as rp  # noqa: PLC0415
    return rp(structure, target)


def baked_phases(record: dict) -> list[dict]:
    """The phases of `record` some scene resolves AND a mesh is baked for."""
    seen, out = set(), []
    for _scene, target in scene_targets():
        ph = resolve_phase(record, target)
        if ph is None or drawn_by_another_layer(ph) or ph.get("id") in seen:
            continue
        seen.add(ph.get("id"))
        out.append(ph)
    return out


def cmd_list(_args) -> int:
    rows = V.load_versions()
    if not rows:
        print("no structure versions committed (data/structures/versions/ is empty)")
        return 0
    for v in rows:
        blk = v["record"].get("version") or {}
        tag = " [test fixture]" if blk.get("test_fixture") else ""
        print(f"{v['id']}  {v['label']}{tag}  — {blk.get('summary', '')}")
    return 0


def cmd_check_label(args) -> int:
    why = V.label_problem(args.label)
    if why:
        print(f"REFUSED: {why}")
        return 2
    print(f"ok: '{args.label}' can name a version")
    return 0


def adopt(sid: str, label: str, *, quiet: bool = False) -> int:
    """Copy the canonical bake into the version's paths where the inputs are identical."""
    import mesh_inputs  # noqa: PLC0415

    path = V.record_path(sid, label)
    if not path.exists():
        print(f"no version record at {path.relative_to(ROOT)}")
        return 2
    record = json.loads(path.read_text())
    canon = json.loads((ROOT / "data" / "structures" / f"{sid}.json").read_text())
    manifest = json.loads((ROOT / "assets" / "manifest.json").read_text()).get("assets", {})
    web = json.loads((ROOT / "assets" / "manifest.web.json").read_text()).get("masters", {})
    vman = V.read_manifest()
    vman["inputs_scheme"] = mesh_inputs.SCHEME

    needs_bake = []
    adopted = 0
    for ph in baked_phases(record):
        key = V.asset_key(sid, label, ph["id"])
        mine = mesh_inputs.structure_inputs_sha(record, ph, record.get("archetype"))
        canon_ph = next((p for p in canon.get("phases", []) if p.get("id") == ph["id"]), None)
        name = f"{sid}__{ph['id']}.glb"
        entry = manifest.get(name)
        theirs = (mesh_inputs.structure_inputs_sha(canon, canon_ph, canon.get("archetype"))
                  if canon_ph else None)
        if not (entry and theirs == mine == entry.get("inputs_sha256")):
            needs_bake.append(key)
            continue
        src_master = ROOT / "assets" / "gltf" / name
        src_web = ROOT / "assets" / "web" / name
        if web.get(name) != V.sha256_file(src_master):
            needs_bake.append(key)
            continue
        dst_master = ROOT / "assets" / "gltf" / key
        dst_web = ROOT / "assets" / "web" / key
        dst_master.parent.mkdir(parents=True, exist_ok=True)
        dst_web.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_master, dst_master)
        shutil.copyfile(src_web, dst_web)
        vman["assets"][key] = {
            "kind": "generated",
            "structure_id": sid,
            "version_label": label,
            "phase_id": ph["id"],
            "archetype": record.get("archetype"),
            "inputs_sha256": mine,
            "bytes": dst_master.stat().st_size,
            "baked_ao": bool(entry.get("baked_ao")),
            "adopted_from": name,
            "web_master_sha256": V.sha256_file(dst_master),
        }
        adopted += 1
        if not quiet:
            print(f"adopted {name} -> assets/gltf/{key} (inputs hash {mine[:12]} identical)")
    V.write_manifest(vman)
    if needs_bake:
        print(f"{len(needs_bake)} version mesh(es) differ from every committed bake and need "
              f"Blender: tools/bake.sh --only {sid}   (bakes {sid} and its versions; or "
              f"dispatch the chicago-4d-bake workflow with only={sid})")
        for k in needs_bake:
            print(f"   needs a bake: assets/gltf/{k}")
        return 3
    if not quiet:
        print(f"{adopted} mesh(es) adopted; run python3 tools/compile_scene.py --all next")
    return 0


def cmd_seed(args) -> int:
    why = V.label_problem(args.label)
    if why:
        print(f"REFUSED: {why}")
        return 2
    canon_path = ROOT / "data" / "structures" / f"{args.id}.json"
    if not canon_path.exists():
        print(f"REFUSED: no canonical record data/structures/{args.id}.json")
        return 2
    path = V.record_path(args.id, args.label)
    if path.exists():
        print(f"REFUSED: {path.relative_to(ROOT)} already exists")
        return 2
    record = json.loads(canon_path.read_text())
    block = {"label": args.label, "summary": args.summary}
    if args.test_fixture:
        block["test_fixture"] = True
    record["version"] = block
    V.write_record(path, record)
    print(f"wrote {path.relative_to(ROOT)} — a copy of the canonical record; edit it into "
          f"the alternate it is for")
    return adopt(args.id, args.label)


def cmd_adopt(args) -> int:
    return adopt(args.id, args.label)



def cmd_build_light(args) -> int:
    """Build reduced geometry from the current v4 record, without touching its master."""
    if args.key != V.GLESSNER_V4_KEY:
        print("   build-light: this recipe is only for Glessner v4")
        return 2
    master = ROOT / "assets/gltf" / args.key
    entry = V.read_manifest()["assets"].get(args.key, {})
    record = json.loads(V.record_path("glessner_house", "v4", ROOT).read_text())
    phase = next(p for p in record["phases"] if p["id"] == "as_built_1887")
    import mesh_inputs  # noqa: PLC0415
    if not master.is_file() or entry.get("inputs_sha256") != mesh_inputs.structure_inputs_sha(
            record, phase, record.get("archetype")):
        print("   build-light: the full version master is missing/stale; bake it first")
        return 2
    from _glessner_lod import build_light  # noqa: PLC0415
    result = build_light(master, Path(args.output), root=ROOT,
                         recipe_sha256=V.lod_recipe_sha(ROOT))
    print("   built same-version light geometry: " + json.dumps(result, sort_keys=True))
    return 0


def cmd_record_web(args) -> int:
    vman = V.read_manifest()
    entry = vman["assets"].get(args.key)
    master = ROOT / "assets" / "gltf" / args.key
    if entry is None or not master.exists():
        print(f"   record-web: {args.key} has no manifest entry or no master — bake it first")
        return 2
    # Record only a complete production: a failed/missing light output cannot stamp
    # either derivative fresh. The producer writes both before invoking this command.
    lods = {}
    for level, key in V.lod_asset_keys(args.key).items():
        output = ROOT / "assets/web" / key
        if not output.is_file():
            print(f"   record-web: missing {level} derivative {key}")
            return 2
        try:
            receipt, triangles = V.light_receipt(output)
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f"   record-web: invalid {level} derivative: {error}")
            return 2
        master_sha, recipe_sha = V.sha256_file(master), V.lod_recipe_sha(ROOT)
        if receipt.get("master_sha256") != master_sha or receipt.get("recipe_sha256") != recipe_sha:
            print(f"   record-web: {level} receipt does not match the current master/recipe")
            return 2
        lods[level] = {"asset": key, "master_sha256": master_sha,
                       "recipe_sha256": recipe_sha, "triangles": triangles,
                       "output_sha256": V.sha256_file(output)}
    entry["web_master_sha256"] = V.sha256_file(master)
    if lods:
        entry["web_lods"] = lods
    V.write_manifest(vman)
    return 0


def _move(src: Path, dst: Path, dry: bool, log: list[str], root: Path) -> None:
    log.append(f"move {src.relative_to(root)} -> {dst.relative_to(root)}")
    if dry:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.replace(dst)


def _prune_empty(d: Path, stop: Path) -> None:
    """Remove now-empty directories from `d` up to (not including) `stop`."""
    while d != stop and d.is_dir() and not any(d.iterdir()):
        d.rmdir()
        d = d.parent


def promote(root: Path, sid: str, label: str, keep: str, *, dry: bool = False,
            today: str | None = None) -> list[str]:
    """Make version `label` of `sid` the default and keep the old default as version `keep`.

    Records AND meshes AND the three build records move together, so the promotion is
    one reviewable diff and nothing needs a bake: a record's inputs hash does not depend
    on which directory it sits in (mesh_inputs hashes the resolved parameters, the
    structure id and the code — the `version` block is not a builder input), so a mesh
    that was fresh as a version is fresh as the default and vice versa. Anything that was
    NOT fresh stays not fresh and `status` / `validate.py --stale` say so.

    Written in Python rather than in the .mjs that fronts it because the records must be
    re-serialised byte-compatibly with data/structures/ — a JavaScript round trip writes
    `90.0` as `90`, which is a different float in the builder's hash and would stale the
    very mesh the promotion is carrying.
    """
    for lab in (label, keep):
        why = V.label_problem(lab)
        if why:
            raise SystemExit(f"REFUSED: {why}")
    if label == keep:
        raise SystemExit("REFUSED: --keep-as must differ from the label being promoted")
    canon_path = root / "data" / "structures" / f"{sid}.json"
    ver_path = V.record_path(sid, label, root)
    keep_path = V.record_path(sid, keep, root)
    if not canon_path.exists():
        raise SystemExit(f"REFUSED: no canonical record {canon_path.relative_to(root)}")
    if not ver_path.exists():
        raise SystemExit(f"REFUSED: no version record {ver_path.relative_to(root)} — "
                         f"`python3 tools/structure_versions.py list` shows what exists")
    if keep_path.exists():
        raise SystemExit(f"REFUSED: {keep_path.relative_to(root)} already exists; pass "
                         f"--keep-as <another label>")

    today = today or dt.date.today().isoformat()
    canon = json.loads(canon_path.read_text(encoding="utf-8"))
    version = json.loads(ver_path.read_text(encoding="utf-8"))
    if version.get("id") != sid or canon.get("id") != sid:
        raise SystemExit("REFUSED: the version and the canonical record must both carry "
                         f"id '{sid}'")
    if V.asset_key(sid, label, "as_built_1887") == V.GLESSNER_V4_KEY:
        raise SystemExit("REFUSED: Glessner v4 has a three-file recovery package and a light "
                         "derivative. Retarget/retire that package and LOD contract explicitly "
                         "before promoting it; no generated asset may be silently orphaned.")
    log: list[str] = []

    # ---- the meshes and their books --------------------------------------------------
    gltf, web = root / "assets" / "gltf", root / "assets" / "web"
    man_p = root / "assets" / "manifest.json"
    web_p = root / "assets" / "manifest.web.json"
    manifest = json.loads(man_p.read_text()) if man_p.exists() else {"assets": {}}
    webdoc = json.loads(web_p.read_text()) if web_p.exists() else {"masters": {}}
    vman = V.read_manifest(root)
    m_assets, masters, v_assets = manifest.setdefault("assets", {}), \
        webdoc.setdefault("masters", {}), vman["assets"]

    # 1. the old default's meshes step aside into versions/<id>/<keep>/
    for name in sorted(n for n, e in m_assets.items() if e.get("structure_id") == sid):
        entry = dict(m_assets.pop(name))
        key = f"versions/{sid}/{keep}/{name}"
        if (gltf / name).exists():
            _move(gltf / name, gltf / key, dry, log, root)
        if (web / name).exists():
            _move(web / name, web / key, dry, log, root)
        entry["version_label"] = keep
        if name in masters:
            entry["web_master_sha256"] = masters.pop(name)
        v_assets[key] = entry
    # 2. the promoted version's meshes take the default's names
    prefix = f"versions/{sid}/{label}/"
    for key in sorted(k for k in list(v_assets) if k.startswith(prefix)):
        entry = dict(v_assets.pop(key))
        name = key[len(prefix):]
        if (gltf / key).exists():
            _move(gltf / key, gltf / name, dry, log, root)
        if (web / key).exists():
            _move(web / key, web / name, dry, log, root)
        web_sha = entry.pop("web_master_sha256", None)
        for k in ("version_label", "adopted_from"):
            entry.pop(k, None)
        m_assets[name] = entry
        if web_sha:
            masters[name] = web_sha
    for base in (gltf, web):
        _prune_empty(base / "versions" / sid / label, base)

    # ---- the records ------------------------------------------------------------------
    kept = dict(canon)
    kept["version"] = {
        "label": keep,
        "summary": (f"The default build of {canon.get('name', sid)} until version "
                    f"“{label}” was promoted on {today}. Kept so the two can still be "
                    f"compared side by side."),
    }
    promoted = {k: v for k, v in version.items() if k != "version"}
    log.append(f"write {keep_path.relative_to(root)} (the old default, kept as '{keep}')")
    log.append(f"write {canon_path.relative_to(root)} (version '{label}', now the default)")
    log.append(f"delete {ver_path.relative_to(root)}")
    if not dry:
        V.write_record(keep_path, kept)
        V.write_record(canon_path, promoted)
        ver_path.unlink()
        man_p.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        webdoc["masters"] = dict(sorted(masters.items()))
        web_p.write_text(json.dumps(webdoc, indent=2) + "\n", encoding="utf-8")
        V.write_manifest(vman, root)
    log.append("update assets/manifest.json, assets/manifest.web.json, "
               "assets/manifest.versions.json")
    return log


def status(sid: str) -> list[str]:
    """Which meshes of `sid` and its versions are missing or stale — what a bake must fix."""
    import mesh_inputs  # noqa: PLC0415

    out = []
    canon = json.loads((ROOT / "data" / "structures" / f"{sid}.json").read_text())
    manifest = json.loads((ROOT / "assets" / "manifest.json").read_text()).get("assets", {})
    for ph in baked_phases(canon):
        name = f"{sid}__{ph['id']}.glb"
        e = manifest.get(name)
        if not e or not (ROOT / "assets" / "gltf" / name).exists():
            out.append(f"assets/gltf/{name} (missing)")
        elif e.get("inputs_sha256") != mesh_inputs.structure_inputs_sha(canon, ph, canon.get(
                "archetype")):
            out.append(f"assets/gltf/{name} (stale)")
    vman = V.read_manifest()["assets"]
    for v in V.load_versions():
        if v["id"] != sid:
            continue
        rec = v["record"]
        for ph in baked_phases(rec):
            key = V.asset_key(sid, v["label"], ph["id"])
            e = vman.get(key)
            if not e or not (ROOT / "assets" / "gltf" / key).exists():
                out.append(f"assets/gltf/{key} (missing)")
            elif e.get("inputs_sha256") != mesh_inputs.structure_inputs_sha(rec, ph, rec.get(
                    "archetype")):
                out.append(f"assets/gltf/{key} (stale)")
            else:
                out.extend(f"{key}: {problem}" for problem in V.lod_problems(key, e, ROOT))
    return out


def cmd_promote(args) -> int:
    root = Path(args.root).resolve() if args.root else ROOT
    keep = args.keep_as or f"pre-{args.label}"
    log = promote(root, args.id, args.label, keep, dry=args.dry_run, today=args.today)
    for line in log:
        print(("would " if args.dry_run else "") + line)
    return 0


def cmd_status(args) -> int:
    todo = status(args.id)
    for line in todo:
        print(f"needs a bake: {line}")
    if not todo:
        print(f"ok: every mesh of {args.id} and its versions is present and fresh")
    return 3 if todo else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("check-label")
    p.add_argument("label")
    p.set_defaults(fn=cmd_check_label)
    p = sub.add_parser("seed")
    p.add_argument("id")
    p.add_argument("label")
    p.add_argument("--summary", required=True,
                   help="what differs, in a sentence a visitor reads on the card")
    p.add_argument("--test-fixture", action="store_true",
                   help="a test-only alternate (the smoke's fixture), labelled so on the card")
    p.set_defaults(fn=cmd_seed)
    p = sub.add_parser("adopt")
    p.add_argument("id")
    p.add_argument("label")
    p.set_defaults(fn=cmd_adopt)
    p = sub.add_parser("build-light", help="reduced same-version geometry; no Blender")
    p.add_argument("key")
    p.add_argument("output")
    p.set_defaults(fn=cmd_build_light)
    p = sub.add_parser("record-web")
    p.add_argument("key")
    p.set_defaults(fn=cmd_record_web)
    p = sub.add_parser("promote", help="the file moves behind tools/promote_version.mjs")
    p.add_argument("id")
    p.add_argument("label")
    p.add_argument("--keep-as", help="label for the old default (default: pre-<label>)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--root", help=argparse.SUPPRESS)
    p.add_argument("--today", help=argparse.SUPPRESS)
    p.set_defaults(fn=cmd_promote)
    p = sub.add_parser("status", help="which meshes of <id> and its versions need a bake")
    p.add_argument("id")
    p.set_defaults(fn=cmd_status)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
