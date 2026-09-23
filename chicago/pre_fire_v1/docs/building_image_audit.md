# Building image audit — Wolf Point research lead

The Digital Research Library of Illinois History Journal article on Wolf Point exposed a real coverage gap: the database had 14 map images but no media linked to a building. The article is retained as a discovery and contextual source, while each copied image is traced to an archival or public-domain source.

## Added public-domain assets

| Subject | Asset | Created | Period depicted | Representation | Provenance and caution |
|---|---|---:|---|---|---|
| Wolf Tavern and Miller House | *Wolf's Point in 1833* | 1867 | 1833, after a George Davis drawing made in 1832 | retrospective lithograph | New York Public Library scan; Wolf Tavern is identified at left and Miller House at right; not a photograph or measured elevation |
| Wolf Tavern and Miller House | Andreas Wolf Point view | 1884 | 1830 | retrospective reconstruction | Cataloged as an imagined view; useful for interpretation, not exact architectural inference |
| Wolf Tavern and Miller House | *Chicago in 1833* | unknown | 1833 | retrospective postcard | Newberry/CARLI item; creation date and building-level accuracy are unresolved |
| Sauganash Hotel | Andreas/Braunhold lithograph | 1884 | circa 1831–1833 | retrospective lithograph | Public domain; Braunhold's first initial conflicts between repository records and is deliberately left unresolved |
| Green Tree Tavern | Green Tree Tavern / West Lake Street House | circa 1859 | circa 1859 | historical photograph | Public-domain Commons derivative linked to the Illinois repository record; building had not yet been moved |
| Point du Sable / Kinzie house | *Chicago Magazine* illustration | March 1857 | early 1800s | retrospective illustration | Published after the depicted period; not a measured architectural record |

`media.csv` stores asset metadata. `media_buildings.csv` is the many-to-many subject join so a single Wolf Point scene can be attached to both named buildings without duplicating the asset. `media_checksums.csv` records local-file integrity and dimensions.

## Excluded or corrected blog images

- The colored Wolf Point painting is credited to George Yelich (1926–2022) and has no open license. It was **not copied**. The NYPL lithograph is the public-domain substitute.
- The annotated relocation graphic uses Google Maps imagery and has no reuse license. It was **not copied**; movement should instead be represented as structured locations and events.
- The blog's Green Tree drawing is not a contemporary 1833 view. The underlying cut was published in 1883 and retrospectively reconstructed the building as remembered. It was not used in this first ingestion pass.
- The blog's post-move Green Tree photograph was published in 1901, not taken at the 1880 move. It remains a future candidate once an archival newspaper scan is acquired.

The blog page remains valuable as a research lead, but its Blogger image URLs are not treated as provenance.
