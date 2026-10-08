#!/usr/bin/env python3
"""Pack, verify and reproduce a versioned, engine-neutral scene bundle (T-2067).

The bundle is what the scheduled content build hands to a consumer that is not
the web page — the Unreal adapter first (T-1358), anything else later. The
contract is docs/unreal/SCENE-BUNDLE.md; this is its one implementation.

    python3 tools/scene_bundle.py pack   --scene 1835 [--commit SHA] [--out DIR]
    python3 tools/scene_bundle.py verify ARCHIVE [--expect-digest HEX]
    python3 tools/scene_bundle.py repro  --scene 1835 [--commit SHA]
    python3 tools/scene_bundle.py advance --index OLD --receipt R --tag T ... --out NEW
    python3 tools/scene_bundle.py --self-test

ONE COMMIT, NEVER THE WORKING TREE. `pack` reads every byte it ships out of the
git objects of a single commit (`git cat-file --batch`), so a bundle cannot carry
sidecars from one commit and meshes from another, and an uncommitted edit in the
checkout cannot leak into it. Which commit is a VALIDATED one is the caller's
question — the content build packs the commit its own gate just passed (T-2068).

NO WALL CLOCK IN THE ARCHIVE. Every member's mtime is the commit's own time and
the gzip header carries none, so the same commit packs to the same bytes on the
same toolchain. The payload digest — sha256 over the sorted `sha256  path` lines
— is the cross-machine identity: it does not move if a different zlib compresses
the same payload differently. `--receipt` writes the build instant OUTSIDE the
archive, where a timestamp belongs.

The payload keeps the source layout under `payload/` (data/…, assets/…), so a
consumer that reads a checkout today — renderers/unreal/Scripts/import_scene.py —
reads an extracted bundle by pointing CHICAGO_SOURCE at that directory.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "chicago4d-scene-bundle/1"
CONTRACT = ROOT / "docs" / "GLB-CONTRACT.md"
TABLE_OPEN = "<!-- T-0252 layer export table"
TABLE_CLOSE = "<!-- end T-0252 layer export table -->"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Refused(Exception):
    """A bundle that must not be made or must not be trusted. The message says why."""


# ---------------------------------------------------------------- git objects

class Snapshot:
    """Read-only view of ONE commit's tree under the project prefix (chicago/4d/)."""

    def __init__(self, commit: str = "HEAD", root: Path = ROOT):
        def git(*args: str) -> str:
            return subprocess.run(["git", "-C", str(root), *args], check=True,
                                  capture_output=True, text=True).stdout.strip()
        try:
            self.commit = git("rev-parse", "--verify", f"{commit}^{{commit}}")
        except subprocess.CalledProcessError as exc:
            raise Refused(f"{commit!r} is not a commit in {root}: {exc.stderr.strip()}")
        self.root = root
        self.prefix = git("rev-parse", "--show-prefix")
        self.commit_time = int(git("show", "-s", "--format=%ct", self.commit))
        listing = subprocess.run(
            ["git", "-C", str(root), "ls-tree", "-r", "-z", "--full-tree", self.commit,
             "--", self.prefix.rstrip("/") or "."],
            check=True, capture_output=True).stdout.decode()
        self.blobs: dict[str, str] = {}
        for row in filter(None, listing.split("\0")):
            meta, path = row.split("\t", 1)
            mode, kind, oid = meta.split()
            if kind == "blob" and mode != "120000":
                self.blobs[path[len(self.prefix):]] = oid
        self._proc = None

    def has(self, rel: str) -> bool:
        return rel in self.blobs

    def under(self, rel_dir: str) -> list[str]:
        head = rel_dir.rstrip("/") + "/"
        return sorted(p for p in self.blobs if p.startswith(head))

    def read(self, rel: str) -> bytes:
        if rel not in self.blobs:
            raise Refused(f"{rel} is not in commit {self.commit[:12]}")
        if self._proc is None:
            self._proc = subprocess.Popen(["git", "-C", str(self.root), "cat-file", "--batch"],
                                          stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self._proc.stdin.write(self.blobs[rel].encode() + b"\n")
        self._proc.stdin.flush()
        header = self._proc.stdout.readline().split()
        size = int(header[2])
        data = self._proc.stdout.read(size)
        self._proc.stdout.read(1)
        return data

    def json(self, rel: str):
        return json.loads(self.read(rel))

    def close(self) -> None:
        if self._proc is not None:
            self._proc.stdin.close()
            self._proc.wait()
            self._proc = None


# ---------------------------------------------------------------- what is carried

def omitted_layers(contract_text: str) -> list[dict]:
    """Every load-drawn layer GLB-CONTRACT § Layers drawn at load names, as OMITTED.

    Read from the table itself, so a layer added there is declared absent here
    without anyone remembering to; a layer that gains an export (T-1360 and its
    successors) moves out of this list when the bundle starts carrying it.
    """
    try:
        body = contract_text.split(TABLE_OPEN, 1)[1].split(TABLE_CLOSE, 1)[0]
    except IndexError:
        raise Refused("docs/GLB-CONTRACT.md has lost its T-0252 layer table — "
                      "the bundle cannot say what it omits")
    out = []
    for line in body.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not cells[0].startswith("`data/"):
            continue
        layer, _, module = cells[0].partition("·")
        cards = "cards only" in cells[1] or "not drawn" in cells[1]
        out.append({
            "layer": layer.strip().strip("`"),
            "module": module.strip(),
            "draws": cells[1].replace("**", ""),
            "why": ("cards, not geometry: JSON in the repository, not yet carried here"
                    if cards else
                    "drawn at load by the web renderer; its GLB export is T-1360's and "
                    "its successors' (GLB-CONTRACT § Layers drawn at load)"),
        })
    if not out:
        raise Refused("docs/GLB-CONTRACT.md's layer table has no rows")
    return out


def licence_basis(rel: str, build_record: dict, licences_text: str) -> str:
    """Why this file may be redistributed, or Refused. Mirrors validate.run_license_check."""
    if rel.startswith("assets/gltf/"):
        name = rel.rsplit("/", 1)[1]
        entry = build_record.get(name)
        if entry and entry.get("kind", "generated") == "generated":
            return "generated by a recorded bake (assets/manifest.json); project licence"
        if rel[len("assets/"):] in licences_text:
            return "assets/LICENSES.md row"
        raise Refused(f"{rel}: no recorded bake produced it and assets/LICENSES.md has no "
                      f"row for it — its rights are unknown, so it does not ship")
    if rel.startswith("assets/"):
        return "build record or licence inventory; project licence"
    if rel.startswith("data/") or rel.startswith("generators/"):
        return "project data; project licence"
    raise Refused(f"{rel}: outside what a scene bundle carries")


def rights_refusals(sources: dict[str, dict]) -> list[str]:
    """The release refusal validate.py already holds: nothing from a source still in check."""
    return [f"source {sid}: rights_status is '{s.get('rights_status')}' but asset_use is "
            f"'geometry' — resolve the rights check before shipping geometry from it"
            for sid, s in sorted(sources.items())
            if s.get("rights_status") in ("check_required", "restricted")
            and s.get("asset_use") == "geometry"]


def plan(snap: Snapshot, scene_id: str, only: list[str] | None = None) -> tuple[list[str], dict]:
    """The file list and the manifest body (everything but the per-file hashes)."""
    scene_rel = f"data/scenes/{scene_id}.json"
    if not snap.has(scene_rel):
        raise Refused(f"no scene {scene_id!r} at {snap.commit[:12]} ({scene_rel})")
    scene = snap.json(scene_rel)
    epoch = scene["terrain_epoch"]
    epoch_dir = f"data/terrain/epochs/{epoch}"
    hf = snap.json(f"{epoch_dir}/heightfield.json")
    index_rel = f"data/sidecars/{scene_id}/index.json"
    index = snap.json(index_rel)

    files = {scene_rel, "data/datum.json", "data/terrain/epochs.json", index_rel,
             f"{epoch_dir}/heightfield.json", f"{epoch_dir}/{hf['bin']}",
             "assets/manifest.json", "assets/LICENSES.md", "generators/blender.pin"}
    terrain = {}
    for layer, asset in sorted(hf.get("glb", {}).items()):
        files.add(f"assets/{asset}")
        terrain[layer] = f"assets/{asset}"
    files.update(snap.under(f"data/sidecars/{scene_id}/sources"))

    rows = index["structures"]
    if only:
        unknown = sorted(set(only) - {r["id"] for r in rows})
        if unknown:
            raise Refused(f"--only names structures not in {index_rel}: {', '.join(unknown)}")
        rows = [r for r in rows if r["id"] in only]
    carried, without, review = [], [], []
    for row in rows:
        side_rel = f"data/{row['sidecar']}"
        files.add(side_rel)
        side = snap.json(side_rel)
        if side.get("review_required"):
            review.append({"id": row["id"], "touches_removal": bool(side.get("touches_removal"))})
        if row.get("asset"):
            files.add(f"assets/{row['asset']}")
            carried.append(row["id"])
        else:
            without.append({"id": row["id"], "drawn_by": side.get("drawn_by")})

    missing = sorted(f for f in files if not snap.has(f))
    if missing:
        raise Refused(f"commit {snap.commit[:12]} lacks files the scene names: "
                      + ", ".join(missing[:8]) + (" …" if len(missing) > 8 else ""))

    sources = {p.rsplit("/", 1)[1][:-5]: snap.json(p) for p in snap.blobs
               if re.fullmatch(r"data/sources/[^/]+\.json", p)}
    refusals = rights_refusals(sources)
    if refusals:
        raise Refused("; ".join(refusals))

    build_record = snap.json("assets/manifest.json").get("assets", {})
    licences = snap.read("assets/LICENSES.md").decode()
    basis = {f: licence_basis(f, build_record, licences) for f in sorted(files)}
    pin = dict(line.split("=", 1) for line in snap.read("generators/blender.pin").decode().splitlines()
               if "=" in line and not line.lstrip().startswith("#"))

    body = {
        "schema": SCHEMA,
        "scene": {"id": scene["id"], "title": scene.get("title"),
                  "target_date": scene.get("target_date"), "terrain_epoch": epoch},
        "source": {"repository": "kevinrhaas/chicago", "commit": snap.commit,
                   "commit_time": snap.commit_time, "prefix": snap.prefix,
                   "read_from": "git objects of this one commit, never a working tree"},
        "build": {"blender": {"version": pin.get("BLENDER_VERSION"),
                              "sha256": pin.get("BLENDER_SHA256")},
                  "packer": "tools/scene_bundle.py",
                  "packer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "coverage": {
            "partial": bool(only),
            "carried": {
                "structures": len(carried),
                "terrain": terrain,
                "heightfield": f"payload/{epoch_dir}/heightfield.json",
                "sidecars": f"payload/{index_rel}",
                "source_records": len(snap.under(f"data/sidecars/{scene_id}/sources")),
                "textures": "embedded in each GLB; no external image is referenced",
            },
            "structures_without_glb": without,
            "omitted_layers": omitted_layers(CONTRACT.read_text()),
            "omitted_other": [
                f"data/sidecars/{scene_id}/versions/ and assets/gltf/versions/ (structure versions)",
                f"data/sidecars/{scene_id}/jaunts/ (web walkthrough routes)",
                "assets/web/ (web derivatives; the bundle carries the master GLBs)",
                "assets/textures/ (bake inputs, already embedded where used)",
            ],
        },
        "review_required": review,
        "release_note": ("review_required travels with every record that carries it; a scene "
                         "holding one is not `released` (AGENTS.md). No human figure is in "
                         "this bundle, for anyone (L1)."),
        "licence": {"project": "LICENSE at the repository root (GPL-3.0)",
                    "inventory": "payload/assets/LICENSES.md"},
    }
    return sorted(files), {"basis": basis, **body}


# ---------------------------------------------------------------- the archive

def digest_lines(entries: list[dict]) -> str:
    return "".join(f"{e['sha256']}  {e['path']}\n" for e in sorted(entries, key=lambda e: e["path"]))


def payload_digest(entries: list[dict]) -> str:
    return hashlib.sha256(digest_lines(entries).encode()).hexdigest()


def _member(name: str, data: bytes, mtime: int) -> tuple[tarfile.TarInfo, io.BytesIO]:
    info = tarfile.TarInfo(name)
    info.size, info.mtime, info.mode = len(data), mtime, 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info, io.BytesIO(data)


def write_archive(path: Path, members: list[tuple[str, bytes]], mtime: int, gz: bool = True) -> None:
    raw = open(path, "wb")
    try:
        stream = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) if gz else raw
        with tarfile.open(fileobj=stream, mode="w", format=tarfile.GNU_FORMAT) as tar:
            for name, data in sorted(members):
                tar.addfile(*_member(name, data, mtime))
        if gz:
            stream.close()
    finally:
        raw.close()


def pack(scene_id: str, commit: str = "HEAD", out: Path = Path("."), only: list[str] | None = None,
         gz: bool = True) -> dict:
    snap = Snapshot(commit)
    try:
        files, body = plan(snap, scene_id, only)
        basis = body.pop("basis")
        entries, members = [], []
        root = f"chicago4d-scene-{scene_id}-{snap.commit[:12]}"
        for rel in files:
            data = snap.read(rel)
            entries.append({"path": f"payload/{rel}", "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest(), "licence": basis[rel]})
            members.append((f"{root}/payload/{rel}", data))
    finally:
        snap.close()
    digest = payload_digest(entries)
    manifest = {**body, "payload_digest": digest, "files": entries}
    members.append((f"{root}/BUNDLE.json", (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()))
    members.append((f"{root}/SHA256SUMS", digest_lines(entries).encode()))
    out.mkdir(parents=True, exist_ok=True)
    name = f"{root}-{digest[:12]}.tar" + (".gz" if gz else "")
    target = out / name
    write_archive(target, members, snap.commit_time, gz)
    return {"archive": str(target), "archive_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "archive_bytes": target.stat().st_size, "payload_digest": digest,
            "source_commit": snap.commit, "scene": scene_id, "files": len(entries),
            "payload_bytes": sum(e["bytes"] for e in entries),
            "structures": body["coverage"]["carried"]["structures"],
            "partial": body["coverage"]["partial"]}


# ---------------------------------------------------------------- the consumer

def read_archive(path: Path) -> tuple[str, dict[str, bytes]]:
    """Every regular member, refusing anything a careless extractor could be hurt by."""
    try:
        tar = tarfile.open(path, mode="r:*")
    except (tarfile.TarError, OSError) as exc:
        raise Refused(f"{path.name} is not a readable archive: {exc}")
    roots, out = set(), {}
    with tar:
        for m in tar.getmembers():
            parts = m.name.split("/")
            if m.name.startswith("/") or ".." in parts or "" in parts[:-1]:
                raise Refused(f"unsafe member path {m.name!r}")
            if not (m.isfile() or m.isdir()):
                raise Refused(f"member {m.name!r} is a link or device; a bundle holds files only")
            roots.add(parts[0])
            if m.isfile():
                if m.name in out:
                    raise Refused(f"member {m.name!r} appears twice")
                out[m.name] = tar.extractfile(m).read()
    if len(roots) != 1:
        raise Refused(f"expected one top-level directory, found {sorted(roots)}")
    return roots.pop(), out


def verify(path: Path, expect_digest: str | None = None) -> dict:
    root, members = read_archive(path)
    raw = members.pop(f"{root}/BUNDLE.json", None)
    if raw is None:
        raise Refused("no BUNDLE.json at the archive root")
    try:
        manifest = json.loads(raw)
    except ValueError as exc:
        raise Refused(f"BUNDLE.json is not JSON: {exc}")
    if manifest.get("schema") != SCHEMA:
        raise Refused(f"schema {manifest.get('schema')!r}, this consumer reads {SCHEMA!r}")
    for key in ("scene", "source", "coverage", "files", "payload_digest", "review_required"):
        if key not in manifest:
            raise Refused(f"BUNDLE.json lacks {key!r}")
    commit = manifest["source"].get("commit", "")
    if not HEX40.match(commit):
        raise Refused(f"source commit {commit!r} is not a full sha")
    if root != f"chicago4d-scene-{manifest['scene']['id']}-{commit[:12]}":
        raise Refused(f"archive root {root!r} does not name the scene and commit BUNDLE.json does")

    sums = members.pop(f"{root}/SHA256SUMS", None)
    listed = {f"{root}/{e['path']}": e for e in manifest["files"]}
    present = set(members)
    missing = sorted(set(listed) - present)
    extra = sorted(present - set(listed))
    if missing:
        raise Refused(f"{len(missing)} listed file(s) missing, first {missing[0].split('/', 1)[1]}")
    if extra:
        raise Refused(f"{len(extra)} file(s) no manifest lists, first {extra[0].split('/', 1)[1]}")
    for name, e in sorted(listed.items()):
        data = members[name]
        if len(data) != e["bytes"] or hashlib.sha256(data).hexdigest() != e["sha256"]:
            raise Refused(f"{e['path']} does not match its recorded sha256 — tampered or truncated")
    digest = payload_digest(manifest["files"])
    if digest != manifest["payload_digest"]:
        raise Refused(f"payload digest {digest[:12]} != the manifest's {manifest['payload_digest'][:12]}")
    if sums is None or sums.decode() != digest_lines(manifest["files"]):
        raise Refused("SHA256SUMS is missing or disagrees with BUNDLE.json")
    if expect_digest and digest != expect_digest:
        raise Refused(f"payload digest {digest} is not the one asked for ({expect_digest})")

    # One commit, cross-read: each GLB's size against the build record that came
    # with it, and every sidecar's mesh present. A file swapped in from another
    # commit and re-hashed into a forged manifest fails here or on --expect-digest.
    def payload(rel: str):
        return json.loads(members[f"{root}/payload/{rel}"])
    record = payload("assets/manifest.json").get("assets", {})
    for e in manifest["files"]:
        rel = e["path"][len("payload/"):]
        if rel.startswith("assets/gltf/"):
            want = record.get(rel.rsplit("/", 1)[1], {}).get("bytes")
            if want is not None and want != e["bytes"]:
                raise Refused(f"{rel} is {e['bytes']} bytes but the build record of commit "
                              f"{commit[:12]} says {want} — a mesh from another build")
    scene_id = manifest["scene"]["id"]
    for row in payload(f"data/sidecars/{scene_id}/index.json")["structures"]:
        side = f"{root}/payload/data/{row['sidecar']}"
        if side in members and row.get("asset") and f"{root}/payload/assets/{row['asset']}" not in members:
            raise Refused(f"{row['id']}'s sidecar names {row['asset']}, which the bundle lacks")
    return {"source_commit": commit, "scene": scene_id,
            "target_date": manifest["scene"].get("target_date"),
            "terrain_epoch": manifest["scene"].get("terrain_epoch"),
            "payload_digest": digest, "files": len(manifest["files"]),
            "structures": manifest["coverage"]["carried"]["structures"],
            "structures_without_glb": len(manifest["coverage"]["structures_without_glb"]),
            "omitted_layers": [f"{l['layer']} · {l['module']}" for l in manifest["coverage"]["omitted_layers"]],
            "review_required": len(manifest["review_required"]),
            "partial": manifest["coverage"].get("partial", False)}


def repro(scene_id: str, commit: str, only: list[str] | None = None, gz: bool = True) -> dict:
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        first = pack(scene_id, commit, Path(a), only, gz)
        second = pack(scene_id, commit, Path(b), only, gz)
    return {"payload_digest": [first["payload_digest"], second["payload_digest"]],
            "archive_sha256": [first["archive_sha256"], second["archive_sha256"]],
            "identical": first["payload_digest"] == second["payload_digest"]
                         and first["archive_sha256"] == second["archive_sha256"]}


# ---------------------------------------------------------------- the discovery manifest

INDEX_SCHEMA = "chicago4d-scene-bundle-index/1"
INDEX_HISTORY = 20
# GitHub's compare status of the NEW bundle's base against the latest-good's base
# (`compare/<latest base>...<new base>`): `ahead` means the new base descends from it.
ADVANCES = ("ahead", "identical")


def index_entry(receipt: dict, tag: str, archive_url: str, release_url: str,
                run_url: str, base_commit: str) -> dict:
    """One published bundle, as the discovery manifest lists it. Refused if it may not be listed."""
    for key in ("payload_digest", "archive_sha256"):
        if not HEX64.match(str(receipt.get(key, ""))):
            raise Refused(f"the pack receipt's {key} is not a sha256: {receipt.get(key)!r}")
    for key, value in (("source_commit", receipt.get("source_commit")), ("base_commit", base_commit)):
        if not HEX40.match(str(value or "")):
            raise Refused(f"{key} is not a full commit sha: {value!r}")
    if receipt.get("partial"):
        raise Refused("a partial bundle (--only) is never published")
    return {"scene": receipt["scene"], "tag": tag, "archive": Path(receipt["archive"]).name,
            "archive_url": archive_url, "release_url": release_url,
            "archive_sha256": receipt["archive_sha256"], "archive_bytes": receipt["archive_bytes"],
            "payload_digest": receipt["payload_digest"], "source_commit": receipt["source_commit"],
            "base_commit": base_commit, "files": receipt["files"],
            "structures": receipt["structures"], "built_at": receipt.get("built_at"),
            "run_url": run_url}


def advance(index: dict | None, entry: dict, compare: str | None) -> tuple[dict, bool, str]:
    """Fold a published bundle into the discovery manifest: (index, moved, why).

    The latest-good pointer moves only to a bundle baked from the same `dev` commit as
    the current one or a descendant of it. Two bakes can finish out of order (a dispatch
    and the nightly do not share a concurrency group), so an older bake that finishes
    last is still published under its own tag but is never pointed at. The bundle the
    pointer leaves goes to the head of `previous`, which keeps INDEX_HISTORY of them.
    """
    if index is None:
        index = {"schema": INDEX_SCHEMA, "scenes": {}}
    if index.get("schema") != INDEX_SCHEMA:
        raise Refused(f"the discovery manifest is {index.get('schema')!r}, not {INDEX_SCHEMA}")
    slot = index["scenes"].setdefault(entry["scene"], {"latest_good": None, "previous": []})
    current = slot["latest_good"]
    if current is None:
        why = "the first bundle published for this scene"
    elif current["payload_digest"] == entry["payload_digest"] \
            and current["source_commit"] == entry["source_commit"]:
        return index, False, "already the latest-good bundle"
    elif compare in ADVANCES:
        why = f"base {entry['base_commit'][:12]} is {compare} of the latest-good's base {current['base_commit'][:12]}"
    else:
        return index, False, (f"base {entry['base_commit'][:12]} is {compare or 'not compared'} against "
                               f"the latest-good's base {current['base_commit'][:12]}: a stale or "
                               f"diverged bake does not move the pointer")
    if current is not None:
        slot["previous"] = ([current] + [p for p in slot["previous"]
                                         if p["tag"] not in (current["tag"], entry["tag"])])[:INDEX_HISTORY]
    slot["latest_good"] = entry
    index["updated_at"] = entry.get("built_at")
    return index, True, why


# ---------------------------------------------------------------- self-test

def self_test() -> int:
    failures = []

    def expect(label: str, ok: bool, detail: str = "") -> None:
        print(f"{'ok  ' if ok else 'FAIL'} {label}" + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(label)

    def refused(label: str, call, needle: str) -> None:
        try:
            call()
        except Refused as exc:
            expect(label, needle in str(exc), str(exc)[:140])
            return
        expect(label, False, "it was accepted")

    snap = Snapshot("HEAD")
    index = snap.json("data/sidecars/1835/index.json")
    snap.close()
    only = [r["id"] for r in index["structures"] if r.get("asset")][:3]
    only += [r["id"] for r in index["structures"] if not r.get("asset")][:1]

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        built = pack("1835", "HEAD", tmp / "a", only)
        seen = verify(Path(built["archive"]))
        expect("a packed bundle verifies as a fresh consumer would read it",
               seen["payload_digest"] == built["payload_digest"],
               f"{seen['files']} files, {seen['source_commit'][:12]}, scene {seen['scene']}")
        expect("it declares the load-drawn layers it does not carry",
               any(l.startswith("data/streets/") for l in seen["omitted_layers"])
               and any(l.startswith("data/flora/") for l in seen["omitted_layers"]))
        expect("it lists a structure that has no GLB rather than dropping it",
               seen["structures_without_glb"] == len(only) - 3)
        expect("a subset says it is partial", seen["partial"] is True)
        again = pack("1835", "HEAD", tmp / "b", only)
        expect("the same commit packs to the same archive bytes and payload digest",
               again["archive_sha256"] == built["archive_sha256"]
               and again["payload_digest"] == built["payload_digest"])
        expect("the digest pin accepts its own bundle",
               verify(Path(built["archive"]), built["payload_digest"])["files"] == built["files"])

        root, members = read_archive(Path(built["archive"]))
        manifest = json.loads(members[f"{root}/BUNDLE.json"])
        glb = next(e["path"] for e in manifest["files"] if e["path"].endswith(".glb")
                   and "terrain__" not in e["path"])

        def variant(name: str, change) -> Path:
            m = dict(members)
            change(m)
            target = tmp / f"{name}.tar"
            mtime = manifest["source"]["commit_time"]
            raw = open(target, "wb")
            with tarfile.open(fileobj=raw, mode="w", format=tarfile.GNU_FORMAT) as tar:
                for n, data in sorted(m.items()):
                    tar.addfile(*_member(n, data, mtime))
            raw.close()
            return target

        def flip(m):
            data = bytearray(m[f"{root}/{glb}"])
            data[len(data) // 2] ^= 0xFF
            m[f"{root}/{glb}"] = bytes(data)
        refused("a flipped byte in a mesh is refused",
                lambda: verify(variant("tampered", flip)), "tampered")
        refused("a missing file is refused",
                lambda: verify(variant("missing", lambda m: m.pop(f"{root}/{glb}"))), "missing")
        refused("a file no manifest lists is refused",
                lambda: verify(variant("extra", lambda m: m.__setitem__(f"{root}/payload/extra.txt", b"x"))),
                "no manifest lists")
        refused("a member climbing out of the bundle is refused",
                lambda: verify(variant("climb", lambda m: m.__setitem__(f"{root}/../evil", b"x"))),
                "unsafe")
        refused("an archive with no BUNDLE.json is refused",
                lambda: verify(variant("bare", lambda m: m.pop(f"{root}/BUNDLE.json"))), "BUNDLE.json")

        def forge(m, swap_to: bytes):
            m[f"{root}/{glb}"] = swap_to
            forged = json.loads(m[f"{root}/BUNDLE.json"])
            for e in forged["files"]:
                if e["path"] == glb:
                    e["bytes"], e["sha256"] = len(swap_to), hashlib.sha256(swap_to).hexdigest()
            forged["payload_digest"] = payload_digest(forged["files"])
            m[f"{root}/BUNDLE.json"] = json.dumps(forged).encode()
            m[f"{root}/SHA256SUMS"] = digest_lines(forged["files"]).encode()
        other = next(e["path"] for e in manifest["files"] if e["path"].endswith(".glb")
                     and e["path"] != glb and e["bytes"] != next(
                         f["bytes"] for f in manifest["files"] if f["path"] == glb))
        refused("a mesh from another build, re-hashed into a forged manifest, is refused",
                lambda: verify(variant("mixed", lambda m: forge(m, members[f"{root}/{other}"]))),
                "another build")
        same_size = bytearray(members[f"{root}/{glb}"])
        same_size[-1] ^= 0x01
        refused("a forged manifest the size check cannot see is refused by the digest pin",
                lambda: verify(variant("forged", lambda m: forge(m, bytes(same_size))),
                               built["payload_digest"]),
                "not the one asked for")

    refused("a GLB no bake recorded and no LICENSES.md row covers does not ship",
            lambda: licence_basis("assets/gltf/stray.glb", {}, "nothing"), "rights are unknown")
    expect("a recorded GLB ships on the project licence",
           "recorded bake" in licence_basis("assets/gltf/x.glb", {"x.glb": {"kind": "generated"}}, ""))
    expect("a source still in rights check refuses geometry",
           bool(rights_refusals({"s": {"rights_status": "check_required", "asset_use": "geometry"}}))
           and not rights_refusals({"s": {"rights_status": "check_required", "asset_use": "text"}}))
    refused("a contract that lost its layer table refuses rather than claiming full coverage",
            lambda: omitted_layers("no table here"), "lost its T-0252 layer table")

    def published(n: int, partial: bool = False) -> dict:
        receipt = {"scene": "1835", "archive": f"/tmp/b{n}.tar.gz", "archive_sha256": f"{n:064x}",
                   "archive_bytes": 1, "payload_digest": f"{n + 100:064x}", "source_commit": f"{n:040x}",
                   "files": 1, "structures": 1, "partial": partial, "built_at": f"2026-10-0{n % 9 + 1}T06:00:00Z"}
        return index_entry(receipt, f"tag{n}", "u", "r", "run", f"{n + 200:040x}")
    idx, moved, _ = advance(None, published(1), None)
    expect("the first published bundle becomes the latest-good", moved
           and idx["scenes"]["1835"]["latest_good"]["tag"] == "tag1")
    idx, moved, _ = advance(idx, published(1), "identical")
    expect("the same bundle again moves nothing", not moved)
    idx, moved, _ = advance(idx, published(2), "ahead")
    slot = idx["scenes"]["1835"]
    expect("a bake of a newer dev commit moves the pointer and keeps the old one as previous-good",
           moved and slot["latest_good"]["tag"] == "tag2" and slot["previous"][0]["tag"] == "tag1")
    for status in ("behind", "diverged", None):
        idx, moved, why = advance(idx, published(3), status)
        expect(f"a bake whose base is {status or 'not compared'} does not move the pointer",
               not moved and idx["scenes"]["1835"]["latest_good"]["tag"] == "tag2", why)
    for n in range(4, 4 + INDEX_HISTORY + 3):
        idx, _, _ = advance(idx, published(n), "ahead")
    expect(f"previous-good keeps {INDEX_HISTORY} bundles, newest first",
           len(idx["scenes"]["1835"]["previous"]) == INDEX_HISTORY
           and idx["scenes"]["1835"]["previous"][0]["tag"] == f"tag{3 + INDEX_HISTORY + 2}")
    refused("a partial bundle is never listed",
            lambda: published(9, partial=True), "partial")
    refused("a manifest of another schema is refused, not overwritten",
            lambda: advance({"schema": "something/0", "scenes": {}}, published(1), None), "not " + INDEX_SCHEMA)

    print(f"scene_bundle self-test: {'PASS' if not failures else 'FAIL ' + ', '.join(failures)}")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("pack", help="pack one scene from one commit")
    p.add_argument("--scene", default="1835")
    p.add_argument("--commit", default="HEAD")
    p.add_argument("--out", default=str(Path(tempfile.gettempdir()) / "chicago4d-bundles"))
    p.add_argument("--only", nargs="*", help="a structure subset (the bundle then says partial)")
    p.add_argument("--receipt", help="write the pack receipt, with the build instant, here")
    v = sub.add_parser("verify", help="verify an archive as a fresh consumer")
    v.add_argument("archive")
    v.add_argument("--expect-digest")
    r = sub.add_parser("repro", help="pack the same commit twice and compare")
    r.add_argument("--scene", default="1835")
    r.add_argument("--commit", default="HEAD")
    a = sub.add_parser("advance", help="fold a published bundle into the discovery manifest")
    a.add_argument("--index", required=True, help="the current manifest (absent: a new one)")
    a.add_argument("--receipt", required=True, help="the pack receipt of the published bundle")
    a.add_argument("--tag", required=True)
    a.add_argument("--archive-url", required=True)
    a.add_argument("--release-url", required=True)
    a.add_argument("--run-url", required=True)
    a.add_argument("--base-commit", required=True, help="the dev commit the bake was built from")
    a.add_argument("--compare", default="", help="GitHub compare status of the new base against the latest-good's")
    a.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    try:
        if args.self_test:
            return self_test()
        if args.cmd == "pack":
            out = pack(args.scene, args.commit, Path(args.out), args.only)
            if args.receipt:
                import datetime
                Path(args.receipt).write_text(json.dumps(
                    {**out, "built_at": datetime.datetime.now(datetime.timezone.utc)
                     .strftime("%Y-%m-%dT%H:%M:%SZ")}, indent=1) + "\n")
            print(json.dumps(out, indent=1, ensure_ascii=False))
            return 0
        if args.cmd == "verify":
            out = verify(Path(args.archive), args.expect_digest)
            print(json.dumps(out, indent=1, ensure_ascii=False))
            print(f"VERIFIED {out['scene']} @ {out['source_commit']} — payload {out['payload_digest']}")
            return 0
        if args.cmd == "repro":
            out = repro(args.scene, args.commit)
            print(json.dumps(out, indent=1, ensure_ascii=False))
            print("REPRODUCIBLE" if out["identical"] else "NOT REPRODUCIBLE")
            return 0 if out["identical"] else 1
        if args.cmd == "advance":
            old = Path(args.index)
            entry = index_entry(json.loads(Path(args.receipt).read_text()), args.tag, args.archive_url,
                                args.release_url, args.run_url, args.base_commit)
            index, moved, why = advance(json.loads(old.read_text()) if old.is_file() else None,
                                        entry, args.compare or None)
            Path(args.out).write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n")
            print(json.dumps({"advanced": moved, "why": why, "tag": args.tag}, ensure_ascii=False))
            return 0
        ap.print_help()
        return 2
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
