# Existing people for the first transport-body assignments

2026-10-18. Applies the owner's latest preference: use existing attested, inferred or reconstructed people before creating an anonymous generic identity. An existing person's identity grade never upgrades their appearance, clothing or particular action. This is a read-only candidate audit; no instance or placement is authored.

## First recommendation: Otis Bardwell, existing reconstructed teamster

**Person `rc_bardwell_otis`; household `hh_rc_bardwell_otis`**, `data/residents/reconstructed_trades/hh_rc_bardwell_otis.json`. Already present in `data/sidecars/1835/people.json`: `present: present`, `grade: reconstructed`, occupation teamster, west division. Record gives male age band **20–29**, reconstructed, not a birth year. Assign the first reusable 1835 work-adult body to **this existing person**, rather than adding an anonymous adult or forcing Mark Beaubien into a teamster role.

The record is unusually explicit about its limits: name **invented**, not found in a document; age/sex/division/trade ordered by `1835_reconstruction_order_book`; teamster share comes from `fergus_1839_trade_table`, a population-model use of a later directory, consciously read back onto1835. This does not claim an attested1839 Otis Bardwell was an1835 teamster. Existing ticket basis T-1347 / parent T-1173. The model and name pools are actual recorded model IDs, not source IDs to invent in `data/sources`.

Its `employment` names `biz_john_s_kinzie_forwarding_and_commission_merchant` as a **reconstructed staffing seat**, explicitly not an attested workplace association. Do not present him as a documented Kinzie employee. Follow the household's seed/retirement rule: a real sourced person of the relevant trade/division can replace the reconstructed slot.

**Appearance assignment:** original reconstructed adult within20–29, reconstructed1835 work clothes bounded by `generic-human-period-clothing.md`; no portrait/likeness exists or is claimed. Community label is itself reconstructed; do not use it to invent facial features or culturally diagnostic clothing. Body may be reusable, but his person-card identity remains stable and independent from asset mesh ID.

**Action assignment:** wagon driver, standing near a wagon/horse and walking are reasonable **reconstructed demonstrations**, not a sourced observation of this invented individual's day. Horse riding is another reconstructed pose requiring separately fitted/sourced riding tack; teamster occupation does not prove a particular saddle, riding skill or mount. No placement in1904 or1812 is authorized by this1835 record.

## Existing1835 alternatives

| Person / household | Existing record and grade | Useful role / limits |
|---|---|---|
| `rc_newell_samuel` / `hh_rc_newell_samuel` | `reconstructed_trades/hh_rc_newell_samuel.json`; reconstructed male20–29, south, teamster | Second work driver/stander/walker if a second identity is needed. Same explicit model/1839 trade-share basis; reconstructed employment seat `biz_john_h_kinzie`. No likeness. |
| `rc_gallagher_daniel` / `hh_rc_gallagher_daniel` | `reconstructed_trades/hh_rc_gallagher_daniel.json`; reconstructed male20–29, north, teamster | Another existing work-driver candidate; no need to mint a fresh generic identity. Reconstructed name/occupation/community and modeled `biz_john_h_kinzie` employment, not documentary biography. |
| `rc_dufresne_joseph` / `hh_rc_dufresne_joseph` | `reconstructed_trades/hh_rc_dufresne_joseph.json`; reconstructed male30–39, south, livery-stable keeper | Natural existing candidate for standing by horses, handling/leading or an explicitly reconstructed riding specimen. No source attests a specific action, garment, mount or likeness; no culture-specific depiction inferred from name/community. |
| `beaubien_mark` / `hh_beaubien_mark` | `households/hh_beaubien_mark.json`; attested tavern keeper; sources include `andreas_1884_v1`, voter/land records and other named citations | Good existing named standing/walking/tavern example; not a documented teamster merely because the tavern kept horses. Portrait/source rights remain unresolved in earlier audit; identity attested does not make a face attested. Not required for first transport adult. |

**Do not backdate later roles:** `cook_thomas`, `smith_william`, `reed_thomas`, `knight_john` and `foot_s` have transport occupations printed in1839 or1843 whose role rows explicitly say `covers_scene_date:false`. Existing1835 presence or another1835 occupation does not turn those later teamster/drayman roles into1835 facts. Prefer an explicitly reconstructed existing teamster over disguising a later role as attested.

## 1904: actual existing people, but no existing named driver

`data/sidecars/1904/people.json` currently contains **two people**, both from `data/residents_1904/households/hh_glessner_john_j.json`:

- **`glessner_john_j`, John J.Glessner**, attested, born1843; farm-machinery executive and1902 International Harvester vice president, cited to `habs_glessner_house_il_1015_data_pages` and `glessner_house_family_page`. Household has present-in1904 and home association at Glessner House from1887-12-01, with sources also including `glessner_story_of_a_house_1923`. Suitable existing identity for a **reconstructed standing/walking or passenger demonstration**, with age-appropriate appearance separately reconstructed unless a cleared dated likeness is obtained. **Do not label him a teamster or professional coachman** or claim a driving/riding event without evidence.
- **`glessner_frances_m`, Frances M.Glessner**, attested, born1848-01-01; household record documents activities, not a paid occupation. Suitable identity for an age-appropriate **reconstructed standing/walking/passenger** example, with garment and appearance evidence still required. This record does not attest she drove the photographed turnouts or rode a specified horse.

Important explicit negative evidence: the1904 household's `not_in_this_household` section states no source read for that record names a **servant, coachman or cook in1904**, so none is on the card. Do not turn an unnamed photographic attendant at the Harvey house into a Glessner employee, and do not identify an1880–1899 attendant as still present1904 without evidence. The visible Harvey coachman/footman image can supply a rights-pending dress/action lead, not a named eligible person.

**Selection decision:** reuse John or Frances for1904 walking/standing/passenger tests. For an actual1904 work driver, first extend research for an existing attested/inferred/reconstructed person of that era; if none can be resolved, a transparently reconstructed driver identity is a justified fallback, not a reason to move Otis Bardwell forward69 years or relabel a Glessner executive. This audit does not mint that identity or choose a name.

## 1812: no compiled person assignment established

Actual scene target is **1812-08-14**, per `data/scenes/1812.json`, not the1835 July1 date. Targeted inventory found no `data/sidecars/1812/people.json` or1812 resident root analogous to the1835/1904 people layer. Built-environment sources name John Kinzie through `kinzie_house_1812`, but the existence of a source-named house owner is not a portable person record with date-qualified presence/appearance/role. Likewise the Lee's Place record describes April1812 deaths; Liberty White and the unnamed/contested Frenchman must not be staged alive on August14.

**Selection decision:** research/mint a date-qualified existing historical identity (Kinzie household/fort civilian or another appropriate person) through the resident/person path before assigning an1812 actor. Do not import John H.Kinzie's1835 card as his father's1812 identity, backdate Mark Beaubien, or default to an unsourced generic teamster merely to fill this scene. No1812 work-driver/rider identity is established by this pass. Generic fallback is permitted only after that identity search cannot produce a suitable record, with explicit reconstruction and separate era clothing/tack evidence.

## Reusable body acceptance remains separate

Otis is the strongest immediate **identity assignment**, not a completed photographic appearance. Build against the existing portable-human skeleton/material/LOD contract, preserve the person-card binding and reconstructed grade, supply dated wardrobe bounds, and review actual close-up anatomy/materials, seated hands/reins, seat/footboard contact, walk stance and horse/stirrup fit. A body that passes skeleton/export tests still needs photographic visual review. A pose library can be reused among eligible people without claiming all had identical faces, clothing or observed actions.

This report uses actual records read and existing source references; no new portrait, garment plate or person image was opened. No new named likeness, cultural depiction, source record, model, person instance or production placement is authored.
