# Back-projection — what an 1835 business does with a door printed after 1835

*Policy. Written for T-0633, 2026-09-04, on the owner's instruction of the same day:
"there are business references that have addresses later and while we don't have that in
1835, you might use a documented address from later to position the business where you
have limited other information or it could contribute." The tool is
`tools/back_project_addresses.py`, the ledger is
`data/research/directories/address_back_projection.json`, the liberty is **L218**, and
the gate is a step in `tools/check.sh`.*

## The fourth grammar

Three documents already answer a way a source places a building, and all three read a
source written **inside** the target year:

| the source says | what it constrains | the policy |
|---|---|---|
| a platted street and nothing narrower | a **face** | `docs/STREET-FACE-ADOPTION.md`, L212 |
| a count of doors off a named corner | a **position along a face** | `docs/CORNER-ORDINAL.md`, L215 |
| a lot and a block | the **plat's own unit** | `docs/LOT-ADDRESS.md`, L216 |
| a street, printed four to nine years later | a **face, read backwards** | this document, L218 |

The fourth arrived with T-0632, which spent four directory crosswalks onto the people
they name and left **87 addresses** on the record — Fergus's Chicago directories of 1839
and 1843 and Norris's of 1844, each printed against somebody the 1835 corpus already
holds. Against that: **20 of 825 households carry a real `lives_at` and 50 a real
`works_at`.** The town prints trades far more often than it prints doors, and the volumes
that print doors are all later than the scene.

An address printed in 1844 is not an address in 1835, and that is the whole of the
difficulty. Chicago between 1835 and 1844 roughly quadrupled, re-platted its river
frontage, renamed streets and numbered them for the first time. Reading a door backwards
across that is a **reconstruction**, and this document exists so that it is a stated one.

## The four clauses

A later address may position an 1835 business **only** when all four hold. They are
evaluated in the order written, and the record says which one decided it — so a refusal
names the first clause that failed, not every clause that would have.

**1. The 1835 record has to attest a business to position.** A person the 1835 corpus
gives no trade — `occupation: none_recorded`, this dataset's own word for an absent
record — has no business for a later door to place. This pass never mints a business out
of a directory printed after the scene date, and clause 1 is where that is enforced
rather than promised. It is also, by a distance, the largest refusal: **39 of the 87**.

**2. Nothing better places it.** An attested 1835 placement always wins: a household
carrying a real `works_at` is left exactly where it is and the later address moves
nothing. A newspaper's *"three doors north of the Tremont House"* wins the same way,
through `docs/CORNER-ORDINAL.md`, because it is a reading of the scene year. And a
directory's **residence** address — its own `res` or `bds`, or `house`, `h` and `r`,
which is Norris's shorthand for the same word — is not this pass's claim at all:
positioning a home from a later door is the same mechanism aimed at a different question,
and it is **T-0669**. The pattern that reads those words is shared with that pass rather
than copied, and T-0987 stretch 6 is why it now names six of them: until Norris's parse
was let across one line at a time, no `house` address had ever reached this clause, and
the first that did — `house N Water st`, Silvester Marsh's home — was placed here as a
shop.

**3. The address has to resolve onto the 1835 street grid** — the street existed under
that name, in that place, on the scene date. `data/streets/1835.json` is that record and
the tool holds to it, with a table of names it accepts and a table of names it refuses,
each refusal written out:

- `Michigan ave` is **not** `Michigan Street`. Michigan Avenue is the lakefront street
  south of the river; the 1835 layer's Michigan Street runs east from La Salle on the
  north side. The 1839 directory prints both, four entries apart.
- `North Dearborn street` is a north-side street of a name the 1835 layer does not carry
  north of the river — its Dearborn runs from Madison to the south bank and stops. The
  north-side street on that meridian in 1835 is Wolcott.
- `West Water street` is the west-bank riverfront street; the 1835 layer carries Market
  and no West Water.
- Madison, Monroe, Adams and Jackson are at or south of the plat's southern bound, so
  `Clark st cor. Monroe` places a grocer three blocks outside the modelled town. **The
  face resolves and the address is still refused**, because taking Clark and dropping the
  qualifier would put the shop somewhere the directory does not say it was.

- **A name the volume CONTRACTED is still that name** (T-1050). Norris's REMARKS page
  says so — "Abbreviations, which occur only in a very few words, will readily be
  understood; b stands for between; Rand for Randolph; Mad for Madison; Wash for
  Washinglon, &c." (printed page 21) — and his `&c.` covers eleven more the page never
  lists: `Ran`, `Dear`, `Wol`, `Frank`, `Kin`, `Clin`, `Mich`, `Mon`, `Jack`, `Ind`,
  `Wab` and `Ad`. `PRINTED_ABBREVIATION` expands them once, before either table is
  consulted, so a refusal is still written out exactly once. Each expansion is unique on
  the 1844 street list and every occurrence of every token, across all 4,235 addresses
  the four volumes print, is that street. Two consequences worth naming: a contraction
  hides a NOT_1835 name as well as an 1835 one, which is the fault T-1050 was filed for;
  and the scanner's word-splits fall out of the same table, because the first half of a
  broken `Wash ington` looks exactly like the contraction Norris declares. `Wat` is the
  one left unread — North or South Water, and the token cannot decide — and a
  contraction is read only where the page sets it as a word of its own, because this OCR
  sets `and` as `;ind` and a damaged conjunction must not become Indiana Street.

Two 1835 streets that never meet cannot be a corner either, however the directory phrased
it: the tool intersects the two committed centrelines and refuses when they do not cross.

**4. The placement is graded `reconstructed` at best**, and its note says in plain words
that it is a later address read backwards and by how many years. There is no path in this
policy to `inferred` and none to `documented`.

## What a placement IS, and what it is not

**A FACE, and no roof.** `docs/STREET-FACE-ADOPTION.md` limit 3 is explicit that dealing
a business to one roof on a face "is an allocation, not a reading" — deterministic,
deliberate, and a statement about nothing. That allocation is defensible on top of an
advertisement printed in the scene year. Stacking it on top of an address already read
back four to nine years would produce a building attachment a reader would badly
over-read, and two inventions under one chip is exactly what this project's confidence
model exists to prevent. So the unit is the face — the unit the owner's ruling of
2026-08-29 says a street name constrains — and **`lives_at` and `works_at` are not
touched by this pass at all.** `tools/back_project_addresses.py --self-test` asserts
that, rather than the prose claiming it.

**A point only where the directory names a crossing**, in two kinds that are not one
claim:

| the directory prints | `placement` | what the point is |
|---|---|---|
| a street and nothing narrower | `face` | none — the face is the whole claim |
| `cor.`, `corner` | `corner` | where the two committed centrelines cross |
| `near`, `next`, `opposite`, `north of`, `bet` | `anchored` | the same crossing, with the distance from it **not** claimed |

**A house number is dropped, and the street crosses.** This is T-0632's rule inherited
rather than re-decided: *a street number in a grid this town's year does not have is
dropped while the street name crosses.* Chicago numbered its streets after 1835, so `159
Lake st` says Lake Street and nothing else this pass can use.

## What it reaches, measured 2026-09-04

| outcome | count |
|---|---|
| addresses adjudicated | **87** |
| **placed** | **15** — 13 faces, 2 anchored on a crossing |
| already better placed | 23 |
| refused, clause 1 — no 1835 business | 39 |
| refused, clause 2 — a residence, not a shop | 6 |
| refused, clause 3 — not on the 1835 grid | 4 |

Six faces are reached: South Water, Lake, Randolph, Clark, Dearborn and **North Water**,
which is the one `docs/STREET-FACE-ADOPTION.md` refusal 2 calls "the narrowest refusal in
the policy" — no roof's lot faces it and no roof ends a tier against it, so the
street-face programme cannot seat anybody there. Three of this pass's fifteen stand on
it, including **Wm. Sabine**, whom that document names twice as still unseated. They
stand on the face and not in a building, which is precisely the distinction this policy
is built to keep.

`lives_at` real values before **20**, after **20**. `works_at` before **50**, after
**50**. Neither moved, and neither was meant to: what fifteen businesses gained is a
face, on the record, graded and dated and reversible.

## Where it reaches a reader

The Evidence panel's *The town's people* section, on the household's own card, under the
directory entry the address was read out of — the outcome, the face, the grade, and the
note saying how many years it was carried. **Every one of the 87 is shown, refusals
included.** An address this pass declines is a reading it made, and a card that showed
only the fifteen would be reporting the pass's successes and hiding its arithmetic — the
same fault `residents.js` already refuses for the crosswalks' three match statuses.

Nothing is drawn. This follows **L2**'s precedent exactly: the fauna layer reaches a
visitor as text and its liberty says so in those words rather than overstating "rendered".
A back-projected face has no geometry because the policy deliberately declines to deal it
one.

## What would settle it

A source inside the scene year that prints a door. The 1835 poll and tax lists, the
land-sales tracts of **T-0609**, and Fergus 1839's appendix of Fort Dearborn Addition lot
sales (**T-0611**) are all closer to the year than a directory is, and any one of them
that places a business supersedes this pass under clause 2 without an argument: an 1835
placement always wins, and this policy's job is to be beaten.
