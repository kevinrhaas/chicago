# 1812 Potawatomi camp coverings — `camp_1812_pbr`

T-3342. Three seamless procedural materials for the coverings of the Potawatomi camp of
August 1812 (`generators/archetypes/lodge_camp.py`), bound by material name in the renderer
by `renderers/web/js/camp-surfaces.js`:

| material (GLB name) | directory | tile (`span_m`) | what it is |
|---|---|---|---|
| `camp_cattail_mat` | `cattail_mat/` | 1.0 m | a lodge mat of cat-tail leaves sewn through with bark cord; leaves run up the image |
| `camp_elm_bark` | `elm_bark/` | 1.2 m | the outer face of an elm-bark sheet, the grain up the image |
| `camp_boughs` | `bough_thatch/` | 1.5 m | cut leafy boughs laid over an arbor's poles, a few days browned |

Rebuild every map with:

    python3 assets/textures/camp_1812_pbr/tools/generate_camp_1812_pbr.py
    python3 tools/ktx2_sheets.py --only camp_1812_pbr/

Each material carries the 1835 library's map-for-map layout at 1024 px (base colour, OpenGL
normal, packed ORM, 16-bit height), 512 px `*_web.jpg` copies of the three bound maps, their
`.ktx2` GPU derivatives, and a `material.json` stating the tile, orientation and confidence.
The look of every map is reconstructed from the texts the camp records cite
(`docs/LIBERTIES.md` L-1812-potawatomi-camp-2515); no photograph is used.
