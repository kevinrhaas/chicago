# Calumet's east walk at 20th, inside Full's budget (T-3012)

T-3008 found the desktop stand on Calumet Avenue's east walk at 20th Street, looking north,
at **4.63 M triangles against the 4.6 M Full budget**, and its own fifteen Calumet drafts only
30,476 of it. On today's dev it reads **4,739,066**. The ticket asked what carries the weight
(the Prairie east-side houses, the trees or the IC apron) and to bring the stand inside the
budget without cutting the background.

## What carries it

`node tools/qa_t3012_triangles.mjs` frames the stand as `tools/qa_draft_t3008.mjs` does and
charges every draw, the sun's pass included, to its layer, and every structure batch's draw
ranges to their records (`triangles-before.json`):

| layer | triangles | view | sun |
|---|---:|---:|---:|
| structures | 3,540,689 | 2,491,429 | 1,049,260 |
| — of which **Glessner House** | **2,006,494** | **1,421,694** | 584,800 |
| — Kimball, 1801 Prairie | 230,184 | 115,092 | 115,092 |
| — Keith, 1808 Prairie | 139,008 | 69,838 | 69,170 |
| — the fifteen Calumet drafts | under 10,000 each | | |
| railway (IC yard, rocks 194,000) | 630,789 | 590,435 | 40,354 |
| context city | 230,558 | 230,558 | 0 |
| terrain | 179,049 | 179,049 | 0 |
| street trees | 107,018 | 42,768 | 64,250 |

None of the three named suspects carries it. **Glessner does.** It stands about 290 m off,
inside the frustum and entirely hidden from it by the Calumet houses and their elms (see
`t3012-before-desktop-calumet-east-walk.jpg`), and its Full master still went whole to the
colour pass: its five granite batches alone 1.05 M, its tile roof 0.55 M.

## The change

Light has carried a conservative view filter since T-2227 (`view-occlusion.js`): a batch piece is
left out of the colour pass only when its whole box projects inside one opaque building
triangle, inset two pixels, and lies behind that triangle's plane. The sun's pass, picking and
instance visibility are untouched. Full now runs the same filter, unchanged. Balanced still
draws without it, because it stands inside its ceiling, and still collects the backing triangles,
because a Balanced -> Light switch keeps the same batches.

## Measured (published /1904/, desktop 1280x800, Full)

`tools/qa_draft_t3008.mjs`, same build with and without the change
(`browser-validation-t3012-{before,after}-desktop.json`):

| stand | before | after | within 4.6 M |
|---|---:|---:|---|
| east down 18th | 2,034,310 | 1,873,609 | yes, yes |
| between Prairie's east houses | 1,045,605 | 1,037,355 | yes, yes |
| **Calumet's east walk at 20th** | **4,739,066** | **2,921,468** | **no, yes** |
| air | 3,727,602 | 3,727,590 | yes, yes |
| load to ready | 34.9 s | 36.8 s | one sample each |
| JS heap after GC | 65.4 MB | 73.3 MB | Full's backing triangles |

No page errors or failed requests either way. The background is not cut: every draft and every
layer draws as before, and the filter removes only pieces hidden behind a building face.

## Pixel proof

`pixel-proof.json`: at eight stands (T-3008's four, and four around Glessner given as offsets from
its footprint's centre), the same frame is rendered with the filter off and on and read back
whole. **Seven are pixel-identical.** At `glessner-18th-nw` (45 m west and 32 m north of its
centre, on 18th Street) **3 pixels of 1,024,000 differ, by at most 6-7 levels of 255**, on the
shaded granite of the north front (`glessner-18th-nw-differing-pixel-off-on.png`, 48 px at 8x,
off left, on right). The filter-off frame rendered twice is identical there, so the difference is
the filter's, not the renderer's. Nothing appears or vanishes; it is a single-pixel tone shift
on one face.

## Found on the way

`glessner-prairie-se` (38 m east and 30 m south of Glessner's centre, on Prairie looking at the
house) reads **4,751,044 without the filter and 4,675,021 with it**, over Full's 4.6 M either
way, and `glessner-18th-nw` 4,720,756 without it (4,593,424 with). Glessner's own close stands
were over before this change; that is filed as its own ticket rather than hidden here.
