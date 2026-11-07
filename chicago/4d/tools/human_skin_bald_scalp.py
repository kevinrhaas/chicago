# SPDX-License-Identifier: GPL-3.0-or-later
"""A bald crown on a MakeHuman skin atlas (T-3441).

MakeHuman's CC0 `old_caucasian_male` atlas paints a short dark stubble over the whole
scalp. John J. Glessner was bald on the crown (his 1897 plate), and his white side hair
is grown at runtime as strands (human-hair.js), so the stubble would read as a dark
crop. This blends the scalp's stubble into the atlas's own forehead skin tone, keeping
a trace of its fine texture, and leaves the face, ears and body as they were:

  python3 tools/human_skin_bald_scalp.py ORIGINAL.png OUT.png

ORIGINAL is the unchanged pack entry pinned in
assets/authored/humans/skin_mh_old_lightskinned_male/SOURCE.json; OUT is that folder's
old_lightskinned_male_bald_crown.png. Deterministic for the same input and Pillow.
"""
import sys

import numpy as np
from PIL import Image, ImageFilter


def bald(a):
    H, W, _ = a.shape
    lum = a @ np.array([.299, .587, .114], np.float32)
    blur = np.asarray(Image.fromarray(lum.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10))).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    head = (xx > 1270) & (yy > 330) & (yy < 1720)          # the head island of the hm08 atlas
    fx, fy = 1250 + 470*1.425, 330 + 500*1.425             # the face's centre (eyes, nose, mouth)
    face = ((xx-fx)/260.)**2 + ((yy-fy)/300.)**2 < 1
    skin_ref = np.median(a[head & face & (lum > 170)], axis=0)
    L_skin = float(np.median(lum[head & face & (lum > 170)]))
    L_hair = float(np.percentile(blur[head & ~face], 10))
    d = ((L_skin - blur) / max(1., L_skin - L_hair)).clip(0, 1)
    d = np.asarray(Image.fromarray((d*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(np.float32)/255
    d = (np.where(head & ~face, d, 0.)*1.6).clip(0, 1)
    detail = (lum / np.maximum(blur, 1.)).clip(.9, 1.1) ** .12
    tone = skin_ref[None, None, :] * detail[..., None] * 1.04
    return a*(1-d[..., None]) + tone*d[..., None]


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
    Image.fromarray(bald(a).clip(0, 255).astype(np.uint8)).save(out, optimize=True)
