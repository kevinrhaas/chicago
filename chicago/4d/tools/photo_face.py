#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""One command from a person's photographs to their face in the town (T-3553). docs/PHOTO-FACES.md is its page.

    python3 tools/photo_face.py PERSON --status
        what the person has (portrait record, fit, skin) and what is still to do; writes nothing
    python3 tools/photo_face.py PERSON --sheet SHEET.png --source SOURCE_ID --model face_landmarker.task --age YEARS
        [--stand-in "STAND-IN, NOT <NAME>"] [--mouth open] [--beard] [--smile PICTURE] [--sex male|female]
        every step below, in order; a step whose record exists is kept as it is and only re-run

The owner, 2026-11-14, of the people after the Greys: he will want it easy "to add or generate a
bunch of people photos for you to apply to the existing people faces". The Greys took a dozen
tools run by hand over three days. This is that path as one command, for the next person:

  1. the person must be drawn (assets/humans/web/hm08_variation_persons.json has them) and the
     pictures' source record must be in data/sources/ with rights cleared and `asset_use:
     texture` (no source is ever written here: docs/PHOTO-FACES.md shows the record to write);
  2. the sheet is the Greys' kind: one square picture, four quadrants of the head, front at the
     top left, the face's left side (turned to the viewer's left) at the top right, its right side
     at the bottom left, the back at the bottom right, on a white ground;
  3. the portrait record (data/humans/variation/portraits/PERSON.json): written here if there is
     none, from MediaPipe Face Landmarker's points on the front quadrant (`mp_<index>` marks, on the
     body the correspondence table calibrated for the person's sex). One that exists is kept: it may
     hold a reader's marks, a side profile, values read by eye (the Greys' do);
  4. the face is fitted to it (tools/fit_portrait_face.py --person: the person alone);
  5. the skin record (data/humans/variation/skins/PERSON.json): written here if there is none (the
     four views, how the hair is grown, the liberty), and the sheet is baked onto the fitted face
     (tools/bake_likeness_skin.py --detect: the points are read again on every view);
  6. the kit's persons file is written again (tools/human_variation_kit.py), so the town draws it;
  7. the three tools' own checks are run on the result.

What it does not do: write a source record, a card's portrait still, a liberty, a changelog entry,
or put the sheet in kevinrhaas/chicago-evidence. The page says each. A new person's face rests on
one front picture's points, where the Greys' were also held to a traced profile and to values read
by eye; that, and the photo match after it, are a person's own work, not this command's.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PERSONS = ROOT / 'assets/humans/web/hm08_variation_persons.json'
PORTRAITS = ROOT / 'data/humans/variation/portraits'
FITS = ROOT / 'data/humans/variation/fits'
SKINS = ROOT / 'data/humans/variation/skins'
SOURCES = ROOT / 'data/sources'
MP_TABLE = ROOT / 'data/humans/variation/mediapipe_hm08_landmarks.json'
LIBERTY = 'L-photo-faces-3553'
# The bodies the MediaPipe correspondence table is calibrated on (tools/face_landmark_correspondence.py),
# one for each sex: a face is fitted on that body's own rest face.
BASE_BODY = {'male': 'glessner_john_j_1904', 'female': 'glessner_frances_m_1904'}
# The axes a face is fitted on: the Greys' own (each sex's), so a new face moves as theirs did.
AXES_FROM = {'male': 'pa1904_grey_w_l', 'female': 'pa1904_grey_mrs_w_l'}
SIGMA_PX = (3.5, 9.0)         # a point's uncertainty (the crop's pixels); the second below the nose's base of a face that smiles or wears a beard
SUBNASALE = 2                 # MediaPipe: the point under the nose
PUPILS = (('pupil_r', 468), ('pupil_l', 473))   # MediaPipe: each iris's middle
QUADRANTS = (('front', (0, 0)), ('left', (1, 0)), ('right', (0, 1)), ('back', (1, 1)))
SIDE_TURN_DEG = 80            # how far a side view is turned, read by eye, where the fit has no side camera of its own
GROW = {'max_cm': 8}          # how far hair may stand out (the Greys: 7 with a beard, 11 for a woman's knot)
GROW_BEARD = {'beard': True, 'beard_cm': 3.0}


def rel(p):
    return str(pathlib.Path(p).resolve().relative_to(ROOT)) if str(pathlib.Path(p).resolve()).startswith(str(ROOT)) else str(p)


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def run(step, *cmd):
    print(f'\n== {step}: {" ".join(cmd)}', flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        sys.exit(f'FAIL {step} (exit {r.returncode}); the files written so far are left for a look')


def person_row(person):
    rows = json.loads(PERSONS.read_text())['persons']
    if person not in rows:
        sys.exit(f'{person}: not a drawn person (not in {rel(PERSONS)}); a face is only made for someone the town draws')
    return rows[person]


def status(person):
    row = person_row(person)
    have = {
        'portrait record': (PORTRAITS / f'{person}.json').exists(),
        'fit': (FITS / f'{person}.json').exists(),
        'skin record': (SKINS / f'{person}.json').exists(),
        'skin baked': bool((json.loads((SKINS / f'{person}.json').read_text()).get('texture') if (SKINS / f'{person}.json').exists() else None)),
        'in the persons file with its skin': 'skin' in row,
    }
    print(f"{person} ({row.get('scene')}, {row.get('record')}; drawn as {', '.join(row.get('drawn_as') or []) or 'nobody yet'})")
    for k, v in have.items():
        print(f"  {'yes' if v else 'no ':3} {k}")
    if (PORTRAITS / f'{person}.json').exists():
        p = json.loads((PORTRAITS / f'{person}.json').read_text())
        marks = p.get('marks') or []
        print(f"  portrait: {len(marks)} marks ({sum(m['landmark'].startswith('mp_') for m in marks)} MediaPipe), body {p.get('base_body')}, "
              f"source {p.get('source')}{', with a traced profile' if p.get('fit_views') else ''}")
    print('  next:', 'nothing; look at the face (docs/PHOTO-FACES.md, "Looking")' if all(have.values()) else
          'python3 tools/photo_face.py PERSON --sheet SHEET --source SOURCE --model MODEL --age YEARS')
    return 0


def check_source(source):
    path = SOURCES / f'{source}.json'
    if not path.exists():
        sys.exit(f'source {source}: no {rel(path)}. Write the source record first (docs/PHOTO-FACES.md, "The source record"); '
                 'this command never writes one')
    s = json.loads(path.read_text())
    bad = [why for ok, why in ((s.get('rights_status') == 'cleared', 'rights_status is not "cleared"'),
                               (s.get('asset_use') == 'texture', 'asset_use is not "texture" (its pixels become the skin)'),
                               (str(s.get('url', '')).startswith('https://'), 'it has no https url')) if not ok]
    if bad:
        sys.exit(f'source {source}: ' + '; '.join(bad))
    return s


def read_sheet(path):
    from PIL import Image
    im = Image.open(path)
    W, H = im.size
    if abs(W - H) > 2 or W < 800:
        sys.exit(f'{path}: a sheet is one square picture of four views (front, left, right, back), at least 800 px; this is {W}x{H}')
    half = W // 2
    return im.convert('RGB'), {name: [qx * half, qy * half, (qx + 1) * half, (qy + 1) * half] for name, (qx, qy) in QUADRANTS}


def detect_front(model, img, crop):
    """MediaPipe Face Landmarker's 478 points on the front quadrant, read at twice its size, in the crop's pixels."""
    import numpy as np
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    from PIL import Image
    x0, y0, x1, y1 = crop
    big = img.crop(crop).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.LANCZOS)
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=str(model)), num_faces=1))
    r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(np.asarray(big))))
    det.close()
    if not r.face_landmarks:
        sys.exit('no face found in the front view (the top left quarter of the sheet)')
    return [(round(l.x * (x1 - x0), 1), round(l.y * (y1 - y0), 1)) for l in r.face_landmarks[0]]


def write_portrait(person, args, row, sex, sheet, crops):
    path = PORTRAITS / f'{person}.json'
    body = BASE_BODY[sex]
    table = json.loads(MP_TABLE.read_text())['bodies'][body]['points']
    pts = detect_front(args.model, sheet, crops['front'])
    loose = args.mouth == 'open' or args.beard
    below = pts[SUBNASALE][1]
    # The pupils first (the fit's camera starts from them): MediaPipe's iris middles, the person's
    # right eye being the one at the picture's left.
    marks = [{'landmark': name, 'x': pts[i][0], 'y': pts[i][1], 'sigma_px': 3} for name, i in PUPILS]
    marks += [{'landmark': f'mp_{i}', 'x': x, 'y': y, 'sigma_px': SIGMA_PX[1] if loose and y > below else SIGMA_PX[0]}
              for i, (x, y) in enumerate(pts) if f'mp_{i}' in table]
    axes = json.loads((PORTRAITS / f'{AXES_FROM[sex]}.json').read_text())['axes']
    rec = {
        'format': 'chicago4d_human_portrait_marks_v1', 'ticket': 'T-3553', 'person_id': person, 'scene': str(row['scene']),
        'source': args.source, 'scan': f'the sheet named by source {args.source} ({pathlib.Path(args.sheet).name}, SHA-256 {sha256(args.sheet)})',
        'scan_size_px': list(sheet.size), 'crop_px': crops['front'],
        '_doc': ("Written by tools/photo_face.py (T-3553): MediaPipe Face Landmarker's points (`mp_<index>`, in pixels of the crop "
                 "`crop_px` of the sheet named in `scan`) on the sheet's front view, each on the skin vertex the correspondence table "
                 "names for `base_body` (data/humans/variation/mediapipe_hm08_landmarks.json). The face is fitted to them alone: no "
                 "side profile, and nothing read by eye (docs/PHOTO-FACES.md)."),
        'base_body': body, 'sex': sex, 'age_at_picture_years': args.age,
        'age_note': 'The age of the face in the pictures, as the person adding them gave it (--age).',
        'grade': 'reconstructed',
        'basis': (f"The face's proportions are fitted to the front picture of source {args.source}. "
                  + ("It is a stand-in's face, not the person's: " if args.stand_in else "")
                  + "a reconstructed likeness (docs/LIBERTIES.md " + LIBERTY + ")."),
        'not_modelled': ['the face\'s depth (one front picture: its profile is the prior\'s and the body\'s)'],
        'axes': axes, 'marks': marks,
    }
    if args.stand_in:
        rec['stand_in'] = {'label': args.stand_in, 'card_note': f"No photograph of this person is known. The face is a stand-in's ({args.source}), not theirs."}
    path.write_text(json.dumps(rec, indent=1) + '\n')
    print(f'wrote {rel(path)}: {len(marks)} marks on {body}')


def write_skin(person, args, row, sheet_path, crops):
    path = SKINS / f'{person}.json'
    front = {'name': 'front', 'crop_px': crops['front']}
    if args.mouth == 'open':
        front.update(camera='upper_face', mouth='open')
    rec = {
        'format': 'chicago4d_human_likeness_skin_v1', 'ticket': 'T-3553', 'person_id': person, 'scene': str(row['scene']),
        '_doc': json.loads((SKINS / 'pa1904_grey_w_l.json').read_text())['_doc'],
        'source': args.source, 'grade': 'reconstructed', 'liberty': LIBERTY,
        'basis': (f"The sheet's four pictures of the head (source {args.source}) are laid on the face fitted to them, as its skin, "
                  "hair and eyes (tools/photo_face.py). " + ("They are a stand-in's, not the person's: " if args.stand_in else "")
                  + "a reconstructed likeness, and no evidence of how the person looked."),
        'sheet': {'scan': f'the sheet named by source {args.source} ({pathlib.Path(sheet_path).name})', 'sha256': sha256(sheet_path), 'size_px': [crops['back'][2], crops['back'][3]]},
        'views': [front] + [{'name': n, 'crop_px': crops[n], 'turn_deg': t} for n, t in (('left', -SIDE_TURN_DEG), ('right', SIDE_TURN_DEG))]
                 + [{'name': 'back', 'crop_px': crops['back']}],
        'not_shown': ['clothing (left out; the figure wears its own dress)', 'each iris mark for mark, and the catchlights'],
        'grow': {**GROW, **(GROW_BEARD if args.beard else {})},
    }
    if args.smile:
        sys.exit('--smile names a picture of the smile of its own: write its `smile_view` into the skin record by hand first '
                 '(docs/PHOTO-FACES.md, "A smile of its own"), then run this again')
    path.write_text(json.dumps(rec, indent=1) + '\n')
    print(f'wrote {rel(path)}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('person')
    ap.add_argument('--status', action='store_true', help='say what the person has and what is to do; write nothing')
    ap.add_argument('--sheet', help='the four-view sheet (a local copy)')
    ap.add_argument('--source', help="the pictures' source record id (data/sources/<id>.json)")
    ap.add_argument('--model', help="MediaPipe's face_landmarker.task (float16 v1)")
    ap.add_argument('--age', type=int, help='the age of the face in the pictures, years')
    ap.add_argument('--sex', choices=('male', 'female'), help="where the person's own record states none")
    ap.add_argument('--stand-in', metavar='LABEL', help='the pictures are of someone else: the card says LABEL ("STAND-IN, NOT ...")')
    ap.add_argument('--mouth', choices=('shut', 'open'), default='shut', help='the front view smiles with the mouth open (the face moves into it)')
    ap.add_argument('--beard', action='store_true', help='the face wears a beard (its outline is not the jaw)')
    ap.add_argument('--smile', metavar='PICTURE', help="the skin record's own picture of the smile (`smile_view`), where it names one")
    args = ap.parse_args()
    person = args.person
    if args.status:
        return status(person)
    missing = [f'--{k}' for k in ('sheet', 'source', 'model') if not getattr(args, k)]
    if missing:
        ap.error('to make a face: ' + ', '.join(missing) + ' (or --status)')
    row = person_row(person)
    check_source(args.source)
    sheet, crops = read_sheet(args.sheet)
    sex = args.sex or row.get('sex')
    if sex not in BASE_BODY:
        sys.exit(f'{person}: the record states no sex; give --sex')
    if not (PORTRAITS / f'{person}.json').exists():
        if args.age is None:
            ap.error('--age: the age of the face in the pictures (a new portrait record needs it)')
        write_portrait(person, args, row, sex, sheet, crops)
    else:
        print(f'keeping {rel(PORTRAITS / (person + ".json"))} as it is')
    run('fit the face', sys.executable, 'tools/fit_portrait_face.py', '--person', person)
    if not (SKINS / f'{person}.json').exists():
        write_skin(person, args, row, args.sheet, crops)
    else:
        print(f'keeping {rel(SKINS / (person + ".json"))} as it is (its sheet must be this one)')
    bake = [sys.executable, 'tools/bake_likeness_skin.py', person, '--sheet', str(pathlib.Path(args.sheet).resolve()), '--detect', str(pathlib.Path(args.model).resolve())]
    if args.smile:
        bake += ['--smile', str(pathlib.Path(args.smile).resolve())]
    run('bake the skin', *bake)
    run('write the persons file', sys.executable, 'tools/human_variation_kit.py')
    run('check the fit', sys.executable, 'tools/fit_portrait_face.py', '--check', '--person', person)
    run('check the skins', sys.executable, 'tools/bake_likeness_skin.py', '--check')
    run('check the kit', sys.executable, 'tools/human_variation_kit.py', '--check')
    body = json.loads((PORTRAITS / f'{person}.json').read_text())['base_body']
    print(f'\n{person}: done. Look at it: tools/human_variation_lineup.html?asset={body}&keys={person}&view=faces&aim=head&dress=1'
          f'&sunat=-0.6,1.4,4&sun=2.2 (docs/PHOTO-FACES.md, "Looking"); then the rest of that page\'s list.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
