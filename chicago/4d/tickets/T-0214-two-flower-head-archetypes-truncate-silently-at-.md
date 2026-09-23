---
id: T-0214
title: Two flower-head archetypes truncate silently at their instance cap
state: done
epic: FLORA
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-26
closed: 2026-08-28
pr: 446
claimed_by: run 8/28/2026, 2:55:45 AM CT
blocked_on: null
needs_bake: false
---

Found by T-0034 while measuring what bounds the bloom, and **not caused by it** — the same two
sets stand at their cap on the build before that ticket's raise as well as after.

`node tools/measure_bloom_headroom.mjs`, standing in every community at four bearings:

| set | worst stand | drawn / cap |
|---|---|---|
| `flora-head-spike` | `z10_settled_town`, facing 90° | **820 / 820** |
| `flora-head-dome` | `z06_dense_forest`, facing 0° | **820 / 820** |
| `flora-head-pompom` | `z06_dense_forest`, facing 90° | 804 / 820 |

`maybeHead` (`renderers/web/js/flora.js`) stops pushing the moment a set is full — `if
(!set.push(...)) return;` — so it truncates **mid-plant and without a word**: the placer deals
the head, the record asked for it, and the frame never draws it. Nothing reports it. The nine
head sets share nine separate `TUNE.cap.head` ceilings of 820 each and the aggregate is barely a
fifth spent at the worst stand measured, so the shortfall is an ALLOCATION, not a budget: two
sets are full while seven are nearly empty.

**Do not simply raise `TUNE.cap.head`.** The three routes worth measuring between are (1)
allocate the nine ceilings against measured per-set demand at a constant or lower TOTAL, which
buys the room out of a budget that already exists; (2) one head archetype set with a per-instance
shape, which removes the nine-way split entirely; (3) accept the ceiling and REPORT the
truncation, which is at least honest and is nearly free. Route 1 needs demand measured across
every community and every bearing before any number moves, because a cap tuned at three stands
and blown at a fourth is the defect this ticket is about.

**Acceptance:** a measurement across every community and four bearings shows **no head set at
its cap anywhere**, or the shortfall is reported by name and count where a reader can see it —
and the total head instance ceiling is not larger than it is today. `tools/measure_bloom_headroom.mjs`
already prints the table; its `--assert` run is the gate.

Related: T-0034 (the measurement that found it) · ROADMAP K58 (the same shape one stratum down:
a ceiling deciding how much of the evidence a visitor sees).

---
## 2026-08-28 — DONE by route 1, and route 3 came with it

**Acceptance restated before working, and not weakened:** a measurement across every
community and four bearings shows NO head set at its cap anywhere, and the total head
instance ceiling is not larger than it is today (9 x 820 = 7,380 instances).

**The demand was measurable only after the placer was made to count it.** `maybeHead`
abandons a plant's remaining inflorescences the moment `push` returns false, so a full
set's own `mesh.count` was the only thing it ever reported — and that number cannot tell a
set which had nothing to draw from one that was cut off. `instSet` now counts DEMAND —
every push attempted, plus the ones the caller gives up on, which `maybeHead` declares
through a new `skip` — and `flora.stats.demand` / `flora.stats.shortfall` carry it out of
the module. That is route 3 of the three the ticket named, and it is what let route 1 be
sized on a number instead of a guess.

**What every set was asked for, at its own worst pose** (`node
tools/measure_bloom_headroom.mjs`, 8 communities x 4 bearings plus the three named
stands, desktop, full detail — printed by its new §2a):

| set | cap | asked | drawn | refused | at its worst pose |
|---|---:|---:|---:|---:|---|
| `dome` | 820 | 1,202 | 820 | **382** | z06_dense_forest facing 90° |
| `spike` | 820 | 852 | 820 | **32** | z10_settled_town facing 90° |
| `pompom` | 820 | 804 | 804 | — | z06_dense_forest facing 90° |
| `raydroop` | 820 | 734 | 734 | — | z02_mesic_prairie |
| `corymb` | 820 | 533 | 533 | — | z10_settled_town facing 270° |
| `ray` | 820 | 248 | 248 | — | z02_mesic_prairie |
| `compound` | 820 | 160 | 160 | — | z10_settled_town facing 270° |
| `panicle` | 820 | 23 | 23 | — | z01_wet_prairie facing 90° |
| `spire` | 820 | 21 | 21 | — | z10_settled_town facing 270° |
| | **7,380** | **4,577** | | **414** | each set's OWN worst pose, summed |

**4,577 against 7,380 confirms the ticket's reading: an ALLOCATION, not a budget.** And
4,577 is already a bound no frame draws — those nine poses stand in five different
communities.

**The allocation.** `HEAD_SHARE` in `renderers/web/js/flora.js` gives each archetype
`tune.cap.head x share`, the nine shares normalised to average exactly 1, so the nine
ceilings still sum to nine times `cap.head` at EVERY detail tier and a tier that halves
`cap.head` halves each share with it. The weights are the measured demands, floored at
`compound`'s 160 — no set is dealt off less than the smallest genuinely-used one, because
21 is a ceiling one new flowering record walks through and the demand table is a reading
of today's records rather than a property of an archetype. Desktop: dome 1,828 · spike
1,296 · pompom 1,223 · raydroop 1,116 · corymb 811 · ray 377 · compound 243 · panicle 243
· spire 243 = **7,380, unchanged**.

**Re-measured: no set at its cap at any pose, and every one at 65.8 % of its ceiling.**
`--assert` passes and now carries two new gates of its own — no head set at a cap anywhere
in the mosaic, and the nine ceilings summing to 7,380 (+/- 9, rounding).

**IT WAS NEEDED THE SAME DAY IT WAS MEASURED.** T-0209 landed on `dev` while this branch
was under verification and carried the prairie bloom out past the near ring to 119.9 m.
More reach is more heads: the demand table moves to 5,090 asked for against the same
7,380, `corymb` alone from 533 to 724 — and `flora-head-raydroop` now stands AT its cap at
`prairie_west` on unmodified `dev`, refusing 28 of the 2,469 heads that stand asks for.
`measure_bloom_headroom.mjs --assert` fails on `origin/dev` at `c39167b4` for exactly
that, and passes here. So `HEAD_DEMAND` carries the SECOND reading and the shares are
sized on it: dome 1,684 · spike 1,259 · raydroop 1,156 · pompom 1,096 · corymb 987 · ray
420 · compound 259 · spire 259 · panicle 259 = **7,379**, one instance under the 7,380
that was there, from rounding.

The assertion `prairie_west heads drawn` is restated from T-0034's 1,968 to **2,469** for
the same reason, and the restatement is T-0209's reach and not this allocation: `dev`
draws 2,441 there and refuses the rest, this branch draws all 2,469 and refuses none. The
two assertion lines agree again.

**WHAT IT COST THE FRAME, A/B against `origin/dev` at `c39167b4`, T-0135's five stands**
(`tools/measure_detail_ceilings.mjs`, published mirrors, both trees read the same hour):

| stand | desktop `full` dev → mine | desktop `balanced` dev → mine | desktop `light` dev → mine |
|---|---|---|---|
| the Sauganash at 26 m | 899,526 → 899,526 | 825,775 → 825,775 | 544,614 → **545,732** |
| Lake at Canal, east | 1,362,043 → 1,362,043 | 1,197,353 → 1,197,353 | 755,194 → 755,194 |
| the forks, from Wolf Point | 1,376,419 → 1,376,419 | 1,213,481 → 1,213,481 | 746,022 → **746,867** |
| Lake and Market | 1,064,062 → 1,064,062 | 974,173 → 974,173 | 636,914 → 636,914 |
| the open aerial | 886,392 → **888,277** | 803,447 → **804,071** | 540,462 → **542,126** |

**`full` and `balanced` are identical to the triangle at four of the five stands**, and
the fifth — the open aerial — moves by 1,885 and 624 against 511,723 of headroom. `light`
moves at three stands by 845–1,664 and passes by 29,806. **Draw calls do not move at any
stand at any tier**: nine sets before, nine after. That is what the head ring predicts —
a head is drawn only near the camera, and no gate stand stands in the dense forest or on
the settled blocks where the two sets were filling.

**The one tier over its ceiling is `dev`'s and is unchanged by this**: desktop `balanced`
reads 1,213,481 of 1,210,000 at the forks on BOTH trees, to the triangle. That is
T-0203/T-0218's parcel, and this run's fresh reading is written onto T-0218.

**Route 2** — one head set with a per-instance shape, removing the nine-way split — is not
taken and is not needed: the split costs nothing now the shares are sized, and collapsing
nine archetypes into one parameterised geometry is a different and much larger argument
about what an inflorescence record is allowed to specify.
