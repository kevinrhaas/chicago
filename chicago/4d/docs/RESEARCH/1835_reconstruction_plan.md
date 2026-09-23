# The 1835 reconstruction plan — how the four bands come together

**Owner direction, 2026-09-17.** After the research spend is confirmed, analyse the known
population, reconstruct the missing residents and households, finish and reconstruct the
businesses, then build every missing structure so that *"every person in Chicago has a place to
live and a place to work"* — every invented element marked `reconstructed` with the reason, so a
later attested or inferred finding can replace it. This page is the map of the tickets that do
it; the tickets are the contract. Order is `tickets/QUEUE.md`; nothing here re-ranks it.

## The shape

```
1. RESEARCH SPEND ─────────────► T-1157 sign-off (GO / NO-GO)
                                        │
2. 1835 TOWN ANALYSIS      T-1158 tiers ─ T-1159 roster ─ T-1160 known profile
                            T-1161 population ─ T-1162 occupations ─ T-1163 households
                            T-1164 lodging ─ T-1165 arrival ──► T-1166 ORDER BOOK
                                        │
3. RECONSTRUCT RESIDENTS   T-1167 programme ─ T-1168 sex/age ─ T-1169 arrival
                            T-1170 named families ─ T-1171 modelled families ─ T-1172 re-admit
                            T-1173 trades ─ T-1174 women & children ─ T-1175 lodgers
                            T-1176 garrison ─ T-1177 cohorts ─ T-1178 transients ──► T-1179
                                        │
4. BUSINESSES              T-1180 layer ─ T-1181 view ─ T-1182 audit ─ T-1183 staffing model
                            T-1184 retail ─ T-1185 mechanics ─ T-1186 professions
                            T-1187 lodging/river ─ T-1188 civic ─ T-1189 staff ──► T-1190
                                        │
5. STRUCTURES   A ground   T-1191 N streets ─ T-1192 W streets ─ T-1193 terrain ─ T-1194 lots
                B seating  T-1195 policy ─ T-1196 programme ─ T-1197 redeal ─ T-1198 known ─ T-1199 reconstructed
                C build    T-1200 ─ T-1201 ─ T-1202 ─ T-1203 ─ T-1204
                           T-1205 ─ T-1206 ─ T-1207 ─ T-1208 ─ T-1209
                D finish   T-1210 fabric ─ T-1211 walks ─ T-1212 yards ─ T-1213 signs ─ T-1214 camps
                E close    T-1215 the town complete
```

## The three files everything converges on

| file | written by | read by |
|---|---|---|
| `data/reconstruction/1835_reconstruction_order_book.json` | T-1166; filled by every reconstruction tool | every band; the "Reconstructing the town" card |
| `data/reconstruction/1835_placement_policy.json` | T-1195 | seating, building, fabric, frontage and yard tickets; the face/end/fabric gates |
| `data/reconstruction/1835_address_book.json` | T-1198, T-1199 | the build tickets; "Go to" on every card |

## The rules that do not move

- **Three tiers, per attribute** (T-1158): `attested` cites a source; `inferred` reasons from
  evidence about this thing; `reconstructed` is invented within a stated model, carries a
  `basis`, a `seed` and a `replaceable_by`, and is recorded in `docs/LIBERTIES.md`. Nothing is
  promoted. A null is `unknown`, never `reconstructed`.
- **The order book is the quota.** A reconstruction tool fills a bucket through its own
  `--build` and cannot overfill it; two builds are byte-identical.
- **Real names before invented ones** (T-1159, T-1172): every name the corpus printed
  and withheld is offered first, under its own read name, with its evidence limit.
- **The standing constraint, as re-ruled 2026-09-17** (AGENTS.md): Native and Métis people,
  households, businesses and camps ARE reconstructed, evidence-bounded, only through T-1177,
  every record `review_required` + `touches_removal`, review by Native scholars still sought
  before release; Black residents, families and Black-owned businesses are identified on a
  `community` filter; no human figure is drawn (L1); the August gathering is not staged.
- **Documented zeros stay zero** (the bank, the lottery office, the lyceum of the State census).
- **The frame budget moves consciously or not at all** (AGENTS.md § the frame budget; T-1154):
  every build ticket measures before it pushes and says which it did.
- **Substitution, not deletion**: `substitute_reconstruction.py` retires a reconstructed person,
  firm or roof when an attested/inferred one matches its `replaceable_by`.

## Sizing

Fifty-nine tickets, each one run (`S`/`M`), owner-requested, inserted between RESEARCH SPEND and
SOUTH THROUGH TIME. Sections over fifteen tickets are lettered sub-bands (RESIDENTS A/B/C,
STRUCTURES A–E) so different agents can take a sub-band; the queue order within a section is the
dependency order. Build tickets are `needs_bake` and hand a successor on, T-0028's shape.


## The bands below the sign-off spend research; they do not start more

**Owner, 2026-09-18.** Bands 3, 4 and 5 read the layer bands 1 and 2 signed off and write
from it. They may not open a new reading of a source or file a ticket to do so.

A gap found while reconstructing goes into the order book as a quantity and into the
record's own `basis` and `replaceable_by`, which is what those fields are for. A
reconstructed value on thin evidence, labelled and replaceable, is the expected output.

The exception is a gap that makes the work impossible rather than uncertain: that is a
blocker on the ticket it blocks, and becomes a research ticket only if it survives there,
under the written-reason override the ticket budget requires.
