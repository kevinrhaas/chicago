# Resident identity research — pass 03 (75 people)

## Scope and disposition

T-0463 is the third fixed, non-overlapping research cohort. It covers 75 real named
people selected from the 848-person eligible set: 25 established names, 25 names with
postal-list presence and 25 uncertain postal names. Reconstructed people are excluded.
The manifest is `data/research/residents/pass_03_75_cohort.json`; the findings are in
`data/research/residents/pass_03_findings.json`.

This pass adds 16 corroborated enrichments, 15 possible identities that remain explicitly
unmerged, and 44 no-corroboration outcomes. The cumulative public layer now covers 225 of
848 eligible people (26.5%): 47 corroborated findings, 45 candidates and 133 no-finds.
The compiler, selector and smoke assertions all derive from the fixed manifest rather than
from an opportunistic list of successful searches.

## What was found

The strongest additions connect named Chicago people to dated civic, legal, commercial,
church, institutional and local-history records. Examples include Daniel Elston's 1833
Chicago merchant and soap/candle, distillery and brewery activities; Stephen F. Gale's
1833 voter and 1839 printing imprint; Russel E. Heacock's subdivision plat and directory
entry; Benjamin Jones's Chicago merchant/speculator role before his 1836 Manitowoc move;
and the Cook County voter, town-clerk, hydraulic-company and newspaper records for several
other names. These are enrichments, not automatic household reconstructions: the original
resident row remains the identity anchor and each source is cited in the sidecar.

The candidate set records useful leads without importing a biography. Examples include
Ben Butterfield's Chicago/Lockport route, Alva Dunlap's 1834 Illinois travel, Andrew
Miles's 1834 Fox River claim, Charles H. Bartlett's 1834 farming diary, Alfred Churchill's
Flag Creek civic record, and Rouse Bly's Ohio record. Geography, chronology, spelling and
the absence of a direct Chicago bridge are recorded as conflicts where applicable.

## Method and limits

Each person received a normalized name-plus-place/date query, then targeted searches in
primary or edited repositories, contemporary newspapers and directories, institutional
finding aids, county/church histories, local archives and digitized legal material. The
source registry records the URL, access date, source tier, query, result and limitation.
Search hits were accepted only when a distinctive name, date, place, occupation or civic
role made the connection explainable. A generic name, a regional match, or a later
chronology is a candidate at most. No surname was used to infer heritage, lineage,
immigration, kinship, marriage or occupation. Duplicate possibilities remain visible and
are not silently merged.

The most common negative result was not evidence of nonexistence: a name-only search did
not yield a safe, period-correct bridge. Postal reachability is not bodily presence in
Chicago, and a later Chicago directory entry is not silently back-projected to 1833–35.
The next pass should prioritize original newspaper columns, land/probate/naturalization,
marriage and church records, and adjudication of the strongest regional candidates.

## Reproducibility and continuation

Run `python3 tools/compile_resident_research_pilot.py` from `chicago/4d` to regenerate the
225-review payload. Run `tools/check.sh` before publishing. If the stacked PR is held for
the browser smoke environment, leave T-0463's data and source registry intact and resume
from the branch/PR rather than selecting another cohort. The next ticket must select a new
non-overlapping 75-person manifest and carry forward the cumulative 225 baseline.
