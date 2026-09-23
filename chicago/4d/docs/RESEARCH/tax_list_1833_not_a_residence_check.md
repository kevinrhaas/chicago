# The 1833 tax list is a property roll, not a residence check

**T-1117.** Arthur Bronson's card said `present_on_scene_date: present` for 1 July 1835,
inferred from a bracket whose at-or-before leg was the Tax List of the Town of Chicago,
1833 — and the town's own historians print him a **visitor** from New York who went home:

> Two visitors to the settlement from New York — Charles Butler and Arthur Bronson — were
> so moved with commiseration at the sight of this apology for a library, that on their
> return home they sent on a donation of two hundred volumes.
> — Moses & Kirkland, *History of Chicago* vol. 2, printed page 367, claim `bk_mose2_021`

A town taxes a non-resident on the ground he holds in it, and Bronson held a great deal:
thirteen blocks of the school section in October 1833, and in 1834 the half of Kinzie's
Addition and the whole of Wolcott's, bought of General David Hunter with his associates.
So the question is not about one card. **Does the 1833 tax list distinguish a resident
payer from a non-resident one?**

## The answer, and it is the list's own

**No — and worse than no: it demonstrably admits a man who was not in the town.**

Two readings settle it, both already in this repository before this ticket was opened.

**1. On its face the list distinguishes nothing.** `civic/claims/town_findings_voter_lists.json`
v001, read for T-0493: *"The 1833 tax list of the Town of Chicago, as published, is a list
of NAMES ONLY. No assessed valuation, no lot, no amount of tax and no rank stands beside
any of its 115 entries."* There is no residence column, so there is no line drawn — not
for Bronson, and not for the other 114. Whatever the IRAD original carries, nobody in this
project has seen it.

**2. Entry 110 of the list is a man three years dead.** It reads `Wolcott, Alexander`
(`tax_1833_110`, text line 162). This project's own reading of Fergus's old-settler death
notices gives him:

> Wolcott, Dr. Alexander, Indian agent, died Oct. 25, 1830, aged 40; his will was the
> first probated in Cook County.
> — `fdn0742`, `fergus_1843_old_settler_death_notices`

Andreas has his house on the north bank *"left unoccupied by the death of Dr. Wolcott"*
(`docs/RESEARCH/cobweb_castle.md`). A man dead in October 1830 was not a resident of the
town of 1833. **His estate was**, under the name the probate carried, and the probate is
how the assessor came by it. The list is therefore a roll of OWNERS AND ESTATES. Some of
them lived in the town. Some did not. The page says which for nobody.

Two further entries stand on this list and on no poll list of 1833, 1834 or 1835:
`Allen, Lt. James` (entry 1) and `Hunter, David` (entry 47) — the Hunter who sold Bronson
the additions. That is consistent with the reading and it proves nothing on its own; the
refutation is Wolcott alone.

## The measurement that was tried and decides nothing

It is recorded rather than dropped, because the obvious argument is that a tax list full
of strangers would overlap the town's poll books badly. **It does not.** Folding entries
on surname and first initial, across the four lists this domain holds:

| | of the 29 distinct names on the 1833 poll list |
|---|---|
| also on the 1833 **tax** list | **15** |
| also on the 1834 poll list | 13 |

The tax list of 1833 captures the town's own voters of 1833 *better* than the next year's
poll book does. And the poll books overlap each other poorly in any case — 18 of the 84 on
the 1835 list stand on the 1834 one — so the town was turning over faster than these lists
can measure, and no argument about who is a stranger can be built on them. **The overlap
test is not evidence for the ruling and it is not evidence against it.**

## What changed, and what deliberately did not

**Presence, and only presence.** `tools/mint_civic_residents.py` now carries
`NOT_A_PRESENCE_CLASS = {"tax_1833"}`: the list is refused as a leg of the presence
bracket, because that bracket is the one claim in the card about where a **body** was on a
day. Thirteen households moved from `present` to `uncertain`, each with the withdrawal
written into the note rather than the old note deleted:

`hh_bell_william_a` · `hh_bronson_arthur` · `hh_cook_josiah_p` · `hh_cook_thomas` ·
`hh_foot_john` · `hh_foster_amos` · `hh_goodrich_john` · `hh_hunter_david` ·
`hh_kimberly_ira` · `hh_morrison_orsemus` · `hh_price_jeremiah` · `hh_rice_john` ·
`hh_williams_john_l`

The layer's presence counts move 461 → 448 `present` and 822 → 835 `uncertain`.

**`uncertain`, and never `absent`.** The Moses & Kirkland passage does not date the visit,
it does not say Bronson was elsewhere on 1 July 1835, and a New York capitalist with this
much Chicago ground may well have been in the town that summer. No source places any of
the thirteen anywhere else on the day. Withdrawing a bad reason for `present` is not a
reason for `absent`.

**The arrival bound STANDS, restated.** Every household the validator accepts carries a
dated `not_later_than` arrival, and this record does give one honestly: the town's
assessor had the name on his roll by the end of 1833. What it does not give is the man at
Chicago, so the sentence that used to say *"names this person at Chicago by 31 December
1833"* is gone rather than softened, and the note now says what the bound bounds.

**No grade moves.** The owner's ratified ladder (2026-09-03) spends this list at **G2b** —
*"an 1833 or 1834 list (poll, tax, the 1832 muster) with another source"* → `inferred` —
to date and corroborate a NAME in the town's own paper, and a property roll can still do
exactly that: the assessor knew the name, the ground and the year. Nothing on that rung
was ever a claim about a body on a day, so nothing on it had to move. No ticket is filed
against the ladder — there is no defect behind the question, only a wording that reads
more like a presence than the rung has ever spent.

**Nothing in `data/research/land_sales/resident_rulings.json` moves.** T-1017 already
settled that the `BRONSON ARTHUR` ruling is an IDENTITY ruling and stands either way.

**No card was hand-edited.** Every one of the thirteen is derived; the change is in the
pass, and `mint_civic_residents.py --check` re-derives all 414 byte for byte.

## What was NOT done

- **The IRAD original was not read.** The reading here is twice mediated — Schulz's
  transcription, then Genealogy Trails' republication — and the original is where an
  assessed valuation, a lot number or a residence column would be, if any exists.
- **The Illinois statute was not consulted.** The ruling is reached from the list's own
  membership, not from the town's charter or the 1831 incorporation act. Reasoning from
  what a town *may* tax would have been an argument; Wolcott is a reading.
- **The other 52 cards that rest on this list alone were not re-graded** — 53 households
  rest on `tax_1833` as their whole civic evidence, and 40 of them already read
  `uncertain`. Nothing about them needed to change for the ruling to hold.
- **`hh_wolcott_alexander` still reads `present`**, and it is the one card this ruling
  could not reach. Its at-or-before leg is not the tax list; it is the man's own death
  notice of 25 October 1830, bracketed against a directory of 1843. That is a second and
  separate defect — a death is not a presence, and `death_notices.json` already records
  `places_in_1835: false` for its whole class while `presence_block` does not read it.
  **T-1131** carried it, and read the answer off a field the domain had already
  published: `places_in_1835` is refused as an at-or-before leg of the bracket and left
  standing as an after leg, and this card became `absent` —
  `docs/RESEARCH/a_death_notice_is_not_a_presence.md`. The ruling's own star witness was
  the next ticket, which is a better outcome than quietly fixing two questions in one PR.

## How this stays true

`tools/assert_tax_roll_ruling.py`, wired into `tools/check.sh`, holds the two readings the
ruling stands on — entry 110 reads `Wolcott, Alexander`, and `fdn0742` dates his death
1830-10-25 with `places_in_1835: false`. If either moves the gate goes red and the ticket
reopens; the ruling is re-read off the page, never re-argued from this note. The cohort
count is printed and **not** asserted: the residents layer grows every week and the ruling
does not rest on a number.

`mint_civic_residents.py --gate` asserts the invariant on every card instead — no
household may read `present` with no at-or-before leg but a property roll — and
`--self-test` proves that refusal fires when broken, and that it has not swallowed the
poll lists with it.
