# The second fort's blockhouse cupola — before and after (T-2388, partial)

Two renders of the same 21-member compound, from **one identical camera**, with nothing changed
between them but the blockhouse's own bytes:

| | master | sha256 |
|---|---|---|
| `before/` | `fort_dearborn_blockhouse__log_1816.glb` | `4b49f0dba271d11ce407e6b407c6e4a766402bce04b93b24ebbcc2862f899e00` |
| `after/` | `fort_dearborn_blockhouse__log_1816.glb` | `96d9fb803cdd3b1639c32b9e0c562d0b3bf2af1b2fe8254abea4d62e8e136b15` |

The picture on the left of each pair is `data/sources/assets/prefire_views_kevin_2026_08/p3_1.png`
(sha256 `80c71433…`), panel 5 of the Kurz & Allison sheet of 1893, captioned "Fort Dearborn as
rebuilt 1835". **Before**: a brick stack standing at the apex of the blockhouse's cap, invented
and unattested, where the panel draws a cupola. **After**: the small square cupola under its own
four-sided cap, seated into all four roof planes, and no stack.

## What this camera is, and is not

`second-fort-panel-5-compound.json` copies every number of the T-3040 landmark fit
(`docs/RESEARCH/fort-reference-groups-T-3040/second-fort-panel-5.json`, preserved untouched) so
that the before and after differ by the geometry alone. That fit reached its imposed **100 m eye
bound**, both stockade endpoints are cropped, and the drawing compresses the compound, so the
whole fort renders aerial and undersized against a nearly level printed view. It is marked
`diagnostic_only`, which is the picture compiler's instruction not to offer its pose as a
historical "from this spot". **It is a control for one change, not a solved historical camera**,
and nothing in the model was moved to fit it.

## What is settled here and what is not

`second-fort-panel-5-compound.match.json` carries the verdict, which is **`differs`**. Exactly
one difference is marked `fixed` — the roof assembly this parcel built. The camera's own fit, the
galleried range's identity, the facade openings, the other roof forms and chimney counts, and the
compound's composition all remain `open`, and the other dated pictures T-2388 lists have not been
read against the model at all. The original ticket stays OPEN.

The cupola's **occurrence** is what the pictures carry. Its size, height, cap pitch and plain
boarded sides are reconstructed: see `docs/LIBERTIES.md`
§ L-second-fort-blockhouse-cupola-2388.
