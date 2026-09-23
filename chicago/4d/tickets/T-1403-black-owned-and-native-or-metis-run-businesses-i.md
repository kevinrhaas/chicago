---
id: T-1403
title: Black-owned and Native or Metis-run businesses identified at the tier the evidence supports, so the Businesses view lists them on one filter and T-1177 reconstructs above an attested floor
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1182
opened: 2026-09-19
closed: 2026-09-19
pr: 1538
claimed_by: run 9/19/2026, 4:08:41 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T22:07:53.623Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35469360801
---

Black-owned and Native or Metis-run businesses identified at the tier the evidence supports, so the Businesses view lists them on one filter and T-1177 reconstructs above an attested floor.

Piece 3 of 5 of **T-1182 — Audit every attested and inferred business against the research: proprietors, partners, dates, primary and secondary premises, the Dec 1835 State census classes and the August 1835 American count — and raise an inferred business for every in-window trade that has none**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

The parent's clause 5, unchanged: every business whose proprietor the sources place in
either community (the Indian traders' houses, the interpreters, the barber, any firm a
register or biography so describes) carries `proprietor_community` at the tier the
evidence supports, so the Businesses view can list them on one filter; the attested set
is the floor T-1177 reconstructs above.

Measured on the layer as it stands: `proprietor_community` reads unknown 85, yankee 46,
new_york 41, other 10, british 9, southern 5 — and NOT ONE house in the Black, Native or
Metis terms of the resident layer's own closed vocabulary. That is the gap; the rule
that fills it is `data/residents/community.json`, never a surname.



**FINDING from T-1401, 2026-09-19.** `docs/RESEARCH/business-layer.md` still says
"`proprietor_community` is `unattested` on all 196, and stays that way until a source
speaks". T-1378 filled that field off `data/residents/community.json` and the sentence
was never moved; it is this ticket's to rewrite, with the real distribution beside it.
