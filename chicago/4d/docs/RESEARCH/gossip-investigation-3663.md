# Gossip comparison validation checkpoint — T-3663

The first optional case reuses the completed Gossip route and existing notebook.
Its exact source units are `land-sale`, `bank-branch`, `bank-springfield`; source IDs
are `chicago_democrat_1833_1835` and `chicago_american_1835`. All five compiled
versions carry the same historical text. The two American claims share one item,
including its locator; the Springfield record's reasoning remains alongside it.

The pure regression drives actual `createFieldNotebook` storage and `notebookHTML`:
all five bands and eligibility refusals, unresolved citations, missing sale figure,
Inferred Springfield reading, full context bounds, explicit saves, unchanged/revised
copies, deleted and independently edited notebook entries, quota/full/damaged/missing
storage, prior-entry preservation and escaped export. Existing reflection and notebook
regressions, string lint, changelog checks and syntax pass.

Official selected-tool measurement:
`node tools/measure_step_isolation.mjs --tool tools/test_jaunt_investigation.mjs`.
The declared command is `node tools/test_jaunt_investigation.mjs`; its registry row is
`{"wrote": [], "wrote_ignored": []}`. `node tools/audit_step_isolation.mjs --check`
passes with the new step registered. Test SHA256:
`68131cf4fc8e0215bdfb92c64164d971e82f5ac966d2c90ebd461c223002cedc`.
The current test includes a regression for the actual saved-case export heading.
Its official remeasurement still writes nothing; no gate budget increase is needed.
This is a selected-tool measurement, not a full gate verdict.

A native DOM fixture passed 53 checks at 390×780 and 1280×800 using the actual
completion view: native summary,
checkbox and textarea traversal, Space activation, review/revise focus, save statuses,
quota refusal, same-session repaint, replay/dismissal, 200% text and exported HTML/PDF.
Notebook excerpts now say **Source context**, covering cited newspaper readings as
well as person-card excerpts. The final native run checks the actual HTML export;
the live Notebook heading is part of the required published flow. Its 53-check receipt
supersedes the earlier 51-check fixture;
all attempts remain in the evidence archive with their original inputs.
It recorded no page, console or HTTP errors. The first fixture attempt incorrectly
forbade the rejected editorial supply inside the source locator's explicit warning;
that attempt is preserved, and the corrected check distinguishes the quotation from
the locator. No application change was needed. This is a no-world fixture, not a
substitute for the actual published Gossip route and committed completion.

PR #2197 has landed; this feature is integrated on DEV `38f51fcda`, preserving its
folded changelog and latest 1904 geometry. Complete source/preflight and required
published checks remain before merge. Fresh stages 13–15 cover the changed feed,
1904 inputs and Jaunts integration; dedicated completed-Gossip flows cover this case.
Earlier evidence requires an exact input/behavior review. No hardware or complete
assistive-technology audit is claimed. PR #2205 and the evidence repository carry
the final results without treating this checkpoint as a release verdict.
