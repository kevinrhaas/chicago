---
id: T-0612
title: dev's gate is red: two merged readings raised no ceiling, and every branch after them inherits the failure
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: measure_research_spend.py --gate exits 0 on dev
needs_bake: false
closed_at: 2026-09-10T04:20:09.742Z
claimed_run: null
---

dev's gate is red: two merged readings raised no ceiling, and every branch after them inherits the failure.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0500 (PR #743) on 2026-09-04, and it blocks every branch opened after it.**

`origin/dev` at 37b93c3c fails its own gate. GitHub agrees: the `gate` check-run on that
commit is `failure`. The failing step is

    step "no research domain reads further ahead of the town than its baseline" \
      python3 tools/measure_research_spend.py --gate

and it reports two domains, neither of which belongs to the branch that finds it:

    directories:    6396 unspent, ceiling 4703 (+1693) — 6684 read, 288 ruled on
    newberry_index: 4825 unspent, ceiling 3148 (+1677) — 6817 read, 1992 ruled on

**How it happened.** The ratchet is doing exactly what it was built to do. Two readings
landed on dev within an hour of each other and neither raised the ceiling it spent:

* **#741, T-0506** — Fergus' 1839 directory read entry by entry. `directories` went from
  4,991 read to 6,684 and the ceiling stayed where T-0571 left it.
* **#740, T-0579** — the Newberry genealogical index, volume 3 (H-P). `newberry_index`
  went from 4,646 read to 6,817 and the ceiling stayed where T-0578 left it.

Both PRs are bot-opened, so the dev gate never ran on the PR itself; it ran on the push to
dev, after the merge, where nothing was watching.

**Why the finding branch did not just fix it.** A raise is not a formality — it is an
argument, in the `--why`, about why a particular reading could not be spent on names. That
argument belongs to the run that did the reading and knows what it read. A third party
inventing a justification for somebody else's 1,693 unspent entries is precisely the
corruption the instrument exists to prevent, and it would also bundle two other tickets'
bookkeeping into an unrelated PR. T-0500 stopped on `hold` instead and filed this.

**The unit.** For each of the two domains, decide and then do ONE of:

1. **Rule on the names.** If the reading really can be spent — the 1839 directory is a
   directory of PEOPLE, so much of it plausibly can — spend it in that domain's
   `crosswalk.json` and the number comes down on its own.
2. **Raise the ceiling with the reading's own argument**, from the ticket that read it
   (T-0506, T-0579), naming what would bring it back down:
   `tools/measure_research_spend.py --raise <domain> --why "..."`.

Do not `--rebaseline`: it writes the file once and then refuses, and it would launder both
ceilings plus every other domain's in one go.

**A SECOND DEFECT ON THE SAME HEAD, AND THIS ONE IS ALREADY REPAIRED.** `check.sh` also
failed at *sidecars derived from data/*: `data/sidecars/1835/residents_sources.json` no
longer compiled from the dataset, because #741 upgraded `fergus_chicago_directory_1839`
from tier 4 to tier 2 with a new citation and `what_it_supplies` and did not re-run
`python3 tools/compile_scene.py --all`. That one needs no argument and invents nothing —
it is a derived file catching up with data already merged — so PR #743 ran the recompile
and carries it. It is recorded here because it is the same fault with the same cause: a
gate that ran only after the merge.

**Also worth a line in this unit.** The dev gate ran only after the merge for both PRs
because bot-opened PRs do not trigger it. That is the reason two red merges could land
back to back without anybody noticing, and it is the same fault the steward prompt already
works around by running `check.sh` by hand. Whether the pipeline should require a
steward-run gate result before merge is the owner's call, and is worth putting to him
rather than deciding here.

**Acceptance**

- `python3 tools/measure_research_spend.py --gate` is green on dev, and `./tools/check.sh`
  passes on dev's HEAD. (The sidecar half of the red is repaired by #743; this unit owns
  the ceilings.)
- Whichever route each domain took is recorded where the next reader will find it: rulings
  in the domain's `crosswalk.json`, or a `--why` in `tools/research_spend_baseline.json`
  that says what brings the number down.
- Nothing minted, no confidence raised, and no ceiling raised for a domain this unit did
  not read.

**Links:** PR #743 (T-0500, parked on `hold` by this) · #741 (T-0506) · #740 (T-0579) ·
`tools/measure_research_spend.py` · `chicago/4d/docs/PIPELINE.md`
