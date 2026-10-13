# Prairie Avenue 1904 lakefront railway PBR library

Version 1.1.0 (T-2478, T-2479): **eight seamless 512 × 512 materials and one alpha card** for the
Illinois Central's right-of-way east of Prairie Avenue in the 1904 scene and its edge against the lake. It is the street-surface library's
sibling (`../prairie_1904_pbr/`), borrows that generator's noise and writers, and is built by one
deterministic script, `tools/generate_prairie_1904_rail.py`, that samples no photograph.

| group | material | tile (along × across) | used for |
|---|---|---|---|
| ballast | `cinder_ballast` | 2.00 × 2.00 m | the bed 1.75 m either side of every track |
| ground | `trodden_cinders` | 4.00 × 4.00 m | the right-of-way between and beside the tracks |
| verge | `weedy_verge` | 3.00 × 3.00 m | the 3 m verge along each edge of the right-of-way |
| timber | `tie_timber` | 2.44 × 0.229 m | the top of a crosstie, one tie per tile |
| edge | `riprap_limestone` | 4.00 × 4.00 m | the stone on the embankment's lakeward face, from above |
| edge | `limestone_block` | 1.00 × 1.00 m | the faces of the single blocks stood on that face near the eye |
| edge | `cap_timber` | 3.00 × 0.30 m | the 12-inch cap timber along the crest, and its piles |
| edge | `made_ground` | 4.00 × 4.00 m | the fill between the crest and the east verge |
| foliage | `grass_tuft` | 0.28 × 0.55 m card | the weeds on the verges and the made ground, as crossed cards |

Each surface keeps four masters (`*_basecolor.png`, `*_normal_gl.png`, `*_height16.png`, `*_orm.png`)
and three web derivatives (`*_basecolor_web.jpg`, `*_normal_gl_web.jpg`, `*_orm_web.jpg`), which are
what `tools/publish.sh` ships and `renderers/web/js/railway.js` binds. The tuft is one RGBA PNG,
`grass_tuft_web.png`. Fewer masters than the street library keeps: the DirectX normal and the loose
AO, roughness and metallic maps are one line of numpy from these, and nothing binds them.

Image x runs **along** the track (along the shore for `edge/`); image y runs **across** it. The tie tile is the whole tie: x is its
length, y its width, with a darker seat where each rail stands.

## What these are evidence of

**Nothing.** Which ground wears which material is `data/railway/1904_spec.json`'s to say. George
Glessner's photographs at 18th Street show the bed dark, fine and filled to the ties; that is all a
map here borrows from a source. Colour, grain, clinker, weeds and timber are ours (`docs/LIBERTIES.md`
L-ic-tracks-2478), and so is every stone of the lake edge (L-ic-lake-edge-2479). The first four
materials and the tuft keep their seeds; the edge's carry their own, so adding them moved nothing.

Regenerate in place with `python3 tools/generate_prairie_1904_rail.py` (numpy, scipy, Pillow).
