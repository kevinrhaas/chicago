# The T-0510 sweep, in the order it was run

Run from `chicago/4d/`. Each stage writes its intermediate to `/tmp` and the next reads it,
so the chain is re-runnable end to end and every number in the package README comes out of it.

| stage | reads | writes |
|---|---|---|
| `01_name_sweep.py` | `data/research/**`, `data/sources/**` | `/tmp/strict.json` — exact-name and justified-variant hits with 200-character context, per cohort member |
| `02_crosswalk_extract.py` | every `*crosswalk*.json` / `*spend*.json` under `data/research/` | `/tmp/xw.json` — the committed verdict records that name each member |
| `03_verdicts.py` | `/tmp/xw.json` | `/tmp/verdict2.json` — each record classified agreement / candidate / documented refusal |
| `04_adjudicate.py` | `/tmp/xw.json`, `/tmp/verdict2.json` | `/tmp/built.json` — outcome, summary, evidence and sources per person |
| `05_emit.py` | `/tmp/built.json` | the findings ledger, `T-0510_resident_research.csv` and the working workbook |

Stage 4 carries the readings taken by hand off Fergus's Historical Series 26-29 — those are
quotations, not machine output, and they are written into the script so the package is one
artifact rather than a script plus a lost chat.
