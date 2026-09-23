#!/usr/bin/env python3
"""`restamp_inputs.py` refuses on a tree whose schemes already agree.

WHY THIS EXISTS (T-0164). `tools/restamp_inputs.py` rewrites the freshness
record — the only thing standing between a committed GLB and the claim that it
still matches the data it was built from. Used at the wrong moment it would bless
a mesh that really is out of date, and the bless would be silent and permanent.

One guard stops that, and it is the one worth a standing test: the tool refuses
unless a SCHEME constant has moved, because a scheme only moves in the commit
that changes what the recipe hashes. On a committed tree the schemes agree by
construction, so the committed tree IS the negative fixture, and it costs
milliseconds to assert against.

The positive path is not tested here and deliberately so: exercising it means
writing a real manifest, and a test that rewrites the freshness record to prove
it can is the failure mode rather than the proof. The positive path is
demonstrated in the commit that needs it, against `validate.py --all`.
"""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import restamp_inputs  # noqa: E402

failures = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global failures
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail and not ok else ""))
    if not ok:
        failures += 1


print("restamp_inputs — the guard that keeps it from blessing a stale mesh")

buf = io.StringIO()
raised = None
try:
    with redirect_stdout(buf):
        restamp_inputs.main(["--reason", "a test that must not be allowed to write"])
except SystemExit as e:  # RestampRefused is a SystemExit subclass
    raised = e

check("it refuses when no scheme has moved", raised is not None,
      "it returned normally on the committed tree, so the guard is not holding")
msg = str(raised) if raised else ""
check("and the refusal says why, naming the bake as the answer",
      "REFUSED" in msg and "no scheme has moved" in msg and "bake.sh" in msg, msg[:200])

# --write must be equally refused: the guard runs before the flag is honoured.
raised = None
try:
    with redirect_stdout(buf):
        restamp_inputs.main(["--reason", "likewise", "--write"])
except SystemExit as e:
    raised = e
check("--write is refused by the same guard, not merely the dry run",
      raised is not None and "no scheme has moved" in str(raised), str(raised)[:200])

print("restamp_inputs OK" if not failures
      else f"restamp_inputs FAILED — {failures} assertion(s)")
sys.exit(1 if failures else 0)
