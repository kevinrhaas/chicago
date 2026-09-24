"""Injected into every python gate step via PYTHONPATH, to record what it WRITES.

Python imports `sitecustomize` automatically at interpreter start-up, which is the
only injection point that reaches a subprocess the gate spawns without editing the
tool itself. The audit hook is the same mechanism T-1336 used to find the six
self-tests that were breaking live files: `open` events carry the mode, so a read
is distinguishable from a write without guessing from the path.

Writes are reported by PATH RELATIVE TO THE REPO and nothing outside it is recorded
— a tool writing its own tempdir is doing the right thing and must not read as a
finding, which is the distinction the whole measurement turns on.
"""
import atexit
import json
import os
import sys

_ROOT = os.environ.get("ISOLATION_ROOT")
_OUT = os.environ.get("ISOLATION_OUT")

if _ROOT and _OUT:
    _root = os.path.realpath(_ROOT)
    _hits = set()

    def _hook(event, args):
        if event != "open":
            return
        path, mode = args[0], args[1]
        # A mode with none of w/a/x/+ is a read. `open` also fires for directories
        # and for fds already open, where mode is None.
        if not mode or not any(c in str(mode) for c in "wax+"):
            return
        try:
            real = os.path.realpath(os.fsdecode(path))
        except Exception:
            return
        if not real.startswith(_root + os.sep):
            return                      # outside the tree: a tempdir, and correct
        rel = os.path.relpath(real, _root)
        if rel.split(os.sep)[0] == ".git":
            return
        _hits.add(rel)

    sys.addaudithook(_hook)

    @atexit.register
    def _flush():
        # A ROW IS WRITTEN EVEN WHEN NOTHING WAS, because "measured and clean" and
        # "never ran" are different answers and the coverage gate has to tell them
        # apart. Silence on a clean run would make an unmeasured step look proven.
        try:
            with open(_OUT, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"argv": sys.argv, "wrote": sorted(_hits)}) + "\n")
        except Exception:
            pass
