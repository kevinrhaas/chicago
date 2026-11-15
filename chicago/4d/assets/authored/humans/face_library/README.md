# Face library: the faces of CC0 MakeHuman skins (T-3553)

The owner, 2026-11-14: "build a library with variations that will work", then, asked which
faces to start from, "MakeHuman skins only for now" (no photographs of anybody).

Every drawn person wore one of three skin atlases, so every face had the same lips, lids
and lines under its own shape and complexion. This folder holds the face of each of 22 more
CC0 skin atlases, for the people who have no pictures of their own:

- `faces/<id>.png`: the face as the atlas has it, unchanged: the 512 by 512 pixel box
  `[1504, 800, 2016, 1312]` of the 2048 by 2048 map every hm08 body shares. The atlases
  themselves are not kept; `SOURCE.json` pins each by size, CRC-32 and SHA-256, with the
  pack it came from, so each can be fetched again.
- `materials/*.mhmat`: the material file of each atlas taken from MakeHuman's own system
  assets, unchanged. Its header is that atlas's licence statement ("explicitly released as
  CC0 in september 2020").
- `skins01.original.json`, `skins02.original.json`: the two community packs' own records
  of their assets, unchanged. Each kept face's row there says `"license": "CC0"`, with its
  author and its page. The community packs' material files are not kept and not used; each
  is read once for a licence line of its own, and `SOURCE.json` keeps its hash and any line
  found. One has one: the material file for `callharvey3d_midtoned_female` is MakeHuman's
  2016 material for the skin it was made from, reused with its AGPLv3 header. The face's
  `licence_note` in the record says why its atlas is read as CC0 all the same.
- `evidence/young_african_female.mhmat`: what that note cites, kept unchanged: MakeHuman's
  own material file for the skin that face's atlas was made from (a skin not used here),
  whose header releases it as CC0.
- `makehuman_system_assets.original.json`: the system pack's own record, unchanged, so the
  three packs' skins can be counted: 59, of which 22 are kept here. `SOURCE.json` pins all
  three records by SHA-256.
- `SOURCE.json`: where each face came from, its licence evidence, and the hash of its cut.

`data/humans/variation/face_library.json` is the editorial record: which faces, whose sex
and age may wear each, the rule by which they are handed out, and why each of the packs'
other 37 skins was left out (three of them were not fetched and not looked at; three more
are the same painting as a kept one, painted again only at the eyelids and nostrils).
`python3 tools/face_library.py` lays the faces on one sheet
(`assets/humans/web/faces/hm08_faces.jpg`), each brought to one tone where it meets the
skin round it; `--check` holds all of it; `--ingest` is how a face is added. A face added
or taken out changes the seeded draw, so some people then wear another face.

These are reusable material components. A face from this library is not anybody's
likeness and attests nobody's complexion, ancestry, age or health: the person's own
recorded complexion is laid over it. A pack's own name for a skin (kept in `SOURCE.json`
and in the material files' names, as the packs have them) is the pack's word, not a fact
about anyone who wears the face, and nobody is given a face by it. See liberty
`L-face-library-3553`.
