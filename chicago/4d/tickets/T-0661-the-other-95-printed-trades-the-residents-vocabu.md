---
id: T-0661
title: The other 95 printed trades the residents vocabulary still cannot say
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 810
claimed_by: run 9/4/2026, 4:06:25 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T21:33:41.737Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33918578062
---
Sweeping the whole gazetteer the way T-0418 swept its 36 finds 131 people who arrive
with a printed trade `compile_register.py` has no word for. T-0418 spent the 36 the
newspaper register held; about 95 remain, and they fall into coherent groups rather
than a long tail:

- **vessel masters** — ~10 people printed as `schooner master`, `ship master` or
  `sloop master`. The largest single group. (`master_mariner` already exists as a word
  since T-0418; only the needles are missing, and whether a master printed with no
  forename is a resident is the placement pass's question, not the vocabulary's.)
- **clergy** — `clergyman` and `Baptist pastor` against the existing `minister`.
- **the town's other offices** — `town clerk`, `president of the town trustees`,
  `secretary to the town trustees`, `clerk of the board of trustees`, `clerk of the
  circuit court`, `Public Administrator of Cook county`, `fire warden`,
  `railroad commissioner`, and the land office's OTHER officer (`receiver, United
  States Land Office` / `Receiver of Public Moneys`), whose Register half T-0418 gave
  a word to.
- **trades** — `livery stable keeper` / `liveryman`, `hatter`, `brewer`,
  `carriage and sleigh maker`, `confectioner`, `pedlar`, `innkeeper`, `engineer`.
- **offices of another government seat**, which belong with T-0418's refusals rather
  than with its words — `Secretary of War`, `Secretary of State of Illinois`,
  `circuit judge`, `colonel of the Cook county regiment`, `regimental adjutant`.

**Acceptance:** every printed trade in that 131 either gains a period-correct word or
is written down with the reason it cannot have one, in the same note T-0418 opened
(`docs/RESEARCH/occupation_vocabulary_1835.md`); the T-0418 ordering rule holds — a new
word fills a null and never displaces a reading the register already makes, proved by
an unchanged action ledger in `register_1835.json`; the people it unblocks are minted
by the pass that owns them, re-derived; `check.sh` stays green.
