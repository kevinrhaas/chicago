# The 1835 lodging model

> DERIVED from `data/reconstruction/1835_lodging_model.json`. Regenerate with
> `tools/build_lodging_model_1835.py --build`; `tools/check.sh` re-derives both.
> Do not hand-edit.

**T-1370**, the first piece of T-1175. The town model says how many beds this town needed in total and says plainly that it "seats nobody in any lodging place and gives no boarding house a capacity of its own". This is the per-place half: how many of those beds stood in each house that is actually in the dataset.

It reads no source. It measures committed structure records and apportions figures the town model already owns, so the town totals are unchanged by construction. It seats nobody.

## What the town holds

| class | scheduled | built | unbuilt | ordinary | full |
|---|---:|---:|---:|---:|---:|
| boarding house | 42 | 7 | 35 | 9 | 21 |
| inn tavern | 10 | 9 | 1 | 9 | 35 |

`ordinary` and `full` are the per-place figures, which this model does not move: the 1840 household tail's p90 (9), p99 (21) and observed maximum (35).

## Every lodging place, and the beds apportioned to it

| place | class | standing | floor | ordinary | full | grade |
|---|---|---|---:|---:|---:|---|
| Rufus Brown's Boarding House | boarding house | named | 89 m² | 5 | 12 | reconstructed |
| Reconstructed H1 small boarding house #007 | boarding house | reconstructed | 119 m² | 7 | 17 | reconstructed |
| Reconstructed H2 medium boarding house #022 | boarding house | reconstructed | 165 m² | 10 | 23 | reconstructed |
| Reconstructed H2 medium boarding house #028 | boarding house | reconstructed | 195 m² | 12 | 27 | reconstructed |
| Reconstructed H2 medium boarding house #030 | boarding house | reconstructed | 173 m² | 10 | 24 | reconstructed |
| Reconstructed H2 medium boarding house #045 | boarding house | reconstructed | 190 m² | 11 | 27 | reconstructed |
| Reconstructed H1 small boarding house #005 | boarding house | reconstructed | 123 m² | 8 | 17 | reconstructed |
| Exchange Coffee House | inn tavern | named | 252 m² | 11 | 35 | reconstructed · clamped |
| Green Tree Tavern | inn tavern | named | 186 m² | 8 | 35 | inferred · clamped |
| Mansion House | inn tavern | named | 108 m² | 5 | 35 | reconstructed · clamped |
| New York House | inn tavern | named | 186 m² | 8 | 35 | reconstructed · clamped |
| Sauganash Hotel | inn tavern | named | 159 m² | 7 | 35 | reconstructed · clamped |
| Steamboat Hotel | inn tavern | named | 240 m² | 11 | 35 | reconstructed · clamped |
| Tremont House (the first) | inn tavern | named | 279 m² | 12 | 35 | reconstructed · clamped |
| Western Hotel | inn tavern | named | 329 m² | 15 | 35 | inferred · clamped |
| Wolf Point Tavern | inn tavern | named | 84 m² | 4 | 35 | reconstructed |

`floor` is the footprint times the storeys. `grade` is the weakest of the footprint and storey claims the capacity rests on — a bed count read off a reconstructed outline is reconstructed, whatever the building is called. `clamped` means a proportional share asked for more than the largest household the 1840 enumerator recorded (35) and was held to it.

Every inn tavern carries the same 35 in the `full` column, and that is the town model speaking rather than this one measuring. The model's crowded end for the class is 10 × 35 — the largest household the 1840 enumerator recorded, once per roof — so it already assumes every one of them full to that maximum and leaves floor area nothing to distinguish. Only the `ordinary` column varies here.

## Against the town model

Built places at their apportioned capacity, plus the unbuilt slots at the model's own per-place figure, give **468–1,232** against the town model's **468–1,232**. They agree, as they must: the apportionment preserves each class's mean exactly.

- The larger boarding houses programme is **7 of 42**: 35 slots hold no building yet, and the 315–735 beds behind them are scheduled rather than standing.
- The inns taverns programme is **9 of 10**: 1 slots hold no building yet, and the 9–35 beds behind them are scheduled rather than standing.

## Open questions

- **The 42 roofs behind the town's bed bracket are scheduled under the group name `larger_boarding_houses`, but 32 of them are families H1 and H2, which the family-archetype crosswalk calls a center-hall house and a merchant's house, and which the six such roofs already built record as `larger_one_and_a_half_story_house` and `merchant_or_professional_house`. Either the group name is wrong or the archetypes are.** If the records are right, the town model's 468-1,232 counts 32 dwellings as lodging places and the bed bracket is too high by most of its width. This model classifies on the records' own `function` and counts the programme both ways rather than choosing, because choosing would be answering a question that belongs to the files' own tickets. (T-1293, T-1196)
- **What staff each lodging place kept -- bar-keeper, hostler, cook, chambermaid -- is not here.** The business staffing model is T-1183 and it is open. A staff establishment written here would be that ticket's answer given by a tool with no licence to give it. (T-1183)

## Carried with no beds

- **Dr Temple's Building, Lake Street** — Lodging the roof programme does not schedule and the town model's bed bracket does not count. Recorded so T-1371 knows the rooms are here; not apportioned, because apportioning it would spend beds the programme allotted to a boarding house somewhere else.
- **Lake House (under construction)** — The record's own function says this building was still going up on 1835-07-01. A house that was not open held nobody, and giving it a capacity would put beds in a building site.
