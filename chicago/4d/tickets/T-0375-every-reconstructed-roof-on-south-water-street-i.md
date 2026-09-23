---
id: T-0375
title: Every reconstructed roof on South Water Street is a labourer's, so five documented tradesmen the papers put there have nowhere to stand
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 560
claimed_by: run 8/29/2026, 2:32:19 PM CT
blocked_on: null
needs_bake: false
---

Every reconstructed roof on South Water Street is a labourer's, so five documented tradesmen the papers put there have nowhere to stand.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found while landing T-0367, which gave the deal a way to ask which street a
reconstructed roof fronts. Six documented tradesmen now reach that test and all
six are turned back by the same fact.

**Five roofs in this town front South Water Street and every one of them is a
labourer's.** So D. Graves the baker, A. Filer and Rockwell the joiners, and
L. W. Montgomery and John Holbrook the shoemakers — all placed on South Water by
their own advertisements — have no roof of their trade on the street the paper
names. J. B. Tuttle wants Dearborn, where the grocers have none either, and
J. H. Barnard wants Lake, where the town's one physician's roof is not.

`python3 tools/replace_invented_residents.py --report` prints the six with the
street each wanted and what his trade's roofs front instead;
`python3 tools/fronting_street.py` prints the frontage of every reconstructed
dwelling.

This is a fact about where the occupation census put the trades, not about the
evidence. The census is calibrated on counts per division and never asked which
street a roof would stand on, so the business streets drew labourers and the
tradesmen drew the inside of blocks.

**Acceptance:** (one demonstration, never weakened to pass)

- Either the trade a reconstructed roof carries can be argued against the street
  it fronts — a shoemaker's roof on South Water rather than a labourer's — with
  the argument recorded and the occupation census's per-division counts unchanged;
  or the answer is that it cannot, stated with the reason, and this ticket closes
  as refuted with the six refusals standing.
- If roofs do change trade, the before → after runs through
  `tools/replace_invented_residents.py --check` and names every documented man it
  seats.
- No confidence is upgraded and no roof moves to reach the result.

Related: **T-0367** (the frontage derivation), **T-0366**/**T-0264** (the deal),
**T-0263** and **T-0306** (which place the BUSINESSES on these same streets).

---

## THE ANSWER, 2026-08-29 — REFUTED, and the refusal it rests on now tells the truth

**It cannot, and the ticket's premise has been overtaken by a merge that landed the
same day it was filed.** Both halves are measured below on an unmodified `dev`; nothing
here is asserted.

### 1. Four of the six men are standing on the street the papers name — as storefronts

`docs/STREET-FACE-ADOPTION.md` is the owner's ruling of 2026-08-29 (T-0354, #551/#553):
a business the paper puts on a street and nothing narrower adopts a reconstructed roof
whose platted lot fronts that street. `python3 tools/adopt_street_faces.py --report`
prints the result, and four of this ticket's six tradesmen are in it (the roofs below are
the allocation as it stands after the identity merges of 2026-08-29; WHICH roof on the face
is the pass's allocation and re-derives, which is limit 3 of that policy):

| the man | stands on South Water Street as | roof |
|---|---|---|
| D. Graves, baker | `D. Graves` | `recon_1835_blk_south_water_dearborn_c3_01` |
| A. Filer, joiner | `A. Filer & Co.` | `recon_1835_blk_south_water_lasalle_d5_01` |
| L. W. Montgomery, shoemaker | `L. W. Montgomery, boot and shoe maker` | `recon_1835_blk_south_water_dearborn_a3_06` |
| John Holbrook, shoemaker | `John Holbrook` | `recon_1835_blk_south_water_lasalle_d4_02` |

So "have nowhere to stand" was never quite what refusal 8 meant, and after 2026-08-29 it
is plainly false. What these men are short of in `tools/replace_invented_residents.py` is
a DWELLING of their trade on that street, which is a narrower and true statement. The two
who are short of anything at all are **Rockwell** (joiner, South Water — the corpus
carries no business under that surname for the adoption pass to seat) and **J. B. Tuttle**
(grocer, Dearborn Street — where no roof's platted lot fronts the street at all, which is
STREET-FACE-ADOPTION.md's own reported cost).

### 2. And the household route is now barred rather than merely empty

**There is not one free roof left on the face.** Nineteen reconstructed roofs front South
Water Street: five are households' homes and the adoption pass has taken all fourteen of
the rest. Two of those fourteen are of the shoemakers' own family band
(`recon_1835_blk_south_water_franklin_d4_02` and `recon_1835_blk_south_water_lasalle_d4_02`,
both D4, both south division — so all three of the adoption tests in the inferred-household
programme's method rule 6 would pass, and the per-division counts would not move). Taking
them is the change this ticket asked about, and it was simulated rather than argued:
`adopt_street_faces.derive()` re-run with those two roofs marked as households' homes.

| | before | after |
|---|---:|---:|
| street-face adoptions, whole town | 24 | **22** |
| adopted on South Water Street | 14 | **12** |
| free roofs fronting South Water | 14 | **12** |
| refused `every roof on the face is spoken for` | 2 | **4** |

The cost is exactly one-for-one, because the face is exhausted. The two documented
businesses evicted are **`E. L. Thrall`** and **`the New Store at the corner of Water and
Clark streets`**. And the arithmetic is the mild part: `recon_1835_blk_south_water_lasalle_d4_02`
is **John Holbrook's own storefront** on today's derivation, so seating a shoemaker
household there to make room for John Holbrook would evict John Holbrook. The two men the
seats would go to — L. W. Montgomery and John Holbrook — would in any case then stand on
South Water Street TWICE, once as a storefront and once as a household head. Trading two documented
businesses for two duplicate seatings is not a demonstration; it is a regression.

### 3. The remaining trade is a claim about means, and no source carries it

The only way to put a tradesman's household on South Water without taking a roof from the
business pool is to trade one of the five D1 log cabins the labourers hold there for a
shoemaker's D4 two-room cottage. **The family band IS the claim** — D1 is the roughest
dwelling in the schedule and D4 a two-room frame cottage — so a shoemaker in the cabin and
a labourer in the cottage are two statements about those men's means that nothing in the
corpus supports, and the acceptance above forbids reaching the result that way. Refused.

### What changed in this PR

No record, roof, coordinate or confidence moves. `tools/replace_invented_residents.py`
reads `data/research/newspapers/street_face_adoptions.json` before it speaks: refusal 8
now names the adoption when there is one, so it can never again be read as saying the man
is absent from the town. The module docstring, which asserted in prose that these men
"have nowhere on it to go", says what is true instead.

**The six refusals stand, and three of the five that reach refusal 8 now say where the man
actually is** (D. Graves is refused earlier, under rule 5, and never reaches it).


---

## PARKED ON `hold`, 2026-08-29 — the measurement above is STALE and must be re-taken

**Read this before spending the section above.** The finding was measured three times
during one run, against `dev` at three different commits, because five slices were merging
into `dev` while it was being written. The THIRD merge — a sibling's storefront seeding —
moved the numbers the argument rests on, and this branch is parked rather than merged so
that a stale claim does not land in a repository whose one invariant is provenance.

| measured on `dev` at | South Water free roofs | adopted on the face | Holbrook adopted? | A. Filer adopted? |
|---|---:|---:|---|---|
| first pass (before the identity merges) | 14 | 14 | yes, `..._lasalle_d5_01` | yes, `..._wells_a3_08` |
| after the identity merges | 14 | 14 | yes, `..._lasalle_d4_02` | yes, `..._lasalle_d5_01` |
| **after the seeding merge (now)** | **9** | **9** | **no** | **no** |

So on today's tree only TWO of the six — D. Graves and L. W. Montgomery — are standing on
South Water Street through the adoption pass; Holbrook and Filer are back to `street_only`
and unadopted, because the seeding consumed five of the face's roofs. **The shape of the
answer is unchanged and if anything is stronger** — the face is more exhausted than it was,
so the one-for-one eviction cost of reseating a household onto it is higher, not lower —
but the ROOF IDS and the COUNTS in the section above are no longer the ones on the tree,
and a refutation whose numbers are wrong is not a refutation.

**What is safe to keep, and what must be re-derived.** The change to
`tools/replace_invented_residents.py` is safe and needs no re-measurement: it READS
`street_face_adoptions.json` rather than quoting it, so it re-derives with the tree and
already prints the truth on this commit (L. W. Montgomery has dropped off refusal 8
entirely; Filer and Holbrook are named without an adoption, correctly). Everything
NUMERIC — the table in § 1, the before/after in § 2, the matching paragraph in
`docs/STREET-FACE-ADOPTION.md` and the third bullet of the changelog entry — must be
re-run against whatever `dev` is when this is picked up:

    python3 tools/adopt_street_faces.py --report
    python3 tools/replace_invented_residents.py --report

The gate was green at every step (`check.sh` PASS; mobile 390x780 stages 1-2/3-4/5-6/7-9
and desktop 1280x800 stage 8 all SMOKE PASS, `--published`) — this is parked for accuracy,
not for a failure.
