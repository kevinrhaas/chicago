#!/usr/bin/env python3
"""Every workflow job that installs Playwright, or runs Blender, runs on a PINNED image.

T-3169. On 2026-10-26 GitHub moved `ubuntu-latest` to ubuntu-26.04, and the
`playwright@1.56.1` every smoke here installs refuses it outright:

    BEWARE: your OS is not officially supported by Playwright; ...
    Error: ERROR: Playwright does not support chromium on ubuntu26.04-x64

All eighteen smoke legs of content build #2031 died in `Install Playwright`, so
no bake could reach `open-pr`. Nothing in the tree had changed: a moving label
moved. Three workflows had already pinned `ubuntu-24.04` (the full-body smoke,
the humans fixture job, moving frames) and four jobs had not; those four broke.

So the rule is the one the pinned three were already keeping: a job that
installs Playwright or its browser system deps names an exact image, never a
`-latest` label. The image is also what every leg cost, frame-time ceiling and
SMOKE_TIMING reading was measured on, so upgrading Playwright and the image is a
re-measurement made on purpose, in one change, and not something a label does
overnight.

T-3296 put Blender under the same rule, because for a bake the image is part of
the recipe. When `ubuntu-latest` moved, the content build's bake job moved with
it, and the same pinned Blender wrote different UVs for the same code on 26.04:
262 committed masters read as moved on every whole-town bake, re-deriving them
took fourteen minutes, and the job died at its cap on every nightly from
2026-10-17. A job that sources `generators/blender.pin` or runs `tools/bake.sh`
names an exact image, and the bake's image changes only as a re-bake on purpose.

The workflows are read as text, job by job (a job is a two-space-indented key
under `jobs:`), the same way `bake_warranted.py` reads the content build: the
check job installs no YAML library, and comments are dropped first so prose
about `ubuntu-latest` (this ticket's own notes) is not mistaken for a setting.

    tools/check_runner_images.py --gate       the check check.sh runs
    tools/check_runner_images.py --self-test  the assertions still fire when broken
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
WORKFLOWS = REPO / ".github" / "workflows"

# What counts as installing Playwright: the CLI's `install` / `install-deps`,
# reached through npx, the global cli.js, or the bare binary.
INSTALLS = re.compile(r"playwright(?:/cli\.js\"?|@[\w.\-]+)?\s+install(?:-deps)?\b")
# What counts as running Blender: the pin every Blender job sources, or the bake itself.
# Invocations only: a path filter or a PR body that names bake.sh runs nothing.
BLENDER = re.compile(r"\bsource\s+\S*generators/blender\.pin\b"
                     r"|(?:^|[\s;&|(])(?:\./)?tools/bake\.sh(?=\s|$)", re.M)
RUNS_ON = re.compile(r"^\s{4}runs-on:\s*(.+?)\s*$")


def _strip_comments(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        out.append(line)
    return out


def jobs(text: str) -> dict[str, list[str]]:
    """The workflow's jobs, each as its own (comment-free) lines."""
    found: dict[str, list[str]] = {}
    inside = False
    current = None
    for line in _strip_comments(text):
        if re.match(r"^jobs:\s*$", line):
            inside = True
            continue
        if inside and re.match(r"^\S", line):
            inside = False
            current = None
        if not inside:
            continue
        m = re.match(r"^  ([A-Za-z0-9_\-]+):\s*$", line)
        if m:
            current = m.group(1)
            found[current] = []
            continue
        if current is not None:
            found[current].append(line)
    return found


def violations(name: str, text: str) -> list[str]:
    bad = []
    for job, lines in jobs(text).items():
        body = "\n".join(lines)
        what = [w for w, rx in (("installs Playwright", INSTALLS), ("runs Blender", BLENDER))
                if rx.search(body)]
        if not what:
            continue
        does = " and ".join(what)
        images = [m.group(1).strip("'\"") for l in lines if (m := RUNS_ON.match(l))]
        if not images:
            bad.append(f"{name} § {job}: {does} and names no `runs-on`")
        for image in images:
            if image.endswith("-latest") or "${{" in image:
                bad.append(f"{name} § {job}: {does} on `{image}`, a label "
                           f"that moves under it — pin an exact image (ubuntu-24.04 or -26.04)")
    return bad


def gate() -> int:
    files = sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))
    if not files:
        print(f"FAIL: no workflows found under {WORKFLOWS}")
        return 1
    bad, checked = [], 0
    for f in files:
        text = f.read_text()
        checked += sum(1 for body in jobs(text).values()
                       if INSTALLS.search("\n".join(body)) or BLENDER.search("\n".join(body)))
        bad += violations(f.name, text)
    if checked == 0:
        print("FAIL: no job installs Playwright or runs Blender, so this gate reads nothing — "
              "the pattern has stopped matching the workflows")
        return 1
    for b in bad:
        print(f"FAIL: {b}")
    if bad:
        return 1
    print(f"ok: {checked} Playwright-installing or Blender-running job(s) across {len(files)} workflow(s), "
          f"every one on a pinned image")
    return 0


def self_test() -> int:
    pinned = ("on: push\njobs:\n  smoke:\n    runs-on: ubuntu-24.04\n    steps:\n"
              "      - run: |\n          npm install -g playwright@1.56.1\n"
              "          node \"$(npm root -g)/playwright/cli.js\" install --with-deps chromium\n")
    cases = [
        ("a pinned job passes", pinned, 0),
        ("the same job on ubuntu-latest is refused",
         pinned.replace("ubuntu-24.04", "ubuntu-latest"), 1),
        ("a quoted latest label is refused",
         pinned.replace("ubuntu-24.04", "'ubuntu-latest'"), 1),
        ("an expression image is refused (it can resolve to a moving label)",
         pinned.replace("ubuntu-24.04", "${{ matrix.os }}"), 1),
        ("npx install-deps counts as installing",
         "jobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n"
         "      - run: npx --no-install playwright install-deps chromium\n", 1),
        ("a job that installs nothing may float",
         "jobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hi\n", 0),
        ("a comment naming ubuntu-latest is prose, not a setting",
         pinned.replace("    runs-on:", "    # was runs-on: ubuntu-latest\n    runs-on:"), 0),
        ("the install is attributed to its own job, not a neighbour",
         "jobs:\n  float:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hi\n"
         + pinned.split("jobs:\n", 1)[1], 0),
        ("…and a floating job after a pinned one is still caught",
         pinned + "  other:\n    runs-on: ubuntu-latest\n    steps:\n"
         "      - run: npx playwright install chromium\n", 1),
        ("a bake on ubuntu-latest is refused (T-3296)",
         "jobs:\n  bake:\n    runs-on: ubuntu-latest\n    steps:\n"
         "      - run: ./tools/bake.sh\n", 1),
        ("…and the same bake pinned passes",
         "jobs:\n  bake:\n    runs-on: ubuntu-26.04\n    steps:\n"
         "      - run: ./tools/bake.sh\n", 0),
        ("sourcing the Blender pin counts as running Blender",
         "jobs:\n  s:\n    runs-on: ubuntu-latest\n    steps:\n"
         "      - run: source chicago/4d/generators/blender.pin\n", 1),
        ("a bake.sh run after a cd, with arguments, counts",
         "jobs:\n  b:\n    runs-on: ubuntu-latest\n    steps:\n"
         "      - run: cd chicago/4d && tools/bake.sh --only x\n", 1),
        ("a PR body quoting `tools/bake.sh` is prose, not a bake",
         "jobs:\n  o:\n    runs-on: ubuntu-latest\n    steps:\n"
         "      - run: gh pr create --body \"Automated bake from \\`tools/bake.sh\\`.\"\n", 0),
        ("a path filter naming bake.sh is not a job running it",
         "on:\n  push:\n    paths:\n      - 'chicago/4d/tools/bake.sh'\n"
         "jobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hi\n", 0),
    ]
    failed = 0
    for label, text, want in cases:
        got = 1 if violations("t.yml", text) else 0
        ok = got == want
        failed += not ok
        print(f"{'ok' if ok else 'FAIL'}: {label}")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gate", action="store_true", help="the check check.sh runs")
    ap.add_argument("--self-test", action="store_true", help="the assertions still fire")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return gate()


if __name__ == "__main__":
    sys.exit(main())
