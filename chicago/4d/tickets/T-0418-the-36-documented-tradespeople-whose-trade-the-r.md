---
id: T-0418
title: The 36 documented tradespeople whose trade the residents vocabulary has no word for
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0373
opened: 2026-08-29
closed: 2026-09-04
pr: 780
claimed_by: run 9/4/2026, 6:23:03 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T12:06:01.466Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33867108004
---

`data/residents/` speaks a CLOSED occupation vocabulary and
`tools/compile_register.py`'s `TRADE_TO_OCCUPATION` is the whole of the translation
into it — deliberately a table rather than a matcher, because a fuzzy trade match
would silently retire an invented household on a word that happened to collide.

The cost of that table is measurable now. 36 people in the newspaper
register arrive with `occupation: null` NOT because the papers are silent about their
trade but because the vocabulary cannot say it. T-0373's pass refuses every one of
them rather than minting a documented tinsmith as trade-less — losing the trade the
corpus prints is not the same as declining to invent one — so they are held here:

- Aaron Russell — bookseller, stationer
- Barry, W. T. — postmaster general
- Botsford, J. K. — sheet iron worker, stove manufacturer, tinsmith
- Bradford, Harriet — administratrix
- Clark, Timothy J. — appraiser
- Cornelius C. Van Horn — justice of the peace, postmaster
- E. Kirby Smith — army officer, post adjutant
- Edward Simons — provision dealer
- George Smith — keeper of the Exchange Coffee House
- Hiram Hugunin — insurance agent, master mariner
- J. A. Collett — refectory keeper, restorator keeper
- J. Allen — harbour agent
- J. F. Wight — steamboat owner
- J. Green — Major, 5th Infantry, commanding the post, army officer
- James Whitlock — Register of the Land Office, register, United States Land Office
- Joseph Duncan — Governor of Illinois
- Josiah Stillman — militia officer
- L. F. Arnold — postmaster
- L. T. Jamison — Lieutenant, U.S. Army, acting commissary of subsistence, army officer, assistant commissary of subsistence
- Lieut. Allen — army officer
- M. Jones — founder, stove dealer
- Peacock, E. — judge of election
- R. Kenworthy — ventriloquist
- Richard M. Young — Judge of the fifth Judicial Circuit
- Samuel Miller — agent
- Silas W. Sherman — Sheriff of Cook County
- Silvester Marsh — provision dealer
- Stephen Forbes — sheriff
- Stephen M. Salisbury — justice of the peace
- Sweet, Richard M. — appraiser
- W. G. Blanchard — house and land agent
- W. Keeney — tinsmith
- Walker, James — justice of the peace
- Walker, Jeremiah — appraiser
- Wm. Jones — founder, stove dealer
- Wm. Payne — mechanic

Some of these are the town's OFFICES rather than its trades — a sheriff, a postmaster,
a justice of the peace, the Register of the United States Land Office. Whether
`data/residents/` should carry an office at all, or carry it somewhere other than the
occupation field, is the first question and it may be the owner's.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Every printed trade in the list above either gains a period-correct word in the
  residents vocabulary, or is written down with the reason it cannot have one.
- No trade is mapped to a near-miss word the paper does not give the person; the
  milliner-compiled-as-miller fault T-0376 found is the standard to stay clear of.
- The people the mapping unblocks are minted by the pass that owns them
  (`tools/mint_documented_residents.py` for a trade, `tools/mint_placed_residents.py`
  for the rest), re-derived rather than typed in, and `tools/check.sh` stays green.
