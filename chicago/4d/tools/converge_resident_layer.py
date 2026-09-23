#!/usr/bin/env python3
"""T-1398 — the rebuild order of the 1835 resident layer, made executable and gated.

THE PROBLEM THIS EXISTS FOR, in one sentence: the resident layer is a cycle, and the
order you rebuild it in is the whole difference between one pass and an oscillation.

`data/reconstruction/1835_town_model.json` is a COUNT OF THE LAYER. The reconstruction
programme's stages DRAW from that model. The stages write cards back into the layer the
model counts. So no ordering of these tools has every step's inputs already current, and
a run that rebuilds "the stale piece the check named" never converges — the check names
the stage that is stale, and the cycle runs through a stage it does not name. That was
measured three times in one evening while clearing #1497 and #1502 (T-1179's findings):

    attempt 1  the three stages, no model        5 gate steps red
    attempt 2  only the piece the check named    a 2-cycle, three passes running
    attempt 3  all four, in order                2 red — transients, attribute tiers

Until now the order lived in a ticket comment, as a list. A list is the wrong shape of
answer: the set is defined by WHAT READS THE LAYER, and the layer gains readers. So the
order is data — `data/reconstruction/1835_resident_layer_rebuild_order.json` — this tool
runs it and iterates to the fixed point, and `--check` holds the file honest.

    python3 tools/converge_resident_layer.py --plan    the order, and why each step is there
    python3 tools/converge_resident_layer.py --run     execute it, iterate to the fixed point
    python3 tools/converge_resident_layer.py --check   the gate (writes nothing)
    python3 tools/converge_resident_layer.py --self-test

WHAT `--check` ASSERTS. It does not re-derive anything: check.sh already runs each
step's own `--check`, and this would only double that cost. It asserts the four things
that make those checks ADD UP to a fixed point, none of which any single check can see:

  A. GATED — every step in the order names a `check` command that appears verbatim in
     `tools/check.sh`. A step the gate does not run can go stale in silence, and the
     order would then converge onto a tree nothing is holding.
  B. DECLARED HONESTLY — every path a step declares it reads or writes actually appears
     in that step's own source. A declaration nobody checks is a comment.
  C. THE CYCLE IS DECLARED — the back edges (a step reading a path a LATER step writes)
     are recomputed from the declarations and must match the file's `the_cycle.edges`
     exactly. An UNDECLARED back edge is the thing that costs three passes: it is a new
     reason one pass cannot converge, arriving unannounced.
  D. THE SET CANNOT GROW SILENTLY — every tool that check.sh gates, names the layer in
     its source, and carries BOTH a write mode and a `--check` is a gated re-derivation
     standing next to the layer. Each must be named in the order or in
     `not_in_the_order.names`. A tool that JOINS that set is red until a run says which.

D is a tripwire and not a classification, and the data file says so on its face: the
names sitting in `not_in_the_order` have been enumerated, not read one by one.

AND AFTERWARDS. A fixed point that `node tools/rederive.mjs --run` undoes is not a fixed
point (T-1363). Verify with `rederive.mjs --check` after this order, and read a `--run`
late in the procedure as a reason to start over.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ORDER = ROOT / "data" / "reconstruction" / "1835_resident_layer_rebuild_order.json"
CHECK_SH = ROOT / "tools" / "check.sh"
TOOLS = ROOT / "tools"

# Path components too generic to be evidence that a tool names a path (assertion B).
GENERIC = {"data", "docs", "chicago", "json", "md", "csv"}


def load(path=ORDER):
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- the order, run

def tool_of(step):
    """The tools/<name>.py a step drives, or None."""
    for word in step["build"]:
        m = re.fullmatch(r"tools/([a-z0-9_]+)\.py", word)
        if m:
            return m.group(1)
    return None


def run_order(order, max_passes=None):
    """Execute the order, then iterate the WHOLE order until every check is green."""
    limit = max_passes or order.get("max_passes", 4)
    for attempt in range(1, limit + 1):
        print(f"\n== pass {attempt} of at most {limit}")
        for step in order["steps"]:
            print("   " + " ".join(step["build"]))
            r = subprocess.run(step["build"], cwd=ROOT)
            if r.returncode != 0:
                print(f"FAIL step {step['key']} exited {r.returncode}; the order stops "
                      "here rather than running the rest over a broken input.",
                      file=sys.stderr)
                return 1
        stale = []
        for step in order["steps"]:
            r = subprocess.run(step["check"], cwd=ROOT, shell=True,
                               capture_output=True, text=True)
            if r.returncode != 0:
                stale.append((step["key"], (r.stdout + r.stderr).strip().splitlines()))
        if not stale:
            print(f"\nFIXED POINT reached after {attempt} pass(es). "
                  "Now run `node tools/rederive.mjs --check` — a fixed point that the "
                  "derived-layer rebuild undoes is not one (T-1363).")
            return 0
        print(f"\n   {len(stale)} step(s) still stale: "
              + ", ".join(k for k, _ in stale))
        print("   re-running the WHOLE order, not those steps — a stage's own check "
              "cannot see that its input is stale.")
    print("\nFAIL the order did not converge in %d pass(es). Still stale:" % limit,
          file=sys.stderr)
    for key, lines in stale:
        print(f"  {key}: {lines[0] if lines else 'no output'}", file=sys.stderr)
    print("That is an oscillation, not a slow convergence: two steps are moving each "
          "other. Read what each one writes in the order file before raising "
          "max_passes.", file=sys.stderr)
    return 1


def plan(order):
    print(order["_doc"].split("\n")[0])
    print()
    for n, step in enumerate(order["steps"], 1):
        print(f"{n:2d}. {step['key']}")
        print(f"      {' '.join(step['build'])}")
        print(f"      writes {', '.join(step['writes'])}")
        print(f"      reads  {', '.join(step['reads']) or '—'}")
    print("\nthe method:")
    for line in order["the_method"]:
        print(f"  - {line}")
    return 0


# ---------------------------------------------------------------- the gate

def overlaps(a, b):
    """Two declared paths touch the same ground (one contains the other)."""
    pa, pb = a.rstrip("/"), b.rstrip("/")
    return pa == pb or pa.startswith(pb + "/") or pb.startswith(pa + "/")


def back_edges(order):
    """Every (reader, writer, path) where a step reads what a LATER step writes."""
    found = []
    steps = order["steps"]
    for i, reader in enumerate(steps):
        for writer in steps[i + 1:]:
            for r in reader["reads"]:
                for w in writer["writes"]:
                    if overlaps(r, w):
                        found.append((reader["key"], writer["key"], r))
    return found


def gated_layer_rederivations(order):
    """Tools check.sh gates that re-derive next to the layer (assertion D's set)."""
    gate = CHECK_SH.read_text(encoding="utf-8")
    names = sorted(set(re.findall(r"python3 tools/([a-z0-9_]+)\.py", gate)))
    layer = order["the_layer"]
    out = []
    for name in names:
        # This file is the ORDER, not a step in it, and it matches its own filter on
        # the flag names it greps for. Left in, it would demand that the order name
        # itself — which the first run of this gate duly reported.
        if name == pathlib.Path(__file__).stem:
            continue
        src = TOOLS / (name + ".py")
        if not src.exists():
            continue
        text = src.read_text(encoding="utf-8")
        if not any(p in text for p in layer):
            continue
        if '"--check"' not in text and "'--check'" not in text:
            continue
        if not any(f in text for f in ('"--build"', "'--build'", '"--write"', "'--write'")):
            continue
        out.append(name)
    return out


def check(order, fail):
    # A. every step is gated by check.sh, and its build names a real tool.
    gate = CHECK_SH.read_text(encoding="utf-8")
    for step in order["steps"]:
        if step["check"] not in gate:
            fail(f"step {step['key']}: tools/check.sh does not run `{step['check']}`, so "
                 "nothing would notice this step going stale")
        name = tool_of(step)
        if name is None or not (TOOLS / (name + ".py")).exists():
            fail(f"step {step['key']}: its build names no tool in tools/")

    # B. every declared path is named by the tool that claims it.
    for step in order["steps"]:
        name = tool_of(step)
        if name is None:
            continue
        text = (TOOLS / (name + ".py")).read_text(encoding="utf-8")
        for path in step["writes"] + step["reads"]:
            parts = [c for c in path.split("/") if c and c not in GENERIC]
            missing = [c for c in parts if c not in text]
            if missing:
                fail(f"step {step['key']}: declares `{path}` but tools/{name}.py never "
                     f"names {', '.join(missing)} — a declaration nobody checks is a "
                     "comment")

    # C. the back edges are exactly the ones declared.
    declared = {(e["reader"], e["writer"], e["path"])
                for e in order["the_cycle"]["edges"]}
    actual = set(back_edges(order))
    for edge in sorted(actual - declared):
        fail("undeclared back edge: %s reads `%s`, which %s writes below it. That is a "
             "new reason one pass cannot converge; declare it in the_cycle.edges with "
             "its reason, or move the step." % (edge[0], edge[2], edge[1]))
    for edge in sorted(declared - actual):
        fail("the_cycle declares %s reads `%s` from %s, and the steps no longer say so. "
             "Remove the edge — a cycle that has closed should be visible as closed."
             % (edge[0], edge[2], edge[1]))

    # D. the set of gated re-derivations over the layer has not grown unclassified.
    in_order = {tool_of(s) for s in order["steps"]}
    known = in_order | set(order["not_in_the_order"]["names"])
    for name in gated_layer_rederivations(order):
        if name not in known:
            fail(f"tools/{name}.py now re-derives beside the resident layer and the gate "
                 "runs it, but the rebuild order neither runs it nor names it. Put it in "
                 "`steps` if the order has to run it, or in `not_in_the_order.names` if "
                 "it writes INTO the layer from a source rather than deriving from it")


# ---------------------------------------------------------------- self-test

def self_test():
    """Break each assertion and require it to fire. The transcript is meant to look bad."""
    failures = []

    def case(label, mutate):
        order = load()
        mutate(order)
        fired = []
        check(order, lambda msg: fired.append(msg))
        ok = bool(fired)
        print(f"   self-test | {'ok  ' if ok else 'FAIL'} {label}")
        if not ok:
            failures.append(label)

    def ungate(order):
        order["steps"][0]["check"] = "python3 tools/rebuild_resident_index.py --nonsense"

    def fiction(order):
        order["steps"][0]["writes"] = ["data/residents/a_file_nobody_writes.json"]

    def hide_an_edge(order):
        order["the_cycle"]["edges"] = order["the_cycle"]["edges"][1:]

    def phantom_edge(order):
        order["the_cycle"]["edges"] = order["the_cycle"]["edges"] + [
            {"reader": "order_book", "writer": "resident_audit",
             "path": "data/residents", "why": "invented"}]

    def unclassify(order):
        order["not_in_the_order"]["names"] = []

    case("a step the gate does not run", ungate)
    case("a path the tool never names", fiction)
    case("a back edge nobody declared", hide_an_edge)
    case("a declared edge the steps do not have", phantom_edge)
    case("a gated re-derivation classified nowhere", unclassify)

    # And the live file must pass, or the cases above prove nothing.
    live = []
    check(load(), lambda msg: live.append(msg))
    ok = not live
    print(f"   self-test | {'ok  ' if ok else 'FAIL'} the committed order still passes")
    if not ok:
        failures.append("the committed order still passes")
        for msg in live:
            print(f"   self-test |      {msg}")

    print(f"   self-test | {len(failures)} failure(s)")
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", action="store_true", help="print the order and the method")
    ap.add_argument("--run", action="store_true", help="execute it, iterate to the fixed point")
    ap.add_argument("--check", action="store_true", help="the gate; writes nothing")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--max-passes", type=int, default=None)
    ap.add_argument("--print-set", action="store_true",
                    help="print assertion D's set, for filling not_in_the_order")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    order = load()
    if args.print_set:
        for name in gated_layer_rederivations(order):
            print(name)
        return 0
    if args.plan:
        return plan(order)
    if args.run:
        return run_order(order, args.max_passes)

    problems = []
    check(order, problems.append)
    if problems:
        print("THE REBUILD ORDER DOES NOT HOLD", file=sys.stderr)
        for msg in problems:
            print(f"  - {msg}", file=sys.stderr)
        return 1
    edges = len(order["the_cycle"]["edges"])
    print(f"the rebuild order holds: {len(order['steps'])} steps, every one gated by "
          f"check.sh, {edges} declared back edge(s), "
          f"{len(gated_layer_rederivations(order))} gated re-derivation(s) beside the "
          "layer and all of them classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
