---
id: T-0167
title: Size the desktop parts from a measured desktop profile, and re-cut whatever still overruns
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0121
opened: 2026-08-23
closed: 2026-08-23
pr: 346
claimed_by: run 8/23/2026, 10:01:49 PM CT
blocked_on: null
needs_bake: false
---

Size the desktop parts from a measured desktop profile, and re-cut whatever still overruns.

Piece 2 of 2 of **T-0121 — The desktop smoke's fourth stage has outgrown the ten-minute command ceiling**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** every part of `SMOKE_STAGE` completes inside 600 s **at 1280x800** on a
standard runner, each one measured and the whole profile written where T-0060's fit was
(docs/ROADMAP.md § THE RUN BUDGET) — re-cutting whatever still overruns, never dropping
a check.

**Why this is its own run, measured rather than argued.** T-0166 cut the four stages
into eight and measured the mobile fit: the mobile body is **13 m 30 s** across the
eight parts, and every one of them fits comfortably. The desktop body does not scale
from it. On this runner, against the published mirror:

| | mobile | desktop |
|---|---|---|
| part 6 (facade tones → the K24 aid) | 0 m 44 s | 1 m 53 s |
| part 7 (the flora census → the street names) | 3 m 48 s | **killed at 10 m 00 s** |

So the desktop cost of a part is not a fixed multiple of its mobile cost — the
camera-heavy parts scale several times harder than the DOM-heavy ones, which is exactly
why an eight-way cut sized on the mobile profile leaves parts over the ceiling. **The
profile has to be measured at 1280x800 and the cut sized from it**, and that measurement
is the whole run: the desktop body is roughly 50 minutes and every part costs another
~1 m 45 s boot, so a full desktop pass is 55-70 minutes of foreground commands. It does
not fit beside a re-cut, and the re-cut is what it exists to size.

**Do it in this order**, so nothing is spent twice: run the eight parts at desktop, one
foreground command each, and record the wall clock each prints (a part that is killed
records ">10 m" and nothing else — the reading it did not give is the reason to cut it
first). Split the parts that overrun at a section boundary re-verified for crossing
bindings — `git log` for T-0121's scope-aware scan — and give each new second half the
idempotent prologue its first line needs (T-0166 needed `enterTown()` for parts 6 and 8,
a panel-open guard for part 8, and a re-frame for part 4). Then measure again.

---

## What this run did, 2026-08-24

**The profile, eight foreground commands at 1280x800 against the published mirror**, each part
run alone with `SMOKE_TIMING=1`. Part 1 3 m 31 s / 66 staged · part 2 2 m 37 s / 66 · part 3
1 m 40 s / 65 · part 4 7 m 07 s / 35 · part 5 6 m 40 s / 19 · part 6 1 m 24 s / 14 · part 7
7 m 43 s / 36 · part 8 8 m 46 s / 107 — 408 staged plus 9 always-on, 39 m 28 s of wall clock.
Written into docs/ROADMAP.md § THE RUN BUDGET, where T-0060's and T-0166's fits are.

**Nothing overran**, which is not the same as fitting, and the ticket's own premise turned out
to be one reading rather than a constant: part 7 measured 7 m 43 s here and part 4 7 m 07 s,
against the ">10 m" kill and the "run part 4 outside the ceiling" instruction this ticket was
opened on. The desktop numbers move by minutes between runs — SwiftShader's cost tracks whatever
else the machine is doing — so parts are sized on MARGIN, not on whether one reading cleared.

**So the re-cut is part 8**, at 1 m 14 s of margin and 107 staged checks, three times the
check-density of any other part. It is the tail, so part 9 is appended and parts 1-7 keep their
numbers; the pairing rule survives as 1+2, 3+4, 5+6, 7+8+9 and the mobile recipe stays four
commands (`7-8` widens to `7-9`). Measured after: part 8 6 m 10 s / 28 staged, part 9
3 m 09 s / 79 staged. **28 + 79 = 107** — no check dropped. Mobile `7-9` gives 143 staged / 9
always-on / 152 passed, identical to `7-8` before the cut. All three were taken twice, once at
`ac1abb80` and again after T-0114 merged into `dev` mid-run, with the same counts both times.

**`SMOKE_TIMING=1` was added because the profile could not be taken without it.** A part that
breaches the ceiling is killed before it prints its wall clock, so the parts worth cutting were
the only ones a plain run said nothing about. Off by default.

**Left for T-0170:** part 7, now the worst margin at 2 m 17 s and the part that was actually
measured over the ceiling once. It is a harder cut — no section headers, half the
`anyStage(5, 7)` street-layer reading, and not the tail — and it is its own run.
