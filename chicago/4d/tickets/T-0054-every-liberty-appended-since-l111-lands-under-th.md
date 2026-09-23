---
id: T-0054
title: Every liberty appended since L111 lands under the Resolved heading and compiles as resolved
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-17
closed: 2026-08-27
pr: 386
claimed_by: run 8/26/2026, 11:30:15 PM CT
blocked_on: null
needs_bake: false
---

Every liberty appended to `docs/LIBERTIES.md` since **L111** has landed physically BELOW the
`## Resolved` heading, because new entries are appended to the end of the file and Resolved is the
last section. `tools/compile_liberties.py` reads the section a heading falls under, so seventeen
standing liberties — L111 through L127, including **L127**, written on 2026-08-18 for a fence that
is standing in the town right now — compile with `section: "resolved"`.

**Why it matters, and it is not cosmetic.** The Resolved section is EXEMPT from the coverage gate's
over-claim check, by design: it is what lets an append-only document survive its own data being
corrected. So every one of those seventeen entries is exempt from a check it should be subject to,
and the Evidence panel groups them as settled when they are not. Found while moving L60 to Resolved
for T-0051; L128 was placed in the per-subject section by hand to avoid joining them.

**Acceptance:** the misfiled entries read as standing liberties again — `data/liberties.json` shows
`section: "per_subject"` (or `standing`) for L111–L127, with each entry's placement decided by what
it says rather than by where the file ended — and `tools/check.sh` refuses a future append that
lands in the wrong section, so this cannot silently recur. No liberty text is edited: this is a
question of where the entries sit and what the document says about appending.

---

**MEASURED, and the count in the paragraph above is wrong in both directions.** It is not
"every liberty appended since L111" and it is not seventeen. Of the **71** entries numbered L111
and above, **24** sit under `## Resolved` and **one of those belongs there** — L116, the sycamore
drawn as an elm, which carries a `**Resolved:**` line. The other **47 were placed by hand in the
right section** by whoever wrote them, and L113, L114 and L118 are among them, so the range is not
contiguous. **23 entries were misfiled**, the newest being **L181** (2026-08-24). Across the whole
document, 34 entries compiled `section: "resolved"` and 11 say what settled them.

The fault is therefore intermittent rather than total: it catches whoever appends at the end of
the file, which is what the document tells you to do, and misses whoever scrolls up first.

**What the exemption was actually worth:** **12 of the 65 claim tokens** exempt from the
over-claim check were exempt by accident — L144's eight (the four Lake-and-Clark roofs' footprints
and positions) and L149 + L150's four slough claims. Put back under the check, **all twelve pass**:
every one is still an invention. That is the point rather than a relief — the entries were not
describing settled questions, so the label was false and the check was switched off for nothing.

**Done.**

- `## Resolved` moved **above** the per-subject register, so an append at the end of the file lands
  where a new liberty belongs. The 23 stay where they were written; the 11 settled entries move up.
  No liberty text edited, nothing removed. Sections now 3 standing / 167 per-subject / 11 resolved.
- `tools/compile_liberties.py` decides `resolved` from **two independent statements that must
  agree** — the section an entry sits under, and the `**Resolved:**` line in its own text. Either
  half alone is reported by id and fails `check.sh`; a misfiled entry compiles `per_subject`, the
  reading that keeps its obligations. Eleven self-test assertions, wired into `check.sh` beside the
  compile step, and the last of them reads the committed document rather than the specimen.
- Ten building cards lose a scope chip reading *resolved* on a liberty that still stands — the
  Western Hotel's wagon-yard fence (L127) among them.
- The derived file is emitted grouped standing → per-subject → resolved, stable within each group,
  so the panel's order is a decision in the compiler rather than a consequence of where a section
  sits in the markdown. On screen the order is unchanged from before the reshuffle.
