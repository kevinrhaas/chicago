# T-3206 — walks, gates and front boundaries of the worked 1800- and 1900-block Prairie houses

The owner, 2026-10-27: *"make sure that you have their walkways to their house correct and the
front gate/fence/borders and side fence/borders etc are correct photographic match. some you have
and they look good, others are missing, cant enter, or are just plain wrong"*.

## What was wrong

Measured in the published `/1904/` app before the change (`stills/walks-before.json`, both widths):
the walker reached every door (closest 0.02-0.33 m, no blocked frame), because only sidecar
footprints are solid. The "can't enter" was visual:

- **No walk** to any door but 1808's. A lawn (or bare ground) ran from the stoop to the street.
- **No front boundary at all** at 1801, 1811, 1812, 1815 and 1823, though each picture shows one.
- **Closed gates** across the walk at 1816, 1824, 1827, 1828 and 1901: the iron fence's entrance
  leaves stood shut, so the fence read as unbroken.
- **Wrong gates and ends**: 1824 had a 5.45 m single side leaf no picture shows; 1827's fence ran
  past the stone pier its photograph shows at the lot's south corner.
- 1834 had its low wall and north opening, but no walk to it.

## What changed

- **K14 walks everywhere.** Each house gets a K14 yard: lawn, a flagged walk from the stoop's foot
  to the inner edge of the public walk, and a service walk down the side passage where the
  pictures or the Sanborn sheet show one. Where a coping's opening is not in front of the stair,
  the walk turns behind the coping to it (1811, 1834).
- **Coping walls on K14 (`dress_open`).** `k14_yard` now dresses a yard behind K11's stone coping
  wall (before, a K14 yard needed a fence). K11's coping wall gained a south-end side return, and
  the fence gained an optional `fence_end` pier.
- **Gates open.** Entrance leaves stand at 70° on the five iron-fence houses.
- **The gate step** `tools/check_house_walks.py`, in `tools/check.sh` with a 13-case self-test.
  For every worked 1904 house, it reads the K14 walk from the GLB and checks four things. The walk
  must start at the stoop, reach the public walk, and have legs that meet. No leg may cross a
  fence line, gate-less run, coping run or stone post, or any sidecar footprint. The 1600 and 1700
  blocks are listed `PENDING` on T-3204 and T-3205. A pending house that starts to pass fails the
  gate until it is taken off the list.

## Per house

Boundary heights are above the walk. "Walker" is the closest the in-app walker came to the stoop's
foot, walking forward from the public walk, at 390×780 after the change (no blocked frames
anywhere). Pairs: `pairs/<house>.jpg`, before (left) and after (right) from the public walk,
1280×800.

| House | Picture(s) read | Walk | Front boundary (built) | Opening / gate | Side | Walker | Remaining gap |
|---|---|---|---|---|---|---|---|
| 1800 Glessner | — | own bake route | unchanged | unchanged | — | (not in the K14 gate) | left as built: no picture shows its walk, gate or coping wrong |
| 1801 Kimball | Taylor c1895 | 2.2 m flags, straight | stone coping 0.35 m on the street line, returned along 18th St | cut at the walk | coping return on 18th | 0.33 m | none; the HABS 1965 views postdate the coping (not shown) |
| 1808 Keith | (T-1883) | existing K14 walk | stone posts and rails (T-1883) | existing | — | 0.13 m | unchanged; already passed |
| 1811 Coleman-Ames | Chicagology, Glessner blog print, Inland Architect plate | 2.2 m flags, turned behind the coping | rock-faced coping 0.45 m: long run, opening s 7.6-10.0, 0.4 m block, gap, long run | open 2.4 m, a little south of the stair, as all three prints show | — (the prints show no opening at the passage) | 0.0x m | within tolerance (≤0.3 m registered on the stair) |
| 1812 Wheeler | Levy; c1888 view down the block | 2.0 m flags, straight | low pale coping 0.35 m | open across the stair's foot | — (house fills lot) | 0.31 m | none |
| 1815 Sears-Meeker | Chicagology square-on and oblique | 1.5 m flags, straight | coping 0.25 m with two 0.9 m square posts | 1.8 m between the posts | — | 0.0x m | posts 0.2-0.45 m off the camera's reading; **open**: a low set-back iron railing north of the walk, unexplained, not built |
| 1816 Henderson | Chicagology | flags, straight; cinder service walk | scroll iron fence on curb (kept) | entrance gate now open | side gate, cinder walk | 0.23 m | the fence's scroll pattern (pre-existing, in its match record) |
| 1823 Dent | 1883 album; Chicagology engraving | 1.5 m flags from the side stoop | coping 0.3 m with 0.75 m posts | between the posts at the side stoop | — | 0.03 m | none |
| 1824 Marsh | Chicagology automobile | flags, straight; cinder service walk | iron fence on curb (kept) | entrance open; side leaf 5.45 m → 1.6 m gate | side gate, cinder walk | 0.04 m | none |
| 1827 Doane | Chicagology exterior | flags from the 5 m porch flight; service walk | low iron fence (kept), now ending at a stone pier at the lot's south corner | entrance open | side gate | 0.31 m | the fence's scroll pattern (pre-existing) |
| 1828 | Chicagology automobile; Glessner partial | flags, straight; cinder service walk | iron fence on curb (kept) | entrance open | side gate, cinder walk | 0.26 m | within tolerance: the two pictures disagree (fence on curb vs low solid wall); the fence is kept |
| 1834 Jones | Chicagology (mirrored); Glessner | 1.2 m flags, turned north behind the low wall | low wall (existing) | the wall's existing north opening s 11.6-13.1 | — | 0.25 m | none |
| 1901 Ream | Chicagology 1898 front and south-west | flags, straight; service walk | scroll fence with tall stone posts (kept) | entrance open between the posts | side gate | 0.02 m | the stoop-cheek curve (open in its match record; not boundary) |

The match records of all eleven changed houses were re-run (`node tools/photo_match.mjs`), each
side-by-side was looked at again, and each record carries a T-3206 difference for its walk and
boundary (fixed, within tolerance or not shown). One is **open**: 1815's set-back railing. Per the
photo-ticket stopping rule (T-3153), no new per-house tickets are filed.

## Liberty

`L-k14-walks-1800-block-3206` (docs/LIBERTIES.md) covers each house's `form.yard`. It records
what is read from the pictures (the kinds of boundary, the openings, the open gates, 1827's pier,
1834's turn) and what is the kit's: walk widths, flags, service walks, coping sections, and
openings within about 0.5 m.

## Reproduce

    python3 tools/check_house_walks.py --report      # every 1904 house: ok / pending / why
    python3 tools/check_house_walks.py --self-test
    QA_TAG=after QA_VIEWPORT=desktop node tools/qa_house_walks_t3206.mjs   # needs site/4d published
