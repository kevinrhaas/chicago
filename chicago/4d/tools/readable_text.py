#!/usr/bin/env python3
"""Research prose as a person reads it: no ticket number, no record id, no file path (T-2825).

    python3 tools/readable_text.py --self-test     plant each rewrite and require it made
    python3 tools/readable_text.py --show "text"   print one string as a reader gets it

THE OWNER'S RULING, 2026-10-18: "You should rewrite the records so you are not referring to
internal ticket numbers or internal record ids in researcher or educator mode." The records
are rewritten, not hidden, and in every mode a person reads. And, the same day: "If in that
mode you want to refer to the tickets as a link or something as an external source or link
back, ok, but I don't want to talk internal ticket language to researchers."

The research prose this project writes — `docs/LIBERTIES.md` first, 624 entries of it — is
written by the people building the town for each other: it names the ticket a ruling was
made under, the record id a claim is about, the file a number was read from. Those are the
right words for the next builder and the wrong ones for anybody else. The markdown is
append-only and stays as written; this module is the step between it and a reader, run by
each compiler that turns such prose into what a page shows, so the page and the gate read
the same rewritten text.

WHAT IT DOES TO A STRING, in this order:

  1. A ticket number goes, and the ticket is kept as a reference beside the text, never in
     it (`refs`, written by the compiler as `work_refs`: the one shape Researcher mode can
     turn into a link behind plain words, and nothing else does). Where it was only a
     label — "(T-1460)", "2026-09-29 (T-1460) —", "**T-1353** (…)" in a list of related
     records — it is dropped. Where it is part of the sentence ("T-0795 had walked the
     whole sheet", "since T-1815 every stoop") it becomes what it is relative to the record
     that names it: "this work", "earlier work" or "later work" (tickets are numbered in
     the order they were opened, so a lower number IS earlier), or "other work" when the
     record has no ticket of its own to be compared with.
  2. A record id becomes the thing it names: a building's own name, a source's human title
     (its citation's opening words, the rule Inspect's Sources tab uses, T-2644), a
     household's or a person's name, a firm's name, a block's number on Wright's 1834 plat,
     a plant community's name, a liberty's title. An id nothing names becomes its words
     ("roof_pitch_deg" → "roof pitch (deg)"), which is what it said all along.
  3. A file path becomes what the file is: "the liberties register", "the research notes
     on the Glessner frontage", "the block infill generator", "the 1835 streets data".
  4. The project's own words for its machinery: a ticket is "work", a source's tier is the
     kind of source it is (the ladder's own terms, as Inspect says them), a tier of blocks
     is a row, and the order book is the reconstruction plan.

It never adds a claim. Every substitution is a name the data already gives the thing, or
the thing's own id spelt as words; the evidence a line rests on is still named, by title.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from compile_summaries import LINK, PATH, SNAKE, TICKET, lint_string  # noqa: E402

# A ticket, or a design-doc / pull-request number the lint calls a ticket too.
TICKET_NO = re.compile(r"\bT-(\d{2,5})\b")
REF = re.compile(r"(?:\*\*)?\b(?:T|NAV|PR)-?#?\d{2,5}\b(?:\*\*)?")
# A run of them: "T-1985, T-1986, T-1989 and T-2000", "**T-1529**, **T-1525**", "T-1909 to T-1929".
REF_RUN = re.compile(
    r"(?:\b(?:the\s+)?(?:tickets?|work items?)\s+)?"
    + REF.pattern
    + r"(?:(?:\s*(?:,|and|or|to|–|-|/|&)\s*|\s+)" + REF.pattern + r")*",
    re.IGNORECASE,
)
SENTENCE_OF_REFS = re.compile(
    r"(?:(?<=^)|(?<=[.!?]\s))" + REF.pattern
    + r"(?:\s*[,;]?\s*(?:and\s+|[A-Za-z-]+(?:\s+(?:by|in|under))?\s+)?" + REF.pattern + r")*\s*[.:]\s+",
    re.IGNORECASE)
DETERMINER = re.compile(r"(?:\b(?:the|this|that|its|their|his|her|a|an|each|every|our|whose)\s+|\w['’]s\s+)$",
                        re.IGNORECASE)
# Words left in a bracket once its ticket numbers are gone that say nothing without them.
FILLER = re.compile(
    r"^(?:[\s,;:·—–\-/&]|and|or|to|of|piece|pieces|stretch|part|parts|item|items|stage|"
    r"parent|this|entry|this entry|ticket|tickets|see|per|under|by|in|from|for|via|"
    r"the|a|an|its|which|and\s+its|\d+[a-z]?)*$",
    re.IGNORECASE,
)

# The source ladder's rungs as Inspect says them (js/strings/inspect-sources.js kind.N).
SOURCE_KIND = {"1": "first-hand", "2": "a witness remembering", "3": "gathered from witnesses",
               "4": "a historian's account", "5": "a modern reconstruction", "6": "a popular map"}

# Files people name often enough to deserve their own words.
NAMED_FILES = {
    "docs/LIBERTIES.md": "the liberties register",
    "LIBERTIES.md": "the liberties register",
    "AGENTS.md": "the project's rules",
    "docs/STATUS.md": "the project's status notes",
    "STATUS.md": "the project's status notes",
    "docs/ROADMAP.md": "the project's roadmap",
    "docs/PROVENANCE.md": "the project's provenance guide",
    "docs/PLAN.md": "the project's plan",
    "tools/check.sh": "the project's gate",
    "check.sh": "the project's gate",
    "tools/validate.py": "the validator",
    "validate.py": "the validator",
    "tools/publish.sh": "the publishing step",
    "data/exclusions.json": "the exclusions record",
    "data/liberties.json": "the liberties register",
}
TOOL_KIND = [
    (re.compile(r"^test_"), "the {} test"),
    (re.compile(r"^(?:check|measure|audit|verify|gate)_"), "the {} check"),
    (re.compile(r"^(?:generate|emit|build|bake|deal|raise|mint|seat)_"), "the {} generator"),
    (re.compile(r"^compile_"), "the {} compiler"),
    (re.compile(r"^(?:read|parse|extract|transcribe)_"), "the {} reader"),
]
UNIT = re.compile(r"_(ft|m|m2|deg|mm|in|pct|px)$")


def words(token: str) -> str:
    """An identifier as words: underscores, dots and hyphens become spaces, a unit suffix
    becomes its bracket (`roof_pitch_deg` → "roof pitch (deg)"), and an all-caps constant
    is lower-cased (`WORKED_SHARE` → "worked share")."""
    t = str(token).strip("`*_.-/ ")
    t = UNIT.sub(r" (\1)", t)
    if re.fullmatch(r"[A-Z0-9_]+", t) and re.search(r"[A-Z]{2}", t):
        t = t.lower()
    t = re.sub(r"[_.]+", " ", t)
    t = re.sub(r"(?<=[A-Za-z])-(?=[A-Za-z])", "-", t)
    return re.sub(r"\s+", " ", t).strip()


# ------------------------------------------------------------------- source titles

ABBREV = {"mr", "mrs", "ms", "dr", "st", "ave", "av", "blvd", "jr", "sr", "co", "gen", "col", "rev",
          "capt", "lt", "mt", "ft", "no", "nos", "vs", "inc", "bros", "messrs", "prof", "hon", "gov",
          "esq", "ill", "vol", "vols", "ed", "eds", "ca", "c", "pp", "p", "fig", "figs", "ser", "dept"}
TITLE_MAX, TITLE_MIN = 80, 36


def _clean(text: str) -> str:
    t = str(text or "").strip()
    return t if t and not lint_string(t) else ""


def _sentences(text: str) -> list[str]:
    out, start = [], 0
    for i, ch in enumerate(text):
        if ch == ";":
            out.append(text[start:i]); start = i + 1; continue
        if ch != "." or not (text[i + 1:i + 2].isspace()):
            continue
        nxt = text[i + 1:].lstrip()[:1]
        if not re.match(r"[A-Z'\"‘“(]", nxt or ""):
            continue
        m = re.search(r"([A-Za-z]+)$", text[start:i])
        word = m.group(1) if m else ""
        if re.fullmatch(r"[A-Z]", word) or word.lower() in ABBREV:
            continue
        out.append(text[start:i]); start = i + 1
    out.append(text[start:])
    return [x.strip() for x in out if x.strip()]


def _trim_tail(x: str) -> str:
    x = re.sub(r"[\s,;:(\[–—-]+$", "", x)
    return re.sub(r"\s+\($", "", x).strip()


def source_title(citation: str) -> str:
    """The Python twin of js/inspect-sources.js `sourceTitle` (T-2644): a source's human
    title is its citation's opening words, cut before anything that is not for a reader and
    shortened at a word. Always a prefix of the citation, so it claims nothing it does not."""
    text = re.sub(r"\s+", " ", str(citation or "")).strip()
    if not text:
        return ""
    parts = _sentences(text)
    title = parts[0] if parts else ""
    i = 1
    while i < len(parts) and len(title) < TITLE_MIN:
        title = f"{title}. {parts[i]}"; i += 1
    if not _clean(title):
        ws, keep = title.split(" "), ""
        for j in range(1, len(ws) + 1):
            nxt = " ".join(ws[:j])
            if not _clean(nxt):
                break
            keep = nxt
        title = keep
    title = _trim_tail(title)
    if len(title) > TITLE_MAX:
        cut = title[:TITLE_MAX]
        title = _trim_tail(cut[:max(cut.rfind(" "), 20)]) + "…"
    return title if len([w for w in title.split(" ") if re.search(r"[A-Za-z]{2,}", w)]) >= 2 else ""


# ------------------------------------------------------------------- names

SPEC = re.compile(r"^Reconstructed\s+(\S+)\s+(.+?)\s+#(\d+)$")
RAISED = re.compile(r"^Reconstructed\s+(.+?)\s+\(([^)]+)\)$")


def structure_title(name: str, sid: str) -> str:
    """A building's name as the card would lead with it. An anonymous roof's production
    name ("Reconstructed D3 one-room frame cottage #017") is said as what it is ("a one-room
    frame cottage"), the half of js/display-name.js that needs no sidecar."""
    name = str(name or "").strip()
    m = SPEC.match(name) or RAISED.match(name)
    if m:
        desc = m.group(2) if SPEC.match(name) else m.group(1)
        return f"{'an' if re.match(r'[aeiou](?!ne)', desc, re.I) else 'a'} {desc}"
    return name or words(sid)


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


class Names:
    """Every id a research record names, against the name the data gives it."""

    def __init__(self, root: Path = ROOT, extra: dict | None = None):
        self.root = Path(root)
        self.table: dict[str, str] = {}
        self.kind: dict[str, str] = {}
        self._load()
        for k, v in (extra or {}).items():
            self.add(k, v, "extra")

    def add(self, key, name, kind):
        if key and name and key not in self.table:
            # A name can carry the machinery too ("… (district draft; refined by T-1932)"):
            # it is said the way any other prose is, without the names, so it cannot loop.
            if problems(name):
                name, _ = rewrite(name, None)
            self.table[key] = name
            self.kind[key] = kind

    def _load(self):
        r = self.root
        for p in sorted(glob.glob(str(r / "data" / "structures" / "*.json"))):
            d = _load(Path(p)) or {}
            sid = Path(p).stem
            self.add(sid, structure_title(plain_name(d.get("name", "")), sid), "structure")
        for p in sorted(glob.glob(str(r / "data" / "sources" / "*.json"))):
            d = _load(Path(p)) or {}
            sid = d.get("id") or Path(p).stem
            title = source_title(d.get("citation", ""))
            if title:
                self.add(sid, title, "source")
        for p in sorted(glob.glob(str(r / "data" / "residents" / "households" / "*.json"))):
            d = _load(Path(p)) or {}
            hid = d.get("id") or Path(p).stem
            name = str(d.get("name") or "").split(" — ")[0].strip()
            if name and _clean(name):
                self.add(hid, name[0].lower() + name[1:] if name.startswith("The ") else name, "household")
            for person in d.get("persons") or []:
                if isinstance(person, dict) and person.get("id") and _clean(str(person.get("name") or "")):
                    self.add(person["id"], person["name"], "person")
        biz = _load(r / "data" / "businesses" / "index.json") or {}
        for b in (biz.get("businesses") if isinstance(biz, dict) else None) or []:
            if isinstance(b, dict) and b.get("id") and _clean(str(b.get("name") or "")):
                self.add(b["id"], b["name"], "business")
        blocks = _load(r / "data" / "traces" / "thompson_block_numbering.json") or {}
        for b in blocks.get("blocks") or []:
            if isinstance(b, dict) and b.get("block_id") and b.get("number") is not None:
                self.add(b["block_id"], f"block {b['number']}", "block")
        for p in sorted(glob.glob(str(r / "data" / "flora" / "zones" / "*.json"))):
            d = _load(Path(p)) or {}
            zid = d.get("id") or Path(p).stem
            nm = d.get("name") or d.get("community")
            if isinstance(nm, str) and _clean(nm):
                self.add(zid, f"the {nm[0].lower() + nm[1:]}" if not nm[:1].isupper() or " " in nm else nm, "zone")
        exc = _load(r / "data" / "exclusions.json") or {}
        for e in exc.get("excluded") or []:
            if isinstance(e, dict) and e.get("id") and _clean(str(e.get("name") or "")):
                self.add(e["id"], e["name"], "exclusion")

    def get(self, token: str) -> str | None:
        return self.table.get(token)


# ------------------------------------------------------------------- the rewrite

def path_words(path: str, names: Names | None = None) -> str:
    """A file path as what the file is."""
    p = path.strip("`'\"()[]{}<>,;:").rstrip(".")
    p = re.sub(r"^(?:\./|\.\./|/)+", "", p)
    p = re.sub(r"^(?:chicago/4d/|site/4d/)", "", p)
    flags = ""
    if " " in p:
        p, flags = p.split(" ", 1)
    if p in NAMED_FILES:
        return NAMED_FILES[p]
    parts = [x for x in p.split("/") if x]
    if not parts:
        return "the project's files"
    leaf = parts[-1]
    stem = re.sub(r"\.[A-Za-z0-9]+$", "", leaf)
    ext = leaf[len(stem) + 1:].lower() if "." in leaf else ""
    top = parts[0]
    if names is not None:
        for key in (stem, leaf):
            hit = names.get(key)
            if hit and names.kind.get(key) == "source" and "sources" in parts:
                return hit
            if hit and names.kind.get(key) == "structure" and "structures" in parts:
                return f"the record of {hit}"
    if top in ("docs",) and len(parts) > 1 and parts[1].lower() == "research":
        topic = parts[2] if len(parts) > 3 else stem
        topic = re.sub(r"^(?:[a-z]\d{2}|r\d+)-", "", topic)
        topic = re.sub(r"[-_](?:\d{4})$", "", topic)
        topic = re.sub(r"^\d{2}-", "", topic)
        w = words(topic.replace("-", " ")) if topic.lower() not in ("readme", "") else ""
        if ext in ("jpg", "jpeg", "png", "webp", "gif"):
            return f"an image in the research notes{f' on {w}' if w else ''}"
        return f"the research notes{f' on {w}' if w else ''}"
    if top == "docs":
        return f"the project's notes on {words(stem.replace('-', ' ')).lower()}"
    if top == "tools" or ext in ("py", "mjs", "sh") and top not in ("renderers", "generators"):
        base = stem
        for pat, fmt in TOOL_KIND:
            if pat.search(base):
                return fmt.format(words(pat.sub("", base)))
        return f"the {words(base)} tool"
    if top == "renderers" or (ext in ("js", "css", "html") and top not in ("data", "tools")):
        return f"the walkthrough's {words(stem.replace('-', ' '))} code"
    if top == "generators":
        return f"the {words(stem)} generator"
    if top == "assets" or ext in ("glb", "gltf", "ktx2", "bin"):
        if ext in ("jpg", "jpeg", "png", "webp", "gif", "tif", "tiff"):
            return f"the {words(stem.replace('-', ' '))} image"
        return f"the {words(stem.replace('-', ' '))} model"
    if top == "data" or ext in ("json", "jsonl", "csv", "geojson"):
        inner = [x for x in parts[1:-1] if x not in ("sidecars", "vectors", "traces")] if top == "data" else parts[:-1]
        if not ext and len(parts) >= 2:  # a folder: data/residents/
            return f"the {words(parts[-1])} data"
        if parts[:3] == ["data", "sources", "assets"] and len(parts) > 3:
            d = re.sub(r"_(\d{4})_(\d{2})_(\d{2})$", r" of \1-\2-\3", parts[3])
            return f"the source files for {words(d) if ' of ' not in d else d.replace('_', ' ')}"
        if stem in ("index", "schema", "README") or re.fullmatch(r"\d{4}", stem):
            label = " ".join(words(x) for x in ([stem] if re.fullmatch(r"\d{4}", stem) else []) + inner[-1:])
            return f"the {label or words(stem)} data"
        return f"the {words(stem.replace('-', ' '))} data"
    if ext in ("jpg", "jpeg", "png", "webp", "gif", "tif", "tiff"):
        return f"the {words(stem.replace('-', ' '))} image"
    if ext == "md":
        return f"the project's notes on {words(stem.replace('-', ' ')).lower()}"
    return f"the {words(stem.replace('-', ' '))} file"


def _work_phrase(numbers: list[int], own: int | None, possessive: bool = False) -> str:
    if own is not None and numbers and all(n == own for n in numbers):
        w = "this work"
    elif own is not None and numbers and all(n < own for n in numbers):
        w = "earlier work"
    elif own is not None and numbers and all(n > own for n in numbers):
        w = "later work"
    else:
        w = "other work"
    return w + ("'s" if possessive else "")


def _drop_refs_in_brackets(text: str, refs: list[str]) -> str:
    """A bracket whose ticket numbers were its point goes; the rest of a bracket stays."""
    def bracket(m):
        inner = m.group(1)
        if not REF.search(inner):
            return m.group(0)
        refs.extend(TICKET_NO.findall(inner))
        rest = REF.sub(" ", inner)
        rest = re.sub(r"\b(?:the\s+)?tickets?\b", " ", rest, flags=re.IGNORECASE)
        if FILLER.match(rest.strip()):
            return "\x00"  # the whole bracket was a label
        rest = re.sub(r"\s+", " ", rest)
        rest = re.sub(r"^[\s,;:·—–/&-]+|[\s,;:·—–/&-]+$", "", rest)
        rest = re.sub(r"^(?:(?:piece|stretch|part|item)\s+\d+[a-z]?\s+(?:of\s*)?)+", "", rest,
                      flags=re.IGNORECASE).strip(" ,;")
        rest = re.sub(r"\s*,\s*,\s*", ", ", rest)
        # "district draft; refined by" — the clause whose object was the ticket goes with it
        rest = re.sub(r"(?:[;,]\s*|\s+)?(?:\b[a-z]+ed\s+)?\b(?:by|under|in|from|of|see|per|via|after|before|since|until)"
                      r"(?:\s+(?:and|or|,))*\s*$", "", rest, flags=re.IGNORECASE).strip(" ,;")
        return f"({rest})" if rest and not FILLER.match(rest) else "\x00"
    out = re.sub(r"\(([^()]*)\)", bracket, text)
    out = re.sub(r"\s*\x00", "", out)
    return out


def rewrite(text: str, names: Names | None = None, own: int | None = None,
            liberties: dict[str, str] | None = None) -> tuple[str, list[str]]:
    """(the text as a reader gets it, the ticket ids it named, in order and once each)."""
    if not isinstance(text, str) or not text:
        return text, []
    refs: list[str] = []
    s = text

    # Links: the link's own host, which is what a reader would say.
    s = LINK.sub(lambda m: re.sub(r"^(?:https?://)?(?:www\.)?([^/\s)]+).*$", r"\1", m.group(0)).rstrip(".,;)")
                 + ("" if not m.group(0).endswith((".", ",", ";", ")")) else m.group(0)[-1]), s)

    # A markdown link is its words; a link into the project's files says which notes it is.
    s = re.sub(r"\[([^\]\n]+)\]\(([^)\s]+)\)",
               lambda m: m.group(1) + (f" ({path_words(m.group(2), names)})" if PATH.search(m.group(2)) else ""), s)

    # 1. tickets
    s = _drop_refs_in_brackets(s, refs)
    # A sentence that is nothing but tickets ("T-0795, amended T-1416.") was a dateline.
    def label(m):
        refs.extend(TICKET_NO.findall(m.group(0)))
        return ""
    s = SENTENCE_OF_REFS.sub(label, s)

    def run(m):
        frag = m.group(0)
        nums = [int(n) for n in TICKET_NO.findall(frag)]
        refs.extend(str(n).zfill(4) for n in nums)
        before = s_[:m.start()]
        after = s_[m.end():]
        if DETERMINER.search(before) and re.match(r"\s+[a-z]", after):
            return "\x01"  # "the T-1234 roster" → "the roster"
        poss = bool(re.match(r"['’]s\b", after))
        return "\x02" + _work_phrase(nums, own, poss) + "\x03"
    s_ = s
    s = REF_RUN.sub(run, s_)
    s = re.sub(r"\x02([^\x03]*)\x03['’]s\b", r"\1", s)  # possessive already in the phrase
    s = s.replace("\x02", "").replace("\x03", "")
    s = re.sub(r"\s*\x01\s*", " ", s)

    # 2. liberty cross-references, by title
    if liberties:
        def lib(m):
            lid = m.group(1)
            title = liberties.get(lid)
            return f"“{title}”" if title else m.group(0)
        s = re.sub(r"(?:\*\*)?\b(L(?:\d+[a-z]?|-[a-z0-9]+(?:-[a-z0-9]+)*))\b(?:\*\*)?(?!-)", lib, s)

    # A newspaper claim (`chicago_democrat_1834_03_04#c010`) is its paper: the claim number
    # is the register's index into the page, not a word for a reader.
    s = re.sub(r"`?\b([a-z0-9]+(?:_[a-z0-9]+)+)#c\d+\b`?",
               lambda m: (names.get(m.group(1)) if names is not None and names.get(m.group(1)) else m.group(1)), s)

    # 3. code spans and file paths
    def code(m):
        inner = m.group(1)
        new = _tokens(inner, names)
        if new != inner:
            return new
        return m.group(0)
    s = re.sub(r"`([^`\n]+)`", code, s)
    s = _tokens(s, names, prose=True)

    # 4. the machinery's words
    def tier_adj(m):
        art, kind, noun = m.group(1), SOURCE_KIND.get(m.group(2), "graded"), m.group(3)
        if kind.startswith(("a ", "an ")):
            out = f"{'an' if re.match(r'[aeiou]', noun) else 'a'} {noun} ({kind})"
        else:
            out = f"{'an' if re.match(r'[aeiou]', kind) else 'a'} {kind} {noun}"
        return out[0].upper() + out[1:] if art[0].isupper() else out
    s = re.sub(r"\b(an?|the)\s+tier[- ]?(\d)\s+([a-z][\w-]*)", tier_adj, s, flags=re.IGNORECASE)
    s = re.sub(r"\btier[- ]?(\d)\b", lambda m: SOURCE_KIND.get(m.group(1), "graded"), s, flags=re.IGNORECASE)
    s = re.sub(r"\b(three|two|four)-tier\b", r"\1-grade", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(attested|inferred|reconstructed|conjectural|documented|bottom|top|lowest|highest|lower|"
               r"higher|own|evidence|source|grade|confidence)(\s+|-)tier(s?)\b",
               lambda m: f"{m.group(1)}{m.group(2)}grade{m.group(3)}", s, flags=re.IGNORECASE)
    if re.search(r"\btiers?\b", s, re.IGNORECASE):
        s = re.sub(r"[^.!?]+[.!?]*", _tier_in_sentence, s)
    s = re.sub(r"\bROADMAP\s+(?:\*\*)?[A-Z]{1,3}\d+[a-z]?(?:\([a-z0-9]{1,3}\))?(?:\*\*)?", "the project's roadmap", s)
    s = re.sub(r"\b(?:the\s+)?(?:reconstruction\s+)?order[\s-]+books?\b",
               lambda m: ((m.group(0)[:3] + " ") if m.group(0).lower().startswith("the") else "") + "reconstruction plan", s,
               flags=re.IGNORECASE)
    s = re.sub(r"\btickets\b", "pieces of work", s, flags=re.IGNORECASE)
    s = re.sub(r"\bticket\b", "piece of work", s, flags=re.IGNORECASE)

    s = _tidy(s, text)
    seen, ordered = set(), []
    for r in refs:
        r = f"T-{int(r):04d}"
        if r not in seen:
            seen.add(r)
            ordered.append(r)
    return s, ordered


PLAT_WORDS = re.compile(r"\b(?:blocks?|lots?|plat\w*|streets?|section|division|alley|madison|monroe|"
                        r"washington|randolph|lake|south water|kinzie|state|clark|wells|market|franklin)\b",
                        re.IGNORECASE)


def _tier_in_sentence(m) -> str:
    """A tier of blocks is a row; any other tier in this prose is a grade of evidence."""
    sent = m.group(0)
    plat = bool(PLAT_WORDS.search(sent))
    sent = re.sub(r"\btiers\b", "rows" if plat else "grades", sent, flags=re.IGNORECASE)
    return re.sub(r"\btier\b", "row" if plat else "grade", sent, flags=re.IGNORECASE)


def _tokens(s: str, names: Names | None, prose: bool = False) -> str:
    """Paths, then ids, in a run of text."""
    s = PATH.sub(lambda m: _path_keep_punct(m.group(0), names), s)

    def snake(m):
        tok = m.group(0)
        return _name(tok, names)
    # a dotted id (`glessner_house.as_built_1887.form.bay_dining_elevation`) as one thing
    s = re.sub(r"\b[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+(?:\.[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*)+\b",
               lambda m: _dotted(m.group(0), names), s)
    s = SNAKE.sub(snake, s)
    return s


def _path_keep_punct(raw: str, names: Names | None) -> str:
    tail = ""
    while raw and raw[-1] in ".,;:)]}'\"`":
        tail = raw[-1] + tail
        raw = raw[:-1]
    if "(" in raw and ")" not in raw:
        tail = ""  # keep balanced
    return path_words(raw, names) + tail


def _name(tok: str, names: Names | None) -> str:
    if names is not None:
        hit = names.get(tok)
        if hit:
            return hit
    m = re.fullmatch(r"e(\d{4})_([a-z0-9_]+)", tok)
    if m:
        return f"the {m.group(1)} {words(m.group(2))} ground"
    m = re.fullmatch(r"blk_([a-z0-9_]+)", tok)
    if m:
        return f"the {words(m.group(1)).title()} block"
    m = re.fullmatch(r"hh_(?:rc_|inf_|ll_)?([a-z]+)_([a-z0-9_]+)", tok)
    if m:
        return f"the {m.group(1).capitalize()} household"
    m = re.fullmatch(r"z\d{2}_([a-z0-9_]+)", tok)
    if m:
        return f"the {words(m.group(1))} zone"
    # A newspaper's issue (`chicago_democrat_1834_11_12`) is the paper and its date.
    m = re.fullmatch(r"([a-z]+(?:_[a-z]+)*)_(1[78]\d\d)_(\d\d)_(\d\d)", tok)
    if m:
        paper = " ".join(w.capitalize() for w in m.group(1).split("_"))
        return f"the {paper} of {m.group(2)}-{m.group(3)}-{m.group(4)}"
    # an id that embeds a ticket number (`T2769_1965_neutrals`) keeps the rest of its words
    return words("_".join(x for x in tok.split("_") if not re.fullmatch(r"(?:T|NAV|PR)\d{2,5}", x)) or tok)


def _dotted(tok: str, names: Names | None) -> str:
    segs = tok.split(".")
    if segs[0] == "terrain" and len(segs) >= 3:
        segs = segs[1:]
    head = segs[0]
    if names is not None and names.get(head):
        rest = [s for s in segs[1:] if s not in ("form",) and not re.fullmatch(
            r"(?:as_built|as_mapped|as_standing|draft|documented|inferred|restored|first_fort|frame|log|works|camp|shed|yard|crossing)_\d{4}|[a-z]+_\d{4}", s)]
        return " ".join([names.get(head)] + [words(x) for x in rest]).strip()
    return " ".join(_name(x, names) if "_" in x else words(x) for x in segs if x not in ("form",))


def _tidy(s: str, original: str) -> str:
    s = re.sub(r"\*\*\s*\*\*", "", s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\s+([,.;:)])", r"\1", s)
    s = re.sub(r"\(\s+", "(", s)
    s = re.sub(r",\s*,", ",", s)
    s = re.sub(r"([,;:])\s*([.;])", r"\2", s)
    s = re.sub(r"—\s*—", "—", s)
    s = re.sub(r"(?:^|(?<=[.!?]\s))(earlier|later|other|this) work\b", lambda m: m.group(0)[0].upper() + m.group(0)[1:], s)
    # "block 20 (block 20)": a name and its id said twice once the id is a name
    s = re.sub(r"\b([\w’'][\w’' ]{2,60}?) \(\1\)", r"\1", s)
    s = re.sub(r"^\s*[,;:—–]\s*", "", s)
    return s.strip() if original.strip() == original else s


# The fields of each compiled sidecar a renderer prints (js/ground.js, js/exclusions.js,
# js/citations.js): compile_scene.py rewrites exactly these, and check_visitor_ui.py lints
# exactly these, so the gate reads what the page shows. Ids, keys and grades are not here.
CITATION_PATHS = ("citation", "tier_label", "what_it_supplies[]", "what_it_does_not_supply[]",
                  "transcribes[].work")
SIDECAR_PATHS = {
    "terrain.json": ["scope", "standard", "context[].label", "context[].text", "not_modelled[].why",
                     "claims[].label", "claims[].group", "claims[].fields[].value", "claims[].notes[]"]
                    + [f"claims[].citations[].{c}" for c in CITATION_PATHS],
    "exclusions.json": ["standard", "uncertain_standard", "excluded[].name", "excluded[].reason",
                        "excluded[].detail", "uncertain[].name", "uncertain[].question",
                        "uncertain[].consequence", "uncertain[].no_source_record",
                        "uncertain[].carried_by_label", "uncertain[].dossier.label",
                        "uncertain[].dossier.anchor"]
                       + [f"{k}[].citations[].{c}" for k in ("excluded", "uncertain") for c in CITATION_PATHS],
}


# The order book's sentences js/orderbook.js prints (build_order_book_1835.py rewrites them,
# check_visitor_ui.py reads them), and the completion audit's (audit_town_completion_1835.py).
ORDER_BOOK_PATHS = ["bucket_families[].title", "bucket_families[].lead",
                    "seats_against_roofs.statement", "seats_against_roofs.what_the_slots_wait_on",
                    "seats_against_roofs.what_is_left", "seats_against_roofs.passes[].title",
                    "seats_against_roofs.requested_slots[].name",
                    "seats_against_roofs.requested_slots[].family",
                    "programme_deltas[].statement", "invariants[].statement", "invariants[].measured_now"]
# The town census's sentences js/census.js shows (as a tile's hover text).
CENSUS_PATHS = ["buildings.basis", "buildings.dwellings.question", "buildings.dwellings.basis",
                "people.split.basis", "people.basis", "people.waiting_note", "people.scene.question",
                "people.scene.basis", "people.scene.population.question", "people.scene.population.basis",
                "people.scene.target_note", "people.scene.target_method", "beyond_the_index.why_apart"]
COMPLETION_PATHS = ["joins[].label", "joins[].what_keeps_it_open", "not_a_remedy"]


def strings_at(doc, paths):
    """(where, text) for every string at `paths` in `doc`, without changing it."""
    def walk(node, steps, where):
        if not steps or not isinstance(node, dict):
            return
        step, rest = steps[0], steps[1:]
        many = step.endswith("[]")
        key = step[:-2] if many else step
        if key not in node:
            return
        val = node[key]
        items = list(enumerate(val)) if many and isinstance(val, list) else ([(None, val)] if not many else [])
        for i, item in items:
            w = f"{where}{key}" + (f"[{i}]" if i is not None else "")
            if rest:
                yield from walk(item, rest, w + ".")
            elif isinstance(item, str) and item.strip():
                yield w, item
    for path in paths:
        yield from walk(doc, path.split("."), "")


def rewrite_paths(doc, paths, names: Names | None = None, liberties: dict | None = None,
                  refs_key: str = "work_refs"):
    """Rewrite, in place, every string a compiled document shows a reader.

    `paths` are the fields a renderer prints, written `claims[].notes[]`,
    `context[].text`, `scope`: a `[]` step walks a list, a name steps into a dict. The
    ticket numbers a string named go onto the record its path starts at (the item of the
    first list walked, or the document itself) as `refs_key`, once each, in order — the
    shape Researcher mode can link from, and never a sentence. Returns the strings
    rewritten, as (where, text), so a gate can lint exactly what was rewritten."""
    out = []

    def walk(node, steps, where, owner):
        if not steps:
            return
        step, rest = steps[0], steps[1:]
        many = step.endswith("[]")
        key = step[:-2] if many else step
        if not isinstance(node, dict) or key not in node:
            return
        val = node[key]
        if many:
            if not isinstance(val, list):
                return
            for i, item in enumerate(val):
                own = owner if owner is not None else (item if isinstance(item, dict) else None)
                if rest:
                    walk(item, rest, f"{where}{key}[{i}].", own)
                elif isinstance(item, str):
                    val[i] = _one(item, own, f"{where}{key}[{i}]")
        elif rest:
            walk(val, rest, f"{where}{key}.", owner)
        elif isinstance(val, str):
            node[key] = _one(val, owner if owner is not None else node, f"{where}{key}")

    def _one(text, owner, where):
        new, refs = rewrite(text, names, liberties=liberties)
        if refs and isinstance(owner, dict):
            have = owner.setdefault(refs_key, [])
            have.extend(r for r in refs if r not in have)
        out.append((where, new))
        return new

    for path in paths:
        walk(doc, path.split("."), "", None)
    return out


# ------------------------------------------------------------------- building names
#
# The owner's naming ruling of 2026-08-18 ("give the locations useful names not technical
# D3 #03 names") reached the anonymous roofs (js/display-name.js) and stopped at the named
# ones: 146 of the 1904 Prairie Avenue records are named with the production step they were
# built in — "…, K01 frontage assembly", "(district draft; refined by T-1908)", "Buckingham
# map-led corner mansion", "its massing read off J. W. Taylor's c. 1895 photograph". Those
# are a builder's notes on how the model was made, not a name the house was known by. The
# card, the target tag and Go to say the name with them taken off, and nothing else changes:
# every word left is the record's own.

PRODUCTION_BRACKET = re.compile(
    r"\s*\((?:[^()]*\b(?:draft|refined|T-\d{2,5})\b[^()]*)\)", re.IGNORECASE)
PRODUCTION_TAIL = re.compile(r",\s*(?:its\s+massing\s+read\s+off|K\d{2}\b)[^,()]*$", re.IGNORECASE)
PRODUCTION_WORDS = re.compile(r"\b(?:map-led|traced)\s+|\bthe\s+K\d{2}\s+(?=\w)|\bK\d{2}\s+(?=\w)",
                              re.IGNORECASE)
SEEN_IN = re.compile(r"^(.*?—\s*)([A-Z][\w'’.-]+)\s+partly seen in\b.*$")
# What reads as the production step in a name, so the gate can refuse one that slipped by.
NAME_MACHINERY = re.compile(r"\b(?:map-led|frontage assembly|district draft|refined by|K\d{2}|"
                            r"massing read off|partly seen in)\b", re.IGNORECASE)


def plain_name(name: str) -> str:
    """A building's name without the production step it was modelled in.

    Only removes: a bracket naming a draft, a refinement or a ticket; a trailing ", K01 …"
    kit clause or ", its massing read off …" clause; the words "map-led" and "traced"; a
    kit code before a noun ("the K16 timber house" → "the timber house"); and "partly seen
    in <a photograph>", which leaves the family's name as the house's ("Roloson" → "the
    Roloson house"). A name with none of those is returned as it is."""
    n = str(name or "")
    if not NAME_MACHINERY.search(n) and not PRODUCTION_BRACKET.search(n) and "traced" not in n:
        return n
    m = SEEN_IN.match(n)
    if m:
        n = f"{m.group(1)}the {m.group(2)} house"
    n = PRODUCTION_BRACKET.sub("", n)
    n = PRODUCTION_TAIL.sub("", n)
    n = PRODUCTION_WORDS.sub(lambda m: "the " if m.group(0).lower().startswith("the ") else "", n)
    return re.sub(r"\s{2,}", " ", n).strip(" ,;")


# ------------------------------------------------------------------- the reader's overlay
#
# Some records a person opens are read by the page straight from the files they are authored
# in, with no compile step between: the plant and wildlife communities, the household records
# behind a person's card, a firm's record, a building's sidecar. Their prose is the builders'
# and stays as written; what a reader gets is the same rewrite every other surface gets,
# applied by the page as it renders, from an overlay compile_reader_text.py writes. The
# overlay is keyed by each original string's CRC-32 and UTF-8 length, and holds the edits
# that turn it into the reader's sentence: `[start, delete, insert]`, in UTF-16 code units
# (a JavaScript string's own indices), in order. js/reader-text.js applies it; reader_copy()
# below is its twin, so check_visitor_ui.py lints exactly what the page shows.

# Spelt out, not `\s`: Python's and JavaScript's whitespace classes differ at the edges,
# and js/reader-text.js holds this same class, so both call the same strings prose.
_WS = " \t\n\r\f\v\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
PROSE = re.compile(f"[^{_WS}][{_WS}]+[^{_WS}]")


def is_prose(value) -> bool:
    """A string a person reads as words: two of them at least. An id, a grade, a date or a
    key is one token, and is the data's, never the overlay's."""
    return isinstance(value, str) and bool(PROSE.search(value))


def reader_key(text: str) -> str:
    raw = text.encode("utf-8")
    return f"{zlib.crc32(raw):08x}:{len(raw):x}"


def prose_strings(doc):
    """Every prose string in a document, values only, depth first."""
    if isinstance(doc, dict):
        for v in doc.values():
            yield from prose_strings(v)
    elif isinstance(doc, list):
        for v in doc:
            yield from prose_strings(v)
    elif is_prose(doc):
        yield doc


TOKEN = re.compile(r"\w+|\s+|[^\w\s]")


def _u16(s: str, i: int) -> int:
    return len(s[:i].encode("utf-16-le")) // 2


def _myers(a: list, b: list) -> list:
    """The shortest edit script from `a` to `b` (Myers, O((N+M)D)): one op per token, in
    order — "=" kept, "-" deleted from `a`, "+" inserted from `b`. A rewrite changes a few
    words in a long sentence, so D is small and this is fast where a quadratic matcher
    is not."""
    n, m = len(a), len(b)
    v = {1: 0}
    trace = []
    for d in range(n + m + 1):
        trace.append(dict(v))
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                x = v.get(k + 1, 0)
            else:
                x = v.get(k - 1, 0) + 1
            y = x - k
            while x < n and y < m and a[x] == b[y]:
                x, y = x + 1, y + 1
            v[k] = x
            if x >= n and y >= m:
                ops = []
                for dd in range(d, 0, -1):
                    vv = trace[dd]
                    kk = x - y
                    if kk == -dd or (kk != dd and vv.get(kk - 1, -1) < vv.get(kk + 1, -1)):
                        pk = kk + 1
                    else:
                        pk = kk - 1
                    px = vv.get(pk, 0)
                    py = px - pk
                    while x > px and y > py:
                        ops.append("=")
                        x, y = x - 1, y - 1
                    ops.append("+" if x == px else "-")
                    x, y = px, py
                ops.extend("=" * x)
                return ops[::-1]
    return []


def edits_between(old: str, new: str) -> list:
    """The `[start, delete, insert]` edits that turn `old` into `new`, word by word."""
    a, b = TOKEN.findall(old), TOKEN.findall(new)
    out, i, j, pos = [], 0, 0, 0
    for op in _myers(a, b):
        if op == "=":
            pos += len(a[i])
            i, j = i + 1, j + 1
            continue
        if not out or out[-1][0] + out[-1][1] != pos:
            out.append([pos, 0, ""])
        if op == "-":
            out[-1][1] += len(a[i])
            pos += len(a[i])
            i += 1
        else:
            out[-1][2] += b[j]
            j += 1
    if any(ord(c) > 0xFFFF for c in old):
        out = [[_u16(old, s), _u16(old, s + d) - _u16(old, s), ins] for s, d, ins in out]
    return out


def apply_edits(old: str, edits) -> str:
    """The twin of js/reader-text.js `applyEdits`, in UTF-16 code units."""
    u = old.encode("utf-16-le")
    out, pos = [], 0
    for start, delete, insert in edits:
        out.append(u[pos * 2:start * 2].decode("utf-16-le"))
        out.append(insert)
        pos = start + delete
    out.append(u[pos * 2:].decode("utf-16-le"))
    return "".join(out)


def reader_copy(doc, overlay: dict):
    """`doc` as the page renders it: every prose string the overlay holds, rewritten."""
    if isinstance(doc, dict):
        return {k: reader_copy(v, overlay) for k, v in doc.items()}
    if isinstance(doc, list):
        return [reader_copy(v, overlay) for v in doc]
    if is_prose(doc):
        e = overlay.get(reader_key(doc))
        if e is not None:
            return apply_edits(doc, e)
    return doc


def problems(text: str) -> list[str]:
    """What is left in a rewritten string that a reader must not get."""
    found = list(lint_string(text))
    for m in re.finditer(r"\b(?:tiers?|tickets?|order[\s-]+books?)\b", text, re.IGNORECASE):
        found.append(f"the word `{m.group(0)}`")
    return found


# ------------------------------------------------------------------- self-test

def self_test() -> int:
    fails = []

    def expect(cond, what):
        print(f"   {'ok  ' if cond else 'FAIL'} {what}")
        if not cond:
            fails.append(what)

    names = Names(extra={"recon_x_001": "a one-room frame cottage", "src_plat": "Wright's survey of 1834"})
    libs = {"L5": "Sauganash Hotel: both outlines are invented", "L-jaunt-pilot": "The first walk"}

    def rw(t, own=None):
        return rewrite(t, names, own=own, liberties=libs)

    t, r = rw("2026-09-29 (T-1460) — both tokens are removed.")
    expect(t == "2026-09-29 — both tokens are removed." and r == ["T-1460"], f"a ticket that was a label is dropped ({t!r})")
    t, r = rw("T-0795 had walked the whole sheet.", own=1460)
    expect(t == "Earlier work had walked the whole sheet." and r == ["T-0795"], f"a ticket in the sentence is earlier work ({t!r})")
    t, _ = rw("since T-1815 every stoop is drawn", own=1460)
    expect(t == "since later work every stoop is drawn", f"…or later work ({t!r})")
    t, _ = rw("T-0987's second pass read it.", own=987)
    expect(t == "This work's second pass read it.", f"a possessive keeps its grammar ({t!r})")
    t, r = rw("the tickets **T-1529**, **T-1525** and **T-1418** left it open.", own=2000)
    expect(t == "Earlier work left it open.", f"a run of tickets is one phrase ({t!r})")
    expect(r == ["T-1529", "T-1525", "T-1418"], f"…and every one is kept as a reference ({r})")
    t, _ = rw("the T-1234 roster stands.")
    expect(t == "the roster stands.", f"a ticket used as an adjective goes ({t!r})")
    t, _ = rw("(T-2310, piece 2 of T-1851)")
    expect(t == "", f"a bracket of nothing but tickets goes whole ({t!r})")
    t, _ = rw("(T-1460, p. 3)")
    expect(t == "(p. 3)", f"a bracket keeps what is not a ticket ({t!r})")
    t, _ = rw("See **L5** and L-jaunt-pilot.")
    expect("“Sauganash Hotel: both outlines are invented”" in t and "“The first walk”" in t, f"a liberty is named by title ({t!r})")
    t, _ = rw("against `recon_x_001` and src_plat.")
    expect(t == "against a one-room frame cottage and Wright's survey of 1834.", f"an id becomes its name ({t!r})")
    t, _ = rw("read from `data/streets/1835.json` by `tools/generate_block_infill.py`.")
    expect(t == "read from the 1835 streets data by the block infill generator.", f"a path becomes what the file is ({t!r})")
    t, _ = rw("see `docs/RESEARCH/k01-1623-farwell-2433/README.md`.")
    expect(t == "see the research notes on 1623 farwell.", f"a research folder is its topic ({t!r})")
    t, _ = rw("the `roof_pitch_deg` and `WORKED_SHARE`.")
    expect(t == "the roof pitch (deg) and worked share.", f"an unnamed id is its words ({t!r})")
    t, _ = rw("a tier-5 lithograph, three-tier vocabulary, the platted tier, its own ticket, the order book")
    expect(not problems(t), f"the machinery's words are the reader's ({t!r})")
    t, _ = rw("`glessner_house.as_built_1887.form.bay_dining_elevation`")
    expect(not problems(t), f"a claim token is words ({t!r})")
    t, _ = rw("the stable (district draft; refined by T-1932) stands.")
    expect(t == "the stable (district draft) stands.", f"a clause whose object was a ticket goes with it ({t!r})")
    t, _ = rw("[Sources and validation](docs/RESEARCH/glessner-porte-cochere/README.md).")
    expect(t == "Sources and validation (the research notes on glessner porte cochere).", f"a markdown link is its words ({t!r})")
    n2 = Names(root=Path("/nonexistent"), extra={"stable_x": "1616 Prairie (district draft; refined by T-1932)"})
    expect(n2.get("stable_x") == "1616 Prairie (district draft)", f"a name is said without its tickets ({n2.get('stable_x')!r})")
    t, _ = rw("the owner's T-1755 question, and **six dwellings**, one to a lot.")
    expect(t == "the owner's question, and **six dwellings**, one to a lot.", f"bold survives and a possessive determiner drops the ticket ({t!r})")
    t, _ = rw("the Madison–Monroe tier the state sold. A tier 1 source and its tier.")
    expect(t == "the Madison–Monroe row the state sold. A first-hand source and its grade.", f"a tier of blocks is a row ({t!r})")
    t, r = rw("T-0795, amended T-1416. The slough. RE-ROUTED BY T-1500: east.")
    expect(t == "The slough. RE-ROUTED BY other work: east." and r == ["T-0795", "T-1416", "T-1500"],
           f"a sentence of nothing but tickets is a dateline and goes ({t!r})")
    t, _ = rw("Franklin Street is the reading taken, at the inferred tier.")
    expect(t == "Franklin Street is the reading taken, at the inferred grade.", f"a grade's tier is a grade, beside a street too ({t!r})")
    t, _ = rw("Contradicted by chicago_democrat_1834_03_04#c010 (notice).")
    expect("#c010" not in t and not problems(t), f"a newspaper claim is its paper ({t!r})")
    t, _ = rw("A plain sentence, with nothing to do.")
    expect(t == "A plain sentence, with nothing to do.", "a clean sentence is untouched")
    cit = "Wright, J. S. Chicago: Map of the Town and its Additions. New York, 1834; see data/x.json."
    expect(source_title(cit) == "Wright, J. S. Chicago: Map of the Town and its Additions",
           f"a source title is its citation's opening words ({source_title(cit)!r})")
    expect(structure_title("Reconstructed D3 one-room frame cottage #017", "x") == "a one-room frame cottage",
           "an anonymous roof is said as what it is")
    # T-2825, second half: the names, the bare ids, and the overlay the page applies.
    t, _ = rw("named in the claim read as chicago_democrat_1834_11_12#c004, and hh_rc_bacon_betsey.")
    expect(t == "named in the claim read as the Chicago Democrat of 1834-11-12, and the Bacon household.",
           f"a newspaper issue is its paper and date, a reconstructed household its family ({t!r})")
    t, _ = rw("added for ROADMAP K49(c) so it reads")
    expect(t == "added for the project's roadmap so it reads", f"a roadmap item's clause goes with it ({t!r})")
    for name, plain in [
        ("1600 Prairie Avenue — brick corner house, K01 frontage assembly", "1600 Prairie Avenue — brick corner house"),
        ("1945 Prairie Avenue — George Armour/Corwith corner mansion (district draft; refined by T-1908)",
         "1945 Prairie Avenue — George Armour/Corwith corner mansion"),
        ("2036 Prairie Avenue — Buckingham map-led corner mansion", "2036 Prairie Avenue — Buckingham corner mansion"),
        ("Shortall-Gregory house (1638 Prairie Avenue): the K16 timber house",
         "Shortall-Gregory house (1638 Prairie Avenue): the timber house"),
        ("2109 Prairie Avenue — Roloson partly seen in Armour photograph", "2109 Prairie Avenue — the Roloson house"),
        ("1635 Prairie Avenue — Italianate villa of 1863 (the Forsyth house)",
         "1635 Prairie Avenue — Italianate villa of 1863 (the Forsyth house)"),
        ("Green Tree Tavern", "Green Tree Tavern")]:
        expect(plain_name(name) == plain, f"a building's name without its production step ({plain_name(name)!r})")
    note = "Seated by T-1433; see data/streets/1835.json and fort_dearborn_barracks — 𝄞 é."
    new, _ = rewrite(note, Names(root=Path("/nonexistent"), extra={"fort_dearborn_barracks": "the barracks"}))
    e = edits_between(note, new)
    expect(apply_edits(note, e) == new and not problems(new), f"the overlay's edits make the reader's sentence ({new!r})")
    expect(reader_copy({"a": [note, "one_token"]}, {reader_key(note): e}) == {"a": [new, "one_token"]},
           "the page's step: a sentence is said, a bare id is the data's and is left alone")
    print(f"   {len(fails)} rewrite(s) not made" if fails else "   every rewrite made")
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test", action="store_true")
    g.add_argument("--show")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    text, refs = rewrite(a.show, Names())
    print(text)
    print("refs:", refs, "problems:", problems(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
