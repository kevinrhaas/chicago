---
id: T-1398
title: The rebuild order made executable and gated as a fixed point: the converge stage runs every reader of the resident layer in the order that converges in one pass, and check.sh refuses a tree that is not at the fixed point
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1394
opened: 2026-09-19
closed: 2026-09-19
pr: 1526
claimed_by: run 9/19/2026, 11:02:36 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T16:44:16.221Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35452789948
---

The rebuild order made executable and gated as a fixed point: the converge stage runs every reader of the resident layer in the order that converges in one pass, and check.sh refuses a tree that is not at the fixed point.

Piece 1 of 3 of **T-1394 — The resident layer's closeout: the rebuild order made executable and gated as a fixed point over every reader of the layer, one liberty entry per stage with its counts, the People view's tier filter and reconstructed pills, and the research doc's final tables by tier**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. **The order is data, not prose.** `data/reconstruction/1835_resident_layer_rebuild_order.json`
   names every step of the rebuild, in order, with what it writes, what it reads, and why it
   sits where it does.
2. **It executes.** `python3 tools/converge_resident_layer.py --run` runs the order and then
   iterates the WHOLE order — never the step a check named — until every step's own `--check`
   is green, and refuses an oscillation by name rather than running forever.
3. **The gate holds the file honest**, and is wired into `tools/check.sh`: every step gated by
   check.sh, every declared path named by the tool that claims it, every back edge declared,
   and every gated re-derivation standing beside the layer classified into the order or out
   of it — so a NEW reader of the layer is red rather than discovered three passes in.
4. Each of those assertions has a self-test that breaks it and requires it to fire.

**Stop condition:** a run that has to converge the resident layer can read the order, run it,
and be told when it is not at the fixed point — without rediscovering the order from a ticket
comment.

---

**Finding (2026-09-19, working this ticket): the order recorded on T-1179 was wrong in three
places, and all three are the same mistake.** That finding's own closing sentence predicted it
— "the only authority on the current set is `tools/check.sh`" — and writing the order down as
DATA, next to what each step reads and writes, is what made the three visible:

* **`migrate_attribute_tiers` ran LAST, after the population profile — and the profile reads
  the table it writes.** `tools/profile_population_1835.py` line 77 reads
  `data/research/residents/attribute_tiers.json`; `tools/migrate_attribute_tiers.py` line 529
  writes it. So the profile was drawing every attribute tier from a table that predated its own
  rebuild. It is step 2 of the order now, above every reader of it.
* **`rebuild_resident_index.py --write` was in no version of the order at all.** The recorded
  lists name the tools that re-derive FROM the count of the layer and never the count itself,
  and `profile_population_1835.py` and `build_order_book_1835.py` both read
  `data/residents/index.json`.
* **Nor was the compiled layer.** `model_town_1835.py` counts `data/sidecars/1835/people.json`
  and `data/town_census.json`, both of which are compiled from the cards. The order starts with
  the model, so the model could be rebuilt from a sidecar the stages had already outrun — the
  T-1314 circle, one hop further out than it was written.

The last of those also corrected this ticket's own first draft. The data file declared a direct
back edge from `town_model` to each stage; `--check` refused it, because no stage writes the
sidecar or the census — the stages write cards, and two other steps compile them. The circle
reaches the model through two back edges rather than one of its own. A hand-written list would
have shipped that.

**What this ticket did NOT do, stated rather than left to be found.** Assertion D enumerates
the 40 tools that `check.sh` gates, name `data/residents`, and carry both a write mode and a
`--check` — every gated re-derivation standing beside the layer. Thirteen are in the order; the
other 34 are listed under `not_in_the_order.names` so that a FORTY-FIRST is red. They have not
been read one at a time. Most of them write INTO the layer from a source rather than deriving
anything from it, which is the opposite direction and is why the order does not run them, but
that is a reading of the set and not of each tool. The tripwire is on additions, not on this
backlog; classifying the 34 is a separate unit of work and nothing in the gate pretends
otherwise.
