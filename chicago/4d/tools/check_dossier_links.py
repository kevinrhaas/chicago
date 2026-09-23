#!/usr/bin/env python3
"""Every dossier link a card offers must resolve — ROADMAP K26.

The fault this exists to catch survived for months because it could only be seen
from outside the repository. `popup.js` linked `docBase + s.research_doc`, a path
relative to the walkthrough, so in the source tree the link worked; on the
deployed site `tools/publish.sh` leaves `docs/` out of the payload by design, and
every one of the 332 cards linked to a 404. "A link nobody clicks in the dev tree
is exactly how this survived."

So the gate asserts the two halves of the link separately, and structurally —
nothing here touches the network, because a gate that needs the network is a gate
that gets skipped:

1. **the path half** — every non-empty `research_doc` in every committed sidecar
   resolves to a file in this repository. The compiler emits `""` where no
   dossier has been written, so this is an absolute assertion rather than a
   ratchet: a card either links to something that exists or does not link.
2. **the base half** — the renderer's `DOSSIER_BASE` is an absolute GitHub blob
   URL whose path ends in this app's own location inside the repository. That is
   what makes the composed URL resolvable, and it is the part that goes wrong
   silently if the app is ever moved.

It also prints the census of records with no dossier written. Those are a
research debt rather than a link fault, and naming them each run is what keeps
the debt from reading as "nothing to see".

    tools/check_dossier_links.py            the gate
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POPUP = ROOT / "renderers/web/js/popup.js"
MAIN = ROOT / "renderers/web/js/main.js"

# Where this app sits inside its repository. The published URL is composed of the
# blob base plus a path relative to here, so the two have to agree; a monorepo
# subtree that moves without this moving is a link that 404s for everyone.
APP_PREFIX = "chicago/4d/"

BASE_RE = re.compile(r"export const DOSSIER_BASE\s*=\s*'([^']+)'")
BLOB_RE = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/blob/[\w.\-/]+/$")


def sidecars() -> list[tuple[str, Path, dict]]:
    out = []
    for scene_dir in sorted((ROOT / "data/sidecars").glob("*")):
        if not scene_dir.is_dir():
            continue
        for f in sorted(scene_dir.glob("*.json")):
            if f.name == "index.json":
                continue
            doc = json.loads(f.read_text())
            if "research_doc" in doc:
                out.append((scene_dir.name, f, doc))
    return out


def main() -> int:
    failures: list[str] = []

    records = sidecars()
    linked = [(s, f, d) for s, f, d in records if d["research_doc"]]
    unwritten = [(s, f) for s, f, d in records if not d["research_doc"]]

    # 1. the path half
    for scene, f, doc in linked:
        target = ROOT / doc["research_doc"]
        if not target.is_file():
            failures.append(
                f"{scene}/{f.stem} links {doc['research_doc']}, which is not a file "
                f"in this repository — the card would offer a 404")

    # 2. the base half
    src = POPUP.read_text()
    m = BASE_RE.search(src)
    if not m:
        failures.append(
            f"{POPUP.relative_to(ROOT)} exports no DOSSIER_BASE — the card is composing "
            f"its dossier link some other way, and this gate cannot see it")
    else:
        base = m.group(1)
        if not BLOB_RE.match(base):
            failures.append(
                f"DOSSIER_BASE is {base!r}, which is not an absolute GitHub blob URL "
                f"ending in '/' — a relative base resolves only in the source tree, "
                f"which is the fault K26 fixed")
        elif not base.endswith(APP_PREFIX):
            failures.append(
                f"DOSSIER_BASE is {base!r} but this app lives at {APP_PREFIX!r} in its "
                f"repository — the composed URL would miss the dossier")
        else:
            print(f"   base: {base}")

    # The link is only absolute if nothing hands the card a relative base back.
    if re.search(r"createPopup\([^)]*docBase\s*:\s*['\"]\.", MAIN.read_text()):
        failures.append(
            f"{MAIN.relative_to(ROOT)} overrides docBase with a relative path — that is "
            f"the pre-K26 behaviour and it 404s everywhere a visitor stands")

    print(f"   {len(linked)} card(s) link a dossier, all resolving; "
          f"{len(unwritten)} link none")

    if unwritten:
        # Not a failure: a documented building whose write-up nobody has done yet
        # is research debt (ROADMAP K26), and the card now says so instead of
        # offering a link that breaks. Named every run so it stays visible.
        print(f"   no dossier written for {len(unwritten)} record(s):")
        for scene, f in unwritten:
            print(f"     {scene}/{f.stem}")

    for msg in failures:
        print(f"   {msg}")
    if failures:
        print(f"   FAIL: {len(failures)} dossier link fault(s)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
