#!/usr/bin/env python3
"""Compile the pictures of each building for its card's Images tab (T-2389).

The owner, 2026-10-11: "As you build each once can you include those photos images of
the house on the card for the house on another tab". The pictures already exist: the
Prairie library's image records (chicago/prairie_1904_v1/research/images/stream-*.json,
merged into data/images.json) with their downloaded copies in the public image store
(kevinrhaas/chicago-images), and the photograph and illustration records in data/sources/
that a structure record cites. This joins them to the structures the walkthrough draws and
writes one slim file per scene, so a card can show its building's pictures without a
visitor's phone fetching the library's 2.5 MB index.

    python3 tools/compile_pictures.py               write data/pictures/<scene>.json
    python3 tools/compile_pictures.py --check       derive in memory and report; write nothing
    python3 tools/compile_pictures.py --self-test   prove the joins and refusals on fixtures

GENERATED, NOT COMMITTED. data/pictures/ is ignored by git and written by publish.sh just
before the mirror. The library is edited by other tickets all the time (T-2368 added 201
held copies in one PR), and a committed derivation of it would go stale on dev the moment
any of them merged — so the file is made from whatever the tree holds when it ships.

WHAT JOINS A PICTURE TO A BUILDING, and nothing else does:
  - 1904: a Prairie structure id carries its street number (`goodman_house_1612_prairie`,
    `glessner_house` is 1800). The library's `by_parcel["prairie_<n>"]` and the records
    whose `building_ids` name a building at that number (buildings-index.tsv) are its
    pictures. A building the index marks demolished before 1904 or absent from the site
    is a different house on the same lot, so its pictures are not this one's.
  - every scene: a photograph or illustration record in data/sources/ that the
    structure record names, and the picture named by a reference view's camera
    (data/reference_views/<id>/<view>.json, the image gate).
  - an accessory (coach house, conservatory, rear or alley building, shed) shows only the
    pictures whose title names that kind of building.

WHAT COUNTS AS A PICTURE OF IT. Maps, site plans, text, permits and documents are kept out
(the library's Images section and the Evidence tab carry those), and so are newspaper
"detail" items, which in this library are portraits of people. What is left is photographs,
prints, plates, postcards and drawings of the building, inside and out.

EVERY PICTURE CARRIES ITS CREDIT. A record without a holder or a creator is not dropped; it
is shown with what it has and says "holder not recorded". A held copy is shown from the
image store; anything else is listed as a link to its holder, never hot-linked.

FOR INSPECT'S PHOTOS TAB (T-2645) each entry also carries, where the data records it:
  - `years`: [earliest, latest] — the library's own `date_earliest`/`date_latest`, or for a
    data/sources record the four-digit years its `date` names. Absent when neither says a
    year: the tab then calls the picture undated, never guesses one.
  - `spot`: where the picture was taken from, ONLY when a solved camera of this building in
    data/reference_views/ names it (the image gate): `u`, `v` and `h` in the structure's
    footprint frame (u east, v north, h metres over its grade), `bearing` (degrees clockwise
    from north, in the same frame) and `pitch`. A drawing's elevation camera, which stands
    hundreds of metres off with a field of view under SPOT_MIN_FOV_DEG to imitate the
    drawing's straight-on look, is not a place anyone stood and carries no spot.
"""

import argparse
import json
import math
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT.parent / "prairie_1904_v1"
IMAGES = LIBRARY / "data" / "images.json"
BUILDINGS = LIBRARY / "research" / "images" / "buildings-index.tsv"
SOURCES = ROOT / "data" / "sources"
STRUCTURES = ROOT / "data" / "structures"
SIDECARS = ROOT / "data" / "sidecars"
VIEWS = ROOT / "data" / "reference_views"
OUT = ROOT / "data" / "pictures"

# Library kinds and views that are not pictures of a building.
NOT_PICTURE_KINDS = {"document", "permit record", "fire insurance map", "atlas plate"}
NOT_PICTURE_VIEWS = {"text", "map", "site plan"}
# The index's statuses that mean the record is another building on the same lot.
OTHER_HOUSE = re.compile(r"demolished before 1904|absent from this site|likely absent", re.I)
# data/sources types that are pictures.
SOURCE_PICTURE_TYPES = {"photograph", "illustration"}
# Accessories and the words a picture's title uses for them.
ACCESSORY = {
    "coach_house": r"coach|carriage|barn|stable|garage",
    "conservatory": r"conservatory|greenhouse|palm",
    "rear_building": r"rear|coach|carriage|barn|stable",
    "alley_building": r"alley|coach|carriage|barn|stable",
}
# Which numbers the Prairie structures that do not carry one stand at.
NUMBER_OF = {"glessner_house": "1800"}

# A solved camera narrower than this is a drawing's far-off elevation camera, not a spot (T-2645).
SPOT_MIN_FOV_DEG = 5.0
YEAR_RE = re.compile(r"\b(1[6-9]\d\d|20\d\d)\b")

# Sort: how a visitor reads a building — its fronts first, then the street, drawings, rooms.
VIEW_RANK = {
    "front elevation": 0, "oblique front": 0, "side elevation": 1, "rear": 1,
    "entrance detail": 2, "detail": 2, "roof detail": 2, "courtyard": 2, "courtyard detail": 2,
    "street view": 3, "aerial": 3, "plan": 4, "section": 4, "interior": 5,
}
PERIOD_RANK = {"in-period": 0, "near-period": 1, "later": 2}
KIND_RANK = {"photograph": 0, "stereograph": 0, "postcard": 0, "aerial": 0}   # prints 1, drawings 2
KIND_RANK.update({k: 2 for k in ("architectural drawing", "measured drawing")})

KIND_LABEL = {
    "photograph": "PHOTO", "stereograph": "STEREO", "postcard": "POSTCARD",
    "engraving": "ENGRAVING", "lithograph": "LITHO", "publication plate": "PLATE",
    "architectural drawing": "DRAWING", "measured drawing": "MEASURED DWG",
    "bird's-eye view": "BIRD'S-EYE", "aerial": "AERIAL", "newspaper item": "NEWSPAPER",
    "illustration": "ILLUSTRATION",
}


def clip(text, n):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= n else text[: n - 1].rstrip(" ,;:—-") + "…"


def first_sentence(text, n):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    m = re.match(r"(.+?[.;])(\s|$)", text)
    return clip(m.group(1) if m and len(m.group(1)) > 20 else text, n).rstrip(";,: ")


def load_json(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def building_numbers(tsv_text):
    """pa-id -> street number on Prairie, for buildings that stood on their lot in 1904."""
    out = {}
    for line in tsv_text.splitlines():
        cols = line.split("\t")
        if len(cols) < 2 or not cols[0].startswith("pa-"):
            continue
        status = cols[4] if len(cols) > 4 else ""
        if OTHER_HOUSE.search(status) or "predecessor" in cols[0]:
            continue
        m = re.match(r"(\d{4}) S\. Prairie Avenue$", cols[1].strip())
        if m:
            out[cols[0]] = m.group(1)
    return out


def structure_place(sid):
    """(number on Prairie or None, accessory kind or None) for a structure id."""
    if sid in NUMBER_OF:
        return NUMBER_OF[sid], None
    m = re.search(r"_(\d{4})_prairie(?:_([a-z_]+))?$", sid)
    if not m:
        return None, None
    suffix = m.group(2)
    if sid.startswith("shed_"):
        return m.group(1), "rear_building"
    if suffix in (None, "front"):
        return m.group(1), None
    return m.group(1), suffix if suffix in ACCESSORY else "rear_building"


def library_entry(r, store, primary=True):
    local = r.get("local") or {}
    ref = r.get("reference_copy") or {}
    credit = ref.get("credit") or {}
    held = None
    prefix, base = (store or {}).get("prefix"), (store or {}).get("base_url")
    disp, thumb = local.get("display"), local.get("thumb") or local.get("display")
    if disp and prefix and base and disp.startswith(prefix) and thumb.startswith(prefix):
        held = {"t": thumb[len(prefix):], "f": disp[len(prefix):]}
        px = local.get("original_px")
        if isinstance(px, list) and len(px) == 2 and px[1]:
            held["a"] = round(px[0] / px[1], 3)
    e = {
        "id": r["id"],
        "kind": KIND_LABEL.get(r.get("kind"), clip(r.get("kind"), 16).upper()),
        "view": r.get("view") or None,
        "title": clip(credit.get("title") or r.get("title"), 160),
        "date": clip(credit.get("date") or r.get("date"), 60) or None,
        "creator": clip(credit.get("creator") or r.get("creator"), 120) or None,
        "holder": clip(credit.get("repository") or r.get("repository"), 140) or None,
        "collection": clip(credit.get("collection") or r.get("collection"), 100) or None,
        "url": credit.get("catalog_url") or r.get("catalog_url") or None,
        "rights": r.get("rights") or None,
        "period": r.get("period") or None,
        "street": bool(r.get("streetscape")),
        "library": True,
    }
    if ref:
        e["reference_copy"] = True
    if held:
        e["held"] = held
    lo, hi = r.get("date_earliest"), r.get("date_latest")
    lo, hi = (lo if isinstance(lo, int) else None), (hi if isinstance(hi, int) else None)
    if lo is not None or hi is not None:
        e["years"] = [lo, hi]
    # Held first; the building's own fronts before the street it stands in, and a picture
    # OF it (named first) before one it stands in the corner of; photographs before prints
    # before drawings; then the picture nearest the scene year.
    year = r.get("date_earliest") or r.get("date_latest")
    e["_sort"] = (0 if held else 1, VIEW_RANK.get(r.get("view"), 3), 0 if primary else 1,
                  KIND_RANK.get(r.get("kind"), 1), PERIOD_RANK.get(r.get("period"), 1),
                  abs(year - 1904) if isinstance(year, int) else 999, r["id"])
    return e


def source_years(date):
    """[earliest, latest] of the four-digit years a source record's date names, or None."""
    ys = [int(y) for y in YEAR_RE.findall(str(date or ""))]
    return [min(ys), max(ys)] if ys else None


def camera_spot(cam):
    """Where a solved camera stood, in the structure's footprint frame, or None (T-2645).

    The camera looks along `basis_right_up_forward`'s forward vector where it has one (an
    inclined or rolled photograph), else along `yaw_deg`, level. None for a camera with no
    eye, a diagnostic_only camera, or one narrower than SPOT_MIN_FOV_DEG (a drawing's elevation camera)."""
    if cam.get("diagnostic_only") is True:
        return None
    eye = cam.get("eye")
    if not (isinstance(eye, list) and len(eye) == 3 and all(isinstance(x, (int, float)) for x in eye)):
        return None
    px, f = cam.get("image_px"), cam.get("focal_px")
    if isinstance(px, list) and len(px) == 2 and isinstance(f, (int, float)) and f > 0:
        if math.degrees(2 * math.atan(px[1] / 2 / f)) < SPOT_MIN_FOV_DEG:
            return None
    basis = cam.get("basis_right_up_forward")
    if isinstance(basis, list) and len(basis) == 3 and isinstance(basis[2], list) and len(basis[2]) == 3:
        fe, fn, fu = basis[2]
        bearing = math.degrees(math.atan2(fe, fn))
        pitch = math.degrees(math.asin(max(-1.0, min(1.0, fu))))
    elif isinstance(cam.get("yaw_deg"), (int, float)):
        bearing, pitch = float(cam["yaw_deg"]), 0.0
    else:
        return None
    return {"u": round(eye[0], 2), "v": round(eye[1], 2), "h": round(eye[2], 2),
            "bearing": round(bearing % 360, 1), "pitch": round(pitch, 1)}


def source_entry(d):
    rights = d.get("rights_status")
    years = source_years(d.get("date"))
    e = {
        "id": d["id"],
        "kind": KIND_LABEL.get(d.get("type"), "PICTURE"),
        "view": None,
        "title": first_sentence(d.get("citation"), 160),
        "date": clip(d.get("date"), 60) or None,
        "creator": clip(d.get("author"), 120) or None,
        "holder": first_sentence(d.get("repository"), 140) or None,
        "collection": None,
        "url": d.get("url") or d.get("archived_url") or None,
        "rights": rights.replace("_", " ") if isinstance(rights, str) else None,
        "period": None,
        "street": False,
        "library": False,
        "_sort": (1, 0, 0, 0 if d.get("type") == "photograph" else 1, 1, int(re.search(r"\d{4}", str(d.get("date") or "9999")).group(0))
                  if re.search(r"\d{4}", str(d.get("date") or "")) else 9999, d["id"]),
    }
    if years:
        e["years"] = years
    return e


def is_picture(r):
    if r.get("kind") in NOT_PICTURE_KINDS or r.get("view") in NOT_PICTURE_VIEWS:
        return False
    if r.get("kind") == "newspaper item" and r.get("view") in (None, "detail"):
        return False
    return True


def derive(images, tsv_text, sources, structure_texts, scenes, views):
    """-> {scene: {"image_store": ..., "by_structure": {sid: [entry, ...]}}}.

    images: the library's merged data/images.json (or None when the library is absent);
    sources: {id: record}; structure_texts: {sid: text of data/structures/<sid>.json};
    scenes: {scene: [sid, ...]}; views: {sid: [camera, ...]}.
    """
    store = (images or {}).get("image_store") or {}
    recs = {r["id"]: r for r in (images or {}).get("images", [])}
    number_of_pa = building_numbers(tsv_text or "")
    pas_at = {}
    for pa, n in number_of_pa.items():
        pas_at.setdefault(n, set()).add(pa)
    by_building = (images or {}).get("by_building", {})
    by_parcel = (images or {}).get("by_parcel", {})
    picture_sources = {k for k, v in sources.items() if v.get("type") in SOURCE_PICTURE_TYPES}
    # A source id is named in a structure record as a value or inside its prose notes.
    src_pat = re.compile(r'(?<![A-Za-z0-9_])(' + "|".join(map(re.escape, sorted(picture_sources, key=len, reverse=True)))
                         + r')(?![A-Za-z0-9_])') \
        if picture_sources else None

    out = {}
    for scene, sids in sorted(scenes.items()):
        by_structure = {}
        for sid in sorted(sids):
            entries, seen_urls = {}, set()
            number, accessory = structure_place(sid)
            lib_ids = set()
            if number and scene == "1904":
                lib_ids.update(by_parcel.get(f"prairie_{number}", []))
                for pa in pas_at.get(number, ()):
                    lib_ids.update(by_building.get(pa, []))
            for cam in views.get(sid, []):
                if cam.get("library_image"):
                    lib_ids.add(cam["library_image"])
            for iid in lib_ids:
                r = recs.get(iid)
                if not r or not is_picture(r):
                    continue
                # A record that names buildings but not this one shows its neighbours, or the
                # house that stood on this lot before (a predecessor is not in number_of_pa).
                named = {number_of_pa.get(b) for b in r.get("building_ids") or []}
                if r.get("building_ids") and number and number not in named:
                    continue
                if accessory and not re.search(ACCESSORY[accessory], r.get("title") or "", re.I):
                    continue
                ids = r.get("building_ids") or []
                entries[iid] = library_entry(r, store, primary=not ids or number_of_pa.get(ids[0]) == number)
            for e in entries.values():
                if e["url"]:
                    seen_urls.add(e["url"])
            cited = set(src_pat.findall(structure_texts.get(sid, ""))) if src_pat else set()
            cited.update(c["source_id"] for c in views.get(sid, []) if c.get("source_id") in picture_sources)
            for s_id in sorted(cited):
                d = sources[s_id]
                if s_id in entries or (d.get("url") and d.get("url") in seen_urls):
                    continue
                entries[s_id] = source_entry(d)
            # T-2645: "from this spot", only where this building's own solved camera names it.
            for cam in views.get(sid, []):
                spot = camera_spot(cam)
                for key in (cam.get("library_image"), cam.get("source_id")):
                    if spot and key in entries and "spot" not in entries[key]:
                        entries[key]["spot"] = spot
            if entries:
                ordered = sorted(entries.values(), key=lambda e: e["_sort"])
                for e in ordered:
                    del e["_sort"]
                    for k in [k for k, v in e.items() if v is None or v is False]:
                        if k not in ("held",):
                            del e[k]
                by_structure[sid] = ordered
        out[scene] = {
            "_doc": "GENERATED by chicago/4d/tools/compile_pictures.py at publish — the pictures of each "
                    "building for its card's Images tab, with their credits. Not committed; edit the "
                    "Prairie library's streams or data/sources/, not this file.",
            "scene": scene,
            "image_store": {"base_url": store.get("base_url"), "repository": store.get("repository")}
            if store.get("base_url") else None,
            "library_viewer": "../prairie-1904/" if scene == "1904" else None,
            "by_structure": by_structure,
        }
    return out


def read_tree():
    images = load_json(IMAGES)
    tsv = BUILDINGS.read_text(encoding="utf-8") if BUILDINGS.exists() else ""
    sources = {}
    for f in sorted(SOURCES.glob("*.json")):
        d = load_json(f)
        if isinstance(d, dict) and d.get("id"):
            sources[d["id"]] = d
    structure_texts = {f.stem: f.read_text(encoding="utf-8") for f in sorted(STRUCTURES.glob("*.json"))}
    skip = {"index", "terrain", "exclusions", "fauna_sources", "flora_sources", "flora_clamp", "residents_sources"}
    scenes = {}
    for d in sorted(p for p in SIDECARS.iterdir() if p.is_dir() and re.fullmatch(r"\d{4}", p.name)):
        scenes[d.name] = [f.stem for f in d.glob("*.json") if f.stem not in skip]
    views = {}
    if VIEWS.exists():
        for f in sorted(VIEWS.glob("*/*.json")):
            if f.name.endswith(".match.json"):
                continue
            cam = load_json(f, {})
            if isinstance(cam, dict):
                views.setdefault(f.parent.name, []).append(cam)
    return images, tsv, sources, structure_texts, scenes, views


def summary(out):
    for scene, doc in out.items():
        bs = doc["by_structure"]
        n = sum(len(v) for v in bs.values())
        held = sum(1 for v in bs.values() for e in v if e.get("held"))
        print(f"   {scene}: {len(bs)} buildings with pictures — {n} pictures, {held} held, {n - held} linked")


def self_test():
    fails = []
    tsv = ("pa-1612-1\t1612 S. Prairie Avenue\tGoodman\t\tinferred present\n"
           "pa-1709-46\t1709 S. Prairie Avenue\tWilliams\t\tdemolished before 1904\n"
           "pa-1709-47\t1709 S. Prairie Avenue\tKellogg\t\tinferred present\n")
    store = {"base_url": "https://example.test/files/", "prefix": "research/images/files/", "repository": "x/y"}
    def img(i, **kw):
        r = {"id": i, "kind": "photograph", "view": "front elevation", "title": i, "building_ids": [],
             "streetscape": False, "period": "in-period", "date_earliest": 1900}
        r.update(kw)
        return r
    held = {"display": "research/images/files/a.jpg", "thumb": "research/images/files/a-thumb.jpg", "original_px": [1200, 800]}
    images = {"image_store": store, "by_parcel": {"prairie_1612": ["map", "front"]},
              "by_building": {"pa-1612-1": ["front", "text", "portrait", "neighbour", "street"],
                              "pa-1709-46": ["old", "before"], "pa-1709-47": ["new"]},
              "images": [img("front", building_ids=["pa-1612-1"], local=held,
                             reference_copy={"credit": {"title": "The front", "repository": "Holder"}}),
                         img("map", kind="atlas plate", view="map"),
                         img("text", kind="newspaper item", view="text"),
                         img("portrait", kind="newspaper item", view="detail"),
                         img("neighbour", building_ids=["pa-1709-47"]),
                         img("street", view="street view", streetscape=True, building_ids=["pa-1612-1", "pa-1709-47"]),
                         img("old", building_ids=["pa-1709-46"]), img("new", building_ids=["pa-1709-47"]),
                         img("before", view="oblique front", streetscape=True, building_ids=["pa-1709-46"]),
                         img("barn", building_ids=["pa-1612-1"], title="Coach house from the alley")]}
    images["by_building"]["pa-1612-1"].append("barn")
    sources = {"plate": {"id": "plate", "type": "illustration", "citation": "A plate of the inn. More.",
                         "url": "https://holder.test/p", "repository": "Holder library."},
               "book": {"id": "book", "type": "book", "citation": "A book."}}
    texts = {"inn": '{"sources": ["plate", "book"]}'}
    scenes = {"1904": ["goodman_house_1612_prairie", "goodman_house_1612_prairie_coach_house",
                       "kellogg_house_1709_prairie"], "1835": ["inn"]}
    views = {"goodman_house_1612_prairie": [
        {"library_image": "front", "eye": [30.0, -5.0, 1.6], "yaw_deg": 290, "image_px": [1200, 800], "focal_px": 1000},
        {"library_image": "street", "eye": [-400, 5.0, 3.0], "yaw_deg": 90, "image_px": [1600, 1500], "focal_px": 47000}]}
    out = derive(images, tsv, sources, texts, scenes, views)
    g = [e["id"] for e in out["1904"]["by_structure"].get("goodman_house_1612_prairie", [])]
    def expect(cond, what):
        if not cond:
            fails.append(what)
    expect(g[:1] == ["front"], f"the held front leads 1612's pictures (got {g})")
    expect("map" not in g and "text" not in g, "maps and text are not pictures of a building")
    expect("portrait" not in g, "a newspaper detail (a portrait) is not a picture of the house")
    expect("neighbour" not in g, "a picture naming only another building is not this one's")
    expect("street" in g, "a street view naming this building is kept")
    f0 = out["1904"]["by_structure"]["goodman_house_1612_prairie"][0]
    expect(f0.get("held") == {"t": "a-thumb.jpg", "f": "a.jpg", "a": 1.5}, f"held copy resolves into the store ({f0.get('held')})")
    expect(f0.get("title") == "The front" and f0.get("holder") == "Holder", "the reference copy's credit is the one shown")
    ch = [e["id"] for e in out["1904"]["by_structure"].get("goodman_house_1612_prairie_coach_house", [])]
    expect(ch == ["barn"], f"a coach house shows only pictures that name it (got {ch})")
    k = [e["id"] for e in out["1904"]["by_structure"].get("kellogg_house_1709_prairie", [])]
    expect("old" not in k and "before" not in k and "new" in k,
           f"a house demolished before 1904 lends its lot no pictures, street views included (got {k})")
    inn = out["1835"]["by_structure"].get("inn", [])
    expect([e["id"] for e in inn] == ["plate"], "a cited illustration source is a picture; a cited book is not")
    expect(inn and "held" not in inn[0] and inn[0].get("url") == "https://holder.test/p", "a source with no held copy is a link")
    # T-2645: the years the data records, and a spot only where a solved camera stood.
    by = {e["id"]: e for e in out["1904"]["by_structure"]["goodman_house_1612_prairie"]}
    expect(by["front"].get("years") == [1900, None], f"a library record carries its own years ({by['front'].get('years')})")
    expect(by["front"].get("spot") == {"u": 30.0, "v": -5.0, "h": 1.6, "bearing": 290.0, "pitch": 0.0},
           f"a solved camera gives its picture a spot ({by['front'].get('spot')})")
    expect("spot" not in by["street"], "a drawing's far-off elevation camera is not a spot")
    diagnostic_views = {"goodman_house_1612_prairie": [dict(views["goodman_house_1612_prairie"][0], diagnostic_only=True)]}
    diagnostic = derive(images, tsv, sources, texts, scenes, diagnostic_views)
    diagnostic_front = next(e for e in diagnostic["1904"]["by_structure"]["goodman_house_1612_prairie"] if e["id"] == "front")
    expect(diagnostic_front == {k: v for k, v in by["front"].items() if k != "spot"},
           "a diagnostic camera retains its picture and credit but offers no historical camera spot")
    expect("spot" not in by.get("barn", {}) and "spot" not in out["1904"]["by_structure"]
           ["goodman_house_1612_prairie_coach_house"][0], "a picture no camera names has no spot")
    expect(source_years("1963 (sheets 1-5); 1965 (sheet 6)") == [1963, 1965] and source_years("n.d.") is None,
           "a source's years are the ones its date names, and none where it names none")
    tilt = camera_spot({"eye": [0, 0, 2], "basis_right_up_forward": [[1, 0, 0], [0, 0, 1], [0, -0.9950042, 0.0998334]]})
    expect(tilt and tilt["bearing"] == 180.0 and tilt["pitch"] == 5.7, f"a basis camera's bearing and pitch ({tilt})")
    for fail in fails:
        print(f"FAIL: {fail}")
    if fails:
        return 1
    print("OK: joins, filters, accessories, demolished lots and credits all behave")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    out = derive(*read_tree())
    if not IMAGES.exists():
        print(f"   note: {IMAGES.relative_to(ROOT.parent)} is absent — 1904 has only its cited sources")
    if a.check:
        summary(out)
        print("OK: pictures derive (generated at publish; nothing written)")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for scene, doc in out.items():
        (OUT / f"{scene}.json").write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    summary(out)
    print(f"wrote {OUT.relative_to(ROOT)}/<scene>.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
