# T-0510 resident-research handoff — cohort 15 of 79

Frozen manifest: `chicago/4d/data/research/residents/pass_15_76_cohort.json` (76 people, not 79 —
T-0492 split the 228 remaining named residents 76/76/76 and the ticket's title kept the older number).

Reviewed **2026-09-05: 76/76 complete, 0 pending** — 18 corroborated, 6 corroborated in a later
volume only, 4 candidate identities retained unasserted, 48 documented no-corroboration outcomes.

## Artifacts

- `T-0510_resident_research.csv` — machine-readable export, one row per manifest person.
- `T-0510_resident_research_working.xlsx` — Residents, Candidates, Sources and Search_Log sheets.
- `sweep/` — the five stages that produced them, in order, with their own README.
- `chicago/4d/data/research/residents/pass_15_findings.json` — the authoritative outcome ledger.

## Method

Exact name first, then justified initial and OCR variants, across: the committed Chicago Democrat
and Chicago American transcriptions and the newspaper identity ledger; the town's 1833 tax list and
its 1834 and 1835 poll lists (IRAD); the Illinois public-domain land tract sales; the 1830 census of
the Chicago precinct; the 1840 census heads; the St Cyr and St Mary registers; Fergus 1839, Fergus
1843 and Norris 1844; **Fergus's Historical Series 26-29** — the 1843 Chicago Directory and
Wentworth's obituary lists; the Calumet Club old-settler rolls; the Newberry genealogical index
cards; and the Genealogy Trails transcriptions.

**Where the repository already holds a crosswalk verdict for a name, that verdict is quoted rather
than re-decided.** Twelve earlier passes and the domain crosswalks have adjudicated most of these
surnames already, and re-deciding them from scratch would have produced a second, unreconciled
opinion. What this pass adds on top is the reading of Fergus 26-29, which the directory claim
ledgers do not cover.

## The outcome rule

| outcome | means |
|---|---|
| `corroborated` | an agreement, forename for forename or initial for initial, with an independent source written **at or before** the scene year |
| `corroborated_enrichment` | the same agreement, but only in a volume printed **after** 1835: it enriches the biography and adds no 1835 attestation |
| `candidate_identity` | a plausible external identity with no date, place, occupation or kinship discriminator bridging it to the 1835 person |
| `no_corroboration` | the post-office lists and a documented refusal — a negative search, not evidence of absence |

## Where a later reading is written, and why it is not promoted

`tools/synthesize_resident_research.py` promotes canonical facts (occupation, arrival year, birth
year, family evidence) out of a completed row's `proposed_facts`, `evidence_for` and `summary`.
So this pass puts **contemporary** evidence in those fields and every **post-1835** volume reading in
`notes`, which the synthesizer does not read. Back-projecting a trade or an age across eight years
is T-0514/T-0515's decision under the ratified ladder, not this pass's, and the split is mechanical
rather than promised.

## What the Fergus volume gave up

Eleven readings the directory claim ledgers do not hold, quoted as printed and recorded in each
person's `notes`. Four resolve initials to full given names:

- **B. S. Morris** is *Buckner Smith Morris*, attorney, 59 Clark — "Chicago's 2d mayor, died December
  16, 1879, aged 79".
- **Philip F. W. Peck** is *Philip Ferdinand Wheeler Peck*, capitalist, 248 Clark.
- **George W. Snow** is *George Washington Snow*, lumber merchant, and the volume dates his death to
  the day: "at Altoona Pa., July 20, 1870, aged 72-10-13".
- **John S. C. Hogan** is *John Stephen Coates Hogan*, ex-postmaster — and the same volume
  **contradicts itself** about his death: the directory says Boonville, Mo., December 2, 1868, aged
  63; the obituary list says Memphis, Tenn., 1866. Both are recorded and neither is asserted.

Also **Elijah Dewey Harmon**, physician; **Russel Easton Heacock**, "Chicago's first attorney at
law"; **Hiram Pearsons**, speculator, boarding at the Tremont House; **Giles Spring** of Spring &
Goodrich; **Thomas J. V. Owen**, Indian agent, dead on **15 October 1835** — three and a half months
after the scene date; and **Alexander Robinson**, "died, on his Reservation, April 22, 1872, aged 83".

The one that did **not** survive is the most tempting. Fergus 1843 prints "Hoit, Thomas, carpenter,
bds Mrs. E. Holt [died 1881, aged 60]" — the exact name of this project's Thomas Hoit, and a trade
for a man whose 1835 record says no trade is recorded. **The age refuses it**: an 1881 death at 60
puts birth about 1821, which would make him fourteen when the Democrat printed the 1835 resident.
It is filed as a candidate and left unasserted.

## A tool defect this cohort exposed

The first full run promoted **`occupation=priest` onto Gregory E. Legg** and **`occupation=printer`
onto B. S. Morris**. Neither word was ever written about either man: `evidence_text()` scanned each
cited source record's *bibliographic citation*, and the St Cyr register was kept by a priest while
Norris 1844 was printed by Ellis & Fergus. A trade is now read only out of the pass's own words
about the person; the two spurious promotions are gone and the two legitimate ones (`hathaway_joshua`,
`woodworth_james_h`, both birth years, both from earlier tickets) are unchanged.

## Limits

Candidate identities stay unasserted and surname similarity is a clue, never a resolution. Negative
searches are documented negatives, not proof of nonexistence. FamilySearch and Ancestry are
login-walled and are recorded as inaccessible rather than absent; HathiTrust page views return 403.
Nothing here changes a grade by hand — the grade movement in this PR is the synthesizer's own
mechanical consequence of a letter-list person having been reviewed, which is the programme's
design and what the twelve earlier cohorts also did.

Cumulative reviewed total after T-0510: **744**. `letter_list_missing_research_row` falls from
**150 to 100**.
