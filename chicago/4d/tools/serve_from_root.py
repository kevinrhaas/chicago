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

THE RULE. For each asset directory below, if EVERY file the mirror holds under it
is byte-identical to the file at the same path in the site root's production
copy, the mirror's copy is removed and the viewer reads that directory from the
root instead. One file that differs, or is missing at the root, keeps the whole
directory in the mirror — so new work the production copy does not have yet
(T-1821's images, today) still ships in the preview, and moves out by itself
the day the production copy is refreshed to hold it.

THE VIEWER SIDE. Each viewer loads viewer/root-served.js, which the source
commits as `self.ROOT_SERVED = null` (everything package-relative). This tool
overwrites the MIRROR's copy with the directories it removed and the root path
they now live under, and the viewers' path resolvers read it.

THE COST, stated rather than hidden: the root is deployed from main, so the
/4d/dev/ preview shows main's bytes for a moved directory. A file changed on dev
but not yet promoted is previewed at its production version (or 404s, if it is
new and its directory was otherwise identical) until the next promotion.

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


def identical_at_root(mirror_dir: Path, root_dir: Path) -> bool:
    files = [p for p in mirror_dir.rglob("*") if p.is_file()]
    if not files:
        return False
    for p in files:
        twin = root_dir / p.relative_to(mirror_dir)
        if not twin.is_file() or not filecmp.cmp(p, twin, shallow=False):
            return False
    return True


def serve_from_root(mirror: Path, site: Path, out=sys.stdout) -> int:
    """Prune the shared directories; return the bytes the mirror no longer ships."""
    saved = 0
    for app, dirs in ASSET_DIRS.items():
        viewer = mirror / app / "viewer"
        if not viewer.is_dir():
            continue
        moved = []
        for d in dirs:
            mine, root = mirror / app / d, site / app / d
            if mine.is_dir() and identical_at_root(mine, root):
                size = sum(p.stat().st_size for p in mine.rglob("*") if p.is_file())
                shutil.rmtree(mine)
                saved += size
                moved.append(d + "/")
                print(f"   {app}/{d}/  {size / 1048576:.2f} MB served from /{app}/{d}/", file=out)
            elif mine.is_dir():
                print(f"   {app}/{d}/  kept — not all of it is at /{app}/{d}/ yet", file=out)
        spec = {"base": f"/{app}/", "dirs": moved} if moved else None
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
        put(mirror / "prairie-1904/research/images/files/new.jpg", "N")   # not at root: stays
        put(mirror / "pre-fire/viewer/root-served.js", "self.ROOT_SERVED = null;\n")
        put(mirror / "pre-fire/media/x.jpg", "dev")                       # differs: stays
        put(site / "pre-fire/media/x.jpg", "main")
        saved = serve_from_root(mirror, site, out=open("/dev/null", "w"))
        prairie = (mirror / "prairie-1904/viewer/root-served.js").read_text()
        checks = [
            (saved == 2, "the two identical directories' bytes are counted as saved"),
            (not (mirror / "prairie-1904/research/public").exists(), "an identical directory leaves the mirror"),
            ((mirror / "prairie-1904/research/images/files/new.jpg").exists(), "a directory the root lacks stays"),
            ((mirror / "pre-fire/media/x.jpg").read_text() == "dev", "a directory with one differing file stays whole"),
            ('"dirs": ["maps/", "research/public/"]' in prairie and '"base": "/prairie-1904/"' in prairie,
             "the viewer is told what moved and where"),
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
