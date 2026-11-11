# Prairie Avenue people: portraits, cards and figures

T-3546, T-3547 and T-3548 (split into T-3549 adults and T-3550 younger residents) implement the owner's request of 11 November 2026:
extend John and Frances Glessner's researched cards and portrait-guided figures
to the people listed throughout Prairie Avenue.

The starting roster has 440 entries in 71 household files. Entries are not all
distinct people: explicit `own_card` links point from former addresses to current
cards, and some Blue Book entries name groups rather than individual children.
The initial scene index marks 379 entries present, 32 absent and 29 uncertain.
These classifications are inherited evidence, not new findings of this work.
The existing eight Glessner household figures and their portrait records are the
reference implementation.

## Evidence rules

- Resolve a portrait's identity from its caption/catalogue and household evidence.
  A matching surname or a plausible face is insufficient.
- Keep birth, occupation, household, presence and appearance claims separately
  sourced and graded. A later portrait may guide facial form, with its date shown
  and age adjusted to the scene; it does not backdate later events or clothing.
- Record the actual sources searched for every person. A missing portrait means
  none identified in those sources, not a claim that no photograph exists.
- Label period stand-ins on the picture and card. Their likenesses and unsupported
  colouring, stature or clothing choices remain reconstructions.
- Preserve source identities and historical absences. An alias gets its canonical
  person's evidence; a collective entry does not become one invented individual.
- Use cleared source images, recorded crop/landmark coordinates and reproducible
  model stills. Keep bulky scans and comparison evidence outside the code repo.

## Current coverage

The roster now contains 445 entries across 71 households. Five daughters already
named in the household census transcriptions have individual cards; their inferred
continued residence stays explicit. Nine aliases retain their canonical links and
three collective listings remain groups rather than invented people.

Seventeen additional portraits were identified and visually inspected: fourteen men
from captioned or signed period books, and Harriet Sanger Pullman in Harris &
Ewing’s 1908 photograph (LOC 90710921), plus Grace Murray Meeker and Albertine
Huck Field in the Chicago Sunday Tribune of 3 March 1907. These later pictures
are explicitly distinguished from the 1904 scene. `portraits.json` records image identity, scan hashes, crops and hair
observations. The fitting records retain landmark uncertainty and single-view
limitations. Unpictured people are labelled reconstructions, never historical
likenesses. No owner acceptance of the new likenesses is asserted here.

`demographics.json` records 113 structured age/birth rulings, chiefly re-read from
existing census transcriptions. Independent biographical corrections preserve
conflicting census readings in the cards. `search-coverage.json` covers every
entry and records the bounded book/museum searches and failed Commons requests;
it is not an exhaustive claim that missing portraits do not exist.
`rejected-candidates.json` preserves mistaken or ambiguous image leads.

The current scene adds 362 adult residents through the existing portable role
assets, with individual appearances, household doors, complete seasonal days,
paired conversations and door calls. The eight existing Glessner actors retain
their own authored interactions. Absent people, aliases and collective entries do
not create duplicate actors. A nearby rotation is bounded to three additional
autonomous figures; explicit calls can summon other available people.

The 40 younger residents are still carded and currently await first-role review
and age-appropriate scene activation. Five new clothing recipes use pinned CC0
child/teenage bodies and identified 1904 clothing references. Infants must remain in household care rather
than being represented as independently walking adults. The remote workflow builds
canonical masters and portable exports without automatically enabling them.

## Review and verification

The working evidence is in `kevinrhaas/chicago-evidence`,
`evidence/prairie-people-2026-11-11/`: original source scans, seventeen source/model
pairs, comparison sheets and published-scene checks. Image rights and exact crops
are recorded there and in `assets/LICENSES.md`.

The published phone test has exercised a Kimball household door call, persistent
Interact controls, a real two-person conversation with Robert Bain, return indoors,
a later activity request and distinct Go inside / Go home behavior. Both figures
and their controls are retired after returning. The tested frame remained within
the scene’s draw budget with no page errors or loader problems.

The desktop native-resolution check also passed with Kimball’s visible figure and
both card images loaded. Default 1.5× desktop supersampling exceeded the software
renderer startup deadline; no pass at that setting is claimed. A phone check caught
and corrected Harriet Pullman’s body selection after her full name replaced the
married title. The corrected phone test passed with her intended woman’s asset,
age 62, both loaded card images and a paired conversation with Miss Robinson
that returned both residents indoors. No page errors or budget breach occurred.

All four local check sections passed, together with the focused person/card,
portrait-body consistency, seasonal schedule and animation audits. The first
canonical child build exposed a missing skin material in the clothing palette;
the corrected recipes preserve the neutral textured-skin material, and a
regression test rejects its omission. The corrected canonical export succeeded in
run 42997832738; the final paragraph records its mechanical and town inspection evidence.
The build uses the established child-body normal readback ceiling of 0.005 from
`people-1812-dress/children.md`, section 4 (the same boy body measured 0.0036919).
The default adult bound and exported geometry and animation checks are unchanged.
The full remote renderer smoke passed on 8c4f4355, followed by the required
checks and mapped refinements on a229ee241. Final integrated revision checks
are recorded on PR #1932 and are required before merge.
`source-budget.json` measures the complete Sources first-open payload at 71,687
gzip bytes, within the unchanged 120,000-byte limit. Twelve additional records
require the established 8 KB increment in the raw index allowance; no citation
or field is cut. Other houses currently use the existing doorstep transition;
Glessner’s animated door and stair passages remain separately tested and intact.

## Reproduction

1. Compile the 1904 scene with `python3 tools/compile_scene.py --scene 1904`.
2. Run `python3 tools/prairie_people.py` and `python3 tools/human_variation_kit.py`.
3. Fit changed landmark records with `tools/fit_portrait_face.py`; render their
   card pictures with `node tools/portrait_still.mjs <person-id>`.
4. `tools/prairie_children_source.py` derives the five source recipes. The opt-in
   `build_prairie_children` dispatch on `chicago-4d-humans.yml` performs canonical
   remote authoring and export, retaining the source commit and diagnostics.
5. The focused Prairie roster test, generator checks and normal human/door/card
   gates run through `tools/check.sh`. Publication compacts JSON structurally and
   leaves authoring-only variation inputs in the repository; `check_published.mjs`
   compares all shipped values with their source.

The later newspaper pass adds captioned 1907 portraits of Grace Murray Meeker and Albertine Huck Field, and eight birth rulings. Gwendolyn Field and Elizabeth Grey move from provisional adult casting to the child roster; their uncertain dates remain explicit. Frances Glessner Lee now uses her museum-documented 1878 birth instead of a default adult age. The Meeker secondary biography has an impossible marriage year, which is not used; its birth-date field is marked inferred.

## Younger-resident review

Five child/teen role prototypes exported successfully through canonical run 42997832738, source a229ee241fc1fd756f2be5b8a5190910e1ba52c5. Forty mechanical browser inspections passed, and desktop/phone town captures retain actual asset, runtime and camera hashes. First-role review under `data/people_match/README.md` and scene activation remain open on T-3550; mechanical success does not establish photographic acceptance. The evidence lives under `evidence/prairie-people-2026-11-11/child-prototypes/` in chicago-evidence. The adult rollout T-3549 does not close this remaining work.
