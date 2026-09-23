---
id: T-0829
title: A repeated string in a provenance or coverage list is the same merge artefact as a repeated id, and nothing asserts it
state: open
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

A repeated string in a provenance or coverage list is the same merge artefact as a repeated id, and nothing asserts it.

## What T-0820 covers, and what it does not

T-0820 shipped `tools/check_unique_ids.py`, which asserts that no committed list
of OBJECTS carries the same `id` twice. T-0820's own acceptance also named
`data/research/*/coverage.json` → `declarations[].items[]`, and that one is NOT
covered: `items[]` is a list of STRINGS and the declarations carry no `id`, so
the shape rule does not reach it. All ten coverage files are clean today, so
nothing is broken — but nothing is holding them, either, and this is exactly how
the streets file drifted.

## Why the obvious rule is the wrong rule — this is the work

"No string appears twice in a string list" was measured over the whole tree
before this ticket was written: **222 kinds of string list, 28,331 lists, and
only 14 carry a repeat.** That looks like the same argument that justified
T-0820. It is not, and the 14 say why:

| file | key | repeated | verdict |
|---|---|---|---|
| `data/research/directories/claims/fergus_1843_civic.json` | `by_ward` | `0`, `2`, `3`, `7` | **correct** — one element per person, two people share a ward |
| `…/fergus_1843_civic.json` | `names`, `entities` | `John S. Wright` | **correct** — one man, two offices |
| `data/research/census_1840/resident_crosswalk.json` | `outcomes` | `candidate` | **correct** — one element per row |
| `tools/forb_clamp_baseline.json` | `_` | — | padding, not data |
| `data/research/newspapers/gazetteer.json` | `mentions` | 3 persons, below | **suspect** |

Most of these lists are MULTISETS — one element per row, and a repeat is the
data saying two rows agree. A blanket rule would refuse correct data, which is
the same mistake T-0820 avoided with `raised[]`. So the rule has to be scoped to
lists that are SETS OF IDENTIFIERS (provenance, coverage, citations), and
scoping means naming them — which reintroduces the stale-table problem T-0820's
"discovered, not listed" design exists to avoid. **Finding a discovery rule that
separates a set from a multiset is the actual work here**, and it is why this is
a separate ticket rather than a line added to the existing check.

One candidate worth trying first: a string list is a SET if every other list
under the same key, everywhere in the tree, is duplicate-free. `mentions` fails
that (3 of its lists repeat); `by_ward` passes it as a multiset. That is
discovered rather than listed, and it can be measured before it is trusted.

## The three suspect entries, which are not to be silently deduplicated

```
persons[339]   person_catton_mr             chicago_democrat_1835_07_01#c004  ×2
persons[1027]  person_isaac_clark           chicago_democrat_1834_07_09#c006  ×2
persons[2342]  person_uncertain_orinda_guryl chicago_democrat_1834_01_28#c001 ×2
```

Either the clipping was counted twice, or the id names a CLIPPING while the list
means a MENTION and one clipping mentions the person twice — the same
under-specification as T-0828's fence runs. **Which one it is decides whether
the fix is a deletion or a renaming**, and anything that counts mentions is
off-by-one until it is settled. Read the three clippings before touching them.

## Acceptance

- The three `mentions` entries are adjudicated against the clippings themselves,
  and the outcome is written down — deduplicated, or the id made mention-level.
- Whatever rule ships is measured over the tree first and does not refuse any of
  the multiset lists in the table above.
- `declarations[].items[]` in all ten coverage files is held by something.
- `tools/check.sh` carries it with a self-test, as T-0820's check is.
