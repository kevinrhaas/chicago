#!/usr/bin/env python3
"""merge_additions.py — clear a text conflict where BOTH sides only ADDED lines.

    python3 chicago/4d/tools/merge_additions.py --resolve PATH...   (from the repo top,
            mid-merge) exit 0: every PATH resolved and staged; exit 1: at least one
            was not, and those are named and left as git left them
    python3 chicago/4d/tools/merge_additions.py --self-test

WHY (2026-11-27, the evening batch). Two pull requests that each add a new step to
tools/check.sh at the same spot, or each put a new section on top of docs/STATUS.md,
conflict in git even though nobody disagrees about anything: the answer is both, one
after the other. The batch merges did that by hand, every time.

THE LINE IT HOLDS: a conflict is resolved only if, in EVERY conflicting hunk, the
merge base held nothing (diff3's base section is empty), so neither side changed or
removed a line the other kept. Then the result is ours' lines followed by theirs' —
`git merge-file --union`. A hunk where either side edited or deleted an existing line
is a real disagreement and is refused, as is a file with a side missing (added on one
side and deleted on the other). Only the suffixes in UNION_OK are tried: prose and
shell step lists, where two additions placed one after the other still read. A JSON
list, a Python call or a table row is not, and is refused whatever the hunks say.
The gate runs on the result either way; this only decides what is worth gating.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

UNION_OK = (".md", ".sh")


def git(*args, cwd=None, check=True, inp=None) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, input=inp)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def stage(path: str, n: int, cwd=None) -> str | None:
    r = subprocess.run(["git", "show", f":{n}:{path}"], cwd=cwd, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def additions_only(diff3: str) -> bool:
    """True when every conflict hunk in a diff3-style merge has an empty base section."""
    state, base_lines, hunks = None, 0, 0
    for line in diff3.splitlines():
        if line.startswith("<<<<<<< "):
            state, base_lines, hunks = "ours", 0, hunks + 1
        elif line.startswith("||||||| ") and state == "ours":
            state = "base"
        elif line.startswith("=======") and state in ("ours", "base"):
            if state == "base" and base_lines:
                return False
            if state == "ours":          # no base marker at all: not a diff3 hunk
                return False
            state = "theirs"
        elif line.startswith(">>>>>>> ") and state == "theirs":
            state = None
        elif state == "base":
            base_lines += 1
    return hunks > 0 and state is None


def resolve(path: str, cwd=None) -> str | None:
    """None when resolved and staged, else the reason it was not."""
    if not path.endswith(UNION_OK):
        return "not a file type two additions can be stacked in"
    base, ours, theirs = (stage(path, n, cwd) for n in (1, 2, 3))
    if ours is None or theirs is None:
        return "one side deleted it"
    base = base or ""
    with tempfile.TemporaryDirectory() as d:
        files = []
        for name, text in (("ours", ours), ("base", base), ("theirs", theirs)):
            p = os.path.join(d, name)
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
            files.append(p)
        r = subprocess.run(["git", "merge-file", "-p", "--diff3", "-L", "ours", "-L", "base",
                            "-L", "theirs", *files], capture_output=True, text=True)
        if r.returncode <= 0:
            union = r.stdout                      # no conflict left at all
        elif not additions_only(r.stdout):
            return "a hunk changes or removes a line the other side kept"
        else:
            u = subprocess.run(["git", "merge-file", "-p", "--union", *files],
                               capture_output=True, text=True)
            if u.returncode < 0:
                return "git merge-file --union failed"
            union = u.stdout
    with open(os.path.join(cwd or ".", path), "w", encoding="utf-8") as f:
        f.write(union)
    git("add", "--", path, cwd=cwd)
    return None


def main(argv: list[str]) -> int:
    if argv[:1] == ["--self-test"]:
        return self_test()
    if argv[:1] != ["--resolve"] or len(argv) < 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    bad = 0
    for path in argv[1:]:
        why = resolve(path)
        if why:
            bad += 1
            print(f"merge_additions: {path} — left as a conflict: {why}")
        else:
            print(f"merge_additions: {path} — both sides only added lines; kept both")
    return 1 if bad else 0


def self_test() -> int:
    with tempfile.TemporaryDirectory() as d:
        g = lambda *a: git(*a, cwd=d)  # noqa: E731
        g("init", "-q", "-b", "main")
        g("config", "user.email", "t@t"); g("config", "user.name", "t")
        w = lambda p, s: open(os.path.join(d, p), "w").write(s)  # noqa: E731
        w("check.sh", "step a\nstep b\n"); w("notes.md", "one\ntwo\n"); w("x.json", "[1]\n")
        g("add", "-A"); g("commit", "-qm", "root")
        g("checkout", "-qb", "left")
        w("check.sh", "step a\nstep L\nstep b\n"); w("notes.md", "one changed\ntwo\n")
        w("x.json", "[1, 2]\n")
        g("commit", "-qam", "left")
        g("checkout", "-q", "main")
        w("check.sh", "step a\nstep R\nstep b\n"); w("notes.md", "one other\ntwo\n")
        w("x.json", "[1, 3]\n")
        g("commit", "-qam", "right")
        subprocess.run(["git", "merge", "left"], cwd=d, capture_output=True)
        assert resolve("check.sh", d) is None
        got = open(os.path.join(d, "check.sh")).read()
        assert got == "step a\nstep R\nstep L\nstep b\n", got
        assert "changes or removes" in resolve("notes.md", d)
        assert "<<<<<<<" in open(os.path.join(d, "notes.md")).read()
        assert "file type" in resolve("x.json", d)
    assert additions_only("<<<<<<< o\nA\n||||||| b\n=======\nB\n>>>>>>> t\n")
    assert not additions_only("<<<<<<< o\nA\n||||||| b\nold\n=======\nB\n>>>>>>> t\n")
    assert not additions_only("<<<<<<< o\nA\n=======\nB\n>>>>>>> t\n")
    assert not additions_only("plain\n")
    print("merge_additions self-test: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
