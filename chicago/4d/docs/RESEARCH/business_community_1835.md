# The community of the 1835 houses of trade — what the register can say, and what it cannot

**T-1378, from T-1177. Derived, never hand-counted.** Every figure on this page is
printed by `python3 tools/compile_businesses.py --community-report`, off
`data/businesses/*.json`, which `tools/check.sh` holds to re-derive from
`data/research/newspapers/register_1835.json` and `data/residents/community.json`.
Nothing here is a reading of a source: no source was opened to write this file, no firm
was minted and no name was read.

## Read this before the table

`proprietor_community` stood at the literal string `unattested` on all 196 business
records from the day the layer was compiled, with the rule that kept it there written
beside it: **NEVER INFERRED FROM A SURNAME.** A community is a claim about a person, the
newspaper register makes no such claim, and reading one off the letters in a name is the
exact move `docs/RESEARCH/1835_population_profile.md` forbids — "using it as evidence
would manufacture exactly the attributions that ticket is required to mark as
reconstructed."

This pass fills the field without breaking that rule, because since T-1375 there is one
place where the claim about a person IS made and committed:
`data/residents/community.json`, derived off household `origin` blocks and the
reconstruction name pools. A house is read off the **people its own record names**, and
off nothing else. 209 proprietors and partners are named across the layer, 157 of them
resolve to a card the town holds, and every one of those cards is printed on the firm's
own card under *The community it is read as*, with the community it carries.

**The value is capped at `inferred`, always.** A person's community is evidence about the
person; a house is not its keeper. An attested keeper still yields an inferred house.

## The table

196 business records; 111 read a community, 85 do not.

| community | houses | of all 196 | of the 111 read |
|---|---:|---:|---:|
| New England (`yankee`) | 46 | 23.5% | 41.4% |
| New York State (`new_york`) | 41 | 20.9% | 36.9% |
| Other (`other`) | 10 | 5.1% | 9.0% |
| British (`british`) | 9 | 4.6% | 8.1% |
| Southern (`southern`) | 5 | 2.6% | 4.5% |
| Irish, German, free Black, Metis, French Canadian, and all four Native terms | 0 | 0.0% | 0.0% |
| **unknown** | **85** | **43.4%** | — |

By the rule that fired: `proprietors_agree` 111, `no_person_linked` 73,
`proprietors_disagree` 8, `no_community_on_the_people_named` 4. By tier: 94
`reconstructed`, 17 `inferred`, and 85 with none because the value is `unknown`.

**The 94 reconstructed readings are the honest size of this.** They are not reconstructed
firms — every one of these 196 houses is compiled from a printing. They are houses whose
keeper's community is itself read off a household `origin` block that the reconstruction
programme wrote, so the reading is no better than that block, and the ladder says so.
Only 17 houses reach `inferred`.

## The Irish and the German shares, checked against the model

This is the clause T-1378 was opened on, and the answer is a measurement rather than a
minting.

| | the resident layer | the business layer |
|---|---:|---:|
| Irish | 405 people, 15.3% of the 2,648 with a community | **0 houses** |
| German | 0 people | **0 houses** |
| free Black | 0 people | **0 houses** |
| Native and Metis | 89 people | **0 houses** |
| French Canadian | 126 people | **0 houses** |

**No house in this layer reads Irish, and it is not because the Irish keepers are
missing.** Two of the eight firms whose partners do not agree are part-Irish — Collins &
Caton (Irish, New York) and Brewster, Hogan & Co. (Irish, New England) — and the rule
refuses to hand either of them to one community on list order. Those are the only two
Irish traces in the whole business layer. The 405 Irish of the resident layer are
overwhelmingly draws from a name pool, against a few dozen households whose origin names
Ireland, and almost none of them keep a house the newspapers printed: the register is an advertising record of the
merchant class, so what it measures is who could afford a notice.

**German reads zero on both sides, so there is nothing here to check against.** The
resident layer has never written the term, and this pass is forbidden by its own rule
from being the first to: a German house would have to come from a keeper's card, and no
card says it. `T-1177` names the German town as a reading still owed.

**The Catholic share cannot be checked at all from this field.** The population profile
records 32 persons named in the St Mary's register — 1.5% of the layer — and a
confessional attribution is not a community in this vocabulary and is not derivable from
one. A business layer cannot carry a share the person layer does not hold.

## The eight houses whose keepers do not agree

| firm | what its keepers read |
|---|---|
| Brewster, Hogan & Co. | Irish, New England |
| Collins & Caton | Irish, New York |
| G. W. & W. Laird | Southern, New England |
| J. Wellmaker & Co. | British, New England |
| Jones, King & Co. | New York, Other, New England |
| Marsh & Simons | Southern, New England |
| Pierce & Abbott | New York, New England |
| Tuttle & Brown | New York, New England |

Each answers `unknown`, and each names every partner and every partner's community on its
card. A partnership between two communities is a finding about the town's trade, and
resolving it to whichever man the register printed first would destroy exactly that
finding.

## The two silences are told apart

73 houses name **nobody the resident layer holds a card for** (`no_person_linked`) — that
is a gap in the register, which prints 52 names the town never met and prints no name at
all for many a house. 4 houses name people the town cards and the resident layer knows no
community for any of them (`no_community_on_the_people_named`) — a gap in the resident
layer, and one T-1179's convergence can close. They are separate rules because they are
owed to different tickets.

## The empty rows are the point

`irish`, `german`, `free_black`, `metis`, `french_canadian`, `native`, `potawatomi`,
`ottawa` and `ojibwe` are all in the vocabulary and no house carries any of them. That is
the same statement `docs/RESEARCH/community_shares_1835.md` makes about the person layer's
five empty terms, made again one layer up, and it is what the cohort tickets exist to
shrink — **T-1377** for the Black-owned firms, **T-1182** for the audit of every attested
and inferred business, **T-1184**–**T-1189** for the trades the register never printed.
The Businesses view offers a pill only where the count is above zero, so an empty term
does not read as an available filter that finds nothing.

## Where each value came from

`data/residents/community_rules.json` — the resident layer's own closed vocabulary, now
literally the business layer's too. The schema used to carry a second list of its own
whose description already claimed to be shared with the resident layer, and was not: it
folded New England, New York, British and Southern into one `anglo_american` and said
`black` where the resident layer says `free_black`. Every record read `unattested` under
it, so ending the divergence cost no record a reading — but a house and its keeper are
counted in one set of terms from here on, which is the whole of what makes the Indian
trade and the Black-owned firms identifiable on one field.
