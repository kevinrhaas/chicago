#!/usr/bin/env python3
"""Compile the Inspect Photos tab: each 1904 building's pictures by date, the 12 best first (T-2645).

    python3 tools/compile_photos.py --check       derive, rank and gate in memory; write nothing
    python3 tools/compile_photos.py --print ID    ...and print one building's tab
    python3 tools/compile_photos.py --build       gate, then write data/photos/<scene>.json
    python3 tools/compile_photos.py --self-test   plant each fault and require it refused by name

Design doc "Field Navigator Mk II" section 08 "Photos": a grid sorted by date, each picture
with its year, a caption and a "from this spot" button; the 12 best first and the rest behind
"All N". It builds on the card's Images tab (T-2389): the pictures and their credits are
tools/compile_pictures.py's own `derive()`, run over the same tree, so the two tabs cannot
disagree about which pictures belong to a building or how they are credited.

WHAT IS SHOWN (AGENTS.md hard rule 6). A picture is shown only when its rights allow display
(`public domain` or `no known restrictions` in the library; `public_domain`,
`no_known_restrictions` or `cleared` for a data/sources record) AND the image store holds a
copy to show. Everything else (copyright, unknown, permission pending, check required, or not
held) is listed under `links`: its credit and its holder's link, never its pixels.

WHAT EACH PHOTO CARRIES.
  - `year`: the library's `date_earliest`/`date_latest` (a source record's first four-digit
    year); `year_text` says "in 1888", "about 1888" (a range of up to 4 years, its middle),
    "between 1885 and 1900", or "undated".
  - `caption`: at most 12 words, TEMPLATED from the record's view and kind ("The front,
    photographed in 1888."), never cut from its archival title, which is a catalogue line
    ("1. Historic American Buildings Survey Harold Allen, Photographer, June 1965 VIEW: ...").
    Held to compile_summaries' lint and to T-2669's sentence limit, and every building's
    captions pooled to Flesch-Kincaid grade 9 or lower.
  - `credit`: creator, holder and date, as compile_pictures gives them.
  - `camera`: the solved camera in data/reference_views/<structure_id>/<view>.json whose
    `library_image` or `source_id` is this picture, for "from this spot"; absent otherwise,
    and the button is hidden.

THE 12 BEST, AND THE RULE. Among the shown pictures only, each is keyed, in this order:
    1. has a solved camera (so "from this spot" works), before one without;
    2. its period: in-period, then near-period, then later (the library's own reading);
    3. its year's distance from the scene year (1904), nearest first; undated last;
    4. its kind: photographs, then prints and plates, then drawings;
    5. its id, so the order is stable.
  Then VIEWPOINTS IN TURN: the pictures are grouped by view (front, oblique front, side, rear,
  entrance, courtyard, street, interior ...), the views ordered by their best picture, and the
  twelve taken round-robin: each view's best, then each view's second best, and so on. So a
  building photographed from one corner forty times still shows its other sides in the twelve,
  no one view takes more than its turn, and within a view the solved, in-period picture
  nearest 1904 comes first. `best` is those up to 12 by date;
  `all` is every shown picture by date, and `count` is its N.

GENERATED, NOT COMMITTED. data/photos/ is git-ignored and written by --build, like
data/pictures/: the image library is edited by other tickets all the time. Wiring --build into
publish.sh is the T-2645 PR's, with the tab that reads it.
"""

import argparse
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import compile_pictures as cp  # noqa: E402
from compile_summaries import lint_string, words  # noqa: E402
from check_reading_level import MAX_GRADE, MAX_SENTENCE_WORDS, pooled, score, split_sentences  # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "photos"
SCENE = "1904"
BEST = 12
MAX_CAPTION_WORDS = 12
SHOWN_LIBRARY = {"public domain", "no known restrictions"}
SHOWN_SOURCE = {"public domain", "no known restrictions", "cleared"}

SUBJECT = {
    "front elevation": "The front", "oblique front": "The front from the corner",
    "side elevation": "A side wall", "rear": "The back", "entrance detail": "The entrance",
    "detail": "A close look", "roof detail": "The roof", "courtyard": "The courtyard",
    "courtyard detail": "A corner of the courtyard", "street view": "The house on its street",
    "aerial": "The house from above", "plan": "A floor plan", "section": "A drawing through the house",
    "interior": "Inside the house",
}
NOUN = {
    "PHOTO": "a photo", "STEREO": "a stereo photo", "POSTCARD": "a postcard",
    "AERIAL": "a photo from the air", "ENGRAVING": "an engraving", "LITHO": "a print",
    "PLATE": "a print", "ILLUSTRATION": "a drawing", "DRAWING": "an architect's drawing",
    "MEASURED DWG": "a measured drawing", "BIRD'S-EYE": "a bird's-eye view",
    "NEWSPAPER": "a newspaper picture", "PICTURE": "a picture",
}
KIND_ORDER = {"PHOTO": 0, "STEREO": 0, "POSTCARD": 0, "AERIAL": 0, "DRAWING": 2, "MEASURED DWG": 2}
PERIOD_ORDER = {"in-period": 0, "near-period": 1, "later": 2}


def years(entry, lib, src):
    """(earliest, latest) years or (None, None)."""
    r = lib.get(entry["id"])
    if r is not None:
        lo, hi = r.get("date_earliest"), r.get("date_latest")
        lo = lo if isinstance(lo, int) else hi if isinstance(hi, int) else None
        hi = hi if isinstance(hi, int) else lo
        return lo, hi
    d = src.get(entry["id"]) or {}
    m = re.search(r"\b(1[6-9]\d\d|20\d\d)\b", str(d.get("date") or ""))
    return (int(m.group(1)), int(m.group(1))) if m else (None, None)


def year_text(lo, hi):
    if lo is None:
        return None, "with no date"
    if lo == hi:
        return lo, f"from {lo}"
    if hi - lo <= 4:
        mid = (lo + hi) // 2
        return mid, f"from about {mid}"
    return lo, f"from {lo} to {hi}"


def caption(entry, subject_of, ytext):
    subject = subject_of or SUBJECT.get(entry.get("view") or "", "The house")
    noun = NOUN.get(entry.get("kind"), "a picture")
    return f"{subject}, {noun} {ytext}."


def shown(entry, src):
    rights = (entry.get("rights") or "").strip().lower()
    if entry.get("library"):
        return rights in SHOWN_LIBRARY and bool(entry.get("held"))
    # A data/sources record is listed by compile_pictures with no store copy of its own.
    d = src.get(entry["id"]) or {}
    return (d.get("rights_status") or "").replace("_", " ") in SHOWN_SOURCE and bool(entry.get("held"))


def cameras_for(views, sid):
    out = {}
    for cam in views.get(sid, []):
        for key in (cam.get("library_image"), cam.get("source_id")):
            if key and key not in out:
                out[key] = {"view": cam.get("_view"), "eye": cam.get("eye"), "yaw_deg": cam.get("yaw_deg"),
                            "basis_right_up_forward": cam.get("basis_right_up_forward"),
                            "focal_px": cam.get("focal_px"), "image_px": cam.get("image_px")}
    return out


def accessory_subject(sid):
    _, acc = cp.structure_place(sid)
    return {"coach_house": "The coach house", "conservatory": "The glass house",
            "rear_building": "The rear building", "alley_building": "The alley building"}.get(acc)


def rank_key(p):
    return (0 if p.get("camera") else 1, PERIOD_ORDER.get(p.get("period"), 1),
            abs(p["year"] - int(SCENE)) if isinstance(p.get("year"), int) else 999,
            KIND_ORDER.get(p.get("kind"), 1), p["id"])


def choose_best(photos):
    """Round-robin over viewpoints in rank order: each view's best, then each view's second, ..."""
    order = sorted(photos, key=rank_key)
    queues, view_order = {}, []
    for p in order:
        v = p.get("view") or "unstated"
        if v not in queues:
            queues[v] = []
            view_order.append(v)
        queues[v].append(p)
    picked = []
    while len(picked) < BEST and any(queues.values()):
        for v in view_order:
            if queues[v] and len(picked) < BEST:
                picked.append(queues[v].pop(0))
    return picked


def by_date(p):
    return (p["year"] if isinstance(p.get("year"), int) else 9999, p["id"])


def build_tab(sid, entries, lib, src, views):
    cams = cameras_for(views, sid)
    subj = accessory_subject(sid)
    photos, links = [], []
    for e in entries:
        lo, hi = years(e, lib, src)
        y, ytext = year_text(lo, hi)
        credit = {k: e[k] for k in ("creator", "holder", "date", "url", "rights") if e.get(k)}
        if not shown(e, src):
            links.append({"id": e["id"], "kind": e.get("kind"), "year": y, "credit": credit})
            continue
        p = {"id": e["id"], "kind": e.get("kind"), "view": e.get("view"), "period": e.get("period"),
             "year": y, "year_text": ytext, "caption": caption(e, subj, ytext), "credit": credit,
             "held": e["held"]}
        if e["id"] in cams:
            p["camera"] = cams[e["id"]]
        photos.append(p)
    best = choose_best(photos)
    best_ids = {p["id"] for p in best}
    for p in photos:
        p["best"] = p["id"] in best_ids
    return {"structure": sid, "count": len(photos), "best": [p["id"] for p in sorted(best, key=by_date)],
            "all": sorted(photos, key=by_date), "links": sorted(links, key=by_date)}


def gate_tab(tab):
    errs = []
    sid = tab["structure"]
    scores = []
    for p in tab["all"]:
        at = f"{sid} {p['id']}"
        c = p["caption"]
        if len(words(c)) > MAX_CAPTION_WORDS:
            errs.append(f"{at}: caption of {len(words(c))} words, over the limit of {MAX_CAPTION_WORDS}")
        for s in split_sentences(c):
            if len(words(s)) > MAX_SENTENCE_WORDS:
                errs.append(f"{at}: a caption sentence over {MAX_SENTENCE_WORDS} words")
        errs += [f"{at}: caption carries {w}" for w in lint_string(c)]
        if not p.get("credit", {}).get("holder") and not p.get("credit", {}).get("creator"):
            errs.append(f"{at}: shown with no credit (no creator and no holder)")
        if (p.get("credit", {}).get("rights") or "").lower() not in SHOWN_LIBRARY | SHOWN_SOURCE:
            errs.append(f"{at}: shown, and its rights `{p.get('credit', {}).get('rights')}` do not allow display (hard rule 6)")
        cam = p.get("camera")
        if cam is not None and not (isinstance(cam.get("eye"), list) and len(cam["eye"]) == 3):
            errs.append(f"{at}: a camera with no eye")
        scores.append(score(c))
    if scores and pooled(scores) > MAX_GRADE:
        errs.append(f"{sid}: its captions pooled read at grade {pooled(scores):.1f}, over {MAX_GRADE:g}")
    if len(tab["best"]) > BEST:
        errs.append(f"{sid}: {len(tab['best'])} best, over {BEST}")
    if tab["count"] and len(tab["best"]) != min(BEST, tab["count"]):
        errs.append(f"{sid}: {len(tab['best'])} best of {tab['count']} shown, and it must be min({BEST}, N)")
    if [p for p in tab["all"] if p["id"] in set(x["id"] for x in tab["links"])]:
        errs.append(f"{sid}: a picture both shown and listed as a link")
    return errs


def read_views():
    views = {}
    vdir = DATA / "reference_views"
    for f in sorted(vdir.glob("*/*.json")):
        if f.name.endswith(".match.json"):
            continue
        cam = cp.load_json(f, {})
        if isinstance(cam, dict) and cam.get("structure_id"):
            cam["_view"] = f"{f.parent.name}/{f.stem}"
            views.setdefault(cam["structure_id"], []).append(cam)
    return views


def derive_all():
    tree = cp.read_tree()
    images, _, sources = tree[0], tree[1], tree[2]
    pictures = cp.derive(*tree)
    lib = {r["id"]: r for r in (images or {}).get("images", [])}
    views = read_views()
    tabs = {}
    for sid, entries in sorted((pictures.get(SCENE) or {}).get("by_structure", {}).items()):
        tabs[sid] = build_tab(sid, entries, lib, sources, views)
    return tabs, (pictures.get(SCENE) or {}).get("image_store")


def run(mode, show=None):
    tabs, store = derive_all()
    errs = [e for t in tabs.values() for e in gate_tab(t)]
    for e in errs:
        print(f"FAIL: {e}")
    if errs:
        print(f"FAIL: {len(errs)} problem(s) in the Photos tabs")
        return 1
    if show:
        t = tabs.get(show)
        if not t:
            print(f"no pictures for {show}")
            return 1
        print(f"{show}: {t['count']} shown, {len(t['links'])} link-only; the 12 best by date:")
        by = {p["id"]: p for p in t["all"]}
        for i in t["best"]:
            p = by[i]
            print(f"  {p.get('year') or '----'}  {'CAM ' if p.get('camera') else '    '}{p.get('view') or '-':18} {p['caption']}")
    if mode == "build":
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{SCENE}.json").write_text(json.dumps(
            {"_doc": "GENERATED by tools/compile_photos.py: the Inspect Photos tab of each building. "
                     "Not committed.", "scene": SCENE, "image_store": store, "by_structure": tabs},
            ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    shown_n = sum(t["count"] for t in tabs.values())
    cams = sum(1 for t in tabs.values() for p in t["all"] if p.get("camera"))
    print(f"OK: {len(tabs)} buildings in {SCENE} with pictures; {shown_n} shown ({cams} with a solved camera), "
          f"{sum(len(t['links']) for t in tabs.values())} link-only by their rights; every caption within "
          f"{MAX_CAPTION_WORDS} words and grade {MAX_GRADE:g}")
    return 0


def self_test():
    fails = 0

    def expect(label, cond):
        nonlocal fails
        print(f"  {'ok  ' if cond else 'FAIL'} {label}")
        fails += 0 if cond else 1

    tabs, _ = derive_all()
    g = tabs.get("glessner_house")
    expect("Glessner House has a Photos tab", g is not None and g["count"] > BEST)
    expect("the committed tabs pass the gate", not [e for t in tabs.values() for e in gate_tab(t)])
    if g:
        by = {p["id"]: p for p in g["all"]}
        best = [by[i] for i in g["best"]]
        expect("Glessner's best are 12, by date", len(best) == BEST and [p.get("year") or 9999 for p in best]
               == sorted(p.get("year") or 9999 for p in best))
        n_views = len({p.get("view") for p in g["all"]})
        expect("the best cover min(12, distinct views) viewpoints",
               len({p.get("view") for p in best}) == min(BEST, n_views))
        cams = [p for p in g["all"] if p.get("camera")]
        expect("every picture with a solved camera of a distinct view is among the best",
               all(p["best"] for p in cams if sum(1 for q in cams if q.get("view") == p.get("view")) == 1)
               or len({p.get("view") for p in cams}) > BEST)
        expect("nothing shown carries rights that forbid display",
               all((p["credit"].get("rights") or "").lower() in SHOWN_LIBRARY | SHOWN_SOURCE for p in g["all"]))
        expect("every caption is templated, not cut from its archival title",
               all(not re.search(r"Historic American Buildings Survey|VIEW:", p["caption"]) for p in g["all"]))

        def planted(label, mutate, needle):
            t = copy.deepcopy(g)
            mutate(t)
            errs = gate_tab(t)
            expect(f"{label} is refused", any(needle in e for e in errs))

        planted("a 13-word caption", lambda t: t["all"][0].update(caption=" ".join(["word"] * 13) + "."), "over the limit of 12")
        planted("a caption with a snake_case id", lambda t: t["all"][0].update(caption="The front of glessner_house."), "snake_case")
        planted("a caption with a file path", lambda t: t["all"][0].update(caption="See photo.jpg here."), "file path")
        planted("a picture shown whose rights forbid display",
                lambda t: t["all"][0]["credit"].update(rights="copyright — link only"), "hard rule 6")
        planted("a picture shown with no credit", lambda t: t["all"][0].update(credit={"rights": "public domain"}), "no credit")
        planted("thirteen best", lambda t: t["best"].extend(["x"] * (BEST + 1 - len(t["best"]))), "over 12")
        planted("a camera with no eye", lambda t: t["all"][0].update(camera={"view": "x/y"}), "a camera with no eye")
        planted("captions that pool above grade 9",
                lambda t: [p.update(caption="Unprecedented architectural repudiation.") for p in t["all"]], "pooled read at grade")
    # The year words, on fixed ranges.
    expect("one year reads `from 1888`", year_text(1888, 1888) == (1888, "from 1888"))
    expect("a short range reads `from about` its middle", year_text(1886, 1890) == (1888, "from about 1888"))
    expect("a long range reads `from ... to`", year_text(1885, 1900)[1] == "from 1885 to 1900")
    expect("no year reads `with no date`", year_text(None, None) == (None, "with no date"))
    # The rule, on a fixture: a solved camera beats a nearer year, and a second view beats a better duplicate.
    mk = lambda i, view, year, cam: {"id": i, "view": view, "year": year, "period": "in-period", "kind": "PHOTO",  # noqa: E731
                                     **({"camera": {"eye": [0, 0, 0]}} if cam else {})}
    pool = [mk(f"f{i}", "front elevation", 1904, False) for i in range(15)] + [mk("cam", "front elevation", 1965, True),
                                                                               mk("side", "rear", 1950, False)]
    chosen = [p["id"] for p in choose_best(pool)]
    expect("a solved camera ranks first", chosen[0] == "cam")
    expect("a second viewpoint is taken before the eleventh front", "side" in chosen and len(chosen) == BEST)
    expect("views take turns: with two views, the second view's only picture is second",
           chosen[1] == "side")
    print(f"compile_photos self-test: {'FAIL' if fails else 'OK'} ({fails} assertion(s) did not fire as required)")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--check", action="store_true")
    m.add_argument("--build", action="store_true")
    m.add_argument("--print", metavar="STRUCTURE_ID")
    m.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return run("build" if a.build else "check", show=a.print)


if __name__ == "__main__":
    sys.exit(main())
