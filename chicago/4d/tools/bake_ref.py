#!/usr/bin/env python3
"""Which tree does the content bake actually build? (T-0454)

`chicago-4d-bake.yml` opened with a checkout and then, unconditionally, this:

    if git ls-remote --exit-code --heads origin dev >/dev/null 2>&1; then
      git checkout -B dev origin/dev
    fi

For the nightly that is right — the schedule always fires on the default branch,
and the bake's PR goes to `dev`, so branching off `main` would put every commit
already promoted past into the diff. For a **dispatch against a branch it is a
silent discard**: the run is handed a ref, throws it away, and bakes `dev`.

That is the whole of T-0454, and it is why the gate and the bake could both be
right while disagreeing. Reproduced on 2026-09-03 on `steward/t-0429-...`'s
fault pattern, one mesh parameter moved on a branch:

    tools/validate.py --stale   FAIL  bates_auction_room__frame_1834.glb is STALE
                                      inputs now hash e2c58b0e5ee8, mesh built from 010608142cf0
    the step above                    HEAD t0454-repro fbebc203 -> dev 8ecfcb57
                                      the changed parameter: 0 occurrences
    build.py --only <id>              rebuilds it in 0.7 s and clears the gate
                                      — WHEN IT IS SHOWN THE TREE THAT CARRIES THE CHANGE

So `build.py` never skips; it was never asked. It rebuilt a fresh `dev`, produced
byte-identical output, and `bake_content_changed.py` reported "no CONTENT" —
correctly, about a tree nobody had asked about. Two right answers to two
different questions, and the branch's stale asset untouched. The remedy the gate
prints ("Re-bake it — tools/bake.sh, or the chicago-4d-bake workflow") was true
of the first and false of the second.

## The rule

Bake `dev` when the run has no tree of its own to speak for:

  * the **schedule**, which always fires on the default branch; and
  * a run whose ref IS the production tier, because nothing may PR into `main`
    (docs/PIPELINE.md) — a bake there would have nowhere to land.

Otherwise bake **the ref the run was started on**, and open the PR against that
same ref. A dispatch names a tree because it means that tree.

The tiers are read from `.github/pipeline.json` rather than spelled `dev`/`main`
here, so the day the pipeline grows a stage tier this does not quietly disagree
with the manifest that every other reader uses.

    tools/bake_ref.py --event <name> --ref <ref> [--github]
    tools/bake_ref.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent          # chicago/4d
REPO = ROOT.parent.parent                                      # the repo root
PIPELINE = REPO / ".github" / "pipeline.json"
WORKFLOW = REPO / ".github" / "workflows" / "chicago-4d-bake.yml"

# The events that arrive without a tree of their own. `schedule` fires on the
# default branch by GitHub's definition, never on the branch anyone cares about.
REFLESS_EVENTS = {"schedule"}


def tiers(pipeline_path=None):
    """(integration, production) from the pipeline manifest."""
    data = json.loads((pipeline_path or PIPELINE).read_text(encoding="utf-8"))
    t = data["tiers"]
    return t[0], t[-1]


def short(ref):
    """`refs/heads/x` and `x` both name the branch x."""
    for prefix in ("refs/heads/", "refs/tags/"):
        if ref.startswith(prefix):
            return ref[len(prefix):]
    return ref


def resolve(event, ref, dev_exists, integration="dev", production="main"):
    """The branch to bake, and why. Pure — the self-test is the point.

    Returns (branch, reason).
    """
    name = short(ref or "")
    if not dev_exists:
        # The pipeline is not activated. Everything bakes what it was given, and
        # the PR goes there; this is the pre-2026-08-14 shape.
        return name or production, "no dev ref — baking the ref this run was started on"
    if event in REFLESS_EVENTS:
        return integration, f"{event} carries no ref of its own — baking {integration}"
    if name == production:
        return integration, (f"{production} is the production tier and nothing may PR into it "
                             f"(docs/PIPELINE.md) — baking {integration}")
    return name, f"baking {name}, the ref this run was started on"


def base_is_live(base, pr_states, integration="dev", production="main"):
    """Can a bake PR into `base` ever reach the integration tier?

    `resolve` above answers "which tree does this bake build". It cannot answer
    "is that tree still going anywhere", because a bake takes the better part of
    an hour and the branch can merge while it runs. When it does, the PR opens
    into a branch nothing will ever merge again: 196 regenerated assets with
    nowhere to land, sitting in the open-PR count forever.

    Measured on 2026-09-14 between 23:15 and 00:41 — seven bakes in that state:

        bake   opened   base                                parent merged
        #1283  23:15    fix/queue-ratchet                   22:27  (before)
        #1285  23:49    steward/t-1004-two-men-one-card     23:09  (before)
        #1286  23:51    steward/t-0995-shared-roll-lines    22:48  (before)
        #1288  00:05    steward/t-0896-drain-check-capable  23:05  (before)
        #1292  00:20    steward/t-0266-phone-picket-moire   23:50  (before)
        #1293  00:31    steward/t-0809-rotting-pr-rule      01:18  (after)
        #1294  00:40    steward/t-0801-prefire-viewer-wright 02:06 (after)

    FIVE of the seven were built against a branch that had ALREADY MERGED before
    the bake opened its PR — the run spent its whole bake on a dead tree. They
    also sit in the janitor's path: `steward/bake-*` matches its sweep pattern,
    so each one costs a full check.sh gate every hour against a base that cannot
    move.

    `pr_states` is every pull request ever opened FROM `base`, as
    "open"/"merged"/"closed". The three answers are deliberately distinct:

      * a pipeline tier is always live — the nightly bakes `dev` and PRs into it,
        and `dev` has no pull request of its own;
      * NO pull request at all is live, and this is the case that makes the rule
        safe. A dispatch may bake a branch before its PR exists — that is exactly
        the T-0454 scenario this whole script was written for, and refusing it
        would trade one silent discard for another;
      * every pull request merged or closed is DEAD. The branch had its say and
        the tree moved on.

    Returns (live, reason).
    """
    if base in (integration, production):
        return True, f"{base} is a pipeline tier, which is always a live base"
    states = [s.lower() for s in pr_states]
    if not states:
        return True, (f"{base} has no pull request yet — a dispatch may bake a branch "
                      f"before it opens one (T-0454), so this is not a dead base")
    if "open" in states:
        return True, f"{base} still has an open pull request"
    return False, (f"every pull request from {base} is already merged or closed, so a bake "
                   f"PR into it could never reach {integration}")


def pr_states_for(base, repo=None):
    """Every PR state ever recorded for head branch `base`. [] when unknown."""
    import json as _json
    import urllib.error
    import urllib.request

    repo = repo or os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not repo or not token:
        raise RuntimeError("GITHUB_REPOSITORY and a token are both needed to ask")
    owner = repo.split("/")[0]
    url = (f"https://api.github.com/repos/{repo}/pulls"
           f"?state=all&head={owner}:{base}&per_page=100")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "chicago-4d-bake-ref",
    })
    with urllib.request.urlopen(req, timeout=30) as fh:
        data = _json.load(fh)
    return ["merged" if p.get("merged_at") else p.get("state", "") for p in data]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", default=os.environ.get("GITHUB_EVENT_NAME", ""))
    ap.add_argument("--ref", default=os.environ.get("GITHUB_REF", ""))
    ap.add_argument("--dev-exists", choices=["0", "1"])
    ap.add_argument("--github", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--check-base", metavar="BRANCH",
                    help="is a bake PR into BRANCH still able to reach the integration "
                         "tier? prints 1 or 0")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    if args.check_base:
        integration, production = tiers()
        # FAIL SAFE, AND IN ONE DIRECTION ONLY. A bake that ran for 45 minutes is
        # not thrown away because the API was briefly unreachable, so every error
        # here answers LIVE and says so. The cost of a wrong "live" is one PR
        # somebody closes; the cost of a wrong "dead" is a lost bake.
        try:
            states = pr_states_for(args.check_base)
        except Exception as exc:                                   # noqa: BLE001
            print(f"could not ask GitHub about {args.check_base} ({exc}) — "
                  f"treating the base as live", file=sys.stderr)
            print("1")
            return 0
        live, reason = base_is_live(args.check_base, states, integration, production)
        print(reason, file=sys.stderr)
        print("1" if live else "0")
        return 0

    integration, production = tiers()
    if args.dev_exists is not None:
        dev_exists = args.dev_exists == "1"
    else:
        import subprocess
        dev_exists = subprocess.run(
            ["git", "ls-remote", "--exit-code", "--heads", "origin", integration],
            cwd=REPO, capture_output=True).returncode == 0

    branch, reason = resolve(args.event, args.ref, dev_exists, integration, production)
    # The REASON goes to stderr and the ANSWER to stdout, always — so the caller
    # can read the branch with `$(...)` whether or not it also wants the step
    # output, and the log still says why. A caller that had to grep
    # $GITHUB_OUTPUT back out would break the day another step appended to it.
    print(reason, file=sys.stderr)
    print(branch)
    if args.github and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"branch={branch}\n")
            fh.write(f"dev_exists={'1' if dev_exists else '0'}\n")
    return 0


# --- the self-test ---------------------------------------------------------
# Pure inputs, so this needs no runner, no remote and no Blender. The drift
# guards at the end are the other half: a correct decision the workflow has
# stopped asking for is the same bug wearing a different hat.

def self_test():
    cases, failed = [], 0

    def case(name, got, want):
        nonlocal failed
        ok = got == want
        cases.append((ok, name, got, want))
        if not ok:
            failed += 1

    # THE FAULT. This is the one that cost PR #597 and produced T-0454.
    case("a dispatch against a branch bakes THAT BRANCH",
         resolve("workflow_dispatch", "refs/heads/steward/t-0429-south-water-lasalle", True)[0],
         "steward/t-0429-south-water-lasalle")
    case("a push to a branch bakes that branch, not dev",
         resolve("push", "refs/heads/steward/t-0121-stage-recut", True)[0],
         "steward/t-0121-stage-recut")

    # …and the nightly's behaviour is UNCHANGED, which is the other half of the
    # fix: it is the reason the old line was written and it still holds.
    case("the nightly bakes dev", resolve("schedule", "refs/heads/main", True)[0], "dev")
    case("a run whose ref is main bakes dev — nothing may PR into main",
         resolve("workflow_dispatch", "refs/heads/main", True)[0], "dev")
    case("a push to dev bakes dev", resolve("push", "refs/heads/dev", True)[0], "dev")

    # Before the pipeline was activated there was no dev, and the old line said so.
    case("with no dev ref, the nightly bakes what it was given",
         resolve("schedule", "refs/heads/main", False)[0], "main")
    case("with no dev ref, a dispatch bakes its own branch",
         resolve("workflow_dispatch", "refs/heads/topic", False)[0], "topic")

    case("a bare branch name is a branch name", short("dev"), "dev")
    case("refs/heads/ is stripped", short("refs/heads/a/b"), "a/b")

    # The tiers come from the manifest every other reader uses.
    case("the tiers are read from .github/pipeline.json", tiers(), ("dev", "main"))

    # --- is the baked ref still going anywhere? ----------------------------
    # THE FAULT: seven bakes on 2026-09-14 opened into a branch that had already
    # merged. Five of them were dead before the bake even started.
    case("a base whose PR has merged is dead",
         base_is_live("steward/t-0809-rotting-pr-rule", ["merged"])[0], False)
    case("…and so is one whose only PR was closed unmerged",
         base_is_live("steward/abandoned", ["closed"])[0], False)
    case("…and one with several, all finished",
         base_is_live("fix/queue-ratchet", ["merged", "merged"])[0], False)

    # The other three answers, each of which must stay true or the rule starts
    # discarding legitimate bakes — the exact failure T-0454 was written about.
    case("a base with an open PR is live",
         base_is_live("steward/t-0848-part9-frame-independence", ["open"])[0], True)
    case("…even when an earlier PR from it was closed",
         base_is_live("steward/reopened", ["closed", "open"])[0], True)
    case("a branch that has NOT opened its PR yet is live — the T-0454 dispatch",
         base_is_live("steward/t-0429-south-water-lasalle", [])[0], True)
    case("dev is live and has no PR of its own — the nightly must never be skipped",
         base_is_live("dev", [])[0], True)
    case("main is a tier too, so the rule never calls the production tier dead",
         base_is_live("main", [])[0], True)
    case("the states are read case-insensitively, as the API spells them",
         base_is_live("steward/x", ["MERGED"])[0], False)

    # --- the drift guards --------------------------------------------------
    # Comments stripped first: the workflow step quotes the line it replaced, and
    # a guard that reads prose cannot tell a fix from a description of one.
    wf = WORKFLOW.read_text(encoding="utf-8")
    live = "\n".join(l for l in wf.splitlines() if not l.lstrip().startswith("#"))
    case("the workflow no longer hard-checks-out dev",
         "git checkout -B dev origin/dev" in live, False)
    case("the workflow asks this script which ref to bake",
         "tools/bake_ref.py" in live, True)
    case("the PR base follows the ref that was baked, not a literal dev",
         "--base dev" in live, False)
    case("…and the base comes from the bake job's own output",
         "needs.bake.outputs.base" in live, True)

    # A correct rule the workflow has stopped consulting is the same bug in a
    # different hat — the guard the original T-0454 drift checks above exist for.
    case("the workflow asks whether the baked ref is still live",
         "--check-base" in live, True)
    case("…and open-pr refuses to open a PR into a base that is not",
         "needs.bake.outputs.base_live == '1'" in live, True)
    # ASKED TWICE, AND THE SECOND TIME IS THE ONE #1303 NEEDED. The job-start
    # answer is three quarters of an hour stale by the time the PR is opened;
    # #1303's base was live at 02:37:50 and merged at 02:44:20, and the PR opened
    # at 03:16 into a branch nothing would ever merge again. A guard that only
    # runs before the work cannot see a base die during it.
    case("…and it asks AGAIN at the moment the PR is opened, not only at job start",
         live.count("--check-base") >= 2, True)
    # A GREEN BAKE PR THAT NOTHING MERGES IS STILL A BAKE PR NOBODY MERGED. The
    # liveness rule above decides whether to OPEN one; this asserts the workflow
    # then arms auto-merge on it. A steward run arms its own PR and merges it
    # inside the run — a bake has no run watching it, and the janitor's gate for
    # this monorepo does not fit inside its own timeout (run 1047: 53m37s on one
    # PR, killed unfinished), so without this nothing merges a bake at all.
    # Measured 2026-09-14: of thirteen non-hold PRs open, the seven carrying
    # auto-merge were every one a T-xxxx ticket and no bake had it.
    case("…and the bake arms auto-merge on the PR it opens",
         "gh pr merge" in live and "--auto" in live, True)

    # A BAKE THAT IS NOT THIS BRANCH'S BUSINESS MUST NOT START, and the reason is
    # arithmetic rather than tidiness. `on.push.paths` matches the files a PUSH
    # carries, not the files a branch OWNS, and the PR lap merges `dev` into
    # every open pull request — so one change under generators/ reaches every
    # branch and every branch matches the filter. Measured 2026-09-14: #1319
    # changed terrain_gen.py, the lap swept, and SEVEN ~20-minute Blender bakes
    # started at once; `dev`'s own — the only authoritative one — sat QUEUED
    # behind the branch copies, and the PR lap queued behind all of them while
    # four pull requests waited `dirty` for exactly that lap.
    #
    # The `warranted` job asks what the filter cannot: does this branch's OWN
    # diff against dev (`dev...HEAD`, three-dot) touch a trigger path? If a later
    # edit drops that gate, the fan-out returns silently — it costs runner time
    # and queue latency, neither of which turns anything red.
    case("a push bake is gated on the branch's own diff, not just the push's",
         "warranted" in live and "needs.warranted.outputs.bake == '1'" in live, True)
    case("…and it asks with the three-dot form, which is what the branch OWNS",
         'origin/$BASE...HEAD' in live, True)
    case("…and it is a separate job, so the Blender runner is never claimed to skip",
         "needs: warranted" in live, True)
    # FAILING OPEN IS THE POINT: a redundant bake costs twenty minutes, a skipped
    # one that was needed ships stale meshes and the staleness gate then blames
    # the pull request instead of the missing bake.
    case("…and an unanswerable diff bakes rather than skips",
         'echo "bake=1" >> "$GITHUB_OUTPUT"' in live and "could not diff against" in wf, True)

    for ok, name, got, want in cases:
        if ok:
            print(f"  ok    {name}")
        else:
            print(f"  FAIL  {name}\n        got  {got}\n        want {want}")
    if failed:
        print(f"SELF-TEST FAIL — {failed} of {len(cases)} case(s)")
        return 1
    print(f"SELF-TEST PASS — the bake builds the ref it was given, the nightly "
          f"still builds dev, and the workflow still asks ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
