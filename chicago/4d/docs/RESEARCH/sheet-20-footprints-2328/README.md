# Sheet 20's 1904 building footprints (T-2328)

**What:** every building on the Prairie Avenue lots of Sanborn 1911 vol. 3 sheet 20
(16th to 18th Street, both faces) as an outline in local metres, each keyed to its
[T-1840 census](../../../../prairie_1904_v1/data/sheet_census/sheet-20.json) polygon:
**36 grounds (38 lots), 49 buildings, 94 parts**, in
[`data/traces/prairie_1904_footprints_s20.json`](../../../data/traces/prairie_1904_footprints_s20.json).

**Why:** T-2160 drafts this block, and requires each house's footprint "from the
reconciled Sanborn polygon, never the viewer's parcel rectangle". The census names every
building but says "Rear buildings are counted and described, not digitized". T-2327 did
sheet 28 for T-2159. This is the same reading for sheet 20.

**How:** the T-2327 tracer (`tools/trace_prairie_1904_footprints.py`), given sheet 20 as
one more `SHEETS` entry: the sheet's fit (`data/traces/gcp/sanborn_1911_v3_sheet_20_gcps.json`),
its census and the two T-0474 blocks `blk_indiana_prairie_16_18` and `blk_prairie_ic_16_18`.
No colour rule, threshold or tolerance was changed for it. Sheet 20 reads at 0.0508 m/px
against sheet 28's 0.0506.

## Three things sheet 20 has that sheet 28 did not, and the rule each got

All three are general rules in the tool, each with a self-test, and none is a per-lot exception.
Sheet 28's outlines are byte-for-byte unchanged by them. Only its metadata gained
`fit_rms_m` and the reworded rule strings.

1. **A frontage over several lots.** 1620 (frontage-20-006) covers three traced strips
   (`prairie_1616_1620`, `prairie_1620`, `prairie_1620_1626`). The one building on them is a
   long alley range crossing the strip lines. Read lot by lot, it came out in pieces, and the
   rear split emptied the street group (the run crashed). **Rule:** a census frontage with
   polygons that spans several lots is read on their union (`ground_parcel_ids`). The rear
   split is never applied where the census names no front building, and never so far that
   nothing is left at the street.
2. **A non-dwelling at the street.** 1605 is the Illinois Central's 16th Street station,
   which the census kind is `non_building_use`. **Rule:** that kind stands at the street like a
   front, and the outline's `kind` says `non_building_use`.
3. **Two service buildings drawn joined.** At 1720 the census names the stable and a
   1-storey range "joining the stable to the garage behind 1726". At 1701 it names a building
   by the tracks and the stable "joined to its south end". Each traces as one outline of
   several parts. **Rule:** detached ids left over go onto the joined (several-part) outline
   nearest the alley, with a `note` saying so. The parts are where they divide. 1720's range
   is clipped at the 1720/1726 lot line, as every outline is clipped to its lot.

## Which outlines are the 1904 building: `for_1904`

The census rules each frontage for 1904, and the outline file now carries that ruling on
each building, because the draft must not stand on a later building:

| value | count | meaning |
|---|---|---|
| `as_mapped` | 47 | present in 1904 as the 1911 sheet draws it |
| `not_1904` | 1 | **1607–1611**: the 1911 four-storey auto-repair loft. The census backcasts the frontage from Robinson 1886, which shows one frame building printed 1609 and 1611. That pair is not on this sheet. |
| `as_mapped_rear_of_backcast` | 1 | the 1620 alley range, behind the open 1911 frontage where Robinson 1886 prints the Law house. The house itself is not on this sheet. |

## Limits

- **Tiers:** outlines and part roles are INFERRED, as on sheet 28. Storeys are not read: the
  census notation is the storey reading.
- **Accuracy:** sheet 20's GCP file carries no independent check, so the file states the
  fit's own residual, **2.46 m RMS** on its four control crossings, and claims nothing
  better. Sheet 28's independent check (1.47 m) is not borrowed. Relative accuracy inside
  a lot is the trace's, about 0.1 m.
- **No modelled house to compare against.** Sheet 28 was checked against Glessner's HABS
  plan and the 1808 record. No house on 16th–18th is modelled yet, so the check here is the
  overlays and the contract (every outline inside its lot, counter-clockwise, every census
  id assigned exactly once).
- **1700 and 1706** (the Glessner family townhouses) trace as one building carrying both
  front ids. The party line between them "does not run to the alley" (census), and the
  draft divides them.
- **1729 Pullman:** the stone house, its 1-storey link and the garage are one building (as
  drawn). Its parts did not separate at the link's walls, so the main part (1,004 m²)
  includes the link and garage. T-1880 refines it.

## Overlays

`overlay-west.jpg` and `overlay-east.jpg`: building outlines in red, parts by role (main
blue, range green, porch orange, stone front purple). Regenerate with
`python3 tools/trace_prairie_1904_footprints.py --sheet 20 --overlay docs/RESEARCH/sheet-20-footprints-2328`.
