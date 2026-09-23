---
id: T-1448
title: Mint the staffing shortfall to the model's typical band: the 105 reconstructed hands 96 houses are still short, written as a stage of the resident reconstruction programme into cards of their own, each carrying its house, its role and where it slept, and nothing already committed written to
state: open
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1434
opened: 2026-09-20
closed: null
pr: null
claimed_by: run 9/20/2026, 7:46:36 AM CT
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35511233651
---

Mint the staffing shortfall to the model's typical band: the 105 reconstructed hands 96 houses are still short, written as a stage of the resident reconstruction programme into cards of their own, each carrying its house, its role and where it slept, and nothing already committed written to.

Piece 1 of 2 of **T-1434 — Mint the staffing shortfall to the model's typical band and close the join: new reconstructed staff where a business is still short, every working-age person a workplace or an explicit not_employed reason, the order book's employment buckets filled and the business card printing its people**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. The hands the staffing model's TYPICAL band wants and no house has are derived per
   house and per role row, from committed files only, with `count_low` and `count_high`
   carried beside every row so the other answers can be priced.
2. A class that names the same role twice — the journeyman printer and the printer's
   boy — has the hands standing in the house allotted across both rows before either
   is called short. A hand is never counted against two rows.
3. What the reconstruction order book can pay for is read from the book's own
   outstanding `.../trade` buckets, and a slot pays for a hand only where the two
   vocabularies OVERLAP in years and the role's sex rule allows that sex.
4. Nothing is minted, no bucket's `filled` moves, no `fills` row is added and no card
   or business record is written to.
5. `--check` re-derives the order byte for byte and is in `tools/check.sh`;
   `--self-test` fires seven assertions.

**What it demonstrated — and why the mint did not run.** The shops want **129 hands**
over **88 houses**. The order book — the only quota this project holds, and the one
whose `no_bucket_overfilled` invariant refuses a stage that draws past it — has **109
outstanding `.../trade` slots**. They do not meet, and they miss in three separate ways:

- **On the count.** 129 wanted against 109 outstanding: 20 short before any axis is
  looked at.
- **On the sex.** Every one of the 129 is a man or a role the model calls
  predominantly male. 40 of the book's 109 slots are women's and cannot be spent here
  at all.
- **On the age.** 24 of the hands are boys of twelve to eighteen. The book's 10–19
  trade buckets are drawn out; there is no slot a shop boy could be minted into.

Spend the book greedily in the stated order and it pays for **55** of the 129. The
other **74** have nowhere to come from. Every outstanding slot is a `lodging/trade`
bucket owned by **T-1175**, so even the 55 would be spent out of another stage's quota.

Minting to the typical band therefore means one of three things, and all three change
what the town IS: re-cut the book (T-1166), come down off the typical band toward the
model's own `count_low` of 65, or let the houses stand short and have the business card
say so. `data/reconstruction/1835_staffing_mint_order.json` carries the numbers for all
three. **Blocked on the owner.**

**Findings handed on.**
- T-1449 ("close the join and print it") cannot finish either: there are no minted
  hands to put on `staff[]`. Its other clause — every working-age person a workplace or
  an explicit `not_employed` reason — does not depend on the mint.
- T-1433's 62 unseatable domestics are NOT in this order. Their taverns are full to the
  model's HIGH band, so they are a town owed more lodging houses, not a house short of
  hands.


## THE OWNER'S RULING, 2026-09-20 — option 1, and only the remainder

Asked which of the three the town takes, the owner ruled **RE-CUT THE BOOK (T-1166)**,
and then, asked what becomes of the people already drawn against the old cut, ruled
**re-cut just the remainder**.

So the two halves of the answer are:

- **The cut changes.** The town's remaining working people are younger and more male
  than a cut shaped by the 1840 schedule's bands makes them. This is the answer that
  lets the mint run to the typical band.
- **Nothing already drawn moves.** The 1,370 persons standing in 78 filled buckets stay
  where they are. The re-cut applies to `to_reconstruct` minus `filled` — the remainder —
  and never re-opens a bucket a stage has already spent against.

**THE EVIDENCE IS ALREADY IN THE MODEL, which is why this is a re-cut and not a new
reading.** `1835_town_model.json` carries it in terms:

> Households drawn symmetrically break the adult sex ratio (146.8 males per 100 females
> aged 20 and over in 1840, and higher in 1835). The surplus men are boarders and
> lodgers, not husbands.

The model said it; the book's trade cut did not carry it through. That is the gap this
ruling closes, and it is why no page of any source has to be read again.

**Measured exposure, on the committed book:** 199 buckets, of which **78 have
`filled > 0`** — 1,370 persons already drawn, the largest being T-1174 at 856, T-1347 at
308, T-1171 at 124 and T-1175 at 75. Those are the buckets the ruling protects. 2,299
remain to reconstruct and are the re-cut's subject.

**T-1448 is unblocked by this**, and the mint it asks for now waits on the re-cut rather
than on a decision. The re-cut is T-1166's successor and is filed separately; this
ticket's own work — minting the shortfall into cards — runs once the remainder can pay
for it.


## WHAT THE RE-CUT RETURNED, 2026-09-21 (T-1459, PR #1611)

The re-cut ran and **moved nothing**, so the mint this ticket asks for still cannot be paid
for — but the reason has changed from a decision to a measurement, and it is now a specific
one.

- **The age argument was made and holds.** The trade cut's age floor is now read off the
  town's own record rather than assumed: 127 people in the layer carry an occupation a
  source records, nine of them aged 15-19, so the `10_19` band is open at 0.2828 of the
  adult participation rate. The 24 shop boys are no longer barred by a band that does not
  exist.
- **The sex argument was refused, and that refusal is final for this book.** 120 of the 127
  are men, and that figure is survivorship — the sources that print an occupation print
  proprietors. The remainder is not re-cut male. The hands a shop wants that only a man can
  fill stand short.
- **And the band has no remainder.** Every cell of it has been drawn against: T-1174 drew
  its children at home and T-1175 seated its boarders. A bucket carrying a counter cannot be
  re-cut at all, because `seat_lodgers_1835.py` reads a bucket's whole `to_reconstruct` and
  re-deals its entire draw when one slot of it moves — measured, and filed as **T-1503**.

**So this ticket now waits on T-1503**, not on the re-cut and not on a ruling. When the
lodging stage draws against its own remainder, the 10_19 band's 35 undrawn slots become
spendable and the mint can run against them. Until then the shops stand short and the
business card says so, which was always the third of the three answers.


## WHAT T-1503 RETURNED, 2026-09-21 — the band has a remainder now, and it is 35

T-1503 gave the lodging stage a committed `quota_basis` and the re-cut was re-run. **35 of
the 36 slots it wanted moved.** The 10-19 trade band is no longer a row of noughts, and
nobody already drawn moved to make room — `seat_lodgers_1835.py --check` is clean and its
56 boarders are byte for byte what they were.

| cell | slots |
|---|---|
| `persons/male/10_19/south/lodging/trade` | 10 |
| `persons/female/10_19/south/lodging/trade` | 9 |
| `persons/male/10_19/west/lodging/trade` | 5 |
| `persons/male/10_19/north/lodging/trade` | 4 |
| `persons/female/10_19/west/lodging/trade` | 4 |
| `persons/female/10_19/north/lodging/trade` | 3 |

**THE AGE ARGUMENT IS PAID FOR NOW, AND IT DOES NOT MAKE THIS MINT LARGER. That is the
measurement and it is worth reading twice.** `1835_staffing_mint_order.json` re-derives to:

| | before the re-cut | after |
|---|---|---|
| slots outstanding in a band that reaches the shop boys | **0** | **35** |
| what the book could pay for today | 38 | **36** |
| what would go unpaid | 92 | **94** |
| payable, men's slots | 39 | 36 |
| payable, women's slots | 22 | 25 |

The band opened and the mint got two slots SMALLER, because the re-cut moves slots within
a cell — `none` to `trade` — and never across the sex axis, which is the refusal T-1459
made on the evidence and did not withdraw. 16 of the 35 landed in the three FEMALE 10-19
cells, and every one of the 130 hands a shop wants is a man or a role the model calls
predominantly male, so those 16 cannot be spent here at all. The adult male cells paid for
them out of slots that could.

**So the three answers are unchanged in kind, and the arithmetic against them is now
current.** 130 hands wanted over 88 houses; 36 payable; 94 with nowhere to come from. The
age bar is gone, the sex bar is where T-1459 left it, and the count is 94 short rather
than 92. Price the choice between the typical band and the model's `count_low` of 65
against THESE figures, not the 2026-09-20 ones above.

**And the remaining 27 slots are held by a named cause, not by a decision.** The re-cut
wanted 27 more out of the `10_19 family` cells and could not take them: `T-1171`,
`T-1174` and `T-1347` deal against the book's live `to_reconstruct` the way the lodging
stage used to, so re-cutting a cell they have drawn against re-deals their whole draw. The
book names them bucket by bucket in `trade_re_cut.held_by_an_unaudited_stage`, and the fix
for each is the one T-1503 made: a committed basis, then a line in
`REMAINDER_STABLE_STAGES`.
