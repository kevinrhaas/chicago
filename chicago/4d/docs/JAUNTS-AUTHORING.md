# Author a jaunt

A jaunt is one JSON file in `data/jaunts/`, named for its stable `id`. Start from
`new-in-chicago.json`. Add content without changing the engine. **No engine change
in a content PR:** a new mechanic needs its own implementation ticket first.

## Build and preview

```sh
python3 tools/compile_jaunts.py
python3 tools/compile_source_use.py
python3 tools/test_compile_jaunts.py
./tools/check.sh
```

Open the published welcome, choose **Jaunts**, then **Preview the route**. This
release previews content; guided play, ETA and keepsake storage have separate
owners. Catalog and story requests happen only after their respective selections.
`data/sidecars/1835/jaunts/` is generated and committed; `publish.sh` copies it.
Compiled stories join public `citations` through the existing scene compiler;
authors keep source IDs in evidence. The compiler's `--check` refuses stale output without writing. A malformed file is
reported, excluded from the regenerated catalog, and makes the command exit nonzero;
other valid files still compile. Fix it before committing. `_fixtures/` is never
part of the live catalog. The deliberately broken `.json.invalid` fixture is copied
to a temporary `.json` path by tests so global JSON integrity stays intact. Use `--source DIR --output TEMP_DIR` to exercise copies.

## Field reference (schema version 1)

Unknown fields are refused. Strings are plain text: no HTML, callbacks, expressions,
`eval`, URLs as executable links, or per-jaunt JavaScript. IDs use letters, digits,
hyphens or underscores, beginning with a letter or digit.

| Field | Meaning |
| --- | --- |
| `schema_version`, `content_version` | Schema is `1`; positive integer content version changes when content changes. |
| `id`, `title`, `premise`, `category`, `scene` | Stable identity; title ≤100 characters, premise ≤260, category ≤60; scene is `"1835"`. |
| `featured` | Optional editorial flag; not an unlock gate. |
| `opening` | `{text, read_s}`; primary reading estimate, excluding optional cards. |
| `default_mode`, `allowed_modes` | `walk`, `wagon`, `horse`, `fly`, `instantly`; default must be allowed. Flight is a viewing convenience. |
| `variables` | Optional map: each `{min,max,initial,unit}` is a bounded integer; units `count`, `cents`, `preference`, `minutes`. Money is integer cents. |
| `inventory` | Optional `{items:[declared IDs],initial:[IDs],capacity}`. Items form a set, not stackable quantities; use a bounded variable for counts. |
| `stops` | Ordered array; first is entry. Normally 4–8 stops; fixtures/legitimate short outings may use fewer. Maximum 50. |
| stop `id`, `destination` | Unique stop ID; destination `{kind,id}` uses `structure`, `anchor`, `intersection`, `person`, `business`. |
| stop `text`, `read_s`, `action_s` | Text is 25–60 whitespace-separated words. Seconds are integers 0–600; action seconds optional (default 0). These are inputs, not measured journey times. |
| stop `evidence` | Nonempty list of this jaunt's evidence IDs covering facts and connective narrative in the stop. |
| stop `choices` | Optional array of 0–3 `{id,label,consequence,when?,effects?,next?}`. IDs unique within the stop. |
| stop `links` | Optional `{kind,id,label}` card links. Kinds: structure, person, business, source, topic. Topic IDs resolve against existing Evidence topics. |
| stop `next` | Unconditional continuation/skip. A choice without `next` inherits it; no implicit array-order jump. |
| `legs` | Optional by-index `{note?,story?}` between-stop notes; no mandatory dwell or effect. |
| `endings` | Unique `{id,text,read_s,completion_eligible,when?,default?}` records. At most one default, with no condition. |
| `keepsake` | `{family,id,title,text}` fictional memento, not a historical artifact. |
| `secondary_family` | At most one optional family besides the primary. |
| `evidence` | Claim records described below; IDs unique in the jaunt. |
| `review_required`, `review_reason` | Boolean; true requires a plain-language reason and compiles as unavailable. Referenced review-held places also make the jaunt unavailable. |
| `liberties` | IDs of existing entries in `docs/LIBERTIES.md`. |

Families: **Provisions**, **Livelihood**, **Wayfinding**, **News & Knowledge**,
**Neighbors**. No global score is required. Preserve IDs when revising prose.

## Branches and state

`next` names a stop, an ending, or `$end`. At `$end`, select the **first** matching
non-default ending in authored order, otherwise the default. A direct ending edge
must satisfy that ending's condition. All authored stops and endings must be reachable.

A stop's unconditional `next` is also its skip/default route. Omit it when a choice
is required. Every reachable state must have a viable forward continuation, and
every possible forward branch must terminate. Cycles are rejected even behind a
currently false condition. `next: "Previous"` is the sole exception: explicit
history navigation, no effects, never the only way out. It refers to the previous
visited stop, retains committed decisions, and must not reapply effects. Playback
implements history; the compiler validates the forward graph independently.

Conditions are data, recursively composed:

```json
{"all":[{"var":"money","op":">=","value":25},{"not":{"has":"receipt"}}]}
```

Use `all`, `any` (nonempty arrays), `not` (one condition), `{has:item}`, or
`{var,op,value}` with `<`, `<=`, `==`, `>=`, `>`, `!=`. Variables/items must be
declared, including in branches that do not run.

Effects are ordered `{op:"set"|"inc",var,value}` or
`{op:"add"|"remove",item,value:1}`. Adding an existing item and removing an absent
one are idempotent. The compiler explores actual reachable states, refusing any
out-of-bounds result or inventory overflow; it never silently clamps. More than
100,000 distinct states is refused with a request to simplify branches.

## Worked choice

With `money: {min:0,max:100,initial:100,unit:"cents"}` and
`inventory: {items:["receipt"],initial:[],capacity:1}`, a stop can offer:

```json
{
  "id": "buy",
  "label": "Spend an imagined 25 cents",
  "consequence": "Keep a fictional receipt.",
  "when": {"var":"money","op":">=","value":25},
  "effects": [
    {"op":"inc","var":"money","value":-25},
    {"op":"add","item":"receipt","value":1}
  ],
  "next": "next-stop"
}
```

The complete three-stop example is `_fixtures/fixture-branch.json`. The two-stop
`fixture-walk.json` shows an outing with no mechanics. Copying either into an
isolated source directory and running the compiler adds a catalog entry with no JS.

## Evidence and dates

Each claim is `{id,text,confidence,sources,locator?,reasoning?,liberty?}`.
`attested` requires at least one registered source ID and a nonempty locator;
`inferred` requires sources and explicit reasoning; `reconstructed` requires a
liberty named in the jaunt's `liberties` list. Facts display [DOC], supported
inference [INF], invented connective text [CONJ]. Never borrow a fact's grade for
its route, placement, conversation, price or keepsake. No invented quotations or
encounters with named people. Stops explicitly reference the relevant claims.

A source must resolve in `data/sources/`; **issue IDs are not necessarily source
IDs**. For a newspaper collection, name the registered publication and put issue
date, page and column in the locator. A valid ID is not proof: read the evidence.
`compile_source_use.py` registers each sourced claim as a typed `jaunt` edge with
its locator and grade. Source-free inventions create no false backlink. Unavailable
jaunts' edges are research use. No images/PDFs are derived from sources here;
`check_required` rights still permit text citation, not asset reuse.

The scene date is **1835-07-01**, despite the warm “summer 1835” greeting. Existing
structure IDs, scene anchors/intersections, people and businesses resolve at build
time. Excluded/date-ineligible destinations are refused. People need a known home
or workplace; businesses need scene-date premises. Use a supported anchor with
an explicit limitation for an uncertain location; never invent a front door.
Review-held content stays unavailable with its reason; no human figures, invented
Indigenous dialogue or ceremony. Follow the project's consultation rules.

For the pilot: Hogan's is the **former** mail corner (move about July 1834). The
Democrat's corner is also a **former** office by May 1835. Brown's exact position
is reconstructed. Historical building labels do not assert continuing tenancies.

Before a content PR, recompile jaunts, liberties (if changed), and source use;
include generated files, the relevant gates and a mobile preview. Adding content
must not require another engine or a duplicate place/source database.
