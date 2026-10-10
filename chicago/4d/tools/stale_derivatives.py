#!/usr/bin/env python3
"""Which masters does a whole-town bake actually have to derive? (T-2314)

    python3 tools/stale_derivatives.py              # comma list, possibly empty
    python3 tools/stale_derivatives.py --self-test

`tools/bake.sh` with no `--only` regenerates every master and then handed all of them
to `tools/web_derivatives.sh` — 714 on 2026-10-10, two npx start-ups each, about twenty
minutes. The content-build job's ceiling is thirty, the embedded gate after it takes
ten, and the checkout takes three and a half, so from about 07:00 that day every
PR-branch bake was cancelled at its ceiling with the gate half read: #631, #639, #643
and #646 each sat in `resume` behind a check that could no longer finish.

Nothing is lost by deriving fewer. T-1653 already skips untouched masters on an
`--only` bake, on T-0776's measurement that all 570 derivatives reproduce byte for
byte from an unchanged master, and K39's record (`assets/manifest.web.json`) is the
gate's own answer to "was this derivative made from the master in the tree?". This
asks it the same question one step earlier. A master is printed when

  * the record has no entry for it, or
  * the record's sha256 is not the sha256 of the master in the tree today, or
  * its derivative is missing from assets/web/,

and every version master (`assets/gltf/versions/*/*/*.glb`) is printed always: their
freshness lives in `tools/structure_versions.py`'s receipts, not in this record, and
there are four of them, so a whole-town bake derives them exactly as it always did.

What this CANNOT see is a change to the recipe — `web_derivatives.sh`'s flags or its
pinned packages. K40 decided against recording a script hash (it would have
invalidated every entry twice on commits that moved no byte), so the rule stands as
that script's header states it: a change that moves any derivative's bytes runs
`tools/web_derivatives.sh` whole in its own commit. `BAKE_DERIVE_ALL=1 tools/bake.sh`
does the same inside a bake.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent


def stale(root: pathlib.Path) -> list[str]:
    gltf, web = root / "assets" / "gltf", root / "assets" / "web"
    record_path = root / "assets" / "manifest.web.json"
    recorded = {}
    if record_path.exists():
        recorded = json.loads(record_path.read_text(encoding="utf-8")).get("masters", {})
    out = []
    for master in sorted(gltf.glob("*.glb")):
        name = master.name
        was = recorded.get(name)
        if (was is None or not (web / name).exists()
                or was != hashlib.sha256(master.read_bytes()).hexdigest()):
            out.append(name)
    out += sorted(str(p.relative_to(gltf)) for p in gltf.glob("versions/*/*/*.glb"))
    return out


def self_test() -> int:
    failures = 0

    def check(label: str, got, want) -> None:
        nonlocal failures
        ok = got == want
        failures += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {label}" + ("" if ok else f": got {got!r}, want {want!r}"))

    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        gltf, web = root / "assets" / "gltf", root / "assets" / "web"
        (gltf / "versions" / "house" / "v4").mkdir(parents=True)
        web.mkdir(parents=True)
        masters = {"fresh.glb": b"a", "moved.glb": b"b", "unrecorded.glb": b"c", "underived.glb": b"d"}
        for name, body in masters.items():
            (gltf / name).write_bytes(body)
            if name != "underived.glb":
                (web / name).write_bytes(b"derived")
        record = {n: hashlib.sha256(b).hexdigest() for n, b in masters.items() if n != "unrecorded.glb"}
        record["moved.glb"] = hashlib.sha256(b"the old building").hexdigest()
        (root / "assets" / "manifest.web.json").write_text(json.dumps({"masters": record}))
        (gltf / "versions" / "house" / "v4" / "house__as_built.glb").write_bytes(b"v")

        got = stale(root)
        check("a master matching its record, with a derivative, is skipped", "fresh.glb" in got, False)
        check("a master whose bytes moved is derived", "moved.glb" in got, True)
        check("a master the record never saw is derived", "unrecorded.glb" in got, True)
        check("a master with no derivative is derived", "underived.glb" in got, True)
        check("a version master is always derived", "versions/house/v4/house__as_built.glb" in got, True)

        (root / "assets" / "manifest.web.json").unlink()
        check("no record at all derives every master", len(stale(root)), 5)
    print(f"stale_derivatives self-test: {'PASS' if not failures else f'{failures} FAIL'}")
    return 1 if failures else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        sys.exit(self_test())
    print(",".join(stale(ROOT)))
