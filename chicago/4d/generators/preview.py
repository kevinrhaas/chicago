"""Render a reference image of an archetype. Run inside Blender:

    blender -b -noaudio --factory-startup --python generators/preview.py -- [args]

    --archetype <name>   log_dwelling | bridge_timber | frame_tavern |
                         frame_dwelling | frame_storefront | outbuilding | all
    --out <dir>          output directory (default docs/RESEARCH)
    --samples <n>        Cycles samples (default 96)
    --width <px>         image width (default 1400)

Why this exists rather than a throwaway script: the committed reference images under
`docs/RESEARCH/archetype-*.png` are the only record of what the generators actually
produce, and an image nobody can regenerate is an image nobody can trust once the code
moves under it. Each archetype's GOLDEN cases below are also the closest thing the
generators have to a fixture — they are the documented buildings, spelled out as
parameters, and running this is the fastest way to find out that a change broke one.

**Cycles on the CPU, always.** EEVEE needs a GL context and dies with a libEGL error in
every headless sandbox this project runs in. Cycles is slower and correct, and a
reference render is not on anyone's inner loop.

The ground is a 1 m checker so heights can be read off the image. There are no figures
in it, per AGENTS.md — the checker is the scale reference instead.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from common.mesh import reset_scene  # noqa: E402
from archetypes import (  # noqa: E402
    bridge_timber, frame_dwelling, frame_storefront, frame_tavern, log_dwelling,
    outbuilding,
)
from archetypes.bridge_timber_params import BridgeTimberParams  # noqa: E402
from archetypes.frame_dwelling_params import FrameDwellingParams  # noqa: E402
from archetypes.frame_storefront_params import FrameStorefrontParams  # noqa: E402
from archetypes.frame_tavern_params import FrameTavernParams  # noqa: E402
from archetypes.log_dwelling_params import LogDwellingParams  # noqa: E402
from archetypes.outbuilding_params import OutbuildingParams  # noqa: E402

DOCUMENTED = "attested"
INFERRED = "reconstructed"
CONJ = "reconstructed"


# The documented buildings, written out as parameters. These are golden cases for
# looking at, not records — the records live in data/structures/ and carry the sources.
GOLDEN = {
    "log_dwelling": (log_dwelling.build, [
        # Wolf Point Tavern: log core plus a frame extension on the end ("partly log
        # and partly frame"), low, with the painted wolf sign hung outside by ~1833.
        ("wolf_point_tavern", LogDwellingParams(
            width_m=13.0, depth_m=7.0, stories=1, wall_height_m=2.55,
            loft=True, frame_addition=True, frame_addition_side="end",
            frame_addition_width_m=5.4, frame_addition_depth_m=6.2,
            frame_addition_stories=1, frame_paint="unpainted",
            sign="a painted wolf",
            confidence={"stories": INFERRED, "construction": DOCUMENTED,
                        "wall_height_m": CONJ, "roof_type": CONJ,
                        "frame_addition": DOCUMENTED,
                        "frame_addition_stories": CONJ,
                        "sign": DOCUMENTED, "loft": CONJ, "chimneys": INFERRED,
                        "footprint": CONJ})),
        # Samuel Miller's house: log cabin with a two-storey frame addition fronting
        # the river.
        ("miller_house", LogDwellingParams(
            width_m=9.5, depth_m=11.0, stories=1, wall_height_m=2.6,
            loft=True, frame_addition=True, frame_addition_side="front",
            frame_addition_width_m=9.5, frame_addition_depth_m=6.0,
            frame_addition_stories=2, frame_paint="unpainted",
            # Two: the record counts one stack per element, and the preview is
            # where the pair is looked at before the town is re-baked.
            chimneys=2,
            confidence={"stories": DOCUMENTED, "construction": DOCUMENTED,
                        "wall_height_m": CONJ, "roof_type": CONJ,
                        "frame_addition": DOCUMENTED,
                        "frame_addition_stories": DOCUMENTED,
                        "loft": CONJ, "chimneys": INFERRED, "footprint": CONJ})),
        # Walker's meeting house: "a small square log building, originally designed
        # for a school-house". The plain case.
        ("walker_meeting_house", LogDwellingParams(
            width_m=6.0, depth_m=6.0, stories=1, wall_height_m=2.45,
            # None, so the preview keeps exercising the degenerate case — the
            # archetype has to reduce to a bare cabin. The record says one.
            loft=False, chimneys=0,
            confidence={"stories": INFERRED, "construction": DOCUMENTED,
                        "wall_height_m": CONJ, "roof_type": CONJ,
                        "chimneys": INFERRED, "footprint": CONJ})),
    ]),
    # FIVE golden cases, not one, and that is the point of them. `outbuilding` is a
    # family spanning a privy to a livery stable, and a single golden case would only
    # ever prove the middle of that range — which is exactly where a set of proportions
    # tuned for one size looks fine and at both ends looks absurd. These five are chosen
    # to break in different places if the archetype regresses: the widest and the
    # narrowest footprint, all three constructions, both roof forms, an open-sided bay,
    # a wagon door and a person's door, and a wall gapped wide enough to be a crib.
    #
    # THE CONFIDENCES ARE HONEST AND THEY ARE BLEAK. Not one source reached by this
    # project describes the fabric, size, roof or material of ANY outbuilding at the
    # forks. What is documented is that these buildings existed — "the large stable and
    # the yard into which the trains were driven" behind the Western Hotel, a Wolf Point
    # 1831 county schedule pricing a horse kept overnight at 50 cents (NOT the "13 cents"
    # this comment used to quote, which was never in any source) — so the door is `inferred` where the traffic
    # through it is attested, and everything else is conjectural. A golden case that
    # marked any of this documented would be teaching the reference image to lie.
    "outbuilding": (outbuilding.build, [
        # A hotel stable of the kind the Western Hotel is recorded as having: big
        # enough for a team, a wagon door onto the yard, hay over the stalls. The
        # dimensions are the archetype's, not a source's.
        ("hotel_stable", OutbuildingParams(
            width_m=13.0, depth_m=7.0, construction="plank",
            roof_type="gable", door="wagon", door_side="front", loft=True,
            board_gap_m=0.022,
            confidence={"construction": CONJ, "roof_type": CONJ,
                        "wall_height_m": CONJ, "open_sides": CONJ,
                        "door": INFERRED, "loft": CONJ, "board_gap_m": CONJ,
                        "fenestration": CONJ, "footprint": CONJ})),
        # A wagon or hay shed: posts and a roof, open on the tall side so a loaded
        # wagon can be run under it. The case that proves the archetype is not a box
        # with a door in it.
        ("wagon_shed", OutbuildingParams(
            width_m=6.6, depth_m=4.0, construction="plank",
            roof_type="shed", open_sides=("front",), door="none",
            board_gap_m=0.025,
            confidence={"construction": CONJ, "roof_type": CONJ,
                        "wall_height_m": CONJ, "open_sides": CONJ,
                        "board_gap_m": CONJ, "footprint": CONJ})),
        # A corn crib: the same shed with its boards laid flat and spaced on purpose,
        # so the crop dries. One parameter is the whole difference, which is what the
        # family is meant to demonstrate. It stands on its sill at grade — a crib up on
        # blocks is a liberty this archetype does not take; see outbuilding_params.
        ("corn_crib", OutbuildingParams(
            width_m=4.2, depth_m=2.2, construction="light_frame",
            roof_type="shed", door="man", board_gap_m=0.09,
            confidence={"construction": CONJ, "roof_type": CONJ,
                        "wall_height_m": CONJ, "door": CONJ,
                        "board_gap_m": CONJ, "footprint": CONJ})),
        # A log smokehouse: the small end of the LOG branch, and the case that keeps
        # the log courses scaling with the building instead of a house's 0.34 m wall
        # log making a 2.6 m building out of seven courses.
        ("log_smokehouse", OutbuildingParams(
            width_m=3.0, depth_m=2.6, construction="log",
            roof_type="gable", door="man",
            confidence={"construction": CONJ, "roof_type": CONJ,
                        "wall_height_m": CONJ, "door": CONJ,
                        "fenestration": CONJ, "footprint": CONJ})),
        # A privy: the bottom of the range, and the case that catches every default
        # tuned for a stable. A fixed eave overhang turns this into a mushroom, a fixed
        # wall height into a tower, and a man's door will not fit its front wall
        # without being told the real dimensions.
        ("privy", OutbuildingParams(
            width_m=1.25, depth_m=1.25, construction="plank",
            roof_type="shed", door="man", door_width_m=0.72, door_height_m=1.78,
            board_gap_m=0.014,
            confidence={"construction": CONJ, "roof_type": CONJ,
                        "wall_height_m": CONJ, "door": CONJ,
                        "board_gap_m": CONJ, "footprint": CONJ})),
    ]),
    "bridge_timber": (bridge_timber.build, [
        # The North Branch bridge as the men who used it described it: the documented
        # 10 ft width and 6 ft clearance, on two bents of four heavy logs. Shortened
        # to a preview span, so the count is scaled with it — two bents over 17 m is
        # the same three-span composition the record builds over 71.83 m.
        ("north_branch_bridge", BridgeTimberParams(
            span_m=17.0, width_m=3.05, clearance_m=1.83, pier_count=2,
            pier_kind="bent",
            confidence={"construction": DOCUMENTED, "width_m": DOCUMENTED,
                        "clearance_m": DOCUMENTED, "pier_kind": DOCUMENTED,
                        "pier_count": DOCUMENTED, "deck_kind": DOCUMENTED,
                        "abutments": CONJ, "footprint": CONJ})),
        # The same crossing built on driven piles instead, and on the archetype's
        # fallback spacing rather than a count — the unattested case, kept so the
        # two readings of "log construction" can be compared side by side and so the
        # colonnade an undescribed bridge still gets stays visible in the previews.
        ("piles_variant", BridgeTimberParams(
            span_m=13.0, width_m=3.05, clearance_m=1.83,
            pier_kind="pile",
            confidence={"construction": DOCUMENTED, "width_m": DOCUMENTED,
                        "clearance_m": DOCUMENTED, "pier_kind": CONJ,
                        "pier_count": CONJ, "abutments": CONJ,
                        "footprint": CONJ})),
    ]),
    # Not this parcel's archetype. Kept because the only way to check that a new
    # archetype belongs to the same town as the existing one is to render them under
    # the same light — the log dwellings' palette was set against this. Transcribed
    # from data/structures/sauganash_hotel.json frame_1831 so it is not a second,
    # divergent statement of what that building was.
    "frame_tavern": (frame_tavern.build, [
        ("sauganash", FrameTavernParams(
            width_m=12.0, depth_m=8.0, stories=2, wall_height_m=5.5,
            roof_pitch_deg=38.0, construction="balloon_frame",
            paint="white", shutters="bright_blue", log_wing=True,
            confidence={"stories": DOCUMENTED, "construction": INFERRED,
                        "cladding": INFERRED, "paint": DOCUMENTED,
                        "shutters": DOCUMENTED, "roof_type": INFERRED,
                        "roof_pitch_deg": INFERRED, "wall_height_m": INFERRED,
                        "log_wing": INFERRED, "fenestration": INFERRED,
                        "chimneys": INFERRED, "footprint": CONJ})),
    ]),
    # ONE RECORD AND TWO FORMS. The first case is transcribed from
    # data/structures/peck_store.json frame_1833, so the reference image is not a
    # second, divergent statement of what that building was — the same rule the
    # Sauganash case above follows. The other two are FORMS the archetype exists to
    # cover and are named for what they are, not for buildings this project has no
    # evidence for.
    #
    # The pair is deliberate and it is the comparison a knowledgeable viewer wants:
    # the same 40 x 25 ft store on the same street, built the two ways it could have
    # been built in 1833. The braced frame shows a 6 in corner post and a girt line
    # at the second floor; the balloon frame shows a thin corner board and one
    # unbroken wall plane, because its studs run sill to plate in a single length.
    # That is what Chicago invented here, and on a finished elevation it is nearly
    # all of what can be seen of it. The third case is the exception: a building left
    # unfinished, where the studs stand open at their true 16 in centres over board
    # sheathing and the rhythm can actually be counted.
    "frame_storefront": (frame_storefront.build, [
        # Transcribed from data/structures/peck_store.json frame_1833 — SW corner of
        # South Water and LaSalle, "two-story frame" with an unfinished loft
        # (andreas_1884_v1). Everything the record does not state is the archetype's
        # default, which is exactly what the record will bake as.
        ("peck_store", FrameStorefrontParams(
            width_m=12.192, depth_m=7.62, stories=2, wall_height_m=5.5,
            roof_type="gable", roof_pitch_deg=38.0, construction="braced_frame",
            chimneys=1,
            confidence={"stories": DOCUMENTED, "construction": INFERRED,
                        "wall_height_m": INFERRED, "roof_type": INFERRED,
                        "roof_pitch_deg": INFERRED, "chimneys": INFERRED,
                        "fenestration": INFERRED, "footprint": CONJ})),
        # The same store as a balloon frame, with the parts a working store carried
        # that no Chicago record has yet described one by one: a rear ell, a loft, a
        # goods door on the loading gable and a board over the door. THE BOARD IS
        # BLANK — see docs/LIBERTIES.md L25 and the generator's _sign.
        ("balloon_shop", FrameStorefrontParams(
            width_m=12.192, depth_m=7.62, stories=2, wall_height_m=5.5,
            roof_type="gable", roof_pitch_deg=38.0, construction="balloon_frame",
            loft=True, chimneys=1, shopfront_bays=2,
            goods_door=True, goods_door_side="end",
            ell=True, ell_side="rear", ell_width_m=5.5, ell_depth_m=2.7,
            ell_stories=1, sign="the firm's name over the door",
            confidence={"stories": INFERRED, "construction": INFERRED,
                        "cladding": INFERRED, "loft": INFERRED, "sign": CONJ,
                        "shopfront": CONJ, "goods_door": CONJ, "ell": CONJ,
                        "roof_type": CONJ, "chimneys": CONJ,
                        "fenestration": INFERRED, "footprint": CONJ})),
        # A frame going up and not yet closed in — the state Andreas describes twice
        # on South Water Street in 1833. The loading gable is open, so this is the
        # one case where the 16 in stud centres and the 9 in sheathing boards are
        # visible rather than implied.
        ("unfinished_frame", FrameStorefrontParams(
            width_m=10.0, depth_m=7.0, stories=2, wall_height_m=5.2,
            roof_type="gable", roof_pitch_deg=36.0, construction="balloon_frame",
            framing_exposed=True, chimneys=1, shopfront_bays=2,
            goods_door=True, goods_door_side="end",
            confidence={"stories": CONJ, "construction": INFERRED,
                        "framing_exposed": CONJ, "shopfront": CONJ,
                        "goods_door": CONJ, "roof_type": CONJ, "chimneys": CONJ,
                        "footprint": CONJ})),
    ]),
    # THREE FORMS, NOT THREE BUILDINGS — and the difference is the honest part. Every
    # other archetype's golden cases are transcribed from a record: the Sauganash, Wolf
    # Point, Miller's house. No structure record uses `frame_dwelling` yet, so there is
    # nothing to transcribe, and inventing three named houses to look at would put
    # buildings in the reference image that this project has no evidence for. These are
    # the three FORMS the archetype exists to cover, dimensioned from the figures the
    # dossiers actually give about frame building at Chicago in these years — the Green
    # Tree's 7 1/2 ft ceilings and 12 ft rooms (chicagology_prefire127), St Mary's
    # 25 x 35 ft balloon frame of 1833 (andreas_1884_v1) — and named for what they are.
    #
    # THE CONFIDENCES ARE HONEST AND THEY CONTAIN NO `DOCUMENTED`. Nothing is documented
    # about a house that is not a record. `construction` is inferred because balloon
    # framing was the dominant local method by 1835, which is the same inference the
    # Western Hotel's record makes; the storey heights are inferred from the one attested
    # ceiling in the dataset; everything else is a guess and says so.
    "frame_dwelling": (frame_dwelling.build, [
        # THE CHARACTERISTIC CHICAGO HOUSE of these years, and the archetype's default
        # answer: a story and a half on a 30 x 20 ft front, chambers in the roof over a
        # 3 ft knee wall lit from the gable ends, a low kitchen ell running back, a
        # plank stoop at the door, unpainted, balloon-framed. The front is asymmetric
        # because the plan behind it is — hall and parlour, door in the middle of the
        # hall — which is the whole of this archetype's answer to LIBERTIES L23.
        ("story_and_a_half_ell", FrameDwellingParams(
            width_m=9.15, depth_m=11.0, stories=1.5, wall_height_m=3.6,
            knee_wall_m=0.95, roof_pitch_deg=42.0, construction="balloon_frame",
            plan="hall_parlour", porch="stoop", paint="unpainted", chimneys=2,
            ell=True, ell_width_m=4.27, ell_depth_m=4.9, ell_side="west",
            confidence={"stories": INFERRED, "construction": INFERRED,
                        "cladding": INFERRED, "wall_height_m": INFERRED,
                        "roof_type": INFERRED, "roof_pitch_deg": CONJ,
                        "knee_wall_m": CONJ, "plan": CONJ, "bays": CONJ,
                        "porch": CONJ, "ell": CONJ, "paint": CONJ,
                        "chimneys": CONJ, "fenestration": CONJ, "footprint": CONJ})),
        # THE SMALLEST CASE, kept so the archetype has to degrade to one room: an 18 x
        # 16 ft single pen, one storey, a door and one window, one stack, no porch and
        # no wing. Most of a boom town's houses were nearer this than the case above,
        # and an archetype that only looks right at its default size is a template.
        ("single_pen", FrameDwellingParams(
            width_m=5.49, depth_m=4.88, stories=1.0, wall_height_m=2.6,
            roof_pitch_deg=38.0, construction="balloon_frame",
            plan="single_pen", bays=2, porch=None, paint="unpainted", chimneys=1,
            confidence={"stories": INFERRED, "construction": INFERRED,
                        "cladding": INFERRED, "wall_height_m": INFERRED,
                        "roof_type": INFERRED, "roof_pitch_deg": CONJ,
                        "plan": CONJ, "bays": CONJ, "paint": CONJ,
                        "chimneys": CONJ, "fenestration": CONJ, "footprint": CONJ})),
        # THE OPPOSITE POLE, and it is in the set on purpose: two storeys, a centred
        # door with two windows either side, white paint, shutters, a roofed porch — a
        # regular front, which the archetype will build when a record asks for one and
        # never by default. Braced-framed, so the reference image also carries the girt
        # band at the upper floor and the wider corner boards that a braced frame shows
        # and a balloon frame does not. Compare its wall with the other two: that
        # difference IS `construction`, which no archetype here has built before.
        ("two_storey_braced", FrameDwellingParams(
            width_m=10.36, depth_m=6.71, stories=2.0, wall_height_m=4.9,
            roof_pitch_deg=38.0, construction="braced_frame",
            plan="centre_passage", bays=5, porch="roofed", paint="white",
            shutters="green", chimneys=2,
            confidence={"stories": INFERRED, "construction": INFERRED,
                        "cladding": INFERRED, "wall_height_m": INFERRED,
                        "roof_type": INFERRED, "roof_pitch_deg": CONJ,
                        "plan": CONJ, "bays": CONJ, "porch": CONJ,
                        "paint": CONJ, "shutters": CONJ, "chimneys": CONJ,
                        "fenestration": CONJ, "footprint": CONJ})),
    ]),
}


def argv_after_ddash() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


# Which axis the golden cases are spread along. Buildings go in a row across the
# frame; bridges go one behind the other, because two 17 m decks side by side make a
# group twelve times wider than it is tall and the camera has to back off until the
# bridges are threads.
STACK_AXIS = {"bridge_timber": "y"}

# How far apart the golden cases stand. 4.2 m suits three buildings of similar size;
# `outbuilding` puts five cases in a row spanning a 13 m stable down to a 1.25 m privy,
# and at 4.2 m the gaps are wider than three of the subjects and the camera backs off
# until the privy is a smudge. Closing them up is what keeps the small end legible.
GAP_M = {"outbuilding": 2.6}


def lay_out(archetype: str) -> list:
    """Build every golden case for an archetype, spread along x with a gap.

    Laid out in reverse because the camera stands on the +x side: screen-right is
    -x, so building the last case first puts the first case on the left of the image
    and the reading order matches the order in GOLDEN.
    """
    build_fn, cases = GOLDEN[archetype]
    axis = STACK_AXIS.get(archetype, "x")
    ai = 0 if axis == "x" else 1
    obs, cursor = [], 0.0
    gap = GAP_M.get(archetype, 4.2 if axis == "x" else 8.0)
    order = reversed(cases) if axis == "x" else cases
    for case_name, params in order:
        ob = build_fn(params, f"{archetype}__{case_name}")
        us = [v.co[ai] for v in ob.data.vertices]
        ob.location[ai] = cursor - min(us)
        obs.append(ob)
        cursor += (max(us) - min(us)) + gap
    for ob in obs:                                   # recentre the group on the origin
        ob.location[ai] -= (cursor - gap) / 2.0
    # `matrix_world` is depsgraph-derived, exactly like `bound_box`: without this it
    # still reads as the identity for objects placed on this tick, scene_bounds
    # measures one building instead of the row, and the camera lands inside it.
    bpy.context.view_layer.update()
    return obs


def scene_bounds(obs) -> tuple[Vector, Vector]:
    """From the vertices, not from `ob.bound_box` — bound_box is filled in by the
    depsgraph and reads as a zero-size box for an object created this tick, which
    silently parks the camera two metres from the origin."""
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for ob in obs:
        for v in ob.data.vertices:
            p = ob.matrix_world @ v.co
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
    return lo, hi


def ground(z: float) -> None:
    """A 1 m checker plane, so heights and widths can be read straight off the
    render. Muted earth tones — a grey checker reads as a studio backdrop and makes
    every log building look like a model kit."""
    me = bpy.data.meshes.new("ground")
    s = 400.0
    me.from_pydata([(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)], [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new("ground", me)
    bpy.context.scene.collection.objects.link(ob)

    mat = bpy.data.materials.new("ground")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    checker = nt.nodes.new("ShaderNodeTexChecker")
    checker.inputs["Color1"].default_value = (0.30, 0.28, 0.23, 1.0)
    checker.inputs["Color2"].default_value = (0.25, 0.24, 0.20, 1.0)
    checker.inputs["Scale"].default_value = 1.0      # one square per metre
    coord = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(coord.outputs["Object"], checker.inputs["Vector"])
    nt.links.new(checker.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    me.materials.append(mat)


def sky() -> None:
    world = bpy.data.worlds.new("sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.52, 0.60, 0.72, 1.0)
    bg.inputs["Strength"].default_value = 0.40


def sun() -> None:
    data = bpy.data.lights.new("sun", type="SUN")
    data.energy = 4.2
    data.angle = math.radians(2.5)          # a soft July edge, not a hard studio key
    data.color = (1.0, 0.95, 0.86)
    ob = bpy.data.objects.new("sun", data)
    bpy.context.scene.collection.objects.link(ob)
    # A LEGIBILITY RIG, not a solar position, and the distinction matters enough to
    # write down. Every documented feature these archetypes carry — the door, the
    # windows, the wolf sign — is on a facade that faces north by the contract's
    # rotation rule, and in Chicago the sun never shines on a north wall in the
    # middle of a July day. A physically-placed July sun therefore leaves the whole
    # subject of the reference image in shadow. So the key comes from the
    # east-north-east and high: the facade is grazed, the east return is fully lit,
    # and the roof reads brightest. Scene renders must not copy this.
    ob.rotation_euler = (math.radians(45), 0.0, math.radians(115))


def _dist(lo: Vector, hi: Vector) -> float:
    """Camera stand-off. Shared by camera(), the aspect calculation and the height
    cap, so the three cannot drift apart."""
    size = max((hi - lo).x, (hi - lo).y, (hi - lo).z * 2.4)
    return size * 1.35 + 7.0


def camera(lo: Vector, hi: Vector) -> None:
    """A three-quarter view from the north-east at standing height plus a little.

    North-east because the facade faces north by the contract's rotation rule, and
    a facade seen dead-on hides every piece of relief the archetype spends its
    triangles on.
    """
    centre = (lo + hi) / 2.0
    dist = _dist(lo, hi)

    data = bpy.data.cameras.new("cam")
    data.lens = 45.0
    ob = bpy.data.objects.new("cam", data)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob

    # Camera height is capped by the SUBJECT, not set by a fixed elevation angle. A
    # fixed angle ties the height to the horizontal distance, which is set by how wide
    # the row is — so a row of three cabins and a row of two bridges get the same 14 m
    # eye, and the bridges end up viewed from a hot-air balloon with their stringers
    # and their 6 ft clearance invisible under the deck. Taking the lesser of "a
    # normal three-quarter angle" and "one and a half times the subject's own height"
    # gives both a raised view of a building and a near-bank view of a bridge, at
    # roughly the same six degrees.
    az = math.radians(34)
    cam_z = lo.z + max(2.0, min(dist * 0.16, (hi.z - lo.z) * 1.5))
    ob.location = (centre.x + dist * math.sin(az),
                   centre.y + dist * math.cos(az),
                   cam_z)
    look = centre.copy()
    look.z = lo.z + (hi.z - lo.z) * 0.45
    direction = look - ob.location
    ob.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def frame_aspect(lo: Vector, hi: Vector, dist: float, lens: float) -> float:
    """Image height as a fraction of its width, chosen so the subject fills the frame.

    A fixed aspect suits one subject and starves the next: the same 0.58 that frames
    three cabins leaves a pair of low bridges as a thread across an empty sky, because
    the camera distance is set by how WIDE the group is and a bridge is all width. So
    the vertical field is derived — show about 2.6 times the subject's height — and
    clamped, since neither a square nor a letterbox slot is a useful reference image.
    """
    want = max(hi.z - lo.z, 1.0) * 2.2
    sensor_h = 2.0 * lens * (want / 2.0) / dist
    return min(0.62, max(0.30, sensor_h / 36.0))


def render(path: Path, samples: int, width: int, aspect: float = 0.58) -> None:
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"                 # EEVEE needs a GL context; see docstring
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x = width
    sc.render.resolution_y = int(width * aspect)
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    # Blender defaults PNG compression to 15%, which triples the size of a flat
    # render like this one for no visual gain. These images are committed.
    sc.render.image_settings.compression = 100
    sc.render.filepath = str(path)
    # Standard, not Filmic or AgX: this image exists to judge whether a hewn log
    # reads as brown and a chink line reads as pale, and a filmic curve desaturates
    # exactly the mid-tones the whole palette lives in.
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = -1.85
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def water(z: float = 0.0) -> None:
    """A dark water plane at the bridge's local z = 0.

    Not decoration. The only two numbers any source gives about these bridges are a
    width and a clearance ABOVE THE WATER, and a bridge photographed standing on a
    checkerboard field shows neither — the clearance becomes an arbitrary gap under a
    deck. With the water in, the reference image states the documented dimension.
    """
    me = bpy.data.meshes.new("water")
    s = 300.0
    me.from_pydata([(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)], [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new("water", me)
    bpy.context.scene.collection.objects.link(ob)
    mat = bpy.data.materials.new("water")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.105, 0.130, 0.118, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.42
    me.materials.append(mat)


def preview(archetype: str, outdir: Path, samples: int, width: int) -> int:
    reset_scene()
    obs = lay_out(archetype)
    lo, hi = scene_bounds(obs)
    if archetype == "bridge_timber":
        ground(lo.z - 0.45)          # riverbed, below the crib feet
        water(0.0)
    else:
        ground(lo.z)
    sky()
    sun()
    camera(lo, hi)
    tris = sum(sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in obs)
    for ob in obs:
        n = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        # The lowest vertex, printed because it is the cheapest possible cross-check on
        # an archetype's GROUND_CONTACT declaration. `perimeter` means the base of the
        # walls sits at local z = 0; anything else here is a building floating or
        # buried, which no amount of looking at a three-quarter render will show.
        z0 = min(v.co.z for v in ob.data.vertices)
        print(f"  {ob.name:<44} {n:>6} tris  {len(ob.data.materials)} materials  "
              f"min z {z0:+.3f}")
    print(f"  bounds {tuple(round(v, 2) for v in lo)} .. "
          f"{tuple(round(v, 2) for v in hi)}")
    out = outdir / f"archetype-{archetype}.png"
    render(out, samples, width, frame_aspect(lo, hi, _dist(lo, hi), 45.0))
    print(f"{archetype}: {tris} tris total -> {out}")
    return tris


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archetype", default="all")
    ap.add_argument("--out", default=str(ROOT / "docs" / "RESEARCH"))
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--width", type=int, default=1500)
    args = ap.parse_args(argv_after_ddash())

    names = list(GOLDEN) if args.archetype == "all" else [args.archetype]
    for name in names:
        if name not in GOLDEN:
            print(f"unknown archetype '{name}'; have {sorted(GOLDEN)}")
            return 2
        preview(name, Path(args.out), args.samples, args.width)
    return 0


if __name__ == "__main__":
    sys.exit(main())
