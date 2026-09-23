#!/usr/bin/env python3
"""The 1833-1835 newspaper corpus, made citable — build it, and gate it.

    tools/newspaper_corpus.py --build [--deposit PATH]   rebuild corpus.json + derived text
    tools/newspaper_corpus.py --check                    the gate (runs without the deposit)
    tools/newspaper_corpus.py --self-test                the gate's assertions still fire

WHAT THIS IS FOR. `chicago/reference/newspapers/Transcriptions/` holds the owner's
archival deposit: 86 issues of the Chicago Democrat (1833-11-26 to 1835-08-26) and
the Chicago American (1835-06-08 to 1835-08-29), transcribed under the methodology
in that folder's own `Newspaper_Transcription_Workflow.md`. The scene date sits
inside both runs and a Democrat was PRINTED on 1835-07-01. Until now nothing in
this project could resolve a citation into that deposit, so nothing could be cited
out of it. `data/research/newspapers/corpus.json` is that resolver, and every later
ticket in the PAPERS epic resolves against it.

THE DEPOSIT IS ON `main`, THIS SUBTREE IS DEVELOPED ON `dev`. The transcriptions
were committed to `main` on 2026-08-28 and have not been back-merged; a `dev`
checkout has `chicago/reference/` WITHOUT `newspapers/`. That is not a defect in
this tool and it must not be papered over, so the deposit is handled as three
states rather than two:

  present   — every reference path is resolved, file by file, and a missing one FAILS.
  absent    — the whole `newspapers/` subtree is missing, which is what `dev` looks
              like today. Derived text is still fully checked; the reference tier is
              reported as unresolvable-here and the gate stays green.
  partial   — the subtree exists and a file named by the corpus does not. FAILS,
              always. This is the state that means damage, and it is the reason the
              absent case is tested wholesale rather than per-file.

Merging `main` into `dev` today is NOT the fix: main carries sixty Finder-duplicate
`... 2.json`/`... 2.glb` files under `site/chicago/4d/data/`, and merging it turns
this repo's gate red in twenty-three places. T-0275 carries that.

DERIVED TEXT. Twenty-three of the deposit's transcriptions exist only as .docx —
the entire American run, the Democrat's 1835 tail, and three alternate witnesses.
`tools/docx_text.py` extracts them, deterministically and with the standard library
alone, to `data/research/newspapers/text/`. Those files are COMMITTED, which is
what makes an American citation resolvable on a branch that has no deposit. The
sixty-six issues that already carry a committed .txt are NOT copied: they are cited
at their archival path, per the ticket, and re-copying them would put a second,
divergeable transcript of the same issue in the repo.

`data/research/` IS RESEARCH, NOT PAYLOAD. `tools/publish.sh` copies named
subdirectories of `data/` and this is not one of them; the gate asserts that
nothing under `data/research/` has reached `site/chicago/4d/`, so the corpus can
grow without touching the 14 MB the walkthrough actually ships.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # chicago/4d
REPO = ROOT.parent.parent                              # repo root
DEPOSIT = REPO / "chicago" / "reference" / "newspapers" / "Transcriptions"
RESEARCH = ROOT / "data" / "research" / "newspapers"
CORPUS = RESEARCH / "corpus.json"
TEXT = RESEARCH / "text"
SITE = REPO / "site" / "chicago" / "4d"

SCHEMA_VERSION = 1

PUBLICATIONS = {
    "chicago_democrat": {
        "title": "The Chicago Democrat",
        "source_id": "chicago_democrat_1833_1835",
        "set_dir": "Chicago_Democrat_1833-11_to_1835-08",
        "file_prefix": "Chicago_Democrat_",
    },
    "chicago_american": {
        "title": "The Chicago American",
        "source_id": "chicago_american_1835",
        "set_dir": "Chicago_American_1835-06_to_1835-08",
        "file_prefix": "Chicago_American_",
    },
}

# The one artifact in the deposit whose filename carries no issue date. It is
# attached to 1833-11-26 as an ALTERNATE witness, and T-0276 settled the
# attachment on 2026-08-28 against the extent of the owner's scan holdings.
# Both of the artifact's own non-dates survive on the record, unrepaired.
UNDATED = {
    "Chicago_Democrat_1833_11-16-Verified_Transcription.docx": {
        "attach_to": "1833-11-26",
        "confidence": "documented",
        "note": (
            "SETTLED 2026-08-28 by the owner's ruling under T-0276, recorded verbatim: "
            "\"NOV. 26 is the first issue date I have scanned.\" The deposit's scan "
            "holdings begin at Vol. I No. 1, so there is no earlier 1833 Democrat scan "
            "set for this transcription to be a reading of. It is headed 'Best-effort "
            "verified reading transcription of the three supplied scan pages', and the "
            "three-image set is the one data/sources/chicago_democrat_1833_11_26.json "
            "describes and was verified against. The attachment is therefore documented "
            "by elimination against the deposit, not inferred from the heading alone. "
            "TWO NON-DATES SURVIVE ON THIS ARTIFACT AND ARE PRESERVED, NOT REPAIRED, per "
            "the corpus workflow's rule 2.3 ('Do not silently repair a visibly printed "
            "date or number; note the discrepancy'): the filename's '11-16', and the "
            "transcription's own first-page line 'Visible date at the top of this "
            "supplied page: NOV. 19, 1833'. The Democrat published under neither date. "
            "Both are artifacts of the transcription and its naming, not readings of "
            "1830s type, and neither may be cited as evidence that any such issue "
            "existed. NOTE THE LIMIT OF THE RULING: it establishes where the scan "
            "holdings START, and nobody re-opened the page images to re-read that "
            "masthead — so the NOV. 19 line stands quarantined and unexplained rather "
            "than corrected, and a scan read would still outrank everything here."
        ),
    }
}

# Manifest columns differ across the three delivery batches, so each is mapped
# rather than guessed at. Keys are the manifest filename stem.
MANIFEST_COLUMNS = {
    "date": ("date", "printed_date"),
    "volume": ("volume",),
    "number": ("issue_number", "number"),
    "word_count": ("word_count",),
    "uncertainty_markers": ("uncertainty_markers",),
    "completeness": ("scan_status",),
    "notes": ("notes",),
}

FNAME = re.compile(
    r"^(?P<prefix>Chicago_(?:Democrat|American))_"
    r"(?P<date>\d{4}-\d{2}-\d{2})_"
    r"(?P<vol>Vol[I0-9]+|Extra)?_?"
    r"(?P<num>No\d+)?_?"
    r"(?P<tail>.*)\.docx$"
)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# A deposit given with --deposit may sit outside the repo (it lives on `main`,
# so verifying the deposit-present branch of the gate means pointing this at a
# checkout of it). Paths are always RECORDED at their canonical repo-relative
# home, never where they happened to be read from, or corpus.json would carry a
# machine's temp directory.
DEPOSIT_ACTUAL = DEPOSIT


def rel(path):
    path = Path(path)
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        pass
    try:
        return (DEPOSIT.relative_to(REPO) / path.relative_to(DEPOSIT_ACTUAL)).as_posix()
    except ValueError:
        raise ValueError("%s is neither in the repo nor under the deposit root" % path)


def issue_id(pub, iso):
    return "%s_%s" % (pub, iso.replace("-", "_"))


# --------------------------------------------------------------------------
# build


def read_manifests(set_dir):
    """{iso date: {field: value}} from every *_Issue_Manifest.csv in a set."""
    rows = {}
    for csv_path in sorted(set_dir.glob("*_Issue_Manifest.csv")):
        with open(csv_path, newline="", encoding="utf-8-sig") as fh:
            for raw in csv.DictReader(fh):
                out = {"manifest": rel(csv_path)}
                for field, candidates in MANIFEST_COLUMNS.items():
                    for c in candidates:
                        if raw.get(c) not in (None, ""):
                            out[field] = raw[c].strip()
                            break
                iso = out.get("date")
                if iso:
                    rows[iso] = out
    return rows


def artifact_role(name, tail):
    """primary, or alternate. A '-2' is a SEPARATE OCR rebuild, not a duplicate.

    Checked by reading both: the 1835-07-01 pair are built from different source
    PDFs (`Jan1835-Jul1835.pdf` pages 33-36 against `Jul1835.pdf` pages 1-4) and
    the '-2' text is markedly poorer. Where an issue has both, the reconciled
    transcription is primary; where '-2' is all there is — 1835-07-15 — it is the
    primary and the record says so.
    """
    return "alternate" if tail.endswith("-2") else "primary"


def build(deposit):
    global DEPOSIT_ACTUAL
    DEPOSIT_ACTUAL = deposit.resolve()
    deposit = DEPOSIT_ACTUAL
    if not deposit.exists():
        sys.exit("no deposit at %s — --build needs the archival transcriptions "
                 "(they are on `main`; see this file's header)" % deposit)
    TEXT.mkdir(parents=True, exist_ok=True)
    for stale in TEXT.glob("*.txt"):
        stale.unlink()

    sys.path.insert(0, str(ROOT / "tools"))
    import docx_text

    issues = {}
    for pub, meta in sorted(PUBLICATIONS.items()):
        set_dir = deposit / meta["set_dir"]
        manifests = read_manifests(set_dir)
        for docx in sorted(set_dir.glob("*.docx")):
            m = FNAME.match(docx.name)
            if m:
                iso, vol, num = m.group("date"), m.group("vol"), m.group("num")
                tail, role = m.group("tail"), artifact_role(docx.name, m.group("tail"))
                undated_note = None
            elif docx.name in UNDATED:
                spec = UNDATED[docx.name]
                iso, vol, num, tail, role = spec["attach_to"], None, None, "verified", "alternate"
                undated_note = spec
            else:
                sys.exit("unrecognised deposit filename: %s" % docx.name)

            key = issue_id(pub, iso)
            entry = issues.setdefault(key, {
                "id": key,
                "publication": pub,
                "source_id": meta["source_id"],
                "date": iso,
                "volume": None,
                "number": None,
                "artifacts": [],
            })
            art = {
                "_vol": None if vol in (None, "Extra") else vol.replace("Vol", ""),
                "_num": "Extra" if vol == "Extra" else ((num or "").replace("No", "") or None),
                "role": role,
                "format": "docx",
                "path": rel(docx),
                "path_kind": "deposit",
                "sha256": sha256(docx),
            }
            # The companion .txt, when the deposit carries one, is the readable
            # form and is cited where it lies. When it does not, the text is
            # derived here and committed.
            txt = docx.with_suffix(".txt")
            if txt.exists():
                art["text_path"] = rel(txt)
                art["text_path_kind"] = "deposit"
                art["text_sha256"] = sha256(txt)
            else:
                # Deferred: the file is named after its ROLE, and a role is not
                # final until the issue's whole set is in hand. 1835-07-15 is
                # why — its only artifact is a `-2`, so it reads as an alternate
                # right up until it is promoted for want of anything else.
                art["_derive_from"] = docx
                art["_tail"] = tail
                art["text_path_kind"] = "derived"
            if undated_note:
                art["identification"] = undated_note["confidence"]
                art["identification_note"] = undated_note["note"]
            entry["artifacts"].append(art)

            row = manifests.get(iso)
            if row and role == "primary":
                entry["manifest"] = row["manifest"]
                for f in ("word_count", "uncertainty_markers", "notes"):
                    if row.get(f):
                        entry[f] = int(row[f]) if f.endswith("count") or f.endswith("markers") else row[f]
                entry["completeness"] = (row.get("completeness") or "").lower() or None

        # A batch's validation notes cover exactly the issues its OWN manifest
        # lists. Matching on the year instead would hang the Jan-Jul 1835 notes
        # on the August tail, which they do not describe and were not written
        # against — the tail arrived in a later delivery with no notes at all.
        for e in issues.values():
            man = e.get("manifest")
            if not man:
                continue
            notes = REPO / man.replace("_Issue_Manifest.csv", "_Validation_Notes.md")
            if _read(rel(notes)).exists():
                e["validation_notes"] = rel(notes)

    for e in issues.values():
        prim = [a for a in e["artifacts"] if a["role"] == "primary"]
        if not prim and len(e["artifacts"]) == 1:
            # 1835-07-15 is the case: the Democrat's No. 13 survives in this
            # deposit ONLY as the `-2` OCR rebuild, the poorer of the two
            # transcription runs. It is the primary because it is all there is,
            # and the record says so rather than letting the promotion be silent.
            only = e["artifacts"][0]
            only["role"] = "primary"
            only["sole_witness_note"] = (
                "The only transcription of this issue in the deposit, and it is a "
                "`-2` OCR rebuild — the run whose text is visibly poorer where the "
                "two can be compared (1835-07-01, 1835-07-08). Read it as the "
                "weakest tier of this corpus."
            )
            prim = [only]
        if len(prim) != 1:
            sys.exit("%s has %d primary artifacts, want exactly 1" % (e["id"], len(prim)))
        e["volume"], e["number"] = prim[0].pop("_vol"), prim[0].pop("_num")
        for a in e["artifacts"]:
            a.pop("_vol", None)
            a.pop("_num", None)
        for a in e["artifacts"]:
            docx = a.pop("_derive_from", None)
            tail = a.pop("_tail", None)
            if docx is None:
                continue
            stem = e["id"] if a["role"] == "primary" else "%s__alt_%s" % (e["id"], slug(tail))
            out = TEXT / (stem + ".txt")
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(docx_text.extract_file(docx))
            a["text_path"] = rel(out)
            a["text_sha256"] = sha256(out)
            a["derived_by"] = "tools/docx_text.py"
        for a in e["artifacts"]:
            a["text_chars"] = len(
                _read(a["text_path"]).read_text(encoding="utf-8", errors="replace"))
        e["text_path"] = prim[0]["text_path"]
        e["text_path_kind"] = prim[0]["text_path_kind"]
        e.setdefault("completeness", None)
        if e["completeness"] is None:
            e["completeness"] = "partial" if "Partial" in prim[0]["path"] else "unstated"
        e["volume"] = roman(e["volume"])
        # The transcriber's own header lines, read from the primary text rather
        # than paraphrased. `Status:` states completeness for the batches that
        # shipped no manifest; `Metadata note:` is where a printed duplicate
        # volume/number is flagged, and the workflow's rule 2.3 forbids quietly
        # renumbering one. 1835-08-26 and the American's 1835-08-29 both reprint
        # a number already used.
        head = _read(e["text_path"]).read_text(encoding="utf-8", errors="replace").split("\n")[:30]
        for line in head:
            for label, field in (("Status:", "status"), ("Metadata note:", "printed_metadata_note")):
                if line.startswith(label) and field not in e:
                    e[field] = line[len(label):].strip()
        if e["completeness"] == "unstated" and e.get("status", "").lower().startswith("complete"):
            e["completeness"] = "complete_per_transcriber"
        e["artifacts"].sort(key=lambda a: (a["role"] != "primary", a["path"]))

    ordered = sorted(issues.values(), key=lambda e: (e["publication"], e["date"]))
    doc = {
        "schema": SCHEMA_VERSION,
        "generated_by": "tools/newspaper_corpus.py --build",
        "deposit_root": rel(deposit),
        "workflow": rel(deposit / "Newspaper_Transcription_Workflow.md"),
        "issue_count": len(ordered),
        "publications": {
            k: {"title": v["title"], "source_id": v["source_id"],
                "issues": sum(1 for e in ordered if e["publication"] == k)}
            for k, v in sorted(PUBLICATIONS.items())
        },
        "issues": ordered,
    }
    CORPUS.parent.mkdir(parents=True, exist_ok=True)
    with open(CORPUS, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False, sort_keys=False)
        fh.write("\n")
    derived = sum(1 for e in ordered for a in e["artifacts"] if a["text_path_kind"] == "derived")
    print("built %s: %d issues, %d derived text file(s)" % (rel(CORPUS), len(ordered), derived))
    return 0


def _read(relpath):
    """The on-disk file for a recorded repo-relative path, during a build."""
    p = REPO / relpath
    if p.exists():
        return p
    return DEPOSIT_ACTUAL / Path(relpath).relative_to(DEPOSIT.relative_to(REPO))


ROMAN = {"1": "I", "2": "II", "I": "I", "II": "II"}


def roman(v):
    """Volume as the paper printed it. The deposit's filenames use Vol1 and VolI
    interchangeably for the same volume; the mastheads print Roman throughout."""
    if v is None:
        return None
    if v not in ROMAN:
        sys.exit("unmapped volume %r — add it to ROMAN rather than guessing" % v)
    return ROMAN[v]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "x"


# --------------------------------------------------------------------------
# the gate


def check(corpus_path=CORPUS, deposit=DEPOSIT, site=SITE, repo=REPO, quiet=False):
    """Returns a list of failure strings. Empty means green."""
    bad = []
    if not corpus_path.exists():
        return ["%s is missing" % corpus_path]
    try:
        doc = json.loads(corpus_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return ["%s is not JSON: %s" % (corpus_path, exc)]

    if doc.get("schema") != SCHEMA_VERSION:
        bad.append("schema is %r, this tool speaks %d" % (doc.get("schema"), SCHEMA_VERSION))
    issues = doc.get("issues") or []

    # 1. The count is ASSERTED, not observed: a silently dropped issue is loud.
    if doc.get("issue_count") != len(issues):
        bad.append("issue_count says %r, the file carries %d issues — an issue was "
                   "added or lost without the count moving"
                   % (doc.get("issue_count"), len(issues)))
    for pub, meta in (doc.get("publications") or {}).items():
        n = sum(1 for e in issues if e.get("publication") == pub)
        if meta.get("issues") != n:
            bad.append("%s declares %r issues and carries %d" % (pub, meta.get("issues"), n))

    # 2. Dates parse, and are strictly increasing per publication.
    seen = {}
    for e in issues:
        pub, iso = e.get("publication"), e.get("date")
        try:
            d = date.fromisoformat(iso)
        except (TypeError, ValueError):
            bad.append("%s: date %r does not parse" % (e.get("id"), iso))
            continue
        prev = seen.get(pub)
        if prev is not None and d <= prev[0]:
            bad.append("%s: %s does not follow %s — dates must strictly increase per "
                       "publication, so two entries for one issue is a fault"
                       % (e.get("id"), iso, prev[1]))
        seen[pub] = (d, iso)
        if e.get("id") != issue_id(pub, iso):
            bad.append("%s: id does not match its publication and date" % e.get("id"))

    # 3. Every text path resolves — or, for a deposit path, the deposit is
    #    wholesale absent. A PARTIAL deposit always fails.
    deposit_present = deposit.exists()
    canon = DEPOSIT.relative_to(REPO).as_posix()

    def on_disk(recorded):
        """Where a recorded repo-relative path actually is, for THIS run.

        A deposit given with --deposit may sit anywhere (it lives on `main`), so
        a deposit-rooted path is re-rooted onto it; everything else is read at
        its committed home under the repo.
        """
        if recorded.startswith(canon + "/"):
            return deposit / recorded[len(canon) + 1:]
        return repo / recorded

    unresolved_deposit = 0
    for e in issues:
        arts = e.get("artifacts") or []
        if not arts:
            bad.append("%s: no artifacts" % e.get("id"))
        prim = [a for a in arts if a.get("role") == "primary"]
        if len(prim) != 1:
            bad.append("%s: %d primary artifacts, want exactly 1" % (e.get("id"), len(prim)))
        elif prim[0].get("text_path") != e.get("text_path"):
            bad.append("%s: text_path does not name its own primary artifact" % e.get("id"))
        for a in arts:
            for field in ("path", "text_path", "text_path_kind", "sha256"):
                if not a.get(field):
                    bad.append("%s: artifact %r has no %s"
                               % (e.get("id"), a.get("path"), field))
            kind, tp = a.get("text_path_kind"), a.get("text_path")
            if not tp:
                continue
            target = on_disk(tp)
            if kind == "derived":
                if not target.exists():
                    bad.append("%s: derived text %s is missing — it is committed by "
                               "construction, so this is damage" % (e.get("id"), tp))
                elif a.get("text_sha256") and sha256(target) != a["text_sha256"]:
                    bad.append("%s: derived text %s no longer matches its recorded "
                               "sha256 — rebuild it with --build" % (e.get("id"), tp))
            elif kind == "deposit":
                if deposit_present and not target.exists():
                    bad.append("%s: %s is named by the corpus and is not in the deposit"
                               % (e.get("id"), tp))
                elif not deposit_present:
                    unresolved_deposit += 1
            else:
                bad.append("%s: unknown text_path_kind %r" % (e.get("id"), kind))
            if a.get("path", "").startswith(canon + "/") and deposit_present \
                    and not on_disk(a["path"]).exists():
                bad.append("%s: deposit artifact %s is absent" % (e.get("id"), a["path"]))

    # 4. data/research/ reaches NOTHING under site/chicago/4d/. The corpus is
    #    research; the published tree has a size budget and a purpose.
    if site.exists():
        if (site / "data" / "research").exists():
            bad.append("site/chicago/4d/data/research/ exists — the corpus is research, "
                       "not payload, and publish.sh must never copy it")
        names = {p.name for p in TEXT.glob("*.txt")} | {CORPUS.name}
        leaked = sorted(p for p in site.rglob("*") if p.is_file() and p.name in names)
        if leaked:
            bad.append("%d corpus file(s) reached the published mirror, starting with %s"
                       % (len(leaked), leaked[0].relative_to(repo)))

    if not quiet:
        state = "present" if deposit_present else "absent (this branch has no deposit)"
        print("  ok    %d issues, %d publications, deposit %s"
              % (len(issues), len(doc.get("publications") or {}), state))
        derived = sum(1 for e in issues for a in e["artifacts"]
                      if a.get("text_path_kind") == "derived")
        print("  ok    %d derived text file(s) present and matching their sha256" % derived)
        if unresolved_deposit:
            print("  note  %d deposit-held text path(s) not resolvable here — they are on "
                  "`main` (T-0275)" % unresolved_deposit)
    return bad


# --------------------------------------------------------------------------
# self-test: every assertion above must be capable of firing.


def self_test():
    import copy
    import tempfile
    doc = json.loads(CORPUS.read_text(encoding="utf-8"))
    failures = []

    def run(mutate, want, label):
        d = copy.deepcopy(doc)
        mutate(d)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "corpus.json"
            p.write_text(json.dumps(d), encoding="utf-8")
            bad = check(corpus_path=p, deposit=DEPOSIT, site=SITE, repo=REPO, quiet=True)
        if not any(want in b for b in bad):
            failures.append("%s: expected a failure mentioning %r, got %r" % (label, want, bad))

    run(lambda d: d["issues"].pop(), "issue_count says", "a dropped issue")
    run(lambda d: d.update(issue_count=d["issue_count"] + 1), "issue_count says", "a miscount")
    run(lambda d: d["issues"][0].update(date="not-a-date"), "does not parse", "an unparseable date")
    run(lambda d: d["issues"][1].update(date=d["issues"][0]["date"]),
        "strictly increase", "a repeated date")
    run(lambda d: d["issues"][0]["artifacts"][0].update(text_sha256="0" * 64),
        "sha256", "a text file edited after the build")
    run(lambda d: d["issues"][0]["artifacts"][0].update(text_path_kind="wishful"),
        "unknown text_path_kind", "an unknown path kind")
    run(lambda d: d["issues"][0].update(text_path="data/research/newspapers/text/nope.txt"),
        "does not name its own primary", "a text_path pointing elsewhere")
    run(lambda d: d.update(schema=99), "schema is", "a schema bump")

    # The derived-text check must fire on a file that is genuinely missing, and
    # the deposit rules must be the three states the header claims.
    d = copy.deepcopy(doc)
    with tempfile.TemporaryDirectory() as td:
        fake_repo = Path(td)
        (fake_repo / "data").mkdir()
        p = fake_repo / "corpus.json"
        p.write_text(json.dumps(d), encoding="utf-8")
        bad = check(corpus_path=p, deposit=fake_repo / "no-deposit",
                    site=fake_repo / "no-site", repo=fake_repo, quiet=True)
        if not any("derived text" in b for b in bad):
            failures.append("a missing derived text file did not fail")
        if any("is named by the corpus and is not in the deposit" in b for b in bad):
            failures.append("an ABSENT deposit was reported as a partial one")

    # ...and a PARTIAL deposit must fail, which is the state that means damage.
    d = copy.deepcopy(doc)
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "Transcriptions"
        fake.mkdir(parents=True)
        p = Path(td) / "corpus.json"
        p.write_text(json.dumps(d), encoding="utf-8")
        bad = check(corpus_path=p, deposit=fake, site=SITE, repo=REPO, quiet=True)
        if not any("is not in the deposit" in b for b in bad):
            failures.append("a PARTIAL deposit (present but empty) did not fail")

    if failures:
        for f in failures:
            print("FAIL: " + f, file=sys.stderr)
        return 1
    print("  ok    every corpus assertion fires when broken (%d cases)" % 11)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--deposit", type=Path, default=DEPOSIT)
    args = ap.parse_args(argv)
    if args.build:
        return build(args.deposit)
    if args.self_test:
        return self_test()
    if args.check or True:
        bad = check(deposit=args.deposit)
        for b in bad:
            print("  FAIL  " + b, file=sys.stderr)
        return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
