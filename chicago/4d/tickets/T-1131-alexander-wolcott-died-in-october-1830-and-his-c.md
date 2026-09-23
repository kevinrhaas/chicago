---
id: T-1131
title: Alexander Wolcott died in October 1830 and his card reads present on 1 July 1835: the bracket's at-or-before leg is his own death notice
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-14
pr: 1348
claimed_by: run 9/14/2026, 10:42:28 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T04:52:12.069Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34925802959
---

Alexander Wolcott died in October 1830 and his card reads present on 1 July 1835: the bracket's at-or-before leg is his own death notice.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1117, which ruled the 1833 tax list a property roll and withdrew thirteen cards
from `present` to `uncertain`. `hh_wolcott_alexander` was the one card the ruling could not
reach, and it is the ruling's own star witness.

**THE DEFECT.** `data/residents/households/hh_wolcott_alexander.json` reads
`present_on_scene_date: present` for 1 July 1835. `tools/mint_civic_residents.py`'s
`presence_block` brackets the day from two records: `fdn0742`, the old-settler death notice
reading *"Wolcott, Dr. Alexander, Indian agent, died Oct. 25, 1830, aged 40; his will was
the first probated in Cook County"*, and a Fergus 1843 directory entry. The at-or-before
leg is therefore the man's own DEATH, and a death at a place is not a presence at it —
Andreas has his house *"left unoccupied by the death of Dr. Wolcott"* five years before the
scene date.

**IT IS A CLASS QUESTION, NOT A CARD ONE.** `data/research/old_settlers/death_notices.json`
already carries `places_in_1835: false` on every record, with the reason: the list's own
header admits it names *"some of Chicago's Old Settlers, prior to 1843, and other well -
known citizens who arrived after 1843, together with others prominently connected with
Illinois history"*. `presence_block` does not read that field. Nothing does.

**THE TRAP.** A death notice is not worthless to a bracket in every direction. A death
AFTER the scene date does say the man was alive to be at Chicago, which is what the
after-leg wants and is exactly what `hh_bronson_arthur` carried before T-1117 withdrew its
other leg. The refusal wanted is narrow and asymmetric, and if it is not, say so.

**Acceptance:**

- The rule is stated as a rule about a CLASS and reached from `places_in_1835`, which the
  domain already asserts, rather than from the one card that exposed it: which evidence
  classes may be an at-or-before leg of the presence bracket, which may be an after leg,
  and which may be neither.
- Every card the rule moves is COUNTED before it is written, and the count is in the PR.
- `hh_wolcott_alexander` is re-stated under the answer, `uncertain` and not `absent`
  unless a source actually places him elsewhere — his death does, and that is the one card
  here where `absent` may be the honest reading. Say which and why.
- The refusal fires in `mint_civic_residents.py --self-test`, asserts on the tree in
  `--gate`, and does not swallow the after leg with it.
- No card is hand-edited; `--check` re-derives byte for byte.
- `bash tools/check.sh` green. No bake.
