---
id: T-0951
title: Two husband-name printings R6 cannot reach: Mrs. T. G. Hadley and Mrs. Wm. B. Egan are merged onto their husbands because no single source prints both readings
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-10
pr: 1077
claimed_by: run 9/10/2026, 11:27:05 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T16:27:05.172Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34496514416
---

Two husband-name printings R6 cannot reach: Mrs. T. G. Hadley and Mrs. Wm. B. Egan are merged onto their husbands because no single source prints both readings.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0723, 2026-09-06.** R6 holds a female honorific apart from the man whose name
it stands on, and it fires only where ONE SOURCE prints both readings as separate entries —
Fergus 1843 setting `Brown, Rufus B.` at 458 and `Brown, Mrs. Rufus B.` at 459. That proof
is what keeps the rule from splitting `Mrs. Eliza Haight` off the census's `Eliza Haight`,
who is one woman: nothing in the letters of a name says Rufus is a man and Eliza is not.

Two printings have the husband-name shape and no such page:

| the honorific reading | the bare reading | why R6 stands down |
|---|---|---|
| `Hadley, Mrs. T. G.` — Fergus 1843, e1164 | `Hadley, T. G.` — Norris 1844, e0769 | two directories, two years |
| `Mrs. Wm. B. Egan` — the 1833-1835 papers | `Egan, Wm. B.` — Norris 1844, e0562 | the press and a directory |

Both are almost certainly a wife under her husband's name — Fergus 1843 also prints
`Hadley, Timothy Gibson` and `Hadley, Elijah W.`, and the Egan household card is Dr William
Bradshaw Egan's. Neither has the page that would prove it, so both stay merged onto the
husband and neither woman has a card or a rung of her own.

**Acceptance:** each of the two is read on its own page — the Fergus and Norris entries in
full, and the newspaper printing of Mrs Wm. B. Egan — and either a source is found that
names the woman apart from her husband (which lands her as her own identity, with the
citation), or the pair is ruled one person with the reasoning written down. Nothing is
split on the shape of the name alone. If the reading turns up a THIRD shape R6 should
reach, the rule is widened with the evidence in hand, not on the strength of these two.

**Links:** T-0723 · `tools/consolidate_resident_evidence.py` rule R6 ·
`data/residents/card_merge_rulings.json` rule D3

**A THIRD SHAPE, FOUND BY T-0960, 2026-09-10 — and it is not the same fault.** The two rows
above are printings R6 LOOKS AT and stands down from for want of a page. `Taylor, Mrs. C.`
(the Chicago Democrat of 19 August 1835, c007) is one R6 never looks at at all: the printed
forename is an INITIAL, so the honorific strip leaves `Taylor, C.`, which is not the bare
reading `Taylor, Charles` letter for letter, and R6's exact-match test — the test that is
correct for `Mrs. Rufus B. Brown` — simply does not fire. M2 takes her instead, because an
initial-only forename attaches to the one full forename of that surname carrying it, and
Charles is the only C-Taylor in the corpus. So a woman printed under a female honorific was
folded onto a man by the ordinary initial rule, with no refusal recorded anywhere.

T-0960 gave her her own card by hand (`hh_taylor_c`, G1b off the Democrat) and left the
consolidation untouched, so `identity_master.json` still spends `person_taylor_mrs_c` on
`id_taylor_charles`. That is the third shape this ticket's last paragraph asks about, held
here with the evidence in hand rather than widened on the strength of one row: any widening
has to say what stops `Mrs. C. Taylor` splitting off a `Charles Taylor` the corpus prints
without an honorific WHEN THEY REALLY ARE ONE HOUSEHOLD'S TWO READINGS — the same question
the Haight case asks of the exact-match rule, one initial further down.

---

## RULED, 2026-09-10 — and R6 was widened, with the evidence in hand

**Both were read on their own pages, out of the committed corpus rather than a fresh scan:**
Fergus 1843 e1164 and e1166, Norris 1844 e0768 and e0769, and the Chicago Democrat of
1 April 1834, claim c001.

**HADLEY — a source DOES name her apart, and the fault was never the want of a page.**
Fergus 1843 sets `Hadley, Mrs. T. G. (Reed), dress and cloak maker, 147½ Lake` at e1164 and
`Hadley, Timothy Gibson (Howard & H.), res alley bet N. Dearborn and Wolcott` at e1166 —
two entries in one page-run, two trades, two addresses, and her own maiden name in the
parenthesis the directory keeps for a firm. Norris 1844 repeats the pair at e0768 and e0769,
the dress and cloak maker still at 147½ Lake. That IS R6's proof shape. What kept the rule
off her is that her entry carries her husband's INITIALS and his carries his whole name, so
the letter-for-letter test never looked and M2 folded her on by the ordinary initial rule —
the same fault T-0960 found one printing further down with `Taylor, Mrs. C.`

**So R6 is widened, and this is the third shape the ticket's last paragraph asked for.** An
initials-only honorific reading now reaches the one full forename of its surname that its
initials fit, **in its own source**, and is refused where more than one fits (R3's
discipline). The guard that matters is untouched: one source has to print both. Three
self-tests hold the widening — the Hadley pair, a rival that refuses it, and the same pair
split across two directories, which still stands the rule down — beside the four T-0723
already had.

**What it reaches, every one checked by hand: five printings, three new identities.**

| the honorific reading | the bare reading, same source | verdict |
|---|---|---|
| `Hadley, Mrs. T. G. (Reed), dress and cloak maker, 147½ Lake` | `Hadley, Timothy Gibson (Howard & H.)`, Fergus 1843 | held apart |
| `Kernikerbacker, Mrs. S. R., dressmaker, res south of First` | `Kernikerbacker, Samuel R., shoemaker, res south of First`, Fergus 1843 | held apart |
| `Anderson, Mrs. G. milliner and straw hat maker, 3d door N. of P. O.` | `Anderson, George, wigmaker, Clark st. 3d door N. of P. O.`, Norris 1844 | held apart — she joins the Fergus 1843 reading R6 already held |
| `Smith, Miss M., teacher public school 3, district 4` | `Smith, Matthias`, Fergus 1843 — the one M-forename of 29 Smiths | held apart |
| `Taylor, Mrs. C.` — the Democrat of 19 August 1835 | `Charles Taylor`, the same papers | held apart — **T-0960's residual, closed** |

Four of the five are a wife in her own trade at her husband's own address: a dress and cloak
maker, a dressmaker, a milliner, and a public-school teacher who is nobody's wife at all. The
fifth is the woman T-0960 gave a card to by hand; `identity_master.json` no longer spends
`person_taylor_mrs_c` on `id_taylor_charles`, so the card and the consolidation now agree.

**Neither Hadley is a resident of 1835.** The town holds no Hadley card, and a directory of
1843 puts nobody in the town of July 1835. This ruling moves a research identity, not a
person on the ground.

**EGAN — ruled the other way, and no card is minted.** `Mrs. Wm. B. Egan` is one line of the
list of letters uncalled-for at the Chicago post office, the Democrat of 1 April 1834, c001 —
the same list that prints `Mrs. Robt. Hountton` two names later. No body prints a bare
`Wm. B. Egan` beside her, so R6 stands down, and the widening does not reach her either:
`Wm` is an abbreviation and not an initial. **It does not need to.** The town already holds
the woman under her own forename — `egan_emeline`, Emeline Egan, wife, attested off Andreas,
on Dr William Bradshaw Egan's own card. So the ruling is simply that the line is HERS: a
letter waiting for `Mrs. Wm. B. Egan` met the man's NAME and not the man, exactly as the
Second Presbyterian roll's 34 husband-name lines already say, and it is not evidence that
Dr Egan was at the post office in April 1834. Written down in
`data/residents/card_merge_rulings.json` → `also_ruled_on`.

**Filed on the way past: nothing.** One thing is worth naming here rather than as a ticket,
under the filing rule: Fergus 1843's `f1843_e1234` runs two directory lines into one claim —
`Hathaway, L. W., clerk, Samuel B. Collins & Co., res Wabash ave Hathaway, Mrs., dressmaker`
— so a third dressmaker is inside a man's entry where no rule can see her. That is a
transcription fault in the claims corpus and not a merge fault, and it belongs to whichever
ticket next re-reads the Fergus 1843 page images.
