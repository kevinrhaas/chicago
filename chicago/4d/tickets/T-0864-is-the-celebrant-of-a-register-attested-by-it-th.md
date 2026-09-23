---
id: T-0864
title: Is the celebrant of a register attested by it? The priest who keeps the G2c St Cyr register is graded on Andreas alone
state: withdrawn
epic: PAPERS
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-06
pr: null
claimed_by: null
blocked_on: Duplicate of T-0841, filed first by PR #931 (T-0724), which is where the finding originated
needs_bake: false
closed_at: 2026-09-06T05:04:41.394Z
claimed_run: null
---

Is the celebrant of a register attested by it? The priest who keeps the G2c St Cyr register is graded on Andreas alone.

**WITHDRAWN — duplicate of T-0841.** PR #931 (T-0724) filed this finding first, in the run whose splitter fix made the priest visible to the ladder at all. Re-filed here from PR #954 without seeing it, because #954 was read against `dev` and T-0841 lives on #931's branch. The finding is not lost — it lands with #931, which also notes that `st_marys_baptisms_1833_1835.json` is in no reader at all.

**Acceptance:** a written ruling on whether the celebrant of a register is attested
BY that register. If he is, the appearances that carry it reach his identity and his
rung is re-derived with the movement reported. If he is not, his card says why the man
who kept the G2c source cannot be graded by it.

## Salvaged from PR #954, which was closed as a duplicate

#954 was a duplicate of #931 in its data, **except for two tickets** — this is the
second. Neither existed on `dev`. Verbatim from that branch:

> **Found while landing T-0724, 2026-09-06.** With N1 in place `st_cyr_john_mary` is
> finally visible to the ladder — and what the ladder says is **G5, on `town_layer`
> alone**. His card is graded `attested` and cites `andreas_1884_v1`, a volume of
> 1884.
>
> The oddity is that the St Cyr parish register — `st_cyr_register_ichr_v4`, the rung
> **G2c that grades 35 of this town's people** — is the priest's OWN book, and it names
> him on nearly every entry as the celebrant. It has never been read as evidence for
> him. Whether a register's celebrant is attested BY his register is a real question
> and not obviously yes: the rung is about a body of record naming a person in the
> town, and **the man who wrote it names himself**.

## Why this is worth a ruling rather than a fix

The tempting move is to say obviously yes and regrade him, and it is not obvious. A
register is evidence that the people it names were in the town; the celebrant's
presence is a premise of the document existing at all, not an observation the document
makes. The opposite reading is just as arguable — he signed each entry, on a date, in
a place, which is exactly what an attestation is.

**Both readings are defensible, so this is a ruling and not a derivation**, and it
should be written down once rather than re-argued by every pass that meets him. Note
the asymmetry it would otherwise leave: the source that grades 35 townspeople at G2c
cannot grade the one man who is on nearly every page of it.
