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
9. **`tools/check.sh` passes before every commit.** No Blender. **A run takes it in four
   parts, `./tools/check.sh --part 1/4` through `--part 4/4`, one foreground call each**
   (T-3299): whole, it was about nineteen minutes of pool on four cores on 2026-11-01, so
   a bare call is cut off at the 600 s cap with no verdict. The parts are a partition of
   the same steps, and each one publishes the mirror for itself. All four green is the
   gate green; one part's `CHECK PASS — part k/4` is not, and it says so. CI runs it
   whole. It runs its steps in a pool sized to the machine (`CHECK_JOBS`, on by
   default since T-1578 — it was serial everywhere but CI, where a 620 s gate no longer
   fit the 600 s a run's single foreground command gets, so a run got no verdict at all).
   `CHECK_JOBS=1` is the serial escape hatch, for reproducing one step's red on a quiet
   tree. **Each part has to keep fitting that ceiling**: the next step that costs a minute
   is made cheaper, moved to `tools/bake.sh`, or argued for in check.sh's header, and when
   a part passes about 540 s the count of parts goes up rather than the bar going down.
   **Read its last four lines, not its middle.** 264 of its 628 steps are self-tests that
   prove a gate by breaking it, so a GREEN run prints `FAIL` lines on purpose.
   Those are tagged — every line of a self-test's transcript starts `   self-test | ` —
   and the steps that actually failed are listed once, by label, under `CHECK FAIL` at
   the end. An untagged `FAIL` is the only kind worth chasing. Three tickets were filed
   against tagged ones before T-0763; do not make a fourth.
10. **A reader of the platted grid says which of its two lines its answer stands on.**
   The **drawn** centreline in `data/streets/1835.json` is the block grid's own control —
   `generate_plat_lots.block_edges` offsets it by the platted half-module — and the
   **control** line is that corridor re-centred onto the street's committed survey control.
   On `south_water` they disagree by 8.58 m and on `kinzie` by 2.91 m, and the owner ruled
   on 2026-09-21 (T-0419) that the block grid is NOT re-cut onto the control: they answer
   two different questions and neither is the other's control. So a question about a block,
   a lot or a roof is asked on the drawn line; a question about where the PLAT put the
   roadway is asked on the control line; and any module calling `corridors`,
   `control_offsets`, `intrusion` or `block_edges` carries `CORRIDOR_LINE` and
   `CORRIDOR_LINE_WHY` saying which and why. `tools/check_corridor_line.py --gate` refuses a
   reader that does not declare, or whose declaration disagrees with its own calls; it reads
   the syntax tree, so naming a line in prose is discussing it and not taking it.
   `docs/CORRIDOR-LINES.md` is the ruling and the disagreement it declined to resolve.
   **Do not "fix" the disagreement by moving the lot grid** — that was priced at 32 lots
   re-cut, 53 committed roofs and a whole documented block into the river, and refused.

11. **A building with a picture of it is built to match the picture, and its ticket does not
   close until it does** (the image gate, T-2368). The owner, 2026-10-11, finding 1612 Prairie
   built from a Sanborn outline while the library linked its photograph: *"if you have an image
   you should work towards it until it's a photographic representation of any images, even
   drawings are ok, but it should look exactly perfectly like the image or drawing"*, and *"you
   don't wrap the case until it matches the photo, not that you can't change one without a
   photo"*. So before drafting, refining or rebuilding any building, find every photograph,
   print and drawing of it (the Prairie library, `data/sources/`); solve each one's camera into
   `data/reference_views/<structure_id>/`; build; render with `node tools/photo_match.mjs`; and
   work the differences down until the side-by-side shows none in what the picture shows. A
   building ticket carries an `## Image gate` section naming its structure ids, and
   `ticket.mjs done` refuses it while any view is not `matches`; a split ticket's gate is asked
   by its last piece to close (2026-10-28: 1729 Pullman closed through twelve pieces while its
   records said `differs`). A summary of a picture is not the picture: read the image itself. `data/reference_views/README.md` is the page.

   **…and it stops at what a visitor would notice** (the photo-ticket stopping rule, T-3153).
   The owner, 2026-10-25: *"you keep going on with creating tickets in an almost never ending
   fashion ... you need to help me with not creating more and more tickets when there are
   probably some seriously diminishing returns"*. Glessner had taken 115 tickets since the
   gate opened, fixed 110 differences and left 9, mostly under a foot or a few pixels, and
   its sign-off had been re-filed five times. He chose the full rule:
   - **A good-enough bar.** A difference is `open` only if a visitor on the street would
     notice it: more than about 1 ft (0.3 m) off in size or place, an element missing or the
     wrong shape, the wrong number of bays, openings or stacks, or the wrong material or
     colour. Anything smaller, any pixel offset, and any gap two pictures or two camera fits
     disagree about is `within tolerance`, which does not block `matches`.
   - **Runs file no photo follow-ups.** A gap found on a photo-gated house (one with a folder
     in `data/reference_views/`) goes into that view's match record, never a new ticket;
     `ticket.mjs new` refuses any filing that is not `--by owner` and names such a house
     (a performance follow-up, or one placed with `--blocks` because dev's gate is red,
     still files). Only the owner opens new work on it, and `--by owner` means he asked.
   - **One sign-off, never split.** A house's sign-off finishes in its own run: it marks what
     is under the bar `within tolerance`, fixes what is over it in the same PR if that fits,
     and writes the rest into the discrepancy register. `split` refuses a sign-off.
   - **A cap.** A house past 25 tickets since 2026-10-11 takes new ones only from the owner,
     and a photo-gated one past it is not split. `split … --owner-asked "<his words>"` is the
     only way past either, and writes his words into every piece. Ship what fits and
     `release` the rest instead.

12. **A structure's own grade says whether we know what it looked like** (T-2686). The owner,
   2026-10-16: *"for a structure if there is an image of it that is reasonable, not just like a
   corner or side ... that is attested, something inferred would be like we only have the sanborn
   map level description, or some text description of it, but nothing to visually depict its size
   or scope or appearance, and then reconstructed will be where we made a determined choice that
   there should have been [one], based on model of town or other guiding research"*. So every
   structure carries one `grade` beside its per-attribute grades, which it never overrides:
   **attested** when a reasonable picture of it exists (a photograph, print or drawing showing it
   whole — front, oblique, side or rear — or any picture an image-gate camera is solved on);
   **inferred** when a map or a text records it and no picture shows it (a Sanborn footprint alone
   is inferred); **reconstructed** when it is unpictured and our model of the town placed it.
   A detail, an interior, a plan, or a street view the building stands in the corner of does not
   attest it. The grade is derived, never typed: `tools/grade_structures.py` is the rule,
   `data/structure_grades.json` holds the rulings it cannot make itself (each with its reason), and
   `compile_scene.py` writes it into the sidecar, so adding a picture or solving a camera means
   compiling again in the same change. **A street drawn on a plat or survey of its time is
   attested** — a map is the picture of a street's line and width (the owner: *"for 1835, all the
   streets should be attested"*). `docs/PROVENANCE.md` § "The grade of a structure" is the page.

## Standing constraint — 1835 and Indigenous history

The final removal of the Potawatomi from Chicago occurred in **August 1835** — inside the
project's first target year. It is the most historically significant event of that year.

**Owner ruling, 2026-10-16, verbatim:** *"I think human figures are ok once we are able to render them and go through those tickets"*

**Owner ruling, 2026-10-16, verbatim:** *"And I think ok to for native and Métis depictions based on your fair and reasonable judgement, you have been careful and I trust you to make informed and reasonable depictions"*

- **L1 is lifted for the portable-humans path.** Figures may be drawn once the portable-human
  pipeline renders them, uniformly for everyone. Use the portable-human asset, provenance,
  scene-date and rendering contracts; a placeholder bypassing that path is not a shipped figure.
- Native and Métis depictions use informed, fair and reasonable judgement. The Newberry's
  Indigenous Chicago curriculum and committed research remain the starting point. Depictions
  are evidence-bounded; thin evidence is declared `reconstructed` and entered in
  `docs/LIBERTIES.md`. No invented dialogue or ceremony is presented as attested.
- `review_required` and `touches_removal` remain on records with their own explanatory prose.
  **They do not block a scene from being marked `released`** — owner, 2026-10-16, when asked
  whether the trust ruling lifts that block too: *"Yes lift that"*.
- **A flagged record says why, in its own words.** `tools/measure_review_constraint.py` still
  holds flag presence, propagation and explanatory prose. A bare boolean does not explain the
  care taken; no flag is silently cleared to implement this ruling.
- The great Potawatomi gathering and last war dance are **August 1835**, after the **1 July
  1835** scene date, and are not staged in it. All other scene-date and source rules stand.
- Black residents, families and Black-owned businesses remain identified on `community`.

**Owner ruling, 2026-09-17, verbatim:** *"i think it is fair, in fact required to Reconstruct
Native or Métis people as part of this. There are some that are certainly in the area
potentially doing business i believe there were indian businesses and it is also very important
that we keep and capture and identify the black owned businesses and residents and family
households."* The 1835 data-layer reconstruction through T-1177 retains its evidence and review
flags. Its former figure prohibition and consultation prerequisite for release are superseded
by the explicit 2026-10-16 rulings above; the historical research and flag reasons remain.

**Owner ruling, 2026-10-13, verbatim** (project thread "1812 structures", T-2490): *"You can
include native lodges as documented"*. Potawatomi lodges stand where and when a source puts
them, in documented mat or bark forms, never a generic tipi. Every lodge record retains
`review_required` + `touches_removal` and its own reason. The former consultation release block
is superseded by the 2026-10-16 ruling. No August gathering is backdated into a July scene.

The owner's 2026-10-18 transport request includes period-clothed drivers, riders,
people standing near horses/carriages and walking streets at photographic quality.
Later steering prioritizes existing attested, inferred or reconstructed people as
references/models; anonymous people are a fallback only when no suitable existing
person can be used. Preserve each existing identity's grade and scene date, and
declare reconstructed appearance/actions without asserting an archival likeness.
That work does not manufacture cultural evidence or stage a ceremony; photographic
quality remains a production acceptance gate, not a label for an articulated fixture.

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

**"Blocked on the owner" is for four things only** — rights and licensing, a depiction outside the owner-authorized
evidence-bounded scope, spending real money, and a decision that changes what the project IS. **A missing
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
- **And take the number BEFORE the parcel deals, not after it bakes** (T-1674). The
  reading at the end of a parcel says what was spent; it cannot say what there was to
  spend, so a parcel on a thin margin discovers a breach with the deal, the generators
  and the bake already behind it. `node tools/measure_detail_ceilings.mjs --price` prices
  the headroom at each tier's own tightest stand into a count of roofs per archetype
  family — the family footprint read from the GLB each roof ships as, the sun's second
  draw measured at the stand — and `--deal D3=6,C2=2` answers a proposed parcel with
  FITS or BREACHES. `--from <a --json reading>` re-prices a reading already taken, with
  no browser. It moves nothing: a raise is still argued here, on the three constraints
  above, and this only puts the number in front of the decision instead of behind it.

The pattern is the same one above: **when the owner asks for something, the scene needing it IS
the justification.** Rationing the town to a budget nobody defended is the same bug as rationing
it to the attested instances.

## THE QUEUE — how work is chosen (since 2026-08-17)

> **SINCE 2026-09-23 THE TICKETS ARE THEIR OWN REPOSITORY — read this first; it
> supersedes the claim-lock and close mechanics described below.** This project moved
> out of kevinrhaas/custom into **kevinrhaas/chicago** (chicago.polecat.live/4d/), and
> `tickets/` became a clone of **kevinrhaas/chicago-tickets** — gitignored here, fetched
> by `bash tools/tickets.sh` (which `check.sh` and `publish.sh` run). Tickets sit in
> folders of 250 (`tickets/T-1500-1749/T-1519-….md`); `tickets/QUEUE.md` is unchanged.
>
> - **Every `ticket.mjs` change is committed and pushed straight to that repo's `main`.**
>   A code PR never contains a ticket file or QUEUE.md, so it cannot conflict on them —
>   the conflict source this section's history keeps returning to is gone.
> - **`claim` is the pushed commit.** Every other run sees it on its next pull; two
>   runs racing for one ticket cannot both push it (the loser is told, and takes the
>   next one). A claim older than 3 h is a dead run and is stolen. There are no
>   `claim/t-NNNN` marker branches in this mode.
> - **`done --pr N` sets `review`**, not `done`. The tickets repo's settle workflow
>   marks it `done` (and removes its queue line) when the PR MERGES, or reopens it if
>   the PR is closed unmerged. So a ticket cannot read done for work that never landed.
> - **A question only the owner can answer stays in the queue**: `ticket.mjs ask T-NNNN
>   --question "…" --option a="…" --option b="…" --rec a --why "…"`. The ticket keeps
>   its rank with `decision: pending`, a `## Decision needed` section and a
>   `#   ? T-NNNN DECISION:` line under its queue entry; `list --workable` and `claim`
>   skip it until it is answered (on Manager's 4D Board, one click). Prefer this to
>   `block --owner`, which took the ticket out of the queue where nobody saw it.
> - Edited a ticket body by hand (a finding added)? `node tools/ticket.mjs sync -m "…"`.
> - **A command commits only what it was asked to change** (T-2280). Every other mutating
>   command refuses while the clone holds a local edit to a ticket it does not name, and
>   lists the files: publish them with `sync -m`, or `git -C tickets stash` them. Before
>   this, `pushTickets`' `git add -A` published them under the command's own message —
>   `done T-1205` (b679d90) reverted a scratch copy of T-1171 to `claimed` for a week.
> - **Bulky evidence goes to kevinrhaas/chicago-evidence, never to the tickets repo**
>   (owner, 2026-10-23, T-3071). Checkpoint folders, tar/zip snapshots, gate and smoke
>   transcripts, solver dumps and screenshot runs grew chicago-tickets' `evidence/` to
>   2.4 GB in five days, and every gate and steward run cloned it (it also ran runners out
>   of memory, T-3069). Commit them to `evidence/<topic>-<date>/` in chicago-evidence (a
>   separate clone; nothing in CI clones it) and cite the path from the ticket. A small
>   text file a tool reads (the T-1837 frontage register) may stay in `tickets/evidence/`.

**`tickets/` is the single operational answer to "what next".** The owner asked for it
directly: his requests were getting lost inside an 11,000-line ROADMAP, and he could not
reorder priorities without editing prose. Read `tickets/README.md` — it is one page and it
is the contract. The short form:

- **Pick**: take the topmost ticket in `tickets/QUEUE.md` you can actually run (skip
  `needs_bake` on the improve runner, with the skip stated in the PR). `node
  tools/ticket.mjs list --workable` prints the same order. That ticket is your ANCHOR;
  § A RUN MAY TAKE A GROUP below says when to add up to four more to it.
- **Skip a LIVE claim, not a dead one** (T-1612). `list --workable` prints each claim's
  age — `claimed 40m` — and a claim older than the three-hour run window as
  `TAKEABLE dead claim 10h`: a run that died. That row is workable in its queue place
  and `claim` steals it without `--force`; the verdict on the line and the one `claim`
  enforces are the same function. T-1444 sat at the top of its band for 131.8 hours
  reading `claimed` because nothing on the line said so.
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
  only live view of work the merged files cannot show yet. Both also read the OPEN PULL
  REQUESTS by title (T-2138): a PR titled `T-NNNN: …` carries its ticket whatever its
  branch is called, so `claim` refuses it — a dead claim included — and `inflight` lists
  it under the ticket; #449 on `claude/project-thread-*` was invisible to both, and a
  slice rebuilt T-2122 in full beside it. It reads each branch as
  **live**, **held**, **open_pr**, **recoverable** or **cold**. A branch under
  **open_pr** has a pull request up right now and is printed with its number and labels
  — `hold` there means THE OWNER is deciding, so do not rebuild it, do not take the ticket
  and do not delete the branch (T-1427); `resume` there means a RUN could not finish and
  the work is waiting for one that can, so do not rebuild it either — **finish it**
  (§ the two labels). `held` is the
  other one to read carefully: the branch is
  older than a run but the ticket's claim lock still stands, so it is either a run reading
  sources for hours or a run that died after its merge. Check its PR before you take it —
  age alone used to file that branch under "finished or litter", and two runs read cohort
  14 in parallel for it (T-0852). On the runner, `claim` also
  records WHICH Actions run holds the ticket (`claimed_run`) and `done` records the
  INSTANT it finished (`closed_at`), so BOARD.md can show what is being worked now and
  what finished in the order it finished. Neither is ever hand-written.
- **A PARKED PULL REQUEST IS ON THE BOARD, WITH THE REASON IT WAS PARKED FOR** (T-1576).
  The lap, `merge-ready.sh` and `pr-stuck.sh` all read labels before they read state and
  all skip `hold` on purpose, so a parked PR is by construction the one kind nothing is
  coming back for — and until now its reason lived only in the PR body. The owner, on
  2026-09-25, finding three at once: *"that seems like a bad move because i am not aware
  of why they are held"*. So `ticket.mjs board --parked` reads the open pull requests and
  puts every one carrying `hold` or `resume` at the TOP of BOARD.md with its ticket, its
  age, how long since it was last touched, and its reason. The settle workflow passes
  `--parked`; `publish.sh`, `pr-lap.sh` and the merge driver do not, and stay offline.
  * **The reason is read, never composed.** T-1573's structured line
    (`resume: <reason> · waits on: <ticket or "nothing">`) in a PR comment first —
    newest wins — then the same line in the body, then the body's own
    `### Why this is on \`hold\`` section. A PR that wrote none is listed saying
    **no reason written on the PR**, which is a true statement about it and is not
    papered over with a guess. `waits on` is carried only where a run named it.
  * **An unread list is not an empty one.** When the PR list cannot be read — a rate
    limit, a 404, no network — the section says **NOT READ** in those words. An empty
    section and a failed call print identically otherwise, and that silence is the
    fault the whole reading was filed against. `tools/test_ticket_parked.mjs` holds it.
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
- **Close** in the merging PR: `node tools/ticket.mjs done T-NNNN --pr N` (a group:
  `done T-A T-B T-C --pr N`, all or nothing). Blocked instead?
  `block --owner "the question"` — the question goes in the ticket, where the owner will
  actually see it, not only in a PR body. **Closing after `publish.sh` is fine**: the tool
  carries `tickets.json` to the published mirror itself, so the order below — publish,
  push, PR, close with the number the PR just got — ends green with no second publish
  (T-0154; before it, that order left the mirror gate red every time — and since
  T-0938 the mirror is not committed, so no order of operations can leave a stale one
  in a PR at all).
- **`done` REFUSES TWO THINGS, and both are cheapest to fix where you are standing.**
  A committed file that still records *this* ticket as live work (T-1548), and — since
  T-1581 — a close that would strand an ANCESTOR of it. A job that was cut up stands as
  a `split` heading over its pieces and is live exactly while some descendant is; take
  its last one and every research unit, ruling and work order pointing at the heading is
  waiting on nobody. That red always lands on the NEXT run, because `done --pr` only sets
  `review` and the tickets repo settles it to `done` when your PR merges — so your own
  gate read it as live. Three closes did it on 2026-09-25 (#40 on T-1189 two levels up,
  #43 on the re-family programme, #49 on 272 landholdings). Ask it yourself at any time:

      python3 tools/ticket_liveness.py --closing T-NNNN   # what this close would strand
      python3 tools/ticket_liveness.py --report           # what is ONE closure away

  `check.sh` asks it of the tickets **your branch name carries**, and of nobody else's —
  a PR is never red for a close somebody else is making. Repoint the pointers in the
  same PR, or say why not: `done T-NNNN --pr N --anyway --why "<reason>"`.
- **The walk over a `split` is ONE definition** — `tools/ticket_liveness.py`. The
  research ledger's `split_live`, the order book's `live_pieces_of` and `ticket.mjs` all
  read it; what each keeps is its own LEAF SET, because the ledger wants an *open* owner
  and the order book counts a blocked ticket as live. They had three copies and a fix
  made to one in July had to be made again to another in September; a self-test now
  fails if any of them starts keeping its own.
- **The build products are GENERATED AND UNTRACKED, so there is nothing to stage**
  (T-0937 for the board, T-0938 for the rest). `tickets/BOARD.md`,
  `tickets/tickets.json` and the whole of `site/4d/` are .gitignored. They used to be the repository's worst conflict source, and for a reason
  worth knowing: `claim` is a run's FIRST act and rewrites all three, so two branches
  conflicted before either had done any work — and GitHub's server-side merge runs none of
  this repo's merge drivers, so `merge=generated` never reached the merge that decides
  mergeability (T-0857). Untracked files cannot conflict. Everything that needs one builds
  it: `ticket.mjs check`/`board`, `publish.sh` before its copy, `deploy.yml` before the
  Pages upload. **Never `git add -f` them**; if one shows in `git status`, the ignore rule
  is the fault.
- **The derived research files are tracked, and a merge in a clone clears them with ONE
  command.** Two branches that each touch a citation both rewrite
  `data/sidecars/1835/sources/` (#137 and #130 conflicted there, 2026-09-27). Never
  hand-merge them. Mid-merge, run `node tools/rederive.mjs --resolve`: it takes one side of
  every conflicted file `tools/derived_manifest.json` lists, rebuilds from the earliest
  owning step down, and stages the result. It refuses and touches nothing while any
  authored file is still unmerged, so resolve those first. The PR lap already does this on
  the server; this is the same move for a local merge. `./tools/check.sh` is still the proof.
- **The asset registries merge entry by entry, in the lap and in a clone** (T-2892).
  `assets/manifest.json` and `assets/manifest.web.json` are rewritten whole by every bake,
  so two PRs that baked different houses used to conflict there and wait a whole run.
  Mid-merge, `python3 tools/merge_asset_registry.py --resolve chicago/4d/assets/manifest.json
  chicago/4d/assets/manifest.web.json` takes each entry from the side that changed it,
  re-emits on the merged tree any pure-Python asset (K01, K13, …) whose recipe moved on both
  sides, keeping it only if the GLB is byte-identical, and refuses a master both sides
  rebuilt — that one is still a rebake. The lap runs it when the rest of the merge can clear.
- **New work found mid-run: extend, place, or make it an epic — in that order** (owner,
  2026-09-10, after the queue reached 195 lines: *"I don't want you to keep adding a whole
  bunch of tickets below your current one and working them … I want fewer tickets to
  work"*). First, **if an open ticket already owns the question, add the finding to it**
  and file nothing. **A picture gap on a photo-gated house is never a ticket** (rule 11's
  stopping rule, T-3153): it goes into the match record, `open` or `within tolerance`. Second, if it is a real one-run piece of the goal, `ticket.mjs new
  "title" --after T-NNNN` places it directly under the ticket it serves — beside related
  work, not at the foot. **Since 2026-09-27 a follow-up a run files goes to the FOOT OF
  BAND 9 instead, and `new` enforces it** (owner: *"move loop follow-ups to band 9"*, then
  *"make the ticket tool enforce it"*; the first district build had filed about seven
  follow-ups beside itself, in 5C, between the owner and the next district). An anchor
  above band 9 is honoured only with `--blocks "<why>"` — dev's gate is red on it, or the
  build in hand or the next 5C/5D row cannot finish without it — and the reason is written
  into the ticket. `--by owner` filings are never redirected; an anchor at or below band 9
  is honoured as before. **Since 2026-10-20 that is the rule for OPERATIONS only: a
  follow-up goes to the band of its KIND** (owner, after GPU and Glessner follow-ups kept
  landing in the loop band; T-2940). `new --kind perf` → the foot of band 1; `--kind
  building` → directly under that building's last queue line (band 2 or 7); `--kind ops`
  → the foot of band 9, found by its header (it now sits right under band 1). Without
  `--kind` the title decides: a performance word (GPU, fps, p95, frame time, memory, a
  figure in ms) is perf, a house it names is building, anything else is ops. Third, **if finishing would take more than five tickets, it is an
  epic**: one ticket under `EPICS` at the foot of QUEUE carrying the list, and no more.
  The loop does not work an epic until the owner promotes it. **Agents never move an
  existing line — only the owner re-ranks.** That is what keeps his priorities durable.
- **An owner ask becomes a ticket the moment it is made**, `--by owner`, before any work
  starts. This is not optional bookkeeping; an owner request going untracked for days is
  the exact failure this system exists to close.
- **Finish your PR inside the run that opened it** — merge on a green gate, or `block`, or
  hand it to the next run with `.github/steward/pr-rest.sh resume <N> --why "…"`
  (§ the two labels). `hold` is not yours to apply. **A claim is only real once its PR merges**: the state
  lives in the ticket file, so an abandoned open PR leaves the ticket reading `open` at the
  top of the queue and the next run rebuilds the same work. It cost about seventy minutes
  on 2026-08-19 (run 943's PR #258 left open, run 944 redoing T-0062 as #259). `claim` now
  checks `git ls-remote` for a rival branch carrying the ticket's number and refuses with a
  `--force` escape — but that only protects the NEXT run; finishing the PR is your half.
  That scan skips `claim/*` (the lock is the authority on a live claim and says who holds
  it) and, since T-1666, `idlock/*` — the ID-MINT LEASE every ticket carries from the day
  it was filed. Reading those as work refused EVERY unclaimed ticket, so `--force` became
  the normal way to claim and the one case the check exists for stopped being visible; the
  same bug was filed three times in three days (T-1601, T-1646, T-1666). **A refusal that
  names a real `steward/*` branch is a real rival — believe it.**
- **Size in RUNS before you FILE, not before you claim.** `XS` part of a run · `S` one
  run · `M` one run, tight (or one run plus a bake) · `L` **more than one run, which
  `new` now REFUSES at the prompt and `claim` refuses after** (T-1593). The test is the
  acceptance clause: *if it needs more than one demonstration, it is more than one
  ticket.* File the pieces as their own tickets, `--after` the work they serve; an L
  already in the queue is cut with `ticket.mjs split T-NNNN "piece" "piece"` — the
  children inherit the parent's exact place in QUEUE, so a split never re-prioritises.
  If a run discovers mid-flight that its ticket is bigger than one demonstration, it
  splits rather than shipping a self-invented "(1/2)". **`split` refuses a parent another
  run holds** — a live claim that is not yours, or an open PR on it (T-1344): the claim
  lock is per id, so the pieces would go into the queue unheld while that run carries on
  onto one of them. Your own claim never refuses, and every piece records what stood on
  the parent; `--anyway --why "…"` splits past a rival and writes the reason into the
  pieces. Separately, `--anyway` is the ticket
  *budget's* override and cannot reach an L: the queue gate refuses one unconditionally,
  so filing one anyway only chooses whose pull request goes red for it.
- `tools/check.sh` runs `ticket.mjs check`: duplicate ids, queue drift, stale BOARD, a
  block with no stated question, an `L` in the queue.
- **…and it says WHOSE red it is** (T-1593). The tickets are a separate repository, so
  nothing that step reads is in the diff under review — which on 2026-09-25 made the two
  L filings above turn `ticket queue` red on #51, a pull request of AGENTS.md and three
  files under `tools/`, 37 minutes later. check.sh passes `--inherited-warn`: a fault in
  *this* repository's files still fails the gate, and a fault in the tickets repository
  is reported as a WARN naming the filing and the one command that clears it for every
  open PR at once. **Run `node tools/ticket.mjs check` bare and it is strict** — by hand
  and in the tickets repository's own CI, which is where the rule keeps its teeth. The
  flag softens nothing your run caused: a dirty or unpushed tickets clone still fails.

### A RUN MAY TAKE A GROUP — one to five tickets, one PR (owner, 2026-10-20)

The owner: *"i am very much liking this move of taking several tickets at once that can be
worked together and merged as a unit ... when claiming a ticket, it can and should evaluate
if it can claim multiple and handle them as a group in a single PR that way we minimize PR
churn ... so maybe 3-5 tickets might get picked up and merged together"*. Every PR costs a
gate, a lap each time a sibling lands, and a merge; five small PRs on one house cost five of
each and conflict with one another on its bake. So a run SHOULD look for a group, every run:

1. **The anchor is picked exactly as above** — the topmost workable ticket (your k-th under
   slices). Nothing in this section moves the pick.
2. **Then look for mates:** `node tools/ticket.mjs list --workable --group T-ANCHOR` prints
   the takeable tickets linked to it — the same house, pieces of the same small split, one
   naming the other, a file or kit id both name — with effort and needs-bake. It is a hint:
   read each one.
3. **Add up to four** (one to five in all) that share files, a subsystem or a building with
   the anchor AND fit one run together: up to five `S`, or one `M` plus up to three `S`;
   **never an `L`**; a `needs_bake` member only if this run bakes anyway. A mate from lower
   in the queue rides the anchor's run; one that would make the anchor late is not a mate.
   Under N slices, never take one of the first N workable rows: those are the other
   slices' anchors.
4. **Claim every member before any work:** `ticket.mjs claim T-A T-B T-C` — one pushed
   commit, each member asked everything a single claim asks. A refused member is printed
   with its reason; work what was claimed (it exits non-zero only if it claimed none).
   Anchor already claimed alone? `claim T-B T-C --with T-A` joins them to its group.
5. **One branch named for every member** (`steward/t2931-t2932-t2923-1801-carving`, so
   `inflight`, the rival scan and the strand gate see each), **one commit per ticket**,
   **one PR titled `T-A, T-B, T-C: …`**, then `ticket.mjs done T-A T-B T-C --pr N`.
6. **A member the run cannot finish is never shipped half-done and never left claimed:**
   `ticket.mjs release T-B --why "…"` gives it back (open, its queue place kept, the reason
   in the ticket), or `split` it and keep the finished piece. Then retitle the PR.
7. **One What's-New entry per PR,** `changelog.d/<anchor>.json`, one item per ticket (the
   budget's six items hold five). The visible-progress rule still counts RUNS: a group is
   one run, visible only if a member changes what a visitor sees.

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
- **A building's pictures go on its card** (T-2389). The owner, 2026-10-11: *"As you build each
  once can you include those photos images of the house on the card for the house on another
  tab"*. The card's Images tab is generated at publish by `tools/compile_pictures.py` from the
  Prairie library and `data/sources/`, so a draft, refine or rebuild that finds a photograph or
  drawing of its building makes it reachable there: in the Prairie library, a record whose
  `building_ids` names the building, with a credited copy in the image store whenever it can be
  fetched (a link-only record shows as a link); for any other year, a `photograph` or
  `illustration` record in `data/sources/` that the structure record names. Before closing, open
  the card at 390x780 and see each picture on the Images tab with its credit.

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
  Never push to `dev` or `main` directly. Unfinished work stays an open PR labelled
  `resume`, with its reason in a line a machine can read (§ the two labels).
- <a id="the-two-labels"></a>**THE TWO LABELS, AND THEY MEAN DIFFERENT THINGS** (T-1573;
  owner, 2026-09-25, on finding three PRs parked on `hold` whose reasons he had not seen:
  *"that seems like a bad move because i am not aware of why they are held"*).

  | label | means | who applies it | what comes for it |
  |---|---|---|---|
  | `hold` | **the owner is deciding** | the owner, never a run | nothing, until he says so |
  | `resume` | **a run could not finish** | the run, with its reason | the lap, the merger, the next run |

  `hold` was the only label a run had, so it was applied to both — and because every
  automated pass in this repository skips a held PR on purpose (a park a robot can
  overrule is not a park), work that needed nobody's decision had nothing coming for it
  either. Measured on the three PRs open at 17:35Z on 2026-09-25: #39's stated reason
  ("this run's clock ran out") was already stale — CI had passed all 620 steps — and it
  had drifted into conflict with `dev` while held; #41 and #42 were both COMPLETE and
  held only because `dev`'s own gate was red. Not one needed a ruling. Each needed a
  machine to lap it, re-gate it and merge it, and each got a person instead.

  So, concretely:

  - **A run never applies `hold`.** If the thing in your way is genuinely the owner's —
    rights, the depiction of people, money, what the project IS — that is `ticket.mjs
    ask`, on the ticket, with options, so it reaches his board with a one-click answer.
    A label is not a question.
  - **A run that cannot finish applies `resume`, with its reason**, in one call:

        .github/steward/pr-rest.sh resume <N> --why "dev's gate is red on T-1567" --waits-on T-1567

    which writes `resume: <reason> · waits on: <T-NNNN|nothing>` as the first line of a
    PR comment, applies the label, and takes `hold` off if a run left one there. The
    reason goes on BEFORE the label, so a labelled PR never exists without it.

    **It acts on the repository THIS CHECKOUT belongs to** — its origin remote —
    which since T-1655 is the one thing it does not read out of the environment. A
    steward improve run executes inside a **polecat-platform** job and clones this
    repo into the workspace, so the ambient repo name is the wrong one for every call
    made from here; on 2026-09-27 that put chicago#104's handoff reason and its
    `resume` label onto polecat-platform#104, an unrelated PR, and it did not fail,
    because both repositories had a #104 open that day. Pass `--repo owner/name` to
    act on another repository, and expect a one-line refusal — never a guess — when
    the repository it resolved does not contain the PR or the branch.

    **And so do the other three steward scripts, since T-1656** — `pr-lap.sh`,
    `merge-ready.sh` and `pr-stuck.sh` all carried the identical
    `${GITHUB_REPOSITORY:-kevinrhaas/chicago}` line, whose `:-` default reads as a
    safety net and is not one: in an Actions job the variable is always set, so the
    default never fires. They were left out of T-1655 only because their callers are
    this repository's own workflows, where the ambient name happens to be right — a
    property of the CALLER, and the same one pr-rest.sh had until a run drove it from
    a clone. Two of them WRITE (merge-ready merges; pr-stuck labels and comments), so
    the silent wrong-repository write was available to them the same way. All four now
    take `--repo owner/name`, default to the origin remote of the checkout the file is
    in, and refuse in one line rather than guess; `tools/check_gh_rest.mjs` names all
    four in `REPO_NAMED`, and its `--self-test` proves each one is covered on its own.
  - **A later run works resumable PRs before it takes new queue work.** Merge `dev` in,
    re-derive, fix what is red, gate, merge — it is the same endgame as any unit, on a
    branch that is already most of the way there. **Skip one whose `waits on` ticket is
    still open** and say so in your summary: it cannot go green yet, and re-gating it
    would spend a run proving that.
  - **Take the PR before you lap it: `node tools/ticket.mjs lap <N>`** (T-1721). The rule
    above carries no slice index, so under `slices > 1` every slice that looks takes the
    same PR — #154 was relapped twice on 2026-09-28, #442 again on 2026-10-05, and each
    loser found out at `git push`, after its gate. `lap` takes `lap/pr-<N>` on the remote
    by the claim lock's compare-and-swap; a refusal (exit 1) means a live sibling is on it,
    so take your own row of the queue instead. `inflight` lists every `resume` PR as
    BEING LAPPED, pushed minutes ago with no lock (treat as held until you have read its
    newest commit), or FREE. Release with `lap <N> --release` once it merges or is handed
    on; a lap older than three hours is a dead run's, stolen by the next `lap` and swept by
    `claims --sweep`.
  - **What each pass does with the two**, stated so nobody has to read three scripts:
    `pr-lap.sh` laps a `resume` PR like any other and skips `hold`; `merge-ready.sh`
    merges a `resume` PR the moment GitHub calls it `clean` (which IS the resume, for one
    REST call) and skips `hold`; `pr-stuck.sh` sees both, reports a resumable PR WITH its
    reason and never labels it, and leaves a held one in silence. `waits on` gates only
    the agentic pickup, never a machine merge of an already-green PR. The lap and
    merge-ready both skip a PR whose `lap/pr-<N>` a live run holds — they ask
    `ticket.mjs lap <N> --status`, the reading `lap` steals by, and an unreadable lock is
    skipped and said, never acted on (T-2929; #1132 was lapped and merged over one).
  - **The tickets repo's settle workflow reads neither label.** It follows the PR's
    merged/closed state alone: a ticket goes `done` when its PR merges and back to `open`
    if the PR closes unmerged. So a `resume` PR's ticket sits at `review` with its PR
    number until the work actually lands — which is the behaviour wanted, and is why
    `ticket.mjs done --pr N` is still called when the PR is opened and not when it merges.

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
    rotting you will be told inside one sweep; rebase it on `dev`, or hand it on with
    `pr-rest.sh resume` so the next run does (§ the two labels).
  - those three files conflict on nearly every landing BY DESIGN — the root
    `.gitattributes` refuses to union-merge the changelog because union silently
    corrupted it on five consecutive merges in one day. So expect to rebase, and **finish
    the PR you open inside your own run** rather than leaving it to be swept.
- **Merging into `dev` is STAGE, not ship.** It publishes only the integration preview at
  `chicago.polecat.live/4d/dev/` — noindex, banner-marked, `build.json` says
  `tier: dev`. Production is untouched.
- **Production moves ONLY when the owner dispatches `chicago-4d-promote-to-prod.yml`.**
  No schedule, no agent. `walk/` changes reach `main` by that dispatch and no other route.
  The hotfix exception stands: a production emergency PRs straight into `main`, and the
  next promotion's back-merge folds it into `dev`.
- **Scope is `chicago/4d/` and its published mirror `site/4d/`.** Since 2026-09-23
  this project has its own repository (kevinrhaas/chicago); the rest of it —
  `chicago/reference/`, the Atlas datasets and viewers, the landing page at `site/` —
  is the 4D project's source material and front door, touched only when a ticket asks.
  The workflow files are outside a run's scope: changing one needs an interactive,
  owner-visible PR.
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
- **You no longer publish in the same commit — `site/4d/` is not committed at
  all (T-0938).** The mirror is a build product with one writer, `tools/publish.sh`,
  and it is untracked and .gitignored. `tools/check.sh` runs publish.sh first and then
  asks `check_published.mjs` whether what it produced matches its source; `deploy.yml`
  publishes both the production tree and the dev-preview worktree before the Pages
  upload; `chicago-4d-bake.yml` publishes before it uploads the mirror the smoke runs
  against. So the URLs are unchanged and a run that forgets to publish can no longer
  ship an invisible change — there is nothing left for it to forget. Run publish.sh
  when you want to LOOK at the published tree (`--published` measurements, a local
  serve); the gate runs it for you either way.
  `site/4d/` is a generated mirror and `deploy.yml` only fires on `site/**`, so
  skipping it ships nothing while looking merged.
- **Changelog: add ONE entry FILE, `changelog.d/<ticket>.json`, and do not touch
  `renderers/web/js/changelog.js` (owner, 2026-10-10).** The file holds
  `{ "title": …, "kind": …, "items": [ … ] }` and nothing else — no `v`, `ts` or `date`.
  Check it with `node tools/changelog-entries.mjs --check` (`check.sh` runs that too); the
  What's-New budget below applies to it unchanged. After the PR merges,
  `.github/workflows/chicago-4d-changelog-fold.yml` folds every pending file into
  `changelog.js` on `dev` (newest landing on top), stamps it, deletes the file and pushes
  one commit, so the published changelog keeps its exact format. `changelog.d/README.md`
  shows an example.
  - **Why a file:** every PR used to edit the top line of `changelog.js`, GitHub does not run
    this repo's merge drivers, so every open PR conflicted with every landing. With ten lanes
    and a twelve-minute gate a sibling always landed first; on 2026-10-09/10 #607, #608, #610
    and #613 each lost three merges to that one line. Two PRs never write the same entry
    file, so they never conflict on it.
  - Name the file after the ticket (`T-2250.json`); two files with the same title are refused.
  - **The old way still passes** (prepend to `changelog.js` with `v: null, ts: '', date: ''`,
    then `node tools/stamp-changelog.mjs` and `node tools/check-changelog.mjs`), so a PR
    opened before 2026-10-10 need not be redone. The notes below are about that file and
    still hold for anyone who edits it.
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
  - **A shipped entry keeps its place, its stamp and its number (T-1380).** When you resolve a
    changelog conflict, the base's entries go back VERBATIM; only your branch's own entries
    are re-stamped. `check-changelog.mjs` holds the working tree to its merge base with `dev`
    and refuses an entry that was dropped, re-stamped or renumbered: measured over every dev
    merge since 2026-08, that happened 25 times and read "contract OK" every time.
  - Only the fold stamps after merge, and only entry files. The file is authored inside
    the app because the What's-new tab imports it; `publish.sh` mirrors it to `site/4d/js/changelog.js`, the URL
    Manager and the polecat.live launcher parse live, which must not move — and to
    `site/4d/walk/js/changelog.js` inside the copied renderer tree.
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
- **In anything a visitor reads, those are called liberties** (owner, 2026-10-11): the
  evidence tile, the popup tab and section, card headings, panel notes, in every year. Never
  "what we made up" or a close variant on screen; the standard above is the internal rule.
- `docs/STATUS.md` states what is unverified. Do not describe a gate as passed if it was skipped.
- Where sources disagree, record the disagreement in `docs/RESEARCH/<id>.md` and pick the
  best-attested reading **with reasoning** — never silently choose.
- No model identifiers in repo artifacts.

## Orientation

**Several builds of one structure** (the owner's side-by-side comparisons, Glessner first)
are structure VERSIONS — `data/structures/versions/<id>/<label>.json`, opened with
`?structure=<id>&version=<label>`, promoted with `node tools/promote_version.mjs <id> <label>`;
`docs/STRUCTURE-VERSIONS.md` is the page (T-1727).

`docs/PLAN.md` is the full development plan. `docs/research/` holds the source dossiers
(committed verbatim, tagged, with their own gaps stated). `docs/PROVENANCE.md` expands the
confidence model. `docs/EPOCHS.md` explains the temporal architecture.
