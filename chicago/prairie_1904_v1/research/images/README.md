# Prairie Avenue 1904 — image & document collection

The iconography layer of the Prairie Avenue research library: **every image, drawing,
plan, map plate and building filing found for each structure and for the streetscape**,
with where it lives, what it shows, when it was made and what you may do with it.
The viewer's **Images** section reads the merged file `../../data/images.json`
(built by `tools/build_images.py` from the `stream-*.json` files here).

## Files

| path | what |
|---|---|
| `stream-*.json` | one research stream's records (a JSON array). Streams are merged, never hand-merged |
| `files/<id>.jpg`, `files/<id>-thumb.jpg` | local derivatives (≤1600 px and ≤480 px JPEG) — **only** for public-domain / no-known-restrictions items, made by `tools/fetch_image.py` |
| `buildings-index.tsv` | the 62 building ids a record may cite in `building_ids` |
| `WORKLOG.md` | what has been searched, what is left — read it before resuming |

## Record schema (one object per image or document)

```jsonc
{
  "id": "img-pullman-det-4a08066",        // unique, lowercase a-z0-9 and hyphens, stable
  "kind": "photograph",                   // photograph | stereograph | postcard | engraving | lithograph |
                                          // publication plate | architectural drawing | measured drawing |
                                          // fire insurance map | atlas plate | bird's-eye view | aerial |
                                          // document | permit record | newspaper item
  "title": "Pullman Residence, Chicago, The",   // the holder's title, verbatim where there is one
  "building_ids": ["pa-1729-5"],          // ids from buildings-index.tsv; [] when it shows none of them
  "addresses": ["1729 S. Prairie Avenue"],
  "streetscape": false,                   // true for street views, district views, maps, aerials
  "view": "oblique front",                // front elevation | oblique front | side elevation | rear | street view |
                                          // aerial | interior | detail | plan | section | site plan | map | text
  "facing": "southeast",                  // camera direction where it can be read; null otherwise
  "camera_position": "from the west side of Prairie Avenue near 18th Street",   // or null
  "date": "c. 1900",                      // the holder's date text
  "date_earliest": 1895, "date_latest": 1905,   // integer bounds; null when unknown
  "period": "in-period",                  // in-period (≤1911) | near-period (1912–1930) | later (1931+)
  "creator": "Detroit Publishing Co.",
  "repository": "Library of Congress Prints & Photographs Division",
  "collection": "Detroit Publishing Company Photograph Collection",
  "call_number": "LC-D4-…",              // or null
  "catalog_url": "https://www.loc.gov/pictures/item/2016794585/",
  "image_url": "https://tile.loc.gov/…/4a08066v.jpg",   // direct image where known, else null
  "rights": "no known restrictions",      // public domain | no known restrictions | copyright — link only |
                                          // unknown — link only
  "rights_basis": "LoC: No known restrictions on publication",
  "local": { … },                         // the JSON tools/fetch_image.py prints, or null (link-only)
  "verified": "viewed",                   // viewed (image or full record seen) | catalog-only (listing seen)
  "found_via": "loc.gov search 'prairie avenue chicago'",
  "notes": "What it shows and what it is worth to the 1904 reconstruction (materials, storeys, porches,
            fences, trees, carriage house, street surface…). Say if it post-dates alterations.",
  "measurements": []                      // [{ "what": "frontage", "value": "100 ft", "locator": "sheet 2" }]
}
```

## Rules (the library's own, restated)

1. **Never invent a record.** Every record is something the researcher actually found at
   `catalog_url`. A lead from secondary literature without a findable holder is written as
   a `document` record with `verified: "catalog-only"` and says so in `notes` — or goes in
   `WORKLOG.md` as a lead, not in a stream file.
2. **Rights decide what is copied.** Local files only for `public domain` or
   `no known restrictions`. Everything else is a link and a description.
   - **The public-domain cutoff rolls forward.** A work PUBLISHED in the United States more
     than 95 years before the current 1 January is public domain. As of 2026 that is
     **publication in 1930 or earlier** (owner, 2026-10-02, widened from "before 1929"); each
     January it advances one year.
   - **What counts as evidence.** The publication — the book, periodical, newspaper issue,
     atlas or catalogue — must be stated in the record, or verifiable at its catalog page. A
     date guessed from a file name or style is not evidence.
   - **Unpublished photographs** (family snapshots, museum-held prints) do not qualify by date.
     They follow the holder's statement, or stay link-only.
   - **A holder's own licence or restriction** governs its copies, whatever the date (for
     example the Houghton finding-aid images).
   - **`pending — permission requested`** (owner, 2026-10-02). An item MAY be stored and shown
     while a permission request to its holder is outstanding, but only when all three hold:
     - the request is written in `research/images/rights-requests/`;
     - the record names that file in `rights_request`;
     - `rights_basis` says why copying is defensible meanwhile (for example, an unpublished work
       whose author died more than 70 years ago).

     The viewer badges these items "Rights pending". If a holder refuses, delete the stored copies
     (fetch_image.py output in the store) and set the record back to link-only.
3. **A later image is evidence of its own date.** Say what changed between 1904 and the
   image date where it is known (HABS 1960s photos post-date alterations and demolitions).
4. Prefer front elevations; collect every angle.

### Glessner 1904 evidence review (T-2198)

All records associated with `pa-1800-22` require `evidence_review`: audit number
(1–168 for the original inventory, null for additions), actual review state,
review date, target date, phase, date basis, evidence role, geometry-use restriction,
reason and source URL. `family` is null until a relationship is established;
linked families require reciprocal `family_members` and the same qualified
`family_relationship`. A separate record is never assumed to be independent evidence.
`metadata_history` retains replaced library descriptions, ticket, date and reason.
See [the source review](../../docs/glessner-source-review.md) for the findings and
rights boundary. The merger validates this contract; the viewer publishes it.
Review does not override copyright or turn design intent into built fabric.

### Retrieval follow-up (T-2199)

`retrieval_review` records the retrieval date, outcome, canonical URL, source identity, date, rights, independence finding and exact-source SHA-256 when recovered. `metadata only` and `unavailable` never imply visual review. Updated descriptions and prior review objects remain in `metadata_history`. The Glessner follow-up closes all 17 retrieval rows: 10 recovered records and 7 still-unavailable images, plus a distinct 1945 IIT view. The published brief is `docs/glessner-reference-recovery.html`; raw request outcomes are `docs/glessner-retrieval-log.json`. Holder-hosted images remain links and no source-image bytes were added.
