# 1634 Prairie refined from the district draft to a K01 stone-front house under a flat roof (T-2350)

Piece 2 of T-2346. Piece 1 was T-2349, which taught the K05 roof kit the stone-front rowhouse's
flat roof (`k05.roof.flat_parapet`, sized to this house) and nothing else. This piece makes K01 build
that roof and stands 1634 on it.

The draft T-2334 stood is refined **in place**. `house_1634_prairie` keeps its id, its traced
main-body rectangle (13.75 m deep, 6.75 m along Prairie) and its placement. Its archetype changes
from `prairie_draft` to `k01_frontage`. The draft rules' `skip` names `s20-1634-f`, so the draft
builder does not stand a second building there. The frontage row names the house (`house_id`).
1634 has no stable on the sheet.

## K01 learns `k01.roof.flat`

`roof_form: "flat"` is new beside `"hip"`. All of it lives in `k01_frontage.Assembly.flat_roof`,
`k01_frontage_params._flat_roof` and a front-only branch in `k10_frontage._cornice`:

- **One closed solid, one K05 union, the way the hip is built.** It joins the deck, a body under it,
  two side parapets, the blocking course, the cornice box and the plain stacks. Every piece is
  K05's own element (`extrude`, `parapet_element`, `body_box`), laid in K01's frame.
- **The deck.** Its rear fascia stands on the wall head (the eave datum, 12.3 m), so the deck's
  soffit is the wall head. It falls 2° (the variant's own fall, inside K05's declared 1-5° band, now
  also the K01 contract's `flat` pitch range) from behind the blocking course to that fascia. Its
  high line is 12.97 m.
- **Parapets.** One on each side wall and a blocking course over the front, all level at 13.42 m
  (the high line plus the variant's 0.45 m upstand) and coped. The side parapets are brick. The
  blocking course is the front's stone (`_emit_shell` picks it by position).
- **The street cornice.** A box 0.6 m out from the front (`eave_overhang_m`), from the soffit line
  up to the deck's rear eave, ended flush with the side walls' planes. K10 lays its brackets and
  bed moulding along the **street front alone**, corner to corner, since the side walls rise into
  parapets.
- **Refused, not faked.** A flat K01 roof names no caps (no hip or ridge), no slate, no dormer, no
  K15 stacks (K15's draught rule reads a hip's covering), and **no rainwater**. K01's half-round
  gutter runs round a hip's eaves, and the deck's one eave, the rear fascia, waits for its own.
- **Two small kit openings, both opt-in.** A blank south wall (`side_bays: []`, here a party wall)
  carries no string course. A K08 bay may be laid in the front's own K02 fabric (`fabric:
  "front_stone"`), so 1634's bay is brownstone like its front, not the fixed limestone of
  `bay_stone`.

Every other K01, K12, K13 and K16 asset rebuilds to the same bytes (`k01_emit.py --check`; the
others re-emitted unchanged). Only their manifest input hashes moved with the generator files.

## What the house is

Read from sheet 20 (T-2328 trace `s20fp-1634-b1`, T-1840 census `s20-1634-f`): three storeys over a
basement ('3B'), brick with a stone front, attached to 1636, with a stone bay at the south end of
the front. Built:

- A K02 **brownstone** (`sandstone_brown`) street front, smooth-dressed over two rusticated base
  courses, on K03 common-brick side and rear walls.
- K06 two-over-two sash, under K09 cornice-hood lintels on the two lower storeys and K01's flat
  stone lintels on the third.
- The K07 door and stoop at the pair's north end.
- The sheet's stone bay as K08's rectangular bay (2.6 × 1.2 m, the kit's plan; the sheet draws
  3.0 × 1.25 m), three storeys, stopping under the cornice's brackets.
- The flat roof above, with two brick stacks against the party wall.
- **The south wall is the party wall with 1636 and is blank.** The north wall has three windows a
  storey over 1630's side yard, and the rear wall has two.
- Liberty `L-k01-1634-stone-front-flat-2350`. 1634 is retired from
  `L-draft-prairie-16-18-west-2334`.

**Why brownstone.** The sheet says only "stone". The Prairie library's text record `cgn-1634-text`
(Chicagology's 1634 page) quotes the *Inter Ocean* of 10 September 1890: "the brown stone mansion
No. 1634". That record is not a source in `data/sources/`, so `stone_front` stays reconstructed,
and its note says what the choice rests on.

## The image gate

The Prairie library was searched for 1634 on 2026-10-11. It holds a Robinson 1886 plate crop
(`cgn-1634-robinson-1886`, a site plan), the text record above, an 1880 auction notice and an 1893
headline. There is **no photograph, print or drawing of the building's appearance**, so there is no
camera to solve and the ticket carries no `## Image gate`. The 1890 text's "brown stone" is the one
reading of its appearance, and it is used.

## Not built

- **The three-storey rear wing** (u -6.5-0, v -0.5-4.25 in the record's frame; the draft's `r2`).
  The ticket asked that the draft keep standing only the wing. The draft builder skips a whole
  traced building or none of it, and `keep_out` would leave the wing as a second draft "house" whose
  street face lies in K01's rear wall plane. So, as T-2355 did for 1628, the wing is gone until
  T-2347 stands it on K01's rear wings (T-2343). It also runs 0.5 m past the main body's south
  side, which K01's wing rule refuses as it stands. The finding is written into T-2347. The
  southern rear window (s 4.6) stands where the wing joins.
- **Gutters and downpipes**, above.
- **The bay's size.** It is 0.4 m narrower and 0.05 m shallower than the sheet's, and centred 0.25
  m north of it, to leave K01's 0.3 m corner pier.

## After, the same stands (`tools/qa_k01_t2350.mjs`)

Actual published `/1904/` app, this branch. Desktop 1280×800 at full detail, phone 390×780 at
light. Stands: front (across Prairie), oblique from the south and north walks, rear (over the
yard), roof (the air). Both runs had 0 page errors and 0 failed requests, and every stand was
`withinBudget`.

| | load to ready | JS heap | draw calls | triangles |
|---|---|---|---|---|
| desktop | 30.8 s | 31.1 MB | 117-149 | 1.82-3.21 M |
| phone | 18.6 s | 31.1 MB | 83-114 | 399-688 k |

The master is 3.40 MB and the web derivative 1.44 MB. No *before* reading was taken this run. The
draft it replaces was 1634's one box with a wing and a bay. Frame times and load are software GL on
the runner, a relative reading.

## Limits

- No photograph of 1634 or of the pair has been read. Every form but the plan, the storeys, the
  stone front, its brown colour and the bay's place is the kits'.
- 1636, its partner, is still the draft until T-2348, so the pair does not yet match across the
  party wall.
