#!/usr/bin/env python3
"""Compile Guide › About this destination: four cards per destination, every number computed (T-2667).

    python3 tools/compile_about_destination.py --check       compute, render and gate; write nothing
    python3 tools/compile_about_destination.py --print       ...and print each destination's cards
    python3 tools/compile_about_destination.py --build       gate, then write data/guide/about/<scene>.json
    python3 tools/compile_about_destination.py --self-test   plant each fault and require it refused

Design doc "Field Navigator Mk II", section 12 and NAV-1002: the Evidence hub's topics
(renderers/web/js/evidence.js TOPICS) fold into four cards: How we grade, Sources, Liberties,
and What lived and grew here. The order book goes behind Researcher mode (owner ruling
2026-10-16). The copy is authored in data/guide/about_destination.json. EVERY NUMBER IN IT IS
COMPUTED HERE from the repository: a {placeholder} names a figure in `figures()` below, and the
gate refuses a digit typed into the copy. So the cards cannot drift from the data they
describe, which is the failure the hub's hand-typed glosses had ("ten habitats").

It refuses:
  - a topic in evidence.js's TOPICS with no card or Researcher home, or a mapped topic that
    no longer exists;
  - a card missing for a destination: all four in 1835 and 1904 (the ticket's acceptance),
    and every card that has copy for 1812;
  - a digit in the copy, a {placeholder} that is not a figure, or a figure this destination
    cannot compute;
  - a `holds` claim the data does not hold ("none is Reconstructed" needs reconstructed = 0);
  - a card body over 60 words, a sentence over 20, a lower-case grade word, a retired term
    (documented, conjectural, Evidence, Citations), an internal term (order book, ticket,
    commit gate, tier, quota, bucket), and anything compile_summaries' lint refuses;
  - a `rests_on` path that does not exist.
Reading grade is held by tools/check_reading_level.py, which reads data/guide/ (T-2669).

--build writes data/guide/about/<scene>.json, the rendered cards. That directory is generated
and not committed (.gitignore), like data/inspect/: the figures move whenever another ticket
adds a building or a source. Wiring it into publish.sh is the T-2667 PR's, with its UI.
"""

import argparse
import copy
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from compile_summaries import lint_string, words  # noqa: E402
from check_reading_level import split_sentences  # noqa: E402

DATA = ROOT / "data"
COPY = DATA / "guide" / "about_destination.json"
OUT = DATA / "guide" / "about"
EVIDENCE_JS = ROOT / "renderers" / "web" / "js" / "evidence.js"
CARDS = ["how_we_grade", "sources", "liberties", "lived_and_grew"]
REQUIRED_EVERY_CARD = ["1835", "1904"]
MAX_BODY_WORDS, MAX_SENTENCE_WORDS = 60, 20
RETIRED = ["documented", "conjectural", "Evidence", "Citations"]
INTERNAL = ["order book", "ticket", "commit gate", "commit-gate", "tier", "quota", "bucket"]
PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def structures(root, scene):
    out = []
    for p in sorted((root / "data" / "sidecars" / scene).glob("*.json")):
        try:
            j = load(p)
        except ValueError:
            continue
        if isinstance(j, dict) and "placement" in j and j.get("id"):
            out.append(j)
    return out


def figures(root, scene):
    """Every number a card may print for this destination, computed from the tree."""
    root = Path(root)
    f = {"year": scene}
    recs = structures(root, scene)
    ids = {r["id"] for r in recs}
    f["buildings"] = len(recs)
    for g in ("attested", "inferred", "reconstructed"):
        f[g] = sum(1 for r in recs if (r.get("grade") or {}).get("value") == g)
    terrain = root / "data" / "sidecars" / scene / "terrain.json"
    if terrain.is_file():
        claims = load(terrain).get("claims") or []
        f["ground_claims"] = len(claims if isinstance(claims, list) else list(claims.values()))
    f["sources_all"] = len(list((root / "data" / "sources").glob("*.json")))
    sdir = root / "data" / "sidecars" / scene / "sources"
    if (sdir / "uses.json").is_file():
        f["sources_here"] = sum(1 for v in load(sdir / "uses.json")["uses"].values() if v == "scene")
    elif (sdir / "index.json").is_file():
        f["sources_here"] = sum(1 for s in load(sdir / "index.json")["sources"] if s.get("use") == "scene")
    lib = root / "data" / "liberties.json"
    if lib.is_file():
        def names_one(l):
            subj = {x for x in l.get("subjects") or [] if isinstance(x, str)}
            cov = {c.get("structure") for c in l.get("covers") or [] if isinstance(c, dict)}
            return bool((subj | cov) & ids)
        f["liberties_here"] = sum(1 for l in load(lib)["liberties"]
                                  if l.get("section") != "resolved" and names_one(l))
    exc = root / "data" / "sidecars" / scene / "exclusions.json"
    if exc.is_file():
        e = load(exc)
        f["left_out"], f["doubts"] = len(e.get("excluded") or []), len(e.get("uncertain") or [])
    layers = load(root / "data" / "scenes" / f"{scene}.json").get("layers") or []
    fauna = root / "data" / "fauna" / "index.json"
    if "fauna" in layers and fauna.is_file():
        zones = load(fauna)["zones"]
        f["habitats"] = len(zones)
        species = set()
        for z in zones:
            for a in load(fauna.parent / z["file"]).get("species") or []:
                species.add(a.get("id"))
        f["animal_species"] = len(species)
    flora = root / "data" / "flora" / "index.json"
    if "flora" in layers and flora.is_file():
        fl = load(flora)
        f["plant_communities"] = sum(1 for z in fl["zones"] if z.get("plantable_in_scene"))
        f["plantings_here"] = sum(1 for p in fl["plantings"] if scene in (p.get("scenes") or []))
    trees = root / "data" / "street_trees" / f"{scene}.json"
    if "street_trees" in layers and trees.is_file():
        t = load(trees)
        f["trees"] = len(t["trees"])
        f["tree_species"] = len(t["species"])
    people = root / "data" / "sidecars" / scene / "people.json"
    if people.is_file():
        rows = load(people).get("people") or []
        f["people_listed"] = len(rows)
        if len(rows) <= 3:
            names = [r["name"] for r in sorted(rows, key=lambda r: (r.get("relationship") != "head", r["name"]))]
            f["people_names"] = (" and ".join(names) if len(names) <= 2
                                 else ", ".join(names[:-1]) + " and " + names[-1])
    return f


def evidence_topics(root):
    text = (Path(root) / "renderers" / "web" / "js" / "evidence.js").read_text(encoding="utf-8")
    block = text[text.index("const TOPICS = ["):]
    block = block[:block.index("\n];")]
    return re.findall(r"^\s*id: '([a-z]+)'", block, re.M)


def voice(where, text):
    errs = []
    for s in split_sentences(text):
        if len(words(s)) > MAX_SENTENCE_WORDS:
            errs.append(f"{where}: a sentence of {len(words(s))} words, over the limit of {MAX_SENTENCE_WORDS}")
    for term in ("attested", "inferred", "reconstructed"):
        if re.search(rf"\b{term}\b", text):
            errs.append(f"{where}: `{term}` in lower case; the locked term is `{term.capitalize()}`")
    for term in RETIRED:
        if re.search(rf"\b{term}\b", text, re.IGNORECASE if term.islower() else 0):
            errs.append(f"{where}: the retired term `{term}`")
    for term in INTERNAL:
        if re.search(rf"\b{re.escape(term)}s?\b", text, re.IGNORECASE):
            errs.append(f"{where}: the internal term `{term}`, which stays behind Researcher mode")
    errs += [f"{where}: {w} in a string a visitor reads" for w in lint_string(text)]
    return errs


def render(doc, root):
    """({scene: [card, ...]}, [refusals])."""
    errs, out = [], {}
    root = Path(root)
    scenes = sorted(p.stem for p in (root / "data" / "scenes").glob("*.json"))
    topics = evidence_topics(root)
    mapped = doc.get("topic_map") or {}
    for t in topics:
        if t not in mapped:
            errs.append(f"topic_map: the hub topic `{t}` has no card or Researcher home")
    for t, card in mapped.items():
        if t not in topics:
            errs.append(f"topic_map: `{t}` is not a topic in evidence.js")
        if card not in CARDS + ["researcher"]:
            errs.append(f"topic_map: `{t}` maps to `{card}`, which is not a card")
    for t in (doc.get("researcher") or {}).get("topics") or []:
        if mapped.get(t) != "researcher":
            errs.append(f"researcher: `{t}` is listed but not mapped to Researcher mode")
    cards = {c.get("id"): c for c in doc.get("cards") or []}
    if list(cards) != CARDS:
        errs.append(f"cards: {list(cards)}, and must be exactly {CARDS}, in that order")
    for cid, c in cards.items():
        for p in c.get("rests_on") or []:
            if not (root / p).exists():
                errs.append(f"{cid}: rests on `{p}`, which does not exist")
        if not c.get("rests_on"):
            errs.append(f"{cid}: no `rests_on`")
        errs += voice(f"{cid}.title", c.get("title") or "")
    for scene in scenes:
        fig = figures(root, scene)
        rendered = []
        for cid in CARDS:
            c = cards.get(cid) or {}
            sc = (c.get("scenes") or {}).get(scene)
            if sc is None:
                if scene in REQUIRED_EVERY_CARD:
                    errs.append(f"{cid}: no copy for {scene}, which must show all four cards")
                continue
            body = sc.get("body") or ""
            where = f"{cid}[{scene}]"
            stripped = PLACEHOLDER.sub("", body)
            if re.search(r"\d", stripped):
                errs.append(f"{where}: a digit typed into the copy; every number must be a computed figure")
            for name in PLACEHOLDER.findall(body):
                if name not in fig:
                    errs.append(f"{where}: `{{{name}}}` is not a figure this destination computes")
            for name, want in (sc.get("holds") or {}).items():
                if fig.get(name) != want:
                    errs.append(f"{where}: holds {name} = {want!r}, and the data has {fig.get(name)!r}")
            def shown(m):
                v = fig.get(m.group(1), m.group(0))
                return f"{v:,}" if isinstance(v, int) else str(v)
            text = PLACEHOLDER.sub(shown, body)
            if len(words(text)) > MAX_BODY_WORDS:
                errs.append(f"{where}: {len(words(text))} words, over the limit of {MAX_BODY_WORDS}")
            errs += voice(where, text)
            rendered.append({"id": cid, "title": c.get("title"), "body": text,
                             "topics": sorted(t for t, k in mapped.items() if k == cid)})
        out[scene] = rendered
    return out, errs


def run(mode, root=ROOT):
    doc = load(Path(root) / "data" / "guide" / "about_destination.json")
    out, errs = render(doc, root)
    for e in errs:
        print(f"FAIL: {e}")
    if errs:
        print(f"FAIL: {len(errs)} problem(s) in About this destination")
        return 1
    if mode == "print":
        for scene, cards in out.items():
            print(f"== {scene}")
            for c in cards:
                print(f"  {c['title']}: {c['body']}")
    if mode == "build":
        OUT.mkdir(parents=True, exist_ok=True)
        for scene, cards in out.items():
            (OUT / f"{scene}.json").write_text(json.dumps(
                {"scene": scene, "standard": "GENERATED by tools/compile_about_destination.py "
                 "from data/guide/about_destination.json; every number computed from the tree.",
                 "cards": cards, "researcher": doc.get("researcher")},
                indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n = sum(len(c) for c in out.values())
    print(f"OK: {n} cards over {len(out)} destinations, every number computed, every topic housed")
    return 0


def self_test():
    doc = load(COPY)
    fails = 0

    def expect(label, mutate, needle):
        nonlocal fails
        d = copy.deepcopy(doc)
        mutate(d)
        _, errs = render(d, ROOT)
        hit = any(needle in e for e in errs) if needle else not errs
        print(f"  {'ok  ' if hit else 'FAIL'} {label}" + ("" if hit else f": {errs[:3]}"))
        fails += 0 if hit else 1

    card = lambda d, cid: next(c for c in d["cards"] if c["id"] == cid)  # noqa: E731
    expect("the committed copy passes", lambda d: None, None)
    expect("a hub topic with no home", lambda d: d["topic_map"].pop("fauna"), "has no card or Researcher home")
    expect("a mapped topic that does not exist", lambda d: d["topic_map"].update(weather="lived_and_grew"), "not a topic in evidence.js")
    expect("a typed number", lambda d: card(d, "sources")["scenes"]["1835"].update(body="We cite 226 sources."), "a digit typed")
    expect("an unknown figure", lambda d: card(d, "sources")["scenes"]["1835"].update(body="We cite {sources_everywhere} sources."), "not a figure")
    expect("a figure the destination cannot compute",
           lambda d: card(d, "lived_and_grew")["scenes"]["1904"].update(body="We found {habitats} habitats."), "not a figure this destination")
    expect("a false `holds`", lambda d: card(d, "how_we_grade")["scenes"]["1835"].update(holds={"reconstructed": 0}), "holds reconstructed")
    expect("a card missing in 1904", lambda d: card(d, "liberties")["scenes"].pop("1904"), "must show all four cards")
    expect("an internal term", lambda d: card(d, "liberties")["scenes"]["1835"].update(body="See the order book."), "internal term")
    expect("a retired term", lambda d: card(d, "sources")["scenes"]["1835"].update(body="The Evidence for {year}."), "retired term")
    expect("a lower-case grade word", lambda d: card(d, "how_we_grade")["scenes"]["1835"].update(body="Most are reconstructed."), "lower case")
    expect("a snake_case id", lambda d: card(d, "sources")["scenes"]["1835"].update(body="Open sources_index now."), "snake_case")
    expect("a body over sixty words", lambda d: card(d, "sources")["scenes"]["1835"].update(body=("Each one is named. " * 16).strip()), "over the limit of 60")
    expect("a claim resting on nothing", lambda d: card(d, "sources").update(rests_on=["data/no_such_dir"]), "does not exist")
    with tempfile.TemporaryDirectory():
        pass
    print(f"compile_about_destination self-test: {'FAIL' if fails else 'OK'} "
          f"({fails} assertion(s) did not fire as required)")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    m = ap.add_mutually_exclusive_group(required=True)
    for flag in ("--check", "--print", "--build", "--self-test"):
        m.add_argument(flag, action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return run("print" if a.print else "build" if a.build else "check")


if __name__ == "__main__":
    sys.exit(main())
