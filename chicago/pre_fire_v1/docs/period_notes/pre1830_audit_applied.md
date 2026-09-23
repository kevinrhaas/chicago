# Applied validation audit: pre-1830 records

> Integration note: the corrections and documented missing candidates in this audit were applied to the normalized `data/buildings.csv` before publication. The row-by-row text below preserves the independent audit trail; statements such as “change” or “remove” describe the pre-audit research draft, not the published database.

## Scope and method

This is a non-destructive audit of the 33 current rows. The CSV was **not edited**. All ten semicolon-delimited source keys resolve in `decade_pre1830_sources.csv`. Claims were checked against the National Park Service Du Sable NHL nomination, Andreas volume I scan/OCR, and the cited *Encyclopedia of Chicago* and City sources. A recurring issue is that current rows turn a documentary latest-known date into an exact construction date, or a sale/reuse date into demolition.

The result is not proof that every pre-1830 building has been found. Contemporary evidence is sparse, household/building identity changes over time, and Andreas often preserves late recollections rather than parcel surveys. Corrections below distinguish a supported entity from unsupported dates or identities.

## Row-specific findings

| Record | Finding and correction needed |
|---|---|
| PRE1830-001 | Retain as an occupation/shelter episode, not a reconstructable surveyed building. The 1674-75 winter is supported, but form, footprint, and exact South Branch/portage location remain unknown. |
| PRE1830-002 | Change completion semantics from exact/traditional 1779 to **present before or by 1779**; the NHL significant year is not a proven construction year. Remove unsupported 1852 demolition. NPS documents a 22-by-40-foot log house and later compound; Andreas shows Kinzie occupancy through 1827 and a house going to ruin, not a verified 1852 loss. |
| PRE1830-003 | Barn 1 is supported as an inventory component **by May 7, 1800**, not as a 1779 completion. Remove 1800 demolition: that is the deed inventory/sale date, and later fate is unknown. |
| PRE1830-004 | Same correction as 003 for barn 2: completion only by 1800; no evidence of demolition in 1800. |
| PRE1830-005 | Horse mill function is supported, but construction is only by 1800 and loss date is unknown. Do not assign the compound centroid as an exact footprint. |
| PRE1830-006 | Bakehouse is supported, but 1779 completion and 1800 demolition are unsupported; use by-1800 and unknown fate. |
| PRE1830-007 | Workshop is supported, but 1779 completion and 1800 demolition are unsupported; use by-1800 and unknown fate. |
| PRE1830-008 | Dairy is supported, but 1779 completion and 1800 demolition are unsupported; use by-1800 and unknown fate. |
| PRE1830-009 | Poultry house is supported, but 1779 completion and 1800 demolition are unsupported; use by-1800 and unknown fate. |
| PRE1830-010 | Smokehouse is supported, but 1779 completion and 1800 demolition are unsupported; use by-1800 and unknown fate. |
| PRE1830-011 | Retain only as a transparent **unidentified count-balancing component**: NPS says ten buildings but lists nine functions including the main house. Remove `possibly_stable` unless a primary inventory names a stable. Use by-1800 and unknown fate, not 1779/1800. |
| PRE1830-012 | Ouilmette's cabin is supported by 1803 and survived the 1812 attack. Remove unsupported 1790 start and 1830 demolition; use completed by 1803 and unknown loss date. |
| PRE1830-013 | Pettell's hut is supported in the four-hut 1803 recollection. Remove unsupported 1790 start and 1812 demolition; Andreas explicitly cautions against assuming all civilian houses burned in 1812. |
| PRE1830-014 | Use **William Burnett** as the probable owner. His letter says he already had a Chicago house in 1798, but Andreas only *possibly* identifies it as the fourth 1803 hut. Completion by 1798 is supportable; 1812 demolition is not. |
| PRE1830-015 | Fort Dearborn I as a complex is sound. Preserve the 1803-04 range and 1812 destruction; avoid claiming a complete component inventory from the surviving summaries. |
| PRE1830-016 | Correct Factory I completion to **1805**. Andreas explicitly dates establishment of the federal factory to 1805; 1803-04 is too early. The 1812 closure/destruction episode is supported. |
| PRE1830-017 | The Lee house near the fort existed by 1804 and was later sold to Jean Baptiste Beaubien. Builder is unknown; `Lee_family` belongs in ownership/occupancy, not architect. Remove unsupported 1850 demolition; Andreas says it later served as a barn but gives no loss date. |
| PRE1830-018 | The separate Lee-farm/Hardscrabble house is one of the five civilian houses in 1812 and later became Crafts' trading house. Remove unsupported 1809 start and 1830 demolition; use completed by 1812 and unknown loss date. |
| PRE1830-019 | Burns house is supported by 1812 and as Jouett's 1817 residence. Remove unsupported 1809 start and 1830 demolition; builder and final fate remain unknown. |
| PRE1830-020 | Rebuilt in 1816 is sound. Retain review flag because current official/secondary sources conflict: City landmark material gives 1856, while the *Encyclopedia of Chicago* gives 1857 for final demolition. |
| PRE1830-021 | Do not use 1823 as demolition. The second federal factory closed in 1822, was sold in 1823, passed through Whiting/American Fur Company/Beaubien ownership, and continued as a residence until 1839 in Andreas. Treat 1823 as sale/repurposing and leave physical loss blank. |
| PRE1830-022 | Dean house is specifically dated 1815 and bought by Beaubien in 1817; retain the entity. Remove unsupported 1830 demolition. Where normalized, identify the contractor as John Dean only after confirming the full name in the printed passage/index. |
| PRE1830-023 | The small trading house built by Beaubien in fall 1818 is supported and distinct from the reused federal factory. Remove unsupported 1830 demolition; keep Jean Baptiste Beaubien/American Fur Company in developer/occupancy fields. |
| PRE1830-024 | Recast as the **Wolcott government agency house**, not a second Kinzie/Du Sable house. Andreas's footnote says Wolcott owned the agency house and Kinzie probably lived there because his own house was going to ruin. Construction was before 1812; 1804-1826 and 1830 demolition are unsupported. Keep distinct from PRE1830-002. |
| PRE1830-025 | Split into two physical records: Beaubien cabin and shanty warehouse. The 1826 recollection proves both existed then, not that they were built in 1817. Reconcile the cabin against Factory II, Dean house, and Lee house before declaring it independent; remove 1830 demolition. |
| PRE1830-026 | Shop is supported by the 1826 recollection, but 1820 start and 1830 demolition are unsupported. Normalize Joseph Porthier spelling with source variants. Andreas separately indicates a Porthier residence north of the river, a missing candidate. |
| PRE1830-027 | Store cabin at the forks is supported by 1826 and may be the cabin Mark Beaubien later bought. Remove unsupported 1820 start and 1830 demolition; perform entity reconciliation before adding a separate Mark Beaubien cabin. |
| PRE1830-028 | Critical count error: Andreas says Hardscrabble had **five or six cabins**, several occupied by Laframboises, “of whom there were four.” Four refers to people, not four cabins. Rename as a Laframboise-occupied cabin group and leave its internal structure count unknown. |
| PRE1830-029 | Wallace cabin/establishment is supported in the Hardscrabble recollection. Remove unsupported 1820 start and 1830 demolition; use active by 1826 and unknown fate. |
| PRE1830-030 | Normalize the person as **Bernadus H. Laughton**, with Lawton as a source variant. Cabin existed by 1826; 1820 start and 1830 demolition are unsupported. |
| PRE1830-031 | Robinson cabin occupied by the Galloways in winter 1826-27 is supported. Remove unsupported 1820 start and 1830 demolition; ownership/occupancy should remain separate. |
| PRE1830-032 | Andreas says Miller House was built “as early as 1827,” not proven exactly in 1827. Use by-1827/approximate precision and remove unsupported 1830 demolition. Keep Wolf Point/forks geography distinct from later street-address certainty. |
| PRE1830-033 | Critical identity error. This was built in 1829 by **Archibald Caldwell and James Kinzie**, sold to James Kinzie, and opened by Elijah Wentworth as the Wolf Tavern in 1830. It was not Billy Caldwell's tavern and is not the Sauganash Hotel. Remove Billy Caldwell/Mark Beaubien conflation and unsupported 1831 replacement. |

## Missing or unresolved candidates

- Government/Indian agency house existing before 1812, if PRE1830-024 is correctly recast.
- The house occupied by Mr. Bridges in 1816 between the agency house and Kinzie house.
- Joseph Porthier residence north of the river, built before 1826.
- Two Clybourne cabins on the North Branch, explicitly stated by Andreas.
- At least one unidentified Hardscrabble cabin in the five-or-six-cabin 1826 recollection.
- Government frame house for Billy Caldwell in 1828 near State and Chicago; Andreas calls it possibly the first frame building.
- Any Mark Beaubien cabin should be added only after resolving whether it is PRE1830-027 or another reused structure.

## Aggregate-denominator cautions

- **1800: 10 buildings** is one Du Sable parcel/compound, not the settlement.
- **1803: 4 huts** and **1812: 5 civilian houses** exclude the fort; the 1812 account separately mentions the fort and attached agency building.
- **1825: about 14 houses** is a visitor's settlement estimate. The same-number taxpayer roll has a different geography and cannot validate a one-house-per-taxpayer assumption.
- **1826: 12-13 enumerated civilian structures** is a derived reconstruction spanning the river mouth, Hardscrabble, and North Branch and includes warehouse/shop/store uses; it is not a direct “houses” census.
- Annual construction counts (1833, 1834, 1844, 1845) are flows. They cannot be added to named-record CSV counts without modeling demolition, replacement, relocation, boundary changes, and possible retrospective undercount.
- Great Fire totals are alternative estimates of the same event. The 13,500, 15,765, and approximately 18,000 figures are not additive.
