---
id: T-0340
title: The bookseller's sign-name and its partners' firm-name are three gazetteer entries for one house
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 547
claimed_by: run 8/29/2026, 9:42:37 AM CT
blocked_on: null
needs_bake: false
---

Three gazetteer entries are one Chicago bookshop, and **T-0304 has just landed the machinery
that could join them** — `identity.json`'s `firm_merges`, with a `merge_rule` that must name
both spellings verbatim. Nobody has applied it here.

| entry | from | what survives |
|---|---|---|
| `business_chicago_wholesale_and_retail_book_stationary_store` | `1834-08-27#c002` | the heading, signature lost |
| `business_russell_clift` | `1834-09-03#c012`, `1834-11-12#c011`, `1834-12-03#c004` | both, or the signature |
| `business_russell_clift_chicago_book_and_stationary_store` | four *Chicago American* claims, 1835 | both, run together |

The first two come from ONE advertisement: the partnership notice of Aaron Russell of Boston
and Benj. [H.] Clift of Philadelphia, copy-dated 26 August 1834, opening a store adjoining
P. Carpenter's drug establishment on South Water Street. Which entry a printing lands in
depends only on which half of the type the segmenter kept. Neither name is a misreading — one
is the shop's sign-name, one is the partners' firm-name — so neither claim can be "corrected"
into the other, and T-0327 deliberately left them standing rather than hand-merge.

**The open question is T-0304's own partner-surname guard**, which refuses a merge unless the
two styles carry the same set of partner surnames. The sign-name entry carries NO proprietors
at all, because the printing that gives it lost the signature. Whether an empty set may merge
into `{Russell, Clift}`, or whether the guard should read "no CONFLICTING surname" instead of
"the same set", is the decision this ticket has to make — and it is a decision about the rule,
not about this shop, so it will govern every headline-only firm in the corpus.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The three entries compile to one, joined by a declared `firm_merges` rule that names the
  spellings verbatim — or the ticket records why they may not be joined, with the same care.
- If the partner-surname guard is changed, the change is argued in `identity.json`'s
  `firm_note` and its negative case is in the compiler's self-test.
- No claim's `business.name` is edited to force the join.

Links: T-0304 (the rule), T-0327 (which found the pair), T-0339.

**RESOLVED (PR #547) — and the premise above was wrong, which is the useful part.** The
guard never saw an empty set: `firm_surnames` runs on the NAME, so it read the sign-name as
three partners, `{book, store, wholesale}`, and reported that they differed from
`{clift, russell}` — surnames no printing ever carried. The compound style read as four.
So the decision is two-part. THE RULING: a style that names no partner cannot contradict one
that does, because an empty set is not a different partnership but a printing that did not
say; the guard now compares only where both styles NAME partners. THE FENCE: since
`firm_style` recognises a trade tail by its lower case and a sign-name is a capitalised
trade, a style counts as naming none only where `identity.json`'s new `firm_sign_names`
declares it one — refused for any house a claim signs with a proprietor, refused when
`partners` + `sign` do not reconstruct the style verbatim, refused for a business no claim
carries, refused with no reason stated. Seven negative cases in `--self-test`; the first is
that an undeclared headline-only style is still refused.

A FOURTH key was found while joining the three: `business_russell_clift_the_chicago_book_store`,
the Democrat's 1835-08-19 notice naming their premises under the Morison's state agency. All
four are now `business_russell_clift`, nine mentions, 1834-08-27 to 1835-08-29, retiring the
survival liberty three of them separately claimed. Carried across and NOT tidied: that claim
reads the firm's own name as a proprietor, so 'Russell & Clift' stands in the merged
proprietor list beside Aaron Russell and Benj. H. Clift — filed as T-0398.
