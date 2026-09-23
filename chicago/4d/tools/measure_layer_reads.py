#!/usr/bin/env python3
"""Which of a plant's, an animal's or a resident's figures reaches a vertex.

ROADMAP K42, opened by K41. This project answers that question for two of its
layers and had never asked it of the other two.

    generators/archetypes/*_params.py   declares CONSUMED — the form attributes
                                        the building generator reads
    generators/terrain_inputs.py        declares CONSUMED — the terrain spec
                                        figures the ground generator reads

`tools/validate.py` turns each of those into a rule: every figure OUTSIDE the
read-set carries a declaration saying what the mesh does instead, because the
confidence model grades how sure we are of a value and says nothing at all about
whether the thing was built. A `documented` painted wolf sign over a building
with no sign on it is the failure that rule exists to end.

`data/flora/` and `data/fauna/` have no such map, and they are not small: 154
plant records across ten communities, 139 animal records across ten habitat
zones, 202 and 30 citations of a source whose rights are unresolved (K41). Every
figure in them is shipped to a browser, and until this ran nothing here could say
which ones a visitor is looking at.

AND NEITHER DID `data/residents/`, which is ROADMAP K52 and ticket T-0021. That
layer is 201 households and 237 person entries, and its box says plainly why it
was the harder of the two rather than the easier: it already had *a* reader —
`tools/compile_scene.py` attaches a household to a building's sidecar and
`popup.js` names it on the card — and **"a layer with one reader is exactly where
an unread figure hides, because 'the browser has it' reads as 'somebody looks at
it'."** K52 then gave it a second reader, the Evidence panel's people section,
and the layer STILL was not censused: assertion 3a below can only fail for a
layer this file knows about, and its layer list was two names long, so a
directory a renderer opens and a map nobody wrote went to no assertion at all.
That is the same expired-claim shape 3a exists to catch, one level up — the gate
was blind rather than wrong.

Censusing it found the thing a census is for. Three of a person's figures —
`age_on_scene_date`, `birth_year` and `name_basis` — are graded claim blocks and
were being handed whole to a text renderer, so **113 person rows read "How this
person is named — [object Object]"**, hiding the sentence this project most needs
read: *"THE NAME IS INVENTED. No source names this resident."* A figure that
arrives on the card as `[object Object]` has not reached a visitor. They are
`shown` here because they are shown now; the commit that declared them is the
commit that fixed them, which is the only order that is honest.

WHY THE MAP IS IN PYTHON AND THE READER IS JAVASCRIPT. `terrain_inputs.py` gives
the argument for not co-locating a read-set with the code that reads: there the
generator's bytes are hashed into the ground, so a constant no builder reads
would have demanded a Blender bake. Here the reason is plainer — the reader is
`renderers/web/js/`, the gate is a Python script, and a declaration written into
the renderer would be a renderer change with a 26-minute smoke behind it every
time a key moved. What co-location would have bought is bought the same way the
terrain buys it: **every declaration is scanned against the renderer sources**,
in both directions, with the JS comments stripped first. A `read` declaration
names an expression that must still be in the source; an `unread` figure must not
be accessible anywhere in it. So a declaration that stops being true fails here
rather than quietly excusing an omission.

    tools/measure_layer_reads.py              print the census
    tools/measure_layer_reads.py --gate       exit 1 on a divergence
    tools/measure_layer_reads.py --self-test  break each assertion, in memory
    tools/measure_layer_reads.py --update     rewrite the baseline

THE FOUR STATES. Three of them are reads and the fourth is the finding.

    mesh    a vertex or a pixel comes from the value
    shown   the renderer reads it and shows it to a visitor as text
    probe   the renderer reads it into a diagnostic or a gate accessor, and
            nothing a visitor sees comes from it
    unread  nothing in the renderer reads it at all

`machinery` is the fifth thing and is not a state: identity, file routing and
provenance keys — `id`, `file`, `sources`, `note` — are not figures and never
reach the gate, exactly as `compile_scene.ground_fields` strips them on the
ground side. An explicit read declaration outranks the machinery list, which is
how `species[].confidence` — a provenance grade everywhere else in this project,
and a colour here, because the confidence view tints each plant by it — is
counted as a figure that reaches a pixel.

FIVE ASSERTIONS.

1.  **(absolute) Every figure present in the data is classified.** A new key in a
    zone, a manifest or a palette with no entry here fails. "The renderer ignores
    it" and "nobody has said" are different states and only one of them is a
    finding — the terrain gate's sentence, arriving on the vegetation.

2.  **(absolute) Every read declaration is a real read.** The expression it names
    must appear in the renderer sources with comments stripped. Stripping first
    is not fastidiousness: `flora.js` discusses `bare_soil_fraction: 0.45` in a
    comment three lines above the line that reads it, and a scan that matches its
    own explanatory prose proves nothing (`check_sidecar_contract` reported
    itself on its first run for exactly this).

3.  **(absolute) Every unread figure is really unread**, in two halves. The
    strong half is the LAYER: a layer no renderer source opens has been read by
    nothing in it, and a layer that gains a reader fails here, because the whole
    of its unread bank rests on nobody opening it. **That is what happened.** It
    settled `data/fauna` entirely until 2026-08-17, when ROADMAP K51 gave the
    layer a reader — `renderers/web/js/fauna.js`, the Evidence panel's wildlife
    section — and this assertion did exactly what it was built for: the thirty
    figures behind that sentence had to be classified in the same commit instead
    of resting on a claim that had quietly expired. All thirty are `shown` and
    none is `mesh`; no animal is drawn in this scene. The narrow half is per
    figure: the reverse scan looks for a
    property access of the leaf. Leaves whose bare name collides with the
    renderer's own vocabulary — `rgb` is a three.js shader field as well as a
    palette key — are declared in `AMBIGUOUS_LEAVES` and scanned
    parent-qualified. Leaves whose name is read under ANOTHER record kind —
    `bare_soil_fraction` is read off a zone and copied into the manifest — are
    listed as shared and exempted, because a text scan cannot attribute a
    property access to one of two records that both have that field, and a scan
    that cannot fail honestly is worse than a stated exemption.

4.  **The unread population is banked and may not grow.** `tools/layer_reads_
    baseline.json`, keyed by layer, record kind and field path, with the number
    of records carrying each figure. A new unread figure fails: either the
    renderer reads it, or shipping it to a browser is a decision somebody makes
    on purpose in the commit that adds it.

5.  **(absolute) The bank may not outlive the data.** An entry that is no longer
    in the tree fails until it is un-banked with `--update` in the same commit,
    because a repair here is a claim and recording it is part of making it.

6.  **The banked record COUNT is held for flora and fauna and not for residents**
    (T-1029). Assertion 4 banks each path with the number of records carrying it,
    and that number went ungated from the day it was written — which is how
    `residents/manifest:households[].head` came to say 1,338 against a tree of
    1,284, and `merged[]` 42 against 57, for as long as nobody looked.

    THE DECISION THIS FILE MAKES, because the ticket asked for one either way. A
    count is a TALLY, not a claim: the claim is assertion 4's, that this figure
    reaches nothing, and the tally only says how widely. Gating it exactly would
    fire on every ticket that mints, folds or merges a resident card — 61 of the 94
    banked paths are `residents/` and the layer is the one thing this project is
    still actively writing — and the whole remedy for that failure is `--update`. A
    gate whose only possible response is to re-bank is not a gate; it is a chore
    that trains people to re-bank without reading, and it would drag a 61-line
    diff of somebody else's measurement into every research PR, which is the
    unread-change laundering T-1029 exists to stop.

    `data/flora/` and `data/fauna/` are the opposite case. They are finished
    research datasets — 154 plant and 139 animal records, unchanged since the day
    they were banked — so a count that moves there is not growth, it is an edit to
    a dataset nobody is editing, and it should have to say so. Those counts are
    held exactly. `COUNTS_NOT_HELD` is where that line is drawn, and a layer that
    stops being written should come out of it.

WHAT THIS DOES NOT DECIDE. Whether an unread figure should be deleted, wired up
or declared is three different answers for three different findings, and none of
them is this parcel's to make — except where somebody has made it, which is what
`REFUSALS` below is: a figure whose answer is "this should not reach a visitor,
and here is why", written against the figure and carried into the bank: `data/fauna/` is a research dataset whose value
does not depend on a renderer existing, the palette's wind and LOD blocks are
render tuning that the renderer has since re-tuned in its own constants, and
`plantable_in_scene` is gated by `tools/validate.py` on every run. The routes are
written up in `docs/ROADMAP.md` K42. This measures, holds and prints.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RENDERER = ROOT / "renderers" / "web" / "js"
BASELINE = ROOT / "tools" / "layer_reads_baseline.json"

# T-1029. The layers whose banked record COUNTS are a dated tally rather than a held
# number. `data/residents/` is the one layer this project is still writing — cards are
# minted, folded and merged most weeks — so every one of its 61 banked paths moves for a
# reason that has nothing to do with what this file asserts. `data/flora/` and
# `data/fauna/` are finished research datasets: their counts have not moved since the
# day they were banked, and a move there IS a finding.
COUNTS_NOT_HELD = {"residents"}

# The renderer, minus the two files that are not renderer code: the changelog is
# authored prose that happens to be JavaScript (and quotes field names by the
# dozen), and vendored three.js is not ours to reason about.
RENDERER_SKIP = ("changelog.js",)

# Identity, file routing, provenance and prose. Not figures, so not the gate's
# business — the same strip `compile_scene.ground_fields` does before the
# ground's geometry check sees a claim. A path declared in READS outranks this.
MACHINERY_LEAVES = frozenset({
    # `_merged_doc` joined these two under T-1233. It is the redirect table's own
    # prose, addressed to a reader of the JSON and to the consumers that resolve a
    # folded id — the same kind of key as the two beside it, and classified with them
    # rather than banked as a figure a card is withholding.
    "_doc", "_researched_not_resident_doc", "_merged_doc",
    "id", "zone", "file", "version", "scene_date", "dossier", "sources",
    "note", "name", "binomial", "synonym", "review_required", "palette",
    "species_count", "confidence", "reads_as",
})

# Leaves whose bare name is also the renderer's own vocabulary, so the reverse
# scan of assertion 3 would fire on code that has nothing to do with the record.
# Scanned parent-qualified instead — to read `ground.rgb` out of a palette the
# renderer has to touch `ground` first. One entry, because the layer rule below
# removes the need for the rest.
AMBIGUOUS_LEAVES = frozenset({
    "rgb",        # `diffuseColor.rgb` is a three.js shader field, in four files
    "min", "max", # generic range/math leaves; require their data parent to match
    # T-1238's `associated_with[]` rows. `from` and `to` are the two ends of a
    # dated relationship and `tier` its confidence, and all three are words the
    # renderer already owns — a documented range has a `.from`, the tier ladder
    # is read straight off the structure records. A bare-name scan attributes
    # those accesses to the new rows and calls them phantoms. The rows have a
    # data parent to qualify them with, which is what this set is for, so the
    # scan is narrowed rather than exempted: the day a renderer really does read
    # `associated_with` it declares the expression and never reaches here.
    "from", "to", "tier",
    # T-1254's `roles[].claim`. `claim` is this renderer's oldest word: every graded
    # structure attribute is a claim, `popup.js` and the Evidence panel read `.claim` on
    # things that have nothing to do with a resident's trade, and a role's claim id sat
    # null on every card until the external volumes were migrated. The moment it carried
    # a value the bare-name scan attributed all of that to it. Same shape as the three
    # above and the same narrowing: qualified by its data parent, so the day the people
    # view really does read a role's claim id (T-1255) it declares the expression and
    # never reaches here.
    "claim",
    # T-1313's `persons[].stated_family.statement`. `statement` is a word this renderer
    # already owns twice over: `orderbook.js` prints `d.statement` and `i.statement` off
    # the reconstruction order book's own disagreement rows, which are not a resident
    # layer figure at all. A bare-name scan attributed that read to the marker the
    # stated-family pass writes, and called an unread provenance key a phantom. Same
    # shape as the four above and the same narrowing rather than an exemption: qualified
    # by its data parent, so the day a card really does print which STATEMENT seated a
    # wife it declares `stated_family.statement` and never reaches here.
    "statement",
    # T-1144's `present_on_scene_date.last_dated_appearance.record`. `record` is a word
    # this renderer has used from the start for the thing a popup is showing —
    # `hit.record`, `z.record`, `task.record.id`, `boat.record` — none of which is a
    # resident's evidence row id. A bare-name scan attributes all of it to the presence
    # leg's audit pointer and calls it a phantom read. Same shape and same narrowing as
    # the four above: the pointer has a data parent to qualify it with, so the day the
    # card really does print the row a leg came from it declares the expression and
    # never reaches here.
    "record",
    # T-1304's `vocabulary.age_bands[].age_band`. The profile report's vocabulary names
    # each age RULE — `birth_year_known`, `adult_by_civic_list` — under the key
    # `age_band`, and the card reads a PERSON's `age_band` block, which is a different
    # thing with the same word. A bare-name scan hands the card's reads to the vocabulary
    # row and calls it a phantom. Qualified by its data parent, like the four above.
    "age_band",
})

# Unread leaves the reverse scan of assertion 3 cannot attribute, STATED rather
# than proven — the same admission the derived `shared` list makes, for names the
# derivation cannot reach because the collision is not with another DECLARED leaf.
# A scan that cannot fail honestly is worse than a stated exemption, so each one
# says here what it collides with and stays in the unread bank either way.
STATED_SHARED = frozenset({
    # `counts.households` is the manifest's own tally. `index.households` is the
    # list the panel renders, and it is read — one `.households` in the renderer,
    # two figures in the data, and no text scan can say which one it touched.
    "households",
    # The head-of-household name. `sp.head` is flora.js's flower head, in nine
    # expressions across the sward, so a bare `.head` is the renderer's own
    # vocabulary; and a top-level leaf has no parent to qualify it with.
    "head",
    # The manifest's denormalised copy of the household's presence claim. The
    # RECORD's `present_on_scene_date` block is read and shown by residents.js;
    # the manifest's copy of it is read by nothing, and the two are the same word.
    "present_on_scene_date",
    # `as_printed`, `from` and `to` WERE here. T-1229's dated roles held all three and
    # nothing read any of them, and a bare-name scan could not say so: `.from`/`.to`
    # are this renderer's own vocabulary for a span — boats.js and frontage.js index
    # face ranges with them, popup.js prints a documented range and facades.js ages a
    # wall — and `as_printed` is the corpus-wide word for a source's own wording, read
    # on name variants. T-1255 put the dated timeline on the card, so all three are
    # declared reads below on `persons[].roles[]` and no `.from`, `.to` or
    # `as_printed` leaf is left in the unread bank for the exemption to cover. It goes
    # rather than being kept as a courtesy, for the reason the `source` exemption went
    # with T-0668: a stated share is an admission the scan cannot attribute an access,
    # and these it can.
    # These seven WERE here: they occur in the separately rendered research_pilot
    # payload as well as in the record's own `resident_research` block, and while the
    # embedded block was unread a bare-name scan could not attribute an access to one
    # of the two. T-1233 wired the embedded block, so all seven are declared reads
    # below and the exemption covers nothing. It goes rather than being kept as a
    # courtesy, for the reason the `source` exemption went with T-0668: a stated share
    # is an admission the scan cannot attribute an access, and these it can.
    # `source` WAS here: the volume each row of a T-0514 evidence block resolves
    # to, with the only `.source` in the renderers being main.js:1808's keyboard
    # event. T-0668 put the blocks on the card, so `citationsById.get(entry.source)`
    # is now a resident read and the five paths are declared shown below. The
    # exemption is gone rather than kept as a courtesy: a stated share is an
    # admission the scan cannot attribute an access, and this one it can.
})

# ---------------------------------------------------------------------------
# THE MAP. Every declaration is `path -> (state, expression)`, and every
# expression is scanned against the renderer with comments stripped. The paths
# are the ones `field_paths()` produces: a leaf under a list of records is
# `species[].height_m`.
# ---------------------------------------------------------------------------

FLORA_ZONE_READS: dict[str, tuple[str, str]] = {
    # How much of the ground a community's matrix covers. Authored per zone,
    # read as a probability directly — the one zone-level figure that changes
    # how many plants stand.
    "cover.matrix_fraction": ("mesh", "cover.matrix_fraction"),
    # Read, and its only consumer is the `zones()` accessor the smoke's sward
    # gate reads. No plant is placed or withheld by it.
    "cover.bare_soil_fraction": ("probe", "cover.bare_soil_fraction"),
    # T-1056 — WHERE THE WOODY STRATUM ESTABLISHES. Two renderers read this one
    # block off the same record: `flora.js`'s `station` withholds a `shrub_low`
    # below the band, and `trees.js`'s planting loop withholds the dune poplars.
    # Both are `mesh` — they change what stands on the ground, which is the
    # strongest claim this map makes about a figure.
    #
    # `woody_stratum.measured_from` is deliberately NOT here and is banked
    # unread: it states what the metres are measured from, for the reader and for
    # `tools/validate.py`, and a renderer that read it would be a renderer that
    # could convert between datums. If it ever disagreed with the heightfield's
    # own datum the right outcome is this gate failing, not a silent conversion.
    "woody_stratum.establishes_m": ("mesh", "const band = w.establishes_m;"),
    "woody_stratum.applies_to_roles": ("mesh", "new Set(w.applies_to_roles ?? [])"),
    # The extent decides WHERE a community stands, which is a position and
    # therefore a vertex. `x` is the extent object inside `matchZone`.
    "extent.kind": ("mesh", "switch (x.kind)"),
    "extent.elev_m": ("mesh", "Array.isArray(x.elev_m)"),
    "extent.polygon": ("mesh", "pointInPolygon(x.polygon, e, n)"),
    "extent.box.e": ("mesh", "const be = x.box.e;"),
    "extent.box.n": ("mesh", "const bn = x.box.n;"),
    "extent.of": ("mesh", "if (x.of !== 'water') return false;"),
    "extent.distance_m": ("mesh", "x.distance_m ?? [0, 0]"),
    "extent.exclude_polygons": ("mesh", "x.exclude_polygons ?? []"),
    # Ground a community holds that its own extent rule cannot reach — the mirror
    # of the exclusions above. z03's evidence names the public square and its rule
    # is an elevation band that cannot find a block the terrain draws flat.
    "extent.include_polygons": ("mesh", "x.include_polygons ?? []"),
    "extent.priority": ("mesh", "rec.extent?.priority"),
    # Per species.
    "species[].role": ("mesh", "OUR_ROLES.has(sp.role)"),
    "species[].form": ("mesh", "GRASS_SHAPE[sp.form]"),
    "species[].height_m": ("mesh", "const h = sp.height_m;"),
    "species[].width_m": ("mesh", "Array.isArray(sp.width_m) ? sp.width_m : null"),
    "species[].substrate": ("mesh", "const declared = sp.substrate;"),
    "species[].abundance.cover_fraction": ("mesh", "mid(ab.cover_fraction)"),
    "species[].abundance.density_per_ha": ("mesh", "mid(ab.density_per_ha)"),
    "species[].abundance.stems_per_m2": ("mesh", "mid(ab.stems_per_m2)"),
    "species[].july.phenology": ("mesh", "july.phenology === 'vegetative'"),
    "species[].july.foliage_rgb": ("mesh", "rgb(july.foliage_rgb)"),
    "species[].july.foliage_rgb_alt": ("mesh", "rgb(july.foliage_rgb_alt)"),
    "species[].july.inflorescence.shape": ("mesh", "HEAD_OF_SHAPE[inflor.shape]"),
    "species[].july.inflorescence.rgb": ("mesh", "rgb(inflor.rgb)"),
    "species[].july.inflorescence.height_frac": ("mesh", "inflor.height_frac ?? 0.9"),
    "species[].july.inflorescence.size_m": ("mesh", "Array.isArray(inflor.size_m)"),
    # A provenance grade everywhere else in this project, and a colour here: the
    # confidence view tints every plant by its species' evidence.
    "species[].confidence": ("mesh", "LEVEL[sp.confidence]"),
    # trees.js shows the July note and the common name in the timber panel.
    "species[].july.appearance": ("shown", "sp.july?.appearance"),
    "species[].common": ("shown", "sp.common ?? base.common"),
    # T-0281 — the plants section of the Evidence panel. These two were banked as
    # reaching nothing and are read by `renderers/web/js/plants.js` now, which is
    # this census doing exactly what it is for: the commit that wires a figure up
    # is the commit that reclassifies it. Both are `shown` and neither is `mesh` —
    # nothing here changes what is planted, it changes what a visitor can read
    # about what is planted.
    "cover.standing_water_fraction": ("shown", "cover.standing_water_fraction"),
    # Three of the ten communities have no modelled ground in this scene, and the
    # card says so rather than listing them as though a visitor could walk to
    # them. Still gated by validate.py; it is now also read.
    "plantable_in_scene": ("shown", "zone.plantable_in_scene ?? entry.plantable_in_scene"),
}

FLORA_MANIFEST_READS: dict[str, tuple[str, str]] = {
    # The manifest's extent is a denormalised copy read as a whole-object
    # fallback — `rec.extent ?? entry.extent` — so its leaves reach the same
    # matcher as the zone record's. validate.py holds the two copies equal.
    "zones[].extent.kind": ("mesh", "rec.extent ?? entry.extent"),
    "zones[].extent.elev_m": ("mesh", "rec.extent ?? entry.extent"),
    "zones[].extent.polygon": ("mesh", "rec.extent ?? entry.extent"),
    "zones[].extent.box.e": ("mesh", "rec.extent ?? entry.extent"),
    "zones[].extent.box.n": ("mesh", "rec.extent ?? entry.extent"),
    "zones[].extent.of": ("mesh", "rec.extent ?? entry.extent"),
    "zones[].extent.distance_m": ("mesh", "rec.extent ?? entry.extent"),
    "zones[].extent.exclude_polygons": ("mesh", "rec.extent ?? entry.extent"),
    "zones[].extent.include_polygons": ("mesh", "rec.extent ?? entry.extent"),
    "zones[].extent.priority": ("mesh", "entry.priority ?? 0"),
    "zones[].priority": ("mesh", "entry.priority ?? 0"),
    # T-1055. The ground mesh paints a zone with box extent its own recorded
    # colour: terrain.js `substrateZones()` takes these two copies off the
    # manifest and `zoneGlsl()` multiplies the prairie tile's luminance
    # through them, so the mean albedo inside the zone is the recorded
    # triple. They were banked unread for as long as the mesh was one
    # material, which is why the beach and the sand bar were drawn green.
    "zones[].ground_rgb": ("mesh", "z.ground_rgb"),
    "zones[].ground_wet_rgb": ("mesh", "z.ground_wet_rgb"),
    # Read once at boot, to report a published shape this renderer has no
    # archetype for. Nothing is drawn from the list itself.
    "vocabulary.inflorescence_shapes": ("probe", "index.vocabulary?.inflorescence_shapes"),
    # T-0281. The manifest's closed sets are shown to a visitor under "the words
    # on these cards", which is the wildlife section's argument (K51) applied to
    # the plants: every chip on every card comes out of one of these lists, and a
    # word the renderer invented would be a gloss the dataset never agreed to. So
    # the lists are the dataset's own, and showing them is how that stays true.
    "vocabulary.roles": ("shown", "rank(vocab.roles, a.role)"),
    "vocabulary.substrates": ("shown", "vocab.substrates"),
    "vocabulary.forms_flora": ("shown", "vocab.forms_flora"),
    "vocabulary.forms_trees": ("shown", "vocab.forms_trees"),
    # The community's own claim about whether it stands anywhere in this scene.
    "zones[].plantable_in_scene": ("shown", "zone.plantable_in_scene ?? entry.plantable_in_scene"),
}

FLORA_PALETTE_READS: dict[str, tuple[str, str]] = {
    "greens": ("mesh", "palette?.greens"),
    "dry_accent": ("mesh", "rgb(palette?.dry_accent)"),
}

# data/fauna HAS a reader as of ROADMAP K51, and every figure in it is `shown`.
#
# This block used to read "data/fauna has no reads at all", and assertion 3a was
# written to fail the moment that stopped being true — because the whole of this
# layer's unread bank rested on nobody opening the directory. That is the gate
# working: `renderers/web/js/fauna.js` opens it, so the bank had to be discharged
# figure by figure in the same commit rather than left standing behind a sentence
# that had quietly expired.
#
# Every one of the thirty is `shown` and none is `mesh`: no animal is drawn in
# this scene, and a state that said otherwise would be this map making a claim
# about the town. `shown` is the honest word for a value a visitor reads on a
# card, and the Evidence panel's wildlife section is a card.
FAUNA_ZONE_READS: dict[str, tuple[str, str]] = {
    # Which habitat this is, and whether its ground is drawn here at all. Two of
    # the ten have no modelled extent in this scene and the card says so — a list
    # that read the same either way would be a claim about the town.
    "habitat": ("shown", "words(zone.habitat)"),
    "in_modelled_extent": ("shown", "zone.in_modelled_extent"),
    # A fauna zone carries no geometry of its own: it names the plant community
    # whose extent it shares, which is what stops the two datasets drifting.
    "extent_from.flora_zone": ("shown", "zone.extent_from?.flora_zone"),
    "extent_from.kind": ("shown", "zone.extent_from?.kind"),
    # July is the quietest wildlife date in the Chicago year, and the soundscape
    # block is where each habitat says so in its own terms.
    "soundscape.dawn_chorus": ("shown", "zone.soundscape?.dawn_chorus"),
    "soundscape.hero": ("shown", "zone.soundscape?.hero"),
    # The animal, as a visitor reads it.
    "species[].common": ("shown", "sp.common || sp.id"),
    "species[].class": ("shown", "rank(vocab.classes, a.class)"),
    "species[].activity": ("shown", "words(sp.activity)"),
    "species[].active_periods": ("shown", "sp.active_periods"),
    # The three graded claims, each named at its call site so this scan can see
    # it — see the note on `claimRow` for why they are not dug out of the claim.
    "species[].july.status.value": ("shown", "july.status?.value"),
    "species[].july.presence.value": ("shown", "july.presence?.value"),
    "species[].july.abundance.value": ("shown", "july.abundance?.value"),
    "species[].july.vocalization": ("shown", "words(july.vocalization)"),
    "species[].july.behaviour": ("shown", "row('On 1 July', july.behaviour)"),
    "species[].july.appearance": ("shown", "july.appearance"),
    "species[].july.max_group": ("shown", "Number.isFinite(july.max_group)"),
    # On eight records only: an animal present as sign alone still has something
    # to show a visitor, and `presence: trace_only` is meaningless without it.
    "species[].july.trace": ("shown", "row('Sign it leaves', july.trace)"),
}

FAUNA_MANIFEST_READS: dict[str, tuple[str, str]] = {
    # The manifest's copies are denormalised on purpose — `tools/validate.py`
    # fails the build if they disagree with the zone record — and the renderer
    # reads them where a zone record is silent. One expression covers the three
    # because one line does.
    "zones[].habitat": ("shown", "zone.habitat ?? entry.habitat"),
    "zones[].in_modelled_extent": ("shown", "zone.in_modelled_extent ?? entry.in_modelled_extent"),
    "zones[].extent_from.flora_zone": ("shown", "zone.extent_from ?? entry.extent_from"),
    "zones[].extent_from.kind": ("shown", "zone.extent_from ?? entry.extent_from"),
    # The eight closed sets. Each is BOTH the order a list is sorted into and the
    # list a visitor is shown under "the words on these cards" — a gloss invented
    # in the renderer would be a vocabulary the dataset never agreed to.
    "vocabulary.habitats": ("shown", "rank(vocab.habitats, a.habitat)"),
    "vocabulary.classes": ("shown", "vocab.classes"),
    "vocabulary.presence_modes": ("shown", "vocab.presence_modes"),
    "vocabulary.july_status": ("shown", "vocab.july_status"),
    "vocabulary.abundance": ("shown", "vocab.abundance"),
    "vocabulary.vocalization": ("shown", "vocab.vocalization"),
    "vocabulary.activity": ("shown", "vocab.activity"),
    "vocabulary.active_periods": ("shown", "rank(vocab.active_periods, a)"),
}

# data/residents — ROADMAP K52, ticket T-0021. Two readers, so two routes, and
# the map does not distinguish them because the scan is over the renderer as one
# text: `residents.js` fetches the manifest and then a household record per row a
# visitor opens, and `popup.js` reads the denormalised copy `compile_scene.py`
# puts in a building's sidecar. A figure read by either has reached a visitor.
#
# NOTHING HERE IS `mesh`, and nothing here ever will be. docs/LIBERTIES.md L1 and
# AGENTS.md's standing constraint hold: v1 draws no human figures, so no figure of
# a person moves a vertex in this scene. `shown` is the whole of the read side,
# and a state that said otherwise would be this map making a claim about the town.
RESIDENTS_MANIFEST_READS: dict[str, tuple[str, str]] = {
    # The count sentence under the section heading, and the layer's own grade
    # tally inside it — how many of this town's people a source names, how many
    # are real people partly reconstructed, and how many are hypotheses. The
    # census of T-0021 found the tally reaching nothing behind the sentence
    # "every one of them graded", which is true and says nothing.
    "counts.persons": ("shown", "counts.persons ?? entries.reduce"),
    "counts.by_grade.attested": ("shown", "${byGrade.attested} named by a source"),
    "counts.by_grade.inferred": ("shown", "${byGrade.inferred} real people whose"),
    "counts.by_grade.reconstructed": ("shown", "${byGrade.reconstructed} hypothesised to"),
    # The evidence-strength tally beside the grade tally, and it is a different
    # axis from both of the others: `grade` says how much of a PERSON is
    # reconstructed, and this says how thin the source is that names them at all.
    # A name on the post office's list of uncalled-for letters and a shopkeeper
    # who advertised his stock are both `attested` and are not the same claim
    # (T-0378), so the count sentence says how many of the people listed are the
    # first kind.
    "counts.letter_list_only": ("shown", "counts.letter_list_only"),
    # T-0491. Three of these people are bridged to a named head of household in the
    # 1840 census, and PR #670 attached that bridge without giving the panel any way
    # to say so. Both copies are read now: the total in the count sentence, so a
    # reader sees how few there are before opening anything, and the per-row tally
    # as a chip, so which rows they are costs no fetch. The bridge itself is on the
    # person's card, argument and all — see `persons[].later_census.*` below.
    "counts.census_1840_linked": ("shown", "counts.census_1840_linked"),
    "households[].census_1840_linked": ("shown", "entry.census_1840_linked"),
    # T-0379. The owner ruled that every letter-list name the evidence admits joins
    # the town, which made this cohort most of the people in it, so the section is
    # SPLIT on this flag rather than sorted by it: the households the rest of the
    # corpus documents keep the list they had, and the letter-list rows sit under
    # them in one closed group. The flag is on the manifest row so that split costs
    # one pass over a file the panel already has, rather than a fetch per household
    # or a renderer that reads a mint tool's id prefix.
    "households[].letter_list_only": ("shown", "entries.filter((e) => e.letter_list_only)"),
    # One row per household: which division it stands in, how many people it
    # holds, and its grade tally as chips.
    "households[].division": ("shown", "words(entry.division)"),
    "households[].persons": ("shown", "entry.persons === 1"),
    "households[].grades.attested": ("shown", "(grades || {})[g]"),
    "households[].grades.inferred": ("shown", "(grades || {})[g]"),
    # The third chip. It was absent from this map for as long as the tally was zero
    # everywhere; T-1314 put people back under the grade and `gradeChips` has always
    # drawn all three from one expression.
    "households[].grades.reconstructed": ("shown", "(grades || {})[g]"),
    # The finding the section was built to carry: a household with neither
    # residence nor workplace attested reaches no building sidecar, so these two
    # copies are what puts "on no building card" on the row.
    "households[].lives_at": ("shown", "Boolean(entry.lives_at || entry.works_at)"),
    "households[].works_at": ("shown", "Boolean(entry.lives_at || entry.works_at)"),
    # The researched-and-not-a-resident list — the exclusions-style half.
    "researched_not_resident[].name": ("shown", "e.name || e.id"),
    "researched_not_resident[].category": ("shown", "words(e.category)"),
    "researched_not_resident[].reason": ("shown", "row('Why not a household here', e.reason)"),
    "researched_not_resident[].note": ("shown", "escapeHtml(e.note)"),
    # The closed sets, shown rather than paraphrased — a gloss invented in the
    # renderer would be a vocabulary the dataset never agreed to. `presence` is
    # declared at its call site because `vocab.presence` is a prefix of fauna's
    # `vocab.presence_modes`, and an expression that matches another layer's line
    # proves nothing about this one.
    "vocabulary.grades": ("shown", "vocab.grades"),
    "vocabulary.presence": ("shown", "['Here on the scene date', vocab.presence]"),
    "vocabulary.divisions": ("shown", "rank(vocab.divisions, a.division)"),
    "vocabulary.arrival_precision": ("shown", "vocab.arrival_precision"),
    "vocabulary.relationships": ("shown", "vocab.relationships"),
    # T-0597. The second relationship set, and it exists because a place INSIDE a
    # household and a tie BETWEEN two households are different questions. The
    # degrees are the whole point of showing it: a reader who cannot see that
    # `half_brother` and `brother` are both in the closed set cannot see that the
    # dataset holds them apart.
    "vocabulary.kin_relations": ("shown", "['Ties between two households', vocab.kin_relations]"),
    # Shown because the value it governs is shown: `persons[].sex` is on every
    # person's card and this was the one closed set the panel withheld.
    "vocabulary.sexes": ("shown", "['Sex, as the records give it', vocab.sexes]"),
    "vocabulary.occupations": ("shown", "vocab.occupations"),
    # T-0668. The ratified grading ladder, carried in the manifest because the card
    # prints a rung id beside a person's grade and the rung's text lived in Python.
    # `tools/consolidate_resident_evidence.py --check` holds this block equal to its
    # own `GRADE_RULES`, so the words on 531 cards cannot drift from the ladder.
    "vocabulary.ladder_rules[].rung": ("shown", "(ladderRules || []).find((r) => r.rung"),
    "vocabulary.ladder_rules[].grade": ("shown", "swatch(rung && rung.grade)"),
    "vocabulary.ladder_rules[].rule": ("shown", "rung ? escapeHtml(rung.rule)"),
    # The consolidation's own mint, on the manifest: the tally in the count
    # sentence, and the per-household flag as a chip on the closed row. Both were
    # banked unread, and both collide by leaf name with `persons[].civic_mint`,
    # which is why they are shown rather than exempted.
    "counts.civic_mint": ("shown", "${counts.civic_mint} of these people were minted"),
    "households[].civic_mint": ("shown", "entry.civic_mint"),
}

RESIDENTS_HOUSEHOLD_READS: dict[str, tuple[str, str]] = {
    # The household's own name, on the building card. `residents.js` labels its
    # rows off the id; this is `popup.js` and the Go-to search, through the
    # sidecar copy.
    "name": ("shown", "households.map((h) => h.name)"),
    # The seven graded claims. Each `value` is named at its own call site — a
    # figure dug out inside a generic accessor is a figure this census cannot
    # see in the file's text — and the three parts every claim block shares
    # (`confidence`, `note`) are read once, in `claimRow`, so one expression
    # covers them all because one line does.
    "arrival.value": ("shown", "(hh.arrival || {}).value"),
    "arrival.precision": ("shown", "words((hh.arrival || {}).precision)"),
    # T-1169. The year the household is CARRIED at, beside the bound its arrival block
    # holds: for 1,196 households `arrival` is a `not_later_than` and says only that
    # somebody was here by a date. Its own row on the card, its own claim block.
    "arrival_year.value": ("shown", "(hh.arrival_year || {}).value"),
    "arrival_year.confidence": ("shown", "tierOf(block) || block.confidence"),
    "arrival_year.note": ("shown", "escapeHtml(block.note)"),
    "party_size_on_arrival.value": ("shown", "party && party.value"),
    "origin.value": ("shown", "(hh.origin || {}).value"),
    "reason_for_coming.value": ("shown", "(hh.reason_for_coming || {}).value"),
    "lives_at.value": ("shown", "(hh.lives_at || {}).value"),
    "works_at.value": ("shown", "(hh.works_at || {}).value"),
    "present_on_scene_date.value": ("shown", "(hh.present_on_scene_date || {}).value"),
    # T-1144 acceptance 9. The dated evidence leg under an `uncertain` presence — the
    # last day the corpus can still see this person — has its own row on the card,
    # `presenceLegRow`, and the row's whole job is to keep a date from reading as a
    # sighting when it is not one. So each of the five figures it turns on is named at
    # the line that reads it: the date as the source printed it, which of the three
    # kinds of leg it is, how exact the reading was, the latest day it can mean, and
    # how far short of the scene date that falls.
    "present_on_scene_date.last_dated_appearance.as_read":
        ("shown", "escapeHtml(leg.as_read)"),
    "present_on_scene_date.last_dated_appearance.leg":
        ("shown", "escapeHtml(kind || leg.leg)"),
    "present_on_scene_date.last_dated_appearance.precision":
        ("shown", "leg.precision] || leg.precision"),
    "present_on_scene_date.last_dated_appearance.reaches":
        ("shown", "reaching ${leg.reaches}"),
    "present_on_scene_date.last_dated_appearance.includes_scene_date":
        ("shown", "leg.includes_scene_date"),
    "present_on_scene_date.last_dated_appearance.days_before_scene_date":
        ("shown", "${leg.days_before_scene_date}"),
    # T-1158. The chip the card draws is the TIER now, and `confidence` is what the
    # tier is derived from — `tierOf(block)` reads it, and falls back to the raw
    # confidence for a block whose shape predates the four-tier vocabulary. The
    # declaration names that line rather than the `swatch()` call, because that line is
    # where the field is actually read.
    "arrival.confidence": ("shown", "tierOf(block) || block.confidence"),
    "party_size_on_arrival.confidence": ("shown", "tierOf(block) || block.confidence"),
    "origin.confidence": ("shown", "tierOf(block) || block.confidence"),
    "reason_for_coming.confidence": ("shown", "tierOf(block) || block.confidence"),
    "lives_at.confidence": ("shown", "tierOf(block) || block.confidence"),
    "works_at.confidence": ("shown", "tierOf(block) || block.confidence"),
    "present_on_scene_date.confidence": ("shown", "tierOf(block) || block.confidence"),
    # The reasoning, and on this layer it is the point: a note here routinely
    # says the record is NOT attested and why the figure is carried anyway.
    "arrival.note": ("shown", "escapeHtml(block.note)"),
    "party_size_on_arrival.note": ("shown", "escapeHtml(block.note)"),
    "origin.note": ("shown", "escapeHtml(block.note)"),
    "reason_for_coming.note": ("shown", "escapeHtml(block.note)"),
    "lives_at.note": ("shown", "escapeHtml(block.note)"),
    "works_at.note": ("shown", "escapeHtml(block.note)"),
    "present_on_scene_date.note": ("shown", "escapeHtml(block.note)"),
    # T-1158's own fields, on the three claims T-1169's stage fills. `tier` drives the
    # chip through the same `tierOf` line the confidences above name; the rest are read
    # in `basisHtml`, which opens a disclosure under any invented value saying whether
    # it was DRAWN from a model or ARGUED from a rule, printing the seed that redraws
    # it and the evidence that would retire it. `replaceable_by.kind` and
    # `written_by_stage` are NOT read — the first is the shape of the replacement
    # record and the second is the build's own bookkeeping — and they stay banked.
    "arrival_year.tier": ("shown", "tierOf(block) || block.confidence"),
    "origin.tier": ("shown", "tierOf(block) || block.confidence"),
    "reason_for_coming.tier": ("shown", "tierOf(block) || block.confidence"),
    "arrival_year.basis.kind": ("shown", "basis.kind === 'model'"),
    "origin.basis.kind": ("shown", "basis.kind === 'model'"),
    "reason_for_coming.basis.kind": ("shown", "basis.kind === 'model'"),
    "arrival_year.seed": ("shown", "escapeHtml(String(block.seed))"),
    "origin.seed": ("shown", "escapeHtml(String(block.seed))"),
    "arrival_year.replaceable_by.match": ("shown", "escapeHtml(String(rep.match || ''))"),
    "origin.replaceable_by.match": ("shown", "escapeHtml(String(rep.match || ''))"),
    "reason_for_coming.replaceable_by.match": (
        "shown", "escapeHtml(String(rep.match || ''))"),
    # T-0597. The kinship rows, which are the first claim on this layer to point at
    # ANOTHER record. Each of the four link fields is named at its own call site in
    # `kinRows` — the person the tie belongs to here, the term, the far household and
    # the far person — for the same reason the seven graded claims are: a figure dug
    # out inside a generic accessor is a figure this census cannot see. The three
    # parts the block shares with every other claim are read in `claimRow`, once.
    "kin[].person": ("shown", "${words(k.person)} is the"),
    "kin[].relation": ("shown", "the ${words(k.relation)} of"),
    "kin[].value": ("shown", "${words(k.value)}, "),
    "kin[].household": ("shown", "words(String(k.household ?? '').replace(/^hh_/, ''))"),
    "kin[].confidence": ("shown", "tierOf(block) || block.confidence"),
    "kin[].note": ("shown", "escapeHtml(block.note)"),
    # T-0632. The later directories, on the record rather than only beside it. The
    # printed lines and the crosswalks' arithmetic stay in
    # `data/residents/directories.json`, which the panel opens once for the town; what
    # the RECORD carries is the claim — a trade or an address a Chicago directory of
    # 1839, 1843 or 1844 prints against this person, graded, dated to the year it
    # describes and citing the volume. `note` and `sources` are the household's own
    # statement of what a later volume is worth and which ones met it.
    "directories.note": ("shown", "escapeHtml(onRecord.note)"),
    "directories.sources": ("shown", "escapeHtml((onRecord.sources || []).join(', '))"),
    "directories.people[].person_id": (
        "shown", "(directoriesOnRecord || []).find((row) => row.person_id === person.id)"),
    "directories.people[].occupation_later.value": (
        "shown", "one(block.occupation_later, 'A trade printed against this name')"),
    "directories.people[].address_later.value": (
        "shown", "one(block.address_later, 'An address printed against this name')"),
    # The three parts every claim block here shares are read once, in `laterClaimHtml`,
    # so one expression covers each of them for both claims — the same economy the seven
    # graded claims above are declared with.
    "directories.people[].occupation_later.confidence": ("shown", "swatch(claim.confidence)"),
    "directories.people[].address_later.confidence": ("shown", "swatch(claim.confidence)"),
    "directories.people[].occupation_later.describes_date": (
        "shown", "escapeHtml(String(claim.describes_date))"),
    "directories.people[].address_later.describes_date": (
        "shown", "escapeHtml(String(claim.describes_date))"),
    "directories.people[].occupation_later.note": ("shown", "escapeHtml(claim.note)"),
    "directories.people[].address_later.note": ("shown", "escapeHtml(claim.note)"),
    "directories.people[].occupation_later.sources": (
        "shown", "(claim.sources || []).map((id) => citationsById.get(id))"),
    "directories.people[].address_later.sources": (
        "shown", "(claim.sources || []).map((id) => citationsById.get(id))"),
    # T-0633. What was DONE with the later address, which is the half a reader
    # cannot check from the address alone: the outcome, the clause that decided
    # it, the face it earned and the years it was carried. All 87 render,
    # refusals included — `backProjectionHtml` has no branch that drops one.
    "directories.people[].back_projection.outcome": (
        "shown", "bp.outcome === 'placed'"),
    "directories.people[].back_projection.clause": (
        "shown", "escapeHtml(String(bp.clause))"),
    "directories.people[].back_projection.value": ("shown", "escapeHtml(where)"),
    "directories.people[].back_projection.confidence": ("shown", "swatch(bp.confidence)"),
    "directories.people[].back_projection.placement": (
        "shown", "words(bp.placement)"),
    "directories.people[].back_projection.position_local_enu_m": (
        "shown", "(bp.position_local_enu_m || []).join(', ')"),
    "directories.people[].back_projection.describes_date": (
        "shown", "escapeHtml(String(bp.describes_date))"),
    "directories.people[].back_projection.read_back_years": (
        "shown", "escapeHtml(String(bp.read_back_years))"),
    "directories.people[].back_projection.note": ("shown", "escapeHtml(bp.note)"),
    # T-0669, the residence half of the same grammar, on its own row of the same
    # card. `residenceBackProjectionHtml` has no branch that drops one either, so
    # all 48 render — the 7 placements and the 41 refusals — and `kind` is the one
    # leaf the business row has no counterpart for: whether the volume printed
    # `res` or `bds` is the difference between a household and a month's rent.
    "directories.people[].residence_back_projection.outcome": (
        "shown", "rp.outcome === 'placed'"),
    "directories.people[].residence_back_projection.clause": (
        "shown", "escapeHtml(String(rp.clause))"),
    "directories.people[].residence_back_projection.kind": (
        "shown", "rp.kind === 'boards' ? 'printed as a lodging' : 'printed as a residence'"),
    "directories.people[].residence_back_projection.value": (
        "shown", "`${rp.value} — the ${words(rp.placement)}, and nothing narrower`"),
    "directories.people[].residence_back_projection.confidence": (
        "shown", "swatch(rp.confidence)"),
    "directories.people[].residence_back_projection.placement": (
        "shown", "words(rp.placement)"),
    "directories.people[].residence_back_projection.describes_date": (
        "shown", "escapeHtml(String(rp.describes_date))"),
    "directories.people[].residence_back_projection.read_back_years": (
        "shown", "escapeHtml(String(rp.read_back_years))"),
    "directories.people[].residence_back_projection.note": (
        "shown", "escapeHtml(rp.note)"),
    "directories.people[].residence_back_projection.sources": (
        "shown", "(rp.sources || []).map((id) => citationsById.get(id))"),
    # The standing constraint, on the record that touches it.
    "touches_removal": ("shown", "hh.touches_removal"),
    "research_note": ("shown", "hh.research_note"),
    # T-0660's ruling (c). Refusals 7 and 8 are mint-time rules: where one lands on a
    # card that already stands, the pass keeps the record and SAYS the collision on it
    # instead of retiring anybody. Saying it to a TOOL and not to a reader would be
    # half the ruling — "so a reader sees the collision and why both records are
    # there" is its own wording — so the row is on the card, under the family name it
    # shares. The note is the reasoning and the other three are the figures.
    "surname_collision.refusal": ("shown", "escapeHtml(hh.surname_collision.refusal)"),
    "surname_collision.holds_the_surname": (
        "shown", "(hh.surname_collision.holds_the_surname || []).join('; ')"),
    "surname_collision.ruling": ("shown", "escapeHtml(hh.surname_collision.ruling)"),
    # The person. `grade` is how much of the PERSON is reconstructed and the
    # occupation's `confidence` is how well that one attribute is evidenced; the
    # manifest is emphatic that the two axes must not be conflated, and they are
    # two chips here for the same reason.
    "persons[].name": ("shown", "escapeHtml(person.name || 'unnamed')"),
    "persons[].grade": ("shown", "swatch(person.grade)"),
    "persons[].relationship": ("shown", "words(person.relationship)"),
    "persons[].sex": ("shown", "words(person.sex)"),
    # T-1303. Where the sex was READ rather than recorded, the row is a graded claim and
    # carries the rule that fired — a gendered title, or a forename that stands in one
    # sex's naming only. `confidence` and `note` go through `claimRow` with every other
    # block; `value` is what the row prints.
    "persons[].sex_basis.value": ("shown", "claimRow('Sex', words(basis.value)"),
    "persons[].sex_basis.confidence": ("shown", "tierOf(block) || block.confidence"),
    "persons[].sex_basis.note": ("shown", "escapeHtml(block.note)"),
    # T-1304. THE SAME ROW, ONE TIER DOWN, AND THAT IS THE POINT. A sex the model DREW
    # goes through `claimRow` exactly as a read one does, so `tier`, `basis` and
    # `replaceable_by` reach the card through `basisHtml` — the collapsed "Drawn from a
    # model" disclosure that prints the model row, the reasoning, the seed a reader can
    # retype and the evidence that would retire the value. A drawn figure shipped to a
    # browser with no way to see what drew it is the one thing this whole tier is against,
    # so every field of it is declared read here rather than banked.
    "persons[].sex_basis.tier": ("shown", "tierOf(block) || block.confidence"),
    "persons[].sex_basis.basis.kind": ("shown", "basis.kind === 'model'"),
    "persons[].sex_basis.basis.id": ("shown", "escapeHtml(String(basis.id || ''))"),
    "persons[].sex_basis.basis.note": ("shown", "escapeHtml(String(basis.note || ''))"),
    "persons[].sex_basis.seed": ("shown", "escapeHtml(String(block.seed))"),
    "persons[].sex_basis.replaceable_by.kind": ("shown", "block.replaceable_by || null"),
    "persons[].sex_basis.replaceable_by.match": ("shown", "escapeHtml(String(rep.match || ''))"),
    # And the age band, which is the second half of the same stage. `value` is the
    # machine-readable label; the card prints the interval out of `low` and `high`, so a
    # reader meets "20 to 29" rather than "20-29" and the top band reads "70 or older".
    "persons[].age_band.value": ("shown", "bandYears(person.age_band)"),
    "persons[].age_band.low": ("shown", "const low = band.low"),
    "persons[].age_band.high": ("shown", "const high = band.high"),
    "persons[].age_band.confidence": ("shown", "tierOf(block) || block.confidence"),
    "persons[].age_band.tier": ("shown", "tierOf(block) || block.confidence"),
    "persons[].age_band.note": ("shown", "escapeHtml(block.note)"),
    "persons[].age_band.basis.kind": ("shown", "basis.kind === 'model'"),
    "persons[].age_band.basis.id": ("shown", "escapeHtml(String(basis.id || ''))"),
    "persons[].age_band.basis.note": ("shown", "escapeHtml(String(basis.note || ''))"),
    "persons[].age_band.seed": ("shown", "escapeHtml(String(block.seed))"),
    "persons[].age_band.replaceable_by.kind": ("shown", "block.replaceable_by || null"),
    "persons[].age_band.replaceable_by.match": ("shown", "escapeHtml(String(rep.match || ''))"),
    # T-1171. `name_basis` comes back to this layer with the drawn people: the row
    # "How this person is named" is a graded claim block like `age_band` above it, and
    # `claimRow` prints every part of one — the value, the tier chip, the model the
    # forename was drawn from, the seed that redraws it and the source that would retire
    # it. It reads through the same expressions because it is the same renderer.
    "persons[].name_basis.value": ("shown", "claimRow('How this person is named', named && named.value, named, citationsById)"),
    "persons[].name_basis.tier": ("shown", "tierOf(block) || block.confidence"),
    "persons[].name_basis.basis.kind": ("shown", "basis.kind === 'model'"),
    "persons[].name_basis.seed": ("shown", "escapeHtml(String(block.seed))"),
    "persons[].name_basis.replaceable_by.kind": ("shown", "block.replaceable_by || null"),
    "persons[].name_basis.replaceable_by.match": ("shown", "escapeHtml(String(rep.match || ''))"),
    # T-1171. …and the household block beside them: what size the 1840 histogram drew
    # this house at, and how much of that size is kin rather than the servants and lodgers
    # later stages seat. `modelledFamilyHtml` prints all of it.
    "modelled_family.stage": ("shown", "escapeHtml(String(block.stage))"),
    "modelled_family.ticket": ("shown", "escapeHtml(String(block.ticket))"),
    "modelled_family.household_type": ("shown", "escapeHtml(words(block.household_type))"),
    "modelled_family.size_drawn": ("shown", "escapeHtml(String(block.size_drawn))"),
    "modelled_family.kin_seated": ("shown", "escapeHtml(String(block.kin_seated))"),
    "modelled_family.seed": ("shown", "escapeHtml(String(block.seed))"),
    "modelled_family.note": ("shown", "escapeHtml(String(block.note || ''))"),
    # T-1171. A RECONSTRUCTED PERSON IS THE DRAWN THING, so the disclosure the attribute
    # tiers hang off a value is printed about the person instead: the stage that wrote
    # them, the model row, the seed a reader can retype and what would retire them.
    # `reconstructedHtml` passes the person record straight to `basisHtml`, which is why
    # `basis`, `seed` and `replaceable_by` read through the same expressions the blocks do.
    "persons[].reconstruction.stage": ("shown", "escapeHtml(String(rc.stage || ''))"),
    "persons[].reconstruction.ticket": ("shown", "escapeHtml(String(rc.ticket))"),
    "persons[].reconstruction.community": ("shown", "escapeHtml(words(rc.community))"),
    "persons[].reconstruction.review_required": (
        "shown", "rc.review_required ? ' This reconstruction carries a standing review.'"),
    "persons[].basis.kind": ("shown", "basis.kind === 'model'"),
    "persons[].basis.id": ("shown", "escapeHtml(String(basis.id || ''))"),
    "persons[].basis.note": ("shown", "escapeHtml(String(basis.note || ''))"),
    "persons[].seed": ("shown", "escapeHtml(String(block.seed))"),
    "persons[].replaceable_by.kind": ("shown", "block.replaceable_by || null"),
    "persons[].replaceable_by.match": ("shown", "escapeHtml(String(rep.match || ''))"),
    "persons[].note": ("shown", "escapeHtml(person.note)"),
    # T-1314. What a RECONSTRUCTED person owes the reader, on their own card:
    # `reconstructionHtml` says which stage of the programme wrote them and what
    # counted them, and hands the basis, the seed that redraws a model draw and the
    # replacement rule to `basisHtml` — the same three parts a reconstructed ATTRIBUTE
    # already showed, rather than a second vocabulary for the same idea.
    "persons[].basis.kind": ("shown", "const drawn = basis.kind === 'model'"),
    "persons[].seed": ("shown", "drawn && block.seed"),
    "persons[].replaceable_by.kind": ("shown", "const rep = block.replaceable_by"),
    "persons[].replaceable_by.match": ("shown", "escapeHtml(String(rep.match || ''))"),
    "persons[].reconstruction.stage": ("shown", "escapeHtml(String(rc.stage || ''))"),
    "persons[].reconstruction.programme": (
        "shown", "escapeHtml(String(rc.programme || 'the reconstruction programme'))"),
    "persons[].reconstruction.community": ("shown", "escapeHtml(String(rc.community))"),
    "persons[].reconstruction.counted_by": ("shown", "escapeHtml(String(rc.counted_by))"),
    "persons[].reconstruction.band_1840": ("shown", "escapeHtml(String(rc.band_1840))"),
    "persons[].reconstruction.age_on_scene_date.low": ("shown", "`${age.low} or older`"),
    "persons[].reconstruction.age_on_scene_date.high": (
        "shown", "age.high === null || age.high === undefined"),
    # The evidence strength, on the person the register minted from a letter list.
    # It reached `gazetteer.json` and `register_1835.json` and stopped there, so
    # for as long as it was unread a letter-list name and a documented tradesman
    # read identically on the card — which is the one thing T-0368's owner ruling
    # said must never happen. It is a row of its own now.
    "persons[].letter_list_only": ("shown", "person.letter_list_only"),
    # T-0379's own condition on the ruling: a letter-list person carries the DATES
    # of the returns that printed them, and the card shows them. With three quarters
    # of the town known this way, "a name on a post-office list" is not one claim —
    # a letter waiting on the scene date and one waiting eighteen months earlier say
    # different things about the same person, and only this figure tells them apart.
    "persons[].letter_list_returns": ("shown", "person.letter_list_returns"),
    # T-1240, folded into T-1255 — THE PLURAL DATED PLACES, ON BOTH CARDS. T-1238
    # landed `associated_with[]`, its gates and four demonstration records and banked
    # every leaf of it unread, because a schema has to exist before a view can read
    # it. `associationsHtml` is that view: seven rows on four records, on the person
    # card and the household card both, and every leaf of the row is declared here.
    #
    # The two figures that do the most work are `to` and `undated`. Neither says
    # whether a relationship held on 1 July 1835 and the renderer does not decide
    # that either — an open `to` on this layer means NO SOURCE CLOSES THE
    # RELATIONSHIP, so the row is printed open and the question left unanswered,
    # which is the flattening the plural shape exists to refuse. A CLOSED `to` is
    # compared against the scene date at the precision it was stored at, because
    # `1835-06` is June and June ends before the day this scene is set on.
    #
    # Two paths are deliberately absent because the DATA does not carry them today:
    # no household row has a closed `to` and no person row carries `undated`. The
    # renderer handles both — `associationBound` and `associationReach` read whichever
    # end a row has — and each is declared on the scope that does hold it, which is
    # where this gate can prove the read. They join when a record writes one.
    "associated_with[].kind": ("shown", 'escapeHtml(words(link.kind))'),
    "associated_with[].place_or_structure_id": ("shown", 'escapeHtml(words(link.place_or_structure_id))'),
    "associated_with[].resolves_to": ("shown", 'escapeHtml(words(link.resolves_to))'),
    "associated_with[].from": ("shown", "String(l.from ?? l.to ?? '9999')"),
    "associated_with[].undated": ("shown", 'link.undated || (!link.from && !link.to)'),
    "associated_with[].tier": ("shown", 'swatch(link.tier)'),
    "associated_with[].source_id": ("shown", 'citationsById.get(link.source_id)'),
    "associated_with[].note": ("shown", 'escapeHtml(link.note)'),
    "persons[].associated_with[].kind": ("shown", 'escapeHtml(words(link.kind))'),
    "persons[].associated_with[].place_or_structure_id": ("shown", 'escapeHtml(words(link.place_or_structure_id))'),
    "persons[].associated_with[].resolves_to": ("shown", 'escapeHtml(words(link.resolves_to))'),
    "persons[].associated_with[].from": ("shown", "String(l.from ?? l.to ?? '9999')"),
    "persons[].associated_with[].to": ("shown", 'endsOnOrAfterSceneDate(link.to)'),
    "persons[].associated_with[].tier": ("shown", 'swatch(link.tier)'),
    "persons[].associated_with[].source_id": ("shown", 'citationsById.get(link.source_id)'),
    "persons[].associated_with[].note": ("shown", 'escapeHtml(link.note)'),
    # T-1255 — THE DATED ROLES, ON THE CARD. `persons[].roles[]` is the canonical
    # record of a trade, a profession or an office and `occupation` is the generated
    # view of the roles that cover 1 July 1835 (index.json `_roles_doc`). T-1229 wrote
    # the list and left it unread: 262 people held 267 roles, 140 of them outside the
    # scene window, and the card showed only the derived word — which for Daniel
    # Elston was `none_recorded` beside two printed trades. `rolesHtml` prints the run
    # as a timeline, so every figure on a role is declared here.
    #
    # `covers_scene_date` is the record's own answer and the renderer never recomputes
    # it: it decides which rows are marked as reaching the scene date and which are
    # marked as not, and the summary count beside the section is read off it too.
    "persons[].roles[].role": ("shown", "escapeHtml(words(role.role))"),
    "persons[].roles[].as_printed": ("shown", "escapeHtml(String(role.as_printed))"),
    "persons[].roles[].kind": ("shown", "escapeHtml(words(role.kind))"),
    "persons[].roles[].from": ("shown", "const from = role.from ?? null;"),
    "persons[].roles[].to": ("shown", "const to = role.to ?? null;"),
    "persons[].roles[].precision": ("shown", "escapeHtml(words(role.precision))"),
    "persons[].roles[].dated_by": ("shown", "escapeHtml(words(role.dated_by || 'undated'))"),
    "persons[].roles[].covers_scene_date": (
        "shown", "const at = Boolean(role.covers_scene_date);"),
    "persons[].roles[].confidence": ("shown", "swatch(role.confidence)"),
    # T-1404. A trade that kept no house of trade of its own says so on the row; an
    # `own_premises` role needs no chip, because the house it implies is a business
    # record and the card's Works-at row is where that shows.
    "persons[].roles[].premises": (
        "shown", "role.premises === 'no_fixed_premises'"),
    "persons[].roles[].note": ("shown", "escapeHtml(role.note)"),
    # T-1299. WHERE THE ROLE WAS WORKED AND FOR WHOM, un-banked here in the commit that
    # renders them. Both arrived on the rows with T-1254 and were banked unread because
    # T-1255 shipped `rolesHtml` while T-1254 was still in flight — not because a
    # visitor should not see them. 164 roles state a place and 56 a body; the rest carry
    # `not_stated`, which is this layer's assertion that the record does not say, and
    # the row prints nothing rather than an empty line for it.
    "persons[].roles[].place": ("shown", "role.place && role.place !== 'not_stated'"),
    "persons[].roles[].employer_or_body": (
        "shown", "role.employer_or_body && role.employer_or_body !== 'not_stated'"),
    # T-1432. THE HOUSES A SOURCE NAMES THIS PERSON IN, on the same card and directly
    # under the roles. Every figure on the row is shown, because the row exists to be
    # read: the house and what they were in it, the run of notices that carry it, the
    # grade the business record gave the claim and the setting the register printed the
    # name under. None of it is a diagnostic and none of it is banked unread.
    "persons[].workplaces[].business_id": (
        "shown", "escapeHtml(w.business_name || w.business_id)"),
    "persons[].workplaces[].business_name": (
        "shown", "escapeHtml(w.business_name || w.business_id)"),
    "persons[].workplaces[].role": ("shown", "escapeHtml(words(w.role || ''))"),
    "persons[].workplaces[].printed_as": ("shown", "escapeHtml(w.printed_as)"),
    "persons[].workplaces[].from": ("shown", "const from = w.from ? printedOn(w.from)"),
    "persons[].workplaces[].to": ("shown", "const to = w.to ? printedOn(w.to)"),
    "persons[].workplaces[].tier": ("shown", "swatch(w.tier)"),
    "persons[].workplaces[].basis": ("shown", "escapeHtml(w.basis)"),
    "persons[].workplaces[].source_id": (
        "shown", "[w.source_id].filter(Boolean).map((id) => citationsById.get(id))"),
    "persons[].workplaces[].claim_ids": (
        "shown", "const notices = (w.claim_ids || []).length;"),
    "persons[].workplaces[].business_present_at_scene_date": (
        "shown", "w.business_present_at_scene_date ?"),
    "persons[].roles[].sources": (
        "shown", "(role.sources || []).map((id) => citationsById.get(id))"),
    # The derived view's own list of which roles reach the scene date. The card reads
    # its LENGTH — the summary line says how many dated roles a person has and whether
    # any of them lands on 1 July 1835, so a closed card no longer reads as trade-less
    # when the record holds a trade printed in another year.
    "persons[].occupation.roles_at_scene_date": (
        "shown", "const rolesAtScene = roles.filter((r) => r.covers_scene_date).length;"),
    "persons[].occupation.value": ("shown", "words(occ.value)"),
    "persons[].occupation.confidence": ("shown", "swatch(tierOf(occ))"),
    "persons[].occupation.note": ("shown", "escapeHtml(occ.note)"),
    # T-0693. `none_recorded` was carrying two facts — "no trade anywhere" and "no
    # trade for 1835, and a dated one for 1839" — and a reader could not tell them
    # apart from the field the card reads out. The pointer that separates them is
    # derived from the `directories` block above, so every figure on it is that
    # block's, dated to the year it describes; `laterOccupationHtml` renders all five
    # beside the 1835 value and never in place of it. The year is read twice on
    # purpose: once in the summary line, so the two states differ before the card is
    # even opened, which was the whole complaint.
    "persons[].occupation.later_occupation.value": ("shown", "escapeHtml(later.value)"),
    "persons[].occupation.later_occupation.describes_date": (
        "shown", "escapeHtml(String(later.describes_date))"),
    "persons[].occupation.later_occupation.confidence": (
        "shown", "swatch(later.confidence)"),
    "persons[].occupation.later_occupation.note": ("shown", "escapeHtml(later.note || '')"),
    "persons[].occupation.later_occupation.sources": (
        "shown", "(later.sources || []).map((id) => citationsById.get(id))"),
    # The three that were reaching the card as `[object Object]` until the commit
    # this map arrived in. See the module docstring: they are graded claim blocks
    # like the household's own, and they go through `claimRow` now.
    "persons[].age_on_scene_date.value": ("shown", "claimRow('Age on 1 July 1835', aged && aged.value"),
    "persons[].birth_year.value": ("shown", "return born.value;"),
    # T-1303. An age at death or an age given in 1879 leaves the birth in one year or in
    # two, and the card prints both years where there are two rather than picking the
    # lower one and reading as exact.
    "persons[].birth_year.precision": ("shown", "if (born.precision === 'band'"),
    "persons[].birth_year.band": ("shown", "`${born.band[0]} or ${born.band[1]}`"),
    "persons[].age_on_scene_date.confidence": ("shown", "tierOf(block) || block.confidence"),
    "persons[].birth_year.confidence": ("shown", "tierOf(block) || block.confidence"),
    "persons[].age_on_scene_date.note": ("shown", "escapeHtml(block.note)"),
    "persons[].birth_year.note": ("shown", "escapeHtml(block.note)"),
    # T-1392 (of T-1179). A birth interval the card itself refutes is not spent, and the
    # block that records the refusal lives in this same key asserting no year. Every one
    # of its figures reaches the Born row through `birthRefusedHtml`: a reader who is told
    # only "not recorded" learns nothing about the obituary still printed further down the
    # same card, so the interval, the page it was read off and the reason are all shown.
    "persons[].birth_year.refused_interval": (
        "shown", "const [from, to] = block.refused_interval || [];"),
    "persons[].birth_year.refused_because": (
        "shown", "born && born.refused_because"),
    "persons[].birth_year.record_id": (
        "shown", "escapeHtml(String(block.record_id ?? ''))"),
    "persons[].birth_year.as_read": (
        "shown", "escapeHtml(String(block.as_read))"),
    # And the weaker verdict — an interval that misses only the franchise's invented line
    # — is CARRIED, with the disagreement folded into the note the Born row already
    # prints. The field is the machine-readable half of that sentence.
    "persons[].birth_year.contradicted_by_the_card": (
        "shown", "born && born.contradicted_by_the_card"),
    # T-0491. The 1840 identity bridge, on the three people that carry one. PR #670
    # attached it and declared nothing, so twenty-four figures reached a browser
    # unread — which is the exact shape this census exists to catch, and the cheap
    # answer was to bank all of them. NONE is banked. An identity bridge is an
    # ARGUMENT — a transcribed name, a normalised reading of it, the page, the row,
    # the serial, and three separate confidences in three separate steps — and each
    # of those is a thing a reader can disagree with only if they can see it.
    # T-1232 — the facts the matched research stated and the record had only in prose.
    # `tools/spend_person_facts.py` adjudicates every candidate in those 94 asserted-identity
    # blocks and writes the asserted ones here; `profileFactsHtml()` prints each one with the
    # DATE IT SPEAKS ABOUT and the sentence it was read from, which is the distinction the
    # whole consolidation rests on. `place_class` is shown as a clause rather than a word,
    # because a fact the source sets outside this town is the reason a presence could not be
    # lifted and it has to read that way.
    "persons[].profile_facts[].field": ("shown", "FACT_LABELS.get(f.field) || words(f.field)"),
    "persons[].profile_facts[].value": ("shown", "escapeHtml(String(f.value ?? ''))"),
    "persons[].profile_facts[].confidence": ("shown", "swatch(f.confidence)"),
    "persons[].profile_facts[].sources": ("shown", "(f.sources || []).map((id) => citationsById.get(id))"),
    "persons[].profile_facts[].describes_date": ("shown", "escapeHtml(printedOn(f.describes_date))"),
    "persons[].profile_facts[].place_class": (
        "shown", "f.place_class === 'outside_chicago' ? ', and somewhere other than this town' : ''"),
    "persons[].profile_facts[].as_read": ("shown", "escapeHtml(String(f.as_read ?? ''))"),
    "persons[].profile_facts[].note": ("shown", "escapeHtml(String(f.note ?? ''))"),
    "persons[].profile_facts[].record_id": ("shown", "Record ${escapeHtml(String(f.record_id))}"),
    "persons[].profile_facts[].precision": (
        "shown", "the source is exact to the ${escapeHtml(words(f.precision))}"),
    "persons[].later_census.year": ("shown", "Found again in the ${escapeHtml(String(census.year))} census"),
    "persons[].later_census.source_id": ("shown", "citationsById.get(census.source_id)"),
    "persons[].later_census.serial": ("shown", "enumeration serial ${\n        escapeHtml(String(census.serial))}"),
    "persons[].later_census.census_page": ("shown", "Page ${escapeHtml(String(census.census_page))}"),
    "persons[].later_census.census_row": ("shown", "escapeHtml(String(census.census_row))"),
    "persons[].later_census.head_name_transcribed": ("shown", "escapeHtml(census.head_name_transcribed)"),
    "persons[].later_census.head_name_normalized": ("shown", "escapeHtml(census.head_name_normalized)"),
    "persons[].later_census.source_image": ("shown", "from image ${escapeHtml(census.source_image)}"),
    # Which image the row was read off, and whether a paired continuation sheet was
    # needed to read it — the 1840 schedules run a household across two facing pages,
    # and a serial fixed from one image alone is a weaker reading than one fixed from
    # both. It is printed beside the image it qualifies.
    "persons[].later_census.source_kind": ("shown", "escapeHtml(census.source_kind)"),
    "persons[].later_census.bridge_basis": ("shown", "escapeHtml(census.bridge_basis)"),
    "persons[].later_census.bridge_status": ("shown", "escapeHtml(words(census.bridge_status))"),
    # Three confidences, not one. The papers can be right about the name and wrong
    # about the man, and the row can be assigned to the wrong serial with both of
    # those right, so the card prints the three and says they fail independently.
    "persons[].later_census.name_confidence": ("shown", "escapeHtml(words(census.name_confidence))"),
    "persons[].later_census.identity_confidence": ("shown", "escapeHtml(words(census.identity_confidence))"),
    "persons[].later_census.serial_mapping_confidence": ("shown", "escapeHtml(words(census.serial_mapping_confidence))"),
    # The 1840 household tallies, shown WITH the record's refusal printed under
    # them. These are the figures most likely to be read back onto 1835 by a
    # visitor doing the arithmetic themselves, and hiding them does not stop that
    # — it only removes the sentence that says the arithmetic is wrong.
    "persons[].later_census.household.persons": ("shown", "['People in the household', hh.persons]"),
    "persons[].later_census.household.children_under_10": ("shown", "['Children under ten', hh.children_under_10]"),
    "persons[].later_census.household.male": ("shown", "['Male', hh.male]"),
    "persons[].later_census.household.female": ("shown", "['Female', hh.female]"),
    "persons[].later_census.household.agriculture": ("shown", "['Employed in agriculture', hh.agriculture]"),
    "persons[].later_census.household.commerce": ("shown", "['Employed in commerce', hh.commerce]"),
    "persons[].later_census.household.manufactures_trades": ("shown", "['Employed in manufactures and trades', hh.manufactures_trades]"),
    "persons[].later_census.household.inland_navigation": ("shown", "['Employed in inland navigation', hh.inland_navigation]"),
    "persons[].later_census.household.professions_engineering": ("shown", "['In a learned profession or engineering', hh.professions_engineering]"),
    "persons[].later_census.household.foreigners_not_naturalized": ("shown", "['Foreigners not naturalized', hh.foreigners_not_naturalized]"),
    "persons[].later_census.household.illiterate_over_21": ("shown", "['Over twenty-one and unable to read or write', hh.illiterate_over_21]"),
    # And the same line read off the photograph of the sheet, shown beside the
    # recovered figures rather than instead of them, with the sentence that says
    # where the two disagree (T-0530).
    "persons[].later_census.scan_verified.read_by": ("shown", "read by ${escapeHtml(scan.read_by)}"),
    "persons[].later_census.scan_verified.sources": ("shown", "(scan.sources || []).map((id) => citationsById.get(id))"),
    "persons[].later_census.scan_verified.image": ("shown", "From ${escapeHtml(scan.image)}"),
    "persons[].later_census.scan_verified.line": ("shown", "Line ${escapeHtml(String(scan.line))}"),
    "persons[].later_census.scan_verified.head_name_as_read": ("shown", "escapeHtml(scan.head_name_as_read)"),
    "persons[].later_census.scan_verified.free_persons": ("shown", "['People on the line', scan.free_persons]"),
    "persons[].later_census.scan_verified.males": ("shown", "['Male', scan.males]"),
    "persons[].later_census.scan_verified.females": ("shown", "['Female', scan.females]"),
    "persons[].later_census.scan_verified.children_under_10": ("shown", "['Children under ten', scan.children_under_10]"),
    "persons[].later_census.scan_verified.age_bands": ("shown", "band by band: ${escapeHtml(scan.age_bands)}"),
    "persons[].later_census.scan_verified.column_totals_check": ("shown", "escapeHtml(scan.column_totals_check)"),
    "persons[].later_census.scan_disagreement": ("shown", "escapeHtml(census.scan_disagreement)"),
    # -----------------------------------------------------------------------
    # T-0668. THE EVIDENCE CONSOLIDATION'S OWN READING, on the card at last.
    #
    # `tools/consolidate_resident_evidence.py` reads seven source domains, decides
    # who is who and grades each person on a ratified ladder. Everything it decided
    # was written onto the person and NOTHING read it: 44 figures over 531 people,
    # the largest unread population this census has ever carried on one layer. That
    # is the T-0491 defect at scale — a grade is a verdict, the appearances are the
    # argument, and a verdict shipped without its argument is an assertion.
    #
    # The five domains share one row shape and one renderer — `evidenceLineHtml` —
    # so one expression covers each leaf across all five, exactly as `claimRow`
    # covers the graded claims above. `describes_date` is on every line on purpose:
    # the domains are not contemporaries of each other and the ladder grades them
    # differently for that reason.
    "persons[].ladder_rule": ("shown", "escapeHtml(String(person.ladder_rule))"),
    "persons[].civic_mint": ("shown", "person.civic_mint"),
    # T-0708. The People directory's "How known" filter reads the subtype off the
    # compiled people.json row (a denormalised copy of this figure, made by
    # compile_scene.py compile_people) and the projected cohort is one of its four
    # answers, so the figure now reaches a visitor as a filter and a row mark.
    "persons[].resident_subtype": ("shown", "r.resident_subtype === 'projected_resident'"),
    "persons[].press_evidence[].list": ("shown", "escapeHtml(words(entry.list))"),
    "persons[].press_evidence[].as_read": ("shown", "escapeHtml(String(entry.as_read ?? ''))"),
    "persons[].press_evidence[].locator": ("shown", "at ${escapeHtml(String(entry.locator))}"),
    "persons[].press_evidence[].record_id": ("shown", "Record ${\n      escapeHtml(String(entry.record_id))}"),
    "persons[].press_evidence[].describes_date": ("shown", "printedOn(entry.describes_date)"),
    "persons[].press_evidence[].source": ("shown", "citationsById.get(entry.source)"),
    "persons[].press_evidence[].rule": ("shown", "rung ${\n      escapeHtml(String(entry.rule))}"),
    "persons[].civic_evidence[].list": ("shown", "escapeHtml(words(entry.list))"),
    "persons[].civic_evidence[].as_read": ("shown", "escapeHtml(String(entry.as_read ?? ''))"),
    "persons[].civic_evidence[].locator": ("shown", "at ${escapeHtml(String(entry.locator))}"),
    "persons[].civic_evidence[].record_id": ("shown", "Record ${\n      escapeHtml(String(entry.record_id))}"),
    "persons[].civic_evidence[].describes_date": ("shown", "printedOn(entry.describes_date)"),
    "persons[].civic_evidence[].source": ("shown", "citationsById.get(entry.source)"),
    "persons[].civic_evidence[].rule": ("shown", "rung ${\n      escapeHtml(String(entry.rule))}"),
    "persons[].church_evidence[].list": ("shown", "escapeHtml(words(entry.list))"),
    "persons[].church_evidence[].as_read": ("shown", "escapeHtml(String(entry.as_read ?? ''))"),
    "persons[].church_evidence[].locator": ("shown", "at ${escapeHtml(String(entry.locator))}"),
    "persons[].church_evidence[].record_id": ("shown", "Record ${\n      escapeHtml(String(entry.record_id))}"),
    "persons[].church_evidence[].describes_date": ("shown", "printedOn(entry.describes_date)"),
    "persons[].church_evidence[].source": ("shown", "citationsById.get(entry.source)"),
    "persons[].church_evidence[].rule": ("shown", "rung ${\n      escapeHtml(String(entry.rule))}"),
    "persons[].book_evidence[].list": ("shown", "escapeHtml(words(entry.list))"),
    "persons[].book_evidence[].as_read": ("shown", "escapeHtml(String(entry.as_read ?? ''))"),
    "persons[].book_evidence[].locator": ("shown", "at ${escapeHtml(String(entry.locator))}"),
    "persons[].book_evidence[].record_id": ("shown", "Record ${\n      escapeHtml(String(entry.record_id))}"),
    "persons[].book_evidence[].describes_date": ("shown", "printedOn(entry.describes_date)"),
    "persons[].book_evidence[].source": ("shown", "citationsById.get(entry.source)"),
    "persons[].book_evidence[].rule": ("shown", "rung ${\n      escapeHtml(String(entry.rule))}"),
    "persons[].census_evidence[].list": ("shown", "escapeHtml(words(entry.list))"),
    "persons[].census_evidence[].as_read": ("shown", "escapeHtml(String(entry.as_read ?? ''))"),
    "persons[].census_evidence[].locator": ("shown", "at ${escapeHtml(String(entry.locator))}"),
    "persons[].census_evidence[].record_id": ("shown", "Record ${\n      escapeHtml(String(entry.record_id))}"),
    "persons[].census_evidence[].describes_date": ("shown", "printedOn(entry.describes_date)"),
    "persons[].census_evidence[].source": ("shown", "citationsById.get(entry.source)"),
    "persons[].census_evidence[].rule": ("shown", "rung ${\n      escapeHtml(String(entry.rule))}"),
    # The two people the consolidation could date. Both go through `claimRow`, so
    # each carries its own confidence, its reasoning and its citation like every
    # other graded claim on this card; the age is a RANGE because a birth year with
    # no month cannot say which side of 1 July the person turned.
    "persons[].biographical_evidence.birth_year.value": ("shown", "bio.birth_year && bio.birth_year.value"),
    "persons[].biographical_evidence.age_on_1835_07_01.value.min": ("shown", "between ${age.value.min}"),
    # -----------------------------------------------------------------------
    # T-1233. THE ADJUDICATIONS, THE RULINGS AND THE OBITUARY, ON THE CARD.
    #
    # 76 of this census's 83 unread resident paths were these six blocks, and every
    # one of them is an ARGUMENT rather than a figure: why this card is named what it
    # is named, which cards were folded into it, which look-alike was weighed and kept
    # apart, what the research block on the record concluded, and what an 1896 obituary
    # list says about somebody of this name. `laterCensusHtml` already made the finding
    # this wiring acts on — "an argument a visitor cannot see is an assertion" — and
    # these blocks are where the project's own reasoning was kept from its readers.
    #
    # `resident_research` is the largest of them and the plainest failure: the RECORDS
    # hold 850 research blocks and `research_pilot.json`, the only copy anything read,
    # holds 375. 476 people carried a dated identity review that reached nobody.
    "persons[].resident_research.outcome": ("shown", "escapeHtml(words(rr.outcome))"),
    "persons[].resident_research.summary": ("shown", "prose(rr.summary, citationsById, named)"),
    "persons[].resident_research.asserted_identity": ("shown", "rr.asserted_identity ? 'identity asserted' : 'identity not asserted'"),
    "persons[].resident_research.programme": ("shown", "escapeHtml(String(rr.programme ?? 'the resident research programme'))"),
    "persons[].resident_research.ticket": ("shown", "escapeHtml(String(rr.ticket ?? ''))"),
    "persons[].resident_research.reviewed_on": ("shown", "escapeHtml(printedOn(rr.reviewed_on))"),
    "persons[].resident_research.regraded_on": ("shown", "rr.regraded_on ? `, regraded ${escapeHtml(printedOn(rr.regraded_on))}"),
    "persons[].resident_research.rule": ("shown", "under rule ${\n          escapeHtml(String(rr.rule ?? ''))}"),
    "persons[].resident_research.evidence_for": ("shown", "prose(rr.evidence_for, citationsById, named)"),
    "persons[].resident_research.evidence_against": ("shown", "prose(rr.evidence_against, citationsById, named)"),
    "persons[].resident_research.proposed_facts": ("shown", "prose(rr.proposed_facts, citationsById, named)"),
    "persons[].resident_research.notes": ("shown", "prose(rr.notes, citationsById, named)"),
    "persons[].resident_research.source_ids": ("shown", "const named = new Set(rr.source_ids || []);"),
    "persons[].resident_research.candidate_ids": ("shown", "escapeHtml((rr.candidate_ids || []).map((id) => words(id)).join(', '))"),
    "persons[].resident_research.candidates[].candidate_id": ("shown", "escapeHtml(String(c.candidate_id))"),
    "persons[].resident_research.candidates[].asserted": ("shown", "escapeHtml(c.asserted ? 'asserted as this person' : 'weighed and not asserted')"),
    "persons[].resident_research.candidates[].assessment": ("shown", "escapeHtml(words(c.assessment))"),
    "persons[].resident_research.candidates[].basis": ("shown", "prose(c.basis, citationsById, named)"),
    "persons[].resident_research.candidates[].conflicts": ("shown", "prose((c.conflicts || []).join(' '), citationsById, named)"),
    "persons[].resident_research.refusals[].withheld": ("shown", "escapeHtml(String(r.withheld ?? ''))"),
    "persons[].resident_research.refusals[].rule": ("shown", "rule ${escapeHtml(String(r.rule ?? ''))}"),
    "persons[].resident_research.refusals[].regraded_on": ("shown", "r.regraded_on ? `, regraded ${escapeHtml(printedOn(r.regraded_on))}`"),
    "persons[].resident_research.refusals[].reason": ("shown", "prose(r.reason, citationsById, named)"),
    # The name ruling. Three people, nine figures, and a displayed spelling that changed
    # with the argument for it left in a file.
    "persons[].name_ruling.ruled_by": ("shown", "Ruled by ${escapeHtml(String(ruling.ruled_by ?? ''))}"),
    "persons[].name_ruling.rule": ("shown", "under rule ${\n      escapeHtml(String(ruling.rule ?? ''))}"),
    "persons[].name_ruling.printed_line": ("shown", "at printed line ${\n        escapeHtml(String(ruling.printed_line))}"),
    "persons[].name_ruling.ruling": ("shown", "<code>${escapeHtml(String(ruling.ruling ?? ''))}</code>"),
    "persons[].name_ruling.takes": ("shown", "The card takes ${prose(ruling.takes, citationsById, named)}"),
    "persons[].name_ruling.over": ("shown", "over ${prose(ruling.over, citationsById, named)}"),
    "persons[].name_ruling.displayed_name_was": ("shown", "escapeHtml(String(ruling.displayed_name_was ?? ''))"),
    "persons[].name_ruling.reasoning": ("shown", "prose(ruling.reasoning, citationsById, named)"),
    "persons[].name_ruling.the_id_did_not_move": ("shown", "prose(ruling.the_id_did_not_move, citationsById, named)"),
    # The fold, and the pair that was weighed and kept apart. `for_merge` is rendered
    # beside `against_merge` on purpose: a verdict of `distinct` published without the
    # case for the other answer is an assertion.
    "persons[].merged_from[].cards": ("shown", "escapeHtml((m.cards || []).map((c) => words(c)).join(', '))"),
    "persons[].merged_from[].rule": ("shown", "Folded under rule ${escapeHtml(String(m.rule ?? ''))}"),
    "persons[].merged_from[].ticket": ("shown", "by ${\n    escapeHtml(String(m.ticket ?? ''))}"),
    "persons[].merged_from[].cluster": ("shown", "escapeHtml(String(m.cluster ?? ''))}\n    cluster"),
    "persons[].merge_ruling[].verdict": ("shown", "escapeHtml(words(r.verdict))"),
    "persons[].merge_ruling[].weighed_against": ("shown", "escapeHtml((r.weighed_against || []).map((c) => words(c)).join(', '))"),
    "persons[].merge_ruling[].rule": ("shown", "under rule ${\n    escapeHtml(String(r.rule ?? ''))}"),
    "persons[].merge_ruling[].cluster": ("shown", "in the ${escapeHtml(String(r.cluster ?? ''))} cluster"),
    "persons[].merge_ruling[].ticket": ("shown", "(${escapeHtml(String(r.ticket ?? ''))})"),
    "persons[].merge_ruling[].referred_to": ("shown", "referred to ${escapeHtml(String(r.referred_to))}"),
    "persons[].merge_ruling[].for_merge": ("shown", "<b>For a merge:</b> ${prose(r.for_merge, citationsById, named)}"),
    "persons[].merge_ruling[].against_merge": ("shown", "<b>Against:</b> ${prose(r.against_merge, citationsById, named)}"),
    # The old-settler obituary, rendered on the PERSON the household's block matched it
    # to. The match is a surname and a first initial, the birth year is this project's
    # own subtraction, and the list's header — which admits people who arrived after
    # 1843 — is the limit the whole reading turns on, so it is quoted rather than
    # summarised.
    "old_settler_deaths.the_header_admission": ("shown", "escapeHtml(String(block.the_header_admission ?? ''))"),
    "old_settler_deaths.people[].person_id": ("shown", "(block.people || []).find((p) => p.person_id === personId)"),
    "old_settler_deaths.people[].manner_of_death": ("shown", "escapeHtml(String(entry.manner_of_death ?? 'died'))"),
    "old_settler_deaths.people[].place_of_death": ("shown", "escapeHtml(String(entry.place_of_death ?? 'a place the page does not give'))"),
    "old_settler_deaths.people[].death_date": ("shown", "escapeHtml(printedOn(entry.death_date))"),
    "old_settler_deaths.people[].age_as_printed": ("shown", "escapeHtml(String(entry.age_as_printed ?? ''))"),
    "old_settler_deaths.people[].trade_or_office": ("shown", "escapeHtml(words(entry.trade_or_office))"),
    "old_settler_deaths.people[].matched_as": ("shown", "Matched as ${escapeHtml(String(entry.matched_as ?? ''))}"),
    "old_settler_deaths.people[].matched_by": ("shown", "prose(entry.matched_by, citationsById, named)"),
    "old_settler_deaths.people[].matched_on_initial_only": ("shown", "entry.matched_on_initial_only || entry.entry_given_is_initial_only"),
    "old_settler_deaths.people[].entry_given_is_initial_only": ("shown", "entry.matched_on_initial_only || entry.entry_given_is_initial_only"),
    "old_settler_deaths.people[].resident_given_is_initial_only": ("shown", "|| entry.resident_given_is_initial_only"),
    "old_settler_deaths.people[].the_agreement": ("shown", "The agreement is ${\n        escapeHtml(String(entry.the_agreement ?? ''))}"),
    "old_settler_deaths.people[].entry_given_as_read": ("shown", "escapeHtml(String(entry.entry_given_as_read ?? ''))"),
    "old_settler_deaths.people[].birth_year_earliest": ("shown", "Born between ${escapeHtml(String(entry.birth_year_earliest ?? ''))}"),
    "old_settler_deaths.people[].birth_year_latest": ("shown", "escapeHtml(String(entry.birth_year_latest ?? ''))"),
    "old_settler_deaths.people[].birth_year_arithmetic": ("shown", "prose(entry.birth_year_arithmetic, citationsById, named)"),
    "old_settler_deaths.people[].as_read": ("shown", "The page reads <q>${escapeHtml(String(entry.as_read ?? ''))}</q>"),
    "old_settler_deaths.people[].record_id": ("shown", "record ${\n        escapeHtml(String(entry.record_id ?? ''))}"),
    "persons[].biographical_evidence.age_on_1835_07_01.value.max": ("shown", "and ${age.value.max}"),
}

READS: dict[str, dict[str, tuple[str, str]]] = {
    "flora/zone": FLORA_ZONE_READS,
    "flora/manifest": FLORA_MANIFEST_READS,
    "flora/palette": FLORA_PALETTE_READS,
    "fauna/zone": FAUNA_ZONE_READS,
    "fauna/manifest": FAUNA_MANIFEST_READS,
    "residents/manifest": RESIDENTS_MANIFEST_READS,
    "residents/household": RESIDENTS_HOUSEHOLD_READS,
}

# Which record kinds a layer keeps, and in which subdirectory. The layer list was
# hardcoded to flora and fauna in two places and the record kinds in a third,
# which is how `data/residents` gained two readers without ever reaching
# assertion 3a. One table now, read by everything that walks a layer.
LAYER_KINDS: dict[str, tuple[tuple[str, str], ...]] = {
    "flora": (("zone", "zones"), ("palette", "palettes")),
    "fauna": (("zone", "zones"), ("palette", "palettes")),
    "residents": (("household", "households"),),
}
LAYERS = tuple(LAYER_KINDS)
RECORD_KINDS = ("zone", "manifest", "palette", "household")

# THE DECLARED REFUSALS. T-0021's acceptance is that every unreached figure gets
# a ticket or a stated refusal, and a refusal written into a ticket nobody runs
# is a refusal nobody reads. These sit against the figure they refuse, are
# carried into `layer_reads_baseline.json` by `--update`, and are printed under
# the census. A refusal is not a permission: the figure stays in the unread bank,
# assertion 4 still fails if a new one appears, and assertion 5 still fails if
# one of these leaves the data.
REFUSALS: dict[str, str] = {
    # -------------------------------------------------------------------------
    # T-1489 carried the drawn employment seat back onto the card of the person holding
    # it — 123 of them, 33 in this directory — because the join beside the layer said
    # where a reconstructed trade-holder worked and the card itself said nothing. The
    # walkthrough was already showing the seat, and it shows it from the join, which
    # carries the whole adjudication: the term of the order rule that chose the house,
    # the class, the candidates considered, the model row that allows the hand. The five
    # keys the CARD carries are a strict subset of that, so a renderer reading them would
    # show a visitor nothing they are not being shown, out of a second copy that moves
    # whenever the business layer moves. The card's copy is for the LAYER — a card that
    # loses the join still says where its holder worked, and the four stages that derive
    # a directory whole now carry it through their rebuilds. `note` is the sixth key and
    # is machinery here, as a note is everywhere in this census. There is no
    # `business_name`: `tools/replace_invented_residents.py` reads the raw text of these
    # cards as a name pool, and writing one there refused a documented tailor from its
    # deal — `employment_block`'s own docstring carries the measurement.
    "residents/household:persons[].employment.business_id": (
        "The house this project POINTED a reconstructed trade-holder at, where no source "
        "names one. `residents.js` shows the seat already and shows it from "
        "data/residents/reconstructed_seating.json, which holds the reasoning this "
        "pointer is the conclusion of; reading the card's copy instead would put a "
        "second, thinner statement of the same claim in front of a visitor. The copy "
        "exists so the resident layer carries its own answer."
    ),
    "residents/household:persons[].employment.role": (
        "The staffing model's own term for the hand this person stands in as — clerk, "
        "domestic, teamster. Shown to a visitor from the join, for the reason above."
    ),
    "residents/household:persons[].employment.tier": (
        "`reconstructed`, on every one of them, because a drawn seat has no other grade. "
        "The confidence a visitor reads is the join's, which states it in a sentence "
        "rather than a word."
    ),
    "residents/household:persons[].employment.seed": (
        "The seed the draw was made under — what makes the seat reproducible and what "
        "lets a gate tell a re-derivation from a hand-edit. Provenance for a tool, never "
        "a figure about a person, and in the same class as `stated_family.pass` below."
    ),
    # -------------------------------------------------------------------------
    # T-1320 reads the book corpus for kinship. A kin row it writes or corroborates names
    # the book claim behind it, so `--check` can hold the row to a live ruling and a row
    # that outlived its ruling goes red. It is a foreign key into
    # data/research/books/kin_rulings.json and data/research/books/claims/*.json, in the
    # same class as `stated_family.statement` below.
    "residents/household:kin[].book_kin": (
        "The id of the book claim this kin row was read out of — a foreign key into "
        "data/research/books/claims/ and the ruling that answers it. It is what makes "
        "the write re-derivable and what lets the gate notice a tie that lost its "
        "reading; it states nothing about either person. What a visitor judges the "
        "relationship by is on the row already and is read there: the relation, the "
        "confidence, the sources and the note that quotes the sentence."
    ),
    # -------------------------------------------------------------------------
    # T-1313 seated the three relatives T-1170's reading ruled `write`, and every seated
    # person carries the marker that makes the write re-derivable. Six keys, none of them
    # a figure about a person: one names the pass, one the ticket, one resolves the read
    # statement, one is a matcher's normalised copy of `relationship`, one is the source's
    # own wording kept for audit, one is the field the sentence was read out of. The
    # evidence a visitor judges these three women by — grade, sources, note, relationship
    # — is on the card already and is read there. Same class as `source_pass`.
    "residents/household:persons[].stated_family.pass": (
        "The stated-family pass's own bookkeeping — which pass wrote this person, so "
        "`--build` can lift its whole output back out and re-derive it rather than "
        "appending to it. That re-derivability is the reason the key exists: a "
        "verdict re-read from `write` to `no_seat` has to take somebody back OUT of "
        "the town, and a pass that cannot find its own writes cannot do that. It is a "
        "fact about the tool, not about the woman on the card."
    ),
    "residents/household:persons[].stated_family.ticket": (
        "Which ticket seated this person. Repository provenance of the same class as "
        "`source_pass` — useful to a reader of the JSON and to the run that has to "
        "audit a pass, and not part of what a visitor judges the record by. What the "
        "visitor needs is the evidence, and the card already shows it: the grade, the "
        "sources and the note that says what the source does NOT say."
    ),
    "residents/household:persons[].stated_family.statement": (
        "The id of the read statement this seat came from — a foreign key into the "
        "derived reading in docs/RESEARCH/stated-families-2026-09.md and into the "
        "verdict table in data/residents/stated_family_rulings.json. It resolves a "
        "row; it states nothing about the person. The claim it resolves to reaches "
        "the visitor as the note and the sources on this person's own row."
    ),
    "residents/household:persons[].stated_family.relation": (
        "The normalised relation word the reading matched on — `wife`, `daughter`. "
        "The poorer of two copies: the person's own `relationship` is what the card "
        "prints, it is the field every other resident carries, and it is authored for "
        "a reader rather than for a matcher. Showing this one instead would be "
        "showing less, which is the ruling this table already makes about "
        "`households[].present_on_scene_date`."
    ),
    "residents/household:persons[].stated_family.as_read": (
        "The source's words for the relative, kept verbatim so the match can be "
        "audited against the page — 'Welthyan Loomis', 'Mrs A. G. Burley'. Where it "
        "differs from the name on the card that difference is a finding, and it "
        "belongs in the note, which is where it is written and where the visitor "
        "reads it. Un-banks the day a card prints the reading beside the name."
    ),
    "residents/household:persons[].stated_family.read_from": (
        "Which field of which record the statement was read out of — the pass's audit "
        "trail back to the sentence. File-and-field routing, the same class of key as "
        "`record_file`, and it names a location in this repository rather than "
        "anything about 1835."
    ),
    # T-1238's two closed sets, re-authored HERE by T-1255 because they were written
    # straight into layer_reads_baseline.json and nowhere else — the same mistake
    # `flora/zone:woody_stratum.measured_from` below records, and `--update` deletes a
    # refusal it cannot find in this table. The prose also had to change: it said both
    # sets "un-bank together with T-1240's view", and T-1240's view has now landed
    # inside T-1255 without reading either.
    #
    # It reads the rung the ROW carries and prints that word, which is the claim a
    # reader needs — "reaches a structure", "reaches a street". It does not implement
    # the sets as behaviour: no label is looked up in them, and no row is ordered or
    # withheld by them. A renderer that drew a row differently per kind, or that
    # refused a rung the set does not hold, would read them, and would declare them
    # here. Until one does, these are two closed sets the data states for a reader and
    # for tools/validate.py, and the honest answer is that nothing reads them.
    "residents/manifest:vocabulary.association_kinds": (
        "The closed set of connection kinds an `associated_with` row may carry. The "
        "person and household cards print the kind word off the ROW (T-1255's "
        "`associationsHtml`) rather than looking it up here, and nothing orders, "
        "labels or withholds a row by this set. tools/validate.py is what holds a row "
        "to it; a renderer that read it would be a second answer to the same question."
    ),
    "residents/manifest:vocabulary.association_resolution": (
        "The closed set of rungs an `associated_with` row may resolve to — a roof, a "
        "street, a part of town. The cards print the row's own `resolves_to` word, "
        "because how far the evidence reached is part of the claim; the SET behind it "
        "is a schema constraint tools/validate.py enforces, and no renderer implements "
        "it as behaviour. It un-banks when one draws a row differently per rung."
    ),
    # T-1056, recovered by T-1029. This refusal was written straight into
    # layer_reads_baseline.json and never into this table, so `--update` — which
    # rebuilds the bank from `state["unread"]` and re-attaches a refusal only if it
    # is HERE — deleted it the first time anybody re-derived the file. Nothing
    # noticed for two days because nothing re-derived it. A stated refusal is a
    # judgement somebody made; losing one silently is the expensive direction, so it
    # is restored here verbatim and the table is now the only place one is authored.
    "flora/zone:woody_stratum.measured_from": (
        "A units declaration, not a figure. It states what woody_stratum.establishes_m's "
        "metres are measured from, for a reader of the record and for tools/validate.py, "
        "which requires it. A renderer that read it would be a renderer able to convert "
        "between datums; if it ever disagreed with the heightfield's own, the right "
        "outcome is this gate failing rather than a silent conversion. T-1056."),
    "residents/manifest:counts.households": (
        "The panel renders one row per household and counts the rows. A tally shown "
        "beside a list it might disagree with is worse than no tally; validate.py holds "
        "the two equal, which is where a disagreement should surface, not on the card."),
    "residents/manifest:households[].head": (
        "A foreign key into `persons[].id`, not a figure — it names which person heads "
        "the household, and that fact already reaches the visitor as that person's "
        "`relationship`, shown on their own row."),
    # T-1144 acceptance 9, the two figures of the presence leg the card does NOT show.
    "residents/household:present_on_scene_date.last_dated_appearance.person": (
        "A foreign key into `persons[].id` — which person of the household the leg was "
        "read on. It is there so the derivation and the roster can be audited against "
        "the card, and the card already names every person of the household on their "
        "own rows; printing the id beside the date would say nothing a reader can use."),
    "residents/household:present_on_scene_date.last_dated_appearance.record": (
        "The `record_id` or locator of the evidence block the leg came from — an "
        "audit pointer, null on the 383 legs read off a post-office return, which "
        "carries no per-return record. The card shows the SOURCE the block cites, "
        "which is the part a reader can follow; an internal row id is not."),
    "residents/household:head": (
        "The record's own copy of the same foreign key. Refused for the same reason, and "
        "it is the record that is authoritative."),
    "residents/household:division": (
        "Denormalised. The MANIFEST's copy is what the panel groups and labels rows by, "
        "and validate.py fails the build if the two disagree; reading both would be two "
        "answers to one question."),
    "residents/manifest:households[].present_on_scene_date": (
        "The flat copy of a graded claim. `residents.js` shows the RECORD's block — its "
        "value, its confidence, its reasoning and its sources — and the manifest's bare "
        "value carries none of that. Showing the poorer copy would be showing less."),
    "residents/manifest:counts.projected_residents": (
        "T-0782, the owner's ruling on the opening card: the aggregate is struck. It "
        "reached a visitor in one place — a parenthesis inside the gate card's inferred "
        "count — where it read as a fourth grade beside attested/inferred/reconstructed "
        "and was in fact a subtype OF the inferred, counted on a different axis. The "
        "claim itself still reaches the visitor, and better: `people.js` filters and "
        "chips `resident_subtype === 'projected_resident'` on the person's own row, "
        "where the evidence that made them projected is beside the label. A bare total "
        "with nothing beside it was the poorer of the two copies. The field stays in the "
        "manifest because the mint tools derive it and validate.py holds it."),
    # -------------------------------------------------------------------------
    # RECOVERED BY T-1313, which needed `--update` to bank six keys and found that
    # running it would have deleted these five. They were written straight into
    # layer_reads_baseline.json and never into this table — the SAME mistake
    # `flora/zone:woody_stratum.measured_from` above records against itself, repeated on
    # T-1304's profile vocabulary. `--update` rebuilds the bank from the measurement and
    # re-attaches a refusal only if it is HERE, so the first re-derivation drops every
    # one of them silently. A stated refusal is a judgement somebody made; this table is
    # the only place one may be authored, and these are moved into it verbatim.
    "residents/manifest:vocabulary.age_bands[].age_band": (
        "The closed set of age bands tools/profile_population_1835.py sorts every "
        "person into, and the rule that assigns each one. The band a person falls in "
        "is a DERIVATION over their card, not a field on it, so the browser meets it "
        "in the profile document the panel renders "
        "(data/reconstruction/1835_population_profile.json) and never here. This copy "
        "is the definition the generator is held to, and it un-banks the day a card "
        "starts carrying its own band."
    ),
    "residents/manifest:vocabulary.age_bands[].means": (
        "The plain-English meaning of an age band. Published beside the band for the "
        "same reason and read the same way — off the profile document, where the "
        "panel prints it — never out of the manifest."
    ),
    "residents/manifest:vocabulary.age_bands[].rule": (
        "The exact test that puts a person in an age band. It is a statement about "
        "the generator, which is what makes it worth shipping beside the layer; no "
        "renderer re-implements it, because a second implementation of a derivation "
        "rule is a second answer to the same question."
    ),
    "residents/manifest:vocabulary.reasons_for_coming[].means": (
        "What a reason term means, published beside it so a reader of the layer can "
        "check the sorting without the tool. Read off the profile document by the "
        "panel, never out of the manifest."
    ),
    "residents/manifest:vocabulary.reasons_for_coming[].term": (
        "The closed set of reasons a household may state for coming to Chicago. A "
        "household record carries its reason as PROSE and the term is the derivation "
        "over it, so the panel prints the term out of the profile document; a card "
        "printing the LIST would be printing the schema rather than anything about "
        "the town."
    ),
    # -------------------------------------------------------------------------
    # T-1233 ruled on the 83 unread resident paths: 63 were wired to the card in the
    # same commit, `_merged_doc` was classified as prose, and these twelve are refused
    # in writing. Every one of them is either a foreign key, a file route, a tally, or
    # the poorer of two copies of something the card already shows from the record —
    # the three shapes this table was already refusing before the ticket reached it.
    "residents/manifest:merged[].person": (
        "T-0839's redirect table, keyed by foreign key. `person` and the three ids "
        "beside it name which card was folded into which; they are how a crosswalk "
        "resolves a stale id, not a figure about anybody. The fold itself now reaches "
        "the visitor on the surviving person's own card, from the record's "
        "`merged_from` block, with the rule and the reasoning that made it."),
    "residents/manifest:merged[].household": (
        "The same foreign key at household scope, refused for the same reason."),
    "residents/manifest:merged[].merged_into_person": (
        "The other end of the same redirect. It resolves an id and states nothing "
        "about a person."),
    "residents/manifest:merged[].merged_into_household": (
        "The other end of the same redirect at household scope."),
    "residents/manifest:merged[].record_file": (
        "File routing — where the folded record is kept whole under "
        "data/residents/merged/. The same class of key as `file`, which this census "
        "strips as machinery wherever it is not nested inside a table."),
    "residents/manifest:merged[].rule": (
        "The manifest's flat copy of the fold's rule. The RECORD's `merged_from[].rule` "
        "is what residents.js shows, beside the cluster, the ticket and the note that "
        "says what the union of the cards means. Showing the manifest's bare copy would "
        "be showing less, which is the ruling this table already makes about "
        "`households[].present_on_scene_date`."),
    "residents/manifest:merged[].cluster": (
        "The same flat copy of the cluster name, refused for the same reason."),
    "residents/manifest:merged[].ticket": (
        "The same flat copy of the ticket, refused for the same reason."),
    "residents/manifest:counts.merged_away": (
        "A tally of the redirect table's rows. Each fold reaches a visitor where it can "
        "be checked — on the card of the person it was folded into — and a bare total "
        "beside no list is the shape this table already refused for `counts.households`. "
        "tools/validate.py holds it equal to the rows of `merged[]`, which is where a "
        "disagreement should surface."),
    "residents/manifest:counts.reconstructed_removed_in_2026_09_02_synthesis": (
        "Bookkeeping about an OPERATION, not a figure about the town: how many "
        "reconstructed cards the synthesis of 2 September 2026 removed. The town it "
        "describes no longer exists in this tree, so a visitor has nothing to hold it "
        "against; `by_grade.reconstructed` — which reads 0 — is the fact about the "
        "layer, and the removal itself is docs/LIBERTIES.md's business."),
    "residents/manifest:households[].projected_resident": (
        "The flat copy of a person-level subtype. `people.js` filters and chips "
        "`resident_subtype === 'projected_resident'` on the person's own row, where the "
        "evidence that made them projected sits beside the label; the household's "
        "boolean carries none of it. The identical ruling T-0782 made about "
        "`counts.projected_residents`, one level down."),
    "residents/manifest:vocabulary.resident_subtypes": (
        "A closed vocabulary tools/validate.py holds the records against — its one "
        "term, `projected_resident`, reaches the visitor as the People directory's "
        "filter and row mark. A card that printed the LIST would be printing the "
        "schema rather than anything about the town."),
    "residents/household:source_pass": (
        "T-0599/T-0604: provenance for the three mint tools' OWN bookkeeping — which pass "
        "(documented/placed/letter_list) minted this record, so a re-run can tell 'a "
        "household I minted' from a plain hand-authored one without an id prefix. Not a "
        "finding about the person: the evidence the panel already shows — grade, "
        "letter_list_only, sources — is what a visitor judges the record by, and which "
        "internal tool produced it is not part of that judgment. See "
        "data/residents/README.md."),
}

STATES = ("mesh", "shown", "probe")


# ---------------------------------------------------------------------------
# the renderer, read as text
# ---------------------------------------------------------------------------

def strip_js_comments(src: str) -> str:
    """Remove `//` and `/* */` comments without touching string bodies.

    A character-level pass rather than a regex, because this project's renderer
    is full of URLs in strings and shader source in template literals, and both
    of the obvious regexes get one of them wrong.
    """
    out: list[str] = []
    i, n = 0, len(src)
    quote = None
    while i < n:
        c = src[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "'\"`":
            quote = c
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def renderer_text() -> str:
    """Every renderer source, comments stripped, concatenated."""
    parts = []
    for path in sorted(RENDERER.glob("*.js")):
        if path.name in RENDERER_SKIP:
            continue
        parts.append(strip_js_comments(path.read_text(encoding="utf-8")))
    return "\n".join(parts)


def reads_leaf(src: str, path: str) -> bool:
    """Does the renderer access this field anywhere?

    The bare form — `.leaf` or `['leaf']` — for a leaf whose name is the
    record's alone; the parent-qualified form for one that collides with the
    renderer's own vocabulary.
    """
    parts = [p for p in re.split(r"[.\[\]]+", path) if p]
    leaf = parts[-1]
    parent = parts[-2] if len(parts) > 1 else None
    if leaf in AMBIGUOUS_LEAVES and parent:
        stem = re.escape(parent)
        pats = [rf"{stem}\s*\??\.\s*{re.escape(leaf)}\b",
                rf"{stem}\s*\[\s*['\"]{re.escape(leaf)}['\"]\s*\]"]
    else:
        pats = [rf"\.\s*{re.escape(leaf)}\b",
                rf"\[\s*['\"]{re.escape(leaf)}['\"]\s*\]"]
    return any(re.search(p, src) for p in pats)


def layer_is_opened(src: str, layer: str) -> bool:
    """Does the renderer fetch this layer's directory at all?

    The strongest form of the question, and the one that settles `data/fauna`
    without any per-field scanning: a renderer that never names the directory
    has read none of it. Both readers of `data/flora` build their URL the same
    way — `new URL('flora/index.json', dataBase)` — so the directory name in a
    string literal is what a read looks like from here.
    """
    return bool(re.search(rf"['\"`]{re.escape(layer)}/", src))


# ---------------------------------------------------------------------------
# the data, walked to leaves
# ---------------------------------------------------------------------------

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def field_paths(obj, prefix: str = "") -> dict[str, int]:
    """Every LEAF path in a record, with how many times it occurs.

    A list of records recurses as `<key>[]`; a list of numbers is a leaf, because
    `elev_m: [1.18, 3.0]` is one figure and not two.

    A key whose value is `null` is NOT counted. `july.inflorescence: null` on the
    57 species that carry no flower on 1 July is the absence of a figure stated
    in the place a figure would go, and counting it would put the same path in
    the map twice — once as the flowering block's parent and once as a leaf.
    """
    out: dict[str, int] = {}

    def walk(node, pre):
        if isinstance(node, dict):
            for k, v in node.items():
                p = f"{pre}.{k}" if pre else k
                if v is None:
                    continue
                if isinstance(v, dict):
                    walk(v, p)
                elif isinstance(v, list) and v and isinstance(v[0], dict):
                    for it in v:
                        walk(it, p + "[]")
                else:
                    out[p] = out.get(p, 0) + 1
        return out

    return walk(obj, prefix)


def merge(into: dict[str, int], more: dict[str, int]) -> None:
    for k, v in more.items():
        into[k] = into.get(k, 0) + v


def layer_records() -> dict[str, dict[str, int]]:
    """Every field path in every layer, by layer and record kind."""
    found: dict[str, dict[str, int]] = {}
    for layer in LAYERS:
        base = DATA / layer
        if not base.exists():
            continue
        manifest = base / "index.json"
        if manifest.exists():
            found.setdefault(f"{layer}/manifest", {})
            merge(found[f"{layer}/manifest"], field_paths(load(manifest)))
        for kind, sub in LAYER_KINDS[layer]:
            d = base / sub
            if not d.exists():
                continue
            key = f"{layer}/{kind}"
            found.setdefault(key, {})
            for path in sorted(d.glob("*.json")):
                merge(found[key], field_paths(load(path)))
    return found


def is_machinery(path: str) -> bool:
    leaf = [p for p in re.split(r"[.\[\]]+", path) if p][-1]
    return leaf in MACHINERY_LEAVES


def classify() -> dict:
    """Every figure in both layers, sorted into the four states."""
    found = layer_records()
    src = renderer_text()
    out = {
        "kinds": {},
        "unread": {},        # "<kind>:<path>" -> {"records": n}
        "declared": {},      # "<kind>:<path>" -> state
        "machinery": [],
        "ghosts": [],        # declared read, expression not in the renderer
        "phantoms": [],      # banked unread, and the renderer reads it
        "shared": [],        # unread, leaf name read under another record kind
        "opened": {layer: layer_is_opened(src, layer) for layer in LAYERS},
    }
    # A leaf name declared read anywhere is a name the text scan cannot attribute
    # to one record kind: `common` is read off a plant, and an animal has one
    # too. Those paths are exempted from the reverse scan and listed, rather than
    # given a scan that cannot fail honestly.
    read_leaves = {[p for p in re.split(r"[.\[\]]+", path) if p][-1]
                   for decl in READS.values() for path in decl}
    for kind, paths in sorted(found.items()):
        layer = kind.split("/")[0]
        declared = READS.get(kind, {})
        counts = {"figures": 0, "mesh": 0, "shown": 0, "probe": 0,
                  "unread": 0, "machinery": 0, "records": len(paths)}
        for path, n in sorted(paths.items()):
            key = f"{kind}:{path}"
            if path in declared:
                state, expr = declared[path]
                out["declared"][key] = state
                counts["figures"] += 1
                counts[state] += 1
                if expr not in src:
                    out["ghosts"].append((key, expr))
                continue
            if is_machinery(path):
                counts["machinery"] += 1
                out["machinery"].append(key)
                continue
            counts["figures"] += 1
            counts["unread"] += 1
            out["unread"][key] = {"records": n}
            leaf = [p for p in re.split(r"[.\[\]]+", path) if p][-1]
            if not out["opened"][layer]:
                # The layer rule already settles it, absolutely: no renderer
                # opens the directory, so no field in it is read.
                continue
            if ((leaf in read_leaves or leaf in STATED_SHARED)
                    and leaf not in AMBIGUOUS_LEAVES):
                out["shared"].append(key)
                continue
            if reads_leaf(src, path):
                out["phantoms"].append(key)
        out["kinds"][kind] = counts
    # A declaration for a path that is no longer in the data is a ghost too: the
    # map would go on asserting a read of a figure nobody ships.
    for kind, declared in sorted(READS.items()):
        present = found.get(kind, {})
        for path in sorted(declared):
            if path not in present:
                out["ghosts"].append((f"{kind}:{path}", "the data no longer carries it"))
    return out


# ---------------------------------------------------------------------------
# K41's residual, asked of a read-set
# ---------------------------------------------------------------------------

def own_field_paths(node: dict, prefix: str) -> set[str]:
    """The leaf paths a node's own citation supports.

    Stops at any nested node that carries its own `sources`, which is the node
    that citation supports instead.
    """
    out: set[str] = set()

    def walk(n, pre, root):
        if not isinstance(n, dict):
            return
        if not root and n.get("sources"):
            return
        for k, v in n.items():
            p = f"{pre}.{k}" if pre else k
            if v is None:
                continue
            if isinstance(v, dict):
                walk(v, p, False)
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                for it in v:
                    walk(it, p + "[]", False)
            else:
                out.add(p)

    walk(node, prefix, True)
    return out


def blocked_sources() -> set[str]:
    out = set()
    for path in sorted((DATA / "sources").glob("*.json")):
        rec = load(path)
        if isinstance(rec, dict) and rec.get("rights_status") in ("check_required", "restricted"):
            out.add(rec["id"])
    return out


def citation_census(state: dict) -> dict:
    """Where the unresolved-source citations of K41's residual actually sit.

    A citation supports the record NODE it is written on, so the question a
    read-set can answer is the ground side's coarse one: does the node this
    citation supports carry at least one figure that reaches a vertex? A
    species' `sources` covers its height, its cover fraction and its July
    colour, all of them `mesh`; a zone's covers its cover fractions and its
    prose. A node's OWN figures stop at the next node that cites its own
    sources, so a zone does not inherit its species' geometry — otherwise every
    citation in the file would be geometry-bearing by containment and the
    number would mean nothing.
    """
    blocked = blocked_sources()
    mesh_paths = {k for k, s in state["declared"].items() if s == "mesh"}
    out = {}
    for layer in LAYERS:
        base = DATA / layer
        if not base.exists():
            continue
        by_dir = {sub: kind for kind, sub in LAYER_KINDS[layer]}
        tally = {"citations": 0, "blocked": 0, "blocked_on_mesh_node": 0}
        for path in sorted(base.rglob("*.json")):
            kind = ("manifest" if path.name == "index.json"
                    else by_dir.get(path.parent.name, "zone"))
            key = f"{layer}/{kind}"

            def walk(node, pre):
                if isinstance(node, dict):
                    cited = [s for s in (node.get("sources") or []) if isinstance(s, str)]
                    if cited:
                        tally["citations"] += len(cited)
                        hit = [s for s in cited if s in blocked]
                        tally["blocked"] += len(hit)
                        if hit:
                            own = own_field_paths(node, pre)
                            if any(f"{key}:{p}" in mesh_paths for p in own):
                                tally["blocked_on_mesh_node"] += len(hit)
                    for k, v in node.items():
                        p = f"{pre}.{k}" if pre else k
                        if isinstance(v, dict):
                            walk(v, p)
                        elif isinstance(v, list):
                            for it in v:
                                if isinstance(it, dict):
                                    walk(it, p + "[]")
            walk(load(path), "")
        out[layer] = tally
    return out


# ---------------------------------------------------------------------------
# the assertions
# ---------------------------------------------------------------------------

def read_bank() -> dict[str, dict]:
    if not BASELINE.exists():
        return {}
    return load(BASELINE).get("entries", {})


def evaluate(state: dict, bank: dict[str, dict]) -> list[str]:
    """The five assertions, as a pure function of what was measured."""
    problems: list[str] = []

    # 2 — a read declaration that is no longer a read.
    for key, expr in state["ghosts"]:
        problems.append(
            f"{key} is declared a read of `{expr}` and the renderer does not contain it. "
            f"A read-set that has stopped being true excuses every omission behind it — "
            f"re-point the declaration at the expression that reads the field, or move the "
            f"field to the unread bank with --update")

    # 3a — absolute: a layer with no declared read is a layer the renderer must
    # not open, and a layer with declared reads must be opened. This is the
    # strong half of assertion 3 and the whole of it for `data/fauna`.
    for layer, opened in sorted(state["opened"].items()):
        declares = any(READS.get(f"{layer}/{k}") for k in RECORD_KINDS)
        if declares and not opened:
            problems.append(
                f"data/{layer} has declared reads and no renderer source opens the "
                f"directory — every read declaration for this layer is describing a "
                f"renderer that no longer exists")
        if not declares and opened:
            problems.append(
                f"data/{layer} is declared unread in every record kind and a renderer "
                f"source now opens the directory. The layer has a reader: give it a read "
                f"map, because the whole of this layer's unread bank rests on nobody "
                f"opening it")

    # 3 — an unread figure the renderer reads.
    for key in state["phantoms"]:
        problems.append(
            f"{key} is banked as reaching nothing and the renderer accesses it. Declare it "
            f"mesh, shown or probe with the expression that reads it — a figure counted "
            f"unread while it drives the scene is the map lying in the expensive direction")

    # 4 — a new unread figure.
    for key in sorted(set(state["unread"]) - set(bank)):
        n = state["unread"][key]["records"]
        problems.append(
            f"{key} is a figure on {n} record(s) that no renderer reads, and it is not in "
            f"{BASELINE.name}. Wire it up, or bank it with --update in this commit and say "
            f"in the message why a figure nobody builds is shipped to a browser")

    # 5 — absolute: the bank may not outlive the data.
    for key in sorted(set(bank) - set(state["unread"])):
        problems.append(
            f"{key} is banked as unread and is no longer an unread figure — it was wired "
            f"up, deleted or renamed. Re-run with --update in the commit that did it, so "
            f"the bank records the repair rather than keeping its ghost")

    # 6 — T-1029. THE BANKED RECORD COUNT, held for the two layers that are
    # finished and deliberately NOT for the one still being written. See assertion 6
    # in the module docstring for the reasoning; the short of it is that a count is a
    # tally, not a claim, and gating a tally that moves for a legitimate reason
    # teaches people to re-bank without reading.
    for key in sorted(set(bank) & set(state["unread"])):
        if key.split("/", 1)[0] in COUNTS_NOT_HELD:
            continue
        banked, measured = bank[key].get("records"), state["unread"][key]["records"]
        if banked != measured:
            problems.append(
                f"{key} is banked on {banked} record(s) and is on {measured}. This layer is "
                f"not being written any more, so its unread population moving is a finding "
                f"and not bookkeeping: say what changed, then re-bank it with --update in "
                f"the commit that changed it")

    # 1 — absolute: assertion 1 is structural. Every figure is either declared or
    # banked, so an unbanked one is assertion 4 above; what is left to check is
    # that the map was applied to something at all.
    if not state["kinds"]:
        problems.append("no flora, fauna or residents records were found, so nothing was "
                        "classified and a pass here means nothing")
    return problems


def measure() -> tuple[dict, list[str]]:
    state = classify()
    state["citations"] = citation_census(state)
    return state, evaluate(state, read_bank())


def print_census(c: dict) -> None:
    print("Which of a flora, fauna or residents figure reaches a visitor — ROADMAP "
          "K42 and K52.\n")
    head = f"  {'record kind':<18}{'figures':>8}{'mesh':>7}{'shown':>7}{'probe':>7}{'unread':>8}"
    print(head)
    for kind, k in sorted(c["kinds"].items()):
        print(f"  {kind:<18}{k['figures']:>8}{k['mesh']:>7}{k['shown']:>7}"
              f"{k['probe']:>7}{k['unread']:>8}")
    total = sum(k["figures"] for k in c["kinds"].values())
    unread = sum(k["unread"] for k in c["kinds"].values())
    print(f"\n  {unread} of {total} figure(s) reach nothing:")
    for key in sorted(c["unread"]):
        print(f"    {key:<56} on {c['unread'][key]['records']:>4} record(s)"
              f"{'  — refused, and why is in the bank' if key in REFUSALS else ''}")
    print(f"\n  {len(c['machinery'])} identity/provenance key(s) are not figures and are "
          f"not asked")
    for layer, opened in sorted(c["opened"].items()):
        print(f"  data/{layer}: {'opened' if opened else 'NOT OPENED'} by any renderer "
              f"source")
    if c["shared"]:
        print(f"  {len(c['shared'])} unread figure(s) share a leaf name with a read field, "
              f"so no text scan can attribute the access and the entry is stated rather "
              f"than proven:")
        for key in sorted(c["shared"]):
            print(f"    {key}")
    for layer, t in sorted(c.get("citations", {}).items()):
        print(f"  data/{layer}: {t['citations']} citation(s), {t['blocked']} of a source "
              f"whose rights are unresolved, {t['blocked_on_mesh_node']} of those on a "
              f"record node carrying a figure that reaches a vertex")


def self_test() -> int:
    """Break each assertion in memory, against the real tree."""
    state = classify()
    state["citations"] = citation_census(state)
    bank = read_bank()
    if not state["unread"] or not bank:
        print("SELF-TEST FAIL: nothing measured, so no assertion can be exercised")
        return 1

    clean = evaluate(state, bank)
    cases: list[tuple[str, dict, dict]] = []
    # Cases that must NOT fire — a deliberate exemption is a claim too, and an
    # exemption nothing exercises is how one silently stops applying (T-1029).
    silent: list[tuple[str, dict, dict]] = []

    s2 = copy.deepcopy(state)
    s2["ghosts"].append(("flora/zone:cover.matrix_fraction", "zone.coverFractionNobodyWrote"))
    cases.append(("2 a read declaration the renderer no longer contains", s2, bank))

    s3 = copy.deepcopy(state)
    s3["phantoms"].append(sorted(state["unread"])[0])
    cases.append(("3 an unread figure the renderer reads", s3, bank))

    s4 = copy.deepcopy(state)
    s4["unread"]["flora/zone:cover.invented_fraction"] = {"records": 10}
    cases.append(("4 a new figure nobody reads", s4, bank))

    b5 = copy.deepcopy(bank)
    b5["flora/zone:a_figure_that_left"] = {"records": 1}
    cases.append(("5 a banked figure that left the data", state, b5))

    # T-1029. Assertion 6 is a DECISION as much as an assertion, so both halves of
    # it are exercised: the held layer must fire and the unheld one must stay
    # silent. A count gate that quietly spread to `residents/` would be a
    # 61-path false alarm on every research ticket, and nothing else would notice.
    held = next(k for k in sorted(bank) if k.split("/", 1)[0] not in COUNTS_NOT_HELD)
    b6 = copy.deepcopy(bank)
    b6[held] = {**b6[held], "records": b6[held]["records"] + 7}
    cases.append((f"6 a banked count that moved in a finished layer ({held})", state, b6))

    unheld = next((k for k in sorted(bank) if k.split("/", 1)[0] in COUNTS_NOT_HELD), None)
    if unheld:
        b6b = copy.deepcopy(bank)
        b6b[unheld] = {**b6b[unheld], "records": b6b[unheld]["records"] + 7}
        silent.append((f"6 a banked count that moved in a layer still being written "
                       f"({unheld})", state, b6b))

    # A layer nothing declares a read for, opened by the renderer. It used to be
    # `fauna` and ROADMAP K51 gave that layer a read map, at which point the case
    # could no longer be constructed out of the repository's own state and went
    # SILENT — a self-test that stops firing because the world moved is the same
    # expired control the layer scan's negative half was. A synthetic layer name
    # holds the assertion whatever this repository contains.
    s3a = copy.deepcopy(state)
    s3a["opened"]["a_layer_with_no_read_map"] = True
    cases.append(("3a the renderer opens a layer declared unread", s3a, bank))

    s3b = copy.deepcopy(state)
    s3b["opened"]["flora"] = False
    cases.append(("3a a layer with declared reads that nothing opens", s3b, bank))

    ok = True
    for label, s, b in cases:
        fired = len(evaluate(s, b)) > len(clean)
        print(f"  {'fires' if fired else 'SILENT'}  {label}")
        ok = ok and fired
    for label, s, b in silent:
        fired = len(evaluate(s, b)) > len(clean)
        print(f"  {'FIRES' if fired else 'quiet'}  {label} — must not fire")
        ok = ok and not fired

    # The two scans are the load-bearing part of assertions 2 and 3, so they are
    # exercised directly: each must be able to say yes AND no.
    src = renderer_text()
    checks = [
        ("the comment stripper removes a line comment",
         "kept" in strip_js_comments("const a = 1; // dropped\nconst b = 'kept';")
         and "dropped" not in strip_js_comments("const a = 1; // dropped\nconst b = 'kept';")),
        ("the comment stripper keeps a string that looks like one",
         "//x" in strip_js_comments("const u = 'http://x';")),
        ("the comment stripper removes a block comment",
         "dropped" not in strip_js_comments("/* dropped */ const a = 1;")),
        ("the renderer text no longer contains the comment that names an unread field",
         "bare_soil_fraction: 0.45" not in src),
        ("the reverse scan sees a read it should see",
         reads_leaf(src, "cover.matrix_fraction")),
        # THE NEGATIVE EXAMPLE HAS TO BE A FIGURE NOBODY ACTUALLY READS, so it
        # moves when one gets wired up — which is the assertion working, not
        # eroding. This was `cover.standing_water_fraction` until T-0281 put the
        # plants on a card and showed it. `cover.litter_fraction` is the
        # replacement: one record carries it, it is banked as unread, and nothing
        # under renderers/ has ever opened it.
        ("the reverse scan does not see a field nobody reads",
         not reads_leaf(src, "cover.litter_fraction")),
        ("the parent-qualified form is used for an ambiguous leaf",
         not reads_leaf(src, "ground.rgb") and reads_leaf(src, "diffuseColor.rgb")),
        ("the layer scan sees the layer the renderer does open",
         all(layer_is_opened(src, layer) for layer in LAYERS)),
        # T-0021. `data/residents` had two readers and no read map for eleven
        # days, because this file's layer list was two names long and 3a can only
        # fail for a layer it walks. The control is that every layer with a map
        # is walked and every layer walked has a map — a blind gate and a wrong
        # gate are the same outcome from a visitor's side.
        ("every declared layer is a layer this file walks",
         {k.split("/")[0] for k in READS} == set(LAYERS)),
        # The negative half used to be `not layer_is_opened(src, "fauna")`, and
        # ROADMAP K51 gave that layer a reader — at which point a control written
        # against the repository's own state stops being a control and becomes a
        # second copy of the measurement. It is a synthetic source now: a scanner
        # that cannot say no about a directory nothing names is broken whatever
        # this repository happens to contain today.
        ("the layer scan does not see a layer a source does not open",
         not layer_is_opened("const u = new URL('flora/index.json', dataBase);", "fauna")),
    ]
    for label, passed in checks:
        print(f"  {'ok   ' if passed else 'FAIL '}  {label}")
        ok = ok and passed

    print("SELF-TEST PASS" if ok else "SELF-TEST FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", action="store_true", help="exit 1 on a divergence")
    ap.add_argument("--quiet", action="store_true", help="print only the verdict")
    ap.add_argument("--self-test", action="store_true",
                    help="break each assertion in memory and check that it fires")
    ap.add_argument("--update", action="store_true", help="rewrite the baseline")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    state, problems = measure()

    if args.update:
        BASELINE.write_text(json.dumps({
            "_doc": "Every figure in data/flora and data/fauna that no renderer reads, as "
                    "of the last deliberate change. A figure is a leaf of a record that is "
                    "not identity, file routing or provenance; 'reads' is scanned against "
                    "renderers/web/js/*.js with the comments stripped. This is a "
                    "measurement and not a permission: tools/measure_layer_reads.py holds "
                    "it exact in both directions, so a new one fails and a wired-up one "
                    "has to be un-banked here in the commit that wired it. Read ROADMAP "
                    "K42 before adding a line. `refused_because` is a STATED REFUSAL "
                    "(T-0021): somebody decided this figure should not reach a visitor "
                    "and wrote down why. It is not a permission and it does not soften "
                    "any assertion — the entry is banked exactly like every other. The `records` "
                    "count is HELD EXACTLY for flora and fauna, which are finished "
                    "datasets, and is a dated tally for residents, which is the layer "
                    "this project is still writing — see assertion 6 in "
                    "tools/measure_layer_reads.py for why the line is drawn there "
                    "(T-1029).",
            "entries": {k: ({**state["unread"][k], "refused_because": REFUSALS[k]}
                             if k in REFUSALS else state["unread"][k])
                        for k in sorted(state["unread"])},
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {BASELINE.relative_to(ROOT)} ({len(state['unread'])} entries)")
        return 0

    if not args.gate and not args.quiet:
        print_census(state)

    for p in problems:
        print(f"FAIL  {p}", file=sys.stderr)
    if problems:
        return 1

    total = sum(k["figures"] for k in state["kinds"].values())
    unread = sum(k["unread"] for k in state["kinds"].values())
    mesh = sum(k["mesh"] for k in state["kinds"].values())
    fauna = sum(k["unread"] for kind, k in state["kinds"].items()
                if kind.startswith("fauna/"))
    residents = sum(k["unread"] for kind, k in state["kinds"].items()
                    if kind.startswith("residents/"))
    shown = sum(k["shown"] for k in state["kinds"].values())
    if args.gate or args.quiet:
        # "which no renderer opens" stood on this line until ROADMAP K51, and by
        # then it was false. A summary is a claim like any other here: `shown` is
        # counted separately from `mesh` because a value a visitor reads on a
        # card and a value that moves a vertex are different answers, and rolling
        # them together is how a layer with no geometry starts sounding drawn.
        print(f"layer reads: {mesh} of {total} flora/fauna/residents figure(s) reach a "
              f"vertex, {shown} reach a visitor as text on a card, {unread} reach nothing, "
              f"{fauna} of those in data/fauna and {residents} in data/residents "
              f"({len(REFUSALS)} of them refused in writing); the unread population is "
              f"banked and may not grow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
