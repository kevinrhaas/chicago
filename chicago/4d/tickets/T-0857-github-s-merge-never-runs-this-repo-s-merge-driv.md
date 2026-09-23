---
id: T-0857
title: GitHub's merge never runs this repo's merge drivers, so every PR reads as conflicting and auto-merge can never fire
state: split
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-06
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T03:32:45.685Z
claimed_run: null
---

GitHub's server-side merge never runs a custom merge driver, so every PR that touches a
`merge=generated` file reads as CONFLICTING to the platform however cleanly it merges here.

**MEASURED 2026-09-06, and this is the whole of it — same branch, same merge, two answers:**

| | result |
|---|---|
| locally, after `bash tools/setup-merge-drivers.sh` | **0 conflicts, clean** |
| GitHub *Update branch* / auto-merge on the identical merge | **merge conflict** |

Tested on PR #940, cut after T-0831. `.gitattributes` can NAME a driver; only a clone that has
run `setup-merge-drivers.sh` can EXECUTE one, and GitHub has run nothing.

**WHAT IT COSTS, and it is the cause of the 2026-09-05/06 backlog rather than a footnote.**
Sixteen PRs stood open at 02:00Z, every one of them GREEN and every one with auto-merge
ARMED by its own run. None could land. Auto-merge cannot fire on a PR GitHub calls
conflicting, *Update branch* refuses it, and the only thing that ever works is a human or
agent doing a lap in a clone that has the drivers — which is why the pile grows at exactly
the rate the lane opens PRs, and shrinks only when someone laps by hand. T-0831 IS WORKING;
it is invisible to the only merge that decides mergeability.

**A SECOND TRAP UNDERNEATH, and it is permanent for the branches it catches.** A merge driver
that lives in the repo cannot resolve a merge on a branch cut BEFORE it: `tools/merge-generated.mjs`
is absent from those trees, the driver cannot run, and the five files conflict on every lap
forever. #841, #911, #913, #914, #917, #921, #926 and the closed #850 are all in that class.

**Acceptance — one of these, argued and measured, not all three:**

1. **Take the generated artifacts off the PR surface.** Stop tracking `BOARD.md`, both
   `tickets.json`, `build.json`, `walk/index.html` and the smoke ledger; regenerate them on
   `dev` after each merge. Nothing to conflict, no driver needed, auto-merge works unaided.
   The cost is `check_published` and the staleness gate, which currently require a branch to
   carry a consistent mirror — they would gate `dev` instead. This is the version where the
   problem stops existing, and it is the one to beat.
2. **A janitor that laps in CI.** A workflow that, for each open `steward/*` PR, registers the
   drivers, merges the base, regenerates and pushes. Drivers work fine in CI. **It needs a PAT
   this repo does not have**: a push made with `GITHUB_TOKEN` does not re-trigger `gate`, so the
   PR would sit with no check on its new head and auto-merge would still not fire. Adding
   `STEWARD_PAT` here is part of the ticket if this route is taken.
3. **Make the five files merge textually** — no driver. Only worth it if a shape exists that a
   default merge resolves, and JSON and HTML mostly do not, so measure before proposing it.

Whichever is taken, **say so in `.gitattributes`**: the file currently promises a conflict-free
merge that only holds on a developer's machine, and the next person to read it will believe it.

**Links:** T-0831 (the drivers, working) · T-0813 (the six build products) · T-0809 (the
janitor) · T-0802 and T-0820 (the same family — nothing here is visible before a PR merges) ·
PR #940 (the measurement).

---

## WORKED, 2026-09-06 — acceptance 2, and the measurement that made it possible

The owner added `STEWARD_PAT` to this repo and chose the janitor route.
`.github/workflows/chicago-4d-pr-lap.yml` + `.github/steward/pr-lap.sh` bring every open
non-draft, non-`hold` PR up to date and push; they never merge a PR, they only remove the
reason GitHub calls it conflicting, and auto-merge does the rest.

**The second trap is solved, and this is the part that was not obvious.** Registering dev's
merge drivers by absolute path is NOT enough on a branch cut before T-0831: git reads `merge=`
out of the .gitattributes in the WORKING TREE, so an old branch routes nothing to a driver
however well it is registered. `$GIT_DIR/info/attributes` outranks the tree, so the lap injects
dev's rules there and merges every branch under them.

    measured on PR #841, cut before T-0831
      drivers from the branch          REAL(3) + 5 generated  = 8 conflicts
      drivers from dev, alone          8 conflicts — attributes still the branch's
      drivers AND attributes from dev  3 conflicts, and all three are real

**What it does NOT fix, measured across all sixteen open PRs on 2026-09-06.** Only #913 and
#940 came out clean; every other PR has a genuine content disagreement with dev — crosswalks,
household cards, minting tools, a research baseline — and the lap REFUSES those rather than
picking a side, leaving one comment naming the files. So the lap is worth having for what it
stops recurring, not as a drain: **it keeps tomorrow's PRs mergeable; it does not rescue
today's, which want the runs that own their tickets.**

**Still open under acceptance 1**, and still the better answer: taking the generated artifacts
off the PR surface entirely would mean no drivers, no attributes injection, no PAT and no lap.
This ticket stays open for it.

**A follow-up the lap wants**: a DERIVED tier below the generated one, for files a tool
rebuilds from sources (`identity_master.json`, `source_coverage.json`, `register_1835.json`,
`street_face_adoptions.json`, the Newberry leads) — #880 already regenerated exactly those by
hand rather than reconciling them. `*_baseline.json` must stay OUT of it: a ratchet is a
measurement, and regenerating one silently lowers a bar.

---

## ACCEPTANCE 1, DESIGNED — and it is bigger and better than this ticket described

Asked for on 2026-09-06 after the lap shipped. Reading the deploy to design it found that the
premise was wrong in the project's favour: **the mirror never needed to be tracked at all.**

**The evidence.** `deploy.yml` already ASSEMBLES into `site/` on the runner — it builds the
`/chicago/4d/dev/` preview there from a worktree — and then uploads with
`actions/upload-pages-artifact` `path: site`. Pages serves what the RUNNER holds, not what the
commit holds. And `publish.sh` is a pure copy: its own header says "copy the publishable tree
into site/". So `site/chicago/4d/` — **2,280 tracked files** — is a build output that happens
to be committed.

**The design, then, is not "take five files off the PR surface" but:**

1. **Untrack `site/chicago/4d/**` and run `tools/publish.sh` in `deploy.yml` before the upload.**
2. `check_published.mjs` changes from *"the committed mirror matches the dataset"* to
   *"publish.sh PRODUCES a mirror that matches"*. That is STRICTER, not weaker, and it keeps
   R-BUG3c-b's sentence — *do not measure the file you built, measure the file you ship* —
   because deploy publishes exactly the tree it just verified.
3. `BOARD.md` and `tickets.json` go the same way: pure functions of the ticket files, and
   `ticket.mjs check` ALREADY regenerates and compares them, so nothing is lost by not
   committing them.
4. `.gitattributes` drops the `merge=generated` lines; `queue` and `changelog` stay.
5. `tools/dev-smoke-state.json` STAYS TRACKED. It is a ledger of readings, not a build output —
   real data with its own append-union driver, and regenerating it is not a thing that can be
   done.

**What it dissolves, all at once:** every mirror conflict for every PR forever (not just the
five files); the need for merge drivers, the `$GIT_DIR/info/attributes` injection, the PAT and
the lap, on those paths; and **the site byte budget** — `SITE_BUDGET_MB` measures a tracked
tree, and there would no longer be one, which retires the fault that produced SIX tickets in a
day (T-0722/0725/0731/0774/0803) and takes T-0727's boot-payload budget from "nice to have" to
"the only site budget there is".

**WHY IT WAS NOT DONE IN THE SESSION THAT DESIGNED IT.** It untracks 2,280 files, rewrites the
gate that R-BUG3c-b bought with three parcels, and changes the single deploy authority — and
it interacts with the `/v/` frozen snapshots and the dev-preview assembly, neither of which was
traced. That is a piece of work with its own gate and its own smoke, not a change to land
unattended at 04:00 behind an auto-merge. The lap (acceptance 2) is in place and holding the
line meanwhile, which is exactly what it was for.

**The one thing to check first, because it decides the shape:** whether `/v/release-vNNN/`
snapshots and `chicago-4d-promote-to-prod.yml` read the COMMITTED mirror. If a frozen snapshot
is taken from the tree rather than rebuilt, it needs the mirror at that commit and this design
needs a step that materialises one.
