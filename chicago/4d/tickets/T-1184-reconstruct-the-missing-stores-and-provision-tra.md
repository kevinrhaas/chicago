---
id: T-1184
title: Reconstruct the missing stores and provision trades: dry goods, groceries, hardware, drug, book and provision houses, packers and the market, to the order book's quota, each with a period firm style, a reconstructed proprietor household and a location class
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-19
pr: 1531
claimed_by: run 9/19/2026, 11:47:43 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T17:53:22.334Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35455936256
---

The owner, 2026-09-17: *"A reconstruction business will all have reconstructed real sounding
names like for example if you think we are missing a shoemaker, then give their business a name
like J L Smith, shoemaker or other correct business names for the period."* This is the first of
five reconstruction tickets, one per business group; they share one style guide and one tool
and differ only in their quota rows.

**The shared machinery (built here, reused by T-1185 … T-1188):**

- `tools/reconstruct_businesses_1835.py --group <group> --build|--check`: reads the order book's
  business buckets for the group, the occupation model's gap per trade, the roster
  (T-1159: a real read name with an in-window trade is used before a pool name), the name
  pools, and writes `data/businesses/authored/rcb_<…>.json` at tier `reconstructed`, each with
  `basis` (the bucket row and the rule), `seed`, `replaceable_by` (e.g. *"a register or directory
  firm of this trade on this street"*), and a `docs/LIBERTIES.md` entry (one entry per group,
  `Scope:` counted).
- **The period style guide** (`docs/RESEARCH/business-naming-1835.md`, written here from the 196
  attested firm styles): sole trader — `J. L. Smith, Boot & Shoe Maker`; partnership — `Smith &
  Jones`, `Smith, Jones & Co.`; a house — `New York Store`, `Eagle Tavern`, `Farmers' Exchange`;
  initials-and-surname as the papers print them; no anachronistic forms (no "Inc.", no "Ltd.",
  no brand words); goods lines in the advertiser's idiom ("Dry Goods, Groceries, Crockery and
  Hardware"). Surnames from the pools by the proprietor's community; a reconstructed firm never
  reuses an attested firm style or an attested proprietor's full name (collision check against
  the identity master).
- Each reconstructed business creates or adopts its **proprietor household**: a person from the
  resident reconstruction band (T-1173) with that trade, or — where that band has not yet
  filled the bucket — a new reconstructed head written through the same tool, counted in the
  order book, at tier `reconstructed`.
- **Location class** at creation: `street_only` on a plausible face (the placement policy of
  T-1195; stores to South Water, Lake and Dearborn; groceries to the approaches and Canal
  Street) — no lot, no roof; T-1199 seats it.

**This group's quota** (from the order book, brackets from the State census and the American):
stores of all kinds to bring the town to the census's shape by street (the census counts 44 stores
against 59 in the register — so this group is expected to ADD FEW general stores and to fill the
kinds the register lacks: the two missing druggists, the second silversmith/jeweller, provision
and grocery stores on the west and north sides, a second market stall/butcher, a confectioner,
a second baker); the packing/provision trade (Clybourne, Dole, Newberry & Dole are attested;
reconstruct only the hands, in T-1189).

**Acceptance:**

- The tool and the style guide land; the group's records build to the order book's quota, no
  more; `--check` re-derives; LIBERTIES entry with scope; counts printed by trade and street.
- Every reconstructed firm has a proprietor person id that resolves and a `locations[]` entry
  of class `street_only` or `unplaceable` with its reason.
- Visible: the Businesses view lists them under the reconstructed filter with their invention
  stated.

**Stop condition:** the order book's retail/provision buckets read filled, and every filled row
names a business record.

**Links:** T-1166 · T-1162 · T-1159 · T-1180 · T-1182 · T-1195.
