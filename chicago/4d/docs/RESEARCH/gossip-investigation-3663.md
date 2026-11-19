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
`ac112f316beec3d15794cce9a355b20a36ed81ea8226fb8b32f276a5c6232db8`.
A separate foreground timing measured 0.128 seconds (exit 0); no budget increase.
This is one tree's no-write measurement, not a full gate verdict.

A native DOM fixture is prepared at `/tmp/t3663-investigation-browser.mjs`, not yet
run. It targets the actual completion view at 390×780 and 1280×800: native summary,
checkbox and textarea traversal, Space activation, review/revise focus, save statuses,
quota refusal, same-session repaint, replay/dismissal, 200% text and exported HTML/PDF.
The existing renderer owns CPU; no browser, publisher or full source gate was started.
Complete source/preflight and required published smoke remain before merge, after the
current classroom delivery lands. No hardware or complete assistive-technology audit
is claimed.
