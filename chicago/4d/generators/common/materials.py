"""The material sheet, as code — `docs/RESEARCH/materials.md` wired into the town.

R-W2a measured 1,353 material slots out of the shipped GLBs and wrote them up as a
document. The document reached nothing: every colour and every roughness in this
project was still a literal sitting in whichever module happened to paint that
surface, and two generators — the nine Blender archetypes and the pure-Python
`inferred_placeholder` — carried two palettes that shared not one value. T-0007 is
the parcel that makes the sheet the source. This module IS the sheet: every row
below is a row of materials.md §1.1 or §2, and every archetype and the placeholder
generator now read their colours and their roughness from here rather than from a
constant of their own.

## What a row is

A surface is TWO things, and keeping them apart is what lets the sheet describe a
whitewashed clapboard wall without a combinatorial table:

* a **substrate** — what the wall is made OF. It owns the roughness, the tiling rate
  and the dimensional module that rate is a whole multiple of (materials.md §3.2:
  every tile is 32 clapboard courses, or 12 log courses, or 20 sheathing boards, so
  the seam lands on the surface's own rhythm rather than on a number chosen to look
  right). No substrate owns a colour.
* a **finish** — what it WEARS. It owns the colour, and the three coating finishes
  own a roughness too, because materials.md §2.1 argues them explicitly: a limewashed
  wall is the flattest surface in the town, and lead paint the only smooth one. §2.1
  calls those three "overlay, not a tile" for exactly this reason — they modify the
  substrate's value and gloss and leave its rhythm showing through.

So `resolve(substrate, finish)` gives the pair the exporter needs, and the tile rate
sits beside it for the bake half to draw its atlas against the same numbers.

## COLOUR SPACE — materials.md §3.4's one process rule

**Every value here is LINEAR**, which is what glTF `baseColorFactor` means and what a
Blender node colour is. The six wall finishes and the four roof conditions are
written as hex because that is the form `inferred_placeholder.py` committed them in,
and materials.md §3.4 proved from the whitewash pair that they were authored as
linear values rather than sRGB ones — read as sRGB the two generators' whitewash
would sit 40 % apart in blue instead of 12.6 %. `hex_rgba` therefore divides by 255
and does nothing else, and this paragraph is the "state the space in the file that
holds it" §3.4 asks for. A PNG atlas is sRGB by convention; the bake half has to
convert, and this is the sentence that tells it so.

## WHAT IS NOT CLAIMED HERE — R-W2a finding 2, and it stands

**No source in this repository states what any Chicago roof of 1835 was covered
with.** 315 records state a roof type and a pitch; zero state a covering. So there is
no `shingle` row in this file and no `roof_board` row, and the roof rows below are
graded by **condition** — fresh, weathered, darkened, patched — which is a statement
about weathering that 218 records actually carry, and not a statement about material.
A future parcel that finds a source for the covering adds the rows then; inventing
one here to make the sheet look finished is the exact move `docs/LIBERTIES.md`
exists to catch. materials.md §2.2 and §5 own the open question.

Likewise absent: the shingle exposure, and a brick or stone course dimension. §3.2
says plainly that no source this project holds gives one, so `brick` and `stone`
carry `tile_m = None` rather than a modern brick quietly chosen to make the
arithmetic land.

## The blast radius, stated

`generators/mesh_inputs.py` hashes every byte of `generators/common/` into every
archetype's mesh inputs, so an edit here stales the whole town. `frame_tavern.py`
keeps its own two colours for precisely that reason and is right to: a value only one
archetype reads does not belong in a shared file. What is here is the opposite case —
the wall finishes, the roof conditions and the log fabric are read by every building
generator in the project and by the placeholder path as well, and holding one copy of
them is the whole point of a sheet.
"""

from __future__ import annotations

from dataclasses import dataclass

# The sheet this module is. Quoted in every row so a reader can find the argument.
SHEET = "docs/RESEARCH/materials.md"

# Every colour in this file is linear. See the module docstring.
COLOUR_SPACE = "linear"


def hex_rgba(value: str) -> tuple[float, float, float, float]:
    """A hex triple as a LINEAR rgba. Divides by 255 and does nothing else.

    Byte-compatible with `generators/inferred_placeholder.py`'s own helper, which is
    load-bearing: that generator's 94 committed GLBs are gated on their exact bytes,
    so the two paths have to produce the same floats from the same string.
    """
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1.0,)


@dataclass(frozen=True)
class Substrate:
    """What a surface is made of: its roughness, its tile, and the module the tile is
    a whole multiple of. Never a colour — that is the finish's."""

    key: str
    roughness: float
    tier: str
    note: str
    #: metres of surface one square of the atlas covers; None where materials.md
    #: §3.2 says the rate cannot be set without a source it does not hold
    tile_m: float | None = None
    #: the surface's own committed dimensional constant, which `tile_m` is a whole
    #: number of — the condition §3.2 puts on every rate
    module_m: float | None = None
    #: texel density at 1024², which §4 W2 bounds at 128–256 px/m
    texel_px_per_m: float | None = None


@dataclass(frozen=True)
class Finish:
    """What a surface wears. Owns the colour; owns a roughness only where
    materials.md §2.1 argues one, which is the three coatings."""

    key: str
    rgba: tuple[float, float, float, float]
    tier: str
    note: str
    #: a coating states its own gloss and overrides the substrate's (§2.1)
    roughness: float | None = None
    #: True for the three coatings, which are overlays rather than fabrics. The trim
    #: rule below reads it, because boards took the paint and bare stock did not.
    coating: bool = False


# --------------------------------------------------------------- the substrates
#
# materials.md §2.1 and §2.2, one row per surface that actually ships. Tiles are the
# sheet's own arithmetic — 32 clapboard courses of 0.14 m, 12 log courses of 0.34 m,
# 20 sheathing boards of 0.229 m — and land inside the 128–256 px/m band by
# construction rather than by choice.

SUBSTRATES: dict[str, Substrate] = {
    "clapboard": Substrate(
        key="clapboard", roughness=0.86, tier="inferred",
        tile_m=4.48, module_m=0.14, texel_px_per_m=228.6,
        note="Riven or sawn horizontal siding weathering silver. The form is attested "
             "on the Sauganash, the agency house and the Green Tree; the 0.14 m "
             "exposure is a period stock, committed as the archetypes' own default "
             "since T-0049. 32 courses to the tile."),
    "board_and_batten": Substrate(
        key="board_and_batten", roughness=0.88, tier="reconstructed",
        tile_m=4.272, module_m=0.356, texel_px_per_m=239.7,
        note="Vertical boards with a batten over each joint at the usual 14 in "
             "set-out. NO source in this repository puts board-and-batten on any "
             "named Chicago building in 1835 — the set-out is typological. 12 battens "
             "to the tile."),
    "vertical_board": Substrate(
        key="vertical_board", roughness=0.90, tier="reconstructed",
        tile_m=4.58, module_m=0.229, texel_px_per_m=223.6,
        note="Plain vertical sawn boards, no batten. One record carries it and its "
             "own note says INVENTED, NOT DERIVED. 20 boards to the tile."),
    "hewn_log": Substrate(
        key="hewn_log", roughness=0.92, tier="attested",
        tile_m=4.08, module_m=0.34, texel_px_per_m=251.0,
        note="Squared log courses. The log town is the best-attested fabric here; the "
             "0.34 m course is logwork.py's, argued from a squared wall log. 12 "
             "courses to the tile."),
    "chinking": Substrate(
        key="chinking", roughness=0.95, tier="inferred",
        tile_m=2.04, module_m=None, texel_px_per_m=251.0,
        note="Clay and lime between the courses, standing proud. Near-uniform: dried "
             "lime does not scatter the way timber does. The tile is HALF the log's "
             "at half the map, which holds the same 251 px/m — a wall whose two "
             "materials render at two densities reads as two walls."),
    "sawn_board": Substrate(
        key="sawn_board", roughness=0.94, tier="inferred",
        tile_m=4.00, module_m=None, texel_px_per_m=256.0,
        note="Plain sawn stock, random widths, gappy. The widths are geometry — the "
             "outbuilding deals them board by board — so the sheet carries grain "
             "only."),
    "heavy_timber": Substrate(
        key="heavy_timber", roughness=0.90, tier="inferred",
        tile_m=4.00, module_m=None, texel_px_per_m=256.0,
        note="Posts, plates, jambs, headers and battens. Heavy stock holds moisture "
             "and weathers darker than siding. materials.md §4 finding 3 recorded that "
             "TWO different materials shared this name and only this one shipped; "
             "T-0126 splits them, and this substrate is the WEATHERED one — the "
             "`HEAVY_TIMBER` finish. Fresh mill stock on an exposed storefront frame "
             "is the `SAWN_FRAMING` finish and carries its own 0.92."),
    "brick": Substrate(
        key="brick", roughness=0.90, tier="inferred",
        tile_m=None, module_m=None, texel_px_per_m=None,
        note="Fired brick in courses. Two records are attested brick. NO source in "
             "this repository gives a brick or a course dimension, so the rate is "
             "UNRESOLVABLE (§3.2) and is left None rather than filled with a modern "
             "brick."),
    "stone": Substrate(
        key="stone", roughness=0.93, tier="reconstructed",
        tile_m=None, module_m=None, texel_px_per_m=None,
        note="Rubble or dressed masonry. The one record carrying it says bare masonry "
             "is unattested and a limewash the commoner Great Lakes finish. Rate "
             "unresolvable, as brick."),
    "earth": Substrate(
        key="earth", roughness=0.95, tier="inferred",
        tile_m=4.00, module_m=None, texel_px_per_m=None,
        note="Trodden ground and turf. Both records carrying it say plainly that no "
             "source describes it. A noise tile: no rhythm to be integral with."),
    # The roof substrate is deliberately ONE row and deliberately unnamed as a
    # covering. See the module docstring: nothing states what these roofs were made
    # of, so the sheet describes the plane and not its material. The roughness is
    # the archetypes' own committed value and is NOT re-argued here — materials.md
    # §3.1 says in terms that the deliverable is a roughness map, not better
    # constants, and that R-W2b should not spend a round re-tuning the 18 numbers.
    "roof_plane": Substrate(
        key="roof_plane", roughness=0.90, tier="reconstructed",
        tile_m=None, module_m=None, texel_px_per_m=None,
        note="The roof plane, COVERING UNSTATED. R-W2a finding 2: 315 records state a "
             "roof type, zero state what it is made of. No exposure, therefore no "
             "tile — materials.md §2.2 says pick the exposure from a source or record "
             "a liberty, and this parcel does neither because it invents nothing."),
}


# ------------------------------------------------------------------ the finishes
#
# materials.md §1.1's six wall finishes and §2.1's three coatings. The six are the
# vocabulary the DATA speaks — `reconstruction.finish_key`, dealt by the 665-roof
# programme and committed on 222 records — and until this parcel they were read by
# `inferred_placeholder.py` alone, so a weathered wall and a fresh one were the same
# pixel on all 244 archetype buildings (finding 4). The hexes are verbatim from that
# generator, which is what keeps its 94 committed GLBs byte-identical.

FINISHES: dict[str, Finish] = {
    "fresh_timber": Finish(
        key="fresh_timber", rgba=hex_rgba("#C3A478"), tier="reconstructed",
        note="New sawn stock, still pale and warm. §1.1; 37 placeholder walls and, "
             "from T-0007, every archetype building the programme dealt it to."),
    "weathered_timber": Finish(
        key="weathered_timber", rgba=hex_rgba("#817D72"), tier="reconstructed",
        note="Bare stock silvered off by a season or two of weather. §1.1."),
    "mixed_patch": Finish(
        key="mixed_patch", rgba=hex_rgba("#BFAE8E"), tier="reconstructed",
        note="A wall patched from more than one stock, averaged. §1.1."),
    "ochre": Finish(
        key="ochre", rgba=hex_rgba("#A98B52"), tier="reconstructed",
        note="An earth-pigment wash. §1.1. No named Chicago building in this "
             "repository is attested ochre; it is a period finish dealt by the "
             "programme, not a reading of any source about any building."),
    "whitewash": Finish(
        key="whitewash", rgba=hex_rgba("#D8D1BC"), roughness=0.90, coating=True,
        tier="reconstructed",
        note="Lime wash over whatever the wall is made of — it coats the substrate "
             "and does not replace it, so the courses stay showing through. Chalky "
             "and flat: the LEAST glossy surface in the town (§2.1). ATTESTED where a "
             "record attests it and never a default. This value converges the two "
             "palettes materials.md §3.4 measured 12.6 % apart in blue: the "
             "archetypes' 0.88/0.87/0.83 is retired in favour of the vocabulary the "
             "records already speak (finding 5)."),
    "red_oxide": Finish(
        key="red_oxide", rgba=hex_rgba("#7A4437"), roughness=0.85, coating=True,
        tier="reconstructed",
        note="Iron-oxide paint. §2.1 grades it conjectural at the building level and "
             "inferred as a period finish: no named Chicago building here is attested "
             "red. One row for both paths, replacing the archetypes' 0.55/0.16/0.13."),
    "white_paint": Finish(
        key="white_paint", rgba=(0.90, 0.89, 0.85, 1.0), roughness=0.60, coating=True,
        tier="attested",
        note="Lead paint, a remarkable expense here and ATTESTED for exactly one "
             "building — the Sauganash, 'a pretentious white two-story building'. "
             "0.60 is the sheet's number and the point of it: the only smooth wall in "
             "Chicago, which is why its neighbours' plainness reads."),
    "unpainted": Finish(
        key="unpainted", rgba=(0.52, 0.44, 0.34, 1.0), tier="reconstructed",
        note="The archetypes' own committed unpainted tone, measured in §1 across 94 "
             "shipped wall slots. Kept as the default for a record that deals no "
             "finish, so that no NAMED building changes colour without a record "
             "saying it should."),
    "weathered_board": Finish(
        key="weathered_board", rgba=(0.335, 0.310, 0.268, 1.0), tier="reconstructed",
        note="The outbuilding's own board tone, and deliberately NOT the taverns' "
             "unpainted brown: bare sawn softwood silvers within a season, and a shed "
             "carrying a tavern's colour would read as the same building at a "
             "distance. §1, 69 shipped `board` slots."),
}


# --------------------------------------------------------------- roof conditions
#
# §1.1's four. `roof_condition` is stated on 218 records and, until this parcel, was
# read by `inferred_placeholder.py` alone. It says how weathered the roof is. It does
# NOT say what the roof is made of, and nothing in this project does — see the module
# docstring.

ROOF_CONDITIONS: dict[str, Finish] = {
    "fresh": Finish(key="fresh", rgba=hex_rgba("#5E4938"), tier="reconstructed",
                    note="Newly laid, still brown. §1.1."),
    "weathered": Finish(key="weathered", rgba=hex_rgba("#6C6258"), tier="reconstructed",
                        note="Silvered off, the palest of the four. §1.1."),
    "darkened": Finish(key="darkened", rgba=hex_rgba("#4B4037"), tier="reconstructed",
                       note="Weather-blackened. §1.1."),
    "patched": Finish(key="patched", rgba=hex_rgba("#3C3732"), tier="reconstructed",
                      note="Mended more than once, the darkest of the four. §1.1."),
}

#: What a roof wears where no record deals a condition — the one colour §1 measured
#: across all 234 shipped `roof` slots. A named building whose record says nothing
#: about its roof keeps exactly the roof it had.
ROOF_DEFAULT = Finish(
    key="roof_default", rgba=(0.34, 0.30, 0.27, 1.0), tier="reconstructed",
    note="The archetypes' committed roof tone, §1. Unchanged by T-0007 wherever a "
         "record deals no condition, which is every named building in the town.")


# ------------------------------------------------------------------- other rows
#
# §1 and §2.3. These ship today at these values and are held here so one file
# answers "what is this surface" for every generator. Values are unchanged, with
# the openings-and-glazing family below as T-0126's exception — that one converges.

HEWN_LOG = Finish(
    key="hewn_log", rgba=(0.340, 0.266, 0.188, 1.0), tier="inferred",
    note="Weathered hewn oak. logwork.py argues it about a fifth darker than the "
         "paler LOG_RGBA it replaced, having measured that a first pass at 0.295 put "
         "the log dwellings visibly in a different town from the Sauganash's wing. "
         "materials.md finding 2: the Sauganash's own wing never followed that "
         "reconciliation and is the ONE log wall in Chicago built from the other "
         "value. T-0007 brings it across, so the town has one log.")
CHINKING = Finish(
    key="chinking", rgba=(0.700, 0.670, 0.590, 1.0), tier="inferred",
    note="Clay and lime, pale where the logs are dark, standing proud so it catches "
         "light. §1, 50 shipped slots.")


# ------------------------------------------------- openings and glazing (T-0126)
#
# materials.md §2.3's other half, and the family T-0007 deliberately left. Two rows,
# and the reason there are two rather than one is the only distinction the evidence
# actually supports: a pane reflects the sky and a hole does not.
#
# WHAT WAS MEASURED FIRST, because the ticket's own count no longer holds. §2.3 was
# written against FOUR values on four generators; re-measured over `assets/gltf/`
# on 2026-08-24 there are THREE, on 287 slots, because the pure-Python placeholder
# path that carried the fourth ships nothing any more — `inferred_placeholder.py
# --check` reports "0 flagged placeholder GLBs; 226 superseded by a canonical bake",
# so `placeholder_opening_dark` (#2D3D33 at 0.70, a green nothing in this repository
# argues for) is dead code and not a shipped surface. What ships is:
#
#   dark      0.070/0.080/0.090  r 0.35  112 slots  frame_dwelling
#   dark      0.070/0.080/0.090  r 0.40   58 slots  log_dwelling, fort_structure, palisade
#   interior  0.072/0.068/0.060  r 0.60  117 slots  outbuilding
#
# Two colours 0.03 apart at their widest and three roughnesses spread over 0.25 —
# which is the half a visitor sees, because roughness is what decides whether a
# surface catches the sun. A doorway on a frame dwelling glinted and the identical
# doorway on the shed beside it did not.

DARK = Finish(
    key="dark", rgba=(0.072, 0.068, 0.060, 1.0), roughness=0.60,
    tier="reconstructed",
    note="ONE ROW for every dark recess in the town: a window or door panel on a "
         "frame dwelling, a log cabin's door, window and gable vent, the fort's "
         "loopholes and its root-house door, and the outbuilding's interior seen "
         "through a board gap, a vent or an open bay. 'Surfaces, not holes' — "
         "frame_dwelling._opening says it in terms: at this level of detail these "
         "are flat panels standing in for an interior, and interiors are out of "
         "scope. THE COLOUR is the warm near-black this sheet already carried (117 "
         "of the 287 slots ship it); the cool 0.070/0.080/0.090 the other 170 wore "
         "is retired, because a cool cast is SKY, and sky in an opening is the "
         "`GLASS` row's business. Light that reaches an unlit room here has bounced "
         "off timber and lime, so it comes back warm. Near-black rather than black: "
         "an interior in daylight is dark, not a hole in the world. THE ROUGHNESS "
         "is bounded rather than read, and both bounds are values this project "
         "already ships. It cannot sit at `GLASS`'s 0.25, because EVERY ONE of the "
         "287 slots carries surfaces that are certainly not glazed — doorways, gaps "
         "between boards, open bays, loopholes, gable vents, the stockade's shut "
         "gate leaves — and at a glazing gloss an open bay takes the same sun glint "
         "a shop window does. It cannot sit at the bare fabrics behind it either "
         "(heavy_timber 0.90, hewn_log 0.92, sawn_board 0.94), because 156 of the "
         "287 ALSO carry windows, and on the 112 frame dwellings among them every "
         "window is sized off the Green Tree's attested 6x8 lights — so those panels "
         "stand for glazed sash, and a sash with no specular reads as a hole knocked "
         "in the wall. Nothing states where between the two it sits, so it sits at "
         "the midpoint, 0.575, taken to the 0.60 the town already speaks rather "
         "than to a newly invented 0.575 that would mean the same thing 0.025 away "
         "(buildings.js: nothing in the dataset uses two roughness values closer "
         "than 0.01). §2.3; docs/LIBERTIES.md, 'One dark behind every opening in "
         "Chicago' — cited by TITLE because a number in this file cannot be "
         "renumbered without re-staling all 342 masters, and six liberty numbers "
         "collided across parallel branches on 2026-08-24 alone. NOT EVERY USE IS AN OPENING and "
         "this row does not pretend otherwise: the fort's sun-dial plate and its "
         "lighthouse lantern drum, the log dwelling's iron hinge straps and the "
         "stockade's two shut gate leaves ride on the same slot. All are dark and "
         "small; separating them would add a material to an asset, which T-0126's "
         "acceptance forbids and K36(a) is the reason for.")
GLASS = Finish(
    key="glass", rgba=(0.09, 0.11, 0.13, 1.0), roughness=0.25,
    tier="reconstructed",
    note="Small-paned sash, seen from the street: mostly the sky reflected in the "
         "pane and a little of the dark room behind it. §2.3 calls it 'the only "
         "sub-0.5 surface on a building'. Already consistent across its two "
         "generators (frame_storefront, frame_tavern — 48 slots at one value), so "
         "T-0126 brings it onto the sheet UNCHANGED rather than re-arguing it. WHAT "
         "THE SOURCES CARRY, measured across data/sources/ on 2026-08-24: the word "
         "'glass' appears in NO source this repository holds. Two records reach the "
         "glazing at all — the Green Tree's `fenestration: small_paned_sash`, "
         "`inferred` off Gale's guest chamber 'about 12x12, with two windows 6x8' "
         "(chicagology_prefire127), which is the one attested pane size in the "
         "dataset and the number frame_dwelling sizes every window from; and the "
         "Sauganash's Trowbridge plate, which shows louvred shutters ON THE SASH "
         "(trowbridge_sauganash_hotel). So THAT the town was glazed in small lights "
         "is inferred and reasonably held; what colour a pane reads at fifty metres "
         "is stated nowhere, and this value is RECONSTRUCTED. Muntins, sash and "
         "reveal are geometry and belong to R-W3c, not here.")

# -------------------------------------------------- heavy timber, split (T-0126)
#
# materials.md §4 finding 3, discharged: `timber` was ONE NAME over TWO materials
# 3.2x apart in linear red, and both are defensible because they are not the same
# thing. Re-measured 2026-08-24: `outbuilding`'s ships on 117 slots and
# `frame_storefront`'s ships on ZERO, exactly as the finding said — no record in
# this dataset turns `framing_exposed` on, so the paler value has never been
# rendered and the collision is LATENT. It would have surfaced the first time a
# storefront exposed its framing beside a shed, as two different materials wearing
# one name. Two rows, two names, and the archetypes' material slots renamed to
# match, so the name in the shipped GLB says which of the two it is.
HEAVY_TIMBER = Finish(
    key="heavy_timber", rgba=(0.208, 0.172, 0.128, 1.0), roughness=0.90,
    tier="inferred",
    note="The outbuilding's heavy squared stock: posts, plates, jambs, headers and "
         "battens. Heavy stock holds moisture and weathers darker than thin sawn "
         "siding, and a post darkens from the foot up — outbuilding.py chose it "
         "against a render in which the door frame came out warmer and no darker "
         "than the siding around it. Roughness is the `heavy_timber` substrate's, "
         "restated on the row so the two timbers can be read side by side. Shipped "
         "as the material `heavy_timber`, renamed from `timber` by T-0126.")
SAWN_FRAMING = Finish(
    key="sawn_framing", rgba=(0.66, 0.56, 0.40, 1.0), roughness=0.92,
    tier="reconstructed",
    note="Fresh sawn framing on a storefront that exposes it — paler than the wall "
         "it stands in, not darker, because this is new mill stock and not a shed's "
         "weathered heavy timber. Lumber came into Chicago sawn, from St Joseph by "
         "scow. GRADED DOWN from the `inferred` its shared row carried: no record "
         "in this dataset turns `framing_exposed` on, so there is no building this "
         "value is an inference ABOUT, and a value that has never been rendered "
         "cannot have been reasoned from anything it renders. Shipped as the "
         "material `sawn_framing`, renamed from `timber` by T-0126; it still "
         "reaches no GLB, and now it cannot be mistaken for the row above when it "
         "does.")


# ---------------------------------------------- the bare masonry, and the stack
#
# R-W2a finding 1, discharged by T-0008: `frame_dwelling`, `frame_storefront` and
# `log_dwelling` built their stacks with the ROOF material, so every stack in the town
# was painted the colour of the roof it passes through — wrong in a way a visitor sees
# from the street. Measured off the resolved parameters of the committed masters, that
# is **157 stacks on 143 buildings** counting `frame_tavern`, which took the same fix;
# R-W2a's own "219 on 199" does not reproduce on this tree and is left as it was
# written rather than quietly restated. The fabric question the finding left open is
# answered in `docs/RESEARCH/chimneys.md`, and its answer is TWO materials rather than
# one, because the two stacks are two different objects:
#
# * A FRAMED house's stack rises inside the building and breaks the roof at the ridge.
#   It has to be masonry to do that, and the masonry Chicago had is brick: Blodgett's
#   brick-yard opened on the North Side in the spring of 1833 (`brickyard_north_side`,
#   Andreas), the Lake House went up in brick in 1835, and the one coloured witness to
#   any Chicago stack — the Petford watercolour of the Sauganash, image 8 of the
#   owner's 2026-08-18 brief — paints **brick chimneys** on a framed clapboard block.
#   INFERRED, and the colour is not a new one: it is `frame_tavern`'s committed
#   `BRICK_RGBA`, wired to the Sauganash by T-0092, which now lives here so the town
#   has ONE brick instead of an archetype-local copy per archetype (§2.3's complaint).
# * A LOG cabin's stack stands OUTSIDE the gable, and `log_dwelling._stack` has always
#   said why in as many words: a stick-and-clay or fieldstone stack built against the
#   wall can be pulled away from the building when it catches fire. Nothing in this
#   repository attests any log house's stack, so this is RECONSTRUCTED — the daub the
#   sticks are laid up in, BOUNDED between the chinking it is made of and the palest
#   roof it stands beside, and sitting at the midpoint because nothing says where else
#   it sits. `docs/LIBERTIES.md` L26 owns every stack's POSITION; L168 owns its fabric.
#
# Neither row claims a stack for a building whose record does not count one, and
# neither is a covering claim about the roof it passes through.

# T-0332 RENAMED THIS ROW, AND THE RENAME IS THE WHOLE OF THAT TICKET. It was
# `CHIMNEY_BRICK` from T-0008, when a stack was the only thing in the town made of
# brick. T-0267 brought the fort's wall onto it and T-0092's tavern stack was already
# on it, so one row named for one surface was being read by three, two of them
# attested brick WALLS and neither of them a chimney. The name is now the FABRIC —
# which is what a material sheet row is — and the surfaces ask for it through the two
# selectors below rather than naming it, so nothing has to be renamed again the next
# time a third kind of brick surface arrives. materials.md §9.5 filed it; §10 closes
# it. No alias is kept: three call sites is not a compatibility surface, and a sheet
# carrying two names for one row is the drift this rename exists to end.
#
# The VALUE is untouched, to the last decimal, and that is the check on the parcel:
# a rename that repaints a building is the wrong change.

BRICK = Finish(
    key="brick", rgba=(0.45, 0.23, 0.17, 1.0), roughness=0.85, tier="inferred",
    note="Unpainted soft-mud brick — the town's ONE brick, on a chimney and on a "
         "wall alike. Verbatim `frame_tavern.BRICK_RGBA` (T-0092), off the Petford "
         "watercolour's brick chimneys, so the Sauganash's own stacks do not change "
         "colour when the rest of the town's stop being roof-coloured. It is NOT a "
         "claim that the fort's 1816 brick matched the town's 1833 brick: nothing "
         "here shows the colour of any fort surface, and the row is read there "
         "because it is the only brick this project has argued. "
         "docs/RESEARCH/chimneys.md §2 and §6, materials.md §9 and §10.")
CHIMNEY_STICK_CLAY = Finish(
    key="chimney_stick_clay", rgba=(0.562, 0.527, 0.468, 1.0), roughness=0.95,
    tier="reconstructed",
    note="A cat-and-clay stack: split sticks laid up in courses and daubed inside and "
         "out with the same clay the wall below it is chinked with. Nothing attests any "
         "Chicago log house's stack, so the tone is BOUNDED rather than read, and both "
         "bounds are values this project already ships: it cannot be as pale as the "
         "CHINKING (0.700/0.670/0.590), which is the same clay sitting sheltered under "
         "an eave while a stack takes weather and smoke on every face; and it cannot be "
         "as dark as the palest ROOF CONDITION (weathered, 0.424/0.384/0.345), or it "
         "stops reading as masonry against the roof it stands beside — which is the "
         "whole defect T-0008 exists to fix. Nothing states where between the two it "
         "sits, so it sits at the midpoint of the two, to three decimals. Roughness "
         "is the sheet's `earth` substrate, because the surface is daub. "
         "docs/LIBERTIES.md L168, docs/RESEARCH/chimneys.md §3.")


# ------------------------------------------------------------------- selection
#
# The half materials.md §2 calls "selected by". Until T-0007 the answer for most
# rows was "nothing".

#: Which substrate a wall is, given what the record says it is built of and clad in.
#: `cladding` is stated on 27 records and read on 22 (finding 3); everything else
#: falls back on the construction, which every record states.
_CLADDING_SUBSTRATE = {
    "clapboard": "clapboard",
    "board_and_batten": "board_and_batten",
    "vertical_board": "vertical_board",
}
_CONSTRUCTION_SUBSTRATE = {
    "log": "hewn_log",
    "hewn_log": "hewn_log",
    "plank": "sawn_board",
    "board": "sawn_board",
    "brick": "brick",
    "stone": "stone",
    "earth": "earth",
    # A framed wall says nothing about its skin, and every framed building in this
    # dataset that does not state a cladding is clapboarded — which is the commonest
    # wall in the town and the one the archetypes build by default.
    "balloon_frame": "clapboard",
    "braced_frame": "clapboard",
    "frame": "clapboard",
}

#: `paint` values that name a coating rather than a bare wall, mapped onto the
#: finish rows. `unpainted` is not here: it means the wall wears its own stock, and
#: which stock is then the record's `finish_key` to say.
_PAINT_FINISH = {
    "white": "white_paint",
    "whitewash": "whitewash",
    "red": "red_oxide",
    "red_oxide": "red_oxide",
    "ochre": "ochre",
}


def wall_substrate(construction: str | None = None, cladding: str | None = None,
                   default: str = "clapboard") -> Substrate:
    """The substrate row for a wall — the roughness and the tile, never the colour."""
    if cladding and cladding in _CLADDING_SUBSTRATE:
        return SUBSTRATES[_CLADDING_SUBSTRATE[cladding]]
    if construction and construction in _CONSTRUCTION_SUBSTRATE:
        return SUBSTRATES[_CONSTRUCTION_SUBSTRATE[construction]]
    return SUBSTRATES[default]


def wall_finish(paint: str | None = None, finish_key: str | None = None,
                default: str = "unpainted") -> Finish:
    """Which finish a wall wears, and the ORDER is the argument.

    1. **A stated coating wins.** Where a record says white, whitewash or red, that
       is a claim about this building's surface and it outranks anything a schedule
       dealt. It is also how the one attested paint in the dataset — the Sauganash's
       white — survives this parcel untouched in kind and improved in gloss.
    2. **Otherwise the record's own `finish_key` decides.** On a reconstructed
       anonymous roof the two attributes never disagree — every one of the 44 records
       carrying both states `whitewash` against `whitewash` and `red` against
       `red_oxide` — so this is not a tie-break between rival claims. It is a choice
       between a value the 665-roof programme dealt against a committed schedule and
       a `paint: unpainted` the archetype's own defaults wrote into the record with a
       note saying, in terms, that the family band does not speak to paint or finish
       and the value is the generator's type default. The dealt finish is the better
       evidence of the two, and it is the one 156 records were carrying into nothing.
    3. **Otherwise the archetypes' committed unpainted tone**, so nothing that has no
       record to read changes colour.
    """
    if paint and paint in _PAINT_FINISH:
        return FINISHES[_PAINT_FINISH[paint]]
    if finish_key and finish_key in FINISHES:
        return FINISHES[finish_key]
    return FINISHES[default]


#: The bare masonry fabrics — a wall whose colour is the material's own rather than
#: something it wears. Exactly one row is here, because exactly one bare wall fabric
#: in this town has a colour anybody argued: `BRICK`, off the Petford watercolour. A
#: FRAMED or CLAD wall is deliberately absent — it wears a finish, and `wall_finish`
#: is the question for that one.
_BARE_WALL_FINISH: dict[str, Finish] = {
    "brick": BRICK,
}


def wall_colour(construction: str | None = None) -> Finish | None:
    """What colour a BARE wall of this construction is — or `None` where the sheet
    states no colour for that fabric, which the caller must then answer itself.

    This is §8.3's move made for the wall: T-0267 put the fort's brick wall onto the
    sheet by NAMING the row, and the row was called `chimney_brick`, so a wall was
    painted out of a constant named for a different surface (T-0332). Asked the
    question rather than told the answer, a wall cannot go on pointing at a row that
    has since moved — and the row can be renamed, as it just has been, without
    hunting the archetypes for the name.

    `None` rather than a fallback is the deliberate half. The sheet does not know
    what colour a stone or an earth wall is — no source in this repository states
    either, and no record in the dataset builds one (measured for T-0332) — and a
    selector that quietly dealt the nearest row would be inventing a colour under a
    reader that looks like it is asking the sheet. Saying nothing is the honest
    answer, and it leaves the value where its one holder can argue it.
    """
    if construction and construction in _BARE_WALL_FINISH:
        return _BARE_WALL_FINISH[construction]
    return None


def roof_finish(roof_condition: str | None = None) -> Finish:
    """What a roof wears. A WEATHERING CONDITION and never a covering — see the
    module docstring, and R-W2a finding 2, which this parcel does not discharge."""
    if roof_condition and roof_condition in ROOF_CONDITIONS:
        return ROOF_CONDITIONS[roof_condition]
    return ROOF_DEFAULT


def chimney_finish(stack: str) -> Finish:
    """What a stack is built of, given WHERE IT STANDS — `interior` or `exterior_gable`.

    The selector is the disposition and not the record, because no record in this
    dataset states a chimney fabric except the Sauganash's (`chimney_material`,
    T-0092, which `frame_tavern` still reads and folds into its confidence). What the
    two rows above argue is a rule about the two kinds of stack this town has, and
    each archetype already knows which kind it builds — `frame_dwelling` says its
    stack rises inside the wall and breaks the roof at the ridge, `log_dwelling` says
    its stack is built against the gable so it can be pulled away when it fires. Those
    two sentences were already committed; this turns them into two materials.

    Anything else takes brick: an interior stack is the town's majority and the
    better-evidenced of the two. `docs/RESEARCH/chimneys.md` is the whole argument.
    """
    return CHIMNEY_STICK_CLAY if stack == "exterior_gable" else BRICK


def resolve(substrate: Substrate, finish: Finish) -> tuple[tuple, float]:
    """The (rgba, roughness) pair an exporter needs: the substrate's gloss unless the
    finish is a coating that states its own (§2.1 — whitewash 0.90, lead paint 0.60,
    iron oxide 0.85)."""
    roughness = finish.roughness if finish.roughness is not None else substrate.roughness
    return finish.rgba, roughness


def trim_rgba(finish: Finish) -> tuple[float, float, float, float]:
    """Sawn trim against a sided wall.

    §2.3: "trim is derived from the wall paint and needs no sheet of its own", and
    the two rules below are the ones `frame_dwelling` has always argued. Over a
    COATING the boards took the same paint, so the trim is the wall lifted just
    enough to read as a separate board at walking distance. Over BARE TIMBER the trim
    is fresher stock than the weathered siding, so it is paler and slightly greyer —
    and the lift is the per-channel ratio the archetype already shipped
    (0.52/0.44/0.34 wall against 0.60/0.53/0.43 trim), which reproduces that pair
    exactly and generalises it to whichever finish the record deals.
    """
    r, g, b, a = finish.rgba
    if finish.coating:
        return (min(1.0, r * 1.06), min(1.0, g * 1.06), min(1.0, b * 1.06), a)
    return (min(1.0, r * (0.60 / 0.52)), min(1.0, g * (0.53 / 0.44)),
            min(1.0, b * (0.43 / 0.34)), a)
