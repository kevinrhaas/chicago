"""bridge_timber — the log bridges over the branches of the Chicago River.

The North Branch bridge (winter 1831-32) and the South Branch bridge between Lake and
Randolph (winter 1832-33) are described in the same two numbers: **about 10 ft wide,
clearing the water by about 6 ft**, of logs. This archetype builds the fixed, piered
form — stringers on abutments and bents, carrying a puncheon deck — and **both branch
crossings are built through it.**

That was not true until 2026-08-11: this docstring used to send the South Branch
crossing away to a raft archetype that was never written, on the strength of the word
every retelling uses for it. The 1883 old-settlers statement describes BOTH bridges as
abutments, two bents, log stringers and a puncheon floor about six feet above the
water, and a floating raft is none of those things. See bridge_timber_params for the
argument and for what would have to turn up to reverse it; the record itself carries
the conflict rather than resolving it away.

The 1834 Dearborn Street drawbridge is built through this archetype too, and it brought
the draw with it: `draw_span_m` clears the intermediate supports out of the opening and
stations `gallows_frames` at its ends, `gallows_height_m` sets how far they stand over
the deck.

**On 2026-08-21 the draw grew the rest of what the plates show** — `gallows_braced`
(knee braces and shores, the frames' A), `draw_lifting_gear` (the hoist chains) and
`draw_leaves` (the joint timber of a closed two-leaf draw). All three default OFF, so
every bridge that predates them resolves to exactly the bridge it resolved to before.
The evidence is a different kind from everything else on this archetype: two
retrospective engravings recorded in
`data/sources/assets/owner_brief_2026_08_18/README.md`, tier-5 pictorial, which may
drive form as `inferred` and never a coordinate. What is still NOT built is a leaf
RAISED, because that is the one thing no plate settles — see `_gallows`. The approaches
at either end of that bridge are not built either, and its record declares them.

The north-branch bridge is documented in 1832-33 as "formed of stringers and only
fitted for foot passengers" and "useless for teams", yet on 18 Aug 1835 it carried the
war-dance procession — hundreds of people at once. Something happened in between and
nothing records what. The archetype's defaults build the *later* reading, because the
scene date is 1835-07-01: four stringers rather than two, a full plank deck rather than
a walkway. Both of those are `inferred` at best and the records should say so.

## Railings: deliberately none ON THE BRANCH BRIDGES

**Decision: no railing, and the parameter defaults to False.** The reasoning, recorded
here because the absence is as much a claim as a presence would be. **Every argument
below is about the two LOG bridges over the branches, and the counter-argument at the
foot of it turned out to be the whole story for the third crossing** — on 2026-08-21
the Dearborn record set `railing: true`, on the strength of the two engravings the
owner supplied, which draw it railed. The default is unchanged and so is the reasoning;
what changed is that one record now has evidence and says so.

- **Updated 2026-08-10: the absence is now stated rather than merely unattested, and it
  has an expiry date nobody wrote down.** The 1883 old-settlers statement (Andreas
  pp. 631-632) has the branch bridges "about ten feet wide and without railings, for the
  first few years, after which guards, or railings, were added". For a scene three years
  after the build the natural reading of "the first few years" covers 1835 and the
  default stands — but it is a reading of a sequence now, and a date for the guards
  falling before July 1835 would flip it. The argument from silence below is what this
  decision rested on until that page was read, and it is kept because it was right.
- No source reached attests a railing on either log bridge. The dossier's crossing
  table gives width, clearance and construction and nothing else.
- The one qualitative description we have runs the other way. "Formed of stringers and
  only fitted for foot passengers" and "useless for teams" describe something closer to
  a causeway of logs than to a piece of civil engineering, and a railing is the part
  you add when you have finished the parts that hold the bridge up.
- A railing is unusually load-bearing visually. A railed bridge reads as considered
  infrastructure; an unrailed one reads as a plank over water. Adding one to look
  finished would change what a visitor believes about how developed the town was, which
  is precisely the kind of silent gap-filling AGENTS.md rule 2 forbids.
- The counter-argument, stated so it is on the record: the 1834 Dearborn Street
  drawbridge was a real piece of engineering and the town clearly could build one, and
  a procession of hundreds crossing a 6-ft-high unrailed deck is an alarming picture.
  That is an argument for the 1835 rebuild having been substantial — not evidence about
  a railing. If a source turns up, set `railing: true` on the record with its own
  confidence; the geometry is written and will build at `conjectural` until something
  better exists.

## Local origin: z = 0 is the water, not the ground

docs/GLB-CONTRACT.md pins a structure's local origin to "y = 0 at the base of the
walls". A bridge has no walls and its documented dimension is a clearance above the
*water*, so this archetype anchors z = 0 at the design water surface: the deck sits at
+clearance +structure, and the cribs run down through zero into the river. A renderer
placing one of these must therefore place it against the water plane, not the terrain.
That is a genuine hole in the contract rather than a deviation from it, and it is
called out in the report for this parcel.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.logwork import (  # noqa: E402
    COURSE_M, HEWN_RGBA, hewn_log_wall, log_prism,
)
from common import materials  # noqa: E402
from common.mesh import MeshBuilder, simple_material  # noqa: E402
from archetypes.bridge_timber_params import BridgeTimberParams  # noqa: E402

M_LOG, M_DECK, M_FILL, M_IRON = 0, 1, 2, 3

PLANK_PITCH_M = 0.42      # a split puncheon, flat face up
SAWN_PITCH_M = 0.26       # a sawn plank, narrower and regular
# How far the cribs and piles run below the waterline before the mesh stops. They
# actually reached the riverbed; there is no point modelling what the water hides, and
# the renderer's water plane sits at z = 0 in this local frame.
SUBMERGED_M = 0.55

DECK_RGBA = (0.47, 0.41, 0.32, 1.0)   # weathered split-log deck, greyer than a wall log
# Crib fill: river stone and gravel, not the pale clay-and-lime that chinks a cabin.
# Reusing CHINK_RGBA here made the piers read as stacks of whitewashed slabs.
FILL_RGBA = (0.300, 0.295, 0.270, 1.0)
# Wrought iron, weathered: the hoist chains, and NOT ON THE MATERIAL SHEET. Every
# other colour this module names is local for the same reason (see DECK_RGBA and
# FILL_RGBA above) — `common/materials.py` is the sheet for wall, roof and paint
# substrates and holds no metal at all. Adding one properly is the material sheet's
# own parcel (T-0007); until then this is declared here, in the open, rather than
# borrowed from a timber row it is not. Dark and only faintly specular, because a
# chain that catches the sun reads as a rope of light at 60 m and the frames are the
# silhouette this bridge is remembered by, not the tackle.
IRON_RGBA = (0.118, 0.112, 0.104, 1.0)

# The hoist chain's section, drawn as a slim square run rather than as links. Links
# would be a few thousand triangles on a member that subtends about two pixels from
# the bank, and the plate shows a line, not a linkage.
CHAIN_S = 0.042
# How far a leaf-edge timber stands proud of the deck boards. Low enough to step over
# without noticing, which is what a bridge deck's joint beams are.
LEAF_PROUD_M = 0.055


def build(params: BridgeTimberParams, name: str):
    """Build the bridge. Returns a Blender object at the local origin; z = 0 is the
    water surface (see the module docstring), y-up is handled by the exporter."""
    params.validate()
    b = MeshBuilder(name)

    # For a bridge the documented description IS dimensional — "about ten feet wide,
    # clearing the water by about six feet, of logs" is the whole of it — so width and
    # clearance sit in the character set that drives the deck and stringers, where a
    # building's width would not. Span and pier spacing stay out of it: nobody
    # recorded the river's width at the crossing or anything at all about the piers.
    # The rule (least-confident-wins over the attributes that say what the thing WAS)
    # is unchanged; the membership of that set is what differs. See
    # bridge_timber_params' module docstring and frame_tavern.build.
    c_struct = params.worst_conf("construction", "width_m", "clearance_m")
    # The floor joined that set on 2026-08-10: "on these stringers puncheons or split
    # logs were laid for a floor" says what the deck WAS, which is the membership test.
    c_deck = params.worst_conf("construction", "width_m", "clearance_m", "deck_kind")
    # WHAT THE SUPPORTS ARE AND HOW MANY, not where they stand. Even at a documented
    # count the spacing along the span is the archetype's (see pier_x), and no tint
    # can say so — docs/LIBERTIES.md carries that half.
    c_pier = params.worst_conf("pier_kind", "pier_count")

    deck_z = params.deck_height_m
    stringer_top = deck_z - params.plank_t_m
    bearing_z = stringer_top - params.stringer_d_m      # underside = the clearance line

    _stringers(b, params, stringer_top, c_struct)
    _deck(b, params, deck_z, c_deck)

    for xp in params.pier_x:
        _pier(b, params, xp, bearing_z, c_pier)
    if params.abutments:
        _abutments(b, params, bearing_z, params.conf("abutments"))
    if params.railing:
        _railing(b, params, deck_z, params.conf("railing"))
    # The closed draw's own timber — the bearing beams at the opening's ends, the two
    # leaves' edge beams, and their butts meeting at mid-draw. It divides the deck
    # visually and not structurally: the boards run through, so the crossing is as
    # walkable as it was. Confidence is the leaf count's, because the count is the
    # claim; see _draw_leaves.
    if params.draw_leaves:
        _draw_leaves(b, params, deck_z,
                     params.worst_conf("draw_leaves", "draw_span_m"))
    # The gallows frames over a draw. Their POSITIONS are documented (either end of a
    # documented opening) and their SIZE is not, so the whole frame takes the height's
    # confidence: a frame whose height is a guess is a guessed frame, even though we
    # know exactly where it stood and how many there were.
    for xg in params.gallows_x:
        _gallows(b, params, xg, deck_z, bearing_z,
                 params.worst_conf("gallows_height_m", "gallows_frames",
                                   "draw_span_m"))
        # The tackle, hung from the frame that was just built. Separate from _gallows
        # because it is separate evidence: the frames come from a sentence and the
        # chains from a plate.
        if params.draw_lifting_gear == "chain_hoist":
            _hoist_chains(b, params, xg, deck_z,
                          params.worst_conf("draw_lifting_gear", "gallows_height_m",
                                            "draw_span_m"))

    mats = [
        # The sheet's hewn-log roughness (0.92), which this module used to miss by
        # 0.01 for no argued reason. Crib logs were not hewn — see logwork.py — but
        # they go through the same wall helper and read as the same joint, and the
        # sheet has one log row until a source gives it two.
        simple_material("log", HEWN_RGBA,
                        roughness=materials.SUBSTRATES["hewn_log"].roughness),
        simple_material("deck", DECK_RGBA, roughness=0.95),
        simple_material("fill", FILL_RGBA, roughness=0.98),
        simple_material("iron", IRON_RGBA, roughness=0.62),
    ]
    return b.to_object(mats)


def _stringer_y(p: BridgeTimberParams) -> list[float]:
    """Stringer centre-lines across the deck.

    Inset by half a diameter, so the outermost log's outer face lands on the deck edge
    and stays visible from the bank. A deeper inset tucks the stringers entirely under
    the overhanging plank ends, which loses the only word any source gives us about
    how this bridge was built: "formed of stringers".
    """
    n = p.stringer_count
    inset = p.stringer_d_m * 0.5
    lo, hi = inset, p.width_m - inset
    if n == 1:
        return [p.width_m / 2.0]
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def _stringers(b: MeshBuilder, p: BridgeTimberParams, top_z: float,
               conf: float) -> None:
    """Round log stringers, one run per bay.

    Broken at every support rather than run continuously, which is what the 1883
    old-settlers statement describes — "stringers of heavy logs stretched from the
    abutments to the bents, and between the bents" — and the butt joints over each
    support are also the detail that tells a viewer from the bank where they stand.

    ONE RUN IS ONE LOG HERE, and over a long bay that is a simplification rather
    than a reading. The North Branch bridge's three bays are 23.9 m each; nobody
    was moving a 24 m timber, so those runs were spliced somewhere and no source
    says where. Splices are omitted rather than invented, and admitted in
    docs/LIBERTIES.md. The earlier version of this docstring said the breaks were
    there because "nobody had 15 m logs", which stopped being a description of what
    this function builds the moment the bay count came off a spacing.
    """
    r = p.stringer_d_m / 2.0
    zc = top_z - r
    edges = [0.0] + list(p.pier_x) + [p.span_m]
    for y in _stringer_y(p):
        for a, c in zip(edges, edges[1:]):
            # overlap the bearings slightly so the joints are lapped, not butted in
            # mid-air
            log_prism(b, (a - 0.18, y, zc), (c + 0.18, y, zc), r, conf, M_LOG)


def _deck(b: MeshBuilder, p: BridgeTimberParams, deck_z: float, conf: float) -> None:
    """The floor: puncheons — split logs laid across the stringers, flat face up —
    or, where a record says so, sawn plank.

    "On these stringers puncheons or split logs were laid for a floor" is the 1883
    old-settlers statement, and `deck_kind` is where a record says it. The two values
    differ in the mesh and not only in the label: a puncheon floor is riven stock of
    uneven width whose butts do not line up, and sawn plank is narrower, regular, and
    laid to a straight edge. Nothing in this dataset carries `plank` today; it exists
    so that the puncheons are a value the generator reads rather than a word in a note.

    Every board is its own box. The first version was one slab with a proud face per
    plank stamped on top, which was cheaper and looked like a concrete slab scored
    with lines: the deck edge stayed dead straight, so from the bank — where anyone
    standing at the forks actually sees this bridge — there was nothing to say it was
    made of logs. Individual boards give a ragged edge of butts, which is the detail
    that carries the whole read. Roughly four hundred triangles on the one surface a
    visitor walks across is a fair trade.
    """
    riven = p.deck_kind == "puncheon"
    t = p.plank_t_m
    over = 0.06 if riven else 0.03   # board ends overhanging the outer stringers
    y0, y1 = -over, p.width_m + over

    pitch_m = PLANK_PITCH_M if riven else SAWN_PITCH_M
    n = max(int(p.span_m / pitch_m), 2)
    pitch = p.span_m / n
    gap = 0.022 if riven else 0.008
    for i in range(n):
        xa, xb = i * pitch + gap / 2, (i + 1) * pitch - gap / 2
        # Split logs vary; nudging alternate ends stops the butts lining up into a
        # sawn edge. Deterministic, not random — the build has to be reproducible.
        # Sawn stock is exactly the case where they SHOULD line up, so no jitter.
        ja = 0.0
        if riven:
            ja = 0.035 if i % 3 == 0 else (-0.02 if i % 3 == 1 else 0.0)
        b.add_box(xa, y0 - ja, deck_z - t, xb, y1 + ja, deck_z, conf, M_DECK,
                  skip=("bottom",))


def _pier(b: MeshBuilder, p: BridgeTimberParams, xp: float, bearing_z: float,
          conf: float) -> None:
    """One intermediate support: a bent of heavy logs, a log crib, or driven piles."""
    if p.pier_kind == "bent":
        _log_bent(b, p, xp, bearing_z, conf)
        return
    if p.pier_kind == "pile":
        _pile_bent(b, p, xp, bearing_z, conf)
        return
    half = 0.58
    _crib(b, xp - half, 0.42, xp + half, p.width_m - 0.42, bearing_z, conf)
    _cap(b, p, xp, bearing_z, conf)


def _crib(b: MeshBuilder, x0: float, y0: float, x1: float, y1: float,
          top_z: float, conf: float) -> None:
    """A log crib: courses of logs laid up in alternating directions, the ends
    protruding at the corners, and the box filled with whatever came out of the river.

    Built by the same `hewn_log_wall` that builds the cabins, which is the point — a
    crib corner and a cabin corner are the same joint and should look it — but with a
    coarser course and a shallower relief. Crib logs were heavier than wall logs and
    nobody chinked them, so the line between courses is a packed seam of stone and
    gravel rather than a band of lime, and it takes the grey M_FILL rather than the
    cabins' pale clay. Reusing the cabin colour here made every pier read as a stack
    of whitewashed slabs.
    """
    hewn_log_wall(b, x0, y0, x1, y1, -SUBMERGED_M, top_z, conf, M_LOG, M_FILL,
                  skip=("bottom",), course=COURSE_M * 1.35, relief=0.016)


def _cap(b: MeshBuilder, p: BridgeTimberParams, xp: float, bearing_z: float,
         conf: float) -> None:
    """A cap log across the crib head, which is what the stringers actually bear on."""
    r = 0.17
    log_prism(b, (xp, -0.10, bearing_z - r), (xp, p.width_m + 0.10, bearing_z - r),
              r, conf, M_LOG)


def _log_bent(b: MeshBuilder, p: BridgeTimberParams, xp: float, bearing_z: float,
              conf: float) -> None:
    """"The bents were of four heavy logs, resting on the bottom, in deeper water."

    Four posts under a cap, and the count is the source's rather than a choice. Heavier
    than the driven piles below — these are logs, not stakes — which is the one thing
    besides the number that the sentence gives.

    WHAT IS NOT MODELLED IS THE HALF THE SENTENCE IS ABOUT. "Resting on the bottom"
    distinguishes a bent stood on the riverbed from one driven into it, and this
    project models neither bed nor anything below `SUBMERGED_M`: above the waterline
    the two are the same picture. So the difference between this function and
    `_pile_bent` is four heavy logs against three light ones, which is what a visitor
    can see, and the rest of the distinction lives in the record.
    """
    r = 0.21
    for i in range(4):
        y = p.width_m * (i + 0.5) / 4.0
        log_prism(b, (xp, y, -SUBMERGED_M), (xp, y, bearing_z - 0.34), r, conf, M_LOG)
    _cap(b, p, xp, bearing_z, conf)


def _pile_bent(b: MeshBuilder, p: BridgeTimberParams, xp: float, bearing_z: float,
               conf: float) -> None:
    """Three driven piles and a cap log. Cheaper than a crib in triangles and in
    1830s labour, and a third reading of "log construction" — `pier_kind` is the
    record's choice among the three. For the North Branch bridge it is no longer a
    choice: the men who used it wrote down that it stood on bents."""
    r = 0.15
    for i in range(3):
        y = p.width_m * (i + 0.5) / 3.0
        log_prism(b, (xp, y, -SUBMERGED_M - 0.4), (xp, y, bearing_z - 0.34), r,
                  conf, M_LOG)
    _cap(b, p, xp, bearing_z, conf)


def _abutments(b: MeshBuilder, p: BridgeTimberParams, bearing_z: float,
               conf: float) -> None:
    """A crib at each bank for the end bays to land on.

    The bridge has to bear on something at the ends and no source says what, so these
    are conjectural by default and are built the same way as the piers so at least the
    invention is consistent with itself. Kept slimmer than a pier: in a scene most of
    an abutment is inside the bank, and a full-sized crib at each end made a 17 m
    bridge look like it was propped on two grain elevators.
    """
    d = 0.62
    for x0, x1 in ((-d, 0.16), (p.span_m - 0.16, p.span_m + d)):
        _crib(b, x0, 0.22, x1, p.width_m - 0.22, bearing_z, conf)


def _strut(b: MeshBuilder, p0, p1, s: float, conf: float, mat: int) -> None:
    """A square-section timber between two arbitrary points.

    `log_prism` only runs along an axis, by design — every log in this archetype is
    square to the deck. A brace is the one member that is not, so it gets its own
    swept box rather than a relaxation of the log helper: a raking round log would
    have to answer how its ends are cut, and a squared brace does not.

    Winding is load-bearing here, not decoration. glTF meshes are single-sided, so a
    quad wound the wrong way is a hole. The section ring is built counter-clockwise
    about the axis, which makes `(near[i], near[i+1], far[i+1], far[i])` face outward
    for every side and lets the two caps be the ring in order and in reverse.
    """
    d = [p1[i] - p0[i] for i in range(3)]
    length = math.sqrt(sum(c * c for c in d))
    if length < 1e-6:
        return
    d = [c / length for c in d]
    ref = (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = [d[1] * ref[2] - d[2] * ref[1],
         d[2] * ref[0] - d[0] * ref[2],
         d[0] * ref[1] - d[1] * ref[0]]
    un = math.sqrt(sum(c * c for c in u))
    u = [c / un for c in u]
    v = [d[1] * u[2] - d[2] * u[1],
         d[2] * u[0] - d[0] * u[2],
         d[0] * u[1] - d[1] * u[0]]
    # Counter-clockwise about d, given d = u x v.
    corners = [(+1, +1), (-1, +1), (-1, -1), (+1, -1)]
    near = [tuple(p0[i] + s * (a * u[i] + c * v[i]) for i in range(3))
            for a, c in corners]
    far = [tuple(p1[i] + s * (a * u[i] + c * v[i]) for i in range(3))
           for a, c in corners]
    for i in range(4):
        j = (i + 1) % 4
        b.add_poly([near[i], near[j], far[j], far[i]], conf, mat)
    b.add_poly(far, conf, mat)
    b.add_poly(list(reversed(near)), conf, mat)


def _gallows(b: MeshBuilder, p: BridgeTimberParams, xc: float, deck_z: float,
             bearing_z: float, conf: float) -> None:
    """One gallows frame: two heavy posts straddling the deck under a head timber.

    "It was of the 'gallows pattern,' and for five years, the frames, one at either
    end, stood like instruments of death to frighten the timid stranger at night."
    That sentence is the whole of the evidence, and it is a description of a
    SILHOUETTE — which is why this function exists at all and why everything it
    builds is tagged with the height's confidence rather than the count's. What a
    gallows is, structurally, is in the name: two uprights and a cross-head, with the
    tackle hung from the head.

    WHAT THIS FUNCTION REFUSED TO BUILD UNTIL 2026-08-21, AND WHY TWO OF THE THREE
    ARE NOW BUILT. The list below was written against the two TEXTS this project
    holds, and as a reading of a text it was right and still is: Andreas and the
    chicagology transcription name no tackle, no leaf and no brace. What changed is
    that the project acquired a second KIND of evidence for this structure — the two
    engravings recorded in `data/sources/assets/owner_brief_2026_08_18/README.md`
    (images 2 and 3), tier-5 pictorial, which may drive form as `inferred`.

    - **Tackle.** Built where a record says `draw_lifting_gear: chain_hoist`, in
      `_hoist_chains`, because both plates draw chains falling from the frames. Still
      absent by default, and still absent from the texts.
    - **Bracing.** Built where a record says `gallows_braced`, below, because both
      plates draw the frames as an A and not as a bare portal. Sections and angles are
      this module's own.
    - **No leaf raised.** Unchanged, and it is the one of the three that no plate
      settles: the deck runs continuously across the opening, which is the state that
      fits every reading of the source at once — one leaf, two leaves, or a section
      lifted bodily between the frames. A RAISED leaf would have to pick one. What
      `_draw_leaves` adds is the joint timber of a draw lying DOWN, which a record may
      decline by leaving `draw_leaves` at zero.

    The posts run from the bearing line rather than from the deck, because a frame
    hoisting a sixty-foot draw is framed down into the substructure and not stood on
    the planking; that much is carpentry rather than evidence, and it is the one
    inference here that no reading of the source disturbs.
    """
    h = p.gallows_height_m
    s = 0.17                       # half-section of a post
    out = 0.26                     # how far outside the deck edge the posts stand
    top = deck_z + h
    for y in (-out, p.width_m + out):
        b.add_box(xc - s, y - s, bearing_z, xc + s, y + s, top, conf, M_LOG,
                  skip=("bottom",))
    # The head timber across the two posts, overhanging each by its own section so the
    # joint reads as a lapped cross-head rather than a butt.
    head_z = top - 0.36
    b.add_box(xc - s * 0.85, -out - 2 * s, head_z,
              xc + s * 0.85, p.width_m + out + 2 * s, top, conf, M_LOG)
    if not p.gallows_braced:
        return
    # THE A. Two knee braces in the frame's own plane, rising from the posts to the
    # underside of the head, and one shore per post raking down the span AWAY from
    # the opening to the bearing line. Face-on from an approach the knees close the
    # portal into a triangle; in profile from the bank the shores do. That is the
    # silhouette both plates draw, and every number in the next six lines is this
    # module's — the plates show a braced frame, not a schedule of scantlings.
    kn = 0.105                      # half-section of a knee brace
    reach = min(1.35, p.width_m * 0.45)
    for y_post, sgn_y in ((-out, 1.0), (p.width_m + out, -1.0)):
        _strut(b, (xc, y_post + sgn_y * s, top - 2.05),
               (xc, y_post + sgn_y * (s + reach), head_z + 0.04),
               kn, conf, M_LOG)
    sh = 0.125                      # half-section of a shore
    sgn_x = -1.0 if xc < p.span_m / 2.0 else 1.0
    for y_post in (-out, p.width_m + out):
        _strut(b, (xc + sgn_x * s, y_post, deck_z + 2.60),
               (xc + sgn_x * (s + 2.85), y_post, bearing_z + 0.06),
               sh, conf, M_LOG)


def _hoist_chains(b: MeshBuilder, p: BridgeTimberParams, xc: float, deck_z: float,
                  conf: float) -> None:
    """The chains, falling from one gallows head to the free end of its leaf.

    **WHAT THIS IS EVIDENCE OF, EXACTLY.** Both engravings in the 2026-08-18 owner
    brief (README images 2 and 3) draw chains running from the frames down to the
    draw. That is a tier-5 pictorial view — retrospective, drawn decades after 1835 —
    and the project's rule for one is that it may drive form as `inferred` and may
    never drive a coordinate. So: THAT there were chains is the plate's, at
    `inferred`. Everything below — two per frame, one each side of the deck, straight,
    this section, this anchorage — is the module's, at `reconstructed`, and it is a
    liberty.

    **WHAT IT IS NOT EVIDENCE OF.** Andreas and the chicagology page still say nothing
    about tackle, and the record's three readings of how the opening was closed still
    all stand. A retrospective engraver had the same problem this project has and
    fewer scruples, so a plate drawn in the 1880s showing an 1834 bridge may be
    reporting the mechanism or may be importing a later one. The chain is built
    because the owner asked for the bridge his plates show and because
    `reconstructed` is the tier that carries exactly this; it is not a finding.

    **The run.** From the underside of the head timber, out and down to the leaf's
    free end at the centre of the opening — the geometry a hinged leaf's hoist has,
    and the one the plates draw. Placed just OUTSIDE the deck edge so a visitor walks
    under nothing: the chain lands on the leaf's outer edge beam, not on the footway.
    Drawn taut. A chain carrying a closed leaf is in fact slack, and a catenary here
    would be four times the triangles for a sag no one can see at 60 m.
    """
    if not p.draw_span_m:
        return
    mid = p.span_m / 2.0
    head_z = deck_z + p.gallows_height_m - 0.36
    for y in (-0.14, p.width_m + 0.14):
        _strut(b, (xc, y, head_z), (mid, y, deck_z + LEAF_PROUD_M * 0.5),
               CHAIN_S, conf, M_IRON)
        # The eye the chain is shackled to, at the head. Small, and it is what stops
        # the run reading as a wire that ends in mid-air.
        b.add_box(xc - 0.09, y - 0.075, head_z - 0.14, xc + 0.09, y + 0.075,
                  head_z + 0.02, conf, M_IRON)


def _draw_leaves(b: MeshBuilder, p: BridgeTimberParams, deck_z: float,
                 conf: float) -> None:
    """The joint timber of a draw lying down: what makes a closed opening legible.

    The deck boards are untouched and run straight through, so the crossing stays as
    walkable as it was — `_deck` never learns there is a draw. What is added is the
    framing a leaf has at its edges: a bearing timber across the deck at each end of
    the opening, where a leaf is hinged and where it lands; an edge beam down each
    side of each leaf; and, at the centre of the opening, the two leaves' ends butted
    against each other with a finger of daylight between them.

    **This is the choice the record makes and the mesh used to refuse.** Two leaves,
    each hinged at its own frame, is one of the three readings
    `form.draw_lifting_gear` enumerates, and it is the one both plates draw. A record
    that would rather take no view leaves `draw_leaves` at zero and gets the 2026-08-11
    bridge back, unbroken across the opening. Nothing here is attested; the whole run
    carries the leaf count's confidence and owes docs/LIBERTIES.md an entry.

    Proud of the deck by `LEAF_PROUD_M` — 55 mm, a threshold rather than a step.
    """
    if not p.draw_span_m:
        return
    mid = p.span_m / 2.0
    lo, hi = mid - p.draw_span_m / 2.0, mid + p.draw_span_m / 2.0
    z0, z1 = deck_z - p.plank_t_m, deck_z + LEAF_PROUD_M
    # The two bearing timbers, at the ends of the opening.
    for x in (lo, hi):
        b.add_box(x - 0.17, -0.10, z0, x + 0.17, p.width_m + 0.10, z1, conf, M_LOG,
                  skip=("bottom",))
    # The leaves' butts at the centre, with the joint between them.
    for x0, x1 in ((mid - 0.36, mid - 0.025), (mid + 0.025, mid + 0.36)):
        b.add_box(x0, -0.10, z0, x1, p.width_m + 0.10, z1, conf, M_LOG,
                  skip=("bottom",))
    # An edge beam down each side of each leaf, which is also what the hoist chain
    # lands on.
    for y0, y1 in ((-0.10, 0.03), (p.width_m - 0.03, p.width_m + 0.10)):
        for a, c in ((lo, mid - 0.025), (mid + 0.025, hi)):
            b.add_box(a, y0, z0, c, y1, z1, conf, M_LOG, skip=("bottom",))


def _railing(b: MeshBuilder, p: BridgeTimberParams, deck_z: float,
             conf: float) -> None:
    """A pole rail on posts. OFF by default — see the module docstring for the
    argument, which is the substantive part of this function. The Dearborn Street
    drawbridge turns it on; the two branch bridges do not."""
    h, r = 0.95, 0.06
    step = max(p.span_m / max(round(p.span_m / 2.2), 1), 1.0)
    n = int(p.span_m / step)
    for y, sgn in ((0.0, -1), (p.width_m, 1)):
        yy = y + sgn * 0.05
        for i in range(n + 1):
            x = min(i * step, p.span_m)
            b.add_box(x - 0.06, yy - 0.06, deck_z, x + 0.06, yy + 0.06, deck_z + h,
                      conf, M_LOG, skip=("bottom",))
        log_prism(b, (-0.10, yy, deck_z + h - r), (p.span_m + 0.10, yy, deck_z + h - r),
                  r, conf, M_LOG)
