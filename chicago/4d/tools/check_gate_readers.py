#!/usr/bin/env python3
"""T-1083 — the gate's own install set, asserted instead of assumed.

Thirteen of the steps `tools/check.sh` runs re-read a committed raster, and each of
them degrades POLITELY when the image and array libraries are absent: it stands on a
banked reading, prints its skip, and exits 0. That is right for a tool a person runs
in a sandbox. It is wrong for a GATE, which then counts the skip as a pass.

It was not hypothetical. `.github/workflows/chicago-4d-check.yml` installed
`jsonschema pyproj openpyxl pypdf` and nothing else, so the dev gate had never once
re-read a sheet. Measured on dev at 33638aa69, running check.sh twice on the same
tree — once with the CI set, once with numpy/scipy/Pillow added — TWO steps changed
behaviour and one of them went red:

    FAIL sauganash_range_m moved from 1066.3 to 1001.2 (tolerance 1.0)

65.1 m of drift against a 1.0 m tolerance, green in CI since T-1065 (#1189) moved
the lighthouse onto Wright's own glyph.

So the workflow now installs the readers, and this asserts that it did. Two states,
deliberately different:

  * `C4D_GATE_REQUIRE_READERS=1` (the workflow sets it) — a missing reader is RED.
    The gate may not degrade. Ever.
  * unset (an agent sandbox, a laptop) — a missing reader is a WARNING that names
    every step now standing on a banked reading, and the gate goes on.

A step that starts re-reading a raster adds itself to READERS below. That is the
whole maintenance burden, and it is the point: the list is what CI installs.
"""
import argparse
import importlib
import os
import pathlib
import sys

# library -> (pip name, the check.sh steps that stop re-reading without it)
READERS = {
    "PIL": ("Pillow", [
        "the fort's stockade is still pointed",
        "p4_0 raises no work at either angle of the fort it draws",
        "the ways the fort plates draw are still the ways the town was built to",
        "Braunhold's Sauganash still says what the research note says it says",
        "the Chappel shore drawing still refuses to place its own station",
        "the four crops are still the panels their citations name",
        # Registered 2026-09-13, and it is the one that was NOT here — which is
        # exactly why it crashed instead of standing on its banked reading. See
        # read_kinzie_addition_water_lots.py § check_sheet.
        "…and the strip still reads the same off the sheet",
    ]),
    "numpy": ("numpy", [
        "…every step PIL names above — each needs both",
        "the traced forks still carry what their generator writes",
        "the traced North Branch still carries what its generator writes",
        "the traced South Branch still carries what its generator writes",
        "the North Branch's repaired east bank has not leaked the west one",
    ]),
    "scipy": ("scipy", [
        "the traced forks still carry what their generator writes",
        "the traced North Branch still carries what its generator writes",
        "the traced South Branch still carries what its generator writes",
        "the North Branch's repaired east bank has not leaked the west one",
    ]),
}


def missing():
    out = []
    for mod in READERS:
        try:
            importlib.import_module(mod)
        except Exception:
            out.append(mod)
    return out


def report(absent, required):
    if not absent:
        print("   ok    every raster reader the gate's steps need is installed: "
              + ", ".join(f"{m} ({READERS[m][0]})" for m in READERS))
        return 0
    for m in absent:
        pip_name, steps = READERS[m]
        print(f"   {'FAIL ' if required else 'WARN '} {m} ({pip_name}) is not installed, "
              f"so {len(steps)} step(s) below stand on a banked reading:")
        for s in steps:
            print(f"            · {s}")
    print("   " + ("FAIL  a GATE may not count a skip as a pass — "
                   f"pip install {' '.join(READERS[m][0] for m in absent)}"
                   if required else
                   "WARN  this is a sandbox, so the gate goes on. CI sets "
                   "C4D_GATE_REQUIRE_READERS=1 and would be red here."))
    return 1 if required else 0


def self_test():
    """prove the assertion fires — the check.sh convention (T-0763)."""
    ok = True
    if report([], True) != 0:
        print("   FAIL self-test a full install set was called a failure")
        ok = False
    print("   fires: a missing reader, with C4D_GATE_REQUIRE_READERS set")
    if report(["numpy"], True) != 1:
        print("   FAIL self-test a missing reader did not fail the required gate")
        ok = False
    print("   passes: the same absence in a sandbox, as a warning")
    if report(["numpy"], False) != 0:
        print("   FAIL self-test a sandbox warning was turned into a failure")
        ok = False
    if not set(READERS) <= {"PIL", "numpy", "scipy"}:
        print("   FAIL self-test READERS names a library this test has not thought about")
        ok = False
    # The enumeration is only worth printing if it is still TRUE of check.sh. A step
    # that gets renamed and not renamed here would name a gate that no longer exists.
    src = (pathlib.Path(__file__).parent / "check.sh").read_text(encoding="utf-8")
    for lib, (_, steps) in READERS.items():
        for st in steps:
            if st.startswith("\u2026"):
                continue
            if f'step "{st}"' not in src:
                print(f"   FAIL self-test {lib} names a step check.sh does not run: {st}")
                ok = False
    print("   ok: every step named above is a step check.sh actually runs")
    print("   self-test: the reader assertion fires when required and warns when not"
          if ok else "   self-test: FAILED")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return report(missing(), bool(os.environ.get("C4D_GATE_REQUIRE_READERS")))


if __name__ == "__main__":
    sys.exit(main())
