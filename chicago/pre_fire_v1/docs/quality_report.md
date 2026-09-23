# Quality report

## Automated validation

`data/validation_report.json` records a passing run over:

- unique primary identifiers for buildings, names, events, assertions, sources, links, and maps;
- valid building and source foreign keys;
- at least one source link and exactly one canonical name per building;
- controlled confidence and review values;
- existence and SHA-256 hashing of every local map and building image.

Final validated row counts are 324 building/structure records, 92 sources, 385 building-source links, 596 names, 758 lifecycle/fire events, 1,563 field-level assertions, 20 aggregate estimates, 14 dated map references with 14 local map images, 6 building-image assets, and 9 building-media subject links covering 5 buildings.

## Independent period work

Research was divided into pre-1830, 1830s, 1840s, 1850s, 1860s, and 1870–October 9, 1871 tranches. Each tranche was checked for CSV width, unique research identifiers, and source-key integrity before normalization.

An additional independent audit reviewed every pre-1830 row. Its corrections were applied before the final build, including:

- changing Du Sable compound outbuildings from an unsupported 1779 completion/1800 demolition to presence by 1800 with unknown fate;
- correcting the first federal factory to 1805;
- distinguishing the second factory's 1823 sale/reuse from physical demolition;
- recasting the supposed duplicate Kinzie house as Wolcott's government agency house;
- correcting the Laframboise people-versus-cabins count;
- separating the Beaubien cabin and warehouse; and
- disentangling the Wolf Tavern from Billy Caldwell and the Sauganash Hotel.

## Viewer test

The static viewer was tested through a local HTTP server in a browser. The 1830, 1853, and 1871 states loaded; the year control changed active-record totals; all-year text and alias filtering returned matching structures; the Sauganash, Wolf Tavern, Miller House, Green Tree Tavern, and Kinzie/du Sable image galleries resolved from local assets with source links and accuracy labels; the 1871 selector exposed four distinct map/view variants, including the burnt-district reference; and no console warnings or errors were present.

## Interpretation risks retained by design

`needs_review=true` is not a failure. It preserves ambiguous addresses, occupancy-versus-construction evidence, rebuilt or relocated identities, OCR-sensitive names, and fire fates that cannot yet meet the direct or spatial evidence threshold. “Probable” losses are counted separately from documented/asserted losses in `statistics.json`.
