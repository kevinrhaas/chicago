#!/usr/bin/env python3
"""The reference browsers' heavy assets, shipped once rather than twice — T-1828.

publish.sh copies two reference browsers into the 4D mirror so the dev preview
carries them: the Prairie Avenue 1904 atlas (prairie-1904/) and the pre-fire
atlas (pre-fire/). The site root ALREADY publishes the production copy of each,
at chicago.polecat.live/prairie-1904/ and /pre-fire/, from the tracked
site/prairie-1904/ and site/pre-fire/. So every map sheet, HABS drawing and photo
the two had in common went out twice, and on 2026-10-01 that was 91.7 MB of a
287 MB mirror — the tree T-1821's image collection pushed 31 MB over its 256 MB
budget, which turned dev's gate red and with it every PR waiting to merge.

This is T-0722's rule ("the same bytes, shipped twice") carried across the one
boundary `site_budget.py --dupes` cannot see, because it only walks site/4d/.

THE RULE, PER FILE (T-2483). For each asset directory below, every file the
mirror holds that is byte-identical to the file at the same path in the site
root's production copy is removed, and the viewer reads it from the root
instead. A file that differs, or is missing at the root, STAYS in the mirror and
is listed in `keep`, so new work the production copy does not have yet still
ships in the preview, and moves out by itself the day the production copy is
refreshed to hold it. ALWAYS_ROOT names the exception: the Prairie image
collection never ships here (owner, 2026-10-02), whatever the root holds.

Until T-2483 the rule was per DIRECTORY: one file the root lacked kept the whole
directory. On 2026-10-13 #783 added one 65 KB photograph (and its thumbnail) to
prairie-1904's research/public/, the root copy did not have it, and all 39.3 MB
of that directory went back into the mirror — 279.2 MB of a 256 MB budget, and
dev's gate red for every PR behind it. Per file, the same addition costs 90 KB.

THE VIEWER SIDE. Each viewer loads viewer/root-served.js, which the source
commits as `self.ROOT_SERVED = null` (everything package-relative). This tool
overwrites the MIRROR's copy with the directories it thinned, the root path they
now live under, and the files under them it kept (`keep`, package-relative paths);
the viewers' path resolvers send a path under a listed directory to the root
unless `keep` names it.

THE COST, stated rather than hidden: the root is deployed from main, so the
/4d/dev/ preview shows main's bytes for a file identical to main's — which is no
cost at all, since they are the same bytes. A file changed or added on dev is
kept and previewed from the mirror.

    python3 tools/serve_from_root.py <site/4d> <site>   # publish.sh runs this
    python3 tools/serve_from_root.py --self-test
"""
from __future__ import annotations

import filecmp
import json
import shutil
import sys
import tempfile
from pathlib import Path

# App -> its asset directories, named rather than globbed: viewer/, data/ and
# docs/ are what the preview is FOR, and stay in the mirror whatever they hold.
ASSET_DIRS = {
    "prairie-1904": ["maps", "research/public", "research/images/files"],
    "pre-fire": ["maps/images", "media"],
}

# Directories that NEVER ship in the mirror, identical at the root or not (owner,
# 2026-10-02: "we want to download as many images as possible"). The Prairie image
# collection's home is the production copy deploy.yml publishes at /prairie-1904/, under
# its own budget in chicago/prairie_1904_v1/tools/validate.py, so it does not grow this
# tree's 256 MB. The cost, stated: a dev-only image is not at the root until promotion,
# and the viewer shows it from its holder's URL until then (images.js fallbackURL).
ALWAYS_ROOT = {
    "prairie-1904": ["research/images/files"],
}


def split_at_root(mirror_dir: Path, root_dir: Path) -> tuple[list[Path], list[Path]]:
    """The mirror's files under mirror_dir: (identical at the root, not)."""
    same, kept = [], []
    for p in sorted(p for p in mirror_dir.rglob("*") if p.is_file()):
        twin = root_dir / p.relative_to(mirror_dir)
        (same if twin.is_file() and filecmp.cmp(p, twin, shallow=False) else kept).append(p)
    return same, kept


def serve_from_root(mirror: Path, site: Path, out=sys.stdout) -> int:
    """Prune the shared files; return the bytes the mirror no longer ships."""
    saved = 0
    for app, dirs in ASSET_DIRS.items():
        viewer = mirror / app / "viewer"
        if not viewer.is_dir():
            continue
        moved, keep = [], []
        for d in dirs:
            mine, root = mirror / app / d, site / app / d
            if not mine.is_dir():
                continue
            if d in ALWAYS_ROOT.get(app, []):
                size = sum(p.stat().st_size for p in mine.rglob("*") if p.is_file())
                shutil.rmtree(mine)
                saved += size
                moved.append(d + "/")
                print(f"   {app}/{d}/  {size / 1048576:.2f} MB served from /{app}/{d}/"
                      " (always: its home is the root)", file=out)
                continue
            same, kept = split_at_root(mine, root)
            if not same:
                print(f"   {app}/{d}/  kept — none of it is at /{app}/{d}/ yet", file=out)
                continue
            size = sum(p.stat().st_size for p in same)
            for p in same:
                p.unlink()
            for sub in sorted((q for q in mine.rglob("*") if q.is_dir()), reverse=True):
                if not any(sub.iterdir()):
                    sub.rmdir()
            saved += size
            moved.append(d + "/")
            keep += [f"{d}/{p.relative_to(mine).as_posix()}" for p in kept]
            print(f"   {app}/{d}/  {size / 1048576:.2f} MB served from /{app}/{d}/"
                  + (f", {len(kept)} file(s) not at the root kept here" if kept else ""), file=out)
        spec = {"base": f"/{app}/", "dirs": moved, "keep": keep} if moved else None
        (viewer / "root-served.js").write_text(
            "// Written by chicago/4d/tools/serve_from_root.py (T-1828): asset directories this\n"
            "// copy reads from the site root's production copy instead of its own package.\n"
            f"self.ROOT_SERVED = {json.dumps(spec)};\n")
    return saved


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        mirror, site = t / "site" / "4d", t / "site"

        def put(path: Path, text: str):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

        for base in (mirror, site):  # identical everywhere: moves
            put(base / "prairie-1904/research/public/a.jpg", "A")
            put(base / "prairie-1904/maps/originals/m.jpg", "M")
        put(mirror / "prairie-1904/viewer/root-served.js", "self.ROOT_SERVED = null;\n")
        put(mirror / "prairie-1904/research/images/files/new.jpg", "N")   # not at root, but ALWAYS_ROOT: leaves
        put(mirror / "pre-fire/maps/images/new.jpg", "N")                 # not at root: stays
        put(mirror / "pre-fire/viewer/root-served.js", "self.ROOT_SERVED = null;\n")
        put(mirror / "pre-fire/media/x.jpg", "dev")                       # differs from the root: stays
        put(site / "pre-fire/media/x.jpg", "main")
        put(mirror / "prairie-1904/research/public/new.jpg", "NEW")       # T-2483: one new file beside identical ones
        saved = serve_from_root(mirror, site, out=open("/dev/null", "w"))
        prairie = (mirror / "prairie-1904/viewer/root-served.js").read_text()
        checks = [
            (saved == 3, "the identical files' bytes, and the always-root directory's, are counted as saved"),
            (not (mirror / "prairie-1904/research/public/a.jpg").exists(), "a file identical at the root leaves the mirror"),
            ((mirror / "prairie-1904/research/public/new.jpg").read_text() == "NEW",
             "a new file beside identical ones stays, and does not keep its directory's other files (T-2483)"),
            ((mirror / "pre-fire/maps/images/new.jpg").exists(), "a directory the root lacks entirely stays"),
            (not (mirror / "prairie-1904/research/images/files").exists(), "an ALWAYS_ROOT directory leaves even when the root lacks it"),
            (not (mirror / "prairie-1904/maps/originals").exists(), "a subdirectory the move empties is removed"),
            ((mirror / "pre-fire/media/x.jpg").read_text() == "dev", "a file that differs from the root's stays"),
            ('"dirs": ["maps/", "research/public/", "research/images/files/"]' in prairie and '"base": "/prairie-1904/"' in prairie,
             "the viewer is told what moved and where"),
            ('"keep": ["research/public/new.jpg"]' in prairie, "the viewer is told which files under a moved directory stayed"),
            ("self.ROOT_SERVED = null;" in (mirror / "pre-fire/viewer/root-served.js").read_text(),
             "a viewer with nothing moved stays package-relative"),
        ]
    bad = [name for ok, name in checks if not ok]
    for ok, name in checks:
        print(("  ok    " if ok else "  FAIL  ") + name)
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv[1:] == ["--self-test"]:
        return self_test()
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    saved = serve_from_root(Path(argv[1]), Path(argv[2]))
    print(f"   reference browsers: {saved / 1048576:.2f} MB not shipped twice (T-1828)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
