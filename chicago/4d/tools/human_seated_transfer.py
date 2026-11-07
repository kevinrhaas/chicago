#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Transfer a reviewed W01 seated pose to another body on the shared hm08 rig (T-3423).

The seated drafts in data/humans/poses/w01/ hold, per bone, a global rest-to-pose rotation
and the bone head it lands on (tools/human_seated_study.py reads them). Rotations are
body-independent on the shared skeleton: every bone has the same name and parent. Heads
are not, so this keeps the donor's rotations and walks the TARGET body's own rest chain
forward from a re-seated pelvis:

  pelvis   x and z from the donor; height above the seat scaled by the two bodies'
           standing pelvis heights (a shorter body sits lower on the same bench)
  others   head = parent head + R_parent (rest head - rest parent head)

so no bone of the target stretches (load_study refuses a stretched chain). It writes the
target's draft beside the donor's and adds or replaces its row in
resident-driver-bindings.json with the measured pelvis head and wrist heads.

  python3 tools/human_seated_transfer.py --donor bardwell_otis_1835 \
      --target flynn_mary_1835_dress_study --person rc_flynn_mary \
      --body assets/authored/humans/makehuman_hm08/prepared_adult_female_25.json
  python3 tools/human_seated_transfer.py ... --check   # reproduce the committed draft byte for byte
"""
import argparse, hashlib, json, math
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
POSES = APP / 'data/humans/poses/w01'
BINDINGS = POSES / 'resident-driver-bindings.json'


def sha(b): return hashlib.sha256(b).hexdigest()


def rotate(r, v): return [math.fsum(r[i][k] * v[k] for k in range(3)) for i in range(3)]


def transfer(bindings, donor_id, target_id, person, body_path):
    donor = next(r for r in bindings['resident_bindings'] if r['asset_id'] == donor_id)
    draft = json.loads((POSES / donor['pose_draft_file']).read_text())
    if sha((POSES / donor['pose_draft_file']).read_bytes()) != donor['pose_draft_sha256']:
        raise SystemExit('donor draft differs from its binding')
    src = draft['bone_global_head_rotation']
    recipe = json.loads((APP / 'data/humans/recipes/worker_1835.json').read_text())
    donor_body = APP / next(v for v in recipe['proof_variants'] if v['id'] == donor_id)['body_input']
    if sha(donor_body.read_bytes()) != donor['body_sha256']:
        raise SystemExit('donor body differs from its binding')
    his = {b['name']: b for b in json.loads(donor_body.read_text())['skeleton']}
    her_bytes = (APP / body_path).read_bytes()
    her = {b['name']: b for b in json.loads(her_bytes)['skeleton']}
    if set(her) != set(src) or any(her[n]['parent'] != his[n]['parent'] for n in her):
        raise SystemExit('target skeleton is not the shared rig')
    seat = donor['seat_surface_m']
    ratio = her['pelvis']['head_m'][1] / his['pelvis']['head_m'][1]
    out = {}
    order = []
    def visit(n):
        if n in out: return
        p = her[n]['parent']
        if p is not None: visit(p)
        rot = src[n]['rotation_3x3']
        if p is None:
            # The root carries the pelvis: place it so that the re-seated pelvis is its child.
            if n != 'root' or her['pelvis']['parent'] != 'root': raise SystemExit('unexpected root bone')
            d = src['pelvis']['head_m']
            pelvis = [d[0], seat[1] + (d[1] - seat[1]) * ratio, d[2]]
            off = rotate(rot, [her['pelvis']['head_m'][k] - her[n]['head_m'][k] for k in range(3)])
            head = [pelvis[k] - off[k] for k in range(3)]
        elif n == 'pelvis':
            d = src[n]['head_m']
            head = [d[0], seat[1] + (d[1] - seat[1]) * ratio, d[2]]
        else:
            local = [her[n]['head_m'][k] - her[p]['head_m'][k] for k in range(3)]
            off = rotate(out[p]['rotation_3x3'], local)
            head = [out[p]['head_m'][k] + off[k] for k in range(3)]
        out[n] = {'head_m': head, 'rotation_3x3': rot}
        order.append(n)
    for n in src: visit(n)
    doc = {'frame': draft['frame'],
           'status': f'Transferred from {donor_id} (T-3423): the donor\'s reviewed rotations on this body\'s own rest chain, '
                     'pelvis re-seated by standing pelvis height; not canonical Blender acceptance',
           'bone_global_head_rotation': {n: out[n] for n in src}}
    raw = (json.dumps(doc, indent=2) + '\n').encode()
    name = f'{target_id}-transferred-pose.json'
    row = {'asset_id': target_id, 'person_reference_id': person, 'person_reference_grade': 'reconstructed',
           'body_sha256': sha(her_bytes), 'pose_draft_file': name, 'pose_draft_sha256': sha(raw),
           'pelvis_head_m': out['pelvis']['head_m'], 'seat_surface_m': seat,
           'wrist_targets_m': {s: out[f'hand_{s}']['head_m'] for s in 'lr'},
           'grip_status': f'transferred from {donor_id}; wrist heads only, no grip sockets',
           'transferred_from': donor_id}
    return name, raw, row


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--donor', required=True); a.add_argument('--target', required=True)
    a.add_argument('--person', required=True); a.add_argument('--body', required=True)
    a.add_argument('--check', action='store_true')
    args = a.parse_args()
    bindings = json.loads(BINDINGS.read_text())
    name, raw, row = transfer(bindings, args.donor, args.target, args.person, args.body)
    rows = [r for r in bindings['resident_bindings'] if r['asset_id'] != args.target] + [row]
    new = dict(bindings, resident_bindings=rows)
    text = json.dumps(new, indent=2) + '\n'
    if args.check:
        ok = (POSES / name).read_bytes() == raw and BINDINGS.read_text() == text
        print(f'seated transfer {args.target}: ' + ('reproduces' if ok else 'DIFFERS'))
        raise SystemExit(0 if ok else 1)
    (POSES / name).write_bytes(raw)
    BINDINGS.write_text(text)
    p = row['pelvis_head_m']
    print(f'wrote {name}; pelvis head {p[1]:.4f} m ({p[1] - row["seat_surface_m"][1]:.4f} above the seat)')


if __name__ == '__main__':
    main()
