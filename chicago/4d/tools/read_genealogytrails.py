#!/usr/bin/env python3
"""Genealogy Trails, Cook County — the assessment pass, and its gate (T-0556).

    tools/read_genealogytrails.py --fetch       re-cache every page under data/research/genealogytrails/
    tools/read_genealogytrails.py --check       the gate
    tools/read_genealogytrails.py --self-test   the gate's assertions still fire when broken

genealogytrails.com/ill/cook/ is a volunteer transcription site, and a transcription
is a POINTER TO ITS ORIGINAL: the row for a section names the work it derives from
where the site names it, and says so plainly where it does not. Nothing here is
payload. `inventory.json` is a reading plan — what the site holds, how much of it is
1830s, and which parts are worth a run — and the extraction lives in the split tickets
that quote this file.

--fetch is the only thing that touches the network, and the gate never runs it: the
gate reads the committed cache, which is what a later run has to be able to trust.
"""
import argparse
import html as htmllib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "data" / "research" / "genealogytrails"
INVENTORY = DOMAIN / "inventory.json"
TEXT = DOMAIN / "text"
HTML = DOMAIN / "html"
CLAIMS = DOMAIN / "claims"

BASE = "https://genealogytrails.com/ill/cook/"
UA = "Mozilla/5.0 (compatible; polecat-4d-research/1.0)"

# Every page this pass read, slug -> absolute URL. The section indexes come from the
# county index page; the leaf pages are the ones a grade had to be earned on rather
# than guessed at from a link's own words.
PAGES = {
    "index": BASE + "index.htm",
    "biographies": BASE + "biographies.html",
    "vitalrecordlindex": BASE + "vitalrecordlindex.html",
    "cemeteryindex": BASE + "cemeteryindex.htm",
    "censusindex": BASE + "censusindex.html",
    "churchdata": BASE + "churchdata.html",
    "townshipindex": BASE + "townshipindex.html",
    "citydirectoryindex": BASE + "citydirectoryindex.html",
    "countyrecords": BASE + "countyrecords.html",
    "events": BASE + "events.html",
    "familyindex": BASE + "familyindex.html",
    "historicalindex": BASE + "historicalindex.html",
    "maps": BASE + "maps.html",
    "marriageindex": BASE + "marriageindex.html",
    "militaryindex": BASE + "militaryindex.html",
    "miscindex": BASE + "miscindex.html",
    "newspaperindex": BASE + "newspaperindex.html",
    "obits": BASE + "obits.htm",
    "educationindex": BASE + "educationindex.html",
    "societies": BASE + "societies.htm",
    "updates": BASE + "updates.html",
    "naturalizations_pg2": BASE + "naturalizations_pg2.html",
    # leaf pages
    "polllist": BASE + "polllist.html",
    "1839chicagodirectory": BASE + "1839chicagodirectory.html",
    "1843directory_1": BASE + "1843directory_1.html",
    "1843directory_2": BASE + "1843directory_2.html",
    "1843directory_3": BASE + "1843directory_3.html",
    "1843directory_4": BASE + "1843directory_4.html",
    "1844directory": BASE + "1844directory.html",
    "1844dir2": BASE + "1844dir2.html",
    "blackhawkwar": BASE + "blackhawkwar.htm",
    "warof1812": BASE + "warof1812.html",
    "marriages_catholic": BASE + "marriages_catholic.html",
    "earlysettlerobits": BASE + "earlysettlerobits.html",
    "marriages": BASE + "marriages.htm",
    "nativeamerican": BASE + "nativeamerican.html",
    "church_catholicdeaths": BASE + "church_catholicdeaths.html",
    "jewry": BASE + "jewry.html",
    "cemeteryhistory": BASE + "cemeteryhistory.html",
    "americanfurco": "https://genealogytrails.com/ill/americanfurco.html",
}

GRADES = {
    "A": "1830s Chicago names or facts in quantity, from a named original — read it in full.",
    "B": "Later evidence that dates, corroborates or enriches 1835 people, trades and places.",
    "C": "Chicago, but wholly post-1850 — no bearing on the scene except by accident.",
    "D": "Nothing here for this project.",
}
STATES = {"unread", "already_read_in_repo", "partly_read_in_repo"}
ROW_FIELDS = {"section", "url", "text_file", "transcribes", "original", "era",
              "items_1830s", "grade", "state", "notes"}
ITEM_FIELDS = {"item", "url", "text_file", "original", "era", "items_1830s",
               "grade", "state", "notes"}

# A page whose link the index carries but which is NOT a Cook County section — the
# other counties, the site-wide furniture, the mail forms. Declared, so that "the
# index links nothing this file skipped" can be an assertion rather than a hope.
NOT_A_SECTION = re.compile(
    r"(?:volunteerinfo|search\.html|myform|trailsmail|/ill/(?:mchenry|kane|will|dupage|lake)/"
    r"|/ill/?$|genealogytrails\.com/?$)"
)


def to_text(raw: str) -> str:
    s = re.sub(r"(?is)<script.*?</script>", "", raw)
    s = re.sub(r"(?is)<style.*?</style>", "", s)
    s = re.sub(r"(?is)<!--.*?-->", "", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|tr|div|li|h[1-6]|td|table)>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = htmllib.unescape(s)
    s = re.sub(r"[ \t\xa0]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return "\n".join(line.strip() for line in s.split("\n")).strip() + "\n"


def links(raw: str):
    out = []
    body = re.sub(r"(?is)<script.*?</script>", "", raw)
    for href, label in re.findall(
            r'(?is)<a\s[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>', body):
        label = re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"(?s)<[^>]+>", "", label))).strip()
        out.append((href.strip(), label))
    return out


def fetch(url: str) -> str:
    out = subprocess.run(["curl", "-sS", "--max-time", "60", "-A", UA, url],
                         capture_output=True)
    if out.returncode != 0:
        raise SystemExit("fetch failed for %s: %s" % (url, out.stderr.decode()[:200]))
    return out.stdout.decode("utf-8", "replace")


def do_fetch() -> None:
    TEXT.mkdir(parents=True, exist_ok=True)
    HTML.mkdir(parents=True, exist_ok=True)
    for slug, url in PAGES.items():
        raw = fetch(url)
        (TEXT / (slug + ".txt")).write_text(to_text(raw), encoding="utf-8")
        if slug == "index":
            # The index is kept RAW as well, because the gate re-reads its links: a
            # section quietly dropped from inventory.json has to fail here, and the
            # text rendering throws the hrefs away.
            (HTML / "index.htm").write_text(raw, encoding="utf-8")
        print("cached %-24s %6d chars" % (slug, len(raw)))
        time.sleep(1.0)


def check(root: Path = ROOT) -> list:
    domain = root / "data" / "research" / "genealogytrails"
    bad = []
    inv_path = domain / "inventory.json"
    if not inv_path.exists():
        return ["data/research/genealogytrails/inventory.json is missing"]
    inv = json.loads(inv_path.read_text(encoding="utf-8"))

    rows = inv.get("sections", [])
    if not rows:
        bad.append("inventory.json declares no sections")
    slugs = set()
    for row in rows:
        name = row.get("section", "?")
        missing = ROW_FIELDS - set(row)
        if missing:
            bad.append("section %r is missing field(s): %s" % (name, ", ".join(sorted(missing))))
            continue
        if row["grade"] not in GRADES:
            bad.append("section %r carries unknown grade %r" % (name, row["grade"]))
        if row["state"] not in STATES:
            bad.append("section %r carries unknown state %r" % (name, row["state"]))
        if not isinstance(row["items_1830s"], int):
            bad.append("section %r counts its 1830s items as %r, not a number"
                       % (name, row["items_1830s"]))
        for tf in [row["text_file"]] + [i.get("text_file") for i in row.get("items", [])]:
            if tf is None:
                continue
            if not (domain / "text" / tf).exists():
                bad.append("section %r names a cached page that is not here: text/%s" % (name, tf))
        for item in row.get("items", []):
            miss = ITEM_FIELDS - set(item)
            if miss:
                bad.append("item %r under %r is missing: %s"
                           % (item.get("item", "?"), name, ", ".join(sorted(miss))))
                continue
            if item["grade"] not in GRADES:
                bad.append("item %r carries unknown grade %r" % (item["item"], item["grade"]))
            if item["state"] not in STATES:
                bad.append("item %r carries unknown state %r" % (item["item"], item["state"]))
        m = re.search(r"([^/]+)$", row["url"])
        if m:
            slugs.add(m.group(1).split("#")[0])

    # The acceptance the ticket wrote in words: "covers every section the index links,
    # none skipped silently". Here it is as an assertion, read off the cached index.
    index_html = domain / "html" / "index.htm"
    if not index_html.exists():
        bad.append("html/index.htm is missing — the gate cannot prove the index was covered")
    else:
        for href, _label in links(index_html.read_text(encoding="utf-8")):
            if href.startswith("mailto:") or NOT_A_SECTION.search(href):
                continue
            leaf = re.search(r"([^/]+)$", href)
            if not leaf:
                continue
            leaf = leaf.group(1).split("#")[0]
            if not leaf:
                continue
            if leaf not in slugs:
                bad.append("the county index links %s and inventory.json has no row for it" % leaf)

    # Quotes. Nothing read in passing may be quoted from memory: every claim's quote
    # is rebuilt out of the committed cache, and one changed character fails.
    for path in sorted((domain / "claims").glob("*.json")) if (domain / "claims").exists() else []:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for claim in doc.get("claims", []):
            cid = claim.get("id", "?")
            for field in ("id", "kind", "reading", "quote", "locator", "describes_date",
                          "town_finding", "notes"):
                if field not in claim:
                    bad.append("claim %s in %s is missing %s" % (cid, path.name, field))
            if "quote" not in claim or "locator" not in claim:
                continue
            tf = claim["locator"].get("text_file")
            src = domain / "text" / (tf or "")
            if not src.exists():
                bad.append("claim %s names a cached page that is not here: text/%s" % (cid, tf))
                continue
            hay = re.sub(r"\s+", " ", src.read_text(encoding="utf-8"))
            if re.sub(r"\s+", " ", claim["quote"]).strip() not in hay:
                bad.append("claim %s does not quote text/%s verbatim" % (cid, tf))
    return bad


def self_test() -> int:
    """Break each assertion in a copy of the tree and prove the gate says so."""
    def run(mutate, expect):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "4d"
            (work / "data" / "research").mkdir(parents=True)
            shutil.copytree(DOMAIN, work / "data" / "research" / "genealogytrails")
            mutate(work)
            bad = check(work)
            hit = [b for b in bad if expect in b]
            print(("  ok   " if hit else "  MISS ") + expect)
            return bool(hit)

    def edit_inv(work, fn):
        p = work / "data" / "research" / "genealogytrails" / "inventory.json"
        doc = json.loads(p.read_text())
        fn(doc)
        p.write_text(json.dumps(doc, indent=2))

    print("self-test — every assertion, broken on purpose:")
    ok = []
    ok.append(run(lambda w: edit_inv(w, lambda d: d["sections"][0].update(grade="A+")),
                  "unknown grade"))
    ok.append(run(lambda w: edit_inv(w, lambda d: d["sections"][0].update(state="skimmed")),
                  "unknown state"))
    ok.append(run(lambda w: edit_inv(w, lambda d: d["sections"][0].update(items_1830s="lots")),
                  "not a number"))
    ok.append(run(lambda w: edit_inv(w, lambda d: d["sections"][0].pop("original")),
                  "missing field"))
    ok.append(run(lambda w: edit_inv(w, lambda d: d["sections"][0].update(text_file="nope.txt")),
                  "cached page that is not here"))
    ok.append(run(lambda w: edit_inv(w, lambda d: d["sections"].pop(0)),
                  "has no row for it"))
    ok.append(run(lambda w: (w / "data/research/genealogytrails/html/index.htm").unlink(),
                  "cannot prove the index was covered"))

    def break_quote(work):
        p = next((work / "data/research/genealogytrails/claims").glob("*.json"))
        doc = json.loads(p.read_text())
        doc["claims"][0]["quote"] = doc["claims"][0]["quote"][:-1] + "Z"
        p.write_text(json.dumps(doc, indent=2))
    ok.append(run(break_quote, "does not quote"))

    def drop_field(work):
        p = next((work / "data/research/genealogytrails/claims").glob("*.json"))
        doc = json.loads(p.read_text())
        doc["claims"][0].pop("describes_date")
        p.write_text(json.dumps(doc, indent=2))
    ok.append(run(drop_field, "is missing describes_date"))

    def blank_inventory(work):
        edit_inv(work, lambda d: d.update(sections=[]))
    ok.append(run(blank_inventory, "declares no sections"))

    print("%d of %d assertions fired" % (sum(ok), len(ok)))
    return 0 if all(ok) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.fetch:
        do_fetch()
        return 0
    if args.self_test:
        return self_test()
    if args.check or True:
        bad = check()
        if bad:
            print("GENEALOGY TRAILS INVENTORY FAIL — %d problem(s)" % len(bad))
            for b in bad:
                print("  - " + b)
            return 1
        inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
        print("OK: %d sections graded, %d cached pages"
              % (len(inv["sections"]), len(list(TEXT.glob("*.txt")))))
        return 0


if __name__ == "__main__":
    sys.exit(main())
