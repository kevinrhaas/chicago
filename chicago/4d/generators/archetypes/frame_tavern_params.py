"""Parameters for the frame_tavern archetype — pure Python, NO bpy import.

This module is imported by tools/check.sh on every commit to validate that every
structure record can actually be resolved into generator parameters. It must stay
importable in a bare Python 3.11 with no Blender, no numpy, nothing.

The split matters: parameter validation is a per-commit concern that has to run in
seconds in every agent sandbox, while mesh generation is a content-build concern
that runs on demand with a pinned Blender. Keeping the params here is what makes
that split possible.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Confidence values as they are written into the _CONFIDENCE glTF attribute.
# See docs/GLB-CONTRACT.md.
CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

ROOF_TYPES = ("gable", "hip", "shed", "gambrel")
CONSTRUCTIONS = ("balloon_frame", "braced_frame", "log", "brick", "timber_crib")

# The form attributes whose VALUE this archetype reads — the ones from_phase below
# turns into a parameter, and therefore the only ones a vertex position can depend
# on. An attribute outside this set contributes nothing the record says it should:
# the mesh either contains nothing of it or contains a fixed default in its place.
#
# Reading an attribute's CONFIDENCE is deliberately not membership. `fenestration`
# tints its geometry with the record's confidence while the shape itself is fixed
# by this module, and a tint is not a building — treating that as "consumed" would
# let the exact case this set exists to surface pass unremarked. `chimneys` was in
# that category until 2026-08-10 and is not any more: the count now decides how
# many stacks get built, so the value moves a vertex and the name belongs here.
#
# tools/validate.py holds every attribute outside it to a `geometry:` declaration
# on the record, so adding a parameter here without adding its name is a gate
# failure rather than a silently unbuilt attribute.
# `finish_key` and `roof_condition` are NOT in this set and must not be, although the
# archetype now reads both (T-0007). This set names FORM attributes — what a phase
# states about the building — and those two live in the record's `reconstruction`
# block, the 665-roof programme's own ledger, one level above the phase. That is why
# no archetype could read them for as long as `from_phase` took only a phase, and it
# is what `docs/RESEARCH/materials.md` §4 finding 4 was pointing at.
CONSUMED = frozenset({
    "stories", "wall_height_m", "roof_type", "roof_pitch_deg", "construction",
    "paint", "siding_exposure_m", "shutters", "gallery", "log_wing", "chimneys",
    "elevation_scheme", "chimney_placement", "side_entrance", "rear_ell",
    "shutter_type", "entrance_frontispiece", "front_opening_details", "front_lower_sash", "chimney_material", "roof_colour",
    "log_wing_door", "log_wing_porch_hood",
    "cross_wing", "cross_wing_depth_m", "cross_wing_end", "enclosed_left_annex",
    "upper_windows", "stovepipes", "rear_ell_door", "eaves_bays", "end_windows",
    "first_story_height_m", "entry_raise_m", "gable_lunette", "front_ground_layout",
    "flagstaff", "flagstaff_height_m", "gable_wall_cladding",
    "gable_arch_treatment", "corner_entry_surround", "gable_arch_text",
})

# How narrow a window bay may get before the piers between the sashes are not walls
# any more: a 0.85 m sash plus a 0.30 m pier. `upper_windows` is refused past it rather
# than squeezed, so a record asking for more chambers than its front can light is told
# so instead of drawn as a glazed strip (T-1778).
UPPER_BAY_MIN_M = 1.15

# The compass names a record may use for a wall-mounted feature, as bearings.
# Local face bearings follow from the placement's rotation_deg (the facade
# bearing): the +y face IS the facade, so +y carries rotation_deg itself and the
# other three walls follow at right angles.
_COMPASS_DEG = {"north": 0.0, "east": 90.0, "south": 180.0, "west": 270.0}

# Where this archetype touches the ground, read by tools/validate.py's ground
# contact check. `perimeter`: the whole footprint outline meets the terrain at
# local z = 0, which is what "y = 0 at the base of the walls" means in
# docs/GLB-CONTRACT.md. A building that says this and stands on ground its own
# outline does not reach is floating on one corner or buried at another.
GROUND_CONTACT = "perimeter"


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


@dataclass
class FrameTavernParams:
    """A two-storey frame tavern, optionally with an attached log wing.

    Dimensions are metres. Confidence keys mirror the record's attribute
    confidences and are what the generator paints into _CONFIDENCE.
    """

    # massing
    width_m: float
    depth_m: float
    stories: int
    wall_height_m: float
    roof_type: str = "gable"
    roof_pitch_deg: float = 38.0
    construction: str = "braced_frame"

    # Main-block end triangles continue the wall cladding (T-2376/T-2383).
    # False retains every legacy roof-material gable; no subsidiary roofs change.
    gable_wall_cladding: bool = field(default=False, kw_only=True)

    # appearance
    paint: str = "white"
    shutters: str | None = None
    # The leaf construction, when a view resolves it. None draws the solid leaf
    # the archetype has always drawn; "louvred" adds slat relief to each leaf —
    # the Sauganash's, read off the Trowbridge drawing alone (T-0092), so the
    # slats carry that attribute's own (weaker) confidence, not the colour's.
    shutter_type: str | None = None
    gallery: bool = False
    # A small flat-hooded surround on the facade's centred entrance — the
    # Sauganash's, drawn by both street views (T-0092). Frontage scheme only:
    # the gable_front scheme dresses its own doors. Sizes are the archetype's;
    # docs/LIBERTIES.md L154 owns them.
    entrance_frontispiece: bool = False
    front_opening_details: dict | None = field(default=None, kw_only=True)
    # Source-specific four lower facade sash; None retains every stock opening.
    front_lower_sash: dict | None = field(default=None, kw_only=True)
    # The clapboard's exposed face. 0.14 m (~5.5 in) is the archetype's own stock —
    # the one rhythm every frame building wore until T-0049 — and stays the default
    # for a record that carries no value. The deal that writes record values is
    # tools/deal_siding_stock.py and docs/LIBERTIES.md owns the invention.
    siding_exposure_m: float = 0.14

    # How many stacks stand on the block. The COUNT comes from the record; where
    # they stand and what they are made of do not — no source describes a stack on
    # any of these buildings — so the archetype spaces them across the frontage and
    # docs/LIBERTIES.md owns the arrangement. Two is the default because two is what
    # both surviving depictions of the Sauganash show.
    chimneys: int = 2

    # How the elevations are dressed. "frontage" is the archetype's original
    # scheme — bays across the two y faces, entrance centred on the facade —
    # read off the Sauganash depictions and still the default. "gable_front" is
    # the Green Tree's scheme, read off plate "11" of the 2026-08-11 reference
    # set (T-0083): the building fronts on a GABLE END, so the even bays run
    # along the two eaves elevations, the gable faces carry the doors and the
    # attic lights, and a second entrance may stand mid-eaves where a record
    # attests one. Requires depth_m > width_m so the ridge actually runs along
    # the deep axis and the facade is a gable end.
    # T-2385: "corner_gable" keeps the existing wide-axis ridge and dresses
    # its short x gables with three bays and its long y walls with five.
    # The two unseen elevations repeat the seen pair as reconstruction.
    elevation_scheme: str = "frontage"

    # T-2385: optional details for the corner-gable block. None/0/False keep
    # both original elevation schemes and the first corner proposal unchanged.
    first_story_height_m: float | None = field(default=None, kw_only=True)
    entry_raise_m: float = field(default=0.0, kw_only=True)
    gable_lunette: bool = field(default=False, kw_only=True)
    # A matte unresolved panel avoids asserting glazing where Gifford shows
    # lettering-like light marks. No text is invented or claimed legible.
    gable_arch_treatment: str = field(default="fanlight", kw_only=True)
    # Optional known-name reconstruction, never a source transcription.
    gable_arch_text: str = field(default="", kw_only=True)
    corner_entry_surround: bool = field(default=False, kw_only=True)
    flagstaff: bool = field(default=False, kw_only=True)
    flagstaff_height_m: float = field(default=4.25, kw_only=True)

    # What the stacks are made of, where a view says. None keeps the archetype's
    # roof-toned masses (the original treatment, kept exactly so no committed
    # building's stacks recolour); "brick" draws them in unpainted brick — the
    # Sauganash's, coloured by the Petford watercolour (T-0092).
    chimney_material: str | None = None

    # The roof's colour, where a view says. None keeps ROOF_RGBA (the archetype's
    # weathered-shingle grey, and every committed building's until T-0092);
    # "moss_green" is the Petford view's dark green/moss shingle tone.
    # "dark_brown" is a reconstructed stock-appearance proxy for monochrome
    # contrast, not source-attested pigment or actual weather-blackening.
    # "deep_brown" selects one quarter of that stock's linear RGB for the
    # reviewed Tremont contrast; it carries the same reconstruction requirement.
    roof_colour: str | None = None

    # Where the stacks stand. "frontage" is the original arrangement — spaced
    # across the frontage at the depth midline, the fractions read off the two
    # Sauganash depictions — kept as the default so no committed building moves.
    # "gable_ends" stands one stack ON the ridge line at each gable end, the
    # disposition plate "11" draws for the Green Tree. With this placement the
    # record's chimney count must be exactly 2.
    chimney_placement: str = "frontage"

    # The resolved LOCAL wall carrying an attested second entrance mid-eaves:
    # None, "x_min" or "x_max". Records state a compass direction
    # (side_entrance: "south"); from_phase resolves it against rotation_deg so
    # the record never has to know which local axis faces the street. Only read
    # by the gable_front scheme.
    side_entrance_face: str | None = None

    # A lower gabled tail off the REAR gable end — the Green Tree's low
    # addition, John Gray's testimony sized by the two retrospective views
    # (T-0083). Ridge continues the main axis at a lower eave; a wide carriage
    # door opens in its own (far) gable. All reconstructed; docs/LIBERTIES.md
    # owns the sizes.
    # Optional undated enclosed side-group reading. All metric layout is R;
    # None leaves every existing canonical/alternate geometry path unchanged.
    enclosed_left_annex: dict | None = field(default=None, kw_only=True)

    rear_ell: bool = False
    rear_ell_width_m: float = 5.5
    rear_ell_depth_m: float = 4.5
    rear_ell_wall_m: float = 2.6
    # What opens in the ell's far gable. "carriage" is the Green Tree's wide door to
    # the wagon yard, and stays the default so that building does not move.
    # "service" is a man-door — a kitchen wing's back door, which is what the
    # boarding house's rear service wing has where an inn has its yard (T-1778: the
    # crosswalk asks the H3 to "remove tavern cues", and a carriage door into the
    # kitchen is one).
    rear_ell_door: str = "carriage"

    # THE BOARDING HOUSE'S CHAMBER RHYTHM (T-1778). None keeps the five-bay
    # elevation every tavern has always had, on every storey. A count draws that
    # many evenly spaced sashes on each long elevation of the UPPER storeys only —
    # the ground floor keeps its five bays and its centred door. The count is the
    # record's, sized there from the house's beds; the spacing is this archetype's.
    upper_windows: int | None = None

    # A pictured gable-front eaves wall may state its own bay count (T-2376).
    # Sparse overrides: x_min/x_max only; a face not named retains the existing
    # footprint-derived count. This does not transfer one pictured elevation's
    # evidence to the unpictured opposite wall. A ground-floor side entrance
    # still replaces one of that face's bays, as before.
    eaves_bays: dict[str, int] = field(default_factory=dict, kw_only=True)

    # Ground floor of the +y gable only: door then two sash in local +u, at fractions
    # across its width. None preserves the legacy centred-door layout exactly.
    # Stations and stock sections remain reconstructed; this is not a survey.
    front_ground_layout: list[float] | None = field(default=None, kw_only=True)

    # Explicit sash on the MAIN gable ends of a frontage-scheme block (T-2383).
    # Each tuple is (end, at, z, width, height): end +x/-x, at a fraction of
    # depth from the rear, z the centre above grade, sizes in metres. Empty
    # preserves the old blank ends; cross-wing windows are separate geometry.
    end_windows: tuple = field(default=(), kw_only=True)

    # Sheet-iron stovepipes through the roof, beside the brick stacks. Positions and
    # heights are dealt here, deterministically by index, so a house with four reads
    # as four stoves and not as a row of identical posts; the count is the record's.
    # 0 draws none and is every committed building's value.
    stovepipes: int = 0

    # the attached log wing — the Sauganash's 1829 cabin surviving as a wing.
    # See docs/RESEARCH/sauganash_hotel.md.
    log_wing: bool = False
    # Sized from the depictions: a single-pen cabin occupying roughly the left
    # third of the frontage, not a barn. Both images show it clearly subordinate
    # to the frame block.
    log_wing_width_m: float = 5.0
    log_wing_depth_m: float = 4.0
    log_wing_height_m: float = 2.35
    # The wing's own door, direct to grade in its street face, and the
    # shed-roofed porch hood over it — the two halves of the Sauganash's wing
    # entry read off the 2026-08-18 brief's views (T-0092). Separate flags
    # because the evidence separates: two views draw the door, only the
    # engraving draws the hood. Leaf and hood sizes are the archetype's;
    # docs/LIBERTIES.md L154 owns them.
    log_wing_door: bool = False
    log_wing_porch_hood: bool = False

    # The SECOND TWO-STOREY MASS — the Sauganash's rear wing, off one gable end,
    # its ridge at right angles to the main block's and meeting it at a shared
    # apex. T-0626 read that apex off Braunhold's plate and it is what sizes this
    # wing: `tools/sauganash_apex_lines.py` shows both lines out of the drawn apex
    # are world-HORIZONTALS (1.35 and 0.11 deg), so they are two ridges and not a
    # ridge and a rake — and two gable ridges of one wall height and one pitch
    # meet at a point only if they span the same width.
    #
    # So the wing's SPAN IS NOT A PARAMETER: it is `depth_m`, the main block's own
    # depth, forced by the shared apex. Only how far the wing runs BACK is stated,
    # and that the plate cannot give (a single sheet gives no depth — T-0617 row
    # 11). docs/LIBERTIES.md owns that one number.
    cross_wing: bool = False
    cross_wing_depth_m: float = 8.0
    cross_wing_end: str = "x_max"

    # The finish the 665-roof programme dealt this building, and how weathered its
    # roof is. NOT form attributes — they live in the record's `reconstruction`
    # block, which is why `from_phase` takes the record — and until T-0007 they were
    # read by `generators/inferred_placeholder.py` alone, so a weathered roof and a
    # fresh one were the same pixel on every archetype building in the town
    # (docs/RESEARCH/materials.md §4 finding 4). None on every named or documented
    # building, which carries no reconstruction block and therefore keeps exactly the
    # colours it had. `common/materials.py` is what turns either into a surface.
    finish_key: str | None = None
    roof_condition: str | None = None
    # FIN-L (T-1962): how far one lap course may stand off the stock, and the seed its
    # lines are drawn from — `common/materials.py`'s `board_lay` and `course_lines`.
    # 0.0 on every record the fabric rule never reached, which keeps its even courses.
    siding_lay_m: float = 0.0
    siding_seed: str = ""

    # per-attribute confidence, keyed by the attribute name in the record
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        """The _CONFIDENCE float for one attribute."""
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the contract's rule for geometry driven by
        several attributes. A wall whose height is a guess is a guessed wall,
        even if we know it was white."""
        return max((self.conf(a) for a in attrs), default=1.0)

    @property
    def left_annex_parts(self) -> list[dict]:
        """Resolved component frames, occupied rings and door faces.

        The builder, compiler and physical readers share these exact frames.
        An open shoulder is occupied by the separate yard bay, not an invisible
        solid rectangle joining the main block to the enclosed connector.
        """
        g = self.enclosed_left_annex
        if g is None:
            return []
        parts = []
        x = self.width_m
        for name in ("shoulder", "connector", "boarding_range"):
            v = g[name]
            x1 = x + v["span_m"]
            front = self.depth_m - g["front_setback_m"] + v.get("front_set_out_m", 0.)
            back = front - v["depth_m"]
            angle = math.radians(v.get("plan_rotation_deg", 0.))
            cs, sn = math.cos(angle), math.sin(angle)

            def turn(u, vv):
                if not angle:
                    return [u, vv]
                return [x + (u-x)*cs - (vv-back)*sn,
                        back + (u-x)*sn + (vv-back)*cs]

            occupied = name != "shoulder" or g.get("shoulder_enclosed", True)
            part = {"id": name, "x0": x, "x1": x1, "back": back, "front": front,
                    "cos": cs, "sin": sn, "rotated": bool(angle),
                    "occupied": occupied,
                    "polygon": [turn(x, back), turn(x1, back),
                                turn(x1, front), turn(x, front)]}
            if name == "boarding_range":
                fraction, width, _height = v["front_door"]
                part["door_face"] = {
                    "face": "annex_boarding_range", "origin": turn(x, front),
                    "along": [cs, sn], "outward": [-sn, cs], "u0": 0.,
                    "u1": v["span_m"], "openings": [{"kind": "door",
                        "u0": fraction*v["span_m"]-width/2,
                        "u1": fraction*v["span_m"]+width/2}]}
            parts.append(part)
            x = x1
        return parts

    def validate(self) -> None:
        if self.enclosed_left_annex is not None:
            _validate_enclosed_left_annex(self)
        if not 2.0 <= self.width_m <= 80.0:
            raise ParamError(f"width_m {self.width_m} outside plausible range 2-80 m")
        if not 2.0 <= self.depth_m <= 60.0:
            raise ParamError(f"depth_m {self.depth_m} outside plausible range 2-60 m")
        if self.stories not in (1, 2, 3):
            raise ParamError(f"stories {self.stories} not in 1..3 "
                             f"(no building in 1835 Chicago exceeded three)")
        if not 1.8 <= self.wall_height_m <= 14.0:
            raise ParamError(f"wall_height_m {self.wall_height_m} outside 1.8-14 m")
        if not 0.10 <= self.siding_exposure_m <= 0.16:
            raise ParamError(f"siding_exposure_m {self.siding_exposure_m} outside "
                             f"0.10-0.16 m (~4-6.3 in): not a period clapboard exposure")
        if not 0.0 <= self.siding_lay_m <= 0.010:
            raise ParamError(f"siding_lay_m {self.siding_lay_m} outside 0-0.010 m: a lay "
                             f"that wide would climb a course over its 0.018 m lip")
        if not isinstance(self.gable_wall_cladding, bool):
            raise ParamError("gable_wall_cladding must be a boolean")
        if self.gable_wall_cladding and self.roof_type != "gable":
            raise ParamError("gable_wall_cladding requires a gable roof")
        if self.roof_type not in ROOF_TYPES:
            raise ParamError(f"roof_type '{self.roof_type}' not in {ROOF_TYPES}")
        if not 10.0 <= self.roof_pitch_deg <= 60.0:
            raise ParamError(f"roof_pitch_deg {self.roof_pitch_deg} outside 10-60 deg")
        if self.construction not in CONSTRUCTIONS:
            raise ParamError(f"construction '{self.construction}' not in {CONSTRUCTIONS}")
        # 0 is allowed and is a claim, not an absence: a record saying a building
        # had no stack gets a building with no stack. The ceiling is the number the
        # frontage can space without the stacks touching.
        if not isinstance(self.chimneys, int) or isinstance(self.chimneys, bool):
            raise ParamError(f"chimneys {self.chimneys!r} is not a whole number — the "
                             f"record states a count, not whether there was one")
        if not 0 <= self.chimneys <= 4:
            raise ParamError(f"chimneys {self.chimneys} outside 0..4; a frame block of "
                             f"these proportions cannot carry more, and a record that "
                             f"means it should say where they stood")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")
        if self.front_lower_sash is not None:
            _validate_front_lower_sash(self)
        if self.front_opening_details is not None:
            _validate_front_opening_details(self)
        if self.elevation_scheme not in ("frontage", "gable_front", "corner_gable"):
            raise ParamError(f"elevation_scheme '{self.elevation_scheme}' not in "
                             f"('frontage', 'gable_front', 'corner_gable')")
        if self.chimney_placement not in ("frontage", "gable_ends", "slope_offsets"):
            raise ParamError(f"chimney_placement '{self.chimney_placement}' not in "
                             f"('frontage', 'gable_ends', 'slope_offsets')")
        if self.elevation_scheme == "gable_front":
            if self.depth_m <= self.width_m:
                raise ParamError(
                    f"elevation_scheme 'gable_front' on a footprint {self.width_m} x "
                    f"{self.depth_m} m: the scheme means the building fronts on a gable "
                    f"end, which needs the ridge along the deep axis (depth > width)")
            if self.shutters:
                raise ParamError("elevation_scheme 'gable_front' draws no shutters — "
                                 "no record needs both yet, and drawing them wrong "
                                 "would be worse than refusing")
        if self.elevation_scheme == "corner_gable":
            if self.width_m <= self.depth_m:
                raise ParamError("corner_gable needs width > depth: its short gables "
                                 "are the x faces, with the ridge along the wide axis")
            if self.roof_type != "gable":
                raise ParamError("corner_gable needs a gable roof")
            if self.wall_height_m / self.stories < 2.25:
                raise ParamError("corner_gable needs at least 2.25 m per storey "
                                 "for its existing window/entrance kit")
            # Existing 0.85 m sash, casing and two 0.357 m open shutter leaves.
            # Reject a bay that would overlap the next instead of shrinking it.
            bay_min = 1.95 if self.shutters else UPPER_BAY_MIN_M
            if self.width_m / 5 < bay_min or self.depth_m / 3 < bay_min:
                raise ParamError("corner_gable's five/three-bay elevations are too "
                                 f"narrow for their openings (minimum bay {bay_min} m)")
            if self.shutter_type is not None:
                raise ParamError("corner_gable supplies plain shutter leaves; a "
                                 "particular louvre pattern is not resolved")
            if self.rear_ell or self.log_wing or self.gallery:
                raise ParamError("corner_gable does not resolve attached wings or "
                                 "a gallery; do not silently add those to its faces")
        if self.chimney_placement == "slope_offsets":
            if self.elevation_scheme != "corner_gable" or self.chimneys != 4:
                raise ParamError("slope_offsets is the corner-gable four-stack "
                                 "layout, not an alias for the old ridge stacks")
        for label, value in (("gable_lunette", self.gable_lunette),
                             ("flagstaff", self.flagstaff),
                             ("corner_entry_surround", self.corner_entry_surround)):
            if type(value) is not bool:
                raise ParamError(f"{label} must be boolean")
        for label, value in (("entry_raise_m", self.entry_raise_m),
                             ("flagstaff_height_m", self.flagstaff_height_m)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ParamError(f"{label} must be a finite number")
        if not 0.0 <= self.entry_raise_m <= 1.2:
            raise ParamError("entry_raise_m outside 0..1.2 m")
        if not 0.5 <= self.flagstaff_height_m <= 8.0:
            raise ParamError("flagstaff_height_m outside 0.5..8 m")
        if self.first_story_height_m is not None:
            height = self.first_story_height_m
            if isinstance(height, bool) or not isinstance(height, (int, float)) or not math.isfinite(height):
                raise ParamError("first_story_height_m must be a finite number")
            if self.stories < 2 or not 2.25 <= height <= self.wall_height_m - 2.25 * (self.stories - 1):
                raise ParamError("first_story_height_m must leave at least 2.25 m "
                                 "for each upper storey")
        if self.gable_arch_treatment not in ("fanlight", "opaque_panel"):
            raise ParamError("gable_arch_treatment must be fanlight or opaque_panel")
        if self.gable_arch_treatment != "fanlight" and not self.gable_lunette:
            raise ParamError("opaque arch treatment needs a gable_lunette outline")
        if not isinstance(self.gable_arch_text, str) or self.gable_arch_text not in ("", "TREMONT"):
            raise ParamError("gable_arch_text supports only empty or reconstructed TREMONT")
        if self.gable_arch_text:
            if (self.elevation_scheme != "corner_gable" or not self.gable_lunette
                    or self.gable_arch_treatment != "opaque_panel"):
                raise ParamError("gable_arch_text needs the opaque corner-gable panel")
            if self.confidence.get("gable_arch_text", "reconstructed") != "reconstructed":
                raise ParamError("gable_arch_text is a conscious reconstruction, not a transcription")
            inner_half = self.depth_m * .20 - .09
            text_half = self.depth_m * (2.68 / 9.14) / 2
            if inner_half <= text_half:
                raise ParamError("gable_arch_text is wider than the inner arch")
            top = .64 + .56 * math.sqrt(1 - (text_half / inner_half) ** 2)
            if top < .65 + .32 + .005:
                raise ParamError("gable_arch_text breaks the inner arch outline")
        detailed = (self.first_story_height_m is not None or self.entry_raise_m > 0
                    or self.gable_lunette or self.flagstaff or self.corner_entry_surround)
        if detailed and self.elevation_scheme != "corner_gable":
            raise ParamError("corner details need the corner_gable elevation scheme")
        if self.gable_lunette:
            rise = (self.depth_m / 2 + 0.25) * math.tan(math.radians(self.roof_pitch_deg))
            if rise < 0.55 + 0.74 + 0.15:
                raise ParamError("gable_lunette needs room below the ridge for "
                                 "its reconstructed arch and surround")
        first_height = self.first_story_height_m or self.wall_height_m / self.stories
        if self.entry_raise_m and self.entry_raise_m + 2.1 + 0.15 > first_height:
            raise ParamError("raised entrance and its head need 0.15 m below the "
                             "first-floor structure")
        if self.chimney_placement == "gable_ends" and self.chimneys != 2:
            raise ParamError(f"chimney_placement 'gable_ends' stands one stack at each "
                             f"gable end, so the count must be 2, not {self.chimneys}")
        if self.side_entrance_face not in (None, "x_min", "x_max"):
            raise ParamError(f"side_entrance_face '{self.side_entrance_face}' not in "
                             f"(None, 'x_min', 'x_max')")
        if self.side_entrance_face and self.elevation_scheme != "gable_front":
            raise ParamError("side_entrance is only read by the gable_front scheme — "
                             "on the frontage scheme it would silently build nothing")
        if self.rear_ell:
            if self.rear_ell_width_m > self.width_m:
                raise ParamError("rear ell is wider than the block it attaches to")
            if not 1.8 <= self.rear_ell_wall_m < self.wall_height_m:
                raise ParamError(f"rear_ell_wall_m {self.rear_ell_wall_m} must sit in "
                                 f"1.8 m..the main wall height — the ell is the LOW "
                                 f"addition or it is not this ell")
        if self.rear_ell_door not in ("carriage", "service"):
            raise ParamError(f"rear_ell_door '{self.rear_ell_door}' not in "
                             f"('carriage', 'service')")
        if self.rear_ell_door != "carriage" and not self.rear_ell:
            raise ParamError("rear_ell_door without rear_ell — a door needs a wing "
                             "to open out of")
        if self.upper_windows is not None:
            if (not isinstance(self.upper_windows, int)
                    or isinstance(self.upper_windows, bool)):
                raise ParamError(f"upper_windows {self.upper_windows!r} is not a "
                                 f"whole number of sashes")
            if self.stories < 2:
                raise ParamError("upper_windows on a one-storey block — there is no "
                                 "upper storey for the rhythm to stand on")
            if self.elevation_scheme != "frontage":
                raise ParamError("upper_windows is read by the frontage scheme only")
            if not 3 <= self.upper_windows <= 12:
                raise ParamError(f"upper_windows {self.upper_windows} outside 3..12")
            if self.width_m / self.upper_windows < UPPER_BAY_MIN_M:
                raise ParamError(
                    f"upper_windows {self.upper_windows} on a {self.width_m} m front "
                    f"leaves {self.width_m / self.upper_windows:.2f} m a bay, under "
                    f"the {UPPER_BAY_MIN_M} m a sash and its pier need")
        if not isinstance(self.eaves_bays, dict):
            raise ParamError("eaves_bays must map x_min/x_max faces to whole bay counts")
        if self.eaves_bays and self.elevation_scheme != "gable_front":
            raise ParamError("eaves_bays is read by the gable_front scheme only")
        for face, bays in self.eaves_bays.items():
            if face not in ("x_min", "x_max"):
                raise ParamError(f"eaves_bays face {face!r} is not x_min or x_max")
            if (not isinstance(bays, int) or isinstance(bays, bool)
                    or not 3 <= bays <= 12):
                raise ParamError(f"eaves_bays[{face!r}] {bays!r} is not a count in 3..12")
            if self.depth_m / bays < UPPER_BAY_MIN_M:
                raise ParamError(
                    f"eaves_bays[{face!r}] {bays} on a {self.depth_m} m wall "
                    f"leaves {self.depth_m / bays:.2f} m a bay, under "
                    f"the {UPPER_BAY_MIN_M} m a sash and its pier need")
        if self.front_ground_layout is not None:
            stations = self.front_ground_layout
            if self.conf("front_ground_layout") != 1.0:
                raise ParamError("front_ground_layout metrics must remain reconstructed")
            if self.elevation_scheme != "gable_front":
                raise ParamError("front_ground_layout needs the gable_front scheme")
            if not isinstance(stations, list) or len(stations) != 3:
                raise ParamError("front_ground_layout needs three local fractions: door, sash, sash")
            if any(isinstance(v, bool) or not isinstance(v, (int, float))
                   or not math.isfinite(v) for v in stations):
                raise ParamError("front_ground_layout stations must be finite numbers")
            if not stations[0] < stations[1] < stations[2]:
                raise ParamError("front_ground_layout must order low-u door before the two local-u sash")
            # Existing opening widths, plus at least .15 m to a corner and
            # .30 m between openings. Never shrink a kit to fit a bad layout.
            spans = [(at * self.width_m - width / 2,
                      at * self.width_m + width / 2)
                     for at, width in zip(stations, (1.20, .85, .85))]
            if spans[0][0] < .15 or spans[-1][1] > self.width_m - .15:
                raise ParamError("front_ground_layout reaches a wall corner")
            if any(right[0] - left[1] < .30 for left, right in zip(spans, spans[1:])):
                raise ParamError("front_ground_layout overlaps openings or leaves too little pier")
            if self.wall_height_m / self.stories < 2.25:
                raise ParamError("front_ground_layout needs the stock 2.1 m door below its storey")
        if self.end_windows:
            if self.elevation_scheme != "frontage" or self.roof_type != "gable" or self.width_m < self.depth_m:
                raise ParamError("end_windows needs a frontage block with gables at its x ends")
            for end, at, z, width, height in self.end_windows:
                if end not in ("+x", "-x"):
                    raise ParamError(f"end_windows end {end!r} not in (+x, -x)")
                if not all(math.isfinite(v) for v in (at, z, width, height)):
                    raise ParamError("end_windows dimensions and stations must be finite")
                if not 0.05 <= at <= 0.95 or not 0.3 <= width <= 1.4 or not 0.3 <= height <= 1.8:
                    raise ParamError("end_windows station/size outside supported bounds")
                lo, hi = z - height / 2, z + height / 2
                u0, u1 = at * self.depth_m - width / 2, at * self.depth_m + width / 2
                if lo < 0.15 or u0 < 0.15 or u1 > self.depth_m - 0.15:
                    raise ParamError("end_windows reaches a wall corner or the ground")
                if lo < self.wall_height_m < hi:
                    raise ParamError("end_windows crosses the eave: state a wall or attic sash")
                if lo >= self.wall_height_m:
                    # Same 0.25 m eave overhang as the committed roof builder.
                    run = min(u0 + 0.25, self.depth_m + 0.25 - u1)
                    ceiling = self.wall_height_m + run * math.tan(math.radians(self.roof_pitch_deg))
                    if hi > ceiling - 0.10:
                        raise ParamError("end_windows attic sash breaks the roof silhouette")
        if (not isinstance(self.stovepipes, int) or isinstance(self.stovepipes, bool)
                or not 0 <= self.stovepipes <= 6):
            raise ParamError(f"stovepipes {self.stovepipes!r} not a count in 0..6")
        if self.stovepipes and self.roof_type != "gable":
            raise ParamError("stovepipes are set on a gable's two slopes; this roof "
                             f"is '{self.roof_type}'")
        if self.log_wing:
            if self.log_wing_width_m > self.width_m:
                raise ParamError("log wing is wider than the block it attaches to")
            if not 1.8 <= self.log_wing_height_m <= 4.0:
                raise ParamError(f"log_wing_height_m {self.log_wing_height_m} outside 1.8-4 m")
        if self.shutter_type not in (None, "louvred"):
            raise ParamError(f"shutter_type '{self.shutter_type}' not in (None, 'louvred')")
        if self.shutter_type and not self.shutters:
            raise ParamError("shutter_type without shutters — a slat needs a leaf to "
                             "sit in, and a record that means louvres should state "
                             "the shutters they are cut into")
        if self.entrance_frontispiece and self.elevation_scheme != "frontage":
            raise ParamError("entrance_frontispiece dresses the frontage scheme's "
                             "centred facade door — the gable_front scheme carries "
                             "its own door treatment, and drawing both would be a "
                             "building no view shows")
        if self.chimney_material not in (None, "brick"):
            raise ParamError(f"chimney_material '{self.chimney_material}' not in "
                             f"(None, 'brick')")
        if self.roof_colour not in (None, "moss_green", "dark_brown", "deep_brown"):
            raise ParamError(f"roof_colour '{self.roof_colour}' not in "
                             f"(None, 'moss_green', 'dark_brown', 'deep_brown')")
        if self.roof_colour in ("dark_brown", "deep_brown") and self.conf("roof_colour") != 1.0:
            raise ParamError("dark_brown/deep_brown roof_colour is an explicitly reconstructed "
                             "stock tonal proxy, not an attested pigment/weather history")
        if self.log_wing_door and not self.log_wing:
            raise ParamError("log_wing_door without log_wing — a door needs a wing "
                             "to open into")
        if self.cross_wing:
            if self.cross_wing_end not in ("x_min", "x_max"):
                raise ParamError(f"cross_wing_end '{self.cross_wing_end}' not in "
                                 f"('x_min', 'x_max') — the wing stands at one gable "
                                 f"end of the block or it is not this wing")
            if self.roof_type != "gable":
                raise ParamError("cross_wing carries its own gable and meets the main "
                                 "ridge at a shared apex, which needs a gable on the "
                                 f"main block; this one is '{self.roof_type}'")
            if self.elevation_scheme != "frontage":
                raise ParamError("cross_wing is read by the frontage scheme only — the "
                                 "gable_front scheme's ridge already runs on the deep "
                                 "axis, so a wing at right angles to it would be a "
                                 "building no view shows")
            if self.depth_m > self.width_m:
                raise ParamError(
                    f"cross_wing spans the main block's own depth ({self.depth_m} m) "
                    f"across a {self.width_m} m frontage: the wing would be wider than "
                    f"the block it stands on. The shared apex forces the span, so a "
                    f"record needing a narrower wing is asking for two ridge heights.")
            if not 3.0 <= self.cross_wing_depth_m <= 30.0:
                raise ParamError(f"cross_wing_depth_m {self.cross_wing_depth_m} outside "
                                 f"3-30 m")
        if self.log_wing_porch_hood and not self.log_wing_door:
            raise ParamError("log_wing_porch_hood without log_wing_door — the hood "
                             "the engraving draws stands over the wing's door, and "
                             "a hood over blank logs is a claim no view makes")



    @property
    def resolved_front_ground_stations(self) -> tuple[float, tuple[float, float]]:
        """Actual local-u centres consumed by mesh and native primary access.

        Existing mesh_inputs hashes all dataclass property VALUES. Keeping the
        geometry arithmetic here makes a station change a real recipe change;
        this is not a hash-only proxy. No plain params helper can move the mesh.
        Exterior +y reverses screen order, so low-u door precedes the local sash.
        Default door applies to all tavern schemes; sash only to gable_front.
        """
        if self.front_ground_layout is None:
            return self.width_m / 2, (self.width_m * .22, self.width_m * .78)
        door, sash_a, sash_b = self.front_ground_layout
        return self.width_m * door, (self.width_m * sash_a, self.width_m * sash_b)


def _validate_front_lower_sash(p: FrameTavernParams) -> None:
    """Only the four lower front sash; never a change to rear or upper openings."""
    g = p.front_lower_sash
    if not isinstance(g, dict) or set(g) != {"width_m", "height_m", "sill_m"}:
        raise ParamError("front_lower_sash needs width_m, height_m and sill_m")
    if p.elevation_scheme != "frontage" or p.stories != 2 or p.gallery:
        raise ParamError("front_lower_sash needs a two-storey frontage without a gallery")
    if p.confidence.get("front_lower_sash", "reconstructed") != "reconstructed":
        raise ParamError("front_lower_sash numeric sections must remain reconstructed")
    for key, lo, hi in [("width_m", .45, 1.2), ("height_m", 1.4, 2.6), ("sill_m", .35, 1.4)]:
        value = g[key]
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not lo <= value <= hi):
            raise ParamError(f"front_lower_sash {key} needs a finite number in {lo}..{hi}")
    if g["sill_m"] + g["height_m"] > p.wall_height_m / p.stories + .05:
        raise ParamError("front_lower_sash head must remain below its storey division")
    reach = g["width_m"] / 2 + .090 + .01 + (g["width_m"] * .42 if p.shutters else 0.)
    if 2 * reach + .02 >= p.width_m / 5:
        raise ParamError("front_lower_sash and shutters overlap the neighbouring bay")


def _validate_front_opening_details(p: FrameTavernParams) -> None:
    """A bounded frontage-only entrance; never an unsupported interior claim."""
    g = p.front_opening_details
    keys = {"kind", "case_width_m", "jamb_outer_width_m", "leaf_width_m",
            "leaf_head_m", "transom_top_m", "cornice_top_m",
            "sidelights_each_width_m"}
    if not isinstance(g, dict) or set(g) != keys:
        raise ParamError("front_opening_details needs exactly the bounded entrance fields")
    if g["kind"] != "blind_dark_recess":
        raise ParamError("front_opening_details supports only a blind dark recess")
    if (p.elevation_scheme != "frontage" or not p.entrance_frontispiece
            or p.stories != 2 or p.gallery):
        raise ParamError("front_opening_details needs a two-storey frontage with an entrance frontispiece")
    if p.confidence.get("front_opening_details", "reconstructed") != "reconstructed":
        raise ParamError("front_opening_details numeric sections must remain reconstructed")
    bounds = {"case_width_m": (2., 3.2), "jamb_outer_width_m": (1.7, 2.4),
              "leaf_width_m": (.7, 1.2), "leaf_head_m": (2.1, 2.7),
              "transom_top_m": (2.6, 3.3), "cornice_top_m": (2.8, 3.5),
              "sidelights_each_width_m": (.2, .45)}
    for key, (lo, hi) in bounds.items():
        value = g[key]
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not lo <= value <= hi):
            raise ParamError(f"front_opening_details {key} needs a finite number in {lo}..{hi}")
    if not (g["leaf_head_m"] + .3 <= g["transom_top_m"]
            and g["transom_top_m"] + .12 <= g["cornice_top_m"]
            and g["cornice_top_m"] <= p.wall_height_m - 1.4):
        raise ParamError("front_opening_details head, transom and crown must stay ordered below the upper row")
    if (g["case_width_m"] < g["jamb_outer_width_m"] + .3
            or g["leaf_width_m"] + 2 * g["sidelights_each_width_m"] + .4 > g["jamb_outer_width_m"]):
        raise ParamError("front_opening_details lights, leaf and jambs overlap")
    # Check against the actual selected front sash and its open leaves.
    sash_width = p.front_lower_sash["width_m"] if p.front_lower_sash else .85
    neighbour_reach = sash_width / 2 + .090 + .01 + (sash_width * .42 if p.shutters else 0.)
    if g["jamb_outer_width_m"] / 2 + neighbour_reach + .02 > p.width_m / 5:
        raise ParamError("front_opening_details jambs overlap the neighbouring lower sash/shutters")


def _board_lay(recon: dict) -> float:
    """The fabric rule's lay for this roof (FIN-L), from the material sheet."""
    from common.materials import board_lay  # noqa: E402 — generators/ is on the path
    return board_lay(recon)

def from_phase(phase: dict, record: dict | None = None) -> FrameTavernParams:
    """Resolve one structure phase into generator parameters.

    Reads only the attested `value` of each form attribute plus its confidence.
    Footprint dimensions come from the phase footprint polygon's bounding box —
    the polygon is authoritative, the width/depth are derived.
    """
    form = phase.get("form", {})

    def val(attr, default=None):
        a = form.get(attr)
        return default if a is None else a.get("value", default)

    def measure(attr, default=None):
        raw = val(attr, default)
        if raw is None:
            return None
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            raise ParamError(f"{attr} must be a finite number")
        return float(raw)

    def conf(attr, default="reconstructed"):
        a = form.get(attr)
        return default if a is None else a.get("confidence", default)

    poly = phase.get("footprint", {}).get("polygon") or []
    if len(poly) < 3:
        raise ParamError("footprint polygon needs at least 3 points")
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    width, depth = max(xs) - min(xs), max(ys) - min(ys)

    # The contract pins the mesh origin to polygon coordinate (0, 0). Deriving
    # only a bounding-box SIZE and then building from the origin silently
    # translates any polygon not anchored there, so the building would stand
    # somewhere its own footprint does not describe. Refuse instead: a footprint
    # that needs an offset is asking for something this archetype does not model.
    if abs(min(xs)) > 1e-6 or abs(min(ys)) > 1e-6:
        raise ParamError(
            f"footprint polygon starts at ({min(xs)}, {min(ys)}), not the origin. "
            f"docs/GLB-CONTRACT.md pins the mesh origin to polygon coordinate (0, 0); "
            f"building from a bounding box would silently move the structure "
            f"{max(abs(min(xs)), abs(min(ys))):.2f} m from where its footprint puts it. "
            f"Re-anchor the polygon at the origin and put the offset in position.")

    # `reconstruction` is the 665-roof programme's own block: it is present on every
    # anonymous or household roof it dealt and absent from every named building.
    recon = (record or {}).get("reconstruction") or {}
    confidences = {a: conf(a) for a in form}
    confidences["footprint"] = phase.get("footprint", {}).get("confidence", "reconstructed")

    # A side entrance is stated as a compass direction; the local wall it lands
    # on follows from the facade bearing. Only the four cardinal walls exist,
    # and a direction that names the facade or the rear names no side wall.
    side_face = None
    side = val("side_entrance")
    if side is not None:
        rot = float((phase.get("position") or {}).get("rotation_deg") or 0.0)
        want = _COMPASS_DEG.get(str(side))
        if want is None:
            raise ParamError(f"side_entrance '{side}' is not a compass direction "
                             f"(north/east/south/west)")
        faces = {"x_max": (rot + 90.0) % 360.0, "x_min": (rot + 270.0) % 360.0}
        matches = [f for f, b in faces.items() if abs((b - want + 180) % 360 - 180) < 45.0]
        if not matches:
            raise ParamError(f"side_entrance '{side}' does not name an eaves-side wall "
                             f"of a building whose facade bears {rot} deg")
        side_face = matches[0]

    p = FrameTavernParams(
        width_m=round(width, 3),
        depth_m=round(depth, 3),
        stories=int(val("stories", 2)),
        wall_height_m=float(val("wall_height_m", 5.5)),
        roof_type=str(val("roof_type", "gable")),
        roof_pitch_deg=float(val("roof_pitch_deg", 38.0)),
        construction=str(val("construction", "braced_frame")),
        paint=str(val("paint", "unpainted")),
        gable_wall_cladding=val("gable_wall_cladding", False),
        siding_exposure_m=float(val("siding_exposure_m", 0.14)),
        shutters=val("shutters"),
        shutter_type=val("shutter_type"),
        gallery=bool(val("gallery", False)),
        entrance_frontispiece=bool(val("entrance_frontispiece", False)),
        front_opening_details=val("front_opening_details"),
        front_lower_sash=val("front_lower_sash"),
        log_wing=bool(val("log_wing", False)),
        log_wing_door=bool(val("log_wing_door", False)),
        log_wing_porch_hood=bool(val("log_wing_porch_hood", False)),
        chimneys=int(val("chimneys", 2)),
        chimney_material=val("chimney_material"),
        roof_colour=val("roof_colour"),
        elevation_scheme=str(val("elevation_scheme", "frontage")),
        first_story_height_m=measure("first_story_height_m"),
        entry_raise_m=measure("entry_raise_m", 0.0),
        gable_lunette=val("gable_lunette", False),
        gable_arch_treatment=val("gable_arch_treatment", "fanlight"),
        gable_arch_text=val("gable_arch_text", ""),
        corner_entry_surround=val("corner_entry_surround", False),
        flagstaff=val("flagstaff", False),
        flagstaff_height_m=measure("flagstaff_height_m", 4.25),
        chimney_placement=str(val("chimney_placement", "frontage")),
        side_entrance_face=side_face,
        enclosed_left_annex=val("enclosed_left_annex"),
        rear_ell=bool(val("rear_ell", False)),
        rear_ell_door=str(val("rear_ell_door", "carriage")),
        upper_windows=(None if val("upper_windows") is None
                       else int(val("upper_windows"))),
        eaves_bays=val("eaves_bays", {}),
        front_ground_layout=val("front_ground_layout"),
        end_windows=tuple((str(o["end"]), float(o["at"]), float(o["z"]),
                           float(o["width_m"]), float(o["height_m"]))
                          for o in (val("end_windows") or ())),
        stovepipes=int(val("stovepipes", 0)),
        cross_wing=bool(val("cross_wing", False)),
        cross_wing_depth_m=float(val("cross_wing_depth_m", 8.0)),
        cross_wing_end=str(val("cross_wing_end", "x_max")),
        # The programme's own finish deal, read off the record rather than the
        # phase. `wall_finish` in `common/materials.py` states the order these are
        # applied in and why a stated coating outranks them.
        finish_key=recon.get("finish_key"),
        roof_condition=recon.get("roof_condition"),
        siding_lay_m=_board_lay(recon),
        siding_seed=f"{(record or {}).get('id', '')}|{phase.get('id', '')}",
        confidence=confidences,
    )
    p.validate()
    return p


def _validate_enclosed_left_annex(p: FrameTavernParams) -> None:
    """One bounded three-mass +X interpretation, not arbitrary compound geometry."""
    g = p.enclosed_left_annex
    if (p.elevation_scheme != "gable_front" or p.roof_type != "gable" or
            p.stories != 2 or p.log_wing or p.cross_wing or p.gallery):
        raise ParamError("enclosed_left_annex needs a simple two-storey gable-front frame block")
    if p.confidence.get("enclosed_left_annex", "reconstructed") != "reconstructed":
        raise ParamError("enclosed_left_annex metric layout must remain reconstructed")
    required = {"attach_face", "front_setback_m", "shoulder", "connector", "boarding_range"}
    if (not isinstance(g, dict) or not required <= set(g)
            or set(g) - (required | {"shoulder_enclosed"})):
        raise ParamError("enclosed_left_annex needs exactly the bounded three-part layout")
    if "shoulder_enclosed" in g and type(g["shoulder_enclosed"]) is not bool:
        raise ParamError("enclosed_left_annex shoulder enclosure must be boolean")
    def number(v, lo, hi, label):
        if isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) or not lo <= v <= hi:
            raise ParamError(f"enclosed_left_annex {label} needs a finite number in {lo}..{hi}")
    if g["attach_face"] != "x_max":
        raise ParamError("enclosed_left_annex attaches only to x_max")
    number(g["front_setback_m"], -.3, 2., "setback")
    common={"span_m", "depth_m", "wall_m", "roof"}
    extra={"shoulder":{"roof_high_m","roof_low_m","front_window","front_gable_light","front_gable_peak_m"},
           "connector":{"roof_low_m","roof_high_m","front_openings"},
           "boarding_range":{"roof_pitch_deg","ridge_axis","front_door","front_window","front_gable_light"}}
    roofs={"shoulder":"shed_with_front_gable","connector":"shed","boarding_range":"gable"}
    for name in ("shoulder","connector","boarding_range"):
        v=g[name]
        optional = {"front_set_out_m", "plan_rotation_deg"} if name == "boarding_range" else set()
        if (not isinstance(v,dict) or not common|extra[name] <= set(v)
                or set(v) - (common|extra[name]|optional)):
            raise ParamError(f"enclosed_left_annex {name} has unsupported or missing fields")
        if "front_set_out_m" in v:
            number(v["front_set_out_m"], 0., 3., name+" front set-out")
        if "plan_rotation_deg" in v:
            number(v["plan_rotation_deg"], 0., 45., name+" plan rotation")
        number(v["span_m"], 1.5, 6., name+" span")
        number(v["depth_m"], 2., min(8.,p.depth_m-g["front_setback_m"]), name+" depth")
        number(v["wall_m"], 1.8, min(3.5,p.wall_height_m-.5), name+" wall")
        if name == "boarding_range":
            lap = v["depth_m"] - v.get("front_set_out_m", 0.)
            if lap < .25 or (v.get("plan_rotation_deg", 0.)
                             and lap > g["connector"]["depth_m"] - .25):
                raise ParamError("enclosed_left_annex boarding range loses its connector attachment")
        if v["roof"] != roofs[name]:
            raise ParamError(f"enclosed_left_annex {name} roof category is fixed")
        if name != "boarding_range":
            number(v["roof_low_m"], v["wall_m"]+.05, p.wall_height_m-.3, name+" roof low")
            number(v["roof_high_m"], v["roof_low_m"]+.05, p.wall_height_m-.2, name+" roof high")
        else:
            number(v["roof_pitch_deg"], 25., 40., name+" pitch")
            if v["ridge_axis"] != "y":
                raise ParamError("enclosed_left_annex boarding range ridge is y")
        if name == "connector":
            if v["front_openings"] != []:
                raise ParamError("enclosed_left_annex low connector has no stated front opening")
            continue
        def opening(key, count):
            a=v[key]
            if not isinstance(a,(list,tuple)) or len(a)!=count:
                raise ParamError(f"enclosed_left_annex {name} {key} has wrong section")
            for n in a:number(n, .01, 5., name+" "+key)
            number(a[0], .15, .85, name+" opening fraction")
            width=a[1] if key=="front_door" else a[2]
            if width/2+.15 > min(a[0],1-a[0])*v["span_m"]:
                raise ParamError("enclosed_left_annex opening breaks its facade edge")
            return a
        w=opening("front_window",4)
        if w[1]+w[3]+.15 > v["wall_m"]:
            raise ParamError("enclosed_left_annex lower sash breaks its eave band")
        light=opening("front_gable_light",4)
        if name=="shoulder":
            number(v["front_gable_peak_m"],max(v["roof_high_m"],light[1]+light[3]+.2),p.wall_height_m-.1,"shoulder peak")
            if light[1]-.1 < v["roof_low_m"] or light[2]+.5 > v["span_m"]:
                raise ParamError("enclosed_left_annex shoulder light breaks its bounded dormer")
        else:
            door=opening("front_door",3)
            if door[2]+.15>v["wall_m"]:
                raise ParamError("enclosed_left_annex door breaks its eave band")
            if abs(door[0]-w[0])*v["span_m"] <= (door[1]+w[2])/2+.15:
                raise ParamError("enclosed_left_annex door and sash overlap")
            edge_z=light[1]+light[3]+.15
            reach=abs((light[0]-.5)*v["span_m"])+light[2]/2+.1
            roof_z=v["wall_m"]+((v["span_m"]+.5)/2-reach)*math.tan(math.radians(v["roof_pitch_deg"]))
            if light[1]-.1<v["wall_m"] or edge_z>roof_z:
                raise ParamError("enclosed_left_annex upper light breaks its gable rake")


# --- THE FRONT ELEVATION, for `facade_openings` (T-3359) ----------------------
#
# The sign layer could not see a tavern's front, so every sign on a tavern hung on a
# bracket, a hood or a post, where an opening behind it did not matter. The owner,
# 2026-11-03, asked for the 1835 boards to be fixed flat on the face of the building
# instead, beside or over the door — and a board fixed flat on a wall whose doors and
# windows nobody has read is the fault T-0459 exists to stop. So this states the
# frontage scheme's front-face rectangles from the SAME numbers
# `frame_tavern._fenestration` and `_frontispiece` draw them with: five ground bays
# with the entrance in the centre one, `upper_windows` (else five) upstairs, a 0.85 x
# 1.35 m sash at 30 % of each storey, the 1.2 m door to 2.1 m, and — where the record
# carries them — the shutter leaves, the frontispiece's pilasters and hood, the
# pictured entrance case and the pictured lower sash, which a board must stay off as
# surely as the glass.
#
# These are copies of the builder's literals, not imports of them: the builder needs
# Blender to import, the commit gate has none, and this module is the one both can
# read. `tools/check_tavern_front_reader.py` holds the two to each other by reading
# the builder's source. Only the frontage scheme is read; the gable-front and
# corner-gable schemes and a log wing on the front still answer None, and the sign
# layer still refuses to fix a board flat on those.
TAVERN_WIN_W_M = 0.85
TAVERN_WIN_H_M = 1.35
TAVERN_SILL_FRACTION = 0.30
TAVERN_DOOR_HALF_W_M = 0.60
TAVERN_DOOR_H_M = 2.10
TAVERN_GROUND_BAYS = 5
TAVERN_SHUTTER_SHARE = 0.42          # a leaf is this share of the sash's width
TAVERN_CASING_W_M = 0.090            # common/openings.CASING_W_M
TAVERN_FRONTISPIECE_HALF_W_M = 1.02  # the crown of the hood, the widest member
TAVERN_FRONTISPIECE_TOP_M = 2.31


def front_wall(p: FrameTavernParams) -> dict | None:
    """`{u0, u1, wall_height_m, openings}` of the front (+y) elevation, or None.

    `u` runs along the front from the footprint's origin, as the builder draws the
    block over `0..width_m` with its facade on +y, the footprint's max-v edge.
    """
    if p.elevation_scheme != "frontage" or p.log_wing:
        return None
    w = float(p.width_m)
    wall_z = float(p.wall_height_m)
    story_h = wall_z / max(p.stories, 1)
    out = []
    for story in range(p.stories):
        z0 = story * story_h + story_h * TAVERN_SILL_FRACTION
        bays = p.upper_windows if (story > 0 and p.upper_windows) else TAVERN_GROUND_BAYS
        for i in range(bays):
            cx = w * (i + 0.5) / bays
            if story == 0 and i == bays // 2:
                g = p.front_opening_details
                if g is not None:
                    # the pictured case (`_pictured_front_entrance`): its crown is
                    # the widest member and its cornice the head of the whole thing
                    half = max(g["case_width_m"], g["jamb_outer_width_m"]) / 2
                    out.append({"kind": "door", "u0": cx - half, "u1": cx + half,
                                "z0": 0.0, "z1": float(g["cornice_top_m"])})
                    continue
                if p.entrance_frontispiece:
                    out.append({"kind": "frontispiece",
                                "u0": cx - TAVERN_FRONTISPIECE_HALF_W_M,
                                "u1": cx + TAVERN_FRONTISPIECE_HALF_W_M,
                                "z0": 0.0, "z1": TAVERN_FRONTISPIECE_TOP_M})
                out.append({"kind": "door", "u0": cx - TAVERN_DOOR_HALF_W_M,
                            "u1": cx + TAVERN_DOOR_HALF_W_M,
                            "z0": 0.0, "z1": TAVERN_DOOR_H_M})
                continue
            # the pictured lower front sash, where the record carries one
            sash = p.front_lower_sash if story == 0 else None
            sw = float(sash["width_m"]) if sash else TAVERN_WIN_W_M
            sh = float(sash["height_m"]) if sash else TAVERN_WIN_H_M
            sz = float(sash["sill_m"]) if sash else z0
            out.append({"kind": "window", "u0": cx - sw / 2, "u1": cx + sw / 2,
                        "z0": sz, "z1": sz + sh})
            if p.shutters:
                leaf = sw * TAVERN_SHUTTER_SHARE + TAVERN_CASING_W_M + 0.01
                for side in (-1, 1):
                    a = cx + side * sw / 2
                    b = cx + side * (sw / 2 + leaf)
                    out.append({"kind": "shutter", "u0": min(a, b), "u1": max(a, b),
                                "z0": sz, "z1": sz + sh})
    return {"u0": 0.0, "u1": w, "wall_height_m": wall_z, "openings": out}
