# Open PR reconciliation — T-0976

The owner requested completion and disposition of the seven open Chicago 4D PRs after
T-0974. PR #1040 carries this reconciliation onto dev. The table records what survives,
what is superseded, and why; an already-completed ticket number alone is not a reason
to discard a branch.

| PR | Reviewed head | Disposition in #1040 |
|---|---|---|
| #1036 | `5d67145b5cf3adee70fb5cfdeb8f38d217905c57` | Import the complete PW recapitulation reading verbatim; update coverage; exclude its page-number rows from both identity consolidation and the census-head crosswalk. Close the old branch after this merge. |
| #1033 | `9b0f48a6e7fbd9f87649ebdebd0d1ecc890159bb` | Import BP and P5 verbatim; resolve T-0969 and T-0970; rebuild the dependent census and resident records. Close the old branch after this merge. |
| #1018 | `c8ec6e8282419725c6f7a19e18fb33fd6ac5e2f4` | Preserve the entire independent 6H reading under `second_readings/`. Its 40–49 inference for the sixth schools footing disagrees with dev's unresolved reading. Do not replace the canonical page or undo T-0755's seventh-column reading. |
| #1011 | `a7e486d084712b644fd01f162e6a0ee9632db898` | Preserve the entire n167 reading, including its blank-column observations and row geometry. Its line 13 manufactures/trades entry is 6; the canonical reading is 1. Other TOTAL/industry values agree after accounting for blank encoding. Preserve the disagreement rather than adding the same exposure as a second enumeration page. |
| #1009 | `ca5467de8fc71cbf0f47c58077ac322dcec1d25a` | Preserve both earlier names-only readings. The stored as-read/normalized pairs differ on 28 RY lines and all 30 RK lines, including spelling-only differences. Current T-0963 cells remain canonical. Merrill's land-purchase evidence is already on dev; the older branch would remove his current later-census paragraph. |
| #991 | `bf214d8e2c6dbeb957eb753ea0c4062fe5a09555` | Port the report-only `--compare-rules` path and its research note, retaining the current generator's other rules and count-as-output documentation. Re-measure: 1 garden under the household rule, 29 under the house rule, 28 added. Close the branch after this merge; T-0772's policy question remains blocked on the owner. |
| #971 | `b38f18454b30eca3da46f27d3fd29638cd43d182` | Keep dev's landed T-0837 synthesis and stronger date guard. Port the useful regression cases to current interfaces. Do not restore mirror writers removed by T-0938, drop finding-aid refusals, or loosen the scene-date condition to any year before 1835. |

## Preserved readings

`data/research/census_1840/second_readings/index.json` records each original path,
full PR head, SHA-256 of the verbatim JSON, canonical counterpart, and line-by-line name
differences. The archive is outside `pages/`, so readers cannot count the same exposure
twice or promote a competing reading into an identity assertion merely by scanning files.
The archive preserves all of #1011's additional blank observations, not just its disputed
trade digit. No new claim of having re-read those scans is made by this integration.

PW has thirty numbered pages, six ward groups and no household names. Its ward grouping
matches the grouping on printed 237; the two readings' population differences remain
unresolved. BP and P5 add 61 named lines and their cell readings. BP's ambiguous footing
stays ambiguous. P5's `Alex[r]. Loyd` stays as read.

## Identity repairs

T-0970 had two connected causes. The consolidation expanded `Alexr` but not `Alex` after
removing an uncertain bracketed letter, creating a rival forename and splitting `A. Loyd`
from Alexander. `Alex` now follows the same identity-only expansion already used by the
census crosswalk. Separately, the civic mint preserves the id and name of its own existing
card when `canonical_person_id` identifies it. A new matched spelling cannot change the
lookup used to carry forward directories and later evidence. The actual rebuild keeps
`hh_loyd_alexander`, `loyd_alexander`, Alexander's directory block and his existing
`present_on_scene_date` value and confidence, supplementing its existing citations with the census. It adds the census evidence; it does not create
`hh_loyd_a`.

T-0969 let `Mrs` stand as a forename. Leading courtesy titles now come off the forename
tokens, while a female style remains a separate identity key so Mrs Rufus Brown cannot
turn into Rufus Brown. Mrs Mary Brown no longer agrees with Mrs Rufus Brown merely on
their title. Existing conservative refusal rules decide the unmatched names; the tool
does not invent the unnamed wife's forename or a new identity ruling.

The combined rebuild also exposed an evidence-paragraph ownership bug: the census writer treated everything after its opening marker as its own text. A later Fergus paragraph could therefore disappear on refresh. The writer now bounds its paragraph by its own full closing statement, preserves following evidence on refresh and withdrawal, and tests both cases.

## Why #971's generated tree is not copied

The branch's substantive commits spend the synthesis and regenerate its downstream
layers; its later commits repeatedly regenerate those same outputs onto newer dev.
The current branch already carries the landed T-0837 work and a zero-drift baseline.
The old-settler people, crosswalk and spend files are byte-identical. Remaining generated
resident and crosswalk differences are reproduced from current sources by current writers,
instead of replacing later research with an older generated snapshot.

The old promotion self-test accepted a source dated 1834 as an attestation of an 1835
occupation. Dev requires the source's stated date span to contain 1835, so that positive
case is refused here. The adapted tests retain the actual Bailey later-trade and Chapman
possessive-printer regressions, verify their dated pointers survive, and distinguish 1834,
1835, 1839, missing dates and a span containing 1835. They run in the normal project gate.

## Completion gate

The reconciliation must pass the full project gate and its applicable published mobile
and desktop smoke tests before #1040 is merged. Only after that merge are the seven
superseded PRs closed with links to their preserved work and this disposition record.
