# AGENTS.md — the contract for anyone working on 4D Chicago

Read this every session. It is one page on purpose.

## What this project is

A year-parameterized, walkable reconstruction of downtown Chicago. **It is a research
dataset with renderers attached** — not a game. The durable artifact is the georeferenced
land + structure data with per-attribute source provenance. Renderers are plural and
disposable. The first rendered scene is `1835` (target date 1835-07-01).

## Hard rules

1. **Never invent a source.** Every `source_id` must resolve in `data/sources/`. If evidence
   does not exist, mark the attribute `conjectural`. Fabricating a citation to make the
   validator pass is the worst thing you can do here.
2. **Never silently fill a gap.** Missing evidence is recorded as missing. `inferred` requires
   a `note` stating the reasoning. That is what the confidence model is for.
3. **Never drift past the scene date.** Most vivid published description of early Chicago is
   1837–1845 and describes a bigger town. `data/exclusions.json` records researched-and-excluded
   structures with citations — read it before adding anything, and add to it rather than
   deleting a finding.
4. **Every mesh is generated from `data/` by a command.** The one exception is
   `assets/authored/`, which is tagged `authored`, exempt from regeneration, and carries the
   same provenance requirements as generated geometry.
5. **Renderers consume glTF + JSON sidecars.** They never reach into `generators/` or
   reimplement the data model. Archetype parameters stay engine-neutral — the contract is
   glTF, not Blender.
6. **No asset without license provenance.** Every file under `assets/` has an entry in
   `assets/LICENSES.md`. A source whose `rights_status` is `check_required` may be cited in
   text but must not have assets derived from it.
7. **Every crosswalk states what it rests on.** A ruling that names a person in the town
   and no `source_id` cannot be carried to that person's card by any tool —
   `persons[].sources` is a list of source ids — so it can only be spent by a human
   rereading the whole file. State it at the top of the crosswalk where the file
   adjudicates from one source, or per entry where a ruling rests on something specific.
   `measure_research_spend.py --gate` holds `no source stated` at 0 and `check.sh` runs it.
   The fix for an unsourced ruling is to state the source or to WITHDRAW the ruling; rule 1
   still binds, and a plausible-looking citation that takes this gate green is worse than
   the missing one.
8. **A ruling names the units it ruled on, and a re-reading says it is one.** The
   research-spend ratchet counts named units READ against the ones RULED ON, so both halves
   have to be sayable. A refusal or a merge names its units by id — `record_id`,
   `household_id`, or plain ids in `evidence[]` — because a ruling whose evidence points at a
   prose locator ("poll_1835 line 293") counts as no adjudication at all, and
   `measure_research_spend.py` will print it as uncounted with that reason. A file that
   RE-reads what the domain already read — a precision sample, a second reading kept for its
   disagreement — declares `not_a_reading: "<what it is instead>"` at the top, or measuring
   your own work reads the meter up and the domain looks further behind for having checked
   itself. Both are printed by the report; neither is ever a silent zero.
9. **`tools/check.sh` passes before every commit.** It takes seconds and needs no Blender.
   **Read its last four lines, not its middle.** 115 of its 304 steps are self-tests that
   prove a gate by breaking it, so a GREEN run prints fourteen `FAIL` lines on purpose.
   Those are tagged — every line of a self-test's transcript starts `   self-test | ` —
   and the steps that actually failed are listed once, by label, under `CHECK FAIL` at
   the end. An untagged `FAIL` is the only kind worth chasing. Three tickets were filed
   against tagged ones before T-0763; do not make a fourth.

## Standing constraint — 1835 and Indigenous history

The final removal of the Potawatomi from Chicago occurred in **August 1835** — inside the
project's first target year. It is the most historically significant event of that year.

- **Do not improvise Native presence, representation, dialogue, or depiction.** This is not a
  research gap to be filled by inference; it is a subject requiring consultation.
- The Newberry's Indigenous Chicago curriculum is the starting point, and the project should
  seek review from Native scholars or community organizations before shipping any depiction.
- **Until then, v1 ships no human figures at all** — uniformly, not selectively. Build the
  built environment accurately and leave human depiction out of scope. An empty, accurate town
  is honest. A populated, invented one is not.
- `review_required: true` on any record blocks a scene from being marked `released`.
- **A flagged record says why, in its own words.** `tools/measure_review_constraint.py`
  asserts that every record carrying the flag refers to it somewhere in its own prose AND
  names the subject it is held for, and prints the sentence it matched under each id. A
  bare boolean tells the next reader that a decision was made and nothing about what it
  rests on (T-0025).

Note also that the great Potawatomi gathering and the last war dance are **August 1835**,
weeks after the 1835 scene date. Staging them in the 1835 scene would be wrong twice over.

**Owner ruling, 2026-09-17, verbatim:** *"i think it is fair, in fact required to Reconstruct
Native or Métis people as part of this. There are some that are certainly in the area
potentially doing business i believe there were indian businesses and it is also very important
that we keep and capture and identify the black owned businesses and residents and family
households."* So, for the 1835 DATA layer (cards, households, businesses, camps): Native and
Métis people are reconstructed, evidence-bounded, through one ticket (T-1177) and its stage of
the resident writer only; every such record carries `review_required` + `touches_removal` with
its sentence, and the review by Native scholars or community organisations is still sought
before a scene is marked `released`. Unchanged: L1 (no human figure is drawn, for anyone), no
invented dialogue, ceremony or depiction, and the August gathering is not staged. Black
residents, families and Black-owned businesses are identified on a `community` field so the
town can list them.

## THE VISIBLE-PROGRESS RULE — read this before choosing a parcel

**Measured 2026-08-15, on the owner's report that the loop "just does organization and research
and not actually applying to the application": 15 of the last 30 changelog entries say nothing
you can see changed, and v124 to v137 is FOURTEEN CONSECUTIVE invisible runs.** That is not a
drift, it is a streak, and it is the loop optimising for what this project praises. The culture
here rewards measurement, refutation and honest gates — rightly — and the result is an agent that
would rather find a defect in an instrument than put a building in the town.

**So: a run must change something a visitor can SEE, and "see" means in the 3-D scene or on a
card a visitor opens.** A new gate is not visible. A corrected metric is not visible. A source
record is not visible. A refactor is not visible. All of those are real work and this project
needs them; they are not what a run is FOR.

**The three exemptions, and they are the only three.**

1. **An owner-reported bug.** Fixing what the owner reported always outranks this rule.
2. **The second half of a split whose first half was a measurement** — the R-BUG3c-a → R-BUG3c-b
   shape, where landing the measurement red before the fix is what stops the fix redefining
   success. The measurement half is exempt ONCE; the run after it must land the fix or say why.
3. **A gate that is BLOCKING a visible parcel** — not one that would be nice to have. Name the
   parcel it unblocks in the PR, or it is not this exemption.

**The cap: at most ONE invisible run in any four.** If the last three merged changelog entries
open with "Nothing you can see" — the phrase is the tell, so search for it — the next run MUST be
visible, and the exemptions above do not extend it. If everything at the top of the queue is
invisible, that is a fact about the queue and the run's job is to fix the queue: pull a visible
parcel up and say in the PR why it was buried.

**How to tell before you start.** Ask: when this merges, what will be different in a screenshot
taken from the same spot? If the honest answer is "nothing", you are on an invisible parcel and
you need one of the three exemptions, in writing, in the PR body.

**And do not make a run visible by writing the changelog as though it were.** The entry describes
what changed; if nothing in the scene changed, it says so. Gaming the phrase instead of the work
is worse than the streak.

## What's-New is for the visitor, not the reviewer — a length budget

**Measured 2026-08-15 on the owner's report that What's-New "has gotten excessively verbose". The
drift is monotonic across the whole history and nobody asked for it:**

| entries | items | words | title words |
|---|---|---|---|
| v60–79 | 5.0 | 443 | 11.9 |
| v80–99 | 7.5 | 642 | 16.2 |
| v100–119 | 7.3 | 724 | 21.4 |
| **v120–138** | **8.9** | **790** | **25.7** |

Words per entry up **78 %**, titles up **116 %**, the longest recent entry **984 words**. A
25-word title is not a title.

**It is the same pressure that produced the invisible-run streak.** This project rewards
thoroughness, so an entry that explains more of itself reads as better work. It is not. **What's-New
is read by a visitor who wants to know what changed in the town** — the reasoning, the refutations,
the measurements and the caveats belong in the PR body and `docs/STATUS.md`, which have no length
limit precisely so this one can.

**The budget, enforced by `tools/check-changelog.mjs` on entries from v139:** title **≤ 12 words**,
**≤ 6 items**, **≤ 450 words** total. Over budget warns; over 1.5× fails. The 138 entries already
written are history and are not retro-failed — the rule binds what is added next.

**Cut the entry rather than raising the number.** If a release genuinely needs more, it is usually
two entries or an entry plus a STATUS section, not one longer entry.
## RECONSTRUCTED IS A TIER, NOT A FAILURE — build, then declare

**The owner, 2026-08-15: the loop is "being hesitant and refusing to build because you are being
too cautious about being perfect. It's ok to create things that have some justification and they
can be inferred or even reconstructed based on your analysis."** He is right, and the example he
gave is the shape of it: the trees were not coloured as described because no source stated the
colour, so nothing was done at all.

**That is a misreading of this project's own vocabulary.** There are three tiers, and the third one
exists precisely for this:

- **attested** — a source states it. Cite the source.
- **inferred** — reasoned from evidence about *this particular thing*. Record the reasoning.
- **reconstructed** — **invented within bounds, because the scene needs it and nothing states it.**
  Record what bounded the invention and add a `docs/LIBERTIES.md` entry.

**`reconstructed` is a licence to build, not an admission of defeat.** Six hundred and sixty-five
roofs stand in this town on exactly that footing. A tree with no stated colour is not a reason to
leave the tree grey — it is a reconstructed colour, bounded by the species, the month and the
reference photographs already committed, recorded as a liberty, and BUILT.

**The rule.** When a parcel stalls for want of evidence, the first question is not "may I proceed?"
It is **"what is the lowest tier that honestly carries this, and what bounds it?"** Then build at
that tier and say so. Refusing to build leaves the scene wrong AND undocumented, which is strictly
worse than a declared reconstruction: an invented colour recorded as invented is honest, and a grey
tree nobody chose is not.

**"Blocked on the owner" is for four things only** — rights and licensing, the L1 constraint on
depicting people, spending real money, and a decision that changes what the project IS. **A missing
number is not one of them.** Derive a defensible figure, label it reconstructed, name what bounds
it, and write down what would replace it. There were **seven** parcels sitting on "blocked on the
owner" when this was written; most were missing numbers.

**What does NOT change, and this is the whole reason the tiers exist.** Never claim a source that
does not exist. Never promote a reconstruction to inferred or attested. Never leave an invention out
of `docs/LIBERTIES.md`. The bar was never "only build what is proven" — it is **"never misrepresent
what you built."** Those are different, and the second one is compatible with building a great deal
more than this loop has been building.

**The owner doubled down, 2026-08-18, verbatim: "in general i think you are being too cautious on
adding items to the scene. you are totally fine to be liberal with adding reconstructed items when i
ask for things, you can just label and mark them as such."** He said it while overriding, one by
one, the conservative readings the loop had settled into: only the two attested docks ("you can add
more docks!"), no boats ("you can add boats correct for the era! they would exist"), wagons only at
attested doors ("of course there would be more wagons all over the place in a frontier town"), signs
only where attested ("you need to add more signage … it is fine if they are reconstructions"). The
pattern to learn: **when the owner asks for something, the scene needing it IS the justification** —
build it at the reconstructed tier, label it, record the liberty, and do not ration it to the
attested instances. The rationing instinct is the bug this section exists to fix.

**And the same ruling reaches the frame budget, 2026-08-21, verbatim: "ok to raise the draw
call budget, if you need to make that a user friendly option in settings because it wont work
on some machines but will on others/most then that is ok" — and, immediately after, "or just
raise the budget?"** So: **just raise it.** A performance ceiling is not a claim about 1835 and
it is not evidence; it is a number this project chose, and when a parcel the owner asked for
needs more of it, the number moves rather than the parcel shrinking. Three constraints survive,
and they are the whole of it:

- **Never silently.** The number moves at the place it is defined, with the reasoning written
  there — where the old figure came from and what supports the new one — and the check that
  guards it updated to match, with its justification. That is a conscious re-budget (T-0115's
  acceptance names it as one of the two honest routes) and it is NOT the same act as weakening
  an assertion to make a red go away. Say which one you are doing.
- **`light` is the floor and stays the floor.** The scene-detail control (`full`/`balanced`/
  `light`) IS the "user friendly option in settings" the owner was offering to have built — it
  already ships, so no new UI is wanted. `light` is the tier a weak machine boots into; keep it
  inside its own ceiling and spend new headroom at the tiers above it.
- **Measure, then move.** Raise it because a parcel needs it and you have the number, not
  pre-emptively. A ceiling checked at one camera stand is a spot reading, not an invariant
  (T-0115 item 1, still open).

The pattern is the same one above: **when the owner asks for something, the scene needing it IS
the justification.** Rationing the town to a budget nobody defended is the same bug as rationing
it to the attested instances.

## THE QUEUE — how work is chosen (since 2026-08-17)

**`tickets/` is the single operational answer to "what next".** The owner asked for it
directly: his requests were getting lost inside an 11,000-line ROADMAP, and he could not
reorder priorities without editing prose. Read `tickets/README.md` — it is one page and it
is the contract. The short form:

- **Pick**: take the topmost ticket in `tickets/QUEUE.md` you can actually run (skip
  `needs_bake` on the improve runner, with the skip stated in the PR). `node
  tools/ticket.mjs list --workable` prints the same order.
- **Check it is not ALREADY DONE**: `node tools/ticket.mjs landed` names every workable
  ticket that a MERGED PR names, with the number, the merge instant and the `done`
  command. Git cannot answer this — everything squash-merges, so a merged branch never
  becomes an ancestor of `dev`, and `inflight` therefore reads a finished ticket's cold
  branch as litter rather than as done. T-0429 sat `claimed` at the top of the queue for
  five days that way and a run rebuilt 116 files onto records already on `dev`.
  `inflight` runs this for you. It REPORTS and never fails a gate: the id in a PR title
  is a convention, so read the PR before you close a ticket on it, and treat its silence
  as silence rather than as proof.
- **Claim** in your first commit: `node tools/ticket.mjs claim T-NNNN`. `ticket.mjs
  inflight` shows what other branches are already carrying a ticket number, which is the
  only live view of work the merged files cannot show yet. It reads each branch as
  **live**, **held**, **open_pr**, **recoverable** or **cold**. A branch under
  **open_pr** has a pull request up right now and is printed with its number and labels
  — `hold` there means a run parked that work for the owner on purpose, so do not
  rebuild it, do not take the ticket and do not delete the branch (T-1427). `held` is the
  other one to read carefully: the branch is
  older than a run but the ticket's claim lock still stands, so it is either a run reading
  sources for hours or a run that died after its merge. Check its PR before you take it —
  age alone used to file that branch under "finished or litter", and two runs read cohort
  14 in parallel for it (T-0852). On the runner, `claim` also
  records WHICH Actions run holds the ticket (`claimed_run`) and `done` records the
  INSTANT it finished (`closed_at`), so BOARD.md can show what is being worked now and
  what finished in the order it finished. Neither is ever hand-written.
- **A CLAIM IS A LOCK, AND IT IS TAKEN ON THE REMOTE** (owner, 2026-09-11: *"can you
  prevent duplicate claiming going forward?"*). `claim` pushes a marker branch
  `claim/t-NNNN` before you do any work, and the push is a compare-and-swap the GitHub
  server decides — two runs claiming in the same second cannot both win. **If it tells
  you the ticket is already claimed, it is: take the next workable ticket.** That
  message is not advisory and `--force` is not the way past it.
  - This exists because six open PRs on 2026-09-11 were six runs working tickets another
    run had already finished. Claiming EARLIER is no protection: T-1008's loser claimed
    an hour BEFORE the winner. A claim reaches `dev` only when its PR merges, so until
    then every other run reads the ticket as `open` — which is why this check does not
    read `dev`, and why the branch scan could never have caught it (a run does not push
    for about an hour after it claims).
  - A claim older than 3h is a dead run and is **stolen automatically**, so a crashed
    run cannot strand a ticket. `--no-lock` is for a checkout with no remote; it is not
    a way past a live claim. `ticket.mjs claims [--sweep]` lists the locks held and
    deletes the stale ones.
  - Unreachable remote, no credentials, no git? The claim **succeeds and says so**. The
    lock never turns a network blip into a dead slice.
- **Close** in the merging PR: `node tools/ticket.mjs done T-NNNN --pr N`. Blocked instead?
  `block --owner "the question"` — the question goes in the ticket, where the owner will
  actually see it, not only in a PR body. **Closing after `publish.sh` is fine**: the tool
  carries `tickets.json` to the published mirror itself, so the order below — publish,
  push, PR, close with the number the PR just got — ends green with no second publish
  (T-0154; before it, that order left the mirror gate red every time — and since
  T-0938 the mirror is not committed, so no order of operations can leave a stale one
  in a PR at all).
- **The build products are GENERATED AND UNTRACKED, so there is nothing to stage**
  (T-0937 for the board, T-0938 for the rest). `tickets/BOARD.md`,
  `tickets/tickets.json` and the whole of `site/chicago/4d/` are .gitignored. They used to be the repository's worst conflict source, and for a reason
  worth knowing: `claim` is a run's FIRST act and rewrites all three, so two branches
  conflicted before either had done any work — and GitHub's server-side merge runs none of
  this repo's merge drivers, so `merge=generated` never reached the merge that decides
  mergeability (T-0857). Untracked files cannot conflict. Everything that needs one builds
  it: `ticket.mjs check`/`board`, `publish.sh` before its copy, `deploy.yml` before the
  Pages upload. **Never `git add -f` them**; if one shows in `git status`, the ignore rule
  is the fault.
- **New work found mid-run: extend, place, or make it an epic — in that order** (owner,
  2026-09-10, after the queue reached 195 lines: *"I don't want you to keep adding a whole
  bunch of tickets below your current one and working them … I want fewer tickets to
  work"*). First, **if an open ticket already owns the question, add the finding to it**
  and file nothing. Second, if it is a real one-run piece of the goal, `ticket.mjs new
  "title" --after T-NNNN` places it directly under the ticket it serves — beside related
  work, not at the foot. Third, **if finishing would take more than five tickets, it is an
  epic**: one ticket under `EPICS` at the foot of QUEUE carrying the list, and no more.
  The loop does not work an epic until the owner promotes it. **Agents never move an
  existing line — only the owner re-ranks.** That is what keeps his priorities durable.
- **An owner ask becomes a ticket the moment it is made**, `--by owner`, before any work
  starts. This is not optional bookkeeping; an owner request going untracked for days is
  the exact failure this system exists to close.
- **Finish your PR inside the run that opened it** — merge on a green gate, or `block`, or
  label it `hold` with the reason. **A claim is only real once its PR merges**: the state
  lives in the ticket file, so an abandoned open PR leaves the ticket reading `open` at the
  top of the queue and the next run rebuilds the same work. It cost about seventy minutes
  on 2026-08-19 (run 943's PR #258 left open, run 944 redoing T-0062 as #259). `claim` now
  checks `git ls-remote` for a rival branch carrying the ticket's number and refuses with a
  `--force` escape — but that only protects the NEXT run; finishing the PR is your half.
- **Size in RUNS before you claim.** `XS` part of a run · `S` one run · `M` one run,
  tight (or one run plus a bake) · `L` **more than one run, and `claim` refuses it**.
  The test is the acceptance clause: *if it needs more than one demonstration, it is
  more than one ticket.* Split with `ticket.mjs split T-NNNN "piece" "piece"` — the
  children inherit the parent's exact place in QUEUE, so a split never re-prioritises.
  If a run discovers mid-flight that its ticket is bigger than one demonstration, it
  splits rather than shipping a self-invented "(1/2)".
- `tools/check.sh` runs `ticket.mjs check`: duplicate ids, queue drift, stale BOARD, a
  block with no stated question, an `L` in the queue — all merge-refusing.

**`docs/ROADMAP.md` is no longer the backlog.** It remains the *reasoning archive* — the
parcel boxes hold measurements, refutations and acceptance clauses that tickets link into,
and nothing there is deleted. Its NEXT UP table is tombstoned with a pointer here. STATUS.md
remains the honest narrative of what shipped; the *state* of work lives in tickets alone.

## The work-parcel contract

Work is parceled so parallel agents never collide. If you are a subagent:

- **One file per source, one file per structure, one file per zone.** Your parcel's outputs are
  disjoint from every other parcel's by construction. Do not restructure shared files.
- **Writing agents get their own git worktree.** A shared checkout across parallel agents has
  produced false alarms and lost work in this fleet before.
- Your parcel is done when `tools/check.sh` passes and your outputs carry their provenance.
- Do not run Blender unless your parcel changes geometry-affecting data. Bakes are batched.

## The two-speed build

| | `tools/check.sh` | `tools/bake.sh` |
|---|---|---|
| when | every commit, every sandbox | on demand + nightly |
| needs Blender | **no** | yes, pinned (`generators/blender.pin`) |
| runtime | seconds | minutes |
| does | schema, provenance, date gates, referential integrity, licenses, archetype params, staleness, JS parse, publish sync | generate → UV → bake AO/normals → GLB → web derivatives → sidecars → publish |

Agents consume committed GLBs. A stale committed GLB is a check failure, not a warning.

## How work ships

**Read `docs/PIPELINE.md` first.** Since 2026-08-14 this app runs a two-tier
**`dev` → `main`** pipeline on the owner's instruction: *overnight work must not ship
straight to production.* The fleet pilot is `kevinrhaas/jobtracker.polecat.live` →
`docs/PIPELINE.md`; ours is the two-tier form of it.

- **Branch `steward/<topic>` off `dev`. PR into `dev`. Merge when the dev gate is green.**
  Never push to `dev` or `main` directly. Ambiguous or unverified work stays an open PR
  with the `hold` label and a written explanation.
- **A `steward/*` PR THAT CANNOT MERGE IS NOT OPEN — IT IS ROTTING.** Its ticket still
  reads `open` at the top of the queue, so the next slice picks the same row and rebuilds
  the same work. Measured 2026-09-13 (T-0809): **all five** open steward PRs on `dev`
  conflicted with it — #1210, #1231, #1239, #1242, #1252 — every one of them on
  `renderers/web/js/changelog.js`, `tickets/QUEUE.md` or `tools/dev-smoke-state.json`,
  and the janitor had swept and silently skipped all five every two hours. Twenty-one had
  silted up the same way in 2026-09: 21 open, 21 conflicting, six build products between
  them, five past saving. Two things follow, and both are now true:
  - the janitor **gates the merge, not the bare branch, and comments once naming the
    conflicting paths** on any PR it cannot merge (polecat-platform#161). If your PR is
    rotting you will be told inside one sweep; rebase it on `dev` or label it `hold`.
  - those three files conflict on nearly every landing BY DESIGN — the root
    `.gitattributes` refuses to union-merge the changelog because union silently
    corrupted it on five consecutive merges in one day. So expect to rebase, and **finish
    the PR you open inside your own run** rather than leaving it to be swept.
- **Merging into `dev` is STAGE, not ship.** It publishes only the integration preview at
  `/custom/chicago/4d/dev/walk/?year=1835` — noindex, banner-marked, `build.json` says
  `tier: dev`. Production is untouched.
- **Production moves ONLY when the owner dispatches `chicago-4d-promote-to-prod.yml`.**
  No schedule, no agent. `walk/` changes reach `main` by that dispatch and no other route.
  The hotfix exception stands: a production emergency PRs straight into `main`, and the
  next promotion's back-merge folds it into `dev`.
- **Scope is `chicago/4d/` and its published mirror `site/chicago/4d/`. Nothing else.**
  `kevinrhaas/custom` is a monorepo of unrelated personal projects — CAD, print models,
  the Joliet game, a landing site. A run that edits any of them is out of bounds, and the
  workflow files are outside scope too: changing one needs an interactive, owner-visible PR.
- **Before you re-run a stage to find out whose red it is, ASK THE RECORD**: `node
  tools/dev-smoke-state.mjs ask --viewport desktop --stage 8` answers "was dev already red
  here, and when did it last pass" from `tools/dev-smoke-state.json` without running
  anything, and says whether the reading was taken on your exact tree. Four runs re-derived
  the same two reds by hand on 2026-08-27 for want of it (T-0215, T-0216). File the smoke
  you ran anyway: `node tools/dev-smoke-state.mjs record <log>`.
- **Before you spend the run's budget on the smoke, ASK WHAT IT COSTS AND WHAT YOU
  NEED**: `node tools/smoke_budget.mjs --for-diff` names the parts that cover your own
  diff and prints the commands, each packed under the 600 s foreground ceiling, with the
  measured margin — read out of the same record above, never asserted. With no arguments
  it prints what the whole gate costs on this machine, against the 90-minute whole-body
  cap; `--legs` prices the nightly gate's eight parallel legs against the 30-minute
  PER-LEG cap, which is a different bound and the one three tickets correctly reason
  against (T-0450). `docs/SMOKE-BUDGET.md` is the page (T-0235). And redirect
  a smoke to a FILE, never a pipe: node block-buffers stdout to a pipe, so a piped log
  stays at zero bytes until the process exits, and a run once killed a green smoke one
  minute from its finish for want of a byte to look at.
- **`./tools/preflight.sh` BEFORE you open the PR.** `check.sh` is not the whole gate:
  two of CI's questions are asked only on the pull_request event, where a base ref
  exists, so a run cannot rehearse them and finds out after the PR is open — when its
  turn has ended and nobody comes back. PR #1049 sat red for 2 h 19 m on a one-line
  commit trailer, with the right sentence written in its PR body where the gate does
  not look. Preflight asks all three in one command: `check.sh`, then
  `check-changelog-entry.mjs` against the merge base, then
  `resolve_id_collisions.mjs --check` (a sibling slice may have taken a ticket id
  this branch minted while you were working). It writes nothing and names the repair
  for each red. `BASE=origin/main ./tools/preflight.sh` for the hotfix path.
- **Both gates, in the foreground, before merging**: `tools/check.sh` (`pip install
  jsonschema pyproj openpyxl pypdf numpy scipy Pillow` — the last three are what let
  thirteen steps RE-READ their rasters instead of standing on a banked copy; without
  them the gate warns and degrades, and CI, which sets `C4D_GATE_REQUIRE_READERS=1`,
  goes red. `tools/check_gate_readers.py` holds the list, T-1083) and `node tools/smoke_renderer.mjs` (Playwright, 390×780 AND 1280×800, zero
  page errors). Mobile is a release gate. **Never weaken an assertion to pass.** The
  `--published` run is the one that matters: the source tree loads uncompressed masters and
  the site loads compressed derivatives, and bugs have shipped in the gap twice.
- **You no longer publish in the same commit — `site/chicago/4d/` is not committed at
  all (T-0938).** The mirror is a build product with one writer, `tools/publish.sh`,
  and it is untracked and .gitignored. `tools/check.sh` runs publish.sh first and then
  asks `check_published.mjs` whether what it produced matches its source; `deploy.yml`
  publishes both the production tree and the dev-preview worktree before the Pages
  upload; `chicago-4d-bake.yml` publishes before it uploads the mirror the smoke runs
  against. So the URLs are unchanged and a run that forgets to publish can no longer
  ship an invisible change — there is nothing left for it to forget. Run publish.sh
  when you want to LOOK at the published tree (`--published` measurements, a local
  serve); the gate runs it for you either way.
  `site/chicago/4d/` is a generated mirror and `deploy.yml` only fires on `site/**`, so
  skipping it ships nothing while looking merged.
- **Changelog**: prepend one entry to `renderers/web/js/changelog.js` with all three
  authored fields blank — `v: null, ts: '', date: ''` — then run
  `node tools/stamp-changelog.mjs` and `node tools/check-changelog.mjs`. **Stamp BEFORE
  merging to `dev`; nothing stamps later in the pipeline.**
  - `date: ''` must be *present*: the stamper fills an empty `ts` but only *regenerates* a
    `date` that already exists, so an entry authored without the key fails the contract check.
  - `v: null` because the number is not yours to guess. Two branches that each compute
    "top + 1" both get it wrong, and the second to merge ships a duplicate — that cost three
    manual renumbers on 2026-08-10 alone. The stamper assigns it; `.gitattributes`
    (`merge=union`) keeps the merge itself conflict-free.
  - **Re-run `check-changelog.mjs` AFTER any merge that touches this file, not only before.**
    `merge=union` runs during the merge, so both parents can be green and the result broken —
    that is exactly how `main` shipped an unparseable changelog on 2026-08-13, killing the
    What's-new tab and this project's release feed to Manager and the launcher.
    `tools/check.sh` runs the contract check as a step, so a plain `./tools/check.sh` after
    merging covers it.
  - Nothing stamps after merge. The file is authored inside the app because the What's-new
    tab imports it; `publish.sh` mirrors it to `site/chicago/4d/js/changelog.js`, the URL
    Manager and the polecat.live launcher parse live, which must not move — and to
    `site/chicago/4d/walk/js/changelog.js` inside the copied renderer tree.
  - **Stamping after `publish.sh` is safe (T-0155).** Both mirrors are compared byte for
    byte by `tools/check_published.mjs`, and the stamper rewrites the source, so that order
    used to leave the gate red with no documented remedy but a remembered second publish.
    `stamp-changelog.mjs` now carries both mirrors itself, on a real rewrite only — a mirror
    somebody else made stale still fails, which `tools/test_changelog_mirror.mjs` asserts in
    `check.sh`. You may still publish last; you no longer have to.
- **No Blender on the improve runner, and do not install one.** Geometry comes from the
  nightly `chicago-4d-bake.yml`, which branches off `dev` and **opens its PR into `dev`**.
  A unit that needs new geometry ships the data/archetype half and says so.
- **`docs/ROADMAP.md` is the backlog and `docs/STATUS.md` is the honest state** — update
  both in the same PR as the work. `docs/RENDERING.md` is the active rendering program;
  its phases are claimed the way ROADMAP parcels are.

## Honesty rules

- `docs/LIBERTIES.md` is append-only. Every compression and invention gets recorded. The
  standard: *a visitor should be able to tell you which parts we made up.*
- `docs/STATUS.md` states what is unverified. Do not describe a gate as passed if it was skipped.
- Where sources disagree, record the disagreement in `docs/RESEARCH/<id>.md` and pick the
  best-attested reading **with reasoning** — never silently choose.
- No model identifiers in repo artifacts.

## Orientation

`docs/PLAN.md` is the full development plan. `docs/research/` holds the source dossiers
(committed verbatim, tagged, with their own gaps stated). `docs/PROVENANCE.md` expands the
confidence model. `docs/EPOCHS.md` explains the temporal architecture.
