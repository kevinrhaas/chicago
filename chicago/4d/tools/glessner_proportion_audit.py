#!/usr/bin/env python3
"""T-2206: measure the current Glessner through T-2200's frozen cameras.

No camera fit, source-pick edit, geometry write, or historical-tier promotion.
--check compares the committed audit with the current inputs and asset bytes.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import math
from glessner_camera_baseline import evaluate_candidate, mesh_trees, metric

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'data/comparisons/glessner'
# The disposition text and nominal control schedule are a dated review. A later
# record must be reviewed, not relabeled by regenerating this report.
AUDITED_RECORD_SHA256 = '8f524efadf459d6b235945dd00ffc249b967d2d37665a2176b4550d76207f450'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive():
    observations = json.loads((DIRECTORY / 'observations.json').read_text())
    baseline = json.loads((DIRECTORY / 'report.json').read_text())
    record = ROOT / 'data/structures/glessner_house.json'
    assert digest(record) == AUDITED_RECORD_SHA256, 'Structure record changed: review the dimension schedule and dispositions before establishing a new audit'
    form = json.loads(record.read_text())['phases'][0]['form']
    value = lambda name: form[name]['value']
    master = ROOT / 'assets/gltf/glessner_house__as_built_1887.glb'
    candidate = evaluate_candidate(observations, baseline, master)
    report = copy.deepcopy(baseline)
    report.update(ticket='T-2206', geometry_changed=False, camera_refitted=False,
                  method=candidate['method'], candidate_sha256=candidate['candidate_sha256'],
                  not_a_reading='Re-measurement of the existing model and T-2200 source picks; no new historical adjudication.')
    for current, old in zip(candidate['views'], report['views']):
        for p, q in zip(current['landmarks'], old['landmarks']):
            q.update(p)
            q['fraction_projected_width'] = p['fraction_baseline_projected_width']
            q['association_warning'] = p['association_distance_m'] > .3
        for role, field in [('fit', 'fit_rms_px'), ('check', 'check_rms_px')]:
            errors = [p['residual_px'] for p in current['landmarks'] if p['role'] == role]
            old[field] = round(math.sqrt(math.fsum(e*e for e in errors)/len(errors)), 4)
        old['max_residual_px'] = max(p['residual_px'] for p in current['landmarks'])
        old['status'] = ('Current model · limited reference; no acceptance verdict' if current['limited']
                         else 'Current model · exceptions remain')
    report['assets'] = {name: {'sha256': digest(ROOT / name)} for name in observations['assets']}
    report['inputs'] = {str(p.relative_to(ROOT)): digest(p) for p in
                        [record, DIRECTORY/'observations.json', DIRECTORY/'report.json', DIRECTORY/'section-readings.json']}

    rows = []
    def row(name, dimension, source, tier, decision):
        rows.append(dict(name=name, model=dimension, source=source, tier=tier, decision=decision))
    angle = lambda rise, run: f'{math.degrees(math.atan2(rise, run)):.2f}°'
    east, north = value('ridge_east_wing'), value('ridge_north_range')
    west = value('v4_detail')['stable_roof_rework']
    row('Prairie roof: street pitch', angle(east['ridge'][0]-east['eave_east'][0], east['W']),
        'HABS sheet 6: ridge 45.7 and eave 27.1 ft above door, scaled from the printed chimney datum; sheet 2: 26 ft 6 in range.',
        'Inferred: ridge centered at W13.25; ±1 ft datum transfer is not a pitch survey.', 'Retain. Stronger vertical control than the earlier schematic section.')
    row('Prairie roof: courtyard pitch', angle(east['ridge'][0]+.74-east['eave_west'][0], 26.5-east['W']),
        'Sheets 4 and 6; the model carries door +0.74 ft to north grade.',
        'Inferred; common datum reconstructed ±1 ft.', 'Retain provisionally. Sheet 4 gives a smaller rise; reconcile the two sheets before changing this slope.')
    row('North roof: street / courtyard pitches', angle(34.1-23.1,14.6)+' / '+angle(34.1-24,29.19-14.6),
        'HABS sheet 4 ridge controls; T-2016 planar interpolation and T-2183 projecting eave.',
        'Reconstructed; courtyard edge ±0.5 ft.', 'Retain the 34.1-ft ridge and continuous 24-ft projecting edge; do not restore the superseded kicked slope.')
    row('West roof: full ridge / courtyard edge', '38.60 / 24.00 ft ng; '+angle(38.6-24,141-(125.75-2.36)),
        'HABS northwest photograph; T-2235 owner-corrected full-length ridge and 2.36-ft courtyard overhang.',
        'Reconstructed, approximately ±1 ft.', 'Retain the straight W141 ridge for all 59.75 ft. Do not reinstate the lowered rear roof.')
    row('West cross-gable: north / south pitches', angle(38.6-25.2,18.4)+' / '+angle(38.6-16.5,35-18.4),
        'T-2231 west-profile controls retained by T-2235; HABS photo 01 is oblique, not a roof survey.',
        'Reconstructed, approximately ±1 ft.', 'Retain independent cross-gable. Neither the cropped Nickel detail nor an isolated west view establishes the hidden courtyard slope.')
    dormers=value('dormers')
    row('Three courtyard dormers: centers', ', '.join(f'S{x:g}' for x in dormers['centres_S'])+' ft',
        'HABS sheet 4, three drawn dormers; spacing re-read in section-readings.json.',
        'Drawn fabric attested; scaled positions and 1904 carryback inferred.', 'Retain. Approximate raster spacings differ by 0.3–1.0 ft; they do not establish a displacement correction.')
    row('Courtyard dormers: body / hood width', f"{dormers['width_ft']:.2f} / {dormers['width_ft']+.52/.3048:.2f} ft",
        'Sheet 4 body/hood outlines; existing v4 hood projects 0.26 m per side.',
        'Body scaled from drawing; exact hood projection reconstructed.', 'Retain flared hood. The section suggests a narrower outline, but approximate raster scale, caps and silhouette definitions need reconciliation first.')
    row('Courtyard dormers: eave / apex / flare', '32.90 / 37.00 ft ng; 0.18 m run, 0.13 m rise',
        'Sheet 4; existing v4 emitter. HABS 05 and Florian GX112.24 are textual visual cross-checks only here.',
        'Drawing-derived heights; exact flare reconstructed.', 'Retain existing two-slope hips and dark soffit. Roof apex and finial tip must be picked separately.')
    row('West dormer: width / hood / height', '10.00-ft body; 1.60-ft side projection; 25.50 / 29.90 ft ng',
        'T-2235 connected hood; Nickel 1966–67 fragment is link-only, cropped and oblique.',
        'Reconstructed, approximately ±1 ft.', 'Retain the connected hood. No complete, unobscured dated west view provides an independent width/height correction.')
    row('Stair turret: radius / eave / apex', '5.25 / 32.50 / 42.30 ft; finial tip 44.30 ft ng',
        'HABS sheet 2 plan and sheet 4 elevation; ca.1923 court and 1948 detail cross-checks.',
        'Retained fabric attested; scaled dimensions and 1904 carryback inferred.', 'Retain provisionally. Sheet 4 suggests about 7.54 ft cone rise versus 9.80 ft in the model; resolve the shared height disagreement and apex/tip definitions before shortening the turret.')
    row('North tower: eave / apex / tip', '32.90 / 43.90 / 45.90 ft ng',
        'HABS section and north photographs; HABS 14 tip is partially screened by utility poles.',
        'Inferred form and scaled heights; finial dimensions reconstructed.', 'Retain pending cross-view reconciliation. Do not lower the tower by converting a pixel residual directly to feet.')
    bay=value('bay_dining')['outline']
    row('Dining bay: actual outer width / projection', f'{max(p[0] for p in bay)-min(p[0] for p in bay):.2f} / {max(p[1] for p in bay)-min(p[1] for p in bay):.2f} ft',
        'HABS sheets 2–3 exterior polygon. The 17 ft 8 in × 11 ft room labels describe the interior.',
        'Drawn plan attested; scaled exterior outline inferred.', 'Retain. Existing prose says 10.3 ft projection; actual coordinates give 9.90 ft. This is a description discrepancy, not a proven mesh defect.')
    row('Dining bay: upper glazing / copper cap', '20.90–24.00 ft ng; apex 34.10 ft; cap rise 10.10 ft',
        'T-2172/T-2183 retained alignment; HABS 05 is a later, restricted visual cross-check.',
        'Reconstructed, approximately ±1 ft.', 'Retain the upper band and 9.3–14.5-ft principal lights. Do not repeat the superseded enlargement from an oblique photo ratio.')
    row('Dining bay: shoulders / tiled connection', 'S29.19 shoulders; S14.60 ridge connection; 14.59-ft run',
        'T-2157 copper hip and crested tiled connection; T-2183 continuous eave.',
        'Reconstructed; exact apron dimensions not surveyed.', 'Retain the shoulder profile and joined roof. Visible northeast lifted copper belongs to T-2220.')
    row('Hall bow: wall / low copper rise', '26.50-ft wall; nominal 3.50-ft rise',
        'HABS sheet 4 low roof beyond the section; sheet 2 printed interior radius 9 ft 6 in; data p.21 copper sheathing.',
        'Copper attested at survey date; hidden roof form reconstructed.', 'Retain the low bow. T-2220 must attach the cladding to its host and remove the fold, without reshaping the main roofs.')

    trees=mesh_trees(master)
    controls=[]
    def control(name, point, material):
        xyz, tree=trees[material]; distance,index=tree.query(metric(point))
        controls.append(dict(name=name, nominal_building_ft=point, material=material,
                             nearest_vertex_m=xyz[index].round(6).tolist(),
                             association_distance_m=round(float(distance),6),
                             meaning='Nearest compatible vertex, not an independently surveyed feature; roof stock can sit above the nominal host.'))
    control('Prairie ridge midpoint',[13.25,40,46.44],'roof_plane')
    control('North ridge at dining connection',[70.6,14.6,34.1],'roof_plane')
    for s in [0,30,59.75]:control(f'West ridge S{s:g}',[141,s,38.6],'roof_plane')
    for i,s in enumerate(dormers['centres_S'],1):
        control(f'Courtyard dormer {i} apex',[23.1,s,37],'roof_plane')
        control(f'Courtyard dormer {i} front eave',[25.2+.30/.3048,s,32.9],'roof_plane')
    control('Stair turret cone apex',[27.3,55,42.3],'roof_plane')
    control('Dining copper apex',[70.6,29.19,34.1],'copper')
    for w in [60.9,80.3]:control(f'Dining shoulder W{w:g}',[w,29.19,24],'copper')
    report['dimension_controls']=rows
    report['mesh_controls']=controls
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=json.dumps(derive(),indent=2,ensure_ascii=False)+'\n'
    path=DIRECTORY/'audit-report.json'
    if args.check:
        assert path.read_text()==result, 'Audit drift; regenerate and review the changed controls and associations'
        print('PASS: T-2206 audit matches current assets and frozen camera inputs')
    else:
        path.write_text(result)
        print('Wrote current-model audit; no cameras or geometry changed')
