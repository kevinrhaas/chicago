---
id: T-0414
title: The street-face adoption refuses W. Montgomery a roof for being the bootmaker, and identity.json already ruled they are two houses
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-05
pr: 885
claimed_by: run 9/5/2026, 9:03:06 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T14:19:54.030Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33968829758
---

The street-face adoption refuses W. Montgomery a roof for being the bootmaker, and identity.json already ruled they are two houses.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured on `dev` while working T-0386, 2026-08-29.**
`tools/adopt_street_faces.py` refusal 3 — *"this face already holds this proprietor"* —
collapses businesses on a face by their normalised proprietor SURNAME SET. On South
Water Street that set is `{montgomery}`, so `L. W. Montgomery, boot and shoe maker`
adopts `recon_1835_blk_south_water_dearborn_a3_06` and **four** headings are refused
behind him:

| refused | mentions | first printed |
|---|---|---|
| `business_a_new_auction_and_commission_room_south_water_street` | 5 | 1835-07-08 |
| `business_w_montgomery` | 4 | 1835-07-08 |
| `business_w_montgomery_auction_and_commission_house` | 2 | 1835-08-05 |
| `business_montgomery_auction_and_commission_house` | 1 | 1835-06-24 |

Every one of them is W. Montgomery the AUCTIONEER, and
`data/research/newspapers/identity.json` § `refused_firm_merges` already holds the
ruling, `kind: "two_houses"`:

> 'W. Montgomery' and 'W. Montgomery, boot and shoe maker' are two houses and this is
> the trap the surname grouping was always going to set. […] a different trade, a
> different stand and eighteen months later.

So the placement pass is answering an identity question by refusing — which
`docs/STREET-FACE-ADOPTION.md` § refusal 3 says in as many words it must not do — and
answering it AGAINST a ruling the corpus already made and wrote down. The refusal
detail even cites T-0338 and T-0340 as the open question, when for this group it is
closed.

**What it needs.** Refusal 3 should consult the committed identity layer: where
`refused_firm_merges` declares two headings `two_houses`, the surname collapse must not
treat them as one. The axis the ruling itself used is the TRADE — `occupation` is
`shoemaker` against `auctioneer` in the register — so keying the collapse on
`(surname set, occupation)` inside a surname group that carries a `two_houses` refusal
is derived from the ruling rather than invented. The three surplus auction headings
would then still collide with EACH OTHER and stay refused, which is right: whether
they are one house is the gazetteer's question, not this pass's.

**And it is not enough on its own.** South Water Street is out of supply — 19 roofs
front it, 14 free, 14 adopted — so un-refusing the auctioneer today would only displace
a better-evidenced business rather than seat a new one. This wants **T-0009**'s roofs
first, or it lands as churn. Size it as one run AFTER that, not before.

Found while working **T-0386**, which is blocked partly behind it.
