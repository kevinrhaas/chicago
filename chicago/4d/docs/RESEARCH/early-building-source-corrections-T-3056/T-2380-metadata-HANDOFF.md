# T-2380 metadata-only rights correction

Ready to review/apply: `T-2380-metadata.patch`, with exact `before/` and `after/` files and base hashes in `base.json`. Repositories remain unchanged by this agent. This patch is separate from both geometric jail proposals; do not combine it with the held silhouette change.

## Changes

- Correct both `chicago/reference/images/IMAGE_SOURCES.md` and its planning copy: withdraw the unsupported original nineteenth-century/pre-1930 public-domain assertion for the detailed jail drawing; distinguish the actual 1930 copy catalogue date from original publication and the 1947 newspaper reproduction. The directory rights summary now acknowledges the exception, preserving each copy's existing item count.
- Add `calisphere_ucr_first_jail_catalogue_1930.json`: the **textual institutional catalogue** as `type=website`, `asset_use=text_only`, `rights_status=check_required`. It contains the actual UCR item identifier, Francis Dare copy attribution, Keystone publication-information field, combined creation/issuance date, rights limits and exact institutional credit. Its persistent OAC institutional ARK is identified as such, not presented as a Wayback capture.
- Update only `log_jail.research_note`: visible card research text records the rights hold and independent public-domain Andreas contrast. Also corrects the stale “probably a courthouse” sentence to the already-established fall-1835 exclusion carried by this record's phase note. No phase/form/source/confidence/date/place value is changed.
- Append dated correction notes to `docs/LIBERTIES.md` and the historical owner-brief README. These preserve historical decisions while clarifying that the detailed artwork has no verified original publication and that the separate Andreas courthouse plate actually includes the jail ensemble. They authorize no geometry and add no new construction liberty.

Required institutional credit is preserved: **Keystone-Mast Collection, UCR/California Museum of Photography, University of California at Riverside.** No author or original publication was invented. School/Tremont project-use approval is not extended to the jail.

## Proof and blast radius

`verify.py` / `verify.log` pass against the current repository snapshot:

- Structure/source schemas valid.
- The structure differs only in `research_note`; parsed phases, source linkages, confidence, footprint, placement, scene dates and every form value are exactly equal.
- Exact `mesh_inputs.structure_inputs_doc` and SHA are unchanged. Full documents are saved in `recipe-before.json` / `recipe-after.json`; hash: `daf789e64dede9497de8d144326e728980e2e0e484f9797cfc03ec7e4c74b6f9`.
- Actual focused `compile_pictures.derive` output is equal before/after. Pure grade is also identical: current tree reports `inferred`, with no joined pictures. This does not assert that no historical picture exists; it records the current automatic join and does not add a camera or grade ruling. The new website source is text-only and is not mislabeled as an illustration simply to add a picture.
- `git apply --check` passes. No asset, generator, camera, sidecar or grade-ruling file is in the patch. Six files change: two inventories, one source record, one research note, and two audit ledgers.

No master/web mesh needs rebuilding from this increment. Parent should compile/publish metadata normally for the corrected research note to appear on the card, and run its required integration checks before commit. This agent did not compile, publish, run a full gate or perform any bake/browser work. Recipes are proved unchanged; committed GLB freshness was not independently re-certified.

## Evidence and limits

Independent actual catalogue/surrogate research: `../T-2380-rights/RIGHTS-FINDINGS.md`. Actual Andreas page-image reread: `../T-2380-andreas-pd/FINDINGS.md`. The public-domain plate identifies the jail ensemble but not the individual original/later cell or its precise July-1835 condition. Its shallow hipped/pyramidal cap conflicts with the taller gable in the held detailed drawing. This correction changes no geometry to resolve that disagreement.

No original artwork publication, affirmative reuse licence or firm 1930 publication was established. The hold remains `check_required`; the earlier numerical silhouette proposal stays unapplied and unbaked. No `matches` verdict or ticket closure is claimed, and no user question was sent.
