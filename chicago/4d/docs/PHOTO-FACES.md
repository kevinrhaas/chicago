# Photo faces: a person's own pictures as their face

The owner, 2026-11-14, after the Greys: he will want it easy "to add or generate a bunch of people
photos for you to apply to the existing people faces". This page is that path. One command does the
work; this page says what to hand it, what it writes, how to look at the result, and what is left
to a person. Liberty: `L-photo-faces-3553` (docs/LIBERTIES.md). Ticket: T-3553.

William and Sarah Grey (2010 Prairie Avenue, 1904) were the first two, made by hand over three
days (`L-grey-photograph-skin-3553`); the command runs the same tools in the same order.

## What you need

1. **A drawn person.** Their id must be in `assets/humans/web/hm08_variation_persons.json`
   (`python3 tools/photo_face.py PERSON --status` says whether it is, and what they already have).
2. **A four-view sheet of the head**, as the owner supplied for the Greys: one square picture,
   at least 800 px, on a white ground, cut in four:

   | top left | top right |
   |---|---|
   | front | the face's left side (turned to the viewer's left) |
   | **bottom left** | **bottom right** |
   | the face's right side | the back of the head |

   Neck and collar may show; clothing is left out of the skin. Even light, no hat, mouth shut
   (or `--mouth open` for a smile with teeth, as William's).
3. **A source record** for the sheet, `data/sources/<id>.json`, written by a person who has read
   the pictures. The command refuses to run without it and never writes one (AGENTS.md rule 1).
   It needs `rights_status: "cleared"`, `asset_use: "texture"` and an https `url`; copy
   `owner_grey_likeness_william_2026.json` and change every line. Say whose face it is. Never put a
   real volunteer's or a living person's face on a historical person without the owner's say; face
   datasets whose people consented to research only are ruled out.
4. **The sheet itself in kevinrhaas/chicago-evidence** (`evidence/<person or batch>/...`), with its
   SHA-256 in the source record. The repository keeps only what is baked from it.
5. **Tools:** Python with `numpy scipy Pillow mediapipe` (and the system's `libegl1 libgles2`), and
   MediaPipe's `face_landmarker.task` (float16 v1, Apache-2.0) from
   `https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task`.

## The command

```
python3 tools/photo_face.py PERSON --sheet SHEET.png --source SOURCE_ID \
    --model face_landmarker.task --age YEARS [--stand-in "STAND-IN, NOT <NAME>"] \
    [--mouth open] [--beard] [--sex male|female]
```

`--age` is the age of the face in the pictures (the renderer ages it to the person's own age at the
scene date). `--stand-in` when the pictures are of someone else: the card says that label.
`--beard` when a beard hides the jaw's outline. A run takes about five minutes on four cores
(a trial on 2026-11-15, William Grey's sheet put on Joseph Daniels and then taken off again: 4 min
20 s, every check green).

It runs, stopping at the first failure:

| step | tool | writes |
|---|---|---|
| portrait record (only if there is none) | MediaPipe on the front quarter | `data/humans/variation/portraits/PERSON.json` |
| fit the face to it | `tools/fit_portrait_face.py --person PERSON` | `data/humans/variation/fits/PERSON.json` |
| skin record (only if there is none) | | `data/humans/variation/skins/PERSON.json` |
| bake the sheet onto the fitted face | `tools/bake_likeness_skin.py PERSON --sheet … --detect …` | `assets/humans/web/likeness/PERSON_skin.jpg`, `PERSON_front.jpg`, the skin record's `texture`; with `--mouth open`, `data/humans/variation/smiles/PERSON.json` |
| the town's persons file | `tools/human_variation_kit.py` | `assets/humans/web/hm08_variation_persons.json` |
| checks | the three tools' `--check` | nothing |

A record that exists is kept: a portrait with a reader's marks, a traced profile or values read by
eye (the Greys') is fitted as it stands, and an existing skin record is baked again from the sheet it
names (the SHA-256 must match). Run it again after any change to either record.

## Looking

Serve `chicago/4d` and open, for a man (a woman: `asset=glessner_frances_m_1904`):

```
tools/human_variation_lineup.html?asset=glessner_john_j_1904&keys=PERSON&view=faces&aim=head&labels=0
    &dress=1&hide=%5Eheadwear&sunat=-0.6,1.4,4&sun=2.2&bg=%23ffffff&dist=0.8&look=0
```

Add `&yaw=…&pitch=…&roll=…` from the skin record's `cameras.front` to stand where the front picture
was taken, and `&smile=1` for a face that smiles. Compare it with the front quarter of the sheet
side by side. Then look in the town at the person's door, on a phone width too (the phone draws the
sheet at half size).

## When the eyes look dark from the front

If the lids rest lower over the eye than the front picture's, the picture's lashes and iris are laid
on them and the eyes look dark and narrow (William Grey's did). Set `"lid_skin": true` in the skin
record and run the command again: the picture's eye openings and lashes are kept off the lids, which
take the picture's own lid skin and are never lit as hair. Leave it off when the eyes already look
right: on Sarah Grey, whose picture's eyes are what make her eyes hers, it drew a pale ring round each.

## What is left to a person

- **The card's portrait** (optional): a `card` block in the portrait record (copy the Greys'),
  `python3 tools/cut_portrait.py PERSON SHEET` and `node tools/portrait_still.mjs PERSON`.
- **The photo match**: what the first bake gets wrong is worked down by hand, as the Greys' were
  (their records' `read_by_eye`, `fit_views` with a traced profile, `grow` settings). AGENTS.md
  rule 11's stopping rule applies: stop at what a visitor would notice.
- **A smile of its own** (the sheet's mouth shut, a separate smiling picture): write the skin
  record's `smile_view` by hand, as Sarah's, then run the command with `--smile PICTURE`.
- **The pull request**: a `changelog.d/<ticket>.json` entry, before and after pictures in the body,
  the gate.

## Limits

- **Two calibrated bodies.** The table of which skin vertex each MediaPipe point lies on
  (`data/humans/variation/mediapipe_hm08_landmarks.json`) holds `glessner_john_j_1904` and
  `glessner_frances_m_1904`, so a face is fitted on one of them by sex. A person drawn on another
  body wears the fitted values and the sheet on their own body, a few millimetres off. Calibrating
  another body is `tools/face_landmark_correspondence.py` on five renders of it.
- **One front picture.** The face's depth (its profile) comes from the fit's prior and the body,
  not from the side pictures, which only colour it.
- **Children.** No child's body is calibrated and no child has been tried.
- **Memory.** Each photo person costs about 225 KB to download, and about 5.7 MiB of texture memory
  on a computer (1.4 MiB on a phone, which halves the sheets). 1904 stood at 1,292 of 1,425 MiB on a
  computer and 426 of 450 MiB on a phone on 2026-11-14: room for a handful, not hundreds. Before a
  batch, faces must be held only for the people near the walker (see the timing note below).

## Timing a crowd

No graphics card was at hand on 2026-11-15, so a crowd was timed on Chromium's software renderer
(SwiftShader, four cores) as a proxy: twelve copies of one man side by side, faces view, dressed, ten
frames each, the median. Time that grows with the picture's size is shading; the rest is the
figures' geometry.

| twelve of William Grey, 1280 x 800 | frame | at 640 x 400 | shading | geometry |
|---|---|---|---|---|
| with his photo face (hair is his grown skin) | 5.2 s | 2.8 s | 3.2 s | 2.0 s |
| with a library face and drawn hair and beard | 7.2 s | 4.6 s | 3.6 s | 3.7 s |

So a photo face draws no slower than the face and hair it replaces; the drawn hair cards cost more.
Against a different man with a library face and short hair (Joseph Daniels) the twelve photo faces
took 18 % longer. A software renderer weighs work differently from a graphics card, so these say
only that the photo face's shader is not the problem. Memory is: see above. A timing on a real
card (a computer or phone in the owner's hands) is still to do before photo faces go wide.
