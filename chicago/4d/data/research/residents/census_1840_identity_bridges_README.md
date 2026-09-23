# 1840 census ↔ 1835 resident identity bridges

This sidecar records **person-identity continuity**, not a back-projection of 1840 household composition into the 1835-07-01 scene.

The source research workbook (`Chicago_1835_Best_Resident_Set_Research_v4.xlsx`) contains 210 named 1840 household-head rows under review on printed census pages 229–235 and 117 row→IPUMS SERIAL assignments in its best-resident set. Most of those rows are later-only or candidate evidence for 1835. Only independently bridged identities belong in `census_1840_identity_bridges.csv`.

Current promotion rule:

- require direct or otherwise independently strong circa-1835 identity evidence;
- require a resolved 1840 census row and IPUMS SERIAL at the recorded mapping confidence;
- attach the 1840 record as `later_census` evidence to an existing canonical resident;
- never create 1835 spouses/children/boarders or age claims solely from the 1840 household;
- retain 1840 household totals and age/sex/industry variables as evidence for later household-reconciliation research.

Issue: #669.
