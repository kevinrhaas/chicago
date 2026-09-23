#!/usr/bin/env python3
"""Did the content bake produce CONTENT, or only its own build stamp? (T-0180)

`chicago-4d-bake.yml` decided whether a nightly had produced anything with
`[ -z "$(git status --porcelain)" ]`. That test can never say no. `publish.sh`
IS the build, and the last thing it writes is the build stamp — the head sha and
a wall clock — into `site/chicago/4d/build.json` and into the gate paragraph of
`site/chicago/4d/walk/index.html`. Both move on every run by construction, so
the tree was always dirty, the `changed=0` branch was unreachable, and every
bake opened a PR whose whole diff was two files and no geometry. Four of them
were open at once on 2026-08-24, and the signal a reviewer needs — *this bake
rebuilt something* — fired identically whether 300 structures had been rebuilt
or nothing at all had.

So the question is asked of the content instead. A dirty path is STAMP-ONLY when
it is one of the two the stamp is written into AND the only thing that moved in
it is the stamp; everything else is content. That is deliberately narrower than
"exclude those two paths": `build.json` growing a real field, or the gate page
changing anywhere but its stamp paragraph, is content and still opens a PR.

Two traps this must not fall into, both recorded on T-0180:

  * The stamp is NOT stopped. It is written, it ships with the next PR that
    carries real content, and the gate screen keeps reading it. What stops is
    the stamp MANUFACTURING that PR.
  * The stamp can never be self-consistent with the commit carrying it —
    merging it changes the head sha it names. Inherent, not a fault to chase.

    tools/bake_content_changed.py              → prints a verdict, exit 0
    tools/bake_content_changed.py --github     → also writes changed=N to $GITHUB_OUTPUT
    tools/bake_content_changed.py --self-test  → the assertions, in a sandbox
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent          # chicago/4d
REPO = ROOT.parent.parent                                      # the repo root

BUILD_JSON = "site/chicago/4d/build.json"
GATE_PAGE = "site/chicago/4d/walk/index.html"

# The three keys publish.sh regenerates on every run, and nothing else in the
# file. A fourth key appearing here is a change to what the build CLAIMS, which
# is content — so this list is exhaustive on purpose.
STAMP_KEYS = {"version", "built_utc", "built_ct"}

# publish.sh replaces exactly this element, whole, with the rendered stamp.
GATE_PLACEHOLDER = '<p class="gate-build" id="gate-build" hidden><!--BUILD_STAMP--></p>'
GATE_OPEN = '<p class="gate-build" id="gate-build">'


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd or REPO, check=True,
                          capture_output=True, text=True).stdout


def committed(path, cwd=None):
    """The path as HEAD has it in BYTES, or None when HEAD does not have it.

    Bytes, not text, because a content path is not always text. `text=True` here
    decoded every committed file as UTF-8, and the bake crashed outright the first
    time a BINARY content file was dirty — `UnicodeDecodeError: 0xf8 in position
    12` on PR #675, whose publish regenerated 372 .glb derivatives. The stamp
    comparison is the only caller that wants characters, and it decodes there,
    where it can say what a failure to decode MEANS.
    """
    r = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=cwd or REPO,
                       capture_output=True)
    return r.stdout if r.returncode == 0 else None


def normalise_gate(text):
    """The gate page with its stamp put back to the placeholder publish.sh found.

    Compared this way, a page whose ONLY difference is the stamp is identical to
    its own source, and a page that changed anywhere else is not.
    """
    i = text.find(GATE_OPEN)
    if i == -1:
        return text
    j = text.find("</p>", i)
    if j == -1:
        return text
    return text[:i] + GATE_PLACEHOLDER + text[j + len("</p>"):]


def is_stamp_only(path, cwd=None):
    """True when this dirty path carries the build stamp and nothing else."""
    old_bytes = committed(path, cwd)
    if old_bytes is None:
        return False                      # a NEW file is never just a stamp
    new_path = (cwd or REPO) / pathlib.Path(path)
    if not new_path.exists():
        return False                      # a DELETED file is content
    try:
        old = old_bytes.decode("utf-8")
        new = new_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False                      # a BINARY file is content, never a stamp

    if path == BUILD_JSON:
        try:
            a, b = json.loads(old), json.loads(new)
        except json.JSONDecodeError:
            return False
        moved = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
        return moved <= STAMP_KEYS and set(a) == set(b)
    if path == GATE_PAGE:
        return normalise_gate(old) == normalise_gate(new)
    return False


def content_paths(cwd=None):
    """Every dirty path under the app that is not purely the build stamp.

    THE MIRROR IS STILL IN THE PATHSPEC AND USUALLY ANSWERS NOTHING (T-0938).
    `site/chicago/4d` is untracked and .gitignored in this repository now, so
    `git status --porcelain` never names it here and the stamp exclusions below
    can only fire in a tree where it is tracked — which is exactly the sandbox
    `--self-test` builds. Both halves are deliberate. The pathspec stays because
    it costs nothing and because the question this asks is about the app's whole
    output, tracked or not; the self-test keeps exercising the stamp logic
    because that logic is what a REAL tracked build stamp would still need, and a
    gate whose assertions stop running is a gate that has quietly stopped.

    What changed for the real tree is simpler and better: the bake's content
    signal now rests entirely on `chicago/4d/`, which is where bake.sh writes
    geometry, and the build stamp cannot manufacture a PR because the two files
    it is written into are not committed at all.
    """
    out = git("status", "--porcelain", "--", "chicago/4d", "site/chicago/4d",
              cwd=cwd)
    paths = []
    for line in out.splitlines():
        if not line.strip():
            continue
        # `XY path`, and `XY old -> new` for a rename; the destination is the
        # one that exists on disk, which is what is_stamp_only reads.
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip().strip('"')
        if is_stamp_only(path, cwd):
            continue
        paths.append(path)
    return paths


def report(cwd=None):
    paths = content_paths(cwd)
    if not paths:
        print("bake produced no CONTENT — only its own build stamp moved "
              f"({BUILD_JSON} and the gate stamp). No branch, no PR: the PR is "
              "the signal that a bake rebuilt something, and nothing was "
              "rebuilt. The stamp ships with the next bake that carries content.")
        return 0
    print(f"bake produced content — {len(paths)} path(s) beyond the build stamp:")
    for p in paths[:20]:
        print(f"  {p}")
    if len(paths) > 20:
        print(f"  … and {len(paths) - 20} more")
    return 1


# --- the self-test ---------------------------------------------------------
# A sandbox repo rather than the live tree, so the assertions can dirty files
# without touching anything and can run on a clean checkout.

def _sandbox(tmp):
    root = pathlib.Path(tmp)
    (root / "chicago/4d/data").mkdir(parents=True)
    (root / "site/chicago/4d/walk").mkdir(parents=True)
    (root / BUILD_JSON).write_text(json.dumps(
        {"version": "aaaaaaa", "built_utc": "2026-08-24T06:04:28Z",
         "built_ct": "Aug 24, 2026, 1:04 AM CT"}, indent=2) + "\n")
    (root / GATE_PAGE).write_text(
        "<html><body>\n" + GATE_PLACEHOLDER + "\n<p>the town</p></body></html>\n")
    (root / "chicago/4d/data/thing.json").write_text('{"a": 1}\n')
    # A COMMITTED BINARY file, because a published tree is mostly .glb and .png
    # and this tool used to decode every committed path as UTF-8. 0xf8 is the
    # byte that actually killed the bake on PR #675.
    (root / "site/chicago/4d/walk/master.glb").write_bytes(
        b"glTF\x02\x00\x00\x00" + bytes(range(0xf0, 0x100)))
    git("init", "-q", cwd=root)
    git("config", "user.email", "t@example.com", cwd=root)
    git("config", "user.name", "t", cwd=root)
    git("add", "-A", cwd=root)
    git("commit", "-qm", "base", cwd=root)
    return root


def _stamp(root, version="bbbbbbb"):
    (root / BUILD_JSON).write_text(json.dumps(
        {"version": version, "built_utc": "2026-08-24T06:32:39Z",
         "built_ct": "Aug 24, 2026, 1:32 AM CT"}, indent=2) + "\n")
    p = root / GATE_PAGE
    p.write_text(p.read_text().replace(
        GATE_PLACEHOLDER, GATE_OPEN + f"build {version} · Aug 24, 2026</p>"))


def self_test():
    cases, failed = [], 0

    def case(name, got, want):
        nonlocal failed
        ok = got == want
        cases.append((ok, name, got, want))
        if not ok:
            failed += 1

    with tempfile.TemporaryDirectory() as tmp:
        root = _sandbox(tmp)
        case("a clean tree has no content", content_paths(root), [])

        _stamp(root)
        case("a stamp-only bake has no content", content_paths(root), [])

        (root / "chicago/4d/data/thing.json").write_text('{"a": 2}\n')
        case("a data byte IS content, stamp or no stamp",
             content_paths(root), ["chicago/4d/data/thing.json"])

        (root / "chicago/4d/data/thing.json").write_text('{"a": 1}\n')
        (root / "site/chicago/4d/walk/asset.glb").write_text("glb\n")
        case("a NEW published file is content",
             content_paths(root), ["site/chicago/4d/walk/asset.glb"])
        (root / "site/chicago/4d/walk/asset.glb").unlink()

        # THE CRASH THIS TOOL TOOK ON PR #675, as a case rather than a story.
        # A committed binary file that CHANGES reaches `is_stamp_only`, which
        # read both sides as UTF-8 text; the bake died with UnicodeDecodeError
        # instead of reporting the content, and a green tree looked broken.
        glb = root / "site/chicago/4d/walk/master.glb"
        glb.write_bytes(b"glTF\x02\x00\x00\x00" + bytes(range(0xe0, 0xf0)))
        case("a committed BINARY file that changed is content, not a crash",
             content_paths(root), ["site/chicago/4d/walk/master.glb"])
        glb.write_bytes(b"glTF\x02\x00\x00\x00" + bytes(range(0xf0, 0x100)))
        case("…and restoring its bytes makes it clean again",
             content_paths(root), [])

        p = root / GATE_PAGE
        p.write_text(p.read_text().replace("the town", "the TOWN"))
        case("the gate page changed AWAY from its stamp is content",
             content_paths(root), [GATE_PAGE])
        p.write_text(p.read_text().replace("the TOWN", "the town"))

        b = root / BUILD_JSON
        d = json.loads(b.read_text())
        d["structures"] = 359
        b.write_text(json.dumps(d, indent=2) + "\n")
        case("build.json growing a real field is content",
             content_paths(root), [BUILD_JSON])
        _stamp(root)

        (root / "chicago/4d/data/thing.json").unlink()
        case("a DELETED data file is content",
             content_paths(root), ["chicago/4d/data/thing.json"])

    # The gate this drifts through: the exclusions above are the two paths
    # publish.sh actually stamps, and if publish.sh ever stamps a third the
    # verdict goes quietly wrong. Assert against publish.sh itself.
    publish = (ROOT / "tools/publish.sh").read_text(encoding="utf-8")
    case("publish.sh still writes the stamp into build.json",
         '$SITE/build.json' in publish, True)
    case("publish.sh still stamps the gate page's placeholder",
         GATE_PLACEHOLDER in publish, True)

    for ok, name, got, want in cases:
        if ok:
            print(f"  ok    {name}")
        else:
            print(f"  FAIL  {name}\n        got  {got}\n        want {want}")
    if failed:
        print(f"SELF-TEST FAIL — {failed} of {len(cases)} case(s)")
        return 1
    print(f"SELF-TEST PASS — the bake's content test refuses the stamp and "
          f"nothing else ({len(cases)} cases)")
    return 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    changed = report()
    if "--github" in sys.argv and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"changed={changed}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
