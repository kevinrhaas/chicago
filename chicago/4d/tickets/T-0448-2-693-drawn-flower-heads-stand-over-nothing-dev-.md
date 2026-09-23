---
id: T-0448
title: 2,693 drawn flower heads stand over nothing — dev's full smoke has been red on it since 2026-08-30 and every PR inherits it
state: done
epic: FLORA
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-31
closed: 2026-09-01
pr: 621
claimed_by: null
blocked_on: null
needs_bake: false
---

`tools/smoke_renderer.mjs` asserts *"every drawn flower head has a plant under
its own stalk"*. It fails, and it is failing on `dev` itself:

```
FAIL  desktop 1280x800: every drawn flower head has a plant under its own stalk
      2693 of 18893 drawn heads over 40 poses had nothing under the foot of
      their own stalk; worst flora-head-corymb at from_above 270deg,
      foot 0.36 m, 0.36 m over its base over open ground
```

**14.3% of drawn flower heads are floating.** A visitor at a desktop viewport,
looking down from above, sees flower heads over open ground with no plant
beneath them.

## It is dev's, not any branch's — the two runs agree to the digit

| run | commit | date | result |
|---|---|---|---|
| `dev` full smoke | `54921610` | 2026-08-30 | 2693 of 18893, worst `flora-head-corymb` at from_above 270deg, foot 0.36 m |
| PR #560 `smoke (desktop, 10-13)` | `ab4dad40` | 2026-08-31 | 2693 of 18893, worst `flora-head-corymb` at from_above 270deg, foot 0.36 m |

Same count, same pose, same worst offender. No branch introduced it.

## Why it went unnoticed, which is the part worth fixing

The per-PR `gate` does not drive a browser, and the staged smoke only runs the
desktop 10-13 leg on some branches. So a fault that has been live on `dev` for
at least a day was invisible to every PR that did not happen to run that leg —
and when it did surface, it surfaced as *that PR's* failure. #591 fails
`smoke (desktop, 10-12)` and #432 fails five legs; both should be re-read against
this ticket before anyone concludes their own work is at fault.

## What is known about the mechanism

The assertion builds a one-metre grid of every rooted plant, then for each drawn
head looks in the nine cells around the foot of its stalk for a plant whose top
reaches it, allowing `SLACK`. `best === -Infinity` means **no plant at all** in
those nine cells — not a plant that is too short. The reported worst case is
`0.36 m over its base over open ground`, so heads are being drawn where the
instance that should carry them is not being drawn.

That points at the fade/ring ramp — `fadeOf(...)` and `aChiRing` decide WHETHER a
plant is drawn at a given distance from the camera, and T-0035's note above the
check says the ramp is *coverage, not height*, and that a plant is drawn whole or
not at all. A head surviving a ramp its own stalk did not would produce exactly
this. **Unverified — that is the first thing to test, not the answer.**

## MERGED RED, ON THE OWNER'S DECISION — 2026-08-31

PR #560 was merged into `dev` with this assertion failing, on the owner's
explicit instruction, because it is 900 of 901 green and the one failure is
inherited from `dev` rather than caused by the branch. Recorded here so the
exception is visible rather than silent, which is the whole reason this ticket
exists as well as the fix.

**Acceptance:**

1. The mechanism is demonstrated, not guessed: a reproduction that shows WHY a
   head is drawn when its own plant is not.
2. The count goes to **zero** heads over nothing. Not reduced — zero. A head
   with no plant beneath it is a drawing this project cannot defend.
3. The assertion is not weakened, its `SLACK` is not widened, and the pose list
   is not trimmed to avoid the failing view.
4. `dev`'s full smoke is green on `desktop 10-13` afterwards, verified on `dev`
   and not only on the branch.
5. #591 and #432 are re-read against the result — if their smoke failures were
   this fault, they are unblocked by the fix rather than by their own work.

---

## A LEAD, 2026-08-31 — the support set may be short two meshes

Read from `tools/smoke_renderer.mjs` and `renderers/web/js/flora.js`. **Not
verified** — verifying needs the renderer, and Playwright's Chromium is what T-0442
could not download either. Recorded so whoever takes this starts here.

The check matches a head to a plant **by proximity on a one-metre grid**, not by
instance identity: for each drawn head it looks in the nine cells around the foot
of its stalk for a plant in `ROOTED` whose top reaches it. `best === -Infinity`
means no plant of that set was found at all.

`ROOTED` (line 8891) holds **four** names:

```
flora-near · flora-forb · flora-rosette · flora-shrub
```

`flora.js` creates **eight** non-head instanced meshes:

```
flora-card · flora-far · flora-forb · flora-mid
flora-near · flora-rosette · flora-shrub · flora-tuft
```

So `flora-card`, `flora-far`, **`flora-mid`** and **`flora-tuft`** are invisible
to the support test. The comment above `ROOTED` justifies excluding a mesh that
"carries no head, so counting one as support is a free pass — it is what made a
first cut of this read zero", which explains a card or a far billboard. It does
not obviously explain `flora-mid` or `flora-tuft`.

**If either of those carries heads, the heads are not floating and the ASSERTION
is what is wrong.** That is a materially different fix from moving geometry, and
it should be settled before anything is moved:

1. Ask the renderer which mesh each of the 2,693 orphaned heads belongs to, and
   which mesh its stem is in. The check already knows the head's mesh — `worst`
   carries `set: m.name` — so the same walk can carry the stem's.
2. If the stems are in `flora-mid` or `flora-tuft`, the fix is `ROOTED`, and the
   town was right all along.
3. If they are in no mesh at all, the heads really are orphaned and the fix is in
   the flora layer.

**Do not widen `ROOTED` to make the number go down.** The comment records that an
earlier cut read zero by counting the wrong meshes as support, which is the same
mistake in the other direction.

## WHICH PRs THIS ACTUALLY BLOCKS — measured 2026-08-31

| PR | its smoke failures | blocked by this? |
|---|---|---|
| **#591** (T-0181) | `smoke (desktop, 10-12)` — **only** the flora assertion, `2693 of 18893`, identical to dev's | **YES, and by nothing else** |
| #432 (T-0219) | five legs, and they are NOT all this: *every tree drawn stands at its own station — 0 of 0 vertices*, *the frontage layer lays all five records' walks*, *the Sauganash's two hitching posts*, plus its own flora count of `2316 of 18002` | no — it has its own faults |

So fixing this releases **#591 outright**. #432 needs its own run whatever happens
here, and its different flora count (2,316 of 18,002 against dev's 2,693 of
18,893) says its tree is different rather than that it inherited this one.

---

## THE LEAD ABOVE IS WRONG, AND HERE IS THE EVIDENCE — 2026-08-31

The lead recorded earlier guessed that `ROOTED` was short two meshes and that the
ASSERTION might be at fault. **It is not.** Read from `renderers/web/js/flora.js`
rather than from a grep for name strings:

`instSet(...)` is what makes an instanced mesh, and it is called for exactly
**fifteen**:

| non-head (6) | head (9) |
|---|---|
| `flora-near`, `flora-forb`, `flora-rosette`, `flora-shrub` | `flora-head-` spike, spire, panicle, corymb, dome, pompom, ray, raydroop, compound |
| `flora-mid`, `flora-far` | |

`ROOTED` holds the four in the first row and excludes `flora-mid` and `flora-far`
— and **both of those are `cardGeometry(...)`**, the billboard LOD:

```
flora-mid = instSet('flora-mid', cardGeometry(7),               ...)
flora-far = instSet('flora-far', cardGeometry(tune.far.columns), ...)
```

A card carries no head, which is exactly what the comment above `ROOTED` says it
is excluding and why. **`flora-tuft` and `flora-card` are not meshes at all** —
they are geometry labels passed to `finishGeo`, which is what the earlier grep
caught and misread.

**So the support set is correct and the heads really are unsupported.** The fault
is in the flora layer, not in the check. Anyone arriving here should not spend a
second on `ROOTED`.

### What is now known about where to look

The caps are worth a look but do not obviously explain it. At full detail
(`TUNE.cap`) the stems get `near: 2400` and `forb: 900` against `head: 820`
shared across all nine head shapes, so heads are the scarcer instance — a cap
that binds would give a stem with no head, which is harmless, rather than the
head with no stem that is being reported.

The check's own geometry is the next thing to read. It derives the head's foot as

```
s  = lo * fl[i*4]          // lo = lowest y in the head geometry, fl = scale
fx = x + mm[o+4] * s       // origin + the instance's local Y axis, scaled
```

and then requires a plant whose top reaches `fy` **and** whose base is within
`max(0.05, p.r) + SLACK` of `(fx, fz)` horizontally. Two candidates follow, and
neither is tested here:

1. **The horizontal test is too tight for a leaning stem.** A head sitting at the
   top of a stem that leans is offset from its own base by more than the base's
   radius, and would read as an orphan while standing on its own plant.
2. **The head is genuinely placed without its stem** — the scatter puts heads and
   stems from separate passes and one of them drops instances the other keeps.

Telling those apart needs the renderer, which is why this is left as a reading
and not a fix. The diagnostic recorded earlier still stands: make the walk report
the STEM's mesh alongside `worst.set`, and the answer falls out.


---

## ANSWERED, MEASURED, 2026-09-01 — the heads are not floating; the check was stale

Both earlier readings named the wrong thing. The mechanism is now measured on
the published mirror, twice, and it is neither of the two candidates left above.

### Run 1 — the lean is not it

`dev` at `516b0ccf`, desktop stage 10-12, with #618's diagnostic:

```
worst flora-head-corymb at from_above 270deg, foot 0.36 m, 0.36 m over its base
over open ground; nearest rooted flora-forb at 1.693 m
(its own radius 0.146 m, top 0.202 m from the foot)
```

The radius test would have accepted `max(0.05, 0.146) + 0.02 = 0.166 m`. The
nearest rooted plant is **1.693 m** — ten times that, and an order beyond the
~0.2 m a stalk can swing its foot at `reach 2.2`, `size 0.12`. **Candidate 1,
"the horizontal test is too tight for a leaning stem", is dead.**

### Run 2 — it is the far card, and it is all of them

A second grid was added holding exactly the meshes `ROOTED` leaves out,
consulted only to explain an orphan and never read by the support test, so the
count stayed comparable. Same branch, same leg:

```
excluded flora-far at 0 m (radius 1.576 m, top 0.324 m from the foot)
2693 of 2693 orphans stand on a mesh ROOTED excludes that reaches them
[flora-far 2693]
```

**2693 of 2693.** Not most — all. Every orphaned head stands on a `flora-far`
card at **0.000 m**: not near one, the same position, because `rebuildFar`
places the head at the card's own `e,n`. The card's top reaches 0.324 m above
the foot. **None** stood on `flora-mid`.

### Why, with a date on it

T-0209 made the far band deal the WHOLE community rather than its grass alone,
and gave a flowering forb's far card its flower:

```js
const h = placeFarCard(farSet, sp, zone, e, y, n, rng, band);
if (forb && h > 0 && sp.head && tune.far.minPx && r <= farHeadReach(...)) {
  maybeHead(heads, sp, e, y, n, rng, h, farHeadRing(...));
}
```

`ROOTED` went on excluding `flora-far` on the stated grounds that "a card
carries no head". **True when written, false since T-0209**, and nobody updated
the support set. So the check has been asking for a stem under a head whose
plant is deliberately drawn as a billboard.

Acceptance 1 is met: the mechanism is demonstrated, not guessed. The fix is the
check, not the flora layer — no geometry moves.

### The naive fix would have been wrong

A card's `spread` is its billboard HALF-WIDTH — 1.576 m in the measurement
above, `wide: [1.5, 2.6]` and `[2.6, 4.6]` in TUNE. Admitting `flora-far` to
`ROOTED` as-is would let any head within a card's width of one count as
supported, which is precisely the free pass the original note refuses and the
mistake it records an earlier cut making.

So a card is admitted with **radius zero**: it supports the head at its own foot
and nowhere else, a 0.07 m window once `SLACK` is added, and the measured `d` is
0.000. `flora-mid` stays excluded and that is measured too — its scatter deals
`graminoids` only and never calls `maybeHead`, and no orphan stood on one.

One more fault was in the way and would have made a wholesale addition read
zero for the wrong reason: `heightAt` returns **null** for `flora-far`, because
`ringOfSet` has no entry for it. Left alone, the card's top would have been its
own base and the reach test would have failed. Since T-0035 a drawn plant is
drawn whole, so the fraction is 1 and the null means "no ramp", not "no height".

`SLACK` is untouched, the pose list is untouched, and the head-side test is
untouched — acceptance 3.

### The earlier leads, and what they cost

| lead | verdict |
|---|---|
| `ROOTED` is short `flora-mid`/`flora-tuft`, so the assertion is wrong | wrong meshes, **right instinct** — and it was retracted in #618 on the strength of the `cardGeometry` reading, which was correct about `flora-mid` and did not think to ask whether `flora-far` had changed |
| the fade/ring ramp draws a head its stem did not get | ruled out by construction: `headRingAt` puts the head's outer radius at `fade[0] - 0.35*fade[1]` with the same inner ramp, strictly INSIDE its plant's ring |
| the horizontal test is too tight for a lean | ruled out by measurement, 1.693 m against a 0.166 m tolerance |
| heads and stems come from separate passes | false — one callback, one plant record; `maybeHead` is only reached when the plant's own push returned `h > 0` |

The retraction in #618 was right to kill the `flora-mid` theory and wrong to
conclude from it that "the support set is correct and the heads really are
unsupported". The support set was incorrect for a different mesh.
