# Prairie Avenue — 1904 research library

The third Chicago Building Atlas research collection follows the pre-fire and rebuilding collections. Its modeling target is **1904**, with **1911** as the supplied Sanborn comparison endpoint. Earlier origins and later demolition/move events remain attached to each building. The geographic core is both sides of Prairie Avenue from 16th to 22nd Streets; adjacent context is explicitly labeled.

Open `viewer/index.html` through an HTTP server. The viewer is a research browser, not a finished 3D scene. It separates named-house histories, 1911 frontage readings, 1904 directory candidates, maps, and a focused Glessner dossier.

## What is held

- `data/library.json`: normalized, portable browser dataset, source registry and evidence layers.
- `data/*.csv`: buildings, dated events, field assertions, many-to-many source links, frontage and directory readings.
- `maps/originals/`: five supplied map JPEGs, unchanged, with checksums.
- `research/*-dossier.json`, `building-research.json`, `map-inventory.json`: full research findings, caveats and acquisition leads.
- `research/acquired-files.json`: checksums and retention status for actually downloaded files; catalog links alone are never counted as downloaded originals.
- `research/acquisition-manifest.json`: additional reports and photographs, including rights/retrieval results.
- `docs/`: methodology, Glessner priorities, source guidance and explicit gaps.

The **Prairie_Avenue_1904_Originals.zip** companion preserves larger PDFs, raw annual directory OCR, and archival photographs. These originals are excluded from Pages and Git history; their source URLs, hashes and rights notes stay in this repository. It is a research-access archive, not a grant of republication rights.

## Existing project connections

Reuse `../pre_fire_v1/data/` and `../postfire_1870s_v1/data/` for predecessor/context matching, but do not merge entities by name alone. The 4D project's `data/sources/habs_glessner_house_il_1015.json` and `habs_kimball_house_il_1077.json` are earlier source readings; this library extends their acquisition trail rather than silently changing their claims. Existing terrain memo `../4d/docs/RESEARCH/scene_1880s_prairie_avenue.md` reflects an older 1888 scene decision. **This library follows the owner's 1904 target; it does not rewrite the existing terrain pipeline or pretend that it already renders 1904.** T-0474–T-0477 and T-1250–T-1252 remain the scene construction work.

## Reproduce publication and checks

```sh
python3 chicago/prairie_1904_v1/tools/validate.py
python3 chicago/prairie_1904_v1/tools/publish.py
python3 -m http.server 8765 --directory site
```

The lightweight copy lives at `/prairie-1904/viewer/` after production promotion; `chicago/4d/tools/publish.sh` also mirrors it into `/4d/dev/prairie-1904/viewer/` for dev preview. Large originals never enter those copies. No production promotion is part of this change.

## Completeness

The library is substantial but **not certified parcel-complete**. A frontage label can represent a shared building or multiple entrances; a directory names selected residents, not every resident or building; a historical owner name is not a 1904 occupant. Sources still needed include individual census schedules, permits, full measured-plan transcription, utilities/paving ordinances and unlabeled outbuilding identities. See `docs/research-gaps.md`.
