# T-1823 — what the fronts-only walks cost the frame (2026-10-02)

Measured with `tools/measure_detail_ceilings.mjs --against`, on the published mirror of this
branch against the published mirror of `dev` at `a55277b3`, both viewports, T-0135's five
stands, on the steward runner (swiftshader). The **delta** is the reading. The absolute
figures run hotter on this machine than on CI's: `dev` itself reads over every desktop
ceiling here, while CI passed desktop part 4 on 2026-10-01.

## The first build, and why it was not shipped

The first build put the new posts in each street's shared standing mesh (`frontage.js`
`standingChunk`). Two posts on Randolph and one on Lake, far to the west, stretched
those meshes' bounding spheres 120-170 m west. That carried them into the sun's shadow box at
`lake_at_canal`, so Lake's and Randolph's existing fences were drawn into the shadow map
as well:

| desktop, worst stand | dev | first build | delta |
|---|---|---|---|
| full | 1,542,404 | 1,588,706 | **+46,302** |
| balanced | 1,353,453 | 1,402,041 | **+48,588** |
| light | 903,259 | 904,347 | +1,088 |

`tools/measure_layer_share.mjs` placed the whole difference in `frontage` (+49,580) and
`sun` (+47,624). Each mesh in the layer was listed before and after. The two street meshes'
spheres moved from c=(448, 114) r=325 to c=(281, 114) r=492 (Lake) and from c=(440, 257)
r=343 to c=(321, 257) r=461 (Randolph).

## As shipped: the fronts-only timber in its own mesh

| desktop 1280x800 | stand | triangles | dev | delta | calls (dev) |
|---|---|---|---|---|---|
| full | Lake at Canal | 1,540,554 | 1,542,404 | -1,850 | 208 (205) |
| balanced | Lake at Canal | 1,353,889 | 1,353,453 | +436 | 191 (188) |
| light | Lake at Canal | 904,395 | 903,259 | +1,136 | 71 (69) |
| full | open aerial | 1,418,849 | 1,417,641 | +1,208 | 138 (134) |

| mobile 390x780 | worst stand | triangles | ceiling | delta |
|---|---|---|---|---|
| full | Lake at Canal | 1,403,728 | 1,460,000 PASS | -1,850 |
| balanced | Lake at Canal | 1,235,991 | 1,280,000 PASS | +436 |
| light | Lake at Canal | 805,535 | 825,000 PASS | +1,136 |

The new timber is about 1,200 triangles where all of it is in view (the aerial). At the worst
stand `full` falls by 1,850, because a farm-box wagon on Canal Street is refused off the
new crossing. The cost is three draw calls: the fronts-only meshes beside the town's
208 of 215.
