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
    "shutter_type", "entrance_frontispiece", "chimney_material", "roof_colour",
    "log_wing_door", "log_wing_porch_hood",
    "cross_wing", "cross_wing_depth_m", "cross_wing_end",
})

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
    elevation_scheme: str = "frontage"

    # What the stacks are made of, where a view says. None keeps the archetype's
    # roof-toned masses (the original treatment, kept exactly so no committed
    # building's stacks recolour); "brick" draws them in unpainted brick — the
    # Sauganash's, coloured by the Petford watercolour (T-0092).
    chimney_material: str | None = None

    # The roof's colour, where a view says. None keeps ROOF_RGBA (the archetype's
    # weathered-shingle grey, and every committed building's until T-0092);
    # "moss_green" is the Petford view's dark green/moss shingle tone.
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
    rear_ell: bool = False
    rear_ell_width_m: float = 5.5
    rear_ell_depth_m: float = 4.5
    rear_ell_wall_m: float = 2.6

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

    def validate(self) -> None:
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
        if self.elevation_scheme not in ("frontage", "gable_front"):
            raise ParamError(f"elevation_scheme '{self.elevation_scheme}' not in "
                             f"('frontage', 'gable_front')")
        if self.chimney_placement not in ("frontage", "gable_ends"):
            raise ParamError(f"chimney_placement '{self.chimney_placement}' not in "
                             f"('frontage', 'gable_ends')")
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
        if self.roof_colour not in (None, "moss_green"):
            raise ParamError(f"roof_colour '{self.roof_colour}' not in "
                             f"(None, 'moss_green')")
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
        siding_exposure_m=float(val("siding_exposure_m", 0.14)),
        shutters=val("shutters"),
        shutter_type=val("shutter_type"),
        gallery=bool(val("gallery", False)),
        entrance_frontispiece=bool(val("entrance_frontispiece", False)),
        log_wing=bool(val("log_wing", False)),
        log_wing_door=bool(val("log_wing_door", False)),
        log_wing_porch_hood=bool(val("log_wing_porch_hood", False)),
        chimneys=int(val("chimneys", 2)),
        chimney_material=val("chimney_material"),
        roof_colour=val("roof_colour"),
        elevation_scheme=str(val("elevation_scheme", "frontage")),
        chimney_placement=str(val("chimney_placement", "frontage")),
        side_entrance_face=side_face,
        rear_ell=bool(val("rear_ell", False)),
        cross_wing=bool(val("cross_wing", False)),
        cross_wing_depth_m=float(val("cross_wing_depth_m", 8.0)),
        cross_wing_end=str(val("cross_wing_end", "x_max")),
        # The programme's own finish deal, read off the record rather than the
        # phase. `wall_finish` in `common/materials.py` states the order these are
        # applied in and why a stated coating outranks them.
        finish_key=recon.get("finish_key"),
        roof_condition=recon.get("roof_condition"),
        confidence=confidences,
    )
    p.validate()
    return p
