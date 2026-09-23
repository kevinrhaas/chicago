#!/usr/bin/env python3
"""Validate the 4D Chicago dataset.

Runs in seconds and needs no Blender. This is the per-commit gate.

    validate.py              schema + referential + semantic + scene date gates
    validate.py --params     also resolve every phase's form to archetype params
    validate.py --licenses   also check asset license coverage and rights gating
    validate.py --stale      also recompute every committed GLB's input hash
    validate.py --site       also check publish sync and the published size budget
    validate.py --all        everything
    validate.py --strict     warnings become errors

The rules enforced here are the project's contract, not style preferences:
documented requires a resolving source, inferred requires stated reasoning, a
structure must have exactly one phase covering a scene's date, and geometry
cannot be generated while the datum origin is unverified.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path

from associations import (ASSOCIATION_KINDS, ASSOCIATION_RESOLUTION,
                         check_association_rows, singular_drift)
from heightfield import Heightfield
from migrate_attribute_tiers import check_tier_block
from tiers import (SOLE_EVIDENCE_MAX_TIER, TESTIMONY_MAX_TIER,
                   TRACEABLE_MAX_TIER, tier_ladder)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# T-0161. `drawn_by` — "this phase builds no mesh" — had four readers and four
# copies of the test, and the one that mattered most (generators/build.py, the
# program the sentence is addressed to) did not have it at all, so every full
# bake rebuilt the retired estray pen and this file then failed it. The rule is
# imported from the generators now so the builder and the validator cannot drift
# apart again; `generators/common/phases.py` imports nothing, so `check.sh` stays
# the sub-second dependency-free gate it is.
sys.path.insert(0, str(ROOT / "generators"))
from common.phases import drawn_by_another_layer  # noqa: E402

# A documented_range spanning more than this earns a warning. Chicago between
# 1833 and 1837 changed faster than almost any settlement in American history;
# a wide range is usually a research gap wearing a disguise.
WIDE_RANGE_YEARS = 12

# Published payload budget. GitHub Pages does not serve Git LFS objects, so the
# published tree holds plain binaries and has to stay reasonable.
#
# 25 -> 28 ON 2026-08-29 (T-0317), AND IT IS A CONSCIOUS RE-BUDGET RATHER THAN A
# WEAKENED ASSERTION. Say which one you are doing, so: this is the first one.
#
# WHERE 25 CAME FROM. docs/PLAN.md set it at the start of the project, when the
# payload was 4.5 MB, as "reasonable" — not as a limit anything imposes. It is not
# a GitHub Pages limit: Pages allows 1 GB a site and 100 MB a file. The LFS clause
# above is the real constraint and it is about FORMAT, not size — the tree must hold
# plain binaries — and 28 MB is as plain as 25 MB. docs/RENDERING.md § the gate table
# has recorded a sanctioned raise to ~100 MB at H2 since the rendering plan was
# written, so the direction was never in question, only the occasion.
#
# WHAT SUPPORTS 28, MEASURED. `dev` publishes at 24.901 MB — 99,573 bytes of
# headroom, which is 0.4 % of the budget. A single platted-block deal of four roofs
# adds 138,399 bytes, so the budget was ALREADY exhausted for every visible parcel in
# the queue before this one: T-0317 is simply the run that hit the wall. 28 MB restores
# 2.85 MB of headroom, which is about twenty more block deals at the rate this one
# measured, and it leaves the payload at a quarter of the sanctioned H2 figure.
#
# WHAT WILL EXHAUST IT AGAIN, WRITTEN DOWN RATHER THAN DISCOVERED LATER. 1,899,254
# bytes of the tree — 7.2 % of it — are TWO byte-identical copies of changelog.js,
# published to `js/` and to `walk/js/` because both paths are contracts (AGENTS.md §
# changelog). That is the fastest-growing item in the payload and it grows on every
# release rather than on every building. Filed as its own ticket; this raise buys the
# time to answer it and does not answer it.
#
# 28 -> 32 ON 2026-08-30 (T-0379), AND IT IS THE SECOND CONSCIOUS RE-BUDGET RATHER
# THAN A WEAKENED ASSERTION. Saying which one, as the note above requires: this is a
# re-budget. Nothing was made cheaper to pass and nothing was moved out of the tree to
# duck the number.
#
# WHAT EXHAUSTED 28, AND IT WAS NOT A BUILDING. The owner was asked how many of the
# names known only from the post office's lists of uncalled-for letters this town
# should hold, was shown that holding all of them makes three quarters of its people a
# name and nothing else — and what a record costs, in as many words, "705 files" — and
# ruled on 2026-08-30 that it should hold all of them. 712 household records joined the
# 15 already standing. That is the largest single addition to the published tree this
# corpus can make, it was decided with the file count in view, and it is not a class of
# growth the last raise's arithmetic (roofs per block deal) was measuring.
#
# WHAT WAS DONE BEFORE RAISING, MEASURED. The 727 records were first cut from 5,503 to
# 3,661 bytes each — 1.34 MB, a third of the cohort — by moving the reasoning IDENTICAL
# on all 727 of them out of 727 files and into the one place it belongs: L214 in
# docs/LIBERTIES.md, the pass's own docstring, and the Evidence panel's group heading,
# which is where a reader meets it anyway. That is a saving worth having whatever the
# budget is, and it was not enough: the tree publishes at 28.48 MiB, 0.48 over. Going
# further would have meant deleting the reasoning rather than de-duplicating it, and a
# record that states its evidence and not what that evidence is worth is the thing this
# project's whole confidence model exists to refuse.
#
# WHAT SUPPORTS 32. The LFS clause above is still the real constraint and it is about
# FORMAT: the tree holds plain binaries at 32 MiB exactly as it did at 25. Pages allows
# 1 GB a site, docs/RENDERING.md § the gate table has recorded a sanctioned raise to
# ~100 MB at H2 since the rendering plan was written, and 32 MiB is under a third of
# that. It restores 3.52 MiB of headroom — more than the 2.85 the last raise bought —
# and the two largest items in the tree are now named and ticketed rather than
# discovered: the letter-list cohort at 2.54 MiB (T-0379, this) and the duplicated
# changelog at 2.07 MiB, 7.3 % of the tree, which is T-0364 and is still unanswered.
#
# 32 -> 36 ON 2026-09-05 (T-0593), AND IT IS THE THIRD CONSCIOUS RE-BUDGET RATHER THAN
# A WEAKENED ASSERTION. Saying which one, as the note above requires: this is a
# re-budget. Nothing was made cheaper to pass, nothing was moved out of the tree to duck
# the number, and no reasoning was deleted to fit under it.
#
# WHAT EXHAUSTED 32, MEASURED ON `dev` AT 06a0a9ec. The published tree stands at
# 33,553,488 bytes against a ceiling of 33,554,432 — 944 BYTES of headroom, which is
# 0.003 % of the budget. That is not a margin; it is a wall that the next merge of any
# kind walks into. A release entry alone costs about 5.4 KB, because the changelog is
# published twice (below, and T-0364), so the budget was already spent for every ticket
# in the queue before this one. T-0593 is simply the run that hit the wall, exactly as
# T-0317 was at 25 and T-0379 at 28.
#
# WHAT THIS UNIT ADDS, AND WHY IT CANNOT BE TRIMMED INTO 944 BYTES. Re-dealing lot 7 of
# block 16 from a D3 cottage to an H1 house publishes 22,285 bytes net: the new roof and
# its sidecar in place of the old (+13,761), the yard fences and dooryard stems the
# larger footprint re-derives (+911), the ruling L222 in liberties.json (+7,655), the
# release entry in its two published copies (+5,414), and 7,404 bytes of sidecars that
# were STALE ON DEV and that any PR touching compile_scene.py has to carry. Everything
# in that list is either derived geometry or reasoning. The two prose items together are
# 13,069 bytes against an overflow of 21,341, so deleting BOTH of them entirely — the
# liberty that records the invention and the note that tells a visitor what changed —
# would still leave the tree 8,272 bytes over. Going further would have meant deleting
# reasoning rather than de-duplicating it, which is what the 28 -> 32 note refused, for
# the same reason, and it is refused again here.
#
# WHAT SUPPORTS 36. The LFS clause at the top is still the real constraint and it is
# about FORMAT: the tree holds plain binaries at 36 MiB exactly as it did at 25. Pages
# allows 1 GB a site, so this is under 4 % of what the host permits, and
# docs/RENDERING.md § the gate table has recorded a sanctioned raise to ~100 MB at H2
# since the rendering plan was written. It restores 3.98 MiB of headroom — more than
# either previous raise bought, 2.85 then 3.52 — which is the first raise in the three
# to leave room for a year of releases rather than a season of them.
#
# WHAT WILL EXHAUST IT AGAIN, NAMED RATHER THAN DISCOVERED. The same two items the last
# raise named, both still open and both now larger: the duplicated changelog is
# 2,753,794 bytes, 8.2 % of the tree and the fastest-growing item in it because it grows
# on every release rather than on every building (T-0364), and the letter-list cohort is
# 2.54 MiB (T-0438). Answering T-0364 alone would return more than two thirds of what
# this raise buys. Neither is answered here: a re-budget buys the time to answer them
# and is not an answer, and folding either into a ticket about a dwelling on Lake Street
# would be two units in one revert.
# AND 36 IS SPENT, ON THE GROUND ITSELF — T-0464, 2026-09-13, the fourth run to hit the
# wall after T-0317 at 25, T-0379 at 28 and T-0593 at 32. The pattern is the same and so
# is the test: say what the unit adds, show it cannot be trimmed, and name what will
# exhaust the next one.
#
# WHAT THIS UNIT ADDS. The owner asked for the shared south terrain to reach modern
# Cermak Road so the 1812 evacuation corridor and the Prairie Avenue district have ground
# to stand on. The box goes from 2 020 x 930 m to 2 020 x 4 200 m and the field from
# 301 757 samples to 1 359 929, which publishes 2 116 344 more bytes of heightfield.bin
# and 1 018 468 more of the terrain derivative: 2.99 MiB, and it is the GROUND. There is
# no prose in it and no duplicate.
#
# WHY IT CANNOT BE TRIMMED. The ticket's acceptance is that a baked epoch covers
# Madison-to-Cermak WITHOUT out-of-bounds fallback, so the field has to reach there at
# the cell the renderer's sampler indexes; the apron, which is free, is exactly the
# fallback the acceptance excludes. Two trims were made before asking for this raise and
# they are already in the number above: the micro-relief texture is switched off south of
# Madison Street, where nothing walks and 30 mm subtends a hundredth of a pixel, which
# returned 807 KiB of payload and 9.10 MB of master; and the surface below Twelfth Street
# is one evidenced row carried, not a computed one, which is what lets the planar dissolve
# collapse it at all. What is left over the budget is 0.73 MB, and the cheapest thing that
# could pay it is the changelog this tree still ships twice (2.04 MB in the walk copy's
# place) — which is T-0364, open, and folding it into a ticket about terrain would be two
# units in one revert, exactly as the 32 -> 36 note refused.
#
# WHAT SUPPORTS 40. Unchanged from the last raise and still the real constraint: the
# clause at the top is about FORMAT, not size, and the tree holds plain binaries at 40 MiB
# as it did at 25. Pages allows 1 GB a site; docs/RENDERING.md's gate table has recorded a
# sanctioned raise to ~100 MB at H2 since the rendering plan was written. This restores
# 3.27 MiB of headroom, in the band the last three raises bought (2.85, 3.52, 3.98).
#
# WHAT WILL EXHAUST IT AGAIN. T-0364's duplicated changelog, still the fastest-growing
# item in the tree because it grows on every release; T-0438's letter-list cohort; and now
# a third, which this unit created and should be said plainly: T-0466, the south-terrain
# tiling and culling plan, is what makes a four-kilometre field affordable, and it sits
# BELOW this ticket in the queue. The field arrived before the plan for carrying it.
#
# AND THE NUMBER MOVED AGAIN, 2026-09-16 (T-0727) — 40 -> 256, AS A RE-BUDGET, NOT A
# WEAKENING. The whole-tree total is the wrong proxy for what a size budget defends:
# measured on this day's tree, a first-time visitor downloads 7.223 MB to stand in
# the 1835 street while the tree carries 38.87 MB — the 1,385 household cards are
# 28 % of the tree and cost a first visit nothing until one is opened. The number
# that defends the visitor is the BOOT PAYLOAD budget in docs/SITE-BUDGET.md §4
# (12 MB, enforced by tools/measure_boot_payload.mjs --check); this cap becomes the
# repository-hygiene guard it always was, set at a quarter of GitHub Pages' 1 GB
# documented site limit so the tree cannot approach the platform wall by drift.
# Raising it removes the recurring "pay for the budget out of the record" raises
# (32 -> 36 -> 40, each bought with a doc edit); the honest guard on visitor cost
# is the boot budget now.
SITE_BUDGET_MB = 256
# Warn at 90 % of it. See run_site_check for why this band exists (T-0722).
SITE_WARN_FRACTION = 0.90
# Identical files smaller than this are not worth a merge refusal (T-0722).
SITE_DUPE_FLOOR = 64 * 1024

CONFIDENCE = ("attested", "inferred", "reconstructed")
SLUG = re.compile(r"^[a-z0-9_]+$")

# The record's fixed attested blocks, in the order a claim reads best. Everything
# else a liberty can be held to is under `form`, whose vocabulary is open and is
# enumerated from the data rather than listed here. Kept in step with
# tools/compile_liberties.py's COVER_ASPECTS.
PHASE_ASPECTS = ("footprint", "position", "documented_range")
STRUCTURE_ASPECTS = ("function", "occupants")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    def ok(self, strict: bool) -> bool:
        return not self.errors and not (strict and self.warnings)

    def print(self, strict: bool) -> None:
        for n in self.notes:
            print(f"  {n}")
        for w in self.warnings:
            print(f"  WARN  {w}")
        for e in self.errors:
            print(f"  FAIL  {e}")
        n_e, n_w = len(self.errors), len(self.warnings)
        verdict = "PASS" if self.ok(strict) else "FAIL"
        print(f"\n{verdict}  {n_e} error(s), {n_w} warning(s)"
              + ("  [strict: warnings are errors]" if strict else ""))


def load_json(path: Path, rep: Report, required: bool = True):
    if not path.exists():
        if required:
            rep.error(str(path.relative_to(ROOT)), "missing")
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        rep.error(str(path.relative_to(ROOT)), f"invalid JSON: {e}")
        return None


def parse_date(s: str):
    try:
        return dt.date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------
# schema
# --------------------------------------------------------------------------

def validate_schemas(sources, structures, scenes, rep: Report) -> None:
    """JSON Schema pass, when jsonschema is installed.

    The semantic checks below are the ones that actually protect the dataset,
    so a missing jsonschema degrades to a warning rather than blocking work.
    """
    try:
        import jsonschema
    except ImportError:
        rep.warn("schema", "jsonschema not installed; skipping schema pass "
                           "(pip install jsonschema). Semantic checks still ran.")
        return

    pairs = [
        (DATA / "source.schema.json", sources, "source"),
        (DATA / "structures.schema.json", structures, "structure"),
        (DATA / "scene.schema.json", scenes, "scene"),
    ]
    for schema_path, docs, label in pairs:
        if not schema_path.exists():
            rep.error("schema", f"missing schema {schema_path.name}")
            continue
        schema = load_json(schema_path, rep)
        if schema is None:
            continue
        validator = jsonschema.Draft202012Validator(schema)
        for path, doc in docs.items():
            for err in sorted(validator.iter_errors(doc), key=lambda e: e.path):
                loc = "/".join(str(p) for p in err.path) or "(root)"
                rep.error(f"{label} {path}", f"{loc}: {err.message}")


# --------------------------------------------------------------------------
# semantic: the confidence contract
# --------------------------------------------------------------------------

def check_attested(where: str, key: str, att: dict, source_ids: set, rep: Report) -> str | None:
    """attested needs a resolving source; inferred and reconstructed need stated reasoning."""
    if not isinstance(att, dict) or "confidence" not in att:
        return None
    conf = att.get("confidence")
    if conf not in CONFIDENCE:
        rep.error(where, f"{key}: unknown confidence '{conf}'")
        return None

    srcs = att.get("sources") or []
    note = (att.get("note") or "").strip()

    # THE PER-ATTRIBUTE TIER (T-1158), checked wherever a block carries one.
    #
    # `confidence` says how well a value is evidenced; `tier` says which of the
    # four kinds of thing the value IS — read from a source, reasoned about this
    # person, invented from a model or a rule, or not asserted at all. They are not
    # the same axis, and the fourth tier is the reason: 7,314 blocks in the resident
    # layer carry `confidence: "reconstructed"` over a value that asserts nothing,
    # which is the opposite of what a reconstruction band will mean by the word.
    #
    # The tier is DERIVED from the confidence and the value and may not disagree
    # with that derivation, so this cannot become a second, softer grade that a
    # writer sets to whatever flatters the record. What it adds is the obligations:
    # a genuinely invented value owes a basis, a replacement rule, and — when it was
    # drawn rather than argued — the seed that redraws it.
    check_tier_block(where, key, att, rep.error)

    if conf == "attested":
        if not srcs:
            rep.error(where, f"{key}: attested requires at least one source_id")
        for sid in srcs:
            if sid not in source_ids:
                rep.error(where, f"{key}: source '{sid}' does not resolve in data/sources/")
    elif conf == "inferred":
        # Reasoned FROM something, so it owes the reasoning; and it may cite the
        # evidence it reasoned from, which is the ordinary case.
        if not note:
            rep.error(where, f"{key}: inferred requires a note stating the reasoning")
        for sid in srcs:
            if sid not in source_ids:
                rep.error(where, f"{key}: source '{sid}' does not resolve in data/sources/")
    else:  # reconstructed — invented to fill a demonstrable need of the town
        # It owes its reasoning too: an invention nobody can defend is the thing
        # this project exists not to ship. What it may NOT be is silent.
        #
        # It may also cite sources, and under the old vocabulary that was a
        # warning — "conjectural but cites sources, so either it is not
        # conjectural or the citation is decorative". That rule died with the
        # rename: a reconstructed value is invented WITHIN a bound, and the source
        # that establishes the bound (the reconstruction programme, a trade
        # roster, a census total) is exactly what makes the invention defensible
        # rather than arbitrary. Citing it is right, not suspicious.
        if not note:
            rep.error(where, f"{key}: reconstructed requires a note stating the reasoning — "
                             f"an invention nobody can defend is not a reconstruction")
        for sid in srcs:
            if sid not in source_ids:
                rep.error(where, f"{key}: source '{sid}' does not resolve in data/sources/")
    return conf


def walk_attested(where: str, node, source_ids: set, rep: Report, tally: dict, prefix: str = "") -> None:
    """Find every attested block in a record and check it."""
    if isinstance(node, dict):
        if "confidence" in node and "value" in node:
            conf = check_attested(where, prefix or "(attr)", node, source_ids, rep)
            if conf:
                tally[conf] = tally.get(conf, 0) + 1
            return
        for k, v in node.items():
            walk_attested(where, v, source_ids, rep, tally, f"{prefix}.{k}" if prefix else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk_attested(where, v, source_ids, rep, tally, f"{prefix}[{i}]")


def check_range(where: str, rng: dict, source_ids: set, rep: Report) -> tuple:
    frm, to = parse_date(rng.get("from", "")), parse_date(rng.get("to", ""))
    if frm is None or to is None:
        rep.error(where, "documented_range: from/to must be ISO dates")
        return None, None
    if to < frm:
        rep.error(where, f"documented_range: to ({to}) precedes from ({frm})")
    # A wide range is only suspicious when it is a guess. A building that demonstrably
    # stood for twenty years and burned on a recorded date is not the failure mode this
    # rule exists to catch — a vague range widened until the date gate stopped complaining is.
    if (to - frm).days > WIDE_RANGE_YEARS * 365.25 and rng.get("confidence") != "attested":
        rep.warn(where, f"documented_range spans {(to - frm).days // 365} years and is not "
                        f"documented — Chicago changed fast in this period; narrow it to what "
                        f"is attested rather than widening it to pass")
    for sid in rng.get("sources") or []:
        if sid not in source_ids:
            rep.error(where, f"documented_range: source '{sid}' does not resolve")
    if rng.get("confidence") == "reconstructed" and not (rng.get("note") or "").strip():
        rep.error(where, "documented_range: inferred requires a note")
    # The confidence contract applied to the claim the whole scene rests on. Every
    # other `documented` value in this dataset owes a resolving source (see
    # check_attested); the date span was outside that rule for no reason but the
    # order the checks were written in, and it is the claim that decides whether a
    # building is in the town at all. It reaches the provenance card now, which is
    # the argument for holding it to the same standard as a roof pitch.
    if rng.get("confidence") == "attested" and not (rng.get("sources") or []):
        rep.error(where, "documented_range: documented requires at least one source_id")
    return frm, to


# --------------------------------------------------------------------------
# semantic: scenes resolve against phases
# --------------------------------------------------------------------------

def validate_scene(scene: dict, structures: dict, epochs: dict, exclusions: dict, rep: Report,
                   households: dict | None = None) -> None:
    sid = scene.get("id", "?")
    where = f"scene {sid}"
    target = parse_date(scene.get("target_date", ""))
    if target is None:
        rep.error(where, "target_date must be an ISO date")
        return

    # the epoch must exist and cover the date
    ep_id = scene.get("terrain_epoch")
    ep = epochs.get(ep_id)
    if ep is None:
        rep.error(where, f"terrain_epoch '{ep_id}' does not resolve in data/terrain/epochs.json")
    else:
        frm, to = parse_date(ep.get("from", "")), parse_date(ep.get("to", ""))
        if frm and to and not (frm <= target <= to):
            rep.error(where, f"terrain_epoch '{ep_id}' covers {frm}..{to}, "
                             f"which does not include target_date {target}")

    included, excluded, blocked = [], [], []
    for path, st in structures.items():
        covering = []
        for ph in st.get("phases", []):
            rng = ph.get("documented_range", {})
            frm, to = parse_date(rng.get("from", "")), parse_date(rng.get("to", ""))
            if frm and to and frm <= target <= to:
                covering.append(ph.get("id", "?"))
        if len(covering) > 1:
            rep.error(f"structure {st.get('id', path)}",
                      f"{len(covering)} phases cover scene {sid} ({target}): {covering} — "
                      f"exactly one must")
        elif len(covering) == 1:
            included.append(f"{st.get('id')}:{covering[0]}")
            if st.get("review_required"):
                blocked.append(st.get("id"))
        else:
            excluded.append(st.get("id"))

    # The people carry the same flag as the buildings, and until 2026-08-16 this list
    # was built out of data/structures/ alone — so a household flagged for AGENTS.md's
    # standing constraint blocked nothing, while the error this validator prints on the
    # household side promised that "any record touching it blocks a scene from being
    # marked released" (ROADMAP K34). The seven flagged households were covered anyway,
    # by the coincidence that every one of them lives or works in a building that is
    # also flagged; nothing required that, and tools/measure_review_constraint.py now
    # does. A household is not date-gated the way a phase is: the residents layer runs
    # its own scene-date gate, and a record flagged for consultation is not made safe
    # to release by being absent from one year of it.
    for hid, h in sorted((households or {}).items()):
        if h.get("review_required"):
            blocked.append(hid)
        for p in h.get("persons", []):
            if p.get("review_required"):
                blocked.append(hid)
                break

    if scene.get("released") and blocked:
        rep.error(where, f"released is true but these records carry review_required: "
                         f"{sorted(set(blocked))}")

    rep.note(f"scene {sid} ({target}): {len(included)} structure(s) included, "
             f"{len(excluded)} excluded by date"
             + (f" [{', '.join(excluded)}]" if excluded else ""))

    # exclusions.json is a research record, not a filter — but it should not
    # contradict the dataset by naming something that is actually in the scene.
    for ex in exclusions.get("excluded", []):
        if ex.get("id") in [i.split(":")[0] for i in included]:
            rep.error(where, f"'{ex.get('id')}' is listed in exclusions.json but resolves "
                             f"into this scene — the data and the research record disagree")
        # The same disagreement in its second form, which no record can report
        # because the excluded structure has no record: an entry that dates a
        # building to 1837 is not an exclusion from an 1837 scene. Nothing here
        # is wrong at one year and becomes wrong later without saying so — this
        # project is year-parameterized, so the year has to be asked.
        earliest = str(ex.get("earliest_scene") or "")
        if earliest.isdigit() and int(earliest) <= target.year:
            rep.error(where, f"'{ex.get('id')}' is excluded, but its own earliest_scene "
                             f"({earliest}) is on or before this scene ({target.year}) — "
                             f"it belongs in the dataset here, or the entry is wrong")


def check_exclusions(exclusions: dict, source_ids: set, rep: Report) -> None:
    """The research record of what was left out is held to the citation rule.

    Every `source_id` in this project must resolve in `data/sources/` — rule one
    in AGENTS.md — and until this check, exclusions.json was the one file where
    it did not: nothing read its `sources` arrays, so a citation there could name
    a source that has never existed. That mattered least while the file was read
    only by agents and matters most now that the walkthrough quotes it: a visitor
    reading why the Saloon Building is not here is reading these ids joined to
    their citations.

    A reason is required for the same reason a `note` is required on an inferred
    value. "Left out" without a stated ground is not a finding, it is a deletion
    with a filename.
    """
    seen: set[str] = set()
    for ex in exclusions.get("excluded", []):
        eid = ex.get("id") or "?"
        where = f"exclusion {eid}"
        if not SLUG.match(eid):
            rep.error(where, f"id '{eid}' is not a lowercase slug")
        if eid in seen:
            rep.error(where, "duplicate id in exclusions.json")
        seen.add(eid)
        if not (ex.get("name") or "").strip():
            rep.error(where, "no name — the list is read by people, not only by ids")
        if not (ex.get("reason") or "").strip():
            rep.error(where, "no reason — an exclusion without a stated ground is a "
                             "deletion, and this file exists so that it is a finding")
        srcs = ex.get("sources") or []
        if not srcs:
            rep.error(where, "no sources — excluding a structure is a claim about the "
                             "evidence and carries a citation like any other")
        for s in srcs:
            if s not in source_ids:
                rep.error(where, f"source '{s}' does not resolve in data/sources/")


# The claims the provenance card renders, as a RECORD names them mapped to the
# sidecar field the card reads. Two of the three words are the same on both sides;
# the position's is not, because `compile_scene.py` flattens the phase's position
# block into `placement.*`. The map is authored — a phase field and a card section
# are two documents and something has to say which pairs with which — but the
# CHECK is not: each path has to be one `renderers/web/js/popup.js` actually
# reads, scanned by the same machinery that found `asset_is_placeholder` never
# rendering. So deleting a section from the card fails here rather than leaving
# the Evidence panel promising a card that shows nothing.
CARD_CLAIM_PATHS = {
    "documented_range": "documented_range",
    "footprint": "footprint",
    "position": "placement.position_confidence",
}

PROVENANCE_CARD = Path("renderers") / "web" / "js" / "popup.js"


def card_claim_reads() -> set[str]:
    """The sidecar paths the provenance card reads, off the card itself."""
    path = ROOT / PROVENANCE_CARD
    if not path.is_file():
        return set()
    return {dotted for _, dotted in sidecar_field_reads(path.read_text(encoding="utf-8"))}


def check_watch_list(exclusions: dict, structures: dict, source_ids: set,
                     rep: Report, root: Path | None = None) -> None:
    """The third category — researched, and neither built nor ruled out.

    `excluded` is a settled finding and a record is a settled decision. Between
    them sits the watch list: four structures whose 1835 status is genuinely
    open. It has been four free-text sentences since the scaffold, read by
    nobody but an agent, and its own stated purpose — "listed here so nobody
    promotes them to documented without new evidence" — was a sentence with
    nothing behind it. One of the four IS in the dataset, so that sentence is
    checkable, and this checks it: an entry naming a committed record must say
    which of the record's claims carries the uncertainty, and that claim may not
    be `documented`. The day the evidence arrives, the promotion fails here and
    the entry has to be argued off this list rather than quietly outgrown.

    The other direction is the cheaper half and worth as much: an entry naming a
    structure that has since been built, still declaring itself unbuilt, would be
    the drift L12 was caught by — a document and its data disagreeing because
    nobody carried a change back.

    The named claim must also be one the provenance card RENDERS, which is the
    other half of the same promise. The Evidence panel's entry for a standing
    structure ends by telling a visitor that "the provenance card shows it" — a
    sentence about a surface this file could not see, which is exactly the shape
    of the two faults that cost this project a `documented_range` and an
    `asset_is_placeholder` that never rendered on any building. `carried_by` could
    have named a graded block the card has no section for, and the panel would
    have gone on promising it. The claim is now held to `CARD_CLAIM_PATHS`, and
    each of those paths is held to being one the card really reads.

    A question is required for the reason a reason is required on an exclusion:
    an id and a shrug is not a finding. `sources` are held to rule one like
    every other citation in this project, and an entry with none must SAY it has
    none and why — the escape hatch is a sentence a reader can weigh, not an
    empty array. The dossier pointer is checked to resolve to a committed file
    and to a line in it, because a pointer into research nobody can find is the
    same failure one level up.
    """
    root = root or ROOT
    excluded_ids = {ex.get("id") for ex in exclusions.get("excluded", [])}
    # Read once, and off the real card rather than off `root`: a temp fixture
    # carries a dataset, never a renderer, and the card being checked is the one
    # that ships.
    card_reads = card_claim_reads()
    seen: set[str] = set()
    uncited: list[str] = []
    for item in exclusions.get("watch_list", []):
        wid = item.get("id") or "?"
        where = f"watch list {wid}"
        if not SLUG.match(wid):
            rep.error(where, f"id '{wid}' is not a lowercase slug")
        if wid in seen:
            rep.error(where, "duplicate id in the watch list")
        seen.add(wid)
        if wid in excluded_ids:
            rep.error(where, "is also in `excluded` — a structure is either ruled out or "
                             "an open question, and saying both says neither")
        if not (item.get("name") or "").strip():
            rep.error(where, "no name — the list is read by people, not only by ids")
        if not (item.get("question") or "").strip():
            rep.error(where, "no question — an entry here states what is UNCERTAIN; an id "
                             "with no question is a hunch with a filename")

        # rule one, and the sentence that stands in for a citation when there is
        # honestly none to give
        srcs = item.get("sources") or []
        for s in srcs:
            if s not in source_ids:
                rep.error(where, f"source '{s}' does not resolve in data/sources/")
        if not srcs:
            uncited.append(wid)
            if not (item.get("no_source_record") or "").strip():
                rep.error(where, "no sources and no `no_source_record` — an open question "
                                 "with nothing behind it has to say so in words, because "
                                 "an empty array reads as an oversight")

        # the dossier pointer resolves to a file and to a line in it
        dossier = item.get("dossier") or {}
        dfile, anchor = dossier.get("file"), dossier.get("anchor")
        if not dfile or not anchor:
            rep.error(where, "no dossier pointer — an open question comes from somewhere, "
                             "and `file` + `anchor` is where the next agent starts")
        else:
            path = root / dfile
            if not path.is_file():
                rep.error(where, f"dossier '{dfile}' is not a committed file")
            elif anchor not in path.read_text(encoding="utf-8"):
                rep.error(where, f"dossier '{dfile}' does not contain the anchor "
                                 f"'{anchor}' — a pointer nobody can follow is not one")

        # both directions against the dataset
        record = next((st for st in structures.values() if st.get("id") == wid), None)
        declared = bool(item.get("in_dataset"))
        if record is None and declared:
            rep.error(where, "declares in_dataset but no record of that id exists in "
                             "data/structures/")
        if record is not None and not declared:
            rep.error(where, "a record of that id IS committed and the entry still says it "
                             "is not in the dataset — the document and the data disagree")
        if record is None and (item.get("carried_by") or "").strip():
            rep.error(where, "carries `carried_by` with no record to carry it")
        if record is not None and declared:
            ref = (item.get("carried_by") or "").strip()
            if not ref:
                rep.error(where, "in the dataset and does not say which claim carries the "
                                 "uncertainty — the point of this list is that the claim "
                                 "stays honest, so it has to be named")
                continue
            if ref.count(".") != 1:
                rep.error(where, f"carried_by '{ref}' is not '<phase_id>.<field>'")
                continue
            pid, field = ref.split(".")
            phase = next((p for p in record.get("phases", []) if p.get("id") == pid), None)
            if phase is None:
                rep.error(where, f"carried_by names phase '{pid}', which the record does "
                                 f"not have")
                continue
            claim = phase.get(field)
            if not isinstance(claim, dict):
                rep.error(where, f"carried_by names '{field}' on phase '{pid}', which is "
                                 f"not a graded claim on the record")
                continue
            if not claim.get("confidence"):
                rep.error(where, f"carried_by names '{field}' on phase '{pid}', which "
                                 f"carries no confidence — an uncertainty has to sit on a "
                                 f"claim that is graded, or there is nothing to hold down")
                continue
            if claim.get("confidence") == "attested":
                rep.error(where, f"{ref} is `attested` while this entry says its 1835 "
                                 f"status is open — the watch list exists to stop exactly "
                                 f"that promotion, so either the evidence arrived and the "
                                 f"entry retires, or the grade is wrong")

            # and the promise the panel makes about the other surface
            wanted = CARD_CLAIM_PATHS.get(field)
            if wanted is None:
                rep.error(where, f"carried_by names '{field}', and the provenance card "
                                 f"renders no claim for it — the Evidence panel tells a "
                                 f"visitor the card shows this doubt, so it has to be one "
                                 f"of {sorted(CARD_CLAIM_PATHS)}")
            elif wanted not in card_reads:
                rep.error(where, f"carried_by names '{field}' and {PROVENANCE_CARD} no "
                                 f"longer reads `{wanted}` — the panel would keep promising "
                                 f"a card that shows this claim while the card shows nothing")
    if uncited:
        rep.note(f"watch list: {len(uncited)} entry(ies) rest on no source record "
                 f"[{', '.join(uncited)}] — each says why")


# Land vertices. The terrain spec's own caveat says no land elevation in it is
# better than `inferred` and that the generator refuses to emit `documented` for
# any land vertex — a statement that was true because whoever wrote the spec kept
# it true, and nothing was checking. These are the blocks that set the height of
# ground a visitor walks on; the reaches and the channel are under water.
LAND_ELEVATION_GROUPS = ("bank", "divisions", "marsh_strips", "swales", "micro_relief")


def load_terrain_specs(rep: Report) -> dict[str, dict]:
    """epoch -> its committed `terrain_spec.json`."""
    specs: dict[str, dict] = {}
    for spec_path in sorted((DATA / "terrain" / "epochs").glob("*/terrain_spec.json")):
        specs[spec_path.parent.name] = load_json(spec_path, rep) or {}
    return specs


def terrain_claim_index(specs: dict[str, dict], rep: Report) -> dict[str, dict[str, dict]]:
    """epoch -> claim id -> the graded statement the ground makes.

    Off `compile_scene.ground_claims`, which is also what puts these on the
    Evidence panel — so the set a gate checks, the set a liberty may admit to and
    the set a visitor reads are one set. A second enumeration would agree with
    the panel until the day somebody added a zone to the spec, which is the drift
    this project keeps closing everywhere else.
    """
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import compile_scene as ground  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        rep.error("terrain", f"cannot import the ground compiler, so the claims the "
                             f"Evidence panel shows cannot be checked: {e}")
        return {}
    return {epoch: {c["id"]: c for c in ground.ground_claims(spec, {})}
            for epoch, spec in sorted(specs.items())}


def terrain_inferred_values(index: dict[str, dict[str, dict]]) -> list[tuple]:
    """Every value the ground states without evidence.

    Returns `(epoch, claim_id, label, where)`. The ground invents as freely as a
    record does — a bank face nobody drew, two swale alignments attested nowhere,
    a channel section whose own note says it carries no evidence at all — and a
    visitor walks on all of it. The confidence view even dithers it. So it owes
    `docs/LIBERTIES.md` an admission on exactly the argument an inferred
    footprint does.
    """
    return [(epoch, cid, claim.get("label") or cid, f"terrain {epoch}/{cid}")
            for epoch, claims in sorted(index.items())
            for cid, claim in claims.items()
            if claim.get("confidence") == "reconstructed"]


def check_terrain_claims(source_ids: set, rep: Report,
                         specs: dict[str, dict] | None = None,
                         index: dict[str, dict[str, dict]] | None = None) -> None:
    """The ground is held to the rules a structure record is held to.

    `terrain_spec.json` is as fully graded as any record — a documented water
    plane, three inferred division levels argued from period narrative feet, a
    inferred bank face — and until the ground claims reached the Evidence
    panel it was read only by the generator, so none of it was ever checked.
    Both halves of that mattered: rule one of AGENTS.md is that every
    `source_id` resolves in `data/sources/`, and this was the second file after
    `exclusions.json` where nothing enforced it. A citation here could have named
    a source that never existed, and now a visitor reads these ids joined to
    their citations.

    The claims are enumerated by the same function that puts them on the panel
    (`compile_scene.ground_claims`), so the checked set and the displayed set are
    one set. A gate walking its own copy would agree with the panel until a zone
    was added to the spec.

    Four rules are enforced, all of them the record's rules:
      * every cited `source_id` resolves;
      * a `documented` claim owes at least one resolving source;
      * an `inferred` claim owes stated reasoning;
      * no land elevation may be `documented` — the spec says so itself, in the
        caveat the walkthrough now quotes to visitors.

    The third of those was a WARNING until 2026-08-10, and what it was waiting for
    is worth recording because it was not the data. Three surface-material claims
    carried no note; the only place to write one is `terrain_spec.json`, and that
    file's BYTES were the terrain's staleness hash, so a sentence of reasoning
    reported the ground as stale and could not land without a Blender bake. The
    rule was right, the data was short, and the gate one level down was charging a
    bake for prose. `generators/terrain_inputs.py` strips prose from the hash, the
    three notes are written, and the rule is an error here exactly as
    `check_attested` makes it one on a record.
    """
    if index is None:
        index = terrain_claim_index(specs if specs is not None else load_terrain_specs(rep), rep)

    total = unreasoned = 0
    for epoch, claims in sorted(index.items()):
        for claim in claims.values():
            total += 1
            where = f"terrain {epoch}/{claim['id']}"
            conf = claim["confidence"]
            if conf not in CONFIDENCE:
                rep.error(where, f"confidence '{conf}' is not one of {sorted(CONFIDENCE)}")
            srcs = claim["sources"]
            for s in srcs:
                if s not in source_ids:
                    rep.error(where, f"source '{s}' does not resolve in data/sources/ — "
                                     f"the ground quotes these ids to a visitor")
            if conf == "attested" and not srcs:
                rep.error(where, "documented with no source — the ground is held to the "
                                 "same rule as a structure record, and the strongest "
                                 "grade this project has is the one that needs evidence")
            if conf == "reconstructed" and not any(n.strip() for n in claim["notes"]):
                unreasoned += 1
                rep.error(where, "inferred with no reasoning recorded — that is what "
                                 "separates an inference from a guess, and the ground is "
                                 "held to it exactly as a structure record is. Write the "
                                 "reasoning in terrain_spec.json; prose there is stripped "
                                 "from the terrain's staleness hash, so it costs no bake")
            if conf == "attested" and claim["id"].split(".")[0] in LAND_ELEVATION_GROUPS:
                rep.error(where, "a land elevation marked documented — the spec's own "
                                 "caveat says no land elevation in it is better than "
                                 "inferred, and that sentence is now shown to visitors")

    rep.note(f"ground claims: {total} graded statement(s) in the terrain specs, held to "
             f"the citation and reasoning rules and shown in the Evidence panel; "
             f"{unreasoned} inferred without recorded reasoning")


def terrain_consumed(rep: Report | None = None) -> dict[str, frozenset]:
    """spec block -> the field keys whose value `terrain_gen.build_field` reads.

    Declared as `CONSUMED` in `generators/terrain_inputs.py` — beside the
    denylist, which is the same kind of statement about the same generator, and
    NOT inside `terrain_gen.py`, whose bytes go into the ground's hash whole: a
    constant that cannot move a vertex would have re-staled the terrain and asked
    for a Blender bake to land a declaration. That module explains the choice at
    length. Imported rather than parsed, and it costs nothing —
    `terrain_inputs.py` imports only hashlib, json and pathlib, so `check.sh`
    stays a sub-second gate with no dependencies.
    """
    sys.path.insert(0, str(ROOT / "generators"))
    try:
        import terrain_inputs  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        if rep:
            rep.error("ground-geometry", f"cannot import generators/terrain_inputs.py, so "
                                         f"nothing can tell which of the ground's claims "
                                         f"reach a vertex: {e}")
        return {}
    consumed = getattr(terrain_inputs, "CONSUMED", None)
    if consumed is None:
        if rep:
            rep.error("ground-geometry", "generators/terrain_inputs.py declares no CONSUMED "
                                         "map, so a figure the spec states and the ground "
                                         "does not contain cannot be told from one it does")
        return {}
    return {k: frozenset(v) for k, v in consumed.items()}


def unbuilt_ground_values(index: dict[str, dict[str, dict]],
                          consumed: dict[str, frozenset]) -> list[tuple]:
    """Every figure the ground states that no vertex comes from.

    Returns `(epoch, claim_id, field_key, state, where)` for the declared ones.
    The fields are the ones `compile_scene.ground_fields` puts on the Evidence
    panel, so the gate asks about exactly what a visitor is shown.
    """
    out: list[tuple] = []
    for epoch, claims in sorted(index.items()):
        for cid, claim in claims.items():
            known = consumed.get(cid.split(".")[0])
            if known is None:
                continue
            for f in claim.get("fields") or []:
                if f["key"] in known:
                    continue
                out.append((epoch, cid, f["key"], f.get("mesh"),
                            f"terrain {epoch}/{cid}"))
    return out


def check_ground_geometry(index: dict[str, dict[str, dict]],
                          consumed: dict[str, frozenset], rep: Report) -> None:
    """The ground may not state a figure the mesh does not contain without saying so.

    This is `check_geometry_declarations` arriving on the terrain, and the
    argument does not change in the move. A building's `documented` wolf sign
    over a building with no sign on it is the failure that rule was written for;
    the ground's version is `black_loam_over_quicksand_over_blue_clay`,
    `documented`, on a surface that is one flat earth colour from one edge of the
    box to the other. The confidence model grades how sure we are of the soil. It
    has nothing to say about whether any of it was built, and a visitor reading
    the panel cannot tell the two apart.

    Nothing here depends on somebody noticing. The claims come from
    `compile_scene.ground_claims`, which is what the panel renders; what reaches
    a vertex comes from `terrain_inputs.CONSUMED`, held to the generator's actual
    reads by a scan in the self-tests. Anything in the first and not the second owes a `mesh:`
    declaration on its block, keyed by field name. (`mesh` rather than the
    records' `geometry`, because in a GeoJSON `geometry` is the coordinates and
    the terrain hash strips this key — see `generators/terrain_inputs.py`.)

    Checked in both directions, as on the structure side: declaring a state over
    a figure the generator DOES read is a false admission that would quietly
    excuse a real omission the day the generator stopped reading it.
    """
    if not consumed:
        rep.note("ground geometry check: no CONSUMED map to compare against")
        return
    missing_group = sorted({cid.split(".")[0]
                            for claims in index.values() for cid in claims
                            if cid.split(".")[0] not in consumed})
    for group in missing_group:
        rep.error("ground-geometry", f"the terrain spec grades a '{group}' block and "
                                     f"terrain_inputs.CONSUMED says nothing about it — 'the "
                                     f"generator ignores it' and 'nobody has said' are "
                                     f"different states and only one of them is a finding")

    declared = owed = 0
    for epoch, cid, key, state, where in unbuilt_ground_values(index, consumed):
        if state is None:
            rep.error(where, f"'{key}' is a figure this claim states, the terrain generator "
                             f"never reads it, and the Evidence panel shows it to a visitor "
                             f"under a confidence chip — so nothing in the ground comes from "
                             f"it and nothing says so. Declare what the ground does in "
                             f"the block's mesh map: 'absent' (nothing of it is built), "
                             f"'simplified' (a fixed default stands in its place), "
                             f"'record_only' (recorded, never a build instruction) or "
                             f"'restated_in_code' (the mesh agrees with it and does not read "
                             f"it). Prose and declarations in terrain_spec.json are stripped "
                             f"from the staleness hash, so this costs no bake")
            continue
        if state not in GROUND_GEOMETRY_STATES:
            rep.error(where, f"'{key}' declares mesh: '{state}', which is not one of "
                             f"{', '.join(GROUND_GEOMETRY_STATES)}")
            continue
        declared += 1
        owed += state in GEOMETRY_OWES_LIBERTY

    # The other direction: an admission over a figure that is built.
    for epoch, claims in sorted(index.items()):
        for cid, claim in claims.items():
            known = consumed.get(cid.split(".")[0])
            if known is None:
                continue
            for f in claim.get("fields") or []:
                if f["key"] in known and f.get("mesh"):
                    rep.error(f"terrain {epoch}/{cid}",
                              f"'{f['key']}' declares mesh: '{f['mesh']}', but "
                              f"terrain_gen reads this field — the ground is built from the "
                              f"value, so there is nothing to declare. Drop it, or take the "
                              f"key out of CONSUMED if the generator stopped using it")

    rep.note(f"ground geometry check: {declared} stated figure(s) the terrain generator does "
             f"not read, each declaring what the ground does instead; {owed} of them owe "
             f"docs/LIBERTIES.md an admission")


def terrain_restates(rep: Report | None = None) -> dict[str, dict]:
    """spec block -> field key -> where the other half of the restatement lives.

    Declared as `RESTATES` in `generators/terrain_inputs.py`, beside `CONSUMED`
    and for the same reason: it is a statement about the generator, and a new key
    in `terrain_spec.json` outside the stripped `mesh` block would be a mesh input
    and would cost a Blender bake to write down.
    """
    sys.path.insert(0, str(ROOT / "generators"))
    try:
        import terrain_inputs  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        if rep:
            rep.error("ground-restated", f"cannot import generators/terrain_inputs.py, so "
                                         f"nothing can tell what the ground's restatements "
                                         f"are supposed to agree with: {e}")
        return {}
    return dict(getattr(terrain_inputs, "RESTATES", {}) or {})


def strip_py_comments(text: str) -> str:
    """The same source with comment tokens blanked and line numbers preserved.

    A scan for an expression in the generator must not be satisfied by a comment
    quoting that expression — which is not hypothetical: `check_sidecar_contract`
    reported itself on its first run, because the comment explaining why a field
    is no longer read names the field. `tokenize` rather than a regex, because a
    `#` inside a string literal is not a comment and this file is not the place
    to rediscover that.
    """
    try:
        import io  # noqa: PLC0415
        import tokenize  # noqa: PLC0415
        out = list(text)
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type != tokenize.COMMENT:
                continue
            (r1, c1), (r2, c2) = tok.start, tok.end
            if r1 != r2:  # a comment token is always one line
                continue
            starts = [0]
            for line in text.splitlines(keepends=True):
                starts.append(starts[-1] + len(line))
            for i in range(starts[r1 - 1] + c1, min(starts[r1 - 1] + c2, len(out))):
                out[i] = " "
        return "".join(out)
    except Exception:  # noqa: BLE001 — a generator that will not tokenize is its own error
        return text


def check_restated_agreement(index: dict[str, dict[str, dict]],
                             restates: dict[str, dict], rep: Report) -> None:
    """`restated_in_code` promises an agreement, so something has to check it.

    The other three `mesh:` states say the ground does NOT contain a figure, and a
    reader who doubts one can go and look. This one says the opposite — the mesh
    contains exactly what the figure says and does not read it from here — which
    is a claim about two documents at once, and the pair was held together by the
    hand that wrote them and by nothing else. `docs/STATUS.md` § 35 filed that as
    the residual: *the one state that asserts an agreement nothing enforces, which
    is a smaller version of the fault this whole family of checks exists to end.*

    Both directions, as everywhere else in this family. A figure declaring the
    state with no entry in `terrain_inputs.RESTATES` is back to asserting an
    agreement with nothing named on the other side of it, and an entry naming a
    figure that no longer declares the state is a check quietly guarding nothing.

    What each kind buys is `RESTATES`' own subject and is written there. The short
    version: an `artifact` claim is held against the heightfield the bake wrote, a
    `figure` claim against the build instruction it restates, and a `code` claim —
    prose describing an algorithm — only against the presence of the expression it
    names. The third is the weak one and is labelled as such rather than left to
    look like the other two.
    """
    if not restates:
        rep.note("restated-in-code check: no RESTATES map to compare against")
        return

    gen_src = strip_py_comments((ROOT / "generators" / "terrain_gen.py").read_text())
    gen_flat = " ".join(gen_src.split())
    checked = weak = 0

    for epoch, claims in sorted(index.items()):
        ep_dir = DATA / "terrain" / "epochs" / epoch
        for cid, claim in claims.items():
            block = cid.split(".")[0]
            declared = restates.get(block) or {}
            fields = {f["key"]: f for f in (claim.get("fields") or [])}
            where = f"terrain {epoch}/{cid}"

            for key, f in fields.items():
                if f.get("mesh") == "restated_in_code" and key not in declared:
                    rep.error(where, f"'{key}' declares mesh: 'restated_in_code' — the mesh "
                                     f"agrees with this figure and does not read it — and "
                                     f"nothing says WHAT it agrees with. That is the state "
                                     f"asserting an agreement with an unnamed second half, "
                                     f"which is the arrangement it was written to end. Name "
                                     f"the other half in terrain_inputs.RESTATES")

            for key, claim_of in declared.items():
                f = fields.get(key)
                if f is None:
                    continue  # a block may not state every figure the map knows about
                if f.get("mesh") != "restated_in_code":
                    rep.error(where, f"terrain_inputs.RESTATES says '{key}' restates "
                                     f"{claim_of[1]}, and the figure declares mesh: "
                                     f"'{f.get('mesh') or 'nothing'}'. A restatement that is "
                                     f"not declared one is a check guarding a promise nobody "
                                     f"made")
                    continue
                kind = claim_of[0]
                checked += 1

                if kind == "artifact":
                    ref, scale = claim_of[1], float(claim_of[2])
                    fname, _, akey = ref.partition(":")
                    doc = load_json(ep_dir / fname, rep, required=False) or {}
                    if akey not in doc:
                        rep.error(where, f"'{key}' restates {ref} and that artifact has no "
                                         f"'{akey}' — the figure it agrees with is gone")
                        continue
                    want, got = float(f["value"]) * scale, float(doc[akey])
                    if abs(want - got) > 1e-9:
                        rep.error(where, f"'{key}' is {f['value']} and declares that the mesh "
                                         f"agrees with it, but {fname} records {akey} = {got}, "
                                         f"which is {want} short of it. One of the two is "
                                         f"describing a ground that does not exist, and the "
                                         f"panel is showing the spec's number to a visitor")
                elif kind == "figure":
                    other = claim_of[1]
                    if other not in fields:
                        rep.error(where, f"'{key}' restates '{other}' and this block does not "
                                         f"state '{other}'")
                        continue
                    a, b = f["value"], fields[other]["value"]
                    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                        same = abs(float(a) - float(b)) <= 1e-9
                    else:
                        same = a == b
                    if not same:
                        rep.error(where, f"'{key}' is {a} and restates '{other}', which is {b}. "
                                         f"'{other}' is what the generator reads, so the ground "
                                         f"is built to {b} and the Evidence panel is telling a "
                                         f"visitor {a}")
                elif kind == "code":
                    expr = " ".join(claim_of[1].split())
                    n = gen_flat.count(expr)
                    if n != 1:
                        rep.error(where, f"'{key}' describes, for a reader, what terrain_gen.py "
                                         f"does — and the line it names, `{claim_of[1]}`, "
                                         f"appears {n} times in that generator with comments "
                                         f"stripped. Either the code moved and this figure now "
                                         f"describes a ground the model no longer has, or the "
                                         f"expression was reformatted and the declaration in "
                                         f"terrain_inputs.RESTATES needs to follow it")
                    weak += 1
                else:
                    rep.error(where, f"'{key}' declares an unknown restatement kind '{kind}'")

    rep.note(f"restated-in-code check: {checked} figure(s) the ground agrees with and does not "
             f"read, each held against the half it restates; {weak} of them are prose about an "
             f"algorithm and are checked only for the presence of the line they describe")


# --------------------------------------------------------------------------
# semantic: the liberties document is complete about what was invented
# --------------------------------------------------------------------------

def graded_values(structures: dict) -> list[tuple]:
    """Every value a structure record puts a confidence on, with the block itself.

    Returns `(structure_id, phase_id|None, aspect, where, block)`, with `aspect`
    in the same vocabulary a `Covers:` token is written in — `footprint`,
    `position`, `documented_range`, the structure-level `function` and
    `occupants`, and `form.<attribute>` for anything under a phase's form,
    however deeply nested.

    The form half is enumerated from the data rather than from a list, because
    the archetypes keep adding attributes and a hard-coded vocabulary would
    quietly stop asking about the newest ones — which is the exact failure the
    checks built on this enumeration exist to prevent, one level up.

    One enumeration, several questions: `inferred_values` asks which of these
    were invented, and `check_evidence_ladder` asks what each one rests on. Two
    walks over the same record is how two gates start disagreeing about what a
    record contains.
    """
    found: list[tuple] = []

    def walk_form(node, sid: str, pid: str, where: str, path: str) -> None:
        if not isinstance(node, dict):
            return
        if "confidence" in node and "value" in node:
            found.append((sid, pid, path, where, node))
            return
        for k, v in node.items():
            walk_form(v, sid, pid, where, f"{path}.{k}")

    for name, st in sorted(structures.items()):
        sid = st.get("id", name)
        for aspect in STRUCTURE_ASPECTS:
            block = st.get(aspect)
            if isinstance(block, dict) and "confidence" in block:
                found.append((sid, None, aspect, f"structure {sid}", block))
        for ph in st.get("phases", []):
            pid = ph.get("id", "?")
            where = f"structure {sid}/{pid}"
            for aspect in PHASE_ASPECTS:
                block = ph.get(aspect)
                if isinstance(block, dict) and "confidence" in block:
                    found.append((sid, pid, aspect, where, block))
            walk_form(ph.get("form") or {}, sid, pid, where, "form")
    return found


def inferred_values(structures: dict) -> list[tuple]:
    """Every value a structure record states without evidence.

    `(structure_id, phase_id|None, aspect, where)` — the `graded_values`
    enumeration filtered to the inventions.
    """
    return [(sid, pid, aspect, where)
            for sid, pid, aspect, where, block in graded_values(structures)
            if block.get("confidence") == "reconstructed"]


def check_evidence_ladder(structures: dict, sources: dict, rep: Report,
                          ground_index: dict | None = None) -> None:
    """What a claim rests on, held to the ladder the schema defines.

    `docs/PROVENANCE.md` § Evidence tiers ranks the evidence and attaches two
    rules to the ranking:

      * tiers 5-6 "must never be the sole evidence for a `documented` attribute";
      * "no geometry is traced from them" — an outline "comes from tier-1 sheets
        or stays inferred".

    Both were written in the prose AND in `data/source.schema.json`, and until
    now neither was enforced anywhere: the word `tier` did not occur in this
    file. Every other rung of the confidence model has had a gate for weeks —
    `documented` owes a resolving source, `inferred` owes stated reasoning, an
    invention owes an admission — while the question those gates all assume an
    answer to, *how good is the source*, was checked by nobody.

    Two readings of the tier-5 rule appear in `docs/PROVENANCE.md` and they are
    not the same rule. The table says such a source may not be the SOLE evidence;
    the 2026-08-10 revision says a tier-5 map "never reaches it, alone or in
    company". The table's reading is the one enforced here, with reasons: the
    revision exists precisely to stop over-caution making the dataset less
    accurate, and forbidding a documented value from CITING a retrospective would
    punish corroboration — the opposite of what it was written for. A value
    carried by a period survey and cross-checked against a 1933 pictorial map is
    better evidenced than the same value with the map struck out.

    The third rule here is a warning, not an error, and it is the one with
    findings in it today. `documented` "still requires a period source"; the
    ladder puts first-hand and testimony-derived evidence at tiers 1-3 and later
    scholarly synthesis at 4. Values resting on nothing but tier 4 are counted
    and named rather than failed, because the fix is research and not a rename:
    either those values are over-graded or those sources are under-tiered — a
    page transcribing a period newspaper is tier 2 whatever the site hosting it
    is, and this dataset already grades one chicagology page that way. Regrading
    a confidence is also a mesh input, so the decision arrives with a bake
    attached. Priced and queued in `docs/STATUS.md` § 43.
    """
    ladder = tier_ladder()
    tiers = {sid: s.get("tier") for sid, s in
             ((s.get("id"), s) for s in sources.values() if isinstance(s, dict))
             if sid}

    def rungs(block: dict) -> list[int]:
        return [tiers[s] for s in (block.get("sources") or [])
                if isinstance(tiers.get(s), int)]

    def named(t: int) -> str:
        return f"tier {t} ({ladder.get(t, '?')})"

    # a source may not declare a use its rung does not support
    for name, s in sorted(sources.items()):
        if not isinstance(s, dict):
            continue
        t = s.get("tier")
        if isinstance(t, int) and t > TRACEABLE_MAX_TIER and s.get("asset_use") == "geometry":
            rep.error(f"source {name}",
                      f"asset_use is 'geometry' at {named(t)} — no geometry is traced from a "
                      f"retrospective reconstruction; it tells you a thing was here, not its "
                      f"outline (docs/PROVENANCE.md § Evidence tiers)")

    claims: list[tuple[str, str, dict]] = [
        (where, aspect, block) for _sid, _pid, aspect, where, block in graded_values(structures)
    ]
    for epoch, blocks in sorted((ground_index or {}).items()):
        for cid, claim in sorted(blocks.items()):
            claims.append((f"ground {epoch}", cid, claim))

    thin: list[str] = []
    for where, aspect, block in claims:
        conf = block.get("confidence")
        got = rungs(block)
        if conf == "attested" and got:
            if min(got) > SOLE_EVIDENCE_MAX_TIER:
                rep.error(where, f"{aspect}: documented on {named(min(got))} alone — tiers "
                                 f"{SOLE_EVIDENCE_MAX_TIER + 1} and up inform inventory and "
                                 f"cross-checks and may never be the sole evidence for a "
                                 f"documented value")
            elif min(got) > TESTIMONY_MAX_TIER:
                thin.append(f"{where} {aspect}")
        # an outline is the one thing a pictorial source cannot give you
        if aspect == "footprint" and conf in ("attested", "reconstructed") and got:
            off = sorted({t for t in got if t > TRACEABLE_MAX_TIER})
            if off:
                rep.error(where, f"footprint: graded {conf} while citing "
                                 f"{', '.join(named(t) for t in off)} — an outline comes from a "
                                 f"period sheet or stays inferred; a retrospective gives you "
                                 f"that a thing was here, not its plan")

    if thin:
        rep.warn("evidence ladder",
                 f"{len(thin)} documented value(s) rest on no source at tier "
                 f"{TESTIMONY_MAX_TIER} or better — later scholarship only, with no period "
                 f"document, eyewitness recollection or compilation from testimony behind them: "
                 f"{', '.join(sorted(thin)[:4])}"
                 + (f" and {len(thin) - 4} more" if len(thin) > 4 else "")
                 + ". Either the values are over-graded or the sources are under-tiered; both "
                   "are research, and regrading a confidence stales a mesh. See "
                   "docs/STATUS.md § 43")

    rep.note(f"evidence ladder: {len(claims)} graded claim(s) held to the {len(ladder)}-rung "
             f"ladder in data/source.schema.json — tiers "
             f"{SOLE_EVIDENCE_MAX_TIER + 1}+ never sole evidence for documented, never an "
             f"outline; {len(thin)} documented on later scholarship alone")


# A record that dates its own retrieval is describing a web page, not a document:
# `date` reads "accessed 2026-08-10" rather than "1884" or "1893-10-29". That
# string is the dataset's own signal and not a new convention — see the check.
_ACCESSED = re.compile(r"^\s*accessed\b", re.I)


def dates_its_own_retrieval(source: dict) -> bool:
    """True when the record dates the fetch rather than the document it carries."""
    return bool(_ACCESSED.match(str(source.get("date") or "")))


def check_transcription_declarations(sources: dict, rep: Report) -> None:
    """A rung is a judgement about a document; this holds it to one.

    `check_evidence_ladder` asks what rung a claim rests on and takes the rung
    from the source record, where somebody typed it. Nothing ever asked what the
    number was a judgement ABOUT — which matters most for the modern pages that
    carry old documents, because there the number is not a judgement about the
    page at all. `chicagology_prefire252` is tier 2 because it prints an 1893
    Tribune retrospective; `chicagology_kinzie_bridge` is tier 3 because it
    prints Andreas, and its `note` said so in as many words — "Tier 3 for the
    Andreas transcription; the surrounding apparatus is a finding aid" — in a
    sentence no check could read. That is the shape of every fault this family of
    gates has found: a true sentence in a file, describing something nothing
    verified.

    So a record that dates its own RETRIEVAL rather than a document — `date`
    reading "accessed 2026-08-10" — and that claims a rung at or above
    `TESTIMONY_MAX_TIER` must declare `transcribes`: the documents it carries,
    each with its own date and its own rung, and each saying which of this
    project's claims it carries. The record's tier is then the best rung
    declared, derived rather than asserted, exactly as a changelog version is.

    Declare the documents the dataset DRAWS ON. A page also carrying a period
    city directory that no value here rests on is carrying apparatus, and
    apparatus goes in `note`; declaring it would claim, falsely, that a rung this
    dataset does not use is a rung it stands on.

    A page that has been READ and reprints nothing is the third state, and it
    needs a word of its own because it is indistinguishable here from a page
    nobody has opened — both declare nothing, and the count below would go on
    calling a read page unread, which is the sentence-nothing-can-see fault this
    whole family of gates exists to end. `wikipedia_chicago_river` is the case:
    it PARAPHRASES Swearingen's 1803 river soundings and footnotes them to a
    named reprinting, which is a citation and not a transcription. Such a record
    says so in `carries_no_document` — the reading, not a flag — and may not be
    graded at or above `TESTIMONY_MAX_TIER`, because there is no document on the
    page for the rung to be a judgement about.

    Two limits, both real and neither closable here. The check cannot read a
    transcription, so it cannot tell whether the document named actually says
    what the note claims — a human read is what put the entry there and a human
    read is what would overturn it. And it is per-record, while
    `check_evidence_ladder` is per-value: a source cited for corroboration on one
    attribute lends its rung to every attribute that lists it, so clearing a
    warning is not the same as improving the evidence for the value that carried
    it. `docs/RESEARCH/evidence_tiers_chicagology.md` walks the committed cases
    one at a time for exactly that reason.
    """
    ladder = tier_ladder()
    undeclared: list[str] = []
    read_and_empty: list[str] = []

    for name, s in sorted(sources.items()):
        if not isinstance(s, dict):
            continue
        tier, declared = s.get("tier"), s.get("transcribes")
        if not isinstance(tier, int):
            continue
        retrieval = dates_its_own_retrieval(s)
        empty = str(s.get("carries_no_document") or "").strip()

        if empty:
            if declared is not None:
                rep.error(f"source {name}",
                          "declares `transcribes` and `carries_no_document` — a page either "
                          "reprints a document or it does not, and both fields are readings of "
                          "the same page")
                continue
            if not retrieval:
                rep.error(f"source {name}",
                          f"dates a document ('{s.get('date')}') and declares "
                          f"`carries_no_document` — a record that IS its document is outside this "
                          f"rule, and saying it reprints nothing describes the wrong page")
                continue
            if tier <= TESTIMONY_MAX_TIER:
                rep.error(f"source {name}",
                          f"graded tier {tier} ({ladder.get(tier, '?')}) while declaring that it "
                          f"reprints no document — a rung at or above {TESTIMONY_MAX_TIER} is a "
                          f"judgement about a document, so a page carrying none is later "
                          f"scholarship at best")
            read_and_empty.append(name)
            continue

        if declared is None:
            if retrieval and tier <= TESTIMONY_MAX_TIER:
                rep.error(f"source {name}",
                          f"graded tier {tier} ({ladder.get(tier, '?')}) while dating its own "
                          f"retrieval ('{s.get('date')}') — a rung at or above "
                          f"{TESTIMONY_MAX_TIER} belongs to a document, not to a page that "
                          f"reprints one, so declare the document in `transcribes`")
            elif retrieval:
                undeclared.append(name)
            continue

        rungs = [e.get("tier") for e in declared if isinstance(e, dict)]
        rungs = [t for t in rungs if isinstance(t, int)]
        if not rungs:
            rep.error(f"source {name}", "`transcribes` declares no rung to read the record's own "
                                        "tier from")
            continue
        best = min(rungs)
        if tier != best:
            rep.error(f"source {name}",
                      f"graded tier {tier} ({ladder.get(tier, '?')}) while the best document it "
                      f"declares carrying is tier {best} ({ladder.get(best, '?')}) — the record's "
                      f"rung is the best rung it transcribes, derived and not typed; move the "
                      f"apparatus out of `transcribes` or correct the tier")
        for i, entry in enumerate(declared):
            if not isinstance(entry, dict):
                continue
            if not str(entry.get("note") or "").strip():
                rep.error(f"source {name}",
                          f"transcribes[{i}] names a document and not what it carries — say which "
                          f"claims in this dataset rest on it, or it is apparatus and does not "
                          f"belong here")
            if _ACCESSED.match(str(entry.get("date") or "")):
                rep.error(f"source {name}",
                          f"transcribes[{i}] dates a retrieval — the document's own date is what "
                          f"places it on the ladder")

    declared_records = sum(1 for s in sources.values()
                           if isinstance(s, dict) and s.get("transcribes"))
    rep.note(f"transcription declarations: {declared_records} source(s) derive their rung from the "
             f"document they carry and {len(read_and_empty)} page(s) were read and reprint none; "
             f"{len(undeclared)} page(s) at tier "
             f"{TESTIMONY_MAX_TIER + 1} or weaker date their own retrieval and declare nothing — "
             f"unread rather than wrong, and the queue in docs/ROADMAP.md § S5"
             + (f" ({', '.join(undeclared[:4])}"
                + (f" and {len(undeclared) - 4} more)" if len(undeclared) > 4 else ")")
                if undeclared else ""))


def archetype_consumed(rep: Report | None = None) -> dict[str, frozenset]:
    """archetype name -> the form attributes whose value its generator reads.

    Declared by each `generators/archetypes/*_params.py` as `CONSUMED`, next to
    the `from_phase` that does the reading, because the two drift apart the
    moment they live in different files. Imports only the pure-Python halves, so
    this costs milliseconds and needs no Blender.

    An archetype with no params module yet returns nothing and is skipped rather
    than assumed empty: "we have not written the generator" and "the generator
    ignores everything" are different states and only one of them is a finding.
    """
    out: dict[str, frozenset] = {}
    arch_dir = ROOT / "generators" / "archetypes"
    if not arch_dir.exists():
        return out
    sys.path.insert(0, str(ROOT / "generators"))
    for mod_path in sorted(arch_dir.glob("*_params.py")):
        name = mod_path.stem.removesuffix("_params")
        try:
            mod = __import__(f"archetypes.{mod_path.stem}", fromlist=["CONSUMED"])
        except Exception as e:  # noqa: BLE001
            if rep:
                rep.error("geometry", f"cannot import {mod_path.name}: {e}")
            continue
        consumed = getattr(mod, "CONSUMED", None)
        if consumed is None:
            if rep:
                rep.error("geometry", f"{mod_path.name} declares no CONSUMED set, so nothing "
                                      f"can tell which of a {name} record's attributes reach "
                                      f"the mesh and which are stated and never built")
            continue
        out[name] = frozenset(consumed)
    return out


# What a `geometry:` declaration may say, and whether saying it is an admission
# that owes the liberties document an entry. `record_only` does not: an attribute
# that is a research note rather than a build instruction — a rejected reading, a
# negative finding — has nothing missing from the model to admit to.
GEOMETRY_STATES = ("absent", "simplified", "record_only")
GEOMETRY_OWES_LIBERTY = ("absent", "simplified")

# The ground's vocabulary is the same three plus one a record cannot need.
# `restated_in_code` is a value the mesh AGREES with and does not come from: the
# water plane is a literal zero in `terrain_gen.py` and the bank's ease-out is
# written in Python, so those spec lines describe the ground accurately while
# driving nothing. Calling that `absent` would be a lie in the visitor's
# direction and `simplified` one in the reviewer's. It owes no liberty — nothing
# is missing from the model — and what it does owe is a warning to whoever edits
# the generator, which is why the declaration says where the duplicate lives.
GROUND_GEOMETRY_STATES = GEOMETRY_STATES + ("restated_in_code",)


def unbuilt_values(structures: dict, consumed: dict[str, frozenset]) -> list[tuple]:
    """Every form attribute whose archetype does not read it.

    Returns `(structure_id, phase_id, aspect, where, attr_dict)` with `aspect` in
    the `Covers:` vocabulary — `form.<attribute>` — so an omission is claimed by
    the same grammar an invention is.

    Attributes whose value is falsy are excluded, and the exclusion is the whole
    difference between a gap and a nothing: `log_core: false` records a reading
    the project rejected, and there is no missing stable, sign or wing behind it
    to admit to. What is left is the set of things a record says the building had
    and the mesh cannot show.
    """
    found: list[tuple] = []
    for name, st in sorted(structures.items()):
        sid = st.get("id", name)
        known = consumed.get(st.get("archetype"))
        if known is None:
            continue
        for ph in st.get("phases", []):
            pid = ph.get("id", "?")
            for attr, a in sorted((ph.get("form") or {}).items()):
                if attr in known or not isinstance(a, dict):
                    continue
                found.append((sid, pid, f"form.{attr}", f"structure {sid}/{pid}", a))
    return found


def check_geometry_declarations(structures: dict, consumed: dict[str, frozenset],
                                rep: Report) -> None:
    """A record may not state something the mesh does not contain without saying so.

    The confidence model answers "how sure are we of this value". It has nothing
    to say about a value nobody builds — and the two are not the same claim at
    all. The Wolf Point Tavern's painted wolf sign is `documented`: the popup
    shows the strongest chip the project has, over a building that has no sign on
    it. That reads as a well-evidenced feature you are looking at, and it is a
    well-evidenced feature you are not.

    So the rule is mechanical and comes from the generator rather than from a
    reviewer's attention: every form attribute outside its archetype's `CONSUMED`
    set carries a `geometry:` declaration saying what the mesh does instead —
    `absent`, `simplified`, or `record_only` for something that was never a build
    instruction. The first two are omissions and simplifications, so they owe
    docs/LIBERTIES.md an entry, which `check_liberties_coverage` collects.

    The declaration is checked the other way too. Putting `geometry:` on an
    attribute the archetype *does* read is a false admission — the value drives
    the mesh by construction — and it would quietly excuse a real omission if the
    parameter were ever removed.
    """
    if not consumed:
        rep.note("geometry check: no archetype params modules to compare against")
        return
    declared = 0
    for name, st in sorted(structures.items()):
        sid = st.get("id", name)
        known = consumed.get(st.get("archetype"))
        if known is None:
            continue
        for ph in st.get("phases", []):
            pid = ph.get("id", "?")
            where = f"structure {sid}/{pid}"
            for attr, a in sorted((ph.get("form") or {}).items()):
                if not isinstance(a, dict):
                    continue
                state = a.get("geometry")
                if attr in known:
                    if state is not None:
                        rep.error(where, f"form.{attr} carries geometry: '{state}', but the "
                                         f"{st.get('archetype')} archetype reads this attribute "
                                         f"— it is built from the value, so there is nothing to "
                                         f"declare. Drop the field, or remove the attribute from "
                                         f"CONSUMED if the generator stopped using it")
                    continue
                if state is None:
                    rep.error(where, f"form.{attr} is stated by the record and the "
                                     f"{st.get('archetype')} archetype never reads it, so "
                                     f"nothing in the mesh comes from it — and the popup still "
                                     f"shows the value with a confidence chip. Declare what the "
                                     f"geometry does: geometry: 'absent' (nothing of it is "
                                     f"built), 'simplified' (a fixed default stands in its "
                                     f"place), or 'record_only' (a reading recorded, not a "
                                     f"build instruction)")
                    continue
                if state not in GEOMETRY_STATES:
                    rep.error(where, f"form.{attr} declares geometry: '{state}', which is not "
                                     f"one of {', '.join(GEOMETRY_STATES)}")
                    continue
                if state in GEOMETRY_OWES_LIBERTY and not a.get("value"):
                    rep.error(where, f"form.{attr} declares geometry: '{state}' over the value "
                                     f"{a.get('value')!r} — admitting to leaving out something "
                                     f"the record says was not there. Use 'record_only' for a "
                                     f"reading recorded rather than a thing omitted")
                    continue
                declared += 1
    rep.note(f"geometry check: {declared} attribute(s) the archetypes do not read, each "
             f"declaring what the mesh does instead")


# How far a structure's ground contact may sit off the terrain under it before
# the record has to say so. The number is not a fresh tolerance: it is the
# walker's step-up rule from renderers/web/js/walker.js — "a little over a foot,
# which is what a plank walk stands above the mud and what a person steps onto
# without thinking". The question this gate asks IS that question. Anything a
# visitor could step onto has met the ground; anything they could not has not.
GROUND_CONTACT_TOL_M = 0.35

# What a phase may say when its structure does not reach the ground. Two states,
# and the second one earned its own argument on 2026-08-11 when Fort Dearborn
# became the first structure in the dataset placed OUTSIDE the modelled terrain
# box rather than merely above it.
#
#   approach_not_modelled   — the ground exists under the structure and the
#                             structure does not reach it. The bridge's case.
#   outside_modelled_ground — there is no ground under the structure at all. The
#                             terrain epoch has not been extended that far yet,
#                             so the question "does it land" has no answer, and
#                             pretending it has one is the failure this state
#                             exists to make visible.
GROUND_CONTACT_STATES = ("approach_not_modelled", "outside_modelled_ground")


def archetype_ground_contact(rep: Report | None = None) -> dict[str, dict]:
    """archetype -> {mode, anchor}, declared beside the generator that builds it.

    `GROUND_CONTACT` is `perimeter` (the footprint outline meets the terrain at
    the base of the walls) or `ends` (only the end edges of the footprint meet
    it, at the params object's `ground_contact_z`). An archetype that declares
    nothing is skipped, not assumed — the same rule `archetype_consumed` uses,
    for the same reason.
    """
    out: dict[str, dict] = {}
    arch_dir = ROOT / "generators" / "archetypes"
    if not arch_dir.exists():
        return out
    sys.path.insert(0, str(ROOT / "generators"))
    for mod_path in sorted(arch_dir.glob("*_params.py")):
        name = mod_path.stem.removesuffix("_params")
        try:
            mod = __import__(f"archetypes.{mod_path.stem}", fromlist=["GROUND_CONTACT"])
        except Exception:  # noqa: BLE001 — archetype_consumed already reported it
            continue
        mode = getattr(mod, "GROUND_CONTACT", None)
        if mode is None:
            continue
        if mode not in ("perimeter", "ends"):
            if rep:
                rep.error("ground contact", f"{mod_path.name} declares GROUND_CONTACT "
                                            f"'{mode}', which is not perimeter or ends")
            continue
        if mode == "ends" and not callable(getattr(mod, "ground_contact_z", None)):
            if rep:
                rep.error("ground contact", f"{mod_path.name} declares GROUND_CONTACT 'ends' "
                                            f"but no ground_contact_z(params) to say at what "
                                            f"height those ends arrive")
            continue
        out[name] = {"mode": mode,
                     "anchor": getattr(mod, "VERTICAL_ANCHOR", None),
                     "contact_z": getattr(mod, "ground_contact_z", None)}
    return out


def _resample(a: tuple, b: tuple, step: float = 1.0) -> list[tuple]:
    """Points along a segment, no farther apart than `step`, ends included."""
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(math.ceil(d / step)))
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


def _contact_outline(poly: list, mode: str) -> list[tuple]:
    """The footprint edges, in local (u, v), where this archetype meets the ground.

    `perimeter` is the whole outline. `ends` is the two edges at the extremes of
    u — the span axis — which for a crossing is where the deck arrives at land
    and everything between is over water by construction.
    """
    edges = [(tuple(poly[i]), tuple(poly[(i + 1) % len(poly)])) for i in range(len(poly))]
    if mode == "perimeter":
        return edges
    us = [p[0] for p in poly]
    lo, hi = min(us), max(us)
    return [(a, b) for a, b in edges
            if (abs(a[0] - lo) < 1e-6 and abs(b[0] - lo) < 1e-6)
            or (abs(a[0] - hi) < 1e-6 and abs(b[0] - hi) < 1e-6)]


def unlanded_values(structures: dict, scenes: dict, rep: Report,
                    field=None, origin: tuple | None = None,
                    contacts: dict | None = None,
                    resolvers: dict | None = None) -> list[tuple]:
    """Every structure whose ground contact does not reach the ground.

    Returns `(structure_id, phase_id, "ground_contact", where, gap_m)`.

    The confidence model grades what a value claims; the geometry declarations
    grade whether a value was built. Neither can see a structure that WAS built,
    faithfully, onto ground that is not underneath it — because nothing in the
    record is wrong. The Wolf Point Tavern's `frame_extension` was a name the
    archetype could not find; this is the class where every name resolves and the
    result still stands in the air.

    Measured against the raw heightfield, not the renderer's walkable surface:
    `terrain.js` reports a wading barrier at +4 m over water so a walker cannot
    stroll into the river, and measuring a bridge against that barrier would be
    measuring it against a navigation rule.
    """
    found: list[tuple] = []
    if field is None or origin is None or not contacts:
        return found
    o_e, o_n = origin
    if resolvers is None:
        resolvers = {}
        sys.path.insert(0, str(ROOT / "generators"))
        for mod_path in sorted((ROOT / "generators" / "archetypes").glob("*_params.py")):
            try:
                mod = __import__(f"archetypes.{mod_path.stem}", fromlist=["from_phase"])
                resolvers[mod_path.stem.removesuffix("_params")] = mod.from_phase
            except Exception:  # noqa: BLE001 — reported by the param check
                continue

    targets = [d for d in (parse_date(sc.get("target_date", "")) for sc in scenes.values()) if d]
    for name, st in sorted(structures.items()):
        sid = st.get("id", name)
        arch = st.get("archetype")
        decl = contacts.get(arch)
        if decl is None or arch not in resolvers:
            continue
        for ph in st.get("phases", []):
            pid = ph.get("id", "?")
            r = ph.get("documented_range", {})
            frm, to = parse_date(r.get("from", "")), parse_date(r.get("to", ""))
            if not (frm and to and any(frm <= t <= to for t in targets)):
                continue
            # No mesh, no ground contact to measure: this phase's geometry is
            # drawn by another layer, which drapes on the heightfield at every
            # post rather than standing a footprint on it.
            if drawn_by_another_layer(ph):
                continue
            pos = ph.get("position") or {}
            poly = (ph.get("footprint") or {}).get("polygon")
            if not isinstance(poly, list) or len(poly) < 3:
                continue
            if pos.get("utm_e") is None or pos.get("utm_n") is None:
                continue
            try:
                params = resolvers[arch](ph)
            except Exception:  # noqa: BLE001 — reported by the param check
                continue

            e0 = float(pos["utm_e"]) - o_e
            n0 = float(pos["utm_n"]) - o_n
            th = math.radians(float(pos.get("rotation_deg") or 0.0))
            cos, sin = math.cos(th), math.sin(th)

            def to_world(p, e0=e0, n0=n0, cos=cos, sin=sin):
                u, v = float(p[0]), float(p[1])
                return (e0 + u * cos + v * sin, n0 - u * sin + v * cos)

            base_y = 0.0 if decl["anchor"] == "water" else field.height(e0, n0)
            contact_z = 0.0 if decl["mode"] == "perimeter" else float(decl["contact_z"](params))
            contact_y = base_y + contact_z

            # Is there any ground here at all? `Heightfield.height` clamps outside
            # the box, so a structure placed beyond the modelled terrain samples
            # the edge for its base AND for every contact point, the two agree
            # exactly, and the measurement below reports a perfect landing on
            # ground that does not exist. Ask the prior question first.
            outline = _contact_outline(poly, decl["mode"])
            points = [pt for a, b in outline
                      for pt in _resample(to_world(a), to_world(b))]
            if not all(field.covers(e, n) for e, n in points) or not field.covers(e0, n0):
                found.append((sid, pid, "ground_contact", f"structure {sid}/{pid}", None))
                continue

            worst = 0.0
            for e, n in points:
                gap = contact_y - field.height(e, n)
                if abs(gap) > abs(worst):
                    worst = gap
            if abs(worst) > GROUND_CONTACT_TOL_M:
                found.append((sid, pid, "ground_contact", f"structure {sid}/{pid}", worst))
    return found


def check_ground_contact(structures: dict, unlanded: list[tuple], rep: Report) -> None:
    """A structure that does not reach the ground has to say so on the record.

    Checked in both directions, like the geometry declarations: a structure that
    stands clear of the terrain and admits nothing is an unrecorded liberty, and
    a structure that admits to one while sitting flat on the ground is an
    admission to something we did not do.
    """
    gapped = {(sid, pid): gap for sid, pid, _, _, gap in unlanded}
    declared = 0
    for name, st in sorted(structures.items()):
        sid = st.get("id", name)
        for ph in st.get("phases", []):
            pid = ph.get("id", "?")
            where = f"structure {sid}/{pid}"
            block = ph.get("ground_contact")
            gap = gapped.get((sid, pid))
            if block is not None and not isinstance(block, dict):
                rep.error(where, "ground_contact must be an object with a state and a note")
                continue
            state = (block or {}).get("state")
            found = (sid, pid) in gapped
            want = "approach_not_modelled" if (found and gap is not None) \
                else "outside_modelled_ground"
            if not found:
                if block is not None:
                    rep.error(where, f"declares ground_contact: '{state}', but its contact "
                                     f"outline sits within {GROUND_CONTACT_TOL_M} m of the "
                                     f"terrain under it — it lands. Drop the declaration, or "
                                     f"move the entry claiming it to the Resolved section of "
                                     f"docs/LIBERTIES.md if the ground caught up")
                continue
            if block is None and gap is None:
                rep.error(where, "stands outside the modelled terrain box altogether — there "
                                 "is no ground under any part of its contact outline, so "
                                 "whether it lands has no answer. Declare ground_contact: "
                                 "{state: 'outside_modelled_ground', note: ...} on the phase "
                                 "and admit it in docs/LIBERTIES.md, or extend the terrain "
                                 "epoch to reach it")
                continue
            if block is None:
                rep.error(where, f"its ground contact stands {gap:+.2f} m off the terrain "
                                 f"beneath it — more than the walker's {GROUND_CONTACT_TOL_M} m "
                                 f"step-up rule, so a visitor could not step between the two. "
                                 f"Nothing in the record is wrong and nothing shows it: declare "
                                 f"ground_contact: {{state: 'approach_not_modelled', note: ...}} "
                                 f"on the phase and admit it in docs/LIBERTIES.md")
                continue
            if state in GROUND_CONTACT_STATES and state != want:
                rep.error(where, f"declares ground_contact: '{state}', but the measurement says "
                                 f"'{want}' — the two are different findings and a visitor "
                                 f"reading the first would be told the ground is there")
                continue
            if state not in GROUND_CONTACT_STATES:
                rep.error(where, f"ground_contact state '{state}' is not one of "
                                 f"{', '.join(GROUND_CONTACT_STATES)}")
                continue
            if not (block.get("note") or "").strip():
                rep.error(where, "ground_contact declares a state with no note — the note is "
                                 "where the reasoning lives, exactly as it is for an inferred "
                                 "value")
                continue
            declared += 1
    rep.note(f"ground contact: {len(gapped)} structure(s) do not reach the terrain under them, "
             f"{declared} declaring it")


# How close a recomputed placement has to land. The corner tolerance is a
# rounding allowance and nothing else: coordinates are committed to 0.1 m and
# polygons to the millimetre, so the eight corner constraints in the dataset
# reproduce to 0.02 m. The waterline tolerance is larger for a stated reason —
# a traced bank is a polyline, and where it crosses a given northing depends on
# which vertex pair you sample, so agreement to the centimetre would be luck
# rather than correctness.
PLACEMENT_TOL_M = 0.05
WATERLINE_TOL_M = 0.5


def world_footprint(phase: dict) -> list[tuple[float, float]]:
    """The footprint polygon where it actually stands, in EPSG:26916 metres.

    `rotation_deg` is a facade bearing, degrees CLOCKWISE from grid north, and
    the polygon is local ENU about the position — so a building at bearing 270
    has its recorded coordinate at what reads on paper as its south-east corner.
    Every constraint below is asked of the placed shape rather than of the
    coordinate, because "the west face stands on the Canal frontage" is a claim
    about the building and stays true when the building is rotated.
    """
    pos = phase.get("position") or {}
    poly = (phase.get("footprint") or {}).get("polygon") or []
    if pos.get("utm_e") is None or pos.get("utm_n") is None or len(poly) < 3:
        return []
    b = math.radians(float(pos.get("rotation_deg") or 0.0))
    cos, sin = math.cos(b), math.sin(b)
    e0, n0 = float(pos["utm_e"]), float(pos["utm_n"])
    return [(e0 + x * cos + y * sin, n0 - x * sin + y * cos) for x, y in poly]


def face_of(pts: list[tuple[float, float]], face: str) -> float:
    es = [p[0] for p in pts]
    ns = [p[1] for p in pts]
    return {"west": min(es), "east": max(es), "south": min(ns), "north": max(ns)}[face]


# The building's own four walls, named as docs/GLB-CONTRACT.md names the footprint
# axes: polygon `u` runs right along the front and `v` runs back from it, so the wall
# a facade bearing points out of is the max-`v` one. `face_of` above answers a
# different question — where a placed shape's most-westerly point lands on the grid —
# and the two are the same wall only when the building is square to the grid.
FOOTPRINT_FACES = {"front": (1, max), "back": (1, min),
                   "right": (0, max), "left": (0, min)}


def footprint_face(phase: dict, face: str) -> tuple[tuple[float, float],
                                                    tuple[float, float]] | None:
    """The midpoint and outward normal of one named wall, in EPSG:26916 metres.

    The same composition `world_footprint` makes, asked of one edge rather than the
    whole ring, because a frontage is a claim about a WALL: "this house's front
    stands 12.19 m off North Water Street" stays true when the house is rotated and
    is not a claim about the polygon's westmost corner. The normal is the direction
    that wall faces, which is what tells a frontage from a back yard.
    """
    pos = phase.get("position") or {}
    poly = (phase.get("footprint") or {}).get("polygon") or []
    if pos.get("utm_e") is None or pos.get("utm_n") is None or len(poly) < 3:
        return None
    axis, pick = FOOTPRINT_FACES[face]
    other = 1 - axis
    extreme = pick(p[axis] for p in poly)
    on = [p for p in poly if abs(p[axis] - extreme) < 1e-6]
    if len(on) < 2:
        return None
    mid = (min(p[other] for p in on) + max(p[other] for p in on)) / 2.0
    u, v = (extreme, mid) if axis == 0 else (mid, extreme)
    b = math.radians(float(pos.get("rotation_deg") or 0.0))
    cos, sin = math.cos(b), math.sin(b)
    point = (float(pos["utm_e"]) + u * cos + v * sin,
             float(pos["utm_n"]) - u * sin + v * cos)
    normal = {"front": (sin, cos), "back": (-sin, -cos),
              "right": (cos, -sin), "left": (-cos, sin)}[face]
    return point, normal


def nearest_on_path(pt: tuple[float, float],
                    path: list[tuple[float, float]]) -> tuple[float, tuple[float, float]]:
    """(distance, foot) from a point to an open polyline, in metres.

    Character for character the arithmetic in
    `tools/generate_business_signboards.py::_nearest_on_path`, which has decided
    which street a signboard faces since T-0459. It was a generator's private
    helper and is now also a gate; the recipe did not change, only what may lean
    on it.
    """
    x, y = pt
    best = (float("inf"), (x, y))
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        fx, fy = x1 + t * dx, y1 + t * dy
        d = math.hypot(x - fx, y - fy)
        if d < best[0]:
            best = (d, (fx, fy))
    return best


def committed_street_paths(base: Path, rep: Report) -> dict:
    """`data/streets/1835.json`'s centrelines, reprojected to EPSG:26916.

    The street records are stored in local ENU metres from `data/datum.json`'s
    origin and the placements are stored in UTM; the offset between them is a
    translation and nothing else, so this adds it once here rather than in every
    caller. A missing datum or streets file is an error the caller reports against
    the placement that asked for it.
    """
    datum = load_json(base / "datum.json", rep, required=False)
    doc = load_json(base / "streets" / "1835.json", rep, required=False)
    if not isinstance(datum, dict) or not isinstance(doc, dict):
        return {}
    e0, n0 = datum.get("origin_utm_e"), datum.get("origin_utm_n")
    if e0 is None or n0 is None:
        return {}
    out: dict = {}
    for st in doc.get("streets") or []:
        path = [(float(e0) + float(p[0]), float(n0) + float(p[1]))
                for p in st.get("path_local_enu_m") or []]
        out[st.get("id")] = {"name": st.get("name_1835") or st.get("id"), "path": path}
    return out


def waterline_crossings(epoch_dir: Path, northing: float, rep: Report,
                        where: str) -> list[float]:
    """Eastings where the traced water boundary crosses a northing."""
    doc = load_json(epoch_dir / "river.geojson", rep, required=False)
    if not isinstance(doc, dict):
        rep.error(where, f"no traced river at {epoch_dir.name} to meet")
        return []
    # The forks window is not the whole river. `branches.geojson` carries the
    # reaches traced OUTSIDE it — today the South Branch from the forks window's
    # south edge to the School Section's south line (T-1071) — and a face that
    # ends on the water down there meets a bank that lives in that file and
    # nowhere else. It is optional: an epoch may have no branches traced yet.
    docs = [doc]
    more = load_json(epoch_dir / "branches.geojson", rep, required=False)
    if isinstance(more, dict):
        docs.append(more)
    out: list[float] = []
    for ft in [f for d in docs for f in d.get("features", [])]:
        geom = ft.get("geometry") or {}
        if geom.get("type") != "Polygon":
            continue
        for ring in geom.get("coordinates", []):
            for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
                if y1 != y2 and (y1 - northing) * (y2 - northing) <= 0:
                    out.append(x1 + (northing - y1) / (y2 - y1) * (x2 - x1))
    return out


def check_position_derivations(structures: dict, source_ids: set, rep: Report,
                               data_root: Path | None = None) -> None:
    """Every placement says how it was arrived at, and the checkable ones are recomputed.

    Five of the nine placements in this dataset are the same construction: read
    a modern intersection centre off OpenStreetMap, step half a platted street
    to the kerb, and stand a named face on it. That construction was written out
    in prose once per building — the same sentence, the same 12.2 m, five sums
    done by hand — and nothing recomputed any of it. Two consequences, and the
    second is the reason this exists rather than the first:

    - A transcription slip in any of those sums is invisible. The numbers happen
      to be right; nothing was making them right.
    - **The module could not be changed.** `data/traces/street_control.json`
      records a live disagreement about the platted street width (80 ft
      annotated on Hathaway 1834, against Currey's 66 ft) whose consequence is
      2.13 m on every offset. Settling it against five paragraphs means five
      hand-redone sums and a reviewer with a calculator; settling it against one
      figure and this check means editing one number and reading which buildings
      moved.

    The rule runs in both directions, which is what stops the file going quietly
    out of date: a phase with coordinates and no `derivation` is an error, and a
    derivation naming control, a street, a kerb or an epoch that does not
    resolve is an error too. A placement no line in the dataset can check
    declares `not_derivable` and owes a reason — three of the nine do, and their
    reasons are the honest ones: no surviving street here, a position stacked on
    another inferred position, an interpolation plus a free 40 m.

    THE THREE METHODS, AND WHAT EACH RE-DERIVES.

    - `platted_corner` — `control` names a junction in the control table and each
      constraint names a `street`, a `kerb` and the `face` of the placed footprint
      that stands on it. Re-derived: that face's grid coordinate against the control
      stepped half a platted module (plus any `offset_m`) out to the named kerb.
      Requires the street to have an `ew`/`ns` axis, because a kerb is found by
      stepping along one.

    - `traced_waterline` — `centreline` gives the axis and any declared variance from
      control, `ends` the epoch and the faces that must land on it. Re-derived: the
      variance, and that each named end meets the traced waterline.

    - `street_frontage` (T-0946) — `frontage` names a `street` id in
      `data/streets/1835.json`, the `face` of the building's own four walls that
      stands on it, and the `setback_m` of that wall from the street's committed
      centreline. Re-derived: the perpendicular distance from that wall's midpoint
      to the nearest point on the committed path, to PLACEMENT_TOL_M, AND that the
      street lies on the side the wall faces rather than behind it. This is the
      method for a street that is not square to the grid, which is most of the north
      bank: `north_water` is a derived offset curve from the traced bank (T-0307,
      T-0447) running 41.4° east of north, so it has no axis to step a kerb along
      and no control point can be hung on it. Before this method the whole bank
      declared `not_derivable` — not because the readings were loose but because the
      vocabulary had no term for them, and a placement nothing re-computes is a
      placement two runs can land 36 m apart without either noticing (T-0947).
    """
    base = data_root or DATA
    doc = load_json(base / "traces" / "street_control.json", rep, required=False)
    if not isinstance(doc, dict):
        rep.error("street control", "data/traces/street_control.json is missing or unreadable — "
                                    "the placements cannot be recomputed without it")
        return

    module = doc.get("platted_street") or {}
    half = module.get("half_width_m")
    if not isinstance(half, (int, float)) or half <= 0:
        rep.error("street control", "platted_street.half_width_m is missing or not a length")
        return
    if module.get("confidence") not in CONFIDENCE:
        rep.error("street control", "the platted street width carries no confidence, and every "
                                    "figure this dataset stands on is graded")
    if module.get("confidence") != "attested" and not (module.get("note") or "").strip():
        rep.error("street control", "the street width is not documented and states no reasoning")
    for key, node in (("platted_street", module), ("platted_street.dissent", module.get("dissent") or {})):
        for s in node.get("sources") or []:
            if s not in source_ids:
                rep.error("street control", f"{key} cites '{s}', which does not resolve in data/sources/")

    streets = doc.get("streets") or {}
    for sid, st in streets.items():
        if st.get("axis") not in ("ew", "ns"):
            rep.error("street control", f"street '{sid}' has no axis; a kerb cannot be found "
                                        f"without knowing which way the street runs")

    control = doc.get("control") or {}
    for cid, c in control.items():
        for sid in c.get("streets") or []:
            if sid not in streets:
                rep.error("street control", f"control '{cid}' names street '{sid}', which is not "
                                            f"in the streets table")
        if c.get("utm_e") is None or c.get("utm_n") is None:
            rep.error("street control", f"control '{cid}' has no coordinate")
        if not c.get("osm_node_ids") and not (c.get("gap") or "").strip():
            rep.error("street control", f"control '{cid}' records no OpenStreetMap node ids and "
                                        f"no `gap` saying so — data/sources/osm_streets_2026.json "
                                        f"promises the ids are recorded, and a control point that "
                                        f"cannot be re-fetched has to say it cannot")
        # Ids alone are not re-derivability. A list of node ids says which nodes
        # were averaged; it does not say what junction they are, so nobody can
        # tell whether the SET is right — and a wrong set is exactly the fault
        # that cost this dataset two coordinates (a substring name query pulling
        # a bikeway's crossings in beside the roadway's, 2026-08-10). The names
        # make the set re-derivable rather than merely re-fetchable, which is the
        # difference between checking the number and checking the reading.
        if c.get("osm_node_ids"):
            ways = c.get("osm_ways") or []
            if len(ways) != 2 or not all(isinstance(w, str) and w.strip() for w in ways):
                rep.error("street control", f"control '{cid}' records node ids but not the two "
                                            f"modern street names in `osm_ways` that make the "
                                            f"junction — without them the node SET cannot be "
                                            f"re-derived, only re-fetched, and a set with the "
                                            f"wrong nodes in it re-fetches perfectly")
            if c.get("lat") is None or c.get("lon") is None:
                rep.error("street control", f"control '{cid}' records node ids and no lat/lon — "
                                            f"the re-fetch reads WGS84 and the comparison would "
                                            f"have to reproject the answer it is checking")

    checked = declared = 0
    streets_utm: dict | None = None
    for name, st in sorted(structures.items()):
        sid = st.get("id", name)
        for ph in st.get("phases", []):
            pos = ph.get("position") or {}
            where = f"structure {sid}/{ph.get('id', '?')}"
            der = pos.get("derivation")
            if pos.get("utm_e") is None:
                if der:
                    rep.error(where, "declares a derivation and has no coordinates to derive")
                continue
            if not der:
                rep.error(where, "has coordinates and no `position.derivation` — how a placement "
                                 "was arrived at is part of the claim, and a placement that "
                                 "nothing can recompute has to say so rather than say nothing")
                continue
            declared += 1
            method = der.get("method")

            if method == "not_derivable":
                if not (der.get("reason") or "").strip():
                    rep.error(where, "not_derivable without a reason — that is an undeclared "
                                     "placement with a label on it")
                for k in ("control", "constraints", "centreline", "ends", "frontage"):
                    if der.get(k):
                        rep.error(where, f"not_derivable but carries `{k}`")
                continue

            if method == "street_frontage":
                fr = der.get("frontage") or {}
                if streets_utm is None:
                    streets_utm = committed_street_paths(base, rep)
                st_rec = streets_utm.get(fr.get("street") or "")
                if not st_rec:
                    rep.error(where, f"fronts street '{fr.get('street')}', which is not a "
                                     f"record in data/streets/1835.json")
                    continue
                if len(st_rec["path"]) < 2:
                    rep.error(where, f"fronts '{fr.get('street')}', whose committed record "
                                     f"carries no path to stand off")
                    continue
                face = fr.get("face")
                if face not in FOOTPRINT_FACES:
                    rep.error(where, f"names face '{face}', which is not one of the "
                                     f"building's four walls")
                    continue
                setback = fr.get("setback_m")
                if not isinstance(setback, (int, float)) or setback < 0:
                    rep.error(where, "declares a frontage and no setback from the committed "
                                     "centreline, which is the whole of the claim")
                    continue
                placed = footprint_face(ph, face)
                if placed is None:
                    rep.error(where, f"has no footprint edge at its {face} to stand on a "
                                     f"frontage")
                    continue
                (px, pn), normal = placed
                got, foot = nearest_on_path((px, pn), st_rec["path"])
                # A back yard can be as close to a street as a front wall is, so the
                # distance alone does not say "frontage". The street has to lie on the
                # side the wall faces — the same test the signboard layer makes before
                # it will stand a post out in front of a wall.
                if (foot[0] - px) * normal[0] + (foot[1] - pn) * normal[1] <= 0:
                    rep.error(where, f"declares its {face} wall on {st_rec['name']}, and "
                                     f"that street lies behind the wall rather than in "
                                     f"front of it — that is a back, not a frontage")
                elif abs(got - float(setback)) > PLACEMENT_TOL_M:
                    rep.error(where, f"its {face} wall stands {got:.2f} m from "
                                     f"{st_rec['name']}'s committed centreline and declares "
                                     f"{float(setback):.2f} ({got - float(setback):+.2f} m)")
                else:
                    checked += 1
                continue

            cid = der.get("control")
            c = control.get(cid or "")
            if not c:
                rep.error(where, f"control '{cid}' does not resolve in "
                                 f"data/traces/street_control.json")
                continue
            pts = world_footprint(ph)
            if not pts:
                rep.error(where, "has coordinates but no footprint polygon to stand on a frontage")
                continue

            if method == "platted_corner":
                cons = der.get("constraints") or []
                if not cons:
                    rep.error(where, "platted_corner with no constraints")
                for con in cons:
                    street = streets.get(con.get("street") or "")
                    if not street:
                        rep.error(where, f"names street '{con.get('street')}', not in the "
                                         f"streets table")
                        continue
                    if con.get("street") not in (c.get("streets") or []):
                        rep.error(where, f"stands on '{con.get('street')}' but its control "
                                         f"'{cid}' is not on that street")
                        continue
                    kerb, axis = con.get("kerb"), street["axis"]
                    if (axis == "ns") != (kerb in ("east", "west")):
                        rep.error(where, f"a {axis} street has no {kerb} kerb")
                        continue
                    outward = 1.0 if kerb in ("east", "north") else -1.0
                    centre = c["utm_e"] if axis == "ns" else c["utm_n"]
                    want = centre + outward * (half + float(con.get("offset_m") or 0.0))
                    got = face_of(pts, con["face"])
                    if abs(got - want) > PLACEMENT_TOL_M:
                        rep.error(where, f"the {con['face']} face stands at {got:.2f} and the "
                                         f"{kerb} frontage of {con['street']} is at {want:.2f} "
                                         f"({got - want:+.2f} m)")
                    else:
                        checked += 1

            elif method == "traced_waterline":
                cl = der.get("centreline") or {}
                ends = der.get("ends") or {}
                axis = cl.get("axis")
                if axis in ("e", "n"):
                    lo = face_of(pts, "west" if axis == "e" else "south")
                    hi = face_of(pts, "east" if axis == "e" else "north")
                    mid = (lo + hi) / 2.0
                    centre = c["utm_e"] if axis == "e" else c["utm_n"]
                    var = float(cl.get("control_variance_m") or 0.0)
                    if var and not (der.get("note") or "").strip():
                        rep.error(where, "declares a variance from its control and explains it "
                                         "nowhere — a stated offset with no reason is the thing "
                                         "this check exists to stop being written")
                    if abs(abs(centre - mid) - abs(var)) > PLACEMENT_TOL_M:
                        rep.error(where, f"sits {centre - mid:+.2f} m from control '{cid}' on the "
                                         f"{axis} axis and declares {var:+.2f}")
                    else:
                        checked += 1
                epoch_dir = base / "terrain" / "epochs" / (ends.get("epoch") or "")
                if not epoch_dir.is_dir():
                    rep.error(where, f"ends on epoch '{ends.get('epoch')}', which is not committed")
                    continue
                mid_n = (face_of(pts, "south") + face_of(pts, "north")) / 2.0
                xs = waterline_crossings(epoch_dir, mid_n, rep, where)
                for f in ends.get("faces") or []:
                    got = face_of(pts, f)
                    near = min((abs(got - x) for x in xs), default=None)
                    if near is None or near > WATERLINE_TOL_M:
                        rep.error(where, f"its {f} end stands at {got:.2f} and meets no traced "
                                         f"{ends.get('epoch')} waterline there"
                                         + (f" (nearest {near:.2f} m)" if near is not None else ""))
                    else:
                        checked += 1
            else:
                rep.error(where, f"unknown derivation method '{method}'")

    rep.note(f"placement derivations: {declared} declared, {checked} constraint(s) recomputed "
             f"from data/traces/street_control.json and data/streets/1835.json")


def check_drawn_by(structures: dict, rep: Report) -> None:
    """A phase whose geometry moved to another layer has to have moved it.

    `drawn_by` is the record saying: nothing bakes this phase, and what a visitor
    sees is built at load by another layer out of another file. It exists because
    Chicago's first public building is a fence — Andreas calls the estray pen "a
    small wooden enclosure and quite roofless" — and the only archetype that would
    build a low walled rectangle cannot build a roofless one, so for a week the
    town's pound stood with an invented shed roof on it (docs/LIBERTIES.md L60).

    The declaration is cheap to write and would be easy to leave half-done, so
    every half is asserted here rather than trusted:

      * the named record EXISTS and names this structure back, so the phase cannot
        point at a file nobody wrote;
      * the layer's own manifest LISTS it — a record the index does not name is
        fetched by nothing, and the pen would silently vanish from the town;
      * NO GLB and NO manifest entry survive the move, which is the assertion that
        actually retires the roof: a phase that still has a baked mesh is still
        drawing one, whatever the record says about it;
      * `form` is EMPTY, because every value in it was a build instruction for the
        mesh that just went away. A retired invention left sitting in the record
        would keep showing on the card with a confidence chip and no geometry
        behind it, which is the exact failure check_geometry_declarations exists
        to stop one level up.
    """
    checked = 0
    for name, st in sorted(structures.items()):
        sid = st.get("id", name)
        for ph in st.get("phases", []):
            decl = ph.get("drawn_by")
            if not drawn_by_another_layer(ph):
                continue
            pid = ph.get("id", "?")
            where = f"structure {sid}/{pid}"
            checked += 1

            if ph.get("form"):
                rep.error(where, f"declares drawn_by {decl.get('layer')!r} but still carries "
                                 f"form attributes ({', '.join(sorted(ph['form']))}) — nothing "
                                 f"builds them now, so they are values on a card with no "
                                 f"geometry behind them. Retire them, or drop drawn_by")

            rel = decl.get("record", "")
            path = ROOT / rel
            if not rel or not path.exists():
                rep.error(where, f"declares drawn_by record {rel!r}, which is not a file in "
                                 f"this repository — the geometry moved to nowhere")
                continue
            try:
                rec = json.loads(path.read_text())
            except Exception as e:  # noqa: BLE001 — an unreadable layer record is a failure
                rep.error(where, f"drawn_by record {rel} does not parse: {e}")
                continue
            if rec.get("structure_id") != sid:
                rep.error(where, f"drawn_by record {rel} names structure_id "
                                 f"{rec.get('structure_id')!r} — the two records disagree about "
                                 f"which building this geometry belongs to")

            index_path = path.parent / "index.json"
            try:
                listed = {e.get("id") for e in
                          json.loads(index_path.read_text()).get("enclosures", [])}
            except Exception as e:  # noqa: BLE001
                rep.error(where, f"cannot read {index_path.relative_to(ROOT)}: {e}")
                listed = set()
            if rec.get("id") not in listed:
                rep.error(where, f"drawn_by record {rel} is not listed in "
                                 f"{index_path.relative_to(ROOT)} — a static host cannot be "
                                 f"globbed, so nothing fetches it and the phase draws nothing "
                                 f"at all")

            glb = f"{sid}__{pid}.glb"
            if (ROOT / "assets" / "gltf" / glb).exists():
                rep.error(where, f"declares drawn_by but assets/gltf/{glb} is still committed — "
                                 f"the mesh this record says it no longer has is still in the "
                                 f"repository and still shipped")
            manifest_path = ROOT / "assets" / "manifest.json"
            if manifest_path.exists():
                try:
                    entries = json.loads(manifest_path.read_text()).get("assets", {})
                except Exception:  # noqa: BLE001 — reported by the stale check
                    entries = {}
                if glb in entries:
                    rep.error(where, f"declares drawn_by but assets/manifest.json still lists "
                                     f"{glb} — the bake would rebuild it on the next run")
    if checked:
        rep.note(f"drawn_by check: {checked} phase(s) drawn by another layer, each with a "
                 f"record that exists, is fetched, and has no mesh left behind it")


def check_liberties_coverage(structures: dict, liberties: dict, rep: Report,
                             consumed: dict[str, frozenset] | None = None,
                             unlanded: list[tuple] | None = None,
                             ground: dict[str, dict[str, dict]] | None = None,
                             ground_consumed: dict[str, frozenset] | None = None) -> None:
    """Every inferred value in a record must be CLAIMED in LIBERTIES.md.

    This is the inverse of the check the walkthrough already makes. The panel and
    the provenance card report the liberties that were *recorded* — which is not
    the claim that everything taken was written down, and the project's standard
    is that a visitor can tell you which parts we made up. An inferred footprint
    is not merely an unknown: the polygon gets drawn, the building stands on it,
    and the visitor sees one specific shape. That is an invention, and an
    invention nobody wrote down is exactly the gap the standard is about.

    The same argument runs past the drawn geometry, which is why the requirement
    now covers every attested value in the record. An inferred `roof_type` is
    not an absence in the model: a gable gets built, and the visitor sees a gable.
    An inferred `gallery: false` is the same claim in the negative — the front
    of the building is rendered plain because nobody found evidence either way,
    and *that* is a decision a visitor cannot recover from a dithered tint. The
    confidence chip says "we do not know"; only the liberty says what we did about
    not knowing.

    So the confidence value drives the requirement, mechanically: mark anything
    inferred and the gate demands an entry whose `Covers:` field names that
    structure and that aspect. The claim is DECLARED, not inferred from the
    entry's wording. Reading the prose — the earlier rule — meant a liberty could
    discharge a footprint by mentioning the word while discussing a gallery, which
    is a coverage check that can be satisfied by an accident of phrasing.

    The claims are checked the other way too. A `Covers:` token that names no such
    structure, no such phase, or an attribute that is not inferred is an
    over-claim: the document says it admitted to something it did not, and that
    reads as diligence while providing none. Entries under **Resolved** are exempt
    from the last of those, because an append-only document has to be able to say
    "evidence settled this" without the settlement itself becoming a gate failure.

    **And the ground answers to all of it too.** Every paragraph above is about a
    building, because the check read `data/structures/` and nothing else. The
    terrain invents on the same terms and at a larger scale — a 6 m bank face
    nobody recorded, on every bank in the box, which is the piece of ground every
    visitor walks down to the water on — and none of that was demanded by a
    check: L32 and L33 were written by a person who noticed. A liberty owed by
    somebody's attention is precisely the arrangement this gate exists to
    replace. Ground claims are enumerated by the same function that puts them on
    the Evidence panel and claimed in a namespace of their own,
    `terrain.<epoch>.<claim>`, because the terrain is not a structure and the one
    document whose subject is honesty should not have to call it one.
    """
    entries = liberties.get("liberties") if isinstance(liberties, dict) else None
    if not entries:
        rep.error("liberties", "data/liberties.json holds no entries, so the values "
                               "invented in data/structures/ cannot be checked against "
                               "docs/LIBERTIES.md — run tools/compile_liberties.py")
        return

    # (structure, phase|None, aspect) -> the entries claiming it, and the ground's
    # (epoch, claim) beside it. Two dicts rather than one keyspace with a marker
    # in it: the two domains are checked against different documents and fail for
    # different reasons, and a shared key would only make that harder to read.
    claims: dict[tuple, list[dict]] = {}
    ground_claims_made: dict[tuple, list[dict]] = {}
    for e in entries:
        for c in e.get("covers") or []:
            if c.get("domain") == "terrain":
                ground_claims_made.setdefault((c.get("epoch"), c.get("claim")), []).append(e)
                continue
            key = (c.get("structure"), c.get("phase"), c.get("aspect"))
            claims.setdefault(key, []).append(e)

    by_subject: dict[str, list[dict]] = {}
    for e in entries:
        for sid in e.get("subjects") or []:
            by_subject.setdefault(sid, []).append(e)

    # Two kinds of thing owe the document an entry, and they are opposites: a
    # value invented to fill a gap, and a value we have but did not build.
    owed: list[tuple] = [(sid, pid, aspect, where, "invented")
                         for sid, pid, aspect, where in inferred_values(structures)]
    for sid, pid, aspect, where, attr in unbuilt_values(structures, consumed or {}):
        state = attr.get("geometry")
        if state in GEOMETRY_OWES_LIBERTY and attr.get("value"):
            owed.append((sid, pid, aspect, where, state))
    # And a third: a structure built faithfully onto ground that is not under it.
    for sid, pid, aspect, where, _gap in (unlanded or []):
        owed.append((sid, pid, aspect, where, "unlanded"))

    covered = 0
    invented = omitted = unlanded_n = ground_n = 0
    honoured: set[tuple] = set()
    # A class token (`recon_*.*.form.*`) stands in for a structure id, a phase id
    # or the attribute after `form.` — see compile_liberties.WILDCARD for why it
    # exists and how far it is allowed to reach. Expanding the key list here
    # rather than the claim list keeps the register's own tokens literal: the
    # document still says what it admits, and only the MATCH is widened.
    def class_keys(s: str, p: str | None, a: str) -> list[tuple]:
        stems = [s] + [s[:i] + "*" for i in range(1, len(s) + 1)] + ["*"]
        phases = [p, None, "*"]
        aspects = [a] + (["form.*"] if a.startswith("form.") else [])
        return [(st, ph, asp) for st in stems for ph in phases for asp in aspects]

    for sid, pid, aspect, where, kind in owed:
        keys = [(sid, pid, aspect), (sid, None, aspect)]
        hit = [k for k in keys if k in claims]
        if not hit:
            hit = [k for k in class_keys(sid, pid, aspect) if k in claims]
        if hit:
            covered += 1
            invented += kind == "invented"
            unlanded_n += kind == "unlanded"
            omitted += kind not in ("invented", "unlanded")
            honoured.update(hit)
            continue
        named = ", ".join(e.get("id", "?") for e in by_subject.get(sid, [])) or "none"
        token = ".".join(t for t in (sid, pid, aspect) if t)
        if kind == "invented":
            # A drawn shape and a stated attribute are invented in different ways, and
            # the message says which one the reader is looking at.
            what = (f"a drawn {aspect}" if aspect in ("footprint", "position")
                    else "a stated " + re.sub(r"\bm\b", "(m)",
                                              aspect.split(".")[-1].replace("_", " ")))
            why = (f"{aspect} is inferred but no liberty in docs/LIBERTIES.md "
                   f"claims it — {what} nobody can defend is something we made up")
        elif kind == "unlanded":
            why = ("this structure does not reach the ground it stands over and no "
                   "liberty in docs/LIBERTIES.md claims it — the record is right, the "
                   "mesh is right, and the model still shows a thing arriving nowhere")
        else:
            why = (f"{aspect} declares geometry: '{kind}' but no liberty in "
                   f"docs/LIBERTIES.md claims it — the record states something the "
                   f"model does not show, which a confidence chip cannot say and a "
                   f"visitor cannot see")
        rep.error(where,
                  f"{why}, and the standard is that a visitor can tell you which parts. "
                  f"Append the liberty with '**Covers:** `{token}`' and re-run "
                  f"tools/compile_liberties.py (liberties naming {sid}: {named})")

    # The ground, on the same terms. Its claims are blocks of a spec rather than
    # attributes of a record, so they are matched by id and not by aspect — but
    # the requirement is the identical one, and so is the argument for it.
    ground = ground or {}
    ground_honoured: set[tuple] = set()
    ground_owed = [(e, c, lab, w, "invented")
                   for e, c, lab, w in terrain_inferred_values(ground)]
    # And the ground's omissions, on the same terms as a building's. The claim is
    # per FIELD and the admission is per CLAIM, because `terrain.<epoch>.<claim>`
    # is the vocabulary the document already writes in and a soil profile is not
    # separably admittable from the block that states it. The mismatch is the
    # block-level grading this panel already carries, one level down: the note is
    # where a reader learns which figure is the unbuilt one.
    seen_omitted: set[tuple] = set()
    for epoch, cid, key, state, where in unbuilt_ground_values(
            ground, ground_consumed if ground_consumed is not None else terrain_consumed()):
        if state not in GEOMETRY_OWES_LIBERTY or (epoch, cid) in seen_omitted:
            continue
        seen_omitted.add((epoch, cid))
        label = (ground.get(epoch, {}).get(cid, {}) or {}).get("label") or cid
        ground_owed.append((epoch, cid, label, where, state))
    for epoch, cid, label, where, kind in ground_owed:
        key = (epoch, cid)
        if key in ground_claims_made:
            covered += 1
            ground_n += 1
            ground_honoured.add(key)
            continue
        if kind == "invented":
            why = (f"'{label}' is inferred and no liberty in docs/LIBERTIES.md claims "
                   f"it — the ground invents as freely as a record does, a visitor walks "
                   f"on the result")
        else:
            why = (f"'{label}' states a figure the ground does not contain "
                   f"(mesh: '{kind}') and no liberty in docs/LIBERTIES.md claims it — "
                   f"the panel shows the claim with a confidence chip over it and nothing "
                   f"tells a visitor there is no vertex behind it")
        rep.error(where,
                  f"{why}, and the standard is that they can tell you which parts. "
                  f"Append the liberty with '**Covers:** `terrain.{epoch}.{cid}`' and "
                  f"re-run tools/compile_liberties.py")

    for (epoch, cid), owners in sorted(ground_claims_made.items(), key=lambda kv: str(kv[0])):
        who = ", ".join(e.get("id", "?") for e in owners)
        if epoch not in ground:
            rep.error("liberties", f"{who} claims to cover 'terrain.{epoch}.{cid}' but no "
                                   f"terrain epoch '{epoch}' is committed — an admission "
                                   f"about ground that does not exist")
            continue
        if cid not in ground[epoch]:
            rep.error("liberties", f"{who} claims to cover 'terrain.{epoch}.{cid}' but that "
                                   f"epoch's spec makes no graded claim '{cid}' — the claims "
                                   f"are the ones the Evidence panel shows, so a token "
                                   f"naming none of them admits to nothing a visitor reads")
            continue
        if (epoch, cid) in ground_honoured:
            continue
        if all((e.get("section") or "") == "resolved" for e in owners):
            continue
        rep.error("liberties", f"{who} claims to cover 'terrain.{epoch}.{cid}', but that "
                               f"ground claim is neither inferred nor stating a figure "
                               f"declared absent or simplified — either evidence arrived "
                               f"and the spec caught up, or the ground was built and the "
                               f"declaration dropped, in which case move the entry to the "
                               f"Resolved section of docs/LIBERTIES.md; or the claim was "
                               f"never true. An admission to something we did not do reads "
                               f"as diligence and provides none")

    # The claims answer for themselves.
    for (csid, cpid, aspect), owners in sorted(claims.items(), key=lambda kv: str(kv[0])):
        who = ", ".join(e.get("id", "?") for e in owners)

        # A CLASS token answers differently. `recon_*.*.form.*` does not name a
        # record, so "no structure has this id" is the wrong question; the right
        # one is whether the class is empty. An admission covering a class that
        # matches nothing is exactly as hollow as one naming a building that was
        # never built, and fails for the same reason — but a class that matches
        # 158 roofs has discharged its obligation 158 times over, and the forward
        # pass above has already recorded that.
        if "*" in csid or cpid == "*" or aspect.endswith(".*"):
            stem = csid.rstrip("*")
            matched = [s for s in structures.values()
                       if str(s.get("id", "")).startswith(stem)] if csid != "*" else list(
                           structures.values())
            if not matched:
                rep.error("liberties", f"{who} claims to cover the class '{csid}.{aspect}' "
                                       f"but no structure id begins '{stem}' — an admission "
                                       f"about a class with nothing in it")
            continue

        st = next((s for s in structures.values() if s.get("id") == csid), None)
        if st is None:
            rep.error("liberties", f"{who} claims to cover '{csid}.{aspect}' but no structure "
                                   f"record has id '{csid}' — a liberty admitting to an "
                                   f"invention in a building that does not exist")
            continue
        if cpid is not None and cpid not in [p.get("id") for p in st.get("phases", [])]:
            rep.error("liberties", f"{who} claims to cover '{csid}.{cpid}.{aspect}' but "
                                   f"'{csid}' has no phase '{cpid}'")
            continue
        if (csid, cpid, aspect) in honoured:
            continue
        if all((e.get("section") or "") == "resolved" for e in owners):
            continue
        rep.error("liberties", f"{who} claims to cover '{csid}"
                               f"{'.' + cpid if cpid else ''}.{aspect}', but that value is "
                               f"neither inferred, nor declared absent or simplified, nor "
                               f"standing off the ground — either "
                               f"the evidence arrived and the model caught up, in which case "
                               f"move the entry to the Resolved section of docs/LIBERTIES.md, or "
                               f"the claim was never true. An admission to something we did not "
                               f"do reads as diligence and provides none")

    rep.note(f"liberties coverage: {covered} value(s) owed an admission — {invented} invented, "
             f"{omitted} stated and not built, {unlanded_n} standing off the ground, "
             f"{ground_n} invented in the ground itself — claimed by "
             f"{len(honoured) + len(ground_honoured)} declaration(s) in docs/LIBERTIES.md")


# --------------------------------------------------------------------------
# the sidecar interface
# --------------------------------------------------------------------------
#
# `tools/compile_scene.py` writes the sidecars and the renderer reads them, and
# until now nothing stated what passes between them. That is not a hypothetical
# gap: `popup.js` read `sidecar.documented_range` from the day the card was
# written and the compiler never emitted it, so the one line answering *was this
# building here on 1 July 1835* rendered as nothing for the life of the project
# (STATUS § 28). Every existing gate was silent, and correctly so — each half was
# consistent with itself, `--check` proves only that the compiler agrees with its
# own output, and the record validated clean.
#
# So the interface is derived from both sides and compared. What the compiler
# emits is read off the committed sidecars, which `compile_scene.py --check`
# proves are exactly what the dataset compiles to; what the renderer reads is
# scanned out of the renderer's own source. A field read on one side and absent
# on the other is an error.

# `record.sidecar`, or the bare `sidecar` the loader binds when it fetches one.
SIDECAR_ROOT = r"(?:\brecord\b\s*\??\.\s*)?\bsidecar\b"
JS_IDENT = r"[A-Za-z_$][\w$]*"
JS_CHAIN = r"((?:\s*\??\.\s*[A-Za-z_$][\w$]*)*)"


def sidecar_shape() -> dict:
    """The shape of a per-structure sidecar, unioned over every committed one.

    A union rather than one file because a field is part of the interface even
    when only one structure carries it — `aka` is empty on most records and the
    card still reads it. The set is taken from each scene's `index.json` rather
    than from every file in the directory, because the other derived documents —
    `exclusions.json`, `terrain.json` — have their own readers and their own
    shapes, and a name-exclusion list stops being right the moment somebody
    compiles a third one. This gate covers the record the popup, the walker and
    the placement code all read.

    Dict values recurse; anything else becomes a leaf. Resolution stops at a
    leaf, which is what keeps `aka.length` and `polygon.map` from being read as
    missing fields of a list.
    """
    def merge(shape: dict, doc: dict) -> dict:
        for k, v in doc.items():
            if isinstance(v, dict):
                prev = shape.get(k)
                shape[k] = merge(prev if isinstance(prev, dict) else {}, v)
            else:
                shape.setdefault(k, None)
        return shape

    shape: dict = {}
    for index in sorted((DATA / "sidecars").glob("*/index.json")):
        listed = json.loads(index.read_text()).get("structures", [])
        for entry in listed:
            p = DATA / entry.get("sidecar", "")
            if not p.is_file():
                continue
            doc = json.loads(p.read_text())
            if isinstance(doc, dict):
                merge(shape, doc)
    return shape


def strip_js_comments(text: str) -> str:
    """Comments out, line numbers intact.

    Not cosmetic: this file's modules explain their own history in prose, and the
    first thing the gate reported was a field named in the comment that documents
    why it is no longer read. A sentence about a field is not a read of it.

    Block comments collapse to their own newlines so a reported line still points
    at the right line. The line-comment rule refuses a `//` preceded by a colon or
    a quote, which is what keeps a URL inside a string from truncating the code
    after it; the cost of the heuristic is a missed read on such a line, never a
    false one.
    """
    text = re.sub(r"/\*[\s\S]*?\*/", lambda m: "\n" * m.group(0).count("\n"), text)
    return re.sub(r"""(?<![:'"\\\w])//[^\n]*""", "", text)


def sidecar_field_reads(text: str, shape: dict | None = None,
                        roots: list[tuple[str, list[str]]] | None = None,
                        ) -> list[tuple[int, str]]:
    """Every sidecar field one renderer module reads, as (line, dotted path).

    A regex over JavaScript is a blunt instrument and this one is deliberately
    narrow: it follows `record.sidecar` and the local names bound directly to it
    (`const s = record.sidecar`, `const p = s.placement ?? {}`), and nothing
    else. A name is only followed when its path lands on a dict, so `const e =
    p.local_e` binds nothing further and a later unrelated `e` in the same file
    cannot be mistaken for it.

    `roots` is how a caller states a binding this scanner cannot infer. The
    per-structure sidecar needs none — `record.sidecar` names itself — but the
    derived documents are read as `doc` and then handed entry by entry to a
    renderer, where the name arrives as a function parameter and the anchor is
    gone. `check_derived_contract` declares those bindings rather than guessing
    them: `("doc", [])` for the document itself, `("claim", ["claims"])` for the
    parameter that holds one of its claims. Each is (identifier, path prefix),
    and it is a claim about the module that the gate's other direction then
    holds to the document.

    What it cannot see is stated rather than implied: a sidecar value handed to a
    function is read through that function's parameter, so `claimRow(label, span,
    range)` puts `range.confidence` out of reach. This finds the reads that name
    the field where the sidecar is in hand, which is where the field name is
    chosen and therefore where it can be wrong.

    Where it errs it errs loudly. Bind a name to a sidecar block and then reuse
    that name for an unrelated object in the same module, and this attributes the
    second object's fields to the sidecar and reports them missing. That is a
    false alarm a reader resolves in a minute by renaming the variable, and it is
    the direction to fail in: the alternative is the silence that let a card read
    a field nobody wrote for the life of the project.
    """
    shape = sidecar_shape() if shape is None else shape
    text = strip_js_comments(text)
    seeds: list[tuple[str, list[str]]] = ([(SIDECAR_ROOT, [])] if roots is None
                                          else [(r"\b%s\b" % re.escape(n), list(p))
                                                for n, p in roots])

    def resolve(path: list[str]):
        """(node, ok, missing_segment) — resolution stops at the first leaf."""
        node = shape
        for i, seg in enumerate(path):
            if not isinstance(node, dict):
                return node, True, None, path[:i]
            if seg not in node:
                return None, False, seg, path[:i + 1]
            node = node[seg]
        return node, True, None, path

    def segments(chain: str) -> list[str]:
        return re.findall(JS_IDENT, chain or "")

    bound: dict[str, list[str]] = {}
    for _ in range(3):          # `s` binds before `p = s.placement` resolves
        anchors = seeds + [(r"\b%s\b" % re.escape(n), p)
                           for n, p in bound.items()]
        for anchor, prefix in anchors:
            pat = r"\b(?:const|let|var)\s+(%s)\s*=\s*%s%s" % (JS_IDENT, anchor, JS_CHAIN)
            for m in re.finditer(pat, text):
                name, path = m.group(1), prefix + segments(m.group(2))
                node, ok, _, _ = resolve(path)
                if name not in bound and ok and isinstance(node, dict):
                    bound[name] = path

    reads: dict[str, int] = {}
    anchors = seeds + [(r"\b%s\b" % re.escape(n), p)
                       for n, p in bound.items()]
    for anchor, prefix in anchors:
        for m in re.finditer(anchor + JS_CHAIN, text):
            path = prefix + segments(m.group(1))
            if not path:
                continue
            _, _, _, reached = resolve(path)
            key = ".".join(reached)
            line = text[:m.start()].count("\n") + 1
            if key and reads.get(key, 1 << 30) > line:
                reads[key] = line
    return sorted((line, path) for path, line in reads.items())


def _corridor_passes_its_method(sheet: str, tv: dict, c_: dict, params: dict,
                                rep: Report) -> None:
    """A committed corridor has to pass the tests the file says it passed.

    The measurement runs on a network fetch and cannot be re-run here, so what this holds
    is the readings against the thresholds the file itself declares. It is not a formality:
    the E-W streets exist in this file because one new test — `clear_run`, how far a
    candidate is open ground down its own middle — threw out ten strips of Wright lots that
    the width test could not tell from a street. A corridor added by hand without that
    reading, or with one below the threshold, is a corridor the method would have rejected.
    """
    where = f"{sheet}/{tv.get('id')}"
    reach = params.get("corridor_reach_m")
    for key, floor, what in (
        ("clear_run_m", params.get("clear_run_min_m"),
         "open ground down its own middle, which is what tells a street from a strip of lots"),
        ("boundary_run_m", params.get("face_min_m"),
         "boundary lines that run a block face"),
    ):
        if floor is None:
            continue
        got = c_.get(key)
        if got is None:
            rep.error("street module", f"{where}: a committed corridor records no {key}, so "
                                       f"nothing says it was held to the method's own test for "
                                       f"{what}")
            continue
        low = min(got) if isinstance(got, list) else got
        if low < float(floor) - 0.05:
            rep.error("street module", f"{where}: a committed corridor records {key} {got}, "
                                       f"below the {floor} m the method requires — this "
                                       f"reading did not pass the test the file says it did")
        if key == "clear_run_m" and reach and got > 2 * float(reach) + 0.05:
            rep.error("street module", f"{where}: a corridor is open for {got} m along a "
                                       f"centreline the method only follows "
                                       f"{2 * float(reach):g} m of")
    share, ceiling = c_.get("interior_ink_share"), params.get("ink_share")
    if share is not None and ceiling is not None and share > float(ceiling) + 1e-9:
        rep.error("street module", f"{where}: a committed corridor's interior is inked over "
                                   f"{share} of its length, above the {ceiling} the method "
                                   f"allows a corridor")


def _identification_rederives(sheet: str, tv: dict, c_: dict, coef, k: float,
                              ctl: dict, rep: Report) -> None:
    """A corridor's street name is re-derived from the control it was named by.

    The names in this file are not counted off from Canal — each one is the corridor that
    the street's committed modern junction(s) land on, projected onto the traverse through
    the sheet's own affine. All three inputs are committed, so the naming re-derives
    offline here: move a junction in `street_control.json`, or edit the offset, and the
    identification stops being true and this fails. A name nothing can re-derive is the
    kind of claim this project does not keep.
    """
    ident = c_.get("identified_as")
    if not ident:
        return
    where = f"{sheet}/{tv.get('id')}"
    sid = ident.get("street")
    street = ((ctl.get("streets") or {}).get(sid) or {})
    if not street:
        rep.error("street module", f"{where}: a corridor is identified as '{sid}', which is "
                                   f"not a street in data/traces/street_control.json")
        return
    if street.get("axis") == tv.get("axis"):
        rep.error("street module", f"{where}: a corridor is identified as {street.get('name')}, "
                                   f"which runs along this traverse rather than across it — a "
                                   f"traverse cannot measure the width of a street it rides")
        return
    across = tv.get("across_utm") or []
    if len(across) != 2:
        rep.error("street module", f"{where}: the traverse records no across_utm axis, so an "
                                   f"identification on it cannot be re-derived")
        return
    junctions = [(ctl.get("control") or {}).get(j) for j in (ident.get("control") or [])]
    if not junctions or not all(junctions):
        rep.error("street module", f"{where}: {street.get('name')} is identified from control "
                                   f"{ident.get('control')}, which does not resolve in "
                                   f"data/traces/street_control.json")
        return
    a, b, c, d, e, f = coef
    cx, cy = (c_.get("centre_px") or [0, 0])
    cE, cN = a * (cx / k) + b * (cy / k) + c, d * (cx / k) + e * (cy / k) + f
    jE = sum(float(j["utm_e"]) for j in junctions) / len(junctions)
    jN = sum(float(j["utm_n"]) for j in junctions) / len(junctions)
    off = abs((cE - jE) * float(across[0]) + (cN - jN) * float(across[1]))
    if abs(off - float(ident.get("offset_m", -1))) > 0.5:
        rep.error("street module", f"{where}: {street.get('name')} is recorded "
                                   f"{ident.get('offset_m')} m from its control and the "
                                   f"committed pixels re-derive to {off:.1f} m")
    tol = ident.get("tolerance_m")
    if tol is not None and off > float(tol) + 0.05:
        rep.error("street module", f"{where}: {street.get('name')} names a corridor {off:.1f} m "
                                   f"from where its control puts it, beyond the {tol} m the "
                                   f"method allows an identification")


def check_street_module(source_ids: set, rep: Report, data_root: Path | None = None) -> None:
    """The module every placement stands on is held to the sheets it was measured off.

    `check_position_derivations` recomputes each placement FROM the module. Nothing
    checked the module itself: 80 ft was an annotation read once during the datum work,
    a second source said 66, and the file recorded the disagreement and left it. The
    corridors are measured now (`data/traces/vectors/street_corridors_1834.json`,
    written by `tools/measure_street_widths.py`), and this is the offline half of that
    measurement — the half that runs on every commit, because the tool needs the network
    and a commit gate that needs the network fails for reasons that have nothing to do
    with the commit.

    Three things are held, and the third is the one with teeth:

    - **Every metre is re-derived from its pixels.** A corridor's width comes back out
      of the two committed boundary pixels through the sheet's own committed affine, and
      the summary comes back out of the corridor list. A metre edited by hand, or a
      median that no longer matches the readings under it, is an error — the same rule
      `tools/rederive_datum.py` applies to the origin.
    - **The adopted figure has to be the one the readings support.** `platted_street`
      may only carry the candidate nearest the measured median, and may not carry a
      candidate the readings exclude. Moving the module to 66 ft now fails here instead
      of moving five buildings quietly.
    - **The control-point finding may not go stale.** The measurement recorded that two
      GCPs sit inside a block rather than in the Canal Street corridor, and what it costs
      the datum to correct one of them. Both figures are pinned to the GCP pixels they
      were computed from, so the day somebody adopts either correction the gate fails
      until the sheet is read again. A finding whose inputs have moved is not a finding.
    """
    base = data_root or DATA
    path = base / "traces" / "vectors" / "street_corridors_1834.json"
    doc = load_json(path, rep, required=False)
    if not isinstance(doc, dict):
        rep.error("street module", "data/traces/vectors/street_corridors_1834.json is missing "
                                   "or unreadable — the platted module is the one figure every "
                                   "placement in this dataset stands on and it is measured, not "
                                   "asserted")
        return
    for s in doc.get("sources") or []:
        if s not in source_ids:
            rep.error("street module", f"the corridor measurement cites '{s}', which does not "
                                       f"resolve in data/sources/")

    params = (doc.get("method") or {}).get("params") or {}
    if not params:
        rep.error("street module", "the file states no method parameters, so nothing can hold "
                                   "a committed corridor to the method that produced it")
    ctl = load_json(base / "traces" / "street_control.json", rep, required=False) or {}

    ft = 0.3048
    all_ft: list[float] = []
    for sheet, sh in (doc.get("sheets") or {}).items():
        if sheet not in source_ids:
            rep.error("street module", f"sheet '{sheet}' is not a source in data/sources/")
        co = ((sh.get("affine") or {}).get("coefficients") or {})
        try:
            a, b, c, d, e, f = (float(co[k]) for k in "abcdef")
        except (KeyError, TypeError, ValueError):
            rep.error("street module", f"sheet '{sheet}' records no usable affine, so its "
                                       f"metres cannot be re-derived from its pixels")
            continue
        k = float((sh.get("raster") or {}).get("gcp_px_to_native") or 0) or None
        if not k:
            rep.error("street module", f"sheet '{sheet}' does not say how its pixels relate to "
                                       f"the image they were read in")
            continue
        for tv in sh.get("traverses") or []:
            for c_ in tv.get("corridors") or []:
                pts = c_.get("px") or []
                if len(pts) != 2:
                    rep.error("street module", f"{sheet}/{tv.get('id')}: a corridor with no two "
                                               f"boundary pixels is not a measurement")
                    continue
                (x1, y1), (x2, y2) = pts
                e1, n1 = a * (x1 / k) + b * (y1 / k) + c, d * (x1 / k) + e * (y1 / k) + f
                e2, n2 = a * (x2 / k) + b * (y2 / k) + c, d * (x2 / k) + e * (y2 / k) + f
                w = math.hypot(e2 - e1, n2 - n1)
                if abs(w - float(c_.get("width_m", -1))) > 0.05:
                    rep.error("street module",
                              f"{sheet}/{tv.get('id')}: a corridor records {c_.get('width_m')} m "
                              f"but its pixels re-derive to {w:.2f} m through the sheet's own "
                              f"affine")
                if abs(w / ft - float(c_.get("width_ft", -1))) > 0.1:
                    rep.error("street module",
                              f"{sheet}/{tv.get('id')}: {c_.get('width_m')} m is not "
                              f"{c_.get('width_ft')} ft")
                all_ft.append(round(w / ft, 1))
                _corridor_passes_its_method(sheet, tv, c_, params, rep)
                _identification_rederives(sheet, tv, c_, (a, b, c, d, e, f), k, ctl, rep)

    summary = doc.get("summary") or {}
    if not all_ft:
        rep.error("street module", "the file records no corridor at all")
    else:
        all_ft.sort()
        median = all_ft[len(all_ft) // 2]
        for key, got in (("n_corridors", len(all_ft)), ("median_ft", median),
                         ("min_ft", all_ft[0]), ("max_ft", all_ft[-1])):
            if summary.get(key) != got:
                rep.error("street module", f"summary.{key} says {summary.get(key)} and the "
                                           f"committed readings give {got}")

    cand = doc.get("candidates") or {}
    tol = float(cand.get("tolerance_ft") or 0)
    figures = [cand.get("adopted", {}).get("width_ft"), cand.get("dissent", {}).get("width_ft")]
    if all_ft and tol > 0 and all(isinstance(x, (int, float)) for x in figures):
        median = all_ft[len(all_ft) // 2]
        nearest = min(figures, key=lambda x: abs(median - x))
        excluded = [x for x in figures if all(abs(r - x) > tol for r in all_ft)]
        if cand.get("nearest_ft") != nearest:
            rep.error("street module", f"candidates.nearest_ft says {cand.get('nearest_ft')} and "
                                       f"the readings are nearest {nearest} ft")
        if sorted(cand.get("excluded_ft") or []) != sorted(excluded):
            rep.error("street module", f"candidates.excluded_ft says {cand.get('excluded_ft')} "
                                       f"and the readings exclude {excluded}")
        module = ctl.get("platted_street") or {}
        adopted = module.get("width_ft")
        if adopted is not None:
            if adopted in excluded:
                rep.error("street module", f"the placements step half of {adopted} ft and no "
                                           f"corridor measured on either 1834 sheet comes within "
                                           f"{tol:g} ft of it")
            elif adopted != nearest:
                rep.error("street module", f"the placements step half of {adopted} ft while the "
                                           f"measured corridors are nearest {nearest} ft; the "
                                           f"module and the sheets have to agree or the "
                                           f"disagreement has to be argued in the file")

    # The finding, pinned to the pixels it was computed from.
    for sheet, sh in (doc.get("sheets") or {}).items():
        cpc = sh.get("control_point_check") or {}
        gid, recorded = cpc.get("gcp"), cpc.get("recorded_px")
        gcp_file = (sh.get("affine") or {}).get("source")
        if not (gid and recorded and gcp_file):
            rep.error("street module", f"sheet '{sheet}' states no control-point reading to check")
            continue
        # Repo-relative in the file, resolved against the data root so the rule is
        # testable against a fixture rather than only against the committed tree.
        gdoc = load_json(base / str(gcp_file).removeprefix("data/"), rep,
                         required=False) or {}
        found = [g for g in gdoc.get("gcps", []) if g.get("id") == gid]
        if not found:
            rep.error("street module", f"sheet '{sheet}' measures GCP {gid}, which is not in "
                                       f"{gcp_file}")
        elif list(found[0].get("pixel") or []) != list(recorded):
            rep.error("street module",
                      f"{gcp_file} GCP {gid} is now at pixel {found[0].get('pixel')} and the "
                      f"corridor measurement was taken against {recorded}. If the correction "
                      f"has been adopted, re-run tools/measure_street_widths.py: the offset and "
                      f"the datum exposure it reports are about the old pixel.")

    exp = doc.get("datum_exposure") or {}
    wg = load_json(base / "traces" / "gcp" / "wright_1834_gcps.json", rep,
                   required=False) or {}
    g5 = [g for g in wg.get("gcps", []) if g.get("id") == exp.get("gcp")]
    if g5 and list(g5[0].get("pixel") or []) != list(exp.get("recorded_px") or []):
        rep.error("street module",
                  f"datum_exposure is computed against {exp.get('gcp')} at "
                  f"{exp.get('recorded_px')} and the committed pixel is "
                  f"{g5[0].get('pixel')} — the figure for what the correction costs is "
                  f"stale, which is worse than not having it")
    if exp and exp.get("status") not in ("queued, not adopted", "adopted"):
        rep.error("street module", "datum_exposure has to say whether the correction it prices "
                                   "has been adopted")


def check_sidecar_contract(rep: Report) -> None:
    """Every sidecar field the renderer reads must be one the compiler writes."""
    shape = sidecar_shape()
    if not shape:
        rep.note("sidecar contract: skipped — no committed sidecars to read the shape from")
        return

    js = sorted(p for p in (ROOT / "renderers").rglob("*.js") if "vendor" not in p.parts)
    read_paths: set[str] = set()
    files_reading = 0
    for path in js:
        reads = sidecar_field_reads(path.read_text(), shape)
        if reads:
            files_reading += 1
        for line, dotted in reads:
            read_paths.add(dotted)
            node = shape
            for seg in dotted.split("."):
                if not isinstance(node, dict):
                    break
                if seg not in node:
                    rep.error("sidecar contract",
                              f"{path.relative_to(ROOT)}:{line} reads `{dotted}` and no "
                              f"committed sidecar carries it — the renderer would read "
                              f"undefined on every building, silently, forever. Either "
                              f"tools/compile_scene.py emits the field or the renderer "
                              f"stops asking for it")
                    break
                node = node[seg]

    # A scanner that matched nothing would pass every renderer ever written, so
    # it reports what it found and the floor it is holding itself to.
    if read_paths and files_reading < 2:
        rep.error("sidecar contract",
                  f"only {files_reading} renderer module reads a sidecar — the scan has "
                  f"probably stopped matching; check sidecar_field_reads")
    rep.note(f"sidecar contract: {len(read_paths)} field(s) read across {files_reading} "
             f"renderer module(s), all present in the compiled sidecars")

    # The other direction is reported and not enforced, because the scan cannot
    # follow a value into a function: `documented_range` is read field by field
    # inside the row renderer it is passed to. At the top level that limit does
    # not bite, so an unread root key is a real finding — something the compiler
    # writes for a visitor who never sees it.
    unread = sorted(k for k in shape if k not in {p.split(".")[0] for p in read_paths})
    if unread:
        rep.note(f"sidecar contract: {len(unread)} top-level field(s) compiled and never "
                 f"read by the renderer ({', '.join(unread)}) — dead weight or an "
                 f"unshipped claim, not an error either way")


# --- the OTHER derived documents ------------------------------------------
#
# `sidecar_shape` says in as many words that it covers the per-structure sidecar
# and not `exclusions.json` or `terrain.json`, because those "have their own
# readers and their own shapes". That sentence has been true and unenforced
# since it was written, and it names precisely the interface the three faults of
# STATUS § 28-30 lived in: a field read and never emitted, a field emitted and
# never read, and a field that never entered the interface at all. Three
# documents were outside every one of those gates.
#
# The binding is DECLARED rather than inferred, and that is the whole design.
# A per-structure sidecar names itself — `record.sidecar` is an anchor a regex
# can follow. These are fetched into a local `doc` and then handed entry by
# entry to a renderer, so the field names are chosen inside a function whose
# parameter is `claim` or `ex` or `u`, with nothing left to anchor on. Writing
# the binding down is a claim about the module, and the gate then holds the
# module to it in both directions: a declared root that reads a field the
# document does not carry fails, and a field the compiler writes that no root
# reads must be declared internal with the reason.
#
# `internal` is § 48's partition arriving at a second family of documents. The
# bounded set there was the source schema; here it is what the compiler emits,
# which `compile_scene.py --check` and `compile_liberties.py --check` already
# prove is exactly what the dataset derives to.
DERIVED_DOCUMENTS = [
    {
        "doc": "sidecars/*/terrain.json",
        "module": "renderers/web/js/ground.js",
        # identifier in that module -> the path inside the document it holds
        "roots": {"doc": "", "claim": "claims", "f": "claims.fields",
                  "c": "context", "z": "not_modelled"},
        "internal": {
            "scene": "the sidecar is fetched by scene id; naming it back is machinery",
            "target_date": "the scene's date, shown by the HUD from the scene record",
            "epoch": "which terrain epoch compiled these claims — a reviewer's join, "
                     "and the claims themselves carry no epoch-specific wording",
            "claims.id": "the spec key the claim was derived from; `label` is what a "
                         "visitor reads and `Covers:` tokens are the gate's business",
            "claims.confidence_key": "which key of the block held the grade, so the "
                                     "gate can find it again; the grade itself is shown",
            "claims.sources": "the raw source ids, joined into `citations` by cite() "
                              "and shown from there",
            "not_modelled.dossier_zone": "the terrain dossier's zone number, a pointer "
                                         "into a file no visitor has; `why` says it in "
                                         "words",
        },
    },
    {
        "doc": "sidecars/*/exclusions.json",
        "module": "renderers/web/js/exclusions.js",
        "roots": {"doc": "", "ex": "excluded", "u": "uncertain"},
        "internal": {
            "scene": "as above — the id this file was fetched by",
            "target_date": "as above",
        },
    },
    {
        "doc": "liberties.json",
        "module": "renderers/web/js/liberties.js",
        "roots": {"doc": "", "lib": "liberties", "f": "liberties.fields",
                  "c": "liberties.covers"},
        "internal": {
            "_doc": "the do-not-hand-edit banner, addressed to whoever opens the file",
            "source": "docs/LIBERTIES.md, the path the list was derived from",
            "count": "the length of the list the visitor is already scrolling",
            "liberties.scope.enumeration": "which derived population a `Scope:` "
                "entry admits to, as the key tools/compile_liberties.py re-counts "
                "it by; the visitor reads the field's own prose, which names the "
                "same file in words",
            "liberties.scope.count": "the count exactly as the markdown declares "
                "it, carried so a drift from the register it enumerates is a gate "
                "failure rather than a number the next compile silently absorbs. "
                "The figure a visitor reads is the one inside the `Scope:` field "
                "text, which is already shipped",
        },
    },
]

# Citation leaves are deferred to `check_source_surface`, which partitions all
# 22 properties of the source schema and holds `citations.js` to them (§ 48).
# One compiled citation shape reaches all three of these documents, so checking
# it here as well would give one field two owners and, the day they disagree,
# two answers.
CITATION_SEGMENT = "citations"


def node_shape(docs: list, path: list[str]) -> dict:
    """Union shape of the node at `path`, with lists left as leaves.

    Descending THROUGH a list means "each element of it", which is what makes a
    declared root like `claims.fields` name the thing a renderer's parameter
    actually holds. Stopping AT one keeps `(claim.fields || []).map` from being
    read as a field named `map` — the same reason `sidecar_shape` stops at a
    leaf, arriving where the interface is a list of entries rather than one
    record.
    """
    nodes: list = list(docs)
    for seg in path:
        nxt: list = []
        for n in nodes:
            if isinstance(n, list):
                nxt.extend(e.get(seg) for e in n if isinstance(e, dict))
            elif isinstance(n, dict) and seg in n:
                nxt.append(n[seg])
        nodes = nxt
    def merge(shape: dict, doc: dict) -> dict:
        for k, v in doc.items():
            if isinstance(v, dict):
                prev = shape.get(k)
                shape[k] = merge(prev if isinstance(prev, dict) else {}, v)
            else:
                shape.setdefault(k, None)
        return shape

    shape: dict = {}
    for n in nodes:
        for e in (n if isinstance(n, list) else [n]):
            if isinstance(e, dict):
                merge(shape, e)
    return shape


def emitted_leaves(docs: list, prefix: str = "") -> dict[str, None]:
    """Every field a derived document states, as dotted paths to its leaves.

    A list of dicts is not a leaf — its entries' fields are — because that is
    the level a visitor meets: `excluded` is a section and `excluded.reason` is
    a sentence somebody wrote. A list of scalars IS one: `subjects` is a set of
    ids rendered as a row of chips, not a nested claim.
    """
    out: dict[str, None] = {}

    def walk(nodes: list, path: str) -> None:
        keys: dict[str, list] = {}
        for n in nodes:
            if not isinstance(n, dict):
                continue
            for k, v in n.items():
                keys.setdefault(k, []).append(v)
        for k, vals in keys.items():
            here = f"{path}.{k}" if path else k
            nested = [v for v in vals if isinstance(v, dict)]
            entries = [e for v in vals if isinstance(v, list) for e in v
                       if isinstance(e, dict)]
            if nested or entries:
                walk(nested + entries, here)
            else:
                out[here] = None

    walk(docs, prefix)
    return out


def load_derived(spec: dict) -> tuple[list, str | None]:
    """The committed copies of a derived document and its declared reader."""
    pattern = spec["doc"]
    paths = sorted(DATA.glob(pattern)) if "*" in pattern else [DATA / pattern]
    docs = [json.loads(p.read_text()) for p in paths if p.is_file()]
    src = ROOT / spec["module"]
    return docs, (src.read_text() if src.is_file() else None)


def check_derived_contract(rep: Report, *, specs: list[dict] | None = None,
                           load=load_derived) -> None:
    """The derived documents outside the sidecar gate, held from both sides."""
    for spec in (DERIVED_DOCUMENTS if specs is None else specs):
        pattern, module = spec["doc"], spec["module"]
        docs, text = load(spec)
        if not docs:
            rep.error("derived contract",
                      f"{pattern} is declared as a derived document and nothing "
                      f"matching it is committed — either the compiler stopped "
                      f"writing it or this declaration is stale")
            continue
        if text is None:
            rep.error("derived contract", f"{module} is declared as the reader of "
                                          f"{pattern} and does not exist")
            continue

        read: dict[str, int] = {}
        for ident, prefix in spec["roots"].items():
            segs = [s for s in prefix.split(".") if s]
            shape = node_shape(docs, segs)
            if not shape:
                rep.error("derived contract",
                          f"{module} binds `{ident}` to `{prefix or '(the document)'}` "
                          f"of {pattern}, and no committed copy has anything there")
                continue
            for line, dotted in sidecar_field_reads(text, shape, roots=[(ident, [])]):
                full = ".".join(segs + dotted.split("."))
                if CITATION_SEGMENT in full.split("."):
                    continue
                node, ok = shape, True
                for seg in dotted.split("."):
                    if not isinstance(node, dict):
                        break
                    if seg not in node:
                        ok = False
                        break
                    node = node[seg]
                if not ok:
                    rep.error("derived contract",
                              f"{module}:{line} reads `{ident}.{dotted}` and no "
                              f"committed {pattern} carries `{full}` — it renders as "
                              f"nothing, on every entry, silently. Either the compiler "
                              f"emits the field or the renderer stops asking for it")
                    continue
                read.setdefault(full, line)

        leaves = [p for p in emitted_leaves(docs)
                  if CITATION_SEGMENT not in p.split(".")]
        internal = spec["internal"]
        for path in sorted(leaves):
            if path in read:
                if path in internal:
                    rep.error("derived contract",
                              f"{pattern}: `{path}` is declared internal — "
                              f"\"{internal[path]}\" — and {module} reads it at line "
                              f"{read[path]}. One of the two is wrong about the visitor")
                continue
            if path not in internal:
                rep.error("derived contract",
                          f"{pattern}: `{path}` is compiled and {module} never reads "
                          f"it. Either it reaches a visitor or DERIVED_DOCUMENTS says "
                          f"in one line why it does not — an authored sentence that "
                          f"renders nowhere is an unshipped claim, not dead weight")
        for path in sorted(internal):
            if path not in leaves:
                rep.error("derived contract",
                          f"{pattern}: `{path}` is declared internal and the compiler "
                          f"does not emit it — a stale partition")

        rep.note(f"derived contract: {pattern} — {len(read)} field(s) read by "
                 f"{Path(module).name}, {len(internal)} declared internal, "
                 f"{len(leaves)} emitted")

    # The honest limit, and it is the same one § 28 was written about: this
    # proves a module NAMES the field, not that the field reaches a pixel.
    # `exclusions.json`'s `standard` and `uncertain_standard` were the standing
    # example — read into a return value, rendered by nobody, and the scan
    # satisfied — until 2026-08-11, when both were mounted and the smoke was given
    # a verbatim assertion against the compiled value. The limit itself has not
    # moved: nothing here can distinguish the next such read from a render, which
    # is why the smoke pins rendered text for every claim that carries one, and
    # why a read is never the last word.
    rep.note("derived contract: a read is a name, not a render — the smoke pins the "
             "rendered text for the claims that carry one")


def citation_shape() -> set[str]:
    """The keys a compiled citation actually carries, unioned over every one.

    Same union argument as `sidecar_shape`: a key is part of the interface even
    when one source in twenty-nine carries it. Taken from every derived document
    that joins citations — the per-structure sidecars, the exclusions list and
    the terrain claims — because `cite()` writes one shape into all three and a
    check reading only the first would stop being right the day a field is
    emitted for an exclusion alone.
    """
    keys: set[str] = set()
    for path in sorted((DATA / "sidecars").rglob("*.json")):
        def walk(node) -> None:
            if isinstance(node, dict):
                for k, v in node.items():
                    if k == "citations" and isinstance(v, list):
                        for c in v:
                            if isinstance(c, dict):
                                keys.update(c)
                    else:
                        walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
        walk(json.loads(path.read_text()))
    return keys


def check_source_surface(sources: dict, rep: Report, *,
                         surface: dict[str, str] | None = None,
                         properties: set[str] | None = None,
                         emitted: set[str] | None = None,
                         js_src: str | None = None) -> None:
    """Every field of a source record either reaches a visitor or says why not.

    The two directions of `check_sidecar_contract` are *read and never emitted*
    (an error: the renderer reads undefined forever) and *emitted and never
    read* (a note: an unshipped claim). Neither can see the third kind, and the
    third kind is what happened here: `data/source.schema.json` grew
    `transcribes`, `carries_no_document`, `what_it_supplies` and
    `what_it_does_not_supply` — four fields whose own schema descriptions are
    addressed to a reader — and `cite()` never carried one of them into a
    sidecar. Nothing was broken. A shape unioned over what IS emitted cannot
    report what was never offered, and the compiler was consistent with itself,
    which is all `--check` proves.

    What makes the fault checkable is that the candidate set is bounded: it is
    the schema's own properties. So the partition is declared in
    `compile_scene.SOURCE_FIELD_SURFACE` and this holds it three ways.

    1. A schema property in neither half fails. That is the mechanism — a field
       added to a source record costs one line saying whether a visitor sees it,
       and the sentence has to be written by whoever knows the answer.
    2. A `visitor` field that some record carries and no compiled citation does
       fails. This is the check that was missing: it is exactly the state the
       dataset was in until today, for four fields and the life of the project.
    3. A `visitor` field never read by `renderers/web/js/citations.js` fails.
       The card is where the promise is kept, and one module renders every
       citation in this walkthrough — which is what makes the § 40 objection
       ("the scan cannot follow a value into a function") not bite here: the
       shape has one name and one renderer, so a member read is a real read.
       It is still a name scan and not dataflow, and that limit is why the
       smoke asserts the rendered card rather than trusting this.

    The reverse of 3 — a key emitted and never read — stays a note, as it is at
    the top level, because the honest response to it is a decision rather than
    an error.

    The four keyword arguments exist for the self-test and default to the
    committed halves; nothing in the suite passes them.
    """
    if surface is None:
        try:
            sys.path.insert(0, str(ROOT / "tools"))
            import compile_scene  # noqa: PLC0415
            surface = compile_scene.SOURCE_FIELD_SURFACE
        except Exception as exc:  # noqa: BLE001
            rep.error("source surface", f"cannot read compile_scene.SOURCE_FIELD_SURFACE: {exc}")
            return

    if properties is None:
        schema_path = DATA / "source.schema.json"
        if not schema_path.is_file():
            rep.note("source surface: skipped — no data/source.schema.json")
            return
        properties = set(json.loads(schema_path.read_text()).get("properties", {}))

    for prop in sorted(properties - set(surface)):
        rep.error("source surface",
                  f"`{prop}` is in data/source.schema.json and not in "
                  f"compile_scene.SOURCE_FIELD_SURFACE. Every field of a source record "
                  f"either reaches the citation a visitor reads or says in one line why "
                  f"it stays in the repository — undeclared is how four reader-facing "
                  f"fields went to nobody for the life of the project")
    for prop in sorted(set(surface) - properties):
        rep.error("source surface",
                  f"compile_scene.SOURCE_FIELD_SURFACE declares `{prop}`, which is not a "
                  f"property of data/source.schema.json — a partition of a set that has "
                  f"moved underneath it")

    visitor = {k for k, why in surface.items() if why.startswith("visitor")}
    if emitted is None:
        emitted = citation_shape()
    if not emitted:
        rep.note("source surface: skipped the emitted half — no compiled citations to read")
    else:
        for prop in sorted(visitor):
            carried = sorted(s for s, rec in sources.items() if rec.get(prop))
            if carried and prop not in emitted:
                rep.error("source surface",
                          f"`{prop}` is declared visitor-facing, {len(carried)} source "
                          f"record(s) carry it ({', '.join(carried[:3])}"
                          f"{', …' if len(carried) > 3 else ''}) and no compiled citation "
                          f"does — tools/compile_scene.cite() is not carrying it, so the "
                          f"claim is written for a reader who cannot reach it")
        for prop in sorted(emitted - visitor - {"source_id", "tier_label"}):
            rep.error("source surface",
                      f"a compiled citation carries `{prop}`, which "
                      f"{'is declared internal' if prop in surface else 'is not in the partition'}"
                      f" — the sidecar is shipping a field nobody said a visitor should see")

    if js_src is None:
        js = ROOT / "renderers" / "web" / "js" / "citations.js"
        if not js.is_file():
            rep.error("source surface", "renderers/web/js/citations.js is missing — the one "
                                        "renderer every citation in this walkthrough goes "
                                        "through")
            return
        js_src = js.read_text()
    src = strip_js_comments(js_src)
    unread = sorted(p for p in visitor
                    if p in emitted and not re.search(rf"\.{re.escape(p)}\b", src))
    for prop in unread:
        rep.error("source surface",
                  f"`{prop}` is compiled into the citations and "
                  f"renderers/web/js/citations.js never reads it. A field declared "
                  f"visitor-facing that no renderer touches is the same unshipped claim "
                  f"in a new place")
    rep.note(f"source surface: {len(properties)} schema field(s) partitioned, "
             f"{len(visitor)} visitor-facing, {len(emitted)} key(s) on a compiled citation")


# --------------------------------------------------------------------------
# flora: zone records, palettes, and the July phenology traps
# --------------------------------------------------------------------------
#
# docs/research/02-flora.md carries a block of "Global phenology rules" whose
# whole point is that a mid-July prairie is easy to render as a September one.
# Those rules are enforced HERE, as schema, rather than left as prose: the
# dossier calls 2 m turkey-foot seed heads on big bluestem in July "the single
# most common historical-reconstruction error", and an error you can only catch
# by eye is one you will ship. Everything below makes a wrong record
# unrepresentable rather than merely discouraged.

FLORA = DATA / "flora"

FLORA_ROLES = ("matrix", "forb", "emergent", "shrub_low", "ground", "tree", "thicket")
# The roles `renderers/web/js/flora.js` deals as SLOTS — one slot is one drawn
# plant, so its lottery is a count and a `cover_fraction` is an area (K49(a)).
# `width_m` is the only thing in a record that converts the one into the other,
# and until K49(c) twenty-five sward records carried a cover and no width, so
# six of twenty lists dealt an area against a count. The two roles left out are
# `tree` and `thicket`, which trees.js deals off `density_per_ha` mixes and
# never converts.
FLORA_SWARD_ROLES = ("matrix", "forb", "emergent", "shrub_low", "ground")
FLORA_PHENOLOGY = ("flowering", "vegetative", "budding", "past_bloom", "fruiting",
                   "leafless", "senescent")
EXTENT_KINDS = ("elevation_band", "polygon", "buffer", "everywhere")
ABUNDANCE_LIMITS = {"cover_fraction": 1.0, "density_per_ha": 5000.0, "stems_per_m2": 200.0}

# The three warm-season grasses that are LEAFY AND VEGETATIVE in mid-July, at
# roughly half their September height. Naming them here is the point: this is the
# error the dossier singles out.
JULY_VEGETATIVE_GRASSES = {
    "Andropogon gerardii": 1.5,
    "Sorghastrum nutans": 1.5,
    "Panicum virgatum": 1.6,
}
# ...and the two that DO flower now. Cordgrass is the tall element in July.
JULY_FLOWERING_GRASSES = ("Sporobolus michauxianus", "Calamagrostis canadensis")
# Later arrivals: a cattail that did not reach Illinois until long after 1835.
BANNED_TAXA = ("Typha angustifolia", "Typha x glauca", "Typha × glauca",
               "Lythrum salicaria", "Phalaris arundinacea", "Rhamnus cathartica",
               "Phragmites australis subsp. australis")


def _rgb_ok(v) -> bool:
    return (isinstance(v, list) and len(v) == 3
            and all(isinstance(c, int) and 0 <= c <= 255 for c in v))


def _is_july_green(rgb) -> bool:
    """A July foliage colour: green-dominant and not straw.

    A tawny sward is the October negative control the reference set carries on
    purpose; the check is deliberately crude and deliberately absolute.
    """
    r, g, b = rgb
    return g >= r and g > b


def _carries_flower_colour(rgb) -> bool:
    """True for a saturated bloom colour — what a past-bloom fruit must not be."""
    r, g, b = rgb
    return b >= max(r, g) or (min(r, g) - b) > 100 or (r - max(g, b)) > 90


def _num_range(v, lo=0.0, hi=1e9) -> bool:
    return (isinstance(v, list) and len(v) == 2
            and all(isinstance(x, (int, float)) for x in v)
            and lo <= v[0] <= v[1] <= hi)


def _point_in_polygon(e: float, n: float, poly: list) -> bool:
    inside = False
    j = len(poly) - 1
    for i, (xi, yi) in enumerate(poly):
        xj, yj = poly[j]
        if (yi > n) != (yj > n):
            x = xi + (n - yi) * (xj - xi) / ((yj - yi) or 1e-12)
            if e < x:
                inside = not inside
        j = i
    return inside


def _water_distance(field) -> list:
    """Chamfer distance in metres from every cell to the nearest water cell.

    Two passes over the grid with a (1, sqrt2) kernel. Approximate by about two
    per cent, which is far inside the tolerance of a question like "is this cell
    within eight metres of the river".
    """
    cols, rows, cell = field.cols, field.rows, field.cell_m
    big = 1e9
    d = [0.0 if field._at(i, j) <= 0.0 else big
         for j in range(rows) for i in range(cols)]
    diag = 2 ** 0.5
    for j in range(rows):
        base = j * cols
        prev = base - cols
        for i in range(cols):
            k = base + i
            if d[k] == 0.0:
                continue
            best = d[k]
            if i > 0:
                best = min(best, d[k - 1] + 1.0)
            if j > 0:
                best = min(best, d[prev + i] + 1.0)
                if i > 0:
                    best = min(best, d[prev + i - 1] + diag)
                if i < cols - 1:
                    best = min(best, d[prev + i + 1] + diag)
            d[k] = best
    for j in range(rows - 1, -1, -1):
        base = j * cols
        nxt = base + cols
        for i in range(cols - 1, -1, -1):
            k = base + i
            if d[k] == 0.0:
                continue
            best = d[k]
            if i < cols - 1:
                best = min(best, d[k + 1] + 1.0)
            if j < rows - 1:
                best = min(best, d[nxt + i] + 1.0)
                if i < cols - 1:
                    best = min(best, d[nxt + i + 1] + diag)
                if i > 0:
                    best = min(best, d[nxt + i - 1] + diag)
            d[k] = best
    return [x * cell for x in d]


def _extent_matches(ext: dict, e: float, n: float, h: float, dwater: float) -> bool:
    box = ext.get("box")
    if box:
        be, bn = box.get("e"), box.get("n")
        if be and not (be[0] <= e <= be[1]):
            return False
        if bn and not (bn[0] <= n <= bn[1]):
            return False
    kind = ext.get("kind")
    ok = True
    if kind == "elevation_band":
        lo, hi = ext.get("elev_m", [0, 0])
        ok = lo <= h <= hi
    elif kind == "polygon":
        ok = _point_in_polygon(e, n, ext.get("polygon") or [])
    elif kind == "buffer":
        lo, hi = ext.get("distance_m", [0, 0])
        ok = lo <= dwater <= hi
    elif kind != "everywhere":
        return False
    # Ground a community holds that its own rule cannot reach — the mirror of the
    # exclusions below, and read here exactly as renderers/web/js/flora.js reads
    # it, so this evaluator keeps answering the question the renderer answers.
    if not ok:
        ok = any(_point_in_polygon(e, n, patch)
                 for patch in ext.get("include_polygons") or [])
    if not ok:
        return False
    for hole in ext.get("exclude_polygons") or []:
        if _point_in_polygon(e, n, hole):
            return False
    return True


def check_flora_extents(zones: dict, field, rep: Report) -> None:
    """Evaluate every zone's extent against the committed heightfield.

    Answers three questions no eye can answer reliably: does a zone that claims
    to be plantable actually match any ground; do two zones tie on priority
    anywhere (the contract calls a tie a data error); and how much land ends up
    unzoned, which the renderer must leave EMPTY rather than fill with a default
    community.
    """
    if field is None:
        rep.note("flora extents: skipped — needs the committed heightfield")
        return
    dwater = _water_distance(field)
    cols, rows, cell = field.cols, field.rows, field.cell_m
    step = 2  # every second cell: 5 m spacing over a 640 m box
    matched = {zid: 0 for zid in zones}
    land = water = unzoned = 0
    ties: set = set()
    for j in range(0, rows, step):
        n = field.origin_n + j * cell
        for i in range(0, cols, step):
            e = field.origin_e + i * cell
            h = field._at(i, j)
            d = dwater[j * cols + i]
            hits = [(z.get("extent", {}).get("priority", 0), zid)
                    for zid, z in zones.items()
                    if _extent_matches(z.get("extent", {}), e, n, h, d)]
            for _, zid in hits:
                matched[zid] += 1
            if h <= 0.0:
                water += 1
                continue
            land += 1
            if not hits:
                unzoned += 1
                continue
            top = max(p for p, _ in hits)
            winners = sorted(zid for p, zid in hits if p == top)
            if len(winners) > 1:
                ties.add(tuple(winners))
    for w in sorted(ties):
        rep.error("flora extents", f"zones {' and '.join(w)} share priority where their "
                                   f"extents overlap — the contract makes a tie a data error, "
                                   f"because it leaves the community at that point undecided")
    for zid, z in zones.items():
        declared = z.get("plantable_in_scene")
        actual = matched[zid] > 0
        if declared is None:
            rep.error(f"flora zone {zid}", "plantable_in_scene is missing — a zone must say "
                                           "whether it has modelled ground in this scene "
                                           "rather than leave the renderer to discover it")
        elif bool(declared) != actual:
            rep.error(f"flora zone {zid}",
                      f"plantable_in_scene is {declared} but its extent matches "
                      f"{matched[zid]} sample(s) of the committed heightfield. A zone off the "
                      f"modelled ground must say so; one on it must not claim otherwise")
    pct = 100.0 * unzoned / land if land else 0.0
    rep.note(f"flora extents: {land} land sample(s), {water} water, {unzoned} unzoned "
             f"({pct:.1f}%) — unzoned ground is planted with NOTHING, never a default "
             f"community")
    if pct > 10.0:
        rep.warn("flora extents", f"{pct:.1f}% of the modelled land matches no zone; that is "
                                  f"bare ground in the walkthrough, so either a zone's extent "
                                  f"is wrong or the gap needs stating")


def check_flora_species(zid: str, sp: dict, source_ids: set, vocab: dict,
                        rep: Report, tally: dict, ext: dict | None = None) -> None:
    where = f"flora zone {zid}/{sp.get('id', '?')}"
    binomial = (sp.get("binomial") or "").strip()
    for key in ("id", "binomial", "common", "role", "form", "abundance", "height_m",
                "july", "confidence"):
        if key not in sp:
            rep.error(where, f"missing required key '{key}'")
            return
    if not SLUG.match(sp["id"] or ""):
        rep.error(where, f"id '{sp['id']}' is not a lowercase slug")
    if sp["role"] not in FLORA_ROLES:
        rep.error(where, f"role '{sp['role']}' is not one of {FLORA_ROLES}")
    forms = set(vocab.get("forms_flora", [])) | set(vocab.get("forms_trees", [])) \
        | set(vocab.get("forms_unimplemented", []))
    if sp["form"] not in forms:
        rep.error(where, f"form '{sp['form']}' is not declared in index.json's vocabulary — "
                         f"a renderer reads that block to know what it may be asked to draw")
    for banned in BANNED_TAXA:
        if binomial.lower() == banned.lower():
            rep.error(where, f"{banned} is a post-settlement arrival and must not appear in "
                             f"an 1835 record")

    # WHICH SIDE OF THE WATERLINE. Nothing machine-readable used to distinguish a
    # water lily from a cattail: both were `role: emergent`, and the placer read
    # the role, so a floating pad was planted on the dry bank like any other
    # emergent. `appearance` said "floating pads in open water" — but that is
    # prose, and prose is not a gate. See ROADMAP § K3.
    substrates = tuple(vocab.get("substrates") or ())
    substrate = sp.get("substrate")
    if substrate is not None and substrate not in substrates:
        rep.error(where, f"substrate '{substrate}' is not declared in index.json's "
                         f"vocabulary {substrates} — the placer reads that block to know "
                         f"which stations a species may be given")
    elif sp["role"] == "emergent" and substrate is None:
        rep.error(where, f"role 'emergent' must state a substrate, one of {substrates}: "
                         f"rooted in wet ground or standing water with the foliage above the "
                         f"surface ('saturated_soil') and rooted under water with the leaves "
                         f"floating on it ('open_water') are different placements, and a "
                         f"record that does not choose gets planted as whichever the renderer "
                         f"guesses")
    if substrate == "open_water":
        is_water_buffer = bool(ext) and ext.get("kind") == "buffer" and ext.get("of") == "water"
        reaches_water = is_water_buffer and (ext.get("distance_m") or [1])[0] == 0
        if not reaches_water:
            rep.error(where, "substrate 'open_water' may only be planted over water, and this "
                             "zone's extent never reaches any: a record that can never be "
                             "drawn is a claim the walkthrough does not make. Either the zone "
                             "is wrong or the species belongs in the marsh record")

    ab = sp["abundance"]
    keys = [k for k in ABUNDANCE_LIMITS if k in ab]
    if len(keys) != 1 or len(ab) != 1:
        rep.error(where, f"abundance must carry EXACTLY ONE of {tuple(ABUNDANCE_LIMITS)}, "
                         f"got {sorted(ab)}")
    elif not _num_range(ab[keys[0]], 0.0, ABUNDANCE_LIMITS[keys[0]]):
        rep.error(where, f"abundance.{keys[0]} must be [min,max] ascending within "
                         f"0..{ABUNDANCE_LIMITS[keys[0]]}, got {ab[keys[0]]}")
    if not _num_range(sp["height_m"], 0.01, 45.0):
        rep.error(where, f"height_m must be [min,max] ascending in metres, got {sp['height_m']}")
    if "width_m" in sp and not _num_range(sp["width_m"], 0.01, 45.0):
        rep.error(where, f"width_m must be [min,max] ascending, got {sp['width_m']}")

    # ROADMAP K49(c) — A COVER IS NOT A COUNT, AND width_m IS THE ONLY BRIDGE.
    # The sward's placer deals slots, one slot per drawn plant, off a single
    # normalised share per list. A record measuring an AREA and a record
    # counting PLANTS were both read into that share, so "covers a quarter of
    # the ground" was compared against "a quarter of a plant per square metre".
    # A width closes it, and the gap has to stay closed: a new cover record
    # without one silently re-opens a list that is measurable today.
    if "cover_fraction" in ab and sp["role"] in FLORA_SWARD_ROLES and "width_m" not in sp:
        rep.error(where, "abundance.cover_fraction is an AREA and the sward is dealt as a "
                         "COUNT of plants, so this record needs width_m — what one plant "
                         "covers on the ground — before it can be dealt against a species "
                         "recorded as a density. See ROADMAP K49(c)")

    # An added width is almost never something a source states, and the record's
    # own `confidence` grades what its sources say about the PLANT. Writing a
    # width under that grade promotes an argument into an attestation, so a
    # width that the record's sources do not state carries its own grade here —
    # and that grade may never outrank the record it sits in.
    wp = sp.get("width_provenance")
    if wp is not None:
        if "width_m" not in sp:
            rep.error(where, "width_provenance grades a width_m this record does not carry")
        wconf = check_attested(where, "width_provenance", wp, source_ids, rep)
        rconf = sp.get("confidence")
        if wconf and rconf in CONFIDENCE and CONFIDENCE.index(wconf) < CONFIDENCE.index(rconf):
            rep.error(where, f"width_provenance is '{wconf}' on a record graded '{rconf}' — a "
                             f"figure may not outrank the record it belongs to")

    # ROADMAP K49(c2) — THE SAME RULE FOR AN ABUNDANCE THE SOURCE DID NOT STATE
    # IN THE UNIT THE RECORD KEEPS IT IN. A dossier that gives a spacing states a
    # count, and a dossier that gives a cover states an area; converting one into
    # the other is arithmetic on top of the source, not the source. Where a
    # record's abundance is that conversion it says so here, under its own grade,
    # and that grade may no more outrank the record than a width's may.
    apr = sp.get("abundance_provenance")
    if apr is not None:
        aconf = check_attested(where, "abundance_provenance", apr, source_ids, rep)
        rconf = sp.get("confidence")
        if aconf and rconf in CONFIDENCE and CONFIDENCE.index(aconf) < CONFIDENCE.index(rconf):
            rep.error(where, f"abundance_provenance is '{aconf}' on a record graded '{rconf}' — "
                             f"a figure may not outrank the record it belongs to")

    j = sp.get("july")
    if not isinstance(j, dict):
        rep.error(where, "july must be the phenology block for the scene date")
        return
    ph = j.get("phenology")
    if ph not in FLORA_PHENOLOGY:
        rep.error(where, f"july.phenology '{ph}' is not one of {FLORA_PHENOLOGY}")
    infl = j.get("inflorescence")
    if "inflorescence" not in j:
        rep.error(where, "july.inflorescence must be present, null when there is nothing "
                         "in flower or fruit — an absent key hides the claim")
    if not (j.get("appearance") or "").strip():
        rep.error(where, "july.appearance is what a critic reads to decide whether the render "
                         "matches the record; it may not be empty")

    fol = j.get("foliage_rgb")
    if ph == "leafless":
        if fol is not None:
            rep.error(where, "phenology 'leafless' requires foliage_rgb null — leafless means "
                             "no leaves, and a green in this field puts them back")
    elif not _rgb_ok(fol):
        rep.error(where, f"july.foliage_rgb must be [r,g,b] 0-255, got {fol}")
    elif not _is_july_green(fol):
        rep.error(where, f"july.foliage_rgb {fol} is not a July green (green must be the "
                         f"dominant channel). A tawny or straw sward is the October scene, "
                         f"which fails the reference bar")
    alt = j.get("foliage_rgb_alt")
    if alt is not None and (not _rgb_ok(alt) or not _is_july_green(alt)):
        rep.error(where, f"july.foliage_rgb_alt {alt} must be a second July green")

    if infl is not None:
        if not isinstance(infl, dict) or not _rgb_ok(infl.get("rgb")):
            rep.error(where, "july.inflorescence needs a shape and an [r,g,b]")
        else:
            if not (0.0 <= (infl.get("height_frac") or -1) <= 1.0):
                rep.error(where, "july.inflorescence.height_frac must be 0..1 (0 base, 1 tip)")
            if not _num_range(infl.get("size_m"), 0.001, 3.0):
                rep.error(where, "july.inflorescence.size_m must be [min,max] in metres")

    # --- the traps ---------------------------------------------------------
    if ph in ("vegetative", "budding") and infl is not None:
        rep.error(where, f"phenology '{ph}' requires inflorescence null — a plant that is "
                         f"vegetative or in bud has nothing open to draw")
    if binomial in JULY_VEGETATIVE_GRASSES:
        limit = JULY_VEGETATIVE_GRASSES[binomial]
        if ph != "vegetative" or infl is not None:
            rep.error(where, f"{binomial} is VEGETATIVE in mid-July with no inflorescence. "
                             f"The dossier names July seed heads on this grass the single "
                             f"most common historical-reconstruction error")
        if isinstance(sp.get("height_m"), list) and len(sp["height_m"]) == 2 \
                and sp["height_m"][1] > limit:
            rep.error(where, f"{binomial} at {sp['height_m'][1]} m is its September height; in "
                             f"mid-July it stands at 50-60 per cent of that, under {limit} m")
    if binomial in JULY_FLOWERING_GRASSES and (ph != "flowering" or infl is None):
        rep.error(where, f"{binomial} IS in flower in mid-July and must carry an "
                         f"inflorescence — cordgrass is the tall flowering element of the "
                         f"July prairie")
    if binomial == "Typha latifolia":
        if ph != "fruiting":
            rep.error(where, "Typha latifolia is FRUITING in July — the spike is mature")
        if isinstance(infl, dict) and _rgb_ok(infl.get("rgb")):
            r, g, b = infl["rgb"]
            if not (r > g > b):
                rep.error(where, f"the July cattail spike is BROWN; {infl['rgb']} is not "
                                 f"(needs red > green > blue). Green or yellow spikes date "
                                 f"the scene to spring")
    if binomial == "Allium tricoccum":
        if ph != "leafless" or sp.get("form") != "scape_leafless" or fol is not None:
            rep.error(where, "Allium tricoccum in July is LEAFLESS: phenology 'leafless', "
                             "form 'scape_leafless', foliage_rgb null. Its leaves wither "
                             "before the scape rises, so green onion foliage in a July scene "
                             "is wrong")
    if ph == "past_bloom" and isinstance(infl, dict) and _rgb_ok(infl.get("rgb")) \
            and _carries_flower_colour(infl["rgb"]):
        rep.error(where, f"phenology 'past_bloom' with inflorescence {infl['rgb']} — a plant "
                         f"past bloom shows a fruit, not its flower colour")
    if ph == "fruiting" and isinstance(infl, dict) and not infl.get("fruit"):
        rep.error(where, "phenology 'fruiting' requires inflorescence.fruit true, so a reader "
                         "cannot mistake the colour for a flower")

    conf = check_attested(where, "species", sp, source_ids, rep)
    if conf:
        tally[conf] = tally.get(conf, 0) + 1


def check_flora(source_ids: set, field, rep: Report, tally: dict) -> dict:
    """Schema, provenance and phenology gate for data/flora/**."""
    index_path = FLORA / "index.json"
    if not index_path.exists():
        rep.note("flora: no data/flora/index.json — the walkthrough plants nothing")
        return {}
    index = load_json(index_path, rep)
    if not isinstance(index, dict):
        return {}

    scene_date = index.get("scene_date") or ""
    d = parse_date(scene_date)
    if d is None:
        rep.error("flora index", "scene_date must be an ISO date")
    elif d.month != 7:
        rep.error("flora index", f"scene_date {scene_date} is not in July, but every zone "
                                 f"record carries a 'july' phenology block. Move the "
                                 f"phenology, do not move the month")

    vocab = index.get("vocabulary") or {}
    for key in ("roles", "forms_flora", "forms_trees", "substrates", "phenology"):
        if not vocab.get(key):
            rep.error("flora index", f"vocabulary.{key} is missing — this validator reads "
                                     f"the block to hold every record to a closed set. It "
                                     f"once said 'the renderer reads this', and ROADMAP "
                                     f"K42 measured that it does not: of the seven "
                                     f"published vocabularies the renderer reads one, "
                                     f"inflorescence_shapes, which is not one of these five")

    palettes = {}
    for entry in index.get("palettes", []):
        pid, pfile = entry.get("id"), entry.get("file")
        path = FLORA / (pfile or "")
        if not pfile or not path.exists():
            rep.error("flora index", f"palette '{pid}' names {pfile}, which does not exist")
            continue
        pal = load_json(path, rep)
        if not isinstance(pal, dict):
            continue
        if pal.get("id") != pid or path.stem != pid:
            rep.error(f"flora palette {pid}", "id must match both the manifest and the filename")
        if pal.get("sources"):
            rep.error(f"flora palette {pid}", "a palette is render tuning, not evidence, and "
                                              "must not carry a source_id")
        greens = pal.get("greens") or []
        if len(greens) < 3 or not all(_rgb_ok(g) for g in greens):
            rep.error(f"flora palette {pid}", "greens must be a ramp of at least three "
                                              "[r,g,b] values")
        elif not all(_is_july_green(g) for g in greens):
            rep.error(f"flora palette {pid}", f"the foliage ramp {greens} is not all July "
                                              f"greens — a straw ramp is the October scene")
        palettes[pid] = pal

    zones = {}
    for entry in index.get("zones", []):
        zid, zfile = entry.get("id"), entry.get("file")
        path = FLORA / (zfile or "")
        if not zfile or not path.exists():
            rep.error("flora index", f"zone '{zid}' names {zfile}, which does not exist — a "
                                     f"static host cannot be globbed, so a manifest entry "
                                     f"without a file is a 404 on the deployed site")
            continue
        z = load_json(path, rep)
        if not isinstance(z, dict):
            continue
        where = f"flora zone {zid}"
        if z.get("id") != zid or path.stem != zid:
            rep.error(where, "id must match both the manifest entry and the filename stem")
        for key in ("zone", "name", "dossier", "scene_date", "palette", "cover", "ground",
                    "extent", "species", "confidence", "plantable_in_scene"):
            if key not in z:
                rep.error(where, f"missing required key '{key}'")
        if z.get("scene_date") != scene_date:
            rep.error(where, f"scene_date {z.get('scene_date')} disagrees with the manifest's "
                             f"{scene_date}; the phenology is stated FOR a date")
        if z.get("palette") not in palettes:
            rep.error(where, f"palette '{z.get('palette')}' does not resolve in the manifest")

        # the manifest carries denormalised copies so terrain.js needs one fetch;
        # a copy that has drifted is worse than no copy at all
        for key, actual in (("extent", z.get("extent")),
                            ("plantable_in_scene", z.get("plantable_in_scene")),
                            ("ground_rgb", (z.get("ground") or {}).get("rgb")),
                            ("ground_wet_rgb", (z.get("ground") or {}).get("wet_rgb")),
                            ("bare_soil_fraction",
                             (z.get("cover") or {}).get("bare_soil_fraction"))):
            if entry.get(key) != actual:
                rep.error("flora index", f"zone '{zid}' {key} in the manifest "
                                         f"({entry.get(key)!r}) disagrees with the zone record "
                                         f"({actual!r}); the zone record is authoritative")
        if entry.get("priority") != (z.get("extent") or {}).get("priority"):
            rep.error("flora index", f"zone '{zid}' priority in the manifest disagrees with "
                                     f"its extent")

        cover = z.get("cover") or {}
        for key in ("matrix_fraction", "bare_soil_fraction", "standing_water_fraction"):
            v = cover.get(key)
            if not isinstance(v, (int, float)) or not 0.0 <= v <= 1.0:
                rep.error(where, f"cover.{key} must be a fraction 0..1, got {v!r}")
        for key in ("rgb", "wet_rgb"):
            if not _rgb_ok((z.get("ground") or {}).get(key)):
                rep.error(where, f"ground.{key} must be [r,g,b] 0-255")

        # T-1056 — THE WOODY STRATUM'S ELEVATION BAND, GATED WHERE IT IS RECORDED.
        #
        # The sand zones carry a bound on where woody growth establishes, because
        # Andreas's timber exception is to the sandy HILLS and the bar across the
        # mouth is not one. It is an ecological claim with two recorded ends, so it
        # is checked exactly as an extent is: a real range, in metres above the
        # summer water surface, over roles this project actually draws, and graded.
        # An unrecognised role would be a bound that silently binds nothing, which
        # is the one failure a reader could not see in the walkthrough.
        ws = z.get("woody_stratum")
        if ws is not None:
            if not isinstance(ws, dict):
                rep.error(where, "woody_stratum must be an object carrying establishes_m, "
                                 "applies_to_roles and its own provenance")
            else:
                if not _num_range(ws.get("establishes_m"), -5.0, 50.0):
                    rep.error(where, "woody_stratum.establishes_m must be [low, high] metres "
                                     "above the summer water surface, low <= high, got "
                                     f"{ws.get('establishes_m')!r}")
                elif ws["establishes_m"][0] == ws["establishes_m"][1]:
                    rep.error(where, "woody_stratum.establishes_m is a single elevation, so it "
                                     "states a STEP; no source in this project gives one, and "
                                     "the band exists to keep the invention visible")
                roles = ws.get("applies_to_roles")
                if not isinstance(roles, list) or not roles:
                    rep.error(where, "woody_stratum.applies_to_roles must name the roles the "
                                     "bound binds; a bound over no role binds nothing")
                else:
                    known = set(vocab.get("roles") or [])
                    for r in roles:
                        if known and r not in known:
                            rep.error(where, f"woody_stratum.applies_to_roles names '{r}', "
                                             f"which is not in the index's role vocabulary")
                    bound = [sp for sp in z.get("species") or []
                             if sp.get("role") in set(roles)]
                    if not bound:
                        rep.error(where, "woody_stratum binds roles this zone records no "
                                         "species in, so the band is unreachable")
                # `measured_from` and not `datum`: the token `datum` occurs in nine
                # renderer files (data/datum.json is the scene's horizontal origin),
                # and tools/measure_layer_reads.py matches a figure's name against
                # the renderer text — so a field called `datum` reads as one the
                # renderers access, which is the opposite of true here.
                if not ws.get("measured_from"):
                    rep.error(where, "woody_stratum.measured_from must say what the metres are "
                                     "measured from; an elevation with no datum is a number")
                check_attested(where, "woody_stratum", ws, source_ids, rep)
                if ws.get("confidence") == "attested":
                    rep.error(where, "woody_stratum cannot be attested: no source in this "
                                     "project states an establishment elevation for lake sand. "
                                     "It is reasoned from two recorded ones and must say so")

        ext = z.get("extent") or {}
        kind = ext.get("kind")
        if kind not in EXTENT_KINDS:
            rep.error(where, f"extent.kind '{kind}' is not one of {EXTENT_KINDS}")
        if kind == "elevation_band" and not _num_range(ext.get("elev_m"), -50.0, 400.0):
            rep.error(where, "extent.elev_m must be [low,high] metres above the datum water")
        if kind == "polygon" and len(ext.get("polygon") or []) < 3:
            rep.error(where, "extent.polygon needs at least three vertices")
        if kind == "buffer":
            if ext.get("of") != "water":
                rep.error(where, "extent.of only takes 'water' — the renderer implements one "
                                 "buffer, and an unimplemented one silently plants nothing")
            if not _num_range(ext.get("distance_m"), 0.0, 2000.0):
                rep.error(where, "extent.distance_m must be [min,max] metres from the water")
        if not isinstance(ext.get("priority"), int):
            rep.error(where, "extent.priority must be an integer; higher wins on overlap")
        # Ground admitted by name rather than by the rule. A ring of two points is
        # a line and matches nothing, which would read in the record as a claim
        # the renderer silently declines to draw.
        for key in ("include_polygons", "exclude_polygons"):
            rings = ext.get(key)
            if rings is None:
                continue
            if not isinstance(rings, list):
                rep.error(where, f"extent.{key} must be a list of rings")
                continue
            for i, patch in enumerate(rings):
                if not isinstance(patch, list) or len(patch) < 3:
                    rep.error(where, f"extent.{key}[{i}] needs at least three vertices")
        check_attested(where, "extent", ext, source_ids, rep)

        seen: set = set()
        matrix_max = 0.0
        for sp in z.get("species") or []:
            if sp.get("id") in seen:
                rep.error(where, f"duplicate species id '{sp.get('id')}' in this zone")
            seen.add(sp.get("id"))
            check_flora_species(zid, sp, source_ids, vocab, rep, tally, ext)
            if sp.get("role") in ("matrix", "ground"):
                cf = (sp.get("abundance") or {}).get("cover_fraction")
                if isinstance(cf, list) and len(cf) == 2:
                    matrix_max += cf[1]
        if not seen:
            rep.error(where, "a zone with no species is not a community record")
        if matrix_max > 1.8:
            rep.warn(where, f"matrix and ground cover fractions sum to {matrix_max:.2f} at "
                            f"their maxima; some overlap is real, this much is a bookkeeping "
                            f"error")
        if cover.get("matrix_fraction", 0) >= 0.5 and not any(
                sp.get("role") in ("matrix", "emergent") for sp in z.get("species") or []):
            rep.error(where, "the zone claims a graminoid matrix but lists no matrix or "
                             "emergent species to build it from")
        check_attested(where, "zone", z, source_ids, rep)
        zones[zid] = z

    check_flora_extents(zones, field, rep)

    # Honesty ledger: how much of the species record rests on a source nobody in
    # this project has actually opened. Not an error — a bibliographic record for
    # a work the dossier cites is legitimate — but it is the number a reader
    # should see rather than have to compute.
    unverified = {sid for sid, s in ((Path(p).stem, json.loads(Path(p).read_text()))
                                     for p in sorted((DATA / "sources").glob("*.json")))
                  if not s.get("verified")}
    resting = 0
    for z in zones.values():
        for sp in z.get("species") or []:
            srcs = sp.get("sources") or []
            if sp.get("confidence") == "attested" and srcs and set(srcs) <= unverified:
                resting += 1
    total_sp = sum(len(z.get("species") or []) for z in zones.values())
    if total_sp:
        rep.note(f"flora: {len(zones)} zone(s), {total_sp} species record(s); {resting} "
                 f"documented claim(s) rest only on sources no agent has retrieved "
                 f"(verified false) — real citations, unread")
    return zones


# --------------------------------------------------------------------------
# fauna: zone records, presence modes, and the July gate
# --------------------------------------------------------------------------
#
# The flora section above exists because a mid-July prairie is easy to render as
# a September one. This one exists for the mirror-image reason: a mid-July
# Chicago is easy to render as a May one. Every headline wildlife event in the
# record — passenger-pigeon flights, prairie-chicken booming, waterfowl clouds,
# the spring dawn chorus — is a spring, autumn or winter phenomenon, and 1 July
# is the QUIETEST wildlife date in the Chicago year. docs/research/08-fauna.md
# § 0.3 states that as guidance; the rules below make the wrong record
# unrepresentable rather than merely discouraged, exactly as the phenology gate
# does for the flora.
#
# The second thing this section enforces is that "present" and "visible" are
# different claims. Liberty L2 licenses fauna at low density and often as sound
# only, and that liberty is worth nothing unless the data can SAY "here, and not
# seen" — which is what `presence.mode` is for.

FAUNA = DATA / "fauna"

FAUNA_CLASSES = ("mammal", "bird", "fish", "amphibian", "reptile", "insect", "mollusc")
FAUNA_ACTIVITY = ("diurnal", "crepuscular", "nocturnal", "cathemeral")
FAUNA_PERIODS = ("dawn", "day", "dusk", "night")
FAUNA_STATUS = ("breeding_resident", "year_round_resident", "post_breeding_dispersal",
                "flightless_moult", "domestic", "feral_or_commensal", "doubtful",
                "absent_seasonal", "absent_extirpated", "absent_anachronism",
                "excluded_by_scope")
FAUNA_PRESENCE = ("visible", "audible", "visible_and_audible", "trace_only",
                  "not_perceptible", "absent", "not_depicted")
FAUNA_ABUNDANCE = ("abundant", "common", "frequent", "uncommon", "sparse", "rare", "absent")
FAUNA_VOICE = ("song_full", "song_reduced", "call_only", "chorus", "display_over",
               "silent", "non_vocal")
FAUNA_DAWN_CHORUS = ("none", "reduced")

# A status that says the animal is not in the scene, and the presence mode each
# of those two families must carry. Kept as two sets because they are different
# findings: `absent` is "not here", `not_depicted` is "here and we chose not to
# show it", and collapsing them would lose the distinction liberty L1 rests on.
FAUNA_ABSENT_STATUS = ("absent_seasonal", "absent_extirpated", "absent_anachronism")
FAUNA_ABSENT_MODES = ("absent",)
FAUNA_WITHHELD_STATUS = ("excluded_by_scope",)
FAUNA_WITHHELD_MODES = ("not_depicted",)

# A voice that does not reach a listener. A species recorded as audible must not
# have one of these, or the record claims a sound nobody could hear.
FAUNA_INAUDIBLE = ("silent", "display_over", "non_vocal")

# THE BIRD-SONG GATE. Named species whose song or display is over, or sharply
# reduced, by 1 July — the direct analogue of JULY_VEGETATIVE_GRASSES. Value is
# the set of voices the record is allowed to claim. Getting this wrong does not
# look wrong: a scene full of birdsong reads as "summer" to every viewer and is
# a May scene.
JULY_QUIET_BIRDS = {
    # The lek is silent from June. This is the fauna dossier's headline trap.
    "Tympanuchus cupido": {"display_over", "silent"},
    # Song stops as the young fledge in early July; the chatter carries on.
    "Icterus galbula": {"call_only", "silent"},
    # An April-to-June performance, finished before this date.
    "Toxostoma rufum": {"call_only", "song_reduced", "silent"},
    # Collapses through July as the birds move to moult.
    "Dolichonyx oryzivorus": {"song_reduced", "call_only", "silent"},
    # No song to lose in any month — calls are the whole vocabulary.
    "Cyanocitta cristata": {"call_only", "silent"},
    "Poecile atricapillus": {"call_only", "silent"},
    "Tyrannus tyrannus": {"call_only", "silent"},
    # Drumming and the long territorial call are spring signals.
    "Melanerpes erythrocephalus": {"call_only", "silent"},
    "Colaptes auratus": {"call_only", "silent"},
    # Vultures are effectively voiceless.
    "Cathartes aura": {"silent", "non_vocal"},
    # Not a songbird at all, whatever the flights looked like.
    "Ectopistes migratorius": {"call_only", "silent"},
}

# ...and the positive half, which is what stops a gate like this being satisfied
# by rendering July silent. These species ARE in full song on 1 July — later
# than almost anything else — and recording them mute is the opposite error.
JULY_STILL_SINGING = ("Contopus virens", "Passerina cyanea", "Hylocichla mustelina",
                      "Geothlypis trichas", "Spizella pusilla", "Colinus virginianus")

# The same gate one class down. These frogs call from March to May and are done
# by 1 July — the species is still in the landscape and its VOICE is not, which
# for a frog is the whole of what a scene would carry. A peeper chorus is the
# easiest wrong sound to lay over any Illinois marsh at any date.
FAUNA_SPRING_CHORUS_OVER = ("Pseudacris crucifer", "Pseudacris maculata",
                            "Pseudacris triseriata", "Lithobates sylvaticus")

# Wing moult. Adult ducks enter simultaneous flight-feather moult in late June
# and July and are flightless or nearly so: dull, skulking, and NOT flying.
FAUNA_MOULTING_WATERFOWL = ("Anas platyrhynchos", "Spatula discors", "Aix sponsa",
                            "Mareca strepera", "Anas acuta", "Aythya americana")
FAUNA_MOULT_MAX_GROUP = 12

# The species whose real abundance sounds like an exaggeration, which is exactly
# why the July number has to be held down by the schema rather than by taste.
PASSENGER_PIGEON = "Ectopistes migratorius"
PASSENGER_PIGEON_JULY_MAX = 60

# Present in the period but nothing like its modern numbers. The default modern
# Chicago gull is a post-1916 phenomenon and a flock of them is the single most
# visible anachronism available at the river mouth.
FAUNA_RARE_ONLY = {"Larus delawarensis": ("rare", "absent")}

# NOT AT THIS PLACE ON THIS DATE, and the dataset may not say otherwise. These
# are the dossier's § 6 negative findings turned into schema: a record may state
# any of them as an ABSENCE — that is what the negative findings are for, and
# recording why something is missing is the whole standard — but it may not put
# the animal in the scene. Without this, a beaver lodge could be added at the
# forks by editing one field, which is exactly the difference between a rule a
# modeller should follow and a record that cannot be written.
FAUNA_ABSENT_TAXA = {
    "Bison bison": "no wild bison remained in Illinois by about 1830",
    "Bos bison": "the period name for the bison; extirpated from Illinois by about 1830",
    "Cervus canadensis": "elk were gone from Illinois by the early 1800s",
    "Castor canadensis": "no Chicago-proper 1830s beaver record exists; the nearest attested "
                         "population was the Calumet region, twelve or more miles south. No "
                         "beaver, no lodges, and no beaver-cut stumps at the forks",
    "Puma concolor": "probably exterminated in Illinois before 1870 and locally far earlier",
    "Ursus americanus": "Chicago-area bear records end in the 1830s and are anecdotal; none is "
                        "datable to 1835",
    "Passer domesticus": "introduced to North America in 1851, sixteen years after this scene",
    "Sturnus vulgaris": "introduced to North America in 1890",
    "Cyprinus carpio": "the common carp was not stocked in North America in numbers until the "
                       "1870s; Andreas's 'twelve carps' are native minnows in period usage",
    "Magicicada septendecim": "northern Illinois is 17-year Brood XIII and its years are 1820, "
                              "1837 and 1854 — not 1835 — and it emerges in late May and June "
                              "in any case",
    "Magicicada cassinii": "as Magicicada septendecim: Brood XIII, and 1835 is not a brood year",
    "Magicicada septendecula": "as Magicicada septendecim: Brood XIII, and 1835 is not a brood "
                               "year",
}

# Words that name a spring, autumn or winter spectacle. Forbidden in `behaviour`
# — the render instruction — for any species the record says is present. A
# negative record may say them freely, because saying what is NOT here is the
# whole job of a negative record.
FAUNA_WRONG_SEASON_WORDS = ("migrat", "skein", "v-formation", "sky-darken",
                            "booming", "lek", "raft of", "dawn chorus", "rut")


def _fauna_val(node, key: str):
    """The value of an attested block, or of a bare value."""
    v = node.get(key)
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


def check_fauna_species(zid: str, sp: dict, source_ids: set, vocab: dict,
                        rep: Report, tally: dict) -> None:
    where = f"fauna zone {zid}/{sp.get('id', '?')}"
    binomial = (sp.get("binomial") or "").strip()
    for key in ("id", "binomial", "common", "class", "activity", "active_periods",
                "july", "confidence"):
        if key not in sp:
            rep.error(where, f"missing required key '{key}'")
            return
    if not SLUG.match(sp["id"] or ""):
        rep.error(where, f"id '{sp['id']}' is not a lowercase slug")
    if sp["class"] not in (vocab.get("classes") or FAUNA_CLASSES):
        rep.error(where, f"class '{sp['class']}' is not declared in index.json's vocabulary")
    if sp["activity"] not in (vocab.get("activity") or FAUNA_ACTIVITY):
        rep.error(where, f"activity '{sp['activity']}' is not one of {FAUNA_ACTIVITY}")

    periods = sp.get("active_periods")
    if not isinstance(periods, list) or not periods \
            or any(p not in FAUNA_PERIODS for p in periods):
        rep.error(where, f"active_periods must be a non-empty subset of {FAUNA_PERIODS}, "
                         f"got {periods!r}")
        periods = []
    # An animal on screen at an hour its own activity pattern excludes is the
    # commonest way a reconstruction quietly invents behaviour. Say cathemeral
    # and mean it — the Chicago coyotes are documented abroad in daylight, and
    # that is a finding, not a default.
    act = sp["activity"]
    if act == "diurnal" and "night" in periods:
        rep.error(where, "activity 'diurnal' with 'night' in active_periods — use 'cathemeral' "
                         "and say on the record why this animal is abroad after dark")
    if act == "nocturnal" and "day" in periods:
        rep.error(where, "activity 'nocturnal' with 'day' in active_periods — use 'cathemeral'. "
                         "A nocturnal animal on screen at noon is a claim, and it needs to be "
                         "made explicitly (the Chicago coyote is exactly that case: Andreas has "
                         "one entering a meat-house IN THE DAY TIME)")
    if act == "crepuscular":
        if "day" in periods:
            rep.error(where, "activity 'crepuscular' with 'day' in active_periods — use "
                             "'cathemeral'; crepuscular means the light margins, not midday")
        if not ({"dawn", "dusk"} & set(periods)):
            rep.error(where, "activity 'crepuscular' but neither dawn nor dusk is in "
                             "active_periods")
    if act == "diurnal" and "day" not in periods:
        rep.error(where, "activity 'diurnal' without 'day' in active_periods")

    j = sp.get("july")
    if not isinstance(j, dict):
        rep.error(where, "july must be the block stating this animal's state on the scene date")
        return
    for key in ("status", "presence", "abundance", "max_group", "vocalization",
                "behaviour", "appearance"):
        if key not in j:
            rep.error(where, f"july.{key} is required — the whole point of this dataset is "
                             f"that the July state is stated rather than assumed")
            return
    if "trace" not in j:
        rep.error(where, "july.trace must be present, null when the animal leaves no rendered "
                         "sign — an absent key hides the claim, exactly as it does for flora "
                         "inflorescence")

    status = _fauna_val(j, "status")
    mode = _fauna_val(j, "presence")
    abundance = _fauna_val(j, "abundance")
    voice = j.get("vocalization")
    group = j.get("max_group")
    behaviour = (j.get("behaviour") or "").strip()
    appearance = (j.get("appearance") or "").strip()

    if status not in FAUNA_STATUS:
        rep.error(where, f"july.status '{status}' is not one of {FAUNA_STATUS}")
    if mode not in FAUNA_PRESENCE:
        rep.error(where, f"july.presence '{mode}' is not one of {FAUNA_PRESENCE}")
    if abundance not in FAUNA_ABUNDANCE:
        rep.error(where, f"july.abundance '{abundance}' is not one of {FAUNA_ABUNDANCE}")
    if voice not in FAUNA_VOICE:
        rep.error(where, f"july.vocalization '{voice}' is not one of {FAUNA_VOICE}")
    if not isinstance(group, int) or isinstance(group, bool) or not 0 <= group <= 500:
        rep.error(where, f"july.max_group must be an integer 0..500 (0 = nothing is placed), "
                         f"got {group!r}")
        group = 0
    if not behaviour:
        rep.error(where, "july.behaviour is the render instruction and may not be empty; write "
                         "'Nothing is drawn.' when that is the answer")
    if not appearance:
        rep.error(where, "july.appearance is what a critic reads to decide whether the render "
                         "matches the record; it may not be empty")

    # --- present, absent, and withheld are three different claims -----------
    #
    # ...and `doubtful` is the fourth, which is why it is exempt from the
    # coupling below. A species whose July presence is genuinely uncertain may
    # be recorded with NOTHING placed for it without that being a finding of
    # absence — the ring-billed gull is the case: rare and persecuted in the
    # 19th century, tempting to a renderer, and neither attested nor refuted
    # here. Forcing that record to choose between "present" and "absent" would
    # make the dataset resolve a question the evidence does not.
    if status == "doubtful":
        pres = j.get("presence")
        if not (isinstance(pres, dict) and (pres.get("note") or "").strip()):
            rep.error(where, "july.status 'doubtful' requires a note on the presence block "
                             "saying what the doubt is and what the scene does about it. "
                             "Recording doubt is the point; recording it silently is not")
    elif status in FAUNA_ABSENT_STATUS:
        if mode not in FAUNA_ABSENT_MODES:
            rep.error(where, f"july.status '{status}' says this animal is not in the scene, but "
                             f"july.presence is '{mode}'. A negative finding that leaves a "
                             f"visible animal on the record is worse than no finding")
        if abundance != "absent":
            rep.error(where, f"july.status '{status}' with abundance '{abundance}' — an animal "
                             f"that is not here has no abundance")
        if group:
            rep.error(where, f"july.status '{status}' with max_group {group} — nothing may be "
                             f"placed for a species recorded as absent")
    elif status in FAUNA_WITHHELD_STATUS:
        if mode not in FAUNA_WITHHELD_MODES:
            rep.error(where, f"july.status 'excluded_by_scope' requires presence 'not_depicted' "
                             f"— the animal IS here and is deliberately not shown, which is a "
                             f"different claim from absence and must not be recorded as one")
        if group:
            rep.error(where, "an excluded_by_scope record may not place anything (max_group 0)")
    else:
        if mode in ("absent", "not_depicted"):
            rep.error(where, f"july.presence '{mode}' with a present status '{status}' — say "
                             f"which absence this is: absent_seasonal, absent_extirpated, "
                             f"absent_anachronism, or excluded_by_scope")
        if abundance == "absent":
            rep.error(where, f"abundance 'absent' with a present status '{status}'")

    # --- present, and not seen ---------------------------------------------
    if mode in ("audible", "visible_and_audible") and voice in FAUNA_INAUDIBLE:
        rep.error(where, f"july.presence '{mode}' claims this animal is HEARD, but its "
                         f"vocalization is '{voice}'. A silent bird cannot be audible, and a "
                         f"lek whose season is over is silent by definition")
    if mode == "trace_only" and not (j.get("trace") or "").strip():
        rep.error(where, "july.presence 'trace_only' requires july.trace to describe the sign "
                         "that IS rendered — runways, burrows, shell scatter, a landed fish. "
                         "Trace-only with no trace renders nothing and claims something")
    if mode == "not_perceptible" and not (
            (j.get("presence") or {}).get("note") if isinstance(j.get("presence"), dict) else None):
        rep.error(where, "july.presence 'not_perceptible' says the animal is here and neither "
                         "seen nor heard, which is the strongest claim in this vocabulary and "
                         "needs a note on the presence block saying why")

    # --- the July gate ------------------------------------------------------
    if sp["class"] == "bird" and voice == "song_full":
        note = (sp.get("note") or "")
        if "July" not in note:
            rep.error(where, "vocalization 'song_full' on a bird is the EXCEPTIONAL claim for "
                             "1 July — the dawn chorus is a spring phenomenon and most "
                             "passerines have stopped or sharply reduced singing by now. The "
                             "record must argue it: put the reason, mentioning July, in the "
                             "species note")
    if binomial in JULY_QUIET_BIRDS and voice not in JULY_QUIET_BIRDS[binomial]:
        rep.error(where, f"{binomial} is not in song on 1 July; this record claims '{voice}'. "
                         f"Allowed: {sorted(JULY_QUIET_BIRDS[binomial])}. A July scene full of "
                         f"birdsong is the fauna equivalent of seed heads on July big bluestem")
    if binomial in JULY_STILL_SINGING and voice in ("silent", "display_over"):
        rep.error(where, f"{binomial} IS still in song on 1 July — later than almost anything "
                         f"else — and recording it silent over-corrects the July gate into a "
                         f"different error")
    if binomial in FAUNA_SPRING_CHORUS_OVER and voice not in ("silent", "non_vocal"):
        rep.error(where, f"{binomial} calls from March to May and is finished by 1 July; this "
                         f"record claims '{voice}'. The animal may still be recorded as "
                         f"present — it is in the landscape — but its chorus is a spring "
                         f"sound and putting it over a July marsh dates the scene by two "
                         f"months")
    if binomial in FAUNA_MOULTING_WATERFOWL and status not in FAUNA_ABSENT_STATUS:
        if status != "flightless_moult":
            rep.error(where, f"{binomial} is in simultaneous wing moult in late June and July "
                             f"and is flightless or nearly so; july.status must be "
                             f"'flightless_moult', not '{status}'. There are no migrating "
                             f"flocks on 1 July and the adults are dull, skulking and not "
                             f"flying")
        if group > FAUNA_MOULT_MAX_GROUP:
            rep.error(where, f"{binomial} with max_group {group} — a moulting July duck is a "
                             f"hen with a brood, not a raft. Ceiling is "
                             f"{FAUNA_MOULT_MAX_GROUP}")
    if binomial == PASSENGER_PIGEON and status not in FAUNA_ABSENT_STATUS:
        if status != "post_breeding_dispersal":
            rep.error(where, "the passenger pigeon on 1 July is in small wandering "
                             "post-breeding flocks, not nesting and not on passage; "
                             "july.status must be 'post_breeding_dispersal'")
        if group > PASSENGER_PIGEON_JULY_MAX:
            rep.error(where, f"max_group {group} for the passenger pigeon. The Chicago record "
                             f"of a sky full of them — 'the horizon in almost every direction "
                             f"was black with them' — is dated 17 SEPTEMBER 1836, a fall "
                             f"movement. On 1 July the number is tens, not millions; the "
                             f"ceiling here is {PASSENGER_PIGEON_JULY_MAX}")
        if not (sp.get("note") or "").strip():
            rep.error(where, "the passenger pigeon needs its numbers argued on the record more "
                             "than any other species in this dataset, because its real "
                             "abundance sounds like exaggeration. State what the source "
                             "actually says, and when it says it")
    if binomial in FAUNA_ABSENT_TAXA and status not in FAUNA_ABSENT_STATUS:
        rep.error(where, f"{binomial} is not at the Chicago town site on 1 July 1835: "
                         f"{FAUNA_ABSENT_TAXA[binomial]}. The record may state this species as "
                         f"an absence — a negative finding is worth keeping — but it may not "
                         f"put the animal in the scene")
    if binomial in FAUNA_RARE_ONLY and abundance not in FAUNA_RARE_ONLY[binomial]:
        rep.error(where, f"{binomial} may only be recorded as "
                         f"{' or '.join(FAUNA_RARE_ONLY[binomial])} in an 1835 scene — it was "
                         f"rare and persecuted in the 19th century and became the abundant "
                         f"Great Lakes gull only after protection in 1916")
    if status not in FAUNA_ABSENT_STATUS and status not in FAUNA_WITHHELD_STATUS:
        low = behaviour.lower()
        for word in FAUNA_WRONG_SEASON_WORDS:
            if word in low:
                rep.error(where, f"july.behaviour names '{word}', which is a spring, autumn or "
                                 f"winter phenomenon. 1 July is the annual minimum for all of "
                                 f"them: no migration, silent leks, moulting waterfowl. Say it "
                                 f"in the note if it needs saying; it may not be a render "
                                 f"instruction")
    if status == "doubtful" and sp.get("confidence") == "attested":
        rep.error(where, "july.status 'doubtful' with confidence 'attested' — if the July "
                         "presence is in doubt the record cannot also be documented. Record the "
                         "doubt rather than resolving it by preference")

    # --- provenance ---------------------------------------------------------
    walk_attested(where, j, source_ids, rep, tally, "july")
    conf = check_attested(where, "species", sp, source_ids, rep)
    if conf:
        tally[conf] = tally.get(conf, 0) + 1
    if conf == "reconstructed" and not (sp.get("note") or "").strip():
        rep.error(where, "conjectural requires a note saying what the belief rests on and that "
                         "it is not evidence. Unknown is recorded as unknown, never left blank")


def check_fauna(source_ids: set, rep: Report, tally: dict) -> dict:
    """Schema, provenance and the July gate for data/fauna/**."""
    index_path = FAUNA / "index.json"
    if not index_path.exists():
        rep.note("fauna: no data/fauna/index.json — the scene carries no animals")
        return {}
    index = load_json(index_path, rep)
    if not isinstance(index, dict):
        return {}

    scene_date = index.get("scene_date") or ""
    d = parse_date(scene_date)
    if d is None:
        rep.error("fauna index", "scene_date must be an ISO date")
    elif d.month != 7:
        rep.error("fauna index", f"scene_date {scene_date} is not in July, but every zone "
                                 f"record carries a 'july' block stating what each animal is "
                                 f"doing on the scene date. Move the seasonal states, do not "
                                 f"move the month")

    vocab = index.get("vocabulary") or {}
    for key in ("classes", "activity", "active_periods", "july_status", "presence_modes",
                "abundance", "vocalization", "habitats"):
        if not vocab.get(key):
            rep.error("fauna index", f"vocabulary.{key} is missing — this validator reads "
                                     f"the block to hold every record to a closed set. No "
                                     f"renderer reads any of it: ROADMAP K42 measured that "
                                     f"nothing under renderers/ opens data/fauna at all, "
                                     f"and publish.sh does not put it on the site")

    # The fauna zones borrow their geometry from the flora zones rather than
    # restating it, so the two datasets cannot drift into describing different
    # ground. That only holds if the reference is checked.
    flora_index = load_json(FLORA / "index.json", rep, required=False)
    flora_zones = {z.get("id"): z for z in (flora_index or {}).get("zones", [])} \
        if isinstance(flora_index, dict) else {}

    zones = {}
    for entry in index.get("zones", []):
        zid, zfile = entry.get("id"), entry.get("file")
        path = FAUNA / (zfile or "")
        if not zfile or not path.exists():
            rep.error("fauna index", f"zone '{zid}' names {zfile}, which does not exist — a "
                                     f"static host cannot be globbed, so a manifest entry "
                                     f"without a file is a 404 on the deployed site")
            continue
        z = load_json(path, rep)
        if not isinstance(z, dict):
            continue
        where = f"fauna zone {zid}"
        if z.get("id") != zid or path.stem != zid:
            rep.error(where, "id must match both the manifest entry and the filename stem")
        for key in ("zone", "name", "habitat", "dossier", "scene_date", "reads_as",
                    "in_modelled_extent", "extent_from", "soundscape", "species",
                    "confidence", "note"):
            if key not in z:
                rep.error(where, f"missing required key '{key}'")
        if z.get("scene_date") != scene_date:
            rep.error(where, f"scene_date {z.get('scene_date')} disagrees with the manifest's "
                             f"{scene_date}; every july block is stated FOR a date")
        if z.get("habitat") not in (vocab.get("habitats") or []):
            rep.error(where, f"habitat '{z.get('habitat')}' is not declared in the manifest "
                             f"vocabulary")

        # denormalised copies, checked the way the flora manifest's are
        for key, actual in (("habitat", z.get("habitat")),
                            ("in_modelled_extent", z.get("in_modelled_extent")),
                            ("extent_from", z.get("extent_from"))):
            if entry.get(key) != actual:
                rep.error("fauna index", f"zone '{zid}' {key} in the manifest "
                                         f"({entry.get(key)!r}) disagrees with the zone record "
                                         f"({actual!r}); the zone record is authoritative")
        if entry.get("species_count") != len(z.get("species") or []):
            rep.error("fauna index", f"zone '{zid}' species_count {entry.get('species_count')!r} "
                                     f"disagrees with the {len(z.get('species') or [])} species "
                                     f"in the record")

        ext = z.get("extent_from") or {}
        fz = ext.get("flora_zone")
        if fz is None:
            if ext.get("kind") != "water":
                rep.error(where, "extent_from must name a flora_zone whose extent this zone "
                                 "shares, or declare kind 'water'. A fauna zone does not "
                                 "restate a polygon: two datasets describing the same ground in "
                                 "two places drift, and then nobody knows which is the town")
        elif flora_zones and fz not in flora_zones:
            rep.error(where, f"extent_from.flora_zone '{fz}' does not resolve in "
                             f"data/flora/index.json")
        elif fz in flora_zones:
            plantable = flora_zones[fz].get("plantable_in_scene")
            if z.get("in_modelled_extent") != plantable:
                rep.error(where, f"in_modelled_extent is {z.get('in_modelled_extent')!r} but "
                                 f"flora zone '{fz}', whose extent this zone shares, is "
                                 f"plantable_in_scene {plantable!r}. The same ground cannot be "
                                 f"inside the modelled box for one dataset and outside it for "
                                 f"the other")

        # --- the soundscape gate -------------------------------------------
        snd = z.get("soundscape")
        if not isinstance(snd, dict):
            rep.error(where, "soundscape is required: a July zone has to state what it SOUNDS "
                             "like, because most of its animals are audible and not visible")
        else:
            dc = snd.get("dawn_chorus")
            if dc not in FAUNA_DAWN_CHORUS:
                rep.error(where, f"soundscape.dawn_chorus '{dc}' is not one of "
                                 f"{FAUNA_DAWN_CHORUS}. There is no third option: the full dawn "
                                 f"chorus is a spring phenomenon and by 1 July most breeding "
                                 f"passerines have stopped or sharply reduced singing. A zone "
                                 f"cannot declare one")
            if not (snd.get("note") or "").strip():
                rep.error(where, "soundscape needs a note saying what July does to this zone's "
                                 "sound — the reduction is the finding")
            heroes = snd.get("hero") or []
            ids = {s.get("id") for s in z.get("species") or []}
            for h in heroes:
                if h not in ids:
                    rep.error(where, f"soundscape.hero names '{h}', which is not a species in "
                                     f"this zone")

        seen: set = set()
        n_birds = n_full = 0
        for sp in z.get("species") or []:
            if sp.get("id") in seen:
                rep.error(where, f"duplicate species id '{sp.get('id')}' in this zone")
            seen.add(sp.get("id"))
            check_fauna_species(zid, sp, source_ids, vocab, rep, tally)
            if sp.get("class") == "bird":
                n_birds += 1
                if (sp.get("july") or {}).get("vocalization") == "song_full":
                    n_full += 1
        if not seen:
            rep.error(where, "a zone with no species is not a fauna record")
        if n_birds and n_full * 2 > n_birds:
            rep.warn(where, f"{n_full} of {n_birds} birds in this zone are in full song on "
                            f"1 July. That is most of them, and by July most breeding birds "
                            f"have stopped — check each one against its own July biology "
                            f"rather than against the habitat")
        check_attested(where, "zone", z, source_ids, rep)
        zones[zid] = z

    # A species is one animal wherever it appears; a binomial that changes
    # between zones means two records that look like one to any renderer that
    # keys on the id.
    binomials: dict = {}
    for zid, z in zones.items():
        for sp in z.get("species") or []:
            sid, b = sp.get("id"), sp.get("binomial")
            if sid in binomials and binomials[sid][0] != b:
                rep.error(f"fauna zone {zid}/{sid}",
                          f"binomial '{b}' disagrees with '{binomials[sid][0]}' for the same "
                          f"species id in {binomials[sid][1]}")
            binomials.setdefault(sid, (b, zid))

    total = sum(len(z.get("species") or []) for z in zones.values())
    if total:
        heard = sum(1 for z in zones.values() for s in z.get("species") or []
                    if (s.get("july") or {}).get("presence", {}).get("value")
                    if isinstance((s.get("july") or {}).get("presence"), dict))
        unseen = sum(1 for z in zones.values() for s in z.get("species") or []
                     if _fauna_val(s.get("july") or {}, "presence")
                     in ("audible", "trace_only", "not_perceptible"))
        gone = sum(1 for z in zones.values() for s in z.get("species") or []
                   if str(_fauna_val(s.get("july") or {}, "status")).startswith("absent")
                   or _fauna_val(s.get("july") or {}, "status") == "excluded_by_scope")
        rep.note(f"fauna: {len(zones)} zone(s), {total} species record(s); {unseen} present and "
                 f"NOT SEEN (audible, trace or imperceptible), {gone} recorded as absent or "
                 f"withheld — liberty L2 in the data (of {heard} with an attested presence)")
    return zones


# --------------------------------------------------------------------------
# residents: households, persons and the accuracy grade
# --------------------------------------------------------------------------
#
# docs/ROADMAP.md K1. The population is what justifies the buildings: every
# household that needs a dwelling eventually becomes a structure record on the
# plat. This section gates the dataset that carries them.
#
# TWO ORTHOGONAL AXES, AND THE WHOLE SECTION EXISTS BECAUSE THEY ARE DIFFERENT
# QUESTIONS. `confidence` is the project's per-attribute evidence grade and is
# checked by check_attested exactly as it is on a roof pitch. `grade` belongs to
# a PERSON and says how much of that person is reconstructed:
#
#   documented  a source names this person
#   derived     a real, named person whose details are partly reconstructed
#   inferred    a hypothesised resident filling a demonstrable need of the town
#
# The word "recommended" is NOT in this vocabulary. The programme was renamed
# away from it on 2026-08-13 and the rename is enforced by name below, because a
# vocabulary that merely omits a word gets it back the first time somebody
# copies an older file.
#
# The gate that actually protects the scene is the arrival date. A person who
# arrived in September 1835 is not in a scene set on 1 July 1835, and the
# failure mode is silent: nothing about a household record looks wrong when its
# subject was still in Vermont. Arrival values carry a `precision` because the
# sources give years far more often than days - and one of those precisions,
# `either_of_two_days`, exists for a source that gives two and declines to pick.
# The rule is asymmetric on
# purpose - the EARLIEST day a value permits must not be after the scene date
# (an error), and a value whose LATEST day is after it earns a warning rather
# than a failure, because "1835" with no month is a real state of the evidence
# and not a mistake.

RESIDENTS = DATA / "residents"

RESIDENT_GRADES = ("attested", "inferred", "reconstructed")
# The grades that make a value a CLAIM, and so the grades that may fill the
# generated 1835 role view. Same reading as
# tools/audit_scene_window_trades.CLAIMING: `reconstructed` is this dataset's
# word for a figure the reconstruction supplies rather than a source.
CLAIMING_GRADES = ("attested", "documented", "inferred")
RESIDENT_SCENE_DATE = "1835-07-01"

# Which of the three mint tools produced this record, recorded now that a
# plain id no longer says so on its own (T-0599: mint_documented_residents.py /
# mint_placed_residents.py / mint_letter_list_residents.py used to encode this
# as an hh_doc_/hh_placed_/hh_ll_ filename prefix; a household minted from here
# on carries this field instead and gets a plain hh_<surname>_<given> id). This
# is provenance for the mint tools' own idempotency, not a finding about the
# person, so it stays optional and off the manifest's public vocabulary block:
# the ~70-odd hand-authored households were never minted by any pass and never
# carry the key at all.
RESIDENT_SOURCE_PASSES = ("documented", "placed", "letter_list", "civic")

# The per-domain evidence blocks tools/mint_civic_residents.py writes onto a person
# (T-0514). Each row is a READING: the list it came from, the transcription as read,
# the locator, the record id, the source it resolves to and the ladder rule that fired
# for the identity. They are what makes a minted person auditable back to a page, so
# the shape is checked rather than trusted — a row that loses its `as_read` or its
# `rule` is a person whose card asserts a grade it can no longer show the working for.
RESIDENT_EVIDENCE_BLOCKS = ("civic_evidence", "census_evidence", "church_evidence",
                            "book_evidence", "press_evidence")
RESIDENT_EVIDENCE_ROW_KEYS = ("list", "as_read", "locator", "record_id",
                              "describes_date", "source", "rule")

# The term this programme was renamed away from. Anything mapping to a grade
# gets a message naming the rename rather than a generic "unknown value", so the
# next person to reach for it learns why.
RETIRED_GRADE_TERMS = ("recommended", "recommendation", "suggested")

RESIDENT_PRECISION = ("day", "either_of_two_days", "month", "season", "year",
                      "not_later_than")

# T-1229 (of T-1145). A ROLE IS PLURAL, DATED, AND CANNOT BE WIDENED TO THE SCENE DATE.
# `persons[].roles[]` is canonical and `persons[].occupation` is a generated view of the
# roles covering 1835-07-01; tools/derive_resident_roles.py writes both. These are the
# closed sets the manifest must declare and a row must speak, and they are checked here
# rather than only in the generator because a hand edit to a card never runs it.
RESIDENT_ROLE_KINDS = ("trade", "profession", "office", "employment", "business_interest")
RESIDENT_ROLE_PRECISION = ("day", "month", "year", "source_span", "unknown")
RESIDENT_ROLE_DATED_BY = ("source_describes_date", "printing_year", "stated_date",
                          "undated")
RESIDENT_ROLE_KEYS = ("role", "kind", "as_printed", "from", "to", "precision",
                      "dated_by", "covers_scene_date", "confidence", "sources", "claim",
                      "note")

# `either_of_two_days` is what a source looks like when it will not choose. Hurlbut
# prints Hubbard as arriving at Chicago "on the last day of October or first day of
# November" of 1818 - two adjacent days, offered as alternatives, and neither of them
# preferred. Every coarser precision here is a LIE about that sentence in one of two
# directions: `day` picks one of the two on the reader's behalf, and `month`, `season`
# or `year` widen a claim that is already exact to within a day in order to contain
# both. The value is the EARLIER of the two days and the bound runs to the day after
# it, so the record keeps the source's own precision AND its own refusal.

# A season, in days, for bounding a "spring of 1833" arrival. Deliberately
# generous: the point is to bound the claim, not to date it.
SEASON_DAYS = 92

# The floor for a not_later_than arrival. No household in this dataset predates
# the first fort; a value earlier than this is a typo, not a finding.
ARRIVAL_FLOOR = dt.date(1800, 1, 1)

RESIDENT_HOUSEHOLD_KEYS = ("id", "name", "division", "head", "arrival",
                           "party_size_on_arrival", "origin", "reason_for_coming",
                           "lives_at", "works_at", "present_on_scene_date", "persons",
                           "touches_removal", "review_required", "research_note")

# --------------------------------------------------------------------------
# kin: a relationship BETWEEN two households (T-0597)
#
# Until this existed the dataset could say everything about a person except who
# they were related to, because `persons[].relationship` is a person's place
# INSIDE one household and stops at its edge. So a kinship that crosses two
# household records had nowhere to live but a free-text note, which is to say
# nowhere a query can reach it — and the households this project most needs to
# keep apart are exactly the ones a shared surname makes mergeable. Four
# household cards in this dataset are Kinzies — six until T-0839 folded two
# duplicate initials cards on 2026-09-05; `data/research/books/crosswalk.json`
# already has to refuse "Mr. John Kinzie" the elder against John Harris Kinzie
# his son, and a household set recording no Kinzie relationship at all offers
# that refusal no support.
#
# A `kin` row is an ordinary graded claim block — `value` names the OTHER
# person, so walk_attested checks its confidence, sources and note exactly as
# it checks an arrival — plus three fields that make it a link: `person` (whose
# relative this is, in THIS household), `household` (where the other person
# lives) and `relation` (the term, from the closed set below).
#
# TWO RULES, AND BOTH EXIST BECAUSE HALF IS THE POINT. Hurlbut's note says HALF
# brother — same father, different mothers — and that is the specific form a
# summary flattens to "brother" the first time nobody is watching. So the
# vocabulary keeps the degrees apart, and:
#
#   * a relation is only legal against its declared inverses, which for a
#     sibling link is a sibling link OF THE SAME DEGREE. A half brother whose
#     mirror row says plain brother is the flattening, caught.
#   * every row is RECIPROCAL. A kinship written on one record and not the
#     other is half a fact: the household you read second still says the two
#     men were unrelated, which is the defect T-0597 was opened about.
#
# THE ASYMMETRIC RELATIONS, ADDED AS PAIRS (T-0734). Until this ticket the set
# was siblings alone, on the rule that "a relation whose inverse is unknown
# cannot be checked for reciprocity ... add the pair together or not at all".
# That rule is kept and satisfied rather than relaxed: `husband` is declared
# WITH `wife`, and the parent terms WITH the child terms, so every relation
# below still has a mirror this file can demand and check. What made them
# askable was the corpus — the St Cyr register marries six couples this town
# holds both halves of, and buries an infant it names the father of, and the
# household records had no way to say so. A relation is still refused outright
# unless its inverse appears here; uncle/nephew and cousin remain undeclared
# because nothing in the corpus has needed them yet.
RESIDENT_KIN_KEYS = ("person", "relation", "household", "value", "confidence")

# relation -> the relations its mirror row may carry. Sibling terms differ by the
# SEX of the person named, not by the degree of the tie, so each degree accepts
# both of its own terms and neither of the other's. A parent's mirror is a child
# term and a child's mirror is a parent term, for the same reason: which of the
# two words is right is a fact about the OTHER person's sex, and the register
# that states the tie usually states that too.
RESIDENT_KIN_INVERSES = {
    "brother": ("brother", "sister"),
    "sister": ("brother", "sister"),
    "half_brother": ("half_brother", "half_sister"),
    "half_sister": ("half_brother", "half_sister"),
    "husband": ("wife",),
    "wife": ("husband",),
    "father": ("son", "daughter"),
    "mother": ("son", "daughter"),
    "son": ("father", "mother"),
    "daughter": ("father", "mother"),
}
RESIDENT_KIN_RELATIONS = tuple(sorted(RESIDENT_KIN_INVERSES))


def arrival_bounds(value, precision: str):
    """The earliest and latest day an arrival value permits, or None."""
    if precision == "year":
        try:
            y = int(str(value))
        except (TypeError, ValueError):
            return None
        return dt.date(y, 1, 1), dt.date(y, 12, 31)
    d = parse_date(str(value))
    if d is None:
        return None
    if precision == "day":
        return d, d
    if precision == "either_of_two_days":
        return d, d + dt.timedelta(days=1)
    if precision == "month":
        if d.month == 12:
            last = dt.date(d.year, 12, 31)
        else:
            last = dt.date(d.year, d.month + 1, 1) - dt.timedelta(days=1)
        return dt.date(d.year, d.month, 1), last
    if precision == "season":
        return d, d + dt.timedelta(days=SEASON_DAYS)
    if precision == "not_later_than":
        return ARRIVAL_FLOOR, d
    return None


def check_resident_roles(where: str, person: dict, occupations: set, source_ids: set,
                         rep: Report) -> None:
    """`roles[]` is canonical; `occupation` is the view of the roles that reach 1835.

    THE CLAUSE THIS EXISTS FOR (T-1145 acceptance 6, T-1229): an undated or later role
    may not stand in the 1835 compatibility field. A trade printed in a directory of
    1843 is evidence about 1843, and the one field the scene compiler, the people index
    and the popup all read must not be able to carry it. The generator refuses to write
    one; this refuses to let one be hand-edited in afterwards, which is the half a
    generator can never cover.
    """
    roles = person.get("roles")
    occ = person.get("occupation")
    occ = occ if isinstance(occ, dict) else {}
    if roles is None:
        # No role evidence, so no view keys and — the assertion that absence makes —
        # no trade in the 1835 field either, because a trade there IS role evidence.
        for key in ("derived_from", "roles_at_scene_date"):
            if key in occ:
                rep.error(where, f"occupation.{key} is set and the person carries no "
                                 f"roles[] - the view keys describe a derivation that is "
                                 f"not there. Run tools/derive_resident_roles.py --write")
        if occ.get("value") not in (None, "", "none_recorded"):
            rep.error(where, f"occupation '{occ.get('value')}' stands with no roles[] "
                             f"behind it. The trade IS role evidence and owes a dated "
                             f"row; tools/derive_resident_roles.py writes it")
        return
    if not isinstance(roles, list) or not roles:
        rep.error(where, "roles is present and is not a non-empty list. An empty roles "
                         "block claims a reading that is not there; omit the key")
        return

    at_scene = []
    for i, row in enumerate(roles):
        rwhere = f"{where}/roles[{i}]"
        if not isinstance(row, dict):
            rep.error(rwhere, "a role must be an object")
            continue
        missing = [k for k in RESIDENT_ROLE_KEYS if k not in row]
        if missing:
            rep.error(rwhere, f"missing {missing} - a role that cannot say what it was, "
                              f"when, how it was dated and on whose word is not an "
                              f"assertion, it is a label")
            continue
        role = row.get("role")
        if role is not None and role not in occupations:
            rep.error(rwhere, f"role '{role}' is not in the manifest occupation "
                              f"vocabulary. Null is the honest value for a printing "
                              f"that has not been adjudicated into it; a near word is "
                              f"not")
        if row.get("kind") not in RESIDENT_ROLE_KINDS:
            rep.error(rwhere, f"kind '{row.get('kind')}' is not one of "
                              f"{list(RESIDENT_ROLE_KINDS)}")
        if row.get("precision") not in RESIDENT_ROLE_PRECISION:
            rep.error(rwhere, f"precision '{row.get('precision')}' is not one of "
                              f"{list(RESIDENT_ROLE_PRECISION)}")
        if row.get("dated_by") not in RESIDENT_ROLE_DATED_BY:
            rep.error(rwhere, f"dated_by '{row.get('dated_by')}' is not one of "
                              f"{list(RESIDENT_ROLE_DATED_BY)} - a date with no account "
                              f"of where it came from cannot be argued with")
        if (row.get("from") is None) != (row.get("to") is None):
            rep.error(rwhere, "a role carries both ends of its bound or neither. One end "
                              "alone reads as a date the evidence does not give")
        if row.get("from") is None and row.get("precision") != "unknown":
            rep.error(rwhere, f"the role has no bound and claims precision "
                              f"'{row.get('precision')}'. An unknown date stays unknown; "
                              f"it is never widened to the scene date")
        if not isinstance(row.get("covers_scene_date"), bool):
            rep.error(rwhere, "covers_scene_date must be true or false - whether the "
                              "evidence reaches the scene date is the whole question this "
                              "row is here to answer")
        if row.get("confidence") not in RESIDENT_GRADES:
            rep.error(rwhere, f"confidence '{row.get('confidence')}' is not one of "
                              f"{list(RESIDENT_GRADES)}")
        srcs = row.get("sources") or []
        if not srcs:
            rep.error(rwhere, "a role cites no source. A trade is a claim about a person "
                              "and carries its evidence like any other")
        for sid in srcs:
            if sid not in source_ids:
                rep.error(rwhere, f"source '{sid}' does not resolve in data/sources/")
        # ONLY A ROLE THAT REACHES 1835 IS MOORED TO THE PERSON'S OWN CITATION LIST, and
        # only by ONE of its sources. Two readings were tried against the tree and both
        # over-reached. Requiring it of every role put 56 later volumes into lists that
        # exist to say what the 1835 RESIDENCY stands on, which the directories block
        # forbids in its own words — "LATER EVIDENCE, BESIDE THE 1835 CLAIMS AND NOT
        # INSIDE THEM ... on its own it makes nobody a resident of 1835". Requiring it of
        # every source of a scene-date role then caught four cards whose trade cites a
        # CORROBORATING volume beside the one the person rests on (Ira Couch's Tremont
        # House is in Andreas and again in chicagology_prefire021), which is a citation
        # working correctly. What is left is the case with no defence: a role asserted
        # about the scene date on evidence the card it sits on does not stand on at all.
        if (row.get("covers_scene_date") and srcs
                and not (set(srcs) & set(person.get("sources") or []))):
            rep.error(rwhere, f"this role reaches {RESIDENT_SCENE_DATE} and not one of its "
                              f"sources {sorted(srcs)} is listed by the person; a role "
                              f"about the scene date may not float free of the evidence "
                              f"its card's grade stands on")
        if not (row.get("note") or "").strip():
            rep.error(rwhere, "a role owes a note saying what its bound means")
        if row.get("covers_scene_date") and role and row.get("confidence") in CLAIMING_GRADES:
            at_scene.append(role)

    # --- the compatibility view ------------------------------------------
    if occ.get("derived_from") != "roles":
        rep.error(where, "occupation.derived_from must be 'roles' on a person who carries "
                         "them - the singular field is a GENERATED VIEW of the roles that "
                         "cover the scene date, not a second place to assert a trade")
    named = occ.get("roles_at_scene_date")
    if named != at_scene:
        rep.error(where, f"occupation.roles_at_scene_date is {named!r} and the roles that "
                         f"reach the scene date are {at_scene!r}. Run "
                         f"tools/derive_resident_roles.py --write")
    want = at_scene[0] if at_scene else "none_recorded"
    if occ.get("value") != want:
        rep.error(where, f"occupation '{occ.get('value')}' is not the view its roles "
                         f"derive ('{want}'). A role that does not reach "
                         f"{RESIDENT_SCENE_DATE} may not fill the {RESIDENT_SCENE_DATE} "
                         f"field, and a role that does may not be dropped from it")
    withdrawn = occ.get("withdrawn_from_scene_date")
    if isinstance(withdrawn, dict):
        if occ.get("value") != "none_recorded":
            rep.error(where, "occupation carries a withdrawal and a trade at once. A "
                             "withdrawal is a refusal that fired; if the field reads a "
                             "trade the refusal no longer applies and must come off")
        for key in ("value", "confidence", "verdict", "note"):
            if not str(withdrawn.get(key) or "").strip():
                rep.error(where, f"withdrawn_from_scene_date.{key} is empty. A trade taken "
                                 f"off a card owes what it was, the grade it was held at "
                                 f"and the verdict that took it off")
    elif withdrawn is not None:
        rep.error(where, "withdrawn_from_scene_date must be an object")


def check_resident_grade(where: str, grade, sources, note: str, source_ids: set,
                         rep: Report, person: dict | None = None) -> None:
    """The accuracy vocabulary, and what each rung owes the reader."""
    if isinstance(grade, str) and grade.strip().lower() in RETIRED_GRADE_TERMS:
        rep.error(where, f"grade '{grade}' uses the term this programme was RENAMED AWAY FROM "
                         f"on 2026-08-13. The word is 'reconstructed' - inferred residents and "
                         f"inferred structures. See data/residents/index.json and "
                         f"docs/ROADMAP.md K1")
        return
    if grade not in RESIDENT_GRADES:
        rep.error(where, f"grade '{grade}' is not one of {RESIDENT_GRADES}")
        return
    if grade == "attested":
        if not sources:
            rep.error(where, "a documented person must cite at least one source_id - "
                             "'attested' means a source NAMES this person")
        for sid in sources or []:
            if sid not in source_ids:
                rep.error(where, f"source '{sid}' does not resolve in data/sources/")
    elif grade == "inferred":
        if not note:
            rep.error(where, "a derived person requires a note stating WHICH details are "
                             "reconstructed and from what - a real person with invented "
                             "details and no reasoning is indistinguishable from a fabrication")
        for sid in sources or []:
            if sid not in source_ids:
                rep.error(where, f"source '{sid}' does not resolve in data/sources/")
    else:  # reconstructed
        if not note:
            rep.error(where, "a reconstructed person requires a note arguing the demonstrable "
                             "need of the town that this resident fills")
        if sources:
            rep.warn(where, "a reconstructed person is HYPOTHESISED and no source names them; "
                            "cite the evidence for the NEED in the note instead of attaching "
                            "source_ids to the person, or promote the grade to inferred")

    # --- an invented name may never outrank the invention ---------------------
    #
    # The reconstructed residents carry invented names now, so that a
    # reconstructed household reads as a household rather than as a row in a
    # table. That is a real risk and this is what contains it: a made-up name is
    # the single easiest way for an invention to be mistaken for a finding,
    # because a name LOOKS like a fact in a way that "wall height 3.25 m" does
    # not. So the name has to declare itself, at the bottom tier, always.
    basis = (person or {}).get("name_basis")
    if grade == "reconstructed":
        if not isinstance(basis, dict):
            rep.error(where, "a reconstructed person carries an INVENTED name and must carry a "
                             "name_basis block saying so and naming the pool it came from "
                             "(tools/generate_inferred_names.py writes it)")
        else:
            if basis.get("confidence") != "reconstructed":
                rep.error(where, f"name_basis is graded '{basis.get('confidence')}' on an "
                                 f"invented name. An invented name can never grade above "
                                 f"reconstructed - that is the whole point of recording it")
            if not (basis.get("note") or "").strip():
                rep.error(where, "name_basis requires a note stating that the name is invented "
                                 "and what bounds the invention")
            for sid in basis.get("sources") or []:
                if sid not in source_ids:
                    rep.error(where, f"name_basis source '{sid}' does not resolve in "
                                     f"data/sources/")
    elif basis is not None:
        rep.error(where, "name_basis belongs only on a reconstructed person. On an attested or "
                         "inferred one the name comes from a source, and marking it as invented "
                         "would understate what is known about a real person")


def check_resident_link(where: str, key: str, node, structure_ids: set, rep: Report) -> None:
    """lives_at / works_at must name a real structure or be null."""
    if not isinstance(node, dict):
        rep.error(where, f"{key} must be an attested block with a value, a confidence and a "
                         f"note - a missing link and an unresearched one are different findings")
        return
    v = node.get("value")
    if v is None:
        if not (node.get("note") or "").strip():
            rep.error(where, f"{key} is null and carries no note. A null link is a CLAIM that "
                             f"the building is not in the dataset or not attested, and it has "
                             f"to say which")
        return
    if not isinstance(v, str) or v not in structure_ids:
        rep.error(where, f"{key} names '{v}', which is not a structure id in data/structures/. "
                         f"A resident may point at a building that exists or at null; a later "
                         f"parcel closes the loop by building the structure")


def check_residents(source_ids: set, structure_ids: set, rep: Report, tally: dict,
                    data_root: Path | None = None) -> dict:
    """Schema, provenance, linkage and the scene-date gate for data/residents/**."""
    root = (data_root or DATA) / "residents"
    index_path = root / "index.json"
    if not index_path.exists():
        rep.note("residents: no data/residents/index.json - the scene carries no population")
        return {}
    index = load_json(index_path, rep)
    if not isinstance(index, dict):
        return {}

    # Every way the manifest can disagree with the cards, collected rather than
    # reported one at a time - see the single error this becomes at the end.
    index_drift: list[str] = []

    scene_date = index.get("scene_date") or ""
    scene = parse_date(scene_date)
    if scene is None:
        rep.error("residents index", "scene_date must be an ISO date - every arrival in this "
                                     "dataset is checked against it")
        return {}

    vocab = index.get("vocabulary") or {}
    for key in ("grades", "relationships", "occupations", "sexes", "presence", "divisions",
                "arrival_precision", "kin_relations", "association_kinds",
                "association_resolution", "role_kinds", "role_date_precision",
                "role_dated_by"):
        if not vocab.get(key):
            rep.error("residents index", f"vocabulary.{key} is missing - a renderer and the "
                                         f"evidence panel read this block to know the closed "
                                         f"sets they must implement")
    if list(vocab.get("grades") or []) != list(RESIDENT_GRADES):
        rep.error("residents index", f"vocabulary.grades must be exactly {list(RESIDENT_GRADES)} "
                                     f"and is {vocab.get('grades')!r}. The accuracy vocabulary "
                                     f"is a contract, not a preference")
    if list(vocab.get("kin_relations") or []) != list(RESIDENT_KIN_RELATIONS):
        rep.error("residents index", f"vocabulary.kin_relations must be exactly "
                                     f"{list(RESIDENT_KIN_RELATIONS)} and is "
                                     f"{vocab.get('kin_relations')!r}. A relation with no "
                                     f"declared inverse cannot be checked for reciprocity, so "
                                     f"the set a record may use is the set validate.py can "
                                     f"mirror")
    if list(vocab.get("association_kinds") or []) != list(ASSOCIATION_KINDS):
        rep.error("residents index", f"vocabulary.association_kinds must be exactly "
                                     f"{list(ASSOCIATION_KINDS)} and is "
                                     f"{vocab.get('association_kinds')!r}. The set a record "
                                     f"may use is the set a reading has needed; it grows in "
                                     f"tools/associations.py with the reading that needed it")
    if list(vocab.get("association_resolution") or []) != list(ASSOCIATION_RESOLUTION):
        rep.error("residents index", f"vocabulary.association_resolution must be exactly "
                                     f"{list(ASSOCIATION_RESOLUTION)} and is "
                                     f"{vocab.get('association_resolution')!r}. A rung a "
                                     f"renderer does not implement is a place it will draw "
                                     f"at a precision the evidence never reached")
    if list(vocab.get("arrival_precision") or []) != list(RESIDENT_PRECISION):
        rep.error("residents index", f"vocabulary.arrival_precision must be exactly "
                                     f"{list(RESIDENT_PRECISION)} and is "
                                     f"{vocab.get('arrival_precision')!r}. A renderer that "
                                     f"reads a shorter list will silently mis-bound an arrival, "
                                     f"which is the one claim the scene date rests on")
    for key, closed in (("role_kinds", RESIDENT_ROLE_KINDS),
                        ("role_date_precision", RESIDENT_ROLE_PRECISION),
                        ("role_dated_by", RESIDENT_ROLE_DATED_BY)):
        if list(vocab.get(key) or []) != list(closed):
            rep.error("residents index", f"vocabulary.{key} must be exactly {list(closed)} "
                                         f"and is {vocab.get(key)!r}. A role's kind, its "
                                         f"date precision and HOW it was dated are three "
                                         f"closed sets a reader must be able to implement "
                                         f"from the manifest alone")
    occupations = set(vocab.get("occupations") or [])
    relationships = set(vocab.get("relationships") or [])
    sexes = set(vocab.get("sexes") or [])
    presences = set(vocab.get("presence") or [])
    divisions = set(vocab.get("divisions") or [])

    households: dict = {}
    kin_rows: list = []
    person_ids: dict = {}
    grade_totals: dict = {g: 0 for g in RESIDENT_GRADES}
    n_persons = 0

    for entry in index.get("households", []):
        hid, hfile = entry.get("id"), entry.get("file")
        path = root / (hfile or "")
        if not hfile or not path.exists():
            rep.error("residents index", f"household '{hid}' names {hfile}, which does not "
                                         f"exist - a static host cannot be globbed, so a "
                                         f"manifest entry without a file is a 404 on the "
                                         f"deployed site")
            continue
        h = load_json(path, rep)
        if not isinstance(h, dict):
            continue
        where = f"resident household {hid}"
        if h.get("id") != hid or path.stem != hid:
            rep.error(where, "id must match both the manifest entry and the filename stem")
        if not SLUG.match(str(hid or "")):
            rep.error(where, f"id '{hid}' is not a lowercase slug")
        if hid in households:
            rep.error(where, "duplicate household id")
        for key in RESIDENT_HOUSEHOLD_KEYS:
            if key not in h:
                rep.error(where, f"missing required key '{key}'")
        if h.get("division") not in divisions:
            rep.error(where, f"division '{h.get('division')}' is not declared in the manifest "
                             f"vocabulary")
        source_pass = h.get("source_pass")
        if source_pass is not None and source_pass not in RESIDENT_SOURCE_PASSES:
            rep.error(where, f"source_pass '{source_pass}' is not one of "
                             f"{RESIDENT_SOURCE_PASSES} - omit the key on a hand-authored "
                             f"household, or match one of the three mint tools' pass names")

        # --- persons -------------------------------------------------------
        persons = h.get("persons") or []
        if not persons:
            rep.error(where, "a household with no persons is not a household record")
        local_grades: dict = {}
        heads = 0
        for p in persons:
            pid = p.get("id")
            pwhere = f"{where}/{pid}"
            if not SLUG.match(str(pid or "")):
                rep.error(pwhere, f"person id '{pid}' is not a lowercase slug")
            if pid in person_ids:
                rep.error(pwhere, f"person id '{pid}' is already used in "
                                  f"{person_ids[pid]} - one person, one id, across the whole "
                                  f"dataset")
            person_ids[pid] = hid
            if not (p.get("name") or "").strip():
                rep.error(pwhere, "a person must have a name, even when it is the source's "
                                  "own placeholder for people it counts and does not name")
            rel = p.get("relationship")
            if rel not in relationships:
                rep.error(pwhere, f"relationship '{rel}' is not declared in the manifest "
                                  f"vocabulary")
            if rel == "head":
                heads += 1
            if "sex" in p and p.get("sex") not in sexes:
                rep.error(pwhere, f"sex '{p.get('sex')}' is not declared in the manifest "
                                  f"vocabulary; omit the key where the sources do not say")
            grade = p.get("grade")
            check_resident_grade(pwhere, grade, p.get("sources") or [],
                                 (p.get("note") or "").strip(), source_ids, rep, p)
            if grade in grade_totals:
                grade_totals[grade] += 1
                local_grades[grade] = local_grades.get(grade, 0) + 1
            n_persons += 1

            occ = p.get("occupation")
            if not isinstance(occ, dict):
                rep.error(pwhere, "occupation must be an attested block - a trade is a claim "
                                  "about a person and carries a confidence like any other")
            elif occ.get("value") not in occupations:
                rep.error(pwhere, f"occupation '{occ.get('value')}' is not in the manifest "
                                  f"vocabulary. The vocabulary is PERIOD-CORRECT by "
                                  f"construction: add the trade the sources actually name, do "
                                  f"not reach for a modern equivalent")
            for k in ("lives_at", "works_at"):
                if k in p:
                    check_resident_link(pwhere, k, p.get(k), structure_ids, rep)
            if "associated_with" in p:
                check_association_rows(pwhere, p.get("associated_with"), error=rep.error,
                                       structure_ids=structure_ids, source_ids=source_ids,
                                       divisions=divisions, scene=scene)
                for msg in singular_drift(p, p.get("associated_with")):
                    rep.error(pwhere, msg)

            check_resident_roles(pwhere, p, occupations, source_ids, rep)

            # --- the evidence blocks a minted person shows its working in ----
            for key in RESIDENT_EVIDENCE_BLOCKS:
                if key not in p:
                    continue
                rows_ = p.get(key)
                if not isinstance(rows_, list) or not rows_:
                    rep.error(pwhere, f"{key} is present and is not a non-empty list. An "
                                      f"empty evidence block claims a reading that is not "
                                      f"there; omit the key instead")
                    continue
                for i, row_ in enumerate(rows_):
                    rwhere = f"{pwhere}/{key}[{i}]"
                    if not isinstance(row_, dict):
                        rep.error(rwhere, "an evidence row must be an object")
                        continue
                    for k in RESIDENT_EVIDENCE_ROW_KEYS:
                        if not str(row_.get(k) or "").strip():
                            rep.error(rwhere, f"'{k}' is empty. A reading that cannot name "
                                              f"its list, its transcription, its locator, "
                                              f"its record, its source and the rule that "
                                              f"fired is not evidence, it is a claim")
                    sid_ = row_.get("source")
                    if sid_ and sid_ not in source_ids:
                        rep.error(rwhere, f"source '{sid_}' does not resolve in data/sources/")
                    if sid_ and sid_ not in (p.get("sources") or []):
                        rep.error(rwhere, f"source '{sid_}' is cited by this reading and not "
                                          f"by the person; the card would show a grade "
                                          f"resting on a source it does not list")
            if p.get("civic_mint") and not any(p.get(k) for k in RESIDENT_EVIDENCE_BLOCKS):
                rep.error(pwhere, "civic_mint is set and the person carries no evidence "
                                  "block - that cohort is minted FROM a reading and has "
                                  "to show it (tools/mint_civic_residents.py)")

        if heads != 1:
            rep.error(where, f"{heads} person(s) carry relationship 'head'; a household record "
                             f"has exactly one")
        head = h.get("head")
        if head not in {p.get("id") for p in persons}:
            rep.error(where, f"head '{head}' is not a person in this household")
        elif next((p for p in persons if p.get("id") == head), {}).get("relationship") != "head":
            rep.error(where, f"head '{head}' does not carry relationship 'head'")

        # --- arrival, and the gate the whole scene rests on -----------------
        arr = h.get("arrival")
        if not isinstance(arr, dict):
            rep.error(where, "arrival must be an attested block")
        else:
            prec = arr.get("precision")
            if prec not in RESIDENT_PRECISION:
                rep.error(where, f"arrival.precision '{prec}' is not one of "
                                 f"{RESIDENT_PRECISION}. The sources give years far more often "
                                 f"than days and the record has to say which it has")
            else:
                bounds = arrival_bounds(arr.get("value"), prec)
                if bounds is None:
                    rep.error(where, f"arrival value {arr.get('value')!r} cannot be read at "
                                     f"precision '{prec}'")
                else:
                    earliest, latest = bounds
                    if earliest > scene:
                        rep.error(where, f"arrival {arr.get('value')!r} ({prec}) cannot have "
                                         f"preceded the scene date {scene_date}. A person who "
                                         f"arrived after 1 July 1835 IS NOT IN THIS SCENE and "
                                         f"belongs in index.json's researched_not_resident "
                                         f"list with the reason, exactly as a later building "
                                         f"belongs in data/exclusions.json")
                    elif latest > scene:
                        rep.warn(where, f"arrival {arr.get('value')!r} at '{prec}' precision "
                                        f"straddles the scene date {scene_date} - the "
                                        f"household may or may not have been here. Narrow the "
                                        f"precision if the evidence allows, and say so in the "
                                        f"note if it does not")

        # --- presence, links, and the removal flag --------------------------
        pres = h.get("present_on_scene_date")
        if not isinstance(pres, dict):
            rep.error(where, "present_on_scene_date must be an attested block - being a "
                             "resident and being in town on one day are different claims")
        else:
            if pres.get("value") not in presences:
                rep.error(where, f"present_on_scene_date '{pres.get('value')}' is not declared "
                                 f"in the manifest vocabulary")
            elif pres.get("value") in ("absent", "uncertain")                     and not (pres.get("note") or "").strip():
                rep.error(where, f"present_on_scene_date '{pres.get('value')}' requires a note. "
                                 f"Saying a documented resident may not have been here is a "
                                 f"finding and owes its reasoning")

        for k in ("lives_at", "works_at"):
            check_resident_link(where, k, h.get(k), structure_ids, rep)

        # --- associated_with: the plural, dated form of the two links above ---
        # T-1238. `lives_at`/`works_at` are singular and undated, and the sources
        # are frequently neither; the list says which places, of what kind, on
        # what dates, at what tier. Both shapes stand until the migration lands,
        # and `singular_drift` is what stops them saying two different things.
        if "associated_with" in h:
            check_association_rows(where, h.get("associated_with"), error=rep.error,
                                   structure_ids=structure_ids, source_ids=source_ids,
                                   divisions=divisions, scene=scene)
            for msg in singular_drift(h, h.get("associated_with")):
                rep.error(where, msg)

        # --- kin: the link out of this record -------------------------------
        # Shape and local resolution here; the other end is checked after the
        # loop, because a kinship may name a household this pass has not loaded
        # yet and a forward reference is not an error.
        kin = h.get("kin")
        if kin is not None and not isinstance(kin, list):
            rep.error(where, "kin must be a list of relationship rows")
        elif kin:
            own_person_ids = {p.get("id") for p in persons}
            for i, k in enumerate(kin):
                kwhere = f"{where}/kin[{i}]"
                if not isinstance(k, dict):
                    rep.error(kwhere, "a kin row must be an object")
                    continue
                for key in RESIDENT_KIN_KEYS:
                    if key not in k:
                        rep.error(kwhere, f"missing required key '{key}'")
                rel = k.get("relation")
                if rel not in RESIDENT_KIN_RELATIONS:
                    rep.error(kwhere, f"relation '{rel}' is not one of "
                                      f"{list(RESIDENT_KIN_RELATIONS)} - the declared set is "
                                      f"the set whose inverse this file knows, and a relation "
                                      f"whose inverse is unknown cannot be checked for "
                                      f"reciprocity")
                if k.get("person") not in own_person_ids:
                    rep.error(kwhere, f"person '{k.get('person')}' is not a person in this "
                                      f"household; a kin row says who in HERE the relative "
                                      f"belongs to")
                other_hid = k.get("household")
                if not (isinstance(other_hid, str) and other_hid.strip()):
                    rep.error(kwhere, "a kin row's 'household' must name a household id in "
                                      "this dataset. KIN IS INSIDE THE TOWN (T-0849): both "
                                      "rules this block enforces are rules about the far end "
                                      "- the inverse has to be legal and the mirror has to "
                                      "exist - so a row with no far end is not a weaker kin "
                                      "row, it is one with the whole checked part removed. A "
                                      "relative who was never in this scene (a parent in "
                                      "Montreal, a brother left in Vermont) is EVIDENCE, not "
                                      "structure: write the name in the prose note of a field "
                                      "the record already has, at that field's grade and under "
                                      "that field's citation, the way every birthplace here is "
                                      "written")
                    continue
                if other_hid == hid:
                    rep.error(kwhere, "a kin row links two households; a relationship inside "
                                      "one household is persons[].relationship")
                kin_rows.append((hid, k, kwhere))

        if h.get("touches_removal") and not h.get("review_required"):
            rep.error(where, "touches_removal is true but review_required is false. AGENTS.md's "
                             "standing constraint: the final removal of the Potawatomi is the "
                             "most historically significant event of this target year and any "
                             "record touching it blocks a scene from being marked released "
                             "until the consultation the project has committed to has happened")
        if not (h.get("research_note") or "").strip():
            rep.error(where, "research_note is required - a household is an argument about "
                             "people and the argument has to be written down")

        # the confidence contract, applied to every attested block in the record
        walk_attested(where, {k: v for k, v in h.items() if k != "persons"},
                      source_ids, rep, tally)
        for p in persons:
            walk_attested(f"{where}/{p.get('id')}", p, source_ids, rep, tally)

        # --- the manifest's denormalised copies -----------------------------
        for key, actual in (("head", h.get("head")),
                            ("division", h.get("division")),
                            ("lives_at", (h.get("lives_at") or {}).get("value")),
                            ("works_at", (h.get("works_at") or {}).get("value")),
                            ("present_on_scene_date",
                             (h.get("present_on_scene_date") or {}).get("value")),
                            ("review_required", h.get("review_required"))):
            if entry.get(key) != actual:
                index_drift.append(f"household '{hid}' {key} in the manifest "
                                   f"({entry.get(key)!r}) disagrees with the record "
                                   f"({actual!r})")
        if entry.get("persons") != len(persons):
            index_drift.append(f"household '{hid}' persons {entry.get('persons')!r} "
                               f"disagrees with the {len(persons)} in the record")
        if entry.get("grades") != local_grades:
            index_drift.append(f"household '{hid}' grades {entry.get('grades')!r} "
                               f"disagrees with the record's {local_grades!r}")
        households[hid] = h

    # --- kin: the far end, and the reciprocity rule -------------------------
    # Every household is loaded by now, so a row can be resolved and, more to
    # the point, its mirror can be demanded. A kinship written on one record
    # only leaves the other record still saying the two people were unrelated,
    # which is exactly the state T-0597 was opened about.
    written = {(hid, k.get("person"), k.get("household"), k.get("value")): k.get("relation")
               for hid, k, _ in kin_rows}
    for hid, k, kwhere in kin_rows:
        other_hid, other_pid = k.get("household"), k.get("value")
        other = households.get(other_hid)
        if other is None:
            rep.error(kwhere, f"household '{other_hid}' does not resolve in "
                              f"data/residents/households/")
            continue
        if other_pid not in {p.get("id") for p in other.get("persons") or []}:
            rep.error(kwhere, f"'{other_pid}' is not a person in household '{other_hid}'")
            continue
        mirror = written.get((other_hid, other_pid, hid, k.get("person")))
        if mirror is None:
            rep.error(kwhere, f"household '{other_hid}' does not carry the matching row. A kin "
                              f"claim is reciprocal: write it on both records or on neither, "
                              f"because the record that omits it still reads as no "
                              f"relationship at all")
        elif mirror not in RESIDENT_KIN_INVERSES.get(k.get("relation"), ()):
            rep.error(kwhere, f"this row says '{k.get('relation')}' and the matching row in "
                              f"'{other_hid}' says '{mirror}'. The degree of a tie is not a "
                              f"matter of which end you read it from - a HALF brother whose "
                              f"mirror says brother is the flattening this check exists to "
                              f"catch")

    counts = index.get("counts") or {}
    if counts.get("households") != len(households):
        index_drift.append(f"counts.households {counts.get('households')!r} "
                           f"disagrees with the {len(households)} loaded")
    if counts.get("persons") != n_persons:
        index_drift.append(f"counts.persons {counts.get('persons')!r} disagrees with "
                           f"the {n_persons} in the records")
    if counts.get("by_grade") != grade_totals:
        index_drift.append(f"counts.by_grade {counts.get('by_grade')!r} disagrees "
                           f"with the records' {grade_totals!r}")

    # ONE FAULT, ONE SENTENCE, AND IT NAMES THE FIX (T-0715). Every disagreement
    # collected above has the same cause - the manifest is DERIVED from the cards,
    # and some pass left behind a row it did not own - and reporting them one per
    # household turned a single stale write into nineteen errors that named no
    # remedy between them. tools/rebuild_resident_index.py is the derivation and
    # tools/check.sh re-runs it; this is the diagnosis, not the gate.
    if index_drift:
        shown = index_drift[:12]
        more = ("" if len(index_drift) == len(shown)
                else f"; ... and {len(index_drift) - len(shown)} more")
        rep.error("residents index",
                  "the manifest is DERIVED from data/residents/households/*.json and no "
                  f"longer matches them on {len(index_drift)} point(s); the records are "
                  "authoritative. Re-derive it with `python3 "
                  "tools/rebuild_resident_index.py --write`. What disagrees: "
                  + "; ".join(shown) + more)

    # The researched-and-excluded half. Same standard as data/exclusions.json:
    # a finding that a person is NOT in this scene is a claim and owes a reason.
    for ex in index.get("researched_not_resident", []):
        exid = ex.get("id")
        exwhere = f"residents index/researched_not_resident/{exid}"
        if not SLUG.match(str(exid or "")):
            rep.error(exwhere, f"id '{exid}' is not a lowercase slug")
        if not (ex.get("reason") or "").strip():
            rep.error(exwhere, "a person researched and left out owes a reason")
        if not (ex.get("note") or "").strip():
            rep.error(exwhere, "a person researched and left out owes the reasoning, so the "
                               "next agent does not redo the work or quietly reverse it")
        for sid in ex.get("sources") or []:
            if sid not in source_ids:
                rep.error(exwhere, f"source '{sid}' does not resolve in data/sources/")
        if exid in person_ids:
            rep.error(exwhere, f"'{exid}' is both a resident and researched-and-excluded")

    if households:
        linked = sum(1 for h in households.values()
                     if (h.get("lives_at") or {}).get("value")
                     or (h.get("works_at") or {}).get("value"))
        unsure = sum(1 for h in households.values()
                     if (h.get("present_on_scene_date") or {}).get("value") != "present")
        flagged = sum(1 for h in households.values() if h.get("review_required"))
        rep.note(f"residents: {len(households)} household(s), {n_persons} person(s) "
                 f"({grade_totals['attested']} attested, {grade_totals['inferred']} inferred, "
                 f"{grade_totals['reconstructed']} reconstructed); {linked} linked to a structure, "
                 f"{unsure} NOT recorded as certainly present on the scene date, "
                 f"{flagged} flagged review_required")
    return households

# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------

def load_dir(d: Path, rep: Report) -> dict:
    out = {}
    if not d.exists():
        return out
    for p in sorted(d.glob("*.json")):
        doc = load_json(p, rep)
        if doc is not None:
            out[p.name] = doc
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--params", action="store_true")
    ap.add_argument("--licenses", action="store_true")
    ap.add_argument("--stale", action="store_true")
    ap.add_argument("--site", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    if args.all:
        args.params = args.licenses = args.stale = args.site = True

    rep = Report()

    sources = load_dir(DATA / "sources", rep)
    structures = load_dir(DATA / "structures", rep)
    scenes = load_dir(DATA / "scenes", rep)

    source_ids = {s.get("id") for s in sources.values() if isinstance(s, dict)}
    for name, s in sources.items():
        if isinstance(s, dict) and s.get("id") != Path(name).stem:
            rep.error(f"source {name}", f"id '{s.get('id')}' does not match filename stem")
        if isinstance(s, dict) and s.get("type") == "website" and not s.get("archived_url"):
            rep.warn(f"source {name}", "website source without archived_url — several key hosts "
                                       "for this project return 503/403 intermittently; a citation "
                                       "that cannot be re-read is not a citation")

    datum = load_json(DATA / "datum.json", rep) or {}
    epochs_doc = load_json(DATA / "terrain" / "epochs.json", rep) or {}
    epochs = {e["id"]: e for e in epochs_doc.get("epochs", []) if isinstance(e, dict)}
    exclusions = load_json(DATA / "exclusions.json", rep) or {}
    liberties = load_json(DATA / "liberties.json", rep) or {}

    validate_schemas(sources, structures, scenes, rep)

    # epoch intervals must not overlap
    spans = []
    for e in epochs.values():
        frm, to = parse_date(e.get("from", "")), parse_date(e.get("to", ""))
        if frm and to:
            spans.append((frm, to, e["id"]))
    for i, (f1, t1, id1) in enumerate(sorted(spans)):
        for f2, t2, id2 in sorted(spans)[i + 1:]:
            if f2 <= t1 and f1 <= t2:
                rep.error("epochs", f"'{id1}' ({f1}..{t1}) overlaps '{id2}' ({f2}..{t2})")

    active = [e["id"] for e in epochs.values() if e.get("status") == "active"]
    if len(active) > 1:
        rep.warn("epochs", f"{len(active)} epochs marked active ({active}); only one should be "
                           f"active until the first milestone ships")

    # structures
    tally: dict = {}
    for name, st in structures.items():
        sid = st.get("id", name)
        where = f"structure {sid}"
        if sid != Path(name).stem:
            rep.error(where, f"id does not match filename stem '{Path(name).stem}'")
        if not SLUG.match(sid or ""):
            rep.error(where, f"id '{sid}' is not a lowercase slug")

        phase_ids = set()
        for ph in st.get("phases", []):
            pid = ph.get("id", "?")
            pwhere = f"{where}/{pid}"
            if pid in phase_ids:
                rep.error(where, f"duplicate phase id '{pid}'")
            phase_ids.add(pid)
            check_range(pwhere, ph.get("documented_range", {}), source_ids, rep)

            pos = ph.get("position", {})
            if pos.get("utm_e") is None and not (pos.get("symbolic_location") or "").strip():
                rep.error(pwhere, "position has no coordinates and no symbolic_location — "
                                  "a structure must be locatable in words even before the datum "
                                  "is verified")
            walk_attested(pwhere, ph.get("form", {}), source_ids, rep, tally, "form")
            check_attested(pwhere, "position", pos, source_ids, rep)
            check_attested(pwhere, "footprint", ph.get("footprint", {}), source_ids, rep)
            tally[pos.get("confidence")] = tally.get(pos.get("confidence"), 0) + 1
            fp_conf = ph.get("footprint", {}).get("confidence")
            tally[fp_conf] = tally.get(fp_conf, 0) + 1

        for key in ("function", "occupants"):
            if key in st:
                check_attested(where, key, st[key], source_ids, rep)
                c = st[key].get("confidence")
                tally[c] = tally.get(c, 0) + 1

    # what was researched and left out — a record with the same citation rule as
    # anything else here, and now one the walkthrough quotes to a visitor
    check_exclusions(exclusions, source_ids, rep)

    # and the third category, which is neither: researched, standing in neither
    # the dataset nor the exclusions, and open. Its own promise — that nothing
    # here gets promoted to documented without new evidence — is a check now.
    check_watch_list(exclusions, structures, source_ids, rep)

    # and the ground itself, which makes graded claims like everything else here
    # and was checked by nothing until it started making them to a visitor. One
    # enumeration serves this check and the coverage gate below, so the ground
    # cannot be graded against one list and admitted to against another.
    ground_index = terrain_claim_index(load_terrain_specs(rep), rep)
    check_terrain_claims(source_ids, rep, index=ground_index)
    # and the ground's omissions, which are the other half of the same question:
    # every gate above asks how sure we are of what the ground claims, and none
    # of them can see a claim with no vertex behind it at all.
    ground_consumed = terrain_consumed(rep)
    check_ground_geometry(ground_index, ground_consumed, rep)
    # and the one declaration that is a promise rather than an absence: the mesh
    # agrees with this figure and does not read it. Three states say a thing is
    # not built and can be checked by looking at the ground; this one says two
    # documents say the same thing, and nothing was holding them together.
    check_restated_agreement(ground_index, terrain_restates(rep), rep)

    # and what every one of those grades rests on. The confidence model ranks the
    # evidence in `data/source.schema.json` and in `docs/PROVENANCE.md`, and until
    # now the ranking was enforced nowhere — a `documented` value owed a source
    # that resolved and nothing asked what kind of source it was.
    check_evidence_ladder(structures, sources, rep, ground_index)

    # and what each rung is a judgement ABOUT. A modern page that reprints an
    # 1883 interview is worth what the interview is worth; until this ran, that
    # reasoning lived in a `note` no check could read.
    check_transcription_declarations(sources, rep)

    # the people, and the scene-date gate they have to obey. The population is
    # what justifies the buildings (docs/ROADMAP.md K1): a household that needs
    # a dwelling becomes a structure record, so a household whose subject was
    # still in Vermont on the scene date would put a house on the plat.
    #
    # RUN BEFORE THE SCENES, which is not where it used to be. The scene's
    # release block has to see this layer — a household carrying AGENTS.md's
    # standing constraint blocks release exactly as a building does — and it
    # could not while the layer was loaded after the block had already run
    # (ROADMAP K34).
    households = check_residents(source_ids, {st.get("id") for st in structures.values()
                                              if isinstance(st, dict)}, rep, tally)

    # scenes
    for name, sc in scenes.items():
        validate_scene(sc, structures, epochs, exclusions, rep, households=households)

    # what we invented has to be written down, not merely tagged — and so does
    # what we recorded and never built, which is the same standard read backwards
    consumed = archetype_consumed(rep)
    check_geometry_declarations(structures, consumed, rep)

    # …and what a record says it no longer builds, it must no longer build.
    check_drawn_by(structures, rep)

    # Does each structure reach the ground it stands over? Needs the committed
    # heightfield and the datum origin; without either the question cannot be
    # asked, and a gate that silently answers "yes" when it cannot see is worse
    # than one that says it did not run.
    contacts = archetype_ground_contact(rep)
    epoch_ids = {sc.get("terrain_epoch") for sc in scenes.values() if sc.get("terrain_epoch")}
    field = None
    for ep in sorted(i for i in epoch_ids if i):
        try:
            field = Heightfield.load(DATA / "terrain" / "epochs" / ep)
        except Exception as e:  # noqa: BLE001
            rep.error("ground contact", f"cannot read the {ep} heightfield: {e}")
        if field is not None:
            break
    datum_origin = None
    if datum.get("origin_utm_e") is not None and datum.get("origin_utm_n") is not None:
        datum_origin = (float(datum["origin_utm_e"]), float(datum["origin_utm_n"]))
    unlanded: list[tuple] = []
    if field is None or datum_origin is None or not contacts:
        rep.note("ground contact: skipped — needs a committed heightfield, a datum origin "
                 "and at least one archetype declaring GROUND_CONTACT")
    else:
        unlanded = unlanded_values(structures, scenes, rep, field, datum_origin, contacts)
        check_ground_contact(structures, unlanded, rep)

    check_liberties_coverage(structures, liberties, rep, consumed, unlanded, ground_index,
                             ground_consumed)

    # and how each of those positions was arrived at, which every record stated
    # in prose and nothing recomputed. The corners come back out of the control
    # and the platted module; the crossing comes back out of the traced bank.
    check_position_derivations(structures, source_ids, rep)

    # and the module those corners are stepped from, which nothing checked until the
    # corridors were measured off both 1834 sheets
    check_street_module(source_ids, rep)

    # what passes between the compiler and the renderer, checked from both sides
    check_sidecar_contract(rep)

    # and the same interface for the three derived documents that gate says, in
    # its own docstring, that it does not cover
    check_derived_contract(rep)

    # and the third direction those two cannot see: a field of a source record
    # that never entered the interface at all
    check_source_surface(sources, rep)

    # the vegetation records, and the July phenology rules they have to obey
    check_flora(source_ids, field, rep, tally)

    # the animal records, and the July gate they have to obey — the same
    # argument as the flora phenology, one trophic level up
    check_fauna(source_ids, rep, tally)

    # the datum gate — the single most consequential check in the suite
    if not datum.get("verified"):
        rep.note("datum is UNVERIFIED — generators and bake will refuse to run. "
                 "This is by design: fixing the origin after geometry exists means "
                 "regenerating everything. See docs/EPOCHS.md.")

    # optional passes
    if args.params:
        run_param_check(structures, scenes, rep)
    if args.licenses:
        run_license_check(sources, rep)
    if args.stale:
        run_stale_check(structures, rep)
        run_bake_reach_check(structures, scenes, rep)
    if args.site:
        run_site_check(rep)

    # confidence summary — the honest picture of the dataset
    total = sum(v for k, v in tally.items() if k)
    if total:
        print(f"\nConfidence across {total} attributes in {len(structures)} structure(s):")
        for level in CONFIDENCE:
            n = tally.get(level, 0)
            bar = "#" * round(40 * n / total) if total else ""
            print(f"  {level:<12} {n:>4}  {100 * n / total:5.1f}%  {bar}")

    print()
    rep.print(args.strict)
    return 0 if rep.ok(args.strict) else 1


def run_param_check(structures: dict, scenes: dict, rep: Report) -> None:
    """Resolve every scene-included phase into archetype parameters.

    Imports only the pure-Python `*_params.py` halves — no bpy, so this runs in
    any agent sandbox in milliseconds. It catches the failure mode where a record
    is schema-valid but produces a building 400 metres tall, long before anyone
    spends minutes on a bake.
    """
    sys.path.insert(0, str(ROOT / "generators"))
    resolvers = {}
    arch_dir = ROOT / "generators" / "archetypes"
    if not arch_dir.exists():
        rep.note("--params: no archetype modules yet")
        return
    for mod_path in sorted(arch_dir.glob("*_params.py")):
        name = mod_path.stem.removesuffix("_params")
        try:
            mod = __import__(f"archetypes.{mod_path.stem}", fromlist=["from_phase"])
            resolvers[name] = mod.from_phase
        except Exception as e:  # noqa: BLE001 — a broken generator must fail the gate
            rep.error("params", f"cannot import {mod_path.name}: {e}")

    checked, no_gen = 0, set()
    for sc in scenes.values():
        target = parse_date(sc.get("target_date", ""))
        if target is None:
            continue
        for st in structures.values():
            arch = st.get("archetype")
            for ph in st.get("phases", []):
                r = ph.get("documented_range", {})
                frm, to = parse_date(r.get("from", "")), parse_date(r.get("to", ""))
                if not (frm and to and frm <= target <= to):
                    continue
                # A phase whose geometry moved to another layer resolves into no
                # archetype parameters, because no archetype builds it. Asking
                # `outbuilding` for the estray pen's roof pitch after the roof was
                # retired is asking a generator about a mesh nobody bakes; what
                # holds that phase together instead is check_drawn_by(), which
                # asserts the layer record exists and that no GLB survives it.
                if drawn_by_another_layer(ph):
                    continue
                if arch not in resolvers:
                    no_gen.add(arch)
                    continue
                try:
                    resolvers[arch](ph)
                    checked += 1
                except Exception as e:  # noqa: BLE001
                    rep.error(f"structure {st.get('id')}/{ph.get('id')}",
                              f"does not resolve into {arch} parameters: {e}")
    rep.note(f"param check: {checked} phase(s) resolved"
             + (f"; no generator yet for {sorted(no_gen)}" if no_gen else ""))


def run_license_check(sources: dict, rep: Report) -> None:
    licenses = ROOT / "assets" / "LICENSES.md"
    if not licenses.exists():
        rep.error("licenses", "assets/LICENSES.md is missing")
        return
    text = licenses.read_text()
    manifest_path = ROOT / "assets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text()).get("assets", {}) \
        if manifest_path.exists() else {}

    generated, third_party = 0, 0
    for p in sorted((ROOT / "assets").rglob("*")):
        if p.is_dir() or p.name in ("LICENSES.md", "manifest.json") or p.name.startswith("."):
            continue
        rel = p.relative_to(ROOT / "assets").as_posix()

        # Build output under gltf/ and web/ is provenance-tracked by the manifest
        # (which records its input hash and the Blender that made it), not by a
        # hand-written licence row. Untracked build output IS an error — it means
        # a file appeared that no recorded bake produced.
        if rel.startswith(("gltf/", "web/")):
            if p.name in manifest:
                generated += 1
            else:
                rep.error("licenses", f"assets/{rel} is not in assets/manifest.json — "
                                      f"no recorded bake produced it")
            continue

        if rel not in text:
            rep.error("licenses", f"assets/{rel} has no entry in assets/LICENSES.md")
        third_party += 1
    rep.note(f"license check: {generated} generated (manifest-tracked), "
             f"{third_party} authored/third-party asset(s)")

    # rights gating: nothing may be derived from a source still awaiting a check
    for name, s in sources.items():
        if s.get("rights_status") in ("check_required", "restricted") \
                and s.get("asset_use") == "geometry":
            rep.error(f"source {name}",
                      f"rights_status is '{s['rights_status']}' but asset_use is 'geometry' — "
                      f"resolve the rights check before deriving geometry from this source")


def run_stale_check(structures: dict, rep: Report) -> None:
    """Does every committed GLB still match the inputs that made it?

    Until 2026-08-10 this function only asked whether each GLB appeared in
    `assets/manifest.json`. The manifest has recorded an `inputs_sha256` per asset
    since the first bake and nothing ever recomputed it, so "a stale committed GLB
    is a check failure, not a warning" (AGENTS.md) was a sentence, not a gate: a
    record could be edited into a different building and the town would keep
    rendering the old one, green.

    The recipe lives with the generators — `generators/mesh_inputs.py` for
    structures, `generators/terrain_inputs.py` for the ground — so the bake that
    writes the hash and the gate that checks it cannot drift apart.

    The two halves carry their own schemes, and the manifest records both, because
    they were redefined on different days for the same reason and a single version
    number would have made the second redefinition look like the first.
    """
    manifest_path = ROOT / "assets" / "manifest.json"
    gltf_dir = ROOT / "assets" / "gltf"
    glbs = sorted(gltf_dir.glob("*.glb"))
    if not manifest_path.exists():
        if glbs:
            rep.error("stale", "assets/gltf contains GLBs but assets/manifest.json is missing")
        else:
            rep.note("stale check: no baked assets yet")
        return

    manifest = json.loads(manifest_path.read_text())
    assets = manifest.get("assets", {})
    for g in glbs:
        if g.name not in assets:
            rep.error("stale", f"assets/gltf/{g.name} is not in manifest.json — "
                               f"it was not produced by a tracked bake")

    sys.path.insert(0, str(ROOT / "generators"))
    try:
        import mesh_inputs  # noqa: PLC0415
        import terrain_gen  # noqa: PLC0415
        import terrain_inputs  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        rep.error("stale", f"cannot import the generators' input-hash recipe, so no committed "
                           f"asset can be checked against its inputs: {e}")
        return

    schemes = {"inputs_scheme": (manifest.get("inputs_scheme"), mesh_inputs.SCHEME),
               "terrain_inputs_scheme": (manifest.get("terrain_inputs_scheme"),
                                         terrain_inputs.SCHEME)}
    for key, (recorded_scheme, computed) in schemes.items():
        if recorded_scheme != computed:
            rep.error("stale", f"manifest {key} is {recorded_scheme!r} but the generators compute "
                               f"{computed!r} — the two sides are hashing different things, so "
                               f"every comparison below would be meaningless. Re-stamp the "
                               f"manifest (and say in the commit why the definition changed)")
            return
    scheme = manifest.get("inputs_scheme")

    by_id = {st.get("id"): st for st in structures.values() if isinstance(st, dict)}
    fresh, stale, unchecked = 0, 0, 0

    for name, entry in sorted(assets.items()):
        if not (gltf_dir / name).exists():
            rep.error("stale", f"manifest.json lists {name} but assets/gltf/{name} does not "
                               f"exist — the record of a bake outlived its output")
            continue
        recorded = entry.get("inputs_sha256")
        if not recorded:
            rep.error("stale", f"{name} has no inputs_sha256, so nothing can say whether it "
                               f"still matches the data it was built from")
            continue
        try:
            if entry.get("structure_id"):
                st = by_id.get(entry["structure_id"])
                if st is None:
                    rep.error("stale", f"{name} was built from structure "
                                       f"'{entry['structure_id']}', which no longer exists in "
                                       f"data/structures — a mesh with no record behind it")
                    continue
                phase = next((p for p in st.get("phases", [])
                              if p.get("id") == entry.get("phase_id")), None)
                if phase is None:
                    rep.error("stale", f"{name} was built from phase '{entry.get('phase_id')}' "
                                       f"of {entry['structure_id']}, which the record no longer "
                                       f"has")
                    continue
                got = mesh_inputs.structure_inputs_sha(st, phase, entry.get("archetype"))
            elif entry.get("terrain_epoch"):
                ep_dir = DATA / "terrain" / "epochs" / entry["terrain_epoch"]
                got = terrain_gen.terrain_inputs_sha(ep_dir)
            else:
                unchecked += 1
                continue
        except Exception as e:  # noqa: BLE001 — an unresolvable input is a failure, not a skip
            rep.error("stale", f"{name}: cannot recompute its input hash: {e}")
            continue

        if got == recorded:
            fresh += 1
        else:
            stale += 1
            rep.error("stale", f"{name} is STALE — its inputs now hash to {got[:12]}, the "
                               f"committed mesh was built from {recorded[:12]}. The data and the "
                               f"geometry disagree, so the renderer is showing the old building. "
                               f"Re-bake it (tools/bake.sh, or the chicago-4d-bake workflow) and "
                               f"land the GLB with the change that caused this")

    rep.note(f"stale check: {fresh} asset(s) match their inputs, {stale} stale"
             + (f", {unchecked} not input-tracked" if unchecked else "")
             + f"; schemes {scheme} / {manifest.get('terrain_inputs_scheme')}, "
             + f"manifest blender {manifest.get('blender', '?')}")


def run_bake_reach_check(structures: dict, scenes: dict, rep: Report) -> None:
    """Can the bake rebuild everything the staleness gate holds it responsible for?

    The staleness gate above hashes `generators/build.py` into every asset, so a
    one-line comment in that file restales all 343 buildings and the remedy is a
    full rebake. That remedy has to be able to reach every asset it is asked to
    heal — and for one of them it could not.

    `build.py` walks `data/structures/` and resolves each record's phase against the
    SCENE's target date; a record no phase covers is skipped, printed as
    *"skip: no phase covers ..."*, and built by nothing. The first Cook County
    court-house is such a record: Andreas dates it to the fall of 1835 and the only
    scene targets 1 July, so `build.py --only cook_county_courthouse_1835` builds
    nothing — while its GLB was committed, was in the manifest, and WAS hashed by
    the staleness gate like every other asset. Editing `build.py` therefore staled
    an asset that the rebake could not then refresh, and the tree could not be made
    green by any committed route. It cost two runs their intended change (T-0008
    monkey-patched `resolve_phase` from a throwaway script; T-0015 reverted a
    demonstrated export guard rather than do that twice) before it was written down
    as T-0139.

    So the rule this asserts is the one that was being assumed: **a committed,
    input-tracked asset must be reachable by the bake.** Reachable means some scene
    in `data/scenes/` resolves that structure's phase — the same rule `build.py` and
    `validate_scene` apply, restated on the asset side.

    It is deliberately the mirror image of `check_drawn_by`'s "no GLB survives the
    move": that one catches geometry that outlived its build instructions, this one
    catches geometry no build instruction reaches. Both say a committed mesh must
    have a live route back to the data.

    Three ways to satisfy it, and the choice is the author's: give the scene set a
    date that covers the phase, teach `build.py` to take a phase explicitly, or stop
    committing the asset. T-0139 took the third for the court-house, because the
    scene already reports it as *"1 excluded by date"* and nothing loads it.
    """
    manifest_path = ROOT / "assets" / "manifest.json"
    if not manifest_path.exists():
        return
    assets = json.loads(manifest_path.read_text()).get("assets", {})

    targets = [(sid, parse_date(sc.get("target_date", "")))
               for sid, sc in sorted(scenes.items())]
    targets = [(sid, d) for sid, d in targets if d]
    if not targets:
        rep.note("bake-reach check: no scene carries a target_date, so nothing to resolve against")
        return

    by_id = {st.get("id"): st for st in structures.values() if isinstance(st, dict)}
    reachable, unreachable = 0, 0

    for name, entry in sorted(assets.items()):
        sid, pid = entry.get("structure_id"), entry.get("phase_id")
        if not sid or not pid:
            continue                      # terrain and other non-structure assets
        st = by_id.get(sid)
        if st is None:
            continue                      # run_stale_check already reports this
        hits = []
        for scene_id, target in targets:
            covering = []
            for ph in st.get("phases", []):
                rng = ph.get("documented_range", {})
                frm, to = parse_date(rng.get("from", "")), parse_date(rng.get("to", ""))
                if frm and to and frm <= target <= to:
                    covering.append(ph.get("id"))
            # exactly one, and it is this phase — the scene rule build.py applies
            if len(covering) == 1 and covering[0] == pid:
                hits.append(scene_id)
        if hits:
            reachable += 1
        else:
            unreachable += 1
            rep.error("bake-reach",
                      f"assets/gltf/{name} is committed and input-tracked, but no scene in "
                      f"data/scenes/ resolves {sid}'s phase '{pid}' — generators/build.py "
                      f"skips the record ('no phase covers <target>') and builds nothing, so "
                      f"the rebake that heals the rest of the town after any generators/ edit "
                      f"CANNOT heal this asset and the tree cannot be made green. Fix it by "
                      f"one of: a scene whose target_date the phase covers, an explicit-phase "
                      f"route in build.py, or not committing an asset nothing loads (T-0139)")

    rep.note(f"bake-reach check: {reachable} committed asset(s) a scene can rebuild"
             + (f", {unreachable} the bake cannot reach" if unreachable else ""))


def run_site_check(rep: Report) -> None:
    site = ROOT.parent.parent / "site" / "chicago" / "4d"
    if not site.exists():
        rep.note("site check: nothing published yet")
        return
    files = [p for p in site.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    mb = total / (1024 * 1024)
    if mb > SITE_BUDGET_MB:
        rep.error("site", f"published tree is {mb:.1f} MB, over the {SITE_BUDGET_MB} MB budget — "
                          f"GitHub Pages cannot serve Git LFS objects, so this has to stay lean. "
                          f"`python3 tools/site_budget.py` says where the bytes are (T-0722)")
    elif mb > SITE_BUDGET_MB * SITE_WARN_FRACTION:
        # A budget with no slack fails the NEXT PR either way, and until T-0722
        # nothing said so until it was already too late: dev reached 31.999 MB of
        # 32 in silence, and the run that discovered it was a run whose finished
        # work could not merge. This band is the warning that was missing — it
        # cannot stop a merge, and it is not meant to; it is meant to reach the
        # queue while there is still room to answer it.
        rep.warn("site", f"published tree is {mb:.2f} MB — {100 * mb / SITE_BUDGET_MB:.0f} % of the "
                         f"{SITE_BUDGET_MB} MB budget, {SITE_BUDGET_MB - mb:.2f} MB left. Print "
                         f"`python3 tools/site_budget.py` and open a ticket before it is a wall")
    rep.note(f"site check: published tree {mb:.2f} MB of {SITE_BUDGET_MB} MB budget "
             f"({SITE_BUDGET_MB - mb:.2f} MB headroom)")

    # THE SAME BYTES, SHIPPED TWICE — T-0722. The mirror carried the 1.31 MB
    # changelog under two URLs for as long as both paths existed, which is 4.1 % of
    # the budget spent on a copy, growing at twice the rate of the record. Nothing
    # noticed, because the only question ever asked of this tree was its total.
    #
    # A duplicate is not a judgement call the way a large file is: one of the two is
    # the file and the other is waste, and the answer is always a re-export, a
    # redirect or a deletion. So this refuses rather than warns. The floor keeps it
    # about payload rather than about tidiness — small identical files (an empty
    # index, a shared stub) are not what this is for.
    by_hash: dict[str, list[Path]] = {}
    for f in files:
        if f.stat().st_size < SITE_DUPE_FLOOR:
            continue
        by_hash.setdefault(hashlib.sha256(f.read_bytes()).hexdigest(), []).append(f)
    for paths in by_hash.values():
        if len(paths) < 2:
            continue
        size = paths[0].stat().st_size
        names = ", ".join(sorted(p.relative_to(site).as_posix() for p in paths))
        rep.error("site", f"{len(paths)} files in the published tree are byte-identical at "
                          f"{size / 1024:.0f} KB each — {names}. That is "
                          f"{size * (len(paths) - 1) / 1048576:.2f} MB of the budget spent on a "
                          f"copy. Publish one and re-export or redirect the others (T-0722)")
    # Only page directories need an index.html; asset and data directories are
    # fetched by explicit path and are never a bare URL a visitor lands on.
    def is_page_dir(d: Path) -> bool:
        rel = d.relative_to(site).as_posix()
        if rel.startswith(("data", "walk/vendor", "walk/js", "walk/css")):
            return False
        return any(p.suffix == ".html" for p in d.iterdir() if p.is_file()) or d == site

    for d in [site] + [p for p in site.rglob("*") if p.is_dir()]:
        if is_page_dir(d) and not (d / "index.html").exists():
            rep.warn("site", f"{d.relative_to(site.parent.parent)} is a page directory with "
                             f"no index.html — the bare URL will 404 on Pages")

    # The flora manifest names its own files, and the renderer fetches exactly
    # what it names — no probing — so a zone file that never reached site/ is a
    # 404 on the deployed walkthrough while the dev tree renders perfectly. This
    # is the failure mode publish.sh exists to prevent, checked rather than hoped.
    index_path = FLORA / "index.json"
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text())
        except json.JSONDecodeError:
            return
        wanted = ["index.json"] + [e.get("file") for e in index.get("zones", [])] \
            + [e.get("file") for e in index.get("palettes", [])]
        missing = [w for w in wanted if w and not (site / "data" / "flora" / w).exists()]
        if missing:
            rep.error("site", f"data/flora/ is not fully published: {len(missing)} file(s) "
                              f"the manifest names are absent from site/, starting with "
                              f"{missing[0]} — run tools/publish.sh")
        else:
            rep.note(f"site check: {len(wanted)} flora file(s) published")


if __name__ == "__main__":
    sys.exit(main())
