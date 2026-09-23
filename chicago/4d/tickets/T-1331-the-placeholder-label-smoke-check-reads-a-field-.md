---
id: T-1331
title: The placeholder-label smoke check reads a field that does not exist, so parts 2-3 have been permanently red on a typo
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-20
pr: 1604
claimed_by: run 9/20/2026, 8:02:29 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T01:57:19.120Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35549436682
---

The placeholder-label smoke check reads a field that does not exist, so parts 2-3 have been permanently red on a typo.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1330, 2026-09-18**, running `SMOKE_VIEWPORT=desktop SMOKE_STAGE=3` against a
diff that touches nine resident cards and no asset at all.

`tools/smoke_renderer.mjs:7218` reads `placeholder.whereholderFlag`. The object built twenty
lines above it has `placeholderFlag`; there is no `whereholderFlag` on it and never was. So the
assertion is `undefined === (placeholder.recommended === true)`, which for an asset that is not
a placeholder is `undefined === false` — false, always, on every tree.

    FAIL desktop 1280x800: the placeholder label agrees with the asset it describes —
    {"real":false,"realFlag":false,"recommended":false,"placeholderFlag":false,
     "grade":"reconstructed","reconstructionFlag":true,"flagNamesTheGrade":true}

The check is the half its own comment says was missing — "placeholder massing is claimed when
the asset IS one, and — the half that was missing — never claimed when it is not". It has never
once made that test. It is on `origin/dev` today and a run can confirm it without a browser:
`git show origin/dev:chicago/4d/tools/smoke_renderer.mjs | grep whereholderFlag`.

**Why it matters more than a typo.** A permanently red check in parts 2-3 is a red every run
has to triage before it can read its own result, and `dev-smoke-state.json` records only the
FIRST failure of a leg — so this one has been hiding behind
`the invented-name programme left nothing behind on this layer` and does not appear in the
standing record at all. Two reds, one recorded.

**Acceptance:** the field name is corrected; the check then passes on a tree where the asset is
a real bake AND fails when a real bake is given a placeholder label (prove the second by
breaking it, in the file's own style); the leg is re-run and filed with
`tools/dev-smoke-state.mjs record`. If correcting it turns the assertion red for a real reason,
that is the finding and this ticket says so rather than deleting the check.

**Not this ticket:** `the invented-name programme left nothing behind on this layer`, the other
standing red in this leg (3 reconstructed people in the manifest, 0 on `hh_inf_cooper_north_04`).


---

## What was done (2026-09-21)

`tools/smoke_renderer.mjs` part 3 — two lines, one fix and one control.

**The fix.** `placeholder.whereholderFlag` → `placeholder.placeholderFlag`, the name the
object twenty lines above actually carries. The old comparison was
`undefined === (recommended === true)`; on today's tree that is `undefined === false`,
which is `false` on every branch that has ever run it.

**The control, and why the fix alone was not enough.** Not one asset in the town carries
`extras.placeholder` today — `grep -l '"placeholder"' assets/web/*.glb` returns nothing,
and `scene-loader.js` sets `assetIsPlaceholder` from that GLB field and from nowhere else.
So the corrected assertion reduces to "no real bake wears a placeholder label", and it
would read green on a renderer that had stopped emitting the label altogether. That is the
same shape of fault as the typo: an assertion that cannot fail. So the other direction is
MANUFACTURED rather than waited for — `sauganash_hotel` is told it is a stand-in, the card
is re-rendered through the real `popup.js`, the flag is read back, and the lie is withdrawn
and the card re-read to prove it was withdrawn. `assetIsPlaceholder` is a registry field the
loader writes and nothing re-reads from the file, so restoring it restores the truth and no
later check sees the mutation. That is the acceptance's "prove the second by breaking it".

**Acceptance, against what shipped:**

- the field name is corrected — yes, one character sequence, line 7377 as it now stands.
- passes on a tree where the asset is a real bake — yes, see the part 3 reading below.
- fails when a real bake is given a placeholder label — yes, and that is now a standing
  assertion (`a real bake told it is a stand-in is caught saying so`) rather than a
  one-time demonstration, so the next rename of the flag's wording cannot quietly retire it.
- the leg is re-run and filed with `dev-smoke-state.mjs record` — **PARTLY, and this is the
  one place the acceptance was not met as written.** `SMOKE_VIEWPORT=desktop SMOKE_STAGE=3`
  was started in the foreground and did not finish: it wedged after
  `the ground was conformed to the field, with nothing left over` and produced no further
  line in 30 minutes, with the node driver asleep on zero CPU and the browser still up. That
  is the `api.walker.teleport` / evidence-only-households block — T-1369's ground, about
  1,200 lines BEFORE anything this branch touches — and dev's own standing record already
  carries part 3 as `page.evaluate: Target page, context or browser has been closed`
  (2026-09-20T21:25, steward-runner, load 4.7).

  `dev-smoke-state.mjs record` DID take the wedge —
  `recorded desktop stage 3: killed (11 passed, 0 failed)` — and then the branch had to be
  rebased onto a `dev` that had moved (T-1368 x2, T-1466), and `dev-smoke-state.json`
  conflicted. The reading was dropped in favour of dev's copy rather than re-stamped,
  because re-running `record` after the rebase would have keyed a `killed` verdict to a tree
  hash the run never actually tested. The record's own convention is that a reading names
  the tree it was taken on; a wrong hash is worse there than a missing entry.

  So the changed lines were proved DIRECTLY instead, against the same published tree the
  leg serves, booting the same way and running this block and nothing else:

      {"real":false,"realFlag":false,"recommended":false,"placeholderFlag":false,
       "mislabelledFlag":true,"restoredFlag":false}
      FAIL  AS ON DEV (the typo): the placeholder label agrees with the asset it describes
      pass  FIXED: the placeholder label agrees with the asset it describes
      pass  FIXED: and a real bake told it is a stand-in is caught saying so
      pass  TEETH: a real bake wearing the label would fail the corrected assertion

  The first line is the standing red reproduced verbatim on this tree, which is what makes
  the other three mean anything: same page, same records, one field name apart.

**The other red in this leg is not this ticket and is still there.** `hh_inf_cooper_north_04`
is T-1369, claimed by another run as this was written. Part 3 therefore does not go green on
this branch — it does not currently run to completion at all — and what this ticket owns is
that the placeholder line is no longer one of its reds, and that `dev-smoke-state.json` —
which records only a leg's FIRST failure — stops having two reds and one entry.
