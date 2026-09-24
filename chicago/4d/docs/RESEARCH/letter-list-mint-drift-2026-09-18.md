# The letter-list mint's 798 files, counted — 2026-09-18

Measured on `origin/dev` at `076051973` by `tools/letter_list_mint_drift.py`, and re-run unchanged after rebasing onto `68ad5bd82`, which reads
`tools/mint_letter_list_residents.py`'s own derivation against the committed tree. T-1334's
first acceptance is that the drift is **measured and named** — *a number, not "it drifts"* —
and this is that reading.

**798 has been carried in prose since T-0662 and it says nothing on its own.** 798 could be
one harmless note-prefix repeated 798 times; it could be the town gaining a hundred people
nobody has read. It is both, in known proportions, and the proportions are the finding.

## The town, if the mint ran today

| | |
| --- | ---: |
| households the mint holds | 791 |
| candidates the mint refuses | 1,088 |
| households the layer carries under this pass's mark | 743 |
| files that differ | 798 |

## What a re-run would do

| class | files | what it is |
| --- | ---: | --- |
| people **GAINED** | 45 | a household the mint derives that is on no committed card, under a name the layer holds nowhere |
| households **RENAMED** | 9 | a re-mint of a name the layer already holds under another id |
| people **LOST** | 6 | a committed letter-list household the mint no longer derives at all |
| cards **REWRITTEN** | 737 | a household both sides hold, differing in fields |
| `index.json` | 1 | the manifest, which follows all of the above |

45 + 9 + 6 + 737 + 1 = 798.

**Sixty of the 798 are people, not prose.** That is the half of this number the prose has
never described: forty-five households the mint would add to the town, nine it would re-mint
under a changed id, six it would take away. `--report` prints all sixty by name.

## The 737 rewritten cards, by who owns the key that moved

Counting each card once per owner it touches:

| files | owner |
| ---: | --- |
| 737 | `synthesize_resident_research.py` / `spend_ladder_rungs.py` |
| 23 | the mint itself |
| 11 | the resident-research passes |
| 6 | the arrival and origin fill stage (T-1169) |

And by the **exact set** of owners each card's difference touches, which is the cut that says
how much of the 798 is one prefix repeated and how much is somebody's work:

| files | owners |
| ---: | --- |
| 700 | the projection and the ladder, and nothing else |
| 21 | the mint + the projection and the ladder |
| 8 | the projection and the ladder + the resident-research passes |
| 5 | the projection and the ladder + the arrival and origin fill stage |
| 2 | the mint + the projection and the ladder + the resident-research passes |
| 1 | the projection and the ladder + the arrival stage + the resident-research passes |

## Every key that moved, and who owns it

| files | key | owner |
| ---: | --- | --- |
| 716 | `persons[].note` | the projection and the ladder |
| 694 | `persons[].grade` | the projection and the ladder |
| 8 | `persons[].sources[]` | the resident-research passes |
| 8 | `present_on_scene_date.note` | the mint |
| 7 | `persons[].letter_list_only` | the mint |
| 6 | `arrival.note` | the mint |
| 6 | `arrival.value` | the mint |
| 6 | `origin.confidence` | the arrival and origin fill stage |
| 6 | `origin.note` | the arrival and origin fill stage |
| 6 | `origin.sources` | the arrival and origin fill stage |
| 6 | `origin.value` | the arrival and origin fill stage |
| 6 | `persons[].occupation.note` | the resident-research passes |
| 6 | `persons[].occupation.sources` | the resident-research passes |
| 5 | `persons[].occupation.confidence` | the resident-research passes |
| 5 | `persons[].occupation.value` | the resident-research passes |
| 3 | `name` | the mint |
| 3 | `persons[].name` | the mint |
| 2 | `persons[].letter_list_returns` | the mint |
| 2 | `persons[].letter_list_returns[]` | the mint |
| 2 | `arrival.confidence` | the mint |
| 2 | `arrival.precision` | the mint |
| 2 | `arrival.sources[]` | the mint |
| 2 | `origin.tier` | the arrival and origin fill stage |
| 1 | `present_on_scene_date.last_dated_appearance` | the mint |
| 1 | `present_on_scene_date.value` | the mint |

**No key is unattributed.** The tool's owner table is in its source with the evidence for
each attribution beside it, and any key that table does not claim comes out under
`UNATTRIBUTED` in the report rather than being folded into a bucket. Today there are none.

## Why the two trees disagree

Two separate causes, and they want different answers.

**1. The pipeline's order (700 cards, and the part of 37 more).** The mint is not the last
writer of the files it derives. `synthesize_resident_research.py` runs after it and rewrites
`grade`, `resident_subtype`, `note`, `sources` and `resident_research` on the `letter_list_only`
cohort — that rewrite IS the PROJECTED RESIDENT downgrade — and `spend_ladder_rungs.py`
regrades on the owner's ratified rungs (G1b, G2e) after that. Re-running the mint over the
committed tree therefore REVERTS both: it puts grades back from `inferred` to `attested` and
strips the qualifier off post-office-only names, which is a confidence upgrade this project
forbids. Three more passes are in the same position on fewer cards — the resident-research
passes' occupations and corroborating sources (11 cards), and T-1169's `origin` block, which
marks itself `written_by_stage: attribute_fill_arrival` (6 cards). **A byte-identity check at
the mint's place in the pipeline is red against a CORRECT tree**, which is T-1222's finding and
this reading agrees with it.

**2. The mint's own derivation has moved (60 people and 23 cards).** The register's
letter-list readings were re-read — T-1115 refused bracketed name readings at the resident
mint, T-1138 settled three contested lines, T-1155 put a transcriber's supplied letters back
into the names — and **the mint has not been run since**. The register's person count is
unchanged at 2,685 across every commit that touched it this month, so nothing was added to
the corpus: the NAMES moved, and with them the ids `household_id()` mints and the candidates
the refusals admit. This is not a pipeline-ordering artefact and no later pass owns it. It is
the mint owing the town a run.

## Where this leaves T-1222, which owns the gate

T-1222 measured the same 798 on 2026-09-17 and cut them four ways: 648 differing in nothing
but the five projection keys, 81 households the mint no longer derives, 54 ids the splitter
mints differently, 14 mint-owned changes. **This reading and that one disagree about the
shape, and the disagreement is stated here rather than resolved in either.** Two differences,
one real and one a matter of where a line is drawn:

- **The withdrawals.** T-1222 counted 81; this counts **6**. The 6 are the committed
  letter-list households the mint no longer derives at all (`hh_adains_will_si`,
  `hh_bandle_will_nm`, `hh_crisey_william`, `hh_pease_h`, `hh_plumer_f`,
  `hh_swena_benjam_n`) — the only files a re-run would DELETE. `hh_abbott_constant`, which
  T-1222 names as one of its 81, is not among them today: the mint derives it, and the
  difference is its `arrival.value` and its `letter_list_returns` moving with a re-read
  return. Eight passes merged into `dev` between the two readings; this one is the later.
- **The additions.** T-1222's 54 "ids the name splitter now mints differently" are counted
  here as **45 people the town would gain** and **9 re-mints**, because the two are not the
  same event and the difference is a person. A household id the layer does not hold, whose
  head's name matches no person in the layer under any spelling, is not a re-spelling of
  anything — it is Isaac Scarritt, Sally Weed, Platt Thorn and forty-two more, and nobody has
  read them. Only 9 of the 54 are the `hh_adains_will_si` → `hh_adains_willisi` shape T-1222
  describes.

What both readings agree on, and what the gate has to be built around: the 700 are the
pipeline's order and cannot be gated by byte identity at the mint's place in it; the rest are
work somebody has to do. **T-1222 owns the check.** This ticket does not write one, does not
add a step to `check.sh`, and changes no resident record — the 45 gains in particular are a
reading, not a by-product, and minting them off the back of a drift measurement is exactly
the thing the ticket forbids.

## Reproducing it

```
python3 tools/letter_list_mint_drift.py           # the report, with all sixty people named
python3 tools/letter_list_mint_drift.py --json    # the same numbers, for a program
```
