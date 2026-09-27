#!/usr/bin/env python3
"""Does this branch's diff warrant a full-town bake? T-1668.

`.github/workflows/chicago-4d-bake.yml`'s `warranted` job used to answer with a
path filter: any diff against `dev` touching `chicago/4d/generators/**`,
`tools/bake.sh` or that workflow baked. Correct as a first screen — T-0454's
drift guards in `bake_ref.py` are why it exists at all — and too coarse as a
verdict, because it costs a pull request its own merge.

THE ARITHMETIC, measured on T-1652 / PR #104, 2026-09-27. That PR was finished,
foreground-gated green (`check.sh` 666 steps, none red; the smoke's mobile and
desktop legs 94/0 each, zero page errors) and mergeable. Three of its four
checks were green — `gate`, `report`, `warranted` — and `bake` was still
`in_progress` eighteen minutes in. A full-town bake is twenty to thirty minutes
of Cycles; two `pr-automerge` laps are 2 x 540 s, which is under that floor. So
**every** pull request touching `generators/` became a `resume` PR by
construction, however green, and the janitor inherited work that was never in
doubt. No number of laps inside a 600 s foreground ceiling changes it.

And #104's three files were `generators/build.py`, `generators/code_inputs.py`
and `generators/common/selection.py` — not one of which can move a vertex. Its
own staleness gate said so: 422 assets matched their inputs with no rebake.

## What the branch bake is FOR, which is the whole rule

**Freshness.** `tools/validate.py`'s stale check hashes every asset's inputs —
the resolved parameters, the data, and the code the generators read through
`generators/mesh_inputs.py` and `generators/terrain_inputs.py` — and refuses a
tree whose committed GLBs no longer match. A generators change that moves one of
those hashes turns the gate red, and the branch bake is the REMEDY: it produces
the meshes the change made necessary and PRs them into the branch. That is why
a generators change earns an immediate bake.

So the register that decides freshness can decide the bake, and asking it is
cheap: no Blender, no third-party package, about half a second over 422 assets.
If nothing on this tree is stale, there is nothing for a bake to remedy.

**"A rebake proves the generator still runs" is a real claim, and a DIFFERENT
one.** It is not about this branch's meshes; it is about whether the pipeline
executes at all. The NIGHTLY bake on `dev` makes exactly that claim, every day,
on the authoritative tree — which is what the nightly is for (see the workflow's
own note on why `data/**` was removed from the trigger). A branch bake is not
the instrument for it, and spending a pull request's merge to take the
measurement a second time buys nothing.

**The skip is only as good as the register**, and that is deliberate rather than
overlooked. If a file that can move a vertex is outside every asset's input
hash, then the staleness gate is already wrong about it and this decision is
wrong about it for the same reason — one instrument, one bug, one fix. The
alternative is a second register kept in step with the first by memory, which is
the drift `generators/code_inputs.py` was written to end.

## Failing open

Unchanged from the path filter it extends, and for the same reason: a redundant
bake costs twenty minutes, a skipped one that was needed ships stale meshes and
the staleness gate then blames the pull request instead of the missing bake. Any
answer this script cannot establish — an unreadable manifest, a recipe that will
not import, no committed assets to compare, a path set it did not expect — is a
bake.

    tools/bake_warranted.py --decide [--changed-file FILE | -] [--base origin/dev]
    tools/bake_warranted.py --self-test
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent          # chicago/4d
REPO = ROOT.parent.parent                                      # the repo root
MANIFEST = ROOT / "assets" / "manifest.json"

# The file that changes HOW a bake runs. No asset's input hash reads it — it is
# the driver that decides what Blender is handed — so the freshness register
# cannot speak for it and it always bakes.
HOW_THE_BAKE_RUNS = {
    "chicago/4d/tools/bake.sh":
        "the bake's own driver — it decides what Blender is handed, and no input "
        "hash reads it",
}

GENERATORS = "chicago/4d/generators/"

# The workflow is the third case, and it is the one this rule's own first pull
# request had to answer. Most of it decides what the bake DOES — which tree,
# which Blender, what is pushed, where the PR goes — and no hash sees any of
# that, so it bakes. But the `warranted` job is the part that decides only
# whether the bake STARTS, and a change confined to it cannot change a single
# byte the bake produces. Editing the gate is not a reason to run the thing the
# gate guards. `workflow_shape_changed` below draws that line by comparing the
# workflow WITHOUT the gate job against the integration tier's copy.
WORKFLOW = ".github/workflows/chicago-4d-bake.yml"
GATE_JOB = "warranted"


class ProbeError(RuntimeError):
    """The freshness register could not be asked, so nothing may be skipped."""


def freshness(root: pathlib.Path | None = None):
    """Ask the SAME instrument `check.sh` uses: is any committed asset stale?

    Returns `(stale_messages, note, n_assets)`. Raises `ProbeError` when the
    question cannot be put — which the caller must read as "bake".

    `tools/validate.py::run_stale_check` is imported rather than reimplemented,
    for the reason `terrain_inputs.py` gives about its own two callers: two
    copies of a freshness rule agree until the day one of them matters.
    """
    root = root or ROOT
    manifest = root / "assets" / "manifest.json"
    if not manifest.exists():
        raise ProbeError(f"{manifest.relative_to(root)} is missing, so no committed "
                         f"asset can be compared with its inputs")
    try:
        n_assets = len(json.loads(manifest.read_text(encoding="utf-8")).get("assets", {}))
    except (ValueError, OSError) as e:
        raise ProbeError(f"assets/manifest.json cannot be read: {e}") from e
    if not n_assets:
        raise ProbeError("assets/manifest.json lists no assets, so freshness says "
                         "nothing about this tree")

    for p in (root / "tools", root / "generators"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    try:
        import validate  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001 — any import failure is "cannot answer"
        raise ProbeError(f"tools/validate.py will not import, so the freshness "
                         f"register cannot be read: {e}") from e

    rep = validate.Report()
    try:
        structures = validate.load_dir(validate.DATA / "structures", rep)
        before = len(rep.errors)
        validate.run_stale_check(structures, rep)
    except Exception as e:  # noqa: BLE001
        raise ProbeError(f"the stale check raised {type(e).__name__}: {e}") from e

    # Only this check's own findings count. `load_dir` above can add schema
    # errors of its own, and they are the `gate` check's business, not this
    # decision's — a malformed record is not a reason to run Blender.
    stale = [m for m in rep.errors[before:] if m.startswith("stale:")]
    note = next((n for n in reversed(rep.notes) if n.startswith("stale check:")), "")
    return stale, note, n_assets


def _without_gate_job(text, job=GATE_JOB):
    """The workflow's YAML with the gate job and every comment taken out.

    Comments go first for the reason `bake_ref.py`'s drift guards strip them: this
    file and that workflow both quote the rules they replaced, and prose about a
    bake is not a bake. The job block is everything from `  <job>:` to the next
    key at that indent — enough structure for a comparison, and deliberately not
    a YAML parse, which would need a package this five-minute gate does not
    install and would normalise away differences that matter.

    Raises `ProbeError` if the job cannot be located, because a rule that silently
    finds nothing to exclude is a rule that has stopped being applied.
    """
    lines = [l for l in text.splitlines() if not l.lstrip().startswith("#")]
    start = next((i for i, l in enumerate(lines) if l == f"  {job}:"), None)
    if start is None:
        raise ProbeError(f"the workflow has no `  {job}:` job at two-space indent, so "
                         f"the part that only decides whether to bake cannot be "
                         f"separated from the part that decides what a bake does")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        l = lines[i]
        if l.strip() and not l.startswith("   ") and l.startswith("  "):
            end = i
            break
    return "\n".join(lines[:start] + lines[end:])


def workflow_shape_changed(base="origin/dev", root=None):
    """Did this branch change what the bake DOES, or only whether it starts?

    Returns True when the workflow differs from `base` outside the gate job.
    Raises `ProbeError` when the two cannot be compared — an unfetched base, a
    workflow that has been restructured — which the caller reads as "bake".
    """
    import subprocess  # noqa: PLC0415 — only this path shells out
    repo = (root or REPO)
    try:
        was = subprocess.run(["git", "-C", str(repo), "show", f"{base}:{WORKFLOW}"],
                             capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, OSError) as e:
        raise ProbeError(f"{base}:{WORKFLOW} cannot be read, so what this branch "
                         f"changed in it cannot be established ({e})") from e
    now = (repo / WORKFLOW).read_text(encoding="utf-8")
    return _without_gate_job(was) != _without_gate_job(now)


def decide(changed, probe=freshness, shape=workflow_shape_changed):
    """(bake, reason). Pure but for `probe`, which is the point of the self-test.

    `changed` is this branch's own three-dot diff against the integration tier,
    as repo-relative paths — the same list the `warranted` job already takes.
    """
    paths = sorted({p.strip() for p in changed if p and p.strip()})
    if not paths:
        return True, ("no changed paths were given, so nothing about this branch "
                      "can be ruled out")

    how = [p for p in paths if p in HOW_THE_BAKE_RUNS]
    if how:
        return True, ("this branch changes how the bake runs, which no input hash "
                      "can see: " + "; ".join(f"{p} — {HOW_THE_BAKE_RUNS[p]}" for p in how))

    if WORKFLOW in paths:
        try:
            if shape():
                return True, (f"this branch changes what the bake DOES in {WORKFLOW}, "
                              f"outside the `{GATE_JOB}` job — no input hash sees that")
        except ProbeError as e:
            return True, f"the workflow could not be compared with its base ({e})"
        rest = [p for p in paths if p != WORKFLOW]
        if not rest:
            return False, (f"this branch changes {WORKFLOW} only inside the `{GATE_JOB}` "
                           f"job, which decides whether a bake starts and never what one "
                           f"produces. Editing the gate is not a reason to run the thing "
                           f"the gate guards")
        paths = rest

    outside = [p for p in paths if not p.startswith(GENERATORS)]
    if outside:
        return True, ("this decision only knows about " + GENERATORS + ", "
                      + ", ".join(sorted(HOW_THE_BAKE_RUNS)) + " and " + WORKFLOW
                      + ", and was handed " + ", ".join(outside))

    try:
        stale, note, n_assets = probe()
    except ProbeError as e:
        return True, f"the freshness register could not be asked ({e})"

    if stale:
        head = stale[0][len("stale:"):].strip()
        return True, (f"{len(stale)} of {n_assets} committed asset(s) no longer match "
                      f"their inputs, so this branch's generators change has meshes to "
                      f"remedy — first: {head}")
    return False, (f"all {n_assets} committed asset(s) still match their inputs "
                   f"({note or 'no note'}), so this branch's generators change moved no "
                   f"mesh and a bake has nothing to remedy. Whether the pipeline still "
                   f"RUNS is the nightly bake on the integration tier's claim, not this "
                   f"branch's")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--decide", action="store_true",
                    help="read changed paths (a file, or - for stdin) and print 1 or 0")
    ap.add_argument("--changed-file", default="-")
    ap.add_argument("--base", default="origin/dev",
                    help="the integration tier this branch's workflow is compared with")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.decide:
        ap.error("nothing asked — pass --decide or --self-test")

    if args.changed_file == "-":
        raw = sys.stdin.read()
    else:
        raw = pathlib.Path(args.changed_file).read_text(encoding="utf-8")
    bake, reason = decide(raw.splitlines(),
                          shape=lambda: workflow_shape_changed(args.base))
    # stdout is the answer, stderr is the reason: one invocation, and a caller
    # that wants only the verdict never has to grep prose out of it.
    print("1" if bake else "0")
    print(("baking — " if bake else "SKIPPING — ") + reason, file=sys.stderr)
    return 0


# --- the self-test ---------------------------------------------------------
# The decision is pure but for `probe`, so every branch of it is reachable with
# no runner, no remote and no Blender — including the fail-open paths, which are
# the ones a real tree can never demonstrate because a real tree is green. The
# drift guards at the end are the other half, for the reason bake_ref.py gives:
# a correct rule the workflow has stopped consulting is the same bug in a
# different hat.

def self_test():
    cases, failed = [], 0

    def case(name, got, want):
        nonlocal failed
        ok = got == want
        cases.append((ok, name, got, want))
        if not ok:
            failed += 1

    fresh = lambda: ([], "stale check: 422 asset(s) match their inputs, 0 stale", 422)
    stale = lambda: (["stale: x.glb is STALE — its inputs now hash to abc"], "", 422)

    def raises():
        raise ProbeError("assets/manifest.json is missing")

    # THE FAULT, and the exact diff that produced T-1668: PR #104's three files,
    # none of which any asset's input hash reads.
    p104 = ["chicago/4d/generators/build.py",
            "chicago/4d/generators/code_inputs.py",
            "chicago/4d/generators/common/selection.py"]
    case("a generators diff that staled nothing does not bake",
         decide(p104, fresh)[0], False)
    case("…and it says so with the register's own count",
         "422 committed asset(s) still match" in decide(p104, fresh)[1], True)

    # …and the case the bake exists FOR is untouched, which is the other half.
    case("a generators diff that staled a mesh bakes",
         decide(["chicago/4d/generators/emit.py"], stale)[0], True)
    case("…and it names what went stale rather than only the path",
         "is STALE" in decide(["chicago/4d/generators/emit.py"], stale)[1], True)

    # FAILING OPEN, every way it can be reached.
    case("a register that cannot be asked bakes", decide(p104, raises)[0], True)
    case("…and says which question it could not put",
         "manifest.json is missing" in decide(p104, raises)[1], True)
    case("an empty diff bakes rather than skips", decide([], fresh)[0], True)
    case("a whitespace-only diff is an empty one", decide(["", "  ", "\t"], fresh)[0], True)
    case("a path set this rule does not know about bakes",
         decide(["chicago/4d/data/structures/x.json"], fresh)[0], True)
    case("…even when a generators path is in the same diff",
         decide(["chicago/4d/generators/emit.py", "renderers/web/js/world.js"], fresh)[0], True)

    # THE FILES NO HASH CAN SEE. The register is silent about them by
    # construction, so a fresh tree must not be allowed to speak for them.
    case("a change to bake.sh bakes however fresh the tree is",
         decide(["chicago/4d/tools/bake.sh"], fresh)[0], True)
    case("…and the reason says a hash cannot see it",
         "no input hash" in decide(["chicago/4d/tools/bake.sh"], fresh)[1], True)
    case("the how-it-runs set is checked before the register is even asked",
         decide(["chicago/4d/tools/bake.sh"], raises)[0], True)

    # EVERY NAMED FILE CARRIES ITS REASON. A name with no sentence beside it is
    # the beginning of the drift code_inputs.py was written to stop.
    case("every how-it-runs entry states why the register cannot speak for it",
         all(len(v) > 40 for v in HOW_THE_BAKE_RUNS.values()), True)

    # THE WORKFLOW, WHICH IS THE CASE THIS RULE'S OWN PULL REQUEST WAS. A change
    # to what the bake DOES bakes; a change confined to the gate that decides
    # whether it starts does not, because that cannot move one byte of output.
    did = lambda: True
    gate_only = lambda: False
    def no_base():
        raise ProbeError("origin/dev:.github/workflows/chicago-4d-bake.yml cannot be read")
    case("a workflow change outside the gate job bakes",
         decide([WORKFLOW], fresh, did)[0], True)
    case("…and says it is what the bake DOES that moved",
         "what the bake DOES" in decide([WORKFLOW], fresh, did)[1], True)
    case("a workflow change confined to the gate job does not bake",
         decide([WORKFLOW], fresh, gate_only)[0], False)
    case("…and says editing the gate is not a reason to run what it guards",
         "not a reason to run" in decide([WORKFLOW], fresh, gate_only)[1], True)
    case("a workflow that cannot be compared with its base bakes",
         decide([WORKFLOW], fresh, no_base)[0], True)
    case("the gate-job carve-out never speaks for the generators beside it",
         decide([WORKFLOW, "chicago/4d/generators/emit.py"], stale, gate_only)[0], True)
    case("…and a fresh tree beside it still skips, on the register's word",
         decide([WORKFLOW, "chicago/4d/generators/emit.py"], fresh, gate_only)[0], False)

    # AND THE CARVE-OUT MUST BE ABLE TO FIND THE JOB IT CARVES OUT. A rule that
    # silently excludes nothing has stopped being applied, and the way that
    # happens is somebody renaming or re-indenting the job.
    wf_text = (REPO / WORKFLOW).read_text(encoding="utf-8")
    case("the gate job is locatable in the workflow as it stands",
         f"  {GATE_JOB}:" in wf_text, True)
    case("…and carving it out leaves the rest of the workflow behind",
         "jobs:" in _without_gate_job(wf_text)
         and "timeout-minutes: 30" in _without_gate_job(wf_text), True)
    case("…and takes the gate's own body with it",
         "bake_warranted.py" in _without_gate_job(wf_text), False)
    try:
        _without_gate_job("jobs:\n  bake:\n    runs-on: x\n")
        located = "no error"
    except ProbeError as e:
        located = "refused" if "cannot be separated" in str(e) else f"wrong: {e}"
    case("…and a workflow with no such job is refused rather than compared",
         located, "refused")

    # THE REGISTER IS THE ONE check.sh USES, not a second copy of it. If this
    # stops importing validate.py the two can disagree, which is the whole thing
    # this decision rests on.
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    case("freshness asks tools/validate.py's own stale check",
         "validate.run_stale_check(" in src, True)

    # --- the drift guards --------------------------------------------------
    # Comments stripped first: the workflow quotes the rule it replaced, and a
    # guard that reads prose cannot tell a fix from a description of one.
    wf = wf_text
    live = "\n".join(l for l in wf.splitlines() if not l.lstrip().startswith("#"))
    case("the warranted job asks this script", "tools/bake_warranted.py" in live, True)
    case("…with --decide, so it gets a verdict and not the usage", "--decide" in live, True)
    case("…and the path filter is still the first screen it applies",
         "origin/$BASE...HEAD" in live, True)
    case("…and a diff that cannot be taken still bakes without asking",
         "could not diff against" in wf, True)
    case("…and the skip is still reported as a skip",
         "SKIPPING" in live, True)

    for ok, name, got, want in cases:
        if ok:
            print(f"  ok    {name}")
        else:
            print(f"  FAIL  {name}\n        got  {got}\n        want {want}")
    if failed:
        print(f"SELF-TEST FAIL — {failed} of {len(cases)} case(s)")
        return 1
    print(f"SELF-TEST PASS — a generators diff that staled nothing does not bake, "
          f"one that staled a mesh does, every unanswerable case bakes, and the "
          f"workflow still asks ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
