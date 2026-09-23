# The fort-reach bank heights — three readings that disagree, recorded (T-0004 / K8)

**Run 2026-08-20.** The owner's K8 ask: *the banks look too low against the fort views
(10–20 ft with graduated slopes there). The dossier gives +2–4 ft at the forks — keep
those — but the fort stood on distinctly rising ground.* This memo is the "research
first" half: what every document actually says about how high the ground at Fort
Dearborn stood, why they disagree, and which reading the mesh follows. The ticket's
instruction — **record the disagreement rather than averaging it** — is the method here.

## The three readings

**1. The witnesses say about eight feet.** Lt. James Strode Swearingen, on the ground on
17 August 1803, measured *"the bank where the fort is to be built is about 8 feet high"*
(tier-1, the journal itself — `docs/RESEARCH/swearingen_1803.md` § 3). Gurdon Hubbard,
correcting *Wau-Bun* in 1881, put *"the ground at the fort"* at *"not over eight feet
above the River at its lowest stage"* (via `swearingen_1803.md` § 5, which left the two
eight-feets as "one line of arithmetic in the fort parcel, not taken here" — taken now,
below). Two witnesses, seventy-eight years apart, on the same number — and the later one
is a correction pushing DOWN against a romantic account, which makes it the strongest
anti-lithograph testimony this project holds.

**2. The reminiscence and the dossier say ten to twelve.** The fort *"stood upon a
flattened mound, formed by the curve of the river at its base on its three sides"* and
was *"as high as any other point, overlooking the surface of the lake"* (chicagology
prefire274; drloihjournal concurs). The modern site elevation is cited at 591 ft ASL.
Dossier zone 6 reconciles these as a flat-topped landform of about 300 × 300 ft at
**+10 to +12 ft, apex +12**, grade `inferred` — documented as existing, its height
inferred. Zone 12, beside it, carries Swearingen's banks as the one **documented** bank
figure in the box: +8.0 south / +6.0 north (the north figure itself a derived maximum —
`swearingen_1803.md` § 4).

**3. The pictures say more.** The two tier-5 fort views (`p4_0`, `p4_1` in
`data/sources/assets/prefire_views_kevin_2026_08/`) draw the stockade on a rising bank
that reads, to the owner's eye and to this one, like 10–20 ft with graduated slopes.
Both plates are retrospective pictorials bound by their directory's README: they may
drive massing and setting as `inferred` and may never drive a coordinate — and
`fort_dearborn_image_accuracy.md` has already caught this pair's genre conflating the
two forts (the flagstaff trap). A drawn bank height is a composition choice; the same
plate raises its viewpoint well above any standing person.

## The arithmetic that reconciles the first two, as far as it goes

Swearingen measured **the bank** — the rise from the water at the river's edge, where he
landed. The mound reminiscence describes **the landform behind it** — an apex standing
back from the bank, with the river "at its base". An 8-ft bank at the waterline and a
+12-ft apex ~50 m behind it are not in contradiction; they are a crest and a summit.
Hubbard's *"not over eight feet"* is harder: *"the ground at the fort"* reads most
naturally as the compound itself, which zone 6 puts at +10 to +12. **That conflict is
real and is not resolved here.** Possible outs — "at its lowest stage" measures from a
lower water surface than this project's summer datum; an 1881 recollection of an 1827
residence rounds down against Wau-Bun's exaggeration — are speculation, and neither is
taken. The disagreement stands on the record; the zone stays `inferred`; nothing is
averaged.

## What the mesh does, and what it deliberately does not

The mesh follows **the dossier**, which is this project's standing authority for the
ground (`terrain_spec.json`'s own `critical_caveat`: no contour survey of the 1835 town
site exists, so no land elevation here is better than inferred). Within zone 6's range,
this parcel moves the mound from the mid-range apex (+11.0, the first pass's choice) to
**the zone's stated apex, +12.0** (`rise_ft` 2.8 → 3.8): *"as high as any other point"*
is a superlative, and at +11.0 the mound stood under two feet over the sand-ridge belt's
+9.4–9.5 while zone 5 puts dune hummocks at +10 to +14.

Deliberately unchanged:

- **The bank crest stays at Swearingen's 8.0 ft** (zone 12, documented — the divisions
  `crest_profile`). The mound rises from it; it does not replace it.
- **The forks stay at their dossier heights** (2.4 ft south / 3.6 ft north, zone 13) —
  the ticket's own instruction, and Swearingen corroborates: *"the banks above are quite
  low."* Measured on the regenerated field: every changed cell lies inside the mound's
  75 m outer radius (2,169 cells, max +0.305 m); the forks are byte-identical.
- **The plates' 10–20 ft is refused as a build input.** Tier 5 cannot outbid a tier-1
  measurement or the dossier's own reconciliation; it is recorded here instead, which is
  what the ticket asked for.

## Measured, before → after (N-transect through the mound centre, E +1152.4)

| N | before | after |
|---|---|---|
| +150 | +8.45 | +8.50 |
| +170 | +10.83 | +11.73 |
| +190 | +11.06 | +12.06 |
| +230 | +10.93 | +11.93 |
| +250 (bank) | +9.02 | +9.86 |
| +260 (face) | +2.00 | +2.18 |
| +270 (water) | −3.58 | −3.58 |

After-shot from the plate's own stand (local 1145, 300, yaw 180°):
`fort_from_the_north_bank_2026-08-20.png`, against the before,
`fort_from_the_north_bank_2026-08-19.png`.

The north face now carries the full +12 ft to the waterline over about a 25 m run —
1:6.8, inside the 1:6 to 1:10 band the spec's `bank` block holds every shore to, and
"graduated" in exactly the sense the plates draw: a bank a track can climb (that track
is T-0099's, workable now that the bank stands). The gradient audit still passes
(plain max 0.468 ft per 300 ft chord) with the mound band itemised by name, as before.

## What this leaves open

- **Hubbard vs zone 6** — recorded above, unresolved. If the owner rules the witnesses
  outrank the dossier's reconciliation, the mound drops to ~+8 and the fort reads flat;
  that is a ruling, not a research gap.
- **Zone 5's dune hummocks** (+10 to +14, "white sand hills both to the north and
  south") are still not modelled anywhere; they are the sand-ridge belt's parcel, not
  the fort bank's.
- The plates' remaining fort-fabric gaps are already ticketed (T-0093 … T-0099).
