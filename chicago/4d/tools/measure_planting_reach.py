#!/usr/bin/env python3
"""Whether a routed woody record can be PLACED — the step after K44's cohort.

ROADMAP K45(a). K44 measured routing: which reader is handed the record. It said
in its own docstring that it does not ask whether a routed record then reaches
the ground, and it named the repair its finding 2 implies —

    "Add `z08_lakeshore` to `TIMBER_ZONES` and the four dune records are drawn
     by the archetypes that already exist."   (docs/LIBERTIES.md L113)

That sentence has two assumptions in it and this file measures both, because
neither is true.

**`TIMBER_ZONES` is a species table, not a placement list.** `trees.js` opens
those four zone files to build one render spec per species — height, crown width,
July foliage, density, confidence — and then throws the zone away. Placement is
`COMMUNITIES`: four hand-written mixes selected by heightfield rules (distance to
water, which land division, a generated relief field), and a stem's species comes
from `pick(mix, rnd())`. A zone's `extent` is never consulted here at all. The
proof is already committed: `z07_bur_oak_savanna`'s declared extent box is
E -2600..-600, N -6400..-4400 — 4.4 km outside the modelled field in the nearest
direction — and its two oaks are drawn anyway, out of the `ridge_oak` mix.

So a woody record reaches a stem only if its species id is in one of those mixes
or is named at an `addTree` call site. **A record whose species is in neither is
routed, archetyped, and selected by nothing** — the same shape of loss K44
measured one level out, and invisible from there for the same reason: K44's
question is answered by the file that receives the record, and this one is
answered by a literal inside it.

**The woody planter WAS a fixed box inside a field four times its size**, and
ROADMAP K45(b2) carried it over the field. It swept `-half..+half` in both axes,
`half = 320 - step`, while the heightfield S2e carried east runs E -320..+1700,
so 73 % of the ground above its own dry floor had never had a stem offered to it
while `flora.js`'s camera-centred lattice reached all of it. It now sweeps the
field inset by one planting step, and the question moved with it: what the loop
may VISIT is nearly everything, and what may GROW there is `communityAt`'s
answer. Both declarations are still scanned rather than restated, because the
asymmetry was the finding and an asymmetry quoted from memory is an anecdote.

**And the timber has an east end, which the square used to supply by accident.**
Andreas runs the South Division belt "east as far as Wells Street" and excepts
"the sandy hills near the lake" from the North Division's timber; the old
square's edge stood at E +316, 13 m short of Wells and 510 m short of the State
Street break-of-slope where `z09_sand_prairie` starts the beach ridges. Both
limits are read by the renderer out of `data/streets/1835.json` and banked here
EXACTLY — a wood that reaches further east is an argument about a source, not a
repair.

**And the weight beside the species id is a FALLBACK.** ROADMAP K45(b1). The
literal in `COMMUNITIES` is documented as *"the dossier's per-species
densities"*, and since ROADMAP K46 it is also the number that plants the stem.
It was not until then: `mixes` was rebuilt as `records.density[id] ?? fallback`,
one global midpoint per species taken from whichever `TIMBER_ZONES` entry named
it first, and seventeen of the twenty-six entries ran at a number other than the
one they are written to. K46 kept the literal because the alternative cannot
express the file: `wet_woods` cites ZONE 6a and `mesic_pocket` cites ZONE 6b and
both resolve to the one record `z06_dense_forest`, so a zone-keyed density gives
the elm 60 in both and the 12 that makes it incidental has nowhere to live.

The record is now the CONSTRAINT. Every weight is scanned against the band of
each zone its community's `zones` field names, and one that falls outside every
such band must be declared in that community's `departures`. Both the weight and
its verdict are banked, so neither a moved number nor a departure that appears
or disappears can pass unread.

    tools/measure_planting_reach.py             print the census
    tools/measure_planting_reach.py --gate      exit 1 on a divergence
    tools/measure_planting_reach.py --self-test break each assertion, in memory
    tools/measure_planting_reach.py --update    rewrite the baseline

FIVE ASSERTIONS.

1.  **(absolute) Every declaration this gate reads is still in the renderer**,
    and `trees.js` still has exactly the banked number of `addTree` call sites.
    A scanner that cannot find its declaration RAISES rather than returning an
    empty set: an empty mix would call every species unselectable and bank it,
    and an unseen third call site would call an unselectable species drawn.

2.  **(absolute, banked; the domain may grow and may not shrink, the east
    limits may not move at all) The woody planter's domain.** The swept bounds
    scanned out of the planting loop — their FORM, since K45(b2) derives them
    from the heightfield rather than writing a number — the field they sit
    inside, how many of the heightfield's nodes stand above the planter's OWN
    dry floor inside them and outside them, and how much of what it now reaches
    lies east of the documented limits and is therefore swept and refused. The
    east limits themselves are banked with the street each is read from, and
    that `communityAt` still applies them: a limit that is loaded and consulted
    by nothing is the loss K45(a) measured one level out.

3.  **(absolute, banked both ways) Every woody species a `TIMBER_ZONE`
    contributes, whose form has an archetype, that no community mix and no
    direct call site can select.** New one fails; a banked one that has become
    selectable fails until it is un-banked in the commit that placed it. This is
    the assertion that refuses L113's repair: adding `z08_lakeshore` puts two
    poplars into this bank and draws nothing.

4.  **(absolute, banked both ways) Every zone in `TIMBER_ZONES` that declares an
    extent box, with whether that box meets the woody planter's domain.** `z07`
    is banked as `outside-the-planter` and is drawn regardless, which is the
    routing-is-not-placement fact held in a file instead of in a paragraph.

5.  **(absolute, banked both ways) Every mix entry's weight, the bands its own
    community's zones record for that species, and whether it sits inside one.**
    A new entry, a departed one, a moved number or a departure that appears or
    disappears fails until it is re-banked. Each community's `zones` field is
    held equal to the `ZONE n` numbers in its own `dossier` prose, so the
    citation a reader sees and the bands the loader checks against cannot drift
    apart. The rule itself is scanned: if `trees.js` goes back to overriding the
    literal with a global midpoint, or stops checking the weight against the
    cited bands at all, this assertion RAISES rather than quietly banking a
    verdict nothing enforces.

THE LIMIT, stated rather than discovered later. `standsDry` is one of several
tests a stem must pass — `terrain.isWater()` is a traced mask, buildings block,
the community classifier returns null over most of the box, and the per-hectare
roll refuses most of what is left. So the land census here is an UPPER bound on
plantable ground, not a count of stems: it answers "could the loop ever visit
this point", which is the question a reach measurement is for. The stems actually
built are `trees.stats`, and they are the smoke's business, not this file's.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import measure_layer_reads as k42      # noqa: E402  (strip_js_comments)
import measure_flora_reach as k44      # noqa: E402  (the cohort this file follows)

DATA = ROOT / "data" / "flora"
TERRAIN = ROOT / "data" / "terrain" / "epochs"
RENDERER = ROOT / "renderers" / "web" / "js"
BASELINE = ROOT / "tools" / "planting_reach_baseline.json"

FLORA_JS = "flora.js"
TREES_JS = "trees.js"

EPOCH = "e1834_harbor_cut"

# Why a routed woody record can never be selected. Named rather than free text,
# for the reason K44 names its own: a bank of reasons is only worth having if two
# runs spell them the same way.
UNSELECTABLE_REASONS = {
    "in-no-community-mix": "its species is in no COMMUNITIES mix and at no addTree call site",
}

# The weight in COMMUNITIES is the weight that places a stem (ROADMAP K46). The
# verdict is about its STANDING against the record, which is now the constraint:
# the first two are allowed to stand and the last three are faults.
VERDICTS = {
    "inside-its-band": "inside a band its own community's zones record",
    "declared-departure": "outside every band its community cites, and declared with its "
                          "reason in that community's `departures`",
    "undeclared-departure": "outside every band its community cites, and declared nowhere "
                            "— an ecological claim no source carries",
    "stale-departure": "declared as a departure and no longer outside its cited bands — "
                       "a note claiming a disagreement that has been repaired",
    "no-band-in-its-zones": "no zone this community cites records a density for the "
                            "species, so the weight is constrained by nothing",
}

# Whether a zone's declared extent box meets the ground the woody planter sweeps.
BOX_VERDICTS = {
    "meets-the-planter": "the declared box overlaps the swept domain",
    "outside-the-planter": "the declared box is wholly outside the swept domain",
    "no-box": "the extent declares no box, so it is bounded by its kind alone",
}


# ---------------------------------------------------------------------------
# the renderer, read for its placement declarations
# ---------------------------------------------------------------------------

def renderer_source(name: str) -> str:
    """One renderer file with its comments stripped.

    Stripped for K42's reason and then for one of this file's own: `trees.js`
    discusses `TIMBER_ZONES` and the community mixes in prose at length, and a
    scan that matches its own commentary would find a sycamore in a mix that has
    never held one.
    """
    path = RENDERER / name
    if not path.exists():
        raise LookupError(f"{path.relative_to(ROOT)} is not there — this gate is "
                          f"describing a renderer that no longer exists")
    return k42.strip_js_comments(path.read_text(encoding="utf-8"))


def js_number(src: str, pattern: str, what: str, where: str) -> float:
    m = re.search(pattern, src)
    if not m:
        raise LookupError(f"{where} no longer declares {what} — this gate measures the "
                          f"planter's reach from it, and a missing bound would read as "
                          f"a planter that sweeps everything")
    return float(m.group(1))


def bracketed(src: str, start: int) -> str:
    """The text inside the `[...]` that opens at `start`, brackets balanced.

    A regex cannot do this and a non-greedy one is worse than useless here: the
    mixes are written several lines long with a `],` closing each species pair,
    so `\\[(.*?)\\],` stops two entries in and reports a community that holds a
    quarter of its own species. It did exactly that on the first run of this
    file, and called six placed trees unselectable.
    """
    depth = 0
    for i in range(start, len(src)):
        if src[i] == "[":
            depth += 1
        elif src[i] == "]":
            depth -= 1
            if depth == 0:
                return src[start + 1:i]
    raise LookupError(f"{TREES_JS} has an unclosed `[` at offset {start} — this gate "
                      f"reads a community's species list out of it")


def community_blocks(src: str) -> list[tuple[str, str]]:
    """Each community's key and its block of source, in declaration order."""
    m = re.search(r"const COMMUNITIES\s*=\s*\{(.*?)\n\};", src, re.S)
    if not m:
        raise LookupError(f"{TREES_JS} no longer declares `COMMUNITIES` as an object — "
                          f"every stem's species comes out of it, so an empty one would "
                          f"call the whole town unselectable")
    body = m.group(1)
    keys = [(mm.group(1), mm.start()) for mm in re.finditer(r"^  (\w+):\s*\{", body, re.M)]
    out = []
    for i, (key, start) in enumerate(keys):
        end = keys[i + 1][1] if i + 1 < len(keys) else len(body)
        out.append((key, body[start:end]))
    if not out:
        raise LookupError(f"{TREES_JS} declares no communities this gate can read")
    return out


def mix_entries(block: str, key: str) -> dict[str, list[tuple[str, float]]]:
    """`{ 'mix': [(species, weight), ...], 'edgeMix': [...] }` for one community."""
    lists: dict[str, list[tuple[str, float]]] = {}
    for name in ("mix", "edgeMix"):
        lm = re.search(rf"\b{name}:\s*\[", block)
        if lm:
            inner = bracketed(block, lm.end() - 1)
            lists[name] = [(sp, float(w))
                           for sp, w in re.findall(r"\['(\w+)',\s*([\d.]+)\]", inner)]
    if not lists:
        raise LookupError(f"{TREES_JS} community `{key}` declares no `mix` this gate "
                          f"can read — a community with no readable mix would hide "
                          f"every species it holds")
    return lists


def community_mixes(src: str) -> dict[str, dict[str, list[str]]]:
    """`const COMMUNITIES = { key: { mix: [['id', w], ...], edgeMix: [...] } }`.

    Returns the species ids per community per list. The weights are read by
    `mix_weights` below rather than here: this function's question is whether
    `pick()` can ever return the id at all, which the weight cannot answer —
    the literal beside the id is a fallback, and `records.density` usually
    replaces it (ROADMAP K45(b1)).
    """
    return {key: {name: [sp for sp, _ in entries]
                  for name, entries in mix_entries(block, key).items()}
            for key, block in community_blocks(src)}


def mix_weights(src: str) -> dict[str, dict]:
    """Every mix entry's weight, the zones its community cites, and its departures.

    The literal is a PER-COMMUNITY figure — `ulmus_americana` is written 60 in
    the swamp thicket and 12 in the mesic pocket — and since ROADMAP K46 it is
    the figure that plants the stem. Two independent statements of where it came
    from are read here and held equal: the `dossier` prose a reader sees, and
    the `zones` list the loader checks the weight against. They are the same
    citation written twice, and a gate that read only one of them would let the
    other drift.
    """
    out: dict[str, dict] = {}
    for key, block in community_blocks(src):
        dm = re.search(r"dossier:\s*'([^']*)'", block)
        if not dm:
            raise LookupError(f"{TREES_JS} community `{key}` no longer carries a `dossier` "
                              f"line — it is where the weights say they come from, and "
                              f"this gate holds the machine-readable `zones` against it")
        zm = re.search(r"zones:\s*\[([^\]]*)\]", block)
        if not zm:
            raise LookupError(f"{TREES_JS} community `{key}` declares no `zones` — it is "
                              f"the list the loader takes its constraint bands from, and "
                              f"a community with none is weighted by nothing at all")
        zones = re.findall(r"'([^']*)'", zm.group(1))
        dossier_zones = sorted(set(re.findall(r"ZONE (\d+)", dm.group(1))))
        # The two citations, reconciled. `ZONE 6a`, `6b` and `6c` all live in the
        # one record `z06_dense_forest`, which is the whole reason K46 kept the
        # hand weights — so the comparison is on the zone NUMBER, not the suffix.
        from_zones = sorted({re.sub(r"^z0?", "", z.split("_")[0]) for z in zones})
        if from_zones != dossier_zones:
            raise LookupError(f"{TREES_JS} community `{key}` cites ZONE "
                              f"{', '.join(dossier_zones)} in its dossier and reads bands "
                              f"from {', '.join(zones)} — the prose and the constraint "
                              f"disagree about which record backs this community")
        out[key] = {
            "dossier_zones": dossier_zones,
            "zones": zones,
            "departures": sorted(re.findall(r"'((?:mix|edgeMix)\.\w+)':", block)),
            "lists": mix_entries(block, key),
        }
    return out


def archetype_fallback(src: str) -> tuple[set[str], str]:
    """`SPECIES`' own keys, and the id every other species is drawn as.

    `loadTimberZones` builds a spec as `SPECIES[sp.id] ?? SPECIES.<fallback>`,
    so a placed species with no entry of its own is drawn with another species'
    bole fraction, taper, puff count and BARK COLOUR — silently, and with its
    `fromRecord` flag still true. The fallback id is scanned rather than named
    here for the usual reason: a gate that hard-codes it would keep reporting
    the elm after somebody changed it.
    """
    m = re.search(r"const SPECIES\s*=\s*\{(.*?)\n\};", src, re.S)
    if not m:
        raise LookupError(f"{TREES_JS} no longer declares `SPECIES` as an object — it is "
                          f"the draw archetype every stem is built from, and a missing one "
                          f"would report the whole town as drawn from a fallback")
    keys = set(re.findall(r"^  (\w+):\s*\{", m.group(1), re.M))
    fm = re.search(r"SPECIES\[sp\.id\]\s*\?\?\s*SPECIES\.(\w+)", src)
    if not fm:
        raise LookupError(f"{TREES_JS} no longer falls back to a default archetype as "
                          f"`SPECIES[sp.id] ?? SPECIES.<id>` — this gate reports which "
                          f"placed species are drawn as something else, and cannot say "
                          f"which one they are drawn as without that line")
    if fm.group(1) not in keys:
        raise LookupError(f"{TREES_JS} falls back to `SPECIES.{fm.group(1)}`, which is not "
                          f"a key of SPECIES — every species without its own entry would "
                          f"be drawn from `undefined`")
    return keys, fm.group(1)


def zone_archetypes(src: str) -> dict[str, set[str]]:
    """`ARCHETYPE_BY_ZONE` — the archetypes a named ZONE supplies for itself.

    ROADMAP K45(b) change one. `SPECIES` is keyed by species id and says "one
    entry per woody species drawn", which held until a species was recorded
    TWICE: `populus_deltoides` is `z05_riverbank_timber`'s 22–30 m gallery
    emergent and `z08_lakeshore`'s 5–15 m half-buried leaner, same binomial and
    nothing else the same. So a zone may declare its own archetypes and a
    community may plant from them (`specsFrom`), and this reads that table — a
    species covered by the zone its own community plants from is NOT drawn with
    the fallback's bole and bark, and reporting it as such would be a false
    finding of exactly the kind assertion 3 exists to make impossible.

    Raises rather than returning an empty map, for the same reason every
    scanner here does: an unread table would report an archetyped species as
    drawn from the elm, and a gate that says the wrong thing confidently is
    worse than one that stops.
    """
    m = re.search(r"const ARCHETYPE_BY_ZONE\s*=\s*\{(.*?)\n\};", src, re.S)
    if not m:
        raise LookupError(f"{TREES_JS} no longer declares `ARCHETYPE_BY_ZONE` as an object "
                          f"— it is where a species recorded by two zones gets its second "
                          f"set of draw parameters, and without it this gate would report "
                          f"every such species as drawn with the fallback's bark")
    body = m.group(1)
    zones = [(mm.group(1), mm.start()) for mm in re.finditer(r"^  (\w+):\s*\{", body, re.M)]
    out: dict[str, set[str]] = {}
    for i, (zone, start) in enumerate(zones):
        end = zones[i + 1][1] if i + 1 < len(zones) else len(body)
        out[zone] = set(re.findall(r"^    (\w+):\s*\{", body[start:end], re.M))
    return out


def community_specs_from(src: str) -> dict[str, str]:
    """Which zone's own archetypes each community plants with, where it says so."""
    out = {}
    for key, block in community_blocks(src):
        sm = re.search(r"specsFrom:\s*'([^']*)'", block)
        if sm:
            out[key] = sm.group(1)
    return out


def timber_zone_order(src: str) -> list[str]:
    """`TIMBER_ZONES` in DECLARATION order, which `k44.js_array` discards.

    The order used to be load-bearing: `loadTimberZones` wrote `density[sp.id]`
    only `if (!(sp.id in density))`, so a species named by two zones took its
    weight from whichever was listed first — z05's band for five of the species
    the swamp thicket and the mesic pocket weight by hand. ROADMAP K46 ended
    that, and the order is scanned now to prove the list is still a list a
    community's `zones` can name into: an unreadable `TIMBER_ZONES` would leave
    every constraint band empty and every weight unchecked.
    """
    m = re.search(r"const TIMBER_ZONES\s*=\s*\[(.*?)\];", src, re.S)
    if not m:
        raise LookupError(f"{TREES_JS} no longer declares `TIMBER_ZONES` as an array — "
                          f"assertion 5 resolves a species' running weight by walking it "
                          f"in order")
    return re.findall(r"'([^']*)'", m.group(1))


def record_density_rule(src: str) -> None:
    """Raise unless `trees.js` still plants the literal and still checks it.

    ROADMAP K46's rule is two claims, and a gate that assumed either would be
    banking a verdict nothing enforces. The first is that the weight written in
    `COMMUNITIES` is the weight `pick()` walks — a renderer that went back to
    `records.density[id] ?? fallback` would make every band verdict below a
    statement about a number that no longer places anything. The second is that
    the recorded band is still READ, per zone, and still compared: without the
    comparison the departures are prose and this assertion is banking whether a
    comment exists.
    """
    if re.search(r"records\.density\[\s*id\s*\]\s*\?\?", src):
        raise LookupError(f"{TREES_JS} has gone back to overriding the mix literal with "
                          f"`records.density[id] ?? fallback` — ROADMAP K46 made the "
                          f"written weight the one that plants the stem, and assertion 5 "
                          f"reports band verdicts on a number that would no longer run")
    if not re.search(r"bands\[id\]\[sp\.id\]\s*=\s*\[perHa\[0\], perHa\[1\]\];", src):
        raise LookupError(f"{TREES_JS} no longer keeps each zone's recorded band PER ZONE "
                          f"— it is the constraint every mix weight is checked against, "
                          f"and a loader that collapses it has nothing left to check")
    if not re.search(r"seen\.some\(\(\[lo, hi\]\) => weight >= lo && weight <= hi\)", src):
        raise LookupError(f"{TREES_JS} no longer tests a mix weight against the bands its "
                          f"own community's zones record — the departures below would be "
                          f"comments, and this assertion would bank the existence of a "
                          f"comment")
    if not re.search(r"c\.departures\?\.\[`\$\{listName\}\.\$\{id\}`\]", src):
        raise LookupError(f"{TREES_JS} no longer reads a community's `departures` when a "
                          f"weight falls outside its cited band — an undeclared departure "
                          f"has to be what raises, or declaring one means nothing")


def direct_call_sites(src: str) -> tuple[int, set[str]]:
    """How many `addTree` call sites the module has, and the ids named at them.

    THREE paths select a spec today. Two are in the source and this function can
    read them: `specs.salix_interior` at the point-bar thicket, and `specs[id]`
    where `id` came from `pick()`. The third is T-0091's planting pass, which
    selects `table[stem.species]` out of a RECORD — so the ids it can draw are
    not in this file's reach at all and are read from the dataset by
    `placed_species()` below. The COUNT is banked because a fourth path is
    exactly how this gate would go quietly wrong: an unselectable species drawn
    by a call site nobody told this file about.
    """
    sites = len(re.findall(r"\baddTree\(", src)) - len(re.findall(r"function addTree\(", src))
    named = set(re.findall(r"\bspecs\.(\w+)\b", src))
    return sites, named


def placed_species() -> dict[str, list[str]]:
    """Species id -> the zones the planting records draw it from (T-0091).

    A planting record states a stem: a species, a position and a height, for a
    tree somebody KEPT rather than one a density dealt. Those species are
    selected by no community mix and by no `specs.<id>` literal, so without this
    they would be reported unselectable — committed, cited and drawn nowhere —
    while standing in a hotel yard where anyone can walk up to them.

    Read through the manifest exactly as the renderer reads it, never by
    globbing the directory: a planting file the manifest does not name is not
    fetched by the walkthrough and must not be counted as drawn here either.
    """
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for entry in index.get("plantings", []):
        rec = json.loads((DATA / entry["file"]).read_text(encoding="utf-8"))
        zone = rec.get("zone")
        for stem in rec.get("stems", []):
            sp = stem.get("species")
            if not sp:
                raise LookupError(f"planting record {entry['file']} carries a stem with no "
                                  f"species — the renderer would decline to draw it and "
                                  f"this gate cannot say which species it reaches")
            out.setdefault(sp, [])
            if zone and zone not in out[sp]:
                out[sp].append(zone)
    return {k: sorted(v) for k, v in sorted(out.items())}


def planter_bounds(src: str, hf: dict) -> dict:
    """The woody planting loop's swept domain, and the steps that inset it.

    ROADMAP K45(b2) replaced a fixed square — `const half = 320 - step`, swept
    `-half..+half` on both axes — with the heightfield's own extent inset by one
    planting step. So this no longer reads a literal out of the renderer: it
    reads the FORM of the declaration and derives the bounds from the same
    heightfield header the land census below reads. That is the stronger gate of
    the two, because a square written as a number can be right by accident and a
    domain derived from the field cannot silently stop tracking it.
    """
    steps = [float(v) for v in re.findall(r"step:\s*([\d.]+),", src)]
    if not steps:
        raise LookupError(f"{TREES_JS} no longer declares the STEMS planting steps — the "
                          f"swept domain is the field inset by one and cannot be sized "
                          f"without them")
    decls = (
        (r"const sweepE0\s*=\s*originE \+ step;", "sweepE0 = originE + step"),
        (r"const sweepE1\s*=\s*originE \+ \(cols - 1\) \* cellM - step;",
         "sweepE1 = originE + (cols - 1) * cellM - step"),
        (r"const sweepN0\s*=\s*originN \+ step;", "sweepN0 = originN + step"),
        (r"const sweepN1\s*=\s*originN \+ \(rows - 1\) \* cellM - step;",
         "sweepN1 = originN + (rows - 1) * cellM - step"),
        (r"for \(let n = sweepN0; n <= sweepN1; n \+= step\)", "the N loop over the sweep"),
        (r"for \(let e = sweepE0; e <= sweepE1; e \+= step\)", "the E loop over the sweep"),
    )
    for pattern, what in decls:
        if not re.search(pattern, src):
            raise LookupError(
                f"{TREES_JS}'s planting loop no longer declares `{what}` — this gate's "
                f"whole domain claim is read off that loop, and a loop it cannot read "
                f"would bank a reach nothing sweeps. If the planter has been rewritten, "
                f"rewrite this scan with it (ROADMAP K45(b2))")
    dry_margin = js_number(src, r"const TREE_DRY_MARGIN_M\s*=\s*([\d.]+);",
                           "TREE_DRY_MARGIN_M", TREES_JS)
    # The widest sweep is the smallest step, which is the `full` detail level.
    # Banking the widest is banking the most generous case: a repair that has to
    # move these numbers cannot be reported done at `light`.
    step = min(steps)
    cols, rows, cell = hf["cols"], hf["rows"], hf["cell_m"]
    e0, n0 = hf["origin_e"], hf["origin_n"]
    return {
        "kind": "the modelled field inset by one planting step",
        "steps_m": sorted(steps),
        "sweep_e_m": [round(e0 + step, 3), round(e0 + (cols - 1) * cell - step, 3)],
        "sweep_n_m": [round(n0 + step, 3), round(n0 + (rows - 1) * cell - step, 3)],
        "dry_margin_m": dry_margin,
    }


def east_limits(src: str) -> dict:
    """Where the woody layer stops in the east, and the streets that say so.

    ROADMAP K45(b2). The planter used to answer this by accident: its square ran
    out at E +316. Now it sweeps the field, so `communityAt` carries the answer,
    and the answer is two street ids rather than two numbers — Andreas puts the
    South Division belt's end at Wells Street and excepts "the sandy hills near
    the lake" from the North Division's timber, which `z09_sand_prairie` places
    from the State Street break-of-slope east.

    Three things are scanned rather than assumed. The ids, out of the renderer.
    That the renderer READS them from the street records the scene index carries
    rather than carrying its own copy of two numbers — a limit quoted from a
    street has to move when the street does. And that `communityAt` actually
    applies them, because a limit that is loaded and never consulted is the exact
    shape of defect K45(a) found in `TIMBER_ZONES`: a declaration everything
    reads and nothing uses.

    The eastings themselves are then taken here from `data/streets/1835.json`,
    which is the file `tools/compile_scene.py` compiles that index FROM. The
    renderer must not fetch it directly: it is not published as itself, so a
    fetch of it passes in the source tree and 404s on the site — the exact gap
    AGENTS.md says has shipped bugs twice, and it shipped this one until the
    `--published` smoke caught it.
    """
    m = re.search(r"const TIMBER_EAST_LIMIT_STREETS\s*=\s*\{([^}]*)\}", src)
    if not m:
        raise LookupError(f"{TREES_JS} no longer declares TIMBER_EAST_LIMIT_STREETS — the "
                          f"east end of the timber is what stops the widened planter "
                          f"putting a wood on the beach, and a missing declaration would "
                          f"read as a layer with no eastern limit at all")
    ids = dict(re.findall(r"(\w+):\s*'([^']+)'", m.group(1)))
    if set(ids) != {"south", "north"}:
        raise LookupError(f"{TREES_JS}'s TIMBER_EAST_LIMIT_STREETS names {sorted(ids)} — "
                          f"this gate reads one limit per division and the divisions are "
                          f"south and north")
    if not re.search(r"timberEastLimits\(streetRecords, problems\)", src):
        raise LookupError(f"{TREES_JS} no longer derives its east limits from the street "
                          f"records handed to it — they would then be numbers copied into "
                          f"a renderer, which is how a limit and the street it cites drift "
                          f"apart")
    if not re.search(r"pts\.reduce\(\(a, p\) => a \+ p\[0\], 0\) / pts\.length", src):
        raise LookupError(f"{TREES_JS} no longer takes the mean easting of a centreline — "
                          f"this gate takes the same mean, and two different readings of "
                          f"the same street are two different limits")
    if not re.search(r"if \(e > \(d === NORTH \? eastLimit\.north : eastLimit\.south\)\) "
                     r"return null;", src):
        raise LookupError(f"{TREES_JS}'s communityAt no longer applies the east limits — "
                          f"they would be loaded and consulted by nothing, which is the "
                          f"loss ROADMAP K45(a) measured one level out")
    streets = json.loads((ROOT / "data" / "streets" / "1835.json").read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in streets.get("streets", [])}
    out = {}
    for side, sid in sorted(ids.items()):
        st = by_id.get(sid)
        if not st:
            raise LookupError(f"data/streets/1835.json carries no street `{sid}`, which "
                              f"{TREES_JS} names as the {side} division's east limit")
        pts = st["path_local_enu_m"]
        out[side] = {
            "street": sid,
            "name_1835": st.get("name_1835", sid),
            # The same mean the renderer takes, and taken here for the same
            # reason it is taken there: a centreline is two or more points and
            # is not exactly north-south.
            "east_m": round(sum(p[0] for p in pts) / len(pts), 1),
        }
    return out


def herbaceous_is_camera_centred(src: str) -> bool:
    """`flora.js` builds its lattice around the camera, not around the origin.

    Scanned, because this is the other half of the asymmetry and an asymmetry one
    side of which is assumed is half a measurement.
    """
    return bool(re.search(r"Math\.floor\(\(camE - radius\) / cell\)", src)
                and re.search(r"Math\.ceil\(\(camE \+ radius\) / cell\)", src))


def declarations() -> dict:
    trees = renderer_source(TREES_JS)
    flora = renderer_source(FLORA_JS)
    sites, named = direct_call_sites(trees)
    placed = placed_species()
    if not herbaceous_is_camera_centred(flora):
        raise LookupError(f"{FLORA_JS} no longer builds its lattice around the camera — "
                          f"this gate's claim that the sward follows the visitor and the "
                          f"timber does not is read off that lattice")
    mixes = community_mixes(trees)
    record_density_rule(trees)
    archetypes, fallback_id = archetype_fallback(trees)
    selectable = {sp for c in mixes.values() for lst in c.values() for sp in lst}
    return {
        "source": trees,
        "weights": mix_weights(trees),
        "archetypes": archetypes,
        "zone_archetypes": zone_archetypes(trees),
        "specs_from": community_specs_from(trees),
        "archetype_fallback": fallback_id,
        "zones": k44.js_array(trees, "TIMBER_ZONES", TREES_JS),
        "forms": k44.js_object_keys(trees, "FORM_OF", TREES_JS),
        "roles": k44.js_role_guard(trees, TREES_JS),
        "communities": mixes,
        "zone_order": timber_zone_order(trees),
        "call_sites": sites,
        "named_at_call_sites": named,
        "placed": placed,
        # A placed stem is a selection like any other — by a record rather than
        # by a mix, and just as drawn.
        "selectable": selectable | named | set(placed),
        "planter": planter_bounds(trees, heightfield()),
        "east_limits": east_limits(trees),
    }


# ---------------------------------------------------------------------------
# the ground, read for what the planter can visit
# ---------------------------------------------------------------------------

def heightfield() -> dict:
    meta = json.loads((TERRAIN / EPOCH / "heightfield.json").read_text(encoding="utf-8"))
    raw = (TERRAIN / EPOCH / "heightfield.bin").read_bytes()
    n = meta["cols"] * meta["rows"]
    if meta.get("encoding") != "int16" or len(raw) != n * 2:
        raise LookupError("the heightfield is no longer the int16 grid this gate reads")
    meta["_samples"] = struct.unpack(f"<{n}h", raw)
    return meta


def land_census(hf: dict, sweep_e: list, sweep_n: list, dry_margin: float,
                limits: dict) -> dict:
    """How many heightfield nodes stand above the planter's own dry floor, and
    how they split across the boundary of the domain it sweeps.

    `east_of_limit` is the second half, added by ROADMAP K45(b2): the planter now
    reaches nearly the whole field, so "can the loop visit this node" stopped
    being the interesting question and "may anything grow on it" started. The
    fraction beyond the further of the two documented east limits is ground the
    loop visits and refuses, which is a different and honest number — the dune
    community that belongs there is K45(b) change one and is not built.
    """
    cols, rows, cell = hf["cols"], hf["rows"], hf["cell_m"]
    e0, n0 = hf["origin_e"], hf["origin_n"]
    scale, off = hf["scale"], hf["offset"]
    floor = hf.get("water_surface_m", 0.0) + dry_margin
    s = hf["_samples"]
    east_cut = max(v["east_m"] for v in limits.values())
    inside = outside = beyond = 0
    for r in range(rows):
        n = n0 + r * cell
        in_n = sweep_n[0] <= n <= sweep_n[1]
        for c in range(cols):
            if s[r * cols + c] * scale + off < floor:
                continue
            e = e0 + c * cell
            if in_n and sweep_e[0] <= e <= sweep_e[1]:
                inside += 1
                if e > east_cut:
                    beyond += 1
            else:
                outside += 1
    total = inside + outside
    ha = cell * cell / 10000.0
    return {
        "dry_floor_m": round(floor, 3),
        "nodes_above_floor": total,
        "inside_planter": inside,
        "outside_planter": outside,
        "inside_pct": round(100.0 * inside / total, 2) if total else 0.0,
        "outside_ha": round(outside * ha, 1),
        "field_e_m": [e0, e0 + (cols - 1) * cell],
        "field_n_m": [n0, n0 + (rows - 1) * cell],
        "east_limit_m": east_cut,
        "reached_east_of_limit": beyond,
        "reached_east_of_limit_ha": round(beyond * ha, 1),
    }


# ---------------------------------------------------------------------------
# the data, asked whether it can be selected
# ---------------------------------------------------------------------------

def boxes_overlap(box: dict, sweep_e: list, sweep_n: list) -> bool:
    be = box.get("e")
    bn = box.get("n")
    if be and (be[1] < sweep_e[0] or be[0] > sweep_e[1]):
        return False
    if bn and (bn[1] < sweep_n[0] or bn[0] > sweep_n[1]):
        return False
    return True


def recorded_bands(dec: dict, zones_read, records: dict[str, dict]) -> dict[str, dict]:
    """`loadTimberZones`'s `bands` table, re-derived here rather than assumed.

    Same two guards, in the same order and for the same reason the renderer has
    them: a role it does not take is skipped, and a form it cannot draw is
    skipped BEFORE the band is written. Kept PER ZONE, because that is the whole
    of ROADMAP K46 — a species named by two zones has two bands, and collapsing
    them to the first is what silently overwrote seventeen mix entries.
    """
    bands: dict[str, dict] = {}
    for zid in sorted(zones_read):
        out: dict[str, list] = {}
        for sp in records[zid].get("species", []):
            if sp.get("role") not in dec["roles"]:
                continue
            if sp.get("form") not in dec["forms"]:
                continue
            band = (sp.get("abundance") or {}).get("density_per_ha")
            if isinstance(band, list) and len(band) == 2:
                out[sp["id"]] = [band[0], band[1]]
        bands[zid] = out
    return bands


def weight_census(dec: dict, bands: dict[str, dict]) -> dict[str, dict]:
    """Every mix entry's weight against the bands its own community cites.

    Four verdicts, and only two of them are allowed to stand. `inside-its-band`
    is the ordinary case. `declared-departure` is a weight outside every cited
    band that the community writes down and explains. `undeclared-departure` and
    `no-band-in-its-zones` are faults the renderer also raises on at load — they
    are reported here so a run that never opens a browser still sees them.
    """
    out: dict[str, dict] = {}
    for key, comm in sorted(dec["weights"].items()):
        declared = set(comm["departures"])
        for name, entries in sorted(comm["lists"].items()):
            for sp, weight in entries:
                seen = {z: bands.get(z, {})[sp]
                        for z in comm["zones"] if sp in bands.get(z, {})}
                is_declared = f"{name}.{sp}" in declared
                if not seen:
                    verdict = "no-band-in-its-zones"
                elif any(lo <= weight <= hi for lo, hi in seen.values()):
                    verdict = ("stale-departure" if is_declared else "inside-its-band")
                elif is_declared:
                    verdict = "declared-departure"
                else:
                    verdict = "undeclared-departure"
                out[f"{key}.{name}.{sp}"] = {
                    "weight": weight,
                    "cited_bands": {z: b for z, b in sorted(seen.items())},
                    "verdict": verdict,
                    "dossier_zones": comm["dossier_zones"],
                }
    return out


def measure(dec: dict | None = None, timber_zones: set[str] | None = None) -> tuple[dict, list[str]]:
    dec = dec or declarations()
    zones_read = timber_zones if timber_zones is not None else dec["zones"]
    manifest = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    hf = heightfield()
    sweep_e = dec["planter"]["sweep_e_m"]
    sweep_n = dec["planter"]["sweep_n_m"]

    contributed: dict[str, list[str]] = {}
    unimplemented: dict[str, list[str]] = {}
    zone_boxes: dict[str, dict] = {}
    zone_records: dict[str, dict] = {}
    for entry in manifest.get("zones", []):
        zid = entry["id"]
        rec = json.loads((DATA / entry["file"]).read_text(encoding="utf-8"))
        zone_records[zid] = rec
        if zid in zones_read:
            box = (rec.get("extent") or {}).get("box")
            if box:
                verdict = ("meets-the-planter" if boxes_overlap(box, sweep_e, sweep_n)
                           else "outside-the-planter")
            else:
                verdict = "no-box"
            zone_boxes[zid] = {"verdict": verdict,
                               "box": {"e": box.get("e"), "n": box.get("n")} if box else None}
        for sp in rec.get("species", []):
            if sp.get("role") not in dec["roles"]:
                continue
            if zid not in zones_read:
                continue
            target = contributed if sp.get("form") in dec["forms"] else unimplemented
            target.setdefault(sp["id"], []).append(zid)

    unselectable = {
        sp: {"zones": sorted(set(zs)), "reason": "in-no-community-mix"}
        for sp, zs in sorted(contributed.items())
        if sp not in dec["selectable"]
    }
    weights = weight_census(dec, recorded_bands(dec, zones_read, zone_records))
    # A species that can be selected but has no archetype of its own is drawn as
    # another species. It is the sycamore today, and it is the shape of thing
    # this file exists to refuse to leave implicit: assertion 3 counts a placed
    # record as reached, and "reached" here means drawn with the American elm's
    # bole, taper, puff count and bark (docs/LIBERTIES.md L116).
    #
    # A species is archetyped for a community either by `SPECIES` or by the zone
    # that community plants from (ROADMAP K45(b) change one): the dune's poplars
    # have no `SPECIES` entry and are not drawn from the elm, because `dune`
    # declares `specsFrom: 'z08_lakeshore'` and that zone declares all three. A
    # species selectable by ANY community that would fall back is reported.
    # It is asked PER COMMUNITY, because `specsFrom` is a per-community
    # declaration: a species covered on the dune and selected by a community
    # that plants from the shared table is still drawn from the fallback there.
    falls_back = set()
    for key, lists in dec["communities"].items():
        zone = dec["specs_from"].get(key)
        own = dec["zone_archetypes"].get(zone, set()) if zone else set()
        for lst in lists.values():
            falls_back |= {sp for sp in lst
                           if sp not in dec["archetypes"] and sp not in own}
    falls_back |= {sp for sp in dec["named_at_call_sites"] if sp not in dec["archetypes"]}
    # And the placed stems, asked against the zone their own record names, which
    # is the table the planting pass reads them out of.
    for sp, zones in dec["placed"].items():
        own: set[str] = set()
        for z in zones:
            own |= dec["zone_archetypes"].get(z, set())
        if sp not in dec["archetypes"] and sp not in own:
            falls_back.add(sp)
    drawn_as = {
        sp: dec["archetype_fallback"]
        for sp in sorted(falls_back)
        if sp in contributed
    }

    state = {
        "planter": {
            **{k: v for k, v in dec["planter"].items() if k != "steps_m"},
            "steps_m": dec["planter"]["steps_m"],
            "call_sites": dec["call_sites"],
        },
        "east_limits": dec["east_limits"],
        "ground": land_census(hf, sweep_e, sweep_n, dec["planter"]["dry_margin_m"],
                              dec["east_limits"]),
        "zones_read": sorted(zones_read),
        "zone_boxes": zone_boxes,
        "communities": {k: sorted({sp for lst in v.values() for sp in lst})
                        for k, v in sorted(dec["communities"].items())},
        "contributed": {k: sorted(set(v)) for k, v in sorted(contributed.items())},
        "unimplemented_form": {k: sorted(set(v)) for k, v in sorted(unimplemented.items())},
        "unselectable": unselectable,
        # What the records place themselves, banked so a stem added to a yard is
        # a diff somebody reads rather than a silent arrival in the town.
        "placed": dec["placed"],
        "drawn_as_another_species": drawn_as,
        "weights": weights,
    }
    problems: list[str] = []
    for entry, w in weights.items():
        if w["weight"] <= 0:
            problems.append(f"the mix entry {entry} is weighted {w['weight']} — `pick()` "
                            f"walks a cumulative sum and can never return a zero-weighted "
                            f"id, so it is in a mix and selectable by nothing, which is "
                            f"the fault assertion 3 exists to catch wearing a disguise")
        if w["verdict"] == "undeclared-departure":
            bands = ", ".join(f"{z} {b[0]}–{b[1]}" for z, b in w["cited_bands"].items())
            problems.append(f"the mix entry {entry} is weighted {w['weight']}, outside "
                            f"every band its own community's zones record ({bands}). "
                            f"Since ROADMAP K46 that number plants the stem, so it is an "
                            f"ecological claim no source carries — declare it in the "
                            f"community's `departures` with the reason, or move it inside "
                            f"the band")
        if w["verdict"] == "stale-departure":
            problems.append(f"the mix entry {entry} declares a departure and its weight "
                            f"{w['weight']} is inside a band its own zones record — drop "
                            f"the declaration in the commit that brought it back inside, "
                            f"or the note claims a disagreement that no longer exists")
        if w["verdict"] == "no-band-in-its-zones":
            comm = entry.rsplit(".", 2)[0]
            zones = ", ".join(dec["weights"][comm]["zones"])
            problems.append(f"the mix entry {entry} is weighted {w['weight']} and no zone "
                            f"this community cites ({zones}) records a density for it — "
                            f"the weight is constrained by nothing at all")
    if not state["contributed"]:
        problems.append("no woody record is routed to the timber reader at all — the "
                        "scan found nothing, which is a broken gate rather than a town "
                        "without trees")
    return state, problems


# ---------------------------------------------------------------------------
# the assertions
# ---------------------------------------------------------------------------

def evaluate(state: dict, bank: dict) -> list[str]:
    out: list[str] = []

    # 1 — the declarations are still there. The scanners raise on absence, so
    # what is left to assert here is the call-site count: a path this file cannot
    # see would call a drawn species unselectable.
    if state["planter"]["call_sites"] != bank["planter"]["call_sites"]:
        out.append(f"trees.js has {state['planter']['call_sites']} addTree call site(s), "
                   f"and this gate accounts for {bank['planter']['call_sites']}. A new "
                   f"selection path has to be read into `direct_call_sites` before the "
                   f"unselectable bank below means anything")

    # 2 — the planter's domain. It may GROW: that is what a repair looks like.
    b, s = bank["planter"], state["planter"]
    # A bank written before ROADMAP K45(b2) describes a square and this state
    # describes a domain. Say so rather than raising a KeyError three frames in:
    # the fix is `--update` in the commit that changed the loop, and a gate whose
    # failure mode is a stack trace teaches nobody which commit owes what.
    missing = [k for k in ("sweep_e_m", "sweep_n_m") if k not in b]
    if missing or "east_limits" not in bank:
        out.append("the baseline predates ROADMAP K45(b2): it banks a fixed square "
                   "(`half_m`) and no east limits, and the planter now sweeps the modelled "
                   "field with a documented limit per division. Re-bank with --update in "
                   "the commit that widened it")
        return out
    if s["dry_margin_m"] != b["dry_margin_m"]:
        out.append(f"the woody planter's dry_margin_m moved: {b['dry_margin_m']} -> "
                   f"{s['dry_margin_m']} — the ground census below is counted against it")
    for key in ("sweep_e_m", "sweep_n_m"):
        if s[key] != b[key]:
            span_b = b[key][1] - b[key][0]
            span_s = s[key][1] - s[key][0]
            direction = "widened" if span_s > span_b else "narrowed"
            note = (" — re-bank it with --update in the commit that widened it"
                    if span_s > span_b else " — the swept domain may grow and may not shrink")
            out.append(f"the woody planter's {key} {direction}: {b[key]} -> {s[key]}{note}")
    # The east limits are the other half of the domain since ROADMAP K45(b2): the
    # loop reaches the field and `communityAt` decides what may stand on it. A
    # limit that MOVES is a claim about a source, so it is banked exactly rather
    # than allowed to grow — a wood that reaches further east is not a repair
    # unless the record that ends it moved too.
    if state["east_limits"] != bank["east_limits"]:
        out.append(f"the timber's east limits moved: {bank['east_limits']} -> "
                   f"{state['east_limits']}. Andreas ends the South Division belt at Wells "
                   f"Street and excepts the sandy hills near the lake from the North "
                   f"Division's timber — moving either is an argument about a source and "
                   f"belongs in a parcel, not in a re-bank")
    bg, sg = bank["ground"], state["ground"]
    if sg["field_e_m"] != bg["field_e_m"] or sg["field_n_m"] != bg["field_n_m"]:
        out.append(f"the modelled field moved: E {bg['field_e_m']} N {bg['field_n_m']} -> "
                   f"E {sg['field_e_m']} N {sg['field_n_m']} — the reach fraction below is "
                   f"a fraction OF this field and has to be re-banked with it")
    if sg["inside_planter"] < bg["inside_planter"]:
        out.append(f"the woody planter reaches less ground than it did: "
                   f"{bg['inside_planter']} -> {sg['inside_planter']} node(s) above its "
                   f"own dry floor. The reach may grow and may not shrink")
    elif sg["inside_planter"] > bg["inside_planter"]:
        out.append(f"the woody planter reaches MORE ground than it did: "
                   f"{bg['inside_planter']} -> {sg['inside_planter']} node(s). That is a "
                   f"repair — re-bank it with --update in the same commit, so the "
                   f"lakeshore question is answered by a number rather than by a claim")

    # 3 — the species no mix can select, exact in both directions.
    sb, bb = state["unselectable"], bank["unselectable"]
    for sp in sorted(set(sb) - set(bb)):
        out.append(f"{sp} is routed to the timber reader by "
                   f"{', '.join(sb[sp]['zones'])}, its form has an archetype, and no "
                   f"community mix or addTree call site can select it — so it is "
                   f"committed, cited and drawn nowhere. Give it a mix entry, or bank "
                   f"it here with --update and say why in docs/LIBERTIES.md")
    for sp in sorted(set(bb) - set(sb)):
        out.append(f"{sp} is banked as selectable by nothing and no longer is — un-bank "
                   f"it with --update in the commit that placed it, so a repair is "
                   f"recorded rather than absorbed")
    for sp in sorted(set(sb) & set(bb)):
        if sb[sp]["zones"] != bb[sp]["zones"] or sb[sp]["reason"] != bb[sp]["reason"]:
            out.append(f"{sp}'s unselectable entry moved: {bb[sp]} -> {sb[sp]}")

    # 4 — the zones routed to the timber reader, and where their ground is.
    sz, bz = state["zone_boxes"], bank["zone_boxes"]
    for zid in sorted(set(sz) - set(bz)):
        out.append(f"{zid} is newly routed to the timber reader and its extent "
                   f"{BOX_VERDICTS[sz[zid]['verdict']]}. Routing is not placement: bank "
                   f"it with --update and read ROADMAP K45(a) before calling it drawn")
    for zid in sorted(set(bz) - set(sz)):
        out.append(f"{zid} is banked as a timber zone and is no longer routed to "
                   f"trees.js — re-bank with --update")
    for zid in sorted(set(sz) & set(bz)):
        if sz[zid]["verdict"] != bz[zid]["verdict"]:
            out.append(f"{zid}'s extent moved relative to the planter: "
                       f"{bz[zid]['verdict']} -> {sz[zid]['verdict']}")

    # 3b — placed, and drawn as something else. Exact both ways, for assertion
    # 3's own reason: a species with no archetype is not "drawn nowhere", it is
    # drawn wearing another species' bark, which is a claim about the town.
    sd, bd = state["drawn_as_another_species"], bank.get("drawn_as_another_species", {})
    for sp in sorted(set(sd) - set(bd)):
        out.append(f"{sp} can be selected and has no `SPECIES` archetype of its own, so it "
                   f"is drawn with {sd[sp]}'s bole, taper, puff count and bark. Give it an "
                   f"entry, or bank it with --update and record the substitution in "
                   f"docs/LIBERTIES.md")
    for sp in sorted(set(bd) - set(sd)):
        out.append(f"{sp} is banked as drawn with another species' archetype and no longer "
                   f"is — un-bank it with --update in the commit that gave it its own")
    for sp in sorted(set(sd) & set(bd)):
        if sd[sp] != bd[sp]:
            out.append(f"{sp} is now drawn as {sd[sp]} where it was drawn as {bd[sp]}")

    # 3c — the stems the records place themselves (T-0091). Exact both ways, for
    # the same reason as 3b: a placed stem is a tree a visitor can walk up to,
    # and one arriving, leaving or changing species without a line in a diff is
    # the town changing by accident.
    sp_, bp_ = state.get("placed", {}), bank.get("placed", {})
    for sp in sorted(set(sp_) - set(bp_)):
        out.append(f"{sp} is newly placed by a planting record, drawn from "
                   f"{', '.join(sp_[sp]) or 'no zone'} — bank it with --update in the "
                   f"commit that placed it, and claim the stems in docs/LIBERTIES.md")
    for sp in sorted(set(bp_) - set(sp_)):
        out.append(f"{sp} is banked as placed by a planting record and no longer is — "
                   f"un-bank it with --update in the commit that removed the stems")
    for sp in sorted(set(sp_) & set(bp_)):
        if sp_[sp] != bp_[sp]:
            out.append(f"{sp}'s placed stems now draw their ecology from "
                       f"{sp_[sp]} where they drew it from {bp_[sp]}")

    # 5 — the weight that plants the stem, against the bands its own community
    # cites, exact both ways. Since ROADMAP K46 the written number IS the number,
    # so what the bank protects is no longer a divergence between two figures but
    # the standing of each one: a weight that moves, a band that moves under it,
    # or a departure that appears or is quietly repaired away.
    if "weights" not in bank:
        out.append("the baseline predates assertion 5 and holds no mix weights at all — "
                   "run --update once to bank every entry's weight and its band verdict")
        return out
    sw, bw = state["weights"], bank["weights"]
    if any("weight" not in v for v in bw.values()):
        out.append("the baseline predates ROADMAP K46: it banks each entry's literal "
                   "against the global midpoint that used to override it, and this gate "
                   "now banks the weight that plants the stem against the bands its own "
                   "community cites. Re-bank with --update in the commit that changed "
                   "the rule")
        return out
    for e in sorted(set(sw) - set(bw)):
        w = sw[e]
        bands = (", ".join(f"{z} {b[0]}–{b[1]}" for z, b in w["cited_bands"].items())
                 or "no band in its community's zones")
        out.append(f"{e} is a mix entry this gate has never banked: weighted "
                   f"{w['weight']}, {VERDICTS[w['verdict']]} ({bands}). Re-bank with "
                   f"--update in the commit that added it")
    for e in sorted(set(bw) - set(sw)):
        out.append(f"{e} is banked as a mix entry and is no longer one — un-bank it with "
                   f"--update in the commit that removed it, so a species leaving the "
                   f"scene is recorded rather than absorbed")
    for e in sorted(set(sw) & set(bw)):
        s, b = sw[e], bw[e]
        if s["weight"] != b["weight"]:
            out.append(f"{e}'s weight moved: {b['weight']} -> {s['weight']}. That is a "
                       f"stem count in the frame — re-bank with --update and say in the "
                       f"commit what evidence moved it")
            continue
        if s["verdict"] != b["verdict"]:
            out.append(f"{e} was {VERDICTS[b['verdict']]} and is now "
                       f"{VERDICTS[s['verdict']]} — re-bank with --update, and if it has "
                       f"become a departure say in docs/LIBERTIES.md what the claim is")
            continue
        for field in ("cited_bands", "dossier_zones"):
            if s[field] != b[field]:
                out.append(f"{e}'s {field} moved: {b[field]} -> {s[field]}. The record is "
                           f"the constraint on this weight, so a band that moves under it "
                           f"is re-banked in the commit that moved the record")
                break
    return out


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------

def print_census(state: dict) -> None:
    p, g = state["planter"], state["ground"]
    print("WHERE THE WOODY PLANTER CAN PUT A STEM")
    print(f"  the swept domain   E {p['sweep_e_m'][0]:.1f}..{p['sweep_e_m'][1]:.1f}  "
          f"N {p['sweep_n_m'][0]:.1f}..{p['sweep_n_m'][1]:.1f} m "
          f"({p['kind']}, steps {'/'.join(f'{s:g}' for s in p['steps_m'])})")
    for side, v in sorted(state["east_limits"].items()):
        print(f"  {side:<5} division timber ends at {v['name_1835']}, E +{v['east_m']:.1f} m")
    print(f"  the modelled field E {g['field_e_m'][0]:.0f}..{g['field_e_m'][1]:.0f}  "
          f"N {g['field_n_m'][0]:.0f}..{g['field_n_m'][1]:.0f} m")
    print(f"  ground above the planter's own dry floor ({g['dry_floor_m']:.2f} m): "
          f"{g['nodes_above_floor']} node(s)")
    print(f"    inside the sweep    {g['inside_planter']:>7} ({g['inside_pct']:.2f} %)")
    print(f"      of which east of the limits {g['reached_east_of_limit']:>7} "
          f"({g['reached_east_of_limit_ha']:.1f} ha swept and refused — the dune "
          f"community that belongs there is ROADMAP K45(b) change one)")
    print(f"    outside it          {g['outside_planter']:>7} "
          f"({100 - g['inside_pct']:.2f} %, {g['outside_ha']:.1f} ha the timber layer "
          f"never visits)")
    print(f"  flora.js's lattice is centred on the camera and has no such bound.")

    print("\nTHE TIMBER READER'S ZONES, AND WHERE THEIR GROUND IS")
    for zid, z in sorted(state["zone_boxes"].items()):
        box = z["box"]
        where = (f"box E {box['e']} N {box['n']}" if box else "no box")
        print(f"  {zid:<24} {z['verdict']:<20} {where}")
    print("  (a zone's extent is read by flora.js and never by trees.js: the timber "
          "reader\n   takes species parameters out of these files and places from "
          "COMMUNITIES)")

    print("\nWHAT EACH COMMUNITY CAN SELECT")
    for key, ids in state["communities"].items():
        print(f"  {key:<14} {len(ids):>2}  {', '.join(ids)}")

    w = state["weights"]
    departing = [e for e, v in w.items() if v["verdict"] != "inside-its-band"]
    print(f"\nTHE WEIGHT THAT PLANTS EACH STEM, AGAINST THE BAND ITS COMMUNITY CITES — "
          f"{len(w) - len(departing)} of {len(w)} inside")
    print(f"  {'entry':<48}{'weight':>7}  {'cited band(s)':<34}verdict")
    for e, v in w.items():
        bands = " ".join(f"{z.split('_')[0]}[{b[0]:g}, {b[1]:g}]"
                         for z, b in v["cited_bands"].items()) or "—"
        short = v["verdict"] if v["verdict"] != "inside-its-band" else ""
        print(f"  {e:<48}{v['weight']:>7.1f}  {bands:<34}{short}")
    print("  (the weight written in COMMUNITIES is the weight `pick()` walks, and the "
          "record's band\n   is the CONSTRAINT on it. A weight outside every band its "
          "community's `zones` name\n   is declared in that community's `departures` with "
          "its reason, or the load raises.)")

    print(f"\nROUTED, ARCHETYPED, AND SELECTED BY NOTHING — "
          f"{len(state['unselectable'])} of {len(state['contributed'])}")
    for sp, e in state["unselectable"].items():
        print(f"  {sp:<28} {UNSELECTABLE_REASONS[e['reason']]}")
        print(f"  {'':<28} routed by {', '.join(e['zones'])}")
    if state["drawn_as_another_species"]:
        print("\nPLACED, AND DRAWN AS ANOTHER SPECIES")
        for sp, as_id in state["drawn_as_another_species"].items():
            print(f"  {sp:<28} no `SPECIES` archetype: drawn with {as_id}'s bole, taper, "
                  f"puffs and bark")

    if state["unimplemented_form"]:
        print(f"\n  (and {len(state['unimplemented_form'])} woody record(s) whose form has "
              f"no archetype at all,\n   which is K44's bank rather than this one: "
              f"{', '.join(state['unimplemented_form'])})")


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------

def self_test() -> int:
    state, _ = measure()
    bank = json.loads(BASELINE.read_text(encoding="utf-8"))
    clean = evaluate(state, bank)
    print("SELF-TEST — each case must FIRE")
    if clean:
        print("  note: the clean tree already reports:")
        for c in clean:
            print(f"    {c}")

    cases: list[tuple[str, dict, dict]] = []

    s1 = copy.deepcopy(state)
    s1["planter"]["call_sites"] += 1
    cases.append(("1 a third addTree call site this gate cannot read", s1, bank))

    s2 = copy.deepcopy(state)
    s2["planter"]["sweep_e_m"] = [-316.0, 316.0]
    cases.append(("2 the swept domain narrowed back to the old square", s2, bank))

    s2e = copy.deepcopy(state)
    s2e["east_limits"]["south"]["east_m"] = 1700.0
    cases.append(("2 the timber's east limit carried to the lake", s2e, bank))

    s2b = copy.deepcopy(state)
    s2b["ground"]["inside_planter"] -= 1
    cases.append(("2 the planter reaching less ground than it did", s2b, bank))

    s2c = copy.deepcopy(state)
    s2c["ground"]["field_e_m"] = [-320.0, 2400.0]
    cases.append(("2 the field extended east under a fixed planter", s2c, bank))

    s3 = copy.deepcopy(state)
    s3["unselectable"]["quercus_alba"] = {"zones": ["z07_bur_oak_savanna"],
                                          "reason": "in-no-community-mix"}
    cases.append(("3 a species newly selectable by nothing", s3, bank))

    b3 = copy.deepcopy(bank)
    b3["unselectable"]["a_species_that_left"] = {"zones": ["z05_riverbank_timber"],
                                                 "reason": "in-no-community-mix"}
    cases.append(("3 a banked unselectable species that has been placed", state, b3))

    if state["unselectable"]:
        b3z = copy.deepcopy(bank)
        first = sorted(state["unselectable"])[0]
        b3z["unselectable"][first] = {**b3z["unselectable"][first],
                                      "zones": ["z10_settled_town"]}
        cases.append(("3 a banked species whose routing moved", state, b3z))

    s3d = copy.deepcopy(state)
    s3d["drawn_as_another_species"]["quercus_alba"] = "ulmus_americana"
    cases.append(("3b a placed species newly drawn with another's archetype", s3d, bank))

    # ROADMAP K47 turned this case round, and the reason is the one K45(b1)
    # already wrote about assertion 3's own negative control: until the sycamore
    # got its archetype, `state` carried the substitution and the case emptied
    # the BANK. It is banked empty now, so emptying it again compares nothing
    # with nothing and the case goes silent — a control that stops controlling
    # the day the thing it watched was repaired. Synthesised on the bank side
    # instead, which is the direction that still has something to say: a
    # substitution recorded in the baseline and no longer in the tree must fire,
    # because that is the un-bank this parcel had to perform.
    b3d = copy.deepcopy(bank)
    b3d["drawn_as_another_species"] = {"platanus_occidentalis": "ulmus_americana"}
    cases.append(("3b a banked substitution that has been given its own archetype",
                  state, b3d))

    s4 = copy.deepcopy(state)
    s4["zone_boxes"]["z09_sand_prairie"] = {"verdict": "outside-the-planter",
                                            "box": {"e": [840, 1400], "n": [-400, 400]}}
    cases.append(("4 a zone newly routed to the timber reader", s4, bank))

    s4b = copy.deepcopy(state)
    s4b["zone_boxes"]["z07_bur_oak_savanna"]["verdict"] = "meets-the-planter"
    cases.append(("4 a banked zone whose extent moved onto the planter", s4b, bank))

    s5 = copy.deepcopy(state)
    first_entry = sorted(state["weights"])[0]
    s5["weights"][first_entry]["weight"] += 3
    cases.append(("5 a mix entry's weight edited and not re-banked — which is a stem "
                  "count in the frame", s5, bank))

    s5b = copy.deepcopy(state)
    s5b["weights"]["gallery.mix.a_species_added_to_the_mix"] = {
        "weight": 1.0, "cited_bands": {"z05_riverbank_timber": [1, 3]},
        "verdict": "inside-its-band", "dossier_zones": ["5"]}
    cases.append(("5 a species added to a mix and not banked", s5b, bank))

    b5 = copy.deepcopy(bank)
    b5["weights"]["gallery.mix.a_species_that_left"] = {
        "weight": 4.0, "cited_bands": {"z05_riverbank_timber": [1, 8]},
        "verdict": "inside-its-band", "dossier_zones": ["5"]}
    cases.append(("5 a banked mix entry that has been removed", state, b5))

    # The record moving under a weight that did not move is the case K46's rule
    # created: the band is the constraint now, so an edited record can turn a
    # standing weight into a claim no source carries without a line of the
    # renderer changing.
    b5r = copy.deepcopy(bank)
    b5r["weights"][first_entry] = {**b5r["weights"][first_entry],
                                   "cited_bands": {"z05_riverbank_timber": [90, 99]}}
    cases.append(("5 a record's band edited under an unchanged weight", state, b5r))

    b5v = copy.deepcopy(bank)
    b5v["weights"]["gallery.mix.salix_amygdaloides"] = {
        **b5v["weights"]["gallery.mix.salix_amygdaloides"], "verdict": "inside-its-band"}
    cases.append(("5 a declared departure that used to sit inside its band", state, b5v))

    # K45(a)'s move applied to K45(b)'s own prescription, and K46 CHANGED WHAT IT
    # CATCHES — recorded here rather than deleted, because a self-test case whose
    # meaning has moved is worth more read than dropped. ROADMAP K45(b) and
    # docs/LIBERTIES.md L114 prescribe `['platanus_occidentalis', 1]`. Under the
    # old rule that 1 was a dead number: the 2 from `records.density` overrode it
    # and nothing used it. Under K46's rule the 1 is admissible — z05 bands the
    # sycamore at [1, 3] and 1 is its floor — and it is no longer a defect but a
    # decision, halving the sycamores that stand. So what fires now is the weight
    # having moved without being re-banked, which is the assertion K46 wants: the
    # gate stopped being about a disagreement between two figures and became
    # about a stem count in the frame.
    s5c = copy.deepcopy(state)
    syc = s5c["weights"].get("gallery.mix.platanus_occidentalis")
    if syc:
        s5c["weights"]["gallery.mix.platanus_occidentalis"] = {**syc, "weight": 1.0}
        cases.append(("5 K45(b)'s prescribed ['platanus_occidentalis', 1] — admissible "
                      "under K46's rule, and half the sycamores", s5c, bank))

    # THE CASE THIS PARCEL EXISTED FOR, IN THE DIRECTION THAT SURVIVES IT.
    # docs/LIBERTIES.md L113 and ROADMAP K45 said the lakeshore's dune records
    # were repaired by adding the zone to `TIMBER_ZONES`; K45(a) fired this case
    # in the other direction and measured that the repair drew nothing, because
    # routing is not placement and no community mix held a poplar. K45(b) change
    # one built the mix, so the zone is routed AND placed and the old case can no
    # longer fire — it would now be the tree as it stands.
    #
    # What replaces it is the same assertion read backwards, and it is the one
    # worth keeping: take the dune's mix away and the poplars must fall back into
    # the unselectable bank. That is L113's finding preserved as a live test
    # rather than as a paragraph about a repair that has since landed.
    dec = declarations()
    s_nodune = copy.deepcopy(state)
    for sp in ("populus_tremuloides", "populus_balsamifera"):
        s_nodune["unselectable"][sp] = {"zones": ["z08_lakeshore"],
                                        "reason": "in-no-community-mix"}
    cases.append(("K45(a) L113 backwards — the dune mix removed puts the poplars back "
                  "in the unselectable bank", s_nodune, bank))

    ok = True
    for label, s, b in cases:
        fired = len(evaluate(s, b)) > len(clean)
        print(f"  {'fires' if fired else 'SILENT'}  {label}")
        ok = ok and fired

    print(f"  …and the bank it was written about is now empty: "
          f"{len(state['unselectable'])} routed, archetyped, unselectable species, "
          f"with z08_lakeshore's own extent box "
          f"{BOX_VERDICTS[state['zone_boxes']['z08_lakeshore']['verdict']]} and its "
          f"three poplars planted by `dune`")

    # The scanners are the load-bearing half of assertion 1: each must be able to
    # say yes AND no. A scanner that silently returns nothing would call every
    # species unselectable and bank the lot.
    src = dec["source"]
    checks = [
        ("the community scanner finds the five mixes",
         set(dec["communities"]) == {"gallery", "wet_woods", "mesic_pocket", "ridge_oak",
                                     "dune"}),
        ("…and reads the gallery's edge mix as well as its mix",
         "salix_nigra" in dec["communities"]["gallery"]["edgeMix"]),
        ("…and reads a multi-line mix to its END, not to its second entry",
         {"juglans_nigra", "salix_amygdaloides"}
         <= set(dec["communities"]["gallery"]["mix"])),
        ("the community scanner refuses a renderer with no COMMUNITIES",
         raises(lambda: community_mixes("const NOTHING = 1;"))),
        ("the direct call site scan finds the point-bar thicket",
         "salix_interior" in dec["named_at_call_sites"]),
        ("the call sites are counted, not assumed", dec["call_sites"] >= 2),
        ("the planter's domain is derived from the field, not from a literal",
         dec["planter"]["sweep_e_m"][1] > 1000.0),
        ("the bound scanner refuses a loop that no longer sweeps the field",
         raises(lambda: planter_bounds(src.replace(
             "for (let n = sweepN0; n <= sweepN1; n += step)",
             "for (const n of everywhere)"), heightfield()))),
        ("the bound scanner refuses a renderer with no planting steps",
         raises(lambda: planter_bounds("const sweepE0 = 1;", heightfield()))),
        ("the east limits are read off the street data, not off the renderer",
         dec["east_limits"]["south"]["street"] == "wells"
         and 320.0 < dec["east_limits"]["south"]["east_m"] < 340.0),
        ("…and a communityAt that stopped applying them is refused",
         raises(lambda: east_limits(src.replace(
             "if (e > (d === NORTH ? eastLimit.north : eastLimit.south)) return null;",
             "if (false) return null;")))),
        ("…and a renderer that stopped reading the street records is refused",
         raises(lambda: east_limits(src.replace(
             "timberEastLimits(streetRecords, problems)", "timberEastLimits()")))),
        ("flora.js's lattice is read as camera-centred",
         herbaceous_is_camera_centred(renderer_source(FLORA_JS))),
        ("…and a lattice that stopped following the camera is refused",
         not herbaceous_is_camera_centred("const c0 = Math.floor((0 - radius) / cell);")),
        ("a species in a mix is selectable",
         "quercus_macrocarpa" in dec["selectable"]),
        # The mix scanner's negative used to be the sycamore, which K45(b1)
        # placed. A gate whose only proof that a scanner can say no is a species
        # somebody is about to plant stops proving it the day the repair lands,
        # so the negative is synthetic now and cannot be repaired out from under
        # this file.
        ("a species in no mix is not",
         "platanus_occidentalis" not in {
             sp for c in community_mixes(
                 "const COMMUNITIES = {\n  gallery: {\n"
                 "    mix: [['ulmus_americana', 1]],\n  },\n};").values()
             for lst in c.values() for sp in lst}),
        ("the weight scanner reads every mix entry in the file",
         len(weight_census(dec, {})) == sum(
             len(v) for c in dec["weights"].values() for v in c["lists"].values())),
        # Synthetic, so that it cannot be satisfied by whichever species happens
        # to sit last in the real gallery today: the bug this guards against is
        # a non-greedy `\[(.*?)\],` stopping at the first line break, and the
        # only honest control for it is a list that HAS a line break in it.
        ("…and reads a multi-line mix to its last weight, not to its second",
         mix_entries("  x: {\n    mix: [\n      ['a', 1], ['b', 2],\n"
                     "      ['c', 3],\n    ],\n  },\n", "x")["mix"]
         == [("a", 1.0), ("b", 2.0), ("c", 3.0)]),
        ("…and each community's dossier still says which ZONE its weights came from",
         all(c["dossier_zones"] for c in dec["weights"].values())),
        ("…and refuses a community that no longer says",
         raises(lambda: mix_weights(re.sub(r"dossier: '", "dossierWas: '", src)))),
        # The two citations are the same fact written twice — the prose a reader
        # sees and the list the loader constrains against — and holding them
        # equal is what stops a community reading bands out of a zone it does
        # not claim. ZONE 6a/6b/6c all resolve to z06, which is K46's whole
        # finding, so the comparison is on the zone NUMBER.
        ("…and each community's machine-readable `zones` agrees with that prose",
         all(c["zones"] for c in dec["weights"].values())),
        ("…and refuses a community whose zones and dossier disagree",
         raises(lambda: mix_weights(src.replace(
             "zones: ['z05_riverbank_timber'],", "zones: ['z09_sand_prairie'],")))),
        ("…and refuses a community that declares no zones at all",
         raises(lambda: mix_weights(src.replace(
             "zones: ['z06_dense_forest', 'z07_bur_oak_savanna'],", "")))),
        ("the departures scanner reads the three this file declares",
         sorted(d for c in dec["weights"].values() for d in c["departures"])
         == ["edgeMix.acer_saccharinum", "mix.salix_amygdaloides", "mix.ulmus_americana"]),
        ("TIMBER_ZONES is still a list a community's `zones` can name into",
         dec["zone_order"][0] == "z05_riverbank_timber"
         and set(dec["zone_order"]) == dec["zones"]),
        ("the archetype table and its fallback are read off the renderer",
         archetype_fallback(src)[1] in archetype_fallback(src)[0]),
        ("…and a fallback to an archetype that is not in the table is refused",
         raises(lambda: archetype_fallback(
             src.replace("SPECIES[sp.id] ?? SPECIES.ulmus_americana",
                         "SPECIES[sp.id] ?? SPECIES.no_such_tree")))),
        # The per-zone archetypes, both ways. A scanner that read nothing would
        # call the dune's three poplars drawn with the elm's bark — a confident
        # false finding, which is the one failure mode assertion 3 cannot have.
        ("the per-zone archetypes are read off the renderer",
         zone_archetypes(src).get("z08_lakeshore", set())
         >= {"populus_deltoides", "populus_tremuloides", "populus_balsamifera"}),
        ("…and a renderer with no ARCHETYPE_BY_ZONE at all is refused",
         raises(lambda: zone_archetypes(
             src.replace("const ARCHETYPE_BY_ZONE", "const ARCHETYPE_BY_ZONE_RENAMED")))),
        ("…and the community that plants from a zone's own archetypes is read",
         community_specs_from(src).get("dune") == "z08_lakeshore"),
        ("K46's rule is scanned out of the renderer, not assumed",
         record_density_rule(src) is None),
        # The regression this file exists to refuse is the ONE it was built to
        # measure: the loader going back to a global midpoint that overwrites
        # every hand weight. It is fired in memory on every run.
        ("…and a renderer that went back to overriding the literal is refused",
         raises(lambda: record_density_rule(
             src + "\n const w = records.density[id] ?? fallback;\n"))),
        ("…and one that stopped keeping the recorded band per zone is refused",
         raises(lambda: record_density_rule(
             src.replace("bands[id][sp.id] = [perHa[0], perHa[1]];",
                         "bands[sp.id] = perHa;")))),
        ("…and one that stopped testing the weight against that band is refused",
         raises(lambda: record_density_rule(src.replace(
             "seen.some(([lo, hi]) => weight >= lo && weight <= hi)", "true")))),
        ("…and one that stopped reading `departures` is refused",
         raises(lambda: record_density_rule(src.replace(
             "c.departures?.[`${listName}.${id}`]", "null")))),
        # The census's own verdicts, fired against a synthetic band table: a gate
        # that only ever sees the passing case is a gate whose failing branch has
        # never run. All three faults are reachable here and none is reachable
        # from the committed file, which is the point.
        ("the census can say `undeclared-departure`",
         weight_census({"weights": {"c": {"zones": ["z05_riverbank_timber"],
                                          "dossier_zones": ["5"], "departures": [],
                                          "lists": {"mix": [("ulmus_americana", 99.0)]}}}},
                       {"z05_riverbank_timber": {"ulmus_americana": [15, 35]}}
                       )["c.mix.ulmus_americana"]["verdict"] == "undeclared-departure"),
        ("…and `declared-departure` for the same weight once it is written down",
         weight_census({"weights": {"c": {"zones": ["z05_riverbank_timber"],
                                          "dossier_zones": ["5"],
                                          "departures": ["mix.ulmus_americana"],
                                          "lists": {"mix": [("ulmus_americana", 99.0)]}}}},
                       {"z05_riverbank_timber": {"ulmus_americana": [15, 35]}}
                       )["c.mix.ulmus_americana"]["verdict"] == "declared-departure"),
        ("…and `stale-departure` for one declared and no longer outside",
         weight_census({"weights": {"c": {"zones": ["z05_riverbank_timber"],
                                          "dossier_zones": ["5"],
                                          "departures": ["mix.ulmus_americana"],
                                          "lists": {"mix": [("ulmus_americana", 25.0)]}}}},
                       {"z05_riverbank_timber": {"ulmus_americana": [15, 35]}}
                       )["c.mix.ulmus_americana"]["verdict"] == "stale-departure"),
        ("…and `no-band-in-its-zones` when the cited zone records none",
         weight_census({"weights": {"c": {"zones": ["z07_bur_oak_savanna"],
                                          "dossier_zones": ["7"], "departures": [],
                                          "lists": {"mix": [("ulmus_americana", 25.0)]}}}},
                       {"z07_bur_oak_savanna": {}}
                       )["c.mix.ulmus_americana"]["verdict"] == "no-band-in-its-zones"),
        ("…and every committed entry is one of the two verdicts that may stand",
         all(v["verdict"] in ("inside-its-band", "declared-departure")
             for v in state["weights"].values())),
        ("the heightfield is the int16 grid this gate reads",
         heightfield()["cols"] > 0),
    ]
    for label, passed in checks:
        print(f"  {'ok   ' if passed else 'FAIL '}  {label}")
        ok = ok and passed

    print("SELF-TEST PASS" if ok else "SELF-TEST FAIL")
    return 0 if ok else 1


def raises(fn) -> bool:
    try:
        fn()
    except LookupError:
        return True
    return False


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
            "_doc": "Whether a routed woody record can be PLACED. K44 measured which "
                    "reader receives a record; trees.js receives one and then selects a "
                    "species out of a hand-written COMMUNITIES mix, so a record it "
                    "receives whose species is in no mix is drawn nowhere. `planter` and "
                    "`ground` are the domain the timber loop sweeps — since ROADMAP "
                    "K45(b2) the modelled field inset by one planting step, not a fixed "
                    "square inside it — and how much of the field it reaches; it may grow "
                    "and may not shrink. `east_limits` is where the woody layer stops in "
                    "the east and the street each limit is read from: Andreas ends the "
                    "South Division belt at Wells Street and excepts the sandy hills near "
                    "the lake from the North Division's timber. They are banked EXACTLY, "
                    "in both directions — a wood that reaches further east is an argument "
                    "about a source, not a repair. "
                    "`unselectable` is the population, exact in both directions, and "
                    "`drawn_as_another_species` is the placed species that have no archetype of "
                    "their own. `placed` is the species a PLANTING RECORD states a stem of "
                    "(T-0091) and the zone each draws its ecology from — a selection made "
                    "by the dataset rather than by a mix, banked exactly so a tree "
                    "arriving in or leaving a yard is a line in a diff. "
                    "`zone_boxes` records that a TIMBER_ZONE's extent is never consulted "
                    "by the reader it is routed to. `weights` is every mix entry's "
                    "literal beside the weight that replaces it at load — the literal is "
                    "a fallback, and `records.density` (the midpoint of the band in the "
                    "first TIMBER_ZONE naming the species) is what places a stem. Held by "
                    "tools/measure_planting_reach.py. Read ROADMAP K45(a) and K45(b1) "
                    "before adding a line, and K45(b2) before moving an east limit.",
            "planter": state["planter"],
            "east_limits": state["east_limits"],
            "ground": state["ground"],
            "zone_boxes": {k: state["zone_boxes"][k] for k in sorted(state["zone_boxes"])},
            "unselectable": state["unselectable"],
            "placed": state["placed"],
            "drawn_as_another_species": state["drawn_as_another_species"],
            "weights": state["weights"],
        }, indent=2) + "\n", encoding="utf-8")
        departing = sum(1 for v in state["weights"].values()
                        if v["verdict"] != "inside-its-band")
        print(f"wrote {BASELINE.relative_to(ROOT)} "
              f"({len(state['unselectable'])} unselectable species, "
              f"{len(state['zone_boxes'])} timber zone(s), "
              f"{len(state['weights'])} mix entries, {departing} of them outside their "
              f"community's own cited bands)")
        return 0

    if not args.gate and not args.quiet:
        print_census(state)

    bank = json.loads(BASELINE.read_text(encoding="utf-8"))
    problems += evaluate(state, bank)

    for p in problems:
        print(f"FAIL  {p}", file=sys.stderr)
    if problems:
        return 1

    if args.gate or args.quiet:
        g = state["ground"]
        departing = sum(1 for v in state["weights"].values()
                        if v["verdict"] != "inside-its-band")
        print(f"planting reach: the woody planter sweeps the modelled field and reaches "
              f"{g['inside_pct']:.1f} % of the ground above its own dry floor "
              f"({g['outside_ha']:.1f} ha outside it, {g['reached_east_of_limit_ha']:.1f} ha "
              f"swept and refused east of the documented limits); "
              f"{len(state['unselectable'])} routed woody species can be selected by no "
              f"community mix; {departing} of {len(state['weights'])} mix weights sit "
              f"outside every band their own community cites. All three are banked and none "
              f"may worsen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
