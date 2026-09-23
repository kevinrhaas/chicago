---
id: T-1033
title: Read the town-lot deposit into records: append the ids, declare its firms, and make tract() resolve or refuse a lot-and-block-in-a-named-town without inventing a section
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1028
opened: 2026-09-11
closed: 2026-09-11
pr: 1125
claimed_by: run 9/11/2026, 6:54:57 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T12:48:58.012Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34596064091
---

Read the town-lot deposit into records: append the ids, declare its firms, and make tract() resolve or refuse a lot-and-block-in-a-named-town without inventing a section.

Piece 2 of 2 of **T-1028 — The 619 town-lot sales the by-section sweep cannot see: Cook County's register describes a lot and block with no section, so 466 sales of 1836 — the town's own ground — are outside the land_sales deposit**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- `isa_land_tract_sales_cook_town_lots_through_1836.tsv` joins `DEPOSITS`, its record
  ids APPENDED so nothing already cited by `data/structures/*.json` renumbers.
- `tract()` either resolves a lot-and-block-in-a-named-town or REFUSES it with a stated
  reason; it never guesses which plat a town code names and never invents a section.
- Every firm the reading finds is declared in `KNOWN_FIRMS` after its rows are read.
- `coverage.json § completeness_probe` re-derives to
  `complete_for_1836_cook_county: true`, or says precisely what is still outside it.
- No resident is minted or regraded. A purchase is a transaction.

**What T-1032 already measured for it** — the four tract forms, the three refusals, the
57 blocks, the `CHIOTVO`/`VO` trap and the 255 purchaser spellings — is in that ticket
and in `data/research/land_sales/README.md` § *The 619 read*.

**THE FIELD IS TWELVE CHARACTERS WIDE, so 131 of the town codes cannot be read as
complete** (filed 2026-09-11 from the withdrawn duplicate reading on PR #1123, which
read the same 619 rows independently and agreed with this deposit letter for letter).

No `aliquot_or_lot` in the file is longer than 12 characters and **154 of the 619 are
exactly 12** — the register's column ends there. So a 12-character row has been cut if
there was more to print, and its town code is a PREFIX of what the clerk wrote, not
necessarily the whole of it.

| the code as it stands | rows | of those, 12 chars — at the edge | rows with room to spare |
|---|---|---|---|
| `CHIOT` | 336 | 19 | 317 |
| `CHIOTV` | 107 | 103 | 4 |
| `CHIV` | 93 | 3 | 90 |
| `CHI` | 62 | 9 | 53 |
| `CHIOTVO` | 20 | **20** | **0** |

**131 of the 154 full-width rows end in `CHI`, `CHIOT` or `CHIOTV`, each of which is a
proper prefix of a longer code this same file attests.** `E2E2L1B46CHI` may be `CHI`,
`CHIV`, `CHIOT`, `CHIOTV` or `CHIOTVO`; the page does not say. The other 23 end in
`CHIV` or `CHIOTVO`, which are not prefixes of anything else here.

**This is where the `VO` trap comes from, and it cuts the other way too.** `CHIOTVO` is
the longest code and appears on 20 rows, every one of them at the field edge — which is
what it must do, since it can only be printed whole when the lot and block take five
characters or fewer. The consequence for the parse is not that `CHIOTVO` is doubtful; it
is that **some of the 103 full-width `CHIOTV` rows may be `CHIOTVO` with the O cut off**,
and nothing on the page distinguishes them. A `tract()` that reads a trailing `VO` as
VOID would therefore be deciding a sale's validity on a character the column had room
for — which is exactly the guess this ticket's acceptance forbids.

**What this asks of the acceptance, without weakening it:** a 12-character description's
town code is a REFUSAL with a stated reason ("the register's field ends here and the code
may be cut"), not a resolution, unless something off the page settles it. The 465 rows
under 12 characters are unaffected.

**Not read from a page image.** This is arithmetic over the committed deposit and can be
re-derived from it at any time; nothing here is a new source.
