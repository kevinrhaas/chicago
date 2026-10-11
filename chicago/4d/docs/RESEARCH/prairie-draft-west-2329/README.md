# The Prairie district draft: the 18th-20th block's west side, and the draft builder (T-2329)

Piece 1 of T-2159 (the owner's district pass of 2026-10-08), split by its own bound: *the draft
builder with the west side, then the east side* (T-2330).

## What stands now

Eighteen `prairie_draft` records on the west side of Prairie Avenue between 18th and 20th Street:

| lot | record | storeys (sheet) | construction | roof | refined by |
|---|---|---|---|---|---|
| 1812 | `wheeler_house_1812_prairie` | 3B | brick | shaped (stepped) street gable | T-1884, T-1885 |
| 1816 | `henderson_house_1816_prairie` (+ coach house) | 3S.B.; rear2B | brick | mansard, dormers, front bay, porch | T-1886 |
| 1824 | `marsh_house_1824_prairie` (+ coach house) | 2½B; rear2B | brick, stone front | hip with attic dormers | T-1887 |
| 1828 | `house_1828_prairie` (+ coach house) | 3B; rear2B | brick, stone front | flat behind a cornice | T-1887 |
| 1834 | `jones_house_1834_prairie` (+ coach house) | 3S.B. | brick, stone front | mansard, bay | T-1888 |
| 1834-1900 strip | `shed_1834_1900_prairie` | 1 | frame | gable | T-1935 |
| 1900 | `elbridge_keith_house_1900_prairie` (+ coach house) | 3B; rear1B | brick, stone front | mansard, corner bay, porch | T-1897 |
| 1906 + 1908 | `edson_keith_house_1906_prairie` (+ coach house) | 3B | brick, stone front | flat, bracketed cornice | T-1898 |
| 1912 | `moulton_lowden_house_1912_prairie` (+ coach house) | 2½B; rear3B | stone (brownstone), brick rear | steep hip, dormers, conical corner turret | T-1899, T-1900 |
| 1916 (1930) | `house_1918_prairie` (+ coach house) | 2½S.B.; bay4B; rear2B | brick | hip, dormers, turret for the 'bay4B' | T-1901, T-1902 |

Every coach house is refined by T-1935. Not touched: **Glessner** (1800, the benchmark), **1808**
(already the K01 assembly, T-1882/T-1883 refine it), **1812's coach house** (T-2321 is building it
from the K12 kit, PR #666), and **1936** (the census rules it an alias of 1918 with no footprint).

## The builder (acceptance 1)

`tools/draft_prairie_1904.py` is data-driven and deterministic. It reads the traced footprints
(`data/traces/prairie_1904_footprints_s28.json`, T-2327), the sheet census, the T-1837 frontage
register (its rows copied to `data/components/prairie_1904/draft_prairie_1904_register.json` so
the gate needs no tickets checkout) and the rules in
`data/components/prairie_1904/draft_prairie_1904.json`. **T-2330 drafts the east side by adding
`"east"` to block 28's `sides`; T-2160 and T-2161 add their sheet under `blocks` and their rows
under `frontages`.** No code change.

- **Plan.** Each traced part is scan-filled on a 0.25 m grid in its lot's own frame and replaced
  by the largest rectangles that fit inside the fill (at most three a part, to 90 % cover). The
  rectangles are never larger than the Sanborn polygon and never the parcel. The main part's
  largest rectangle is the main body; a shallow rectangle at the front is a bay; the sheet's
  ranges, porches and stone fronts keep their roles.
- **Elevation.** Full storeys from the printed notation (`3B`, `2½S.B.; rear2B`); everything
  else from the family row (Second Empire → mansard, Chateauesque → steep hip, Italianate →
  bracketed flat, gable → shaped gable, stone front → flat behind a cornice, default hip) overlaid
  with the frontage's own row.
- **Gate.** `--check` re-derives every record byte for byte and refuses a hand edit, a missing
  record and a record the rules no longer build; `--self-test` (6 cases) proves the fit stays
  inside an L-shaped part, reads the notation, and that the refusals fire. Both in `check.sh`.

`generators/archetypes/prairie_draft.py` builds the GLB in pure Python (`generators/draft_emit.py`,
wired into `bake.sh` and `check.sh --check`): closed blocks per rectangle over a stone basement
course; the family roof; sash with sill, lintel and meeting rail on every storey of every exposed
wall (a wall within 0.9 m of a lot line is a party wall and is left blind); door, transom, stoop
and area lights on the front; string courses, cornices, dormers, chimneys, porches and turrets.
Coach houses take a gable roof, a carriage door and loft door on the alley. Flat colours, each
nudged inside ±6 % by the record's seed, so no two neighbours share a brick.

## Provenance

Every record carries `draft_plan` (inferred: the rectangles and which trace part each came from),
`draft_elevation` (reconstructed: the rules' row and the frontage's reason), `stories` (attested:
the notation), `construction` (the register's reading of the map colour) and `draft` (record
only: pass, liberty, register row, census ids, trace building, seed, `replaceable_by`). The name
on each card ends "(district draft; refined by T-…)". One liberty for the block:
**L-draft-prairie-18-20-west-2329**. L264's brick-population count is restated (5 → 16) because
the drafts say brick; they take no course from its substrate.

## Captured and measured (acceptance 3)

`tools/qa_draft_t2329.mjs`, the published `/1904/` app, normal boot, desktop 1280×800 at full and
phone 390×780 at light, before (dev at 829dce332) and after. Stands: the landing pose looking
down the row, the west walk, the east walk, the alley and the air. Zero page errors and zero
failed requests in all four runs.

| | load to ready | JS heap after GC | draw calls (5 stands) | draft GLBs |
|---|---|---|---|---|
| desktop before | 26.2 s | 17.8 MB | 72-86 | — |
| desktop after | 24.3 s | 19.3 MB | 59-88 | 18, 594 KB (web) |
| phone before | 12.7 s | 17.7 MB | 48-78 | — |
| phone after | 12.4 s | 19.2 MB | 51-80 | 18 |

Frame times are in the JSON files; they are software-GL readings on this runner (seconds, not
milliseconds) and only comparable within one run. The drafts add 38,600 triangles at full detail
(910-4,550 a house) and about 1.5 MB of heap; the phone tab is not near a memory limit. The draft
has no detail tiers of its own yet: its geometry is light enough that the scene's `light` tier
carries it whole.

## Limits, said plainly

- A rectangle fit loses the drawn curve of a rounded bay and any wall the trace bent; 1816's
  rounded front bays are a square-cornered projection.
- The turret corners of 1912 and 1916 are reconstructed; the sheet does not place them here.
- No K02-K16 kit part is used: the kits are the per-building tickets' to lay. The draft only has
  to read as the right family and fabric from the walk.
