# T-2529 — the phone's `light` tier back inside its ceiling down Prairie's east row

**The breach.** T-2434 (PR #838) found that on a phone, at `light`, the stand looking down
Prairie's east row from 1613 to 1621 (`oblique-north` in `tools/qa_k01_t2434.mjs`: eye
1394 E / −2979 N at 1.7 m, target 1414 / −3001 at 8 m) drew more than the 1,270,000
triangles `/1904/` allows at `light` (`GLESSNER_V4_LIGHT_TRIANGLES`). On published dev
4743bcf9e it read **1,370,993 triangles, 134 calls**.

## Where the triangles went (390×780, `light`, dev 4743bcf9e)

| reading | triangles |
|---|---|
| the frame | 1,370,993 |
| with nothing casting into the sun's map | 776,077 |
| with only the structure batches not casting | 803,017 |

So the structures' shadow pass was **567,976**, 41 % of the frame. Two easier trims were
priced first and rejected:

- **A shorter reach.** The sun's box at `light` is ±120 m around the camera. At 100, 90,
  80, 70 and 60 m the stand read 1,354,826 / 1,332,296 / 1,299,880 / 1,272,379 / 1,235,731.
  Even ±60 m would only just fit, and it would cut every phone's shadows off at 60 m.
  Shifting the box forward along the view made it worse (1,378,861 at +40 m).
- **Leaving fine materials out of the shadow pass.** The batches are keyed by shader, not by
  name. One bucket holds K12 brick, slate, sash, every draft material and more. Glass, the
  one honest candidate, cast about 12,000 triangles at this stand.

Turning each record off in turn gave its cost in both passes. 1619 Prairie cost 78,900
(39,450 drawn twice). **1620 Prairie, across the street and behind the camera, cost
68,723: its whole assembly, once, in the sun's pass alone.** The sun stands at 126.6°
(10:30 on 1 July 1904, 62.9° up), so that shadow falls north-west, away from everything on
screen. The other west-side houses beside the camera (1600–1616) were the same.

## The change

`renderers/web/js/shadow-casters.js` wraps each structure batch's `onBeforeShadow`. Before
three's own cull against the sun's box, it checks every piece. Its bounding sphere is swept
along the sun's direction to 30 m below its base. The piece is left out of that one draw
only when the whole swept capsule lies outside a single plane of the view frustum, so no
point of its shadow can land on anything the camera sees. The test is conservative: it can
keep a piece it did not need, but it never drops one whose shadow is on screen.
Visibility is restored before the colour pass. `DETAIL.light.castersTowardView` switches
it on through `applyShadowTier`, and `full` and `balanced` are unchanged.
`__chicago4d.setCastersTowardView(on)` is harness-only, the same kind of switch as
`setFarMerge`.

## After (`node tools/qa_shadow_casters_t2529.mjs`, same held frame, cull off → on)

| stand | off | on | pixels changed | control: no shadows at all |
|---|---|---|---|---|
| front | 904,727 | 437,501 | 0 of 304,200 | 97,077 |
| oblique-north | 1,370,993 | **981,989** | 0 | 120,230 |
| oblique-south | 1,006,608 | 585,037 | 0 | 85,329 |
| rear | 1,045,246 | 862,867 | 0 | 29,848 |
| roof | 1,110,949 | 756,990 | 0 | 83,019 |

The control is the reason "0 pixels" means something. The same comparison, with the sun
casting nothing, changes 29,848–120,230 pixels at these stands. So the comparison can see a
shadow, and it found none missing. One harness draft took the control frame *between* the
two frames being compared. That left 268 pixels at the front stand off by at most 4 of 255,
because rebuilding the shadow map moved them. With the control moved after the comparison,
every stand reads 0.

Not claimed: a frame rate. This machine renders in software GL. The test adds one sphere
check per piece per frame on the CPU, the same kind of loop three already runs for its own
culling.
