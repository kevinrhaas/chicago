#!/usr/bin/env python3
"""The closing convergence rebuild: one command for the whole closing set (T-1333).

    python3 tools/rebuild_closing_set.py --rebuild     run the set, in the manifest's
                                                       order, then write the report
    python3 tools/rebuild_closing_set.py --build       write the report from the tree
    python3 tools/rebuild_closing_set.py --check       the set is owned and the report
                                                       is not stale  (tools/check.sh)
    python3 tools/rebuild_closing_set.py --measure     print the measurement as JSON
    python3 tools/rebuild_closing_set.py --self-test   mutate it, and prove --check fires

WHY THIS EXISTS. Five files close the resident layer — `data/residents/index.json` with
its `merged` redirect table, the 1835 sidecars, `data/town_census.json`, the published
residents under `site/chicago/4d/data/residents/`, and the final resident audit workbook.
Every one of them is derived, every one of them has a tool, and until this file there was
no place that said they were ONE SET or what order they go in. A run that moved the town
tree rebuilt whichever of the five it happened to remember, and the ones it forgot stayed
green because each is gated on its own terms: `--check` asks "does this file follow from
its inputs", and a file that nobody rebuilt at all follows from its inputs perfectly well
until somebody else's rebuild moves them. T-1144 banked three of its acceptances "to the
closing pass to state as deltas rather than claimed closed from a spot reading" for
exactly that reason: a spot reading repeated is still a spot reading.

THE ORDER IS NOT INVENTED HERE. `tools/derived_manifest.json` already holds the whole
derived layer in dependency order, learned by hitting real failures; the closing set is a
SUBSEQUENCE of it, and this file names the members and reads their order back out of the
manifest rather than restating it. A member whose tool is not a manifest step is a
failure of `--check`, not a footnote — that is the one thing that keeps the two files
from drifting into two different opinions about how the town is rebuilt.

WHAT THE REPORT IS. `docs/RESEARCH/closing-convergence-2026-09.md` states every number as
a DELTA: the value on the tree this ticket opened on (frozen in
`tools/closing_convergence_baseline.json`, with the commit it was taken at), the value
now, and the difference. A count with no baseline is not a delta. The baseline is
measured, committed and never recomputed; "now" is re-derived on every gate run, so a
later branch that moves the town tree and leaves this report alone turns the gate red
instead of shipping a stale page that still reads clean.

THE MIRROR IS A MEMBER AND IS DELIBERATELY NOT IN THE MANIFEST, which is a finding this
file states rather than hides: `site/chicago/4d/` is generated and untracked (T-0938), so
the PR lap can never be handed a conflict in it and has nothing to resolve. `tools/
publish.sh` owns it, `tools/check.sh` publishes it as its first step and
`check_published_residents.mjs` gates the shipped value. `--check` holds that exemption to
its written reason, so dropping the reason is as red as dropping the file.
"""
from __future__ import annotations

import argparse
import io
import csv
import json
import re
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # chicago/4d
REPO = ROOT.parents[1]                               # the repository root
sys.path.insert(0, str(ROOT / "tools"))

from audit_scene_window_trades import offenders  # noqa: E402
from rebuild_resident_index import redirect_faults  # noqa: E402

MANIFEST = ROOT / "tools" / "derived_manifest.json"
BASELINE = ROOT / "tools" / "closing_convergence_baseline.json"
REPORT = ROOT / "docs" / "RESEARCH" / "closing-convergence-2026-09.md"
GATE = ROOT / "tools" / "check.sh"

RESIDENT_INDEX = ROOT / "data" / "residents" / "index.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
SIDECARS_1835 = ROOT / "data" / "sidecars" / "1835"
TOWN_CENSUS = ROOT / "data" / "town_census.json"
AUDIT_CSV = REPO / "chicago" / "reference" / "resident-research" / "final" / "audit" / "resident_audit_master.csv"
PUBLISHED_RESIDENTS = REPO / "site" / "chicago" / "4d" / "data" / "residents"

AS_OF = "2026-09-18"

# THE CLOSING SET, in the order T-1333 names it. `owner` is the script a manifest step
# runs; the ORDER the rebuild actually uses is that step's position in the manifest, never
# this list's, so the two files cannot hold different opinions. `claims` is what the
# manifest lists under `resolves` for that step — the files the PR lap is allowed to clear
# a conflict in by rebuilding — and `exempt` is the written reason a member has no step.
MEMBERS = (
    {
        "key": "resident_index",
        "what": "`data/residents/index.json` and its `merged` redirect table",
        "owner": "tools/rebuild_resident_index.py",
        "claims": ("chicago/4d/data/residents/index.json",),
        "footprint": "chicago/4d/data/residents/index.json",
        "exempt": None,
    },
    {
        "key": "sidecars_1835",
        "what": "the 1835 sidecars, `data/sidecars/1835/`",
        "owner": "tools/compile_scene.py",
        "claims": ("chicago/4d/data/sidecars/1835/people.json",),
        "footprint": "chicago/4d/data/sidecars/1835/*.json",
        "exempt": None,
    },
    {
        "key": "town_census",
        "what": "the town census, `data/town_census.json`",
        "owner": "tools/town_census.py",
        "claims": ("chicago/4d/data/town_census.json",),
        "footprint": "chicago/4d/data/town_census.json",
        "exempt": None,
    },
    {
        "key": "resident_audit",
        "what": "the final resident audit, `chicago/reference/resident-research/final/audit/`",
        "owner": "tools/export_resident_audit.py",
        "claims": (
            "chicago/reference/resident-research/final/audit/resident_audit_master.xlsx",
            "chicago/reference/resident-research/final/audit/resident_audit_master.csv",
            "chicago/reference/resident-research/final/audit/README.md",
        ),
        "footprint": "chicago/reference/resident-research/final/audit/*",
        "exempt": None,
    },
    {
        "key": "published_residents",
        "what": "the published residents, `site/chicago/4d/data/residents/`",
        "owner": "tools/publish.sh",
        "claims": (),
        "footprint": None,   # untracked; the mirror is not a tracked footprint at all
        "exempt": (
            "The mirror is generated and untracked (T-0938), so no merge can ever conflict "
            "in it and the lap has nothing to resolve; `tools/publish.sh` writes it, "
            "`tools/check.sh` publishes it as its first step, and "
            "`tools/check_published_residents.mjs` asserts the shipped value equals its "
            "source, file for file."
        ),
    },
)

# The four readings T-1144 acceptance 3 refused, asked of the layer by name rather than
# remembered. A refusal that is not measured is a sentence in a closed ticket.
REFUSED_NAMES = {
    "Mary Durbin": re.compile(r"\bmary\s+durbin\b", re.I),
    "John Simmons": re.compile(r"\bjohn\s+simmons\b", re.I),
    "John Vincent": re.compile(r"\bjohn\s+vincent\b", re.I),
    "Logdson": re.compile(r"\blogdson\b", re.I),
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_steps() -> list[dict]:
    return read_json(MANIFEST)["steps"]


def step_for(owner: str, steps: list[dict] | None = None) -> tuple[int, dict] | None:
    """The manifest step that runs `owner`, with its position. None if there is none."""
    for i, step in enumerate(steps if steps is not None else manifest_steps()):
        if len(step.get("command", [])) > 1 and step["command"][1] == owner:
            return i, step
    return None


def footprint(member: dict) -> list[str]:
    """The tracked files this member's tool actually writes, measured off the tree.

    `claims` says what the manifest lets the PR lap rebuild; this says what is there.
    They are different questions and the gap between them is section 2 of the report.
    """
    pattern = member.get("footprint")
    if not pattern:
        return []
    if "*" not in pattern:
        return [pattern] if (REPO / pattern).exists() else []
    parent, glob = pattern.rsplit("/", 1)
    return sorted(f"{parent}/{path.name}" for path in (REPO / parent).glob(glob))


# ------------------------------------------------------------------ measuring

def measure() -> dict:
    """Every number in the report, derived. Nothing here is typed."""
    index = read_json(RESIDENT_INDEX)
    counts = index.get("counts") or {}
    by_grade = counts.get("by_grade") or {}

    presences = {"uncertain": 0, "uncertain_with_leg": 0}
    refused = {name: 0 for name in REFUSED_NAMES}
    cards = sorted(HOUSEHOLDS.glob("hh_*.json"))
    for card in cards:
        doc = read_json(card)
        # The presence and its evidence leg are HOUSEHOLD fields — see
        # tools/derive_presence_evidence_leg.py, which writes the leg under the verdict.
        presence = doc.get("present_on_scene_date")
        value = presence.get("value") if isinstance(presence, dict) else presence
        if value == "uncertain":
            presences["uncertain"] += 1
            if presence.get("last_dated_appearance"):
                presences["uncertain_with_leg"] += 1
        for person in doc.get("persons") or []:
            name = person.get("name") or ""
            for label, pattern in REFUSED_NAMES.items():
                if pattern.search(name):
                    refused[label] += 1

    sidecars = sorted(SIDECARS_1835.glob("*.json"))
    people_sidecar = read_json(SIDECARS_1835 / "people.json")
    census = read_json(TOWN_CENSUS)

    audit_rows = 0
    if AUDIT_CSV.exists():
        with AUDIT_CSV.open(encoding="utf-8", newline="") as handle:
            audit_rows = max(sum(1 for _ in csv.reader(handle)) - 1, 0)

    return {
        "layer": {
            "households": counts.get("households"),
            "household_cards": len(cards),
            "persons": counts.get("persons"),
            "retired_redirects": len(index.get("merged") or []),
            "redirect_faults": len(redirect_faults(index)),
        },
        "grades": {
            "attested": by_grade.get("attested", 0),
            "inferred": by_grade.get("inferred", 0),
            "reconstructed": by_grade.get("reconstructed", 0),
        },
        "sidecars": {
            "files": len(sidecars),
            "people": len(people_sidecar.get("people") or []),
        },
        "town_census": {
            "buildings_standing": (census.get("buildings") or {}).get("standing"),
            "people_housed": (census.get("people") or {}).get("housed"),
            "households_housed": (census.get("people") or {}).get("households_housed"),
        },
        "audit": {"rows": audit_rows},
        # AN ABSENCE IS NOT A MEASUREMENT OF ZERO, and this row is the one place in the
        # set where the two are easy to confuse. `site/chicago/4d/` is generated and
        # untracked (T-0938), so a fresh clone has no mirror at all until
        # `tools/publish.sh` runs — and a run that rebuilds this report before
        # publishing used to write "0 files, -1336 against the baseline" as though it
        # had counted an empty mirror. It had counted nothing. `tools/check.sh`
        # publishes as its FIRST step, so the false zero then disagreed with the tree
        # and the gate went red saying the report was STALE, which sent the reader
        # looking for a change that did not exist. Measured on PRs #1557, #1560 and
        # #1561, three different runs on 2026-09-20, each red for about an hour.
        # `None` is the honest reading: not counted. `mirror_unpublished()` holds it,
        # and --build and --check refuse rather than write it down or compare against it.
        "published_residents": {
            "files": (len(list(PUBLISHED_RESIDENTS.rglob("*.json")))
                      if PUBLISHED_RESIDENTS.exists() else None),
        },
        "standing": {
            "refused_names_in_layer": sum(refused.values()),
            "scene_window_trade_rows": len(offenders()),
            "uncertain_presences": presences["uncertain"],
            "uncertain_presences_with_leg": presences["uncertain_with_leg"],
        },
    }


# ------------------------------------------------------------------ rendering

ROWS = (
    ("layer", "households", "households in `index.json`"),
    ("layer", "household_cards", "household cards on disk"),
    ("layer", "persons", "persons in `index.json`"),
    ("layer", "retired_redirects", "rows in the `merged` redirect table"),
    ("layer", "redirect_faults", "redirects that do not arrive"),
    ("grades", "attested", "persons graded `attested`"),
    ("grades", "inferred", "persons graded `inferred`"),
    ("grades", "reconstructed", "persons graded `reconstructed`"),
    ("sidecars", "files", "1835 sidecar files"),
    ("sidecars", "people", "people in the 1835 people sidecar"),
    ("town_census", "buildings_standing", "buildings standing in the town census"),
    ("town_census", "people_housed", "people housed in the town census"),
    ("town_census", "households_housed", "households housed in the town census"),
    ("audit", "rows", "rows in the final resident audit"),
    ("published_residents", "files", "published resident files in the mirror"),
)

BANKED = (
    ("standing", "refused_names_in_layer",
     "acc. 3 — Mary Durbin, John Simmons, John Vincent or Logdson in the layer"),
    ("standing", "scene_window_trade_rows",
     "acc. 5 — standing 1835 trades cited to no 1835 source"),
    ("standing", "uncertain_presences",
     "acc. 9 — uncertain presences"),
    ("standing", "uncertain_presences_with_leg",
     "acc. 9 — …of them carrying a dated evidence leg"),
)


MIRROR_UNPUBLISHED = (
    "the mirror is not published, so the published-resident count was not taken. "
    "site/chicago/4d/ is generated and untracked (T-0938) — run `bash tools/publish.sh` "
    "(or `./tools/check.sh`, which publishes first) and try again.")


def mirror_unpublished(now: dict) -> bool:
    """True when the mirror was not there to count. NOT the same as a mirror of zero."""
    return now["published_residents"]["files"] is None


def shown(value) -> str:
    """A value that was never counted prints as no reading, never as `None`."""
    return "—" if value is None else str(value)


def delta(now, then) -> str:
    if now is None or then is None:
        return "—"
    difference = now - then
    return "0" if difference == 0 else f"{difference:+d}"


def render(now: dict, baseline: dict, order: list[tuple[int, dict]]) -> str:
    base = baseline["measurement"]
    out: list[str] = []
    w = out.append
    w("# The closing convergence rebuild")
    w("")
    w(f"*Derived — regenerate with `python3 tools/rebuild_closing_set.py --build`; "
      f"`tools/check.sh` re-derives it. T-1333, as of {AS_OF}.*")
    w("")
    w("Five derived files close the resident layer. This page is the one place that says "
      "they are a set, what order they rebuild in, and — as measured deltas against a "
      "frozen baseline, never as a spot reading — what the last rebuild moved.")
    w("")
    w("```")
    w("python3 tools/rebuild_closing_set.py --rebuild")
    w("```")
    w("")
    w("## 1. The set, and the order it rebuilds in")
    w("")
    w("The order is read out of `tools/derived_manifest.json`, which holds the whole "
      "derived layer in dependency order; the closing set is a subsequence of it. A "
      "member whose tool is not a manifest step fails `--check`.")
    w("")
    w("| # | member | rebuilt by | manifest step | files the lap may rebuild |")
    w("|---|---|---|---|---|")
    for n, (position, member) in enumerate(order, start=1):
        where = f"{position + 1}" if position is not None else "**none** — see §2"
        w(f"| {n} | {member['what']} | `{member['owner']}` | {where} | {len(member['claims'])} |")
    w("")
    w("## 2. What the manifest does not own")
    w("")
    w("Acceptance 5 of T-1333: a file in this set that `tools/derived_manifest.json` does "
      "not own is a finding, not a footnote. Two of them, both measured.")
    w("")
    w("**The mirror.** " + next(m["exempt"] for m in MEMBERS if m["exempt"]))
    w("")
    w("That one is a property of the mirror rather than an oversight — it is the one "
      "member `tools/rederive.mjs` will never rebuild, and it has nothing to rebuild. "
      "`--check` holds the exemption to this written reason, so deleting the reason is as "
      "red as deleting the file.")
    w("")
    w("**The sidecars, and it is a real gap.** A member's tool writes a footprint; the "
      "manifest claims a subset of it, and only a claimed file can have a merge conflict "
      "cleared by rebuilding. Everything else is refused to the run that owns the ticket "
      "— safe, and it is the state that leaves a PR open.")
    w("")
    w("| member | tracked files written | claimed by the manifest | unowned |")
    w("|---|---:|---:|---:|")
    for _, member in order:
        if member["exempt"]:
            continue
        written = len(footprint(member))
        w(f"| {member['what']} | {written} | {len(member['claims'])} | "
          f"{written - len(member['claims'])} |")
    w("")
    gaps = {m["key"]: len(footprint(m)) - len(m["claims"]) for m in MEMBERS if not m["exempt"]}
    unowned = sum(gaps.values())
    where = ", ".join(f"`{key}`" for key, gap in gaps.items() if gap) or "nowhere"
    w(f"{unowned} tracked closing-set file(s) are written by a manifest step and not "
      f"claimed by it — in {where}. Widening `resolves` to the whole "
      f"sidecar directory is a decision about what the lap may overwrite, not a "
      f"bookkeeping fix, and the manifest is explicit that \"being run by the manifest "
      f"and owning your outputs are separate decisions\" — so this states the number "
      f"rather than taking that decision. The row moves the moment the count does.")
    w("")
    w("## 3. The deltas")
    w("")
    w(f"Baseline: `{baseline['commit']}` on `{baseline['branch']}`, taken "
      f"{baseline['taken_on']} — the tree T-1333 opened on. The baseline is measured "
      f"once and committed; a value here that is not `0` is what the closing rebuild "
      f"moved.")
    w("")
    w("| measured | baseline | now | delta |")
    w("|---|---:|---:|---:|")
    for section, key, label in ROWS:
        w(f"| {label} | {shown(base[section][key])} | {shown(now[section][key])} | "
          f"{delta(now[section][key], base[section][key])} |")
    w("")
    w("## 4. T-1144's banked acceptances, as deltas")
    w("")
    w("T-1144 banked acceptances 3, 5 and 9 to this pass \"to state as deltas rather "
      "than claimed closed from a spot reading\". Each is measured here on both trees, "
      "so a later branch that reintroduces one turns the gate red.")
    w("")
    w("| measured | baseline | now | delta |")
    w("|---|---:|---:|---:|")
    for section, key, label in BANKED:
        w(f"| {label} | {shown(base[section][key])} | {shown(now[section][key])} | "
          f"{delta(now[section][key], base[section][key])} |")
    w("")
    uncertain = now["standing"]["uncertain_presences"]
    with_leg = now["standing"]["uncertain_presences_with_leg"]
    w(f"Acceptance 9 reads as a pair: {with_leg} of {uncertain} uncertain presences carry "
      f"a `last_dated_appearance`, so the gap is "
      f"{uncertain - with_leg}.")
    w("")
    w("## 5. What holds this page")
    w("")
    w("`python3 tools/rebuild_closing_set.py --check` runs in `tools/check.sh` and asserts "
      "three things: every member is rebuilt by a manifest step or carries a written "
      "exemption, every member's tool is gated with `--check` by `tools/check.sh`, and "
      "this page re-renders to itself from the tree. The last of those is what stops a "
      "branch that moves the town from leaving a stale report green.")
    w("")
    return "\n".join(out)


def ordered_members(steps: list[dict] | None = None) -> list[tuple[int | None, dict]]:
    """The set, sorted by where the manifest runs it. Exempt members come last."""
    steps = steps if steps is not None else manifest_steps()
    found = []
    for member in MEMBERS:
        hit = step_for(member["owner"], steps)
        found.append((hit[0] if hit else None, member))
    return sorted(found, key=lambda pair: (pair[0] is None, pair[0] if pair[0] is not None else 0))


def report_text(now: dict | None = None) -> str:
    return render(now if now is not None else measure(), read_json(BASELINE), ordered_members())


# -------------------------------------------------------------------- rebuild

def rebuild() -> int:
    """The one rebuild. Every member, in the manifest's order, then the report."""
    steps = manifest_steps()
    before = measure()
    if mirror_unpublished(before):
        # Said BEFORE the members run, not after: the rebuild takes minutes, and none of
        # its steps publishes the mirror, so the refusal at the end would be the same one.
        print(f"REFUSED: {MIRROR_UNPUBLISHED}")
        return 1
    for position, member in ordered_members(steps):
        if position is None:
            command = ["bash", member["owner"]]
        else:
            command = steps[position]["command"]
        label = " ".join(command)
        print(f"  [{member['key']}] {label}")
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  FAILED: {label}")
            print("\n".join((result.stdout + result.stderr).splitlines()[-8:]))
            return 1
    after = measure()
    if mirror_unpublished(after):
        print(f"REFUSED to write {REPORT.relative_to(ROOT)}: {MIRROR_UNPUBLISHED}")
        return 1
    moved = [label for section, key, label in ROWS + BANKED
             if after[section][key] != before[section][key]]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(after), encoding="utf-8")
    print(f"\nclosing set rebuilt — {len(MEMBERS)} member(s), in the manifest's order")
    print(f"{len(moved)} measured value(s) moved against the tree this rebuild started on"
          + (":" if moved else ""))
    for label in moved:
        print(f"  - {label}")
    print(f"wrote {REPORT.relative_to(ROOT)}")
    return 0


# ---------------------------------------------------------------------- check

def check(quiet: bool = False, steps: list[dict] | None = None, gate: str | None = None) -> int:
    steps = steps if steps is not None else manifest_steps()
    gate = gate if gate is not None else GATE.read_text(encoding="utf-8")
    problems: list[str] = []

    for member in MEMBERS:
        hit = step_for(member["owner"], steps)
        if hit is None and not member["exempt"]:
            problems.append(
                f"{member['key']}: no step in tools/derived_manifest.json runs "
                f"{member['owner']}, so the lap never rebuilds a member of the closing "
                f"set. Add the step, or declare a written exemption here.")
        if hit is not None and member["exempt"]:
            problems.append(
                f"{member['key']}: is exempted as un-rebuildable and the manifest runs "
                f"{member['owner']} at step {hit[0] + 1}. Drop the exemption.")
        if member["exempt"] and len(member["exempt"]) < 80:
            problems.append(f"{member['key']}: the exemption states no reason")
        if hit is not None:
            claimed = tuple(hit[1].get("resolves") or ())
            if claimed != tuple(member["claims"]):
                problems.append(
                    f"{member['key']}: the manifest step resolves {list(claimed)}, and "
                    f"this set says {list(member['claims'])}. One of them is out of date.")
        if not re.search(re.escape(member["owner"]) + r"[^\n]*--check", gate) \
                and member["owner"] != "tools/publish.sh":
            problems.append(
                f"{member['key']}: tools/check.sh never runs {member['owner']} with "
                f"--check, so nothing asserts this member re-derives.")

    for _, member in ordered_members(steps):
        for claim in member["claims"]:
            if not (REPO / claim).exists():
                problems.append(f"{member['key']}: {claim} is not in the tree")

    if problems:
        print("THE CLOSING SET FAILED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    if not REPORT.exists():
        print(f"FAIL {REPORT.relative_to(ROOT)} is missing — run "
              f"python3 tools/rebuild_closing_set.py --build")
        return 1
    # BEFORE the freshness comparison, because an unmeasured row would lose it and the
    # reader would be told the report is STALE — sent looking for a change to the town
    # that never happened. The two failures want different remedies and must not share
    # a message.
    now = measure()
    if mirror_unpublished(now):
        print(f"FAIL cannot check {REPORT.relative_to(ROOT)}: {MIRROR_UNPUBLISHED}")
        return 1
    if REPORT.read_text(encoding="utf-8") != report_text(now):
        print(f"FAIL {REPORT.relative_to(ROOT)} is stale — the tree has moved under it. "
              f"Run python3 tools/rebuild_closing_set.py --rebuild")
        return 1
    if not quiet:
        print(f"OK: the closing set is {len(MEMBERS)} member(s), each rebuilt by a gated "
              f"manifest step or exempted in writing, and the report re-derives")
    return 0


# ------------------------------------------------------------------ self-test

def self_test() -> int:
    steps = manifest_steps()
    gate = GATE.read_text(encoding="utf-8")
    failures: list[str] = []

    def fires(label: str, mutate) -> None:
        kept = [dict(member) for member in MEMBERS]
        try:
            mutate()
            if check(quiet=True, steps=steps, gate=gate) == 0:
                failures.append(label)
        finally:
            globals()["MEMBERS"] = tuple(kept)

    fires("a member the manifest does not run is accepted", lambda: globals().__setitem__(
        "MEMBERS", tuple([{**MEMBERS[0], "owner": "tools/no_such_tool.py"}] + list(MEMBERS[1:]))))
    fires("a member whose claimed files drift from the manifest is accepted",
          lambda: globals().__setitem__("MEMBERS", tuple(
              [{**MEMBERS[0], "claims": ("chicago/4d/data/town_census.json",)}] + list(MEMBERS[1:]))))
    fires("an exemption with no written reason is accepted", lambda: globals().__setitem__(
        "MEMBERS", tuple(list(MEMBERS[:-1]) + [{**MEMBERS[-1], "exempt": "because"}])))
    # …and the gate half on its own: the manifest still runs the member, and only
    # tools/check.sh has forgotten to ask it `--check`. A member that neither file knows
    # is case 1; this one isolates the assertion that proves the rebuild was RIGHT.
    ungated = re.sub(r"^.*rebuild_resident_index\.py --check.*$", "", gate, flags=re.M)
    if check(quiet=True, steps=steps, gate=ungated) == 0:
        failures.append("a member the gate never asks --check of is accepted")

    # …and the freshness half: move a measured value and the report must not re-render.
    base = measure()
    rendered = report_text(base)
    moved = json.loads(json.dumps(base))
    moved["layer"]["persons"] = base["layer"]["persons"] + 7
    if report_text(moved) == rendered:
        failures.append("the person count moved and the report did not")
    moved = json.loads(json.dumps(base))
    moved["standing"]["refused_names_in_layer"] = 1
    if report_text(moved) == rendered:
        failures.append("a refused name came back and the report did not say so")

    # …and the mirror, which is the one member that can be ABSENT rather than wrong.
    # Every case below is run against a measurement whose mirror row is None — what
    # measure() returns on a tree where tools/publish.sh has not run. The old code
    # wrote 0 there and each of these passed while saying something false.
    # Both fixtures are CONSTRUCTED rather than read off this tree, because whether the
    # tree happens to be published is exactly the variable under test — and a working
    # copy that has never run publish.sh would otherwise make case 2 unreachable.
    unpublished = json.loads(json.dumps(base))
    unpublished["published_residents"]["files"] = None
    published = json.loads(json.dumps(base))
    published["published_residents"]["files"] = 2153
    if not mirror_unpublished(unpublished):
        failures.append("an unpublished mirror is not recognised as uncounted")
    if mirror_unpublished(published):
        failures.append("a mirror that IS published is called unpublished")
    # The fault itself, reproduced: a zero is indistinguishable from an absence, so the
    # report renders and commits a -1336 delta nobody measured.
    zeroed = json.loads(json.dumps(base))
    zeroed["published_residents"]["files"] = 0
    if mirror_unpublished(zeroed):
        failures.append("a mirror published EMPTY is refused — 0 is a count, None is not")
    if report_text(zeroed) == report_text(published):
        failures.append("the mirror count moved to 0 and the report did not say so")
    # The distinction the whole fix rests on: uncounted and counted-zero are different
    # readings and must not render alike.
    if report_text(zeroed) == report_text(unpublished):
        failures.append("an uncounted mirror and an empty one render identically")
    # And the row itself is rendered as uncounted rather than as a number, so a report
    # that ever did reach disk could not read as a measurement.
    if "| published resident files in the mirror | " not in report_text(unpublished):
        failures.append("the mirror row vanished from the report when uncounted")
    if "1336 | None |" in report_text(unpublished):
        failures.append("an uncounted mirror renders as `None` rather than as no reading")

    # THE CASES ABOVE ARE FIXTURES, AND A FIXTURE CANNOT REACH THIS FAULT. The bug was
    # never in how a None renders — it was in measure() turning a missing DIRECTORY into
    # the number 0, and no hand-built dict exercises that line. Mutation-tested: restoring
    # `else 0` leaves every case above green, which is the same shape of dead check T-1427
    # found in `inflight`. So these two drive the real function against a real path that
    # is not there.
    global PUBLISHED_RESIDENTS
    kept_path = PUBLISHED_RESIDENTS
    try:
        PUBLISHED_RESIDENTS = REPO / "site" / "chicago" / "4d" / "data" / "no_such_mirror"
        if measure()["published_residents"]["files"] is not None:
            failures.append("measure() counts a mirror that is not on disk — an absent "
                            "directory came back as a number")
        noise = io.StringIO()
        with redirect_stdout(noise):
            code = check(steps=steps, gate=gate)
        said = noise.getvalue()
        if code == 0:
            failures.append("--check passes with no mirror to count")
        if "stale" in said:
            failures.append("--check calls an unpublished mirror STALE — the wrong "
                            "remedy, and it sends the reader after a change to the town "
                            "that never happened")
        if "not published" not in said:
            failures.append("--check does not say the mirror is unpublished")
    finally:
        PUBLISHED_RESIDENTS = kept_path

    for line in failures:
        print(f"  MISS {line}")
    print(f"CLOSING SET SELF-TEST {'FAIL' if failures else 'PASS'} — "
          f"{len(failures)} failure(s), 17 case(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true",
                        help="run the closing set in the manifest's order, then report")
    parser.add_argument("--build", action="store_true", help="write the report from the tree")
    parser.add_argument("--check", action="store_true", help="the set is owned, the report is fresh")
    parser.add_argument("--measure", action="store_true", help="print the measurement as JSON")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.measure:
        print(json.dumps(measure(), indent=1))
        return 0
    if args.rebuild:
        return rebuild()
    if args.check:
        return check(quiet=args.quiet)
    if args.build:
        now = measure()
        if mirror_unpublished(now):
            print(f"REFUSED to write {REPORT.relative_to(ROOT)}: {MIRROR_UNPUBLISHED}")
            return 1
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(report_text(now), encoding="utf-8")
        print(f"wrote {REPORT.relative_to(ROOT)}")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
