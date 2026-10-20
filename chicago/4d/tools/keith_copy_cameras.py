#!/usr/bin/env python3
"""T-2876: the three reproductions of the 1888 Keith plate re-derived from the plate's camera.

a18-gh-1808-keith-field-front, a18-rba-ia-1888-keith-1808 and cgn-1808-inland-1888-keith-copy are
copies of the one photograph inland-1888 is solved on. T-1883 registered each to the plate by
SIFT/RANSAC and fitted its camera to the plate's camera THEN (eye about [47.67, -0.55, 0.5]); the
plate has been re-solved since (T-2763's level fit, T-2845's re-fit on the rebuilt loggia, eye
[40.883, -2.97, 0.746]), and the copies were not, so on the GLB in the tree they draw the loggia's
pairs where the old camera put them, not where the print has them.

A reproduction is a plane-to-plane map of the print, so its camera is the plate's camera followed
by that map: P_copy = H K R [I | -eye], H the homography each copy's solve records (plate pixels to
copy pixels). This decomposes H K R (RQ) into the copy's own intrinsics and rotation, closed form;
the eye is the plate's. The decomposition's skew is dropped (photo_match has none) and what that
costs is printed as the largest pixel shift over a grid of points on the front.

  python3 tools/keith_copy_cameras.py            # print the re-derived cameras
  python3 tools/keith_copy_cameras.py --write    # and write them into the three camera files
"""
from pathlib import Path
import argparse, json, math, re
import numpy as np

HERE = Path(__file__).resolve().parents[1]
VIEWS = HERE / 'data/reference_views/keith_house_1808_prairie'
COPIES = ['a18-gh-1808-keith-field-front', 'a18-rba-ia-1888-keith-1808', 'cgn-1808-inland-1888-keith-copy']
TAG = 'T-2876:'


def plate_camera(c):
    """K (image y down) and R (rows right, down, forward in the u/v/y frame) of a yaw camera."""
    assert 'basis_right_up_forward' not in c and c.get('pixel_aspect', 1) == 1
    t = math.radians(c['yaw_deg'])
    right, up, fwd = np.array([math.cos(t), -math.sin(t), 0]), np.array([0, 0, 1.0]), np.array([math.sin(t), math.cos(t), 0])
    K = np.array([[c['focal_px'], 0, c['principal_px'][0]], [0, c['focal_px'], c['principal_px'][1]], [0, 0, 1.0]])
    return K, np.array([right, -up, fwd])


def rq(M):
    """M = K R, K upper triangular with a positive diagonal, R a rotation."""
    P = np.flipud(np.eye(3))
    Q, U = np.linalg.qr((P @ M).T)
    K, R = P @ U.T @ P, P @ Q.T
    S = np.diag(np.sign(np.diag(K)))
    K, R = K @ S, S @ R
    if np.linalg.det(R) < 0:
        K, R = -K, -R
    return K / K[2, 2], R


def project(K, R, eye, X):
    d = (R @ (X - eye).T)
    p = K @ d
    return (p[:2] / p[2]).T


def homography(solve):
    m = re.search(r'Homography (\[\[.*?\]\])', solve)
    return np.array(json.loads(m.group(1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    plate = json.loads((VIEWS / 'inland-1888.json').read_text())
    K0, R0 = plate_camera(plate)
    eye = np.array(plate['eye'], float)
    # points over the street front and loggia (u 18 the front's face, v 0-10.4, 0-16 m up)
    grid = np.array([[18.0, v, y] for v in np.linspace(0, 10.4, 9) for y in np.linspace(0, 16, 9)])
    for name in COPIES:
        f = VIEWS / f'{name}.json'
        cam = json.loads(f.read_text())
        H = homography(cam['solve'])
        K, R = rq(H @ K0 @ R0)
        fx, skew, cx, fy, cy = K[0, 0], K[0, 1], K[0, 2], K[1, 1], K[1, 2]
        Kn = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
        exact = project(H @ K0, R0, eye, grid)
        built = project(Kn, R, eye, grid)
        inside = (exact[:, 0] >= 0) & (exact[:, 0] < cam['image_px'][0]) & (exact[:, 1] >= 0) & (exact[:, 1] < cam['image_px'][1])
        cost = float(np.abs(exact - built)[inside].max())
        old = project(*plate_camera_from(cam), grid)
        moved = float(np.hypot(*(old - built)[inside].T).max())
        # a rerun reads the camera it wrote itself, so the move from T-1883's is the one it recorded
        prior = re.search(r'against it the front moves up to ([\d.]+) px', cam['solve'])
        if prior:
            moved = float(prior.group(1))
        basis = [R[0].tolist(), (-R[1]).tolist(), R[2].tolist()]
        aspect = fx / fy
        print(f'{name}: focal {fy:.2f} px, pixel aspect {aspect:.4f}, principal [{cx:.2f}, {cy:.2f}], '
              f'skew {skew:.2f} px dropped (at most {cost:.2f} px over the front), '
              f'the front moves up to {moved:.1f} px from the T-1883 camera')
        if a.write:
            cam.update(principal_px=[round(cx, 3), round(cy, 3)], focal_px=round(fy, 3), eye=plate['eye'],
                       yaw_deg=plate['yaw_deg'], basis_right_up_forward=[[round(x, 6) for x in b] for b in basis])
            if abs(aspect - 1) > 5e-4:
                cam['pixel_aspect'] = round(aspect, 5)
            else:
                cam.pop('pixel_aspect', None)
            note = (f' {TAG} re-derived from the plate\'s camera as it now stands (inland-1888.json, re-fitted by T-2845, eye '
                    f'{plate["eye"]}) through the homography above, closed form: the copy\'s camera is H K R, RQ-decomposed into its '
                    f'own intrinsics and rotation (tools/keith_copy_cameras.py). Focal {fy:.2f} px, pixel aspect {aspect:.4f}, the '
                    f'decomposition\'s {skew:.2f} px skew dropped, which shifts no point on the front by more than {cost:.2f} px. '
                    f'T-1883\'s camera had been fitted to the plate\'s camera of its day (eye about [47.67, -0.55, 0.5]); against it the '
                    f'front moves up to {moved:.1f} px. The registration\'s own residual (above) is unchanged, and so is the plate\'s '
                    f'uncertainty: this view adds no independent survey.')
            cam['solve'] = cam['solve'].split(f' {TAG}')[0] + note
            f.write_text(json.dumps(cam, indent=2, ensure_ascii=False) + '\n')


def plate_camera_from(cam):
    """The K, R, eye a camera file draws with (basis or yaw, pixel aspect)."""
    f = cam['focal_px']
    K = np.array([[f * cam.get('pixel_aspect', 1), 0, cam['principal_px'][0]], [0, f, cam['principal_px'][1]], [0, 0, 1.0]])
    if 'basis_right_up_forward' in cam:
        r, u, fw = (np.array(b, float) for b in cam['basis_right_up_forward'])
    else:
        t = math.radians(cam['yaw_deg'])
        r, u, fw = np.array([math.cos(t), -math.sin(t), 0]), np.array([0, 0, 1.0]), np.array([math.sin(t), math.cos(t), 0])
    return K, np.array([r, -u, fw]), np.array(cam['eye'], float)


if __name__ == '__main__':
    main()
