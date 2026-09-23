# Can this repository reproduce the bytes it publishes?

**Parcel K40** (ROADMAP · KERNEL) · measured 2026-08-16 · **a measurement and four decisions,
not a change to any asset**

K39 recorded, for every one of the 334 published derivatives, the sha256 of the master it was
made from — and could not verify the record the obvious way, by regenerating a derivative and
comparing bytes, because `tools/web_derivatives.sh` did not produce the bytes on the site. On a
20-asset sample it reproduced 6. K39 reported the shortfall as a lower bound of **195** taken
from a vertex signature, and named the exact count, the price and the decision as this parcel.

Everything below is measured with `tools/measure_web_reproduction.py`, which runs
`tools/web_derivatives.sh` itself — never a reimplementation of it — over all 334 masters into a
scratch tree and compares md5s. It is chunked because the control costs ~13 minutes and a steward
run's harness caps one foreground command at ten; that shape is now in the tool, so the next
parcel that wants this number does not have to invent the loop.

---

## 0. Headline

| | |
|---|---|
| derivatives | **334** |
| reproduced byte-for-byte by today's step | **142** |
| **not** reproduced | **192** |
| of those, reproduced byte-for-byte under `BAKE_PALETTE=1` | **189** — the palette-era set, counted exactly |
| reproduced under neither step | **3**, and all three were already owned |
| cost of regenerating every failure | **+48,328 bytes** (+1.01 % of the 4,764,664-byte tree, +0.18 % of the 25 MB budget) |

And the finding that changes what the parcel was for:

**THIS RUNNER'S CONTROL IS THE NIGHTLY'S OUTPUT, ON ALL 189, AND THE REWRITE IS NOT SCHEDULED —
IT IS OPEN.** Bake PR #175 (`steward/bake-31933246760`, opened 07:34 UTC on 2026-08-16) rewrites
**280 derivatives**, and every one of the 192 this parcel measured as non-reproducing is in it.
On the 189 palette-era files the nightly's bytes and this runner's control are **identical, 189
of 189, md5 for md5**. So the sentence the whole no-Blender repair strategy rests on — *this
runner can regenerate what the nightly ships* — is true after all, and now has a control behind
it rather than a comment.

---

## 1. The census, and what the three exceptions are

The 192 failures decompose completely, with nothing left over:

| | |
|---|---|
| reproduce under `BAKE_PALETTE=1` — made by the step K36(b) turned off | **189** |
| `recon_1835_blk_randolph_clark_h2_02__inferred_1835.glb` | K37's open end |
| `recon_1835_blk_randolph_wells_h2_01__inferred_1835.glb` | K37's open end |
| `terrain__e1834_harbor_cut.glb` | R-W6(b) |

The two `recon_…_h2_…` files are the two of the ninety placeholders that K37 measured compressing
**smaller** (−808 and −816 bytes) and left as master passthroughs by name. Today's step compresses
them (8,712 → 7,904 and 8,728 → 7,912), so they fail a byte comparison for a reason that is
recorded and decided rather than unknown. The terrain is committed at 14 bits against the step's
16-bit ask, which is R-W6(b) in one file; the control produces 688,348 bytes and so does the
nightly, which is R-W6's own quoted +1,116.

## 2. The price, both ways

Over the 189 palette-era files alone: **+48,836 bytes**, mean **+258** per asset, and **all 189
grow** — an unwelded file carries the vertices the weld merged. The worst single asset is
`fort_dearborn_garrison_garden__fence_1816.glb` at **+7,240** (6,288 → 7,488 vertices). Against
the whole tree the net is **+48,328** once the two placeholders' −1,624 is counted in.

K39's sample estimated +197 per asset from 14 files; the true figure is +258 from 189. Its
sample also under-read the reproduction rate — 6 of 20 (30 %) against the true 142 of 334
(42.5 %), or 51 of 241 (21 %) counting only the compressed derivatives.

**10,491 vertices** are merged across the palette-era set (K39's 10,513 counted its 195).

## 3. The vertex signature is not the palette signature — REFUTED

K39 counted derivatives carrying fewer vertices than their masters, found 195, and reasoned that
*"only the palette-era step produces this"*. Measured against the exact control, the two sets
differ in **both** directions:

| | |
|---|---|
| in both the welded set and the failure set | 189 |
| **welded, and reproduced exactly by today's step** | **6** |
| failed, with no weld at all | 3 (the exceptions in §1) |

The six are `beaubien_barn__converted_1817`, `clybourn_slaughterhouse__log_1827`,
`estray_pen__pen_1833`, `log_jail__log_1833`, `recon_1835_south_a1_046__inferred_1835` and
`wolf_point_tavern_stable__stable_1831`, each dropping 2–4 vertices: `optimize` dedups without
the palette pass. So the signature is neither the set nor a bound on it, and **195 is a number to
stop quoting**. It arrived at the right order of magnitude by a route that does not hold, which
is the more useful thing to know about it. `tools/measure_web_reproduction.py` prints the proxy
next to the exact answer for exactly this reason, and no gate is built on the vertex count.

## 4. Decision — who moves the 189, and why

**Nobody, in this parcel: the nightly already has, and the diff now has a number on it.**

The parcel was written expecting a choice between regenerating 195 binary files on a runner that
cannot finish the desktop smoke, and letting a nightly land them as a diff nobody could review.
Measuring first removed the choice and left only the second half of the problem, which is the
real one. Bake PR #175's 280 changed derivatives decompose exactly:

| | |
|---|---|
| the palette-era set, unwelded | **189** |
| the 90 placeholder masters, upgraded to canonical archetype bakes (`recon_1835_*`, 5 KB boxes → 25–83 KB buildings) | **90** |
| `terrain__e1834_harbor_cut.glb` at 16 bits — R-W6(b), landing on its own | **1** |
| | **280** |

Regenerating them here would duplicate 189 binary files that an open PR already holds, byte for
byte, and would need an acceptance this harness cannot run. So this parcel moves no asset. What
it leaves behind instead is the instrument: anyone can re-derive that decomposition in ~13
chunked minutes, and check a bake's binary diff against a count rather than reading it.

**The steward runs do not review that PR and this parcel does not merge it.** #175 and #164 carry
**no status checks at all** — a bot-opened PR does not trigger the dev gate — so what they need is
the gate run against them, which is the janitor's job and the owner's call, not a measurement's.

## 5. Decision — should the record name the STEP as well as the master? **No.**

K39 recorded the master and not the step, and asked whether a second field — the tool version and
the flag set — should exist, on the grounds that it would have caught this on the day K36(b)
landed. It would have. It should still not exist, and the measurement says why.

**The two ways to encode a step both fail here.**

*A flag-set string* is prose, and prose can be edited to make a red gate green. That is the one
property K39 deliberately denied the record: there is no `--write-record`, and the only remedy
for a mismatch is regenerating the bytes. A field a person can retype is a field that will be
retyped at 3 a.m.

*A hash of the script* is not editable, and it is wrong in a way that is measurable. The step has
been changed **four times** since K36(b) lifted it out of `tools/bake.sh`, and the derivatives
that actually changed in those four commits were:

| commit | derivatives changed |
|---|---|
| K36(b) — the palette pass off | 38 |
| K37 — the size rule | 3 |
| K38 — the passthrough gate | **0** |
| K39 — the master record | **0** |

A script hash would have invalidated all 334 entries on each of the four, twice on a commit that
moved no byte at all — and the script is 380 lines of which most are comment, so any parcel
writing down what it learned would go red too. A gate that fires on documentation trains people
to bank it without reading, which is the failure `tools/web_derivative_baseline.json`'s own note
warns about.

**What the step change actually needed was a rule, not a field.** K36(b) turned a pass off and
regenerated the 38 assets that showed the fault; the other 195 kept bytes no step in the tree
could produce, and it took three days and two parcels to find out. So:

> **A change to `tools/web_derivatives.sh` that changes any derivative's bytes regenerates all
> 334, not the ones that visibly broke.**

It is in the step's header now. It is deliberately not a gate: the only exact test is the control,
the control costs 13 minutes, and `tools/check.sh` is ~90 seconds because a gate that takes four
minutes gets skipped. A cheap gate here would have to be the vertex signature, and §3 is the
measurement that says the vertex signature does not answer this question.

---

## Method, and what this does not claim

`tools/measure_web_reproduction.py --chunk K/N` runs `tools/web_derivatives.sh --out <scratch>
--only <name>` per asset; `--palette-chunk K/N` re-runs the failures with `BAKE_PALETTE=1`;
`--report` compares md5s and prints §0. The tool refuses to write into `assets/` under any flag.
Measured on gltf-transform **4.4.2**, ~2.4 s per asset, 334 assets in four chunks of 3 min 21 s.

It does **not** claim that a future bake's bytes are predictable in general. The control runs the
derivative step over the **committed** masters; a bake runs Blender first, and a master that moves
takes its derivative with it — which is exactly what the 90 placeholder upgrades in §4 are. The
claim is narrower and checkable: for a master that does not move, this runner's step and the
nightly's step now produce the same file, and 189 of 189 is the evidence.
