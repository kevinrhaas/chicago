# Glessner's roof course module, read on the early prints (T-3072)

T-3025 read the c. 1887 Cornell print's stable-roof courses at about 6.4 in, where the model
lays HABS's 1963 5 in exposure (L-glessner-roof-tiles-2203, carried back to 1904 as inferred).
Its reading was a ratio against the render's course, which was only 3.4-3.7 px.

**Acceptance, stated before the work:** the render's course is measured in a way that does not
depend on the texture's sampling. A second early picture is read. The question of whether the
roof was relaid between 1887 and 1963 is answered from the pictures. The 1904 module is ruled
with its reason, and the house is rebaked only if the module changes.

**Ruling: the 1904 module stays 5 in. Nothing is rebaked.** The c. 1887 print and the 1963
photograph count the same courses on the same slope, so the roof kept one module across those
years. HABS measured that module at 5 in. T-3025's 6.4 in came from the Cornell camera's scale
on that plane, not from the roof.

    python3 docs/RESEARCH/glessner-roof-module-T-3072/read_module.py    # writes readings.json

The script needs the gitignored GLB: `python3 tools/recover_glessner_v4.py --materialize`.

## 1. The period in roof-plane inches, without the render

The committed GLB lays every tile as geometry (64,930 of them). For a band of print columns,
a plane is fitted to the roof-tile vertices that project into the band through the picture's
solved camera. Each pixel's ray meets that plane, which gives the pixel a place on the slope.
Each column's intensities are resampled onto the slope's distance at 0.25 in. The course is
then the peak of the summed Hann-windowed spectrum, searched between 4 and 9 in. The same
reading on the GLB's own tile vertices returns **5.00 in on every band**, so the method recovers
the module where the answer is known.

| picture | plane (fitted pitch) | 5 in drawn as | print course |
|---|---|---|---|
| Cornell print, c. 1887 | stable west slope (42.5°) | 3.3-3.6 px | **6.55-6.66 in** |
| HABS photograph 1, 1963 | the same stable west slope | 3.3-3.4 px | **4.85-5.00 in** |
| HABS photograph 1, 1963 | long west roof (37°) | 2.1-2.2 px | 6.0-6.1 in, *at the sampling limit* |
| Taylor 2135, 1887-1889 | 18th Street roof (44.7°) | 2.9-3.3 px | **4.75-4.82 in** |

(`readings.json`, three or four column bands each.) The render's 5 in course comes out at
3.3-3.6 px on the Cornell plane, the same as T-3025's render periods (3.40-3.67 px), so that
render was not aliased. The question was never the render's sampling.

The decisive row is HABS photograph 1. It shows the **same plane** as the Cornell print, from
nearly the same corner. It was taken in the year HABS measured the roof at 5 in, and through
its camera it reads 5 in. The long west roof in the same photograph draws a 5 in course at about
2 px, so that reading is beyond what the print resolves and decides nothing.

## 2. The count, which no camera can bend

The period reading depends on each camera's scale on the plane. A count of courses between two
edges the print itself shows does not. The ridge is read at the foot of the cresting and the
eave at the plane's lower edge, on 4x strips at three columns of each print
(`same-plane-strips.jpg`; red marks the ridge rows, blue the eave rows). The courses between the
two edges are counted as the unwrapped phase of the band-passed column, over seven columns each.
A count does not change under any warping of the column.

| picture | columns | courses, ridge to eave | slope the camera puts there |
|---|---|---|---|
| Cornell print, c. 1887 | 1040 / 1060 / 1080 | 41.7 / 43.7 / 43.9 | 21.9-23.3 ft |
| HABS photograph 1, 1963 | 1480 / 1500 / 1520 | 40.6 / 41.6 / 42.7 | 16.9-17.6 ft |

The two prints count the same courses, a mean of 43.1 against 41.6, within 4 %. The columns of
the two prints do not fall at exactly the same places along the roof, and the count rises along
the slope the same way in both. A 6.4 in course on the slope HABS's camera reads would show about
32 courses; the 1887 print shows about 43. **The stable roof was not relaid to a different module
between 1887 and 1963.** The two pictures cannot rule out a relaying in like tiles, but the
module is the question here and it did not change.

The two cameras disagree on the slope's length by a factor of 1.3, over the same courses between
the same two edges. HABS's camera gives 5 in to the course, matching HABS's own survey. The
Cornell camera's west-wall solve stands on reconstructed eave heights, and its match record
already carries that as an open residual. That camera, or the stable roof's plane as it meets it,
draws the slope long. This is filed as **T-3080**; it is a camera question, not a roof one.

## 3. The second early picture

Taylor 2135 (1887-1889), through T-3058's re-solved camera, reads **4.75-4.82 in** on the main
house's 18th Street roof. Its courses are drawn at about 3 px, so this is a supporting reading
at the edge of what the print resolves, not a measurement. It is near 5 in and nowhere near
6.4 in. The *Inland Architect* plate has no solved camera for this house in the library and was
not read.

## 4. What changed

- `docs/LIBERTIES.md` L-glessner-roof-tiles-2203: the basis now carries the early readings, and
  the liberty is revised. Its decision and its `inferred` confidence stand. The early prints show
  the module was the same in 1887 and 1963, so its survival to 1904 is better grounded, but no
  source measures the 1904 roof.
- The Cornell and HABS 1 match records each carry the ruling on the module item. The record and
  the GLB are untouched.
- T-3025's README § 3 is left as written; its reading was honest, and this README answers it.
