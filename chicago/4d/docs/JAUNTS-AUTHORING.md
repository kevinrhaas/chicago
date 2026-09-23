# Authoring a jaunt — the content contract

**This page is written by T-1253** alongside `data/jaunts/schema.json` and
`tools/compile_jaunts.py`; until that ticket lands, the contract is
[ARRIVAL-JAUNTS-ARCHITECTURE.md §C](ARRIVAL-JAUNTS-ARCHITECTURE.md#c-jaunt-json-contract)
and the shared authoring rule in [JAUNTS-INITIAL-LIBRARY.md](JAUNTS-INITIAL-LIBRARY.md).
Content tickets (5H, 5I) link here so that one page, not eleven ticket bodies, carries the
field reference once it exists.

What T-1253 must put here (≤ 200 lines):

1. The field reference from §C with one complete worked example (`new-in-chicago`).
2. The provenance rules: a DOC sentence has a source id **and** a locator; an INF sentence
   states its reasoning; invented connective text — errands, prices, small talk, keepsakes —
   is `reconstructed` and gets a `docs/LIBERTIES.md` line; no quotation in a named person's
   mouth; nothing after 1 July 1835 narrated as present; no figure, ceremony or Indigenous
   dialogue; exterior stand-offs only.
3. The norms the compiler checks: 4–8 stops, 25–60 words per stop, 0–3 choices, every
   branch reaches an ending, a viable choice or "move on" at every state.
4. How to run it: `python3 tools/compile_jaunts.py` (in `check.sh`) and
   `node tools/play_jaunt.mjs <id> --all-paths`; how to measure the primary path.
5. The rule that a content PR changes no engine, compiler or CSS file.
