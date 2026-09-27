# T-1253 — jaunt content and preview receipts

The authored pilot is `new-in-chicago`; its five destinations resolve in the July
1835 scene. The welcome offers a read-only route preview with per-stop evidence,
not playback or an earned keepsake. T-1279 owns the guided runtime.

`python3 tools/test_compile_jaunts.py` exercises 25 tests, including every refusal
named by the ticket, all five destination kinds, Evidence topics, review inheritance,
and the existing confidence auditor's reading of the new `reasoning` field.
The invalid JSON fixture is stored as `.json.invalid` and copied into a temporary
source directory during the refusal test; the repository still contains valid JSON.

Data-only expansion proof: compiling `fixture-walk.json` alone writes its full
content and a one-card catalog. Adding only `fixture-branch.json` adds that full
content file and a second catalog row; the first content is byte-identical. The
test asserts both diffs without touching JavaScript. Neither fixture is published.
A synthetic 27-entry copy of the real five-stop pilot compiles to **22,322 bytes**
against the 30,000-byte catalog limit. The live one-entry catalog is **869 bytes**.

The source compiler from T-1248 is present and used directly. Every sourced pilot
claim registers as `entity_type: jaunt`, with stable evidence ID, locator and grade.
The source-free invented outing has no fabricated source backlink. The seven
claims distinguish five historical claims, one continuity/placement inference,
and one declared narrative liberty (`L-jaunt-pilot`).

The Andreas locators were checked against the registered Internet Archive edition's
OCR: printed pp. 139–140 (Postal Affairs), p. 132 (Mrs Rufus Brown), and p. 303
(Porter's May 1833 lodging and Brown's house behind Peck's). These repeat existing
structure/dossier readings, not a new building attribution. The Democrat's May 20
colophon locator comes from the existing issue extraction's c007 notes: page 4,
column 6, transcription lines 4177–4180, rather than the apprentice advertisement
on page 3. That issue ID resolves to the registered publication source ID.

`tools/test_jaunt_preview.mjs` serves the published mirror at both production and
dev URL bases, exercises catalog/story failures separately, verifies zero jaunt
requests at boot and no story fetch before selection, checks unavailable reasons,
reads all five stops and evidence, and exercises 390×780, 1280×800, 320×568 and
780×390 layouts. Screenshots and `preview.json` hold its completed reading.

The broad scene smoke also exposed a compatibility regression inherited with the
shared picker: `goToTarget` rejected the harness's explicit coordinate intersection
viewpoints because they have no inventory ID. That adapter path is restored; named
picker destinations still require the shared resolver. No pixel threshold changed.

Validation commands and final outcomes are recorded in the PR and STATUS entry.

The full smoke's other inherited mismatch was its frontage refusal snapshot:
108 versus 112 authored refusals. Comparing T-1657 (`3424d20f`) with the base dev
(`face5164`) identifies exactly four additions: T-1640's Dearborn lot-6 shed wall;
T-1682's Market lot-6 wall and the two reconstructed C2 trade refusals. Franklin
lot-4's existing wall refusal was renamed. The exact expected count is updated to
112; all walk, crossing, post, fence and pixel assertions remain unchanged.
