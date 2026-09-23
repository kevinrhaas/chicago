---
id: T-0194
title: Hitching posts at the commercial frontages
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0127
opened: 2026-08-24
closed: 2026-08-27
pr: 412
claimed_by: run 8/27/2026, 8:07:04 AM CT
blocked_on: null
needs_bake: false
---

Hitching posts at the commercial frontages.

Piece 5 of 5 of **T-0127 — The rest of the town gets the street edge**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

---

## 2026-08-27 (morning) — BUILT AND GATED, HELD ON A CEILING IT DID NOT BREACH

Branch **`steward/t-0194-hitching-posts`** (2 commits, pushed). **The PR could not be
opened: GitHub rate-limited the steward PAT three times in a row** (403, "API rate limit
exceeded for user ID 4193586") at the end of the run. Everything below is what the PR body
would have said; open the PR from that branch with the `hold` label when the limit clears.

**Twelve hitching posts** stand in the verge outside the plank walk on South Water Street
and Lake Street, one at each trading frontage the rule accepts. Acceptance met: the rule is
generated, re-derived byte for byte by `check.sh`, and both of the smoke's frontage
assertions pass at BOTH viewports.

### The rule, and where every clause came from

The post itself is not new — it is the Sauganash's own (T-0090, L136) carried across
unchanged: 1.30 m of 0.16 m timber under a 0.22 m capped head, 0.90 m beyond the walk's
outer edge. What is new is only WHICH other frontages get one:

1. a committed building stands on the lot (the fence rule's clause 2);
2. its `function` is one of `PUBLIC_TRADES`, **imported** from
   `tools/generate_business_signboards.py` rather than restated, so "which trade takes its
   custom off a stranger in the street" has one answer in this repository. A works or a
   warehouse is refused in writing — carts at a yard gate is a different fitting from a
   rider at a post, which is the same distinction that file already draws between a board
   over a footway and a name painted on a front;
3. the trade is held `attested`/`documented`/`inferred` rather than dealt by the roof
   schedule, which is what keeps posts off the anonymous slots. The signboard rule's other
   exclusion — an anonymous slot has no name to paint — is deliberately NOT copied: a post
   carries no lettering;
4. the walk was actually laid in front of it;
5. its own stand is dry committed ground, unoccupied, clearing the track by 0.35 m.

WHERE is the BUILDING's own projected frontage at 0.28 of its length, not the lot's: the
Sauganash and Philo Carpenter's shop share one platted lot.

**Seven refused, each naming its clause** — the Sauganash (already stands its own two under
L136); three works/warehouse trades; two named buildings whose trade is graded
`reconstructed` (filed as **T-0230**); and Bates's auction room, where no walk is laid.

### WHY IT IS HELD, measured on both sides

`tools/measure_stand_budget.mjs --stand lake_at_canal --tiers balanced --only desktop
--source`, desktop 1280x800:

| | `dev` @ 73c228e0 | this branch | delta |
|---|---:|---:|---:|
| `balanced`, whole frame | 1,265,390 | 1,265,678 | **+288** |
| ceiling | 1,260,000 | 1,260,000 | — |
| **over by** | **5,390** | **5,678** | |
| draw calls | 199 | 199 | **0** |
| frontage layer | 161,386 / 38c / 37 meshes | 161,674 / 38c / 37 | +288 / 0 / 0 |

**`dev` is already 5,390 triangles over `balanced` on its own**, one commit after T-0229
raised that ceiling to 1,260,000 against a then-measured 1,252,802 — the town has drifted
+12,588 past that reading in a day. This parcel adds 288 triangles (12 posts x 2 boxes x 12)
and no draw call at all, because a post is standing timber and lands in its street's
EXISTING standing mesh beside the fences.

AGENTS.md's frame-budget ruling permits a conscious re-budget when a parcel the owner asked
for needs it. **This parcel does not need it** — it needs 288 triangles out of a 5,390 hole
it did not dig. Raising the ceiling here would spend the SIXTH re-basing on someone else's
triangles inside an unrelated PR, which is what T-0135 named as the bug and what T-0229
wrote the count into `main.js` to make harder. **T-0209** (the timber cull: `trees` draws
363,884 of the 183,360 it holds, 181,560 of it the sun's pass over timber outside the
shadow box) is the real repair and was claimed on another branch during this run.

So: merge it if +288/+0 into an already-breached ceiling is acceptable, or hold it until
T-0209 lands and the leg goes green on its own.

### Verification, all foreground

* `./tools/check.sh` — **CHECK PASS**. This is the repo's declared DEV GATE
  (`docs/PIPELINE.md` -> `chicago-4d-check.yml` runs exactly this). Baselined against clean
  `dev` first, which also passes.
* `SMOKE_STAGE=2` (the frontage leg), **both viewports, SMOKE PASS 78/78, zero pageerrors** —
  desktop 1280x800 3 m 40 s, mobile 390x780 2 m 01 s. Both new assertions green:
  *the frontage layer lays all five records' walks and stands their posts*, and
  *every hitching post stands on its own ground, carrying nothing*.
* `SMOKE_STAGE=3-4` desktop, 11 m 13 s — **108 passed, 1 failed**: the `balanced` ceiling
  above. `full`, `light` and both draw-call ceilings pass.
* `generate_frontage_works.py --check` re-derives byte for byte; `check-changelog.mjs` OK
  (v292); `publish.sh` run in the same commit. **No bake owed** — the street edge is drawn
  at load, not baked, so no GLB moved and `validate.py --stale` is green.

### One gate repaired on the way

The smoke's hitching probe read the SHARED mesh only. With the posts bucketed into their
street's standing mesh it would have read `top = -Infinity` for twelve of the fourteen and
reported a pass on the two it could still see. It walks every timber mesh now.

### Bookkeeping on the branch

L160 amended and `Revised:` stamped, `liberties.json` recompiled; changelog v292 stamped and
mirrored; T-0230 filed `--by loop` at the QUEUE bottom; QUEUE order otherwise untouched.
**This ticket is left `claimed`, not `done`** — its state only reaches `dev` when its PR
merges, and `ticket.mjs claim` will point the next run at this branch rather than let it
rebuild the work.


## 2026-08-27 (evening) — THE HOLD IS LIFTED: THE CEILING THAT HELD IT IS NO LONGER BREACHED

The run above finished the work, could not open its PR (three consecutive 403s on the steward
PAT), and left the branch pushed with an explicit handoff. Nothing was reworked here: the branch
was **rebased onto today's `dev`** — which has since taken **T-0223** (the timber cull, #411),
**T-0146** (#408) and **T-0208** (#410) — every derived artefact re-generated on that base, and
the gate re-run in full. The parallel implementation this run had built independently was
discarded rather than opened as a second PR: one ticket, one branch, one PR. `ticket.mjs inflight`
reported nothing at claim time because the rival branch was pushed hours earlier and had aged out
of the three-hour "live" window — which is the same collision **T-0238** is already filed for.

**The hold was never about this parcel, and it is gone.** T-0223 landed the timber cull the morning
run named as the real repair, and the whole frame came down with it. Re-measured by the smoke's own
ceiling leg, on this branch, at the worst stand in each set:

| tier | ceiling | desktop 1280×800 | mobile 390×780 |
|---|---:|---:|---:|
| `full` | 1,425,000 | 1,252,879 | 1,145,313 |
| `balanced` | 1,260,000 | 1,084,292 | 1,020,684 |
| `light` | 1,050,000 | 703,610 | 649,296 |

`balanced` was **5,678 over** this morning and is **175,708 under** now. Draw calls: 141 worst
(desktop), 137 (mobile). The 288 triangles this parcel adds are inside the instrument's own noise.

**Re-run in the foreground on this branch, all of it:**

* `./tools/check.sh` — **CHECK PASS**. This is the declared dev gate (`docs/PIPELINE.md`: *"the dev
  gate is `check.sh` and nothing else"*), and it re-derives the record byte for byte.
* `SMOKE_STAGE=2`, **both viewports** — **160 passed, 0 failed, SMOKE PASS**, including both
  hitching-post assertions and *aiming at the frontage opens the inn it belongs to* at each.
* `SMOKE_STAGE=3-4`, **mobile 390×780** — **113 passed, 0 failed, SMOKE PASS**, all three ceilings.
* `SMOKE_STAGE=3`, **desktop 1280×800** — **74 passed, 0 failed, SMOKE PASS**.
* `SMOKE_STAGE=4`, **desktop 1280×800** — every assertion in the part passed, **including all
  three detail ceilings and the draw-call ceiling**, run TWICE with identical figures. The part
  could not reach its own teardown inside the runner's ten-minute per-command ceiling either time.
  That is the condition **T-0173** ("part 4 and part 5 have under a minute of margin") and
  **T-0235** ("the unfiltered smoke takes 55 minutes on the steward runner") already record on
  `dev`; it is a fact about the runner, not about this branch.
* Changelog re-stamped on the rebased base (the morning's v292 collided with three merges since);
  `publish.sh` re-run in the same commit; `compile_liberties.py` re-derived; `ticket.mjs board`
  regenerated. **T-0230's QUEUE line was re-appended at the BOTTOM** of the file as the owner
  re-ordered it this afternoon — his ranking is untouched.
