#!/usr/bin/env python3
"""Which RECORDS a read reaches — the cohort behind K42's read-set.

ROADMAP K44, opened by K42. That parcel asked whether a FIGURE is read: does any
file under `renderers/web/js/` contain an expression that touches
`species[].july.inflorescence.shape`? One file does, so the figure is `mesh` and
the map is finished with it.

The map is finished with it for all 154 species records at once, and no reader in
this project has ever received all 154. **Every reader takes a cohort**, and the
cohorts are declared in the renderer as three different kinds of literal:

    renderers/web/js/flora.js   OUR_ROLES        5 of the manifest's 7 roles
                                GRAMINOID_FORMS  \\ 15 forms between them, which is
                                FORB_FORMS       / the whole `forms_flora` list
                                every zone the manifest publishes

    renderers/web/js/trees.js   role === 'tree' || role === 'thicket'
                                FORM_OF          the 5 `forms_trees` forms
                                TIMBER_ZONES     FOUR of the manifest's TEN zones

So a figure read by `flora.js` reaches nothing on a record `flora.js` never
receives, and the read-set cannot see it: the two statements *"this figure is
read"* and *"this record is read"* are different, and the second one is nobody's
gate. This is that gate. It multiplies K42's map by the routing above and counts
the (record, figure) pairs the map calls read and the renderer never sees.

    tools/measure_flora_reach.py             print the census
    tools/measure_flora_reach.py --gate      exit 1 on a divergence
    tools/measure_flora_reach.py --self-test break each assertion, in memory
    tools/measure_flora_reach.py --update    rewrite the baseline

WHAT IT MEASURES, AND THE LIMIT IT DOES NOT MEASURE. Routing only: which reader
is handed the record. Whether a routed record then has ground to stand on is a
different question with a different answer — a zone whose extent meets no
modelled ground plants nothing however well it is routed, which K42's finding
4(b) already records for zones 7-9 — and this tool does not ask it. A record it
calls reached is a record the reader receives, not a plant a visitor is
guaranteed to be standing in front of. Saying so here is cheaper than having the
next parcel discover it.

THE READER SETS ARE SCANNED, NEVER HARDCODED. Every set above is read out of the
renderer source at run time, and a set this file cannot find is a failure rather
than an empty set that quietly routes nothing — K42's lesson about a declaration
that stops being true, applied to the declaration this file is made of. The
figure-level read sets are K42's own `FLORA_ZONE_READS`, imported rather than
copied, so the two gates cannot drift apart: a figure whose declaration moves
moves here too.

FIVE ASSERTIONS.

1.  **(absolute) Every routing declaration is still in the renderer**, and the
    manifest's published form vocabularies still match the renderers' dispatch
    tables in both directions. `forms_flora` is what `flora.js` draws,
    `forms_trees` is what `trees.js` draws, and `forms_unimplemented` is the
    list the manifest says nothing draws. A form added to the data's vocabulary
    without an archetype is a species the renderer reports at boot to nobody.

2.  **(absolute) The two cohorts are disjoint and total.** Every record's role is
    in the manifest's published `roles` vocabulary, and no role is claimed by
    both readers. A record that two readers receive would be drawn twice, and
    the arithmetic below would be wrong rather than the town.

3.  **(absolute, banked both ways) The records that reach NO reader are exactly
    the banked set**, with the reason each. A new one fails; a banked one that
    has become reachable fails until it is un-banked in the commit that routed
    it. Six today, and four of them are the lakeshore's woody records — trees
    researched, committed, cited, and handed to nothing.

4.  **(absolute, banked both ways) Every declared-read figure whose carriers are
    not ALL reached is banked with its counts.** This is the parcel's own
    finding held in place: the read-set may not call a figure read again without
    this file recording which of its records that read reaches.

5.  **(absolute, banked both ways) Every record carrying a `july.inflorescence`
    whose head is not drawn is banked with a reason.** The July gate in
    `flora.js` and the archetype table are inside the reader; this is the third
    place a recorded flower can be lost, and it is the one K43's fruit half was
    written about.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import measure_layer_reads as k42  # noqa: E402  (the map this file multiplies)

DATA = ROOT / "data" / "flora"
RENDERER = ROOT / "renderers" / "web" / "js"
BASELINE = ROOT / "tools" / "flora_reach_baseline.json"

FLORA_JS = "flora.js"
TREES_JS = "trees.js"

# The reasons a record reaches no reader. Named rather than free text, because a
# bank of reasons is only worth having if two runs spell them the same way.
UNROUTED_REASONS = {
    "form-not-implemented": "its `form` is in no reader's dispatch table",
    "zone-not-read": "its reader does not open this zone",
    "role-unrouted": "its `role` is in no reader's cohort",
}

# The functions that actually put an inflorescence into a buffer, one per
# reader. `flora.js` instances its heads through `maybeHead`; `trees.js` merges
# them through `addHead` (ROADMAP K45(c)). A reader that grows a third way to
# draw a flower has to be named here, and until it is, this gate says its
# cohort's flowers are not drawn — which is the safe direction to be wrong in.
HEAD_EMITTERS = ("maybeHead", "addHead")

# The reasons a recorded inflorescence draws no head.
NO_HEAD_REASONS = {
    "record-unrouted": "the record reaches no reader at all",
    "reader-draws-no-head": "the reader that receives it has no head archetype",
    "july-gate": "its reader refuses a head on a vegetative or budding record",
    "shape-no-archetype": "its recorded shape has no archetype in its reader's table",
}


# ---------------------------------------------------------------------------
# the renderer, read for its cohorts
# ---------------------------------------------------------------------------

def renderer_source(name: str) -> str:
    """One renderer file with its comments stripped.

    Stripped for the same reason K42 strips: `flora.js` discusses the fields it
    reads in prose three lines above the line that reads them, and a scan that
    matches its own commentary proves nothing.
    """
    path = RENDERER / name
    if not path.exists():
        raise LookupError(f"{path.relative_to(ROOT)} is not there — this gate is "
                          f"describing a renderer that no longer exists")
    return k42.strip_js_comments(path.read_text(encoding="utf-8"))


def js_set(src: str, name: str, where: str) -> set[str]:
    """`const NAME = new Set([...])` — the string literals in it."""
    m = re.search(rf"const {re.escape(name)}\s*=\s*new Set\(\[(.*?)\]\)", src, re.S)
    if not m:
        raise LookupError(f"{where} no longer declares `{name}` as a Set — this gate "
                          f"routes every record through it, so an empty one would pass "
                          f"the whole town silently")
    return set(re.findall(r"'([^']*)'", m.group(1)))


def js_array(src: str, name: str, where: str) -> set[str]:
    """`const NAME = [ 'a', 'b' ];` — the string literals in it."""
    m = re.search(rf"const {re.escape(name)}\s*=\s*\[(.*?)\];", src, re.S)
    if not m:
        raise LookupError(f"{where} no longer declares `{name}` as an array — this gate "
                          f"decides which zones a reader opens from it")
    return set(re.findall(r"'([^']*)'", m.group(1)))


def js_object_keys(src: str, name: str, where: str) -> set[str]:
    """`const NAME = { key: ..., }` — the top-level keys, at one indent."""
    m = re.search(rf"const {re.escape(name)}\s*=\s*\{{(.*?)\n\}};", src, re.S)
    if not m:
        raise LookupError(f"{where} no longer declares `{name}` as an object — this gate "
                          f"reads a reader's dispatch table out of it")
    return set(re.findall(r"^\s{2}(\w+)\s*:", m.group(1), re.M))


def js_role_guard(src: str, where: str) -> set[str]:
    """The roles `trees.js` accepts, off its own guard line.

    Written as a negated pair — `if (sp.role !== 'tree' && sp.role !== 'thicket')
    continue;` — because that is what a cohort looks like when it is two values
    rather than a Set. Scanned rather than assumed for the same reason as the
    rest: the pair moving is exactly the change this gate exists to notice.
    """
    m = re.search(r"role\s*!==\s*'(\w+)'\s*&&\s*[\w.?]*role\s*!==\s*'(\w+)'", src)
    if not m:
        raise LookupError(f"{where} no longer guards on a pair of roles — the cohort this "
                          f"gate attributes to it cannot be read")
    return {m.group(1), m.group(2)}


def js_draws_heads(src: str, where: str) -> bool:
    """Whether a reader has a head path at all, off its own code.

    A shape table with entries in it is not the same claim as a renderer that
    draws from it, so both halves are required: the archetype table, and a call
    to one of the two emitters below. Named rather than pattern-guessed, because
    a regex loose enough to match any future emitter is loose enough to match a
    comment about one — and this file strips comments precisely so that it
    cannot.
    """
    has_table = re.search(r"const \w*HEAD_OF_SHAPE\s*=\s*\{", src) is not None
    draws = any(re.search(rf"\b{name}\s*\(", src) for name in HEAD_EMITTERS)
    if has_table != draws:
        raise LookupError(
            f"{where} has a head archetype table and no emitter, or an emitter and no "
            f"table ({has_table=}, {draws=}) — this gate cannot say whether a flower "
            f"on its cohort is drawn, and guessing either way misreports every one")
    return has_table


def cohorts() -> dict:
    """Every routing declaration, scanned out of the two readers."""
    flora = renderer_source(FLORA_JS)
    trees = renderer_source(TREES_JS)
    manifest = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    zones = [z["id"] for z in manifest.get("zones", [])]
    return {
        "sources": {FLORA_JS: flora, TREES_JS: trees},
        "manifest": manifest,
        "zones": zones,
        FLORA_JS: {
            "roles": js_set(flora, "OUR_ROLES", FLORA_JS),
            "forms": (js_set(flora, "GRAMINOID_FORMS", FLORA_JS)
                      | js_set(flora, "FORB_FORMS", FLORA_JS)),
            "zones": set(zones),          # it iterates the manifest's own list
            "shapes": js_object_keys(flora, "HEAD_OF_SHAPE", FLORA_JS),
            "draws_heads": js_draws_heads(flora, FLORA_JS),
        },
        TREES_JS: {
            "roles": js_role_guard(trees, TREES_JS),
            "forms": js_object_keys(trees, "FORM_OF", TREES_JS),
            "zones": js_array(trees, "TIMBER_ZONES", TREES_JS),
            # SCANNED, not declared, and that is a repair rather than a tidy-up.
            # Until K45(c) these two fields were the literals `set()` and
            # `False` — the one pair of routing facts in this gate that was
            # asserted here instead of measured out of the reader. A head path
            # added to `trees.js` would therefore have gone on being reported as
            # absent for as long as nobody edited THIS file, and the assertion
            # is exact in both directions, so it would have PASSED while saying
            # the opposite of what the renderer does. Every other cohort field
            # above is scanned for exactly this reason.
            "shapes": js_object_keys(trees, "WOODY_HEAD_OF_SHAPE", TREES_JS),
            "draws_heads": js_draws_heads(trees, TREES_JS),
        },
    }


def figure_readers(sources: dict[str, str]) -> dict[str, dict]:
    """Per declared-read figure: which files read it.

    Two scans, unioned, because either alone is wrong here. K42's declaration
    names ONE expression per figure and several of these fields are read by both
    files through different expressions — `sp.height_m` is destructured in
    `flora.js` and type-checked in `trees.js` — so the expression alone
    undercounts. The bare leaf scan alone overcounts nothing but misses the
    renamed local: `flora.js` reads `inflor.rgb` off a variable, and `rgb` is an
    ambiguous leaf K42 scans parent-qualified, so the leaf scan cannot see it.
    """
    out: dict[str, dict] = {}
    for path, (state, expr) in k42.FLORA_ZONE_READS.items():
        if not path.startswith("species[]."):
            continue
        readers = {name for name, src in sources.items() if expr in src}
        readers |= {name for name, src in sources.items() if k42.reads_leaf(src, path)}
        out[path] = {"state": state, "expr": expr, "readers": readers}
    return out


# ---------------------------------------------------------------------------
# the data, routed
# ---------------------------------------------------------------------------

def species_records(manifest: dict) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    for entry in manifest.get("zones", []):
        path = DATA / entry["file"]
        rec = json.loads(path.read_text(encoding="utf-8"))
        for sp in rec.get("species", []):
            out.append((entry["id"], sp))
    return out


def route(zone_id: str, sp: dict, coh: dict) -> tuple[str | None, str | None]:
    """Which reader receives this record, or why none does."""
    role, form = sp.get("role"), sp.get("form")
    for name in (FLORA_JS, TREES_JS):
        c = coh[name]
        if role not in c["roles"]:
            continue
        if form not in c["forms"]:
            return None, "form-not-implemented"
        if zone_id not in c["zones"]:
            return None, "zone-not-read"
        return name, None
    return None, "role-unrouted"


def leaf_at(sp: dict, path: str):
    """The value at `species[].a.b`, or `KeyError` if the record does not carry it."""
    node = sp
    for key in path[len("species[]."):].split("."):
        if not isinstance(node, dict) or key not in node:
            raise KeyError(path)
        node = node[key]
    return node


def head_state(reader: str | None, unrouted: str | None, sp: dict, coh: dict) -> str | None:
    """Why a recorded inflorescence draws no head, or None if one is drawn."""
    july = sp.get("july") or {}
    inflor = july.get("inflorescence")
    if not inflor:
        return None
    if reader is None:
        return "record-unrouted"
    if not coh[reader]["draws_heads"]:
        return "reader-draws-no-head"
    if july.get("phenology") in ("vegetative", "budding"):
        return "july-gate"
    if inflor.get("shape") not in coh[reader]["shapes"]:
        return "shape-no-archetype"
    return None


def classify() -> dict:
    coh = cohorts()
    figures = figure_readers(coh["sources"])
    manifest = coh["manifest"]
    vocabulary = manifest.get("vocabulary", {})

    unrouted: dict[str, dict] = {}
    heads: dict[str, dict] = {}
    per_figure: dict[str, dict] = {
        path: {"carriers": 0, "reached": 0, "readers": sorted(f["readers"]),
               "state": f["state"]}
        for path, f in figures.items()
    }
    by_reader: dict[str, int] = {FLORA_JS: 0, TREES_JS: 0, "none": 0}
    roles_seen: set[str] = set()
    pairs = reached_pairs = 0

    for zone_id, sp in species_records(manifest):
        reader, why = route(zone_id, sp, coh)
        key = f"{zone_id}/{sp.get('id') or sp.get('binomial') or '?'}"
        roles_seen.add(sp.get("role"))
        by_reader[reader or "none"] += 1
        if reader is None:
            unrouted[key] = {"role": sp.get("role"), "form": sp.get("form"),
                             "reason": why}
        state = head_state(reader, why, sp, coh)
        if state:
            heads[key] = {"shape": (sp.get("july") or {}).get("inflorescence", {})
                          .get("shape"), "phenology": (sp.get("july") or {})
                          .get("phenology"), "reason": state}
        for path, f in figures.items():
            try:
                leaf_at(sp, path)
            except KeyError:
                continue
            per_figure[path]["carriers"] += 1
            pairs += 1
            if reader in f["readers"]:
                per_figure[path]["reached"] += 1
                reached_pairs += 1

    partial = {path: {"carriers": v["carriers"], "reached": v["reached"],
                      "unreached": v["carriers"] - v["reached"],
                      "readers": v["readers"], "state": v["state"]}
               for path, v in per_figure.items() if v["carriers"] != v["reached"]}

    return {
        "cohorts": {name: {k: sorted(v) for k, v in coh[name].items()
                           if isinstance(v, set)} for name in (FLORA_JS, TREES_JS)},
        "vocabulary": {k: sorted(vocabulary.get(k, [])) for k in
                       ("roles", "forms_flora", "forms_trees", "forms_unimplemented")},
        "records": sum(by_reader.values()),
        "by_reader": by_reader,
        "unrouted": unrouted,
        "heads": heads,
        "figures": partial,
        "figure_count": len(per_figure),
        "pairs": pairs,
        "reached_pairs": reached_pairs,
        "roles_seen": sorted(r for r in roles_seen if r),
        "vocabulary_faults": vocabulary_faults(coh, vocabulary),
        "overlap": sorted(coh[FLORA_JS]["roles"] & coh[TREES_JS]["roles"]),
    }


def vocabulary_faults(coh: dict, vocabulary: dict) -> list[str]:
    """Assertion 1's second half: the manifest's lists against the dispatch tables."""
    out: list[str] = []
    pairs = [("forms_flora", FLORA_JS), ("forms_trees", TREES_JS)]
    for key, reader in pairs:
        published = set(vocabulary.get(key, []))
        drawn = coh[reader]["forms"]
        for form in sorted(published - drawn):
            out.append(f"data/flora/index.json publishes form '{form}' in `{key}` and "
                       f"{reader} has no archetype for it — a species recording it is "
                       f"reported at boot and drawn as nothing")
        for form in sorted(drawn - published):
            out.append(f"{reader} draws form '{form}' and `{key}` in the manifest does "
                       f"not publish it — the vocabulary a record is validated against "
                       f"and the table that draws it disagree")
    unimplemented = set(vocabulary.get("forms_unimplemented", []))
    both = coh[FLORA_JS]["forms"] | coh[TREES_JS]["forms"]
    for form in sorted(unimplemented & both):
        out.append(f"form '{form}' is published as deliberately unimplemented and a "
                   f"reader now draws it — un-publish it, because a record author is "
                   f"reading that list as a promise")
    return out


# ---------------------------------------------------------------------------
# the assertions
# ---------------------------------------------------------------------------

def read_bank() -> dict:
    if not BASELINE.exists():
        return {"records": {}, "figures": {}, "heads": {}}
    banked = json.loads(BASELINE.read_text(encoding="utf-8"))
    return {k: banked.get(k, {}) for k in ("records", "figures", "heads")}


def evaluate(state: dict, bank: dict) -> list[str]:
    problems: list[str] = []

    # 1 — the manifest's vocabularies against the readers' dispatch tables.
    problems.extend(state["vocabulary_faults"])

    # 2 — the two cohorts are disjoint, and every role is a published one.
    for role in state["overlap"]:
        problems.append(f"role '{role}' is in both readers' cohorts — a record with it "
                        f"is drawn twice, and every count in this gate is wrong before "
                        f"the town is")
    published = set(state["vocabulary"]["roles"])
    for role in state["roles_seen"]:
        if role not in published:
            problems.append(f"a species record carries role '{role}', which the manifest "
                            f"does not publish — it is routed to nothing by a rule this "
                            f"gate cannot see")

    # 3 — the records that reach no reader, exact in both directions.
    for key in sorted(set(state["unrouted"]) - set(bank["records"])):
        u = state["unrouted"][key]
        problems.append(
            f"{key} ({u['role']}/{u['form']}) reaches no reader — {UNROUTED_REASONS[u['reason']]} "
            f"— and is not in {BASELINE.name}. Route it, or bank it with --update in this "
            f"commit and say in the message why a researched record is drawn nowhere")
    for key in sorted(set(bank["records"]) - set(state["unrouted"])):
        problems.append(
            f"{key} is banked as reaching no reader and now reaches one, or has left the "
            f"data. Re-run with --update in the commit that did it: the bank has to "
            f"record the repair rather than keep its ghost")
    for key in sorted(set(state["unrouted"]) & set(bank["records"])):
        if state["unrouted"][key]["reason"] != bank["records"][key].get("reason"):
            problems.append(
                f"{key} reaches no reader for a different reason than the one banked "
                f"({bank['records'][key].get('reason')} -> "
                f"{state['unrouted'][key]['reason']}) — the fault moved rather than "
                f"being fixed")

    # 4 — the figures a read reaches only part of, exact in both directions.
    for path in sorted(set(state["figures"]) - set(bank["figures"])):
        f = state["figures"][path]
        problems.append(
            f"{path} is declared a read and reaches only {f['reached']} of its "
            f"{f['carriers']} carrier(s) — {', '.join(f['readers']) or 'no file'} reads "
            f"it and the rest of the records go to another reader. Bank it with --update, "
            f"because a read-set that calls this figure read is telling the truth about "
            f"a file and not about the town")
    for path in sorted(set(bank["figures"]) - set(state["figures"])):
        problems.append(
            f"{path} is banked as partly reached and now reaches every record that "
            f"carries it, or has left K42's map. Re-run with --update in the commit "
            f"that did it")
    for path in sorted(set(state["figures"]) & set(bank["figures"])):
        now, was = state["figures"][path], bank["figures"][path]
        if (now["carriers"], now["reached"]) != (was.get("carriers"), was.get("reached")):
            problems.append(
                f"{path} reaches {now['reached']} of {now['carriers']} carrier(s), and "
                f"{BASELINE.name} banks {was.get('reached')} of {was.get('carriers')}. "
                f"The population moved: --update in the commit that moved it")

    # 5 — the recorded flowers that draw no head, exact in both directions.
    for key in sorted(set(state["heads"]) - set(bank["heads"])):
        h = state["heads"][key]
        problems.append(
            f"{key} records a July inflorescence and no head is drawn — "
            f"{NO_HEAD_REASONS[h['reason']]}. Bank it with --update, or draw it")
    for key in sorted(set(bank["heads"]) - set(state["heads"])):
        problems.append(
            f"{key} is banked as a recorded flower that draws no head and now draws one, "
            f"or has left the data. --update in the commit that did it")
    for key in sorted(set(state["heads"]) & set(bank["heads"])):
        if state["heads"][key]["reason"] != bank["heads"][key].get("reason"):
            problems.append(
                f"{key} draws no head for a different reason than the one banked "
                f"({bank['heads'][key].get('reason')} -> {state['heads'][key]['reason']})")

    if not state["records"]:
        problems.append("no flora species records were routed, so nothing was measured "
                        "and a pass here means nothing")
    return problems


def measure() -> tuple[dict, list[str]]:
    state = classify()
    return state, evaluate(state, read_bank())


def print_census(c: dict) -> None:
    print("Which RECORDS a read reaches — ROADMAP K44.\n")
    print(f"  {c['records']} species record(s) across {len(c['vocabulary']['roles'])} "
          f"published role(s):")
    for name in (FLORA_JS, TREES_JS):
        coh = c["cohorts"][name]
        print(f"    {name:<10} {c['by_reader'][name]:>4} record(s)  "
              f"roles {len(coh['roles'])}, forms {len(coh['forms'])}, "
              f"zones {len(coh['zones'])}")
    print(f"    {'none':<10} {c['by_reader']['none']:>4} record(s)")
    print(f"\n  {c['pairs'] - c['reached_pairs']} of {c['pairs']} (record, figure) pair(s) "
          f"that K42's map calls read reach nothing, across "
          f"{len(c['figures'])} of {c['figure_count']} declared-read figure(s):")
    for path in sorted(c["figures"], key=lambda p: -c["figures"][p]["unreached"]):
        f = c["figures"][path]
        print(f"    {path:<46} {f['reached']:>4} of {f['carriers']:>4} reached  "
              f"[{', '.join(f['readers']) or 'nothing'}]")
    print(f"\n  {len(c['unrouted'])} record(s) reach no reader at all:")
    for key in sorted(c["unrouted"]):
        u = c["unrouted"][key]
        print(f"    {key:<46} {u['role']}/{u['form']}  {u['reason']}")
    print(f"\n  {len(c['heads'])} recorded July inflorescence(s) draw no head:")
    for key in sorted(c["heads"]):
        h = c["heads"][key]
        print(f"    {key:<46} {h['shape']}/{h['phenology']}  {h['reason']}")
    print("\n  Routing only: a record this census calls reached is one its reader "
          "receives.\n  Whether its zone has modelled ground under it is a different "
          "question (K42 4b).")


def self_test() -> int:
    """Break each assertion in memory, against the real tree."""
    state = classify()
    bank = read_bank()
    if not state["records"] or not bank["records"]:
        print("SELF-TEST FAIL: nothing measured, so no assertion can be exercised")
        return 1
    clean = evaluate(state, bank)
    cases: list[tuple[str, dict, dict]] = []

    s1 = copy.deepcopy(state)
    s1["vocabulary_faults"].append("a published form no reader draws")
    cases.append(("1 a published form with no archetype", s1, bank))

    s2 = copy.deepcopy(state)
    s2["overlap"] = ["shrub_low"]
    cases.append(("2 a role both readers claim", s2, bank))

    s2b = copy.deepcopy(state)
    s2b["roles_seen"] = [*state["roles_seen"], "liana"]
    cases.append(("2 a record whose role the manifest does not publish", s2b, bank))

    s3 = copy.deepcopy(state)
    s3["unrouted"]["z02_mesic_prairie/invented_sp"] = {
        "role": "tree", "form": "tree_gallery", "reason": "zone-not-read"}
    cases.append(("3 a new record that reaches no reader", s3, bank))

    b3 = copy.deepcopy(bank)
    b3["records"]["z01_wet_prairie/a_record_that_left"] = {"reason": "zone-not-read"}
    cases.append(("3 a banked unrouted record that has left the data", state, b3))

    b3r = copy.deepcopy(bank)
    first = sorted(state["unrouted"])[0]
    b3r["records"][first] = {**b3r["records"][first], "reason": "role-unrouted"}
    cases.append(("3 a banked record whose reason moved", state, b3r))

    s4 = copy.deepcopy(state)
    s4["figures"]["species[].substrate"] = {
        "carriers": 154, "reached": 3, "unreached": 151, "readers": [FLORA_JS],
        "state": "mesh"}
    cases.append(("4 a read that newly reaches only part of its records", s4, bank))

    b4 = copy.deepcopy(bank)
    b4["figures"]["species[].gone"] = {"carriers": 1, "reached": 0}
    cases.append(("4 a banked partial read that has left the map", state, b4))

    b4c = copy.deepcopy(bank)
    path = sorted(state["figures"])[0]
    b4c["figures"][path] = {**b4c["figures"][path], "reached": 0}
    cases.append(("4 a banked partial read whose counts moved", state, b4c))

    s5 = copy.deepcopy(state)
    s5["heads"]["z01_wet_prairie/invented_sp"] = {
        "shape": "spike", "phenology": "flowering", "reason": "shape-no-archetype"}
    cases.append(("5 a new recorded flower that draws no head", s5, bank))

    b5 = copy.deepcopy(bank)
    b5["heads"]["z01_wet_prairie/a_flower_that_left"] = {"reason": "july-gate"}
    cases.append(("5 a banked headless flower that has left the data", state, b5))

    s6 = copy.deepcopy(state)
    s6["records"] = 0
    cases.append(("the empty measurement, which must not pass", s6, bank))

    ok = True
    for label, s, b in cases:
        fired = len(evaluate(s, b)) > len(clean)
        print(f"  {'fires' if fired else 'SILENT'}  {label}")
        ok = ok and fired

    # The scanners are the load-bearing half of assertion 1: each must be able to
    # say yes AND no, because a scanner that silently returns nothing routes the
    # whole town to `none` and banks it.
    coh = cohorts()
    trees_src = coh["sources"][TREES_JS]
    checks = [
        ("the Set scanner finds a cohort that is there",
         "matrix" in coh[FLORA_JS]["roles"]),
        ("the Set scanner refuses a cohort that is not",
         raises(lambda: js_set(trees_src, "OUR_ROLES", TREES_JS))),
        ("the array scanner finds the zone list",
         "z05_riverbank_timber" in coh[TREES_JS]["zones"]),
        ("the array scanner refuses a list that is not there",
         raises(lambda: js_array(trees_src, "PRAIRIE_ZONES", TREES_JS))),
        ("the object scanner finds a dispatch table",
         "tree_gallery" in coh[TREES_JS]["forms"]),
        ("the object scanner refuses a table that is not there",
         raises(lambda: js_object_keys(trees_src, "FORM_OF_NOTHING", TREES_JS))),
        ("the role guard is read off the source",
         coh[TREES_JS]["roles"] == {"tree", "thicket"}),
        ("the head archetype table is not empty",
         len(coh[FLORA_JS]["shapes"]) > 0),
        # K45(c). Both readers draw heads now, and both facts are scanned. The
        # three cases below are the ones that matter: the scan is not a constant
        # (it went False for `trees.js` for as long as that file had no head
        # path, and this gate said so); a table with nothing drawing from it
        # RAISES rather than reporting every flower on that cohort as drawn; and
        # so does an emitter with no table.
        ("both readers are scanned as drawing heads",
         coh[FLORA_JS]["draws_heads"] and coh[TREES_JS]["draws_heads"]),
        ("a reader with no head path at all scans False",
         js_draws_heads("const FORM_OF = { a: 1 };", "synthetic.js") is False),
        ("a head table with no emitter is refused",
         raises(lambda: js_draws_heads("const HEAD_OF_SHAPE = {\n  spike: 1,\n};",
                                       "synthetic.js"))),
        ("an emitter with no head table is refused",
         raises(lambda: js_draws_heads("addHead(buf, 1, 2, 3);", "synthetic.js"))),
        ("the woody head table is read off trees.js",
         "cluster_terminal" in coh[TREES_JS]["shapes"]),
        ("a routed record goes to the reader whose cohort holds it",
         route("z01_wet_prairie", {"role": "matrix", "form": "sedge_tussock"}, coh)
         == (FLORA_JS, None)),
        # The example moved 2026-08-17 and the move is the point: this case named
        # `z08_lakeshore`, and ROADMAP K45(b) change one put that zone into
        # `TIMBER_ZONES` and its three poplars into the scene, so the case was
        # asserting the repository's state rather than the mechanism. It is asked
        # of `z09_sand_prairie`, which no reader's zone list holds — and if that
        # zone is ever routed too, this case moves again rather than being
        # deleted, because a routing gate needs a zone outside the list to test.
        ("a woody record outside TIMBER_ZONES reaches nothing",
         route("z09_sand_prairie", {"role": "tree", "form": "tree_columnar"}, coh)
         == (None, "zone-not-read")),
        ("an unimplemented form reaches nothing",
         route("z05_riverbank_timber", {"role": "thicket", "form": "vine_drape"}, coh)
         == (None, "form-not-implemented")),
        ("a role in no cohort reaches nothing",
         route("z01_wet_prairie", {"role": "liana", "form": "vine_drape"}, coh)
         == (None, "role-unrouted")),
        ("the two-scan figure reader sees the leaf both files read",
         {FLORA_JS, TREES_JS} <= figure_readers(coh["sources"])["species[].height_m"]
         ["readers"]),
        # This case used to assert that `inflorescence.rgb`'s readers are
        # EXACTLY {flora.js} — which tested the tree as it stood rather than the
        # mechanism, and went red the moment K45(c) gave `trees.js` a head path
        # that reads the same field. What it exists to prove is the property:
        # `flora.js` reads that field off a local named `inflor`, `rgb` is an
        # ambiguous leaf scanned parent-qualified, so the LEAF scan alone cannot
        # see the read and only the declared expression can.
        ("…and the renamed local only the declaration can prove",
         FLORA_JS in figure_readers(coh["sources"])
         ["species[].july.inflorescence.rgb"]["readers"]
         and not k42.reads_leaf(coh["sources"][FLORA_JS],
                                "species[].july.inflorescence.rgb")),
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
            "_doc": "Where a read stops, by RECORD rather than by field. K42's read-set "
                    "says a figure is read if any renderer source reads it; every reader "
                    "here takes a cohort, so a read figure still reaches nothing on the "
                    "records its reader never receives. `records` are the species records "
                    "no reader receives at all, `figures` are the declared reads that "
                    "reach only part of their carriers, and `heads` are the recorded July "
                    "inflorescences that draw no flower. Routing only: a reached record "
                    "is one its reader receives, not one a visitor is standing in front "
                    "of. Held exact in both directions by tools/measure_flora_reach.py. "
                    "Read ROADMAP K44 before adding a line.",
            "records": {k: state["unrouted"][k] for k in sorted(state["unrouted"])},
            "figures": {k: state["figures"][k] for k in sorted(state["figures"])},
            "heads": {k: state["heads"][k] for k in sorted(state["heads"])},
        }, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {BASELINE.relative_to(ROOT)} ({len(state['unrouted'])} record(s), "
              f"{len(state['figures'])} figure(s), {len(state['heads'])} head(s))")
        return 0

    if not args.gate and not args.quiet:
        print_census(state)

    for p in problems:
        print(f"FAIL  {p}", file=sys.stderr)
    if problems:
        return 1

    if args.gate or args.quiet:
        print(f"flora reach: {state['pairs'] - state['reached_pairs']} of "
              f"{state['pairs']} (record, figure) pair(s) K42 calls read reach nothing, "
              f"{len(state['unrouted'])} record(s) reach no reader at all and "
              f"{len(state['heads'])} recorded flower(s) draw no head; all three "
              f"populations are banked and none may grow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
