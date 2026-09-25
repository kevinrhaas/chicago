# Convergence coverage — which roles and which places reach 1 July 1835

Derived by `tools/report_convergence_coverage.py --build` (T-1144, acceptance 7) over `data/residents/households/`, the location reconciliation and the business register. Table: `data/research/convergence_coverage.json.gz`, 2,383 rows, one per person. Do not edit either by hand.

This report RE-DECIDES NOTHING. Every reach flag is copied from the derivation that owns it — `roles[].covers_scene_date` for a role, the reconciliation's `resolved`-at-`scene_date` grading for a home or a workplace, the firm's own `present_at_scene_date` for a business premises — so a row here can only be wrong if its source is wrong, and each of those sources is gated above this one.

Read the three verdicts apart. **reaches** — at least one row on the axis reaches the scene date. **limited** — the corpus makes claims on the axis and not one of them reaches the day; that is a preserved refusal and a finished answer. **none** — the corpus makes no claim on the axis about this person, which is a stated absence. Adding `limited` to `none` and calling the total a gap is the error this table exists to stop.

## Coverage per axis

| Axis | reaches 1 Jul 1835 | limited | no claim |
| --- | ---: | ---: | ---: |
| `roles[]` — trades, professions, offices | 138 | 190 | 2,055 |
| home (`lives_at`) | 181 | 664 | 1,538 |
| work (`works_at`) | 131 | 0 | 2,252 |
| other places — later addresses, business premises | 128 | 307 | 1,948 |

Of 2,383 people in 1,512 households.

| Axes reaching the scene date | People |
| --- | ---: |
| 0 | 1,970 |
| 1 | 287 |
| 2 | 90 |
| 3 | 33 |
| 4 | 3 |

## The rows behind the verdicts

**Roles.** 738 dated role rows across the layer; 160 reach 1 July 1835. By kind: `employment` 1, `office` 52, `profession` 84, `trade` 601.

**Places.** 3,006 location rows reach a person; 465 of them reach the scene date. By claim kind: `business_location` 153, `home` 2,242, `later_home_address` 119, `later_workplace_address` 361, `workplace` 131.

A person inherits his household's `home` and `workplace` rows — the claim is made about the roof, not about the man — and inherits a `business_location` row from every firm that names him as proprietor, partner or staff. That is why the location row count above is larger than the reconciliation's own: the same roof is carried to each of the people living under it.

## Presence, carried for reading

| Household presence on the scene date | People |
| --- | ---: |
| `absent` | 2 |
| `present` | 1,436 |
| `uncertain` | 945 |

Presence is not a fifth axis. It is the household's verdict (T-1144 acceptance 9, with the last dated sighting under it) and it is carried here only so a row can be read without a second file open. A man whose household is `uncertain` may still hold a role that reaches the day: the role is bounded by its own source, and the two bounds are different questions.

## Two rows, read out

**A person the corpus places on the day.** Col. Jean Baptiste Beaubien (`beaubien_jean_baptiste`, The Jean Baptiste Beaubien household), presence `present`, axes reaching: `roles`, `home`, `work`.

| Axis | Verdict | Rows |
| --- | --- | --- |
| `roles` | `reaches` | trader (trade, 1673–1857, reaches) · merchant (trade, 1833-12-17–1835-07-01, reaches) · public_administrator (office, 1833-12-17–1835-07-01, reaches) · militia_officer (office, 1834-09-03–1834-09-24, dated away) |
| `home` | `reaches` | home: jb_beaubien_homestead (reaches) |
| `work` | `reaches` | workplace: jb_beaubien_homestead (reaches) |
| `other` | `none` | — |

**A person no axis reaches.** [?] G. Abbot (`abbot_8_g`, The Abbot household — a name from the post office's letter lists), presence `present`, axes reaching: none.

| Axis | Verdict | Rows |
| --- | --- | --- |
| `roles` | `none` | — |
| `home` | `none` | home: no claim |
| `work` | `none` | — |
| `other` | `none` | — |

Reproduce: `python3 tools/report_convergence_coverage.py --check`.
