#!/usr/bin/env python3
"""T-0714 — every tool that can re-derive itself, and whether the gate ever asks it to.

    tools/audit_check_gates.py            the report: which --check modes check.sh runs
    tools/audit_check_gates.py --gate     fail if the ungated set has GROWN
    tools/audit_check_gates.py --write    re-record the baseline after a deliberate change
    tools/audit_check_gates.py --self-test

WHY THIS EXISTS. `crosswalk_census_1840_heads.py --check` had been red on `dev` for an
unknown number of days when T-0714 measured it: 498 heads adjudicated on disk against
788 read off the pages. Every sibling crosswalk IS gated and fails the moment its
committed file stops re-deriving; this one alone was not, so 290 heads of reading sat
un-adjudicated without one red build. The fault is not the crosswalk. The fault is that
NOTHING ASKED whether a tool with a `--check` mode is wired into `tools/check.sh`, so the
answer could only ever be found by hand, one tool at a time, by someone who suspected it.

WHAT THIS ASSERTS, AND WHAT IT DOES NOT. It does not assert that every `--check` runs in
the gate: some of these are one-shot passes whose inputs are gone, some are slow, and a
few are red today for reasons that are their own tickets (T-0691 holds
`mint_letter_list_residents.py --check`, which is red because a cohort drifted, not
because this file is wrong). Gating them is work with rulings in it and it is not free.
What this asserts is a RATCHET: the set of `--check`-capable tools the gate never runs
may SHRINK freely and may not GROW. A new derivation arrives gated, or it arrives with a
deliberate line in `data/research/check_gate_baseline.json` saying why not.

HOW IT READS check.sh. A tool counts as gated when `tools/check.sh` invokes it with
`--check` anywhere — the same string a reader would grep for. A tool check.sh runs under
some OTHER mode (`--gate`, `--self-test`, `--offline`) is still counted UNGATED here, and
the report says which modes it does run, because those modes prove different things: a
self-test proves the assertions fire, and only `--check` proves the committed file still
follows from its inputs.

WHAT T-0896 ADDED, AND WHY THE RATCHET ALONE WAS NOT ENOUGH. T-0714's baseline recorded
the tools and nothing else, and `--write` rebuilt the file from the survey — so a reason
written into it by hand did not survive the next write, and the acceptance T-0896 was
filed with ("each carries a stated reason a reader can act on") could not be met at all.
Reasons are AUTHORED now, `--write` carries them forward by tool, and the gate asks for
one. Three ways to fail instead of one:

  * a tool newly ungated and absent from the baseline — the original ratchet;
  * a tool in the baseline that the gate DOES run `--check` on now. The set may shrink
    freely, but the file has to be told, in the commit that shrank it. It was not: the
    baseline said 18 on 2026-09-13 and the survey said 16, because
    `crosswalk_norris_1844_advertiser.py` and `generate_school_section_grid.py` had been
    gated since and nothing asked. A ratchet that can only measure growth against a
    number allowed to stay too high is a ratchet with slack in it;
  * an ungated tool carrying no `why_not_gated`. Silence is what this whole file exists
    to end, and an empty string is silence.

A REASON IS NOT ONLY "it cannot be gated". Ten of the sixteen are ungated because their
`--check` is RED — the committed file has stopped following from its inputs and nobody
knew. That is a finding, not an exemption, so those rows carry the measured red and the
ticket that owns it; `owner_ticket` is where a reader goes next.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK_SH = ROOT / "tools" / "check.sh"
BASELINE = ROOT / "data" / "research" / "check_gate_baseline.json"
SEARCH = ("tools/*.py", "generators/*.py", "tools/*.mjs")


def scripts() -> list[Path]:
    out: list[Path] = []
    for pattern in SEARCH:
        out.extend(sorted(ROOT.glob(pattern)))
    return out


def survey() -> dict:
    """Every script advertising a --check flag, and how check.sh invokes it.

    Read off the COMMANDS check.sh runs, not off its text (T-0662). Until 2026-09-17
    this grepped the whole file, so a comment that named a tool beside `--check` — the
    natural way to write down that a pass is red and who owns it — counted as gating
    it, and the ratchet went quiet about a tool nothing ran. The gate is the commands.
    """
    commands = [command for _label, command in steps()]
    capable, ungated = [], []
    for path in scripts():
        body = path.read_text(errors="replace")
        if not re.search(r"""["']--check["']""", body):
            continue
        rel = path.relative_to(ROOT).as_posix()
        capable.append(rel)
        runs = [c for c in commands if re.search(re.escape(rel) + r"(?:\s|$)", c)]
        # `--check` as a PREFIX, deliberately: six trace/measure tools are gated by
        # `--check-properties` and this has always counted them, so narrowing it here
        # would add six rows to the baseline on a ticket that is not about them.
        if any(re.search(re.escape(rel) + r"\s[^|;&]*--check", c) for c in runs):
            continue
        modes = sorted({m for c in runs
                        for m in re.findall(re.escape(rel) + r"\s+(--[a-z-]+)", c)})
        ungated.append({"tool": rel, "other_modes_in_check_sh": modes})
    return {"check_capable": capable, "ungated": ungated}


def load_baseline() -> dict:
    if not BASELINE.exists():
        return {"ungated": []}
    return json.loads(BASELINE.read_text())


# The fields a person writes and no survey can produce. `--write` carries them
# forward by tool, which is the whole of T-0896's mechanism: before it, the only
# place to put a reason was a file the next write overwrote.
AUTHORED = ("why_not_gated", "owner_ticket")


def merge_authored(rows: list[dict], known: dict) -> list[dict]:
    """Each surveyed row, wearing whatever the baseline already said about it."""
    out = []
    for row in rows:
        merged = dict(row)
        for field in AUTHORED:
            value = known.get(row["tool"], {}).get(field)
            if value not in (None, ""):
                merged[field] = value
        out.append(merged)
    return out


def by_tool(baseline: dict) -> dict:
    return {row["tool"]: row for row in baseline.get("ungated", [])}


def verdicts(found: list[dict], known: dict) -> list[str]:
    """Every way the baseline can be out of step with the tree, in reading order."""
    bad = []
    names = {row["tool"] for row in found}
    for tool in sorted(names - set(known)):
        bad.append("BAD: %s has a --check mode that tools/check.sh never runs, and it "
                   "is not in %s. Gate it, or record why not."
                   % (tool, BASELINE.relative_to(ROOT)))
    for tool in sorted(set(known) - names):
        bad.append("BAD: %s is listed as ungated in %s, and the gate runs its --check "
                   "now. Re-run tools/audit_check_gates.py --write in this commit so "
                   "the ratchet tightens."
                   % (tool, BASELINE.relative_to(ROOT)))
    for tool in sorted(names & set(known)):
        if not str(known[tool].get("why_not_gated") or "").strip():
            bad.append("BAD: %s is ungated and %s states no reason. Write why_not_gated "
                       "— what a reader should do about it — or gate the tool."
                       % (tool, BASELINE.relative_to(ROOT)))
    return bad


# ---------------------------------------------------------------------------
# T-0662 — a step may not borrow another pass's command
# ---------------------------------------------------------------------------
# The ratchet above asks whether a tool's `--check` is run AT ALL. It cannot see the
# other half of the same fault, and that half sat in this file's own subject matter for
# a fortnight: `tools/synthesize_resident_research.py --check` was run FIVE times, under
# five different labels, four of which named a pass check.sh does not run — the K1
# inferred-household programme, the invented names, T-0264's roof deal, and the
# documented and letter-list mints. Every one of those five passes carries a `--check`
# of its own, every one is RED, and every one is in the baseline below as ungated. So
# the baseline was right and the build was green and a reader of check.sh would have
# concluded, reasonably, that five derivations were held. One was.
#
# A borrowed command is what that looks like in the file, and it is cheap to refuse: a
# command that runs under more than one label is either a lie about one of them or a
# duplicate paid for twice. Measured across all 424 steps on 2026-09-17, after the five
# were collapsed to one, no command in check.sh runs twice. The rule costs nothing to
# keep and it makes T-0662's defect unrepeatable under a different pair of names.

def steps(text: str | None = None) -> list[tuple[str, str]]:
    """Every (label, command) tools/check.sh runs, continuations joined."""
    if text is None:
        text = CHECK_SH.read_text()
    lines = text.splitlines()
    out: list[tuple[str, str]] = []
    for i, line in enumerate(lines):
        m = re.match(r'\s*(?:step|selftest)\s+"((?:[^"\\]|\\.)*)"\s*(.*)$', line)
        if not m:
            continue
        label, rest = m.group(1), m.group(2).strip()
        j = i
        while rest.endswith("\\"):
            rest = rest[:-1].strip()
            j += 1
            if j >= len(lines):
                break
            rest = (rest + " " + lines[j].strip()).strip()
        command = " ".join(rest.split())
        if command:
            out.append((label, command))
    return out


def borrowed(text: str | None = None) -> list[tuple[str, list[str]]]:
    """Commands check.sh runs under more than one label, worst first."""
    seen: dict[str, list[str]] = {}
    for label, command in steps(text):
        seen.setdefault(command, []).append(label)
    return sorted(((c, ls) for c, ls in seen.items() if len(ls) > 1),
                  key=lambda row: (-len(row[1]), row[0]))


def borrowed_verdicts(text: str | None = None) -> list[str]:
    bad = []
    for command, labels in borrowed(text):
        bad.append("BAD: tools/check.sh runs `%s` under %d labels, so at most one of "
                   "them is the truth about what it proves (T-0662): %s"
                   % (command, len(labels), "; ".join('"%s"' % l for l in labels)))
    return bad


def report() -> int:
    found = survey()
    print("TOOLS WITH A --check MODE: %d" % len(found["check_capable"]))
    print("RUN WITH --check BY tools/check.sh: %d"
          % (len(found["check_capable"]) - len(found["ungated"])))
    print("NOT RUN WITH --check BY tools/check.sh: %d" % len(found["ungated"]))
    dup = borrowed()
    print("STEPS: %d, of which %d command(s) run under more than one label"
          % (len(steps()), len(dup)))
    for command, labels in dup:
        print("  %s" % command)
        for label in labels:
            print("      %s" % label)
    known = by_tool(load_baseline())
    for row in merge_authored(found["ungated"], known):
        other = (" ".join(row["other_modes_in_check_sh"])
                 if row["other_modes_in_check_sh"] else "not run in check.sh at all")
        print("  %-52s %s" % (row["tool"], other))
        why = row.get("why_not_gated")
        print("      %s%s" % (why or "NO REASON RECORDED",
                              " (%s)" % row["owner_ticket"] if row.get("owner_ticket")
                              else ""))
    return 0


def gate(quiet: bool = False) -> int:
    found = survey()["ungated"]
    known = by_tool(load_baseline())
    bad = verdicts(found, known) + borrowed_verdicts()
    for line in bad:
        print(line)
    if bad:
        return 1
    if not quiet:
        print("OK: %d ungated --check mode(s), each recorded, none new and none "
              "stale; %d step(s), no command run under two labels"
              % (len(found), len(steps())))
    return 0


def write() -> int:
    found = survey()
    rows = merge_authored(found["ungated"], by_tool(load_baseline()))
    doc = {
        "schema": 2,
        "ticket": "T-0714, with T-0896's reasons",
        "what": "The tools carrying a --check mode that tools/check.sh does not run with "
                "--check, and WHY each one is not. A ratchet, not a target: this list "
                "may shrink, and audit_check_gates.py --gate fails when it grows, when "
                "it is left standing above what the tree actually shows, or when a row "
                "states no reason.",
        "how_to_change_it": "Gate the tool in tools/check.sh and re-run --write, or, if "
                            "it cannot be gated today, write why_not_gated on its row "
                            "here — --write carries that field forward — and point "
                            "owner_ticket at whoever owns the answer. The gate fails on "
                            "a row with no reason, and on a row the gate has since "
                            "started running.",
        "counts": {"check_capable": len(found["check_capable"]),
                   "gated": len(found["check_capable"]) - len(rows),
                   "ungated": len(rows)},
        "ungated": rows,
    }
    BASELINE.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s — %d of %d --check-capable tool(s) ungated"
          % (BASELINE.relative_to(ROOT), len(found["ungated"]),
             len(found["check_capable"])))
    return 0


def self_test() -> int:
    failures = []

    def expect(label, got, want):
        if got != want:
            failures.append("%s: got %r, wanted %r" % (label, got, want))

    found = survey()
    expect("the survey finds the gate's own siblings",
           "tools/apply_census_1840_bridges.py" in found["check_capable"], True)
    expect("a tool check.sh runs with --check is not reported ungated",
           "tools/apply_census_1840_bridges.py" in {r["tool"] for r in found["ungated"]},
           False)
    expect("the crosswalk this ticket gated is no longer ungated",
           "tools/crosswalk_census_1840_heads.py" in {r["tool"] for r in found["ungated"]},
           False)
    expect("a tool run only under another mode still counts as ungated",
           next((r["other_modes_in_check_sh"]
                 for r in found["ungated"]
                 if r["tool"] == "tools/mint_letter_list_residents.py"), None),
           ["--gate", "--self-test"])
    expect("the baseline covers every ungated tool found today",
           sorted({r["tool"] for r in found["ungated"]}
                  - {r["tool"] for r in load_baseline().get("ungated", [])}), [])

    # T-0896. The three ways the baseline can be out of step with the tree. Fabricated
    # against the real survey, because what these assert is the JUDGEMENT and not the
    # tree: a fixture that drifts from the repository proves nothing about it.
    real = found["ungated"]
    sample = real[0]["tool"]
    full = {row["tool"]: {"tool": row["tool"], "why_not_gated": "recorded"}
            for row in real}
    expect("a tree that matches a fully-reasoned baseline raises nothing",
           verdicts(real, full), [])
    expect("a newly ungated tool the baseline has never heard of fails",
           len(verdicts(real, {k: v for k, v in full.items() if k != sample})), 1)
    expect("…and it says to gate it or record why",
           "Gate it, or record why not"
           in verdicts(real, {k: v for k, v in full.items() if k != sample})[0], True)
    stale = dict(full, **{"tools/not_a_tool_any_more.py":
                          {"tool": "tools/not_a_tool_any_more.py",
                           "why_not_gated": "recorded"}})
    expect("a row the gate runs --check on now fails until --write tightens it",
           len(verdicts(real, stale)), 1)
    expect("…and it names the write that tightens it",
           "--write" in verdicts(real, stale)[0], True)
    silent = dict(full, **{sample: {"tool": sample, "why_not_gated": "   "}})
    expect("an ungated tool with no stated reason fails",
           len(verdicts(real, silent)), 1)
    expect("…and a missing field is the same silence as a blank one",
           len(verdicts(real, dict(full, **{sample: {"tool": sample}}))), 1)

    # The reason is AUTHORED, so the only thing that can destroy it is the writer.
    expect("a write carries an authored reason forward onto the surveyed row",
           merge_authored(real, {sample: {"tool": sample, "why_not_gated": "kept",
                                          "owner_ticket": "T-0896"}})[0].get("why_not_gated"),
           "kept")
    expect("…and the ticket beside it",
           merge_authored(real, {sample: {"tool": sample, "why_not_gated": "kept",
                                          "owner_ticket": "T-0896"}})[0].get("owner_ticket"),
           "T-0896")
    expect("…and an empty authored field does not overwrite the survey",
           "why_not_gated" in merge_authored(real, {sample: {"tool": sample,
                                                             "why_not_gated": ""}})[0],
           False)
    expect("every reason the committed baseline states is non-empty",
           sorted(t for t, r in by_tool(load_baseline()).items()
                  if not str(r.get("why_not_gated") or "").strip()), [])

    # T-0662 — the borrowed command, fired against the shape it was found in. The
    # fabricated file is the real defect in miniature: one command, two labels, and one
    # of them naming a pass that is not run.
    TWO_LABELS = (
        'step "the minted letter-list residents re-derive from the register" \\\n'
        '  python3 tools/synthesize_resident_research.py --check\n'
        'step "the resident synthesis re-derives the population it writes" \\\n'
        '  python3 tools/synthesize_resident_research.py --check\n')
    expect("a command run under two labels is refused",
           len(borrowed_verdicts(TWO_LABELS)), 1)
    expect("…and the verdict names both labels",
           all(part in borrowed_verdicts(TWO_LABELS)[0]
               for part in ("the minted letter-list residents",
                            "the resident synthesis")), True)
    expect("…and says how many there were",
           "under 2 labels" in borrowed_verdicts(TWO_LABELS)[0], True)
    ONE_LABEL = ('step "the resident synthesis re-derives the population it writes" \\\n'
                 '  python3 tools/synthesize_resident_research.py --check\n')
    expect("the same command under ONE label is not a borrowing",
           borrowed_verdicts(ONE_LABEL), [])
    expect("two labels over two different commands are not a borrowing",
           borrowed_verdicts(TWO_LABELS.replace("--check\nstep", "--drift\nstep", 1)), [])
    expect("tools/check.sh as committed runs no command under two labels",
           borrowed(), [])

    # …and the continuation the parser has to join to see the command at all.
    expect("a step's command is read off its continuation line",
           steps('step "a label" \\\n  python3 tools/x.py --check\n'),
           [("a label", "python3 tools/x.py --check")])
    expect("a step written on one line is read too",
           steps('step "data JSON parses" check_json\n'),
           [("data JSON parses", "check_json")])

    # The survey reads COMMANDS. Prose that names a tool beside --check — which is how
    # an ungated red pass gets written down — must not count as gating it.
    PROSE = ('# tools/mint_documented_residents.py --check reports 10 file(s) differing\n'
             'step "something else entirely" \\\n'
             '  python3 tools/synthesize_resident_research.py --check\n')
    import tempfile
    global CHECK_SH
    real_path = CHECK_SH
    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as fh:
        fh.write(PROSE)
        CHECK_SH = Path(fh.name)
    try:
        expect("a tool named only in a comment is not counted as gated",
               "tools/mint_documented_residents.py" in {r["tool"]
                                                        for r in survey()["ungated"]},
               True)
    finally:
        CHECK_SH = real_path

    for line in failures:
        print("FAIL: %s" % line)
    print("self-test: %d assertion(s) failed" % len(failures))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.write:
        return write()
    if args.gate:
        return gate(args.quiet)
    return report()


if __name__ == "__main__":
    sys.exit(main())
