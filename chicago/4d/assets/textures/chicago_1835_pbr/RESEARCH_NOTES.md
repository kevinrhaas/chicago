# Research notes

## Project evidence used first

The texture inventory was derived from the reconstruction itself rather than a generic “old
west” material list. The principal local sources were:

- `chicago/4d/docs/RESEARCH/materials.md` — shipped-surface census, material evidence,
  roughness reasoning, and tile dimensions.
- `chicago/4d/generators/common/materials.py` — current engine-neutral finish vocabulary and
  mean material values.
- `chicago/4d/docs/RESEARCH/chimneys.md` — framed-building brick versus reconstructed
  cat-and-clay log-cabin chimney treatment.
- `chicago/4d/docs/research/01-terrain-hydrology.md` — low, wet ground; loam, muck, and water
  relationships.
- `chicago/4d/docs/research/04-structures-south.md` — overwhelmingly frame/log fabric,
  unpaved streets, standing water, mud, beach, and sand hills.
- `chicago/4d/docs/RESEARCH/north_side_school_1833.md` — the direct “sheeted and shingled roof”
  attestation.

## External cross-checks

The National Park Service Technical Preservation Services material was used to cross-check how
historic material systems differ visually and physically:

- Preservation Brief 2, *Repointing Mortar Joints in Historic Masonry Buildings*:
  https://www.nps.gov/orgs/1739/upload/preservation-brief-02-repointing.pdf
- Preservation Brief 4, *Roofing for Historic Buildings*:
  https://www.nps.gov/orgs/1739/upload/preservation-brief-04-roofing.pdf
- Preservation Brief 10, *Exterior Paint Problems on Historic Woodwork* (listed in the index):
  https://www.nps.gov/orgs/1739/preservation-briefs.htm
- Preservation Brief 19, *The Repair and Replacement of Historic Wooden Shingle Roofs*
  (listed in the index): https://www.nps.gov/orgs/1739/preservation-briefs.htm
- Preservation Brief 26, *The Preservation and Repair of Historic Log Buildings*:
  https://www.nps.gov/orgs/1739/upload/preservation-brief-26-log-buildings.pdf

These references support broad material behavior—lime mortar, historic paint weathering,
wood-shingle variation, log/chinking distinction—not an unsupported claim that a particular
Chicago building carried a particular finish.

## Deliberate exclusions

- No asphalt, concrete paving, Portland-cement mortar, modern dimensional lumber, modern tire
  tracks, galvanized sheet metal, or synthetic coatings.
- No bark/puncheon roof texture: the current project evidence neither models nor supports it.
- No generic “cobblestone street”: Chicago's 1835 streets in the reconstruction are unpaved.
- No photographic texture extraction from rights-unclear retrospective Chicago images.
- No vegetation cards, human skin/clothing, water shader, decals, or signage lettering; those
  are separate systems and are not ordinary tileable PBR surfaces.

