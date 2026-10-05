#!/usr/bin/env python3
"""The letter-list cohort, published as a roster rather than one file per name — T-0438.

The owner's ruling of 2026-08-30 (T-0379) put the post office's letter-list names
into the town as households, and the RECORDS stay exactly that: one canonical file
per person under data/residents/households/, which `validate.py` and
`mint_letter_list_residents.py --gate` read and nothing here touches. What this
changes is only the PUBLISHED form of those files.

WHY. Filed at 727 records and 2.54 MiB, the cohort had grown to 773 records and
9.30 MiB minified by 2026-10-04 — more than three times over, because every fill
pass since (arrival year, origin, reason for coming, sex, age band, division)
wrote its own paragraph onto each record, and wrote the SAME paragraph onto most
of them. The growth is bounded by nothing the project has decided, and a visitor
pays for none of the repetition: the panel opens these rows one at a time out of
one closed group.

THE FORM. Under `site/4d/data/residents/letter_list/`:

  roster.json   the shared string table — every string value that recurs in the
                cohort and is at least MIN_BYTES long, held once — and `shards`,
                which names the shard file each household record is in;
  <a-z|_>.json  `{"records": {"households/hh_….json": <record>}}`, one shard per
                initial of the household id, each string from the table written
                as `{"$s": <index>}`.

and the 773 per-record files are taken out of the mirror. The renderer reads a
cohort row through `renderers/web/js/letter-list-roster.js`, which fetches the
roster once and the row's shard once, and falls back to the per-record file — so
the dev tree, which publishes nothing, reads exactly as it did.

THE CONTRACT. publish.sh copies; this is the second place it derives, after the
minify above it, and `tools/check_published_residents.mjs` holds the shipped form
to the same claim it holds the minified files to: every cohort record, unpacked by
the renderer's own code, is deep-equal to its source, none missing, none extra, and
none shipped twice. Nothing is dropped, and refusal is loud — a record carrying an
object whose only key is "$s" would be ambiguous once packed, so `pack` refuses it
and the publish fails rather than ship a record that would read back wrong.

    python3 tools/pack_letter_list.py <site/4d/data/residents>   # publish.sh calls this
    python3 tools/pack_letter_list.py --self-test
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROSTER_DIR = "letter_list"
ROSTER = "roster.json"
MARK = "$s"
# A reference costs `{"$s":NNNN}` — eleven bytes — so a shorter string is cheaper
# written out where it stands.
MIN_BYTES = 16
VERSION = 1


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def shard_of(file: str) -> str:
    """The shard a household file is packed into: the initial after `hh_`."""
    stem = Path(file).stem
    c = (stem[3:4] if stem.startswith("hh_") else stem[:1]).lower()
    return c if "a" <= c <= "z" else "_"


def _strings(value, counts: Counter) -> None:
    if isinstance(value, dict):
        for v in value.values():
            _strings(v, counts)
    elif isinstance(value, list):
        for v in value:
            _strings(v, counts)
    elif isinstance(value, str):
        counts[value] += 1


def _refuse_marker(value, where: str) -> None:
    if isinstance(value, dict):
        if list(value) == [MARK]:
            raise ValueError(f"{where} holds an object whose only key is {MARK!r}: it would read "
                             "back as a reference to the string table, so the cohort cannot be "
                             "packed without changing it")
        for k, v in value.items():
            _refuse_marker(v, f"{where}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _refuse_marker(v, f"{where}[{i}]")


def _intern(value, index: dict):
    if isinstance(value, dict):
        return {k: _intern(v, index) for k, v in value.items()}
    if isinstance(value, list):
        return [_intern(v, index) for v in value]
    if isinstance(value, str) and value in index:
        return {MARK: index[value]}
    return value


def unpack_record(packed, strings: list):
    if isinstance(packed, dict):
        if list(packed) == [MARK]:
            return strings[packed[MARK]]
        return {k: unpack_record(v, strings) for k, v in packed.items()}
    if isinstance(packed, list):
        return [unpack_record(v, strings) for v in packed]
    return packed


def pack(records: dict) -> tuple[dict, dict]:
    """`{file: record}` -> (roster, {shard: shard_body}). Deterministic for one input."""
    counts: Counter = Counter()
    for file in sorted(records):
        _refuse_marker(records[file], file)
        _strings(records[file], counts)
    strings = sorted(s for s, n in counts.items()
                     if n > 1 and len(s.encode("utf-8")) >= MIN_BYTES)
    index = {s: i for i, s in enumerate(strings)}
    where: dict = {}
    shards: dict = {}
    for file in sorted(records):
        shard = shard_of(file)
        where[file] = shard
        shards.setdefault(shard, {})[file] = _intern(records[file], index)
    roster = {
        "_doc": "The letter-list cohort's published form (T-0438): the canonical records are "
                "data/residents/households/*.json in the repository. `strings` holds every "
                "string the cohort repeats; a shard writes each one as {\"$s\": index}. "
                "`shards` names the file under letter_list/ that holds each household. "
                "Written by tools/pack_letter_list.py, read by "
                "renderers/web/js/letter-list-roster.js.",
        "version": VERSION,
        "strings": strings,
        "shards": where,
    }
    return roster, {s: {"records": body} for s, body in sorted(shards.items())}


def unpack(roster: dict, shards: dict) -> dict:
    out = {}
    for file, shard in roster["shards"].items():
        out[file] = unpack_record(shards[shard]["records"][file], roster["strings"])
    return out


def apply(residents: Path) -> dict:
    """Pack the published cohort under `residents` and take its per-record files out."""
    index = json.loads((residents / "index.json").read_text(encoding="utf-8"))
    files = sorted(e["file"] for e in index.get("households", []) if e.get("letter_list_only"))
    missing = [f for f in files if not (residents / f).is_file()]
    if missing:
        raise SystemExit(f"pack_letter_list: {len(missing)} cohort file(s) the index names are not "
                         f"in {residents}: {missing[:5]} — publish.sh must copy the layer first")
    records = {f: json.loads((residents / f).read_text(encoding="utf-8")) for f in files}
    before = sum((residents / f).stat().st_size for f in files)
    roster, shards = pack(records)
    if unpack(roster, shards) != records:
        raise SystemExit("pack_letter_list: the packed cohort does not read back as its records — "
                         "refusing to take any file out of the mirror")
    out = residents / ROSTER_DIR
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / ROSTER).write_text(_dump(roster), encoding="utf-8")
    for shard, body in shards.items():
        (out / f"{shard}.json").write_text(_dump(body), encoding="utf-8")
    for f in files:
        (residents / f).unlink()
    after = sum(p.stat().st_size for p in out.iterdir())
    return {"records": len(files), "before": before, "after": after,
            "shards": len(shards), "strings": len(roster["strings"])}


def self_test() -> int:
    fails = []

    def check(name, ok):
        if not ok:
            fails.append(name)
        print(f"self-test | {'ok  ' if ok else 'FAIL'} {name}")

    long_note = "A BOUND FROM THE RETURN, NOT AN ARRIVAL — the same paragraph on every record."
    recs = {
        "households/hh_abbot_g.json": {"id": "hh_abbot_g", "head": "abbot_g", "note": long_note,
                                       "persons": [{"id": "abbot_g", "n": 1, "x": None,
                                                    "returns": ["1835-07-01"], "t": True,
                                                    "note": long_note, "short": "inferred"}]},
        "households/hh_zane_é.json": {"id": "hh_zane_é", "note": long_note, "short": "inferred",
                                      "unicode": "Côté — ‘quoted’ and repeated here",
                                      "again": "Côté — ‘quoted’ and repeated here"},
        "households/hh_9_odd.json": {"id": "hh_9_odd", "nested": [[long_note], {"k": long_note}]},
    }
    roster, shards = pack(recs)
    check("every cohort record reads back deep-equal", unpack(roster, shards) == recs)
    check("a string repeated across records is held once", roster["strings"].count(long_note) == 1)
    check("a short repeated string is written where it stands", "inferred" not in roster["strings"])
    check("a string seen once stays in its record", "hh_abbot_g" not in roster["strings"])
    check("shards by initial, and the odd initial goes to '_'",
          roster["shards"] == {"households/hh_abbot_g.json": "a",
                               "households/hh_zane_é.json": "z",
                               "households/hh_9_odd.json": "_"})
    again = pack(dict(reversed(list(recs.items()))))
    check("the packed form does not depend on the order records arrive in",
          _dump(again[0]) == _dump(roster) and _dump(again[1]) == _dump(shards))
    try:
        pack({"households/hh_x.json": {"id": "hh_x", "odd": {MARK: 0}}})
        check("a record holding a bare {\"$s\": …} object is refused", False)
    except ValueError:
        check("a record holding a bare {\"$s\": …} object is refused", True)
    check("an object with $s beside other keys is not a reference",
          unpack(*pack({"households/hh_y.json": {"o": {MARK: 1, "k": 2}}}))
          == {"households/hh_y.json": {"o": {MARK: 1, "k": 2}}})

    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        (res / "households").mkdir()
        index = {"households": [{"id": "hh_abbot_g", "file": "households/hh_abbot_g.json",
                                 "letter_list_only": True},
                                {"id": "hh_zane_é", "file": "households/hh_zane_é.json",
                                 "letter_list_only": True},
                                {"id": "hh_kept", "file": "households/hh_kept.json"}]}
        (res / "index.json").write_text(_dump(index), encoding="utf-8")
        for f in ("households/hh_abbot_g.json", "households/hh_zane_é.json"):
            (res / f).write_text(_dump(recs[f]), encoding="utf-8")
        (res / "households/hh_kept.json").write_text(_dump({"id": "hh_kept"}), encoding="utf-8")
        got = apply(res)
        check("the cohort's per-record files leave the mirror",
              not (res / "households/hh_abbot_g.json").exists()
              and not (res / "households/hh_zane_é.json").exists())
        check("a household outside the cohort is left where it is",
              (res / "households/hh_kept.json").is_file())
        r2 = json.loads((res / ROSTER_DIR / ROSTER).read_text(encoding="utf-8"))
        sh2 = {p.stem: json.loads(p.read_text(encoding="utf-8"))
               for p in (res / ROSTER_DIR).iterdir() if p.name != ROSTER}
        check("what landed reads back as the two cohort records",
              unpack(r2, sh2) == {f: recs[f] for f in ("households/hh_abbot_g.json",
                                                       "households/hh_zane_é.json")})
        check("the report counts the records it packed", got["records"] == 2)

    print(f"self-test | {len(fails)} failure(s)")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("residents", nargs="?", help="the PUBLISHED data/residents directory")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.residents:
        ap.error("name the published residents directory")
    got = apply(Path(a.residents))
    mib = 1024 * 1024
    print(f"letter-list cohort: {got['records']} records packed from {got['before'] / mib:.2f} MiB "
          f"of per-record files to {got['after'] / mib:.2f} MiB in {got['shards']} shard(s) and a "
          f"{got['strings']}-string roster (T-0438)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
