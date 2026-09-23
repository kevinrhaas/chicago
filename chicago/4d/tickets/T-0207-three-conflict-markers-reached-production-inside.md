---
id: T-0207
title: Three conflict markers reached production inside two liberty cards, and every gate passed them
state: done
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-26
pr: 383
claimed_by: integrator
blocked_on: null
needs_bake: false
---

Three conflict markers reached production inside two liberty cards, and every gate passed them.

`docs/LIBERTIES.md` carried three literal git conflict-marker lines from commit
**e2056e97** (T-0117, the poplar rows) onward. They compiled into
`data/liberties.json`, published to `site/chicago/4d/`, merged to `dev`, and were
**promoted to `main` in promotion run #13** (`f09db144`, tagged `release-v269`).
A visitor opening the Evidence panel on either of two liberties was shown:

    L180 …  Recorded: 2026-08-23. <<<<<<< HEAD
    L181 …  Recorded: 2026-08-24. ======= >>>>>>> origin/dev

**No liberty text was lost** — dev's side of the hunk was empty, L181 appears
exactly once, and the damage is the three marker lines and nothing else. It is
cosmetic, and it is exactly the kind of cosmetic that costs a provenance project
its credibility: the panel whose whole job is to say *this part is invented and
here is why* was showing unresolved merge debris.

**Why nothing caught it.** Three things had to line up, and they did:

1. **The liberties gate asks whether two derivations agree, and they did.**
   `compile_liberties.py` recognises `### L<n> — title` headings and
   `**Label:** text` fields. A marker line is neither, so it was swept up as
   body text on the entry above it. The markdown and the compiled JSON matched
   *perfectly* — both contained the same garbage. A consistency check cannot see
   a fault that both sides reproduce faithfully.
2. **`git add -A` stages a marker-carrying file without complaint**, and
   `git diff --name-only --diff-filter=U` then reports nothing unresolved. The
   index calls it resolved because you told it to. This bit the integrator a
   second time on 2026-08-24, on a different branch, and was caught that time
   only by grepping the text.
3. **The conflicting hunk had an empty other side.** It was a *positional*
   conflict over an entry both branches already had — no visible disagreement,
   nothing to prompt a careful read, and the obvious `--ours` reflex leaves the
   markers in.

**Fixed here.** The three lines are removed, `liberties.json` recompiled (181
liberties, unchanged count), and the mirror republished.

**Closed here.** `tools/test_no_conflict_markers.py`, wired into `check.sh` at
the top where it costs milliseconds: a deliberately dumb TEXT scan over every
tracked file under `chicago/4d` and `site/chicago/4d`. It asks nothing about
structure, because structure is what missed it. It refuses `<<<<<<< `, a whole
line of `=======`, and `>>>>>>> ` — and deliberately does NOT refuse a markdown
heading underline, a table rule, an indented divider, or prose that mentions a
marker mid-line, so it stays a guard rather than a nuisance. Its self-test
proves all nine of those, including that the tool does not trip its own scan
(the patterns are built from `"<" * 7` rather than written out).

Verified against the real fault: run on the unrepaired tree it named all three
lines with their file and line numbers; run on the repaired tree it clears 3,340
tracked files.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The markers are gone from `docs/LIBERTIES.md`, `data/liberties.json` and the
  published mirror, with no liberty text lost — **done**, L181 intact at 72
  lines, liberty count unchanged at 181.
- A gate refuses a conflict marker in any committed file under the app, and its
  own assertions are proved to fire — **done**.
- The gate is proved against *this* fault rather than a synthetic one — **done**.

**Still open, and deliberately not done here:**

- **`main` keeps the markers until the next promotion.** This fix lands on dev;
  production carries them until dev→prod is dispatched again. Not routed as a
  hotfix straight to main because it is cosmetic, and the hotfix lane exists for
  emergencies — but it is the reason to promote sooner rather than later.
- **The fleet's other apps have the same shape of exposure.** Every one of them
  compiles or parses an authored markdown/JS file (`js/changelog.js` above all)
  with a parser that recognises structure and ignores everything else. A marker
  in any of them would ride the same path. Worth a sweep in polecat-platform.
- **The scan is per-file text, not per-hunk semantics.** It cannot tell a
  correctly-resolved merge from a wrongly-resolved one — only an unresolved one.
  That is the honest limit of it, and it is the limit that would have been
  enough here.
