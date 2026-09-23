#!/usr/bin/env python3
"""Where the published tree's bytes actually are — T-0722.

`tools/validate.py` has carried a 32 MB budget over `site/chicago/4d/` since the
mirror existed, and it prints one number: the total. On 2026-09-05 that number
reached 31.999 MB on `dev` alone, which made every open PR unmergeable — a
changelog entry is a few KB and a few KB was all that remained. T-0722 was filed
by the PR that hit it, and its first ask was the one nothing here had ever
answered:

    "Say where the 32 MB actually is. A report over site/chicago/4d/ by directory
     and by file type — GLBs against JSON against textures — so the decision is
     made on numbers. It has never been printed."

This prints it, and it prints one thing more, because a total cannot tell you the
difference between a byte that IS the record and a byte that is a COPY of one:
every group of files in the mirror with identical content. That check is what
found the 1.34 MB the mirror was spending to ship the changelog twice.

    python3 tools/site_budget.py            # the report
    python3 tools/site_budget.py --dupes    # only the duplicate groups

The report is a measurement, not a gate. The gate stays in validate.py, which is
the one place a merge is refused from; `run_site_check` there now warns at 90 % of
budget so a PR is told before it is stopped, and refuses a duplicate group over
64 KB so this particular waste cannot come back silently.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT.parent.parent / "site" / "chicago" / "4d"
# THE BUDGET IS READ FROM THE GATE, NOT RESTATED HERE. This tool hardcoded 32.0
# while tools/validate.py had been raised to 36 (T-0593, #823), so the report said
# "95.0 % of the 32 MB budget, 1.588 MB of headroom" about a tree the gate saw as
# 30.4 of 36 with 5.59 MB spare — and a 2026-09-05 ticket cleanup quoted the wrong
# figure out of it. A reporting tool that names a different number than the gate it
# reports on is worse than no report.
def _gate_budget_mb(default: float = 36.0) -> float:
    try:
        src = (ROOT / "tools" / "validate.py").read_text()
        m = re.search(r"^SITE_BUDGET_MB\s*=\s*([0-9.]+)", src, re.M)
        if m:
            return float(m.group(1))
    except OSError:
        pass
    return default


BUDGET_MB = _gate_budget_mb()
DUPE_FLOOR = 64 * 1024  # a group smaller than this is not worth a word


def walk(site: Path) -> list[Path]:
    return sorted(p for p in site.rglob("*") if p.is_file())


def mb(n: int) -> str:
    return f"{n / 1048576:7.3f} MB"


def by_group(files: list[Path], key) -> list[tuple[str, int, int]]:
    size: dict[str, int] = defaultdict(int)
    count: dict[str, int] = defaultdict(int)
    for p in files:
        k = key(p)
        size[k] += p.stat().st_size
        count[k] += 1
    return sorted(((k, size[k], count[k]) for k in size), key=lambda r: -r[1])


def dir_key(site: Path, p: Path) -> str:
    rel = p.relative_to(site).parts
    return "/".join(rel[:2]) if len(rel) > 2 else ("/".join(rel[:-1]) or "(root)")


def duplicate_groups(files: list[Path], floor: int = DUPE_FLOOR):
    """Files whose CONTENT is byte-identical, grouped, largest wasted first.

    Waste is (n - 1) x size: one copy is the file, the rest are the cost.
    """
    by_hash: dict[str, list[Path]] = defaultdict(list)
    for p in files:
        if p.stat().st_size < floor:
            continue
        by_hash[hashlib.sha256(p.read_bytes()).hexdigest()].append(p)
    groups = []
    for paths in by_hash.values():
        if len(paths) > 1:
            size = paths[0].stat().st_size
            groups.append((size * (len(paths) - 1), size, sorted(paths)))
    return sorted(groups, key=lambda g: -g[0])


def report(site: Path, out=sys.stdout) -> int:
    files = walk(site)
    total = sum(p.stat().st_size for p in files)
    budget = int(BUDGET_MB * 1048576)

    # Repo-relative: this report is committed to docs/SITE-BUDGET.md, and an
    # absolute path there is a fact about one runner rather than about the tree.
    print(f"PUBLISHED TREE  {site.relative_to(ROOT.parent.parent)}", file=out)
    print(f"  {mb(total)} in {len(files)} files "
          f"— {100 * total / budget:.1f} % of the {BUDGET_MB:.0f} MB budget, "
          f"{mb(budget - total)} of headroom\n", file=out)

    print("BY DIRECTORY (two levels)", file=out)
    for k, s, c in by_group(files, lambda p: dir_key(site, p)):
        print(f"  {mb(s)}  {c:5d}  {k}", file=out)

    print("\nBY FILE TYPE", file=out)
    for k, s, c in by_group(files, lambda p: p.suffix.lower() or "(none)"):
        print(f"  {mb(s)}  {c:5d}  {k}", file=out)

    print("\nTHE 20 LARGEST FILES", file=out)
    for p in sorted(files, key=lambda p: -p.stat().st_size)[:20]:
        print(f"  {mb(p.stat().st_size)}  {p.relative_to(site)}", file=out)

    groups = duplicate_groups(files)
    print(f"\nIDENTICAL CONTENT, SHIPPED MORE THAN ONCE "
          f"(groups over {DUPE_FLOOR // 1024} KB)", file=out)
    if not groups:
        print("  none — every file over the floor is the only copy of itself", file=out)
    for wasted, size, paths in groups:
        print(f"  {mb(wasted)} wasted — {len(paths)} x {mb(size)}", file=out)
        for p in paths:
            print(f"      {p.relative_to(site)}", file=out)
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dupes", action="store_true",
                    help="print only the identical-content groups")
    args = ap.parse_args()

    if not SITE.exists():
        print("nothing published yet — run tools/publish.sh", file=sys.stderr)
        return 1
    if args.dupes:
        for wasted, size, paths in duplicate_groups(walk(SITE)):
            print(f"{mb(wasted)} wasted — {len(paths)} x {mb(size)}")
            for p in paths:
                print(f"    {p.relative_to(SITE)}")
        return 0
    report(SITE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
