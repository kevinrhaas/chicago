# ROADMAP

The build order and the work parcels. `docs/PLAN.md` carries the full reasoning; this is the
operational view â€” what to pick up next, and what it depends on.

```
S0 scaffold â”€â”¬â”€â–º S1 georeference + datum â”€â”€â–º S2 terrain e1834 â”€â”€â–º S3 M0 Sauganash walkable
   [DONE]     â”‚        [DONE]
              â”œâ”€â–º R1 renderer shell (synthetic geometry) â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”œâ”€â–º P1 research dossiers (read-only) â”€â”€â–º S5 structure records â”€â”€â–º S8 M1
              â””â”€â–º S4 archetype generators (golden params) â”€â”€â”€â”€â”€â”€â–º S5 bakes
S2 â”€â”€â–º S6 flora + fauna â”€â”€â–º S7 polish, audio, perf â”€â”€â–º release sweep
```

**Critical path: S1 â†’ S2 â†’ S3.** The datum gates every coordinate in the project. Work that does
not need coordinates is deliberately structured to proceed in parallel.

### Boot-budget enforcement â€” T-1156

The nightly bake's desktop `1-2` smoke leg runs the existing boot-payload
measurement with `--check` against the downloaded baked mirror. Its failure
withholds the bake PR through `needs: smoke`; the 12 MB budget and the smoke
matrix remain unchanged. See `docs/SITE-BUDGET.md` Â§4 and the ticket for evidence.

### Research completion accounting â€” T-1143 complete 2026-09-15

The completion sequence at the bottom of `tickets/QUEUE.md` now starts from a closed unit ledger,
not the old aggregate unspent count. `data/research/domains.json` registers all twelve research
domains with their reading file patterns and stable unit-id rule;
`data/research/research_spend_ledger.json.gz` dispositions all 23,699 registered units with zero
unclassified. The historical 21,419 / 7,769 / 13,650 read-spent-unspent comparison and the 1,643
second-hop card writes remain separate and unchanged. T-1137 is next: its writer must preserve
this ledger before the resident truth repairs and convergence work proceed.

### Resident identity research â€” two passes complete 2026-09-01

Two reproducible passes now cover 150 of 848 eligible real named people (17.7%):
31 corroborated findings, 30 unmerged candidate identities and 89 documented no-find
outcomes cumulatively. `docs/RESEARCH/resident_identity_pass_02_75.md` records the
second cohort, evidence, duplicate probes and limits. Next: inspect the original Eliza
Chappel and ambiguous-name newspaper columns, adjudicate the strongest hinterland
candidates, then continue with a third non-overlapping 75-person pass through land,
probate, naturalization, marriage and church records. Reconstructed residents remain
outside this programme.

---

## THE OVERNIGHT LANES â€” 2026-08-14 Â· **START HERE**

Two lanes, opened on the owner's instruction of 2026-08-14 alongside the activation of
`docs/RENDERING.md` and the `dev` â†’ `main` pipeline. Everything below:

- **targets `dev`.** Branch `steward/<topic>` off `dev`, PR into `dev`, merge when the dev
  gate is green. Production moves only when the owner dispatches
  `chicago-4d-promote-to-prod.yml`. See `docs/PIPELINE.md`.
- **is ONE parcel per run.** Claim it first (the K16-style heading below), check `git log`
  and open PRs, then work only inside your parcel's file list.
- **is disjoint by construction.** Lane 1 touches renderer and tool files; lane 2 touches
  data and docs. **They cannot collide**, so one of each may run at the same time. Two
  parcels from the SAME lane may not.
- **stays vocabulary-agnostic on confidence names while K16 is in flight.** Name the three
  levels by function â€” source-attested, reasoned-from-specific-evidence,
  invented-to-fill-a-need â€” and read `docs/PROVENANCE.md` at your arrival date for the
  current strings.
- **never installs Blender.** Geometry arrives via the nightly `chicago-4d-bake.yml`, which
  now branches off `dev` and PRs into `dev`. A parcel needing new geometry ships the
  data/archetype half and says so.

### THE RUN BUDGET IS 150 MINUTES, AND THE SMOKE COSTS 26 OF THEM

Set 2026-08-14 on the owner's instruction â€” *"if it's too long we will want to break it into
pieces"* â€” after a run was cancelled at exactly 150 minutes having committed nothing.

**The arithmetic, measured rather than estimated.** `steward-improve` allows 150 minutes
(raised from 90 that day, because runs of 95, 81 and 70 minutes were real work being destroyed
at the ceiling). One `tools/smoke_renderer.mjs` pass costs **~26 minutes** at both viewports.
`tools/critic_shots.mjs --metrics` costs ~12 minutes for the full station set, ~3 with
`--stations`. So a parcel gets **roughly four smoke-equivalents in total**, and it also has to
read, think, write, publish and open a PR inside that.

**The rule: a parcel whose acceptance needs more than TWO full smoke passes must be split
before it is claimed.** Measure-then-fix parcels are the ones that breach this, and they split
along a seam they already have:

- **(a) land the failing gate** â€” build the measurement, prove it fails on the current build,
  commit it red with the numbers quoted. One smoke.
- **(b) fix it green** â€” take (a)'s committed numbers as the baseline. One smoke.

This is better than a time-saving trick: it forces the measurement to be committed *before*
anyone knows which candidate cause is guilty, so the fix cannot quietly redefine success. It
is exactly how R-BUG2 succeeded â€” *"measure before choosing"* refuted its own prime suspect.

**Use `--stations` and `SMOKE_VIEWPORT`.** `critic_shots.mjs --stations a,b,c` runs in about
2 minutes instead of 13; the smoke takes `SMOKE_VIEWPORT=desktop` for a single viewport while
iterating. Full runs belong at the end, not in the loop. (**Corrected 2026-08-15 by R-W4a**:
this paragraph promised a `--stations` flag that did not exist and a `--only` flag the smoke
does not have, so every run that took the advice ran the full set. `--stations` exists now and
was measured at 2 min 03 s for three desktop stations. The full both-viewport `--metrics` run
now costs 13 min with R-W4a's second capture.)
**Updated 2026-08-15 by R-W4c(a), which added a THIRD capture (flower heads hidden).** Measured
on the same three desktop stations: **3 min 45 s**, against R-W4a's 2 min 58 s for two captures
and the original 2 min 03 s for one. The full both-viewport run was **not** re-measured â€” 13 min
is R-W4a's figure and the third capture will have added to it. `--no-mask` drops both extra
captures.
**Use `--stations` and `SMOKE_VIEWPORT`.** `critic_shots.mjs --stations a,b,c` runs in 3 minutes
instead of 12; `SMOKE_VIEWPORT=mobile` runs one viewport while iterating. Full runs belong at the
end, not in the loop.

**AND A CEILING THE RUN BUDGET DOES NOT COVER, measured 2026-08-15 (K21): an agent's single
foreground command is capped at TEN MINUTES, and the desktop half of the smoke does not fit in
it.** The 150-minute figure above is the *run's* budget; the harness a steward run executes in also
caps each individual command, and that is the binding constraint for this gate. Measured on this
runner, serving the published mirror: **`SMOKE_VIEWPORT=mobile` finished in 4 m 43 s, 214 passed /
0 failed. `SMOKE_VIEWPORT=desktop` was killed at 10 m 00 s having passed 151 with 0 failed** â€” an
estimated ~13 minutes end to end, so it fails by about three. Both halves in one command is ~18
minutes and never fits. The trailing `page.click: Target page â€¦ has been closed` in such a log is
the kill, not a failure.

**So a parcel whose acceptance needs the desktop half cannot self-verify it here, and should say so
in its PR rather than quietly merging on the mobile half.** `tools/check.sh` â€” which is the actual
dev gate (`.github/workflows/chicago-4d-check.yml` runs it and nothing else) â€” is unaffected at
~90 s. The durable fix is for the smoke to take a test-name or section filter the way it takes
`SMOKE_VIEWPORT`, so the desktop half can be run as two commands that each fit; until then, the
desktop half belongs to a runner without the per-command ceiling.

**RESOLVED 2026-08-20 by T-0060: the smoke takes `SMOKE_STAGE=1..4`, and each stage fits the
ten-minute command.** The body of each viewport is cut at three section boundaries verified for
crossing bindings (two crossed â€” `terrainLoad`, `streetLayer` â€” and both are now read before the
split; the scans that missed them are written up in the ticket). Measured on the improve runner,
mobile against the published mirror: **stage 1 â€” 1 m 54 s, 74 staged checks Â· stage 2 â€” 3 m 00 s,
91 Â· stage 3 â€” 3 m 17 s, 33 Â· stage 4 â€” 7 m 30 s, 143**, plus 9 always-on checks (boot, loader
problems, run-to-completion, page errors, vendor) taken in EVERY invocation â€” the run prints that
split so the halves can be audited to add up to an unfiltered pass: 341 staged + 9 = 350. The
page-error assertion is no longer the tail of an unrunnable body: a mid-suite throw is caught,
recorded as its own FAIL, and the tail still runs. The unfiltered single-process reference lives
in `.github/workflows/chicago-4d-smoke.yml` (push-to-its-own-path or dispatch on main) â€” that is
the "runner without the per-command ceiling" this section asked for. Desktop stage timings are
not yet measured; stage 4 is the one to watch (its mobile 7 m 30 s includes the shared
street-layer reading), and if it overruns on desktop the fifth cut goes in then, the same way.

**RE-CUT 2026-08-24 by T-0166 (piece 1 of T-0121): the four stages are EIGHT parts, and
`SMOKE_STAGE` takes a range.** The four had eroded exactly as the paragraph above feared, and
faster: by 2026-08-23 three of the four DESKTOP quarters ran past the ten-minute ceiling and the
fourth cleared it by two minutes, so the desktop half a steward run could reach was stage 1
alone. Each quarter is now halved at a section boundary re-verified for crossing bindings, so
**part 2k-1 plus part 2k is exactly T-0060's stage k** â€” the cheap viewport is still four
commands (`SMOKE_STAGE=1-2`, `3-4`, `5-6`, `7-8`) and nothing about the audit changes.

Three of the four new second halves inherited page state rather than a binding, which the
scope-aware scan cannot see and only a part run alone from a fresh boot will show: part 6 and
part 8 boot at the GATE SCREEN (`enterTown()`, T-0060's inline accommodation, now one function
called at the head of four parts), part 8 also needs the PANEL open because its first statement
clicks a tab inside it, and part 4 needs the Sauganash framed because its first check picks
whatever is down the crosshair. All three prologues are guarded on the state they establish, so
an unfiltered run runs them as no-ops.

**The mobile fit, measured on the improve runner against the published mirror** â€” part 1
**1 m 41 s**, 66 staged checks Â· part 2 **1 m 17 s**, 66 Â· part 3 **0 m 52 s**, 65 Â· part 4
**3 m 17 s**, 38 Â· part 5 **2 m 52 s**, 19 Â· part 6 **0 m 44 s**, 14 Â· part 7 **3 m 48 s**, 36 Â·
part 8 **4 m 19 s**, 107 â€” 411 staged checks plus the 9 always-on ones every invocation takes,
and 18 m 50 s of wall clock for eight boots. Every part is inside the ceiling by at least five
minutes. (Part 5 carries T-0114's two road-legibility failures, which are red on `dev` today and
are that ticket's, not this cut's.)

**The audit was taken against the old code rather than asserted.** Running `origin/dev`'s own
`smoke_renderer.mjs` beside the re-cut one, at mobile on the published mirror: old stage 1 gives
**132 staged / 9 always-on / 141 passed**, and new `SMOKE_STAGE=1-2` gives **132 / 9 / 141**. Old
stage 3 gives 33 staged with T-0114's two failures; new parts 5 and 6 give 19 + 14 = 33 with the
same two failures, which is also where those failures are demonstrated to be `dev`'s and not this
cut's.

**Every invocation now prints its own wall clock on its last line**, which is the cheapest
possible early warning: this ceiling has been breached three times and each breach cost a run a
hand measurement to discover.

**THE DESKTOP FIT WAS NOT CLAIMED BY T-0166, AND T-0167 IS WHERE IT IS.** The reason it was
deferred stands: `SMOKE_VIEWPORT=desktop SMOKE_STAGE=7` was killed at 10 m 00 s on T-0166's
runner against 3 m 48 s for the same part at mobile, while part 6 cost 0 m 44 s at mobile and
1 m 53 s at desktop â€” so the desktop cost of a part is NOT a fixed multiple of its mobile cost,
the camera-heavy parts scale several times harder than the DOM-heavy ones, and an eight-way cut
sized on the mobile profile could not be assumed to fit.

**THE DESKTOP PROFILE, MEASURED 2026-08-24 by T-0167** â€” eight foreground commands at 1280x800
on the improve runner against the published mirror, one part each, `SMOKE_TIMING=1`:

| part | desktop | margin | staged checks | mobile (T-0166) |
|---|---|---|---|---|
| 1 | **3 m 31 s** | 6 m 29 s | 66 | 1 m 41 s |
| 2 | **2 m 37 s** | 7 m 23 s | 66 | 1 m 17 s |
| 3 | **1 m 40 s** | 8 m 20 s | 65 | 0 m 52 s |
| 4 | **7 m 07 s** | 2 m 53 s | 35 | 3 m 17 s |
| 5 | **6 m 40 s** | 3 m 20 s | 19 | 2 m 52 s |
| 6 | **1 m 24 s** | 8 m 36 s | 14 | 0 m 44 s |
| 7 | **7 m 43 s** | 2 m 17 s | 36 | 3 m 48 s |
| 8 | **8 m 46 s** | 1 m 14 s | 107 | 4 m 19 s |

408 staged checks plus the 9 always-on ones every invocation takes, and **39 m 28 s** of wall
clock for eight boots. (Mobile's 411 is these 408 plus the three checks part 4 takes only at
mobile.)

**THE TABLE ABOVE IS SPELLED IN THE PART NUMBERING OF 2026-08-24, WHICH IS NOT TODAY'S**
(noted 2026-09-03, T-0450). Its rows are the nine parts as they stood before T-0346, T-0173
and T-0170 each cut one in two; read forward, its part 4 is today's 4+5+6, its 5 is 7+8 and
its 7-9 are 10-13. It is kept because it is the measurement the cuts below were sized from,
and re-labelling it would destroy that. For what the parts and the gate's legs cost TODAY,
in today's numbering, ask the record: `node tools/smoke_budget.mjs` and `--legs`.

**The table above was taken at `ac1abb80`**, and T-0166's mobile column at the same commit.
T-0114 merged into `dev` while this run was measuring and changed `streets.js`, so the parts
that read the roads â€” 5 and 7 â€” will have moved a little since, and part 5's reading was taken
with T-0114's road-legibility check still failing. The re-cut readings below, and the audit,
were re-taken on top of T-0114.

**NOTHING OVERRAN, AND THAT IS NOT THE SAME AS FITTING.** Two readings have to be held together:
part 7 measured 7 m 43 s here and was KILLED at 10 m 00 s on T-0166's runner three days earlier,
on a body that had not grown in between. **These desktop numbers move by minutes between runs**
â€” SwiftShader is a software renderer and its cost tracks whatever else the machine is doing â€” so
a part is not sized by whether one reading cleared the ceiling but by how much margin it has when
it does. A 74-second margin is not a margin.

**RE-CUT 2026-08-24 by T-0167 (piece 2 of T-0121): part 8 is halved and there are NINE parts.**
Part 8 was both the thinnest margin on the profile and the most check-dense part of the suite by
a factor of three, which is the combination worth cutting. It is also the TAIL, so the new part
is APPENDED and parts 1-7 keep their numbers: the pairing rule survives as 1+2, 3+4, 5+6, **7+8+9**,
and the mobile recipe's last command widens from `7-8` to `7-9` â€” still four commands. The
boundary is the Evidence panel: the profile put 6 m 05 s of the old part 8 above it and 2 m 41 s
below, and the scope-aware scan found three names crossing it (`eye`, `toggles`, `typed`) of which
all three are prose or a different local (`typedE.typed`), so nothing crosses in fact. Part 9's
prologue is `enterTown()` alone â€” the liberties reading already carries its own guarded panel-open
and clicks its own tab, so unlike part 8 it needs no panel guard bolted on.

**Measured after the cut, at desktop: part 8 â€” 6 m 10 s, 28 staged Â· part 9 â€” 3 m 09 s, 79
staged.** 28 + 79 = 107, exactly the old part 8's count, which is how "never dropping a check" is
demonstrated rather than asserted. Both were taken twice, once at `ac1abb80` (6 m 08 s / 3 m 08 s)
and again on top of T-0114 â€” the same counts and within two seconds either way, which is also a
reading on how much of the desktop variance is the scene and how much is the machine. The worst
desktop margin is now **part 7 at 2 m 17 s**, and it is the next one to go â€” T-0170, which also
records why it was not taken in the same run: part 7 has no section headers to cut at, it holds
one half of the `anyStage(5, 7)` street-layer reading, and it is not the tail, so cutting it
renumbers everything after it. The audit was taken at mobile too: old `SMOKE_STAGE=7-8` gives 143
staged / 9 always-on / 152 passed and new `7-9` gives **143 / 9 / 152**, in 5 m 53 s against
5 m 49 s.

**AND THE HEADING OF THIS SECTION IS OUT OF DATE BY A FACTOR OF TWO.** "The smoke costs 26 of
them" was measured on 2026-08-14. T-0167's profile puts the staged gate at **39 m 58 s of desktop
across nine commands plus 13 m 26 s of mobile across four** â€” call it **53 minutes**, better than a
third of the 150-minute run budget, and that is before a part is re-run after a fix. The two-full-
passes rule above should be read as ONE full pass and a re-run of the parts a change touches; a
parcel whose acceptance needs the whole gate twice has already outgrown a run.

**RE-CUT 2026-08-30 by T-0173: part 7 is halved and there are TWELVE parts.** T-0346 cut part 4
into three that morning; part 7 went the same way by the evening. Profiled with `SMOKE_TIMING=1`
on the steward runner at **load average 0.81-2.86, 4 cores**, part 7 was **killed at 9 m 25 s**
with its last two assertions unrun â€” so the reading in T-0167's table above, 7 m 43 s, is again a
description of a machine rather than of the part. **7 m 04 s of that cost was ONE block**: the
three road-legibility stations, each teleporting to its own viewpoint and reading
`page.screenshot` frames through five distance bands (`south_water` 2 m 13 s, `from_above`
2 m 02 s, `lake_market` 2 m 49 s). Around it, 20 s of boot, 33 s of navigation and the street
checks, 1 m 04 s of the R-A1 aid and the batch merge under it.

**So the boundary is not a section header, and T-0170 had already said why it could not be.** The
best of part 7's own `// --- ` boundaries leaves 7 m 37 s against 1 m 30 s. The cut falls at the
STATION â€” the grain the block is made of â€” and nothing crosses it: `roadRuns` is local, the
movement report built from it is printed and never gated and has always compared only what the
invocation measured, and `--update-road-bands` merges per band. R-A1's three assertions are taken
standing at `lake_market`, so that station moves into the new part with them.

**Measured after the cut, at desktop, on the same runner in the same hour: part 7 â€” 5 m 05 s, 12
staged Â· part 8 â€” 5 m 06 s, 8 staged, both SMOKE PASS.** 12 + 8 = 20, exactly the old part 7's
count. Both clear the ceiling by 4 m 55 s. Part 7 keeps the shared `streetLayer` reading, so the
guard becomes `anyStage(7, 10)`; part 8's profile â€” boot at 0 m 17 s, first station at 3 m 17 s â€”
is the proof it does not pay for it. Parts 8-11 are renumbered 9-12; the pairing rule survives as
1+2, 3+4+5+6, **7+8+9**, **10+11+12**, ranges `1-2 3-6 7-9 10-12`. The audit was taken at mobile
too: old `SMOKE_STAGE=7-8` gave 43 passed and new `7-9` gives **43 passed, 34 staged** in 7 m 33 s,
and `10-12` gives 168 passed / 159 staged in 9 m 33 s. **The worst desktop margin left on the
profile is what was part 7 and is now part 10 â€” T-0170, still open**, which this cut re-labels
rather than takes.

**RE-CUT 2026-08-30 by T-0170 (the last piece of T-0121): part 10 is HALVED and there are
THIRTEEN.** Part 10 â€” the part T-0173 above hands on as "the worst desktop margin left" â€” was
never inside the ceiling at all. Profiled at 1280x800 on an **idle** runner (load average
0.27-1.48, zero other Chromium processes, so this is the friendliest reading the suite can be
given) it was **killed at 9 m 20 s with the street readouts and the Settings units still to
run**. That is the third and fourth kill of the same part; T-0167's 7 m 43 s is the outlier in
the record rather than the reading to size a cut from.

**Why it had been left, and what changed.** This part carried no `// --- section ---` headers at
all, which is exactly why T-0167 cut part 8 instead: the boundary had to be MADE before it could
be taken. Its seams are named now â€” eight of them, five in the head and three in the tail â€” so
the next cut in this part is a choice from a list rather than a fresh profile.

**The cut is the second candidate, and the first one is in the record because it was measured
and rejected.** Cutting above R-BUG7's flower-head census gave **5 m 05 s / 6 m 24 s** â€” a
3 m 36 s margin on the second half, and this section's own rule is that a margin that thin is
not a margin. Moving that one section up into the first half balances it:

| part | desktop | margin | staged checks | what it is |
|---|---|---|---|---|
| 10 | **5 m 59 s** | 4 m 01 s | 23 | the drawn population, the horizon timber, the sward census in every community, the marsh substrate, T-0035's pop-in, R-BUG7's heads |
| 11 | **4 m 41 s** | 5 m 19 s | 13 | the ragged boundary and its fringe, each community's recorded ground cover, the street readouts, the navigation guide, the Settings units |

23 + 13 = **36**, exactly the count the part took before the cut, which is how "never dropping a
check" is demonstrated rather than asserted. The second half is SMOKE PASS; the first half's one
red is **T-0279's flower heads** (2,693 of 18,893), which `tools/dev-smoke-state.json` already
records as dev's on 2026-08-29 at 2,526 of 18,911 â€” it moved parts, not sides, and it does not
fire at mobile at all.

**The audit was taken against the old code rather than asserted.** Running the pre-cut
`smoke_renderer.mjs` beside the re-cut one, at mobile on the published mirror and on the same
tree: the single part gives **45 passed / 0 failed / 36 staged / 9 always-on in 5 m 59 s**, and
the pair gives **45 / 0 / 36 / 9 in 6 m 01 s** â€” one boot for the pair, which is why the mobile
recipe does not grow a command.

**One binding crosses the new boundary and it is the one that already crossed the stage split.**
`streetLayer`, and BOTH halves read it â€” the head for the road panels and the horizon band, the
tail for the readouts â€” so the guard becomes `anyStage(7, 10, 11)`. The scan turned up six other
names below the line (`headSupport`, `horizon`, `over`, `planted`, `popIn`, `sward`) and every
occurrence is prose or a string. The second half's prologue is `enterTown()` and `setFly(false)`:
every camera-bearing section below it teleports itself, but all of them read the drawing from a
walker on the ground and the last thing the part does is fly.

**AND THESE READINGS WERE TAKEN AT LOAD 0.9-5.1 WITH NO OTHER AGENT ON THE BOX**, which is the
condition this section demands be recorded. T-0215's factor of twenty applies to them the same as
to every row above: 4 m 01 s of margin is a margin against the machine that measured it, and no
cut of this suite survives load 50. Old parts 11-12 are renumbered 12-13; the pairing rule
survives as 1+2, 3+4+5+6, 7+8+9, **10+11+12+13**, ranges `1-2 3-6 7-9 10-13`.

**`SMOKE_TIMING=1` stamps every check line with the elapsed clock**, and T-0167 added it because
the profile could not have been taken without it. A part that BREACHES the ceiling is killed
*before* it prints its wall clock, so the parts actually worth cutting were the only ones a plain
run reported nothing about â€” T-0166's part 7 reading is literally ">10 m", and nothing else. With
the stamp on, a killed run is still a profile of everything it reached, which is what places the
next cut. It is off by default so the gate's own output stays comparable between runs.

**AND EVERY NUMBER IN THE TABLE ABOVE IS A READING OF THE MACHINE AS MUCH AS OF THE SUITE â€”
T-0167 said so, and 2026-08-27 put a factor on it.** T-0167 wrote that "these desktop numbers move
by minutes between runs because SwiftShader's cost tracks whatever else the machine is doing", and
sized its cuts on margin rather than on any single reading. **T-0215 measured how far that goes.**
On a box carrying a dozen parallel agents â€” load average **38.7-51.7**, **71-115** concurrent
Chromium processes â€” ten consecutive animation frames of this scene cost

**17,036 Â· 29 Â· 333 Â· 21,451 Â· 20,211 Â· 119 Â· 4,420 Â· 22,280 Â· 12,242 Â· 26,580 ms**

against the **0.46-1.10 s** of 2026-08-13. That is a factor of twenty on the quantity every
Playwright action is denominated in, and the 29 ms frames in the same sample are the proof it is
contention rather than the scene. Boot to `ready` measured **29 s, 106.8 s and 127.4 s** on one
tree inside twenty minutes, against the 30 s the boot check allows; two runs had their browser
killed outright; a `page.goto` against a **local static file server** timed out at 30 s. So:

- **A part's timing is only comparable to another taken under the same load.** Record the load
  average and the Chromium process count beside any reading added to the table above, the way
  T-0215's are recorded in its ticket. A margin measured at load 2 is not a margin at load 50.
- **A `page.click` timeout on this suite is a question, not a verdict.** It has now twice been
  read as a broken control and twice been the budget â€” 2026-08-13 and 2026-08-27, the second time
  by three separate agents on one day. The smoke now prints what a frame costs whenever an action
  times out, and `clickChrome` (part 8's fourteen chrome clicks) takes the panel chrome out of the
  race entirely without dropping one assertion. See STATUS 2026-08-27.
- **The ten-minute ceiling this section exists to fit is not the binding constraint on a loaded
  box.** Part 8 measured 6 m 10 s at desktop on 2026-08-24 and could not reach its first assertion
  in 4 m 23 s on 2026-08-27. Cutting parts finer does not help that; running fewer of them at once
  does (T-0216).

**AND THE CONTROLLED A/B, TAKEN WHEN THE BOX DRAINED.** `origin/dev`'s own unmodified harness, on
the same tree, at load 10.4-13.7 with 20-24 Chromium processes: **37 passed, 0 failed, all 28
staged checks, SMOKE PASS â€” in 14 m 33 s.** Two readings to hold together. Stage 8 was never
broken: the harness that failed three agents is green on a quieter machine. And it does not fit:
**14 m 33 s is four and a half minutes past the ten-minute ceiling**, on a part T-0167 measured at
6 m 10 s three days earlier and cut to that size deliberately. So the table above is a *floor* on
what these parts cost on a shared box, not a description of it. T-0215's `clickChrome` puts part 8
back at **6 m 10 s** â€” T-0167's figure to the second, all 28 checks â€” by not paying for frames
where the frames are not the subject. Desktop-only: the same part costs 2 m 52 s at 390Ã—780, where
a frame covers a quarter the pixels.

**THE LEG COSTS WERE NEVER MEASURED AS LEGS, AND T-0181 MEASURED THEM â€” 104 REAL ONES.**
T-0171's merge commit said its four desktop legs cost *"6 m 08 s, 8 m 47 s, 8 m 04 s and
17 m 02 s"* and that the *"worst leg keeps better than ten minutes of margin"*. **Both claims
are wrong, and the record is corrected here.** Those four numbers were SUMMED from T-0167's
per-PART profile on the reasoning that a pair boots once where the profile paid a boot per
part; not one of them was a reading of a leg. T-0181 then restated the margin as **9 m 49 s**
from a single leg in bake run #273. That is also wrong â€” one sample of a quantity T-0167 had
already written down as varying "by minutes between runs".

**The readings are this workflow's own job history**, taken 2026-08-30 from the Actions API for
`chicago-4d-bake.yml`, runs **#271-#391** â€” every desktop tail leg it has ever run (`7-9` before
T-0346 renumbered the parts, `9-11` after it, and `10-12` since T-0173 halved part 7 later the same
day; the leg carries identical content across all three renames, so they are one population). Each job is decomposed into its steps, which is what makes
the result legible:

| quantity | n | min | median | worst |
|---|---|---|---|---|
| the leg's **smoke command**, body completed | **90** | 9 m 26 s | **17 m 12 s** | **21 m 48 s** (#306) |
| â€¦of those, the ones that also passed | 47 | 12 m 10 s | 16 m 48 s | 21 m 48 s |
| the **whole job** (checkout + install + smoke) | 90 | 10 m 41 s | 18 m 38 s | **28 m 04 s** (#293) |
| `actions/checkout@v4` | 104 | 0 m 31 s | **0 m 38 s** | **30 m 01 s** (#284) |

Standard deviation on the smoke command is **2 m 58 s**. So the honest margin on a 30-minute cap
is **about seven minutes against the worst smoke ever recorded**, and **1 m 56 s against the worst
whole job** â€” not ten minutes, and not 9 m 49 s.

**THE RISK T-0181 CALLED HYPOTHETICAL HAS MATERIALISED SEVEN TIMES.** The ticket said "nothing
todayâ€¦ the risk is a slow runner pushing desktop 7-9 past 30 minutes". It has, in runs **#284,
#288, #290, #357, #358, #360 and #364**, every one killed at 30 m 1x s with `open-pr` never
running â€” exactly the failure T-0171 was written to end. GitHub reports a `timeout-minutes` kill
as `cancelled`, which is why a scan for failures missed all seven.

**AND NOT ONE OF THEM WAS A SLOW SMOKE.**

| run | job total | `checkout` | smoke |
|---|---|---|---|
| #364 | 30 m 16 s | **13 m 20 s** | 16 m 23 s |
| #360 | 30 m 15 s | **21 m 38 s** | 8 m 08 s |
| #358 | 30 m 15 s | **15 m 20 s** | 14 m 23 s |
| #357 | 30 m 14 s | **21 m 19 s** | 8 m 26 s |
| #290 | 30 m 16 s | **23 m 23 s** | 6 m 21 s |
| #288 | 30 m 20 s | **29 m 17 s** | 0 m 33 s |
| #284 | 30 m 07 s | **30 m 01 s** | 0 m 00 s |

The checkout's median is 38 seconds and its 75th percentile is 47; but **11 of 104 exceeded five
minutes and 7 exceeded thirteen**, and in #284 it ate the entire cap before the suite ran a single
check. The distribution is bimodal, and the upper mode is the whole failure mode. `custom` is a
3.2 GB monorepo of unrelated projects â€” `garage/` alone is 968 MB against `chicago/4d`'s 182 MB â€”
and this job clones all of it to run one subtree's tools against an artifact it downloads
separately. That is **T-0437**, filed by this ticket; it is the real defect and no cap closes it.

**SO THE CUT IS THE WRONG INSTRUMENT HERE, AND THIS IS THE EVIDENCE AGAINST IT.** T-0181 offered
two candidates and asked for a choice on evidence rather than taste. Splitting the tail leg
further halves its smoke but leaves its checkout untouched, so every new leg draws again from the
distribution that is actually causing the kills. Against these 104 checkouts a two-way split moves
the expected breach rate from 7/104 to roughly 6/104 â€” noise â€” while adding a runner and another
boot. **Three of the seven breaching checkouts are longer than a split leg's entire budget would
be.** Splitting is not merely insufficient; it buys nothing.

**T-0181 THEREFORE SET THE CAP TO 45 MINUTES** (`chicago-4d-bake.yml`, the `smoke` job; superseded by T-0437 below), sized on the table
above: worst measured smoke command 21 m 48 s, plus the ~22 minutes of checkout excursion the
raise is meant to absorb. That covers five of the seven breaches outright and the sixth against a
median smoke. It does **not** cover #284 and #288, and it is not supposed to â€” a 30-minute
checkout is a defect to fix, not a budget to fund.

**The general lesson, which is now three-for-three.** T-0165 sized this cap off mobile; T-0167
exists because T-0166's cut was sized off mobile too; T-0171's margin was summed rather than
measured; T-0181's was one sample. Each was a number nobody had read off the thing it governed.
**The job history is free and it is right there** â€” `gh api repos/OWNER/REPO/actions/runs/ID/jobs`
gives per-step `started_at`/`completed_at` for every leg this workflow has ever run. Any future
change to this cap or this cut should quote that, and should decompose the job into steps before
blaming the suite, because on the evidence above the suite was never the problem.


**T-0437 â€” reduced smoke checkout, measured over five bakes, 2026-09-17.**
The smoke job selects only `/chicago/4d/tools/` and
`/chicago/4d/docs/SITE-BUDGET.md`, using non-cone sparse checkout, `blob:none`,
and depth 1 at the bake's exact output SHA. Non-cone mode excludes ancestor
files as well as unrelated tenants. At `c66b9a29`, those 423 files contain
**12,227,359 bytes**, versus **3,783,182,311 bytes** across the tracked repository
(99.68% fewer selected working-tree bytes). These are file-size counts,
**not** network-transfer or checkout-duration measurements.

Dependency audit: `smoke_renderer.mjs` imports `critic_metrics.mjs`,
`drawn_placement_census.mjs`, `drawn_timber_census.mjs`, and
`road_band_movement.mjs` from `tools/`; their imports are Node built-ins.
Its disk baselines are `road_band_baseline.json` and `far_timber_baseline.json`
in that directory. Playwright is installed separately. Page modules, resident
index, geometry and all HTTP-served resources resolve inside the downloaded
published mirror. T-1156's boot measurement imports Node built-ins and
Playwright, serves that mirror, and reads its limit from `SITE-BUDGET.md`.
The source renderer, data, assets and other monorepo projects are not needed.

A fresh local network fetch at that SHA, using `--depth=1 --filter=blob:none`
and these exact sparse patterns before checkout, took **30.423 s** (fetch
8.524 s, checkout 21.899 s), materialized exactly the 423 selected files, and
stored **5,559,171 bytes** under `.git`. This checks the fetch recipe; it is not
a GitHub-runner tail sample.

In an isolated sparse checkout with no source renderer/data/assets, the unchanged
smoke ran stage 9 plus always-on checks at both release viewports against the
stable published fixture exported for T-1156 (`01ce6b77`): **46 passed, 0 failed**,
zero page errors, **5 m 21 s**. The boot check passed at **7.270 MB / 12 MB**
across 916 requests. This proves those browser runs and the audited imports
resolve without the rest of the repository; it is not a full 13-stage smoke pass.

**The actual job-history comparison:** exact `Run actions/checkout@v4`
step timestamps from five bake runs, all eight legs per bake, latest attempt.
Runner queue time is excluded; p90 uses nearest rank. Each of the 40 checkouts
completed successfully; none was censored. The same sparse configuration was
used throughout; sample refs differ only by a workflow comment to trigger a bake.

| cohort | n | median | p90 | max | >5 min | >13 min |
|---|---:|---:|---:|---:|---:|---:|
| T-0181 historical desktop tail, #271â€“#391 | 104 | 38 s | 331 s | 1801 s | 11 | 7 |
| T-0437 desktop tail, five bakes | 5 | 3 s | 4 s | 4 s | 0 | 0 |
| T-0437 all eight legs, five bakes | 40 | 3 s | 4 s | 5 s | 0 | 0 |
| Concurrent unchanged full checkout, #606, all eight legs | 8 | 183 s | 414 s | 414 s | 2 | 0 |

The historical and new desktop-tail rows are the like-for-like comparison.
The all-leg rows are supporting evidence, not 40 independent bake runs.
The contemporary [full-checkout baseline #606](https://github.com/kevinrhaas/custom/actions/runs/35249224177)
measured 41, 44, 46, 92, 274, 291, 333 and 414 s; its desktop tail was 291 s.
This short follow-up shows the previous upper mode absent under these runs;
it does not guarantee that no future checkout will be slow.

| bake | completed checkouts | range, all legs | p90, all legs | desktop tail | >5 / >13 min |
|---|---:|---:|---:|---:|---:|
| [#611](https://github.com/kevinrhaas/custom/actions/runs/35250863185) | 8 | 2â€“4 s | 4 s | 2 s | 0 / 0 |
| [#613](https://github.com/kevinrhaas/custom/actions/runs/35251010985) | 8 | 1â€“4 s | 4 s | 3 s | 0 / 0 |
| [#614](https://github.com/kevinrhaas/custom/actions/runs/35251015637) | 8 | 2â€“4 s | 4 s | 3 s | 0 / 0 |
| [#615](https://github.com/kevinrhaas/custom/actions/runs/35251020803) | 8 | 2â€“5 s | 5 s | 3 s | 0 / 0 |
| [#616](https://github.com/kevinrhaas/custom/actions/runs/35252272736) | 8 | 2â€“4 s | 4 s | 4 s | 0 / 0 |

**No attempt was silently dropped.** [#612](https://github.com/kevinrhaas/custom/actions/runs/35251007292)
failed before smoke when the unchanged `drain-selftest.mjs` hit `ENOTEMPTY`
removing a temporary `.git/objects` directory; it has no checkout reading.
#616 replaces that missing bake. The timestamped audit is
[`measurements/T-0437-checkouts.json`](measurements/T-0437-checkouts.json).
All 40 jobs are now terminal: **27 passed, 8 failed, 5 cancelled**. All 40
checkout steps succeeded. The eight stage 3â€“6 triangle-budget failures also
occur in baseline #606 and are addressed by T-1245 (#1406), already on target
`dev`; the sampling refs predate it. The five cancellations are #611 smoke
bodies superseded by the final workflow push, after their checkout readings.
This is **not a claim that five full renderer matrices passed**.

**The completed sample refutes the provisional 30-minute cap.** The first
snapshot contained 23 completed bodies and a largest successful body of 23 m 07 s.
Three later successful desktop `10-13` bodies took **31 m 49 s** (#615),
**31 m 59 s** (#614), and **32 m 10 s** (#616); a 30-minute cap would have
killed all three. PR #1407 landed the partial-snapshot cap before this correction.
The checkout improvement stands; the smaller body bound does not.

**The corrected cap is 40 minutes**, reduced from the original 45, using the
completed results. Largest successful body: **1930 s / 32 m 10 s** (#616).
Largest overhead of a successful job: **51 s** (job wall time minus body),
including checkout, Playwright, artifact, boot check where selected, and cleanup.
Combining these maxima gives **1981 s / 33 m 01 s**. Add 20% (**2377.2 s**) and
round up to the next five-minute interval: **2400 s / 40 minutes**. This leaves
**419 s / 6 m 59 s / 21.2%** headroom. The failed and cancelled bodies do not
count as successful-duration samples. The reasoning is beside `timeout-minutes`;
all eight legs and the blocking `open-pr` dependency remain. Future growth needs
another complete reading, not an assumption that a faster checkout makes the
renderer body cheap.

**AND THE THREE CAPS IN THIS SECTION BOUND THREE DIFFERENT THINGS â€” corrected
2026-09-03 by T-0450, on the owner's report.** Everything above is written against the
**600-second** per-command ceiling, which is the constraint on a steward run and is
correct as it stands. Two other caps get quoted beside it and neither is that one, nor
each other's:

| cap | what it bounds | where it is written |
|---|---|---|
| **600 s** | ONE foreground command in a steward run | the harness â€” this section |
| **30 min** | ONE LEG of the nightly gate: one viewport over one stage range, eight legs in parallel | `chicago-4d-bake.yml` Â§ `smoke`, `timeout-minutes` |
| **90 min** | the WHOLE body in one process, both viewports, no per-leg cap at all | `chicago-4d-smoke.yml` Â§ `smoke`, `timeout-minutes` |

`docs/SMOKE-BUDGET.md` opened by telling T-0170, T-0173 and T-0181 that the 30-minute
figure their margins are taken against "is not this machine's", with the whole gate's
**55 m 10 s** offered as proof. **It is not proof â€” the two are not the same quantity**,
and 55 m 10 s is a reading of the third row, comfortably inside its own 90-minute cap.
Those three tickets were reasoning about the leg cap correctly and the page has been
corrected to say so. **The machine is the same one, too**: the nightly gate's legs, the
full-body run, the dev gate and the improve runner are all `runs-on: ubuntu-latest`, the
two smoke workflows install the same `playwright@1.56.1` and chromium alone, and
`smoke_renderer.mjs` passes `--enable-unsafe-swiftshader` wherever it runs â€” so
SwiftShader is a property of the suite rather than of one runner. T-0450 measured one leg
at **4 m 40 s** on the gate runner and **4 m 44 s** on the improve runner; that pair is
recorded with its provenance, and its unverified half named as such, in
`docs/SMOKE-BUDGET.md` Â§ THREE CAPS.

**None of this moves a number above.** The 600-second ceiling this whole section is built
on is untouched, every reading stands, and the cuts sized against them stand. What
changes is which cap a LEG's margin is compared with, and that comparison now lives in a
tool rather than in prose: `node tools/smoke_budget.mjs --legs` prices each of the
nightly gate's legs â€” read from the workflow, never restated â€” against the 30-minute cap,
and `--self-test` fails if those ranges ever stop tiling the parts exactly once.

### NEXT UP â€” every row says whether a visitor can SEE it

**Rewritten 2026-08-15 on the owner's report that the loop does research and organisation rather
than work on the app. Measured: 15 of the last 30 changelog entries say nothing you can see
changed, and v124â€“v137 is fourteen invisible runs in a row.** Two causes, both fixed here. The
first is the rule â€” see AGENTS.md Â§ THE VISIBLE-PROGRESS RULE, which caps invisible runs at one in
four. The second is this table: it had grown ~20 completed rows above the live picks, so the
visible parcels were the hardest ones to find. Completed work now lives in its own section below,
not at the top of the queue.

> ## â›” THIS TABLE IS FROZEN AS OF 2026-08-17 â€” THE LIVE QUEUE IS `tickets/QUEUE.md`
>
> On the owner's direct request the operational backlog moved to **`tickets/`**: one file
> per ticket, `QUEUE.md` holding the priority order (the owner orders it; agents only append
> and remove), `BOARD.md` generated, and `tools/ticket.mjs check` gating it all in check.sh.
> His requests were untraceable in this file â€” the K-series he asked for in August was
> sitting below line 9,300 with no status tags while the loop picked from this table â€” and
> he could not reorder priorities without editing prose. Every open parcel below became a
> ticket carrying its old id in `legacy_id`; the deep boxes in this file remain the
> reasoning archive and tickets link into them. **Do not add rows here. Do not pick from
> here. Read AGENTS.md Â§ THE QUEUE.**

| # | lane | parcel | why first |
|---|---|---|---|
| â€” | RENDERING | ~~R-BUG7~~ | **SEEN** | **DONE 2026-08-17 â€” the stalk was aimed at the stem and then TURNED to a random bearing, and now the flower is hung by its foot.** `maybeHead` computes `tiltAz` so the stalk leans back to the stem and passes a random `yaw` beside it; `push`'s Euler is `YXZ`, so the yaw spins the whole tilted head and the azimuth with it â€” and `push`'s own docstring says *"Pass `yaw` 0 alongside a tilt"*. **Four repairs computed that bearing correctly and not one reached the geometry.** The repair is not a fifth aim: the archetype's origin moved to the FOOT of its own stalk, so the offset from the stem is generated by the rotation and `foot <= plantH` makes attachment an invariant at every fade rather than a number. **38 of 11,752 drawn heads over 32 poses â†’ 0**, all 38 `corymb`, worst foot **58 cm** from any stem; foot-to-stem median **21 mm â†’ 0**. Read its box before adding a per-instance rotation to any set |
| â€” | RENDERING | ~~R-BUG5b~~ | **SEEN** | **DONE 2026-08-16 â€” it was the PLANTER after all, and the whole near-field wood was drawn mirrored.** The loop asks every question in ENU (`isWater`, `communityAt`, `surfaceHeight`, `blocked`, `noteStation`) and hands its ENU north straight to `addTree`, which takes a three world **z** â€” and `enuToWorld` is `(e, y, -n)`. So every tree was TESTED at `(px, pz)` and DRAWN at `(px, -pz)`: **391 stations, 0 wet, 64 of the same 391 wet at their mirror, 10,734 vertices of timber over open water and the worst 48 m from dry ground.** Three green gates all walk `stations`, which is the point that was TESTED â€” **nothing had ever read the geometry back**. Read its box before trusting any placement gate in this file |
| â€” | RENDERING | ~~R-BUG5~~ | **DONE 2026-08-16 Â· a real second fault, but NOT the owner's picture (see R-BUG5b)** â€” it was the SKYLINE, not the planter. Both of the owner's populations are ONE body of far timber authored **between the two banks** of the main stem, 39 of 39 samples over water and **3.347 m** under its surface; the scatter is the horizon solver's own gap modulation breaking the same run into crowns. Both existing gates were green because both count the near-field planter's 632 m square, and **nothing had ever asked the five `FAR_TIMBER` polylines where they stand**. Read its box before quoting any horizon-timber number |
| â€” | RENDERING | ~~R-BUG5(b)~~ | **SEEN** | **DONE 2026-08-27 (T-0031) â€” the owner picked route 1 and the belt is back on the skyline.** `main_stem_belt_east` is now DERIVED from the committed `south_water` centreline â€” offset half a platted corridor south, clipped east at the committed `wells` easting `timberEastLimits()` already hands the near planter â€” and `tools/derive_timber_belt.py --check` re-derives it on every commit. Census **39 of 39 samples over water, 3.347 m deep â†’ 0 of 136**; the old stub also ended **66.7 m east** of the street it was named for. The side of the street is the one assertion and it is **L182** |
| â€” | RENDERING | ~~R-BUG3c~~ | **DONE 2026-08-15** â€” neither surface moved: the publish step quantises the ground onto a **306 mm** vertical lattice AFTER the only gate that measures it, burying the road and the flora by up to **228 mm**. The heights are read back off the field at load, and two gates now hold the file that SHIPS. Read the box before quoting any ground number |
| â€” | RENDERING | ~~R-W4c(a)~~ | **DONE 2026-08-15** â€” the flower-load recipe's hue cut at 50Â° runs through the middle of a July prairie's bloom, so `0.0012` is not a count of flowers. (a) landed the honest measurement; **(b) is the tuning half and must take (a)'s committed numbers as its baseline** |
| â€” | RENDERING | ~~R-W4c(b1)~~ | **DONE 2026-08-15** â€” **there is no 4â€“6 % target.** Its remnant half cites no photograph this repository holds; its planting half does not reproduce (**5.54 %**, and 12.91 % is not on that frame under either ordering); and the repair R-W4c(a)'s diagnosis implies **fails** â€” reordering the tests takes precision **0.998 â†’ 0.062**, so the flower test cannot see a flower either. Read its box before quoting any flower number |
| â€” | RENDERING | ~~R-W4c(b2)~~ | **DONE 2026-08-27 as T-0034 â€” the bar that governs the bloom is the LATTICE, and the records already asked for more bloom than it can draw.** `forbShare` clamps at one plant per lattice slot â€” **0.346 forbs per mÂ²** â€” and the mesic prairie's own records sum to **0.408** at their upper bounds, so nothing had to be invented: the forb stratum is dealt off the TOP of every recorded range instead of its midpoint (L182), which is **1.236x** at the mesic prairie, **1.254x** at the wet prairie, **1.572x** on the sand prairie and, measurably, **nothing at the other six** â€” they were already over the ceiling. `prairie_west` **206 forbs / 1,617 heads â†’ 256 / 1,968**. **It is the last raise either prairie can be given**: both now read a share of 1.000. Read its box before raising any flora density |
| â€” | RENDERING | ~~R-W6~~ | **DONE 2026-08-16** â€” **yes, at 16 bits**, and the artefact was not invisible: the 14-bit ground stands up to **46.3 mm** above the field, past the 22 mm road lift at 87 sample points, **one of them 1.9 m from South Water Street's centreline**. 16 bits costs **1,116 bytes** and takes the worst error to 12.9 mm, under the lift everywhere; the uncompressed 5.8 MB would buy 12.9 â†’ 7.7 mm, and 7.7 is DECIMATION the master carries too. Read its box before quoting any payload or lattice number. **Its 12.9 mm no longer describes the tree** â€” re-measured 2026-08-23 on the terrain as extended east, the same 16-bit ground is **77.1 mm** worst with **56** samples past the lift, on 60â€“90 % slopes that did not exist in the box R-W6 measured. T-0152 |
| â€” | RENDERING | ~~R-BUG4~~ | **DONE 2026-08-15** â€” the wet-corner rule deleted the dry half of a road panel with the wet half. Clipped at the waterline now: **28 panels / 62.7 m** of roadway recovered, and the gate asserts the invariant rather than the number |
| â€” | RENDERING | ~~R-W4a~~ | **DONE 2026-08-15** â€” the horizon figure counted the town's roofs as timber (62 % of it at `prairie_south`), the Gâˆ’B discriminator this project named was measured and **refuted**, and the replacement cannot move when a block lands. Read its box before quoting any horizon number |
| 2 | RENDERING | **R-BUG4** | XS, owner-reported. A wet CORNER deletes a whole road panel, dry half included: **28 panels / 62.7 m** of roadway removed where the centreline is dry land |
| 3 | RENDERING | **R-W4a** | the horizon-timber metric counts gable ends as trees, so W4's headline number is unmeasurable and a town parcel already banked a false pass. Prior to every other W4 half Â· *promoted 2026-08-15: R-M1b, which was #1, is blocked on the owner* |
| â€” | RENDERING | ~~R-M1~~ | **R-M1a DONE 2026-08-15** â€” the two scales are measured and their baseline is committed. **R-M1b is NOT a pick: it is blocked on a threshold source, because the photograph R-M1 named to derive from contains no dirt track.** Read R-M1b's box before touching it |
| â€” | RENDERING | ~~R-M1c~~ | **SEEN** | **DONE 2026-08-16 â€” the road score divided by probes SEEN, so an occluder RAISED it.** One band, three builds, one evening: **seen 157 â†’ 177 â†’ 163** and the old score **62 % â†’ 54 % â†’ 59 %**, while the number of readable stretches never moved off **96** and `nBare` was **182 in all three**. The build with the whole wood on the wrong side of the river scored HIGHEST; K45(b2) would have gone green by planting more timber in front of the road. **The instrument was already built and already printing** â€” `shotMF`'s own comment says the marked-only denominator "drops instead of failing" â€” and nothing had ever divided by it. Scored on `nBare`: **53.3 / 52.7 / 52.7 %**, under the 0.55 bar in all three. Read its box before quoting any road-contrast percentage taken before this date |
| â€” | RENDERING | ~~R-W1~~ | **SEEN** | **LANDED ON `dev` 2026-08-16 â€” the light was wrong by 1.9Ã— and 2.9Ã— red against its own sky, and the honest sky costs the roads.** Literal black pixels 12,063 â†’ 0 at three stations; `south_water` 250â€“600 m falls **71 % â†’ 16 %**. **NOT FOR PROMOTION** until the owner walks `/dev/` or R-W2 buys the contrast back â€” read its release-condition box before any promotion. Its third finding is R-M1d: the suite reported **229/2 before and after**, because a station already red on another band hides a 55-point collapse |
| â€” | RENDERING | ~~R-W2a~~ | **DONE 2026-08-16** â€” the material sheet, measured out of the shipped GLBs: **1,353 material slots, 32 names, 41 colours, 18 roughness values, zero textures**. Five findings, and two of them block texturing outright: **the chimney is not a material here** (219 stacks painted `roof`) and **no record states a roof covering** (315 roof types, 0 coverings). Read `docs/RESEARCH/materials.md` Â§4 before quoting any material number |
| â€” | TOWN | ~~T-A15~~ | **DONE 2026-08-15** â€” `blk_randolph_clark`, the block opposite the courthouse: the first with a store on it, the face rule EXTENDED to rank one (**K32**), the end rule measured at **1.02Ã— / 7.5 m** and declared exhausted (**K31**), and **two of T-A14's three adoption candidacies refuted** â€” the laundress and teamster arguments never claim a floor, so they fail rule 6's test 1. Read finding 3 before quoting any adoption test |
| â€” | TOWN | ~~T-A16~~ | **DONE 2026-08-15** â€” `blk_randolph_lasalle` is **the public square** and is not a building site. It was withdrawn rather than built: no lots, no roofs, a gate, and **two documented buildings moved off it**. The block parcel's own gates all passed on the old placement, because not one of them asks whether the ground was for sale. Read its box before scheduling anything anywhere |
| â€” | TOWN | ~~T-A3h~~ | **DONE 2026-08-15** â€” the last open block entry, and the two adoptions it predicted are the two it made: `blk_randolph_dearborn`'s D3 to the carpenters and its D1 to the labourers, measured with `tools/measure_adoption_tests.py` rather than recalled. **Its finding is about the other two**: the D4 and the D2 that pass as a "second roof" are pairs this layer has NEVER housed â€” the D4 evidence is one household in the NORTH, the D2's is four in the NORTH and WEST â€” so every second-roof refusal K28 has collected is a candidacy built from two projections of one table. Read its box and K28's before quoting any adoption test |
| â€” | TOWN | ~~T-V1(a)~~ | **DONE 2026-08-15** â€” the stamp is **not** at `south_water`: every twin in the town is in the North Division parcel, **36 of its 60 roofs**, and the census found something bigger â€” **40 eaves outside the band their own note cites**, 18 of them in a parcel that samples its footprints and says so. (b) is written, measured and **blocked by a circular dependency in the pipeline** â€” read its box before touching any dimension on a baked record |
| 2 | TOWN | **T-V1(b)** | the sixty North records: **NEEDS ONE BAKE**, and cannot go green on the improve runner. A policy question for the owner, not an engineering one |
| â€” | TOWN | ~~T-I3(a)~~ | **DONE 2026-08-16** â€” the town's public buildings are **three roofs** and this project already had all three, so the refusal is now absolute rather than argued. The finding is the fourth building: **the court-house was not built yet** â€” Andreas fixes the season, the month AND the corner the record said nothing fixed, and the citation it had was a **picture caption** â€” so a record is taken OUT of a scene on evidence for the first time. Read its box before quoting any civic number |
| â€” | TOWN | ~~T-I3(b)~~ | **DONE 2026-08-27 as ticket T-0032, route 1** â€” the owner's "close it at 665 or 662" is closed at **662**: `roof_total` 665 â†’ 662, `I3` 6 â†’ 3, `principal_functional` 511 â†’ 508. The correction found a **second** fault in the same row â€” `institutional_public` was apportioned south 10 / west 1 / north 1 while the named records stand **south 5 / west 1 / north 3** â€” so the south district goes 370 â†’ **365** and the north 150 â†’ **152**, not the 370 â†’ 367 the box predicted. Every I3 slot has left the block schedule and the gate screen now reads *of the 662 the town held*. Read its box before quoting any civic or roof-total number |
| â€” | TOWN | ~~K30(a)~~ | **DONE 2026-08-16** â€” it is **29 buildings on eight streets**, not three on one, and every one of them is a record a PERSON placed: **zero** generated roofs lap a corridor, across 332 placed phases. The depths are bimodal with an empty gap at 1.98â€“3.48 m, and **13 of the 17 deep ones are South Water**. T-A7's "fourteen" does not reproduce **at its own commit** (16 there, the same 16 today), and the anchor-convention suspect is **refuted** â€” recentring makes 10 of the 29 worse. Read its box before quoting any intrusion number |
| â€” | TOWN | ~~K30(b)~~ | **DONE 2026-08-16 Â· ITS CAUSE IS REFUTED 2026-08-22 â€” read K30(d) before quoting any of this row.** The anchors it compares with the half-width are BACK corners, so the comparison could not see the displacement it looked for; the real cause is the committed `south_water` centreline standing 4.3â€“8.8 m south of the control the placements were offset from. Its own text follows: the cause is the **drawing**, and the Wacker made-ground suspect is **refuted** by arithmetic: the anchors sit 11.64â€“15.30 m from the centreline against a 12.192 m half-width, with both signs, so no displacement of 4.51â€“8.17 m is there. The records are derived to their FRONTAGE and drawn with the body growing north from it (331 of 333 footprints grow from the minimum corner), so each stands in the road by its own depth â€” **all 17** deep records, and reflection takes 12 of them under 1 m. **The residual law** settles the shallow tail without moving anything: what survives correct drawing IS the point's own penetration, to 0.10 m. Read its box before quoting any intrusion cause |
| â€” | TOWN | ~~K20~~ | **DONE 2026-08-16** â€” the invented-name allocator, measured properly for the first time: **73 of 113 renamed by ONE new household**, not the 17â€“25 the eleven by-product measurements reported, and never zero in the two big buckets. It is **10** now, and the report prints each bucket's **pool pressure** so the residual cannot be misread â€” at 0.14Ã— it renames **one**, at 2.03Ã— it renames ten, and that is the pool being too small. Unwelding the given name from the surname exposed **two identical residents**. Read its box before quoting any churn number |
| â€” | TOWN | ~~K29~~ | **SEEN** | **DONE 2026-08-27 (T-0022) â€” ITS PREMISE IS REFUTED AND THE RE-APPORTIONMENT IS REFUSED.** L99 and L100 worried that the schedule "will keep dealing cabins to commercial frontage"; measured, the fault ran the other way. South Water Street's line carried **15 invented buildings and NOT ONE of them log**, against a documented line of 8 with Hogan's log store on it, because the recipes' own face rule â€” "the two meanest take Lake" â€” had put all five dealt log dwellings on the OTHER principal thoroughfare. The owner's plate of the row draws it as *log and frame shoulder to shoulder* and this project had taken only the half of that sentence about shape. **No schedule term was written**: ten records changed places, nothing was added, and `tools/measure_frontage_fabric.py` now holds it. K29's other half â€” weighting the trade families ONTO the business front, which the same census supports at 80 % â€” **shipped 2026-08-27 as T-0213**: the documented trade share is monotone in the committed street hierarchy (0.7778 principal / 0.4545 ordinary / 0.0000 light) and `tools/reconcile_665.py` now weights each platted block by its own four faces. Read its box before quoting any frontage rule |
| â€” | TOWN | ~~K28~~ | **DONE 2026-08-16** â€” three questions, three clauses, **two gates, and not one record moved**. The table is **projections** (the pair reading is refused because it refuses T-A4's fourteenth labouring household, one of the four rule 6 says its third test recovers); there **is** a cap, one adoption per trade per block, which is what makes the projections safe; and test 1 means the trade's **own committed text**, so the laundresses' D2 and the teamsters' D4 are refused with the remedy named. All **21** standing block adoptions already obeyed it. Read its box before quoting any adoption rule |
| â€” | TOWN | ~~K25a~~ | **DONE 2026-08-15** â€” it is **98 values on 80 of 249 records**, not 54 on 193, and **24 causes, not 98**: seven metre values hold all 54 eaves and six degree constants hold all 38 pitches, because the generator authors the archetype's constant and the note cites the family's band. **Roof pitch had never been measured by anything.** The sub-1-ft question is decided â€” they are failures, and nearness is the diagnosis. Read its box before quoting any band number |
| â€” | TOWN | ~~K33~~ | **DONE 2026-08-15** â€” it is **623 values on 227 of 249 records**, not 581, and the extra 42 are the finding: `roof_pitch_deg` cites a band on five families whose roof line is **"gable or shed"**, a form with no slope, and K25(a) could not see them because **a value with no band is never tested against one**. Route 2 (split the note), and route 3 is measured as unavailable â€” the confidence floats are in the mesh hash and prose is not. The assertion is **absolute, not a ratchet**. Read its box before quoting any citation number |
| â€” | GROUND | ~~T-E2~~ | **DONE 2026-08-15** â€” 26.5 % of the modelled land above the water surface is the reservation or the bar, and every gate this project had would have built on it. Nothing moved: **zero** anonymous roofs were there. Read its box before quoting any buildable-ground figure |
| â€” | GROUND | ~~T-E4~~ | **REFUTED 2026-08-24 (T-0026)** â€” there is no southern buildable ground to widen onto. The modelled box ends at local **N -400 m**, INSIDE Washington Street's own platted corridor; of the 0.0819 ha of land south of that corridor, **0.0000 ha** is in the South Division. Madison â€” the plat's south boundary â€” is **125.2 m** further south, and the plat's last tier (6 blocks, 48 lots, 6.28 ha) has **0 of 24** boundary points on modelled ground. The South's 120 roofs were gated on street control; the blocker is **terrain**, and street control stops where the ground does. Read its box before quoting any southern-ground figure |

**Every row is tagged. `SEEN` means a screenshot from the same spot looks different when it
merges. `UNSEEN` means it does not â€” those are real work and this project needs them, but they are
rationed.**

| # | lane | parcel | seen? | why |
|---|---|---|---|---|
| â€” | RENDERING | ~~K49(f)~~ | **SEEN** | **DONE 2026-08-16 â€” 2 species absent â†’ 0, and the block's own phase pays for itself twice.** The even deal dealt the SAME 64 values of `u` in every block of the world, so a band narrower than 1/64 fell between two of them EVERYWHERE: **45 matrix bands, exactly 2 under one step, and exactly those 2 were the species drawn nowhere.** Matrix deviation **282.90 â†’ 219.19**. Its finding is not the repair: **K49(e)'s leading explanation is refuted for the bigger of the two rows it was written about** â€” the settled town recovers 23.66 of its 24.87 regression on a change that touches no filter. Read its box before quoting K49(d) on a regressed row |
| â€” | RENDERING | ~~R-A1~~ | **SEEN** | **DONE 2026-08-16 â€” the Road visibility slider, off by default, and the first parcel taken by PULLING A SEEN ROW UP when every numbered one was blocked.** Its finding is about gates, not roads: **an inertness assertion needs a liveness assertion beside it**, because "the default is unchanged" passes identically whether a control is wired correctly or wired to nothing â€” R-BUG1's dead `--no-sun-shadow` one parcel earlier. And the instrument was measured before its threshold was set: the 12Â² frame signature scores the aid at **worst 2 against a residual of 0**, the same difference at 48Â² is **worst 6**, and nothing about the scene changed between the two runs. Read its box before adding any preference to Settings |
| â€” | RENDERING | ~~K24~~ | **SEEN** | **DONE 2026-08-17 â€” the Brightness slider, off by default, and the SECOND parcel taken by pulling a SEEN row up when every numbered one was blocked.** Owner-requested on 2026-08-14 and deferred behind PR #125 by a sequencing note that turned out to be a claim about a diff nobody had checked: the aid is one constant and one method, not a `world.js` rewrite. **Its finding is about R-A1's gate rather than about light** â€” `Object.assign` copies what a getter returns, so `get roadAid()` had been a frozen `0` since it shipped, and both of R-A1's readback assertions expect `0`. The control was live; its report of itself was not. Read its box before adding any reading to `window.__chicago4d` |
| â€” | RENDERING | ~~K51~~ | **SEEN** | **DONE 2026-08-17 â€” 139 researched animals reached no browser at all, and the whole layer is now a card in the Evidence panel.** Fauna figures reaching a visitor **0 of 30 â†’ 30 of 30**; the dataset's unread population **58 of 100 â†’ 28**. Its findings are about instruments, not animals: K42's assertion 3a **fired exactly as designed** the moment the directory was opened, and **two of that gate's own controls had been written against the repository's state** â€” one became a copy of the measurement and the other printed SILENT rather than failing. And `docs/LIBERTIES.md` **L2 said "ambient wildlife is rendered sparsely" for eight days while nothing was rendered at all**. Read its box before quoting any layer-read number |
| â€” | RENDERING | ~~R-BUG6(a)~~ | **SEEN in motion** | **DONE 2026-08-17 â€” the shadow box was re-centred on the visitor's exact position, so its texel lattice slid under every step and re-quantised every shadow edge in the town.** It moves in whole texels now: with the camera held still and the box slid half a texel, `from_above` **2,023 changed pixels â†’ 0** and `descend_main_stem` **5,650 â†’ 0**. Three findings, and two of them are about instruments: **the control that "cleared the shadow map" was inert** (a compile-time flag is not a runtime handle â€” it moves 5,439 px now), and **a sub-pixel nudge cannot measure a shadow box at all** â€” scaled up to a half texel it changes 29,138 px with the fix and 28,784 without, sign included. The answer to the parcel's title: **the shadow map is 14â€“16 % of the town's flicker**, not the cause of it. Read its box before quoting any flicker number |
| â€” | RENDERING | ~~R-BUG6(b)~~ | â€” | **DONE 2026-08-17 â€” the premise was wrong and two tests say so. The residual is NOT co-planar ties: switching the depth test from `LessEqual` to `Less` moves 36,187 px of the frame and only 13 of the 1,108 flickering ones (1.2 %), and 5Ã— the depth precision leaves 604 of 607 surviving.** It is the town's own edges being resampled, which is antialiasing and not a defect â€” R-BUG1's near plane had already taken the real one. Three findings: **an exact tie is STABLE and a near tie is what flickers** (which is why 3.5 % of this frame is co-planar and none of it shimmers); the ownership instrument (`tools/measure_tie_class.mjs`, 0 unattributed, buildings + trees own 94.5 % of the flicker on 7.7 % of the frame); and **`measure_river_edge.mjs`'s bank mask counts the SKY as water** â€” rows 0â€“200 are 1,280 of 1,280 "waterish", so no bank-line pixel count from it is a statement about the river. Read its box before quoting any flicker or bank number |
| â€” | TOWN | ~~K52~~ | **SEEN** | **DONE 2026-08-17 â€” the layer that already had a reader was hiding seventeen households, and the reader is the reason nobody looked.** A household reaches a visitor only through a building it `lives_at` or `works_at`, so the 17 whose residence AND workplace are both unattested on 1 July 1835 attached to no building and appeared **on no card anywhere** â€” 20 person entries, one of them the **Mark Beaubien** household, dropped for exactly the thin evidence that makes its record interesting. And the join carried a third of each record it did reach: arrival, origin, reason for coming, presence, a person's age, sex, name basis and sources, and all ten `researched_not_resident` findings reached nothing. **K42's assertion 3a did not fire** â€” the census tool names `flora` and `fauna` only, which is K52(b). The third parcel taken by pulling a SEEN row up when every numbered one was bake-blocked. Read its box before assuming a layer with a reader is a layer that is read |
| **1** | RENDERING | **R-BUG6(c)** | UNSEEN | **NEEDS ONE BAKE.** The 36,187 co-planar pixels above are steady but arbitrary: two surfaces of different colours at one depth, with draw order picking the winner. A question about the models, opened by (b) |
| â€” | RENDERING | ~~K53~~ | **SEEN** | **DONE 2026-08-17 â€” twenty-one shrub records were drawn with the forb archetype, and the clamp that made that survivable was hiding the recorded width.** Shrubs 0 â†’ **14** drawn over 32 poses, clump width **0.40 m clamped â†’ 1.80 m median**, and the census is identical plant for plant (2,201 forb-layer plants before, 2,187 + 14 after, every zone conserved). Its finding is the reason the number is 14 and not 140 â€” **the forb lottery deals by HEAD COUNT, so a hazel covering 7 mÂ² competes as one plant against 40 wild leeks per mÂ²**, and the wet woods' attested dominant shrub gets 0.2 % of the slots. Opened as **K54**. Read its box before quoting a shrub count |
| â€” | RENDERING | ~~K54~~ | **SEEN** | **DONE 2026-08-17 â€” the two strata were sharing one lattice, and where the herb layer saturates it the deal is a subsample by head count. 4 bushes standing over the eight stations â†’ 181.** The shrubs are dealt from their own pass at their own recorded clump density: `z06_dense_forest` **2 â†’ 156** drawn and **40.1 %** of its recorded 94.9 % cover, the riverbank dogwood belt **20.1 % against a recorded 19.5 %**, matrix deviation unmoved to the second decimal and **0 of 98** pairs drawn nowhere. Two findings: **the slot count still mixed units** and planted the riverbank understory **8.8Ã—** too thickly (K55), and **the instrument this parcel named cannot answer its question** â€” "deviation from the recorded cover" has measured the lattice against its own target since K49(c2). Read its box before quoting 89.11 or any deviation sum across two builds |
| â€” | RENDERING | ~~K56~~ | **SEEN** | **DONE 2026-08-17 â€” 16 sprays â†’ 32, shell fill 17.7 % â†’ 30.9 %, and the lowest band arches down over the stems.** The size did NOT move: a spray is a leaf MASS, not a leaf, so shrinking it would have bought a smaller plate with more sky round it. Follow-up **K57** |
| â€” | RENDERING | ~~K57~~ | **SEEN** | **DONE 2026-08-17 â€” the question cannot be asked at a fixed plate area, because the plates are what carries the RECORDED clump width.** 64 sprays at the shipped total area buy 8.5 points of cover and pay **reach 0.990 â†’ 0.890** of the recorded half-width for them, plate 37 â†’ 26 cm. So the grain trades against TRIANGLES: at the shipped plate size, 32 â†’ 48 â†’ 64 sprays cover **36.9 % â†’ 46.9 % â†’ 51.3 %** of the outline for 72 â†’ 104 â†’ 136 triangles, and **48 is where the return halves**. Stem cover 40.9 % â†’ 51.3 %, 38.8 % of the frame changed. Two findings: **K56's 17.7 %/30.9 % were taken by a script nobody committed** â€” the instrument is `tools/measure_spray_grain.mjs` now, reproducing K56's plate area to the digit off `renderers/web/js/shrub-grain.js`, which imports nothing; and the wet woods' ring is **167 shrubs, not the 156 K54 and K56 quote**. Opened **K59**, which is now DONE and spent the 4.4 points: read K59's box before timing anything in a browser here. Read this one before shrinking any archetype plate |
| â€” | RENDERING | ~~K55~~ | **SEEN, and only just** | **DONE 2026-08-17 â€” the same fault runs BOTH WAYS, and for the herbs it ran the other one.** A cover fraction read as a count over-planted the 2.25 m dogwood by 8.8Ã— and UNDER-planted the riverbank's 10 cm ground layer by **96Ã—**: `z05` 0.025 â†’ 2.407 plants/mÂ², `z03` 0.123 â†’ 1.254, forb slots **781 â†’ 923** over the eight stations, `z03`'s own layer **31 â†’ 84**, matrix and shrub unchanged to the second decimal. Three findings: the sign of the fault is decided by whether one plant covers more or less than a square metre, so the queue inherited "over-planting" from the case measured first; **three of the parcel's six named rows were never faults** â€” the `basis` column was printing `subsetOn`'s default argument and the matrix slot count comes off `cover.matrix_fraction`; and the count moved a fifth while the frame moved **0.15 %**, with `z10_settled_town` â€” the parcel's predicted visible half â€” not moving at all, because its share was clamped before and after. Opened **K58**. Read its box before quoting a forb count or calling a mixed list a defect |
| â€” | RENDERING | ~~K58~~ | **SEEN** | **DONE 2026-08-28 as T-0019 â€” it is NINE forb layers of ten, not six, and the shortfall is now declared rather than derived.** `tools/forb_clamp_baseline.json` names every (community, side) the 0.346 plants/mÂ² lattice ceiling binds, and `measure_sward_draw.mjs --gate` fails when the set drifts. K58's six were counted at the recorded MIDPOINTS; T-0034 deals the forb stratum off the upper bound, so `z06_dense_forest` asks **66.381 /mÂ² and draws 0.5 %**, the marsh 22.000 and 1.6 %, and the two prairies and the lakeshore joined the clamp. The marsh's WET side is measured for the first time. No ceiling was raised: every route out buys plants with geometry in the two layers already carrying the most, and the detail ceilings are breached on dev. Read its box before quoting a forb density or the count of clamped layers **AMENDED 2026-08-28 by T-0282 â€” it is TEN, and the tenth is a stratum the declaration could not see.** `flora.js` deals four (stratum, side) lotteries through the same `shareOf` against the same ceiling; T-0019 declared the forb ones. `z06_dense_forest`'s SHRUB layer asks 0.403 clumps/mÂ² against 0.346 and has been over it since K54 named it, and `shrubShareWet`/`shrubDensityWet` were not exported at all. The declared identity is now (community, stratum, side), and `docs/LIBERTIES.md` **L201** is the visitor's copy of the table. |
| â€” | TOWN | ~~K30(c)~~ | **SEEN** | **REFUTED 2026-08-22 (T-0009, K30(d)) â€” DO NOT RUN THIS REPAIR.** The 29 buildings are still drawn standing in the roadway, but not for this reason: `--anchors` finds the record's point at the BACK corner on **all 17** of the deep records and on the kerb face on **none** of them, so the street-facing FACE is what was placed on the frontage and reflection would take twelve documented buildings a full depth behind their own frontage. The cause is the committed `south_water` centreline, deliberately shifted 4.3â€“8.8 m south of the control the placements were offset from. **What to do about it is the owner's, and T-0009 is blocked on him** |
| **2** | RENDERING | **R-W2b** | **SEEN** | wire R-W2a's committed material sheet into the params and records â€” 1,353 materials measured out of the shipped GLBs and currently reaching nothing. **This is what repaints the town**, and R-W2 owns the worst-scored axis on R-G1's whole table (texture, **1.4**) |
| â€” | RENDERING | ~~R-W2c~~ | **SEEN** | **DONE 2026-08-22 (T-0008) â€” the stack is not the roof.** 157 stacks on 143 buildings now carry a masonry material of their own: **brick on 112 framed buildings**, off `frame_tavern`'s committed Petford value moved into the sheet, and a **cat-and-clay daub on 31 log cabins** at the midpoint of the two committed values that bound it. `docs/RESEARCH/chimneys.md` is the fabric argument; L168 records the invention. **Three findings.** It was NOT a one-file fix and it was not palette-only: the two dispositions the archetypes had already argued in prose are two materials, and the fabric had to be researched before either could be chosen. **It cost NO draw call** â€” `buildings.js::materialKey` batches on maps and flags, never on colour or roughness, both of which ride per vertex, so 113 calls before and 113 after at `south_water`. And R-W2a's *219 stacks on 199 buildings* does not reproduce: the resolved parameters of the committed masters give **157 on 143** across four archetypes. Left standing: the fort (**T-0137**) and the placeholders' second brick (**T-0138**) |
| â€” | TOWN | ~~T-V2~~ | **DONE 2026-08-16** â€” the anchor named South Water Street stood 101 m from it, in a field. Now in the street at Wells, both coordinates read from committed data. **It sat on `hold` two days on a number other parcels had already fixed**: the far band it was parked for reads **2.1 L\* / 71 %** today, not 0.5 / 30 %. Its real finding is R-M1c's, from a second direction â€” the field stand scored **100 % on six probes of 510** and the street stand shows **93 perceptible stretches against 31** and scores lower. T-V2b folded into R-M1c; baseline re-shoot is T-V2c |
| **5** | GROUND | **T-E3** | **SEEN** | the heightfield east (= `S2e`). Ground a visitor can walk onto that is not there today |
| 6 | TOWN | **T-V1(b)** | SEEN | the sixty North records â€” but **NEEDS ONE BAKE** and cannot go green on the improve runner. Claim only with the bake available |
| **1** | RENDERING | **R-W2** | **SEEN** | **PROMOTED 2026-08-16 â€” R-W1 landed on `dev` and cannot leave it until this parcel runs.** Textured coverage is the only thing that buys back the contrast the honest sky costs: R-W1 takes `south_water` 250â€“600 m from **71 % to 16 %**, and the near band's opaque *ceiling* is 3.4â€“4.3 L\* whatever the light does. Every road band in the suite is now under or near its bar, and no amount of relighting fixes a surface with no texture on it. Read R-W2a's material sheet first â€” its findings 1 and 2 (the chimney is not a material; no record states a roof covering) bound what can be textured today |
| â€” | RENDERING | ~~R-W3b(a)~~ | **SEEN** | **DONE 2026-08-17 â€” the sun threw a shadow within 60 m of the visitor and nowhere else: 5 to 8 of 331 structures and 0 to 41 of 730 stems, measured at all eight anchors.** It is Â±120 m now, at the SAME texel size (the map doubles with the box), and `green_tree` goes 8 â†’ 27 structures, `south_water` 8 â†’ 26 and 12 â†’ 54 stems. **Its finding is the ceiling: the reach is DRAW-CALL-bound, not fill-bound** â€” every batch entering the box is another call in the shadow pass, and the worst anchor reads 70 calls at 60 m, 74 at 120, 78 at 150 and **exactly 80 at 180, which is the budget**, with the town still two thirds outside the box. Read its box before raising the number |
| â€” | RENDERING | ~~R-W5a2 + R-W3b(a2)~~ | **SEEN** | **DONE 2026-08-17 â€” 16 batches â†’ 1, and the reach went straight from Â±120 m to Â±240 m on the calls it freed.** Roughness is the last thing that was splitting the town, and it is per-vertex now; the worst anchor reads **50 draw calls of 80 where it read 74 this morning**, at the SAME 11.7 cm texel. `green_tree` 27 â†’ **49** of 331 structures and 0 â†’ **70** of 730 stems; `south_water` 26 â†’ **91** and 54 â†’ **239**. **Its finding is that the batch merge is not neutral after all** â€” 942 pixels of 7,168,000 move across seven poses, all of them depth ties between co-planar surfaces of different materials, which is R-BUG6's own class one draw call in. Read its box before quoting a draw-call figure taken before this date |
| â€” | RENDERING | ~~R-W4c(b2)~~ | â€” | **DONE 2026-08-27 as T-0034** â€” the bar is the lattice, the records already ask for 18 % more bloom than it can draw, and the prairies are on the ceiling now |
| â€” | TOWN | ~~T-I3(b)~~ | â€” | **DONE 2026-08-27 as ticket T-0032** â€” closed at **662** on the owner's delegated pick; the institutional matrix row is now the census, and the target is gated against a civic ledger re-derived on every run |
| â€” | GROUND | ~~T-E5(b)~~ | **SEEN** | **DONE 2026-08-24 as T-0027 â€” and it refuted its own question. There is no wet fraction to read: 43,885 samples at 0.5 m over the platted block, 0 of them at or below the water surface, and the block's whole relief is 1.49 in â€” INSIDE the spec's own micro-relief noise, so the terrain models no basin here and a fraction read off it would be a read of the seed. The answer is a DEPTH: the dossier's own bed for zone 15 is +1.0 to +2.0 ft and the committed ground stands 0.84 to 1.96 ft above it, so the pond has to be DUG, not chosen. What was wrong was the SWARD â€” `docs/research/02-flora.md` heads ZONE 3 with the Public Square by name and `z03`'s elevation-band extent could never reach a block drawn at the plain's height. Read its box before proposing an extent for zone 15 |
| â€” | RENDERING | ~~K45(b) change one~~ | **SEEN** | **DONE 2026-08-17 as K45(b4) â€” 88 poplars stand on 4.30 ha of lakeshore sand that had never been offered a stem, and the placement rule is the SWARD'S.** The dune is a substrate and the heightfield does not carry substrate, so `communityAt` asks `flora.js` which zone a point is in rather than carrying a second copy of the beach. Two findings: the 40.2 ha refused east of the limits is **4.30 ha of plantable lakeshore and 33.6 ha of sand prairie whose own record carries no tree at all**, so most of it was never a woody omission; and **`SPECIES` is keyed by species id, which breaks the first time a species is recorded twice** â€” `populus_deltoides` is a 22â€“30 m gallery emergent AND a 5â€“15 m dune leaner, and the beach was one line from being planted with the wrong one. Read its box before adding a species to a second zone |
| â€” | RENDERING | ~~K45(b3)~~ | **SEEN on `light`** | **DONE 2026-08-17 â€” the control was inert for the wood and was quietly halving the one thing that must not thin.** Measured before the repair: the three levels planted **472 / 470 / 437 trees** â€” one wood planted three times, exactly as K45(b2) predicted â€” while the point-bar willow screen went **258 / 190 / 133 stools**, because the thicket roll is a fixed per-cell chance and a coarser grid visits fewer bar cells. **So the only thing scene detail did was break the screen its own comment says must not be broken.** `keep` is now a fraction on the tree acceptance roll (1 / 0.80 / 0.60, the levels' own triangle ceilings read as a ratio â€” L121) and the thicket roll scales with its cell instead: **`light` 437 â†’ 257 trees and 133 â†’ 182 stools**, scene triangles **416,222 â†’ 370,738**, `full` unchanged to the stem, and the wood reaches N +391.8 m at `light` against `full`'s +397.7. Read its box before quoting a stem count at any level but `full` |
| â€” | RENDERING | ~~K45(b2)~~ | **SEEN** | **DONE 2026-08-16** â€” the planter sweeps the field (reach 27.05 % â†’ 98.37 %), the timber gets the east end Andreas gives it, and `z05`'s own note had Wells Street 440 m from where the committed centreline puts it. Read its box before quoting a reach number or moving a woody east limit |
| â€” | RENDERING | ~~K48~~ | **SEEN** | **DONE 2026-08-16 â€” and it refuted its own premise. 0 sycamores became 2.** Both repairs it named are impossible: rescaling to the bands is an unsolvable system in two of four communities (`wet_woods` floors sum to 100/ha under a stand ceiling of 84), and deriving `perHa` from the mix sum contradicts the same dossier's own canopy sentence. The share is not the defect; the **draw** was. Read its box before proposing a change to any weight, density or band |
| â€” | RENDERING | ~~K49(d)~~ | **SEEN** | **DONE 2026-08-16 â€” the block permutation works and `prairie_west` does not stripe: matrix deviation 368.80 â†’ 282.89, and the 31.47-slot row is now 3.67.** Its finding is not the repair: **the stratum size is a U-curve**, and K49(b) finding 3's rule is only its left half â€” a block also has a CEILING, because exactness over the block is read through a sub-window. Measured at five sizes, and the smallest is 7.4Ã— WORSE than doing nothing. Read its box before setting a stratum size anywhere |
| â€” | RENDERING | ~~R-BUG1~~ | **SEEN** | **DONE 2026-08-16 â€” the owner's flickering river edge was the NEAR PLANE, and 15.6 % of the drawn bank line is now 3.3 %.** A fixed 0.1 m near against a 3,000 m far leaves two surfaces 350 m away needing 10 cm of separation before the depth buffer can order them, and the waterline is co-planar BY DESIGN. The instrument is the finding: **move the camera 2 mm and photograph the same view twice** â€” the control is 0 px, so anything that changes is a tie. **Most of what flickers is not the bank (R-BUG6), and its suspect is UNTESTED because the flag written to test it changes nothing.** Read its box before biasing any surface to settle a tie |
| â€” | RENDERING | ~~K49(e)~~ | UNSEEN | **DONE 2026-08-23 (T-0018) â€” REFUTED, and in the opposite direction.** The filters do not eat the stratification: over 7,844 dealt slots the survivors sit at **0.65** of what a rank-BLIND filter of the same size departs by, and the riverbank row the parcel was left on refuses **0.0 %** of its slots. The instrument was shown red before it was believed â€” a width-selective control on the same vectors reads 3.9â€“5.0. Read its box before blaming a filter for a census row |
| â€” | RENDERING | ~~K49(b)~~ | **SEEN** | **DONE 2026-08-16 â€” all six species are standing, 6 absent â†’ 0 over 6,795 slots.** And the screenshot the parcel asked for vetoed half its own repair: on the dense matrix layers the same construction rows the prairie. Read its box before proposing a low-discrepancy draw anywhere else â€” the answer is layer-dependent, and the census would have merged the striped version |
| â€” | RENDERING | ~~K49(c1)~~ | â€” | **DONE 2026-08-16 â€” the 25 footprints are in, `unconvertible` 25 â†’ 0, and the conversion is measured and NOT shipped.** It moves the shares by up to 3Ã— (June grass 8.1 % â†’ 24.0 %, wood nettle 1.1 % â†’ 6.3 %) and improves both deviations (matrix 219.19 â†’ 197.46, forb 107.18 â†’ 89.11), and it puts *Scirpus atrovirens* at **1.10 slots owed, 0 drawn** â€” K49(f)'s absolute gate. Read its box before dealing a sward slot off any number |
| â€” | RENDERING | ~~K49(c2)~~ | **SEEN** | **DONE 2026-08-16 â€” the conversion is SHIPPED and the tail gate is green on the mirror: matrix deviation 219.19 â†’ 154.19, forb 107.18 â†’ 89.11, worst shortfall 15.21 â†’ 8.50.** Route 1 was built and is **refuted at frame scale** (the sweep alone leaves *S. cyperinus* drawn nowhere at 1.11 owed, because a frame does not hold whole blocks â€” K49(e)'s question); route 3, which K49(c1) said was "not a route to green", **is** what got there. Read its box before proposing a construction to fix a tail |
| â€” | RENDERING | ~~K49(a)~~ | â€” | **DONE 2026-08-16.** The drawn census of the sward, in every community, + the abundance-unit audit. **And the lesson that is not about flora: the gate's own station reports 0 species absent, because it stands in one community of ten.** Read its box before quoting a flora share or a per-frame figure the smoke prints |
| â€” | RENDERING | ~~K49~~ | **SEEN** | **opened 2026-08-16 by K48.** Every other weighted draw in this project is the same shape and none has been asked what its tail does â€” the 63 inferred households, the roof coverings, the massing-variety picker. K48's own finding is that a small weighted sample loses its rare end permanently when the seed is fixed. Pick one, census what it actually draws, and it is visible wherever the answer is a building |
| â€” | RENDERING | ~~K47~~ | â€” | **DONE 2026-08-16 â€” and it inverted: claimed SEEN, delivered UNSEEN.** The sycamore's archetype is built and `drawn_as_another_species` is empty; the tree is **0 of 163 stems**. Read its box before quoting v139 or K45(b1) on what stands by the river |
| â€” | RENDERING | ~~K46~~ | **SEEN** | **DONE 2026-08-16** â€” the written weight plants the stem, and route 3 was refuted by the DATASET: ZONE 6a and 6b are one record, so a zone-keyed density cannot hold the elm at 60 in the thicket and 12 in the pocket. 23 of 26 weights sit inside their own cited band, 3 below, **none above**. Read its box before quoting a mix weight or a species share |

**If you are about to claim an UNSEEN parcel, stop and read the rule.** It needs one of three
written exemptions: an owner-reported bug, the second half of a measure-then-fix split, or a gate
that is blocking a named SEEN parcel. "It would be good to have" is not one of them.

**And if the SEEN rows above are all blocked, that is the finding** â€” say so in the PR and pull a
SEEN parcel up from the sections below rather than defaulting to another gate.

**AND THAT IS WHAT HAPPENED â€” 2026-08-16, R-A1, the first run to take this paragraph rather than
the table.** Every numbered SEEN pick was blocked (K30(c), T-E3, R-W2c, T-V1(b) need a bake; T-V2
and R-W1 were parked on `hold` â€” **both landed 2026-08-16 when the whole `hold` queue was worked
down; see R-M1c for why three of the four holds were one instrument fault**; R-W2b is a 315-record
schema change with no source stating a roof
covering), and the only unblocked NEXT UP row was **K49(e)**, which is UNSEEN â€” and the visible-
progress cap forbade it: v148 is already the one invisible run in the last four, so a second would
have made it two in four. So a SEEN parcel was pulled up from the sections below and shipped. **It
took ~25 minutes of budget to establish that, which is what the box below exists to save** â€” but
the pull-up route is now proven, and `R-A1`'s own section is the model: a parcel deferred for a
reason, whose stated precondition another parcel has since met, is a SEEN pick hiding in the file.
Search for *"deferred"* and *"unblocked"* the way T-E5(a) searched for `not_modelled`.

**THE TABLE ABOVE IS NEARLY OUT OF PICKS THIS RUNNER CAN CLOSE â€” counted 2026-08-16 by K28, and
stated here because the next run will otherwise spend a third of its budget rediscovering it.**
Of the numbered picks left standing, **T-V1(b), K30(c), T-E3 and R-W2c all say NEEDS A BAKE** and
cannot go green on the improve runner; **T-V2 landed 2026-08-16 (its `hold` was withdrawn â€” the
number it was parked on had been fixed by other parcels), and R-W1 is still on `hold` PR #125**;
**R-M1b is blocked on the owner** (R-W4c(b2) closed 2026-08-27 as T-0034, and T-I3(b)
as ticket T-0032 on the owner's delegated pick); and **R-W5a2's own box says to take it
only when the lane has nothing sharper**. That leaves **R-W2b** â€” whose R-W2a finding 2 makes it a
schema change across 315 records with no source yet stating a roof covering, so it is larger than
"unblocked" reads â€” and **T-E5**, whose ground half also needs a bake though its research and
`docs/LIBERTIES.md` half does not. **The lane needs new parcels opened more than it needs the next
one picked**, and the bake-shaped backlog is the reason: four parcels are waiting on a nightly.

**AND THE COUNT IS BETTER THAN IT WAS â€” 2026-08-16, K45(b2).** The box above says the lane needs
new parcels more than it needs the next pick, and this run left **two runner-closable SEEN ones**
where it took one: **K45(b) change one** (the dune community, whose hard question K45(b2) removed
rather than answered) and **K45(b3)** (the detail control, which K45(b2) measured as doing nothing
at all). Both are rows 1a and 1b in the table above. Neither needs a bake.

**T-E5 WAS THE LAST OF THOSE TWO AND IT IS TAKEN â€” 2026-08-16, T-E5(a).** The count above was
right and the paragraph's own advice is now the binding one: **the lane needs new parcels opened
more than it needs the next one picked.** T-E5's bake-free half is spent, its successor T-E5(b)
needs a bake, and every other numbered pick still sits behind a bake, a `hold` PR or the owner. So
the next runner-closable unit here is most likely **a parcel this file does not yet contain**, and
the honest way to find one is the way T-E5(a) found its own: read a deferral, a `not_modelled`
entry or a "deferred to parcel (c)" phrase and ask **what question it was never asked**. That is
where four of the last six findings came from.

**AND IT PAID A THIRD TIME, ONE LINK FURTHER IN â€” 2026-08-16, K36(b).** The successor to the
paragraph below took its own advice literally: K36(a) had gated a transformation and named its
output a fault about NAMES, so K36(b) asked what else that transformation changes. The answer
was the town's draw-call budget, breached at half its scene anchors, on a flag whose
documentation says it does the opposite. **The generalisation: when a tool's own justification
for a step is a number, measure the number in YOUR system.** `--palette` merges materials
inside one file; this renderer batches across files; those are not the same currency and
nothing had ever converted between them. The lane is full of steps justified by a
tool's README â€” `--simplify`, `--compress`, `meshopt`'s bit depths, the AO bake's own nightly
(B-A1 asks exactly this question of it, and is still unclaimed).
**And it opened TWO runner-closable parcels, K37 and R-W6(b)**, which is the count the box
above says the lane needs more than it needs the next pick.
**K37 IS SPENT â€” 2026-08-16 â€” and it opened two more of the same shape.** Its own finding was
that the parcel's question ("are these 90 special?") had the wrong subject: the discriminator was
not the asset's kind but a number nobody had taken, and taking it convicted three assets the
parcel never suspected. The two it leaves open are both *writers of `assets/web/` that nothing
decided*: `generators/inferred_placeholder.py`, which seeds the tree from the master on every
run, and `tools/publish.sh`, which copies a master through on an **mtime** comparison. Three
scripts write that directory and only one of them is the step. **The generalisation, and it is
the K36(a) seam one turn further: when a directory has more than one writer, the gate on its
contents is a gate on the last writer only.**

**AND THAT SENTENCE WAS WORTH A PARCEL ON ITS OWN â€” 2026-08-16, K38.** It took K37's
declined paragraph verbatim and the answer was worse than the paragraph guessed: the count
is not three writers but **four passthrough branches across three scripts**, three of them
silent, and the fault is reachable in one command. Two masters `touch`ed and
`tools/publish.sh` run put **1,212,760 uncompressed bytes into the payload** and drew
**CHECK PASS** from the entire dev gate â€” because a master copied over its own derivative
satisfies assertions 1 through 7 *by construction*. **The generalisation one turn further:
a gate written against a transformation is not a gate on its output directory**, and the
difference is invisible for as long as only the transformation writes there. Two of this
project's directories now have more writers than gates, and `assets/gltf/` â€” written by
`generators/build.py`, by the nightly, and by whatever a parcel does with `--only` â€” has
never been asked the question at all. K38's own successor K39 is the narrower half: the
step knows which master it compressed and writes it down nowhere, so staleness is still a
timestamp.

**AND THE NARROW HALF WAS THE ONE THAT PAID â€” 2026-08-16, K39.** The record itself is
exactly what K38 predicted and took an afternoon. The finding came from trying to VERIFY
it: a seeded hash wants a reproduction control, this repository claims one in as many
words (*"it reproduces 331 of 334"*), and **the claim is false** â€” 6 of 20, with the other
14 reproducing byte-for-byte under a flag K36(b) turned off two parcels ago. **The
generalisation, and it is the K36(b) seam turned on ourselves: when a repair regenerates
SOME of a set, the remainder becomes the output of a step that no longer exists.** K36(b)
regenerated 38 of 241 and said so honestly; nothing asked what the other 203 were. This
project has done partial regenerations at least three times â€” K36(b)'s 38, K37's 3, and
R-W6's terrain that never reached the file at all â€” and each one left a cohort behind.
K40 is this instance. The question is worth asking of `assets/gltf/` too, where the
nightly, a `--only` run and `generators/build.py` all write.

**THE SEAM IS STILL OPEN, AND IT PAID AGAIN â€” 2026-08-16, K36(a).** Same move as K34, one link
further out: instead of a rule about a record, take a rule about a FILE â€” *"a stale committed GLB
is a check failure, not a warning"*, *"the bytes a visitor downloads have to be the bytes
something tested"* â€” and ask which of the steps between the data and the browser anything
actually measures. Two of three, it turned out, and the ungated one had been shipping 75
textures out of a repository that contains none. **The generalisation worth carrying forward:
this project gates its ARTEFACTS at their ends and not at their transformations**, and every
transformation here is a script with a flag in it. `publish.sh`, `compile_scene.py` and the dev
preview assembler are the same shape of thing; two of them now have a gate and the question is
worth asking of anything that rewrites a file on its way out.

**THE ADVICE WORKS, AND THE RICHEST SEAM IS NOT THE DEFERRALS â€” 2026-08-16, K34.** It took the
paragraph above and widened it one step: instead of a deferral, read a **rule this project states
about itself** and ask what enforces it. AGENTS.md's standing constraint on the removal is the
most important sentence in this repository and nothing had ever measured what it covers; the
answer was "the buildings, and not the people", plus one record that claimed the flag in prose
and never carried it. **`docs/` and `AGENTS.md` are full of sentences of that shape** â€” a rule
stated, a mechanism named, and nothing that runs. K35 is the successor this one opened, and the
seam is not exhausted.

**R-W5a is DONE (2026-08-15) â€” the town was paying one draw call per COLOUR OF PAINT, and the
growth term is now zero.** All 47 building batches were the same `MeshStandardMaterial` in every
respect a renderer distinguishes â€” metalness 0, no map of any kind, `DoubleSide`, opaque, no alpha
test, smooth-shaded. The only fields that differed were `color` (39 distinct values) and
`roughness` (16). Base colour moved to a per-vertex attribute and left the key, so **47 batches
became 16** and **11 of 22 station-viewports over the â‰¤ 80 budget became 0**. Full table and the
identity proof under R-W5a below. Three things came out of it that are not the number:

- **R-G1's "+11 draw calls per 19 roofs" was 11 new MATERIAL GROUPS, not 11 objects** â€” which is
  why it was uniform at bearings 150Â° apart: it counts paints in frame, not buildings. That term
  is now **zero by construction**: a new roof of any colour joins an existing batch. T-A8 and the
  399 roofs behind it are unblocked, and no future block parcel needs to think about this.
- **Triangles are identical to the triangle at all 22 station-viewports**, which is the proof that
  nothing was dropped to buy the calls.
- **The frame is not byte-identical and the difference is quantified rather than waved at**:
  2 of 22 shots hash the same, the rest differ on ~0.013 % of pixels in scattered 7â€“56 px specks
  at building silhouettes â€” depth ties resolving the other way under a changed draw order â€” for a
  whole-frame mean |Î”| of **0.003â€“0.005 of one 8-bit count**. No surface is repainted; the albedo
  arithmetic is the same product in a different order.

**R-BUG3 is REOPENED (2026-08-15) â€” the owner reproduced it WITH the fix in.** What it fixed is
real and stays; what it claimed is not. See **R-BUG3c** and **R-BUG4** below, and read them before
quoting any road number. The original write-up follows, corrected:

**R-BUG3's near-field contrast half is done (2026-08-15)** â€” the owner-reported invisible-at-your-feet road was **the alpha,
and NOT the grass**: the near band scored **1.5 L\* / 30 %** and now scores **3.1 of a measured
ceiling of 3.4 with 80 % perceptible on mobile, 3.2 of 4.3 with 60 % on desktop**, and the alpha
half of the fix fades to nothing by 40 m, so every band past it is unchanged to the decimal. (Those
figures are re-measured on the merge of 2026-08-15; an earlier draft of this line quoted *2.8 of
3.7 / 60 %*, which was one iteration stale and matched neither viewport. The gate prints the bands
â€” quote it, do not paraphrase it.) Two things were found
that are not the fix and matter more. **The near band was empty at both gated stations, because
neither one stands on a road** â€” `south_water` is 101 m from its own centreline (T-V2) and
`from_above` is in the air â€” so the parcel's own first move, adding `[2, 40]`, measured nothing
until a station stood on the roadway. And **a band gated on probes SEEN gates itself out exactly
when the road goes invisible**; the bands are now gated on probes PROJECTED, so that failure is
loud. Full findings under R-BUG3 below â€” read them before pointing any gate at anything.

**R-BUG2 is DONE (2026-08-14)** â€” the owner-reported vanishing roads were **two** faults, not one,
and the parcel's prime suspect was **refuted by measurement**. The gate could not see any of it and
now can: `roadContrast()` scores the fault at **0.3 L\* / 14 %** on foot at range and **1.1 L\* /
0 %** from the air, against **4.0 / 92 %** and **2.9 / 91 %** with the fix. Full findings under
R-BUG2 below â€” read the refutation before reaching for a mip-filter fix anywhere else.

**K21 is DONE (2026-08-15)** â€” the four trades whose adoption test was silent are silent no longer:
every roof this layer raises now carries the family band its own prose has always named, **29 of 29
census trades resolve across 44 trade-family pairs**, and a gate fails if a household is ever housed
on a roof that names no family. No liberty was owed â€” the value was already committed twice over â€”
and rule 6 gains no clause. The parcel's own Watch note was **refuted**: the two sawyer roofs differ
because they were dealt different families. The real archetype split, and the finding underneath it
â€” **54 of 193 roofs sit outside the band their note cites** â€” are **K25**. Full findings under K21
below; read the refutation before massing anything off an archetype.

**T-A7 is DONE (2026-08-15)** â€” a lot was known to be free by the *absence of a centroid*, and a
building standing proud of its own frontage has its centroid in the road, so four documented
buildings â€” the Temple Building, Harmon & Loomis's store, the Chicago Democrat's office and the
Cook County courthouse â€” stood on lots the schedule was offering to anonymous roofs. Occupancy is
now measured by area, in ONE module both halves import. **266 stand and 399 remain, 61 of them on
covered ground** (was 66). Full findings under T-A7 below; read them before claiming a block.

**T-A6 is DONE (2026-08-15)** â€” the schedule was dealing five of the ten open blocks roofs their
own lots could not hold, and the deal now derives lot occupancy the same way the block generator
does. **266 stand and 399 remain, 66 of them on covered ground** (was 71 â€” five roofs never had
anywhere to stand; **re-derived to 61 by T-A7**). Full findings under T-A6 below.

**T-A5 is DONE (2026-08-14)** â€” `blk_randolph_market` carries eight roofs, so **266 stand and 399
remain**, 71 of them on covered ground (**re-derived to 66 by T-A6**). It is the first block whose standing roofs this project's
*own inferred-residents layer* had put there, and it **settles the division question T-A4 left
open**: rule 6 takes three tests, the third being the roof's division, and the written test recovers
all four adoption decisions made before it. It also found what the tests cannot answer â€” four trades
are housed only in family-less bespoke records, so test 2 is silent rather than negative for them
(**K21**). Full findings under T-A5 below.

**T-A4 is DONE (2026-08-14)** â€” `blk_randolph_clinton`, the first West Division block, carries
seven roofs and one adopted household, so **258 stand and 407 remain**, 79 of them on covered
ground. It is the first block parcel to arrive at ground that was already partly built, and the
gates that assumed an empty block are what it fixed. Full findings under T-A4 below.

**T-E1 is DONE (2026-08-14)** â€” the 1830 sheet is registered and read, and it is a **land-title
map, not a settlement map**: a name on a tract is who took title between 1828 and **1836**, not
who lived there and not that anything was built. A named tract may never license an anonymous
roof. Full findings under T-E1 below; read them before T-E2 or T-E4.

**T-A2h is DONE (2026-08-14)** â€” two of `blk_randolph_wells`'s ten roofs carry an argued
household and eight stay anonymous, under a **two-test rule now written into the household
programme's own `method` list**: a block roof may be adopted only where the trade's committed
argument calls its count a floor rather than a bound, AND the roof's family is one this layer
already houses that trade in. **The adoption is no longer a parcel of its own.** The generator
carries the gate in both directions, so T-A4 onward applies the rule in the same run as the
block â€” `T-A3h` was the one outstanding backfill because its block landed first, and it is **DONE (2026-08-15)**: every block this lane has placed has now been asked the question, and what the backfill found about the tests themselves is in its box and in K28.

**LANE 3 (ground) is a THIRD lane, opened 2026-08-14** â€” it touches terrain, sources and the
infill generator's eligibility rule. It is **disjoint from lane 1** (renderer) but **overlaps
lane 2** at `tools/generate_block_infill.py` and the inventory, so **a lane-2 block parcel and
a lane-3 parcel may not run at the same time.** Lane 1 may always run alongside either.

**Why it matters now:** only 86 of the 414 remaining roofs sit on covered ground. Lane 2
exhausts them in roughly a day and a half and then has nowhere to build. Lane 3 is what keeps
the town growing after that â€” and the owner's condition on opening it is that the geography be
real, not convenient.

**R-G0 is DONE (2026-08-14)** â€” the harness and the baseline are in, so every parcel below
opens with `node tools/critic_shots.mjs --metrics` and closes with the same command, and
quotes the two tables rather than an adjective.

**R-G1 is DONE (2026-08-14) â€” the baseline scores 4.18 of 10, every axis below 7.** Texture
**1.4** is the floor, historical accuracy **6.8** the ceiling, and the five-point gap between
them is the shape of this project. Full tables and per-axis justification in `docs/STATUS.md`
Â§ "The baseline scored". **Three findings came out of it that are not scores**, and each is
written into the parcel that owns it below:

- **Â§1 item 7's mechanism does not survive.** 94â€“100 % of the literal-black pixels lie in
  components entirely above the land/sky row â€” they are the shaded near canopy, not a shadow â€”
  and the darkest-decile figure reaches the same surface a second way, because the metric's
  per-column "ground" starts at the top of a crown. **R-W1** owns it; raising a shadow floor
  will not move either number.
- **The horizon-timber metric counts a gable as a tree.** `prairie_south` gained 20 % on that
  metric between two runs with no renderer change, from 19 new roofs. **R-W4** owns the target
  and needs a discriminator before its â‰¥ 90 % acceptance number means anything.
- **19 roofs cost +11 draw calls at seven of eleven stations**, taking the over-budget count
  from 4 to 6 desktop. Extrapolated over the 414 remaining roofs that is about +240 against a
  budget of 80. **R-W5** owns it and should treat batching as its first question.

**T-A3 is DONE (2026-08-14)** â€” `blk_randolph_dearborn` carries **nine of the ten roofs the
schedule dealt it**, so **251 stand and 414 remain**, 86 of them on covered ground. The tenth was
a civic roof and is deferred with its reasoning: the parcel shape repeated exactly as T-A2
predicted, and what it found was that one family cannot be massed at all. See T-I3.

**T-A2 is DONE (2026-08-14)** â€” `blk_randolph_wells` carries ten roofs, so **242 stand and 423
remain**, 95 of them on covered ground. The parcel authors no coordinates: block parcels are now
a recipe entry read against the committed lot polygons, which is what makes T-A3 onward cheap.

**T-A1 is DONE (2026-08-14)** â€” 232 roofs stood, 433 remained, and
`data/reconstruction/1835_665_roof_programme.json` schedules them per block. Only **105 of
the 433** have modelled ground to stand on, so lane 2 has about ten block parcels of work in
it and then it is blocked on S9 street control and the terrain extensions, not on recipes.

---

## LANE 1 â€” RENDERING Â· phases from `docs/RENDERING.md`

Acceptance numbers are copied from RENDERING Â§5 so a builder does not have to hold two
documents open. Where a phase has a bake-dependent half, it is marked â€” ship the half you
can and say so.

### T-0179 â€” three families offer a shed their ridge band cannot carry Â· **DONE 2026-08-27 â€” two held, one refuted, and a fourth nobody had measured**

**The reasoning archive for L182 and the STATUS box of the same date.** T-0148's sweep printed C1,
F1 and F4 as NOTE lines: families whose crosswalk roof line offers a SHED their own `ridge_ft` band
cannot carry, latent because no generator dealt them one. Asked of what the archetypes actually
build:

| family | ticket | measured | the reason |
|---|---|---|---|
| C1 | 231 of 441 | **231 of 441** | `frame_storefront._shed_roof` always falls back-to-front; the run is the 20-30 ft depth |
| F1 | 399 of 441 | **399 of 441** | `outbuilding` with no open side, so the fall is down 32-50 ft |
| F4 | 441 of 441 | **0 of 441** | F4's own entry is `1/open`, "open posts", "part-open sides" â€” the fall goes across the 24-36 ft width (L73) |
| W5 | â€” | **84 of 441** | never swept: the sweep reports a family with no pitch band before testing any FORM |

**Three findings worth keeping.** (1) The sweep constrained a claim it did not know it was
constraining â€” the AXIS a shed falls down â€” exactly as T-0145 had constrained the eave; the shape of
that error is now twice-observed and worth watching for a third time. (2) `ridge_model` turned the
shed's span with `gable_front`; all three archetypes that build a shed ignore the orientation
entirely, and no committed GLB is a shed on those archetypes, so the gate that exists to keep the
model honest had nothing to compare against. **A model checked only against what has been built is
unchecked wherever the build has not gone.** (3) The shed set was written five times and had drifted
over A5 â€” one roof stands on the difference â€” which is the same one-rule-two-files fault
`family_bands.py` was created to end, three files later.

**Owner question, unresolved and not blocking:** the `ridge_ft` column is authored for a gable's
half-span. Retiring the shed reading for C1, F1 and W5 in the crosswalk would be cleaner than
recording a refusal on every one of their records; recording it is what an agent may do, editing the
specification is not. See L182 "How to resolve".

**Still owed:** T-0212, the one A5 roof held on a gable pending a bake.

### R-BUG5b â€” the trees are still in the river Â· **DONE 2026-08-16 Â· the whole wood was drawn mirrored**

**THE WOOD WAS TESTED IN ENU AND DRAWN IN WORLD SPACE, AND THE TWO POINT OPPOSITE WAYS.** The
near-field planter in `renderers/web/js/trees.js` walks a 4 m grid and asks every question in local
ENU metres â€” `terrain.isWater(e, n)`, `communityAt(e, n)`, `terrain.surfaceHeight(e, n)`,
`cellAt(e, n)`, `blocked(e, n)`, `noteStation(e, n, y)`. Then it called
`addTree(buf, spec, px, gy, pz, rnd)`, and `addTree`'s fifth argument is a **three world z**.
`terrain.js`'s own `enuToWorld` is `(e, y, -n)`. The sign was never taken. **Every tree in the wood
was tested at `(px, pz)` and drawn at `(px, -pz)` â€” the entire near-field woodland mirrored across
the datum's eastâ€“west line through the forks.**

**The numbers, measured on `dev` as it stood (the build in the owner's screenshot):**

| | |
|---|---|
| stations recorded | **391** |
| stations wet at the point that was TESTED | **0** â€” which is why every gate was green |
| stations wet at the point that was DRAWN | **64** (16.4 %) |
| drawn vertices over the water mask | **12,285 of 77,688** (15.8 %) |
| â€¦more than 4 m from the nearest dry ground | **10,734** |
| worst distance from dry ground | **48 m** â€” at E 160.1, N 47.8, 0.61 m above the water |
| nearest station to a vertex, read as ENU `n = -z` | **âˆž** (no station anywhere near the geometry) |
| nearest station to a vertex, read as ENU `n = +z` | **13.1 m** â€” one crown radius. That is the proof |

**THE FINDING IS NOT THE SIGN. It is that three gates agreed with each other and all three were
measuring the same wrong thing.** `wetTreeStations`, `drownedTreeStations` and
`tools/measure_far_timber.py` all walk `stations` â€” the list the planter writes at the moment it
DECIDES to plant. That list is correct and always was; not one entry of it is in the water. **No
check anywhere read the merged geometry back and asked where a tree was DRAWN**, so a fault that
separates the decision from the drawing was invisible to all of them simultaneously. This is the
generalisation, and it is the sixth green-gate-versus-window disagreement on this project: **a gate
on a placement is not a gate on a picture. If a layer decides in one coordinate system and draws in
another, only a gate that reads the drawn buffers back can see the step between them.**
`renderers/web/js/flora.js` had it right the whole time â€” `_m.setPosition(e, y, -n2)` â€” which is
exactly why the sward has never been in the channel and the wood always was.

**R-BUG5 (#196) IS NOT RETRACTED, AND SAYING SO PRECISELY MATTERS.** `main_stem_belt_east` really
is authored between the two banks, really is 39 of 39 samples over water, and really should not be
drawn; that clip stands and its gate stands. What #196 got wrong is the ATTRIBUTION: it explained
the owner's photograph with the horizon band, shipped, and told the owner it was fixed. The band
was a second, genuine fault that happens to sit in the same direction from the same viewpoint. The
lesson it paid for is the one its own box asked for and did not get â€” **reproduce the frame before
choosing a cause.** This parcel's first commit was a screenshot, not a diagnosis.

**How the frame was reproduced, so the next person does not have to find it again.** The owner's
pose is `local_e -100, local_n -40, yaw_deg 76, altitude_m 1.22` â€” the south bank west of the
forks, 4 ft up, ENE 076Â°, which is what the HUD reads in his screenshot. The line of crowns is
at 130â€“190 m, over the main stem. `tools/shoot.mjs` puts the camera there in one command.

**The repair** is one named function, `worldZ(n) => -n`, applied at the two `addTree` call sites,
plus the comment block that says why it is named rather than inlined. Nothing about which trees
grow where, how many stand, or the evidence behind any of it moved: `perHa`, `edgeFade`,
`clearedFactor`, the waterline gate, the species draw and the seed are all untouched. **Every tree
simply moved to the side of the river it was already recorded as standing on** â€” so the North
Division's body of timber is now on the North Side, and the south bank of the main stem opens out,
which is what the sources describe and what the town's own `blocked()` footprints were being tested
against all along.

**The two new gates, in `tools/smoke_renderer.mjs`, and both were demonstrated RED on the unfixed
published mirror before the fix went in:**

- *every tree drawn stands at its own station* â€” every vertex of the merged timber within 24 m of
  some entry in `stations`. **This is the one that could never have passed through the bug**: under
  the mirror the nearest station is twice the vertex's own northing away. Structural, not a
  threshold.
- *no timber is drawn out in the channel* â€” no vertex over the water mask further than 12 m from
  dry ground, which is a bank willow's lean (see `TREE_DRY_MARGIN_M`'s box and `lean` in `SPECIES`)
  and no more. This is the owner's report in the owner's terms.

**Neither may ever be relaxed into a test of the placement. That is the test that was already
green.**

**LANDED WITH ONE GATE KNOWINGLY RED, AND THE `hold` IT WAS FIRST PARKED UNDER WAS WITHDRAWN ON
MEASUREMENT.** With the wood repaired, `the roads reach the screen from the air, at the aerial
anchor` fails â€” the FLYING station; **both on-foot road stations are green**, so nothing a walker
sees regressed. It is not a regression in the streets either: not one street vertex moved, and every
street gate â€” drape, wet vertices, the R-BUG4 panel invariant â€” is still green.

This parcel was first parked on `hold` asking the owner to accept that red. **The premise of the
question was measurable, and measuring it reversed the answer.** Both columns below were taken the
same evening on the same runner, mobile 390Ã—780, published mirror, with nothing but `trees.js`
between them â€” `dev` at 3ea4e00 and this branch rebased onto it. The earlier figures in this box
were taken against the pre-R-BUG1 base and are superseded by these:

| aerial anchor, gated bands | `dev` (wood mirrored) | wood repaired |
|---|---|---|
| 100â€“250 m â€” seen of 63 projected | 46 | **60** |
| 100â€“250 m â€” perceptible | 80 % â†’ **37 probes** | 85 % â†’ **51 probes** |
| 250â€“600 m â€” seen of 186 projected | 157 | **177** |
| 250â€“600 m â€” median Î”L\* | 2.7 of 6.1 opaque | 2.3 of 4.8 opaque |
| 250â€“600 m â€” perceptible | 62 % â†’ **~97 probes** | 54 % â†’ **~96 probes** |
| 250â€“600 m â€” weber / ground L\* | 0.1104 / 53.9 | 0.0951 / 52.8 |
| **gated probes a visitor can SEE** | **203** | **237** |
| **gated probes that are PERCEPTIBLE** | **~134** | **~147** |

**The repaired build shows about thirteen MORE perceptible stretches of road and scores lower.**
That is the metric, not the town: `perceptible` is a ratio over probes **seen**, and `seen` is
exactly the quantity an occluder shrinks. **A gate whose score improves when something hides the
thing it measures is dividing by the wrong number.**

**This is R-BUG3's own lesson surviving one level below where R-BUG3 fixed it.** `roadContrast()`
already moved the decision of WHETHER to gate a band from "enough probes were seen" to "enough were
PROJECTED", and the comment beside it says exactly why: *"a band nobody can see reports n=0 and
gates itself out, which is indistinguishable from a band with no road in it."* The band's SCORE
still divides by `seen`. Score the same band on `nProjected` â€” fixed at 186 whatever stands in the
way â€” and **`dev` reads 52 % and this branch reads 52 %.** `dev` is under the 0.55 bar too, and has
been; it reports 62 % only because twenty-nine of its probes stand behind trees that were never
supposed to be there. **The band did not regress today. It stopped being flattered.**

**`ROAD_MIN_PERCEPTIBLE` is NOT lowered** â€” AGENTS.md Â§ "never weaken an assertion to pass", and
cutting a bar to admit the probes an occluder was hiding is the exact shape of that mistake. Note
too that the honest denominator would not have let this branch through either, which is what makes
it a finding rather than a route: it fails both builds. The band's real fix is **R-W2**'s textured
coverage â€” its ceiling is 4.8 L\* opaque, so the contrast is there to be spent â€” and the denominator
is **R-M1c**, opened below by this parcel. **R-W1** (`hold` PR #125) and **R-M1b** (no threshold
source) remain the owner's.

**Why it merged rather than waiting.** Holding a correct, visible, owner-reported fix behind a gate
that was passing on an artefact of the very bug being fixed inverts what the gate is for. Merging to
dev is stage, not ship: it publishes the `/dev/` preview only, and production moves solely on owner
dispatch. Recorded here so no later run reads the red as fresh breakage â€” it is red on merit, red on
`dev` as much as here, and it belongs to R-W2 and R-M1c.

**What this leaves open, and it is a real question rather than a courtesy.** Every other layer that
decides in ENU and draws in world space should be asked the same question by the same method â€”
reading its buffers back rather than its intentions. `flora.js` is measured and clean.
`streets.js`, `buildings.js` and `ground.js` have not been asked, and the ROADMAP entry for it is
**K50** below.

<details>
<summary>The parcel as it was written when it was claimed (2026-08-16)</summary>

**The owner reshot the river at 3:14 PM CT, standing 4 ft up on the south bank looking ENE 076Â°, on
the build whose What's-New panel says â€” in the same screenshot â€” "The trees standing in the river
are gone Â· Fixed Â· Aug 16, 2026, 1:31 PM CT". A straight line of crowns still runs across the
channel, with scattered ones beside it. The two sights #196 said were "one thing seen twice" are
both still there.**

**#196 is not to be trusted as a starting point, and this is the point of the parcel.** It shipped
`trees.js` (+74), `tools/measure_far_timber.py` (+484), a committed baseline and a new smoke
assertion â€” and the thing a visitor sees did not change. **Three instruments agreed with each other
and disagreed with the window.** That is now the FIFTH time on this project that a green gate and
the owner's screen have disagreed, after R-BUG2, R-BUG3, R-BUG3c and R-BUG4.

**The first job is NOT the trees. It is to reproduce the owner's frame and see them in it.** Until a
harness stands at that pose and photographs the trees over the water, nothing measured about timber
means anything, and any further fix is aimed at a target nobody has sighted.

**Do this in order and do not skip to the third:**

1. **Stand where the owner stood** â€” south bank of the main stem, 4 ft eye height, bearing 076Â°.
   Screenshot it. **If the trees are not in your frame, your pose is wrong, not his screenshot.**
2. **Make the gate FAIL on the current build.** #196's assertion passes today with the defect on
   screen, so it is measuring something else â€” find out what, and say so, before changing it. A
   check that passed through this bug is evidence about the check.
3. **Only then** work out why the crowns are over water, and fix it.

**One reading of #196 worth testing first, because it is cheap.** #196 changed `trees.js` and the
tools â€” **it changed no data.** Its own account says the South Water timber belt is *written*
between the two banks, every point over the channel, the worst 3.33 m under the surface. If the
committed line still runs across the river and the fix only taught the renderer to cull crowns over
water, then the cull is either not reaching this band, not reaching this viewpoint, or being applied
in a space where the water test does not answer â€” the ENU-vs-world swap and the single `y = 0`
water quad are both still live candidates from R-BUG5. **Fixing the record so the belt runs beside
the street it is named after may be the honest repair, not culling the symptom.**

**Acceptance, and it is stricter than #196's because #196 met its own and shipped a defect:**
a screenshot from the owner's pose with no crown over water, posted in the PR **beside the "before"
from the same pose**; the gate demonstrated FAILING on `dev` as it stands today and passing after;
and the What's-New entry does not say "fixed" unless that pair of screenshots is in the PR.

</details>

### K51 â€” the fauna layer reaches a visitor Â· **DONE 2026-08-17 â€” 139 animal records were read by nothing, and the gate that was supposed to notice had been told to expect it**

**Read this box before quoting any layer-read number taken before today.** The census line printed
by `tools/measure_layer_reads.py --gate` ended in the words *"which no renderer opens"* until this
parcel, and by then that clause was a claim rather than a measurement: it was true when K42 wrote
it and the gate had no way to keep it true. It is gone, and the line now separates a figure that
moves a vertex from one a visitor reads on a card, because rolling the two together is how a layer
with no geometry starts sounding drawn.

**What shipped.** The Evidence panel's *What was living here* section: ten habitats in the
manifest's own order, and inside each one every species researched into it â€” **139 records**, each
with its July status, its presence mode, its abundance, what it would be doing, what it would look
like, its voice, the sign it leaves, and the sources behind the three graded claims. The citations
are the joined records `citations.js` renders everywhere else, not bare ids.

**Numbers, measured rather than promised.** Fauna figures reaching a visitor: **0 of 30 â†’ 30 of
30**. Whole-dataset: **58 of 100 figures reached nothing â†’ 28**, and `data/fauna`'s share of that
is **30 â†’ 0**. Habitats on the card **10 of 10**, species **139 of 139**, citations rendered **54**,
zero page errors at 390Ã—780.

**FINDING 1 â€” the gate did exactly what it was built for, and that is the part worth carrying.**
K42 wrote assertion 3a to fail *the moment* a layer with no declared reads gains a reader â€”
*"because the whole of this layer's unread bank rests on nobody opening it"* â€” and it fired on the
first commit that opened the directory. Thirty figures had to be classified in the same commit
instead of riding on a sentence that had quietly expired. **A gate written against an absence has
to name the event that ends the absence**, or the absence becomes permanent by default.

**FINDING 2 â€” two of that gate's own controls were written against the repository's state, and
both went silent when the state moved.** Its self-test asserted `not layer_is_opened(src, "fauna")`
and constructed its 3a case by setting `opened["fauna"] = True`. Opening the layer turned the first
into a second copy of the measurement and the second into a case that could not be built at all â€”
it printed **SILENT** rather than failing, which is the quieter of the two ways a control dies.
Both are synthetic now: a scanner that cannot say *no* about a directory nothing names is broken
whatever this repository happens to contain today. **This is the sixth time on this project that a
green reading came from an instrument pointed at nothing**, and the first where the instrument was
a self-test rather than a flag.

**FINDING 3 â€” `docs/LIBERTIES.md` L2 has said "ambient wildlife is rendered sparsely" since
2026-08-09, and nothing was rendered at all.** Not sparsely: none. The entry's own revision of
2026-08-11 added a paragraph of measured detail about a dataset no renderer had opened, which is
how a liberty about the scene becomes a liberty about a file. L2 now states what the renderer does
â€” nothing is drawn, heard or traced â€” and keeps the decision as the standing intent for whenever
animals *are* drawn.

**What it does NOT do.** No animal is in the 3-D scene, no animal geometry is proposed, and the
standing constraint on depicting people is untouched. Every one of the thirty read declarations is
`shown` and none is `mesh`, deliberately: a state that said otherwise would be the read map making
a claim about the town. K42's route 1 â€” *"leave it and say so"*, which needs `data/scenes/1835.json`
and L2 to stop implying a reader â€” is **half discharged**: L2 is corrected here, and the `layers`
list is now honest for a different reason, because the layer does reach the browser.

**Files:** `renderers/web/js/fauna.js` (new) Â· `renderers/web/index.html` Â·
`renderers/web/js/main.js` Â· `renderers/web/css/walk.css` Â· `tools/publish.sh` Â·
`tools/check_published.mjs` (the copy rule) Â· `tools/compile_scene.py` (the citation join only) Â·
`tools/measure_layer_reads.py` + `tools/layer_reads_baseline.json` Â· `tools/smoke_renderer.mjs` Â·
`docs/LIBERTIES.md` L2.

**Not claimed:** the desktop half of the smoke â€” ~13 min against this runner's 10-minute
per-command ceiling; see the run-budget box at the top of this file. The section was photographed
at 1280Ã—800 by hand and reads correctly there.

**What it opens.** K42's third route, *give it a reader in the scene*, is untouched and is a much
larger parcel behind a bake. The narrower successor is **K52**: the same question asked of
`data/residents/` â€” that layer IS published and IS read by the building card, and nothing has ever
censused which of its figures reach a visitor. The read map covers flora and fauna and the two
generators declare their own `CONSUMED`; the population layer is declared by nothing, which is the
state `data/fauna` was in this morning.

### K52 â€” nobody has censused what the residents' figures reach Â· **DONE 2026-08-17 â€” the layer with a reader was hiding seventeen households, and the reader is why nobody looked**

**The census answer, and it is worse than the fauna one it was written to be safer than.**
`data/residents/` had exactly one reader: `tools/compile_scene.py`'s `compile_residents()`
attaches a household to a building's sidecar and `popup.js` names it on the building card.
That join reaches a building through `lives_at` or `works_at` â€” so **a household whose
residence AND workplace are both unattested at the scene date attaches to nothing and
appeared on no card anywhere in this project.**

| | households | person entries |
|---|---|---|
| in `data/residents/` | 173 | 209 |
| reachable through a building card | 156 | 189 |
| **reachable nowhere, before today** | **17** | **20** |

**One of the seventeen is the Mark Beaubien household** â€” the man who built the Sauganash,
whose house held the incorporation election of 10 August 1833, and whose own record calls
itself *"the most famous household in the town and one of the thinnest records in this
parcel."* He is unreachable for exactly the reason his record is interesting: he had left
the Sauganash by 1834 and the Exchange by August 1834, so where he slept on 1 July 1835 is
not in the record, `lives_at` is `null`, and the join drops him. **The layer was dropping
records for being poorly evidenced, which is the opposite of what the confidence model is
for.**

**Finding 2 â€” a reader is not a read map, and this one carried a third of each record it
did reach.** `compile_residents()` copies id, name, division, the relation, its note, and a
person's name, relationship, grade and occupation *word*. Everything else stopped at the
repository: `arrival`, `origin`, `reason_for_coming`, `party_size_on_arrival`,
`present_on_scene_date`, `touches_removal`, a person's `sex`, `age_on_scene_date`,
`birth_year`, `name_basis` and their own `sources`, the occupation's grade and reasoning,
and the ten `researched_not_resident` findings whose own manifest doc calls them *"as
load-bearing as the households"*. **This is what K52's box predicted in as many words** â€” *"a
layer with one reader is exactly where an unread figure hides, because 'the browser has it'
reads as 'somebody looks at it'."* It was right, and the hiding place was bigger than the
fauna layer's, which at least had the decency to have no reader at all.

**Finding 3 â€” K42's assertion 3a did NOT fire here, and that is a hole rather than a pass.**
`tools/measure_layer_reads.py` scans `flora` and `fauna` and nothing else, so giving
`residents` a reader tripped no gate. The fauna parcel was caught by its own instrument; this
one was caught by reading the join. **Extending the census tool to `data/residents/` is not
done and is opened as K52(b)** â€” the tool is built around flora/fauna figure kinds and the
extension is its own parcel, not a line in this one.

**What shipped.** `renderers/web/js/residents.js`, the Evidence panel's people section: the
manifest in one fetch, all 173 households listed with their division, their people and their
grade tallies, the 17 marked on their own rows in the conjectural colour, and each household's
full record fetched the first time its row is opened. Every graded claim shows its value, its
confidence swatch, its reasoning and its joined citations; the ten researched non-residents
are published with theirs. **Nothing is drawn** â€” L1 and the standing constraint on depicting
people are untouched, and nothing in `docs/LIBERTIES.md` needed a line because nothing was
invented: this parcel published records that already existed.

**Files:** `renderers/web/js/residents.js` (new) Â· `renderers/web/index.html` Â·
`renderers/web/js/main.js` Â· `renderers/web/css/walk.css` Â·
`tools/compile_scene.py` (`compile_residents_sources`, the citation join, 11 sources) Â·
`tools/smoke_renderer.mjs` (ten assertions) Â· `data/sidecars/1835/residents_sources.json`.

**Not verified here:** the desktop half of the smoke does not fit the runner's ten-minute
per-command ceiling (Â§ THE RUN BUDGET). The mobile half ran on the published mirror: **263
passed, 2 failed**, and both failures are the road-contrast bands `dev` already carries red â€”
see `docs/STATUS.md` Â§ *Landed with two bands red*. This parcel changes no 3-D rendering.

### K52(b) â€” extend the read census to `data/residents/` Â· **DONE 2026-08-28 (T-0021) â€” the census found 113 person rows reading `[object Object]`, which is what a figure looks like when it is shipped, fetched, rendered and still not read**

`tools/measure_layer_reads.py` covered `flora` and `fauna` **by name** â€” its kinds, its
baseline and its self-test's negative control all written around those two â€” so `residents`
gaining a reader on 2026-08-17 fired nothing. The layer list is one table now (`LAYER_KINDS`),
read by the record walk, the citation census and assertion 3a alike, and the self-test carries
a new control for the shape of the hole itself: **every layer with a read map is a layer this
file walks.** A blind gate and a wrong gate are the same outcome from a visitor's side.

**69 residents figures classified: 64 `shown`, 0 `mesh`, 5 unread.** None is `mesh` and none
ever will be â€” L1 stands, v1 draws no human figures, so no figure of a person moves a vertex.

**AND THE CENSUS FOUND WHAT A CENSUS IS FOR.** Three of a person's figures â€”
`age_on_scene_date`, `birth_year` and `name_basis` â€” are graded claim blocks
(`{value, confidence, note, sources}`) and `personHtml` was handing all three **whole** to a
text renderer. **113 of the 209 person rows read "How this person is named â€” [object Object]"**
and nine said it twice more for the age and the birth year. Every assertion in the stage-9
suite passed throughout, because a card that renders the wrong string still renders a string;
what was lost is the pool an invented name was drawn from, on the 113 people whose names this
project invented. They go through `claimRow` now, with the swatch, the reasoning and the
citations every other graded claim on the card gets, and three smoke checks hold it â€” each one
verified to FAIL against the old render path before it was kept.

**Two smaller holes, wired in the same commit.** `counts.by_grade` reached nothing behind the
sentence *"every one of them graded"*, which is true and tells a reader nothing; the note now
gives the tally (76 attested, 20 inferred, 113 reconstructed). And `vocabulary.sexes` was the
one closed set the panel withheld while showing the value it governs.

**Five figures reach nobody and stay that way, each with a written reason in the bank**
(`refused_because`, new in `tools/layer_reads_baseline.json`): `counts.households` and
`households[].present_on_scene_date` and the household's own `division` are denormalised
copies of things already shown â€” showing the poorer copy would be showing less â€” and
`head`, in both copies, is a foreign key into `persons[].id` whose fact already reaches the
visitor as that person's `relationship`. A refusal is **not a permission**: the entries stay
banked, assertion 4 still fails on a new one and assertion 5 still fails if one leaves.

**Files:** `tools/measure_layer_reads.py` Â· `tools/layer_reads_baseline.json` Â·
`renderers/web/js/residents.js` Â· `tools/smoke_renderer.mjs` (stage 9).

### K53 â€” every shrub in the town is drawn as a giant forb Â· **DONE 2026-08-17 â€” the archetype is in, the recorded width is drawn, and the reason only fourteen of them stand is measured**

**The whole shrub layer is drawn with `forbGeometry()`** â€” one 12-triangle herbaceous stalk with
four broad leaves, scaled to the record's height. Twenty-one records across eight zones carry
`form: 'shrub_low'`, and `FORB_FORMS` contains that string, so a 3 m American hazel, a 2.5 m
elderberry, a multi-stemmed black-oak grub and a *sprawling mat* of sand cherry are all the same
wand of leaves at four different sizes. `placeForb`'s own comment names the damage and treats the
symptom: *"a riverbank shrub recorded at two metres across therefore grew sixty-centimetre leaves"*
â€” so the recorded clump width is CLAMPED to 0.40 m of spread, which is the shrub layer being made
narrow enough to look like a forb rather than being drawn as a shrub.

**It is SEEN and needs no exemption.** `corylus_americana` is the wet woods' *attested* dominant
shrub at 20â€“50 % cover â€” the dossier's own headline finding, with *"under-rendering hazel is the
specific mistake this record exists to prevent"* written beside it â€” and it is a wand. So is the
elder at the gallery edge, the dogwood on the river bank, the currant in the fenced dooryards and
the willow scrub on the lakeshore back slope, which is the population K45(b4) recorded as *"still
not planted"* in as many words.

**What it is NOT:** it is not a new record, not a new density and not a bake. Every number this
draws with â€” height, clump width, foliage greens, the July head â€” is committed and already read;
the archetype that consumes them is what is missing. The shrub form itself is a **reconstruction**
and gets a `docs/LIBERTIES.md` entry, exactly as the nine flower archetypes did.

**Files:** `renderers/web/js/flora.js` (a `shrubGeometry` archetype, a set beside `rosetteSet`, a
`placeShrub`) Â· `data/liberties.json` + `docs/LIBERTIES.md` Â· the flora gates' baselines if a read
moves Â· `renderers/web/js/changelog.js` Â· `site/chicago/4d/` Â· `docs/STATUS.md`.

**WHAT SHIPPED.** `shrubGeometry()` â€” four woody stems from one root, sixteen leaf sprays over
them, 40 triangles against the forb's 12 â€” on its own instanced set `flora-shrub`, dealt from the
forb lattice so it takes slots the forb archetype used to take rather than adding any. `placeShrub`
reads `width_m` as what it is on a shrub: the clump diameter. **Measured on the published mirror, at
all eight anchors and four bearings each:**

| | before | after |
|---|---|---|
| plants drawn with the shrub archetype | **0** | **14** |
| clump width | 0.40 m, the forb clamp | **1.80 m median, 2.00 m worst** |
| forb-layer plants, all archetypes | 2,201 | 2,187 + 14 = **2,201** |
| flora triangles, worst view | 41,754 | 41,772 |

**The census is identical plant for plant**, per zone as well as in total (`z08_lakeshore` 131 â†’
122 + 9, `z05_riverbank_timber` 61 â†’ 57 + 4, `z06_dense_forest` 222 â†’ 221 + 1). Nothing was redealt,
no density moved, and no record changed: this parcel changes what a plant is DRAWN as and nothing
else, which is why the sward census gate reads the same 6,809 slots and the same 154.19 / 89.11
deviations K49(c2) banked.

**FINDING 1 â€” the wands were only survivable because the width was clamped away.** `placeForb`
clamps spread to 0.40 m, and its own comment says why: *"a riverbank shrub recorded at two metres
across therefore grew sixty-centimetre leaves"*. That is the leaf archetype being protected from a
number that was never a leaf. `prunus_pumila`'s committed appearance is *"low sprawling mats 1-3 m
across"* and it was drawn 0.7 m wide and vertical. **A clamp that exists to protect one archetype
from another's data is a missing archetype, stated as a bound.**

**FINDING 2 â€” and it is why this is fourteen plants and not a hundred and forty: the forb lottery
deals by HEAD COUNT, so it under-draws exactly the plants that are big.** K49(c2) moved the lottery
onto `stems` â€” plants per mÂ² â€” to fix the opposite fault, a species recorded as covering 25 % of the
ground being dealt as 0.25 plants/mÂ². The conversion for a cover-recorded species is
`cover / (Ï€ Â· (width/2)Â²)`, so a hazel that covers 7 mÂ² of ground converts to 0.088 plants/mÂ² and
competes for slots against `allium_tricoccum` at **40 plants/mÂ²**. Measured over each zone's forb
list, the shrubs' share of the lottery is:

| zone | shrub share of the forb list | the species that takes the rest |
|---|---|---|
| `z10_settled_town` | **0.1 %** | four weeds at 0.4â€“1.1 plants/mÂ² |
| `z06_dense_forest` | **1.0 %** | `allium_tricoccum`, 99.0 % |
| `z08_lakeshore` | 2.6 % | `artemisia_campestris`, `campanula_rotundifolia` |
| `z05_riverbank_timber` | 3.0 % | `allium_canadense`, 97.0 % |
| `z09_sand_prairie` | 7.6 % | `allium_cernuum`, `monarda_punctata` |

So `corylus_americana`, **attested** at 20â€“50 % ground cover and named in its own note as the
specific under-rendering this record exists to prevent, is drawn as **1 plant of 221** in the wet
woods. The count is not wrong â€” one hazel IS one plant â€” but the layer is a SAMPLE of ~220 slots
against a population of tens of thousands, and a sample drawn by count reproduces the population's
head count while reproducing none of its ground cover. **Both readings are defensible and this
parcel changes neither**; the numbers are banked and the question is opened as **K54** rather than
retuned here, because K49(c2) moved this lottery deliberately and moving it back is a decision, not
a repair.

**FINDING 3 â€” the first cut of the archetype was the wand at a larger size.** Four stems each
carrying one 60 cm paddle reads as a candelabra, not a bush; the shot showed it and the fix was
sixteen small sprays over two heights rather than four big ones. **A silhouette is made by its
outer shell**, which is the same thing `trees.js` says about a crown in its own comment â€” and it is
worth writing down that the archetype had to be LOOKED at, twice, after it measured correct.

**Verified:** `tools/check.sh` â€” CHECK PASS (the dev gate; `chicago-4d-check.yml` runs it and
nothing else), after `tools/publish.sh` in the same commit. `tools/measure_sward_draw.mjs --gate` â€”
PASS, 0 of 98 (list, species) pairs drawn nowhere, 6,809 slots, deviations unmoved. The before/after
readings above are `flora-shrub`/`flora-forb`/`flora-rosette` instance counts and their `aFlora`
attributes read back off the published mirror at 1280Ã—800, against a worktree of `origin/dev` for
the before column. Evidence: `docs/evidence/k53-{before,after}.png`, the river-bank stand at
E âˆ’288 / N +368 facing SSE. **Zero page errors** in every run.

**NOT verified here:** neither half of `tools/smoke_renderer.mjs`. The desktop half has never fitted
this runner's ten-minute per-command ceiling and K45(b4) recorded the mobile half outgrowing it too;
the three gates in it that read the flora sets by NAME were extended to `flora-shrub` in this commit
(rooted-plant anchoring, the pop-in walk, head support) plus `tools/measure_head_support.mjs`, so
the new set is inside them rather than invisible to them â€” but that extension is unexecuted here and
is the first thing to run on a runner without the ceiling.

### K54 â€” the forb lottery deals by head count, and the shrub layer is the population it loses Â· **DONE 2026-08-17 â€” route 2, and neither reading of the sample was the fault: the two strata were sharing one lattice**

**The answer to "which quantity should a sample reproduce" is that this sample did not have to
choose.** A lattice slot is 2.89 mÂ² of ground and carries one plant, so where the herb layer's own
recorded density SATURATES the lattice â€” five of the ten communities â€” the deal stops being a
population draw and becomes a count-proportional subsample. A subsample by head count thins the
shrubs by the whole saturation ratio, and in the wet woods that ratio is **117**. But a hazel clump
stands OVER the leeks rather than instead of them, and the records state the two separately: nine
`shrub_low` records in `z06_dense_forest` summing to **94.9 %** ground cover, above a herb layer
recorded at **40 plants/mÂ²**. So the shrub stratum is dealt from **its own lattice pass over the same
ring**, at its own recorded clump density, with a different salt so the two draws are independent.
**Nothing is taken from the herb layer to pay for it, and no share, cap or tuning number was
authored.**

| `tools/measure_sward_draw.mjs`, published mirror, 8 communities stood in | before | after |
|---|---|---|
| shrub instances standing, summed over the 8 stations | **4** | **181** |
| shrubs drawn standing in `z06_dense_forest` | 2 | **156** |
| drawn shrub cover there, against a recorded 94.9 % | ~0 | **40.1 %** |
| drawn shrub cover, `z05_riverbank_timber`, recorded 19.5 % | 2.0 % *(the whole forb list)* | **20.1 %** |
| deviation per 100 slots â€” matrix | 2.58 over 5,965 | **2.58 over 5,965** |
| deviation per 100 slots â€” forb | 10.56 over 844 | **10.40 over 781** |
| deviation per 100 slots â€” shrub | â€” | **10.41 over 181** |
| (list, species) pairs owed a whole slot and drawn nowhere | 0 of 98 | **0 of 98** |

**The gain K54 required is kept, and the raw sums cannot show it** â€” `forb 89.11` became
`forb 81.22 + shrub 18.84` because the deviation is an absolute sum over slots and this parcel split
one list into two. Per 100 slots the herb list IMPROVED and the new shrub list draws at the same
fidelity. Hence the tool's new per-slot column: **a discrepancy sum cannot compare two draws of
different sizes**, and every previous parcel that quoted 89.11 against another build was comparing
lists of the same length by luck.

**FINDING 1 â€” the slot count still mixed units, and it planted the riverbank understory 8.8Ã— too
thickly.** K49(c2) moved the LOTTERY onto `stems` and its own comment says the slot count was left
on the recorded sum. That sum adds cover fractions to plants per mÂ², and sixteen of the twenty-one
shrub records state an area: `z05_riverbank_timber`'s forb share was **0.636 where its herb records
give 0.072**, and `z07_bur_oak_savanna`'s hazel â€” its only forb-list species â€” was planted at **4Ã—**
its own recorded clump density. So the riverbank swap is not only more shrubs: it is **11 dogwood,
elder and ninebark clumps carrying 20.1 % cover in place of 33 herbs carrying 2.0 %**, and the herbs
that left were never in the record. Dealing the shrub stratum off `stems` closes it for that
stratum; **four herb lists still carry it (`z03`, `z05`, `z06`, `z10`), and the tool now names them
with a `basis` column. Opened as K55.**

**FINDING 2 â€” the instrument K54's own box named cannot answer K54's question, and had been
mislabelled since K49(c2).** `expected` is `share Ã— slots` and `share` is the species' share of the
LOTTERY, so *"deviation from the recorded cover"* â€” the line this box quoted as *"the very quantity
in question"* â€” measures the lattice's disagreement with its own target distribution and never
touches a record. It is the right figure for comparing two draws and the wrong one for judging
fidelity to the data. The tool prints a real `cover` column now, and **its first denominator was
wrong in R-M1c's exact way**: dividing a community's drawn plants by the whole ring reported 17.9 %
where that community holds a fifth of the ring. It divides by the community's own MEASURED plantable
ground inside the ring â€” 1 mÂ² samples through `zoneAt` and `plantableAt`, the placer's own rules.

**What it costs and what is NOT verified.** One extra lattice pass over the forb ring per rebuild;
`flora-shrub` was already a committed set and a committed draw call, so the frame gains instances and
no batch. Neither half of `tools/smoke_renderer.mjs` ran â€” the desktop half has never fitted this
runner's ten-minute per-command ceiling and the mobile half has outgrown it (K45(b4), K53) â€” and the
scene was not measured at `full` detail, where the lattice offers ~1,113 slots against the set's
900-instance cap, so a saturated community may cap there. The forb set has the identical lattice and
cap and sits just under it today. `tools/check.sh` CHECK PASS after `tools/publish.sh` in the same
commit; `--gate` PASS; zero page errors in every run.

**Two station-row diagnostics appeared and are not the gate.** `solidago_riddellii` (owed 1.77 at one
station) and `physocarpus_opulifolius` (owed 1.17 at one station) are drawn nowhere in the ring at
one station each, having been drawn there before; both are drawn elsewhere in the scene, so the
K49(f) scene-wide gate reads 0 of 98 as it did. They moved because removing the shrubs renormalised
those lists' shares. Read K49(a) before quoting a station row as a scene figure.

**The routes NOT taken.** Route 1 (a fixed slot share off `cover_fraction`) authors a quantity no
record states, and the measurement that decided against it is worth keeping: dealt on cover, the
shrubs would take **30â€“100 %** of the forb list's slots in seven of ten communities, because the herb
forbs' own summed cover is under 1 % of the ground in most of them â€” the ground cover in a prairie
belongs to the MATRIX list, which is dealt separately. Route 3 (say it on the card) was available and
is now unnecessary.

**FINDING 3 â€” and it came from LOOKING, which is K53's finding 3 one parcel later: the archetype
was designed and photographed at fourteen instances in the whole scene, and the wet woods now
carries 158 in one ring.** `docs/evidence/k54-{before,after}.png`, the same station (E âˆ’54 / N +314,
bearing 135Â°) at 1280Ã—800 on the published mirror: the before frame is an open field with a log
building 15 m away and ONE shrub in the corner; the after frame is a thicket the building shows
through. That is what the record asks for â€” `z06_dense_forest` reads_as *"a hazel shrub layer
through all of it"* and its nine shrub records sum to 94.9 % cover â€” and it is also the first time
anyone has seen this archetype repeated. **At that density its leaf sprays read as ~0.4 m paddles**,
which is the shell L122 bounded to 0.30â€“0.55 of the recorded half-width and is defensible on a
2.25 m hazel; whether it should scale that way is now a question a visitor can answer, and it is
opened as **K56**. Flora triangles at the station **46,904 â†’ 58,868**; the herb layer is untouched
(forb 194 â†’ 195, rosette 35 â†’ 31) which is the arithmetic proof that nothing was taken to pay for
it; zero page errors.

### K54 â€” original statement, for the record Â· **superseded by the box above**

**The arithmetic is banked in K53 finding 2 and is not in dispute.** The forb layer deals ~220
slots over the ring; each slot is one plant; species compete for slots on `stems`, plants per mÂ².
A hazel covering 7 mÂ² of ground is 0.088 plants/mÂ² and a wild leek is 40, so the wet woods are
drawn as leeks with one shrub in them, and the shrub layer their own dossier calls the dominant
one takes **1.0 %** of the deal.

**The question is which quantity a SAMPLE should reproduce.** By head count the current deal is
exactly right and the frame is wrong; by ground cover the frame would be right and the head count
wrong. Three routes, none of them free:

1. **Deal a fixed share of the slots to the shrub sub-list**, off the recorded `cover_fraction` â€”
   the field the shrubs mostly carry â€” and deal the rest by count as today. Honest, cheap, and it
   makes the layer's slot mix a second authored quantity that no record states.
2. **Give the shrubs their own lattice**, the way `trees.js` has one: a sparse layer dealt on
   plants per hectare over a wider radius, which is what a shrub layer physically is. The most
   faithful and the largest.
3. **Leave it and say so on the card.** The layer is a count-faithful sample; the Evidence panel
   could say that a drawn plant is one plant and that ground cover is not what the sward reproduces.

**Do not take this as a tuning.** K49(c2) moved this lottery onto counts deliberately and measured
the improvement; whatever lands here has to keep that gain (matrix 154.19 / forb 89.11 deviation,
0 species drawn nowhere) and say which quantity it is now faithful to. **`tools/measure_sward_draw.mjs`
already prints everything needed to judge it** â€” it reports the deviation from recorded cover, which
is the very quantity in question.

**Files:** `renderers/web/js/flora.js` (`compileZones`, `dealt`) Â· `tools/measure_sward_draw.mjs`
(a cover-share column) Â· `docs/LIBERTIES.md` if a share is authored.

### K55 â€” four herb lists still deal their SLOT COUNT off a sum of areas and counts Â· **DONE 2026-08-17 â€” the same fault runs BOTH WAYS, and for the herbs it ran the other one: the riverbank's ground layer was planted 96Ã— too THINLY**

**The repair.** `SLOT_BASIS` is one object naming which sum each stratum's slot count is dealt off,
and both lattice strata now read `stems`. The forb half is what moved; the arithmetic is K54's and
was not re-derived.

| forb layer | density before | after | ratio | forbShare before â†’ after |
|---|---|---|---|---|
| `z05_riverbank_timber` | 0.025 /mÂ² | **2.407** | **96Ã—** | 0.072 â†’ **1.0 (clamped)** |
| `z10_settled_town` | 0.395 | **7.760** | 19.6Ã— | 1.0 â†’ **1.0, no slot moves** |
| `z03_sedge_meadow` | 0.123 | **1.254** | 10.2Ã— | 0.354 â†’ **1.0 (clamped)** |
| `z06_dense_forest` | 40.615 | **44.545** | 1.10Ã— | 1.0 â†’ 1.0 |
| the other six | unchanged to the digit | | 1Ã— | unchanged |

Drawn, on the published mirror over the census's eight stations: **forb slots 781 â†’ 923**,
`z03_sedge_meadow`'s own layer **31 â†’ 84** (cover 1.0 % â†’ 2.8 % of a recorded 11.0 %),
`z05_riverbank_timber`'s **1 â†’ 16** at its own station and **4 â†’ 50** standing in the wet woods, with
a row at `z03` that did not exist before (**0 â†’ 14**). Forb deviation per 100 slots **10.40 â†’ 9.33**.
**Matrix and shrub are unchanged to the second decimal** â€” 154.19 and 18.84, the same figures K54
banked â€” and `0 of 98` pairs are drawn nowhere.

### Finding 1 â€” a cover fraction read as a count is wrong in whichever direction the plant's own size points

K54 measured this fault OVERSTATING by 8.8Ã— and fixed it downward. The herb lists have it
understating by up to 96Ã—, and the two are the same division: `stems = cover Ã· Ï€(width/2)Â²`, so the
sign is decided by whether one plant covers more or less than a square metre. A 2.25 m dogwood
clump covers ~4 mÂ², so its cover fraction is a bigger number than its count; a 10 cm forb covers
~0.008 mÂ², so its cover fraction is ~125Ã— smaller. **"Adding an area to a count" was banked here as
over-planting because that is the case that was measured first**, and the queue inherited the
direction along with the diagnosis.

### Finding 2 â€” the report was naming three refusals as work, because it printed a default argument

The parcel's own box suspected the matrix half was a refusal and it is: `matrixShare` comes off
`cover.matrix_fraction` directly, and `subsetOn`'s `density` was **computed for the matrix and read
by nobody**. The `basis` column that named `z03.matrix`, `z08.matrix` and `z09.matrix` as K55 work
was printing `subsetOn`'s default parameter, not a fact about the renderer â€” so three of the parcel's
six named rows were never faults at all. Both the renderer and the report read `SLOT_BASIS` now, and
the matrix's entry is `null` rather than a label, so there is no number left to misread.

### Finding 3 â€” it is SEEN, and only just: the count moved a fifth and the picture moved 0.15 %

`docs/evidence/k55-{before,after}.png`, `z05_riverbank_timber` at E âˆ’300 / N +398 bearing 090Â°,
1280Ã—800 on the published mirror: **1,586 changed pixels of 1,024,000 (0.15 %)** â€” a scatter of white
flower heads through the near grass. At the `z03_sedge_meadow` station the same comparison is **24
pixels at 135Â° and nothing at 315Â°**, because the added plants are small and stand under a dense
matrix layer. **The parcel's own prediction that `z10_settled_town`'s weeds were "the visible half"
is refused by the table above**: that share was over the lattice ceiling before and after, so the
one community a visitor spends the walk in is the one community that does not move. Quote the
counts for this parcel, not a screenshot.

### Successor â€” K58, the forb lattice's ceiling now binds six communities of ten

`forbShare` clamps at one plant per slot, and K55 takes the clamped count from four communities to
six (`z05` and `z03` join `z04`, `z08`, `z10`, `z06`). A clamped share means the record is asking for
more plants than the lattice can carry, so the drawn cover is bounded by `TUNE.forb` rather than by
any research figure â€” `z06_dense_forest` reaching 40.1 % of a recorded 94.9 % is that ceiling, not a
data gap. Opened below.

### K55 â€” original statement, for the record Â· **superseded by the box above**

**The arithmetic is banked in K54 finding 1 and is not in dispute.** `subsetOn`'s `density` sums
`s.recorded` â€” the abundance in whatever unit the record used â€” and `forbShareOf` reads that sum as
plants per mÂ². Where a list mixes the two, the slot count is a cover fraction added to a count.
K49(c2) left it there deliberately and said so; K54 fixed the shrub stratum's half of it by dealing
that list off `stems`. **What is left, printed every run by `tools/measure_sward_draw.mjs` under
`slot count off 'recorded'`:** `z03_sedge_meadow.matrix`, `z03_sedge_meadow.forb`,
`z06_dense_forest.forb`, `z08_lakeshore.matrix`, `z09_sand_prairie.matrix` â€” and `z05`'s and `z10`'s
forb lists, which are ENTIRELY area-recorded and therefore do not register as "mixed" at all. That
last case is the trap: a list where every species records an area reads as consistent and its slot
count is still wrong by the same conversion.

**It is SEEN and it is not a free change.** `z10_settled_town`'s forb layer is the weeds in the
streets of the town a visitor spends most of their walk in, and its share is currently saturated at
1.0; dealt on `stems` it may not be. So this is a measure-then-fix parcel: land the before/after
census with the per-100-slot column K54 added, and expect the town to look different.

**The matrix lists are the harder half and may be a refusal.** `matrixShare` comes off the record's
own `cover.matrix_fraction` and is not this sum at all, so a matrix list's `mixed` row is about the
LOTTERY only, which K49(c2) already put on `stems`. Check that before changing anything there.

**Files:** `renderers/web/js/flora.js` (`subsetOn`, `forbShareOf`) Â· `tools/measure_sward_draw.mjs`
baselines Â· `docs/STATUS.md`.

### K56 â€” the shrub's leaf spray is scaled off the clump width, and 158 of them in one ring is the first look anyone has had at that Â· **DONE 2026-08-17 â€” the spray is a leaf MASS, so the size was never the number: sixteen of them covered 17.7 % of the shell and you could see straight through every clump**

`shrubGeometry`'s sprays are a fraction of the recorded half-width (L122), so a `corylus_americana`
recorded 2.25 m across carries sprays about 0.4 m long. At fourteen instances scattered over the
whole scene that was invisible; at **158 in the wet woods' ring** it is the near-field texture of a
whole community â€” `docs/evidence/k54-after.png`.

**The question is not whether 0.4 m is right, it is what the spray STANDS FOR.** A grass tuft in
this renderer is a bundle of shoots and says so; if a spray is a bundle of leaves then its size is a
rendering choice bounded by the plant's shell and the answer may be "unchanged". If it is meant to
read as a leaf, a hazel leaf is ~10 cm and no scaling off the clump width can produce one at 40
triangles. **Decide which, write it into L122 or a new liberty, and only then change a number.**

Cheap and visible: one archetype function, one before/after pair at the station K54 used, and
`tools/measure_sward_draw.mjs` is unaffected because no count moves.

**Files:** `renderers/web/js/flora.js` (`shrubGeometry`) Â· `docs/LIBERTIES.md` Â· `docs/evidence/`.

**THE ANSWER TO THE QUESTION THE PARCEL ASKED, because it decides which number moves.** A spray
stands for **a mass of leaves on one shoot**, not a leaf. That is the same abstraction the tree
canopy's plates and the near tuft's bundle of shoots already use in this renderer, and it is the
only one two triangles can carry: a hazel leaf is ~10 cm and no scaling off the clump width
produces one. So the honest reading of the 0.4 m spray is **not wrong**, and shrinking it would
have bought a smaller plate with more sky around it. Written into `docs/LIBERTIES.md` as **L124**
before any number changed, which is the order the parcel asked for.

**WHAT THE LOOKING FOUND, and it is the count.** Summed over the archetype's own loop, the sixteen
sprays' plates cover **17.7 %** of the shell they are spread over â€” a clump a visitor sees straight
through, which is why an isolated plate reads as one enormous leaf: nothing overlaps it. **32
sprays cover 30.9 %.** `docs/evidence/k56-{before,after}.png`, the same station K54 used (E âˆ’54 /
N +314, bearing 135Â°) at 1280Ã—800 on the published mirror.

| | before | after |
|---|---|---|
| leaf sprays per shrub | 16 | **32** |
| spray bands | 2 | **3, the lowest arching DOWN** |
| plate area, archetype unitsÂ² | 1.399 | **2.698** |
| shell fill | 17.7 % | **30.9 %** |
| triangles per shrub | 40 | **72** (+5,056 in the wet woods' ring, of a 1,000,000 ceiling) |
| spray length on a 2.25 m clump | 0.26â€“0.44 m | **0.26â€“0.44 m â€” unchanged** |
| drawn reach, as a fraction of the recorded half-width | 0.91 | **0.98** |

**FINDING â€” nothing in the first cut hung below its own attachment.** All sixteen sprays rose, so
the shell stayed open exactly where the four stems are most exposed, and `k0 = shade(0.16)` makes
those stems a black stick wherever foliage does not cover them â€” which the archetype's own comment
had feared in the abstract and the before frame shows happening. The lowest of the three bands now
arches down over them, bounded so no tip is pushed below the plant's base.

**No census moved.** Same species in the same places, plant for plant; `spread`, `height` and the
lattice are untouched. The gate `tools/measure_sward_draw.mjs` is unaffected, as the parcel
predicted, because no count moves.

### K57 â€” the spray's GRAIN, which trades triangles against the size of a leaf mass Â· **DONE 2026-08-17 â€” asked at a fixed plate area it cannot be asked at all, because the plates carry the recorded clump width; 48 sprays ship at K56's plate size and 48 is where the return halves**

K56 answered *what a spray stands for* and moved the count. It did **not** answer the finer
question underneath: at a fixed total plate area, is the shell better read as 32 masses of 0.4 m or
64 of 0.2 m? That is a grain question and it costs triangles â€” 32 sprays is 72 triangles a shrub,
64 would be 136 â€” so it needs a **frame-time and triangle budget measured in the wet woods**, where
158 of them stand in one ring and the matrix layer is densest, rather than a preference.

**What bounds the answer.** The plate may not shrink below the size at which it reads as a single
leaf against its neighbours, which is the fault K56 diagnosed and would rebuild at a smaller scale
if the count did not rise with it. So grain and count move together or not at all.

Cheap and visible: one archetype function, one before/after pair at the same station, and the
triangle line printed by the smoke at both viewports is the budget half.

**Files:** `renderers/web/js/flora.js` (`shrubGeometry`) Â· `docs/LIBERTIES.md` Â· `docs/evidence/`.

**What it measured, banked so nothing re-derives it.** 24 bearings, orthographic, on the archetype the
scene draws â€” foliage cover is the UNION of the projected plates over the convex hull of them, because
"you can see straight through it" is a statement about union and a sum counts an overlap twice:

| candidate | plate area | cover | worst bearing | stem cover | reach | plate cm | triangles |
|---|---|---|---|---|---|---|---|
| 32 @ 1.000 (K56) | 2.698 | 36.9 % | 33.0 % | 40.9 % | 0.990 | 37.3 | 72 |
| 48 @ 0.816 (area held) | 2.604 | 43.3 % | 39.3 % | 46.8 % | 0.930 | 29.3 | 104 |
| 64 @ 0.707 (area held) | 2.624 | 45.4 % | 41.5 % | 48.3 % | 0.890 | 25.8 | 136 |
| **48 @ 1.000 (shipped)** | 3.812 | **46.9 %** | **43.0 %** | **51.3 %** | **0.998** | 35.0 | **104** |
| 64 @ 1.000 | 4.986 | 51.3 % | 47.3 % | 54.2 % | 0.997 | 34.6 | 136 |

**The generalisation, and it is not about shrubs.** An archetype's numbers divide into the ones the
RECORD owns and the ones the renderer owns, and a tuning question phrased as "hold X and improve Y" is
only answerable once you know which side X is on. Here X was the total plate area, which sounds like a
renderer number and is a researched one wearing a disguise: the plates ARE the silhouette, and the
silhouette is the record's `height_m` and half-width. **Before holding a quantity fixed in any
archetype, ask which side of that line it is on.** The same trap is live in every other plate-based
archetype here â€” the tree canopy, the near tuft, the forb head.

### K59 â€” the last 4.4 points of the shrub's shell, and whether a frame can afford them Â· **DONE 2026-08-23 (T-0020) â€” the frame was read and the points are spent: 64 sprays ship, for +3.0 % of a frame on desktop and +2.1 % on mobile against a 0.2 % A/B/A control**

K57 shipped 48 sprays at the knee and left 64 measured and unspent: **cover 46.9 % â†’ 51.3 %, worst
bearing 43.0 % â†’ 47.3 %, stem cover 51.3 % â†’ 54.2 %, for 104 â†’ 136 triangles a shrub** and 17,368 â†’
22,712 in the wet woods' ring of 167, of a 1,000,000 ceiling. Reach is unaffected (0.998 â†’ 0.997), so
this is a pure budget question and the numbers are already banked â€” nothing needs re-measuring.

**What is NOT known, and it is the whole parcel:** no frame-time figure has been taken anywhere in this
archetype's history. K57 justified 104 on a triangle count and a draw-call count, which is not a frame.
The batch does not split â€” one instanced set, one draw call, K56 and K57 both â€” so the cost is fill and
vertex work, and neither has been read. **Take this parcel only with a frame-time measurement in
hand**, in the wet woods where 167 of them stand; without one it is a preference wearing a table, which
is exactly what K57 refused.

**Files:** `renderers/web/js/shrub-grain.js` (`SHRUB_GRAIN.fill`) Â· `tools/measure_spray_grain.mjs`
Â· `docs/LIBERTIES.md` Â· `docs/STATUS.md`.

**THE ANSWER, 2026-08-23 (T-0020). The parcel's own condition was met before anything moved:
`tools/measure_shrub_frame_cost.mjs` is the frame-time instrument this box refused to be claimed
without.** It stands the walker in `z06_dense_forest` â€” 158 shrubs drawn in one ring, the densest
of the ten communities â€” sweeps eight bearings and fixes the camera at the most expensive of them
(1,343,341 triangles at 135Â°), holds the clock, drives frames one at a time rather than letting the
browser pace them, and fences each frame with a one-pixel readback.

| | 48 sprays | 64 sprays | |
|---|---|---|---|
| desktop 1280Ã—800 | 4282.30 ms | 4410.30 ms | **+3.0 %** |
| mobile 390Ã—780 | 2739.60 ms | 2795.80 ms | **+2.1 %** |
| desktop, shipped grain measured AGAIN | **4292.90 ms** | | **+0.2 %** â€” the control |

**Finding 1 â€” three points of a frame for 4.4 points of shell, and the control is what makes that
readable.** The A/B/A third row is the identical scene measured after the candidate: the runner's
own drift is two tenths of a point, so the candidate's three are fifteen times it. Cover 46.9 % â†’
51.3 %, worst bearing 43.0 % â†’ 47.3 %, stem cover 51.3 % â†’ 54.2 %, reach unmoved at 0.997, 17,368 â†’
22,712 triangles in the ring of a 1,000,000 ceiling. **64 ships** (L175).

**Finding 2, and it is the durable one â€” `gl.finish()` IS NOT A FENCE HERE, and a measurement built
on it was wrong by a factor of a thousand.** The first cut of this instrument timed `step()` +
`gl.finish()` and reported **2.90 ms** a frame while the process spent about **four seconds** of
wall clock on each one. ANGLE's SwiftShader backend rasterises in another process, so a finish
returns having synchronised nothing a caller can observe; what was being timed was how fast three.js
can TALK, which is the one quantity that does not move when a shrub grows 32 triangles. It even
produced a plausible-looking answer â€” **+31 %**, which would have refused this parcel. A one-pixel
`readPixels` is a real fence, because the caller cannot be handed a pixel that has not been drawn,
and it is what the renderer's own `capture()` has always used. **Read this before timing anything in
a browser here, and prefer a readback to a finish.**

**Finding 3 â€” a Playwright route handler is not free.** The grain was first injected by intercepting
`shrub-grain.js` with `page.route`. Registering ANY route turns network interception on for EVERY
request in that context, and this page pulls several hundred GLB and JSON files through it: one page
load went from about eight seconds to over four minutes. The instrument patches the byte at the
static server it already runs instead.

**What this parcel does NOT settle.** Every figure above is a headless software rasteriser on a
shared CI machine â€” the absolute milliseconds are that machine's, and a frame there is four seconds.
The ratio is the answer, and it argues in the safe direction: a software rasteriser is the most
fill-sensitive renderer available, so it is the harshest witness for the one risk here (overdraw
1.33 â†’ 1.56). The reading L121, L156 and L174 all still want â€” a real low-end machine â€” is not this.

### K58 â€” six forb layers of ten now ask for more plants than the lattice can carry Â· **DONE 2026-08-28 as T-0019 â€” NINE of ten, and declared rather than fixed**

**Answered.** The count in this box's title is wrong twice over and both errors are worth keeping: it is **nine** populated forb layers of ten, and the densities below are the recorded MIDPOINTS while the renderer has dealt the forb stratum off each record's UPPER BOUND since T-0034. Measured 2026-08-28, `tools/measure_sward_draw.mjs --source`: `z06_dense_forest` asks **66.381** plants/mÂ² against 44.545 here and draws **0.5 %** of it; `z04_marsh` 22.000 against 14.5 (and its WET side the same, measured for the first time); `z10_settled_town` 11.866 against 7.760; and `z08_lakeshore` (0.630), `z02_mesic_prairie` (0.408) and `z01_wet_prairie` (0.407) have joined the clamp since. `z09_sand_prairie` alone fits.

**Route taken: the third one this box names â€” print the shortfall â€” and it is now a declaration with a gate on it** rather than a printed line: `tools/forb_clamp_baseline.json`, asserted by `measure_sward_draw.mjs --gate`, which fails on a layer joining the clamp, a layer leaving it, the ceiling moving, or an asked density drifting. Shown reading red three ways. **No ceiling constant was raised**: the other two routes buy plants with geometry, most of it in `z06` and `z10`, and the `full` and `balanced` detail ceilings are breached on dev (T-0223, T-0229). See `docs/STATUS.md` 2026-08-28. The original box follows.

`forbShareOf` is `min(1, density Ã— cellÂ² / perCell)`, and the clamp is a lattice ceiling of one
plant per slot. K55 took the number of communities sitting ON that clamp from four to six â€” `z05`
(2.407 plants/mÂ² asked) and `z03` (1.254) join `z04` (14.5), `z06` (44.545), `z08` and `z10` (7.760).

**What the clamp costs, stated plainly: those six layers are drawn at a density `TUNE.forb` chose
and not at one any record states.** `z06_dense_forest` drawing 40.1 % of its recorded 94.9 % cover is
that ceiling and not a research gap, and K54's box already flagged it as the one community whose
shrub density reached it â€” the forb stratum has now joined it in five more.

**It is not a free tune, which is why it is its own parcel.** The lattice's cell and `perCell` were
fitted against the reference photographs on a closed prairie sward (L32), so raising either changes
every community and costs geometry in exactly the two â€” `z06`, `z10` â€” that already carry the most.
Candidate routes, none of them chosen here: a per-stratum cell; more than one plant per slot where
the record asks for it; or accepting the ceiling and **printing the shortfall per community**, which
is at least honest and is nearly free.

**The measurement to land first**, and it fits in one census run: `tools/measure_sward_draw.mjs`
already knows both numbers, so print `forbShare` beside the drawn cover per community and the size
of the debt is visible without a single plant moving. `flora.communities()` exposes `forbShare`,
`forbShareWet`, `shrubShare` and both densities as of K55, so nothing new needs wiring.

**Files:** `renderers/web/js/flora.js` (`forbShareOf`, `TUNE.forb`) Â· `tools/measure_sward_draw.mjs`
Â· `docs/STATUS.md` Â· `docs/evidence/`.

### K52 â€” nobody has censused what the residents' figures reach Â· **UNCLAIMED Â· UNSEEN Â· opened 2026-08-17 by K51 Â· Effort: Sâ€“M**

`tools/measure_layer_reads.py` covers `data/flora` and `data/fauna`; `generators/archetypes/*_params.py`
and `generators/terrain_inputs.py` declare their own `CONSUMED`. **`data/residents/` is declared by
nothing.** It is published (`tools/publish.sh` copies it) and the building card names the households
attached to a structure, so unlike this morning's fauna the layer certainly has *a* reader â€” which
makes it the harder question, not the easier one: a layer with one reader is exactly where an
unread figure hides, because "the browser has it" reads as "somebody looks at it". 96 researched
people, 113 invented names, and no answer to which of their figures a visitor ever sees.

**It is UNSEEN and carries no exemption**, so it is not a pick while the visible queue has picks in
it. Take it the way K51's own gate was taken: as the second half of a parcel that ends in a card.

K42 finding 2, taken: **`data/fauna` has no reader, and three separate documents imply it does.**
139 animal records across ten habitat zones, 90 citations, every one of them researched to the
July gate â€” and no file under `renderers/` names the directory, `tools/publish.sh` does not copy
it, so a browser has never been offered the layer. K42 wrote three routes and this is route 2,
*"give it a reader"*, which its own box says is a renderer parcel of real size and **no bake**.

**It is a CARD, not a herd.** Nothing is drawn in the 3-D scene: the standing constraint on
depicting people is untouched, and no animal geometry is proposed here. What a visitor gets is
the Evidence panel section this dataset was always for â€” the ten habitats, what each reads as on
1 July, and every species with its July status, presence mode, abundance, behaviour, voice and
its sources. The visible-progress rule's own definition of SEEN is *"in the 3-D scene or on a
card a visitor opens"*, and this is the second of those.

**The gate it must pass through is the one K42 built.** `tools/measure_layer_reads.py` assertion
3a fails the moment a layer with no declared reads gains a reader â€” deliberately, *"because the
whole of this layer's unread bank rests on nobody opening it"*. So the parcel owes a read map for
all 30 fauna figures, in the same commit, and the self-test's negative control has to move off
`fauna` onto a synthetic source rather than the repository's own state.

**Files:** `renderers/web/js/fauna.js` (new) Â· `renderers/web/index.html` Â· `renderers/web/js/main.js`
Â· `renderers/web/css/*` Â· `tools/publish.sh` Â· `tools/compile_scene.py` (the citation join only)
Â· `tools/measure_layer_reads.py` + its baseline Â· `tools/smoke_renderer.mjs`.

### K50 â€” ask every other layer the question that caught R-BUG5b Â· **DONE 2026-08-17 â€” both layers draw where they decided, and the instrument that caught R-BUG5b does not transfer whole**

**The answer is: nothing is mirrored.** 331 structures unioned out of 1,310 drawn instances,
**533,346 vertices read back** through the instance matrices the renderer hands the GPU, and
**19,372 road vertices** read back off the ribbon:

| layer | population read back | anchors outside their own drawn footprint | nearer to their MIRROR |
|---|---|---|---|
| `buildings.js` | 331 structures Â· 533,346 vertices | **0**, worst **0.00 m** | **0** |
| `streets.js` | 19,372 vertices Â· 3 meshes Â· 17 centrelines | **0** off every centreline, worst **0.00 m** | not a discriminator â€” see finding 2 |

Measured on the **published mirror** at 1280Ã—800, against the DATA rather than against another
renderer number: a structure's `placement.local_e/local_n` in its sidecar and a street's
`path_local_enu_m`. The ground half was not redone â€” `smoke_renderer.mjs` already reads the drawn
surface back against `heightfield.bin` at every field sample and `tools/measure_terrain_horizontal.mjs`
holds its two horizontal axes â€” and `flora.js` was measured clean by R-BUG5b itself. **All four
layers named in this parcel are now answered.**

**Finding 1 â€” a per-INSTANCE box is not a building, and the first reading of this census said 279
of 1,310 bodies were misplaced.** A structure joins one batch per material it uses, so it holds
several instances and any one of them is walls, or roof, or trim. Judging a building by one of its
materials produced a **21 % false-positive rate** on a town that is entirely correct â€” worst
"stray" 24.45 m on `fort_dearborn_palisade`. `buildings.js` `instanceBounds()` warns about exactly
this in its own comment, for exactly the reason a size gate once passed a town of collapsed boxes:
*"a building is walls plus roof plus trim, and any one of those alone is not the building."*
**A new gate on this layer that does not union per structure id is measuring a material.**

**Finding 2 â€” the mirror test does not discriminate on a street grid, and R-BUG5b's instrument
therefore does not transfer.** Asking whether a drawn road vertex is nearer to a street at its
mirrored northing answered *yes* for **3,975 of 19,372** vertices on a build where every single
vertex is inside its own track. Two causes, both structural: reflect a point across an east-west
line in a **grid** town and it lands on another east-west street; and a vertex at the EDGE of its
own track scores worse than a mirror landing mid-track, by construction. So the streets gate is the
**half-width test alone** â€” which a mirrored ribbon cannot pass, because a reflected road runs
where no centreline is recorded â€” and the mirror figure is printed as a diagnostic that gates
nothing. What transferred from R-BUG5b was the QUESTION, not the instrument.

**Finding 3 â€” the gate was proved RED before it was believed.** `--refute` injects R-BUG5b's exact
fault into the live scene (the sign of each instance matrix's z translation; the sign of every
drawn road vertex's z) and re-runs the same census:

| | clean | fault injected |
|---|---|---|
| buildings outside their footprint | 0 of 331 | **329 of 331**, worst **1,238.89 m** |
| buildings nearer their mirror | 0 | **324** |
| road vertices off every centreline | 0 of 19,372 | **15,397**, worst 222.30 m, **5,010** off the grid altogether |

The two buildings that survive the mirror are the two standing on the datum's own east-west line,
which is arithmetic rather than a hole. This is R-A1's finding taken seriously one parcel on: *an
assertion that can only ever see one value is not an assertion*, and a placement gate that has only
run on a correct build has demonstrated nothing.

**What it unblocks, named as the visible-progress rule requires: `K30(c)`** â€” the queue's #1 SEEN
pick, *"29 buildings on eight streets are drawn standing in the roadwayâ€¦ redraw the bodies onto the
correct side of their own frontage."* K30(c) changes where 331 bodies are drawn relative to their
records, and until today **no gate in this project read the buildings layer's geometry back at
all**. The census is its acceptance instrument and its before-picture: worst anchor-outside-footprint
**0.00 m**, worst anchor-to-nearest-corner **47.11 m**.

**Files:** `tools/drawn_placement_census.mjs` (new â€” the census, shared) Â·
`tools/measure_drawn_placement.mjs` (new â€” the instrument, ~1 min at one viewport) Â·
`tools/smoke_renderer.mjs` (two gates, both viewports). The census lives in ONE module that both
import, because R-BUG5's own box records `measure_far_timber.py` and the browser disagreeing until
they were made to agree sample for sample.

R-BUG5b was invisible to three gates because all three asked where a layer DECIDED to put something
and none read back where it was DRAWN. Four layers decide in ENU and draw in three's world space:
`flora.js` (measured clean â€” `_m.setPosition(e, y, -n2)`), `streets.js`, `buildings.js` and
`ground.js`. The method is committed and cheap: transform each layer's drawn vertices to ENU with
`worldToEnu`'s own convention and compare them against the layer's own record of where it meant to
put them. **UNSEEN if it finds nothing and SEEN the moment it does**, which is the honest way to
scope it; it qualifies under the visible-progress rule's third exemption either way, as a gate on
nothing less than trust in every other placement gate in the renderer.

### R-BUG5 â€” trees stand in the river Â· **DONE 2026-08-16 Â· a real second fault, not the owner's picture**

**The owner's two populations are ONE cause, and neither of them is a planted stem.** The report was
a screenshot from 31 ft up, bearing 044Â°, north-east across the main stem: a straight LINE of woody
plants running out across the channel, and scattered ones over the open water beside it. The line is
`FAR_TIMBER.main_stem_belt_east`, a three-point polyline in `renderers/web/js/trees.js`, and the
scatter is the horizon solver's own gap modulation breaking the rest of the same run into separate
crowns.

**Measured, from the reported viewpoint with the far bank loaded, and the population is reported so
the denominator is visible** â€” the trap this box warned about is real and the probe below does not
fall into it:

| population | counted | over water |
|---|---|---|
| planted woody stations (`noteStation`) | **391** | **0** |
| flora instances, every set in the group | **1,024** | **0** |
| far-timber polyline samples at 2 m | **6,527 in-box of 6,664** | **47** |

Counted in the browser, on the published mirror, from the reported viewpoint. The two woody gates
were telling the truth about the 391 and the 1,024; the 47 is a population neither of them has a
reader for. **The Python census and the browser census agree sample for sample and to the
millimetre on every body** â€” which is the R-BUG3c-class assumption (the mask in `data/` and the mask
the page loads being the same mask) asserted rather than assumed, for the first time on this
layer.

**So nothing the two existing gates measure was ever wrong.** They were measuring the wrong
population. `"woody vegetation never occupies the river mask"` walks
`trees.group.userData.stations`, which `noteStation()` writes inside the near-field planter's 632 m
square; `"emergent flora stays within eight metres of a riverbank"` walks the flora instance
matrices, a lattice re-centred on the camera. `FAR_TIMBER` is neither: five bodies of timber the
sources put beyond the modelled town, authored as polylines and drawn as a horizon silhouette. **No
gate in this project had ever asked those polylines where they stand.** Fifth time a green gate and
the owner's screen have disagreed, and the fifth time the gate was pointed at something other than
what ships.

**The census, `tools/measure_far_timber.py`, RED on the build in the screenshot:**

| body | samples | over water | wet run | worst depth |
|---|---|---|---|---|
| `main_stem_belt_east` | 39 | **39** | **73.4 m of 73.4 m** | **3.347 m** |
| `north_branch_belt` | 2,513 | 8 | 16.0 m of 5,016.1 m | 1.380 m |
| `south_branch_belt` | 2,308 | 0 | â€” | â€” |
| `north_division_timber` | 459 | 0 | â€” | â€” |
| `south_branch_grove` | 1,345 | 0 | â€” | â€” |

`main_stem_belt_east` runs (326, 46) â†’ (396, 68). The committed `south_water` centreline is at
n â‰ˆ +7 across that reach and `north_water` at n â‰ˆ +66, so **a belt whose own note says it follows
South Water Street was authored between the two banks.** It is not a survey error at the margin: it
is on the far side of the river from the street it is named after, along its whole length.

**Three of the four candidates this box listed are REFUTED, and the fourth is not what happened.**
The row emitter does consult the mask â€” `communityAt()` refuses `terrain.isWater` outright and the
planting loop tests the exact stem point before the ecology. The space is right: everything on that
path is ENU throughout. The mask and the drawn water do not disagree here. And nothing streams past
a placement gate. **The bug was in a population nobody had listed as a suspect**, which is the
finding worth keeping: the candidate list was written from the near-field planter, because that is
where a search for "what plants things" leads, and the thing that drew these trees does not plant
anything at all.

**The fix, and it is an invariant rather than a coordinate.** `solveHorizon()` now asks
`terrain.isWater(pe, pn)` at every emitted sample and skips it. The near-field planter has refused
that mask since it was written; a stand drawn at four hundred metres makes the same claim about the
same water. It is sampled at the EMITTED point, not at the body's vertices, because a belt can cross
a channel between two dry ends â€” which is exactly what the North Branch belt does. Outside the
modelled heightfield the mask returns its fallback and answers "dry", and that is the honest answer:
this project has no survey of that ground and a clip that claimed one would be inventing it.

**What is NOT fixed, deliberately: `main_stem_belt_east` now draws NOTHING, because none of it was
on land.** *(Superseded 2026-08-27 by R-BUG5(b) below â€” the owner ruled and the belt is derived
from the street. The paragraph is kept because it is the reasoning the ruling answered.)*
Repairing it means choosing where the belt's near edge actually ran, and no source here
settles that â€” the note that produced the fault is itself this project's best current reading of
Andreas ("the South Side timber extend[ed] east as far as Wells Street"). Picking a new line to make
the census green would be inventing the very thing the measurement just showed nobody knows. So the
two offenders are **banked by name in `tools/far_timber_baseline.json`**: the fault may shrink and
may not grow, a new offender fails, and a repair that forgets to re-bank fails too. **The renderer
half is absolute and needs no baseline.**

**R-BUG5(b) â€” where the South Water Street belt stood Â· DONE 2026-08-27, T-0031, route 1.** The
owner ruled on 2026-08-17 and the belt is derived rather than authored; the box below is kept
verbatim as the question that was put to him. **What shipped:**
`tools/derive_timber_belt.py` builds the path from `data/streets/1835.json` â€” the committed
`south_water` centreline, offset **12.192 m** (half the platted 24.384 m corridor) to the SOUTH on
a mitred offset, clipped east at the **mean easting of the committed `wells` centreline, E +329.3**,
which is byte for byte the number `timberEastLimits()` gives the near planter for the same limit.
`tools/check.sh` re-derives it, so the belt cannot drift from the street it is cut from.

**The measurements.** The census went **39 of 39 samples over water, 3.347 m under the surface â†’
0 of 136**, and `main_stem_belt_east` left `far_timber_baseline.json` by the ratchet's own
third rule (a repair the baseline is not told about fails). The browser census agrees with the
Python one body for body. The belt is **265.0 m** long against the stub's 73.4 m, and every 2 m
sample stands **24â€“49 m from the water's edge** â€” inside the 30â€“74 m gallery `communityAt()` deals
from the same bank distance, so the horizon body stands on ground the near planter's own
classifier independently calls ZONE 5. **The stub was also 66.7 m east of Wells**: it was authored
on the old 640 m box's edge with Wells guessed at E +400, the same class of error K45(b2) found in
`z05_riverbank_timber`'s note, and being east of the street it was named for is the other half of
why it ended up in the channel.

**What a visitor sees.** The band drew NOTHING for eleven days. Measured through `horizonCensus()`
at three stands: the belt now wins **19 bearings at the Green Tree anchor** (73â€“80Â°, crowns to
36.6 px), **36 at Randolph and Canal** (47â€“61Â°, 37.3 px â€” the stand R-BUG5 reproduced the owner's
screenshot from) and **15 at the forks** (84â€“89Â°, 46.9 px). From the `south_water` anchor itself it
draws nothing, which is correct: standing on the belt puts it inside `MIN_FAR_M`. Frames:
`docs/evidence/t-0031-{before,after}.png` and the crop `t-0031-green-tree-crop.png`.

**One thing the ticket did not ask and a reader deserves.** Since K45(b2) the near-field planter
sweeps the whole field and ends the South Division timber at the same Wells Street, so **70 stems
already stand in this reach**. The far body is not a duplicate of them â€” it is the same
relationship `north_division_timber` has had with the ZONE 6 wood since the sweep widened: stems
near, silhouette far, one east limit. But it is worth knowing that the belt was never wholly
absent from the scene, only from the skyline.

**The three routes as they were put to the owner, kept verbatim:**
1. **Re-derive it from the committed `south_water` centreline**, south of the corridor. Mechanical,
   and the same move `south_branch_belt` already makes off the river's modern course â€” but it
   asserts which side of the street the timber stood on, which Andreas does not say.
2. **Leave it drawing nothing** and record the body as researched-but-unplaceable. Honest, and it
   loses a documented body of timber from the skyline.
3. **Withdraw the record** the way T-A16 withdrew the public square, on the grounds that a belt
   whose position cannot be derived is not a body this scene can carry.

**Files:** `renderers/web/js/trees.js` Â· `tools/measure_far_timber.py` Â·
`tools/far_timber_baseline.json` Â· `tools/smoke_renderer.mjs` Â· `tools/check.sh`

**Gates:** `tools/check.sh` runs the census and its self-test (five broken-assertion cases plus the
three ratchet directions). `smoke_renderer.mjs` asserts the browser's own census matches the banked
numbers AND that `horizonWetSkipped > 0` from a stand where the belt clears `MIN_FAR_M` â€” from the
spawn point it is **329.2 m** away against a 330 m cut-off â€” 0.8 m inside it â€” so a gate that solved
only at spawn would have exercised nothing. Measured on the shipped build from that stand:
**7 samples clipped**.


### R-G0 â€” the critic harness Â· **DONE 2026-08-14 (G0.1 + the numeric half of G0.2)**

**Phase:** RENDERING Â§4 G0 Â· **Runner:** improve-runner (no Blender) Â· **Effort:** S

Everything later measures through this, which is why it was first. One reproducible loop so a
phase proves its delta in numbers rather than adjectives.

**Shipped:** `tools/critic_shots.mjs` â€” eleven stations (the eight scene anchors, driven by
`goTo` so they cannot drift from what a visitor is offered, plus three re-established
prairie-sweep stands), both release viewports at device scale 1, the clock held from before
the render loop's second tick, the DOM chrome hidden, pitch printed and asserted per station.
`tools/critic_metrics.mjs` â€” a dependency-free PNG reader and the six Appendix B recipes, so
the SAME code can measure a reference photograph and one of our frames, which has never been
true here before. Baseline for both viewports in `docs/STATUS.md` Â§ "The critic baseline".

**Two things came out of it that are not the harness**, both recorded rather than fixed:

- **Draw calls exceed the â‰¤ 80 budget at four of the eleven stations** â€” `prairie_west` 97
  desktop / 94 mobile, `green_tree` 91/88, `forks` 87/82, `south_water` 85/83. The budget was
  only ever measured at the spawn station, where it passes at 65/62. Not a regression; a
  measurement nobody had taken. R-W5 owns the draw-call work and should take it.
- **Captures are byte-identical within a browser process and near-identical across
  processes.** Both baseline runs came out 11/11 byte-identical at both viewports, but an
  earlier pair of rounds had four desktop stations alternating between two variants differing
  in 1, 2, 11 and 43 pixels of 1,024,000 â€” on the horizon row and on alpha-blended surfaces.
  So the acceptance line "byte-stable" is now a stated stability CONTRACT in the harness
  (â‰¤ 0.05 % of pixels may differ AND every reported metric must repeat within 1 %), it is
  checked by `--stability`, and the byte-identical count is reported alongside it. See
  RENDERING Â§4 G0 for the amendment.

**Still open from G0.2:** the baseline **8-axis rubric score**. The protocol requires a critic
that did not write the code under review, and the same run cannot both build the harness and
be that critic. It is a parcel of its own â€” **R-G1** below.

**Trap (kept for the record):** the harness must use the existing `window.__chicago4d` API
(`goTo`, `setAnimationHold(true)`, `capture`) and must not add a second way to drive the
scene. It does not: non-anchor stands use the same `walker.teleport` `tools/shoot.mjs`
already uses, and nothing in `renderers/` changed.

### R-G1 â€” the baseline scored pass Â· **DONE 2026-08-14 Â· mean 4.18 of 10**

**Phase:** RENDERING Â§4 G0.2 Â· **Runner:** improve-runner Â· **Effort:** S Â· **After:** R-G0

Scored at five named stations â€” `sauganash`, `first_post_office`, `south_water`, `prairie_west`,
`river_bank` â€” desktop 1280Ã—800, against the Â§0 reference set and never against a commercial
game frame. **Mean 4.18; no axis reaches 7**, against a pass bar of mean â‰¥ 8.0 with no axis
below 7. Axis means: texture **1.4**, lighting **3.2**, material **3.6**, post **3.8**,
atmosphere **4.2**, geometry **4.6**, composition **5.8**, historical accuracy **6.8**.

**The independence condition held**: this parcel changed no code â€” three documents and a
changelog entry â€” and the run that wrote the harness was a different one. The mobile set was
captured and measured in the same run and deliberately **not** scored; six of the eleven
stations were read for context and not scored. Both facts are on the record in STATUS rather
than left to be inferred.

**Where the fixes went** â€” R-W1 (lighting, and the corrected mechanism for Â§1 item 7), R-W2
(material and texture, both halves), R-W3 (openings and the AO cage that has to carry form the
sun angle does not), R-W4 (atmosphere, the flower load, and a horizon-timber metric that cannot
tell a gable from an oak), R-W5 (post-processing and the draw-call growth), and two new lane-2
parcels, **T-V1** and **T-V2**, for the two failures that are data rather than rendering.

**Files:** `docs/STATUS.md` Â· `docs/ROADMAP.md` Â· `renderers/web/js/changelog.js` (no code)

**What it did not do:** re-anchor the Â§5 targets by measuring a reference plate through
`tools/critic_metrics.mjs`. That is still a one-line job and still not done.

### R-W1 â€” calibrated light and environment Â· **SHIPPED TO PRODUCTION 2026-08-17 ON THE OWNER'S RULING**

> ## âœ… RELEASE CONDITION â€” DISCHARGED BY THE OWNER, 2026-08-17
>
> **The condition below was put to Kevin before the promotion that carried this parcel, with the
> cost stated and three options offered â€” ship it, re-measure first, or promote without it. He
> chose to ship it.** The parcel went to production in the same promotion as K24's brightness
> slider, which is the accommodation he asked for on 2026-08-14 when he was first told this scene
> would be ~16 % dimmer.
>
> **The cost is real and is not retracted.** `south_water` 250â€“600 m fell from **71 % of probes
> perceptible to 16 %** when this landed on `dev`, and the far road down a street is a complaint
> he has raised twice. **R-W2**'s textured coverage is still the parcel that buys it back, and it
> stays #1 on the rendering lane for that reason. If a later run finds that band still dead, the
> answer is R-W2 â€” not a smaller bar, and not a revert of the light.
>
> **The figure is also older than the build it shipped in.** It was taken on `dev` at 836fa84;
> K24, the doubled shadow reach (R-W3b/R-W5a2) and R-BUG6(a)/(b) all landed after it and none was
> re-measured against this band. **Do not quote 16 % as this build's number** â€” it is the number
> this parcel cost on the day it landed. Re-read it before using it to argue anything.
>
> *Original condition, kept because the reasoning is the record:* R-W1 was not to be promoted
> until the owner had walked the `/dev/` preview and approved the look, or R-W2 had bought the
> contrast back. It was held on `dev` for exactly that purpose, and released by the first route.

**The light was wrong and this parcel is right about it.** Measured on an upward-facing white
Lambertian card, sun excluded, on the rebased branch: the old `HemisphereLight` rig put out
**1.9Ã— the luminance and ~2.9Ã— the red of the sky it was standing under**. Every calibration this
project has made â€” the sward's density, the wall colours, the crown contrast â€” was taken under a
fill that contradicted its own backdrop.

**And it is expensive, in the place that is already sore.** The scene is ~16 % dimmer, so road
contrast falls almost everywhere. Mobile, published mirror, honest denominator (R-M1c), against
`dev` at 836fa84:

| station Â· band | `dev` | R-W1 | |
|---|---|---|---|
| `south_water` 2â€“40 m | 90 % | 90 % | â€” |
| `south_water` 40â€“100 m | 87 % | 80 % | âˆ’7 |
| `south_water` 100â€“250 m | 52 % âœ— | 33 % âœ— | âˆ’19 |
| **`south_water` 250â€“600 m** | **71 % âœ“** | **16 % âœ—** | **âˆ’55** |
| `from_above` 100â€“250 m | 85 % | 78 % | âˆ’7 |
| `from_above` 250â€“600 m | 53 % âœ— | 50 % âœ— | âˆ’3 |
| `lake_market` 40â€“100 m | 100 % | 93 % | âˆ’7 |
| `lake_market` 250â€“600 m | 98 % | 100 % | +2 |

**THE SUITE REPORTS 229 / 2 BEFORE AND 229 / 2 AFTER, AND THAT IS A THIRD INSTRUMENT FINDING.**
The count is identical because `south_water` was *already* red on its 100â€“250 m band, so a band
collapsing from 71 % to 16 % **changed no verdict and appears nowhere in the summary**. A
station-level check hides a band-level regression, and a reader comparing tallies would conclude
this parcel cost nothing. Opened as **R-M1d**: the suite should report a band that moves against
its own last figure, not only a station that crosses a bar.

**What it buys, and this is real too.** Literal black pixels go to zero at all three metric
stations â€” `river_bank` **12,063 â†’ 0**, `first_post_office` **11,015 â†’ 0**, `prairie_south`
**2,315 â†’ 0** â€” and the decile L\* rises everywhere, nearly doubling at `river_bank` (0.93 â†’ 1.78).
Â§1 item 11 is retired and item 7's "no literal (0,0,0)" half with it.

**The sequencing conclusion, stated because it is the actual answer:** R-W1 is **correct and
premature**. It belongs *with or after* **R-W2**'s textured coverage, which is the parcel that buys
the contrast back. Landing it before R-W2 trades a documented, owner-reported defect for a
less-visible correctness win. It is on `dev` and not in production precisely so that trade is
visible to the person entitled to make it.

Everything below is the parcel as written on 2026-08-14, kept because it records the reasoning;
the branch has been rebased onto `dev` and its figures re-measured above.

**What shipped on the branch.** `scene.environment` is a PMREM of the calibrated sky **with
a ground half in it**, and the ground half is the finding: an analytic sky model is defined
over the whole sphere, so a sky-only environment paints the ground blue and lights every
downward-facing surface in the town with sky from below. That is what "swamped albedo" in
the 2026-08 attempt this file records. The ground half's radiance is DERIVED â€”
`reflectance x E_horizontal / PI`, with the reflectance the dun the hemisphere light already
carried as its ground colour, read as what its numbers already are (a 15 % reflector). No
new constant, and the bounce is finally tied to how much light is falling on the ground it
is bouncing off. The hemisphere lights are gone.

**THE FINDING, and it outlives the parcel: the old fill was not the sky.** Measured with the
new instrument, the `HemisphereLight(0xa8c4e0, 0x7a6b4e, 2.4)` rig delivered **1.86x the
luminance and 2.85x the red** of the very sky this project calibrated against a verified
photograph. The town was lit by a sky that does not exist, at an exposure set for one that
does, and every calibration since â€” the sward's density, the wall colours, the crown
contrast â€” was measured under it.

**Measured, desktop, at the three worst stations** (`node tools/critic_shots.mjs --metrics
--stations river_bank,first_post_office,prairie_south`):

| station | literal black px | decile L\* | crown Gâˆ’B |
|---|---|---|---|
| `river_bank` | 12,063 â†’ **0** | 0.93 â†’ 1.78 | 47.8 â†’ 33.7 |
| `first_post_office` | 11,015 â†’ **0** | 5.35 â†’ 6.20 | 12.2 â†’ 15.7 |
| `prairie_south` | 2,315 â†’ **0** | 7.09 â†’ 7.97 | 19.9 â†’ 10.7 |

So **Â§1 item 11 is retired** (an environment is installed and it does not override albedo),
**item 7's "no literal (0,0,0)" half is retired**, and **item 8 holds** â€” every station stays
over the â‰¥ +10 crown target. Fill on downward-facing surfaces is up 30 %.

**What did NOT clear, with the arithmetic rather than an excuse.** The decile target of
L\* â‰¥ 14 is not reachable by lighting and the numbers say why. An interior crown vertex
carries `CROWN_SHADE_FLOOR = 0.060` folded into its own vertex colour, so its albedo is the
record's foliage green times 0.06 â€” **0.24 % reflectance, darker than charcoal**. Even at a
floor of 1.0, i.e. no self-shadowing at all, that surface reaches only L\* â‰ˆ 12 under this
rig. R-G1 was right that the metric reads canopy rather than shadow; what this parcel adds is
that the canopy is dark in the ALBEDO, where no environment can reach it. **The next lever is
`CROWN_SHADE_FLOOR` in `trees.js`, and it is a separate calibration** â€” the constant's own
committed check is the Weber contrast the reference photograph's tree mass holds (0.625,
against 0.655 here), so raising it has to be paid for there and not smuggled through a
lighting parcel.

**WHY IT IS PARKED â€” one real regression, named.** `tools/smoke_renderer.mjs` reports **403
passed, 4 failed**; three were an unstamped changelog and are fixed. The fourth is
**`the roads reach the screen from the air, at the aerial anchor`** â€” R-BUG2's own gate,
added yesterday, which requires Î”L\* â‰¥ 1.8 and â‰¥ 55 % of probes perceptible. `south_water`
still passes; only the aerial band fails. **Do not weaken it.** Two candidates worth
separating before touching anything: the scene is 16 % dimmer overall, and the environment
adds an indirect specular term to the terrain that is near-uniform across road and grass and
therefore compresses their ratio. The second would be the more interesting fault and is
testable on its own â€” the roads were tuned yesterday under the brighter rig, so a re-tune may
be owed, but it belongs to whichever parcel proves which cause it is.

**A note on the plan this deviates from.** RENDERING Â§4 W1 asks for `tools/gen_sky_env.py`
and a committed `.hdr` loaded through a vendored `RGBELoader`. That was not built, on purpose:
the sky in this renderer is already fitted to a verified photograph inside its own shader
(SKY_EXPOSURE, HORIZON_RESTORE), so a Python re-implementation would be a SECOND sky that must
be kept in step with the first, and RENDERING's own acceptance asks the environment and the
backdrop to agree in hue at the horizon. A PMREM of the shader agrees by construction. No
binary asset, no vendor change, no licence entry. **This is a proposal, not a settled
amendment** â€” RENDERING Â§4 W1 still reads as written and the owner may prefer the .hdr.

**Files on the branch:** `renderers/web/js/world.js` Â· `renderers/web/js/flora.js` (reads the
fill from `scene.userData.chiSkyFill`, because a Lambert material cannot see
`scene.environment` and the sward would otherwise have kept a fill the town no longer has) Â·
`tools/light_probe.mjs` (new) Â· `tools/critic_shots.mjs` (`--stations`) Â·
`renderers/web/js/changelog.js` Â· `site/chicago/4d/` Â· `docs/`

**Phase:** RENDERING Â§4 W1 Â· **Runner:** improve-runner Â· **Effort:** M Â· **After:** R-G0

Retires RENDERING Â§1 items 7, 8 and 11.

**Files:** `tools/gen_sky_env.py` (new) Â· `assets/env/` (new, with `assets/LICENSES.md`) Â·
`renderers/web/js/world.js` Â· `renderers/web/vendor/MANIFEST` (+ `RGBELoader`) Â·
`tools/smoke_renderer.mjs`

**Acceptance (RENDERING Â§5):** shadowed darkest decile **L â‰¥ 14**, no literal `(0,0,0)`;
sunlit crown **Gâˆ’B â‰¥ +10**; a documented white wall reads white and a brown log wall keeps
**R/B â‰ˆ 1.75** (measured 1.08 at the failure). Sun disc EXCLUDED from the HDRI â€” the direct
sun stays on the directional light; `world.js` documents why a five-figure-radiance disc
destroys the PMREM.

**Trap:** this is the change that failed before. Tune environment intensity until materials
keep their hue, THEN rebalance the hemisphere fill and ground bounce DOWN â€” otherwise total
illuminance doubles instead of being redistributed.

**From R-G1 (scored 3.2, the second-worst axis) â€” the acceptance number needs re-reading before
you start.** "No literal `(0,0,0)`" and "darkest decile L â‰¥ 14" were both written believing they
measured shadow. They do not, at any station measured: 94â€“100 % of the literal-black pixels lie
in connected components entirely above the median land/sky row, on the shaded side of the near
canopy, and the darkest-decile metric reaches the same pixels because its per-column "ground"
begins at the top of a crown. **Raising a shadow floor moves neither number.** What lights a leaf
facing away from the sun is the environment term this parcel installs â€” so the two numbers are
still W1's to earn, by the IBL rather than by the shadow path, plus a floor on the crown's
darkest albedo if the IBL alone does not clear it. Verify by locating the dark pixels â€” connected
components and their bounding boxes against the land/sky row â€” and not by the aggregate alone: an
aggregate that moves for the wrong reason is how this got mis-stated once already. Second, the
sun stands **70.5Â°** up at the scene's 12:30 and a
shadow is 0.354 Ã— the height of what casts it, so the frame carries almost no shadow information
and form must come from the IBL and from W3's AO â€” the hour is a recorded, reasoned choice and
this is not an argument to move it, but W1 should not expect the shadow map to help it.

### R-W4 â€” atmosphere and the mid-field Â· **SPLIT FOUR WAYS â€” claim ONE**

> **R-W4a is DONE 2026-08-15** â€” the metric counted the town's roofs as timber, the
> discriminator this entry named was measured and REFUTED, and the figure it was replaced with
> cannot move when a block lands. Findings and the corrected table under R-W4a below.
> R-W4b/c/d are free and now have a number they can trust.

**Phase:** RENDERING Â§4 W4 Â· **Runner:** improve-runner Â· **After:** R-G0

The largest single visual gap: RENDERING Â§1 items 1â€“6. **It was tagged L and that is why it is
split** â€” the run budget is 150 minutes and one smoke pass is 26 of them (see the budget section
at the top). Each half below is one coherent change with one smoke.

| | parcel | why it stands alone |
|---|---|---|
| ~~**R-W4a**~~ | ~~fix the horizon-timber metric~~ Â· **DONE 2026-08-15** | The headline figure counted gable ends as trees and the acceptance number was unmeasurable. It is measurable now, and it is much worse than it read. Findings below. |
| ~~**R-W4b**~~ | ~~the ring seam~~ Â· **ALREADY SHIPPED 2026-08-13 (PR #95) â€” NOT A PICK.** Noticed 2026-08-17 by R-BUG6(a) while choosing a parcel: every lattice slot has carried its own outer radius since that commit (`fringeOf`, `LOBE_M`, `TUNE.mid.fringe = 3.0`), the spread went **1.4 px â†’ 5.9 px** at 1280Ã—800 and 17.4 px at 390Ã—780, and a gate holds it. **This row stayed pickable for four days and cost this run part of its budget** â€” see `docs/STATUS.md` Â§ *the sward ended on a straight line*. | 
| ~~**R-W4c**~~ | ~~flower load~~ Â· **(a) and (b1) DONE 2026-08-15, (b2) IS THE TUNING HALF** | `0.0012` was not a count of flowers: the recipe's hue cut at 50Â° runs through the middle of a July prairie's bloom and misses **94.5 %** of it. The render's true bloom at `prairie_west` is **2.19 %**, not 0.12 %. **And there is no 4â€“6 % target to tune to** â€” R-W4c(b1) found it unsourced on one half and unreproducible on the other. Findings under R-W4c(a) and R-W4c(b1) below â€” **read both before quoting any flower number, and before tuning anything**. |
| **R-W4d** | **the mid-field itself** | Vegetated pixels to the fog-90 % distance, crown fine-detail â‰¥ 0.6, depth-band high-pass RMS. The bulk, and the part that genuinely needs the others' numbers to be trustworthy first. |

**R-W4a is not bookkeeping.** A town parcel has already handed W4 a pass it did not earn, and
the same thing will happen again on every block that lands. Fixing the metric before chasing the
number is the difference between improving the scene and improving the score.

**Files:** `renderers/web/js/flora.js` Â· `renderers/web/js/trees.js` Â·
`renderers/web/js/world.js` (horizon band) Â· `data/flora/` (tuning only) Â·
`tools/smoke_renderer.mjs`

**Acceptance (RENDERING Â§5):** vegetated pixels present to the fog-90 % distance; horizon
timber column coverage **â‰¥ 90 %** â€” quoted from `horizonTimber.timberOnly.coverageAll` and
never from `coverageAll`, which counts roofs (R-W4a); crown fine-detail ratio **â‰¥ 0.6**; depth-band high-pass
RMS non-collapsing, far band **â‰¥ 0.75Ã—** reference; flower load **4â€“6 %** â€” quoted from
`flower.bloom` and never from `flower.load`, which counts a yellow coneflower as grass
(R-W4c(a)), and against a target R-W4c(b) must re-derive before it compares the two; the ring seam gone
(no constant screen row across all columns). Fog still total by 1500 m (**L17**), and
`HAZE_MAX = 0.82` on the horizon band is **L35** â€” a technique that changes what either
claims gets an appended **Revised** line in `docs/LIBERTIES.md` in the same PR.

**Trap:** the ring seam is a circle of constant radius drawn on flat ground, which is why it
lands on one screen row. Varying the radius per patch is the fix that worked for the sward;
the same shape of fix is wanted here, not a bigger radius.

**From R-G1 (scored 4.2) â€” the â‰¥ 90 % horizon-timber target does not currently measure timber.**
The recipe counts a column as timbered if any pixel in the band above the land/sky line falls
3 luma below, or 3 Gâˆ’B above, the sky extrapolated from the 20 rows over it. A gable end breaking
the skyline satisfies that as surely as an oak, and it has already happened: with **no renderer
change** between two runs (`git diff --stat 282dd9a..HEAD -- renderers/` is `changelog.js` and
nothing else), `prairie_south` moved **0.364 â†’ 0.436** all and **0.340 â†’ 0.441** centre on the
strength of 19 new anonymous roofs, whose grey gable ends occupy the left third of that station's
skyline. **A town-completion parcel can therefore hand W4 a pass it did not earn.** Before the
acceptance number is quoted again, either the metric excludes columns carrying a structure
silhouette or a second figure reports timber-only coverage; the crown-hue channel the recipe
already computes (Gâˆ’B) is the obvious discriminator, since a whitewashed gable is not green.
Two further reads from the scored pass: the sky is a single cloudless gradient at all five
stations, and the flower load at `prairie_west` is **0.0012** against the honest 4â€“6 % target â€”
the largest single accuracy deduction on the historical axis outside the town itself.

#### R-W4a â€” DONE 2026-08-15 Â· the horizon metric was scoring the town, and the discriminator this entry named does not work

**What it was.** `critic_metrics.mjs` counted a horizon column as timbered if anything broke the
skyline in the band above the land/sky line. A gable end does that as surely as an oak, so the
figure rose when the town grew â€” R-G1 measured `prairie_south` moving 0.364 â†’ 0.436 on nineteen
new roofs with no renderer change â€” and 399 roofs were still to come.

**The named discriminator was refuted before anything was built.** This entry proposed the Gâˆ’B
channel, "since a whitewashed gable is not green". Measured on the 2026-08-15 `dev` build,
desktop, at the first hit pixel of every broken column: the grey gables at `prairie_south` sit at
**Î”Gâˆ’B +22.4** and hazed timber at `prairie_west` ranges **+0.1 to +17.5**. The populations
overlap completely, because the sky near the horizon is strongly blue-dominant and *every*
non-sky pixel clears a +3 Gâˆ’B test by a wide margin â€” the channel is a not-sky detector, and
`coverageAll` was reading the same thing twice. **No colour test can work here in principle**:
L17 makes extinction total by 1500 m, so distant timber and a distant wall converge on the fog
colour. The atmosphere destroys the evidence the discriminator needs, correctly.

**What was done instead â€” subtraction, not a heuristic.** `critic_shots.mjs` photographs each
station twice from the identical pose: once as the visitor sees it, and once with the
`structures` group's `visible` flag down. `measure()` runs the same recipe on both. The second
frame's coverage is timber by construction â€” no threshold, no hue, nothing to tune â€” and it
**cannot move when a block lands**. The old number is kept, unchanged in value and computed
exactly as before, under a name that says what it counts (skyline breaks), so the 2026-08-14
baseline stays comparable.

**The corrected table â€” source tree, 2026-08-15 `dev`, both viewports, 11 stations.** `breaks` is
the old figure; `timber` is the honest one; `town` is the share of the old figure that was roofs.

| station | dsk breaks | dsk **timber** | dsk town | mob breaks | mob **timber** | mob town |
|---|---|---|---|---|---|---|
| `sauganash` | 0.638 | **0.477** | 29 % | 0.756 | **0.574** | 33 % |
| `sauganash_wing` | 0.518 | **0.492** | 20 % | 0.636 | **0.636** | 16 % |
| `lake_market` | 0.532 | **0.534** | 16 % | 0.697 | **0.597** | 24 % |
| `first_post_office` | 0.847 | **0.751** | 12 % | 0.919 | **0.698** | 24 % |
| `forks` | 0.738 | **0.651** | 25 % | 0.749 | **0.818** | 16 % |
| `green_tree` | 0.737 | **0.745** | 9 % | 0.762 | **0.797** | 3 % |
| `south_water` | 0.889 | **0.706** | 25 % | 0.836 | **0.362** | 58 % |
| `from_above` | 0.212 | **0.212** | 0 % | 0.156 | **0.156** | 0 % |
| `prairie_south` | 0.632 | **0.295** | **62 %** | 0.682 | **0.403** | 49 % |
| `prairie_west` | 0.830 | **0.894** | 5 % | 0.669 | **0.639** | 21 % |
| `river_bank` | 0.641 | **0.651** | 1 % | 0.713 | **0.713** | 0 % |

**Three things in that table are worth reading before quoting it:**

- **The worst overstatement is `prairie_south`, where 62 % of the "timber" was the town** â€” 409
  of 1053 measured columns broke the skyline on a roof and on nothing else. The station R-G1 used
  to demonstrate the fault is the station the fault was worst at, which is the fault being
  self-consistent rather than a coincidence.
- **The correction runs the OTHER way at six of the twenty-two station-viewports** (`green_tree`,
  `lake_market`, `prairie_west` desktop, `forks` mobile, `river_bank`), because a building can
  stand in front of timber and hide it. This is the figure answering "is the horizon timbered",
  not "can the visitor see timber past the town" â€” the right question for a target derived from
  photographs of a treeline, and it is stated here so nobody reads a rise as an improvement.
- **Nought of twenty-two station-viewports meet the â‰¥ 90 % target on the honest figure**, against
  one on the old one. Mean 0.582 against 0.672. **R-W4d inherits a bigger gap than it was
  promised**, and `from_above` (0.212 / 0.156, town share 0 %) is an aerial pose whose band is
  not a horizon at all â€” do not average it in without saying so.

**Cost, measured.** The full 11-station both-viewport `--metrics` run took **13 min 12 s** with
the second capture, against the ~12 min the budget section quotes without it; on a 3-station
desktop A/B it went 2 min 03 s â†’ 2 min 58 s, most of the fixed cost being the page load the two
share. `--no-mask` opts out and says so in the header.

**Putting the town back leaves the frame alone, measured rather than assumed.** The visitor's
screenshot is taken BEFORE the toggle, so a station's own frame cannot be affected by it; the
question is whether the NEXT station's is. Same three stations before and after the change, in
separate browser processes: **5, 9 and 51 differing pixels of 1,024,000** (â‰¤ 0.005 %), inside the
harness's own documented cross-process residual of 1â€“43 px and far under its 0.05 % ceiling. The
`--stability` contract passes with the second capture in it, byte-identical at both stations
tested, worst metric drift **0**.

**And a doc claim was found false while using it.** The budget section has told every run since
2026-08-14 to use `critic_shots.mjs --stations a,b,c` for a 3-minute run instead of 12. **That
flag did not exist**, so every run that followed the advice ran the full set. It exists now.

#### R-W4c(a) â€” DONE 2026-08-15 Â· the flower metric cannot see most of a flower, and the gap it reported is 18Ã— too big

**What it was.** R-G1 measured a flower load of `0.0012` at `prairie_west` against a 4â€“6 %
target and this file called it "an under-representation of a July prairie by two orders of
magnitude". The recipe sorts every ground pixel into *plant* or *flower*, and it applies the
plant test first: `hue âˆˆ [50Â°, 180Â°)` with any chroma at all is plant. **No yellow-through-cyan
pixel can therefore ever be a flower, however brilliant it is** â€” and the headline colour of a
July prairie is the yellow composite.

**The cut runs through the bloom it is sorting, and this project's own records straddle it.**
Measured on the committed `data/flora/zones/` inflorescence colours:

| record | rgb | hue | counted as |
|---|---|---|---|
| `silphium_laciniatum` | 228, 200, 62 | **49.880** | flower |
| `ratibida_pinnata` | 232, 206, 72 | **50.250** | **the grass it is compared against** |
| `opuntia_humifusa` | 236, 208, 72 | 49.756 | flower |
| `nuphar_advena` | 230, 206, 80 | 50.400 | **plant** |

Two yellow composites 0.37Â° apart land on opposite sides, and nobody looking at the frame could
tell the pair apart. Of the **97** inflorescence colours in the zone records, **52 are called
plant, 26 are called neither** â€” dropped from *both* sides of the ratio, which is where the
saturated dark purples go (`liatris_pycnostachya`, `vernonia_fasciculata`, `dalea_purpurea`,
`pontederia_cordata`) â€” and only **19 are called flower**.

**So the harness was made to take the flowers away, the same subtraction R-W4a used for the
town.** `critic_shots.mjs` photographs each station a third time with the nine `flora-head-*`
instanced sets hidden; every ground pixel that moved is a pixel a flower head painted, by
construction â€” no hue, no colour threshold, nothing that moves when the palette is re-tuned.
The heads cast no shadow (`flora.js` sets `castShadow = false` on every set), so hiding them
cannot change a pixel they did not cover. Both frames are read over the **visitor frame's**
ground line, so a scape breaking the skyline cannot move the boundary and count its own removal.

**The measurement â€” source tree, 2026-08-15 `dev`, desktop, the three prairie stations.**

| station | recipe `load` | **true bloom** (of hued ground) | of ground | bloom px | recipe **recall** | recipe **precision** |
|---|---|---|---|---|---|---|
| `prairie_west` | 0.0012 | **0.0219** | 0.0202 | 10,843 | **0.055** | 0.998 |
| `prairie_south` | 0.0024 | **0.0187** | 0.0107 | 9,137 | **0.128** | 0.996 |
| `river_bank` | 0.0022 | **0.0076** | 0.0057 | 4,131 | **0.284** | 1.000 |

**Where the missing bloom goes, in-frame â€” this is the whole finding.** Of the 10,843 pixels a
flower actually painted at `prairie_west`: **5.5 % are called flower, 69.7 % are called PLANT,
24.9 % are called neither.** The recipe does not merely miss them â€” a bloom pixel called plant
is subtracted from the numerator **and added to the denominator**, so the ratio is pushed down
twice by the same pixel. Precision runs the other way and is near-perfect (0.998): almost
everything it *does* call a flower is one. It is not over-counting. It is blind.

**Three things follow, and two of them are corrections to this project's own claims.**

- **"Two orders of magnitude" is wrong and is corrected wherever it appears.** The render's
  bloom at `prairie_west` is **2.19 %**, not 0.12 %. Against a 4â€“6 % target that is a factor of
  about two to three â€” a real gap, worth R-W4c(b), and **eighteen times smaller than the one
  this file has been quoting**. A parcel sized against the old figure would have been sized
  against a measurement error.
- **NEITHER COMPARISON WITH THE 4â€“6 % TARGET IS SOUND YET, AND R-W4c(b) MUST NOT BE ACCEPTED ON
  ONE.** That target was derived by running *this same recipe* on the reference photographs
  (STATUS Â§00: planting 12.91 %, virgin remnant 1.79â€“5.54 %). So `0.0012` vs 4â€“6 % is
  recipe-against-recipe, which is at least consistent in method but reads a number that is
  94.5 % blind on our side and blind by an unmeasured amount on the photograph's; and 2.19 % vs
  4â€“6 % compares a true count against a blind one. A photograph has no second frame, so its
  bloom **cannot** be measured by subtraction. **Re-deriving the target with a method of known
  recall is R-W4c(b)'s first job, before it tunes anything** â€” otherwise the tuning half will
  chase a bar that was never on this scale.
- **What (a) does give (b) is an exact baseline.** Whatever `data/flora/` or `flora.js` is
  changed to, the bloom it paints is now countable to the pixel and the count cannot be gamed by
  a palette shift. That is the point of landing the measurement before the fix, and it is why
  the parcel was split.

**The one limit of the figure, checked rather than waved at.** It counts head pixels **over
ground only**, because that is `load`'s denominator. A head silhouetted against the sky is
therefore outside it. Measured whole-frame against ground-only: `prairie_west` 10,873 vs 10,843
(**30 px**, 0.3 %), `prairie_south` 9,137 vs 9,137 (**0**), `river_bank` 4,240 vs 4,131
(**109 px**). The restriction costs essentially nothing at these stations and the figure is a
floor, not an estimate.

**Cost, measured.** Three desktop stations with all three captures: **3 min 45 s**, against the
2 min 58 s R-W4a measured for the same three with two captures. The third capture is frames, not
a page load, and `--no-mask` still opts out of both.

**`flower.load` is unchanged in name and in value**, exactly as `coverageAll` was kept by R-W4a,
so the 2026-08-14 baseline and the photograph-derived target stay comparable to themselves. The
new reading is `flower.bloom`, and it is `null` for a reference photograph the same way
`timberOnly` is.

#### R-W4c(b1) â€” DONE 2026-08-15 Â· there is no 4â€“6 % target: half of it is unsourced, half does not reproduce, and the instrument cannot be repaired

**What it was.** R-W4c(a) ruled that the tuning half's *first* job is to re-derive the 4â€“6 %
flower-load target "with a method of known recall, before it tunes anything â€” otherwise the
tuning half will chase a bar that was never on this scale". That is a whole parcel, so it was
split off as (b1). **The answer is that the target cannot be re-derived from anything in this
repository, and the instrument that produced it cannot be fixed by the repair its own diagnosis
implies.** Every figure below comes out of `node tools/measure_bloom_target.mjs`, which is
committed; `--assert` holds the inputs to the numbers quoted here.

The target's stated derivation (STATUS Â§00, from the 2026-08-10 prairie sweep) has two clauses:
the recipe read **12.91 %** on a restoration planting and **1.79â€“5.54 %** on a never-plowed
remnant, so the honest bar for unmanaged 1835 prairie is 4â€“6 %. Both clauses were checked.

**1 Â· THE REMNANT HALF IS UNSOURCED.** There is **no never-plowed remnant photograph in this
repository and no source record describing one.** Three photographs are committed: the DuPage
restoration planting, a September 2017 Kansas trail, and the owner's sagebrush two-track. The
phrase "never-plowed remnant" occurs exactly **once** in `data/sources/` â€” inside the record of
the DuPage planting, the photograph that is *not* the remnant, and the same record that forbids
quoting that photograph for this number. It cites nothing. So the entire lower reference of the
target, and therefore the "4â€“6 %" that was set below the planting's reading on the strength of
it, rests on a measurement no reader can check. **That is precisely the failure `AGENTS.md` rule
1 exists to prevent**, reached not by inventing a citation but by carrying a number forward until
its source was forgotten.

**2 Â· THE PLANTING HALF DOES NOT REPRODUCE.** The committed recipe on the committed photograph:

| what was measured | flower load |
|---|---|
| the full frame, 4032Ã—3024 | **5.54 %** |
| the nearest quarter | 7.02 % |
| the nearer half | 6.69 % |
| the full frame, flower test first (the Â§3 repair) | 25.82 % |

**12.91 % is not there** â€” not on the full frame, not on a nearer crop, and not under either
ordering of the recipe's two tests. The one candidate cause with a motive was tested and
**refuted**: the render reads 12.93 % under the reversed ordering, a hair from the missing
12.91 %, so the obvious explanation is that the sweep's uncommitted harness ordered its tests the
other way â€” but that ordering reads 25.82 % on the photograph, not 12.91 %. The near-match at
12.9 % is between two different images and means nothing.

**And 5.54 % is, to the digit, the figure this project attributes to the never-plowed remnant it
has no photograph of.** That coincidence is recorded and not explained. It is not built on
anywhere below.

**3 Â· THE INSTRUMENT CANNOT BE REPAIRED BY THE OBVIOUS FIX, and R-W4c(a)'s precision finding
needs a correction.** R-W4c(a) diagnosed the bug exactly â€” the plant test runs first and swallows
every yellow-through-cyan pixel â€” and the repair that diagnosis implies is to run the flower test
first. Scored against the same subtraction ground truth, on the same frames:

| station | instrument | load | recall | precision | bloom / ground |
|---|---|---|---|---|---|
| `prairie_west` | committed | 0.12 % | 0.055 | **0.998** | 2.02 % |
| `prairie_west` | flower test first | 12.93 % | 0.367 | **0.062** | |
| `prairie_south` | committed | 0.30 % | 0.128 | 0.801 | 1.07 % |
| `prairie_south` | flower test first | 3.60 % | 0.305 | 0.159 | |
| `river_bank` | committed | 0.22 % | 0.284 | 1.000 | 0.57 % |
| `river_bank` | flower test first | 27.65 % | 0.525 | 0.014 | |

Recall roughly sextuples and **precision collapses by sixteen times**. Reordered, the recipe calls
**12.93 %** of `prairie_west`'s ground a flower where a flower painted **2.02 %** of it.

So R-W4c(a)'s reading of the precision figure â€” *"almost everything it does call a flower is one.
It is not over-counting. It is blind"* â€” was true of the recipe as a whole and **wrong about
which half of it was working**. The near-perfect 0.998 was the plant test's pre-filter, not the
flower test's discrimination: the flower test is "saturated and light, or white and light", which
in a July prairie is *sunlit grass*. It cannot see a flower either. Ordering is not the whole bug,
and there is no repair here that a re-read of the photograph could be trusted to.

(The last column is `bloom.shareOfGround`. R-W4c(a)'s headline **2.19 %** is `shareOfHued`, over
the smaller denominator `load` uses. Both are in the metrics and they are not the same number â€”
quote which one you mean.)

**4 Â· THE BAR THAT DOES EXIST, and it needs neither a classifier nor a photograph.** Every
flowering forb in `data/flora/zones/` carries a sourced `density_per_ha` and a sourced
inflorescence `size_m`. Heads as discs of diameter `size_m`, that is a bloom fraction **in plan**,
by arithmetic, from committed records:

| zone | bloom in plan | species with a density / stated by cover instead |
|---|---|---|
| `z01_wet_prairie` | **0.097 â€“ 1.064 %** | 9 / 2 |
| `z02_mesic_prairie` | **0.027 â€“ 0.219 %** | 11 / 0 |
| `z09_sand_prairie` | 0.004 â€“ 0.044 % | 5 / 0 |
| `z03_sedge_meadow` | 0.016 â€“ 0.140 % | 2 / 6 |

**This is not a target and must not be quoted as one.** It is a *plan* fraction and `load`,
`bloom` and the photograph are all *screen-space* readings at an oblique pose â€” a head is seen
frontally from an eye at 1.6 m while the ground it stands on is foreshortened to nothing, so the
screen figure is expected to be much the larger. The conversion is not attempted here.

What it does settle is **where a bloom change lives**. `flora.js` plants the forb layer at "the
zone's OWN summed `density_per_ha`" (`flora.js:644`, weight at `:1089`), subject to a lattice cap.
So the bloom a visitor sees is generated from sourced record fields, and **raising it is a DATA
change requiring source support â€” not a renderer knob and not a palette tune.** Whether the
realised density matches the specified one is *not* measured here and is named as open work below.

**WHAT R-W4c(b2) MUST NOT DO.** It must not tune against 4â€“6 % (unsourced and unreproducible), it
must not tune against `flower.load` (recall 0.055), and it must not "fix" the recipe by reordering
it (precision 0.062). The honest reading is `bloom.shareOfHued` / `bloom.shareOfGround`, which has
no classifier on either side â€” and **it has no target**. Three routes out, for the owner to choose
between rather than an agent to pick:

- **commit a never-plowed July remnant photograph** with rights cleared the way
  `saari_2018_dupage_tallgrass` and `samstone_2017_tallgrass_trail` were on 2026-08-15 (Commons
  API, SHA-1 checked against the file page), and derive a bar from it by a *stated* method. Note
  that a photograph has no second frame, so its bloom cannot be measured by subtraction and any
  method used on it will have unmeasured recall â€” this route buys a source, not an instrument.
- **derive the bar from the flora records** by building the planâ†’screen conversion the table
  above deliberately skips. This is the only route that ends in a number the project can
  re-derive by command, and it is a real parcel, not a line of arithmetic.
- **decide the bloom is not gated on a number at all** and retire the 4â€“6 % figure from STATUS,
  RENDERING Â§4 and this file rather than leaving it to be quoted again. It has been quoted five
  times in three documents while resting on the two clauses above.

**Cost, measured.** The whole parcel: one 3-station desktop capture at **4 min 02 s**, and 19 s
for `measure_bloom_target.mjs` (of which Â§2 is 4032Ã—3024 pixels twice). No renderer file changed,
so no bake and no new geometry.

#### R-W4c(b2) â€” DONE 2026-08-27 as T-0034 Â· there was no target, but there was a CEILING, and the records were already over it

**What it was.** "Raise the bloom." R-W4c(b1) had removed the bar it was to be raised against and
left the parcel blocked on the owner with three routes in its box. The owner ruled on the ticket
instead: *"I think you can adjust that without source"* â€” the bloom may be tuned as a
**reconstructed** value, bounded, declared in `docs/LIBERTIES.md`, never promoted. So the target
was never re-derived and is not quoted below. What the run had to find was the other half of the
ticket's own title: **raising a number is only a raise if something downstream can carry it.**

**The instrument.** `tools/measure_bloom_headroom.mjs`, new, committed, `--assert`. It drives the
placer through its own entry points â€” `flora.update` with a synthetic camera, then `flora.stats`
and `flora.communities()` â€” and asks the three ceilings between `density_per_ha` and a flower on
the screen which of them binds. Two readings had to be wired for it, because they were inside the
module and unreadable from outside: `flora.stats.caps` (the ceiling beside each set's count) and
`flora.forbLattice` (the lattice geometry `forbShareOf` clamps against). **A share sitting on its
clamp had looked exactly like a share that was simply small** â€” the same blindness K55 hit when it
multiplied `z10_settled_town`'s forb density and drew the same 146 plants.

**1 Â· THE BAR IS THE LATTICE, AND IT IS 0.346 FORBS PER SQUARE METRE.** `forbShareOf` is
`min(1, density Ã— cellÂ² / perCell)`: four slots to a 3.4 m cell, one plant per slot, and not one
plant more whatever any record says. Measured on the build before the change, **six of ten forb
layers were already ON that clamp** (K58, still open) â€” for those, `density_per_ha` is a number
the renderer cannot spend and a raise applied to it draws nothing.

**2 Â· AND THE RECORDS ALREADY ASKED FOR MORE BLOOM THAN IT CAN DRAW.** Nothing had to be invented
to raise the prairie. Every abundance in `data/flora` is a *range*, the renderer had been reading
the **midpoint** â€” a figure no source states, chosen silently â€” and the top of the same range is a
reading of the same evidence:

| community | midpoint sum | recorded top | share was | share now | raise |
|---|---|---|---|---|---|
| `z02_mesic_prairie` | 0.2800 /mÂ² | **0.4080** | 0.809 | **1.000** | 1.236x |
| `z01_wet_prairie` | 0.2760 | **0.4070** | 0.798 | **1.000** | 1.254x |
| `z09_sand_prairie` | 0.0725 | **0.1140** | 0.210 | 0.329 | 1.572x |
| the other seven | â€” | â€” | 1.000 / 0 | 1.000 / 0 | **none** |

The mesic prairie's own records sum to **0.408** where the lattice carries **0.346**, so **18 % of
what the evidence asks for is clipped by a rendering constant**. The species lottery still runs on
the midpoints, so the mix of the sward did not move: only how many slots are filled. Declared as
**L182**, reconstructed tier, bounded by the records themselves â€” no species is planted denser
than its own record's larger figure.

**3 Â· WHAT A VISITOR GETS, AND THAT IT IS THE LAST OF IT.** At `prairie_west`, **206 forbs and
1,617 flower heads â†’ 256 and 1,968**, for 8,191 more sward triangles; at `prairie_south`, 125 and
949 â†’ 155 and 1,122. **Both prairies now read a share of 1.000 with no headroom left.** The next
flower on that ground needs a different lattice (K58) and not a different number, and this box is
the measurement that says so.

**4 Â· TWO FINDINGS THE RUN DID NOT CAUSE, both filed.** Standing in every community at four
bearings: `flora-head-spike` in the settled town and `flora-head-dome` in the wet woods stand at
**820 of 820** and truncate silently â€” `maybeHead` stops pushing mid-plant â€” on the build *before*
this raise as well as after (**T-0208**). And the head ring reaches **23.65 m** while the sward is
carried to **175 m** as aggregate cards that carry no head at all, so **bloom covers 1.8 % of the
ground the sward covers** (**T-0209**). That second one is the real answer to "raise the bloom"
and it is a DISTANCE, not a density: this parcel spent the whole of the lattice's remaining 24 %
and the frame past twenty-four metres did not change by a pixel.

**Cost, measured.** One browser run of `measure_bloom_headroom.mjs` at about 70 s (32 mosaic stands
plus 3 sweep poses); no bake, no new geometry files, no data record edited.

### R-W5 â€” water, post-lite, dynamic resolution Â· **SPLIT TWO WAYS â€” claim ONE**

> **R-W5a is DONE 2026-08-15** (PR on `steward/r-w5a-batch-albedo`). **R-W5b is free**, and so is
> its successor **R-W5a2** below. Read the R-W5a findings before touching `buildings.js`.

**Phase:** RENDERING Â§4 W5 Â· **Runner:** improve-runner Â· **After:** R-W5a nothing; R-W5b after R-W1

| | parcel | why it stands alone |
|---|---|---|
| **R-W5a** | **the draw-call budget and batching** | **The more urgent half, and it is not really about water at all.** R-G1 measured lane 2 adding **exactly +11 draw calls per 19 structure records**; the straight-line over the 414 roofs still to come is **+240 against a budget of 80**. This is being spent right now, every time a block lands. Independent of the water surface. |
| **R-W5b** | **the water surface, post-lite, dynamic resolution** | RENDERING Â§1 item 13, EffectComposer/SMAA. It no longer carries **R-BUG1** â€” the flickering river edge was closed on its own 2026-08-16, and it was the camera's near plane rather than the water material. Still owns `terrain.js`'s water material. |

**R-W5a is the whole queue's first parcel as of 2026-08-15, and it has NO dependency on R-W1.**
The `After: R-W1` this section carried was inherited from the unsplit parcel and is true only of
**R-W5b**, which shares tonemapping and exposure with W1's post chain. Batching touches neither.
Nothing is gained by holding it behind a parked PR, and the TOWN lane is the reason: **T-A8 and
every block after it is blocked on this budget**, and each block that lands while it is unmet
spends more of what is left. A budget met by tuning after 414 roofs have landed is a rewrite; met
now, it is a design choice. The two leads R-G1 left are in the finding below and neither has been
explained â€” start there rather than reaching for a batching library.

**Files:** `renderers/web/js/terrain.js` (water material) Â· `renderers/web/js/world.js` Â·
`renderers/web/vendor/MANIFEST` (+ EffectComposer/SMAA) Â· `tools/smoke_renderer.mjs`

**Acceptance:** RENDERING Â§1 item 13 retired; draw calls still **â‰¤ 80** in the main pass with
extra passes accounted separately; triangles within the per-tier ceilings; zero page errors
at both viewports. **R-BUG1 is DONE and was not this parcel's** â€” the flickering river edge was
the depth buffer's precision, closed 2026-08-16 with no change to the water material at all. Read
its box before reaching for a `polygonOffset` here.

**From R-G1 (scored 3.8) â€” the draw-call budget is moving away from you, and lane 2 is what
moves it.** Re-measured on the same renderer with 19 more structure records (242 â†’ 261):
**exactly +11 draw calls at seven of eleven desktop stations, exactly 0 at the other four**,
triangles up by only 244â€“562, so this is per-object cost and not geometry. Stations over the
â‰¤ 80 budget go **4 â†’ 6** desktop and **4 â†’ 5** mobile; the worst goes 97 â†’ 108. Straight-line
over the 414 roofs still to come is roughly **+240 draw calls against a budget of 80**. That is
not an argument for slowing lane 2 â€” the roofs are the product â€” it means **batching is this
parcel's first question, not its last**, and that a budget met by tuning after the fact will not
stay met overnight. Two leads: `from_above`, which sees the whole town, gained **0**, so
something already drops these objects at distance; and the +11 is suspiciously uniform across
bearings 150Â° apart, which no one has explained.

#### R-W5a â€” DONE 2026-08-15 Â· the town was paying a draw call per colour of paint

**What it was.** `buildings.js` groups the town into one `BatchedMesh` per distinct material, and
the grouping key included the material's base colour. Every one of the 47 batches in the
2026-08-15 `dev` scene was the same `MeshStandardMaterial` â€” metalness 0, **no map of any kind**,
`DoubleSide`, opaque, `alphaTest` 0, smooth-shaded. The only fields that differed were `color`
(39 distinct values across 47 batches) and `roughness` (16 values). The town was spending 47 draw
calls to render two numbers.

**What was done.** Base colour moved OUT of the key and INTO the geometry, as a per-vertex `color`
attribute filled from `material.color`, with the shared batch material left white and
`vertexColors` on. This is not an approximation: `material.color` is already in the renderer's
linear working space, three's `<color_fragment>` multiplies `diffuseColor.rgb` by the attribute
with no colour-space conversion of its own, and the confidence view's tint was **already** applied
after `<color_fragment>` â€” so the shader does the identical product in a different order. A
documented white wall still renders at the value its record claims, to the bit. Roughness and
metalness are additionally compared at three decimals, which merged two more pairs: the bespoke
masters carry `0.8999999761581421` (a float32) and the generated infill writes `0.9`, and
comparing them exactly had split the 0.90 and 0.88 buckets for no reason a visitor could see.

**The result â€” `tools/critic_shots.mjs`, source tree, both viewports, before and after on the same
`dev` at 276 structure records:**

| draw calls | `sauganash` | `s'nash_wing` | `lake_market` | `f_post_office` | `forks` | `green_tree` | `south_water` | `from_above` | `prairie_south` | `prairie_west` | `river_bank` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| desktop before | 75 | 78 | 90 | 66 | 98 | 103 | 96 | 72 | 95 | **109** | 56 |
| desktop after | 56 | 58 | 60 | 57 | 68 | 70 | 66 | 59 | 62 | **75** | 52 |
| mobile before | 72 | 74 | 78 | 60 | 82 | 99 | 94 | 72 | 93 | **106** | 49 |
| mobile after | 54 | 55 | 58 | 51 | 64 | 68 | 64 | 59 | 61 | **73** | 47 |

**Batches 47 â†’ 16. Station-viewports over the â‰¤ 80 budget: 11 of 22 â†’ 0 of 22.** The worst station
falls 109 â†’ 75 desktop and 106 â†’ 73 mobile.

**The growth term is zero, and that is the point.** R-G1's "+11 draw calls per 19 roofs" was
**11 new material GROUPS** â€” new paints, not new objects â€” which is exactly why it was uniform at
bearings 150Â° apart: the cost counts paints in frame, not buildings. A new roof of any colour now
joins an existing batch, so **T-A8 and the 399 roofs behind it cost nothing in draw calls**, and
the ~+240 extrapolation is retired rather than deferred. The one residual growth path is a NEW
ROUGHNESS from a future bespoke bake, which adds one batch and is bounded by the material palette,
not by the roof count. (`from_above` gaining 0 in R-G1 is consistent with none of those 11 paints
having an instance in that frame; it is not worth chasing now that the term is zero.)

**Two acceptance facts, measured rather than asserted:**

- **Triangles are identical to the triangle at all 22 station-viewports.** Nothing was dropped,
  culled or simplified to buy the draw calls.
- **The frames are not byte-identical, and here is exactly how far apart they are.** 2 of 22 shots
  hash the same; the rest differ on **0.013 % of pixels** â€” 15 to 487 pixels per frame, in 7 to
  195 scattered components whose largest is 56 px, lying on building silhouettes. That is depth
  ties at coincident surfaces resolving the other way under a changed draw order. Worst single
  pixel 93/255; **whole-frame mean |Î”| 0.003â€“0.005 of one 8-bit count**. No surface is repainted.

### R-W5a2 + R-W3b(a2) â€” the last 16 batches â†’ 1, and the reach it buys spent Â· **DONE 2026-08-17 â€” Â±120 m became Â±240 m at the same texel, and the batch merge is not the pixel-identical operation it was written up as**

**Phase:** RENDERING Â§4 W5 + Â§4 W3 Â· **Runner:** improve-runner Â· **Files:**
`renderers/web/js/buildings.js` (`roughnessAttribute`, `perVertexRoughness`, `materialKey`) Â·
`renderers/web/js/world.js` (`SHADOW_REACH_M`, the shadow block) Â· `tools/smoke_renderer.mjs`
(four new assertions) Â· `docs/evidence/r-w5a2-{before,after}.png` Â· `site/chicago/4d/**`.

**It was taken as ONE parcel on purpose.** R-W5a2 alone is UNSEEN by its own row and the visible-
progress cap forbade a second invisible run in four (v161 is the one). But R-W3b(a), six hours
earlier, had measured the shadow reach as **draw-call-bound** and named this parcel as what unbinds
it â€” so the batch merge is the enabler and the reach is the payoff, and shipping the enabler alone
would have been an invisible run whose whole point was the visible one it declined to take.

**Finding 1 â€” the shadow pass is where the batch count was actually being spent.** R-W5a2's box
priced the merge at "about 15 draw calls at every station", which is the COLOUR pass alone. Every
batch that enters the sun's ortho box is a second call in the shadow pass, so the true saving grows
with the reach and the town's batch count was setting how far the sun could see. Measured on the
published mirror at 1280Ã—800, at the eight scene anchors:

| anchor | dev, Â±120 m, 16 batches | this, Â±240 m, 1 batch |
|---|---|---|
| `green_tree` | **74** of 80 | **50** |
| `forks` | 73 | 47 |
| `south_water` | 69 | 41 |
| `from_above` | 69 | 44 |
| `lake_market` | 65 | 37 |
| `sauganash_wing` | 64 | 36 |
| `first_post_office` | 62 | 39 |
| `sauganash` | 61 | 34 |

**What the reach buys, counted off the DATA** the way R-W3b(a) counted it â€” each structure's
`placement.local_e/local_n`, each planted stem's own station, against the shadow camera's matrices:

| anchor | structures inside, Â±120 m | at Â±240 m | stems, Â±120 m | at Â±240 m |
|---|---|---|---|---|
| `green_tree` | 27 of 331 | **49** | 0 of 730 | **70** |
| `south_water` | 26 | **91** | 54 | **239** |
| `forks` | 16 | **46** | 17 | **151** |

**Â±240 and not more, and this time the ceiling is resolution rather than calls.** 4096Â² over a
480 m box is **11.7 cm per texel** â€” the same figure this rig has resolved since R-W3b(a), and the
2048Â² phone map holds **23.4 cm**, likewise unchanged. Â±360 m would need 6144Â² to hold that, or it
buys reach by blurring the eave shadow a visitor is standing under, which is the trade R-W3b(a)
refused. The route past here is **R-W3b(b)**, true cascades, and it is now a resolution parcel
rather than a budget one: at Â±240 m the worst anchor sits **30 calls under budget**, where before
this it sat 6.

**FINDING 2, AND IT IS THE ONE TO CARRY FORWARD â€” a batch merge is not pixel-identical, and
R-W5a's acceptance could not have seen why.** The acceptance both halves of R-W5a inherit is
"whole-frame mean |Î”| under 0.01 of an 8-bit count", and this passes it four times over at
**0.0024**. But the mean is the wrong statistic for this operation: shot at seven poses, 1280Ã—800,
**942 pixels of 7,168,000 changed, and the worst of them by 90 counts** â€” a whole surface, not a
rounding. They are scattered singletons over roofs and wall junctions, and the cause is that
merging sixteen batches into one **reorders the submission of co-planar triangles that were tying
in the depth buffer**, so the tie resolves the other way. That is **R-BUG6's** exact class of defect
(*"something in the frame is decided by a tie, and the tie is not stable"*), reached from a
direction R-BUG6 did not consider: a batching change can move a tie without touching a material, a
bias or a near plane. **The generalisation: an acceptance stated as a frame MEAN cannot distinguish
"nothing changed" from "a few hundred pixels changed completely", and the second is what a
reordering does.** A merge parcel owes a changed-pixel COUNT and a worst-pixel figure beside the
mean, which is what this box quotes and what R-W5a's does not.

**Why the per-vertex substitution is exact where it is exact, and it is not an argument, it is
6,999,058 pixels.** Roughness is written once per vertex from the source material, so all three
vertices of any triangle carry the identical float â€” a triangle never spans two source meshes â€” and
the interpolation of three equal values is that value. `perVertexRoughness` replaces
`#include <roughnessmap_fragment>` with `float roughnessFactor = vChiRough;`, which is that chunk
verbatim minus a `USE_ROUGHNESSMAP` branch no asset in this dataset takes (R-W2a: 1,353 material
slots, **zero** textures). If the substitution had silently failed, the whole town would have
rendered at ONE roughness and millions of pixels would have moved; 6,999,058 of 7,168,000 are
identical to the byte, which is a stronger proof than any assertion.

**The gate, and it is R-A1's shape.** Four assertions, of which the first two would pass identically
on a town that merged its batches by throwing roughness away â€” one batch, one sheen, every wall the
same â€” so the third is the one that does the work: the town is **1** batch; the merged batch still
carries **16** distinct roughness values spanning **0.25â€“0.98**; driving every vertex to 0.02 moves
the worst 48Â² cell by **13** (floor 4, a third of the reading, measured before it was set); and
restoring the channel returns the frame with residual **0**. `STRUCTURE_BATCHES = 1` is asserted as
an equality rather than a ceiling deliberately: a textured asset would legitimately raise it, and
raising it should be an edit with a reach measurement beside it, because the reach is standing on
this number.

**Verification.** `tools/check.sh` **CHECK PASS**. `SMOKE_VIEWPORT=mobile` on the published mirror:
**250 passed, 2 failed** against `origin/dev`'s **246 passed, 2 failed** on the same runner and the
same command â€” the same two road assertions `dev` already carries (R-BUG5b/#201 and T-V2/#135), and
the +4 is exactly this parcel's four new gates. No threshold, band or station was weakened. **The
desktop half of the smoke does not fit the runner's ten-minute per-command ceiling and did not run**
(ROADMAP Â§ THE RUN BUDGET); the desktop figures above are `measure_shadow_reach.mjs` and
`measure_shipped_batches.mjs` at 1280Ã—800 on the published mirror.

**Superseded numbers.** Any draw-call figure in this file taken before 2026-08-17 is a 16-batch
figure â€” including R-W5a's own 16, K36(b)'s 56-vs-16 and R-W3b(a)'s 70/74/78/80 ladder. The town
is one batch now and the ladder must be re-measured before it is quoted.

#### R-W5a2 â€” the parcel as written, kept for the record

**Phase:** RENDERING Â§4 W5 Â· **Runner:** improve-runner Â· **After:** R-W5a (done)

The 16 remaining building batches are one per distinct `roughness` in the town. Carrying roughness
per-vertex the way R-W5a carried colour would make it **1**, worth about 15 draw calls at every
station â€” measured, not estimated: R-W5a's own instrumented run counted 18 structure draw calls
before the three-decimal merge and 16 after, at every station.

**It needs a shader patch, which is why it was not done in the same run.** `vertexColors` is a
stock three feature; per-vertex roughness is not, and wants a `_roughness` attribute plus a
replacement of `#include <roughnessmap_fragment>`, chained onto `confidence.patch`'s
`onBeforeCompile` the way that patch already chains onto whatever came before it. The `_confidence`
channel is the proof the pattern works inside a `BatchedMesh` here.

**Take it only when the lane has nothing sharper.** The budget is met with 5 calls of headroom at
the worst station and the growth term is already zero, so this buys margin, not a fix.
*(Overtaken 2026-08-17: the margin WAS the fix â€” see finding 1 above. The paragraph priced the
colour pass and the shadow pass was where the count was being spent.)*

**Files:** `renderers/web/js/buildings.js` Â· `renderers/web/js/confidence.js` (chaining only)

**Acceptance:** 1 structure batch; draw calls â‰¤ 80 at all 11 stations, both viewports; triangles
unchanged to the triangle; the same frame-difference budget R-W5a measured itself against
(whole-frame mean |Î”| under 0.01 of an 8-bit count); zero page errors.

### R-W2 â€” texture the town Â· **UNCLAIMED Â· SPLIT**

**Phase:** RENDERING Â§4 W2 Â· **Effort:** L Â· **After:** R-W1

**The no-Blender half is itself TWO parcels â€” claim ONE:**

| | parcel | scope |
|---|---|---|
| **R-W2a** | ~~**the material sheet**~~ Â· **DONE 2026-08-16 â€” `docs/RESEARCH/materials.md`. Read its Â§4 before texturing anything: the chimney is not a material here, no record states a roof covering, and 27 % of the town is painted by a generator that shares no colour with the other 73 %** | Research and write it: which surfaces exist, what each is made of, its **roughness** (not only colour and tiling rate â€” see the R-G1 finding below), tiling rates, and which archetype parameter selects it. **Files:** `docs/RESEARCH/materials.md` (new) only. No code, no records, so no smoke â€” it is a document, and it is the input everything downstream needs. |
| **R-W2b** | ~~**wire the sheet in**~~ Â· **LANDED 2026-08-21 as T-0007** â€” `generators/common/materials.py` is the sheet as code and 207 of 243 committed GLBs were repainted from it. **The records needed no new material field:** `finish_key` (222 records) and `roof_condition` (218) were already committed in the `reconstruction` block, one level ABOVE the phase, which is exactly why no archetype could read them â€” so the wiring is `from_phase(phase, record)` rather than a 315-record schema change. Triangle delta 0 and material-count delta 0 (K36(a)'s five-material threshold binds hard). Findings 2 and 5 discharged; **finding 2's covering half stands untouched** â€” no `shingle` row exists and roofs are graded by weathering CONDITION. `docs/LIBERTIES.md` L155 (now **L157** â€” the file is append-only and the number shifted); materials.md Â§6; STATUS.md. **The half it left is DONE 2026-08-24 as T-0126** â€” Â§2.3's dark openings and the glazing beside them, and finding 3's one name over two timbers. Re-measured first: Â§2.3 says FOUR values and **three ship**, because `inferred_placeholder.py` now paints no committed asset (`--check`: *0 flagged placeholder GLBs; 226 superseded by a canonical bake*), so Â§1's whole census is stale and must be re-measured before it is quoted again. One `dark` row at `0.072, 0.068, 0.060` / **0.60** over 287 slots â€” the roughness bounded between `glass` 0.25 and the bare fabrics 0.90â€“0.94 and taken at their midpoint, because every one of those slots carries surfaces that are certainly not glazed while 156 of them also carry windows, 112 of those sized off the one attested pane. `glass` comes onto the sheet unchanged; `timber` becomes `heavy_timber` + `sawn_framing`. Material-count delta 0, triangle delta 0 (484,903 both sides). L182; materials.md Â§7. | Take R-W2a's committed sheet and make the params and records name its surfaces. **Files:** `generators/archetypes/*_params.py` Â· `data/structures/*.json` (material fields only). Re-derives through the generators' `--check`. |

**R-W2a costs almost nothing to run and unblocks the rest** â€” it is reading and writing, not
rendering. Do not merge the two: a sheet argued and a sheet applied are different reviews.

**The bake half (nightly bake, arrives as a dev-targeted PR):** UV layout, atlas generation
and the actual textured GLBs. The `ktx` binary is installed on the bake runner as of
2026-08-14 (RENDERING Â§8 decision 5), so `--texture-compress ktx2` can finally run.

**Do not** attempt the bake half on the improve runner.

**From R-G1 â€” this parcel owns the two worst axes on the board**, texture **1.4** and material
**3.6**, and nothing else can move them. The scored reading: every surface in the town is one
flat colour, so a roof, a whitewashed clapboard wall, a hewn log, its chinking and a chimney
differ only in hue; there is no roughness variation anywhere, so nothing reads as painted,
weathered or wet; and the Wau-Bun blue shutters at `sauganash` sit at the same value as the
glazing beside them. The material sheet should name a roughness per surface, not only a colour
and a tiling rate.

### R-W2a â€” the material sheet Â· **DONE 2026-08-16 Â· `docs/RESEARCH/materials.md`**

**Phase:** RENDERING Â§4 W2.1 Â· **Runner:** improve-runner Â· **Effort:** S (a document) Â·
**Files:** `docs/RESEARCH/materials.md` (new) Â· `docs/ROADMAP.md` Â· `docs/STATUS.md` Â·
`renderers/web/js/changelog.js`. No code, no parameter, no record â€” so no smoke, by the
parcel's own definition.

**The sheet is measured out of the shipped GLBs, not read off the source**, because this
project has shipped a bug in that gap twice (B-BUG2). **334 assets carry 1,353 material
slots** resolving to **32 names, 41 base colours and 18 roughness values**; every one is
`metallicFactor 0`, `doubleSided`, `OPAQUE` and carries no map of any kind. It sizes every
tile to a whole number of the surface's own committed module (32 clapboard courses of 0.14 m
â†’ 4.48 m at 1024Â² â†’ 228.6 px/m; 12 log courses of 0.34 m â†’ 4.08 m â†’ 251.0 px/m) so the tiles
land inside Â§4 W2's 128â€“256 px/m band without a chosen-to-look-right number anywhere.

**Five findings, none of them patched â€” this parcel ships a document:**

1. **The chimney is not a material in this project.** `frame_dwelling`, `frame_storefront`
   and `log_dwelling` build their stacks with `M_ROOF`: **219 stacks on 199 buildings are
   painted with the roof's colour.** The 90 inferred placeholders ship a real
   `placeholder_chimney_brick`. So the town *has* a brick chimney material and the archetype
   buildings do not use it â€” and `log_dwelling`'s own docstring argues at length that a
   frontier stack is stick-and-clay or fieldstone, a different object from a framed house's
   brick stack, which renders identically to it. Opened as **R-W2c**.
2. **No record anywhere states a roof covering.** 315 records state a roof *type* and 309 a
   pitch; **zero** state what the roof is made of. All 234 `roof` slots are one colour, and
   the board roof `outbuilding` argues for is separated from a shingle field by **0.03 of
   roughness and nothing else**. The repository's one direct attestation â€” the North Side
   school's "sheeted and shingled roof" â€” is read by nothing. Roofs cannot be textured until
   an attribute exists to select the covering, and that is a schema change across 315 records.
3. **A `documented` material fact is committed, correct, and rendered by nothing.**
   `cobweb_castle` carries `cladding: clapboard_part_way_up`, **attested**, sourced to
   `andreas_1884_v1` â€” and it is a `log_dwelling`, which does not read `cladding`, and the
   value is not in `CLADDINGS`. `cladding` is stated on 27 records and read on 22.
4. **27 % of the town is painted by a generator with no shared palette.** The 90 placeholders
   share not one colour and not one roughness with the 244 archetype assets (their walls are
   all 0.86, a value that appears nowhere else). They also read `roof_condition` â€” stated on
   **218 records** â€” and `finish_key`, and **no archetype reads either**, so on 244 buildings
   a weathered roof and a fresh one are the same pixel. An atlas that textures one path and
   not the other splits the town visibly in half.
5. **R-G1's "there is no roughness variation anywhere" is right about what matters and wrong
   as written, and the difference decides what W2 builds.** *Between* surfaces there are 18
   argued values spanning 0.15â€“1.00. What is absent is variation *within* a surface â€” every
   square metre of every wall has one roughness, which is why nothing reads as weathered.
   **The deliverable is a roughness map, not better constants.** Do not spend a round
   re-tuning the 18 numbers.

Two smaller ones on the record: `timber` is one name over two materials **3.2Ã— apart in
linear red** (only the outbuilding's ships â€” no record turns `framing_exposed` on), and one
log wall in Chicago is a different timber from the other 52 (`frame_tavern` alone still
imports `LOG_RGBA`, and the affected asset is the Sauganash's log wing, in front of the
station named after it).

**It also decides the licensing question W2.1 has to answer: generate the atlas, do not
photograph it.** 38 of the project's 65 sources are `check_required`; the one full-resolution
photograph committed is CC BY-SA 4.0 cleared for measurement and **explicitly not for any
derived asset**; and the owner's twelve-view reference set says in its own README that it may
drive materials as `inferred` â€” while being the same `chicagology_*` material
`assets/LICENSES.md` gates. Procedural tiles built from the dimensional constants in the sheet
need no new clearance and keep the property this project actually cares about.

### R-W2c â€” the chimney is roof-coloured on 199 buildings Â· **DONE 2026-08-22 as ticket T-0008 â€” brick on the framed town, cat-and-clay on the log cabins**

219 stacks painted `roof` (finding 1 above). **It is not a palette fix, and picking the
placeholder's brick would be the wrong half of it**: `log_dwelling` argues a stick-and-clay or
fieldstone stack against the gable, `frame_dwelling` an interior brick stack at the gable end,
and those are two materials, not one. So the parcel **opens with the research question** â€”
what a Chicago chimney of 1835 was built of, by building type â€” and only then touches a
palette. `docs/LIBERTIES.md` L26 already owns every chimney's *position*; whatever this lands
owes the same treatment for its *fabric*.

**Files:** `docs/RESEARCH/` (a dossier) Â· `generators/archetypes/*.py` (material index only) Â·
`generators/common/mesh.py` if a shared value is wanted. **NEEDS ONE BAKE** â€” it changes
material assignment on committed geometry, so it cannot go green on the improve runner and
should ship the research + palette half and say so.

**HOW IT LANDED, 2026-08-22 (T-0008), and the bake half came with it** â€” Blender has been on the
improve runner since 2026-08-19, so the parcel shipped whole rather than in halves: 245 generated
masters rebuilt, derivatives and publish in the same commit.

**The research is `docs/RESEARCH/chimneys.md`** and its answer is the one this box predicted â€”
two materials, not one â€” arrived at from what the repository already held rather than from a
palette. The framed town gets **brick**, `inferred`: the Petford watercolour of the Sauganash is
the one coloured witness here to any Chicago chimney and it says brick; Blodgett's brick-yard
opened on the North Side in the spring of 1833 (`brickyard_north_side`, Andreas p. 1161) and the
Lake House went up in brick in 1835; and an interior flue through a timber roof has to be masonry.
The log cabins get a **cat-and-clay daub**, `reconstructed` and bounded rather than picked â€” no
paler than the CHINKING it is daubed with, no darker than the palest ROOF CONDITION, and at the
midpoint of the two because nothing states where between them it sits. Fieldstone is the other
half of `log_dwelling`'s own sentence and is deliberately not built.

**The tone is not a new number.** `frame_tavern`'s `BRICK_RGBA` moved into
`generators/common/materials.py` verbatim â€” the same convergence T-0007 made for the hewn log â€”
so the Sauganash's masters come out byte-for-byte unchanged, which is the proof the value did not
move.

**Three findings.**

1. **It was not a one-file fix.** Four archetype modules and the sheet, because a material index
   is only the last step: `M_CHIMNEY` is appended CONDITIONALLY in each archetype, on the
   discipline `log_dwelling` already held itself to for `M_PAINT` â€” an unreferenced slot still
   reaches the glTF, so an unconditional append would rewrite every chimneyless master for a
   colour it does not use. Two `frame_storefront` masters keep their six-material list for
   exactly that reason.
2. **It cost NO draw call, and the reason is worth banking.** `buildings.js::materialKey` batches
   on type, emissive, metalness, the four maps, side, transparency and flat-shading â€” never on
   base colour and never on roughness, both of which ride per vertex since R-W5a2. So two new
   material colours merge into the buckets that already exist: **113 draw calls before and 113
   after** at `south_water`, 1280Ã—800. A parcel that adds a COLOUR to this town is free; one that
   adds a MAP is not.
3. **R-W2a's own count does not reproduce.** This box says 219 stacks on 199 buildings; the
   resolved parameters of the committed masters give **157 stacks on 143 buildings** across the
   three archetypes plus `frame_tavern` (frame_dwelling 71/69, frame_storefront 33/33,
   log_dwelling 34/31, frame_tavern 19/10). The 2026-08-16 figure is not re-derivable from
   anything committed, so it is left as written and this is the measurement that replaces it.

**Left standing, in writing rather than by omission:** the fort's ten garrison buildings keep
roof-coloured stacks â€” 1816, federal ground, four constructions, and neither answer above reaches
them without inventing a third (**T-0137**); and the 90 inferred placeholders keep their own
`#89503F` brick, about 20 % apart in linear red from the archetypes' (**T-0138**), because
converging it moves 90 masters and the banked passthrough set. A third trap surfaced on the way:
the bake cannot reach `cook_county_courthouse_1835` at all, so any `generators/common/` edit
leaves it stale with no committed route to heal it (**T-0139**).

### R-W3b(a) â€” the shadow reach Â· **DONE 2026-08-17 â€” the sun lit the town and shadowed 8 buildings of 331, and the ceiling is draw calls rather than fill**

**The answer is 60 m, and it was costing the whole mid-field.** `world.js` gives the sun ONE
orthographic shadow camera, a box that follows the visitor, and everything outside it is clipped
out of the depth map before it is drawn â€” so it casts no shadow on anything. Counted off the DATA
(each structure's `placement.local_e/local_n`, each planted stem's own station) against the shadow
camera's own matrices, on the published mirror at 1280Ã—800:

| anchor | structures inside, Â±60 m | inside at Â±120 m | stems, Â±60 m | at Â±120 m |
|---|---|---|---|---|
| `south_water` | **8** of 331 | **26** | **12** of 730 | **54** |
| `green_tree` | 8 | 27 | 0 | 0 |
| `sauganash` | 5 | 16 | 34 | 76 |
| `lake_market` | 5 | 13 | 33 | 73 |
| `forks` | 5 | 16 | 0 | 17 |
| `from_above` | **1** | 8 | 41 | 55 |

**Shipped: Â±120 m, and the map doubles with it â€” 2048Â² desktop, 1024Â² phone â€” so the texel size is
UNCHANGED at 11.7 cm and 23.4 cm.** That is the whole reason the number is 120 and not 150: nothing
a visitor stands next to got softer to buy the distance. The before/after pair in
`docs/evidence/r-w3b-{before,after}.png` is shot at `green_tree` at both rigs AS THEY SHIP â€” the
first pair taken for this parcel compared Â±60 m at 2048Â² against Â±120 m at 2048Â², which is a
comparison of two texel sizes and made the near wall look like the change.

**THE FINDING â€” the reach is DRAW-CALL-bound, not fill-bound, and that is the opposite of what a
shadow map is usually limited by.** Every batch that enters the box is another draw call in the
shadow pass (three renders it inside `render()`, after `info.reset()`, so `renderer.info` counts
it). Measured at the worst anchor, `green_tree`:

| reach | draw calls | triangles | structures inside |
|---|---|---|---|
| Â±60 m (shipped before) | 70 | 742,256 | 8 |
| Â±120 m (**shipped now**) | **74** | 772,268 | 27 |
| Â±150 m | 78 | 825,146 | 33 |
| Â±180 m | **80 â€” the budget exactly** | 830,690 | 38 |

The budget is 80 (`main.js` `BUDGET.drawCalls`) and the smoke asserts it. So **Â±180 m fails the
gate at the first station that adds a batch**, with two thirds of the town still outside the box,
and the route past Â±120 m is fewer batches â€” **R-W5a2**, "the last 16 batches â†’ 1", which this
parcel therefore promotes from "not needed for the budget" to the thing that unblocks the reach â€”
or true cascades, **R-W3b(b)**. Raising the constant alone will not get there.

**AND R-W5a2 TOOK THAT ROUTE THE SAME DAY â€” the ladder above is a 16-batch ladder and is
superseded.** With the town merged to one batch the same worst anchor reads **48 calls at Â±120 m
and 50 at Â±240**, so the shipped reach is **Â±240 m at 4096Â²/2048Â², still 11.7 / 23.4 cm per
texel**. Read R-W5a2's box for the new table; do not quote 70/74/78/80 for anything but the
16-batch scene they were taken on.

**The gate, and the liveness assertion R-A1 says it owes.** `tools/smoke_renderer.mjs` asserts at
`lake_market` that the rig carries Â±120 m over the right map for its tier, AND that winding the
reach back to Â±60 m CHANGES the frame â€” because a reach wired to nothing passes the first
assertion identically. The threshold was measured before it was set: winding back moves 104 of
2,304 cells with a worst cell of 8 at 1280Ã—800 and 86 with a worst of 8 at 390Ã—780, and the gate
asks for 4. `world.setShadowReach()` exists for that assertion and nothing else.

**Files:** `renderers/web/js/world.js` (`SHADOW_REACH_M`, the shadow block, `shadowRig`,
`setShadowReach`) Â· `tools/measure_shadow_reach.mjs` (new â€” the instrument) Â·
`tools/smoke_renderer.mjs` (two assertions) Â· `docs/evidence/r-w3b-{before,after}.png`.

**Not verified here:** the desktop half of the smoke does not fit the runner's ten-minute
per-command ceiling (ROADMAP Â§ THE RUN BUDGET), so the desktop assertions were run through
`measure_shadow_reach.mjs` at 1280Ã—800 rather than through the gate itself. The draw-call figures
above are that measurement, at every anchor.

### R-W3 â€” ambient occlusion and cascaded shadows Â· **UNCLAIMED Â· SPLIT**

**Phase:** RENDERING Â§4 W3 Â· **Effort:** M Â· **After:** R-W2

**The no-Blender work is THREE parcels â€” claim ONE. They are genuinely unrelated jobs that were
filed together only because RENDERING Â§4 groups them:**

| | parcel | scope |
|---|---|---|
| **R-W3a** | **the AO cage rule** | Â§1 item 10: the bake works end to end and fails because clapboard courses and window reveals a centimetre off the wall occlude each other. ~~mean 0.265, 69 % of texels below half~~ â€” **both figures void, T-0158.** **T-0227 answered the question on the frame, 2026-08-28: yes, far too dark â€” the Sauganash's own pixels fall from mean L\* 33.8 to 11.1 with 6,532 of them at literal black. Correction 3 below carries the tables, and the acceptance is now a frame reading, not an atlas mean.** It needs a **low-poly cage**, not tuning. **Files:** `docs/RESEARCH/ao-cage.md` (new) Â· `generators/archetypes/*.py` (cage emission) Â· `tools/measure_ao_frame.mjs` (the before/after reading). |
| **R-W3b** | **cascaded shadows** | `renderers/web/js/world.js` only â€” today one 1024Â² map on a Â±60 m follow ortho, nothing beyond 60 m. **Touches no generator and no record**, so it shares nothing with 3a and can run beside it. **SPLIT 2026-08-17 into R-W3b(a) â€” the reach of the one map, DONE â€” and R-W3b(b) â€” true cascades, which (a)'s measurement says is now the only route past Â±120 m that does not start by cutting batches.** |
| **R-W3c** | **openings** | The silhouette failure R-G1 names: no reveal, no sill, no sash, no muntin anywhere in the set, so the 6-over-6 rhythm the Green Tree plate documents does not exist. Archetype geometry. |

**The bake half (nightly bake):** re-bake with the cage and flip `baked_ao` on the 244 assets.
**After R-W3a**, and see `B-A1` before assuming the nightly should be the thing that runs it.

**Two corrections to the numbers R-W3a is built on â€” T-0158, 2026-08-27, and the second one
changes the parcel's target.**

1. **The export was losing the bake entirely.** `build.py --ao` tagged the baked image
   `Non-Color` AFTER the bake, which frees a generated image's buffer â€” it regenerates black â€”
   and clears the `is_dirty` flag Blender's exporter tests before it will carry unsaved pixels.
   Measured on `sauganash_hotel`, 512Ã—512, 48 samples: in memory min 0.000 / max 1.000 / mean
   0.2158, in the GLB **min 0, max 0, all 262,144 texels**, with `baked_ao: true` beside it.
   Tagging the image before the bake fixes it â€” 0.1665 in memory, 0.1665 in the file, 0.0 %
   drift â€” and `generators/ao_export.py` now refuses the failure at build time and on every
   commit. So R-W3a can now measure a cage rather than a black square.
2. **"Mean 0.265, 69 % of texels below half" is wrong twice over, and so is the 0.38.** First,
   both were read off an sRGB-tagged buffer, so they are the sRGB-ENCODED occlusion rather than
   the occlusion: `Image.pixels` on an 8-bit buffer is raw in both directions (measured), so the
   tag decides what the bake WRITES, and glTF samples occlusion as `byte/255` with no transfer
   decode. Second, and worse, both are taken over the **whole 512Ã—512 atlas, 68.9 % of which is
   empty UV space** â€” the "69 % below half" is very nearly the empty fraction itself, so most of
   what it counted was blank rather than dark. Re-measured from the exported file: atlas-wide raw
   mean **0.1665**, and over the **81,458** texels the unwrap actually writes, **mean 0.5358 with
   58.7 % below half**. The 0.38 has not been re-measured at all.

   The concern's *shape* survives â€” over half the written surface below half occlusion, on a
   building whose white paint is documented â€” but **every number this parcel is written around is
   void, and none was ever read off a file that carried the occlusion** (the export was shipping
   black). **T-0227 answers it from a rendered frame before this parcel builds a cage to improve
   a figure nobody has measured correctly**, and carries the unwrap with it: an atlas two-thirds
   empty is two-thirds of every occlusion map's bytes spent on nothing.

3. **AND THE ANSWER, T-0227, 2026-08-28: yes â€” and the atlas statistic understates it badly.**
   `sauganash_hotel` baked with `--ao` (the fixed export: baked 0.1665 -> exported 0.1665, 0.0 %
   drift), swapped into the source tree, and shot at both Sauganash anchors and both viewports
   against the same tree without it. `tools/measure_ao_frame.mjs` reads the building's own
   visible pixels â€” the structures mask intersected with what moved between the two conditions â€”
   so the reading is of the walls rather than of the frame or of the atlas:

   | station | viewport | pixels read | mean L* without â†’ with | L* < 20 | literal black px |
   |---|---|---|---|---|---|
   | `sauganash` | desktop | 87,893 | **33.8 â†’ 11.1** | 31.1 % â†’ **88.9 %** | 0 â†’ **6,532** |
   | `sauganash` | mobile | 20,010 | 33.4 â†’ 11.1 | 31.8 % â†’ 89.5 % | 0 â†’ 1,289 |
   | `sauganash_wing` | desktop | 99,681 | 39.1 â†’ 17.9 | 15.4 % â†’ 64.9 % | 0 â†’ 3,781 |
   | `sauganash_wing` | mobile | 17,511 | 41.9 â†’ 20.6 | 4.9 % â†’ 56.5 % | 0 â†’ 340 |

   The whole-frame critic table agrees from the other side: `literal black px` 0 â†’ 6,841 and
   `shadow darkest decile L` 4.67 â†’ 2.00 at `sauganash` desktop, with triangles unchanged.
   **A documented white wall loses two thirds of its lightness and puts thousands of pixels at
   0,0,0.** Why so much worse than "0.5358 mean over written texels" suggests: glTF occlusion
   scales the INDIRECT term only, and at the scene's 70.5Â° sun the street-facing elevations a
   walker sees are carried by little else (Â§1 items 9â€“11) â€” so occlusion near 1 there removes
   essentially all of their light. **The parcel keeps its cage and loses its target: acceptance
   is `measure_ao_frame.mjs` showing the walls hold their lightness, not an atlas mean moving.**

   **Two costs this parcel now inherits, measured on that one asset.** The atlas is **31.1 %
   occupied** â€” 81,458 written texels of 262,144, the master 94,420 â†’ 202,292 bytes (+114 %) â€”
   so the ~107 KB occlusion PNG is two-thirds empty space before any decision about resolution.
   And **`aoMap` is part of `materialKey`** in `renderers/web/js/buildings.js`, so an asset
   carrying its own map cannot batch with one that does not: **+2 draw calls at every station
   and both viewports for a single building**, against a draw-call ceiling already breached.
   A per-asset map is therefore a batching decision as well as a byte-budget one (T-0285), and
   the empty two thirds of the atlas is its own ticket (T-0286).

**And a cost figure the bake half has to answer first.** With the export working, one asset's
master goes **94,420 â†’ 202,292 bytes (+114 %)**: a 512Ã—512 occlusion PNG carrying real variation
costs ~107 KB, where the uniformly black one compressed to 3,620 â€” which is why T-0015 measured
the AO file cost at "+4.4 %" and why that figure is now void. `assets/gltf/` is 27 MB for 348
masters; one 512Â² occlusion map each would add roughly 37 MB to it. Textures do not meshopt, so
the derivatives carry the same PNGs â€” and the published tree is **23.53 MB against a 25 MB
`SITE_BUDGET_MB`**, i.e. 1.5 MB of headroom against a ~37 MB ask. **So the cage parcel's first
question is texture size, atlas resolution and how many assets get a map at all, not cage
geometry** â€” a per-building 512Â² map is not affordable on this site as budgeted, and finding
that out after baking 346 of them would be the expensive way to learn it.

**3a and 3c are the same conversation about the same few centimetres of wall** (R-G1 says so),
so whoever takes one should read the other â€” but they ship separately.

**From R-G1 (geometry scored 4.6) â€” AO is carrying more than it looks like it is.** At the
scene's 70.5Â° sun a shadow is 0.354 Ã— the height that casts it, so the only cast shadow legible
in the five scored frames is each chimney's on the roof beside it. Form in this scene therefore
has to come from the environment term (W1) and from this parcel's AO, and both are currently
off. Separately, the silhouette failure the score names is **openings**: no reveal, no sill, no
sash and no muntin anywhere in the set, so the 6-over-6 rhythm the Green Tree plate documents
does not exist. The cage rule and the opening geometry are the same conversation about the same
few centimetres of wall.

---

## LANE 2 â€” TOWN COMPLETION Â· data only, no renderer files

Carries the town toward its documented late-1835 density â€” the **665-roof programme** â€”
through the existing generators. **This lane touches no file lane 1 touches**, which is what
makes the two safe to run at once.

**Where the count stands after T-A5 (2026-08-14): 266 roofs Â· 156 households Â· 192 persons**
(76 source-attested, 20 reasoned-from-evidence, 96 invented-to-fill-a-need). 399 roofs remain of
the 665-roof programme, **71 of them on ground the project has coverage for** â€” the binding
constraint is coverage, not recipes, which is what lane 3 exists to move.

**The rules, every parcel:**
- Recipe â†’ structure records + household records via the existing generators
  (`tools/generate_*_infill.py`, `tools/generate_inferred_households.py`,
  `tools/generate_inferred_names.py`), then `tools/compile_scene.py --all`.
- Placeholder massing from `generators/inferred_placeholder.py`. **No Blender.**
- **Every invention grades at the invented-to-fill-a-need tier with its reasoning note.**
  `tools/audit_confidence.py --strict` enforces the rule that nothing on an invented
  structure may outrank the invention that put it there.
- **Liberties appended** where a recipe embodies a compression â€” `docs/LIBERTIES.md` is
  append-only, and L91 shows the class-token form for a whole programme.
- `review_required: true` is honoured, not cleared. It blocks a scene from `released`.
- **Residents are RECORDS and Evidence/popup content only.** The no-human-figures constraint
  (AGENTS.md standing constraint, L1) is untouched by this lane and is not negotiable.

### T-A1 â€” refresh the 665-roof recipe Â· **DONE 2026-08-14**

Every later block parcel reads this, so it went first. The programme is now
`data/reconstruction/1835_665_roof_programme.json`, **derived** by `tools/reconcile_665.py`
and re-derived by `tools/check.sh` â€” a ledger about a town that grows most nights cannot be
an authored number, which is exactly how the crosswalk came to call 617 roofs remaining
while 232 were standing.

**232 physical roofs stand** (242 records: 12 of them are bridges, piers, a palisade, a
parade ground, a garden and a construction site that the reconciliation credits with no
roof, and one record is two cabins). **433 remain.** By district: South 270, West 94,
North 69, Fort 0 â€” the fort is complete.

**The finding that matters is not the count, it is where the count can go.** The plat module
reaches 19 blocks holding 152 lots. At the phase-1 parcel's own density â€” one principal roof
per lot, ancillary at the programme's 154:511 â€” those blocks have **105 roofs of headroom**.
The other **328 of the 433 have nowhere to stand**: 20 in the two blocks the module refuses
for want of South Water street control, 35 in the West recipe's own extension-gated set, and
273 in ground with no committed street control at all (east of State, south of Washington,
west of Clinton, and the whole North Division, which the grid does not cover by a single
block). **The binding constraint on the 665-roof programme is coverage, not recipes** â€” S9
street control and the terrain extensions are now what the town is waiting on, and T-A2
onward can only work the 105.

Six families are already **over** their target â€” C1, I2, T2, W1, W4, W5, nine roofs in all,
every one of them evidence the research placed after the target was written. A documented
roof is never removed to protect a family cap, so the excess is reported and taken out of
the invented family with the most slack (D4, the two-storey frame dwellings).

**Files:** `tools/reconcile_665.py` (new) Â· `data/reconstruction/1835_665_roof_programme.json`
(new, derived) Â· `tools/check.sh` (one step) Â· `1835_building_inventory.json` and
`1835_family_archetype_crosswalk.json` (stale statuses corrected) Â· `docs/ROADMAP.md` (S10) Â·
`docs/STATUS.md`

### T-A2 â€” the first refreshed block Â· **DONE 2026-08-14 (`blk_randolph_wells`)**

Ten anonymous roofs on the block bounded by Randolph, LaSalle, Washington and Wells: seven
principal buildings on seven of its eight lots and three yard buildings off the alley, to the
family mix the schedule apportioned it (A1 A3 A4 D1 D2 D3 D4 D5 H1 H2). Standing roofs
**232 â†’ 242**; remaining **433 â†’ 423**, of which **95** still have modelled ground.

**The parcel shape that repeats, and it is not the one T-A2 was written expecting.** The three
earlier parcels authored their own coordinates â€” a row northing and a list of eastings, or a
centre per slot â€” because the plat module did not exist when they were written. This one
authors **no coordinates at all**: the recipe says which family stands on which lot, whether it
fronts the street or the alley, and how far back, and `tools/generate_block_infill.py` reads
every metre off the committed lot polygons. That is what makes T-A3â€¦T-An a recipe entry rather
than a new geometry argument each time, and it retires by construction the defect class K7 found
(seven buildings in the middle of the road, from a recipe that never asked where the road was).

**Two findings came out of it that are not the block.**

- **`family_bands_ft` in the building inventory has no H1, H2, H3, C4, T1-T3, W5, F3, F4, I1-I3
  or M1 band** â€” 14 of the programme's 35 families â€” so the earlier generators could only build
  the families somebody had retyped into Python, and the schedule was apportioning H1 and H2 to
  this very block. **The crosswalk had them all along**: `1835_family_archetype_crosswalk.json`
  carries the footprint band, the storey count, the eave height and the placeholder archetype for
  every family, and agrees with `family_bands_ft` on all 21 both of them hold. This generator
  reads the crosswalk, so every family the programme can name is now buildable and no band is
  retyped anywhere. **H1 and H2 stand for the first time.**
- **The A3 privy's authored eave band (6-7 ft) dips below what the outbuilding archetype needs**
  to carry its own man door plus a header â€” refused by name at 1.891 m. The sample is now drawn
  from the part of the authored band the archetype can build (2.07 m here, beside phase one's
  privies at 2.05), and a family whose whole band sits under that floor fails loudly rather than
  being quietly raised out of its typology. Recorded in L92.

**Deferred, deliberately, and it is the one part of the parcel as written that did not ship:**
the **household layer**. Adopting these ten roofs as dwellings means restating
`1835_inferred_household_programme.json`'s occupation census â€” the generator gates the census and
the households against each other in both directions â€” and that is the K1 programme's own
argument about who the town's tradesmen were, not something a block parcel should re-decide as a
side effect. **T-A2h below owns it.**

**Files:** `tools/generate_block_infill.py` (new) Â·
`data/reconstruction/1835_platted_block_parcels.json` (new, authored) Â·
`data/structures/recon_1835_blk_randolph_wells_*.json` (10, derived) Â·
`data/structures.schema.json` (four lot-provenance fields) Â· `data/sidecars/1835/` Â·
`assets/â€¦` placeholder massing Â· `docs/LIBERTIES.md` (L92) Â· `tools/check.sh` (one step)

### T-A2h â€” the ten roofs' households Â· **DONE 2026-08-14 (two adopted, eight refused)**

**Two of the ten roofs are adopted and the other eight are not, and the ratio is the finding.**
The parcel was written expecting an argument about the town's trade mix. The argument it actually
produced is about who is allowed to start one: a block parcel appends ten dwellings to the plat in
the time it takes to write a recipe entry, and an occupation census that grows to match is a
census driven by what has been drawn rather than by the town. The 3,265-people-in-398-dwellings
calibration is a claim about Chicago; letting a drawn cottage raise it is fitting the evidence to
the model.

**So the rule, now written into the household programme's own `method` list where the next parcel
reads it.** A block roof may be adopted only where BOTH tests pass: the trade's own committed
argument states in its text that its count is a **floor rather than a bound**, and the roof's
family is one this layer **already houses that trade in**.

- **Test one passes for exactly two of twenty-nine trades.** The carpenter â€” *"the shop count is a
  floor under the trade, not a measure of it"* â€” and the labourer â€” *"still a small fraction of
  what 3,265 people implies"*. Every other entry states a ceiling (the plasterer's and the
  drover's say *"and no more"* outright) or is bounded by a workshop or store family's roof target
  under method rule 2. Two apparent third and fourth matches are a false positive worth naming:
  the laundress and the boarding-house keeper entries contain the word *floor* only inside the
  Andreas quotation *"with the floor covered besides"*.
- **Test two, measured against the layer as it stood, picks the same two families.** All 8 of the
  layer's adopted labouring households live in a D1 and 9 of its 10 carpenters in a D3 â€” and a D1
  and a D3 are two of the seven dwellings this block deals. The tests were derived independently
  and agreed on the first block they were applied to, which is the only reason to trust either.
- **The result:** `hh_inf_labourer_south_13` in the D1 log cabin and `hh_inf_carpenter_south_11`
  in the D3 cottage. Households **152 â†’ 154**, persons **188 â†’ 190**, adopted anonymous roofs
  **83 â†’ 85**. Standing roofs unchanged at **251** â€” this parcel built nothing.

**Three kinds of refusal, and only one of them is the rule.** The stable, privy and woodshed are
refused because a yard building has no occupant to argue about, and the generator now says so by
name. D2, D4 and D5 are refused by the rule: this layer houses laundresses, boatmen, masons,
clerks and shoemakers in those families and every one of those counts was argued to a number.
**H1 and H2 are refused for the strongest reason** â€” 18 larger houses and 14 merchant or
professional houses in the whole town, whose occupants are the most likely people here to be
nameable, so inventing an anonymous merchant into one would break the programme's own rule never
to infer a person where a documented one is available. They want T-I3's treatment, not a census
draw.

**The adoption is data, in one place, gated in both directions.** `tools/generate_block_infill.py`
now reads `tools/inferred_occupancy.py` exactly as the three earlier anonymous parcels do, so the
adoption is authored once in the household ledger and handed to whichever generator owns the roof
â€” hand-editing a generated record would have failed the drift check that makes these parcels
trustworthy. The new gate refuses an adoption that lands on an ancillary roof, and refuses a roof
the ledger names that no recipe builds. Both verified by doing each: the privy adoption fails by
name, and a household pointed at a non-existent block roof fails by name.

**One thing this parcel churned and did not fix â€” see K20.** Adding two people renamed **25 of the
94** reconstructed residents, because the invented-name allocator deals names round each pool by
index within a bucket, so an insertion shifts everyone after it. No grade moved and every name
re-derives, but the file's own docstring claims the assignment is a function of a person's id, and
it is a function of the whole population.

**Files:** `data/reconstruction/1835_inferred_household_programme.json` (census, two households,
method rule 6) Â· `tools/generate_block_infill.py` (occupancy + the adoption gate) Â·
`data/residents/households/*.json` Â· `data/residents/index.json` Â·
`data/structures/recon_*.json` (occupancy only, via the generators) Â· `data/sidecars/1835/` Â·
`assets/manifest.json` Â· `docs/LIBERTIES.md` (L94) Â· `docs/ROADMAP.md` Â· `docs/STATUS.md`

### T-A3h â€” the second block's households Â· **DONE 2026-08-15 (two adopted, three refused, and the refusals traced)**

**The prediction held and the reason it held was not the one this box gave.** `blk_randolph_dearborn`
landed on 2026-08-14, a day before rule 6 took its third test, and its five dwellings had never been
asked the adoption question. Run rather than recalled â€” `tools/measure_adoption_tests.py <family>
south`, five times â€” the block's D3 on lot 0 is adoptable by the **carpenters** and nobody else, its
D1 on lot 3 by the **labourers** and nobody else, and its D5 by no trade at all. Both are adopted:
carpenter households **19 â†’ 20**, labouring **22 â†’ 23**, inferred households **99 â†’ 101**, inferred
persons **111 â†’ 113**, adopted anonymous roofs **102 â†’ 104**. **Standing roofs unchanged at 322 and
remaining unchanged at 343** â€” this parcel raises no building, invents no position and moves no
record. Recorded in L109.

**THE OTHER TWO DWELLINGS ALSO PASS ALL THREE TESTS, AND WHAT THEY PASS ON IS THIS PARCEL'S
FINDING.** The D4 on lot 6 prints ADOPTABLE for the carpenters and the D2 on lot 5 for the
labourers, exactly as the "second roof" at eight blocks before this one did. Nobody had asked where
those verdicts come from:

- this layer houses **one** carpenter in a D4 â€” `hh_inf_carpenter_north_10`, in the **North**
  Division â€” and all thirteen carpenters it houses in the **South** Division are in a D3;
- it houses **four** labourers in a D2 â€” the shanties north_a, north_b, west_a, west_b â€” and all
  eleven labourers it houses in the **South** Division are in a D1.

**So neither candidacy is a pair this layer has ever housed.** Rule 6 says in its own committed text
that *the three tests are independent*, so test 2 reads the set of families and test 3 the set of
divisions, and a roof passes on a family taken out of one division and a division taken out of
another family. `tools/measure_adoption_tests.py --pairs` (new here) prints the whole table: **20
(family, division) pairs across 8 trades are admitted by the projections and housed by nothing**, and
test 1 narrows the ones that can actually be adopted to exactly **two** â€” the carpenters' D4/south and
the labourers' D2/south. Those two are the entire content of the second-roof question. Every refusal
K28 has collected â€” nine for the labourers, seven for the carpenters â€” refused a candidacy assembled
out of evidence that is never about the same roof twice.

**THE STRICTER READING IS NOT OBVIOUSLY RIGHT AND THIS PARCEL DOES NOT TAKE IT.** Requiring the PAIR
would refuse the **fourteenth labouring household**: T-A4 adopted a D1 in the WEST Division when this
layer housed labourers west of the river only in D2 shanties, and argued it in exactly the projected
form â€” the family from one division, the division from another family. Rule 6 names that adoption as
one of the four decisions its third test *recovers*, so a pair reading breaks the calibration the
rule rests on. Both facts are now committed and K28 decides with them in front of it; the tool
reports the column and gates nothing, because a gate would freeze the question shut.

**The two refused roofs are refused on T-A9's reading, unchanged**, for the ninth and seventh time,
as a choice rather than a rule. **Nothing was built on the block's three open lots**: they are named
open in T-A3's committed recipe with a reason each â€” one for the refused I3 civic slot, two on the
programme's alternating-vacancy assumption â€” and filling one to house a household would be the
fitting-the-model-to-the-drawing rule 6 exists to stop.

**The eleventh K20 measurement is 67 of 111** carried-over invented persons renamed â€” the highest
since T-A14's 61-of-108, and for the structural reason K20 predicts: two insertions landed in the
middle of the two largest buckets this layer has. No grade moved, every `name_basis` kept its pool
citation, and `check.sh` re-derives all 113.

**Files:** `data/reconstruction/1835_inferred_household_programme.json` (two households, two census
counts, two arguments) Â· `tools/measure_adoption_tests.py` (the `pair housed` column and `--pairs`) Â·
`data/residents/households/*.json` Â· `data/residents/index.json` Â· `data/structures/recon_1835_blk_randolph_dearborn_{d1_04,d3_01}.json`
(occupancy only, via the generators) Â· `data/sidecars/1835/` Â· `assets/manifest.json` Â·
`docs/LIBERTIES.md` (L109) Â· `docs/ROADMAP.md` Â· `docs/STATUS.md` Â·
`renderers/web/js/changelog.js` Â· `site/chicago/4d/` (publish mirror)

### K20 â€” the invented-name allocator is not stable under insertion Â· **DONE 2026-08-16**

> **DONE â€” and the twelve anecdotes understated it. One new household renamed up to 73 of the
> 113 invented residents, 64.6 % of the layer, and in the two largest buckets it never renamed
> nobody. It is 10 now, the pools are the reason it is not 0, and the instrument is committed.**
>
> **The eleven measurements were all real and all low.** T-A2h read 25 of 94, T-A5 17 of 33
> touched, T-A9 19 of 98, T-A14 61 of 108, and L101 â€” the worst before this â€” 72 of 100. Every
> one was a by-product of a parcel doing something else, which means every one measured a
> single arbitrary insertion at a single arbitrary point in the hash order. Sampled properly,
> with 240 synthetic single-household insertions across all six trades this layer populates,
> the distribution is not centred anywhere near 25: mean **40.4** for a carpenter, worst
> **73 of 113**, and **1 of 40** probes in that bucket renamed nobody. The parcels that read
> 17 and 19 were lucky, and the argument that "a fifth of the layer" was the cost was built on
> the low half of a distribution nobody had drawn.
>
> **The cause is exactly what the parcel predicted, and the fix is the shape it proposed with
> one change.** Dealing by index makes a name a function of *how many people sort ahead of you*.
> It is now a function of *who you collide with*: each person has their own deterministic
> ordering of the pool, and taking them in the same stable hash order, each claims the
> least-used name they are permitted. The change to the proposal is that **a given name and a
> surname are not the same problem** and the old code welded them to one index. A repeated
> given name is what a town looks like â€” five Johns among 73 men in 1835 is unremarkable and
> claims nothing about anybody â€” so a given name is now simply each person's first preference,
> with no ledger at all, which is the most insertion-local rule available. A repeated *surname*
> reads as kinship, which this layer asserts of nobody, so that one keeps the ledger and the
> floor rule that holds every count within one of every other.
>
> **Measured after, on the same 240 probes: worst 10 of 113, mean 4.6.** Splitting the two
> halves is a third of that improvement on its own â€” the floor rule on both halves gives 17.
>
> **The residual is the POOL, not the allocator, and the report proves it rather than asserting
> it.** `tools/measure_name_churn.py` prints each bucket's pressure â€” its size over its surname
> pool. The two buckets with room to spare (**0.14Ã—**) rename **at most one** person, which is
> the literal acceptance criterion: only the person actually collided with. The four dealing 36
> surnames to 73 men (**2.03Ã—**) rename up to ten, because at that pressure there is no spare
> name at the floor, so the newcomer must displace somebody and that person displaces the next.
> **8 renames at pressure 2.03Ã— is a pool that is too small; 8 at 0.14Ã— would be an allocator
> that is still not local.** The gate reads the second as a failure and the first as arithmetic.
>
> **A bug the fix exposed, which the index deal had been hiding.** Unwelding the given name from
> the surname allows two people to draw the same pair, and the first run of it shipped **two
> Alvah Hastings** â€” two invented residents who were the same person. The allocator now carries
> that as its one absolute constraint; all 113 full names are distinct.
>
> **The one-time cost is the whole layer: 113 of 113 renamed, 101 household files.** That is
> what K20 said it would be, it is recorded as **L111**, and it invents nothing new â€” the pools,
> the grading, the `name_basis` citation and the note are untouched, and a different invented
> name is the same claim about the same nobody.
>
> **The durable half is a gate**, in `check.sh` at ~2 s: `measure_name_churn.py --gate` fails if
> one insertion rewrites more than **16** names. Sixteen rather than ten because what it must
> catch is the class â€” an allocation that depends on how many people precede you â€” and every
> measurement of that class has been above it. If growth ever fires it, the answer is a wider
> pool, not a higher number.
>
> **What this does NOT fix, and what to open if the diffs go noisy again:** the surname pools
> are 2.03Ã— oversubscribed and are seeded from the 76 attested residents this project holds, so
> widening them is **evidence work** â€” more named 1835 Chicagoans out of Andreas and the census
> rolls â€” and not a tuning knob. At 3Ã— pressure the residual will climb again. That is the
> parcel to open, and it buys a better-attested pool as well as a quieter diff.
>
> **Files:** `tools/generate_inferred_names.py` Â· `tools/measure_name_churn.py` (new) Â·
> `tools/check.sh` Â· `data/residents/households/*.json` (101) Â· `data/sidecars/1835/*.json` Â·
> `docs/LIBERTIES.md` Â· `docs/ROADMAP.md` Â· `docs/STATUS.md` Â· `renderers/web/js/changelog.js`
> and the published mirror. `data/residents/index.json` is deliberately untouched: it carries
> person ids, not names, which is the point the naming tool's own closing comment makes.

`tools/generate_inferred_names.py` said of itself, before this parcel: *"Assignment is DETERMINISTIC, from a hash of
the person's id. Re-running produces the same townâ€¦ nobody has to wonder whether a name drifted."*
The first clause is what the code was built for and the second is not what it does. Pass two deals
each `(community, sex)` bucket round its pool **by index** â€” deliberately, to stop four unrelated
households sharing a surname â€” so a person inserted into a bucket shifts every name after them.
Measured on T-A2h: **two new people renamed 25 of the 94** reconstructed residents.

Nothing about that is a provenance failure â€” every name is invented, graded `reconstructed`, and
re-derives under `--check`. It is a churn and a documentation defect, and it compounds: every
future block parcel will rewrite a quarter of the town's invented names as a side effect, which
buries the parcel's real diff and makes a genuine drift harder to see.

**The likely fix** is to keep the anti-collision property while making it insertion-local: give
each person a deterministic permutation of the pool from their own id and, walking people in
stable hash order, take the first pair not already claimed. An insertion then only bumps the
people it actually collides with. That is a **one-time rename of the whole layer** in the PR that
does it, which is why it belongs in its own parcel with its own liberty note rather than riding
along with a block.

**Files:** `tools/generate_inferred_names.py` Â· `data/residents/households/*.json` Â·
`data/residents/index.json` Â· `docs/ROADMAP.md`

**Acceptance:** adding one household to the programme renames only the people who collide with it,
demonstrated by measurement in the PR; `tools/check.sh` green; no grade moves and no `name_basis`
loses its pool citation.

**Measured a second time by T-A5 (2026-08-14):** a **one**-household insertion renamed **17 of the
33** carried-over invented persons in the household files it touched, and dragged 24 files into a
diff whose real content is one addition. Two independent measurements at the same rate; the "buries
the parcel's real diff" paragraph above is now demonstrated rather than predicted.

### K21 â€” the adoption tests are silent, not negative, for four trades Â· **DONE 2026-08-15**

**The answer was the first of the two the parcel offered, and it was not close.** Every one of the
31 buildings this layer raises was dealt a crosswalk family by the programme, and every one has
always *said* so in prose: the footprint note reads "a 16 x 22 ft rectangle from the **D3** family
band", and each form value cites the same band. What no record carried was the band as a **value**.
So there was nothing to decide â€” the assignment is a transcription of a string committed in two
other places, which is why **it owes `docs/LIBERTIES.md` nothing**: a liberty is an invention, and
writing down what was already committed invents nothing. The second branch (records deliberately
outside the typology, rule 6 gaining a fourth clause) was never reached, and rule 6 gains **no new
clause** â€” a trade whose families are now readable can still fail the test.

**What it measured, before and after.** Of 29 census trades, **four resolved nothing**
(`brickmaker`, `packer`, `sawyer`, `wheelwright`) and **eight resolved partly** â€” 17 households
stood on 31 roofs that named no family. After: **29 of 29 trades resolve, across 44 trade-family
pairs**, and the two sawyer households T-A5 refused now read D3 and D2 â€” facts a parcel can check
rather than a question it could not ask.

**The gate is the durable half.** `tools/generate_inferred_households.py` now fails if any roof a
household *lives or works in* names no family in the crosswalk, over both links rather than the
dwelling alone â€” a shop's family is as much a claim about the town as a cottage's. A test cannot go
silent again without a gate saying so, which is the same medicine T-A4's `deferred` gate applied
one level down.

**The suspicion in the parcel's own Watch note is refuted, and the refutation is the useful part.**
`inf_sawyer_dwelling_b` masses as an `outbuilding` while `_a` masses as a `frame_dwelling` because
**they were dealt different families** â€” D3 and D2 â€” and each resolves through its own family's
committed placeholder archetype. The programme says so in the record's own existence note: the
second sawyer's roof is "a plank dwelling of the schedule's D2 shanty family, which is what the
meanest end of the building trade lived in". Two dwellings of one trade massed as different kinds
of thing is the deliberate claim, not a defect. **The real archetype split is elsewhere and the
Watch note pointed at the wrong record:** five W4 shops, one family, are massed two ways â€”
`inf_shoemaker_shop`, `inf_tailor_shop` and `inf_barber_shop` as `frame_storefront` at a 3.25 m
eave, `inf_gunsmith_shop` and `inf_harness_shop` as `outbuilding` at 2.05 m. All five are
one-storey, so W4's own licence for the storefront massing ("acceptable only for one-storey
massing; two-storey shop-house variants need dwelling/storefront openings") does not explain it.
That is **K25**, with the larger finding it opened.

**Two side effects, both caught by gates rather than by reading.** `tools/reconcile_665.py`
classified a record by whether it carried a reconstruction block at all, so all 31 moved from
`inferred_household_programme` into `generated` â€” totals unchanged, attribution wrong, which is
precisely the kind of thing a total hides; it keys on the status now. And `compile_scene.py` sent
every reconstruction-block record to the anonymous-infill dossier, which would have put a visitor
who clicked a building raised for one argued household in front of a write-up about aggregate
count-units; the household layer has its own dossier and now points at it. That link is dead on the
live site for every building on the site â€” see **K26**.

**Files:** `tools/generate_inferred_households.py`, `tools/compile_scene.py`,
`tools/reconcile_665.py`, `data/structures.schema.json` (the block gains an `inferred_household`
status and an `occupation`; `sequence` and `inventory_class` are required of the anonymous status
only, because a bespoke roof has no parcel slot and inventing one would be a claim),
`data/reconstruction/1835_inferred_household_programme.json` (rule 6 records the resolution),
31 structure records + their sidecars.

<details>
<summary>The parcel as it was written</summary>

**Phase:** lane 2, data only Â· **Runner:** improve-runner (no Blender)

Rule 6 of the household programme's `method` list now has three tests, and the second asks whether
the roof's family is one this layer already houses that trade in. **For four trades that question
has no answer.** `brickmaker`, `packer`, `sawyer` and `wheelwright` are housed exclusively in
bespoke `inf_*_dwelling_*` records raised by the inferred-residents parcel, which carry no
`reconstruction.family` field at all â€” they were built to order against the census rather than
dealt off the roof programme. Eight further trades (blacksmith, boatman, carpenter, cooper, grocer,
labourer, mason, teamster) are partly so, and for those the test can still be answered from the
households that do stand on a family-bearing roof.

**Why it is not merely tidiness.** T-A5 met the case head on: the two sawyer households stand on
`blk_randolph_market` itself, and the sawyer argument's *"the smallest number that answers the
demand"* passes test 1 cleanly. The trade was refused adoption because test 2 could not be
evaluated, not because it was evaluated and failed. **A refusal this project cannot distinguish
from an unanswerable question is the same defect T-A4's `deferred` gate was written to close**, one
level up.

**What is owed.** Decide which of two things is true and say so: either each bespoke inferred
dwelling can be assigned the crosswalk family its committed footprint and form already sit inside â€”
in which case assign them and the test answers itself â€” or those records are deliberately outside
the family typology, in which case rule 6 needs a fourth clause naming the silent case and stating
what happens in it. **Do not simply grant the silent trades a pass**: that would let a census grow
on the strength of a missing field.

**Watch:** `inf_sawyer_dwelling_b` resolves through the `outbuilding` archetype while `_a` resolves
through `frame_dwelling` â€” two dwellings of one trade massed as different kinds of thing. Worth
looking at while in the file; it may be the same root cause and it may be a second finding.

**Files:** `data/reconstruction/1835_inferred_household_programme.json` Â·
`tools/generate_inferred_households.py` Â· `data/structures/inf_*_dwelling_*.json` Â·
`docs/LIBERTIES.md` Â· `docs/ROADMAP.md` Â· `docs/STATUS.md`

**Acceptance:** every trade in the occupation census either resolves test 2 or is named as a case
rule 6 explicitly handles; `tools/check.sh` green; `tools/audit_confidence.py --strict` green; no
household is added by this parcel.

</details>

### K25 â€” the invention is not bounded by the specification it cites Â· **(a) DONE 2026-08-15 Â· from K21 Â· (b) NEEDS THE BAKE**

**Phase:** lane 2 for (a), and (b) NEEDS THE BAKE Â· **Effort:** M

**(a) DONE 2026-08-15 â€” it is 98 values, not 54, and 24 causes, not 98.** The parcel was
scoped from an eave count taken on 193 records. Measured properly â€” every reconstructed
record in the dataset, and every form value the crosswalk authors a testable band for â€”
**1135 values were tested against a band and 98 are outside it, on 80 of 249 records**:

| field | tested | outside | near the edge |
|---|---:|---:|---:|
| eave (`wall_height_m` vs `eave_ft`) | 249 | **54** | 46 |
| roof pitch (vs the `roof` rise:run) | 207 | **38** | 38 |
| storeys + loft (vs `levels`) | 181 | **4** | 1 |
| footprint (vs `footprint_ft`) | 249 | **2** | 0 |
| roof form (vs the `roof` prose) | 249 | **0** | â€” |

The eave figure of 54 survived the widening by coincidence; T-V1(a)'s 40 is its
anonymous-layer half (40 + 14 household). **Roof pitch had never been measured by
anything**, and it is the second-largest fault in the dataset's provenance.

**The 98 are 24 causes.** Every offender is one of a handful of archetype constants
landing on a family whose band nobody checked it against â€” 13 distinct (family, value)
pairs hold all 54 eaves and **six values hold all 38 pitches**:

| | value | band | records |
|---|---|---|---:|
| eave | 2.78 m = 9.12 ft | D3 8â€“9 ft | 20 |
| eave | 2.05 m = 6.73 ft | D2 7â€“8 ft | 10 |
| eave | 2.05 m = 6.73 ft | W4 9â€“18 ft â€” **the worst, +2.27 ft** | 3 |
| pitch | 18.0Â° = 3.90:12 | D2 4:12â€“8:12 | 21 |
| pitch | 32.0Â° = 7.50:12 | A2 8:12â€“12:12 | 9 |
| pitch | 38.0Â° = 9.38:12 | H2/H3 6:12â€“9:12 | 4 |

**Seven metre values account for all 54 eaves** â€” 2.05, 2.75, 2.78, 3.25, 5.05, 5.20,
5.35 â€” which is the archetype table, not a measurement of anything.

**Pitch has its own mechanism, and it is a unit mismatch.** The crosswalk authors
rise:run; the generator authors whole degrees. 4:12 is 18.435Â°, and the shed constant is
18.0Â°, so **21 D2 sheds are 0.10 of a 1:12 step under a floor they would have cleared if
the value had been authored in the band's own units**. All 38 pitch offenders are within
one step. That is the diagnosis, not a defence â€” and it tells (b) exactly what to do:
author the pitch from the band's rise:run rather than from a degree constant.

**The sub-1-ft decision, which (a) owed: they are failures.** 46 of the 54 eaves are
within a foot and every pitch is within a step, and nearness is exactly what a retyped
constant looks like â€” 2.78 m clears D3's 9 ft ceiling by 37 mm because the frame-dwelling
archetype builds 2.78 m walls, not because anyone measured a cottage. A tolerance wide
enough to forgive that is wide enough to forgive a third of a D3 band, and it would
forgive the fault the parcel exists to name. The only slack in the tool is 1.5 mm for the
metre round-trip; five footprints sat half a millimetre over an edge and are exact whole
feet in the source, so they are not counted.

**And a second fault the parcel did not know it had.** The same sentence is attached to
values the crosswalk says nothing about at all: **`paint` on 227 records, 220 of them
against a family that never mentions paint; `board_gap_m` on 99 against a specification
that names no board gap anywhere; `chimneys` on 150, 93 of them silent.** A note citing a
band that does not speak to the value is a different fault from a value outside its band â€”
worse in kind, since there is no band to be inside â€” and the instrument that finds it is a
keyword over the family's authored strings, so it is **reported and not gated**. It wants
its own parcel; see **K33** below.

**What shipped.** `tools/measure_band_claims.py` â€” census, `--strict` (the assertion (b)
must turn green; it exits 1 today) and `--gate` (a ratchet against the committed census in
`tools/band_claims_baseline.json`, on every `check.sh`). Both halves of the ratchet were
broken on purpose and proved to fail before being trusted: planting a 4.9 m D1 wall is
caught as NEW, and repairing `recon_1835_north_d3_002` without re-writing the baseline is
caught as an unrecorded repair. **The fault may shrink and may not grow.** No dimension
moved; the strict assertion is red on purpose and `check.sh` runs the ratchet, because a
permanently red dev gate would block every unrelated parcel behind it.

**(b) is blocked exactly where T-V1(b) is blocked.** Every offender is on a parcel whose
meshes are canonical Blender bakes; changing a dimension stales the GLB, `validate.py
--all` fails a stale GLB, that validator is the dev gate, there is no Blender on the
improve runner, and `chicago-4d-bake.yml` bakes from `dev`. The repair cannot pass the
gate it must pass to reach the branch the bake reads. T-V1(b)'s three routes are (b)'s
routes; choosing one is the owner's.

---

*The original parcel description follows, with its 193-record numbers left as written.*

Every reconstructed roof carries the same sentence on every form value: *"Type-level choice within
the D3 band in the reconstruction specification."* For **54 of 193** records the value is not in
that band. Measured against `key_geometry_parameters` in
`data/reconstruction/1835_family_archetype_crosswalk.json`, reading `wall_height_m` as the eave the
placeholder massing builds it as:

| layer | records | outside | worst |
|---|---:|---:|---|
| anonymous infill (`recon_1835_*`) | 162 | **39** | F2 at 17.6 ft against 19â€“23 |
| inferred-household (K21's 31) | 31 | **15** | W4 at 6.7 ft against **9â€“18** |

**The root cause is one line, and it is not a typo.** `inferred_form()` in
`tools/generate_inferred_households.py` â€” and its counterparts in the anonymous generators â€” choose
every form value from the **archetype**, consulting the family only for a handful of special cases.
So `outbuilding` hands out a 2.05 m wall whether the family band asks for 7â€“8 ft (D2, near enough)
or 9â€“18 ft (W4, out by a third of the band's floor), and the note attached to that value cites the
band regardless. **Fifteen of the 54 are within 1 ft and read as rounding** (D3 at 9.1 ft against a
band ending at 9.0). The other end is not rounding: `inf_laundry_north` is 280 sq ft against an A5
band of 48â€“192, and `inf_sawpit_shed` is 720 against W5's 792â€“2160.

**Why it outranks a tidy-up.** A note that cites a band is a provenance claim â€” it says the
invention is *bounded by the specification*, which is the whole defence for inventing it. Where the
value is outside the band the note is not merely imprecise, it is **wrong about its own source**,
and it is wrong on 54 buildings at once.

**(a) land the failing measurement.** A gate that reads each form value against its family's
committed band and fails, committed RED with the numbers above quoted, plus the decision about the
sub-1-ft cases (widen the tolerance and say why, or accept them as failures). Data and tools only;
no geometry moves. **(b) turn it green** takes (a)'s numbers as the baseline. Some fixes are a
number in a table; any that changes a wall height changes the massing and **needs the bake**, so
(b) ships the data half and says so.

**Do not fix this by widening a band.** The bands are the specification's, not this project's, and
a band widened to admit the value it was supposed to bound stops being evidence. Where a value
genuinely belongs outside its band, the record's note must say so in its own words instead of
citing a band it does not sit in.

**The W4 split rides along.** Five W4 shops, one family, two massings (three `frame_storefront` at
3.25 m, two `outbuilding` at 2.05 m) and all five one-storey, so the family's own licence for the
storefront does not explain it. Decide which is right for a one-storey artisan shop and make the
five agree, or record why a barber's shop and a gunsmith's are different kinds of building.

### K33 â€” the note cites a band for values the specification does not bound Â· **DONE 2026-08-15 Â· 623 values, and 42 of them nothing could have found**

**Phase:** lane 2 Â· **Effort:** S to decide, M to apply Â· data and tools only, no bake

**DONE 2026-08-15 â€” it is 623 values on 227 of 249 records, and the decision is route 2:
split the note.** The box below scoped it from the prose census (581). The true figure is
**623**, because the census could only ask its question of the fields it had classified as
prose, and **42 `roof_pitch_deg` values cite a band on five families whose roof line is
"gable or shed"** â€” a form with no slope in it. Those were invisible to K25(a) for a
structural reason worth keeping: **a value with no band is never tested against one**, so
the banded half of the tool walked straight past the very records where the fault is total
rather than partial. The generous keyword instrument was not the only floor in the census;
the classification itself was.

| field | repaired | field | repaired |
|---|---:|---|---:|
| `paint` | 220 | `door` / `door_side` | 37 each |
| `chimneys` | 93 | `bays` | 35 |
| `board_gap_m` | 69 | `porch` | 23 |
| `plan` | 46 | `goods_door` / `goods_door_side` | 8 each |
| **`roof_pitch_deg`** | **42** | `gallery` / `shopfront` | 4 / 1 |

**The decision, and why route 2 rather than route 3.** Route 1 (extend the crosswalk) would
author evidence rather than record it and is refused. **Route 3 â€” grade these a level lower
â€” is not available at this project's price, and the reason is mechanical: the confidence
FLOATS are hashed into `generators/mesh_inputs.py`'s input recipe.** Regrading 623 values
would stale 249 committed GLBs, and that is the identical wall T-V1(b) and K25(b) are stuck
behind. **Prose is not hashed.** So route 2 is both the honest repair and the only one that
lands without a bake â€” and that coincidence is worth naming, because next time it will not
be a coincidence and somebody will be tempted by the cheap one anyway.

**What the note says now.** It negates the paragraph above it rather than quietly dropping
a citation. Every one of these values is prefixed by a generator-level lede reading *"the
spec is cited because the invention is bounded by it"* â€” the exact claim that is untrue
here â€” so dropping the trailing citation alone would have left the false impression intact
and made the repair invisible. The replacement opens `NOT BOUNDED BY THE SPECIFICATION,
and the sentence above about the invention being bounded does not hold for this value`,
names the family and the field, and says what the value actually is: the reconstruction
generator's type default. Each parcel's own closing clause ("it is not evidence for this
anonymous North Division instance") is preserved verbatim.

**What shipped.** `tools/band_notes.py` â€” the single predicate for *may this value cite the
band*, imported by all five generators that author the sentence and by
`tools/measure_band_claims.py` that audits it. One file, because `family_bands.py` exists
for exactly this reason and its docstring says so: the same arithmetic in two files, and
only one of them ran. The assertion is now in `--gate` and `--strict` and is **absolute â€”
no baseline, no allowance**, in deliberate contrast to K25's ratchet beside it, because
this repair costs prose and cannot block anything. Proven in three directions before being
trusted: **red at 623 against the pre-repair data**, **green at 0 after**, and a planted
fresh offender caught. It also fails on a citation attached to a field neither table has
classified, so the next invented fitting cannot inherit a citation by default.

**What did NOT change, and the residual.** No value moved and no geometry moved; 623 note
strings and nothing else. Two things are left open on purpose:

- **`sources` still lists the spec on these values.** The note now says the spec does not
  bound them, while the machine-readable `sources` array still cites it. The spec IS the
  source of the family assignment that produced the archetype default, so it is not simply
  wrong â€” but the two fields no longer say the same thing, and that is a smaller version of
  this same parcel's subject. It wants a decision, not a sweep.
- **The prose tier keeps its citation.** Where the crosswalk speaks without bounding â€”
  `construction` as "hewn or round logs with chinking", `variants` as "2/3 bays; external
  chimney" â€” the citation stands. K25(a) drew that line when it separated the prose fields
  from the banded ones and K33 does not reopen it. A parcel that wants to argue the middle
  tier down is a new one, and it should read `PROSE_KEYWORDS` first: the instrument is a
  keyword and generous by design.

---

*The original parcel description follows, with its 581-value prose census left as written.*

K25(a) measured the values the crosswalk *does* bound. This is the other half, and it is
worse in kind: **`paint` on 227 records carries "Type-level choice within the D3 band",
and 220 of those families never mention paint at all.** There is no band to be inside.
The census, printed by `tools/measure_band_claims.py` on every run:

| field | records citing a band | of which the family's authored geometry says nothing |
|---|---:|---:|
| `paint` | 227 | **220** |
| `chimneys` | 150 | 93 |
| `board_gap_m` | 99 | **69 â€” and the specification names no board gap anywhere** |
| `plan` | 103 | 46 |
| `door` / `door_side` | 99 | 37 each |
| `bays` | 103 | 35 |
| `porch` | 35 | 23 |
| `gallery` | 4 | 4 |
| `construction`, `cladding`, `gable_front` | 249 / 21 / 21 | 0 |

**The instrument is a keyword** over the family's `key_geometry_parameters` strings, and
it is deliberately generous â€” a hit means the specification *mentions* the thing, not that
it bounds it. So the true count is a floor, and the field is reported rather than gated
until the decision below is made.

**It is a decision before it is a fix.** These values are not wrong; a board gap of 12 mm
on an unpainted plank shed is a perfectly ordinary invention. What is wrong is the
*citation*: the note says the value is bounded by a specification that does not speak to
it. Three candidates, and the second is the honest cheap one: extend the crosswalk so the
specification actually authors these (large, and it would be authoring evidence rather
than recording it); **or split the note â€” cite the band only where a band exists, and say
plainly "the specification does not speak to this; the value is the archetype's default"
where it does not**; or grade these values a level lower than the ones the band covers.

**Whatever is chosen, `tools/measure_band_claims.py` gains the assertion** â€” a value may
cite a band only if the family authors one for it. Until then the census prints and does
not fail, and this box says why.

### K34 â€” what `review_required` actually blocks Â· **DONE 2026-08-16 Â· one record claimed the flag in prose and never carried it, and the block read buildings only**

**Phase:** lane 2 Â· **Effort:** S to measure, S to gate Â· data, tools and docs only, no bake

AGENTS.md puts one constraint above the work â€” *the final removal of the Potawatomi from
Chicago occurred in August 1835, inside this project's first target year* â€” and gives it one
mechanism: **`review_required: true` on any record blocks a scene from being marked
`released`.** Nothing had ever measured what that sentence covers. It covers **9 structures
of 332**; it did **not** cover the **7 households of 173** that carry the same flag, nor the
person layer that carries the same two fields.

**FINDING 1 â€” `hh_caldwell_billy` says it carries the flag and never has.** Its
`research_note` has read *"It carries review_required so that no scene containing it can be
marked released before the consultation the project has committed to"* since the record was
written, and `git log -S` finds no commit in which the field was ever `true`. The sentence is
the same one `hh_robinson_alexander` carries, where both fields ARE set. Billy Caldwell â€”
Sauganash, the agency's interpreter, the namesake of the town's best-known tavern â€” is the
one household in this dataset whose own text quotes Andreas putting its subject at the head
of the march to the Missouri. **Both flags are set now, on the record's own committed text
and on nothing new**, and the note records that they were false and that the paragraph above
them said otherwise. `touches_removal â‡’ review_required` could not catch it because
`touches_removal` was false too.

**FINDING 2 â€” the release block was `data/structures/` alone, and the households were safe by
coincidence.** `validate.py`'s scene gate built its `blocked` list out of structures while
its own household-side error promised that *"any record touching it blocks a scene from being
marked released"* â€” a consequence that did not follow. The seven flagged households were
covered anyway because **all 11 of their `lives_at`/`works_at` links land on a structure that
is flagged too**. Nothing required that. A flagged household with a null `lives_at` and an
unflagged workplace â€” or with no links at all â€” passed clean, and the self-test that proves
it is committed.

**FINDING 3 â€” the same sentence read the other way is a deliberate, honest NO.**
`chappel_infant_school`, `walker_meeting_house` and `watkins_school_house` each say
*"review_required is set false â€¦ but the call is worth a second opinion"*, and each is false.
That is the reason assertion 1 tests **both directions** rather than "prose mentions the
constraint â‡’ set the flag": three settler buildings that reasoned their way to `false` in
writing are not defects, and a gate that could not tell them from finding 1 would have been
a gate arguing for its own conclusion. **Three of the nine flagged structures â€” `beaubien_barn`,
`clybourn_slaughterhouse`, `robert_kinzie_store` â€” state no reason at all**, which is the
open end of this parcel and is left open rather than guessed at: see K35. â€” **CORRECTED
2026-08-28 by K35 / T-0025: it was ONE of the three, not three.** Two of them said it at
this parcel's own commit, in a field this sentence did not read: the barn in `research_note`,
the slaughterhouse in `function.note`. Only `robert_kinzie_store` was bare. The K35 box
below carries the re-measurement and the gate that now holds it.

**WHAT SHIPPED.** `tools/measure_review_constraint.py`, in `check.sh`, with **four absolute
assertions and no ratchet** â€” a ratchet is the instrument for a fault being paid down, and
this is a commitment. (1) a record whose prose claims the flag carries it, and one whose prose
declines it does not; (2) `touches_removal â‡’ review_required` at household AND person level,
the person half never having been asked; (3) the flag reaches the building a constrained
household lives or works in, 11 of 11; (4) **behavioural** â€” `validate_scene` is run against
the real dataset with `released` forced true and the blocked set it names must equal the union
of flagged ids across every layer, so a gate that restated the rule cannot pass while the
validator disagrees with it. Plus `tools/review_constraint_baseline.json`: adding a flag is
free, **clearing one fails** and names what clearing it would mean.

**All four were broken deliberately before the gate was trusted** â€” the Caldwell flag cleared
again, `cobweb_castle` unflagged under three households, a person given `touches_removal`
without `review_required`, and the validator reverted to reading structures only. Each exits
1 with the divergence named; the restored tree passes.

**WHAT IT DID NOT DO.** It moved no building, no household and no coordinate, invented
nothing, and upgraded no confidence. No liberty is owed: `docs/LIBERTIES.md` records
inventions, and nothing here was invented.

**Verified:** `tools/check.sh` green. `SMOKE_VIEWPORT=mobile node tools/smoke_renderer.mjs`
green against the published mirror. The desktop half was not run and is not claimed â€” it
needs ~13 minutes against this harness's 10-minute per-command ceiling (see the run-budget
box at the top of this file). This parcel changes no renderer file and no geometry.

### K35 â€” three records carry the standing constraint and say why nowhere Â· **DONE 2026-08-28 (T-0025) Â· one of the three was bare, and the census that named three had read one field of a record whose reasoning is spread over four**

**Phase:** lane 2 Â· **Effort:** S Â· one data record, one gate, docs â€” no renderer file, no
geometry, no coordinate, no bake

**THE FIRST THING THIS PARCEL DID WAS RE-MEASURE ITS OWN PREMISE, AND THE PREMISE WAS WRONG.**
K34 finished by naming `beaubien_barn`, `clybourn_slaughterhouse` and `robert_kinzie_store` as
carrying the flag with *"no text anywhere in the record"* saying what for. Checked against the
committed bytes at K34's own commit (`23bb280b`), reading the WHOLE record rather than
`research_note`:

| record | at K34's commit | where |
|---|---|---|
| `beaubien_barn` | **said it** | `research_note` â€” *"REVIEW IS FLAGGED for the reason data/structures/jb_beaubien_homestead.json â€¦ give"* |
| `clybourn_slaughterhouse` | **said it** | `function.note` â€” *"flagged for review with the rest of this record's Indigenous content rather than paraphrased away"* |
| `robert_kinzie_store` | bare | â€” |
| `council_house` (never named by K34) | **said it** | `function.note` â€” *"the reason it is flagged review_required: the events the sources attach to this building â€¦ are the removal"* |

So the convention was kept by **eight of nine** structures and not six, the one real gap sat
behind two records that were not gaps, and a fourth record was credited with a silence it never
had. The fault is not carelessness â€” it is the shape of these records. A building's reasoning is
distributed across `function.note`, `position.note`, the per-attribute notes and `research_note`,
and the one place a reader looks for a policy statement is the last of them. **`clybourn`'s
sentence is in the field that names the man: "the Government butcher for the Pottawatomies", a
treaty-provision post.** That is where the reason belonged.

**THE ONE REAL GAP IS CLOSED, AND IT IS CLOSED WITH THE RECORD'S OWN ATTESTED BUSINESS.**
`robert_kinzie_store` is not a shop that happened to stand near Native people: Andreas lists its
keeper among the town's Indian traders (scan p. 235) and among those licensed to sell goods (scan
p. 249), chicagology has it dealing in *"groceries and Indian goods"*, and the record's own `aka`
carries the source's phrase â€” *"R. A. Kinzie, Indian trader"*. The trade that names the building
is the trade the 1833 Treaty of Chicago ended, and the removal it ended in was under way six
weeks after the scene date. The flag was already right; what was missing was the argument, and
the argument was already inside the record in three fields that never said what it implied. The
row agrees: `robinson_caldwell_cabins`, forty-odd metres along the same west-bank frontage,
carries the flag for the same subject. **Nothing was regraded, no confidence moved, no source was
added and the flag was not lifted** â€” lifting it is the claim that the consultation has happened,
which assertion 5 already refuses.

**ROUTE 1, ASSERTED â€” and route 2 is declined with a reason.** K34 left three routes and called
the choice the owner's. The re-measurement decides it: a `review_reason` field would be a SECOND
carrier for text that nine of nine records already write, and a second carrier for the same claim
is the exact shape assertion 1 exists to catch (a record whose prose and whose field disagree).
What the records needed was not a field, it was a reader that reads the record.

`tools/measure_review_constraint.py` gains **assertion 6**: every record carrying the flag, at
every layer, must (a) refer to it in one of the phrasings this dataset uses and (b) name the
subject AGENTS.md places under the constraint â€” both in the record's own prose, wherever in it
they fall. Record-level and not sentence-level on purpose: `cobweb_castle` opens *"THE RECORD IS
FLAGGED review_required BECAUSE OF WHAT THIS BUILDING WAS"* and spends the next two sentences
saying what that was, which is good writing and would fail a same-sentence rule. **K35's own
objection to this route â€” "says something" is not "says why" â€” stands, and is answered the only
honest way: the census PRINTS the sentence it matched under every flagged id.** The gate holds
the shape of the claim; a reader judges the argument, and now has it in front of them without
opening nine files.

    structures       9 flagged of  349
                     clybourn_slaughterhouse
                       why: Andreas elsewhere calls Archibald Clybourne 'the Government
                            butcher for the Pottawatomies' (scan p. 253), a treaty-provision
                            post â€” recorded here because it is what the man was, and flagged
                            for review with the rest of this record's Indigenous content â€¦

**Both halves were broken before the gate was trusted**, in memory against the real dataset: the
flag phrasing scrubbed out of `robert_kinzie_store` (fires â€” *"carries review_required and its own
text never says so"*), and the subject scrubbed out of `council_house` while its flag sentence
stands (fires â€” *"refers to the flag â€¦ and names nowhere the subject"*). The restored tree passes.

**WHAT IT DID NOT DO.** It moved no building, household or coordinate, built no geometry, and
invented nothing â€” `docs/LIBERTIES.md` records inventions and there is none here. It did not give
the visitor anything: a building held under the constraint still says so nowhere on the card a
visitor opens, and the flag reaches the browser only as a console line in `scene-loader.js`. That
is filed as T-0268 rather than smuggled in here.

### K36(a) â€” nothing compared a shipped derivative to the master it came from Â· **DONE 2026-08-16 Â· the site has 75 textures and the repository has none**

**Phase:** kernel (lane 1 side) Â· **Effort:** S to measure, S to gate Â· tools and docs only â€”
no data record, no renderer file, no geometry, no bake

The geometry a visitor downloads reaches them along four links:

    data/  ->  assets/gltf/  ->  assets/web/  ->  site/chicago/4d/assets/web/

Link 1 is gated â€” `validate.py --stale` recomputes every master's input hash. Link 3 is gated â€”
`check_published.mjs` asserts the mirror is byte-identical to its source, and exists because
R-BUG3c-b cost three parcels discovering that *"nothing else in this project measures a
published artefact against its own source"*. **Link 2 was gated by nothing at all**, and it is
the link with the moving parts: two `gltf-transform` passes whose own comments in `tools/bake.sh`
record what has already come out of them â€” *"a bug that collapsed every building to a two-metre
box shipped past a fully green gate â€” twice"*, and a `--texture-compress ktx2` flag that
*"silently turned every derivative into an uncompressed copy of its master, in every
environment, since this step was written"*. Both were found by a person reading the script.
This reads the bytes.

**FINDING 1 â€” the town on the site is textured; the town in this repository is not.**
`optimize`'s palette pass folds the named materials of **38 of 334 assets** into one
`PaletteMaterial001` carrying generated PNGs. **75 textures exist in `assets/web/` that exist in
no master**, and the material NAMES they replace â€” `log`, `chinking`, `board`, `roof`, `dark`,
`interior` â€” do not reach the browser at all on those 38.

**FINDING 1b â€” the split is a COUNT and it is exact.** Every master carrying **five or six**
materials is faulted (31 `log_dwelling`, 6 `outbuilding`, 1 `frame_tavern`); every master
carrying **four or fewer** is clean, 296 of 296. Nothing about logs: that is the palette pass's
own documented minimum of five materials, and its output is named `PaletteMaterial001` by the
tool. The consequence is the reason this is a ratchet rather than a curiosity â€” **275 assets sit
exactly one material short of the threshold**, so an archetype that gains a fifth surface moves
every asset it paints across it. That is what R-W2b does.

**FINDING 2 â€” R-W2a's material sheet inventories the masters under the words "the shipped
GLBs".** `docs/RESEARCH/materials.md` reasons in its own preamble that *"the source and the
shipped bytes have disagreed in this project before â€¦ a sheet that inventories intentions is
worth nothing to a bake"* â€” and then measures `assets/gltf/**/*.glb`, which is the source side
of exactly that disagreement. Its **"nothing in the town carries a texture of any kind"** is
true of what is baked and false of what is served. Corrected in place, with a Â§0 note and a
pointer here; **none of its five findings moves**, because all five are about what the
generators paint and that is unaffected. What DOES move is R-W2b's plan: it wires an atlas onto
material names that the publish path deletes on 38 assets, and it now knows that before it
starts rather than after a bake.

**FINDING 3 â€” 90 assets ship uncompressed, and the only instrument that could notice is a
25 MB budget.** They are exactly the 90 pure-Python placeholders, which
`generators/inferred_placeholder.py` writes byte-identically into both trees; the 244
Blender-baked assets compress **5.29Ã—**. It is 508 KB and **11.4 % of the payload** â€” not a
problem today, and it is now a printed census line rather than a warning in a nightly log.

**WHAT DOES NOT MOVE, MEASURED RATHER THAN ASSUMED.** Triangle counts are identical across all
334 pairs, so `--simplify false` has held in fact and not only in the script. Node names, the
`structure_id`/`phase_id` extras and mesh names all survive, so the sidecar join key is intact.
`_CONFIDENCE` â€” how a visitor is told which parts we made up â€” reaches the site on every asset
carrying it. The world bounding box agrees to at worst **2.63 rungs** of an asset's own extent
(0.107 mm on a 2.7 m shed); the terrain's 82.8 mm is **1.08 rungs** of its 5,020 m box, the same
quantity R-W6 committed as a 76.6 mm lattice, which is the cross-check that the two
measurements are of the same thing.

**WHAT SHIPPED.** `tools/measure_web_derivatives.py`, in `check.sh` at **0.2 s and with no
decoder** â€” the shipped positions are `EXT_meshopt_compression` payloads this project cannot
decode here, and every claim above is answerable from the glTF JSON chunk instead, because the
spec requires POSITION accessors to carry `min`/`max` and a quantised file carries its
dequantisation in the node's own TRS. **Five absolute assertions** â€” bijection both ways,
triangle count, node/mesh identity, the attributes `docs/GLB-CONTRACT.md` names, and a bounding
box within **four rungs** (`extent / 65535`) of the master's. The bound is a lattice rather than
a millimetre count because the assets differ in size by three orders of magnitude, and a
building collapsed to a two-metre box is thousands of rungs, not four. **One ratchet** â€”
`tools/web_derivative_baseline.json`, the 38 â€” which fails on a new offender, on a banked one
whose loss has grown, AND on a banked one that is now clean and has not been banked as repaired.
TEXCOORD_0 is dropped from 204 masters on the way and that is reported, not gated: the UVs are
unused on an untextured asset and the prune pass is right to drop them.

**All eight failure modes were broken deliberately before the gate was trusted**
(`--self-test`, in memory, against the real tree): a derivative with no master, a master with no
derivative, a simplified mesh, a lost `structure_id`, a lost `_CONFIDENCE`, a collapsed
bounding box, a new material fault, and a repaired one left in the baseline. Each fires; the
clean tree passes.

**WHAT IT DID NOT DO.** It moved no record, no coordinate and no byte of geometry, invented
nothing and upgraded no confidence. No liberty is owed â€” `docs/LIBERTIES.md` records inventions,
and this parcel measures.

**Verified:** `tools/check.sh` green (with the new step). `SMOKE_VIEWPORT=mobile node
tools/smoke_renderer.mjs --published` green. The desktop half was not run and is not claimed â€”
it needs ~13 minutes against this harness's 10-minute per-command ceiling (see the run-budget
box at the top of this file). This parcel changes no renderer file and no geometry, so the
scene it would exercise is byte-for-byte the one the last run smoked.

### K36(b) â€” give the site back the material names it was baked with Â· **DONE 2026-08-16 Â· the palette pass was not buying draw calls, it was spending them, and four of the eight anchors were over budget**

**Phase:** kernel (lane 1 side) Â· **Effort:** Sâ€“M Â· tools, docs and 38 derivative files â€”
no data record, no renderer file, no master, no bake

**FINDING 1 â€” the flag's own justification is false here, and it is false by 40 batches.**
The palette pass merges materials *inside one file*, which is a saving when the renderer
batches per file. This one does not. `materialKey()` in `renderers/web/js/buildings.js`
includes `m.map?.uuid`, and a GLTFLoader mints a fresh uuid per loaded texture â€” so an asset
arriving with its own generated palette map **cannot join any batch, not even another palette
asset's**. Measured on the mirror: the 38 faulted assets shipped as **40 single-building
batches** on top of the town's 16 (40 rather than 38 because `sauganash_hotel` came out with
three `PaletteMaterial`s, its glass and shutters refusing the merge), and the published town
drew **56 batches where R-W5a's committed number is 16**. With the pass off: **56 â†’ 16**, every
one of the 40 folded back into the roughness buckets, `textures` in memory 55 â†’ 41, shader
programs 15 â†’ 12.

**FINDING 2 â€” the answer to K36(b)'s own "second question" is: R-W5a's numbers were taken on
the SOURCE tree.** Its *"no map of any kind"* is true of what is baked and was never true of
what is served, exactly as K36(a)'s finding 2 was of R-W2a's sheet. That is the same mistake
twice in three days, from two different parcels, and the reason is the same both times â€” the
instrument was pointed at `assets/gltf/`. `tools/measure_shipped_batches.mjs` is pointed at
the mirror by default and prints which tree it read, so the next parcel cannot make it a third
time. **R-W5a's finding stands** â€” the collapse from 47 to 16 is real and is what the 40 now
fold back into â€” but its "16 batches" was never a statement about the site.

**FINDING 3 â€” and this is the one that matters to a visitor: four of the eight scene anchors
were OVER the 80-call budget on the published site.** A batch holding one building is culled
with that building, so the cost is paid per pose and it is worst where the town is densest.
Measured at 1280Ã—800 through the renderer's own `goTo`, before â†’ after:

| anchor | before | after |
|---|---|---|
| green_tree | **102** | 70 |
| forks | **96** | 68 |
| from_above | **84** | 63 |
| south_water | **82** | 69 |
| lake_market | 71 | 63 |
| sauganash_wing | 68 | 61 |
| first_post_office | 66 | 60 |
| sauganash | 62 | 59 |

**None is over budget now, and the worst falls 102 â†’ 70.** Nothing had ever measured this,
because the smoke reads the counter at the pose it happens to be standing in and
`critic_shots.mjs` reports draw calls per station without asserting on them.

**WHAT IT COST.** The 38 derivatives go **318,540 â†’ 505,932 bytes (+187,392, +58.8 %)** â€” 197
named materials take more room than 75 generated PNGs â€” which is **+4.1 %** on a 4.5 MB tree
against a 25 MB budget. `material identity: 334 of 334` now, and the K36(a) ratchet is rebanked
empty; it will fail loudly on the 39th.

**WHAT SHIPPED.** `tools/web_derivatives.sh` â€” the web-derivative step lifted out of
`tools/bake.sh` **whole and unchanged apart from the flag**, so a Blender-free runner can
regenerate derivatives from the committed masters and MEASURE them. That was the structural
problem behind this parcel: link 2 could be *found* broken by K36(a) but not *repaired* without
a nightly. `BAKE_PALETTE=1` restores the old behaviour for re-measurement; nothing sets it.
Plus `tools/measure_shipped_batches.mjs` (one page load, seconds, no captures) and the
`docs/GLB-CONTRACT.md` bullet that recommended the pass, now struck through with the numbers.

**THE CONTROL, and it is what makes the 38 changes attributable.** Regenerating all 334
derivatives under `BAKE_PALETTE=1` reproduces **243 of 334 byte-for-byte**, md5 for md5,
including **all 38** faulted ones. So the difference in the shipped files is `--palette false`
and not a change of tools. **The other 91 are two findings this parcel did NOT fix and did not
hide** â€” see K37 and R-W6(b) below; both are real, both are outside a parcel about materials,
and neither is safe to "tidy" without a gate looking at it.

**WHAT IT DID NOT GATE, deliberately and worth someone's parcel.** Finding 3 is measured and
not asserted: nothing fails if an anchor goes back over 80. `measure_shipped_batches.mjs` costs
a page load (~40 s), which is too much for `check.sh` at 14 s, so the right home is the smoke â€”
it already has a page open and already reads `stats().drawCalls` at whatever pose it is
standing in. **Walking the eight anchors and asserting each is the missing gate**, and it is a
few lines rather than a parcel's worth of work.

**WHAT IT DID NOT DO.** It moved no record, no coordinate, no master and no triangle â€”
triangle counts are asserted identical across all 334 pairs by the K36(a) gate, which passes.
It invented nothing and upgraded no confidence. No liberty is owed.

**Verified:** `tools/check.sh` green. `SMOKE_VIEWPORT=mobile node tools/smoke_renderer.mjs
--published` green. The desktop half was not run and is not claimed â€” ~13 minutes against this
harness's 10-minute per-command ceiling (see the run-budget box at the top of this file) â€” but
the desktop draw-call numbers in finding 3 ARE measured at 1280Ã—800, by
`tools/measure_shipped_batches.mjs`, which is the quantity the desktop half would have been
run for.

### K37 â€” 90 derivatives were never put through the step that produces them Â· **DONE 2026-08-16 Â· the passthrough is right, the rule is not "placeholder", and three assets were going the other way**

**Phase:** kernel Â· tools, docs and three derivative files â€” no data record, no renderer
file, no master, no bake, no record moved, no confidence touched.

**FINDING 1 â€” the answer is the passthrough, and the margin is not close.** The step was
run over all 90 flagged placeholders, which is the measurement the parcel asked for:
**520,700 â†’ 628,028 bytes, +107,328 (+20.6 %)**, and **88 of the 90 grow**. `meshopt`
writes a compression header, a buffer-view table and an index buffer, and on a
sixteen-to-sixty-triangle shed those cost more than the compression saves. K36(a) read
the 90 as an anomaly; K36(b)'s control read them as a non-reproduction; both were true
and **neither was a rule**. Committing them squeezed would have grown the payload to buy
nothing.

**FINDING 2 â€” and this is the one the parcel did not expect: the class predicate is wrong
in BOTH directions.** "Placeholder â‡’ master copy" fits the tree exactly today â€”
`kind: placeholder` is 90 of 90 uncompressed, `kind: generated` was 244 of 244
compressed â€” and it is a coincidence of write order, not a rule:

| | bytes | Î” |
|---|---|---|
| `fort_dearborn_root_house__cellar_1816` | 4,488 â†’ 4,812 | **+324 (+7.2 %)** |
| `lake_house_construction__shell_1835` | 5,620 â†’ 5,860 | **+240 (+4.3 %)** |
| `fort_dearborn_magazine__brick_1816` | 6,236 â†’ 6,460 | **+224 (+3.6 %)** |
| `fort_dearborn_parade__parade_1816` | 5,504 â†’ 4,156 | âˆ’1,348 (âˆ’24.5 %) |
| `recon_1835_blk_randolph_wells_h2_01` (placeholder) | 8,728 â†’ 7,912 | âˆ’816 (âˆ’9.3 %) |
| `recon_1835_blk_randolph_clark_h2_02` (placeholder) | 8,712 â†’ 7,904 | âˆ’808 (âˆ’9.3 %) |

**Three assets that have been through this step on every bake since it was written have
been shipping LARGER than the masters they came from**, and two of the ninety
placeholders compress smaller. Byte size does not predict it either â€” `parade` is 5,504
bytes and wins, `lake_house_construction` is 5,620 and loses; the discriminator is
triangle count against header overhead, and the honest way to know is to run it. So the
rule is **keep whichever file is smaller, measured per asset**, and it is in
`tools/web_derivatives.sh` rather than in a list of names.

**WHAT MOVED.** Three derivatives, replaced by their masters: **âˆ’788 bytes**, and they
now carry exact float positions rather than a quantised lattice. Nothing else. The 90
placeholders are byte-identical to what they were â€” the parcel's own *"do not fix this by
regenerating them"* held, and the measurement is why.

**THE GATE.** `tools/measure_web_derivatives.py` assertion 6, **absolute, bound zero**: no
derivative may be larger than the master it came from. Its `--self-test` grows a
derivative by one byte and confirms it fires, **and grows an epoch mesh by one byte and
confirms it does not** â€” an exclusion nobody has watched hold is an exclusion nobody has
watched.

**THE ONE EXCLUSION, by name and with its number.** `water__e1834_harbor_cut.glb` is
1,352 â†’ 2,096 bytes (**+744, +55.0 %**) and the rule would pass it through. It is not
passed through and it is not banked as a fault: the epoch meshes' bit depth is a
*geometric* decision (R-W6 set `EPOCH_QUANT_BITS` against measured drawn-surface error,
and the ground and waterline are what R-BUG3c, R-BUG4, R-M1a and the road-contrast bands
all measure against), and **R-W6(b) is holding both files** pending the owner's word on
regenerating geometry outside a bake. A payload rule does not get to move the water while
that is open. R-W6(b) inherits the question with the number already taken.

**THE OPEN END, stated rather than tidied.** The two placeholders that compress 9.3 %
smaller are left as master copies, because `generators/inferred_placeholder.py` rewrites
**every** non-superseded placeholder into both trees on every run and would silently undo
them â€” the same write-order coupling that produced this parcel. Fixing it means deciding
whether that generator may seed a provisional derivative at all, which is a generator
change and a separate question. Cost of leaving it: **1,624 bytes**. With the size rule
in place and these three repairs applied, `tools/web_derivatives.sh` reproduces **331 of
334** committed derivatives; the three are those two and `terrain__` (14 bits committed,
16 asked for â€” R-W6(b)).

**A THIRD WRITER OF `assets/web/`, noticed and not chased.** `tools/publish.sh` copies a
master through whenever it is **newer by mtime** than its derivative. That is a
passthrough nothing decided either, it is invisible to this gate (a copy is never larger
than its master), and on a fresh clone mtimes come from checkout order. Worth a parcel's
attention; it is not this one's.

**AND THE GATE'S OWN SELF-TEST HAD BEEN RED SINCE THE DAY BEFORE.**
`measure_web_derivatives.py --self-test` reported **SELF-TEST FAIL** on a clean `dev` from
K36(b) onward: K36(b) repaired all 38 material faults and rebanked the ratchet empty, so
the mutation *"a banked asset was repaired and not banked"* had nothing to mutate and
printed MISSED. Nothing caught it because `check.sh` ran `--gate` and never `--self-test`.
Both are fixed: an inapplicable mutation now prints `skipped`, and `check.sh` runs the
self-test as its own step. The docstring's *"38 of 334 assets fail this today"* was also
a day stale and now says 334 of 334.

**Verified:** `tools/check.sh` green (including the two new steps).
`SMOKE_VIEWPORT=mobile node tools/smoke_renderer.mjs --published` green. The desktop half
was not run and is not claimed â€” ~13 minutes against this harness's 10-minute per-command
ceiling; see the run-budget box at the top of this file. Nothing in this parcel moves a
vertex, a material or a pose, and the three files it does move become *more* geometrically
exact, so the desktop half has no quantity of its own to measure here.

### K37 â€” the parcel as written, kept for the record

K36(a) reported *"90 assets ship uncompressed, and the only instrument that could notice is a
25 MB budget"*, and attributed it to `generators/inferred_placeholder.py` writing the same
bytes into both trees. K36(b)'s control adds the other half: **running the pipeline's own
web-derivative step over those 90 masters does not reproduce their committed derivatives** â€”
it produces different, and *larger*, files. On the sample measured, `4,968 â†’ 6,000 bytes`
(**+20.8 %**), because `meshopt` adds a compression header and index buffer to a file too small
to earn either back.

So the count is exact in both directions and the two halves disagree about which is right:
`tools/web_derivatives.sh` says those 90 should be meshopt-compressed and 21 % bigger; the
committed tree says they should be master copies. **Nothing measures the disagreement**, which
is the same shape of gap K36(a) opened â€” a transformation with a flag in it and no gate.

The decision is small and needs a number, not a preference:

1. measure the payload both ways across all 90 (the sample says the passthrough wins on bytes);
2. decide whether a placeholder derivative is *supposed* to be a master copy â€” if it is, say so
   in `tools/web_derivatives.sh` and skip them there deliberately, rather than by the accident
   of write order;
3. either way, make `tools/measure_web_derivatives.py` assert the rule, so the 91st cannot
   appear silently.

Watch: **do not "fix" this by regenerating them.** It grows the payload and moves 90 files for
no visitor-visible reason. The fault is that nothing states which behaviour is intended.

### K38 â€” `assets/web/` has three writers and the gate on it watched one Â· **DONE 2026-08-16 Â· two masters copied into the payload, +1,212,760 bytes, and the whole gate printed CHECK PASS**

**Phase:** kernel Â· `tools/publish.sh`, `tools/web_derivatives.sh`,
`tools/measure_web_derivatives.py`, `tools/check.sh`, docs. No data record, no renderer
file, no master, no GLB moved, no confidence touched.

**FINDING 1 â€” the fault is real, it was reachable in one command, and every gate this
project owns passed it.** Two compressed masters were `touch`ed and `tools/publish.sh`
run, which is the state the tree reaches whenever `generators/build.py` is run on its
own â€” the exact case the script's own comment says the passthrough exists for:

| | master | derivative before | shipped after |
|---|---|---|---|
| `fort_dearborn_palisade__picket_1816.glb` | 841,836 | 114,768 | **841,836** |
| `dearborn_street_drawbridge__draw_1834.glb` | 557,196 | 71,504 | **557,196** |

**+1,212,760 bytes into the payload**, written into the *tracked* `assets/web/` and
mirrored to `site/`. Then, on that tree: `measure_web_derivatives.py --gate` **exit 0**,
`check_published.mjs` **exit 0**, and the full `tools/check.sh` printed **CHECK PASS**.

**FINDING 2 â€” and it could not have been otherwise, which is the general point.** A
master copied over its own derivative carries the master's triangles (assertion 2), node
names and `extras` (3), contract attributes (4), bounding box to **zero** rungs (5) and
material table (7), and a byte count that is *equal* rather than larger (6). K36(a) wrote
those assertions to watch the transformation `assets/gltf/ â†’ assets/web/`. **They watch
the transformation. They cannot see a file that skipped it** â€” and the whole point of a
gate on a directory is that it holds whatever put the bytes there.

**FINDING 3 â€” it is not three writers, it is three scripts and FOUR passthrough
branches**, three of which are silent:

| writer | branch | decided? |
|---|---|---|
| `tools/web_derivatives.sh` | the size rule â€” compressed file is bigger, keep the master (K37) | **yes**, 93 assets |
| `tools/web_derivatives.sh` | `optimize` failed â†’ `cp "$f" "$out"` | no â€” warns, gated by nothing |
| `tools/web_derivatives.sh` | `gltf-transform` unavailable â†’ copy **all 334** | no â€” warns, gated by nothing |
| `tools/publish.sh` | master newer by mtime â†’ `cp` | no â€” announced, gated by nothing |
| `generators/inferred_placeholder.py` | seeds both trees from the master every run (K37) | no â€” and 90 of the 93 are its output |

The no-tool branch is the widest of them: it takes the payload from **4.54 MB to
20.96 MB**, a 4.6Ã— against a 25 MB budget, and the only instrument that would have
noticed is that budget.

**FINDING 4 â€” mtime was answering a content question, and it is wrong in BOTH
directions.** On a fresh clone of this repository, **334 of 334 masters are OLDER than
their derivatives** â€” not because anything is fresh, but because `git checkout` writes in
index order and `assets/gltf/` sorts before `assets/web/`. So the rule fires on any
rebuild that rewrites a master (true positive, wrong response) and is blind on a clean
clone (false negative, no response). It has never once compared a byte.

**WHAT MOVED.** No asset. **Assertion 8**, absolute in both directions against a set
banked by name in `tools/web_derivative_baseline.json`: 93 decided passthroughs, and a
94th fails whichever writer produced it; a banked one that comes back compressed fails
too, and says to re-bank. Its two `--self-test` mutations both fire. **And
`tools/publish.sh` is no longer a writer of `assets/web/`** â€” it keeps the mtime scan,
moves it above the first write, and **refuses**, naming each stale file and the
`tools/web_derivatives.sh --only <name>` that fixes it. Verified end to end: the same two
`touch`es now stop the publish at exit 1 with the working tree clean.

**THE COST, STATED.** A new placeholder now needs
`measure_web_derivatives.py --write-baseline` in the commit that adds it. That is the
assertion working, not a wart: `generators/inferred_placeholder.py` is the writer of 90
of the 93, and "the generator added one" and "something copied a master through" are the
same bytes. One of them is a decision and it is now written down.

**THE RESIDUAL, and it is K39.** Refusing on mtime is strictly better than copying on
mtime, but it is still mtime: on a fresh clone it will not fire, so a derivative that is
genuinely stale in CONTENT â€” a master rebuilt with different `_CONFIDENCE` values and the
same geometry, which is the debugging round `publish.sh`'s original comment cites â€” passes
assertion 2 through 7 and this scan alike. **The honest fix is for the step to record the
master it compressed**, so staleness is a hash comparison and not a timestamp. That is a
change to what a bake commits, so it is a parcel and not a footnote.

**Verified:** `tools/check.sh` green including the self-test step.
`SMOKE_VIEWPORT=mobile node tools/smoke_renderer.mjs --published` green. The desktop half
was not run and is not claimed â€” ~13 minutes against this harness's 10-minute per-command
ceiling; see the run-budget box at the top of this file. No vertex, material or pose moves
in this parcel and no committed asset changed a byte, so the desktop half has no quantity
of its own to measure here.

### K38 â€” the parcel as written, kept for the record

**Phase:** kernel Â· `tools/publish.sh`, `tools/measure_web_derivatives.py`, docs. No data
record, no renderer file, no master, no confidence.

K37 closed with a paragraph it declined to chase: *"A THIRD WRITER OF `assets/web/`, noticed
and not chased. `tools/publish.sh` copies a master through whenever it is newer by mtime.
That is a passthrough nothing decided either, it is invisible to this gate (a copy is never
larger than its master), and on a fresh clone mtimes come from checkout order."* Its
generalisation is the parcel: **when a directory has more than one writer, the gate on its
contents is a gate on the last writer only.**

The questions, in order:

1. **Can the mtime rule fire, and what does it do when it does?** Not "is it firing today" â€”
   whether the tree can reach a state where `publish.sh` replaces a compressed derivative
   with an uncompressed master copy, in the *tracked* source tree and in the mirror.
2. **Which of the eight assertions in `tools/measure_web_derivatives.py` sees it?** A master
   copied over its own derivative has the master's triangles, node identity, attributes,
   bounding box, materials and byte count. Answer it by measurement, not by reading.
3. **What does the passthrough cost if it fires everywhere?** The census already prints the
   payload both ways; put the number in the parcel rather than leaving it as a ratio.
4. **Then decide the writer, not only the gate.** `publish.sh`'s copy exists for a real
   failure (run `generators/build.py` alone and `assets/web/` is stale), but this project's
   own rule for that case is *"a stale committed GLB is a check failure, not a warning"*
   (AGENTS.md), and `measure_web_derivatives.py --gate` already answers staleness from
   CONTENT. A silent `cp` and a content gate cannot both be the answer.

Watch: the 93 legitimate passthroughs K37 decided are legitimate â€” the gate must tell a
decided passthrough from an accidental one, and a bound of zero would be wrong.

### K39 â€” the derivative does not record the master it was made from Â· **DONE 2026-08-16 â€” it does now, and the control that was supposed to verify it does not exist: 14 of 20 shipped derivatives cannot be produced by this repository's own step**

**Phase:** kernel Â· `tools/web_derivatives.sh`, `tools/measure_web_derivatives.py`,
`tools/publish.sh`, `assets/manifest.web.json` (new), `assets/LICENSES.md`, docs. No data
record, no renderer file, no master, no confidence, and **no committed asset changed a
byte**.

**THE COUPLING, DECIDED BEFORE THE FILE WAS WRITTEN** â€” which is what the parcel asked
for, because it is the part that can turn a nightly into a red dev gate for everyone
else. **The STEP writes the record, on every run, and a bake carries the diff.**

- The record's lifecycle is the derivative's: same producer, same run, same commit.
  `tools/bake.sh`'s only web-derivative call is `tools/web_derivatives.sh`, and the bake
  workflow commits `chicago/4d` whole â€” so a nightly that regenerates geometry rewrites
  the record in the same breath, and **no workflow change is needed** (which matters:
  workflow files are outside a steward run's scope).
- Hand-banking was the alternative and it is the failure this project has now measured
  twice â€” `build.json`, written once by hand and two days stale on the site; the
  665-roof crosswalk, authored and wrong by a third of the programme. A record a person
  maintains describes the tree as it was when they last remembered.
- **It is not in `tools/web_derivative_baseline.json`**, which is K39's own Watch. That
  file is a record of FAULTS a person banks deliberately with `--write-baseline`; a map
  that changes on every bake has the opposite lifecycle and would train everyone to run
  `--write-baseline` without reading it. It went beside **`assets/manifest.json`**
  instead, because the two are the two links of one chain: the manifest records
  data â†’ master and is written by the Blender build, `manifest.web.json` records
  master â†’ derivative and is written by the step after it.

**FINDING 1 â€” one hash, and the assertion is absolute in both directions.** 334 of 334
derivatives now record the master they were made from. A derivative whose recorded hash
is not its master's hash today fails; a derivative with no entry fails (that is a file no
step here claims to have produced); an entry naming a derivative that is not there fails.
**Exercised against the real tree rather than only in memory**: appending one byte to
`cobweb_castle__log_1820.glb`'s master makes `--gate` fail by name â€” *"made from a master
with sha256 275bab93cbe7â€¦ and the master in the tree today is d6e5c694decdâ€¦"* â€” and makes
`tools/publish.sh` **refuse before it writes anything**, working tree clean afterwards.
Two new `--self-test` mutations, both caught, and they are the mutations assertions 1-8
survive: a master rebuilt into the same geometry moves no triangle, no node, no
attribute, no bounding box, no material and no byte count.

**There is deliberately no way to rewrite the record without regenerating the bytes.** No
`--write-record` on the gate, no reseed flag on the step. The remedy for every failure
assertion 9 can produce is `tools/web_derivatives.sh --only <name>`. A hash map you can
rewrite to make a gate green is a hash map that says nothing, and this project already
keeps one file whose whole discipline is that it may only be rewritten to record a
repair.

**FINDING 2, AND IT IS THE ONE WORTH READING â€” the record's own verification control
does not exist.** The obvious way to prove a seeded hash is to regenerate the derivative
and compare bytes, and `tools/web_derivatives.sh`'s header says that works: *"it
reproduces 331 of 334."* **It does not.** Measured on a 20-asset spread sample of the
compressed derivatives:

| | reproduced by `tools/web_derivatives.sh` | did not |
|---|---|---|
| 20-asset spread sample | **6** | **14** |

And the 14 are not noise â€” **every one of them reproduces BYTE FOR BYTE under
`BAKE_PALETTE=1`** (checked on three: `bates_auction_room`, `jh_kinzie_forwarding_store`,
`recon_1835_west_022`). The cause is a side effect nobody had measured: **`optimize`'s
palette pass welds**, and K36(b) turned that pass off for draw-call reasons that stand,
then regenerated only the **38** assets that carried the material fault. The other
derivatives still carry palette-era bytes.

The size of it needs no `npx` at all â€” a welded derivative carries fewer vertices than
its master, and that is readable from the glTF JSON:

| compressed derivatives (334 âˆ’ 93 passthroughs) | 241 |
|---|---|
| **fewer vertices than their master** â€” only the palette-era step produces this | **195** |
| exactly the master's vertex count â€” today's step, or nothing to weld | 46 |
| vertices the welded set drops in total | 10,513 |

195 is a **lower bound**: an asset with no duplicate vertices to weld looks identical
under both steps, which is exactly why 6 of the sample reproduced.

**Nothing is wrong with the bytes on the site.** A weld is lossless, the triangles are
equal, and assertions 1-9 are green on all 195. What is wrong is the claim: the sentence
the whole no-Blender repair strategy rests on â€” *this runner can regenerate what the
nightly ships* â€” is true for 46 of 241 and false for 195. And the consequence is
scheduled: **the next nightly bake rewrites all 195 as unwelded files**, +2,756 bytes
across the 14 sampled (+197 each), arriving in a bake PR as binary noise nothing
predicted.

**FINDING 3 â€” and it is why assertion 9 stops where it does.** The hash names the
MASTER, not the STEP. All 195 palette-era derivatives record the right master and are
correctly green, because their master *is* the master beside them. Answering "which step
made this" is a second field with a 195-file repair behind it, and it is K40's, not this
parcel's â€” K39's own effort line says one field.

**THE SEED, STATED PLAINLY.** The record was seeded in this commit rather than produced
by a full run of the step, because a full run regenerates all 334 derivatives and 195 of
them would change bytes â€” that is K40's repair and it needs a smoke half this runner
cannot finish. One entry (`cobweb_castle__log_1820.glb`) was written by the step itself,
and its derivative came back **md5-identical**; the other 333 were hashed from the
masters in the tree and merged into the same structure. **What the seed rests on** is
assertions 1-8: each derivative carries this master's triangles, node identity and
`extras`, contract attributes, bounding box to under 2.63 rungs, and material table, and
93 of them are byte-identical to it. **What it does not claim** is that the shipped bytes
were produced by today's step â€” finding 2 measured that at least 195 of them were not.

**Verified:** `tools/check.sh` green, including the self-test step and the licence check
(`assets/manifest.web.json` is accounted for in `assets/LICENSES.md`, beside
`manifest.json`, as a build record rather than an asset).
`SMOKE_VIEWPORT=mobile node tools/smoke_renderer.mjs --published` green. The desktop half
was not run and is not claimed â€” ~13 minutes against this harness's 10-minute
per-command ceiling; see the run-budget box at the top of this file. No vertex, material
or pose moves in this parcel and no committed asset changed a byte.

### K40 â€” 195 shipped derivatives were made by a step this repository no longer has Â· **DONE 2026-08-16 â€” it is 189, this runner reproduces the nightly's bytes on every one of them, and the rewrite is not scheduled: it is sitting in an open bake PR**

**Read `docs/RESEARCH/web-reproduction.md` before quoting any reproduction number, and stop
quoting 195.** Four questions were asked and all four are answered from a control that runs
`tools/web_derivatives.sh` itself over all 334 masters â€” chunked into four 3 min 21 s passes
to fit the harness's ten-minute per-command ceiling, which is why the loop is now a tool
(`tools/measure_web_reproduction.py`) rather than something each parcel reinvents.

**FINDING 1 â€” the exact count, and the failures decompose with nothing left over.**
**142 of 334** reproduce. Of the 192 that do not, **189 come back BYTE FOR BYTE under
`BAKE_PALETTE=1`** â€” the palette-era set, counted rather than inferred â€” and the remaining
**three were already owned by name**: the two K37 placeholders that compress smaller
(`recon_1835_blk_randolph_clark_h2_02`, `â€¦_wells_h2_01`) and `terrain__e1834_harbor_cut.glb`,
committed at 14 bits against a 16-bit ask, which is R-W6(b) in one file.

**FINDING 2, AND IT IS THE ONE THAT MOVES THE PARCEL â€” the rewrite is not scheduled, it is
OPEN, and this runner's control produces the nightly's exact bytes.** Bake PR **#175**
(opened 07:34 UTC, 2026-08-16) rewrites **280 derivatives**, and all 192 non-reproducing
files are in it. On the 189 the nightly's bytes and this runner's are **md5-identical, 189 of
189**. So the claim the whole no-Blender repair strategy rests on â€” *this runner can
regenerate what the nightly ships* â€” is **true**, with a control behind it for the first
time. What was wrong was never the extraction; it was that a step change had been carried
through 38 files and not 334. The bake's 280 decompose exactly: **189** palette-era + **90**
placeholder masters upgraded to canonical archetype bakes (5 KB boxes â†’ 25â€“83 KB buildings)
+ **1** terrain at 16 bits. A binary diff nobody could review now has an arithmetic.

**FINDING 3 â€” K39's vertex signature is REFUTED as an identifier.** It counted 195 files
carrying fewer vertices than their masters and reasoned that only the palette-era step
produces that. Against the exact set it is wrong in **both** directions: 189 shared, **six
welded files that today's step reproduces exactly** (2â€“4 vertices each â€” `optimize` dedups
without the palette pass) and three failures with no weld. The tool prints the proxy beside
the exact answer so it cannot be rounded off again, and **no gate is built on the vertex
count**.

**THE PRICE.** +48,836 bytes over the 189 (mean **+258**, and **all 189 grow**; worst
`fort_dearborn_garrison_garden__fence_1816` at +7,240), **+48,328** net across the tree once
K37's two placeholders' âˆ’1,624 is counted. That is +1.01 % of 4,764,664 bytes and **0.18 % of
the 25 MB budget**. K39's sample said +197 from 14 files and 30 % reproduction; the true
figures are +258 and 42.5 %. **10,491** vertices are merged across the set.

**DECISION 1 â€” who moves the 189: nobody here.** The parcel expected a choice between
regenerating 195 binary files on a runner that cannot finish the desktop smoke, and letting a
nightly land them unreviewable. Measuring first dissolved the first option â€” an open PR
already holds those exact bytes â€” and answered the second with the decomposition above. This
parcel therefore **moves no asset and merges no bake**: #175 and #164 carry **no status checks
at all**, because a bot-opened PR does not trigger the dev gate, and running that gate against
them is the janitor's job and the owner's call.

**DECISION 2 â€” should the record name the STEP as well as the master? NO,** and the
measurement is the reason. A flag-set string is prose, and prose can be edited to turn a red
gate green â€” the one property K39 deliberately denied the record. A hash of the script is not
editable and is wrong measurably: the four commits that have changed
`tools/web_derivatives.sh` since it was extracted moved **38, 3, 0 and 0** derivatives, so a
script hash would have invalidated all 334 entries four times, **twice on a commit that moved
no byte**, and the file is mostly comment â€” every parcel writing down what it learned would go
red. What the failure needed was a rule, and it is in the step's header now: **a change here
that moves any derivative's bytes regenerates all 334, not the ones that visibly broke.** It
is deliberately not a gate â€” the only exact test is the 13-minute control, `tools/check.sh` is
90 seconds on purpose, and the one cheap candidate is the signature finding 3 refutes.

**Verified:** `tools/check.sh` green; `SMOKE_VIEWPORT=mobile node tools/smoke_renderer.mjs
--published` green. The desktop half was not run and is not claimed â€” ~13 minutes against a
10-minute per-command ceiling; see the run-budget box at the top of this file. **No asset,
record, parameter or renderer file changed in this parcel** â€” it is a measurement, two
decisions, a tool and the documents.

**Open, and named rather than left implicit:** #175 rewrites `assets/web/` and this parcel did
not gate it. When it or a successor lands, `tools/measure_web_reproduction.py --report` should
read **334 of 334**, and the two K37 placeholders are the ones to watch â€” today's step
compresses them, so `tools/web_derivative_baseline.json`'s passthrough list moves 93 â†’ 91 and
assertion 8 asks to be re-banked. That is a repair to record deliberately, not a surprise.

### K40 â€” the parcel as written, kept for the record

K39 needed a reproduction control and could not get one. `tools/web_derivatives.sh` does
not produce the bytes on the site: **6 of 20 sampled derivatives reproduce, 14 do not,
and all 14 come back byte-for-byte with `BAKE_PALETTE=1`.** K36(b) turned the palette
pass off â€” correctly, it was costing draw calls at four of eight scene anchors â€” and
regenerated only the 38 assets whose material identity it had broken. The pass was also
**welding**, which nothing had measured, so **195 of the 241 compressed derivatives carry
fewer vertices than their masters** (10,513 vertices in total) and are the output of a
step that no longer exists here.

Nothing on the site is wrong today. The problem is that the repair is *scheduled without
a decision*: the next nightly bake regenerates all 195 unwelded, and that lands as a
195-file binary diff in a bake PR with no number attached to it.

The questions, in order:

1. **Count it exactly.** The 195 is a lower bound from the vertex signature; a full
   `tools/web_derivatives.sh --out <tmp>` control over 334 masters gives the exact set.
   It costs about 17 minutes of `npx` at ~3 s per asset, so it must be **chunked** under
   this harness's 10-minute per-command ceiling â€” that constraint is the parcel's shape,
   not an aside.
2. **Price it.** +197 bytes per asset on the 14 sampled, against a 4.5 MB payload and a
   25 MB budget. Take the real total, both ways, and quote it.
3. **Decide who moves them, and say why.** Regenerating them here is one command and no
   Blender, but it moves 195 binary files and the acceptance is the *desktop* smoke half
   â€” which this harness cannot finish (see the run-budget box). Letting the nightly do it
   costs nothing and buys a bake PR nobody can review. Both are defensible; picking
   silently is not.
4. **Then ask whether the record should name the STEP.** K39 deliberately recorded the
   master and not the step, and finding 3 says why: the 195 record the right master and
   are correctly green. A second field â€” the tool version and the flag set â€” would have
   caught this on the day K36(b) landed. It would also go stale on every flag change, so
   it is a lifecycle question, not a hashing one.

Watch: **do not "fix" this by turning the palette pass back on.** K36(b) measured what it
costs â€” 56 draw calls against R-W5a's 16, four of eight anchors over the 80 budget, worst
102 at the Green Tree â€” and that measurement stands. If the weld is worth having, it is
worth having *on its own*: `gltf-transform` ships a `weld` command, and a pass this
project adds deliberately is a pass it can measure. Do not add one without a number.

### K39 â€” the parcel as written, kept for the record

K38 took `tools/publish.sh` out of the business of writing `assets/web/` and left its
detector in place, refusing instead of copying. **The detector is still an mtime
comparison, and K38 measured that mtime cannot answer this question**: on a fresh clone
334 of 334 masters are older than their derivatives by `git checkout`'s own write order,
so the scan is silent on exactly the tree a steward run starts from.

The gap that survives is narrow and named. `measure_web_derivatives.py` asserts triangles,
node identity, contract attributes, a bounding box within four rungs and material
identity â€” so a master rebuilt into a *different building* fails. A master rebuilt into
the **same** geometry with different `_CONFIDENCE` values does not, and that is the
failure `publish.sh`'s original comment was written about: *"a rebuilt building kept
rendering with its old confidence values."* `_CONFIDENCE` is how a visitor is told which
parts we made up, so a stale one is a provenance fault wearing a rendering fault's
clothes.

The fix is one hash. `tools/web_derivatives.sh` knows exactly which master it compressed;
nothing writes that down.

1. Have the step record `name â†’ sha256(master)` as it produces each derivative â€” as a
   committed sidecar it writes itself, so the record travels with the artefact and the
   step stays the only thing that authors it.
2. Assert it: a derivative whose recorded master hash is not the master's hash today is
   stale, absolutely, whatever the timestamps say. That subsumes K38's mtime scan and
   `publish.sh` can then simply run the gate.
3. **Decide the coupling first, because it is the real question.** The record changes on
   every bake, so a nightly that regenerates geometry and does not rewrite it turns the
   dev gate red for everything else. Either the step rewrites it (and the bake PR carries
   the diff, which is honest) or it is banked by hand (and it will go stale). Pick, and
   say why, before writing the file.

Watch: do **not** fold this into `tools/web_derivative_baseline.json`. That file is a
record of FAULTS and repairs, deliberately rewritten only by a person banking a decision;
a hash map that changes on every bake has the opposite lifecycle and would train everyone
to run `--write-baseline` without reading it.

### K42 â€” the read-set for the flora and fauna layers Â· **DONE 2026-08-16 â€” 58 of the two layers' 100 figures reach nothing, and one whole layer has no reader at all: no file under `renderers/` opens `data/fauna`, and `publish.sh` never puts it on the site**

**Read this box before quoting any flora or fauna read number.** K41's residual, taken at
face value: the buildings and the ground each declare which of their figures reaches a
vertex, `tools/validate.py` turns each declaration into a rule, and the two layers with 293
records between them had never been asked the question.

**FINDING 1 â€” the count, and it is nearly evenly split.** **100 figures** across five record
kinds (flora zone / manifest / palette, fauna zone / manifest), after identity, file routing,
provenance and prose keys are stripped the way `compile_scene.ground_fields` strips them on
the ground side. **38 reach a vertex or a pixel**, 2 are read only to be shown as text, 2 are
read only into a diagnostic or a gate accessor, and **58 reach nothing at all**. One of the
38 is worth naming because it is provenance everywhere else in this project and a colour
here: `species[].confidence`, which the confidence view tints each plant by.

**FINDING 2 â€” `data/fauna` has no reader, and three separate documents imply it does.** **139
species records across 10 habitat zones**, 30 figures, **zero reads** â€” and the strong form of
that is not a field scan but a directory one: **no file under `renderers/` names the layer**,
and `tools/publish.sh` does not copy it, so `site/chicago/4d/data/` has no `fauna/` in it and a
browser has never been offered the layer. Against that: `data/scenes/1835.json` lists `fauna`
in its `layers`; `docs/LIBERTIES.md` L2 describes the July soundscape as shipped; and
`tools/validate.py` demanded eight vocabulary blocks on the ground that *"a renderer reads this
block"*. **This is not an argument for deleting anything** â€” AGENTS.md says the dataset is the
durable artefact and renderers are disposable, so a sourced July soundscape nothing draws is
banked work. The fault is that nothing said so, and a reader of any of those three documents
would conclude the town has animals in it.

**FINDING 3 â€” four unread things in the flora, one of which is a false sentence in the data.**
(a) `data/flora/index.json`'s own `_doc` said the `ground_*` and `bare_soil_fraction` copies
were denormalised into the manifest *"so the ground shader can work from one fetch"* â€” and
**`terrain.js` never opens `data/flora`**; the sward's `bare_soil_fraction` is read off the
zone record, by the smoke's cover gate, not by the ground. That sentence is rewritten to what
is true. (b) `plantable_in_scene` is read by nothing in either place it is written: zones 7â€“9
match nothing because their extents do not meet the modelled ground, not because of the flag.
(c) **The palettes are 12 unread figures each, 108 in all** â€” `wind.{speed_mps,sway_deg,gust,
wave_m}`, `lod.{near_m,mid_m,far_m}`, `budget.instances_{near,mid}` and `ground.{rgb,dry_rgb,
wet_rgb}` â€” because `flora.js` tuned its own `TUNE` constants and reads only `greens` and
`dry_accent`. (d) **31 flowering species record a July `fruit` nothing draws**, plus
`cover.standing_water_fraction` on all ten zones and `cover.litter_fraction` on one.

**FINDING 4 â€” K41's residual, answered, and the plants are on the wrong side of it.** All
**202** unresolved-source citations in `data/flora` sit on a record node carrying at least one
figure that reaches a vertex (a node's own figures stop at the next node that cites its own
sources, so a zone does not inherit its species' geometry). All **30** in `data/fauna` sit on
a layer nothing draws. Under K41's wide reading the flora layer is the worst-affected
population in the project â€” worse proportionally than the 49 building attributes â€” and under
the narrow reading it is untouched. **Same reading, same owner, same three routes as K41.**

**WHAT SHIPPED.** `tools/measure_layer_reads.py` â€” census, `--gate`, `--self-test`,
`--update` â€” and `tools/layer_reads_baseline.json`, 58 entries banked by layer, record kind
and field path with the record count on each. Five assertions: **1** every figure present is
classified; **2** every read declaration names an expression still in the renderer; **3**
absolute in two halves â€” a layer with no declared reads may not be opened by any renderer
source and a layer with them must be, then per figure a reverse property scan; **4** a new
unread figure fails; **5** absolute, a banked entry that has left the data fails until it is
un-banked in the commit that wired it up. All exercised in memory by `--self-test`, which
`tools/check.sh` runs.

**THE TWO METHOD NOTES worth carrying to the next parcel of this shape.** (a) **The map is
Python and the reader is JavaScript**, which is `terrain_inputs.py`'s problem in a new
costume â€” there the reason not to co-locate was the ground's hash, here it is a 26-minute
smoke behind every renderer edit. Both buy the same thing the same way: **the declaration is
scanned against the source it describes**. (b) **Strip the comments before scanning.**
`flora.js` discusses `bare_soil_fraction: 0.45` in a comment three lines above the line that
reads it, and `check_sidecar_contract` reported *itself* on its first run for exactly this.
The stripper is exercised in the self-test in both directions, including a string that looks
like a comment.

**THE LIMIT, stated rather than discovered later.** A text scan cannot attribute a property
access to one of two record kinds that both carry that field name â€” `bare_soil_fraction` is
read off a zone and copied into the manifest â€” so **2 entries are exempted from the per-field
scan and listed by name in the census** as stated rather than proven. The fauna half needs no
exemption because the layer rule is absolute. The durable fix is the same one this project
keeps arriving at from other directions: a renderer that declares its own read-set in a form
the gate can import.

**WHAT THIS PARCEL DOES NOT DECIDE, and the routes.** Whether an unread figure should be
deleted, wired up or declared is three different answers. *The fauna layer*: (1) leave it and
say so â€” the honest option, and it needs `data/scenes/1835.json`'s `layers` list and
`docs/LIBERTIES.md` L2 to stop implying otherwise, which is a claim about the scene and the
owner's; (2) give it a reader, which is a renderer parcel of real size and no bake; (3) do
nothing, which is where the last three days left it. *The palettes*: their unread blocks are
render tuning the renderer has re-tuned, so either the palette record stops carrying them or
`flora.js` reads them â€” a `TUNE`-versus-record question with no evidence in it, and cheap.
*The `fruit` on 31 species*: it is the one entry here with a research half, because a July
fruit is a visible thing this scene omits and `docs/LIBERTIES.md` does not record the
omission.

**Verified:** `tools/check.sh` green with the two new steps; `SMOKE_VIEWPORT=mobile node
tools/smoke_renderer.mjs --published` green. The desktop half was not run and is not claimed â€”
~13 minutes against a 10-minute per-command ceiling; see the run-budget box at the top of this
file. **No record moved and no asset changed**: the only data edit is one `_doc` sentence in
`data/flora/index.json` that was false, and two `tools/validate.py` error messages that said
a renderer reads a block no renderer reads.

### K45(a) â€” the repair K44 named draws nothing, because `TIMBER_ZONES` is a species table and the placer picks from a hand-written list Â· **DONE 2026-08-16 â€” one line of prescribed repair refuted three ways, and the American sycamore has been standing in the same hole all along**

**Read this box before quoting any planting-reach number.** K44 found four researched
lakeshore trees handed to no reader and wrote the repair down in `docs/LIBERTIES.md`
**L113** and in this file: *"Add `z08_lakeshore` to `TIMBER_ZONES` and the four dune
records are drawn by the archetypes that already exist."* This parcel is the run-budget
box's rule applied to that sentence â€” **land the measurement before spending a smoke on
the fix** â€” and the measurement refuses the fix.

**FINDING 1 â€” `TIMBER_ZONES` places nothing; it is a SPECIES table, and the proof is
already committed.** `trees.js` opens those four zone files to build one render spec per
species â€” height, crown width, July foliage, density, confidence â€” and then throws the
zone away. A zone's `extent` is read by `flora.js` and **never** by `trees.js`. Placement
is `COMMUNITIES`: four hand-written mixes chosen by heightfield rules (distance to water,
which land division, a generated relief field), and a stem's species is
`pick(mix, rnd())`. Nobody has to take that on argument, because the repo contains the
control: **`z07_bur_oak_savanna`'s declared extent box is E âˆ’2600..âˆ’600, N âˆ’6400..âˆ’4400** â€”
4.4 km outside the modelled field in the nearest direction, so no point in the scene is
ever in that zone â€” **and its two oaks are drawn anyway**, out of the `ridge_oak` mix. A
zone in the list is a zone whose species parameters are read. It is not a zone that is
planted.

**FINDING 2 â€” so the prescribed repair draws exactly zero stems, and the gate now says so
in memory.** Applied to the real tree by `--self-test`, adding `z08_lakeshore` to
`TIMBER_ZONES` does this and nothing else: `populus_deltoides` and `salix_interior`
**already** have a spec from `z05_riverbank_timber`, and `loadTimberZones` is first-zone-
wins (`if (specs[sp.id]) continue`) with the new zone appended last, so z05's gallery
cottonwood keeps the entry and the dune form never lands â€” which is the right outcome and
also not a repair. The other two, **`populus_tremuloides` and `populus_balsamifera`, are in
no community mix**, so `pick()` can never return them: they gain a `specs` entry nothing
can select. Four records in, zero stems out. The count is asserted rather than described â€”
the self-test prints the two species the repair adds to the unselectable bank.

**FINDING 3 â€” and the hole was already occupied.** Ask the question of the town as it
stands and one species falls into it: **`platanus_occidentalis`, the American sycamore** â€”
routed by `z05_riverbank_timber`, role `tree`, form `tree_gallery` which has an archetype,
`density_per_ha` **[1, 3]** written down, graded `inferred` off McBride & Bowles, its July
appearance recorded as *"Rare, at its northern edge; white mottled bark flashing on the
upper limbs"* â€” **and in none of the four mixes.** It is drawn nowhere and always has
been. **K44 counted it as reached**, correctly by its own definition: the record is handed
to `trees.js`. It is the same loss one level in, and invisible from K44 for the same reason
K44 was invisible from K42 â€” *"this record is received"* and *"this record can be selected"*
are different sentences, and only the first one had a gate.

**FINDING 4 â€” the timber layer has never visited three quarters of the modelled ground.**
The woody planting loop sweeps a fixed square, `half = 320 - step`, so **E/N âˆ’316..+316 m**
at full detail. S2e carried the heightfield east to **E âˆ’320..+1700, N âˆ’400..+400**.
Measured against the planter's own dry floor (`water_surface_m + TREE_DRY_MARGIN_M`, 0.20 m):
**192,844 heightfield nodes stand above it, 52,163 of them inside the square â€” 27.05 % â€”
and 140,681 outside, which is 87.9 ha.** `flora.js`'s lattice is built around `camE`/`camN`
and follows the visitor over all of it, so the sward reaches ground the timber cannot. And
`z08_lakeshore`'s own box starts at E +1400, **1,084 m east of the planter's east edge**:
even a repair that fixed the mix would still plant nothing there.

**WHAT THIS MEANS FOR THE PARCEL, stated as a plan rather than left implied.** K45's first
repair is not one line, it is two changes and one research question: a **dune community**
in `COMMUNITIES` with a placement rule (what selects it â€” substrate? distance to the lake?
the zone extent, which would make `trees.js` read an extent for the first time) and the
sourced densities the records already carry (3â€“15, 2â€“8, 2â€“8 per ha), **and** the planting
loop's square carried east over the ground that community stands on. Both carry the smoke,
and the second one changes how much ground the loop sweeps, which is a cost question this
box does not answer. That is **K45(b)**.

**WHAT SHIPPED.** `tools/measure_planting_reach.py` â€” census, `--gate`, `--self-test`,
`--update` â€” and `tools/planting_reach_baseline.json`. Four assertions: **1** the
declarations are still in the renderer, and `trees.js` still has exactly the **2**
`addTree` call sites this gate accounts for, so a third selection path is a failure rather
than a species wrongly called unselectable; **2** the planter's domain, banked exactly and
allowed to GROW and not shrink â€” the number K45(b) has to move; **3** the routed,
archetyped, unselectable species, exact both ways, which is the assertion that refuses
L113's repair; **4** every `TIMBER_ZONE` that declares an extent box with whether that box
meets the planter, so routing-is-not-placement is held in a file instead of a paragraph.
Every declaration is **scanned out of the renderer**, and a scanner that cannot find its
own is a raise rather than an empty set.

**THE SCANNER BUG THIS FILE FOUND IN ITSELF, recorded because it is the failure mode the
house style exists to prevent.** The first version read a community's mix with
`\[(.*?)\],` and the mixes are written several lines long with a `],` closing each species
pair, so the non-greedy match stopped two entries in â€” and the census confidently reported
**nine** unselectable species, six of which are drawn in every frame. A bracket-balanced
reader replaced it and a self-test check now asserts that a multi-line mix is read to its
END. **A scan that under-reads looks exactly like a finding**, which is why every scanner
here has to be able to say no as well as yes.

**THE LIMIT.** `standsDry` is one of several tests a stem must pass â€” the traced water
mask, the buildings, the community classifier (which returns null over most of the box)
and the per-hectare roll all remove more. The land census is therefore an **upper bound on
ground the loop could visit**, not a count of stems; the stems actually built are
`trees.stats` and belong to the smoke. The tool's docstring says so.

**Verified:** `tools/check.sh` green with the two new steps; `SMOKE_VIEWPORT=mobile node
tools/smoke_renderer.mjs --published` green. The desktop half was not run and is not
claimed â€” ~13 minutes against a 10-minute per-command ceiling; see the run-budget box at
the top of this file. **No record, asset, parameter or renderer file changed** â€” this
parcel is a measurement, a bank, two gate steps, a correction to L113 and a changelog
entry. Nothing a visitor sees moved, which is the honest outcome when the repair on the
table would have moved nothing either.

### K45(b) â€” the lakeshore repair as it actually is Â· **SPENT 2026-08-17 â€” all three changes have landed Â· opened 2026-08-16 by K45(a)**

> **NOT A PICK â€” there is nothing left in it.** Change three (the sycamore) landed as K45(b1),
> change two (the planter's square) as K45(b2), and change one (the dune community) as
> K45(b4) below. Its successors are **K45(b3)**, the detail control, and the willow scrub
> K45(b4) leaves unplanted.

K45(a) refuted the one-line version. What is left is two changes and one research question, and
its numbers are all measured and committed â€” take them, do not re-derive them.

**Change one: a community that can stand on dune sand.** `COMMUNITIES` has four mixes and the
classifier that chooses between them (`communityAt`) asks distance-to-water, which land division,
and a generated relief field. On the beach the lake IS water, so bank distance is small and the
classifier would return `gallery` â€” silver maple and elm on open sand, which is worse than nothing.
A `dune` mix needs its own branch and the branch needs a rule: the honest candidates are
**substrate** (the zone record's own `cover`/`ground`), **the zone extent** (which would make
`trees.js` read an extent for the first time in its life, and is a real design change, not a
line), or **distance to the lake specifically** rather than to any water. The densities are
already sourced â€” `populus_deltoides` [3, 15]/ha in the dune form, `populus_tremuloides` and
`populus_balsamifera` [2, 8] each, all three graded `attested` off the MNFI open-dune survey and
Cowles 1901. **Do not invent a fourth species to round the mix out.**

**Change two: the planting loop's square carried east.** `const half = 320 - step` sweeps
E/N âˆ’316..+316 while the field runs E âˆ’320..+1700, N âˆ’400..+400 â€” **87.9 ha, 72.95 % of the ground
above the loop's own dry floor, is outside it**. The cost is the open question this parcel has to
answer with a number rather than a guess: the loop is O(cells) and the field is 4Ã— the square, so
the sweep gets ~4Ã— longer at the same step, on top of whatever the new stems cost in triangles and
draw calls. `stats.drawCalls` and the â‰¤ 80-per-station budget R-W5a and K36(b) both measure are
the gate. **Measure it before widening it**: a `SMOKE_VIEWPORT=desktop` run cannot self-verify on
this runner, so if the widened sweep needs the desktop half, split again and say so.

**And the third thing, which is separable and much smaller.** The **American sycamore** is one mix
entry â€” `['platanus_occidentalis', 1]` in `gallery`, weighted at the [1, 3]/ha its own record
carries â€” and it is drawn nowhere today. It has nothing to do with the lakeshore and could ship on
its own, ahead of either change above, as the cheapest way to move `tools/measure_planting_reach.py`'s
unselectable bank from one to zero. It changes the frame, so it carries the smoke; that is the whole
of its cost.

**The gate will demand the bank move.** `tools/measure_planting_reach.py` holds the planter's reach
(may grow, may not shrink) and the unselectable population (exact both ways), so each of the three
has to `--update` in the commit that makes it. `docs/LIBERTIES.md` **L114** is the entry to move to
**Resolved**, in halves, as they land.

**THE THIRD THING IS SPENT â€” 2026-08-16, K45(b1) â€” and the line above got its weight wrong twice.**
See K45(b1) below before writing any mix entry. Changes one and two stand exactly as written.

**CHANGE TWO IS SPENT â€” 2026-08-16, K45(b2) â€” and it answered change one's hardest question on the
way.** The planter sweeps the field; the cost is measured; and the classifier's beach problem is
solved for now by an east limit rather than by a dune mix. **Change one is what is left of K45(b)
and it is now the only thing standing between `z08_lakeshore`'s three dune poplars and the
ground** â€” read K45(b2) below before writing its placement rule, because the branch it needs is
narrower than this box says: `communityAt` already refuses everything east of State Street, so a
`dune` mix does not have to out-argue the bank-distance test, it has to be reached at all.

### K45(b2) â€” the planter sweeps the field, and the timber gets the east end its own source gives it Â· **DONE 2026-08-16 â€” the square was 13 m from right on one bank and 510 m from right on the other**

**SEEN.** 147 stems stand east of the old square's edge where **one** did; a screenshot taken
looking east from anywhere on the north bank differs. It also holds no exemption and needs none.

**Read this box before quoting a planting-reach number or moving a woody east limit.**

**WHAT SHIPPED, one: the loop.** `const half = 320 - step` is gone. The planting loop sweeps the
heightfield's own extent inset by one planting step â€” **E âˆ’316..+1696, N âˆ’396..+396** â€” so the
reach goes from **52,163 to 189,700 of the field's 192,844 dry nodes, 27.05 % â†’ 98.37 %**, and the
87.9 ha it had never offered a stem to is **2.0 ha of one-step rim**. The bounds are derived from
the heightfield rather than written down, which is the stronger form: a square written as a number
can be right by accident, and this one was.

**WHAT SHIPPED, two: the east end, which the square used to supply by accident.** Ground the loop
reaches is not ground a wood may stand on, and the classifier had no eastern answer at all â€”
`bank <= width` would have read the lake as a river and planted silver maple on the beach.
Andreas ends both divisions in the sentence `z05_riverbank_timber` is already built from: the
South Side belt runs *"east as far as Wells Street"*, and the North Side's timber excepts *"the
sandy hills near the lake"*. `communityAt` now carries one limit per division, **read at load out
of `data/streets/1835.json`** â€” Wells at **E +329.3**, State at **E +825.8** â€” so a limit and the
street it cites cannot drift apart. **64,385 nodes, 40.2 ha, are swept and refused**, which is a
stated omission where an unstated one stood.

**FINDING 1 â€” `z05_riverbank_timber`'s own note put Wells Street 440 m east of where it is, and
the error was load-bearing.** The note read *"Wells Street is about 440 m east of this box's east
edge, so the whole South DivisioßŽüó†òµë(š+my×F÷vã¢F†R'&–FvR&V'2¢£ãL+V7Böbæ÷'F‚¢¢g&öÒF†B&Æö6°§v†–ÆRF†Rf6R'Vç2V7N(	7vW7BÂ6òF†R7&—FW&–öâ6âöæÇ’6VR¢§6–âƒãL+’Ò‚R¢¢öbF—7Æ6VÖVç@¦ÆöærF†R7G&VWBâWfW'’&VÖ–æ–ær&Æö6²öâF†—2&÷r—2–âF†R6ÖR÷6—F–öâ÷"v÷'6RÂæBF†RGvð¦ÆGFVEö&Æö6µöv—F–æu÷7G&VWEö6öçG&öÆVçG&–W2öâ6÷WF‚vFW"&Ræ÷Bà ¢¢¥F†RVW7F–öâ—2æ÷Bv†WF†W"Fò¶VW—B(	B—B—2v†B&WÆ6W2—BÂæBF†Rç7vW"×W7Bæ÷B&P¦6†÷6Vâöâ&Æö6²v†W&R—Bw&VW2v—F‚F†RöÆB'VÆRâ¢¢BÔRw2÷vâÆ÷Bb—2F†RG&¢—Bv–ç2VæFW ¦F—7Fæ6RÖ2ÖÖV7W&VBäBVæFW"g&öçFvRöâF†R'&–FvR7G&VWBÂ6òF†B&Æö6²6ææ÷BF—67&–Ö–æFP¦&WGvVVâF†RGvòâ6æF–FFW2v÷'F‚ÖV7W&–ærÂöâ&Æö6²v†W&RF†W’F—6w&VS  ¢Ò¢¦F—7Fæ6RÆöærF†R7G&VWBæWGv÷&²¢¢FòF†R'&–FvR&F†W"F†â7G&–v‡BÖÆ–æR(	B&W7F÷&W2F†P¢F—67&–Ö–æF–öâF†R&ö¦V7F–öâFW7G&÷—2ÂæB—2v†B&W6–FVçB7GVÆÇ’vÆ¶VC°¢Ò¢¦g&öçFvRöâæÖVBF‡&÷Vv‚7G&VWB¢¢„FV&&÷&âFòF†R'&–FvRÂÆ¶RæB6÷WF‚vFW"FòF†P¢'W6–æW72g&öçB’(	B6Æ–Ò&÷WBF†R7G&VWB&F†W"F†â&÷WBF†R6÷&æW#°¢Ò¢¦æ÷F†–ærBÆÂ¢£¢FV6Æ&RF†Rv—F†–âÖf6R÷&FW"&&—G&'’öâ&Æö6·2VæFW"6öÖRÖV7W&V@¢F‡&W6†öÆBæB6’6òW"&Æö6²Â&F†W"F†âG&W76–ær&÷VæF–ærW2&V6öæ–ærâ¢¥F†—2—2¢ÆVv—F–ÖFRç7vW"¢¢æB&ö&&Ç’F†R†öæW7BöæRf÷"rãRÒ7&VBà ¥v†FWfW"ÆæG2ÂF†RFVÆ—fW&&ÆR—2F†R6ÖR6†R2FööÇ2öÖV7W&U÷7G&VWEög&öçFvRç–¢6öÖÖæ@§F†B&–çG2F†RçVÖ&W"Â6òF†RæW‡B&Æö6²–æ†W&—G2—BâFòäõB&WG&òÖf—BF†Rç7vW"Fò&Æö6·0¦Ç&VG’'V–ÇB(	BÃ"öçv&B&V6÷&Bv†Bv2FöæRæBv‡’ÂæBF†—2Fö7VÖVçB—2VæBÖöæÇ’à ¢222³3"(	BÖ’F†Rf6R'VÆR&æ²7F÷&Sò+r¢¥Tä4Ä”ÔTB+rg&öÒBÔR+rVff÷'C¢2(	BFV6—6–öâÂF†Vâ6ÆW6R¢  ¥F†Rf6R'VÆR26öÖÖ—GFVBBBÔ2æBBÔB&æ·2¢¦GvVÆÆ–æw2¢£¢F†R&W7BF¶RF†R&WGFW"7G&VWBÀ§F†RÖVæW7BF¶RF†R&6²öæRâ&Æµ÷&æFöÇ…ö6Æ&¶v2F†Rf—'7B&Æö6²FVÇB¢¦3& §7F÷&R×&W6–FVæ6R¢¢æBF†R'VÆR6–Bæ÷F†–ær&÷WB—BâBÔRW‡FVæFVB—B(	B7F÷&Rw26Æ–ÒöâF†P¦&WGFW"g&öçFvR—2gVæ7F–öæÂ&F†W"F†â6ö6–ÂÂ&V–ærF†RöæÇ’&ööbv†÷6RW'÷6R&WV—&W2§7G&ævW"6âf–æB—B(	BæBWBF†R3&öâ&æFöÇ‚ÂF—7Æ6–ærCfFòF†R&6²7G&VWBà ¢¢¥F†BW‡FVç6–öâ—2â–çfVçF–öâ&÷WBƒ3R6öÖÖW&6RÖFR'’âvVçBÂæB—BæVVG26WGFÆ–ær&Vf÷&P¦—B&WVG2â¢¢F†R66†VGVÆR7F–ÆÂ†öÆG23(
f3FÂc(
fcFÂƒ6Â“6ÂCÂs(
fsVf÷"&Æö6·0¦æ÷B–WB'V–ÇBÂ6òF†R6ÖRVW7F–öâ'&—fW2v–âF†RÖöÖVçBvv÷&·6†÷÷"âfv&V†÷W6R—0¦FVÇB(	BæBv&V†÷W6Rw2ç7vW"—2Æ–æÇ’F†R÷÷6—FRöb7F÷&Rw2Â&V6W6Rv&V†÷W6RvçG2F†P§&—fW"æBæ÷BF†R7&÷vBâF‡&VR&VF–æw2Fò6†ö÷6R&WGvVVã  £â¢§&æ²'’6Æ–Òöâg&öçFvR¢¢…BÔRw2“¢6öÖÖW&6Râ&WGFW"GvVÆÆ–ærâÖVæW"GvVÆÆ–ærÂv—F‚F†P¢&æ¶–ærWF†÷&VBW"–çfVçF÷'’w&÷W–âƒ3Uö'V–ÆF–æuö–çfVçF÷'’æ§6öæ&F†W"F†âW"&6VÃ°£"â¢§&æ²GvVÆÆ–æw2öæÇ’¢¢æBÆ6RæöâÖGvVÆÆ–æw2'’F†V—"÷vâgVæ7F–öâ(	BF†R7F÷&RFòF†R'W6–W7@¢g&öçFvRÂF†Rv&V†÷W6RFòF†RvFW"ÂF†Rv÷&·6†÷FòF†RÆÆW’(	Bv†–6‚—2Ö÷&R†öæW7B&÷W@¢F†W&R&V–ærGvò'VÆW2æBæ÷BöæS°£2â¢§&VgW6RF†RVW7F–öâ¢£¢ÆVfRæöâÖGvVÆÆ–ærÆ6VÖVçBFòF†R'&ævVÖVçBæ÷FRöbv†–6†WfW"&6VÀ¢ÖVWG2—BÂ2BÔR–âVffV7BF–BÂæB66WBF†B—Bv–ÆÂæ÷B&W&öGV6Rà ¥&VF–ær"—2F†RÆ–¶VÆ–W7BæB—2F†RöæR³#’‚'F†R66†VGVÆRFVÇ2Æör6&–ç2FòF†RF÷vâw0¦6öÖÖW&6–Âg&öçFvR"’—2Ç&VG’6—&6Æ–ærg&öÒF†R÷F†W"6–FS²F†RGvò6†÷VÆB&ö&&Ç’&R6WGFÆV@§FövWF†W"âv†FWfW"ÆæG2&VÆöæw2–âF†R&V6—Rw2Æ6VÖVçE÷'VÆVÂv†W&RF†RvVæW&F÷"6â&RÖFP§Fò6†V6²—BÂ&F†W"F†â–â&÷6RÆFW"&6VÂ†2Fò&VÖVÖ&W"à ¢222BÔB(	B&Æµ÷&æFöÇ…ög&æ¶Æ–æ+r¢¤DôäR##bÓ‚ÓR¢  ¥F†Rf—'7B&Æö6²öbF†R&÷r¢§Gvò7G&VWG2&6²¢¢g&öÒF†R'W6–æW72g&öçB(	B&÷VæFVB'’&æFöÇ‚À¥vVÆÇ2Âv6†–æwFöâæBg&æ¶Æ–â(	B6'&–W2¢¦V–v‡B&öög2Â6—‚&–æ6—ÂæBGvòæ6–ÆÆ'’¢¢Âöâ6—‚ö`¦—G26WfVâg&VRÆ÷G2âÆ÷B—2ÆVgB÷Vã²Æ÷B"—2†VÆB'’†&Ööâw2Æör6&–âÂFW&—fVB'¦FööÇ2÷ÆEöö67Wæ7’ç–&F†W"F†âWF†÷&VBâ¢£3B7FæBæB3S&VÖ–âÂ2öbF†VÒöâ6÷fW&V@¦w&÷VæBâ¢¢F†R&V6—R6ÆV&VBWfW'’Æ6VÖVçBvFRöâ—G2f—'7B'Vâ(	BF†R6WfVçF‚&Æö6²–â&÷r(	@¦æB—B—2F†R¢¦f—'7B&Æö6²&6VÂöbF†—26†RFò6öÖÖ—BFööÂ¢¢ÂFööÇ2öÖV7W&U÷7G&VWEög&öçFvRç–À¦f÷"F†R&V6öâ–âf–æF–ærâGvòF÷F–öç2VæFW"'VÆRc¢F†RC2öæR×&ööÒ6÷GFvRöâÆ÷Br&V6öÖW0§F†Ræ–æWFVVçF‚–æfW'&VB6'VçFW"†÷W6V†öÆBÂF†RCÆör6&–âöâÆ÷B2F†RGvVçG’Öf—'7BÆ&÷W&–æp¦öæRâgVÆÂFÖ—76–öâ–âFö72ôÄ”$U%D”U2æÖF¢¤ÃR¢¢à ¢¢¤f÷W"f–æF–æw26ÖR÷WBöb—BF†B&Ræ÷BF†R&Æö6²â¢  £â¢¥BÔ2w2f6R×'VÆRÖV7W&VÖVçBFöW2æ÷B&W&öGV6RÂæBF†Rf—‚—26öÖÖæB&F†W"F†â¢6÷'&V7F–öââ¢¢BÔ2&W÷'FVBÆ¶R"Â&æFöÇ‚"Â6÷WF‚vFW"’&6÷VçF–ærWfW'’Fö7VÖVçFVB÷ ¢–æfW'&VB7G'V7GW&Rv†÷6Rfö÷G&–çB6VçG&ö–B7FæG2v—F†–â#RÒöb7G&VWBw26öÖÖ—GFV@¢6VçG&VÆ–æR"âæòf–ÇFW"&V6÷fW&&ÆRg&öÒF†R&W÷6—F÷'’&öGV6W2F†÷6RF‡&VRçVÖ&W'3¢F†R7FFV@¢öæRv—fW2¢¤Æ¶Rrò&æFöÇ‚rò6÷WF‚vFW"B¢¢öâF†R&W6V&6‚Æ–W"ÆöæRâF†Rf–æF–ær—@¢7W÷'FVB7W'f—fW2WfW'’f–ÇFW"G&–VB(	BÆ¶R—2F†R&WGFW"f6R'’v–FRÖ&v–â(	B6òv†Bf–ÆV@¢v2æ÷BF†R§VFvVÖVçB'WBF†R¢§&W&öGV6–&–Æ—G’¢¢ÂæBöâ&ö¦V7Bv†÷6R&öGV7B—2&÷fVææ6P¢F†B—2F†RÖ÷&R6W&–÷W2f–ÇW&RâFööÇ2öÖV7W&U÷7G&VWEög&öçFvRç–—26öÖÖ—GFVB†W&R6òF†P¢æW‡B&Æö6²'Vç2F†RÖV7W&VÖVçB–ç7FVBöb&VÖVÖ&W&–ær—BâÃB—2ÆVgBfW&&F–Ó¢Ä”$U%D”U2æÖB—0¢VæBÖöæÇ’æBF†RÖWF†öB—2v†B—26÷'&V7FVBà£"â¢¥F†R6÷VçB×W7B&W÷'B—G2F‡&VRWf–FVæ6RÆ–W'26W&FVÇ’ÂæBF†—2&Æö6²—2F†P¢FVÖöç7G&F–öââ¢¢F†R&V6öç7G'V7F–öâÆ–W"(	BF†Ræöç–Ö÷W2&öög2F†R&Æö6²&6VÇ2F†V×6VÇfW0¢Æ6R(	B7FööBB¢£Röâ&æFöÇ‚æB’öâv6†–æwFöâ¢¢v†VâF†—2'&ævVÖVçBv26†÷6VâæB&V@¢¢£‚æB"¢¢F†RÖöÖVçBF†R&6VÂ'V–ÇBâf6R'VÆR6÷VçF–ærF†BÆ–W"&VG2F†R&öw&ÖÖRw0¢÷vâ÷WGWB&6²2Wf–FVæ6RæBG&–gG2Æ—GFÆRgW'F†W"g&öÒF†RF÷vâw2&V6÷&Bv—F‚WfW'’&Æö6²à¢W†6ÇVFVBÂF†Rç7vW"†W&R—2¢£Bv–ç7B¢£¢&æFöÇ‚6'&–W2r&W6V&6‚ÖÆ–W"&V6÷&G2æBp¢–æfW'&VBÖ†÷W6V†öÆB'V–ÆF–æw2ÂæB¢¥v6†–æwFöâ7G&VWBw2VçF—&RFö7VÖVçFVBƒ3Rg&öçFvR—2F†P¢W7G&’Vâ¢¢ÂF†RF÷vâw2÷VæBf÷"7G&’æ–ÖÇ2à£2â¢¥F†RVæB'VÆRF†–ç2f÷"6V6öæB&Æö6²'Vææ–ærâ¢¢F—7Fæ6RFòF†RFV&&÷&â7G&VWBG&v'&–FvP¢'Vç2¢£S#rã‚Ò¢¢BÆ÷BbFò¢£SƒBãÒ¢¢BÆ÷BöâF†R&æFöÇ‚g&öçFvRæB¢£Sc‚ãRÒ¢¢BÆ÷@¢rFò¢£c#ãÒ¢¢BÆ÷B&V†–æC²F†Rf"VæBöbF†Rg&öçBf6R7FæG2¢£ã9r¢¢2f"g&öÒF†P¢'&–FvR2F†RæV"VæBÂv–ç7BBÔ2w2ã2æBBÔ"w2"ã“2ÂæBF†Rg&öçBf6Rw2'6öÇWFP¢7&VB—2¢£Sbã"Ò¢¢v–ç7BBÔ2w2c‚ã"ÒâföÆÆ÷vVBç—v’öâBÔ2w2&V6öæ–æs²&V6÷&FVB0¢6Æ÷6W"Fò&&—G&'’F†â÷&FW&VBà£Bâ¢¥F†R'6V6öæB&ööb"VW7F–öâ†2&VVâF†Rw&öærVW7F–öâf÷"6—‚&Æö6·2ÂæBF†—2—2F†Rf–æF–æp¢F†BÖGFW'2Ö÷7Bâ¢¢WfW'’&Æö6²6–æ6RBÔ’†2&V6÷&FVB—G2CBæB—G2C"2§6V6öæB¢&öög2f÷ ¢F†R6'VçFW'2æBF†RÆ&÷W&W'2æB&VgW6VBF†VÒ6öç6W'fF—fVÇ’â&÷F‚vW&RFVÇB†W&RæB&÷F€¢&R&VgW6VBv–â(	B'WBF†RCB—2Ç6òF†R¢¦f—'7B¢¢&ööböbF†R¢§FV×7FW'2¢¢æBF†RC"F†P¢f—'7B&ööböbF†R¢¦ÆVæG&W76W2¢¢ÂF†R÷F†W"GvòöbÖWF†öB'VÆR"w2f÷W"Væ&÷VæFVBG&FW2ÂV6€¢†÷W6VB–âF†BöæRfÖ–Ç’æB–âæò÷F†W"æBV6‚Ç&VG’Æ6VB–âF†R6÷WF‚F—f—6–öââ&÷F€¢72ÆÂF‡&VRöb'VÆRbw2FW7G2æBæò&6VÂ†2WfW"æÖVBF†VÒâ¢¥6—‡FVVâæöç–Ö÷W2C"æBC@¢&öög27FæB–âF†R6÷WF‚F—f—6–öâFöF’VæFW"W†7FÇ’F†BFW67&—F–öââ¢¢¢¤³#‚¢¢—2F†W&Vf÷&P¢6WGFÆ–ærÆ&vW"VW7F–öâF†âF†RöæR—Bv2÷VæVBöã¢æ÷Bv†WF†W"G&FRÖ’F¶R6V6öæ@¢&ööbÂ'WBv†WF†W"'VÆRbFÖ—G2&ööbf÷"G&FRF†B†2æ÷B6¶VBf÷"öæRà ¢¢¥F†Ræ–çF‚³#ÖV7W&VÖVçB—2cöb‚¢¢6'&–VBÖ÷fW"–çfVçFVBW'6öç2&VæÖVBÂv–ç7BcrÖöbÓ`¦BBÔ2ÂS’ÖöbÓBBBÔ"ÂrÖöbÓ"BBÔÂs"ÖöbÓBBÔÂ’ÖöbÓ“‚BBÔ’æB3"ÖöbÓ“`¦BBÔ‚â6WfVâÖV7W&VÖVçG2æ÷r7ârRFòs"Rv—F‚æ÷F†–ærf—†VB÷"'&ö¶Vâ&WGvVVâF†VÒâ³# §7F–ÆÂ÷vç2F†Rf—‚à ¢¢¤f–ÆW3¢¢¢FF÷&V6öç7G'V7F–öâóƒ3U÷ÆGFVEö&Æö6µ÷&6VÇ2æ§6öæ+p¦FF÷&V6öç7G'V7F–öâóƒ3Uö–æfW'&VEö†÷W6V†öÆE÷&öw&ÖÖRæ§6öæ+rFF÷7G'V7GW&W2öƒ‚æWr’+p¦FF÷&W6–FVçG2öƒ"æWr†÷W6V†öÆG2Â"æWrW'6öç2Â³#6‡W&â’+p¦FF÷&V6öç7G'V7F–öâóƒ3UóccU÷&ööe÷&öw&ÖÖRæ§6öæ†FW&—fVB’+r76WG2övÇFbö²76WG2÷vV"ö ¢ƒ‚fÆvvVBÆ6V†öÆFW"tÄ'2Âæò&ÆVæFW"’+r6–FV6'2+rFö72ôÄ”$U%D”U2æÖFÃR+rFö72õ5DEU2æÖF+p¦Fö72õ$ôDÔæÖF+r&VæFW&W'2÷vV"ö§2ö6†ævVÆöræ§6+rF†RV&Æ—6†VBÖ—'&÷"â¢¤öæRFööÂf–ÆS ¦FööÇ2öÖV7W&U÷7G&VWEög&öçFvRç–ÂæWrÂ7FæFÆöæRÂæ÷Bv—&VB–çFò6†V6²ç6†â¢  ¢222BÔb(	B&Æµ÷&æFöÇ…öÆ6ÆÆV—2F†RV&Æ–27V&R+r¢¤DôäR##bÓ‚ÓR+rF†R&Æö6²v2t•D„E$tâÂæ÷B'V–ÇB¢  ¥F†RF†—'FVVçF‚&Æö6²&6VÂ6Æ–ÖVBF†RÆ7B÷VâVçG'’öâF†R&æFöÇŽ(	5v6†–æwFöâ&÷ræ@¢¢¦6÷VÆBæ÷B'V–ÆB—B¢¢â&Æµ÷&æFöÇ…öÆ6ÆÆV(	B&æFöÇ‚Â6Æ&²Âv6†–æwFöâÂÆ6ÆÆR(	B—0¢¢§F†RV&Æ–27V&R¢£¢æG&V26ÆÇ2—B§F†R7V&R¢æB§F†R6÷W'BÖ†÷W6R7V&R¢ÂF†—0§&ö¦V7Bw2÷vâw&÷VæB6öçG&öÂæÖW2—G26÷&æW'2¤årò4R6÷&æW"öbF†RV&Æ–27V&R&Æö6²¢À¦æB—B6'&–W2F‡&VRöbF†R6÷VçG’w2÷vâ'V–ÆF–æw2(	BF†RW7G&’Vâöâ—G26÷WF‚×vW7B6÷&æW ¢„Ö&6‚ƒ32Â6†–6vòw2f—'7BV&Æ–2'V–ÆF–ær’ÂF†RÆör¦–Âöâ—G2æ÷'F‚×vW7B†fÆÂƒ32’æ@§F†Rf—'7B6öö²6÷VçG’6÷W'BÖ†÷W6Rƒƒ3R’âF†RccR×&ööb&öw&ÖÖRv2FVÆ–ær—BâÂ¦C6ÂCFæBCVà ¥6òF†R&6VÂ&W6W'fVB—B–ç7FVBâFF÷&V6öç7G'V7F–öâóƒ3U÷&W6W'fVEöw&÷VæBæ§6öæ—2F†P¦WF†÷&VB&W6W'fF–öã²F†RÆBÖöGVÆRVÖ—G2F†R&Æö6²¢§v—F‚æòÆ÷G2¢£²&V6öæ6–ÆUóccRç– §&W÷'G2—BÆGFVEö&Æö6µ÷&W6W'fVFò7FFS¢&W6W'fVFæBFVÇ2—Bæ÷F†–æs°¦vVæW&FUö&Æö6µö–æf–ÆÂç–&VgW6W2&V6—RF†BæÖW2—BÂ'’æÖRæB&Vf÷&R—B'V–ÆG0¦ç—F†–æs²æBFööÇ2öÖV7W&U÷&W6W'fVEöw&÷VæBç’ÒÖvFV—27FWöb6†V6²ç6†âgVÆÀ¦FÖ—76–öâ–âFö72ôÄ”$U%D”U2æÖF¢¤Ãr¢¢â—B—2F†Rf—'7B&6VÂöbF†—26†RFò6öÖÖ—Bæð§7G'V7GW&R&V6÷&BBÆÂÂæBF†RF†—&BFò6öÖÖ—BFööÂà ¢¢¤f÷W"f–æF–æw26ÖR÷WBöb—BF†B&Ræ÷BF†R&Æö6²â¢  £â¢¤WfW'’Æ6VÖVçBvFRF†—2&ö¦V7B†276VBF†RGvò'V–ÆF–æw2F†BvW&R7FæF–æröâF†P¢7V&Râ¢¢w&–v‡Eö'V–ÆF–æu÷FõöÆWEöæBö&(	B¦ö†âw&–v‡Bw2GvòFö7VÖVçFVB6÷GFvW2Fð¢ÆWB(	BvW&RÆ6VB–â¢'F†R6÷WF‚F—f—6–öâ&æBF†R&V6—W2W6Rf÷"÷&F–æ'’GvVÆÆ–æw2"¢À¢æBF†B&æB&â7&÷72F†R7V&RâF†RÆ6VÖVçBv2FW7FVBf÷"6ÆV&æ6Rg&öÒ÷F†W ¢'V–ÆF–æw2Âf÷"—G2÷vâÆ÷BÆ–æW2Âf÷"F†RÆGFVB&öGv’æBf÷"'V–ÆF&ÆRw&÷VæBâ¢¤æ÷@¢öæRöbF†÷6RVW7F–öç2—2v†WF†W"F†Rw&÷VæBv2f÷"6ÆR¢¢Âv†–6‚—2v‡’Fö7VÖVçFV@¢&—fFR'V–ÆF–ær6÷VÆB7FæBöâF†R6÷VçG’w27V&RF‡&÷Vv‚WfW'’vFRF†R&ö¦V7B÷vç2à¢F†RæWrvFR—2F†RöæRF†B6·2—Bà£"â¢¥F†RFVfV7B—2W7G&VÒöbF†R66†VGVÆRÂ–âF†RÆBÖöGVÆRâ¢¢vVæW&FU÷ÆEöÆ÷G2ç– ¢7V&F—f–FW2WfW'’&Æö6²—B6â'V–ÆB–çFòf÷W"Æ÷G2Fòf6RÂ&V6W6RF†B—2v†BF†P¢F†ö×6öâÖöGVÆR6—2&Æö6²—2âG&v–ærV–v‡BÆ÷BÆ–æW27&÷72F†R7V&R76W'FVB¢7V&F—f—6–öâF†BF†—2&ö¦V7B†2æWfW"&VBöâç’6†VWBÂæBWfW'—F†–ærF÷vç7G&VÐ¢&VÆ–WfVB—BâF†R&W6W'fF–öâF†W&Vf÷&Rv—F†G&w2F†R¢¦Æ÷G2¢¢Âæ÷BÖW&VÇ’F†R66†VGVÆRw0¢W&Ö—76–öâFòW6RF†VÓ¢F†Rw&–BG&÷2S"(i"¢£CBÆ÷G2¢¢ÂæBÆ÷G5÷W%öf6U÷v—F††VÆF ¢&V6÷&G2v†BF†RÖöGVÆRv÷VÆB†fRG&vâà£2â¢¥F†R&W6W'fF–öâ—2–æfW'&VFæB—2æ÷B&öÖ÷FVBâ¢¢æò6÷W&6RF†—2&ö¦V7B†öÆG26—2–à¢FW&×2F†BF†R7V&Rv2&W6W'fVBg&öÒ6ÆRâv†B—B†öÆG2—2F†R&Æö6²w2æÖRÂF†P¢6÷VçG’w2F‡&VR'V–ÆF–æw2öâ—BÂF†RF÷76–W"w2÷vâ&VF–æröbF†R&W7Böb—B(	B¢&÷VâÀ¢Væ–×&÷fVBÂfVæ6VB÷"VæfVæ6VB&—&–R&Æö6²"¢(	BæBöæRW&–öBFW67&—F–öâöbF†Rw&÷Væ@¢—G6VÆc¢¢$÷W"V&Æ–27V&Rv2F†VâöæBÂv†W&RF†R–æF–ç2†BG&VBF†R×W6·&BÂæ@¢v†W&RF†Rf—'7B6WGFÆW'2‡VçFVBGV6·2"¢†6†–6vöÆöw•÷&Vf—&S#s6Â'Vær"’âF‡&VR&VF–æw0¢g&öÒF‡&VRF—&V7F–öç2ÂæöæRöbF†VÒ†÷W6RÂæBF†Rw&FR7F—2–âF†RÖ–FFÆRF–W"v†W&P¢F†RWf–FVæ6RWG2—Bà£Bâ¢¥F†RöæB—2Fö7VÖVçFVBæB—2æ÷BÖöFVÆÆVB¢¢(	BF†RFW'&–â6'&–W2æò7FæF–ærvFW"†W&P¢æBF†RÖ'6‚fÆ÷&¦öæR—2'VffW"öbF†RÖVBvFW"Â6òF†R7V&R&VæFW'22G'¢&—&–Râ6V6öæBfÇ6R7FFVÖVçB&÷WBF†R6ÖRw&÷VæBÂ6ÖÆÆW"F†âF†RöæRf—†VBæBæ÷@¢f—†VB†W&Râ÷VæVB2¢¥BÔSR¢¢à ¢¢¥v†W&RF†RGvò6÷GFvW2vVçBâ¢¢V6‚F¶W2F†RæV&W7Bg&VRÆGFVBÆ÷B¢§F†Bæò6öÖÖ—GFV@¦&Æö6²&V6—R†2Ç&VG’7ö¶Vâf÷"¢¢(	BF†R&V6—W2æÖRF†V—"÷VâÆ÷G2æB6’v‡’Âæ@§F¶–æröæRv÷VÆB&Ww&—FR&6VÂF†B†2ÆæFVBâ'V–ÆF–ær¦¢Ö÷fW2¢£ƒ2Ò¢¢FòÆ÷Brö`¦&ÆµöÆ¶U÷vVÆÇ6Â'V–ÆF–ær¦"¢¢£c’Ò¢¢FòÆ÷Bröb&ÆµöÆ¶UöÆ6ÆÆVÂ&÷F‚öâF†R&æFöÇ€¦g&öçFvRf6–ærF†R7V&RâF†R—"—2¢§7Æ—B¢¢ÂæBF†B—27FFVB&F†W"F†â†–FFVã¢F†P¦öæÇ’w&÷VæBF†Bv÷VÆB†fR¶WBF†VÒöâöæR&Æö6²v2#ÒgW'F†W"öfbæBf6VBGvð¦F–ffW&VçB7G&VWG2ÂæBöæRGfW'F—6VÖVçBöffW&–ærGvò'V–ÆF–æw2v2æWfW"7FFVÖVçBF†@§F†W’6†&VB†öÆF–ærà ¢¢¥F†RVÆWfVçF‚³#ÖV7W&VÖVçB—2öb¢¢6'&–VBÖ÷fW"–çfVçFVBW'6öç2&VæÖVBÂv–ç7@£"ÖöbÓBBÔRÂcÖöbÓ‚BBÔBÂcrÖöbÓbBBÔ2ÂS’ÖöbÓBBBÔ"ÂrÖöbÓ"@¥BÔÂs"ÖöbÓBBÔÂ’ÖöbÓ“‚BBÔ’æB3"ÖöbÓ“bBBÔ‚â¦W&òf÷"7G'V7GW&Â&V6öà¦æBæ÷BÇV6·’öæR(	B¢§F†—2&6VÂ–ç6W'G2æB&VÖ÷fW2æòW'6öâÂ6òF†RÆÆö6F÷"†2æ÷F†–æp§Fò6†–gBâ¢¢æ–æRÖV7W&VÖVçG2–âÂF†B—2F†Rf—'7BWf–FVæ6R&÷WB§v†B¢W'GW&'2—BÂæB³# §6†÷VÆB7F'BF†W&Rà ¢¢¤ÆVFvW#¢¢¢7FæF–ær&öög2Væ6†ævVBB¢£3#"¢£²¢£3C2&VÖ–âÂöbF†VÒöâw&÷VæBF†R&ö¦V7@¦†26÷fW&vRf÷"¢¢‡v2R(	BF†R7V&R†VÆBf÷W"öbF†Rf—fR’âÆæR"—2æ÷röæR&Æö6²VçG'¦g&öÒ†f–æræ÷v†W&RFò'V–ÆBÂv†–6‚—2v†BÄäR2W†—7G2f÷"à ¢¢¤f–ÆW3¢¢¢FF÷&V6öç7G'V7F–öâóƒ3U÷&W6W'fVEöw&÷VæBæ§6öæ†æWr’+p¦FF÷&V6öç7G'V7F–öâóƒ3Uö–æfW'&VEö†÷W6V†öÆE÷&öw&ÖÖRæ§6öæ+p¦FF÷&V6öç7G'V7F–öâóƒ3UóccU÷&ööe÷&öw&ÖÖRæ§6öæ†FW&—fVB’+p¦FF÷G&6W2÷fV7F÷'2÷F†ö×6öåöÆ÷G2æ§6öæ†FW&—fVB’+rFF÷7G'V7GW&W2öƒ"Ö÷fVBÂæWr’+p§6–FV6'2+rFö72ôÄ”$U%D”U2æÖFÃr+rFö72õ5DEU2æÖF+rFö72õ$ôDÔæÖF+p¦&VæFW&W'2÷vV"ö§2ö6†ævVÆöræ§6+rF†RV&Æ—6†VBÖ—'&÷"â¢¤f÷W"FööÂf–ÆW3 ¦FööÇ2öÖV7W&U÷&W6W'fVEöw&÷VæBç–†æWrÂæBv—&VB–çFò6†V6²ç6†’À¦FööÇ2övVæW&FU÷ÆEöÆ÷G2ç–ÂFööÇ2÷&V6öæ6–ÆUóccRç–ÂFööÇ2övVæW&FUö&Æö6µö–æf–ÆÂç–¢¢(	@§F†R$ôDÔ6·2&6VÂF†BVF—G2F†R&Æö6²vVæW&F÷"Fò6’v†Bv2vVçV–æVÇ’æWrÂæ@§F†—2—2—C¢¢§F†RvVæW&F÷"†Bæò6öæ6WBöbw&÷VæBF†B—2æ÷Bf÷"6ÆRâ¢  ¢222BÔ>(
eBÔâ(	BF†R&VÖ–æ–ær&Æö6·2+r¢¥Tä4Ä”ÔTB¢  ¤öæR&Æö6²W"'VâÂ6ÖR6†RÂVçF–ÂF†R66†VGVÆR—2W††W7FVBâV6‚æÖW2—G2÷vâ&Æö6°§&Vf—‚–â—G26Æ–Ò†VF–ær6òGvò'Vç26ææ÷BF¶RF†R6ÖRöæRâ¢¥&VBF†R66†VGVÆRB–÷W"÷và¦'&—fÂFFR¢¢(	B—B—2FW&—fVBg&öÒv†B7FæG2Â6òWfW'’&Æö6²&6VÂF†BÆæG2&RÖ÷'F–öç0§F†RfÖ–Æ–W2öbWfW'’&Æö6²F†B†2æ÷Bâ&6VÂF†BÖVWG2â–ç7F—GWF–öæÂfÖ–Ç’FVfW'2—@§W"BÔ2&F†W"F†â&V6†–ærf÷"6†RÂæB&Æö6²F†B—2Ç&VG’'FÇ’'V–ÇB†2—G2F¶Và¦Æ÷G2FW&—fVB&F†W"F†âWF†÷&VBW"BÔBà ¢¢¥F†R'VÆW2&Ræ÷r6ö×ÆWFRVæ÷Vv‚F†B&Æö6²&6VÂ6†÷VÆBæVVBæò&wVÖVçBöb—G2÷vâ&W–öæ@¦—G2'&ævVÖVçBæ÷FRâ¢¢FVfW'&Â…BÔ2’ÂFW&—fVBö67Wæ7’v—F‚—G2f—fR&VgW6Ç2…BÔB’æBF†P§F‡&VR×FW7BF÷F–öâ'VÆR…BÔ&‚²BÔR’ÆÂÆ—fR–â6öFR÷"–âF†R&öw&ÖÖRw2ÖWF†öFÆ—7BÂæ@¥BÔR6†ævVBæòFööÂBÆÂâ'VâF†Bf–æG2—G6VÆbVF—F–ærFööÇ2övVæW&FUö&Æö6µö–æf–ÆÂç–†0¦ÖWB6öÖWF†–ærvVçV–æVÇ’æWræB6†÷VÆB6’v†B—Bv2–â—G2$ôDÔVçG'’à ¢¢¤÷VâgFW"BÔbÂ&RÖFW&—fVBg&öÒF†R&öw&ÖÖRF†B&6VÂ6öÖÖ—GFVB(	B&ööb7&÷72ôäP¦VçG'“¢¢¢&Æµ÷&æFöÇ…öFV&&÷&æ†C6’â¢¦&Æµ÷&æFöÇ…öÆ6ÆÆV—2vöæRg&öÒF†—2Æ—7Bf÷ ¦vööB¢£¢BÔbf÷VæB—Bv2F†RV&Æ–27V&RæB&W6W'fVB—BÂ6òF†Rf÷W"&öög2—B†VÆBvVçB&6°§FòF†RF—7G&–7B&Ææ6RâF†R&÷r—26Æ÷6VBà¦&Æµ÷&æFöÇ…öÆ6ÆÆV—2¢§F†RV&Æ–27V&R&Æö6²¢¢(	B—BÇ&VG’6'&–W2F†R6öö²6÷VçG¦6÷W'F†÷W6RÂF†RW7G&’VâæB&÷F‚w&–v‡B'V–ÆF–æw2FòÆWBÂ6ò—B'&—fW2v—F‚f÷W"öbV–v‡BÆ÷G0§F¶VâæB—2F†Rf—'7B÷VâVçG'’v†÷6R7FæF–ær&öög2&RÆÂ&W6V&6‚ÖÆ–W"&V6÷&G2&F†W"F†à§F†—2&öw&ÖÖRw2÷vââ&Æµ÷&æFöÇ…öFV&&÷&æ—27F–ÆÂæ÷B&Æö6²&6VÂf÷"F†R6ÖR&V6öâ—Bv0¦æ÷BöæRgFW"BÔC¢öæRFVÇB&ööbF†B6âöæÇ’&RFVfW'&VBv—F‚—G2&V6öâÂ6òBÔ6‚w2&&6¶f–ÆÂÀ¦æ÷rC2"7F—27FÆRâ¢¥F†R6÷WF‚vFW"&÷r—26Æ÷6VBÂÆ¶RæBÖ&¶WBv—F‚—BÂæB&æFöÇ‚@¤g&æ¶Æ–âæBB6Æ&²æ÷rFöò¢£²&÷F‚÷VâVçG&–W2&RöâF†R&æFöÇŽ(	5v6†–æwFöâ&÷rà¢¢¥F†—2Æ—7B—26öçfVæ–Væ6RæBvöW27FÆRF†RÖöÖVçBF†RæW‡B&6VÂÆæG2¢¢(	BF†R66†VGVÆP§&RÖ÷'F–öç2WfW'’÷Vâ&Æö6²V6‚F–ÖRöæR6Æ÷6W2â&RÖFW&—fR—BÂFòæ÷BG'W7B—Bâv†BBÔ`¦wV&çFVW2ÂæBv†BF†RÆ—7B—G6VÆbFöW2æ÷BÂ—2F†Bv†FWfW"–÷R&RÖFW&—fRv–ÆÂd•C¢æò&Æö6°¦—2FVÇBÖ÷&R&–æ6—Â&öög2F†â—B†2g&VRÆ÷G2ÆW72öæRÂæBæò&Æö6²—2FVÇB–&@¦'V–ÆF–ærv—F†÷WB&ööbFò7FæB—B&V†–æBà ¢ÒÒÐ ¢22ÄäR2(	BD„RT5DU$âäB4õUD„U$âu$õTäB+r÷VæVB##bÓ‚ÓBöâF†R÷væW"w2–ç7G'V7F–öà £â¢$–b–÷RæVVBFòW‡FVæBF†RF÷vâV7BFòFB÷VÆF–öâF†B—2f–æR(
b'WB–÷R×W7BÖ¶P£â7W&RF†BF†RW‡FVç6–öâöbF†R6—G’ÖF6†W2F†R&VÂvVöw&†–2Ö2öbF†R6—G’ÂÆ–¶Rv†W&P£âF†RVæ–ç7VÆ6öÖW2F÷vâv—F‚F†R6æB&'26†÷VÆB&R67W&FRâ'WB’FöâwBF†–æ²†÷W6W2&P£â–â×V6‚öb—B&V6W6Röbf÷'BFV&&÷&ââ–÷R6†÷VÆB&R&ÆRFòFVf–æRgW'F†W"6÷WF‚g&öÐ£â67W&FRÖ2â"¢(	B¶Wf–âÂ##bÓ‚ÓBÂ7WÇ––ærGvò66ç2öb¢¤Ööb6†–6vò–âƒ3¢¢à ¢¢¥v‡’F†—2ÆæRW†—7G2â¢¢F†R&ööb&öw&ÖÖR—2÷WBöb&ööÒâ#S&öög27FæBæBCB&VÖ–âÀ¦'WBöæÇ’¢£ƒb6—Böâw&÷VæBF†R†V–v‡Ff–VÆB7W'&VçFÇ’6÷fW'2¢£²F†R÷F†W"¢£3#‚†fRæ÷v†W&P§Fòvò¢¢âÆæR"†—G2F†BvÆÂ–â&÷WBF’æB†ÆbâF†—2ÆæRÖ¶W2F†Rw&÷VæBÂæB—@¦—2F†R÷væW"w2–ç7G'V7F–öâF†BÖ¶–ær—B—2Æ–6Vç6VB§&÷f–FVBF†RvVöw&‡’—2&VÂ¢à ¢222D„RE$ÂæB—Bv–ÆÂ6F6‚'VææW"v†ò6¶–×0 ¢¢¥F†R7WÆ–VB6†VWB—2FFVBƒ3âF†R66VæR—2ƒ3RÓrÓÂæBF†R†&&÷W"v27WB–à¦&WGvVVââ¢¢FF÷FW'&–âöWö6‡2öSƒ3Eö†&&÷%ö7WBöW†—7G2&V6—6VÇ’&V6W6RF†B7WBÖ÷fVBF†P§&—fW"w2Ö÷WFƒ¢&Vf÷&R—BÂF†R6†–6vò&—fW"GW&æVB6÷WF‚&V†–æB6æB&"æBVçFW&VBF†RÆ¶P§vVÆÂ&VÆ÷rF†Rf÷'C²gFW"—BÂ7G&–v‡B6†ææVÂæB–W'2vVçBF‡&÷Vv‚F†R&"â'VææW"v†ð§G&6W2F†Rƒ3÷WFÆWB–çFòF†Rƒ3R66VæRv–ÆÂ†fRÖ÷fVBF†R&—fW"w2Ö÷WF‚'’6WfW&Â‡VæG&V@¦ÖWG&W2æBv–ÆÂ†fRFöæR—B6öæf–FVçFÇ’Âg&öÒ&VÂÖà ¥v÷'6RÂF†R6†VWB6'&–W2Æ&VÂ&VF–ær¢¢'&W6VçB÷WFÆWBöb&—fW""¢¢â¥&W6VçB¢ÖVç2F†P§V&Æ–6F–öâw2&W6VçBÂæ÷Bƒ3æB6W'F–æÇ’æ÷Bƒ3Râ—B—2&WG&÷7V7F—fRææ÷FF–öâöâ§&WG&÷7V7F—fRÖâF†R6ÖRvöW2f÷"—G2ƒ"Ö&¶–æw2‡F†R6×ÂF†R7W'&VæFW"ÂF†RÖ767&P§6—FR“¢F†÷6R&RÖVÖ÷&–ÂÆ&VÇ2Æ6VB'’ÆFW"†æBÂæ÷BfVGW&W27FæF–ær–âƒ3RÂæ@¦æ÷F†–ær–âF†—2ÆæRÖ’&VæFW"F†VÒ27V6‚à ¢¢¥6òF†RF—f—6–öâöbÆ&÷W"—2f—†VBÂæB—2æ÷B'VææW"w26†ö–6S¢¢  §ÂVÆVÖVçBÂG&—fW"ÂF†Rƒ36†VWBw2&öÆRÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×À§ÂÆ¶R6†÷&RÂ6æB&"Â†&&÷W"7WBÂ–W'2ÂF†RöÆB6÷WF‡v&B6†ææVÂÂ¢¥w&–v‡Bƒ3B¢¢†Ç&VG’3&Rw2G&—fW"’Â6÷'&ö&÷&F–öâöæÇ’À§ÂÆæB6Æ–×2Â÷væW'2ÂæBv†W&R6WGFÆVÖVçB7GVÆÇ’&V6†VBÂ¢§F†Rƒ36†VWB¢¢Â&–Ö'’À§Â7G&VWBæB&Æö6²vVöÖWG'’Â¢¥F†ö×6öâÆBƒ3¢¢²¢¤†F†v’ƒ3B¢¢Â6÷'&ö&÷&F–öâöæÇ’À§ÂF†Rf÷'Bw2&W6W'fF–öâW‡FVçBÂ¢§F†Rƒ36†VWB¢¢²æG&V2&÷6RÂ&–Ö'’À ¥F†R&"w2¦f÷&Ò¢6öÖW2g&öÒw&–v‡B&V6W6Rw&–v‡B—27W'fW’f—fR–V'26Æ÷6W"FòF†RF&vW@¦FFRæB—2Ç&VG’F†RÖ7FW"v'–ær&7FW"âF†Rƒ36†VWB6—2v†ò†VÆBv†–6‚w&÷VæB(	BF†P§F†–ærw&–v‡BFöW2æ÷B6’ÂæBF†RF†–ærF†—2ÆæR7GVÆÇ’æVVG2à ¢222BÔS(	B&Vv—7FW"F†Rƒ36†VWB26÷W&6R+r¢¤DôäR##bÓ‚ÓB¢  ¦FF÷6÷W&6W2öæG&V5óƒƒEö6†–6võóƒ3öÖæ§6öæ²Fö72õ$U4T$4‚ö6†–6võóƒ3ö6Æ–×2æÖFà ¢¢¤–FVçF–f–VB'’÷Væ–ærF†RvRÂæ÷B'’–æfW&Væ6S¢¢¢æG&V2föÂâƒƒƒB’ÂföÆBÖ÷WB–ç6W@¦f6–ærâ.(	32Ò–çFW&æWB&6†—fRÆVb¢¦ã#C¢¢â7&÷72Öf—†VB&V6W6RÆVbã#C&—2â0¦6''––ærF†R†'&—6öâ†&&÷W"ÖÇ&VG’&Vv—7FW&VB†W&RÂv†–6‚–ç2F†RÆVb×Fò×vRöfg6WBà¥&–v‡G2vW&RÇ&VG’6WGFÆVB(	BF†RföÇVÖR—2æG&V5óƒƒE÷cÂV&Æ–2FöÖ–âà ¢¢¥v†BF†R&6VÂf÷VæBÂæB—B6†ævW2ÆæR2w26†S¢¢  £â¢¤—B—2ÆæB×F—FÆRÖâæÖR—2æ÷B†÷W6Râ¢¢F†RÆFRw2÷vâ&–çFVBæ÷FR6—2F†P¢æÖW2&R'&–Ö'’FVçFVW2Â÷"W'6öç2'’v†öÒVçG'’v2ÖFRÂVçFW&VB÷"FVçFVB"â6ò¢æÖVBG&7BÖ’¢¦æWfW"¢¢Æ–6Vç6Râæöç–Ö÷W2&ööbÂæBBÔSBw2VÆ–v–&–Æ—G’'VÆR×W7Bæ÷@¢&VB&æÖVB(y"'V–ÆF&ÆR"âF†R†æFgVÂöb7G'V7GW&W2F†RÆFR7GVÆÇ’G&w2—2f"&WGFW ¢wV–FRFòv†W&R'V–ÆF–ær†B†VæVBF†âF†RvÆÂöbæÖW2—2(	Bv†–6‚7W÷'G2F†R÷væW"w0¢–ç7F–æ7BF†B†÷W6W2vW&Ræ÷B7&VB7&÷72F†—2w&÷VæBà£"â¢¥F†RVçG'’v–æF÷r—2ƒ#Ž(	3ƒ3b(	B7BF†R66VæRFFRâ¢¢6öÖRæÖW2&VÆöærFòV÷ÆRv†ò†@¢æ÷BVçFW&VBF†RÆæBöâƒ3RÓrÓÂæBF†R6†VWBFöW2æ÷BFFR–æF—f–GVÂVçG&–W2à£2â¢¤—B—2âƒƒB6ö×–ÆF–öâF†BÆ&VÇ2—G2æ6‡&öæ—6×2'&W6VçBâ"¢¢$U4TåB4äÆ—2F†P¢–ÆÆ–æö—2bÖ–6†–vâ6æÂÂ¢¦æ÷B6ö×ÆWFVBVçF–ÂƒC‚¢¢âÇ6ò&W6VçB6÷W'B†÷W6R7V&VÀ¢&W6VçB÷WFÆWBöb&—fW&ÂæB7G&VWBw&–BF†Ræ÷FR—G6VÆbF—66Æ–×22÷7BÓƒ3âWfW'¢'&W6VçB"öâF†—2ÆFR—2f–gG’Öf÷W"×–V"æ6‡&öæ—6Òà£Bâ¢¥GvòÆFW2–âF†RföÇVÖR6†&RF†RæÖR¢¢(	BÖ†–ç6WBÂâ.(	32’æB–7F÷&–Âf–Wp¢‡âcB’â6—FRF†RÆVbÂæWfW"F†RæÖRà£Râ¢¥F†R÷væW"w2Gvò66ç2&Ræ÷BF†R6ÖRFö7VÖVçBâ¢¢F†RÆ–æRÖ'B—77VR—2F–ffW&Vç@¢&VæFW&–ærÂVæ–FVçF–f–VBÂæB¢¦Ö’æ÷B&R6—FVB¢¢VçF–Â—B—2à£bâ¢¥BÔS"Ö’æVVBæòæWrWf–FVæ6Rf÷"F†R&"â¢¢†'&—6öåóƒ3÷&—fW%öÖ÷WF†(	BÇ&VG’†VÆB(	@¢G&w2F†R6æB&"ÂF†R%6æBæBw&fVÂ"w&÷VæBæBF†RöÆB6÷WF‡v&B6†ææVÂ–âÆâà¢6†V6²—B&Vf÷&Rvö–ærÆöö¶–ærà ¢222BÔS‡7V2’(	BF†R÷&–v–æÂ&6VÂFVf–æ—F–öà ¤æ÷F†–ærVÇ6R–âF†—2ÆæRÖ’6—FRF†RÖVçF–Â—B&W6öÇfW2–âFF÷6÷W&6W2öâ¢¤æWfW"–çfVç@¦6÷W&6R¢¢(	BF†B'VÆR—2æ÷B&VÆ†VB&V6W6RF†R÷væW"7WÆ–VBF†R–ÖvRà ¥F†R–FVçF–f–6F–öâ—2W‡V7FVBFò&R6†V¢æG&V5óƒƒE÷c—2Ç&VG’&Vv—7FW&V@¢‡V&Æ–2FöÖ–âÂF–W"2Â&6†—fRæ÷&röFWF–Ç2ö†—7F÷'–öf6†–6vóæG&’æ@¦†'&—6öåóƒ3÷&—fW%öÖ÷WF†Ç&VG’6—FW2âã#C&öbF†B6ÖRföÇVÖRâF†RÆFR—2fW'¦Æ–¶VÇ’–â—Bâ¢¥fW&–g’F†C²Fòæ÷B77VÖR—Bâ¢¢–b—B—2ÂF†—2—2ÆFR6—FF–öâv—F†–â§6÷W&6RÇ&VG’†VÆBÂæB&–v‡G2&R6WGFÆVBâ–b—B—2æ÷BÂf–æBF†R7GVÂV&Æ–6F–öâæ@§&V6÷&B—Bv—F‚v–&6²6æ6†÷BÆ–¶Rç’÷F†W"à ¥GvòVF—F–öç2&R–â†æBæBF†W’&Ræ÷BF†R6ÖRFö7VÖVçC¢Æ–âÆ–æRÖ'BfW'6–öâæB¦6öÆ÷W&VBfW'6–öâ6''––ær7V'7FçF–ÆÇ’Ö÷&RFWF–Â‡F–Ö&W"7F—ÆRÂF†R6æÂÆæBæB66†ööÀ¥6V7F–öâ&Æö6·2ÂF†Rƒ"ææ÷FF–öç2ÂFF—F–öæÂ6Æ–ÒæÖW2’â&V6÷&B¢§v†–6‚¢¢—26—FVBf÷ ¦V6‚&VF–ærÂ&V6W6RF†W’Fòæ÷Bw&VRöâWfW'—F†–ærà ¢¢¤f–ÆW3¢¢¢FF÷6÷W&6W2óÆ–Câæ§6öæ†æWr’+rFö72õ$U4T$4‚ö6†–6võóƒ3ö6Æ–×2æÖF†æWr¢¢¤66WFæ6S¢¢¢FööÇ2ö6†V6²ç6†w&VVã²F†R&V6÷&B7FFW2ÆFRÂvRæBVF—F–öã²¦v†Eö—EöFöW5öæ÷E÷7WÇ–Æ—7BF†BæÖW2F†Rƒ3×g2Óƒ3R&ö&ÆVÒæBF†R'&W6VçB÷WFÆWB ¦Æ&VÂW‡Æ–6—FÇ’à ¢222BÔS"(	BF†Rw&÷VæBF†B×W7B7F’V×G’+r¢¤DôäR##bÓ‚ÓR¢  ¥Gvòw&÷VæG2÷WG6–FRF†RÆB&Rv—F†G&vâg&öÒF†R'V–ÆF&ÆRF÷vã¢F†R¢¥Væ—FVB7FFW0¥&W6W'fF–öâ¢¢V7Böb7FFR7G&VWBæBF†R¢§6æB&"7&÷72F†R&—fW"Ö÷WF‚¢¢âF†R&VgW6Â—0¦WF†÷&VB–âFF÷&V6öç7G'V7F–öâóƒ3Uöæõö'V–ÆEöw&÷VæBæ§6öæÂVæf÷&6VB–à¦FööÇ2övVæW&FUö&Æö6µö–æf–ÆÂç–&Vf÷&Rç’Æ6VÖVçBFW7BF†B6÷VÆBÖ6²—BÂæBvFVB'¦FööÇ2öÖV7W&Uöæõö'V–ÆEöw&÷VæBç’ÒÖvFV27FWöbFööÇ2ö6†V6²ç6†âgVÆÂFÖ—76–öâ–à¦Fö72ôÄ”$U%D”U2æÖF¢¤Ã‚¢¢à ¢¢¥F†RÖV7W&VÖVçB—2F†R&6VÂâ¢¢öbF†R¢£#ã‚†¢¢öbÖöFVÆÆVBÆæB7FæF–ær&÷fRF†RvFW §7W&f6RÂ¢£3"ã†(	B#bãRR¢¢—2öæRöbF†RGvó¢F†R&W6W'fF–öâ¢£#"ãSr†¢¢ÂF†R&"¢£’ãS2†¢¢à¤WfW'’vFRF†—2&ö¦V7B†B6¶VBv†WF†W"Æ6VÖVçB6ÆV&VB—G2æV–v†&÷W'2Â—G2Æ÷BÆ–æW2ÂF†P§ÆGFVB&öGv’ÂF†RÖöFVÆÆVBFW'&–âæBF†R&VÆ–Vc²¢¦æöæRöbF†VÒ6¶VBv†WF†W"F†Rw&÷VæBv0¦WfW"f÷"6ÆRâ¢¢Ãrf÷VæBF†B†öÆR–ç6–FRF†RÆBBBÔbâF†—2—2F†R6ÖR†öÆRÂf÷W"F–ÖW0¦Æ&vW"Â÷WG6–FR—Bà ¢¢¤f÷W"f–æF–æw2F†B&Ræ÷BF†RöÇ–vöç2â¢  £â¢¤æ÷F†–ær†BFòÖ÷fRÂæBF†B—2â66–FVçB&F†W"F†â'VÆRâ¢¢6WfVçFVVâ7G'V7GW&R&V6÷&G0¢7FæBöâF†RGvòw&÷VæG2(	BF†Rf÷'Bw27Fö6¶FRÂ&FRæBVÆWfVâ'V–ÆF–æw2ÂF†Rv'&—6öâv&FVâÀ¢F†Rƒ3"Æ–v‡F†÷W6RÂ&VV&–Vâw2†öÖW7FVBæB&&âÂæBF†R6÷WF‚–W"Âv†–6‚F÷V6†W2&÷F€¢&V6W6RF†B—2v†B–W"'Vâ÷WBF‡&÷Vv‚&"FöW2(	BæB¢§¦W&òæöç–Ö÷W2&öög2¢¢âWfW'¢&V6—RFòFFRv2¶W–VBFòÆGFVB&Æö6²æBF†R&W6W'fF–öâv2æWfW"ÆGFVBâBÔbv2æ÷@¢6òÇV6·“¢GvòFö7VÖVçFVB6÷GFvW2†B&VVâ7FæF–æröâF†RV&Æ–27V&Rf÷"f—fRF—2à£"â¢¥F†R&VgW6Â—2Fö7VÖVçFVFæBF†R&÷VæF'’—2–æfW'&VFÂæBw&F–ærF†VÒFövWF†W"v÷VÆ@¢†fR&VVâF†RW'&÷"â¢¢æG&V2v—fW2sRãc’7&W2ÂF†R6÷WF‡vW7Bg&7F–öæÂV'FW"öb6V7F–öâÀ¢VçÆGFVBÂ÷WG6–FRF†RF÷vâw2V7FW&â&÷VæF'’ÂVæFW"&VV&–Vâw2&RÖV×F–öâ6Æ–Òf–ÆVBf—fP¢vVV·2&Vf÷&RF†R66VæRFFRâF†RöÇ–vöâ—2F–ffW&VçB6Æ–Ó¢¢¦æòfW'FW‚öb—B—2WF†÷&VBâ¢ ¢—G2vW7BæB6÷WF‚6–FW2&RF†RV'FW"w2Gvò7W'fW’Æ–æW2&W6öÇfVBg&öÒöæR6öÖÖ—GFVB6öçG&öÀ¢ö–çB(	BsÂ7FFRbÖF—6öâÂv†÷6R÷vâæ÷FR†26–B6–æ6RF†RFGVÒv÷&²F†B¤ÖF—6öâw2Æ–æP¢6öçF–çVW2V7B2F†R&W6W'fF–öâw26÷WF‚&÷VæF'’¢(	B6'&–VBöâF†RÆBw2V7B×vW7B&V&–ærÀ¢v†–6‚Æ¶RÂ&æFöÇ‚æBv6†–æwFöâw&VRöâFòF†R6—‡F‚FV6–ÖÂâ—G2F†—&B6–FR—2F†P¢6öÖÖ—GFVBvFW&Æ–æRF†RG&6R—G6VÆb6ÆÇ2§F†Rf÷'BFV&&÷&â&W6W'fF–öâw2Æ¶R6†÷&R¢à£2â¢¥F†RFW&—fVBöÇ–vöâ—22ã"R6†÷'BöbF†RFö7VÖVçFVB7&VvRæB—2äõBGVæVBFò6Æ÷6R—C ¢cRãs7&W2v–ç7BsRãc’â¢¢F‡&VR6æF–FFW2ÂæöæRÖV7W&VB(	Bg&7F–öæÂV'FW"—27W'fW–V@¢FòF†RÆ¶Rw2ÖVæFW"Æ–æRÂv†–6‚Æ–W2V7BöbF†Rƒ3BvFW&Æ–æRæBVæ6Æ÷6W2F†RöÆB6÷WF‡v&@¢6†ææVÂw2vFW#²F†RG&6VB6†÷&R6'&–W2²òÓ#Ó²F†R6†÷&RG&6Rw2÷vâæ÷FR6—2—BÆVfW2—G0¢v–æF÷r6÷WF‚öbÖF—6öââ¢¥6òF†RöÇ–vöâ—2dÄôõ"¢¢ÂæBF†RfÆö÷"—276W'FVB&F†W"F†à¢†÷VC¢F†RvFR&RÖ6÷VçG2WfW'’6VÆÂöbÖöFVÆÆVBÆæB&÷fRF†RvFW"7W&f6RF†B7FæG2V7Bö`¢F†RvW7BÆ–æRÂæ÷'F‚öbÖF—6öâÂ6÷WF‚öbF†RÖ–â7FVÒæB–ç6–FRæV—F†W"öÇ–vöââ¢¤—B—2¦W&ð¢FöF’¢¢ÂæB—B—2v†Bv–ÆÂf–Âv†Vâ¢¥BÔS2¢¢W‡FVæG2F†RFW'&–â7BF†RG&6VB6†÷&Rà£Bâ¢£Sc"6VÆÇ2Æöö¶VBÆ–¶R†öÆRæBvW&Ræ÷BöæRâ¢¢F†Rf—'7B72fÆvvVBF†BÖç’Væ6Æ76–f–V@¢G'’6VÆÇ2&WGvVVâF†R&W6W'fF–öâw2V7B&æ²æBF†R&#²ÖV7W&VBÂWfW'’öæRöbF†VÒÆ–W0¢&WGvVVâ¢¢ÓãÒæBãÒ¢¢(	BF†RvFW&Æ–æRFöÆW&æ6R&æBF†R'V–ÆF&ÆRFW7B6'&–W2Âæ÷@¢w&÷VæBâ&÷fRF†RvFW"7W&f6RF†R6÷VçB—2¦W&òÂv†–6‚—2v‡’F†RvFR—2w&—GFVâv–ç7BF†P¢vFW"7W&f6R&F†W"F†âv–ç7BF†RFöÆW&æ6Rà ¢¢¤&÷F‚76W'F–öç2vW&R&÷fVBFòf–Â&Vf÷&RV—F†W"v2G'W7FVB¢¢ÂF†R7FæF&B³#ræB³#‚vW&P¦†VÆBFó¢&VÖ÷f–æröæRW&Ö—GFVBVçG'’f–Ç2F†RvFR'’æÖRÂæB6‡&–æ¶–ærF†R&"öÇ–vöâFò§6Æ—fW"f–Ç2F†RVæFW"Ö6÷fW&vR6÷VçBv—F‚¢£Ã¢¢6VÆÇ2à ¢¢¥F†Rf÷W"÷VâVW7F–öç2F†—2&6VÂF–Bæ÷B6Æ÷6RÂæBF–Bæ÷B&WFVæBFòâ¢¢F†Rƒ3ÆFRG&w0¢¢¤Ö&²&VV&–Vâw2¢¢Â¢¤VÆ–¦‚vVçGv÷'F‚w26&–â¢¢Â¢¤Æg&Ö&ö—6Rw26&–âæB7F÷&R¢¢æ@¢¢¥÷'FW"w2Æör6&–â¢£²æöæR†2&V6÷&BÂâW†6ÇW6–öâÂ÷"FW7FVB7W'f—fÂFòƒ3RÓrÓâF†P¦æWrF—7÷6—F–öâF&ÆRBF†Rfö÷BöbFö72õ$U4T$4‚ö6†–6võóƒ3ö6Æ–×2æÖF66÷VçG2f÷"WfW'§7G'V7GW&RF†RÆFRG&w2æBÆ—7G2F†W6Rf÷W"2÷VâÂv†–6‚—2F†RF—7÷6—F–öâBÔS"w266WFæ6P¦ÆÆ÷w2æBF†RöæÇ’†öæW7BöæRf–Æ&ÆRg&öÒâƒƒBÆæB×F—FÆR6ö×–ÆF–öââ¢¤Ö&²&VV&–Vâw2—0§F†RöæR–ç6–FRF†RÖöFVÆÆVB&VæB—2F†RöæRv÷'F‚F¶–ærf—'7Bâ¢¢BÔS"ÖFRæòæWr7G'V7GW&P§&V6÷&BæBæòæWrW†6ÇW6–öâà ¢¢¥v†B—B6÷7G2F†R&ööb&öw&ÖÖS¢æ÷F†–ærF†Bv2÷vVBâ¢¢F†Rsr&öög2–à¦6÷WF…÷ÆEö&W–öæEö6öÖÖ—GFVEö6öçG&öÆv—Böâ7G&VWB6öçG&öÂ&V6†–ærV7Böb7FFRæB6÷WF‚ö`¥v6†–æwFöââF†—2&6VÂ&VÖ÷fW2âç7vW"F†Bv2æWfW"f–Æ&ÆR(	BF†Rw&÷VæB–ÖÖVF–FVÇ’V7Bö`¥7FFR—2æ÷B6öÖ–ærÂBç’FFRÂ&V6W6R—B—2F†R&W6W'fF–öâà ¢¢¤f–ÆW3¢¢¢FF÷&V6öç7G'V7F–öâóƒ3Uöæõö'V–ÆEöw&÷VæBæ§6öæ†æWr’+p¦FööÇ2öÖV7W&Uöæõö'V–ÆEöw&÷VæBç–†æWr’+rFööÇ2övVæW&FUö&Æö6µö–æf–ÆÂç–+rFööÇ2ö6†V6²ç6†+p¦Fö72õ$U4T$4‚ö6†–6võóƒ3ö6Æ–×2æÖF+rFö72ôÄ”$U%D”U2æÖFÃ‚²FFöÆ–&W'F–W2æ§6öæ+p¦Fö72õ5DEU2æÖF+rFö72õ$ôDÔæÖF+r&VæFW&W'2÷vV"ö§2ö6†ævVÆöræ§6+rF†RV&Æ—6†VBÖ—'&÷"à¢¢¤æò7G'V7GW&R&V6÷&B6†ævVBÂæBæòvVöÖWG'’v2&¶VBâ¢  ¢222BÔS"‡7V2’(	BF†R÷&–v–æÂ&6VÂFVf–æ—F–öà ¥F†R÷væW"w2&VB(	B¢$’FöâwBF†–æ²†÷W6W2&R–â×V6‚öb—B&V6W6Röbf÷'BFV&&÷&â"¢(	B—0§F†R7V'7Fæ6RöbF†—2&6VÂÂæB—B—26Æ–ÒFò&RWf–FVæ6VBÂæ÷B77VÖVBà ¥F†R¢¦Ö–Æ—F'’&W6W'fF–öâ¢¢V7BöbF†RF÷vâ—2æ÷B÷&F–æ'’'V–ÆF–ærw&÷VæBÂæBF†R¢§6æ@¦&"¢¢—2æ÷B'V–ÆF–ærw&÷VæBBÆÂâ&÷F‚×W7B&V6öÖRöÇ–vöç2F†R–æf–ÆÂvVæW&F÷"&VgW6W2À¦–âF†R6ÖRv’$TeU4TEôdÔ”Ä”U6Ç&VG’&VgW6W26—f–2&öög3¢âæöç–Ö÷W2&ööbÆ6VBöâF†P§&W6W'fF–öâ÷"öâF†R&"—2æ÷BÆW6–&ÆR–æfW&Væ6RÂ—B—2âW'&÷"F†R66†VGVÆRÖFP¦&V6W6Ræ÷F†–ær7F÷VB—Bà ¢¢¥F†—2&6VÂÖ’æ÷B6–×Ç’6‡&–æ²F†R'V–ÆF&ÆR&VæB6ÆÂ—BFöæRâ¢¢v†W&RæÖV@§7G'V7GW&RvVçV–æVÇ’7FööBöâ÷"æV"F†R&W6W'fF–öâÂF†Rƒ36†VWBæÖW26WfW&Â(	BF†R¶–ç¦–P¦†÷W6RÂ&VV&–Vâw27F÷&RÂF†R&F—7FR&VV&–Vâf–VÆBÂF†R7&gG2†÷W6R(	BæBF†÷6R&P¢§&V6÷&G2¢Âæ÷Bæöç–Ö÷W2–æf–ÆÂâv†WF†W"V6‚v27F–ÆÂ7FæF–æröâƒ3RÓrÓ—2W"×&V6÷&@§VW7F–öâv—F‚âç7vW"÷"âW†6ÇW6–öâÂæWfW"wVW72à ¢¢¤f–ÆW3¢¢¢FF÷FW'&–âþ(
böæõö'V–ÆBæ§6öæ†æWr’+rFööÇ2övVæW&FUö&Æö6µö–æf–ÆÂç–+p¦FFöW†6ÇW6–öç2æ§6öæ+rFö72ôÄ”$U%D”U2æÖF ¢¢¤66WFæ6S¢¢¢FööÇ2ö6†V6²ç6†w&VVã²F†RvVæW&F÷"&VgW6W2F†R&W6W'fF–öâæBF†R&"æ@§6—2v‡“²WfW'’æÖVB6Æ–Òg&öÒF†R6†VWB—2V—F†W"7G'V7GW&R&V6÷&BÂâW†6ÇW6–öâv—F‚¦6—FF–öâÂ÷"Æ—7FVB2â÷VâVW7F–öâ(	Bæ÷F†–ær6–ÆVçFÇ’G&÷VBà ¢222BÔS2(	Bf–æ—6‚F†R†V–v‡Ff–VÆBV7B+r¢¥Tä4Ä”ÔTB+rgFW"BÔS+räTTE2D„R$´R¢  ¢¢¥F†—2—23&V&VÆ÷rÂæ÷BæWr&6VÂ(	B&VB—B&Vf÷&R7F'F–ærâ¢¢&6VÂ†’—2FöæRæB—@¦Ç&VG’ÖV7W&VBF†Rç7vW"öfbw&–v‡C¢F†R&÷‚×W7B&V6‚&÷WB¢¤R³s¢¢Â&÷Vv†Ç£"ã¶Ò9rãr¶ÒÂã##F²6×ÆW2BF†R7W'&VçB"ãRÒ6VÆÂâW6R6ö'6W"6VÆÂV7BöbF†R'V–Ç@¦&Æö6·2Âv†W&RF†RWf–FVæ6RFöW2æ÷B7W÷'B"ãRÒFWF–Âç—v’à ¤æWrvVöÖWG'’'&—fW2f–6†–6vòÓFBÖ&¶Rç–ÖÆ2"–çFòFWfâF†RFF†Æb6†—2†W&Ræ@§6—26òà ¢222BÔSB(	BF†R6÷WF†W&â'V–ÆF&ÆRw&÷VæBÂæBF†R&RÖ÷'F–öæVB66†VGVÆR+r¢¥$TeUDTB##bÓ‚Ó#B…BÓ#b’¢  ¢¢¥F†W&R—2æò6÷WF†W&â'V–ÆF&ÆRw&÷VæBFòv–FVâöçFòÂæBF†R&6VÂw2÷vâ66WFæ6R—2v†@§&VgWFW2—Bâ¢¢BÔSB6–B&ööbÖ’7FæBöæÇ’v†W&RF†Rw&÷VæB—2¦6÷fW&VB'’F†R†V–v‡Ff–VÆBä@¦†—7F÷&–6ÆÇ’ÆW6–&ÆR¢ÂæBFöÆBF†RæW‡B'VâFòv–FVâF†RVÆ–v–&ÆRw&÷VæB6÷WF‚âÖV7W&VBv–ç7@§F†R6öÖÖ—GFVB†V–v‡Ff–VÆB'’FööÇ2öÖV7W&U÷6÷WF†W&åöw&÷VæBç–ÂF†Rf—'7B6öæF—F–öâ—2Ç&VG§Vç6F—6f–&ÆRWfW'—v†W&R6÷WF‚öbF†RF÷vã¢¢§F†RÖöFVÆÆVB&÷‚VæG2BÆö6ÂâÓCÒÂæBF†BÆ–æP¦fÆÇ2”å4”DRv6†–æwFöâ7G&VWBw2÷vâƒgBÆGFVB6÷'&–F÷"â¢  §ÂÂÖV7W&VBÀ§ÂÒÒ×ÂÒÒ×À§ÂÆæB&÷fRF†RvFW"7W&f6R6÷WF‚öbv6†–æwFöâw2ÆGFVB6÷'&–F÷"Â¢£ãƒ’†¢¢ƒ36VÆÇ2’À§Âââæöb—B–âF†R6÷WF‚F—f—6–öâÂ¢£ã†¢¢(	BWfW'’6VÆÂ—2vW7BöbÆö6ÂRÓÂF†RvW7BF—f—6–öâ&æ²7&÷72F†R6÷WF‚'&æ6‚À§Âv6†–æwFöâw2÷vâ6÷'&–F÷"Ç––æröfbF†Rf–VÆBÂ¢£ã32†¢¢Â÷fW"¢£ƒ“’Ò¢¢öb—G2ÆVæwF‚ÂWFò¢£rã#’Ò¢¢FVWÀ§ÂÖF—6öâ7G&VWB(	BF†RÆBw26÷WF‚&÷VæF'’(	B&VÆ÷rF†Rf–VÆBw26÷WF‚VFvRÂ¢£#Rã"Ò¢¢B7FFRÂ’ã"ÒBÖ&¶WBÀ§ÂF†RÆBw2Æ7BF–W"Âv6†–æwFöâFòÖF—6öâÂÖ&¶WBFò7FFRÂ¢£b&Æö6·2ÂC‚Æ÷G2Âbã#‚†Âöb#B&÷VæF'’ö–çG2öâÖöFVÆÆVBw&÷VæB¢¢À ¢¢¥F†R&Æö6¶W"F†RccR×&ööb&öw&ÖÖRæÖVBf÷"F†R6÷WF‚v2F†Rw&öæröæRÂæB—Bv2ö–çF–ærF†P¦æW‡B'VâBF†Rw&öærv÷&²â¢¢6÷WF…÷ÆEö&W–öæEö6öÖÖ—GFVEö6öçG&öÆ(	B#&öög2ÂF†RÆ&vW7BöbF†P§F‡&VRvFVB&Ææ6W2(	B6–B¢&æò&Æö6²V7Böb7FFR÷"6÷WF‚öbv6†–æwFöâ†2f÷W"6öÖÖ—GFV@¦6VçG&VÆ–æW2…$ôDÔ3’’"¢âG'VRÂæBF÷vç7G&VÓ¢¢¦WfW'’æ÷'F‚×6÷WF‚6öÇVÖâöbF†R6÷WF‚ÆB†0¦—G26öÖÖ—GFVB6VçG&VÆ–æR7WBBW†7FÇ’âÓCÂF†Rf–VÆBw2÷vâ6÷WF‚VFvRâ¢¢Ö&¶WBÂg&æ¶Æ–âÀ¥vVÆÇ2ÂÆ6ÆÆRÂ6Æ&²ÂFV&&÷&âæB7FFRÆÂVæBöâF†BÆ–æRæBæ÷BB7G&VWBâ7G&VWB6öçG&öÀ§7F÷2v†W&RF†Rw&÷VæBFöW2ÂæBF†R6öçG&öÂF†Bv÷VÆB6''’—BgW'F†W"—2Ç&VG’6öÖÖ—GFVB(	@¦sÂF†RÅ526÷&æW"B7FFRbÖF—6öâÂ—2â÷Vå7G&VWDÖæöFRv—F‚â–BæB2ã’Ò&W6–GVÂà¤6''’F†RÆ–æW26÷WF‚v—F†÷WBF†RFW'&–âæBF†RÆBÖöGVÆRVÖ—G26—‚&Æö6·2v†÷6RWfW'’Æ6VÖVç@¦FööÇ2övVæW&FUö&Æö6µö–æf–ÆÂç–&VgW6W2f÷"§7FæF–ær÷WG6–FRF†RÖöFVÆÆVBFW'&–â¢â¢¥F†R6÷WF†W&à§VæÆö6²—2DU%$”â&6VÂÂæ÷B'VÆRF†R&öw&ÖÖR6â&VÆ‚â¢  ¢¢¥v†BF†RFW'&–â&6VÂæVVG2Â6ò—B—2æ÷B&RÖFW&—fVC¢öæRG&6RÂæB—B—2&÷VæFVBâ¢¢F†P¦&÷‚w2åöÖ–æ—26VB'’Wf–FVæ6R&F†W"F†â'’6÷7B(	B¢'F†R6÷WF‚'&æ6‚w2G&6VBvFW"VæG2@¤âÓCBãRÂv†W&RF†Rf÷&·2G&6–ærv–æF÷r6Æ÷6W2Â6ò&÷‚&V6†–ærgW'F†W"6÷WF‚v÷VÆB6†÷r÷Và§&—&–Rv†W&RF†R&—fW"7GVÆÇ’6öçF–çVW2"¢âF†B—27FFVÖVçB&÷WBF†R¢¥6÷WF‚'&æ6‚öæÇ’¢¢à¥F†R†&&÷W"×&V6‚6†÷&VÆ–æRÇ&VG’&V6†W2¢¤âÓSƒ’ã"¢¢æBF†R6æB&"¢¤âÓC3b¢¢Â&÷F‚6÷WF‚ö`¤ÖF—6öã²F†RöÆB6÷WF‡v&B6†ææVÂ—2G&6VBF‡&÷Vv‚F†Rv†öÆRöbF†RæWrFWF‚â6òW‡FVæF–ærF†P¦&÷‚FòÖF—6öâw26÷'&–F÷"æVVG2F†R6÷WF‚'&æ6‚w2Gvò&æ·26'&–VBg&öÒ¢¤âÓCRFò&÷WBâÓS3(	@£#bÒW"&æ²¢¢(	Böfb6†VWBF†—2&ö¦V7BÇ&VG’†öÆG2ÂæBF†Vâ&¶RâWfW'—F†–ærV7BöbF†P§&—fW"–âF†BF–W"—2G'’w&÷VæBv—F‚æòvFW"–â—C¢BâÓCF†R'&æ6‚ö67W–W2Æö6ÂRÓ‚Fð¢³3RæBF†RF–W"'Vç2R³ƒ‚„Ö&¶WB’Fò³ƒ#b…7FFR’à ¢¢¤æ÷F†–ær&÷WBF†Rw&÷VæBV7Böb7FFR6†ævW2æBæ÷F†–ærv2†÷VBf÷"F†W&Râ¢¢BÔS"6WGFÆVB—C §F†B—2F†RVæ—FVB7FFW2&W6W'fF–öâÂ#"ãSr†Â&VgW6VBBç’FFRâ6òF†R6÷WF‚&Ææ6R—2vFV@¦öâW†7FÇ’öæRF†–æræ÷rÂæBF†R&öw&ÖÖR6—2v†–6‚à ¢¢¥v†B6†—VBâ¢¢FööÇ2öÖV7W&U÷6÷WF†W&åöw&÷VæBç–†æWs²F†R&W÷'BÂGvò76W'F–öç2æB§6VÆb×FW7BÂv—&VB–çFòFööÇ2ö6†V6²ç6†’+rFööÇ2÷&V6öæ6–ÆUóccRç–6ö×÷6W2F†R6÷WF‚&Ææ6Rw0¦v—F–æuööæg&öÒF†BÖV7W&VÖVçB–ç7FVBöbWF†÷&–ær—BÂæB6'&–W2F†Rf–wW&W2–à¦6÷fW&vRç6÷WF†W&åöw&÷VæF6ò66†VGVÆW"&VG2F†VÒv—F†÷WB'Vææ–ær6öÖÖæB+p¦FööÇ2ö6ö×–ÆU÷66VæRç–WG2F†RÖV7W&VB6÷WF†W&âVFvRöâF†Rw&÷VæB6&Bf—6—F÷"÷Vç2â¢¤æð§7G'V7GW&R&V6÷&BÖ÷fVBÂæò&ööbv2FFVB÷"&VÖ÷fVBÂF†RccRF÷FÂ—2Væ6†ævVBÂæBæòvVöÖWG'§v2&¶VBâ¢  ¢¢¥F†R7V66W76÷"—2BÓ#–¢¢Âf–ÆVBBF†RTUTR&÷GFöÓ¢f–æ—6‚F†R†V–v‡Ff–VÆB4õUD‚FòÖF—6öâÀ§F†RÖ—'&÷"öbBÔS2òBÓw2V7FW&âW‡FVç6–öââ—B—2F†RÆ&vW7B6–ævÆRVæÆö6²ÆVgB–âF†P§&öw&ÖÖRæB—B—2F†RöæÇ’&÷WFRFòç’öbF†R6÷WF‚w2¢£#¢¢&öög2(	B6—‚&Æö6·2BF†P§66†VGVÆRw2÷vâ3×&ööb&Æö6²66—G’—2ƒb&öög2öbw&÷VæBÂ6òF†RF–W"v÷VÆB'6÷&"F†Rv†öÆP§6÷WF†W&â&Ææ6RæB7F–ÆÂ†fR&ööÒÂv–ç7BBÓc2w2SB×&ööb6÷WF‚vFW"VæÆö6²à ¢222BÔSB‡7V2’(	BF†R÷&–v–æÂ&6VÂFVf–æ—F–öà ¥F†R÷væW"—2&–v‡BF†B6÷WF‚—2v†W&RF†R&ööÒ—3¢F†R6†VWB6†÷w2F†RF÷vâw2ÆGFVB&Æö6·2À§F†Vâ6æÂÆæBæBF†R66†ööÂ6V7F–öâ&VÆ÷rÖF—6öâÂv—F‚æÖVB6Æ–×266GFW&VBF‡&÷Vv‚âF†@¦—2&VÂÂÖVBF—7F–æ7F–öâ&WGvVVâw&÷VæBF†Bv27V&F—f–FVBæBw&÷VæBF†Bv2æ÷BÂæB—@§6†÷VÆBv÷fW&âv†W&RF†R&VÖ–æ–ær3#‚&öög2Ö’vòà ¢¢¥F†R66†VGVÆR—2FW&—fVBÂæ÷BWF†÷&VB¢¢(	BFööÇ2÷&V6öæ6–ÆUóccRç–&V6ö×WFW2F†R&VÖ–æFW ¦g&öÒv†B7FæG2(	B6òF†—2&6VÂw2¦ö"—2Fòv–FVâF†R¦VÆ–v–&ÆRw&÷VæB¢ÂF†VâÆWBF†P¦÷'F–öæÖVçBfÆÂ÷WBâ&ööbÖ’&RÆ6VBöæÇ’v†W&RF†Rw&÷VæB—2¢¦6÷fW&VB'’F†P¦†V–v‡Ff–VÆBäB†—7F÷&–6ÆÇ’ÆW6–&ÆR¢¢âv–FVæ–ærF†Rf—'7Bv—F†÷WBF†R6V6öæB—2W†7FÇ’F†P¦f–ÇW&RF†—2ÆæRv2÷VæVBFò&WfVçBà ¢¢¤f–ÆW3¢¢¢FF÷&V6öç7G'V7F–öâóƒ3Uö'V–ÆF–æuö–çfVçF÷'’æ§6öæ+p¦FööÇ2övVæW&FUö&Æö6µö–æf–ÆÂç–+rFö72õ$U4T$4‚ö6†–6võóƒ3ö6Æ–×2æÖF ¢¢¤66WFæ6S¢¢¢FööÇ2ö6†V6²ç6†w&VVã²F†RVÆ–v–&ÆRÖw&÷VæB'VÆR—27FFVB–âF†R&öw&ÖÖRæ@¦Væf÷&6VB'’F†RvVæW&F÷#²F†R&V6öæ6–Æ–F–öâ7F–ÆÂ&Ææ6W3²æò&ööb7FæG2öâF†R&"ÂF†P§&W6W'fF–öâÂvFW"Â÷"VæÖöFVÆÆVBw&÷VæBà ¢ÒÒÐ ¢222BÔSR†’(	BFFRF†R–â×F÷vâvFW"&Vf÷&Rç—F†–ærÖöFVÇ2—B+r¢¤DôäR##bÓ‚Ób¢  ¢¢¥F†RFVfW'&Â6¶VB&÷WBÆ6RæBv2&VB2F†÷Vv‚—Bç7vW&VB&÷WB66VæRâ¢¢F†P§FW'&–â7V2FVfW'2¢¦f÷W"¢¢–â×F÷vâvFW"fVGW&W2VæFW"öæR6†&VB‡&6R(	B¢&W†—7FVæ6P¦Fö7VÖVçFVBÂvVöÖWG'’6öæ¦V7GW&Â"¢(	BæBæ÷BöæRöbF†VÒ†BWfW"&VVâ6¶VBv†W&R—B7FæG2öà¢¢£ƒ3RÓrÓ¢¢âF†W’Fòæ÷Bç7vW"Æ–¶RÂv†–6‚—2F†Rv†öÆRf–æF–æs  §ÂF÷76–W"¦öæRÂfVGW&RÂBƒ3RÓrÓÂv†BFFW2—BÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§ÂBÂF†R6Æ÷Vv‚Â¢§&W6VçB¢¢†–æfW'&VB’Â7G'V7GW&RF†—2&ö¦V7BÇ&VG’7FæG2–âF†R66VæRÀ§ÂRÂ¢¥F†RV&Æ–2×7V&RöæB¢¢Â¢¦æ÷BW7F&Æ—6†VB¢¢†–æfW'&VB’Âæ÷F†–ær(	BæBöæRFö7VÖVçB&wVW2&÷F‚v—2À§ÂbÂF†Rg&öröæBÂÆ¶RbÆ6ÆÆRÂ&W6VçB†–æfW'&VB’ÂæWw7W"ÂöæR–V"ÆFRFòF†RF’À§ÂrÂF†RvVÆÇ27G&VWBÖ'6‚Â&W6VçB†–æfW'&VB’ÂF†R6VçFVæ6RF†Bv—fW2F†R6Æ÷Vv‚v—fW2v†B—BG&–ç2À ¢¢¥F†R6†'W7BF†–ær–â—B—2æ÷BF†RöæC¢F†R66VæRG&w2%$”DtR÷fW"vFW&6÷W'6RF†P§66VæRFöW2æ÷B6öçF–ââ¢¢6Æ÷Vv…öÆöuö'&–FvV—26öÖÖ—GFVB7G'V7GW&R7FæF–æröâƒ3RÓrÓæ@§F†R6÷W&6R'Vç2F†B7&÷76–ær¢'VçF–ÂgFW"ƒC"¢Â6òf—6—F÷"vÆ·2öçFòF–Ö&W"7&÷76–ærÆ–@¦÷fW"÷Vâ&—&–RâF†B—2æ÷Bâ&wVÖVçBf÷"7WGF–ær6öæ¦V7GW&Â6†ææVÂ(	BFWF‚æBv–GF‚&P§7F–ÆÂVç6÷W&6VBæB&6VÂ†2’7F–ÆÂ÷vç2F†VÒ(	B—B—2F†R&ööbF†BF†Rf÷W"vW&RæWfW"öâöæP¦fö÷F–ærÂv†–6‚öæR6†&VB‡&6R–×Æ–VBF†W’vW&Rà ¢¢¥6–æ6RÂ##bÓ‚Ó#B…BÓ’’â¢¢¦öæRB6ÖRöfbF†RFVfW'&ÂÆ—7C¢¢¥BÓR¢¢6'fVB—Böà£##bÓ‚Ó#æB¢¥BÓ‚¢¢&â—G2Æ7B&V6‚7V&RVæFW"F†R7&÷76–ærF†R6ÖRF’ÂBF†P§&V6öç7G'V7FVBF–W"v—F‚FWF‚æBv–GF‚FV6Æ&VB–çfVçFVB–â¢¤ÃC’¢¢â6òF†R'&–FvR÷fW"æ÷F†–ær—0¦vöæRÂæBF†R&VF–ær—2æ÷rF¶Vâ&F†W"F†â&wVVB(	BFööÇ2öÖV7W&U÷6Æ÷Vv…ö7&÷76–ærç–ÂöâF†P¦6öÖÖ—GFVB†V–v‡Ff–VÆC¢¢£2ã3Òöb÷VâvFW"–ââ‚ãÒ7âÂãS2ÒFVWÂ"ã3RÒöbG'’'WFÖVç@§6VBBV6‚VæBÂF†R&V6‚FòF†R&—fW"Væ'&ö¶VâÂæ÷F†–ærVÇ6R&ö÷FVB–âF†R7WBâ¢¢F†R÷F†W"F‡&VP§¦öæW27FæBW†7FÇ’2F†—2&÷‚ÆVgBF†VÒÂæBF†R6÷'&W7öæFVæ6RvFR&÷fR7F–ÆÂ†öÆG2F†VÓ¢RÀ£bæBr&VÖ–âFVfW'&VBæBFFVBÂæB¦öæRBæòÆöævW"V'2–âF†RFF–ær&V6÷&B&V6W6RF†P§7V2æòÆöævW"FVfW'2—Bà ¢¢¤öâF†RöæB—G6VÆbF†Rç7vW"—2æ÷EöW7F&Æ—6†VFÂæBFVÆ–&W&FVÇ’æ÷B&—Bv2æ÷BF†W&R"â¢ ¤öæRFö7VÖVçBÂ6†–6vöÆöw•÷&Vf—&S#s6Â6'&–W2&÷F‚6–FW2âdõ#¢—G26Æ÷Vv‚6VçFVæ6R†2F†R7G&VÐ¦G&–æ–ær¢'F†RöæBæBF†RÖ'6‚W‡FVæF–ærWvVÆÇ27G&VWB"¢2Æ—fRfVGW&RöbG&–ævP§7—7FVÒv†÷6R'&–FvR÷WFÆ—fW2F†R66VæR'’f—fR–V'2ât”å5BÂæBF†RFVfW'&ÂvV–v†VBæöæRö`§F†W6RF‡&VR(	BF†RV÷FF–öâFFW2æ÷F†–ær‚¢'v2F†Vâ"¢Â7BFVç6Rv–ç7Bâ¢£ƒSr¢¢&W6VçBÂ–à¦Fö7VÖVçBF†—2&ö¦V7Bw2÷vâ6÷W&6R&V6÷&B–FVçF–f–W22'V–ÇBöâ¢¤‡V&&&Bw26†–6vòöbƒ‚¢ ¦æB¢¤Ff—2w2ƒ3"¢¢G&v–ær“²F†RF÷76–W"w2÷vâ&÷r6ÆÇ2F†RöæB¢§6V6öæÂ¢¢v—F‚vFW ¢¢#ã^(	3"gBFVW–â7&–ær"¢v–ç7B66VæRFFVB¢£§VÇ’¢£²æBF†—2&ö¦V7BÇ&VG’7FæG2F†P¢¢¦W7G&’Vâ¢¢öâF†R7V&Rw26÷WF‚×vW7B6÷&æW"g&öÒ¢¤Ö&6‚ƒ3"¢¢æBF†R¢¦Æör¦–Â¢¢öâ—G0¦æ÷'F‚×vW7B6÷&æW"g&öÒF†R¢¦fÆÂöbƒ32¢¢â÷VæB—2æ÷B'V–ÇB–âöæBà ¢¢¥F†R'V–ÆF–æw2Fòæ÷B&VgWFRöæB(	BF†W’$õTäBöæRÂæBF†B—2v‡’F†RFFRæBF†RW‡FVçB&P¦öæRVW7F–öââ¢¢v†öÆRÖ&Æö6²öæB—2&VgW6VB'’F†—2&ö¦V7Bw2÷vâ6öÖÖ—GFVB&V6÷&G3²'F–À¦öæR—2VçF÷V6†VB'’F†VÒæB—2W†7FÇ’BÔSRw2F†—&BVW7F–öâÂv†–6‚æò6÷W&6R&V6†VB6âç7vW"à¥6òF†R‡&6Rw26V6öæB†Æbv2æWfW"FWF–ÂFòf–ÆÂ–âÆFW#¢F†R6öæ¦V7GW&ÂvVöÖWG'’—2F†P§F†–ærF†BFV6–FW2v†WF†W"vFW"7FæG2VæFW"6†–6vòw2f—'7BV&Æ–2'V–ÆF–ærà ¢¢¥BÔSRw2fÆÆ&6²—2F—66†&vVBæBäòÄ”$U%E’•2õtTBâ¢¢—G2–ç7G'V7F–öâv2¢&–b—B6ææ÷B&P¦ÖFR†öæW7FÇ’ÂF†R†öæW7Bç7vW"—2Fö72ôÄ”$U%D”U2æÖFVçG'’6––ærF†R7V&R—2G&vâG'’æ@§v‡’â"¢æ÷F†–ærv2–çfVçFVBÂæò6öæf–FVæ6RÖ÷fVBWÂæBF†R7V&Rv2¢¦Ç&VG’¢¢G&vâG'’æ@¦Ç&VG’&V6÷&FVB27V6‚–âFW‡Bf—6—F÷"6â&VBâv†Bv2Ö—76–ærv2F†R&V6öâÂæBF†P§&V6öâ—2æ÷r–âF†B6ÖRf—6—F÷"Öf6–ærFW‡B(	BF†Rf÷W"v‡–7G&–æw2w&÷VæBæ§6&VæFW'2â&÷6P¦–âF†R7V2—27G&—VBg&öÒF†RFW'&–âw27FÆVæW72†6‚Â6ò—B6÷7Bæò&¶Rà ¢¢¤æB—B6÷7B6öÖWF†–ærF÷vç7G&VÒæö&öG’v÷VÆB†fRvöæRÆöö¶–ærf÷"â¢ ¦FFöfVæ÷¦öæW2öcEöÖ'6‚æ§6öæ&W7FVB¢§F‡&VR6Æ–×2¢¢öâF†RöæBV÷FF–öâ2–â×66VæP¦Wf–FVæ6RÂöæRöbF†VÒ6––ær6ò–â2Öç’v÷&G2(	B×W6·&B&W6Væ6VæBÖÆÆ&B&W6Væ6VvW&P¦GFW7FVFöâ¢§F†BV÷FF–öâÆöæR¢¢Âæ÷FVB2¢&F—&V7BWf–FVæ6Röbæ–ÖÇ2&W6VçB–âçVÖ&W'2@¦æÖVBÆö6F–öâ–ç6–FRF†R66VæR&÷‚"¢â¢¤æòw&FRÖ÷fVB¢¢ÂæBF†B—2ÖV7W&VB&F†W"F†à¦6öçfVæ–VçC¢v†B6'&–W2GFW7FVF—2æG&V2w2¢&GV6·2æB×W6·&G2–âF†RÖ'6†W2"¢ÂæBF†P¦Ö'6†W2†RæÖW2¢¦&R¢¢F†R†&—FBF†—2¦öæRÆçG2(	B£EöÖ'6†w2W‡FVçB—2'VffW"öbF†P¦ÖVBvFW"ÂF†R&—fW"×6†÷&R7G&—ÂæB†2æWfW"&V6†VBF†R7V&RâF†Ræ–ÖÂ—2GFW7FVB–à§F†R†&—FBF†R66VæRG&w2æB—2æòÆöævW"GFW7FVBBæÖVB&Æö6²F†R66VæRG&w2G'’Âæ@§F†Ræ÷FW2æ÷r6’v†–6‚öbF†RGvòF†W’ÖVâà ¢¢¥6†—VC¢¢¢FF÷FW'&–âóƒ3Uö–çF÷vå÷vFW%öFF–æræ§6öæ†WF†÷&VBÂæò6ö÷&F–æFW2ÂæòvVöÖWG'’“°¦FööÇ2öÖV7W&Uö–çF÷vå÷vFW"ç–²FööÇ2ö6†V6²ç6†7FW†öÆF–ærF†R6÷'&W7öæFVæ6R¢¦–â&÷F€¦F—&V7F–öç2¢¢Â6òf–gF‚fVGW&R6ææ÷B&RFVfW'&VBVæFFVBæBFF–ærVçG'’6ææ÷B÷WFÆ—fRF†P¦FVfW'&Â—Bw&FW3²F†Rf÷W"f—6—F÷"Öf6–ærv‡–7G&–æw3²F†RF‡&VRfVæ6÷'&V7F–öç3°¦Fö72õ$U4T$4‚÷V&Æ–5÷7V&U÷öæBæÖFâ¢¥F†RvFRv2fW&–f–VBFòf–Â¢¢öâf÷W"6W&FP¦–æ¦V7F–öç2(	BâVæFFVBFVfW'&ÂÂâ–æfW'&VFw&FRv—F‚—G2&V6öæ–ær&Ææ¶VBÂ¦öæRçVÖ&W ¦æ÷F†–ærFVfW'2ÂæB6÷W&6RF†BFöW2æ÷B&W6öÇfR(	BæBFò72&W7F÷&VBâ6†V6²F†B†2æWfW ¦f–ÆVB—2æ÷B6†V6²à ¢¢¥v†B—BF–BäõBFó¢¢¢—BÖöFVÆÆVBÂÖ÷fVBæB6—¦VBæ÷F†–ærâÆÂf÷W"fVGW&W2&VÖ–âFVfW'&VBFð§&6VÂ†2’ÂæBæò&W6V&6‚F÷76–W"v2VF—FVB(	BF†÷6R&R6öÖÖ—GFVBfW&&F–ÒÂv†–6‚—2v‡’F†P¦F—6w&VVÖVçBÆ—fW2–âFö72õ$U4T$4‚öà ¢222BÔSR†"’(	B†÷r×V6‚öbF†R7V&Rv2vWB+r¢¤DôäR##bÓ‚Ó#B2BÓ#r+räò$´RäTTDTBÂæBF†B—2f–æF–ær¢  ¢¢¤•B$TeUDTB•E2õtâTU5D”ôâÂäBD„R$TeUDD”ôâ•2$UEDU"D„âD„RåTÔ$U"tõTÄB„dR$TTââ¢ ¦FööÇ2öÖV7W&U÷V&Æ–5÷7V&Rç–†æWrÂæBv—&VB–çFò6†V6²ç6†’6×ÆW2F†R6öÖÖ—GFVBÆGFV@¦&Æö6²BãRÒ(	B¢£C2ÃƒƒR6×ÆW2÷fW"Ã“sbÜ+"¢¢(	BæB&VG3  §ÂÂÀ§ÂÒÒ×ÂÒÒ×À§Âw&÷VæBÂ¢¢³"ãƒBFò³"ã“bgB¢¢&÷fRF†R7VÖÖW"Óƒ3RvFW"7W&f6RÀ§Â&VÆ–Vb7&÷72F†Rv†öÆR&Æö6²Â¢£ãC’–â¢¢À§Â¢§vWBg&7F–öâ¢¢Â¢£ãR¢¢(	BöbC2ÃƒƒR6×ÆW2B÷"&VÆ÷rF†RvFW"À§ÂF†RF÷76–W"w2÷vâ&VB‡&÷rR’Â³ãFò³"ãgBÂv†–6‚F†Rw&÷VæB7FæG2¢£ãƒBFòã“bgB&÷fR¢¢À§ÂF†R7V&Rw2G&–âÂ7FFU÷6Æ÷Vv…ö6÷W'6VÂ†VG2¢£3BãBÒ¢¢öfbF†R&Æö6²w2V7B¶W&"Â÷WG6–FR—BÀ ¢¢¥F†R¦W&ò—2&VF–æröbF†RÔôDTÂÂæBF†R6V6öæB&÷r—2v†B6—26òâ¢¢â–æ6‚æB†Æbö`§&VÆ–Vb7&÷726—G’&Æö6²—2–ç6–FRF†R7V2w2÷vâFV6Æ&VBÖ–7&ò×&VÆ–Vb(	B+ãgBöbfÇVRæö—6P§F†BÖ–7&õ÷&VÆ–Vbææ÷FV6ÆÇ2¢&FW‡GW&RÂæ÷B6Æ–Ò"¢(	B6òF†R7V&R6'&–W2æòÆæFf÷&Ò@¦ÆÂÂæB&VF–ærvWBg&7F–öâöfb—Bv÷VÆB&R&VF–ærF†Ræö—6R6VVBâF†B—2v‡’F†RFööÂ76W'G0§F†R&VÆ–Vb&W6–FRF†RvFW#¢76W'F–öâ—27FFVÖVçB&÷WBF†RÖöFVÂöæÇ’f÷"2Æöær0¦76W'F–öâ"†öÆG2à ¢¢¥6òF†Rç7vW"Fò&†÷r×V6‚"—2DUD‚ÂæB—B—2F†RVW7F–öâF†—2&÷‚F–Bæ÷B6²â¢¢F†Röæ@§F†RF÷76–W"FW67&–&W26ææ÷B&RÆ–BöâF†—2&Æö6³²—B†2Fò&R¢¦GVr¢¢ÂöæRFòGvòfVWBFVW÷fW £Ã“sbÜ+"Â÷WBöbF†RöæRÆæBVÆWfF–öâ–âF†—2&÷‚F†B&W7G2öâFö7VÖVçF'’6VçFVæ6R‚¢&ÆWfVÀ§Æ–âVÆWfFVBöæÇ’GvòFòF‡&VRfVWB&÷fRF†R&—fW""¢’ÂVæFW"F†R&Æö6²6''––ær6†–6vòw2f—'7@§V&Æ–2'V–ÆF–ærÂöâæò6÷W&6RF†B7FFW2FWF‚âvVöÖWG'’6öæ¦V7GW&Æv26''––ærF†Bâ¢¥F†P¦W‡FVçBv2æWfW"F†Rv†öÆRVW7F–öâæBF†RFFRv2æWfW"F†R÷F†W"†Æböb—B¢¢(	BF†W&R—2F†—&@§VW7F–öâVæFW&æVF‚&÷F‚ÂæB—B—2F†RW‡Vç6—fRöæRà ¢¢¥v†Bv27GVÆÇ’w&öærv2F†R5t$BÂæBæò&¶Rv2æVVFVBFòf—‚—Bâ¢ ¦Fö72÷&W6V&6‚ó"ÖfÆ÷&æÖF†VG2—G2¤ôäR2¢%4ÄõTt‚b4TDtRÔTDõr‚¢¥V&Æ–27V&R¢¢(i"G&VÖöç@¤†÷W6R6—FR(i"&—fW"B7FFR7B’"¢æB—G2*rã"6ÆÇ2F†B6Æ÷Vv‚F†R6–ævÆRÖ÷7B–×÷'Fç@§fVvWFF–öâfVGW&R”å4”DRF†RÆGFVBw&–Bâ£5÷6VFvUöÖVF÷vw2W‡FVçB—2â¢¦VÆWfF–öâ&æB¢¢ö`¢³ãbFò³"ã"gBÂv†–6‚6÷VÆBæWfW"&V6‚&Æö6²F†RFW'&–âG&w2B³"ã’gB(	B¦&V6W6R¦öæRR—0¦FVfW'&VB¢â6òF†RöæR&Æö6²F‡&VR6÷W&6W2FW67&–&R2vFW"v2ÆçFVB'’F†R6ÖR'VÆR0¦æöç–Ö÷W2&—&–RƒÒvW7BÂæBF†RöæBV÷FF–öâ&V6†VBF†RfÆ÷&Æ–W"æ÷v†W&RâF†—2—2F†P¦Ö—'&÷"öbv†BBÔSR†’f÷VæB–âF†RfVæ¢£EöÖ'6†—2'VffW"öbF†RÖVBvFW"æB&†0¦æWfW"&V6†VBF†R7V&R"V—F†W"à ¢¢¥6†—VC¢¢¢–æ6ÇVFU÷öÇ–vöç6öâF†RfÆ÷&W‡FVçBÖF6†W"†&VæFW&W'2÷vV"ö§2öfÆ÷&æ§6ÂÖ—'&÷&V@¦–âFööÇ2÷fÆ–FFRç–æB&Vv—7FW&VB–âFööÇ2öÖV7W&UöÆ–W%÷&VG2ç–’(	BF†RW†7BÖ—'&÷"ö`¦W†6ÇVFU÷öÇ–vöç6Âf÷"6öÖ×Væ—G’v†÷6RWf–FVæ6R—2Ä4RæBv†÷6R'VÆR—2„T”t…C²F†P§7V&Rw2&–æröâ£5÷6VFvUöÖVF÷vÂF¶VâfW'FW‚f÷"fW'FW‚g&öÒF†R6öÖÖ—GFVBÆBæB†VÆBF†W&P¦'’F†RvFRÂ6ò¢¦æ÷F†–ær—2f—GFVB¢¢(	B–â'F–7VÆ"æ÷F†–ær6†VB&÷VæBF†RW7G&’VâÂF†RÆöp¦¦–ÂæBF†R6÷W'BÖ†÷W6RÂv†–6‚7FæBôâF†R7v&C²Fö72ôÄ”$U%D”U2æÖF¢¤Ãƒ‚¢¢f÷"F†RöæP¦–çfVçF–öâÂF†BF†RvWBw&÷VæB7F÷VBBF†R7W'fW–÷"w2Æ–æS²F†R6÷'&V7F–öâö`¦ƒ3U÷&W6W'fVEöw&÷VæBæ§6öæw2æ÷rÖfÇ6R¢'F†R7V&R&VæFW'22G'’&—&–R"£²æ@¦Fö72õ$U4T$4‚÷V&Æ–5÷7V&U÷öæBæÖF*rbà ¢¢¥v†B—BF–BäõBFòâ¢¢—BÖ÷fVBæòw&÷VæBÂ7WBæò&6–âÂFFVBæòvFW"æB&öÖ÷FVBæò6öæf–FVæ6Rà¥¦öæRR—27F–ÆÂFVfW'&VBÂ7F–ÆÂæ÷EöW7F&Æ—6†VFÂæB7F–ÆÂæVVG2&¶RæB6÷W&6R&Vf÷&R—B6à¦&Rç—F†–ærVÇ6Râ¢¤—G2fÆÆ&6²7FæG2F—66†&vVC¢¢¢F†RÆ–&W'G’F†—2&÷‚6¶VBf÷"—2w&—GFVâÂæ@¦—BFÖ—G2&÷VæF'’&F†W"F†âöæBà £ÆFWF–Ç3à£Ç7VÖÖ'“ãÆ#åF†R'&–Vb2BÔSR†’÷VæVB—BÂ##bÓ‚ÓcÂö#ãÂ÷7VÖÖ'“à ¥v†B†’FVÆ–&W&FVÇ’F–Bæ÷Bç7vW"â—G2f—'7BVW7F–öâ—2æ÷B†÷rFòÖöFVÂâW‡FVçB'W@¢¢§v†WF†W"ç’6÷W&6R7FFW2öæRBÆÂ¢¢(	B†’f÷VæBæöæRÂæBF†RGvò6÷&æW'2F†—2&ö¦V7B†0¦Ç&VG’'V–ÇBöâ&RF†RöæÇ’†&B6öç7G&–çBç—v†W&R–âF†RWf–FVæ6Râ&V@¦Fö72õ$U4T$4‚÷V&Æ–5÷7V&U÷öæBæÖF*r2&Vf÷&RF÷V6†–ær—C¢'F–ÂöæBf—GFVBFò6ÆV"F†P¦'V–ÆF–æw2—2çVÖ&W"6†÷6VâFòÆöö²&–v‡BÂv†–6‚—2F†Rf–ÇW&RÖöFR"ÔÓ"—2&¶VBöâæBF†P¦öæRF†—2&ö¦V7B†2&VVâ†æFVBGv–6Râ–bF†R†öæW7Bç7vW"—2F†BæòW‡FVçB—2&V6÷fW&&ÆRÀ§F†B—2f–æF–æræB—B&VÆöæw2–âFö72ôÄ”$U%D”U2æÖF(	B'WB†’—2æ÷B—BÂ&V6W6R†’–çfVçFV@¦æ÷F†–ærâw&÷VæBvVöÖWG'’ÖVç2&¶RV—F†W"v’à £ÂöFWF–Ç3à £ÆFWF–Ç3à£Ç7VÖÖ'“ãÆ#åF†R÷&–v–æÂBÔSR'&–VbÂ2÷VæVB'’BÔböâ##bÓ‚ÓSÂö#ãÂ÷7VÖÖ'“à ¦FFöfVæ÷¦öæW2öcEöÖ'6‚æ§6öæ6'&–W2F†Rf–æF–ær–â—G2÷vâæ÷FS¢¢%F†RV&Æ–27V&R(	@¥&æFöÇ‚Fòv6†–æwFöâÂ6Æ&²FòÆ6ÆÆR(	Bwv2F†VâöæBÂv†W&RF†R–æF–ç2†BG&VBF†P¦×W6·&BÂæBv†W&RF†Rf—'7B6WGFÆW'2‡VçFVBGV6·2r"¢Âg&öÒ6†–6vöÆöw•÷&Vf—&S#s6B'Vær"Âæ@¦Fö72÷&W6V&6‚ó‚ÖfVææÖFÆ–æRCBæBFö72÷&W6V&6‚ó"ÖfÆ÷&æÖFÆ–æRC6''’F†R6ÖRvFW"æ@§F†R6Æ÷Vv‚G&–æ–ær—B7BF†RG&VÖöçB†÷W6R6—FRFòF†R&—fW"BF†Rfö÷Böb7FFR7G&VWBâF†P§FW'&–â6'&–W2æöæRöb—C¢F†W&R—2æò7FæF–ærvFW"öâF†—2&Æö6²–âç’6öÖÖ—GFVBWö6‚ÂF†P¦Ö'6‚fÆ÷&¦öæRw2W‡FVçB—2¢¦'VffW"öbF†RÖVBvFW"¢¢6ò—BÆçG2æ÷F†–ær†W&RÂæBF†P§7V&RF†W&Vf÷&R&VæFW'22G'’&—&–Rv—F‚÷VæBÂ¦–ÂæB6÷W'BÖ†÷W6R7FæF–æröâ—Bà ¢¢¥F‡&VRF†–æw2Fò6WGFÆR&Vf÷&Rç’w&÷VæBÖ÷fW2¢¢ÂæBF†RF†—&B—2F†RöæRF†Bv–ÆÂ&—FRà £â¢¤†÷r×V6‚öbF†R&Æö6²ÂæBv†Vââ¢¢F†RV÷FF–öâ—2&V6öÆÆV7F–öâV&Æ—6†VB–âƒSröb¢W&–öBF†Rw&—FW"FFW2Æö÷6VÇ“²¢'v2F†Vâ"¢—2æ÷B§VÇ’ƒ3RâFFöW†6ÇW6–öç2æ§6öæ—2F†P¢Æ6Rf÷"&W6V&6†VBÖæBÖW†6ÇVFVB&VF–ær–bF†RöæBGW&ç2÷WBFò&VFFRF†R66VæRFFR(	@¢F†RW7G&’VâvVçBWöâF†—2&Æö6²–âÖ&6‚ƒ32æB÷VæB—2æ÷B'V–ÇB–âöæBà£"â¢¥F†R6Æ÷Vv‚—2F†R6ÖRfVGW&RæB—2Ç&VG’†Æb×&V6÷&FVB¢¢(	BFö72÷&W6V&6‚ó×FW'&–âÐ¢‡–G&öÆöw’æÖF&÷rBv—fW2—G2&÷WFRFö7VÖVçFVBæB—G2FWF‚æBv–GF‚6öæ¦V7GW&Ââv†FWfW ¢ÆæG2†W&R6†÷VÆBÆæBv—F‚—B&F†W"F†âÖöFVÆÆ–æröæBF†BG&–ç2æ÷v†W&Rà£2â¢¥F‡&VR6öÖÖ—GFVB7G'V7GW&W27FæBöâF†—2&Æö6²¢¢ÂGvòöbF†VÒöâ6÷&æW'2æG&V2v—fW2âvFW ¢VæFW"Fö7VÖVçFVB'V–ÆF–ær—2v÷'6RW'&÷"F†âæòvFW"BÆÂÂ6òF†RFVÆ—fW&&ÆR—0¢&ö&&Ç’vWB¢§'B¢¢öbF†R7V&Rv—F‚F†RF‡&VRV&Æ–2'V–ÆF–æw26ÆV"öb—B(	Bv†–6‚—2¢6Æ–Ò&÷WBW‡FVçBF†Bæò6÷W&6R&V6†VB7W÷'G2â–b—B6ææ÷B&RÖFR†öæW7FÇ’ÂF†R†öæW7@¢ç7vW"—2Fö72ôÄ”$U%D”U2æÖFVçG'’6––ærF†R7V&R—2G&vâG'’æBv‡’à ¢¢¤æ÷BW&vVçBÂæBæ÷B&Æö6¶W"f÷"ç—F†–ær¢¢(	Bæò&ööb—266†VGVÆVB†W&Ræ÷rF†BBÔb†0§&W6W'fVBF†R&Æö6²à £ÂöFWF–Ç3à ¢22'Vw2f÷VæBæBæ÷B–WBf—†V@ ¢222"Ô%Ts(	BF†Ræ–v‡FÇ’&¶RF–VBBF†Rf–æ—6‚Æ–æR+r¢¤d•„TB##bÓ‚ÓB¢  ¥&V6÷&FVB&V6W6RF†R6†Röb—Bv–ÆÂ&V7W"Âæ÷B&V6W6R—B—27F–ÆÂ÷Vâà ¥F†RV&Æ—6†VBÖÖ—'&÷"6Öö¶Rv2FFVBFòF†RVæBöbFööÇ2ö&¶Rç6†öâ##bÓ‚Ó2#£UD0¢†6öÖÖ—BscCV&Sf’ÂæB—Bv2F†R&–v‡BF†–ærFòFC¢F†R6÷W&6RG&VRæBF†RV&Æ—6†V@§G&VRFòæ÷BÆöBF†R6ÖRvVöÖWG'’ÂæB'VrF†BfÆGFVæVBWfW'’'V–ÆF–ærFòGvòÖÖWG&P¦&÷‚†BÇ&VG’6†—VB7Bw&VVâvFRGv–6R&V6W6Ræ÷F†–ær†BWfW"ÆöFVBF†P¦6ö×&W76VBFW&—fF—fW2à ¦6†–6vòÓFBÖ&¶Rç–ÖÆFöW2æ÷B–ç7FÆÂÆ—w&–v‡Bâ6òg&öÒF†B6öÖÖ—Böçv&BF†Ræ–v‡FÇ¦F–BÆÂöb—B(	BfWF6†VB&ÆVæFW"ÂvVæW&FVBÂ&¶VBòÂ6ö×&W76VBÂV&Æ—6†VBÂvFVB¢¦w&VVâ¢ ®(	BæBF†VâF–VBöâ6ææ÷Bf–æBÖöGVÆR(
b÷Æ—w&–v‡Bö–æFW‚æ§6ÂöæR7FW6†÷'BöbF†R7FW §F†BW6†W2F†R&¶R'&æ6‚æB÷Vç2F†R"âWfW'’æ–v‡Bw2÷WGWBv2F—66&FVBâ'Vç0¦3scƒCvƒ£C•¢’æB3ss“3CfƒC£S%¢’&÷F‚&VB2f–ÆVB6öçFVçB'V–ÆBv—F€¦æò6ÇVR–âF†R7VÖÖ'’F†BWfW'—F†–æröb7V'7Fæ6R†B7V66VVFVBà ¢¢¤f—†VB¢¢'’–ç7FÆÆ–ærÆ—w&–v‡DãSbãvÆö&ÆÇ’ÇW2F†RÖF6†–ær6‡&öÖ—VÒ–âF†R&¶P§v÷&¶fÆ÷râæ÷F†–ærv26¶—VBæBæò76W'F–öâv2vV¶VæVB(	B4´•õ4Ôô´SÓW†—7G2æBv0¦FVÆ–&W&FVÇ’æ÷BW6VBÂ&V6W6Ræ–v‡FÇ’F†BV&Æ—6†W2v—F†÷WBÆöF–ærv†B—BV&Æ—6†VB—0§F†RW†7B†öÆRF†—26Öö¶Rv2FFVBFò6Æ÷6Rà ¢¢¥F†RvVæW&ÂÆW76öâÂf÷"v†öWfW"FG2F†RæW‡BvFS¢¢¢&¶Rç6†'Vç2–âGvòÆ6W2v—F€¦F–ffW&VçBFööÆ6†–ç2(	BFWb6öçF–æW"F†B†2Æ—w&–v‡BæB'VææW"F†BFöW2æ÷B(	Bæ@¦7FWFFVBFòF†R67&—B—2öæÇ’&VÆÇ’FFVBöæ6RF†R'VææW"6âW†V7WFR—Bâ6†V6²F†P§v÷&¶fÆ÷r–âF†R6ÖR6öÖÖ—B2F†R67&—Bà ¢222"Ô%Ts"(	B–ç7FÆÆ–ær·G†GW&æVBöâFW‡GW&W2F†R&VæFW&W"6ææ÷B&VB+r¢¤d•„TB##bÓ‚ÓB¢  ¥F†R–ÖÖVF–FR6WVVÂFò"Ô%TsÂæBF†R&V6öâF†Bf—‚v2v÷'F‚Ö¶–æs¢F†RÖöÖVçBF†P¦&¶R6÷VÆB'Vâ—G26Öö¶Rv–âÂF†R6Öö¶Rf÷VæB6öÖWF†–ærà ¦FööÇ2ö&¶Rç6†6¶VBf÷"Ò×FW‡GW&RÖ6ö×&W72·Gƒ&v†VæWfW"·G†&–æ'’v2öâD‚âF†@¦—2F†Rw&öær&V6öæF—F–öââv†WF†W"F†RDôôÂ6âw&—FRµEƒ"6—2æ÷F†–ær&÷WBv†WF†W"F†P¥$TäDU$U"6â&VB—B(	BæB—B6ææ÷BâF†RfVæF÷&VBtÅDdÆöFW&†æFÆW2´…%÷FW‡GW&Uö&6—7V ¦öæÇ’gFW"6WDµEƒ$ÆöFW"‚–—26ÆÆVBÂæ÷F†–ær6ÆÇ2—BÂæBæò&6—2G&ç66öFW"—2fVæF÷&V@¢†—Bv÷VÆB†fRFò&S¢&VæFW&W'2÷vV"öF¶W2æò4Dâ’à ¥6òv†VâF†RµE‚Õ6ögGv&R–ç7FÆÂÆæFVBöâF†R'VææW"ÂF‡&VRFW&—fF—fW26ÖR&6²v—F‚µEƒ §FW‡GW&W2(	B&Æ6·6Ö—F…÷6†÷÷7FFU÷7EõöÆöuóƒ#6Â'&÷våö&ö&F–æuö†÷W6UõöFö7VÖVçFVEóƒ3VÀ¦&VV&–Våö&&åõö6öçfW'FVEóƒv(	BæBV6‚F‡&WrD…$TRätÅDdÆöFW#¢6WDµEƒ$ÆöFW"×W7B&P¦6ÆÆVB&Vf÷&RÆöF–ærµEƒ"FW‡GW&W6à ¢¢¤ÆÂVÆWfVâf–ÇW&W2–â&¶R'Vâ3ss3#cs†&RF†BöæR6W6Râ¢¢â76WBF†BF‡&÷w2–à§F†RÆöFW"—2â76WBF†B—2æ÷B–âF†R66VæRÂ6òF†R6÷VçBwV&BöâF†Rw&÷VæBÖ6öçF7@¦6†V6²†ââ#’6r“‚æBG&—VBÂæBF†R&–67BÂ6Æ–6²×FòÖ–ç7V7BæB–ç7V7BÖg&öÒ×F†RÖ— ¦6†V6·2†BÆW72F÷vâFò†—Bâæ÷F†–ærfÆöFVB(	BF†Rv÷'7B6÷&æW"v2ãsrÒÂvVÆÂ–ç6–FRF†P£ãRÒFöÆW&æ6Râ&VF–ærF†Rf–ÇW&RÆ—7B2VÆWfVâ&ö&ÆV×2v÷VÆB†fR6VçB6öÖVöæRÆöæp§v’–âF†Rw&öærF—&V7F–öâà ¢¢¤æöæRöb—BÆVgBF†R'VææW"â¢¢F†R&¶Rf–Ç2&Vf÷&R—G2W6‚7FWÂ6òæò'&æ6‚Âæò"Âæ@§&öGV7F–öâv2æWfW"F÷V6†VC¢F†RV&Æ—6†VBÖ—'&÷"26†—VB6'&–W2¦W&òµEƒ"FW‡GW&W2æ@§'Vç2C276VBÂf–ÆVFà ¢¢¤f—†VB¢¢'’vF–ærF†RfÆröââW‡Æ–6—B$´UôµEƒ#Ó–ç7FVBöböâF†R&–æ'’w2&W6Væ6Rà¥F†R·G†–ç7FÆÂ7F—2(	Bs"æVVG2—BæB—B6÷7G2æ÷F†–ær–FÆRà ¢¢¥GW&æ–ær—Böâ—2'Böbs"Â–âF†—2÷&FW#¢¢¢v—&RµEƒ$ÆöFW&ÇW2fVæF÷&VBG&ç66öFW ¦–çFòF†R&VæFW&W"Â&÷fR—BÆöG2FW‡GW&VB76WBB&÷F‚f–Ww÷'G2ÂæBöæÇ’F†Vâ6W@¦$´UôµEƒ#Óà ¢222"Ô%Ts2(	BF†R&Wf—fVB&¶Rf—&VBöâWfW'’ÖW&vRæB–ÆVBW'2+r¢¤d•„TB##bÓ‚ÓB¢  ¥F†RF†—&BæBÆ7B6öç6WVVæ6RöbF†R&¶RæWfW"†f–ærv÷&¶VC¢æö&öG’†BWfW"6VVâv†B—@¦FöW2v†Vâ—B§7V66VVG2¢–â&Wòv†÷6RÆö÷—2'Vææ–ærà ¦6†–6vòÓFBÖ&¶Rç–ÖÆG&–vvW&VBöâW6†W2F÷V6†–ær6†–6vòóFBöFFò¢¦ÂæB6'&–VBæð¦6öæ7W'&Væ7–w&÷W†&÷F‚FWÆ÷’ç–ÖÆæBF†R&öÖ÷F–öâ†fRöæR’âF†Bv26÷VæBv†VâFF¦6†ævVB&&VÇ’â—B—2æ÷B6÷VæBæ÷r(	BF†R7FWv&BÆö÷w2VçF—&R¦ö"F†—2vVV²—2FF–æp§7G'V7GW&W2Â6òæV&Ç’WfW'’ÖW&vR–çFòFWfF÷V6†W2FFò¢¦â&WGvVVâc£C"æB#£’F†P¦&¶R÷VæVB¢§6WfVâ¢¢'2(	B3rÂ3Â3Â32Â3BÂ3bÂ3r(	BV6‚gVÆÀ§&VvVæW&F–öâöbF†R6ÖR&–æ'’76WG2ÂV6‚ã#Ö–çWFW2öb&ÆVæFW"ÂÆÂ×WGVÆÇ’6öæfÆ–7F–ærÀ¦æBÆÂ'WBF†RæWvW7BÇ&VG’7FÆRv–ç7BFWfF†B†BÖ÷fVBöââGvò—'0¢†3sƒcsƒSC†ö3sƒcs“c#ƒ–Â3s“3“cSö3s“3“#c“–’vW&R&6–ær'Vç26V6öæG2'Bà ¥F†Rv÷&¶fÆ÷rw2÷vâ†VFW"6–B&æWfW"öâWfW'’6öÖÖ—B"âF†RG&–vvW"Æ—7BV–WFÇ’7F÷V@¦†öæ÷W&–ær—Böæ6RF†RÆö÷6†ævVBv†BG—–6Â6öÖÖ—BÆöö·2Æ–¶Rà ¢¢¤f—†VB¢¢'’G&÷–ærFFò¢¦g&öÒF†RW6‚G&–vvW"(	B6†ævRFòtTäU$Dõ"÷"Fð¦&¶Rç6†ÇFW'2†÷rWfW'—F†–ær—2'V–ÇBæBV&ç2â–ÖÖVF–FR&V&¶RÂv†–ÆRFF6†ævR—0¦W†7FÇ’v†BF†Ræ–v‡FÇ’—2f÷"(	BæB'’FF–ær6öæ7W'&Væ7“¢²w&÷W¢6†–6vòÓFBÖ&¶RÀ¦6æ6VÂÖ–â×&öw&W73¢G'VRÖâ7WW'6VFVB&¶R†2æ÷F†–ærFòöffW#¢—G2÷WGWB—2ÖV7W&V@¦v–ç7BFWfF†B†2Ç&VG’Ö÷fVBÂ6ò6æ6VÆÆ–ær—B—2F†R6÷'&V7B÷WF6öÖR&F†W"F†â¦Æ÷7B&W7VÇBà ¢¢¤ÆVgBf÷"F†R÷væW#¢¢¢F†R6WfVâ÷Vâ'2âF†W’†öÆB&VÂ&¶VBvVöÖWG'’æBöæÇ’F†RæWvW7@¢‚3rÂ&6VBöâF†R7W'&VçBFWf’—27W'&VçC²F†R&W7B&R7FÆRæB6öæfÆ–7Bv—F‚—Bâ6Æ÷6–æp§6—‚æBÖW&v–æröæR—2§VFvVÖVçB6ÆÂ&÷WB6öçFVçBÂæ÷Bv÷&¶fÆ÷rFVfV7BÂ6ò—B†2æ÷@¦&VVâÖFR†W&Rà ¢222"Ô%TsB(	Bæ÷'F‚vFW"7G&VWBw26öÖÖ—GFVB6VçG&VÆ–æR'Vç2–ç6–FRF†RvFW"Ö6²+r¢¤õTâÂBÓ##b¢  ¤f÷VæB##bÓ‚Ó#r'’BÓƒBw2¦ö–çB&ö&RÂv†–6‚—2F†R6†Rv÷'F‚¶VW–æs¢äUr–ç7G'VÖVçBw0¦f—'7B&VF–ærv2#RÓ"öb'Væ6÷fW&VB&öGv’"æBöb—Bv2æ÷BF†RfVÇBF†R–ç7G'VÖVç@§v2'V–ÇBFò6VRâF‡&VRöbæ÷'F‚vFW"7G&VWBw26—‚&VæG2(	B³33ÂceÒÂ³CS"ÂsUÒÂ³SsbÂƒeÒ(	@§6—Böâ6VçG&VÆ–æRF†RvFW"Ö6²6ÆÇ2&—fW"Â6ò7G&VWG2æ§6&VgW6W2WfW'’æVÂF†W&RVæFW ¥"Ô%TsBw2÷vâ'VÆR‚&6Æ—ÂFöâwB–çBf÷&B"’âvÆ¶VBB†ÆbÖÖWG&R7FW2Â¢£CsrãBÒöbF†@§7G&VWBw2ƒC2ã2Ò6VçG&VÆ–æR—2–ç6–FRF†RÖ6²Â–âöæRVæ'&ö¶Vâ'Vâg&öÒ³#ã"ÂSUÒFð¥³csRãBÂ“RãuÒ¢¢(	BSrRöbF†R7G&VWBÂæBæò&–&&öâ—2G&vâöâç’öb—BâF†R&ö&R&W÷'FV@¦V6‚öbF†RF‡&VR&VæG2232ã‚Ó"Væ6÷fW&VBÂv†–6‚v2G'VRæB—'&VÆWfçBà ¥Gvò&VF–æw2&R÷76–&ÆRæBF†—2'VâF–Bæ÷B6WGFÆRv†–6ƒ¢F†RG&6VBæ÷'F‚&æ²—2Föòf §6÷WF‚ÆöærF†B&V6‚Â÷"F†R7G&VWB&V6÷&Bw2Æ–æR—2Föòf"æ÷'F‚â&÷F‚&R&V6÷&FVB6Æ–×0§v—F‚6÷W&6W2Â6ò—B—2&W6V&6‚VW7F–öâ&F†W"F†âçVFvR(	Bf–ÆVB2¢¥BÓ##b¢¢v—F‚F†P¦W‡FVçBÖV7W&VBà ¢¢¥F†R–ç7G'VÖVçBv2f—†VB&F†W"F†âF†RçVÖ&W"W‡Æ–æVBv’â¢¢&öEö¦ö–çE÷&ö&RæÖ§6æ÷p¦FVf–æW2F†RæöÖ–æÂ&–&&öâ2w&÷VæBF†RÖöGVÆR—2ÄÄõtTBFò–çB(	Bv—F†–âF†R†Æb×v–GF‚öb¦6†÷&BF†B7W'f—fVBF†R6VçG&VÆ–æRvFW"FW7BæBF†R6Æ—fW"G&÷ÂæBæ÷B—G6VÆböâvFW"(	Bæ@¦6÷VçG2F†RvFW"×&VgW6VB&VæG2öâF†V—"÷vâÆ–æR6òF†W’6ææ÷B†–FR–âF÷FÂâç’¦ö–çBvFP¦'V–ÇBöâF†—2–ç7G'VÖVçB&VG2F†R¦ö–çG2æBöæÇ’F†R¦ö–çG2à ¢222"Õ$Tc(	B6öÖÖ—BF†R&VfW&Væ6R†÷Föw&‚+r¢¤DôäR##bÓ‚ÓR¢  ¦&"öGWvU÷FÆÆw&75ó#‚ÓrÓ#Bæ§v(	BF†RfW&–f–VB§VÇ’–ÆÆ–æö—2×&—&–R†÷Föw&‚F†—0§&ö¦V7B6Æ–'&FW2—G26·’v–ç7BæB&V6öç2&÷WBG&VRÖÖ726öçG&7Bg&öÒ(	B¢¦—2æ÷B–âF†P§&Wòâ¢¢6öæf—&ÖVB##bÓ‚ÓC¢v—BÇ2Öf–ÆW6&WGW&ç2æ÷F†–ærf÷"—Bà ¢¢¤—B—2æ÷r&Æö6¶–ærGvòF†–æw2Âæ÷BöæRâ¢¢"ÕsæÖVB—B¢'F†R6–ævÆRF†–ærÖ÷7B–âF†Rv’ö`¦§VFv–ærF†W6RçVÖ&W'2"¢(	B$TäDU$”är*sRw2æ÷FR6·2F†RF&vWG2Fò&R&RÖæ6†÷&VB'’ÖV7W&–æp¦&VfW&Væ6RF‡&÷Vv‚F†—26öFRÂæBF†B6ææ÷B&RFöæRv–ç7Bf–ÆRæö&öG’†2âæB¢¦"ÔÓ ¦&VÆ÷ræVVG2—B¢¢FòFW&—fR—G2F‡&W6†öÆG2g&öÒv†B&VÂF—'BG&6²†öÆG2v–ç7B&VÂ&—&–RÀ§&F†W"F†âg&öÒçVÖ&W'2–6¶VBFòf—BFöF’w2'V–ÆBà ¢¢¥F†Rv†öÆR&6VÂ—3¢W7F&Æ—6‚F†R&–v‡G2Â6öÖÖ—BF†Rf–ÆRÂ&Vv—7FW"—B26÷W&6Râ¢¢—B—2§†÷Föw&‚Æ–¶Rç’÷F†W"–çWB(	BFF÷6÷W&6W2óÆ–Câæ§6öæv—F‚—G2Æ–6Væ6RÂ&÷fVææ6RæB¦v†Eö—EöFöW5öæ÷E÷7WÇ–Æ—7BÂW†7FÇ’2WfW'’Ö–âF†—2FF6WB6'&–W2â–bF†R&–v‡G2Fð¦æ÷BW&Ö—B6öÖÖ—GF–ær—BÂ¢§6’6ò–âF†R6÷W&6R&V6÷&BæBæÖR7V'7F—GWFR¢¢F†BFöW3²à§Væ6—F&ÆR6Æ–'&F–öâ&VfW&Væ6R—26Æ–'&F–öâæö&öG’6â6†V6²à ¢¢¤f–ÆW3¢¢¢F†R–ÖvR+rFF÷6÷W&6W2óÆ–Câæ§6öæ+r76WG2ôÄ”4Tå4U2æÖF+rFö72õ$TäDU$”äræÖF ¢¢¤66WFæ6S¢¢¢FööÇ2ö6†V6²ç6†w&VVã²F†Rf–ÆR&W6öÇfW3²F†R&–v‡G2&R&V6÷&FVBÂæ÷B77VÖVBà ¢¢¤DôäR##bÓ‚ÓRâ¢¢F†Rf–ÆR—0¦FF÷6÷W&6W2ö76WG2÷6&•ó#…öGWvU÷FÆÆw&72öGWvU÷FÆÆw&75ó#‚ÓrÓ#Bæ§vÂ6÷W&6P§&V6÷&B6&•ó#…öGWvU÷FÆÆw&76ÂÆ–6Væ6R&÷r–â76WG2ôÄ”4Tå4U2æÖFÂæB&÷F‚"Õsæ@¥"ÔÓ&RVæ&Æö6¶VBâgVÆÂf–æF–æw2–âFö72õ5DEU2æÖF*r'F†R†÷Föw&‚F†R6·’—26Æ–'&FV@¦v–ç7B"âf÷W"F†–æw2F†RæW‡B&6VÂ6†÷VÆBF¶Rg&öÒ—B&F†W"F†â&VF—66÷fW#  ¢Ò¢¤—B—2F†R&–v‡B†÷Föw&‚æBF†RçVÖ&W'2&÷fR—Bâ¢¢—F†öã2FööÇ2öÖV7W&U÷&VfW&Væ6Rç– ¢†æWrÂ–ÆÆ÷rÖ÷F–öæÂÂFVÆ–&W&FVÇ’÷WG6–FR6†V6²ç6†’&W&öGV6W2ÆÂf÷W"6·’&VF–æw0¢v÷&ÆBæ§6V÷FW2Fòv—F†–âfWrVæ—G2Âv—F‚æ÷F†–ær–âF†R&VæFW&W"F÷V6†VBâ–FVçF–f–6F–öà¢æWfW"&W7FVBöâF†Rf–ÆVæÖS¢F†R6öÖÖöç2FW67&—F–öâ6'&–W2F†R6ÖP¢&W7F÷&F–öâÖæ÷B×&VÖæçBf–æF–ærF†R##bÓ‚Ó7vVWÖFR&÷WBF†—2†÷Föw&‚ÂæBF†P¢U„”b6—2#‚ÓrÓ#B“£3#£#Rà¢Ò¢¥F†Rg&ÖR—26öÇfVC¢VÆWfF–öâ‡&÷r’Òƒƒ#(‰"&÷r’òSrãFVw&VW2¢¢ÂBãL+&÷fRF†P¢†÷&—¦öâFò3‚ã|+&VÆ÷rÂ6ÖW&—F6‚(‰#"ã+(	Bv†–6‚—2F†Rã,+F÷vâ×F–ÇBF†R&—&–R7vVW ¢f÷VæB–æFWVæFVçFÇ’â¢¥V÷FRF†RVÆWfF–öâöbç’&VF–ærâ¢¢&÷F‚öbF†—2&ö¦V7Bw0¢&VfW&Væ6RF—6w&VVÖVçG2vW&RGvòV÷ÆRÖV7W&–ærF–ffW&VçB†V–v‡G2–âöæR†÷Föw&‚à¢Ò¢¥F†R&–v‡G2&R42%’Õ4BãæBF†W’&—FRâ¢¢fW&&F–Ò&VF—7G&–'WF–öâæBÖV7W&VÖVçB&P¢6ÆV&VC²¢¦ç’7&÷Â&W6×ÆRÂFW‡GW&R÷"ÅUB—2âFFF–öâ¢¢æBv÷VÆBWB6†&TÆ–¶P¢ö&Æ–vF–öâöâF†—2&W÷6—F÷'’â"ÔÓÖ’ÖV7W&R—Bg&VVÇ’(	B—B×W7Bæ÷B7WBF–ÆR÷WBöb—Bà¢Ò¢¥"ÔÓw2fÆÆ&6²—2æ÷BæVVFVBâ¢¢—Bv2w&—GFVâFòg&VW¦R&÷f—6–öæÂvV&W"f–wW&W2&–bF†P¢&–v‡G2f÷&&–B6öÖÖ—GF–ær—B"âF†W’Fòæ÷BâçäFW&—fRF†RF‡&W6†öÆG2g&öÒF†R†÷Föw&‚ççà¢Ò¢¤4õ%$T5DTB##bÓ‚ÓR'’"ÔÓ¢F†R†÷Föw&‚6ææ÷B7WÇ’"ÔÓw2F‡&W6†öÆG2ÂæBF†—0¢'VÆÆWBv2w&öærFò&öÖ—6R—B6÷VÆBâ¢¢—B6öçF–ç2æò&&RÖV'F‚7W&f6R(	Bv–FW7B6öçF–wV÷W0¢&&R'Vâ¢£‚ã"RöbF†Rg&ÖRv–GF‚ÂB(‰#3‚ã,+¢¢ÂBF†R†÷Föw&†W"w2fVWB(	B6òF†W&R—2æð¢F—'BG&6²–â—BFòÖV7W&R&öB6öçG&7Bv–ç7Bâ—F†öã2FööÇ2öÖV7W&U÷&VfW&Væ6Rç– ¢&–çG2F†R7W'fW’â¢¤æ÷F†–ærVÇ6RöâF†—2Æ—7B—2ffV7FVB¢£¢F†R6·’Â†÷&—¦öâæB6æ÷¢&VF–æw2"Õ$TcÆæFVBÆÂ7F–ÆÂ&W&öGV6RÂæBF†W’&Rv†Bv÷&ÆBæ§6æBG&VW2æ§6 ¢7GVÆÇ’V÷FRâ"Õ$TcVæ&Æö6¶VB"Õsw2F&vWB&RÖæ6†÷&–ærÂv†–6‚v2F†R÷F†W"†Æböbv†@¢—Bv2f÷"â6VR"ÔÓ"f÷"v†BF‡&W6†öÆB6÷W&6Rv÷VÆBæ÷r†fRFò&Rà ¢222"ÔÓ(	BF†RGvò66ÆW2ÂÖV7W&VBæBæ÷BvFVB+r¢¤DôäR##bÓ‚ÓR¢  ¢¢¥F†R&6VÂv27Æ—B&Vf÷&R—Bv26Æ–ÖVBÂVæFW"F†RÆæRw2÷vâ'VâÖ'VFvWB'VÆRâ¢¢"ÔÓw0¦66WFæ6RæÖW2F‡&VR'V–ÆG2Fò6Öö¶R(	BF†R&RÕ"Ô%Ts"'V–ÆBÂ7W'&VçBFWfÂæB"Õsw0¦'&æ6‚(	BæBF†R'VÆR&÷fR—2F†B¦&6VÂv†÷6R66WFæ6RæVVG2Ö÷&RF†âEtògVÆÂ6Öö¶P§76W2×W7B&R7Æ—B&Vf÷&R—B—26Æ–ÖVB¢âF†R6VÒF†B'VÆR&W67&–&W2—0¢¢¢†’ÆæBF†RÖV7W&VÖVçBæB6öÖÖ—B—G2çVÖ&W'2¢¢Â¢¢†"’6WBF†R&'2v–ç7BF†VÒ¢¢ÂæB—@¦V&ç2Ö÷&R†W&RF†âF†RF–ÖR—B6fW3¢F†R&6VÆ–æR†2FòW†—7B&Vf÷&Rç–öæR¶æ÷w2v†–6€§F‡&W6†öÆB—Bv–ÆÂ§W7F–g’Â6ò†"’6ææ÷BV–WFÇ’–6²&"æB6ÆÂ—BFW&—fVBà ¢¢¥v†BÆæFVBâ¢¢vV&W$6öçG&7FæB&VÆF—fTÇVÖ–ææ6V&RW‡÷'FVBg&öÐ¦FööÇ2ö7&—F–5öÖWG&–72æÖ§6(	BF†Rf—'7BF†–ær–âFööÇ2öFò6ö×WFRvV&W"Âv†–6‚G&VW2æ§6æ@¦Ä”$U%D”U2æÖF†fR&VVâV÷F–ær'’†æB(	BæBWfW'’&öB&æB–â6Öö¶U÷&VæFW&W"æÖ§6æ÷rÇ6ð§&W÷'G2¢¦vV&W&¢¢†W‡÷7W&RÖ–çf&–çB&öBÖv–ç7BÖw&÷VæB6öçG&7BÂÖvæ—GVFRÂÖVF–â÷fW"F†P§6ÖR&ö&W2’æB¢¦w&÷VæDÆ¢¢†ÖVF–â4”RÅÂ¢öbF†Rw&÷VæBBF†÷6R&ö&W2ÂF†RfÆö÷"&VF–ær’à¢¢¤æV—F†W"—2vFVBâ¢¢æ÷F†–ærF†—26†ævRF÷V6†W26âÇFW"72÷"f–ÂÂv†–6‚—2F†Rv†öÆP§&V6öâ—B—26fRFòÆæB–âöæR6Öö¶S¢vFRF†BÖ÷fW2BF†R6ÖRÖöÖVçB2—G2÷vâ&6VÆ–æP¦†2æò&6VÆ–æRà ¢¢¥D„R$4TÄ”äRÂFWd##ƒv#3²F†—2'&æ6‚ÂöæRgVÆÂ6Öö¶RÂ&÷F‚f–Ww÷'G2â¢¢vFVB&æG2öæÇ“°¦vV&W&—2F†RÖVF–âÖvæ—GVFRÂæF†R&ö&W2—B—2F¶Vâ÷fW"à §Â7FF–öâÂ&æBÂÖö&–ÆR3“9ssƒÂFW6·F÷#ƒ9sƒÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Â6÷WF…÷vFW&ÂC(	3ÒÂãCc†â3B’+rÅÂ¢S"ãrÂãSs†â32’+rÅÂ¢S2ãRÀ§Â6÷WF…÷vFW&Â(	3#SÒÂãCƒ"†â#B’+rÅÂ¢S2ãÂãcb†â3b’+rÅÂ¢SBãbÀ§Â6÷WF…÷vFW&Â#S(	3cÒÂ¢£ãS#r†âR’¢¢+rÅÂ¢S"ãÂãcCb†â’+rÅÂ¢SBãrÀ§Âg&öÕö&÷fVÂ(	3#SÒÂãc’†âC’+rÅÂ¢Sã"Â¢£ã#r†â’¢¢+rÅÂ¢Sã’À§Âg&öÕö&÷fVÂ#S(	3cÒÂãR†âS’+rÅÂ¢S2ãRÂã““’†â3#r’+rÅÂ¢S2ã’À§ÂÆ¶UöÖ&¶WFÂ.(	3CÒÂã“†â’+rÅÂ¢SãÂã3#b†â’+rÅÂ¢SãRÀ§ÂÆ¶UöÖ&¶WFÂC(	3ÒÂãC“†âR’+rÅÂ¢S"ãrÂã#ƒ‚†âR’+rÅÂ¢S"ãrÀ§ÂÆ¶UöÖ&¶WFÂ(	3#SÒÂã33’†âC2’+rÅÂ¢S2ãRÂ¢£‚ãƒ#2†â#2’+rÅÂ¢2ã¢¢À§ÂÆ¶UöÖ&¶WFÂ#S(	3cÒÂã#sB†â#"’+rÅÂ¢Sbã2Â¢£ã3“cR†â‚’¢¢+rÅÂ¢SBãBÀ ¢¢¥F†R–×ÆVÖVçFF–öâ—2fW&–f–VBv–ç7BçVÖ&W"F†—2&ö¦V7B6öÖÖ—GFVB&Vf÷&R—BW†—7FVBÂæ@¦F–Bæ÷B6ö×WFRâ¢¢"Õsw2&¶VBÖV7W&VÖVçB&V6÷&FVBvV&W"¢£ã#r¢¢Bg&öÕö&÷fVÀ¦FW6·F÷Â(	3#SÒÂFWdCsc&–ÂF¶Vâ'’†æBBF†Rö–çBöbW6RâF†—2†VÇW"&VG0¢¢£ã#rBâ¢¢v–ç7B"Õsw2¢¦ãÓ¢¢ÂöâFWfF†B†2Ö÷fVBVÆWfVâ6öÖÖ—G26–æ6Rà¥F†B—2&W&öGV7F–öâÂæ÷Bâw&VVÖVçBöbF¦V7F—fW2ÂæB—B—2F†RWf–FVæ6RF†BF†RGvð¦†ÇfW2öb"ÔÓ&RÖV7W&–æröæRVçF—G’âF†R#S(	3cÒ&æB—2F†RöæRF†BÖ÷fVB(	@£ã“C(i"ã““’‚³bã2R’Âv—F‚éDÅÂ¢"ã3b(i""ãB–â7FW(	Bv†–6‚—2"Ô%Ts2w2÷VRÖæBÖÇ†§v÷&²6†÷v–ærWv†W&R"Ô%Ts26–B—Bv÷VÆBæ÷B&V6‚æB—2v÷'F‚öæRÆ–æRöb"ÔÓ"w2GFVçF–öâà ¢¢¥F‡&VRF†–æw2†"’×W7Bæ÷BvÆ²7BÂæBF†Rf—'7BöbF†VÒ—2v‡’F†—2†Æbv2v÷'F‚ÆæF–æp¦öâ—G2÷vââ¢  ¢Ò¢¥tT$U"•2Tä$õTäDTB$TÄõrÂäBôäR$äBÅ$TE’$õdU2•BâÆ¶UöÖ&¶WFÂFW6·F÷À¢(	3#SÒ&VG2vV&W"‚ãƒ#6÷fW"w&÷VæBöbÂ¢2ãâ¢¢F†RFVæöÖ–æF÷"—2F†RÆ–v‡BF†P¢w&÷VæB—26''––ærÂæBBF†B7FF–öâÖ&æBÂöâF†Bf–Ww÷'BÂF†R&öBw2&ö¦V7FVB&ö&W0¢ÆæBv–ç7B6öÖWF†–ærÆÖ÷7B&Æ6²(	B6ò&F–òF†B&VG2ã2öâF†R6ÖR&æBBÖö&–ÆP¢&VG2¢¦V–v‡Bö–çBV–v‡B¢¢öâFW6·F÷âæ÷F†–ær—2w&öærv—F‚F†R&öBF†W&S²éDÅÂ¢&VG2‚ã ¢æBRW&6WF–&ÆRâ—B—2F†R66ÆRF†B†2æò6V–Æ–ær2—G2&6¶w&÷VæBvöW2F&²à¢¢¤ÖVF–âvV&W"÷fW"&æB6âF†W&Vf÷&R&R6WB'’—G2F&¶W7B&ö&W2&F†W"F†â'’—G0¢&öG2¢¢Âv†–6‚—2F†RW†7Bf–ÇW&RF†R÷væW"w2'VÆ–ærçF–6—FVBv†Vâ—B—&VBF†R&F–ð¢v—F‚fÆö÷"&F†W"F†â&WÆ6–æröæR&"v—F‚F†R÷F†W"â†"’†2Fò6’v†B—BFöW2&÷W@¢—B(	BW†6ÇVFR&ö&W2&VÆ÷rF†RfÆö÷"ÂvFRF†RGvò&'2W"×&ö&R&F†W"F†âW"ÖÖVF–âÂ÷ ¢6öÖWF†–ær&WGFW"(	BæB—B×W7Bæ÷B6–×Ç’F‡&W6†öÆBF†—26öÇVÖââ¢¤†BF†R&'2&VVâ6WB–à¢F†R6ÖR"2F†R&6VÆ–æRÂF†—2—2F†RçVÖ&W"F†W’v÷VÆB†fR&VVâ6WBv–ç7Bâ¢ ¢Ò¢¦6÷WF…÷vFW&B#S(	3cÒ—2æ÷B&æBÂ—B—2f–gFVVâ—†VÇ2â¢¢Öö&–ÆR&VG2¢£ãS#r¢ ¢v–ç7BWfW'’÷F†W"&æBw2ã(	3ãrÂöâ¢£R&ö&W26VVâöbS&ö¦V7FVB¢¢ÂæBFW6·F÷ ¢&VG2ãcCböâ¢£öbc3r¢¢âF‡&W6†öÆBf—GFVBFòF†B7FF–öâÖ&æB—2f—GFVBFòv†FWfW ¢F†÷6RfWr7W'f—f–ær&ö&W2†VâFò6—Bv–ç7Bâ$ôEôÔ”åõ$ô$U6—2‚æBF†—26ÆV'2—C°¢F†RçVÖ&W"F†B6†÷VÆBv÷''’F‡&W6†öÆB×6WGFW"—2F†R6VVâ×Fò×&ö¦V7FVB&F–òÂæ÷BF†R6÷VçBà¢Ò¢¥F†RfÆö÷"—2&VÖ&¶&Ç’fÆBæBF†B—2f–æF–ær&÷WBF†RfÆö÷"Âæ÷B&÷WBF†R&öG2â¢ ¢WfW'’vFVB&æBöâ&÷F‚f–Ww÷'G2&VG2w&÷VæBÅÂ¢¢£S(	3S‚¢¢âfÆö÷"&"ç—v†W&R&VÆ÷rãS ¢v÷VÆBæWfW"f—&Röâç’'V–ÆBF†—2&ö¦V7B†26†—VBÂv†–6‚Ö¶W2—BVçFW7F&ÆR&F†W"F†à¢6fRâ"Õsw2'V–ÆB—2F†RöæRF†BÖ÷fW2—B(	BN(	3rRF&¶W"(	B6òF†RfÆö÷"w2fÇVR†2Fò&P¢FW&—fVBv–ç7B§F†B¢'&æ6‚÷"—B—2FV6÷&F–öâà ¢222"ÔÓ"(	B6WBF†RGvò&'2+r¢¥Tä4Ä”ÔTB+räU…BU+rg&öÒ"ÔÓ+rVff÷'C¢Ò+r$Äô4´TBôâD…$U4„ôÄB4õU$4R¢  ¥F¶R"ÔÓw2F&ÆR2F†R&6VÆ–æRâv†B—2ÆVgB—2"ÔÓw2÷&–v–æÂ66WFæ6S¢F†RæWr&'0¢¢¦f–ÂöâF†R&RÕ"Ô%Ts"'V–ÆB¢¢æB¢§72öâ7W'&VçBFWf¢¢Â"Õsw2'&æ6‚—2&R×'Vâv–ç7@§F†VÒ¢§v—F†÷WB&R×GVæ–ærF†R7G&VWG2¢¢ÂWfW'’W†—7F–ær&æB7F–ÆÂ&W÷'G2ÂæBV6‚F‡&W6†öÆ@¦6'&–W2—G2FW&—fF–öâ–â6öÖÖVçB&W6–FR—Bà £â222D„RDU$•dD”ôâ4õU$4R"ÔÓäÔTBDôU2äõBU„•5BâDòäõB5T%5D•EUDRuTU52dõ"•Bà£à£â"ÔÓ6—2FòFW&—fRF†RF‡&W6†öÆG2'’ÖV7W&–ær'v†B6öçG&7B&VÂF—'BG&6²†öÆG0£âv–ç7B&VÂ&—&–R"–âF†R"Õ$Tc†÷Föw&‚â¢¤—BFöW2æ÷B6öçF–âF—'BG&6²â¢ £â—F†öã2FööÇ2öÖV7W&U÷&VfW&Væ6Rç–æ÷r7W'fW—2F†RÆæB&Vv–öâöbF†Rg&ÖRæB&–çG2—C £âF†Rv–FW7B6öçF–wV÷W2&&RÖV'F‚'Vâç—v†W&R&VÆ÷rF†R†÷&—¦öâ—2¢£33"‚Â‚ã"RöbF†P£âg&ÖRv–GF‚ÂB(‰#3‚ã,+¢¢(	BF†R&÷GFöÒVFvRÂBF†R†÷Föw&†W"w2÷vâfVWBÂæB—B—2Æ—GFW £âæBG'’7FV×2&WGvVVâÆçG2&F†W"F†â7W&f6RâF†Rv–FW7B'Vâv—F‚æòw&VVâW†6W72@£âÆÂ—2¢£ãRB(‰#ãL+¢¢Âv†–6‚—2F†R†¦VBG&VVÆ–æRæB—2æ÷Bw&÷VæBâG&6²7&÷76–æp£âF†Bg&ÖRv÷VÆBWB6öçF–wV÷W2&&R'Vâ7&÷72Æ&vRg&7F–öâöbF†Rv–GF‚B6öÖP£âVÆWfF–öââæ÷F†–ær–â—BFöW2âF†R6ö–ÂÖÆ–¶R¦g&7F–öâ¢—22R÷fW&ÆÂæB&—6W2Fò‚ãRP£â–âF†R&÷GFöÒ\+(	Bv†–6‚—2W†7FÇ’v‡’F†Rg&7F–öâ6ææ÷BFV6–FRF†—2æBF†R'VâÆVæwF€£â6âà£à£âF†—2—2F†R6ÖR6†RöbW'&÷"F†R##bÓ‚Ó7vVW&V6÷&FVBv–ç7B—G6VÆc¢'&–Vb†æFV@£â'V–ÆFW"F&vWB(	B¢%vV&W"ã3n(	3ãcr"¢(	BF†B¢¢&FöW2æ÷BW†—7B–âF†R&VfW&Væ6RBç£âF‡&W6†öÆB"¢¢ÂæB5DEU2æÖB6—2öb—B¢'F†BW'&÷"v2F†R'&–Vbw2Âæ÷BF†R'V–ÆFW"w2"¢à£â"ÔÓw2F‡&W6†öÆB6ÆW6R—2F†R6V6öæB–ç7Fæ6RâF†R6·’Â†÷&—¦öâæB6æ÷’&VF–æw2F†P£â†÷Föw&‚¦FöW2¢7W÷'B&RVçF÷V6†VB'’F†—2æB7F–ÆÂ&W&öGV6Rà£à£â¢¥6ò†"’æVVG26÷W&6RÂæB–6¶–æröæR—2&÷fRF†—2ÆæRw2’w&FRâ¢¢F†R†öæW7B÷F–öç2À£âf÷"F†R÷væW"&F†W"F†âf÷"'VææW# £à£ââ¢¤6V6öæB&VfW&Væ6R†÷Föw&‚¢¢(	BFö7VÖVçFVBF—'BG&6²F‡&÷Vv‚w&72Â42ÖÆ–6Vç6VBÀ£â6öÖÖ—GFVBF†Rv’"Õ$Tc6öÖÖ—GFVBF†—2öæRÂÖV7W&VB'’F†R6ÖR6öFRâ—B—2"Õ$Tcv–à£â–âgVÆÃ¢–FVçF–f–6F–öâÂ&–v‡G2ÂU„”bÂg&ÖR6öÇfVB6ò&VF–ær6â7FFR—G2VÆWfF–öâà£â6ÆÂ—B¢¥"Õ$Tc"¢¢â—B—2F†RöæÇ’÷F–öâF†BÖ¶W2&FW&—fVB"Æ—FW&ÆÇ’G'VRà£â"â¢¤V&Æ—6†VBFWFV7F–öâF‡&W6†öÆB¢¢Â6—FVB27V6‚(	BvV&W"6öçG&7BB†÷F÷–2ÆWfVÇ2f÷ £âÆ&vR7W&F‡&W6†öÆBF&vWB(	Bv—F‚F†R&"6WBB7FFVB×VÇF—ÆRöb—BæBF†P£â×VÇF—ÆR&wVVB–âF†R6öÖÖVçBâ†öæW7BÂæB—B—26Æ–Ò&÷WB¦W–W2¢Âæ÷B&÷WB§&öG2¢À£âv†–6‚—2F–ffW&VçB&"F†âF†R&6VÂ6¶VBf÷"æB×W7B&RÆ&VÆÆVB2öæRà£â2â¢¤g&VW¦R"ÔÓw2÷vâ&6VÆ–æR2æò×&Vw&W76–öâ&"¢¢ÂW‡Æ–6—FÇ’Æ&VÆÆVB&÷f—6–öæÂ–à£âF†R6öFRF†Rv’"ÔÓw27G'V6²Ö÷WBfÆÆ&6²v÷VÆB†fR&VVââ—B—2F†RvV¶W7C¢—B6—0£âöæÇ’&æòv÷'6RF†â##bÓ‚ÓR"æB—B6ææ÷Bf–ÂF†R&RÕ"Ô%Ts"'V–ÆBVæÆW72F†RÖ&v–à£â—26†÷6VâÂv†–6‚—2–6¶–ærçVÖ&W"v—F‚W‡G&7FW2à£à£â¢¤Fòæ÷BV–WFÇ’F¶R÷F–öâ2æBFW67&–&R—B2FW&—fVBâ¢¢–b†"’'&—fW2&Vf÷&RF†R÷væW £â†2'VÆVBÂÆæB÷F–öâ2¦Æ&VÆÆVB2÷F–öâ2¢æB6’6ò–âF†R"(	B÷"ÆVfRF†R&'0£âVævFVBæB6’v‡’à ¢2222"ÔÓ‡7V2’(	BF†R÷&–v–æÂ&6VÂFVf–æ—F–öâÂ¶WBfW&&F–Ð ¥Væ6†ævVBW†6WBf÷"F†RF‡&W6†öÆB×6÷W&6R&w&‚Âv†–6‚—27G'V6²F‡&÷Vv‚&VÆ÷rf÷"F†P§&V6öâ"ÔÓ"7FFW2â†’F—66†&vVBF†R†VÇW"ÂF†RGvòÖV7W&VÖVçG2æBF†R&6VÆ–æS²†"’÷vç0¦WfW'—F†–ærVÇ6R–â—Bà ¢¢¥F†RFV6—6–öâÂÖFR'’F†R÷væW"gFW""Õs'&ö¶RF†RvFR'’ÆVv—F–ÖFVÇ’6†æv–ærW‡÷7W&S §66÷&RW‡÷7W&RÖ–çf&–çB6öçG&7BäB¶VWâ'6öÇWFRfÆö÷"â&÷F‚&'2Âæ÷B&WÆ6VÖVçBâ¢  ¢¢¥v‡’F†RöÆBÖWG&–2v2æ÷Bw&öærÂöæÇ’VæwV&FVBâ¢¢4”RÂ¦—2W&6WGVÂ66ÆR(	BWVÀ§7FW2&R&÷Vv†Ç’WVÂW&6V—fVBF–ffW&Væ6R§VæFW"f—†VBFFF–öâ7FFR¢âF†B&V6öæF—F–öà¦†VÆBf÷"2Æöær2W‡÷7W&Rv2f—†VBÂæB"Õs—2F†Rf—'7B&6VÂFò'&V²—BâéDÅÂ¢F–Bæ÷@¦f–Ã²—G277V×F–öâF–BâÖV7W&VC¢"Õs&W6W'fVBF†R&öBöw&÷VæB&F–òFòv—F†–â¢£ãBR¢¢æ@§7F–ÆÂÆ÷7BF†RvFRÂ&V6W6RF†R66VæRv÷BN(	3rRF&¶W"à ¢¢¥v‡’&F–òÆöæR—2æ÷BF†Rç7vW"V—F†W"â¢¢6öçG&7B6Vç6—F—f—G’vVçV–æVÇ’6öÆÆ6W2BÆ÷p¦ÇVÖ–ææ6RÂ6òW&R&F–òÖWG&–2v÷VÆB7266VæRFöòF&²Fò6VRç—F†–ær–ââF†B—2F†P¦f–ÇW&RÖöFR&V–ærG&FVB–çFòÂæBF†RfÆö÷"—2v†B&WfVçG2—Bà ¢¢¥6ó¢6öçG&7B&"f÷"&—2F†R&öBF—7F–æwV—6†&ÆRg&öÒF†Rw&÷VæB"ÂæBÇVÖ–ææ6RfÆö÷"f÷ ¢&—2F†W&RVæ÷Vv‚Æ–v‡BFòF—7F–æwV—6‚ç—F†–ærBÆÂ"â¢¢V6‚6F6†W2v†BF†R÷F†W"6ææ÷BÂæ@§FövWF†W"F†W’&R7G&–7FÇ’7G&öævW"F†âF†R6–ævÆR&"–âÆ6RFöF’âF†—2—2æ÷B&VÆ†F–öà¦æB×W7Bæ÷B&V6öÖRöæR(	BF†RÖWG&–27F–ÆÂ†2Fòd”ÂöâF†R&RÕ"Ô%Ts"'V–ÆBà ¢¢¥vV&W"—2Fö7VÖVçFVB7FæF&B†W&RÂæ÷B6†&VB†VÇW"â¢¢G&VW2æ§3£ƒSf&V6öç2–âvV&W ¦6öçG&7Bv–ç7BF†R&"†÷Föw&‚æB5DEU2æÖFòÄ”$U%D”U2æÖFV÷FR—BÂ'WBæ÷F†–ær–à¦FööÇ2ö6ö×WFW2—BâW‡V7BFòw&—FRF†RgVæ7F–öââ(	B¢¤D•44„$tTB'’"ÔÓ¢£ ¦vV&W$6öçG&7FæB&VÆF—fTÇVÖ–ææ6V&RW‡÷'FVBg&öÒFööÇ2ö7&—F–5öÖWG&–72æÖ§6ÂæBF†P¦f—'7BF†–ærF†W’vW&RW6VBf÷"&W&öGV6VB"Õsw2†æB×F¶Vâã#rW†7FÇ’à §çâ¢¤FW&—fRF†RF‡&W6†öÆG3²Fòæ÷B–6²F†VÒâ¢¢FöF’w2$ôEôÔ”åôDTÅDôÂÒã†æ@¦$ôEôÔ”åõU$4UD”$ÄRÒãSVvW&R6WBVæFW"öæRW‡÷7W&RæB&Ræ÷rVææ6†÷&VBâF†R†öæW7@§6÷W&6R—2F†R&VfW&Væ6R†÷Föw&‚(	Bv†B6öçG&7BFöW2&VÂF—'BG&6²†öÆBv–ç7B&VÀ§&—&–Sò†Væ6R¢¥"Õ$Tcf—'7Bâ¢¢çä–bF†R&–v‡G2f÷&&–B6öÖÖ—GF–ær—BÂg&VW¦RF†RÖV7W&VBvV&W ¦f–wW&W2g&öÒF†RÆ7Bw&VVBÖvööB'V–ÆB‚¢£ã“BB#S(	3cÒÂã‚B(	3#SÒ¢¢ÂFW6·F÷À¦FWdCsc&–’2&÷f—6–öæÂfÆö÷"æB¢¦Æ&VÂF†VÒ&÷f—6–öæÂ–âF†R6öFR¢¢ççà ¢¢¥"Õ$TcÆæFVB##bÓ‚ÓRÂ6òF†RfÆÆ&6²—2öfbâ¢¢F†R†÷Föw&‚—26öÖÖ—GFVB@¦FF÷6÷W&6W2ö76WG2÷6&•ó#…öGWvU÷FÆÆw&72öGWvU÷FÆÆw&75ó#‚ÓrÓ#Bæ§væB—G0§&VF–æw2&W&öGV6R†—F†öã2FööÇ2öÖV7W&U÷&VfW&Væ6Rç–’â¢¤FW&—fRF†RF‡&W6†öÆG2g&öÒ—Bâ¢ ¥Gvò6öæF—F–öç26öÖRv—F‚—C¢V÷FRF†R¢¦VÆWfF–öâ¢¢öbWfW'’&VF–ær(	BVÆWfF–öâ‡&÷r’Ð¢ƒƒ#(‰"&÷r’òSrãFVw&VW2ÂF†Rg&ÖR'Vç2BãL+&÷fRF†R†÷&—¦öâFò3‚ã|+&VÆ÷r(	Bæ@¢¢¦ÖV7W&R—BÂæWfW"7WB—BW¢¢â—B—242%’Õ4Bã¢ÖV7W&VÖVçBæBfW&&F–Ò&VF—7G&–'WF–öà¦&R6ÆV&VBÂ7&÷÷"&W6×ÆR—2âFFF–öâF†Bv÷VÆBWB6†&TÆ–¶RöâF†—0§&W÷6—F÷'’†76WG2ôÄ”4Tå4U2æÖF’âF†RvV&W"f–wW&W2&÷fR7F’W6VgVÂ2F†RÆ7@¦w&VVBÖvööB'V–ÆBw2çVÖ&W'2Fò6æ—G’Ö6†V6²FW&—fVBF‡&W6†öÆBv–ç7BÂv†–6‚—2F–ffW&Vç@¦¦ö"g&öÒ&V–ærF†RF‡&W6†öÆBççà ¢¢¥5E%T4²##bÓ‚ÓR'’"ÔÓ¢F†R†÷Föw&‚6öçF–ç2æòF—'BG&6²Â6ò—B6ææ÷B&RF†P§6÷W&6Râ¢¢ÖV7W&VBÂ&–çFVBæB&W&öGV6–&ÆR(	B—F†öã2FööÇ2öÖV7W&U÷&VfW&Væ6Rç–â6VP¥"ÔÓ"w2&÷‚&÷fRf÷"v†BF†R÷F–öç2æ÷r&S²F†RGvò6öæF—F–öç2öâ§&VF–ær¢F†R†÷Föw&€¢‡V÷FRF†RVÆWfF–öâÂæWfW"7WB—BW’7FæBæBÇ’Fòç—F†–ærF†BÖV7W&W2—Bà ¢¢¤æ÷BW6W"6WGF–ærÂæBF†R&V6öæ–ær—2v÷'F‚¶VW–ærâ¢¢F†RvFR'Vç2†VFÆW72–â4“²F†W&P¦—2æòW6W"–âF†R&ööÒâ—G2F‡&W6†öÆG2&RÇ&VG’GVæ&ÆR–âF†R&–v‡Bv’(	BæÖVB6öç7FçG2@§F†RF÷öb6Öö¶U÷&VæFW&W"æÖ§6v—F‚F†R&V6öæ–ær&W6–FRF†VÒÂ6ò6†ævRV'2–âF–fbæ@¦vWG2&wVVBâÖ÷f–ærF†VÒFò6öæf–rf–ÆRv÷VÆBÖ¶RF†VÒV6–W"Fò6†ævR§v—F†÷WB¢&Wf–WrÀ§v†–6‚—2&6·v&G2f÷"vFRà ¢¢¤f–ÆW3¢¢¢FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6+rFööÇ2ö7&—F–5öÖWG&–72æÖ§6‡F†RvV&W"†VÇW"’+p¦FööÇ2öÖV7W&U÷&VfW&Væ6Rç–…"ÔÓÂF†R7W'fW’F†B7G'V6²F†RF‡&W6†öÆB6÷W&6R¢¢¤66WFæ6S¢¢¢F†RæWr&'2f–ÂöâF†R&RÕ"Ô%Ts"'V–ÆBæB72öâ7W'&VçBFWf²"Õsw0¦'&æ6‚—2&R×'Vâv–ç7BF†VÒ¢§v—F†÷WB&R×GVæ–ærF†R7G&VWG2¢£²WfW'’W†—7F–ær&öB&æB7F–ÆÀ§&W÷'G3²F‡&W6†öÆG26''’F†V—"FW&—fF–öâ–â6öÖÖVçBâ(	B¢¦ÆÂöb—B"ÔÓ"w2¢¢ÂW†6W@¢&WfW'’W†—7F–ær&öB&æB7F–ÆÂ&W÷'G2"Âv†–6‚"ÔÓ†öÆG2w&VVâ'’æ÷BvF–ærç—F†–ærà ¢222"ÔÓB(	B&æB6â6öÆÆ6Rv—F†÷WBF†R7V—FR6––ærç—F†–ær+r¢¥Tä4Ä”ÔTB+rTå4TTâ+rg&öÒ"Õs+rVff÷'C¢2¢  ¢¢¥F†RvFR—2W"5DD”ôâæBF†RÖV7W&VÖVçB—2W"$äBÂ6ò&æBF†BfÆÇ2öfb6Æ–fbVæFW"§7FF–öâF†B—2Ç&VG’&VB—2–çf—6–&ÆRâ¢¢"ÕsFöö²6÷WF…÷vFW&#S(	3cÒg&öÒ¢£sRöb&ö&W0§W&6WF–&ÆRFòbR¢¢(	BSR×ö–çB6öÆÆ6R–âF†Rf"&öBF÷vâ7G&VWB(	BæBF†R7V—FR&W÷'FV@¢¢£##’76VBò"f–ÆVB¢¢&Vf÷&RæB¢£##’76VBò"f–ÆVB¢¢gFW"â–FVçF–6Ââæ÷F†–ær–âF†P§7VÖÖ'’Ö÷fVBÂ&V6W6RF†B7FF–öâv2Ç&VG’f–Æ–æröâ—G2£(	3#SÒ¢&æBÂæB&BæÆVæwF€£ÓÓÒ6ææ÷BF—7F–æwV—6‚öæR&B&æBg&öÒGvòà ¢¢¤&VFW"6ö×&–ærFÆÆ–W2v÷VÆB†fR6öæ6ÇVFVBF†R&6VÂ6÷7Bæ÷F†–ærâ¢¢F†B—2F†R6ÖR6†P¦öb&Æ–æFæW722"ÔÓ2öæR7FWW¢F†W&RÂâö66ÇVFW"6÷VÆB&—6R66÷&Rv—F†÷WBç–öæR6VV–æs°¦†W&RÂ&Vw&W76–öâ6â†Vâv—F†÷WBç–öæR6VV–ærâ&÷F‚&RF†R7V—FR&W÷'F–ærfW&F–7Bv†W&R¦f–wW&Rv2æVVFVBà ¢¢¥66÷Râ¢¢&æ²V6‚vFVB&æBw2Æ7Bf–wW&RæB$Uõ%Bç’&æBF†BÖ÷fW2v–ç7B—G2÷vâ&æ°¦'’Ö÷&RF†â7FFVBÖ&v–âÂv†FWfW"F†R7FF–öâw2fW&F–7Bâ—B—2&W÷'BÂæ÷BæWr&"(	BF†P§F‡&W6†öÆG27F’W†7FÇ’v†W&RF†W’&R(	B'WB—B×W7B&RÆ÷VBVæ÷Vv‚F†B'Vâ6ææ÷BÆæB£SR×ö–çBG&÷æBFW67&–&RF†R7V—FR2Væ6†ævVBâ&öD6öçG&7B‚–Ç&VG’&WGW&ç2WfW'—F†–æp¦æVVFVC²æ÷F†–æræWr†2Fò&RÖV7W&VBà ¢¢¥vF6‚F†RF—&V7F–öââ¢¢F†—2×W7Bæ÷B&V6öÖR&F6†WBF†Bf÷&&–G2&æBg&öÒWfW"fÆÆ–ær(	@¥"Õs6†÷w2&æB6âfÆÂf÷"â†öæW7B&V6öââF†R&WV—&VÖVçB—2F†BF†RfÆÂ—2§7FFVB–âF†P¥"¢Âæ÷BF†B—B—2f÷&&–FFVâà ¢¢¤f–ÆW3¢¢¢FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6‡F†R$ôEõ5DD”ôå6Æö÷’ÂÇW2&æ¶VBf–wW&W2f–ÆP¢¢¤66WFæ6S¢¢¢&WÆ’"Õsw2'&æ6‚v–ç7BFWfæB6†÷rF†RFööÂæÖ–ær6÷WF…÷vFW&#S(	3cÐ£sR(i"bRv—F†÷WB&V–ærFöÆBv†W&RFòÆöö³²æòF‡&W6†öÆBÖ÷fW3²&æBF†B&—6W2—2&W÷'FVBFöòà ¢222"ÔÓ2(	BF†R&öB66÷&RF—f–FW2'’çVÖ&W"âö66ÇVFW"6â6‡&–æ²+r¢¤DôäR##bÓ‚Ób‚3#r’(	BF†RFVæöÖ–æF÷"—2ä&&V²F†—2†VFW"v27FÆRVçF–Â##bÓ‚Ór¢  ¢¢¤vFRv†÷6R66÷&R”Õ$õdU2v†Vâ6öÖWF†–ær†–FW2F†RF†–ær—BÖV7W&W2—2F—f–F–ær'’F†Rw&öæp¦çVÖ&W"â¢¢&öD6öçG&7B‚–6ö×WFW2W&6WF–&ÆV2G2æf–ÇFW"†BãÒ"’æÆVæwF‚òG2æÆVæwF†Âv†W&P¦G6'Vç2÷fW"F†R&ö&W2¢¥4TTâ¢¢âç—F†–ær7FæF–ær&WGvVVâF†R6ÖW&æBf–çB7G&WF6‚öb&ö@§&VÖ÷fW2F†B7G&WF6‚g&öÒF†RFVæöÖ–æF÷"ÂæBF†R&æB66÷&W2†–v†W"f÷"—Bà ¢¢¥F†—2—2"Ô%Ts2w2÷vâÆW76öâ7W'f—f–æröæRÆWfVÂ&VÆ÷rv†W&R"Ô%Ts2f—†VB—Bâ¢¢"Ô%Ts2Ç&VG¦Ö÷fVBF†RFV6—6–öâöbt„UD„U"FòvFR&æBg&öÒ&Væ÷Vv‚&ö&W24TTâ"Fò&Væ÷Vv‚$ô¤T5DTB"Âæ@¦—G26öÖÖVçB6—2v‡“¢¢&&æBæö&öG’6â6VR&W÷'G2ãÓæBvFW2—G6VÆb÷WBÂv†–6‚—0¦–æF—7F–æwV—6†&ÆRg&öÒ&æBv—F‚æò&öB–â—Bâ"¢F†R6ÖR&wVÖVçBÆ–W2FòF†R66÷&RæBv0¦æ÷BÆ–VBFò—Bà ¢¢¥D„R”å5E%TÔTåBt2Å$TE’%T”ÅBäBÅ$TE’$”åD”ärâ¢¢F†R6†÷DÔfÖ&¶W"72†÷Föw&‡2F†P§6ÖR&ö&W2v—F‚F†R7v&BæBF†RG&VW2†–FFVâÂæB—G2÷vâ6öÖÖVçB7FFW2F†—2&6VÂw2f–æF–ær–à¦gVÆÃ¢¢$&ö&RÖ&¶VB†W&R'WBæ÷B–â6†÷DÖ—2&öBF†B—2ôâ45$TTâæB4õdU$TB%¥dTtUDD”ôâÂ¢§v†–6‚F†RÖ&¶VBÖöæÇ’FVæöÖ–æF÷"G&÷2–ç7FVBöbf–Æ–ær¢¢â"¢—Bv2w&—GFVâ2¦F–væ÷7F–2Â—B†2&VVâ&W÷'FVB–âWfW'’&æBÆ–æRf÷"Gvò&6VÇ2ÂæBæ÷F†–ærWfW"F—f–FVB'’—Bà ¢¢¦ä&&V—2F†RFVæöÖ–æF÷"ÂäõBå&ö¦V7FVF(	BæBF†RF–ffW&Væ6R—26Æ–Ò&÷WBv†Bf—6—F÷ ¦—2÷vVBâ¢¢&öB&V†–æB7F÷&R—2&öBf—6—F÷"ÆVv—F–ÖFVÇ’6ææ÷B6VRÂæB66÷&–ærv–ç7@¦å&ö¦V7FVFv÷VÆBFVÖæB‚×&’f—6–öâF‡&÷Vv‚F†RF÷vâw2÷vâ'V–ÆF–æw2âfVvWFF–öâ—2F–ffW&VçC ¦—B—2÷W'2Â—BÖ÷fW2v†VâvR6†ævR—BÂæB—B×W7Bæ÷B&R&ÆRFòÆVæFW"f–çB&öB÷WBöbF†P§6×ÆRâ6VVâ(¨b&&VÇv—2Â6òF†R6†ævR6âöæÇ’WfW"ÄõtU"66÷&Rà ¢¢¤ÖV7W&VBöâöæR&æB7&÷72F‡&VR'V–ÆG2F†R6ÖRWfVæ–ærÂæBF†R66R—2F†R7F&–Æ—G’&F†W §F†âç’6–ævÆRçVÖ&W"â¢¢W&–Âæ6†÷"Â#S(	3cÒÂÖö&–ÆRÂV&Æ—6†VBÖ—'&÷"Â6ÖR'VææW"âF†RöæÇ¦F–ffW&Væ6R&WGvVVâF†R6öÇVÖç2—2v†BF†RæV"Öf–VÆBvööB—2Fö–æs  §ÂW&–ÂÂ#S(	3cÒÂvööBÖ—'&÷&VB†FWf6VFS’ÂvööB&W—&VB…"Ô%TsV"’ÂvööBv–FVæVB„³CR†#"’’À§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Â&ö&W2¢§6VVâ¢¢ÂSrÂsrÂc2À§Â&ö&W2¢¦&&R¢¢Â¢£ƒ"¢¢Â¢£ƒ"¢¢Â¢£ƒ"¢¢À§ÂW&6WF–&ÆR&ö&W2Âã“rÂã“bÂã“bÀ§Â66÷&R÷fW"¢§6VVâ¢¢‡F†RöÆBöæR’Â¢£c"R¢¢(	B76W2Â¢£SBR¢¢(	Bf–Ç2Â¢£S’R¢¢(	B76W2À§Â66÷&R÷fW"¢¦&&R¢¢‡F†—2&6VÂ’Â¢£S2ã2R¢¢Â¢£S"ãrR¢¢Â¢£S"ãrR¢¢À ¢¢¥F†RöÆB66÷&R7wVærV–v‡Bö–çG2F‡&VRF–ÖW2v†–ÆRF†RçVÖ&W"öb&VF&ÆR7G&WF6†W2öb&öBæWfW ¦Ö÷fVBöfbæ–æWG’×6—‚â¢¢F†R'V–ÆBv—F‚'VrF†B7FööBF†Rv†öÆRvööBöâF†Rw&öær6–FRöbF†P§&—fW"66÷&VB„”t„U5BöbF†RF‡&VS²³CR†#"’v÷VÆB†fRvöæRw&VVâ'’ÆçF–ærÖ÷&RF–Ö&W"–âg&öçBö`§F†R6ÖR&öBâF†R†öæW7B66÷&R—2fÆBFò†Æbö–çBÂæB—B—2¢§VæFW"F†RãSR&"–âÆÀ§F‡&VR¢¢(	Bv†–6‚—2F†R&VÂ7FFRöbF†B&æBæBÇv—2v2à ¢¢¥66÷Râ¢¢6†ævRW&6WF–&ÆVw2FVæöÖ–æF÷"g&öÒG2æÆVæwF†Fòä&&V²¶VWæÂä&&Væ@¦å&ö¦V7FVFÆÂ&–çF–ær6òö66ÇW6–öâ7F—2ÆVv–&ÆR2ö66ÇW6–öââF†Vâ&R×&VBWfW'’&æBBWfW'§7FF–öâæBw&—FRF÷vâv†BÖ÷fW2(	BF†—2t”ÄÂGW&â&æG2&VBF†B&VBw&VVâFöF’ÂæBF†B—2F†P§&6VÂÂæ÷B6–FRVffV7Bà ¢¢¥F†RF†–ærF†—2&6VÂ×W7Bæ÷BFòâ¢¢—B×W7Bæ÷B'&—fRv—F‚$ôEôÔ”åõU$4UD”$ÄVÆ÷vW&VBFð¦'6÷&"v†B—BVæ6÷fW'2â–b†öæW7B66÷&–ærWG2&æBVæFW"F†R&"ÂF†R&æB—2VæFW"F†R&"Âæ@§F†Rf—‚—2¢¥"Õs"¢¢w2FW‡GW&VB6÷fW&vR÷"¢¥"Õs¢¢w2Æ–v‡B(	Bæ÷B6ÖÆÆW"çVÖ&W"âæ÷FRF†BF†—0¦6†ævRÖ¶W266÷&W27G&–7FÇ’tõ%4RÂæWfW"&WGFW"Â6ò—B6ææ÷B&RÖ—7F¶Vâf÷"&÷WFRF‡&÷Vv‚¦vFRà ¢¢¤f–ÆW3¢¢¢FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6†&öD6öçG&7FÂæÆ–æRC“r¢¢¤66WFæ6S¢¢¢F†RFVæöÖ–æF÷"—2ä&&V²æÂä&&VæBå&ö¦V7FVFÆÂ7F–ÆÂ&–çC²F†P¦W&–Â#S(	3cÒ&æB—26†÷vâ&VF–ærF†R6ÖRöâÖ—'&÷&VB×vööB'V–ÆBæB&W—&VBöæS²WfW'’&æBw2æWrf–wW&P¦—2&V6÷&FVB–âF†R#²æòF‡&W6†öÆBÖ÷fW2à ¢222"Ô(	B&öBÖÆVv–&–Æ—G’66W76–&–Æ—G’–B+r¢¤DôäR##bÓ‚Ób(	B6†—VBôdb'’FVfVÇBÂæBF†RvFRF†B&÷fW2—B&V6†W2F†R&VæFW"†BFò&RÖV7W&VB&Vf÷&R—B6÷VÆB&R6WB¢  ¢¢¥&VBF†—2&÷‚&Vf÷&RFF–ærç’÷F†W"&VfW&Væ6RFò6WGF–æw2â¢  ¢¢¥v†B6†—VBâ¢¢¢¥&öBf—6–&–Æ—G’¢¢6Æ–FW"Â&öD–F(i"ÂFVfVÇB¢£¢¢â—B66ÆW2F†P§7G&VWB&–&&öç2rÇ†Æ7B–â7G&VWG2æ§6w2g&vÖVçBF6‚(	BgFW"F†RF†–â×&–&&öâfÆö÷"æ@¥"Ô%Ts2w2æV"Æ–gB(	B6ò—B6âæWfW"6†ævRv†–6‚7W&f6R—2f–çFW"F†âv†–6‚â”Eôt”æ—0¦òã#F¢ã#B—2F†Rf–çFW7B&öG’Ç†ç’7W&f6RWF†÷'2†Æ–v‡Bv÷&âV'F‚B—G27&÷vâ’À§6ògVÆÂ–BF¶W2F†BöæR7W&f6RFò÷VRÂv†–6‚—2F†R6V–Æ–ær"Ô%Ts2ÖV7W&VB'’f÷&6–ærF†P¦æV"&ö&W2÷VRâBU&öD–BÓÒF†RGvòFFVBÆ–æW2&VGV6RFòÖ–â†¢ãÂÔ…ôÅ„–(	@§F†R7FFVÖVçBF†Bv2Ç&VG’F†W&R(	B6òF†RFVfVÇBg&ÖR—2F†Rg&ÖRF†B6†—VB&Vf÷&RF†P¦6öçG&öÂW†—7FVBà ¢¢¤f–æF–ær(	B'F†RFVfVÇB—2Væ6†ævVB"76W'F–öâ—2æ÷BVæ÷Vv‚ÂæB"Ô%Ts—2v‡’â¢¢F†P¦ö'f–÷W2vFRf÷"&VfW&Væ6R—2F†B—B—2–æW'BB—G2FVfVÇBâF†B76W'F–öâ76W0¦–FVçF–6ÆÇ’v†WF†W"F†R6öçG&öÂ—2v—&VB6÷'&V7FÇ’÷"¢§v—&VBFòæ÷F†–ær¢¢Âv†–6‚—2W†7FÇ’F†P¦f–ÇW&R"Ô%Ts&æ¶VBöæR&6VÂvó¢ÒÖæò×7Vâ×6†F÷v6ÆV&VB7W7V7B—BæWfW"&V6†VBæ@§&W÷'FVB&æ÷BF†R6W6R"f÷"F†R6ÖR&V6öâ'&ö¶VâF†W&ÖöÖWFW"&W÷'G27FVG’FV×W&GW&Rà¥6òF†R–B—2vFVBF‡&VRv—2Âæ÷BöæR(	B¢¦öfbB&ö÷B¢¢Â¢§&—6–ær—B6†ævW2F†Rg&ÖR¢¢À¢¢¦G&÷–ær—B&W7F÷&W2F†Rg&ÖR¢¢(	BæBF†RÖ–FFÆRöæR—2F†RÆöBÖ&V&–æröæRâ¢¥F†P¦vVæW&Æ—6F–öã¢â–æW'FæW7276W'F–öâæVVG2Æ—fVæW7276W'F–öâ&W6–FR—BÂ÷"—B—2FW7BF†@¦6öçG&öÂW†—7G2&F†W"F†âFW7BF†B—Bv÷&·2â¢  ¢¢¤f–æF–ær"(	BF†R–ç7G'VÖVçB†BFò&RÖV7W&VB&Vf÷&RF†RF‡&W6†öÆB6÷VÆB&R6WBÂæBF†P¦FVfVÇB–ç7G'VÖVçBv2F†Rw&öæröæRâ¢¢F†R,+"g&ÖR6–væGW&RF†R6öæf–FVæ6Rf–Wr—2w&FVBöà¦fW&vW2F†R–Bv“¢BÆ¶UöÖ&¶WFF†R&öGv’—2&÷WBFVçF‚öbF†Rg&ÖRÂæBF†Rf—'7@§'Vâ66÷&VB¢§v÷'7B"6÷VçG2v–ç7B&W7F÷&VB&W6–GVÂöb¢¢(	B&VÂ6–væÂv—F‚æò†VG&ööÒFð¦vFRöââB¢£CŒ+"¢¢F†R6ÖRF–ffW&Væ6R—2¢§v÷'7BbÂÖVâã#b¢¢Â&W6–GVÂ7F–ÆÂ¢£ãò¢¢à¤vFVBBv÷'7B(šRBòÖVâ(šRãRÂF†—&BVæFW"F†RÖV7W&VÖVçBâ&÷F‚w&–G2&R&–çFVBà¢¢¤æ÷F†–ær&÷WBF†R66VæR6†ævVB&WGvVVâF†÷6RGvò'Vç2¢¢(	BöæÇ’†÷rf–æVÇ’F†Rg&ÖRv0¦F—f–FVB&Vf÷&R—Bv26ö×&VBÂv†–6‚—2v÷'F‚&VÖVÖ&W&–ærF†RæW‡BF–ÖRFVÇFvFR&VG0¢&&&VÇ’"à ¢¢¥v‡’—Bv2ÆÆ÷vVBFò6†—BÆÂâ¢¢—Bv2FVfW'&VB##bÓ‚ÓB&V6W6R6öçG&7B&VfW&Væ6P¦6öçfW'G2FVfV7B–çFò&VfW&Væ6Râ"Ô%Ts2ÖFRF†RFVfVÇB6÷'&V7Böâ##bÓ‚ÓR†æV"&æ@£ãRÅÂ¢ò3R(i"¢£2ãöb6V–Æ–æröb2ãBòƒR¢¢öâÖö&–ÆR’Âv†–6‚—2F†R&V6öæF—F–öâF†P¦FVfW'&Â—G6VÆbæÖVBâ¢¤—BFöW2æ÷BF—66†&vR"Õs"¢£¢F†RæV"&æBw2¦6V–Æ–ær¢—27F–ÆÂF†P¦Æ÷vW7Böbç’&æBæBFW‡GW&VB6÷fW&vR—2F†R†öæW7Bf—‚f÷"F†Bà ¢¢¤f–ÆW3¢¢¢&VæFW&W'2÷vV"ö§2÷7G&VWG2æ§6‡F†RVæ–f÷&ÒÂ6WDÆVv–&–Æ—G”–F’+p¦&VæFW&W'2÷vV"ö§2ö‡VBæ§6†&öD–FÂF†R&ævR’+r&VæFW&W'2÷vV"ö§2öÖ–âæ§6†&ö÷B²öå6WGF–æv ¢²F†R†&æW72†æFÆR’+r&VæFW&W'2÷vV"ö–æFW‚æ‡FÖÆ‡F†R6öçG&öÂæB—G2æ÷FR’+p¦FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6‡F‡&VR76W'F–öç2’à ¢¢¤æ÷B6Æ–ÖVC¢¢¢F†RFW6·F÷†ÆböbF†R6Öö¶R(	Bã2Ö–âv–ç7BF†—2'VææW"w2ÖÖ–çWFP§W"Ö6öÖÖæB6V–Æ–ærâÖö&–ÆR3“9ssƒ—2w&VVâÂ##’76VBòf–ÆVBöâF†RV&Æ—6†VBÖ—'&÷"âæð¦66W76–&–Æ—G’7FæF&B—26Æ–ÖVBFò&RÖWBÂæBFö72ôÄ”$U%D”U2æÖF—2VçF÷V6†VC¢F†RFVfVÇ@§&VæFW&–ær—2Væ6†ævVBFòF†RF–v—Bà ¢¢¥F†R÷&–v–æÂ&÷‚Âf÷"F†R&V6öæ–ærF†BvFVB—C¢¢  ¤6öç6–FW&VBæBFVÆ–&W&FVÇ’FVfW'&VBÂ##bÓ‚ÓBÂ&V6W6RF†R&V6öæ–ærÖGFW'2Ö÷&RF†âF†P ¤6öç6–FW&VBæBFVÆ–&W&FVÇ’FVfW'&VBÂ##bÓ‚ÓBÂ&V6W6RF†R&V6öæ–ærÖGFW'2Ö÷&RF†âF†P¦fVGW&RâW6W"6öçG&öÂF†B&ö÷7G2&öB6öçG&7B¢¦6öçfW'G2FVfV7B–çFò&VfW&Væ6R¢¢æ@§F¶W2F†R&W77W&Röfbf—†–ærF†RFVfVÇBâ³#Fw2Æ–v‡F–ær6WGF–ær—2FVfVç6–&ÆR&V6W6R&÷F€§÷6—F–öç2&RÆVv—F–ÖFRæBF†RFVfVÇB—2F†RWf–FVæ6RÖæ6†÷&VBöæS²¢'&öG2–÷R6ææ÷B6VP§v†–ÆR7FæF–æröâF†VÒ"¢—2æ÷B÷6—F–öâv÷'F‚öffW&–ærà ¢¢¤'WBF†R66W76–&–Æ—G’66R—2&VÂ¢¢(	B6öçG&7B6Vç6—F—f—G’f&–W2ÂæB†öæR67&VVâ–à§7VæÆ–v‡B—2''WFÂÂv†–6‚—2F†RW†7B6öæF—F–öâ"Ô%Ts2v2&W÷'FVBg&öÒâ6òF†—26†—22à¦–BÆ–W&VBöâ6÷'&V7BFVfVÇB(	B¢¥"Ô%Ts2ÖFRF†RFVfVÇB6÷'&V7Böâ##bÓ‚ÓRÂ6òF†P§&V6öæF—F–öâ—2ÖWB¢¢(	BæB—B–æ†W&—G2³#Fw26öç7G&–çC¢F†R†&æW72ÖV7W&W2F†RFVfVÇ@§&Vv&FÆW72öb7F÷&VB&VfW&Væ6Râæ÷FRv†B"Ô%Ts2ÆVgB7FæF–æs¢F†RæV"&æBw2¦6V–Æ–ær¢—0£2ãN(	3Bã2ÅÂ¢ÂF†RÆ÷vW7Böbç’&æBÂæBf–gF‚öbæV"&ö&W26ææ÷B6ÆV"F†RF‡&W6†öÆBWfVà¦gVÆÇ’÷VRâF†R†öæW7Bf—‚f÷"F†B—2¢¥"Õs"¢¢w2FW‡GW&VB6÷fW&vRÂæ÷BF†—2–C²6†—–æp§F†—2öæR×W7Bæ÷B&RÆÆ÷vVBFò&WF—&RF†Bà ¢222"Ô%Ts2(	BF†R&öB—2–çf—6–&ÆRB”õU"dTUB+r¢¥%DÅ’DôäR##bÓ‚ÓR+r$TõTäTB2"Ô%Ts62¢  ¢¢¥v†B—BFöö²ÂæBv†B—B&VgWFVBâ¢¢F†RæV"&æBv2FFVBÂ—Bf–ÆVBW†7FÇ’2F†—2&6VÀ§&VF–7FVB(	B¢£ãRÅÂ¢v—F‚3Röb&ö&W2W&6WF–&ÆRB.(	3CÒÂv–ç7B2ãBòƒrR–âF†RfW'¦æW‡B&æB÷WB¢¢(	BæB—B—2æ÷r¢£2ãöbÖV7W&VB6V–Æ–æröb2ãBÂv—F‚ƒRW&6WF–&ÆR¢¢öà¦Öö&–ÆRƒ2ã"öbBã2v—F‚cRöâFW6·F÷’ÂöâF†RV&Æ—6†VBÖ—'&÷"âF‡&VP¦f–æF–æw26ÖR÷WBöb—BÂæBöæÇ’F†RF†—&B—2F†RöæRF†—2&6VÂW‡V7FVC  £â¢¥F†RæV"&æBv2TÕE’ÂæBæòF‡&W6†öÆBv÷VÆB†fR6Vv‡BF†—2'Vrâ¢¢³"ÂCÖöâ—G2÷và¢6†ævW2æ÷F†–ærÂ&V6W6R¢¦æV—F†W"vFVB7FF–öâ7FæG2öâ&öB¢£¢6÷WF…÷vFW&6—G2¢£Ð¢g&öÒF†R6VçG&VÆ–æR—B—2æÖVBgFW"¢¢‡F†B—2BÕc"ÂÖV7W&VBg&öÒF†R6öÖÖ—GFVBF‚’æ@¢rÒg&öÒF†RæV&W7BöæRÂæBg&öÕö&÷fV—2sRÒWâF†RæV"&æB6öÆÆV7FVB¢¦öæR&ö&R¢ ¢BF†Rf—'7B7FF–öâæB¢¦æöæR¢¢BF†R6V6öæBâF†R&6VÂw2÷vâf—'7BÖ÷fRv2æV6W76'’æ@¢æ÷v†W&RæV"7Vff–6–VçB(	BF†Rv–æF÷rv2w&öær–âEtòF–ÖVç6–öç2ÂF—7Fæ6RæB÷6RÂæBöæÇ¢F†RF—7Fæ6RöæRv2f—6–&ÆRg&öÒF†Rf–Æ–ærvFRâF†W&R—2æ÷rF†—&B7FF–öâÀ¢Æ¶UöÖ&¶WFÂv†–6‚'&—fW2F†Rv’f—6—F÷"FöW2(	B'’6Æ–6¶–ærfW&–f–VB7G&VWBÖ6öçG&öÀ¢–çFW'6V7F–öâ–âF†RvòFòF"(	BæBF†VâGW&ç2FòÆöö²ÆöærF†R6VçG&VÆ–æR—B—27FæF–æröâÀ¢&V&–ær&VBöfbF†R6öÖÖ—GFVBF‚&F†W"F†âWF†÷&VB†W&RâF†R'&—fÂ÷6RÆöæRv0¢æ÷BVæ÷Vv‚V—F†W#¢F†R6†—VB§V×f6W2f—†VB&V&–ærÂv†–6‚B7&÷76–ærö–çG0¢F–vöæÆÇ’–çFòF†R&Æö6²æBWB¢§¦W&ò¢¢&öB&ö&W2–ç6–FRÒà£"â¢¥D„R$”ÔR5U5T5B•2$TeUDTB(	Bæòw&72—2†–F–ærF†—2&öBâ¢¢F†R†&æW72æ÷r&R×6†ö÷G2—G0¢&öBÖ&¶W'2v—F‚F†R7v&BæBF†RG&VW2†–FFVâÂ6òâö66ÇVFVB&ö&R—2F—7F–æwV—6†&ÆRg&öÐ¢â'6VçBöæRÂæB–âF†RæV"&æB¢¦ÆÂFVâ&ö&W2&RÖ&¶VBV—F†W"v’¢¢â7v&Bö66ÇW6–öà¢æBF†R6ÆV&–ærÖ6÷'&–F÷"v–GF‚&R&÷F‚÷WBÂF†—2&6VÂw2æöâÖÆ–6Væ6RæWfW"†BFò&RFW7FVBÀ¢æBfÆ÷&æ§6—2VçF÷V6†VBâF†RvFR&W÷'G2F†RF—67&–Ö–æF–öâöâWfW'’&æBg&öÒæ÷röà¢†6VVââöbÒ&ö¦V7FVB„²6ÆV"öbfÆ÷&–’&V6W6R—B—2F†RF—7F–æ7F–öâF‡&VRvFW2–â&÷p¢†fRf–ÆVBFòG&rà£2â¢¥F†RfVÇB—26æF–FFR2ÂæBF†RÖV6†æ—6Ò—26†'W"F†â&Ç†"â¢¢âÇ††W&R—2¢¢¦6÷fW&vRg&7F–öâ¢¢ÂæB6÷fW&vRg&7F–öâ—2öæÇ’F†R&–v‡B–7GW&RöbÖ—‡GW&Rv†W&RöæP¢—†VÂ7ç2Öç’F6†W2öb—BâW6Æ÷6RöæR—†VÂ7ç2öæRF6‚Âv†–6‚—2V—F†W"V'F‚÷ ¢w&72ÂæBF†R&ÆVæB–çG2Væ–f÷&Òv6‚–ç7FVBâF†R†&æW72ÖV7W&W2&÷F‚VæG3¢F†R6ÖP¢æV"&ö&W2f÷&6VBgVÆÇ’¢¦÷VR¢¢66÷&R¢£2ãBÅÂ¢¢¢Â6òF†R6öçG&7Bv2–âF†R&–&&öâw2÷và¢6öÆ÷W"æBF†R6†—VBÇ†v27VæF–ærVæFW"†Æböb—BâF†RæV"f–VÆBÇ6ò†2ÆW72Fò7VæB(	BF†P¢w&÷VæBVæFW&fö÷B—2vVçV–æVÇ’F&¶W"F†âB&ævRÂ¢¤ÅÂ¢Sãv–ç7BS"ã~(	3Sbã2¢¢(	Bv†–6‚—0¢v‡’7VæF–ær—BÖGFW'2†W&RæBæ÷BB#SÒâF†Rf—‚66ÆW2Ç†'’"ãB–ç6–FRRÒÂfF–æp¢Fòæ÷F†–ær'’CÓ²WfW'’&æB7BF†RfFR—2Væ6†ævVBFòF†RFV6–ÖÂÂv†–6‚—2F†P¢&—F†ÖWF–2wV&çFVRæBÇ6òF†RÖV7W&VÖVçBâ&V6÷&FVB2¢¤Ã“‚¢¢à ¢¢¤æBöæRÆW76öâf÷"F†RvFW2Âv†–6‚—2F†RGW&&ÆR'Bâ¢¢&æBvFVBöâ¦†÷rÖç’&ö&W2vW&P¥4TTâ¢vFW2—G6VÆb÷WBBW†7FÇ’F†RÖöÖVçBF†RF†–ær—BÖV7W&W2vöW2w&öæs¢&öBæö&öG’6à§6VR&W÷'G2ãÓæB—2–æF—7F–æwV—6†&ÆRg&öÒ&öBF†B—2æ÷BF†W&RâF†R&æG2&Ræ÷rvFVBöà¦†÷rÖç’&ö&W2vW&R¢¥$ô¤T5DTB¢¢(	Böâ67&VVâæBF†W&Vf÷&R÷vVB–7GW&RâF†B—2F†RF†—&@§F–ÖRF†—2'Vr†2&VVâVW7F–öâöbv†BF†RvFRv2ö–çFVBBÂæB—B—2F†Rf—'7Bf—‚F†@¦Ö¶W2F†RvFRf–ÂÆ÷VFÇ’&F†W"F†âV–WFÇ’'7F–âà ¢¢¤öæRÖ÷&RF†–ærF†R÷VR72FVv‡BÂæB—B—2vFRÆW76öâFöòâ¢¢—G2f—'7Bf÷&ÒG&÷VBF†P§&–&&öâ–çFòF†R÷VRVWVRv—F†÷WBÆWGF–ær—Bw&—FRFWF‚Â6òF†RFW'&–â–çFVB&6²÷fW"—@¦æBF†R72&W÷'FVB¢£ã6V–Æ–ærVæFW"W&fV7FÇ’†VÇF‡’&öB¢¢â—Bw&—FW2FWF‚æ÷rÂÆ–¶P§F†RÖ&¶W"72—B6†÷VÆBÇv—2†fRÖ—'&÷&VBâF–væ÷7F–2F†BÆ–W2V–WFÇ’—2v÷'6RF†âæöæRÀ¦æBF†—2öæRÆ–VB–âF†RF—&V7F–öâöb&æ÷F†–ærFò6VR†W&R"(	BF†R6ÖRF—&V7F–öâ2WfW'—F†–ærVÇ6P¦–âF†—2'Vrw2†—7F÷'’à ¢¢¤æB6V6öæBfVÇBÂf÷VæB'’F†RæWr7FF–öâæBf—†VBv—F‚—Bâ¢¢BFW6·F÷Â(	3#SÒg&öÒF†P¦7&÷76–ærÂF†R&–&&öâ66÷&VB¢£ãÅÂ¢¢¢v—F‚F†RÖ&¶W"72g&öçFÖ÷7C¢"Ô%Ts"w2fVÇBv–âÂ—G0§öÇ–vöâöfg6WB†f–ær&VVâGVæVBVçF–ÂF†R&æG2¦BF†RGvò7FF–öç2F†VâvFVB¢76VBâFVWVæV@§FòF†RÖ&¶W"w2÷vâfÇVW2ÂF†B&æB&VG2¢£‚ãÅÂ¢BRW&6WF–&ÆR¢¢âF†RçVÖ&W"v2æWfW §w&öæs²F†R6×ÆR—Bv2GVæVBv–ç7Bv2à ¢¢¤æ÷BFöæR†W&RÂæBFVÆ–&W&FVÇ“¢¢¢F†RæV"&æB†2F†RÆV7B†VG&ööÒöbç’&æBvÆ¶W ¦7GVÆÇ’7FæG2–â(	B—G2÷VR6V–Æ–ær—2¢£2ãBÅÂ¢öâÖö&–ÆRæBBã2öâFW6·F÷¢¢Âv–ç7@£Rãž(	3bã’BF†R6ÖR7FF–öâw2C(	3ÒæBB&÷F‚W&–Â&æG2(	BæB¢£#RöbæV"&ö&W2öà¦Öö&–ÆRÂCRöâFW6·F÷Â6ææ÷B6ÆV"F†RW&6WF–&–Æ—G’F‡&W6†öÆBWfVâgVÆÇ’÷VR¢¢â6’—@§F†Bv’&F†W"F†â'F†RÆ÷vW7Böbç’&æB#¢BÆ¶UöÖ&¶WFF†Rc(	3CÒ&æBw26V–Æ–ær—0¦Æ÷vW"7F–ÆÂƒ2ã"Öö&–ÆR’Âv†–6‚—2&öBB¶–ÆöÖWG&RæBæ÷BF†RF†–ærF†—2&6VÂ—2&÷WBà¤Ã“‚æÖW2F†R†öæW7Bf—‚(	BFW‡GW&VB6÷fW&vRÂV'F‚æBw&72&W6öÇfVB2F6†W2BF†R66ÆR¦æV"—†VÂ6â6†÷rÂ6òF†RW–R–çFVw&FW2F†R&V6÷&FVBg&7F–öâ–ç7FVBöbF†R&ÆVæFW"&RÖÖ—†–æp¦—BâF†B&VÆöæw2Fò¢¥"Õs"¢¢‡FW‡GW&RF†RF÷vâ’Âv†–6‚—2v†W&RF†RãBFW‡GW&R66÷&RÆ—fW2à £ÆFWF–Ç3à£Ç7VÖÖ'“åF†R&6VÂ2÷VæVBÂ##bÓ‚ÓCÂ÷7VÖÖ'“à  ¥&W÷'FVB'’F†R÷væW"##bÓ‚ÓBÂöâÖö&–ÆRÂöâF†R¢¦FWb&Wf–Wr¢¢(	B6ò¢§v—F‚F†R"Ô%Ts"f—€¦Ç&VG’–â¢£¢7FæF–æröâg&æ¶Æ–â7G&VWB&ö6†–ær&æFöÇ‚ÂF†Rv†VVÂ'WG2&VB6ÆV&Ç’–à§F†RÖ–BÖF—7Fæ6RæB¢§F†R&öB—26–×Ç’æ÷BF†W&R–âF†RæV"f–VÆB¢¢â¢$—B6†÷VÆBæ÷B&P¦–çf—6–&ÆRv†Vâ’Ò7FæF–æröâ—Bâ"  ¢¢¥"Ô%Ts"—2v÷&¶–ærâF†—2—2F†R&æB—BæWfW"ÖV7W&VBâ¢¢—G2vFR—0¦$ôEô$äE2Òµ³CÂÒÂ³Â#SÒÂ³#SÂcÒÂ³cÂCÕÖ(	B¢§F†RæV&W7B&æB7F'G2@£CÖWG&W2â¢¢WfW'—F†–ærg&öÒF†RvÆ¶W"w2fVWB÷WBFòCÒv2÷WG6–FRF†R6×ÆRÂ6òF†R&ö@¦6÷VÆB&RW&fV7FÇ’–çf—6–&ÆRVæFW&fö÷Bv†–ÆRWfW'’vFVB&æB76VBB2ãn(	3Bã2éDÅÂ¢âF†P¦ÖV7W&VÖVçBv26÷VæBæBF†Rf—‚v2&VÃ²F†Rv–æF÷rv2w&öærà ¢¢¥F†B—2F†RÆW76öâv÷'F‚F¶–ærÂæB—B—2F†R6V6öæBF–ÖRöâF†—26ÖR'Vs¢¢¢F†Rf—'7BvFP¦ÖV7W&VBF†RvVöÖWG'’æBæWfW"6¶VBv†WF†W"F†R&öB&V6†VBF†R67&VVã²F†R6V6öæB6¶VBÂ'W@¦öæÇ’7BCÒâvFRç7vW'2W†7FÇ’F†RVW7F–öâ—Bv2ö–çFVBBà ¢¢¥5Ä•B”âEtò(	B6VR'F†R'Vâ'VFvWB—2SÖ–çWFW2"&÷fRâ6Æ–ÒôäRâ¢  ¢¢¥"Ô%Ts6(	BÆæBF†RæV"Öf–VÆB&æBÂ&VBâ¢¢W‡FVæB$ôEô$äE6v—F‚³"ÂCÖ&æB†&VÆ÷p§ã"ÒF†R7W&f6R—2VæFW"F†R6ÖW&æBFVvVæW&FR’â&öD6öçG&7B‚–Ç&VG’†2F†P¦Ö6†–æW'“¢F†R÷VRÖÖ&¶W"FVæöÖ–æF÷"¢¤Ò¢¢v÷&·2–FVçF–6ÆÇ’†W&RÂæB&öBö66ÇVFVB'¦w&727F—2–âF†R6×ÆRæB66÷&W22¦&öBF†B6÷fW'2—†VÂæBFöW2æ÷B6†ævR—B¢(	@¦W†7FÇ’F†R6–væGW&RvçFVBâ¢¤6öÖÖ—B—Bd”Ä”ärÂv—F‚F†RÖV7W&VBçVÖ&W'2V÷FVB¢¢ÂæB7F÷à¤öæR6Öö¶R72âF†Bf–ÇW&R—2F†—2†Æbw266WFæ6RÂæB6öÖÖ—GF–ær—B&Vf÷&Rç–öæR¶æ÷w0§v†–6‚6W6R—2wV–ÇG’—2v†B7F÷2F†Rf—‚&VFVf–æ–ær7V66W72à ¢¢¥"Ô%Ts6"(	BGW&â—Bw&VVââ¢¢F¶W2"Ô%Ts6w26öÖÖ—GFVBçVÖ&W'22F†R&6VÆ–æRæBv÷&·2F†P¦6æF–FFW2&VÆ÷râöæR6Öö¶R72â¢¤Fòæ÷B7F'BVçF–Â6†2ÆæFVBâ¢  ¢¢¤6æF–FFRÖV6†æ—6×2(	BÖV7W&R&Vf÷&R6†ö÷6–ærâ¢¢F†B–ç7G'V7F–öâ—2v†B6fVB"Ô%Ts"g&öÐ¦f—‚F†Bv÷VÆB†fRÖFRF†–æw2v÷'6RÂæB—BÆ–W2v–ã  £â¢¤æV"Öf–VÆB7v&Bö66ÇW6–öâÂæBF†—2—2F†R&–ÖR7W7V7Bâ¢¢BW–R†V–v‡BF†Rw&70¢æV&W7BF†R6ÖW&—2Væ÷&Ö÷W2–â67&VVâ76RæB7F6·2Â6òF†R&öB6â&R6ö×ÆWFVÇ¢†–FFVâv—F†–âfWrÖWG&W2WfVâB¦6÷'&V7B¢ÆçF–ærFVç6—G’âF†RW†—7F–ær6†V6²(	@¢7G&VWB6ÆV&–ær&VÖ÷fW2G&fVÂ×G&6²ÆçG2'WB&W6W'fW2F†R&Æö6¶(	B—2&ööÆVâöâöæP¢7G&VWBæBöæR&Æö6²â—B6ææ÷B6VRF†—2à£"â¢¥F†R6ÆV&–ær6÷'&–F÷"—2æ'&÷vW"F†âF†RG&vâG&6²¢¢Â6òF†R&–&&öâw2VFvW2&P¢ÆçFVB÷fW"WfVâv†W&RF†R6VçG&R—26ÆV"à£2â¢¤Ç†VæFW"Övæ–f–6F–öââ¢¢"Ô%Ts"&—6VBF†R&6VÆ–æW2FòãSBóã3‚óã#‚æBFFVB¢7V"×—†VÂfÆö÷"F†B§66ÆW2Ç†W¢&VÆ÷r"‚(	Bv†–6‚'’FW6–vâFöW2æ÷F†–ærW6Æ÷6RÀ¢v†W&RF†R&–&&öâ—2v–FW7Bâv÷&âG&6²Bã3‚6VVâF‡&÷Vv‚æV"Öf–VÆBw&72Ö’6–×Ç¢æ÷B&RVæ÷Vv‚à ¢¢¥F†RæöâÖÆ–6Væ6RÂæB—B—2&VÂ6öç7G&–çBâ¢¢Fò¢¦æ÷B¢¢f—‚F†—2'’6ÆV&–ærw&72&÷Væ@¦WfW'’&öBâV6‚6öÖ×Væ—G’w2w&÷VæB6÷fW"—2FF6WB6Æ–Òv—F‚—G2÷vâvFR(	B¢'F†R7v&B—0§ÆçFVBBV6‚6öÖ×Væ—G’w2÷vâ&V6÷&FVB6÷fW""¢(	BæBv–FVæ–ær6ÆV&–ær6÷'&–F÷"Fòv–â¦6öçG&7B66÷&Rv÷VÆB&RfÇ6–g––ær&V6÷&FVBf–wW&RFò72FW7Bâ–bF†R6÷'&–F÷"vVçV–æVÇ§6†÷VÆB&Rv–FW"ÂF†B—26†ævRFòF†R&V6÷&Bv—F‚—G2&V6öæ–ærÂæ÷BGVæ–ær6öç7FçBà ¢¢¤f–ÆW3¢¢¢FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6‡F†RæV"&æB’+r&VæFW&W'2÷vV"ö§2öfÆ÷&æ§6†6ÆV&–ær’+p¦&VæFW&W'2÷vV"ö§2÷7G&VWG2æ§6†Ç†’+rFö72ôÄ”$U%D”U2æÖF–b&V6÷&FVB6÷fW"÷"6÷'&–F÷"Ö÷fW0 ¢¢¤66WFæ6S¢¢¢F†RæV"&æBvFVBæBw&VVâB&÷F‚f–Ww÷'G2Âv—F‚F†RfVÇBWB&6²Fò&÷fP§F†R6†V6²æÖW2—C²WfW'’W†—7F–ær&öB&æB7F–ÆÂw&VVã²F†RW"Ö6öÖ×Væ—G’7v&B6÷fW"6†V6°§VçF÷V6†VBæB7F–ÆÂ76–ærâ¢¤Öö&–ÆR—2F†R&W÷'BæBÖö&–ÆR—2F†RvFR¢¢(	B3“9ssƒ—2v†W&P¦—Bv26VVâà £ÂöFWF–Ç3à ¢222"Ô%Ts62(	BF†RæV"w&÷VæB—2Ö—76–ærÂæB—B—2äõBF†R7G&VWG2+r¢¤DôäR##bÓ‚ÓR¢  ¢¢¥"Ô%Ts62Ö"—2DôäRƒ##bÓ‚ÓR’(	BäT•D„U"7W&f6RÖ÷fVBâF†RV&Æ—6‚7FWÖ÷fW2F†RÖW6€¤eDU"F†RöæÇ’vFRF†BÖV7W&W2—Bâ¢  ¢†’6¶VBv†–6‚öbF†RGvòv2w&öæræB&VgW6VBFòwVW72âF†Rç7vW"—2æV—F†W#¢F†RG&và¦w&÷VæBæBF†R6×ÆW"&R&÷F‚f—F†gVÂFòF†RFW'&–â7V2ÂæBF†RF—6w&VVÖVçB—0¦–çG&öGV6VB&WGvVVâF†RvVæW&F÷"æBF†R'&÷w6W"Â'’vÇFb×G&ç6f÷&Ò÷F–Ö—¦V–à¦FööÇ2ö&¶Rç6†à ¢¢¤ÖV7W&VBöâF†R6öÖÖ—GFVB'—FW2¢¢(	BFööÇ2öÖV7W&U÷FW'&–åöf—BæÖ§6ÂF†—&B&VFW"öbF†—0¦vVöÖWG'’Âv†–6‚FV6öFW2U…EöÖW6†÷Eö6ö×&W76–öææB´…%öÖW6…÷VçF—¦F–öæF†Rv’F†P§&VæFW&W"FöW2æB6ö×&W2fW'FW‚†V–v‡G2v–ç7BF†R6ÖR†V–v‡Ff–VÆBæ&–æF†RvÆ¶W"6×ÆW3  §ÂÖW6‚ÂÆGF–6RÂÖVâÂ&×2ÂÖ‚ÇÌéEÇÂÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Â76WG2övÇFbö¢¦Ö7FW"¢¢(	Bv†BF†RvVæW&F÷"vFW2ÂfÆöBÂ(‰#ãÖÒÂãBÖÒÂ¢£"ãRÖÒ¢¢À§Â76WG2÷vV"ö¢§6†—VB¢¢(	Bv†B'&÷w6W"ÆöG2Â¢£3bãBÖÒ¢¢ÂRãÖÒÂƒRãÖÒÂ¢£##rãbÖÒ¢¢À ¥F†RÖ7FW"†öæ÷W'2ÔU4…ôd•EõDôÄU$ä4UôÖFò¢£"ãRÖÒ¢¢Âv†–6‚—2F†R†V–v‡Ff–VÆBw2÷và§VçF—6F–öâW'&÷"(	B—B—22W†7B2F†Rf–VÆB—B—2'V–ÇBg&öÒâF†RFW&—fF—fRV&Æ—6†V@¦&W6–FR—B—2öfb'’WFò¢£##‚ÖÒ¢¢à ¢¢¥v‡’Â&V6—6VÇ’â¢¢vÇFb×G&ç6f÷&ÖVçF—6W2õ4•D”ôâFò¢¦&—BFWF‚(	BB'’FVfVÇB¢¢(	@§VæFW"ôäRTä”dõ$ÒæöFR66ÆRÂæB7F÷&W2F†R&W7VÇB–âF†RæW‡B–çFVvW"G—RWÂ6òF†RÆ÷p§Gvò&—G2&RÇv—2¦W&òâF†RVæ–f÷&Ò66ÆR—26WB'’F†Rv–FW7B†—2âF†—2ÖW6‚—0¢¢£RÃ#Òv–FR¢¢†"Ã#Ò&÷‚ÇW24´•%EôÔ$t”åôÖÒãR¶Òöb&öâöâV6‚6–FR’æ@¢¢£‚ãbÒFÆÂ¢¢Ââ7V7B&F–òöbSƒ£Â6òF†RfW'F–6Â'Vær76–ær—0¦S#òc3ƒ6Ò¢£3bÖÒ¢¢âF†R6¶—'B(	Bv†÷6RVçF—&R¦ö"—2Fò6''’F†R6†ææVÂ7BF†P¦&÷‚VFvR(	B—2v†B6WG2F†R&V6—6–öâöbF†Rw&÷VæBF†RF÷vâ7FæG2öâà ¢¢¤æBæò6WGF–ærf—†W2—BÂv†–6‚—2F†R'BF†BFV6–FW2F†R6†RöbF†Rf—‚â¢¢ÖV7W&VBÂæ÷@¦&wVVC¢Ò×VçF—¦R×÷6—F–öâfÂF†RÖ†–×VÒF†Rf÷&ÖBöffW'2ÂÆæG2öâ¢£sbãbÖÒ¢¢ÆGF–6P¢‡&×2#"ãÖÒÂÖ‚SBãBÖÒ’(	B7F–ÆÂ÷fW"F†R3ÖÒF†RvVæW&F÷"&VgW6W2FòW‡÷'B7Bà¦ÒÖÖW6†÷BÖÆWfVÂÖVF—VÖVçF—6W2–FVçF–6ÆÇ’æB6÷7G2cb´"Ö÷&RâöæÇ’ÒÖ6ö×&W72fÇ6V ¦ÖVWG2F†RFöÆW&æ6RÂB¢£bãCRÔ"v–ç7Bcƒ‚´"¢¢à ¢¢¥6òF†R&VæFW&W"&VG2F†R†V–v‡G2&6²öfbF†Rf–VÆBBÆöB¢¢(	@¦6öæf÷&Ôw&÷VæEFôf–VÆB‚––â§2÷FW'&–âæ§6âæ÷B6÷'&V7F–öâf7F÷"æBW‡Æ–6—FÇ’æ÷BF†P¦Ä”eEôÖgVFvR†’f÷&&FS¢F†R†V–v‡Ff–VÆB—2¦Ç&VG’¢F†RWF†÷&—G’f÷"6öÆÆ—6–öâÂ'V–ÆF–æp¦æ6†÷&–ærÂfÆ÷&&ö÷G2æB7G&VWBG&RÂ6òF†—2Ö¶W2F†R7W&f6Rf—6—F÷"4TU2F†R6ÖP§7W&f6R2F†RöæRF†RF÷vâ—2Æ6VBöâÂ'’6öç7G'V7F–öâ&F†W"F†â'’FöÆW&æ6RâF†RtÄ ¦¶VW2F†R¦ö'2F†Rf–VÆB6ææ÷BFò(	BF†RFV6–ÖFVBF÷öÆöw’ÂF†Ræ÷&ÖÇ2ÂF†Rô4ôäd”DTä4V ¦6†ææVÂâÆÂ¢£#BÃC¢¢fW'F–6W2Ö÷fRÂ'’WFò¢£##rãbÖÒ¢¢ÂæBF†R&W6–GVÂgFW'v&G2—0¢¢£ã#B+VÒ¢¢Âv†–6‚—2fÆöC3"7F÷&vRæBæ÷F†–ærVÇ6Rà ¥F†R6¶—'B—26'&–VB&F†W"F†âfÆGFVæVC¢—BÆ–W2÷WG6–FRF†R&÷‚Âv†W&R6×ÆR‚–&WGW&ç0¦—G2¢¦fÆÆ&6²öb¢¢–ç7FVBöb6Æ×–ærÂ6ò6æ–ær—Bæ—fVÇ’v÷VÆB†fRG&÷VBãR¶Òö`¦&öâöçFòF†RvFW"ÆæRâ6×Æ–ærBF†R6Æ×VB÷6—F–öâ&W&öGV6W2F†RvVæW&F÷"w2÷và§'VÆRf÷"F†R6¶—'B(	B&6''’V6‚&÷VæF'’fW'FW‚÷WGv&BÂ¶VW–ær—G2÷vâ†V–v‡B"(	BæBF†P§6VÒBF†R&÷‚VFvR6Æ÷6W2W†7FÇ’à ¢¢¥F‡&VRvFW2Ö—76VBF†—2ÂæBF†R&V6öâF†W’ÆÂÖ—76VB—B—2F†R6ÖRâ¢¢F†Ræ÷&ÖÇ2vFRÀ§F†R&öBÖ6öçG&7BvFRæBF†R†÷&—¦öâvFRV6‚6ö×&RF†R&VæFW"Fòæ÷F†W"&VæFW"â§VçF—6VBw&÷VæB—2¦6÷'&V7BÖÆöö¶–ær¢w&÷VæC²—B—2öæÇ’w&öær&VÆF—fRFòÖV7W&VÖVç@¦æöæRöbF†VÒ†VÆBâGvòæWrvFW2†öÆB—C  ¢Ò¢¦FööÇ2ö6†V6²ç6†¢¢(	B76W'G2F†R6öÖÖ—GFVBÔ5DU"7F–ÆÂÖVWG2ÔU4…ôd•EõDôÄU$ä4UôÖæ@¢$Uõ%E2F†RFW&—fF—fRw2G&–gBâæ÷F†–ær&RÖ6†V6¶VBF†RÖ7FW"gFW"F†R&¶RÂ&V6W6RF†P¢vVæW&F÷"w2÷vâ&VgW6Â†Vç2–ç6–FR&ÆVæFW"'VâF†—2vFR6ææ÷BÖ¶S²†æBÖVF—FVBtÄ ¢v÷VÆB†fR6–ÆVBF‡&÷Vv‚WfW'’6†V6²–âF†—2&WòâF†RFW&—fF—fR—2&W÷'FVBæB¢¦æ÷B¢ ¢76W'FVBÂ&V6W6R—B6ææ÷B72æB6––ær6òv÷VÆBöæÇ’76W'BF†B6ö×&W76÷"—2¢6ö×&W76÷"à¢Ò¢¦FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6¢¢(	B76W'G2F†R7W&f6R7GVÆÇ’E$tâÂBF†RF–ÆW2r÷và¢fW'F–6W2gFW"WfW'’ÆöB7FWÂv–ç7BF†R6×ÆW"F†RF÷vâ—2Æ6VBv—F‚âF†B—2F†P¢6ö×&—6öâæöæRöbF†RF‡&VRÖFRâw&VVâB¢¦&÷F‚¢¢f–Ww÷'G2à ¢¢¥v†B—2äõB&W—&VBÂæB—2VW7F–öâ&F†W"F†âFVfV7Bâ¢¢F†R6ÖRVçF—6W"Ö÷fW2Ræ@¤â'’WFò¢£S2ÖÒ¢¢Âv†–6‚—2–çf—6–&ÆRöâFV6–ÖFVB&—&–RæB—2v‡’öæÇ’’—2&VB&6²à¥v†WF†W"F†RFW'&–â6†÷VÆB6†—VçF—6VBBÆÂ(	Bcƒ‚´"v—F‚ÆGF–6RÂv–ç7BbãCRÔ ¦W†7B(	B—2–ÆöBFV6—6–öâv—F‚â÷væW"Öf6–ær6÷7BÂ6ò—B—2¢¥"Õsb¢¢&VÆ÷r&F†W"F†à§6öÖWF†–ærF†—2&6VÂ6WGFÆVBöâ—G2÷vââF†Rf—‚†W&RÖ¶W2F†Bç7vW"7F÷ÖGFW&–ærf÷"F†P¦w&÷VæBf—6—F÷"7FæG2öâà ¢¢¥F†RvFRÆW76öâÂf÷"F†Rf÷W'F‚F–ÖRöâF†—2'Vs¢Fòæ÷BÖV7W&RF†Rf–ÆR–÷R'V–ÇBâÖV7W&P§F†Rf–ÆR–÷R6†—â¢  ¢¢¥F†R÷væW"&W&öGV6VB"Ô%Ts2öâF†R'&æ6‚F†Bf—†W2—B¢¢ÂöâÖö&–ÆRÂöâÆ¶R7G&VWB&ö6†–æp¤g&æ¶Æ–â(	BF†R6ÖR6ö×Æ–çBÂgFW"F†R&6VÂ&VÆ÷rFV6Æ&VB—B6öÇfVBâ&W&öGV6VB†W&RBF†@¦W†7B÷6R†vÆ¶W"çFVÆW÷'FFòF†R6öÖÖ—GFVBÆ¶R‚g&æ¶Æ–â–çFW'6V7F–öâÂS"ãBÒ&6²Âf6–æp¤Æ¶Rw2÷vâ6VçG&VÆ–æR&V&–ærÂ3“ƒsƒ’âf–æF–æw2ÂÆÂÖV7W&VBÂæöæR–æfW'&VC  £â¢¤—B—2æ÷BF†RÇ†ÂæBæòÇ†6â&V6‚—Bâ¢¢v—F‚F†R7G&VWG2f÷&6VBgVÆÇ’õTRÀ¢FWF‚×w&—F–ærÂBF†RÖ&¶W"72w2÷vâöÇ–vöâöfg6WB(	Bæ÷F†–ær&ÆRFò†–FRF†VÒ(	BF†R&–&&öà¢7F–ÆÂ&V6†W2öæÇ’¢§&÷r“3röbSc¢¢âF†R&÷GFöÒ¢£CRöbF†Rg&ÖR6öçF–ç2æò&öGv’@¢ç’÷6—G’¢¢â"Ô%Ts2w2äT%ôt”æ—266Æ–ærF†RÇ†öbg&vÖVçG2F†B&Ræ÷BG&vâà£"â¢¤—B—2æ÷B7G&VWG2'Vrâ¢¢W"×&÷r†–v‚Ög&WVVæ7’VæW&w’7&÷72F†R6ÖRg&ÖR6öÆÆ6W2g&öÐ¢¢£ãÓ"ãB&÷fR&÷rFòã"&VÆ÷r&÷r#¢¢(	BRÓ‚G&÷â&VÆ÷rF†BÆ–æRF†W&R—2æð¢&öBÂ¢¦æòw&72GVgG2æBæòw&÷VæBFW‡GW&RBÆÂ¢£¢6Öö÷F‚w&VVâv6‚âWfW'—F†–ærF†@¢6—G2öâF†Rw&÷VæBfæ—6†W2FövWF†W"ÂBöæR&F—W2Âv†–6‚—2v‡’F†RVFvR—26ÆVà¢†÷&—¦öçFÂÆ–æR(	B6öç7FçBF—7Fæ6Rg&öÒF†R6ÖW&à£2â¢¥F†RvVöÖWG'’W†—7G2â¢¢5DUôÒÒ"ã#VÂÄ”eEôÒÒã#&ÂæB¢£3"7G&VWBfW'F–6W2Æ–Rv—F†–à¢ÒöbF†R6ÖW&¢¢BF†—2÷6Râ6öÖWF†–ær—2'W'––ærF†VÓ²F†W’&Ræ÷B'6VçBà¢„f—'7B&ö&R&W÷'FVB&æòfW'FW‚v—F†–âãRÒöbF†R6VçG&VÆ–æR"(	BF†Bv2F†R$ô$Rw0¢W'&÷"Âæ÷Bf–æF–æs¢&–&&öâVBw2f÷W"6÷&æW'2&RÆÂB²òÒ†ÆbF†RG&6²v–GF‚Â6ð¢F†W&R&RæWfW"fW'F–6W2ôâF†R6VçG&VÆ–æRâFòæ÷B&WVB—Bâ ¢¢¥5UU%4TDTBôâÔT4„ä•4Ò'’3CRÂ##bÓ‚ÓR(	B&VBF†Bf—'7Bâ¢¢F†RÖV7W&VÖVçG2&VÆ÷r7FæBæ@§&W&öGV6S²F†R4ôä4ÅU4”ôâG&vâg&öÒF†VÒÂF†BF†RGvò&RvF–ffW&VçBFFrÂv2w&öær&÷WBv‡’à¢3CRf÷VæBF†R6W6S¢¢§F†RV&Æ—6‚7FWVçF—6W2F†RÖW6‚gFW"F†RöæÇ’vFRF†BÖV7W&W2—B¢¢Â6ð¦æV—F†W"w&÷VæBÖ÷fVBâ&÷F‚ÖV7W&VÖVçG2†W&RvW&RF¶Vâv–ç7BF†RT$Ä•4„TBÖ—'&÷"(	Bv†–6‚—2F†P§&–v‡BF&vWBf÷"f—6—F÷"Öf6–ær'VræBF†Rw&öæröæRf÷"6¶–ærv†–6‚6÷W&6R7W&f6R—0¦WF†÷&—FF—fRÂ&V6W6RF†RV&Æ—6†VB6÷’—2æ÷BF†R7W&f6RV—F†W"vVæW&F÷"VÖ—GFVBâF†R7&VBö`¬+2Ò—2F†RVçF—6F–öâw&–BÂæ÷BF—6w&VVÖVçB&WGvVVâF†RtÄ"æB†V–v‡Ff–VÆBæ&–æà ¢¢¥D„R…•õD„U4•2•24ôäd•$ÔTBÂäB•B•2tõ%4RD„â5DDTB(	BÖV7W&VB##bÓ‚ÓRâ¢  ¥F†Rw&÷VæBF†B—2E$tâ—2æ÷BF†Rw&÷VæBF†BF†–æw2&RÄ4TBöâÂæBF†Rv—2â÷&FW"ö`¦Övæ—GVFRÆ&vW"F†âF†R&öBw2÷vâÆ–gBâÖV7W&VBBF†R÷væW"w2÷6R'’f–æF–ærÂf÷"V6‚6×ÆP§ö–çBÂF†R7GVÂG&–ævÆRöbF†Rw&÷VæBÖW6‚&÷fR—BæB–çFW'öÆF–ær—G2†V–v‡B(	Bæò&–67FW"À¦æò77V×F–öâ&÷WB†÷rF†RÖW6‚—2'V–ÇC  §ÂB†Ò’Â7W&f6T†V–v‡B‚–ÂG&vâw&÷VæBÂG&vâ(‰"6×ÆVBÂ&öBÆ6VBBÂ'W&–VBÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Â"ÂãssRÂ¢£ã“b¢¢Â¢¢³ã3¢¢Âãs“rÂ–W2À§ÂÂãsƒÂã“bÂ³ã#RÂãƒ2Â–W2À§Â#RÂãs“Âã“bÂ³ãbÂãƒ"Â–W2À§ÂSÂãƒRÂã“bÂ³ãÂãƒ#rÂ–W2À§ÂÂãƒÂã“bÂ³ã“bÂãƒ3"Â–W2À ¢¢¥F†RG&vâw&÷VæB6—G2’ãn(	32ã6Ò$õdRF†R6×ÆW"Â÷fW"F†Rv†öÆR‡VæG&VBÖWG&W2â¢¢Ä”eEôÖ—0¢¢£#"ÖÒ¢¢âF†R&öB—2VæFW"F†Rf—6–&ÆRw&÷VæBÆöær—G2VçF—&RÆVæwF‚†W&RæBæWfW"†B6†æ6S°§6ò—2WfW'’ÆçB&ö÷FVB'’F†R6ÖR6×ÆW"Âv†–6‚—2v‡’F†Rw&72GVgG2fæ—6‚v—F‚—Bà ¢¢¥F†Vâv‡’—2F†R&öBf—6–&ÆR&W–öæBãrÒBÆÃò¢¢&V6W6RF†RöÇ–vöâöfg6WBv–ç2B&ævRæ@¦Æ÷6W2W6Æ÷6S¢FWF‚Ö'VffW"&W6öÇWF–öâ—2f–æW7BæV"F†R6ÖW&Â6òf—†VBã"6Ò'W&–Â—0¦FV6—6—fVÇ’&W6öÇf&ÆRBRÒæB7v×VB'’F†Röfg6WBBSÒâF†R7&÷76÷fW"FWVæG2öâF—7Fæ6P¦ÆöæR(	Bv†–6‚—2W†7FÇ’v‡’F†RVFvR—26ÆVâ†÷&—¦öçFÂÆ–æRB6öç7FçB&F—W2ÂF†RöæP¦fVGW&RöbF†R67&VVç6†÷G2æò÷F†W"W‡ÆæF–öâ66÷VçFVBf÷"à ¢¢¥F†RvÆ¶W"—2–ç6–FRF†R†–ÆÂâ¢¢W–R—2B"ãCSRv—F‚F†R6×ÆW"BãssR(	Bãc‚ÒöbW–R†V–v‡BÀ¦2&V6÷&FVB(	B'WBF†RG&vâw&÷VæBVæFW"F†B6ÖRö–çB—2ã“bÂ6òf—6—F÷"7FæG2¢£26Ò7Væ°¦–çFòF†RFW'&–âF†W’6â6VR¢¢â6öÆÆ—6–öâÂ'V–ÆF–æræ6†÷&–ærÂfÆ÷&&ö÷G2æB7G&VWBG&RÆÂW6P§F†R6×ÆW"Â6òF†—2—2æ÷BöæÇ’&öB'Vs¢¢¦WfW'—F†–ær–âF†RF÷vâ—2æ6†÷&VBFò7W&f6RF†@¦—2æ÷BF†RöæRöâ67&VVââ¢  ¢¢¥v†B†2äõB&VVâW7F&Æ—6†VBÂæB×W7B&R&Vf÷&Rç—F†–ær—26†ævVBâ¢¢v†–6‚öbF†RGvò—0§w&öærâF†RG&vâÖW6‚—2&¶VBtÄ#²F†R6×ÆW"&VG2†V–v‡Ff–VÆBæ&–æ²&÷F‚FW66VæBg&öÒF†P§6ÖRFW'&–â7V2ÂæBF†—2ÖV7W&VÖVçB6—2öæÇ’F†BF†W’F—6w&VRÂæ÷Bv†–6‚öæRÖ÷fVBâFòæ÷@¢&f—‚"F†—2'’&—6–ærÄ”eEôÖ(	BF†B†–FW226ÒFGVÒF—6w&VVÖVçB&V†–æBgVFvRæBÆVfW0¦'V–ÆF–æw2æB6öÆÆ—6–öâ7F–ÆÂw&öærâf–æB÷WBv‡’F†RGvòF—6w&VRà ¢¢¥F†R÷&–v–æÂ‡—÷F†W6—2Â2w&—GFVâ&Vf÷&RF†RÖV7W&VÖVçC¢¢  ¢¢¥F†R‡—÷F†W6—2FòFW7Bd•%5BÂæB—B—2öæÇ’‡—÷F†W6—2â¢¢&öG2æBfÆ÷&&R&÷F‚Ä4T@§v—F‚FW'&–âç7W&f6T†V–v‡B‚–â–bF†RFW'&–âF†B—2E$tâ6—G2&÷fRF†B6×ÆW"æV"F†P¦6ÖW&Â&÷F‚&R'W&–VB'’F†R6ÖRfWr6VçF–ÖWG&W2BF†R6ÖR&F—W2(	Bv†–6‚—2F†R7–×FöÐ¦W†7FÇ’â—Bv÷VÆBÇ6òf—B¢¥"Ô%Ts¢¢‡F†R&—fW"VFvRfÆ–6¶W&–ærv†VâfÇ––ær’âÖV7W&RF†RG&và§FW'&–â7W&f6Rv–ç7B7W&f6T†V–v‡B‚–&Vf÷&R6†æv–ærç—F†–ærà ¢¢¤æBF†RvFRÆW76öâÂf÷"F†RF†—&BF–ÖRöâF†—2öæR'Vrâ¢¢"Ô%Ts2FFVB7FF–öâF†B7FæG0¢¦B¢F†RÆ¶RôÖ&¶WB7&÷76–ær(	BöæRöbF†RfWrÆ6W2F†RæV"w&÷VæB—2–çF7B(	BæB—BvVç@¦w&VVââF†R÷væW"v2s"gB6†÷'Böbâ–çFW'6V7F–öââ7FF–öâB7&÷76–ær6ææ÷B7V²f÷"F†P¦&Æö6²&WGvVVâ7&÷76–æw2âFBÖ–BÖ&Æö6²7FF–öâöâfö÷B&Vf÷&R6Æ–Ö–ærF†—26Æ÷6VBà ¢¢¤Fòæ÷B&RÖFV6Æ&RF†—2FöæRg&öÒ76–ærvFRâ¢¢6†ö÷BF†Rg&ÖRæBÆöö²B—Bà ¢222"Õsb(	B6†÷VÆBF†RFW'&–â6†—VçF—6VBBÆÃò+r¢¤DôäR##bÓ‚Ób+r÷VæVB'’"Ô%Ts62¢  ¢¢¥”U2ÂBb$•E2(	BæBF†R'FVf7Bv2äõB–çf—6–&ÆRÂv†–6‚—2F†Rf–æF–ærâ¢¢F†—2&6VÂv0§w&—GFVâW‡V7F–ærFò6öæf—&ÒF†BF†R†÷&—¦öçFÂF—7Æ6VÖVçB6ææ÷B&R6VVâæBFò&—6RF†R&—@¦FWF‚&V6W6R—B—2g&VRâF†R6V6öæB†Æb7FæG3²F†Rf—'7B—2w&öærâÖV7W&VBöâF†R'—FW2F†@§6†—ÂF†RBÖ&—Bw&÷VæB7FæG2¢§WFòCbã2ÖÒ&÷fRF†Rf–VÆBF†RF÷vâ—2Æ6VBöâ¢¢Â7BF†P¢¢£#"ÖÒ¢¢&öBÆ–gBB¢£ƒr¢¢öbF†Rf–VÆBw2#S’Ãcƒ’6×ÆRö–çG2ÂCBöbF†VÒöâG'’w&÷VæB(	@¢¢¦æBF†R6Æ÷6W7BöbF†÷6R7FæG2ã’Òg&öÒF†R6VçG&VÆ–æRöb6÷WF‚vFW"7G&VWB¢¢Â–ç6–FR£ãRÒG&fVÆÆVBG&6²Â3ã"ÖÒ÷fW"&öBF†B—2Æ–gFVB#"ÖÒâF†B—2"Ô%Ts62w2÷vâf–ÇW&P¦ÖöFRÂöâF†R7G&VWBF†R÷væW"&W÷'FVB—Bg&öÒÂ7W'f—f–ærF†Rf—‚BóRF†R6—¦RæBã2Rö`§F†RF÷vââFööÇ2öÖV7W&U÷FW'&–åö†÷&—¦öçFÂæÖ§6—2F†RæWr&VFW#²ÒÖÖW6‚bævÆ#ÖÆ&VÆ&–6W0¦ç’6æF–FFRFW&—fF—fRv–ç7BF†R6ÖR6öÇVÖç2à ¢¢¥F†RG&FR—2æ÷BF†RöæRF†R&÷‚&VÆ÷rFW67&–&W2Â&V6W6Rb&—G2—2æV&Ç’g&VRæBæV&Ç¦W†7Bâ¢¢WfW'’&÷rÖV7W&VBv—F‚F†R6ÖRvÇFb×G&ç6f÷&ÖF†R&¶R'Vç2ÂöâF†R6öÖÖ—GFV@¦Ö7FW"ÂæBF†RBÖ&—B&V'V–ÆB6ÖR&6²¢¦'—FRÖf÷"Ö'—FR–FVçF–6ÂFòF†Rf–ÆR–à¦76WG2÷vV"ö¢¢(	B6òF†W6R&RF†R6†—–ærçVÖ&W'2Âæ÷B6–×VÆF–öâöbF†VÓ  §ÂVæ6öF–ærÂ´"ÂfW'F–6ÂÆGF–6RÂÇÌéG•ÇÂ†æFVBFòF†R'&÷w6W"ÂÆâF—7Æ6VÖVçBÂ¢¦G&vâ7W&f6Rg2F†Rf–VÆBÂgFW"6öæf÷&Ö–ær¢¢Â7BF†R#"ÖÒÆ–gBÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§ÂÖ7FW"†76WG2övÇFbö’Âc#“bÂfÆöBÂ"ãRÖÒÂ(	BÂã2&×2ò2ã‚“’ò¢£rãrÖ‚¢¢Â(	BÀ§Â¢§6†—VBFöF’ÂBÖ&—B¢¢Â¢£cs¢¢Â3bãBÖÒÂ##rãbÖÒÂ¢£#s2ãÖÒ¢¢Â"ãòrã’ò¢£Cbã2¢¢Â¢£ƒr¢¢ƒCBG'’’À§ÂRÖ&—BÂcsrÂS2ã"ÖÒÂrãÖÒÂ3ãÖÒÂãRòBãRò¢£#"ãB¢¢ÂÀ§Â¢£bÖ&—B(	BD´Tâ¢¢Â¢£cs"¢¢ÂsbãbÖÒÂSBãBÖÒÂS"ãÖÒÂãBò2ã‚ò¢£"ã’¢¢Â¢£¢¢À§Âæò6ö×&W76–öâÂc#“bÂfÆöBÂ"ãRÖÒÂãÖÒÂã2ò2ã‚ò¢£rãr¢¢ÂÀ ¤f÷W"F†–æw2–âF†BF&ÆR&Rv÷'F‚Ö÷&RF†âF†RFV6—6–öã  ¢Ò¢¥F†RÆ7B6öÇVÖâ—2ÖV7W&VBBÆÂ#S’Ãcƒ’öbF†Rf–VÆBw2÷vâ6×ÆRö–çG2ÂgFW ¢6öæf÷&Ôw&÷VæEFôf–VÆB‚–¢¢(	BF†R7W&f6Rf—6—F÷"—27GVÆÇ’6†÷vâÂ&VB'’–çFW'öÆF–æp¢F†R6öçF–æ–ærG&–ævÆR–âÆâF†Rv’&7FW&—6W"FöW2âæ÷BBF‡&VR6ÖW&æ6†÷'3¢à¢æ6†÷"6WB6ææ÷Bç7vW"VW7F–öâ&÷WBãb¶Ü+"öbw&÷VæBÂæB"Ô%Ts2w2÷vâvFRvVçBw&VVà¢7FæF–ærs"gBg&öÒF†RfVÇBà¢Ò¢¥F†RÖ7FW"w2ã2ÖÒ&×2òrãrÖÒÖ‚—2DT4”ÔD”ôâÂæBWfW'’&÷r6'&–W2—Bâ¢¢6òF†P¢Væ6ö×&W76VBf–ÆR'W—2"ã’ÖÒ(i"rãrÖÒf÷"¢£Rã‚Ô"¢¢ÂæBv†B—2ÆVgBgFW"F†B—2æ÷BF†P¢6ö×&W76÷"w2Fòv—fR&6²âF†B—2F†Rv†öÆRç7vW"Fò'6†÷VÆB—B6†—VçF—6VBBÆÂ"à¢Ò¢¥F†RÖV6†æ—6Ò—26Æ÷RÂæ÷B6—¦Râ¢¢fW'FW‚6öæf÷&ÖVBBF—7Æ6VB÷6—F–öâ†öÆG2F†P¢f–VÆBw2†V–v‡Bf÷"F†Rw&öærÆ6RÂ6òF†R6÷7B—2‡6Æ÷R9rF—7Æ6VÖVçB“¢F†Rƒr÷fW"Ö'VFvW@¢6×ÆW26—BB¢¦ÖVF–â6Æ÷Röb‚R¢¢(	B&æ²f6W2ÂF†R6æB&–FvW2ÂF†R†&&÷W"7WB(	@¢æBfÆBÆGFVB&—&–R6ææ÷B6†÷rF†—2'FVf7BBç’&—BFWF‚à¢Ò¢¥"Ô%Ts62w2$RæBâÖ÷fR'’WFòS2ÖÒ"v2&—F†ÖWF–2(	B†ÆböbF†R3bãBÖÒ'Vær(	Bæ@¢F†RÖV7W&VBf–wW&R—2Æ&vW"¢£¢#2ãbÖÒV7BÂƒ"ãÖÒæ÷'F‚Â¢£#s2ãÖÒ–âÆâ¢¢âV÷FRF†P¢ÖV7W&VBöæRâ„—G2bÖ&—B&÷r&W&öGV6W2W†7FÇ“¢SBãBÖÒâ ¢¢¥&V6—6–öâ—2W"ÖÖW6‚ÂæBöæÇ’GvòÖW6†W2–âF†—2F÷vâ&R&–rVæ÷Vv‚Fò6&Râ¢ ¦vÇFb×G&ç6f÷&ÖVçF—6W2õ4•D”ôâVæFW"öæRVæ–f÷&ÒæöFR66ÆR6WB'’F†RÖW6‚w2õtâ&÷VæF–æp¦&÷‚Â6òâ76WBw2ÆGF–6R—2—G2v–FW7B†—2÷fW"%æ&—G2(	Bæ÷F†–ærFòFòv—F‚†÷rf–æR—G0¦FWF–Ç2&Râ7&÷72F†R#CBFW&—fF—fW2F†B6†—VçF—6VC¢vFW%õöSƒ3Eö†&&÷%ö7WF33ã‚ÖÒÀ¦FW'&–åõöSƒ3Eö†&&÷%ö7WF3bãBÖÒÂæ÷'F…÷–W&bã‚ÖÒÂæB¢¦WfW'’÷F†W"76WB(šBBã‚ÖÒÀ¦ÖVF–âãRÖÒ¢¢â6òF†R&—BFWF‚—2&—6VBöâF†RWö6‚ÖW6†W2æBÆVgBÆöæRWfW'—v†W&RVÇ6S ¢¢¢³Ãb'—FW2¢¢Âv–ç7B¢¢³Rãr´"‚³"ãBR’¢¢ÖV7W&VBf÷"b&—G27&÷72F†Rv†öÆR–ÆöBFð¦'W’æ÷F†–ærç—F†–ær6â6VRâUô4…õTåEô$•E6ò54UEõTåEô$•E6–âFööÇ2ö&¶Rç6†à ¢¢¥Gvò6ÖÆÆW"ÖV7W&VBf7G2Â&V6÷&FVB6òæö&öG’&RÖFW&—fW2F†VÓ¢¢¢R&—G2—2$”ttU"F†â`¢ƒc“2ãB´"v–ç7Bcƒ‚ã2’(	BFòæ÷B&÷F–Ö—6R"Fò—C²æBF†RvFW"ÖW6‚—2f÷W"fW'F–6W2@¦W†7FÇ’’ÒÂv†–6‚ÆæG2öâF†RÆGF–6RBWfW'’&—BFWF‚Â6ò—G233ã‚ÖÒ'VæræWfW"†@¦ç—F†–ærFò7ö–ÂæB—G2FW&—fF—fR—2'—FRÖ–FVçF–6ÂV—F†W"v’à ¢¢¥F†R6¶—'B7Æ—B—2äõBF¶VâÂæBF†B—2æ÷rÖV7W&VÖVçB&F†W"F†âFVfW'&Ââ¢¢F†R–FV¦&VÆ÷r—26÷VæB(	BãR¶Òöb&öâöâV6‚6–FR—2v†B6WG2F†RVçF—6F–öâföÇVÖR(	B'WBB`¦&—G2WfW'’öæRöbF†R#S’Ãcƒ’6×ÆW2—2Ç&VG’–ç6–FRF†RF–v‡FW7B'VFvWBF†—2F÷vâ†2Â6ð§7Æ—GF–ærF†R6¶—'Bv÷VÆB'W’&V6—6–öâæ÷F†–ær—2v—F–æröâÂBF†R6÷7BöbvVæW&F÷"6†ævRÀ¦Fö72ôtÄ"Ô4ôåE$5BæÖFÖVæFÖVçBæB&¶Râ&V÷Vâ—B–bgWGW&RWö6‚w2&÷‚w&÷w2÷"F†P¦w&÷VæBvWG2F–v‡FW"6öç7VÖW"F†âF†R&öBÆ–gBà ¢¢¥v†B—2äõBfW&–f–VB†W&S¢¢¢F†RFW6·F÷†ÆböbFööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6‡F†RFVâÖÖ–çWFP§W"Ö6öÖÖæB6V–Æ–ær(	B6VR'F†R'Vâ'VFvWB"&÷fR’âF†R¢¦Öö&–ÆR¢¢†Æbv2'Vâv–ç7B§V&Æ—6†VBÖ—'&÷"6''––ærF†RbÖ&—Bw&÷VæC¢¢£#‚76VBÂf–ÆVBÂ¦W&òvRW'&÷'2¢¢À¦–æ6ÇVF–ærF†RG&vâ×7W&f6RÖv–ç7B×F†R×6×ÆW"76W'F–öâ"Ô%Ts62FFVBâ¢¤æòtÄ"—26öÖÖ—GFVB'§F†—2&6VÂ¢¢(	B76WG2÷vV"ö—2F†R&¶Rw2Fòw&—FRÂæBF†Rw&÷VæB&V6†W2F†R6—FRv—F‚F†P¦æW‡Bæ–v‡FÇ’6†–6vòÓFBÖ&¶Rç–ÖÆâVçF–Â—BFöW2ÂF†R6†—VBw&÷VæB—2F†RBÖ&—BöæRF†—2&÷€¦ÖV7W&W2à ¢¢¤f–ÆW3¢¢¢FööÇ2ö&¶Rç6†‡F†RGvò×7FvR÷F–Ö—¦R²ÖW6†÷B72ÂæBF†RW"ÖÖW6‚&—BFWF‚’+p¦FööÇ2öÖV7W&U÷FW'&–åö†÷&—¦öçFÂæÖ§6†æWr’+rFööÇ2öÖV7W&U÷FW'&–åöf—BæÖ§6†W‡÷'G2—G0§&VFW"&F†W"F†âw&÷v–ærf÷W'F‚öæR’+rFö72õ$TäDU$”äræÖF+rFö72õ5DEU2æÖF  ¢ÒÒÐ ¢¢¥F†R&6VÂ2w&—GFVâÂf÷"F†R&V6÷&C¢¢  ¥"Ô%Ts62f÷VæBF†BF†RV&Æ—6†VBw&÷VæBÖW6‚ÆæG2öâ¢£3bÖÒ¢¢fW'F–6ÂÆGF–6RæBf—†V@§F†R6öç6WVVæ6R&F†W"F†âF†R6W6S¢F†R&VæFW&W"&VG2F†R†V–v‡G2&6²öfbF†R†V–v‡Ff–VÆBÀ§6òF†Rw&÷VæBf—6—F÷"7FæG2öâ—26÷'&V7Bv†FWfW"F†R6ö×&W76÷"FöW2âF†—2&6VÂ6·0§v†WF†W"F†R6W6R—2v÷'F‚&VÖ÷f–ærà ¢¢¥F†RçVÖ&W'2&RÇ&VG’ÖV7W&VB¢¢(	B6VR"Ô%Ts62w2F&ÆRæ@¦FööÇ2öÖV7W&U÷FW'&–åöf—BæÖ§6  §ÂVæ6öF–ærÂ6—¦RÂfW'F–6ÂÆGF–6RÂÖ‚ÇÌéEÇÂg2F†Rf–VÆBÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Â6†—VBFöF’†ÖW6†÷BÂBÖ&—B’Â¢£cƒ‚´"¢¢Â3bãBÖÒÂ##rãbÖÒÀ§ÂÖW6†÷BÂbÖ&—B‡F†Rf÷&ÖBw2Ö‚’Âcƒ‚´"ÂsbãbÖÒÂSBãBÖÒÀ§ÂÖW6†÷BÂÒÖÆWfVÂÖVF—VÖÂbÖ&—BÂƒSB´"ÂsbãbÖÒÂSBãBÖÒÀ§Âæò6ö×&W76–öâÂ¢£bãCRÔ"¢¢ÂfÆöBÂ"ãRÖÒÀ ¢¢¥v†B—27F–ÆÂ÷VâÂæB—B—2vVçV–æVÇ’FV6—6–öâ&F†W"F†âÖV7W&VÖVçBâ¢¢Rã‚Ô"—2§&VÂ6÷7BöâF†R†öæRF†—2&ö¦V7Bv2&W÷'FVBg&öÒGv–6RÂæBF†R6öæf÷&Ö–ær72†2ÖFP§F†R†V–v‡BW'&÷"†&ÖÆW72âv†B&VÖ–ç2w&öær—2F†R¢¦†÷&—¦öçFÂ¢¢F—7Æ6VÖVçB(	BRæBâÖ÷fP¦'’WFò¢£S2ÖÒ¢¢(	Bv†–6‚æ÷F†–ær6÷'&V7G2æBv†–6‚æö&öG’†2–WB6†÷vâf—6—F÷"6â6VRà ¢¢¥6òF†R†öæW7B÷&FW"—3¢ÖV7W&RF†R†÷&—¦öçFÂ'FVf7B$Tdõ$RG&F–ærRã‚Ô"f÷"—Bâ¢ ¦FööÇ2ö7&—F–5÷6†÷G2æÖ§2ÒÖÖWG&–76W†—7G2f÷"W†7FÇ’F†—2¶–æBöb&6â–÷R6VR—B"VW7F–öâà¤–b—B—2–çf—6–&ÆRBF†Ræ6†÷'2f—6—F÷"—2öffW&VBÂF†Rç7vW"—2Fò¶VWF†Rcƒ‚´"Â&—6P§F†R&—BFWF‚Fòb&V6W6R—B—2g&VRÂæBw&—FRF†R&V6öæ–ærF÷vââFòæ÷Bç7vW"F†—2'§&VfW&Væ6RÂæBFòæ÷Bç7vW"—B'’&V6†–ærf÷"F†RVæ6ö×&W76VBf–ÆR&V6W6RW†7FæW72fVVÇ0§6fW"(	BvRvV–v‡B—2W6W"Öf6–ær6÷7BF†R6ÖRv’'W&–VB&öB—2à ¢¢¤öæRF†–ærFò6†V6²f—'7BÂ&V6W6R—BÖ’Ö¶RF†Rv†öÆRG&FR6†V¢¢¢F†RRÃ#Òv–GF‚F†@§6WG2F†RÆGF–6R—2Ö÷7FÇ’4´•%EôÔ$t”åôÖ(	BãR¶Òöb&öâöâV6‚6–FRöb"Ã#Ò&÷‚â§6¶—'BVÖ—GFVB2—G2÷vâÖW6‚v÷VÆB6‡&–æ²F†Rw&÷VæBw2VçF—6F–öâföÇVÖR'’"ã\9p¢†Ò×VçF—¦F–öâ×föÇVÖRÖW6†—2Ç&VG’F†RFVfVÇB’Âv†–6‚Bb&—G2v÷VÆBWBF†RÆGF–6P¦æV"3ÖÒf÷"æ÷F†–ær'WBvVæW&F÷"6†ævRâF†BæVVG2&¶RÂ6ò—B—2&÷÷6ÂFð¦Fö72ôtÄ"Ô4ôåE$5BæÖFæBvVæW&F÷'2÷FW'&–åövVâç–Âæ÷BVæ–ÆFW&ÂVF—Bà ¢¢¤f–ÆW3¢¢¢FööÇ2ö&¶Rç6†+rvVæW&F÷'2÷FW'&–åövVâç–‡6¶—'B7Æ—BÂ–bF¶Vâ’+p¦Fö72õ$TäDU$”äræÖF+rFö72ôtÄ"Ô4ôåE$5BæÖF‡&÷÷6R’âÖV7W&VÖVçBf—'7Bà ¢222"Ô%TsB(	BvWB6÷&æW"FVÆWFW2F†Rv†öÆR&öBVBÂG'’†Æb–æ6ÇVFVB+r¢¤DôäR##bÓ‚ÓR¢  ¢¢¤DôäR##bÓ‚ÓRâ¢¢F†RVFvRFW7B6Æ—2BF†RvFW&Æ–æRæ÷r–ç7FVBöbFVÆWF–ærF†RæVÂâV6€¦VæB—2G&–ÖÖVBöâV6‚6–FR”äDUTäDTåDÅ’'’&—6V7F–öâ÷WBg&öÒF†RG'’6VçG&VÆ–æR(	B7–ÖÖWG&–2öà§W'÷6RÂ&V6W6R&æ²&öB—2vWBöâöæR6–FRöæÇ’æB6‡&–æ¶–ær—B7–ÖÖWG&–6ÆÇ’v÷VÆBF‡&÷rF†P¦G'’fW&vRv’FöòâF†R6VçG&VÆ–æRFW7B—2VçF÷V6†VC¢&öBv†÷6R6VçG&R—2–âF†R&—fW"—2¦7&÷76–ærÂæBF†B—2'&–FvRw2¦ö"à ¢¢¤ÖV7W&VBöâF†R'V–ÇBvVöÖWG'’Âæ÷Böâ&WÆ’öbF†R'VÆS¢¢¢BÃƒC2æVÇ2†fRG'¦6VçG&VÆ–æRÂ¢¦ÆÂBÃƒC2æ÷r&V6‚F†R&–&&öâ¢¢Â¢£#‚öbF†VÒ6Æ—VBBF†RvFW&Æ–æR¢¢Â¢£¢ ¦G&÷VB27V"ÖÖWG&R6Æ—fW'2ÂæB¢£c"ãrÒöb&öGv’&V6÷fW&VB¢¢âF†R2VG2òã3Öf—'7@§&V6÷&FVB†W&Rv2&VBöfbG'Væ6FVB&ö&RÆ—7F–æræBv2¢¦†ÆbF†RG'VRf–wW&R¢¢(	B&VÖ–æFW §F†B6÷'FVBF&ÆR&VBg&öÒ—G2F–Â—2æ÷BF÷FÂà ¥F†RvFR76W'G2F†R”åd$”åB&F†W"F†âF†RçVÖ&W#¢WfW'’æVÂv—F‚G'’6VçG&VÆ–æR&V6†W0§F†R&–&&öâÂF†RöæÇ’W&Ö—GFVB'6Væ6W2&V–ær7V"ÖÖWG&R6Æ—fW'2Âv†–6‚&R6÷VçFVBæB&–çFVBâ—@¦Ç6ò76W'G2F†B6Æ—–ær7GVÆÇ’†Vç2Â6òÆFW"6–×Æ–f–6F–öâ&6²FòFVÆWF–ærF†RæVÀ¦f–Ç2–â4’&F†W"F†â–â67&VVç6†÷BâF†RW†—7F–ær&æò7G&VWBfW'FW‚7FæG2öâvFW""76W'F–öà¦—2Væ6†ævVBæB7F–ÆÂ76W2(	BF†R6Æ—7F÷2BG'’w&÷VæB'’6öç7G'V7F–öâà  ¤÷væW"×&W÷'FVB##bÓ‚ÓRg&öÒ6÷WF‚vFW"7G&VWC¢6ÆVâÖVFvVBw&VVâVG&–ÆFW&ÂVæ6†V@§F‡&÷Vv‚F†R&öGv’†VBâ7G&–v‡BVFvW2ÖVâvVöÖWG'’ÂæB—B—2F†R6—¦RöböæR&öBVBà ¦7G&VWG2æ§2FE&V6÷&FG&÷2VBv†VâF†R6VçG&VÆ–æRõ"¢¦ç’öb—G2f÷W"6÷&æW'2¢¢—2vFW#  ¢–b‡FW'&–âæ—5vFW"†’ÇÂFW'&–âæ—5vFW"†"’ÇÂ6÷&æW'2ç6öÖR†—5vFW"’’²6öçF–çVS²Ð ¥F†R6öÖÖVçB6—2F†RVFvRFW7BW†—7G2Fò&¶VW&æ²&öBg&öÒ–çF–ær÷fW"vFW"§W7B&V6W6P¦—G2ÆVvÂ6÷'&–F÷"&V6†W2—B"(	Bf—"–ÒÂæBF†Rw&öær–ç7G'VÖVçBâ¢¥F†R&VÖVG’f÷"&Fòæ÷@§–çB÷fW"vFW""—2Fò4Ä•F†RVBBF†RvFW&Æ–æRÂæ÷BFòFVÆWFR—B¢¢Â&V6W6RFVÆWF–ærF¶W0§F†RG'’†Æbv—F‚—Bâöâ&æ²&öBF†R6÷'&–F÷"w2÷WFW"6÷&æW"w&¦W2F†RÖ6²6öç7FçFÇ’à ¥&WÆ–VBv–ç7BF†R6†—VBÖ6²ÂW"7G&VWC  §Â7G&VWBÂVG2ÂG&÷VC¢vWB4TåE$RÂG&÷VC¢vWBTDtRôäÅ’ÂÖWG&W2FVÆWFVBÂRÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Â¶–ç¦–RÂc3"ÂƒBÂ¢£b¢¢Â#"Â¢£Bã"R¢¢À§ÂÆ¶RÂSC2Â3BÂÂs’ÂbãRRÀ§Âv6†–æwFöâÂSC2Â#ÂÂCrÂ2ã’RÀ§Â6æÂÂ3SrÂ2Â"Â32ÂBã"RÀ§Â&æFöÇ‚ÂSCBÂ#"ÂÂC’ÂBãRÀ§Â6÷WF‚vFW"Â3CÂBÂ¢£2¢¢ÂbÂ"ãRÀ ¥F†R¢¦VFvRÖöæÇ’¢¢6öÇVÖâ—2F†R–æFVfVç6–&ÆR'Bâ¢¥F†RF&ÆR&÷fRVæFW'7FFW2—B¢£¢—Bv2&V@¦öfbG'Væ6FVBÆ—7F–ærÂæBF†Rv†öÆR×F÷vâf–wW&RÖV7W&VBg&öÒF†R'V–ÇBvVöÖWG'’—2¢£#‚æVÇ0¦æBc"ãrÒöb&öGv’FVÆWFVBv†–ÆRF†R6VçG&VÆ–æRv2G'’ÆæBf—6—F÷"6â7FæBöâ¢¢(	BGv–6P§v†Bv2f—'7Bw&—GFVâF÷vâ†W&RâV÷FRF†RÖV7W&VBf–wW&RÂæ÷BF†RF&ÆRâF†RvWBÖ6VçG&RG&÷2&RFVfVç6–&ÆR–â&–æ6—ÆP¢†&öBvVçV–æVÇ’7&÷76–ærF†R&—fW"’'WB6†÷VÆB&R6†V6¶VBv–ç7BF†R'&–FvR&V6÷&G2&F†W"F†à¦77VÖVB(	B3BVG2öâÆ¶R—2s’ÒÂæB—B—2v÷'F‚¶æ÷v–ærv†WF†W"F†B—2öæR7&÷76–ær÷"¦Ö6²F†B—2FöòvVæW&÷W2à ¢¢¤f–ÆW3¢¢¢&VæFW&W'2÷vV"ö§2÷7G&VWG2æ§6†6Æ—ÂFòæ÷BG&÷’+rFööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6†6†V6°§F†Bæò7G&VWBÆ÷6W2VBv†÷6R6VçG&VÆ–æR—2G'’¢¢¤66WFæ6S¢¢¢F†RVFvRÖöæÇ’FVÆWF–öç2vòFò¢§¦W&ò¢£²F†RvWBÖ6VçG&RFVÆWF–öç2&RVæ6†ævVB÷ ¦§W7F–f–VBW"7G&VWC²F†R6÷WF‚vFW"†öÆR—2vöæR–â6†÷BBF†R÷væW"w2÷6S²æò&öB–çG0¦÷fW"vFW"(	B&÷fR—BÂFòæ÷B76W'B—Bà ¢222"Ô(	BFöW2F†Rò&¶RV&â—G2æ–v‡FÇ“ò+r¢¥Tä4Ä”ÔTB+räU…BU†ÆæR÷"7FæFÆöæR’¢  ¤÷VæVB##bÓ‚ÓBgFW"æ–æR&¶R'2‚3rÂ3Â3Â32Â3BÂ3bÂ3rÂ3‚Â3#§vW&R6Æ÷6VBVæÖW&vVB–â&F6‚â¢¤"Ô%Ts27F÷VBF†VÒ67V×VÆF–æs²F†—2&6VÂ6·2v†WF†W §F†W’6†÷VÆB&R&öGV6VBBÆÂâ¢  ¢¢¥v†B6Æ÷6–ærF†VÒ&WfVÆVBâ¢¢WfW'’tÄ"–âF†RæWvW7B"v2¢¦ÖöF–f–VBÂæöæRFFVB¢¢(	BSp¦ÖöF–f–VBÂæWr(	Bv–ç7BFWfF†BÇ&VG’6'&–VBÆÂ#sÂ–æ6ÇVF–ærF†Ræ–æP¦&æFöÇ…öFV&&÷&æ&öög2g&öÒF†BÖ÷&æ–ærw2&Æö6²â&Æö6²&6VÂÆæG26ö×ÆWFS¢F†R–æf–ÆÀ¦vVæW&F÷'2VÖ—BÆ6V†öÆFW"vVöÖWG'’FWFW&Ö–æ—7F–6ÆÇ’v—F†÷WB&ÆVæFW ¢†vVæW&F÷'2ö–æfW'&VE÷Æ6V†öÆFW"ç–ÂvFVB'’6†V6²ç6†’Â6òF†Ræ–v‡FÇ’—2¢§&RÖ&¶–ærv†@¦Ç&VG’W†—7G2&F†W"F†â7WÇ––ærç—F†–ærÖ—76–ær¢¢âæB&RÖ&¶R&Ww&—FW2'—FW2WfVâv†Và¦æ÷F†–ær6†ævVBÂ&V6W6RFööÇ2ö&¶Rç6†6—26òöâ—G2÷vâf6S¢FWFW&Ö–æ—6Ò—2FVf–æVBöà¤”åUE2Â&&V6W6R7–6ÆW2ò—2æ÷B&—B×&W&öGV6–&ÆR7&÷72†&Gv&R"à ¥6ò&¶R"—2Â'—FRf÷"'—FRÂÖ÷7FÇ’6‡W&â(	BæB—BvöW27FÆRv—F†–â†÷W'2â3#v÷VÆB†fP¢¢¦FVÆWFVBVÆWfVâÆ–æW2g&öÒF†RV&Æ—6†VB6†ævVÆör¢¢æB&Ww&—GFVâvÆ²ö–æFW‚æ‡FÖÆÂ&V6W6P¦—B'&æ6†VBf—fR6öÖÖ—G2&6²æB&R×V&Æ—6†VBÖ—'&÷"F†B&VFFVBF†Rv÷&²6–æ6RÂ–æ6ÇVF–æp§F†R"Ô%Ts"f—‚à ¢¢¥F†RVW7F–öâÂæB—B—2ç7vW&&ÆR&F†W"F†âÖGFW"öbF7FS¢¢¢v†BFöW2F†Rò&¶P§f—6–&Ç’'W’÷fW"F†RÆ6V†öÆFW"vVöÖWG'“ò"ÔsÖW&vVBF†BÖ÷&æ–ær&V6—6VÇ’6ò&F–BF†—0¦6†ævR†÷r—BÆöö·2"7F÷2&V–ærâF¦V7F—fRâW6R—Bà ¢¢¤ÖWF†öBâ¢¢F¶RöæR&Æö6²F†B†2&÷F‚f÷&×2f–Æ&ÆRÂ6†ö÷B—BF‡&÷Vv€¦FööÇ2ö7&—F–5÷6†÷G2æÖ§2ÒÖÖWG&–762Æ6V†öÆFW"ÖöæÇ’æB2&¶VBÂæBV÷FRF†RGvòF&ÆW2à¥F†Vâ6’v†–6‚öbF†W6RF†RWf–FVæ6R7W÷'G3  ¢Ò¢¤—BV&ç2F†Ræ–v‡FÇ’¢¢(	BF†RF–ffW&Væ6R—2f—6–&ÆRBF†Ræ6†÷'2f—6—F÷"—2öffW&VBà¢¶VWF†R6FVæ6S²F†Rf—‚—2F†BF†R&¶R6†÷VÆB6Æ÷6R—G2÷vâ7WW'6VFVB'2v†Vâ—B÷Vç0¢æWröæRÂ6òW†7FÇ’öæR—2÷VâæB—B—2Çv—27W'&VçBà¢Ò¢¤—BV&ç26FVæ6RÂ'WBæ÷Bæ–v‡FÇ’¢¢(	Bf—6–&ÆR'WB6Æ÷rÖÖ÷f–ærâÖ÷fRFòvVV¶Ç’÷"Fð¢F—7F6‚ÂæB6’v†BF†RG&–vvW"6†÷VÆB&Rà¢Ò¢¤—BFöW2æ÷BV&âV—F†W"¢¢(	BF†RÆ6V†öÆFW'2&Rv†B6†—2æBF†R&¶R—2&Vf–æ–æp¢6öÖWF†–æræö&öG’6VW2BF†RF—7Fæ6W2F†R—2vÆ¶VBBâF†VâF†R†öæW7B÷WF6öÖR—2Fð¢7F÷'Vææ–ær—Böâ66†VGVÆRÂ¶VW—BöâF—7F6‚f÷"v†VâvVöÖWG'’vVçV–æVÇ’6†ævW2Âæ@¢&V6÷&BF†B–âFö72õ$TäDU$”äræÖFà ¢¢¤Fòæ÷Bç7vW"F†—2'’&VfW&Væ6Râ¢¢æ–æR'2F’öb'VææW"F–ÖR—2&VÂ6÷7BæB6ò—0§F‡&÷v–ærv’&Vf–æVÖVçBF†BÖGFW'3²F†RF&ÆW2FV6–FR—Bà ¢¢¤f–ÆW3¢¢¢Fö72õ$TäDU$”äræÖF+ræv—F‡V"÷v÷&¶fÆ÷w2ö6†–6vòÓFBÖ&¶Rç–ÖÆ†6FVæ6RæBö÷"F†P§7WW'6VFR7FW’+rFö72õ$ôDÔæÖFâÖV7W&VÖVçBöæÇ’(	BæòFF&V6÷&B6†ævW2à ¢¢¤æ÷FS¢¢¢F†R&¶R'2rvFR'Vç2Ç6ò6—B–â7F–öå÷&WV—&VF„v—D‡V"†öÆF–æp¦&÷BÖ'&æ6‚v÷&¶fÆ÷w2f÷"ÖçVÂ&÷fÂ’Â6òF†W’6÷VÆBæWfW"†fRvöæRw&VVâVæGFVæFV@¦ç—v’â–bF†R÷WF6öÖR¶VW2'2–âF†R–7GW&RÂF†BæVVG26öÇf–ærFöòÂ÷"WfW'’&¶R ¦'&—fW2W&ÖæVçFÇ’VævFVBà ¢222"Ô%Ts"(	BF†RF÷vâw2&öG2fæ—6‚–âÆ6W2ÂæBg&öÒF†R—"+r¢¤DôäR##bÓ‚ÓB+rGvòfVÇG2ÂæBF†RF†—&B7W7V7B&VgWFVB¢  ¢¢¥6†—VC¢¢¢F†RvFRf—'7BÂF†VâF†Rf—‚Â–âF†B÷&FW"æBf÷"F†B&V6öâà ¢¢¥F†RvFR(	B&öD6öçG&7B‚––âFööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6â¢¢F‡&VRg&ÖW2öböæR†VÆB66VæR@¦V6‚öbGvòæ6†÷'2ÂB&÷F‚f–Ww÷'G3¢F†R&VÂ&VæFW"¢¥"¢¢ÂF†R6ÖRvVöÖWG'’2â÷VP¦Ö&¶W"v—F‚FVÆ–&W&FVÇ’DTUU"öÇ–vöâöfg6WB¢¤Ò¢¢ÂæBF†R66VæRv—F‚F†R7G&VWBw&÷W ¦†–FFVâ¢¤ò¢¢â¢¤Ò—2F†RFVæöÖ–æF÷"æB—B—2v†BÖ¶W2F†—2v÷&²¢¢(	B&ö&R6÷VçG2öæÇ’v†W&P§F†RÖ&¶W"&V6†VBF†R67&VVâÂ6ò&öB&V†–æB'V–ÆF–ærÂG&VR÷"&—6RG&÷2÷WBöbF†P§6×ÆR–ç7FVBöb&V–ær66÷&VB2fVÇBÂv†–ÆR&öBF†BÆ÷6W2F†RFWF‚f–v‡BFòF†RFW'&–à§7F—2–â—BæB6†÷w2W2&öBF†B6÷fW'2—†VÂæBFöW2æ÷B6†ævR—BâF†RçVÖ&W"—0¦ÄÂ¢…"’(‰"Â¢„ò—ÆBV6‚7W'f—f–ær&ö&RÂöâ7&—F–5öÖWG&–72æÖ§6w2÷vâÆ$Æ(	BF†R6ÖR66ÆP§F†R7&—F–2†&æW72ÖV7W&W2&VfW&Væ6R†÷Föw&‡2v—F‚â&'3¢ÖVF–â¢¬éDÅÂ¢(šRã‚¢¢æB¢®(šRSRR¢ ¦öb&ö&W2BéDÅÂ¢(šR"ÂW"F—7Fæ6R&æBÂ&æG2æVVF–ær(šR‚&ö&W2ÂvFVBFò(šBcÒæB&W÷'FV@¦&W–öæBà ¢¢¥v†B—BÖV7W&VBv—F‚F†RfVÇB–â(	B&÷F‚&'2f–ÆVBÂv†–6‚—2F†R66WFæ6S¢¢  §Â7FF–öâÂ&æBÂÖVF–âéDÅÂ¢ÂW&6WF–&ÆRÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Â6÷WF…÷vFW&†W–R’Â#S(	3cÒÂ¢£ã2¢¢Â¢£BR¢¢À§Âg&öÕö&÷fV†W&–Â’Â(	3#SÒÂ¢£ã¢¢Â¢£R¢¢À ¢¢¤æBv—F‚F†Rf—‚–âÂFW6·F÷¢¢  §Â7FF–öâÂC(	3ÒÂ(	3#SÒÂ#S(	3cÒÂcÒ²‡VævFVB’À§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Â6÷WF…÷vFW&ÂBã"òsRÂ2ã’òƒ’RÂBãò“"RÂ(	BÀ§Âg&öÕö&÷fVÂ(	BÂ"ã’ò“RÂ"ãBòc2RÂ2ã2òRÀ ¢¢¤dTÅB(	BF†RFWF‚f–v‡BÂæB—B—2F†R&–âÆ6W2"â¢¢öÇ–vöäöfg6WDf7F÷#¢ÓÀ§öÇ–vöäöfg6WEVæ—G3¢Óv–ç7B6÷Ææ"FW'&–â—2g&7F–öâöbFWF‚Væ—BÂæBFWF€§&V6—6–öâFVw&FW2v—F‚F—7Fæ6RÂ6ò7Bã#SÒF†RFW'&–âvöâ–âF6†W2âFVWVæ–ærF†Röfg6W@§Fò¢®(‰#Bò(‰#‚¢¢ÄôäRFöö²6÷WF…÷vFW&#S(	3cÒg&öÒã2òBRFò¢£2ã2òsR¢¢âæòfW'FW€¦Ö÷fVBæBv÷'7DG&V7F–ÆÂvFW2BRÓRÒà ¢¢¤dTÅB"(	BF†R&öBv2BR÷VRÂæB—B—2F†R&g&öÒF†R—""â¢¢BF†RW&–Âæ6†÷"F†P§&–&&öâ—2v–FRÂVæö66ÇVFVBæBv–ç2FWF‚ÂæB—B5D”ÄÂ66÷&VBãòS¢æV—F†W"F†Röfg6WBæ÷ §F†RF†–â×&–&&öâ'VÆRÖ÷fVBF†B&æBBÆÂâF†R6W6Rv2F†RWF†÷&VBÇ†(	BÆ–v‡FÇ’v÷&à§G&6²v2ã‚²'WG2£ãSB(‰"7&÷vâ£ãFÂ6ò‚RV'F‚÷fW"“"R&—&–Rv’g&öÒF†R'WG2æ@£BRBF†R7&÷vââ&6VÆ–æW2&—6VBFò¢£ãSBòã3‚òã#‚¢¢†w&FVBòv÷&âòÆ–v‡B’ÂÖöGVÆF–öà§6†RæB6Æ72÷&FW&–ærVçF÷V6†VBâ&V6÷&FVB2¢¤Ã“b¢¢–âFö72ôÄ”$U%D”U2æÖF2âÖVæFÖVçBFð¤Ãs’Âv†–6‚Ç&VG’&V6÷&FVBF†W6RçVÖ&W'22–çfVçF–öâà ¢¢¥$TeUDTB(	BÖ—ÖfW&vVBÇ†fÆÆ–ærVæFW"Ç†FW7FÂF†R&6VÂw2÷vâ&–ÖR7W7V7Bâ¢¢—B—0§F†R&–v‡B6†RæB—B—2F†RcsBG&VVÆ–æRfÖ–Ç’ÂæB—B—2æ÷Bv†B—2†Væ–æs¢GW&æ–æp¦Ö—Ö2ôdbÖFRWfW'’&æBtõ%4R†6÷WF…÷vFW&#S(	3cÒÂ6†&Röb&ö&W2&V6†–ærF†R67&VVã ¢¢£#"Rv—F‚Ö—2ÂbRv—F†÷WB¢¢’âF†RÖ—6†–â—2†öÆF–ær7V"×—†VÂ&–&&öâFövWF†W"Âæ÷@¦W&6–ær—BâÖ–äf–ÇFW&—2Væ6†ævVBâ¢¤ÖV7W&R&Vf÷&R6†ö÷6–ærv2F†R&–v‡B–ç7G'V7F–öâæB—@§6fVBf—‚F†Bv÷VÆB†fRÖFRF†—2v÷'6Râ¢  ¢¢¤Ç6ò6†—VBÂæB—B—2æ÷Bv†Bf—†VBV—F†W"fVÇC¢¢¢7V"×—†VÂfÆö÷"–âF†R7G&VWB6†FW"à¦V'Vç2(i#W†7FÇ’7&÷72F†RG&6²Â6òögv–GF‚‡dÖWbç‚–•2F†R&–&&öâw2v–GF‚–â67&VVà§—†VÇ2(	BæòVæ–f÷&ÒÂæòf–Ww÷'BFò¶VW–â7–æ2âVæFW""‚F†RÇ†66ÆW2W–â&÷÷'F–öâÀ¦6VBBl9ræBã“"â6ÖR&–æ6—ÆR2Ô”åõ4”Ä„õTUEDUõ†–âG&VW2æ§6â—B&–æG2öæÇ’BF†P§F†–âVæBÂv†–6‚—2v‡’—BF–Bæ÷F†–ærg&öÒF†R—"à ¢¢¥F†—&B7W7V7BÂäõB7FVBöââ¢¢G&ç7&VçC¢G'VVv—F‚Ç†FW7FFöW2WBF÷vâ×v–FRÖW6‚–à§F†R&6²×FòÖg&öçB726÷'FVBöâÖVæ–ævÆW72&÷VæF–ær×7†W&R6VçG&RâÖ÷f–ær—BFòF†R÷VP§VWVRÖV7W&VB26ÖÆÂÂ6öç6—7FVçB–×&÷fVÖVçB(	BæB—BÖ¶W2WfW'’&öB4ôÄ”BÂ&V6W6Rà§Væ&ÆVæFVBÇ†×FW7FVBg&vÖVçBG&w2BgVÆÂ7G&VæwF‚âF†Bv÷VÆBFVÆWFRF†Rw&FVB÷v÷&âöÆ–v‡@¦F—7F–æ7F–öâF†RFF6WB6'&–W2âÆVgB2—B—2ÂFVÆ–&W&FVÇ“²–bF†R6÷'BWfW"&—FW2ÂF†Rf—‚—2§W"×&V6÷&B&VæFW$÷&FW"Âæ÷B÷6—G’à ¢¢¤öæRF†–ærF†RvFR†BFòÆV&â&÷WB—G6VÆc¢¢¢g&öÕö&÷fV—2âW&–Âæ6†÷"ÂæBÆVf–æp§F†R6ÖW&F†W&R'&ö¶RF†R†÷&—¦öâ×F–Ö&W"6†V6²gW'F†W"F÷vâF†Rf–ÆRÂv†–6‚&VG2F†R&æBF†P§G&VR6öÇfW"'V–ÆG2&÷VæBF†R6ÖW&æBf÷VæBæ÷Vv‡Böbæ÷Vv‡B6÷fW&VB&V&–æw2âÖV7W&VÖVç@§F†BÖ÷fW2F†R6ÖW&÷vW2F†RæW‡BöæR—G2÷6R&6²â—BFöW2æ÷rà ¥&W÷'FVB'’F†R÷væW"##bÓ‚ÓC¢¢'F†RF÷vâ&öG26VVÒFòF—6V"–âÆ6W2æBv†Vâ–÷P¦fÇ’÷fW"F†VÒ–÷RÆ÷6RF†VÒÂF†W’6†÷VÆB&RöâF†R7W&f6RæB&R6VVââ"  ¢¢¥F†RvFR6ææ÷B6VRF†—2ÂæBF†B—2F†Rf—'7BF†–ærFòf—‚â¢¢FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6 ¦76W'G2F†R7G&VWG2&R§÷VÆFVBæBG&VB¢(	B&V6÷&B6÷VçBÂfW'FW‚6÷VçBÂG&RW'&÷"À¦æòvWBfW'F–6W2(	BæBWfW'’öæRöbF†÷6R76W2v†–ÆRF†R&öG2&R–çf—6–&ÆRâG&VB—2æ÷@§6VVââF†W&R—2æò76W'F–öâç—v†W&RF†B&öB&V6†W2F†R67&VVâà ¢¢¥F‡&VR6æF–FFRÖV6†æ—6×2ÂÆÂ–â&VæFW&W'2÷vV"ö§2÷7G&VWG2æ§6ÂæBF†W’6ö×÷VæBà¤ÖV7W&R&Vf÷&R6†ö÷6–ær(	BFòæ÷Bf—‚ÆÂF‡&VR&Æ–æBâ¢  ¢¢£âÖ—ÖfW&vVBÇ†fÆÆ–ærVæFW"Ç†FW7FâF†RÖ÷7BÆ–¶VÇ’ÂæBF†—2&ö¦V7B†0¦Ç&VG’&VVâ&—GFVâ'’—Böæ6Râ¢¢F†R&öBFW‡GW&Rw2Ç†—2'V–ÇB0¦#SR¢VFvR¢&öG–Âv†W&RVFvV&×2Fò¦W&ò7&÷72F†R÷WFW""RöbF†Rv–GF‚æB&öG– ¦f÷"âVæ–×&÷fVBG&6²—2ã‚²'WG2£ãSBÒ7&÷vâ£ãF(	B6òv’g&öÒF†Rv†VVÂ'WG2F†P¦Ç†—2&÷WB¢£#ó#SR¢¢âv—F‚Ö–äf–ÇFW#¢Æ–æV$Ö—ÖÆ–æV$f–ÇFW&Â6Æ–Ö&–ærv’fW&vW0§F†BF†–âÂÆ÷rÖÇ†&–&&öâv–ç7B—G2÷vâG&ç7&VçBVFvW3²öæ6RF†RfW&vVBÇ†G&÷0§VæFW"Ç†FW7C¢ã#VF†Rg&vÖVçG2&R¢¦F—66&FVB÷WG&–v‡B¢¢âF†B—2F†R6ÖRf–ÇW&P¦fÖ–Ç’26†ævVÆör¢§csB¢¢(	B¢%F†RF—7FçBG&VVÆ–æR†B†öÆW2–â—BF†BvW&Ræ÷B6·’"¢Âv†W&P¦7&÷vâÖöGVÆF–öâ7WBöæR×—†VÂ6–Æ†÷VWGFR÷WBöbW†—7FVæ6RâF†Rf—‚GFW&âF†Bv÷&¶VBF†W&P¦—2F†RöæRFò&V6‚f÷#¢æWfW"ÆWBÖöGVÆF–öâF¶RfVGW&R&VÆ÷röæR—†VÂöbF†Rf–WvW"w0¦÷vâ67&VVââG&VW2æ§66'&–W2F†R&V6VFVçBà ¢¢£"â–ç7Vff–6–VçBöÇ–vöâöfg6WBBÇF—GVFRâ¢¢F†RÖFW&–Â6WG0¦öÇ–vöäöfg6WDf7F÷#¢ÓÂöÇ–vöäöfg6WEVæ—G3¢Óv–ç7B6÷Ææ"FW'&–ââöæRVæ—B—0§F–ç’ÂæBFWF‚Ö'VffW"&W6öÇWF–öâFVw&FW26†'Ç’v—F‚F—7Fæ6RÂ6òg&öÒF†R—"F†RFW'&–à¦6âv–âF†RFWF‚FW7B–âF6†W2(	Bv†–6‚—2W†7FÇ’F†R&W÷'FVB¢&–âÆ6W2"¢Â&F†W"F†â¦6ÆVâÆÂÖ÷"Öæ÷F†–ærfFRâæ÷FRF†RÖW6‚—2FWF…w&—FS¢fÇ6V'WB7F–ÆÂFWF‚Ò¢§FW7G2¢¢à ¢¢£2âF†RG&ç7&VçBVWVR—26÷'F–ærF÷vâ×v–FRÖW6‚'’öæR6VçG&Rö–çBâ¢ ¦G&ç7&VçC¢G'VVWG2F†R7G&VWG2–âF†R&6²×FòÖg&öçB72Âv†W&RÖW&vV@¦ÖW6‚×W"×7W&f6R6÷'G2öâ—G2&÷VæF–ær×7†W&R6VçG&R(	BÖVæ–ævÆW72ö–çBf÷"&öBæWGv÷&°§7ææ–ærF†Rv†öÆRF÷vââÇ†FW7Fv—F‚G&ç7&VçC¢G'VV—26ÖVÆÂ–â—G6VÆc¢à¦Ç†×FW7FVB7W&f6RW7VÆÇ’&VÆöæw2–âF†R÷VRVWVRÂw&—F–ærFWF‚Âv†W&RF†R6÷'B—0§W"Ög&vÖVçBæBg&VRà ¢¢¤f–ÆW3¢¢¢&VæFW&W'2÷vV"ö§2÷7G&VWG2æ§6+rFööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6  ¢¢¤66WFæ6S¢¢¢æWrvFRF†Bv÷VÆBd”ÂFöF’(	B6×ÆRF†R&VæFW&VBg&ÖRÆöær¶æ÷vâ7G&VW@¦6VçG&VÆ–æW2g&öÒF†RvÆ¶W"w2W–RäBg&öÒF†RW&–Âæ6†÷"ÂB&÷F‚f–Ww÷'G2ÂæB76W'BF†P§&öB—2F—7F–æwV—6†&ÆRg&öÒF†Rw&÷VæB&W6–FR—BâV÷FRF†RÖV7W&VBçVÖ&W'2ÂæBWBF†P¦fVÇB&6²Fò&÷fRF†R6†V6²æÖW2—Bâ$TäDU$”är*sRw2ÖWF†öBÆ–W3¢ÖV7W&RÂFòæ÷B76W'Bà¦F¦V7F—fRâF†R&öG2×W7B&VB¦öâF†R7W&f6R¢(	BF†—2—2æ÷BÆ–6Væ6RFòÆ–gBF†VÒöfbF†P§FW'&–âÂv†–6‚v÷VÆB'&V²F†RG&R76W'F–öâF†BÇ&VG’76W2æB—26÷'&V7Bà ¢¢¥'VææW#¢¢¢ÆæRâ—BF÷V6†W2æòFFæBæòvVæW&F÷"Â6ò—BÖ’'Vâ&W6–FRç’F÷vâ&6VÂà ¢222BÔ%Ts"(	Bs’w&÷VæBfW'F–6W2f6RF÷vçv&B+r¢¤DôäR##bÓ‚Ó#2…BÓB’(	BF†R6Æ76–f–W"†BæòF‡&W6†öÆB–â—B¢  ¢¢¤6Æ÷6VB'’vVæW&F÷'2÷FW'&–åövVâç–*röf6U÷F†U÷6·’‚–ÂæBF†R6÷VçB—2â¢¢F†P¦FVfV7BFV6ö×÷6VBW†7FÇ’öâF†R6†—VBÖ7FW"Âv—F‚æ÷F†–ærÆVgB÷fW#¢¢£32G&–ævÆW0§v÷VæB&6·v&G2¢¢‡Æâ&V(‰#2ã#RFò(‰##RãÜ+"Â÷&F–æ'’gVÆÂ×6—¦Rw&÷VæBf6W2v†÷6P§v–æF–ærF†RâÖvöâG&–æwVÆF–öâ&WfW'6VB’æB¢£“r7FæF–ærVFvRÖöâ¢¢‡Æâ&VW†7FÇ£ã(	B6Æ—fW'2–âÆæRöb6öç7FçBRÂ6öç7FçBâÂ÷"F‡&VRö–çG26öÆÆ–æV"–âÆã°§F†RæV6·2öb¶W–†öÆW2F†RÆæ"F—76öÇfRÆVfW2–â—G2âÖvöç2ÂæBF†R6÷W&6RöbF†P¦ÖW6‚w2RöæR×G&–ævÆRfW'F–6W2’âF†RvVæW&F÷"æ÷r&R×v–æG2F†Rf—'7B6WBæBFVÆWFW0§F†R6V6öæBÂF†Vâ&VgW6W2FòW‡÷'B–bV—F†W"7W'f—fW2à ¢¢¥v†BÖ¶W2—B&W—"æBæ÷BÖ6³¢F†R6Æ76–f–W"—2F†R–çf&–çBÂæB—B†2æð§GVæVBçVÖ&W"–â—Bâ¢¢&÷F‚7W&f6W2F†—2ÖöGVÆRVÖ—G2&R6–ævÆR×fÇVVBgVæ7F–öç2ö`¢„RÂâ’Â6ò6VVâg&öÒ&÷fRWfW'’G&–ævÆR×W7B6÷fW"÷6—F—fRÆâ&VæBv–æ@¦6÷VçFW"Ö6Æö6·v—6RâF†R"ãRÒÆGF–6RVçF—6W2Æâ&VFò×VÇF—ÆW2öb†Æb6VÆÂÂ6ð§F†R†—7Föw&Ò†26ÆVâvV—F†W"6–FRöbæ÷F†–æs¢“rf6W2BW†7FÇ’ãÜ+"ÂF†Và§F†R6ÖÆÆW7B†öæW7BG&–ævÆRB2ã#RÜ+"âæòF†—&B÷VÆF–öâÂæò§VFvVÖVçB6ÆÂà¤FVÆWF–ærâVFvRÖöâf6R6ææ÷B÷Vâ†öÆRf÷"F†R6ÖR&V6öâ—B—2FVÆWFVB(	B—B6÷fW'0¦æòÆâ&V(	BæBÖW6…÷g5öf–VÆB‚–6—26ò÷WBÆ÷VC¢¢£Ö—76W2öb#‚Ãƒ“&—2ÂÖ€£bÖÒÂ&Vf÷&RæBgFW"â¢  ¢¢¥F†Rö'f–÷W2f—‚v2G&–VBf—'7BæB—2v÷'6Râ¢¢ævöåöÖWF†öCÒ$4Ä•&†V"6Æ—–ærÀ§&ö'W7Böâ6öæ6fRâÖvöç2v†W&R$TUE’—2æ÷B’v—fW2¢£C"¢¢&6·v&G2f6W2–ç7FVBöb30¦æB¢£’ÃCƒ2¢¢7V"ÖÖÜ+"6Æ—fW'2–ç7FVBöbƒ‚ÂÖV7W&VBöâF†—26ÖRÖW6‚âF†P§G&–æwVÆF–öâ&ÆVæFW"–6·2—2æ÷BF†RF†–ærFò&wVRv—F‚à ¤Ö7FW#¢#C’Ãƒ#b(i"#C’Ãc#’G&–ævÆW2Â#RÃƒ(i"#RÃsBfW'F–6W2Â(‰#"ÃS3"'—FW3²F†R6—€¦Æ÷7BfW'F–6W2&R¶W–†öÆRF—2æBWfW'’7W'f—f–ærfW'FW‚¶VW2—G2ô4ôäd”DTä4VfÇVP§FòF†R&—Bâv÷'7B6†—VBw&÷VæBæ÷&ÖÂæ÷rö–çG2¢£ãs3r¢¢WÂv–ç7BvFRBãà¦FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§676W'F–öâ†"’—2ÓÓÒæB×W7B7F’F†W&Rà ¢ÒÒÐ ¢¢¥F†R÷&–v–æÂ&÷‚Â2—B7FööC¢¢  ¤f÷VæB##bÓ‚ÓBv†–ÆRvF–ærF†R&Æ6²×vVFvRf—‚â¢£s’öbF†RFW'&–âw2sC"ÃSƒfW'F–6W0¢ƒãR’6öÖR÷WBöbF†RvVæW&F÷"v—F‚æ÷&ÖÇ2f6–ærDõtâ¢¢(	B66GFW&VB—6öÆFVBö–çG0¦–ç6–FRF†RF÷vâB÷&F–æ'’VÆWfF–öç2†R“â(‰#3ÂR#2â(‰#3RÂR##‚â32’Âæ÷B¦6öçF–wV÷W2F6‚æBæ÷BBF†R&÷‚VFvRÂv†–6‚—2v‡’F†W’&öGV6Ræòf—6–&ÆR'FVf7Bà ¤F—7F–æ7Bg&öÒF†RvVFvRF†B&ö×FVBF†R6V&6ƒ¢F†Bv232öbôäRF–ÆRw2“’fW'F–6W2(	B§F†—&Böb—B(	B6W6VB'’vÇFb×G&ç6f÷&Ò÷F–Ö—¦V6–×Æ–g––ærF†Rw&÷VæBÂæB—B—2f—†VBà¥F†W6Rs’&R–âF†RÖ7FW"æB&VFFR—BâÖ÷7BÆ–¶VÇ’FVvVæW&FRG&–ævÆW2÷"¦æ÷&ÖÂÖfW&v–ær'FVf7B–âF†RFV6–ÖF÷"à ¢¢¥–ææVBÂæ÷B–væ÷&VBâ¢¢FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§676W'G2F†R6÷VçB6ææ÷BW†6VVBs’Â6ð§F†RçVÖ&W"6âöæÇ’vòF÷vââf—†–ærF†—2Æ÷vW'2F†R6öç7FçB–âF†R6ÖR"à ¢¢¤f–ÆW3¢¢¢vVæW&F÷'2÷FW'&–åövVâç–+rFW'&–â&V&¶R†æ–v‡FÇ’&¶RÆæR’+p¦FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6†Æ÷vW"F†R6öç7FçB ¢¢¥'VææW#¢¢¢F†RæòÔ&ÆVæFW"†Æb—2F–væ÷6—2(	Bf–æBF†Rs’–âF†RvVæW&F÷"w2÷vâ÷WGWBæ@§6’v†BÖ¶W2F†VÒâF†R&V&¶R'&—fW2f–6†–6vòÓFBÖ&¶Rç–ÖÆà ¢222"Ô%Ts(	BF†R&—fW"VFvRfÆ–6¶W'2v†VâfÇ––ær+r¢¤DôäR##bÓ‚Ób(	B—Bv2F†RäT"ÄäRÂæBF†Rf—‚Ö÷fW2æòVFvR¢  ¢¢¥&VBF†—2&÷‚&Vf÷&R&–6–ærç’7W&f6RFò6WGFÆRFWF‚F–Râ¢¢F†R÷væW"w2fÆ–6¶W&–ær&æ°¦Æ–æR—2F†RFWF‚'VffW"'Vææ–ær÷WBöbçVÖ&W'2B&ævRÂæBF†R6W6R—26ÖW&6WGF–æp§&F†W"F†âç—F†–ær&÷WBF†RvFW#¢Ö–âæ§66'&–VB¢¦f—†VBãÒæV"ÆæR¢¢v—F‚£2ÃÒf"ÆæRâW'7V7F—fRFWF‚'VffW"&W6öÇfW2&÷WB¬+"ò†æV"+r%æ&—G2–BF—7Fæ6P¦¦Â6òBF†RãÒæV"ÂGvò7W&f6W2¢£3SÒv’†BFò&Rã6Ò'B–âFWF‚¢¢&Vf÷&RF†P¦'VffW"6÷VÆB÷&FW"F†VÒ(	BæBF†RvFW&Æ–æR—2F†RöæRÆ6R–âF†—266VæRv†W&RGvò7W&f6W2&P¢¢¦6ò×Ææ"'’FW6–vâ¢¢†FW'&–âæ§6¢F†R&æ²Æ–æR•2v†W&RF†Rw&÷VæB7&÷76W2’Ò’â–ç6–FP§F†B&æBF†Rv–ææW"—2FV6–FVB'’&÷VæF–ærÂæBç’6ÖW&Ö÷fVÖVçB&R×&öÆÇ2—Bà ¢¢¥F†R–ç7G'VÖVçBÂæB—B—2F†R'Bv÷'F‚6''––ærf÷'v&C¢ÔõdRD„R4ÔU$EtòÔ”ÄÄ”ÔUE$U2â¢ ¦FööÇ2öÖV7W&U÷&—fW%öVFvRæÖ§67FæG2BF‡&VRW&–Â÷6W2ÆöærF†R÷væW"w2÷vâ&W&öGV7F–öâÀ§†÷Föw&‡2V6‚ÂçVFvW2F†R6ÖW&"ÖÒ(	B&÷WBf—fRÖ‡VæG&VGF‚öb—†VÂBF†W6R&ævW2Â6ð¦æòVFvR6â†öæW7FÇ’Ö÷fR(	BæB†÷Föw&‡2—Bv–ââF†R6Æö6²—2†VÆBÂF†R…TB—2†–FFVâÂæ@¢¢§F†R6ÖR÷6R†÷Föw&†VBGv–6Rv—F‚æòçVFvRF–ffW'2'’—†VÇ2BWfW'’7FF–öâ¢¢Âv†–6‚—0§F†R6öçG&öÂF†BÖ¶W2F†R&W7Böb—BÖVâç—F†–ærâ—†VÂF†B6†ævW2VæFW"F†RçVFvR6†ævV@¦&V6W6RFWF‚F–R&W6öÇfVBF†R÷F†W"v’âfÆ–6¶W"—2Ö÷F–öâÂæBF†—2—2†÷r7F–ÆÂg&ÖP¦ç7vW'2VW7F–öâ&÷WBÖ÷F–öâà §Â7FF–öâÂÇF—GVFRÂ&æ²Æ–æRÂ‚Â¢¦&æ²fÆ–6¶W"Â&Vf÷&R¢¢Â¢¦gFW"¢¢À§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Âg&öÕö&÷fV‡F†R66VæRæ6†÷"’ÂsRÒÂ#ÃCSrÂcs"+r¢£2ãR¢¢ÂSƒ2+r¢£"ãrR¢¢À§ÂFW66VæEöÖ–å÷7FVÖÂ“ÒÂbÃ““BÂ"ÃcC‚+r¢£RãbR¢¢ÂSc+r¢£2ã2R¢¢À§Â÷fW%÷F†Uöf÷&·6ÂCRÒÂ’Ãs“BÂÃCc’+r¢£rãBR¢¢ÂCs+r¢£"ãBR¢¢À ¤ÖV7W&VBöâF†RT$Ä•4„TBÖ—'&÷"B#ƒ9sƒâF†RvFR—2ÒÖvFVÂB¢£RRöbF†R&æ²Æ–æR¢£ §&VBBGvòöbF†RF‡&VR7FF–öç2&Vf÷&RÂw&VVâBÆÂF‡&VRgFW"v—F‚ãrö–çG2Fò7&Râ—B—0¦4„$RæBæ÷B6÷VçBöâW'÷6R(	B6÷VçB—2çVÖ&W"&÷WBF†R÷6Rà ¢¢¥F†Rf—‚—2&V6—6–öâÂæ÷BF–RÖ'&V²ÂæBF†BF—7F–æ7F–öâ—2F†R&6VÂw2&wVÖVçBâ¢¢F†RæV §ÆæRæ÷r÷Vç2v—F‚ÇF—GVFR†äT&–âÖ–âæ§6¢GvVçG’Öf–gF‚öbF†RW–Rw2†V–v‡B&÷fRF†P¦w&÷VæBÂVçF—6VBÂ6Æ×VBFòã(	3‚Ò’âöâfö÷BÇF—GVFV—2Â6ò¢¦vÆ¶W"w26ÖW&—2F†P¦6ÖW&F†W’†B&Vf÷&RÂFòF†RF–v—B¢¢âF†Rö'f–÷W2ÇFW&æF—fR(	BöÇ–vöäöfg6WFöâF†RvFW ¦ÖFW&–Â(	Bv2&V¦V7FVBöâF†R66WFæ6RF†—2&÷‚v2w&—GFVâv—Fƒ¢—B6WGFÆW2F†RF–R'’&–6–æp§F†RvFW"F÷v&BF†R6ÖW&ÂæBB3SÒöæRFWF‚7FW—2ã6Òöbw&÷VæBÂ6òF†RG&và§vFW&Æ–æRv÷VÆB6Æ–Ö"F†R&æ²'’WFòF†B×V6‚â¢¥F†B'&V·2F†R–çf&–çBF†RFW6–vâW†—7G0§FòwV&çFVRâ¢¢&V6—6–öâ6÷7G2æ÷F†–æræBÖ÷fW2æòVFvS²&–2'W—2F†R6ÖR–7GW&R'¦Ç––ær&÷WBv†W&RF†R&—fW"—2à ¢¢¤f–æF–ær(	BÔõ5Bôbt„BdÄ”4´U%2•2äõBD„R$ä²ÂæB—B—2æ÷r"Ô%Tsbâ¢¢F†Rv†öÆRÖg&ÖR6÷Vç@§VæFW"F†R6ÖRçVFvR—2Ãc“òRÃ“ò2Ãƒƒb‚&Vf÷&RæBÃSc‚òÃƒƒ2òÃs2gFW#¢F†P¦6öçF–çV÷W2ÖvVçFÆ–æRÆöærF†R&æ²–âF†R&Vf÷&RÖÖ6²—2vöæRÂæBv†B—2ÆVgB—2¢§7V6¶ÆP¦öâ&öög2ÂvÆÇ2æB6æ÷–W2¢¢BWfW'’7FF–öââF†B—26V6öæB÷VÆF–öâv—F‚F–ffW&Vç@¦6W6RÂæBF†—2&6VÂF–Bæ÷B6†6R—BâF†R&W6–GVÂ"ãN(	32ã2RBF†R&æ²—2F†R6ÖR7V6¶ÆP¦fÆÆ–ærv—F†–âGvò—†VÇ2öbvFW&Æ–æRÂv†–6‚—2v‡’F†RvFR—2æ÷BF–v‡FW"à ¢¢¤æBF†R7W7V7Bf÷"—B—2TåDU5DTB&F†W"F†â&VgWFVBÂ&V6W6RF†R–ç7G'VÖVçBv2–æW'Bâ¢ ¦ÒÖæò×7Vâ×6†F÷vv2w&—GFVâFòFW7BF†Rö'f–÷W26æF–FFR(	BF†R6†F÷r6ÖW&föÆÆ÷w2F†P§vÆ¶W"Â6òÖ÷fVB6ÖW&&R×&7FW&—6W2F†R6†F÷rÖöçFò6†–gFVBFW†VÂw&–Bâ—B&W÷'FVBF†P¦çVÖ&W'2¢§Væ6†ævVBFòF†R—†VÂ¢¢Âv†–6‚&VB2&VgWFF–öââ—B—2æ÷C¢F†RfÆrw2÷vâ6öçG&öÀ¢‡WBF†R6†F÷r&6²Â†÷Föw&‚v–â’6†ævW2¢£—†VÇ2¢¢Â6òG&÷–ær67E6†F÷vgFW"&ö÷@¦æWfW"&V6†W2F†R&VæFW"BÆÂâF†RfÆræ÷r¢¦W†—G2"¢¢öâF†B6öçG&öÂ&F†W"F†â&–çF–ær¦f–æF–ærâ¤F–væ÷7F–2F†B6†ævW2æ÷F†–ær&W÷'G2&æ÷BF†R6W6R"f÷"F†R6ÖR&V6öâ'&ö¶Và§F†W&ÖöÖWFW"&W÷'G27FVG’FV×W&GW&R¢(	BF†R6—‡F‚F–ÖRöâF†—2&ö¦V7BF†Bw&VVâ&VF–æp¦6ÖRg&öÒâ–ç7G'VÖVçBö–çFVBBæ÷F†–ærà ¢¢¤f–ÆW3¢¢¢&VæFW&W'2÷vV"ö§2öÖ–âæ§6‡F†RäT&&Æö6²Â6WDæV$f÷&Â7FG2‚’æ6ÖW&æV&’+p¦FööÇ2öÖV7W&U÷&—fW%öVFvRæÖ§6†æWr’+rFööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6‡Gvò7G'V7GW&Â76W'F–öç2öà§F†RæV"ÆæS²F†R—†VÂvFR7F—2–âF†RFööÂÂBF‡&VRg&ÖW27FF–öâ’à ¢¢¤æ÷B6Æ–ÖVC¢¢¢F†RFW6·F÷†ÆböbF†R6Öö¶R(	Bã2Ö–âv–ç7BF†—2'VææW"w2ÖÖ–çWFP§W"Ö6öÖÖæB6V–Æ–ærâF†RÖV7W&VÖVçB—G6VÆbv2'VâB#ƒ9sƒÂv†–6‚—2F†R†&FW"f–Ww÷'Bf÷ §F†—2FVfV7C¢Ö÷&R—†VÇ2öb&æ²Æ–æRFòF—6w&VR&÷WBà ¢222"Ô%Tsr(	BfÆ÷vW"†VG2†ær–âF†R6·’v—F‚æ÷F†–ærVæFW"F†VÒ+r¢¤DôäR##bÓ‚Ór+r4TTâ+rõtäU"Õ$Uõ%DTB##bÓ‚Ób¢  ¢¢¥D„RõtäU"u2$Uõ%BÂæB—B—2F†Rf–gF‚F–ÖRF†—27–×FöÒ†2&VVâf—†VBâ¢¢7FæF–æröâ6÷WF€¥vFW"7G&VWBöâF†RöFWbö&Wf–WrB¢¦&V&–ærääR#\+¢¢ÂÆöö¶–æræ÷'F‚7&÷72F†RÖ–â7FVÓ¢Gvð§–VÆÆ÷rfÆ÷vW"†VG2fÆöB¢¦&÷fRF†R†÷&—¦öâÆ–æR¢¢ÂV6‚öâ6†÷'B7FÆ²F†B¢§7F÷2–âÖ–BÖ—"¢ ¦æB&V6†W2æòÆçBâ†—2v÷&G3¢¢'–VÆÆ÷rfÆöF–ærö&¦V7G2Â’wVW72F†W’&R7W÷6VBFò&RfÆ÷vW'0¦'WB—BFöW2æ÷B6öææV7Bâ"¢&÷F‚6—BvVÆÂ&÷fRW–RÆWfVÂv—F‚6ÆV"6·’&VæVF‚F†VÓ²F†RæV"öæR—0§F†RÆ&vW"Â6òF†W’&RBF–ffW&VçBFWF‡2æBF†—2—2æ÷BöæR7G&’–ç7Fæ6Rà ¢¢¤dõU"$”õ"$U•%2$Ru$•EDTâ”åDò&VæFW&W'2÷vV"ö§2öfÆ÷&æ§6dõ"D„•2U„5B5”ÕDôÒÂäBD„P¥5”ÕDôÒ•2”â$ôET5D”ôââ¢¢&VBF†VÒ&Vf÷&RF÷V6†–ærç—F†–ær(	BV6‚6Æ÷6VB&VÂÖV6†æ—6Òæ@¦æöæRöbF†VÒ6Æ÷6VBF†—3  §Âv†W&RÂv†B—Bf—†VBÂ—G2÷vâv÷&G2À§ÂÒÒ×ÂÒÒ×ÂÒÒ×À§ÂæÆ–æRccbÂ†VBæBÆçBG&Wr†V–v‡G2g&öÒ–æFWVæFVçBG&w2öböæR&ævRÂ¢'F†R—"öbfÆ÷vW"†VG2F†R7&—F–2f÷VæBfÆöF–ærVæGF6†VB–âF†R÷Vâ6·’"¢À§ÂæÆ–æR#3“‚ÂWfW'’†VB&6†WG—Rv–æVB¢§VGVæ6ÆR¢¢&VÆ÷r—BÂ¢&fÆ÷vW"F†BVæG2v†W&R—G27FÆ²6†÷VÆB&Vv–â—2F†RfÆöF–ær7&—FRF†R7&—F–26Vv‡B–âF†R6·’"¢À§ÂæÆ–æR#C’ÂTETä4ÄV&÷VæG2†÷rf"'&æ6†VB†VBÖ’6—BöfbF†R7FVÒÂ¢&ÆöÆÆ—÷2†æv–ær–âF†R—"&W6–FRF†R66R"¢À§ÂæÆ–æR#S3"Â&”vVöÖWG'–vVçBg&öÒ’&—2FòB6òF—62—2æ÷B7–FW"Â¢&Bæ–æR6VçF–ÖWG&W2öâ&—&–RÖFö6²66R—Bv2¢¦–VÆÆ÷r7F"–âF†R6·’¢¢"¢À ¢¢¥D„Rd”äD”är•2Å$TE’d”Ä$ÄRäB•B•2"Ô%TsV"w3¢f÷W"f—†W2FòF†RE$t”ärÂæBæ÷BöæRvFP§F†B&VG2F†RG&v–ær&6²â¢¢FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6†2æò76W'F–öâç—v†W&RF†BG&và¦fÆ÷vW"†VB†2ÆçBvVöÖWG'’&VæVF‚—BâF†RGvòF†–æw2F†B6÷VæBÆ–¶R—B&Ræ÷B—B(	BF†P¦fÆöF–æv6†V6²æV"Æ–æR#Sr—2&÷WB¢¦'V–ÆF–æw2¢¢†÷fW&–ær÷fW"F†V—"w&÷VæBÂæ@¦fÆöF–ætG'’öfÆöF–æuvWFæV"Æ–æR#ƒCb6·2v†WF†W"vFW"ÖÆ–Ç’§&V6÷&B¢—2¢§Æ6VB¢¢öâG'¦ÆæBÂv†–6‚—2Æ6VÖVçBFW7BöbW†7FÇ’F†R¶–æB"Ô%TsV"&÷fVB6ææ÷B6VRG&v–ærfVÇBâ¢¥6ð§F†—27–×FöÒ†2&VVâ&W—&VBf÷W"F–ÖW2'’W–RæB76W'FVB¦W&òF–ÖW2â¢  ¢¢¥Etò5U5T5E2$RÅ$TE’$TeUDTB(	BFòæ÷B7VæBF†R'VâöâF†VÒv–ââ¢  £â¢¤—B—2äõB"Ô%TsV"w26–vâfVÇBâ¢¢fÆ÷&æ§6w2W6‚‚–‡æÆ–æR“c‚’F¶W2TåRã&æBFöW0¢öÒç6WE÷6—F–öâ†RÂ’ÂÖã"–¢¦—G6VÆb¢¢Â6òWfW'’6ÆÆW"(	B†VG2–æ6ÇVFVB(	B—2æVvFVBöæ6Ræ@¢öæÇ’öæ6RâÖ–&T†VF76–ærâ²ÖF‚æ6÷2†’¢&—26÷'&V7Bà£"â¢¤—B—2äõB†VB7W'f—f–ærG&÷VB7FVÒâ¢¢Æ6Tf÷&&æBÆ6Tw&Ö–æö–F&÷F‚Væ@¢&WGW&â6WBçW6‚‚âââ’ò‚¢ÂæB&÷F‚6ÆÂ6—FW2wV&B–b†‚â–&Vf÷&R6ÆÆ–æp¢Ö–&T†VFâF†R6öÖÖVçB&W6–FR—BÇ&VG’7FFW2F†R'VÆS¢¢&¦W&ò6—2F†R6v2&V6†VBæ@¢æ÷F†–ærv2G&vâ†W&RÂ6òæ÷F†–ærÖ’&R‡Væröfb—BV—F†W"â"  ¢¢¥D„RÄ•dR5U5T5E2Â–âF†R÷&FW"v÷'F‚FW7F–ærâ¢  £â¢¥D„R$”ärdDRÄõtU%2D„R„TBäBD„RÄåB4U$DTÅ’â¢¢Ö–&T†VF76W2&—6VFòF†P¢6†FW"2vVÆÂ2FF–ær—BFò–ÂæBF†R&V6öâ—2w&—GFVâF÷vã¢¢'F†R6†FW"†2Fò'&–ærF†P¢†VBDõtâv—F‚F†RÆçB2F†R&–ærfFW2—C¢†VBÆVgBBF†R†V–v‡BF†R5RWB—Bv÷VÆ@¢†ær–âF†R—"÷fW"6‡&–æ¶–ær7FVÒâ"¢F†R†VBæBF†RÆçB&R–â¢¦F–ffW&VçB–ç7Fæ6V@¢6WG2v—F‚F–ffW&VçB&–ær&ÖWFW'2¢¢†æV"æ†VFò&–ætB†bæ†VBÂ(
b–v–ç7BF†RÆçBw2÷và¢bæfFV’ÂæBF†RöæÇ’F†–ærG––ærF†VÒFövWF†W"—2&F—W26ö×&—6öâBF†R6ÆÂ6—FP¢†"ÃÒbæ†VE³Ò²öfb²7FW’â¢¤&F—W26ö×&—6öâ—2æ÷BF†R6ÖR7FFVÖVçB2'F†R7FVÐ¢VæFW"F†—2†VB—2BgVÆÂ†V–v‡B"â¢¢–bF†RÆçBw2fFR&V6†W2¦W&ò&Vf÷&RF†R†VBw2FöW2À¢F†RFö7VÖVçFVBf–ÇW&RÖöFR—2W†7FÇ’F†R÷væW"w2†÷Föw&‚à£"â¢¥F†Rw&÷VæBF†R†VB—2‡VæröfbÖ’æ÷B&RF†Rw&÷VæBF†R7FVÒ7FæG2öââ¢¢’Ò7FF–öâ†RÂâÀ¢¦öæRÂ7ÂvWB–—26×ÆVBöæ6RæBW6VBf÷"&÷F‚Â'WBF†R6†÷B—2F¶Vâ¢¦7&÷72vFW"¢¢Âæ@¢F†RVÖW&vVçB÷vWBF‚—2F†RÆV7B×G&fVÆÆVBöæR–âF†BgVæ7F–öâà£2â¢¥66ÆRâ¢¢†VB—26—¦VBg&öÒF†R&V6÷&Bw2–æfÆ÷&W66Væ6Rç6—¦UöÖF‡&÷Vv‚æöÖ–æÂVæ—B&÷ƒ°¢&V6÷&Bv—F‚&B6—¦UöÖv—fW2†VBf"FöòÆ&vRf÷"—G2ÆçBÂv†–6‚&VG22fÆöF–æp¢WfVâv†Vâ—B—2GF6†VBâ6†VFò'VÆR–â÷"÷WB(	B&–çBF†RG&vâ†VB6—¦Rv–ç7B—G0¢ÆçBw2†V–v‡BæBÆöö²BF†RF–Âà ¢¢¥D„R44UDä4RÂæB—B—2æ÷BæVv÷F–&ÆRÂ&V6W6Rf÷W"W–V&ÆÂf—†W2—2Væ÷Vv‚â¢¢F†R&W—"6†—0§v—F‚vFRF†B¢§&VG2F†RÖW&vVB†VBvVöÖWG'’&6²æB&WV—&W2ÆçBvVöÖWG'’&VæVF‚WfW'¦†VB¢¢(	BF†R6ÖR6†R2"Ô%TsV"w2¦WfW'’G&VRG&vâ7FæG2B—G2÷vâ7FF–öâ¢Âv†–6‚—2F†RöæP¦vFRF†B6÷VÆBæ÷B†fR76VBF‡&÷Vv‚F†B'Vrâ6öæ7&WFVÇ“¢f÷"WfW'’G&vâfÆ÷vW"Ö†VB–ç7Fæ6RÀ§6öÖRÆçB–ç7Fæ6RöbF†R6ÖR7V6–W2v—F†–â—G2÷vâ7&VBÂv†÷6RG&vâF÷&V6†W2F†R†VBw0§7FÆ²â¢¤FVÖöç7G&FR—B$TBöâFöF’w2'V–ÆB&Vf÷&RF†Rf—‚vöW2–ââ¢¢vFRöâF†RÆ6VÖVçB—0§F†RvFRF†B†2&VVâw&VVâF‡&÷Vv‚ÆÂf÷W"&W—'2à ¢¢¥&W&öGV6Rf—'7BÂF–væ÷6R6V6öæB¢¢(	B"Ô%TsV"w2'VÆRÂæBF†RöæR3“b6¶—VBâF†R÷6R—2öà¥6÷WF‚vFW"7G&VWBBääR#\+²FööÇ2÷6†ö÷BæÖ§6WG2F†R6ÖW&F†W&Râ¢¥F†Rf—'7B6öÖÖ—BöbF†—0§&6VÂ6†÷VÆB&R67&VVç6†÷Bâ¢  ¢¢¥D„Rå5tU"Â##bÓ‚Ós¢D„R$T$”ärt2$”t…BäBD„RÔE$•‚EU$äTB•Bâ¢¢Ö–&T†VF6ö×WFW0¦F–ÇD¦6òF†R7FÆ²ÆVç2&6²FòF†R7FVÒÂæBF†Vâ76W2¢§&æFöÒ–v¢¢–çFòF†R6ÖP¦W6†6ÆÂâW6†'V–ÆG2F†R–ç7Fæ6R&÷FF–öâ2âWVÆW"–â¢¦•…¦÷&FW"¢¢Â6òF†B–r—2¦'–Æ–VBõUE4”DRF†RF–ÇC¢—B7–ç2F†Rv†öÆRÆVæ–ær†VBÂæBF†R¦–×WF‚v—F‚—BÂFò§Væ–f÷&ÖÇ’&æFöÒ&V&–ærâ¢¦W6†w2÷vâFö77G&–ær6—2¢%72–vÆöæw6–FRF–ÇB(	BF†RÖG&—€¦6'&–W2F†Rv†öÆR&÷FF–öâ"¢ÂæBF†R6ÆÆW"FöW2æ÷B¢¢(	BæBF†R–r—2æ÷BWfVâæVVFVBF†W&RÀ¦&V6W6RF†RfW'FW‚&öw&ÒÇ&VG’7–ç2F†R†VB&÷WB—G2÷vâ†—2öfbfÆ÷&çvâ—Bv2Æ–V@§Gv–6RÂæBF†R6V6öæBÆ–6F–öâv2F†R'VrâF†B—2v‡’f÷W"&W—'2FòF†RE$t”ärV6‚6Æ÷6VB§&VÂÖV6†æ—6ÒæBæöæRöbF†VÒ6Æ÷6VBF†—3¢¢¦WfW'’öæRöbF†VÒ6ö×WFVBçVÖ&W"F†BÆFW"Æ–æP§F‡&Wrv’â¢¢F†RÆ—fR7W7V7G2–âF†R&÷‚&÷fRvW&RÆÂw&öær(	BF†R&–ærfFR—2Ööæ÷FöæR††V@¦fFR—2&÷f&Ç’(šBÆçBfFRBWfW'’F—7Fæ6R’ÂæBF†RfVÇB&W&öGV6W2F÷vâG'’7G&VWBà ¢¢¥D„R$TBÂÄäDTBd•%5BÂôâD„RTäÔôD”d”TBFWf%T”ÄBâ¢¢FööÇ2öÖV7W&Uö†VE÷7W÷'BæÖ§6&VG2F†P¦–ç7Fæ6R'VffW'2&6²(	BWfW'’†VB6WBæBWfW'’&ö÷FVB6WB(	B&W&öGV6W2F†RfW'FW‚&öw&Òw2&–æp¦fFRæB†VBFW66VçB–â¥2ÂæB6·2v†WF†W"F†Rfö÷BöbV6‚G&vâ†VBw27FÆ²ÆæG2–ç6–FR¦G&vâÆçBw2&öG’ÂVæFW"—G2G&vâF÷âV&Æ—6†VBÖ—'&÷"ÂFW6·F÷ÂÆÂV–v‡B66VæRæ6†÷'2Bf÷W ¦&V&–æw3  §ÂÂ&Vf÷&RÂgFW"À§ÂÒÒ×ÂÒÒ×ÂÒÒ×À§ÂG&vâ†VG2v—F‚æ÷F†–ærVæFW"F†VÒÂ¢£3‚öbÃsS"¢¢Â¢£öbÃs3R¢¢À§Â÷6W26''––ærfVÇBÂ¢£‚öb3"¢¢ÂÀ§Â7FÆ²fö÷B(i"æV&W7B7FVÒÂÖVF–âÂ¢£#ÖÒ¢¢Â¢£¢¢À§Âââç“’òv÷'7BÂ¢£#3BÖÒòSƒ"ÖÒ¢¢Â¢£ò¢¢À§Â'’6†RÂ¢£3‚öbÃCr6÷'–Ö&¢¢ÂöbF†R÷F†W"V–v‡BÂ(	BÀ ¢¢¤—B—2ÆÂ6÷'–Ö&ÂæBF†B—2F†R&—F†ÖWF–2&F†W"F†â6ö–æ6–FVæ6S¢¢¢6÷'–Ö%öfÆF—2F†P¦öæR&6†—FV7GW&Rv—F‚&÷F‚Æ&vRF–ÇB&æBƒãCN(	3ãsB&B’æBWFòGvVçG’†VG2W"ÆçBÂæ@§F†R†VBw2öfg6WB—26VBB&V6‚9r6—¦R9r6–â†ÆVâ–(	BãS2Òöâ#B6ÒVÖ&VÂâ&æFöÐ¦&V&–æröâF†B6—2†ÆbÖÖWG&RÖ—72âWfW'’÷F†W"6†R—26ÖÆÂVæ÷Vv‚Â÷"W&–v‡BVæ÷Vv‚ÂF†@§F†RÖ—727F—2–ç6–FRF†RÆçB—B6ÖRg&öÒà ¢¢¥D„R$U•"•2äõBd”eD‚”ÒÂæBF†B—2FVÆ–&W&FRâ¢¢F†R†VB&6†WG—W2&Ræ÷r'V–ÇBv—F€§F†V—"÷&–v–âBF†R¢¦fö÷BöbF†V—"÷vâ7FÆ²¢¢†VGVæ6ÆVÆ–gG2F†Rv†öÆR&6†WG—R'’—G2÷và¦G&÷ÂæB—B—2F†RÆ7B6ÆÂ–âÆÂæ–æR'V–ÆFW'2’âF†R–ç7Fæ6R—2F†VâW6†VB¢¦öâF†R7FVÒ¢¢Â@§F†R†V–v‡BF†R'&æ6‚ÆVfW2—BÂæBF†RF–ÇB&÷FFW2F†R†VB÷WB&÷WBF†Bö–çB(	B6òF†Röfg6W@¦g&öÒF†R7FVÒ—2¦vVæW&FVB'’¢F†R7FÆ²–ç7FVBöb&V–ær6V6öæBçVÖ&W"F†B†2Fòw&VRv—F€¦—BâF‡&VRF†–æw2föÆÆ÷rÂæBF†RF†—&B—2F†RöæRF†BÖGFW'3  £â&Â7&VFæBF†Rã“FgVFvR&RvöæRg&öÒÖ–&T†VFâF†W&R—2æ÷F†–ærÆVgBFòF—6w&VRà£"â6†”fFV66ÆW2F†R†VB&÷WB—G2fö÷BÂ6ò†VB6Æ–FW2Dõtâ—G2÷vâ7FÆ²2—G2Æç@¢6‡&–æ·2â&Vf÷&RÂF†RÆFW&Âöfg6WBv2&¶VB–çFòF†RG&ç6ÆF–öâæBF–Bæ÷B6‡&–æ²BÆÂ(	@¢6V6öæBÂV–WFW"FWF6†ÖVçBF†BF†Rf—'7B7WBöbF†R&W—"ÆVgB&V†–æBBöbÃs3Rà£2âfö÷BÒÖ–â‡ÆçD‚Â&—6R(‰"&V6Œ+w6—¦\+v6÷2†ÆVâ’–ÂæBF†R6†FW"66ÆW2&÷F‚F†Rfö÷Bw2&—6Ræ@¢F†RÆçBw2†V–v‡B'’F†R6ÖR&×Â6ò¢¦fö÷B9rfFR(šB†V–v‡B9rfFVBWfW'’fFR¢¢âF†RvFP¢—2â–çf&–çBF†B†öÆG2'’6öç7G'V7F–öâÂæ÷BçVÖ&W"ÖV7W&VBBF†R÷6R6öÖVöæR6†÷6Rà ¢¢¥D„RtDRâ¢¢FööÇ2÷6Öö¶U÷&VæFW&W"æÖ§66'&–W2—BB&÷F‚f–Ww÷'G2(	B¦WfW'’G&vâfÆ÷vW"†VB†0¦ÆçBVæFW"—G2÷vâ7FÆ²¢(	B÷fW"F†R6ÖRV–v‡Bæ6†÷'2Bf÷W"&V&–æw2â—BF¶W2F†R7FÆ²fö÷@¦g&öÒ¢§F†R&6†WG—Rw2÷vâÆ÷vW7BfW'FW‚¢¢&F†W"F†âg&öÒ6öç7FçBÂv†–6‚—2v‡’F†R&Vf÷&Ræ@¦gFW"çVÖ&W'2&÷fR&R6ö×&&ÆR7&÷72&W—"F†BÖ÷fVBF†Ræ6†÷#¢F†R6ÖRÖV7W&VÖVçB&VG0¦Ö–å’Ò(‰%TETä4ÄU¶¶–æEÖöâF†RöÆB'V–ÆBæBÖ–å’ÒöâF†RæWröæRæB&W÷'G2F†R6ÖRö–çBà¤Ö–B6ÇV×6&B—2W†6ÇVFVBg&öÒF†RÆçG2F†BÖ’7W÷'B†VB(	Bæò†VB—2‡Værg&öÒöæRÂæ@¦6÷VçF–ærF†VÒ—2W†7FÇ’†÷rF†Rf—'7B7WBöbF†—2ÖV7W&VÖVçB&VB¢£Vç7W÷'FVB¢¢öâ'V–ÆBF†P¦6öÖÖ—GFVBWf–FVæ6Rg&ÖR6†÷w2Fò&R'&ö¶Vâà ¢¢¥D„RÄU54ôâÂæB—B—2f÷"WfW'’6WB–âF†—2f–ÆRÂæ÷Bf÷"fÆ÷vW'2â¢¢W"Ö–ç7Fæ6R&÷FF–öâF†@¦—26ö×÷6VBg&öÒGvò6÷W&6W2(	BöæRF†R6ÆÆW"6ö×WFVBæBöæR—B76VBÆöær÷WBöb†&—B(	B†2æð¦W'&÷"ÖöFRF†BÆöö·2Æ–¶RâW'&÷"â—B&VæFW'2â—B&VæFW'2ÆW6–&Ç’â¢¤f÷W"6W&FRvVçG2f—†V@§F†—27–×FöÒ'’W–RæBF†RvVöÖWG'’æWfW"öæ6RF–Bv†Bç’öbF†V—"6öÖÖVçG26’—BFöW2â¢¢&Vf÷&P¦FF–ær&÷FF–öâFW&ÒFòâ–ç7Fæ6VB6WBÂ6²v†BVÇ6R—2Ç&VG’&÷FF–ær—Bà ¢¢¤&Vf÷&RæBgFW"¢¢BFö72öWf–FVæ6R÷"Ö'Vsr×¶&Vf÷&RÆgFW'Òçæv(	BF†R6ÖRv†—FRVÖ&VÂ'’F†P§7F÷&Vg&öçG2öâ6÷WF‚vFW"7G&VWBB&V&–ær“+ÂV&Æ—6†VBÖ—'&÷"ÂFW6·F÷#ƒ9sƒÂ7&÷VBg&öÐ§F†Rg&ÖRFö72öWf–FVæ6R÷B×c"ÖgFW"çæv&V6÷&FVBF†RfVÇB–âà ¢¢¤4T4ôäB”å5Dä4R•2Å$TE’4ôÔÔ•EDTBÂBD”ddU$TåB5DD”ôâÂ”ââ”ÔtR4„õBdõ"äõD„U ¥$4TÂâ¢¢Fö72öWf–FVæ6R÷B×c"ÖgFW"çæv(	BF†Röâ×7G&VWB6÷WF‚vFW"f–WrÂ¢¦&V&–ær“+ÂFW6·F÷ £#ƒ9sƒ¢¢ÂF¶VâFò6†÷rBÕc"w2æ6†÷"Ö÷fR(	B6'&–W2¢§ÆRfÆ÷vW"†VBB&ööb†V–v‡BBF†P§&–v‡BÖ†æBVFvRöbF†Rg&ÖR¢¢Â&W6–FRF†R7F÷&Vg&öçB&÷rÂv—F‚6ÆV"6·’&V†–æB—BâF–ffW&Vç@¦&V&–ærÂF–ffW&VçBf–Ww÷'BÂF–ffW&VçBF’Â6ÖR7–×FöÒâGvòF†–æw2föÆÆ÷s  £â¢¥F†R&W&ò—26†VæBFöW2æ÷BæVVBF†R÷væW"w2W†7B÷6Râ¢¢GvòöbF†RF‡&VR6öÖÖ—GFV@¢6÷WF‚vFW"g&ÖW26†÷r—Bâ7F'Bv—F‚F†RöæW2Ç&VG’–âF†RG&VRà£"â¢¤—B—2æ÷B6öæf–æVBFòÆöö¶–ær7&÷72vFW"¢¢Âv†–6‚vV¶Vç2Æ—fR7W7V7B"†7FF–öâ‚–öâF†P¢VÖW&vVçBF‚÷fW"F†R&—fW"’&Vf÷&Rç–öæR7VæG2'Vâöâ—B(	BF†—2g&ÖRÆöö·2¦F÷vâG'¢7G&VWB¢v—F‚F†R&—fW"öfbFòF†RÆVgBâ7W7V7BÂF†R&–ærfFRÂ7W'f—fW2F†C²6†V6²—Bf—'7Bà ¢222BÓ3R(	BF†RfÆ÷vW'2w&÷rW÷WBöbF†Rw&÷VæB2–÷R&ö6‚+r¢¤DôäR##bÓ‚Ó‚+rõtäU"Õ$Uõ%DTB##bÓ‚Ór¢  ¢¢¥D„RõtäU"u2$Uõ%C¢¢¢¢'F†RfÆ÷vW'27F–ÆÂ6VVÒÆ–¶RF†W’w&÷r÷WBöbF†Rw&÷VæB2–÷R&ö6€§F†VÒÂF†W’Fòæ÷BfFR–â2–÷RvÆ²F÷v&G2ÂF†W’w&÷rWâ"¢¢¢%7F–ÆÂ"—2F†Rv†öÆRf–æF–ær¢¢(	@§F†—2—2†—24T4ôäB&W÷'BöâF†R6ÖR&–ærÂæBF†Rf—'7BöæRv2ç7vW&VBv—F†÷WBç7vW&–ær—Bà ¢¢¥t„BD„Rd•%5Bå5tU"D”Bâ¢¢†—2##bÓ‚ÓB&W÷'B(	B¢&w&72æBfÆ÷vW'2V"÷WBöbF†Rw&÷Væ@¦2–÷RvÆ²F÷v&G2F†VÒ"¢(	Bv2F–væ÷6VB2$DR&ö&ÆVÒæB—B&VÆÇ’v2öæS¢F†R&×v0¦&¶VB–çFòF†R†V–v‡BöâF†R5RæB6÷VÆBöæÇ’6†ævRv†VâF†RÆGF–6Rv2&V'V–ÇBÂ6òÆç@¦'&—fVBBSRRöb—G2†V–v‡B&WGvVVâöæRg&ÖRæBF†RæW‡BâF†R&W—"Ö÷fVBF†R&×–çFòF†P§fW'FW‚&öw&Ò†6öçF–çV÷W2ÂW"g&ÖR’æB–ç6WBF†RfFR&–ær–ç6–FR—G2÷vâÆGF–6R'’F†R&V'V–Æ@§7FWÂ6òæ÷F†–ær—2WfW"G&vâ&Vf÷&R—B—2Æ6VBâF†R÷–ævFR–âF†R6Öö¶R†öÆG2&÷F‚†ÇfW0¦æB—27F–ÆÂw&VVâ(	BÖV7W&VBöâF†—2'&æ6‚Â¢£S2'&—fÇ2÷fW"2ÒvÆ²Âv÷'7B'&—fÂãRö`§F†R&×¢¢Âv†–6‚—2F†R–ç6WBFö–ærW†7FÇ’v†B—Bv2'V–ÇBf÷"à ¢¢¤äB•BÄTeBD„R$ÕE$•d”är44ÄRâ¢¢G&ç6f÷&ÖVB£Ò6†”fFV(	BF†Rv†öÆRÆçBÂVæ–f÷&ÖÇ’Â&÷W@¦—G2÷vâ&6RÂv—F‚ÖF6†–ærv÷&ÆB×76RFW66VçB†6†”G&÷Ò6†•&—6R¢ƒÒ6†”fFR–’F†B6Æ–B¦fÆ÷vW"†VBF÷vâ—G2÷vâ7FÆ²6ò—B7F–VBöâF†R6‡&–æ¶–ær7FVÒâ¢¤ÆçBF†BvöW2g&öÒæ÷F†–æp§FògVÆÂ6—¦R&÷WB—G2&6R—2w&÷v–ærÂ†÷vWfW"f–æVÇ’–÷R7V&F—f–FRF†Rw&÷wF‚â¢¢F†Rf—'7B&W— ¦ÖFRF†Rw&÷wF‚4ÔôõD‚Âv†–6‚—2æ÷Bv†B†R6¶VBf÷"V—F†W"F–ÖRà ¢¢¥D„Rd•ƒ¢D„R$Õ•24õdU$tRÂäõB„T”t…Bâ¢¢fÆ÷&æ§6*rÆçDÖFW&–Æ†æG26†”fFVFòF†P¦g&vÖVçB6†FW"2f'––æræB&W6öÇfW2—Bv—F‚F†R÷&FW&VBL9sB&–W"67&VVâÖFö÷"F—F†W"F†—0§&ö¦V7BÇ&VG’W6W2FòG&râVæWf–FVæ6VBvÆÂ†6öæf–FVæ6Ræ§6’(	B6†÷6Vâ÷fW"&VÂG&ç6ÇV6Væ7¦&V6W6R7v&B—2V–v‡BF†÷W6æBF÷V&ÆR×6–FVB–ç7Fæ6W2F†Bv÷VÆB†fRFò&RFWF‚×6÷'FVBWfW'¦g&ÖRÂæB÷fW"W"Ö–ç7Fæ6R7Fö6†7F–27WB&V6W6RF†B—2÷Âv†–6‚—2F†RFVfV7BF†R&–æp§v2'V–ÇBFò&VÖ÷fRâF‡&VR6öç6WVVæ6W3  ¢¢¢¤†V–v‡B—2÷"æBæ÷F†–ær&WGvVVâ¢¢††V–v‡Döf’âG&vâÆçB—2G&vâBF†R†V–v‡B—G0¢&V6÷&Bv—fW2—BÂBWfW'’F—7Fæ6R—B—2G&vâBBÆÂà¢¢¢¥F†R†VBFW66VçB—2vöæRv—F‚F†R66ÆR—B6†6VBâ¢¢"Ô%Tsrw2–çf&–çB7W'f—fW2–çF7BæBvWG0¢6–×ÆW#¢Ö–&T†VFw26Æ×v—fW2fö÷BÃÒÆçD†ÂæBæ÷F†–ær66ÆW2V—F†W"6–FRöb—Bæ÷rà¢¢¢¤6öçF÷W&–ær—2'&ö¶Vâ'’W"Ö–ç7Fæ6R†6Râ¢¢6—‡FVVâF—F†W"ÆWfVÇ2v–ç7B&×–âD•5Dä4P¢v÷VÆB&R6—‡FVVâ6öæ6VçG&–2&–æw2&÷WBF†RvÆ¶W"(	B*r3f—FVÒ2w2&6öç7FçBv÷&ÆB&F—W2—2¢6öç7FçB67&VVâ&÷r"ÆÂ÷fW"v–â(	B6òV6‚ÆçBöfg6WG2—G2F‡&W6†öÆB'’†6‚öb—G2÷và¢v÷&ÆB÷6—F–öââg&7B†&–W"²†6R–—27F–ÆÂVæ–f÷&Òöâ³Ã’Â6ò6÷fW&vR—2Væ6†ævVBà ¢¢¥D„RtDRÂæB—B—2æWröæR&F†W"F†â&R×'Vââ¢¢F†R6Öö¶Rw2÷–âvÆ²æ÷rÇ6ò&VG2F†P¦G&vâ„T”t…BöbWfW'’ÆçB÷fW"F†R6ÖRGvVçG’6W3¢¦ÆçB—2G&vâB—G2÷vâ†V–v‡BÂf–çBÀ¦æWfW"6†÷'B¢(	BæòÆçBF†B—2G&vâBÆÂ—2G&vâ6†÷'BÂæBæ÷F†–ærÇ&VG’öâ67&VVâv–ç0¦†V–v‡B&WGvVVâGvòg&ÖW26R'Bâ¢¤ÖV7W&VC¢6†÷'FW7BG&vâÆçBãRöb—G2÷vâ†V–v‡BÀ§v÷'7Bv–âãRW"ãRÒ6RâF†R6ÖR&VF–æröbF†RôÄB†V–v‡BFW&Ò÷fW"F†R6ÖRvÆ²—0£ã"R¢¢(	BÆçBG&vâBf—fR×F†÷W6æGF‚öb—G2†V–v‡BÂv†–6‚—2v†Bw&÷v–ær÷WBöbF†Rw&÷Væ@¦Æöö·2Æ–¶Rw&—GFVâF÷vâà ¤—B—2FVÆ–&W&FVÇ’æ÷B6¶VBöb%$•dÅ2ÆöæRâF†R–ç6WBÖVç2ÆçB'&—fW2B6÷fW&vR¦W&òÂ6ð¦â'&—fÂÖöæÇ’&VF–ær6·2F†RVW7F–öâöbÆçBF†B—2æ÷B–WBG&vâæB76W2öâç—F†–æs°§F†RvFR&VG2WfW'’G&vâÆçB–âWfW'’g&ÖRöbF†RvÆ²âFööÇ2öÖV7W&Uö†VE÷7W÷'BæÖ§6æ@§F†R6Öö¶Rw2"Ô%TsrvFRÆ÷6RF†V—"¢fFVFW&×2–âF†R6ÖR6öÖÖ—BÂ&V6W6R&÷F‚&W&öGV6RF†P§fW'FW‚&öw&ÒæBÖ—'&÷"F†BG&–gG27F÷2&VF–ærF†RG&v–ærà ¢¢¤4õ5Bâ¢¢G&r6ÆÇ2CæBcÃƒ#2G&–ævÆW2ÂVæ6†ævVC¢F†R–ç7Fæ6W2vW&RÇv—2–âF†R'VffW"À§F†R&×öæÇ’WfW"6†ævVBF†V—"6—¦Râv†BF†R&æB—2–ç7FVB—2f–ÆÂ(	BÆçG2–ç6–FR—B&P§&7FW&—6VBv†öÆR&F†W"F†â6‡'Væ¶Vâ(	BæBv†B—B6fW2—2F†RæçVÇW2÷WG6–FRF†RfFR&–ærÀ§v†–6‚æ÷r6öÆÆ6W2Fòö–çB–ç7FVBöb&7FW&—6–ærgVÆÂ×6—¦RÆçBFòF—66&BWfW'’g&vÖVçBà  ¢222"Ô%Tsb†’(	BF†R6†F÷rw&–B6Æ–BVæFW"WfW'’7FWÂæBF†R6öçG&öÂF†B6ÆV&VB—Bv2–æW'B+r¢¤DôäR##bÓ‚Ór+r4TTâ–âÖ÷F–öâ+r÷VæVB##bÓ‚Ób'’"Ô%Ts¢  ¢¢¥†6S¢¢¢ÆæRÂ&VæFW&W"öæÇ’+r¢¥'VææW#¢¢¢–×&÷fR×'VææW"+r¢¤f–ÆW3¢¢ ¦&VæFW&W'2÷vV"ö§2÷v÷&ÆBæ§6†6VçG&Tf÷&ÂföÆÆ÷vÂ6WE6†F÷u6æÂ6†F÷u&–rç6æVF’+p¦FööÇ2öÖV7W&U÷&—fW%öVFvRæÖ§6‡F†R&W—&VB6öçG&öÂÂÒÖ&÷‚ÖG&–gFÂÒ×6æÖöffÀ¦$•dU%ôåTDtUôÖ’+rFööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6‡F‡&VR76W'F–öç2’+r6—FRö6†–6vòóFBò¢¦à ¢¢¥D„R4„•TBd•ƒ¢F†R6†F÷r&÷‚Ö÷fW2–âv†öÆRFW†VÇ2â¢¢—BföÆÆ÷w2F†Rf—6—F÷"ÂæB—Bv0§&RÖ6VçG&VBöâF†V—"W†7B÷6—F–öâWfW'’g&ÖR(	B6òF†RÖw26×ÆRÆGF–6R6Æ–Bg&7F–öâöb§FW†VÂv—F‚WfW'’7FWæB&R×VçF—6VBWfW'’6†F÷rVFvR–âF†R66VæRv†–ÆRæ÷F†–ær–âF†Rv÷&Æ@¦Ö÷fVBâF†R6VçG&R—2æ÷r&÷VæFVBöçFòv÷&ÆBÖæ6†÷&VBÆGF–6RöbF†R&÷‚w2÷vâFW†VÂ6—¦RÂ–âF†P¦Æ–v‡Bw2÷vâÆæRâ¢¤ÖV7W&VBv—F‚F†R6ÖW&†VÆBW&fV7FÇ’7F–ÆÂæBF†R&÷‚6Æ–B†ÆbFW†VÀ¢ƒS‚ãbÖÒ“¢g&öÕö&÷fV"Ã#26†ævVB—†VÇ2(i"ÂFW66VæEöÖ–å÷7FVÖRÃcS(i"â¢  ¥F†R6÷'&V7F–öâ—2BÖ÷7B†ÆbFW†VÂ(	BRã’6ÒFW6·F÷Âãr6Ò†öæR(	BæB—B—2¢¦öæÇ’WfW ¦7&÷72F†RÖÂæWfW"ÆöærF†R7Vâ¢¢Â6òF†R&V6‚ÂF†RÖ6—¦RÂF†Rãr6ÒFW†VÂæBF†R&–6 ¢òæ÷&ÖÄ&–66Æ–'&FVBFò—B&RÆÂVçF÷V6†VBà ¢¢¤d”äD”är(	BD„R4ôåE$ôÂD„B$4ÄT$TBD„R4„DõrÔ"4õTÄBäõB„dR4ÄT$TBå•D„”ärÂäBäõp¤•BÔõdU2RÃC3’•„TÅ2â¢¢ÒÖæò×7Vâ×6†F÷vG&÷VB7Vâæ67E6†F÷vgFW"&ö÷BæB6†ævVB §—†VÇ2öbF†Rg&ÖRÂv†–6‚F†—2&÷‚&VB2'F†RfÆræWfW"&V6†VBF†R&VæFW""âF†RÖV6†æ—6Ò—0¦6ö×–ÆF–öã¢67E6†F÷v—2&VBv†VâÖFW&–Âw2&öw&Ò—2'V–ÇBÂ6òfÆ—–ær—BÆFW"ÆVfW0¦WfW'’6†FW"7F–ÆÂ6×Æ–ærF—&V7F–öæÅ6†F÷tÖ³Ö(	BæBF†RÖ—G6VÆb—27F–ÆÂ†æv–ær–âF†P§FW‡GW&RVæ—Bg&öÒF†RÆ7Bg&ÖRF†B†BöæRâF†R&W—&VB†æFÆR7v—F6†W2&VæFW&W"ç6†F÷tÖ ¦öfb¢¦æBÖ&·2WfW'’ÖFW&–ÂæVVG5WFFV¢¢Âv†–6‚&V'V–ÆG2V6‚&öw&Òv–ç7BF†RæWp¦åTÕôD•%ôÄ”t…Eõ4„Dõu6â¢¥F†RvVæW&Æ—6F–öã¢&VæFW&W"fÆr&VBB6ö×–ÆRF–ÖR—2æ÷B§'VçF–ÖR†æFÆRÂæBF–væ÷7F–2F†BfÆ—2öæR—2ÖV7W&–ærF†R66VæR—BÖVçBFòW†6ÇVFRâ¢  ¢¢¤d”äD”är"(	BD„Rå5tU"DòD„•2$4TÂu2D•DÄRÂäB•B•2Ôõ5DÅ’äõBD„R5Tââ¢¢v—F‚F†R&W—&V@¦6öçG&öÂÂF†Rv†öÆRÖg&ÖRfÆ–6¶W"VæFW"F†R"ÖÒçVFvRöâFWffÆÇ2g&öÒ¢£Ã#ƒB(i"Ã‚¢¢@¦g&öÕö&÷fVæB¢£"Ã3ƒ2(i""Ã‚¢¢BFW66VæEöÖ–å÷7FVÖv†VâF†R6†F÷rÖ—2F¶Vâ÷W@¦VçF—&VÇ“¢¢§F†R6†F÷rÖ6'&–W2N(	3bRöb—Bâ¢¢F†R6æ&æ·2&÷WB†ÆböbF†BƒÃ#ƒB(i £ÃƒBæB"Ã3ƒ2(i""Ã“RÂæBF†RvFVB&æ²6†&R"ã’R(i""ãbRæB2ãBR(i"2ãR“²F†R÷F†W §ãƒBR—2¢¤äõB¢¢6ò×Ææ"FWF‚F–W2(	B"Ô%Tsb†"’&VgWFVBF†Böâ##bÓ‚Órv—F‚F†RFWF‚ÖgVæ7F–öà§7v—F6‚ƒ2öbÃ‚’æB\9rF†RæV"ÆæRƒcBöbcr7W'f—fR“²—B—2F†RF÷vâw2÷vâVFvW2&V–æp§&W6×ÆVBâF†R6VçFVæ6R&VÆ÷r7FööBf÷"öæRF’æB—2¶WB&V6W6RF†R&÷‚—B6—G2–â—2V÷FVBà¤Fòæ÷BV÷FP§F†R6†F÷rÖ2F†R6W6RöbF†RF÷vâw2fÆ–6¶W"à ¢¢¤d”äD”är2(	BD„RåTDtR”å5E%TÔTåB4ääõBÔT5U$RD„R4„Dõr$õ‚ÂäBD„REDTÕB•2ôâD„P¥$T4õ$Bâ¢¢"ÖÒ6Æ–FW2F†RÆGF–6R'’ãrRöbFW†VÂÂ6òF†RçVFvR6VW2ãrRöbFVfV7B§vÆ¶–ærf—6—F÷"ÖVWG2GvVÇfRFW†VÇ2öbW"6V6öæBâçVFv–ær'’†ÆbFW†VÂ–ç7FVBFò66ÆR—BW ¢¢¦f–Ç2¢£¢Bg&öÕö&÷fVS‚ãbÖÒçVFvR6†ævW2¢£#’Ã3‚¢¢—†VÇ2v—F‚F†R6æöâæB¢£#‚ÃsƒB¢ §v—F‚—Böfb(	BF†R6ÖW&Ö÷fR&W6×ÆW2F†Rv†öÆRg&ÖRæB7v×2F†R&÷‚Â6–vâ–æ6ÇVFVBâ¢¤§7V"×—†VÂçVFvR—2â–ç7G'VÖVçBf÷"FWF‚F–W2öæÇ’â¢¢F†R&–v‡B–ç7G'VÖVçBÖ÷fW2F†R$õ‚æBæ÷@§F†R6ÖW&Âv†–6‚—2v†BÒÖ&÷‚ÖG&–gFFöW3¢—Bg&VW¦W2föÆÆ÷vÂÆ6W2F†R&÷‚Gv–6R†Æb§FW†VÂ'BÂæB†÷Föw&‡2öæR–FVçF–6Â÷6RâF†B—2v†W&RF†R"Ã#2(i"&÷fR6öÖW2g&öÒà ¢¢¤d”äD”ärB(	BD„R”å5E%TÔTåB4õTÄBäõB%TâôâD„•2%TääU"BÄÂÂäBD„R$T4ôâ•2t•Bâ¢ ¤WfW'’6GW&R–âÖV7W&U÷&—fW%öVFvRæÖ§6F–ÖVB÷WC¢VÆVÖVçD†æFÆRç67&VVç6†÷B‚–v—G2f÷"F†P¦VÆVÖVçBFò&R§7F&ÆR¢(	BGvò6öç6V7WF—fRæ–ÖF–öâg&ÖW2v—F‚âVæ6†ævVB&÷‚(	BæBöæRg&ÖRö`§F†—266VæRVæFW"7v–gE6†FW"F¶W2&÷WBFVâ6V6öæG2Â6òGvòFòæ÷Bf—BÆ—w&–v‡Bw2327F–öà§F–ÖV÷WBâÖV7W&VC¢VÆVÖVçB6GW&Rf–Ç2B"2v†W&RvRç67&VVç6†÷B‚–&WGW&ç2–âã"2g&öÐ§F†R6ÖRvRâF†RFööÂ†÷Föw&‡2F†RvRæ÷rÂv—F‚â76W'F–öâF†BF†R6çf2f–ÆÇ2F†P§f–Ww÷'B6òF†R7V'7F—GWF–öâ—2&÷fVâ&F†W"F†â77VÖVBâ¢¤7F&–Æ—G’v—B—2F†Rw&öærv—B–à¦†&æW72F†B†öÆG2F†R6Æö6²öâW'÷6Râ¢  ¢¢¥F†RvFRâ¢¢F‡&VR76W'F–öç2ÂæBF†RÖ–FFÆRöæR—2"Ôw3¢F†R&÷‚†öÆG27F–ÆÂ7&÷72§7V"×FW†VÂ7FW‚¢£"ãB9r(¼+ž(RÒ¢¢7&÷72F†RÖÂfÆöBæö—6R“²v—F‚6WE6†F÷u6æ†fÇ6R–F†P§6ÖRÖ–ÆÆ–ÖWG&RÖ÷fW2—B¢£ã““BÖÒ¢¢Â6òF†R6æ&V6†W2F†R&÷‚&F†W"F†â&V–ær76W'FVB–çFð¦W†—7FVæ6S²æBÒvÆ²Ö÷fW2—B¢£RF–ÖW2BF†R†öæRw2#2ãB6ÒFW†VÂæBBF†RFW6·F÷w0£ãr6ÒÂWfW'’§V×W†7FÇ’ãFW†VÂ¢¢Âv†–6‚—2F†RÆGF–6R—F6‚ÖV7W&VBg&öÒ÷WG6–FRâ¢¥F†Rf—'7BfW'6–öâöbF†Bf—'7B76W'F–öâFVÖæFVBF†R&÷€¦†öÆB7F–ÆÂ%4ôÅUDTÅ’æBf–ÆVB6÷'&V7B&–rBãrÖÒ¢¢(	BF†R6VçG&R¶VW2F†RvÆ¶W"w0¦6ö×öæVçBÆöærF†R7VâÂv†W&Râ÷'F†öw&†–26ÖW&&7FW&—6W2WfW'’v÷&ÆBö–çBFòF†R6ÖP§FW†VÂæBF†Rw&—GFVâæB6ö×&VBFWF‡26†–gBFövWF†W"âF†R–çf&–çB—2¦7&÷72F†RÖ¢Âæ@¦v÷&ÆBæF—&V7F–öæ—2v†BF†R76W'F–öâ&ö¦V7G2öçFòà ¢¢¥fW&–f–6F–öââ¢¢FööÇ2ö6†V6²ç6†¢¤4„T4²52¢¢â4Ôô´Uõd”Uuõ%CÖÖö&–ÆVöâF†RV&Æ—6†V@¦Ö—'&÷#¢¢£#S276VBÂ"f–ÆVB¢¢(	BF†R6ÖRGvò&öB76W'F–öç2FWfÇ&VG’6'&–W0¢…"Ô%TsV"ò3#æBBÕc"ò33R’ÂæBF†R³2—2W†7FÇ’F†—2&6VÂw2F‡&VRvFW2âF†RFW6·F÷†Æ`¦FöW2æ÷Bf—BF†R'VææW"w2FVâÖÖ–çWFRW"Ö6öÖÖæB6V–Æ–ær…$ôDÔ*rD„R%Tâ%TDtUB’æBF–Bæ÷@§'Vã²WfW'’f–wW&R&÷fR—2ÖV7W&U÷&—fW%öVFvRæÖ§6B#ƒ9sƒöâF†RV&Æ—6†VBÖ—'&÷"à ¢222"Ô%Tsb†"’(	BF†R÷F†W"ƒBR—2äõB6ò×Ææ"F–W2+r¢¤DôäR##bÓ‚Ór(	BF†R&VÖ—6R—2&VgWFVB'’F†RGvòFW7G2F†B6â6WGFÆR—BÂæBF†R&W6–GVÂ—2F†RF÷vâw2÷vâVFvW2¢  ¢¢¥†6S¢¢¢ÆæRÂ&VæFW&W"öæÇ’Âæò&¶R+r¢¥'VææW#¢¢¢–×&÷fR×'VææW"+r¢¤f–ÆW3¢¢ ¦FööÇ2öÖV7W&U÷F–Uö6Æ72æÖ§6†æWr’+rFö72õ$ôDÔæÖF+rFö72õ5DEU2æÖF+p¦&VæFW&W'2÷vV"ö§2ö6†ævVÆöræ§6+r6—FRö6†–6vòóFBò¢¦â¢¤æò&VæFW&W"f–ÆRv26†ævVBÂ&V6W6P¦æ÷F†–ærv2f÷VæBFò6†ævRâ¢  ¢¢¥D„Rå5tU#¢2—†VÇ2öbÃ‚â¢¢F‡&VR&÷†W2öbF†—2f–ÆR(	B"Ô%Tsw27V66W76÷"æ÷FRÀ¥"Ô%Tsb†’f–æF–ær"æBF†R&÷r–âäU…BU(	B6–BF†R&W6–GVÂfÆ–6¶W"v2&6ò×Ææ"FWF€§F–W2"Â'’æÆöw’v—F‚"ÕsV"w2&F6‚ÖW&vRâ—B—2æ÷BâGvò–æFWVæFVçBFW7G26’6òÂæ@¦æV—F†W"†B&VVâ'Vã  §ÂFW7BÂv†B—B6â6VRÂ&W7VÇBÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Â¢§F†RFWF‚gVæ7F–öâ¢¢(	BÆW74WVÆ(i"ÆW76ÂÆÂÖFW&–Ç2Â6†ævW2—†VÂ¢¦öæÇ’¢¢v†W&RGvò7W&f6W2†fRW†7FÇ’F†R6ÖRFWF‚â—B—2F†RFVf–æ—F–öâöb6ò×Ææ"Â6¶VBöbF†R&VæFW&W"Â¢£3bÃƒr‚öbF†Rg&ÖRÖ÷fR(	BæBöæÇ’2öbF†VÒ&RfÆ–6¶W&–ær—†VÇ2ƒã"R’¢¢À§Â¢§F†RæV"ÆæR¢¢(	BrÒ(i"3RÒÂ\9rF†RFWF‚&V6—6–öâÂ†VÇ2ç’F–RFV6–FVB'’&÷VæF–ær&F†W"F†â'’vVöÖWG'’Â¢£cBöbcr–çFW&–÷"F–W27W'f—fR¢£²F†Rv†öÆRg&ÖRvöW2Ã‚(i"ÃRÀ ¥6òF†R&VÖ–æFW"—2æV—F†W"6ò×Ææ"æ÷"&V6—6–öâÖÆ–Ö—FVBâ¢¤—B—2F†R66VæRw2÷vâvVöÖWG&–0¦VFvW2&V–ær&W6×ÆVB'’6ÖW&F†BÖ÷fVB¢¢(	Bv†–6‚—2v†BçF–Æ–6–ær—2Â—2&W6VçB–à¦WfW'’6÷'&V7B&VæFW&W"ÂæB—2æ÷BFVfV7Bâ"Ô%Tsw2æV"ÆæR†BÇ&VG’F¶VâF†R&VÀ¦öæRà ¢¢¤d”äD”är(	BâU„5BD”R•25D$ÄRÂäBD„B•2t…’D„•244TäRtõBt’t•D‚3bÃƒr•„TÅ2ô`¤•Bâ¢¢F†RFWF‚ÖgVæ7F–öâ7v—F6‚Ö÷fW2¢£2ãRRöbF†Rv†öÆRg&ÖR¢¢Â6ò6ò×Ææ"7W&f6W2&P¦WfW'—v†W&R–âF†—2F÷vâ(	BæBæ÷BöæRöbF†VÒ6†–ÖÖW'2âF†R&V6öâ—2F†R&—F†ÖWF–2æö&öG’†@§w&—GFVâF÷vã¢Gvò7W&f6W2B¦W†7FÇ’¢F†R6ÖRFWF‚VçF—6RFòF†R6ÖRfÇVRg&öÒWfW'¦6ÖW&÷6—F–öâÂ6òF†RF–R—2'&ö¶Vâ'’E$rõ$DU"Âv†–6‚—2FWFW&Ö–æ—7F–2æBFöW2æ÷BÖ÷fP§v†VâF†Rf—6—F÷"FöW2â¢¤—B—2F†RäT"F–R(	Bv6ÖÆÆW"F†âöæRFWF‚VçGVÒ(	BF†@¦fÆ–6¶W'2Â&V6W6RF†RVçGVÒ&÷VæF'’—2v†BF†R6ÖW&Ö÷fW2â¢¢F†RGvòÆöö²–FVçF–6Â–â§7F–ÆÂg&ÖRæB&V†fR÷÷6—FVÇ’–âÖ÷F–öâÂæBF†—2&ö¦V7B†B&VVâ&V6öæ–ær&÷WBF†P¦f—'7Bv†–ÆRÖV7W&–ærF†R6V6öæBà ¢¢¤d”äD”är"(	BD„R”å5E%TÔTåC¢Ä”U"u2dôõE$”åB•2D„R4UBôb•„TÅ2D„B4„ätRt„Tâ”õR„”DP¤•Bâ¢¢FööÇ2öÖV7W&U÷F–Uö6Æ72æÖ§6'F—F–öç2F†RfÆ–6¶W"'’v†B—27GVÆÇ’G&vâF†W&R(	@¦W†7B÷væW'6†—ÂFV6–FVB'’ö66ÇW6–öâÂF†R6ÖRv’F†RFWF‚'VffW"FV6–FW2—Bâ@¦g&öÕö&÷fVÂv—F‚F†R6†F÷rÖöfb'’"Ô%Tsb†’w2&W—&VB6öçG&öÃ  §ÂÆ–W"Âfö÷G&–çB‚Â—G2fÆ–6¶W"Â6†&RÂ–çFW&–÷"Â6–Æ†÷VWGFRÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Â7G'V7GW&W2Â#"ÃsRÂSSbÂSã"RÂ3ƒ2Âs2À§ÂG&VW2ÂSbÃScRÂC“ÂCBã2RÂ#Â#ƒÀ§Âw&÷VæBÂs#Ã3CbÂ3RÂ2ã"RÂ"Â#2À§ÂvFW"Âs‚Ã#Â#"Â"ãRÂÂ#À§Â7G&VWG2ÂCrÃ“‚ÂBÂãBRÂÂBÀ§ÂfÆ÷&ÂÂÂãRÂÂÀ§Â¢§VæGG&–'WFVB¢¢Â(	BÂ¢£¢¢Â(	BÂ(	BÂ(	BÀ ¥¦W&òVæGG&–'WFVBæB¦W&ò6öçG&öÂG&–gBÂ6ò—B—2'F—F–öâöbF†Rv†öÆR6WB&F†W"F†â§6×ÆRöb—Bâ¢¥F†R'V–ÆF–æw2æBF†RG&VW2÷vâ“BãRRöbF†RfÆ–6¶W"öârãrRöbF†Rg&ÖR¢¢(	@§v†–6‚—2F†R6†Röb&VFvW2"Âæ÷BF†R6†Röb'7W&f6W2"à ¢¢¤d”äD”är2(	BäBD„RE$”âÕ’õtâd•%5B”å5E%TÔTåBÂt„”4‚•2t…’d”äD”äräTTDTBD„RDUD€¤eTä5D”ôââ¢¢F†R–çFW&–÷&6öÇVÖâ&÷fRv2'V–ÇBFò6W&FRF–W2g&öÒVFvW3¢—†VÂv†÷6P¦÷væW"w2fö÷G&–çB7W'&÷VæG2—BöâÆÂV–v‡B6–FW2†2æ÷F†–ærVÇ6RG&vâF†W&RÂ6ò6†ævP¦Æöö¶VBÆ–¶RF†RÆ–W"f–v‡F–ær—G6VÆbâ¢¤—B—2æ÷B6÷VæBÂæBF†Rg&ÖW26’6ò¢¢(	B&öö`¦v–ç7B—G2÷vâvÆÂÂ6†–ÖæW’v–ç7B—G2÷vâ&ööbÂöæR'V–ÆF–ær–âg&öçBöbæ÷F†W"æB§6†–ævÆR6÷W'6Rv–ç7BF†R6÷W'6R&VÆ÷r&RÆÂ¦–çFW&–÷"FòF†R7G'V7GW&W6fö÷G&–çB¢æ@¦ÆÂ÷&F–æ'’6–Æ†÷VWGFW2âcr&–çFW&–÷"F–W2"7W'f—fRB\9r&V6—6–öâ&V6—6VÇ’&V6W6RcBö`§F†VÒvW&RæWfW"F–W2â¢¤fö÷G&–çBFVÆÇ2–÷Rt„ò÷vç2—†VÂæB6ææ÷BFVÆÂ–÷Rt…’—@¦Ö÷fVB¢¢ÂæBF†R6öÇVÖâ—2¶WBÂv—F‚F†—26fVB&–çFVB&W6–FR—BÂ&V6W6RF†R÷væW'6†—†Æ`¦—2W†7BæBW6VgVÂà ¢¢¤d”äD”ärB(	BÖV7W&U÷&—fW%öVFvRæÖ§6w2$ä²Ô4²4õTåE2D„R4µ’2tDU"â¢¢—G2vFW"FW7B—0¦"â"²bbbrâ&ÂæB§VÇ’6·’76W2—C¢ÖV7W&VBöâF†R6ÖRg&ÖRÂ¢§&÷w2(	3#&RÃ#ƒ ¦öbÃ#ƒ'vFW&—6‚"¢¢Â6ò&æµ÷†Ò32Ã3#‚—2Ö÷7FÇ’F†R†÷&—¦öâæBWfW'’&ööbæB6æ÷§6–Æ†÷VWGFRv–ç7B—BâF†RvFR—2§6†&R¢Â6ò&÷F‚†ÇfW2&R–æfÆFVBæB—B†2æ÷B&VVà§&VF–ærfÇ6VÇ’(	B'WB¢¢#sƒBöbF†R&æ²Æ–æRfÆ–6¶W'2"—2æ÷B7FFVÖVçB&÷WBF†R&—fW"¢¢Âæ@§F†RçVÖ&W"6†÷VÆBæ÷B&RV÷FVB2öæRâF†RÆ–W"fö÷G&–çG2–âF†RFööÂ&÷fR&Rv†B&VÀ¦&æ²Ö6²v÷VÆB&R'V–ÇBg&öÓ¢F†R&÷VæF'’v†W&RF†RvFW&fö÷G&–çBÖVWG2F†Rw&÷VæFöæRà¤æ÷Bf—†VB†W&R(	B—B—2"Ô%Tsw2vFRæB6†æv–ær—G2FVæöÖ–æF÷"6†ævW26†—VBF‡&W6†öÆBÀ§v†–6‚—2—G2÷vâ&6VÂà ¢¢¥fW&–f–6F–öââ¢¢FööÇ2ö6†V6²ç6†¢¤4„T4²52¢¢â4Ôô´Uõd”Uuõ%CÖÖö&–ÆVöâF†RV&Æ—6†V@¦Ö—'&÷"âF†RFW6·F÷†ÆbFöW2æ÷Bf—BF†R'VææW"w2FVâÖÖ–çWFRW"Ö6öÖÖæB6V–Æ–ærŒ*rD„R%Tà¤%TDtUB’æBF–Bæ÷B'Vã²WfW'’f–wW&R&÷fR—2ÖV7W&U÷F–Uö6Æ72æÖ§6B#ƒ9sƒöâF†P§V&Æ—6†VBÖ—'&÷"Â6öçG&öÂ‚æB&WGW&â×Fò×÷6R‚öâWfW'’'Vâà ¢¢¥v†B—2ÆVgBöb"Ô%TsbÂæB—B—2æ÷B&VæFW&W"&6VÂâ¢¢F†R3bÃƒr6ò×Ææ"—†VÇ2&P§7F&ÆRÂ'WBF†W’&RGvò7W&f6W2öb÷76–&Ç’F–ffW&VçB6öÆ÷W'2G&vâBF†R6ÖRFWF‚Âv—F€¦G&r÷&FW"–6¶–ærF†Rv–ææW"(	B6ò§v†–6‚¢7W&f6Rf—6—F÷"6VW2F†W&R—2&&—G&'’WfVâF†÷Vv€¦—B—27FVG’âv†WF†W"F†B—22ãRRöbF†Rg&ÖR–çFVBF†Rw&öær6öÆ÷W"—2VW7F–öâ&÷W@§F†RtTôÔUE%’ÂæVVG2&¶RÂæB—2¢¥"Ô%Tsb†2’¢¢&VÆ÷rà ¢222"Ô%Tsb†2’(	B2ãRRöbF†Rg&ÖR—2Gvò7W&f6W2BöæRFWF‚+r¢¥Tä4Ä”ÔTB+r÷VæVB##bÓ‚Ór'’"Ô%Tsb†"’+räTTE2ôäR$´R+rVff÷'C¢Ò¢  ¥F†RFWF‚ÖgVæ7F–öâ7v—F6‚Ö÷fW2¢£3bÃƒr—†VÇ2öbÃ#BÃ×—†VÂg&ÖR¢¢âWfW'’öæRöbF†VÐ¦—2Æ6Rv†W&RGvò7W&f6W26—BBW†7FÇ’F†R6ÖRFWF‚¦æB&Ræ÷BF†R6ÖR6öÆ÷W"¢(	B–`§F†W’ÖF6†VBÂF†R7v—F6‚6÷VÆBæ÷B†fRÖ÷fVBF†R—†VÂâG&r÷&FW"FV6–FW2v†–6‚öæRF†P§f—6—F÷"6VW2ÂæBG&r÷&FW"—2&÷W'G’öbF†R&F6‚Âæ÷BöbF†R'V–ÆF–ærà ¤—B—27F&ÆRÂ6ò—B—2æ÷BfÆ–6¶W"æBæ÷BF†—2&6VÂâ—B—2VW7F–öâ&÷WBF†RÖöFVÇ3¢v†–6€§—'2öb7W&f6W2&R6ö–æ6–FVçBÂ—2—BF†R6ÖR—"öâWfW'’&6†WG—RÂæB—2F†R7W&f6P§F†B7W'&VçFÇ’v–ç2F†RöæRF†R&V6÷&B–çFVæG3ò7F'B'’GG&–'WF–ærF†÷6R—†VÇ2F†Rv¦ÖV7W&U÷F–Uö6Æ72æÖ§6GG&–'WFW2fÆ–6¶W"ÂF†VâÆöö²BF†RvVæW&F÷"F†BVÖ—G2F†R—"à¢¢¤æVVG2&¶R–bF†Rç7vW"—2FòÖ÷fRf6R¢¢Âv†–6‚—2v‡’—B—2æ÷BföÆFVB–çFò†"’à ¢222"Ô%Tsb†3"’(	Bv†Bf–v‡G2”å4”DRÆ–W"+r¢¤å5tU$TB##bÓ‚Ó#2'’BÓ2+ræ÷F†–ærF†W&R—2FVfV7B¢  ¦ÖV7W&U÷F–Uö6Æ72æÖ§67Æ—G2V6‚Æ–W"w2fÆ–6¶W"–çFò4”Ä„õTUEDR6†&R‡F†R&÷VæF'¦v–ç7BWfW'—F†–ærVÇ6RÂv†–6‚ç’6ÖW&&W6×ÆW2’æBâ”åDU$”õ"6†&RÂv†W&RF†RÆ–W"w0¦÷vâfö÷G&–çB7W'&÷VæG2F†RÖ÷f–ær—†VÂöâÆÂV–v‡B6–FW2âF†R–çFW&–÷"6†&Rv2&VB2¦¦Æ–W"f–v‡F–ær—G6VÆb¢æBBÓ2v2&RÖ–ÖVBB—C¢3s‚öâ7G'V7GW&W6Â#SröâG&VW6à ¦FööÇ2öF–væ÷6Uö–çFW&–÷%öfÆ–6¶W"æÖ§66·2v†BF†RDUD‚d”TÄBFöW2BV6‚öbF†÷6R—†VÇ2À¦'’†÷Föw&†–ær6¶VBÖFWF‚72BF†R&6R÷6RæBBF†RçVFvVB÷6RâF‡&VRç7vW'2&P§÷76–&ÆRæBF†W’&RFöÆB'Bv—F†÷WBç’W"×7W&f6RF‡&W6†öÆC  ¢Òâ¢¦–çFW&æÂVFvR¢¢(	BFWF‚%$T²–ç6–FRF†RÆ–W"w2÷vâfö÷G&–çBâ'&V²—26V6öæ@¢F–ffW&Væ6R†ÆB‚Ó’²B‚³’Ò,+vBƒ—Æ’Âv†–6‚—2ãöâç’ÆæR†÷vWfW"7FVWÇ’—B—26VVà¢æBÆ&vRv†W&RF†R7W&f6R6†ævW2Â6òw&¦–ær&ööb6ææ÷B&RÖ—7F¶Vâf÷"âVFvRà¢Ò¢¦FWF‚&V÷&FW"¢¢(	BÆö6ÆÇ’6Öö÷F‚FWF‚ÂæBF†Rg&öçBÖÖ÷7B7W&f6Rã2ÒæV&W"÷"gW'F†W ¢gFW""ÖÒçVFvRâGvò7W&f6W27vVBâF†—2—2F†Rf–v‡BF†R&6VÂv2÷VæVBf÷"à¢Ò¢¦æV—F†W"¢¢(	B6ÖRF—7Fæ6RÂ6ÖR6†RÂF–ffW&VçB6öÆ÷W#¢6†F–ærÂæ÷BvVöÖWG'’â¢æV"Ö6÷Ææ"¢Öf–v‡BÇ6òÆæG2†W&RÂ&V6W6R—"ÖÒ'B7v2v—F†÷WBÖ÷f–ærF†P¢FWF‚Â6òF†—26Æ72—2v†W&R7V6‚f–v‡Bv÷VÆB†fRFòV"à ¥&VBBg&öÕö&÷fVÂ#ƒ9sƒÂ"ÖÒçVFvRÂ6†F÷rÖöfb'’"Ô%Tsb†’w2&W—&VB6öçG&öÂÀ¦6öçG&öÂ‚æB&WGW&âƒ  ¦ ¦Æ–W"–çFW&–÷"–çFW&æÂVFvRFWF‚&V÷&FW"6ÖR7W&f6RæòFWF€§7G'V7GW&W23s3C’ƒ“BR’ƒR’ƒR’#§G&VW2#Sr#S"ƒ“‚R’ƒR’ƒR’P¦w&÷VæBs‚sRƒ“bR’ƒR’ƒR’0¦  ¢¢¤æ÷BöæR—†VÂ–âV—F†W"Æ–W"—2FWF‚&V÷&FW"ÂæBæ÷BöæR—26†F–ærâ¢¢Gvò6öçG&öÆÆV@§FövvÆW26öæf—&Ò—Bg&öÒF†R÷F†W"6–FRâ7WW'6×Æ–ær†FWf–6R—†VÂ&F–ò(i"#¢f÷W"F–ÖW2F†P§6×ÆW2ÂF†R6ÖRvVöÖWG'’æBF†R6ÖR6†F–ær’ÆVfW2c2öb3s7G'V7GW&W2‚æB‚öb#Sp§G&VW2‚Ö÷f–ær(	Bƒ>(	3“2R†VÆVBÂv†–6‚—2v†B6÷fW&vRÖ&÷VæBVFvRFöW2æBv†BFWF€§&V÷&FW"6ææ÷BFòÂ6–æ6RWfW'’W‡G&6×ÆRvWG2F†R6ÖRw&öærç7vW"âvö–ærÖGFRƒ€¦ÖFW&–Ç2B&÷Vv†æW72ÂÖWFÆæW72(	BF†R7V7VÆ"Æö&RvöæRÂWfW'’fW'FW‚v†W&R—Bv2¦6†ævW2cBÃSs"‚öbF†R–7GW&RæB†VÇ2¢¦æ÷F†–ær¢£¢3s(i"3sæB#Sr(i"#Sbà ¥F†RæòFWF†6öÇVÖâ—2F†R6ÖRf–æF–ærv–â&F†W"F†âv–â—BâF†÷6R—†VÇ2&VBF†P¦f"ÆæRv†W&RF†V—"Æ–W"—2G&vâÂ&V6W6R6¶VBFWF‚†÷Föw&†VBF‡&÷Vv‚Õ4—2¤$ÄTäBöbF†R6×ÆW2r'—FW2ÂæBF†R6¶–ær—2æ÷BÆ–æV"7&÷72—G2f÷W"6†ææVÇ2â—†VÀ§v†÷6RFWF‚6ææ÷B&RFV6öFVB—2—†VÂv—F‚Ö÷&RF†âöæR7W&f6R–â—Bà ¢¢¥6òF†R–çFW&–÷"÷6–Æ†÷VWGFRF—67&–Ö–æF÷"FöW2æ÷BÖVâv†B—G2æÖR6—2â¢¢–çFW&–÷$öf ¦¶æ÷w2öæRÆ–W"w2÷WFÆ–æRv–ç7BF†R&W7BöbF†R66VæS²—B6ææ÷B6VRF†R&÷VæF'’&WGvVVâGvð§7W&f6W2ôbF†BÆ–W"(	BöæR7&÷vâ&V†–æBæ÷F†W"Â6†–ÖæW’v–ç7B—G2÷vâ&ööbÂ†÷W6P¦v–ç7BF†R†÷W6R&V†–æB—BâF†÷6R&R6–Æ†÷VWGFW2FöòÂæB“N(	3“‚RöbF†R&–çFW&–÷""6÷VçB—0¦ÖFRöbF†VÒâv†B—2ÆVgBöb"Ô%TsbBg&öÕö&÷fV—3¢#‚W†7FÇ’6÷Ææ"†"’Â‚ö`§6VÆbÖf–v‡B††W&R’ÂæBF†R&W7B—2F†RF÷vâw2÷vâVFvW2&V–ær&W6×ÆVBà ¢¢£##bÓ‚Ó#‚(	BD„R”å5E%TÔTåBäõr$Uõ%E2D„•25Ä•B•E4TÄb…BÓSb’â¢¢WfW'—F†–ær&÷fRv0¦ÖV7W&VBv—F‚6V6öæBFööÂæBF†RÖV7W&VBFööÂv2FVÆ–&W&FVÇ’ÆVgBÆöæRÂ&V6W6R6Æ÷6–ær§F–6¶WB'’&Ww&—F–ærF†R–ç7G'VÖVçBF†BÖV7W&VB—B—2F†RöæRÖ÷fRF†—2&ö¦V7BFöW2æ÷BÆÆ÷rà¤f—fRF—2ÆFW"ÖV7W&U÷F–Uö6Æ72æÖ§6v27F–ÆÂ&–çF–ær”åDU$”õ"DõDÃ¢âââF†R—†VÇ2v†W&R¦Æ–W"f–v‡G2•E4TÄfÂ6òç–öæR&VF–ærF†R–ç7G'VÖVçB&F†W"F†âF†—2&÷‚&VBF†R&VgWFVB6Æ–Ð®(	BæBF†R6öÇVÖâw2æÖR76W'FVB—BFöòâ—Bæ÷r&–çG2F†R7Æ—B&W6–FRF†R6÷VçBÂg&öÐ¦FööÇ2öFWF…öf–VÆBæÖ§6¢BÓ2w2F—67&–Ö–æF÷"ÂW‡G&7FVB6òF†RGvò–ç7G'VÖVçG26ææ÷Bç7vW §F†R6ÖRVW7F–öâF–ffW&VçFÇ’âF†R6öÇVÖâ—26ÆÆVB5U%$õTäDTFÂv†–6‚—2v†B—BÖV7W&W2à ¢¢¤æ÷F†–ærv2&R×F‡&W6†öÆFVBæBæò&6VÆ–æRÖ÷fVBâ¢¢F†R7W'&÷VæFVB6÷VçG2&R–FVçF–6ÂÂ—†VÀ¦f÷"—†VÂBÆÂ6—‚Æ–W'2ÂFòF†R'VâF¶Vâ–ÖÖVF–FVÇ’&Vf÷&RF†R6†ævRâ&VB2&÷fR(	BF†P§V&Æ—6†VBÖ—'&÷"Âg&öÕö&÷fVÂ#ƒ9sƒÂ"ÖÒçVFvRÂ6†F÷rÖöfb'’"Ô%Tsb†’w2&W—&V@¦6öçG&öÂÂ6öçG&öÂ‚æB&WGW&â‚(	Bv—F‚&÷F‚FööÇ2'VâF†R6ÖRgFW&æööâöâF†R6ÖRÖ—'&÷#  ¦ ¢ÖV7W&U÷F–Uö6Æ72æÖ§2F–væ÷6Uö–çFW&–÷%öfÆ–6¶W"æÖ§0¦Æ–W"7W'&÷VæFVBVFvR&V÷&FW"6ÖRæöFWF‚–çFW&–÷"VFvR&V÷&FW"6ÖRæöFWF€§7G'V7GW&W2C#C"’C#C"§G&VW2#3#‚2#3#‚0¦w&÷VæBcbcRsrsB0§7G&VWG2(	B(	B(	B(	B(	@§vFW"22(	B(	B(	B(	B(	@¦fÆ÷&(	B(	B(	B(	B(	@¦  ¦7G'V7GW&W6æBG&VW6w&VR—†VÂf÷"—†VÂâw&÷VæFFöW2æ÷BÂæBF†RF–ffW&Væ6R—2F†RGvð§FööÇ2rÄ”U"Ä•5E2&F†W"F†âF†RF—67&–Ö–æF÷#¢—†VÂ—2GG&–'WFVBFòF†Rd•%5BÆ–W"v†÷6P¦fö÷G&–çB6Æ–×2—BÂæBÖV7W&U÷F–Uö6Æ766'&–W27G&VWG6ÂfÆ÷&æBvFW&Âv†–6€¦F–væ÷6Uö–çFW&–÷%öfÆ–6¶W&FöW2æ÷B(	B6òVÆWfVâ—†VÇ2F†÷6RÆ–W'2÷vâ†W&RfÆÂFòw&÷VæF §F†W&Râ&÷F‚&VF–æw26’F†R6ÖRF†–ær&÷WBF†VÒà ¢¢¥F†R6†&W2†öÆBv–ç7B##bÓ‚Ó#3²F†R6÷VçG2Fòæ÷BÂæBF†B—2F†RF÷vâw&÷v–ærâ¢ §7G'V7GW&W23s(i"C#ÂG&VW2#Sr(i"#3Âw&÷VæBs‚(i"sr÷fW"f—fRF—2öb6öçFVçBâF†P¦–çFW&æÂÖVFvR6†&R&VG2“Rò“Bò“‚Rv–ç7B“Bò“‚ò“bRÂæBF†R6VÆbÖf–v‡B6÷VçB—0¢¢£–âWfW'’Æ–W"öâ&÷F‚FFW2¢¢(	BF†—2'Vâw2F÷FÂ—2¢£öbs37W'&÷VæFVB—†VÇ2¢¢âv†@§F†—2&÷‚6Æ–×2—2F†R6†&RæBF†R¦W&òÂæB&÷F‚7W'f—fRF÷vâF†Bw&WrVæFW"F†VÒà ¢222"Ô%Tsb†32’(	BF†R„ôäRw2†ÆböbF†R6ÖRVFvW2+r¢¤å5tU$TB##bÓ‚Ó#B'’BÓSr+rÕ4æ÷r6†—2öâWfW'’FWf–6R¢  ¤WfW'—F†–ær&÷fRv2ÖV7W&VBB#ƒ9sƒöâF†RDU4µDõ&ö÷BÂv†–6‚†2†BçF–Æ–3¢G'VV §6–æ6RÖ–ÆW7FöæRâÖ–âæ§6&VBçF–Æ–3¢6ö'6VÂ6òF†RFWf–6RF†Bv2äõBÖV7W&VBv0§F†RöæÇ’öæRG&v–ærF†W6RVFvW2v—F‚æò×VÇF—6×Æ–ærBÆÂ(	BæBÖö&–ÆR—2&VÆV6RvFR†W&Rà ¢¢¤f—'7BÂF†R–ç7G'VÖVçB6÷VÆBæ÷B6VR†öæRâ¢¢ÖV7W&U÷F–Uö6Æ72æÖ§6w2D”Uõd”Uuõ%CÖÖö&–ÆV ¦÷Vç2Æ–âæWuvR‡²f–Ww÷'BÒ–²&VfW'5F÷V6‚‚–6·2f÷"‡ö–çFW#¢6ö'6R–÷ ¦Ö…F÷V6…ö–çG2âbb–ææW%v–GF‚Â“ÂæB¢¦f–Ww÷'B6F—6f–W2æV—F†W"¢¢â6òF†RW†—7F–æp¢&Öö&–ÆR"&VF–ærv2F†RFW6·F÷&VæFW&W"–âæ'&÷rv–æF÷r(	BçF–Æ–3¢G'VVÂFWF–Ã¢gVÆÆÀ§F†Rö–çFW"ÖÆö6²&6¶VæBâ6ÖR6†R2BÓ‚w2f–æF–ærv–ç7B5t$Eõd”Uuõ%CÖÖö&–ÆVà¦FööÇ2öÖV7W&U÷†öæUöæÖ§6W6W26öçFW‡Bv—F‚†5F÷V6†æBFWf–6U66ÆTf7F÷#¢&ÂF†P§&VÆV6RvFRw2÷vâÂæB&–çG2ö–çFW#¢6ö'6VÂF†R&W6öÇfVBFWF–ÂÆWfVÂæBF†R&VæFW&W"w0§—†VÂ&F–ò6òF†R&ö÷B6ææ÷B&R77VÖVBà ¢¢¤æBF†VâF†Rö'f–÷W2çVÖ&W"ö–çFVBF†Rw&öærv’â¢¢3“9ssƒÂV&Æ—6†VBÖ—'&÷"Â"ÖÒçVFvRÀ§6†F÷rÖöfb'’"Ô%Tsb†’w2&W—&VB6öçG&öÂÂ6öçG&öÂ‚æB&WGW&âƒ  ¦ §7FF–öâfÆ–6¶W"‚†&BfÆ—2†FVÇFãÒcBöb#SR’v÷'7BBÖVâ@¦g&öÕö&÷fRSbÓâ#Cƒ"#RÓâRÓâ#‚RãbÓâbã€¦Æ¶UöÖ&¶WBCƒC2Óâs3#BÓâCÓâ3rBã‚Óâbã@¦  ¢¢¥F†RfÆ–6¶W"4õTåB&—6W23RRW&–ÂæBSRBW–R†V–v‡Bv†VâÕ4—27v—F6†VBöâ¢¢(	BF†P¦6÷VçBF†—2f–ÆRV÷FW2–âF‡&VR6W&FR&÷†W22F†RÖV7W&RöbF†RFVfV7Bâ—B&—6W2&V6W6R§'F–Â&W6×ÆRF÷V6†W2Ö÷&R—†VÇ2F†âv†öÆRfÆ—FöW2âv†B6öÆÆ6W2—26WfW&—G“¢ÆÂC§—†VÇ2F†BvW&R7v–ær7W&f6R÷WG&–v‡B7F÷ÂæBF†Rv÷'7B6–ævÆR—†VÂÖ÷fW2&÷WBV'FW ¦2f"â¢¤&6VÂF†B†BÖV7W&VBöæÇ’F†R6÷VçBv÷VÆB†fR&VgW6VBF†Rf—‚öâ—G2÷và¦Wf–FVæ6R¢¢Âv†–6‚—2"Ô%Ts"w2ÆW76öâ'&—f–ærg&öÒæWrF—&V7F–öã¢ÖV7W&R&Vf÷&R6†ö÷6–ærÂæ@¦&R&VG’f÷"F†R&–ÖR7W7V7Bw2÷vâÖWG&–2Fò&RF†RÖ—6ÆVF–æröæRà ¢¢¤6÷7BÂæB—G2Æ–Ö—Bâ¢¢FVâ66VæRæ6†÷'2Â6Æö6²†VÆBÂ&VE—†VÇ6fVæ6RÂô"ô¢¢¢³SbãBR¢ ¦öbg&ÖRƒ#BÃCSr(i"C2Ã#ƒ2×2’ÂF†R'VææW"G&–gF–ær³#bã2R&WGvVVâ—G2÷vâGvò76W3²Gvð¦f÷W"×7FF–öâ&WVG2&VB³C’ã2RæB³sãbRâG&vâF‡&÷Vv‚7v–gE6†FW"Â4ôeEt$R&7FW&—6W §&W6öÇf–ærWfW'’6×ÆRöâF†R5R(	BF†R†'6†W7Bv—FæW72F†W&R—2f÷"F†—26†ævRÂ6òF†Rf–wW&P¦—2âWW"&÷VæBâ¢¥†öæR×6–Æ–6öâ6÷7B—2æ÷BÖV7W&VBæBæ÷B6Æ–ÖVBâ¢¢F†Rf—6—F÷"w2W†—7F–æp¥&VæFW"×VÆ—G’6öçG&öÂv2F–ÖVB&F†W"F†â76W'FVC¢B—†VÂ&F–òv—F‚Õ4F†Rg&ÖR—0£n(	3’R4„TU"F†âF†R&F–òÓãRg&ÖRF†B6†—VB&Vf÷&RÂ7F–ÆÂçF–Æ–6VBâÆ–v‡F7F—2F†P¦fÆö÷"à ¢¢¤6V6öæBf–æF–ær&÷WBF†R÷væW'6†—–ç7G'VÖVçBÂg&öÒ'Vææ–ær—BBU”R„T”t…Bf÷"F†Rf—'7@§F–ÖRâ¢¢F†Rfö÷G&–çB'F—F–öâ†BöæÇ’WfW"&VVâ&VBg&öÒF†R—"ÂæB—G2÷vâ†VFW"v&ç0§F†BÆ&vR÷fW&Æ&WGvVVâGvòÆ–W'2—2'Vr–âF†RFööÂ&F†W"F†âf–æF–ærâW&–ÆÇ’F†P¦÷fW&Æ2&R(	33öbÃSbæBF†R'F—F–öâ—26÷VæBâBÆ¶UöÖ&¶WFF†Rw&÷VæBw2fö÷G&–ç@¦÷fW&Æ2F†R7G&VWG2röâ¢£"ÃC3böb—G2"Ãcr¢¢fÆ–6¶W&–ær—†VÇ2(	BF†R7G&VWBÆ–W"—26¶–âôà§F†R†V–v‡Ff–VÆBÂ6ò†–F–ærV—F†W"Ö÷fW2F†R6ÖR—†VÇ2âV6‚—†VÂ—27F–ÆÂ6÷VçFVBöæ6RÂ'W@§F†R7&VF—B&WGvVVâF†÷6RGvòÆ–W'2fÆÇ2FòF†RÄ”U%2Æ—7B÷&FW"&F†W"F†âFòö66ÇW6–öâÂ6ð§F†RW–RÖ†V–v‡B7G&VWG6öw&÷VæF7Æ—B—2æ÷Bâ÷væW'6†—6Æ–Òâæ÷F†–ær&÷fRFWVæG2öâ—C §F†Rg&ÖRF÷FÇ2&RGG&–'WF–öâÖg&VRà ¢¢¤&VÖ—6R6÷'&V7FVBöâF†Rv’â¢¢BÓSr†VÆBF†B†öæR—2&6VBBãR&F†W"F†â""à¥F†R&ö÷B×F–ÖR6ö'6RòãR¢&—27WW'6VFVB'’6WE—†VÅ&F–ò„ÖF‚æÖ–â†G"Â‡VBç6WGF–æw0¢çVÆ—G’’–æBVÆ—G–FVfVÇG2FòãRöâ$õD‚ÆFf÷&×2(	B6òF†R†öæR&W÷'G2ãRBG" ¦æBF†RFW6·F÷ãBG"âF†R†öæRv2Ç&VG’7WW'6×Æ–ærÖ÷&RF†âF†RFW6·F÷²v†B—@¦Æ6¶VBv2Õ4à ¢222"Ô%Tsb†"’(	BF†R&6VÂ2w&—GFVâÂ¶WBf÷"F†R&V6÷&@ ¢¢¥F†R7W7V7BÆ—7B—2öæR6†÷'FW"æBF†R&VÖ–æFW"—2ÖV7W&VB¢£¢v—F‚F†R6†F÷rÖ7v—F6†V@¦öfb'’F†R&W—&VB6öçG&öÂÂg&öÕö&÷fV7F–ÆÂfÆ–6¶W'2¢£Ã‚¢¢—†VÇ2æ@¦FW66VæEöÖ–å÷7FVÖ¢£"Ã‚¢¢VæFW"F†R"ÖÒçVFvRâF†÷6R&RF–W2ÂæB"ÕsV"†2Ç&VG¦6†&7FW&—6VBF†R6Æ72g&öÒF†R÷F†W"F—&V7F–öâ(	BÖW&v–ær6—‡FVVâ&F6†W2–çFòöæRÖ÷fVB“C §—†VÇ2Â¢&ÆÂöbF†VÒFWF‚F–W2&WGvVVâ6ò×Ææ"7W&f6W2öbF–ffW&VçBÖFW&–Ç2"¢à ¢¢¥7F'Bv†W&R"ÕsV"VæFVBÂæ÷Bv†W&R"Ô%TsF–Bâ¢¢F†R6æF–FFW2ÆVgB&RF†R'V–ÆF–æw2p¦F÷V&ÆU6–FVf6W2ÖVWF–ærB6÷Ææ"6VÒÂF†R6æ÷–W2rÇ†×FW7FVB6&G2÷&FW&–æp¦F–ffW&VçFÇ’ÂæBF†R6öæf–FVæ6R×f–WrGG&–'WFRFƒ²F†R6†F÷rÖ—27VçBâÒÖ&÷‚ÖG&–gF—0§F†R6†Röb–ç7G'VÖVçBF†Bv÷&·2†W&R(	B†öÆBF†R6ÖW&7F–ÆÂæBÖ÷fRF†RöæRF†–ærVæFW §7W7–6–öâ(	BæBÒÖæò×7Vâ×6†F÷v—2æ÷r6öçG&öÂF†B&V6†W2F†R&VæFW"Â6ò'Vâ6à§7V'G&7BF†R6†F÷rw26†&R†öæW7FÇ’&F†W"F†â77VÖ–ær—Bà ¢222"Ô%Tsb(	BF†R&6VÂ2w&—GFVâÂ¶WBf÷"F†R&V6÷&@ ¢¢¥VæFW"F†R"ÖÒçVFvRÂv—F‚F†R&æ²Æ–æRf—†VBÂÃs>(	3Ãƒƒ2—†VÇ2öbWfW'’W&–Âg&ÖR7F–ÆÀ¦6†ævR¢¢(	B66GFW&VB÷fW"&öög2ÂvÆÇ2æBG&VR6æ÷–W2Âæ÷B÷fW"F†Rw&÷VæB&WGvVVâF†VÒâF†P¦6öçG&öÂ—2Â6ò—B—2æ÷Bæö—6Râ—B—2F†R6ÖR6Æ72öbFVfV7B"Ô%Ts§W7B6Æ÷6VBBF†P§vFW&Æ–æS¢6öÖWF†–ær–âF†Rg&ÖR—2FV6–FVB'’F–RÂæBF†RF–R—2æ÷B7F&ÆRà ¢¢¥7F'B'’&÷f–ær–÷W"–ç7G'VÖVçBâ¢¢"Ô%Tsw26†F÷rÖÖ7W7V7B—2VçFW7FVBÂæ÷B&VgWFVC ¦ÖV7W&U÷&—fW%öVFvRæÖ§2ÒÖæò×7Vâ×6†F÷vG&÷27Vâæ67E6†F÷vgFW"&ö÷BæB6†ævW2¢£—†VÇ0¦öbF†RG&vâg&ÖR¢¢Â6òF†R'VâF†B&6ÆV&VB"F†R6†F÷rÖ6ÆV&VBæ÷F†–ærâFW7BF†@§&V6†W2F†R&VæFW"†2Fò&V'V–ÆBF†R6†F÷r7FFR(	B÷"F†R66VæR(	B&F†W"F†âfÆ—–ærfÆröà¦Æ–v‡Bv†÷6RÖFW&–Ç2&RÇ&VG’6ö×–ÆVBâ¢¤ÆæBF†B6öçG&öÂw&VVâ&Vf÷&RV÷F–ærç¦çVÖ&W"¢¢ÂæBF†R&6VÂw2f—'7B6öÖÖ—B—2F†B6öçG&öÂÂæ÷Bf—‚à ¢¢¤6æF–FFW2ÂæöæRöbF†VÒÖV7W&VC¢¢¢F†R6†F÷rÖw2FW†VÂw&–BÖ÷f–ærv—F‚F†R6ÖW&²F†P¦'V–ÆF–æw2rF÷V&ÆU6–FVf6W2ÖVWF–ærB6÷Ææ"6VÓ²F†RG&VR6æ÷–W2rÇ†×FW7FVB6&G0¦÷&FW&–ærF–ffW&VçFÇ“²F†R6öæf–FVæ6R×f–WrGG&–'WFRF‚âFööÇ2öÖV7W&U÷&—fW%öVFvRæÖ§6F¶W0¦$•dU%õ5DD”ôå6æBw&—FW2ÖvVçFfÆ–6¶W"Ö6²v—F‚ÒÖ÷WFÂv†–6‚—2†÷rF†R&æ²Æ–æRv0§6W&FVBg&öÒF†R&W7B'’W–R–âF†Rf—'7BÆ6Rà ¢¢¥'VææW#¢¢¢ÆæRÂ&VæFW&W"öæÇ’Âæò&¶Râ—BÖ’'Vâ&W6–FRç’F÷vâ&6VÂà ¥&W÷'FVB'’F†R÷væW"##bÓ‚ÓC¢fÇ––ær÷fW"F†R&—fW"Â—G2VFvW2fÆ–6¶W"âÆÖ÷7B6W'F–æÇ¢¢§¢Öf–v‡F–ær&WGvVVâF†RvFW"ÆæRBF†RFGVÒ‡’Ò’æBF†RFW'&–â7&÷76–ær—B¢¢(	BF†P§vFW&Æ–æR—2G&vâ'’F†RFWF‚'VffW"&F†W"F†â'’G&6VB÷WFÆ–æRÂv†–6‚—2FVÆ–&W&FP¢†FW'&–âæ§6†VFW#¢F†R&æ²Æ–æR•2v†W&RF†Rw&÷VæB7&÷76W2’ÒÂ6òF†RvFW&Æ–æR6à¦æWfW"G&–gB÷WBöb7FWv—F‚F†RG&6R’æB—2W†7FÇ’F†R6öæf–wW&F–öâF†B6ò×Ææ §7W&f6W2f–v‡B–âBFWF‚Ö'VffW"&V6—6–öâÂv÷'6RF†RgW'F†W"F†R6ÖW&—2g&öÒF†P§7W&f6R(	B†Væ6R'v†VâfÇ––ær"à ¢¢¤÷væVB'’"ÕsR¢¢Âv†–6‚—2F†R&6VÂF†BF÷V6†W2F†RvFW"7W&f6RâFòæ÷Bf—‚—B–â¦ÆæRÓ"&6VÂ÷"–â76–ærà ¢¢¤6æF–FFRf—†W2Â–âF†R÷&FW"v÷'F‚G'––æs¢¢¢6ÖÆÂöÇ–vöäöfg6WFöâF†RvFW"ÖFW&–Ã°§&—6–ærF†R6ÖW&w2æV&ÆæR†Æ&vRæV"öf"&F–ò—2v†B7F'fW2FWF‚&V6—6–öâ@¦ÇF—GVFR“²÷"Æöv&—F†Ö–2FWF‚'VffW"âv†–6†WfW"—26†÷6VâÂF†R66WFæ6R—2F†B¢§F†P§vFW&Æ–æR7F—2W†7FÇ’v†W&RF†Rw&÷VæB7&÷76W2F†RFGVÒ¢¢(	Bf—‚F†BÖ÷fW2F†P§vFW&Æ–æR†2'&ö¶VâF†RF†–ærF†R7W'&VçBFW6–vâW†—7G2FòwV&çFVRÂæBv÷VÆBæVVB¦Æ–&W'G’VçG'’à ¢¢¥&W&öGV6S¢¢¢fÇ’FòF†Rg&öÕö&÷fVæ6†÷"ÂF†VâFW66VæB6Æ÷vÇ’F÷v&BF†Rf÷&·3²F†P¦VFvW26†–ÖÖW"ÆöærF†R&æ²Æ–æRà ¢ÒÒÐ ¢22²(	B¶Wf–âw2Væ6‚Æ—7Böb##bÓ‚Ó2+r¢¥D„R$”õ$•E’TUTR(	B7FWv&BÂv÷&²F†W6Rf—'7B¢  ¥F†—'FVVâF—&V7F–öç2g&öÒF†R&ö¦V7B÷væW"Âw&—GFVâW2&6VÇ2âvVçB6â–6²W6öÆBà¤V6‚æÖW2—G2f–ÆW2Â—G2Wf–FVæ6RÂ—G2vFRæB—G2G&â7FæF–æröÆ–7’f÷"ÆÂöbF†VÓ ¢¢¦'V–ÆBÆ–&W&ÆÇ’Âw&FR†öæW7FÇ’¢¢(	B6öæ¦V7GW&Æ—2ÆVv—F–ÖFRç7vW"æBF†R6öæf–FVæ6P§f–Wr–çG2—C²F†RGvò'6öÇWFR'VÆW2†æWfW"–çfVçB6÷W&6RÂæWfW"6–ÆVçFÇ’f–ÆÂv’Fð¦æ÷B&VÆ‚â¤fö–B6—&6Æ–æröâ†—7F÷&–6ÂW&fV7F–öã¢FòF†R&V6öæ&ÆR&W7BÂÖ&²F†R&W7BÀ¦Ö÷fRöââ¢öæR&6VÂW"'Vã²ÆVfRF†R÷F†W'2f÷"F†RæW‡BF–6²÷"f÷"–çFW&7F—fR6W76–öç2(	@¦6†V6²v—BÆövf—'7B6ò–÷RFòæ÷BGWÆ–6FR&6VÂÇ&VG’ÆæFVBà ¢¢¤6Æ–×2(	B†÷rGvò'Vç2fö–B'V–ÆF–ærF†R6ÖRF†–ærâ¢¢v—BÆövöæÇ’6†÷w2v÷&²Ç&VG¤ÄäDTBÂv†–6‚—2æò†VÇv–ç7Bv÷&²–âfÆ–v‡C¢F†R66†VGVÆVB7FWv&BæBâ–çFW&7F—fP§6W76–öâ6â&÷F‚7F'BF†R6ÖR&6VÂæBæV—F†W"6â6VRF†R÷F†W"VçF–ÂöæRöbF†VÒW6†W2à¥6ò'VâF¶–ær&6VÂ&–rVæ÷Vv‚Fò&Rv÷'F‚&÷FV7F–ærÖ&·2—G2†VF–æp¢¢¦+r4Ä”ÔTBÆFFSâ(	BDòäõB”4²U¢¢Âw&—FW2öæRÆ–æR6––ærv†ò†öÆG2—BæBv†BFòF¶P¦–ç7FVBÂæB¢§W6†W2F†BFòÖ–æ&Vf÷&R7F'F–ærF†Rv÷&²¢¢(	B6Æ–ÒF†B6—G2VçW6†VBöà¦'&æ6‚&÷FV7G2æ÷F†–ærâ&W7V7Bç’6Æ–Ò–÷Rf–æBâ6Æ–×26''’âW‡—'’ÂæBâW‡—&V@¦öæR—2fö–Bv—F†÷WB6W&VÖöç“¢â&æFöæVB6Æ–Ò×W7Bæ÷B&V6öÖRW&ÖæVçBÆö6²öâ&6VÂà¥6ÖÆÂ&6VÇ2Fòæ÷BæVVBF†—2(	BF†R6÷7Böb6Æ–Ö–ærW†6VVG2F†R6÷7Böb6öÆÆ—6–öâà ¢222³#B(	BÆWBF†Rf—6—F÷"6†ö÷6RF†RÆ–v‡B+r¢¤DôäR##bÓ‚Ór+r÷væW"×&WVW7FVB##bÓ‚ÓB¢  £â¢¥4„•TC¢'&–v‡FæW726Æ–FW"Â7F÷2‡F†R6Æ–'&FVBw&FR’Fò³7F÷ÂFVfVÇBöfbâ¢¢F†P£âFW6–vâVW7F–öâF†R&÷‚ÆVgB÷Vâ—2FV6–FVB(	B¢¦6Æ–FW"ÂæBF†R&VF÷WBæÖW2F†R6Æ–'&FV@£â÷6—F–öâ¢¢&F†W"F†â6†÷v–ær&&R¦W&òÂöâF†RW–RÖ†V–v‡B&V6VFVçBâF†R6V–Æ–ær—2¢¦öæP£â†÷Föw&†–27F÷¢¢&V6W6R7F÷—2F†RVæ—B6÷'&V7F–öâÆ–¶RF†—2—2&÷VæFVB–âÂæ÷B&V6W6P£âöæR7F÷Æöö¶VB&–v‡C²7B—B4U2&öÆÇ2F†R&öög2æBF†R6·’–çFòöæRfÆB†–v†Æ–v‡Bà£à£â¢¤—BF–BäõB†fRFòv—Bf÷"3#Râ¢¢F†R6WVVæ6–æræ÷FR&VÆ÷rv2&–v‡BF†Bv÷&ÆBæ§6—0£âv†B3#R&Ww&—FW2æBw&öærF†BF†—2æVVFVBF†Rf–ÆS¢F†R–B—2öæR6öç7FçB†$4UôU…õ5U$V£âæBöæRÖWF†öBöâF†R&WGW&æVBv÷&ÆBÂ6ò3#R6öæfÆ–7G2v—F‚GvòFF—F–öç2&F†W"F†â£â&Ww&—GFVâf–ÆRâ¢¤6WVVæ6–æræ÷FR—26Æ–Ò&÷WBD”dbÂæB—B6†÷VÆB&R6†V6¶VBv–ç7BF†P£âF–fb&Vf÷&R—BFVfW'2&6VÂf÷"F‡&VRF—2â¢ £à£â¢¥D„Rd”äD”är•2$õUB"Ôu2$TD$4²ÂäõB$õUBÄ”t…Bâ¢¢W‡÷7W&V—2F†Rf—'7B&VF–æröà£âv–æF÷råõö6†–6vóFFv†÷6RW‡V7FVBfÇVRÔõdU2ÂæB—B&W÷'FVBã“Vöâg&ÖRF†B†B§W7@£â6†ævVB'’CR6÷VçG2âö&¦V7Bæ76–væ¢¦–çfö¶W2vWGFW"æB6÷–W2F†RfÇVR¢¢Â6ð£âvWB&öD–B‚–(	Bw&—GFVâ–ç6–FRF†Rö&¦V7Bæ76–vâ†’Â¾(
gÒ–Æ—FW&Â'’"ÔöæRF’V&Æ–W"(	@£â¢¦†2&VVâ6öç7FçB6–æ6R—B6†—VB¢¢â&÷F‚öb"Ôw2&VF&6²vFW276W'BÓÓÒÂ6ò£âg&÷¦Vâ76VB&÷Fƒ²F†RÆ—fVæW72vFR&VG2g&ÖR6–væGW&RæBæWfW"F÷V6†VB—BâF†R6öçG&öÀ£âv2Çv—2Æ—fRæBF†R$Uõ%Böb—G2÷6—F–öâv2F†RFVBF†–ærâf—†VBÂÇW2vFRF†BF†P£â&öB–B&VG2&6²¢£¢¢v†Vâ&—6VBâ¢¥&VBF†—2&Vf÷&RFF–ærç’&VF–ærFòF†R†&æW73 £âç—F†–ærv†÷6Rç7vW"6†ævW2gFW"&ö÷BvöW2–âö&¦V7BæFVf–æU&÷W'F–W6ÂæBâ76W'F–öâF†@£â6âöæÇ’WfW"6VRöæRfÇVR—2æ÷Bâ76W'F–öââ¢ £à£âÖV7W&VBÂÖö&–ÆR3“9ssƒÂV&Æ—6†VBÖ—'&÷#¢öfbB&ö÷B'&–v‡FæW72òW‡÷7W&Rã“V²³7F÷ £âÖ÷fW2F†R,+"6–væGW&R¢¦ÖVâC’ãCÂv÷'7BS¢£²6WD'&–v‡FæW72ƒ’–6Æ×2Fò¢£¢£²&W7F÷&V@£â&W6–GVÂ¢£ãò¢¢âgVÆÂw&—FR×W–âFö72õ5DEU2æÖFà ¢222³#B(	BF†R&6VÂ2w&—GFVâÂ¶WBf÷"F†R&V6÷&@ ¤÷væW"Âöâ&V–ærFöÆB"ÕsÖ¶W2F†R66VæRbRF–ÖÖW"æBF†B†öÆF–ærF†RöÆB'&–v‡FæW72v÷VÆ@¦6öÆÆ6RÆ&VFò&WFVçF–öâFòc"S¢¢$6â–÷RÖ¶RF†—2â÷F–öâ–â6WGF–æw3ò"  ¢¢¤—BF—76öÇfW2F†RG&FRÖöfb&F†W"F†â–6¶–ær6–FRâ¢¢"Õsw2&wVÖVçBf÷"—G2÷vâÖvæ—GVFP¦—26÷VæB(	B&VÂ6·’—2&ÇVRÂæB66Æ–ær—BFò6''’v&ÒÆ×w2ÇVÖ–ææ6RFW7G&÷—2F†RvÆÀ¦6öÆ÷W'2F†RFF6WBFö7VÖVçG2â'WB&6÷'&V7BæBF–Ò"æB&'&–v‡BæBw&öær"—2fÇ6R6†ö–6P§v†VâF†Rf—6—F÷"6â&R†æFVBF†RF–Âà ¢¢¥6WGF–æw2Ç&VG’†2F†R6†Rf÷"F†—2â¢¢‡VBæ§6v—&U&ævR†–BÂÆ&VÂÂ¶W’Âf×B–G&—fW0¦7VVFÂW–T†V–v‡FæBf÷f²2×Væ—G6—2F†R6VÆV7BGFW&ã²WfW'—F†–ærW'6—7G2FF—F—fVÇ¦–çFò6†–6vóFBç6WGF–æw6âæ÷F†–æræWr—2æVVFVB7G'V7GW&ÆÇ’à ¢¢¥F†R&V6VFVçBFò6÷’—2F†RW–RÖ†V–v‡B6Æ–FW"¢¢ÂæB—B—2W†7FÇ’F†R&–v‡BöæRâ—B&–çG0¦(	BW&–öBW–RÆWfVÆv†Vâ—B6—G2öâF†R&W6V&6†VBFVfVÇBÂ¢'6òÖ÷f–æröfb—B—2f—6–&ÆP¦6†ö–6R–ç7FVBöb6–ÆVçBG&–gB"¢†‡VBæ§6’âÆ–v‡B6öçG&öÂæVVG2F†R6ÖRG&VFÖVçC¢F†P¦FVfVÇB÷6—F–öâ—2F†RöæR6Æ–'&FVBv–ç7BfW&–f–VB§VÇ’&—&–R†÷Föw&‚ÂæB—B6†÷VÆ@§6’6òöâ—G2f6Rà ¢¢¥F†RF†–ærF†—2×W7Bæ÷B&V6öÖRâ¢¢F†—2&ö¦V7Bw&FW2WfW'’6Æ–Ò'’Wf–FVæ6Râ'&–v‡FæW70¦6öçG&öÂ×W7B&VB2¢§f–Wv–ær66öÖÖöFF–öâÂÆ–¶RF†RVæ—G2FövvÆR¢¢(	BF†R6ÖR66VæRÂV6–W §Fò6VR(	BæBæWfW"26Æ–Ò&÷WB†÷r'&–v‡Bƒ3Rv2âÆ&VÂ—B6òF†Bæò&VF–æröbF†RT§7VvvW7G2F†R'&–v‡FW"6WGF–ær—2âÇFW&æF—fR&V6öç7G'V7F–öââF†R&—6²—26öæ7&WFS¢f—6—F÷ §v†òÖ÷fW2F†RF–ÂæBF†Vâf÷&×2§VFvVÖVçB&÷WBF†RF÷vâw26öÆ÷W'2—2§VFv–ærVæFW"Æ–v‡@§F†—2&ö¦V7B†2§W7BÖV7W&VB2¢£ãƒl9rF†RÇVÖ–ææ6RæB"ãƒ\9rF†R&VB¢¢öb—G2÷vâ6·’à ¢¢¥F†RæöâÖæVv÷F–&ÆS¢6Æ–'&F–öâ7F—2æ6†÷&VBFòF†RDTdTÅBâ¢¢FööÇ2ö7&—F–5÷6†÷G2æÖ§6À¦FööÇ2öÆ–v‡E÷&ö&RæÖ§6æBWfW'’vFR–â6Öö¶U÷&VæFW&W"æÖ§6ÖV7W&RF†RFVfVÇB6WGF–æræ@¦×W7B¶VWFö–ær6òâ–bvFR6â&RÖFRFò72'’Ö÷f–ærF†—26öçG&öÂÂF†R6öçG&öÂ†2&V6öÖP¦v’FòÆVæFW"f–ÇW&R(	BFBâ76W'F–öâF†BF†RFVfVÇB&VæFW&–ær—2Væ6†ævVB'’F†P§6WGF–ærw2W†—7FVæ6RÂæBF†BF†R†&æW72&VG2F†RFVfVÇB&Vv&FÆW72öb7F÷&VB&VfW&Væ6Rà ¢¢¤äBD„B•"•2äõBTäõTt‚(	B6÷’"Ôw2D„•$B76W'F–öâƒ##bÓ‚Ób’â¢¢"Ô6†—VBF†—0¦W†7B6†Röb6öçG&öÂf÷"F†R&öG2æBf÷VæBF†B&öfbB&ö÷B"ÇW2'F†RFVfVÇB—2Væ6†ævVB ¦&÷F‚72–FVçF–6ÆÇ’v†Vâ6öçG&öÂ—2¢§v—&VBFòæ÷F†–ær¢¢â—BvFW2F‡&VRv—3¢öfbB&ö÷BÀ¢¢§&—6–ær—B6†ævW2F†Rg&ÖR¢¢ÂG&÷–ær—B&W7F÷&W2F†Rg&ÖRâ"Ôw2&÷‚†2F†R6öFRÂF†P¦w&–B—B†BFò&RÖV7W&VBBÂæBF†RçVÖ&W'2à ¢¢¤÷VâFW6–vâVW7F–öâÂv÷'F‚FV6–F–ær&F†W"F†âFVfVÇF–æs¢¢¢Gvò×v’6†ö–6R&WGvVVâæÖV@§&–w2Â÷"6öçF–çV÷W2W‡÷7W&R6Æ–FW"v—F‚F†R6Æ–'&FVBö–çBÖ&¶VCòF†R6Æ–FW"ÖF6†W2F†P¦W–RÖ†V–v‡B&V6VFVçBæB—2g&–VæFÆ–W#²F†RFövvÆR—2†&FW"FòÖ—7&VB2&67W&7’F–Â"à¥&V6öÖÖVæFF–öã¢¢§6Æ–FW"Âv—F‚F†R6Æ–'&FVBFVfVÇBæÖVB–âF†R&VF÷WB¢¢(	B'WB6’v†–6‚v0¦6†÷6VâæBv‡’à ¢¢¥6WVVæ6–æs¢¢¢F†—2F÷V6†W2v÷&ÆBæ§6Âv†–6‚¢¥"3#R&Ww&—FW27V'7FçF–ÆÇ’¢¢â—B×W7BÆæ@¢¢¦gFW"¢¢3#R&W6öÇfW2÷"—Bv–ÆÂ6öæfÆ–7B&FÇ’â—BÇ6òFöW2¢¦æ÷B¢¢Væ&Æö6²3#R(	BF†B"w0§&öBÖvFRf–ÇW&Rö67W'2BF†R¦FVfVÇB¢6WGF–ærÂæB&VfW&Væ6R6öçG&öÂFöW2æ÷B6†ævR—Bà ¢¢¤f–ÆW3¢¢¢&VæFW&W'2÷vV"ö§2÷v÷&ÆBæ§6+r&VæFW&W'2÷vV"ö§2ö‡VBæ§6+r&VæFW&W'2÷vV"ö–æFW‚æ‡FÖÆ ¢‡F†R6öçG&öÂ’+rFööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6†FVfVÇB×Væ6†ævVB76W'F–öâ’+rFö72ö–æFW‚æ‡FÖÆ„†VÇ ¢¢¤66WFæ6S¢¢¢FööÇ2ö6†V6²ç6†w&VVã²F†R6WGF–ærW'6—7G27&÷72&VÆöBæBFöW2æ÷B'&V²à¦W†—7F–ær7F÷&VB6†–6vóFBç6WGF–æw6²F†RFVfVÇB&VæFW&–ær—2'—FRÖ6ö×&&ÆRFò&Vf÷&RF†P§6WGF–ærW†—7FVC²WfW'’7&—F–2æB6Öö¶RÖV7W&VÖVçB7F–ÆÂ&VG2F†RFVfVÇC²F†R&VF÷WBæÖW0§F†R6Æ–'&FVB÷6—F–öã²¢¦Öö&–ÆR3“9ssƒ—2&VÆV6RvFR¢¢æBF†R6öçG&öÂ×W7B&R&V6†&ÆP¦æBÆVv–&ÆRF†W&Rà ¢222³#2(	BF†R–çfVçFVB'V–ÆF–æw2&R7F–ÆÂäÔTB$–æfW'&VB"ÂæBF†R6&BæWfW"6—2v†BvRÖFRW+r¢¤³#6DôäR##bÓ‚ÓR+r³#6"DôäR##bÓ‚ÓR+r÷væW"×&W÷'FVB##bÓ‚ÓB¢  £â¢¤$õD‚„ÅdU2$RDôäRâ¢¢³#6ÖFRF†R&÷6Rw&VRv—F‚F†Rw&FRƒ“2æÖW2“²³#6"WBF†P£âW"ÖÆWfVÂ7VÖÖ'’öâF†R6&Bâf–æF–æw2VæFW"$³#6(	Bv†BF†R7vVW7GVÆÇ’f÷VæB"æ@£â$³#6"(	Bv†BF†R7VÖÖ'’†BFòFV6–FR"&VÆ÷rà ¤÷væW"Âg&öÒ6&BöâF†RFWb&Wf–Ws¢¢'F†W6R&R&V7&VFVB7G'V7GW&W2Â&V7&VF–öç2Âæ÷@¦–æfW'&VB&–v‡CòÆ–¶R–b—Bv2F÷FÆÇ’–çfVçFVB&6VBöâ÷W"÷VÆF–öâ†÷W6V†öÆB&öw&Ò—Bv0§&ö&&Ç’&V7&VFVBæ÷B–æfW'&VBâ6â–÷R6†V6²F†÷6RFW67&—F–öâ6&G2âæBv†Vâ–÷R6’v†BvP¦ÖFRWÂ6’v†BvR–æ6ÇVFVB–âF†R&V7&VF–öâÂ÷"v†BvR–æ6ÇVFVB–âF†R–æfW'&VB'V–ÆF–ærÂ÷ §v†BvR–æ6ÇVFVB–âF†RGFW7FVB'V–ÆF–ærâ"  ¢¢¥F†W’&R&–v‡BÂæBF†R6&B6öçG&F–7G2—G6VÆböâ67&VVââ¢¢F†RF—FÆR&VG0¢¢¢$–æfW'&VB"&&â÷"6'&–vR6†VB3‚"¢¢v†–ÆRF†R6†—F—&V7FÇ’&VæVF‚—B&VG0¢¢¥$T4ôå5E%T5DTB¢¢ÂæB6òFöW2WfW'’÷F†W"6†—öâF†R6&Bà ¢¢¥fW&–f–VBÂæ÷B77VÖVBâ¢¢FF÷7G'V7GW&W2÷&V6öåóƒ3Uö&Æµ÷&æFöÇ…öÖ&¶WEöóræ§6öæ6öçF–ç0§F†R7G&–ær'&V6öç7G'V7FVB&¢§F†—'FVVâF–ÖW2¢¢æB&–æfW'&VB&¢§¦W&ò¢¢F–ÖW2(	BæB—G2æÖV ¦—2$–æfW'&VB7F&ÆR3r&â¢£“27G'V7GW&R&V6÷&G2¢¢&RæÖVBF†—2v’à ¢¢¥v‡’—B†VæVBÂæB—B—2F†R&W6–GVRöbf—‚F†Bv÷&¶VBâ¢¢6†ævVÆör¢§csb¢¢Ö÷fVB’Ãs`§fÇVW2öçFòF†R7W'&VçBF‡&VRÆWfVÇ2æB&RÖw&FVBÃc“BF†B†B6Æ–ÖVBFò&R&V6öæ–ærv†Và§F†W’vW&R–çfVçF–öââ—BÖ÷fVBF†RDDâ—BF–Bæ÷BÖ÷fRF†RvVæW&FVB$õ4RÂv†–6‚—2†&F6öFVC  ¦ §FööÇ2övVæW&FUö&Æö6µö–æf–ÆÂç“£S#"&æÖR#¢b$–æfW'&VB¶fÖ–Ç—Ò¶gVæ7F–öçÒ7·6W£&GÒ §FööÇ2övVæW&FUö&Æö6µö–æf–ÆÂç“£SC2&6†ævUöæ÷FR#¢$–æfW'&VBæöç–Ö÷W2§VÇ’ƒ3R&Æö6²–æf–ÆÎ(
b §FööÇ2övVæW&FUö–æfW'&VEö–æf–ÆÂç“£##’&æÖR#¢b$–æfW'&VB¶fÖ–Ç—Ò¶gVæ7F–öçÒ7·6W£6GÒ §FööÇ2övVæW&FUö–æfW'&VEö–æf–ÆÂç“£#S&6†ævUöæ÷FR#¢$–æfW'&VBæöç–Ö÷W2§VÇ’ƒ3R–æf–ÆÎ(
b ¦  ¥VæFW"F†RôÄBfö6'VÆ'’–æfW'&VFv2F†R$õEDôÒF–W"æBF†÷6RæÖW2vW&R†öæW7BâVæFW"F†P¦7W'&VçBöæR—B—2F†RÔ”DDÄRF–W"(	B§&V6öæVBg&öÒWf–FVæ6R&÷WBF†—2'F–7VÆ"F†–ær¢(	Bv†–6€¦—2W†7FÇ’v†Bâæöç–Ö÷W2&ööbFVÇB'’F†R†÷W6V†öÆB&öw&ÖÖR—2¢¦æ÷B¢¢â6òWfW'’öæRö`§F†R“2æÖW2æ÷r6Æ–×2w&FR¢¦&WGFW"F†â—G2÷vâ&V6÷&B¢¢Â–âF†RÆ&vW7BFW‡BöâF†R6&Bà¥F†—2—2F†RcsbfVÇB7W'f—f–ær–âF†RÖ÷7Bf—6–&ÆRÆ6R–âF†Rà ¢¢¥5Ä•B(	B6Æ–ÒôäRâæB"&RÖV6†æ–6Â7vVWæBFW6–vâVW7F–öâÂæB'VæFÆ–ærF†VÐ¦ÖVç2F†R7vVWv—G2öâF†RFW6–vââ¢  ¢Ò¢¤³#6(	BÖ¶RF†R&÷6Rw&VRv—F‚F†Rw&FRâ¢¢'B&VÆ÷râFWFW&Ö–æ—7F–2Â&RÖFW&—fW0¢F‡&÷Vv‚F†RvVæW&F÷'2rÒÖ6†V6¶ÂæB—B7F÷2F†R6öçG&F–7F–ær—G6VÆböâ67&VVââ6†— ¢—Böâ—G2÷vâà¢Ò¢¤³#6"(	B6’v†BvR7GVÆÇ’F–BÂW"ÆWfVÂâ¢¢'B"&VÆ÷râF†—2öæRæVVG2v÷&F–æp¢FV6—6–öâæB6&BÆ–÷WBÂæB—B6†÷VÆBæ÷B†öÆBW“2æÖW2F†B&R7W'&VçFÇ’w&öærà ¢¢¥'B(	BÖ¶RF†R&÷6Rw&VRv—F‚F†Rw&FRâ¢¢f—‚—B–âF†RtTäU$Dõ%2Âæ÷BF†R&V6÷&G3 §F†W’&RÒÖ6†V6¶vFVBÂ6òF†R&V6÷&G2×W7B&RÖFW&—fR&F†W"F†â&R†æBÖVF—FVBâ7vVWF†P¦æÖVÂ6†ævUöæ÷FVæB&W6V&6…öæ÷FV&÷6RÂæBFF÷&W6–FVçG2öFöòâF†Vâ6†V6²v†WF†W ¦ç’õD„U"W6W"×f—6–&ÆR7G&–ær7F–ÆÂW6W2ÆWfVÂ×v÷&B–â—G2öÆB6Vç6Rà ¢¢¥'B"(	B6’v†BvR7GVÆÇ’F–BÂW"ÆWfVÂâ¢¢F†—2—2F†R7V'7FçF—fR†ÆbÂæBF†R÷væW"w0¦÷vâg&Ö–ær—2F†R7V6–f–6F–öã¢f÷"V6‚'V–ÆF–ærF†R6&B6†÷VÆB6’¢§v†Bv2–æ6ÇVFVBæ@§v†W&R—B6ÖRg&öÒ¢¢(	@ ¢Ò¢¦GFW7FVB¢¢(	Bv†–6‚GG&–'WFW2F†R6÷W&6R7FFW2ÂæBv†–6‚6÷W&6S°¢Ò¢¦–æfW'&VB¢¢(	Bv†Bv2&V6öæVBÂæB¦g&öÒv†B7V6–f–2Wf–FVæ6R&÷WBF†—2F†–ær£°¢Ò¢§&V6öç7G'V7FVB¢¢(	Bv†BvR–çfVçFVBÂæBv†B&÷VæFVBF†R–çfVçF–öâ‡F†R&6†WG—RF&ÆRÀ¢F†R†÷W6V†öÆB&öw&ÖÖRÂF†RccR×&ööb66†VGVÆR’à ¥F†R6&BÇ&VG’6'&–W2W"ÖGG&–'WFR6†—2æBv‡–F—66Æ÷7W&W2Â6òF†R'G2W†—7C²v†B—0¦Ö—76–ær—2F†RÆ–â7VÖÖ'’f—6—F÷"&VG2f—'7Bâ¢$–&B'V–ÆF–æröfbF†R&Æö6²ÆÆW’"¢FöW0¦æ÷BFVÆÂF†VÒF†Rfö÷G&–çBÂF†R†V–v‡BÂF†R&ööbf÷&ÒæBF†R÷6—F–öâvW&RÆÂ–çfVçFVBæ@¦öæÇ’F†R&Æö6²v2&V6öæVBà ¢¢¥F†RG&â¢¢³f&VÆ÷r—2¢¥5DÄRæB×W7Bæ÷B&RföÆÆ÷vVB¢¢(	B—BFW67&–&W2&VæÖRFð¦Fö7VÖVçFVBöFW&—fVBö–æfW'&VFF†Bv27WW'6VFVB'’v†B7GVÆÇ’6†—VB–âcs`¢†GFW7FVBö–æfW'&VB÷&V6öç7G'V7FVF’âv†öWfW"F¶W2F†—26†÷VÆB6Æ÷6R³b÷WBv—F‚Æ–æR6––æp§6òâF†R7FæF–ær–ç7G'V7F–öâFò7F’fö6'VÆ'’Övæ÷7F–2v†–ÆR³bv2–âfÆ–v‡B—27VçC¢F†P§fö6'VÆ'’ÆæFVBÂæBF†—2&6VÂ—2&÷WBÖ¶–ærF†Rv÷&G2öâ67&VVâÖF6‚—Bà ¢¢¤f–ÆW3¢¢¢FööÇ2övVæW&FUö&Æö6µö–æf–ÆÂç–+rFööÇ2övVæW&FUö–æfW'&VEö–æf–ÆÂç–+p¦FööÇ2övVæW&FUö–æfW'&VEö†÷W6V†öÆG2ç–+r&VæFW&W'2÷vV"ö§2÷÷Wæ§6+r&VvVæW&FV@¦FF÷7G'V7GW&W2ò¦+rFö72õ$õdTää4RæÖF+rFö72õ$ôDÔæÖF†6Æ÷6R³b ¢¢¤66WFæ6S¢¢¢FööÇ2ö6†V6²ç6†w&VVâv—F‚WfW'’vVæW&F÷"w2ÒÖ6†V6¶&RÖFW&—f–æs²¢¦æð§W6W"×f—6–&ÆR7G&–æræÖW2ÆWfVÂ—B—2æ÷B¢£²6Öö¶R76W'F–öâF†B&V6÷&Bw2F—7Æ–VBæÖP¦æWfW"6öçG&F–7G2—G2÷vâW†—7FVæ6Rw&FR(	BWBF†RfVÇB&6²æB—B×W7BæÖR—C²F†R6&@§7FFW2v†Bv2–æ6ÇVFVBBV6‚ÆWfVÂf÷"öæRGFW7FVBÂöæR–æfW'&VBæBöæR&V6öç7G'V7FV@¦'V–ÆF–ærâÖö&–ÆR—2v†W&R—Bv2&W÷'FVBà ¢2222³#6"(	Bv†BF†R7VÖÖ'’†BFòFV6–FR+r¢¤DôäR##bÓ‚ÓR¢  ¢¢¥6†—VC¢¢¢6V7F–öâBF†RDõöbWfW'’&÷fVææ6R6&B(	Bv†BF–BvR–æ6ÇVFRÂæBv†W&RF–@¦—B6öÖRg&öÓö(	BF†B'F—F–öç2WfW'’w&FVB6Æ–Ò&VÆ÷r—B–çFòF†RF‡&VRÆWfVÇ2ÂæÖW2F†P¦6Æ–×2BV6‚ÂæB6—2v†W&RF†W’6ÖRg&öÒâ&VæFW&W'2÷vV"ö§2÷÷Wæ§6†&6—56V7F–öæ’À¦&VæFW&W'2÷vV"ö772÷vÆ²æ776Âf÷W"76W'F–öç2–âFööÇ2÷6Öö¶U÷&VæFW&W"æÖ§6ÂæBF†R6†ævVÆörà¤æòFF6†ævVBæBæòvVæW&F÷"&ã¢F†—2—2VçF—&VÇ’&VF–æröb&V6÷&G2F†BÇ&VG’W†—7FVBà ¢¢¤Ö¶–ær—B%D•D”ôâ—2v†BÖFR—BvFV&ÆRÂæBF†Bv2F†RFW6–vâFV6—6–öââ¢¢7VÖÖ'¦6â&Rw&—GFVâ2†–v†Æ–v‡B&VVÂ(	B¢&GFW7FVC¢—G26—¦RÂ—G2÷6—F–öâ"¢(	BæBæ÷F†–ær6âF†Và¦6†V6²—BÂ&V6W6RF†W&R—2æò&—F†ÖWF–2FòF—6w&VRv—F‚âWfW'’6Æ–ÒF†R6&B&VæFW'2ÆæG2–à¦W†7FÇ’öæR&÷r–ç7FVBÂ6òF†RvFR—2$T4õTåC¢–6²WfW'’'V–ÆF–ærÂFÆÇ’F†R6öæf–FVæ6R6†—0¦öfbF†R&VæFW&VB6&BÂæB&WV—&RF†R6V7F–öâw2÷vâF‡&VRçVÖ&W'2Fò&RF†÷6RçVÖ&W'2à¢¢¤ÆÂ#sbÆöFVB'V–ÆF–æw2w&VRÂB&÷F‚f–Ww÷'G2â¢¢F†R&V6÷VçBFVÆ–&W&FVÇ’W6W2F†R4ÔP§6VÆV7F÷"2F†RöÆFW"6†—Ö6÷fW&vR76W'F–öâ†ç÷ÖÖWFæ6öæbÂç÷×6V2F&ÆRæGG'2æ6öæf’(	@§GvòFVf–æ—F–öç2öb&6Æ–ÒöâF†—26&B"—2W†7FÇ’†÷r7VÖÖ'’v÷VÆB6öÖRFòF—6w&VRv—F€§F†R6&B—B7VÖÖ&—6W2v†–ÆR&÷F‚vFW27F–VBw&VVâà ¢¢¤6—FF–öâÖVç2F–ffW&VçBF†–ærBV6‚ÆWfVÂÂæBöæRÆ&VÂ÷fW"ÆÂF‡&VRv÷VÆB†fR&VVà§F†R6ÖR6FVv÷'’W'&÷"F†—26&Bw2†—7F÷'’—2ÖFRöbâ¢¢öââGFW7FVF6Æ–Ò6÷W&6R—0§v†W&RF†RfÇVR6ÖRe$ôÒâöâ&V6öç7G'V7FVFöæR—B—2v†B$õTäDTBâ–çfVçF–öâ(	BF†P§&V6÷&G26’6òF†V×6VÇfW2‚¢'F†R7V2—26—FVB&V6W6RF†R–çfVçF–öâ—2&÷VæFVB'’—BÂv†–6‚—0§v†BÖ¶W2—BFVfVç6–&ÆR&F†W"F†â&&—G&'’"¢’(	BæB“2æöç–Ö÷W2&öög26—FP¦÷væW%ö6†–6võóƒ3U÷&V6öç7G'V7F–öå÷7V5ó##fæBæG&V5óƒƒE÷cöâWfW'’GG&–'WFRF†W’†fRà¤6–ævÆR6÷W&6W3¦Æ–æR÷fW"F†R7VÖÖ'’v÷VÆB†fR&–çFVBæ–æWFVVçF‚Ö6VçGW'’†—7F÷'’0¦GG&–'WF–öâf÷"'V–ÆF–æræö&öG’6Æ–×27FööBF†W&RâF†RF‡&VRÆVG2&R¢¤g&öÒ¢¢Â¢¥&V6öæV@¦g&öÒ¢¢æB¢¤&÷VæFVB'’¢¢à ¢¢¤GFW7FVB—2æ÷BF†R6ÖR2'V–ÇBÂæB7VÖÖ'’öbv†Bv2”ä4ÅTDTB—2W†7FÇ’v†W&RF†@¦vFöW2FÖvRâ¢¢F†RvW7FW&â†÷FVÂw27F&ÆW2&RGFW7FVF(	B&RÖf—&R66÷VçBFW67&–&W2F†P§vvöâ–&B(	BæBF†W&R—2æ÷F†–æröbF†VÒ–âF†RÖöFVÂâ¢£B&V6÷&G26''’âGG&–'WFR–âF†@§7FFRâ¢¢F†R&÷w2&VÆ÷r†fRÖ&¶VB—B6–æ6RF†RvVöÖWG'–FV6Æ&F–öâW†—7FVC²F†R7VÖÖ'§&WVG2—B†æ÷B–âF†RÖöFVÃ¢7F&ÆW6’&F†W"F†âfW&v–ær—B–çFò6÷VçBöbF†–æw2vP¦–æ6ÇVFVBâvFVBöâF†RF—67&–Ö–æF–ær—#¢F†RvW7FW&â†÷FVÂ6†÷w2F†RÆ–æRÂF†R6Vvæ6‚†0¦æò7V6‚GG&–'WFRæB6†÷w2æ÷F†–ærà ¢¢¤âV×G’ÆWfVÂ6—26ò–âv÷&G2ÂæBF†B—2F†R6öÖÖöâ66R&F†W"F†âF†RVFvR66Râ¢ ¤7&÷72F†RFF6WBw2#s’&V6÷&G2æB¢£2ÃcsRw&FVB6Æ–×2(	B“’GFW7FVBÂS’–æfW'&VBÂ"Ã“cp¦–çfVçFVB(	B#B&V6÷&G2†fRæòGFW7FVB6Æ–ÒBÆÂâ¢¢&÷rF†B&VæFW&VBöæÇ’v†VâæöâÖV×G§v÷VÆBvò6–ÆVçBöâF‡&VRV'FW'2öbF†RF÷vâÂBF†RöæRÖöÖVçBf—6—F÷"Ö÷7BæVVG2FVÆÆ–ærà¥6òF†RGFW7FVB&÷röââæöç–Ö÷W2&ööb&VG2¢$æ÷F†–ær&÷WBF†—2'V–ÆF–ær—2GFW7FVB'’§6÷W&6Râ"  ¢¢¥F†Rf–æF–ærF†—2&6VÂF–Bæ÷BvòÆöö¶–ærf÷#¢c’'V–ÆF–æw2†fR–çfVçF–öç2F†Bæ÷F†–ær—0§&V6÷&FVB2&÷VæF–ærâ¢¢&V6öç7G'V7FVF&WV—&W2æ÷FRÂæ÷B6÷W&6R(	BFVÆ–&W&FVÇ’ÂæB³#6¦&wVVBv‡’F†RöÆB&&÷GFöÒ×F–W"fÇVR6—F–ær6÷W&6W2—27W7–6–÷W2"'VÆRF–VBv—F‚F†R&VæÖRà¥F†R6öç6WVVæ6R†BæWfW"&VVâ6÷VçFVC¢öbF†R#s&V6÷&G26''––ærBÆV7BöæR–çfVçFVB6Æ–ÒÀ¢¢£c’6—FRæ÷F†–ærBÆÂöâç’öbF†VÒ¢¢Â6òF†V—"&÷VæFVB'–Æ–æR&VG2¢$æ÷F†–ær—26—FVB0¦&÷VæF–ærF†W6Râ"¢F†R6Vvæ6‚†÷FVÂ—2öæRöbF†VÒ(	B—G2fö÷G&–çB—2F†RÆ6V†öÆFW"—G2÷và¦æ÷FR6ÆÇ2Æ6V†öÆFW"ÂæBæòG—öÆöw’—2æÖVB&W6–FR—BâF†B—2†öæW7BæB—B—2æ÷p¥d•4”$ÄRÂv†–6‚—2F†Rö–çC²v†WF†W"F†÷6Rc’6†÷VÆB7V—&R&÷VæB—2&W6V&6‚VW7F–öâf÷ ¦7V66W76÷"æBæ÷B6öÖWF†–ærFòW"÷fW"öâF†R6&Bà ¢¢¥GvòF†–æw2FVÆ–&W&FVÇ’æ÷BFöæRâ¢¢F†R6V7F–öâFöW2æ÷B6Æ–ÒFò6÷fW"F†RÄ”$U%D”U2(	B¦Æ–&W'G’&VÆöæw2FòæòGG&–'WFRÂv†–6‚—2v‡’—B†2—G2÷vâ6V7F–öâ(	B6òF†RÆVBö–çG2@¢%v†BvRÖFRW†W&R"&F†W"F†â–×Ç––ærF‡&VR&÷w2öb6Æ–ÒÆ&VÇ2&RF†Rv†öÆRöbv†Bv0¦–çfVçFVBâæBF†RF‡&VRFVf–æ—F–öç2&RF†RWf–FVæ6RæVÂw2÷vâv÷&G2ÂÆ—FW&ÆÇ“¢V6‚—2§7V'7G&–æröbF†RÆVvVæB–â–æFW‚æ‡FÖÆÂ76W'FVB27V6‚Â&V6W6RGvò7W&f6W2V–WFÇ¦F—6w&VV–ær&÷WBv†B–æfW'&VFÖVç2—2F†RfVÇB³#67VçB'Vâ6ÆVæ–ærWà ¢2222³#6(	Bv†BF†R7vVW7GVÆÇ’f÷VæB+r¢¤DôäR##bÓ‚ÓR¢  ¢¢¥F†R&6VÂæÖVBGvòvVæW&F÷'2âF†W&RvW&Rf—fRÂÇW26—‡F‚7FvRæö&öG’†BÆ—7FVBâ¢ ¦vVæW&FUö&Æö6µö–æf–ÆÂç–æBvVæW&FUö–æfW'&VEö–æf–ÆÂç–vW&RF†RGvòw&—GFVâF÷vã°¦vVæW&FUöæ÷'F…ö–æf–ÆÂç–ÂvVæW&FU÷vW7Eö–æf–ÆÂç–æBvVæW&FUö–æfW'&VEö†÷W6V†öÆG2ç– ¦6''’F†R6ÖRf÷W"7G&–æw2ÂæBvVæW&FUö–æfW'&VEöæÖW2ç–—2¢§6V6öæB72F†B'Vç2gFW §F†R†÷W6V†öÆB&öw&ÖÖRæB&Ww&—FW2F†R†÷W6V†öÆBw2÷vâÆ&VÂ¢¢â&VvVæW&F–ærF†R†÷W6V†öÆG0§v—F†÷WB—B6–ÆVçFÇ’FVÆWFVBWfW'’–çfVçFVB&W6–FVçBw2æÖRæBæÖUö&6—6&Æö6²(	BF†Rv†öÆRö`¤³‚(	BæBF†RF–fbv2F†RöæÇ’F†–ærF†B6–B6òâ¢¦vVæW&FUö–æfW'&VEö†÷W6V†öÆG2ç–F†Và¦vVæW&FUö–æfW'&VEöæÖW2ç–Â–âF†B÷&FW"¢¢Â÷"–÷RÆ÷6RF†RæÖ–ærÆ–W#²F†R†÷W6V†öÆ@§&öw&ÖÖRw2ÒÖ6†V6¶†–FW2F†—2'’÷fW&Æ––ærF†RæÖ–ær72&Vf÷&R—B6ö×&W2Â6òÒÖ6†V6¶ ¦—2w&VVâV—F†W"v’à ¢¢¤f÷W"7G&–æw2W"vVæW&F÷"Âæ÷BöæRâ¢¢æÖVÂ6†ævUöæ÷FVÂ&W6V&6…öæ÷FV(	Bæ@¦7–Ö&öÆ–5öÆö6F–öæÂv†–6‚F†R&6VÂF–Bæ÷BÆ—7BæBv†–6‚6–B$æöç–Ö÷W2–æfW'&VB&ööb–à§F†R(
b"öâc"&V6÷&G2âÆÂf÷W"æ÷r6’&V6öç7G'V7FVFà ¢¢¢$äõBDô5TÔTåDTBäÔTB%T”ÄD”är"v2w&öærGv–6R–âöæRÆ–æRâ¢¢WfW'’&W6V&6…öæ÷FVVæFV@¦'’6öçG&7F–ær—G6VÆbv—F‚F–W"6ÆÆVBFö7VÖVçFVFÂv†–6‚†2æ÷BW†—7FVB6–æ6Rcsbâ—B&VG0¦äõBâEDU5DTBäÔTB%T”ÄD”ävæ÷rà ¢¢¥F†R6÷VçG2Â6òF†RæW‡B7vVW6âFVÆÂG&–gBg&öÒg&W6‚fVÇBâ¢¢“2æÖW2ÂÆÂöâ&V6÷&G0¦w&FVB&V6öç7G'V7FVFBW†—7FVæ6R(	BæBF†RF‡&VR&W6V&6…öæ÷FV÷VæW'2'F—F–öâF†VÐ¦W†7FÇ“¢C"$T4ôÔÔTäDTBòtTäU$DTFÂ3”ädU%$TB%T”ÄD”ävÂ#”ädU%$TBòtTäU$DTFâF†W&P¦—2æòf÷W'F‚w&÷WæBæò&V6÷&Bv2Ö—76VBâ&V6öÖÖVæFVF—2F†Rv÷&BF†—2&ö¦V7B&VæÖVBv¦g&öÒ¢¦'’æÖR¢¢öâ##bÓ‚Ó2æBF†Vâ¶WB&–çF–æröâC"6&G2f÷"f÷'Fæ–v‡Bà ¢¢¥F‡&VRF†–æw2÷WG6–FRF†RvW&R6––ær—BFöòÂæBGvòöbF†VÒ&Rv÷'6RF†âF†R6&G3¢¢  ¢Ò¢¦Fö72õ$õdTää4RæÖFFö7VÖVçFVBfö6'VÆ'’F†R'V–ÆB&V¦V7G2â¢¢—B7F–ÆÂFVf–æV@¢Fö7VÖVçFVBò–æfW'&VBò6öæ¦V7GW&Æâ—B—2F†RvR–÷R6VæB6öÖVöæRFòv†VâF†W’6²v†@¢F†Rw&FW2ÖVâÂ6òç–öæRföÆÆ÷v–ær—Bv÷VÆB†fRw&—GFVâ&V6÷&BfÆ–FFRç–&VgW6W2à¢7vVBÂv—F‚FFVBæ÷FR&V6÷&F–ærF†R&VæÖRæBö–çF–ærB4ôäd”DTä4V2F†P¢Væf÷&6VÖVçBâ—G2&V6öç7G'V7FVF&÷rÇ6ò†BFò6†ævRÔTä”ärÂæ÷B§W7B7VÆÆ–æs¢F†RöÆ@¢&÷GFöÒF–W"ÖVçB&æòWf–FVæ6RÂf–ÆÆVBf÷"f—7VÂ6ö×ÆWFVæW72"ÂF†RæWröæRÖVç2&–çfVçFV@¢v—F†–â&÷VæBæB÷v–æræ÷FR"ÂæBF†R'VÆRF†B&÷GFöÒ×F–W"fÇVR6—F–ær6÷W&6W2—0¢7W7–6–÷W2¢¦F–VBv—F‚F†R&VæÖR¢¢(	BF†R6÷W&6RF†B&÷VæG2â–çfVçF–öâ—2v†BÖ¶W2—@¢FVfVç6–&ÆRâFö7VÖVçFVE÷&ævV¶VW2—G2æÖS²—B—2f–VÆBÂæ÷BÆWfVÂà¢Ò¢¦fÆ–FFRç–w2÷vâW'&÷"ÖW76vW2æÖVBF†Rw&öærF–W"â¢¢Ö—76–ær6÷W&6RöââGFW7FVF ¢fÇVR&W÷'FVB¢&Fö7VÖVçFVB&WV—&W2BÆV7BöæR6÷W&6Uö–B"£²&V6öç7G'V7FVFfÇVRv—F‚æð¢æ÷FR&W÷'FVB¢&–æfW'&VB&WV—&W2æ÷FR"¢ââW'&÷"F†BæÖW2w&FRF†R&ö¦V7BFöW2æ÷@¢†fR6VæG2F†R&VFW"Fòf—‚F†Rw&öærf–VÆBà¢Ò¢¥F†R6Öö¶Rw2÷vâ†÷W6V†öÆB76W'F–öâ&WV—&VBF†R'Vrâ¢¢—B76W'FVBF†R†÷W6V†öÆBÆ&VÀ¢ÖF6†VBö–æfW'&VBö(	B6òF†R&VÆV6RvFRv2¦†öÆF–ærF†RfVÇB–âÆ6R¢â—B—2–ææVBFð¢F†R†VBw2÷vâw&FVæ÷r&F†W"F†âFòÆ—FW&ÂÂv†–6‚—2F†Rf÷&ÒF†B6ææ÷B&÷Bà ¢¢¥v†Bv2FVÆ–&W&FVÇ’äõB6†ævVBÂæBv‡’â¢  ¢Ò¢¦&V6öç7G'V7F–öâç7FGW3¢&–æfW'&VEöæöç–Ö÷W2&ÂF†R–æfW'&VEóƒ3V†6R–BÂF†P¢†…ö–æeò¦öƒ3Uö–æfW'&VEö†÷W6V†öÆE÷&öw&ÖÖRæ§6öæf–ÆVæÖW2ÂæBF†RvVæW&F÷"f–ÆVæÖW2â¢ ¢F†W6R&RÖ6†–æR–FVçF–f–W'3¢æWfW"&–çFVBÂæB–æfW'&VEöæöç–Ö÷W6æÖW2F†RtÄ"f–ÆW2à¢F†RÆ7BF–ÖRF†—2fÇVRv2&VæÖVBÂ÷Wæ§6v2ÆVgBFW7F–ærF†RöÆB7G&–æræB¢§F†P¢&V6öç7G'V7F–öâfÆr6–ÆVçFÇ’fæ—6†VBg&öÒ‚6&G2¢¢(	BFW7BöâfÇVRæ÷F†–ær6'&–W2—0¢Çv—2fÇ6Râ&÷6RÖ÷fVC²¶W—2F–Bæ÷BâF†R6&Bw2v÷&F–æræB—G2¶W’&Ræ÷rFV6÷WÆVBöà¢W'÷6RÂv—F‚F†R&V6öâw&—GFVâBF†RFW7Bà¢Ò¢¦&VæFW&W'2÷vV"ö§2ö6†ævVÆöræ§6VçG&–W2cƒræBV&Æ–W"â¢¢F†W’&RF†R†—7F÷&–6Â&V6÷&Bæ@¢FW67&–&Rv†B6†—VB¦BF†RF–ÖR¢Âv†Vâ'&V6öÖÖVæFVB&V6öç7G'V7F–öâ"v2F†Rv÷&B7GVÆÇ’öà¢F†R6&G2â&Ww&—F–ær6†—VB&VÆV6Ræ÷FRFòÆöö²&WGFW"—2F†R¶–æBöbF–G––ærF†—2&ö¦V7@¢W†—7G2æ÷BFòFòà ¢¢¤ÆVgBf÷"7V66W76÷"Â7FFVB&F†W"F†âV–WFÇ’6¶—VBâ¢¢Fö72õ$õdTää4RæÖFw2¦&wVÖVçG2 §vW&RöæÇ’&R×&VBv†W&RF†Rv÷&B×7vÖFR6VçFVæ6RfÆFÇ’fÇ6Râ—G2*r%F†W’Ö’Â†÷vWfW"À¦6''’÷6—F–öâFò–æfW'&VF"7F–ÆÂvÆ÷76W2F†R&÷GFöÒF–W"276W'F–ær¦æòWf–FVæ6RW†—7G2¢À§v†–6‚v2G'VRöb6öæ¦V7GW&ÆæB—2öæÇ’†ÆbG'VRöb&V6öç7G'V7FVFâF†B—2&÷6R&÷W@§&V6öæ–ær&F†W"F†âÖ—6Æ&VÆÆVBw&FRÂ6ò—B—26W&FR&VBv–ç7BfÆ–FFRç–æ@¦æ÷BÆ–æRFò6†ævR–â76–ærà ¢222³(	BF†R–æfW'&VB×&W6–FVçG2&öw&ÖÖR¢‡F†R&–röæS²×VÇF’×6W76–öã²6'fR–çFòF—7G&–7G2’ ¤6†–6vòvVçBg&öÒã3SV÷ÆRƒƒ32’Fòã2Ã#cR†ÆFRƒ3R’â'V–ÆBF†RõTÄD”ôâ2FF6WBÀ§F†Vâ'V–ÆBF†R'V–ÆF–æw2—B–×Æ–W2âæWrF—&V7F÷'’FF÷&W6–FVçG2ö¢öæRf–ÆRW"„õU4T„ôÄBÀ¦w&÷W–ærW'6öç2Âv—F‚W"×W'6öâf–VÆG2(	BæÖRÂ'&—fÂFFR†ÖöçF‚–b¶æ÷v&ÆR’Â'G’6—¦RÀ¦÷&–v–âÂv‡’F†W’6ÖRÂW&–öBÖ6÷'&V7Bö67WF–öâÂv†W&RF†W’Æ—fVBÂv†W&RF†W’v÷&¶VB(	BæBà¦67W&7’w&FRW6–ærU„5DÅ’F†—2fö6'VÆ'“¢¢¦Fö7VÖVçFVF¢¢†æÖVB–â6÷W&6S¢æG&V2—0¦FVç6Rv—F‚F†VÒ(	Böff–6–Ç2ÂÖ–æ—7FW'2ÂG&FW'2ÂFfW&â¶VWW'2ÂF†R¤FVÖö7&B¢w2GfW'F—6W'2’À¢¢¦FW&—fVF¢¢†&VÂW'6öâv†÷6RFWF–Ç2&R'FÇ’&V6öç7G'V7FVB’Â¢¦–æfW'&VF¢¢†¦‡—÷F†W6—6VB&W6–FVçBf–ÆÆ–ærF†RF÷vâw2FVÖöç7G&&ÆRæVVG2(	BF†Rf—'7B&&&W"ÂF†R6V6öæ@¦&Æ6·6Ö—F‚ÂF†R6ö÷W"F†R6¶–ærG&FR&WV—&W2’âäUdU"'&V6öÖÖVæFVB"(	BF†Rv÷&G2&P¢¢¦–æfW'&VB&W6–FVçG2¢¢æB¢¦–æfW'&VB7G'V7GW&W2¢¢âæF—fW2v†ò&VÖ–æVB&VÆöær–âF†P§÷VÆF–öâv†W&R6÷W&6VC²FW–7F–öâöbV÷ÆR7F—2÷WBöb66÷R„Ã’(	BF†—2—2DD4UBÆ–W ¦fVVF–ær7G'V7GW&W2â7&÷72×&VfW&Væ6RV6‚†÷W6V†öÆBFòFF÷7G'V7GW&W2ö–G2†Æ—fW5öFÀ¦v÷&·5öF“²'W6–æW76W26ÇW7FW"F÷v&BF†R&—fW"÷7G&VWG2Â&W6–FVæ6W27&VB÷WGv&B2F†RF÷và¦7&÷vG2‡W6RF†RF†ö×6öâÆBÆ÷G2Â³r’âW‡FVæBFööÇ2÷fÆ–FFRç–6ò&W6–FVçBw26÷W&6Uö–G0¦×W7B&W6öÇfRæBw&FW2&RVæf÷&6VBâ¢¥F†R&–Ö'’vöÂ—2'V–ÆF–æw2¢£¢WfW'’–æfW'&V@¦†÷W6V†öÆBF†BæVVG2GvVÆÆ–ærvWG2â–æfW'&VB7G'V7GW&V&V6÷&BöâF†RÆBÂ&6†WG—VBÀ¦&¶VBÂ6öæf–FVæ6RÖw&FVB(	BF†—2—2†÷rF†RF÷vâ&V6†W2—G2G'VRƒ3RFVç6—G’â7F'Bv—F€¤Dô5TÔTåDTBV÷ÆR†Ö–÷'2×FòÖ&RÂövFVâÂ‡V&&&BÂF†R6ÆW&w’ÂWfW'’GfW'F—6W"Ç&VG’–à¦6†–6võöFVÖö7&Eóƒ35óó#f’ÂF†VâFW&—fRÂF†Vâ–æfW"Fòf–ÆÂF†R6÷VçB'’ö67WF–öâ6Vç7W2à ¢¢¥†6RöæRDôäR##bÓ‚Ó2¢¢(	BF†RFö7VÖVçFVBæBFW&—fVBÆ–W#¢s"†÷W6V†öÆG2Â“bW'6öç2À¦FööÇ2÷fÆ–FFRç’6†V6µ÷&W6–FVçG2‚–ÂæBF†R&VæÖRF†B&WF—&VB'&V6öÖÖVæFVB"g&öÒF†P§fö6'VÆ'’æBg&öÒF†R6öFRâ¢¥†6RGvòDôäR##bÓ‚Ó2¢¢(	Bƒ–æfW'&VB†÷W6V†öÆG2æB“ §W'6öâVçG&–W2ƒS"òƒ‚–âÆÃ¢sbFö7VÖVçFVBÂ#FW&—fVBÂ“"–æfW'&VB’Â¢£3‚æWr7G'V7GW&W2¢ ¢ƒrFö7VÖVçFVB'V–ÆF–æw2F†R6÷W&6W2FW67&–&RæBF†RÖöFVÂÆ6¶VBÂ3–æfW'&VBv÷&·Æ6W2æ@¦GvVÆÆ–æw2’ÂæB¢£ƒ2öbF†R‚æöç–Ö÷W2&öög2F÷FVB¢¢–çFò&wVVBö67Wæ7’â##"7G'V7GW&W3°£c"æÖR†÷W6V†öÆBöâF†R6&BâFö72ôÄ”$U%D”U2æÖFÃƒBFÖ—G2F†RÆ÷C²F†R&V6—RæB—G0§&R×'Vææ&ÆRvFW2&RFF÷&V6öç7G'V7F–öâóƒ3Uö–æfW'&VEö†÷W6V†öÆE÷&öw&ÖÖRæ§6öæ°¦FööÇ2övVæW&FUö–æfW'&VEö†÷W6V†öÆG2ç’ÒÖ6†V6¶²&V6öæ–ær–à¦Fö72õ$U4T$4‚÷&W6–FVçG5óƒ3Uö–æfW'&VBæÖFà ¢¢¥†6RF‡&VR†’DôäR##bÓ‚Ó2(	BF†R'V–ÆF–æw2&R÷WBöbF†R&öBÂæBF†RvFR6â6VRF†P§&öBæ÷râ¢¢F†RÆ6VÖVçBvFR–âFööÇ2övVæW&FUö–æfW'&VEö†÷W6V†öÆG2ç–FW7FVB÷fW&ÆÂvFW ¦æBÖöFVÆÆVBw&÷VæBæB†BæWfW"FW7FVBf÷"F†R7G&VWBâ—BFöW2æ÷rÂF‡&÷Vv€¦FööÇ2÷ÆEö6÷'&–F÷'2ç–(	BF†R6ÖRÖöGVÆRFööÇ2övVæW&FU÷ÆEöÆ÷G2ç’Ò×&W÷'F&VG2Â6òF†P¦6†V6²æBF†RvVæW&F÷"F†B×W7B6F—6g’—B6ææ÷Bç7vW"F–ffW&VçFÇ’(	BæB—B&VgW6W2¢¦ç’¢ ¦vVæW&FVBfö÷G&–çBF†B&V6†W2–ç6–FRÆGFVB6÷'&–F÷"â¢£#2öbF†R3‚&V6—R6VçG&W2Ö÷fVB¢ ¢†ÖVF–â"ãÒÂv÷'7B#ã’Ò“²–âÖ6÷'&–F÷"6VçG&W27&÷72F†Rv†öÆR66VæRfVÆÂ#"(i"æBæ÷@¦öæRöbF†RFVâ—2vVæW&FVBÆ6VÖVçBâF†R6VçG&RFW7B†BVæFW'7FFVBF†R&ö&ÆVÒ'’Ö÷&RF†à¦†Æc¢F†R&V6—R&VBF†RƒgBg&öçFvR&æG22Æ–æW2Fò6—Bôâ&F†W"F†âVFvW2Fò6—@¤$T„”äBÂ6ò&÷röbÆ¶R7G&VWB6†÷27FööBv—F‚—G2g&öçB†Æb–âF†R7G&VWBæB—G26VçG&R¦ÖWG&R÷WG6–FRF†R6÷'&–F÷"Â–çf—6–&ÆRFòö–çBFW7Bâfö÷G&–çG2–ç6–FR6÷'&–F÷"7&÷72F†P§66VæS¢¢£Sb(i"32¢¢â÷6—F–öç27F’6öæ¦V7GW&Æ¢6ÆV&–ærF†R&öGv’—2æ÷B7FæF–æröâ§&V6÷fW&VBÆ÷BâFWF–Â–âFö72õ$U4T$4‚÷F†ö×6öå÷ÆEöw&–BæÖF*rvà ¢¢¥v†B†6RF‡&VR–æ†W&—G2â¢¢†’æò–æfW'&VBW'6öâ—2æÖVBæBæöæR6†÷VÆB&R(	Bâ–æfW'&V@§&W6–FVçB—26Æ–Ò&÷WB&F–òâ†"’¢¤æòW&–öBG&FRF&ÆRf÷"6ö×&&ÆRvW7FW&âF÷vâ—0¦–âFF÷6÷W&6W2ö¢£²WfW'’&F–ò—2FW&—fVBg&öÒf—fR–âÖFF6WB6Æ–'&F–öç2æBF†R&—F†ÖWF–0¦—2w&—GFVâ÷WBW"G&FRâf–æF–ær&VÂG&FRF&ÆR—2F†R6–ævÆR†–v†W7B×fÇVR&W6V&6‚W'&æ@¦ÆVgB–âF†—2&öw&ÖÖRÂ&V6W6R—Bv÷VÆBÖ÷fRF†Rö67WF–öâ6Vç7W2öfbFW&—fVB&—F†ÖWF–2à¢†2’#Ræöç–Ö÷W2&öög2&RFVÆ–&W&FVÇ’VæF÷FVB‡&—f–W2Â6†VG2Â7F&ÆW2ÂF†R66†ööÆ†÷W6R’à¢†B’F†RSR&W6W'fVBvW7BÔF—f—6–öâ6Æ÷G2æBƒB6÷WF‚†6RÓ"6Æ÷G2&RVçF÷V6†VBæBF†P§Æ6VÖVçBvFRæ÷r7F—fVÇ’fö–G2F†VÒâ†R’Gvò†÷W6V†öÆG2'&—fRB–V&&V6—6–öâ7G&FFÆ–æp£ƒ3RÓrÓ††…öFf—5ö¦ö†æÂ†…ö†FFö6µöVGv&F’æB&R7F–ÆÂv&æ–æw2à ¢222³"(	B–ÖvRÖ67W&7’Æö÷2öâF†RÆæFÖ&²'V–ÆF–æw0¥&VfW&Væ6R6WC¢FF÷6÷W&6W2ö76WG2÷&Vf—&U÷f–Ww5ö¶Wf–åó##eó‚öƒ"ÆFW3²$TB•E2$TDÔR(	@§F†RF÷&–2×÷'F–6ò6÷W'F†÷W6RÆFR—2F†Rƒ3r²'V–ÆF–æræB—2äTtD•dR&VfW&Væ6R’âÇ6ð¦‡GG3¢òö6†–6vöÆöw’æ6öÒ÷&Vf—&R÷&Vf—&S#sRò‡6÷W&6R&V6÷&BW†—7G2’âÆö÷W"'V–ÆF–æs §&VæFW"F†RÖöFVÂw2'V–ÆF–ærg&öÒF†RÆFRw2f–Wwö–çBÂ6ö×&RÂ–×&÷fRÂ&WVBVçF–ÂÖ76–ærÀ§&ööbÂfVæW7G&F–öâ&‡—F†ÒÂ6†–ÖæW—2æB6–væ&ö&BÖF6‚âF–W"ÓR–7F÷&–Â'VÆR†öÆG3¢f–Ww0¦G&—fRdõ$Ò2–æfW'&VFÂæWfW"6ö÷&F–æFR÷"fö÷G&–çBâ¢¤w&VVâG&VRf—'7B¢¢‡ÆFR(	@§Gvò×7F÷&W’6Æ&ö&BÂVæB6†–ÖæW—2&÷F‚v&ÆW2ÂWfVâbób&—2Â†æv–ær6÷&æW"4”tä$ô$BÂ&V ¦VÆÂ’ÂF†VâF†Rf÷'Bw&÷W‡Æ—6FRöâ&—6–ærw&÷VæB’ÂF†Vâ6Vvæ6‚õvöÆbö–çBà ¢¢¥Gvò6WF–öç2F†—2&6VÂ†2æ÷r–Bf÷"Â&÷F‚g&öÒF†Rf÷'B72…BÓCB(i"BÓ“B’â¢  £â¢¢%v†—FWv6†VBÆ—6FR"—2F†R&VfW&Væ6R6WBw2$TDÔRFÆ¶–ærÂæ÷B6÷W&6Râ¢¢F†RÆFR–çG0¢F†Rf÷'Bw2öæR6öçF–çV÷W2æ÷'F‚7W'F–â7&÷72¢£ãƒ\9r¢¢&ævRöbFöæR–â6–ævÆRf–Wr(	@¢ÇVÖ–ææ6R“V7BöbF†RvFRv÷&²Â2vW7Böb—B(	Bv—F‚F†R7W&f6RF†—2&ö¦V7B6†—0¢††WvåöÆövÂÇVÖ–ææ6RC2’6—GF–ær&WGvVVâF†RGvòâfW&wW2w2v†—FR×v6†VB&ö&BfVæ6R—2F†P¢Væ6Æ÷7W&Röb¢£ƒS¢¢ÂgFW"F†R–6¶WG26ÖRF÷vââæV—F†W"Æ–6Vç6W2FöæRà£"â¢¥F†—2Æö÷6ö×&W2Gvò–7GW&W2%’U”RÂæBF†B—2†÷r—B&öGV6VBw&öærF–6¶WBâ¢¢BÓCBw0¢&÷r26–BF†RÖöFVÂw2–6¶WG2vW&RfÆB×F÷VBæBF†RÆFRw2ö–çFVC²F†RÖöFVÂ†26'&–V@¢ã3"Òöb6†'VæVB†VBöâÆÂsc‚÷7G26–æ6RF†R&6†WG—Rv2w&—GFVâÂæBF†RÆFR'VÆW0¢—G267G&–v‡BFòãCR‚&×2v†–ÆR&W6öÇf–ær–6¶WG2B‚—F6‚â&÷F‚&VF–æw2vW&P¢f–Æ&ÆRFòç–öæRv†òÖV7W&VBÂæBæö&öG’†Bâ¢¥v†W&R&÷röbF†—27276W'G26†R÷"¢FöæRÂÖV7W&R—B&Vf÷&R—B&V6öÖW2F–6¶WB¢¢(	BFööÇ2öÖV7W&U÷–6¶WE÷ÆFRç–—2F†R6†Rö`¢–ç7G'VÖVçBF†B6÷7G2Ö–çWFRæB6WGFÆW2—BâBÓ“B—2F†Rw&—FR×W²¢¥BÓƒB¢¢—2F†RöæP¢f–æF–æröbF†BÖV7W&VÖVçBF†B7W'f—fVBà ¢222³2(	BfÆ÷&÷Ö–âæB6÷fW&vR+r¢¥õÔ”âDôäR##bÓ‚Ó3²4õdU$tR5D”ÄÂõTâ¢ ¤w&72æBfÆ÷vW'2&V"÷WBöbF†Rw&÷VæB2–÷RvÆ²F÷v&G2F†VÒâ  ¢¢¥F†R÷Ö–â†Æb—2f—†VBÂæBF†RF–væ÷6—2—2F†R'Bv÷'F‚¶VW–ærâ¢¢F†RG&ç6—F–öâv0¦æ÷BÖ—76–ær(	B&–ætfFVö–ææW$fFV†B&VVâ66Æ–ærWfW'’ÆçBF÷vâ÷fW"F†R÷WFW"&æBö`¦—G2&–ær6–æ6RF†RÆ–W"v2w&—GFVââ—Bv2¦g&÷¦Vâ£¢F†RfFRv2&¶VB–çFòF†R–ç7Fæ6Rw0¦†V–v‡BBÆGF–6R×&V'V–ÆBF–ÖRÂæBF†RÆGF–6R—2&V'V–ÇBöæÇ’WfW'’ETäRç7FWææV&ÖWG&W0§vÆ¶VBâ6òF†R&×v26×ÆVBöæ6RW"7G&–FRæB†VÆBâv—F‚ã"Ò7FWv–ç7BF†RæV §&–ærw2"ã"Ò&æBÂÆçBvVçBg&öÒæ÷F†–ærFò¢£SRRöbgVÆÂ†V–v‡B&WGvVVâöæRg&ÖRæBF†P¦æW‡B¢¢(	BfFRgVæ7F–öâ&öGV6–ær7FWÂv†–6‚—2v‡’F†R6öFRÆöö¶VBÆ–¶R—BÇ&VG’F–@§v†BF†R÷væW"v26¶–ærf÷"à ¥F†R&×æ÷r'Vç2W"e$ÔR–âF†RfW'FW‚6†FW"v–ç7B6ÖW&÷6—F–öæ†6†•&–æv6'&–W0¦¶÷WFW"Â&æBÂ–ææW"Â–ææW$&æEÖW"–ç7Fæ6S²F†R66ÆR—2Væ–f÷&ÒÂ&÷WBF†RÆçBw2&6R’à¥F‡&VRF†–æw26ÖRv—F‚—C  ¢Ò¢¤fÆ÷vW"†VG2†fRFòFW66VæBÂæ÷B§W7B6‡&–æ²â¢¢†VBw2÷&–v–â—2'Gv’W7FVÒÂ6ð¢66Æ–ær—B–âÆ6RÆVfW2—B†æv–ær÷fW"ÆçBF†B—2æòÆöævW"VæFW"—Bâ6†•&—6V ¢6'&–W2F†R†V–v‡BöbF†R†VB÷fW"—G2÷vâÆçBw2&6RæBF†R6†FW"Æ÷vW'2—B'¢&—6R9rƒ(‰"fFR–ÂÆ–VBgFW"F†R–ç7Fæ6RG&ç6f÷&Ò&V6W6RF†R–ç7Fæ6RÖG&—‚6'&–W0¢&VÂ&÷FF–öâf÷"F†RF–ÇFVB†VG2à¢Ò¢¥F†RfFRÂã3V†VBvFRv27FW–âF†RÖ–FFÆRöb&×¢¢(	BæBF†RÖ÷7B6öç7–7V÷W0¢÷–âF†Rf–VÆBÂ&V6W6RfÆ÷vW"—2F†R'&–v‡FW7BF†–ær–â—Bâ†VG2†fRF†V—"÷vâ&–æræ÷rÀ¢&V6†–ær¦W&òW†7FÇ’v†W&RF†RÆçBw2&×76W2ã3RÂ6òF†R6ÖR†VG2&RG&vâæBF†P¢†VB66VW2F†R6ÖR&W77W&Rà¢Ò¢¥F†RÆGF–6R—2æ÷r–ç6WBg&öÒF†RfFR&–ær'’F†R&V'V–ÆB7FW¢¢†&–æw4f÷&’Âv†–6‚—2v†@¢Ö¶W2'&—f–ærÖÇ&VG’Öw&÷vâ–×÷76–&ÆR&F†W"F†âÖW&VÇ’&&S¢ÆçB—2Çv—2Ç&VG¢Æ6VBÂB¦W&ò†V–v‡BÂ&Vf÷&R—B—2æV"Væ÷Vv‚Fò&Rv÷'F‚ç’âF†R÷WFW"VFvR—2&÷Vv‡B'¢Ö÷f–ærF†R¦fFR¢–â†w&÷v–ærF†RÆGF–6Rv÷VÆB6÷7B3BRv–FW"æV"æçVÇW2v–ç7BbRö`¢G&–ævÆR†VG&ööÒ(	B6VR³B“²F†R–ææW"VFvR'’Ö÷f–ærF†R¦ÆGF–6R¢÷WBÂv†–6‚6÷7G2ã2Rö`¢F†RÖ–B&–æræB¶VW2F†RæV"öÖ–B7&÷76÷fW"W†7FÇ’v†W&R—B—2â7FW—2†ÇfVBFòãbÒÀ¢6–æ6R—G2¦ö"—2æ÷rF†Rv–GF‚öbF†BÖ&v–â&F†W"F†âF†Rg&WVVæ7’öbF†R&×à¢Ò¢¥F†R&÷VæB—2öæRg&ÖRÂæ÷B¦W&ò¢¢ÂæB—B—27FFVB&F†W"F†â†–FFVã¢F†R&V'V–ÆBf—&W2öà¢F†Rg&ÖRF†B6'&–W2F†RvÆ¶W"7BF†R7FWÂ6ò—B6â÷fW'6†ö÷B'’†÷vWfW"f"F†BöæP¢g&ÖRÖ÷fVB(	Bã#BÒBcg2Â&÷WBRöbÆçBw2†V–v‡BâF†RvFRvÆ·2GvVçG’ãRÐ¢6W2B&÷F‚f–Ww÷'G2æB&WV—&W2WfW'’ÆçB'&—f–ær–âg&öçBöbF†RvÆ¶W"Fò&RVæFW ¢RöbgVÆÃ²ÖV7W&VBãRà ¢¢¤6÷fW&vRÂ'BöæRÂDôäR##bÓ‚Ó3¢F†R7v&B&VG2V6‚6öÖ×Væ—G’w2÷vâ&V6÷&FVB6÷fW"â¢ ¥F†R¦öæR&V6÷&G2WF†÷"6÷fW"æÖG&—…ög&7F–öæW"6öÖ×Væ—G’æB&&U÷6ö–Åög&7F–öæ&W6–FP¦—C²FööÇ2÷fÆ–FFRç–vFW2&÷F‚æB–æFW‚æ§6öæFVæ÷&ÖÆ—6W2F†R6V6öæB6òF†Rw&÷VæB6†FW ¦6âfWF6‚—Böæ6Râ¢¦fÆ÷&æ§6†BæWfW"6¶VBf÷"V—F†W"â¢¢ÆÂFVâ6öÖ×Væ—F–W2vW&RÆçFVB@§F†RöæRÆGF–6RFVç6—G’Ã3"GVæVBöâ6Æ÷6VBvWB&—&–RÂ6òF†R6WGFÆVBF÷vâƒãCRÖG&—‚ÂãCP¦&&R'’—G2÷vâ&V6÷&B’ÂF†R6†FVB&—fW&&æ²VæFW'7F÷'’ƒãCR’ÂF†RÆ¶W6†÷&R6æBƒã3R’æ@§F†Rf÷&W7BfÆö÷"ƒã3R’vW&RG&vâ2FVç6VÇ’2&—&–RF†B6÷fW'2F†Rw&÷VæB6ö×ÆWFVÇ’âF†P¦g&7F–öâ—2æ÷rF†R&ö&&–Æ—G’ÖG&—‚ÆGF–6R6Æ÷B6'&–W2ÆçBÂ–âF†RæV"Æ–W"æBF†P¦Ö–B6&G2Æ–¶R(	BF†R'VÆRF†Rf÷&"Æ–W"†2Çv—2Æ–VBFò—G2÷vâ&V6÷&FVBFVç6—F–W2à¤ÖV7W&VB7&÷72F†RV–v‡B6öÖ×Væ—F–W2v—F‚6ÆVâ6×Æ–ær7FF–öã¢ÆçFVBFVç6—G’7ç0¢¢£"ã#(	3bã“W"Ü+"¢¢v†W&R—Bv2öæRçVÖ&W"ÂæBF†R–×Æ–VBgVÆÂÖ6÷fW"FVç6—G’w&VW2@¢¢£bã3(	3‚ãR¢¢v–ç7BÆGF–6RF†B6'&–W2rã3â¢¥vWB&—&–R—2VçF÷V6†VB¢¢†—B&V6÷&G2ã’À§6òæ÷F†–ærF†R&—&–R7vVWGVæVBÖ÷fVBÂæBF†R6†ævR6âöæÇ’WfW"&VÖ÷fR–ç7Fæ6W3¢ÖV7W&V@¦v–ç7BÖ–æB#ƒ9sƒÂvWB&—&–R—23c“s’G&—2v–ç7B3cƒc2‡F†R&W6‡VffÆVBG&r’ÂF†P§6WGFÆVBF÷vâC#’#ƒv–ç7BCCcƒ2æBF†RÖ'6‚VFvR#“’cv–ç7B3‚#3RâÃ3"6'&–W2&Wf—6VBÆ–æS¢F†RFVç6—G’$D”ò&WGvVVâGvð¦6öÖ×Væ—F–W2—2F†R&V6÷&Bw2æ÷s²F†R'6öÇWFRf–wW&RæBF†R6GW&F–öâæ6†÷"7F’Æ–&W'F–W2à ¢¢¥7F–ÆÂ÷Vã¢4õdU$tRÂ'BGvòâ¢¢F†RÖ–BÖf–VÆBF&vWG2g&öÒF†R&—&–R7vVW7FæB–â*r3fÀ¦æBF†RæV"&–ærw2§f—6–&ÆR¢&F—W2—2ãbÒ6†÷'FW"F†â—Bv2(	BF†B—2F†R÷Ö–â–ç6WBÂæ@¦—B—26÷fW&vRVW7F–öâf÷"F†—2†ÆböbF†R&6VÂFòvV–v‚à ¢¢¥F†RÖ–FFÆRÖF—7Fæ6R&–ær6VÒ—2÷WBÂ##bÓ‚Ó2(	B3f—FVÒ2â¢¢F†R÷WFW"VFvRöbF†R7v&@§v26—&6ÆR&÷WBF†RvÆ¶W"ÂæBöâw&÷VæBv—F‚Bã3gBöb&VÆ–Vb7&÷72F†Rv†öÆR&÷‚¦6öç7FçBv÷&ÆB&F—W2—26öç7FçB67&VVâ$õs¢ÖV7W&VBB¢£ãB‚¢¢öbf&–F–öâ7&÷72F†P§f–Wr&Vf÷&RF†R6†ævRÂv†–6‚—2F†R7vVWw2'&¦÷"7G&–v‡B7&÷72ÆÂ#ƒ6öÇVÖç2"2¦çVÖ&W"âWfW'’ÆGF–6R6Æ÷Bæ÷r6'&–W2—G2÷vâ÷WFW"&F—W2Âöfg6WB'’v÷&ÆBÖæ6†÷&VBg&–ævRö`¬+2ÒBgVÆÂFWF–ÂÂæBF†R&÷VæF'’7ç2¢£Rã’‚¢¢B#ƒ9sƒæB¢£rãB‚¢¢B3“9ssƒà¤—B6÷7G2æ÷F†–ær(	BG&–ævÆW2&R–Bf÷"'’F†RÆGF–6RæB6Æ÷BW6†VB÷WBöb&V6‚—0¦G&÷VB&F†W"F†âG&vâB¦W&ò†V–v‡B(	BæB—BF¶W2æ÷F†–æröfbF†R&–ærw2ÖVâ&V6‚Â6ò—@¦—2æ÷B6÷fW&vRÆ÷72G&W76VB2f—‚âgVÆÂæ÷FRæBF†RG&2–â*r3f—FVÒ2à ¢¢¥Gvòf–æF–æw2F†B6Æ–6RÖV7W&VBæBF–Bæ÷Bf—‚(	B$õD‚$U4ôÅdTB##bÓ‚Ó2â¢¢†’¢¥3f—FVÒ¦æÖVBF†Rw&öær¦öæRâ¢¢—B&VBF†R&—fW%ö&æ¶6†÷Bv–ç7B¦öæRw26÷&Fw&72BC(	3SRRÂ'W@¦w&÷VæBv—F†–âV–v‡BÖWG&W2öbvFW"—2F†RÔ%4‚¦öæR'’W‡FVçB†£FÂ&–÷&—G’s’(	BÖV7W&VB@§F†R6†÷Bw2÷vâ&æ²ÂF†R7v&BF†W&R—2R£BæB£ÂæBæöæRöb—B—2£âF†RÖ'6‚w2÷và§&V6÷&B6—2ãsRÖG&—‚æBã&&RÂv†–6‚—2v†B—B—2æ÷rÆçFVBBâ—FVÒ’6—26òæ÷rà¢†"’¢¥GvòfÆöF–ærÖÆVfVBVF–72vW&R&ö÷FVBöâG'’ÆæB(	Bd•„TBÂæB—Bv2FFf–VÆBâ¢ ¦çW†%öGfVææBç–×†VööF÷&F&R&öÆS¢VÖW&vVçFÂf÷&Ó¢ÖE÷&÷7G&FVÂã(	3ãÐ§FÆÂÂæBF†V—"÷vâV&æ6V6—2&fÆöF–ærG2–â÷VâvFW""(	B'WBF†B—2&÷6RÂæ@¦æ÷F†–ærÖ6†–æR×&VF&ÆRF—7F–æwV—6†VBvFW"Æ–Ç’g&öÒ6GF–ÂÂ6ò&÷F‚vW&RÆçFVBöâF†P¦G'’Ö'6‚VFvRÆ–¶Rç’÷F†W"VÖW&vVçC¢¢£bãRRöbF†RGVgG2¢¢öâF†B&æ²ÂG2Bæ¶ÆR†V–v‡@§7FæF–æröâ6ö–ÂÂv†–6‚—2&WGFW"W‡ÆæF–öâöbF†R'ã#R6Ò7&–w2"–â—FVÒ’F†âç’FVç6—G¦—2à ¦FFöfÆ÷&ö–æFW‚æ§6öææ÷rV&Æ—6†W2¢¦7V'7G&FW6¢¢fö6'VÆ'’(	B6ö–Æ‡&ö÷FVBw&÷VæB&÷fP§F†RvFW"ÂF†RFVfVÇBv†VâF†Rf–VÆB—2'6VçB’Â6GW&FVE÷6ö–Æ‡F†RVÖW&vVçB†&—C¢vWBw&÷Væ@¤õ"7FæF–ærvFW"ÂföÆ–vR&÷fRF†R7W&f6R’æB÷Vå÷vFW&‡&ö÷FVB&VÆ÷rF†R7W&f6RÂÆVfW0¦fÆöF–ærôâ—B’(	BWfW'’&öÆS¢VÖW&vVçF&V6÷&B×W7B7FFRöæRÂæBfÆ–FFRç–&VgW6W2à¦÷Vå÷vFW&7V6–W2–â¦öæRv†÷6RW‡FVçBæWfW"&V6†W2vFW"Â&V6W6R&V6÷&BF†B6âæWfW ¦&RG&vâ—26Æ–ÒF†RvÆ·F‡&÷Vv‚FöW2æ÷BÖ¶RâfÆ÷&æ§67Æ—G2V6‚6öÖ×Væ—G’–çFòF†P§7V'6WBÆVvÂöâV6‚6–FRöb—G2vFW&Æ–æRæB–6·2g&öÒD„BÂv—F‚F†RvV–v‡G2&Væ÷&ÖÆ—6V@¦÷fW"F†R7V'6WC¢F†R&V6÷&FVBÖG&—…ög&7F–öæ7F–ÆÂFV6–FW2†÷rÖç’6Æ÷G26''’ÆçBÂ6ð¦6ÆV&–ærF†RÆ–Æ–W2öfbF†R&æ²FöW2æ÷BF†–â—Bâ&VgW6–ærF†R6Æ÷B–ç7FVBv÷VÆB†fR&VÖ÷fV@£bãRRöbF†B7v&BÂæBãsRFöW2æ÷B7F÷ÖVæ–ærãsR&V6W6RGvòöb—G27V6–W2fÆöBà ¢¢¤ÖV7W&VBÂ&÷F‚f–Ww÷'G2â¢¢â‚Ò7vVWöbF†RÖöFVÆÆVB&÷‚f–æG2¢£#“’G'’Ö'6‚ÖVFvP§7FF–öç2¢¢ƒ#ƒ’F†RÆ6W"v–ÆÂÆçBBÆÂ’æB¢£#ƒb÷fW"vFW"¢£²F†RGvòÆ–Æ–W2vW&RÆVvÂ@¦WfW'’öæRöbF†R#ƒ’æB&Ræ÷rÆVvÂB¢¦æöæR¢¢Âv†–ÆRF†R6GF–Â7F–ÆÂ7FæG2öâ&÷F‚6–FW0¢ƒ#ƒ’G'’ò#s2vWB’âBF†RÖ'6‚ÖVFvR7FF–öâæV&W7BF†Rf÷&·2F†R7v&B—2F†R6ÖRFVç6—G’—@§v2(	B¢£"Cƒ2(i""Cƒ&ö÷FVB–ç7Fæ6W2ÂCrSS(i"CrC3RG&–ævÆW2¢¢(	BæBF†RGvò†VE÷&– ¦fÆ÷vW'2F†B7FööBöâF†BG'’&æ²Âv†–6‚&RF†RvFW"ÖÆ–Ç’&Æöö×2Â&RvöæRâvWB×&—&–P¦6öçG&öÂ7FF–öâ—2–FVçF–6ÂFòF†R'—FRâæWrvFS¢F‡&VR76W'F–öç2–â6Öö¶U÷&VæFW&W"æÖ§6F†@¦6²F†RÆ6W"—G6VÆb†fÆ÷&ç7FF–öäöf’&F†W"F†â&RÖFW&—f–ær—G2'VÆW2Â–æ6ÇVF–ærF†P¦çF’×f7V—G’†Æb(	BÆ6W"F†B&VgW6VBWfW'—F†–æröâF†B&æ²v÷VÆB÷F†W'v—6R&VB272à ¢222³B(	Bf6FW3¢vVF†W&VBvööBÂæ÷B–çFVB6ÆöæW0¥F†R'V–ÆF–æw2&VB2g&W6†Ç’–çFVBæB–FVçF–6Ââ&W6V&6‚f—'7BÂF†Vâ–×ÆVÖVçC¢Ö÷7Bƒ3P¤6†–6vòg&ÖR'V–ÆF–æw2vW&RTå”åDTBvVF†W&&ö&B÷"v†—FWv6†VB(	B–çBv2W‡Vç6—fS²¶VW §F†RFö7VÖVçFVBW†6WF–öç2W†7FÇ’2Fö7VÖVçFVB…vRÔ'Vâw2v†—FR6Vvæ6‚v—F‚'&–v‡BÖ&ÇVP§6‡WGFW'2’âFBÖFW&–Âf&–F–öâW"'V–ÆF–ær(	B&ö&BFöæR¦—GFW"ÂvVF†W&–ær'’vRöbF†P§†6RÂ&ö&B×v–GF‚—'&VwVÆ&—G’(	B6òæòGvò6†&Rf6R†W‡FVæG2Ã#"ôÃ#2&F†W"F†à§&WVF–ærF†VÒ’âÆör'V–ÆF–æw3¢†Wvâg2&÷VæBÆöw2W"&V6÷&Bâ6—FRv†B–÷R6ã²w&FRF†P§&W7B–æfW'&VFv—F‚F†RV6öæöÖ–72&wVÖVçB–âF†Ræ÷FRà ¢¢¢$&ö&B×v–GF‚—'&VwVÆ&—G’(
b6òæòGvò6†&Rf6R"—2æ÷rG'VRöbF†Rv†öÆRF÷vâ(	BBÓC’f÷ §F†R#BæÖVB'V–ÆF–æw2ÂBÓ"f÷"F†R÷F†W"3â¢¢F†RæÖVB†Æb6÷VÆBæ÷B&V6‚F†Ræöç–Ö÷W0§&öög2&V6W6RWfW'’öæRöbF†VÒ&RÖFW&—fW2'—FRÖf÷"Ö'—FRg&öÒ&6VÂ&V6—RÂ6òBÓ"WBF†P¦FVÂ”å4”DRF†R&V6—W2†FööÇ2÷6–F–æu÷7Fö6²ç–Â–×÷'FVB'’ÆÂf—fRvVæW&F÷'2æB'¦FööÇ2öFVÅ÷6–F–æu÷7Fö6²ç–’â¢¥F†R&VgWFF–öâv÷'F‚¶VW–ær—2&÷WBF†R´U’â¢¢ÃC‚&6W2¦æÖVB'V–ÆF–ærw27Fö6²öâ—G2†6Rw26öç7G'V7F–öâ6V6öâÂv†–6‚F†RæÖVB&V6÷&G26â6''¦&V6W6RF†V—"FFW2F–ffW#²ÖV7W&VBöâF†Ræöç–Ö÷W2öæW2Â¢¦ÆÂ36''¦Fö7VÖVçFVE÷&ævRæg&öÒÒƒ3RÓÓ¢¢ÂF†R&öw&ÖÖRw26÷VçB×Væ—B6öçfVçF–öâ&F†W"F†âFFP¦ç—F†–ærv2'V–ÇBâ&R×W6–ærF†R6V6öâ¶W’F†W&RFVÇ2ÆÂ3öæR7Fö6²(	BF†R&6†WG—W2p§6–ævÆR6÷W'6RöæR7FW÷fW"Â&ævR6öÆÆ6VBFòö–çBÂv†–6‚—2BÕcæBBÓC"w2fVÇB§F†—&BF–ÖRâ6òF†R&6R—2G&vâg&öÒF†Rf÷W"×7Fö6²Æ—7BöâF†R&V6÷&Bw2÷vâ7F&ÆR¶W’æBF†Và¦Gfæ6VB'’F†R6ÖRcÒ6W&F–öââ6Æ&ö&B—'2v—F†–âcÒvV&–ærF†R6ÖR&ö&BfÆÀ¢¢£“"ó#cb(i"#ó#cb¢¢7&÷72F†RF÷vâæB¢£ƒbóƒb(i"bóƒb¢¢ÖöærF†Ræöç–Ö÷W2&öög3²#ö`£3æöç–Ö÷W2&öög2æ÷rF–ffW"g&öÒF†V—"æV&W7BæV–v†&÷W"Âv†W&RæöæRF–BâF†R&W6–GVÂ—0§7FFVB&F†W"F†â&÷VæFVC¢&V6—RFVÇ2—G2÷vâ&6VÂöæÇ’†F÷vâ×v–FRFVÂv2ÖV7W&VB@£’óƒbæB&VgW6VBÂ&V6W6R—Bv÷VÆBÖ¶RÖ÷f–æröæR&ööb&W7FÆRWfW'’÷F†W"&6VÂw2ÖW6†W2’À¦æBf÷W"7Fö6·26ææ÷B6W&FR&ööbv—F‚æ–æRæV–v†&÷W'2â¢¤Ã“bâ¢  ¢222³R(	BF†RF÷vâw2gW&æ—GW&S¢fVæ6W2Â–&G2Âvvöç2Â6–vç2Â÷&6†W2ÂFö6·0¥F†R66VæR—2'V–ÆF–æw2öâ&&Rw&÷VæC²v÷&¶–ærF÷vâ†25ETdbâ–â÷&FW#¢†’F†P¢¢¦Væ6Æ÷7W&V&6†WG—R¢¢(	BfVæ6RÆ–æRÂvFWv’6÷VçBÂvFRv–GF‚ÂfVæ6RG—R‡–6¶WB÷&–Âð§v÷&Ò’(	BÇ&VG’F†R6–ævÆR&–vvW7B7G'V7GW&Âv¢—BF—66†&vW2F†RW7G&’Vâ†7W'&VçFÇ’§&ööfVB6†VBÂw&öævÇ’’ÂF†RvW7FW&â†÷FVÂvvöâ–&B„Ã’Â6Ç–&÷W&âw27Fö6·–&BÂv&FVâfVæ6W0¢‡F†R¶–ç¦–R×f–WrÆFR(	BæVÂ"öb·W'¥öÆÆ—6öåóƒ“6(	B6†÷w2–6¶WBÖfVæ6VBv&FVâÆ÷G0¦æBÆöÖ&&G’÷Æ'3¢&VfW&Væ6Rf÷"E$TDÔTåBÂF†R†÷W6R—G6VÆb7F—2W†6ÇVFVB“²†"’¢§6–væ&ö&G2¢¢öâ'W6–æW76W2(	BGFW7FV@¢‡F†Rw&VVâG&VRÆFRw2†æv–ær6–vã²F†RvöÆb6–vâFö7VÖVçFVB’(	B&ÖWFW"W†—7G2–à¦g&ÖU÷7F÷&Vg&öçFÂ7v—F6‚—BöâW"&V6÷&BÂÆWGFW&–ær7F—2VæG&vâ„Ã#R“²†2’¢§–&@¦ö&¦V7G2¢£¢vvöç2öG&—2†Fö7VÖVçFVBÖ—&VBöâÆ¶R7B’ÂvööG–ÆW2æBÇVÖ&W"7F6·2„÷&F–ææ6R¦Fö7VÖVçG2F–Ö&W"Â7FöæRÂ'&–6²Â&÷†W2Â&'&VÇ2”âF†R7G&VWG2’Â7&FW2æB&'&VÇ2BF†P§7F÷&W2Â¶—F6†Vâv&FVç2†f÷'Bv&FVâFö7VÖVçFVC²Fö÷'–&Bv&FVç2–æfW'&VB’Â7F÷fR—W2öà¦WfW'’g&ÖR'V–ÆF–ær„÷&F–ææ6Rb(	BFö7VÖVçFVBÂæöæRÖöFVÆÆVB“²†B’¢§÷&6†W2¢¢ôäÅ’v†W&P¦GFW7FVB÷"G—öÆöv–6ÆÇ’&wVVB(	BF†R¶–ç¦–R–§¦—2F†RGFW7FVBW†V×Æ#²Fòæ÷B&Ææ¶W@§F†RF÷vã²†R’¢¦Fö6·2÷v†'fW2¢¢BF†Rf÷'v&F–ær†÷W6W2†GFW7FVB'v—F‚—G2Fö6²ÆöærF†P§&—fW"g&öçB#²æVVG2&—fW"×v†&bÖöFRöb–W%ö7&–&’âWfW'—F†–ær–çfVçFVBvWG2—G2Æ–&W'G’à ¢¢¢†"’—26†—VBöâ4”tätRÆ–W"ÂæB—B7G'V6²öæRöb—G2÷vâ6—FF–öç2â¢¢¢¥BÓ3’¢£ ¦FF÷6–vævRöÂ&VæFW&W'2÷vV"ö§2÷6–vævRæ§6ÂvVæW&FVB'¦FööÇ2övVæW&FUö'W6–æW75÷6–væ&ö&G2ç–æB&RÖFW&—fVB'’FööÇ2ö6†V6²ç6†(	B#B&Ææ²&ö&G2öà¦'W6–æW72g&öçFvW26†÷6Vâ'’'VÆR†æÖVB&V6÷&B+rV&Æ–2G&FR+rG&FRGFW7FVB÷"–æfW'&VB+p§7FæF–ær+ræò6–vâÇ&VG’’ÂB&VgW6VB–âw&—F–ærÂWfW'’fW'FW‚w&FVB&V6öç7G'V7FVF„Ã3’À¦ÆWGFW&–ærVæG&vâW"Ã#RâGvò6÷'&V7F–öç2FòF†—2&÷‚w2÷vâÆ–æR&÷fRâ¢¥F†Rw&VVâG&VRÆFRw0¦†æv–ær6–vâ—2æ÷BWf–FVæ6RF†—2&ö¦V7B†öÆG2¢£¢FF÷6÷W&6W2ö6†Õöw&VVå÷G&VUóƒS’æ§6öæ&V6÷&G0§F†BF†R–ÖvR†2æWfW"&VVâ&WG&–WfVBæBfW&–f–VF—2fÇ6RÂ6ò—BVæFW'w&—FW2æ÷F†–æræB—0§7G'V6²g&öÒF†R&wVÖVçBâ¢¤æB'7v—F6‚F†Rg&ÖU÷7F÷&Vg&öçF&ÖWFW"öâW"&V6÷&B"6ææ÷B&P¦FöæR†W&R¢¢(	BF†B&ÖWFW"—2&ÆVæFW"w2Â6òF†R&6†WG—R&÷WFRv—G2öâ&¶S²F†RÆ–W"&÷fP¦—2F†R&VæFW&W"×6–FR†ÆbæBæVVG2æöæRâv†B†"’7F–ÆÂ÷vW3¢F†RtTäU$Dõ"†ÆbÂ6ò&¶VBF÷và¦6'&–W2—G2÷vâ&ö&G3²æBç’6÷W&6RF†Bv—fW2tõ$D”ärÂv†–6‚—2F†RöæÇ’F†–ærF†B6÷VÆ@¦WfW"WBÆWGFW&–æröâöæRà ¢¢¤æBF†BÆ7B6VçFVæ6Rv2÷fW'F¶Vâ'’F†R÷væW"(	BBÓcbÂ##bÓ‚Ó#â¢¢¢'–÷R6âæB6†÷VÆ@§WBF†RæÖRöbF†RÆö6F–öâöâF†R6–vâ&ö&BâF†R6–vâ&ö&G26†÷VÆB†fRf&–F–öâ–â6öÆ÷"æ@§7G–ÆRæB6–vævRföçBæB6öÆ÷"Â6öÖR6–vç2Ö’†ærg&öÒâvæ–æræB÷F†W'2Ö’&RöâF†P¦'V–ÆF–ær÷"–çFVBöâF†Rf6RöbF†R'V–ÆF–ærâ–÷RæVVBFòFBÖ÷&R6–vævRæB&RW&–ö@¦6÷'&V7BæB—B—2f–æR–bF†W’&R&V6öç7G'V7F–öç2â"¢6òF†RÆ–W"æ÷r6'&–W2F†RäÔRöbWfW'¦'W6–æW72—B6VÆV7G2(	BF†RæÖRF†R&V6÷&BÇ&VG’v—fW2—BÂ6òF†R6–vâæBF†R6&Bw&VR(	B–à¦öæRöbFVâ6öÆ÷W'v—2æBf÷W"ÆWGFW&f÷&×2ÂöâöæRöbf—fRÖ÷VçF–æw2†'&6¶WBÂvæ–ær†ööBÂ&ö&@¦öâF†RvÆÂÂ÷7BBF†R7G&VWBVFvRÂæBF†RæÖR–çFVB7G&–v‡BöçFòF†R'V–ÆF–ær’ÂFVÇB6ð§F†BæòGvò6–vç2v—F†–âCÒ6†&R7G–ÆR÷"w&÷VæB6öÆ÷W"âF†R6÷VçB—2#2(i"¢£32¢£¢F†P§G&FR'VÆRv–ç2tõ$µ2äBt$T„õU4R6Æ72F†B–çG2—G2f—&Òöâ—G2g&öçBæB†æw2æ÷F†–ærà¢¢¤Ã#R—2VçF÷V6†VB¢¢(	Bæò&ö&B6'&–W2â–ÖvR÷"G&FRFWf–6RÂæBF†RvöÆb—27F–ÆÂvöÆ`§v—F‚æòv÷&G2öâ—BâWfW'—F†–ærBÓcbFG2—2&V6öç7G'V7FVFæB6Æ–ÖVBB¢¤ÃS‚¢¢âv†B†"§7F–ÆÂ÷vW2—2Væ6†ævVBæBæ÷r6†÷'FW#¢F†RtTäU$Dõ"†ÆbÂæB6÷W&6RF†Bv—fW2v÷&F–ærÂ¦6öÆ÷W"÷"Ö÷VçF–ærf÷"æÖVB†÷W6Rà ¢¢¤æBF†Rv÷&F–ær—G6VÆbv26÷'&V7FVBF†RæW‡BF’(	BBÓ3Â##bÓ‚Ó#"Â6òF†R&w&‚&÷fP¦—2æ÷rF†R&wVÖVçBF†Bv2f–Æ&ÆR&Vf÷&RF†R÷væW"&VB&ö&Bâ¢¢BÓcb–çFVBD„P¥$T4õ$Bu2õtâäÔRÂv†–6‚—2F†—2&ö¦V7Bw2Æ&VÂf÷"%T”ÄD”äræBæ÷Bv†B6–vçw&—FW ¦ÆWGFW&VBâF†R÷væW"ÂöbF†R6'VçFW"&ö&C¢¢'†–Æòv÷VÆBæ÷B†fR&VfW'&VBFò†—2÷vâÆ6R0¦ÆörG'Vr7F÷&R(
bF†BÖ’&RF–ffW&VçBF†âF†RæÖRöbF†R'V–ÆF–ærf÷"W2ÂF†R6–vâÖ’&V@¦F–ffW&VçFÇ’†—7F÷&–6ÆÇ’"£²öbF†RæW‡C¢¢'6ÖRv—F‚†övâw27F÷&R"£²æBF†Vâ¢&’wVW72Fò70¦öâÆÂF†÷6R6–vç2æBÖ¶R7W&RF†W’fVVÂ&–v‡Bf÷"F†RW&â"¢ÆÂ32&R&RÖÆWGFW&VB–âF†P§&Vv—7FW"F†RF÷vâw2÷vâæWw7W"GfW'F—6–ærW6W2(	B&÷&–WF÷"÷"f—&Òf—'7BæBÆ&vW7BÂF†P§G&FR&VæVF‚ÂF†RÆ6RÆ7BæB6ÖÆÆW7B(	Bv—F‚F†Rv÷&F–ær2—G2õtâf–VÆBÂg&VRFòF–ffW ¦g&öÒF†RæÖVæBF–VBFò—BöæÇ’'’FV6Æ&VB6–våö–FVçF—G–F†B×W7BV"–â&÷F‚à¢¢£B6''’f—&Òw2÷vâGfW'F—6VBÆ–æR†–æfW'&VF’¢¢Â’&R&V6öç7G'V7FVFg&öÒF†RG&FP§fö6'VÆ'’F†÷6RvW2Wf–FVæ6RÂæB¢¦æöæR—2GFW7FVF¢¢Â&V6W6RF†R6WfVâæWw7W"vW0¦&V†–æBF†VÒ&R–ÖvW27WÆ–VB–â6öçfW'6F–öâæB&Ræ÷B6öÖÖ—GFVBFòFF÷6÷W&6W2ö76WG2öà¤WfW'’öæRöbF†÷6Ræ÷FW26—2v†Bv÷VÆBWw&FR—BæBF†R&V6—R—2–âF–6¶WB¢¥BÓ3¢¢Â6ð§v†B†"’7F–ÆÂ÷vW2†26†ævVB6†S¢æ÷B&6÷W&6RF†Bv—fW2v÷&F–ær"(	BF†Rv÷&F–æw2&R†W&P®(	B'WB¢§F†R6WfVâvW26öÖÖ—GFVB26÷W&6R&V6÷&G2¢¢Âv†–6‚v÷VÆBF¶Rf÷W'FVVâöbF†VÒöf`¦–æfW'&VF–ââgFW&æööââ¢¤Ã#R—25D”ÄÂVçF÷V6†VB¢¢ÂæBBÓ3—2F†R66RF†B6†÷w2v‡’—B—0¦&÷WB”ÔtU2&F†W"F†â&÷WB6–vç3¢6'VçFW"w2÷vâƒ3Ræ÷F–6R†VG2—G6VÆb¢$BD„R4”tâôbD„P¤tôÄDTâÔõ%D""¢Â6ò†—2&ö&B6'&–W2–çFVBÖ÷'F"(	BFWf–6R—G2÷væW"FW67&–&VB–â&–çB(	@§v†–ÆRF†RvöÆbÂv†–6‚æö&öG’FW67&–&VBÂ—2ÃcRw2æB&W7G2öâ6VçFVæ6R6––ærvöÆbv2öâ—Bà¤æò÷F†W"&ö&BvWG2FWf–6RÂæBF†R6Öö¶R–ç2F†B6÷VçBBöæRâ¢¤Ãcbâ¢  ¢¢¢†2’—26†—VB”â%BÂöâ”$BÆ–W"ÂæB—G2Wf–FVæ6R—2F†R7G&öævW7BöâF†—2&÷‚â¢ ¢¢¥BÓC¢£¢FF÷–&BöÂ&VæFW&W'2÷vV"ö§2÷–&Bæ§6ÂvVæW&FVB'’FööÇ2övVæW&FU÷–&EövööG2ç– ¦æB&RÖFW&—fVB'’FööÇ2ö6†V6²ç6†(	B¢£C’ö&¦V7G2B#bG&F–ærg&öçFvW2¢¢ƒ"W&–v‡B66·2À£Cb6¶–ær66W2ÂâV×G’Æ–Böâ—G26–FR÷WG6–FRF†RV&Æ–2†÷W6W2’æB¢¦öæRvvöâ¢¢ÂWfW'§fW'FW‚w&FVB&V6öç7G'V7FVF„Ã3’Âæò'&æBÂæÖRÂ7FVæ6–Â÷"Æ&VÂöâç’öbF†VÒâVæÆ–¶R†"’À§F†—26ÆW6RFöW2æ÷B&W7BöâG&VFÖVçB&wVÖVçC¢¢¤÷&F–ææ6R’öbræ÷fVÖ&W"ƒ32—2F–W"Ó¦6öçFV×÷&'’7FFVÖVçBF†BF†—2F÷vâw27G&VWG2†BF–Ö&W"Â7FöæRÂ'&–6²Â&÷†W2æB&'&VÇ0§7FæF–ær–âF†VÒ¢¢†FF÷6÷W&6W2ö6†–6võöFVÖö7&Eóƒ35óó#bæ§6öæ’ÂæB6÷'÷&F–öâFöW2æ÷@¦ÆVv—6ÆFRv–ç7BF†–æræö&öG’FöW2âv†B—Bv—fW2—2æòFG&W72BÆÂÂ6òv†–6‚g&öçFvR—2§'VÆR(	BæÖVB&V6÷&BÂvööG2Ö¶VW–ærG&FRÂF†BG&FRGFW7FVB÷"–æfW'&VBÂöâF†RDõtâw0¦w&÷VæB‡F†Rf÷'Bw2&÷f—6–öâ7F÷&RæBF†R7WFÆW"w2&R&VgW6VC¢fVFW&Âw&÷VæBÂæò6÷'÷&F–öà§7G&VWB–âg&öçBöbF†RFö÷"’â¢¤öæR6÷'&V7F–öâFòF†—2&÷‚w2÷vâÆ–æRâ¢¢¢'vvöç2öG&—0¢†Fö7VÖVçFVBÖ—&VBöâÆ¶R7B’"¢(	B¢§F†—2&ö¦V7B†öÆG2æò6÷W&6R&V6÷&Bf÷"F†B6Æ–Ò¢¢Â6ò—@§VæFW'w&—FW2æ÷F†–æræB—27G'V6²âF†RvvöâF†B•2G&vâ&W7G2öâ6†–6vöÆöw•÷&Vf—&S#s†æ@§F†RvW7FW&â†÷FVÂw2–&BÂF†RöæRÆ6R–âF†RF÷vâæÖVBf÷"vvöç2ÂB7FæBFW&—fVB&F†W §F†â–6¶VBâv†B†2’7F–ÆÂ÷vW3¢¢§F†RF–Ö&W"Â7FöæRæB'&–6²†Æböb÷&F–ææ6R’¢¢Âv†–6‚—0¦'V–ÆF–ærÖFW&–ÂöâÆ÷BVæFW"6öç7G'V7F–öâ&F†W"F†âÖW&6†çBw27Fö6²æB—2f–ÆVB2—G0¦÷vâF–6¶WC²vööG27FæF–ær–â$ôEt’Âv†–6‚—2F†R÷&F–ææ6Rw2÷vâ7G&öævW"&VF–æræB—0¦FVÆ–&W&FVÇ’æ÷BG&vâ†W&S²7F÷fR—W2öâWfW'’g&ÖR'V–ÆF–ær„÷&F–ææ6Rb“²æBF†RvVæW&F÷ ¦†ÆbÂ6ò&¶VBF÷vâ6'&–W2—G2÷vâ–&G2à ¢¢¢†R’—26†—VBöât„$bÆ–W"ÂæB—B—2F†R6ÆW6RöâF†—2&÷‚F†B†B&VVâ÷vVBÆöævW7Bâ¢ ¢¢¥BÓC¢£¢FF÷v†'fW2öÂ&VæFW&W'2÷vV"ö§2÷v†'fW2æ§6ÂvVæW&FVB'¦FööÇ2övVæW&FU÷&—fW%÷v†'fW2ç–æB&RÖFW&—fVB'’FööÇ2ö6†V6²ç6†(	B¢§GvòFö6·2Â#b7&–"&VçG2À¦WfW'’fW'FW‚w&FVB&V6öç7G'V7FVF„Ã3"’¢¢â¢¥F†—2&÷‚w2÷vâÆ–æR6–B—B&æVVG2&—fW"×v†&`¦ÖöFRöb–W%ö7&–&"ÂæBF†B—2$´R&V6öâ¢£¢F†R&VæFW&W"×6–FR†ÆbæVVG2æò&ÆVæFW"ÂF†P§6ÖR&wVÖVçBF†BÇ&VG’6'&–W2†’Â†"’æB†2’âv†–6‚g&öçFvR—2'VÆRæB—B&VG2F†P§&V6÷&G2&F†W"F†âG&FRF&ÆR(	B6–FV6"7FæF–æröâF†R66VæRFFRv†÷6R÷vâFö6¶ ¦GG&–'WFR—2G'VRæBw&FVBGFW7FVF÷"–æfW'&VFÂv†–6‚6VÆV7G2W†7FÇ’F†RGvòv&V†÷W6W0§F†—2Æ–æR6—FW2æB&VgW6W2WfW'’÷F†W"&—fW"g&öçFvR–âF†RFF6WBâF†R÷WFÆ–æR—2FW&—fV@¢‡F†R6öÖÖ—GFVBfö÷G&–çBw2Ö‚ÖfVFvRÂF†RG&6VBƒ3B&æ²w2÷vâFævVçBBF†RæV&W7Bö–çBÀ§F†R6öÖÖ—GFVB†V–v‡Ff–VÆBf÷"F†RFWF‚BF†Rf6R’æBF†R4•¤R—2–çfVçFVBv—F†–â7FFVB&÷VæG3°§F†RFV6²w2†V–v‡B—2F†RFW'&–âw2Â6×ÆVBBÆöBÂv†–6‚—2BÓw2f–æF–ærÆ–VBFòÆ–W §F†B†2æòvÆ²7W&f6RFò6F6‚—BGv–6Râ&÷F‚Fö6¶GG&–'WFW2Ö÷fRg&öÒvVöÖWG'“¢&'6VçB& §Fò'6–×Æ–f–VB&Âv†–6‚—2F†R†Æböb¢¤Ãcb¢¢F†—2F—66†&vW2(	BF†R&æ²V6‚v&V†÷W6R7FæG2öà¦—2VçF÷V6†VBæB7F–ÆÂ÷Vââv†B†R’7F–ÆÂ÷vW3¢FV6²f—6—F÷"6âvÆ²÷WBÆöær†—G2÷và§F–6¶WB“²ç—F†–ærÇ––ærBV—F†W"v†&bÂv†–6‚æò6÷W&6R†W&RFW67&–&W3²æBF†RtTäU$Dõ"†ÆbÂ6ð¦&¶VBF÷vâ6'&–W2—G2÷vâFö6·2à ¢¢¤æB'F†RtTäU$Dõ"†Æb"—2æ÷rôäRVW7F–öâf÷"ÆÂf÷W"6ÆW6W2Âæ÷Bf÷W"(	BBÓS§v—F†G&vâÂBÓ#S"÷VæVBÂ##bÓ‚Ó#râ¢¢F†—2&÷‚6·2f÷"—B–âæV&Ç’F†R6ÖRv÷&G2B†"’À¢†2’æB†R’ÂæBBÓS’v2†R’w2âÖV7W&VB'’FööÇ2öÖV7W&UövVæW&F÷%ö†Æbç–æBvFVB–à¦FööÇ2ö6†V6²ç6†¢¢¦æ–æRöbæ–æRFFÆ–W'2G&vâBÆöBg&öÒ6öÖÖ—GFVB¥4ôâ÷vRvVæW&F÷ ¦†ÆbÂæBæöæR†2öæR¢¢(	B&öG2ÂVæ6Æ÷7W&W2ÂfVæÂfÆ÷&Âg&öçFvRÂ&W6–FVçG2Â6–vævRÀ§v†'fW2Â–&BâF†W&R—2¢¦öæR&VæFW&W"¢¢Â&VæFW&W'2÷vV&ÂæB—BG&w2ÆÂæ–æRÇ&VG’Â6ð§F†RtÄ"F†W6R6ÆW6W26²f÷"†2æò&VFW"FöF’âæBF†Rf—'7BÆ–W"FòF¶RF†R&÷WFR—0¦f÷"F†R÷F†W"V–v‡C¢æWr&6†WG—RVçFW'2vVæW&F÷'2ö'V–ÆBç–w2$4„UE•U6&Vv—7G'’À§v†÷6R'—FW2&R†6†VB–çFò¢£3CröbF†R3C’¢¢6öÖÖ—GFVBÖW6†W2Â6ò—B6÷7G2gVÆÂF÷vâ&V&¶P¦&Vf÷&R—B'V–ÆG2G&–ævÆR(	Bv†–ÆR¦ÖöFR¢–ç6–FRâW†—7F–ær&6†WG—R6÷7G2Gvòâ†R’—0¦Ç6òF†Rv÷'7BöbF†Ræ–æRFò7F'Bv—Fƒ¢v†'fW2æ§6F¶W2—G2FV6²†V–v‡BÂWfW'’7&–"&Vç@¦æB—G27F—"G&VB6÷VçBg&öÒFW'&–âç7W&f6T†V–v‡F¢¦BÆöB¢¢ÂæBtÄ"g&VW¦W2ÆÂF‡&VP¦BF†R†V–v‡Ff–VÆBöbF†R&¶R(	BBÓw2fVÇBÂ'’6öç7G'V7F–öâÂ–âF†RÆ–W"F†B6—FW0¥BÓ2F†R&V6öâ—B6×ÆW2BÆÂâ6òF†R6ÆW6R—2æ÷B&VgW6VBæBæ÷B6†—VC¢—B—0¢¢§&VfW'&VB¢¢Âv†öÆRÂFòBÓ#S"Âv†W&RF†R÷væW"FV6–FW2—Böæ6Rf÷"ÆÂæ–æRà ¢¢¢†R’w&WrF†—&B6†÷&Röâ##bÓ‚Ó#BÂæBF†R&V6öâF†Rf—'7BGvòvW&RF†RöæÇ’Gvò—2v÷'F€§&V6÷&F–ærâBÓc"¢¢7FFVBf—fR&V6öç7G'V7FVBFö6·2öâF†R÷væW"w2¢'–÷R6âFBÖ÷&RFö6·2"¢(	Bæ@¦—B7FFVBF†VÒöâ¢¥6÷WF‚vFW"ÖW&6†çG2¢¢Â6òF†RF÷vâw2÷F†W"6†÷&W2vW&RæWfW"6¶VBâF†Ræ÷'F€¤F—f—6–öâ6†÷&R†BÆæF–æröæÇ’&V6W6R¶–ç¦–Rb‡VçFW"w2Fö6²—2GFW7FVC²F†RvW7B&æ²BvöÆ`¥ö–çBÂf—fR'V–ÆF–æw2ÆÂg&öçF–ærF†RvFW"Â†BæöæRâ¢¥BÓr¢¢6·2F†RG&FRFW7BöbWfW'’&—fW ¦g&öçFvR–âF†RF÷vâÂæBöâF†RvW7B&æ²—B6VÆV7G2W†7FÇ’öæR&V6÷&C¢¢¥&ö&W'Bâ¶–ç¦–Rw0§7F÷&V†÷W6R¢¢Â&FVÆ–ær–âw&ö6W&–W2æB–æF–âvööG2"Âv†÷6R6öÖÖ—GFVB÷6—F–öâæ÷FRöb##bÓ‚Ó¦†BÇ&VG’&V6öæVBF†B¢&7F÷&V†÷W6RG&F–ærvööG2öfb6æöW2†2÷6—F—fR&V6öâFòf6RF†P¦ÆæF–ær"¢âf—fRÆæF–æw2æ÷r7FæBv†W&Rf÷W"F–B„Ãs’’âF†R&÷rw2÷F†W"f÷W"7FFRæòFö6²æBvW@¦æöæR(	BÆöFv–ærÂGvVÆÆ–æræBv÷'6†—F¶Ræ÷F†–æröfb6æöRâ—BÇ6ò6†—VB¢¦6ÆW6Rb¢£¢F†P¦FV6²—2öæR7FæF&B&V7FævÆR6WBöâF†R&æ²w2÷vâFævVçBÂ¢§F†R&æ²&VæG2BvöÆbö–çB¢¢Âæ@¦f6RF†Bv÷VÆB7FæBöâG'’w&÷VæB…"3#S‚ÖV7W&VB(‰#ã3BÒB†övâw27F÷&R’—2&VgW6VBv—F€§F†RÖV7W&VB&—6RöâF†R&V6÷&B&F†W"F†âv—fVâ&W7ö¶R÷WFÆ–æRâF†R6ÆW6R&VgW6W2æ÷F†–ær–à§F†RF÷vâ2—B7FæG2æB—2&÷fVB'’vVæW&FU÷&—fW%÷v†'fW2ç’Ò×6VÆgFW7FÂv†–6‚ÒÖ6†V6¶'Vç2à ¢¢¢†’—26†—VB–âF‡&VR–V6W2ÂÆÂöâF†RVæ6Æ÷7W&RÆ–W"¢¢†FFöVæ6Æ÷7W&W2öÀ¦&VæFW&W'2÷vV"ö§2öVæ6Æ÷7W&W2æ§6’(	BF†R&VæFW&W"×6–FR†ÆböbF†R&6†WG—RF†—2&÷‚6¶VBf÷"À§v†–6‚æVVG2æò&¶Râ¢¥BÓS¢¢'V–ÇBF†RÆ–W"æBF†RvW7FW&â†÷FVÂw2vvöâ–&B„Ã#r“°¢¢¥BÓS¢¢Ö÷fVBF†RW7G&’VâöçFò—BæB&WF—&VB—G2&ööb„Ã#‚ÂÃc&W6öÇfVB“²¢¥BÓS"¢ ¦FFVBF†R–6¶WFfVæ6RG—RæBF†R¢¦Fö÷'–&Bv&FVâÆ÷G2¢¢F†—2Æ–æR6—FW2F†R¶–ç¦–R×f–Wp§ÆFRf÷"(	B‚öbF†VÒÂöâÆGFVB†÷W6RÆ÷G26†÷6Vâ'’'VÆRæBvVæW&FVB'¦FööÇ2övVæW&FUöFö÷'–&E÷–6¶WG2ç–&F†W"F†âÆ6VB„Ã#’“²¢¥BÓSR¢¢F†Vâ–FVçF–f–VBF†@§ÆFRÂv†–6‚BÓS"6÷VÆBöæÇ’6—FR'’6öÖÖ—GFVBF‚Â2¢§æVÂ"öb·W'¥öÆÆ—6öåóƒ“6¢¢(	B§6÷W&6R&V6÷&BF†—2&ö¦V7B†B†VÆBÆÂÆöær(	BæBf–ÆÆVBF†RVæ6Æ÷7W&R&V6÷&Bw2V×G¦W†—7FVæ6Rç6÷W&6W6v—F‚—BâF†RÆFR7F—2F–W"RæBF†RfVæ6R7F—2&V6öç7G'V7FVF²v†BF†P¦–FVçF–f–6F–öâ'W—2—26—F&ÆRö&¦V7Bv—F‚FFRÂV&Æ—6†W"ÂÆ–'&'’öb6öæw&W726÷’æ@¦âW‡—&VBƒ“26÷—&–v‡B–âÆ6Röb3“×—†VÂ7&÷öbVç7FFVB&–v‡G2âv†B†’7F–ÆÂ÷vW3¢6Ç–&÷W&âw0§7Fö6·–&BÂF†R–rVç2F†Ræ÷fVÖ&W"ƒ32F÷vâ6öFR–×Æ–W2ÂF†RfVæ6VBÖ÷"×VæfVæ6VB7FFRöbF†P§V&Æ–27V&RÂæBF†RtTäU$Dõ"†Æb(	BÆ—6FV7F–ÆÂ'V–ÆG2æòVæ6Æ÷7W&Rf÷&ÒÂ6òæ÷F†–ær†W&P¦—2&¶VBv—F‚F†RF÷vâà ¢222³b(	BF†R&—fW"'VÆvRB6Æ&²7G&VWB+r¢¤DôäR##bÓ‚Ó2¢ ¤æ÷BW"7G&WF6‚æBæ÷BÖ—2×G&6VB7G&VÓ¢F†RG&6VB6÷WF‚&æ²†B&VVâvÆ¶VB&÷Væ@§F†R¢¦÷WFÆ–æR6—FÂröb$4„”4tò$•dU""¢¢Âv†–6‚w&–v‡BÆWGFW'27&÷72F†R6†ææVÂÂ¦ö–æV@§FòF†RG&vâ&æ²'’'&÷vâf÷†–ær7F–ââFööÇ2÷G&6U÷6†÷&VÆ–æRç–v–æVBFV6Æ&V@¦ÄUEDU$”ävv–æF÷rF†B&VG2F†RÖw2÷vâG—R2G—RÂ7Æ–6VB–çFòF†RVæ6÷'&V7FVB&–æp§6òF†RFV6Æ&VB&÷‚—2F†R&Æ7B&F—W2â†V–v‡Ff–VÆB&VvVæW&FVC¢¢£6VÆÇ26†ævVB÷WG6–FP§F†R6÷'&–F÷"R³SR(
b³ccÂÖ‚ÆFVÇFÂãÒÂvFW&Æ–æR7&÷76–æw2¢£²–ç6–FR—Bs¦6VÆÇ2ÂÖ‚2ãcRÒÂc#7&÷76–æw2ÂÆÂÆæB(i"vFW"âw&F–VçBVF—BVæ6†ævVBæB76–æp¢†Æ–åö&Æö6µöÖ†ãCc‚gBò3gB’âÖVÖó ¦Fö72õ$U4T$4‚ö6Æ&µ÷&V6…ö'VÆvUóƒ3BæÖFâF†RsŽ(	3ƒÒg2^(	3’Ò6÷WF‚vFW"F—67&Wæ7§F†—2—FVÒ6—FVBv2F†—2FVfV7BÂ6ò¢¦Fö72õ$U4T$4‚ö6†–6võöÖW&–6åööff–6RæÖF*r2æ÷p¦÷fW'7FFW2F†R6Æ&²&W6–GVÂ¢¢æB6†÷VÆB&R&RÖÖV7W&VBv–ç7BF†R6÷'&V7FVBG&6Rà  ¢222³r(	BF†ö×6öâÆBÆ÷BÆ–æW2+r¢¥„4RôäRDôäR##bÓ‚Ó2¢ ¤vVæW&FR&Æö6²öÆ÷BvVöÖWG'’æÇ—F–6ÆÇ’g&öÒF†RÆBÖöGVÆRƒƒÖgB7G&VWG2ÂFö7VÖVçFVBÆ÷@§v–GF‡2’Â6æVBFòF†RFGVÒ(	BF†R36''’Öf÷'v&Bæ÷FRÇ&VG’&W67&–&W2W†7FÇ’F†—2à¤6öÖÖ—B2FF÷G&6W2÷fV7F÷'2÷F†ö×6öåöÆ÷G2æ§6öæâ—B&V6öÖW2F†RÆ6VÖVçBw&–Bf÷"³w0¦–æfW'&VB7G'V7GW&W2æBF†R6†V6²öâWfW'’&6÷&æW"öb‚æB’"÷6—F–öâ–âF†RFF6WBà ¢¢¥6†—VB¢£¢’&Æö6·2ÂS"Æ÷G2ÂvVæW&FVBg&öÒF†RÖöGVÆRæBF†—2&ö¦V7Bw26öÖÖ—GFVB7G&VW@¦Æ–æW2'’FööÇ2övVæW&FU÷ÆEöÆ÷G2ç–Â&RÖFW&—fVB'—FRf÷"'—FR–âFööÇ2ö6†V6²ç6†â&Æö6²VFvW0¦&R–æfW'&VF†&—F†ÖWF–2öâ–æfW'&VB7G&VWBÆ–æW2æBâ–æfW'&VBÖöGVÆRv–GF‚“²F†RÆ÷BÆ–æW0¦æBF†RÆÆW’õ4•D”ôâ&R6öæ¦V7GW&ÆæB6’6ò(	Bf÷W"Æ÷G2Fòf6R—2&VF–æröböæP¦&Æö6²Â&Æö6²‚öâF†R÷væW"w26Æ&²×&V6‚7&÷âæòÆ÷B÷"&Æö6²—2çVÖ&W&VC¢F†—2&ö¦V7B†0¦æWfW"&VBF†ö×6öâw2çVÖ&W&–æröfb6†VWBâf—fR6æF–FFR&Æö6·2&R&VgW6VBv—F‚F†V— §&V6öç2ÂF‡&VRöbF†VÒ&V6W6R&Æö6²F†W&Rv÷VÆB7âF†R6÷WF‚'&æ6‚âÖVÖó ¦Fö72õ$U4T$4‚÷F†ö×6öå÷ÆEöw&–BæÖFà ¢¢¥v†B†6RGvò–æ†W&—G2â¢¢†’çå6WfVâ7G'V7GW&W27FæBbã^(	3"ãÒ–ç6–FRÆGFVB7G&VW@¦6÷'&–F÷'çâ(	B¢¤DôäR##bÓ‚Ó2VæFW"³†6RF‡&VR†’¢£¢F†RvFRW†—7G0¢†FööÇ2÷ÆEö6÷'&–F÷'2ç–Â6†&VBv—F‚Ò×&W÷'F’Â#2&V6—R6VçG&W2Ö÷fVB6ÆV"ÂæBF†P§&W÷'Bæ÷rÖV7W&W2dôõE$”åE22vVÆÂ26VçG&W2Âv†–6‚—2v†B6†÷vVBF†R6WfVâFò&RF†RÆ÷V@¦VæBöb6WBöb#2âçåv†B—2ÆVgB–âF†R&öGv’—2æ÷BF†RvVæW&F÷"w3¢¢¦f÷W"æöç–Ö÷W2&öög2¢ ¦g&öÒF†RGvò–æf–ÆÂvVæW&F÷'2‡v÷'7B&V6öåóƒ3U÷6÷WF…öUóCFÂBã2Ò(	BF†BvFR—2FFVBv†Và§F†B&6VÂæW‡B'Vç2Â&V6W6RÖ÷f–ærâæöç–Ö÷W2&ööb&RÖFW&—fW2F†Rö67Wæ7’ÆVFvW"F†÷6P¦vVæW&F÷'2÷vâ—çâ(	B¢¤DôäR##bÓ‚Ó22†6RGvò†"’¢£¢&÷F‚–æf–ÆÂvVæW&F÷'26''’F†RvFRÀ§F‡&÷Vv‚F†R6ÖRFööÇ2÷ÆEö6÷'&–F÷'2ç–ÂæB¢¦æòvVæW&FVBÆ6VÖVçBç—v†W&R–âF†—2FF6W@§7FæG2–âÆGFVB6÷'&–F÷"¢¢†fö÷G&–çG2–â6÷'&–F÷"32(i"#’’âF†Rf÷W"vW&RöæR&÷rw0§76–ærÂæ÷Bf÷W"çVÖ&W'3¢F†R&6VÂw2V–v‡Bæ6–ÆÆ'’'V–ÆF–æw2vW&RÆ–Böâ#2Ò—F6‚(	@§F†R&Æö6²—F6‚(	Bv†–6‚WBöæRBF†RV7FW&âVFvRöbWfW'’&Æö6²ÂæBF†Rf÷W"F†B76V@§76VB'’&V–ær&—f–W2&F†W"F†â'’&V–ærÆ6VBƒãN(	3"ãÒ6ÆV"v–ç7B+#Ð¦vV÷&VfW&Væ6R’âÆÂV–v‡Bæ÷r7FæB&V†–æBF†RV7FW&æÖ÷7B&–æ6—Â&ööböbF†V—"÷vâ&Æö6²À§v†–6‚—2v†B&V"–&B—3²~(	33"ÒöbÖ÷fVÖVçBÂæ÷F†–ær&Vw&FVBÂæBF†R†÷W6V†öÆBÆVFvW ¦¶W—2öâ–B6òF†RF÷F–öç27W'f—fVBâFWF–Â–âFö72õ$U4T$4‚÷F†ö×6öå÷ÆEöw&–BæÖF*rv"âv†@¦—2ÆVgB—2¢£#’†æB×Æ6VB&V6÷&G2v†÷6R÷6—F–öç26''’g&öçFvR&wVÖVçB¢¢âö`§F†÷6RÂF†—'FVVâ&Röâ6÷WF‚vFW"7G&VWBæBF†W’&Rf–æF–ær&F†W"F†âVWVS¢g&öÒ6÷WF€¥vFW"w26öÖÖ—GFVB6VçG&VÆ–æRF†RG&6VBƒ3BvFW&Æ–æR—2¢£ãsRÒv’BR³ƒv–ç7B£"ã’Ò†ÆbÖ6÷'&–F÷"¢¢Â6òF†RÆGFVB7G&VWBF†W&R'Vç2ãBÒ–çFòF†R&—fW"æB'V–ÆF–æröà¦—G2æ÷'F‚6–FR6ææ÷B&R&÷F‚6ÆV"öbF†R6÷'&–F÷"æBöâG'’ÆæBâF†B—2F†RÆBÖöGVÆRæ@§F†RG&vâ&æ²F—6w&VV–ærÂæB—BvçG2&VF–æröbF†RG&fVÆÆVBv’„Ãs’’Âæ÷BçVFvRFð§F†—'FVVâ&V6÷&G2âF†R6Vvæ6‚w2f—'7B6&–â&VÖ–ç2F†R&VÖ–æFW"F†B'V–ÆF–ær–âF†R7G&VW@¦—26öÖWF–ÖW2f7BÂæB6Æ÷Vv…öÆöuö'&–FvV–âF†R6÷WF‚vFW"6÷'&–F÷"—2F†R&VÖ–æFW"F†@§6öÖWF–ÖW2—B—2F†Rö–çBâ†"’F†Rw&–@¦6÷fW'2’öbF†RÆBw2S‚&Æö6·3²F†Ræ÷'F‚F—f—6–öâ—2'6VçB&V6W6R—G27G&VWB6öçG&öÂ—0§v†B*r3’7F–ÆÂ&V6÷&G22÷vVBÂæB&Æµ÷6÷WF…÷vFW%öÖ&¶WF(	BöæRöbF†RÖ÷7B'V–ÇB×W&Æö6·0¦–âF÷vâ(	B—2&VgW6VBöæÇ’&V6W6RF†R7G&VWBÆ–W"FöW2æ÷B6''’6÷WF‚vFW"vW7BöbR³à¢†2’Gvò—F6†W2F—6w&VRv—F‚F†Rƒ3BG&fW'6W2„FV&&÷&î(i%7FFR#‚ãÒÂÆ¶^(i%&æFöÇ‚C"ã‚Ò¦æB&R&V6÷&FVB&F†W"F†âfW&vVBâ†B’æò6÷W&6R–âFF÷6÷W&6W2öv—fW2F†ö×6öâÄõ@¤DUDƒ²F†RFWF‡2†W&R&R&W6–GVÇ2öbF†R&Æö6²ÂæBf–æF–ær7FFVBöæR—2v†Bv÷VÆBÖ÷fP§F†RÆ÷BÆ–æW2öfb6öæ¦V7GW&Râ†R’æ÷F†–ærG&w2F†Rw&–B(	Bv†VâF†RÆ÷BÆ–æW2&V6‚F†R67&VVà§F†W’æVVBÆ–&W'G’æB6öæf–FVæ6RG&VFÖVçBv—F‚F†VÒà ¢222³‚(	B&—fW"&æ²†V–v‡G2¢‡&W6V&6‚f—'7BÂF†VâFW'&–â’¢+r¢¤DôäR##bÓ‚Ó#…BÓB’¢ ¥F†R÷væW#¢&æ·2Æöö²FöòÆ÷rv–ç7BF†Rf÷'Bf–Ww2ƒ(	3#gBv—F‚w&GVFVB6Æ÷W2’âF†P¦F÷76–W"v—fW2³.(	3BgB&æ·2BF†Rf÷&·2†Fö7VÖVçFVB’'WBF†Rdõ%B7FööBöâF—7F–æ7FÇ’&—6–æp¦w&÷VæB(	B'F†RfÆGFVæVBÖ÷VæB"ÂF†Rƒ3†'&—6öâÆâw2&æ²Â7vV&–ævVâw2‚ÖgBööÂBF†P¦f÷'B&VæBâ&6VÃ¢&R×&VB×FW'&–âÖ‡–G&öÆöw’æÖFæBF†R&–Ö'’66÷VçG3²&—6Ræ@¤u$ETDRF†Rf÷'B×&V6‚6÷WF‚&æ²2F†RWf–FVæ6R7W÷'G3²&V6÷&BF†RF—6w&VVÖVçB&WGvVVà§F†RF–W"ÓRÆ—F†öw&‡2æBF†RF÷76–W"&F†W"F†âfW&v–ær—C²¶VWF†Rf÷&·2&æ·2BF†V— ¦Fö7VÖVçFVB†V–v‡Bâw&F–VçBVF—B&R×'Vã²W†V×F–öâ—FVÖ—6VBÆ–¶RF†R÷F†W'2à ¢¢¥6†—VB¢£¢F†RÖ÷VæB&—6VBg&öÒF†R¦öæRw2Ö–B×&ævRFò—G27FFVBW‚(	@¦f÷'EöFV&&÷&åöÖ÷VæBç&—6UögF"ã‚(i"2ã‚ÂfÆBF÷³ã(i"³"ãgBÂF†Ræ÷'F‚f6R6''––æp§F†RgVÆÂ&—6RFòF†RvFW&Æ–æRB£bã‚†–ç6–FRF†R&æ²&Æö6²w2£n(	3£&æB’âF†P¦F—6w&VVÖVçB—2F‡&VRÖ6÷&æW&VBÂæ÷BGvòÂæB—2&V6÷&FVB&F†W"F†âfW&vVB–à¦Fö72õ$U4T$4‚öf÷'E÷&V6…ö&æµö†V–v‡G2æÖF¢F†Rv—FæW76W2…7vV&–ævVâƒ2F–W"Óã‚gC°¤‡V&&&Bƒƒ&æ÷B÷fW"V–v‡BfVWB"Â6÷'&V7F–öâW6†–ærDõtâ’¶VWF†R$ä²Â¦öæRbw0¢³(	3"öW‚³"F¶W2F†RÖ÷VæBÂæBF†RÆFW2r(	3#gB—2&VgW6VB2'V–ÆB–çWBà¤‡V&&&B×g2×¦öæRÓb7FæG2Vç&W6öÇfVBöâF†R&V6÷&B(	B–bF†R÷væW"'VÆW2F†Rv—FæW76W2÷WG&æ°§F†RF÷76–W"w2&V6öæ6–Æ–F–öâÂF†RÖ÷VæBG&÷2Fòâ³ƒ²F†B—2'VÆ–ærÂæ÷B&W6V&6‚và¤ÖV7W&VC¢"Ãc’6†ævVB6VÆÇ2ÂÖ‚³ã3RÒÂ¦W&ò÷WG6–FRF†RÖ÷VæBw2sRÒ&F—W2(	BF†Rf÷&·0¦'—FRÖ–FVçF–6Ââw&F–VçBVF—B52‡Æ–âÖ‚ãCc‚’ÂÖ÷VæB&æB—FVÖ—6VB2&Vf÷&RâF†P¦&æ²æ÷r7FæF–ær—2v†BVæ&Æö6·2BÓ“’w2G&6²g&öÒF†Ræ÷'F‚vFRF÷vâFòF†RvFW"à ¢222³’(	Bæf–vF–öâæB6WGF–æw2T’+r¢¤DôäR##bÓ‚Ó2¢ ¢†’¢¢$vòFò"F"¢¢(	B'V–ÆF–æw2æB7G&VWB–çFW'6V7F–öç2ÂDô5TÔTåDTBVçG&–W2öæÇ’f÷"æ÷p¢†–æfW'&VBÆö6F–öç2¦ö–âÆFW"öæ6R³ÆæG2“²—B&WÆ6W2F†R÷fW&Æ–ærf–Wwö–çG2Æ—7Bæ@§6—G22—G2÷vâF"gFW"6öçG&öÇ2â†"’F†RæVÂ÷VæW"&V6öÖW2¢¦†Ö'W&vW"ÖVçR¢¢†—B—0¦Ö÷&RF†â6WGF–æw2“²&V76W72F†R#ò"–6öââÖö&–ÆR3“9ssƒvFS²6Öö¶RFW7G2WFFVBv—F‚F†P¥T’ÂæWfW"vV¶VæVBà ¢¢¥6†—VB¢£¢öæRÆ—7B(	B‚WF†÷&VBf–Wwö–çG2ÂBfW&–f–VB§Væ7F–öç2æBÆÂ##"ÆöFV@§7G'V7GW&W2(	B–âv÷FöF"6V6öæB–âF†R7G&—Â÷VæVB'’Æ¶&CäsÂö¶&Câ‡v†–6‚fö7W6W2F†P§6V&6‚öâ¶W–&ö&BæBFVÆ–&W&FVÇ’FöW2æ÷Böâ†öæRÂv†W&R—Bv÷VÆB&—6RF†Röâ×67&VVà¦¶W–&ö&B÷fW"F†RÆ—7B’âF†R6WGF–æw26÷–W2&RvöæS¢F†Rf–Wwö–çB6†—2æBF†RGWÆ–6FP§6V&6‚&R&÷F‚&WF—&VBFò—Bâ6'FâÖ†VÇ—2†Ö'W&vW"v—F‚&–ÖÆ&VÃÒ$ÖVçR&à ¢¢¥F†RöæRFW'GW&Rg&öÒF†R&6VÂ2w&—GFVâÂæBv‡’â¢¢—BFöW2äõBÆ—7BFö7VÖVçFVBVçG&–W0¦öæÇ’â³†2ÆæFVB6–æ6RF†—2v2w&—GFVâÂæBF†R†öæW7B&VF–æröb&–æfW'&VBÆö6F–öç2¦ö–à¦ÆFW""—2æ÷rF†R6V6öæBöæS¢¢¦æò7G'V7GW&R÷6—F–öâ–âF†—2FF6WB—2Fö7VÖVçFVF¢¢(	BSB&P¦–æfW'&VFæBc‚6öæ¦V7GW&Æ(	B6òFö7VÖVçFVBÖöæÇ’ÖVçRv÷VÆB†fR†VÆBf÷W"§Væ7F–öç2æ@¦æ÷F†–ærVÇ6RâWfW'’7G'V7GW&R–ç7FVB6'&–W2—G2÷vâÆ6VÖVçBç÷6—F–öåö6öæf–FVæ6V26†—À¦–âF†R÷Ww2F‡&VRv÷&G2æBF‡&VR6öÆ÷W'2ÂæBF†RvFR6ö×&W2WfW'’6†—v–ç7BF†P§&V6÷&B—B§V×2Fòâf–Wwö–çG2æB§Væ7F–öç26''’æöæS¢æV—F†W"—26Æ–Ò&÷WBF†RF÷vâà ¢¢¥v†B—B–æ†W&—G2â¢¢†’F†RFÆÇ’–âF†RF"—26÷VçFVBg&öÒF†RÆ—7BÂ6ò—BÖ÷fW2v†VâF†P¦FF6WBFöW2(	Bæ÷F†–ærFò&W7FFR†W&Rv†Vâ÷6—F–öâ—2&Vw&FVBâ†"’f—fRF'2f—Bv—F‚&÷W@£#‚öb6Æ6²B&÷F‚f–Ww÷'G2†FW6·F÷æVÂv–FVæVB3c(i"3ƒ‚ÂF"FF–ær’(i"b‚À¦Öö&–ÆRG—R"ãR(i"ãR‚“²¢§6—‡F‚F"FöW2æ÷Bf—B¢¢æBF†RvFRv–ÆÂ6’6ò&F†W"F†à§6†—–ærGvò×&÷r7G&—â†2’F†RvFRw2÷vâFW6·F÷†Æb†Bæ÷B&VVâ'Vææ–æs¢6VR*rF†R6Öö¶P¦'VFvWB–â5DEU2à ¢222³(	B'&–FvR&ö6†W0¢$†÷rv÷VÆBvvöâ7&÷72F†Cò"WfW'’'&–FvR7W'&VçFÇ’fÆöG2÷fW"—G2&æ·0¢†&ö6…öæ÷EöÖöFVÆÆVF’â'V–ÆB'WFÖVçBV'F‡v÷&·2÷&×2F†BÖVWBF†RFV6²Bw&FRöâ&÷F€¦VæG2(	BWf–FVæ6S¢F†Rƒƒ26WGFÆW'2r7FFVÖVçB†Æör'WFÖVçG2”âF†R6†ÆÆ÷rvFW"æV"F†P¦&æ·2’ÂFV6²†V–v‡G2Ç&VG’Fö7VÖVçFVBâvÆ¶&ÆRVæBFòVæBÂvvöâ×ÆW6–&ÆRw&F–VçG3°§&Vw&FRw&÷VæEö6öçF7F2V6‚'&–FvR7GVÆÇ’ÆæG3²Ö÷fRF†R&VÆWfçBÆ–&W'G’FW‡Bà ¢222³(	BG&VW27FæF–ær–âF†R&—fW"+r¢¤DôäR##bÓ‚Ó2¢ ¥F†R&—fW"Ö6²†—5vFW&’&Vv–ç2ÖÒ$TÄõrF†RvFW"ÆæRÂ6ò7FVÒ6÷VÆB&ö÷B–âF†@¦&æBÂ72F†RÖ6²æB&VæFW"7FæF–ær–â÷VâvFW"(	B3böbc‚7FF–öç2vW&RFö–ær—Bà¦G&VW2æ§6æ÷r&WV—&W2WfW'’G&VRæBF†–6¶WBFò7FæBE$TUôE%•ôÔ$t”åôÖÒã#Ò6ÆV"ö`§F†RWö6‚w2÷vâvFW%÷7W&f6UöÖƒãRÒöb7Væ²&öÆR²F†Rã2Òw&÷VæBÖÖW6‚FöÆW&æ6RÀ§ÇW2#ÖÒ’â“r6æF–FFW2&V¦V7FVC²Æ÷vW7B7W'f—f–ær7FF–öâ³ã#ÒâæWr6Öö¶R76W'F–öà¢¢¢&æòG&VR7FæG2&VÆ÷rF†RvFW&Æ–æR"¢¢ÂÆöæw6–FR(	Bæ÷B&WÆ6–ær(	BF†R&—fW"ÖÖ6²6†V6²à  ¢222³"(	BÆö÷‡–v–VæR¢‡7FæF–ær–ç7G'V7F–öâFòWfW'’7FWv&B'Vâ’ ¤WfW'’'VâF†BFG2ç—F†–ærW6W"×f—6–&ÆRw&—FW2—G26†ævVÆörVçG'’‡c¢çVÆÂÂG3¢rr’”âD„P¥4ÔR%Tâ(	BF†R÷fW&æ–v‡BW6‚öb##bÓ‚ÓÆæFVBãS'V–ÆF–æw2v—F‚æò6†ævVÆörVçG'’æ@§F†R÷væW"æ÷F–6VB&Vf÷&RvRF–BâV&Æ—6‚†FööÇ2÷V&Æ—6‚ç6†’æBÖW&vRFòÖ–â6òF†RFWÆ÷¦7GVÆÇ’6†—3²Ö–â—2F†RöæÇ’'&æ6‚vW2V&Æ—6†W2à ¢¢£##bÓ‚Ó2(	BF†R6†ævVÆörv26÷''WFVB'’ÔU$tRÂæBF†RvFRæ÷r'Vç2–â6†V6²ç6†â¢ ¦Ö–æ6'&–VB&VæFW&W'2÷vV"ö§2ö6†ævVÆöræ§6F†BF–Bæ÷B'6RÂæB†BFöæR6–æ6RÖW&vP¦cV3†FSâöæRÖ—76–ærÒÒÆ7vÆÆ÷vVBcBVçG&–W2–çFòöæS²GWÆ–6FRc¢cF&öFRÆöærâF†P¥v†Bw2ÖæWrF"v2FVBöâF†RÆ—fR6—FRæBF†—2&ö¦V7B&W÷'FVBæò&VÆV6W2FòÖævW"÷"F†P¦ÆVæ6†W"â¢¤&÷F‚&VçG2öbF†BÖW&vR'6S²F†RÖW&vRFöW2æ÷B¢¢(	Bæv—FGG&–'WFW6ÖW&vW2F†—0¦f–ÆRÖW&vS×Væ–öæÂæBF†RVæ–öâG&—fW"'Vç2GW&–ærF†RÖW&vRÂ6òw&VVâ"6â7F–ÆÂ&öGV6R§&VBÖ–æâ&W—&VBÂæBFööÇ2ö6†V6²ç6†æ÷r'Vç2FööÇ2ö6†V6²Ö6†ævVÆöræÖ§627FW ¢‡&Wf–÷W6Ç’†æB×'Vâ–ç7G'V7F–öâ–âtTåE2æÖBÂv†–6‚—2&V6—6VÇ’v†BÖW&vR×F–ÖR6÷''WF–öà¦WfFW2’âF†R6öçG&7B6†V6²æ÷r&VG2F†RÆ—FW&Âw26†R2DU…B&Vf÷&RW†V7WF–ær—BÂæBæÖW0§F†RVçG'’F†BÆ÷7B—G2FW&Ö–æF÷"æBF†RVçG'’F†Bv÷B7vÆÆ÷vVBâFWF–Â–â5DEU2à ¢¢¥v†B—27F–ÆÂ÷VâÂæB—B—2æ÷BF†—2&6VÂw2Fòf—‚â¢¢æ÷F†–ær'Vç2öâÖW&vR6öÖÖ—@¦—G6VÆbâF†R&W÷6—F÷'’w24’Æ—fW2÷WG6–FR6†–6vòóFFæB÷WG6–FRF†—2ÆæRw266÷RÂ6òÖW&vP§W&f÷&ÖVBöâv—D‡V"6â7F–ÆÂV&Æ—6‚Væ–öâÖ6÷''WFVB6†ævVÆörv—F‚æòvFR&WGvVVâ—Bæ@¥vW2âGvò6æF–FFRf—†W2Â&÷F‚æVVF–ærFV6—6–öâ&F†W"F†â6Æ–6S¢'VâF†R7V'G&VRw2vFP¦g&öÒF†R&Wòw2÷vâv÷&¶fÆ÷röâW6†W2FòÖ–æÂ÷"&WÆ6RÖW&vS×Væ–öæöâF†—2F‚v—F‚¦ÖW&vRG&—fW"F†BVæFW'7FæG2F†RÆ—FW&Ââ¢¥F†R7FæF–ær–ç7G'V7F–öâVçF–ÂF†Vã¢ç’vVçBF†@§W&f÷&×2ÖW&vRffV7F–ær6†ævVÆöræ§6&R×'Vç2FööÇ2ö6†V6²Ö6†ævVÆöræÖ§6eDU"F†RÖW&vRÀ¦æ÷BöæÇ’&Vf÷&R—Bâ¢   ¢222³2(	BF†RÆ6ÆÆR7G&VWB&RÖVçG&çBÂæBF†R÷F†W"Ö–â'&æ6‚6Æ÷Vv‡0¥w&–v‡BG&w2æ'&÷rvFW&6÷W'6RG&÷–ær6÷WF‚öfbF†RÖ–â7FVÒ&WGvVVâÆB&Æö6·2’æ@£‚ÂBÆö6ÂR³Cc"(
b³Cc’(	BÆ6ÆÆR7G&VWBâF†RvFW&Æ–æRG&6R6'&–W2—G2Ö÷WF‚‡F†B—0¦2f"2w&–v‡Bv6†W2—B’æBæ÷F†–ær&W–öæBâF†RF÷76–W"&V6÷&G2F†BF†Rƒ3F†ö×6öà§ÆB6†÷w2¢§F‡&VR6Æ÷Vv‡2öfbF†RÖ–â'&æ6‚¢¢ÂæB$ôDÔ*r3&RÖ¶W26öæÆW’õ7FVÇ¦W"ƒ30§F†R&–Ö'’wV–FRf÷"v†W&RF†R7G&V×26öÖR–âæBv†W&RF†W’FW&Ö–æFRâ&6VÃ¢–FVçF–g§F†RF‡&VRÂæB6''’F†RöæW2F†B&RGFW7FVB2‡–G&öÆöw’ævVö§6öæ4TåE$TÄ”äU2–âF†P¦f÷&ÒF†Ræ÷'F‚×6–FR6Æ÷Vv‚Ç&VG’F¶W2(	BæWfW"2G&6VB&÷VæF&–W2Â&V6W6RF†R&æ²v6€¦—2æ÷BF†W&RFòG&6Râ7&÷72Ö6†V6²F†R7FFR7G&VWB6Æ÷Vv‚Ö÷WF‚F†RG&6RÇ&VG’6'&–W2@¤R³ƒS(
b³ƒSbv–ç7BF÷76–W"¦öæRBà ¢222³B(	BF†RFW'&–âFV6–ÖF÷.(	—2FöÆW&æ6R6Æ–fb+r¢¤DôäR##bÓ‚Ó2¢ ¦vVæW&F÷'2÷FW'&–åövVâç’ÒÖFV6–ÖFRÖFVv&V†fW226Æ–fbÂæ÷BF–ÂÂv–ç7@¦ÔU4…ôd•EõDôÄU$ä4UôÖ¢gFW"F†R³b6÷'&V7F–öâÂãCæBã3‚&÷F‚ÆæBB3ÖÒæB&P§&VgW6VBÂv†–ÆRã3ÆæG2B2ãÖÒ(	BæB6÷7G2#CrS#rG&–ævÆW2òbãBÔ"v–ç7BF†P§&Wf–÷W23R#C’ò2ãRÔ"âF†RtÄ"æ÷r6öÖÖ—GFVB—2F†Rã3öæRâv÷'F‚Æöö²Bv†WF†W §F†RÆæ"FV6–ÖFR—2F†R&–v‡B÷W&F÷"†W&RÂ÷"v†WF†W"F†Rf—B6†÷VÆB&RVæf÷&6VB'’§VG&–2ÖW'&÷"'VFvWB–ç7FVBöbF–†VG&ÂævÆS²F†R–ÆöB—2–ç6–FRF†R#RÔ"'VFvW@¢†FööÇ2÷V&Æ—6‚ç6†&W÷'G2’ãbÔ"’'WBF†Rw&÷VæB—2æ÷rF†RÆ&vW7B6–ævÆR76WB'’§v–FRÖ&v–ââ¢¥F†R&VæFW&VB×G&–ævÆR'VFvWB—2F†RF–v‡FW"6öç7G&–çB¢£¢F†R6Öö¶RÖV7W&W0¢¢£ScBcƒG&—2B#ƒ9sƒv–ç7Bc'VFvWB¢¢(	BbRöb†VG&ööÒÂv†W&R&Vf÷&RF†—0¦6†ævRF†W&Rv2&÷Vv†Ç’#RRâF†RFW'&–â—2g'W7GVÔ7VÆÆVBÒfÇ6VÂ6òÆÂ#CrS#röb—G0§G&–ævÆW2&R–âWfW'’g&ÖRâF†RæW‡B&6VÂF†BFG2vVöÖWG'’v–ÆÂ†—BF†—26V–Æ–æp¦&Vf÷&R—B†—G2F†R–ÆöBöæRà ¢¢¥$U4ôÅdTB##bÓ‚Ó2ÂæBæ÷Bv†W&RF†—2—FVÒv2Æöö¶–ærâ¢¢F†RFV6–ÖF÷"v2æWfW"F†P§&ö&ÆVÒv÷'F‚6öÇf–æs¢F†Rw&÷VæBv2ôäRÖW6‚v—F‚g'W7GVÔ7VÆÆVBÒfÇ6VÂ6ò—G2v†öÆP£#CrS#rG&–ævÆW2vW&RG&vâWfW'’g&ÖRæòÖGFW"v†–6‚v’F†RvÆ¶W"f6VBâ7WB–çFò¢¢£"9r2w&–B'’G&–ævÆR6VçG&ö–B¢¢†&VæFW&W'2÷vV"ö§2÷FW'&–âæ§2F–ÆTw&÷VæB‚–’ÂV6‚F–ÆP¦6'&–W2—G2÷vâ&÷VæF–ær7†W&RæBF†RöæW2&V†–æB–÷R&R6¶—VBâFW6·F÷vVçB¢£SSS2(i £Cc"G&–ævÆW2¢¢BsöbƒG&r6ÆÇ3²†VG&ööÒ—2æ÷r¢£3‚ƒƒ‚¢¢v†W&R—Bv2C’Cƒrà¤w&–B–6¶VB'’ÖV7W&VÖVçB(	BŒ9sBv—fW2F†R6ÖRG&r6ÆÇ2f÷"#rÔõ$RG&–ævÆW2Â,9s`§6fW2æ÷F†W"#b'WBÆVfW2ôäRG&r6ÆÂ7&RÂv†–6‚—2æ÷B†VG&ööÒà¢¢¥GvòF†–æw27F–ÆÂöâF†RF&ÆR¢¢ÂæV—F†W"F¶Vã¢†’,9sb÷"f–æW"Â–bF†RG&rÖ6ÆÂ'VFvWB—0¦WfW"FVÆ–&W&FVÇ’&Wf—6—FVB(	BF†RFW'&–âF–ÆW2&R6†V6ÆÇ26†&–æröæRÖFW&–ÂÂ'WBF†P¦'VFvWB—2vFRæBÖ÷f–ær—B—2FV6—6–öâÂæ÷B6–FRVffV7C²†"’F†RFV6–ÖF÷"VW7F–öâ0¦÷&–v–æÆÇ’w&—GFVâÂv†–6‚—2æ÷r&÷WB”ÄôB&F†W"F†âg&ÖR6÷7BæB—2×V6‚ÆW72W&vVç@§6–æ6RF†RV&Æ—6†VBG&VRfVÆÂFòãs‚Ô"‡6VRF†RÖW6†÷Bf—‚öbF†R6ÖRF’’à¢¢¥F†R–ÆöBf–wW&RV÷FVB&÷fR—27FÆR¢¢(	B’ãbÔ"v2ÖV7W&VBv†VâF†Ræöç–Ö÷W2&öög0§vW&RÆ6V†öÆFW"Ö76–æræBWfW'’vV"FW&—fF—fRv2âVæ6ö×&W76VB6÷’öb—G2Ö7FW"à¢222³‚(	BF†R–çfVçFVB&W6–FVçG2†fRæÖW2+r¢¤DôäR##bÓ‚ÓB¢  ¤WfW'’&V6öç7G'V7FVB&W6–FVçBW6VBFò&VB$&¶W"†–æfW'&VB&W6–FVçBÂVææÖVB’"ÂæBF†R&V6÷&@¦&wVVBf÷"—C¢â–çfVçFVB7W&æÖRv÷VÆBÖ¶RF†RVçG'’–æF—7F–æwV—6†&ÆRBvÆæ6Rg&öÒF†P¦Fö7VÖVçFVBÆ–W"&W6–FR—BâF†B—26÷VæB&÷WBF†RDDæBw&öær&÷WBF†RDõtâ(	BÆ6P§v†W&RÖ÷7B†÷W6V†öÆG2&R6ÆÆVB&â–æfW'&VB6ö÷W"w2†÷W6V†öÆB"&VG227&VG6†VWBÂæ÷B§F÷vââF†R÷væW"6¶VBf÷"æÖW2à ¢¢¥v†B&÷VæG2F†R–çfVçF–öââ¢¢F†RööÇ2–âFF÷&V6öç7G'V7F–öâóƒ3Uö–çfVçFVEöæÖU÷ööÇ2æ§6öæ ¦&R6VVFVBg&öÒF†R¢£sbEDU5DTB&W6–FVçG2F†—2&ö¦V7BÇ&VG’†öÆG2¢¢(	B&VÂV÷ÆRÂæÖV@¦g&öÒ6—FVB6÷W&6W2(	B6òâ–çfVçFVB6ö÷W"—2æÖVBF†Rv’F†—2F÷vâw2&VÂ6ö÷W'2vW&RæÖV@§&F†W"F†âF†Rv’æ÷fVÂv÷VÆBæÖRöæRâF‡&VR6öÖ×Væ—F–W2ÂV6‚v—F‚F†RWf–FVæ6RF†BWG0¦—B†W&S¢æWrVævÆæBæBæWr–÷&²‡F†RFö7VÖVçFVB÷&–v–ç2'VâfW&ÖöçBÂ6öææV7F–7WBÂæWr–÷&²’À¤g&Væ6‚6öÆöæ–ÂæBÖWF—2öbF†RFWG&ö—BæBÖ–ÇvV¶VR6÷VçG'’„&VV&–VâV'2F‡&VRF–ÖW0¦ÖöærF†RæÖVB&W6–FVçG2’ÂæB—&—6‚†öæRGFW7FVB÷&–v–â–â6÷VçG’¶W''“²VvâæB66W’’à ¢¢¥v†W&RvV–v‡F–ær—2—G6VÆbwVW72Â—B6—26òâ¢¢&öFÖVâG&rg&Væ6‚6öÆöæ–ÂôâUd”DTä4R(	@§F†R6''––ærG&FRöbF†—2&—fW"v2v÷&¶VB'’F†B6öÖ×Væ—G’âÆ&÷W&W'2G&rUdTäÅ’ÂæBF†P¦æ÷FRW‡Æ–ç2v‡“¢F†R—&—6‚Æ&÷W&–ær6†–6vòöb÷VÆ"ÖVÖ÷'’'&—fW2v—F‚F†R6æÀ¦6öçG&7G2öb¢£ƒ3b¢¢ÂgFW"F†—266VæRÂ6òvV–v‡F–ærƒ3RÆ&÷W&W'2—&—6‚v÷VÆB&R–×÷'F–ær¦ÆFW"FV6FR–çFòF†—2öæRà ¢¢¥v†B7F÷2—B&V6öÖ–ærÆVæFW&–ær&÷WFRâ¢¢æÖRÆöö·2Æ–¶Rf7B–âv’'vÆÂ†V–v‡@£2ã#RÒ"FöW2æ÷BÂv†–6‚Ö¶W2—BF†RV6–W7Bv’f÷"â–çfVçF–öâFò&RÖ—7F¶Vâf÷"f–æF–ærà¥6ó¢WfW'’&V6öç7G'V7FVBW'6öâ6'&–W2æÖUö&6—6&Æö6²Âw&FVB&V6öç7G'V7FVFÂv†÷6Ræ÷FP¦÷Vç2%D„RäÔR•2”ådTåDTB#²fÆ–FFRç–¢¦W'&÷'2¢¢–b&V6öç7G'V7FVBW'6öâÆ6·2öæRÂ–`¦—G2w&FR—2ç—F†–ær&WGFW"Â÷"–bâGFW7FVBW'6öâ6'&–W2öæRBÆÂ‡F†V—"æÖR6öÖW2g&öÐ¦6÷W&6RæBÖ&¶–ær—B–çfVçFVBv÷VÆBVæFW'7FFRv†B—2¶æ÷vâ&÷WB&VÂW'6öâ’âF‡&VP§6VÆb×FW7G2†öÆBÆÂF‡&VRF—&V7F–öç2â76–væÖVçB—2FWFW&Ö–æ—7F–2g&öÒF†RW'6öâw2–Bæ@¦6†V6²ç6†&RÖFW&—fW2—BÂ6òæÖRF†BÖ÷fVBv—F†÷WBF†RööÇ2Ö÷f–ær—2f–æF–ærà ¤æÖW2&R¢¦FVÇB¢¢&÷VæBV6‚ööÂ&F†W"F†âG&vâ–æFWVæFVçFÇ“¢–æFWVæFVçBG&w2WBf÷W §Vç&VÆFVB†÷W6V†öÆG2VæFW"$Ç–Öâ"æBf÷W"VæFW"$v–Æ&W'B"ÂæB6†&VB7W&æÖR&VG20¦¶–ç6†—F†—2Æ–W"6Æ–×2æ÷F†–ær&÷WBâcF—7F–æ7B7W&æÖW27&÷72“"V÷ÆRà ¢222³r(	B†–F–ærÆWfVÂÂföÆFVB–çFòF†R6öæf–FVæ6R6öçG&öÂ+r¢¤DôäR##bÓ‚ÓB¢  ¥F†R6öæf–FVæ6R6†—6öÆ÷W&VBF†RF÷vâ'’Wf–FVæ6Râ—Bæ÷rÇ6ò†26&WBÂæB&V†–æB—BF‡&VP¦6†V6¶&÷†W3¢¢¤GFW7FVB+r–æfW'&VBc’+r&V6öç7G'V7FVBc"¢¢Â6÷VçFVBg&öÒF†RÆöFVB&Vv—7G'§&F†W"F†âw&—GFVâF÷vââGW&æ–æröæRöfb&VÖ÷fW2—Bg&öÒF†Rf–Wr÷WG&–v‡Bà ¢¢¤†–F–ær—2FVÆ–&W&FVÇ’–æFWVæFVçBöbF†R6öÆ÷W&–ærâ¢¢F†W’&RGvòVW7F–öç2æBF†R6V6öæ@¦—2F†RÖ÷&R6V&6†–æröæS¢6öÆ÷W&–ær6·2†÷r7W&RvR&RÂ†–F–ær6·2§v†B—2ÆVgB–b–÷R¶VW ¦öæÇ’v†B6öÖV&öG’w&÷FRF÷vâ¢âG––ær—BFòF†R6öÆ÷W"ÖöFRv÷VÆBÖVâ–÷R6÷VÆBöæÇ’6²—@§v†–ÆRF†Rv†öÆRF÷vâv2Ö&W"æBF—F†W&VBÂæBF†Rç7vW"&VG2f"&WGFW"–âF–Æ–v‡BâGW&à¦öfb&V6öç7G'V7FVFæBÖ÷7BöbF†RF÷vâfæ—6†W2âF†B—2F†R†öæW7B–7GW&Röb†÷r×V6‚ö`£ƒ3R6†–6vò—2&V6÷fW&&ÆRÂ—B—2æ÷B6öÖf÷'F&ÆRF†–ærf÷"F†—2&ö¦V7BFò6†÷rÂæB—B—0¦æ÷röæR6Æ–6²v’à ¤–×ÆVÖVçFVB2öæRT†–FTÆWfVÆVæ–f÷&Ò&æFVBg&öÒF†R6ÖRF‡&W6†öÆG22ÆWfVÄöb‚–Â6òF†P§6†FW"æBF†RÆ&VÇ26ææ÷BF—6w&VR&÷WBv†–6‚ÆWfVÂg&vÖVçB—2–ââF†R6†ö–6RW'6—7G2À¦—2Æ–VB&Vf÷&RF†Rf—'7Bg&ÖR†&WGW&æ–ærf—6—F÷"6†÷VÆBæ÷BvF6‚F†R†–FFVâF÷vâfÆ6€¦–â’ÂæBF†R6&WB6'&–W2F÷Bv†–ÆRç—F†–ær—2†–FFVâ(	B6öçG&öÂF†BV–WFÇ’&VÖ÷fW2Gvð§F†—&G2öbF†R'V–ÆF–æw2†2Fò6’6òv†–ÆR—G2æVÂ—26‡WBà ¢222³’(	BF†RF÷vâ6†—VB2#C"GvòÖÖWG&R&÷†W2ÂæBF†RvFRv2w&VVâ+r¢¤DôäR##bÓ‚Ó2¢  £â¢¤DôäRâ¢¢f—†VB–â'V–ÆF–æw2æ§6²FW'&–âæ§6²æWrvFW2–â6Öö¶U÷&VæFW&W"æÖ§6²F†RG& £â—2w&—GFVâW–âFö72ôtÄ"Ô4ôåE$5BæÖF*r¥VçF—6VBvVöÖWG'“¢fÆöB&Vf÷&R–÷RG&ç6f÷&Ò¢à ¢¢¥v†BF†Rf—6—F÷"6râ¢¢WfW'’'V–ÆF–ærB&÷Vv†Ç’6—‡F‚öb—G26—¦RâB6÷WF‚vFW"æ@¤Æ¶R(	BF†R'W6–W7B6÷&æW"–âF†RF÷vâ(	BGvò¶æVRÖ†–v‚&÷†W2æB6öÖRfW'’Æ&vRG&VW2âÆ—fRf÷ §6WfW&ÂF—2ÂF‡&÷Vv‚GvòGFV×FVBf—†W2à ¢¢¥F†RFVfV7BÂW†7FÇ’â¢¢VæFW"´…%öÖW6…÷VçF—¦F–öæõ4•D”ôâ—2¦æ÷&ÖÆ—¦VB¢–çCd'&– ®(	B7F÷&VB–çFVvW"÷fW"3#scrÂ6òF†RGG&–'WFR6âöæÇ’&W&W6VçB²ÓÂÖ(	BæBF†RÖWG&W26öÖP¦g&öÒFWVçF—6F–öâ66ÆRöâF†RæöFRƒbã#RöâF†R6Vvæ6‚’à¦'VffW$GG&–'WFRæÇ”ÖG&—ƒF&VG2FVæ÷&ÖÆ—6VBfÆöG2ÂG&ç6f÷&×2F†VÒÂæBw&—FW2F†R&W7VÇ@¢¢¦&6²–çFòF†B6ÖRæ÷&ÖÆ—¦VB–çCd'&–¢¢âÇ––ærF†RFWVçF—6F–öâF†W&Vf÷&R6Æ×V@¦WfW'’6ö÷&F–æFR÷fW"ÖWG&RFòW†7FÇ’öæRÖWG&Râ&÷F‚66ÆR&Vw&W76–öç2vW&RF†—2öæP§w&—FRÖ&6³¢F—66&F–ærF†RæöFRG&ç6f÷&ÒvfRGvòÖÖWG&R'V–ÆF–æw2ÂÇ––ær—BvfRGvòÖÖWG&P¦'V–ÆF–æw2¦–â–V6W2¢Â&V6W6RF†R6Æ×—2W"Ö†—2æB'V–ÆF–ær—2æ÷B6VçG&VBöâ—G0¦÷&–v–ââF†Rf—‚—2FòfÆöBf—'7BæBG&ç6f÷&Ò6V6öæBÂ–â&÷F‚ÖöGVÆW2à ¢¢¥v‡’F‡&VR&÷VæG2öbF–væ÷6—2Ö—76VB—Bâ¢¢WfW'’&VF–ærv2F¶Vâg&öÒG&VRF†BFöW2æ÷@¦†fRF†R'Vrâ6–FV6"w2vÇFbóÆæÖSâævÆ&&W6öÇfW2v–ç7B76WG2ö–âF†R6÷W&6RG&VR(	BF†P§Væ6ö×&W76VBÖ7FW'2(	BæBv–ç7BFFööâF†R6—FRÂv†–6‚V&Æ—6‚ç6†f–ÆÇ2g&öÐ¦76WG2÷vV"öâF†R6Öö¶R†BæWfW"öæ6RÆöFVB6ö×&W76VB76WBâÆö6Â6GW&W2&VæFW&V@¦6÷'&V7FÇ’ÂÖV7W&VB'V–ÆF–æw26ÖR÷WBB6Vç6–&ÆR6—¦W2ÂæBÆÂöb—Bv2G'VRæB—'&VÆWfçBà ¢¢¥F‡&VRvFW2æ÷rW†—7BF†Bv÷VÆB†fR6Vv‡B—BöâF’öæS¢¢  £â6Öö¶U÷&VæFW&W"æÖ§2Ò×V&Æ—6†VF6W'fW2F†RÖ—'&÷"æBVçFW'2B÷vÆ²ö(	BF†Rf—6—F÷"w0¢W†7B'—FW2æBÆ–÷WBâ&¶Rç6†'Vç2—BgFW"V&Æ—6‚âF†—2Ç6ò6÷fW'2F†R÷F†W"f–ÇW&P¢F†—2&ö¦V7B¶VW2†—GF–æs¢f–ÆRF†BW†—7G2–âF†R6÷W&6RG&VRÂ—2æWfW"6÷–VBÂæBCG0¢öæÇ’v†VâÆ—fRà£"âW"×7G'V7GW&R6—¦R76W'F–öç2âF†RöÆB6†V6²Föö²F†R¢§FÆÆW7B¢¢'V–ÆF–ær–âF†R66VæRæ@¢6¶VBv†WF†W"—Bv2&WGvVVâ2æB3Ò(	Bv†–6‚76W2v—F‚öæR6÷'&V7B'V–ÆF–æræB#C¢'&ö¶VâöæW2ÂæBF†B—2F†R66VæRF†B6†—VBâWfW'’7G'V7GW&R—2æ÷rÖV7W&VBv–ç7B—G0¢÷vâ&V6÷&BÂ–æ6ÇVF–ær—G2Fö7VÖVçFVBvÆÅö†V–v‡EöÖâ&V–çG&öGV6–ærF†RfVÇBf–Ç2F†RæWp¢6†V6·2'’æÖRöâÆÂ#C"æBV÷FW2F†R†V–v‡G2F†W’6†÷VÆB†fR†Bà£2âFööÇ2öÖV7W&UövÆ'2ç–ÖV7W&W276WG2v–ç7B&V6÷&G2v—F‚æò'&÷w6W"BÆÂÂæ@¢FööÇ2÷6†ö÷BæÖ§6F¶W2–7GW&W2&F†W"F†â76W'F–öç2(	B&V6W6RF†R76W'F–öç2vW&Rw&VVà¢æBF†RF÷vâv2æ÷Bà ¢¢¥F†RÆW76öâv÷'F‚¶VW–æs¢¢¢vFRF†B6ææ÷B&V6‚F†R'—FW2F†B6†——2æ÷BvFRÂæBà¦vw&VvFR76W'F–öâ†Ö†Âç–ÂF†RFÆÆW7F’†–FW2W†7FÇ’F†Rf–ÇW&RÖöFRv†W&RÆÖ÷7@¦WfW'—F†–ær—2'&ö¶VââæV—F†W"öbF†÷6R—27V6–f–2FòVçF—6F–öâà ¢222³R(	BF†RGvò&W6W'fVBæöç–Ö÷W2&6VÇ2+r¢¥tU5B%BDôäR##bÓ‚Ó2+r4õUD‚5D”ÄÂ4Ä”ÔTB¢  £â¢¥tU5C¢DôäRâ¢¢FööÇ2övVæW&FU÷vW7Eö–æf–ÆÂç–VÖ—G2¢£#öbF†RSR¢¢æB—2&RÖFW&—fVB'£âFööÇ2ö6†V6²ç6†âF†R÷F†W"¢£3R&R†VÆB'’F†R&V6—Rw2÷vâFW'&–âvFR¢¢(	BF†V—"6VçG&W2Æ–P£âvW7BöbÆö6ÂRÓ3ÒæBF†R6öÖÖ—GFVBw&÷VæB7F÷2BRÓ3#ÒâF†W’&Ræ÷BÆ÷7C¢–G2æ@£âfÖ–Ç’ÆÆö6F–öâ&R¶WBÂæBW‡FVæF–ærF†RFW'&–â&÷‚vW7B&VÆV6W2F†VÒv—F†÷W@£â&RÖWF†÷&–ærâFÖ—76–öã¢Fö72ôÄ”$U%D”U2æÖF¢¤Ã“¢¢â¢¤V–v‡BöbF†RGvVçG’7FööB–ç6–FR£âÆGFVB7G&VWB¢¢'’"ã.(	3ãrÒæBvW&R6WB&6²†Æ&vW7BÖ÷fR"ãRÒÂ–ç6–FRF†R&V6—Rw2÷và£â+#Ò“²F†R&V6—R&VFFW2³rw2ÆBw&–BÂ6òæ÷F†–ær6÷VÆB†fR6Vv‡B—B&Vf÷&Râg&÷¦Và£â6öç7FçG2–âF†RvVæW&F÷"Âæ÷B6V&6‚BvVæW&F–öâF–ÖRà£à£â¢¥4õUDƒ¢7F–ÆÂ6Æ–ÖVBÂæB—B—2F†R†&FW"†Æb¢¢(	BF†R&V6—R†26ÇW7FW'6æB£âÆ6VÖVçE÷66†VÖ'WBäòÆ6VÖVçG6Â6ò—G2ƒB6Æ÷G2×W7B&RUD„õ$TBv–ç7BF†R6ÇW7FW £â÷fW&ÆÖ6öçG&öÇ2‡&W6W'fRVçfVÆ÷W2&÷VæBWfW'’æÖVB6÷WF‚vFW"æBÆ¶R7G&VWB&V6÷&BÂ¶VW £â÷WBöbF†RV&Æ–27V&RÂ&W7V7BF†RW7G&’×VâVçfVÆ÷R’æBF†VâvVæW&FVBF†R6ÖRv’à£à£â¢¤4Ä”Ò(	B7FWv&BÂ6¶—F†R6÷WF‚†Æbâ¢¢F¶Vâ'’F†R–çFW&7F—fR6W76–öâöâ##bÓ‚Ó2gFW £â³Bg&VVBF†RG&–ævÆR†VG&ööÒ—BæVVG2â—B—2Æ&vRÂ6–ævÆRÂ–æF—f—6–&ÆRVæ—B‡Gvð£âvVæW&F÷'2Âã3’&V6÷&G2ÂöæRÆ–&W'F–W2&Æö6²’æBGvò'Vç2'V–ÆF–ær—B6öæ7W'&VçFÇ’v÷VÆ@£â6öÆÆ–FRöâFF÷7G'V7GW&W2öæBöâF†RccR×&ööbÆVFvW"Âv†–6‚—2W†7FÇ’F†R¶–æBö`£â6öæfÆ–7BF†B—2W‡Vç6—fR&F†W"F†âÖW&VÇ’ææ÷––ærâF¶R¢¤³"Â³BÂ³RÂ³‚÷"³¢ £â–ç7FVBâF†—26Æ–Ò—2fö–B–bæò6öÖÖ—BF÷V6†–ær—BÆæG2'’¢£##bÓ‚ÓR¢¢(	B6Æ–ÒF†@£â÷WFÆ—fW2F†Rv÷&²—2Æö6²ÂæBæö&öG’6†÷VÆB&R&Æö6¶VB'’â&æFöæVBöæRà ¥Gvò&V6—W2†fR&VVâ6—GF–ærgVÆÇ’7V6–f–VBæBVæ–ç7FçF–FVBÂæBFövWF†W"F†W’&RF†P¦Æ&vW7B&VÖ–æ–ær&Æö6²öb'V–ÆF–æw2–âF†R&ö¦V7C  ¢Ò¢¦FF÷&V6öç7G'V7F–öâóƒ3U÷†6S%÷vW7E÷vöÆe÷ö–çEö&ö6†W2æ§6öæ¢¢†7FGW3 ¢&W6V&6…÷&V6—Uöæ÷Eö–ç7FçF–FVF’(	B¢£SR&öög2¢¢ÂCB&–æ6—Â²æ6–ÆÆ'’ÂCãrRöbF†P¢3R×&ööbvW7BF—f—6–öâF&vWBâw&÷WÖ—‚æBW"ÖfÖ–Ç’6÷VçG2„C(	4CrÂƒ(	4ƒ"Â3(	43"Âs(	5sRÀ¢cÂ(	4R’&RÇ&VG’w&—GFVââÖVÖó¢Fö72õ$U4T$4‚÷vW7EöF—f—6–öåö–æf–ÆÅóƒ3RæÖFà¢Ò¢¦FF÷&V6öç7G'V7F–öâóƒ3U÷†6S%÷6÷WF…ö6÷&UöæEöÖ—†VE÷&V6—Ræ§6öæ¢¢†7FGW3 ¢&÷÷6VEöæ÷EövVæW&FVF’(	B¢£ƒB&öög2¢¢Âcb&–æ6—Â²‚æ6–ÆÆ'’Âv–ç7B3s×&ööb6÷WF€¢F—f—6–öâF&vWBâ6'&–W2Æ6VÖVçE÷66†VÖæB6ö÷&F–æFU÷7—7FVÖ&Æö6²v—F‚F†RUDÐ¢6öçfW'6–öâ7VÆÆVB÷WBâÖVÖó¢Fö72õ$U4T$4‚÷†6S%÷6÷WF…ö6÷&UöæEöÖ—†VBæÖFà ¢¢¥F†RGFW&âFòföÆÆ÷rÇ&VG’W†—7G2Gv–6R¢£¢FööÇ2övVæW&FUö–æfW'&VEö–æf–ÆÂç–…6÷WF€§†6RÂC‚’æBFööÇ2övVæW&FUöæ÷'F…ö–æf–ÆÂç–„æ÷'F‚Âc’Â&÷F‚&RÖFW&—fVB'—FRÖf÷"Ö'—FR'¦ÒÖ6†V6¶7FW–âFööÇ2ö6†V6²ç6†âF†—&BæBf÷W'F‚vVæW&F÷"–âF†B6†R—2F†R¦ö"(	@¤äõB†æB×w&—GFVâ&V6÷&G2Â&V6W6R3’†æB×Æ6VB'V–ÆF–æw26ææ÷B&R&RÖFW&—fVBæBF†P§Æ6VÖVçBvFRv÷VÆB†fRæ÷F†–ærFò6†V6²v–ç7Bà ¢¢¥F†RG&2ÂÆÂöbF†VÒÇ&VG’–Bf÷"öæ6Râ¢¢†’F†R6÷VçF–ær'VÆR—2–âF†R6÷WF‚&V6—Rw0¦÷vâv÷&G3¢¦&WGFW"ÖWf–FVæ6VB&ööb5T%5D•EUDU2f÷"6Æ÷C²—BæWfW"–æ7&V6W2F†RccRF&vWB¢(	@§6òF†W6R3’Fòæ÷B7F6²öâF÷öb³w23‚â†"’FööÇ2övVæW&FUö–æfW'&VEö†÷W6V†öÆG2ç–Æ6V@¤³†6RGvòv†–ÆR7F—fVÇ’fö–F–ærF†W6R6Æ÷G2Â6òF†W’&R7F–ÆÂ6ÆV"(	B¶VW—BF†Bv’Âæ@§&R×'Vâ—G2ÒÖ6†V6¶gFW"â†2’WfW'’6öæ¦V7GW&ÂW†—7FVæ6RÂ÷6—F–öâæBfö÷G&–çB÷vW2¦Fö72ôÄ”$U%D”U2æÖFVçG'’v—F‚6÷fW'3¦Fö¶Vç2Â–â&÷F‚F—&V7F–öç2â†B’Æ6VÖVçB×W7B72F†P¦W†—7F–ærvFW3¢æòfö÷G&–çBv—F†–â2Òöbç’÷F†W"ÂFW'&–â6÷fW&VBÂG'’Â(šCã3ÒW&–ÖWFW §&VÆ–Vb(	BæB†V–v‡Ff–VÆBæ6÷fW'2‚–W†—7G2&V6W6R7G'V7GW&Röæ6RÆæFVBƒ3"ÒG&–gBæ@§&W÷'FVBW&fV7Bf—Bâ†R’G&–ævÆR'VFvWC¢3’&öög2BF†Rãs#2G&—2F†R³&¶RfW&vVB—0§ãÂv–ç7BSsBCCöb†VG&ööÒBgVÆÂFWF–Ââ—Bf—G2æ÷s²—BF–Bæ÷B&Vf÷&R³Bà ¢222³b(	BF†R6öæf–FVæ6Rfö6'VÆ'’—2w&öærÂæBF†R÷væW"æÖVBF†Rf—‚+r¢¤4Äõ4TB##bÓ‚ÓR(	B5UU%4TDTBÂDòäõBdôÄÄõr¢  £â¢¤4Äõ4TB'’³#6â¢¢F†R&VæÖR†VæVBÂ'WB¢¦æ÷BFòF†Rv÷&G2w&—GFVâ&VÆ÷r¢¢âF†—2&6VÀ£â&÷÷6VBFö7VÖVçFVBòFW&—fVBò–æfW'&VF²v†B7GVÆÇ’6†—VB–âF†RcsbÖW&vRö`£â##bÓ‚Ó2—2¢¦GFW7FVBò–æfW'&VBò&V6öç7G'V7FVF¢¢ÂæBFööÇ2÷fÆ–FFRç–w24ôäd”DTä4V £âGWÆR—2F†RVæf÷&6VÖVçBâWfW'—F†–ærg&öÒ%F†R&VæÖRÂv†–6‚—2&VæÖRæBæ÷BæWrF–W" £âöçv&BFW67&–&W2fö6'VÆ'’F†—2&ö¦V7BFöW2æ÷BW6R(	B¢¦&V6÷&Bw&—GFVâFòF†RF&ÆR&VÆ÷p£âf–Ç2F†R'V–ÆBâ¢¢Fö72õ$õdTää4RæÖF—2F†R7W'&VçBWF†÷&—G’æBæ÷r6'&–W2FFVBæ÷FP£â6––ær6òà£à£âF†R&6VÂ—2¶WB&F†W"F†âFVÆWFVB&V6W6R—G2§&V6öæ–ær¢—2F†R&V6öæ–ær&V†–æBF†P£âv÷&G2F†BF–B6†—ÂæB&V6W6R—B—2F†R÷&–v–âöbF†RfVÇB³#67vWBW¢—BÆVgBF†P£â7FæF–ær–ç7G'V7F–öâFò7F’'fö6'VÆ'’Övæ÷7F–2v†–ÆR³b—2–âfÆ–v‡B"ÂæBVæFW"F†@£â–ç7G'V7F–öâ“2vVæW&FVBæÖW2vVçBöâ6––ær–æfW'&VFf÷"F‡&VRvVV·2gFW"–æfW'&VF £â7F÷VBÖVæ–ær–çfVçFVBâ¢¥F†B–ç7G'V7F–öâ—27VçBâ¢¢&VBF†R7G&–æw2öf`£âFö72õ$õdTää4RæÖFÂæ÷BöfbF†—26V7F–öâà ¥F†R÷væW"w26÷'&V7F–öâÂ##bÓ‚Ó2Â–âF†V—"v÷&G3¢¢$’FöâwBvçBFòW6R–æfW'&VB–âF†÷6R¶–æ@¦öb66W2v†W&RF†W&Rv26öÖR6öÆ–B&W6V&6‚&V†–æB—N(
bF†Rv÷fW&æÖVçB&Æ6·6Ö—F‚6†÷6VV×0¦f—&Ç’vööB–âÆö6F–öâæB–÷RÆ&VÆVB—B–æfW'&VBâ–æfW'&VB—2F†RæÖRf÷"v†Vâ–÷RÖ¶R–÷W §&W6V&6‚6öÖ&–æF–öâæB–çfVçBW'6öâ&6VBöâÆ–¶VÇ’æVVG2öbF†R6—G’æB÷VÆF–öââ"  ¥F†W’&R&–v‡BÂæBF†RfVÇB—2F†BGvòfW'’F–ffW&VçB7G26†&RöæRv÷&BâÆ6–ærF†RvVæ7¦&Æ6·6Ö—F‚6†÷g&öÒæG&V2w2FW67&—F–öâ—2$U4T$4ƒ²–çfVçF–ær6ö÷W"&V6W6RF÷vâ6¶–æp§GvòF†÷W6æB†öw2æVVG2öæR—2”ådTåD”ôââ&÷F‚7W'&VçFÇ’&VB–æfW'&VFà ¢¢¥F†R&VæÖRÂv†–6‚—2&VæÖRæBæ÷BæWrF–W"¢¢(	BF†RF‡&VRW†—7F–ærÆWfVÇ2¶VWF†V— ¦ÖVæ–æw2æBF†V—"–çBÂæBGvòöbF†VÒvWB†öæW7BæÖW3  §Âæ÷rÂ&V6öÖW2Â–çBÂÖVç2À§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§ÂFö7VÖVçFVFÂFö7VÖVçFVFÂv†—FRòVæÖ&¶VBÂ6÷W&6RGFW7G2F†—2BF†R66VæRFFRÀ§Â–æfW'&VFÂ¢¦FW&—fVF¢¢ÂvöÆBÂ&V6öæVBg&öÒ7V6–f–2Wf–FVæ6R$õUBD„•2D„”är(	BFW67&–&VBÆö6F–öâÂÖV7W&VBÆ÷BÂâF¦6VçB&V6÷&Bâ&W6V&6†VBæBÆ–¶VÇ’âÀ§Â6öæ¦V7GW&ÆÂ¢¦–æfW'&VF¢¢ÂF—F†W&VBÂ–çfVçFVBFòf–ÆÂFVÖöç7G&&ÆRæVVBöbF†RF÷vââæòWf–FVæ6Rf÷"F†—2'F–7VÆ"F†–ærâ¢¤æ÷B&wVW72"¢¢(	BF†R÷væW"6¶VBf÷"F†Bv÷&BFòvòâÀ ¥F†—2Ç6òTä”d”U2F†RGvò†W3¢FF÷&W6–FVçG2öÇ&VG’w&FW2V÷ÆP¦Fö7VÖVçFVFòFW&—fVFò–æfW'&VFv—F‚ÆÖ÷7BW†7FÇ’F†W6RÖVæ–æw2†Fö72õ$õdTää4RæÖBæ@¦FF÷&W6–FVçG2ö–æFW‚æ§6öæ’âgFW"F†R&VæÖRöæRfö6'VÆ'’6÷fW'2&÷F‚à ¢¢¤÷&FW"ÖGFW'2Â&V6W6RF†Rv÷&G26öÆÆ–FRÖ–BÖfÆ–v‡Bâ¢¢6öæ¦V7GW&Æ(i&–æfW'&VF6ææ÷B'Và¦&Vf÷&R–æfW'&VF(i&FW&—fVFÂ÷"WfW'’öÆB–æfW'&VF—27vÆÆ÷vVBâFò—B2ôäR67&—FVB70§v—F‚Gvò×†6R7V'7F—GWF–öâF‡&÷Vv‚6VçF–æVÂÂ&RÖFW&—fRWfW'’vVæW&FVB&V6÷&BÂæBF–fbF†P¦6÷VçBöbV6‚ÆWfVÂ&Vf÷&RæBgFW#¢F†RF÷FÇ2×W7BÖ÷fR2W&×WFF–öâÂæ÷B6†ævRà ¢¢¥v†B×W7BÖ÷fRv—F‚—C¢¢¢66†VÖ2ò¢æ§6öæVçV×2+rFööÇ2÷fÆ–FFRç–†–æ6ÇVF–æp¦6†V6µöÆ–&W'F–W5ö6÷fW&vVÂv†–6‚¶W—2öâ6öæ¦V7GW&Æ(	BgFW"F†R&VæÖRF†RÆ–&W'F–W2G&–vvW ¦—2–æfW'&VF’+rF†RF‡&VR–æf–ÆÂvVæW&F÷'2æBF†R†÷W6V†öÆBvVæW&F÷"Âv†÷6RÆ—FW&Â7G&–æw0¦&R&RÖFW&—fVB'—FRf÷"'—FR+r&VæFW&W'2÷vV"ö§2ö6öæf–FVæ6Ræ§6+rF†RWf–FVæ6RÆVvVæB–à¦–æFW‚æ‡FÖÆ+r÷Wæ§6+rFö72õ$õdTää4RæÖFÂtTåE2æÖFÂFö72ôÄ”$U%D”U2æÖF&÷6Rà¢¢¤Fòæ÷B&Ww&—FRF†R†—7F÷&–6Â&÷6R–âFö72õ5DEU2æÖF÷"6†—VB6†ævVÆörVçG&–W2¢¢(	BF†W¦&R&V6÷&Böbv†Bv26–BBF†RF–ÖRà ¢222³r‡7V2’(	B6öæf–FVæ6Rf–Ws¢F—F†W"F†R&öög2ÂæBÆWBÆWfVÂ&R7v—F6†VBöfb+r¢¤D•44„$tTB##bÓ‚ÓB¢  £â'V–ÇBâF†R&ööb†ÆbÆæFVBv—F‚³#"Âv†–6‚ÖFRF†Rv†öÆRöb&V6öç7G'V7FVB'V–ÆF–æp£âF—F†W"FövWF†W"(	BvÆÇ2Â&ööbÂG&–ÒæB6†–ÖæW’(	B&F†W"F†âÆVf–ærv†÷7Bv—F‚6öÆ–@£â6†–ÖæW’öâ—BâF†R7v—F6‚ÖÖÆWfVÂÖöfb†Æb—2F†R³rVçG'’&÷fRâF†R÷&–v–æÂ7V2—2¶W@£â&VÆ÷r&V6W6R—B—2v†Bv26¶VBf÷"æBF†RVçG'’&÷fR—2v†Bv2'V–ÇBà  ¤FWVæG2öâ³bw2fö6'VÆ'’âF‡&VRF†–æw2F†R÷væW"6¶VBf÷"öâ##bÓ‚Ó3  £â¢¥F†R&öög2Fòæ÷BF—F†W"â¢¢–âF†R6öæf–FVæ6Rf–WrF†RvÆÇ2F¶RF†RF—F†W&VBG&VFÖVçBæ@¢F†R&ööbÆæW2Fòæ÷BÂ6ò'V–ÆF–ærF†B—2VçF—&VÇ’–çfVçFVB7F–ÆÂ&VG22†Æb×6öÆ–Bà¢f–æB÷WBv†WF†W"F†R&ööbÖFW&–ÂÖ—76W2F†Rö6öæf–FVæ6VGG&–'WFR÷"F†RF6‚ÂæBV—F†W ¢F—F†W"—B÷"(	BF†R÷væW"w2÷vâ7VvvW7F–öâ(	Bv—fRF†R&ööbF—7F–æ7BG&VFÖVçB6òF—F†W&V@¢vÆÂæBF—F†W&VB&ööb7F’ÆVv–&ÆRv–ç7BV6‚÷F†W"à£"â¢¤†–FRÖöFRâ¢¢¢$’v÷VÆBÆ–¶RFò&R&ÆRFòFövvÆRF†Bf–WrFòÖ¶RF†R'V–ÆF–æw2ö&¦V7G0¢—FV×2F—6V"ÇFövWF†W"&6VBöâF†÷6RÆWfVÇ2â"¢6òF†R6öæf–FVæ6Rf–Wrv–ç2ÖöFS¢4ôÄõU ¢‡FöF’w2&V†f–÷W"’÷"„”DRÂv†W&RÆWfVÂw2vVöÖWG'’—2&VÖ÷fVBg&öÒF†R66VæR&F†W"F†à¢F–çFVB(	BvÆ²F÷vâöböæÇ’v†B—2Fö7VÖVçFVBÂF†VâöæÇ’v†B—2Fö7VÖVçFVBæBFW&—fVBà¢F†R÷væW"7VvvW7G26öç6öÆ–FF–ær—B–çFòF†R6öæf–FVæ6R6öçG&öÂ&F†W"F†âFF–ær6V6öæ@¢öæRÂv†–6‚—2&–v‡C¢—B—2F†R6ÖRVW7F–öâ6¶VBGvòv—2à£2âW"ÖÆWfVÂFövvÆW2Â6òF†RF‡&VRÆWfVÇ26â&R6†÷vâ÷"†–FFVâ–æFWVæFVçFÇ’à ¢¢¥F†R†öæW7BG&¢¢¢†–F–ær'’ÆWfVÂ×W7B†–FRv†öÆRô$¤T5E2'’F†V—"&V6÷&Bw2w&FRÂæ÷@¦–æF—f–GVÂGG&–'WFW2(	B'V–ÆF–ærv†÷6R÷6—F–öâ—2FW&—fVB'WBv†÷6R&ööb—F6‚—2–æfW'&VB—0¦öæR'V–ÆF–ærÂæB—B†2Fò&R6öÖWv†W&RâFV6–FRæBw&—FRF÷vâv†–6‚GG&–'WFRv÷fW&ç2à¦ö&¦V7Bw2f—6–&–Æ—G’†W†—7FVæ6RÂ7W&VÇ’’&Vf÷&R'V–ÆF–ærF†R6öçG&öÂà ¢222³‚‡7V2’(	B–çfVçBW&–öBÖ&÷&–FRæÖW2f÷"–æfW'&VB&W6–FVçG2+r¢¤D•44„$tTB##bÓ‚ÓB¢  £â'V–ÇB(	B6VRF†R³‚VçG'’&÷fRf÷"F†RööÇ2ÂF†RvV–v‡F–æræBF†RfÆ–FF÷"'VÆRF†@£â¶VW2â–çfVçFVBæÖRg&öÒWfW"w&F–ær&÷fRF†R–çfVçF–öââ7V2¶WBf÷"F†R&V6÷&Bà  ¥F†R÷væW"Â##bÓ‚Ó3¢¢&f÷"–æfW'&VBV÷ÆR–÷R6â–çfVçBö7&VFRW&–öB&÷&–FRæÖW2f÷ §F†VÞ(
böb6÷W'6R—Bw2öæRöbF†R–æfW&Væ6W26ò’vÒ7W&R—Bv–ÆÂ&R6ÆV.(
bW6Rv†FWfW"†—7F÷&–6À§&W6V&6‚—2&V6öæ&ÆRf÷"æÖW2Æ–¶RFö7F÷'2Ö–v‡B†fR6öÖRæÖW2æBÆ&÷&W'2v÷VÆB†fP¦÷F†W'2â"  ¥F†—2$UdU%4U2F†R7FæF–ær'VÆR–âFö72ôÄ”$U%D”U2æÖFÃƒBæBFF÷&W6–FVçG2ö–æFW‚æ§6öæÂv†–6€§6’æò–æfW'&VBW'6öâ—2æÖVBâF†B&WfW'6Â—2F†R÷væW"w26ÆÂæB—B—2ÖFR(	B'WBF†P§&V6öâf÷"F†RöÆB'VÆR†2Fò&Rç7vW&VB&F†W"F†âf÷&v÷GFVã¢æÖVB–çfVçFVBW'6öâ×W7@¦æWfW"&RÖ—7F¶&ÆRf÷"Fö7VÖVçFVBöæRâ6òF†RæÖR—2âGG&–'WFRÆ–¶Rç’÷F†W"æB6'&–W0§F†R–æfW'&VFw&FRF†RW'6öâÇ&VG’†3²F†R6&B×W7B6†÷rF†RæÖRæBF†Rw&FRFövWF†W"à ¢¢¤FòF†R&W6V&6‚&F†W"F†â–6¶–ærÆV6çBæÖW2â¢¢ƒ3R6†–6vòw2–æfW'&VB÷VÆF–öâ6†÷VÆ@¦G&röâF†RFö7VÖVçFVBöæRw2÷vâ6ö×÷6—F–öâ(	BF†Rƒ32G&FR&÷7FW"æBF†R&W6–FVçG2Ç&VG’–à¦FF÷&W6–FVçG2ö&RF†R6×ÆS¢æWrVævÆæBæBæWr–÷&²–æ¶VW2ÂæWr–÷&²GWF6‚Â—&—6‚æ@¤vW&Öâ'&—fÇ2öâF†R6æÂv÷&·2Âg&Væ6‚Ô6æF–âæBÜ:—F—2fÖ–Æ–W2BF†Rf÷&·2âG&FP¦6÷'&VÆFW2v—F‚÷&–v–â–âv—2F†R6÷W&6W27W÷'B†6æÂÆ&÷W"†Vf–Ç’—&—6ƒ²ÖW&6†çG2æ@§&öfW76–öæÇ2F—7&÷÷'F–öæFVÇ’–æ¶VR’ÂæBF†B6÷'&VÆF–öâ(	Bæ÷B&æFöÒG&r(	B—2v†@¦Ö¶W2â–çfVçFVBæÖRFVfVç6–&ÆRâ7W&æÖW2æBv—fVâæÖW26†÷VÆB6öÖRg&öÒW&–öBÖGFW7FV@¦Æ—7G2ÂæBF†RÖVÖò×W7B6’v†–6‚æBv‡’ÂW"F†R7FæF–ær'VÆRF†B6÷W&6Uö–B&W6öÇfW2à ¤FBæÖUö&6—6†÷"WV—fÆVçB’FòF†RW'6öâ&V6÷&B6òF†R6&B6â6’t…’F†—2æÖRæBæ÷@¦æ÷F†W"ÂæBW‡FVæBFööÇ2÷fÆ–FFRç–6òâ–æfW'&VBW'6öâw2æÖR6ææ÷B&Rw&FVB&÷fP¦–æfW'&VFà ¢ÒÒÐ ¢223(	BvV÷&VfW&Væ6RæBfW&–g’F†RFGVÒ+r¢¤DôäR##bÓ‚Ó’¢  ¤÷&–v–ã¢RCCss"ãrÂâCc3s3“Rã‚„U4s£#c“b’ÒCãƒƒcs#ÂÓƒrãc3s“S(	BF†Rw&–v‡BÖG&vâf÷&·2À¦V–v‡BÔt5f—B$Õ2rãRÒÂ7&÷72Ö6†V6¶VBv–ç7Bâ–æFWVæFVçB†F†v’vV÷&VfW&Væ6RƒSrã’Ò¦æBF†RÖöFW&âõ4Ò§Væ7F–öâƒ3’ãBÒ’âF†RV&Æ—6†VBÆÆÖ22×ö–çBG&ç6f÷&Òv2ÖV7W&V@¢…$Õ2#Rã’Òv–ç7B–æFWVæFVçB6öçG&öÂ’æB7WW'6VFVC²æòææ÷FF–öâW†—7FVBf÷"F†RÄô0¤†F†v’Â6òF†BvV÷&VfW&Væ6R—2æWrv÷&²âÖVÖó¢Fö72õ$U4T$4‚öFGVÕöFW&—fF–öâæÖF°¦Væf÷&6VÖVçC¢FööÇ2÷&VFW&—fUöFGVÒç––â6†V6²ç6†â6''’Öf÷'v&C¢+#Òv÷&¶–ærVæ6W'F–çG¦f÷"ç—F†–ærG&6VBg&öÒF†Rƒ3B6†VWG3²vVæW&FR7G&VWBvVöÖWG'’æÇ—F–6ÆÇ’g&öÒÆ@¦F–ÖVç6–öç2„†F†v’ææ÷FFW2F†VÒ’æB6æFò6öçG&öÂ&F†W"F†âG&6–ær—†VÇ2à ¢223"(	BFW'&–âÂWö6‚Sƒ3Eö†&&÷%ö7WF  ¢2223&R(	BW‡FVæBF†Rw&÷VæBT5BFòF†RÆ¶R+r¢¤”â$ôu$U52(	B&6VÂ†’DôäR##bÓ‚Ó¢  ¥&öÖ÷FVB&÷fRF†R&W7Böb3"&V6W6RF†Rg&VRÖfÇ’6ÖW&ÖFRF†Rv–×÷76–&ÆRFð¦Ö—72g&öÒF†R—#¢¢§F†RÖöFVÆÆVBw&÷VæB7F÷2ƒÒ6†÷'Böbf÷'BFV&&÷&âæB&÷WB¦¶–ÆöÖWG&R6†÷'BöbÆ¶RÖ–6†–vââ¢  ¥F†RçVÖ&W'2ÂÖV7W&VBv–ç7BFFöFGVÒæ§6öæ&F†W"F†âW7F–ÖFVC  §ÂÂÆö6ÂRÂ–ç6–FRF†R&÷ƒòÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Â7W'&VçBFW'&–â&÷‚Â(‰#3#(
b¢¢³3#¢¢Â(	BÀ§ÂÆ¶R7Bb7FFR7BÂ³ƒC"ÂæòÀ§Â¢¤f÷'BFV&&÷&â6—FR¢¢„Ö–6†–vâfR'&–FvR’Â¢¢³#r¢¢ÂæòÂ2ã\9r&W–öæBF†RVFvRÀ§ÂÖöFW&âÆ¶Vg&öçBBF†R&—fW"Ö÷WF‚Â³#SRÂæòÀ ¢„ÆæFÖ&²÷6—F–öç2&RÖöFW&â×7V66W76÷"66÷–ærf–wW&W2Âæ÷BFF6WB6Æ–×2(	BF†W’6¦†÷rf"F†R&÷‚fÆÇ26†÷'BÂæ÷F†–ær&÷WBƒ3Râ ¢¢¥F†Rƒ3RÆ¶RVFvR—2æ÷v†W&RæV"F†RÖöFW&âöæR¢¢(	BWfW'—F†–ærV7Böb&÷Vv†Ç’Ö–6†–và¤fVçVR—2ÆFW"ÆæFf–ÆÂÂ×V6‚öb—Bf—&RFV'&—2gFW"ƒs(	B6òG&v–ærFöF’w26ö7@§v÷VÆB&RF†R6–ævÆRÆ&vW7BfÇ6R6Æ–Ò–âF†RFF6WBâ—B6öÖW2öfbw&–v‡Bƒ3BâF†—2—0§&V6—6VÇ’F†R66RF†R–V"×&ÖWFW&—¦VB&6†—FV7GW&RW†—7G2f÷#¢Fö72ôUô4…2æÖFG&VG0§FW'&–â2fW'6–öæVBW"Wö6‚Â6òÆFW"–V"vWG2—G2÷vâ6†÷&VÆ–æR&F†W"F†âVF—F–æp§F†—2öæRà ¢¢¥v†–6‚6÷W&6RG&—fW2v†–6‚VÆVÖVçB¢¢‡6WB##bÓ‚Ó'’¶Wf–âÂv†ò—2&–v‡BF†BF†P¦V&Æ–W"&VF–æröbF†W6R6÷W&6W2v2÷fW"Ö6WF–÷W2(	B6VRFö72õ$õdTää4RæÖF*rF–W"R“  §ÂVÆVÖVçBÂ6÷W&6RÂ6öæf–FVæ6R—B7W÷'G2À§ÂÒÒ×ÂÒÒ×ÂÒÒ×À§ÂÆ¶R6†÷&RÂ†&&÷W"7WBÂ–W'2Â6æBFöæwVRÂF†RöÆB6÷WF‡v&B6†ææVÂÂ¢¥w&–v‡Bƒ3B¢¢(	B7W'fW’ÂæBF†RÖ7FW"v'–ær&7FW"Â–æfW'&VFÂ+#Ó²f—"W7F–ÖFR—2W‡V7FVB&F†W"F†âfö–FVBÀ§ÂF†R&—fW"F‡&÷Vv‚F†R6VçG&Â&Æö6·3²7G&VWBæB&Æö6²vVöÖWG'’Â¢¥F†ö×6öâÆBƒ3¢¢(	BƒÖgB7G&VWG2Â‚ÖgBÆÆW—2ÂvVæW&FVBæÇ—F–6ÆÇ’g&öÒF†RÖöGVÆRÂæ÷BG&6VBÂFö7VÖVçFVFf÷"F†RÖöGVÆRÂ–æfW'&VFf÷"F†Rf—BÀ§ÂF†R7G&V×26öÖ–ær–âÂæBv†W&RV6‚öæRFW&Ö–æFW2Â¢¤6öæÆW’õ7FVÇ¦W"ƒ32¢¢2&–Ö'’wV–FRÂw&–v‡B2F†R6†V6²Â–æfW'&VFÂæÖVB–âF†Ræ÷FRÀ§Â¢¦'&–FvR÷6—F–öç2¢¢Â¢¤6öæÆW’õ7FVÇ¦W"ƒ32¢¢(	B—BG&w2F†VÒ–âÆ6RÂ–æfW'&VFÀ§ÂvVæW&Â7&÷72Ö6†V6²öâÆÂöbF†R&÷fRÂâƒ3bÖ(	B¢¦æ÷B–WB–âFF÷6÷W&6W2ö²f–æBæB&V6÷&BöæRf—'7B¢¢Â(	BÀ ¥F†R7FæF–ær'VÆR7F–ÆÂ†öÆG2v†W&R—BV&ç2—G2¶VW¢æ÷F†–ærG&6VBg&öÒ–7F÷&–À§6†VWB&V6öÖW2â¦÷WFÆ–æR¢â&V6öç7G'V7F–öâFVÆÇ2–÷R'&–FvRv2†W&S²—BFöW2æ÷BFVÆÀ§–÷R—G2Æââ÷6—F–öâ–æfW'&VFv—F‚æ÷FRÂvVöÖWG'’g&öÒF†R&6†WG—Rà ¢¢¤Fòæ÷BÆWB+#Ò7F÷F†Rv÷&²â¢¢F†RVæ6W'F–çG’—2&V6÷&FVBW"7G'V7GW&RæB6†÷vâ–à§F†R÷W²F†B—2F†RÖV6†æ—6Òf÷"†æFÆ–ær—BâÆVf–ærF†RV7B†ÆböbF†RF÷vâV×G¦&V6W6RF†R6†÷&R6ææ÷B&Rf—†VBFòF†RÖWG&R—2F†RÖ÷&RÖ—6ÆVF–æröbF†RGvò÷F–öç2à ¢¢¥66÷RÂæ÷rÖV7W&VBöfbF†R6†VWB&F†W"F†âwVW76VBâ¢¢f—'7B&VF–æw2&R6öÖÖ—GFVB–à¦FF÷G&6W2÷fV7F÷'2÷w&–v‡Eóƒ3EöV7Bæ§6öæÂFW&—fVB'’FööÇ2÷w&–v‡E÷‚ç–g&öÒF†R6ÖP¦f—GFVBff–æRF†RFGVÒ—26†V6¶VBv–ç7C  §ÂfVGW&RÂg&öÒw&–v‡Bƒ3BÂÆö6ÂRÂÆö6ÂâÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Âf÷'BFV&&÷&â†Æ&VÂ6VçG&R’Â¢¢³S"¢¢Â³##À§Â&—fW"Ö÷WF‚Â6÷WF‚&æ²Â³ƒÂ³#s"À§ÂÆ¶R6†÷&Ræ÷'F‚öbF†R†&&÷W"Â¢¢³33(
b³3cR¢¢Â³33(
b³s3RÀ§Âæ÷'F‚–W"Â÷WFW"VæBÂ¢¢³SCB¢¢Â³s‚À ¥6òF†R&÷‚×W7B&V6‚&÷WB¢¤R³s¢¢Âæ÷BF†R³S’f—'7BW7F–ÖFVB(	BF†R†&&÷W §v÷&·2'VâgW'F†W"÷WBF†âF†R6†÷&RFöW2âF†Bv—fW2ã"ã¶Ò9rãr¶Òf–VÆC²BF†P¦7W'&VçB"ãRÒ6VÆÂÂã##F²6×ÆW2‡ãCS´"–çCb’v–ç7BFöF’w2cf²ƒ3"´"’âvVÆÂ–ç6–FP§F†R#RÔ"V&Æ—6‚'VFvWBÂ'WBv÷'F‚6ö'6W"6VÆÂV7BöbF†R'V–ÇB&Æö6·2Âv†W&RF†P¦Wf–FVæ6RFöW2æ÷B7W÷'B"ãRÒFWF–Âç—v’à ¥GvòF†–æw2F†Rf—'7B726WGFÆVBÂæBöæR—BF–Bæ÷C  ¢Ò¢¥F†Rf÷'BFV&&÷&â÷6—F–öâ—27&÷72Ö6†V6¶VBâ¢¢w&–v‡BWG2—BBR³S"Ââ³##²F†P¢ÖöFW&â7V66W76÷"ÆæFÖ&²„Ö–6†–vâfVçVR'&–FvR’–æFWVæFVçFÇ’v—fW2R³#rÂâ³“Rà¢3RÒ'BÂg&öÒÖWF†öG26†&–æræò–çWBâF†B—2v†BÆ–6Vç6W2–æfW'&VFà¢Ò¢¥w&–v‡BÆ&VÇ2F†R&W6W'fF–öâÂæ÷BF†Rf÷'Bâ¢¢F†W&R—2æòÆ—6FRÆâöâF†—26†VWBÀ¢6òF†Rfö÷G&–çB†2Fò6öÖRg&öÒVÇ6Wv†W&R(	BæG&V2Â÷"F†Rf÷'Bw2÷vâV&Æ—6†VBÆç2à¢Fòæ÷BG&6Râ÷WFÆ–æRöfbF†R&ææW"à¢Ò¢¥F†R6æB&"æBF†RöÆB6÷WF‡v&B6†ææVÂ&Ræ÷r&VB¢¢‡6V6öæB72Â6ÖRF’’âF‡&VP¢–æ²Æ–æW2ÂæW7FVBvW7BFòV7C¢F†RÖ–æÆæB&æ²öbF†RFV6––æröÆB6†ææVÂÂF†R&"w0¢6†ææVÂ6–FRÂæBF†R&"w2Æ¶RÖf6–ær6–FRâ6†V6¶VBf÷"6ö†W&Væ6R&F†W"F†âW–V&ÆÆV@¢(	BBWfW'’6×ÆVBæ÷'F†–ærF†RF‡&VRæW7B–â÷&FW"æBF†R&"6öÖW2÷WBs(	3sÒv–FRÀ¢æ'&÷v–ærFò—G26÷WF†W&â†öö²Âv†–6‚—2v†BÆ—GF÷&Â7—B6†÷VÆBFòâVæ6W'F–çG’—0¢&V6÷&FVBB3Ò&F†W"F†âF†R6†÷&Rw2#S¢F†W6R&R–æ²Æ–æW2÷fW"v6‚ÂæBF†P¢6÷WF†W&â†öö²—2F†RÆV7B6W'F–â6†R–âF†—2VG&çBà ¢¢¥F†R6ö7FÆ–æRvFR—2F†W&Vf÷&R6ÆV&VBâ¢¢6†÷&RÂ†&&÷W"–W'2Â6æB&"æBöÆB6†ææVÀ¦&RÆÂ–âFF÷G&6W2÷fV7F÷'2÷w&–v‡Eóƒ3EöV7Bæ§6öæ–âÆö6ÂTåRâv†B3&R7F–ÆÂæVVG2—0§F†R¦†V–v‡Ff–VÆB¢v÷&²(	BW‡FVæF–ærF†R¦öæRF&ÆRV7B÷fW"ã"ã¶Ò9rãr¶ÒÂv—F‚F†R& ¦26æBæBF†RöÆB6†ææVÂ2vFW"(	Bæ÷BÖ÷&RG&6–ærà ¥Væ&Æö6·2F†R¢¤f÷'BFV&&÷&â¢¢æB¢¤†&&÷"v÷&·2¢¢&6VÇ2–â3RÂv†–6‚6ææ÷B&RÆ6V@¦öçFòw&÷VæBF†BFöW2æ÷BW†—7Bâ—BÇ6ò&WF—&W2F†RW&–Âf–Wrw2v÷'7B'FVf7C¢g&öÐ£SÒW–÷R7W'&VçFÇ’6VRF†Rw&÷VæB6–×Ç’VæBà ¥&6VÇ2‡&ÆÆVÂöæ6R3ÆæG2“  ¢Ò¢¢†’6†÷&VÆ–æR²&—fW"fV7F÷'2¢¢(	B¢¤DôäR##bÓ‚Óâ¢¢FööÇ2÷G&6U÷6†÷&VÆ–æRç–(i ¢FF÷FW'&–âöWö6‡2öSƒ3Eö†&&÷%ö7WB÷6†÷&VÆ–æRævVö§6öæ¢F†RÖ–â7FVÒg&öÒF†R&÷‚VFvP¢V7BÂF†Rƒ3B7WB&WGvVVâ—G2–W'2ÂF†RöÆB6÷WF‡v&B6†ææVÂÂF†R¢§6æB&"2à¢—6ÆæB¢¢‡F†RvFW"öÇ–vöâw2–çFW&–÷"&–ær’ÂæBF†RÖ–æÆæBÆ¶R6†÷&R(	B"CcbÒöb6÷WF€¢6†÷&RÂSc‚Òöbæ÷'F‚6†÷&RÂãR¶Ò&"W&–ÖWFW"ÂÆÂöfbF†R6ÖRw&–v‡Bƒ3B6†VW@¢F‡&÷Vv‚F†R6ÖRff–æRÂ+#ÒâÖVÖó¢Fö72õ$U4T$4‚÷6†÷&VÆ–æUö†&&÷%óƒ3BæÖFâGvò&÷VæF'¢'Vç2vW&Rf÷VæBæBG&÷VBöâW'÷6S¢F†R÷WFW"VFvRöbF†RÆ¶Rv6‚—2v†W&RF†P¢G&Vv‡G6Öâ7F÷VBv6†–ærÂæ÷B6ö7Bâ¢¤ÖV7W&VBÂv†–6‚6†ævW2F†R&÷ƒ¢¢¢F†RÖ–æÆæ@¢6†÷&R&V6†W2R³#SræBF†R&"w2V7BVFvRR³C“rÂ6òF†R&÷÷6VB³S6Æ—2F†R&"'¢2Ò(	B¢§W6RR³Sc¢¢Â–ç6–FRF†RG&6VBv–æF÷rw2³SsâF†RGvòv–æF÷w2÷fW&Æ'’ƒÒæ@¢w&VRF†W&RFòã(	3RãrÒÂv†–6‚—2F†R6†V6²F†BF†R6VvÖVçFF–öâ—2&VF–ærF†RÖ&F†W ¢F†â—G2÷vâ&ÖWFW'2âæ÷B–WB6öç7VÖVB'’FW'&–åövVâç–²—B—2F†RWf–FVæ6RÂæ÷BF†P¢w&÷VæBà¢Ò¢¢†"’†V–v‡Ff–VÆB¢¢(	BF†R3×¦öæRF&ÆR–âFö72÷&W6V&6‚ó×FW'&–âÖ‡–G&öÆöw’æÖFÂVçF—¦VB(šCã#RgBB^(	3gB6VÆÇ2âöæRF†–ærF†—2&6VÂæòÆöævW"†2Fò'VFvWBf÷"ƒ##bÓ‚ÓÂ5DEU2*r3B“¢¢§&÷6R–âFW'&–å÷7V2æ§6öæ—2÷WBöbF†RFW'&–âw27FÆVæW72†6‚¢¢Â6ò¦öæRw2&V6öæ–ærÂ6fVB÷"6—FF–öâ6â&Rw&—GFVâÂ&wVVBæB&Ww&—GFVâv—F†÷WB&¶R(	BæB—B×W7B&RÂ&V6W6Râ–æfW'&VFw&÷VæB6Æ–Òv—F‚æò7FFVB&V6öæ–ær—2æ÷râW'&÷"&F†W"F†âv&æ–ærâçVÖ&W"Ââ–B÷"6öæf–FVæ6R7F–ÆÂ7FÆW2F†Rw&÷VæBÂ6òF†R7V2w2f–wW&W2æBF†R&¶R&R7F–ÆÂöæR6Æ–6Râ£ÓBF†Rƒ3RÆ¶R7W&f6Râ¢¤æW‡B6Æ–6R¢¢ÂæB—BæVVG2&¶Rf÷"F†Rw&÷VæBtÄ"Â6ò&V6÷&B²ÖW6‚ÆæBFövWF†W"âGvòF†–æw2&6VÂ†’†æG2—C¢F†R&"—2¦ÆæB–ç6–FRvFW"¢Â6òF†R6–væVBÖF—7Fæ6R'VÆRF†B'V–ÆG2F†Rf÷&·2w&÷VæB†2FòVæFW'7FæB—6ÆæG2Âæ÷BöæÇ’&æ·3²æBæòVÆWfF–öâf÷"F†R&"W†—7G2–âç’6÷W&6RÂ6ò—G2†V–v‡B—27V2&wVÖVçBFò&RÖFR–âF†R÷VâÂæ÷BçVÖ&W"Fò–6²à¢Ò¢¢†2’‡–G&öÆöw’¢¢(	BF†R6Æ÷Vv‚‡V&Æ–2×7V&RöæB(i"7BÆ¶RbFV&&÷&â(i"&—fW"BF†Rfö÷Böb7FFR’Âg&öröæBBÆ¶RbÆ6ÆÆRÂF†RvVÆÇ27G&VWBÖ'6‚ÂF†RÖ'6‡’&—fW"×6†÷&R7G&—à¢Ò¢¢†B’FW'&–åövVâç–¢¢(	B7V2²fV7F÷'2(i"FW'&–âÖW6‚²†V–v‡Ff–VÆBæ&–æf÷"6öÆÆ—6–öâà ¥&VÖ–æFW#¢–W'2æB'&–FvW2&R¢§7G'V7GW&W2v—F‚†6W2¢¢Âæ÷BFW'&–â‡6VRFö72ôUô4…2æÖF’à ¢22#(	B&VæFW&W"6†VÆÂ+r¦6â7F'Bæ÷rÂæVVG2æòFGVÒ  ¥&6VÇ3¢†’6†VÆÂ²–çWBÖ–çFVçBÆ–W"²vÆ¶W#²†"’6öæf–FVæ6R6†FW"²&÷fVææ6R÷W ¦v–ç7B†æB×w&—GFVâFW7B6–FV6#²†2’FööÇ2÷6Öö¶RæÖ§6à ¤'V–ÆBv–ç7B7–çF†WF–2vVöÖWG'’æBfÆBw&÷VæBâ6öçG&7B–âFö72õÄâæÖFâÖö&–ÆP¢ƒ3“9ssƒ’—2&VÆV6RvFRg&öÒF†Rf—'7BvÆ¶&ÆR6öÖÖ—B(	B&WG&öf—GF–ærF÷V6‚–çFò4@§vÆ·F‡&÷Vv‚ÆFW"—2F†RW‡Vç6—fRv’FòFò—Bà ¢22#"(	B&VæFW&–ær&öw&Ò+r¢¤5D•dR(	B÷væW"&Wf–WvVBæBÖW&vVB##bÓ‚ÓB…"3b’¢  ¥F†R†6VBÆâf÷"†–v†W"Öf–FVÆ—G’&VæFW&–ær(	BG&6²†vÆ²ö–×&÷fVB–âÆ6S¢Æ–v‡BÀ§FW‡GW&W2ÂòÂ666FW2ÂFÖ÷7†W&RÂvFW"Â6öçFVçB’ÂG&6²"†6V6öæB†–v‚Öf–FVÆ—G’vV §&VæFW&W"BvÆ²Ö†Bö’ÂG&6²2†æF—fRÖVæv–æR&VæFW&W"’(	BÆ—fW2–âFö72õ$TäDU$”äræÖFÀ§v—F‚W"×†6RvFW2Â66WFæ6RçVÖ&W'2æB'VææW"&÷WF–ærà ¢¢¥F†RrG&6²æBs&R'V–ÆF&ÆRæ÷râ‚æBâ7F’vFVB¢¢&V†–æBF†RõtäU"DT4•4”ôæ ¦—FV×2–â$TäDU$”är*s‚Â2FòF†R÷Vâ'VFvWBæBF—7G&–'WF–öâVW7F–öç2âF†R6Æ–Ö&ÆP§&6VÇ2&RF†R¢¥$TäDU$”ärÆæR¢¢&VÆ÷s²V6‚öæRæÖW2—G2$TäDU$”är†6RÂ—G2f–ÆRÆ—7BÀ¦—G266WFæ6RçVÖ&W'2æB—G2'VææW"à ¢¢¤WfW'—F†–ærÆæG2öâFWf¢¢†Fö72õ•TÄ”äRæÖF’â&öGV7F–öâÖ÷fW2öæÇ’v†VâF†R÷væW ¦F—7F6†W26†–6vòÓFB×&öÖ÷FR×Fò×&öBç–ÖÆà ¢2232(	BÖ–ÆW7FöæR¢F†R6Vvæ6‚ÂVæBFòVæ@ ¤FVf–æ—F–öâöbFöæR–âFö72õÄâæÖFâF†R&V6÷&BÂF†R6÷W&6W2ÂæBF†RF÷76–W"&RÇ&VG§w&—GFVã²v†B&VÖ–ç2—2F†Rg&ÖU÷FfW&æ&6†WG—RÂF†Rf—'7B&¶RÂæBF†RvÆ¶&ÆRvP§v—F‚v÷&¶–ær6öæf–FVæ6RFövvÆRà ¥7V66W72—2æ÷B&'V–ÆF–ærV'2"â7V66W72—2F†Bf–WvW"6âFövvÆRF†R6öæf–FVæ6Rf–Wp¦æB6VRW†7FÇ’v†–6‚'G2öbF†R6Vvæ6‚vR6âFVfVæB(	BF†Rv†—FRGvò×7F÷'’&Æö6²æBF†P¦&ÇVR6‡WGFW'26öÆ–BÂF†R–çfVçFVBfö÷G&–çBæBF†RF—7WFVBvÆÆW'’F—F†W&VBà ¢223’(	B7G&VWG2Â&öG2æBF‡2+r¢¥d•4”$ÄRT%D‚Ä”U"²Ä•dRäÔU2DôäR##bÓ‚Ó¢  ¤6¶VBf÷"2'7G&VWG2Â&öG2ÂF‡2–â67W&FR7W&f6RæBVÆWfF–öç2"ÂF†VâW‡æFVBFò§FövvÆV&ÆRƒ3Rö7W'&VçBÖæÖR&VF÷WBâF†Rf—'7BFFVBf—6–&ÆRÆ–W"—2æ÷r–ã¢6WfVçFVVâV'F€§G&fVÇv—26ö×–ÆVB–çFòF†R66VæR–æFW‚ÂG&VBöâF†R†V–v‡Ff–VÆBÂ7WBBvFW"Â6ÆV&VBöæÇ§F‡&÷Vv‚F†Ræ'&÷rG&fVÆÆVB7G&—ÂG&vâöâF†R÷fW'f–WrÖæBVW&–VBÆ—fRf÷"F†R7G&VW@§VæFW&fö÷B÷"F†RæW‡B7&÷727G&VWB†VBâF†R&VÖ–æ–ærv÷&²—2FòW‡FVæB6öçG&öÂöâæ÷'F‚vFW ¦æBF†Ræ÷'F‚×6–FRw&–BÂ&W6V&6‚ç’FFVBÆæ²fö÷GvÆ·26W&FVÇ’ÂæB&WÆ6RÃs’w2f—7VÀ§vV"v–GF‡2v†W&WfW"7V6–f–6F–öâ÷"FW–7F–öâ7W'f—fW2à ¢¢¤†ÆböbF†B6VçFVæ6R—26öÖÖ—GFVBFF2öb##bÓ‚Óâ¢¢FF÷G&6W2÷7G&VWEö6öçG&öÂæ§6öæ ¦†öÆG2F†RÖöGVÆRƒƒgB7G&VWG2Â–æfW'&VFÂv—F‚F†RcbgBF—76VçB&V6÷&FVB&W6–FR—B’æBF†P¦6öçG&öÂF&ÆRF†—2&ö¦V7B7GVÆÇ’6æ2FòÂV6‚7G&VWB6''––ær—G2†—2æB—G2ÖöFW&à¦WV—fÆVçB(	BæBÂ6–æ6R##bÓ‚ÓÂF†R'VÆRF†BÖ¶W26öçG&öÂö–çB&RÖFW&—f&ÆR&F†W"F†à¦ÖW&VÇ’&RÖfWF6†&ÆR†æöFU÷'VÆV¢F†RæöFW26†&VB'’F†RGvòæÖVB7W&f6R&öGv—2ÂfW&vVBÀ§v—F‚&–¶Wv—2æB7F6¶VBÆ÷vW"ÖÆWfVÂ7G&VWG2W†6ÇVFVB’âv†B—27F–ÆÂÖ—76–ærf÷"F†—2&6VÂ—0§F†RÆBw2¢¦&Æö6²F–ÖVç6–öç2æBW‡FVçB¢¢(	BF†Bf–ÆR†öÆG2öæÇ’v†BF†RW†—7F–ærÆ6VÖVçG0§W6VBâ6VRFö72õ$U4T$4‚÷7G&VWEöÖöGVÆUóƒ3æÖFà ¢¢¤æBF†RÖöGVÆR—2ÖV7W&VB&F†W"F†âææ÷FFVBÂ##bÓ‚Ó¢¢…5DEU2*rC"À¦Fö72õ$U4T$4‚÷7G&VWEöÖöGVÆUóƒ3æÖF*r‚ÂFF÷G&6W2÷fV7F÷'2÷7G&VWEö6÷'&–F÷'5óƒ3Bæ§6öæ’à¤V–v‡BÆGFVB6÷'&–F÷'2&VBöfb$õD‚ƒ3B6†VWG2ÂsRãrÓ“"ã‚gBÂæöæRv—F†–â’gBöbcc¢F†P¦F—76VçB—2W†6ÇVFVBæB6ò—2F†R&V6öæ6–Æ–F–öâF†B—BÖ–v‡B&R&÷WBF–ffW&VçB7G&VWG2âGvð§F†–æw2F†—2&6VÂ–æ†W&—G2âf—'7BÂ¢¦ÖV7W&VB&Æö6²—F6‚¢¢(	B6WfVâ6öç6V7WF—fR6÷'&–F÷ §76–æw2öbbãbÓ#2ã"ÒÂF†R3gB&Æö6²ÇW2öæR7G&VWB(	Bv†–6‚—2F†R&Vv–ææ–æröbF†R&Æö6°¦F–ÖVç6–öç2F†—26V7F–öâ6·2f÷"ÂF†÷Vv‚æ÷B–WBF†RÆBw2W‡FVçBâ6V6öæBÂ¢¦ÖWF†öB&ö&ÆVÒFð§6öÇfR&Vf÷&RF†RRÕr7G&VWG26â&RÖV7W&VB¢£¢F†RâÕ2G&fW'6R&VG2w&–v‡Bw2Æ÷BÆ–æW2Âv†÷6P¦FWF‡2&RÆGFVB7G&VWBw2v–GF‚æBv†÷6RÆ–æW2'Vâ2f"2&Æö6²f6RFöW2Â6ò6÷'&–F÷ ¦†W&R†2Fò&R–FVçF–f–VB'’6öÖWF†–ær÷F†W"F†â—G2v–GF‚âÆ¶RÂ&æFöÇ‚Â6÷WF‚vFW"æ@¤Ö&¶WB&RVæÖV7W&VBVçF–ÂF†BW†—7G2à ¢¢¥4ôÅdTB##bÓ‚Ó¢¢…5DEU2*rS"ÂÖVÖò*r’âF†RF‡&VRFW7G2F†Bf–ÆVB&RÆÂ&VF–æw0§F¶Vâ¦7&÷72¢6æF–FFRBöæRÆ6S²F†RöæRF†Bv÷&·2GW&ç2æ–æWG’FVw&VW2æB6·2†÷rf ¦6æF–FFR—2÷Vâw&÷VæB¢¦F÷vâ—G2÷vâ6VçG&VÆ–æR¢¢Âv†–6‚7G&VWB—2f÷"v†öÆR&Æö6²æB§7G&—öbÆ÷G2æWfW"—2âF†RF‡&W6†öÆB—2FW&—fVBg&öÒF†RÖöGVÆR&æBƒ“R(‰"3ÒcRÒ’&F†W §F†âGVæVBâ¢¤Æ¶R&VG2s’ãBgBæB&æFöÇ‚ƒãRgB¢¢öâw&–v‡B(	B&÷F‚æÖVB'’F†V—"6öÖÖ—GFV@¦ÖöFW&â§Væ7F–öç2Fòã’ÒÂæ÷B'’6÷VçF–ær(	Bv—F‚öæRVææÖVB6÷'&–F÷"&Æö6²gW'F†W"6÷WF‚@£ƒbãRgC²FVâÆ÷B7G&—2vW&R&V¦V7FVBæBæöæRöbF†RV–v‡BÇ&VG’Ö6öÖÖ—GFVB6÷'&–F÷'2v2à¥F‡&VRF†–æw2F†—2&6VÂ–æ†W&—G2g&öÒ—Bâ¢¥F†RRÕr—F6‚—23BÓ3bÒv–ç7BbãbÓ#2ã"ÒF†P¦÷F†W"v’¢¢Â6òF†R&Æö6·2&RäõB7V&RæBF†R3gB&Æö6²F†Bf—G2F†RâÕ27G&VWG2FöW2æ÷@¦FW67&–&RF†VÒ(	BF†B—2F†R&W7BöbF†R&Æö6²F–ÖVç6–öç2F†—26V7F–öâ6·2f÷"ÂæB—B6öÖW2öf`§Gvò76–æw2öâöæR6†VWBÂ6òÖV7W&RÖ÷&R&Vf÷&RvVæW&F–ærw&–Bg&öÒ—Bâ¢¥F†RRÕrv–GF‡0§&W7BöâöæR6†VWB¢£¢†F†v’w2âÕ2G&fW'6R6öÖÖ—G2æ÷F†–ærÂ6òF†W’†fRæò7&÷72Ö6†V6²âæ@¢¢¥6÷WF‚vFW"æBÖ&¶WB&R7F–ÆÂVæÖV7W&VB¢¢(	BÖ&¶WBfÆÇ2÷WG6–FR&÷F‚G&fW'6W2ÂæBWfW'¦6æF–FFRæ÷'F‚öbÆ¶R—2&÷VæFVB'’Æ–æRF†B7F÷2gFW"#BÓ3"Òâ&÷F‚æVVBG&fW'6P§Æ6VBf÷"F†VÒÂæ÷BÆö÷6W"f–ÇFW"à ¢¢¤6WF–öâf÷"F†RvVæW&F÷"Âg&öÒF†R6ÖR6Æ–6Râ¢¢F†R6÷'&–F÷'2G&vâöâF†W6R6†VWG2'Và¦&÷WBRgBv–FW"F†âƒgBöâ&÷F‚ÂæBF†B—2W"7G&WF6‚ÇW2VâÆ6VÖVçBÂæ÷BWf–FVæ6P¦öbv–FW"7G&VWBâvVæW&FRF†Rw&–Bg&öÒF†RÆGFVBÖöGVÆRŒ*r&÷fR’æB6æ—BFò6öçG&öÂ(	@¦Fòæ÷Bf—B—BFòF†RG&6VB6÷'&–F÷"v–GF‡2Âv†–6‚v÷VÆB&¶RBRöbW"F—7F÷'F–öâ–çFòF†P§F÷vâà ¢¢¤vVöÖWG'’6öÖW2g&öÒF†RF†ö×6öâÖöGVÆRÂvVæW&FVBÂæ÷BG&6VBâ¢¢F†Rƒ3ÆBv—fW0£ƒÖgB7G&VWG2æB‚ÖgBÆÆW—2÷fW"F†R÷&–v–æÂã3sR7Ö“²w&–v‡Bƒ3B6†÷w2F†R6ÖP¦w&–BW‡FVæFVBÂæB&÷F‚6†VWG26''’+#ÒöbvV÷&VfW&Væ6–ær6Æ÷F†BG&6–ærv÷VÆB&¶P¦–â2vö&&ÆRâvVæW&FRF†Rw&–BæÇ—F–6ÆÇ’g&öÒF†RÖöGVÆRæB6æ—BFò6öçG&öÂâ§7G&VWBF†B—27G&–v‡B&V6W6RF†R7W'fW–÷"ÖFR—B7G&–v‡B6†÷VÆBæ÷B'&—fR&Vç@¦&V6W6RvRG&6VBföÆFVB6†VWBà ¢¢¢$67W&FR7W&f6R"–âƒ3RÖVç2V'F‚Âæ÷Bw&fVÂâ¢¢F†Rf—'7B–ç7F–æ7B(	B7&÷væVBÀ¦¶W&&VBÂw&fVÆÆVB÷"fVB&öGv’(	B—2w&öærf÷"F†RFFRÂ'WBF†RV&Æ–W"v÷&F–ær†W&Rv0§Föò'&öB–âF†R÷÷6—FRF—&V7F–öââF†Röff–6–Âƒ“×Væ–6—Â6‡&öæöÆöw’&V6÷&G26÷WF€¥vFW"÷&FW&VB—F6†VB'’&–Âƒ3BæBw&FVBf÷"G&–ævRF†B§VÇ’ÂæB6ÆÇ26÷WF‚vFW ¦æBÆ¶RF†RGvò&–æ6—ÂV&Ç’GW&ç–¶VBæBw&FVB7G&VWG2â—B6W&FVÇ’FFW26æÂÀ¤Æ¶RvW7BFòFW7Æ–æW2æB&æFöÇ‚GW&ç–¶–ærFòfÆÂƒ3c²7G&VWBÆæ¶–ær&Vv–ç2–âƒCBÀ¦vVæW&ÂÆæ¶–ær–âƒC’ÂÆ–ÖW7FöæR&Æö6²–âƒSRÂæBÖ6FÒö6ö&&ÆR–âƒSbâöâ§VÇ’ƒ3P§F†RFVfVç6–&ÆRf—7VÂfö6'VÆ'’—2F†W&Vf÷&R¢¦w&FVB÷"F‡&÷vâ×WV'F‚öâF†R&–æ6—À§&÷WFW2Âv÷&âæF—fR6ö–ÂöâÆW76W"7G&VWG2Âw&77’Ö&v–ç2Âæòw&fVÂ÷"†&Bf–ær¢¢âFFV@§Ææ²fö÷GvÆ·2&VÖ–â6W&FR&W6V&6‚&6VÂæB&Ræ÷B6–ÆVçFÇ’7WÆ–VB'’F†R&öBà ¢¢¢$67W&FRVÆWfF–öç2"ÖVç2ÖöFW7BV&Ç’w&F–ær—2æ÷BF†RÆFW"&—6–æröb6†–6vòâ¢ ¥6÷WF‚vFW"w2Fö7VÖVçFVBG&–ævR÷&FW"ÖVç2&æ÷F†–ær†B&VVâw&FVB"v2fÇ6Râv†Bæð§6÷W&6R7WÆ–W2—2F†RÖ÷VçBÂ7&÷72×6V7F–öâÂ7&÷vâ÷"f–ÆÂ&öf–ÆRÂ6òF†—2f—'7BÆ–W"FöW0¦æ÷BVF—BF†R†V–v‡Ff–VÆB÷"–çfVçBöæS¢—G2fW'F–6W26×ÆRF†RW†—7F–ærw&÷VæBW†7FÇ’æB6—@£#"ÖÒ&÷fR—BöæÇ’Fòfö–BFWF‚f–v‡F–ærâF†RvÆ²6ÖW&æ÷rÆö6·2FòF†B6ÖR&–Æ–æV §7W&f6RV6‚g&ÖR–ç7FVBöbV6–ær&V†–æB—Böâ&—6W2æBfÆÇ2âv†W&R7G&VWB&V6†W2vFW"À§F†R&–&&öâ7F÷3²7&÷76–ær—26öçFVçBFò&W6V&6‚Âæ÷B&VæFW&–ær'FVf7BFòfÆGFVâv’à ¢223V(	Bf÷'BFV&&÷&â+r¢¤DôäR##bÓ‚Ó¢  ¤¶Wf–âw26ÆÂÂæBF†RFWVæFVæ7’†RæÖVB—26F—6f–VC¢F†R6ö7FÆ–æRÂF†R6æB&"æBF†P¦†&&÷W"v÷&·2&R&VBÂ6òF†W&R—2w&÷VæBFòWB—Böâöæ6R3&R'V–ÆG2F†R†V–v‡Ff–VÆBà ¢Ò¢¥÷6—F–öâ—26WGFÆVBæB7&÷72Ö6†V6¶VB¢£¢Æö6ÂR³S"Ââ³##ÂGvò–æFWVæFVçBÖWF†öG0¢3RÒ'B‡6VR3&R’à¢Ò¢¥v†B—B§v2¢öâƒ3RÓrÓ—24UEDÄTBÂ##bÓ‚Ó¢¢(	BFö72õ$U4T$4‚öf÷'EöFV&&÷&âæÖFà¢â¢¦ö67W–VBVæ—FVB7FFW2&×’÷7BÂ6öÖÖæFVB'’Ö¦÷"¦ö†âw&VVæR¢¢Âv†ò†VÆB—Bg&öÐ¢‚FV6VÖ&W"ƒ32VçF–Âb6WFVÖ&W"ƒ3RâF‡&VR6W&FVÇ’w&—GFVâ66÷VçG2w&VRF†Rf÷'@¢v2v'&—6öæVBF‡&÷Vv‚ƒ3RæBF†R÷7B7W&vVöâw2&W67&—F–öâ&öö²†2âVçG'’FFV@¢RÖ&6‚ƒ3RâF†R6öÆF–W'2ÆVgBöâ#’FV6VÖ&W"ƒ3bæBF†R÷7Bv2æ÷Bv—fVâWVçF–À¢§VæR÷"§VÇ’ƒ3r(	Bv†–6‚—2†÷ræG&V2ÖævW2Fòv—fRƒ3b–âöæR6†FW"æ@¢Ö’ƒ3r–âæ÷F†W"âæ÷F†–ær†W&RvöW2FòFFöW†6ÇW6–öç2æ§6öæ²F†Rf÷'Bv2†W&Rà¢Ò¢¥F†Rfö÷G&–çB—27F–ÆÂäõB6÷W&6VBÂ'WBF†R6V&6‚—2æ'&÷vVBFòF‡&VR6æF–FFW2â¢ ¢w&–v‡B¦Æ&VÇ2¢F†R&W6W'fF–öâæBG&w2æòÆã²æV—F†W"FöW2†F†v’âF†R&W7BÆVB—0¢7W'fW’Âæ÷B–7GW&S¢F†Rv"FW'FÖVçBw2vVçBÂ&W÷'F–æröâ#æ÷fVÖ&W"ƒCÂæÖW0¢F†RÆGFVBÆ÷G2öbF†R¢¤f÷'BÔFV&&÷&âFF—F–öâƒƒ3’’¢¢F†BvW&Rv—F††VÆBg&öÒ6ÆP¢&V6W6RF†W’6÷fW&VB'F†Rf÷'G&W72öbf÷'BFV&&÷&â§v—F†–âF†R–6¶WG2¢"âf–æBF†BÆBÀ¢f—B—B†—G27G&VWG27W'f—fR–âF†RÖöFW&âw&–B’æB&VBF†Rv—F††VÆBÆ÷G2â6V6öæC¢¢¤†Vç'¢†'Bw2ƒS27W'fW’öbF†Rf÷'B¢¢ÂæÖVB'WBæ÷B–WBÆö6FVBâF†—&C¢v"FW'FÖVçBÆà¢öbF†R&V'V–ÇBf÷'BÂæWfW"Æöö¶VBf÷"â'VÆVB÷WBv—F‚&V6öç2–âF†RÖVÖò*rr(	BFòæ÷@¢&R×'VâF†VÒâ7F–ÆÃ¢Fòæ÷B–æfW"7Fö6¶FR÷WFÆ–æRg&öÒ&ææW"à¢Ò¢¤f÷W"6öç7G&–çG2W†—7Bæ÷rF†BF–Bæ÷Bâ¢¢wW&Föâ2â‡V&&&BÂ6÷'&V7F–ærF†R¥vRÔ'Vâ ¢f–Wr–âƒƒÂ7FFW2F†BF†RVæ6Æ÷7W&R&â&æV&Ç’æ÷'F‚æB6÷WF‚ÂV7BæBvW7B#²F†@¢F†Ræ÷'F‚–6¶WBÆ–æR7FööBæ÷v†W&RÖ÷&RF†âƒgBg&öÒF†RvFW"æBSÓcgB÷÷6—FP¢F†Ræ÷'F‚vFS²F†BF†Rw&÷VæBBF†Rf÷'Bv2&æ÷B÷fW"V–v‡BfVWB&÷fRF†R&—fW"B—G0¢Æ÷vW7B7FvR#²æBF†BF†Ræ÷'F‚æB6÷WF‚vFW2vW&RöâöæR6–v‡BÆ–æRâF†Rf—'7BGvò&P¢W6&ÆRv–ç7BF†RG&6VBƒ3B&æ²â¢¥F†RF†—&B—2f–æF–ær&÷WBF†RFW'&–â¢£¢â‚g@¢ÆFf÷&Ò—2FÆÆW"F†âç’ÆæFf÷&Ò–âF†RÖöFVÆÆVB&÷‚‡F÷FÂ&VÆ–VbBã3gB’Â6ò—@¢&VÆöæw2Fò3&R&6VÂ†"’2×V6‚2FòF†—2&6VÂà¢Ò—B—2¢¦6ö×ÆW‚Âæ÷B'V–ÆF–ær¢£¢3Rw2f÷'BFV&&÷&â&6VÂÇ&VG’—FVÖ—6W2Æ—6FRÀ¢&Æö6¶†÷W6RÂ&7F–öâÂÖv¦–æRÂV'FW'2Â&'&6·2Â7WFÆW"Â†÷7—FÂÂ&FRæBv&FVç2à¢W‡V7B6WfW&Â&V6÷&G2æB6WfW&Â&¶W2Âæ÷BöæRâF†R–çFW&–÷"'&ævVÖVçB—2æ÷rGFW7FV@¢VÆVÖVçB'’VÆVÖVçB†ÖVÖò*rR’æBF†RöæR÷VâF—6w&VVÖVçB—2v†WF†W"F†W&RvW&RGvð¢&7F–öç2÷"öæRà¢Ò¢¤6WF–öâF†RÖVÖò—2f÷"â¢¢F‡&VRVæ6Æ÷7W&W2vWB6öægW6VB–âF†—2Æ—FW&GW&RæBöæÇ¢öæR—2F†Rƒ3Rf÷'C¢F†Rƒb7Fö6¶FRÂF†R÷7BÖ&×’6ö×÷VæBöbƒS‡–6¶WG2vöæRÂ¢v†—FWv6†VB&ö&BfVæ6RÂ'6’CfVWB"’ÂæBF†RS<+ÂÖ7&R&W6W'fF–öââF†RCgBf–wW&P¢—2F†RÖ–FFÆRöæRæB×W7Bæ÷B&R&VB2Æ—6FRà ¢¢¤†÷r&÷F‚vFW2vW&R6ÆV&VBÂæBv†B—B6÷7Bâ¢  ¢Ò¢¥F†RÆâ6÷W&6RW†—7G2æB—B—27W'fW’â¢¢¤ÖöbF†RÖ÷WF‚öb6†–6vò&—fW"¢Âbâ†'&—6öà¢§"âÂ72wBRå2â6—f–ÂVæv–æVW"Âf÷"F†R&÷÷6VB†&&÷W"–×&÷fVÖVçG2Â&÷fVB'’v–ÆÆ–Ð¢†÷v&B#BfV''V'’ƒ3(	B&W&öGV6VB–â¢¤æG&V2föÂââ2¢¢æBÆ—7FVB–âF†BföÇVÖRw0¢÷vâF&ÆRöbÖ22$f÷'BFV&&÷&â–âƒ3Ó3""â—BG&w2F†Rf÷'B–âÆâæBæÖW2F†Rw&÷Væ@¢&÷VæB—B„v&FVâf÷"F†Rv'&—6öâÂ7VÇF—fFVBf–VÆBÂ&–r&&âv—F‚7WöÆÂv6‚†÷W6RÂvVÆÂÀ¢6†÷Âf÷'B6VÖWFW'’ÂF†RfW''’’â&V6÷&FVB2†'&—6öåóƒ3÷&—fW%öÖ÷WF†Â76WE÷W6S¢vVöÖWG'–À¢F–W""(	B&V6W6RF†RÆFR6—2öâ—G2f6RF†B—B6'&–W2&FF—F–öç2æB6†ævW2(
b7VvvW7FV@¢'’F†RÖVÖ÷'’öbV&Ç’6WGFÆW'2"Â6ò—B—2W&–öB7W'fW’ÇW2f–gG’×–V"ÖöÆB&V6öÆÆV7F–öà¢Ö—†VBöâöæRÆFRâ¢¤æ÷F†–ærF¶Vâg&öÒ—B—2w&FVBFö7VÖVçFVFâ¢ ¢Ò¢¥F†RÆFR†2æò66ÆR&"ÂæBF†B—2F†Rv†öÆRF–ff–7VÇG’â¢¢F†R66ÆR—2FW&—fVB'¢6WGF–ærF†RG&vâæ÷'F‚&ævRWVÂFòF†R6öÖÖæFçBw2V'FW'2B&&÷WB#R‚SgB"g&öÒF†P¢ƒSR†÷Föw&‚¶W’(	BãgB÷‚(	BæB6†V6¶VBGv–6RöâF†R6ÖRÆFR†G&vâ7V7Bã“£¢v–ç7B7FFVB"ã£²&FRv–GF‚sgBv–ç7B7FFVBƒgB’â¢¬+#R¢¢öâWfW'’FW&—fV@¢F–ÖVç6–öâÂöâF÷öbF†RFGVÒw2+#ÒâF†R7Fö6¶FR6öÖW2÷WB&÷WB¢£S2ÒƒsBgB’7V&R¢¢à¢¢¤æòF–ÖVç6–öâöbF†Rƒbf÷'BW†—7G2–âF†RÆ—FW&GW&R¢£¢V–fRw2Ööæöw&‚&–çG0¢v†—7FÆW"w2ÖV7W&VBƒ‚G&Vv‡BöbF†Rd•%5Bf÷'BæB7FFW2æöæRf÷"F†R6V6öæBç—v†W&Rà¢Ò¢¥F†R'&ævVÖVçB—2×V6‚&WGFW"Wf–FVæ6RF†âF†R66ÆR¢¢ÂæB—B—2v†BÆ–6Vç6W2–æfW'&VF ¢&F†W"F†â6öæ¦V7GW&Æf÷"F†R÷6—F–öç3¢âƒ3Væv–æVW"w2ÆâæBwW&Föâ‡V&&&Bw2ƒ#p¢vÆ²&÷VæBF†R–ç6–FRw&VR'V–ÆF–ær'’'V–ÆF–ærÂöâF†R6ÖR6–FW2öbF†R6ÖRGvòvFW2à¢Ò¢¥F†Rv'&—6öâ—26WGFÆVBâ¢¢†VÆB6öçF–çV÷W6Ç’¢¤§VæRƒ3"(i"#’FV6VÖ&W"ƒ3b¢£²æG&V0¢'&6¶WG2F†R66VæRFFRæBF†RG&Æö–†¦÷W&æÂ6‡&öæöÆöw’f–ÆÇ2F†R'&6¶WBv—F‚¢¤Ö¢â¦ö†à¢w&VVæRÂWF‚–æfçG'’¢¢âGvò6ö×æ–W2–âƒ33²¢¦æò7G&VæwF‚f–wW&Rf÷"Ö–BÓƒ3Rv2f÷VæBæ@¢æöæR—26Æ–ÖVB¢¢âF†Rf÷'B—2ÖöFVÆÆVBÖ–çF–æVBÂv—F‚—G2vFW26‡WBà¢Ò¢¤f÷W'FVVâ&V6÷&G2ÂGvòæWr&6†WG—W2Âf÷W'FVVâ&¶W2ÂãrÃG&–ævÆW2â¢¢Æ—6FV ¢‡–6¶WB7Fö6¶FRv—F‚æÖVBvFW2æB6÷&æW"v÷&·3²v÷&Ò&–ÂfVæ6Rf÷"F†Rv&FVâ’æ@¢f÷'E÷7G'V7GW&V†VÆWfVâ¶–æG2(	BV'FW'2Â&'&6·2Â&Æö6¶†÷W6RÂÖv¦–æRÂ7F÷&RÂwV&BÀ¢7WFÆW"Â'F–ÆÆW'’Â&FRÂ&ö÷B†÷W6RÂF÷vW"’âF†RÆ–v‡F†÷W6Röbƒ3"6ÖRv—F‚F†VÒà¢Ò¢¤f—fRW†6ÇW6–öç2Âf÷W"öbF†VÒw&öærÖf÷'Bf–æF–æw2¢£¢F†Rf—'7Bf÷'B—G6VÆbÂF†R6ÆÇ’×÷'BÀ¢F†RF‡&VR'F–ÆÆW'’–V6W2æBF†Rf–gG’–çfÆ–G2ÂF†RƒS2&ö&BfVæ6RæBGW&ç7F–ÆR(	BÇW0¢¢§F†W&R—2æò†÷7—FÂ'V–ÆF–ær¢¢ÂöæÇ’F†Rf÷'B¦&V6öÖ–ær¢vVæW&Â†÷7—FÂ–âF†Rƒ3 ¢6†öÆW&âF‡&VR6÷'&V7F–öç2FòFö72÷&W6V&6‚óB×7G'V7GW&W2×6÷WF‚æÖF&R&V6÷&FVB–à¢Fö72õ$U4T$4‚öf÷'EöFV&&÷&âæÖF*rbÂæBöæRFò*r"–à¢Fö72õ$U4T$4‚ö6†–6võöÆ–v‡F†÷W6Uóƒ3"æÖFà¢Ò¢¤—B7FööBöâæ÷F†–ærf÷"&÷WBf÷W"†÷W'2â¢¢F†R6ö×ÆW‚—2ƒ3"ÒV7Böbv†W&RF†P¢†V–v‡Ff–VÆBW6VBFò7F÷ÂæBv†–ÆR—Bv2F†W&R—BW‡÷6VB&VÂ&Æ–æB7÷B–âF†P¢w&÷VæBÖ6öçF7BvFR(	BF†R6Æ×VBVFvRÖFRf÷'B–âF†Rfö–B&W÷'BW&fV7BÆæF–ærâ6VP¢5DEU2*r$¶æ÷vâvV¶æW76W2"â¢¥3&R&6VÂ†"’F†VâÆæFVBF†R6ÖRF’¢£¢F†Rf–VÆB&V6†W0¢R³sÂGvVÇfRöbF†Rf÷W'FVVâ7G'V7GW&W2ÆæBÂæBF†RÆ–v‡F†÷W6RæBF†R&ö÷B†÷W6R(	B&÷F€¢6öæ¦V7GW&Æ–â÷6—F–öâ(	BÖ÷fVBöfbF†R6†ææVÂæBöçFòF†R&æ²F÷æ÷rF†BF†W&R—2¢7W&f6RFò&Rw&öær&÷WBâF†RGvòF†B&VÖ–âöfbF†Rw&÷VæB&RF†R7Fö6¶FRæBF†P¢6öÖÖæFçBw2V'FW'2Âv†÷6Ræ÷'F‚6–FW27&÷72F†RF÷öbF†R&—fW"&æ²'’ãCÒæBãCbÒÀ¢&V6W6R¢¦æò7WBÂf–ÆÂÂ&WfWFÖVçB÷"f÷VæFF–öâ—2ÖöFVÆÆVBç—v†W&R–âF†—2&ö¦V7B¢¢âÃCbà ¢¢¥F†RvFW2vW&R÷VâÂæBEóæWfW"G&WrF†R6÷&æW"v÷&·2—Bv26–BFò…BÓ“RÀ£##bÓ‚Ó#B’â¢¢Gvòf–æF–æw2ÂöæRÖV7W&VBöfbF†R6†VWBæBöæRöfbF†R6†—VBÖW6‚(	@¦Fö72õ$U4T$4‚öf÷'EöFV&&÷&åövFUöæEö6÷&æW%÷v÷&·2æÖFÂ†VÆB'¦FööÇ2öÖV7W&Uöf÷'E÷v÷&·5÷ÆFRç–æBFööÇ2öÖV7W&Uöf÷'EövFW2ç–à ¢Ò¢¥F†RÆFR&—6W2æòv÷&²BV—F†W"ævÆR—BG&w2â¢¢—B&—6W2W†7FÇ’Gvò&ööfVBÀ¢ÆçFW&æVBÂÆörÖf6VBv÷&·2æB&÷F‚7FæB÷fW"F†RÔ”DDÄRöbF†RvÆÂÂB¢£ãC3Ræ@¢ãS#¢¢öbF†RG&vâ'Vã²6÷&æW"v÷&²7FæG2Bã÷"ãâF†RöæRævÆR—B6†÷w0¢Væö66ÇVFVB—2F†Ræ÷'F‚ÖV7BæB—B—2G&vâÆ–â(	Bv†–6‚—2v†BF†R&V6÷&B6—2öbF†@¢ævÆRâF†Ræ÷'F‚×vW7BævÆRÂF†RöæRF†R&V6÷&BFöW2WBv÷&²BÂ—2&V†–æBF†RG&VP¢÷WG6–FRF†RvÆÇ2â¢¤æ÷F†–ærv2Ö76VBBF†RævÆW2¢¢ÂæBF†RÆörÖf6VBv÷&²÷fW"F†P¢vFRv2æ÷B'V–ÇBV—F†W#¢F†R6†VWBÇ&VG’6'&–W26W'F–f–VBd•%5BÖf÷'BfVGW&R‡F†P¢fÆw7FfbÂFFöW†6ÇW6–öç2æ§6öæ’æBGvò&ööfVBÆçFW&æVBÆörF÷vW'2—2F†Bf÷'Bw2÷và¢6–væGW&R–âWfW'—F†–ær'WB÷6—F–öââ6ÖRf–ÇW&R2BÓ“BÂöæRF’'BÂöâF†R6ÖP¢6†VWC¢F†RÆFR&VB'’W–Rà¢Ò¢¤&÷F‚Fö7VÖVçFVBvFW27FööBV'FW"÷Vââ¢¢öæRÆVböbV6‚—"v2Æ6VBg&öÒ¢Ö–Gö–çBF†B6öÆÆ6VBöçFò—G2÷vâ¦Ö"Â6ò¢£ã“ÒöbF†R2ãbÒvFWv’v2F–Æ–v‡@¢7G&–v‡BF‡&÷Vv‚F†RvÆÂ¢¢æBã“ÒöbÆVbÆ’7&÷72F†R–6¶WG2÷WG6–FRF†Rg&ÖR(	@¢–âF†R6öÖÖ—GFVBtÄ"Â6ò–âF†R'—FW2f—6—F÷"F÷væÆöFVBâf÷W"Æ–æW2–âÆ—6FRç–À¢öæR76WB&V&¶VB†f÷'EöFV&&÷&å÷Æ—6FUõ÷–6¶WEóƒf’âF†RvFRF†B†öÆG2—B&VG2F†P¢6†—VBÖW6‚&F†W"F†â&RÖFW&—f–ærF†RÆ6VÖVçBÂ&V6W6RF†RFW&—fF–öâv2F†RfVÇBà¢Ò¢¥F†R6÷WF‚×vW7B&Æö6¶†÷W6RÇ&VG’&VB&÷fRF†R7W'F–â¢¢æBæ÷r†2çVÖ&W#¢’ãC‚Ð¢öb'V–ÆF–ær÷fW"2ãƒÒ7W'F–âÂg&öÒ—G2÷vâ–ç7Fæ6R&÷VæG2–âF†R66VæRà ¢¢¥7F–ÆÂ÷Vâ–âF†—2VG&çBÂ–âF†R÷&FW"F†RWf–FVæ6R7W÷'G3¢¢¢F†RæÖVBw&÷VæBöâF†Rƒ3 §ÆâF†B—2G&vâ27–Ö&öÂæBÆ&VÂæBæ÷F†–ærVÇ6R„&–r&&âv—F‚7WöÆÂv6‚†÷W6RÀ¥vVÆÂÂ6†÷Â÷WB'V–ÆF–æw2ÂRå2âf7F÷"w2†÷W6RÂ7VÇF—fFVBf–VÆBÂF†RfW''’(	BF†Rf÷'B6VÖWFW'¦FVÆ–&W&FVÇ’ÆVgBÆöæR“²F†RG&–ÆÂw&÷VæB6÷WF‚öbF†R–6¶WG2Âv†–6‚¶–ç¦–RGFW7G2æBFöW2æ÷@¦ÖV7W&S²F†Rv&FVâw2ÆçF–ærÂv†–6‚—2Fö7VÖVçFVBæBæVVG2¢¦7VÇF—fFVBfÆ÷&¦öæR¢¢&F†W §F†â7G'V7GW&S²æB¶VWW"w2GvVÆÆ–ær&W6–FRF†RÆ–v‡F†÷W6RÂv†–6‚—2ÆW6–&ÆRæ@§VæGFW7FVBà  ¢223B(	B&6†WG—RvVæW&F÷'0 ¤öæR&6VÂW"&6†WG—RÂV6‚v—F‚vöÆFVâ×&ÖWFW"tÄ"æB&VfW&Væ6R6†÷C  ¦g&ÖU÷FfW&æ+rg&ÖU÷7F÷&Vg&öçF+rg&ÖUöGvVÆÆ–æv+rÆöuöGvVÆÆ–æv+r–ç7F—GWF–öæÆ+p¦f÷'E÷7G'V7GW&V+r÷WF'V–ÆF–æv+rÆæµ÷vÆ¶+r'&–FvU÷F–Ö&W&+r–W%ö7&–&+rÆ—6FV  ¤&ÆÆööâÖg&ÖRÆöv–2‡7GVB76–ærÂ6†VF†–ærÂ&÷÷'F–öç2’—2f—'7BÖ6Æ72&WV—&VÖVçBÂæ÷B¦FWF–Ã¢ƒ3>(	33R6†–6vò—2v†W&R&ÆÆööâg&Ö–ærv2–çfVçFVBÂæB—B—2F†Rf—'7BF†–ær¦¶æ÷vÆVFvV&ÆRf–WvW"6†V6·2à ¢¢¦g&ÖUöGvVÆÆ–ævDôäR##bÓ‚Ó¢¢(	BæB—B—2F†RöæRF†BVæ&Æö6·2†÷W6W2âVçF–Â—BW†—7FV@¦WfW'’g&ÖR&V6÷&B†BFò&RGvò×7F÷&W’V&Æ–2†÷W6R÷"Æör6&–âÂ6òF†RFF6WB†VÆ@§FfW&ç2Â7F÷&W2æB'&–FvRæBæ÷BöæRGvVÆÆ–ærâ—BF¶W27F÷&–W6ÂãR÷""†FVfVÇBF†P§7F÷'’ÖæBÖÖ†ÆbÂ¶æVRvÆÂæBv&ÆRÖVæBGF–2v–æF÷rÂv†–6‚—2F†Rf÷&ÒöbF†W6R–V'2“²&VG0§F†R&V"¢¦VÆÂöfbF†Rfö÷G&–çBöÇ–vöâ¢¢&F†W"F†âöfb–çfVçFVBF–ÖVç6–öç2Â6òâÂ×6†V@§Æâ—2'V–ÇB2âÂæBu$õTäEô4ôåD5C¢W&–ÖWFW&—2Æ—FW&ÆÇ’G'VRöbF†RÖW6ƒ²'V–ÆG2§7Fö÷÷"6ÖÆÂ&ööfVB÷&6‚ÂæWfW"F†RFfW&âw2vÆÆW'“²æBÖ¶W26öç7G'V7F–öæF†Rf—'7@¦GG&–'WFR–âF†—2&ö¦V7BF†BÔõdU2dU%DU‚&F†W"F†â6—GF–ærVç&VB–âF†R6–FV6"(	BF†P§7GVBÖöGVÆRƒb–â&ÆÆööâÂ#B–â'&6VB’Æ6W2WfW'’÷Væ–ærÂF†R6Æ&ö&B'WGB¦ö–çG2fÆÂöà§7GVBÆ–æW2ÂæB'&6VBg&ÖRvWG2F†Rv—'B&æBB—G2WW"fÆö÷"F†B&ÆÆööâg&ÖR†2æð¦Æ–æRf÷"âÆæ²&—6&R¢¤Ã#2w2÷vâ7FFVB&W6öÇWF–öâ¢¢(	B&’6÷VçBFW&—fVBg&öÒg&öçFvP¦æB&‡—F†ÒF†B6öÖW2g&öÒF†R&ööÒ'&ævVÖVçB(	B6òF†RFVfVÇBg&öçB—27–ÖÖWG&–2æ@§VæWfVæÇ’76VB&F†W"F†âF†R6Vvæ6‚w2f—fR&—2v÷&â'’WfW'’'V–ÆF–ærà ¥7F–ÆÂ÷Vâöâ—BÂæBv÷'F‚&V6÷&Bw2GFVçF–öâ&Vf÷&RF†Rf—'7B†÷W6RÆæG3¢æòF÷&ÖW"‡F†P¦†Æb7F÷&W’—2Æ—BöæÇ’g&öÒF†Rv&ÆRVæG2’Âæòf÷VæFF–öâ÷"6VÆÆ"Âæò×VçF–ç2–âF†R66‚À¦æBF†R7Fö÷&ö¦V7G2÷WG6–FRF†R&V6÷&FVBfö÷G&–çBâÆÂf÷W"&R–âF†R&W÷'BGF6†VBFð§F†R&6VÂæB&VÆöær–âFö72ôÄ”$U%D”U2æÖBF†RF’g&ÖUöGvVÆÆ–æv&V6÷&BFöW2à ¢¢¦÷WF'V–ÆF–ævDôäR##bÓ‚Ó¢¢(	B7F&ÆW2Â6†VG2Â7&–'2Â6Öö¶V†÷W6W2Â&—f–W2â'V–ÇB2¤dÔ”Å’&F†W"F†â6†RÂ&V6W6R6–ævÆR6WBöb&÷÷'F–öç2F†BfÆGFW'2F†RÖ–FFÆRöbF†P§&ævR'&V·2&÷F‚VæG3¢f—fRvöÆFVâf&–çG27âã#RÒ&—g’Fò2Ò†÷FVÂ7F&ÆRÂæ@¦u$õTäEô4ôåD5C¢W&–ÖWFW&—2fW&–f–VBöâÆÂf—fR&F†W"F†âöâöæRâFVÆ–&W&FR'6Væ6W26''¦2×V6‚öbF†RFW6–vâ2F†R&ÖWFW'2(	B7F÷&–W6—2äõB6öç7VÖVBÂ&V6W6RGvò7F÷&W—2öbvÆÂöà¦6V6öæF'’'V–ÆF–ær—26Æ–ÒæBvÆÅö†V–v‡EöÖ—2F†R†öæW7Bv’FòÖ¶R—C²6öç7G'V7F–öæ ¦æÖW2Æör÷Ææ²öÆ–v‡Eög&ÖR&F†W"F†â&ÆÆööâö'&6VBÂ&V6W6Ræ÷F†–ær&V†–æBF†R&ö&G2öb6†V@¦—2f—6–&ÆRBF†—2ÄôBæBæò6÷W&6RFW67&–&W2F†Rg&Ö–æröbç’÷WF'V–ÆF–ær†W&RÂ6òF†P§fö6'VÆ'’æÖW2öæÇ’v†Bf–WvW"6â6VRà ¥GvòF†–æw2—B†æG2Wv&Bâ¢¤Ã6†÷VÆB&Rä%$õtTBÂæ÷B&W6öÇfVB¢£¢F†—2&6†WG—R6â'V–ÆBF†P¥vW7FW&â†÷FVÂw27F&ÆR'WBæ÷B—G2vvöâ–&BÂæB–&B—2âVæ6Æ÷7W&R(	BfVæ6RÆ–æRÂGvð¦vFWv—2ÂG&öFFVâw&÷VæB(	B6ò'V–ÆF–ær—B÷WBöbâ÷WF'V–ÆF–ærv÷VÆB&R6ÆÆ–ærfVæ6R¦'V–ÆF–ærâF†R6ÖRv7vÆÆ÷w2F†RW7G&’VâæB6Ç–&÷W&âw27Fö6·–&BÂæBâVæ6Æ÷7W&V ¦&6†WG—R—2æ÷ræÖVBvçBâæB¢§&Vv—7FW&–ærç’&6†WG—R&W7FÆW2WfW'’6öÖÖ—GFVBtÄ"¢£ ¦ÖW6…ö–çWG2åö6öFU÷6†6†6†W2'V–ÆBç–w2'—FW2f÷"WfW'’&6†WG—RÂæB'V–ÆBç–6'&–W2F†P¦$4„UE•U6&Vv—7G&F–öâF&ÆRÂ6òFF–ær&÷rFò—B6†ævW2F†R†6‚öb'V–ÆF–æw2—BæWfW §F÷V6†VBâGvò&6VÇ2†—BF†—2–æFWVæFVçFÇ’æB&÷F‚fW&–f–VBF†R&RÖ&¶R—2'—FRÖ–FVçF–6ÂâF†P¦f—‚—2Fò7Æ—BF†RW‡÷'BF‚÷WBöb'V–ÆBç–6òF†R&Vv—7G&F–öâF&ÆR7F÷2&V–ærÖW6€¦–çWC²VçF–ÂF†VâöæR&F6†VB&RÖ&¶R6ÆV'2—Bà ¢¢¦g&ÖU÷7F÷&Vg&öçFDôäR##bÓ‚Ó¢¢(	B#26öç7VÖVBGG&–'WFW2ÂÆÂ2Æ—fR7F÷&Vg&öçB&V6÷&G0§&W6öÇf–ærv—F‚æòvVöÖWG'“¦FV6Æ&F–öâ÷vVBâ—B—2F†R&6†WG—Rv†W&R6öç7G'V7F–öæf–æÆÇ§6W&FW2g&öÒg&ÖU÷FfW&æ¢&ÆÆööâg&ÖRvWG2F†–âB–â6÷&æW"&ö&BÂæòv—'BæBb–à¦ÖöGVÆS²'&6VBg&ÖRvWG2b–â6÷&æW"÷7BæBv—'BÆ–æRBF†R6V6öæBfÆö÷"â6ÆFF–æv—0§&VB&F†W"F†â–væ÷&VBÂv†–6‚—2F†RÃ#"FVfV7Bæ÷B&WVFVBâæBF†RVæf–æ—6†VB7FFR—0¦'V–ÆF&ÆR(	B÷Vâ7GVGv÷&²÷fW"’–â&ö&B6†VF†–æröâF†RÆöF–ærv&ÆRÂGFW7FVB–â¶–æB'¤æG&V2f÷"F†R¤6†–6vòFVÖö7&B¢w2÷vâ'V–ÆF–ærB6÷WF‚vFW"æB6Æ&²Â'Væf–æ—6†VBBF†P§F–ÖR"–âæ÷fVÖ&W"ƒ32âæWfW"FVfVÇBà ¢222F‡&VR'Vw2—Bf÷VæB–âæV–v†&÷W&–ær6öFR(	BäõBf—†VBÂæBF†RF†—&B—2vFR†öÆP £â¢¦ÖW6„'V–ÆFW"æFEöv&ÆU÷&ööff–ÆÇ2V6‚v&ÆRVæBv—F‚6öÆ–BG&–ævÆRã#RÒõUD$ô$Bö`¢F†RvÆÂâ¢¢6òç—F†–ærG&vâöâv&ÆRBF†RvÆÂÆæR—2¦–ç6–FR¢F†R&ööbæB–çf—6–&ÆRà¢ÆöuöGvVÆÆ–æråöÆögEö÷Væ–ævFöW2W†7FÇ’F†—3¢—G2ÆögB÷Væ–æw2&Ræ÷B–âF†R6öÖÖ—GFV@¢&VfW&Væ6R–ÖvRæBæWfW"vW&RâvVæW&F÷"F†B6–ÆVçFÇ’7vÆÆ÷w2—G2÷vâ÷WGWB—2F†Rv÷'7@¢¶–æBöb'Vr†W&RÂ&V6W6RF†R&VfW&Væ6R&VæFW"—2v†B&Wf–WvW"6†V6·2à£"â¢¦ÆöuöGvVÆÆ–ævw2&¶VBtÄ"†2•öÖ–âÒÓãcV¢¢v†–ÆRFV6Æ&–æru$õTäEô4ôåD5C ¢W&–ÖWFW&(	Bâ÷Væ–ær7W'&÷VæB&VÆ÷rw&FRâF†R6ÖR'Vrv2f÷VæBæB6Æ×VB–ç6–FP¢g&ÖU÷7F÷&Vg&öçF²F†—2öæR—2Æ—fR–âF†R6öÖÖ—GFVB76WBÂ6ò&V6÷&B—2Ö¶–ærfÇ6P¢w&÷VæBÖ6öçF7B6Æ–Ò&–v‡Bæ÷rà£2â¢¦g&ÖU÷FfW&æFV6Æ&W26öç7G'V7F–öææBvÆÆW'––â4ôå5TÔTBæB'V–ÆG2æV—F†W"¢¢(	@¢æBFW7Eö6öç7VÖVEöGG&–'WFW5ö7GVÆÇ•÷&V6…÷F†U÷&ÖWFW'654U2Â&V6W6R—BöæÇ’&WV—&W0¢F†R&W6öÇfVB§&ÖWFW'2¢FòÖ÷fRÂæ÷BF†RvVöÖWG'’âFöF’WfW'’&V6÷&B6—2vÆÆW'“¢fÇ6VÀ¢6òF†RfÇ7’'VÆR†–FW2—C²¢§F†Rf—'7B&V6÷&BF†B6—2G'VVvWG2W†7W6VBg&öÒ¢vVöÖWG'“¦FV6Æ&F–öâf÷"vÆÆW'’F†B—2æWfW"'V–ÇBâ¢¢F†B—2F†RW†7Bf–ÇW&RF†P¢4ôå5TÔTB6öçG&7BW†—7G2Fò&WfVçBÂ6—GF–ær–ç6–FRF†RFW7BF†B—27W÷6VBFòVæf÷&6R—Bà¢f—†–ær—BÖVç2F†RFW7B†2Fò6ö×&RfW'F–6W2Âæ÷B&ÖWFW'2à ¢223R(	B7G'V7GW&R&V6÷&G0 ¢¢¥VWVVBf—'7BÂæB—B—2&Vw&FR&F†W"F†ââFF—F–öã¢#Fö7VÖVçFVFfÇVW2&W7Böà¦ÆFW"66†öÆ'6†—ÆöæR¢¢ƒ##bÓ‚ÓÂ5DEU2*rC2’âF†RWf–FVæ6RÆFFW"†2vFRæ÷rÂæB—G0¦f÷W'F‚'VÆR—26÷VçFVBv&æ–ær&F†W"F†ââW'&÷#¢Fö7VÖVçFVFfÇVRv—F‚æò6÷W&6R@§F–W"2÷"&WGFW"(	BæòW&–öBFö7VÖVçBÂæòW–Wv—FæW72&V6öÆÆV7F–öâÂæò6ö×–ÆF–öâg&öÒ–öæVW §FW7F–Ööç’(	B—2V—F†W"â÷fW"Öw&FVBfÇVR÷"âVæFW"×F–W&VB6÷W&6RÂæBöæÇ’&VF–ærF†RvP§6WGFÆW2v†–6‚à ¢¢¥F†R6÷W&6R†Æb—2DôäR##bÓ‚ÓæB—Bv2f–gFVVâöbF†RGvVçG’ÖöæR¢¢…5DEU2*rCBÀ¦Fö72õ$U4T$4‚öWf–FVæ6U÷F–W'5ö6†–6vöÆöw’æÖF’â&Vf—&S#vÂ&Vf—&S#s6æB&Vf—&S#s†vW&P¦fWF6†VBæB&VB–âgVÆÃ²ÆÂF‡&VRG&ç67&–&RæV"×&–Ö'’&V6öÆÆV7F–öâ(	BF†R¤–çFW"ö6Vâ ¦öÆB×6WGFÆW"–çFW'f–Ww2öbæB#"§VÇ’ƒƒ2ÂæBF†R¤6†–6vòÖv¦–æR¢öbRÖ’ƒSr'V–ÇBöà¤‡V&&&Bw2÷vâ66÷VçB(	BæBÆÂF‡&VRvW&Rw&FVBBâF†W’&R"ÂæòfÇVRÖ÷fVBÂæòÖW6‚vVç@§7FÆRÂæBF†R6÷VçB&VG2¢§6—‚¢¢âF†R§VFvVÖVçB—2Ç6òFV6Æ&F–öâæ÷r&F†W"F†âG—V@¦çVÖ&W#¢&V6÷&BFF–ær—G2÷vâ&WG&–WfÂæB6Æ–Ö–ærFW7F–Ööç’'Vær×W7BFV6Æ&P¦G&ç67&–&W6ÂæB—G2F–W"—2F†R&W7B'Vær—BFV6Æ&W2à ¢¢¥F†Rf÷W"6†'öæW2&Rv†B—2ÆVgBÂæBF†W’&RF†RW‡Vç6—fR†Æb¢£¢6Vvæ6…ö†÷FVÆ ¦f÷&Òç7F÷&–W6æBf÷&Òæ6öç7G'V7F–öæÂÖ–ÆÆW%ö†÷W6Vf÷&Òæg&ÖUöFF—F–öå÷7F÷&–W6æ@¦vöÆe÷ö–çE÷FfW&æf÷&Òç6–væ&R7W÷'FVB'’æ÷F†–ær'WBF†RGvòG&Æö–†&Æör6ö×–ÆF–öç2À§v†÷6R÷vâ6÷W&6R&V6÷&G26’¦æWfW"26öÆRWf–FVæ6R¢â&R×F–W&–ær6ææ÷BF÷V6‚F†VÒ(	BF†RvW0¦&RVæfö÷Fæ÷FVBÂ×WGVÆÇ’6öçG&F–7F÷'’æBVæ&6†—fVB(	B6òF†—2—2&Vw&FRöbF†RdÅTRÂæ@¦6öæf–FVæ6R—2ÖW6‚–çWC¢F†R6Æ–6R7FÆW2F†÷6RtÄ'2æBÆæG2v—F‚&¶Râ&V†–æB—BÂF†P¦Ö6†–æR×&VF&ÆR†Æb(	BæWfW%÷6öÆUöWf–FVæ6VfÆröâ6÷W&6R&V6÷&BÂv†–6‚GW&ç2F†÷6Rf÷W ¦–çFòW'&÷'2(	B7F—2FVÆ–&W&FVÇ’&V†–æBF†R&Vw&FRÂ&V6W6RvFRF†Bf–Ç2F†R6öÖÖ—GFV@¦FF6WBöâF†RF’—BÆæG2—2vFRF†BvWG27v—F6†VBöfbà ¢¢¥F†R÷F†W"Gvò&R÷WG6–FRF†R'V–ÆF–æw2¢£¢w&÷VæB7W&f6UöÖFW&–Ç2ç6÷WF…öF—f—6–öæ ¢†6†–6võö&6†—FV7GW&Uö†—7F÷'•óV’æBw&÷VæBvFW&†v–¶—VF–ö6†–6võ÷&—fW&’âçåF†Rf—'7@¦öbF†÷6R†2æ÷B&VVâ÷VæVBççâ¢¤&÷F‚&R&VBæB&÷F‚&R÷fW"Öw&FVBdÅTU2¢¢(	BvFW&öà£##bÓ‚ÓŒ*rCbÂFö72õ$U4T$4‚÷7vV&–ævVåóƒ2æÖF’æBF†R6ö–Â&öf–ÆRF†R6ÖRF¢…5DEU2*rSÂFö72õ$U4T$4‚÷7W&f6UöÖFW&–Ç5÷6÷WF…öF—f—6–öâæÖF’âF†R6ö–ÂvR—2##"W76§F†B—2—G2÷vâFö7VÖVçBÂ6÷'&V7FÇ’B'VærBÂæB—B&–çG2¢¦æòfö÷Fæ÷FRÂVæFæ÷FR÷"&VfW&Væ6P¦ç—v†W&R–â—B¢£²F†RöæRv—FæW72öâ—B(	B¦ö†âÖ–ÆÇ2fâ÷6FVÂÂ&Æö6²×V÷FVBv—F‚æòV&Æ–6F–öâÀ¦FFR÷"vRÂæBVæÖVçF–öæVB'’F†—2&ö¦V7Bw2÷vâF÷76–W"(	BGFW7G2F†Rõ$DU"öbF†R7G&Fæ@§F†RG&–ævRf–ÇW&RæBv—fW2¢¦æò&Æ6²ÆöÒæBæ÷BöæRF†–6¶æW72¢¢Â6òF†RF‡&VRf–wW&W2–à§F†R6Æ–Ò†fRæö&öG’&V†–æBF†VÒâFö7VÖVçFVF(i"–æfW'&VFÂæB—BÆæG2v—F‚F†R&¶Rà ¢¢¥F†RF‡&VRvW2F†BÆöö¶VBÆ–¶RF†R6ÖR66RvW&R÷VæVB##bÓ‚Ó¢¢…5DEU2*rCRÀ¦Fö72õ$U4T$4‚öWf–FVæ6U÷F–W'5÷&÷VæE÷GvòæÖF’ÂæBGvòöbF†VÒvW&Râ&Vf—&Sc&&W&–çG0¢¢¤æG&V2¢¢Âv†òV÷FW2F†R¤6†–6vòÖW&–6â¢öb’§VÇ’¢£ƒ3b¢¢†æ÷Bƒ3R’f÷"F†RÆ¶Ræ@¤Æ6ÆÆRg&öröæB(	BF–W"2ÂöâæG&V2æBFVÆ–&W&FVÇ’æ÷BöâF†RæWw7W"æö&öG’†W&R†0¦÷VæVBâ&Vf—&S#sf&W&–çG2F†R¤6†–6vòÖv¦–æR¢öbRÖ’ƒSrÂF†R6ÖRFö7VÖVçBæBF†P§6ÖR&VF–ær2&Vf—&S#s6(	BF–W""Âv—F‚F†RƒSb¥G&–'VæR¢æ÷F–6R&W6–FR—BÆVgBVæFV6Æ&V@¦&V6W6Ræò6Æ–Ò†W&R&W7G2öâ—BâæV—F†W"vR—26—FVB'’ç—F†–ærFöF’Â6òF†RÆFFW"6÷Vç@§7F—2B6—ƒ²&÷F‚&RVWVVB&W6V&6‚…3"&6VÂ†2’w2öæBÂæBF†Rf÷'B’F†B6âæ÷r&P¦w&FVB†öæW7FÇ’v†Vâ—B—2w&—GFVâà ¢¢¦v–¶—VF–ö6†–6võ÷&—fW&v2äõBF†R66RÂæBF†B—2F†Rf–æF–ærv—F‚6öç6WVVæ6Râ¢¢—@§&W&–çG2æ÷F†–ær(	BöæR6VçFVæ6RöbVæ7–6Æ÷VF–&÷6R&‡&6–ær7vV&–ævVâv—F‚fö÷Fæ÷FRFð¢¢¥V–fR“2Ââ3s2Ó3sr¢¢Âv†–6‚—2F†R&–Ö'’&–çF–ærF†R&V6÷&B†26¶VBf÷"6–æ6R—Bv0§w&—GFVââGvòF†–æw26öÖRöfb—C  §ÂVWVVBÂv†B—B6÷7G2À§ÂÒÒ×ÂÒÒ×À§ÂçäfWF6‚V–fR“2â3s2Ó3sræB&V6÷&B7vV&–ævVâw2ƒ26÷VæF–æw2BF†V—"÷vâ'VæwçâÂ¢¤DôäR##bÓ‚Ó¢¢(	BV–fUó“5÷7vV&–ævVæÂF†RFF6WBw2f—'7BF–W"Ów&—GFVâW–Wv—FæW72Fö7VÖVçC²ÖVÖòFö72õ$U4T$4‚÷7vV&–ævVåóƒ2æÖFâæB¢§F†R&–6R&÷fRv2w&öær¢£¢vVæW&F÷'2÷FW'&–åö–çWG2ç–7G&—26÷W&6W6g&öÒF†RFW'&–â†6‚Æöærv—F‚F†R&÷6RÂ6ò6—F–ær—Bg&öÒFW'&–å÷7V2æ§6öæ6÷7Bæ÷F†–æræBv2FöæR–âF†R6ÖR6Æ–6Râ6öæf–FVæ6V—2F†RÖW6‚–çWBÂæ÷B6—FF–öâÀ§Â¢¦w&÷VæBvFW&¢Fö7VÖVçFVF(i"–æfW'&VF¢¢(	BF†RfÆB7W&f6R&W7G2öââVæfö÷Fæ÷FVBVæ7–6Æ÷VF–6VçFVæ6R&÷WB6ÇVvv—6‚fÆ÷rÂæ÷Böâ7vV&–ævVâÂv†òv—fW2æòw&F–VçBæBÖV7W&W2ã"Ö–ÆW2F÷vç7G&VÒÂ6öæf–FVæ6R—2ÖW6‚–çWC¢—B7FÆW2F†Rw&÷VæBæBÆæG2v—F‚—G2&ÆVæFW"&¶RÂW†7FÇ’Æ–¶RF†Rf÷W"G&Æö–†fÇVW2â¢¤&WGFW"&wVVB2öb##bÓ‚ÓæBVæ6†ævVB–âF—&V7F–öâ¢£¢&VF–ær7vV&–ævVâÖFRF†R66R7G&öævW"&F†W"F†â&W67V–ær—BÂ&V6W6R†—2vFVBvFW"r—2GG&–'WFVB–âF†R6ÖR6ÆW6RFòÖ÷WF‚7F÷VB'’6æB(	BF†RSƒ3öæGW&Æ6öæF—F–öâF†Rƒ3B7WB&VÖ÷fVBâ†R—2FVÆ–&W&FVÇ’äõB6—FVBöâF†RvFW"ÆæS²F†R&Æö6²w2æ÷FR6—26òv†W&Rf—6—F÷"&VG2—BÀ ¥F†B—2F†R¢¦f—'7BöbF†R6—‚v&æ–æw26WGFÆVB–âF†R÷fW"Öw&FVBF—&V7F–öâ¢¢(	BF†R6÷W&6R—0¦6÷'&V7FÇ’F–W&VBæBF†RfÇVR—2æ÷Bà ¢¢¤æBF†R&–Ö'’&–çF–ær'&—fVB##bÓ‚ÓÂv†–6‚6÷7BF†RVæ7–6Æ÷VF–öæRöb—G2Gvò&æ°¦f–wW&W2¢¢…5DEU2*rCbÂFö72õ$U4T$4‚÷7vV&–ævVåóƒ2æÖF’âV–fRw2VæF—‚’—2æ÷p¦V–fUó“5÷7vV&–ævVæBF–W"Â&VBg&öÒGvò–çFW&æWB&6†—fR66ç2F†Bw&VR6†&7FW ¦f÷"6†&7FW"âv–¶—VF–w2¢#bgBöâF†Ræ÷'F‚"¢—2æ÷v†W&R–âF†R¦÷W&æÃ¢7vV&–ævVâv—fW2æð¦æ÷'F‚Ö&æ²†V–v‡BÂöæÇ’&÷VæFVBF–ffW&Væ6RfÆvvVB2ÖFR¦'’V&æ6W2¢ÂæBb—2v†B¦ÆFW"w&—FW"v÷B'’7V'G&7F–ærF†RÖ†–×VÒg&öÒ‚âv†BF†R&‡&6RG&÷VBÖGFW'2Ö÷&R(	@¢¢'F†R&æ·2&÷fR&RV—FRÆ÷r"¢—2F†RöæÇ’6VçFVæ6R–âF†R76vR&÷WBF†R&V6‚F†—0§&ö¦V7BÖöFVÇ2ÂæB—B—2GF6†VBFòF†R7V2w2&æ¶&Æö6²æ÷rÂv†–6‚6—FVBæ÷F†–ær&Vf÷&Rà¤f÷W'F‚6—FF–öâf÷VæBÖ—6FW67&–&–ær—G2÷vâvRÂæBF†Rf—'7Bf÷VæB'’÷Væ–ærF†RFö7VÖVç@§&F†W"F†âF†R†÷7Bâçå6—‚vW2BF–W"B÷"vV¶W"7F–ÆÂFV6Æ&Ræ÷F†–æp¢†6†–6võ÷FV×ÆUö†—7F÷'–Â6†–6vöÆöw•öf—'7E÷÷7Eööff–6VÂ6†–6vöÆöw•öÆ7Gv&Fæ6VÀ¦6†–6vöÆöw•÷&Vf—&S#sFÂG&Æö–…ö†÷FVÇ6ÂG&Æö–…÷vöÆe÷ö–çF’Â6÷VçFVB'’F†RfÆ–FF÷"WfW'§'VâÂæBF†RGvòG&Æö–†vW2&Ræ÷B6öÇf&ÆRF†—2v’ççà ¢¢¥F†Rf÷W"F†B6÷VÆB&R÷VæVBvW&R÷VæVB##bÓ‚ÓÂæBF†R6÷VçB&VG2Gvò¢¢…5DEU2*rCrÀ¦Fö72õ$U4T$4‚öWf–FVæ6U÷F–W'5÷&÷VæE÷F‡&VRæÖF’â6†–6vöÆöw•öÆ7Gv&Fæ6V—2F†R¤6†–6vð¥G&–'VæR¢öbBVwW7B“&–çF–ær¢¤¦ö†âFVâ6Föâw2÷vâw&—GFVâ&V6öÆÆV7F–öâ¢¢(	Bà¦–FVçF–f–VBW–Wv—FæW72Âæ÷BF†R&ÆFW"6ö×–ÆF–öâöb&V6öÆÆV7F–öç2"F†R&V6÷&B6Æ–ÖVB(	BæB—0§'Vær"â6†–6vöÆöw•÷&Vf—&S#sF—2¤6†–6vòÖv¦–æR¢ÂÖ&6‚ƒSrÂF†R–ç7FÆÆÖVçB&Vf÷&P¦&Vf—&S#sfÂæB—2F†Rf—'7B6÷W&6R†W&Rw&FVB¢¦'’v†–6‚'Böb—B–÷R7FæBöâ¢£¢'Vær ¦f÷"F†RÆæFf÷&ÒF†—2&ö¦V7B6—FW2Âæò&WGFW"F†â2f÷"—G2ƒ2Óƒ"f÷'Bæ'&F—fRÂv†–6€¦æ÷F†–ær6—FW2â6†–6vöÆöw•öf—'7E÷÷7Eööff–6Vv2&VBæB¢¦ÆVgBBB¢¢(	B7W'&W’“#"æÖ–æp¦æòWF†÷&—G’f÷"F†R÷7BÖöff–6Rf7G2(	Bv†–6‚—2v†BF†—26V7F–öâÖVçB'’§Vç&VB&F†W"F†à§w&öær¢â6†–6võ÷FV×ÆUö†—7F÷'–&W&–çG2æ÷F†–æræB6—26ò–â6'&–W5öæõöFö7VÖVçF²—G0¦Ö—76–ær&6†—fVE÷W&Æ—2f–ÆÆVBg&öÒ##bÓbÓR6æ6†÷BfW&–f–VBv–ç7B&÷F‚V÷FF–öç2À¦öæR7FæF–ærv&æ–ærvöæRà ¢¢¥F†Rf–æF–ær—2öâF†R÷7BÖöff–6RvRæB—BF÷V6†W23’â¢¢F†RcbgB7G&VWBÖöGVÆR(	BF†P¦F—76VçBv–ç7BF†RƒgBWfW'’ÆGFVBÆ6VÖVçB—2öfg6WBg&öÒ(	B—2¦æ÷B'Böb7W'&W’w0¦'F–6ÆR£¢—B–çFW''WG2†—26‡&öæöÆöw’Â—G27V&¦V7B—27W'fW’–ââ'F–6ÆR&÷WB'V–ÆF–æw2À¦æB—B—2F†RöæR&w&‚æÖ–æræòWF†÷&—G’v†–ÆRw&—F–ær&F÷vç7FFR&æFöÇ‚6÷VçG’"â—B—0§VæFV6Æ&VBÂöfbF†RÆFFW"ÂæBFF÷G&6W2÷7G&VWEö6öçG&öÂæ§6öææòÆöævW"6—2$7W'&W’7FFW2"à¤æòçVÖ&W"Ö÷fW2(	BF†Rf–wW&Rv2Ç&VG’W†6ÇVFVB'’ÖV7W&VÖVçB(	B'WBF†RF—76VçB—2æ÷r§6÷W&6VÆW72vV'6—FR6VçFVæ6R&F†W"F†âæÖVB†—7F÷&–âÂv†–6‚—2F–ffW&VçBF†–ærf÷"F†P§7G&VWG2&6VÂFòvV–v‚à ¢¢¥v†B—2ÆVgBöbF†—2F‡&VB—2æ÷B&W6V&6‚ÂæB2öb##bÓ‚ÓF†B—2G'VRöbÆÂ6—‚â¢ ¤öæÇ’G&Æö–…ö†÷FVÇ6æBG&Æö–…÷vöÆe÷ö–çF7F–ÆÂFV6Æ&Ræ÷F†–ærÂæBF†—2ÖWF†öBFöW2æ÷B&V6€§F†VÓ¢F†RvW2&RVæfö÷Fæ÷FVBÂ×WGVÆÇ’6öçG&F–7F÷'’æBVæ&6†—fVBÂæBF†V—"f÷W"fÇVW2æVV@§F†RdÅTR&Vw&FVBÂv†–6‚—2ÖW6‚–çWBâ¢¥F†B6Æ–6RÂw&÷VæBvFW&æBw&÷Væ@¦7W&f6UöÖFW&–Ç2ç6÷WF…öF—f—6–öæ&RöæR&¶R¢¢(	Bf—fRfÇVW2Â6—‚v&æ–æw2ÂF¶RF†VÒFövWF†W ¦öâ'VææW"v—F‚&ÆVæFW"âWfW'’vR&V†–æBF†R6—‚†2æ÷r&VVâ÷VæVBæBF†RfW&F–7BöâWfW'¦öæRöbF†VÒ—2F†R6ÖS¢F†R6÷W&6R—2F–W&VB6÷'&V7FÇ’æBF†RfÇVR—2w&FVBFöò†–v‚à  ¢¢¥F†R&W—"VWVRF†B6ÖR&Vf÷&R—BÂÆÂöb—BDôäR(	BF‡&VRGG&–'WFW2F†BvW&R&V6÷&FV@¦æBVæ'V–ÇBâ¢¢f÷VæB'’F†RöÖ—76–öâvFRöâ##bÓ‚ÓæBFÖ—GFVBÖVçv†–ÆR'’Ã#æBÃ#à §Â&V6÷&BÂGG&–'WFRÂv†BF†R&6†WG—R&VG2ÂVffV7BÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§ÂçævöÆe÷ö–çE÷FfW&æçâÂçæg&ÖUöW‡FVç6–öæçâÂg&ÖUöFF—F–öæÂ¢¤DôäR##bÓ‚Ó¢¢(	B&VæÖVBÂF–ÖVç6–öæVBæB&RÖ&¶VB–âöæR6Æ–6RÀ§ÂçævöÆe÷ö–çE÷FfW&æçâÂçæ6–vævVçâÂ6–væÂ¢¤DôäR##bÓ‚Ó¢¢(	BF†R&ö&B†æw2öâF†R&—fW"g&öçC²F†RvöÆb—2æ÷BG&vâ„Ã#R’À§ÂçæÖ–ÆÆW%ö†÷W6VçâÂçæ6†–ÖæW—3¢&çâÂ6†–ÖæW–†&ööÆVâ’Â¢¤DôäR##bÓ‚Ó¢¢(	BF†R6÷VçB—2&ÖWFW"öb&÷F‚&6†WG—W3²F†R6V6öæB7F6²7FæG2öâF†Rg&ÖR&ævRÀ ¢¢¥F†RöæR&W—"f÷VæB'’&VF–ær&F†W"F†â'’vFR—2DôäR¢¢ƒ##bÓ‚ÓÂ5DEU2*r#2(i"*r#B“  §Â&V6÷&BÂGG&–'WFRÂv†BF†RWf–FVæ6R6—2ÂVffV7BÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§Âçææ÷'F…ö'&æ6…ö'&–FvVçâÂçæ–W%÷76–æuöÖçâƒR7&–'2BF†R&6†WG—RFVfVÇB’Â¢§Gvò&&VçG2"öbf÷W"†Vg’Æöw2&W7F–æröâF†R&÷GFöÒ¢¢Â¢¤DôäR¢¢(	B–W%ö6÷VçC¢&&WÆ6W2F†R76–ær–â&V6÷&BæB&6†WG—S²Ã#’&W6öÇfVBÂÃ3æWrÀ§Âçææ÷'F…ö'&æ6…ö'&–FvVçâÂçæ–W%ö¶–æC¢7&–&çâÂF†R6WGFÆW'2r÷vâv÷&B—2¢¦&VçG2¢¢(	BæB6ÆVfW"6–væVB—BÂ¢¤DôäR¢¢(	B&VçF&W6–FR7&–&æB–ÆV²f÷W"†Vg’Æöw2VæFW"6À§Âçææ÷'F…ö'&æ6…ö'&–FvVçâÂçæ6ÆV&æ6UöÖçâ†–æfW'&VFÂvRæ÷Bf÷VæB’Â¢¢&&÷WB6—‚fVWB&÷fRF†RvFW"Â6òF†BFV×276VBVæFW"F†VÒöâF†R–6Rg&VVÇ’"¢¢Â¢¤DôäR¢¢(	BFö7VÖVçFVFöâöÆE÷6WGFÆW'5ö'&–FvW5óƒƒ6²F†RFV6²æB7G&–ævW'26öÖR÷WBöbF—F†W&–ærÀ§Âçææ÷'F…ö'&æ6…ö'&–FvVçâÂçæFV6·çâ†&6†WG—Rw2ÂVç7FFVB’Â¢¢'Væ6†Vöç2÷"7Æ—BÆöw2vW&RÆ–Bf÷"fÆö÷""¢¢Â¢¤DôäR¢¢(	BFV6µö¶–æC¢Væ6†VöæÂfÇVRF†RvVæW&F÷"&VG2À ¤ÆÂf÷W"vW&RÖW6‚–çWG2Â6òF†R&V6÷&BÂF†R&6†WG—R6†ævRæBF†R&¶RÆæFVB2öæR6Æ–6R(	@§F†R6ÖR6÷WÆ–ærF†Ræ÷FR&VÆ÷rFW67&–&W2Â'&—f–ærg&öÒæWrF—&V7F–öââF†RWf–FVæ6R—2§6–væVBƒƒ27FFVÖVçB'’f÷W"ÖVâv†òW6VBF†R'&–FvRÂ&–çFVB2fö÷Fæ÷FRBæG&V0§âc3Óc3"æBÖ—76VB'’F†RgVÆÂ×FW‡B–æFWƒ²6VRFö72õ$U4T$4‚öæ÷'F…ö'&æ6…ö'&–FvRæÖF*rbà ¢¢¥F†RÆW76öâ—2&÷WBF†R&ÖWFW"Âæ÷BF†RçVÖ&W"â¢¢'&–FvU÷F–Ö&W&F—f–FVB7â'’§76–ærÂ6ò—B6÷VÆBöæÇ’WfW"&öGV6R6öÆöææFS²æò6÷W&6Rv–ÆÂWfW"7FFR76–ærÂæBv†@¦v—FæW72&VÖVÖ&W'2—26÷VçBæBf÷&Òâ6WGF–ærBãRÒFò#2ã“BÒv÷VÆB†fRf—†VBF†—2'&–FvP¦æBÆVgBF†RæW‡BöæRFò&Rf÷VæB'’F†R6ÖR66–FVçBâv÷'F‚6¶–æröbç’&6†WG—Rv†÷6P¦FVfVÇG2&R&÷WBFò&R÷fW'&–FFVã¢—2—B6¶–ærf÷"F†R¶–æBöbçVÖ&W"6÷W&6R6÷VÆB6öçF–ãð¥v†BF†R&W—"6÷VÆBæ÷B6WGFÆR—2v†W&RÆöærF†R7âF†RGvò&VçG27FööB(	BF†RÆWGFW"Æö6FW0§F†VÒ'’FWF‚Â–â&—fW"v†÷6R&VBF†—2&ö¦V7BFöW2æ÷BÖöFVÂ(	B6òF†W’6—BBF†RF†—&Bö–çG0¦æB¢¤Ã3¢¢FÖ—G2—BÂFövWF†W"v—F‚F†R7Æ–6W2–âF‡&VR#2ã’Ò7G&–ævW"'Vç2F†Bæò6÷W&6P§Æ6W2à ¤V6‚öbF†RV&Æ–W"&W—'2v26ÖÆÂFFVF—BÇW2&RÖ&¶RÂ6ò¢§&V6÷&BæBvVöÖWG'’ÆæFVB–âöæR6Æ–6R¢¢(	BF†P§6ÖR6÷WÆ–ærF†Ræ÷FR&VÆ÷rFW67&–&W2âÆÂF‡&VR&RFöæRà ¢¢¥F†RÆ—7B&Vf–ÆÇ2—G6VÆbÂv†–6‚—2F†Rö–çBöbF†RvFRâ¢¢Ö¶–ærF†R6†–ÖæW’6÷VçB&VÀ§&WV—&VBÆ6–ærÖ–ÆÆW"w26V6öæB7F6²ÂæBÆ6–ær—BW‡÷6VBF†RæW‡B&W—"öbW†7FÇ’F†P§6ÖR¶–æC  §Â&V6÷&BÂGG&–'WFRÂv†BF†R&6†WG—RFöW2ÂVffV7BÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×ÂÒÒ×À§ÂçæÖ–ÆÆW%ö†÷W6VçâÂçæg&ÖUöFF—F–öæ†Fö7VÖVçFVBÂVæF–ÖVç6–öæVB—çâÂ–6·26–FRÂv–GF‚ÂFWF‚æB7F÷&W’6÷VçBg&öÒ—G2FVfVÇG2Â¢¤DôäR##bÓ‚Ó¢¢(	BF†R&V6÷&B7FFW2ÆÂf—fRÂF†RGvò–çfVçFVBöæW2&RÃ#rÂ&RÖ&¶VB–âF†R6Æ–6RÀ ¥F†Bv2Ã#Bw2FVfV7BöæR'V–ÆF–ær÷fW"ÂæB—B6ÖRv—F‚6V6öæBöæRVæFW&æVF‚—BF†Bv0¦æ÷Böâç’Æ—7Bâ¢¦7F÷&–W3¢"ÂFö7VÖVçFVFv2F†Rg&ÖR&ævRw2æBÆöuöGvVÆÆ–æv&VG2—B0§F†RÆör6÷&Rw2¢¢Â6òF†RFö7VÖVçFVB6Æ–Òv27VçBöâF†R6&–âÂF†R&ævRFöö²BãrÒFVfVÇBÀ¦æBF†RÖöFVÂ7FööBGvò×7F÷&W’Æör6&–â&V†–æB6†÷'FW"g&ÖR&Æö6²(	BF†R6ö×÷6—F–öà¦–çfW'FVBâF†R&V6÷&Bæ÷r6W&FW2F†VÓ¢g&ÖUöFF—F–öå÷7F÷&–W3¢&Fö7VÖVçFVBÂ7F÷&–W3¢ ¦–æfW'&VBf÷"F†R6&–âÂg&ÖUöFF—F–öåö†V–v‡EöÓ¢Rã&æBvÆÅö†V–v‡EöÓ¢"ãfâGvòöbF†Rf÷W §VWVVBGG&–'WFW2GW&æVB÷WBFò&RGFW7FVB&F†W"F†â–çfVçFVB(	BF†R6–FRÂ&V6W6RF†R6÷W&6P§6—2¦g&öçF–ærF†R&—fW"¢ÂæBF†R7F÷&W’6÷VçB(	BæBöæÇ’F†Rv–GF‚æBFWF‚&RwVW76W2ÂF¶Và¦öfbF†R&V6÷&Bw2÷vâfö÷G&–çBÆ–Ö"ƒ’9rbÒ’&F†W"F†â–6¶VBg&W6‚âÃ2Ö÷fW2Fò&W6öÇfVBÀ¤Ã#r—2æWrâ¢¥F†R&W—"VWVR—2V×G’æBæ÷F†–ær&Vf–ÆÆVB—C¢3R—2FF—F–öç2v–ââ¢  ¥F†RÆW76öâv÷'F‚6''––ær7BF†—2F&ÆS¢F†RöÖ—76–öâvFRf÷VæBF‡&VRÖ—77VÆÆ–æw2æBF†P¦f÷W'F‚fVÇBv2æ÷BöæRâ7F÷&–W6v2æÖRF†R&6†WG—R¦f÷VæB¢æB&VB2&V–ær&÷WBF†P¦÷F†W"†ÆböbGvò×'B'V–ÆF–ær(	Bv†–6‚—2–çf—6–&ÆRFò7VÆÆ–ær6†V6²æBFð¦FW7Eö6öç7VÖVEöGG&–'WFW5ö7GVÆÇ•÷&V6…÷F†U÷&ÖWFW'6Â6–æ6RF†RfÇVRFöW2Ö÷fRvVöÖWG'’À¦§W7BF†Rw&öærvVöÖWG'’âç’&6†WG—RGG&–'WFRF†BÖVç2F–ffW&VçBF†–æw2FòF–ffW&Vç@¦VÆVÖVçG2öb6ö×÷6—FR'V–ÆF–ær—2F†R6ÖRG&²vÆÅö†V–v‡EöÖv2F†R6V6öæBöæR–âF†—0§&V6÷&Bà ¢¢¥F†RvöÆbö–çB—"ÆæFVBFövWF†W"Âv†–6‚—2F†R6†R¢¢ƒ##bÓ‚Ó’â&÷F‚&VæÖW2ÂF†Rf÷W ¦GG&–'WFW2F†Rg&ÖR&’æVVFVBÂF†R&RÖ&¶RÂF†RV&Æ—6‚æBF†RÆ–&W'F–W2Ö÷fVB–âöæR"âGvð§F†–æw2&Rv÷'F‚6''––ærf÷'v&Bâf—'7BÂ&VæÖR—2æWfW"öæÇ’&VæÖS¢g&ÖUöFF—F–öã¢G'VV ¦ÆöæRv÷VÆB†fRÆWBF†R&6†WG—R6†ö÷6RF†R&’w26–FRÂv–GF‚ÂFWF‚æB7F÷&W’6÷VçBg&öÒ—G0¦FVfVÇG2Â6òFö7VÖVçFVBfVGW&Rv÷VÆB†fR'&—fVBBâ–çfVçFVB6—¦Rv—F‚æ÷F†–ærFÖ—GF–æp¦—B(	BF†R&V6÷&Bæ÷r7FFW2ÆÂf÷W"æBÃ#BFÖ—G2F†RF‡&VRF†B&R6öæ¦V7GW&Ââ6V6öæBÂF†P§7FÆVæW72vFRF–BW†7FÇ’v†B—Bv2w&—GFVâf÷#¢F†R&V6÷&BVF—BGW&æVBF†RFfW&âw2tÄ"5DÄP¦öâF†R7÷BæBF†R6öÖÖ—B6÷VÆBæ÷Bvòw&VVâVçF–ÂF†R&¶RÆæFVBv—F‚—Bà ¢¢¤æBF†R6÷VçBöbF†–ær—2æ÷BF†RF†–ær¢¢ƒ##bÓ‚Ó’â6†–ÖæW—6v27FFVB'’WfW'’&V6÷&@¦æB&VB'’æV—F†W"&6†WG—S¢g&ÖU÷FfW&æ'V–ÇBGvò7F6·2æBÆöuöGvVÆÆ–æv'V–ÇBöæRÀ§v†FWfW"F†RçVÖ&W"6–Bâ&÷F‚F¶RF†R6÷VçBæ÷rÂæBF†Rg&ÖR—"¶VW2—G2W†7B÷6—F–öç26ð§F†B&ÖWFW&—6–ærçVÖ&W"F–Bæ÷BÖ÷fR'V–ÆF–ærv†÷6R6÷VçBv2Ç&VG’&–v‡BâF†P¦ÆöuöGvVÆÆ–æv†Æbv2F†Rg&ÖUöW‡FVç6–öæö6–vævVf–ÇW&RF†—&BF–ÖR(	BF†R&ÖWFW"v0¦6†–ÖæW–æBæò&V6÷&B†2WfW"6öçF–æVBF†Bv÷&B(	B6òF†R6Æ72†26†V6²æ÷r&F†W"F†à¦æ÷F†W"F—66÷fW&W#¢FW7Eö6öç7VÖVEöGG&–'WFW5ö7GVÆÇ•÷&V6…÷F†U÷&ÖWFW'6W'GW&'2WfW'’7FFV@§fÇVRâ&6†WG—RFV6Æ&W2—B6öç7VÖW2æB&WV—&W2F†R&W6öÇfVB&ÖWFW'2Fò6†ævRâv†BF†P¦6÷VçB7F–ÆÂFöW2æ÷B6''’—2v†W&R7F6²7FööBÂ†÷r&–r—Bv2÷"v†B—Bv2ÖFRöc²æ÷F†–æp¦–âF†RFF6WB&V6÷&G2F†Bf÷"ç’'V–ÆF–ærÂæBÃ#b—2v†W&R—B—2FÖ—GFVBà ¢¢¥–÷R6ææ÷BÆæB†ÆböböæRç’Ö÷&R¢¢ƒ##bÓ‚Ó’â6†V6²ç6†&V6ö×WFW2V6‚6öÖÖ—GFVBtÄ"w0¦–çWG2æBf–Ç2v†VâF†R&V6÷&BæBF†RÖW6‚F—6w&VRâF†Rv÷&¶–ær6†S¢&W&RF†R&V6÷&Böà¦'&æ6‚ÂÆWBF†R&¶Rv÷&¶fÆ÷r'Vâv–ç7BF†B'&æ6‚†—BG&–vvW'2öâç’W6‚VæFW ¦6†–6vòóFBöFFò¢¦÷"vVæW&F÷'2ò¢¦’ÂF¶R—G2&¶VB76WG2öçFòF†R6ÖR'&æ6‚ÂæBÖW&vP¦öæR"6''––ær&÷F‚â6VRvVæW&F÷'2öÖW6…ö–çWG2ç–f÷"v†B6÷VçG22â–çWBæBv†@¦FVÆ–&W&FVÇ’FöW2æ÷Bà ¢¢¥F†Rf—'7B'&–FvRÆæFVB##bÓ‚ÓÂæB—B—2F†Rf—'7B&V6÷&Bv†÷6R6—¦R—2Wf–FVæ6Râ¢¢F†P¤æ÷'F‚'&æ6‚7&÷76–ærB¶–ç¦–R7G&VWB(	B6†–6vòw2f—'7B'&–FvRÂƒ3"Óƒ3’(	B—2&V6÷&BÂ&¶P¦æBV&Æ—6†VBÖW6‚öâF†R'&–FvU÷F–Ö&W&&6†WG—RÂv†–6‚†B&VVâw&—GFVâæBæWfW"W6VBà¥F‡&VRF†–æw2v÷'F‚6''––ær–çFòF†R&W7Böb3S  ¢Ò¢¤7&÷76–ær6â&RÖV7W&VBv†W&R'V–ÆF–ær6ææ÷Bâ¢¢—G2sãƒ2Ò7â—2F†RF—7Fæ6P¢&WGvVVâF†RGvòG&6VBƒ3BvFW&Æ–æW2ÆöærF†R¶–ç¦–RÆ–væÖVçBÂ&VBöfb&—fW"ævVö§6öæÀ¢æB—G22ãC‚Òv–GF‚—26ÆVfW"w2'FVâfVWBv–FR"(	B6òF†Rfö÷G&–çB—2FW&—fVB&F†W"F†â¢Æ6V†öÆFW"âç—F†–ærF†BÖVWG2F†RG&6VBvFW"‡F†R–W'2ÂF†Rv†'fW2ÂF†R&gB'&–FvR’6à¢&RF–ÖVç6–öæVBF†R6ÖRv’âç—F†–ærF†BFöW2æ÷B7F–ÆÂvWG2Æ6V†öÆFW"à¢Ò¢¥F†R–çfVçF–öâÖ÷fVBg&öÒF†R÷WFÆ–æRFòF†R–çFW&–÷"â¢¢'V–ÆF–ærw2Æ6V†öÆFW"—2—G0¢fö÷G&–çC²F†—2'&–FvRw2—2F†Rf–gFVVâ7&–'2F†R&6†WG—RWG2VæFW"7âæö&öG’FW67&–&V@¢F†RÖ–FFÆRöb„Ã#’’â6ÖR6Æ72öbfVÇBÂF–ffW&VçBÆ6RFòÆöö²f÷"—Bà¢Ò¢¥F†R6öçG&7Bw2vFW"æ6†÷"—2–×ÆVÖVçFVBæ÷r¢¢(	BdU%D”4Åôä4„õ&öâF†R&6†WG—RÀ¢Æ6VÖVçBçfW'F–6Åöæ6†÷&–âF†R6–FV6"ÂÆ—FW&Â’Ò–âF†R&VæFW&W"ÂæB6Öö¶P¢76W'F–öâw&—GFVâ2F†RF–ffW&Væ6R&WGvVVâF†RGvòæ6†÷'2âF†RæW‡B7G'V7GW&R÷fW"vFW ¢æVVG2æò&VæFW&W"v÷&²â¢¥v†B—27F–ÆÂÖ—76–ær—2vÆ¶–æröâ—B¢£¢F†RvÆ¶W"föÆÆ÷w2F†P¢FW'&–âÂ6òF†RFV6²—266VæW'’âF†B—2—G2÷vâVæ—BæB—B—2&V6÷&FVB–â5DEU2Âæ÷Bf¶VBà ¢¢¥F†Rf—'7B'V–ÆF–ærv†÷6Rfö÷G&–çB—2Wf–FVæ6RÆæFVB##bÓ‚Ó¢¢ÂæB—B—2âDD•D”ôà§&F†W"F†â&W—"(	BF†Rf—'7B6–æ6RF†RVWVRV×F–VBâ†övå÷7F÷&VÂF†RÆör7F÷&RBF†P§vW7BVæBöbF†RÆ¶R7G&VWB&Æö6²v†W&RF†RVæ—FVB7FFW2÷VæVB÷7Böff–6RB6†–6vòöà£3Ö&6‚ƒ3Â6'&–W2Fö7VÖVçFVFfö÷G&–çC¢æG&V27FFW2—G26—¦RGv–6RÂGvVçG’'¦f÷'G’Öf—fRfVWBÂ&÷F‚F–ÖW22â6–FR&÷WB†÷rÆ—GFÆR&ööÒF†RF÷vâw2Ö–ÂæVVFVBâF‡&VP§F†–æw2v÷'F‚6''––ær–çFòF†R&W7Böb3S  ¢Ò¢¤'V–ÆF–ær6â&RÖV7W&VBgFW"ÆÂÂv†VâF†R6÷W&6R—2FW67&–&–ær6öÖWF†–ærVÇ6Râ¢¢F†P¢'&–FvRw2çVÖ&W'26ÖRg&öÒv—FæW72FW67&–&–ærF†R'&–FvRâF†—2öæRw26ÖRg&öÒw&—FW ¢Ö¶–ærö–çB&÷WBF†R§÷7Böff–6Rw2¢7&×VBV'FW'2âF–ÖVç6–öç2–âF†—2Æ—FW&GW&R†–FP¢–ç6–FR&wVÖVçG2&÷WB6öÖWF†–ær÷F†W"F†âF†R'V–ÆF–ærÂ6ò6V&6‚F†R&÷6R&÷VæBà¢–ç7F—GWF–öâ&F†W"F†âF†RVçG'’f÷"7G'V7GW&Rà¢Ò¢¥&VF–ærvR6÷'&V7FVBF†RF÷76–W"w26‡&öæöÆöw’'’GvVçG’ÖöçF‡2â¢¢Fö72÷&W6V&6‚ö ¢*rBFFVBF†R÷7Böff–6Rw2Ö÷fRFòg&æ¶Æ–âæB6÷WF‚vFW"g&öÒF†RF’†övâ&V6ÖP¢÷7FÖ7FW"ƒ"æ÷bƒ3"“²æG&V26—2Gv–6R—BÖ÷fVB&÷WB§VÇ’ƒ3BâF†RF÷76–W"w27VÖÖ'¢F&ÆW2&Rf–æF–ær–G2ÂæBF&ÆR&÷r—2æ÷BF†RvRâ6VRFö72õ$U4T$4‚ö†övå÷7F÷&RæÖF ¢*r2à¢Ò¢¥F†Rf—'7B&V6÷&Bv—F‚æ÷F†–ær6öæ¦V7GW&Â–â—Bâ¢¢—G2v2&Rv2–âF†R6÷W&6W2p¢&V6—6–öâ&F†W"F†âf–ÆÆVB†öÆW2Â6ò—BæVVG2æòÆ–&W'G’(	Bv†–6‚f–æÆÇ’W†W&6—6W2F†P¢&÷fVææ6R÷Ww2V×G’%v†BvRÖFRW†W&R"7FFRF†B5DEU2*r&V6÷&FVB2VæW†W&6—6V@¢'’&VÂFFâ—G2vV²ö–çB—2–ç7FVB—G2¢§7W'f—fÂ¢£¢GFW7FVBFò&÷WB§VÇ’ƒ3Bæ@¢Æ6VB–â66VæRVÆWfVâÖöçF‡2ÆFW"öâ6öçF–çV—G’&wVÖVçBÂ7FFVB27V6‚öâF†R&V6÷&Bà ¥W"Ö6ÇW7FW"&6VÇ2ÂV6‚öæRf–ÆRW"7G'V7GW&R6ò&ÆÆVÂvVçG2æWfW"6öÆÆ–FS  §Â&6VÂÂ6öçFVçG2À§ÂÒÒ×ÂÒÒ×À§ÂvöÆbö–çBvW7B&æ²ÂvöÆbFfW&â‡–çFVBvöÆb6–vâ’Âw&VVâG&VRÂvW7FW&â†÷FVÂÂ¦ÖW2¶–ç¦–R†÷W6RÂ"ââ¶–ç¦–R7F÷&RÀ§Âæ÷'F‚&æ²ÂÖ–ÆÆW"†÷W6RÂÖ–ÆÆW"FææW'’Â6ö'vV"67FÆRÂvÆ¶W"w2ÖVWF–ær†÷W6RÂ7FVÖ&öB†÷FVÂÂÆ¶R†÷W6R‡VæFW"6öç7G'V7F–öâ’À§Â6÷WF‚vFW"&Æö6·2(	4rÂF†R&Æö6²Ö'’Ö&Æö6²6¶WF6‚–âFö72÷&W6V&6‚óB×7G'V7GW&W2×6÷WF‚æÖF—2F†Rv÷&²÷&FW"âçä†övâw27F÷&RòF†Rf—'7B÷7Böff–6RÂÆ¶RB6÷WF‚vFW'çâ¢¤DôäR##bÓ‚Ó¢¢âæW‡BöâF†—2&Æö6³¢†–Æò6'VçFW"w2ÆörG'Vr7F÷&RÂ&–ÖÖVF–FVÇ’F¦6VçBFòF†R6Vvæ6‚w2V&Æ–2&""Âv†–6‚†2æòF–ÖVç6–öç2BÆÃ²æBF†R¢¤g&æ¶Æ–â7G&VWB÷7Böff–6R¢¢ÂF†R'V–ÆF–ær7GVÆÇ’†öÆF–ærF†RÖ–ÂöâF†R66VæRFFRÂöbv†–6‚æ÷F†–ær'WB7G&VWB§Væ7F–öâ—2GFW7FVB(	B6VRFö72õ$U4T$4‚ö†övå÷7F÷&RæÖF*rB&Vf÷&R'V–ÆF–ær—BÀ§ÂÆ¶R7G&VWBÂG&VÖöçB†÷W6R’ÂÖç6–öâ†÷W6RÂW†6†ævR6öffVR†÷W6RÂ7BâÖ'’w2Âf—'7B&W6'—FW&–âÂF†öÖ26‡W&6‚7F÷&RÀ§Â6—f–27V&RÂW7G&’VâÂÆör¦–ÂÂ6÷W'F†÷W6R‡VæFW"6öç7G'V7F–öâÂÖöçF‚Væf—†VB’À§Âf÷'BFV&&÷&âÂÆ—6FRÂ&Æö6¶†÷W6RÂ&7F–öâÂÖv¦–æRÂV'FW'2Â&'&6·2Â7WFÆW"Â†÷7—FÂÂ&FRÂv&FVç2À§Â†&&÷"v÷&·2Âæ÷'F‚–W"Â6÷WF‚–W"ÂF†R7WBÂF†RÆ–v‡F†÷W6RÂv†'fW2À§Â7&÷76–æw2Âçäæ÷'F‚'&æ6‚'&–FvWçâ¢¤DôäR##bÓ‚Ó¢¢+r6÷WF‚'&æ6‚&gB'&–FvR†fÆöF–ær(	BæVVG2—G2÷vâ&6†WG—RÂ6VR'&–FvU÷F–Ö&W%÷&×6’+rFV&&÷&â7G&VWBG&v'&–FvRƒ#gBv—F‚cÖgBG&rÂF–ffW&VçBæ–ÖÂæB÷WG6–FRF†R7W'&VçBFW'&–â&÷‚’À ¢223b(	BfÆ÷&æBfVæ ¢¢¤æBF†Rw&÷VæBw27W&f6RÂv†–6‚—2æ÷rFV6Æ&VBöÖ—76–öâ&F†W"F†ââVç7FFVBöæR¢ ¢ƒ##bÓ‚ÓÂÃ3R“¢F†RFW'&–â7V2w&FW2f—fR7W&f6RÖFW&–Ç2(	BF†RF—f—6–öç2rÆöÒ÷fW §V–6·6æB÷fW"&ÇVR6Æ’ÂF†RÖ'6‚7G&—w2VBæB6VFvRÂF†R6†ææVÂw26–ÇB(	BæBF†RÖW6‚—0¦öæRV'F‚6öÆ÷W"âW"×¦öæR7W&f6RG&VFÖVçBG&—fVâ'’F†÷6RVçG&–W2&WF—&W2Ã3S²F†RÆWGFP¦†2Fò&R&wVVBg&öÒF†R6÷W&6W2&F†W"F†â–6¶VBÂv†–6‚—2F†R6ÖRG&F†R7G&VWB7W&f6P¦—2Œ*r3’’à ¥W"×¦öæR&6VÇ2g&öÒF†RF÷76–W'3¢fÆ÷&¦öæW2ÂrfVæ¦öæW2â†öæ÷"F†R§VÇ’†VæöÆöw§'VÆW2(	B&–r&ÇVW7FVÒ—2fVvWFF—fR–â§VÇ’Â6÷&Fw&72—2F†RFÆÂfÆ÷vW&–ærVÆVÖVçBÂ&×2&P¦ÆVfÆW7266W2âæVvF—fRf–æF–æw2†æò&–ærÖ&–ÆÆVBwVÆÇ2Âæò&VfW"ÂæòW&–öF–6Â6–6F2’vð¦–çFòF†RFF2'6VçFVçG&–W2v—F‚6—FF–öç2Â6òæö&öG’&RÖFG2F†VÒÆFW"à ¢2223f(	BF†RW–RÖ†V–v‡B7v&B+r¢¥$õTäB”â##bÓ‚Ó¢  ¦&VæFW&W'2÷vV"ö§2öfÆ÷&æ§6G&w2F†Rw&Ö–æö–BÖG&—‚ÂF†Rf÷&"Æ–W"ÂF†RVÖW&vVçG2æBF†P¦Æ÷r6‡'V'2g&öÒFFöfÆ÷&öÂÖ÷VçFVB–âÖ–âæ§6&W6–FRG&VW2æ§6â&ÆFRvVöÖWG'’'Vç2v—F†–à¦&÷WBrãbÒæB6ÖW&Öf6–ær6ÇV×6&G2Fò#rÓ²&W–öæBF†VÒF†R7GVÂFW'&–âw2&ö6VGW&À§&—&–RFW‡GW&R6'&–W2Vç&W6öÇfVB6öÆ÷W"âÆ6VÖVçB—2FWFW&Ö–æ—7F–2v÷&ÆBÆGF–6P§&RÖ6VçG&VBöâF†RvÆ¶W"æB7VÆÆVBFòc,+6öæRÂ6òæ÷F†–ær7v–×2VæFW&fö÷BæBæ÷F†–ær—0§–Bf÷"&V†–æB–÷W"†VBâ†V–v‡G2Âw&VVç2Â6÷fW"Â†VæöÆöw’æBW"×ÆçB6öæf–FVæ6RÆÂ6öÖP¦g&öÒF†R&V6÷&G3²F†RGVgBFVç6—G’æBf"×FW‡GW&R6ö×&W76–öâ&RÆ–&W'F–W2„Ã3"ÂÃƒ’à ¢¢¤6÷'&V7FVBgFW"F†R##bÓ‚Ó&VÂÖFWf–6R&Wf–Ws¢¢¢F†Rf÷&ÖW"Ã32f"Öf–VÆB6æ÷’v2§6öÆ–B7W&f6RBÆçB×F÷†V–v‡Bâ—BÆöö¶VBÆ–¶R6V6öæBFW'&–âÆ–W"Â†–Bf÷VæFF–öç2æ@§&ö÷G2ÂæB6÷VÆB&RvÆ¶VBVæFW&æVF‚â—Bv2&VÖ÷fVB&F†W"F†âÖ¶–ærF†RvÆ¶W"æBWfW'¦'V–ÆF–ær7FæBöâfÇ6RÆçB×F÷F÷öw&‡’âFW'&–â—2æ÷rF†R6öÆR‡—6–6ÂæBf—6–&ÆP§7W&f6S²ÆÂFWF–ÆVBfÆ÷&æB7G'V7GW&W26†&R—G26×ÆW"âÃƒ&V6÷&G2F†R&WÆ6VÖVçBà ¢¢¤§VFvVBv–ç7Btõ$²ö&&¢¢(	BGvòfW&–f–VB†÷Föw&‡2öb7W'f—f–ær–ÆÆ–æö—2FÆÆw&72–à¦Ö–BÔ§VÇ’†6†–6vò×&Vv–öâ&VÖæçBÂ#’§VÇ’##²GUvR&W7F÷&F–öâÂ#B§VÇ’#‚’æBà¤ö7Fö&W"æVvF—fR6öçG&öÂâv†W&R&÷VæB7FæG2ÂÖV7W&VBöâF†R&–Ö'’6†÷B&F†W"F†à¦76W'FVC  §ÂFVÆÂÂ&VfW&Væ6RÂ&÷VæBÀ§ÂÒÒ×ÂÒÒ×ÂÒÒ×À§ÂF†Rw&÷VæB—2†–FFVâBW–R†V–v‡BÂ–çf—6–&ÆRÂ†–FFVâ7Bã2ÒÂF6‡’–âF†RæV&W7B"ÒÀ§Â6WfW&Â†V–v‡G2Â6WfW&Âw&VVç2ÂBÓRÆ–W'2ÂR7V6–W2†V–v‡G2ÂGvòw&VVç2V6‚ÂW"&V6÷&BÀ§Â§VÇ’‡VR†w&VVâÂæ÷BFvç’’Â"ôrãsbÓã“2Â¢£ãs2Óãƒ¢¢À§ÂÆö6Â6öçG&7B‡“(‰"ÇVÖ–ææ6R’Â¢£CÓ#"¢¢Â¢£æV"Âƒ2Ö–BÂCbf"¢¢À§ÂæòfÆ÷vW&–ær&ÇVW7FVÒô–æF–âw&72÷7v—F6†w&72ÂæöæRÂæöæRÂ7G'V7GW&ÆÇ’À ¢2223fæW‡B(	BF†R÷Vâv÷&²Â–âF†R÷&FW"—B—2v÷'F‚Fö–æp ¢¢¥&V÷&FW&VB##bÓ‚ÓgFW"F‡&VRÖ7&—F–2&Æ–æB&÷VæBöâöæR–FVçF–6Â6†÷B6WBâ¢¢WfW'’—FVÐ¦&VÆ÷r6'&–W2ÖV7W&VBF&vWBæBF†RFVf–æ—F–öâ—B—2ÖV7W&VBv—F‚Â&V6W6RGvò&÷VæG2ö`§F†—2v÷&²vW&R7VçB6†6–ærçVÖ&W'2F†BV—F†W"F–Bæ÷B&W&öGV6R÷"F–Bæ÷BW†—7B–âF†P§&VfW&Væ6Râ6VR5DEU2æÖB*r$¶æ÷vâvV¶æW76W2"f÷"F†RgVÆÂÖV7W&VÖVçG2âF†RöÆBÆ—7Bw0¦—FV×2(	32vW&Ræ÷Bw&öæs²F†W’vW&R–ÖVBBF†RæV"f–VÆBÂæBF†R&Æ–æBFW7B—2&V–ærÆ÷7@¦–âF†R¢¦Ö–B¢¢f–VÆBà £â¢¥&W7F÷&RF—7FçBfVvWFF–öâv—F†÷WB&W7F÷&–ær6V6öæB7W&f6Râ¢¢F†R&VÖ÷fVBÃ326†VW@¢6ææ÷B&WGW&ã¢ç’–×÷7F÷"÷"7'6Rf"vVöÖWG'’×W7B&R&ö÷FVBöâF†R†V–v‡Ff–VÆBÂ&VÖ–à¢f—6–&Ç’÷&÷W2ÂæB72F†R6ÖR&ö÷Bö'V–ÆF–ær÷vÆ¶W"7W&f6R6†V6·22F†RFWF–ÆVBf–VÆBà¢F†RFW'&–âFW‡GW&R—2F†R†öæW7B7W'&VçBfÆÆ&6²&W–öæB#rÒà£"â¢¤v—fRF†Rf"FW'&–âFW‡GW&Rw&–âBg&vÖVçB66ÆRâ¢¢¶VW—BöâF†R‡—6–6ÂFW'&–âÀ¢v—F‚Væ÷Vv‚—'&VwVÆ"6öçG&7BFò7VvvW7BVç&W6öÇfVBfVvWFF–öâv—F†÷WB76W'F–ær6V6öæ@¢†V–v‡B÷"7V6–W26–Æ†÷VWGFRâ&RÖÖV7W&RF†RöÆB†–v‚×72F&vWBv–ç7BF†R6÷'&V7FV@¢&VæFW&W"&Vf÷&R&WW6–ær—C²F†R&–÷"Bãbf–wW&RÖV7W&VBF†R&VÖ÷fVB6†VWBà£2â¢¤¶–ÆÂF†RÖ–FFÆRÖF—7Fæ6R&–ær6VÒâ¢¢+r¢¤DôäR##bÓ‚Ó2â¢¢ETäRæÖ–Bç&F—W2Ò#rãF–@¢ÖFò6öç7FçB67&VVâ&÷röâfÆBw&÷VæBÂæBF†RÖV7W&VÖVçBF†B6—26ò—2æ÷r–âF†P¢vFS¢&–âF†Rf–Wr'’&V&–ærÂ6²V6‚&–â†÷rf"—G2÷vâ7v&B&V6†W2Â6öçfW'BFòF†R&÷p¢—BÆæG2öââöâF†R&–ær2—B7FööBF†÷6R&÷w27ææVB¢£ãB‚¢¢(	BF†Rf–æF–ærw2'&¦÷ ¢7G&–v‡B7&÷72ÆÂ#ƒ6öÇVÖç2"Â–âöæRçVÖ&W"âf—†VBF†R6V6öæBv’F†R—FVÒöffW'2Âæ÷@¢F†Rf—'7C¢WfW'’ÆGF–6R6Æ÷B6'&–W2—G2÷vâ÷WFW"&F—W2ÂfFU³ÖÇW2v÷&ÆBÖæ6†÷&V@¢öfg6WBöbWFò¢¬+2Ò¢¢Œ+ãbÒöâ†öæR(	B&÷WBâV–v‡F‚öbF†R&–ærBWfW'’FWF–À¢6WGF–ær’Âg&öÒ6Öö÷F‚BÒfÇVRÖæö—6RÆö&W2v—F‚W"×6Æ÷BF—F†W"öâF÷âÖV7W&VBgFW# ¢¢£Rã’‚¢¢öb7&VBB#ƒ9sƒæB¢£rãB‚¢¢B3“9ssƒÂ&V6†–ær#Rã(	3#‚ãBÒ&÷WB¢æöÖ–æÂ#bãBâWfW'’6&B—27F–ÆÂ&ö÷FVBöâF†RFW'&–âæBæ÷F†–ærÖ÷fVBfW'F–6ÆÇ’à¢Ò¢¥v–FVæ–ærF†RfFRv2F†Rw&öær†ÆböbF†R6†ö–6Râ¢¢F†R&æB—2Ç&VG’rÒÂv†–6‚—0¢‚‚öbF†Rg&ÖRBF†BF—7Fæ6S²F†RÆ–æR—2æ÷BF†R&×Â—B—2v†W&RF†R&×&V6†W0¢¦W&òÂæBv–FW"&×7F–ÆÂ&V6†W2¦W&òWfW'—v†W&RBöæ6Rà¢Ò¢¤—B—2æV&Ç’g&VRÂæBF†B—2&÷W'G’öbF†RFW6–vâ&F†W"F†âÇV6²â¢¢G&–ævÆW2&P¢–Bf÷"'’F†RÄED”4RÂæ÷B'’F†RfFRÂ6ò6Æ÷BF†Rg&–ævRW6†W2&W–öæB&V6‚—0¢G&÷VBB&V'V–ÆB–ç7FVBöbG&vâB¦W&ò†V–v‡C²F†RÆGF–6Rw&Wr'’F†R×Æ—GVFRFð¢6''’F†RöæW2—BW6†W2–âÂæBv—F‚7–ÖÖWG&–2öfg6WBF†RÖVâ6÷7B—0¢&F—W<+"²f&–æ6V&F†W"F†â‡&F—W2²×Æ—GVFRœ+&âÖV7W&VBô"B#ƒ9sƒBF‡&VP¢f—†VB7FF–öç3¢÷Vâ&—&–R¢£sB3c2(i"sbcSb¢¢G&–ævÆW2‚³ã2RÂ2sC"(i"2ƒSfÆ÷&¢–ç7Fæ6W2’Â6WGFÆVBF÷vâ¢£3ƒ’3c’(i"3ƒ’#S2¢¢Ž(‰#ã2R’Â&—fW"&æ²¢£3S’(i"3SR¢¢à¢G&r6ÆÇ2Væ6†ævVBB3ròcbòs"â––ærf÷"F†Rv†öÆRæçVÇW2–ç7FVB(	BG&v–ærF†P¢W6†VBÖ÷WB6Æ÷G2B¦W&ò†V–v‡B(	Bv÷VÆB†fR&VVâF†R×Æ—GVFRGv–6R÷fW"à¢Ò¢¥F†Röfg6WB—2gVæ7F–öâöbv÷&ÆB÷6—F–öâöæÇ’¢¢Â6òF†R&vvVBVFvR—2æ6†÷&VBFòF†P¢w&÷VæC¢—BFöW2æ÷B7v–Ò2F†RvÆ¶W"Ö÷fW2ÂæB—B—2F†R6ÖRVFvRv†–6†WfW"v’F†W¢f6RâF†RvFR6·2F†RÆ6W"†fÆ÷&æg&–ævTF’f÷"—B&F†W"F†â&RÖFW&—f–ærF†Ræö—6RÀ¢æB6†V6·2æ–æRö–çG2ç7vW"–FVçF–6ÆÇ’g&öÒGvò6ÖW&2CÒ'Bà¢Ò¢¥F†Rf÷&"&–ærVæG2v—F†–âÖWG&RöbF†RÖ–B&–ær¢¢Â6òF†RfÆ÷vW'2v÷VÆB†fRvöæRöà¢G&v–ærF†RÆ–æRF†Rw&72æòÆöævW"FöW3²—B6'&–W2F†R6ÖRg&–ævRâ—B—2vFVBöâ—G0¢$”äu2&F†W"F†âöâ—G2G&vâVFvR(	BB2ãBÒ6VÆÇ22ãs\+&–â†öÆG2öæR÷"Gvòf÷&'2Â6ð¢'F†RgW'F†W7BöæRG&vâ"—26×Æ–ær7FF—7F–2ÂæBÖV7W&VBF†Bv’—B&W÷'FVBæ–æP¢ÖWG&R†öÆR–âw&÷VæBF†B†2æöæRà¢Ò¢¥F†R÷Ö–âvFR†BFò&RÖFR–ç7Fæ6RÖv&RFò7F’†öæW7Bâ¢¢—B6¶VBF†RÆ–W"w0¢æöÖ–æÂ&–ær†÷rfFVBâ'&—f–ærÆçBv2ÂæBF†RæöÖ–æÂ&–ærç7vW'2§¦W&ò¢(	Bg&VP¢72(	Bf÷"W†7FÇ’F†RÆçG2F†Rg&–ævRW6†W2gW'F†W7B÷WBâ—B&VG2V6‚–ç7Fæ6Rw2÷và¢6†•&–ævæ÷râ6ÖR&÷VæBÂ6ÖRÖV7W&VBãR'&—fÂ†V–v‡Bà£6"â¢¥F†RäT"ôÔ”B†æF÷fW"—2FVç6—G’†æF÷fW"â¢¢+r¢¤DôäR##bÓ‚Ó#BÂBÓ“2â¢¢F†R6–&Æ–ærö`¢—FVÒ3¢F†BöæRv2&÷WBv†W&RF†R7v&B5Dõ2ÂF†—2öæR—2&÷WBv†W&R—G2Gvð¢&W&W6VçFF–öç27v÷fW"â&VBF†—2&÷‚&Vf÷&RV÷F–æræV"×&–ær&æB÷"&Vf÷&R77VÖ–ær¢&–æræÖVB–âF–6¶WB—2F†R&–ærG&v–ærF†R'FVf7Bà¢Ò¢¥F†R–ç7G'VÖVçBf—'7B¢¢Â&V6W6RF†W&Rv2æöæS¢FööÇ2öÖV7W&UöæV%÷fW&vRæÖ§66Æ76W2WfW'¢fÆ÷&–ç7Fæ6RF†Rv’F†Rg&vÖVçB6†FW"w2÷vâwV&BFöW2(	Bv†öÆV†6÷fW&vRÂF†R&–W ¢'&æ6‚—26¶—VB’Â'F–ÆƒÂ6÷fW&vRÂÂ¢¦WfW'’g&vÖVçBF‡&W6†öÆFVB(	BF†RF÷G2¢¢’À¢'6VçF(	BöfbF†R6†•&–ævF†BvVçBFòF†RuRÂF†Vâ&ö¦V7G2V6‚G&vâÆçBw2&V6÷&FV@¢†V–v‡BæB7&VBFò67&VVâæB7V×2F†Rfö÷G&–çG2â–ç7Fæ6R6÷VçG2&RF†Rw&öærVæ—C¢¢‡VæG&VBÆçG2Bf÷'G’ÖWG&W2&Rf÷W"—†VÇ2âÖö&–ÆR'Vç2BFWf–6U66ÆTf7F÷#¢ãVÂæ÷@¢F†R6Öö¶Rw2"Â6òöæRÖV7W&VB—†VÂ—2öæRG&v–ærÖ'VffW"—†VÂ(	BF†R67&VVâFö÷"—2Æö6¶V@¢FòvÅôg&t6ö÷&FæBBó2&W6×ÆR6ÖV'2F†Rw&–âà¢Ò¢¥D„RD”4´UBu2$”ÔR5U5T5B•2„ÄbD„RUD„õ"ÂäBB•E2õtâEtò5DäE2•B•2äôäRôb•Bâ¢ ¢BÓƒbw2Gvò7FæG2&R–â&öGv’æB7FF–öâ‚–6ÆV'2F†RG&fVÂG&6²(	BãRÒöâ6÷WF€¢vFW"ÂrÒöâvVÆÇ2(	B6òB¥6÷WF‚vFW"&ö6†–ærvVÆÇ2¢F†RæV"&–ærÆ6W2¢£GVgG2@¢Æ–v‡FÂBgVÆÆ¢¢âB¥vVÆÇ2&ö6†–ærÆ¶R¢öâ†öæRF†RæV"6WB—2V×G’æBF†P¢v†öÆR67&VVâÖFö÷&VBfW&vRƒãs#’RöbF†Rg&ÖR’—2w&—GFVâ'’F†R¢¦Ö–B&–ærw2–ææW"&× ¢fF–ær”â7&÷72Bã^(	3rãRÒ¢¢âöæÇ’–â÷Vâ&—&–RFöW2F†RæV"&–ærFöÖ–æFS¢Rã“Rv–ç7@¢F†RÖ–Bw22ãcRRW‡÷6VBBÆ–v‡Fâ6ò&÷F‚&÷VæF&–W2vW&R6öçfW'FVBÂæ÷BF†RæÖVBöæRà¢Ò¢¥F†R&æB—2æ÷Bv†W&RF†RF–6¶WB6—2V—F†W"â¢¢&–æw4f÷&–ç6WG2WfW'’fFR&–ær–ç6–FR—G0¢ÆGF–6R'’F†RãbÒ&V'V–ÆB7FWÂ6òF†R&×'Vç2¢£Bãƒ(	3rãÒ¢¢BgVÆÆ†ÖV7W&VB2F†P¢F&ævRöbF†R'F–Â–ç7Fæ6W2’Âæ÷BRãN(	3rãc²æBBÆ–v‡FF†R&–ær—2BãbÒÂ6òF†R&× ¢—2¢£ãƒ(	3BãÒ¢¢(	BVæFW"F†RvÆ¶W"w2fVWBÂv†–6‚—2v‡’F†R†öæRg&ÖR—2F†RG&ÖF–2öæP¢ƒS2ãcSBRöb—B67&VVâÖFö÷&VB–â÷Vâ&—&–RÂv–ç7BCRãs2RöâF†RFW6·F÷’à¢Ò¢¥F†Rf—‚—2BÓƒbw2ç7vW"öâ&–ærF†B7F–ÆÂ†2âVFvR–â—Bâ¢¢ETäV ¢æV"ç7&VD÷WFW&òÖ–Bç7&VD–ææW&Ö÷fRF†R&æB÷WBöbF†R&×æB–çFòW"×6Æ÷@¢7&VBöbF†R&÷VæF'“¢fFU³Ò(‰"&æB9r†æF÷fW%&æ²†RÂâ–Âv÷&ÆBÖæ6†÷&VBæBVçF—6VBFð¢(Y²Ò2f%&æ¶—2Âv—F‚F†R6†FW"w2&–ærÆVgB27FW†„$F’âF†Rg&7F–öâöb6Æ÷G0¢G&vâBF—26Æ×‚†fFU³Ò(‰"B’ò&æB–(	B¢§F†R6ÖRçVÖ&W"F†RÇ†W6VBFòw&—FR¢¢(	@¢6òW‡V7FVB6÷fW"—2Væ6†ævVBFòF†R&—F†ÖWF–2æBæòGVæ–ærf–wW&RÖVç2ç—F†–æræWrà¢Ò¢¥Æ6VÖVçB—2VçF÷V6†VBöâW'÷6Râ¢¢F†RÖ–B&–ærw2&WGW&æf÷"6Æ÷G2F†Rg&–ævRW6†W2÷W@¢öb&V6‚—2FVÆ–&W&FVÇ’äõB6÷–VBFòF†RæV"73¢WfW'’6Æ÷B—27F–ÆÂFVÇB7V6–W2æ@¢7F–ÆÂ6÷VçFVBÂ6òæò6öÖ×Væ—G’w2÷VÆF–öâ÷"6÷fW"f–wW&RÖ÷fW2â—B6÷7G2æ÷F†–ær(	BF†P¢fW'FW‚&öw&ÒÇ&VG’6öÆÆ6VBâ÷WBÖöb×&–ærÆçBFòö–çB(	BæB—B6fW2f–ÆÂÂ&V6W6P¢†ÆbF†R&æBw2g&vÖVçG2&RæòÆöævW"&7FW&—6VBöæÇ’Fò&RF—66&FVBà¢Ò¢¥Gvò¶æö6²Ööç2â¢¢†VG2&–FRF†V—"ÄåBw2&–æræ÷rÂæ÷BF†RÆ–W"w3¢öâ7&VB&÷VæF'’F†P¢Æ–W"w2&–ærç7vW'2f÷"æò'F–7VÆ"GVgBÂæB†VB‡Væröâ—B—2"Ô%Tsrg&öÒF†R÷F†W ¢VæBâæBfÆ÷&æfFTFö†V–v‡DFF¶RÆÂf÷W"&–ærçVÖ&W'2Â&V6W6R&VFW"6''––æröæÇ¢F†R÷WFW"&F—W2v÷VÆB&RFöÆBWfW'’Ö–B6&B7BBãRÒ—2G&vâà¢Ò¢¥F†R&W6–GVRÂ†VÆB&F†W"F†â6Æ÷6VBâ¢¢F†RÖ–BæBf÷&"&–æw2r÷vâõUDU"&×2&R7F–ÆÀ¢6÷fW&vR&×2ÂæBBÆ–v‡FF†W’&V6‚–âFò¢£RãBÒ¢¢æB¢£rãBÒ¢¢(	B–ç6–FRF†RfW&vRöâ¢†öæRâF†B—2F†RÖ–N(i&f"†æF÷fW"Âv†–6‚BÓƒbç7vW&VB'’7FæF–ærF†Rf"&æB÷fW"—C°¢F†RvFR†öÆG2—Bv–ç7BFööÇ2öæV%÷fW&vUö&6VÆ–æRæ§6öæ6ò—B6ææ÷Bw&÷rÂæB—B—2f–ÆVBà¢¢¤6Æ÷6VB##bÓ‚Ó#r'’—FVÒ62&VÆ÷rÂæBäõBF†Rv’F†—2&÷‚W‡V7FVBâ¢ £62â¢¥F†R÷WFW"&×2rt”ED‚Âæ÷BF†V—"¶–æBâ¢¢+r¢¤DôäR##bÓ‚Ó#rÂBÓƒrâ¢¢F†R&W6–GVR—FVÒ6 ¢&æ¶VC¢BÆ–v‡FF†RÖ–BæBf÷&"&–æw2r÷WFW"6÷fW&vR&×2&VvâRãBÒæBrãBÒ†VBö`¢F†RvÆ¶W"æBRãBRöbF†R†öæRw2g&ÖR–ç6–FRæ–æRÖWG&W2v2w&—GFVâF‡&÷Vv‚F†R67&VVà¢Fö÷"â&VBF†—2&÷‚&Vf÷&R&÷÷6–ærFVç6—G’†æF÷fW"öâç’õUDU"VFvRà¢Ò¢¥F†R6W6R—2öæRÆ–æRF†Bv2æWfW"66ÆVBâ¢¢ÄõvæBÔ”F7WB&F—W6æB66ÆV@¢g&–ævVv—F‚—B(	B&&÷WBâV–v‡F‚öbF†R&F—W2BWfW'’6WGF–ær"Â—G2÷vâ6öÖÖVçB(	BæBÆVg@¢&æFBETäRw2rãÒæBRãÒâ&×6—¦VBf÷"Ž(	3#rÒF†W&Vf÷&R6Böâ2Ò&–æræ@¢6ÖR÷WB7&÷72F†RÖ–FFÆRöbF†R†öæRw2f–VÆBâ&Ææ6VF†B—BFöó¢F†RÖ–B&×&Vvâ@¢¢£‚ã"Ò¢¢F†W&RÂÇ6ò–ç6–FRF†RfW&vRâæ÷F†–ær&÷WBF†R†öæRv27V6–Ã²F†RçVÖ&W"6–×Ç¢v2æ÷B6'&–VBF÷vâà¢Ò¢¥D„Rô%d”õU2d•‚t2$”4TBäB$TeU4TBÂæBF†RçVÖ&W"—2F†R&V6öââ¢¢†æF–ærF†W6RVFvW0¢÷fW"'’FVç6—G’(	B7&VD÷WFW&ÂBÓ“2w2÷vâç7vW"(	Bv26–×VÆFVB6Æ÷B'’6Æ÷BöâF†P¢V&Æ—6†VBÖ—'&÷"v–ç7BWfW'’Ö–B–ç7Fæ6Rw2÷vâ6†•&–ævæBF†RvFRw2÷vâb&V&–æp¢&–ç2â—BF¶W2F†RÖVâG&vâ&V6‚g&öÒ¢£#bãƒÒFò#RãC"ÒBgVÆÆ¢¢Âv†–6‚F†R&÷VæF'¢6†V6²7W'f—fW2†&"#Bã“’ÂæBg&öÒ¢£ãƒ’ÒFò’ãcBÒBÆ–v‡F¢¢Âv†W&RF†R&"7FæG2@¢¢£ãcÒæBöæÇ’ã#’Òöb—Bv2Vç7VçB¢¢âWfVâöæRÖÖWG&R7&VBÆæG2BãC‚ÒâF†P¢Æ÷72—2æ÷BGVæ–ær'FVf7C¢F†RG&vâVFvRöb7Fö6†7F–2F†–ææ–ær—2F†RFWF‚Bv†–6€¢F†RF†–ææ–ær7F–ÆÂÆVfW2ÆçB7FæF–ær–âv—fVâ&V&–ærÂæBF†RÖ–BÆGF–6RFVÇ2&÷W@¢öæR6Æ÷BW"ÖWG&RW"&–âB"Òv–ç7BGvòæBF†—&BB#bÒà¢Ò¢¥F†R&"—Bf–Ç2—2&W7F–æröâÆçG2æö&öG’6â6VRÂæBF†B—2æ÷r—G2÷vâF–6¶WBâ¢¢F†P¢&V6‚FÖ—G2ç’ÆçBBfFTBâã&(	BGvòW"6VçB6÷fW&vRÂöæR—†VÂ–âf–gG’F‡&÷Vv€¢F†R&–W"ÖG&—‚âöâ6÷fW&vR&×F†B—2WfW'’Æ6VB6Æ÷BÂ6òF†R7FF—7F–2&W÷'G2v†W&P¢F†RÆ6W"7F÷VBÆ6–ær&F†W"F†âv†W&RF†Rf–VÆBVæG2ÂæB—B6âöæÇ’WfW"&RÖWB'¢G&v–ærv†÷7G2â¢¥BÓ#’â¢¢F†R&'2vW&RÆVgBW†7FÇ’v†W&RF†W’7FööBà¢Ò¢¥6òF†R&×—27WBFòF†R&–ær–ç7FVBâ¢¢F†R'VÆS¢â÷WFW"&æBÖ’æ÷B$Tt”â–ç6–FRF†P¢fW&vR(	B&F—W2(‰"7FW(‰"g&–ævR(‰"’ãÂF†Ræ–æRÖWG&W2FööÇ2öÖV7W&UöæV%÷fW&vRæÖ§66ÆÇ0¢F†Rw&÷VæBvÆ¶W"Æöö·2BâÆ–v‡FF¶W2¢£ãbÒ¢¢öâ&÷F‚&–æw2‡F†R6ÆV&æ6R&–æG2@¢ãƒ²—BÆæG2WVÂFòF†Rg&–ævRÂ6òF†RVFvRF†–ç2÷fW"æòÖ÷&Rw&÷VæBF†â—B—2&vvV@¢'’“²&Ææ6VFF¶W2F†R&÷÷'F–öæFR¢£BãrÒ¢¢æB¢£2ãBÒ¢¢Âv†–6‚Ç&VG’6ÆV"—C²gVÆÆ ¢—2Væ6†ævVBBrãÒæBRãÒÂ6ÆV&–ær'’bãBÒæBrãBÒà¢Ò¢¥v†B—B6÷7G2æBv†B—B'W—2â¢¢F†RÆGF–6R—2VçF÷V6†VBÂ6òG&–ævÆW2Â–ç7Fæ6W2æBG&p¢6ÆÇ2&RVæ6†ævVB(	BF†R&×w2÷vâ6öÖÖVçB–â—FVÒ2Ç&VG’6—2F†RÆGF–6R—2f÷"F†P¢vVöÖWG'’æBF†RfFR—2f÷"æ÷F†–ærâv†B6†ævW2—2f–ÆÃ¢F†Rw&÷VæBF†R&×W6VBFð¢F†–â—2G&vâ6öÆ–BÂæBF†R†öæRw27v&B7F÷2÷Væ–ærWf—fRÖWG&W2†VBöbF†RvÆ¶W"à¢öfb–FVçF–6ÂÆ6VÖVçBÂfÆ÷&ÖÖ–FG&vât„ôÄRvöW2¢£r(i"CB¢¢–â÷Vâ&—&–RÂ"(i"s@¢vVÆÇ2Âb(i"3öâF†R6÷WF‚vFW"fW&vRâF†RfÆ÷vW"†VG2&V6‚gW'F†W"÷WBv—F‚—BÂ&V6W6P¢†VE&–ætöf†æw2F†R†VB&–æröfbF†R&æB†fFU³Ò(‰"ã3R9r&æF“¢BÆ–v‡FF†Rf÷& ¢†VG2'VâFòã‚Òv†W&RF†W’7F÷VBBãÒà¢Ò¢¤æBF†R&V6‚—Bv2&VgW6VBf÷"vVçBUâ¢¢'BrB3“9ssƒgFW#¢Ö–â¢£ã3"Ò¢ ¢‡VæÖ÷fVB’ÂÖVâ¢£ãƒ’(i"ã“bÒ¢¢ÂÖ‚¢£"ãsb(i"2ã#"Ò¢¢Â&÷VæF'’&÷w2¢£rãB(i"’ã‚‚¢¢À¢&÷F‚&'2w&VVâv†W&RF†W’7FööBâ&—F†ÖWF–2&F†W"F†âÇV6²(	BF†R6Öö¶R7VÆÇ2&VÆ÷p¢fFTBÃÒã&Âv†–6‚—2ãBÒöb&V6‚öârÒ&æBæBã2ÒöâãbÒöæRâv†–6‚—0¢F†RÖ—'&÷"–ÖvRöbv‡’F†RFVç6—G’†æF÷fW"6÷VÆBæ÷B&R†C¢—BFöW2æ÷BG&rF†R÷WFW&Ö÷7@¢ÆçG2BÆÂà£Bâ¢¥&RÖ&6VÆ–æRF†R7&÷vâÖWG&–72â¢¢F†R&Wf–÷W27&÷vâf–æRÖFWF–ÂÂF&¶æW72æB‡VRF&vWG0¢ÖV7W&VB7W&f6RF†BæòÆöævW"W†—7G2âW7F&Æ—6‚æWræV"öÖ–BæBf"×FW'&–â&æG2&Vf÷&P¢GVæ–ær6öÆ÷W"÷"6öçG&7C²æWfW"–×&÷fRF†R66÷&R'’6Æ÷6–ærF†Rf"f–VÆB–çFò6†VWBà£Râ¢¤†÷&—¦öâ6öçF–çV—G’â¢¢6öÇVÖç26''––ærF–Ö&W"¢£3R(i"(šR“R¢¢‡&VfW&Væ6RR–âWfW'¢&æB’â&æB¦†V–v‡B¢7F—2(	3B‚(	BF†B&—F†ÖWF–2—2†öæW7BâGvòÖV6†æ—6×3¢G&÷ ¢†¦TF—7Æ”Æ–æV"‚–w24U27FW6òF†R&æB7F÷2&V–ær–ÖVBb"ò"r7BF†Rw&÷Væ@¢—BF÷V6†W2ÂæB7W&W72F†R7&÷vâövÖöGVÆF–öâ¶v†VæWfW"7&÷vâ7V'FVæG2VæFW"ã"‚À¢v†W&R—BFVÆWFW2F†R6–Æ†÷VWGFR&F†W"F†âFW‡GW&–ær—Bà¢¢¤$õD‚ÔT4„ä•4Õ2DôäR##bÓ‚Ó2âF†R†÷Föw&†–26öÇVÖâ6÷VçB—2äõB&RÖÖV7W&VBÂæ@¢F†B†ÆböbF†R—FVÒ7F—2÷Vâ¢¢(	BF†R6†÷B†&æW72F†R3R6ÖRg&öÒ—2æ÷B–âF†RvFRÀ¢æBV÷F–ærçVÖ&W"F†—26Æ–6RF–Bæ÷BÖV7W&Rv÷VÆB&RW†7FÇ’F†Rf–ÇW&R*r3fv0¢&V÷&FW&VBFò7F÷à¢Ò¢¥F†R6öÆ÷W"—2öæRÆ–æRæB—Bv2&—F†ÖWF–2ç7vW&–ærF†Rw&öærVW7F–öââ¢ ¢†¦TF—7Æ”Æ–æV"‚–&â„õ$•¤ôåô„¤VF‡&÷Vv‚4U2Fò&V6‚F†R&æBw2F—7Æ’6öÆ÷W"à¢F†R&æB—2FöæTÖVC¢fÇ6RÂfös¢fÇ6VÂ6ò—G2g&vÖVçBvöW2÷VR(i"6öÆ÷'76V ¢æBÆ–æV"fW'FW‚6öÆ÷W"F—7Æ—22F†R†W‚—BFV6öFW2g&öÓ²F†RfövvVBw&÷VæBvöW0¢÷VR(i"FöæVÖ–ær(i"6öÆ÷'76R(i"fövv—F‚föt6öÆ÷&WÆöFVB–âF†RõUEUB6öÆ÷W ¢76RÂ6ò—B6öçfW&vW2öâF†B6ÖRÆ—FW&Â†W‚âöæRFV6öFRV6‚âF†RFöæR7W'fRv0¢Æ–VBFòöæRVæBæBFòæ÷F†–ær—B†BFòÖF6‚Âv†–6‚—2F†Rb"ò"r(	BæBF†Rc¢–â&ÇVRB&—&–U÷vW7F(	BöbÃ3Râ&÷F‚VæG2æ÷r&W÷'B¢¢3ƒ†63¢¢æBF†RvFR6ö×&W0¢F†R&æBw2÷vâ†¦VBVæBv–ç7B66VæRæföræ6öÆ÷&&F†W"F†âv–ç7B†W‚–âV—F†W ¢f–ÆRâ6V6öæB6öç6WVVæ6RÂVç7FFVB–âF†R—FVÓ¢F†R&æBw2f"VæBv2F—7Æ––ær@¢¢¤Âsv–ç7B†÷&—¦öâ6·’öbÂc"¢¢(	B§ÆR¢&æBÂ'&–v‡FW"F†âF†R6·’&V†–æB—BÀ¢v†–6‚—2F†RöæRF†–ærG&VVÆ–æRæWfW"—2â—B—2ÂS’æ÷rÂF‡&VR&VÆ÷r—G26·’à¢Ò¢¥F†RÖöGVÆF–öâ—2fÆö÷&VB–â•„TÅ2Âv†–6‚—2v‡’F†R&æB—2æ÷r6öÇfVBv–ç7BF†P¢f–Ww÷'Bâ¢¢Ô”åõ4”Ä„õTUEDUõ‚Òã¢F†R7&÷vâövFW&ÒÖ’7WB&V&–ærFòöæR—†VÀ¢æBæògW'F†W"ÂæBv†W&RF†R&r7&÷vâ—2—G6VÆb7V"×—†VÂ—B—27W&W76VB÷WG&–v‡@¢†´fÆö÷&&V6†W2’âfÆö÷"öâF†R$U5TÅB&F†W"F†â6öâ¶&–æG2öæÇ’v†W&P¢—†VÇ2&R66&6R(	BCÒG&VVÆ–æR—2C‚FÆÂæB¶VW2—G2v2FòF†RÆ7BW ¢6VçBâÖ–âæ§676W2—†VÇ5W%&F–æg&öÒF†RÆ—fR&VæFW&W"6—¦RæB6ÖW&f–VÆBÂ6ð¢†öæRƒCsR‚÷&BB—G2“L+6Æ×’æBFW6·F÷ƒƒ32‚÷&BBS\+’vWBF†V—"÷và¢ç7vW"–ç7FVBöböæR†&BÖ6öFVBf–VÆC²f–Ww÷'B6†ævR&R×6öÇfW2F†R&æBW†7FÇ’0¢vÆ¶–ærFöW2à¢Ò¢¤ÖV7W&VBBF†R7vâ7FF–öâÂv—F‚F†RfÆö÷"&VÖ÷fVBæBF†Vâ–âÆ6Râ¢¢#ƒöb“ ¢&V&–æw26''’&öG’âv—F†÷WBF†RfÆö÷"F†RÖöGVÆF–öâG&Wr¢£#Söb#ƒ¢¢&W6öÇf&ÆP¢&V&–æw2B—†VÂ÷"Ö÷&RöâF†R†öæRæB¢£#cröb#ƒ¢¢öâF†RFW6·F÷Âv÷'7@¢6–Æ†÷VWGFR¢£ã‚‚¢¢æB¢£ã3‚¢¢âv—F‚—BÂ¢£#ƒó#ƒæB#ƒó#ƒ¢¢Âv÷'7@¢¢£ã‚¢¢ÂæBF†R†÷&—¦öâ&æBw2G&–ævÆR6÷VçB—2Væ6†ævVBBSc"(	BF†RfÆö÷"Ö÷fW0¢fW'F–6W2ÂæWfW"F†V—"çVÖ&W"à¢Ò¢¥F†RvFR—2WfW'’&W6öÇf&ÆR&V&–ærÂæ÷BW&6VçFvR¢¢Â&V6W6R“Rv÷VÆB†fR76V@¢F†RFW6·F÷†ÆböbF†RFVfV7Bƒ#cró#ƒ—2“RR’â—B6'&–W2&÷F‚çF’×f7V—G’wV&G2(	B¢6öÇfW"F†B7F÷VBWGF–ærF–Ö&W"Wv÷VÆB÷F†W'v—6R&W÷'BW&fV7Bg&7F–öâöbæ÷F†–æp¢(	BæBF†—&B76W'F–öâF†BF†R&æBv26öÇfVBv–ç7BD„•2f–Ww÷'BÂ6–æ6RfÆö÷ ¢ÖV7W&VB–â—†VÇ2—2ÖVæ–ævÆW72v–ç7B†&BÖ6öFVBf–VÆBà£bâ¢¤6Æ÷6RF†RæV"f–VÆBv—F‚&ö÷FVBvVöÖWG'’â¢¢FWF–ÂÖg&VR&Vƒ\9sRÇVÖ–ææ6R6–vÖÀ¢"ó#SRÂ&VÆ÷rÖ†÷&—¦öâÂ&W6×ÆVBFò#ƒv–FR’v2¢£2ãrR¢¢–âF†RæV&W7BV'FW"v–ç7@¢&VfW&Væ6W2Bã>(	3ãRS²&RÖÖV7W&R—BgFW"F†RöæR×7W&f6R6÷'&V7F–öââFB¢¦'&öBÖÆVb¢ ¢VÆVÖVçB(	B–â&÷F‚&VfW&Væ6W2F†Rf—7VÂÖ72BWfW'’F—7Fæ6R—2F–6÷BÆVbÂæ÷Bw&70¢&ÆFR(	BæBFVWVâF†R6†FRv—F†÷WBF–ÖÖ–ærF†RfÆV6·2âWfW'’æWr–ç7Fæ6R×W7B&Vv–âöà¢FW'&–âç7W&f6T†V–v‡B‚–&F†W"F†â&÷'&÷v–ærf—7VÂ6Æ÷7W&Rg&öÒâVÆWfFVB6†VWBà£râ¢¤fÆ÷vW"ÆöBÂv–ç7BF†R6÷'&V7FVB&"â¢¢çåv†öÆR×7v&B6‡&öÖfÆ÷vW"¢£ãC’R(i"N(	3bR¢ ¢‚¦æ÷B¢2ãƒ’R’+ræV&W7BV'FW"¢£ãrR(i"2ãR¢¢Âv†–6‚¦—2¢&–v‡B(	B—B—2v†B¢æWfW"×Æ÷vVB&VÖæçB6†÷w2BÖF6†VBÆöö²ÖævÆRççâ¢¤UdU%’dÄõtU"d”uU$R”âD„•2•DTÒ•0¢t•D„E$tâÂ##bÓ‚ÓR'’"ÕsF2†#’â¢¢F†W&R—2æòN(	3bR&#¢æò&VÖæçB†÷Föw&‚—0¢6öÖÖ—GFVBÂ"ã“RFöW2æ÷B&W&öGV6RöâF†RÆçF–ærF†B—2ÂæBF†R&V6—RÆÂf÷W"çVÖ&W'0¢vW&R&VBv—F‚†2&V6ÆÂãSRâ&VB"ÕsF2†#’w2&÷‚&Vf÷&R&W7FF–ærç’öbF†VÒà¢6öÆ÷W"f&–WG“¢VfdâÖgFW"ÖÖVF–âBWVÂà¢¢£CB(i"(šR3¢¢Âw&VVâ‡VR•"¢£Rãl+(i"(šR‚ã\+¢¢Âw&VVâ6‡&öÖ#R¢£3"ã2(i"(šB#b¢¢‡v†B—0¢Ö—76–ær—2F†Rw&W’Öw&VVâæBvÆV6÷W2föÆ–vRÂæ÷BF†R6GW&FVBfÆ÷vW'2’à£‚â¢¤f—‚F†R6†÷B6WB&Vf÷&RG'W7F–ærç’öbF†R&÷fRâ¢¢&—&–U÷6÷WF†6—G2–ç6–FRF†P¢vÆÆW'’F–Ö&W"ƒ#2ãBR÷Vâ6·’’Â6òF†W&R—2W†7FÇ’öæR÷Vâ×&—&–Rf–Wræ@¢&—&–U÷vW7F†2&VVâGVæVBv–ç7B—G6VÆbv—F‚æò6öçG&öÂâÖ÷fR—BÂæBFB6†÷@¢7FæF–ær–â¢§£"ÖW6–2&—&–R¢¢(	BF†R6ÖW&B&—&–U÷vW7F7FæG2R6Ò&VÆ÷rF†R£ ¢VÆWfF–öâF‡&W6†öÆBÂv†–6‚—2v‡’v–ÆB&W&vÖ÷BÂ–VÆÆ÷r6öæVfÆ÷vW"Â&GFÆW6æ¶RÖ7FW"æ@¢ÆRW'ÆR6öæVfÆ÷vW"&VæFW"¦W&ò—†VÇ2–âWfW'’g&ÖRâF†BF‡&W6†öÆB—2FÖ—GFVFÇ’÷W'0¢‡F†R¦öæRw2÷vâæ÷FS¢&&VF–æröbF†RFW'&–âÂæ÷BWf–FVæ6R"’â¢¤Fòæ÷BÖ÷fR7V6–W0¢&WGvVVâ¦öæW2Fò6F—6g’6ÖW&â¢ £’â¢¦&—fW%ö&æ¶—2æ÷B†öæ÷W&–ær—G2÷vâFF6WBâ¢¢¦öæR7V6–f–W26÷&Fw&72Bã.(	3"ãÐ¢æBC(	3SRR6÷fW"v—F‚&&U÷6ö–Åög&7F–öã¢ã²F†Rg&ÖR6†÷w2ã#R6Ò7&–w2öâ&&P¢6ö–Â–âæV"×&÷w2âF†RFF—2&–v‡C²F†R&VæFW&W"—2æ÷B&VF–ær—Bà¢¢¥F†RvVæW&Â†Æb—2DôäR##bÓ‚Ó2¢¢(	B6VR³3¢WfW'’6öÖ×Væ—G’—2æ÷rÆçFVBB—G2÷và¢&V6÷&FVB6÷fW"æÖG&—…ög&7F–öæÂv†–6‚æ÷F†–ær†B&VBâ¢¥F†R—FVÒw2÷vâ&VF–ær—2w&öæp¢–âGvòv—2Â&÷F‚ÖV7W&VB&F†W"F†â&wVVBâ¢¢F†R&æ²—2æ÷B¦öæR¢v—F†–âV–v‡BÖWG&W0¢öbvFW"F†RW‡FVçB—2F†RÖ'6‚†£FÂ&–÷&—G’s’ÂæBF†R6†÷Bw27v&B—2VçF—&VÇ’£@¢æB£âæBF†R7&–w2vW&Ræ÷BFVç6—G’&ö&ÆVÒ(	BçW†%öGfVææBç–×†VööF÷&FÀ¢fÆöF–ærÖÆVfVBVF–72&V6÷&FVBã(	3ãÒFÆÂÂvW&RbãRRöbF†RGVgG2ÆçFVBöâF†@¢G'’&æ²Â&V6W6R&öÆS¢VÖW&vVçFv2ÆÂF†R&VæFW&W"6÷VÆB6VRæBæ÷F†–ær–âF†P¢fö6'VÆ'’6–BÆ–Ç’fÆöG2â¢¤DôäR##bÓ‚Ó2¢¢(	BF†RV&Æ—6†VBfö6'VÆ'’v–æV@¢7V'7G&FVæBF†RÆ6W"&VG2—C²6VR³2âv†B&VÖ–ç2öbF†—2—FVÒ—2F†RÖ–BÖf–VÆ@¢6÷fW&vRVW7F–öâ–â—FV×2(	3rÂæ÷BF†RÆ–Æ–W2æBæ÷B¦öæRà£â¢¤FF—fR'VFvWBâ¢¢F†–âF†R7v&BWFöÖF–6ÆÇ’v†VâÖV7W&VBg&ÖRF–ÖRW†6VVG2¢F‡&W6†öÆBÂ6ò6Æ÷rFWf–6RFVw&FW2–ç7FVBöb7GWGFW&–ærâÖö&–ÆR—2&VÆV6RvFRæ@¢F†RÆ÷r×7V2f–VÆB—27W'&VçFÇ’f—†VBÂ†æB×GVæVB&VGV7F–öâà£â¢¥v–æBâ¢¢öæRG&fVÆÆ–ærvfRæBwW7C²F†R&VfW&Væ6W26†÷r6öÖ&–ærB6WfW&Â66ÆW2à ¤FVfW'&VBÂv—F‚F†R&V6öã¢â¢§VæFW'7F÷'’&VÆ÷r2Ò¢¢v÷VÆBf—‚&VÂæBÖV7W&VB–çfW'6–öà¢†÷W"G&VVÆ–æR&6R—2¦'&–v‡FW"¢F†â—G27&÷vç2(	B&6Rö7&÷vâãƒBv–ç7BF†R†÷Föw&‚w0£ãsBÂv÷'F‚ãcÂ’'WB—B—2–çf—6–&ÆRVçF–ÂF†R7&÷vç27F÷&VF–ær2&÷VÆFW'2âf—†–ær—@¦f—'7BWG2F&²6¶—'BVæFW"–ÆRöb6ÆFRà ¢223r(	BöÆ—6€ ¥W&f÷&Öæ6Rv–ç7BF†R'VFvWG2ÂÆ–6Vç6VBÖ&–Væ6RVF–òÂ&÷fVææ6R×÷WU‚ÂÄ”$U%D”U2æÖF ¦6ö×ÆWFVæW7272ÂÖö&–ÆR&VÆV6RvFRà ¢¢¤FöæR##bÓ‚Ó(	Bæf–vF–öâF†Bw&÷w2v—F‚F†RFF6WBâ¢¢Æ—fR6ö×726†÷w2F†P§vÆ¶W"w26—‡FVVâ×ö–çB†VF–æræBçVÖW&–2&V&–ærâæ÷'F‚×W÷fW'f–WrG&w2ÆæBæBvFW ¦g&öÒF†RÆöFVB†V–v‡Ff–VÆBÂWfW'’7G'V7GW&Rg&öÒ—G26ö×–ÆVBfö÷G&–çBÂæBF†RÖ÷f–ærf—6—F÷ ¦Ö&¶W"g&öÒF†RvÆ¶W"7FFS²&÷F‚÷fW&Æ—2&R–æFWVæFVçFÇ’W'6—7FVçB6WGF–æw2âF†RöÆ@¦æ6†÷"'WGFöç2&VÖ–â2WF†÷&VBf–Wwö–çG2Âv†–ÆRF†R6V&6†&ÆR§V×–æFW‚æ÷rVçVÖW&FW0¦ÆÂsbÆöFVB7G'V7GW&W2æBÆÂf÷W"fW&–f–VB7G&VWBÖ6öçG&öÂ–çFW'6V7F–öç2â–çFW'6V7F–öç2&P¦6ö×–ÆVB–çFò6–FV6'2óÇ66VæSâö–æFW‚æ§6öæg&öÒ7G&VWEö6öçG&öÂæ§6öææBF†RFGVÒÂ6òF†P§&VæFW&W"7F–ÆÂ6öç7VÖW2FW&—fVB66VæRFFæBæò6öçG&öÂ6ö÷&F–æFR—26÷–VB–çFòF†RT’à ¢¢¤FöæR##bÓ‚Ó(	Bg&VRÖfÇ’ÂæBF†RF÷vâ6VVâv†öÆRâ¢¢f†÷"F†R)k"6†—’Æ–gG2F†Rf—6—F÷ ¦öfbF†R&—&–S²76VöæBF÷V6‚B&—6RæBFW66VæC²F†Rg&öÕö&÷fVæ6†÷"'&—fW0¦Ç&VG’–âF†R—"âf÷'v&BföÆÆ÷w2F†RÆöö²F—&V7F–öâæB7G&fR7F—2ÆWfVÃ²†÷&—¦öçFÂ7VV@§66ÆW2v—F‚ÇF—GVFRÂ6VBÂ&V6W6RB3ÒvÆ¶–ær6R&VG22æ÷BÖ÷f–ærâFW'&–à§&VÖ–ç2fÆö÷"(	BF†R7FW×W'VÆRæBF†Rfö÷G&–çB67VÆR&RFVÆ–&W&FVÇ’¦æ÷B¢Æ–VBÀ§6–æ6RF†W’&RW†7FÇ’v†B–÷R6¶VBFòÆVfRâÆVf–ærg&VRÖfÇ’6æ2FòF†Rw&÷VæB&F†W §F†âFW66VæF–æs¢F†RvÆ²F‚w2w&÷VæB×6Öö÷F†–ær—2W‡öæVçF–ÂBB÷2Âv†–6‚g&öÒsRÒ—2£SÒ÷2ÇVÖÖWBföÆÆ÷vVB'’7&vÂà ¥v÷'F‚¶æ÷v–ærf÷"v†öWfW"F¶W2F†RæW‡B6Æ–6S¢¢§F†RW&–Âf–Wr—2F†RÖ÷7B†öæW7B–7GW&Rö`¦†÷rÆ—GFÆR—2'V–ÇBâ¢¢6—‚7G'V7GW&W27&÷72cCÒ&÷‚ÂæBF†RVFvRöbF†RÖöFVÆÆVBw&÷VæB—0§f—6–&ÆRg&öÒ&÷WBSÒWâF†B—2Ãrv÷&¶–ær2–çFVæFVBÂæ÷B'VrFò†–FR(	B'WB—BÖ¶W0¥3R†Ö÷&R7G'V7GW&W2’F†Rö'f–÷W2æW‡BVæ—BÂæB—B&wVW2f÷"âWfVçGVÂ†¦RöW‡FVçBG&VFÖVç@§&F†W"F†â&–vvW"6¶—'Bà ¢¢¤FöæR##bÓ‚Ó(	BF†RÆ–&W'F–W2&R–âF†RvÆ·F‡&÷Vv‚â¢¢Fö72ôÄ”$U%D”U2æÖF7F—2F†P¦VæBÖöæÇ’6÷W&6RöbG'WFƒ²FööÇ2ö6ö×–ÆUöÆ–&W'F–W2ç–FW&—fW2FFöÆ–&W'F–W2æ§6öæÀ¦6†V6²ç6†&RÖFW&—fW2—BæBf–Ç2öâG&–gBÂæBF†RWf–FVæ6RæVÂÆ—7G2ÆÂV–v‡FVVâv—F€§F†V—"&V6öæ–ærà ¢¢¤FöæR##bÓ‚Ó(	BæBGF6†VBFòF†V—"'V–ÆF–æw2â¢¢F†R&÷fVææ6R÷W&VG27V&¦V7G6 ¦æB6†÷w2F†RÆ–&W'F–W2F¶Vâv—F‚F†R'V–ÆF–ær&V–ær–ç7V7FVBÂVæFW"%v†BvRÖFRW†W&R"À¦&WGvVVâF†RGG&–'WFRF&ÆRæBF†R6—FF–öç2âæVÂæB6&B6†&RöæRVçG'’&VæFW&W ¢†Æ–&W'G”VçG'”‡FÖÆ’6òF†W’6ææ÷BG&–gC²F†R6Öö¶R76W'G2W"Ö'V–ÆF–ærf–ÇFW&–ær&F†W"F†à¦6÷VçBÂv†–6‚—2F†R76W'F–öâ÷WGV×–ærÆÂV–v‡FVVâv÷VÆB7F–ÆÂ†fR76VBà ¢¢¤FöæR##bÓ‚Ó(	BF†RFö7VÖVçB—26†V6¶VBf÷"v2â¢¢F†R–çfW'6R6†V6²'Vç2–à¦fÆ–FFRç–†6†V6µöÆ–&W'F–W5ö6÷fW&vV’æBF†W&Vf÷&R–â6†V6²ç6†¢WfW'’†6Rv†÷6P¦fö÷G&–çF÷"÷6—F–öæ—26öæ¦V7GW&Æ×W7B&RæÖVB'’Æ–&W'G’F†B—2¦&÷WBF†@¦7V7B¢ÂÖF6†VBv–ç7BF†RVçG'’w2÷vâ&÷6RâæÖ–ærF†R'V–ÆF–ær—2FVÆ–&W&FVÇ’æ÷@§7Vff–6–VçBÂæBF†R6VÆb×FW7B76W'G2W†7FÇ’F†B66Râ6—‚–çfVçF–öç2–âF†R6öÖÖ—GFVBFFÀ§6—‚6÷fW&VBâF†RWf–FVæ6RæVÂ7FFW2F†RwV&çFVRÂ&V6W6R&öÖ—6Rf—6—F÷"6ææ÷B&V@¦—2æ÷BöæRà ¢¢¤FöæR##bÓ‚Ó(	B6÷fW&vR—2æ÷r76W'FVBÂæ÷B–æfW'&VBâ¢¢VçG&–W26''’¢¤6÷fW'3¢¢¦ ¦f–VÆBöb7G'V7GW&Uö–E²ç†6Uö–EÒæ7V7FFö¶Vç3²6ö×–ÆUöÆ–&W'F–W2ç–'6W2—BÂæ@¦6†V6µöÆ–&W'F–W5ö6÷fW&vVÖF6†W2F†R6Æ–×2v–ç7BF†R&V6÷&G2¢¦–â&÷F‚F—&V7F–öç2¢¢(	Bà¦–çfVçF–öâv—F‚æòFÖ—76–öâf–Ç2ÂæB6òFöW2âFÖ—76–öâv†÷6RfÇVR—2æ÷B6öæ¦V7GW&À¢†W†V×BVæFW"¢¥&W6öÇfVB¢¢Â6òWf–FVæ6R—2ÆÆ÷vVBFò'&—fRv—F†÷WB'&V¶–ærF†RvFR’âF†P¦¶W—v÷&BÖF6‚÷fW"&÷6R—2vöæRÂæBF†R6VÆb×FW7Bw2F—67&–Ö–æF–ær66R—2æ÷râVçG'’F†@§FÆ·2&÷WBfö÷G&–çG2æBÆ6VÖVçBv†–ÆR6Æ–Ö–æræ÷F†–ærâw&—F–ærF†R6Æ–×2F÷vâ–ÖÖVF–FVÇ¦f÷VæBG&–gBF†R†WW&—7F–2v2–æF–ffW&VçBFó¢Ã"FW67&–&VBF†RvÆ¶W"ÖVWF–ær†÷W6R÷6—F–öà¦2–æfW'&VFÖöçF‡2gFW"F†R&V6÷&Bv2F÷væw&FVBFò6öæ¦V7GW&ÆâF†R6†—2&R–âF†P¤Wf–FVæ6RæVÂæBöâF†R&÷fVææ6R6&BÂ&V6W6RwV&çFVRVæf÷&6VBöæÇ’–âF†R&W÷6—F÷'¦—2F†Rf–ÆVB6öæfW76–öâF†—2v†öÆRÆ–æRöbv÷&²W†—7G2Fò7F÷&V–ærà ¢¢¤FöæR##bÓ‚Ó(	BF†R'VÆRæ÷r6÷fW'2v†B'V–ÆF–ær¦—2¢Âæ÷BöæÇ’v†W&R—B7FæG2â¢¢F†P¦6÷fW'3¦fö6'VÆ'’v2fö÷G&–çFö÷6—F–öæ²—B—2æ÷rWfW'’GFW7FVBfÇVR–â&V6÷&B(	@§F†÷6RGvòÂFö7VÖVçFVE÷&ævVÂF†R7G'V7GW&RÖÆWfVÂgVæ7F–öææBö67WçG6ÂæBf÷&ÒãÆGG#æ ¦f÷"ç—F†–ærVæFW"†6Rw2f÷&ÒÂVçVÖW&FVBg&öÒF†RFF&F†W"F†âg&öÒÆ—7B6òæWp¦&6†WG—RGG&–'WFR—2–ç6–FRF†R'VÆRF†RF’—BV'2âF†R&wVÖVçB—2F†B6öæ¦V7GW&À¦&ööe÷G—V—2æ÷Bâ'6Væ6R–âF†RÖöFVÃ¢v&ÆRvWG2'V–ÇBæBF†Rf—6—F÷"6VW2v&ÆRÂæ@¦6öæ¦V7GW&ÂvÆÆW'“¢fÇ6V—2F†R6ÖR6Æ–Ò–âF†RæVvF—fR(	BÆ–âg&öçB&VæFW&VB&V6W6P¦æö&öG’f÷VæBWf–FVæ6RV—F†W"v’Âv†–6‚&VG22F†Rf–æF–ærâf÷W"–çfVçF–öç2vW&R÷vVBà¦FÖ—76–öâæB†BæöæS¢F†R6Vvæ6‚w2ƒ#’6&–â†V–v‡BæB&ööb„Ã‚’æBF†Rw&VVâG&VRw2æ@§F†RvW7FW&âw2vÆÆW&–W2„Ã’’âFVâ6öæ¦V7GW&ÂfÇVW2ÂFVâFV6Æ&F–öç2âF†R6†—2&VB0¦GG&–'WFW2(	B%6Vvæ6‚†÷FVÂ&ööbG—R"(	Bv†–ÆRF†RFö¶VâF†RvFRÖF6†W2¶VW2—G2f÷&Òæ §&Vf—‚à ¢¢¤FöæR##bÓ‚Ó(	BF†R†&B†Æc¢öÖ—76–öç2æB6–×Æ–f–6F–öç2&RVæf÷&6VBâ¢¢F†RÖ—76–æp¦6Æ–ÒGW&æVB÷WBFò&VÆöærFòF†R¦vVæW&F÷"¢Âæ÷BFòF†R&V6÷&B÷"F†RFö7VÖVçBâV6€¦vVæW&F÷'2ö&6†WG—W2ò¥÷&×2ç–æ÷rFV6Æ&W24ôå5TÔTFÂF†Rf÷&ÒGG&–'WFW2—G2g&öÕ÷†6V ¦7GVÆÇ’&VG2ÂæBfÆ–FFRç–†öÆG2WfW'’GG&–'WFR÷WG6–FRF†B6WBFòvVöÖWG'“¦ ¦FV6Æ&F–öâöâF†R&V6÷&B(	B'6VçF†æ÷F†–æröb—B—2'V–ÇB’Â6–×Æ–f–VF†f—†VBFVfVÇ@§7FæG2–â—G2Æ6R’÷"&V6÷&EööæÇ–†&V¦V7FVB&VF–ærÂv†–6‚÷vW2æ÷F†–ær’â'6VçFæ@¦6–×Æ–f–VFæVVB6÷fW'3¦Fö¶VâW†7FÇ’2â–çfVçF–öâFöW2Â6†V6¶VB&÷F‚v—2ÂæBF†P§÷WÖ&·2F†÷6R&÷w2¦æ÷B'V–ÇB¢ò¦æ÷BÖöFVÆÆVBg&öÒF†—2¢6òF†RFÖ—76–öâ&V6†W2f—6—F÷ ¦æBæ÷BöæÇ’&Wf–WvW"âGvVçG’ÖöæRGG&–'WFW27&÷726—‚'V–ÆF–æw2&V6‚æòfW'FWƒ²Ã’æBÃ ¦æ÷r6Æ–ÒF†V—'2ÂæBÃ#(	4Ã#2&RæWrà ¥7v—F6†–ær—Böâf÷VæB&VÂFVfV7BÂv†–6‚—2F†R&wVÖVçBf÷"F†R'VÆR–âöæRÆ–æS¢¢§F†RvöÆ`¥ö–çBFfW&âw2g&ÖRW‡FVç6–öâæB—G2–çFVBvöÆb6–vâ&R&÷F‚Fö7VÖVçFVFæBæV—F†W"—0¦ÖöFVÆÆVBâ¢¢F†R&V6÷&B7VÆÇ2F†VÒg&ÖUöW‡FVç6–öææB6–vævV²ÆöuöGvVÆÆ–æv&VG0¦g&ÖUöFF—F–öææB6–væ²F†R'6VçBGG&–'WFW2&W6öÇfVBFòFVfVÇG2æBæ÷F†–ær6ö×Æ–æVBà¤&÷F‚vW&Rf—†VBF†R6ÖRF’Â–âöæR6Æ–6Rv—F‚F†R&RÖ&¶R(	B6VR3RâF†R7FæF–ærÆ–Ö—B—0§Væ6†ævVBæBv÷'F‚&WVF–æs¢æ÷F†–ær6â6F6‚Æ–&W'G’F¶VâF†Bæö&öG’æ÷F–6VBF¶–ær(	B'W@¦âGG&–'WFR&V6÷&FVBæBæWfW"'V–ÇB—2æòÆöævW"–âF†B6FVv÷'’à ¢¢¤FöæR##bÓ‚Ó(	BæBF†RFVfV7B—Bf÷VæB—2&W—&VC¢F†RvöÆb6–vâ†æw2â¢¢F†R'VÆRw2v†öÆP¦&wVÖVçBv2öæR'V–ÆF–ærÂ6ò†W&R—2F†B'V–ÆF–ærf–æ—6†VBâF†R&V6÷&Bw2g&ÖUöW‡FVç6–öææ@¦6–vævV&Ræ÷rg&ÖUöFF—F–öææB6–væÂF†RæÖW2ÆöuöGvVÆÆ–æv&VG3²F†Rg&ÖR&’æ@§F†R6–væ&ö&B&R&¶VBÂV&Æ—6†VBæBf—6–&ÆS²æBF†R÷Ww2Fö7VÖVçFVF6†—2÷fW"&÷F‚æ÷p¦FW67&–&R6öÖWF†–ærf—6—F÷"6âvÆ²WFòâF†R&VæÖRÆöæRv÷VÆB†fR&VVâF†R6ÖÆÆW"†Æbö`§F†Rf—‚âg&ÖRFF—F–öâv—F‚æòF–ÖVç6–öç2&V6÷&FVBF¶W2F†R&6†WG—Rw2FVfVÇG2(	BGvò×7F÷&W¦&Æö6²7&÷72F†R&—fW"g&öçBÂöâFfW&âF†R6÷W&6W2FW67&–&R2Æ÷r(	B6òF†R&V6÷&B7FFW2F†P¦&’w26–FRÂv–GF‚ÂFWF‚æB7F÷&W’6÷VçBÂæBÃ#BFÖ—G2F†RF‡&VRöbF†÷6RF†B&R–çfVçFVBà¥F†R&ö&B—2FVÆ–&W&FVÇ’&Ææ³¢F†R6–vâ—2Fö7VÖVçFVBæBF†R–çF–æröâ—B—2æ÷B„Ã#R’à ¢¢¤FöæR##bÓ‚Ó(	Bv†B—2æ÷B†W&RÂæBF†Rf–ÆRF†B6–B6ò&V6†–ærf—6—F÷"â¢¢WfW'¦vFR&÷fR6·2v†WF†W"v†BvR¦'V–ÇB¢—2†öæW7BâæöæRöbF†VÒ6÷VÆB&V6‚F†R7G'V7GW&W0§F†—2&ö¦V7B&W6V&6†VBæBFVÆ–&W&FVÇ’F–Bæ÷B'V–ÆC¢FFöW†6ÇW6–öç2æ§6öæ†2†VÆ@¦f÷W'FVVâöbF†VÒÂv—F‚F†RWf–FVæ6RF†BFFW2V6‚öæRÂ6–æ6RF†R66fföÆB(	BæB—B6†—V@¦æ÷v†W&Rf—6—F÷"6÷VÆB&VB—BâF†RWf–FVæ6RæVÂæ÷r6'&–W2F†VÒVæFW"¢¥v†B—2æ÷@¦†W&R¢¢ÂFW&—fVBW"66VæR'’6ö×–ÆU÷66VæRç–v—F‚6—FF–öç2¦ö–æVBÂ–âF†R6ÖRVçG'’F†P¦Æ–&W'F–W2W6RâF†RæVÂ7FFW2ÂæBF†R6Öö¶R76W'G2ÂF†BF†—2—2¢¦æ÷B¢¢Æ—7Bö`¦WfW'—F†–ærÖ—76–æs¢V–v‡Böb&÷Vv†Ç’f÷'G’&W6V&6†VB7G'V7GW&W27FæBÂæBF†RW&–Âf–Wp§&VÖ–ç2F†R†öæW7B–7GW&RöbF†R&W7Bà ¥7v—F6†–ær—Böâf÷VæBF†RöæRf–ÆRv†W&R'VÆRv2æWfW"Væf÷&6VBâWfW'’6÷W&6Uö–F–âF†—0§&ö¦V7B×W7B&W6öÇfR–âFF÷6÷W&6W2ö²æ÷F†–ær&VBF†RW†6ÇW6–öç2f–ÆRw2Â6ò6—FF–öà§F†W&R6÷VÆB†fRæÖVB6÷W&6RF†BæWfW"W†—7FVBâ6†V6µöW†6ÇW6–öç6æ÷r&WV—&W26ÇVr–BÀ¦æÖRÂ7FFVB&V6öâæB6—FF–öâF†B&W6öÇfW2(	BF†R6öÖÖ—GFVBf–ÆR76W2Væ6†ævVBÀ¦æBF†RæW‡BVçG'’6ææ÷B6¶——BâF†RFFRvFRÇ6ò'Vç2&6·v&G2æ÷s¢âVçG'’FF–ær¦'V–ÆF–ærFòƒ3r—26÷'&V7BW†6ÇW6–öâg&öÒƒ3RæBw&öæröæRg&öÒƒ3rÂv†–6‚æð¦6ö×&—6öâv–ç7BF†R&V6÷&G26â6F6‚Â&V6W6RâW†6ÇVFVB7G'V7GW&R†2æò&V6÷&Bà ¤æBF†R6–FV6'2&R&RÖFW&—fVBöâWfW'’6öÖÖ—B†6ö×–ÆU÷66VæRç’ÒÖÆÂÒÖ6†V6¶Â–à¦6†V6²ç6†’âF†W’&R6öÖÖ—GFVB6òF†R6—FRæVVG2æò'V–ÆB7FWÂv†–6‚öæÇ’¶VW2F†P§vÆ·F‡&÷Vv‚æBF†R&6†—fRFövWF†W"–b&V6÷&BVF—FVBv—F†÷WB&V6ö×–ÆR—2vFRf–ÇW&P§&F†W"F†âF—66÷fW'’öâF†RFWÆ÷–VB6—FRâÆÂV–v‡BvW&R'—FRÖ–FVçF–6ÂöâF†Rf—'7B'Vâà ¢¢¤FöæR##bÓ‚Ó(	BF†RF†—&B6FVv÷'’ÂæBF†R&öÖ—6R–ç6–FR—Bâ¢¢F†RVçG'’&÷fRVæG2'§6––ærF†RvF6‚Æ—7B—2FVÆ–&W&FVÇ’æ÷B6†÷vâæBF†B—G2Væ6W'F–çG’&VÆöæw2öâF†R&V6÷&G0¦æB–âF†R÷WâF†Bv2&–v‡B&÷WBF†RöæRöbF†Rf÷W"F†B—25DäD”äræBw&öær&÷WBF†P§F‡&VRF†B&Ræ÷C¢âV×G’Æ÷B6ææ÷B6’§&W6V&6†VBÂæB7F–ÆÂ÷Vâ¢ç’Ö÷&RF†â—B6÷VÆ@§6’§&W6V&6†VBæB'VÆVB÷WB¢âF†Rf÷W"&R7G'V7GW&VBFFæ÷r(	Bv†B—2÷VâÂv†B6WGFÆ–ær—@§v÷VÆB6†ævRÂF÷76–W"ö–çFW"F†B×W7B&W6öÇfRFò6öÖÖ—GFVBf–ÆRæBFòÆ–æR–ç6–FR—BÀ¦æB6—FF–öç2F†B&W6öÇfR÷"6VçFVæ6R6––ærv‡’F†W&R&RæöæR(	BæBF†W’&VæFW"VæFW"¢¥v†@¦—27F–ÆÂâ÷VâVW7F–öâ¢¢Âv—F‚F†R7FæF–æröæR6†—VB§7FæF–ær†W&R¢&F†W"F†âÆ—7FV@¦Ööær'6Væ6W2â6†V6µ÷vF6…öÆ—7FVæf÷&6W2F†Rf–ÆRw2÷vâ6VçFVæ6RÂv†–6‚†BæWfW"&VVà¦Væf÷&6VC¢âVçG'’æÖ–ær6öÖÖ—GFVB&V6÷&B×W7BæÖRF†R6Æ–Ò6''––ærF†RF÷V'BÂæBF†@¦6Æ–ÒÖ’æ÷B&RFö7VÖVçFVFÂ6òF†RF’F†RWf–FVæ6R'&—fW2F†RvFRf–Ç2–ç7FVBöbF†RÆ—7@§V–WFÇ’vö–ær÷WBöbFFRâæ÷F†–ær–âF†R6öÖÖ—GFVBf÷W"v2w&öær(	BF†RfÇVR—2F†RæW‡BVçG'®(	BæBF†RæV"Ö—72—BF–B7W&f6R—2vW7FW&åö†÷FVÆÂv†÷6RÆ–æR7F–ÆÂ&VB2F†÷Vv‚—G0¦'V–ÆBÖFFRVW7F–öâvW&R÷VâF’gFW"F†R&V6÷&B6WGFÆVB—Bâ6VR5DEU2*r3rà ¢¢¤FöæR##bÓ‚Ó(	BF†R6&Bç7vW'2'v2—B†W&Sò"Âv†–6‚—BæWfW"†Bâ¢¢WfW'’vFRæBWfW'§æVÂ&÷fR6·2†÷r7W&RvR&Röb6öÖWF†–ærvR'V–ÇBâæöæRöbF†VÒv26¶–ærF†RVW7F–öâ§f—6—F÷"6·2f—'7BÂæBF†R6&B6÷VÆBæ÷Bç7vW"—C¢÷Wæ§6†2&V@¦6–FV6"æFö7VÖVçFVE÷&ævV6–æ6RF†R6&Bv2w&—GFVâæB6ö×–ÆU÷66VæRç–æWfW"VÖ—GFVBF†P¦f–VÆBÂ6òF†RÆ–æR&VæFW&VB2æ÷F†–æröâWfW'’'V–ÆF–ærf÷"F†RÆ–fRöbF†R&ö¦V7BâF†R†6Rw0¦6Æ–Ò&÷WB—G6VÆbæ÷rG&fVÇ2FòF†R6&B–âF†RGG&–'WFR6†R(	BF†RFFVB7âv—F‚—G0¦6öæf–FVæ6RÂ6÷W&6W2æB&V6öæ–æs²F†R†6Rw26†ævUöæ÷FV–âF†R&V6÷&Bw2÷vâv÷&G3²æBF†P§÷6—F–öâw2&wVÖVçB&V†–æBv‡–öâF†RÆ–æRF†BÇ&VG’6†÷vVB—G26†—âFFW2&–çB0§&V6÷&FVBÂ&V6W6R6WfVâöbF†RV–v‡B7ç2VæBöâ3FV6VÖ&W"öb–V"æBF†B—2&÷VæBÂæ÷@¦F’ç–&öG’w&÷FRF÷vâà ¥F†Rf–ÇW&R6Æ72—2v÷'F‚6''––ær&F†W"F†âF†Rf—ƒ¢¢§Gvò†ÇfW2V6‚6÷'&V7B&÷WBF†V— ¦÷vâ6–FRöbâ–çFW&f6RæV—F†W"7FFW2¢¢âF†R6ö×–ÆW"v26öç6—7FVçBv—F‚—G6VÆbÂv†–6‚—2ÆÀ¦ÒÖ6†V6¶&÷fW3²F†R&V6÷&BfÆ–FFVB6ÆVã²F†RÖ&·Wv2&–v‡Bâ6òF†RFW7B÷Vç2F†R7GVÀ¦6&BæB&VG2v†Bf—6—F÷"v÷VÆB6VRÂæB76W'G2F†RF—67&–Ö–æF–ær—"(	BF†R6Vvæ6€¦Fö7VÖVçFVFÂ†övâw27F÷&R–æfW'&VF(	B&V6W6R6&B7F×–æröæRw&FRöâÆÂV–v‡Bv÷VÆ@¦†fR76VBç’6†V6²f÷"'F†W&R—26†—"âç’÷F†W"6–FV6"f–VÆBF†R&VæFW&W"&VG2—2–âF†P§6ÖR6FVv÷'“²FW7E÷F†Uö6&Eö—5öfVE÷F†Uö6Æ–×5ö—E÷&VæFW'6—2v†W&RF†RæW‡BöæRvöW2à¤öæRvFR6ÖRv—F‚—C¢Fö7VÖVçFVFFFR7âæ÷r÷vW2&W6öÇf–ær6÷W&6RÂÆ–¶RWfW'’÷F†W ¦Fö7VÖVçFVFfÇVRâ7F–ÆÂæ÷BöâF†R6&C¢F†Rfö÷G&–çBw2&V6öæ–ærÂ&V6W6RF†Rfö÷G&–çB†0¦æòF—7Æ’fÇVRF†B—2æ÷B—G6VÆbFW&—fF–öâ(	B6VR5DEU2*r#‚à ¢¢¤FöæR##bÓ‚Ó(	BF†R6–FV6"–çFW&f6R—27FFVBÂæB7FF–ær—Bf÷VæBF†R6V6öæBf–VÆ@¦fÆÆ–ærF‡&÷Vv‚—Bâ¢¢F†RVçG'’&÷fRVæG2v—F‚6VçFVæ6Rv†W&RÖV6†æ—6Ò&VÆöæw2(	B¦ç¦÷F†W"6–FV6"f–VÆBF†R&VæFW&W"&VG2—2–âF†R6ÖR6FVv÷'’¢(	BæBöæRöbF†VÒv2Ç&VG¦'&ö¶VââF†R&÷fVææ6R6&B6·2F†R6–FV6"76WEö—5÷Æ6V†öÆFW&Âf–VÆB6ö×–ÆU÷66VæRç– ¦†2æWfW"w&—GFVâæBÂ6ö×–Æ–ærg&öÒFFöÆöæRÂ6ææ÷C¢6òF†Ræ÷FRFVÆÆ–ærf—6—F÷"§F†—0§6†R—27FæBÖ–âÂæ÷B&¶Rg&öÒF†R&V6÷&B¢†2æWfW"&VæFW&VBöâç’'V–ÆF–ærà ¦6†V6µ÷6–FV6%ö6öçG&7FFW&—fW2F†R–çFW&f6Rg&öÒ&÷F‚†ÇfW2&F†W"F†â6¶–ærV—F†W"Fð¦FV6Æ&R—B(	Bv†B—2VÖ—GFVB6öÖW2öfbF†R6öÖÖ—GFVB6–FV6'2Âv†–6‚ÒÖ6†V6¶Ç&VG’&÷fW0¦&Rv†BF†RFF6WB6ö×–ÆW2FòÂæBv†B—2&VB—266ææVB÷WBöbF†R&VæFW&W"w2÷vâÖöGVÆW2à£#r&VG27&÷726—‚ÖöGVÆW3²öæR&W6öÇfVBFòæ÷F†–ærâF†Rf—‚Ö÷fW2F†Rf7B–ç7FVBöb–çfVçF–æp¦f–VÆC¢Æ6V†öÆFW"—26öÖWF†–ærF†RtÄ"6—2&÷WB—G6VÆbÂ66VæRÖÆöFW&†2&VB—BBÆö@§F–ÖRÆÂÆöærÂæB—Bæ÷r&V6†W2F†R6&BöâF†R&Vv—7G'’VçG'’âF†R66â6VW2&VBF†@¦æÖW2f–VÆBv†–ÆRF†R6–FV6"—2–â†æBæBæ÷BöæRÖFRF‡&÷Vv‚gVæ7F–öâ&ÖWFW"(	Bv†–6€¦—2F†RF—&V7F–öâ&÷F‚fVÇG26ÖRg&öÒÂ6–æ6RF†B—2v†W&RF†Rf–VÆBæÖR—26†÷6VââF†P§&WfW'6RF—&V7F–öâ—2æ÷FRÂæ÷BâW'&÷"ÂæB—B†2öæRf–æF–ær–â—C¢&W6V&6…öæ÷FV—0¦6ö×–ÆVB–çFòWfW'’6–FV6"æB6†÷vâæ÷v†W&RâF†B—2âVç6†—VB6Æ–Ò&F†W"F†âFV@§vV–v‡BÂæB—B&VÆöæw2Fòv†öWfW"æW‡Bv÷&·2öâF†R6&Bà ¢¢¤FöæR##bÓ‚Ó(	BæBF†B6Æ–Ò—26†—VC¢F†R&V6÷&Bw2÷vâ66÷VçB—2öâF†R6&Bâ¢¢F†P¦Æ7BVçG'’VæG2'’†æF–ær&W6V&6…öæ÷FVFòv†öWfW"æW‡Bv÷&¶VB†W&RÂæBF†—2—2F†B6Æ–6Rà¤—B—2F–ffW&VçBfVÇBg&öÒF†RGvò&÷fR—BæBF†RF–ffW&Væ6R—2F†Rö–çC¢æ÷F†–ærv0¦'&ö¶VââF†R6&B6¶VBf÷"æ÷F†–ær—Bv2æ÷Bv—fVâÂF†R6ö×–ÆW"w&÷FRv†B—B6†÷VÆBÂWfW'¦vFRv2&–v‡B(	B¢§F†Rf–VÆB6–×Ç’†Bæò7W&f6R¢¢Âv†–6‚—2†÷r6Æ–ÒvöW2Vç6†—VBv†Và§F†W&R—2æòfVÇBf÷"6†V6²Fòf–æBâWfW'’7G'V7GW&R&V6÷&B6'&–W2öæRÂw&—GFVâf÷"&VFW# §v†B—B7GVÆÇ’76W'G2Âv†–6‚6÷W&6W2F—6w&VRÂv†–6‚v2&VÆ–WfVBæBv‡’ÂæBv†W&RF†P§&V6÷&B—2vV¶W7Bà ¥6†÷vâ¢§fW&&F–Ò¢¢ÂæBF†R6Öö¶R–ç2F†Bv—F‚âW†7B7G&–ær6ö×&—6öâv–ç7BF†R6–FV6 §&F†W"F†â7V'7G&–ærÖF6‚(	Bæ÷FRv†÷6R7V&¦V7B—2F†RÆ–Ö—BöbF†RWf–FVæ6R—2F†RÆ7@§FW‡BöâF†—26&BF†B&öw&Ò6†÷VÆBG&–Ò÷"7VÖÖ&—6RÂæBf—'7B6VçFVæ6Rv—F‚âVÆÆ—6—0§v÷VÆB72ç’Æö÷6W"6†V6²âF†RF—67&–Ö–æF–ær66R—276W'FVB2WfW'—v†W&RVÇ6RöâF†—0¦6&C¢6V6öæB'V–ÆF–ærvWG2—G2÷vâ66÷VçBÂ6òöæRf—†VB&Æö6²öb&÷6Rf–Ç2â6öÆÆ6VB'¦FVfVÇBf÷"F†RÆ–&W'F–W2r&V6öâ(	B6WfW&Â‡VæG&VBv÷&G2÷Vâv÷VÆBW6‚F†R6—FF–öç2öfb£c'f‚æVÂöâ†öæRâF†RVç&VBÖf–VÆBæ÷FR—2F÷vâFò&6†WG—VÂ66VæVæBF&vWEöFFVÀ§v†–6‚&RÖ6†–æW'’f—6—F÷"†2æò&V6öâFò6VRÂ6òF†RÆ—7B—2V×G’öbVç6†—VB6Æ–×2à¥VçFW7FVBæB7FFVC¢F†RV×G’7FFRÂ6–æ6RÆÂV–v‡B&V6÷&G26''’æ÷FRà ¢¢¤FöæR##bÓ‚Ó(	BF†R÷WFÆ–æR6—2†÷r×V6‚öb—G6VÆb—2Wf–FVæ6RÂæBF†R6–ÆVæ6R—26÷VçF&ÆP¦æ÷râ¢¢F†R6&Bw&FVB&ööb—F6‚æB6–Bæ÷F†–ærv†FWfW"&÷WBF†RÆ&vW7B6Æ–Òf—6—F÷"—0§7FæF–ær–âg&öçBöc¢6ö×–ÆU÷66VæRç–6'&–VBfö÷G&–çBæ6öæf–FVæ6VæBG&÷V@¦fö÷G&–çBç6÷W&6W6æBfö÷G&–çBææ÷FVÂ6ò6—‚Æ6V†öÆFW'2F†B6’Ä4T„ôÄDU"–âF†V—"÷và¦f—'7BÆ–æR&V6†VBæö&öG’ÂæBæV—F†W"F–BF†RGvòfö÷G&–çG2F†B&RWf–FVæ6Râ¢¥v2—BF†—0§6†Sò¢¢—26V7F–öâöb—G2÷vâÂ&VæFW&VB'’F†R6ÖR6Æ–Ò&VæFW&W"2F†R&W6Væ6RÆ–æR6òF†P§Gvò6ææ÷B&RVÆ–f–VBF–ffW&VçFÇ’à ¥F†R6&B&–çG2¢¦æòF–ÖVç6–öâ¢¢ÂæB5DEU2*r#‚w2&wVÖVçBf÷"F†B—2Væ6†ævVB(	BF†RöæÇ§&–çF&ÆRfÇVR—2F†RöÇ–vöâÂ&VGV6–ær—BFò&÷‚—2ÖV7W&VÖVçBF†R&V6÷&BFöW2æ÷BÖ¶RÂæ@§F†R6†R—2Ç&VG’–âg&öçBöbF†Rf—6—F÷"BgVÆÂ6—¦Râ6Æ–Õ&÷v&VæFW'2æòfÇVR6VÆÂf÷"¦çVÆÆfÇVRæBF†R6Öö¶R–ç2F†B7&÷72ÆÂV–v‡B'V–ÆF–æw2à ¥GvòF†–æw2v÷'F‚6''––ærâ¢¥F†R6ö×Vç6F–ærF—66Æ÷7W&Rv26VçFVæ6RÂæ÷B'V–ÆB¢£¢F†RÖ76–æp§'VÆRv2æ'&÷vVBFò7F÷F—F†W&–ærFö7VÖVçFVB'V–ÆF–ær÷fW"âVæ¶æ÷vâ4•¤RÂöâF†R&V6÷&FV@§VæFW'7FæF–ærF†BF†R6—¦Rv÷VÆB&R6'&–VBöâF†R6&BÂæBæ÷F†–ær6'&–VB—Bâ¢¤æBF†—2—2F†P§6V6öæBw&FVBÖæB×6–ÆVçB6Æ–Òf÷VæB'’&VF–ærf–ÆR¢¢†Fö7VÖVçFVE÷&ævVv2F†Rf—'7B’Â6ò—@¦†26÷VçB&F†W"F†âF†—&BF—66÷fW&W#¢F†R6Öö¶RÖF6†W2V6‚&V6÷&Bw2w&FVB6Æ–×2v–ç7@§F†R6†—2—G26&BG&w2Âf÷"WfW'’'V–ÆF–ærÂæB&W÷'G2ÆÂV–v‡BöæR6†—6†÷'Bv†Vâ'Vâv–ç7@§F†R&Wf–÷W26öÖÖ—Bâv†B—B6ææ÷B6VR—26†—v†÷6R&V6öæ–ær—2w&öærÂæB—B6ææ÷B&V6‚¦f–VÆBF†R6ö×–ÆW"æWfW"w&—FW2(	B6†V6µ÷6–FV6%ö6öçG&7Fw2Vç&VB&W÷'B—2F÷ÖÆWfVÂöæÇ’Âæ@§v–FVæ–ær—BFòÆVfW2v2&VgW6VB&V6W6RF†R66â6ææ÷BföÆÆ÷rfÇVR–çFògVæ7F–öâà ¢¢¤FöæR##bÓ‚Ó(	BF†R÷VâVW7F–öâ&V6†W2F†R'V–ÆF–ær—B—2&÷WBÂæBF†RæVÂw2&öÖ—6P¦&÷WBF†R6&B—2vFRâ¢¢*r#b6–BF†RvF6‚Æ—7Bw2Væ6W'F–çG’&VÆöæw2öâF†R&V6÷&G2æB–âF†P§&÷fVææ6R÷WæBÆVgB—BVçVWVVC²F†RæVÂ†Æb6†—VBæB—G2VçG'’f÷"F†RöæR5DäD”äp§7G'V7GW&RFVÆÇ2f—6—F÷"Â–â&VæFW&VBFW‡BÂF†B§F†R&÷fVææ6R6&B6†÷w2—B¢âF†R6&B6†÷vV@§F†RFFVB6Æ–Òv—F‚â–æfW'&VF6†—æBæWfW"F†BF†R6Æ–Ò—2G&6¶VB÷VâVW7F–öâ(	Bæ÷@§F†RF—7WFR&V†–æB—B‡F†R'V–ÆFW"w2÷vâ7FFVÖVçBv–ç7B†÷FVÂ6‡&öæöÆöw’’Âæ÷BF†BF†RÆFW ¦FFRv÷VÆBÖ¶RF†RvW7FW&â†÷FVÂ'&æBæWröâF†R66VæRFFRÂæ÷BF†BF†Rw&FR—2†VÆBF÷vâöà§W'÷6RâF†R6&Bæ÷r6'&–W2F†RæVÂw2÷vâVçG'’F‡&÷Vv‚F†RæVÂw2÷vâ&VæFW&W"v—F‚à¦öä6&FfÆrÂf–ÇFW&VB'’÷VåVW7F–öç4f÷&W†7FÇ’2F†RÆ–&W'F–W2&RÂ6òöæRVæ6W'F–çG¦6ææ÷B&RFW67&–&VBGvòv—2âF†R÷F†W"6WfVâ'V–ÆF–æw2&VæFW"æ÷F†–ær&F†W"F†â&V77W&æ6RÀ¦&V6W6R&æò÷VâVW7F–öç2&V6÷&FVB"v÷VÆB&VB26WGFÆVBæBF†RÆ—7B6ææ÷B&öÖ—6RF†Bà¤æB6†V6µ÷vF6…öÆ—7Fæ÷r†öÆG26'&–VEö'–Fò6Æ–ÒF†R6&B&VÆÇ’&VæFW'2(	BF†RF‚—2&V@¦÷WBöb÷Wæ§6'’*r#’w266ææW"(	Bv†–6‚—2F†RF†—&B–ç7Fæ6Röb6VçFVæ6R–âF†—2&ö¦V7@¦FW67&–&–ær7W&f6R—B6÷VÆBæ÷B6VRâFFæBÖW6†W2VçF÷V6†VC²æ÷F†–ærv2&RÖ&¶VBâ5DEU2*rCà ¢¢¤FöæR##bÓ‚Ó(	B'Vær—2§VFvVÖVçB&÷WBFö7VÖVçBÂæBF†RFö7VÖVçB†BæWfW"&V6†V@§F†R6&Bâ¢¢f÷W"6Æ–6W2Œ*rCBÓCr’W7F&Æ—6†VBv†–6‚vR6'&–W2v†–6‚Fö7VÖVçBæBv†BV6€¦öæR6ææ÷B7WÇ“²ÆÂöb—BÆæFVB–âFF÷6÷W&6W2ò¢æ§6öææBæöæRöb—BÆVgBF†R&W÷6—F÷'’à¥6òf—6—F÷"föÆÆ÷v–ær6—FF–öâ&V6†VB&W6VçBÖF’&Æör7F×VB§F–W""+ræV"×&–Ö'§&V6öÆÆV7F–öâ¢v—F‚æ÷F†–ær6––ær—B&W&–çG2F†R¤6†–6vòG&–'VæR¢öbBVwW7B“6''––æp¤¦ö†âFVâ6Föâw2÷vâ66÷VçB(	BF†RÆFFW"ÖFRFòÆöö²Æ–¶Râ÷fW"Öw&FR'’F†RöæRf–VÆBF†@§v÷VÆB†fRW‡Æ–æVB—BâWfW'’6—FF–öâæ÷r6'&–W2F†RFö7VÖVçB—B&W&–çG2v—F‚F†@¦Fö7VÖVçBw2FFRÂ÷"F†Rf–æF–ærF†BF†RvR&W&–çG2æöæRÂæBF†R6÷W&6Rw2÷và¦v†Eö—E÷7WÆ–W6òv†Eö—EöFöW5öæ÷E÷7WÇ–&V†–æBÆFWF–Ç3æà ¥F†RfVÇB—2F†—&B¶–æBæB—B—2v‡’F†RvFR—26†VBF†Rv’—B—2â*r#‚v2f–VÆB&V@¦æBæWfW"VÖ—GFVC²*r3v2f–VÆBVÖ—GFVBæBæWfW"&VBâF†—2öæR¢¦æWfW"VçFW&VBF†P¦–çFW&f6R¢¢Âv†–6‚æV—F†W"F—&V7F–öâöb6†V6µ÷6–FV6%ö6öçG&7F6â6VR(	B6†RVæ–öæVB÷fW §v†B—2VÖ—GFVB6ææ÷B&W÷'Bv†Bv2æWfW"öffW&VBâF†R&÷VæFVB6WB—2F†R66†VÖÂ6ð¦6ö×–ÆU÷66VæRå4õU$4Uôd”TÄEõ5U$d4V'F—F–öç2ÆÂ#"&÷W'F–W2æB6†V6µ÷6÷W&6U÷7W&f6V ¦f–Ç2öâ&÷W'G’–âæV—F†W"†ÆbÂöâf—6—F÷"Öf6–ærf–VÆBæò6ö×–ÆVB6—FF–öâ6'&–W2Âæ@¦öâöæR6—FF–öç2æ§6æWfW"&VG2âFF–ærf–VÆBFò6÷W&6R&V6÷&Bæ÷r6÷7G2öæRÆ–æR6––æp§v†WF†W"f—6—F÷"6VW2—Bà ¥F‡&VRF†–æw2v÷'F‚6''––æs  ¢Ò¢¤'F—F–öâ–ç6–FRf–VÆB—2ÆVv—F–ÖFRæB†2Fò&R&wVVBâ¢¢F†R6&BvWG2F†RFö7VÖVç@¢æBF†RÆ–Ö—G3²—BFöW2æ÷BvWBF†Ræ÷FVöâG&ç67&–&W6VçG'’÷"F†R&VF–ær–à¢6'&–W5öæõöFö7VÖVçFÂ&V6W6R&÷F‚V÷FR'VærçVÖ&W'2ÂæÖRf–ÆW2–âFFöæB&V6÷&B…EE ¢7FGW6W2(	BF†W’&RFG&W76VBFòv†öWfW"&RÖw&FW2F†R6÷W&6Râ7FFVB–â6—FF–öç2æ§6æB–à¢5DEU2*rC‚&F†W"F†âÆVgBÆöö¶–ærÆ–¶Râ÷fW'6–v‡Bà¢Ò¢¤öæR&VæFW&W"f÷"WfW'’6öçFW‡B7F÷VB&V–ær&–v‡BÂæBFW7B6–B6òf—'7Bâ¢¢F†R&W&–çG0¢Æ–æR'&—fVBVæFW"%v†B—2æ÷B†W&R"æBæÖVB¢%F†RöÆBvW7FW&â†÷FVÂ"¢(	B'V–ÆF–ær7FæF–æp¢#Òv’(	Bf–Æ–ær*r#bw276W'F–öâF†B7FæF–ær'V–ÆF–ærÖ’æ÷BV"öâF†BÆ—7BâF†P¢6V7F–öâ¶VW2F†RÆ–â6—FF–öâÂWf–FVæ6S¢fÇ6V6—26òBF†R6ÆÂ6—FRÂæBæWp¢76W'F–öâ–ç2—B6òF†R÷F–öâ6ææ÷BfÆ—&6²à¢Ò¢¤Ö&·W–ç6–FRÆ—7B—FVÒÖ¶W26÷VçF–ær6VÆV7F÷'2w&öærâ¢¢æW7FVBÇVÃæ'&ö¶RGvð¢Vç&VÆFVB76W'F–öç2VçVÖW&F–æræ6—FW2Æ–²F†W’&Ræ6—FW2âÆ–æ÷râ6V6öæBö67W'&Væ6Rö`¢F†—26†Rà ¢¢¤FöæR##bÓ‚Ó(	BF†R÷F†W"F‡&VRFW&—fVBFö7VÖVçG2&Râ–çFW&f6RFöòÂæB&÷F‚6VçFVæ6W0§F†W’vW&R†–F–ærvW&Rw&—GFVâf÷"f—6—F÷"â¢¢F†RVçG'’&÷fR6Æ÷6W2F†R6÷W&6R×&V6÷&@¦F—&V7F–öââv†B—BFöW2æ÷B6Æ÷6R—2F†R¦Fö7VÖVçB£¢6–FV6%÷6†V6—2–â—G2÷vâFö77G&–æp§F†B—B6÷fW'2F†RW"×7G'V7GW&R6–FV6"æBæ÷BW†6ÇW6–öç2æ§6öæ÷"FW'&–âæ§6öæÂ&V6W6P§F†÷6R&†fRF†V—"÷vâ&VFW'2æBF†V—"÷vâ6†W2"(	B6òF†R–çFW&f6Rv†W&R*r#‚Â*r#’æB*r3 ¦V6‚f÷VæBfVÇBv2wV&FVBf÷"öæRFö7VÖVçB÷WBöbf÷W"â6†V6µöFW&—fVEö6öçG&7F6÷fW'2F†P¦÷F†W"F‡&VRÂ&÷F‚F—&V7F–öç2ÂæBf÷VæBGvòöâ—G2f—'7B'Vâà ¥F†Rw&÷VæBæ÷r6—2¢§v†–6‚w&÷VæB¢¢—G2GvVçG’6Æ–×2&R&÷WB(	BF†R7V2w2÷vâ6VçFVæ6R&÷W@§F†Rf÷&·2VG&çBÂ6ö×–ÆVB–çFòWfW'’FW'&–â6–FV6"6–æ6RF†RFW'&–âÆæFVBæB6¶VBf÷"'¦æö&öG’Âv†–6‚—2F†Rf—'7BVW7F–öâf—6—F÷"†2gFW"vF6†–ærF†Rw&÷VæBVæBg&öÒF†R—"âæ@§F†RÆ–&W'F–W2Æ—7B6—2v†BÆ–&W'G’—2¢¦–âF†RFö7VÖVçBw2v÷&G2¢£¢Æ–&W'F–W2æ§6öæ6'&–W0§F†B6VçFVæ6RÂ–æFW‚æ‡FÖÆ6'&–VB†æB×G—VB&‡&6Röb—Bv—F‚æ÷F†–ær†öÆF–ærF†RGvð§FövWF†W"ÂæBF†R&‡&6R—2vöæRà ¥F‡&VRF†–æw2v÷'F‚6''––æs  ¢Ò¢¥F†R&–æF–ær—2FV6Æ&VBÂæ÷B–æfW'&VBÂæBF†B—2F†RFW6–vââ¢¢6–FV6"æÖW2—G6VÆc°¢F†W6R&RfWF6†VB–çFòFö6æB†æFVBVçG'’'’VçG'’Fò&VæFW&W"Â6òF†Rf–VÆBæÖR—0¢6†÷6Vâv–ç7BgVæ7F–öâ&ÖWFW"(	B*r#’w27FFVBÆ–Ö—BâDU$•dTEôDô5TÔTåE6w&—FW2F†P¢&–æF–ærF÷vâæBF†RvFR†öÆG2F†RÖöGVÆRFò—B&÷F‚v—2Â–æ6ÇVF–ær&ö÷B&÷VæBv†W&RF†P¢Fö7VÖVçB†2æ÷F†–ærà¢Ò¢¦–çFW&æÆ—2*rC‚w2'F—F–öâöâ6V6öæBfÖ–Ç’¢¢Â÷fW"v†BF†R6ö×–ÆW"VÖ—G2&F†W"F†à¢÷fW"66†VÖÂ6†V6¶VB–â&÷F‚F—&V7F–öç26òFV6Æ&F–öâ6ææ÷B÷WFÆ—fR—G2f–VÆB÷"&Rw&öæp¢&÷WBF†Rf—6—F÷"â6—FF–öâÆVfW27F’v—F‚6†V6µ÷6÷W&6U÷7W&f6V¢öæRf–VÆBÂöæR÷væW"à¢Òçâ¢¤&VB—2æÖRÂæ÷B&VæFW"(	BæBöæR—27F–ÆÂ÷WG7FæF–ærâ¢§çâ¢¤DôäR##bÓ‚Ó¢ ¢…5DEU2*rS’âW†6ÇW6–öç2æ§6öæw27FæF&FæBVæ6W'F–å÷7FæF&FvW&R&VB–çFð¢Ö÷VçDW†6ÇW6–öç6w2&WGW&âfÇVRÂ&VæFW&VB'’æö&öG’ÂæB&W7FFVB'’†æB–â–æFW‚æ‡FÖÆ°¢&÷F‚&RÖ÷VçFVBfW&&F–Òæ÷ræBF†R&‡&6W2&RFVÆWFVBâ—Bv2F†RW7F–ÖFVB6—¦R(	B¢7FæF&DÖ÷VçFæBGvò&w&‡2(	BæB—Bf÷VæBöæRF†–ærF†RW7F–ÖFRF–Bæ÷C¢F†P¢÷Vâ×VW7F–öç2&‡&6R†BG&–gFVB–çFò¢¦†æB×G—VB6÷VçB¢¢öbF†RvF6‚Æ—7B‚'F‡&VRö`¢F†W6R(
bæBF†Rf÷W'F‚"’Âv†–6‚vöW2w&öærF†RF’f–gF‚VW7F–öâ—2&V6÷&FVBæBv†–6‚æð¢vFR–âF†—2&ö¦V7B6÷VÆB†fR†VÆBâF†R6Öö¶R76W'G2F†R6ö×–ÆVB6VçFVæ6RfW&&F–ÒÂöæ6RÀ¢æBF†BF†R6÷VçB—2vöæRâ¢¥F†RvFRw2Æ–Ö—B—2Væ6†ævVBæBv2æ÷Bv–FVæVB¢£¢&VB—0¢7F–ÆÂæÖRÂF†R66â7F–ÆÂ6ææ÷BföÆÆ÷rfÇVR–çFògVæ7F–öâÂæBF†RæW‡B7V6‚f–VÆ@¢v–ÆÂ&Rf÷VæB'’W'6öâ&VF–ærÖöGVÆRà ¢¢¤FöæR##bÓ‚Ó(	BF†R7FÆVæW72vFR—26†V6²æ÷rÂæ÷B6VçFVæ6Râ¢¢WfW'’'VÆR&÷fP¦77VÖW2F†R6†—VBÖW6‚—2F†RöæRF†R&V6÷&BFW67&–&W2ÂæBæ÷F†–ærv2FW7F–ærF†C¢F†P¦Öæ–fW7B†B6'&–VBâ–çWG5÷6†#SfW"76WB6–æ6RF†Rf—'7B&¶RæBæò6öFRWfW §&V6ö×WFVB—Bâ—BFöW2æ÷rÂf÷"'V–ÆF–æw2æBFW'&–âÆ–¶RÂv—F‚F†R&V6—RÆ—f–ær&W6–FRF†P¦vVæW&F÷'26òF†Rw&—FW"æBF†R6†V6¶W"6ææ÷BG&–gBà ¥GW&æ–ær—BöâÖVçB&Ww&—F–ærv†BF†R†6‚—2÷fW"Â&V6W6RF†RöÆBöæR&W÷'FVBÆÂ6—€¦'V–ÆF–æw27FÆRf÷"&V6öç2F†B6ææ÷BÖ÷fRfW'FW‚(	B&V6÷&B&÷6RÂæB6öç7FçBFFVBFò§6–&Æ–ær&6†WG—Rw2&ÖWFW"ÖöGVÆRâ—Bæ÷r†6†W2F†R§&W6öÇfVB¢&ÖWFW'2ÂF†RFW&—fV@§&÷W'F–W2ÂF†R6öæf–FVæ6RfÆöG2æBF†R'V–ÆFW"w2'—FW3²&ÖWFW"ÖÖöGVÆR6÷W&6R—2÷WBÀ¦&V6W6R—G2VçF—&RVffV7BöâF†RÖW6‚—2F†Rö&¦V7B—B&WGW&ç2âF†RV–v‡B6öÖÖ—GFVB†6†W2vW&P§&R×7F×VBv—F†÷WB&¶RæBF†R&R×7F×—2&÷fVB&F†W"F†â76W'FVC¢'VâF†RæWr&V6—P¦–ç6–FRv÷&·G&VRöbF†RÆ7B&¶R6öÖÖ—BæBF†R–çWBFö7VÖVçG26öÖR÷WB–FVçF–6ÂÂ'V–ÆBç– ¦W†6WFVBÂv†÷6RöæÇ’6†ævR—2FVÆVvF–ærF†R†6‚â6VR5DEU2*rRf÷"F†RgVÆÂ66÷VçBæBF†P¦Æ–Ö—B(	BF†—26ö×&W2–çWG2Âæ÷B÷WGWBÂ6ò†æBÖVF—FVBtÄ"7F–ÆÂ76W2à ¢¢¤FöæR##bÓ‚Ó(	B7G'V7GW&R†2Fò&V6‚F†Rw&÷VæBÂæBöæRFöW2æ÷Bâ¢¢F†RF†—&@¦†öæW7G’vFR–âF†RfÖ–Ç’F†B&Vvâv—F‚Æ–&W'F–W26÷fW&vRâF†R6öæf–FVæ6RÖöFVÂw&FW2v†@¦fÇVR6Æ–×2æBF†RvVöÖWG'’FV6Æ&F–öç2w&FRv†WF†W"—Bv2'V–ÇC²æV—F†W"6â6VR§7G'V7GW&R76VÖ&ÆVBf—F†gVÆÇ’öçFòw&÷VæBF†B—2æ÷BVæFW"—BÂ&V6W6RWfW'’æÖR&W6öÇfW2æ@¦WfW'’fÇVR&V6†W2fW'FW‚âV6‚&6†WG—Ræ÷rFV6Æ&W2v†W&R—BF÷V6†W2F†RFW'&–â(	@¦W&–ÖWFW&BF†R&6RöbF†RvÆÇ2ÂVæG6BFV6²†V–v‡Bf÷"7&÷76–ær(	BæBfÆ–FFRç– ¦ÖV7W&W2F†B÷WFÆ–æRv–ç7BF†R6öÖÖ—GFVB†V–v‡Ff–VÆBâF†RFöÆW&æ6R—2F†RvÆ¶W"w2ã3RÐ§7FW×W'VÆR&F†W"F†âg&W6‚çVÖ&W"Â&V6W6RF†RvFR—26¶–ærF†RvÆ¶W"w2VW7F–öâà ¥F†R6—‚'V–ÆF–æw2ÆæBÂv÷'7B6÷&æW"ãbÒâ¢¥F†Ræ÷'F‚'&æ6‚'&–FvR7FæG2"ãC"Ò6ÆV"ö`§F†Rw&÷VæBB&÷F‚ÆæF–æw2æBæòÆæB–âF†RcCÒ&÷‚&—6W2Fò—G2FV6²¢¢Â6òF†R7&÷76–æp§F÷V6†W2æV—F†W"&æ²âF†R&V6÷&BFV6Æ&W2w&÷VæEö6öçF7C¢&ö6…öæ÷EöÖöFVÆÆVFÂÃ3FÖ—G0¦—BÂæBF†R6†—&V6†W2F†Rf—6—F÷"F‡&÷Vv‚F†R&÷fVææ6R÷WâGvòföÆÆ÷rÖöç2F†—2ÆVfW0¦öâF†RF&ÆRÂ&÷F‚&VÂæB&÷F‚&–vvW"F†â6Æ–6S  ¢Ò¢¥F†R&ö6‚—G6VÆb—2VæGFW7FVBâ¢¢æ÷F†–ærFW67&–&W2†÷rW'6öâv÷Bg&öÒF†R&æ²öçFð¢F†RFV6²Â6òF†Rf—‚—2&W6V&6‚&Vf÷&R—B—2vVöÖWG'’(	BF†Rƒ3Bóƒ3Rv&ç6–æB¶–ç¦–Rw0¢FF—F–öâÆB—2F†R&W7B6æF–FFRÂæB6÷W&6VB6ÆV&æ6Rv÷VÆBæ'&÷r—BFöòÂ6–æ6R¢Æ÷vW"FV6²æVVG2ÆW72&ö6‚à¢Ò¢¥vÆ¶–ærF†RFV6²¢¢…5DEU2*r#’—2æ÷rÖV7W&&Ç’&Æö6¶VB&F†W"F†âÖW&VÇ’Væ'V–ÇC¢WfVà¢v—F‚7W&f6W2Ö&÷fR×F†RÖw&÷VæB–âF†RvÆ¶W"ÂF†W&R—2æ÷F†–ærFò7FWg&öÒâF†RGvò&RöæP¢–V6Röbv÷&²Â–âF†B÷&FW"à ¢¢¤FöæR##bÓ‚Ó(	BF†Rw&÷VæB7FFW2—G2÷vâ6Æ–×2ÂæB7FF–ærF†VÒf÷VæBF†R6V6öæBf–ÆP§v†W&R'VÆRöæRv2æWfW"6†V6¶VBâ¢¢WfW'’†öæW7G’7W&f6R&÷fR&VÆöæw2Fò'V–ÆF–ærâF†P§FW'&–âw&FW2—G6VÆb26&VgVÆÇ’2ç’&V6÷&B(	BFö7VÖVçFVFvFW"Â–æfW'&VFF—f—6–öà¦ÆWfVÇ2öfbW&–öBæ'&F—fRfVWBÂ6öæ¦V7GW&Æ&æ²f6RÂ6†ææVÂ6V7F–öâv†÷6Ræ÷FR6—0¦—B6'&–W2æòWf–FVæ6RBÆÂ(	BæB6–BæöæRöb—BFòf—6—F÷"Âv†–ÆRF—F†W&–ærVæFW"F†P¦6öæf–FVæ6Rf–WrÆ–¶RWfW'—F†–ærVÇ6RÂv†–6‚6†÷w2F†B§VFvVÖVçBW†—7G2æBæ÷F†–ær&÷W@§v†Bv2§VFvVBâF†RWf–FVæ6RæVÂæ÷r6'&–W2¥F†Rw&÷VæB–÷R&R7FæF–æröâ£¢#6Æ–×0§v—F‚F†R7V2w2÷vâf–wW&W2Â—G2&V6öæ–ærfW&&F–ÒæB—G26—FF–öç2¦ö–æVBÂFW&—fVB'¦6ö×–ÆU÷66VæRç–æB&RÖFW&—fVB'’6†V6²ç6†â6†V6µ÷FW'&–åö6Æ–×6†öÆG2F†VÒFòF†P§&V6÷&Bw2'VÆW2(	B6÷W&6W2&W6öÇfRÂFö7VÖVçFVF÷vW2Wf–FVæ6RÂæòÆæBVÆWfF–öâÖ’6Æ–ÒFò&P¦Fö7VÖVçFVB(	BöfbF†R6ÖRVçVÖW&F–öâF†RæVÂ&VæFW'2Â6òF†R6†V6¶VB6WB6ææ÷B7F÷&V–æp§F†RF—7Æ–VB6WBâÃ3"æBÃ32FÖ—BF†R&æ²f6RæBF†R6†ææVÂ&öf–ÆRÂv†–6‚†fR&VVà¦6öæ¦V7GW&Â–âF†RFF6–æ6RF†RFW'&–âÆæFVBæBvW&RFÖ—GFVBæ÷v†W&Rà ¥GvòföÆÆ÷rÖöç2Â&÷F‚&VÂÂ&÷F‚7FFVB–â5DEU2*r3"&F†W"F†âV–WFÇ’G&÷VC  ¢Ò¢¥F‡&VR6Æ–×2&R–æfW'&VFv—F‚æò&V6öæ–ærBÆÂ¢¢(	BF†Ræ÷'F‚æBvW7BF—f—6–öâ6ö–Ç0¢æBF†R6†ææVÂw2âöâ&V6÷&BF†B—2âW'&÷#²†W&R—B—2v&æ–ærÂ&V6W6RF†Ræ÷FR†2Fð¢vò–âFW'&–å÷7V2æ§6öæÂv†÷6R¦'—FW2¢&RF†RFW'&–âw27FÆVæW72†6‚Â6ò6VçFVæ6RF†@¢6ææ÷BÖ÷fRfW'FW‚&R×7FÆW2F†Rw&÷VæBæBæVVG2&¶Râ¢¥F†R6Æ–6RF†Bw&—FW2F†÷6RF‡&VP¢æ÷FW2ÆæG2F†R&¶Rv—F‚F†VÒæBGW&ç2F†R'VÆR–çFòâW'&÷"â¢¢v÷'F‚Fö–ærBF†R6ÖRF–ÖS ¢FW'&–åö–çWG5÷6†7F–ÆÂ†6†W2v†öÆRf–ÆW2Âv†–6‚—2F†RfÇ6R÷6—F—fR5DEU2*rR&VÖ÷fV@¢g&öÒF†R'V–ÆF–ær†6‚'&—f–æröâF†RFW'&–â6–FRà¢Òçâ¢¥F†RÆ–&W'F–W26÷fW&vRvFR6ææ÷B6VRF†RFW'&–â7V2â¢§çâ¢¤DôäR##bÓ‚Ó¢¢(	B6VRF†P¢VçG'’&VÆ÷rà ¢¢¤FöæR##bÓ‚Ó(	BF†Rw&÷VæBç7vW'2FòF†R6÷fW&vRvFRÂæBF†Rf—'7BF†–ær—B6¶VBf÷ §v2â–çfVçF–öâæö&öG’†Bæ÷F–6VBâ¢¢F†RVçG'’&÷fRæÖW2—G2÷vâÆ–Ö—C¢F†RFW'&–âw0¦–çfVçF–öç2&V6†VBF†RWf–FVæ6RæVÂæB7F–VB÷WG6–FRF†RvFRÂ6òÃ3"æBÃ32W†—7FV@¦&V6W6RW'6öâæ÷F–6VBâ6÷fW'3¦æ÷r†26V6öæBæÖW76RÂFW'&–âãÆWö6ƒâãÆ6Æ–ÓæÀ¦VçVÖW&FVB'’F†R6ÖR6ö×–ÆU÷66VæRæw&÷VæEö6Æ–×6F†RæVÂ&VæFW'2g&öÒæBÖF6†VB–â&÷F€¦F—&V7F–öç2(	BâVæ6Æ–ÖVB6öæ¦V7GW&Âw&÷VæBfÇVRf–Ç2ÂæB6òFöW26Æ–Òöâ&Æö6²F†B—0¦æ÷B6öæ¦V7GW&ÂÂöââWö6‚F†B—2æ÷B6öÖÖ—GFVBÂ÷"öâ6Æ–Ò–BF†R7V2FöW2æ÷Bw&FRà ¥6—‚6öæ¦V7GW&Âw&÷VæB6Æ–×3²f—fR†B&÷6R&V†–æBF†VÒ„ÃBÖ–7&ò×&VÆ–VbÂÃRF†RGvò7vÆW2À¤Ã3"F†R&æ²f6RÂÃ32F†R6†ææVÂ6V7F–öâ’æBFF–ærF†V—"6÷fW'3¦f–VÆG2v2&öö¶¶VW–ærà¢¢¥F†R6—‡F‚†Bæ÷F†–ærâ¢¢F†Ræ÷'F‚×6–FR6Æ÷Vv‚w2W†—7FVæ6RæB6÷W'6R&Rw&–v‡Bƒ3Bw3²—G0¦öæRÖfö÷B&VBæBã"ÒRÖföÆB&R–âF†RÖöFVÂ&V6W6R6†ÆÆ÷vW"6†ææVÂ7F÷2&VF–ær0§vFW"ÂæBæòÆ—7BÖVçF–öæVBF†VÒâ¢¤Ã3B¢¢—2æWrâF†—&B6†V6²–âF†—2fÖ–Ç’Fòf–æB6öÖWF†–æp¦öâ—G2f—'7B'Vâà ¥GvòFV6—6–öç2&R76W'FVB&F†W"F†â77VÖVBÂæB&÷F‚&R&÷WBæÖ–ærâF†RWö6‚—2–âF†P§Fö¶Vâ&V6W6RFö72ôUô4…2æÖFfW'6–öç2F†Rw&÷VæBÂ6òÆFW"6†÷&VÆ–æRw2–çfVçF–öç2×W7Bæ÷B&P¦F—66†&vVB'’F†—2öæRw2FÖ—76–öâ(	BF†R6VÆb×FW7B–ç2F†BâæBF†RFW'&–â—2æ÷BÖöFVÆÆVB0¦7G'V7GW&R&V6÷&B6ÆÆVBFW'&–æ¢F†RFöÖ–ç2&R6W&FRö&Æ–vF–öç2ÂæV—F†W"F—66†&vW2F†P¦÷F†W"ÂæBF†R6Æ–Ò6'&–W2—G2FöÖ–æ&F†W"F†âÆVf–ær&VFW"Fò–æfW"—Bg&öÒFö¶Vâw0§6†Râçåv†B—27F–ÆÂ÷WG6–FRF†R'VÆR—2F†Rw&÷VæBw2¢¦öÖ—76–öç2¢¢(	BF†W&R—2æòFW'&–à¦4ôå5TÔTFçâ(	B¢¤DôäR##bÓ‚ÓÂ6VRF†RVçG'’&VÆ÷r¢£²F†Rw&FW27F’&Æö6²ÖÆWfVÂÂ6òÃ3@¦FÖ—G2Ö÷&RF†âF†RFFFöW2à ¢¢¤FöæR##bÓ‚Ó(	BF†Rw&÷VæB†2Fò6’v†B—BFöW2æ÷B'V–ÆBÂæB—B—2æ÷BÖFRöbv†B—@§6—2—B—2ÖFRöbâ¢¢F†RVçG'’&÷fRæÖW2—G2÷vâÆ–Ö—C¢F†R6÷fW&vR'VÆRf—&W2öâ¦6öæ¦V7GW&ÆFrÂ6òâ–çfVçF–öâv2FVÖæFVBæBâöÖ—76–öâÆVgBæòG&6RâF†RFW'&–â†2¦4ôå5TÔTFæ÷r(	BF†R7V2f–wW&W2FW'&–åövVâæ'V–ÆEöf–VÆF7GVÆÇ’&VG2(	Bæ@¦6†V6µöw&÷VæEövVöÖWG'–†öÆG2WfW'’÷F†W"f–wW&RF†RWf–FVæ6RæVÂ6†÷w2FòÖW6ƒ¦ ¦FV6Æ&F–öâöâ—G2&Æö6²Â–â&÷F‚F—&V7F–öç2Âv—F‚'6VçFæB6–×Æ–f–VF÷v–ær6÷fW'3¦ §Fö¶VâW†7FÇ’2F†W’Fòöâ&V6÷&Bà ¢¢¤f—fR7W&f6RÖFW&–Ç2ÂGvòöbF†VÒFö7VÖVçFVFÂFW67&–&R6ö–Âæò7W&f6R–âF†—2ÖöFVÂ—0¦ÖFRöbâ¢¢F†Rw&÷VæBÖW6‚—2öæRV'F‚6öÆ÷W"VFvRFòVFvS²FW'&–åövVâç–'V–ÆG2VÆWfF–öà¦æBæ÷F†–ærVÇ6RâF†B—2F†RvöÆbö–çBvöÆb6–vâöæRFöÖ–â÷fW"(	BF†R&ö¦V7Bw27G&öævW7@¦6†—÷fW"6öÖWF†–ærf—6—F÷"—2V×†F–6ÆÇ’æ÷BÆöö¶–ærB(	BæBÃ3R—2v†W&R—B—2FÖ—GFVBà¥F†R&÷w26’¦æ÷BÖöFVÆÆVBg&öÒF†—2¢Â–âF†R&÷fVææ6R6&Bw2v÷&G2Â÷WBöbF†R&÷fVææ6P¦6&Bw2ÖöGVÆR†&VæFW&W'2÷vV"ö§2övVöÖWG'’æ§6Âæ÷r6†&VB'’&÷F‚7W&f6W2’â6öÆ÷W&–ærw&÷VæB'§¦öæR—2¢¥3b¢¢æBF†RFV6Æ&F–öâ6öÖW2öfbF†RF’F†RvVæW&F÷"&VG2F†RfÇVRà ¥F‡&VRF†–æw2v÷'F‚6''––ærÂÆÂöbF†VÒ&÷WBv†W&RFV6Æ&F–öâÖ’Æ—fS  ¢Ò¢¦FW'&–åö–çWG2ä4ôå5TÔTFÂæ÷BFW'&–åövVâä4ôå5TÔTFâ¢¢â&6†WG—RFV6Æ&W2—G26öç7VÖV@¢6WB&W6–FRF†R6öFRF†B&VG2—BÂæBF†BöæÇ’v÷&·2&V6W6R&×2ÖöGVÆRw2'—FW2&R÷W@¢öbF†R'V–ÆF–ær†6‚âFW'&–åövVâç–vöW2–çFòF†Rw&÷VæBw2†6‚v†öÆRÂ6òF†RÖ&R×7FÆV@¢F†RFW'&–âöâ6–v‡BæB6¶VBf÷"&ÆVæFW"&¶RFòÆæB6öç7FçBâ—B6—G2&W6–FRF†P¢FVç–Æ—7B–ç7FVB(	B6ÖRf–ÆRÂ6ÖR7V&¦V7B(	BæBFW7EöFV6Æ&VE÷FW'&–å÷&VG5ö&U÷&VÅ÷&VG6 ¢66ç2F†RvVæW&F÷"f÷"&VBöbWfW'’FV6Æ&VB¶W’Âv†–6‚—2v†B6òÖÆö6F–öâv÷VÆB†fP¢&÷Vv‡Bà¢Ò¢¥F†R¶W’—2ÖW6†&V6W6RvVöÖWG'–—2F¶Vââ¢¢–âvVô¥4ôâF†Bv÷&B—2F†R6ö÷&F–æFW3°¢7G&—–ær—Bg&öÒF†R†6‚v÷VÆB†fRF¶VâWfW'’G&6VB&æ²Æ–æR÷WBöbF†Rw&÷VæBw0¢7FÆVæW72âFW7Bw&—GFVâf÷"*r3Bw2W'÷6R&VgW6VB—BöâF†Rf—'7B'Vâà¢Ò¢¦&W7FFVEö–åö6öFV—2f÷W'F‚7FFRæBöæÇ’F†Rw&÷VæBæVVG2—Bâ¢¢F†RvFW"ÆæRw2¦W&ð¢æBF†R&æ²w2V6RÖ÷WB&Rw&—GFVâ–âF†R7V2æB6W&FVÇ’w&—GFVâ–â—F†öââF†RÖW6€¢w&VW2v—F‚F†VÒæBFöW2æ÷B&VBF†VÓ²F†B—2v&æ–ærFòv†öWfW"VF—G2F†RvVæW&F÷"&F†W ¢F†â6fVBFòf—6—F÷"Â6ò—B6'&–W2æòÖ&¶W"â¢¥v†B†VÆBF†RGvò†ÇfW2FövWF†W"v0¢æ÷F†–ærÂæB6–æ6R##bÓ‚Ó…5DEU2*r3b’—B—2FW'&–åö–çWG2å$U5DDU6¢£¢V6‚&W7FFVÖVç@¢æÖW2F†R†Æb—Bw&VW2v—F‚(	Bf–wW&R–âF†R†V–v‡Ff–VÆBF†R&¶Rw&÷FRÂæ÷F†W"f–wW&R–à¢F†R6ÖR&Æö6²Â÷"Æ–æRöbFW'&–åövVâç–(	BæB6†V6µ÷&W7FFVEöw&VVÖVçF6ö×&W2F†VÒà¢7v—F6†–ær—Böâf÷VæBF‡&VRf–wW&W2Ö¶–ærF†R&öÖ—6RVæFW"F†Rw&öær7FFS¢WfW'’F—f—6–öâw0¢&æµö7&W7EögF&W7FFW2æV%ögFæBv2FV6Æ&VB&V6÷&EööæÇ–Âv†–6‚÷vW2æ÷F†–æræB6·0¢æ÷F†–ærâÆÂ6WfVâw&VRFöF“²F†RfÇVR—2F†BF†RæW‡BVF—BFòF—f—6–öâÆWfVÂ6ææ÷BÆVfP¢F†RæVÂ6†÷v–ærF†RöÆB7&W7Bà ¢¢¤FöæR##bÓ‚Ó(	BF†R7VÒVæFW"f—fR'V–ÆF–æw2—2FFæ÷rÂæB—Bv2f—fR&w&‡2â¢¢WfW'¦vFR&÷fR6·2v†WF†W"6Æ–Ò—2†öæW7C²F†—2öæR6·2v†WF†W"F†R&—F†ÖWF–2&VæVF‚¦6ö÷&F–æFRv2WfW"&VFöæRâf—fRÆ6VÖVçG2&RF†R6ÖR6öç7G'V7F–öâ(	BÖöFW&â–çFW'6V7F–öà¦6VçG&Röfb÷Vå7G&VWDÖÂ†ÆbâƒgBÆGFVB7G&VWBFòF†R¶W&"ÂæÖVBf6Röâ—B(	Bw&—GFVà¦÷WBöæ6RW"&V6÷&BÂv—F‚F†RçVÖ&W""ã"V&–ær–âf—fR&w&‡2æBæòf–ÆRà¦FF÷G&6W2÷7G&VWEö6öçG&öÂæ§6öæ†öÆG2F†RÖöGVÆRæBF†R6öçG&öÂöæ6S°¦6†V6µ÷÷6—F–öåöFW&—fF–öç6&V'V–ÆG2WfW'’Æ6VÖVçBg&öÒF†VÒæB†öÆG2F†R&W7BFò¦FV6Æ&F–öã²æBF†R7V×2vW&RÆÂ6÷'&V7BÂv†–6‚—2F†RÆV7B–çFW&W7F–ær'Bà ¥F‡&VRF†–æw2v÷'F‚6''––æs  ¢Ò¢¤6²F†RÆ6VB6†RÂæ÷BF†R6ö÷&F–æFRâ¢¢&V6÷&Bw2÷6—F–öâ—2F†Rfö÷G&–çBöÇ–vöâw2÷và¢÷&–v–âÂ6òf6FR&V&–ærGW&ç2—BöfbF†R6÷&æW"F†R6Æ–Ò—2&÷WB(	BF†Rw&VVâG&VRw0¢V7F–ær6—G2#BãBÒg&öÒ—G2–çFW'6V7F–öâv†W&RF†R6Æ–Ò6—2"ã"â6†V6²6ö×&–æp¢6ö÷&F–æFW2Fò¶W&'276W26÷'&V7FÇ’Æ6VB'V–ÆF–æræB&÷FFVBÖ÷WBÖöbÖ—G2ÖÆ÷B'V–ÆF–æp¢v—F‚WVÂ6öæf–FVæ6RÂ6òF†R6VÆb×FW7Bw2F—67&–Ö–æF–ær66R—2öæR'V–ÆF–ærV&–ærGv–6Rà¢Ò¢¤F—6w&VVÖVçB–÷R6ææ÷B7BöâvWG2&V6÷&FVBæBÆVgBâ¢¢F†RƒgBòcbgB7G&VWBv–GF€¢†Fö72õ$U4T$4‚ö†övå÷7F÷&RæÖF*rR’6B&V6W6R6WGFÆ–ær—BÖVçBf—fR†æB×&VFöæR7V×2â—B—0¢æ÷röæRVF—BæB&–çFVBÆ—7Böbv†–6‚'V–ÆF–æw2Ö÷fVBÂ"ã2ÒV6‚à¢Ò¢¥w&—F–ærF†R6öçG&öÂF÷vâf÷VæBGvò6ö÷&F–æFW2f÷"öæR§Væ7F–öâ¢¢(	B6æÂæB¶–ç¦–RÂfW&vV@¢÷fW"f—fRõ4ÒæöFW2f÷"F†RvV÷&VfW&Væ6RæBF‡&VRf÷"F†R'&–FvRÂ2ã‚Ò'BâF†R'&–FvR—0¢æ÷BÖ÷fVC¢—G27â—2F†RF—7Fæ6R&WGvVVâF†RG&6VB&æ·2Æöær—G26VçG&VÆ–æRÂF†BF—7Fæ6P¢—2ÖW6‚&ÖWFW"ÂæB&RÖFW&—f–ær—B6·2f÷"&¶RâF†Rf&–æ6R—2FV6Æ&VBæB6†V6¶V@¢–ç7FVBâ6VRFö72õ$U4T$4‚÷7G&VWEöÖöGVÆUóƒ3æÖFà¢Ò¢¥F†R6öçG&öÂö–çBF†Rv†öÆRvW7BF—f—6–öâ—2ÖV7W&VBg&öÒ—2–ç6–FR&Æö6²¢¢ƒ##bÓ‚ÓÀ¢5DEU2*rC"“¢†F†v’„—2S"ãBÒvW7BöbF†R6æÂ7G&VWB6÷'&–F÷"æBw&–v‡BsR#ã"ÒvW7BÀ¢&÷F‚v—F‚&Æö6²#‚w2çVÖ&W"&–çFVB7&÷72F†VÒâsR—2FGVÒt5Â6òF†RW‡÷7W&R—2&–6V@¢ƒRãÒöb÷&–v–âÖ÷fVÖVçBÂ$Õ2Væ6†ævVB’æBVWVVB&F†W"F†âF¶Vâ(	BF÷F–ær—B&RÖFW&—fW0¢WfW'’6ö÷&F–æFRæB7FÆW2WfW'’ÖW6‚â6†V6µ÷7G&VWEöÖöGVÆVf–Ç2F†RF’V—F†W"6÷'&V7F–öà¢ÆæG2Â&V6W6RF†Rf–æF–ærw2–çWG2v÷VÆB†fRÖ÷fVBà¢Ò¢¤æB&RÖfWF6†–ærF†R6öçG&öÂF†RæW‡BF’6–Bv†–6‚öbF†RGvòv2&–v‡B¢¢ƒ##bÓ‚ÓÀ¢5DEU2*r3’’â§Væ7F–öâ—2F†RæöFW26†&VB'’F†RGvòæÖVB§7W&f6R&öGv—2£²Gvòöb¶–ç¦–P¢æB6æÂw2f—fR6öÖÖ—GFVBæöFW2&R&–¶Wv’7&÷76–æw2ÂæBF†R÷F†W"F‡&VR&RF†R'&–FvRw0¢&VF–ærFò6VçF–ÖWG&RâF†R6ÖR–æ6ÇW6–öâ†BWB&æFöÇ‚æB6æÂBãCBÒ÷WBÂv†–6‚Ö÷fV@¢F†RvW7FW&â†÷FVÂâFööÇ2÷&VfWF6…ö6öçG&öÂç–&RÖFW&—fW2§Væ7F–öâg&öÒF†R7G&VWBæÖW2æ@¢&RÖfWF6†W2F†R&V6÷&FVBæöFR–G3²—BæVVG2F†RæWGv÷&²Â6ò—B—2öâÖFVÖæBæBæ÷B–à¢FööÇ2ö6†V6²ç6†à ¢223(	B6ö×ÆWFR§VÇ’ƒ3R'V–ÆF–ær–çfVçF÷'’+r¢¥$T4ôä4”ÄTB##bÓ‚ÓB¢  ¥F†R÷væW"×7WÆ–VB&V6öç7G'V7F–öâ7V6–f–6F–öâW7F&Æ—6†W2&öGV7F–öâF&vWBöb¢£ccR&öög2¢£ £S&–æ6—ÂögVæ7F–öæÂæBSBæ6–ÆÆ'’ÂF—7G&–'WFVB6÷WF‚3sòvW7B3Ròæ÷'F‚Sòf÷'@£âF†RGW&&ÆRÖ7FW"ÆVFvW"—2FF÷&V6öç7G'V7F–öâóƒ3Uö'V–ÆF–æuö–çfVçF÷'’æ§6öæ²—B&W6W'fW0§F†R–æFWVæFVçFÇ’&V6öæ6–Æ&ÆRfÖ–Ç’æBF—7G&–7BÖG&–6W2æBW‡Æ–6—FÇ’6W&FW2vw&VvFP¦ÖöFW&FR6öæf–FVæ6Rg&öÒ–çFW'&WF—fRW"Ö–ç7Fæ6RÆ6VÖVçBâ¢¥F†Bf–ÆR—2F†RD$tUBæBFöW0¦æ÷BÖ÷fRâ¢¢v†B†2&VVâ'V–ÇBv–ç7B—BÂv†B—2ÆVgBæBv†W&R—B6âvò&RFW&—fVB(	@¦FööÇ2÷&V6öæ6–ÆUóccRç–(i"FF÷&V6öç7G'V7F–öâóƒ3UóccU÷&ööe÷&öw&ÖÖRæ§6öæÂ&RÖFW&—fVB'¦FööÇ2ö6†V6²ç6†öâWfW'’6öÖÖ—B…BÔ’à ¢¢¥7FæF–ær##bÓ‚ÓC¢#3"‡—6–6Â&öög2g&öÒ#C"&V6÷&G2â&VÖ–æ–æs¢C32¢¢(	B6÷WF‚#sÀ¥vW7B“BÂæ÷'F‚c’Âf÷'BâöbF†÷6RC32Â¢£R†fRÖöFVÆÆVBÂÆGFVBw&÷VæBFò7FæBöâ¢¢æ@£3#‚Fòæ÷C¢#–âF†RGvò&Æö6·2F†RÆBÖöGVÆR&VgW6W2f÷"vçBöb6÷WF‚vFW"7G&VWB6öçG&öÂÀ£3R†VÆB'’F†RvW7B&V6—Rw2÷vâW‡FVç6–öâvFRÂæB#s2–âw&÷VæBv—F‚æò6öÖÖ—GFVB7G&VW@¦6öçG&öÂBÆÂ(	BV7Böb7FFRÂ6÷WF‚öbv6†–æwFöâÂvW7Böb6Æ–çFöâÂæBF†Rv†öÆRæ÷'F€¤F—f—6–öâÂv†–6‚F†Rw&–B6÷fW'2'’æ÷BöæR&Æö6²âF†RccR×&ööb&öw&ÖÖR—2¢¦6÷fW&vRÖ&÷VæBÀ¦æ÷B&V6—RÖ&÷VæB¢£²*r3’—2v†B7FæG2&WGvVVâ—BæBF†RæW‡BGvò‡VæG&VB&öög2à ¥6—‚fÖ–Ç’F&vWG2&RÇ&VG’W†6VVFVB'’Wf–FVæ6R(	B3Â“"ÂC"ÂsÂsBæBsRÂæ–æR&öög2(	@§v†–6‚F†RÆVFvW"&W÷'G2&F†W"F†â†–FW2âFö7VÖVçFVB&ööb—2æWfW"&VÖ÷fVBFò&÷FV7B¦fÖ–Ç’6Â6òF†Ræ–æR6öÖR÷WBöbF†R–çfVçFVBfÖ–Ç’v—F‚F†RÖ÷7B6Æ6²à ¢Ò¢¥†6RFöæS¢¢¢C‚f—6–&Ç’FvvVBæöç–Ö÷W26÷WF‚F—f—6–öâ&öög2–âf—fRÖ—†VB&Æö6·>(	CC ¢&–æ6—ÂögVæ7F–öæÂæBV–v‡Bæ6–ÆÆ'’â&W&öGV6–&ÆR&V6÷&G2æBfÆvvVB&Wf–WrtÄ'2&P¢FW&—fVBg&öÒF†R&6VÂ&V6—Rv—F†÷WB&ÆVæFW"æB6†V6¶VBöâWfW'’6öÖÖ—Bà¢Ò¢¥†6R"Æææ–ærGfæ6VB–â&ÆÆVÃ¢¢¢&Wf–WvVBÂæöâ×&VæFW&VB&V6—W2æ÷r&W6W'fRæ÷F†W ¢ƒB6÷WF‚&öög2ÂSRvW7B&öög2æBcæ÷'F‚&öög2v—F†÷WB÷fW&G&v–ærç’fÖ–Ç’F&vWBâF†P¢6÷WF‚&V6—R—26öÆÆ—6–öâÖ6†V6¶VBv–ç7B&÷FV7FVBæÖVB6—FW3²F†Ræ÷'F‚6WBw2cfö÷G&–çG0¢7F’öâF†R7W'&VçBG'’FW'&–ââF†RvW7B&V6—RFVÆ–&W&FVÇ’vFW23R&öög2VçF–ÂF†Rv÷&Æ@¢W‡FVæG2FòÆö6ÂRÓsÒÂæBF†R&VÖ–æ–ær“×&ööbæ÷'F‚72v—G2f÷"Væ–f–VBFW'&–âÀ¢‡–G&öÆöw’Â6öÆÆ—6–öâÂfÆ÷&Â7G&VWG2æBÖ6÷fW&vRFòâ³scÒâF†W6R&R&öGV7F–öâÆç2À¢æ÷BFFVB66VæR6÷VçC²W†—7F–ær×&ööb&V6öæ6–Æ–F–öâ6öÖW2f—'7Bà¢Ò¢¤FöæR##bÓ‚Ó#¢¢¢ÆÂsb&RÖW†—7F–ær&V6÷&G2&R&V6öæ6–ÆVBFò‡—6–6Â&ööbVæ—G3²'&–FvW2À¢–&G2ÂÆ—6FW2Â6öç7G'V7F–öâ6—FW2æB6ö×÷VæG2æòÆöævW"Ö¶R&V6÷&B6÷VçB&÷‡’à¢Ò¢¤FöæR##bÓ‚Ó#¢¢¢F†RFW'&–â×6fRc×&ööbæ÷'F‚–æ—F–Â&6VÂ—2f—6–&ÆRæB6†V6¶VBà¢ÒfW&–g’F†Rö67W–VBvW7Böæ÷'F‚6WGFÆVÖVçBW‡FVçB&Vf÷&RW‡FVæF–ærFW'&–ââF†RVæÆ&vVBÆ@¢—2æ÷BF†R6ÖRF†–ær2'V–ÇBfö÷G&–çBÂæBBÆV7BCRRöb—B&VÖ–ç27'6Rö÷Vâà¢Ò–×ÆVÖVçBF†R3RfÖ–Ç’&6†WG—W2æB#S²f—6–&ÆR6öÖ&–æF–öç2Â&WÆ6–æ~(	Fæ÷B6–ÆVçFÇ¢&öÖ÷F–æ~(	GF†R&Wf–WrÖ76–æw2à¢Ò÷VÆFR&VÖ–æ–ærF—7G&–7B&6VÇ2FòF†R&V6öæ6–ÆVBF&vWBÂF†VâFBFW'&–â×6×ÆV@¢f÷VæFF–öç2Â–&G2æB&÷2âæò6W&FR6öÆÆ—6–öâÆæRà ¥6VRFö72õ$U4T$4‚÷&V6öÖÖVæFVEö–æf–ÆÅóƒ3RæÖFÀ¦Fö72õ$U4T$4‚óƒ3UöW†—7F–æu÷&ööe÷&V6öæ6–Æ–F–öâæÖFÀ¦Fö72õ$U4T$4‚óƒ3UöfÖ–Ç•ö&6†WG—Uö7&÷77vÆ²æÖFÀ¦Fö72õ$U4T$4‚÷†6S%÷6÷WF…ö6÷&UöæEöÖ—†VBæÖFÀ¦Fö72õ$U4T$4‚÷vW7EöF—f—6–öåö–æf–ÆÅóƒ3RæÖFÂæBÆ–&W'G’Ãƒà¥F†Ræ÷'F‚æÇ—6—2—2Fö72õ$U4T$4‚óƒ3Uöæ÷'F…öF—f—6–öåöW‡FVçEöæEö–æf–ÆÂæÖFà ¢223‚(	BÖ–ÆW7FöæR ¥vöÆbö–çB6ÇW7FW"²6÷WF‚vFW"&Æö6²B„Æ6ÆÆ^(	46Æ&²’âF†Rf—'7BFW7Böbv†WF†W"F†P¦&6†WG—R&ö6‚7GVÆÇ’—2f÷"—G6VÆbà ¢22ÆFW"(	BF†RDB&öö` ¤6V6öæB66VæRƒƒ32÷"ƒ3’W†W&6—6–ærF†RWö6‚Ö6†–æW'’ÂF†R&Uöf—&U÷c7&÷77vÆ²Âæ@¦ÖævW"&÷rv—F‚F†R6†ævVÆör6FVæ6R'Vææ–ærà ¢ÒÒÐ ¢22v÷&¶–æræ÷FW0 ¢ÒFööÇ2ö6†V6²ç6†&Vf÷&RWfW'’6öÖÖ—Bâ—BF¶W2VæFW"6V6öæBà¢ÒöæR6ö†W&VçBVæ—Böbv÷&²W"'Vâà¢Òw&—F–ær7V&vVçG2V6‚vWBF†V—"÷vâv—Bv÷&·G&VRà¢ÒWFFR5DEU2æÖF–âF†R6ÖR6öÖÖ—B2F†Rv÷&²ÂæB¶VW—BVæfÆGFW&–ærà¢ÒæòÖöFVÂ–FVçF–f–W'2–â&Wò'F–f7G2à  ¢222BÓ“sB(	B–ÖvRS6öçF–çVF–öâ&VBƒ##bÓ’Ór ¥BÓ“s27Æ—B–âÆ6S¢BÓ“sB&VG2355Ôu•”¢Ó”£V²BÓ“sR¶VW2F†RGvVÇfP§&VÖ–æ–ærf–ÆÆVBÆVfW2æB&Ææ²$‚âÆÂ3Æ–æW2&R&V6÷&FVBÂ6—‚F÷FÇ2&VÖ–à¦W‡Æ–6—FÇ’Vç&W6öÇfVBÂæBF†RF‡&VRö67WF–öâfö÷F–æw26Æ÷6RBbÂ‚æB"à¤æòf–Æ&ÆRÆVgB×6†VWB÷VÆF–öâ¶W’7W÷'G2—&–ærâF†RvRf–ÆRæ@¦6Vç7W2FöÖ–â$TDÔR&W6W'fRF†R7&÷vVöÖWG'’ÂÇFW&æF—fW2æBgVÆÂ6æF–FFP¦Æ—7C²æòƒ3R&W6–FVçB÷"w&FR6†ævW2à  ¢222BÓ“sb(	B÷Vâ"&V6öæ6–Æ–F–öâ…"3C ¤–çFVw&FVBBÓ“cB„%õR’æBBÓ“cb…r’v—F†÷WB&WÆ6–ærÆFW"FWbv÷&²âF†Rf÷W"V&Æ–W"6ö×WF–ærvR&VF–æw2&R&WF–æVBfW&&F–ÒVæFW"FF÷&W6V&6‚ö6Vç7W5óƒC÷6V6öæE÷&VF–æw2öÂv—F‚÷&–v–æÂ6öÖÖ—G2Â6öçFVçB†6†W2æBæÖR6ö×&—6öç2âF†RrvRçVÖ&W'2&RW†6ÇVFVBg&öÒ&÷F‚†VBæB–FVçF—G’&VFW'2âBÓ“c’æBBÓ“s&W—"6÷W'FW7’×F—FÆR'6–æræBF†RÆ÷–B–FVçF—G’7Æ—Bâ6VRFö72õ$U4T$4‚ö÷Vâ×"×&V6öæ6–Æ–F–öâÓ##bÓ’Ó‚æÖFf÷"V6‚öÆB.(	—2F—7÷6—F–öâæBF†RVç&W6öÇfVB&W6V&6‚F—6w&VVÖVçG2à ¢22BÓ“sr(	B6öçF–çVF–öâ•5¢F†—'G’VçG&–W2Âf÷W"Vç&W6öÇfVBF÷FÇ0 ¤–ÖvRS"—2&VB–âvW2ó355Ôu•”¢Ó•5æ§6öæ¢3ö67W–VBDõDÂVçG&–W2À¦ÆÂ6WfVâ–æGW7G'’6öÇVÖç2ÂæBF†R÷F†W"f—6–&ÆR&Æö6·2âf÷W"F÷FÇ2&VÖ–âçVÆÀ¢†Æ–æW2RÂrÂ2Âb’Âv—F‚f—7VÂÇFW&æF—fW2âF†R#b&VF&ÆRF÷FÇ27VÒFòC’à¤öæÇ’öæR6öÖ&–æF–öâöbF†÷6RÇFW&æF—fW2&V6†W2F†Rw&—GFVâsRÂ'WB&—F†ÖWF–0¦—2æ÷B&VF–æs²æöæR—2f–ÆÆVBâw&–7VÇGW&RÂ6öÖÖW&6RBÂ–æÆæBæf–vF–öâ¦æB&öfW76–öç2b6Æ÷6R–æFWVæFVçFÇ’âf÷W"6ÆV"ÖçVf7GW&–ærVçG&–W2Ç6ò7VÐ§Fò—G2fö÷F–ærBÂ'WBf–gF‚6†÷'BW&–v‡BÖ&²7F—2Vç&W6öÇfVBâ6ÖÆÂÆö÷ ¦&W6–FR6ÆfRÖ6öÇVÖâ'VÆR—2Vç&W6öÇfVC²F†Rö'67W&VB66†ööÂöÆ—FW&7’VFvR—2Vç&VBà ¥&–çFVB##B„¤Ò’6†&W23†÷W6V†öÆG2æBsRV÷ÆRÂ'WBöæÇ’"öbF†R#`§&VF&ÆR&–v‡BÖ†æBF÷FÇ2ÖF6‚—G2–æFWVæFVçFÇ’6öÖÖ—GFVB†÷W6V†öÆB6WVVæ6Rà¥F†B6ö–æ6–FVçFÂGvòÖ¶W’ÖF6‚—2&VgW6VBâ&–çFVB#b„DB’†2sRV÷ÆR'W@£3†÷W6V†öÆG2æBf–Ç2F†R6÷VçBâF†R6†VWB7F—2Vç—&VBæB76–vç2æòæÖW0¦÷"ö67WF–öç2Fòƒ3R&W6–FVçG2âÖV7W&VB6öÇVÖâ&æG2Â7&÷&÷†W2æBF†P¦–ç7G'VÖVçBw2G'Væ6FVBÖ&öG’Æ–Ö—FF–öâ&R&V6÷&FVBöâF†RvRà ¤w&÷W2æ÷r†2F‡&VR6öçF–çVF–öç2&VBÆ–æR'’Æ–æRæBGvVÇfR–çfVçF÷&–VBÖöæÇ¦–ÖvW2âBÓ“sRv27Æ—B–âÆ6S¢BÓ“sr÷vç2F†—2ÆVc²BÓ“s‚&WF–ç2VÆWfVà¦f–ÆÆVBÆVfW2æB&Ææ²$‚ÂöæRÆVbW"'Vââ"3C6'&–W2F†—26ö×ÆWF–öâà ¢22BÓ“s’(	B6öçF–çVF–öâ•¤³¢GvVçG’×F‡&VR†÷W6V†öÆG2ÂVç—&V@ ¤–ÖvRS2—2&V6÷&FVB–âvW2ó355Ôu•”¢Ó•¤²æ§6öæÂv—F‚ÆÂ#2ö67W–VBDõDÀ¦VçG&–W2æB6WfVâ–æGW7G'’6öÇVÖç2–ç7V7FVBâæ–æWFVVâF÷FÇ2&R&VBæB7VÐ§Fò“S²Æ–æW22ÂBÂ‚æB#&VÖ–âçVÆÂv—F‚ÇFW&æF—fW2âF†V—"öæR6öæF—F–öæÀ¦6ö×ÆWF–öâFòF†Rw&—GFVâfö÷F–ær’—2&V6÷&FVBv—F†÷WBf–ÆÆ–ærç’6VÆÂà¥F†R–çfVçF÷'’w2öÆB7G&—7VÒöb‚—2æ÷B&öÖ÷FVBFò&VF–ærà ¤w&–7VÇGW&R6Æ÷6W2B"²²ÒBâVÆWfVâÖçVf7GW&–ærVçG&–W26Æ÷6RB#À¦–æ6ÇVF–ærF†R–æFWVæFVçFÇ’&VBröâÆ–æR#â–æÆæBæf–vF–öâ†2öæR&öG¦VçG'’æBæòw&—GFVâfö÷F–ærâ†÷&—¦öçFÂ&öfW76–öç2Ö&²Â7&÷76VBÖ&°¦&W6–FRF—6&–Æ—G’Ö6öÇVÖâ'VÆRÂæBâW&–v‡BÖ&²æV"F†R66†ööÂ&–æF–æp§&VÖ–âVç&W6öÇfVBâF†RÆ—FW&7’6öÇVÖâ—2Vç&VBâvVöÖWG'’&V6÷&G2F†RÖV7W&V@¦&æG2Â–æF—f–GVÂ7&÷&÷†W2æBF†R–ç7G'VÖVçBw27W&–÷W26ö×öæVçBw&÷W2à ¥F†R6öÆR6öÖÖ—GFVBÆVgB6†VWBv—F‚#2†÷W6V†öÆG2—2&–çFVB##Rƒ”…’’Âv†÷6P£R×W'6öâfö÷F–ærw&VW2v—F‚—G2÷vâ6VÆÇ2â—Bf–Ç2F†—26†VWBw2’×W'6öà¦¶W’âæò†÷W6V†öÆB–FVçF—G’÷"ƒ3Rö67WF–öâ—276–væVBâw&÷W2æ÷r†2f÷W ¦6öçF–çVF–öç2&VBÆ–æR'’Æ–æRæBVÆWfVâ–ÖvW27F–ÆÂ–çfVçF÷&–VBöæÇ’à¥BÓ“s‚7Æ—B–âÆ6S¢BÓ“s’÷vç2F†—2ÆVbÂBÓ“ƒ&WF–ç2FVâf–ÆÆVBÆVfW0¦æB&Ææ²$‚â"3C"6'&–W2F†—26ö×ÆWF–öâà ¢22BÓ“ƒ(	B6öçF–çVF–öâ%3¢GvVçG’Öæ–æR†÷W6V†öÆG2ÂVç—&V@ ¤–ÖvRSb—2&V6÷&FVB–âvW2ó355Ôu•”¢Ô%2æ§6öæÂv—F‚ÆÂ#’ö67W–VBDõDÀ¦VçG&–W2æBWfW'’6öçF–çVF–öâ&Æö6²–ç7V7FVBâGvVçG’×6—‚fÖ–Ç’F÷FÇ2&P§&VF&ÆRæB7VÒFò"âÆ–æW2BÂæB"&VÖ–âçVÆÂv—F‚ÇFW&æF—fW2B÷ £²F†R&W7VÇF–ær6öæF—F–öæÂF÷FÇ2&RBÂ#Â#‚æB3RÂæöæRWVÂFð§F†Rw&—GFVâfö÷F–ær3âF†RF—67&Wæ7’7F—2&V6÷&FVBæBæòvÇ—‚—26†÷6Và¦g&öÒF†R&—F†ÖWF–2à ¤ÆÂ6WfVâw&—GFVâö67WF–öâæB66†ööÂfö÷F–æw26Æ÷6R–æFWVæFVçFÇ“¢w&–7VÇGW&P£"Â6öÖÖW&6RrÂÖçVf7GW&W2æBG&FW2RÂ–æÆæBæf–vF–öâÂÆV&æVB&öfW76–öç0£ÂöæR&–Ö'’ö6öÖÖöâ66†ööÂæBR66†öÆ'2âÖ–æ–æræBö6Vâæf–vF–öâ&P¦&Ææ²–âF†R&öG’æBfö÷F–ærâF†R6ÆfRÂVç6–öæW"ÂæBF—6&–Æ—G’&Æö6·2&P¦&Ææ³²F†RÆ—FW&7’6öÇVÖâBF†R&÷VæBVFvR&VÖ–ç2Vç&VBà ¥F†RöæÇ’f–Æ&ÆRÆVgB×6†VWB¶W’v—F‚#’ö67W–VB†÷W6V†öÆG2—2&–çFVB##bÀ§v—F‚÷VÆF–öâƒBâF†RöæÇ’÷VÆF–öâ¶W’öb3—2&–çFVB#‚Âv—F‚3 ¦†÷W6V†öÆG2âæV—F†W"76W2&÷F‚¶W—2Â6òF†R6†VWB&VÖ–ç2Vç—&VBæB6WVVæ6P¦Wf–FVæ6R—2æ÷BW6VBâæò†÷W6V†öÆB–FVçF—G’Â&W6–FVçBÂö67WF–öâÂ÷"66†ööÂf7@¦—2&ö¦V7FVB–çFòƒ3Râw&÷W2æ÷r†2f—fR6öçF–çVF–öç2&VBÆ–æR'’Æ–æRæ@§FVâ–ÖvW27F–ÆÂ–çfVçF÷&–VBöæÇ’âBÓ“ƒ"&WF–ç2F†R&VÖ–æ–æræ–æRf–ÆÆVBÆVfW0¦æB&Ææ²$‚ÂöæRÆVbW"'Vââ"3C26'&–W2F†—26ö×ÆWF–öâà ¢22BÓ“ƒ2(	B6öçF–çVF–öâe26Æ÷6W2æB7F—2Vç—&V@ ¦355Ôu•”¢Ôe6—2&VBÆ–æR'’Æ–æS¢#rö67W–VBfÖ–Ç’F÷FÇ27VÒW†7FÇ’Fð§F†R6÷'&V7FVBæF—fR×&W6öÇWF–öâfö÷F–ær#RÂv†–ÆRÖçVf7GW&W2"Â–æÆæ@¦æf–vF–öâæBÆV&æVB&öfW76–öç2Ç6ò6Æ÷6RâF†R6öçF7B×6†VWB–çfVçF÷'’w0£#‚Æ–æW2òS"fö÷F–ær—26÷'&V7FVB–âÆ6Râæòf–Æ&ÆRÆVgB6†VWB76W2&÷F€§F†R†÷W6V†öÆBÖ6÷VçBæB÷VÆF–öâ¶W—2Â6òæò6WVVæ6R÷"–FVçF—G’—2–æfW'&VBà¤w&÷W27FæG2B6—‚&VB6öçF–çVF–öç2æBæ–æR–çfVçF÷&–VBÖöæÇ’–ÖvW2âBÓ“ƒ@§&WF–ç2F†R&VÖ–æ–ærV–v‡Bf–ÆÆVBÆVfW2æB&Ææ²$‚VæFW"F†RöæRÖÆVb×W"×'Và§'VÆS²"3CB6'&–W2F†—2ÆVbà 