# The United States Indian Agency at Chicago, 1 July 1835

T-1374. What the corpus says about the agency establishment, what this project has now
written down, and — the larger half — what it has refused to write and why.

The record is `data/businesses/authored/biz_indian_agency_chicago.json`. It is a `civic`
establishment, like the post office, the land office and the county's rooms, and it counts
against no census line: the December 1835 State census runs through the trades and never
reaches a federal agency.

**AGENTS.md's standing constraint governs this page and that record.** The final removal of
the Potawatomi from Chicago is August 1835, six weeks after the scene date. Nothing here is
depicted, no figure is drawn for anybody, the August gathering is not staged, and the record
carries `review_required` until the review by Native scholars or community organisations that
this project has committed to has been sought.

## 1. The establishment, as the sources name it

Andreas names it in one sentence, under the agent's own name, and every one of these men
already stood in the resident layer graded `attested` on those same words. What did not
exist until now was the ESTABLISHMENT: six offices with no house to be offices of.

| Office | Man | Card | Evidence |
| --- | --- | --- | --- |
| Indian agent | Thomas Jefferson Vance Owen | `owen_thomas_jv` | Appointed in the winter of 1830-31, arrived spring 1831, agent at his death at Chicago 15 Oct 1835 |
| Sub-agent | Gholson Kercheval | `kercheval_gholson` | Ran the office until Owen arrived; the 1833 roster calls him "Government Agent and clerk" |
| Sub-agent | James Stuart | *none* | Named with Kercheval in the same roster sentence |
| Interpreter | Billy Caldwell (Sauganash) | `caldwell_billy` | "Billy Caldwell (Sauganash) as interpreter" |
| Blacksmith | David McKee | `mckee_david` | Government blacksmith, hired 1823 against the 1821 treaty obligation |
| Striker | Joseph Porthier | `porthier_joseph` | "and Joseph Porthier as striker"; the 1830-31 agency staffing lists the pair |

Two of those rows carry a ruling rather than a transcription.

**James Stuart gets no card out of this.** The office is attested on the same sentence as the
other five, so the row stands with `person_id: null` — a statement about the evidence, not a
placeholder. A business record may not mint a resident, and this one does not.

**The striker is written as a `blacksmith`.** A striker swings the sledge while the smith
holds; it is a distinct office and this project's occupation vocabulary has no word for it.
Porthier's own card ruled that years ago — *"The occupation vocabulary has no separate entry
for a striker and blacksmith is the trade he was in"* — and the business layer follows the
card rather than minting a seventh role word on one man on one line of one source. The word
`striker` appears in his row's prose, so the card prints what Andreas said.

The four role words this added to `data/businesses.schema.json` — `indian_agent`, `sub_agent`,
`interpreter`, `blacksmith` — were all already in `data/residents/index.json`
`.vocabulary.occupations`, which is the only door that enum opens by. T-1410 brought the four
civic offices through it and T-1421 the two church offices; these come the same way.

## 2. Where it stood, and why the record claims no roof

The location is `anchored` against the Agency House (`cobweb_castle`) and **not** a `premises`
there, and the reason is that the Agency House's own record argues against it. Andreas has it
*"left unoccupied by the death of Dr. Wolcott"* in 1830 and Colonel R. J. Hamilton living in it
in the autumn of 1832, with the agency's business running down through the 1833 treaty. A
`premises` row would have claimed an office in a building this project's own structure record
calls, most likely, somebody's private house.

What the sources do place is a **cluster**. Wau-Bun: *"Around the Agency House were grouped a
collection of log buildings, the residences of the different persons in the employ of
Government ... blacksmith, striker, and laborers."* Andreas puts McKee's shop *"near the Agency
House, at the foot of State Street"*, and the *"small log buildings occupied by the blacksmith,
Mr. McKee, and Billy Caldwell"* in the same vicinity. The three resident cards that carry
`works_at: cobweb_castle` grade that `inferred` for exactly this reason; the location is capped
at the grade those cards are.

One building of the establishment IS standing in this town, and it is the second location:
`blacksmith_shop_state_st`, named "Government Blacksmith Shop", `function: blacksmith_shop` at
`attested`, "the agency smithy" among its aka. It is not the primary row — an agency is
transacted at an office and shod at a forge — but it is the one premises of these six offices
that a visitor can be pointed at.

**A street row was considered and refused.** `data/streets/1835.json` holds `state`, which is
State Street on the SOUTH side of the river; there is no `state_north` corridor. "At the foot
of State Street" is the north bank, so a `street_only` row on `state` would have put the agency
across the water from itself. The anchor is the honest form.

## 3. The counted-but-unnamed: what is NOT written here

This is the half of T-1374 the ticket names second and the corpus answers worst.

Wau-Bun's ring of log buildings holds *"the different persons in the employ of Government ...
blacksmith, striker, and laborers."* The blacksmith and the striker are named. **The laborers
are not** — not named, not numbered, not dated. The sentence describes the agency house's
surroundings as Juliette Kinzie knew them, which is the early 1830s and not July 1835.

So the figures, stated plainly:

- **Named employees of the agency in the corpus: six.** All six are above, all six are carded
  or ruled, and five of the six already held a `attested` occupation on this evidence.
- **Employees the corpus counts without naming: zero.** Wau-Bun's "laborers" is a plural noun,
  not a count. No roll, return, payroll or annuity schedule in this corpus enumerates the
  agency's hands.
- **Native and Métis people at Chicago on 1 July 1835, counted anywhere in this corpus: zero.**
  This is the same finding `reconstruct_underdocumented.py` states in
  `the_counted_but_unnamed` and T-1353 states for the crews of the vessels. There is no count,
  so there is no remainder to draw.
- **Families of the agency's employees drawn here: none.** The households of the five carded
  men are the residents layer's, on the residents layer's own evidence, and this record moves
  none of them.

**A remainder cannot be drawn out of a count that does not exist.** Drawing "some laborers"
for the agency would be minting people out of a plural noun, which is the one thing the
reconstruction programme's whole apparatus of buckets, seeds and `replaceable_by` exists to
stop somebody doing by hand. The order book holds no agency bucket, and this record does not
invent one: T-1177's stage `underdocumented` is the only writer permitted to card a Native or
Métis person at all, and it is not this record.

What would change the answer, in order of how much it would buy: an agency return or payroll
naming the hands; an annuity schedule for the Chicago agency; the 1833 treaty's own claims and
reservation schedules read against the layer. Each is filed as a source to read, not as a gap
to fill.

## 4. Two speculative smithies retired by it

Writing the agency down took two records OUT of the layer, and that is a correction rather
than a loss.

`tools/complete_inwindow_trades.py` raises a house for every tradesman whose dated role
reaches the scene date and whom the business layer gave nowhere to work. David McKee and
Joseph Porthier were two of them, so it had raised `biz_mckee_david_blacksmith` and
`biz_porthier_joseph_blacksmith` — each an `inferred` shop *"followed in a house of this
keeper's own"*, and each seated on `blacksmith_shop_state_st`.

That house is the Government Blacksmith Shop. Neither man kept a shop of his own there:
McKee held a federal appointment against the 1821 treaty obligation and Porthier struck for
him. The raised records were the layer saying, correctly, that two men with a trade had no
workplace — and answering it with the only form it had, a private shop.

Now that the agency exists and names them both as staff, `--build` stops raising either one
and the tool's own `--check` retires them. Two conjectural one-man smithies at a federal
forge are replaced by one establishment that says whose forge it was. The count moves from
40 authored records counted by the trade census to 38, and `data/research/residents/
inwindow_trade_workplaces.json` records the change.

## 5. What this record did not move

- **No presence verdict.** Kercheval's card still reads `present_on_scene_date: uncertain` on a
  last dated reading 643 days before the scene date. A seat is an office a source gives a man;
  it is not a statement that he stood in the town that morning.
- **No occupation.** Every one of the five carded men already held the office as an occupation.
  Nothing on a resident card was rewritten.
- **No community reading.** `proprietor_community` is `unknown` with rule `no_person_linked`: a
  United States agency has no proprietor to read one off, and reading it off the staff would
  make a federal office Potawatomi because it employed a Potawatomi interpreter.
- **No date.** The agency at Chicago is older than this establishment — Wolcott held it before
  Owen, the treaty blacksmith was hired in 1823 — and no source here names the day it stopped.
  Both ends are unbounded.

**Sources:** `andreas_1884_v1`, `kinzie_waubun_1856`. **Links:** T-1374 · T-1176 · T-1348 ·
T-1349 · T-1177 · `docs/RESEARCH/fort_dearborn.md` · `AGENTS.md` § Standing constraint.
