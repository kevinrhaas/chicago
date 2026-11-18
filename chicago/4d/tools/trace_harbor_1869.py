#!/usr/bin/env python3
"""Derive a local metric trace from inspected August 1869 chart pixels.

This makes NO geographic registration and does not update any scene. The metre
frame follows the printed scale/meridian, centred on the lighthouse symbol.
Optional audit SVG embeds the original verified raster for visual review.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / 'data/traces/harbor_1869/image_trace.json'
CONTROL = ROOT / 'data/traces/gcp/usace_chicago_harbor_1869_metric_controls.json'
OUTPUT = ROOT / 'data/traces/harbor_1869/metric_trace.geojson'


def derive():
    trace = json.loads(TRACE.read_text())
    controls = json.loads(CONTROL.read_text())
    bar = controls['scale_bar']
    pixel_span = math.dist(bar['pixel_zero'], bar['pixel_1000ft'])
    scale = bar['length_feet'] * bar['feet_to_metres'] / pixel_span
    meridian = controls['north_orientation']
    direction = [b-a for a,b in zip(meridian['pixel_south'], meridian['pixel_north'])]
    norm = math.hypot(*direction)
    north = [x/norm for x in direction]
    east = [-north[1], north[0]]
    origin = controls['origin']['pixel']
    features = []
    for record in trace['features']:
        points = []
        for pixel in record['geometry']['coordinates']:
            delta = [a-b for a,b in zip(pixel, origin)]
            points.append([round(math.fsum(a*b for a,b in zip(delta,east))*scale,4),
                           round(math.fsum(a*b for a,b in zip(delta,north))*scale,4)])
        features.append({'type':'Feature','id':record['id'],
                         'properties':{key:value for key,value in record.items() if key not in ('geometry','id')},
                         'geometry':{'type':record['geometry']['type'],'coordinates':points}})
    return trace, controls, {'type':'FeatureCollection',
        'coordinate_space':'Local paper-derived east/north metres about the 1869 lighthouse symbol; not WGS84 or project ENU.',
        'source_id':'usace_chicago_harbor_august_1869',
        'observed_date':'1869-08',
        'scene_adoption':'pending_absolute_registration_and_1869_to_1871_reconciliation',
        'derivation':{'command':'python3 tools/trace_harbor_1869.py',
                      'image_sha256':trace['image']['sha256'],
                      'pixel_metres':round(scale,9),
                      'origin_pixel':origin,'north_unit_pixel':north,'east_unit_pixel':east,
                      'absolute_registration_rms_m':None,
                      'manual_pixel_read_tolerance_m':round(scale*trace['manual_pick_precision_pixels'],3),
                      'uncertainty_note':'Manual read tolerance is not a ground accuracy result. The paper may be distorted, survey errors remain unknown, and source date precedes scene.'},
        'features':features}


def verified_raster(trace, raster):
    content = raster.read_bytes()
    if hashlib.sha256(content).hexdigest() != trace['image']['sha256']:
        raise ValueError('Raster SHA-256 does not match inspected source image')
    return content


def audit_svg(trace, raster, output):
    content = verified_raster(trace, raster)
    width,height = trace['image']['pixels']
    data = base64.b64encode(content).decode('ascii')
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             f'<image width="{width}" height="{height}" href="data:image/jpeg;base64,{data}"/>']
    palette=['#f44336','#1e88e5','#8e24aa','#00acc1','#ff8800','#43a047','#c51162','#3949ab']
    for i,record in enumerate(trace['features']):
        points=record['geometry']['coordinates']
        points_text=' '.join(','.join(str(v) for v in point) for point in points)
        parts.append(f'<polyline points="{points_text}" fill="none" stroke="{palette[i%len(palette)]}" stroke-width="5"/>')
        for x,y in points:
            parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="white" stroke="{palette[i%len(palette)]}" stroke-width="2"/>')
        x,y=points[len(points)//2]
        parts.append(f'<text x="{x+12}" y="{y-18}" font-family="sans-serif" font-size="24" fill="{palette[i%len(palette)]}" stroke="white" stroke-width="0.5">{record["id"]}</text>')
    parts.append('</svg>')
    output.write_text('\n'.join(parts)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--raster',type=Path)
    parser.add_argument('--audit-svg',type=Path)
    args=parser.parse_args()
    trace, controls, result=derive()
    raster = args.raster or ROOT / trace['image']['raster']
    verified_raster(trace, raster)
    serialized=json.dumps(result,indent=2)+'\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text()!=serialized:
            raise SystemExit('Metric trace is stale; run python3 tools/trace_harbor_1869.py')
    else:
        OUTPUT.write_text(serialized)
    if args.audit_svg:
        audit_svg(trace,raster,args.audit_svg)
    print(f'{len(result["features"])} relative traces; {result["derivation"]["pixel_metres"]:.6f} m/pixel; geographic registration pending')

if __name__=='__main__':
    main()
