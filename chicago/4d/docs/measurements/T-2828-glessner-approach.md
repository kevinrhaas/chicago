# T-2828 — 1904 on a phone, walking up to the Glessner front

The owner's iPhone was killed about 5 s into Read frame pacing's walk from 1904's spawn
(`glessner_house`, the east sidewalk at E 18th, facing west) across Prairie Avenue; its
black box's last sample was 1390,-3220 — at the Glessner front — with 741 textures and
291 geometries resident, at Light, pixel ratio 1.

## Reproduced on the runner

`node tools/measure_memory.mjs --walk glessner-approach --only mobile [--picks 20]`:
/1904/ at the phone profile (390×780, Light, pixel ratio 1 — the boot the owner's phone
made), the eye stood every 4 m from the spawn to 1394,-3219.6, then 3 m from the east
face (1390.6,-3220) twice, then back at the spawn. The page reads **739 textures and 290
geometries** there — the owner's phone's state to within two of each.

**The runner stays under the ceiling, and nothing climbs toward the house.** At every
station GPU textures read 97.7 MB and GPU buffers 102.6 MB, flat; residency holds 56 of
63 sources (62.7 of 256 MiB) from the spawn to the front. What the walk does show:

| reading | before (dev 43d8f0a04) | after (T-2828) |
|---|---|---|
| 4 m west of the spawn, after the probe's GC (`--picks`) | 403.1 MB · arraybuffers 124.3 | 346.4 MB · arraybuffers 68.1 |
| 3 m from the front, after GC | 403.3 MB | 347.1 MB |
| along the walk, no forced GC, settled | 403.2 – 404.4 MB | 352.5 – 374.2 MB |
| arrival transient, no forced GC (first 1–4 stations) | 487.1 – 506.9 MB | 498.9 – 512.4 MB |
| /1904/ mobile spawn gate (`--gate`) | 408.1 MB (T-2806's reading) | 346.8 MB |

The largest thing the page held for nothing was **the GLB KTX2s' transcoded levels**: a
heap snapshot at spawn (`--retainers 45`) named `CompressedTexture.mipmaps` behind 40-odd
of the 45 largest ArrayBuffer paths, and an in-page census counted 62 compressed textures
holding 64.6 MB — 63 MB of it the GLBs' kit maps (`limestone_basecolor` 2048² at 6.7 MB,
the rest 1024² at 1.33 MB), each also on the GPU at the same size. Image bitmaps stopped
being held twice in T-2548; KTX2 levels never did.

## The fix

On a phone (`closeImages`), texture residency lets go of a GLB KTX2 source's levels once
every texture of it is uploaded, or at once while it is distant and drawn by its stand-in,
and keeps the KTX2 file its GLB carried (18.6 MB for all 63 sources) to transcode again
when the walk brings the source back. 63 sources released 77.6 MB at boot.
`--walk prairie-there-and-back` exercises the way back: 126 releases, 126 evictions, 63
retranscodes and 63 re-uploads, no residency problem, no page error, at most 364.8 MB.
GPU textures are unchanged at every station, so every picture is drawn as before and the
Glessner photo-match records are untouched.

## The gaze pick

`--picks 20` aims target.js's probe twenty times at every station and reads what was left:
GL textures, framebuffers, renderbuffers and programs, three's counts, and the pick's own
target, materials and stand-in pool. **Every station: made nothing**, heap kept ≤ 0.1 MB,
5–8 ms a pick. The walk now fails if a pick makes any of them.

## What is not settled

- **The arrival transient.** For the first seconds after the welcome the page carries
  about 130 MB of ArrayBuffers that are already garbage (201.8 MB before the first natural
  GC, 68.1 after) and the heap grows 5–7 MB a station until it is collected. Unchanged by
  this fix, and over the 400 MiB ceiling while it lasts. Filed after this ticket.
- **The phone's own ceiling.** These are floors (`measure_memory.mjs`: a driver's copies
  are not counted). Whether the walk now survives on the owner's iPhone is T-2733's reading.

Readings: `T-2828-glessner-approach-{before,after}.json` (with `--picks 20`),
`…-{before,after}-nogc.json`, `T-2828-prairie-there-and-back-after.json`,
`T-2828-memory.json` (the gate reading the ceiling is set from).
