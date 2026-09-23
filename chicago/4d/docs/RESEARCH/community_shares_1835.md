# The community shares of the 1835 layer — what they are, and what they are not

**T-1375, from T-1177. Derived, never hand-counted.** Every figure on this page is
printed by `python3 tools/derive_person_community.py --report`, off
`data/residents/community.json`, which `tools/check.sh` holds to re-derive from the
household records and `data/residents/community_rules.json`. Nothing here is a reading
of a source: no source was opened to write this file and nobody was minted.

## The figures below are T-1375's own run, and two of its empty rows have since been filled

**Addendum, 2026-09-19.** This page is the snapshot T-1375 printed on the day it derived
the attribute, and it is kept as that. Two of the five empty rows it ends on have since
been written, by the tickets it names:

| row | on this page | today |
|---|---:|---:|
| `native` | 0 (2 people carried the value by an origin sentence) | **87** — T-1376 carded the company the 1832 Chicago roll heads INDIAN |
| `free_black` | 0 | **15** — T-1377 wrote the free Black town to the FLOOR of its bracket: Caton's six or seven free coloured men of August 1833 below, the 1840 census's 53 free coloured persons carried back above. `docs/RESEARCH/black_chicago_1835.md` |

`german` is still nobody, and the Irish 341 are still what T-1378 checked against the
model. Everything else below stands as printed; re-run
`python3 tools/derive_person_community.py --report` for the current table.

## Read this before the table

**Half of this distribution is the reconstruction programme's own shares, handed back.**
Of the 2,436 people the layer can give a community, 1,167 — 48 per cent — are
reconstructed residents drawn from the name pools of
`data/reconstruction/1835_invented_name_pools.json`, and their community is the pool's,
because the pool is what they were drawn from. Counting them is counting the
programme's assumptions, not the town. The 1,269 people whose community is read off a
household's `origin` block are the half that is evidence, and even there the origin of
1,330 households is itself `reconstructed`.

So the table below is **a description of the layer, not a measurement of 1835**, and the
one line of it that can be checked against anything outside the layer is the New York
and New England share.

## The table

| community | people | of all 2,626 | of the 2,436 known |
|---|---:|---:|---:|
| New England (`yankee`) | 1,182 | 45.0% | 48.5% |
| New York State (`new_york`) | 502 | 19.1% | 20.6% |
| Irish (`irish`) | 341 | 13.0% | 14.0% |
| French Canadian (`french_canadian`) | 126 | 4.8% | 5.2% |
| Other (`other`) | 123 | 4.7% | 5.0% |
| British (`british`) | 97 | 3.7% | 4.0% |
| Southern (`southern`) | 63 | 2.4% | 2.6% |
| Metis (`metis`) | 2 | 0.1% | 0.1% |
| Potawatomi, Ottawa, Ojibwe, free Black, German | 0 | 0.0% | 0.0% |
| **unknown** | **190** | **7.2%** | — |

By the rule that fired: `origin_region` 1,262, `reconstruction_community` 1,167,
`stated_community` 7, and 190 with no rule — 174 in households that record no origin, 12
who are a boarder, lodger, servant or unnamed household member under a roof whose origin
is not evidence about them, and 4 in households whose origin this project has decided it
cannot read into a community (bare "Detroit"; "Chicago, by way of Fort Winnebago";
"Chicago — born at the settlement").

## Against the town model

`data/reconstruction/1835_town_model.json` § *Arrival and origin* holds the only origin
distribution this project has, and says in its own open questions that it is not the
town's: of the 70 Old Settlers who registered an arrival at or before 1835 and gave a
birthplace, 27 were born in New York State (0.386) and 25 elsewhere in New England — New
York and New England together, 0.743.

| figure | the model | this layer |
|---|---:|---:|
| New York State alone | 0.386 | **0.206** |
| New York and New England together | 0.743 | **0.691** |
| born abroad | a floor of 10 people | 564 (Irish, British and French Canadian) |

**The combined share lands inside the model's band and the New York line does not, and
the reason is a known artefact rather than a finding.** The `yankee` name pool is
labelled "New England and New York" and was assembled from both; 734 reconstructed
people were drawn from it and every one of them reads `yankee`. The layer cannot put any
of those 734 in New York, so New York is under-read by exactly the amount the pool
cannot separate — and `yankee` is over-read by the same amount. The combined line is the
one to compare, and it is 0.691 against 0.743.

**The foreign-born line is not a disagreement.** The model's 10 is a floor taken off the
Old Settlers roll — a self-selected sample registered forty-four years later, of men who
stayed and prospered — and its own note says the 1840 extract's foreign-born column was
never coded, so this project holds no measure of the town's foreign-born at all. 564 is
what the reconstruction programme ordered, chiefly 312 Irish from the pool of that name.

## The five empty rows are the point

`potawatomi`, `ottawa`, `ojibwe`, `free_black` and `german` are in the vocabulary and no
card carries any of them. That is not a gap in this pass — this pass reads no sources and
is forbidden by its own self-test from writing those five values. It is the measurement
T-1177 was opened to act on, now stated as a number:

- The Native and Metis town of 1835 reaches **two people** in this layer, Billy Caldwell
  and Alexander Robinson, and only because each card's origin sentence happens to state a
  parentage. The other six `touches_removal` households read `french_canadian`,
  `british`, `southern`, `new_york` or `unknown`. **T-1376** is the reading.
- The free Black town reaches **nobody**. The layer's only trace is Caton's 1833 defence
  of "six or seven free coloured men"; 1840 counts 53 free coloured persons. **T-1377**.
- German reaches nobody, and the Irish 341 are 312 pool draws against 29 households whose
  origin names Ireland. **T-1378** checks both against the model rather than minting again.

Two entries in the table are deliberately coarse and are the owner's to rule on:

- **`other` is 123 people the vocabulary has no term for** — 112 of "The Mid-Atlantic
  states", 16 "West of the Alleghenies", one Pennsylvania household and one man out of
  Lyons by way of the Missouri seminary. This pass will not fold Mid-Atlantic stock into
  `new_york`, which is a different claim from the one the origin makes.
- **`french_canadian` is this vocabulary's Great Lakes trade community**, so French birth
  is not it; `data/residents/community_rules.json` says so beside the Lyons rule.

## Where each value came from

`data/residents/community_rules.json` is the whole of it: the closed vocabulary, every
one of the 54 distinct `origin` strings in the layer accounted for exactly once — as a
stated community, as a region, or as explicitly unreadable — and the rule that a place is
not a community, so a region reading is capped at `inferred` however attested the origin.
An origin string that enters the layer without a decision in that file makes the gate red.
