---
id: T-0229
title: The full and balanced ceilings are raised on the owner's decision, and the raise expires with T-0223's timber cull
state: done
epic: RENDERING
requested_by: owner
seen: false
effort: XS
legacy_id: null
parent: T-0223
opened: 2026-08-27
closed: 2026-08-27
pr: 414
claimed_by: run 8/27/2026, 3:54:35 PM CT
blocked_on: T-0223
needs_bake: false
---

The `full` and `balanced` scene-detail ceilings are raised on the owner's decision, and the raise expires with T-0223's timber cull.

    full      1,400,000 -> 1,425,000
    balanced  1,210,000 -> 1,260,000

**This ticket exists to take them back down.** It is the receipt for a decision
that was taken deliberately and is meant to be temporary, filed so that
"temporary" is a thing the queue remembers rather than a thing a comment claims.

## What was measured, and why the content is not at fault

T-0223's `tools/measure_stand_budget.mjs`, at the release smoke's own worst
stand — *Lake Street at Canal, east down the axis*, desktop 1280×800:

| tier | ceiling | measured | over by |
|---|---:|---:|---:|
| `full` | 1,400,000 | **1,412,120** | 12,120 |
| `balanced` | 1,210,000 | **1,252,802** | 42,802 |

And the layer table underneath it:

> `trees` draws **360,926** triangles out of the **181,900** the layer owns —
> the whole layer twice. **180,100** of that is the sun's pass over timber lying
> outside the ±240 m shadow box: **14.4 % of the entire frame**, casting nothing
> any pixel of the shadow map can hold.

So the frame carries roughly **four times** the headroom either ceiling needs,
in work the renderer should not be doing at all. `trees.js` builds the near
timber as four quadrant meshes spanning kilometres, and a mesh whose bounding
sphere merely touches the shadow box is submitted whole — there is nothing to
cull per-mesh until the timber is chunked. The guarding comment at
`mesh.castShadow = true` still says the shadow camera is *"only ±60 m around the
walker"*, which T-0115 made false.

## Why it was raised anyway

The nightly bake's `smoke (desktop, 3-4)` leg is red on **every** branch until
either the trim or the raise happens, so it reports nothing about the branch
under test — a gate that is red for everyone is a gate nobody reads. It also
blocks shipping: production cannot be promoted without a known breach. The trim
is real work rather than a flag, and the owner chose to unblock now and pay
later. That is a legitimate call and it is recorded as one.

## Where the numbers come from

Measured worst stand plus about 0.6 % — the smallest step that clears the breach
and leaves an ordinary parcel room. Deliberately **not** a round number, and not
sized to fit any particular record.

**This is the fifth re-basing of these ceilings.** The count is itself the
argument for T-0223, and it is written into `main.js` beside the constants so
the sixth is harder to reach for.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- T-0223's first step (cull the timber from the sun's camera) has landed.
- The worst stand is re-measured with `tools/measure_stand_budget.mjs` — not
  assumed from the 180,100 figure.
- `full` is back to **1,400,000** and `balanced` to **1,210,000**, and the
  measured worst stand is under both.
- The expiry note in `main.js` is removed with them, so the constants stop
  carrying a promise that has been kept.

**If the cull recovers materially less than 180,100**, this ticket does NOT
close by quietly keeping the raised numbers. That is a finding: it means the
breakdown was wrong somewhere, and the ceilings need re-arguing from a fresh
measurement rather than inheriting today's decision by default.

---

> **Corrected 2026-08-27, hours after it was filed (T-0231).** Every reference
> above read **T-0209** when this ticket was written — in the title, in `parent`,
> in `blocked_on`, and four times in the body — and T-0209 is a FLORA ticket
> about how far the sward's bloom reaches. It has nothing to do with timber, the
> shadow box or this budget. The measurement, the per-layer table and the costed
> cull are and always were **T-0223**.
>
> The numbers are untouched, because none of them came from the wrong ticket:
> `tools/measure_stand_budget.mjs` is real, the 180,100 and the 14.4 % are
> T-0223's own readings, and the owner's decision was to raise the ceilings
> bounded by the cull — which is what it still says. **Only the pointer was
> wrong, and on this ticket the pointer is the entire mechanism.** An expiry
> receipt blocked on the wrong ticket does not expire: it comes due when an
> unrelated flora ticket closes, and the ceiling stays up because the thing that
> was supposed to bring it down was never watching.
