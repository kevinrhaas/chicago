# Rights requests

Requests to holders for permission to copy items the collection keeps link-only. Each file is the
request as drafted, with the records it covers. When a holder answers, record the answer here and
update each record's `rights` / `rights_basis` (quoting the permission). Then run
`tools/fetch_image.py` and `tools/sync_image_store.py`.

**Published while pending** (owner, 2026-10-02; README rule 2). These items are already stored and
shown, badged "Rights pending". Each record carries `rights: pending — permission requested` and a
`rights_request` naming its file here.
- **If the holder grants permission:** set `rights` to the granted basis.
- **If the holder refuses:** delete the record's files from the store, set `local` to null and
  `rights` back to `unknown — link only`, then re-run `tools/sync_image_store.py`.

| request | holder | items | drafted | sent | published pending | answer |
|---|---|---|---|---|---|---|
| [aic-renwick-2026-10.md](aic-renwick-2026-10.md) | Art Institute of Chicago, Ryerson & Burnham Archives | 8 microfilm frames + 3 public-domain sheets (files) | 2026-10-02 | — | 2026-10-02: the 8 frames (the 3 sheets' image server refuses downloads) | — |
| [ghm-george-glessner-2026-10.md](ghm-george-glessner-2026-10.md) | Glessner House Museum | 10 George Glessner photographs (13 records) | 2026-10-02 | — | 2026-10-02: all 13 records | — |
