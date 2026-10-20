#!/usr/bin/env python3
"""merge_asset_registry.py — the lap's entry-by-entry merge of the two asset registries (T-2892).

WHY (owner, 2026-10-19: "build it and merge to dev"). `assets/manifest.json` and
`assets/manifest.web.json` are ONE JSON OBJECT FOR THE WHOLE TOWN, keyed by GLB name, and
every bake rewrites the file whole. So two PRs that bake DIFFERENT structures change
different entries and still conflict on the file: measured on 2026-10-19, #1104 (1637's
cheek lights) was conflicting with dev on `assets/manifest.json` and NOTHING ELSE, and #1109
(1625's south lights) carried the same conflict beside its real one. Each such conflict cost
a full steward run to merge `dev` and rebake — the lap refused it as a REAL CONFLICT because
the file is outside both its generated set and tools/derived_manifest.json.

Neither list is the right home. The registry is not regenerable from source by any one cheap
command (it is written by the bake, entry by entry, as a side effect of building GLBs), so
it cannot go in derived_manifest.json's `resolves`; and "take ours" — the generated set's
rule — would silently drop the other side's entries. What IS true is that the file is a map
whose entries are owned by their GLBs: an entry changes exactly when its master is rebuilt.

THE RULE, per top-level key and per entry of the asset map (`assets` / `masters`):

    both sides agree                        -> that value
    only one side changed it from the base  -> that side's value (an added or deleted
                                               entry is a change like any other)
    both changed it, differently            -> REFUSED, with one exception, below

The refusal is the case where both branches rebuilt the SAME master. The exception is the
one double change that is not a disagreement: an asset built by a pure-Python emitter (K01,
K13, K16, K12, draft, haystack — no Blender, seconds, same bytes from same inputs) where at
least one side changed nothing but `inputs_sha256`, which is what a shared generator change
leaves on every house it touches. Measured on #1104 against dev, 2026-10-19: 26 K01-family
entries, every one byte-identical on both sides, three input hashes each. Those structures
are emitted again ON THE MERGED TREE — the emitter computes the hash, nobody chooses it — and
kept only if every GLB it writes is byte-identical to the merge's; otherwise everything is
put back as git left it and the PR waits for a run, as before.

AND THE GATE STILL DECIDES. The lap pushes the merge and CI's gate runs on it:
`validate.py` compares every entry's inputs hash against the merged tree (an entry merged
beside a generator change that should have rebaked it reads STALE), and
`measure_web_derivatives.py` checks every recorded master hash against the GLB on disk.
Auto-merge fires on a green gate and on nothing else.

BYTES, NOT JUST CONTENT. Each file is re-serialized the way its writer writes it —
generators/build.py: `json.dumps(indent=2, sort_keys=True) + "\\n"`; web_derivatives.sh:
`json.dumps(indent=2) + "\\n"` with the masters sorted — and the tool first proves that
serializer reproduces ours, theirs and the base byte for byte. If a writer ever changes
format, the proof fails and the file is refused rather than rewritten in a format nobody
chose.

Usage (inside a merge that stopped on conflicts, from the repository root or anywhere in it):
    python3 chicago/4d/tools/merge_asset_registry.py --list
    python3 chicago/4d/tools/merge_asset_registry.py --resolve <path>...
    python3 chicago/4d/tools/merge_asset_registry.py --self-test

--resolve writes every path or none: one refusal leaves every file as git left it, and the
exit status is 1.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

# Enumerated, not pattern-matched — the same safety property derived_manifest.json states:
# what is in scope can be read here, and nothing else is ever touched.
REGISTRIES = {
    "chicago/4d/assets/manifest.json": {"map": "assets", "sort_keys": True},
    "chicago/4d/assets/manifest.web.json": {"map": "masters", "sort_keys": False},
}

# The emitters that build a GLB in pure Python — no Blender, seconds, the same bytes from
# the same inputs (each has a --check that holds it to that) — in the order tools/bake.sh
# runs them. Only an asset one of these wrote can be re-emitted inside the lap.
PURE_EMITTERS = (
    "generators/k01_emit.py",
    "generators/k13_emit.py",
    "generators/k16_emit.py",
    "generators/k12_emit.py",
    "generators/draft_emit.py",
    "generators/haystack_emit.py",
)

MISSING = object()


class Refused(Exception):
    pass


def dumps(obj, sort_keys: bool) -> str:
    return json.dumps(obj, indent=2, sort_keys=sort_keys) + "\n"


def three_way(base: dict, ours: dict, theirs: dict, where: str, reemit: dict | None = None) -> dict:
    out = {}
    order = list(ours) + [k for k in theirs if k not in ours] + [k for k in base if k not in ours and k not in theirs]
    for key in order:
        b, o, t = base.get(key, MISSING), ours.get(key, MISSING), theirs.get(key, MISSING)
        if o == t:
            pick = o
        elif o == b:
            pick = t
        elif t == b:
            pick = o
        elif reemit is not None and recipe_only(b, o, t) is not None:
            pick = recipe_only(b, o, t)  # provisional: the emitter rewrites its hash on the merged tree
            reemit[key] = pick["structure_id"]
        else:
            raise Refused(f"{where}{key!r}: both sides changed it differently")
        if pick is not MISSING:
            out[key] = pick
    return out


def recipe_only(b, o, t):
    """The one double change that is not a disagreement, or None.

    Both sides rebuilt the same asset with a pure-Python emitter, and at least one of them
    changed nothing but `inputs_sha256` — the mark a SHARED generator change leaves on
    every asset it touches without moving a byte. Measured on #1104 against dev, 2026-10-19:
    27 K01-family entries changed on both sides; 26 had identical bytes on both and three
    different input hashes, and the 27th was the PR's own house (1637), rebuilt with new
    geometry on its side and only re-hashed on dev's. That is not two buildings. It is one
    building, or one building and a recipe, and the honest resolution is the one a run makes
    — emit it again on the merged tree — never a hash chosen by hand (restamp_inputs.py
    refuses that too).

    Returns the side to take provisionally: the one that changed more than the hash (the
    rebuilt geometry, whose GLB git has merged cleanly), or ours when neither did.
    """
    if not (isinstance(o, dict) and isinstance(t, dict)):
        return None
    if o.get("generator") not in PURE_EMITTERS or not o.get("structure_id"):
        return None
    if (o.get("generator"), o.get("structure_id")) != (t.get("generator"), t.get("structure_id")):
        return None
    strip = lambda e: {k: v for k, v in e.items() if k != "inputs_sha256"}  # noqa: E731
    if strip(o) == strip(t):
        return o
    if isinstance(b, dict) and strip(t) == strip(b):
        return o
    if isinstance(b, dict) and strip(o) == strip(b):
        return t
    return None


def merge_texts(path: str, base_txt: str, ours_txt: str, theirs_txt: str,
                reemit: dict | None = None) -> str:
    spec = REGISTRIES[path]
    sides = {}
    for name, txt in (("base", base_txt), ("ours", ours_txt), ("theirs", theirs_txt)):
        try:
            obj = json.loads(txt)
        except ValueError as e:
            raise Refused(f"{name} is not JSON ({e})")
        if not isinstance(obj, dict) or not isinstance(obj.get(spec["map"]), dict):
            raise Refused(f"{name} has no `{spec['map']}` object — not the shape this tool knows")
        if dumps(obj, spec["sort_keys"]) != txt:
            raise Refused(f"{name} is not written the way its writer writes it — refusing to re-serialize")
        sides[name] = obj
    base, ours, theirs = sides["base"], sides["ours"], sides["theirs"]
    m = spec["map"]
    merged = three_way({k: v for k, v in base.items() if k != m},
                       {k: v for k, v in ours.items() if k != m},
                       {k: v for k, v in theirs.items() if k != m}, "top-level ")
    entries = three_way(base[m], ours[m], theirs[m], f"{m}.",
                        reemit if path == "chicago/4d/assets/manifest.json" else None)
    if list(ours[m]) == sorted(ours[m]):
        entries = dict(sorted(entries.items()))
    # Put the map back where ours keeps it.
    result = {}
    for key in ours:
        result[key] = entries if key == m else merged.get(key, MISSING)
    for key, value in merged.items():
        if key not in result:
            result[key] = value
    result = {k: v for k, v in result.items() if v is not MISSING}
    return dumps(result, spec["sort_keys"])


def git(*args: str, cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


def stage(path: str, n: int, cwd: str | None = None) -> str | None:
    r = git("show", f":{n}:{path}", cwd=cwd, check=False)
    return r.stdout if r.returncode == 0 else None


def resolve(paths: list[str], cwd: str | None = None) -> int:
    top = git("rev-parse", "--show-toplevel", cwd=cwd).stdout.strip()
    results, reemit = {}, {}
    for path in paths:
        if path not in REGISTRIES:
            print(f"merge_asset_registry: REFUSED {path}: not one of the registries this tool merges")
            return 1
        texts = [stage(path, n, cwd=top) for n in (1, 2, 3)]
        if any(t is None for t in texts):
            print(f"merge_asset_registry: REFUSED {path}: not a content conflict on both sides "
                  "(added or deleted on one) — left as git left it")
            return 1
        try:
            results[path] = merge_texts(path, *texts, reemit=reemit)
        except Refused as e:
            print(f"merge_asset_registry: REFUSED {path}: {e}")
            return 1
    unmerged = set(git("diff", "--name-only", "--diff-filter=U", cwd=top).stdout.split())
    clashing = sorted(k for k in reemit if f"chicago/4d/assets/gltf/{k}" in unmerged)
    if clashing:
        print(f"merge_asset_registry: REFUSED: {clashing[0]} is itself conflicting, so its two "
              "builds differ in bytes, not only in inputs — a rebake, not a merge")
        return 1
    as_git_left = {}
    for path, text in results.items():
        with open(os.path.join(top, path), "rb") as f:
            as_git_left[path] = f.read()
        with open(os.path.join(top, path), "w", encoding="utf-8") as f:
            f.write(text)
    if reemit:
        why = reemit_on_merged_tree(top, reemit)
        if why:
            for path, raw in as_git_left.items():
                with open(os.path.join(top, path), "wb") as f:
                    f.write(raw)
            print(f"merge_asset_registry: REFUSED: {why} — every file put back as git left it")
            return 1
    for path in results:
        print(f"merge_asset_registry: merged {path} entry by entry")
    return 0


def reemit_on_merged_tree(top: str, reemit: dict) -> str | None:
    """Run the pure emitters over the structures both sides rebuilt, on the merged tree.
    Returns None when every asset they wrote kept its bytes and only its input hash moved;
    otherwise the reason, with every GLB they wrote restored from the index."""
    app = os.path.join(top, "chicago", "4d")
    man_path = os.path.join(app, "assets", "manifest.json")
    with open(man_path, encoding="utf-8") as f:
        before = json.load(f)["assets"]
    ids = ",".join(sorted(set(reemit.values())))
    wrote_log = tempfile.NamedTemporaryFile(prefix="registry-wrote-", delete=False).name
    print(f"merge_asset_registry: {len(reemit)} entr{'y' if len(reemit) == 1 else 'ies'} changed on "
          f"both sides, at least one only in inputs_sha256 — re-emitting {len(set(reemit.values()))} structure(s) on the merged tree")
    failed = None
    for emitter in PURE_EMITTERS:
        if not os.path.exists(os.path.join(app, emitter)):
            continue
        r = subprocess.run([sys.executable, emitter, "--only", ids, "--wrote", wrote_log],
                           cwd=app, capture_output=True, text=True)
        if r.returncode != 0:
            failed = f"{emitter} exited {r.returncode}: {(r.stdout + r.stderr).strip().splitlines()[-1:]}"
            break
    with open(wrote_log, encoding="utf-8") as f:
        wrote = sorted({line.strip() for line in f if line.strip()})
    os.unlink(wrote_log)
    glbs = [f"chicago/4d/assets/gltf/{n}" for n in wrote]

    def back(reason: str) -> str:
        if glbs:
            git("checkout", "--", *glbs, cwd=top, check=False)
        return reason

    if failed:
        return back(failed)
    missing = sorted(set(reemit) - set(wrote))
    if missing:
        return back(f"no emitter rebuilt {missing[0]}")
    for g in glbs:
        disk = git("hash-object", g, cwd=top).stdout.strip()
        index = git("rev-parse", f":{g}", cwd=top, check=False).stdout.strip()
        if disk != index:
            return back(f"{g.rsplit('/', 1)[-1]} came out with different bytes on the merged tree — "
                        "that is a rebake and its web derivative must follow, so it is a run's")
    with open(man_path, encoding="utf-8") as f:
        after = json.load(f)["assets"]
    for key in sorted(set(before) | set(after)):
        b, a = before.get(key, MISSING), after.get(key, MISSING)
        if b == a:
            continue
        if key not in wrote or not (isinstance(a, dict) and isinstance(b, dict)) \
                or {k: v for k, v in a.items() if k != "inputs_sha256"} != {k: v for k, v in b.items() if k != "inputs_sha256"}:
            return back(f"re-emitting moved {key} beyond its input hash")
    print(f"merge_asset_registry: re-emitted {len(wrote)} asset(s); every GLB byte-identical, "
          "input hashes now those of the merged tree")
    return None


# --- self-test: real merges in a scratch repository ---------------------------------------

def _entry(n: int) -> dict:
    return {"bytes": n, "inputs_sha256": f"{n:064x}", "kind": "generated"}


def _write(repo: str, rel: str, obj, sort_keys: bool) -> None:
    if not sort_keys and isinstance(obj.get("masters"), dict):
        obj["masters"] = dict(sorted(obj["masters"].items()))  # as web_derivatives.sh writes it
    full = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(dumps(obj, sort_keys))


def self_test() -> int:
    failures = 0

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"\n        {detail}" if not ok and detail else ""))
        failures += 0 if ok else 1

    man, web = "chicago/4d/assets/manifest.json", "chicago/4d/assets/manifest.web.json"
    base_man = {"assets": {"a.glb": _entry(1), "b.glb": _entry(2), "c.glb": _entry(3)},
                "blender": "4.2.1", "inputs_scheme": "mesh-inputs-v3"}
    base_web = {"$note": "derived — the note says so", "written_by": "tools/web_derivatives.sh",
                "masters": {"a.glb": "1" * 64, "b.glb": "2" * 64, "c.glb": "3" * 64}}

    scratch: list[str] = []

    def scenario(ours_edit, theirs_edit):
        repo = tempfile.mkdtemp(prefix="c4d-registry-")
        scratch.append(repo)
        git("init", "-q", "-b", "dev", cwd=repo)
        git("config", "user.name", "t", cwd=repo)
        git("config", "user.email", "t@t", cwd=repo)
        _write(repo, man, base_man, True)
        _write(repo, web, base_web, False)
        git("add", "-A", cwd=repo)
        git("commit", "-q", "-m", "base", cwd=repo)
        git("checkout", "-q", "-b", "pr", cwd=repo)
        for rel, obj, sk in ours_edit(json.loads(json.dumps(base_man)), json.loads(json.dumps(base_web))):
            _write(repo, rel, obj, sk)
        git("commit", "-qam", "ours", cwd=repo)
        git("checkout", "-q", "dev", cwd=repo)
        for rel, obj, sk in theirs_edit(json.loads(json.dumps(base_man)), json.loads(json.dumps(base_web))):
            _write(repo, rel, obj, sk)
        git("commit", "-qam", "theirs", cwd=repo)
        git("checkout", "-q", "pr", cwd=repo)
        git("merge", "dev", "--no-edit", cwd=repo, check=False)
        return repo

    def read(repo, rel):
        with open(os.path.join(repo, rel), encoding="utf-8") as f:
            return f.read()

    print("1. two bakes of DIFFERENT structures merge entry by entry, in both files")

    # The shape #1104 had: each side baked a structure the other did not, and two new
    # names sort into the same gap, so git sees both insertions at one line.
    def ours1(m, w):
        m["assets"]["a.glb"] = _entry(11); w["masters"]["a.glb"] = "a" * 64
        m["assets"]["b2.glb"] = _entry(22); w["masters"]["b2.glb"] = "e" * 64
        return [(man, m, True), (web, w, False)]

    def theirs1(m, w):
        m["assets"]["b1.glb"] = _entry(21); w["masters"]["b1.glb"] = "d" * 64
        m["assets"]["c.glb"] = _entry(33); w["masters"]["c.glb"] = "c" * 64
        return [(man, m, True), (web, w, False)]

    repo = scenario(ours1, theirs1)
    u = git("diff", "--name-only", "--diff-filter=U", cwd=repo).stdout.split()
    check("git itself calls both files conflicting", sorted(u) == sorted([man, web]), str(u))
    rc = resolve([man, web], cwd=repo)
    check("--resolve resolves both", rc == 0)
    got_m, got_w = json.loads(read(repo, man)), json.loads(read(repo, web))
    check("manifest: ours' rebake and new entry, theirs' rebake and new entry, all kept",
          got_m["assets"] == {"a.glb": _entry(11), "b.glb": _entry(2), "b1.glb": _entry(21),
                              "b2.glb": _entry(22), "c.glb": _entry(33)}, str(got_m["assets"]))
    check("manifest.web: the same four changes on the masters map",
          got_w["masters"] == {"a.glb": "a" * 64, "b.glb": "2" * 64, "b1.glb": "d" * 64,
                               "b2.glb": "e" * 64, "c.glb": "c" * 64}, str(got_w["masters"]))
    check("written exactly as build.py writes (indent 2, sorted keys, final newline)",
          read(repo, man) == dumps(got_m, True))
    check("written exactly as web_derivatives.sh writes ($note first, masters sorted)",
          read(repo, web) == dumps(got_w, False) and list(got_w) == ["$note", "written_by", "masters"]
          and list(got_w["masters"]) == sorted(got_w["masters"]), str(list(got_w)))

    print("2. both sides rebaked the SAME master — refused, nothing written")

    def ours2(m, w):
        m["assets"]["a.glb"] = _entry(11); w["masters"]["a.glb"] = "a" * 64
        return [(man, m, True), (web, w, False)]

    def theirs2(m, w):
        m["assets"]["a.glb"] = _entry(111); w["masters"]["a.glb"] = "f" * 64
        return [(man, m, True), (web, w, False)]

    repo = scenario(ours2, theirs2)
    before = read(repo, man)
    rc = resolve([man, web], cwd=repo)
    check("--resolve exits 1", rc == 1)
    check("…and leaves the conflicted file exactly as git left it", read(repo, man) == before)

    print("3. a top-level field both sides moved differently is refused; one side's move is taken")

    def ours3(m, w):
        m["blender"] = "4.2.3"; m["assets"]["a.glb"] = _entry(11)
        return [(man, m, True)]

    def theirs3(m, w):
        m["assets"]["c.glb"] = _entry(33); del m["assets"]["b.glb"]
        return [(man, m, True)]

    repo = scenario(ours3, theirs3)
    u = git("diff", "--name-only", "--diff-filter=U", cwd=repo).stdout.split()
    if u:
        check("one side's blender bump merges", resolve(u, cwd=repo) == 0)
    got = json.loads(read(repo, man))
    check("…ours' blender, theirs' deletion of b.glb and both rebakes all stand",
          got["blender"] == "4.2.3" and "b.glb" not in got["assets"]
          and got["assets"]["a.glb"] == _entry(11) and got["assets"]["c.glb"] == _entry(33), str(got))

    def theirs3b(m, w):
        m["blender"] = "4.3.0"; m["assets"]["c.glb"] = _entry(33)
        return [(man, m, True)]

    repo = scenario(ours3, theirs3b)
    check("two different blender versions are refused", resolve([man], cwd=repo) == 1)

    print("4. a file not written the way its writer writes it is refused, not reformatted")
    try:
        merge_texts(man, dumps(base_man, True), json.dumps(base_man) + "\n", dumps(base_man, True))
        check("compact JSON on one side is refused", False, "merge_texts accepted it")
    except Refused:
        check("compact JSON on one side is refused", True)

    print("5. a path outside the two registries is refused")
    check("assets/gltf/x.glb is not merged", resolve(["chicago/4d/assets/gltf/x.glb"], cwd=repo) == 1)

    print("6. a shared recipe moved on both sides: re-emitted on the merged tree")
    # A stand-in for a pure emitter, with the real one's interface (--only, --wrote) and
    # its two outputs: the GLB, whose bytes come from the structure's own record and —
    # when the recipe says `geometry` — from the recipe too; and the manifest entry, whose
    # inputs_sha256 hashes the recipe and the record, written as build.py writes it.
    emitter = """import argparse, hashlib, json, pathlib
ap = argparse.ArgumentParser(); ap.add_argument('--only'); ap.add_argument('--wrote'); a = ap.parse_args()
root = pathlib.Path(__file__).resolve().parent.parent
recipe = (root / 'generators' / 'recipe_a.txt').read_text() + (root / 'generators' / 'recipe_b.txt').read_text()
man = json.loads((root / 'assets' / 'manifest.json').read_text()); wrote = []
for sid in a.only.split(','):
    rec = (root / 'data' / (sid + '.txt')).read_text()
    body = rec + (recipe if 'geometry' in recipe else '')
    name = sid + '__p.glb'
    (root / 'assets' / 'gltf' / name).write_text(body)
    man['assets'][name] = {'bytes': len(body), 'generator': 'generators/k01_emit.py', 'structure_id': sid,
                           'inputs_sha256': hashlib.sha256((recipe + rec).encode()).hexdigest()}
    wrote.append(name)
(root / 'assets' / 'manifest.json').write_text(json.dumps(man, indent=2, sort_keys=True) + '\\n')
open(a.wrote, 'a').writelines(n + '\\n' for n in wrote)
"""

    def emit_repo(theirs_recipe_b: str, ours_record: str = "house one\n"):
        repo = tempfile.mkdtemp(prefix="c4d-registry-emit-")
        scratch.append(repo)
        app = os.path.join(repo, "chicago", "4d")
        for d in ("generators", "data", "assets/gltf"):
            os.makedirs(os.path.join(app, d), exist_ok=True)

        def put(rel, text):
            with open(os.path.join(app, rel), "w", encoding="utf-8") as f:
                f.write(text)

        def bake():
            for sid in ("h1", "h2"):
                subprocess.run([sys.executable, "generators/k01_emit.py", "--only", sid,
                                "--wrote", os.devnull], cwd=app, check=True)

        git("init", "-q", "-b", "dev", cwd=repo)
        git("config", "user.name", "t", cwd=repo)
        git("config", "user.email", "t@t", cwd=repo)
        put("generators/k01_emit.py", emitter)
        put("generators/recipe_a.txt", "a1\n")
        put("generators/recipe_b.txt", "b1\n")
        put("data/h1.txt", "house one\n")
        put("data/h2.txt", "house two\n")
        put("assets/manifest.json", dumps({"assets": {}, "blender": "4.2.1"}, True))
        bake()
        git("add", "-A", cwd=repo)
        git("commit", "-qm", "base", cwd=repo)
        git("checkout", "-qb", "pr", cwd=repo)
        put("generators/recipe_a.txt", "a2\n")       # the PR's own generator change...
        put("data/h1.txt", ours_record)              # ...and, maybe, its own house
        bake()
        git("commit", "-qam", "ours", cwd=repo)
        git("checkout", "-q", "dev", cwd=repo)
        put("generators/recipe_b.txt", theirs_recipe_b)  # dev's, to a different file
        bake()
        git("commit", "-qam", "theirs", cwd=repo)
        git("checkout", "-q", "pr", cwd=repo)
        git("merge", "dev", "--no-edit", cwd=repo, check=False)
        return repo, app

    repo, app = emit_repo("b2\n")
    u = git("diff", "--name-only", "--diff-filter=U", cwd=repo).stdout.split()
    check("only the manifest conflicts (the GLBs are byte-identical on both sides)", u == [man], str(u))
    check("the double re-hash is resolved", resolve([man], cwd=repo) == 0)
    got = json.loads(read(repo, man))["assets"]
    import hashlib
    want = hashlib.sha256(("a2\nb2\n" + "house one\n").encode()).hexdigest()
    check("…with the input hash of the MERGED recipe, which neither side had",
          got["h1__p.glb"]["inputs_sha256"] == want, got["h1__p.glb"]["inputs_sha256"][:12])
    check("…and no GLB moved", git("status", "--porcelain", "--", "chicago/4d/assets/gltf", cwd=repo).stdout == "")

    repo, app = emit_repo("b2\n", ours_record="house one, its porch rebuilt\n")
    check("the PR's own rebuilt house beside dev's re-hash is resolved too",
          resolve([man], cwd=repo) == 0
          and json.loads(read(repo, man))["assets"]["h1__p.glb"]["bytes"] == len("house one, its porch rebuilt\n"))

    repo, app = emit_repo("b2 geometry\n")
    u = git("diff", "--name-only", "--diff-filter=U", cwd=repo).stdout.split()
    if man in u:
        before = read(repo, man)
        check("a recipe change that moves bytes is refused", resolve([man], cwd=repo) == 1)
        check("…the manifest put back with its conflict markers", read(repo, man) == before)
        check("…and every GLB the emitter wrote restored to the merge's own",
              git("diff", "--name-only", "--", "chicago/4d/assets/gltf", cwd=repo).stdout.strip() == "")
    else:
        check("a recipe change that moves bytes conflicts in the GLBs themselves", any(p.endswith(".glb") for p in u), str(u))
        check("…and is refused", resolve([man], cwd=repo) == 1)

    for repo in scratch:
        shutil.rmtree(repo, ignore_errors=True)
    print(f"\nmerge_asset_registry self-test: {'all hold' if not failures else f'{failures} FAILED'}")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--list"]:
        print("\n".join(REGISTRIES))
        return 0
    if argv[:1] == ["--resolve"] and argv[1:]:
        return resolve(argv[1:])
    if argv[:1] == ["--self-test"]:
        return self_test()
    print(__doc__.split("Usage")[1] if "Usage" in __doc__ else __doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
