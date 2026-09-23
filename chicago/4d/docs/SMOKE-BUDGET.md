# The renderer gate's budget — what it costs here, and what covers what

**T-0235.** A steward run's single foreground command is capped at **600 s**, so no
run can take the gate whole. It takes the parts that cover what it touched — and
until this page, nothing said which those were. A run either spent more than its
entire budget on all fifteen staged commands, or picked by feel.

The answer is tools rather than prose, because a table of part numbers rots the
first time the parts are re-cut — which has happened four times in 2026 (T-0060,
T-0121, T-0167, T-0346).

```
node tools/smoke_budget.mjs                    # what the gate costs on this machine
node tools/smoke_budget.mjs --legs             # the nightly gate leg by leg, against its own cap
node tools/smoke_budget.mjs --for <path>…      # the parts that cover those files
node tools/smoke_budget.mjs --for-diff         # the same, off your own diff vs origin/dev
node tools/smoke_budget.mjs --self-test        # the map has not rotted (runs in check.sh)
```

## THREE CAPS, AND EACH BOUNDS A DIFFERENT THING (T-0450, 2026-09-03)

**Corrected here.** This page used to open by telling T-0170, T-0173 and T-0181
that the **30-minute** cap their margins are taken against "is not this
machine's", and offered the whole gate's **55 m 10 s** as the proof. That
reasoning does not hold, for the plainest possible reason: *the two numbers are
not the same quantity.* Neither bounds the other.

| cap | what it bounds | where it is written |
|---|---|---|
| **600 s** | ONE foreground command in a steward run | the harness; ROADMAP § THE RUN BUDGET |
| **30 min** | ONE LEG of the nightly gate — one viewport over one range of parts, eight legs in parallel | `.github/workflows/chicago-4d-bake.yml` § `smoke`, `timeout-minutes` |
| **90 min** | the WHOLE body in one process, both viewports, no per-leg cap at all | `.github/workflows/chicago-4d-smoke.yml` § `smoke`, `timeout-minutes` |

**So T-0170, T-0173 and T-0181 were reasoning about the leg cap correctly**, and
this page told them for three days that they were not. The 55 m 10 s figure is a
reading of the third row and belongs beside the 90-minute cap; a leg's margin
belongs beside the 30-minute one. `node tools/smoke_budget.mjs` now totals the
whole body against the whole-body cap and `--legs` totals each leg against the
per-leg cap, both read out of the workflows rather than restated here — a number
in prose is what rotted the first time.

**And it is the same machine.** The claim that it is not was the load-bearing
half of the old opening, and nothing in the committed tree supports it: the
nightly gate's legs (`chicago-4d-bake.yml` § `smoke`), the full-body run
(`chicago-4d-smoke.yml` § `smoke`), the dev gate (`chicago-4d-check.yml`) and the
steward improve runner (`polecat-platform` § `steward-improve.yml`) are all
`runs-on: ubuntu-latest` with node 22, and the first two install the same
`playwright@1.56.1` and chromium alone. `smoke_renderer.mjs` launches that
chromium with `--enable-unsafe-swiftshader` wherever it runs, so the software
rasteriser is a property of the suite, not of one runner.

**The timings, and exactly how far they are checked.** T-0450 measured one leg
twice — the same leg, minutes apart, on the two runners the old text called
different machines:

| runner | reading | provenance |
|---|---|---|
| the nightly gate — run **33290607360**, `Smoke the published mirror` | **4 m 40 s** | reported by T-0450; the run is verified as a `chicago-4d-bake.yml` run on `dev`, created 2026-08-30T03:35:19Z |
| the improve runner — PR #589's branch | **4 m 44 s** | reported by T-0450; that branch is closed and the reading is not re-derivable |

Four seconds apart. **What is NOT verified**, and is recorded so nobody promotes
it: T-0450 gives `dev` at `415909cf` for the pair, and run 33290607360's own head
commit is `fc10c83d`, so "the same bytes" is the ticket's word and not a checked
fact. The four seconds are quoted as its reading. The same-machine finding above
does not rest on them — it rests on the four workflow files, which anyone can
re-read.

## The nightly gate's legs, and why they are not in this file

The gate is cut into legs by `chicago-4d-bake.yml` § `smoke` — two viewports over
four stage ranges, **eight legs, all in parallel**, each under the 30-minute cap.
Those ranges have been re-spelled four times in 2026 as the body was re-cut, and
every prose copy of them has gone stale in turn. So **`--legs` reads them from
the workflow and prices them from `tools/dev-smoke-state.json`**, and
`--self-test` (which `check.sh` runs) fails if the ranges ever stop tiling parts
`1..PARTS` exactly once — the property the workflow's own comment has asserted
since T-0171 and nothing held.

A leg whose only readings straddle its boundary is priced with the neighbour
included and says so: the cost is then an upper bound and the margin a lower one,
which is the safe direction to be wrong in.

## Where the seconds come from

Every figure is READ out of `tools/dev-smoke-state.json` — the standing record
T-0216 built — filtered to readings taken on `host.kind: steward-runner` against
the published mirror, and reported as the median of the readings for that part.
Nothing on this page is asserted, nothing is a bar, and a part with no reading is
named as having none rather than given a plausible number. As readings
accumulate the figures move on their own; file the smoke you ran anyway:

```
node tools/dev-smoke-state.mjs record /tmp/smoke-desktop4.log
```

**The numbering changed THREE TIMES on 2026-08-30** — T-0346 cut old part 4 into
4 + 5 + 6 and renumbered old 5-9 to 7-11; T-0173 then cut part 7 into 7 + 8 and
renumbered 8-11 to 9-12; T-0170 then cut part 10 into 10 + 11 and renumbered
11-12 to 12-13. Readings filed before a cut are labelled in the numbering of
their day and the tool RENUMBERS them rather than discarding them, pushing each
one through every cut it predates in order: a reading of old part 5 is a reading
of what is now parts 7 + 8. Three cases cannot be renumbered to a single part —
old part 4 is a reading of 4 + 5 + 6, a T-0346-era part 7 is a reading of 7 + 8,
and a T-0173-era part 10 is a reading of 10 + 11 — and each is reported as the
group it is.

## The recipe is conservative by construction

The map in `tools/smoke_budget.mjs` can only ever ADD parts:

- a path the map does **not** know maps to **the whole gate**, so a module nobody
  wrote a row for makes the recipe bigger, never quietly smaller;
- a path the map knows reads **no** part of the body — the gate's own tooling,
  the backlog, prose — says `NO PART` explicitly, which is a different statement
  from "unmapped", and still earns one cheap staged pass per viewport, because
  boot, the page-error check and the vendor checks are taken in **every**
  invocation whichever stage is asked for;
- `--self-test` fails if a mapped path has vanished from the tree, if any part
  1..13 is covered by no row, if `PARTS` in `smoke_renderer.mjs` has moved out
  from under the map, if the renumbering arithmetic breaks, or if an unmapped
  path ever stops meaning the whole gate. `check.sh` runs it.

**The limitation this page used to state is GONE (T-0938), and it is worth
recording what it was.** `tools/publish.sh` restamps the build id into
`site/chicago/4d/walk/index.html` on every publish, and that file is the page
itself — every part clicks its markup — so under the old map a published change
was always told "the whole gate", however small the real edit. Run #1464
(2026-09-03) ran seven legs for two census page files and lost its budget to it.
The mirror is untracked and generated now, so it can never appear in a
`git diff --name-only` and `--for-diff` prices a PR on the source it changed,
which is the only thing a PR changes. The six `site/chicago/4d/` rows are gone
from the map with it; the self-test asserts the mirror is still untracked, and
fails — asking for the rows back — if that ever stops being true.

**A staged run is not the gate**, and it says so on its own first line. The gate
is both viewports, every part. What this page buys is the ability to spend ten
minutes on the parts that could possibly have moved, instead of spending nothing
because the whole thing did not fit.

## What each part covers

The map's rows are justified by the parts' own section headings in
`tools/smoke_renderer.mjs`. In outline:

| part | what it takes |
|---|---|
| 1 | the town count, water anchoring, the enclosure layer, the pound, the dooryard pickets, the lot-line fences, the plantings, the fort stockade, the business signs and what they say |
| 2 | the yard goods, the wagons, the building material, the frontage layer, the plank walk, the street edge, the wharves and walking one, the boats, the confidence view |
| 3 | the ground faces the sky, the ground the town stands on, the residents' names, the level prose, pick → provenance, the dossier link, the liberties on the card, who was here |
| 4 | the raycast pick, walking, standing, the bridge decks, the touch backend, the budgets, life size, nothing hovers |
| 5 | the scene-detail ladder, and nothing else (T-0346 cut it out on its own) |
| 6 | the gate and the chrome, and the confidence menu's own clicks |
| 7 | navigation and its readouts, and two of the three road-legibility stations (T-0173 cut it here) |
| 8 | the third road station, the road-legibility aid taken standing at it, and the batch merge |
| 9 | the facade tones, the shadow reach, the shadow box, the brightness aid |
| 10 | the drawn population, the horizon timber, the sward dealt in every community, the marsh substrate, the pop-in, the flower heads (T-0170 cut it here) |
| 11 | the sward's ragged boundary and its fringe, each community's recorded ground cover, the street readouts, the navigation guide, the Settings units |
| 12 | eye height, typing is not driving, the Go-to tab, What's-new |
| 13 | the Evidence panel — liberties, people, wildlife, what grows, what is not here, researched-and-open, what the ground claims — free-fly, and inspecting from the air |

## The zero-byte log, which is why a green run got killed

`node` block-buffers stdout **to a pipe**. A smoke redirected through a pipe
therefore writes nothing at all until the process exits, so a long staged run
looks identical to a hung one for its entire life. On 2026-08-27 a run watching
41 minutes of zero-byte log killed the smoke **one minute from its finish**, as
the flushed fragment showed afterwards.

**Redirect to a real file and tail it.** Never pipe a smoke you intend to watch.

```
SMOKE_VIEWPORT=desktop SMOKE_STAGE=5 node tools/smoke_renderer.mjs --published > /tmp/smoke-d5.log 2>&1
```

`SMOKE_TIMING=1` stamps every check line with the elapsed clock. Turn it on when
you are profiling a part rather than gating one: a part that BREACHES the ceiling
is killed before it prints its wall clock, so the parts most worth cutting are
exactly the ones a plain run learns nothing about.

## Related

`docs/PIPELINE.md` (where a green gate sends the work) · `AGENTS.md` § How work
ships · T-0216 `tools/dev-smoke-state.mjs` (the record these figures are read
from) · T-0170 (the last re-cut) · T-0173, T-0181 (the margins taken against the
per-leg cap, which is the right cap for them) · T-0450 (the three caps, and the
same-machine finding) · ROADMAP § THE RUN BUDGET.
