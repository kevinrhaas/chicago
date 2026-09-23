---
id: T-1459
title: Re-cut the order book's unfilled remainder to the adult sex ratio the town model already states, and reopen the 10-19 trade band the 1840 schedule drew out — the 78 filled buckets and their 1,370 drawn persons do not move
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-21
pr: 1611
claimed_by: run 9/21/2026, 12:29:43 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T06:57:03.178Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35564560037
---

Re-cut the order book's unfilled remainder to the adult sex ratio the town model already states, and reopen the 10-19 trade band the 1840 schedule drew out — the 78 filled buckets and their 1,370 drawn persons do not move.

**The owner's ruling of 2026-09-20**, on T-1448's three answers: take option 1, the
re-cut — and re-cut **just the remainder**. This ticket is that ruling turned into work.

## What the shops asked for, and why the book could not pay

`tools/staffing_mint_order_1835.py` (T-1448) set the staffing model beside the order book
and counted. The shops want **129 hands** and the book has **109 slots** left, and the
count is the smallest of the three disagreements:

| | |
|---|---:|
| hands wanted (typical band) | 129 |
| slots outstanding | 109 |
| what the book could pay for TODAY | **55** |
| what would go unpaid | **74** |

- **Sex.** All 129 wanted are men, or roles the model calls *predominantly male* — which
  the tool pays as male, because declining to refuse a woman the role is not evidence of
  one. **40 of the 109 slots are women's** and can pay for none of it.
- **Age.** **24 of the hands are boys of 12-18.** The book's `10_19` trade buckets are
  drawn out entirely: **zero** outstanding slots in any band that reaches them.

The demand is concentrated, which is what makes it arguable rather than diffuse: 44 clerks
(male, 16-25), 28 labourers (male, 18-45), 8 joiners and 8 joiner's boys, 7 domestic boys,
6 tavern keepers.

## The evidence is already committed — this is a re-cut, not a new reading

`data/reconstruction/1835_town_model.json` states it in terms:

> Households drawn symmetrically break the adult sex ratio (**146.8 males per 100 females
> aged 20 and over in 1840, and higher in 1835**). The surplus men are boarders and
> lodgers, not husbands.

The model says the town is more male than a symmetric draw; the book's TRADE cut did not
carry it through. No page of any source is read again here. **But note what that figure
does and does not settle**: 146.8:100 is a ~59.5% male share overall, and the remaining
trade slots are already 69/109 = 63% male. So the overall ratio does NOT by itself justify
an all-male trade remainder — the argument has to be about the TRADE cut specifically
(clerks, apprentices, shop hands), and it has to be made rather than assumed. A re-cut
that reaches the right answer by the wrong argument is the thing this project refuses.

## Only the remainder moves

**Measured on the committed book:** 199 buckets, **78 with `filled > 0`**, **1,370 persons
already drawn** — T-1174 856, T-1347 308, T-1171 124, T-1175 75, and four more. 2,299
remain to reconstruct.

The ruling protects every one of those 1,370. The re-cut's subject is
`to_reconstruct - filled` and nothing else.

**Acceptance:**

- The re-cut changes only the **unfilled remainder** of each bucket. A bucket's `filled`
  count is never lowered, no already-drawn person is unwritten, and `no_bucket_overfilled`
  holds before and after. A re-cut that would take a bucket's target below what has
  already been drawn against it is REFUSED by name, with the bucket and the two numbers —
  not silently clamped.
- **The trade cut carries an argument of its own**, written down: why the remaining trade
  hands are more male and younger than the 1840 schedule's bands make them, distinct from
  the town-wide 146.8:100 the model already states. If that argument cannot be made from
  committed files, the ticket says so and the remainder is NOT re-cut to suit the demand.
- The **`10_19` trade band is reopened** on the same terms — an apprentice and a shop boy
  are a trading town's ordinary establishment — or its absence is argued and the 24 boys
  stand short with the business card saying why.
- `tools/build_order_book_1835.py --check` re-derives, and its self-test gains a guard that
  fires when a re-cut lowers a bucket below its `filled`.
- **The seven tickets that have already drawn are named in the report** with what they
  spent, so a reader can see which parts of the book are settled history and which are
  still open. A re-cut that moves a quota under a stage which already spent is the one
  failure this ticket exists to make impossible.
- `docs/RESEARCH/1835_reconstruction_order_book.md` states the re-cut, its basis and its
  date; a liberty is recorded if the trade cut rests on typology rather than on a source.
- T-1448's mint runs against the re-cut remainder afterwards, not as part of this ticket.

**Stop condition:** the book's remainder can pay for the hands the shops want, or it says
in writing which hands it cannot pay for and why — and in neither case has a person already
drawn been moved, unwritten or re-ordered.

**Links:** T-1448 (the adjudication and the ruling) · T-1166 (owns the book) · T-1434 ·
T-1189 · T-1293 (the models the book subtracts from) ·
`data/reconstruction/1835_staffing_mint_order.json` — every figure above re-derives from it.
