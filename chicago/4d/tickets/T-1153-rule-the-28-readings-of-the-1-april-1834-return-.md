---
id: T-1153
title: Rule the 28 readings of the 1 April 1834 return where the page and the extraction set a name differently, and lift the two lines no claim carries
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-15
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1291
needs_bake: false
closed_at: 2026-09-17T19:18:46.160Z
claimed_run: null
---

Rule the 28 readings of the 1 April 1834 return where the page and the extraction set a
name differently, and lift the two lines no claim carries.

**Filed by T-1141**, which read all 193 printed lines of the return at the 8 April
impression and built `letter_list_1834_04_01_concordance.json`. That pass is T-1010's twin
for April: it counts and it moves nothing. THIS one is T-1139's twin — the adjudication —
and it carries T-1141's own two tails.

## 1. The 28 disagreements (the ledger's `name_differs`)

Each row is a line where the 8 April page and one or more extractions set the name
differently. T-0321's rule says the PAGE overturns a transcription; T-1139's rule says the
card may keep its own spelling where a source OUTSIDE this return outranks the image
there, and that file must name the source. Both are needed, because some of these are
plainly the image winning and at least one is plainly not:

| line | page | extraction | reaches |
|---|---|---|---|
|   7 | `Clark B. Albe` | `Clark B. Albe[e]` (04_01) | refused |
|  13 | `Josept Babeax` | `[uncertain: Joseph Babeax]` (04_01) | refused |
|  23 | `Lyman Bennett` | `Lyman Bennet` (04_01) | minted |
|  27 | `Eli Bona` | `Eli Benn` (04_08) | minted |
|  60 | `Tila[m] Dayton 2` | `[uncertain: Titan Dayton]` (04_01) | refused |
|  61 | `Hexekiah Duncklo` | `[uncertain: — Duncklo]` (04_08) | refused |
|  62 | `Lewis D[?]ud` | `Lewis Doud` (04_16) | minted |
|  63 | `William Denny` | `[uncertain: — Denny]` (04_08) | refused |
|  64 | `Pierce Dowaer` | `Pierce Downer` (04_01) | refused |
|  80 | `John C. Hugunin 2` | `[uncertain: John C. Hngunin]` (04_01) | refused |
|  84 | `Nathan Hutchins` | `Nathan Hutchin[g]s` (04_01) | refused |
|  85 | `Manen Hauks` | `[uncertain: Manen Hanks]` (04_01) | refused |
|  94 | `Thomas Hartsell` | `Thomas Hartec[l]l` (04_01) | refused |
| 106 | `Ivin Lou` | `[uncertain: Wm. Lou]` (04_01) | refused |
| 107 | `Jacob S. Lansing 3` | `Jacob L[a]nsing` (04_01) | refused |
| 111 | `B. H. Laughton` | `[S.] A. H. Laughton` (04_01) | held_already |
| 120 | `Jomes Mulford` | `[uncertain: James Mulford]` (04_08) | held_already |
| 134 | `Robt. Ogilley` | `Robt. Ogil[v]ey` (04_01) | refused |
| 137 | `Dadly Peck` | `D[u]dly Peck` (04_01) | refused |
| 149 | `Thos. H. Richy 2` | `[Thos. H.] Ritchy` (04_01) | refused |
| 156 | `Eli Strattan` | `Eli Stratt[o]n` (04_01) | refused |
| 164 | `Orin R. Stevens` | `Orin N. Stevens` (04_01) | refused |
| 165 | `Peter Schauder` | `Peter Schander` (04_01) | minted |
| 166 | `Stephen M. Salsby` | `[uncertain: Stephen M. Satsby]` (04_01) | refused |
| 177 | `Elam Teller` | `Elam Tuller` (04_16) | minted |
| 178 | `Alason B. Vaughan` | `Jason B. Vaughan` (04_01) | refused |
| 179 | `Amy C. West 2` | `Amy C. Wear` (04_01) | minted |
| 193 | `Philip Whittermore` | `Philip Whitte[m]ore` (04_01) | refused |

`Pierce Dowaer` at line 64 is the one that shows why this is an adjudication and not a
rewrite. The town holds `hh_downer_pierce`, and Pierce Downer is documented outside this
return; what the 8 April type sets at that line is `Dowaer`, which is what a broken `n`
looks like. The ledger records the disagreement and refuses to act on it — that refusal is
this ticket's work, not T-1141's.

## 2. The two lines no claim carries

`P. Cook` (line 48) and `Jeter Foster` (line 68) are printed on the page and are carried by
none of the six claims the corpus holds for this return: the 1 April transcription drops
both, the 16 April extraction saw both and could not read them (its own debris lines 3835
`p, Cock` and 3855 `Jeter oats`), and the 8 April supplement was written before either was
known. They need T-1011's lift — one claim in `chicago_democrat_1834_04_08.json`, in that
tool's shape — after which the mint's refusals reach them like every other name.

## BLOCKED ON T-1137, and this is why the tails are here rather than in T-1141's PR

Both halves end in one run of `tools/mint_letter_list_residents.py`, and on 2026-09-15 that
writer rewrote **744 files, 25,932 deletions, whole households deleted** on the committed
tree *with no edit at all*. The measurement is on T-1137, which owns the question. Until a
run can write that pass without taking those deletions with it, neither half of this ticket
can be shipped honestly.

## Acceptance

1. Every one of the 28 rows is ruled: the card takes the image's reading, or it keeps its
   own and the ruling names the source outside this return that outranks the image there.
   `letter_list_1834_04_01_name_rulings.json`, in T-1139's shape.
2. A card whose name moves is WITHDRAWN and re-minted rather than renamed in place — the
   rule T-1138 applied to its three.
3. `P. Cook` and `Jeter Foster` are lifted into the extraction of the impression they were
   read at, and each is then minted or refused by one of `mint_letter_list_residents.py`'s
   own named refusals.
4. The concordance's `--check` is re-derived and green afterwards, and a ruled row moves
   out of `name_differs` the way January's does.
5. `./tools/check.sh` green.

**Links:** T-1141 (the reading and the ledger) · T-1139 (the shape of the rulings) ·
T-1011 (the shape of the lift) · T-1138 (the withdrawal rule) · T-0321 (the page overturns
a transcription) · T-1137 (the blocker)
